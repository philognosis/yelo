# Bloom Architecture

This document provides a comprehensive technical overview of Bloom's architecture, design patterns, and implementation details.

## Table of Contents

- [System Overview](#system-overview)
- [Architectural Layers](#architectural-layers)
- [Multi-Agent Swarm Design](#multi-agent-swarm-design)
- [Database Schema](#database-schema)
- [Communication Protocols](#communication-protocols)
- [State Machine Workflow](#state-machine-workflow)
- [RAG Pipeline](#rag-pipeline)
- [Security & RBAC](#security--rbac)
- [Scalability](#scalability)
- [Design Patterns](#design-patterns)

## System Overview

Bloom is built on the **IRAS (Intelligent Research & Analysis Swarm)** framework, a multi-agent system designed for complex, autonomous workflows.

### Core Principles

1. **Autonomous by Default**: Agents make decisions independently within defined guardrails
2. **Event-Driven Architecture**: State transitions trigger events that cascade through the system
3. **Eventual Consistency**: Distributed agents converge on consistent state
4. **Graceful Degradation**: System continues operating even if individual agents fail
5. **Observable & Debuggable**: All actions are logged and traceable

### Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│ Application Layer                                           │
│  • Python 3.9+                                              │
│  • Pydantic (data validation)                               │
│  • Loguru (structured logging)                              │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Agent Framework Layer (IRAS)                                │
│  • Multi-agent coordination                                 │
│  • HTN Planning                                             │
│  • Communication protocols                                  │
│  • Autonomous controllers                                   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Data Layer                                                  │
│  • PostgreSQL (DocumentStore)                               │
│  • Redis (caching, pub/sub)                                 │
│  • Vector DB (embeddings for RAG)                           │
│  • Neo4j (GraphStore for relationships)                     │
│  • InfluxDB (TimeSeriesStore for metrics)                   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Integration Layer                                           │
│  • Slack API (notifications)                                │
│  • SMTP (email)                                             │
│  • Google Calendar / Outlook API                            │
│  • Jira API                                                 │
│  • GitHub/GitLab API                                        │
└─────────────────────────────────────────────────────────────┘
```

## Architectural Layers

### Layer 1: Orchestration

**BloomOrchestrator** is the top-level coordinator that:

```python
class BloomOrchestrator:
    def __init__(self, config: BloomConfig):
        # Initialize databases
        self.document_store = DocumentStore()
        self.vector_store = VectorStore(embedding_dim=384)
        self.graph_store = GraphStore(directed=True)
        self.timeseries_store = TimeSeriesStore()

        # Initialize communication
        self.blackboard = BlackboardSystem()
        self.contract_net = ContractNetProtocol()
        self.pubsub = PubSubProtocol()

        # Initialize workflow
        self.state_machine = EvaluationStateMachine()
        self.phase_handlers = PhaseHandlerFactory()

        # Initialize agents
        self.watchkeeper = Watchkeeper(...)
        self.context_miners = [ContextMiner(...) for _ in range(N)]
        self.scribes = [Scribe(...) for _ in range(N)]
        self.chasers = [Chaser(...) for _ in range(N)]
        self.gatekeeper = Gatekeeper(...)
        self.analyst = BloomAnalyst(...)

        # Autonomous controllers
        self.autonomous_controllers = {
            agent.id: AutonomousController(agent, ...)
            for agent in all_agents
        }
```

**Key Responsibilities**:
- Agent lifecycle management (initialization, health monitoring, shutdown)
- Database connection pooling
- Communication protocol setup
- State machine initialization
- Background task orchestration

### Layer 2: Agent Swarm

Six specialized agents with distinct roles:

#### Agent Architecture (Common Pattern)

```python
class Agent(ABC):
    def __init__(self, config: AgentConfig):
        self.id = uuid4()
        self.config = config

        # Core IRAS components
        self.state_manager = StateManager()
        self.memory = MemorySystem()
        self.reasoning = ReasoningEngine()
        self.planner = HTNPlanner()

        # Communication
        self.message_queue = asyncio.Queue()

        # Tools/capabilities
        self.tools: Dict[str, AgentTool] = {}

    async def initialize(self) -> None:
        """Initialize agent subsystems"""

    async def execute(self, task: Task) -> TaskResult:
        """Execute assigned task"""

    async def shutdown(self) -> None:
        """Graceful shutdown"""
```

#### Agent-Specific Implementations

**Watchkeeper (Orchestrator)**:
```python
Capabilities:
  - Evaluation lifecycle management
  - Cohort scheduling (L6, L5, L4, IC)
  - Deadline monitoring
  - HTN planning for workflow orchestration
  - System health monitoring

Design Pattern: State Machine Controller + Event-Driven Scheduler
```

**Context Miner (Data Engineer)**:
```python
Capabilities:
  - Multi-source data integration (Calendar, Jira, Git, Slack)
  - Relationship strength calculation
  - Graph analytics (centrality, community detection)
  - Peer suggestion generation

Design Pattern: ETL Pipeline + Graph Analytics
```

**Scribe (AI Synthesis)**:
```python
Capabilities:
  - RAG-based content generation
  - Voice dictation cleanup
  - Peer feedback synthesis
  - Manager draft generation with evidence citations
  - Clarifying question generation

Design Pattern: RAG Pipeline + Interactive Q&A System
```

**Chaser (Deadline Enforcer)**:
```python
Capabilities:
  - Deadline monitoring
  - Automated reminder scheduling
  - Multi-channel notification dispatch
  - Escalation workflows

Design Pattern: Event Scheduler + Notification Bus
```

**Gatekeeper (Security Controller)**:
```python
Capabilities:
  - RBAC enforcement
  - State transition validation
  - Audit logging
  - Data encryption/decryption

Design Pattern: Policy Engine + Audit Logger
```

**Analyst (Metrics & Calibration)**:
```python
Capabilities:
  - Evaluation metrics generation
  - Rating distribution analysis
  - Calibration support
  - Anomaly detection

Design Pattern: Analytics Pipeline + Statistical Analyzer
```

### Layer 3: Communication

Three primary communication patterns:

#### 1. Blackboard System (Shared State)

```python
class BlackboardSystem:
    """Shared knowledge base for agents"""

    async def write(self, key: str, value: Any, agent_id: UUID):
        """Write data to blackboard"""

    async def read(self, key: str) -> Any:
        """Read data from blackboard"""

    async def subscribe(self, pattern: str, agent_id: UUID):
        """Subscribe to blackboard changes"""
```

**Use Cases**:
- Sharing evaluation state across agents
- Coordinating multi-step workflows
- Caching frequently accessed data

#### 2. Pub/Sub Protocol (Event Broadcasting)

```python
class PubSubProtocol:
    """Publish-subscribe for event distribution"""

    async def publish(self, topic: str, content: Dict, publisher_id: UUID):
        """Publish event to topic"""

    async def subscribe(self, topic_pattern: str, subscriber_id: UUID):
        """Subscribe to topic pattern (supports wildcards)"""

    async def unsubscribe(self, topic_pattern: str, subscriber_id: UUID):
        """Unsubscribe from topic"""
```

**Topic Structure**:
```
evaluations/{eval_id}/started
evaluations/{eval_id}/peers_suggested
evaluations/{eval_id}/peer_feedback_submitted
evaluations/{eval_id}/state_changed
deadlines/{eval_id}/approaching
deadlines/{eval_id}/missed
notifications/{user_id}/sent
```

**Use Cases**:
- State change notifications
- Deadline alerts
- Real-time dashboard updates

#### 3. Contract Net Protocol (Task Allocation)

```python
class ContractNetProtocol:
    """Task bidding and allocation"""

    async def announce_task(self, task: Task, manager_id: UUID):
        """Announce task for bidding"""

    async def submit_bid(self, task_id: UUID, bid: Bid, agent_id: UUID):
        """Agent submits bid for task"""

    async def award_task(self, task_id: UUID, winner_id: UUID):
        """Award task to winning bidder"""
```

**Use Cases**:
- Load balancing across Scribe instances
- Dynamic task allocation
- Agent failure recovery

### Layer 4: Data Persistence

Four specialized databases for different access patterns:

#### DocumentStore (PostgreSQL)

**Schema**:
```sql
-- Evaluations table
CREATE TABLE evaluations (
    id UUID PRIMARY KEY,
    employee_id UUID NOT NULL,
    manager_id UUID NOT NULL,
    cycle_name VARCHAR(100) NOT NULL,
    current_phase VARCHAR(50) NOT NULL,
    current_state VARCHAR(50) NOT NULL,

    -- Peer selection
    suggested_peers JSONB,
    employee_selected_peers JSONB,
    manager_approved_peers JSONB,

    -- Feedback collections
    peer_feedbacks JSONB,
    self_evaluation JSONB,
    manager_evaluation JSONB,

    -- Deadlines
    peer_selection_deadline TIMESTAMP,
    peer_feedback_deadline TIMESTAMP,
    self_eval_deadline TIMESTAMP,
    manager_eval_deadline TIMESTAMP,
    calibration_date TIMESTAMP,
    release_date TIMESTAMP,

    -- State history
    state_history JSONB,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_employee_id (employee_id),
    INDEX idx_cycle_name (cycle_name),
    INDEX idx_current_state (current_state)
);

-- Employees table
CREATE TABLE employees (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255),
    level VARCHAR(10),
    sub_level INTEGER,
    role VARCHAR(50),
    manager_id UUID,

    -- Employee data
    skills JSONB,
    certifications JSONB,
    trainings JSONB,
    calendar_metrics JSONB,
    team_hours JSONB,

    hire_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_email (email),
    INDEX idx_manager_id (manager_id),
    INDEX idx_level (level)
);

-- Peer Feedback table
CREATE TABLE peer_feedbacks (
    id UUID PRIMARY KEY,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id),
    peer_id UUID NOT NULL,
    peer_name VARCHAR(255),

    raw_input TEXT NOT NULL,
    input_method VARCHAR(20),
    synthesized_feedback TEXT,

    technical_rating VARCHAR(20),
    leadership_rating VARCHAR(20),
    communication_rating VARCHAR(20),
    collaboration_rating VARCHAR(20),

    submitted_at TIMESTAMP DEFAULT NOW(),
    synthesized_at TIMESTAMP,

    INDEX idx_evaluation_id (evaluation_id),
    INDEX idx_peer_id (peer_id)
);

-- Self Evaluations table
CREATE TABLE self_evaluations (
    id UUID PRIMARY KEY,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id),
    employee_id UUID NOT NULL,

    raw_achievements TEXT NOT NULL,
    raw_challenges TEXT,
    raw_growth_areas TEXT,
    raw_goals TEXT,

    synthesized_achievements TEXT,
    synthesized_challenges TEXT,
    synthesized_growth_areas TEXT,
    synthesized_goals TEXT,

    uploaded_docs JSONB,
    project_links JSONB,

    submitted_at TIMESTAMP DEFAULT NOW(),
    synthesized_at TIMESTAMP,

    INDEX idx_evaluation_id (evaluation_id)
);

-- Deadlines table
CREATE TABLE deadlines (
    id UUID PRIMARY KEY,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id),
    deadline_type VARCHAR(50) NOT NULL,

    due_date TIMESTAMP NOT NULL,
    warning_date TIMESTAMP,
    escalation_date TIMESTAMP,

    responsible_user_id UUID,
    escalation_user_id UUID,

    status VARCHAR(20) NOT NULL,
    completed_at TIMESTAMP,

    reminder_schedule JSONB,
    reminders_sent JSONB,

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_evaluation_id (evaluation_id),
    INDEX idx_due_date (due_date),
    INDEX idx_status (status)
);

-- Notifications table
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    evaluation_id UUID,
    recipient_id UUID NOT NULL,

    template_name VARCHAR(100),
    subject VARCHAR(500),
    message TEXT,
    channel VARCHAR(20),
    priority VARCHAR(20),
    status VARCHAR(20),

    scheduled_for TIMESTAMP,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,

    external_id VARCHAR(255),

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_recipient_id (recipient_id),
    INDEX idx_status (status),
    INDEX idx_scheduled_for (scheduled_for)
);
```

#### VectorStore (RAG Embeddings)

**Purpose**: Store embeddings for RAG pipeline

**Collections**:
- `synthesized_feedback` - Processed peer feedback embeddings
- `self_evaluations` - Self-evaluation embeddings
- `historical_evaluations` - Past evaluation embeddings
- `company_docs` - Policy/guideline embeddings

**Vector Operations**:
```python
# Add document with embedding
await vector_store.add_document(
    collection="synthesized_feedback",
    document_id=str(feedback_id),
    content=synthesized_text,
    metadata={"evaluation_id": eval_id, "peer_id": peer_id}
)

# Semantic search
results = await vector_store.search(
    collection="synthesized_feedback",
    query_text="technical excellence and innovation",
    limit=10,
    min_similarity=0.7
)
```

#### GraphStore (Collaboration Networks)

**Purpose**: Model employee relationships and collaboration patterns

**Node Types**:
- `employee` - Employee nodes
- `team` - Team/project nodes
- `skill` - Skill nodes

**Edge Types**:
- `collaboration` - Collaboration relationship (weighted by strength)
- `manages` - Management hierarchy
- `works_on` - Project/team membership
- `has_skill` - Skill associations

**Graph Operations**:
```python
# Add collaboration edge
await graph_store.add_edge(
    source=str(employee_a_id),
    target=str(employee_b_id),
    edge_type="collaboration",
    weight=0.85,
    properties={
        "calendar_meetings": 25,
        "jira_interactions": 40,
        "last_interaction": "2024-12-01"
    }
)

# Calculate centrality (identify key influencers)
centrality = await graph_store.get_centrality(
    algorithm="pagerank",
    node_type="employee"
)

# Detect communities
communities = await graph_store.detect_communities(
    algorithm="louvain"
)
```

#### TimeSeriesStore (Metrics & Trends)

**Purpose**: Track metrics over time for analytics

**Metrics**:
```python
# Evaluation metrics
"evaluations.created"
"evaluations.completed"
"evaluations.deadline_violations"
"evaluations.state_transitions"

# Agent metrics
"agent.task_execution_time"
"agent.success_rate"
"agent.workload"

# System metrics
"system.health_score"
"system.active_evaluations"
```

**Time-Series Operations**:
```python
# Write point
await timeseries_store.write_point(
    metric="evaluations.created",
    value=1.0,
    tags={"cohort": "L5_Q", "cycle": "Q4 2024"},
    timestamp=datetime.now()
)

# Query range
results = await timeseries_store.query(
    metric="system.health_score",
    start_time=datetime.now() - timedelta(days=7),
    end_time=datetime.now(),
    aggregation="mean",
    interval="1h"
)
```

## Communication Protocols

### Message Flow Example

```
User submits peer feedback (via Slack)
    │
    ▼
┌─────────────────────────────────────┐
│  Slack Integration Handler          │
└─────────────────────────────────────┘
    │
    │ PubSub: evaluations/{id}/peer_feedback_submitted
    ▼
┌─────────────────────────────────────┐
│  Orchestrator receives event        │
└─────────────────────────────────────┘
    │
    │ Contract Net: Announce synthesis task
    ▼
┌─────────────────────────────────────┐
│  Scribes submit bids                │
│  (based on current workload)        │
└─────────────────────────────────────┘
    │
    │ Contract Net: Award to Scribe-2
    ▼
┌─────────────────────────────────────┐
│  Scribe-2 synthesizes feedback      │
│  - Cleans voice dictation           │
│  - Extracts themes                  │
│  - Generates professional narrative │
└─────────────────────────────────────┘
    │
    │ Blackboard: Write synthesized feedback
    ▼
┌─────────────────────────────────────┐
│  VectorStore: Add embedding         │
└─────────────────────────────────────┘
    │
    │ PubSub: evaluations/{id}/feedback_synthesized
    ▼
┌─────────────────────────────────────┐
│  State Machine: Check if all        │
│  feedback collected                 │
└─────────────────────────────────────┘
    │
    │ (if complete)
    ▼
┌─────────────────────────────────────┐
│  State Machine: Transition to       │
│  data_gathering_complete            │
└─────────────────────────────────────┘
```

## State Machine Workflow

### State Transition Graph

```
                         PHASE 1: CONTEXT & PEER SELECTION
┌──────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│ cycle_started│─────▶│peer_suggestion_     │─────▶│employee_peer_review │
└──────────────┘      │generated            │      └─────────────────────┘
                      └─────────────────────┘               │
                                                             ▼
                      ┌─────────────────────┐      ┌─────────────────────┐
                      │ peer_list_locked    │◀─────│manager_peer_approval│
                      └─────────────────────┘      └─────────────────────┘
                               │
                               │ PHASE TRANSITION
                               ▼
                         PHASE 2: DATA GATHERING
                      ┌─────────────────────┐
                      │peer_feedback_       │
                      │requested            │
                      └─────────────────────┘
                               │
                               ▼
                      ┌─────────────────────┐      ┌─────────────────────┐
                      │peer_feedback_in_    │─────▶│self_eval_requested  │
                      │progress             │      └─────────────────────┘
                      └─────────────────────┘               │
                                                             ▼
                      ┌─────────────────────┐      ┌─────────────────────┐
                      │data_gathering_      │◀─────│self_eval_in_        │
                      │complete             │      │progress             │
                      └─────────────────────┘      └─────────────────────┘
                               │
                               │ PHASE TRANSITION
                               ▼
                         PHASE 3: MANAGER EVALUATION
                      ┌─────────────────────┐      ┌─────────────────────┐
                      │manager_eval_started │─────▶│ai_draft_generated   │
                      └─────────────────────┘      └─────────────────────┘
                                                             │
                                                             ▼
                      ┌─────────────────────┐      ┌─────────────────────┐
                      │manager_eval_complete│◀─────│manager_review_in_   │
                      └─────────────────────┘      │progress             │
                               │                   └─────────────────────┘
                               │ PHASE TRANSITION
                               ▼
                         PHASE 4: CALIBRATION
                      ┌─────────────────────┐      ┌─────────────────────┐
                      │calibration_pending  │─────▶│calibration_in_      │
                      └─────────────────────┘      │progress             │
                                                    └─────────────────────┘
                                                             │
                                                             ▼
                      ┌─────────────────────┐
                      │calibration_complete │
                      └─────────────────────┘
                               │
                               │ PHASE TRANSITION
                               ▼
                         PHASE 5: RELEASE & DISCUSSION
                      ┌─────────────────────┐      ┌─────────────────────┐
                      │release_scheduled    │─────▶│released             │
                      └─────────────────────┘      └─────────────────────┘
                                                             │
                                                             ▼
                      ┌─────────────────────┐      ┌─────────────────────┐
                      │discussion_complete  │◀─────│discussion_scheduled │
                      └─────────────────────┘      └─────────────────────┘
                               │
                      ┌────────┴────────┐
                      ▼                 ▼
            ┌─────────────┐   ┌─────────────┐
            │acknowledged │   │  declined   │
            └─────────────┘   └─────────────┘
                      │                 │
                      └────────┬────────┘
                               ▼
                      ┌─────────────────────┐
                      │     COMPLETED       │
                      └─────────────────────┘
```

### Transition Rules

Each transition has:

1. **Trigger Type**:
   - `MANUAL`: User action required
   - `AUTOMATIC`: System-triggered
   - `AGENT`: Agent-driven decision
   - `DEADLINE`: Time-based trigger

2. **Required Conditions**:
   - `employee_selected_peers`: Employee has selected peers
   - `manager_approved_peers`: Manager has approved peer list
   - `self_eval_submitted`: Self-evaluation completed
   - `peer_feedback_complete`: All peer feedback received
   - `manager_eval_finalized`: Manager evaluation complete

3. **Actions on Transition**:
   - `trigger_agents`: Which agents to activate
   - `send_notifications`: Which notifications to send
   - `set_deadlines`: Which deadlines to create

## RAG Pipeline

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG PHASE 1: RETRIEVE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input: evaluation_id                                       │
│                                                             │
│  1. Retrieve peer feedbacks from DocumentStore             │
│  2. Retrieve self-evaluation from DocumentStore            │
│  3. Retrieve historical evaluations for employee           │
│  4. Vector search for similar feedback (semantic)          │
│                                                             │
│  Output: Raw evidence corpus                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG PHASE 2: ANALYZE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Extract themes from each piece of feedback             │
│     - Technical excellence                                  │
│     - Leadership & mentorship                               │
│     - Communication & collaboration                         │
│     - Innovation & problem-solving                          │
│                                                             │
│  2. Build evidence mapping                                  │
│     - Map each claim/theme to supporting evidence          │
│     - Track source (peer name, self-eval, etc.)            │
│                                                             │
│  3. Use reasoning engine (inductive)                        │
│     - Identify patterns across multiple sources            │
│     - Detect contradictions or gaps                         │
│                                                             │
│  Output: Structured themes + evidence map                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG PHASE 3: GENERATE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Cluster themes by category                             │
│     - Technical Assessment                                  │
│     - Leadership & Impact                                   │
│     - Communication & Collaboration                         │
│                                                             │
│  2. Generate section for each category                      │
│     - Include top themes                                    │
│     - Add evidence citations                                │
│     - Use professional tone                                 │
│                                                             │
│  3. Generate overall summary                                │
│     - Synthesize across all categories                      │
│     - Highlight key strengths and growth areas             │
│                                                             │
│  Output: Structured draft evaluation                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  RAG PHASE 4: VALIDATE & QUESTION           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Identify gaps in evidence                               │
│     - Missing technical assessment?                         │
│     - Limited peer feedback count?                          │
│     - No examples for claimed strengths?                    │
│                                                             │
│  2. Generate clarifying questions                           │
│     - Category-specific questions                           │
│     - Priority ranking (high/medium/low)                    │
│                                                             │
│  3. Create interactive Q&A flow for manager                 │
│                                                             │
│  Output: Draft + clarifying questions                       │
└─────────────────────────────────────────────────────────────┘
```

### Evidence Citation Example

```json
{
  "draft_summary": "Jane demonstrated exceptional technical leadership...",
  "evidence_map": {
    "technical_excellence": [
      "Peer feedback from John: 'Led the API migration with deep technical expertise...'",
      "Self-evaluation: 'Architected new microservices platform...'",
      "Historical evaluation (2023): 'Strong technical foundation in distributed systems'"
    ],
    "leadership": [
      "Peer feedback from Sarah: 'Mentored 3 junior engineers...'",
      "Peer feedback from Mike: 'Led incident response with calm authority...'"
    ]
  },
  "clarifying_questions": [
    {
      "question": "Can you provide specific examples of Jane's innovation this cycle?",
      "category": "technical",
      "priority": "high"
    }
  ]
}
```

## Security & RBAC

### Role-Based Access Control

**Roles**:
- `EMPLOYEE`: View own evaluation, submit self-eval, select peers
- `MANAGER`: View direct reports' evaluations, approve peers, write evaluations
- `CALIBRATOR`: View evaluations in calibration, adjust ratings
- `HR_ADMIN`: Full access, configure cycles, view all evaluations
- `SYSTEM_ADMIN`: Full system access, configure agents

**Permissions Matrix**:

| Action | Employee | Manager | Calibrator | HR Admin | System Admin |
|--------|----------|---------|------------|----------|--------------|
| View own evaluation | ✓ | ✓ | ✓ | ✓ | ✓ |
| View direct reports' evaluations | ✗ | ✓ | ✗ | ✓ | ✓ |
| Submit self-evaluation | ✓ | ✓ | ✗ | ✓ | ✓ |
| Select peers | ✓ | ✓ | ✗ | ✓ | ✓ |
| Approve peer selection | ✗ | ✓ | ✗ | ✓ | ✓ |
| Write evaluation | ✗ | ✓ | ✗ | ✓ | ✓ |
| Calibrate ratings | ✗ | ✗ | ✓ | ✓ | ✓ |
| Start evaluation cycle | ✗ | ✗ | ✗ | ✓ | ✓ |
| Configure agents | ✗ | ✗ | ✗ | ✗ | ✓ |

### Data Encryption

**At Rest**:
- All PII encrypted with AES-256
- Database-level encryption for sensitive fields
- Encrypted backups

**In Transit**:
- TLS 1.3 for all API calls
- Encrypted WebSocket connections
- Encrypted agent-to-agent communication

### Audit Logging

All actions logged to immutable audit log:

```python
{
  "timestamp": "2024-12-01T10:30:00Z",
  "actor_id": "uuid",
  "actor_type": "user",  # or "agent" or "system"
  "action": "state_transition",
  "resource_type": "evaluation",
  "resource_id": "eval_uuid",
  "details": {
    "from_state": "peer_list_locked",
    "to_state": "peer_feedback_requested"
  },
  "ip_address": "192.168.1.1",
  "user_agent": "bloom-client/1.0"
}
```

## Scalability

### Horizontal Scaling

**Agent Scaling**:
```python
# Scale Scribe instances based on load
config = BloomConfig(
    num_scribes=5,  # Increase for higher throughput
    num_context_miners=2,
    num_chasers=2,
)
```

**Database Scaling**:
- Read replicas for DocumentStore
- Sharding for VectorStore by employee_id
- Redis cluster for pub/sub
- GraphStore clustering

### Load Balancing

**Adaptive Load Balancing** (IRAS math module):

```python
from iras.math import adaptive_load_balance

# Get agent loads
agent_loads = [
    {"id": agent.id, "current_load": agent.workload}
    for agent in self.scribes
]

# Define task
tasks = [{"id": "synthesis_task", "load": 0.2}]

# Allocate task to least-loaded agent
allocation = adaptive_load_balance(tasks, agent_loads)
selected_agent = allocation[0]["agent_id"]
```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| RAG draft generation | < 30 seconds | P95 latency |
| Peer suggestion | < 5 seconds | P95 latency |
| State transition | < 1 second | P99 latency |
| Notification delivery | < 10 seconds | P95 latency |
| Concurrent evaluations | 1000+ | Per orchestrator instance |
| Agent failure recovery | < 30 seconds | Mean time to recovery |

## Design Patterns

### 1. State Machine Pattern
**Used by**: EvaluationStateMachine

**Benefits**:
- Explicit state transitions
- Validation of state changes
- Audit trail of transitions
- Prevents invalid state combinations

### 2. Event-Driven Architecture
**Used by**: PubSubProtocol, Orchestrator

**Benefits**:
- Loose coupling between components
- Asynchronous processing
- Easy to add new event handlers
- Scalable event distribution

### 3. Contract Net Protocol
**Used by**: Task allocation to Scribes

**Benefits**:
- Dynamic load balancing
- Agent autonomy in bidding
- Failure recovery (re-announce task)
- Optimal resource utilization

### 4. RAG (Retrieval Augmented Generation)
**Used by**: Scribe agent

**Benefits**:
- Grounded in evidence
- Reduces hallucination
- Transparent citations
- Leverages historical data

### 5. ETL Pipeline
**Used by**: Context Miner

**Benefits**:
- Modular data sources
- Incremental processing
- Error handling per source
- Cacheable results

### 6. Observer Pattern
**Used by**: State change notifications

**Benefits**:
- Multiple observers can react to same event
- Decoupled event source and listeners
- Easy to add new observers

---

## Conclusion

Bloom's architecture is designed for:
- **Autonomy**: Agents operate independently within guardrails
- **Scalability**: Horizontal scaling of agents and databases
- **Reliability**: Graceful degradation and failure recovery
- **Transparency**: All actions logged and traceable
- **Extensibility**: Easy to add new agents or modify workflows

For deployment guidance, see [DEPLOYMENT.md](./DEPLOYMENT.md).
For API reference, see [API.md](./API.md).
For development guide, see [DEVELOPMENT.md](./DEVELOPMENT.md).
