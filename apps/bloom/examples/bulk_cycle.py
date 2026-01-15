"""
Bulk Evaluation Cycle Example

Demonstrates starting an evaluation cycle for a cohort of employees:
1. Load employee cohort (e.g., all L3 engineers)
2. Start bulk evaluation cycle
3. Monitor progress across all evaluations
4. Track completion metrics
5. Identify overdue evaluations

This example shows how to manage evaluations at scale.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from loguru import logger

from bloom.models import (
    Employee,
    Person,
    EmployeeLevel,
    EmployeeRole,
    EvaluationPhase,
    EvaluationState,
)
from bloom.orchestrator import BloomOrchestrator, BloomConfig


async def create_mock_employees(count: int) -> List[Employee]:
    """Create mock employees for demonstration"""

    employees = []
    manager_id = uuid4()

    for i in range(count):
        employee = Employee(
            person=Person(
                id=uuid4(),
                name=f"Employee {i+1}",
                email=f"employee{i+1}@company.com",
                title="Senior Software Engineer",
                location="San Francisco, CA",
                region="NAM",
                level=EmployeeLevel.L3,
                sub_level=i % 3,  # Mix of sub-levels
                role=EmployeeRole.INDIVIDUAL_CONTRIBUTOR,
                manager_id=manager_id,
                hire_date=(datetime.now() - timedelta(days=365 * (2 + i % 3))).date(),
            )
        )
        employees.append(employee)

    return employees


async def monitor_cycle_progress(
    orchestrator: BloomOrchestrator,
    cycle_name: str,
) -> dict:
    """Monitor and report on cycle progress"""

    # Query all evaluations for this cycle
    eval_docs = await orchestrator.document_store.find(
        collection="evaluations",
        query={"cycle_name": cycle_name},
        limit=1000,
    )

    # Calculate statistics
    total = len(eval_docs)
    by_phase = {}
    by_state = {}
    overdue = 0
    completed_feedbacks = 0
    total_feedbacks = 0

    for doc in eval_docs:
        from bloom.models import Evaluation

        evaluation = Evaluation(**doc)

        # Count by phase
        phase = evaluation.current_phase.value
        by_phase[phase] = by_phase.get(phase, 0) + 1

        # Count by state
        state = evaluation.current_state.value
        by_state[state] = by_state.get(state, 0) + 1

        # Check if overdue
        if any([
            evaluation.is_past_deadline("peer_feedback"),
            evaluation.is_past_deadline("self_eval"),
            evaluation.is_past_deadline("manager_eval"),
        ]):
            overdue += 1

        # Feedback metrics
        total_feedbacks += len(evaluation.manager_approved_peers)
        completed_feedbacks += len(evaluation.peer_feedbacks)

    return {
        "total": total,
        "by_phase": by_phase,
        "by_state": by_state,
        "overdue": overdue,
        "feedback_completion": (
            completed_feedbacks / total_feedbacks * 100
            if total_feedbacks > 0
            else 0
        ),
    }


async def main():
    """Run bulk evaluation cycle example"""

    logger.info("=== Bulk Evaluation Cycle Example ===")

    # ========================================================================
    # Step 1: Initialize Orchestrator
    # ========================================================================

    logger.info("\n[Step 1] Initializing Bloom orchestrator...")

    config = BloomConfig(
        num_scribes=2,  # More scribes for parallel processing
        num_context_miners=1,
        num_chasers=1,
        enable_autonomous_mode=True,  # Let agents work autonomously
        enable_rag=True,
        max_concurrent_evaluations=100,
    )

    orchestrator = BloomOrchestrator(config)
    await orchestrator.initialize()

    logger.info("✓ Orchestrator initialized")

    # ========================================================================
    # Step 2: Load Employee Cohort
    # ========================================================================

    logger.info("\n[Step 2] Loading employee cohort...")

    # Create 20 mock employees
    cohort_size = 20
    employees = await create_mock_employees(cohort_size)

    # Store employees in database
    for employee in employees:
        await orchestrator.document_store.insert(
            collection="employees",
            document=employee.model_dump(mode="json"),
            doc_id=str(employee.person.id),
        )

    logger.info(f"✓ Loaded {len(employees)} employees")
    logger.info(f"  Example: {employees[0].person.name} ({employees[0].person.email})")

    # ========================================================================
    # Step 3: Start Bulk Evaluation Cycle
    # ========================================================================

    logger.info("\n[Step 3] Starting bulk evaluation cycle...")

    cycle_name = "Q4 2024 - Engineering"
    start_time = datetime.now()

    evaluation_ids = await orchestrator.start_evaluation_cycle(
        cycle_name=cycle_name,
        employees=employees,
        start_date=start_time,
    )

    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info(f"✓ Created {len(evaluation_ids)} evaluations in {elapsed:.2f}s")
    logger.info(f"  Average: {elapsed / len(evaluation_ids):.2f}s per evaluation")
    logger.info(f"  Cycle: {cycle_name}")

    # ========================================================================
    # Step 4: Monitor Initial Progress
    # ========================================================================

    logger.info("\n[Step 4] Monitoring initial cycle progress...")

    stats = await monitor_cycle_progress(orchestrator, cycle_name)

    logger.info(f"\nCycle Statistics:")
    logger.info(f"  Total evaluations: {stats['total']}")
    logger.info(f"  Overdue: {stats['overdue']}")
    logger.info(f"\n  By Phase:")
    for phase, count in stats["by_phase"].items():
        logger.info(f"    {phase}: {count}")
    logger.info(f"\n  By State:")
    for state, count in stats["by_state"].items():
        logger.info(f"    {state}: {count}")

    # ========================================================================
    # Step 5: Simulate Peer Selection
    # ========================================================================

    logger.info("\n[Step 5] Processing peer selections for all evaluations...")

    # Process peer selection for first 5 evaluations (to demonstrate)
    for i, eval_id in enumerate(evaluation_ids[:5], 1):
        logger.info(f"  Processing peer selection {i}/5...")

        evaluation = await orchestrator.get_evaluation(eval_id)

        result = await orchestrator.process_peer_selection(
            evaluation_id=eval_id,
            employee_id=evaluation.employee_id,
        )

        logger.info(
            f"  ✓ Suggested {len(result.get('suggested_peers', []))} peers "
            f"for {evaluation.employee_id}"
        )

    logger.info(f"✓ Completed peer selection for 5 sample evaluations")

    # ========================================================================
    # Step 6: Auto-Approve Peers (Simulated)
    # ========================================================================

    logger.info("\n[Step 6] Auto-approving peer selections...")

    approved_count = 0

    for eval_id in evaluation_ids[:5]:
        evaluation = await orchestrator.get_evaluation(eval_id)

        # Auto-approve first 5 suggested peers
        if evaluation.suggested_peers:
            evaluation.manager_approved_peers = evaluation.suggested_peers[:5]
            await orchestrator._update_evaluation(evaluation)
            approved_count += 1

    logger.info(f"✓ Auto-approved peers for {approved_count} evaluations")

    # ========================================================================
    # Step 7: Monitor Progress After Peer Selection
    # ========================================================================

    logger.info("\n[Step 7] Monitoring progress after peer selection...")

    stats = await monitor_cycle_progress(orchestrator, cycle_name)

    logger.info(f"\nUpdated Statistics:")
    logger.info(f"  By State:")
    for state, count in stats["by_state"].items():
        logger.info(f"    {state}: {count}")

    # ========================================================================
    # Step 8: Identify At-Risk Evaluations
    # ========================================================================

    logger.info("\n[Step 8] Identifying at-risk evaluations...")

    # Find evaluations that might be delayed
    at_risk = []

    for eval_id in evaluation_ids:
        evaluation = await orchestrator.get_evaluation(eval_id)

        # Check if approaching deadlines with no progress
        if evaluation.peer_feedback_deadline:
            days_until_deadline = (
                evaluation.peer_feedback_deadline - datetime.now()
            ).days

            if days_until_deadline < 7 and not evaluation.peer_feedbacks:
                at_risk.append({
                    "evaluation_id": eval_id,
                    "employee_id": evaluation.employee_id,
                    "days_until_deadline": days_until_deadline,
                    "reason": "No peer feedback received",
                })

    logger.info(f"\nAt-Risk Evaluations: {len(at_risk)}")
    for i, risk in enumerate(at_risk[:3], 1):  # Show first 3
        logger.info(
            f"  {i}. Employee {risk['employee_id']}: "
            f"{risk['reason']} ({risk['days_until_deadline']} days left)"
        )

    # ========================================================================
    # Step 9: Generate Progress Report
    # ========================================================================

    logger.info("\n[Step 9] Generating cycle progress report...")

    # Calculate detailed metrics
    stats = await monitor_cycle_progress(orchestrator, cycle_name)

    completion_rate = (
        stats["by_phase"].get(EvaluationPhase.COMPLETED.value, 0)
        / stats["total"]
        * 100
    )

    in_progress = stats["total"] - stats["by_phase"].get(
        EvaluationPhase.COMPLETED.value, 0
    )

    logger.info(f"\n{'='*60}")
    logger.info(f"CYCLE PROGRESS REPORT: {cycle_name}")
    logger.info(f"{'='*60}")
    logger.info(f"\nOverall Progress:")
    logger.info(f"  Total Evaluations: {stats['total']}")
    logger.info(f"  Completed: {stats['by_phase'].get(EvaluationPhase.COMPLETED.value, 0)}")
    logger.info(f"  In Progress: {in_progress}")
    logger.info(f"  Completion Rate: {completion_rate:.1f}%")
    logger.info(f"  Overdue: {stats['overdue']}")

    logger.info(f"\nPhase Distribution:")
    for phase in EvaluationPhase:
        count = stats["by_phase"].get(phase.value, 0)
        if count > 0:
            pct = count / stats["total"] * 100
            logger.info(f"  {phase.value:30s}: {count:3d} ({pct:5.1f}%)")

    logger.info(f"\nFeedback Progress:")
    logger.info(f"  Feedback Completion: {stats['feedback_completion']:.1f}%")

    logger.info(f"\nRisk Assessment:")
    logger.info(f"  At-Risk Evaluations: {len(at_risk)}")
    if at_risk:
        logger.info(f"  Primary Issue: No peer feedback received")

    logger.info(f"\n{'='*60}")

    # ========================================================================
    # Step 10: Export Data (Simulated)
    # ========================================================================

    logger.info("\n[Step 10] Exporting cycle data...")

    # In production, would export to CSV/Excel
    export_data = {
        "cycle_name": cycle_name,
        "export_date": datetime.now().isoformat(),
        "statistics": stats,
        "at_risk_evaluations": at_risk,
    }

    logger.info(f"✓ Export data prepared")
    logger.info(f"  Total records: {stats['total']}")
    logger.info(f"  At-risk flagged: {len(at_risk)}")

    # ========================================================================
    # Step 11: Demonstrate Swarm Status
    # ========================================================================

    logger.info("\n[Step 11] Checking agent swarm status...")

    swarm_status = await orchestrator.get_swarm_status()

    logger.info(f"\nAgent Swarm Status:")
    logger.info(f"  Running: {swarm_status['is_running']}")
    logger.info(f"  Uptime: {swarm_status['uptime_seconds']:.0f}s")
    logger.info(f"  Active Evaluations: {swarm_status['active_evaluations']}")
    logger.info(f"  Background Tasks: {swarm_status['background_tasks']}")

    logger.info(f"\n  Agent Details:")
    agents = swarm_status["agents"]

    if agents.get("watchkeeper"):
        logger.info(f"    Watchkeeper: Active")

    if agents.get("scribes"):
        logger.info(f"    Scribes: {len(agents['scribes'])} active")

    if agents.get("context_miners"):
        logger.info(f"    Context Miners: {len(agents['context_miners'])} active")

    if agents.get("chasers"):
        logger.info(f"    Chasers: {len(agents['chasers'])} active")

    # ========================================================================
    # Cleanup
    # ========================================================================

    logger.info("\n[Cleanup] Shutting down orchestrator...")
    await orchestrator.shutdown()

    logger.info("\n=== Bulk Evaluation Cycle Complete ===")
    logger.info(f"\nSummary:")
    logger.info(f"  Created {len(evaluation_ids)} evaluations")
    logger.info(f"  Completion rate: {completion_rate:.1f}%")
    logger.info(f"  At-risk evaluations: {len(at_risk)}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
