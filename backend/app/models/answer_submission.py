from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AnswerSubmission(BaseModel):
    """Records a single answer submission event with BKT/Elo updates."""
    
    id: str = Field(alias="_id")
    user_id: str = Field(description="Reference to users collection")
    subject_id: str = Field(description="Reference to subjects collection")
    question_id: str = Field(description="Reference to questions collection")
    concept_id: str = Field(description="Primary concept being tested")
    timestamp: datetime
    
    # Answer data
    is_correct: bool = Field(description="Whether the answer was correct")
    time_taken_seconds: Optional[int] = Field(
        default=None,
        ge=0,
        description="Time spent on this question"
    )
    user_answer: Optional[str] = Field(
        default=None,
        description="User's submitted answer (for review)"
    )
    
    # BKT state changes
    P_L_before: float = Field(
        ge=0.0,
        le=1.0,
        description="Mastery probability before this question"
    )
    P_L_after: float = Field(
        ge=0.0,
        le=1.0,
        description="Mastery probability after this question"
    )
    P_knew: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Posterior probability they knew it (calculated via Bayes)"
    )
    
    # Elo state changes
    student_elo_before: int = Field(
        ge=0,
        description="Student's Elo rating before this question"
    )
    student_elo_after: int = Field(
        ge=0,
        description="Student's Elo rating after this question"
    )
    question_elo_before: int = Field(
        ge=0,
        description="Question's Elo rating before this submission"
    )
    question_elo_after: int = Field(
        ge=0,
        description="Question's Elo rating after this submission"
    )
    
    # Mastery tracking
    mastery_status_before: str = Field(
        description="Mastery status before (locked/learning/mastered)"
    )
    mastery_status_after: str = Field(
        description="Mastery status after (locked/learning/mastered)"
    )
    
    # Analytics
    observations_count: int = Field(
        ge=0,
        description="Total observations for this concept after this submission"
    )
    
    class Config:
        populate_by_name = True


class MistakeRecord(BaseModel):
    """A single mistake made during problem solving."""
    step_number: int
    error_type: str  # "arithmetic", "algebraic", "notation", "conceptual"
    error_message: Optional[str] = None
    from_expr: Optional[str] = None
    to_expr: Optional[str] = None


class AnswerSubmissionCreate(BaseModel):
    """Request body for submitting an answer."""

    question_id: str
    is_correct: bool
    time_taken_seconds: Optional[int] = None
    user_answer: Optional[str] = None

    # Mistake tracking
    mistake_count: int = Field(default=0, ge=0, description="Total mistakes made before solving")
    mistakes: list[MistakeRecord] = Field(default_factory=list, description="Details of each mistake")


class AnswerSubmissionResponse(BaseModel):
    """Response after submitting an answer (includes updates)."""
    
    submission_id: str
    is_correct: bool
    
    # Changes
    mastery_change: float = Field(
        description="Change in P(L): P_L_after - P_L_before"
    )
    elo_change: int = Field(
        description="Change in student Elo: student_elo_after - student_elo_before"
    )
    
    # New state
    new_mastery_probability: float
    new_mastery_status: str
    new_student_elo: int
    
    # Unlocks/achievements
    unlocked_concepts: list[str] = Field(
        default_factory=list,
        description="New concepts unlocked as a result of this submission"
    )
    concept_mastered: bool = Field(
        default=False,
        description="True if this submission pushed concept to 'mastered'"
    )
    
    # Feedback
    feedback_message: str = Field(
        description="Human-readable message about progress"
    )
    
    # Next action
    recommended_next_concept: Optional[str] = Field(
        default=None,
        description="concept_id to focus on next"
    )
