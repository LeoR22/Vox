from fastapi import FastAPI, HTTPException, Header
from pymongo import MongoClient
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from bson import ObjectId
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Bookmark Service")

# Configuración de MongoDB con reintentos
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/bookmark_db")
for attempt in range(10):
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        logger.info(f"Conexión a MongoDB establecida correctamente (intento {attempt + 1})")
        break
    except Exception as e:
        logger.error(f"Intento {attempt + 1} fallido: {str(e)}")
        if attempt < 9:
            time.sleep(5)
        else:
            raise Exception(f"No se pudo conectar a MongoDB tras 10 intentos: {str(e)}")

db = client["bookmark_db"]
bookmarks_collection = db["bookmarks"]

# Modelo Pydantic
class BookmarkData(BaseModel):
    user_id: str
    post_id: str

# Validar ObjectId
def is_valid_objectid(oid: str) -> bool:
    try:
        ObjectId(oid)
        return True
    except Exception:
        return False

# Ruta para guardar/eliminar un bookmark
@app.post("/bookmarks")
async def toggle_bookmark(bookmark_data: BookmarkData, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    if not is_valid_objectid(bookmark_data.post_id):
        raise HTTPException(status_code=400, detail="Invalid post_id format")

    try:
        # Verificar si ya existe el bookmark
        existing_bookmark = bookmarks_collection.find_one({
            "user_id": bookmark_data.user_id,
            "post_id": bookmark_data.post_id
        })

        if existing_bookmark:
            # Si existe, eliminar
            result = bookmarks_collection.delete_one({
                "user_id": bookmark_data.user_id,
                "post_id": bookmark_data.post_id
            })
            if result.deleted_count == 0:
                raise HTTPException(status_code=500, detail="Failed to remove bookmark")
            logger.info(f"Bookmark eliminado para post_id: {bookmark_data.post_id}, user_id: {bookmark_data.user_id}")
            return {"message": "Bookmark removed successfully", "action": "removed"}
        else:
            # Si no existe, crear
            bookmark_dict = bookmark_data.dict()
            bookmark_dict["created_at"] = datetime.utcnow()
            result = bookmarks_collection.insert_one(bookmark_dict)
            if not result.inserted_id:
                raise HTTPException(status_code=500, detail="Failed to add bookmark")
            logger.info(f"Bookmark añadido para post_id: {bookmark_data.post_id}, user_id: {bookmark_data.user_id}")
            return {"message": "Bookmark added successfully", "action": "added"}
    except Exception as e:
        logger.error(f"Error al procesar bookmark: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing bookmark: {str(e)}")

# Ruta para obtener todos los bookmarks de un usuario
@app.get("/bookmarks/user/{user_id}")
async def get_user_bookmarks(user_id: str, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    try:
        bookmarks = list(bookmarks_collection.find({"user_id": user_id}))
        # Convertir ObjectId a string para serialización JSON
        for bookmark in bookmarks:
            bookmark["_id"] = str(bookmark["_id"])
        logger.info(f"Obtenidos {len(bookmarks)} bookmarks para user_id: {user_id}")
        return bookmarks
    except Exception as e:
        logger.error(f"Error al obtener bookmarks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching bookmarks: {str(e)}")

# Ruta para verificar si un post está guardado por un usuario
@app.get("/bookmarks/check")
async def check_bookmark(user_id: str, post_id: str, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    if not is_valid_objectid(post_id):
        raise HTTPException(status_code=400, detail="Invalid post_id format")

    try:
        bookmark = bookmarks_collection.find_one({
            "user_id": user_id,
            "post_id": post_id
        })
        is_bookmarked = bookmark is not None
        logger.info(f"Check bookmark para post_id: {post_id}, user_id: {user_id}: {is_bookmarked}")
        return {"is_bookmarked": is_bookmarked}
    except Exception as e:
        logger.error(f"Error al verificar bookmark: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking bookmark: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)