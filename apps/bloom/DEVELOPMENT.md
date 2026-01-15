# Bloom Development Guide

Developer guide for contributing to Bloom, including project structure, best practices, and testing guidelines.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Adding New Agents](#adding-new-agents)
- [Extending Workflows](#extending-workflows)
- [Testing Guidelines](#testing-guidelines)
- [Code Style Guide](#code-style-guide)
- [Debugging](#debugging)
- [Performance Optimization](#performance-optimization)
- [Contributing Guidelines](#contributing-guidelines)

## Getting Started

### Development Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd apps/bloom

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies (including dev tools)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Set up local databases (Docker)
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
python scripts/migrate_database.py

# Run tests
pytest

# Start development server
python main.py --env development
```

### Development Dependencies

```txt
# requirements-dev.txt
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
pytest-mock==3.11.1
black==23.7.0
isort==5.12.0
mypy==1.4.1
pylint==2.17.5
flake8==6.0.0
pre-commit==3.3.3
ipython==8.14.0
jupyter==1.0.0
httpx==0.24.1  # for API testing
faker==19.2.0  # for generating test data
```

## Project Structure

```
apps/bloom/
├── __init__.py                 # Package initialization, version info
├── main.py                     # Application entry point
├── orchestrator.py             # Main BloomOrchestrator class
│
├── agents/                     # Agent implementations
│   ├── __init__.py            # Agent exports
│   ├── watchkeeper.py         # Orchestrator agent
│   ├── context_miner.py       # Collaboration analysis
│   ├── scribe.py              # AI synthesis & RAG
│   ├── chaser.py              # Deadline enforcement
│   ├── gatekeeper.py          # Security & RBAC
│   └── analyst.py             # Metrics & calibration
│
├── models/                     # Pydantic data models
│   ├── __init__.py
│   ├── employee.py            # Employee, Person, Skill, etc.
│   ├── evaluation.py          # Evaluation, PeerFeedback, etc.
│   └── workflow.py            # WorkflowEvent, Deadline, etc.
│
├── workflows/                  # Workflow management
│   ├── __init__.py
│   ├── state_machine.py       # EvaluationStateMachine
│   └── phase_handlers.py      # PhaseHandlerFactory
│
├── integrations/              # External system integrations
│   ├── __init__.py
│   ├── slack.py               # Slack API client
│   ├── email.py               # Email SMTP client
│   ├── calendar.py            # Calendar API (Google/Microsoft)
│   ├── jira.py                # Jira API client
│   └── git.py                 # GitHub/GitLab API client
│
├── api/                        # REST API (FastAPI)
│   ├── __init__.py
│   ├── main.py                # FastAPI app setup
│   ├── routes/                # API route handlers
│   │   ├── evaluations.py
│   │   ├── agents.py
│   │   ├── auth.py
│   │   └── metrics.py
│   ├── middleware/            # Middleware (auth, logging, etc.)
│   └── schemas/               # API request/response schemas
│
├── dashboard/                  # Real-time dashboard (optional)
│   ├── __init__.py
│   ├── app.py                 # Dashboard server
│   └── components/            # Dashboard UI components
│
├── config/                     # Configuration management
│   ├── __init__.py
│   ├── settings.py            # Environment-based settings
│   └── logging.py             # Logging configuration
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py            # pytest fixtures
│   ├── unit/                  # Unit tests
│   │   ├── test_agents.py
│   │   ├── test_models.py
│   │   └── test_workflows.py
│   ├── integration/           # Integration tests
│   │   ├── test_api.py
│   │   └── test_orchestrator.py
│   └── e2e/                   # End-to-end tests
│       └── test_evaluation_flow.py
│
├── scripts/                    # Utility scripts
│   ├── init_databases.py      # Initialize database schema
│   ├── migrate_database.py    # Run database migrations
│   ├── seed_data.py           # Seed test data
│   └── benchmark.py           # Performance benchmarks
│
├── docs/                       # Documentation
│   ├── README.md              # This file
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── API.md
│   └── DEVELOPMENT.md
│
├── docker/                     # Docker configuration
│   ├── Dockerfile             # Production image
│   ├── Dockerfile.dev         # Development image
│   └── docker-compose.yml
│
├── .env.example               # Environment variable template
├── .gitignore
├── .pre-commit-config.yaml    # Pre-commit hook configuration
├── pyproject.toml             # Python project metadata
├── requirements.txt           # Production dependencies
└── requirements-dev.txt       # Development dependencies
```

## Development Workflow

### Branch Strategy

```
main                 # Production-ready code
  ├── develop        # Integration branch
      ├── feature/*  # Feature branches
      ├── bugfix/*   # Bug fix branches
      └── hotfix/*   # Critical fixes
```

### Creating a Feature

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/add-new-agent

# Make changes
# ... code ...

# Run tests
pytest tests/

# Run linters
black .
isort .
mypy .
pylint bloom/

# Commit changes
git add .
git commit -m "feat: Add new agent for skill gap analysis"

# Push to remote
git push origin feature/add-new-agent

# Create pull request (GitHub/GitLab)
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Code style changes (formatting)
refactor: Code refactoring
test: Add or update tests
chore: Maintenance tasks
perf: Performance improvements
```

**Examples**:
```
feat(agents): Add skill gap analyzer agent
fix(scribe): Handle empty peer feedback gracefully
docs(api): Update authentication documentation
test(workflows): Add state machine transition tests
```

## Adding New Agents

### Agent Template

```python
"""
[Agent Name] - [One-line description]

Responsibilities:
- Responsibility 1
- Responsibility 2
- Responsibility 3

Design Pattern: [Pattern name]
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger

from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.state import AgentStatus
from iras.databases import DocumentStore


class MyNewAgent(Agent):
    """
    [Detailed agent description]

    Capabilities:
    - Capability 1
    - Capability 2
    """

    def __init__(
        self,
        name: str = "MyNewAgent",
        document_store: Optional[DocumentStore] = None,
    ):
        config = AgentConfig(
            name=name,
            role="agent_role",
            capabilities={
                "capability_1",
                "capability_2",
            },
            temperature=0.3,  # Adjust based on task
            max_tokens=3000,
        )
        super().__init__(config)

        # Database connections
        self.document_store = document_store or DocumentStore()

        # Agent-specific state
        self.agent_state = {}

        # Register tools
        self._register_tools()

        logger.info(f"MyNewAgent '{name}' initialized")

    def _register_tools(self) -> None:
        """Register agent-specific tools"""
        self.register_tool(
            AgentTool(
                name="tool_name",
                description="Tool description",
                parameters={
                    "param1": {"type": "string"},
                },
                function=self.tool_function,
            )
        )

    async def tool_function(
        self,
        param1: str,
    ) -> Dict[str, Any]:
        """
        Tool implementation

        Args:
            param1: Parameter description

        Returns:
            Result dictionary
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason="Executing tool_function",
        )

        try:
            # Implementation
            result = {}

            logger.info(f"Tool function completed")
            return result

        except Exception as e:
            logger.error(f"Tool function failed: {e}")
            raise

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)
```

### Integrating the New Agent

1. **Add to Orchestrator**:

```python
# orchestrator.py

from bloom.agents import MyNewAgent

class BloomOrchestrator:
    def __init__(self, config: BloomConfig):
        # ... existing code ...

        # Initialize new agent
        self.my_new_agent = MyNewAgent(
            document_store=self.document_store,
        )

    async def _initialize_agents(self) -> None:
        # ... existing agents ...

        # Initialize new agent
        await self.my_new_agent.initialize()
        logger.info("MyNewAgent initialized")
```

2. **Add Tests**:

```python
# tests/unit/test_agents.py

import pytest
from bloom.agents import MyNewAgent


@pytest.mark.asyncio
async def test_my_new_agent_initialization():
    """Test agent initialization"""
    agent = MyNewAgent()
    await agent.initialize()

    assert agent.config.name == "MyNewAgent"
    assert "capability_1" in agent.config.capabilities


@pytest.mark.asyncio
async def test_my_new_agent_tool_function():
    """Test agent tool function"""
    agent = MyNewAgent()
    await agent.initialize()

    result = await agent.tool_function(param1="test")

    assert result is not None
    assert "expected_key" in result
```

3. **Update Documentation**:
   - Add agent description to README.md
   - Update ARCHITECTURE.md with agent design
   - Add API endpoints if needed to API.md

## Extending Workflows

### Adding a New State

1. **Define State in Enum**:

```python
# models/evaluation.py

class EvaluationState(str, Enum):
    # ... existing states ...
    MY_NEW_STATE = "my_new_state"
```

2. **Add State Transition**:

```python
# workflows/state_machine.py

def _define_transitions(self) -> None:
    # ... existing transitions ...

    self.transitions.append(
        StateTransition(
            from_state=EvaluationState.EXISTING_STATE,
            to_state=EvaluationState.MY_NEW_STATE,
            trigger=TransitionTrigger.AUTOMATIC,
            description="Transition to my new state",
            required_conditions=["condition_to_check"],
            trigger_agents=["AgentName"],
            send_notifications=["notification_template"],
        )
    )
```

3. **Implement Condition Check**:

```python
# workflows/state_machine.py

def _check_condition(self, evaluation: Evaluation, condition: str) -> bool:
    # ... existing conditions ...

    if condition == "condition_to_check":
        return self._is_condition_met(evaluation)

    return False

def _is_condition_met(self, evaluation: Evaluation) -> bool:
    """Check if condition is met"""
    # Implementation
    return True
```

4. **Add Tests**:

```python
# tests/unit/test_workflows.py

@pytest.mark.asyncio
async def test_transition_to_my_new_state():
    """Test transition to new state"""
    state_machine = EvaluationStateMachine()

    evaluation = create_test_evaluation(
        current_state=EvaluationState.EXISTING_STATE
    )

    # Set up condition
    # ... prepare evaluation ...

    result = await state_machine.transition(
        evaluation=evaluation,
        to_state=EvaluationState.MY_NEW_STATE,
    )

    assert result.success
    assert result.new_state == EvaluationState.MY_NEW_STATE
```

## Testing Guidelines

### Test Structure

```python
# tests/unit/test_example.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bloom.agents import Scribe
from bloom.models import Evaluation


@pytest.fixture
def scribe_agent():
    """Fixture for Scribe agent"""
    return Scribe()


@pytest.fixture
def sample_evaluation():
    """Fixture for sample evaluation"""
    return Evaluation(
        employee_id=UUID("00000000-0000-0000-0000-000000000001"),
        manager_id=UUID("00000000-0000-0000-0000-000000000002"),
        cycle_name="Test Cycle",
    )


@pytest.mark.asyncio
async def test_scribe_synthesize_feedback(scribe_agent, sample_evaluation):
    """Test peer feedback synthesis"""
    # Arrange
    raw_feedback = "Great work on the project"

    # Act
    result = await scribe_agent.synthesize_peer_feedback(
        raw_input=raw_feedback,
        input_method="text",
    )

    # Assert
    assert result["synthesized_text"] is not None
    assert len(result["themes"]) > 0
```

### Test Categories

**Unit Tests** (`tests/unit/`):
- Test individual functions/methods
- Mock external dependencies
- Fast execution (< 1 second each)

**Integration Tests** (`tests/integration/`):
- Test component interactions
- Use test databases
- Medium execution time (< 10 seconds each)

**E2E Tests** (`tests/e2e/`):
- Test complete workflows
- Use all real components
- Slow execution (< 60 seconds each)

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bloom --cov-report=html

# Run specific test file
pytest tests/unit/test_agents.py

# Run specific test
pytest tests/unit/test_agents.py::test_scribe_initialization

# Run tests in parallel
pytest -n auto

# Run only fast tests
pytest -m "not slow"

# Run with verbose output
pytest -v
```

### Test Markers

```python
# Mark slow tests
@pytest.mark.slow
async def test_long_running_operation():
    pass

# Mark integration tests
@pytest.mark.integration
async def test_api_endpoint():
    pass

# Mark tests requiring external services
@pytest.mark.requires_external
async def test_slack_integration():
    pass
```

### Mock Example

```python
@pytest.mark.asyncio
async def test_scribe_with_mocked_llm():
    """Test Scribe with mocked LLM"""
    scribe = Scribe()

    # Mock LLM call
    with patch('iras.llm.generate') as mock_generate:
        mock_generate.return_value = "Mocked response"

        result = await scribe.clean_voice_dictation(
            raw_text="um, like, the project was good"
        )

        assert "um" not in result
        assert "like" not in result
        mock_generate.assert_called_once()
```

## Code Style Guide

### Python Style

Follow [PEP 8](https://pep8.org/) with these additions:

**Line Length**: 100 characters (not 79)

**Imports**:
```python
# Standard library
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

# Third-party
from loguru import logger
from pydantic import BaseModel

# Local
from bloom.agents import Scribe
from bloom.models import Evaluation
```

**Type Hints**:
```python
# Always use type hints
def process_evaluation(
    evaluation_id: UUID,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Process evaluation with options"""
    pass
```

**Docstrings** (Google style):
```python
def complex_function(
    param1: str,
    param2: int,
) -> Dict[str, Any]:
    """
    One-line summary of function.

    Longer description if needed. Explain the purpose,
    behavior, and any important details.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Dictionary containing:
        - key1: Description
        - key2: Description

    Raises:
        ValueError: When param2 is negative

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["key1"])
        "value"
    """
    pass
```

**Async Functions**:
```python
# Async functions should have 'async' in name or be obvious from context
async def fetch_evaluation(evaluation_id: UUID) -> Evaluation:
    """Fetch evaluation from database"""
    pass

# Use 'await' explicitly
result = await fetch_evaluation(eval_id)
```

### Code Formatting

Use automated formatters:

```bash
# Black (code formatter)
black apps/bloom/

# isort (import sorter)
isort apps/bloom/

# Both in one command
black apps/bloom/ && isort apps/bloom/
```

### Linting

```bash
# MyPy (type checker)
mypy apps/bloom/

# Pylint (linter)
pylint apps/bloom/

# Flake8 (style guide enforcement)
flake8 apps/bloom/
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.4.1
    hooks:
      - id: mypy
```

## Debugging

### Logging

```python
from loguru import logger

# Different log levels
logger.debug("Debug information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error occurred")
logger.exception("Exception with traceback")

# Structured logging
logger.info(
    "Evaluation created",
    evaluation_id=str(eval_id),
    employee_id=str(employee_id),
    cycle=cycle_name,
)
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb (enhanced debugger)
import ipdb; ipdb.set_trace()

# Or use built-in breakpoint() (Python 3.7+)
breakpoint()
```

### Debugging Agents

```python
# Enable debug logging for specific agent
from loguru import logger

logger.add(
    "logs/scribe_debug.log",
    filter=lambda record: "Scribe" in record["name"],
    level="DEBUG",
)

# Check agent state
agent_state = scribe.get_state()
print(f"Status: {agent_state.status}")
print(f"Workload: {agent_state.workload}")
print(f"Memory: {agent_state.memory_usage}")
```

### Debugging State Machine

```python
# Visualize state transitions
state_machine = EvaluationStateMachine()
graph = state_machine.get_transition_graph()

# Check valid transitions from current state
valid = state_machine.get_valid_transitions(
    current_state=EvaluationState.PEER_FEEDBACK_IN_PROGRESS,
    current_phase=EvaluationPhase.DATA_GATHERING,
)

for transition in valid:
    print(f"{transition.from_state} -> {transition.to_state}")
```

## Performance Optimization

### Profiling

```python
# Time profiling
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
await orchestrator.process_peer_selection(eval_id, employee_id)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### Memory Profiling

```bash
# Install memory_profiler
pip install memory_profiler

# Run with memory profiling
python -m memory_profiler main.py

# Or decorate function
@profile
def memory_intensive_function():
    pass
```

### Database Query Optimization

```python
# Use indexes
await document_store.create_index("evaluations", "employee_id")
await document_store.create_index("evaluations", "current_state")

# Batch operations
evaluations = await document_store.find(
    collection="evaluations",
    query={"cycle_name": cycle},
    batch_size=100,
)

# Use projections (select only needed fields)
evaluations = await document_store.find(
    collection="evaluations",
    query={},
    projection={"id": 1, "current_state": 1},
)
```

### Caching

```python
from functools import lru_cache
import asyncio

# Sync cache
@lru_cache(maxsize=128)
def expensive_computation(param):
    pass

# Async cache
from aiocache import cached

@cached(ttl=3600)  # Cache for 1 hour
async def fetch_employee_data(employee_id: UUID):
    pass
```

## Contributing Guidelines

### Pull Request Process

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**:
   - Write code
   - Add tests
   - Update documentation

3. **Run Checks**:
   ```bash
   # Format code
   black .
   isort .

   # Run tests
   pytest

   # Run linters
   mypy .
   pylint bloom/
   ```

4. **Commit Changes**:
   ```bash
   git add .
   git commit -m "feat: Your feature description"
   ```

5. **Push and Create PR**:
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub/GitLab
   ```

6. **PR Description Template**:
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] All tests passing

   ## Checklist
   - [ ] Code follows style guide
   - [ ] Documentation updated
   - [ ] Changelog updated
   - [ ] No breaking changes (or documented)
   ```

### Code Review Guidelines

**For Reviewers**:
- Check for correctness and edge cases
- Verify tests are comprehensive
- Ensure documentation is updated
- Look for performance issues
- Verify type hints are correct

**For Authors**:
- Respond to all comments
- Make requested changes
- Update tests as needed
- Keep PR scope focused

### Release Process

1. **Update Version**:
   ```python
   # __init__.py
   __version__ = "0.2.0"
   ```

2. **Update Changelog**:
   ```markdown
   # Changelog

   ## [0.2.0] - 2024-12-01
   ### Added
   - New skill gap analyzer agent
   - Support for 360-degree feedback

   ### Changed
   - Improved RAG pipeline performance
   - Updated peer suggestion algorithm

   ### Fixed
   - Fixed deadline notification race condition
   ```

3. **Create Release Tag**:
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

---

## Additional Resources

- **IRAS Framework Docs**: [Link to IRAS documentation]
- **Python Async Guide**: https://docs.python.org/3/library/asyncio.html
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

For deployment, see [DEPLOYMENT.md](./DEPLOYMENT.md).
For architecture details, see [ARCHITECTURE.md](./ARCHITECTURE.md).
For API reference, see [API.md](./API.md).
