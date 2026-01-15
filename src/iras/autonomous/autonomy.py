"""
Autonomous Agent Controller

Main controller for autonomous agent operations, integrating:
- Self-monitoring and health tracking
- Error recovery and resilience
- Adaptive learning and improvement
- Self-directed planning
- Human-in-the-loop decision making
- Confidence-based escalation

Features:
- Autonomous execution loop
- Intelligent decision making
- Continuous self-improvement
- Graceful degradation under failures
- Human oversight for critical decisions
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

from iras.autonomous.adaptive_learning import (
    AdaptiveLearningSystem,
    ExperienceType,
    OutcomeType,
    StrategyType,
)
from iras.autonomous.error_recovery import (
    ErrorRecoverySystem,
    RecoveryAction,
    RetryConfig,
)
from iras.autonomous.monitoring import (
    AlertLevel,
    HealthStatus,
    MetricType,
    MonitoringSystem,
)


class AutonomyLevel(str, Enum):
    """Levels of agent autonomy"""

    MANUAL = "manual"  # Always ask human
    SUPERVISED = "supervised"  # Ask for complex decisions
    SEMI_AUTONOMOUS = "semi_autonomous"  # Ask when low confidence
    AUTONOMOUS = "autonomous"  # Full autonomy
    ADAPTIVE = "adaptive"  # Adjust autonomy based on performance


class DecisionType(str, Enum):
    """Types of decisions"""

    TASK_EXECUTION = "task_execution"
    STRATEGY_SELECTION = "strategy_selection"
    ERROR_RECOVERY = "error_recovery"
    RESOURCE_ALLOCATION = "resource_allocation"
    ESCALATION = "escalation"


class Decision(BaseModel):
    """Represents a decision to be made"""

    id: UUID = Field(default_factory=uuid4)
    type: DecisionType
    description: str
    options: List[str] = Field(default_factory=list)
    recommended_option: Optional[str] = None
    confidence: float = 0.5  # 0.0 to 1.0
    context: Dict[str, Any] = Field(default_factory=dict)
    requires_human: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)
    decision_made: Optional[str] = None
    decided_at: Optional[datetime] = None


class AutonomousTask(BaseModel):
    """Task for autonomous execution"""

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    goal: str
    priority: int = 1
    max_duration: float = 300.0  # seconds
    retry_config: Optional[RetryConfig] = None
    requires_human_approval: bool = False
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class AutonomyConfig(BaseModel):
    """Configuration for autonomous controller"""

    autonomy_level: AutonomyLevel = AutonomyLevel.SEMI_AUTONOMOUS
    confidence_threshold: float = 0.7  # Ask human when below this
    critical_decision_threshold: float = 0.9  # Always ask for very critical
    enable_monitoring: bool = True
    enable_learning: bool = True
    enable_recovery: bool = True
    max_concurrent_tasks: int = 3
    health_check_interval: float = 10.0  # seconds
    learning_interval: float = 300.0  # seconds


class AutonomousController:
    """
    Main autonomous agent controller

    Integrates monitoring, recovery, and learning for fully autonomous operation.

    Features:
    - Self-monitoring and health management
    - Automatic error recovery
    - Continuous learning and adaptation
    - Confidence-based human escalation
    - Self-directed task execution
    """

    def __init__(
        self,
        agent_id: UUID,
        config: Optional[AutonomyConfig] = None,
    ):
        self.agent_id = agent_id
        self.config = config or AutonomyConfig()

        # Core subsystems
        self.monitoring = MonitoringSystem(
            agent_id=agent_id,
            monitoring_interval=self.config.health_check_interval,
        ) if self.config.enable_monitoring else None

        self.recovery = ErrorRecoverySystem(
            agent_id=agent_id,
        ) if self.config.enable_recovery else None

        self.learning = AdaptiveLearningSystem(
            agent_id=agent_id,
        ) if self.config.enable_learning else None

        # State
        self.running = False
        self.current_autonomy_level = self.config.autonomy_level
        self.task_queue: List[AutonomousTask] = []
        self.active_tasks: Dict[UUID, AutonomousTask] = {}
        self.completed_tasks: List[AutonomousTask] = []

        # Decision tracking
        self.pending_decisions: List[Decision] = []
        self.decision_history: List[Decision] = []

        # Human interaction
        self.human_callback: Optional[Callable[[Decision], str]] = None
        self.awaiting_human_response: Set[UUID] = set()

        # Performance tracking
        self.total_autonomous_decisions = 0
        self.total_human_escalations = 0
        self.performance_score = 0.5

        # Background tasks
        self._execution_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None

        logger.info(
            f"Autonomous controller initialized for agent {agent_id} "
            f"at {self.current_autonomy_level.value} level"
        )

    async def start(self) -> None:
        """Start autonomous operation"""
        if self.running:
            logger.warning("Autonomous controller already running")
            return

        self.running = True

        # Start monitoring
        if self.monitoring:
            await self.monitoring.start()
            # Register alert handler
            self.monitoring.add_alert_handler(self._handle_alert)

        # Start execution loop
        self._execution_task = asyncio.create_task(self._execution_loop())

        logger.info("Autonomous controller started")

    async def stop(self) -> None:
        """Stop autonomous operation"""
        if not self.running:
            return

        self.running = False

        # Cancel tasks
        if self._execution_task:
            self._execution_task.cancel()
            try:
                await self._execution_task
            except asyncio.CancelledError:
                pass

        # Stop monitoring
        if self.monitoring:
            await self.monitoring.stop()

        logger.info("Autonomous controller stopped")

    async def _execution_loop(self) -> None:
        """Main autonomous execution loop"""
        while self.running:
            try:
                # Check health status
                await self._check_health()

                # Process pending decisions
                await self._process_decisions()

                # Execute tasks
                await self._execute_tasks()

                # Periodic learning
                if self.learning and self.total_autonomous_decisions % 50 == 0:
                    await self.learning.learn_from_experiences()

                # Adapt autonomy level if in adaptive mode
                if self.config.autonomy_level == AutonomyLevel.ADAPTIVE:
                    await self._adapt_autonomy_level()

                await asyncio.sleep(1.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                await asyncio.sleep(5.0)

    async def _check_health(self) -> None:
        """Check system health and take action if needed"""
        if not self.monitoring:
            return

        health_status = self.monitoring.get_health_status()

        if health_status == HealthStatus.CRITICAL:
            logger.critical("Critical health status detected!")
            # Could trigger graceful degradation here
            await self._handle_critical_health()

        elif health_status == HealthStatus.WARNING:
            logger.warning("Health status is degraded")
            # Maybe reduce concurrent tasks
            if len(self.active_tasks) > 1:
                logger.info("Reducing concurrent tasks due to health warning")

    async def _handle_critical_health(self) -> None:
        """Handle critical health situation"""
        # Cancel non-critical tasks
        for task_id, task in list(self.active_tasks.items()):
            if task.priority < 3:
                logger.warning(f"Cancelling low-priority task: {task.name}")
                task.status = "cancelled"
                del self.active_tasks[task_id]

        # Create alert decision for human
        decision = Decision(
            type=DecisionType.ESCALATION,
            description="Critical health status - system degraded",
            options=["continue_with_degradation", "pause_operations", "shutdown"],
            recommended_option="continue_with_degradation",
            confidence=0.3,
            requires_human=True,
            context={
                "health_status": "critical",
                "active_tasks": len(self.active_tasks),
            },
        )

        await self._request_human_decision(decision)

    def _handle_alert(self, alert) -> None:
        """Handle monitoring alert"""
        logger.warning(f"Alert received: [{alert.level.value}] {alert.title}")

        # Record as experience for learning
        if self.learning:
            asyncio.create_task(
                self.learning.record_experience(
                    experience_type=ExperienceType.ERROR_RECOVERY,
                    action="handle_alert",
                    outcome=OutcomeType.SUCCESS,
                    context={
                        "alert_level": alert.level.value,
                        "metric_type": alert.metric_type.value if alert.metric_type else None,
                    },
                )
            )

        # Take action based on alert level
        if alert.level == AlertLevel.CRITICAL:
            asyncio.create_task(self._handle_critical_health())

    async def _process_decisions(self) -> None:
        """Process pending decisions"""
        if not self.pending_decisions:
            return

        for decision in list(self.pending_decisions):
            if decision.requires_human:
                # Wait for human response
                if decision.id not in self.awaiting_human_response:
                    await self._request_human_decision(decision)
            else:
                # Make autonomous decision
                await self._make_autonomous_decision(decision)
                self.pending_decisions.remove(decision)

    async def _make_autonomous_decision(self, decision: Decision) -> str:
        """
        Make an autonomous decision

        Args:
            decision: Decision to make

        Returns:
            Chosen option
        """
        self.total_autonomous_decisions += 1

        # Use learning to inform decision if available
        if self.learning and decision.recommended_option:
            # Check if we should follow recommendation based on past performance
            success_prob = self.learning.predict_success_probability(
                action=decision.recommended_option,
                context=decision.context,
            )

            if success_prob < 0.3:
                # Low predicted success, consider alternatives
                logger.warning(
                    f"Low predicted success ({success_prob:.2f}) for "
                    f"recommended option: {decision.recommended_option}"
                )

        # Make decision (use recommended if confident, otherwise fallback)
        if decision.confidence >= self.config.confidence_threshold:
            chosen = decision.recommended_option or decision.options[0]
        else:
            # Low confidence, might need human input
            if await self._should_escalate_to_human(decision):
                return await self._request_human_decision(decision)

            # Use learning to recommend alternative
            if self.learning and len(decision.options) > 1:
                # Try to pick best option based on experience
                best_option = decision.recommended_option or decision.options[0]
                for option in decision.options:
                    prob = self.learning.predict_success_probability(
                        action=option,
                        context=decision.context,
                    )
                    if prob > 0.5:
                        best_option = option
                        break
                chosen = best_option
            else:
                chosen = decision.recommended_option or decision.options[0]

        decision.decision_made = chosen
        decision.decided_at = datetime.now()
        self.decision_history.append(decision)

        logger.info(
            f"Autonomous decision: {decision.type.value} -> {chosen} "
            f"(confidence: {decision.confidence:.2f})"
        )

        return chosen

    async def _should_escalate_to_human(self, decision: Decision) -> bool:
        """
        Determine if decision should be escalated to human

        Based on:
        - Autonomy level
        - Decision confidence
        - Decision criticality
        - Past performance
        """
        if self.current_autonomy_level == AutonomyLevel.MANUAL:
            return True

        if self.current_autonomy_level == AutonomyLevel.AUTONOMOUS:
            return False

        # Supervised or semi-autonomous
        if decision.confidence < self.config.confidence_threshold:
            return True

        # Check decision criticality
        if decision.type == DecisionType.ESCALATION:
            return True

        # Check past performance for similar decisions
        if self.learning:
            if decision.recommended_option:
                success_prob = self.learning.predict_success_probability(
                    action=decision.recommended_option,
                    context=decision.context,
                )
                if success_prob < 0.4:
                    logger.info(
                        f"Escalating to human due to low predicted success: {success_prob:.2f}"
                    )
                    return True

        return False

    async def _request_human_decision(self, decision: Decision) -> str:
        """
        Request human input for a decision

        Args:
            decision: Decision requiring human input

        Returns:
            Human's chosen option
        """
        self.total_human_escalations += 1
        decision.requires_human = True

        logger.info(
            f"Escalating decision to human: {decision.description} "
            f"(confidence: {decision.confidence:.2f})"
        )

        # Add to pending and awaiting list
        if decision not in self.pending_decisions:
            self.pending_decisions.append(decision)
        self.awaiting_human_response.add(decision.id)

        # Call human callback if registered
        if self.human_callback:
            try:
                response = self.human_callback(decision)
                await self._receive_human_decision(decision.id, response)
                return response
            except Exception as e:
                logger.error(f"Error in human callback: {e}")

        # For now, use recommended option as fallback
        # In production, this would wait for actual human input
        fallback = decision.recommended_option or decision.options[0]
        logger.warning(f"No human response, using fallback: {fallback}")

        await self._receive_human_decision(decision.id, fallback)
        return fallback

    async def _receive_human_decision(
        self,
        decision_id: UUID,
        chosen_option: str,
    ) -> None:
        """
        Receive human decision response

        Args:
            decision_id: Decision ID
            chosen_option: Human's chosen option
        """
        # Find decision
        decision = None
        for d in self.pending_decisions:
            if d.id == decision_id:
                decision = d
                break

        if not decision:
            logger.warning(f"Decision {decision_id} not found")
            return

        # Record decision
        decision.decision_made = chosen_option
        decision.decided_at = datetime.now()

        # Remove from pending
        self.pending_decisions.remove(decision)
        self.awaiting_human_response.discard(decision_id)
        self.decision_history.append(decision)

        logger.info(f"Human decision received: {chosen_option}")

        # Learn from human decision
        if self.learning:
            await self.learning.record_experience(
                experience_type=ExperienceType.PLANNING,
                action=chosen_option,
                outcome=OutcomeType.SUCCESS,  # Will update based on actual outcome
                context=decision.context,
                strategy_used="human_decision",
            )

    async def _execute_tasks(self) -> None:
        """Execute queued tasks autonomously"""
        # Check if we can take more tasks
        if len(self.active_tasks) >= self.config.max_concurrent_tasks:
            return

        # Get tasks from queue
        while (
            self.task_queue and
            len(self.active_tasks) < self.config.max_concurrent_tasks
        ):
            task = self.task_queue.pop(0)

            # Check if task requires human approval
            if task.requires_human_approval:
                decision = Decision(
                    type=DecisionType.TASK_EXECUTION,
                    description=f"Approve execution of task: {task.name}",
                    options=["approve", "reject", "defer"],
                    recommended_option="approve",
                    confidence=0.6,
                    context={"task_id": str(task.id), "task_name": task.name},
                    requires_human=True,
                )

                response = await self._request_human_decision(decision)
                if response != "approve":
                    logger.info(f"Task {task.name} not approved by human")
                    continue

            # Execute task
            asyncio.create_task(self._execute_single_task(task))
            self.active_tasks[task.id] = task

    async def _execute_single_task(self, task: AutonomousTask) -> None:
        """
        Execute a single task with monitoring and recovery

        Args:
            task: Task to execute
        """
        task.status = "running"
        task.started_at = datetime.now()
        start_time = datetime.now()

        logger.info(f"Executing autonomous task: {task.name}")

        try:
            # Create checkpoint before execution
            if self.recovery:
                self.recovery.create_checkpoint(
                    name=f"before_task_{task.id}",
                    state_data={
                        "task_id": str(task.id),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            # Execute with retry and recovery
            if self.recovery:
                result = await self.recovery.execute_with_retry(
                    self._task_execution_logic,
                    task,
                    retry_config=task.retry_config,
                    circuit_breaker=f"task_{task.name}",
                )
            else:
                result = await self._task_execution_logic(task)

            # Success
            task.status = "completed"
            task.result = result
            task.completed_at = datetime.now()
            duration = (task.completed_at - task.started_at).total_seconds()

            logger.info(f"Task {task.name} completed in {duration:.2f}s")

            # Record experience
            if self.learning:
                await self.learning.record_experience(
                    experience_type=ExperienceType.TASK_EXECUTION,
                    action=task.name,
                    outcome=OutcomeType.SUCCESS,
                    duration=duration,
                    context={"goal": task.goal, "priority": task.priority},
                )

        except Exception as e:
            # Failure
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            duration = (task.completed_at - task.started_at).total_seconds()

            logger.error(f"Task {task.name} failed: {e}")

            # Record failure experience
            if self.learning:
                await self.learning.record_experience(
                    experience_type=ExperienceType.TASK_EXECUTION,
                    action=task.name,
                    outcome=OutcomeType.FAILURE,
                    duration=duration,
                    context={
                        "goal": task.goal,
                        "priority": task.priority,
                        "error": str(e),
                    },
                )

            # Try rollback if available
            if self.recovery:
                checkpoint_data = self.recovery.rollback_to_checkpoint(
                    f"before_task_{task.id}"
                )
                if checkpoint_data:
                    logger.info("Rolled back to checkpoint")

        finally:
            # Move to completed and remove from active
            self.completed_tasks.append(task)
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]

            # Record metric
            if self.monitoring:
                self.monitoring.record_metric(
                    MetricType.RESPONSE_TIME,
                    duration * 1000,  # Convert to milliseconds
                    metadata={"task_name": task.name},
                )

    async def _task_execution_logic(self, task: AutonomousTask) -> Any:
        """
        Core task execution logic

        This is a placeholder - would be replaced with actual task execution

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        # Simulate task execution
        await asyncio.sleep(0.5)

        # Placeholder result
        return {
            "task_id": str(task.id),
            "task_name": task.name,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }

    async def _adapt_autonomy_level(self) -> None:
        """Adapt autonomy level based on performance"""
        if self.total_autonomous_decisions < 20:
            return  # Not enough data

        # Calculate success rate
        if self.learning:
            summary = self.learning.get_learning_summary()
            success_rate = summary.get("success_rate", 0.5)
            avg_reward = summary.get("average_reward", 0.0)

            # Update performance score
            self.performance_score = 0.6 * success_rate + 0.4 * (avg_reward + 1) / 2

            # Adapt autonomy level based on performance
            if self.performance_score > 0.8:
                # High performance, increase autonomy
                if self.current_autonomy_level == AutonomyLevel.SUPERVISED:
                    self.current_autonomy_level = AutonomyLevel.SEMI_AUTONOMOUS
                    logger.info("Increased autonomy to SEMI_AUTONOMOUS")
                elif self.current_autonomy_level == AutonomyLevel.SEMI_AUTONOMOUS:
                    self.current_autonomy_level = AutonomyLevel.AUTONOMOUS
                    logger.info("Increased autonomy to AUTONOMOUS")

            elif self.performance_score < 0.4:
                # Low performance, decrease autonomy
                if self.current_autonomy_level == AutonomyLevel.AUTONOMOUS:
                    self.current_autonomy_level = AutonomyLevel.SEMI_AUTONOMOUS
                    logger.info("Decreased autonomy to SEMI_AUTONOMOUS")
                elif self.current_autonomy_level == AutonomyLevel.SEMI_AUTONOMOUS:
                    self.current_autonomy_level = AutonomyLevel.SUPERVISED
                    logger.info("Decreased autonomy to SUPERVISED")

    def add_task(self, task: AutonomousTask) -> None:
        """Add task to execution queue"""
        self.task_queue.append(task)
        logger.info(f"Added task to queue: {task.name}")

    def register_human_callback(
        self,
        callback: Callable[[Decision], str],
    ) -> None:
        """Register callback for human decisions"""
        self.human_callback = callback
        logger.info("Human decision callback registered")

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive autonomous controller status"""
        status = {
            "agent_id": str(self.agent_id),
            "running": self.running,
            "autonomy_level": self.current_autonomy_level.value,
            "performance_score": self.performance_score,
            "task_queue_size": len(self.task_queue),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "pending_decisions": len(self.pending_decisions),
            "total_decisions": self.total_autonomous_decisions,
            "human_escalations": self.total_human_escalations,
            "escalation_rate": (
                self.total_human_escalations / self.total_autonomous_decisions
                if self.total_autonomous_decisions > 0
                else 0.0
            ),
        }

        # Add monitoring status
        if self.monitoring:
            status["monitoring"] = self.monitoring.get_monitoring_summary()
            status["health_status"] = self.monitoring.get_health_status().value

        # Add recovery status
        if self.recovery:
            status["recovery"] = self.recovery.get_recovery_statistics()

        # Add learning status
        if self.learning:
            status["learning"] = self.learning.get_learning_summary()

        return status
