"""
Coordinator - Multi-Agent Swarm Orchestration

The Coordinator is the heart of the IRAS system, managing a swarm of specialized
agents to perform complex research and analysis tasks. It orchestrates workflows,
manages communication, integrates databases, and provides autonomous operation.

Key Features:
- Multi-agent swarm management (researcher, analyst, fact-checker, synthesizer)
- Advanced communication protocols (Contract Net, Blackboard, Pub/Sub)
- Multi-database integration (Vector, Graph, Time-Series, Document)
- Mathematical task allocation and load balancing
- Autonomous operation with monitoring and error recovery
- Complete research & analysis pipeline

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                    Coordinator                           │
    │  ┌─────────────────────────────────────────────────┐   │
    │  │           Agent Swarm Management                 │   │
    │  │  [Researcher] [Analyst] [FactChecker] [Synth]   │   │
    │  └─────────────────────────────────────────────────┘   │
    │  ┌─────────────────────────────────────────────────┐   │
    │  │        Communication Protocols                   │   │
    │  │  [ContractNet] [Blackboard] [PubSub]            │   │
    │  └─────────────────────────────────────────────────┘   │
    │  ┌─────────────────────────────────────────────────┐   │
    │  │          Database Integration                    │   │
    │  │  [Vector] [Graph] [TimeSeries] [Document]       │   │
    │  └─────────────────────────────────────────────────┘   │
    │  ┌─────────────────────────────────────────────────┐   │
    │  │        Autonomous Operations                     │   │
    │  │  [Monitoring] [Recovery] [Learning]             │   │
    │  └─────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field

# Core components
from iras.core.planning import Task, TaskPriority, TaskStatus

# Specialized agents
from iras.agents.analyst import AnalystAgent
from iras.agents.fact_checker import FactCheckerAgent
from iras.agents.researcher import ResearcherAgent
from iras.agents.synthesizer import SynthesizerAgent

# Communication protocols
from iras.communication.protocols import (
    BlackboardSystem,
    ContractNetProtocol,
    PubSubProtocol,
    TaskAnnouncement,
    Bid,
)

# Databases
from iras.databases import (
    DocumentStore,
    GraphStore,
    TimeSeriesStore,
    VectorStore,
)

# Mathematical foundations
from iras.math import (
    load_aware_allocation,
    least_loaded_balance,
    weighted_voting,
)

# Autonomous operations
from iras.autonomous.monitoring import MonitoringSystem, HealthStatus, AlertLevel
from iras.autonomous.error_recovery import (
    ErrorRecoverySystem,
    RecoveryStrategy,
)
from iras.autonomous.adaptive_learning import AdaptiveLearningSystem


class WorkflowType(str, Enum):
    """Types of research workflows"""

    SIMPLE_RESEARCH = "simple_research"
    COMPREHENSIVE_RESEARCH = "comprehensive_research"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    FACT_CHECKING = "fact_checking"
    CUSTOM = "custom"


class WorkflowStage(str, Enum):
    """Stages in a research workflow"""

    INITIALIZATION = "initialization"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    VERIFICATION = "verification"
    SYNTHESIS = "synthesis"
    COMPLETION = "completion"
    ERROR = "error"


class WorkflowConfig(BaseModel):
    """Configuration for a research workflow"""

    workflow_id: UUID = Field(default_factory=uuid4)
    workflow_type: WorkflowType = WorkflowType.COMPREHENSIVE_RESEARCH
    topics: List[str] = Field(default_factory=list)

    # Research parameters
    research_depth: int = Field(default=2, ge=1, le=5)
    num_sources: int = Field(default=10, ge=1)

    # Feature flags
    enable_analysis: bool = True
    enable_fact_checking: bool = True
    enable_synthesis: bool = True

    # Advanced options
    use_contract_net: bool = True
    use_blackboard: bool = True
    use_pubsub: bool = True
    store_in_databases: bool = True
    enable_monitoring: bool = True
    enable_error_recovery: bool = True
    enable_adaptive_learning: bool = True

    # Thresholds
    min_source_quality: float = Field(default=0.6, ge=0.0, le=1.0)
    min_verification_confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    # Timeout settings (in seconds)
    research_timeout: float = 300.0
    analysis_timeout: float = 180.0
    verification_timeout: float = 120.0
    synthesis_timeout: float = 120.0

    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    """Results from a workflow execution"""

    workflow_id: UUID
    workflow_type: WorkflowType
    status: str  # success, partial_success, failure

    # Stage results
    research_results: Optional[Dict[str, Any]] = None
    analysis_results: Optional[Dict[str, Any]] = None
    verification_results: Optional[Dict[str, Any]] = None
    synthesis_results: Optional[Dict[str, Any]] = None

    # Metadata
    start_time: datetime
    end_time: datetime
    duration_seconds: float

    # Quality metrics
    overall_quality_score: float = 0.0
    sources_used: int = 0
    insights_generated: int = 0

    # Error information
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Database references
    vector_store_ids: List[str] = Field(default_factory=list)
    graph_node_ids: List[str] = Field(default_factory=list)
    document_ids: List[str] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)


class Coordinator:
    """
    Main orchestrator for the IRAS multi-agent system

    The Coordinator manages a swarm of specialized agents and orchestrates
    complex research and analysis workflows. It provides:

    1. Agent Management:
       - Researcher agents for information gathering
       - Analyst agents for data analysis
       - Fact-checker agents for verification
       - Synthesizer agents for report generation

    2. Communication:
       - Contract Net Protocol for task allocation
       - Blackboard System for shared memory
       - Pub/Sub for event-driven messaging

    3. Database Integration:
       - Vector store for semantic search
       - Graph store for relationships
       - Time-series store for temporal data
       - Document store for full-text storage

    4. Autonomous Operations:
       - Self-monitoring and health tracking
       - Error detection and recovery
       - Adaptive learning from past workflows

    Example:
        >>> coordinator = Coordinator()
        >>> await coordinator.initialize()
        >>>
        >>> results = await coordinator.research("quantum computing")
        >>> print(results.synthesis_results["summary"])
    """

    def __init__(
        self,
        num_researchers: int = 2,
        num_analysts: int = 1,
        num_fact_checkers: int = 1,
        num_synthesizers: int = 1,
    ):
        """
        Initialize the Coordinator

        Args:
            num_researchers: Number of researcher agents
            num_analysts: Number of analyst agents
            num_fact_checkers: Number of fact-checker agents
            num_synthesizers: Number of synthesizer agents
        """
        self.coordinator_id = uuid4()
        self.initialized = False
        self.running = False

        # Agent swarm
        self.researchers: List[ResearcherAgent] = []
        self.analysts: List[AnalystAgent] = []
        self.fact_checkers: List[FactCheckerAgent] = []
        self.synthesizers: List[SynthesizerAgent] = []

        self.num_researchers = num_researchers
        self.num_analysts = num_analysts
        self.num_fact_checkers = num_fact_checkers
        self.num_synthesizers = num_synthesizers

        # Communication protocols
        self.contract_net: Optional[ContractNetProtocol] = None
        self.blackboard: Optional[BlackboardSystem] = None
        self.pubsub: Optional[PubSubProtocol] = None

        # Databases
        self.vector_store: Optional[VectorStore] = None
        self.graph_store: Optional[GraphStore] = None
        self.timeseries_store: Optional[TimeSeriesStore] = None
        self.document_store: Optional[DocumentStore] = None

        # Autonomous systems
        self.monitoring: Optional[MonitoringSystem] = None
        self.error_recovery: Optional[ErrorRecoverySystem] = None
        self.adaptive_learning: Optional[AdaptiveLearningSystem] = None

        # Workflow tracking
        self.active_workflows: Dict[UUID, WorkflowConfig] = {}
        self.workflow_history: List[WorkflowResult] = []

        # Statistics
        self.total_workflows_completed = 0
        self.total_tasks_allocated = 0
        self.total_sources_processed = 0

        logger.info(
            f"Coordinator initialized: {num_researchers} researchers, "
            f"{num_analysts} analysts, {num_fact_checkers} fact-checkers, "
            f"{num_synthesizers} synthesizers"
        )

    async def initialize(self) -> None:
        """
        Initialize all components of the coordinator

        This includes:
        - Creating agent swarm
        - Setting up communication protocols
        - Initializing databases
        - Starting autonomous systems
        """
        if self.initialized:
            logger.warning("Coordinator already initialized")
            return

        logger.info("Initializing coordinator...")

        # 1. Create agent swarm
        await self._initialize_agents()

        # 2. Setup communication protocols
        await self._initialize_communication()

        # 3. Initialize databases
        await self._initialize_databases()

        # 4. Start autonomous systems
        await self._initialize_autonomous_systems()

        self.initialized = True
        self.running = True

        logger.info("Coordinator initialization complete")

    async def _initialize_agents(self) -> None:
        """Initialize agent swarm"""
        logger.info("Initializing agent swarm...")

        # Create researchers
        for i in range(self.num_researchers):
            researcher = ResearcherAgent(name=f"Researcher-{i+1}")
            self.researchers.append(researcher)

        # Create analysts
        for i in range(self.num_analysts):
            analyst = AnalystAgent(name=f"Analyst-{i+1}")
            self.analysts.append(analyst)

        # Create fact-checkers
        for i in range(self.num_fact_checkers):
            fact_checker = FactCheckerAgent(name=f"FactChecker-{i+1}")
            self.fact_checkers.append(fact_checker)

        # Create synthesizers
        for i in range(self.num_synthesizers):
            synthesizer = SynthesizerAgent(name=f"Synthesizer-{i+1}")
            self.synthesizers.append(synthesizer)

        total_agents = len(self.get_all_agents())
        logger.info(f"Agent swarm initialized: {total_agents} agents")

    async def _initialize_communication(self) -> None:
        """Initialize communication protocols"""
        logger.info("Initializing communication protocols...")

        # Contract Net Protocol for task allocation
        self.contract_net = ContractNetProtocol(
            bid_timeout=30.0,
            task_timeout=300.0,
            max_reannouncements=3,
        )

        # Blackboard System for shared memory
        self.blackboard = BlackboardSystem(
            max_entries=10000,
            enable_notifications=True,
        )

        # Pub/Sub for event-driven messaging
        self.pubsub = PubSubProtocol(
            max_retained_per_topic=10,
            message_ttl=3600.0,  # 1 hour
        )

        # Subscribe all agents to relevant topics
        for agent in self.get_all_agents():
            await self.pubsub.subscribe(
                topic="coordinator/#",
                agent_id=agent.id,
            )

        logger.info("Communication protocols initialized")

    async def _initialize_databases(self) -> None:
        """Initialize database integrations"""
        logger.info("Initializing databases...")

        # Vector store for semantic search
        self.vector_store = VectorStore(
            dimension=1536,  # OpenAI embedding dimension
            similarity_metric="cosine",
        )

        # Graph store for relationships
        self.graph_store = GraphStore()

        # Time-series store for temporal data
        self.timeseries_store = TimeSeriesStore(
            retention_days=90,
        )

        # Document store for full-text storage
        self.document_store = DocumentStore(
            enable_full_text_search=True,
        )

        logger.info("Databases initialized")

    async def _initialize_autonomous_systems(self) -> None:
        """Initialize autonomous operation systems"""
        logger.info("Initializing autonomous systems...")

        # Monitoring system
        self.monitoring = MonitoringSystem(
            agent_id=self.coordinator_id,
            metrics_retention_hours=24,
            monitoring_interval=5.0,
        )
        await self.monitoring.start()

        # Error recovery system
        self.error_recovery = ErrorRecoverySystem(
            agent_id=self.coordinator_id,
            max_retries=3,
            enable_circuit_breaker=True,
        )

        # Adaptive learning system
        self.adaptive_learning = AdaptiveLearningSystem(
            agent_id=self.coordinator_id,
            learning_rate=0.01,
        )

        logger.info("Autonomous systems initialized")

    async def shutdown(self) -> None:
        """Gracefully shutdown the coordinator"""
        logger.info("Shutting down coordinator...")

        self.running = False

        # Stop monitoring
        if self.monitoring:
            await self.monitoring.stop()

        # Clear active workflows
        self.active_workflows.clear()

        self.initialized = False

        logger.info("Coordinator shutdown complete")

    # ========================================================================
    # High-Level Research Methods
    # ========================================================================

    async def research(
        self,
        topic: str,
        depth: int = 2,
        **kwargs,
    ) -> WorkflowResult:
        """
        Perform simple research on a topic

        This is a convenience method for basic research without advanced features.

        Args:
            topic: Topic to research
            depth: Research depth (1-5)
            **kwargs: Additional configuration options

        Returns:
            WorkflowResult with research findings

        Example:
            >>> results = await coordinator.research("quantum computing", depth=3)
            >>> print(results.synthesis_results["summary"])
        """
        config = WorkflowConfig(
            workflow_type=WorkflowType.SIMPLE_RESEARCH,
            topics=[topic],
            research_depth=depth,
            enable_analysis=kwargs.get("enable_analysis", True),
            enable_fact_checking=kwargs.get("enable_fact_checking", False),
            enable_synthesis=kwargs.get("enable_synthesis", True),
        )

        return await self.execute_workflow(config)

    async def comprehensive_research(
        self,
        topics: List[str],
        depth: int = 3,
        enable_fact_checking: bool = True,
        **kwargs,
    ) -> WorkflowResult:
        """
        Perform comprehensive research on multiple topics

        This uses all available agents and features for thorough research.

        Args:
            topics: List of topics to research
            depth: Research depth (1-5)
            enable_fact_checking: Whether to verify facts
            **kwargs: Additional configuration options

        Returns:
            WorkflowResult with comprehensive findings

        Example:
            >>> results = await coordinator.comprehensive_research(
            ...     topics=["AI", "blockchain"],
            ...     depth=4,
            ...     enable_fact_checking=True,
            ... )
        """
        config = WorkflowConfig(
            workflow_type=WorkflowType.COMPREHENSIVE_RESEARCH,
            topics=topics,
            research_depth=depth,
            num_sources=kwargs.get("num_sources", 20),
            enable_analysis=True,
            enable_fact_checking=enable_fact_checking,
            enable_synthesis=True,
            use_contract_net=True,
            use_blackboard=True,
            use_pubsub=True,
            store_in_databases=True,
        )

        return await self.execute_workflow(config)

    async def comparative_analysis(
        self,
        topics: List[str],
        **kwargs,
    ) -> WorkflowResult:
        """
        Perform comparative analysis across multiple topics

        Args:
            topics: Topics to compare
            **kwargs: Additional configuration options

        Returns:
            WorkflowResult with comparative analysis

        Example:
            >>> results = await coordinator.comparative_analysis(
            ...     topics=["Python", "JavaScript", "Rust"]
            ... )
        """
        config = WorkflowConfig(
            workflow_type=WorkflowType.COMPARATIVE_ANALYSIS,
            topics=topics,
            research_depth=kwargs.get("depth", 3),
            enable_analysis=True,
            enable_fact_checking=True,
            enable_synthesis=True,
        )

        return await self.execute_workflow(config)

    # ========================================================================
    # Workflow Execution
    # ========================================================================

    async def execute_workflow(self, config: WorkflowConfig) -> WorkflowResult:
        """
        Execute a research workflow

        This is the main orchestration method that coordinates all agents
        and systems to complete a research workflow.

        Args:
            config: Workflow configuration

        Returns:
            WorkflowResult with all findings

        Raises:
            RuntimeError: If coordinator not initialized
        """
        if not self.initialized:
            raise RuntimeError("Coordinator not initialized. Call initialize() first.")

        start_time = datetime.now()
        self.active_workflows[config.workflow_id] = config

        logger.info(
            f"Starting workflow {config.workflow_id}: "
            f"{config.workflow_type.value} on {len(config.topics)} topics"
        )

        # Publish workflow start event
        if config.use_pubsub and self.pubsub:
            await self.pubsub.publish(
                topic="coordinator/workflow/started",
                content={
                    "workflow_id": str(config.workflow_id),
                    "type": config.workflow_type.value,
                    "topics": config.topics,
                },
                publisher_id=self.coordinator_id,
            )

        result = WorkflowResult(
            workflow_id=config.workflow_id,
            workflow_type=config.workflow_type,
            status="in_progress",
            start_time=start_time,
            end_time=start_time,  # Will be updated
            duration_seconds=0.0,
        )

        try:
            # Stage 1: Research
            logger.info(f"[{config.workflow_id}] Stage 1: Research")
            research_results = await self._execute_research_stage(config)
            result.research_results = research_results
            result.sources_used = research_results.get("total_sources_found", 0)

            # Stage 2: Analysis
            if config.enable_analysis and research_results:
                logger.info(f"[{config.workflow_id}] Stage 2: Analysis")
                analysis_results = await self._execute_analysis_stage(
                    config, research_results
                )
                result.analysis_results = analysis_results
                result.insights_generated = len(
                    analysis_results.get("key_insights", [])
                )

            # Stage 3: Verification
            if config.enable_fact_checking and research_results:
                logger.info(f"[{config.workflow_id}] Stage 3: Verification")
                verification_results = await self._execute_verification_stage(
                    config, research_results
                )
                result.verification_results = verification_results

            # Stage 4: Synthesis
            if config.enable_synthesis:
                logger.info(f"[{config.workflow_id}] Stage 4: Synthesis")
                synthesis_results = await self._execute_synthesis_stage(
                    config,
                    research_results,
                    result.analysis_results,
                    result.verification_results,
                )
                result.synthesis_results = synthesis_results
                result.overall_quality_score = synthesis_results.get(
                    "quality_score", 0.0
                )

            # Store in databases
            if config.store_in_databases:
                await self._store_results_in_databases(config, result)

            # Calculate final quality score
            result.overall_quality_score = self._calculate_workflow_quality(result)

            result.status = "success"
            logger.info(
                f"Workflow {config.workflow_id} completed successfully "
                f"(quality: {result.overall_quality_score:.2f})"
            )

        except Exception as e:
            logger.error(f"Workflow {config.workflow_id} failed: {e}")
            result.status = "failure"
            result.errors.append({
                "stage": "execution",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })

            # Attempt recovery if enabled
            if config.enable_error_recovery and self.error_recovery:
                recovery_result = await self.error_recovery.handle_error(
                    error=e,
                    context={"workflow_id": str(config.workflow_id)},
                    strategy=RecoveryStrategy.RETRY,
                )
                if recovery_result.get("recovered"):
                    result.status = "partial_success"
                    result.warnings.append("Recovered from error with reduced results")

        finally:
            # Update result timing
            end_time = datetime.now()
            result.end_time = end_time
            result.duration_seconds = (end_time - start_time).total_seconds()

            # Clean up
            del self.active_workflows[config.workflow_id]
            self.workflow_history.append(result)
            self.total_workflows_completed += 1

            # Publish completion event
            if config.use_pubsub and self.pubsub:
                await self.pubsub.publish(
                    topic="coordinator/workflow/completed",
                    content={
                        "workflow_id": str(config.workflow_id),
                        "status": result.status,
                        "duration": result.duration_seconds,
                        "quality": result.overall_quality_score,
                    },
                    publisher_id=self.coordinator_id,
                )

            # Adaptive learning
            if config.enable_adaptive_learning and self.adaptive_learning:
                await self.adaptive_learning.learn_from_outcome(
                    task_type=config.workflow_type.value,
                    outcome=result.status,
                    metrics={
                        "quality_score": result.overall_quality_score,
                        "duration": result.duration_seconds,
                        "sources_used": result.sources_used,
                    },
                )

        return result

    async def _execute_research_stage(
        self,
        config: WorkflowConfig,
    ) -> Dict[str, Any]:
        """Execute research stage using researcher agents"""

        # If using Contract Net Protocol, allocate via bidding
        if config.use_contract_net and self.contract_net and len(self.researchers) > 1:
            return await self._research_via_contract_net(config)

        # Otherwise, use direct allocation
        return await self._research_direct(config)

    async def _research_via_contract_net(
        self,
        config: WorkflowConfig,
    ) -> Dict[str, Any]:
        """Allocate research tasks via Contract Net Protocol"""

        all_results = []

        for topic in config.topics:
            # Announce research task
            announcement = TaskAnnouncement(
                description=f"Research topic: {topic}",
                required_capabilities={"web_search", "source_evaluation"},
                metadata={
                    "topic": topic,
                    "depth": config.research_depth,
                    "num_sources": config.num_sources,
                },
            )

            task_id = await self.contract_net.announce_task(
                announcement, self.coordinator_id
            )
            self.total_tasks_allocated += 1

            # Collect bids from researchers
            await asyncio.sleep(2.0)  # Wait for bids

            # Evaluate bids (use lowest cost strategy)
            winning_bid = await self.contract_net.evaluate_bids(
                task_id, strategy="best_confidence"
            )

            if winning_bid:
                # Award task to winner
                await self.contract_net.award_task(
                    task_id, winning_bid, self.coordinator_id
                )

                # Get the winning researcher
                winning_researcher = next(
                    (r for r in self.researchers if r.id == winning_bid.agent_id),
                    self.researchers[0]
                )

                # Execute research
                topic_result = await winning_researcher.research_topic(
                    topic=topic,
                    depth=config.research_depth,
                    num_sources=config.num_sources,
                )

                all_results.append(topic_result)

                # Submit result back
                await self.contract_net.submit_result(
                    task_id, winning_bid.agent_id, topic_result, self.coordinator_id
                )

                # Store in blackboard
                if config.use_blackboard and self.blackboard:
                    await self.blackboard.write(
                        key=f"research/{topic}",
                        value=topic_result,
                        author_id=winning_bid.agent_id,
                        tags={"research", "topic", topic},
                    )
            else:
                # No bids, use first researcher
                logger.warning(f"No bids for research on '{topic}', using fallback")
                topic_result = await self.researchers[0].research_topic(
                    topic=topic,
                    depth=config.research_depth,
                    num_sources=config.num_sources,
                )
                all_results.append(topic_result)

        # Combine results
        return self._combine_research_results(all_results)

    async def _research_direct(self, config: WorkflowConfig) -> Dict[str, Any]:
        """Direct research allocation (load balancing)"""

        all_results = []

        # Use load-aware allocation
        researcher_loads = [0.0] * len(self.researchers)

        for i, topic in enumerate(config.topics):
            # Select least loaded researcher
            researcher_idx = researcher_loads.index(min(researcher_loads))
            researcher = self.researchers[researcher_idx]

            # Execute research
            topic_result = await researcher.research_topic(
                topic=topic,
                depth=config.research_depth,
                num_sources=config.num_sources,
            )

            all_results.append(topic_result)

            # Update load
            researcher_loads[researcher_idx] += 1.0

            # Store in blackboard
            if config.use_blackboard and self.blackboard:
                await self.blackboard.write(
                    key=f"research/{topic}",
                    value=topic_result,
                    author_id=researcher.id,
                    tags={"research", "topic", topic},
                )

        return self._combine_research_results(all_results)

    def _combine_research_results(
        self,
        results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Combine multiple research results"""

        combined = {
            "topics": [],
            "sources": [],
            "total_sources_found": 0,
            "quality_sources": 0,
            "queries_used": [],
            "timestamp": datetime.now().isoformat(),
        }

        for result in results:
            combined["topics"].append(result.get("topic"))
            combined["sources"].extend(result.get("sources", []))
            combined["total_sources_found"] += result.get("total_sources_found", 0)
            combined["quality_sources"] += len(result.get("sources", []))
            combined["queries_used"].extend(result.get("queries_used", []))

        self.total_sources_processed += combined["total_sources_found"]

        return combined

    async def _execute_analysis_stage(
        self,
        config: WorkflowConfig,
        research_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute analysis stage using analyst agents"""

        # Use first analyst (can be expanded for parallel analysis)
        analyst = self.analysts[0]

        sources = research_results.get("sources", [])
        analysis_results = await analyst.analyze_sources(sources)

        # Store in blackboard
        if config.use_blackboard and self.blackboard:
            await self.blackboard.write(
                key="analysis/latest",
                value=analysis_results,
                author_id=analyst.id,
                tags={"analysis", "insights"},
            )

        return analysis_results

    async def _execute_verification_stage(
        self,
        config: WorkflowConfig,
        research_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute verification stage using fact-checker agents"""

        fact_checker = self.fact_checkers[0]

        # Extract claims from research (simulated)
        sources = research_results.get("sources", [])
        claims = []
        for source in sources[:5]:  # Check top 5 sources
            claim = source.get("snippet", source.get("title", ""))
            if claim:
                claims.append(claim)

        if not claims:
            return {
                "total_claims": 0,
                "verifications": [],
                "summary": {"verified": 0, "refuted": 0, "unverified": 0},
                "overall_reliability": 0.0,
            }

        verification_results = await fact_checker.verify_claims(claims, sources)

        # Store in blackboard
        if config.use_blackboard and self.blackboard:
            await self.blackboard.write(
                key="verification/latest",
                value=verification_results,
                author_id=fact_checker.id,
                tags={"verification", "fact_checking"},
            )

        return verification_results

    async def _execute_synthesis_stage(
        self,
        config: WorkflowConfig,
        research_results: Dict[str, Any],
        analysis_results: Optional[Dict[str, Any]],
        verification_results: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute synthesis stage using synthesizer agents"""

        synthesizer = self.synthesizers[0]

        # Determine topic for report
        topics = config.topics
        topic = ", ".join(topics) if len(topics) <= 3 else f"{topics[0]} and {len(topics)-1} others"

        # Generate comprehensive report
        synthesis_results = await synthesizer.generate_report(
            topic=topic,
            research_results=research_results,
            analysis_results=analysis_results or {},
            verification_results=verification_results,
            format="comprehensive",
        )

        # Store in blackboard
        if config.use_blackboard and self.blackboard:
            await self.blackboard.write(
                key="synthesis/latest",
                value=synthesis_results,
                author_id=synthesizer.id,
                tags={"synthesis", "report"},
            )

        return synthesis_results

    async def _store_results_in_databases(
        self,
        config: WorkflowConfig,
        result: WorkflowResult,
    ) -> None:
        """Store workflow results in databases"""

        try:
            # Store in document store
            if self.document_store and result.synthesis_results:
                doc_id = await self.document_store.store_document(
                    content=result.synthesis_results.get("full_report", ""),
                    metadata={
                        "workflow_id": str(result.workflow_id),
                        "topics": config.topics,
                        "timestamp": result.start_time.isoformat(),
                    },
                )
                result.document_ids.append(doc_id)

            # Store sources in vector store for semantic search
            if self.vector_store and result.research_results:
                sources = result.research_results.get("sources", [])
                for source in sources[:10]:  # Store top 10
                    vector_id = await self.vector_store.add_embedding(
                        text=source.get("snippet", ""),
                        metadata=source,
                    )
                    result.vector_store_ids.append(vector_id)

            # Store workflow relationships in graph
            if self.graph_store:
                # Create workflow node
                workflow_node = await self.graph_store.add_node(
                    node_type="workflow",
                    properties={
                        "workflow_id": str(result.workflow_id),
                        "type": config.workflow_type.value,
                        "quality_score": result.overall_quality_score,
                    },
                )
                result.graph_node_ids.append(workflow_node)

                # Link to topics
                for topic in config.topics:
                    topic_node = await self.graph_store.add_node(
                        node_type="topic",
                        properties={"name": topic},
                    )
                    await self.graph_store.add_edge(
                        workflow_node, topic_node, "researched"
                    )

            # Store metrics in time-series
            if self.timeseries_store:
                await self.timeseries_store.record_metric(
                    metric_name="workflow_quality",
                    value=result.overall_quality_score,
                    tags={
                        "workflow_type": config.workflow_type.value,
                        "workflow_id": str(result.workflow_id),
                    },
                )

                await self.timeseries_store.record_metric(
                    metric_name="workflow_duration",
                    value=result.duration_seconds,
                    tags={"workflow_type": config.workflow_type.value},
                )

        except Exception as e:
            logger.error(f"Error storing results in databases: {e}")
            result.warnings.append(f"Database storage failed: {str(e)}")

    def _calculate_workflow_quality(self, result: WorkflowResult) -> float:
        """Calculate overall workflow quality score"""

        scores = []

        # Research quality (based on source count and quality)
        if result.research_results:
            quality_sources = result.research_results.get("quality_sources", 0)
            if quality_sources >= 10:
                scores.append(0.9)
            elif quality_sources >= 5:
                scores.append(0.7)
            else:
                scores.append(0.5)

        # Analysis quality (based on insights generated)
        if result.analysis_results:
            insights = len(result.analysis_results.get("key_insights", []))
            if insights >= 3:
                scores.append(0.9)
            elif insights >= 1:
                scores.append(0.7)
            else:
                scores.append(0.5)

        # Verification quality
        if result.verification_results:
            reliability = result.verification_results.get("overall_reliability", 0)
            scores.append(reliability)

        # Synthesis quality
        if result.synthesis_results:
            synth_quality = result.synthesis_results.get("quality_score", 0.5)
            scores.append(synth_quality)

        return sum(scores) / len(scores) if scores else 0.5

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_all_agents(self) -> List[Any]:
        """Get all agents in the swarm"""
        return (
            self.researchers +
            self.analysts +
            self.fact_checkers +
            self.synthesizers
        )

    def get_swarm_status(self) -> Dict[str, Any]:
        """Get status of the entire swarm"""
        return {
            "coordinator_id": str(self.coordinator_id),
            "initialized": self.initialized,
            "running": self.running,
            "agents": {
                "researchers": len(self.researchers),
                "analysts": len(self.analysts),
                "fact_checkers": len(self.fact_checkers),
                "synthesizers": len(self.synthesizers),
                "total": len(self.get_all_agents()),
            },
            "communication": {
                "contract_net_active": self.contract_net is not None,
                "blackboard_active": self.blackboard is not None,
                "pubsub_active": self.pubsub is not None,
            },
            "databases": {
                "vector_store": self.vector_store is not None,
                "graph_store": self.graph_store is not None,
                "timeseries_store": self.timeseries_store is not None,
                "document_store": self.document_store is not None,
            },
            "workflows": {
                "active": len(self.active_workflows),
                "completed": self.total_workflows_completed,
                "total_tasks_allocated": self.total_tasks_allocated,
                "total_sources_processed": self.total_sources_processed,
            },
            "health": self.monitoring.get_health_status() if self.monitoring else "unknown",
        }

    def get_workflow_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow history"""
        recent = self.workflow_history[-limit:]
        return [
            {
                "workflow_id": str(wf.workflow_id),
                "type": wf.workflow_type.value,
                "status": wf.status,
                "quality_score": wf.overall_quality_score,
                "duration": wf.duration_seconds,
                "timestamp": wf.start_time.isoformat(),
            }
            for wf in recent
        ]
