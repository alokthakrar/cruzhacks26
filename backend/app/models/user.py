from datetime import datetime
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class Weakness(BaseModel):
    """Tracks a specific weakness with confidence scoring."""

    error_count: int = 0
    last_seen: Optional[datetime] = None
    confidence: float = 0.0  # 0.0 to 1.0


class UserState(BaseModel):
    """User profile with weakness tracking."""

    id: str = Field(alias="_id")
    name: str
    email: Optional[str] = None
    weaknesses: Dict[str, Weakness] = {}
    created_at: datetime

    class Config:
        populate_by_name = True


class UserCreate(BaseModel):
    """Request body for creating a user."""

    name: str
    email: Optional[str] = None


class UserUpdate(BaseModel):
    """Request body for updating a user."""

    name: Optional[str] = None
    email: Optional[str] = None


class WeaknessRecord(BaseModel):
    """Request body for recording a weakness."""

    weakness_type: str  # e.g., "chain_rule", "negative_signs"


class Session(BaseModel):
    """A learning session record."""

    id: str = Field(alias="_id")
    user_id: str
    problem_id: str
    timestamp: datetime
    status: Literal["passed", "failed"]
    error_type: Optional[str] = None
    steps_attempted: int = 0

    class Config:
        populate_by_name = True


class SessionCreate(BaseModel):
    """Request body for creating a session."""

    problem_id: str
    status: Literal["passed", "failed"]
    error_type: Optional[str] = None
    steps_attempted: int = 0
