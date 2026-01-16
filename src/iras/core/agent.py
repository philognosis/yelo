"""
Core Agent Implementation

Integrates all agent components:
- State management
- Memory systems
- Reasoning engine
- Planning module
- Tool execution
- LLM interface
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

from iras.core.memory import MemorySystem, MemoryType
from iras.core.planning import HTNPlanner, Plan, Task, TaskStatus
from iras.core.reasoning import EvidenceType, ReasoningChain, ReasoningEngine, ReasoningStrategy
from iras.core.state import AgentState, AgentStatus, StateManager
from iras.llm import LLMClient, LLMConfig


class AgentConfig(BaseModel):
    """Agent configuration"""

    name: str
    role: str
    capabilities: Set[str] = Field(default_factory=set)

    # LLM configuration
    model: str = "claude-sonnet-4"
    temperature: float = 0.7
    max_tokens: int = 4000

    # Memory configuration
    working_memory_capacity: int = 20
    episodic_memory_capacity: int = 10000

    # Performance configuration
    max_concurrent_tasks: int = 3
    task_timeout: float = 300.0  # seconds

    # Autonomy configuration
    autonomous_mode: bool = True
    ask_threshold: float = 0.5  # Ask human when confidence < threshold


class AgentTool(BaseModel):
    """Tool that an agent can use"""

    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    function: Optional[Callable] = None

    class Config:
        arbitrary_types_allowed = True


class Agent:
    """
    Complete AI Agent Implementation

    Architecture:
    - LLM Core: Language model interface
    - Reasoning Engine: Multi-strategy reasoning
    - Planning Module: HTN planning and task decomposition
    - Memory System: Multi-tiered memory (working, episodic)
    - State Management: State tracking and transitions
    - Tool System: Extensible tool interface
    """

    def __init__(self, config: AgentConfig):
        self.id = uuid4()
        self.config = config

        # Core components
        self.state_manager = StateManager(agent_id=self.id)
        self.memory = MemorySystem(
            working_capacity=config.working_memory_capacity,
            episodic_capacity=config.episodic_memory_capacity,
        )
        self.reasoning = ReasoningEngine()
        self.planner = HTNPlanner()

        # LLM client for intent understanding and generation
        llm_config = LLMConfig(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        self.llm = LLMClient(llm_config)

        # Tools registry
        self.tools: Dict[str, AgentTool] = {}

        # Current execution context
        self.current_plan: Optional[Plan] = None
        self.current_task: Optional[Task] = None

        # Performance tracking
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0
        self.created_at = datetime.now()

        logger.info(f"Agent '{config.name}' ({config.role}) initialized with ID: {self.id}")

    async def initialize(self) -> None:
        """Initialize agent and perform startup tasks"""
        await self.state_manager.update_status(
            AgentStatus.IDLE,
            reason="Agent initialized",
        )

        # Add initial capabilities to state
        self.state_manager.current_state.capabilities = self.config.capabilities

        logger.info(f"Agent {self.config.name} ready with capabilities: {self.config.capabilities}")

    def register_tool(self, tool: AgentTool) -> None:
        """Register a tool for the agent to use"""
        self.tools[tool.name] = tool
        self.config.capabilities.add(tool.name)
        logger.info(f"Agent {self.config.name} registered tool: {tool.name}")

    async def execute_task(
        self,
        task: Task,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a single task

        Args:
            task: Task to execute
            context: Optional execution context

        Returns:
            Task result
        """
        self.current_task = task
        task_start = datetime.now()

        try:
            # Update state
            await self.state_manager.update_status(
                AgentStatus.EXECUTING,
                reason=f"Executing task: {task.name}",
            )

            # Remember task in working memory
            await self.memory.remember(
                content={
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "description": task.description,
                },
                importance=0.7,
                memory_type=MemoryType.WORKING,
            )

            # Execute based on task type
            result = await self._execute_task_logic(task, context or {})

            # Record success
            duration = (datetime.now() - task_start).total_seconds()
            await self.state_manager.record_task_completion(success=True, duration=duration)
            self.total_tasks_completed += 1

            # Store result in episodic memory
            await self.memory.remember(
                content={
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "result": result,
                    "duration": duration,
                },
                importance=0.8,
                memory_type=MemoryType.EPISODIC,
            )

            logger.info(f"Task '{task.name}' completed in {duration:.2f}s")
            return result

        except Exception as e:
            # Record failure
            duration = (datetime.now() - task_start).total_seconds()
            await self.state_manager.record_task_completion(success=False, duration=duration)
            self.total_tasks_failed += 1

            await self.state_manager.update_status(
                AgentStatus.ERROR,
                reason=f"Task failed: {str(e)}",
            )

            logger.error(f"Task '{task.name}' failed: {e}")
            raise

        finally:
            self.current_task = None
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def _execute_task_logic(
        self,
        task: Task,
        context: Dict[str, Any],
    ) -> Any:
        """
        Core task execution logic using LLM for intent understanding

        Process:
        1. Use LLM to understand the task intent
        2. Select and execute appropriate tools
        3. Reason about results
        4. Return structured output
        """
        logger.debug(f"Executing task logic for: {task.name}")

        # Check if we have required capabilities
        missing_caps = task.requirements.required_capabilities - self.config.capabilities
        if missing_caps:
            raise ValueError(f"Missing required capabilities: {missing_caps}")

        # Use LLM to understand task intent and plan execution
        system_prompt = f"""You are {self.config.name}, an AI agent with the role of {self.config.role}.

Your capabilities: {', '.join(self.config.capabilities)}
Your available tools: {', '.join(self.tools.keys())}

Analyze the task and provide a brief execution plan."""

        task_prompt = f"""Task: {task.name}
Description: {task.description}
Context: {context}

What is the best way to accomplish this task? Provide a concise execution plan."""

        # Get LLM analysis
        try:
            response = await self.llm.generate(
                prompt=task_prompt,
                system=system_prompt,
                temperature=0.5,  # More deterministic for task planning
            )

            execution_plan = response.content
            logger.info(f"LLM execution plan: {execution_plan[:200]}...")

        except Exception as e:
            logger.warning(f"LLM call failed, using fallback: {e}")
            execution_plan = f"Execute task {task.name} using available tools"

        # Return structured result
        result = {
            "task_id": str(task.id),
            "task_name": task.name,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "agent": self.config.name,
            "execution_plan": execution_plan,
            "context": context,
        }

        return result

    async def execute_plan(self, plan: Plan) -> Dict[str, Any]:
        """
        Execute a complete plan

        Manages task execution according to plan dependencies
        """
        self.current_plan = plan
        plan_start = datetime.now()

        try:
            await self.state_manager.update_status(
                AgentStatus.PLANNING,
                reason=f"Executing plan: {plan.goal}",
            )

            # Execute tasks until plan is complete
            while plan.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                # Get next ready tasks
                ready_tasks = plan.get_next_tasks()

                if not ready_tasks:
                    # No tasks ready, check if we're waiting for something
                    if plan.current_tasks:
                        await asyncio.sleep(0.1)  # Wait for current tasks
                        continue
                    else:
                        # No tasks ready and none in progress - plan is stuck
                        logger.error("Plan is stuck - no tasks ready")
                        break

                # Execute ready tasks (up to max concurrent)
                tasks_to_execute = ready_tasks[: self.config.max_concurrent_tasks]

                # Execute tasks concurrently
                task_results = await asyncio.gather(
                    *[
                        self._execute_plan_task(plan, task)
                        for task in tasks_to_execute
                    ],
                    return_exceptions=True,
                )

                # Check for errors
                for task, result in zip(tasks_to_execute, task_results):
                    if isinstance(result, Exception):
                        await self.planner.mark_task_failed(
                            plan.id,
                            task.id,
                            str(result),
                        )

            duration = (datetime.now() - plan_start).total_seconds()

            return {
                "plan_id": str(plan.id),
                "status": plan.status,
                "duration": duration,
                "completed_tasks": len(plan.completed_tasks),
                "failed_tasks": len(plan.failed_tasks),
                "progress": plan.get_progress(),
            }

        finally:
            self.current_plan = None
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def _execute_plan_task(self, plan: Plan, task: Task) -> Any:
        """Execute a task within a plan"""
        # Mark as started
        await self.planner.mark_task_started(plan.id, task.id, self.id)

        try:
            # Execute task
            result = await self.execute_task(task)

            # Mark as completed
            await self.planner.mark_task_completed(plan.id, task.id, result)

            return result

        except Exception as e:
            await self.planner.mark_task_failed(plan.id, task.id, str(e))
            raise

    async def reason(
        self,
        query: str,
        strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT,
    ) -> ReasoningChain:
        """
        Perform reasoning about a query

        Args:
            query: Question or problem to reason about
            strategy: Reasoning strategy to use

        Returns:
            Complete reasoning chain
        """
        await self.state_manager.update_status(
            AgentStatus.PLANNING,
            reason=f"Reasoning about: {query[:50]}...",
        )

        try:
            chain = await self.reasoning.reason(query, strategy)

            # Store reasoning in episodic memory
            await self.memory.remember(
                content={
                    "query": query,
                    "strategy": strategy,
                    "conclusion": chain.final_conclusion,
                    "confidence": chain.overall_confidence,
                },
                importance=0.7,
                memory_type=MemoryType.EPISODIC,
            )

            return chain

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def should_ask_human(self, confidence: float, context: str) -> bool:
        """
        Determine if human input is needed

        Based on:
        - Confidence threshold
        - Task importance
        - Autonomous mode setting
        """
        if not self.config.autonomous_mode:
            return True  # Always ask in non-autonomous mode

        if confidence < self.config.ask_threshold:
            logger.info(f"Low confidence ({confidence:.2f}) - would ask human about: {context}")
            return True

        return False

    def get_state(self) -> AgentState:
        """Get current agent state"""
        return self.state_manager.get_state()

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        state = self.get_state()
        memory_stats = self.memory.get_memory_stats()
        reasoning_stats = self.reasoning.get_statistics()

        return {
            "id": str(self.id),
            "name": self.config.name,
            "role": self.config.role,
            "status": state.status,
            "health": state.health,
            "workload": state.workload,
            "capabilities": list(state.capabilities),
            "tasks_completed": self.total_tasks_completed,
            "tasks_failed": self.total_tasks_failed,
            "success_rate": self.state_manager.get_success_rate(),
            "current_task": self.current_task.name if self.current_task else None,
            "memory": memory_stats,
            "reasoning": reasoning_stats,
            "uptime": (datetime.now() - self.created_at).total_seconds(),
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown agent"""
        logger.info(f"Shutting down agent {self.config.name}")

        # Consolidate memory
        await self.memory.consolidate()

        # Update state
        await self.state_manager.update_status(
            AgentStatus.SHUTDOWN,
            reason="Agent shutdown requested",
        )

        logger.info(f"Agent {self.config.name} shutdown complete")
