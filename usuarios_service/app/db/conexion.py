from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings

class DataBase:
    client: AsyncIOMotorClient = None

db = DataBase()

async def connect_to_mongo(db_name: str, models: list):
    db.client = AsyncIOMotorClient(settings.MONGO_CONNECTION_STRING)
    await init_beanie(
        database=db.client[db_name], 
        document_models=models
    )

async def close_mongo_connection():
    if db.client:
        db.client.close()