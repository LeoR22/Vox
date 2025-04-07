from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Like Service")

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/like_db")
client = MongoClient(MONGO_URI)
db = client["like_db"]
likes_collection = db["likes"]

# URL del API Gateway para validar posts
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

# Modelos Pydantic
class Like(BaseModel):
    post_id: str
    user_id: str

# Rutas
@app.post("/likes/post/{post_id}")
async def add_like(post_id: str, like: Like):
    if like.post_id != post_id:
        raise HTTPException(status_code=400, detail="Post ID mismatch")

    # Verificar que el post_id exista
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_GATEWAY_URL}/posts/{post_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Post not found")

    if likes_collection.find_one({"post_id": post_id, "user_id": like.user_id}):
        raise HTTPException(status_code=400, detail="User already liked this post")
    like_dict = like.dict()
    like_dict["created_at"] = datetime.utcnow()
    result = likes_collection.insert_one(like_dict)
    like_id = str(result.inserted_id)
    return {"message": "Like added successfully", "like_id": like_id}

@app.get("/likes/post/{post_id}")
async def get_likes(post_id: str):
    # Verificar que el post_id exista
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_GATEWAY_URL}/posts/{post_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Post not found")

    likes = list(likes_collection.find({"post_id": post_id}))
    for like in likes:
        like["_id"] = str(like["_id"])
    return {"post_id": post_id, "likes_count": len(likes), "likes": likes}