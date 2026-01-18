"""
Bayesian Knowledge Tracing Service

Implements the core BKT probability update logic for mastery tracking.
All methods are pure functions for easy testing.
"""

from typing import Literal, Tuple


class BKTService:
    """Service for Bayesian Knowledge Tracing calculations."""
    
    # Mastery thresholds
    MASTERY_THRESHOLD = 0.90  # P(L) >= 0.90 → mastered
    LEARNING_THRESHOLD = 0.40  # 0.40 <= P(L) < 0.90 → learning
    # P(L) < 0.40 → needs prerequisite work
    
    @staticmethod
    def calculate_posterior(
        P_L: float,
        is_correct: bool,
        P_G: float,
        P_S: float
    ) -> float:
        """
        Calculate P(Knew | Action) using Bayes' Theorem.
        
        This determines the probability the student knew the concept
        at the moment they answered, given their performance.
        
        Args:
            P_L: Prior probability of mastery (0-1)
            is_correct: Whether the student answered correctly
            P_G: Guess probability (correct despite not knowing)
            P_S: Slip probability (incorrect despite knowing)
        
        Returns:
            P(Knew | Action): Posterior probability (0-1)
        
        Formula (if correct):
            P(Knew | Correct) = [P(L) * (1 - P(S))] / 
                                [P(L) * (1 - P(S)) + (1 - P(L)) * P(G)]
        
        Formula (if incorrect):
            P(Knew | Incorrect) = [P(L) * P(S)] / 
                                  [P(L) * P(S) + (1 - P(L)) * (1 - P(G))]
        """
        # Validate inputs
        if not (0 <= P_L <= 1):
            raise ValueError(f"P_L must be in [0, 1], got {P_L}")
        if not (0 <= P_G <= 1):
            raise ValueError(f"P_G must be in [0, 1], got {P_G}")
        if not (0 <= P_S <= 1):
            raise ValueError(f"P_S must be in [0, 1], got {P_S}")
        
        if is_correct:
            # Student answered correctly
            numerator = P_L * (1 - P_S)
            denominator = P_L * (1 - P_S) + (1 - P_L) * P_G
        else:
            # Student answered incorrectly
            numerator = P_L * P_S
            denominator = P_L * P_S + (1 - P_L) * (1 - P_G)
        
        # Handle edge case: denominator = 0
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    @staticmethod
    def update_mastery(
        P_L_old: float,
        P_knew: float,
        P_T: float
    ) -> float:
        """
        Update the mastery probability after a question.
        
        Args:
            P_L_old: Previous mastery probability (0-1)
            P_knew: Posterior probability from calculate_posterior (0-1)
            P_T: Transition probability (learn rate, 0-1)
        
        Returns:
            P(L_new): Updated mastery probability (0-1)
        
        Formula:
            P(L_new) = P(Knew | Action) + (1 - P(Knew | Action)) * P(T)
        
        Intuition: 
            - If they knew it (P_knew ≈ 1), mastery doesn't change much
            - If they didn't know it (P_knew ≈ 0), they might have learned it (P_T chance)
        """
        # Validate inputs
        if not (0 <= P_L_old <= 1):
            raise ValueError(f"P_L_old must be in [0, 1], got {P_L_old}")
        if not (0 <= P_knew <= 1):
            raise ValueError(f"P_knew must be in [0, 1], got {P_knew}")
        if not (0 <= P_T <= 1):
            raise ValueError(f"P_T must be in [0, 1], got {P_T}")
        
        P_L_new = P_knew + (1 - P_knew) * P_T
        
        # Ensure result is in valid range (due to floating point)
        return max(0.0, min(1.0, P_L_new))
    
    @staticmethod
    def determine_mastery_status(P_L: float) -> Literal["locked", "learning", "mastered"]:
        """
        Determine mastery status based on probability threshold.
        
        Args:
            P_L: Current mastery probability (0-1)
        
        Returns:
            "mastered": P(L) >= 0.90
            "learning": 0.40 <= P(L) < 0.90
            "locked": P(L) < 0.40 (should regress to prerequisites)
        """
        if P_L >= BKTService.MASTERY_THRESHOLD:
            return "mastered"
        elif P_L >= BKTService.LEARNING_THRESHOLD:
            return "learning"
        else:
            return "locked"  # Not truly locked, but needs foundational work
    
    @staticmethod
    def update_elo(
        student_elo: int,
        question_elo: int,
        is_correct: bool,
        K: int = 32
    ) -> Tuple[int, int]:
        """
        Update Elo ratings for both student and question.
        
        Standard Elo formula used in chess, adapted for education.
        
        Args:
            student_elo: Current student Elo rating
            question_elo: Current question Elo rating
            is_correct: Whether student answered correctly
            K: K-factor (sensitivity of rating changes, default 32)
        
        Returns:
            (new_student_elo, new_question_elo)
        
        Formula:
            Expected(A) = 1 / (1 + 10^((Elo_B - Elo_A) / 400))
            New_Elo = Old_Elo + K * (Actual - Expected)
        
        Intuition:
            - Student beats hard question → Student Elo goes up a lot
            - Student fails easy question → Student Elo goes down a lot
            - Question is beaten by weak student → Question Elo goes down
        """
        # Calculate expected scores
        expected_student = 1 / (1 + 10 ** ((question_elo - student_elo) / 400))
        expected_question = 1 - expected_student
        
        # Actual scores (1 if won, 0 if lost)
        actual_student = 1.0 if is_correct else 0.0
        actual_question = 1.0 - actual_student
        
        # Update ratings
        new_student_elo = student_elo + K * (actual_student - expected_student)
        new_question_elo = question_elo + K * (actual_question - expected_question)
        
        # Round to integers and ensure non-negative
        new_student_elo = max(0, int(round(new_student_elo)))
        new_question_elo = max(0, int(round(new_question_elo)))
        
        return new_student_elo, new_question_elo
    
    @staticmethod
    def calculate_elo_range(student_elo: int, tolerance: int = 50) -> Tuple[int, int]:
        """
        Calculate Elo range for question matching.
        
        Args:
            student_elo: Current student Elo rating
            tolerance: +/- range for matching (default ±50)
        
        Returns:
            (min_elo, max_elo) for question selection
        """
        return (max(0, student_elo - tolerance), student_elo + tolerance)
    
    @classmethod
    def full_bkt_update(
        cls,
        P_L_old: float,
        is_correct: bool,
        P_T: float,
        P_G: float,
        P_S: float
    ) -> dict:
        """
        Complete BKT update in one call (convenience method).
        
        Returns dict with all intermediate values for logging/debugging.
        
        Args:
            P_L_old: Previous mastery probability
            is_correct: Whether answer was correct
            P_T: Transition probability (learn rate)
            P_G: Guess probability
            P_S: Slip probability
        
        Returns:
            {
                "P_L_old": float,
                "P_knew": float,
                "P_L_new": float,
                "mastery_status_old": str,
                "mastery_status_new": str,
                "mastery_change": float
            }
        """
        # Step 1: Calculate posterior
        P_knew = cls.calculate_posterior(P_L_old, is_correct, P_G, P_S)
        
        # Step 2: Update mastery
        P_L_new = cls.update_mastery(P_L_old, P_knew, P_T)
        
        # Step 3: Determine status
        status_old = cls.determine_mastery_status(P_L_old)
        status_new = cls.determine_mastery_status(P_L_new)
        
        return {
            "P_L_old": P_L_old,
            "P_knew": P_knew,
            "P_L_new": P_L_new,
            "mastery_status_old": status_old,
            "mastery_status_new": status_new,
            "mastery_change": P_L_new - P_L_old,
            "is_correct": is_correct
        }
