from datetime import datetime
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field


class ConceptMastery(BaseModel):
    """Tracks a user's mastery state for a single concept."""
    
    P_L: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Current probability the user has mastered this concept"
    )
    P_T: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Personalized learn rate (can adapt over time)"
    )
    P_G: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Personalized guess rate"
    )
    P_S: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Personalized slip rate"
    )
    observations: int = Field(
        default=0,
        ge=0,
        description="Number of questions answered for this concept"
    )
    correct_count: int = Field(
        default=0,
        ge=0,
        description="Number of questions answered correctly"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of last BKT update"
    )
    mastery_status: Literal["locked", "learning", "mastered"] = Field(
        default="locked",
        description="Current state: locked (not unlocked), learning (in progress), mastered (P_L > threshold)"
    )
    unlocked_at: Optional[datetime] = Field(
        default=None,
        description="When this concept became available to practice"
    )
    mastered_at: Optional[datetime] = Field(
        default=None,
        description="When P_L crossed mastery threshold (0.90)"
    )


class UserMastery(BaseModel):
    """Complete mastery state for a user in a specific subject."""
    
    id: str = Field(alias="_id")
    user_id: str = Field(description="Reference to users collection")
    subject_id: str = Field(description="Reference to subjects collection")
    elo_rating: int = Field(
        default=1200,
        ge=0,
        description="Student's overall Elo rating for this subject"
    )
    concepts: Dict[str, ConceptMastery] = Field(
        default_factory=dict,
        description="Map of concept_id -> ConceptMastery"
    )
    unlocked_concepts: list[str] = Field(
        default_factory=list,
        description="List of concept_ids currently available to practice"
    )
    mastered_concepts: list[str] = Field(
        default_factory=list,
        description="List of concept_ids that have been mastered (P_L >= 0.90)"
    )
    current_focus: Optional[str] = Field(
        default=None,
        description="concept_id the user is currently working on"
    )
    total_questions_answered: int = Field(
        default=0,
        ge=0,
        description="Total questions answered across all concepts"
    )
    created_at: datetime
    last_updated: datetime
    
    class Config:
        populate_by_name = True


class UserMasteryCreate(BaseModel):
    """Request body for initializing user mastery."""
    
    subject_id: str


class UserMasteryUpdate(BaseModel):
    """Request body for updating user mastery (usually automatic)."""
    
    current_focus: Optional[str] = None


class MasteryStatusResponse(BaseModel):
    """Response for mastery status queries."""
    
    concept_id: str
    concept_name: str
    P_L: float
    mastery_status: Literal["locked", "learning", "mastered"]
    observations: int
    accuracy: float  # correct_count / observations
    unlocked_at: Optional[datetime]
    mastered_at: Optional[datetime]
