from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
import time
import jwt
import bcrypt

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Auth Service")

# Configuración de MongoDB con reintentos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/user_db")  # Cambiar a user_db
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret")  # Asegúrate de que sea un secreto fuerte en producción

for attempt in range(10):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # Verifica la conexión
        logger.info("Conexión a MongoDB establecida correctamente")
        break
    except Exception as e:
        logger.error(f"Intento {attempt + 1} fallido: {str(e)}")
        if attempt < 9:
            time.sleep(5)  # Espera 5 segundos antes de reintentar
        else:
            raise Exception(f"No se pudo conectar a MongoDB tras 10 intentos: {str(e)}")

db = client["user_db"]  # Usar user_db en lugar de auth_db
users_collection = db["users"]

# Modelo Pydantic para login
class LoginData(BaseModel):
    email: str
    password: str

# Función para verificar contraseña
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Ruta para login
@app.post("/auth/login")
async def login(login_data: LoginData):
    logger.info(f"Buscando usuario con email: {login_data.email}")
    user = users_collection.find_one({"email": login_data.email})
    if not user:
        logger.warning(f"Usuario no encontrado: {login_data.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verificar la contraseña con bcrypt
    if "password" not in user or not verify_password(login_data.password, user["password"]):
        logger.warning(f"Contraseña incorrecta para: {login_data.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generar JWT
    token_payload = {
        "user_id": user["user_id"],
        "email": user["email"],
        "exp": time.time() + 3600  # Token expira en 1 hora
    }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
    
    logger.info(f"Login exitoso para user_id: {user['user_id']}")
    return {
        "token": token,
        "user_id": user["user_id"],
        "name": user["name"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)