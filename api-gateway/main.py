from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
import httpx
import json
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Twitter Clone API Gateway")

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de JWT
SECRET_KEY = os.getenv("SECRET_KEY", "my-super-secret-key-1234567890")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# OAuth2 para validar tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# URLs de los microservicios
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8002")
POST_SERVICE_URL = os.getenv("POST_SERVICE_URL", "http://post-service:8003")
COMMENT_SERVICE_URL = os.getenv("COMMENT_SERVICE_URL", "http://comment-service:8004")
LIKE_SERVICE_URL = os.getenv("LIKE_SERVICE_URL", "http://like-service:8008")
FRIEND_SERVICE_URL = os.getenv("FRIEND_SERVICE_URL", "http://friend-service:8006")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8007")

# Validar token directamente en el API Gateway
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"email": email}

# Rutas HTTP
@app.post("/auth/register")
async def register(data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/register", json=data)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/auth/login")
async def login(data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/login", json=data)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/users")
async def create_user(data: dict, user: dict = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_SERVICE_URL}/users", json=data)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/users/{user_id}")
async def get_user(user_id: str, user: dict = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/chat/messages")
async def send_message(data: dict, token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(f"{CHAT_SERVICE_URL}/chat/messages", json=data, headers=headers)
        return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/chat/messages/{user_id}/{receiver_id}")
async def get_messages(user_id: str, receiver_id: str, token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"{CHAT_SERVICE_URL}/chat/messages/{user_id}/{receiver_id}", headers=headers)
        return JSONResponse(content=response.json(), status_code=response.status_code)

# Ruta WebSocket
@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    try:
        token = await websocket.receive_text()
        if not token.startswith("Bearer "):
            await websocket.close(code=1008, reason="Invalid token format")
            return
        token = token.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            await websocket.close(code=1008, reason="Invalid token")
            return
    except (JWTError, Exception):
        await websocket.close(code=1008, reason="Token required")
        return

    async with httpx.AsyncClient() as client:
        ws_url = f"ws://{CHAT_SERVICE_URL.split('http://')[1]}/ws/chat/{user_id}"
        async with client.websocket(ws_url) as chat_ws:
            await chat_ws.send_text(f"Bearer {token}")
            async def forward_from_client_to_service():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await chat_ws.send_text(data)
                except WebSocketDisconnect:
                    await chat_ws.close()

            async def forward_from_service_to_client():
                try:
                    while True:
                        data = await chat_ws.receive_text()
                        await websocket.send_text(data)
                except WebSocketDisconnect:
                    await websocket.close()

            import asyncio
            await asyncio.gather(
                forward_from_client_to_service(),
                forward_from_service_to_client()
            )