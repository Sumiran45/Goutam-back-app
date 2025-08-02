import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "fastapi_app")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def init_indexes():
    """Create necessary indexes"""
    await db.doctors.create_index([("contact_info.location", "2dsphere")])
    
    # Symptom collection indexes for better performance
    await db.symptoms.create_index([("user_id", 1), ("date", -1)])  # Compound index for user queries
    await db.symptoms.create_index([("date", -1)])  # Date index for time-based queries
    await db.symptoms.create_index([("user_id", 1)])  # User index for user-specific queries
