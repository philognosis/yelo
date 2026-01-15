"""
Pytest Configuration and Fixtures for Bloom Tests

Provides common fixtures for testing Bloom components including:
- Mock employees and evaluations
- Mock databases
- Mock orchestrator
- Async test configuration
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, Mock

from bloom.models.employee import (
    Certification,
    Employee,
    EmployeeLevel,
    EmployeeRole,
    Person,
    Skill,
    SkillArea,
    SkillLevel,
    Training,
    CalendarMetric,
    TeamHours,
)
from bloom.models.evaluation import (
    Evaluation,
    EvaluationPhase,
    EvaluationState,
    ManagerEvaluation,
    PeerFeedback,
    PromotionEligibility,
    Rating,
    SelfEvaluation,
)
from bloom.orchestrator import BloomConfig, BloomOrchestrator


# ============================================================================
# Async Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Employee Fixtures
# ============================================================================


@pytest.fixture
def mock_person() -> Person:
    """Mock Person model"""
    return Person(
        id=uuid4(),
        name="Jane Doe",
        email="jane.doe@company.com",
        title="Senior Software Engineer",
        location="San Francisco, CA",
        region="NAM",
        level=EmployeeLevel.L3,
        sub_level=2,
        role=EmployeeRole.INDIVIDUAL_CONTRIBUTOR,
        manager_id=uuid4(),
        hire_date=date(2020, 6, 15),
        last_promotion_date=date(2022, 1, 1),
        is_active=True,
    )


@pytest.fixture
def mock_manager_person() -> Person:
    """Mock manager Person model"""
    return Person(
        id=uuid4(),
        name="John Manager",
        email="john.manager@company.com",
        title="Engineering Manager",
        location="San Francisco, CA",
        region="NAM",
        level=EmployeeLevel.L4,
        sub_level=1,
        role=EmployeeRole.MANAGER,
        manager_id=uuid4(),
        hire_date=date(2018, 3, 1),
        is_active=True,
    )


@pytest.fixture
def mock_skills() -> List[Skill]:
    """Mock skills list"""
    person_id = uuid4()
    return [
        Skill(
            person_id=person_id,
            name="Python",
            level=SkillLevel.EXPERT,
            area=SkillArea.TECHNICAL,
            sub_type="Programming Language",
            acquired_date=date(2020, 1, 1),
            last_used_date=date.today(),
            evidence_links=["https://github.com/jane/project1"],
        ),
        Skill(
            person_id=person_id,
            name="Team Leadership",
            level=SkillLevel.ADVANCED,
            area=SkillArea.LEADERSHIP,
            acquired_date=date(2021, 6, 1),
            last_used_date=date.today(),
        ),
        Skill(
            person_id=person_id,
            name="Technical Writing",
            level=SkillLevel.INTERMEDIATE,
            area=SkillArea.COMMUNICATION,
        ),
    ]


@pytest.fixture
def mock_certifications() -> List[Certification]:
    """Mock certifications list"""
    person_id = uuid4()
    return [
        Certification(
            person_id=person_id,
            name="AWS Solutions Architect - Professional",
            issuer="Amazon Web Services",
            passed_on=date(2023, 3, 15),
            valid_till=date(2026, 3, 15),
            skills_earned=["Cloud Architecture", "AWS Services"],
            certificate_url="https://aws.com/cert/12345",
            credential_id="AWS-12345",
        ),
    ]


@pytest.fixture
def mock_trainings() -> List[Training]:
    """Mock trainings list"""
    person_id = uuid4()
    return [
        Training(
            person_id=person_id,
            name="Advanced Leadership Program",
            provider="Internal L&D",
            training_type="instructor-led",
            started_on=date(2023, 8, 1),
            completed_on=date(2023, 9, 30),
            skills_earned=["Strategic Planning", "Team Management"],
            score=95.0,
            duration_hours=40,
        ),
    ]


@pytest.fixture
def mock_calendar_metrics() -> List[CalendarMetric]:
    """Mock calendar metrics"""
    person_id = uuid4()
    return [
        CalendarMetric(
            person_id=person_id,
            peer_id=uuid4(),
            total_hours=45.5,
            total_last_yr=30.0,
            total_ytd=12.5,
            total_last_2_years=40.0,
            total_previous_two_yrs=5.5,
            total_days=28,
            total_meetings=42,
            last_meeting_date=date.today(),
            relationship_strength=0.85,
        ),
        CalendarMetric(
            person_id=person_id,
            peer_id=uuid4(),
            total_hours=60.0,
            total_last_yr=50.0,
            total_ytd=20.0,
            total_days=35,
            total_meetings=58,
            relationship_strength=0.92,
        ),
    ]


@pytest.fixture
def mock_team_hours() -> List[TeamHours]:
    """Mock team hours"""
    person_id = uuid4()
    return [
        TeamHours(
            person_id=person_id,
            team_id=uuid4(),
            team_name="Platform Engineering",
            group="Engineering",
            hours=20.0,
            total_hours=520.0,
            total_last_yr=400.0,
            total_ytd=180.0,
            total_days=150,
            role_in_team="Tech Lead",
        ),
    ]


@pytest.fixture
def mock_employee(
    mock_person,
    mock_skills,
    mock_certifications,
    mock_trainings,
    mock_calendar_metrics,
    mock_team_hours,
) -> Employee:
    """Mock complete Employee model"""
    return Employee(
        person=mock_person,
        skills=mock_skills,
        certifications=mock_certifications,
        trainings=mock_trainings,
        calendar_metrics=mock_calendar_metrics,
        team_hours=mock_team_hours,
    )


@pytest.fixture
def mock_employees(mock_person) -> List[Employee]:
    """Mock list of employees"""
    employees = []
    for i in range(5):
        person = Person(
            id=uuid4(),
            name=f"Employee {i+1}",
            email=f"employee{i+1}@company.com",
            title="Software Engineer",
            location="Remote",
            region="NAM",
            level=EmployeeLevel.L3,
            sub_level=0,
            role=EmployeeRole.INDIVIDUAL_CONTRIBUTOR,
            manager_id=uuid4(),
            hire_date=date(2020, 1, 1),
        )
        employees.append(Employee(person=person))
    return employees


# ============================================================================
# Evaluation Fixtures
# ============================================================================


@pytest.fixture
def mock_peer_feedback() -> PeerFeedback:
    """Mock peer feedback"""
    return PeerFeedback(
        evaluation_id=uuid4(),
        peer_id=uuid4(),
        peer_name="Bob Smith",
        raw_input="Jane did a great job on the API migration project. She handled the database issues really well.",
        input_method="text",
        synthesized_feedback="Demonstrated exceptional technical leadership on API migration, resolving complex database challenges.",
        technical_rating=Rating.EXCEEDS,
        leadership_rating=Rating.MEETS,
        communication_rating=Rating.MEETS,
        synthesized_at=datetime.now(),
    )


@pytest.fixture
def mock_peer_feedbacks() -> List[PeerFeedback]:
    """Mock list of peer feedbacks"""
    eval_id = uuid4()
    return [
        PeerFeedback(
            evaluation_id=eval_id,
            peer_id=uuid4(),
            peer_name=f"Peer {i+1}",
            raw_input=f"Great collaboration with this person on project {i+1}",
            synthesized_feedback=f"Strong technical collaboration demonstrated on project {i+1}",
            technical_rating=Rating.EXCEEDS if i % 2 == 0 else Rating.MEETS,
        )
        for i in range(5)
    ]


@pytest.fixture
def mock_self_evaluation() -> SelfEvaluation:
    """Mock self evaluation"""
    return SelfEvaluation(
        evaluation_id=uuid4(),
        employee_id=uuid4(),
        raw_achievements="Led the API migration from v1 to v2, resulting in 40% performance improvement...",
        raw_challenges="Faced challenges with legacy system compatibility",
        raw_growth_areas="Want to improve system design skills",
        raw_goals="Become tech lead for platform team",
        synthesized_achievements="Successfully led critical API migration delivering significant performance gains",
        uploaded_docs=[
            {"name": "API_Migration_Deck.pdf", "url": "https://docs.com/1"},
        ],
        project_links=["https://github.com/company/api-migration"],
        synthesized_at=datetime.now(),
    )


@pytest.fixture
def mock_manager_evaluation() -> ManagerEvaluation:
    """Mock manager evaluation"""
    return ManagerEvaluation(
        evaluation_id=uuid4(),
        manager_id=uuid4(),
        employee_id=uuid4(),
        ai_draft_summary="Based on analysis of 5 peer reviews and self-evaluation, employee demonstrates strong technical excellence...",
        ai_draft_evidence_map={
            "technical_excellence": ["Peer feedback 1", "Self-eval achievement 1"],
            "leadership": ["Peer feedback 2", "Peer feedback 3"],
        },
        ai_questions=[
            {"question": "Can you provide more context on the API migration impact?", "category": "technical"},
        ],
        ai_generated_at=datetime.now(),
        final_summary="Jane demonstrated exceptional technical leadership on the API migration project...",
        technical_assessment="Expert-level technical skills with strong architecture understanding",
        leadership_assessment="Growing leadership skills, mentored 2 junior engineers",
        growth_opportunities="System design and scalability planning",
        overall_rating=Rating.EXCEEDS,
        technical_rating=Rating.EXCEEDS,
        leadership_rating=Rating.MEETS,
        communication_rating=Rating.MEETS,
        promotion_eligibility=PromotionEligibility.READY_NEXT_CYCLE,
        promotion_justification="Demonstrated consistent excellence and growing leadership",
        submitted_at=datetime.now(),
    )


@pytest.fixture
def mock_evaluation(mock_employee, mock_manager_person) -> Evaluation:
    """Mock evaluation"""
    return Evaluation(
        id=uuid4(),
        employee_id=mock_employee.person.id,
        manager_id=mock_manager_person.id,
        cycle_name="Q4 2024",
        current_phase=EvaluationPhase.CONTEXT_PEER_SELECTION,
        current_state=EvaluationState.CYCLE_STARTED,
        peer_selection_deadline=datetime.now() + timedelta(days=7),
        peer_feedback_deadline=datetime.now() + timedelta(days=21),
        self_eval_deadline=datetime.now() + timedelta(days=21),
        manager_eval_deadline=datetime.now() + timedelta(days=35),
        calibration_date=datetime.now() + timedelta(days=42),
        release_date=datetime.now() + timedelta(days=49),
    )


@pytest.fixture
def mock_evaluation_with_data(
    mock_evaluation,
    mock_peer_feedbacks,
    mock_self_evaluation,
    mock_manager_evaluation,
) -> Evaluation:
    """Mock evaluation with all data populated"""
    eval_with_data = mock_evaluation.model_copy(deep=True)
    eval_with_data.suggested_peers = [uuid4() for _ in range(5)]
    eval_with_data.employee_selected_peers = eval_with_data.suggested_peers[:5]
    eval_with_data.manager_approved_peers = eval_with_data.suggested_peers[:5]
    eval_with_data.peer_feedbacks = mock_peer_feedbacks
    eval_with_data.self_evaluation = mock_self_evaluation
    eval_with_data.manager_evaluation = mock_manager_evaluation
    eval_with_data.current_phase = EvaluationPhase.MANAGER_EVALUATION
    eval_with_data.current_state = EvaluationState.AI_DRAFT_GENERATED
    return eval_with_data


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def mock_document_store():
    """Mock DocumentStore"""
    store = AsyncMock()
    store.insert = AsyncMock(return_value="mock_id")
    store.find_by_id = AsyncMock(return_value=None)
    store.find = AsyncMock(return_value=[])
    store.update = AsyncMock(return_value=True)
    store.delete = AsyncMock(return_value=True)
    store.count = AsyncMock(return_value=0)
    store.create_index = AsyncMock(return_value=True)
    store.get_statistics = MagicMock(return_value={"total_documents": 0})
    return store


@pytest_asyncio.fixture
async def mock_vector_store():
    """Mock VectorStore"""
    store = AsyncMock()
    store.add_document = AsyncMock(return_value="mock_id")
    store.search = AsyncMock(return_value=[])
    store.get_statistics = MagicMock(return_value={"total_vectors": 0})
    return store


@pytest_asyncio.fixture
async def mock_graph_store():
    """Mock GraphStore"""
    store = AsyncMock()
    store.add_node = AsyncMock(return_value=True)
    store.add_edge = AsyncMock(return_value=True)
    store.get_neighbors = AsyncMock(return_value=[])
    store.get_centrality = AsyncMock(return_value={})
    store.detect_communities = AsyncMock(return_value={})
    store.get_statistics = MagicMock(return_value={"num_nodes": 0, "num_edges": 0})
    return store


@pytest_asyncio.fixture
async def mock_timeseries_store():
    """Mock TimeSeriesStore"""
    store = AsyncMock()
    store.write_point = AsyncMock(return_value=True)
    store.query = AsyncMock(return_value=[])
    store.get_statistics = MagicMock(return_value={"total_points": 0})
    return store


# ============================================================================
# Orchestrator Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def mock_orchestrator(
    mock_document_store,
    mock_vector_store,
    mock_graph_store,
    mock_timeseries_store,
):
    """Mock BloomOrchestrator"""
    config = BloomConfig(
        num_scribes=1,
        num_context_miners=1,
        num_chasers=1,
        enable_autonomous_mode=False,
    )

    orchestrator = BloomOrchestrator(config)

    # Replace databases with mocks
    orchestrator.document_store = mock_document_store
    orchestrator.vector_store = mock_vector_store
    orchestrator.graph_store = mock_graph_store
    orchestrator.timeseries_store = mock_timeseries_store

    # Mock key methods
    orchestrator.initialize = AsyncMock()
    orchestrator.shutdown = AsyncMock()
    orchestrator.start_evaluation_cycle = AsyncMock(return_value=[uuid4()])
    orchestrator.process_peer_selection = AsyncMock(return_value={"suggested_peers": []})
    orchestrator.process_peer_feedback = AsyncMock()
    orchestrator.generate_manager_draft = AsyncMock()
    orchestrator.get_evaluation = AsyncMock(return_value=None)
    orchestrator._update_evaluation = AsyncMock()

    orchestrator.is_running = True

    return orchestrator


# ============================================================================
# Agent Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def mock_watchkeeper(mock_document_store, mock_timeseries_store):
    """Mock Watchkeeper agent"""
    from bloom.agents.watchkeeper import Watchkeeper

    watchkeeper = Watchkeeper(
        document_store=mock_document_store,
        timeseries_store=mock_timeseries_store,
    )
    watchkeeper.initialize = AsyncMock()
    return watchkeeper


@pytest_asyncio.fixture
async def mock_context_miner(mock_document_store, mock_graph_store):
    """Mock ContextMiner agent"""
    from bloom.agents.context_miner import ContextMiner

    miner = ContextMiner(
        document_store=mock_document_store,
        graph_store=mock_graph_store,
    )
    miner.initialize = AsyncMock()
    return miner


@pytest_asyncio.fixture
async def mock_scribe(mock_document_store, mock_vector_store):
    """Mock Scribe agent"""
    from bloom.agents.scribe import Scribe

    scribe = Scribe(
        document_store=mock_document_store,
        vector_store=mock_vector_store,
    )
    scribe.initialize = AsyncMock()
    return scribe


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user"""
    from bloom.api.auth import User, UserRole

    return User(
        id=uuid4(),
        email="test@company.com",
        name="Test User",
        role=UserRole.EMPLOYEE,
    )


@pytest.fixture
def mock_auth_manager():
    """Mock authenticated manager"""
    from bloom.api.auth import User, UserRole

    return User(
        id=uuid4(),
        email="manager@company.com",
        name="Test Manager",
        role=UserRole.MANAGER,
    )


@pytest.fixture
def mock_auth_hr_admin():
    """Mock authenticated HR admin"""
    from bloom.api.auth import User, UserRole

    return User(
        id=uuid4(),
        email="hr@company.com",
        name="HR Admin",
        role=UserRole.HR_ADMIN,
    )


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing"""
    return datetime(2024, 12, 1, 12, 0, 0)


@pytest.fixture
def sample_feedback_text() -> str:
    """Sample feedback text for testing"""
    return """
    Um, so like, Jane did a really great job on the API migration project.
    She, you know, handled all the database issues really well and, uh,
    helped the team ship on time. Kind of amazing work.
    """


@pytest.fixture
def sample_clean_feedback_text() -> str:
    """Expected clean version of sample feedback"""
    return "Jane did a really great job on the API migration project. She handled all the database issues really well and helped the team ship on time. Amazing work."
