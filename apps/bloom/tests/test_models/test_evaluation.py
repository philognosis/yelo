"""
Tests for Evaluation Models

Tests Evaluation, PeerFeedback, SelfEvaluation, ManagerEvaluation,
and evaluation workflow state management.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from bloom.models.evaluation import (
    Evaluation,
    EvaluationPhase,
    EvaluationState,
    FeedbackSource,
    ManagerEvaluation,
    PeerFeedback,
    PromotionEligibility,
    Rating,
    SelfEvaluation,
)


class TestPeerFeedback:
    """Test PeerFeedback model"""

    def test_peer_feedback_creation(self, mock_peer_feedback):
        """Test creating peer feedback"""
        assert mock_peer_feedback.peer_name == "Bob Smith"
        assert mock_peer_feedback.input_method == "text"
        assert mock_peer_feedback.synthesized_feedback is not None
        assert mock_peer_feedback.technical_rating == Rating.EXCEEDS

    def test_peer_feedback_voice_input(self):
        """Test peer feedback from voice dictation"""
        feedback = PeerFeedback(
            evaluation_id=uuid4(),
            peer_id=uuid4(),
            peer_name="Voice Peer",
            raw_input="Um, so like, great work on the project",
            input_method="voice",
        )
        assert feedback.input_method == "voice"
        assert feedback.synthesized_feedback is None  # Not yet synthesized

    def test_peer_feedback_anonymous(self):
        """Test anonymous peer feedback"""
        feedback = PeerFeedback(
            evaluation_id=uuid4(),
            peer_id=uuid4(),
            peer_name="Anonymous",
            raw_input="Good technical skills",
            is_anonymous=True,
        )
        assert feedback.is_anonymous is True

    def test_peer_feedback_with_evidence(self):
        """Test peer feedback with supporting documents"""
        feedback = PeerFeedback(
            evaluation_id=uuid4(),
            peer_id=uuid4(),
            peer_name="Peer",
            raw_input="Great work",
            supporting_docs=[
                "https://docs.com/project1",
                "https://docs.com/project2",
            ],
        )
        assert len(feedback.supporting_docs) == 2


class TestSelfEvaluation:
    """Test SelfEvaluation model"""

    def test_self_evaluation_creation(self, mock_self_evaluation):
        """Test creating self evaluation"""
        assert "API migration" in mock_self_evaluation.raw_achievements
        assert mock_self_evaluation.synthesized_achievements is not None
        assert len(mock_self_evaluation.uploaded_docs) == 1

    def test_self_evaluation_all_sections(self):
        """Test self evaluation with all sections filled"""
        self_eval = SelfEvaluation(
            evaluation_id=uuid4(),
            employee_id=uuid4(),
            raw_achievements="Achieved X, Y, Z",
            raw_challenges="Faced challenges A, B",
            raw_growth_areas="Want to improve in C, D",
            raw_goals="Goals for next year",
        )
        assert self_eval.raw_achievements is not None
        assert self_eval.raw_challenges is not None
        assert self_eval.raw_growth_areas is not None
        assert self_eval.raw_goals is not None

    def test_self_evaluation_minimal(self):
        """Test self evaluation with only required fields"""
        self_eval = SelfEvaluation(
            evaluation_id=uuid4(),
            employee_id=uuid4(),
            raw_achievements="Basic achievements",
        )
        assert self_eval.raw_challenges is None
        assert self_eval.raw_growth_areas is None


class TestManagerEvaluation:
    """Test ManagerEvaluation model"""

    def test_manager_evaluation_creation(self, mock_manager_evaluation):
        """Test creating manager evaluation"""
        assert mock_manager_evaluation.ai_draft_summary is not None
        assert mock_manager_evaluation.overall_rating == Rating.EXCEEDS
        assert mock_manager_evaluation.promotion_eligibility == PromotionEligibility.READY_NEXT_CYCLE

    def test_manager_evaluation_ratings(self):
        """Test different rating combinations"""
        evaluation = ManagerEvaluation(
            evaluation_id=uuid4(),
            manager_id=uuid4(),
            employee_id=uuid4(),
            final_summary="Summary",
            overall_rating=Rating.EXCEPTIONAL,
            technical_rating=Rating.EXCEPTIONAL,
            leadership_rating=Rating.EXCEEDS,
            promotion_eligibility=PromotionEligibility.READY_NOW,
        )
        assert evaluation.overall_rating == Rating.EXCEPTIONAL
        assert evaluation.technical_rating == Rating.EXCEPTIONAL
        assert evaluation.leadership_rating == Rating.EXCEEDS

    def test_manager_evaluation_with_questions(self, mock_manager_evaluation):
        """Test AI-generated clarifying questions"""
        assert len(mock_manager_evaluation.ai_questions) > 0
        question = mock_manager_evaluation.ai_questions[0]
        assert "question" in question
        assert "category" in question

    def test_manager_evaluation_evidence_map(self, mock_manager_evaluation):
        """Test evidence mapping in draft"""
        evidence_map = mock_manager_evaluation.ai_draft_evidence_map
        assert evidence_map is not None
        assert "technical_excellence" in evidence_map
        assert len(evidence_map["technical_excellence"]) > 0

    def test_manager_evaluation_calibration(self):
        """Test calibration workflow"""
        evaluation = ManagerEvaluation(
            evaluation_id=uuid4(),
            manager_id=uuid4(),
            employee_id=uuid4(),
            final_summary="Summary",
            overall_rating=Rating.EXCEEDS,
            promotion_eligibility=PromotionEligibility.READY_NEXT_CYCLE,
            pre_calibration_rating=Rating.EXCEPTIONAL,  # Changed during calibration
            calibration_notes="Committee adjusted rating based on peer comparison",
        )
        assert evaluation.pre_calibration_rating == Rating.EXCEPTIONAL
        assert evaluation.overall_rating == Rating.EXCEEDS  # After calibration
        assert evaluation.calibration_notes is not None


class TestEvaluation:
    """Test Evaluation model and workflow"""

    def test_evaluation_creation(self, mock_evaluation):
        """Test creating evaluation"""
        assert mock_evaluation.cycle_name == "Q4 2024"
        assert mock_evaluation.current_phase == EvaluationPhase.CONTEXT_PEER_SELECTION
        assert mock_evaluation.current_state == EvaluationState.CYCLE_STARTED

    def test_evaluation_phases(self):
        """Test all evaluation phases exist"""
        phases = [
            EvaluationPhase.CONTEXT_PEER_SELECTION,
            EvaluationPhase.DATA_GATHERING,
            EvaluationPhase.MANAGER_EVALUATION,
            EvaluationPhase.CALIBRATION,
            EvaluationPhase.RELEASE_DISCUSSION,
            EvaluationPhase.COMPLETED,
            EvaluationPhase.CANCELLED,
        ]
        assert len(phases) == 7

    def test_evaluation_states_coverage(self):
        """Test that major workflow states exist"""
        required_states = [
            EvaluationState.CYCLE_STARTED,
            EvaluationState.PEER_SUGGESTION_GENERATED,
            EvaluationState.PEER_LIST_LOCKED,
            EvaluationState.PEER_FEEDBACK_IN_PROGRESS,
            EvaluationState.SELF_EVAL_IN_PROGRESS,
            EvaluationState.DATA_GATHERING_COMPLETE,
            EvaluationState.AI_DRAFT_GENERATED,
            EvaluationState.MANAGER_EVAL_COMPLETE,
            EvaluationState.CALIBRATION_COMPLETE,
            EvaluationState.RELEASED,
            EvaluationState.ACKNOWLEDGED,
            EvaluationState.COMPLETED,
        ]
        # Just verify they exist
        for state in required_states:
            assert isinstance(state, EvaluationState)

    def test_add_state_transition(self, mock_evaluation):
        """Test adding state transition to history"""
        old_state = mock_evaluation.current_state

        mock_evaluation.add_state_transition(
            new_state=EvaluationState.PEER_SUGGESTION_GENERATED,
            reason="Context Miner completed analysis",
        )

        assert mock_evaluation.current_state == EvaluationState.PEER_SUGGESTION_GENERATED
        assert len(mock_evaluation.state_history) == 1

        transition = mock_evaluation.state_history[0]
        assert transition["from_state"] == old_state
        assert transition["to_state"] == EvaluationState.PEER_SUGGESTION_GENERATED
        assert transition["reason"] == "Context Miner completed analysis"

    def test_state_transition_with_phase_change(self, mock_evaluation):
        """Test state transition that also changes phase"""
        mock_evaluation.current_state = EvaluationState.PEER_LIST_LOCKED

        mock_evaluation.add_state_transition(
            new_state=EvaluationState.PEER_FEEDBACK_REQUESTED,
            new_phase=EvaluationPhase.DATA_GATHERING,
            reason="Starting data gathering",
        )

        assert mock_evaluation.current_state == EvaluationState.PEER_FEEDBACK_REQUESTED
        assert mock_evaluation.current_phase == EvaluationPhase.DATA_GATHERING

    def test_get_completion_percentage(self, mock_evaluation):
        """Test completion percentage calculation"""
        # Phase 1: 10%
        mock_evaluation.current_phase = EvaluationPhase.CONTEXT_PEER_SELECTION
        assert mock_evaluation.get_completion_percentage() == 0.1

        # Phase 2: 30%
        mock_evaluation.current_phase = EvaluationPhase.DATA_GATHERING
        assert mock_evaluation.get_completion_percentage() == 0.3

        # Phase 3: 50%
        mock_evaluation.current_phase = EvaluationPhase.MANAGER_EVALUATION
        assert mock_evaluation.get_completion_percentage() == 0.5

        # Phase 4: 70%
        mock_evaluation.current_phase = EvaluationPhase.CALIBRATION
        assert mock_evaluation.get_completion_percentage() == 0.7

        # Phase 5: 90%
        mock_evaluation.current_phase = EvaluationPhase.RELEASE_DISCUSSION
        assert mock_evaluation.get_completion_percentage() == 0.9

        # Completed: 100%
        mock_evaluation.current_phase = EvaluationPhase.COMPLETED
        assert mock_evaluation.get_completion_percentage() == 1.0

    def test_is_past_deadline(self, mock_evaluation):
        """Test deadline checking"""
        # Set deadline in the past
        mock_evaluation.peer_selection_deadline = datetime.now() - timedelta(days=1)
        assert mock_evaluation.is_past_deadline("peer_selection") is True

        # Set deadline in the future
        mock_evaluation.peer_feedback_deadline = datetime.now() + timedelta(days=7)
        assert mock_evaluation.is_past_deadline("peer_feedback") is False

        # No deadline set
        mock_evaluation.manager_eval_deadline = None
        assert mock_evaluation.is_past_deadline("manager_eval") is False

    def test_get_pending_feedbacks(self, mock_evaluation):
        """Test getting list of peers who haven't submitted feedback"""
        # Add approved peers
        peer1 = uuid4()
        peer2 = uuid4()
        peer3 = uuid4()
        mock_evaluation.manager_approved_peers = [peer1, peer2, peer3]

        # Add feedback from peer1 only
        feedback = PeerFeedback(
            evaluation_id=mock_evaluation.id,
            peer_id=peer1,
            peer_name="Peer 1",
            raw_input="Great work",
        )
        mock_evaluation.peer_feedbacks = [feedback]

        # Should return peer2 and peer3
        pending = mock_evaluation.get_pending_feedbacks()
        assert len(pending) == 2
        assert peer2 in pending
        assert peer3 in pending
        assert peer1 not in pending

    def test_evaluation_with_all_data(self, mock_evaluation_with_data):
        """Test evaluation with complete data"""
        eval_with_data = mock_evaluation_with_data

        assert len(eval_with_data.suggested_peers) == 5
        assert len(eval_with_data.employee_selected_peers) == 5
        assert len(eval_with_data.manager_approved_peers) == 5
        assert len(eval_with_data.peer_feedbacks) == 5
        assert eval_with_data.self_evaluation is not None
        assert eval_with_data.manager_evaluation is not None


class TestEvaluationComplexScenarios:
    """Complex test scenarios for evaluations"""

    def test_evaluation_full_lifecycle(self, mock_evaluation):
        """Test evaluation progressing through all phases"""
        # Phase 1: Context & Peer Selection
        assert mock_evaluation.current_phase == EvaluationPhase.CONTEXT_PEER_SELECTION

        mock_evaluation.add_state_transition(
            EvaluationState.PEER_SUGGESTION_GENERATED,
            reason="Peers suggested",
        )
        mock_evaluation.add_state_transition(
            EvaluationState.EMPLOYEE_PEER_REVIEW,
            reason="Employee reviewing",
        )
        mock_evaluation.add_state_transition(
            EvaluationState.MANAGER_PEER_APPROVAL,
            reason="Manager approving",
        )
        mock_evaluation.add_state_transition(
            EvaluationState.PEER_LIST_LOCKED,
            reason="Peers locked",
        )

        # Phase 2: Data Gathering
        mock_evaluation.add_state_transition(
            EvaluationState.PEER_FEEDBACK_REQUESTED,
            new_phase=EvaluationPhase.DATA_GATHERING,
            reason="Requesting feedback",
        )
        mock_evaluation.add_state_transition(
            EvaluationState.DATA_GATHERING_COMPLETE,
            reason="All data collected",
        )

        # Phase 3: Manager Evaluation
        mock_evaluation.add_state_transition(
            EvaluationState.MANAGER_EVAL_STARTED,
            new_phase=EvaluationPhase.MANAGER_EVALUATION,
            reason="Manager starting",
        )
        mock_evaluation.add_state_transition(
            EvaluationState.AI_DRAFT_GENERATED,
            reason="AI draft ready",
        )
        mock_evaluation.add_state_transition(
            EvaluationState.MANAGER_EVAL_COMPLETE,
            reason="Manager finalized",
        )

        # Phase 4: Calibration
        mock_evaluation.add_state_transition(
            EvaluationState.CALIBRATION_PENDING,
            new_phase=EvaluationPhase.CALIBRATION,
            reason="Queued for calibration",
        )
        mock_evaluation.add_state_transition(
            EvaluationState.CALIBRATION_COMPLETE,
            reason="Calibrated",
        )

        # Phase 5: Release
        mock_evaluation.add_state_transition(
            EvaluationState.RELEASE_SCHEDULED,
            new_phase=EvaluationPhase.RELEASE_DISCUSSION,
            reason="Scheduled",
        )
        mock_evaluation.add_state_transition(
            EvaluationState.RELEASED,
            reason="Released to employee",
        )
        mock_evaluation.add_state_transition(
            EvaluationState.ACKNOWLEDGED,
            reason="Employee acknowledged",
        )
        mock_evaluation.add_state_transition(
            EvaluationState.COMPLETED,
            new_phase=EvaluationPhase.COMPLETED,
            reason="Evaluation complete",
        )

        # Verify final state
        assert mock_evaluation.current_phase == EvaluationPhase.COMPLETED
        assert mock_evaluation.current_state == EvaluationState.COMPLETED
        assert len(mock_evaluation.state_history) > 10

    def test_evaluation_decline_and_committee_review(self, mock_evaluation):
        """Test employee declining evaluation and committee review"""
        # Fast forward to discussion
        mock_evaluation.current_phase = EvaluationPhase.RELEASE_DISCUSSION
        mock_evaluation.current_state = EvaluationState.DISCUSSION_COMPLETE

        # Employee declines
        mock_evaluation.employee_declined = True
        mock_evaluation.employee_response = "I disagree with the technical rating"
        mock_evaluation.add_state_transition(
            EvaluationState.DECLINED,
            reason="Employee declined evaluation",
        )

        assert mock_evaluation.current_state == EvaluationState.DECLINED
        assert mock_evaluation.employee_declined is True

        # Committee reviews
        mock_evaluation.committee_review_requested = True
        mock_evaluation.committee_decision = "Committee upheld original rating"
        mock_evaluation.add_state_transition(
            EvaluationState.COMPLETED,
            new_phase=EvaluationPhase.COMPLETED,
            reason="Committee resolved",
        )

        assert mock_evaluation.committee_decision is not None

    def test_multiple_peer_feedbacks_tracking(self, mock_evaluation):
        """Test tracking multiple peer feedbacks"""
        peers = [uuid4() for _ in range(7)]
        mock_evaluation.manager_approved_peers = peers

        # Add feedbacks one by one
        for i, peer_id in enumerate(peers[:5]):  # 5 of 7 submit
            feedback = PeerFeedback(
                evaluation_id=mock_evaluation.id,
                peer_id=peer_id,
                peer_name=f"Peer {i+1}",
                raw_input=f"Feedback {i+1}",
            )
            mock_evaluation.peer_feedbacks.append(feedback)

        # Check progress
        assert len(mock_evaluation.peer_feedbacks) == 5
        pending = mock_evaluation.get_pending_feedbacks()
        assert len(pending) == 2

    def test_deadline_progression(self, mock_evaluation):
        """Test deadline tracking through workflow"""
        base_time = datetime.now()

        # Set progressive deadlines
        mock_evaluation.peer_selection_deadline = base_time + timedelta(days=7)
        mock_evaluation.peer_feedback_deadline = base_time + timedelta(days=21)
        mock_evaluation.self_eval_deadline = base_time + timedelta(days=21)
        mock_evaluation.manager_eval_deadline = base_time + timedelta(days=35)
        mock_evaluation.calibration_date = base_time + timedelta(days=42)
        mock_evaluation.release_date = base_time + timedelta(days=49)

        # All should be in the future initially
        assert not mock_evaluation.is_past_deadline("peer_selection")
        assert not mock_evaluation.is_past_deadline("peer_feedback")
        assert not mock_evaluation.is_past_deadline("self_eval")
        assert not mock_evaluation.is_past_deadline("manager_eval")

        # Verify deadline ordering
        assert mock_evaluation.peer_selection_deadline < mock_evaluation.peer_feedback_deadline
        assert mock_evaluation.peer_feedback_deadline < mock_evaluation.manager_eval_deadline
        assert mock_evaluation.manager_eval_deadline < mock_evaluation.calibration_date
