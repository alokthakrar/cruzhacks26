from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box for a question on a page."""
    x: int
    y: int
    width: int
    height: int


class PDFQuestion(BaseModel):
    """A question extracted from a PDF."""
    id: str = Field(alias="_id")
    pdf_id: str
    created_by: str
    subject_id: Optional[str] = None
    page_number: int
    question_number: int
    text_content: str
    latex_content: Optional[str] = None
    question_type: str  # e.g., "derivative", "integral", "word_problem"
    difficulty_estimate: Optional[str] = None  # "easy", "medium", "hard"
    cropped_image: str  # base64 encoded PNG of the question
    bounding_box: BoundingBox
    extraction_confidence: float
    created_at: datetime

    class Config:
        populate_by_name = True


class PDFDocument(BaseModel):
    """A PDF document uploaded by a user."""
    id: str = Field(alias="_id")
    user_id: str
    subject_id: Optional[str] = None
    filename: str
    total_pages: int
    status: str  # "processing", "completed", "failed"
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        populate_by_name = True


class PDFUploadResponse(BaseModel):
    """Response after uploading a PDF."""
    pdf_id: str
    filename: str
    subject_id: Optional[str] = None
    status: str
    message: str
    total_pages: int
    question_count: int


class QuestionListResponse(BaseModel):
    """Paginated list of questions."""
    questions: List[PDFQuestion]
    total: int
    page: int
    limit: int
