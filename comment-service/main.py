from fastapi import FastAPI, HTTPException, Header
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from bson import ObjectId
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Comment Service")

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
class Comment(BaseModel):
    user_id: str
    user_name: str
    content: str

# Ruta para añadir comentario
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
        
        logger.info(f"Comentario añadido para post_id: {post_id}, user_id: {comment.user_id}")
        return comment_dict
    except Exception as e:
        logger.error(f"Error al añadir comentario: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid post_id format: {str(e)}")

# Ruta opcional para obtener comentarios de un post (si la necesitas)
@app.get("/posts/{post_id}/comments")
async def get_comments(post_id: str, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"post_id": post_id, "comments": post.get("comments", [])}
    except Exception as e:
        logger.error(f"Error al obtener comentarios: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid post_id format: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)