"""
Evaluation State Machine

Implements the core state machine for evaluation workflows:
- Defines valid state transitions
- Validates state changes
- Triggers appropriate agents on transitions
- Manages phase progression
- Integrates with IRAS protocols

The state machine orchestrates the entire evaluation lifecycle through
5 main phases with multiple states per phase.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field

from bloom.models.evaluation import Evaluation, EvaluationPhase, EvaluationState
from bloom.models.workflow import (
    DeadlineType,
    EventType,
    NotificationChannel,
    StateTransition,
    TransitionTrigger,
    WorkflowEvent,
)


class TransitionResult(BaseModel):
    """Result of a state transition attempt"""

    success: bool
    new_state: Optional[EvaluationState] = None
    new_phase: Optional[EvaluationPhase] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    triggered_agents: List[str] = Field(default_factory=list)
    sent_notifications: List[str] = Field(default_factory=list)
    created_deadlines: List[DeadlineType] = Field(default_factory=list)
    event: Optional[WorkflowEvent] = None


class EvaluationStateMachine:
    """
    Evaluation Workflow State Machine

    Manages the evaluation workflow through defined states and transitions.
    Ensures valid state progression and triggers appropriate actions.

    Phase Flow:
    1. Context & Peer Selection
       - cycle_started -> peer_suggestion_generated -> employee_peer_review
       -> manager_peer_approval -> peer_list_locked

    2. Data Gathering
       - peer_feedback_requested -> peer_feedback_in_progress
       -> self_eval_requested -> self_eval_in_progress
       -> data_gathering_complete

    3. Manager Evaluation
       - manager_eval_started -> ai_draft_generated
       -> manager_review_in_progress -> manager_eval_complete

    4. Calibration
       - calibration_pending -> calibration_in_progress
       -> calibration_complete

    5. Release & Discussion
       - release_scheduled -> released -> discussion_scheduled
       -> discussion_complete -> acknowledged/declined
    """

    def __init__(self):
        """Initialize state machine with transition definitions"""

        self.transitions: List[StateTransition] = []
        self.transition_validators: Dict[str, Callable] = {}
        self.transition_callbacks: Dict[str, List[Callable]] = {}

        # Define valid transitions
        self._define_transitions()

        logger.info("Evaluation state machine initialized")

    def _define_transitions(self) -> None:
        """Define all valid state transitions"""

        # Phase 1: Context & Peer Selection
        self.transitions.extend([
            StateTransition(
                from_state=EvaluationState.CYCLE_STARTED,
                to_state=EvaluationState.PEER_SUGGESTION_GENERATED,
                from_phase=EvaluationPhase.CONTEXT_PEER_SELECTION,
                to_phase=EvaluationPhase.CONTEXT_PEER_SELECTION,
                trigger=TransitionTrigger.AGENT,
                description="Context Miner generates peer suggestions",
                trigger_agents=["Context Miner"],
                send_notifications=[],
            ),
            StateTransition(
                from_state=EvaluationState.PEER_SUGGESTION_GENERATED,
                to_state=EvaluationState.EMPLOYEE_PEER_REVIEW,
                trigger=TransitionTrigger.AUTOMATIC,
                description="Employee reviews suggested peers",
                send_notifications=["peer_review_request"],
                set_deadlines=["peer_selection"],
            ),
            StateTransition(
                from_state=EvaluationState.EMPLOYEE_PEER_REVIEW,
                to_state=EvaluationState.MANAGER_PEER_APPROVAL,
                trigger=TransitionTrigger.MANUAL,
                description="Employee submits peer selection",
                required_conditions=["employee_selected_peers"],
                send_notifications=["manager_peer_approval_request"],
            ),
            StateTransition(
                from_state=EvaluationState.MANAGER_PEER_APPROVAL,
                to_state=EvaluationState.PEER_LIST_LOCKED,
                trigger=TransitionTrigger.MANUAL,
                description="Manager approves peer list",
                required_conditions=["manager_approved_peers"],
            ),
        ])

        # Phase 2: Data Gathering
        self.transitions.extend([
            StateTransition(
                from_state=EvaluationState.PEER_LIST_LOCKED,
                to_state=EvaluationState.PEER_FEEDBACK_REQUESTED,
                from_phase=EvaluationPhase.CONTEXT_PEER_SELECTION,
                to_phase=EvaluationPhase.DATA_GATHERING,
                trigger=TransitionTrigger.AUTOMATIC,
                description="Request feedback from approved peers",
                trigger_agents=["Peer Collector"],
                send_notifications=["peer_feedback_request"],
                set_deadlines=["peer_feedback"],
            ),
            StateTransition(
                from_state=EvaluationState.PEER_FEEDBACK_REQUESTED,
                to_state=EvaluationState.PEER_FEEDBACK_IN_PROGRESS,
                trigger=TransitionTrigger.AUTOMATIC,
                description="Peers are providing feedback",
            ),
            StateTransition(
                from_state=EvaluationState.PEER_FEEDBACK_IN_PROGRESS,
                to_state=EvaluationState.SELF_EVAL_REQUESTED,
                trigger=TransitionTrigger.AUTOMATIC,
                description="Request self-evaluation from employee",
                send_notifications=["self_eval_request"],
                set_deadlines=["self_evaluation"],
            ),
            StateTransition(
                from_state=EvaluationState.SELF_EVAL_REQUESTED,
                to_state=EvaluationState.SELF_EVAL_IN_PROGRESS,
                trigger=TransitionTrigger.MANUAL,
                description="Employee is completing self-evaluation",
            ),
            StateTransition(
                from_state=EvaluationState.SELF_EVAL_IN_PROGRESS,
                to_state=EvaluationState.DATA_GATHERING_COMPLETE,
                trigger=TransitionTrigger.MANUAL,
                description="All data collection complete",
                required_conditions=["self_eval_submitted", "peer_feedback_complete"],
            ),
        ])

        # Phase 3: Manager Evaluation
        self.transitions.extend([
            StateTransition(
                from_state=EvaluationState.DATA_GATHERING_COMPLETE,
                to_state=EvaluationState.MANAGER_EVAL_STARTED,
                from_phase=EvaluationPhase.DATA_GATHERING,
                to_phase=EvaluationPhase.MANAGER_EVALUATION,
                trigger=TransitionTrigger.AUTOMATIC,
                description="Manager begins evaluation",
                trigger_agents=["Draft Writer"],
                send_notifications=["manager_eval_started"],
                set_deadlines=["manager_evaluation"],
            ),
            StateTransition(
                from_state=EvaluationState.MANAGER_EVAL_STARTED,
                to_state=EvaluationState.AI_DRAFT_GENERATED,
                trigger=TransitionTrigger.AGENT,
                description="AI generates draft evaluation",
                trigger_agents=["Draft Writer"],
            ),
            StateTransition(
                from_state=EvaluationState.AI_DRAFT_GENERATED,
                to_state=EvaluationState.MANAGER_REVIEW_IN_PROGRESS,
                trigger=TransitionTrigger.AUTOMATIC,
                description="Manager reviews and refines draft",
                send_notifications=["manager_review_request"],
            ),
            StateTransition(
                from_state=EvaluationState.MANAGER_REVIEW_IN_PROGRESS,
                to_state=EvaluationState.MANAGER_EVAL_COMPLETE,
                trigger=TransitionTrigger.MANUAL,
                description="Manager finalizes evaluation",
                required_conditions=["manager_eval_finalized"],
            ),
        ])

        # Phase 4: Calibration
        self.transitions.extend([
            StateTransition(
                from_state=EvaluationState.MANAGER_EVAL_COMPLETE,
                to_state=EvaluationState.CALIBRATION_PENDING,
                from_phase=EvaluationPhase.MANAGER_EVALUATION,
                to_phase=EvaluationPhase.CALIBRATION,
                trigger=TransitionTrigger.AUTOMATIC,
                description="Evaluation queued for calibration",
                send_notifications=["calibration_pending"],
                set_deadlines=["calibration"],
            ),
            StateTransition(
                from_state=EvaluationState.CALIBRATION_PENDING,
                to_state=EvaluationState.CALIBRATION_IN_PROGRESS,
                trigger=TransitionTrigger.MANUAL,
                description="Calibration session in progress",
            ),
            StateTransition(
                from_state=EvaluationState.CALIBRATION_IN_PROGRESS,
                to_state=EvaluationState.CALIBRATION_COMPLETE,
                trigger=TransitionTrigger.MANUAL,
                description="Calibration complete, ratings finalized",
                required_conditions=["calibration_completed"],
            ),
        ])

        # Phase 5: Release & Discussion
        self.transitions.extend([
            StateTransition(
                from_state=EvaluationState.CALIBRATION_COMPLETE,
                to_state=EvaluationState.RELEASE_SCHEDULED,
                from_phase=EvaluationPhase.CALIBRATION,
                to_phase=EvaluationPhase.RELEASE_DISCUSSION,
                trigger=TransitionTrigger.AUTOMATIC,
                description="Schedule evaluation release",
                set_deadlines=["release"],
            ),
            StateTransition(
                from_state=EvaluationState.RELEASE_SCHEDULED,
                to_state=EvaluationState.RELEASED,
                trigger=TransitionTrigger.DEADLINE,
                description="Evaluation released to employee",
                send_notifications=["eval_released"],
                trigger_agents=["Release Manager"],
            ),
            StateTransition(
                from_state=EvaluationState.RELEASED,
                to_state=EvaluationState.DISCUSSION_SCHEDULED,
                trigger=TransitionTrigger.AUTOMATIC,
                description="Schedule discussion meeting",
                send_notifications=["discussion_scheduled"],
                set_deadlines=["discussion"],
            ),
            StateTransition(
                from_state=EvaluationState.DISCUSSION_SCHEDULED,
                to_state=EvaluationState.DISCUSSION_COMPLETE,
                trigger=TransitionTrigger.MANUAL,
                description="Discussion meeting completed",
                required_conditions=["discussion_completed"],
            ),
            StateTransition(
                from_state=EvaluationState.DISCUSSION_COMPLETE,
                to_state=EvaluationState.ACKNOWLEDGED,
                trigger=TransitionTrigger.MANUAL,
                description="Employee acknowledges evaluation",
                required_conditions=["employee_acknowledged"],
            ),
            StateTransition(
                from_state=EvaluationState.DISCUSSION_COMPLETE,
                to_state=EvaluationState.DECLINED,
                trigger=TransitionTrigger.MANUAL,
                description="Employee declines evaluation",
                required_conditions=["employee_declined"],
            ),
            StateTransition(
                from_state=EvaluationState.ACKNOWLEDGED,
                to_state=EvaluationState.COMPLETED,
                from_phase=EvaluationPhase.RELEASE_DISCUSSION,
                to_phase=EvaluationPhase.COMPLETED,
                trigger=TransitionTrigger.AUTOMATIC,
                description="Evaluation process completed",
            ),
            StateTransition(
                from_state=EvaluationState.DECLINED,
                to_state=EvaluationState.COMPLETED,
                from_phase=EvaluationPhase.RELEASE_DISCUSSION,
                to_phase=EvaluationPhase.COMPLETED,
                trigger=TransitionTrigger.MANUAL,
                description="Declined evaluation resolved",
                required_conditions=["committee_decision"],
            ),
        ])

        logger.info(f"Defined {len(self.transitions)} state transitions")

    def get_valid_transitions(
        self,
        current_state: EvaluationState,
        current_phase: EvaluationPhase,
    ) -> List[StateTransition]:
        """
        Get valid transitions from current state/phase

        Args:
            current_state: Current evaluation state
            current_phase: Current evaluation phase

        Returns:
            List of valid transitions
        """
        valid = [
            t for t in self.transitions
            if t.is_valid_transition(current_state, current_phase)
        ]

        # Sort by priority (higher first)
        valid.sort(key=lambda t: t.priority, reverse=True)

        return valid

    def can_transition(
        self,
        evaluation: Evaluation,
        to_state: EvaluationState,
    ) -> bool:
        """
        Check if transition to target state is valid

        Args:
            evaluation: Current evaluation
            to_state: Target state

        Returns:
            True if transition is valid
        """
        # Find matching transition
        for transition in self.transitions:
            if (
                transition.from_state == evaluation.current_state
                and transition.to_state == to_state
                and transition.is_valid_transition(
                    evaluation.current_state,
                    evaluation.current_phase,
                )
            ):
                return True

        return False

    def validate_conditions(
        self,
        evaluation: Evaluation,
        conditions: List[str],
    ) -> tuple[bool, List[str]]:
        """
        Validate transition conditions

        Args:
            evaluation: Evaluation to check
            conditions: List of condition names

        Returns:
            Tuple of (all_valid, failed_conditions)
        """
        failed: List[str] = []

        for condition in conditions:
            if not self._check_condition(evaluation, condition):
                failed.append(condition)

        return len(failed) == 0, failed

    def _check_condition(self, evaluation: Evaluation, condition: str) -> bool:
        """
        Check if a specific condition is met

        Args:
            evaluation: Evaluation to check
            condition: Condition name

        Returns:
            True if condition is met
        """
        # Implement condition checks
        if condition == "employee_selected_peers":
            return len(evaluation.employee_selected_peers) > 0

        elif condition == "manager_approved_peers":
            return len(evaluation.manager_approved_peers) > 0

        elif condition == "self_eval_submitted":
            return evaluation.self_evaluation is not None

        elif condition == "peer_feedback_complete":
            expected_count = len(evaluation.manager_approved_peers)
            received_count = len(evaluation.peer_feedbacks)
            return received_count >= expected_count

        elif condition == "manager_eval_finalized":
            return (
                evaluation.manager_evaluation is not None
                and evaluation.manager_evaluation.final_summary != ""
            )

        elif condition == "calibration_completed":
            return (
                evaluation.manager_evaluation is not None
                and evaluation.manager_evaluation.calibrated_at is not None
            )

        elif condition == "discussion_completed":
            return evaluation.discussion_completed_at is not None

        elif condition == "employee_acknowledged":
            return evaluation.employee_acknowledged

        elif condition == "employee_declined":
            return evaluation.employee_declined

        elif condition == "committee_decision":
            return evaluation.committee_decision is not None

        # Unknown condition - log warning
        logger.warning(f"Unknown condition: {condition}")
        return False

    async def transition(
        self,
        evaluation: Evaluation,
        to_state: EvaluationState,
        actor_id: Optional[UUID] = None,
        actor_type: str = "system",
        reason: Optional[str] = None,
        skip_validation: bool = False,
    ) -> TransitionResult:
        """
        Execute state transition

        Args:
            evaluation: Evaluation to transition
            to_state: Target state
            actor_id: ID of user/agent triggering transition
            actor_type: Type of actor (user, agent, system)
            reason: Reason for transition
            skip_validation: Skip condition validation (use carefully)

        Returns:
            Transition result
        """
        logger.info(
            f"Transitioning evaluation {evaluation.id} "
            f"from {evaluation.current_state.value} to {to_state.value}"
        )

        result = TransitionResult(success=False)

        # Find transition definition
        transition = None
        for t in self.transitions:
            if (
                t.from_state == evaluation.current_state
                and t.to_state == to_state
                and t.is_valid_transition(
                    evaluation.current_state,
                    evaluation.current_phase,
                )
            ):
                transition = t
                break

        if not transition:
            error = f"Invalid transition: {evaluation.current_state.value} -> {to_state.value}"
            logger.error(error)
            result.errors.append(error)
            return result

        # Validate conditions
        if not skip_validation and transition.required_conditions:
            conditions_met, failed = self.validate_conditions(
                evaluation,
                transition.required_conditions,
            )

            if not conditions_met:
                error = f"Transition conditions not met: {failed}"
                logger.warning(error)
                result.errors.append(error)
                return result

        # Execute transition
        try:
            # Update state
            old_state = evaluation.current_state
            old_phase = evaluation.current_phase

            evaluation.current_state = to_state
            if transition.to_phase:
                evaluation.current_phase = transition.to_phase

            # Record in history
            evaluation.add_state_transition(
                new_state=to_state,
                new_phase=transition.to_phase,
                reason=reason or transition.description,
            )

            # Create event
            event = WorkflowEvent(
                evaluation_id=evaluation.id,
                event_type=EventType.STATE_CHANGED,
                actor_id=actor_id,
                actor_type=actor_type,
                description=transition.description,
                previous_state=old_state,
                new_state=to_state,
                previous_phase=old_phase,
                new_phase=evaluation.current_phase,
            )

            # Execute transition actions
            result.triggered_agents = transition.trigger_agents.copy()
            result.sent_notifications = transition.send_notifications.copy()
            result.created_deadlines = [
                DeadlineType(dl) for dl in transition.set_deadlines
            ]

            # Update result
            result.success = True
            result.new_state = to_state
            result.new_phase = evaluation.current_phase
            result.event = event

            logger.info(
                f"Transition successful: {old_state.value} -> {to_state.value}"
            )

            # Execute callbacks
            await self._execute_callbacks(transition, evaluation, result)

            return result

        except Exception as e:
            error = f"Transition failed: {e}"
            logger.error(error)
            result.errors.append(error)
            result.success = False
            return result

    async def auto_advance(
        self,
        evaluation: Evaluation,
        actor_id: Optional[UUID] = None,
    ) -> Optional[TransitionResult]:
        """
        Automatically advance to next state if possible

        Args:
            evaluation: Evaluation to advance
            actor_id: Actor triggering advancement

        Returns:
            Transition result or None if no auto transition available
        """
        # Get valid automatic transitions
        valid = self.get_valid_transitions(
            evaluation.current_state,
            evaluation.current_phase,
        )

        auto_transitions = [
            t for t in valid
            if t.trigger in [TransitionTrigger.AUTOMATIC, TransitionTrigger.AGENT]
        ]

        if not auto_transitions:
            return None

        # Try first automatic transition
        transition = auto_transitions[0]

        # Check conditions
        if transition.required_conditions:
            conditions_met, _ = self.validate_conditions(
                evaluation,
                transition.required_conditions,
            )
            if not conditions_met:
                return None

        # Execute transition
        return await self.transition(
            evaluation,
            transition.to_state,
            actor_id=actor_id,
            actor_type="system",
            reason="Automatic advancement",
        )

    def register_transition_callback(
        self,
        from_state: EvaluationState,
        to_state: EvaluationState,
        callback: Callable,
    ) -> None:
        """
        Register callback to execute on transition

        Args:
            from_state: Source state
            to_state: Destination state
            callback: Async callback function
        """
        key = f"{from_state.value}:{to_state.value}"
        if key not in self.transition_callbacks:
            self.transition_callbacks[key] = []
        self.transition_callbacks[key].append(callback)

        logger.debug(f"Registered callback for transition {key}")

    async def _execute_callbacks(
        self,
        transition: StateTransition,
        evaluation: Evaluation,
        result: TransitionResult,
    ) -> None:
        """
        Execute registered callbacks for transition

        Args:
            transition: Transition that occurred
            evaluation: Evaluation being transitioned
            result: Transition result
        """
        key = f"{transition.from_state.value}:{transition.to_state.value}"

        callbacks = self.transition_callbacks.get(key, [])
        if not callbacks:
            return

        logger.debug(f"Executing {len(callbacks)} callbacks for transition {key}")

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(evaluation, result)
                else:
                    callback(evaluation, result)
            except Exception as e:
                logger.error(f"Callback execution failed: {e}")
                result.warnings.append(f"Callback error: {e}")

    def get_transition_graph(self) -> Dict[str, List[str]]:
        """
        Get state transition graph

        Returns:
            Dictionary mapping states to reachable states
        """
        graph: Dict[str, List[str]] = {}

        for transition in self.transitions:
            from_key = transition.from_state.value
            to_key = transition.to_state.value

            if from_key not in graph:
                graph[from_key] = []

            graph[from_key].append(to_key)

        return graph

    def validate_workflow(self) -> tuple[bool, List[str]]:
        """
        Validate workflow definition

        Returns:
            Tuple of (is_valid, errors)
        """
        errors: List[str] = []

        # Check for unreachable states
        graph = self.get_transition_graph()
        reachable = set()
        to_visit = [EvaluationState.CYCLE_STARTED.value]

        while to_visit:
            state = to_visit.pop()
            if state in reachable:
                continue

            reachable.add(state)
            to_visit.extend(graph.get(state, []))

        all_states = {s.value for s in EvaluationState}
        unreachable = all_states - reachable

        if unreachable:
            errors.append(f"Unreachable states: {unreachable}")

        # Check for dead ends (except terminal states)
        terminal_states = {
            EvaluationState.COMPLETED.value,
            EvaluationState.CANCELLED.value,
        }

        for state in all_states:
            if state not in terminal_states and state not in graph:
                errors.append(f"Dead end state (no outgoing transitions): {state}")

        is_valid = len(errors) == 0
        return is_valid, errors
