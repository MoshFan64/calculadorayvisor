from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
 
# Configuración de conexión (puedes ajustar la URI)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "matrices_db"
COLLECTION_NAME = "execution_logs"
 
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
logs_collection = db[COLLECTION_NAME]
 
async def registrar_log(session_id: str, operacion: dict, exito: bool) -> str:
    log_document = {
        "session_id": session_id,
        "fecha_uso": datetime.utcnow(),
        "operacion": operacion,  # Se guarda directamente como documento/JSON
        "resultado": exito
    }
    resultado = await logs_collection.insert_one(log_document)
    return str(resultado.inserted_id)