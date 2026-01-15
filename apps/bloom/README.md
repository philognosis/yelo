# Bloom - Employee Evaluation & Growth Engine

**Version:** 0.1.0
**Built on:** IRAS (Intelligent Research & Analysis Swarm) Framework

Bloom is a zero-UI, autonomous multi-agent system for performance evaluations that leverages AI to streamline and enhance the entire evaluation process.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
- [Agent Descriptions](#agent-descriptions)
- [Workflow Phases](#workflow-phases)
- [Configuration](#configuration)
- [Documentation Links](#documentation-links)

## Overview

Bloom transforms the traditional performance evaluation process by:

- **Autonomous Operation**: Agents orchestrate the entire workflow with minimal human intervention
- **AI-Assisted Drafting**: Generates evidence-based evaluation drafts using RAG (Retrieval Augmented Generation)
- **Intelligent Peer Selection**: Automatically suggests peer reviewers based on collaboration data
- **Zero-UI Design**: Operates through Slack, email, and voice interactions
- **Multi-Agent Coordination**: Six specialized agents work together to manage the evaluation lifecycle

### What Makes Bloom Different?

Traditional evaluation systems require managers to manually:
- Select peer reviewers
- Chase down feedback submissions
- Synthesize feedback from multiple sources
- Write evaluations from scratch

Bloom automates 80% of this work while maintaining transparency and human oversight.

## Key Features

### 🤖 Multi-Agent System
- **6 Specialized Agents**: Each with distinct responsibilities
- **Autonomous Coordination**: Agents communicate via blackboard and pub/sub patterns
- **Intelligent Load Balancing**: Distributes work across agent instances

### 🎯 RAG-Powered Evaluation Drafting
- Ingests peer feedback, self-evaluations, and historical data
- Generates evidence-based drafts with citation trails
- Asks clarifying questions to fill knowledge gaps
- Maintains transparency with source attribution

### 📊 Data-Driven Peer Selection
- Analyzes calendar, Jira, Git, and Slack collaboration patterns
- Calculates relationship strength scores
- Suggests optimal peer reviewers automatically
- Uses graph analytics to identify key collaborators

### 🔔 Intelligent Deadline Management
- Automated reminder scheduling
- Escalation workflows for missed deadlines
- Multi-channel notifications (Slack, email, in-app)
- Real-time progress tracking

### 🔒 Security & RBAC
- Role-based access control (RBAC)
- Data encryption at rest and in transit
- Audit trails for all state transitions
- Configurable approval workflows

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Bloom Orchestrator                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Multi-Agent Swarm (IRAS-based)             │  │
│  │                                                       │  │
│  │  Watchkeeper (1)  → Monitors & orchestrates cycles   │  │
│  │  ContextMiner (1+) → Analyzes collaboration data     │  │
│  │  Scribe (2+)       → AI synthesis & RAG pipeline     │  │
│  │  Chaser (1+)       → Deadline enforcement            │  │
│  │  Gatekeeper (1)    → Security & RBAC                 │  │
│  │  Analyst (1)       → Metrics & calibration           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Communication Protocols                  │  │
│  │  • BlackboardSystem  • PubSubProtocol                │  │
│  │  • ContractNet       • EventBus                      │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Database Layer (IRAS)                    │  │
│  │  • DocumentStore  → Evaluations, employees, feedback │  │
│  │  • VectorStore    → RAG embeddings                   │  │
│  │  • GraphStore     → Collaboration networks           │  │
│  │  • TimeSeriesStore → Metrics & trends                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    Slack API     Email SMTP      Calendar API    Jira API
```

### System Layers

1. **Orchestration Layer**: BloomOrchestrator manages agent lifecycle and coordination
2. **Agent Layer**: Specialized agents perform domain-specific tasks
3. **Communication Layer**: IRAS protocols enable agent collaboration
4. **Data Layer**: Multiple database types for different data patterns
5. **Integration Layer**: External system connectors (Slack, Jira, Git, Calendar)

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL (for DocumentStore)
- Redis (for caching)
- API keys for: Slack, Email provider, Calendar service

### Basic Setup

```python
from bloom import BloomOrchestrator, BloomConfig
from bloom.models import Employee, Person
import asyncio

async def main():
    # Configure Bloom
    config = BloomConfig(
        num_scribes=2,
        num_context_miners=1,
        enable_autonomous_mode=True,
        enable_rag=True,
        slack_enabled=True,
        email_enabled=True,
    )

    # Initialize orchestrator
    orchestrator = BloomOrchestrator(config)
    await orchestrator.initialize()

    # Start evaluation cycle
    employees = [
        # Your employee list
    ]

    evaluation_ids = await orchestrator.start_evaluation_cycle(
        cycle_name="Q4 2024",
        employees=employees,
    )

    print(f"Started {len(evaluation_ids)} evaluations")

    # Monitor system health
    status = await orchestrator.get_swarm_status()
    print(f"System health: {status}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Installation

### From Source

```bash
# Clone repository
git clone <repository-url>
cd apps/bloom

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize databases
python scripts/init_databases.py

# Run tests
pytest tests/

# Start Bloom orchestrator
python main.py
```

### Docker

```bash
# Build image
docker build -t bloom:latest .

# Run container
docker-compose up -d

# Check logs
docker-compose logs -f bloom
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

## Usage Examples

### Example 1: Process Peer Selection

```python
# Generate peer suggestions using ContextMiner
result = await orchestrator.process_peer_selection(
    evaluation_id=eval_id,
    employee_id=employee_id,
)

print(f"Suggested {len(result['suggested_peers'])} peers")
for peer in result['suggested_peers']:
    print(f"  - {peer['peer_name']}: {peer['justification']}")
```

### Example 2: Submit Peer Feedback

```python
# Submit raw feedback (voice or text)
feedback = await orchestrator.process_peer_feedback(
    evaluation_id=eval_id,
    peer_id=peer_id,
    raw_feedback="Jane did exceptional work on the API migration...",
    input_method="voice",  # or "text"
)

print(f"Synthesized: {feedback.synthesized_feedback}")
```

### Example 3: Generate Manager Draft

```python
# Generate AI-assisted evaluation draft
draft = await orchestrator.generate_manager_draft(
    evaluation_id=eval_id,
)

print(f"Draft Summary: {draft.ai_draft_summary}")
print(f"Evidence Citations: {len(draft.ai_draft_evidence_map)} claims")
print(f"Clarifying Questions: {len(draft.ai_questions)}")
```

### Example 4: Get Swarm Status

```python
# Monitor agent health and performance
status = await orchestrator.get_swarm_status()

print(f"Orchestrator: {status['orchestrator_id']}")
print(f"Active Evaluations: {status['active_evaluations']}")
print(f"Watchkeeper Status: {status['agents']['watchkeeper']['status']}")
print(f"Scribe Instances: {len(status['agents']['scribes'])}")
```

## Agent Descriptions

### Watchkeeper (Orchestrator)
- **Role**: System orchestrator and lifecycle manager
- **Responsibilities**:
  - Monitors evaluation deadlines
  - Triggers state transitions
  - Manages cohort scheduling (L6, L5, L4, IC)
  - Coordinates agent activities via HTN planning
  - Tracks system health
- **Key Features**: Cron-style scheduling, autonomous workflow advancement

### Context Miner (Data Engineer)
- **Role**: Collaboration data analyst
- **Responsibilities**:
  - Connects to Calendar, Jira, Git, Slack APIs
  - Calculates relationship strength scores
  - Generates peer reviewer suggestions
  - Builds collaboration network graphs
- **Key Features**: Multi-source data integration, graph analytics

### Scribe (AI Synthesis Engine)
- **Role**: Content generation and RAG pipeline
- **Responsibilities**:
  - Synthesizes peer feedback into professional narratives
  - Generates manager evaluation drafts using RAG
  - Cleans voice dictation
  - Maintains evidence citation trails
  - Asks clarifying questions to fill gaps
- **Key Features**: RAG pipeline, evidence mapping, voice-to-text cleanup

### Chaser (Deadline Enforcer)
- **Role**: Deadline monitoring and notification
- **Responsibilities**:
  - Monitors all evaluation deadlines
  - Sends automated reminders (configurable schedule)
  - Escalates to managers when deadlines are missed
  - Tracks notification delivery and engagement
- **Key Features**: Multi-channel notifications, escalation workflows

### Gatekeeper (Security Controller)
- **Role**: Access control and data protection
- **Responsibilities**:
  - Enforces RBAC policies
  - Validates state transitions
  - Audits all data access
  - Ensures data privacy and compliance
- **Key Features**: Role-based permissions, audit logging

### Analyst (Metrics & Calibration)
- **Role**: Analytics and calibration support
- **Responsibilities**:
  - Generates evaluation metrics and trends
  - Supports calibration committee with data
  - Identifies rating distribution patterns
  - Detects anomalies and biases
- **Key Features**: Statistical analysis, calibration support

## Workflow Phases

Bloom orchestrates evaluations through **5 main phases**:

### Phase 1: Context & Peer Selection
```
States: cycle_started → peer_suggestion_generated → employee_peer_review
        → manager_peer_approval → peer_list_locked
```

**Actions**:
1. Context Miner analyzes collaboration data
2. Generates AI-suggested peer list (5-7 peers)
3. Employee reviews and modifies suggestions
4. Manager approves final peer list

**Deadline**: 7 days (configurable)

### Phase 2: Data Gathering
```
States: peer_feedback_requested → peer_feedback_in_progress
        → self_eval_requested → self_eval_in_progress
        → data_gathering_complete
```

**Actions**:
1. Chaser sends feedback requests to approved peers
2. Scribe synthesizes submitted peer feedback
3. Employee submits self-evaluation
4. All data collected and stored in vector DB

**Deadline**: 14 days for feedback, 14 days for self-eval

### Phase 3: Manager Evaluation
```
States: manager_eval_started → ai_draft_generated
        → manager_review_in_progress → manager_eval_complete
```

**Actions**:
1. Scribe generates RAG-based evaluation draft
2. Draft includes evidence citations and clarifying questions
3. Manager reviews, edits, and finalizes evaluation
4. Manager submits ratings and promotion recommendation

**Deadline**: 21 days (configurable)

### Phase 4: Calibration
```
States: calibration_pending → calibration_in_progress → calibration_complete
```

**Actions**:
1. Analyst prepares calibration data and metrics
2. Calibration committee reviews rating distribution
3. Adjustments made to ensure fairness
4. Final ratings locked

**Deadline**: Based on calibration session scheduling

### Phase 5: Release & Discussion
```
States: release_scheduled → released → discussion_scheduled
        → discussion_complete → acknowledged/declined → completed
```

**Actions**:
1. Evaluation released to employee
2. Discussion meeting scheduled (auto-added to calendar)
3. Manager and employee discuss evaluation
4. Employee acknowledges or declines (committee review if declined)

**Deadline**: 7 days post-release for acknowledgment

## Configuration

### BloomConfig Options

```python
config = BloomConfig(
    # Agent Counts
    num_scribes=2,              # Number of Scribe instances (2-5 recommended)
    num_context_miners=1,       # Number of ContextMiner instances
    num_chasers=1,              # Number of Chaser instances

    # Features
    enable_autonomous_mode=True,     # Enable autonomous agent operation
    enable_rag=True,                 # Enable RAG for draft generation
    enable_voice_synthesis=True,     # Enable voice-to-text processing

    # Deadlines (in days)
    peer_selection_deadline_days=7,
    peer_feedback_deadline_days=14,
    self_eval_deadline_days=14,
    manager_eval_deadline_days=21,
    calibration_days=7,

    # Notifications
    notification_channels=["slack", "email", "in_app"],
    slack_enabled=True,
    email_enabled=True,

    # Performance
    max_concurrent_evaluations=100,
    health_check_interval_minutes=5,

    # Database
    use_production_databases=False,  # Use production or in-memory DBs
)
```

### Environment Variables

```bash
# Database
POSTGRES_URL=postgresql://user:pass@localhost/bloom
REDIS_URL=redis://localhost:6379

# Integrations
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=bloom@company.com

# Calendar
GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json

# LLM Provider
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key

# Security
BLOOM_SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

## API Documentation

See [API.md](./API.md) for complete API reference including:
- REST endpoints
- WebSocket protocol
- Authentication flow
- Example requests and responses

## Development

See [DEVELOPMENT.md](./DEVELOPMENT.md) for:
- Project structure
- Adding new agents
- Extending workflows
- Testing guidelines
- Code style guide
- Contributing guidelines

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- Production deployment guide
- Docker setup
- Kubernetes manifests
- Monitoring and logging
- Troubleshooting

## Architecture Deep Dive

See [ARCHITECTURE.md](./ARCHITECTURE.md) for:
- System layers and components
- Agent swarm design patterns
- Database schema
- Communication protocols
- State machine workflow
- RAG pipeline details
- Security and RBAC
- Scalability considerations

## Documentation Links

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Technical architecture and design
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Deployment and operations guide
- **[API.md](./API.md)** - Complete API documentation
- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - Developer guide and best practices

## License

[Your License Here]

## Support

For questions and support:
- GitHub Issues: [link]
- Slack Channel: #bloom-support
- Email: bloom-support@company.com

## Roadmap

**Q1 2025**:
- [ ] Advanced RAG with fine-tuned models
- [ ] Multi-language support
- [ ] Mobile app integration

**Q2 2025**:
- [ ] 360-degree feedback support
- [ ] Skills gap analysis
- [ ] Career path recommendations

**Q3 2025**:
- [ ] Integration with learning platforms
- [ ] Automated goal tracking
- [ ] Predictive analytics for retention

---

Built with ❤️ using the IRAS Multi-Agent Framework
