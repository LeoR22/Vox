from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from typing import Optional
import uuid
from pymongo import MongoClient
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import time
import logging
import bcrypt
from fastapi.responses import FileResponse
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="User Service")

# Conexión a MongoDB con reintentos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/user_db")
for attempt in range(10):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # Verifica la conexión
        logger.info(f"Conexión a MongoDB establecida correctamente (intento {attempt + 1})")
        break
    except Exception as e:
        logger.error(f"Intento {attempt + 1} fallido: {str(e)}")
        if attempt < 9:
            time.sleep(5)
        else:
            raise Exception(f"No se pudo conectar a MongoDB tras 10 intentos: {str(e)}")

db = client["user_db"]
users_collection = db["users"]

# Modelo Pydantic para validación
class User(BaseModel):
    email: str
    password: str
    name: str
    bio: str
    user_id: str

# Función para hashear contraseña
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Crear directorio uploads si no existe
os.makedirs("/app/uploads", exist_ok=True)

# Ruta para crear usuario
@app.post("/users")
async def create_user(user: User):
    user_dict = user.dict()
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    user_dict["password"] = hash_password(user.password)
    user_dict["created_at"] = datetime.utcnow().isoformat()
    result = users_collection.insert_one(user_dict)
    return {"message": "User created successfully", "user_id": user.user_id}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])
    return user

@app.put("/users/{user_id}")
async def update_user(
    user_id: str,
    profile_image: Optional[UploadFile] = File(None),
    cover_image: Optional[UploadFile] = File(None),
    bio: Optional[str] = Form(None),
    name: Optional[str] = Form(None)
):
    update_data = {}
    if profile_image:
        profile_image_filename = f"{uuid.uuid4()}_{profile_image.filename}"
        profile_image_path = os.path.join("/app/uploads", profile_image_filename)
        with open(profile_image_path, "wb") as f:
            f.write(await profile_image.read())
        update_data["profile_image_url"] = f"/uploads/{profile_image_filename}"
    if cover_image:
        cover_image_filename = f"{uuid.uuid4()}_{cover_image.filename}"
        cover_image_path = os.path.join("/app/uploads", cover_image_filename)
        with open(cover_image_path, "wb") as f:
            f.write(await cover_image.read())
        update_data["cover_image_url"] = f"/uploads/{cover_image_filename}"
    if bio is not None:
        if len(bio) > 160:  # Validación de longitud máxima
            raise HTTPException(status_code=400, detail="La biografía no puede exceder los 160 caracteres")
        update_data["bio"] = bio
    if name is not None:
        if len(name) > 50:  # Validación de longitud máxima
            raise HTTPException(status_code=400, detail="El nombre no puede exceder los 50 caracteres")
        if len(name) < 1:
            raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")
        update_data["name"] = name

    if update_data:
        result = users_collection.update_one({"user_id": user_id}, {"$set": update_data})
        if result.modified_count:
            return {"message": "Perfil actualizado con éxito"}
        else:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
    raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")

@app.get("/uploads/{filename}")
async def serve_uploaded_file(filename: str):
    file_path = os.path.join("/app/uploads", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)