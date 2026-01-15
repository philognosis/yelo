#!/usr/bin/env python3
"""
Semi-Complex Example - Multi-Topic Comparative Analysis

This example demonstrates intermediate IRAS capabilities:
- Multi-topic research
- Comparative analysis across topics
- Database integration
- Contract Net Protocol for task allocation
- Fact-checking verification

Perfect for:
- Comparing multiple technologies/concepts
- Understanding multi-agent coordination
- Learning database integration

Usage:
    python examples/semi_complex_example.py
"""

import asyncio
from datetime import datetime

from loguru import logger

# Configure logging
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
)

# Import IRAS components
from iras.orchestration import Coordinator, WorkflowConfig, WorkflowType


async def main():
    """
    Multi-topic comparative analysis example

    This demonstrates:
    1. Multi-agent swarm coordination
    2. Comparative analysis across topics
    3. Contract Net Protocol for task allocation
    4. Fact-checking and verification
    5. Database integration for results storage
    """

    print("=" * 80)
    print("IRAS Semi-Complex Example - Multi-Topic Comparative Analysis")
    print("=" * 80)
    print()

    # ========================================================================
    # Step 1: Initialize Coordinator with Expanded Swarm
    # ========================================================================

    print("Step 1: Initializing IRAS Coordinator with Multi-Agent Swarm...")
    print("-" * 80)

    # Create coordinator with expanded agent swarm
    # - 2 researchers for parallel information gathering
    # - 1 analyst for comparative analysis
    # - 1 fact-checker for verification
    # - 1 synthesizer for report generation
    coordinator = Coordinator(
        num_researchers=2,  # Multiple researchers for parallel work
        num_analysts=1,
        num_fact_checkers=1,  # Enable fact-checking
        num_synthesizers=1,
    )

    # Initialize all systems
    await coordinator.initialize()

    print()
    print("✓ Coordinator initialized successfully!")
    print()

    # Display swarm status
    status = coordinator.get_swarm_status()
    print("Swarm Configuration:")
    print(f"  • Total agents: {status['agents']['total']}")
    print(f"  • Researchers: {status['agents']['researchers']}")
    print(f"  • Analysts: {status['agents']['analysts']}")
    print(f"  • Fact-checkers: {status['agents']['fact_checkers']}")
    print(f"  • Synthesizers: {status['agents']['synthesizers']}")
    print()

    print("Communication Protocols:")
    print(f"  • Contract Net: {'✓ Active' if status['communication']['contract_net_active'] else '✗ Inactive'}")
    print(f"  • Blackboard: {'✓ Active' if status['communication']['blackboard_active'] else '✗ Inactive'}")
    print(f"  • Pub/Sub: {'✓ Active' if status['communication']['pubsub_active'] else '✗ Inactive'}")
    print()

    print("Database Integration:")
    print(f"  • Vector Store: {'✓ Ready' if status['databases']['vector_store'] else '✗ Not available'}")
    print(f"  • Graph Store: {'✓ Ready' if status['databases']['graph_store'] else '✗ Not available'}")
    print(f"  • Time-Series Store: {'✓ Ready' if status['databases']['timeseries_store'] else '✗ Not available'}")
    print(f"  • Document Store: {'✓ Ready' if status['databases']['document_store'] else '✗ Not available'}")
    print()

    # ========================================================================
    # Step 2: Define Comparative Research Topics
    # ========================================================================

    print("Step 2: Defining comparative research topics...")
    print("-" * 80)

    # Topics for comparison
    topics = [
        "Python programming language",
        "JavaScript programming language",
        "Rust programming language",
    ]

    print("Topics for comparison:")
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic}")
    print()

    # ========================================================================
    # Step 3: Execute Comparative Analysis Workflow
    # ========================================================================

    print("Step 3: Executing comparative analysis workflow...")
    print("-" * 80)
    print()

    # Create detailed workflow configuration
    config = WorkflowConfig(
        workflow_type=WorkflowType.COMPARATIVE_ANALYSIS,
        topics=topics,

        # Research parameters
        research_depth=3,  # Moderate-high depth
        num_sources=15,    # More sources for better comparison

        # Enable all analysis features
        enable_analysis=True,
        enable_fact_checking=True,
        enable_synthesis=True,

        # Use Contract Net Protocol for task distribution
        use_contract_net=True,
        use_blackboard=True,
        use_pubsub=True,

        # Store results in databases
        store_in_databases=True,

        # Quality thresholds
        min_source_quality=0.7,
        min_verification_confidence=0.8,

        # Timeouts
        research_timeout=300.0,
        analysis_timeout=180.0,
        verification_timeout=120.0,
        synthesis_timeout=120.0,
    )

    print(f"Workflow Configuration:")
    print(f"  • Type: {config.workflow_type.value}")
    print(f"  • Research Depth: {config.research_depth}/5")
    print(f"  • Sources per topic: {config.num_sources}")
    print(f"  • Contract Net Protocol: {'✓ Enabled' if config.use_contract_net else '✗ Disabled'}")
    print(f"  • Database Storage: {'✓ Enabled' if config.store_in_databases else '✗ Disabled'}")
    print()

    start_time = datetime.now()

    # Execute workflow
    print("Executing workflow (this may take a few moments)...")
    results = await coordinator.execute_workflow(config)

    duration = (datetime.now() - start_time).total_seconds()

    print()
    print(f"✓ Workflow completed in {duration:.2f} seconds!")
    print()

    # ========================================================================
    # Step 4: Display Detailed Results
    # ========================================================================

    print("Step 4: Detailed Results")
    print("=" * 80)
    print()

    # === Research Findings ===
    if results.research_results:
        print("📚 RESEARCH FINDINGS")
        print("-" * 80)
        print()

        print(f"Topics researched: {', '.join(results.research_results.get('topics', []))}")
        print(f"Total sources found: {results.research_results.get('total_sources_found', 0)}")
        print(f"Quality sources: {results.research_results.get('quality_sources', 0)}")
        print(f"Queries executed: {len(results.research_results.get('queries_used', []))}")
        print()

        # Display top sources per topic
        sources = results.research_results.get("sources", [])
        if sources:
            print("Top sources (showing first 5):")
            for i, source in enumerate(sources[:5], 1):
                print(f"\n  {i}. {source.get('title', 'Unknown')}")
                print(f"     URL: {source.get('url', 'N/A')}")
                print(f"     Type: {source.get('source_type', 'unknown')}")
                eval_data = source.get("evaluation", {})
                print(f"     Quality Score: {eval_data.get('overall_score', 0):.2f}")
                print(f"     Credibility: {eval_data.get('credibility_score', 0):.2f}")
                print(f"     Relevance: {eval_data.get('relevance_score', 0):.2f}")
        print()

    # === Analysis Insights ===
    if results.analysis_results:
        print("🔍 ANALYSIS & INSIGHTS")
        print("-" * 80)
        print()

        insights = results.analysis_results.get("key_insights", [])
        if insights:
            print("Key Insights:")
            for insight in insights:
                insight_type = insight.get('type', 'General').title()
                insight_text = insight.get('insight', 'N/A')
                confidence = insight.get('confidence', 'medium')
                print(f"  • [{insight_type}] {insight_text}")
                print(f"    Confidence: {confidence}")
        else:
            print("  No specific insights generated")
        print()

        # Quality distribution
        quality_dist = results.analysis_results.get("quality_distribution", {})
        if quality_dist:
            print("Source Quality Distribution:")
            print(f"  • Mean: {quality_dist.get('mean', 0):.2f}")
            print(f"  • Median: {quality_dist.get('median', 0):.2f}")
            print(f"  • Std Dev: {quality_dist.get('std', 0):.2f}")
            print(f"  • Min: {quality_dist.get('min', 0):.2f}")
            print(f"  • Max: {quality_dist.get('max', 0):.2f}")
        print()

        # Recommendations
        recommendations = results.analysis_results.get("recommendations", [])
        if recommendations:
            print("💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
            print()

    # === Fact-Checking Results ===
    if results.verification_results:
        print("✅ FACT-CHECKING & VERIFICATION")
        print("-" * 80)
        print()

        summary = results.verification_results.get("summary", {})
        total_claims = results.verification_results.get("total_claims", 0)

        print(f"Claims verified: {total_claims}")
        print(f"  • Verified: {summary.get('verified', 0)}")
        print(f"  • Refuted: {summary.get('refuted', 0)}")
        print(f"  • Disputed: {summary.get('disputed', 0)}")
        print(f"  • Unverified: {summary.get('unverified', 0)}")
        print()

        reliability = results.verification_results.get("overall_reliability", 0)
        print(f"Overall Reliability Score: {reliability:.1%}")
        print()

        # Show sample verifications
        verifications = results.verification_results.get("verifications", [])
        if verifications:
            print("Sample Verifications (first 3):")
            for i, verification in enumerate(verifications[:3], 1):
                claim = verification.get("claim", "")
                verdict = verification.get("verdict", "unknown")
                confidence = verification.get("confidence", 0)
                print(f"\n  {i}. Claim: {claim[:60]}...")
                print(f"     Verdict: {verdict.upper()}")
                print(f"     Confidence: {confidence:.2f}")
                print(f"     Supporting sources: {len(verification.get('supporting_sources', []))}")
                print(f"     Contradicting sources: {len(verification.get('contradicting_sources', []))}")
        print()

    # === Synthesis Report ===
    if results.synthesis_results:
        print("📝 GENERATED REPORT")
        print("=" * 80)
        print()

        # Executive summary
        summary = results.synthesis_results.get("summary", "")
        if summary:
            print(summary)
            print()

        # Report metadata
        metadata = results.synthesis_results.get("metadata", {})
        print("\nReport Metadata:")
        print(f"  • Generated: {metadata.get('generated_at', 'N/A')}")
        print(f"  • Sources: {metadata.get('sources_count', 0)}")
        print(f"  • Analysis performed: {'Yes' if metadata.get('analysis_performed') else 'No'}")
        print(f"  • Fact-checked: {'Yes' if metadata.get('fact_checked') else 'No'}")
        print()

        quality = results.synthesis_results.get("quality_score", 0)
        print(f"Report Quality Score: {quality:.2f}/1.00")
        print()

    # ========================================================================
    # Step 5: Database Storage Information
    # ========================================================================

    print("Step 5: Database Storage")
    print("-" * 80)
    print()

    print("Results stored in databases:")
    if results.document_ids:
        print(f"  • Document Store: {len(results.document_ids)} documents")
    if results.vector_store_ids:
        print(f"  • Vector Store: {len(results.vector_store_ids)} embeddings")
    if results.graph_node_ids:
        print(f"  • Graph Store: {len(results.graph_node_ids)} nodes")

    if not (results.document_ids or results.vector_store_ids or results.graph_node_ids):
        print("  • No data stored (storage may be disabled)")
    print()

    # ========================================================================
    # Step 6: Quality Metrics & Performance
    # ========================================================================

    print("Step 6: Quality Metrics & Performance")
    print("-" * 80)
    print()

    print("📊 Overall Metrics:")
    print(f"  • Workflow Status: {results.status.upper()}")
    print(f"  • Overall Quality Score: {results.overall_quality_score:.2f}/1.00")
    print(f"  • Duration: {results.duration_seconds:.2f} seconds")
    print(f"  • Sources Used: {results.sources_used}")
    print(f"  • Insights Generated: {results.insights_generated}")
    print()

    # Performance breakdown
    print("⏱️  Performance Breakdown:")
    print(f"  • Research phase: ~{results.duration_seconds * 0.4:.1f}s (estimated)")
    print(f"  • Analysis phase: ~{results.duration_seconds * 0.3:.1f}s (estimated)")
    print(f"  • Verification phase: ~{results.duration_seconds * 0.2:.1f}s (estimated)")
    print(f"  • Synthesis phase: ~{results.duration_seconds * 0.1:.1f}s (estimated)")
    print()

    # Warnings and errors
    if results.warnings:
        print("⚠️  Warnings:")
        for warning in results.warnings:
            print(f"  • {warning}")
        print()

    if results.errors:
        print("❌ Errors:")
        for error in results.errors:
            print(f"  • {error.get('stage', 'unknown')}: {error.get('error', 'Unknown error')}")
        print()

    # ========================================================================
    # Step 7: Swarm Statistics
    # ========================================================================

    print("Step 7: Multi-Agent Swarm Statistics")
    print("-" * 80)
    print()

    final_status = coordinator.get_swarm_status()

    print("Agent Performance:")
    print(f"  • Total tasks allocated: {final_status['workflows']['total_tasks_allocated']}")
    print(f"  • Total sources processed: {final_status['workflows']['total_sources_processed']}")
    print(f"  • Workflows completed: {final_status['workflows']['completed']}")
    print(f"  • Active workflows: {final_status['workflows']['active']}")
    print()

    # Get workflow history
    history = coordinator.get_workflow_history(limit=5)
    if history:
        print("Recent Workflow History:")
        for i, wf in enumerate(history, 1):
            print(f"  {i}. {wf['type']} - Quality: {wf['quality_score']:.2f} - {wf['status']}")
    print()

    # ========================================================================
    # Step 8: Cleanup
    # ========================================================================

    print("Step 8: Cleanup")
    print("-" * 80)
    print()

    # Gracefully shutdown coordinator
    await coordinator.shutdown()

    print("✓ Coordinator shut down successfully!")
    print()

    # ========================================================================
    # Summary
    # ========================================================================

    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()

    print(f"Successfully performed comparative analysis on {len(topics)} topics:")
    for topic in topics:
        print(f"  • {topic}")
    print()

    print("Performance Summary:")
    print(f"  • Quality Score: {results.overall_quality_score:.2f}/1.00")
    print(f"  • Duration: {results.duration_seconds:.2f} seconds")
    print(f"  • Sources analyzed: {results.sources_used}")
    print(f"  • Insights generated: {results.insights_generated}")
    print()

    print("This semi-complex example demonstrated:")
    print("  ✓ Multi-topic comparative analysis")
    print("  ✓ Multi-agent coordination with 2 researchers")
    print("  ✓ Contract Net Protocol for task allocation")
    print("  ✓ Fact-checking and verification")
    print("  ✓ Database integration for result storage")
    print("  ✓ Comprehensive reporting and synthesis")
    print()

    print("Next steps:")
    print("  • Try complex_example.py for full autonomous swarm features")
    print("  • Experiment with different topics and configurations")
    print("  • Explore the stored data in databases")
    print()
    print("=" * 80)


if __name__ == "__main__":
    # Run the example
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user.")
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise
