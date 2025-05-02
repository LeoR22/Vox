from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from bson import ObjectId
import logging
from typing import Optional, List
import time
import uuid
import httpx

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Post Service")

# Montar el directorio de imágenes estáticas
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

# Configuración de MongoDB con reintentos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/post_db")
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

db = client["post_db"]
posts_collection = db["posts"]

# URL del notification-service
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8008")
FRIEND_SERVICE_URL = os.getenv("FRIEND_SERVICE_URL", "http://friend-service:8006")

# Modelos Pydantic
class Comment(BaseModel):
    user_id: str
    user_name: str
    content: str
    created_at: Optional[datetime] = None
    likes: Optional[List[str]] = []

class Post(BaseModel):
    content: str
    user_id: str
    image_url: Optional[str] = None
    comments: Optional[List[Comment]] = []
    likes: Optional[List[str]] = []
    created_at: Optional[datetime] = None

# Enviar notificación asíncrona
async def send_notification(user_id: str, message: str, type: str, post_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications",
                json={
                    "user_id": user_id,
                    "message": message,
                    "type": type,
                    "related_post_id": post_id
                }
            )
            response.raise_for_status()
            logger.info(f"Notificación enviada a user_id: {user_id}, tipo: {type}")
        except httpx.HTTPError as e:
            logger.error(f"Error enviando notificación a user_id: {user_id}: {str(e)}")

# Obtener seguidores de un usuario
async def get_followers(user_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{FRIEND_SERVICE_URL}/friends/followers/{user_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error obteniendo seguidores para user_id: {user_id}: {str(e)}")
            return []

# Rutas
@app.post("/posts")
async def create_post(content: str = Form(...), user_id: str = Form(...), image: UploadFile = File(None), authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    post_dict = {
        "content": content,
        "user_id": user_id,
        "likes": [],
        "comments": [],
        "created_at": datetime.utcnow()
    }
    
    if image:
        image_filename = f"{uuid.uuid4()}_{image.filename}"
        image_path = os.path.join("/app/uploads", image_filename)
        with open(image_path, "wb") as f:
            f.write(await image.read())
        post_dict["image_url"] = f"/uploads/{image_filename}"
    
    result = posts_collection.insert_one(post_dict)
    post_id = str(result.inserted_id)
    logger.info(f"Post creado con ID: {post_id} para user_id: {user_id}")

    # Notificar a los seguidores
    followers = await get_followers(user_id)
    for follower in followers:
        await send_notification(
            follower["user_id"],
            f"{user_id} ha publicado un nuevo post",
            "new_post",
            post_id
        )

    return {"message": "Post created successfully", "post_id": post_id}

@app.get("/posts/{post_id}")
async def get_post(post_id: str):
    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        post["_id"] = str(post["_id"])
        logger.info(f"Post obtenido con ID: {post_id}")
        return post
    except Exception as e:
        logger.error(f"Error al obtener post con ID: {post_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid post_id format: {str(e)}")

@app.get("/posts")
async def get_all_posts():
    posts = list(posts_collection.find())
    for post in posts:
        post["_id"] = str(post["_id"])
    logger.info(f"Obtenidos {len(posts)} posts")
    return posts

@app.post("/posts/{post_id}/comments")
async def add_comment(post_id: str, comment: Comment, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        comment_dict = comment.dict()
        comment_dict["created_at"] = datetime.utcnow()
        result = posts_collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$push": {"comments": comment_dict}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Post not found")
        logger.info(f"Comentario añadido al post_id: {post_id} por user_id: {comment.user_id}")
        return comment_dict
    except Exception as e:
        logger.error(f"Error al añadir comentario al post_id: {post_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid post_id format: {str(e)}")

@app.post("/posts/{post_id}/likes")
async def toggle_like(post_id: str, user_id: str = Form(...), authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        likes = post.get("likes", [])
        if user_id in likes:
            posts_collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$pull": {"likes": user_id}}
            )
            action = "removed"
        else:
            posts_collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$push": {"likes": user_id}}
            )
            action = "added"
            # Notificar al dueño del post
            if post["user_id"] != user_id:  # No notificar si el usuario se da like a sí mismo
                await send_notification(
                    post["user_id"],
                    f"{user_id} ha dado like a tu post",
                    "like",
                    post_id
                )
        logger.info(f"Like {action} para post_id: {post_id} por user_id: {user_id}")
        return {"message": "Like toggled successfully", "action": action}
    except Exception as e:
        logger.error(f"Error al gestionar like para post_id: {post_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid post_id format: {str(e)}")

@app.post("/posts/{post_id}/comments/{comment_index}/likes")
async def toggle_comment_like(post_id: str, comment_index: int, user_id: str = Form(...), authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        comments = post.get("comments", [])
        if comment_index < 0 or comment_index >= len(comments):
            raise HTTPException(status_code=404, detail="Comment not found")

        comment = comments[comment_index]
        likes = comment.get("likes", [])

        if user_id in likes:
            likes.remove(user_id)
            action = "removed"
        else:
            likes.append(user_id)
            action = "added"

        # Actualizar el comentario en la base de datos
        posts_collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {f"comments.{comment_index}.likes": likes}}
        )
        logger.info(f"Like {action} para comentario {comment_index} en post_id: {post_id} por user_id: {user_id}")
        return {"message": "Comment like toggled successfully", "action": action}
    except Exception as e:
        logger.error(f"Error al gestionar like en comentario {comment_index} para post_id: {post_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid post_id or comment_index: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)