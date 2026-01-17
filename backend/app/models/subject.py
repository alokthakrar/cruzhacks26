from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Subject(BaseModel):
    """A math subject created by a user."""

    id: str = Field(alias="_id")
    user_id: str
    name: str
    created_at: datetime
    last_accessed: datetime

    class Config:
        populate_by_name = True


class SubjectCreate(BaseModel):
    """Request body for creating a subject."""

    name: str


class SubjectUpdate(BaseModel):
    """Request body for updating a subject."""

    name: Optional[str] = None
