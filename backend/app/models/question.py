from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Question(BaseModel):
    """A practice question with Elo rating and concept tagging."""
    
    id: str = Field(alias="_id")
    subject_id: str = Field(description="Reference to subjects collection")
    concept_id: str = Field(description="Primary concept this question tests")
    related_concepts: List[str] = Field(
        default_factory=list,
        description="Secondary concepts involved (for multi-concept questions)"
    )
    question_text: Optional[str] = Field(
        default=None,
        description="Text content of the question"
    )
    question_image: Optional[str] = Field(
        default=None,
        description="Base64 image or URL to question image"
    )
    answer_key: Optional[str] = Field(
        default=None,
        description="Correct answer (for auto-grading)"
    )
    solution_steps: Optional[List[str]] = Field(
        default=None,
        description="Step-by-step solution explanation"
    )
    elo_rating: int = Field(
        default=1200,
        ge=0,
        description="Question difficulty rating (updated via Elo)"
    )
    times_attempted: int = Field(
        default=0,
        ge=0,
        description="Total number of attempts across all users"
    )
    times_correct: int = Field(
        default=0,
        ge=0,
        description="Total number of correct answers"
    )
    difficulty_label: Literal["easy", "medium", "hard"] = Field(
        default="medium",
        description="Human-assigned difficulty (initial estimate)"
    )
    created_by: str = Field(description="user_id who created this question")
    created_at: datetime
    last_attempted: Optional[datetime] = Field(
        default=None,
        description="Most recent attempt timestamp"
    )
    
    class Config:
        populate_by_name = True
    
    @property
    def success_rate(self) -> float:
        """Calculate the percentage of correct answers."""
        if self.times_attempted == 0:
            return 0.0
        return self.times_correct / self.times_attempted


class QuestionCreate(BaseModel):
    """Request body for creating a question."""
    
    subject_id: str
    concept_id: str
    related_concepts: List[str] = []
    question_text: Optional[str] = None
    question_image: Optional[str] = None
    answer_key: Optional[str] = None
    solution_steps: Optional[List[str]] = None
    difficulty_label: Literal["easy", "medium", "hard"] = "medium"


class QuestionUpdate(BaseModel):
    """Request body for updating a question."""
    
    question_text: Optional[str] = None
    question_image: Optional[str] = None
    answer_key: Optional[str] = None
    solution_steps: Optional[List[str]] = None
    difficulty_label: Optional[Literal["easy", "medium", "hard"]] = None


class QuestionResponse(BaseModel):
    """Response model for question queries."""
    
    id: str
    subject_id: str
    concept_id: str
    concept_name: Optional[str] = None  # Populated from knowledge graph
    question_text: Optional[str]
    question_image: Optional[str]
    elo_rating: int
    difficulty_label: Literal["easy", "medium", "hard"]
    success_rate: float
    times_attempted: int
