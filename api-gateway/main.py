from fastapi import FastAPI, HTTPException, Request
import httpx
import os
from dotenv import load_dotenv
import logging
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

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
LIKE_SERVICE_URL = os.getenv("LIKE_SERVICE_URL", "http://like-service:8000")
COMMENT_SERVICE_URL = os.getenv("COMMENT_SERVICE_URL", "http://comment-service:8000")
FRIEND_SERVICE_URL = os.getenv("FRIEND_SERVICE_URL", "http://friend-service:8006")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8007")

# Helper function para manejar solicitudes HTTP
async def forward_request(method: str, url: str, json=None, data=None, files=None, headers=None, timeout=10):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method == "POST":
                response = await client.post(url, json=json, data=data, files=files, headers=headers)
            elif method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "PUT":
                response = await client.put(url, data=data, files=files, headers=headers)
            else:
                raise ValueError(f"Método no soportado: {method}")
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"Error en {method} a {url}: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            logger.error(f"Error de red en {method} a {url}: {str(e)}")
            raise HTTPException(status_code=503, detail=f"No se pudo conectar al servicio en {url}")

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

@app.put("/users/{user_id}")
async def update_user(user_id: str, request: Request):
    headers = {"Authorization": request.headers.get("Authorization", "")}
    form_data = await request.form()
    files = {
        "profile_image": (form_data["profile_image"].filename, await form_data["profile_image"].read(), form_data["profile_image"].content_type)
        if "profile_image" in form_data and form_data["profile_image"]
        else None,
        "cover_image": (form_data["cover_image"].filename, await form_data["cover_image"].read(), form_data["cover_image"].content_type)
        if "cover_image" in form_data and form_data["cover_image"]
        else None,
    }
    files = {k: v for k, v in files.items() if v is not None}
    logger.info(f"Enviando solicitud de actualización de usuario a {USER_SERVICE_URL}/users/{user_id}")
    return await forward_request("PUT", f"{USER_SERVICE_URL}/users/{user_id}", files=files, headers=headers)

# Post Service
@app.post("/posts")
async def create_post(request: Request):
    form_data = await request.form()
    files = {"image": (form_data["image"].filename, await form_data["image"].read(), form_data["image"].content_type)} if "image" in form_data and form_data["image"] else None
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

# Like Service
@app.post("/posts/{post_id}/likes")
async def toggle_like(post_id: str, request: Request):
    data = await request.json()
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de like a {LIKE_SERVICE_URL}/posts/{post_id}/likes")
    return await forward_request("POST", f"{LIKE_SERVICE_URL}/posts/{post_id}/likes", json=data, headers=headers)

# Comment Service
@app.post("/posts/{post_id}/comments")
async def add_comment(post_id: str, request: Request):
    data = await request.json()
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de comentario a {COMMENT_SERVICE_URL}/posts/{post_id}/comments")
    return await forward_request("POST", f"{COMMENT_SERVICE_URL}/posts/{post_id}/comments", json=data, headers=headers)

# Proxy para servir imágenes desde el post-service
@app.get("/uploads/{path:path}")
async def serve_uploaded_file(path: str):
    logger.info(f"Intentando proxificar imagen: {path}")
    async with httpx.AsyncClient() as client:
        try:
            # Primero intenta con post-service
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
                # Intenta con user-service
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

# Friend Service
@app.post("/friends/follow/{follow_id}")
async def follow_user(follow_id: str, request: Request):
    data = await request.json()
    headers = {"Authorization": request.headers.get("Authorization", "")}
    logger.info(f"Enviando solicitud de seguir a {FRIEND_SERVICE_URL}/friends/follow/{follow_id}")
    return await forward_request("POST", f"{FRIEND_SERVICE_URL}/friends/follow/{follow_id}", json=data, headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)