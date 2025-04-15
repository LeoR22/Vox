from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
import httpx
import json
from dotenv import load_dotenv
import os
import time

load_dotenv()

app = FastAPI(title="Chat Service")

# Configuración de MongoDB con reintentos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/chat_db")
for attempt in range(10):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        print(f"Conexión a MongoDB establecida correctamente (intento {attempt + 1})")
        break
    except Exception as e:
        print(f"Intento {attempt + 1} fallido: {str(e)}")
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

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

# Validar user_id
async def validate_user(user_id: str, token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_GATEWAY_URL}/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return response.json()

# Rutas HTTP
@app.post("/chat/messages")
async def send_message(message: Message, token: str = Depends(oauth2_scheme)):
    if message.sender_id == message.receiver_id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")

    await validate_user(message.sender_id, token)
    await validate_user(message.receiver_id, token)

    message_dict = message.dict()
    message_dict["created_at"] = datetime.utcnow()
    result = messages_collection.insert_one(message_dict)
    message_id = str(result.inserted_id)
    message_dict["_id"] = message_id

    await manager.send_personal_message(message_dict, message.receiver_id)

    return {"message": "Message sent successfully", "message_id": message_id}

@app.get("/chat/messages/{user_id}/{receiver_id}")
async def get_messages(user_id: str, receiver_id: str, token: str = Depends(oauth2_scheme)):
    await validate_user(user_id, token)
    await validate_user(receiver_id, token)

    messages = list(messages_collection.find({
        "$or": [
            {"sender_id": user_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": user_id}
        ]
    }))
    for msg in messages:
        msg["_id"] = str(msg["_id"])
    return messages

# Ruta WebSocket
@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()

    try:
        token_message = await websocket.receive_text()
        if not token_message.startswith("Bearer "):
            await websocket.close(code=1008, reason="Invalid token format")
            return
        token = token_message.replace("Bearer ", "")
    except Exception:
        await websocket.close(code=1008, reason="Token required")
        return

    try:
        await validate_user(user_id, token)
    except HTTPException as e:
        await websocket.close(code=1008, reason=str(e.detail))
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text("Invalid JSON format")
                continue

            if not all(key in message for key in ["sender_id", "receiver_id", "content"]):
                await websocket.send_text("Invalid message format")
                continue
            if message["sender_id"] != user_id:
                await websocket.send_text("Sender ID mismatch")
                continue
            if message["sender_id"] == message["receiver_id"]:
                await websocket.send_text("Cannot send message to yourself")
                continue

            await validate_user(message["receiver_id"], token)

            message_dict = {
                "sender_id": message["sender_id"],
                "receiver_id": message["receiver_id"],
                "content": message["content"],
                "created_at": datetime.utcnow()
            }
            result = messages_collection.insert_one(message_dict)
            message_dict["_id"] = str(result.inserted_id)

            await manager.send_personal_message(message_dict, message["receiver_id"])
            await websocket.send_json({"status": "Message sent", "message_id": message_dict["_id"]})
    except WebSocketDisconnect:
        manager.disconnect(user_id)
