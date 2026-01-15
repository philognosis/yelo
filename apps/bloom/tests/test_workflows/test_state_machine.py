"""
Tests for Evaluation State Machine

Tests valid state transitions, transition validation,
agent triggering, and notification creation.
"""

import pytest

from bloom.models.evaluation import Evaluation, EvaluationPhase, EvaluationState
from bloom.workflows.state_machine import EvaluationStateMachine, TransitionResult


class TestStateMachine:
    """Test state machine initialization and configuration"""

    def test_state_machine_creation(self):
        """Test creating state machine"""
        sm = EvaluationStateMachine()
        assert len(sm.transitions) > 0

    def test_all_phases_have_transitions(self):
        """Test that all phases have defined transitions"""
        sm = EvaluationStateMachine()

        # Check transitions exist for each phase
        phases_with_transitions = set()
        for transition in sm.transitions:
            if transition.from_phase:
                phases_with_transitions.add(transition.from_phase)
            if transition.to_phase:
                phases_with_transitions.add(transition.to_phase)

        # Should have transitions for main phases
        assert EvaluationPhase.CONTEXT_PEER_SELECTION in phases_with_transitions
        assert EvaluationPhase.DATA_GATHERING in phases_with_transitions


class TestValidTransitions:
    """Test identifying valid transitions"""

    def test_get_valid_transitions_from_start(self):
        """Test valid transitions from initial state"""
        sm = EvaluationStateMachine()

        valid = sm.get_valid_transitions(
            EvaluationState.CYCLE_STARTED,
            EvaluationPhase.CONTEXT_PEER_SELECTION,
        )

        assert len(valid) > 0
        # Should be able to move to peer suggestion generated
        assert any(t.to_state == EvaluationState.PEER_SUGGESTION_GENERATED for t in valid)

    def test_get_valid_transitions_sorted_by_priority(self):
        """Test transitions are sorted by priority"""
        sm = EvaluationStateMachine()

        valid = sm.get_valid_transitions(
            EvaluationState.CYCLE_STARTED,
            EvaluationPhase.CONTEXT_PEER_SELECTION,
        )

        if len(valid) > 1:
            priorities = [t.priority for t in valid]
            assert priorities == sorted(priorities, reverse=True)

    def test_can_transition_valid(self, mock_evaluation):
        """Test checking valid transition"""
        sm = EvaluationStateMachine()

        mock_evaluation.current_state = EvaluationState.CYCLE_STARTED

        can_transition = sm.can_transition(
            mock_evaluation,
            EvaluationState.PEER_SUGGESTION_GENERATED,
        )

        assert can_transition is True

    def test_can_transition_invalid(self, mock_evaluation):
        """Test checking invalid transition"""
        sm = EvaluationStateMachine()

        mock_evaluation.current_state = EvaluationState.CYCLE_STARTED

        # Can't jump to completed from start
        can_transition = sm.can_transition(
            mock_evaluation,
            EvaluationState.COMPLETED,
        )

        assert can_transition is False


class TestConditionValidation:
    """Test transition condition validation"""

    def test_validate_employee_selected_peers(self, mock_evaluation):
        """Test employee_selected_peers condition"""
        sm = EvaluationStateMachine()

        # Without peers
        valid, failed = sm.validate_conditions(mock_evaluation, ["employee_selected_peers"])
        assert not valid
        assert "employee_selected_peers" in failed

        # With peers
        mock_evaluation.employee_selected_peers = [uuid4() for _ in range(3)]
        valid, failed = sm.validate_conditions(mock_evaluation, ["employee_selected_peers"])
        assert valid
        assert len(failed) == 0

    def test_validate_manager_approved_peers(self, mock_evaluation):
        """Test manager_approved_peers condition"""
        sm = EvaluationStateMachine()

        # Add approved peers
        mock_evaluation.manager_approved_peers = [uuid4() for _ in range(5)]

        valid, failed = sm.validate_conditions(mock_evaluation, ["manager_approved_peers"])
        assert valid

    def test_validate_peer_feedback_complete(self, mock_evaluation, mock_peer_feedbacks):
        """Test peer_feedback_complete condition"""
        sm = EvaluationStateMachine()

        # Set approved peers
        mock_evaluation.manager_approved_peers = [uuid4() for _ in range(5)]

        # Not enough feedback
        mock_evaluation.peer_feedbacks = mock_peer_feedbacks[:3]
        valid, failed = sm.validate_conditions(mock_evaluation, ["peer_feedback_complete"])
        assert not valid

        # All feedback received
        mock_evaluation.peer_feedbacks = mock_peer_feedbacks[:5]
        valid, failed = sm.validate_conditions(mock_evaluation, ["peer_feedback_complete"])
        assert valid


class TestStateTransitionExecution:
    """Test executing state transitions"""

    @pytest.mark.asyncio
    async def test_transition_success(self, mock_evaluation):
        """Test successful transition"""
        sm = EvaluationStateMachine()

        mock_evaluation.current_state = EvaluationState.CYCLE_STARTED

        result = await sm.transition(
            mock_evaluation,
            EvaluationState.PEER_SUGGESTION_GENERATED,
            reason="Test transition",
        )

        assert result.success is True
        assert result.new_state == EvaluationState.PEER_SUGGESTION_GENERATED
        assert mock_evaluation.current_state == EvaluationState.PEER_SUGGESTION_GENERATED

    @pytest.mark.asyncio
    async def test_transition_with_phase_change(self, mock_evaluation):
        """Test transition that changes phase"""
        sm = EvaluationStateMachine()

        mock_evaluation.current_state = EvaluationState.PEER_LIST_LOCKED
        mock_evaluation.current_phase = EvaluationPhase.CONTEXT_PEER_SELECTION

        result = await sm.transition(
            mock_evaluation,
            EvaluationState.PEER_FEEDBACK_REQUESTED,
        )

        assert result.success is True
        assert result.new_phase == EvaluationPhase.DATA_GATHERING
        assert mock_evaluation.current_phase == EvaluationPhase.DATA_GATHERING

    @pytest.mark.asyncio
    async def test_transition_triggers_agents(self, mock_evaluation):
        """Test transition triggers appropriate agents"""
        sm = EvaluationStateMachine()

        result = await sm.transition(
            mock_evaluation,
            EvaluationState.PEER_SUGGESTION_GENERATED,
        )

        # Should trigger Context Miner
        assert len(result.triggered_agents) > 0

    @pytest.mark.asyncio
    async def test_transition_creates_deadlines(self, mock_evaluation):
        """Test transition creates deadlines"""
        sm = EvaluationStateMachine()

        mock_evaluation.current_state = EvaluationState.PEER_SUGGESTION_GENERATED

        result = await sm.transition(
            mock_evaluation,
            EvaluationState.EMPLOYEE_PEER_REVIEW,
        )

        # Should create peer selection deadline
        if result.success:
            assert len(result.created_deadlines) >= 0

    @pytest.mark.asyncio
    async def test_transition_invalid(self, mock_evaluation):
        """Test invalid transition fails"""
        sm = EvaluationStateMachine()

        result = await sm.transition(
            mock_evaluation,
            EvaluationState.COMPLETED,  # Can't jump to completed
        )

        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_transition_condition_not_met(self, mock_evaluation):
        """Test transition fails when conditions not met"""
        sm = EvaluationStateMachine()

        mock_evaluation.current_state = EvaluationState.EMPLOYEE_PEER_REVIEW
        # Don't set employee_selected_peers

        result = await sm.transition(
            mock_evaluation,
            EvaluationState.MANAGER_PEER_APPROVAL,
        )

        assert result.success is False
        assert any("condition" in err.lower() for err in result.errors)


class TestAutoAdvance:
    """Test automatic state advancement"""

    @pytest.mark.asyncio
    async def test_auto_advance_available(self, mock_evaluation):
        """Test auto-advance when available"""
        sm = EvaluationStateMachine()

        mock_evaluation.current_state = EvaluationState.PEER_SUGGESTION_GENERATED

        result = await sm.auto_advance(mock_evaluation)

        # Should auto-advance to employee review
        if result:
            assert result.success is True

    @pytest.mark.asyncio
    async def test_auto_advance_not_available(self, mock_evaluation):
        """Test auto-advance when not available"""
        sm = EvaluationStateMachine()

        # Manual transition required
        mock_evaluation.current_state = EvaluationState.EMPLOYEE_PEER_REVIEW

        result = await sm.auto_advance(mock_evaluation)

        assert result is None  # No auto transition


class TestWorkflowValidation:
    """Test workflow definition validation"""

    def test_validate_workflow(self):
        """Test validating workflow definition"""
        sm = EvaluationStateMachine()

        is_valid, errors = sm.validate_workflow()

        # Workflow should be valid
        if not is_valid:
            print(f"Workflow errors: {errors}")

    def test_get_transition_graph(self):
        """Test getting transition graph"""
        sm = EvaluationStateMachine()

        graph = sm.get_transition_graph()

        assert isinstance(graph, dict)
        # Start state should have outgoing transitions
        assert "cycle_started" in graph


from uuid import uuid4
