from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Subject(BaseModel):
    """A math subject created by a user."""

    id: str = Field(alias="_id")
    user_id: str
    name: str
    color: str = "Blue"  # Folder accent color
    created_at: datetime
    last_accessed: datetime

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class SubjectCreate(BaseModel):
    """Request body for creating a subject."""

    name: str
    color: str = "Blue"


class SubjectUpdate(BaseModel):
    """Request body for updating a subject."""

    name: Optional[str] = None
    color: Optional[str] = None
