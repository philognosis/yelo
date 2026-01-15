"""
Chaser Agent - Deadline Enforcer and Notification Manager

The Chaser ensures evaluation deadlines are met through proactive monitoring
and escalating notifications.

Responsibilities:
- Monitor evaluation deadlines continuously
- Send escalating notifications (reminder → warning → escalation)
- Track completion rates and identify bottlenecks
- Generate deadline reports for managers
- Coordinate with Watchkeeper for state transitions

Design Pattern: Event-Driven Notification System + Escalation Engine
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from loguru import logger

from apps.bloom.models.evaluation import Evaluation, EvaluationPhase, EvaluationState
from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.memory import MemoryType
from iras.core.state import AgentStatus
from iras.databases.document_store import DocumentStore
from iras.databases.timeseries_store import TimeSeriesStore


class NotificationType(str, Enum):
    """Types of notifications"""

    REMINDER = "reminder"  # Gentle reminder, 3+ days before
    WARNING = "warning"  # Urgent warning, 1-2 days before
    ESCALATION = "escalation"  # Missed deadline, escalate to manager
    COMPLETION = "completion"  # Positive: task completed


class NotificationChannel(str, Enum):
    """Notification delivery channels"""

    EMAIL = "email"
    SLACK = "slack"
    IN_APP = "in_app"
    SMS = "sms"


class Notification:
    """Notification record"""

    def __init__(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        subject: str,
        message: str,
        channels: List[NotificationChannel],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = UUID(int=0)  # Will be assigned
        self.recipient_id = recipient_id
        self.notification_type = notification_type
        self.subject = subject
        self.message = message
        self.channels = channels
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.sent_at: Optional[datetime] = None
        self.read_at: Optional[datetime] = None


class Chaser(Agent):
    """
    Deadline enforcement and notification agent

    The Chaser is relentless in ensuring deadlines are met,
    using a sophisticated escalation strategy to motivate completion.

    Capabilities:
    - Deadline monitoring
    - Multi-channel notifications
    - Escalation management
    - Completion tracking
    - Bottleneck identification
    - Manager reporting
    """

    def __init__(
        self,
        name: str = "Chaser",
        document_store: Optional[DocumentStore] = None,
        timeseries_store: Optional[TimeSeriesStore] = None,
    ):
        config = AgentConfig(
            name=name,
            role="enforcer",
            capabilities={
                "deadline_monitoring",
                "notification_management",
                "escalation_handling",
                "completion_tracking",
                "reporting",
            },
            temperature=0.1,  # Deterministic for enforcement
            max_tokens=2000,
            autonomous_mode=True,
        )
        super().__init__(config)

        # Database connections
        self.document_store = document_store or DocumentStore()
        self.timeseries_store = timeseries_store or TimeSeriesStore()

        # Escalation configuration
        self.escalation_schedule = {
            "reminder_days_before": 3,  # First reminder 3 days before
            "warning_days_before": 1,  # Warning 1 day before
            "escalation_hours_after": 24,  # Escalate 24h after deadline
        }

        # Notification tracking
        self.sent_notifications: Dict[UUID, List[Notification]] = {}

        # Register tools
        self._register_chaser_tools()

        logger.info(f"Chaser '{name}' initialized with escalation monitoring")

    def _register_chaser_tools(self) -> None:
        """Register Chaser-specific tools"""
        self.register_tool(
            AgentTool(
                name="check_and_notify_deadlines",
                description="Check deadlines and send notifications",
                parameters={},
                function=self.check_and_notify_deadlines,
            )
        )

        self.register_tool(
            AgentTool(
                name="send_notification",
                description="Send notification to user",
                parameters={
                    "recipient_id": {"type": "string"},
                    "notification_type": {"type": "string"},
                    "subject": {"type": "string"},
                    "message": {"type": "string"},
                },
                function=self.send_notification,
            )
        )

        self.register_tool(
            AgentTool(
                name="generate_completion_report",
                description="Generate completion rate report",
                parameters={
                    "cycle_name": {"type": "string"},
                },
                function=self.generate_completion_report,
            )
        )

    async def check_and_notify_deadlines(self) -> Dict[str, Any]:
        """
        Check all deadlines and send appropriate notifications

        This is the main enforcement loop that:
        1. Scans all active evaluations
        2. Calculates time to deadline
        3. Sends appropriate notifications based on escalation schedule
        4. Records metrics

        Returns:
            Summary of notifications sent
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason="Checking deadlines and sending notifications",
        )

        try:
            now = datetime.now()
            notifications_sent = {
                NotificationType.REMINDER: 0,
                NotificationType.WARNING: 0,
                NotificationType.ESCALATION: 0,
                NotificationType.COMPLETION: 0,
            }

            # Get all active evaluations
            evaluations = await self.document_store.find(
                collection="evaluations",
                query={"current_phase": {"$ne": "completed"}},
            )

            logger.info(f"Checking deadlines for {len(evaluations)} active evaluations")

            for eval_doc in evaluations:
                eval_id = UUID(eval_doc["_id"])
                employee_id = UUID(eval_doc["employee_id"])
                manager_id = UUID(eval_doc["manager_id"])
                current_state = eval_doc["current_state"]

                # Check each deadline type based on current state
                if current_state in [
                    EvaluationState.CYCLE_STARTED,
                    EvaluationState.PEER_SUGGESTION_GENERATED,
                    EvaluationState.EMPLOYEE_PEER_REVIEW,
                ]:
                    # Check peer selection deadline
                    await self._check_deadline(
                        eval_id=eval_id,
                        recipient_id=employee_id,
                        deadline_type="peer_selection",
                        deadline_str=eval_doc.get("peer_selection_deadline"),
                        now=now,
                        notifications_sent=notifications_sent,
                    )

                elif current_state in [
                    EvaluationState.PEER_FEEDBACK_REQUESTED,
                    EvaluationState.PEER_FEEDBACK_IN_PROGRESS,
                ]:
                    # Check peer feedback deadline
                    # Notify each peer who hasn't submitted
                    for peer_id in eval_doc.get("manager_approved_peers", []):
                        submitted_peers = [
                            UUID(fb["peer_id"]) for fb in eval_doc.get("peer_feedbacks", [])
                        ]
                        if UUID(peer_id) not in submitted_peers:
                            await self._check_deadline(
                                eval_id=eval_id,
                                recipient_id=UUID(peer_id),
                                deadline_type="peer_feedback",
                                deadline_str=eval_doc.get("peer_feedback_deadline"),
                                now=now,
                                notifications_sent=notifications_sent,
                            )

                elif current_state in [
                    EvaluationState.SELF_EVAL_REQUESTED,
                    EvaluationState.SELF_EVAL_IN_PROGRESS,
                ]:
                    # Check self-eval deadline
                    await self._check_deadline(
                        eval_id=eval_id,
                        recipient_id=employee_id,
                        deadline_type="self_eval",
                        deadline_str=eval_doc.get("self_eval_deadline"),
                        now=now,
                        notifications_sent=notifications_sent,
                    )

                elif current_state in [
                    EvaluationState.MANAGER_EVAL_STARTED,
                    EvaluationState.AI_DRAFT_GENERATED,
                    EvaluationState.MANAGER_REVIEW_IN_PROGRESS,
                ]:
                    # Check manager eval deadline
                    await self._check_deadline(
                        eval_id=eval_id,
                        recipient_id=manager_id,
                        deadline_type="manager_eval",
                        deadline_str=eval_doc.get("manager_eval_deadline"),
                        now=now,
                        notifications_sent=notifications_sent,
                    )

            # Record metrics
            total_notifications = sum(notifications_sent.values())
            await self.timeseries_store.write_point(
                metric="chaser.notifications_sent",
                value=float(total_notifications),
                tags={"check_time": now.isoformat()},
            )

            for notif_type, count in notifications_sent.items():
                await self.timeseries_store.write_point(
                    metric=f"chaser.notifications.{notif_type.value}",
                    value=float(count),
                    tags={"check_time": now.isoformat()},
                )

            # Remember in memory
            await self.memory.remember(
                content={
                    "action": "deadline_check",
                    "evaluations_checked": len(evaluations),
                    "notifications_sent": total_notifications,
                    "breakdown": {k.value: v for k, v in notifications_sent.items()},
                },
                importance=0.7,
                memory_type=MemoryType.EPISODIC,
            )

            logger.info(
                f"Deadline check complete: {total_notifications} notifications sent "
                f"({notifications_sent[NotificationType.ESCALATION]} escalations)"
            )

            return {
                "evaluations_checked": len(evaluations),
                "notifications_sent": total_notifications,
                "breakdown": {k.value: v for k, v in notifications_sent.items()},
                "check_time": now.isoformat(),
            }

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def _check_deadline(
        self,
        eval_id: UUID,
        recipient_id: UUID,
        deadline_type: str,
        deadline_str: Optional[str],
        now: datetime,
        notifications_sent: Dict[NotificationType, int],
    ) -> None:
        """
        Check a specific deadline and send notification if needed

        Args:
            eval_id: Evaluation ID
            recipient_id: Who to notify
            deadline_type: Type of deadline
            deadline_str: Deadline timestamp string
            now: Current time
            notifications_sent: Counter to update
        """
        if not deadline_str:
            return

        deadline = datetime.fromisoformat(deadline_str)
        time_to_deadline = (deadline - now).total_seconds() / 3600  # Hours

        # Check if we've already sent a notification recently
        recent_notifs = await self._get_recent_notifications(
            eval_id, recipient_id, deadline_type, hours=24
        )

        # Determine notification type based on time to deadline
        notification_type = None
        should_send = False

        if time_to_deadline < -self.escalation_schedule["escalation_hours_after"]:
            # Past deadline + escalation period
            notification_type = NotificationType.ESCALATION
            # Only send escalation once per day
            should_send = not self._has_recent_notification(
                recent_notifs, NotificationType.ESCALATION, hours=24
            )

        elif time_to_deadline < 0:
            # Past deadline but within escalation grace period
            notification_type = NotificationType.WARNING
            should_send = not self._has_recent_notification(
                recent_notifs, NotificationType.WARNING, hours=12
            )

        elif time_to_deadline < self.escalation_schedule["warning_days_before"] * 24:
            # Approaching deadline (within 1 day)
            notification_type = NotificationType.WARNING
            should_send = not self._has_recent_notification(
                recent_notifs, NotificationType.WARNING, hours=24
            )

        elif time_to_deadline < self.escalation_schedule["reminder_days_before"] * 24:
            # Reminder period (within 3 days)
            notification_type = NotificationType.REMINDER
            should_send = not self._has_recent_notification(
                recent_notifs, NotificationType.REMINDER, hours=48
            )

        if should_send and notification_type:
            await self._send_deadline_notification(
                eval_id=eval_id,
                recipient_id=recipient_id,
                deadline_type=deadline_type,
                notification_type=notification_type,
                deadline=deadline,
                time_to_deadline_hours=time_to_deadline,
            )
            notifications_sent[notification_type] += 1

    async def send_notification(
        self,
        recipient_id: UUID,
        notification_type: NotificationType,
        subject: str,
        message: str,
        channels: Optional[List[NotificationChannel]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send notification to user

        Args:
            recipient_id: Recipient
            notification_type: Type of notification
            subject: Subject line
            message: Message body
            channels: Delivery channels
            metadata: Additional metadata

        Returns:
            Notification result
        """
        if channels is None:
            channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]

        notification = Notification(
            recipient_id=recipient_id,
            notification_type=notification_type,
            subject=subject,
            message=message,
            channels=channels,
            metadata=metadata or {},
        )

        # Store notification
        notif_dict = {
            "recipient_id": str(recipient_id),
            "notification_type": notification_type.value,
            "subject": subject,
            "message": message,
            "channels": [c.value for c in channels],
            "metadata": metadata or {},
            "created_at": notification.created_at.isoformat(),
            "sent_at": datetime.now().isoformat(),
        }

        await self.document_store.insert(
            collection="notifications",
            document=notif_dict,
        )

        # In production, actually send via email/Slack/etc.
        logger.info(
            f"Sent {notification_type.value} notification to {recipient_id}: {subject}"
        )

        # Track sent notification
        if recipient_id not in self.sent_notifications:
            self.sent_notifications[recipient_id] = []
        self.sent_notifications[recipient_id].append(notification)

        return {
            "success": True,
            "recipient_id": str(recipient_id),
            "notification_type": notification_type.value,
            "channels": [c.value for c in channels],
            "sent_at": datetime.now().isoformat(),
        }

    async def generate_completion_report(
        self,
        cycle_name: str,
    ) -> Dict[str, Any]:
        """
        Generate completion rate report for evaluation cycle

        Args:
            cycle_name: Cycle to report on

        Returns:
            Completion statistics
        """
        # Get all evaluations in cycle
        evaluations = await self.document_store.find(
            collection="evaluations",
            query={"cycle_name": cycle_name},
        )

        total = len(evaluations)
        if total == 0:
            return {"cycle_name": cycle_name, "total": 0}

        # Calculate completion by phase
        phase_counts = {}
        for eval_doc in evaluations:
            phase = eval_doc["current_phase"]
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

        # Calculate completion rates for each stage
        peer_selection_complete = sum(
            1
            for e in evaluations
            if e["current_state"] not in ["cycle_started", "peer_suggestion_generated"]
        )

        peer_feedback_complete = sum(
            1
            for e in evaluations
            if e["current_state"]
            not in ["peer_feedback_requested", "peer_feedback_in_progress"]
            and e["current_phase"] != "context_peer_selection"
        )

        manager_eval_complete = sum(
            1
            for e in evaluations
            if e["current_phase"] in ["calibration", "release_discussion", "completed"]
        )

        report = {
            "cycle_name": cycle_name,
            "total_evaluations": total,
            "phase_distribution": phase_counts,
            "completion_rates": {
                "peer_selection": peer_selection_complete / total,
                "peer_feedback": peer_feedback_complete / total,
                "manager_evaluation": manager_eval_complete / total,
            },
            "generated_at": datetime.now().isoformat(),
        }

        logger.info(
            f"Completion report for {cycle_name}: "
            f"{manager_eval_complete}/{total} manager evals complete"
        )

        return report

    async def _send_deadline_notification(
        self,
        eval_id: UUID,
        recipient_id: UUID,
        deadline_type: str,
        notification_type: NotificationType,
        deadline: datetime,
        time_to_deadline_hours: float,
    ) -> None:
        """Send deadline-specific notification"""
        # Generate message based on notification type
        if notification_type == NotificationType.ESCALATION:
            subject = f"🚨 URGENT: Overdue {deadline_type.replace('_', ' ').title()}"
            message = (
                f"Your {deadline_type.replace('_', ' ')} was due on {deadline.strftime('%Y-%m-%d')}. "
                f"This is now {abs(time_to_deadline_hours):.0f} hours overdue. "
                f"Please complete immediately or contact your manager."
            )
            channels = [
                NotificationChannel.EMAIL,
                NotificationChannel.SLACK,
                NotificationChannel.IN_APP,
            ]

        elif notification_type == NotificationType.WARNING:
            subject = f"⚠️ Urgent: {deadline_type.replace('_', ' ').title()} Due Soon"
            if time_to_deadline_hours < 0:
                message = f"Your {deadline_type.replace('_', ' ')} is now overdue. Please complete as soon as possible."
            else:
                message = f"Your {deadline_type.replace('_', ' ')} is due in {time_to_deadline_hours:.0f} hours."
            channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]

        else:  # REMINDER
            subject = f"Reminder: {deadline_type.replace('_', ' ').title()} Due {deadline.strftime('%b %d')}"
            message = (
                f"Friendly reminder: Your {deadline_type.replace('_', ' ')} is due in "
                f"{time_to_deadline_hours / 24:.1f} days."
            )
            channels = [NotificationChannel.IN_APP]

        await self.send_notification(
            recipient_id=recipient_id,
            notification_type=notification_type,
            subject=subject,
            message=message,
            channels=channels,
            metadata={
                "evaluation_id": str(eval_id),
                "deadline_type": deadline_type,
                "deadline": deadline.isoformat(),
            },
        )

    async def _get_recent_notifications(
        self,
        eval_id: UUID,
        recipient_id: UUID,
        deadline_type: str,
        hours: int,
    ) -> List[Dict]:
        """Get recent notifications for evaluation/recipient"""
        cutoff = datetime.now() - timedelta(hours=hours)

        notifications = await self.document_store.find(
            collection="notifications",
            query={
                "recipient_id": str(recipient_id),
                "metadata.evaluation_id": str(eval_id),
                "metadata.deadline_type": deadline_type,
                "created_at": {"$gte": cutoff.isoformat()},
            },
        )

        return notifications

    def _has_recent_notification(
        self,
        recent_notifs: List[Dict],
        notification_type: NotificationType,
        hours: int,
    ) -> bool:
        """Check if notification of type was sent recently"""
        cutoff = datetime.now() - timedelta(hours=hours)

        for notif in recent_notifs:
            if notif["notification_type"] == notification_type.value:
                created_at = datetime.fromisoformat(notif["created_at"])
                if created_at > cutoff:
                    return True

        return False
