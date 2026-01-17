from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates for a question region."""

    x: int
    y: int
    width: int
    height: int


class QuestionBase(BaseModel):
    """Base fields for a question."""

    page_number: int
    question_number: int
    text_content: str
    latex_content: Optional[str] = None
    question_type: str  # integral, derivative, equation, word_problem, other
    difficulty_estimate: Optional[str] = None  # easy, medium, hard
    bounding_box: BoundingBox
    extraction_confidence: float


class Question(QuestionBase):
    """A question extracted from a PDF."""

    id: str = Field(alias="_id")
    pdf_id: str
    user_id: str
    subject_id: Optional[str] = None  # Associated subject for pooling questions
    cropped_image: str  # base64 encoded PNG
    created_at: datetime

    class Config:
        populate_by_name = True


class QuestionCreate(QuestionBase):
    """Internal model for creating a question during extraction."""

    cropped_image: str  # base64 encoded PNG


class ExtractedPDF(BaseModel):
    """Metadata for an extracted PDF document."""

    id: str = Field(alias="_id")
    user_id: str
    subject_id: Optional[str] = None  # Associated subject for pooling questions
    original_filename: str
    upload_timestamp: datetime
    total_pages: int
    processing_status: Literal["pending", "processing", "completed", "failed"]
    processing_error: Optional[str] = None
    question_count: int = 0

    class Config:
        populate_by_name = True


class ExtractedPDFCreate(BaseModel):
    """Internal model for creating a PDF record."""

    original_filename: str


class PDFUploadResponse(BaseModel):
    """Response after uploading a PDF."""

    pdf_id: str
    filename: str
    subject_id: Optional[str] = None
    status: str
    message: str
    total_pages: int = 0
    question_count: int = 0


class QuestionsListResponse(BaseModel):
    """Response for listing questions."""

    questions: List[Question]
    total: int
    page: int
    limit: int
