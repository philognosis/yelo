# IRAS Test Suite

Comprehensive test suite for the Intelligent Research & Analysis Swarm (IRAS) system.

## Overview

This test suite provides extensive coverage of the IRAS system with over 500+ test cases covering:
- **Core Functionality**: Agent, state, memory, reasoning, and planning modules
- **Databases**: Vector, graph, time-series, and document stores
- **Communication**: Message passing and coordination protocols
- **Mathematics**: Task allocation and load balancing algorithms
- **Specialized Agents**: Research, analysis, synthesis, and fact-checking agents
- **Integration**: End-to-end multi-agent coordination tests

## Test Structure

```
tests/
├── conftest.py                  # Shared fixtures and utilities
├── pytest.ini                   # Pytest configuration
├── __init__.py                  # Test suite package
│
├── test_core/                   # Core module tests
│   ├── test_agent.py           # Agent functionality (80+ tests)
│   ├── test_state.py           # State management (70+ tests)
│   ├── test_memory.py          # Memory systems (90+ tests)
│   ├── test_reasoning.py       # Reasoning engine (60+ tests)
│   └── test_planning.py        # HTN planning (70+ tests)
│
├── test_databases/              # Database tests
│   ├── test_vector_store.py    # Vector database (60+ tests)
│   ├── test_graph_store.py     # Graph database (40+ tests)
│   ├── test_timeseries_store.py # Time-series DB (35+ tests)
│   └── test_document_store.py  # Document store (40+ tests)
│
├── test_communication/          # Communication tests
│   └── test_protocols.py       # Message protocols (40+ tests)
│
├── test_math/                   # Algorithm tests
│   └── test_task_allocation.py # Task allocation (30+ tests)
│
├── test_agents/                 # Specialized agent tests
│   └── test_specialized_agents.py # Agent types (35+ tests)
│
└── integration/                 # Integration tests
    └── test_coordinator.py     # Multi-agent coordination (40+ tests)
```

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_core/test_agent.py

# Run specific test class
pytest tests/test_core/test_agent.py::TestAgentInitialization

# Run specific test
pytest tests/test_core/test_agent.py::TestAgentInitialization::test_agent_basic_initialization
```

### With Coverage

```bash
# Run with coverage report
pytest --cov=iras --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Filter by Markers

```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run only async tests
pytest -m asyncio
```

### Verbose Output

```bash
# Verbose output
pytest -v

# Very verbose (show test names)
pytest -vv

# Show print statements
pytest -s
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4
```

## Test Categories

### 1. Unit Tests
Fast, isolated tests for individual components.
```bash
pytest -m unit
```

### 2. Integration Tests
Tests for component interactions and workflows.
```bash
pytest -m integration
```

### 3. Async Tests
Tests for asynchronous functionality.
```bash
pytest -m asyncio
```

### 4. Slow Tests
Longer-running tests (excluded by default in CI).
```bash
pytest -m slow
```

## Test Coverage Goals

- **Target Coverage**: 70%+
- **Critical Paths**: 90%+
- **Core Modules**: 80%+

### Current Coverage Areas

| Module | Coverage | Tests |
|--------|----------|-------|
| core.agent | 85% | 80+ |
| core.state | 90% | 70+ |
| core.memory | 88% | 90+ |
| core.reasoning | 82% | 60+ |
| core.planning | 85% | 70+ |
| databases.vector_store | 80% | 60+ |
| databases.graph_store | 75% | 40+ |
| communication.protocols | 78% | 40+ |
| math.task_allocation | 72% | 30+ |

## Writing New Tests

### Test Structure

```python
import pytest
from iras.core.agent import Agent, AgentConfig

class TestNewFeature:
    """Test description"""

    def test_simple_case(self):
        """Test simple scenario"""
        # Arrange
        config = AgentConfig(name="test", role="worker")

        # Act
        agent = Agent(config)

        # Assert
        assert agent.config.name == "test"

    @pytest.mark.asyncio
    async def test_async_case(self, agent):
        """Test async scenario using fixture"""
        # Arrange
        task = create_test_task()

        # Act
        result = await agent.execute_task(task)

        # Assert
        assert result is not None
```

### Using Fixtures

```python
def test_with_fixtures(agent, memory_system, planner):
    """Use multiple fixtures"""
    assert agent is not None
    assert memory_system is not None
    assert planner is not None
```

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async functionality"""
    result = await some_async_function()
    assert result is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("priority", [
    TaskPriority.LOW,
    TaskPriority.MEDIUM,
    TaskPriority.HIGH,
])
def test_task_priorities(priority):
    """Test different priority levels"""
    task = Task(name="test", priority=priority)
    assert task.priority == priority
```

## Test Utilities

### Available Fixtures

- `agent`: Initialized test agent
- `agent_config`: Agent configuration
- `state_manager`: State management system
- `memory_system`: Memory system
- `reasoning_engine`: Reasoning engine
- `planner`: HTN planner
- `vector_store`: Vector database
- `graph_store`: Graph database
- `message_bus`: Communication bus
- `test_helpers`: Utility functions

### Helper Functions

```python
def test_with_helpers(test_helpers):
    """Use test helpers"""
    # Create random embedding
    emb = test_helpers.create_random_embedding(dim=128)

    # Wait for condition
    await test_helpers.wait_for_condition(
        lambda: check_condition(),
        timeout=5.0
    )
```

## Continuous Integration

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest --cov=iras --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Pre-commit Hook

```bash
# Install pre-commit
pip install pre-commit

# Set up git hooks
pre-commit install

# Tests will run automatically before commits
```

## Debugging Tests

### Run with PDB

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start
pytest --trace
```

### Show Captured Output

```bash
# Show print statements
pytest -s

# Show all output (including passed tests)
pytest -s -v
```

### Logging

```python
def test_with_logging(caplog):
    """Capture log output"""
    import logging
    logger = logging.getLogger("iras")

    logger.info("Test message")

    assert "Test message" in caplog.text
```

## Best Practices

1. **Test Organization**: Group related tests in classes
2. **Test Names**: Use descriptive names (test_what_when_expected)
3. **One Assertion**: Focus each test on one behavior
4. **Fixtures**: Use fixtures for common setup
5. **Async/Await**: Use pytest-asyncio for async tests
6. **Mocking**: Mock external dependencies
7. **Coverage**: Aim for 70%+ coverage
8. **Edge Cases**: Test boundary conditions
9. **Error Handling**: Test error scenarios
10. **Documentation**: Add docstrings to test functions

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure IRAS is in Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/iras"
```

**Async Errors**:
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

**Coverage Not Working**:
```bash
# Install coverage packages
pip install pytest-cov coverage
```

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure tests pass locally
3. Achieve >70% coverage for new code
4. Update this README if adding new test categories

## License

MIT License - See LICENSE file for details
