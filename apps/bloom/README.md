# 🌸 Bloom - Employee Evaluation & Growth Engine

**Version:** 1.0.0
**Built on:** IRAS (Intelligent Research & Analysis Swarm) Framework

Bloom is an AI-powered, multi-agent autonomous system for employee performance evaluations that combines zero-UI philosophy with modern dashboards to streamline and enhance the entire evaluation process.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
  - [Docker Deployment (Recommended)](#docker-deployment-recommended)
  - [Manual Installation](#manual-installation)
- [Usage Examples](#usage-examples)
- [Agent Descriptions](#agent-descriptions)
- [Workflow Phases](#workflow-phases)
- [Configuration](#configuration)
- [Production Deployment](#production-deployment)
- [API & Dashboard](#api--dashboard)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
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

## 🚀 Quick Start

### Docker Deployment (Recommended)

The fastest way to get Bloom running is with Docker:

```bash
# 1. Clone the repository
git clone <repository-url>
cd apps/bloom

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration
# At minimum, set: ANTHROPIC_API_KEY or OPENAI_API_KEY

# 3. Start all services (one command!)
./start.sh

# That's it! Bloom is now running.
```

**Access Points:**
- 📊 **Dashboard**: http://localhost:3000
- 🔌 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🗄️ **Database Admin**: http://localhost:5432 (PostgreSQL)

**What Gets Deployed:**
- Bloom API (FastAPI backend)
- Next.js Dashboard (React frontend)
- PostgreSQL (document storage)
- Redis (caching & pub/sub)
- Qdrant (vector database for RAG)

**Optional Services:**
```bash
# Start with all services (Neo4j graph DB + InfluxDB metrics)
./start.sh --full

# Start with Nginx reverse proxy
./start.sh --nginx

# Run in foreground (see logs in terminal)
./start.sh --fg
```

**Stop Services:**
```bash
# Stop all services (preserve data)
./stop.sh

# Stop and remove all data
./stop.sh --volumes
```

---

### Manual Installation

If you prefer to run without Docker:

#### Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Node.js 20+** (for dashboard)
- **PostgreSQL 15+**
- **Redis 7+**
- **Qdrant** (optional, for production RAG)

#### Backend Setup

```bash
# 1. Navigate to Bloom directory
cd apps/bloom

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install IRAS core (required dependency)
pip install -e ../../src/iras

# 4. Install Bloom dependencies
pip install -r requirements.txt

# 5. Install Bloom as package
pip install -e .

# 6. Configure environment
cp .env.example .env
# Edit .env with your settings

# 7. Initialize databases
python -c "
from bloom.orchestrator import BloomOrchestrator, BloomConfig
import asyncio

async def init():
    config = BloomConfig()
    orch = BloomOrchestrator(config)
    await orch.initialize()
    print('✓ Databases initialized')

asyncio.run(init())
"

# 8. Run tests to verify installation
pytest tests/ -v

# 9. Start API server
uvicorn bloom.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Dashboard Setup

```bash
# 1. Navigate to dashboard directory
cd dashboard

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

# 4. Run development server
npm run dev

# Dashboard will be available at http://localhost:3000
```

---

### Quick Example: Run a Simple Evaluation

Once Bloom is running, try this example:

```bash
# Run the simple evaluation example
cd apps/bloom
python examples/simple_evaluation.py
```

This will:
1. Create a test employee
2. Start an evaluation cycle
3. Generate AI peer suggestions
4. Simulate peer feedback submissions
5. Create self-evaluation
6. Generate AI manager draft
7. Complete manager evaluation

**Expected Output:**
```
=== Simple Evaluation Workflow Example ===
[Step 1] Initializing Bloom orchestrator...
✓ Orchestrator initialized successfully
[Step 2] Creating employee record...
✓ Created employee: Jane Doe (jane.doe@company.com)
[Step 3] Starting evaluation cycle...
✓ Evaluation created: <evaluation-id>
...
[Step 10] Final evaluation summary...
Evaluation Complete!
  Overall rating: exceeds
  Promotion: ready_next_cycle
```

For more examples, see the [Usage Examples](#usage-examples) section below.

## 💡 Usage Examples

Bloom provides multiple example workflows demonstrating different use cases.

### Example 1: Simple Evaluation Workflow

The simplest way to see Bloom in action:

```bash
python examples/simple_evaluation.py
```

This demonstrates a complete evaluation workflow for a single employee, including:
- Creating employee records
- Generating AI peer suggestions
- Submitting peer feedback
- Creating self-evaluations
- Generating AI manager drafts
- Completing manager evaluations

**Code snippet:**
```python
from bloom.orchestrator import BloomOrchestrator, BloomConfig
from bloom.models import Employee, Person, EmployeeLevel, EmployeeRole

# Initialize Bloom
config = BloomConfig(
    num_scribes=1,
    num_context_miners=1,
    enable_autonomous_mode=False,  # Manual control for demo
    enable_rag=True,
)

orchestrator = BloomOrchestrator(config)
await orchestrator.initialize()

# Create employee
employee = Employee(
    person=Person(
        name="Jane Doe",
        email="jane.doe@company.com",
        title="Senior Software Engineer",
        level=EmployeeLevel.L3,
        role=EmployeeRole.INDIVIDUAL_CONTRIBUTOR,
    )
)

# Start evaluation cycle
evaluation_ids = await orchestrator.start_evaluation_cycle(
    cycle_name="Q4 2024",
    employees=[employee],
)

# Process peer selection
result = await orchestrator.process_peer_selection(
    evaluation_id=evaluation_ids[0],
    employee_id=employee.person.id,
)

# ... continue with workflow
```

---

### Example 2: Bulk Evaluation Cycle

Process evaluations for a large cohort:

```bash
python examples/bulk_cycle.py
```

This demonstrates:
- Batch evaluation creation
- Parallel processing with multiple agents
- Progress monitoring across cohorts
- Real-time metrics tracking

---

### Example 3: Manager AI Workflow

See how managers interact with AI drafts:

```bash
python examples/manager_workflow.py
```

This demonstrates:
- AI-generated evaluation drafts
- Evidence-based citations
- Clarifying questions from AI
- Manager review and editing process
- Final submission

---

### Example 4: Dashboard Demo

Run the interactive dashboard:

```bash
python examples/dashboard_demo.py
```

Then open http://localhost:3000 to see:
- Real-time evaluation status
- Multi-role dashboards (Employee, Manager, HR Admin)
- Live WebSocket updates
- Interactive evaluation editing

---

### Programmatic API Examples

#### Process Peer Selection

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

#### Submit Peer Feedback

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

#### Generate Manager Draft

```python
# Generate AI-assisted evaluation draft
draft = await orchestrator.generate_manager_draft(
    evaluation_id=eval_id,
)

print(f"Draft Summary: {draft.ai_draft_summary}")
print(f"Evidence Citations: {len(draft.ai_draft_evidence_map)} claims")
print(f"Clarifying Questions: {len(draft.ai_questions)}")
```

#### Monitor Swarm Status

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

---

## 🚢 Production Deployment

### Using the Deployment Script

For production deployments, use the provided deployment script:

```bash
# Deploy to production
./deploy.sh

# Deploy to staging
./deploy.sh --env staging

# Skip tests (not recommended)
./deploy.sh --skip-tests

# Skip database backup
./deploy.sh --skip-backup
```

**What the deployment script does:**
1. ✅ Validates environment configuration
2. ✅ Runs full test suite
3. ✅ Backs up existing database
4. ✅ Pulls latest code changes
5. ✅ Builds fresh Docker images
6. ✅ Performs zero-downtime deployment
7. ✅ Runs health checks
8. ✅ Cleans up old images

### Production Checklist

Before deploying to production, ensure:

- [ ] `.env` configured with production values
- [ ] `JWT_SECRET` set to secure random string (min 32 chars)
- [ ] Database passwords changed from defaults
- [ ] LLM API keys configured (Anthropic or OpenAI)
- [ ] SMTP settings configured for emails
- [ ] Slack tokens configured (if using Slack integration)
- [ ] SSL certificates configured (for HTTPS)
- [ ] Backup strategy implemented
- [ ] Monitoring and logging configured

### Environment Configuration

Critical production settings:

```bash
# .env
BLOOM_ENV=production
LOG_LEVEL=info

# Security (MUST CHANGE!)
JWT_SECRET=<64-character-random-string>
POSTGRES_PASSWORD=<secure-password>
NEO4J_PASSWORD=<secure-password>

# LLM Provider
ANTHROPIC_API_KEY=sk-ant-xxxxx
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022

# Features
BLOOM_ENABLE_AUTONOMOUS_MODE=true
BLOOM_ENABLE_RAG=true

# Integrations
SLACK_BOT_TOKEN=xoxb-xxxxx
SMTP_HOST=smtp.gmail.com
SMTP_USER=bloom@company.com
```

See `.env.example` for complete configuration options.

---

## 🌐 API & Dashboard

### REST API

The Bloom API provides full programmatic access:

**Base URL:** `http://localhost:8000`

**Key Endpoints:**
- `POST /api/v1/evaluations/cycles` - Start evaluation cycle
- `GET /api/v1/evaluations/{id}` - Get evaluation details
- `POST /api/v1/evaluations/{id}/peers/suggest` - Get peer suggestions
- `POST /api/v1/feedback/peer` - Submit peer feedback
- `POST /api/v1/feedback/self` - Submit self-evaluation
- `POST /api/v1/evaluations/{id}/draft` - Generate manager draft
- `GET /api/v1/swarm/status` - Get agent swarm status

**Interactive Docs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Dashboard

The Next.js dashboard provides role-based interfaces:

**Employee View** (`/employee`)
- My evaluations
- Peer selection
- Self-evaluation form
- Evaluation results

**Manager View** (`/manager`)
- Team evaluations
- AI draft review
- Evaluation editing
- Calibration prep

**HR Admin View** (`/hr`)
- Cycle management
- Analytics dashboard
- Cohort scheduling
- System configuration

**Committee View** (`/committee`)
- Calibration sessions
- Rating distribution
- Declined evaluations review

### WebSocket Real-Time Updates

Connect to WebSocket for live updates:

```typescript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Real-time update:', update);
};
```

---

## 🧪 Testing

Bloom includes a comprehensive test suite with 196+ tests.

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=bloom --cov-report=html

# Run specific test file
pytest tests/test_agents/test_scribe.py -v

# Run specific test
pytest tests/test_agents/test_scribe.py::test_scribe_rag_pipeline -v
```

### Test Categories

**Model Tests** (51 tests)
- Employee and person models
- Evaluation workflow models
- Data validation

**Agent Tests** (71 tests)
- Watchkeeper orchestration
- ContextMiner peer selection
- **Scribe RAG pipeline** (32 tests)
- Chaser notifications
- Gatekeeper RBAC
- Analyst metrics

**Workflow Tests** (25 tests)
- State machine transitions
- Phase handlers
- Deadline management

**API Tests** (24 tests)
- REST endpoints
- WebSocket connections
- Authentication

**Integration Tests** (25 tests)
- Slack integration
- Email integration
- Calendar sync

### Test Fixtures

Comprehensive fixtures available in `tests/conftest.py`:
- Sample employees and evaluations
- Mock databases
- Mock integrations
- Test configurations

---

## 🔧 Troubleshooting

### Common Issues

**Issue: API won't start**
```bash
# Check logs
docker-compose logs api

# Verify environment
docker-compose exec api env | grep -E "(ANTHROPIC|POSTGRES)"

# Restart API
docker-compose restart api
```

**Issue: Database connection errors**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U bloom -d bloom -c "SELECT 1;"

# Reset database
./stop.sh --volumes
./start.sh
```

**Issue: Dashboard can't connect to API**
```bash
# Verify API is accessible
curl http://localhost:8000/health

# Check dashboard environment
docker-compose exec dashboard env | grep NEXT_PUBLIC_API_URL

# Restart dashboard
docker-compose restart dashboard
```

**Issue: Out of memory errors**
```bash
# Check Docker resources
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → 8GB+

# Reduce agent pool sizes in .env
BLOOM_NUM_SCRIBES=1
BLOOM_NUM_CONTEXT_MINERS=1
```

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=debug

# Restart services
docker-compose restart
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Dashboard health
curl http://localhost:3000/api/health

# Database health
docker-compose exec postgres pg_isready

# Agent swarm status
curl http://localhost:8000/api/v1/swarm/status
```

---

## 📚 Documentation

- **[Architecture Overview](../../docs/ARCHITECTURE.md)** - System design and components
- **[Agent Specifications](./docs/AGENTS.md)** - Detailed agent descriptions
- **[API Reference](./docs/API.md)** - Complete REST API documentation
- **[Development Guide](./docs/DEVELOPMENT.md)** - Contributing and extending Bloom
- **[Deployment Guide](./docs/DEPLOYMENT.md)** - Production deployment details

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) for details

---

## 💬 Support

For questions and support:
- **GitHub Issues**: [Create an issue](../../issues)
- **Documentation**: [Bloom Docs](./docs/)
- **Email**: bloom-support@company.com

---

## 🗺️ Roadmap

### Version 1.1 (Q1 2025)
- [ ] Advanced RAG with fine-tuned embeddings
- [ ] Multi-language support (Spanish, French, German)
- [ ] Mobile app (iOS/Android)
- [ ] Slack App Directory submission

### Version 1.2 (Q2 2025)
- [ ] 360-degree feedback support
- [ ] Skills gap analysis and recommendations
- [ ] Career path planning
- [ ] Integration with LinkedIn Learning

### Version 2.0 (Q3 2025)
- [ ] Automated goal tracking from Jira/GitHub
- [ ] Predictive analytics for retention risk
- [ ] Advanced calibration algorithms
- [ ] Custom evaluation templates

---

## 🙏 Acknowledgments

Built with:
- **[IRAS Framework](../../src/iras/)** - Multi-agent AI system foundation
- **[Anthropic Claude](https://anthropic.com)** - LLM for AI synthesis
- **[FastAPI](https://fastapi.tiangolo.com)** - Modern Python web framework
- **[Next.js](https://nextjs.org)** - React framework for dashboards
- **[Pydantic](https://pydantic.dev)** - Data validation

---

<p align="center">
  Built with ❤️ using the IRAS Multi-Agent Framework
</p>

<p align="center">
  <strong>Bloom</strong> - Making performance evaluations delightful 🌸
</p>
