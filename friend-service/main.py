from fastapi import FastAPI, HTTPException, BackgroundTasks
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from bson import ObjectId
import time
import logging
import httpx
from fastapi.responses import FileResponse
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI(title="Friend Service")

# Configuración de MongoDB con reintentos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/friend_db")
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

db = client["friend_db"]
friends_collection = db["friends"]

# URL del user-service para actualizar contadores
USER_SERVICE_URL = "http://user-service:8000"

# Modelo Pydantic
class FollowRequest(BaseModel):
    user_id: str

# Función para verificar si un usuario existe
async def user_exists(user_id: str, token: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": token}
        try:
            response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}", headers=headers)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            logger.error(f"Error al verificar usuario {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al verificar usuario {user_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error al conectar con user-service para verificar usuario {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al conectar con user-service: {str(e)}")

# Función para actualizar contadores
async def update_follow_counts(user_id: str, follow_id: str, increment: bool, token: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": token}
        try:
            # Incrementar/decrementar following_count del usuario que sigue
            await client.put(
                f"{USER_SERVICE_URL}/users/{user_id}/update-follow-count",
                json={"field": "following_count", "value": 1 if increment else -1},
                headers=headers
            )
            # Incrementar/decrementar followers_count del usuario seguido
            await client.put(
                f"{USER_SERVICE_URL}/users/{follow_id}/update-follow-count",
                json={"field": "followers_count", "value": 1 if increment else -1},
                headers=headers
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Error al actualizar contadores: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al actualizar contadores: {str(e)}")
        except Exception as e:
            logger.error(f"Error al conectar con user-service para actualizar contadores: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al conectar con user-service: {str(e)}")

# Rutas
@app.post("/friends/follow/{follow_id}")
async def follow_user(follow_id: str, request: FollowRequest, background_tasks: BackgroundTasks, authorization: str = None):
    try:
        user_id = request.user_id
        if user_id == follow_id:
            raise HTTPException(status_code=400, detail="No puedes seguirte a ti mismo")

        # Verificar si los usuarios existen
        if not authorization:
            raise HTTPException(status_code=401, detail="Token de autorización requerido")
        if not await user_exists(user_id, authorization):
            raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
        if not await user_exists(follow_id, authorization):
            raise HTTPException(status_code=404, detail=f"Usuario {follow_id} no encontrado")

        # Verificar si ya sigue al usuario
        existing_follow = friends_collection.find_one({"user_id": user_id, "followed_id": follow_id})
        if existing_follow:
            raise HTTPException(status_code=400, detail="Ya sigues a este usuario")

        # Añadir la relación de seguimiento
        follow_data = {"user_id": user_id, "followed_id": follow_id, "created_at": datetime.utcnow()}
        friends_collection.insert_one(follow_data)

        # Actualizar contadores en user-service
        background_tasks.add_task(update_follow_counts, user_id, follow_id, True, authorization)

        return {"message": f"Ahora sigues a {follow_id}"}
    except Exception as e:
        logger.error(f"Error al seguir usuario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al seguir usuario: {str(e)}")

@app.post("/friends/unfollow/{follow_id}")
async def unfollow_user(follow_id: str, request: FollowRequest, background_tasks: BackgroundTasks, authorization: str = None):
    try:
        user_id = request.user_id
        if user_id == follow_id:
            raise HTTPException(status_code=400, detail="No puedes dejar de seguirte a ti mismo")

        # Verificar si los usuarios existen
        if not authorization:
            raise HTTPException(status_code=401, detail="Token de autorización requerido")
        if not await user_exists(user_id, authorization):
            raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
        if not await user_exists(follow_id, authorization):
            raise HTTPException(status_code=404, detail=f"Usuario {follow_id} no encontrado")

        # Verificar si sigue al usuario
        existing_follow = friends_collection.find_one({"user_id": user_id, "followed_id": follow_id})
        if not existing_follow:
            raise HTTPException(status_code=400, detail="No sigues a este usuario")

        # Eliminar la relación de seguimiento
        friends_collection.delete_one({"user_id": user_id, "followed_id": follow_id})

        # Actualizar contadores en user-service
        background_tasks.add_task(update_follow_counts, user_id, follow_id, False, authorization)

        return {"message": f"Has dejado de seguir a {follow_id}"}
    except Exception as e:
        logger.error(f"Error al dejar de seguir usuario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al dejar de seguir usuario: {str(e)}")

@app.get("/friends/following/{user_id}")
async def get_following(user_id: str, authorization: str = None):
    try:
        # Verificar si el usuario existe
        if not authorization:
            raise HTTPException(status_code=401, detail="Token de autorización requerido")
        if not await user_exists(user_id, authorization):
            return []  # Devolver lista vacía si el usuario no existe, en lugar de un error 404

        following = list(friends_collection.find({"user_id": user_id}))
        return [{"followed_id": friend["followed_id"]} for friend in following]
    except Exception as e:
        logger.error(f"Error al obtener usuarios seguidos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios seguidos: {str(e)}")

@app.get("/friends/followers/{user_id}")
async def get_followers(user_id: str, authorization: str = None):
    try:
        # Verificar si el usuario existe
        if not authorization:
            raise HTTPException(status_code=401, detail="Token de autorización requerido")
        if not await user_exists(user_id, authorization):
            return []  # Devolver lista vacía si el usuario no existe

        followers = list(friends_collection.find({"followed_id": user_id}))
        return [{"follower_id": follower["user_id"]} for follower in followers]
    except Exception as e:
        logger.error(f"Error al obtener seguidores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener seguidores: {str(e)}")

@app.get("/friends/{user_id}")
async def get_friends(user_id: str, authorization: str = None):
    try:
        # Verificar si el usuario existe
        if not authorization:
            raise HTTPException(status_code=401, detail="Token de autorización requerido")
        if not await user_exists(user_id, authorization):
            return []  # Devolver lista vacía si el usuario no existe

        following = set(friend["followed_id"] for friend in friends_collection.find({"user_id": user_id}))
        followers = set(follower["user_id"] for follower in friends_collection.find({"followed_id": user_id}))
        friends = following.intersection(followers)
        return list(friends)
    except Exception as e:
        logger.error(f"Error al obtener amigos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener amigos: {str(e)}")