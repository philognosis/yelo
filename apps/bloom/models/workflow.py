"""
Workflow Data Models

Defines workflow orchestration entities for state machine transitions,
event tracking, deadlines, and notifications.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from bloom.models.evaluation import EvaluationPhase, EvaluationState


class EventType(str, Enum):
    """Types of workflow events"""

    # State transitions
    STATE_CHANGED = "state_changed"
    PHASE_CHANGED = "phase_changed"

    # User actions
    PEER_SELECTED = "peer_selected"
    PEER_APPROVED = "peer_approved"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    SELF_EVAL_SUBMITTED = "self_eval_submitted"
    MANAGER_EVAL_SUBMITTED = "manager_eval_submitted"
    EVALUATION_RELEASED = "evaluation_released"
    EMPLOYEE_ACKNOWLEDGED = "employee_acknowledged"
    EMPLOYEE_DECLINED = "employee_declined"

    # System events
    DEADLINE_APPROACHING = "deadline_approaching"
    DEADLINE_MISSED = "deadline_missed"
    REMINDER_SENT = "reminder_sent"
    NOTIFICATION_SENT = "notification_sent"
    ERROR_OCCURRED = "error_occurred"

    # Agent actions
    AGENT_TRIGGERED = "agent_triggered"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"

    # Calendar events
    MEETING_SCHEDULED = "meeting_scheduled"
    MEETING_COMPLETED = "meeting_completed"


class WorkflowEvent(BaseModel):
    """
    Workflow event record

    Tracks all significant events in the evaluation workflow for
    audit trails, debugging, and analytics.
    """

    id: UUID = Field(default_factory=uuid4)
    evaluation_id: UUID = Field(..., description="Associated evaluation")
    event_type: EventType = Field(..., description="Type of event")

    # Event source
    actor_id: Optional[UUID] = Field(None, description="User/agent that triggered event")
    actor_type: str = Field(default="system", description="Type of actor (user, agent, system)")

    # Event details
    description: str = Field(..., description="Human-readable event description")
    previous_state: Optional[EvaluationState] = Field(None, description="State before event")
    new_state: Optional[EvaluationState] = Field(None, description="State after event")
    previous_phase: Optional[EvaluationPhase] = Field(None, description="Phase before event")
    new_phase: Optional[EvaluationPhase] = Field(None, description="Phase after event")

    # Context data
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event-specific data"
    )
    tags: Set[str] = Field(default_factory=set, description="Event tags for filtering")

    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: Optional[float] = Field(None, description="Event processing duration (ms)")

    # Error tracking
    is_error: bool = Field(default=False)
    error_message: Optional[str] = None
    error_stack_trace: Optional[str] = None

    def add_tag(self, tag: str) -> None:
        """Add a tag to the event"""
        self.tags.add(tag)

    def to_log_entry(self) -> str:
        """
        Convert event to log-friendly string

        Returns:
            Formatted log entry
        """
        parts = [
            f"[{self.timestamp.isoformat()}]",
            f"[{self.event_type.value}]",
            f"[{self.actor_type}]",
            self.description,
        ]

        if self.is_error:
            parts.append(f"ERROR: {self.error_message}")

        return " ".join(parts)

    class Config:
        json_schema_extra = {
            "example": {
                "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "state_changed",
                "actor_type": "agent",
                "description": "Transitioned to peer feedback collection",
                "previous_state": "peer_list_locked",
                "new_state": "peer_feedback_requested",
                "metadata": {"agent_name": "Context Miner"},
            }
        }


class TransitionTrigger(str, Enum):
    """What triggers a state transition"""

    MANUAL = "manual"  # User action
    AUTOMATIC = "automatic"  # System/time-based
    AGENT = "agent"  # Agent decision
    DEADLINE = "deadline"  # Deadline reached
    COMPLETION = "completion"  # Task completion


class StateTransition(BaseModel):
    """
    State machine transition definition

    Defines valid state transitions, their conditions, and
    triggered actions (notifications, agent activations, etc.).
    """

    id: UUID = Field(default_factory=uuid4)

    # Transition definition
    from_state: EvaluationState = Field(..., description="Source state")
    to_state: EvaluationState = Field(..., description="Destination state")
    from_phase: Optional[EvaluationPhase] = Field(None, description="Source phase (if phase changes)")
    to_phase: Optional[EvaluationPhase] = Field(None, description="Destination phase (if phase changes)")

    # Trigger conditions
    trigger: TransitionTrigger = Field(..., description="What triggers this transition")
    required_conditions: List[str] = Field(
        default_factory=list,
        description="Conditions that must be met (e.g., 'all_peers_submitted')"
    )

    # Actions to execute on transition
    trigger_agents: List[str] = Field(
        default_factory=list,
        description="Agent names to trigger on this transition"
    )
    send_notifications: List[str] = Field(
        default_factory=list,
        description="Notification template names to send"
    )
    set_deadlines: List[str] = Field(
        default_factory=list,
        description="Deadline types to set (e.g., 'peer_feedback')"
    )

    # Metadata
    description: str = Field(..., description="Human-readable transition description")
    is_reversible: bool = Field(default=False, description="Can this transition be reversed")
    requires_approval: bool = Field(default=False, description="Requires manual approval")
    priority: int = Field(default=0, description="Transition priority (higher = prefer this path)")

    def is_valid_transition(
        self,
        current_state: EvaluationState,
        current_phase: EvaluationPhase,
    ) -> bool:
        """
        Check if this transition is valid from current state/phase

        Args:
            current_state: Current evaluation state
            current_phase: Current evaluation phase

        Returns:
            True if transition is valid
        """
        if current_state != self.from_state:
            return False

        if self.from_phase is not None and current_phase != self.from_phase:
            return False

        return True

    def get_next_phase(self) -> EvaluationPhase:
        """
        Get the phase after this transition

        Returns:
            Next phase (either to_phase or current from_phase)
        """
        return self.to_phase or self.from_phase or EvaluationPhase.CONTEXT_PEER_SELECTION

    class Config:
        json_schema_extra = {
            "example": {
                "from_state": "peer_list_locked",
                "to_state": "peer_feedback_requested",
                "trigger": "automatic",
                "description": "Begin peer feedback collection",
                "trigger_agents": ["Peer Collector"],
                "send_notifications": ["peer_feedback_request"],
                "set_deadlines": ["peer_feedback"],
            }
        }


class DeadlineType(str, Enum):
    """Types of deadlines in the workflow"""

    PEER_SELECTION = "peer_selection"
    PEER_FEEDBACK = "peer_feedback"
    SELF_EVALUATION = "self_evaluation"
    MANAGER_EVALUATION = "manager_evaluation"
    CALIBRATION = "calibration"
    RELEASE = "release"
    DISCUSSION = "discussion"
    ACKNOWLEDGMENT = "acknowledgment"


class DeadlineStatus(str, Enum):
    """Deadline status"""

    UPCOMING = "upcoming"  # Deadline is in the future
    APPROACHING = "approaching"  # Deadline is near (within warning period)
    DUE_TODAY = "due_today"  # Deadline is today
    OVERDUE = "overdue"  # Deadline has passed
    COMPLETED = "completed"  # Task completed before deadline
    CANCELLED = "cancelled"  # Deadline cancelled


class Deadline(BaseModel):
    """
    Deadline tracking

    Manages deadlines for various evaluation tasks with
    warnings, escalations, and completion tracking.
    """

    id: UUID = Field(default_factory=uuid4)
    evaluation_id: UUID = Field(..., description="Associated evaluation")
    deadline_type: DeadlineType = Field(..., description="Type of deadline")

    # Timing
    due_date: datetime = Field(..., description="When task is due")
    warning_date: Optional[datetime] = Field(
        None,
        description="When to send warning (e.g., 2 days before)"
    )
    escalation_date: Optional[datetime] = Field(
        None,
        description="When to escalate (e.g., 1 day after due date)"
    )

    # Responsible parties
    responsible_user_id: Optional[UUID] = Field(None, description="User responsible for meeting deadline")
    responsible_users: List[UUID] = Field(
        default_factory=list,
        description="Multiple users responsible"
    )
    escalation_user_id: Optional[UUID] = Field(None, description="User to escalate to if missed")

    # Status tracking
    status: DeadlineStatus = Field(default=DeadlineStatus.UPCOMING)
    completed_at: Optional[datetime] = Field(None, description="When task was completed")
    warning_sent_at: Optional[datetime] = Field(None, description="When warning was sent")
    escalation_sent_at: Optional[datetime] = Field(None, description="When escalation was sent")

    # Reminders
    reminder_schedule: List[int] = Field(
        default_factory=list,
        description="Days before due date to send reminders (e.g., [7, 3, 1])"
    )
    reminders_sent: List[datetime] = Field(
        default_factory=list,
        description="Timestamps of sent reminders"
    )

    # Metadata
    description: str = Field(..., description="Human-readable deadline description")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update_status(self) -> DeadlineStatus:
        """
        Update and return current deadline status

        Returns:
            Current deadline status
        """
        now = datetime.now()

        # Check if completed
        if self.completed_at is not None:
            self.status = DeadlineStatus.COMPLETED
            return self.status

        # Check if cancelled
        if self.status == DeadlineStatus.CANCELLED:
            return self.status

        # Check various time-based statuses
        if now > self.due_date:
            self.status = DeadlineStatus.OVERDUE
        elif now.date() == self.due_date.date():
            self.status = DeadlineStatus.DUE_TODAY
        elif self.warning_date and now >= self.warning_date:
            self.status = DeadlineStatus.APPROACHING
        else:
            self.status = DeadlineStatus.UPCOMING

        self.updated_at = datetime.now()
        return self.status

    def get_time_remaining(self) -> timedelta:
        """
        Get time remaining until deadline

        Returns:
            Time remaining (negative if overdue)
        """
        return self.due_date - datetime.now()

    def is_overdue(self) -> bool:
        """
        Check if deadline is overdue

        Returns:
            True if overdue
        """
        self.update_status()
        return self.status == DeadlineStatus.OVERDUE

    def needs_reminder(self) -> bool:
        """
        Check if a reminder should be sent

        Returns:
            True if reminder is due
        """
        if self.status in [DeadlineStatus.COMPLETED, DeadlineStatus.CANCELLED]:
            return False

        now = datetime.now()
        days_until_due = (self.due_date - now).days

        # Check if any reminder day matches and hasn't been sent yet
        for reminder_day in self.reminder_schedule:
            if days_until_due <= reminder_day:
                # Check if we haven't sent this many reminders yet
                if len(self.reminders_sent) < len([d for d in self.reminder_schedule if d >= reminder_day]):
                    return True

        return False

    def mark_reminder_sent(self) -> None:
        """Record that a reminder was sent"""
        self.reminders_sent.append(datetime.now())
        self.updated_at = datetime.now()

    def mark_completed(self) -> None:
        """Mark deadline as completed"""
        self.completed_at = datetime.now()
        self.status = DeadlineStatus.COMPLETED
        self.updated_at = datetime.now()

    def mark_cancelled(self) -> None:
        """Mark deadline as cancelled"""
        self.status = DeadlineStatus.CANCELLED
        self.updated_at = datetime.now()

    @classmethod
    def create_with_warning(
        cls,
        evaluation_id: UUID,
        deadline_type: DeadlineType,
        due_date: datetime,
        warning_days: int = 2,
        description: str = "",
        **kwargs,
    ) -> Deadline:
        """
        Create deadline with automatic warning date

        Args:
            evaluation_id: Associated evaluation
            deadline_type: Type of deadline
            due_date: When task is due
            warning_days: Days before due date to warn
            description: Human-readable description
            **kwargs: Additional deadline fields

        Returns:
            New deadline instance
        """
        warning_date = due_date - timedelta(days=warning_days)

        return cls(
            evaluation_id=evaluation_id,
            deadline_type=deadline_type,
            due_date=due_date,
            warning_date=warning_date,
            description=description or f"{deadline_type.value} deadline",
            **kwargs,
        )

    class Config:
        json_schema_extra = {
            "example": {
                "evaluation_id": "550e8400-e29b-41d4-a716-446655440000",
                "deadline_type": "peer_feedback",
                "due_date": "2024-12-15T17:00:00",
                "warning_date": "2024-12-13T09:00:00",
                "description": "Peer feedback submission deadline",
                "reminder_schedule": [7, 3, 1],
                "status": "upcoming",
            }
        }


class NotificationChannel(str, Enum):
    """Notification delivery channels"""

    EMAIL = "email"
    SLACK = "slack"
    SLACK_DM = "slack_dm"
    IN_APP = "in_app"
    SMS = "sms"


class NotificationPriority(str, Enum):
    """Notification priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Notification delivery status"""

    PENDING = "pending"  # Queued for delivery
    SENT = "sent"  # Successfully sent
    DELIVERED = "delivered"  # Confirmed delivered
    READ = "read"  # User has read/opened
    FAILED = "failed"  # Delivery failed
    CANCELLED = "cancelled"  # Cancelled before sending


class Notification(BaseModel):
    """
    Notification tracking

    Manages multi-channel notifications with delivery tracking,
    retry logic, and user interaction monitoring.
    """

    id: UUID = Field(default_factory=uuid4)
    evaluation_id: Optional[UUID] = Field(None, description="Associated evaluation (if applicable)")

    # Recipients
    recipient_id: UUID = Field(..., description="Primary recipient")
    cc_recipients: List[UUID] = Field(default_factory=list, description="CC recipients")

    # Message content
    template_name: str = Field(..., description="Notification template identifier")
    subject: str = Field(..., description="Notification subject/title")
    message: str = Field(..., description="Notification body/content")
    action_url: Optional[str] = Field(None, description="URL for user action")
    action_label: Optional[str] = Field(None, description="Label for action button")

    # Delivery
    channel: NotificationChannel = Field(..., description="Delivery channel")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    status: NotificationStatus = Field(default=NotificationStatus.PENDING)

    # Timing
    scheduled_for: Optional[datetime] = Field(
        None,
        description="When to send (None for immediate)"
    )
    sent_at: Optional[datetime] = Field(None)
    delivered_at: Optional[datetime] = Field(None)
    read_at: Optional[datetime] = Field(None)

    # Retry logic
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_count: int = Field(default=0)
    retry_after: Optional[datetime] = Field(None, description="When to retry after failure")

    # Tracking
    external_id: Optional[str] = Field(
        None,
        description="External system ID (e.g., Slack message ID)"
    )
    delivery_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Channel-specific delivery data"
    )

    # Error tracking
    error_message: Optional[str] = None
    error_count: int = Field(default=0)

    # User interaction
    clicked: bool = Field(default=False, description="User clicked action link")
    clicked_at: Optional[datetime] = None
    responded: bool = Field(default=False, description="User responded")
    response_data: Optional[Dict[str, Any]] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def mark_sent(self, external_id: Optional[str] = None) -> None:
        """
        Mark notification as sent

        Args:
            external_id: External system message ID
        """
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now()
        if external_id:
            self.external_id = external_id
        self.updated_at = datetime.now()

    def mark_delivered(self) -> None:
        """Mark notification as delivered"""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_read(self) -> None:
        """Mark notification as read"""
        self.status = NotificationStatus.READ
        self.read_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_failed(self, error_message: str, retry_after: Optional[datetime] = None) -> None:
        """
        Mark notification as failed

        Args:
            error_message: Error description
            retry_after: When to retry (if applicable)
        """
        self.status = NotificationStatus.FAILED
        self.error_message = error_message
        self.error_count += 1
        self.retry_count += 1

        if retry_after:
            self.retry_after = retry_after
            self.status = NotificationStatus.PENDING  # Re-queue for retry

        self.updated_at = datetime.now()

    def mark_clicked(self) -> None:
        """Mark notification action as clicked"""
        self.clicked = True
        self.clicked_at = datetime.now()
        self.updated_at = datetime.now()

    def should_retry(self) -> bool:
        """
        Check if notification should be retried

        Returns:
            True if retry should be attempted
        """
        if self.status != NotificationStatus.FAILED:
            return False

        if self.retry_count >= self.max_retries:
            return False

        if self.retry_after and datetime.now() < self.retry_after:
            return False

        return True

    def is_actionable(self) -> bool:
        """
        Check if notification has an action for user

        Returns:
            True if notification has action URL
        """
        return self.action_url is not None

    def get_delivery_time(self) -> Optional[timedelta]:
        """
        Get time taken to deliver

        Returns:
            Time from creation to delivery (None if not delivered)
        """
        if not self.delivered_at:
            return None

        return self.delivered_at - self.created_at

    @classmethod
    def create_from_template(
        cls,
        template_name: str,
        recipient_id: UUID,
        channel: NotificationChannel,
        template_data: Dict[str, Any],
        evaluation_id: Optional[UUID] = None,
        **kwargs,
    ) -> Notification:
        """
        Create notification from template

        Args:
            template_name: Template identifier
            recipient_id: Notification recipient
            channel: Delivery channel
            template_data: Data to populate template
            evaluation_id: Associated evaluation
            **kwargs: Additional notification fields

        Returns:
            New notification instance
        """
        # In production, this would render actual templates
        # For now, we'll use simple string formatting
        subject = template_data.get("subject", f"Notification: {template_name}")
        message = template_data.get("message", "")

        return cls(
            template_name=template_name,
            recipient_id=recipient_id,
            channel=channel,
            subject=subject,
            message=message,
            evaluation_id=evaluation_id,
            **kwargs,
        )

    class Config:
        json_schema_extra = {
            "example": {
                "recipient_id": "550e8400-e29b-41d4-a716-446655440000",
                "template_name": "peer_feedback_request",
                "subject": "Peer Feedback Request for Jane Doe",
                "message": "You have been selected to provide feedback for Jane Doe...",
                "channel": "slack_dm",
                "action_url": "https://bloom.company.com/feedback/12345",
                "action_label": "Provide Feedback",
                "priority": "normal",
                "status": "pending",
            }
        }
