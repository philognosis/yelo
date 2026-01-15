"""
Simple Evaluation Workflow Example

Demonstrates a basic evaluation workflow for a single employee:
1. Create an evaluation
2. Get AI peer suggestions
3. Submit peer feedback
4. Submit self-evaluation
5. Generate manager draft
6. Complete manager evaluation

This example shows the core functionality with minimal complexity.
"""

import asyncio
from datetime import datetime
from uuid import uuid4

from loguru import logger

from bloom.models import Employee, Person, EmployeeLevel, EmployeeRole, Rating, PromotionEligibility
from bloom.orchestrator import BloomOrchestrator, BloomConfig


async def main():
    """Run a simple evaluation workflow"""

    logger.info("=== Simple Evaluation Workflow Example ===")

    # ========================================================================
    # Step 1: Initialize Bloom Orchestrator
    # ========================================================================

    logger.info("\n[Step 1] Initializing Bloom orchestrator...")

    config = BloomConfig(
        num_scribes=1,
        num_context_miners=1,
        num_chasers=1,
        enable_autonomous_mode=False,  # Manual control for demo
        enable_rag=True,
        enable_voice_synthesis=False,
    )

    orchestrator = BloomOrchestrator(config)
    await orchestrator.initialize()

    logger.info("✓ Orchestrator initialized successfully")

    # ========================================================================
    # Step 2: Create Employee Record
    # ========================================================================

    logger.info("\n[Step 2] Creating employee record...")

    # Create employee
    employee = Employee(
        person=Person(
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
            hire_date=datetime(2020, 6, 15).date(),
        )
    )

    # Store employee in database
    await orchestrator.document_store.insert(
        collection="employees",
        document=employee.model_dump(mode="json"),
        doc_id=str(employee.person.id),
    )

    logger.info(f"✓ Created employee: {employee.person.name} ({employee.person.email})")

    # ========================================================================
    # Step 3: Start Evaluation Cycle
    # ========================================================================

    logger.info("\n[Step 3] Starting evaluation cycle...")

    evaluation_ids = await orchestrator.start_evaluation_cycle(
        cycle_name="Q4 2024",
        employees=[employee],
        start_date=datetime.now(),
    )

    evaluation_id = evaluation_ids[0]
    logger.info(f"✓ Evaluation created: {evaluation_id}")

    # Get evaluation details
    evaluation = await orchestrator.get_evaluation(evaluation_id)
    logger.info(f"  Current phase: {evaluation.current_phase}")
    logger.info(f"  Current state: {evaluation.current_state}")
    logger.info(f"  Peer feedback deadline: {evaluation.peer_feedback_deadline}")

    # ========================================================================
    # Step 4: Get AI Peer Suggestions
    # ========================================================================

    logger.info("\n[Step 4] Getting AI peer suggestions...")

    result = await orchestrator.process_peer_selection(
        evaluation_id=evaluation_id,
        employee_id=employee.person.id,
    )

    suggested_peers = result.get("suggested_peers", [])
    logger.info(f"✓ AI suggested {len(suggested_peers)} peer reviewers:")

    for i, peer in enumerate(suggested_peers, 1):
        logger.info(
            f"  {i}. {peer.get('name', 'Unknown')} "
            f"(strength: {peer.get('relationship_strength', 0):.2f})"
        )

    # ========================================================================
    # Step 5: Approve Peers
    # ========================================================================

    logger.info("\n[Step 5] Approving peer reviewers...")

    # Refresh evaluation
    evaluation = await orchestrator.get_evaluation(evaluation_id)

    # Manager approves first 3 suggested peers
    evaluation.manager_approved_peers = evaluation.suggested_peers[:3]
    await orchestrator._update_evaluation(evaluation)

    logger.info(f"✓ Approved {len(evaluation.manager_approved_peers)} peer reviewers")

    # ========================================================================
    # Step 6: Submit Peer Feedback
    # ========================================================================

    logger.info("\n[Step 6] Submitting peer feedback...")

    # Simulate 3 peer feedback submissions
    peer_feedbacks = [
        {
            "peer_id": evaluation.manager_approved_peers[0],
            "raw_input": (
                "Jane did an excellent job leading the API migration project. "
                "She handled technical challenges well and kept the team aligned. "
                "Her code reviews are thorough and educational."
            ),
        },
        {
            "peer_id": evaluation.manager_approved_peers[1],
            "raw_input": (
                "Jane is a strong technical contributor. She helped me debug "
                "a complex database issue and explained the solution clearly. "
                "Great teammate to work with."
            ),
        },
        {
            "peer_id": evaluation.manager_approved_peers[2],
            "raw_input": (
                "Jane consistently delivers high-quality work on time. "
                "She's proactive in identifying issues and proposing solutions. "
                "Would love to collaborate with her more."
            ),
        },
    ]

    for i, feedback_data in enumerate(peer_feedbacks, 1):
        logger.info(f"  Submitting feedback from peer {i}...")

        feedback = await orchestrator.process_peer_feedback(
            evaluation_id=evaluation_id,
            peer_id=feedback_data["peer_id"],
            raw_feedback=feedback_data["raw_input"],
            input_method="text",
        )

        logger.info(f"  ✓ Peer {i} feedback synthesized")
        logger.info(f"    Raw: {feedback_data['raw_input'][:60]}...")
        if feedback.synthesized_feedback:
            logger.info(f"    Synthesized: {feedback.synthesized_feedback[:60]}...")

    logger.info(f"✓ All {len(peer_feedbacks)} peer feedbacks submitted")

    # ========================================================================
    # Step 7: Submit Self-Evaluation
    # ========================================================================

    logger.info("\n[Step 7] Submitting self-evaluation...")

    from bloom.models import SelfEvaluation

    self_eval = SelfEvaluation(
        evaluation_id=evaluation_id,
        employee_id=employee.person.id,
        raw_achievements=(
            "Led the API v2 migration project, improving performance by 40%. "
            "Mentored 2 junior engineers on system design best practices. "
            "Reduced production incidents by implementing comprehensive monitoring."
        ),
        raw_challenges=(
            "Balancing feature development with technical debt was challenging. "
            "Learned to better estimate complex projects."
        ),
        raw_growth_areas=(
            "Want to develop stronger leadership skills for larger initiatives. "
            "Would like to learn more about ML infrastructure."
        ),
        raw_goals=(
            "Lead a cross-team initiative in Q1 2025. "
            "Present at engineering all-hands. "
            "Complete advanced system design course."
        ),
    )

    # Update evaluation
    evaluation = await orchestrator.get_evaluation(evaluation_id)
    evaluation.self_evaluation = self_eval
    await orchestrator._update_evaluation(evaluation)

    logger.info("✓ Self-evaluation submitted")
    logger.info(f"  Achievements: {self_eval.raw_achievements[:60]}...")

    # ========================================================================
    # Step 8: Generate AI Manager Draft
    # ========================================================================

    logger.info("\n[Step 8] Generating AI manager draft...")

    manager_eval = await orchestrator.generate_manager_draft(evaluation_id)

    logger.info("✓ AI draft generated successfully")
    logger.info(f"  Draft summary: {manager_eval.ai_draft_summary[:100]}...")
    logger.info(f"  Evidence categories: {len(manager_eval.ai_draft_evidence_map or {})}")
    logger.info(f"  Clarifying questions: {len(manager_eval.ai_questions)}")

    if manager_eval.ai_questions:
        logger.info("\n  AI asked the following questions:")
        for i, question in enumerate(manager_eval.ai_questions[:3], 1):
            logger.info(f"    {i}. {question.get('question', 'Unknown')}")

    # ========================================================================
    # Step 9: Complete Manager Evaluation
    # ========================================================================

    logger.info("\n[Step 9] Completing manager evaluation...")

    # Manager reviews draft and finalizes
    evaluation = await orchestrator.get_evaluation(evaluation_id)
    manager_eval = evaluation.manager_evaluation

    # Manager fills in final details
    manager_eval.final_summary = (
        "Jane has demonstrated exceptional technical leadership this quarter. "
        "The API migration project was complex and high-stakes, and she executed "
        "it flawlessly while mentoring junior team members. Her code quality and "
        "attention to detail are consistently outstanding. Ready for senior IC role."
    )
    manager_eval.technical_assessment = (
        "Expert-level technical skills. Strong system design and implementation."
    )
    manager_eval.leadership_assessment = (
        "Emerging leadership through mentorship and technical guidance."
    )
    manager_eval.growth_opportunities = (
        "Continue developing leadership skills. Take on larger cross-team initiatives."
    )

    # Ratings
    manager_eval.overall_rating = Rating.EXCEEDS
    manager_eval.technical_rating = Rating.EXCEEDS
    manager_eval.leadership_rating = Rating.MEETS
    manager_eval.communication_rating = Rating.EXCEEDS
    manager_eval.strategic_thinking_rating = Rating.MEETS

    # Promotion
    manager_eval.promotion_eligibility = PromotionEligibility.READY_NEXT_CYCLE
    manager_eval.promotion_justification = (
        "Strong technical performance and emerging leadership. "
        "Would benefit from leading 1-2 more major initiatives before promotion."
    )

    manager_eval.submitted_at = datetime.now()

    # Update evaluation
    await orchestrator._update_evaluation(evaluation)

    logger.info("✓ Manager evaluation completed")
    logger.info(f"  Overall rating: {manager_eval.overall_rating}")
    logger.info(f"  Promotion eligibility: {manager_eval.promotion_eligibility}")

    # ========================================================================
    # Step 10: View Final Evaluation
    # ========================================================================

    logger.info("\n[Step 10] Final evaluation summary...")

    evaluation = await orchestrator.get_evaluation(evaluation_id)

    logger.info(f"\nEvaluation Complete!")
    logger.info(f"  Employee: {employee.person.name}")
    logger.info(f"  Cycle: {evaluation.cycle_name}")
    logger.info(f"  Phase: {evaluation.current_phase}")
    logger.info(f"  State: {evaluation.current_state}")
    logger.info(f"  Completion: {evaluation.get_completion_percentage() * 100:.0f}%")
    logger.info(f"\n  Peer feedbacks: {len(evaluation.peer_feedbacks)}")
    logger.info(f"  Self-evaluation: {'✓' if evaluation.self_evaluation else '✗'}")
    logger.info(f"  Manager evaluation: {'✓' if evaluation.manager_evaluation else '✗'}")
    logger.info(f"\n  Overall rating: {manager_eval.overall_rating}")
    logger.info(f"  Promotion: {manager_eval.promotion_eligibility}")

    # ========================================================================
    # Cleanup
    # ========================================================================

    logger.info("\n[Cleanup] Shutting down orchestrator...")
    await orchestrator.shutdown()

    logger.info("\n=== Simple Evaluation Workflow Complete ===")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
