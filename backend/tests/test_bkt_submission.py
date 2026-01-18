"""
Unit tests for BKT submission flow and question tracking

Tests the complete answer submission pipeline including:
- Question loading (text and image-only)
- BKT updates with logging
- Question tracking by concept
- Progress endpoint with breakdown
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.recommendation_engine import RecommendationEngine
from app.models.knowledge_graph import ConceptNode, KnowledgeGraph, BKTParams
from app.models.user_mastery import UserMastery, ConceptMastery
from app.models.question import Question
from datetime import datetime
from bson import ObjectId


@pytest.fixture
def mock_db():
    """Create a mock database with collections."""
    db = MagicMock()
    db["knowledge_graphs"] = MagicMock()
    db["user_mastery"] = MagicMock()
    db["questions"] = MagicMock()
    db["answer_submissions"] = MagicMock()
    return db


@pytest.fixture
def sample_graph():
    """Create a sample knowledge graph with BKT params."""
    nodes = {
        "derivatives": ConceptNode(
            concept_id="derivatives",
            name="Derivatives",
            parents=["limits"],
            children=["chain_rule"],
            default_params=BKTParams(
                P_L0=0.10,
                P_T=0.15,
                P_G=0.25,
                P_S=0.10
            ),
            depth=1
        ),
        "limits": ConceptNode(
            concept_id="limits",
            name="Limits",
            parents=[],
            children=["derivatives"],
            default_params=BKTParams(
                P_L0=0.10,
                P_T=0.10,
                P_G=0.25,
                P_S=0.10
            ),
            depth=0
        ),
    }
    
    return KnowledgeGraph(
        _id=str(ObjectId()),
        subject_id="calculus_subject",
        created_by="admin",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        nodes=nodes,
        root_concepts=["limits"]
    )


@pytest.fixture
def text_question():
    """Create a text-based question."""
    question_id = str(ObjectId())
    return {
        "_id": question_id,
        "id": question_id,
        "subject_id": "calculus_subject",
        "concept_id": "derivatives",
        "related_concepts": [],
        "question_text": "Find the derivative of f(x) = 3x² + 2x - 5",
        "question_image": None,
        "answer_key": "6x + 2",
        "hints": [],
        "elo_rating": 1200,
        "difficulty_label": "medium",
        "times_attempted": 0,
        "times_correct": 0,
        "success_rate": 0.0,
        "created_by": "admin",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def image_question():
    """Create an image-only question (no text)."""
    question_id = str(ObjectId())
    return {
        "_id": question_id,
        "id": question_id,
        "subject_id": "calculus_subject",
        "concept_id": "derivatives",
        "related_concepts": [],
        "question_text": None,  # Image-only question
        "question_image": "https://example.com/image.png",
        "answer_key": "Solution in image",
        "hints": [],
        "elo_rating": 1200,
        "difficulty_label": "medium",
        "times_attempted": 0,
        "times_correct": 0,
        "success_rate": 0.0,
        "created_by": "admin",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def initialized_mastery():
    """Create an initialized user mastery state."""
    return UserMastery(
        _id=str(ObjectId()),
        user_id="test_user",
        subject_id="calculus_subject",
        elo_rating=1200,
        concepts={
            "derivatives": ConceptMastery(
                P_L=0.25,
                P_T=0.15,
                P_G=0.25,
                P_S=0.10,
                observations=2,
                correct_count=1,
                mastery_status="learning"
            )
        },
        unlocked_concepts=["limits", "derivatives"],
        mastered_concepts=[],
        current_focus="derivatives",
        total_questions_answered=2,
        questions_by_concept={"derivatives": 2},
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )


@pytest.fixture
def uninitialized_mastery():
    """Create a mastery state without the target concept initialized."""
    return UserMastery(
        _id=str(ObjectId()),
        user_id="test_user",
        subject_id="calculus_subject",
        elo_rating=1200,
        concepts={},  # No concepts initialized yet
        unlocked_concepts=["limits", "derivatives"],
        mastered_concepts=[],
        current_focus=None,
        total_questions_answered=0,
        questions_by_concept={},
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )


@pytest.mark.asyncio
async def test_submit_answer_text_question_correct(mock_db, text_question, initialized_mastery, sample_graph):
    """Test successful submission with text-based question (correct answer)."""
    # Setup mocks
    mock_db["questions"].find_one = AsyncMock(return_value=text_question)
    mock_db["user_mastery"].find_one = AsyncMock(return_value=initialized_mastery.model_dump(by_alias=True))
    mock_db["user_mastery"].update_one = AsyncMock()
    mock_db["questions"].update_one = AsyncMock()
    
    with patch('app.services.recommendation_engine.GraphService') as mock_graph_service:
        mock_graph_instance = MagicMock()
        mock_graph_instance.get_graph = AsyncMock(return_value=sample_graph)
        mock_graph_instance.get_next_unlockable_concepts = MagicMock(return_value=[])
        mock_graph_service.return_value = mock_graph_instance
        
        engine = RecommendationEngine(mock_db)
        engine.graph_service = mock_graph_instance
        
        # Mock get_next_question to avoid circular dependency
        with patch.object(engine, 'get_next_question', new=AsyncMock(return_value=(None, "No more questions", None))):
            result = await engine.process_answer_submission(
                user_id="test_user",
                subject_id="calculus_subject",
                question_id=text_question["id"],
                is_correct=True,
                mistake_count=1
            )
    
    # Assertions
    assert result is not None
    assert "error" not in result
    assert result["is_correct"] is True
    assert result["mastery_change"] > 0  # Should increase
    assert "new_mastery_probability" in result
    assert "new_student_elo" in result
    
    # Verify database updates were called
    mock_db["user_mastery"].update_one.assert_called_once()
    mock_db["questions"].update_one.assert_called_once()
    
    # Check that questions_by_concept was updated
    update_call = mock_db["user_mastery"].update_one.call_args
    assert "questions_by_concept" in update_call[0][1]["$set"]


@pytest.mark.asyncio
async def test_submit_answer_image_question(mock_db, image_question, initialized_mastery, sample_graph):
    """Test submission with image-only question (no text) - should handle None gracefully."""
    # Setup mocks
    mock_db["questions"].find_one = AsyncMock(return_value=image_question)
    mock_db["user_mastery"].find_one = AsyncMock(return_value=initialized_mastery.model_dump(by_alias=True))
    mock_db["user_mastery"].update_one = AsyncMock()
    mock_db["questions"].update_one = AsyncMock()
    
    with patch('app.services.recommendation_engine.GraphService') as mock_graph_service:
        mock_graph_instance = MagicMock()
        mock_graph_instance.get_graph = AsyncMock(return_value=sample_graph)
        mock_graph_instance.get_next_unlockable_concepts = MagicMock(return_value=[])
        mock_graph_service.return_value = mock_graph_instance
        
        engine = RecommendationEngine(mock_db)
        engine.graph_service = mock_graph_instance
        
        with patch.object(engine, 'get_next_question', new=AsyncMock(return_value=(None, "No more questions", None))):
            result = await engine.process_answer_submission(
                user_id="test_user",
                subject_id="calculus_subject",
                question_id=image_question["id"],
                is_correct=False,
                mistake_count=3
            )
    
    # Should complete without error even with None question_text
    assert result is not None
    assert "error" not in result
    assert result["is_correct"] is False


@pytest.mark.asyncio
async def test_submit_answer_initializes_new_concept(mock_db, text_question, uninitialized_mastery, sample_graph):
    """Test that submitting answer initializes concept if not tracked yet."""
    # Setup mocks
    mock_db["questions"].find_one = AsyncMock(return_value=text_question)
    mock_db["user_mastery"].find_one = AsyncMock(return_value=uninitialized_mastery.model_dump(by_alias=True))
    mock_db["user_mastery"].update_one = AsyncMock()
    mock_db["questions"].update_one = AsyncMock()
    
    with patch('app.services.recommendation_engine.GraphService') as mock_graph_service:
        mock_graph_instance = MagicMock()
        mock_graph_instance.get_graph = AsyncMock(return_value=sample_graph)
        mock_graph_instance.get_next_unlockable_concepts = MagicMock(return_value=[])
        mock_graph_service.return_value = mock_graph_instance
        
        engine = RecommendationEngine(mock_db)
        engine.graph_service = mock_graph_instance
        
        with patch.object(engine, 'get_next_question', new=AsyncMock(return_value=(None, "No more questions", None))):
            result = await engine.process_answer_submission(
                user_id="test_user",
                subject_id="calculus_subject",
                question_id=text_question["id"],
                is_correct=True,
                mistake_count=0
            )
    
    # Should initialize concept with graph defaults
    assert result is not None
    assert "error" not in result
    
    # Verify concept was initialized in update
    update_call = mock_db["user_mastery"].update_one.call_args
    set_operations = update_call[0][1]["$set"]
    assert f"concepts.{text_question['concept_id']}" in set_operations


@pytest.mark.asyncio
async def test_question_tracking_increments(mock_db, text_question, initialized_mastery, sample_graph):
    """Test that questions_by_concept counter increments correctly."""
    # Setup mocks
    mock_db["questions"].find_one = AsyncMock(return_value=text_question)
    mock_db["user_mastery"].find_one = AsyncMock(return_value=initialized_mastery.model_dump(by_alias=True))
    mock_db["user_mastery"].update_one = AsyncMock()
    mock_db["questions"].update_one = AsyncMock()
    
    with patch('app.services.recommendation_engine.GraphService') as mock_graph_service:
        mock_graph_instance = MagicMock()
        mock_graph_instance.get_graph = AsyncMock(return_value=sample_graph)
        mock_graph_instance.get_next_unlockable_concepts = MagicMock(return_value=[])
        mock_graph_service.return_value = mock_graph_instance
        
        engine = RecommendationEngine(mock_db)
        engine.graph_service = mock_graph_instance
        
        with patch.object(engine, 'get_next_question', new=AsyncMock(return_value=(None, "No more questions", None))):
            result = await engine.process_answer_submission(
                user_id="test_user",
                subject_id="calculus_subject",
                question_id=text_question.id,
                is_correct=True,
                mistake_count=0
            )
    
    # Check update call
    update_call = mock_db["user_mastery"].update_one.call_args
    updated_tracking = update_call[0][1]["$set"]["questions_by_concept"]
    
    # Should have incremented from 2 to 3 for derivatives
    assert "derivatives" in updated_tracking
    assert updated_tracking["derivatives"] == 3


@pytest.mark.asyncio
async def test_submit_answer_with_mistakes_reduces_learning(mock_db, text_question, initialized_mastery, sample_graph):
    """Test that mistakes reduce effective learning rate."""
    # Setup mocks
    mock_db["questions"].find_one = AsyncMock(return_value=text_question)
    mock_db["user_mastery"].find_one = AsyncMock(return_value=initialized_mastery.model_dump(by_alias=True))
    mock_db["user_mastery"].update_one = AsyncMock()
    mock_db["questions"].update_one = AsyncMock()
    
    with patch('app.services.recommendation_engine.GraphService') as mock_graph_service:
        mock_graph_instance = MagicMock()
        mock_graph_instance.get_graph = AsyncMock(return_value=sample_graph)
        mock_graph_instance.get_next_unlockable_concepts = MagicMock(return_value=[])
        mock_graph_service.return_value = mock_graph_instance
        
        engine = RecommendationEngine(mock_db)
        engine.graph_service = mock_graph_instance
        
        with patch.object(engine, 'get_next_question', new=AsyncMock(return_value=(None, "No more questions", None))):
            # Submit with 3 mistakes
            result_with_mistakes = await engine.process_answer_submission(
                user_id="test_user",
                subject_id="calculus_subject",
                question_id=text_question["id"],
                is_correct=True,
                mistake_count=3
            )
    
    # Mastery change should be positive but reduced due to mistakes
    assert result_with_mistakes["mastery_change"] > 0
    assert result_with_mistakes["mastery_change"] < 0.15  # Less than full P_T


@pytest.mark.asyncio
async def test_submit_answer_question_not_found(mock_db):
    """Test error handling when question doesn't exist."""
    mock_db["questions"].find_one = AsyncMock(return_value=None)
    
    engine = RecommendationEngine(mock_db)
    
    result = await engine.process_answer_submission(
        user_id="test_user",
        subject_id="calculus_subject",
        question_id="nonexistent_id",
        is_correct=True,
        mistake_count=0
    )
    
    assert "error" in result
    assert result["error"] == "Question not found"


@pytest.mark.asyncio
async def test_submit_answer_mastery_not_found(mock_db, text_question):
    """Test error handling when user mastery doesn't exist."""
    mock_db["questions"].find_one = AsyncMock(return_value=text_question)
    mock_db["user_mastery"].find_one = AsyncMock(return_value=None)
    
    engine = RecommendationEngine(mock_db)
    
    result = await engine.process_answer_submission(
        user_id="test_user",
        subject_id="calculus_subject",
        question_id=text_question["id"],
        is_correct=True,
        mistake_count=0
    )
    
    assert "error" in result
    assert result["error"] == "User mastery state not found"


@pytest.mark.asyncio
async def test_total_questions_increments(mock_db, text_question, initialized_mastery, sample_graph):
    """Test that total_questions_answered increments."""
    mock_db["questions"].find_one = AsyncMock(return_value=text_question)
    mock_db["user_mastery"].find_one = AsyncMock(return_value=initialized_mastery.model_dump(by_alias=True))
    mock_db["user_mastery"].update_one = AsyncMock()
    mock_db["questions"].update_one = AsyncMock()
    
    with patch('app.services.recommendation_engine.GraphService') as mock_graph_service:
        mock_graph_instance = MagicMock()
        mock_graph_instance.get_graph = AsyncMock(return_value=sample_graph)
        mock_graph_instance.get_next_unlockable_concepts = MagicMock(return_value=[])
        mock_graph_service.return_value = mock_graph_instance
        
        engine = RecommendationEngine(mock_db)
        engine.graph_service = mock_graph_instance
        
        with patch.object(engine, 'get_next_question', new=AsyncMock(return_value=(None, "No more questions", None))):
            await engine.process_answer_submission(
                user_id="test_user",
                subject_id="calculus_subject",
                question_id=text_question["id"],
                is_correct=True,
                mistake_count=0
            )
    
    # Check that total incremented from 2 to 3
    update_call = mock_db["user_mastery"].update_one.call_args
    assert update_call[0][1]["$set"]["total_questions_answered"] == 3
