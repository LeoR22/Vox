from fastapi import FastAPI, HTTPException, Request
import httpx
import os
from dotenv import load_dotenv
import logging
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from fastapi import WebSocket, WebSocketDisconnect

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="API Gateway")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URLs de los servicios
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
POST_SERVICE_URL = os.getenv("POST_SERVICE_URL", "http://post-service:8000")
FRIEND_SERVICE_URL = os.getenv("FRIEND_SERVICE_URL", "http://friend-service:8006")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8007")
BOOKMARK_SERVICE_URL = os.getenv("BOOKMARK_SERVICE_URL", "http://bookmark-service:8009")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8008")

# Helper function para manejar solicitudes HTTP
async def forward_request(method: str, url: str, json=None, data=None, files=None, headers=None, timeout=10):
    logger.info(f"Headers enviados a {url}: {headers}")
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method == "POST":
                response = await client.post(url, json=json, data=data, files=files, headers=headers)
            elif method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=json, data=data, files=files, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Método no soportado: {method}")
            response.raise_for_status()
            try:
                if "Content-Type" in response.headers and "image" in response.headers["Content-Type"]:
                    return StreamingResponse(
                        content=response.iter_bytes(),
                        status_code=response.status_code,
                        headers={"Content-Type": response.headers.get("Content-Type", "image/png")}
                    )
                return response.json()
            except ValueError:
                return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"Error en {method} a {url}: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
        except httpx.RequestError as e:
            logger.error(f"Error de red en {method} a {url}: {str(e)}")
            raise HTTPException(status_code=503, detail=f"No se pudo conectar al servicio en {url}")

# WebSocket proxy
async def forward_websocket(websocket: WebSocket, url: str):
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("GET", url, timeout=None) as response:
                await websocket.accept()
                async for chunk in response.aiter_bytes():
                    await websocket.send_bytes(chunk)
        except Exception as e:
            logger.error(f"Error en WebSocket proxy a {url}: {str(e)}")
            await websocket.close()

# Auth Service
@app.post("/auth/login")
async def login(request: Request):
    logger.info(f"Enviando solicitud de login a {AUTH_SERVICE_URL}/auth/login")
    data = await request.json()
    return await forward_request("POST", f"{AUTH_SERVICE_URL}/auth/login", json=data)

# User Service
@app.post("/users")
async def create_user(request: Request):
    logger.info(f"Enviando solicitud de registro a {USER_SERVICE_URL}/users")
    data = await request.json()
    return await forward_request("POST", f"{USER_SERVICE_URL}/users", json=data)

@app.get("/users/{user_id}")
async def get_user(user_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de usuario a {USER_SERVICE_URL}/users/{user_id}")
    return await forward_request("GET", f"{USER_SERVICE_URL}/users/{user_id}", headers=headers)

@app.get("/users")
async def get_all_users(request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de todos los usuarios a {USER_SERVICE_URL}/users")
    return await forward_request("GET", f"{USER_SERVICE_URL}/users", headers=headers)

@app.put("/users/{user_id}")
async def update_user(user_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    form_data = await request.form()
    files = {}
    data = {}

    # Manejar archivos (profile_image y cover_image)
    if "profile_image" in form_data and form_data["profile_image"] and form_data["profile_image"].filename:
        file_content = await form_data["profile_image"].read()
        if file_content:
            files["profile_image"] = (
                form_data["profile_image"].filename,
                file_content,
                form_data["profile_image"].content_type
            )
    if "cover_image" in form_data and form_data["cover_image"] and form_data["cover_image"].filename:
        file_content = await form_data["cover_image"].read()
        if file_content:
            files["cover_image"] = (
                form_data["cover_image"].filename,
                file_content,
                form_data["cover_image"].content_type
            )

    # Manejar campos de texto (bio y name)
    if "bio" in form_data and form_data["bio"] is not None:
        data["bio"] = form_data["bio"]
    if "name" in form_data and form_data["name"] is not None:
        data["name"] = form_data["name"]

    if not files and not data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos ni archivos para actualizar")

    logger.info(f"Enviando solicitud de actualización de usuario a {USER_SERVICE_URL}/users/{user_id} con data: {data}, files: {list(files.keys())}")
    return await forward_request("PUT", f"{USER_SERVICE_URL}/users/{user_id}", data=data, files=files, headers=headers)

@app.put("/users/{user_id}/update-follow-count")
async def update_follow_count(user_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de actualización de contador a {USER_SERVICE_URL}/users/{user_id}/update-follow-count")
    return await forward_request("PUT", f"{USER_SERVICE_URL}/users/{user_id}/update-follow-count", headers=headers, json=await request.json())

# Post Service
@app.post("/posts")
async def create_post(request: Request):
    form_data = await request.form()
    files = {"image": (form_data["image"].filename, await form_data["image"].read(), form_data["image"].content_type)} if "image" in form_data and form_data["image"] and form_data["image"].filename else None
    data = {key: form_data[key] for key in form_data if key != "image"}
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de creación de post a {POST_SERVICE_URL}/posts")
    return await forward_request("POST", f"{POST_SERVICE_URL}/posts", data=data, files=files, headers=headers)

@app.get("/posts")
async def get_all_posts(request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de todos los posts a {POST_SERVICE_URL}/posts")
    return await forward_request("GET", f"{POST_SERVICE_URL}/posts", headers=headers)

@app.get("/posts/{post_id}")
async def get_post(post_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de post a {POST_SERVICE_URL}/posts/{post_id}")
    return await forward_request("GET", f"{POST_SERVICE_URL}/posts/{post_id}", headers=headers)

@app.post("/posts/{post_id}/likes")
async def toggle_like(post_id: str, request: Request):
    data = await request.form()
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de like a {POST_SERVICE_URL}/posts/{post_id}/likes")
    return await forward_request("POST", f"{POST_SERVICE_URL}/posts/{post_id}/likes", data=data, headers=headers)

@app.post("/posts/{post_id}/comments")
async def add_comment(post_id: str, request: Request):
    data = await request.json()
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de comentario a {POST_SERVICE_URL}/posts/{post_id}/comments")
    return await forward_request("POST", f"{POST_SERVICE_URL}/posts/{post_id}/comments", json=data, headers=headers)

@app.post("/posts/{post_id}/comments/{comment_index}/likes")
async def toggle_comment_like(post_id: str, comment_index: int, request: Request):
    data = await request.form()
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de like a comentario a {POST_SERVICE_URL}/posts/{post_id}/comments/{comment_index}/likes")
    return await forward_request("POST", f"{POST_SERVICE_URL}/posts/{post_id}/comments/{comment_index}/likes", data=data, headers=headers)

# Friend Service
@app.post("/friends/follow/{follow_id}")
async def follow_user(follow_id: str, request: Request):
    data = await request.json()
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de seguir a {FRIEND_SERVICE_URL}/friends/follow/{follow_id}")
    return await forward_request("POST", f"{FRIEND_SERVICE_URL}/friends/follow/{follow_id}", json=data, headers=headers)

@app.post("/friends/unfollow/{follow_id}")
async def unfollow_user(follow_id: str, request: Request):
    data = await request.json()
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de dejar de seguir a {FRIEND_SERVICE_URL}/friends/unfollow/{follow_id}")
    return await forward_request("POST", f"{FRIEND_SERVICE_URL}/friends/unfollow/{follow_id}", json=data, headers=headers)

@app.get("/friends/following/{user_id}")
async def get_following(user_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de usuarios seguidos a {FRIEND_SERVICE_URL}/friends/following/{user_id}")
    return await forward_request("GET", f"{FRIEND_SERVICE_URL}/friends/following/{user_id}", headers=headers)

@app.get("/friends/followers/{user_id}")
async def get_followers(user_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de seguidores a {FRIEND_SERVICE_URL}/friends/followers/{user_id}")
    return await forward_request("GET", f"{FRIEND_SERVICE_URL}/friends/followers/{user_id}", headers=headers)

@app.get("/friends/{user_id}")
async def get_friends(user_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de amigos a {FRIEND_SERVICE_URL}/friends/{user_id}")
    return await forward_request("GET", f"{FRIEND_SERVICE_URL}/friends/{user_id}", headers=headers)

# Chat Service
@app.get("/chat/messages/{user_id}/{receiver_id}")
async def get_messages(user_id: str, receiver_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de mensajes a {CHAT_SERVICE_URL}/chat/messages/{user_id}/{receiver_id}")
    return await forward_request("GET", f"{CHAT_SERVICE_URL}/chat/messages/{user_id}/{receiver_id}", headers=headers)

@app.post("/alerts")
async def send_message(request: Request):
    data = await request.json()
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de envío de mensaje a {CHAT_SERVICE_URL}/chat/messages")
    return await forward_request("POST", f"{CHAT_SERVICE_URL}/chat/messages", json=data, headers=headers)

# Notification Service
@app.get("/notifications/{user_id}")
async def get_notifications(user_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de notificaciones a {NOTIFICATION_SERVICE_URL}/notifications/{user_id}")
    return await forward_request("GET", f"{NOTIFICATION_SERVICE_URL}/notifications/{user_id}", headers=headers)

@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: str):
    async with httpx.AsyncClient() as client:
        ws_url = f"ws://{NOTIFICATION_SERVICE_URL.split('http://')[1]}/ws/notifications/{user_id}"
        logger.info(f"Conectando WebSocket a {ws_url}")
        try:
            async with client.websocket(ws_url) as backend_ws:
                await websocket.accept()
                try:
                    while True:
                        data = await backend_ws.receive_json()
                        await websocket.send_json(data)
                except WebSocketDisconnect:
                    logger.info(f"Cliente WebSocket desconectado para user_id: {user_id}")
                except Exception as e:
                    logger.error(f"Error en WebSocket para user_id: {user_id}: {str(e)}")
                    await websocket.close()
        except Exception as e:
            logger.error(f"Error conectando al backend WebSocket {ws_url}: {str(e)}")
            await websocket.close()

# Proxy para servir imágenes desde el post-service o user-service
@app.get("/uploads/{path:path}")
async def serve_uploaded_file(path: str):
    logger.info(f"Intentando proxificar imagen: {path}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{POST_SERVICE_URL}/uploads/{path}")
            response.raise_for_status()
            logger.info(f"Imagen obtenida de post-service: {path}")
            return StreamingResponse(
                content=response.iter_bytes(),
                status_code=response.status_code,
                headers={"Content-Type": response.headers.get("Content-Type", "image/png")}
            )
        except httpx.HTTPStatusError as e:
            logger.warning(f"Imagen no encontrada en post-service: {path}, intentando con user-service")
            try:
                response = await client.get(f"{USER_SERVICE_URL}/uploads/{path}")
                response.raise_for_status()
                logger.info(f"Imagen obtenida de user-service: {path}")
                return StreamingResponse(
                    content=response.iter_bytes(),
                    status_code=response.status_code,
                    headers={"Content-Type": response.headers.get("Content-Type", "image/png")}
                )
            except httpx.HTTPStatusError as e2:
                logger.error(f"Error al obtener imagen de user-service: {e2.response.status_code} - {e2.response.text}")
                raise HTTPException(status_code=e2.response.status_code, detail="No se pudo obtener la imagen")
        except httpx.RequestError as e:
            logger.error(f"Error de red al obtener imagen: {str(e)}")
            raise HTTPException(status_code=503, detail="No se pudo conectar al servicio")

# Bookmark Service
@app.post("/bookmarks")
async def toggle_bookmark(request: Request):
    data = await request.json()
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de bookmark a {BOOKMARK_SERVICE_URL}/bookmarks")
    return await forward_request("POST", f"{BOOKMARK_SERVICE_URL}/bookmarks", json=data, headers=headers)

@app.get("/bookmarks/user/{user_id}")
async def get_bookmarks(user_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de bookmarks a {BOOKMARK_SERVICE_URL}/bookmarks/user/{user_id}")
    return await forward_request("GET", f"{BOOKMARK_SERVICE_URL}/bookmarks/user/{user_id}", headers=headers)

@app.get("/bookmarks/check")
async def check_bookmark(user_id: str, post_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de verificación de bookmark a {BOOKMARK_SERVICE_URL}/bookmarks/check?user_id={user_id}&post_id={post_id}")
    return await forward_request("GET", f"{BOOKMARK_SERVICE_URL}/bookmarks/check?user_id={user_id}&post_id={post_id}", headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)