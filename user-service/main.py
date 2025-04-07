from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from bson import ObjectId

load_dotenv()

app = FastAPI(title="User Service")

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/user_db")
client = MongoClient(MONGO_URI)
db = client["user_db"]
users_collection = db["users"]

# Modelos Pydantic
class User(BaseModel):
    email: str
    name: str
    bio: str

# Rutas
@app.post("/users")
async def create_user(user: User):
    user_dict = user.dict()
    result = users_collection.insert_one(user_dict)
    user_id = str(result.inserted_id)
    return {"message": "User created successfully", "user_id": user_id}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user["_id"] = str(user["_id"])
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid user_id format: {str(e)}")