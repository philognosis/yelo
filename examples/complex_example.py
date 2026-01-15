#!/usr/bin/env python3
"""
Complex Example - Full Autonomous Research Swarm

This example demonstrates the complete IRAS system with all features:
- Large multi-agent swarm (multiple agents of each type)
- All communication protocols (Contract Net, Blackboard, Pub/Sub)
- Complete database integration (Vector, Graph, Time-Series, Document)
- Autonomous monitoring and health tracking
- Error recovery and resilience
- Adaptive learning from past workflows
- Production-ready deployment patterns

Perfect for:
- Production deployments
- Complex research workflows
- Understanding full system architecture
- Advanced multi-agent coordination

Usage:
    python examples/complex_example.py
"""

import asyncio
from datetime import datetime
from typing import List

from loguru import logger

# Configure logging with more detail for complex example
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    level="DEBUG",  # More verbose logging
)

# Import IRAS components
from iras.orchestration import Coordinator, WorkflowConfig, WorkflowType
from iras.autonomous.monitoring import AlertLevel


async def setup_alert_handlers(coordinator: Coordinator):
    """
    Setup custom alert handlers for monitoring system

    This demonstrates how to handle system alerts in production
    """

    def alert_handler(alert):
        """Handle monitoring alerts"""
        if alert.level == AlertLevel.CRITICAL:
            logger.critical(
                f"🚨 CRITICAL ALERT: {alert.title} - {alert.message}"
            )
        elif alert.level == AlertLevel.ERROR:
            logger.error(
                f"❌ ERROR ALERT: {alert.title} - {alert.message}"
            )
        elif alert.level == AlertLevel.WARNING:
            logger.warning(
                f"⚠️  WARNING ALERT: {alert.title} - {alert.message}"
            )
        else:
            logger.info(
                f"ℹ️  INFO ALERT: {alert.title} - {alert.message}"
            )

    if coordinator.monitoring:
        coordinator.monitoring.add_alert_handler(alert_handler)
        logger.info("Alert handlers configured")


async def display_monitoring_dashboard(coordinator: Coordinator):
    """
    Display real-time monitoring dashboard

    This shows how to access system health metrics
    """
    if not coordinator.monitoring:
        return

    print("\n" + "=" * 80)
    print("SYSTEM HEALTH DASHBOARD")
    print("=" * 80)

    summary = coordinator.monitoring.get_monitoring_summary()

    print(f"\nHealth Status: {summary['health_status'].value.upper()}")
    print(f"Monitoring Active: {'✓ Yes' if summary['monitoring_active'] else '✗ No'}")
    print()

    # Latest metrics
    latest = summary.get('latest_metrics')
    if latest:
        print("System Metrics:")
        print(f"  • CPU Usage: {latest['cpu_percent']:.1f}%")
        print(f"  • Memory Usage: {latest['memory_percent']:.1f}%")
        print(f"  • Process Memory: {latest['process_memory_mb']:.1f} MB")
        print(f"  • Disk Usage: {latest['disk_usage_percent']:.1f}%")
        print()

    # Active alerts
    print(f"Active Alerts: {summary['active_alerts_count']}")
    print(f"  • Critical: {summary['critical_alerts']}")
    print(f"  • Warning: {summary['warning_alerts']}")
    print()

    # Get specific alerts
    active_alerts = coordinator.monitoring.get_active_alerts(
        unacknowledged_only=True
    )
    if active_alerts:
        print("Unacknowledged Alerts:")
        for alert in active_alerts[:5]:  # Show first 5
            print(f"  • [{alert.level.value.upper()}] {alert.title}")

    print("=" * 80 + "\n")


async def demonstrate_blackboard_communication(coordinator: Coordinator):
    """
    Demonstrate Blackboard System communication

    This shows how agents can share information via blackboard
    """
    if not coordinator.blackboard:
        return

    print("\n" + "-" * 80)
    print("Blackboard System Communication")
    print("-" * 80)

    # Read research findings from blackboard
    research_entries = await coordinator.blackboard.read(
        tags={"research"}
    )

    print(f"\nResearch entries on blackboard: {len(research_entries)}")
    for entry in research_entries[:3]:
        print(f"  • {entry.key} (version {entry.version})")
        print(f"    Author: {entry.author_id}")
        print(f"    Tags: {', '.join(entry.tags)}")

    # Read analysis insights
    analysis_entries = await coordinator.blackboard.read(
        tags={"analysis"}
    )

    print(f"\nAnalysis entries on blackboard: {len(analysis_entries)}")
    for entry in analysis_entries[:3]:
        print(f"  • {entry.key} (version {entry.version})")

    # Get blackboard statistics
    stats = coordinator.blackboard.get_stats()
    print(f"\nBlackboard Statistics:")
    print(f"  • Total entries: {stats['total_entries']}")
    print(f"  • Subscribers: {stats['subscribers']}")
    print(f"  • Queue size: {stats['notification_queue_size']}")

    print("-" * 80 + "\n")


async def demonstrate_database_queries(coordinator: Coordinator):
    """
    Demonstrate database query capabilities

    This shows how to retrieve stored research data
    """
    print("\n" + "-" * 80)
    print("Database Query Demonstration")
    print("-" * 80)
    print()

    # Vector store queries
    if coordinator.vector_store:
        stats = coordinator.vector_store.get_stats()
        print("Vector Store:")
        print(f"  • Total embeddings: {stats.get('total_embeddings', 0)}")
        print(f"  • Dimension: {stats.get('dimension', 0)}")
        print()

    # Graph store queries
    if coordinator.graph_store:
        stats = coordinator.graph_store.get_stats()
        print("Graph Store:")
        print(f"  • Total nodes: {stats.get('total_nodes', 0)}")
        print(f"  • Total edges: {stats.get('total_edges', 0)}")
        print()

    # Time-series store queries
    if coordinator.timeseries_store:
        stats = coordinator.timeseries_store.get_stats()
        print("Time-Series Store:")
        print(f"  • Total metrics: {stats.get('total_metrics', 0)}")
        print(f"  • Unique series: {stats.get('unique_series', 0)}")
        print()

    # Document store queries
    if coordinator.document_store:
        stats = coordinator.document_store.get_stats()
        print("Document Store:")
        print(f"  • Total documents: {stats.get('total_documents', 0)}")
        print(f"  • Total size: {stats.get('total_size_mb', 0):.2f} MB")
        print()

    print("-" * 80 + "\n")


async def run_sequential_workflows(
    coordinator: Coordinator,
    topics_list: List[List[str]]
):
    """
    Run multiple workflows sequentially to demonstrate learning

    This shows how the system improves over time with adaptive learning
    """
    print("\n" + "=" * 80)
    print("SEQUENTIAL WORKFLOW EXECUTION (Demonstrating Adaptive Learning)")
    print("=" * 80)
    print()

    results_list = []

    for i, topics in enumerate(topics_list, 1):
        print(f"\n--- Workflow {i}/{len(topics_list)} ---")
        print(f"Topics: {', '.join(topics)}")
        print()

        # Create workflow config
        config = WorkflowConfig(
            workflow_type=WorkflowType.COMPREHENSIVE_RESEARCH,
            topics=topics,
            research_depth=3,
            num_sources=20,
            enable_analysis=True,
            enable_fact_checking=True,
            enable_synthesis=True,
            use_contract_net=True,
            use_blackboard=True,
            use_pubsub=True,
            store_in_databases=True,
            enable_monitoring=True,
            enable_error_recovery=True,
            enable_adaptive_learning=True,
        )

        start_time = datetime.now()
        results = await coordinator.execute_workflow(config)
        duration = (datetime.now() - start_time).total_seconds()

        print(f"\n✓ Workflow {i} completed")
        print(f"  • Status: {results.status}")
        print(f"  • Quality: {results.overall_quality_score:.2f}")
        print(f"  • Duration: {duration:.2f}s")
        print(f"  • Sources: {results.sources_used}")

        results_list.append({
            'workflow': i,
            'quality': results.overall_quality_score,
            'duration': duration,
            'sources': results.sources_used,
        })

        # Brief pause between workflows
        await asyncio.sleep(1)

    # Analyze learning progress
    print("\n" + "-" * 80)
    print("Learning Progress Analysis")
    print("-" * 80)
    print()

    print("Workflow Performance Over Time:")
    for result in results_list:
        print(f"  Workflow {result['workflow']}: "
              f"Quality={result['quality']:.2f}, "
              f"Duration={result['duration']:.1f}s, "
              f"Sources={result['sources']}")

    # Calculate trends
    if len(results_list) >= 2:
        quality_trend = results_list[-1]['quality'] - results_list[0]['quality']
        duration_trend = results_list[-1]['duration'] - results_list[0]['duration']

        print()
        print("Observed Trends:")
        if quality_trend > 0.05:
            print(f"  ✓ Quality improved by {quality_trend:.2f}")
        elif quality_trend < -0.05:
            print(f"  ⚠ Quality decreased by {abs(quality_trend):.2f}")
        else:
            print(f"  → Quality remained stable")

        if duration_trend < -5:
            print(f"  ✓ Processing time improved by {abs(duration_trend):.1f}s")
        elif duration_trend > 5:
            print(f"  ⚠ Processing time increased by {duration_trend:.1f}s")
        else:
            print(f"  → Processing time remained stable")

    print()
    print("-" * 80 + "\n")

    return results_list


async def main():
    """
    Full autonomous research swarm example

    This demonstrates:
    1. Large-scale multi-agent swarm (3 researchers, 2 analysts, etc.)
    2. All communication protocols working together
    3. Complete database integration
    4. Autonomous monitoring with alerts
    5. Error recovery and resilience
    6. Adaptive learning across multiple workflows
    7. Production-ready patterns and best practices
    """

    print("=" * 80)
    print("IRAS COMPLEX EXAMPLE - FULL AUTONOMOUS RESEARCH SWARM")
    print("=" * 80)
    print()
    print("This example demonstrates a production-ready multi-agent system")
    print("with comprehensive features and autonomous operation.")
    print()

    # ========================================================================
    # Step 1: Initialize Production-Scale Coordinator
    # ========================================================================

    print("Step 1: Initializing Production-Scale Coordinator...")
    print("-" * 80)
    print()

    # Create coordinator with large-scale agent swarm
    coordinator = Coordinator(
        num_researchers=3,      # Multiple researchers for parallel work
        num_analysts=2,         # Multiple analysts for diverse perspectives
        num_fact_checkers=2,    # Redundant fact-checking
        num_synthesizers=1,     # Synthesizer for final reports
    )

    print("Agent Swarm Configuration:")
    print(f"  • Researchers: 3 (parallel information gathering)")
    print(f"  • Analysts: 2 (diverse analytical perspectives)")
    print(f"  • Fact-checkers: 2 (redundant verification)")
    print(f"  • Synthesizers: 1 (report generation)")
    print(f"  • Total agents: 8")
    print()

    # Initialize all systems
    print("Initializing systems...")
    await coordinator.initialize()

    # Setup alert handlers
    await setup_alert_handlers(coordinator)

    print()
    print("✓ Coordinator initialized successfully!")
    print()

    # Display initial status
    status = coordinator.get_swarm_status()
    print("System Status:")
    print(f"  • Health: {status['health'].value if hasattr(status['health'], 'value') else status['health']}")
    print(f"  • Agents: {status['agents']['total']} active")
    print(f"  • Communication: All protocols active")
    print(f"  • Databases: All stores ready")
    print()

    # Display initial monitoring dashboard
    await display_monitoring_dashboard(coordinator)

    # ========================================================================
    # Step 2: Execute Comprehensive Research Workflow
    # ========================================================================

    print("Step 2: Executing Comprehensive Research Workflow...")
    print("-" * 80)
    print()

    # Complex research topics
    topics = [
        "Large Language Models architecture",
        "Multi-agent systems coordination",
        "Vector databases for AI",
        "Autonomous AI agents",
    ]

    print("Research Topics:")
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic}")
    print()

    # Create comprehensive workflow configuration
    config = WorkflowConfig(
        workflow_type=WorkflowType.COMPREHENSIVE_RESEARCH,
        topics=topics,

        # High-quality research parameters
        research_depth=4,  # High depth for thorough research
        num_sources=25,    # Many sources for comprehensive coverage

        # Enable all features
        enable_analysis=True,
        enable_fact_checking=True,
        enable_synthesis=True,

        # All communication protocols
        use_contract_net=True,
        use_blackboard=True,
        use_pubsub=True,

        # Full database integration
        store_in_databases=True,

        # Autonomous features
        enable_monitoring=True,
        enable_error_recovery=True,
        enable_adaptive_learning=True,

        # High quality thresholds
        min_source_quality=0.75,
        min_verification_confidence=0.85,

        # Extended timeouts for complex workflow
        research_timeout=600.0,
        analysis_timeout=300.0,
        verification_timeout=240.0,
        synthesis_timeout=180.0,
    )

    print("Workflow Configuration:")
    print(f"  • Type: {config.workflow_type.value}")
    print(f"  • Topics: {len(topics)}")
    print(f"  • Research Depth: {config.research_depth}/5 (High)")
    print(f"  • Sources per topic: {config.num_sources}")
    print(f"  • Min Source Quality: {config.min_source_quality}")
    print(f"  • Min Verification Confidence: {config.min_verification_confidence}")
    print()
    print("Features Enabled:")
    print(f"  • Contract Net Protocol: ✓")
    print(f"  • Blackboard System: ✓")
    print(f"  • Pub/Sub Messaging: ✓")
    print(f"  • Database Storage: ✓")
    print(f"  • Health Monitoring: ✓")
    print(f"  • Error Recovery: ✓")
    print(f"  • Adaptive Learning: ✓")
    print()

    print("Executing comprehensive workflow...")
    print("(This may take several minutes due to the complexity)")
    print()

    start_time = datetime.now()
    results = await coordinator.execute_workflow(config)
    duration = (datetime.now() - start_time).total_seconds()

    print()
    print(f"✓ Workflow completed in {duration:.2f} seconds!")
    print()

    # ========================================================================
    # Step 3: Comprehensive Results Analysis
    # ========================================================================

    print("Step 3: Comprehensive Results Analysis")
    print("=" * 80)
    print()

    # === Executive Summary ===
    print("📊 EXECUTIVE SUMMARY")
    print("-" * 80)
    print(f"Status: {results.status.upper()}")
    print(f"Overall Quality Score: {results.overall_quality_score:.2f}/1.00")
    print(f"Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
    print(f"Total Sources: {results.sources_used}")
    print(f"Insights Generated: {results.insights_generated}")
    print()

    # === Research Phase ===
    if results.research_results:
        print("📚 RESEARCH PHASE")
        print("-" * 80)
        print(f"Topics researched: {len(results.research_results.get('topics', []))}")
        print(f"Sources found: {results.research_results.get('total_sources_found', 0)}")
        print(f"Quality sources: {results.research_results.get('quality_sources', 0)}")
        print(f"Unique queries: {len(results.research_results.get('queries_used', []))}")
        print()

        # Source quality breakdown
        sources = results.research_results.get("sources", [])
        if sources:
            high_quality = sum(1 for s in sources if s.get('evaluation', {}).get('overall_score', 0) >= 0.8)
            medium_quality = sum(1 for s in sources if 0.6 <= s.get('evaluation', {}).get('overall_score', 0) < 0.8)
            low_quality = len(sources) - high_quality - medium_quality

            print("Source Quality Distribution:")
            print(f"  • High quality (≥0.8): {high_quality}")
            print(f"  • Medium quality (0.6-0.8): {medium_quality}")
            print(f"  • Low quality (<0.6): {low_quality}")
            print()

    # === Analysis Phase ===
    if results.analysis_results:
        print("🔍 ANALYSIS PHASE")
        print("-" * 80)

        insights = results.analysis_results.get("key_insights", [])
        print(f"Total insights: {len(insights)}")
        print()

        if insights:
            # Group insights by type
            insight_types = {}
            for insight in insights:
                itype = insight.get('type', 'general')
                if itype not in insight_types:
                    insight_types[itype] = []
                insight_types[itype].append(insight)

            print("Insights by Type:")
            for itype, type_insights in insight_types.items():
                print(f"\n  {itype.title()} ({len(type_insights)}):")
                for insight in type_insights[:2]:  # Show first 2 of each type
                    print(f"    • {insight.get('insight', 'N/A')}")

        print()

        recommendations = results.analysis_results.get("recommendations", [])
        if recommendations:
            print(f"Recommendations: {len(recommendations)}")
            for rec in recommendations[:3]:
                print(f"  • {rec}")
            print()

    # === Verification Phase ===
    if results.verification_results:
        print("✅ VERIFICATION PHASE")
        print("-" * 80)

        total_claims = results.verification_results.get("total_claims", 0)
        summary = results.verification_results.get("summary", {})
        reliability = results.verification_results.get("overall_reliability", 0)

        print(f"Claims analyzed: {total_claims}")
        print(f"Verified: {summary.get('verified', 0)} ({summary.get('verified', 0)/max(total_claims,1)*100:.1f}%)")
        print(f"Refuted: {summary.get('refuted', 0)} ({summary.get('refuted', 0)/max(total_claims,1)*100:.1f}%)")
        print(f"Disputed: {summary.get('disputed', 0)} ({summary.get('disputed', 0)/max(total_claims,1)*100:.1f}%)")
        print(f"Unverified: {summary.get('unverified', 0)} ({summary.get('unverified', 0)/max(total_claims,1)*100:.1f}%)")
        print()
        print(f"Overall Reliability: {reliability:.1%}")
        print()

    # === Synthesis Phase ===
    if results.synthesis_results:
        print("📝 SYNTHESIS PHASE")
        print("-" * 80)
        print()

        # Show executive summary
        summary = results.synthesis_results.get("summary", "")
        if summary:
            print(summary)
            print()

        report_quality = results.synthesis_results.get("quality_score", 0)
        print(f"Report Quality Score: {report_quality:.2f}/1.00")
        print()

    # ========================================================================
    # Step 4: Communication Protocol Analysis
    # ========================================================================

    print("Step 4: Communication Protocol Analysis")
    print("=" * 80)
    print()

    # Contract Net statistics
    if coordinator.contract_net:
        print("Contract Net Protocol:")
        print(f"  • Active tasks: {len(coordinator.contract_net.awarded_tasks)}")
        print(f"  • Completed tasks: {len(coordinator.contract_net.task_results)}")
        print(f"  • Total announcements: {len(coordinator.contract_net.announcements)}")
        print()

    # Demonstrate blackboard
    await demonstrate_blackboard_communication(coordinator)

    # Pub/Sub statistics
    if coordinator.pubsub:
        pubsub_stats = coordinator.pubsub.get_stats()
        print("Pub/Sub Protocol:")
        print(f"  • Total subscriptions: {pubsub_stats['total_subscriptions']}")
        print(f"  • Messages published: {pubsub_stats['total_published']}")
        print(f"  • Messages delivered: {pubsub_stats['total_delivered']}")
        print(f"  • Queue size: {pubsub_stats['message_queue_size']}")
        print()

    # ========================================================================
    # Step 5: Database Integration Analysis
    # ========================================================================

    print("Step 5: Database Integration Analysis")
    print("=" * 80)
    print()

    print("Stored Results:")
    print(f"  • Documents: {len(results.document_ids)}")
    print(f"  • Vector embeddings: {len(results.vector_store_ids)}")
    print(f"  • Graph nodes: {len(results.graph_node_ids)}")
    print()

    # Demonstrate database queries
    await demonstrate_database_queries(coordinator)

    # ========================================================================
    # Step 6: Autonomous Systems Status
    # ========================================================================

    print("Step 6: Autonomous Systems Status")
    print("=" * 80)
    print()

    # Monitoring system
    await display_monitoring_dashboard(coordinator)

    # Error recovery statistics
    if coordinator.error_recovery:
        recovery_stats = coordinator.error_recovery.get_stats()
        print("Error Recovery System:")
        print(f"  • Total errors handled: {recovery_stats.get('total_errors', 0)}")
        print(f"  • Successful recoveries: {recovery_stats.get('successful_recoveries', 0)}")
        print(f"  • Circuit breaker status: {recovery_stats.get('circuit_breaker_status', 'unknown')}")
        print()

    # Adaptive learning statistics
    if coordinator.adaptive_learning:
        learning_stats = coordinator.adaptive_learning.get_stats()
        print("Adaptive Learning System:")
        print(f"  • Total learning sessions: {learning_stats.get('total_sessions', 0)}")
        print(f"  • Learned patterns: {learning_stats.get('patterns_learned', 0)}")
        print(f"  • Current learning rate: {learning_stats.get('learning_rate', 0):.4f}")
        print()

    # ========================================================================
    # Step 7: Sequential Workflows (Demonstrating Learning)
    # ========================================================================

    print("Step 7: Sequential Workflows (Demonstrating Adaptive Learning)")
    print("=" * 80)
    print()

    # Run multiple workflows to demonstrate learning
    workflows_topics = [
        ["Neural networks", "Deep learning"],
        ["Transformer architecture", "Attention mechanisms"],
        ["Graph neural networks", "Message passing"],
    ]

    workflow_results = await run_sequential_workflows(
        coordinator,
        workflows_topics
    )

    # ========================================================================
    # Step 8: Final Statistics and Performance Analysis
    # ========================================================================

    print("Step 8: Final Statistics and Performance Analysis")
    print("=" * 80)
    print()

    final_status = coordinator.get_swarm_status()

    print("Overall System Performance:")
    print(f"  • Total workflows completed: {final_status['workflows']['completed']}")
    print(f"  • Total tasks allocated: {final_status['workflows']['total_tasks_allocated']}")
    print(f"  • Total sources processed: {final_status['workflows']['total_sources_processed']}")
    print(f"  • Average sources per workflow: {final_status['workflows']['total_sources_processed'] / max(final_status['workflows']['completed'], 1):.1f}")
    print()

    # Workflow history
    history = coordinator.get_workflow_history(limit=10)
    if history:
        print("Workflow History:")
        for wf in history:
            print(f"  • {wf['type']}: Quality={wf['quality_score']:.2f}, "
                  f"Status={wf['status']}, Duration={wf['duration']:.1f}s")
        print()

        # Calculate averages
        avg_quality = sum(wf['quality_score'] for wf in history) / len(history)
        avg_duration = sum(wf['duration'] for wf in history) / len(history)
        success_rate = sum(1 for wf in history if wf['status'] == 'success') / len(history)

        print("Performance Averages:")
        print(f"  • Average Quality: {avg_quality:.2f}")
        print(f"  • Average Duration: {avg_duration:.1f}s")
        print(f"  • Success Rate: {success_rate:.1%}")
        print()

    # Agent-specific statistics
    print("Agent-Specific Performance:")
    for i, researcher in enumerate(coordinator.researchers, 1):
        summary = researcher.get_research_summary()
        print(f"  Researcher-{i}:")
        print(f"    • Queries executed: {summary['total_queries']}")
        print(f"    • Sources found: {summary['total_sources']}")
        print(f"    • Uptime: {summary['uptime']:.1f}s")

    for i, analyst in enumerate(coordinator.analysts, 1):
        summary = analyst.get_analysis_summary()
        print(f"  Analyst-{i}:")
        print(f"    • Analyses performed: {summary['total_analyses']}")
        print(f"    • Insights generated: {summary['total_insights']}")
        print(f"    • Uptime: {summary['uptime']:.1f}s")

    print()

    # ========================================================================
    # Step 9: Cleanup and Shutdown
    # ========================================================================

    print("Step 9: Cleanup and Shutdown")
    print("-" * 80)
    print()

    # Final monitoring check
    if coordinator.monitoring:
        active_alerts = coordinator.monitoring.get_active_alerts()
        if active_alerts:
            print(f"⚠️  {len(active_alerts)} active alerts at shutdown")
            for alert in active_alerts[:5]:
                print(f"  • [{alert.level.value}] {alert.title}")
            print()

    # Graceful shutdown
    print("Shutting down coordinator...")
    await coordinator.shutdown()

    print("✓ Coordinator shut down successfully!")
    print()

    # ========================================================================
    # Final Summary
    # ========================================================================

    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print()

    print(f"Successfully executed {len(workflow_results) + 1} comprehensive workflows")
    print(f"using a production-scale multi-agent swarm.")
    print()

    print("System Highlights:")
    print(f"  • Agent Swarm: 8 specialized agents working in coordination")
    print(f"  • Communication: 3 protocols (Contract Net, Blackboard, Pub/Sub)")
    print(f"  • Databases: 4 stores (Vector, Graph, Time-Series, Document)")
    print(f"  • Autonomous: Monitoring, Error Recovery, Adaptive Learning")
    print()

    print("Workflow Performance:")
    print(f"  • Overall Quality: {results.overall_quality_score:.2f}/1.00")
    print(f"  • Total Duration: {duration:.2f}s ({duration/60:.1f} minutes)")
    print(f"  • Sources Processed: {final_status['workflows']['total_sources_processed']}")
    print(f"  • Tasks Allocated: {final_status['workflows']['total_tasks_allocated']}")
    print()

    print("This complex example demonstrated:")
    print("  ✓ Large-scale multi-agent coordination (8 agents)")
    print("  ✓ All three communication protocols")
    print("  ✓ Complete database integration")
    print("  ✓ Real-time health monitoring and alerting")
    print("  ✓ Error recovery and system resilience")
    print("  ✓ Adaptive learning across multiple workflows")
    print("  ✓ Production-ready deployment patterns")
    print()

    print("Production Deployment Considerations:")
    print("  • Scale agent swarm based on workload")
    print("  • Configure monitoring alerts for your environment")
    print("  • Adjust timeouts based on network conditions")
    print("  • Implement persistent database backends")
    print("  • Setup distributed deployment for high availability")
    print("  • Integrate with existing logging and metrics systems")
    print()

    print("Next Steps:")
    print("  • Customize agent swarm for your use case")
    print("  • Integrate with real data sources (APIs, databases)")
    print("  • Deploy to production environment")
    print("  • Monitor and optimize performance")
    print("  • Expand with custom agent types")
    print()

    print("=" * 80)
    print("Thank you for exploring the IRAS multi-agent system!")
    print("=" * 80)


if __name__ == "__main__":
    # Run the complex example
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user.")
        print("Note: Some cleanup operations may not have completed.")
    except Exception as e:
        logger.error(f"Example failed with error: {e}")
        logger.exception("Full traceback:")
        raise
