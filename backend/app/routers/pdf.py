from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from bson import ObjectId
import base64
import io
from PIL import Image

from ..auth import get_current_user_id
from ..database import get_database
from ..models.pdf import (
    PDFDocument,
    PDFQuestion,
    PDFUploadResponse,
    QuestionListResponse,
    BoundingBox
)

router = APIRouter(prefix="/pdf", tags=["PDF"])


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    pdf: UploadFile = File(...),
    subject_id: str = Form(...),
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_database)
):
    """
    Upload a PDF and extract questions.
    
    For now, returns fake data until OCR/parsing is implemented.
    """
    if not pdf.content_type or pdf.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
    
    pdf_bytes = await pdf.read()
    
    if len(pdf_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty PDF file"
        )
    
    # Create PDF document record
    pdf_id = str(ObjectId())
    pdf_doc = {
        "_id": pdf_id,
        "user_id": user_id,
        "subject_id": subject_id,
        "filename": pdf.filename,
        "total_pages": 2,  # TODO: Get actual page count
        "status": "completed",
        "uploaded_at": datetime.utcnow(),
        "processed_at": datetime.utcnow(),
    }
    
    await db["pdf_documents"].insert_one(pdf_doc)
    
    # TODO: Actually parse PDF and extract questions
    # For now, create fake questions
    fake_questions = create_fake_questions(pdf_id, user_id, subject_id)
    
    # Insert fake questions
    if fake_questions:
        await db["pdf_questions"].insert_many([q for q in fake_questions])
    
    return PDFUploadResponse(
        pdf_id=pdf_id,
        filename=pdf.filename,
        subject_id=subject_id,
        status="completed",
        message=f"Successfully extracted {len(fake_questions)} questions from 2 pages (using fake data for now)",
        total_pages=2,
        question_count=len(fake_questions)
    )


@router.get("/subject/{subject_id}/questions")
async def get_subject_questions(
    subject_id: str,
    page: int = 1,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_database)
):
    """Get all questions for a subject (folder)."""
    skip = (page - 1) * limit
    
    # Query questions
    cursor = db["pdf_questions"].find({
        "user_id": user_id,
        "subject_id": subject_id
    }).sort("created_at", -1).skip(skip).limit(limit)
    
    questions = await cursor.to_list(length=limit)
    
    # Count total
    total = await db["pdf_questions"].count_documents({
        "user_id": user_id,
        "subject_id": subject_id
    })
    
    # Convert _id to id for frontend
    result_questions = []
    for q in questions:
        q['id'] = q.pop('_id')  # Rename _id to id
        q['created_at'] = q['created_at'].isoformat() if 'created_at' in q else None
        result_questions.append(q)
    
    return {
        "questions": result_questions,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/{pdf_id}/questions/{question_id}", response_model=PDFQuestion)
async def get_question(
    pdf_id: str,
    question_id: str,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_database)
):
    """Get a specific question by ID."""
    question = await db["pdf_questions"].find_one({
        "_id": question_id,
        "pdf_id": pdf_id,
        "user_id": user_id
    })
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    return PDFQuestion(**question)


# Helper function to create fake questions for testing
def create_fake_questions(pdf_id: str, user_id: str, subject_id: str = None) -> list:
    """Create fake questions for testing until PDF parsing is implemented."""
    
    # Create a simple blank image as base64
    img = Image.new('RGB', (100, 50), color='white')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    now = datetime.utcnow()
    
    questions = [
        {
            "_id": str(ObjectId()),
            "pdf_id": pdf_id,
            "user_id": user_id,
            "subject_id": subject_id,
            "page_number": 1,
            "question_number": 1,
            "text_content": "Find the derivative of f(x) = 3x² + 2x - 5",
            "question_type": "derivative",
            "difficulty_estimate": "medium",
            "cropped_image": img_base64,
            "bounding_box": {"x": 0, "y": 0, "width": 100, "height": 50},
            "extraction_confidence": 0.95,
            "created_at": now,
        },
        {
            "_id": str(ObjectId()),
            "pdf_id": pdf_id,
            "user_id": user_id,
            "subject_id": subject_id,
            "page_number": 1,
            "question_number": 2,
            "text_content": "Evaluate the integral: ∫(4x³ - 2x + 1)dx",
            "question_type": "integral",
            "difficulty_estimate": "medium",
            "cropped_image": img_base64,
            "bounding_box": {"x": 0, "y": 60, "width": 100, "height": 50},
            "extraction_confidence": 0.92,
            "created_at": now,
        },
        {
            "_id": str(ObjectId()),
            "pdf_id": pdf_id,
            "user_id": user_id,
            "subject_id": subject_id,
            "page_number": 2,
            "question_number": 3,
            "text_content": "Using the chain rule, find dy/dx for y = sin(x²)",
            "question_type": "derivative",
            "difficulty_estimate": "hard",
            "cropped_image": img_base64,
            "bounding_box": {"x": 0, "y": 0, "width": 100, "height": 50},
            "extraction_confidence": 0.88,
            "created_at": now,
        },
        {
            "_id": str(ObjectId()),
            "pdf_id": pdf_id,
            "user_id": user_id,
            "subject_id": subject_id,
            "page_number": 2,
            "question_number": 4,
            "text_content": "Find the critical points of f(x) = x³ - 6x² + 9x + 2",
            "question_type": "equation",
            "difficulty_estimate": "hard",
            "cropped_image": img_base64,
            "bounding_box": {"x": 0, "y": 60, "width": 100, "height": 50},
            "extraction_confidence": 0.90,
            "created_at": now,
        },
    ]
    
    return questions
