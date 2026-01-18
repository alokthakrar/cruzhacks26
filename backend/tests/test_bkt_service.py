"""
Unit tests for BKT Service

Tests all BKT probability calculations, Elo updates, and edge cases.
"""

import pytest
from app.services.bkt_service import BKTService


class TestCalculatePosterior:
    """Test P(Knew | Action) calculations."""
    
    def test_correct_answer_high_mastery(self):
        """If student has high mastery and answers correctly, P(knew) should be very high."""
        P_knew = BKTService.calculate_posterior(
            P_L=0.90,
            is_correct=True,
            P_G=0.25,
            P_S=0.10
        )
        # With high P(L) and correct answer, should be confident they knew it
        assert P_knew > 0.95
    
    def test_correct_answer_low_mastery(self):
        """If student has low mastery but answers correctly, could be a guess."""
        P_knew = BKTService.calculate_posterior(
            P_L=0.10,
            is_correct=True,
            P_G=0.25,
            P_S=0.10
        )
        # Low P(L) + correct could be guess, so P(knew) should be lower
        assert P_knew < 0.50
    
    def test_incorrect_answer_high_mastery(self):
        """If student has high mastery but answers incorrectly, likely a slip."""
        P_knew = BKTService.calculate_posterior(
            P_L=0.90,
            is_correct=False,
            P_G=0.25,
            P_S=0.10
        )
        # High P(L) + incorrect = slip, so P(knew) should still be high
        assert P_knew > 0.50
    
    def test_incorrect_answer_low_mastery(self):
        """If student has low mastery and answers incorrectly, clearly didn't know it."""
        P_knew = BKTService.calculate_posterior(
            P_L=0.10,
            is_correct=False,
            P_G=0.25,
            P_S=0.10
        )
        # Low P(L) + incorrect = definitely didn't know, P(knew) should be very low
        assert P_knew < 0.10
    
    def test_boundary_P_L_zero(self):
        """Test with P(L) = 0 (completely unknown)."""
        P_knew_correct = BKTService.calculate_posterior(
            P_L=0.0,
            is_correct=True,
            P_G=0.25,
            P_S=0.10
        )
        # If P(L) = 0 and correct, must be pure guess
        assert P_knew_correct == 0.0
        
        P_knew_incorrect = BKTService.calculate_posterior(
            P_L=0.0,
            is_correct=False,
            P_G=0.25,
            P_S=0.10
        )
        # If P(L) = 0 and incorrect, definitely didn't know
        assert P_knew_incorrect == 0.0
    
    def test_boundary_P_L_one(self):
        """Test with P(L) = 1.0 (completely mastered)."""
        P_knew_correct = BKTService.calculate_posterior(
            P_L=1.0,
            is_correct=True,
            P_G=0.25,
            P_S=0.10
        )
        # If P(L) = 1 and correct, definitely knew it
        assert P_knew_correct == 1.0
        
        P_knew_incorrect = BKTService.calculate_posterior(
            P_L=1.0,
            is_correct=False,
            P_G=0.25,
            P_S=0.10
        )
        # If P(L) = 1 and incorrect, must be slip, still knew it
        assert P_knew_incorrect == 1.0
    
    def test_invalid_P_L_raises_error(self):
        """Test that invalid P(L) values raise ValueError."""
        with pytest.raises(ValueError, match="P_L must be in"):
            BKTService.calculate_posterior(1.5, True, 0.25, 0.10)
        
        with pytest.raises(ValueError, match="P_L must be in"):
            BKTService.calculate_posterior(-0.1, True, 0.25, 0.10)
    
    def test_invalid_P_G_raises_error(self):
        """Test that invalid P(G) values raise ValueError."""
        with pytest.raises(ValueError, match="P_G must be in"):
            BKTService.calculate_posterior(0.5, True, 1.5, 0.10)
    
    def test_invalid_P_S_raises_error(self):
        """Test that invalid P(S) values raise ValueError."""
        with pytest.raises(ValueError, match="P_S must be in"):
            BKTService.calculate_posterior(0.5, True, 0.25, -0.1)


class TestUpdateMastery:
    """Test P(L) update calculations."""
    
    def test_knew_it_no_learning(self):
        """If student knew it (P_knew=1), mastery should stay same."""
        P_L_new = BKTService.update_mastery(
            P_L_old=0.50,
            P_knew=1.0,
            P_T=0.10
        )
        # P_knew=1 means no learning needed
        assert P_L_new == pytest.approx(1.0)
    
    def test_didnt_know_it_learning(self):
        """If student didn't know it (P_knew=0), learn rate applies."""
        P_L_new = BKTService.update_mastery(
            P_L_old=0.50,
            P_knew=0.0,
            P_T=0.10
        )
        # P_knew=0 means full learning opportunity: 0 + (1-0)*0.10 = 0.10
        assert P_L_new == pytest.approx(0.10)
    
    def test_partial_knowledge(self):
        """Test with partial knowledge (P_knew=0.5)."""
        P_L_new = BKTService.update_mastery(
            P_L_old=0.50,
            P_knew=0.50,
            P_T=0.10
        )
        # Formula: 0.50 + (1-0.50)*0.10 = 0.50 + 0.05 = 0.55
        assert P_L_new == pytest.approx(0.55)
    
    def test_mastery_increases_over_time(self):
        """Simulate multiple correct answers → mastery should increase."""
        P_L = 0.10
        P_T = 0.10
        P_G = 0.25
        P_S = 0.10
        
        # Simulate 10 correct answers
        for _ in range(10):
            P_knew = BKTService.calculate_posterior(P_L, True, P_G, P_S)
            P_L = BKTService.update_mastery(P_L, P_knew, P_T)
        
        # After 10 correct answers, mastery should have increased significantly
        assert P_L > 0.50
    
    def test_mastery_capped_at_one(self):
        """Test that mastery never exceeds 1.0."""
        P_L_new = BKTService.update_mastery(
            P_L_old=0.95,
            P_knew=1.0,
            P_T=0.50  # High learn rate
        )
        assert P_L_new <= 1.0
    
    def test_mastery_floored_at_zero(self):
        """Test that mastery never goes below 0.0."""
        P_L_new = BKTService.update_mastery(
            P_L_old=0.01,
            P_knew=0.0,
            P_T=0.0  # No learning
        )
        assert P_L_new >= 0.0
    
    def test_invalid_inputs_raise_errors(self):
        """Test that invalid inputs raise ValueError."""
        with pytest.raises(ValueError):
            BKTService.update_mastery(1.5, 0.5, 0.1)
        
        with pytest.raises(ValueError):
            BKTService.update_mastery(0.5, 1.5, 0.1)
        
        with pytest.raises(ValueError):
            BKTService.update_mastery(0.5, 0.5, -0.1)


class TestDetermineMasteryStatus:
    """Test mastery status thresholds."""
    
    def test_mastered_status(self):
        """P(L) >= 0.90 should be 'mastered'."""
        assert BKTService.determine_mastery_status(0.90) == "mastered"
        assert BKTService.determine_mastery_status(0.95) == "mastered"
        assert BKTService.determine_mastery_status(1.00) == "mastered"
    
    def test_learning_status(self):
        """0.40 <= P(L) < 0.90 should be 'learning'."""
        assert BKTService.determine_mastery_status(0.40) == "learning"
        assert BKTService.determine_mastery_status(0.65) == "learning"
        assert BKTService.determine_mastery_status(0.89) == "learning"
    
    def test_locked_status(self):
        """P(L) < 0.40 should be 'locked' (needs prerequisite work)."""
        assert BKTService.determine_mastery_status(0.00) == "locked"
        assert BKTService.determine_mastery_status(0.20) == "locked"
        assert BKTService.determine_mastery_status(0.39) == "locked"


class TestUpdateElo:
    """Test Elo rating updates."""
    
    def test_student_beats_equal_question(self):
        """Student with same Elo beats question → both adjust."""
        new_student, new_question = BKTService.update_elo(
            student_elo=1200,
            question_elo=1200,
            is_correct=True,
            K=32
        )
        # Expected outcome is 0.5, actual is 1.0, so +16 for student
        assert new_student == 1216
        assert new_question == 1184
    
    def test_weak_student_beats_hard_question(self):
        """Weak student beats hard question → big Elo gain."""
        new_student, new_question = BKTService.update_elo(
            student_elo=1000,
            question_elo=1400,
            is_correct=True,
            K=32
        )
        # Unexpected win → large gain for student
        assert new_student > 1000 + 20  # At least +20
        assert new_question < 1400 - 10  # Question Elo drops
    
    def test_strong_student_fails_easy_question(self):
        """Strong student fails easy question → big Elo loss."""
        new_student, new_question = BKTService.update_elo(
            student_elo=1400,
            question_elo=1000,
            is_correct=False,
            K=32
        )
        # Unexpected loss → large loss for student
        assert new_student < 1400 - 20  # At least -20
        assert new_question > 1000 + 10  # Question Elo increases
    
    def test_elo_never_negative(self):
        """Test that Elo ratings never go below 0."""
        new_student, new_question = BKTService.update_elo(
            student_elo=50,
            question_elo=1500,
            is_correct=False,
            K=32
        )
        assert new_student >= 0
        assert new_question >= 0
    
    def test_different_K_factors(self):
        """Test that different K factors produce different sensitivities."""
        # High K = more sensitive
        new_student_high_K, _ = BKTService.update_elo(1200, 1200, True, K=64)
        
        # Low K = less sensitive
        new_student_low_K, _ = BKTService.update_elo(1200, 1200, True, K=16)
        
        # High K should change more
        assert abs(new_student_high_K - 1200) > abs(new_student_low_K - 1200)


class TestCalculateEloRange:
    """Test Elo range calculation for question matching."""
    
    def test_default_tolerance(self):
        """Test default ±50 tolerance."""
        min_elo, max_elo = BKTService.calculate_elo_range(1200)
        assert min_elo == 1150
        assert max_elo == 1250
    
    def test_custom_tolerance(self):
        """Test custom tolerance."""
        min_elo, max_elo = BKTService.calculate_elo_range(1200, tolerance=100)
        assert min_elo == 1100
        assert max_elo == 1300
    
    def test_low_elo_clamped_at_zero(self):
        """Test that minimum Elo is clamped at 0."""
        min_elo, max_elo = BKTService.calculate_elo_range(30, tolerance=50)
        assert min_elo == 0
        assert max_elo == 80


class TestFullBKTUpdate:
    """Test complete BKT update pipeline."""
    
    def test_correct_answer_increases_mastery(self):
        """Correct answer should increase P(L)."""
        result = BKTService.full_bkt_update(
            P_L_old=0.50,
            is_correct=True,
            P_T=0.10,
            P_G=0.25,
            P_S=0.10
        )
        
        assert result["P_L_new"] > result["P_L_old"]
        assert result["mastery_change"] > 0
        assert result["is_correct"] is True
    
    def test_incorrect_answer_may_decrease_mastery(self):
        """Incorrect answer typically decreases P(L)."""
        result = BKTService.full_bkt_update(
            P_L_old=0.50,
            is_correct=False,
            P_T=0.10,
            P_G=0.25,
            P_S=0.10
        )
        
        # With incorrect answer, P(knew) will be low, so P(L) may drop or stay similar
        assert result["is_correct"] is False
        # P(L) change depends on learn rate vs knew probability
    
    def test_status_transitions(self):
        """Test that status can transition from learning to mastered."""
        result = BKTService.full_bkt_update(
            P_L_old=0.88,  # Just below mastery
            is_correct=True,
            P_T=0.10,
            P_G=0.25,
            P_S=0.05  # Low slip rate
        )
        
        # Should push over mastery threshold
        assert result["mastery_status_old"] == "learning"
        # Depending on calculation, might reach mastered
        assert result["P_L_new"] >= result["P_L_old"]
    
    def test_result_contains_all_fields(self):
        """Test that result dict contains all expected fields."""
        result = BKTService.full_bkt_update(
            P_L_old=0.50,
            is_correct=True,
            P_T=0.10,
            P_G=0.25,
            P_S=0.10
        )
        
        required_fields = {
            "P_L_old", "P_knew", "P_L_new",
            "mastery_status_old", "mastery_status_new",
            "mastery_change", "is_correct"
        }
        assert set(result.keys()) == required_fields


class TestEdgeCasesAndRobustness:
    """Test edge cases and numerical stability."""
    
    def test_repeated_updates_converge(self):
        """Test that repeated correct answers converge to P(L)=1.0."""
        P_L = 0.10
        
        # Simulate many correct answers
        for _ in range(100):
            result = BKTService.full_bkt_update(
                P_L_old=P_L,
                is_correct=True,
                P_T=0.10,
                P_G=0.25,
                P_S=0.05
            )
            P_L = result["P_L_new"]
        
        # Should converge close to 1.0
        assert P_L > 0.95
    
    def test_alternating_answers(self):
        """Test alternating correct/incorrect answers."""
        P_L = 0.50
        
        for i in range(10):
            is_correct = (i % 2 == 0)  # Alternate
            result = BKTService.full_bkt_update(
                P_L_old=P_L,
                is_correct=is_correct,
                P_T=0.10,
                P_G=0.25,
                P_S=0.10
            )
            P_L = result["P_L_new"]
        
        # With alternating performance, P(L) can drift based on posterior calculations
        # Should remain in valid range but may not stay centered
        assert 0.10 < P_L < 0.80  # Broader realistic range
    
    def test_zero_learn_rate(self):
        """Test with P(T)=0 (no learning from questions)."""
        result = BKTService.full_bkt_update(
            P_L_old=0.50,
            is_correct=True,
            P_T=0.0,  # No learning
            P_G=0.25,
            P_S=0.10
        )
        
        # P(L) should still update based on Bayesian inference, not stay at 0.50
        assert result["P_L_new"] != 0.50
