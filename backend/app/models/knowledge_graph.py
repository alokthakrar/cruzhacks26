from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class BKTParams(BaseModel):
    """Bayesian Knowledge Tracing parameters for a concept."""
    
    P_L0: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Initial knowledge probability (before any observations)"
    )
    P_T: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Transition probability (learn rate per question)"
    )
    P_G: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Guess probability (correct despite not knowing)"
    )
    P_S: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Slip probability (incorrect despite knowing)"
    )


class ConceptNode(BaseModel):
    """A single concept/topic node in the knowledge graph."""
    
    concept_id: str = Field(
        description="Unique identifier (e.g., 'calculus_derivatives')"
    )
    name: str = Field(description="Display name (e.g., 'Derivatives')")
    description: Optional[str] = Field(
        default=None,
        description="Detailed explanation of this concept"
    )
    parents: List[str] = Field(
        default_factory=list,
        description="List of parent concept_ids (prerequisites)"
    )
    children: List[str] = Field(
        default_factory=list,
        description="List of child concept_ids (depends on this)"
    )
    default_params: BKTParams = Field(
        default_factory=BKTParams,
        description="Default BKT parameters for this concept"
    )
    depth: int = Field(
        default=0,
        ge=0,
        description="Depth in tree (0 = root, used for topological ordering)"
    )


class KnowledgeGraph(BaseModel):
    """Complete knowledge graph for a subject (stored in MongoDB)."""
    
    id: str = Field(alias="_id")
    subject_id: str = Field(description="Reference to subjects collection")
    created_by: str = Field(description="user_id who created this graph")
    created_at: datetime
    updated_at: datetime
    nodes: Dict[str, ConceptNode] = Field(
        default_factory=dict,
        description="Map of concept_id -> ConceptNode"
    )
    root_concepts: List[str] = Field(
        default_factory=list,
        description="List of concept_ids with no parents (entry points)"
    )
    
    class Config:
        populate_by_name = True


class KnowledgeGraphCreate(BaseModel):
    """Request body for creating a knowledge graph."""
    
    subject_id: str
    nodes: Dict[str, ConceptNode]


class KnowledgeGraphUpdate(BaseModel):
    """Request body for updating a knowledge graph."""
    
    nodes: Optional[Dict[str, ConceptNode]] = None
