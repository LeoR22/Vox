from fastapi import FastAPI, HTTPException, Header
from pymongo import MongoClient
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
from bson import ObjectId
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Like Service")

# Configuración de MongoDB con reintentos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/post_db")
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

db = client["post_db"]
posts_collection = db["posts"]

# Modelo Pydantic
class LikeData(BaseModel):
    user_id: str

# Ruta para alternar like
@app.post("/posts/{post_id}/likes")
async def toggle_like(post_id: str, like_data: LikeData, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        likes = post.get("likes", [])
        if like_data.user_id in likes:
            posts_collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$pull": {"likes": like_data.user_id}}
            )
            logger.info(f"Like removido para post_id: {post_id}, user_id: {like_data.user_id}")
        else:
            posts_collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$push": {"likes": like_data.user_id}}
            )
            logger.info(f"Like añadido para post_id: {post_id}, user_id: {like_data.user_id}")
        
        return {"message": "Like toggled successfully"}
    except Exception as e:
        logger.error(f"Error al procesar like: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid post_id format: {str(e)}")

# Ruta opcional para obtener likes de un post (si la necesitas)
@app.get("/posts/{post_id}/likes")
async def get_likes(post_id: str, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"post_id": post_id, "likes": post.get("likes", [])}
    except Exception as e:
        logger.error(f"Error al obtener likes: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid post_id format: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)