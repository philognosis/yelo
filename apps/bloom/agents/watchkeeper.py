"""
Watchkeeper Agent - Evaluation Cycle Orchestrator

The Watchkeeper monitors evaluation cycles and orchestrates state transitions.

Responsibilities:
- Monitors evaluation deadlines and triggers state transitions
- Manages cron-style scheduling for different cohorts (L6, L5, etc.)
- Orchestrates workflow using IRAS HTN Planner
- Coordinates other agents to complete evaluation phases
- Tracks overall system health and evaluation progress

Design Pattern: State Machine Controller + Event-Driven Scheduler
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from loguru import logger

from apps.bloom.models.evaluation import (
    Evaluation,
    EvaluationPhase,
    EvaluationState,
)
from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.memory import MemoryType
from iras.core.planning import HTNPlanner, Plan, Task, TaskRequirements, TaskStatus
from iras.core.state import AgentStatus
from iras.databases.document_store import DocumentStore
from iras.databases.timeseries_store import TimeSeriesStore


class CohortSchedule:
    """Schedule configuration for evaluation cohorts"""

    def __init__(
        self,
        cohort_name: str,
        level: str,
        cycle_start_day: int,  # Day of month
        peer_selection_days: int = 7,
        peer_feedback_days: int = 14,
        self_eval_days: int = 14,
        manager_eval_days: int = 14,
        calibration_offset_days: int = 35,
    ):
        self.cohort_name = cohort_name
        self.level = level
        self.cycle_start_day = cycle_start_day
        self.peer_selection_days = peer_selection_days
        self.peer_feedback_days = peer_feedback_days
        self.self_eval_days = self_eval_days
        self.manager_eval_days = manager_eval_days
        self.calibration_offset_days = calibration_offset_days


class Watchkeeper(Agent):
    """
    Orchestrator agent for evaluation workflow

    The Watchkeeper is the "brain" of the Bloom system, coordinating all
    evaluation activities and ensuring timely progression through phases.

    Capabilities:
    - Evaluation lifecycle management
    - Deadline monitoring and enforcement
    - Multi-cohort scheduling
    - Workflow orchestration via HTN planning
    - State transition coordination
    - System health monitoring
    """

    def __init__(
        self,
        name: str = "Watchkeeper",
        document_store: Optional[DocumentStore] = None,
        timeseries_store: Optional[TimeSeriesStore] = None,
    ):
        config = AgentConfig(
            name=name,
            role="orchestrator",
            capabilities={
                "evaluation_orchestration",
                "deadline_monitoring",
                "state_management",
                "workflow_planning",
                "cohort_scheduling",
                "health_monitoring",
            },
            temperature=0.1,  # Deterministic for orchestration
            max_tokens=3000,
            autonomous_mode=True,
        )
        super().__init__(config)

        # Database connections
        self.document_store = document_store or DocumentStore()
        self.timeseries_store = timeseries_store or TimeSeriesStore()

        # Cohort schedules
        self.cohort_schedules: Dict[str, CohortSchedule] = {}
        self._initialize_default_cohorts()

        # Active evaluations tracker
        self.active_evaluations: Set[UUID] = set()

        # Monitoring state
        self.last_check_time = datetime.now()
        self.check_interval = timedelta(hours=1)  # Check every hour

        # Register tools
        self._register_orchestration_tools()

        logger.info(f"Watchkeeper '{name}' initialized with {len(self.cohort_schedules)} cohorts")

    def _initialize_default_cohorts(self) -> None:
        """Initialize default cohort schedules"""
        # L6+ (Senior leadership) - Quarterly on 1st
        self.cohort_schedules["L6_Q"] = CohortSchedule(
            cohort_name="L6 Quarterly",
            level="L6+",
            cycle_start_day=1,
            peer_selection_days=10,
            peer_feedback_days=21,
            self_eval_days=21,
            manager_eval_days=21,
            calibration_offset_days=60,
        )

        # L5 (Directors) - Quarterly on 10th
        self.cohort_schedules["L5_Q"] = CohortSchedule(
            cohort_name="L5 Quarterly",
            level="L5",
            cycle_start_day=10,
            peer_selection_days=7,
            peer_feedback_days=14,
            self_eval_days=14,
            manager_eval_days=14,
            calibration_offset_days=45,
        )

        # L4 (Managers) - Quarterly on 15th
        self.cohort_schedules["L4_Q"] = CohortSchedule(
            cohort_name="L4 Quarterly",
            level="L4",
            cycle_start_day=15,
            peer_selection_days=7,
            peer_feedback_days=14,
            self_eval_days=14,
            manager_eval_days=14,
            calibration_offset_days=40,
        )

        # L3 and below (ICs) - Quarterly on 20th
        self.cohort_schedules["IC_Q"] = CohortSchedule(
            cohort_name="IC Quarterly",
            level="L3-",
            cycle_start_day=20,
            peer_selection_days=7,
            peer_feedback_days=14,
            self_eval_days=14,
            manager_eval_days=14,
            calibration_offset_days=35,
        )

    def _register_orchestration_tools(self) -> None:
        """Register Watchkeeper-specific tools"""
        self.register_tool(
            AgentTool(
                name="start_evaluation_cycle",
                description="Start a new evaluation cycle for a cohort",
                parameters={
                    "cohort_id": {"type": "string"},
                    "cycle_name": {"type": "string"},
                },
                function=self.start_evaluation_cycle,
            )
        )

        self.register_tool(
            AgentTool(
                name="check_deadlines",
                description="Check all evaluations for deadline violations",
                parameters={},
                function=self.check_deadlines,
            )
        )

        self.register_tool(
            AgentTool(
                name="transition_evaluation_state",
                description="Transition evaluation to next state",
                parameters={
                    "evaluation_id": {"type": "string"},
                    "new_state": {"type": "string"},
                },
                function=self.transition_evaluation_state,
            )
        )

    async def start_evaluation_cycle(
        self,
        cohort_id: str,
        cycle_name: str,
        employee_ids: List[UUID],
    ) -> Dict[str, Any]:
        """
        Start a new evaluation cycle for a cohort

        Args:
            cohort_id: Cohort identifier
            cycle_name: Cycle name (e.g., "Q4 2024")
            employee_ids: List of employees to evaluate

        Returns:
            Cycle initiation results
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Starting evaluation cycle: {cycle_name}",
        )

        try:
            schedule = self.cohort_schedules.get(cohort_id)
            if not schedule:
                raise ValueError(f"Unknown cohort: {cohort_id}")

            # Create HTN plan for cycle initiation
            plan = await self.planner.create_plan(
                goal=f"Initialize {cycle_name} for {len(employee_ids)} employees",
                context={"cohort_id": cohort_id, "cycle_name": cycle_name},
            )

            # Task 1: Create evaluation records
            create_evals_task = Task(
                name="Create evaluation records",
                description=f"Create {len(employee_ids)} evaluation records",
                requirements=TaskRequirements(
                    required_capabilities={"evaluation_orchestration"},
                ),
            )
            await self.planner.add_task(plan.id, create_evals_task)

            # Task 2: Initialize Context Miner for peer suggestions
            init_context_task = Task(
                name="Initialize peer suggestions",
                description="Trigger ContextMiner to generate peer suggestions",
                requirements=TaskRequirements(
                    required_capabilities={"evaluation_orchestration"},
                ),
            )
            await self.planner.add_task(
                plan.id,
                init_context_task,
                dependencies=[create_evals_task.id],
            )

            # Task 3: Send notifications
            notify_task = Task(
                name="Send cycle start notifications",
                description="Notify employees and managers",
                requirements=TaskRequirements(
                    required_capabilities={"evaluation_orchestration"},
                ),
            )
            await self.planner.add_task(
                plan.id,
                notify_task,
                dependencies=[init_context_task.id],
            )

            # Execute plan
            created_evaluations = []
            base_time = datetime.now()

            for employee_id in employee_ids:
                # Create evaluation record
                evaluation = Evaluation(
                    employee_id=employee_id,
                    manager_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
                    cycle_name=cycle_name,
                    current_phase=EvaluationPhase.CONTEXT_PEER_SELECTION,
                    current_state=EvaluationState.CYCLE_STARTED,
                    peer_selection_deadline=base_time + timedelta(days=schedule.peer_selection_days),
                    peer_feedback_deadline=base_time + timedelta(
                        days=schedule.peer_selection_days + schedule.peer_feedback_days
                    ),
                    self_eval_deadline=base_time + timedelta(
                        days=schedule.peer_selection_days + schedule.self_eval_days
                    ),
                    manager_eval_deadline=base_time + timedelta(
                        days=schedule.peer_selection_days + schedule.manager_eval_days
                    ),
                    calibration_date=base_time + timedelta(days=schedule.calibration_offset_days),
                )

                # Store in document store
                eval_dict = evaluation.model_dump(mode="json")
                eval_id = await self.document_store.insert(
                    collection="evaluations",
                    document=eval_dict,
                    doc_id=str(evaluation.id),
                )

                self.active_evaluations.add(evaluation.id)
                created_evaluations.append(evaluation.id)

                # Record metric
                await self.timeseries_store.write_point(
                    metric="evaluations.created",
                    value=1.0,
                    tags={"cohort": cohort_id, "cycle": cycle_name},
                )

            # Remember in memory
            await self.memory.remember(
                content={
                    "action": "cycle_started",
                    "cohort": cohort_id,
                    "cycle": cycle_name,
                    "count": len(created_evaluations),
                },
                importance=0.9,
                memory_type=MemoryType.EPISODIC,
            )

            logger.info(
                f"Started evaluation cycle '{cycle_name}' for cohort '{cohort_id}': "
                f"{len(created_evaluations)} evaluations created"
            )

            return {
                "success": True,
                "cohort_id": cohort_id,
                "cycle_name": cycle_name,
                "evaluations_created": len(created_evaluations),
                "evaluation_ids": [str(eid) for eid in created_evaluations],
                "deadlines": {
                    "peer_selection": (base_time + timedelta(days=schedule.peer_selection_days)).isoformat(),
                    "peer_feedback": (
                        base_time + timedelta(days=schedule.peer_selection_days + schedule.peer_feedback_days)
                    ).isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Failed to start evaluation cycle: {e}")
            raise

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def check_deadlines(self) -> Dict[str, Any]:
        """
        Check all active evaluations for deadline violations

        Returns:
            Summary of deadline checks and violations
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason="Checking evaluation deadlines",
        )

        try:
            now = datetime.now()
            violations = {
                "peer_selection": [],
                "peer_feedback": [],
                "self_eval": [],
                "manager_eval": [],
            }

            # Query all active evaluations
            evaluations = await self.document_store.find(
                collection="evaluations",
                query={"current_phase": {"$ne": "completed"}},
            )

            for eval_doc in evaluations:
                eval_id = eval_doc["_id"]

                # Check each deadline type
                for deadline_type in ["peer_selection", "peer_feedback", "self_eval", "manager_eval"]:
                    deadline_field = f"{deadline_type}_deadline"
                    deadline_str = eval_doc.get(deadline_field)

                    if deadline_str:
                        deadline = datetime.fromisoformat(deadline_str)
                        if now > deadline:
                            violations[deadline_type].append(
                                {
                                    "evaluation_id": eval_id,
                                    "employee_id": eval_doc["employee_id"],
                                    "deadline": deadline.isoformat(),
                                    "overdue_hours": (now - deadline).total_seconds() / 3600,
                                }
                            )

            # Record metrics
            total_violations = sum(len(v) for v in violations.values())
            await self.timeseries_store.write_point(
                metric="evaluations.deadline_violations",
                value=float(total_violations),
                tags={"check_time": now.isoformat()},
            )

            # Remember check in memory
            await self.memory.remember(
                content={
                    "action": "deadline_check",
                    "total_violations": total_violations,
                    "timestamp": now.isoformat(),
                },
                importance=0.6,
                memory_type=MemoryType.EPISODIC,
            )

            self.last_check_time = now

            logger.info(f"Deadline check complete: {total_violations} violations found")

            return {
                "check_time": now.isoformat(),
                "evaluations_checked": len(evaluations),
                "total_violations": total_violations,
                "violations": violations,
            }

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def transition_evaluation_state(
        self,
        evaluation_id: UUID,
        new_state: EvaluationState,
        new_phase: Optional[EvaluationPhase] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transition an evaluation to a new state

        Args:
            evaluation_id: Evaluation to transition
            new_state: Target state
            new_phase: Optional new phase
            reason: Reason for transition

        Returns:
            Transition result
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Transitioning evaluation {evaluation_id}",
        )

        try:
            # Load evaluation
            eval_doc = await self.document_store.find_by_id(
                collection="evaluations",
                doc_id=str(evaluation_id),
            )

            if not eval_doc:
                raise ValueError(f"Evaluation not found: {evaluation_id}")

            old_state = eval_doc["current_state"]
            old_phase = eval_doc["current_phase"]

            # Update state
            await self.document_store.update(
                collection="evaluations",
                query={"_id": str(evaluation_id)},
                update={
                    "$set": {
                        "current_state": new_state,
                        "current_phase": new_phase or old_phase,
                        "updated_at": datetime.now().isoformat(),
                    },
                    "$push": {
                        "state_history": {
                            "from_state": old_state,
                            "to_state": new_state,
                            "from_phase": old_phase,
                            "to_phase": new_phase or old_phase,
                            "timestamp": datetime.now().isoformat(),
                            "reason": reason,
                        }
                    },
                },
            )

            # Record metric
            await self.timeseries_store.write_point(
                metric="evaluations.state_transitions",
                value=1.0,
                tags={
                    "from_state": old_state,
                    "to_state": new_state,
                    "evaluation_id": str(evaluation_id),
                },
            )

            logger.info(
                f"Evaluation {evaluation_id} transitioned: {old_state} -> {new_state}"
            )

            return {
                "success": True,
                "evaluation_id": str(evaluation_id),
                "old_state": old_state,
                "new_state": new_state,
                "old_phase": old_phase,
                "new_phase": new_phase or old_phase,
                "reason": reason,
            }

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def monitor_system_health(self) -> Dict[str, Any]:
        """
        Monitor overall system health and evaluation progress

        Returns:
            System health metrics
        """
        # Get active evaluations count
        active_evals = await self.document_store.count(
            collection="evaluations",
            query={"current_phase": {"$ne": "completed"}},
        )

        # Get evaluations by phase
        phase_distribution = {}
        for phase in EvaluationPhase:
            count = await self.document_store.count(
                collection="evaluations",
                query={"current_phase": phase.value},
            )
            if count > 0:
                phase_distribution[phase.value] = count

        # Check deadline compliance
        deadline_check = await self.check_deadlines()

        health_score = 1.0
        if deadline_check["total_violations"] > 0:
            health_score -= min(0.5, deadline_check["total_violations"] * 0.05)

        # Record health metric
        await self.timeseries_store.write_point(
            metric="system.health_score",
            value=health_score,
        )

        return {
            "health_score": health_score,
            "active_evaluations": active_evals,
            "phase_distribution": phase_distribution,
            "deadline_violations": deadline_check["total_violations"],
            "last_check": self.last_check_time.isoformat(),
        }

    async def run_orchestration_loop(self, interval_seconds: int = 3600) -> None:
        """
        Main orchestration loop (run continuously)

        Args:
            interval_seconds: Check interval in seconds
        """
        logger.info(f"Starting orchestration loop with {interval_seconds}s interval")

        while True:
            try:
                # Check deadlines
                await self.check_deadlines()

                # Monitor system health
                health = await self.monitor_system_health()
                logger.info(f"System health: {health['health_score']:.2f}")

                # Sleep until next check
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                await asyncio.sleep(60)  # Short sleep on error
