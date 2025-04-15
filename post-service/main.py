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

# Modelos Pydantic
class Comment(BaseModel):
    user_id: str
    user_name: str
    content: str
    created_at: Optional[datetime] = None

class Post(BaseModel):
    content: str
    user_id: str
    image_url: Optional[str] = None
    comments: Optional[List[Comment]] = []
    likes: Optional[List[str]] = []
    created_at: Optional[datetime] = None

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
    return {"message": "Post created successfully", "post_id": str(result.inserted_id)}

@app.get("/posts/{post_id}")
async def get_post(post_id: str):
    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        post["_id"] = str(post["_id"])
        return post
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid post_id format: {str(e)}")

@app.get("/posts")
async def get_all_posts():
    posts = list(posts_collection.find())
    for post in posts:
        post["_id"] = str(post["_id"])
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
        return comment_dict
    except Exception as e:
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
        else:
            posts_collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$push": {"likes": user_id}}
            )
        return {"message": "Like toggled successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid post_id format: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)