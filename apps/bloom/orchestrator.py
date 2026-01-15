"""
Bloom Orchestrator

Main coordinator for the Bloom evaluation system.
Manages the multi-agent swarm and orchestrates the evaluation workflow.

Built on top of IRAS (Intelligent Research & Analysis Swarm) framework.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from loguru import logger

from iras.autonomous import AutonomousController, AutonomyLevel
from iras.communication import BlackboardSystem, ContractNetProtocol, PubSubProtocol
from iras.core import AgentState, AgentStatus
from iras.databases import DocumentStore, GraphStore, TimeSeriesStore, VectorStore
from iras.math import adaptive_load_balance
from iras.orchestration import Coordinator as IRASCoordinator

from bloom.agents import (
    BloomAnalyst,
    Chaser,
    ContextMiner,
    Gatekeeper,
    Scribe,
    Watchkeeper,
)
from bloom.models import (
    Employee,
    Evaluation,
    EvaluationPhase,
    EvaluationState,
    ManagerEvaluation,
    PeerFeedback,
    Person,
    SelfEvaluation,
)
from bloom.workflows import EvaluationStateMachine, PhaseHandlerFactory


class BloomConfig:
    """Bloom orchestrator configuration"""

    def __init__(
        self,
        # Agent counts
        num_scribes: int = 2,
        num_context_miners: int = 1,
        num_chasers: int = 1,
        # Features
        enable_autonomous_mode: bool = True,
        enable_rag: bool = True,
        enable_voice_synthesis: bool = True,
        # Deadlines (in days)
        peer_selection_deadline_days: int = 7,
        peer_feedback_deadline_days: int = 14,
        self_eval_deadline_days: int = 14,
        manager_eval_deadline_days: int = 21,
        calibration_days: int = 7,
        # Notifications
        notification_channels: List[str] = None,
        slack_enabled: bool = True,
        email_enabled: bool = True,
        # Database
        use_production_databases: bool = False,
        # Advanced
        max_concurrent_evaluations: int = 100,
        health_check_interval_minutes: int = 5,
    ):
        self.num_scribes = num_scribes
        self.num_context_miners = num_context_miners
        self.num_chasers = num_chasers

        self.enable_autonomous_mode = enable_autonomous_mode
        self.enable_rag = enable_rag
        self.enable_voice_synthesis = enable_voice_synthesis

        self.peer_selection_deadline_days = peer_selection_deadline_days
        self.peer_feedback_deadline_days = peer_feedback_deadline_days
        self.self_eval_deadline_days = self_eval_deadline_days
        self.manager_eval_deadline_days = manager_eval_deadline_days
        self.calibration_days = calibration_days

        self.notification_channels = notification_channels or ["slack", "email", "in_app"]
        self.slack_enabled = slack_enabled
        self.email_enabled = email_enabled

        self.use_production_databases = use_production_databases

        self.max_concurrent_evaluations = max_concurrent_evaluations
        self.health_check_interval_minutes = health_check_interval_minutes


class BloomOrchestrator:
    """
    Main orchestrator for the Bloom evaluation system

    Manages:
    - Multi-agent swarm (Watchkeeper, Scribe, ContextMiner, Chaser, Gatekeeper, Analyst)
    - Evaluation workflow state machine
    - Database integrations
    - Communication protocols
    - Autonomous operation

    Architecture:
        Watchkeeper (1) - Monitors and triggers cycles
        ContextMiner (1+) - Gathers context and suggests peers
        Scribe (2+) - AI synthesis and draft generation
        Chaser (1+) - Deadline enforcement
        Gatekeeper (1) - Security and RBAC
        Analyst (1) - Metrics and calibration
    """

    def __init__(self, config: Optional[BloomConfig] = None):
        """
        Initialize Bloom orchestrator

        Args:
            config: Orchestrator configuration
        """
        self.config = config or BloomConfig()
        self.id = uuid4()
        self.created_at = datetime.now()

        # Agents
        self.watchkeeper: Optional[Watchkeeper] = None
        self.context_miners: List[ContextMiner] = []
        self.scribes: List[Scribe] = []
        self.chasers: List[Chaser] = []
        self.gatekeeper: Optional[Gatekeeper] = None
        self.analyst: Optional[BloomAnalyst] = None

        # Databases
        self.document_store: Optional[DocumentStore] = None
        self.vector_store: Optional[VectorStore] = None
        self.graph_store: Optional[GraphStore] = None
        self.timeseries_store: Optional[TimeSeriesStore] = None

        # Communication
        self.blackboard: Optional[BlackboardSystem] = None
        self.contract_net: Optional[ContractNetProtocol] = None
        self.pubsub: Optional[PubSubProtocol] = None

        # Workflow
        self.state_machine: Optional[EvaluationStateMachine] = None
        self.phase_handlers: Optional[PhaseHandlerFactory] = None

        # Autonomous controllers
        self.autonomous_controllers: Dict[UUID, AutonomousController] = {}

        # Tracking
        self.active_evaluations: Dict[UUID, Evaluation] = {}
        self.is_running = False
        self.background_tasks: Set[asyncio.Task] = set()

        logger.info(f"Bloom orchestrator {self.id} created")

    async def initialize(self) -> None:
        """Initialize all systems and agents"""
        logger.info("Initializing Bloom orchestrator...")

        try:
            # Initialize databases
            await self._initialize_databases()

            # Initialize communication protocols
            await self._initialize_communication()

            # Initialize workflow systems
            await self._initialize_workflow()

            # Initialize agents
            await self._initialize_agents()

            # Initialize autonomous controllers
            if self.config.enable_autonomous_mode:
                await self._initialize_autonomous_controllers()

            # Start background tasks
            await self._start_background_tasks()

            self.is_running = True
            logger.info("Bloom orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Bloom orchestrator: {e}")
            raise

    async def _initialize_databases(self) -> None:
        """Initialize all database systems"""
        logger.info("Initializing databases...")

        # Document store for evaluations and employee data
        self.document_store = DocumentStore()

        # Vector store for RAG (embeddings of feedback, docs)
        self.vector_store = VectorStore(embedding_dim=384)

        # Graph store for org relationships and peer networks
        self.graph_store = GraphStore(directed=True)

        # Time-series store for metrics and trends
        self.timeseries_store = TimeSeriesStore()

        # Create indexes
        await self.document_store.create_index("evaluations", "employee_id")
        await self.document_store.create_index("evaluations", "cycle_name")
        await self.document_store.create_index("evaluations", "current_state")
        await self.document_store.create_index("employees", "email")

        logger.info("Databases initialized")

    async def _initialize_communication(self) -> None:
        """Initialize communication protocols"""
        logger.info("Initializing communication protocols...")

        # Blackboard for shared state
        self.blackboard = BlackboardSystem()

        # Contract Net for task allocation
        self.contract_net = ContractNetProtocol()

        # Pub/Sub for events
        self.pubsub = PubSubProtocol()

        # Set up subscriptions
        await self.pubsub.subscribe("evaluations/#", self.id)
        await self.pubsub.subscribe("deadlines/#", self.id)
        await self.pubsub.subscribe("notifications/#", self.id)

        logger.info("Communication protocols initialized")

    async def _initialize_workflow(self) -> None:
        """Initialize workflow systems"""
        logger.info("Initializing workflow systems...")

        # State machine
        self.state_machine = EvaluationStateMachine(
            document_store=self.document_store,
            pubsub=self.pubsub,
        )

        # Phase handlers
        self.phase_handlers = PhaseHandlerFactory(
            document_store=self.document_store,
            blackboard=self.blackboard,
            pubsub=self.pubsub,
        )

        logger.info("Workflow systems initialized")

    async def _initialize_agents(self) -> None:
        """Initialize all agents"""
        logger.info("Initializing agents...")

        # Watchkeeper (orchestrator)
        self.watchkeeper = Watchkeeper(
            document_store=self.document_store,
            pubsub=self.pubsub,
        )
        await self.watchkeeper.initialize()
        logger.info("Watchkeeper initialized")

        # Context Miners
        for i in range(self.config.num_context_miners):
            miner = ContextMiner(
                graph_store=self.graph_store,
                document_store=self.document_store,
            )
            await miner.initialize()
            self.context_miners.append(miner)
        logger.info(f"Initialized {len(self.context_miners)} context miners")

        # Scribes (AI synthesis)
        for i in range(self.config.num_scribes):
            scribe = Scribe(
                vector_store=self.vector_store,
                document_store=self.document_store,
                enable_rag=self.config.enable_rag,
            )
            await scribe.initialize()
            self.scribes.append(scribe)
        logger.info(f"Initialized {len(self.scribes)} scribes")

        # Chasers (deadline enforcement)
        for i in range(self.config.num_chasers):
            chaser = Chaser(
                document_store=self.document_store,
                timeseries_store=self.timeseries_store,
                notification_channels=self.config.notification_channels,
            )
            await chaser.initialize()
            self.chasers.append(chaser)
        logger.info(f"Initialized {len(self.chasers)} chasers")

        # Gatekeeper (security)
        self.gatekeeper = Gatekeeper(
            document_store=self.document_store,
        )
        await self.gatekeeper.initialize()
        logger.info("Gatekeeper initialized")

        # Analyst (metrics)
        self.analyst = BloomAnalyst(
            document_store=self.document_store,
            timeseries_store=self.timeseries_store,
        )
        await self.analyst.initialize()
        logger.info("Analyst initialized")

    async def _initialize_autonomous_controllers(self) -> None:
        """Initialize autonomous controllers for agents"""
        logger.info("Initializing autonomous controllers...")

        agents = [
            self.watchkeeper,
            *self.context_miners,
            *self.scribes,
            *self.chasers,
            self.gatekeeper,
            self.analyst,
        ]

        for agent in agents:
            if agent:
                controller = AutonomousController(
                    agent=agent,
                    autonomy_level=AutonomyLevel.AUTONOMOUS,
                    confidence_threshold=0.7,
                )
                self.autonomous_controllers[agent.id] = controller

        logger.info(f"Initialized {len(self.autonomous_controllers)} autonomous controllers")

    async def _start_background_tasks(self) -> None:
        """Start background monitoring tasks"""
        logger.info("Starting background tasks...")

        # Watchkeeper monitoring loop
        task1 = asyncio.create_task(self.watchkeeper.orchestrate())
        self.background_tasks.add(task1)

        # Chaser deadline monitoring
        for chaser in self.chasers:
            task = asyncio.create_task(chaser.monitor_deadlines())
            self.background_tasks.add(task)

        # Health monitoring
        task2 = asyncio.create_task(self._health_monitoring_loop())
        self.background_tasks.add(task2)

        logger.info(f"Started {len(self.background_tasks)} background tasks")

    async def _health_monitoring_loop(self) -> None:
        """Background task for health monitoring"""
        while self.is_running:
            try:
                await self.watchkeeper.monitor_system_health()
                await asyncio.sleep(self.config.health_check_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)

    async def start_evaluation_cycle(
        self,
        cycle_name: str,
        employees: List[Employee],
        start_date: Optional[datetime] = None,
    ) -> List[UUID]:
        """
        Start a new evaluation cycle for a cohort of employees

        Args:
            cycle_name: Name of the evaluation cycle
            employees: List of employees to evaluate
            start_date: When to start (default: now)

        Returns:
            List of created evaluation IDs
        """
        logger.info(f"Starting evaluation cycle '{cycle_name}' for {len(employees)} employees")

        evaluation_ids = []
        start_date = start_date or datetime.now()

        for employee in employees:
            try:
                # Create evaluation record
                evaluation = await self._create_evaluation(
                    employee=employee,
                    cycle_name=cycle_name,
                    start_date=start_date,
                )

                evaluation_ids.append(evaluation.id)
                self.active_evaluations[evaluation.id] = evaluation

                # Publish event
                await self.pubsub.publish(
                    topic=f"evaluations/{evaluation.id}/started",
                    content={
                        "evaluation_id": str(evaluation.id),
                        "employee_id": str(employee.person.id),
                        "cycle_name": cycle_name,
                    },
                    publisher_id=self.id,
                )

            except Exception as e:
                logger.error(f"Failed to create evaluation for {employee.person.name}: {e}")

        logger.info(f"Created {len(evaluation_ids)} evaluations for cycle '{cycle_name}'")
        return evaluation_ids

    async def _create_evaluation(
        self,
        employee: Employee,
        cycle_name: str,
        start_date: datetime,
    ) -> Evaluation:
        """Create a new evaluation with deadlines"""

        # Calculate deadlines
        peer_selection_deadline = start_date + timedelta(
            days=self.config.peer_selection_deadline_days
        )
        peer_feedback_deadline = peer_selection_deadline + timedelta(
            days=self.config.peer_feedback_deadline_days
        )
        self_eval_deadline = peer_selection_deadline + timedelta(
            days=self.config.self_eval_deadline_days
        )
        manager_eval_deadline = peer_feedback_deadline + timedelta(
            days=self.config.manager_eval_deadline_days
        )
        calibration_date = manager_eval_deadline + timedelta(
            days=self.config.calibration_days
        )
        release_date = calibration_date + timedelta(days=7)

        # Create evaluation
        evaluation = Evaluation(
            employee_id=employee.person.id,
            manager_id=employee.get_manager(),
            cycle_name=cycle_name,
            current_phase=EvaluationPhase.CONTEXT_PEER_SELECTION,
            current_state=EvaluationState.CYCLE_STARTED,
            peer_selection_deadline=peer_selection_deadline,
            peer_feedback_deadline=peer_feedback_deadline,
            self_eval_deadline=self_eval_deadline,
            manager_eval_deadline=manager_eval_deadline,
            calibration_date=calibration_date,
            release_date=release_date,
        )

        # Store in database
        eval_dict = evaluation.model_dump(mode="json")
        await self.document_store.insert(
            collection="evaluations",
            document=eval_dict,
            doc_id=str(evaluation.id),
        )

        logger.info(f"Created evaluation {evaluation.id} for {employee.person.name}")
        return evaluation

    async def process_peer_selection(
        self,
        evaluation_id: UUID,
        employee_id: UUID,
    ) -> Dict[str, Any]:
        """
        Process peer selection for an evaluation

        Uses ContextMiner to suggest peers based on collaboration data.
        """
        logger.info(f"Processing peer selection for evaluation {evaluation_id}")

        # Get employee data
        employee_doc = await self.document_store.find_by_id("employees", str(employee_id))
        if not employee_doc:
            raise ValueError(f"Employee {employee_id} not found")

        employee = Employee(**employee_doc)

        # Select best available ContextMiner using load balancing
        miner = await self._select_agent(self.context_miners)

        # Generate peer suggestions
        suggested_peers = await miner.suggest_peers(
            employee=employee,
            num_peers=5,
            min_relationship_strength=0.5,
        )

        # Update evaluation
        evaluation = self.active_evaluations.get(evaluation_id)
        if evaluation:
            evaluation.suggested_peers = [peer["peer_id"] for peer in suggested_peers]
            await self._update_evaluation(evaluation)

        # Publish event
        await self.pubsub.publish(
            topic=f"evaluations/{evaluation_id}/peers_suggested",
            content={
                "evaluation_id": str(evaluation_id),
                "suggested_peers": suggested_peers,
            },
            publisher_id=self.id,
        )

        return {
            "evaluation_id": str(evaluation_id),
            "suggested_peers": suggested_peers,
            "status": "success",
        }

    async def process_peer_feedback(
        self,
        evaluation_id: UUID,
        peer_id: UUID,
        raw_feedback: str,
        input_method: str = "text",
    ) -> PeerFeedback:
        """
        Process peer feedback submission

        Uses Scribe to synthesize raw input into professional feedback.
        """
        logger.info(f"Processing peer feedback for evaluation {evaluation_id}")

        # Select best available Scribe
        scribe = await self._select_agent(self.scribes)

        # Synthesize feedback
        synthesized = await scribe.synthesize_peer_feedback(
            raw_input=raw_feedback,
            input_method=input_method,
        )

        # Create feedback record
        evaluation = self.active_evaluations.get(evaluation_id)
        if not evaluation:
            raise ValueError(f"Evaluation {evaluation_id} not found")

        # Get peer name
        peer_doc = await self.document_store.find_by_id("employees", str(peer_id))
        peer_name = peer_doc.get("person", {}).get("name", "Unknown") if peer_doc else "Unknown"

        feedback = PeerFeedback(
            evaluation_id=evaluation_id,
            peer_id=peer_id,
            peer_name=peer_name,
            raw_input=raw_feedback,
            input_method=input_method,
            synthesized_feedback=synthesized["synthesized_text"],
            synthesized_at=datetime.now(),
        )

        # Add to evaluation
        evaluation.peer_feedbacks.append(feedback)
        await self._update_evaluation(evaluation)

        # Publish event
        await self.pubsub.publish(
            topic=f"evaluations/{evaluation_id}/peer_feedback_submitted",
            content={
                "evaluation_id": str(evaluation_id),
                "peer_id": str(peer_id),
            },
            publisher_id=self.id,
        )

        logger.info(f"Peer feedback processed for evaluation {evaluation_id}")
        return feedback

    async def generate_manager_draft(
        self,
        evaluation_id: UUID,
    ) -> ManagerEvaluation:
        """
        Generate AI-assisted manager evaluation draft

        This is the CRITICAL function that implements RAG pipeline.
        """
        logger.info(f"Generating manager draft for evaluation {evaluation_id}")

        evaluation = self.active_evaluations.get(evaluation_id)
        if not evaluation:
            raise ValueError(f"Evaluation {evaluation_id} not found")

        # Select best available Scribe
        scribe = await self._select_agent(self.scribes)

        # Generate draft using RAG
        draft = await scribe.generate_manager_draft(
            evaluation_id=evaluation_id,
            peer_feedbacks=evaluation.peer_feedbacks,
            self_evaluation=evaluation.self_evaluation,
        )

        # Create manager evaluation record
        manager_eval = ManagerEvaluation(
            evaluation_id=evaluation_id,
            manager_id=evaluation.manager_id,
            employee_id=evaluation.employee_id,
            ai_draft_summary=draft["draft_summary"],
            ai_draft_evidence_map=draft["evidence_map"],
            ai_questions=draft["clarifying_questions"],
            ai_generated_at=datetime.now(),
            final_summary="",  # To be filled by manager
            overall_rating="meets",  # Placeholder
            promotion_eligibility="developing",  # Placeholder
        )

        # Update evaluation
        evaluation.manager_evaluation = manager_eval
        await self._update_evaluation(evaluation)

        # Transition state
        await self.state_machine.transition(
            evaluation=evaluation,
            new_state=EvaluationState.AI_DRAFT_GENERATED,
        )

        logger.info(f"Manager draft generated for evaluation {evaluation_id}")
        return manager_eval

    async def _select_agent(self, agents: List[Any]) -> Any:
        """Select best available agent using load balancing"""
        if not agents:
            raise ValueError("No agents available")

        if len(agents) == 1:
            return agents[0]

        # Get agent loads
        agent_loads = []
        for agent in agents:
            state = agent.get_state()
            agent_loads.append({
                "id": agent.id,
                "current_load": state.workload,
            })

        # Use adaptive load balancing from IRAS
        tasks = [{"id": "current_task", "load": 0.1}]
        allocation = adaptive_load_balance(tasks, agent_loads)

        if allocation:
            selected_agent_id = allocation[0]["agent_id"]
            return next(a for a in agents if a.id == selected_agent_id)

        return agents[0]

    async def _update_evaluation(self, evaluation: Evaluation) -> None:
        """Update evaluation in database and cache"""
        evaluation.updated_at = datetime.now()

        eval_dict = evaluation.model_dump(mode="json")
        await self.document_store.update(
            collection="evaluations",
            query={"_id": str(evaluation.id)},
            update={"$set": eval_dict},
        )

        self.active_evaluations[evaluation.id] = evaluation

    async def get_evaluation(self, evaluation_id: UUID) -> Optional[Evaluation]:
        """Get evaluation by ID"""
        # Check cache first
        if evaluation_id in self.active_evaluations:
            return self.active_evaluations[evaluation_id]

        # Fetch from database
        eval_doc = await self.document_store.find_by_id("evaluations", str(evaluation_id))
        if eval_doc:
            evaluation = Evaluation(**eval_doc)
            self.active_evaluations[evaluation_id] = evaluation
            return evaluation

        return None

    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get comprehensive swarm status"""
        return {
            "orchestrator_id": str(self.id),
            "is_running": self.is_running,
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
            "agents": {
                "watchkeeper": self.watchkeeper.get_status() if self.watchkeeper else None,
                "context_miners": [m.get_status() for m in self.context_miners],
                "scribes": [s.get_status() for s in self.scribes],
                "chasers": [c.get_status() for c in self.chasers],
                "gatekeeper": self.gatekeeper.get_status() if self.gatekeeper else None,
                "analyst": self.analyst.get_status() if self.analyst else None,
            },
            "active_evaluations": len(self.active_evaluations),
            "background_tasks": len(self.background_tasks),
            "database_stats": {
                "document_store": self.document_store.get_statistics(),
                "vector_store": self.vector_store.get_statistics(),
                "graph_store": self.graph_store.get_statistics(),
                "timeseries_store": self.timeseries_store.get_statistics(),
            },
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown orchestrator"""
        logger.info("Shutting down Bloom orchestrator...")

        self.is_running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Shutdown agents
        agents = [
            self.watchkeeper,
            *self.context_miners,
            *self.scribes,
            *self.chasers,
            self.gatekeeper,
            self.analyst,
        ]

        for agent in agents:
            if agent:
                await agent.shutdown()

        # Shutdown autonomous controllers
        for controller in self.autonomous_controllers.values():
            if hasattr(controller, "shutdown"):
                await controller.shutdown()

        logger.info("Bloom orchestrator shutdown complete")
