from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
import asyncio
import time
from typing import List, Dict
from bson import ObjectId

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Notification Service")

# Configuración de MongoDB con reintentos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/notification_db")
for attempt in range(10):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        logger.info("Conexión a MongoDB establecida correctamente")
        break
    except Exception as e:
        logger.error(f"Intento {attempt + 1} fallido: {str(e)}")
        if attempt < 9:
            time.sleep(5)
        else:
            raise Exception(f"No se pudo conectar a MongoDB tras 10 intentos: {str(e)}")

db = client["notification_db"]
notifications_collection = db["notifications"]

# Modelo Pydantic para notificaciones
class Notification(BaseModel):
    user_id: str
    message: str
    type: str  # e.g., "new_post", "like"
    related_post_id: str
    created_at: datetime = None

# Almacenar conexiones WebSocket activas
websocket_connections: Dict[str, List[WebSocket]] = {}

# Endpoint para conectar WebSocket
@app.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    if user_id not in websocket_connections:
        websocket_connections[user_id] = []
    websocket_connections[user_id].append(websocket)
    logger.info(f"WebSocket conectado para user_id: {user_id}")
    try:
        while True:
            await websocket.receive_text()  # Mantener la conexión viva
    except WebSocketDisconnect:
        websocket_connections[user_id].remove(websocket)
        if not websocket_connections[user_id]:
            del websocket_connections[user_id]
        logger.info(f"WebSocket desconectado para user_id: {user_id}")

# Enviar notificación a un usuario
async def send_notification(user_id: str, notification: Notification):
    notification_dict = notification.dict()
    notification_dict["created_at"] = datetime.utcnow()
    notifications_collection.insert_one(notification_dict)
    logger.info(f"Notificación guardada para user_id: {user_id}, tipo: {notification.type}")

    if user_id in websocket_connections:
        for ws in websocket_connections[user_id]:
            try:
                await ws.send_json(notification_dict)
                logger.info(f"Notificación enviada a user_id: {user_id} via WebSocket")
            except Exception as e:
                logger.error(f"Error enviando notificación a user_id: {user_id}: {str(e)}")

# Endpoint para crear notificación (usado por otros servicios)
@app.post("/notifications")
async def create_notification(notification: Notification):
    await send_notification(notification.user_id, notification)
    return {"message": "Notificación creada y enviada"}

# Endpoint para obtener notificaciones de un usuario
@app.get("/notifications/{user_id}")
async def get_notifications(user_id: str):
    notifications = list(notifications_collection.find({"user_id": user_id}).sort("created_at", -1))
    for notif in notifications:
        notif["_id"] = str(notif["_id"])
    logger.info(f"Obtenidas {len(notifications)} notificaciones para user_id: {user_id}")
    return notifications

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)