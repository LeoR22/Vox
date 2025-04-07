from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Friend Service")

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/friend_db")
client = MongoClient(MONGO_URI)
db = client["friend_db"]
friendships_collection = db["friendships"]

# URL del API Gateway para validar usuarios
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

# Modelos Pydantic
class Friendship(BaseModel):
    user_id: str
    friend_id: str

# Rutas
@app.post("/friends/follow/{user_id}")
async def follow_user(user_id: str, friendship: Friendship):
    if friendship.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    if user_id == friendship.friend_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    # Verificar que user_id y friend_id existan
    async with httpx.AsyncClient() as client:
        # Verificar user_id
        response = await client.get(f"{API_GATEWAY_URL}/users/{user_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        # Verificar friend_id
        response = await client.get(f"{API_GATEWAY_URL}/users/{friendship.friend_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Friend not found")

    if friendships_collection.find_one({"user_id": user_id, "friend_id": friendship.friend_id}):
        raise HTTPException(status_code=400, detail="Already following this user")
    friendship_dict = friendship.dict()
    friendship_dict["created_at"] = datetime.utcnow()
    result = friendships_collection.insert_one(friendship_dict)
    friendship_id = str(result.inserted_id)
    return {"message": "Followed successfully", "friendship_id": friendship_id}

@app.get("/friends/followers/{user_id}")
async def get_followers(user_id: str):
    # Verificar que user_id exista
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_GATEWAY_URL}/users/{user_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")

    followers = list(friendships_collection.find({"friend_id": user_id}))
    for follower in followers:
        follower["_id"] = str(follower["_id"])
    return {"user_id": user_id, "followers_count": len(followers), "followers": followers}

@app.get("/friends/following/{user_id}")
async def get_following(user_id: str):
    # Verificar que user_id exista
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_GATEWAY_URL}/users/{user_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")

    following = list(friendships_collection.find({"user_id": user_id}))
    for follow in following:
        follow["_id"] = str(follow["_id"])
    return {"user_id": user_id, "following_count": len(following), "following": following}