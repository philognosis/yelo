#!/usr/bin/env python3
"""
Simple Example - Basic Single-Topic Research

This example demonstrates the most basic usage of the IRAS system:
- Single topic research
- Minimal configuration
- Quick results

Perfect for:
- Getting started with IRAS
- Simple research tasks
- Understanding basic workflow

Usage:
    python examples/simple_example.py
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
from iras.orchestration import Coordinator


async def main():
    """
    Simple single-topic research example

    This demonstrates:
    1. Initializing the coordinator with minimal agents
    2. Performing basic research on a single topic
    3. Accessing and displaying results
    """

    print("=" * 80)
    print("IRAS Simple Example - Single Topic Research")
    print("=" * 80)
    print()

    # ========================================================================
    # Step 1: Initialize Coordinator
    # ========================================================================

    print("Step 1: Initializing IRAS Coordinator...")
    print("-" * 80)

    # Create coordinator with minimal agent swarm
    # - 1 researcher for gathering information
    # - 1 analyst for analyzing data
    # - 1 synthesizer for creating reports
    # - 0 fact-checkers (disabled for speed)
    coordinator = Coordinator(
        num_researchers=1,
        num_analysts=1,
        num_fact_checkers=0,  # Disabled for simple example
        num_synthesizers=1,
    )

    # Initialize all systems
    await coordinator.initialize()

    print()
    print("✓ Coordinator initialized successfully!")
    print()

    # Display swarm status
    status = coordinator.get_swarm_status()
    print("Swarm Status:")
    print(f"  • Total agents: {status['agents']['total']}")
    print(f"  • Researchers: {status['agents']['researchers']}")
    print(f"  • Analysts: {status['agents']['analysts']}")
    print(f"  • Synthesizers: {status['agents']['synthesizers']}")
    print()

    # ========================================================================
    # Step 2: Perform Research
    # ========================================================================

    print("Step 2: Performing research...")
    print("-" * 80)

    # Define research topic
    topic = "quantum computing"
    print(f"Topic: {topic}")
    print()

    # Execute simple research workflow
    # - depth=2: Moderate research depth (1-5 scale)
    # - enable_analysis=True: Analyze the research findings
    # - enable_fact_checking=False: Skip fact-checking for speed
    # - enable_synthesis=True: Generate a report

    start_time = datetime.now()

    results = await coordinator.research(
        topic=topic,
        depth=2,
        enable_analysis=True,
        enable_fact_checking=False,
        enable_synthesis=True,
    )

    duration = (datetime.now() - start_time).total_seconds()

    print()
    print(f"✓ Research completed in {duration:.2f} seconds!")
    print()

    # ========================================================================
    # Step 3: Display Results
    # ========================================================================

    print("Step 3: Research Results")
    print("-" * 80)
    print()

    # Research findings
    if results.research_results:
        print("📚 Research Findings:")
        print(f"  • Sources found: {results.research_results.get('total_sources_found', 0)}")
        print(f"  • Quality sources: {results.research_results.get('quality_sources', 0)}")
        print(f"  • Queries executed: {len(results.research_results.get('queries_used', []))}")
        print()

        # Display top sources
        sources = results.research_results.get("sources", [])
        if sources:
            print("  Top Sources:")
            for i, source in enumerate(sources[:3], 1):
                print(f"    {i}. {source.get('title', 'Unknown')}")
                print(f"       URL: {source.get('url', 'N/A')}")
                eval_score = source.get("evaluation", {}).get("overall_score", 0)
                print(f"       Quality Score: {eval_score:.2f}")
        print()

    # Analysis insights
    if results.analysis_results:
        print("🔍 Analysis Insights:")
        insights = results.analysis_results.get("key_insights", [])
        if insights:
            for insight in insights:
                print(f"  • {insight.get('type', 'General').title()}: {insight.get('insight', 'N/A')}")
        else:
            print("  • No specific insights generated")
        print()

        # Recommendations
        recommendations = results.analysis_results.get("recommendations", [])
        if recommendations:
            print("💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
            print()

    # Synthesis report
    if results.synthesis_results:
        print("📝 Generated Report:")
        print("-" * 80)
        summary = results.synthesis_results.get("summary", "")
        if summary:
            print(summary)
        else:
            print("No summary available")
        print()
        print("-" * 80)
        print()

    # ========================================================================
    # Step 4: Quality Metrics
    # ========================================================================

    print("Step 4: Quality Metrics")
    print("-" * 80)
    print()

    print("📊 Workflow Metrics:")
    print(f"  • Status: {results.status}")
    print(f"  • Overall Quality Score: {results.overall_quality_score:.2f}/1.00")
    print(f"  • Duration: {results.duration_seconds:.2f} seconds")
    print(f"  • Sources Used: {results.sources_used}")
    print(f"  • Insights Generated: {results.insights_generated}")
    print()

    # Display any warnings or errors
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
    # Step 5: Cleanup
    # ========================================================================

    print("Step 5: Cleanup")
    print("-" * 80)
    print()

    # Get final status before shutdown
    final_status = coordinator.get_swarm_status()
    print("Final Statistics:")
    print(f"  • Workflows completed: {final_status['workflows']['completed']}")
    print(f"  • Total sources processed: {final_status['workflows']['total_sources_processed']}")
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
    print(f"Successfully researched '{topic}' using the IRAS multi-agent system.")
    print(f"Quality Score: {results.overall_quality_score:.2f}")
    print(f"Duration: {results.duration_seconds:.2f} seconds")
    print()
    print("This simple example demonstrated:")
    print("  ✓ Coordinator initialization with minimal configuration")
    print("  ✓ Single-topic research workflow")
    print("  ✓ Research, analysis, and synthesis stages")
    print("  ✓ Result interpretation and quality metrics")
    print()
    print("Next steps:")
    print("  • Try semi_complex_example.py for multi-topic analysis")
    print("  • Try complex_example.py for full autonomous swarm features")
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
