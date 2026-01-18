"""
Recommendation Engine

Combines BKT mastery tracking and knowledge graph traversal to recommend
the optimal next question for a student.

This is the "brain" of the adaptive learning system.
"""

from typing import Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from .bkt_service import BKTService
from .graph_service import GraphService
from ..models.knowledge_graph import KnowledgeGraph
from ..models.user_mastery import UserMastery, ConceptMastery
from ..models.question import Question


class RecommendationEngine:
    """Service for adaptive question recommendations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.bkt_service = BKTService()
        self.graph_service = GraphService(db)
        self.questions_collection = db["questions"]
    
    async def get_next_question(
        self,
        user_id: str,
        subject_id: str
    ) -> Optional[Tuple[Question, str, str]]:
        """
        Get the optimal next question for a student.
        
        This is the main recommendation algorithm that combines:
        - BKT mastery thresholds
        - Knowledge graph traversal
        - Elo-based difficulty matching
        
        Returns:
            (Question, reasoning, concept_id) or None if no suitable question
            
        Algorithm:
        1. Load user mastery state and knowledge graph
        2. Determine target concept:
           - If student has current_focus, check its status
           - If mastered (P_L >= 0.90), unlock next concepts
           - If weak (P_L < 0.40), regress to prerequisites
           - If learning (0.40 <= P_L < 0.90), continue practice
        3. Select question from target concept matching student Elo (±50)
        4. Return question with reasoning message
        """
        # Load mastery state
        mastery_doc = await self.db["user_mastery"].find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        if not mastery_doc:
            # First time - initialize
            return None, "Please initialize user mastery state first.", None
        
        mastery_state = UserMastery(**mastery_doc)
        
        # Load knowledge graph
        graph = await self.graph_service.get_graph(subject_id)
        if not graph:
            return None, "No knowledge graph found for this subject.", None
        
        # Determine target concept
        target_concept, reasoning = await self._determine_target_concept(
            mastery_state, graph
        )
        
        if not target_concept:
            return None, reasoning or "No available concepts to practice.", None
        
        # Find suitable question
        question = await self._find_question_for_concept(
            target_concept, mastery_state.elo_rating
        )
        
        if not question:
            return None, f"No questions available for {target_concept}.", target_concept
        
        return question, reasoning, target_concept
    
    async def _determine_target_concept(
        self,
        mastery_state: UserMastery,
        graph: KnowledgeGraph
    ) -> Tuple[Optional[str], str]:
        """
        Determine which concept the student should work on next.
        
        Returns:
            (concept_id, reasoning_message)
        """
        # Step 1: Check if student has a current focus
        if mastery_state.current_focus:
            focus_id = mastery_state.current_focus
            
            if focus_id not in mastery_state.concepts:
                # Current focus not yet attempted
                return focus_id, f"Continuing work on {graph.nodes[focus_id].name}"
            
            focus_mastery = mastery_state.concepts[focus_id]
            status = self.bkt_service.determine_mastery_status(focus_mastery.P_L)
            
            # Check if mastered
            if status == "mastered":
                # Unlock next concepts
                new_unlocks = self.graph_service.get_next_unlockable_concepts(
                    graph,
                    set(mastery_state.mastered_concepts),
                    set(mastery_state.unlocked_concepts)
                )
                
                if new_unlocks:
                    # Pick first unlockable concept
                    next_concept = new_unlocks[0]
                    return next_concept, f"Mastered {graph.nodes[focus_id].name}! Moving to {graph.nodes[next_concept].name}."
                else:
                    # All concepts mastered or no more unlocks
                    return None, "Congratulations! You've mastered all available concepts."
            
            # Check if weak (needs regression)
            elif status == "locked":
                # Find weak prerequisite
                weak_prereq = self.graph_service.find_weak_prerequisite(
                    graph,
                    mastery_state.concepts,
                    focus_id,
                    threshold=BKTService.LEARNING_THRESHOLD
                )
                
                if weak_prereq:
                    return weak_prereq, f"Struggling with {graph.nodes[focus_id].name}. Let's strengthen {graph.nodes[weak_prereq].name} first."
                else:
                    # No weak prerequisites - continue with current focus
                    return focus_id, f"Continuing practice on {graph.nodes[focus_id].name}"
            
            # Learning status - continue practice
            else:
                return focus_id, f"Making progress on {graph.nodes[focus_id].name}. Keep practicing!"
        
        # Step 2: No current focus - find something to start
        # Check unlocked concepts
        if mastery_state.unlocked_concepts:
            # Find concept with lowest observations (least practiced)
            least_practiced = None
            min_observations = float('inf')
            
            for concept_id in mastery_state.unlocked_concepts:
                obs = mastery_state.concepts.get(concept_id, ConceptMastery()).observations
                if obs < min_observations:
                    min_observations = obs
                    least_practiced = concept_id
            
            if least_practiced:
                return least_practiced, f"Starting work on {graph.nodes[least_practiced].name}"
        
        # Step 3: Nothing unlocked - start with root concepts
        if graph.root_concepts:
            root = graph.root_concepts[0]
            return root, f"Beginning with foundational concept: {graph.nodes[root].name}"
        
        return None, "No concepts available."
    
    async def _find_question_for_concept(
        self,
        concept_id: str,
        student_elo: int,
        elo_tolerance: int = 50
    ) -> Optional[Question]:
        """
        Find a suitable question for the given concept matching student Elo.
        
        Args:
            concept_id: Target concept
            student_elo: Student's current Elo rating
            elo_tolerance: Allowed Elo deviation (default ±50)
        
        Returns:
            Question or None
        """
        # Calculate Elo range
        min_elo, max_elo = self.bkt_service.calculate_elo_range(
            student_elo, elo_tolerance
        )
        
        # Query for questions in this concept and Elo range
        question_doc = await self.questions_collection.find_one({
            "concept_id": concept_id,
            "elo_rating": {"$gte": min_elo, "$lte": max_elo}
        })
        
        if not question_doc:
            # No question in Elo range - try any question in this concept
            question_doc = await self.questions_collection.find_one({
                "concept_id": concept_id
            })
        
        if question_doc:
            return Question(**question_doc)
        
        return None
    
    async def process_answer_submission(
        self,
        user_id: str,
        subject_id: str,
        question_id: str,
        is_correct: bool,
        mistake_count: int = 0
    ) -> Dict:
        """
        Process an answer submission and update BKT + Elo.

        This is called after a student submits an answer.

        Args:
            user_id: User identifier
            subject_id: Subject identifier
            question_id: Question identifier
            is_correct: Whether the final answer was correct
            mistake_count: Number of mistakes made during problem solving

        Returns:
            Dict with update results, achievements, and next recommendation
        """
        # Load question
        question_doc = await self.questions_collection.find_one({"_id": question_id})
        if not question_doc:
            return {"error": "Question not found"}
        
        question = Question(**question_doc)
        concept_id = question.concept_id
        
        # Load user mastery
        mastery_doc = await self.db["user_mastery"].find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        if not mastery_doc:
            return {"error": "User mastery state not found"}
        
        mastery_state = UserMastery(**mastery_doc)
        
        # Get or create concept mastery
        if concept_id not in mastery_state.concepts:
            # Initialize concept if not tracked yet
            if concept_id not in mastery_state.concepts:
                # Get default BKT params from graph
                if graph and concept_id in graph.nodes:
                    default_params = graph.nodes[concept_id].default_params
                    mastery_state.concepts[concept_id] = ConceptMastery(
                        P_L=default_params.P_L0,
                        P_T=default_params.P_T,
                        P_G=default_params.P_G,
                        P_S=default_params.P_S
                    )
                else:
                    # Use defaults if no graph node
                    mastery_state.concepts[concept_id] = ConceptMastery(
                        P_L=0.10,
                        P_T=0.10,
                        P_G=0.25,
                        P_S=0.10
                    )
        
        concept_mastery = mastery_state.concepts[concept_id]
        
        # Save before state
        P_L_before = concept_mastery.P_L
        student_elo_before = mastery_state.elo_rating
        question_elo_before = question.elo_rating
        status_before = self.bkt_service.determine_mastery_status(P_L_before)
        
        # Update BKT (with mistake count affecting learning rate)
        bkt_result = self.bkt_service.full_bkt_update(
            P_L_old=concept_mastery.P_L,
            is_correct=is_correct,
            P_T=concept_mastery.P_T,
            P_G=concept_mastery.P_G,
            P_S=concept_mastery.P_S,
            mistake_count=mistake_count
        )
        
        # Update Elo
        new_student_elo, new_question_elo = self.bkt_service.update_elo(
            student_elo=mastery_state.elo_rating,
            question_elo=question.elo_rating,
            is_correct=is_correct
        )
        
        # Apply updates
        concept_mastery.P_L = bkt_result["P_L_new"]
        concept_mastery.observations += 1
        if is_correct:
            concept_mastery.correct_count += 1
        concept_mastery.mastery_status = bkt_result["mastery_status_new"]
        
        mastery_state.elo_rating = new_student_elo
        mastery_state.total_questions_answered += 1
        
        # Check for achievements
        unlocked_concepts = []
        concept_mastered = False
        
        if bkt_result["mastery_status_new"] == "mastered" and status_before != "mastered":
            # Newly mastered!
            concept_mastered = True
            if concept_id not in mastery_state.mastered_concepts:
                mastery_state.mastered_concepts.append(concept_id)
            
            # Check for new unlocks
            graph = await self.graph_service.get_graph(subject_id)
            if graph:
                new_unlocks = self.graph_service.get_next_unlockable_concepts(
                    graph,
                    set(mastery_state.mastered_concepts),
                    set(mastery_state.unlocked_concepts)
                )
                
                for unlock_id in new_unlocks:
                    if unlock_id not in mastery_state.unlocked_concepts:
                        mastery_state.unlocked_concepts.append(unlock_id)
                        unlocked_concepts.append(unlock_id)
        
        # Update question stats
        await self.questions_collection.update_one(
            {"_id": question_id},
            {
                "$set": {"elo_rating": new_question_elo},
                "$inc": {
                    "times_attempted": 1,
                    "times_correct": 1 if is_correct else 0
                }
            }
        )
        
        # Update mastery state in database
        await self.db["user_mastery"].update_one(
            {"user_id": user_id, "subject_id": subject_id},
            {
                "$set": {
                    f"concepts.{concept_id}": concept_mastery.model_dump(),
                    "elo_rating": mastery_state.elo_rating,
                    "total_questions_answered": mastery_state.total_questions_answered,
                    "mastered_concepts": mastery_state.mastered_concepts,
                    "unlocked_concepts": mastery_state.unlocked_concepts
                }
            }
        )
        
        # Generate feedback message
        feedback = self._generate_feedback_message(
            is_correct, bkt_result, concept_mastered, unlocked_concepts
        )
        
        # Get next recommendation
        next_question, reasoning, next_concept = await self.get_next_question(
            user_id, subject_id
        )
        
        return {
            "is_correct": is_correct,
            "mastery_change": bkt_result["mastery_change"],
            "elo_change": new_student_elo - student_elo_before,
            "new_mastery_probability": bkt_result["P_L_new"],
            "new_mastery_status": bkt_result["mastery_status_new"],
            "new_student_elo": new_student_elo,
            "unlocked_concepts": unlocked_concepts,
            "concept_mastered": concept_mastered,
            "feedback_message": feedback,
            "recommended_next_concept": next_concept,
            "next_question_id": next_question.id if next_question else None
        }
    
    def _generate_feedback_message(
        self,
        is_correct: bool,
        bkt_result: Dict,
        concept_mastered: bool,
        unlocked_concepts: List[str]
    ) -> str:
        """Generate human-readable feedback message."""
        if concept_mastered:
            msg = "🎉 Concept mastered! "
            if unlocked_concepts:
                msg += f"You've unlocked {len(unlocked_concepts)} new concept(s)!"
            return msg
        
        if is_correct:
            mastery_pct = int(bkt_result["P_L_new"] * 100)
            if bkt_result["mastery_status_new"] == "learning":
                return f"✓ Correct! You're making progress. (Mastery: {mastery_pct}%)"
            else:
                return f"✓ Correct! Keep practicing to strengthen this concept. (Mastery: {mastery_pct}%)"
        else:
            if bkt_result["mastery_status_new"] == "locked":
                return "✗ Incorrect. This concept might need more foundational work."
            else:
                return "✗ Incorrect. Review the solution and try again."
    
    async def initialize_user_mastery(
        self,
        user_id: str,
        subject_id: str
    ) -> str:
        """
        Initialize user mastery state for a subject.
        
        Unlocks root concepts and sets starting Elo.
        """
        from bson import ObjectId
        from datetime import datetime
        
        # Check if already exists
        existing = await self.db["user_mastery"].find_one({
            "user_id": user_id,
            "subject_id": subject_id
        })
        
        if existing:
            return existing["_id"]
        
        # Load graph to get root concepts
        graph = await self.graph_service.get_graph(subject_id)
        if not graph:
            raise ValueError("No knowledge graph found for this subject")
        
        # Create mastery state
        mastery_doc = {
            "_id": str(ObjectId()),
            "user_id": user_id,
            "subject_id": subject_id,
            "elo_rating": 1200,  # Starting Elo
            "concepts": {},
            "unlocked_concepts": graph.root_concepts.copy(),  # Unlock roots
            "mastered_concepts": [],
            "current_focus": graph.root_concepts[0] if graph.root_concepts else None,
            "total_questions_answered": 0,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }
        
        await self.db["user_mastery"].insert_one(mastery_doc)
        return mastery_doc["_id"]
