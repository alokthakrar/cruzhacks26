from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .config import get_settings

settings = get_settings()

client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo():
    """Initialize MongoDB connection."""
    global client, db
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.database_name]
    # Verify connection
    await client.admin.command("ping")
    print(f"Connected to MongoDB: {settings.database_name}")


async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo first.")
    return db


def get_user_collection():
    """Get user_state collection."""
    return get_database()["user_state"]


def get_sessions_collection():
    """Get sessions collection."""
    return get_database()["sessions"]


def get_subjects_collection():
    """Get subjects collection."""
    return get_database()["subjects"]


def get_pdfs_collection():
    """Get extracted_pdfs collection."""
    return get_database()["extracted_pdfs"]


def get_questions_collection():
    """Get questions collection."""
    return get_database()["questions"]
