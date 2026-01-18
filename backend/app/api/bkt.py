"""
BKT (Bayesian Knowledge Tracing) API Router

Endpoints for adaptive learning: answer submissions, mastery tracking, and question recommendations.
"""

from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime

from ..database import get_database
from ..services.recommendation_engine import RecommendationEngine
from ..models.answer_submission import AnswerSubmissionCreate, AnswerSubmissionResponse
from ..models.user_mastery import UserMastery, MasteryStatusResponse
from ..models.question import QuestionResponse

router = APIRouter(prefix="/api/bkt", tags=["BKT"])


@router.post("/initialize")
async def initialize_user_mastery(
    user_id: str,
    subject_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Initialize BKT mastery tracking for a user in a subject.
    
    - Unlocks root concepts
    - Sets initial Elo rating (1200)
    - Creates mastery state document
    
    **Call this once when user starts a new subject.**
    """
    engine = RecommendationEngine(db)
    
    try:
        mastery_id = await engine.initialize_user_mastery(user_id, subject_id)
        return {
            "mastery_id": mastery_id,
            "message": "Mastery tracking initialized successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@router.get("/mastery/{user_id}/{subject_id}")
async def get_user_mastery(
    user_id: str,
    subject_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get complete mastery state for a user in a subject.
    
    Returns:
    - Elo rating
    - Concept mastery probabilities
    - Unlocked/mastered concepts
    - Total questions answered
    """
    mastery_doc = await db["user_mastery"].find_one({
        "user_id": user_id,
        "subject_id": subject_id
    })
    
    if not mastery_doc:
        raise HTTPException(
            status_code=404,
            detail="Mastery state not found. Call /initialize first."
        )
    
    return UserMastery(**mastery_doc)


@router.get("/mastery/{user_id}/{subject_id}/concepts")
async def get_concept_mastery_summary(
    user_id: str,
    subject_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get mastery status for all concepts in a subject.
    
    Returns list of concepts with:
    - Mastery probability
    - Status (locked/learning/mastered)
    - Accuracy
    - Observations
    """
    # Get mastery state
    mastery_doc = await db["user_mastery"].find_one({
        "user_id": user_id,
        "subject_id": subject_id
    })
    
    if not mastery_doc:
        raise HTTPException(status_code=404, detail="Mastery state not found")
    
    # Get knowledge graph for concept names
    graph_doc = await db["knowledge_graphs"].find_one({"subject_id": subject_id})
    if not graph_doc:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    # Build summary
    concepts = mastery_doc.get("concepts", {})
    summary = []
    
    for concept_id, concept_data in concepts.items():
        node = graph_doc["nodes"].get(concept_id, {})
        accuracy = (
            concept_data["correct_count"] / concept_data["observations"]
            if concept_data["observations"] > 0
            else 0.0
        )
        
        summary.append(MasteryStatusResponse(
            concept_id=concept_id,
            concept_name=node.get("name", concept_id),
            P_L=concept_data["P_L"],
            mastery_status=concept_data["mastery_status"],
            observations=concept_data["observations"],
            accuracy=accuracy,
            unlocked_at=concept_data.get("unlocked_at"),
            mastered_at=concept_data.get("mastered_at")
        ))
    
    return {"concepts": summary}


@router.post("/submit", response_model=AnswerSubmissionResponse)
async def submit_answer(
    submission: AnswerSubmissionCreate,
    user_id: str,
    subject_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Submit an answer and update BKT + Elo ratings.
    
    This triggers:
    1. BKT probability update
    2. Elo rating adjustment
    3. Concept unlocking (if mastery threshold reached)
    4. Next question recommendation
    
    **This is the core adaptive learning endpoint.**
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("📥 BKT ANSWER SUBMISSION STARTED")
    logger.info(f"   User ID: {user_id}")
    logger.info(f"   Subject ID: {subject_id}")
    logger.info(f"   Question ID: {submission.question_id}")
    logger.info(f"   Is Correct: {submission.is_correct}")
    logger.info(f"   Mistake Count: {submission.mistake_count}")
    logger.info(f"   Time Taken: {submission.time_taken_seconds}s")
    logger.info("=" * 80)
    
    engine = RecommendationEngine(db)
    
    try:
        logger.info("🔄 Starting BKT processing...")
        result = await engine.process_answer_submission(
            user_id=user_id,
            subject_id=subject_id,
            question_id=submission.question_id,
            is_correct=submission.is_correct,
            mistake_count=submission.mistake_count
        )
        logger.info("✅ BKT processing completed successfully")
        
        if "error" in result:
            logger.error(f"❌ BKT processing returned error: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Log results
        logger.info("📊 BKT RESULTS:")
        logger.info(f"   Mastery Change: {result['mastery_change']:+.4f} ({result.get('P_L_before', 0.0):.4f} → {result['new_mastery_probability']:.4f})")
        logger.info(f"   Status Change: {result.get('mastery_status_before', 'unknown')} → {result['new_mastery_status']}")
        logger.info(f"   Elo Change: {result['elo_change']:+d} → {result['new_student_elo']}")
        logger.info(f"   Concept Mastered: {result['concept_mastered']}")
        logger.info(f"   Unlocked Concepts: {result['unlocked_concepts']}")
        
        # Log submission to answer_submissions collection
        from bson import ObjectId
        logger.info("💾 Saving submission to database...")
        submission_doc = {
            "_id": str(ObjectId()),
            "user_id": user_id,
            "subject_id": subject_id,
            "question_id": submission.question_id,
            "concept_id": result.get("concept_id", "unknown"),
            "timestamp": datetime.utcnow(),
            "is_correct": submission.is_correct,
            "time_taken_seconds": submission.time_taken_seconds,
            "user_answer": submission.user_answer,
            "P_L_before": result.get("P_L_before", 0.0),
            "P_L_after": result["new_mastery_probability"],
            "student_elo_before": result["new_student_elo"] - result["elo_change"],
            "student_elo_after": result["new_student_elo"],
            "question_elo_before": result.get("question_elo_before", 1200),
            "question_elo_after": result.get("question_elo_after", 1200),
            "mastery_status_before": result.get("mastery_status_before", "learning"),
            "mastery_status_after": result["new_mastery_status"],
            "observations_count": result.get("observations_count", 1)
        }
        
        await db["answer_submissions"].insert_one(submission_doc)
        logger.info(f"✅ Submission saved with ID: {submission_doc['_id']}")
        logger.info("=" * 80)
        
        return AnswerSubmissionResponse(
            submission_id=submission_doc["_id"],
            is_correct=result["is_correct"],
            mastery_change=result["mastery_change"],
            elo_change=result["elo_change"],
            new_mastery_probability=result["new_mastery_probability"],
            new_mastery_status=result["new_mastery_status"],
            new_student_elo=result["new_student_elo"],
            unlocked_concepts=result["unlocked_concepts"],
            concept_mastered=result["concept_mastered"],
            feedback_message=result["feedback_message"],
            recommended_next_concept=result["recommended_next_concept"]
        )
        
    except Exception as e:
        import traceback
        logger.error("=" * 80)
        logger.error("❌ BKT SUBMISSION FAILED")
        logger.error(f"   Error Type: {type(e).__name__}")
        logger.error(f"   Error Message: {str(e)}")
        logger.error(f"   Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Submission processing failed: {str(e)}")


@router.get("/recommend/{user_id}/{subject_id}")
async def get_recommendation(
    user_id: str,
    subject_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get the next recommended question for a user.
    
    Algorithm:
    1. Determine target concept (based on mastery, regression, unlocking)
    2. Find question matching student Elo (±50)
    3. Return question with reasoning
    
    **Call this to get the next question after each submission.**
    """
    engine = RecommendationEngine(db)
    
    try:
        question, reasoning, concept_id = await engine.get_next_question(
            user_id, subject_id
        )
        
        if not question:
            return {
                "question": None,
                "reasoning": reasoning or "No questions available",
                "target_concept": concept_id
            }
        
        # Get concept name
        graph_doc = await db["knowledge_graphs"].find_one({"subject_id": subject_id})
        concept_name = None
        if graph_doc and concept_id in graph_doc["nodes"]:
            concept_name = graph_doc["nodes"][concept_id]["name"]
        
        return {
            "question": QuestionResponse(
                id=question.id,
                subject_id=question.subject_id,
                concept_id=question.concept_id,
                concept_name=concept_name,
                question_text=question.question_text,
                question_image=question.question_image,
                elo_rating=question.elo_rating,
                difficulty_label=question.difficulty_label,
                success_rate=question.success_rate,
                times_attempted=question.times_attempted
            ),
            "reasoning": reasoning,
            "target_concept": concept_id,
            "concept_name": concept_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


@router.get("/progress/{user_id}/{subject_id}")
async def get_progress_summary(
    user_id: str,
    subject_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get high-level progress summary for visualization.
    
    Returns:
    - Total questions answered
    - Concepts mastered count
    - Average mastery probability
    - Elo rating
    - Recent submissions (last 10)
    """
    # Get mastery state
    mastery_doc = await db["user_mastery"].find_one({
        "user_id": user_id,
        "subject_id": subject_id
    })
    
    if not mastery_doc:
        raise HTTPException(status_code=404, detail="Mastery state not found")
    
    # Get knowledge graph for concept names
    graph_doc = await db["knowledge_graphs"].find_one({"subject_id": subject_id})
    concept_names = {}
    if graph_doc and "nodes" in graph_doc:
        for concept_id, node_data in graph_doc["nodes"].items():
            concept_names[concept_id] = node_data.get("name", concept_id)
    
    # Calculate stats
    concepts = mastery_doc.get("concepts", {})
    total_concepts = len(concepts)
    mastered_count = len(mastery_doc.get("mastered_concepts", []))
    
    if total_concepts > 0:
        avg_mastery = sum(c["P_L"] for c in concepts.values()) / total_concepts
    else:
        avg_mastery = 0.0
    
    # Get recent submissions
    recent_submissions = await db["answer_submissions"].find({
        "user_id": user_id,
        "subject_id": subject_id
    }).sort("timestamp", -1).limit(10).to_list(length=10)
    
    # Build questions by concept breakdown with names
    questions_by_concept = mastery_doc.get("questions_by_concept", {})
    questions_breakdown = [
        {
            "concept_id": concept_id,
            "concept_name": concept_names.get(concept_id, concept_id),
            "count": count
        }
        for concept_id, count in questions_by_concept.items()
    ]
    # Sort by count descending
    questions_breakdown.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "total_questions_answered": mastery_doc.get("total_questions_answered", 0),
        "total_solved_questions": len(mastery_doc.get("solved_questions", [])),
        "elo_rating": mastery_doc.get("elo_rating", 1200),
        "concepts_attempted": total_concepts,
        "concepts_mastered": mastered_count,
        "concepts_unlocked": len(mastery_doc.get("unlocked_concepts", [])),
        "average_mastery": round(avg_mastery, 3),
        "mastery_percentage": round(avg_mastery * 100, 1),
        "questions_by_concept": questions_breakdown,
        "recent_submissions": [
            {
                "timestamp": sub["timestamp"],
                "concept_id": sub["concept_id"],
                "is_correct": sub["is_correct"],
                "mastery_change": sub["P_L_after"] - sub["P_L_before"]
            }
            for sub in recent_submissions
        ]
    }


@router.get("/graph/{subject_id}")
async def get_knowledge_graph(
    subject_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get the knowledge graph structure for a subject.

    Returns DAG of concepts with prerequisites/dependencies.
    Useful for visualization and navigation.
    """
    graph_doc = await db["knowledge_graphs"].find_one({"subject_id": subject_id})

    if not graph_doc:
        raise HTTPException(status_code=404, detail="Knowledge graph not found for this subject")

    # Fill missing name/description from subject if needed
    if not graph_doc.get("name") or not graph_doc.get("description"):
        subject_doc = await db["subjects"].find_one({"_id": subject_id})
        if subject_doc:
            graph_doc.setdefault("name", subject_doc.get("name"))
            graph_doc.setdefault(
                "description",
                f"Learning path for {subject_doc.get('name')}"
            )

    # Normalize nodes for frontend (array with prerequisites + bkt_params)
    nodes = graph_doc.get("nodes")
    if isinstance(nodes, dict):
        normalized_nodes = []
        for concept_id, node in nodes.items():
            bkt_params = node.get("default_params") or node.get("bkt_params") or {
                "P_L0": 0.10,
                "P_T": 0.10,
                "P_G": 0.25,
                "P_S": 0.10
            }
            normalized_nodes.append({
                "id": node.get("concept_id", concept_id),
                "name": node.get("name", concept_id),
                "description": node.get("description", ""),
                "prerequisites": node.get("parents", node.get("prerequisites", [])),
                "depth": node.get("depth", 0),
                "bkt_params": bkt_params
            })
        graph_doc["nodes"] = normalized_nodes

    # Convert ObjectId to string for JSON serialization
    if "_id" in graph_doc:
        graph_doc["_id"] = str(graph_doc["_id"])

    return graph_doc


@router.get("/mistakes/{user_id}/{subject_id}/{concept_id}")
async def get_concept_mistakes(
    user_id: str,
    subject_id: str,
    concept_id: str,
    limit: int = 20,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get mistake history for a specific concept.
    
    Returns recent submissions that were incorrect, including:
    - Timestamp
    - Mastery probability before/after
    - User answer (if available)
    - BKT parameters used
    
    Useful for identifying patterns in student errors.
    """
    # Get recent submissions for this concept (both correct and incorrect)
    submissions = await db["answer_submissions"].find({
        "user_id": user_id,
        "subject_id": subject_id,
        "concept_id": concept_id
    }).sort("timestamp", -1).limit(limit).to_list(length=limit)
    
    if not submissions:
        return {
            "concept_id": concept_id,
            "total_attempts": 0,
            "mistakes": [],
            "correct_attempts": 0,
            "accuracy": 0.0
        }
    
    # Separate mistakes from correct attempts
    mistakes = []
    correct_count = 0
    
    for sub in submissions:
        if not sub["is_correct"]:
            mistakes.append({
                "timestamp": sub["timestamp"],
                "question_id": sub.get("question_id"),
                "user_answer": sub.get("user_answer"),
                "P_L_before": sub.get("P_L_before", 0.0),
                "P_L_after": sub.get("P_L_after", 0.0),
                "mastery_change": sub.get("P_L_after", 0.0) - sub.get("P_L_before", 0.0),
                "student_elo_before": sub.get("student_elo_before", 1200),
                "student_elo_after": sub.get("student_elo_after", 1200)
            })
        else:
            correct_count += 1
    
    total_attempts = len(submissions)
    accuracy = (correct_count / total_attempts) if total_attempts > 0 else 0.0
    
    return {
        "concept_id": concept_id,
        "total_attempts": total_attempts,
        "mistakes": mistakes,
        "correct_attempts": correct_count,
        "accuracy": round(accuracy, 3),
        "accuracy_percentage": round(accuracy * 100, 1)
    }


@router.delete("/mastery/{user_id}/{subject_id}")
async def reset_mastery(
    user_id: str,
    subject_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Reset mastery state for a user (for testing/debugging).
    
    ⚠️ **Destructive operation** - deletes all progress.
    """
    result = await db["user_mastery"].delete_one({
        "user_id": user_id,
        "subject_id": subject_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mastery state not found")
    
    return {"message": "Mastery state reset successfully"}
