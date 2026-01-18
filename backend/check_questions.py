"""
Quick script to check if questions are in the database
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def check_questions():
    mongodb_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME", "adaptive_tutor")
    
    client = AsyncIOMotorClient(mongodb_uri)
    db = client[database_name]
    
    # Check questions collection
    questions_count = await db["questions"].count_documents({})
    print(f"Total questions in database: {questions_count}")
    
    # Check by subject
    subject_id = "696c822c9c49006c79590379"
    subject_questions = await db["questions"].count_documents({"subject_id": subject_id})
    print(f"Questions for subject {subject_id}: {subject_questions}")
    
    # Sample a question
    sample = await db["questions"].find_one({"subject_id": subject_id})
    if sample:
        print(f"\nSample question:")
        print(f"  _id: {sample.get('_id')}")
        print(f"  subject_id: {sample.get('subject_id')}")
        print(f"  concept_id: {sample.get('concept_id')}")
        print(f"  created_by: {sample.get('created_by')}")
        print(f"  text_content: {sample.get('text_content', '')[:100]}...")
        print(f"  Fields: {list(sample.keys())}")
    else:
        print("\nNo questions found for this subject")
    
    # Check PDF questions collection
    pdf_questions_count = await db["pdf_questions"].count_documents({})
    print(f"\n\nTotal PDF questions in database: {pdf_questions_count}")
    
    subject_pdf_questions = await db["pdf_questions"].count_documents({"subject_id": subject_id})
    print(f"PDF questions for subject {subject_id}: {subject_pdf_questions}")
    
    # Sample a PDF question
    pdf_sample = await db["pdf_questions"].find_one({"subject_id": subject_id})
    if pdf_sample:
        print(f"\nSample PDF question:")
        print(f"  _id: {pdf_sample.get('_id')}")
        print(f"  subject_id: {pdf_sample.get('subject_id')}")
        print(f"  user_id: {pdf_sample.get('user_id')}")
        print(f"  text_content: {pdf_sample.get('text_content', '')[:100]}...")
        print(f"  Fields: {list(pdf_sample.keys())}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_questions())
