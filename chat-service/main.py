from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
import httpx
import json
import asyncio
from dotenv import load_dotenv
import os
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Chat Service")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de MongoDB con reintentos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/chat_db")
for attempt in range(10):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        logger.info(f"Conexión a MongoDB establecida correctamente (intento {attempt + 1})")
        break
    except Exception as e:
        logger.error(f"Intento {attempt + 1} fallido: {str(e)}")
        if attempt < 9:
            time.sleep(5)
        else:
            raise Exception(f"No se pudo conectar a MongoDB tras 10 intentos: {str(e)}")

db = client["chat_db"]
messages_collection = db["messages"]

# URL del API Gateway para validar usuarios
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

# OAuth2 para validar tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Modelos Pydantic
class Message(BaseModel):
    sender_id: str
    receiver_id: str
    content: str

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        await websocket.send_json({"status": "connected", "user_id": user_id})
        logger.info(f"Usuario {user_id} conectado vía WebSocket")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"Usuario {user_id} desconectado")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
                logger.debug(f"Mensaje enviado a {user_id}: {message}")
            except Exception as e:
                logger.error(f"Error enviando mensaje a {user_id}: {str(e)}")
                self.disconnect(user_id)

manager = ConnectionManager()

# Validar user_id con reintentos y backoff exponencial
async def validate_user(user_id: str, token: str):
    async with httpx.AsyncClient() as client:
        for attempt in range(5):
            try:
                response = await client.get(
                    f"{API_GATEWAY_URL}/users/{user_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                logger.debug(f"Usuario {user_id} validado correctamente")
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Error validando usuario {user_id}: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=f"Usuario {user_id} no encontrado")
            except httpx.RequestError as e:
                logger.warning(f"Intento {attempt + 1} fallido al conectar con API Gateway: {str(e)}")
                if attempt < 4:
                    await asyncio.sleep(2 ** attempt)  # Backoff exponencial: 1s, 2s, 4s, 8s
                else:
                    raise HTTPException(status_code=503, detail=f"No se pudo conectar al API Gateway: {str(e)}")

# Rutas HTTP
@app.post("/chat/messages")
async def send_message(message: Message, token: str = Depends(oauth2_scheme)):
    if message.sender_id == message.receiver_id:
        raise HTTPException(status_code=400, detail="No puedes enviarte un mensaje a ti mismo")

    await validate_user(message.sender_id, token)
    await validate_user(message.receiver_id, token)

    message_dict = message.dict()
    message_dict["created_at"] = datetime.utcnow()
    result = messages_collection.insert_one(message_dict)
    message_id = str(result.inserted_id)
    message_dict["_id"] = message_id

    await manager.send_personal_message(message_dict, message.receiver_id)
    await manager.send_personal_message(message_dict, message.sender_id)

    logger.info(f"Mensaje guardado y enviado: {message_id}")
    return {"message": "Mensaje enviado correctamente", "message_id": message_id}

@app.get("/chat/messages/{user_id}/{receiver_id}")
async def get_messages(user_id: str, receiver_id: str, token: str = Depends(oauth2_scheme)):
    await validate_user(user_id, token)
    await validate_user(receiver_id, token)

    messages = list(messages_collection.find({
        "$or": [
            {"sender_id": user_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": user_id}
        ]
    }).sort("created_at", 1))
    for msg in messages:
        msg["_id"] = str(msg["_id"])
    logger.info(f"Obtenidos {len(messages)} mensajes entre {user_id} y {receiver_id}")
    return messages

# Ruta WebSocket
@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()

    try:
        token_message = await websocket.receive_text()
        if not token_message.startswith("Bearer "):
            await websocket.close(code=1008, reason="Formato de token inválido")
            return
        token = token_message.replace("Bearer ", "").strip()
        if not token:
            await websocket.close(code=1008, reason="Token requerido")
            return
    except Exception as e:
        logger.error(f"Error recibiendo token: {str(e)}")
        await websocket.close(code=1008, reason="Token requerido")
        return

    try:
        await validate_user(user_id, token)
    except HTTPException as e:
        logger.error(f"Validación de usuario fallida para {user_id}: {str(e)}")
        await websocket.close(code=1008, reason=str(e.detail))
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text("Formato JSON inválido")
                logger.warning(f"Mensaje inválido recibido de {user_id}: {data}")
                continue

            if not all(key in message for key in ["sender_id", "receiver_id", "content"]):
                await websocket.send_text("Formato de mensaje inválido")
                logger.warning(f"Formato de mensaje inválido de {user_id}: {message}")
                continue
            if message["sender_id"] != user_id:
                await websocket.send_text("El ID del remitente no coincide")
                logger.warning(f"ID de remitente no coincide para {user_id}: {message['sender_id']}")
                continue
            if message["sender_id"] == message["receiver_id"]:
                await websocket.send_text("No puedes enviarte un mensaje a ti mismo")
                logger.warning(f"Intento de mensaje a sí mismo por {user_id}")
                continue

            try:
                await validate_user(message["receiver_id"], token)
            except HTTPException as e:
                await websocket.send_text(f"Validación del receptor fallida: {e.detail}")
                logger.error(f"Validación del receptor fallida para {message['receiver_id']}: {str(e)}")
                continue

            message_dict = {
                "sender_id": message["sender_id"],
                "receiver_id": message["receiver_id"],
                "content": message["content"],
                "created_at": datetime.utcnow()
            }
            result = messages_collection.insert_one(message_dict)
            message_dict["_id"] = str(result.inserted_id)

            await manager.send_personal_message(message_dict, message["receiver_id"])
            await manager.send_personal_message(message_dict, message["sender_id"])
            await websocket.send_json({"status": "Mensaje enviado", "message_id": message_dict["_id"]})
            logger.info(f"Mensaje WebSocket procesado: {message_dict['_id']}")
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Error en WebSocket para {user_id}: {str(e)}")
        await websocket.close(code=1008, reason="Error interno del servidor")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)