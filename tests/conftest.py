"""
Pytest Configuration and Shared Fixtures

Provides:
- Common fixtures for all tests
- Test utilities and helpers
- Mock objects and data generators
- Async test support configuration
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime
from uuid import uuid4
from typing import Dict, List, Any

# Import main IRAS components for fixtures
from iras.core.agent import Agent, AgentConfig
from iras.core.state import StateManager, AgentStatus
from iras.core.memory import MemorySystem
from iras.core.reasoning import ReasoningEngine
from iras.core.planning import HTNPlanner, Task, TaskPriority
from iras.databases.vector_store import VectorStore
from iras.databases.graph_store import GraphStore
from iras.databases.timeseries_store import TimeSeriesStore
from iras.databases.document_store import DocumentStore
from iras.communication.protocols import MessageBus


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest settings"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# ============================================================================
# Event Loop Fixture
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Core Component Fixtures
# ============================================================================

@pytest.fixture
def agent_config():
    """Basic agent configuration"""
    return AgentConfig(
        name="test_agent",
        role="tester",
        capabilities={"test_capability"},
    )


@pytest.fixture
async def agent(agent_config):
    """Create a test agent"""
    agent = Agent(agent_config)
    await agent.initialize()
    yield agent
    await agent.shutdown()


@pytest.fixture
def state_manager():
    """Create a state manager"""
    return StateManager(agent_id=uuid4())


@pytest.fixture
def memory_system():
    """Create a memory system"""
    return MemorySystem(
        working_capacity=20,
        episodic_capacity=100,
    )


@pytest.fixture
def reasoning_engine():
    """Create a reasoning engine"""
    return ReasoningEngine()


@pytest.fixture
def planner():
    """Create an HTN planner"""
    return HTNPlanner()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
async def vector_store():
    """Create a vector store"""
    vs = VectorStore(embedding_dim=128)
    yield vs
    await vs.clear()


@pytest.fixture
async def graph_store():
    """Create a graph store"""
    gs = GraphStore()
    yield gs
    await gs.clear()


@pytest.fixture
async def timeseries_store():
    """Create a time-series store"""
    ts = TimeSeriesStore()
    yield ts
    await ts.clear()


@pytest.fixture
async def document_store():
    """Create a document store"""
    ds = DocumentStore()
    yield ds
    await ds.clear()


# ============================================================================
# Communication Fixtures
# ============================================================================

@pytest.fixture
def message_bus():
    """Create a message bus"""
    return MessageBus()


# ============================================================================
# Data Generator Fixtures
# ============================================================================

@pytest.fixture
def random_embedding():
    """Generate random embedding vector"""
    def _generator(dim=128):
        return np.random.rand(dim)
    return _generator


@pytest.fixture
def sample_task():
    """Create a sample task"""
    def _create_task(name="test_task", **kwargs):
        return Task(
            name=name,
            description=kwargs.get("description", "Test task"),
            priority=kwargs.get("priority", TaskPriority.MEDIUM),
            **kwargs
        )
    return _create_task


@pytest.fixture
def sample_agent_config():
    """Create sample agent configuration"""
    def _create_config(**kwargs):
        return AgentConfig(
            name=kwargs.get("name", "test_agent"),
            role=kwargs.get("role", "worker"),
            capabilities=kwargs.get("capabilities", set()),
        )
    return _create_config


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        {
            "id": "doc1",
            "content": "The quick brown fox jumps over the lazy dog",
            "metadata": {"category": "A", "author": "Alice"},
        },
        {
            "id": "doc2",
            "content": "Machine learning is a subset of artificial intelligence",
            "metadata": {"category": "B", "author": "Bob"},
        },
        {
            "id": "doc3",
            "content": "Neural networks are inspired by biological neurons",
            "metadata": {"category": "B", "author": "Alice"},
        },
    ]


@pytest.fixture
def sample_graph_data():
    """Sample graph data for testing"""
    return {
        "nodes": [
            {"id": "n1", "type": "person", "props": {"name": "Alice"}},
            {"id": "n2", "type": "person", "props": {"name": "Bob"}},
            {"id": "n3", "type": "company", "props": {"name": "ACME"}},
        ],
        "edges": [
            {"from": "n1", "to": "n3", "type": "works_at"},
            {"from": "n2", "to": "n3", "type": "works_at"},
            {"from": "n1", "to": "n2", "type": "knows"},
        ],
    }


@pytest.fixture
def sample_timeseries_data():
    """Sample time-series data"""
    now = datetime.now()
    return [
        {"timestamp": now, "value": 10.0, "metric": "cpu"},
        {"timestamp": now, "value": 20.0, "metric": "memory"},
        {"timestamp": now, "value": 5.0, "metric": "disk"},
    ]


# ============================================================================
# Utility Functions
# ============================================================================

class TestHelpers:
    """Helper functions for tests"""

    @staticmethod
    async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
        """Wait for a condition to become true"""
        elapsed = 0.0
        while elapsed < timeout:
            if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
                return True
            await asyncio.sleep(interval)
            elapsed += interval
        return False

    @staticmethod
    def create_random_embedding(dim=128, seed=None):
        """Create reproducible random embedding"""
        if seed is not None:
            np.random.seed(seed)
        return np.random.rand(dim)

    @staticmethod
    async def create_sample_plan(planner, goal="Test goal", num_tasks=3):
        """Create a sample plan with multiple tasks"""
        plan = await planner.create_plan(goal=goal, auto_decompose=False)

        # Add subtasks
        root_task = plan.tasks[plan.root_task]
        for i in range(num_tasks):
            task = Task(
                name=f"subtask_{i}",
                description=f"Subtask {i}",
                parent_task=root_task.id,
            )
            plan.tasks[task.id] = task
            root_task.subtasks.append(task.id)

        return plan

    @staticmethod
    async def populate_vector_store(vector_store, num_docs=10, dim=128):
        """Populate vector store with test data"""
        doc_ids = []
        for i in range(num_docs):
            doc_id = await vector_store.add(
                content=f"Document {i}",
                embedding=np.random.rand(dim),
                metadata={"index": i, "category": f"cat_{i % 3}"},
            )
            doc_ids.append(doc_id)
        return doc_ids


@pytest.fixture
def test_helpers():
    """Provide test helper functions"""
    return TestHelpers


# ============================================================================
# Mock Objects
# ============================================================================

class MockLLM:
    """Mock LLM for testing"""

    def __init__(self, response="Mock response"):
        self.response = response
        self.call_count = 0

    async def generate(self, prompt, **kwargs):
        """Mock generation"""
        self.call_count += 1
        return self.response

    async def embed(self, text):
        """Mock embedding"""
        return np.random.rand(128)


@pytest.fixture
def mock_llm():
    """Provide mock LLM"""
    return MockLLM()


# ============================================================================
# Performance Testing Utilities
# ============================================================================

@pytest.fixture
def performance_tracker():
    """Track performance metrics in tests"""
    class PerformanceTracker:
        def __init__(self):
            self.metrics = {}

        def record(self, name, value):
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(value)

        def get_average(self, name):
            if name in self.metrics:
                return sum(self.metrics[name]) / len(self.metrics[name])
            return 0.0

        def get_stats(self, name):
            if name in self.metrics:
                values = np.array(self.metrics[name])
                return {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                }
            return {}

    return PerformanceTracker()


# ============================================================================
# Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup():
    """Automatic cleanup after each test"""
    yield
    # Cleanup code here if needed
    await asyncio.sleep(0)  # Allow pending tasks to complete


# ============================================================================
# Test Markers
# ============================================================================

# Slow tests marker
slow = pytest.mark.slow

# Integration tests marker
integration = pytest.mark.integration

# Async tests marker (pytest-asyncio provides this, but we define for clarity)
async_test = pytest.mark.asyncio
