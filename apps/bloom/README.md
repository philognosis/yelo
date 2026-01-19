# 🌸 Bloom - Employee Evaluation & Growth Engine

**Version:** 1.0.0
**Built on:** IRAS (Intelligent Research & Analysis Swarm) Framework

Bloom is an AI-powered, multi-agent autonomous system for employee performance evaluations that combines zero-UI philosophy with modern dashboards to streamline and enhance the entire evaluation process.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start (3 Steps!)](#quick-start-3-steps)
- [Installation Methods](#installation-methods)
  - [Method 1: Docker (Recommended)](#method-1-docker-recommended)
  - [Method 2: Local with uv](#method-2-local-with-uv)
  - [Method 3: Local with pip](#method-3-local-with-pip)
- [Architecture](#architecture)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## Overview

Bloom transforms the traditional performance evaluation process by:

- **🤖 Autonomous Operation**: Agents orchestrate the entire workflow with minimal human intervention
- **🎯 AI-Assisted Drafting**: Generates evidence-based evaluation drafts using RAG (Retrieval Augmented Generation)
- **📊 Intelligent Peer Selection**: Automatically suggests peer reviewers based on collaboration data
- **⚡ Zero-UI Design**: Operates through Slack, email, and voice interactions
- **🔄 Multi-Agent Coordination**: Six specialized agents work together to manage the evaluation lifecycle

### What Makes Bloom Different?

Traditional evaluation systems require managers to manually:
- Select peer reviewers
- Chase down feedback submissions
- Synthesize feedback from multiple sources
- Write evaluations from scratch

Bloom automates 80% of this work while maintaining transparency and human oversight.

---

## 🚀 Quick Start (3 Steps!)

Get Bloom running in under 5 minutes:

### Step 1: Get an LLM API Key

Choose ONE provider and get an API key:

| Provider | Get Key | Free Tier | Best For |
|----------|---------|-----------|----------|
| **Anthropic Claude** | [console.anthropic.com](https://console.anthropic.com/) | No | Best quality |
| **OpenAI GPT** | [platform.openai.com](https://platform.openai.com/api-keys) | No | Well-known |
| **Google Gemini** | [makersuite.google.com](https://makersuite.google.com/app/apikey) | ✅ Yes | Free option |

### Step 2: Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd yelo/apps/bloom

# Copy environment template
cp .env.example .env

# Edit .env and add your API key (choose one):
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# OPENAI_API_KEY=sk-your-key-here
# GEMINI_API_KEY=your-key-here

# Set your provider:
# LLM_PROVIDER=anthropic  # or openai, or gemini
```

**Minimal .env configuration:**
```bash
# Required: Choose ONE
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# OR
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# OR
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Required: Set provider
LLM_PROVIDER=anthropic  # Match the key you provided above

# Optional: Model selection
LLM_MODEL=claude-3-5-sonnet-20241022  # or gpt-4-turbo, or gemini-pro
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

### Step 3: Start Bloom

```bash
# From apps/bloom directory
./start.sh

# That's it! 🎉
```

**Access Bloom:**
- 📊 **Dashboard**: http://localhost:3000
- 🔌 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

**Test it works:**
```bash
# Run a simple evaluation example
docker-compose exec api python examples/simple_evaluation.py
```

---

## 📦 Installation Methods

Choose the method that fits your workflow:

### Method 1: Docker (Recommended) ⭐

**Best for:** Production, quick start, no local Python setup needed

**Prerequisites:**
- Docker Desktop or Docker Engine
- docker-compose

**Steps:**

```bash
# 1. Navigate to Bloom
cd yelo/apps/bloom

# 2. Configure environment
cp .env.example .env
# Edit .env - add at least one LLM API key

# 3. Start everything
./start.sh

# 4. Verify it's running
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# 5. Try an example
docker-compose exec api python examples/simple_evaluation.py
```

**Docker Options:**
```bash
# Start with all services (Neo4j + InfluxDB)
./start.sh --full

# Start with Nginx reverse proxy
./start.sh --nginx

# Run in foreground (see logs)
./start.sh --fg

# Stop services
./stop.sh

# Stop and remove all data
./stop.sh --volumes
```

**What Docker deploys:**
- ✅ Bloom API (FastAPI backend)
- ✅ Dashboard (Next.js React frontend)
- ✅ PostgreSQL (document storage)
- ✅ Redis (caching & pub/sub)
- ✅ Qdrant (vector database for RAG)
- ⭐ Optional: Neo4j (graph database)
- ⭐ Optional: InfluxDB (time-series metrics)

---

### Method 2: Local with uv ⚡

**Best for:** Development, fastest dependency installation

**Prerequisites:**
- Python 3.10+ (3.11 recommended)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- PostgreSQL 15+ (running locally)
- Redis 7+ (running locally)

**Install uv:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Steps:**

```bash
# 1. Navigate to repository root
cd yelo

# 2. Install IRAS framework
cd src/iras
uv pip install -e .

# 3. Install Bloom
cd ../../apps/bloom
uv pip install -e .

# 4. Configure environment
cp .env.example .env
# Edit .env - add LLM API key and database settings

# 5. Initialize databases (if needed)
# Make sure PostgreSQL and Redis are running locally

# 6. Run tests
uv run pytest tests/ -v

# 7. Start API server
uv run uvicorn bloom.api.main:app --host 0.0.0.0 --port 8000 --reload

# 8. In another terminal, start dashboard
cd dashboard
npm install
npm run dev
```

**Access:**
- API: http://localhost:8000
- Dashboard: http://localhost:3000

---

### Method 3: Local with pip 🐍

**Best for:** Traditional Python workflows

**Prerequisites:**
- Python 3.10+ (3.11 recommended)
- PostgreSQL 15+ (running locally)
- Redis 7+ (running locally)

**Steps:**

```bash
# 1. Navigate to repository root
cd yelo

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install IRAS framework
pip install -e src/iras

# 4. Install Bloom
pip install -e apps/bloom

# 5. Configure environment
cp apps/bloom/.env.example apps/bloom/.env
# Edit .env

# 6. Run tests
pytest apps/bloom/tests/ -v

# 7. Start API
uvicorn bloom.api.main:app --host 0.0.0.0 --port 8000 --reload

# 8. Start dashboard (in another terminal)
cd apps/bloom/dashboard
npm install
npm run dev
```

---

## 📖 Step-by-Step Guide: First Evaluation

Once Bloom is running, create your first evaluation:

### 1. Access the Dashboard

Open http://localhost:3000 in your browser.

### 2. Run the Example Script

```bash
# If using Docker:
docker-compose exec api python examples/simple_evaluation.py

# If using local installation:
uv run python examples/simple_evaluation.py
# or
python examples/simple_evaluation.py
```

### 3. What Happens

The example script will:

1. **Initialize Bloom orchestrator**
   ```
   ✓ Orchestrator initialized with 2 Scribes, 2 ContextMiners
   ```

2. **Create a test employee**
   ```
   ✓ Created employee: Jane Doe (jane.doe@company.com)
   ```

3. **Start evaluation cycle**
   ```
   ✓ Evaluation cycle started: Q4 2024
   ```

4. **Generate AI peer suggestions**
   ```
   ✓ Suggested 5 peers based on collaboration data
   ```

5. **Simulate peer feedback**
   ```
   ✓ Processed 5 peer feedback submissions
   ✓ AI synthesized informal feedback into professional narratives
   ```

6. **Create self-evaluation**
   ```
   ✓ Self-evaluation submitted
   ```

7. **Generate AI manager draft**
   ```
   ✓ AI-generated draft using RAG pipeline
   ✓ Evidence citations mapped to peer feedback
   ✓ Clarifying questions generated for manager
   ```

8. **Complete evaluation**
   ```
   ✓ Manager review complete
   ✓ Overall rating: exceeds_expectations
   ✓ Promotion recommendation: ready_next_cycle
   ```

### 4. View in Dashboard

Refresh the dashboard to see:
- Real-time evaluation progress
- AI-generated content
- Evidence citations
- Workflow state transitions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Bloom Orchestrator                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Multi-Agent Swarm (IRAS-based)             │  │
│  │                                                       │  │
│  │  Watchkeeper (1)  → Monitors & orchestrates cycles   │  │
│  │  ContextMiner (2) → Analyzes collaboration data      │  │
│  │  Scribe (2)       → AI synthesis & RAG pipeline      │  │
│  │  Chaser (1)       → Deadline enforcement             │  │
│  │  Gatekeeper (1)   → Security & RBAC                  │  │
│  │  Analyst (1)      → Metrics & calibration            │  │
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
│  │  • DocumentStore  → Evaluations, employees           │  │
│  │  • VectorStore    → RAG embeddings                   │  │
│  │  • GraphStore     → Collaboration networks           │  │
│  │  • TimeSeriesStore → Metrics & trends                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    Slack API     Email SMTP      Calendar API    Jira API
```

**Key Components:**

1. **Orchestration Layer**: BloomOrchestrator manages agent lifecycle
2. **Agent Layer**: 6 specialized AI agents
3. **Communication Layer**: Blackboard, Pub/Sub, Contract Net protocols
4. **Data Layer**: 4 database types for different data patterns
5. **Integration Layer**: Enterprise system connectors

---

## 💡 Usage Examples

### Example 1: Bulk Evaluation Cycle

```bash
docker-compose exec api python examples/bulk_cycle.py
```

Creates evaluations for multiple employees in parallel.

### Example 2: Manager AI Workflow

```bash
docker-compose exec api python examples/manager_workflow.py
```

Demonstrates manager interaction with AI-generated drafts.

### Example 3: Dashboard Demo

```bash
docker-compose exec api python examples/dashboard_demo.py
```

Then open http://localhost:3000 to see real-time updates.

### Programmatic API Usage

```python
from bloom.orchestrator import BloomOrchestrator, BloomConfig
from bloom.models import Employee, Person

# Initialize
config = BloomConfig(
    num_scribes=2,
    enable_rag=True,
    enable_autonomous_mode=True
)

orchestrator = BloomOrchestrator(config)
await orchestrator.initialize()

# Start evaluation cycle
evaluation_ids = await orchestrator.start_evaluation_cycle(
    cycle_name="Q4 2024",
    employees=[employee1, employee2, ...]
)

# Process peer selection
result = await orchestrator.process_peer_selection(
    evaluation_id=evaluation_ids[0],
    employee_id=employee_id
)

# Generate AI draft
draft = await orchestrator.generate_manager_draft(
    evaluation_id=evaluation_ids[0]
)

print(f"AI-generated summary: {draft.ai_draft_summary}")
print(f"Citations: {len(draft.ai_draft_evidence_map)}")
print(f"Questions: {draft.ai_questions}")
```

---

## ⚙️ Configuration

### Environment Variables

Key settings in `.env`:

```bash
# LLM Configuration (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-xxxxx     # Anthropic Claude
OPENAI_API_KEY=sk-xxxxx            # OpenAI GPT
GEMINI_API_KEY=xxxxx               # Google Gemini
LLM_PROVIDER=anthropic             # Which provider to use
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Bloom Configuration
BLOOM_NUM_SCRIBES=2                # Number of Scribe agents
BLOOM_NUM_CONTEXT_MINERS=2         # Number of ContextMiner agents
BLOOM_ENABLE_RAG=true              # Enable RAG pipeline
BLOOM_ENABLE_AUTONOMOUS_MODE=true  # Autonomous agent operation

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_DB=bloom
POSTGRES_USER=bloom
POSTGRES_PASSWORD=secure_password

# Security
JWT_SECRET=your-64-character-random-string
```

See `.env.example` for complete configuration options and detailed explanations.

### LLM Provider Selection

Bloom supports 3 LLM providers. See [LLM Configuration Guide](./docs/LLM_CONFIGURATION.md) for details.

**Quick comparison:**

| Provider | Quality | Speed | Cost/Eval | Free Tier |
|----------|---------|-------|-----------|-----------|
| Anthropic Claude | ⭐⭐⭐⭐⭐ | Fast | $0.05-0.15 | No |
| OpenAI GPT | ⭐⭐⭐⭐ | Fast | $0.03-0.10 | No |
| Google Gemini | ⭐⭐⭐⭐ | Fast | $0.01-0.03 | ✅ Yes |

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Docker
docker-compose exec api pytest tests/ -v

# Local with uv
uv run pytest tests/ -v

# Local with pip
pytest tests/ -v

# With coverage
pytest tests/ --cov=bloom --cov-report=html
```

**Test coverage:** 196+ tests across:
- 51 model tests
- 71 agent tests (including 32 RAG pipeline tests)
- 25 workflow tests
- 24 API tests
- 25 integration tests

---

## 🔧 Troubleshooting

### Issue: API won't start

```bash
# Check logs
docker-compose logs api

# Verify LLM API key
docker-compose exec api env | grep -E "(ANTHROPIC|OPENAI|GEMINI)_API_KEY"

# Restart
docker-compose restart api
```

### Issue: "LLM Client failed to initialize"

**Cause:** Missing or invalid API key

**Solution:**
1. Check `.env` has correct API key
2. Verify key is valid (test at provider console)
3. Ensure `LLM_PROVIDER` matches the key you provided

### Issue: Database connection errors

```bash
# Check PostgreSQL
docker-compose ps postgres

# Reset database
./stop.sh --volumes
./start.sh
```

### Issue: Dashboard can't connect to API

```bash
# Verify API is accessible
curl http://localhost:8000/health

# Check dashboard environment
docker-compose exec dashboard env | grep NEXT_PUBLIC_API_URL
```

### Common Solutions

| Problem | Solution |
|---------|----------|
| Out of memory | Increase Docker memory to 8GB+ |
| Slow responses | Reduce `BLOOM_NUM_SCRIBES` to 1 |
| API key errors | Verify key is active and has credits |
| Port conflicts | Change ports in docker-compose.yml |

**Get Help:**
- Check logs: `docker-compose logs -f`
- Health check: `curl http://localhost:8000/health`
- Agent status: `curl http://localhost:8000/api/v1/swarm/status`

---

## 📚 Documentation

**Comprehensive Guides:**
- **[LLM Configuration](./docs/LLM_CONFIGURATION.md)** - Configure Anthropic, OpenAI, or Gemini (525 lines)
- **[Architecture Overview](../../docs/ARCHITECTURE.md)** - System design and components
- **[API Reference](./docs/API.md)** - REST API documentation
- **[Development Guide](./docs/DEVELOPMENT.md)** - Contributing and extending Bloom

**Quick Links:**
- [Agent Descriptions](#agent-descriptions) - Details on all 6 agents
- [Workflow Phases](#workflow-phases) - 5-phase evaluation process
- [Production Deployment](#production-deployment) - Deploy to production
- [API & Dashboard](#api--dashboard) - Using the API and dashboard

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

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Docker-Ready-brightgreen.svg" alt="Docker Ready">
  <img src="https://img.shields.io/badge/LLM-Anthropic%20%7C%20OpenAI%20%7C%20Gemini-orange.svg" alt="Multi-LLM">
  <img src="https://img.shields.io/badge/Tests-196%2B-success.svg" alt="196+ Tests">
</p>

<p align="center">
  Built with ❤️ using the IRAS Multi-Agent Framework
</p>

<p align="center">
  <strong>Bloom</strong> - Making performance evaluations delightful 🌸
</p>
