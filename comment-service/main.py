from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Comment Service")

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/comment_db")
client = MongoClient(MONGO_URI)
db = client["comment_db"]
comments_collection = db["comments"]

# URL del API Gateway para validar posts
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

# Modelos Pydantic
class Comment(BaseModel):
    content: str
    post_id: str
    user_id: str

# Rutas
@app.post("/comments")
async def create_comment(comment: Comment):
    # Verificar que el post_id exista
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_GATEWAY_URL}/posts/{comment.post_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Post not found")

    comment_dict = comment.dict()
    comment_dict["created_at"] = datetime.utcnow()
    result = comments_collection.insert_one(comment_dict)
    comment_id = str(result.inserted_id)
    return {"message": "Comment created successfully", "comment_id": comment_id}

@app.get("/comments/post/{post_id}")
async def get_comments(post_id: str):
    # Verificar que el post_id exista
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_GATEWAY_URL}/posts/{post_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Post not found")

    comments = list(comments_collection.find({"post_id": post_id}))
    for comment in comments:
        comment["_id"] = str(comment["_id"])
    return comments