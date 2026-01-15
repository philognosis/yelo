# Bloom Test Suite

Comprehensive test suite for the Bloom AI-powered performance evaluation system.

## Overview

This test suite provides comprehensive coverage of all Bloom components:
- **Models**: Employee and Evaluation data models
- **Agents**: Watchkeeper, ContextMiner, Scribe, and other agents
- **Workflows**: State machine and phase handlers
- **API**: REST endpoints and WebSocket connections
- **Integrations**: Slack, Email, and other external integrations

## Structure

```
tests/
├── conftest.py                      # Shared fixtures and configuration
├── pytest.ini                       # Pytest configuration
├── requirements-test.txt            # Test dependencies
│
├── test_models/
│   ├── test_employee.py            # Employee model tests
│   └── test_evaluation.py          # Evaluation model tests
│
├── test_agents/
│   ├── test_watchkeeper.py         # Watchkeeper agent tests
│   ├── test_context_miner.py       # ContextMiner agent tests
│   └── test_scribe.py              # Scribe agent tests (CRITICAL - RAG pipeline)
│
├── test_workflows/
│   ├── test_state_machine.py       # State machine tests
│   └── test_phase_handlers.py      # Phase handler tests
│
├── test_api/
│   └── test_endpoints.py           # API endpoint tests
│
└── test_integrations/
    ├── test_slack.py               # Slack integration tests
    └── test_email.py               # Email integration tests
```

## Installation

Install test dependencies:

```bash
pip install -r tests/requirements-test.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_agents/test_scribe.py
```

### Run tests with coverage
```bash
pytest --cov=bloom --cov-report=html
```

### Run only unit tests
```bash
pytest -m unit
```

### Run only async tests
```bash
pytest -m asyncio
```

### Run with verbose output
```bash
pytest -v
```

## Test Categories

### Simple Tests
Basic validation tests for models, simple method calls, and initialization.

**Examples:**
- `test_person_creation` - Validate Person model creation
- `test_watchkeeper_initialization` - Verify Watchkeeper initializes correctly
- `test_clean_voice_dictation_simple` - Basic voice cleanup

### Semi-Complex Tests
Tests involving multiple components, state transitions, or data processing.

**Examples:**
- `test_start_evaluation_cycle_simple` - Create evaluation cycle
- `test_suggest_peers_with_scores` - Generate peer suggestions with scoring
- `test_transition_evaluation_state` - State machine transitions

### Complex Tests
End-to-end tests, RAG pipeline tests, and full workflow tests.

**Examples:**
- `test_full_rag_pipeline` - Complete RAG pipeline from retrieval to generation
- `test_evaluation_full_lifecycle` - Evaluation through all phases
- `test_generate_manager_draft_with_evidence_map` - Complete draft generation

## Key Test Files

### conftest.py (CRITICAL)
Provides all shared fixtures:
- Mock employees, evaluations, feedbacks
- Mock databases (DocumentStore, VectorStore, GraphStore, TimeSeriesStore)
- Mock orchestrator and agents
- Authentication fixtures

### test_scribe.py (CRITICAL)
Tests the most critical component - the Scribe agent:
- **Voice Dictation Cleanup**: Removes filler words, fixes grammar
- **Peer Feedback Synthesis**: Converts raw input to professional feedback
- **RAG Pipeline**: 4-phase process for manager draft generation
  - Phase 1: Retrieve evidence
  - Phase 2: Analyze themes
  - Phase 3: Generate draft with citations
  - Phase 4: Generate clarifying questions
- **Evidence Mapping**: Links claims to supporting evidence

### test_state_machine.py
Tests workflow state transitions:
- Valid transition identification
- Condition validation
- Agent triggering
- Notification creation
- Automatic advancement

## Coverage Goals

Target coverage: **70%+**

High-priority coverage areas:
- ✅ Models: 80%+
- ✅ Scribe Agent (RAG): 90%+
- ✅ State Machine: 85%+
- ✅ API Endpoints: 75%+
- ✅ Watchkeeper: 80%+
- ✅ ContextMiner: 75%+

## Fixtures

### Employee Fixtures
- `mock_person` - Basic person model
- `mock_employee` - Complete employee with skills, certs, metrics
- `mock_employees` - List of employees
- `mock_skills`, `mock_certifications`, `mock_trainings`
- `mock_calendar_metrics`, `mock_team_hours`

### Evaluation Fixtures
- `mock_evaluation` - Basic evaluation
- `mock_evaluation_with_data` - Evaluation with all data populated
- `mock_peer_feedback`, `mock_peer_feedbacks`
- `mock_self_evaluation`
- `mock_manager_evaluation`

### Database Fixtures
- `mock_document_store` - Mock DocumentStore
- `mock_vector_store` - Mock VectorStore
- `mock_graph_store` - Mock GraphStore
- `mock_timeseries_store` - Mock TimeSeriesStore

### Agent Fixtures
- `mock_orchestrator` - Mock BloomOrchestrator
- `mock_watchkeeper` - Mock Watchkeeper agent
- `mock_context_miner` - Mock ContextMiner agent
- `mock_scribe` - Mock Scribe agent

### Auth Fixtures
- `mock_auth_user` - Mock employee user
- `mock_auth_manager` - Mock manager user
- `mock_auth_hr_admin` - Mock HR admin

## Best Practices

1. **Use Fixtures**: Always use provided fixtures instead of creating test data manually
2. **Mock External Dependencies**: Mock all external APIs (Slack, Email, etc.)
3. **Test Error Cases**: Include tests for error handling and edge cases
4. **Async Tests**: Use `@pytest.mark.asyncio` for async tests
5. **Descriptive Names**: Use clear, descriptive test function names
6. **Docstrings**: Add docstrings explaining what each test validates

## CI/CD Integration

Tests are automatically run in CI/CD pipeline on:
- Pull requests
- Commits to main branch
- Nightly builds

Required checks:
- All tests must pass
- Coverage must be ≥70%
- No critical security issues

## Debugging Tests

### Run single test with print statements
```bash
pytest tests/test_agents/test_scribe.py::TestScribe::test_scribe_initialization -s
```

### Run with debugging
```bash
pytest --pdb
```

### See full tracebacks
```bash
pytest --tb=long
```

## Contributing

When adding new features to Bloom:
1. Write tests first (TDD)
2. Ensure tests pass locally
3. Maintain or improve coverage
4. Update this README if adding new test categories

## License

Same as Bloom project license.
