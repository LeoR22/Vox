from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
import httpx
from dotenv import load_dotenv
import os
from bson import ObjectId  # Importar ObjectId desde bson

load_dotenv()

app = FastAPI(title="Post Service")

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/post_db")
client = MongoClient(MONGO_URI)
db = client["post_db"]
posts_collection = db["posts"]

# URL del API Gateway para validar usuarios
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

# Modelos Pydantic
class Post(BaseModel):
    content: str
    user_id: str

# Función para validar user_id
async def validate_user(user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_GATEWAY_URL}/users/{user_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return response.json()

# Rutas
@app.post("/posts")
async def create_post(post: Post):
    # Validar user_id
    await validate_user(post.user_id)

    post_dict = post.dict()
    post_dict["created_at"] = datetime.utcnow()
    result = posts_collection.insert_one(post_dict)
    post_id = str(result.inserted_id)
    post_dict["_id"] = post_id
    return {"message": "Post created successfully", "post_id": post_id}

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