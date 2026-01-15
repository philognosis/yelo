"""
Phase Handlers

Implements handlers for each evaluation phase:
- Phase 1: Context & Peer Selection
- Phase 2: Data Gathering
- Phase 3: Manager Evaluation
- Phase 4: Calibration
- Phase 5: Release & Discussion

Each handler manages:
- Phase-specific logic and validations
- Agent coordination
- Notification sending
- Deadline management
- State transitions within the phase
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field

from bloom.models.employee import Employee
from bloom.models.evaluation import Evaluation, EvaluationPhase, EvaluationState
from bloom.models.workflow import Deadline, DeadlineType, Notification, NotificationChannel


class PhaseContext(BaseModel):
    """Context for phase execution"""

    evaluation: Evaluation
    employee: Employee
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PhaseResult(BaseModel):
    """Result of phase execution"""

    success: bool
    phase: EvaluationPhase
    messages: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    next_state: Optional[EvaluationState] = None
    notifications_sent: int = 0
    deadlines_created: int = 0
    agents_triggered: List[str] = Field(default_factory=list)


class PhaseHandler(ABC):
    """
    Base class for phase handlers

    Each phase has a handler that manages the phase-specific logic,
    coordinates agents, and ensures proper workflow progression.
    """

    def __init__(self):
        """Initialize phase handler"""
        self.phase: EvaluationPhase = EvaluationPhase.CONTEXT_PEER_SELECTION

    @abstractmethod
    async def enter_phase(self, context: PhaseContext) -> PhaseResult:
        """
        Execute when entering the phase

        Args:
            context: Phase execution context

        Returns:
            Phase execution result
        """
        pass

    @abstractmethod
    async def exit_phase(self, context: PhaseContext) -> PhaseResult:
        """
        Execute when exiting the phase

        Args:
            context: Phase execution context

        Returns:
            Phase execution result
        """
        pass

    @abstractmethod
    async def validate_phase_complete(self, context: PhaseContext) -> tuple[bool, List[str]]:
        """
        Validate if phase is complete

        Args:
            context: Phase execution context

        Returns:
            Tuple of (is_complete, blocking_issues)
        """
        pass

    async def send_notification(
        self,
        recipient_id: UUID,
        template_name: str,
        channel: NotificationChannel,
        **template_data,
    ) -> Notification:
        """
        Send notification

        Args:
            recipient_id: Recipient user ID
            template_name: Notification template
            channel: Delivery channel
            **template_data: Template data

        Returns:
            Notification record
        """
        # In production, this would use the actual notification service
        notification = Notification.create_from_template(
            template_name=template_name,
            recipient_id=recipient_id,
            channel=channel,
            template_data=template_data,
        )

        logger.info(f"Sending notification: {template_name} to {recipient_id} via {channel.value}")
        return notification

    async def create_deadline(
        self,
        evaluation_id: UUID,
        deadline_type: DeadlineType,
        due_date: datetime,
        responsible_user_id: Optional[UUID] = None,
        description: str = "",
    ) -> Deadline:
        """
        Create deadline

        Args:
            evaluation_id: Evaluation ID
            deadline_type: Type of deadline
            due_date: When deadline is due
            responsible_user_id: User responsible
            description: Human-readable description

        Returns:
            Deadline record
        """
        deadline = Deadline.create_with_warning(
            evaluation_id=evaluation_id,
            deadline_type=deadline_type,
            due_date=due_date,
            warning_days=2,
            description=description,
            responsible_user_id=responsible_user_id,
            reminder_schedule=[7, 3, 1],
        )

        logger.info(f"Created deadline: {deadline_type.value} due {due_date}")
        return deadline


class ContextPeerSelectionHandler(PhaseHandler):
    """
    Phase 1: Context & Peer Selection Handler

    Manages:
    - Context mining (skills, calendar metrics, collaboration data)
    - AI peer suggestions based on relationship strength
    - Employee peer review and selection
    - Manager peer approval
    - Peer list finalization
    """

    def __init__(self):
        super().__init__()
        self.phase = EvaluationPhase.CONTEXT_PEER_SELECTION

    async def enter_phase(self, context: PhaseContext) -> PhaseResult:
        """
        Enter context & peer selection phase

        Triggers Context Miner agent to generate peer suggestions
        """
        logger.info(f"Entering Phase 1: Context & Peer Selection for evaluation {context.evaluation.id}")

        result = PhaseResult(
            success=True,
            phase=self.phase,
        )

        evaluation = context.evaluation
        employee = context.employee

        try:
            # Trigger Context Miner agent
            result.messages.append("Triggering Context Miner to analyze employee context")
            result.agents_triggered.append("Context Miner")

            # The Context Miner will:
            # 1. Analyze calendar metrics for peer relationships
            # 2. Review Jira for cross-functional collaboration
            # 3. Check Git for code review patterns
            # 4. Generate peer suggestions based on relationship strength

            # Set state to peer suggestion in progress
            result.next_state = EvaluationState.PEER_SUGGESTION_GENERATED
            result.messages.append("Peer suggestion generation in progress")

            logger.info("Phase 1 entry complete, Context Miner triggered")
            return result

        except Exception as e:
            logger.error(f"Phase 1 entry failed: {e}")
            result.success = False
            result.errors.append(str(e))
            return result

    async def handle_peer_suggestions_generated(
        self,
        context: PhaseContext,
        suggested_peers: List[UUID],
    ) -> PhaseResult:
        """
        Handle AI-generated peer suggestions

        Args:
            context: Phase context
            suggested_peers: List of suggested peer IDs

        Returns:
            Phase result
        """
        logger.info(f"Processing {len(suggested_peers)} peer suggestions")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        # Store suggestions
        evaluation.suggested_peers = suggested_peers

        # Send notification to employee to review peers
        await self.send_notification(
            recipient_id=evaluation.employee_id,
            template_name="peer_review_request",
            channel=NotificationChannel.SLACK_DM,
            employee_name=context.employee.person.name,
            suggested_count=len(suggested_peers),
        )

        result.notifications_sent += 1

        # Create deadline for peer selection
        deadline = await self.create_deadline(
            evaluation_id=evaluation.id,
            deadline_type=DeadlineType.PEER_SELECTION,
            due_date=datetime.now() + timedelta(days=7),
            responsible_user_id=evaluation.employee_id,
            description="Employee peer selection deadline",
        )

        result.deadlines_created += 1

        # Transition to employee review state
        result.next_state = EvaluationState.EMPLOYEE_PEER_REVIEW

        return result

    async def handle_employee_peer_selection(
        self,
        context: PhaseContext,
        selected_peers: List[UUID],
    ) -> PhaseResult:
        """
        Handle employee's peer selection

        Args:
            context: Phase context
            selected_peers: Peers selected by employee

        Returns:
            Phase result
        """
        logger.info(f"Employee selected {len(selected_peers)} peers")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        # Validate selection count (typically 3-7 peers)
        if len(selected_peers) < 3:
            result.errors.append("Must select at least 3 peers")
            result.success = False
            return result

        if len(selected_peers) > 10:
            result.errors.append("Cannot select more than 10 peers")
            result.success = False
            return result

        # Store employee selection
        evaluation.employee_selected_peers = selected_peers

        # Send to manager for approval
        await self.send_notification(
            recipient_id=evaluation.manager_id,
            template_name="manager_peer_approval_request",
            channel=NotificationChannel.SLACK_DM,
            employee_name=context.employee.person.name,
            peer_count=len(selected_peers),
        )

        result.notifications_sent += 1
        result.next_state = EvaluationState.MANAGER_PEER_APPROVAL

        return result

    async def handle_manager_peer_approval(
        self,
        context: PhaseContext,
        approved_peers: List[UUID],
    ) -> PhaseResult:
        """
        Handle manager's peer approval

        Args:
            context: Phase context
            approved_peers: Final approved peer list

        Returns:
            Phase result
        """
        logger.info(f"Manager approved {len(approved_peers)} peers")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        # Store approved peers
        evaluation.manager_approved_peers = approved_peers

        # Lock peer list
        result.next_state = EvaluationState.PEER_LIST_LOCKED
        result.messages.append("Peer list locked, ready for data gathering")

        return result

    async def exit_phase(self, context: PhaseContext) -> PhaseResult:
        """Exit Phase 1, transition to data gathering"""
        logger.info("Exiting Phase 1: Context & Peer Selection")

        result = PhaseResult(success=True, phase=self.phase)

        # Validate completion
        is_complete, issues = await self.validate_phase_complete(context)

        if not is_complete:
            result.success = False
            result.errors.extend(issues)
            return result

        result.messages.append("Phase 1 complete, transitioning to data gathering")
        return result

    async def validate_phase_complete(self, context: PhaseContext) -> tuple[bool, List[str]]:
        """Validate Phase 1 is complete"""
        issues: List[str] = []

        evaluation = context.evaluation

        if not evaluation.manager_approved_peers:
            issues.append("No peers have been approved")

        if len(evaluation.manager_approved_peers) < 3:
            issues.append("At least 3 peers must be approved")

        return len(issues) == 0, issues


class DataGatheringHandler(PhaseHandler):
    """
    Phase 2: Data Gathering Handler

    Manages:
    - Peer feedback collection (voice notes or text)
    - Feedback synthesis using AI
    - Self-evaluation collection
    - Achievement documentation gathering
    - Jira/Git metrics collection
    """

    def __init__(self):
        super().__init__()
        self.phase = EvaluationPhase.DATA_GATHERING

    async def enter_phase(self, context: PhaseContext) -> PhaseResult:
        """
        Enter data gathering phase

        Triggers peer feedback requests
        """
        logger.info(f"Entering Phase 2: Data Gathering for evaluation {context.evaluation.id}")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        try:
            # Trigger Peer Collector agent
            result.agents_triggered.append("Peer Collector")

            # Send feedback requests to all approved peers
            for peer_id in evaluation.manager_approved_peers:
                await self.send_notification(
                    recipient_id=peer_id,
                    template_name="peer_feedback_request",
                    channel=NotificationChannel.SLACK_DM,
                    employee_name=context.employee.person.name,
                    voice_note_url=f"https://bloom.company.com/voice/{evaluation.id}/{peer_id}",
                )
                result.notifications_sent += 1

            # Create peer feedback deadline
            await self.create_deadline(
                evaluation_id=evaluation.id,
                deadline_type=DeadlineType.PEER_FEEDBACK,
                due_date=datetime.now() + timedelta(days=14),
                description="Peer feedback submission deadline",
            )

            result.deadlines_created += 1

            # Also request self-evaluation
            await self.send_notification(
                recipient_id=evaluation.employee_id,
                template_name="self_eval_request",
                channel=NotificationChannel.EMAIL,
                employee_name=context.employee.person.name,
            )

            result.notifications_sent += 1

            # Create self-eval deadline
            await self.create_deadline(
                evaluation_id=evaluation.id,
                deadline_type=DeadlineType.SELF_EVALUATION,
                due_date=datetime.now() + timedelta(days=14),
                responsible_user_id=evaluation.employee_id,
                description="Self-evaluation submission deadline",
            )

            result.deadlines_created += 1

            result.next_state = EvaluationState.PEER_FEEDBACK_IN_PROGRESS
            result.messages.append(f"Requested feedback from {len(evaluation.manager_approved_peers)} peers")

            return result

        except Exception as e:
            logger.error(f"Phase 2 entry failed: {e}")
            result.success = False
            result.errors.append(str(e))
            return result

    async def handle_peer_feedback_submitted(
        self,
        context: PhaseContext,
        peer_id: UUID,
        raw_feedback: str,
    ) -> PhaseResult:
        """
        Handle peer feedback submission

        Args:
            context: Phase context
            peer_id: Peer who submitted feedback
            raw_feedback: Raw feedback text/transcription

        Returns:
            Phase result
        """
        logger.info(f"Processing peer feedback from {peer_id}")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        # Trigger Voice Synthesizer agent if needed
        if "voice_note" in context.metadata:
            result.agents_triggered.append("Voice Synthesizer")
            result.messages.append("Synthesizing voice note to professional feedback")

        # Check if all feedback collected
        expected = len(evaluation.manager_approved_peers)
        received = len(evaluation.peer_feedbacks) + 1  # +1 for this new one

        result.messages.append(f"Received {received}/{expected} peer feedback responses")

        # Check if self-eval also complete
        if received >= expected and evaluation.self_evaluation:
            result.next_state = EvaluationState.DATA_GATHERING_COMPLETE
            result.messages.append("All data gathering complete")

        return result

    async def handle_self_eval_submitted(
        self,
        context: PhaseContext,
    ) -> PhaseResult:
        """
        Handle self-evaluation submission

        Args:
            context: Phase context

        Returns:
            Phase result
        """
        logger.info("Processing self-evaluation submission")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        # Trigger Voice Synthesizer if voice note used
        result.agents_triggered.append("Voice Synthesizer")

        # Check if peer feedback also complete
        expected_peers = len(evaluation.manager_approved_peers)
        received_peers = len(evaluation.peer_feedbacks)

        if received_peers >= expected_peers:
            result.next_state = EvaluationState.DATA_GATHERING_COMPLETE
            result.messages.append("All data gathering complete")

        return result

    async def exit_phase(self, context: PhaseContext) -> PhaseResult:
        """Exit Phase 2, transition to manager evaluation"""
        logger.info("Exiting Phase 2: Data Gathering")

        result = PhaseResult(success=True, phase=self.phase)

        # Validate completion
        is_complete, issues = await self.validate_phase_complete(context)

        if not is_complete:
            result.success = False
            result.errors.extend(issues)
            return result

        result.messages.append("Phase 2 complete, ready for manager evaluation")
        return result

    async def validate_phase_complete(self, context: PhaseContext) -> tuple[bool, List[str]]:
        """Validate Phase 2 is complete"""
        issues: List[str] = []

        evaluation = context.evaluation

        # Check peer feedback
        expected = len(evaluation.manager_approved_peers)
        received = len(evaluation.peer_feedbacks)

        if received < expected:
            issues.append(f"Missing peer feedback: {received}/{expected} received")

        # Check self-evaluation
        if not evaluation.self_evaluation:
            issues.append("Self-evaluation not submitted")

        return len(issues) == 0, issues


class ManagerEvaluationHandler(PhaseHandler):
    """
    Phase 3: Manager Evaluation Handler

    Manages:
    - AI draft generation from all inputs
    - Manager review and refinement
    - Interactive Q&A for missing context
    - Final evaluation submission
    """

    def __init__(self):
        super().__init__()
        self.phase = EvaluationPhase.MANAGER_EVALUATION

    async def enter_phase(self, context: PhaseContext) -> PhaseResult:
        """
        Enter manager evaluation phase

        Triggers Draft Writer agent
        """
        logger.info(f"Entering Phase 3: Manager Evaluation for evaluation {context.evaluation.id}")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        try:
            # Trigger Draft Writer agent
            result.agents_triggered.append("Draft Writer")
            result.messages.append("Generating AI draft from all collected data")

            # Notify manager
            await self.send_notification(
                recipient_id=evaluation.manager_id,
                template_name="manager_eval_started",
                channel=NotificationChannel.SLACK_DM,
                employee_name=context.employee.person.name,
            )

            result.notifications_sent += 1

            # Create deadline
            await self.create_deadline(
                evaluation_id=evaluation.id,
                deadline_type=DeadlineType.MANAGER_EVALUATION,
                due_date=datetime.now() + timedelta(days=7),
                responsible_user_id=evaluation.manager_id,
                description="Manager evaluation deadline",
            )

            result.deadlines_created += 1

            result.next_state = EvaluationState.AI_DRAFT_GENERATED
            return result

        except Exception as e:
            logger.error(f"Phase 3 entry failed: {e}")
            result.success = False
            result.errors.append(str(e))
            return result

    async def handle_draft_generated(
        self,
        context: PhaseContext,
        draft_summary: str,
    ) -> PhaseResult:
        """
        Handle AI draft generation complete

        Args:
            context: Phase context
            draft_summary: Generated draft

        Returns:
            Phase result
        """
        logger.info("AI draft generated, notifying manager")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        # Notify manager to review
        await self.send_notification(
            recipient_id=evaluation.manager_id,
            template_name="manager_review_request",
            channel=NotificationChannel.EMAIL,
            employee_name=context.employee.person.name,
            dashboard_url=f"https://bloom.company.com/evaluations/{evaluation.id}",
        )

        result.notifications_sent += 1
        result.next_state = EvaluationState.MANAGER_REVIEW_IN_PROGRESS

        return result

    async def handle_manager_submission(
        self,
        context: PhaseContext,
    ) -> PhaseResult:
        """
        Handle manager evaluation submission

        Args:
            context: Phase context

        Returns:
            Phase result
        """
        logger.info("Manager evaluation finalized")

        result = PhaseResult(success=True, phase=self.phase)
        result.next_state = EvaluationState.MANAGER_EVAL_COMPLETE
        result.messages.append("Manager evaluation complete, ready for calibration")

        return result

    async def exit_phase(self, context: PhaseContext) -> PhaseResult:
        """Exit Phase 3, transition to calibration"""
        logger.info("Exiting Phase 3: Manager Evaluation")

        result = PhaseResult(success=True, phase=self.phase)

        # Validate completion
        is_complete, issues = await self.validate_phase_complete(context)

        if not is_complete:
            result.success = False
            result.errors.extend(issues)
            return result

        result.messages.append("Phase 3 complete, queuing for calibration")
        return result

    async def validate_phase_complete(self, context: PhaseContext) -> tuple[bool, List[str]]:
        """Validate Phase 3 is complete"""
        issues: List[str] = []

        evaluation = context.evaluation

        if not evaluation.manager_evaluation:
            issues.append("Manager evaluation not submitted")
        elif not evaluation.manager_evaluation.final_summary:
            issues.append("Manager evaluation summary is empty")

        return len(issues) == 0, issues


class CalibrationHandler(PhaseHandler):
    """
    Phase 4: Calibration Handler

    Manages:
    - Calibration session scheduling
    - Rating normalization across teams
    - Promotion decision alignment
    - Final rating updates
    """

    def __init__(self):
        super().__init__()
        self.phase = EvaluationPhase.CALIBRATION

    async def enter_phase(self, context: PhaseContext) -> PhaseResult:
        """
        Enter calibration phase

        Queues evaluation for calibration session
        """
        logger.info(f"Entering Phase 4: Calibration for evaluation {context.evaluation.id}")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        try:
            # Notify calibration committee
            await self.send_notification(
                recipient_id=evaluation.manager_id,
                template_name="calibration_pending",
                channel=NotificationChannel.EMAIL,
                employee_name=context.employee.person.name,
                employee_level=context.employee.person.level.value,
            )

            result.notifications_sent += 1

            result.next_state = EvaluationState.CALIBRATION_PENDING
            result.messages.append("Evaluation queued for calibration session")

            return result

        except Exception as e:
            logger.error(f"Phase 4 entry failed: {e}")
            result.success = False
            result.errors.append(str(e))
            return result

    async def handle_calibration_complete(
        self,
        context: PhaseContext,
        calibration_notes: str,
    ) -> PhaseResult:
        """
        Handle calibration completion

        Args:
            context: Phase context
            calibration_notes: Notes from calibration session

        Returns:
            Phase result
        """
        logger.info("Calibration complete, ratings finalized")

        result = PhaseResult(success=True, phase=self.phase)
        result.next_state = EvaluationState.CALIBRATION_COMPLETE
        result.messages.append("Ratings calibrated and finalized")

        return result

    async def exit_phase(self, context: PhaseContext) -> PhaseResult:
        """Exit Phase 4, transition to release"""
        logger.info("Exiting Phase 4: Calibration")

        result = PhaseResult(success=True, phase=self.phase)
        result.messages.append("Phase 4 complete, scheduling evaluation release")
        return result

    async def validate_phase_complete(self, context: PhaseContext) -> tuple[bool, List[str]]:
        """Validate Phase 4 is complete"""
        issues: List[str] = []

        evaluation = context.evaluation

        if not evaluation.manager_evaluation:
            issues.append("No manager evaluation found")
        elif not evaluation.manager_evaluation.calibrated_at:
            issues.append("Evaluation not calibrated")

        return len(issues) == 0, issues


class ReleaseDiscussionHandler(PhaseHandler):
    """
    Phase 5: Release & Discussion Handler

    Manages:
    - Evaluation release scheduling and delivery
    - Discussion meeting scheduling
    - Employee acknowledgment/decline
    - Committee review if declined
    - Evaluation completion
    """

    def __init__(self):
        super().__init__()
        self.phase = EvaluationPhase.RELEASE_DISCUSSION

    async def enter_phase(self, context: PhaseContext) -> PhaseResult:
        """
        Enter release & discussion phase

        Schedules evaluation release
        """
        logger.info(f"Entering Phase 5: Release & Discussion for evaluation {context.evaluation.id}")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        try:
            # Schedule release (typically next business day)
            release_date = datetime.now() + timedelta(days=1)

            await self.create_deadline(
                evaluation_id=evaluation.id,
                deadline_type=DeadlineType.RELEASE,
                due_date=release_date,
                description="Evaluation release date",
            )

            result.deadlines_created += 1
            result.next_state = EvaluationState.RELEASE_SCHEDULED
            result.messages.append(f"Evaluation release scheduled for {release_date.date()}")

            return result

        except Exception as e:
            logger.error(f"Phase 5 entry failed: {e}")
            result.success = False
            result.errors.append(str(e))
            return result

    async def handle_release(
        self,
        context: PhaseContext,
    ) -> PhaseResult:
        """
        Handle evaluation release

        Args:
            context: Phase context

        Returns:
            Phase result
        """
        logger.info("Releasing evaluation to employee")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        # Send release notification
        await self.send_notification(
            recipient_id=evaluation.employee_id,
            template_name="eval_released",
            channel=NotificationChannel.EMAIL,
            employee_name=context.employee.person.name,
            dashboard_url=f"https://bloom.company.com/evaluations/{evaluation.id}",
        )

        result.notifications_sent += 1

        # Trigger Release Manager agent to schedule discussion
        result.agents_triggered.append("Release Manager")

        result.next_state = EvaluationState.RELEASED
        result.messages.append("Evaluation released to employee")

        return result

    async def handle_discussion_scheduled(
        self,
        context: PhaseContext,
        meeting_time: datetime,
    ) -> PhaseResult:
        """
        Handle discussion scheduling

        Args:
            context: Phase context
            meeting_time: Scheduled meeting time

        Returns:
            Phase result
        """
        logger.info(f"Discussion scheduled for {meeting_time}")

        result = PhaseResult(success=True, phase=self.phase)
        evaluation = context.evaluation

        # Send calendar invites
        await self.send_notification(
            recipient_id=evaluation.employee_id,
            template_name="discussion_scheduled",
            channel=NotificationChannel.EMAIL,
            meeting_time=meeting_time.isoformat(),
        )

        result.notifications_sent += 1

        result.next_state = EvaluationState.DISCUSSION_SCHEDULED
        result.messages.append("Discussion meeting scheduled")

        return result

    async def handle_acknowledgment(
        self,
        context: PhaseContext,
        acknowledged: bool,
    ) -> PhaseResult:
        """
        Handle employee acknowledgment or decline

        Args:
            context: Phase context
            acknowledged: True if acknowledged, False if declined

        Returns:
            Phase result
        """
        logger.info(f"Employee {'acknowledged' if acknowledged else 'declined'} evaluation")

        result = PhaseResult(success=True, phase=self.phase)

        if acknowledged:
            result.next_state = EvaluationState.ACKNOWLEDGED
            result.messages.append("Evaluation acknowledged, process complete")
        else:
            result.next_state = EvaluationState.DECLINED
            result.messages.append("Evaluation declined, routing to committee review")

            # Notify committee
            await self.send_notification(
                recipient_id=context.evaluation.manager_id,
                template_name="eval_declined",
                channel=NotificationChannel.EMAIL,
                employee_name=context.employee.person.name,
            )

            result.notifications_sent += 1

        return result

    async def exit_phase(self, context: PhaseContext) -> PhaseResult:
        """Exit Phase 5, evaluation complete"""
        logger.info("Exiting Phase 5: Release & Discussion")

        result = PhaseResult(success=True, phase=self.phase)
        result.messages.append("Phase 5 complete, evaluation cycle finished")
        return result

    async def validate_phase_complete(self, context: PhaseContext) -> tuple[bool, List[str]]:
        """Validate Phase 5 is complete"""
        issues: List[str] = []

        evaluation = context.evaluation

        if not evaluation.released_at:
            issues.append("Evaluation not released")

        if not evaluation.discussion_completed_at:
            issues.append("Discussion not completed")

        if not evaluation.employee_acknowledged and not evaluation.employee_declined:
            issues.append("Employee has not responded")

        if evaluation.employee_declined and not evaluation.committee_decision:
            issues.append("Declined evaluation pending committee review")

        return len(issues) == 0, issues
