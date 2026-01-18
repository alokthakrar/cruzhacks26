"""
Migration script to rename user_id to created_by in questions collection.

This fixes the Pydantic validation error where questions were inserted with
'user_id' but the Question model expects 'created_by'.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def migrate():
    # Connect to MongoDB
    mongodb_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME", "adaptive_tutor")
    
    client = AsyncIOMotorClient(mongodb_uri)
    db = client[database_name]
    questions_collection = db["questions"]
    
    # Count documents that need migration
    count = await questions_collection.count_documents({"user_id": {"$exists": True}})
    print(f"Found {count} questions with 'user_id' field that need migration")
    
    if count == 0:
        print("No migration needed - all questions already have 'created_by' field")
        client.close()
        return
    
    # Rename user_id to created_by
    result = await questions_collection.update_many(
        {"user_id": {"$exists": True}},
        {"$rename": {"user_id": "created_by"}}
    )
    
    print(f"✅ Migration completed!")
    print(f"   - Modified {result.modified_count} documents")
    print(f"   - Matched {result.matched_count} documents")
    
    # Verify migration
    remaining = await questions_collection.count_documents({"user_id": {"$exists": True}})
    migrated = await questions_collection.count_documents({"created_by": {"$exists": True}})
    
    print(f"\nVerification:")
    print(f"   - Documents still with 'user_id': {remaining}")
    print(f"   - Documents now with 'created_by': {migrated}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
