from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Body
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
async def follow_user(follow_id: str, user: dict = Body(...), authorization: str = Header(None)):
    try:
        logger.info(f"Header Authorization recibido: {authorization}")
        if not authorization:
            raise HTTPException(status_code=401, detail="Token de autorización requerido")
        
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="El campo user_id es requerido")

        # Normalizar user_id y follow_id
        user_id = user_id.lower().strip()
        follow_id = follow_id.lower().strip()
        logger.info(f"Intentando seguir: user_id={user_id}, follow_id={follow_id}")

        if user_id == follow_id:
            raise HTTPException(status_code=400, detail="No puedes seguirte a ti mismo")

        # Verificar si ambos usuarios existen
        if not await user_exists(user_id, authorization):
            raise HTTPException(status_code=404, detail=f"El usuario {user_id} no existe")
        if not await user_exists(follow_id, authorization):
            raise HTTPException(status_code=404, detail=f"El usuario {follow_id} no existe")

        # Verificar si ya sigue al usuario
        existing_follow = friends_collection.find_one({"user_id": user_id, "followed_id": follow_id})
        if existing_follow:
            logger.warning(f"Relación de seguimiento ya existe: user_id={user_id}, follow_id={follow_id}")
            raise HTTPException(status_code=400, detail="Ya sigues a este usuario")

        # Crear la relación de seguimiento
        follow_data = {
            "user_id": user_id,
            "followed_id": follow_id,
            "created_at": datetime.utcnow()
        }
        result = friends_collection.insert_one(follow_data)
        logger.info(f"Relación de seguimiento creada: {result.inserted_id}")

        # Actualizar contadores de seguimiento usando la función correcta
        await update_follow_counts(user_id, follow_id, True, authorization)

        return {"message": f"Ahora sigues a {follow_id}"}
    except HTTPException as e:
        raise e  # Re-lanzar excepciones HTTP para que se manejen correctamente
    except Exception as e:
        logger.error(f"Error al seguir usuario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al seguir usuario: {str(e)}")

@app.post("/friends/unfollow/{follow_id}")
async def unfollow_user(follow_id: str, request: FollowRequest, background_tasks: BackgroundTasks, authorization: str = Header(None)):
    try:
        logger.info(f"Header Authorization recibido: {authorization}")
        user_id = request.user_id.lower().strip()
        follow_id = follow_id.lower().strip()
        logger.info(f"Intentando dejar de seguir: user_id={user_id}, follow_id={follow_id}")

        if user_id == follow_id:
            raise HTTPException(status_code=400, detail="No puedes dejar de seguirte a ti mismo")

        if not authorization:
            raise HTTPException(status_code=401, detail="Token de autorización requerido")
        if not await user_exists(user_id, authorization):
            raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
        if not await user_exists(follow_id, authorization):
            raise HTTPException(status_code=404, detail=f"Usuario {follow_id} no encontrado")

        # Verificar si sigue al usuario y loguear todas las relaciones
        existing_follows = list(friends_collection.find({"user_id": user_id, "followed_id": follow_id}))
        logger.info(f"Relaciones encontradas para user_id={user_id}, follow_id={follow_id}: {existing_follows}")
        if not existing_follows:
            logger.warning(f"No se encontró relación de seguimiento: user_id={user_id}, follow_id={follow_id}")
            raise HTTPException(status_code=400, detail="No sigues a este usuario")

        # Eliminar la relación de seguimiento (eliminará todas las coincidencias)
        result = friends_collection.delete_many({"user_id": user_id, "followed_id": follow_id})
        logger.info(f"Relación de seguimiento eliminada: {result.deleted_count} documentos eliminados")

        # Actualizar contadores en user-service
        background_tasks.add_task(update_follow_counts, user_id, follow_id, False, authorization)

        return {"message": f"Has dejado de seguir a {follow_id}"}
    except Exception as e:
        logger.error(f"Error al dejar de seguir usuario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al dejar de seguir usuario: {str(e)}")

@app.get("/friends/following/{user_id}")
async def get_following(user_id: str, authorization: str = Header(None)):
    try:
        logger.info(f"Header Authorization recibido: {authorization}")
        user_id = user_id.lower().strip()
        if not authorization:
            raise HTTPException(status_code=401, detail="Token de autorización requerido")
        if not await user_exists(user_id, authorization):
            return []

        # Obtener todas las relaciones y eliminar duplicados
        following = list(friends_collection.find({"user_id": user_id}))
        logger.info(f"Usuarios seguidos por {user_id} (antes de eliminar duplicados): {[friend.get('followed_id') for friend in following]}")
        # Eliminar duplicados manteniendo el orden
        seen = set()
        unique_following = []
        for friend in following:
            followed_id = friend.get("followed_id")
            if followed_id and followed_id not in seen:
                seen.add(followed_id)
                unique_following.append(friend)
        logger.info(f"Usuarios seguidos por {user_id} (después de eliminar duplicados): {[friend.get('followed_id') for friend in unique_following]}")
        return [{"followed_id": friend.get("followed_id")} for friend in unique_following if friend.get("followed_id") is not None]
    except Exception as e:
        logger.error(f"Error al obtener usuarios seguidos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios seguidos: {str(e)}")

@app.get("/friends/followers/{user_id}")
async def get_followers(user_id: str, authorization: str = Header(None)):
    try:
        logger.info(f"Header Authorization recibido: {authorization}")
        user_id = user_id.lower().strip()
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
async def get_friends(user_id: str, authorization: str = Header(None)):
    try:
        logger.info(f"Header Authorization recibido: {authorization}")
        user_id = user_id.lower().strip()
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