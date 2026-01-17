from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Session(BaseModel):
    """A learning session for a subject."""

    id: str = Field(alias="_id")
    user_id: str
    subject_id: str
    problem_image: Optional[str] = None  # base64 or URL
    timestamp: datetime
    status: Literal["in_progress", "completed"]
    error_types: List[str] = []
    steps_attempted: int = 0

    class Config:
        populate_by_name = True


class SessionCreate(BaseModel):
    """Request body for creating a session."""

    problem_image: Optional[str] = None  # base64 string


class SessionUpdate(BaseModel):
    """Request body for updating a session."""

    status: Optional[Literal["in_progress", "completed"]] = None
    steps_attempted: Optional[int] = None
