"""
Autonomous Operation Module for IRAS

Provides comprehensive autonomous capabilities for AI agents including:
- Self-monitoring and health tracking
- Error recovery and resilience
- Adaptive learning and continuous improvement
- Autonomous decision making and execution
- Human-in-the-loop escalation

Main Components:
- MonitoringSystem: Real-time health and performance monitoring
- ErrorRecoverySystem: Automatic error recovery with retry and circuit breaker
- AdaptiveLearningSystem: Experience-based learning and strategy optimization
- AutonomousController: Main controller integrating all autonomous features

Example Usage:
    ```python
    from iras.autonomous import AutonomousController, AutonomyConfig, AutonomyLevel
    from uuid import uuid4

    # Create autonomous controller
    agent_id = uuid4()
    config = AutonomyConfig(
        autonomy_level=AutonomyLevel.SEMI_AUTONOMOUS,
        confidence_threshold=0.7,
        enable_monitoring=True,
        enable_learning=True,
        enable_recovery=True,
    )

    controller = AutonomousController(agent_id, config)

    # Start autonomous operation
    await controller.start()

    # Add tasks for autonomous execution
    from iras.autonomous import AutonomousTask

    task = AutonomousTask(
        name="data_analysis",
        description="Analyze dataset and generate insights",
        goal="Complete analysis with >90% accuracy",
        priority=2,
    )
    controller.add_task(task)

    # Get status
    status = controller.get_status()
    print(f"Health: {status['health_status']}")
    print(f"Performance Score: {status['performance_score']}")
    ```
"""

from iras.autonomous.adaptive_learning import (
    AdaptiveLearningSystem,
    Experience,
    ExperienceType,
    OutcomeType,
    Pattern,
    StrategyPerformance,
    StrategyType,
)
from iras.autonomous.autonomy import (
    AutonomousController,
    AutonomousTask,
    AutonomyConfig,
    AutonomyLevel,
    Decision,
    DecisionType,
)
from iras.autonomous.error_recovery import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    Checkpoint,
    ErrorRecord,
    ErrorRecoverySystem,
    RecoveryAction,
    RetryConfig,
    RetryStrategy,
)
from iras.autonomous.monitoring import (
    Alert,
    AlertLevel,
    AnomalyDetector,
    HealthMetrics,
    HealthStatus,
    MetricThreshold,
    MetricType,
    MetricValue,
    MonitoringSystem,
)

__all__ = [
    # Main Controller
    "AutonomousController",
    "AutonomousTask",
    "AutonomyConfig",
    "AutonomyLevel",
    "Decision",
    "DecisionType",
    # Monitoring
    "MonitoringSystem",
    "HealthStatus",
    "HealthMetrics",
    "MetricType",
    "MetricValue",
    "Alert",
    "AlertLevel",
    "AnomalyDetector",
    "MetricThreshold",
    # Error Recovery
    "ErrorRecoverySystem",
    "RetryConfig",
    "RetryStrategy",
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerOpenError",
    "RecoveryAction",
    "ErrorRecord",
    "Checkpoint",
    # Adaptive Learning
    "AdaptiveLearningSystem",
    "Experience",
    "ExperienceType",
    "OutcomeType",
    "StrategyType",
    "StrategyPerformance",
    "Pattern",
]

__version__ = "1.0.0"
