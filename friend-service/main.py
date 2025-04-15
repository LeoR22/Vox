from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from bson import ObjectId
import time

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

# Modelo Pydantic
class Friend(BaseModel):
    user_id: str
    friend_id: str

# Rutas
@app.post("/friends/follow/{follow_id}")
async def follow_user(follow_id: str, follower: dict):
    user_id = follower["user_id"]
    friend = {"user_id": user_id, "friend_id": follow_id}
    friends_collection.insert_one(friend)
    return {"message": "Followed successfully"}

@app.get("/friends/following/{user_id}")
async def get_following(user_id: str):
    following = list(friends_collection.find({"user_id": user_id}))
    return [str(friend["friend_id"]) for friend in following]

@app.get("/friends/followers/{user_id}")
async def get_followers(user_id: str):
    followers = list(friends_collection.find({"friend_id": user_id}))
    return [str(follower["user_id"]) for follower in followers]

@app.get("/friends/{user_id}")
async def get_friends(user_id: str):
    following = set(friend["friend_id"] for friend in friends_collection.find({"user_id": user_id}))
    followers = set(follower["user_id"] for follower in friends_collection.find({"friend_id": user_id}))
    friends = following.intersection(followers)
    return list(friends)