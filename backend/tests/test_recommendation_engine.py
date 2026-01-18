"""
Unit tests for Recommendation Engine

Tests adaptive learning logic, concept targeting, and question selection.
Uses mocked database operations to test pure recommendation logic.
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
    """Create a mock database."""
    db = MagicMock()
    db["knowledge_graphs"] = MagicMock()
    db["user_mastery"] = MagicMock()
    db["questions"] = MagicMock()
    return db


@pytest.fixture
def sample_graph():
    """Create a sample calculus knowledge graph."""
    nodes = {
        "limits": ConceptNode(
            concept_id="limits",
            name="Limits",
            parents=[],
            children=["derivatives"],
            default_params=BKTParams()
        ),
        "derivatives": ConceptNode(
            concept_id="derivatives",
            name="Derivatives",
            parents=["limits"],
            children=["chain_rule"],
            default_params=BKTParams()
        ),
        "chain_rule": ConceptNode(
            concept_id="chain_rule",
            name="Chain Rule",
            parents=["derivatives"],
            children=[],
            default_params=BKTParams()
        ),
    }
    
    return KnowledgeGraph(
        _id=str(ObjectId()),
        subject_id="calculus",
        created_by="admin",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        nodes=nodes,
        root_concepts=["limits"]
    )


@pytest.fixture
def sample_question():
    """Create a sample question."""
    return Question(
        _id=str(ObjectId()),
        subject_id="calculus",
        concept_id="limits",
        related_concepts=[],
        question_text="What is the limit of x as x approaches 2?",
        answer_key="2",
        elo_rating=1200,
        created_by="admin",
        created_at=datetime.utcnow()
    )


class TestDetermineTargetConcept:
    """Test the adaptive concept selection logic."""
    
    @pytest.mark.asyncio
    async def test_start_with_root_concept(self, mock_db, sample_graph):
        """Test that new students start with root concepts."""
        engine = RecommendationEngine(mock_db)
        
        # New student - no focus, nothing unlocked
        mastery_state = UserMastery(
            _id=str(ObjectId()),
            user_id="user1",
            subject_id="calculus",
            elo_rating=1200,
            concepts={},
            unlocked_concepts=["limits"],  # Root unlocked
            mastered_concepts=[],
            current_focus=None,
            total_questions_answered=0,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        target, reasoning = await engine._determine_target_concept(mastery_state, sample_graph)
        
        assert target == "limits"
        assert "limits" in reasoning.lower() or "foundational" in reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_continue_current_focus_when_learning(self, mock_db, sample_graph):
        """Test that students continue on current focus if making progress."""
        engine = RecommendationEngine(mock_db)
        
        # Student working on limits, making progress (learning status)
        mastery_state = UserMastery(
            _id=str(ObjectId()),
            user_id="user1",
            subject_id="calculus",
            elo_rating=1200,
            concepts={
                "limits": ConceptMastery(P_L=0.65, observations=5, correct_count=3)  # Learning
            },
            unlocked_concepts=["limits"],
            mastered_concepts=[],
            current_focus="limits",
            total_questions_answered=5,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        target, reasoning = await engine._determine_target_concept(mastery_state, sample_graph)
        
        assert target == "limits"
        assert "progress" in reasoning.lower() or "practicing" in reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_unlock_next_after_mastery(self, mock_db, sample_graph):
        """Test that mastering a concept unlocks the next one."""
        engine = RecommendationEngine(mock_db)
        
        # Student mastered limits (P_L >= 0.90)
        mastery_state = UserMastery(
            _id=str(ObjectId()),
            user_id="user1",
            subject_id="calculus",
            elo_rating=1250,
            concepts={
                "limits": ConceptMastery(P_L=0.92, observations=10, correct_count=9)  # Mastered
            },
            unlocked_concepts=["limits"],
            mastered_concepts=["limits"],
            current_focus="limits",
            total_questions_answered=10,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        target, reasoning = await engine._determine_target_concept(mastery_state, sample_graph)
        
        assert target == "derivatives"  # Next concept
        assert "mastered" in reasoning.lower()
        assert "derivatives" in reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_regression_to_weak_prerequisite(self, mock_db, sample_graph):
        """Test that weak performance triggers regression."""
        engine = RecommendationEngine(mock_db)
        
        # Student struggling with chain_rule, weak on derivatives
        mastery_state = UserMastery(
            _id=str(ObjectId()),
            user_id="user1",
            subject_id="calculus",
            elo_rating=1150,
            concepts={
                "limits": ConceptMastery(P_L=0.85, observations=10, correct_count=8),
                "derivatives": ConceptMastery(P_L=0.30, observations=5, correct_count=1),  # Weak
                "chain_rule": ConceptMastery(P_L=0.20, observations=3, correct_count=0)  # Very weak
            },
            unlocked_concepts=["limits", "derivatives", "chain_rule"],
            mastered_concepts=[],
            current_focus="chain_rule",
            total_questions_answered=18,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        target, reasoning = await engine._determine_target_concept(mastery_state, sample_graph)
        
        # Should regress to derivatives (prerequisite of chain_rule)
        assert target == "derivatives"
        assert "struggling" in reasoning.lower() or "strengthen" in reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_all_concepts_mastered(self, mock_db, sample_graph):
        """Test when student has mastered everything."""
        engine = RecommendationEngine(mock_db)
        
        mastery_state = UserMastery(
            _id=str(ObjectId()),
            user_id="user1",
            subject_id="calculus",
            elo_rating=1400,
            concepts={
                "limits": ConceptMastery(P_L=0.95, observations=15, correct_count=14),
                "derivatives": ConceptMastery(P_L=0.93, observations=12, correct_count=11),
                "chain_rule": ConceptMastery(P_L=0.91, observations=10, correct_count=9)
            },
            unlocked_concepts=["limits", "derivatives", "chain_rule"],
            mastered_concepts=["limits", "derivatives", "chain_rule"],
            current_focus="chain_rule",
            total_questions_answered=37,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        target, reasoning = await engine._determine_target_concept(mastery_state, sample_graph)
        
        assert target is None
        assert "mastered" in reasoning.lower() or "congratulations" in reasoning.lower()


class TestQuestionSelection:
    """Test Elo-based question matching."""
    
    @pytest.mark.asyncio
    async def test_find_question_in_elo_range(self, mock_db, sample_question):
        """Test finding a question matching student Elo."""
        engine = RecommendationEngine(mock_db)
        
        # Mock question collection
        mock_db["questions"].find_one = AsyncMock(return_value=sample_question.model_dump(by_alias=True))
        
        question = await engine._find_question_for_concept("limits", student_elo=1200, elo_tolerance=50)
        
        assert question is not None
        assert question.concept_id == "limits"
        assert question.elo_rating == 1200
    
    @pytest.mark.asyncio
    async def test_fallback_when_no_elo_match(self, mock_db, sample_question):
        """Test that engine falls back to any question if no Elo match."""
        engine = RecommendationEngine(mock_db)
        
        # Mock: first query (Elo range) returns None, second query (any) returns question
        mock_db["questions"].find_one = AsyncMock(side_effect=[None, sample_question.model_dump(by_alias=True)])
        
        question = await engine._find_question_for_concept("limits", student_elo=1500, elo_tolerance=50)
        
        assert question is not None
        assert question.concept_id == "limits"
    
    @pytest.mark.asyncio
    async def test_no_questions_available(self, mock_db):
        """Test when no questions exist for a concept."""
        engine = RecommendationEngine(mock_db)
        
        mock_db["questions"].find_one = AsyncMock(return_value=None)
        
        question = await engine._find_question_for_concept("limits", student_elo=1200)
        
        assert question is None


class TestAnswerProcessing:
    """Test answer submission and BKT updates."""
    
    @pytest.mark.asyncio
    async def test_correct_answer_increases_mastery(self, mock_db, sample_graph, sample_question):
        """Test that correct answers increase P(L)."""
        engine = RecommendationEngine(mock_db)
        
        # Mock database responses with all required fields
        question_data = {
            "_id": sample_question.id,
            "subject_id": sample_question.subject_id,
            "concept_id": sample_question.concept_id,
            "related_concepts": sample_question.related_concepts,
            "question_text": sample_question.question_text,
            "answer_key": sample_question.answer_key,
            "elo_rating": sample_question.elo_rating,
            "times_attempted": sample_question.times_attempted,
            "times_correct": sample_question.times_correct,
            "difficulty_label": sample_question.difficulty_label,
            "created_by": sample_question.created_by,
            "created_at": sample_question.created_at
        }
        mock_db["questions"].find_one = AsyncMock(return_value=question_data)
        mock_db["questions"].update_one = AsyncMock()
        
        initial_mastery = UserMastery(
            _id=str(ObjectId()),
            user_id="user1",
            subject_id="calculus",
            elo_rating=1200,
            concepts={
                "limits": ConceptMastery(P_L=0.50, P_T=0.10, P_G=0.25, P_S=0.10, observations=5, correct_count=2)
            },
            unlocked_concepts=["limits"],
            mastered_concepts=[],
            current_focus="limits",
            total_questions_answered=5,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        mock_db["user_mastery"].find_one = AsyncMock(return_value=initial_mastery.model_dump(by_alias=True))
        mock_db["user_mastery"].update_one = AsyncMock()
        
        # Mock graph service
        with patch.object(engine.graph_service, 'get_graph', return_value=sample_graph):
            with patch.object(engine, 'get_next_question', return_value=(None, "Continue", "limits")):
                result = await engine.process_answer_submission(
                    user_id="user1",
                    subject_id="calculus",
                    question_id=sample_question.id,
                    is_correct=True
                )
        
        # Verify mastery increased
        assert result["is_correct"] is True
        assert result["mastery_change"] > 0
        assert result["new_mastery_probability"] > 0.50
    
    @pytest.mark.asyncio
    async def test_mastery_achievement(self, mock_db, sample_graph, sample_question):
        """Test that crossing mastery threshold triggers achievement."""
        engine = RecommendationEngine(mock_db)
        
        question_data = {
            "_id": sample_question.id,
            "subject_id": sample_question.subject_id,
            "concept_id": sample_question.concept_id,
            "related_concepts": sample_question.related_concepts,
            "question_text": sample_question.question_text,
            "answer_key": sample_question.answer_key,
            "elo_rating": sample_question.elo_rating,
            "times_attempted": sample_question.times_attempted,
            "times_correct": sample_question.times_correct,
            "difficulty_label": sample_question.difficulty_label,
            "created_by": sample_question.created_by,
            "created_at": sample_question.created_at
        }
        mock_db["questions"].find_one = AsyncMock(return_value=question_data)
        mock_db["questions"].update_one = AsyncMock()
        
        # Student very close to mastery (P_L = 0.88)
        almost_mastered = UserMastery(
            _id=str(ObjectId()),
            user_id="user1",
            subject_id="calculus",
            elo_rating=1250,
            concepts={
                "limits": ConceptMastery(P_L=0.88, P_T=0.10, P_G=0.20, P_S=0.05, observations=15, correct_count=13)
            },
            unlocked_concepts=["limits"],
            mastered_concepts=[],
            current_focus="limits",
            total_questions_answered=15,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        mock_db["user_mastery"].find_one = AsyncMock(return_value=almost_mastered.model_dump(by_alias=True))
        mock_db["user_mastery"].update_one = AsyncMock()
        
        with patch.object(engine.graph_service, 'get_graph', return_value=sample_graph):
            with patch.object(engine, 'get_next_question', return_value=(None, "Next", "derivatives")):
                result = await engine.process_answer_submission(
                    user_id="user1",
                    subject_id="calculus",
                    question_id=sample_question.id,
                    is_correct=True
                )
        
        # Should cross mastery threshold
        assert result["new_mastery_probability"] >= 0.90
        assert result["concept_mastered"] is True
        assert "mastered" in result["feedback_message"].lower()
    
    @pytest.mark.asyncio
    async def test_elo_update(self, mock_db, sample_graph, sample_question):
        """Test that Elo ratings update correctly."""
        engine = RecommendationEngine(mock_db)
        
        question_data = {
            "_id": sample_question.id,
            "subject_id": sample_question.subject_id,
            "concept_id": sample_question.concept_id,
            "related_concepts": sample_question.related_concepts,
            "question_text": sample_question.question_text,
            "answer_key": sample_question.answer_key,
            "elo_rating": sample_question.elo_rating,
            "times_attempted": sample_question.times_attempted,
            "times_correct": sample_question.times_correct,
            "difficulty_label": sample_question.difficulty_label,
            "created_by": sample_question.created_by,
            "created_at": sample_question.created_at
        }
        mock_db["questions"].find_one = AsyncMock(return_value=question_data)
        mock_db["questions"].update_one = AsyncMock()
        
        mastery = UserMastery(
            _id=str(ObjectId()),
            user_id="user1",
            subject_id="calculus",
            elo_rating=1200,
            concepts={
                "limits": ConceptMastery(P_L=0.60, P_T=0.10, P_G=0.25, P_S=0.10, observations=5, correct_count=3)
            },
            unlocked_concepts=["limits"],
            mastered_concepts=[],
            current_focus="limits",
            total_questions_answered=5,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        mock_db["user_mastery"].find_one = AsyncMock(return_value=mastery.model_dump(by_alias=True))
        mock_db["user_mastery"].update_one = AsyncMock()
        
        with patch.object(engine.graph_service, 'get_graph', return_value=sample_graph):
            with patch.object(engine, 'get_next_question', return_value=(None, "Continue", "limits")):
                result = await engine.process_answer_submission(
                    user_id="user1",
                    subject_id="calculus",
                    question_id=sample_question.id,
                    is_correct=True
                )
        
        # Student beat equal-Elo question → Elo should increase
        assert result["elo_change"] > 0
        assert result["new_student_elo"] > 1200


class TestInitialization:
    """Test user mastery initialization."""
    
    @pytest.mark.asyncio
    async def test_initialize_new_user(self, mock_db, sample_graph):
        """Test creating initial mastery state for new user."""
        engine = RecommendationEngine(mock_db)
        
        # No existing mastery
        mock_db["user_mastery"].find_one = AsyncMock(return_value=None)
        mock_db["user_mastery"].insert_one = AsyncMock()
        
        with patch.object(engine.graph_service, 'get_graph', return_value=sample_graph):
            mastery_id = await engine.initialize_user_mastery(
                user_id="user1",
                subject_id="calculus"
            )
        
        assert mastery_id is not None
        
        # Verify insert was called
        mock_db["user_mastery"].insert_one.assert_called_once()
        
        # Check that root concepts were unlocked
        inserted_doc = mock_db["user_mastery"].insert_one.call_args[0][0]
        assert "limits" in inserted_doc["unlocked_concepts"]
        assert inserted_doc["elo_rating"] == 1200
        assert inserted_doc["current_focus"] == "limits"
    
    @pytest.mark.asyncio
    async def test_skip_if_already_initialized(self, mock_db, sample_graph):
        """Test that initialization doesn't overwrite existing state."""
        engine = RecommendationEngine(mock_db)
        
        existing_id = str(ObjectId())
        mock_db["user_mastery"].find_one = AsyncMock(return_value={"_id": existing_id})
        
        mastery_id = await engine.initialize_user_mastery(
            user_id="user1",
            subject_id="calculus"
        )
        
        assert mastery_id == existing_id
        # Should NOT have called insert
        mock_db["user_mastery"].insert_one.assert_not_called()


class TestFeedbackMessages:
    """Test human-readable feedback generation."""
    
    def test_mastery_achievement_message(self, mock_db):
        """Test message when concept is mastered."""
        engine = RecommendationEngine(mock_db)
        
        bkt_result = {
            "P_L_new": 0.92,
            "mastery_status_new": "mastered"
        }
        
        feedback = engine._generate_feedback_message(
            is_correct=True,
            bkt_result=bkt_result,
            concept_mastered=True,
            unlocked_concepts=["derivatives"]
        )
        
        assert "mastered" in feedback.lower()
        assert "unlock" in feedback.lower()
    
    def test_correct_answer_feedback(self, mock_db):
        """Test positive feedback for correct answer."""
        engine = RecommendationEngine(mock_db)
        
        bkt_result = {
            "P_L_new": 0.65,
            "mastery_status_new": "learning"
        }
        
        feedback = engine._generate_feedback_message(
            is_correct=True,
            bkt_result=bkt_result,
            concept_mastered=False,
            unlocked_concepts=[]
        )
        
        assert "correct" in feedback.lower()
        assert "progress" in feedback.lower()
    
    def test_incorrect_answer_feedback(self, mock_db):
        """Test constructive feedback for incorrect answer."""
        engine = RecommendationEngine(mock_db)
        
        bkt_result = {
            "P_L_new": 0.35,
            "mastery_status_new": "locked"
        }
        
        feedback = engine._generate_feedback_message(
            is_correct=False,
            bkt_result=bkt_result,
            concept_mastered=False,
            unlocked_concepts=[]
        )
        
        assert "incorrect" in feedback.lower()
        assert "foundational" in feedback.lower() or "review" in feedback.lower()


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_missing_question(self, mock_db):
        """Test handling of non-existent question."""
        engine = RecommendationEngine(mock_db)
        
        mock_db["questions"].find_one = AsyncMock(return_value=None)
        
        result = await engine.process_answer_submission(
            user_id="user1",
            subject_id="calculus",
            question_id="nonexistent",
            is_correct=True
        )
        
        assert "error" in result
        assert "question not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_missing_mastery_state(self, mock_db, sample_question):
        """Test handling when user mastery doesn't exist."""
        engine = RecommendationEngine(mock_db)
        
        question_data = {
            "_id": sample_question.id,
            "subject_id": sample_question.subject_id,
            "concept_id": sample_question.concept_id,
            "related_concepts": sample_question.related_concepts,
            "question_text": sample_question.question_text,
            "answer_key": sample_question.answer_key,
            "elo_rating": sample_question.elo_rating,
            "times_attempted": sample_question.times_attempted,
            "times_correct": sample_question.times_correct,
            "difficulty_label": sample_question.difficulty_label,
            "created_by": sample_question.created_by,
            "created_at": sample_question.created_at
        }
        mock_db["questions"].find_one = AsyncMock(return_value=question_data)
        mock_db["user_mastery"].find_one = AsyncMock(return_value=None)
        
        result = await engine.process_answer_submission(
            user_id="user1",
            subject_id="calculus",
            question_id=sample_question.id,
            is_correct=True
        )
        
        assert "error" in result
        assert "mastery state not found" in result["error"].lower()
