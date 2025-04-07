from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Auth Service")

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/auth_db")
client = MongoClient(MONGO_URI)
db = client["auth_db"]
users_collection = db["users"]

# Configuración de JWT
SECRET_KEY = os.getenv("SECRET_KEY", "my-super-secret-key-1234567890")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Configuración de hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Modelos Pydantic
class User(BaseModel):
    email: str
    password: str

# Funciones auxiliares
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Rutas
@app.post("/register")
async def register(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    user_dict = {"email": user.email, "hashed_password": hashed_password}
    users_collection.insert_one(user_dict)
    return {"message": "User registered successfully"}

@app.post("/login")
async def login(user: User):
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}