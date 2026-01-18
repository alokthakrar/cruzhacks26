from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from bson import ObjectId

from ..auth import get_current_user_id
from ..database import get_pdfs_collection, get_questions_collection, get_subjects_collection
from ..models.question import (
    ExtractedPDF,
    PDFQuestion,
    PDFUploadResponse,
    PDFQuestionsListResponse,
)
from ..services.pdf_extractor import pdf_extractor_service
from ..services.knowledge_graph_generator import knowledge_graph_generator

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    pdf: UploadFile = File(..., description="PDF file containing math problems"),
    subject_id: Optional[str] = Form(None, description="Subject ID to associate questions with"),
    user_id: str = Depends(get_current_user_id),
):
    """
    Upload a PDF and extract math questions from it.

    The PDF is processed page-by-page using Gemini 2.5 Flash to:
    1. Identify individual questions
    2. Extract text and LaTeX content
    3. Crop question images from the page

    Optionally associate with a subject to pool questions together.

    Returns the PDF ID and extraction results.
    """
    # Validate subject_id if provided
    if subject_id:
        subjects_collection = get_subjects_collection()
        subject = await subjects_collection.find_one({"_id": subject_id, "user_id": user_id})
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )
    # Validate file type
    if not pdf.content_type or pdf.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF",
        )

    # Read PDF bytes
    pdf_bytes = await pdf.read()

    if len(pdf_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty PDF file",
        )

    # Generate PDF ID
    pdf_id = str(ObjectId())
    filename = pdf.filename or "untitled.pdf"

    # Create initial PDF record
    pdfs_collection = get_pdfs_collection()
    pdf_doc = {
        "_id": pdf_id,
        "user_id": user_id,
        "subject_id": subject_id,
        "original_filename": filename,
        "upload_timestamp": datetime.utcnow(),
        "total_pages": 0,
        "processing_status": "processing",
        "processing_error": None,
        "page_images": [],
    }
    await pdfs_collection.insert_one(pdf_doc)

    try:
        # Process the PDF
        result = pdf_extractor_service.process_pdf(pdf_bytes, user_id, filename)

        if result["error"]:
            # Update PDF record with error
            await pdfs_collection.update_one(
                {"_id": pdf_id},
                {
                    "$set": {
                        "processing_status": "failed",
                        "processing_error": result["error"],
                    }
                },
            )
            return PDFUploadResponse(
                pdf_id=pdf_id,
                filename=filename,
                subject_id=subject_id,
                status="failed",
                message=result["error"],
                total_pages=0,
                question_count=0,
            )

        # Store extracted questions
        questions_collection = get_questions_collection()
        question_count = 0

        # Tag questions with concepts if subject_id is provided
        concept_ids = []
        if subject_id and result["questions"]:
            # Prepare questions for batch tagging
            questions_for_tagging = [
                {
                    "text_content": q.get("text_content", ""),
                    "latex_content": q.get("latex_content")
                }
                for q in result["questions"]
            ]
            concept_ids = await knowledge_graph_generator.tag_questions_batch(
                questions_for_tagging,
                subject_id
            )
            print(f"Tagged {len(concept_ids)} questions with concepts: {concept_ids}")

        for i, q in enumerate(result["questions"]):
            # Get concept_id from batch tagging result, or None
            concept_id = concept_ids[i] if i < len(concept_ids) else None

            question_doc = {
                "_id": str(ObjectId()),
                "pdf_id": pdf_id,
                "created_by": user_id,
                "subject_id": subject_id,
                "concept_id": concept_id,
                "page_number": q.get("page_number", 1),
                "question_number": q.get("question_number", 1),
                "text_content": q.get("text_content", ""),
                "latex_content": q.get("latex_content"),
                "question_type": q.get("question_type", "other"),
                "difficulty_estimate": q.get("difficulty_estimate"),
                "bounding_box": q.get("bounding_box", {"x": 0, "y": 0, "width": 100, "height": 50}),
                "cropped_image": q.get("cropped_image", ""),
                "extraction_confidence": q.get("confidence", 0.0),
                "elo_rating": 1200,
                "times_attempted": 0,
                "times_correct": 0,
                "created_at": datetime.utcnow(),
            }
            await questions_collection.insert_one(question_doc)
            question_count += 1

        # Update PDF record with success
        await pdfs_collection.update_one(
            {"_id": pdf_id},
            {
                "$set": {
                    "total_pages": result["total_pages"],
                    "processing_status": "completed",
                    "page_images": result["page_images"],
                }
            },
        )

        return PDFUploadResponse(
            pdf_id=pdf_id,
            filename=filename,
            subject_id=subject_id,
            status="completed",
            message=f"Successfully extracted {question_count} questions from {result['total_pages']} pages",
            total_pages=result["total_pages"],
            question_count=question_count,
        )

    except Exception as e:
        # Update PDF record with error
        await pdfs_collection.update_one(
            {"_id": pdf_id},
            {
                "$set": {
                    "processing_status": "failed",
                    "processing_error": str(e),
                }
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF processing failed: {str(e)}",
        )


@router.get("", response_model=List[ExtractedPDF])
async def list_pdfs(user_id: str = Depends(get_current_user_id)):
    """List all PDFs uploaded by the current user."""
    pdfs_collection = get_pdfs_collection()
    questions_collection = get_questions_collection()

    cursor = pdfs_collection.find({"user_id": user_id}).sort("upload_timestamp", -1)
    pdfs = await cursor.to_list(length=100)

    # Add question counts
    result = []
    for pdf in pdfs:
        question_count = await questions_collection.count_documents({"pdf_id": pdf["_id"]})
        pdf["question_count"] = question_count
        result.append(ExtractedPDF(**pdf))

    return result


@router.get("/{pdf_id}", response_model=ExtractedPDF)
async def get_pdf(
    pdf_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get metadata for a specific PDF."""
    pdfs_collection = get_pdfs_collection()
    questions_collection = get_questions_collection()

    pdf = await pdfs_collection.find_one({"_id": pdf_id, "user_id": user_id})

    if not pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found",
        )

    # Add question count
    question_count = await questions_collection.count_documents({"pdf_id": pdf_id})
    pdf["question_count"] = question_count

    return ExtractedPDF(**pdf)


@router.get("/{pdf_id}/questions", response_model=PDFQuestionsListResponse)
async def get_pdf_questions(
    pdf_id: str,
    user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    page_number: int = Query(None, ge=1, description="Filter by PDF page number"),
):
    """
    Get extracted questions for a PDF.

    Supports pagination and filtering by page number.
    """
    pdfs_collection = get_pdfs_collection()
    questions_collection = get_questions_collection()

    # Verify PDF exists and belongs to user
    pdf = await pdfs_collection.find_one({"_id": pdf_id, "user_id": user_id})
    if not pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found",
        )

    # Build query
    query = {"pdf_id": pdf_id}
    if page_number is not None:
        query["page_number"] = page_number

    # Get total count
    total = await questions_collection.count_documents(query)

    # Get paginated results
    skip = (page - 1) * limit
    cursor = questions_collection.find(query).sort(
        [("page_number", 1), ("question_number", 1)]
    ).skip(skip).limit(limit)

    questions = await cursor.to_list(length=limit)

    return PDFQuestionsListResponse(
        questions=[PDFQuestion(**q) for q in questions],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{pdf_id}/questions/{question_id}", response_model=PDFQuestion)
async def get_question(
    pdf_id: str,
    question_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a specific question."""
    pdfs_collection = get_pdfs_collection()
    questions_collection = get_questions_collection()

    # Verify PDF exists and belongs to user
    pdf = await pdfs_collection.find_one({"_id": pdf_id, "user_id": user_id})
    if not pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found",
        )

    question = await questions_collection.find_one(
        {"_id": question_id, "pdf_id": pdf_id}
    )

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    return PDFQuestion(**question)


@router.delete("/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pdf(
    pdf_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a PDF and all its extracted questions."""
    pdfs_collection = get_pdfs_collection()
    questions_collection = get_questions_collection()

    # Verify PDF exists and belongs to user
    pdf = await pdfs_collection.find_one({"_id": pdf_id, "user_id": user_id})
    if not pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found",
        )

    # Delete all questions for this PDF
    await questions_collection.delete_many({"pdf_id": pdf_id})

    # Delete the PDF record
    await pdfs_collection.delete_one({"_id": pdf_id})

    return None


@router.get("/subject/{subject_id}/questions", response_model=PDFQuestionsListResponse)
async def get_subject_questions(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    question_type: Optional[str] = Query(None, description="Filter by question type"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
):
    """
    Get all questions for a subject (pooled from all PDFs).

    This endpoint returns questions from all PDFs associated with the given subject,
    allowing you to view all extracted problems in one place.
    """
    subjects_collection = get_subjects_collection()
    questions_collection = get_questions_collection()

    # Verify subject exists and belongs to user
    subject = await subjects_collection.find_one({"_id": subject_id, "user_id": user_id})
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    # Build query
    query = {"subject_id": subject_id, "created_by": user_id}
    if question_type:
        query["question_type"] = question_type
    if difficulty:
        query["difficulty_estimate"] = difficulty

    # Get total count
    total = await questions_collection.count_documents(query)

    # Get paginated results
    skip = (page - 1) * limit
    cursor = questions_collection.find(query).sort(
        [("created_at", -1), ("page_number", 1), ("question_number", 1)]
    ).skip(skip).limit(limit)

    questions = await cursor.to_list(length=limit)

    return PDFQuestionsListResponse(
        questions=[PDFQuestion(**q) for q in questions],
        total=total,
        page=page,
        limit=limit,
    )
