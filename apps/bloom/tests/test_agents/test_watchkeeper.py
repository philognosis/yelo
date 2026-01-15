"""
Tests for Watchkeeper Agent

Tests cycle triggering, deadline monitoring, state transitions,
and system health monitoring.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from bloom.agents.watchkeeper import CohortSchedule, Watchkeeper
from bloom.models.evaluation import Evaluation, EvaluationPhase, EvaluationState


class TestWatchkeeper:
    """Test Watchkeeper agent basic functionality"""

    @pytest.mark.asyncio
    async def test_watchkeeper_initialization(self, mock_watchkeeper):
        """Test Watchkeeper initializes correctly"""
        assert mock_watchkeeper.config.name == "Watchkeeper"
        assert "evaluation_orchestration" in mock_watchkeeper.config.capabilities
        assert len(mock_watchkeeper.cohort_schedules) > 0

    @pytest.mark.asyncio
    async def test_default_cohort_schedules(self, mock_watchkeeper):
        """Test default cohort schedules are created"""
        # Should have schedules for different levels
        assert "L6_Q" in mock_watchkeeper.cohort_schedules
        assert "L5_Q" in mock_watchkeeper.cohort_schedules
        assert "L4_Q" in mock_watchkeeper.cohort_schedules
        assert "IC_Q" in mock_watchkeeper.cohort_schedules

    @pytest.mark.asyncio
    async def test_cohort_schedule_configuration(self, mock_watchkeeper):
        """Test cohort schedule has correct configuration"""
        l6_schedule = mock_watchkeeper.cohort_schedules["L6_Q"]
        assert l6_schedule.level == "L6+"
        assert l6_schedule.cycle_start_day == 1
        assert l6_schedule.peer_selection_days > 0


class TestEvaluationCycleManagement:
    """Test evaluation cycle creation and management"""

    @pytest.mark.asyncio
    async def test_start_evaluation_cycle_simple(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test starting a simple evaluation cycle"""
        employee_ids = [uuid4(), uuid4(), uuid4()]

        result = await mock_watchkeeper.start_evaluation_cycle(
            cohort_id="IC_Q",
            cycle_name="Q4 2024",
            employee_ids=employee_ids,
        )

        assert result["success"] is True
        assert result["evaluations_created"] == 3
        assert result["cohort_id"] == "IC_Q"
        assert result["cycle_name"] == "Q4 2024"

    @pytest.mark.asyncio
    async def test_start_evaluation_cycle_invalid_cohort(self, mock_watchkeeper):
        """Test starting cycle with invalid cohort fails"""
        with pytest.raises(ValueError, match="Unknown cohort"):
            await mock_watchkeeper.start_evaluation_cycle(
                cohort_id="INVALID_COHORT",
                cycle_name="Q4 2024",
                employee_ids=[uuid4()],
            )

    @pytest.mark.asyncio
    async def test_start_evaluation_cycle_creates_deadlines(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test that evaluation cycle creates proper deadlines"""
        result = await mock_watchkeeper.start_evaluation_cycle(
            cohort_id="L5_Q",
            cycle_name="Q1 2025",
            employee_ids=[uuid4()],
        )

        assert "deadlines" in result
        assert "peer_selection" in result["deadlines"]
        assert "peer_feedback" in result["deadlines"]

    @pytest.mark.asyncio
    async def test_start_evaluation_cycle_multiple_cohorts(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test starting cycles for different cohorts"""
        # L6 cohort
        result_l6 = await mock_watchkeeper.start_evaluation_cycle(
            cohort_id="L6_Q",
            cycle_name="Q4 2024",
            employee_ids=[uuid4()],
        )

        # IC cohort
        result_ic = await mock_watchkeeper.start_evaluation_cycle(
            cohort_id="IC_Q",
            cycle_name="Q4 2024",
            employee_ids=[uuid4(), uuid4()],
        )

        assert result_l6["success"] is True
        assert result_ic["success"] is True
        assert result_ic["evaluations_created"] == 2


class TestDeadlineMonitoring:
    """Test deadline checking and monitoring"""

    @pytest.mark.asyncio
    async def test_check_deadlines_no_violations(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test checking deadlines with no violations"""
        # Mock evaluations with future deadlines
        mock_document_store.find.return_value = [
            {
                "_id": str(uuid4()),
                "employee_id": str(uuid4()),
                "current_phase": "data_gathering",
                "peer_selection_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
                "peer_feedback_deadline": (datetime.now() + timedelta(days=14)).isoformat(),
                "self_eval_deadline": (datetime.now() + timedelta(days=14)).isoformat(),
                "manager_eval_deadline": (datetime.now() + timedelta(days=21)).isoformat(),
            }
        ]

        result = await mock_watchkeeper.check_deadlines()

        assert result["total_violations"] == 0
        assert result["evaluations_checked"] == 1

    @pytest.mark.asyncio
    async def test_check_deadlines_with_violations(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test checking deadlines with violations"""
        # Mock evaluation with past deadline
        mock_document_store.find.return_value = [
            {
                "_id": str(uuid4()),
                "employee_id": str(uuid4()),
                "current_phase": "context_peer_selection",
                "peer_selection_deadline": (datetime.now() - timedelta(days=2)).isoformat(),
                "peer_feedback_deadline": (datetime.now() + timedelta(days=10)).isoformat(),
                "self_eval_deadline": None,
                "manager_eval_deadline": None,
            }
        ]

        result = await mock_watchkeeper.check_deadlines()

        assert result["total_violations"] > 0
        assert len(result["violations"]["peer_selection"]) == 1
        assert "overdue_hours" in result["violations"]["peer_selection"][0]

    @pytest.mark.asyncio
    async def test_check_deadlines_multiple_violations(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test multiple deadline violations across evaluations"""
        mock_document_store.find.return_value = [
            {
                "_id": str(uuid4()),
                "employee_id": str(uuid4()),
                "current_phase": "data_gathering",
                "peer_selection_deadline": (datetime.now() - timedelta(days=5)).isoformat(),
                "peer_feedback_deadline": (datetime.now() - timedelta(days=1)).isoformat(),
                "self_eval_deadline": None,
                "manager_eval_deadline": None,
            },
            {
                "_id": str(uuid4()),
                "employee_id": str(uuid4()),
                "current_phase": "manager_evaluation",
                "peer_selection_deadline": None,
                "peer_feedback_deadline": None,
                "self_eval_deadline": (datetime.now() - timedelta(days=3)).isoformat(),
                "manager_eval_deadline": None,
            },
        ]

        result = await mock_watchkeeper.check_deadlines()

        assert result["total_violations"] >= 3  # peer_selection, peer_feedback, self_eval


class TestStateTransitions:
    """Test evaluation state transitions"""

    @pytest.mark.asyncio
    async def test_transition_evaluation_state(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test transitioning evaluation to new state"""
        eval_id = uuid4()
        mock_document_store.find_by_id.return_value = {
            "_id": str(eval_id),
            "employee_id": str(uuid4()),
            "current_state": "cycle_started",
            "current_phase": "context_peer_selection",
        }

        result = await mock_watchkeeper.transition_evaluation_state(
            evaluation_id=eval_id,
            new_state=EvaluationState.PEER_SUGGESTION_GENERATED,
            reason="Context Miner completed",
        )

        assert result["success"] is True
        assert result["new_state"] == "peer_suggestion_generated"
        assert result["old_state"] == "cycle_started"

        # Verify update was called
        mock_document_store.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_transition_with_phase_change(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test state transition that also changes phase"""
        eval_id = uuid4()
        mock_document_store.find_by_id.return_value = {
            "_id": str(eval_id),
            "employee_id": str(uuid4()),
            "current_state": "peer_list_locked",
            "current_phase": "context_peer_selection",
        }

        result = await mock_watchkeeper.transition_evaluation_state(
            evaluation_id=eval_id,
            new_state=EvaluationState.PEER_FEEDBACK_REQUESTED,
            new_phase=EvaluationPhase.DATA_GATHERING,
            reason="Starting data gathering",
        )

        assert result["success"] is True
        assert result["new_phase"] == "data_gathering"

    @pytest.mark.asyncio
    async def test_transition_nonexistent_evaluation(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test transitioning non-existent evaluation fails"""
        mock_document_store.find_by_id.return_value = None

        with pytest.raises(ValueError, match="Evaluation not found"):
            await mock_watchkeeper.transition_evaluation_state(
                evaluation_id=uuid4(),
                new_state=EvaluationState.PEER_SUGGESTION_GENERATED,
            )


class TestSystemHealthMonitoring:
    """Test system health monitoring"""

    @pytest.mark.asyncio
    async def test_monitor_system_health_healthy(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test system health monitoring when healthy"""
        # Mock healthy state
        mock_document_store.count.return_value = 10
        mock_document_store.find.return_value = []  # No deadline violations

        health = await mock_watchkeeper.monitor_system_health()

        assert health["health_score"] == 1.0
        assert health["active_evaluations"] == 10
        assert health["deadline_violations"] == 0

    @pytest.mark.asyncio
    async def test_monitor_system_health_with_violations(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test health score degrades with violations"""
        # Mock state with violations
        mock_document_store.count.return_value = 10
        mock_document_store.find.return_value = [
            {
                "_id": str(uuid4()),
                "employee_id": str(uuid4()),
                "current_phase": "data_gathering",
                "peer_feedback_deadline": (datetime.now() - timedelta(days=5)).isoformat(),
                "peer_selection_deadline": None,
                "self_eval_deadline": None,
                "manager_eval_deadline": None,
            }
        ]

        health = await mock_watchkeeper.monitor_system_health()

        assert health["health_score"] < 1.0
        assert health["deadline_violations"] > 0

    @pytest.mark.asyncio
    async def test_monitor_system_health_phase_distribution(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test health monitoring includes phase distribution"""
        # Mock count calls for different phases
        async def mock_count(collection, query):
            phase = query.get("current_phase")
            if phase == "context_peer_selection":
                return 3
            elif phase == "data_gathering":
                return 5
            elif phase == "manager_evaluation":
                return 2
            return 0

        mock_document_store.count.side_effect = mock_count

        health = await mock_watchkeeper.monitor_system_health()

        assert "phase_distribution" in health


class TestComplexScenarios:
    """Complex test scenarios"""

    @pytest.mark.asyncio
    async def test_large_scale_cycle_start(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test starting cycle for large employee cohort"""
        # 100 employees
        employee_ids = [uuid4() for _ in range(100)]

        result = await mock_watchkeeper.start_evaluation_cycle(
            cohort_id="IC_Q",
            cycle_name="Q4 2024",
            employee_ids=employee_ids,
        )

        assert result["evaluations_created"] == 100

    @pytest.mark.asyncio
    async def test_concurrent_cohort_cycles(
        self, mock_watchkeeper, mock_document_store
    ):
        """Test multiple cohorts running simultaneously"""
        # Start L6 cohort
        l6_result = await mock_watchkeeper.start_evaluation_cycle(
            cohort_id="L6_Q",
            cycle_name="Q4 2024",
            employee_ids=[uuid4() for _ in range(5)],
        )

        # Start IC cohort
        ic_result = await mock_watchkeeper.start_evaluation_cycle(
            cohort_id="IC_Q",
            cycle_name="Q4 2024",
            employee_ids=[uuid4() for _ in range(50)],
        )

        assert l6_result["evaluations_created"] == 5
        assert ic_result["evaluations_created"] == 50
