"""
Manager Review Workflow with AI Assistance

Demonstrates the manager's evaluation workflow with AI assistance:
1. Review pending evaluations for team
2. Get AI-generated draft for an evaluation
3. Review AI evidence mapping
4. Answer AI clarifying questions
5. Edit and finalize evaluation
6. Submit for calibration

This example shows the AI-assisted manager experience.
"""

import asyncio
from datetime import datetime
from uuid import uuid4

from loguru import logger

from bloom.models import (
    Employee,
    Person,
    EmployeeLevel,
    EmployeeRole,
    PeerFeedback,
    SelfEvaluation,
    Rating,
    PromotionEligibility,
)
from bloom.orchestrator import BloomOrchestrator, BloomConfig


async def setup_evaluation_with_feedback(
    orchestrator: BloomOrchestrator,
    employee: Employee,
) -> uuid4:
    """Create an evaluation with peer feedback and self-eval already submitted"""

    # Create evaluation
    evaluation_ids = await orchestrator.start_evaluation_cycle(
        cycle_name="Q4 2024",
        employees=[employee],
        start_date=datetime.now(),
    )

    evaluation_id = evaluation_ids[0]
    evaluation = await orchestrator.get_evaluation(evaluation_id)

    # Add mock peer feedback (3 peers)
    peer_feedbacks = [
        PeerFeedback(
            evaluation_id=evaluation_id,
            peer_id=uuid4(),
            peer_name="Alice Johnson",
            raw_input=(
                "Sarah led the microservices migration with exceptional skill. "
                "She handled complex architectural decisions and kept stakeholders "
                "informed throughout. Her code reviews are thorough and educational."
            ),
            synthesized_feedback=(
                "Sarah demonstrated strong technical leadership on the microservices "
                "migration project, making sound architectural decisions while maintaining "
                "clear stakeholder communication. Her code review quality is consistently high."
            ),
            technical_rating=Rating.EXCEEDS,
            leadership_rating=Rating.EXCEEDS,
            communication_rating=Rating.EXCEEDS,
            submitted_at=datetime.now(),
        ),
        PeerFeedback(
            evaluation_id=evaluation_id,
            peer_id=uuid4(),
            peer_name="Bob Chen",
            raw_input=(
                "Sarah is an incredible mentor. She helped me understand distributed "
                "systems and always makes time for questions. Her documentation is "
                "top-notch and makes onboarding so much easier."
            ),
            synthesized_feedback=(
                "Sarah excels at mentorship and knowledge sharing, with particular "
                "strength in distributed systems. Her documentation practices "
                "significantly improve team onboarding and knowledge retention."
            ),
            technical_rating=Rating.EXCEEDS,
            leadership_rating=Rating.MEETS,
            communication_rating=Rating.EXCEPTIONAL,
            submitted_at=datetime.now(),
        ),
        PeerFeedback(
            evaluation_id=evaluation_id,
            peer_id=uuid4(),
            peer_name="Carol Martinez",
            raw_input=(
                "Working with Sarah on the payment service was great. She's very "
                "detail-oriented and caught several edge cases I missed. She also "
                "coordinated well with the product team to clarify requirements."
            ),
            synthesized_feedback=(
                "Sarah exhibits strong attention to detail and proactive edge case "
                "identification. She demonstrates effective cross-functional collaboration, "
                "particularly with product teams on requirement clarification."
            ),
            technical_rating=Rating.EXCEEDS,
            collaboration_rating=Rating.EXCEEDS,
            submitted_at=datetime.now(),
        ),
    ]

    evaluation.peer_feedbacks = peer_feedbacks

    # Add self-evaluation
    evaluation.self_evaluation = SelfEvaluation(
        evaluation_id=evaluation_id,
        employee_id=employee.person.id,
        raw_achievements=(
            "1. Led microservices migration for payment platform (Q3-Q4), improving "
            "system reliability from 99.5% to 99.95% and reducing latency by 60%. "
            "2. Mentored 3 mid-level engineers on distributed systems design. "
            "3. Established code review best practices that were adopted team-wide. "
            "4. Contributed to 2 open-source projects used by the team. "
            "5. Presented 'Building Resilient Services' at engineering all-hands."
        ),
        raw_challenges=(
            "Balancing the migration timeline with feature development was difficult. "
            "Had to negotiate scope and phasing with product. Also struggled initially "
            "with stakeholder communication - learned to provide better status updates."
        ),
        raw_growth_areas=(
            "Want to improve strategic thinking and roadmap planning. "
            "Would like to develop stronger skills in leading cross-team initiatives. "
            "Need more experience with organizational influence."
        ),
        raw_goals=(
            "1. Lead a major cross-org initiative in 2025. "
            "2. Speak at an external conference. "
            "3. Develop and deliver internal training on system design. "
            "4. Grow mentorship to include engineers outside immediate team."
        ),
        synthesized_achievements=(
            "Led critical microservices migration achieving significant reliability "
            "and performance improvements. Demonstrated strong mentorship and knowledge "
            "sharing through code review practices and technical presentations."
        ),
        submitted_at=datetime.now(),
    )

    # Update evaluation
    await orchestrator._update_evaluation(evaluation)

    return evaluation_id


async def main():
    """Run manager workflow example"""

    logger.info("=== Manager Review Workflow with AI Assistance ===")

    # ========================================================================
    # Step 1: Initialize Orchestrator
    # ========================================================================

    logger.info("\n[Step 1] Initializing Bloom orchestrator...")

    config = BloomConfig(
        num_scribes=2,
        num_context_miners=1,
        num_chasers=1,
        enable_autonomous_mode=False,
        enable_rag=True,  # Enable RAG for AI drafts
        enable_voice_synthesis=False,
    )

    orchestrator = BloomOrchestrator(config)
    await orchestrator.initialize()

    logger.info("✓ Orchestrator initialized")

    # ========================================================================
    # Step 2: Create Employee and Evaluation
    # ========================================================================

    logger.info("\n[Step 2] Setting up employee and evaluation...")

    manager_id = uuid4()

    employee = Employee(
        person=Person(
            id=uuid4(),
            name="Sarah Chen",
            email="sarah.chen@company.com",
            title="Senior Software Engineer",
            location="Seattle, WA",
            region="NAM",
            level=EmployeeLevel.L4,
            sub_level=1,
            role=EmployeeRole.INDIVIDUAL_CONTRIBUTOR,
            manager_id=manager_id,
            hire_date=datetime(2019, 3, 1).date(),
        )
    )

    # Store employee
    await orchestrator.document_store.insert(
        collection="employees",
        document=employee.model_dump(mode="json"),
        doc_id=str(employee.person.id),
    )

    logger.info(f"✓ Created employee: {employee.person.name}")

    # Create evaluation with feedback
    evaluation_id = await setup_evaluation_with_feedback(orchestrator, employee)

    logger.info(f"✓ Created evaluation with peer feedback and self-eval")

    # ========================================================================
    # Step 3: Manager Views Pending Evaluations
    # ========================================================================

    logger.info("\n[Step 3] Viewing pending evaluations for team...")

    # In real system, would query by manager_id
    eval_docs = await orchestrator.document_store.find(
        collection="evaluations",
        query={"manager_id": str(manager_id)},
        limit=10,
    )

    logger.info(f"\nPending Evaluations: {len(eval_docs)}")

    for i, doc in enumerate(eval_docs, 1):
        from bloom.models import Evaluation

        eval_obj = Evaluation(**doc)
        logger.info(
            f"  {i}. {employee.person.name} - {eval_obj.current_phase.value} "
            f"({len(eval_obj.peer_feedbacks)} peer feedbacks)"
        )

    # ========================================================================
    # Step 4: Request AI Draft
    # ========================================================================

    logger.info("\n[Step 4] Requesting AI-generated evaluation draft...")

    logger.info("  AI is analyzing:")
    evaluation = await orchestrator.get_evaluation(evaluation_id)
    logger.info(f"    - {len(evaluation.peer_feedbacks)} peer feedback submissions")
    logger.info(f"    - 1 self-evaluation")
    logger.info(f"    - Employee's work history and context")

    logger.info("\n  Generating draft using RAG pipeline...")

    manager_eval = await orchestrator.generate_manager_draft(evaluation_id)

    logger.info("✓ AI draft generated successfully")

    # ========================================================================
    # Step 5: Review AI Draft Summary
    # ========================================================================

    logger.info("\n[Step 5] Reviewing AI draft summary...")

    logger.info(f"\n{'='*70}")
    logger.info("AI-GENERATED DRAFT SUMMARY")
    logger.info(f"{'='*70}")

    if manager_eval.ai_draft_summary:
        # Format the summary nicely
        logger.info(f"\n{manager_eval.ai_draft_summary}")
    else:
        logger.info("\n[Mock] Sarah demonstrated exceptional technical leadership...")

    logger.info(f"\n{'='*70}")

    # ========================================================================
    # Step 6: Review Evidence Mapping
    # ========================================================================

    logger.info("\n[Step 6] Reviewing AI evidence mapping...")

    logger.info("\nAI Evidence Map (statements backed by specific examples):")

    evidence_map = manager_eval.ai_draft_evidence_map or {
        "Technical Leadership": [
            "Led microservices migration (self-eval)",
            "Made sound architectural decisions (Alice)",
            "Strong distributed systems knowledge (Bob)",
        ],
        "Mentorship": [
            "Mentored 3 mid-level engineers (self-eval)",
            "Excellent at knowledge sharing (Bob)",
            "Created educational code reviews (Alice)",
        ],
        "Communication": [
            "Clear stakeholder communication (Alice)",
            "Excellent documentation (Bob)",
            "Good cross-functional collaboration (Carol)",
        ],
        "Technical Excellence": [
            "99.95% reliability achievement (self-eval)",
            "Detail-oriented, catches edge cases (Carol)",
            "High-quality code reviews (Alice)",
        ],
    }

    for category, evidence_list in evidence_map.items():
        logger.info(f"\n  {category}:")
        for evidence in evidence_list:
            logger.info(f"    • {evidence}")

    # ========================================================================
    # Step 7: Review AI Questions
    # ========================================================================

    logger.info("\n[Step 7] Reviewing AI clarifying questions...")

    ai_questions = manager_eval.ai_questions or [
        {
            "question": "How did Sarah handle the stakeholder communication challenges mentioned in her self-eval?",
            "context": "She mentioned struggling initially but improving. Specific examples would strengthen the evaluation.",
            "suggested_impact": "Leadership and communication ratings",
        },
        {
            "question": "What was the scope and impact of the open-source contributions?",
            "context": "Self-eval mentions 2 open-source projects. Understanding scope would help assess strategic impact.",
            "suggested_impact": "Technical excellence and strategic thinking",
        },
        {
            "question": "How has Sarah's mentorship impacted the team's capabilities?",
            "context": "Multiple mentions of mentorship. Quantifying impact would strengthen promotion case.",
            "suggested_impact": "Leadership rating and promotion eligibility",
        },
    ]

    logger.info(f"\nAI identified {len(ai_questions)} areas needing clarification:")

    for i, q in enumerate(ai_questions, 1):
        logger.info(f"\n  Question {i}:")
        logger.info(f"    Q: {q['question']}")
        logger.info(f"    Context: {q['context']}")
        logger.info(f"    Impact: {q['suggested_impact']}")

    # ========================================================================
    # Step 8: Manager Answers Questions
    # ========================================================================

    logger.info("\n[Step 8] Manager answering AI questions...")

    manager_responses = [
        {
            "question_id": "1",
            "response": (
                "Sarah initially sent detailed technical updates but realized "
                "stakeholders needed higher-level summaries. She adapted by creating "
                "a weekly stakeholder digest with key metrics and risks. This became "
                "a template for the whole team."
            ),
        },
        {
            "question_id": "2",
            "response": (
                "Sarah contributed to our logging library and monitoring framework. "
                "Both are now used across 15+ services. She also reviews external "
                "contributions, which has improved our relationship with the community."
            ),
        },
        {
            "question_id": "3",
            "response": (
                "The 3 engineers she mentored are now confidently designing services "
                "independently. One of them led a recent migration project using "
                "patterns Sarah taught. Team velocity on distributed systems work "
                "has improved noticeably."
            ),
        },
    ]

    for i, response in enumerate(manager_responses, 1):
        logger.info(f"\n  Response {i}:")
        logger.info(f"    {response['response'][:100]}...")

    logger.info("\n✓ All questions answered")

    # Update manager evaluation with responses
    manager_eval.manager_responses = manager_responses

    # ========================================================================
    # Step 9: Finalize Evaluation
    # ========================================================================

    logger.info("\n[Step 9] Finalizing manager evaluation...")

    # Manager reviews draft and adds final touches
    manager_eval.final_summary = (
        "Sarah has demonstrated exceptional technical leadership and growth this year. "
        "Her leadership of the microservices migration was exemplary - she delivered "
        "significant improvements in reliability and performance while navigating complex "
        "stakeholder dynamics. Her evolution in stakeholder communication shows strong "
        "learning agility. "
        "\n\n"
        "Her mentorship impact is particularly noteworthy. The engineers she's mentored "
        "are now independently leading projects, and her code review practices have "
        "elevated the entire team's standards. "
        "\n\n"
        "Sarah is ready for promotion to Staff Engineer. She has demonstrated technical "
        "excellence, leadership through mentorship and example, and strategic impact "
        "through her open-source work and process improvements."
    )

    manager_eval.technical_assessment = (
        "Exceptional technical skills with deep expertise in distributed systems. "
        "Consistently delivers high-quality, well-designed solutions. Strong attention "
        "to reliability, performance, and operational excellence."
    )

    manager_eval.leadership_assessment = (
        "Strong emerging leadership through mentorship and technical influence. "
        "Has successfully mentored engineers to independence and improved team practices. "
        "Shows good learning agility in adapting stakeholder communication approach."
    )

    manager_eval.growth_opportunities = (
        "Continue developing strategic roadmap planning skills. Take on larger "
        "cross-organizational initiatives to build broader organizational influence. "
        "Consider presenting at external conferences to build industry presence."
    )

    # Assign ratings
    manager_eval.overall_rating = Rating.EXCEPTIONAL
    manager_eval.technical_rating = Rating.EXCEPTIONAL
    manager_eval.leadership_rating = Rating.EXCEEDS
    manager_eval.communication_rating = Rating.EXCEEDS
    manager_eval.strategic_thinking_rating = Rating.EXCEEDS

    # Promotion recommendation
    manager_eval.promotion_eligibility = PromotionEligibility.READY_NOW
    manager_eval.promotion_justification = (
        "Sarah meets all criteria for Staff Engineer: exceptional technical depth, "
        "demonstrated leadership through mentorship, strategic impact through tooling "
        "and processes, and strong communication skills. Her migration project shows "
        "ability to lead complex, high-impact initiatives. Ready for immediate promotion."
    )

    manager_eval.submitted_at = datetime.now()

    # Update evaluation
    evaluation = await orchestrator.get_evaluation(evaluation_id)
    evaluation.manager_evaluation = manager_eval
    await orchestrator._update_evaluation(evaluation)

    logger.info("✓ Manager evaluation finalized")

    # ========================================================================
    # Step 10: Review Final Evaluation
    # ========================================================================

    logger.info("\n[Step 10] Final evaluation summary...")

    logger.info(f"\n{'='*70}")
    logger.info("FINAL EVALUATION SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"\nEmployee: {employee.person.name}")
    logger.info(f"Title: {employee.person.title}")
    logger.info(f"Level: {employee.person.level.value}.{employee.person.sub_level}")
    logger.info(f"\nCycle: {evaluation.cycle_name}")
    logger.info(f"Manager: {manager_id}")

    logger.info(f"\n{'='*70}")
    logger.info("RATINGS")
    logger.info(f"{'='*70}")
    logger.info(f"Overall: {manager_eval.overall_rating.value.upper()}")
    logger.info(f"Technical: {manager_eval.technical_rating.value}")
    logger.info(f"Leadership: {manager_eval.leadership_rating.value}")
    logger.info(f"Communication: {manager_eval.communication_rating.value}")
    logger.info(f"Strategic Thinking: {manager_eval.strategic_thinking_rating.value}")

    logger.info(f"\n{'='*70}")
    logger.info("PROMOTION RECOMMENDATION")
    logger.info(f"{'='*70}")
    logger.info(f"Eligibility: {manager_eval.promotion_eligibility.value.upper()}")
    logger.info(f"\n{manager_eval.promotion_justification}")

    logger.info(f"\n{'='*70}")
    logger.info("INPUT SUMMARY")
    logger.info(f"{'='*70}")
    logger.info(f"Peer Feedbacks: {len(evaluation.peer_feedbacks)}")
    logger.info(f"Self-Evaluation: ✓")
    logger.info(f"AI Draft: ✓")
    logger.info(f"Manager Questions Answered: {len(manager_responses)}")

    logger.info(f"\n{'='*70}")

    # ========================================================================
    # Step 11: Show Time Savings
    # ========================================================================

    logger.info("\n[Step 11] AI assistance time savings analysis...")

    logger.info("\nEstimated Time Savings:")
    logger.info("  Without AI:")
    logger.info("    - Reading all feedback: ~30 min")
    logger.info("    - Identifying themes: ~20 min")
    logger.info("    - Finding evidence: ~25 min")
    logger.info("    - Writing draft: ~60 min")
    logger.info("    - Total: ~135 minutes")

    logger.info("\n  With AI:")
    logger.info("    - Review AI summary: ~10 min")
    logger.info("    - Review evidence map: ~5 min")
    logger.info("    - Answer questions: ~15 min")
    logger.info("    - Finalize evaluation: ~30 min")
    logger.info("    - Total: ~60 minutes")

    logger.info("\n  Time Saved: ~75 minutes (56% reduction)")
    logger.info("  Quality: Higher (evidence-based, comprehensive)")

    # ========================================================================
    # Cleanup
    # ========================================================================

    logger.info("\n[Cleanup] Shutting down orchestrator...")
    await orchestrator.shutdown()

    logger.info("\n=== Manager Review Workflow Complete ===")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
