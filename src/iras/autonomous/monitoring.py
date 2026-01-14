"""
Self-Monitoring System for Autonomous Agents

Provides comprehensive health monitoring, performance tracking,
anomaly detection, and alerting capabilities for autonomous agents.

Features:
- Real-time health monitoring (CPU, memory, response times)
- Performance metrics tracking and analysis
- Anomaly detection using statistical methods
- Multi-channel alerting system
- Historical data analysis
- Threshold-based monitoring
"""

from __future__ import annotations

import asyncio
import os
import platform
import psutil
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Set
from uuid import UUID, uuid4

import numpy as np
from loguru import logger
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class AlertLevel(str, Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Types of metrics to track"""

    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    TASK_COMPLETION_RATE = "task_completion_rate"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    CUSTOM = "custom"


@dataclass
class MetricValue:
    """Single metric measurement"""

    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthMetrics(BaseModel):
    """System health metrics snapshot"""

    timestamp: datetime = Field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    process_cpu_percent: float = 0.0
    process_memory_mb: float = 0.0
    disk_usage_percent: float = 0.0

    # Agent-specific metrics
    active_tasks: int = 0
    queue_size: int = 0
    average_response_time: float = 0.0
    error_count: int = 0
    success_rate: float = 1.0

    # Custom metrics
    custom_metrics: Dict[str, float] = Field(default_factory=dict)


class Alert(BaseModel):
    """System alert"""

    id: UUID = Field(default_factory=uuid4)
    level: AlertLevel
    title: str
    message: str
    metric_type: Optional[MetricType] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricThreshold(BaseModel):
    """Threshold configuration for a metric"""

    metric_type: MetricType
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison: str = "greater_than"  # greater_than, less_than, equals
    window_size: int = 5  # Number of samples to average
    consecutive_violations: int = 3  # Violations before alerting


class AnomalyDetector:
    """
    Statistical anomaly detection for metrics

    Uses multiple methods:
    - Z-score (standard deviations from mean)
    - Moving average deviation
    - Percentile-based detection
    """

    def __init__(
        self,
        window_size: int = 100,
        z_threshold: float = 3.0,
        percentile_threshold: float = 95.0,
    ):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.percentile_threshold = percentile_threshold

        # Store historical values per metric type
        self.history: Dict[MetricType, Deque[float]] = {}

    def add_value(self, metric_type: MetricType, value: float) -> None:
        """Add a new metric value to history"""
        if metric_type not in self.history:
            self.history[metric_type] = deque(maxlen=self.window_size)

        self.history[metric_type].append(value)

    def detect_anomaly(
        self,
        metric_type: MetricType,
        value: float,
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Detect if a value is anomalous

        Returns:
            (is_anomaly, details_dict)
        """
        if metric_type not in self.history or len(self.history[metric_type]) < 10:
            # Not enough data
            return False, {"reason": "insufficient_data"}

        values = np.array(list(self.history[metric_type]))

        # Z-score method
        mean = np.mean(values)
        std = np.std(values)

        if std > 0:
            z_score = abs((value - mean) / std)
            if z_score > self.z_threshold:
                return True, {
                    "method": "z_score",
                    "z_score": float(z_score),
                    "mean": float(mean),
                    "std": float(std),
                    "threshold": self.z_threshold,
                }

        # Percentile method
        percentile = np.percentile(values, self.percentile_threshold)
        if value > percentile:
            return True, {
                "method": "percentile",
                "value": float(value),
                "percentile": float(percentile),
                "threshold": self.percentile_threshold,
            }

        return False, {}

    def get_statistics(self, metric_type: MetricType) -> Dict[str, float]:
        """Get statistical summary for a metric"""
        if metric_type not in self.history or not self.history[metric_type]:
            return {}

        values = np.array(list(self.history[metric_type]))

        return {
            "count": len(values),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
            "p95": float(np.percentile(values, 95)),
            "p99": float(np.percentile(values, 99)),
        }


class MonitoringSystem:
    """
    Comprehensive monitoring system for autonomous agents

    Features:
    - Real-time health monitoring
    - Performance metrics tracking
    - Anomaly detection
    - Alert generation and management
    - Historical data retention
    """

    def __init__(
        self,
        agent_id: UUID,
        metrics_retention_hours: int = 24,
        alert_retention_hours: int = 168,  # 7 days
        monitoring_interval: float = 5.0,  # seconds
    ):
        self.agent_id = agent_id
        self.metrics_retention = timedelta(hours=metrics_retention_hours)
        self.alert_retention = timedelta(hours=alert_retention_hours)
        self.monitoring_interval = monitoring_interval

        # State
        self.running = False
        self.current_health = HealthStatus.UNKNOWN

        # Metrics storage
        self.metrics_history: Deque[HealthMetrics] = deque(maxlen=10000)
        self.metric_values: Dict[MetricType, Deque[MetricValue]] = {}

        # Alerts
        self.active_alerts: List[Alert] = []
        self.alert_history: Deque[Alert] = deque(maxlen=1000)

        # Configuration
        self.thresholds: Dict[MetricType, MetricThreshold] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []

        # Anomaly detection
        self.anomaly_detector = AnomalyDetector()

        # Tracking
        self.violation_counts: Dict[MetricType, int] = {}

        # System process
        self.process = psutil.Process(os.getpid())

        # Background task
        self._monitor_task: Optional[asyncio.Task] = None

        # Register default thresholds
        self._register_default_thresholds()

        logger.info(f"Monitoring system initialized for agent {agent_id}")

    def _register_default_thresholds(self) -> None:
        """Register default monitoring thresholds"""

        # CPU usage threshold
        self.thresholds[MetricType.CPU_USAGE] = MetricThreshold(
            metric_type=MetricType.CPU_USAGE,
            warning_threshold=70.0,
            critical_threshold=90.0,
            comparison="greater_than",
            window_size=3,
            consecutive_violations=2,
        )

        # Memory usage threshold
        self.thresholds[MetricType.MEMORY_USAGE] = MetricThreshold(
            metric_type=MetricType.MEMORY_USAGE,
            warning_threshold=75.0,
            critical_threshold=90.0,
            comparison="greater_than",
            window_size=3,
            consecutive_violations=2,
        )

        # Response time threshold (milliseconds)
        self.thresholds[MetricType.RESPONSE_TIME] = MetricThreshold(
            metric_type=MetricType.RESPONSE_TIME,
            warning_threshold=1000.0,
            critical_threshold=5000.0,
            comparison="greater_than",
            window_size=5,
            consecutive_violations=3,
        )

        # Error rate threshold (percentage)
        self.thresholds[MetricType.ERROR_RATE] = MetricThreshold(
            metric_type=MetricType.ERROR_RATE,
            warning_threshold=5.0,
            critical_threshold=10.0,
            comparison="greater_than",
            window_size=10,
            consecutive_violations=3,
        )

    async def start(self) -> None:
        """Start monitoring"""
        if self.running:
            logger.warning("Monitoring already running")
            return

        self.running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Monitoring started")

    async def stop(self) -> None:
        """Stop monitoring"""
        if not self.running:
            return

        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect metrics
                metrics = await self.collect_metrics()

                # Store metrics
                self.metrics_history.append(metrics)

                # Check thresholds
                await self._check_thresholds(metrics)

                # Update health status
                self._update_health_status(metrics)

                # Cleanup old data
                self._cleanup_old_data()

                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def collect_metrics(self) -> HealthMetrics:
        """Collect current system and agent metrics"""
        try:
            # System-wide metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Process-specific metrics
            process_cpu = self.process.cpu_percent()
            process_memory = self.process.memory_info()

            metrics = HealthMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                process_cpu_percent=process_cpu,
                process_memory_mb=process_memory.rss / (1024 * 1024),
                disk_usage_percent=disk.percent,
            )

            # Add to anomaly detector
            self.anomaly_detector.add_value(MetricType.CPU_USAGE, cpu_percent)
            self.anomaly_detector.add_value(MetricType.MEMORY_USAGE, memory.percent)

            return metrics

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return HealthMetrics()

    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a custom metric value"""
        metric = MetricValue(
            type=metric_type,
            value=value,
            metadata=metadata or {},
        )

        if metric_type not in self.metric_values:
            self.metric_values[metric_type] = deque(maxlen=1000)

        self.metric_values[metric_type].append(metric)

        # Add to anomaly detector
        self.anomaly_detector.add_value(metric_type, value)

        # Check for anomalies
        is_anomaly, details = self.anomaly_detector.detect_anomaly(metric_type, value)
        if is_anomaly:
            self._create_alert(
                level=AlertLevel.WARNING,
                title=f"Anomaly detected in {metric_type.value}",
                message=f"Value {value} is anomalous. Details: {details}",
                metric_type=metric_type,
                metric_value=value,
                metadata={"anomaly_details": details},
            )

    async def _check_thresholds(self, metrics: HealthMetrics) -> None:
        """Check metric thresholds and generate alerts"""

        # Check CPU threshold
        await self._check_metric_threshold(
            MetricType.CPU_USAGE,
            metrics.cpu_percent,
        )

        # Check memory threshold
        await self._check_metric_threshold(
            MetricType.MEMORY_USAGE,
            metrics.memory_percent,
        )

    async def _check_metric_threshold(
        self,
        metric_type: MetricType,
        value: float,
    ) -> None:
        """Check a specific metric against its threshold"""
        threshold = self.thresholds.get(metric_type)
        if not threshold:
            return

        # Determine if threshold is violated
        violated = False
        level = None
        threshold_value = None

        if threshold.comparison == "greater_than":
            if threshold.critical_threshold and value >= threshold.critical_threshold:
                violated = True
                level = AlertLevel.CRITICAL
                threshold_value = threshold.critical_threshold
            elif threshold.warning_threshold and value >= threshold.warning_threshold:
                violated = True
                level = AlertLevel.WARNING
                threshold_value = threshold.warning_threshold
        elif threshold.comparison == "less_than":
            if threshold.critical_threshold and value <= threshold.critical_threshold:
                violated = True
                level = AlertLevel.CRITICAL
                threshold_value = threshold.critical_threshold
            elif threshold.warning_threshold and value <= threshold.warning_threshold:
                violated = True
                level = AlertLevel.WARNING
                threshold_value = threshold.warning_threshold

        # Track consecutive violations
        if violated:
            self.violation_counts[metric_type] = self.violation_counts.get(metric_type, 0) + 1

            # Create alert if consecutive violations exceeded
            if self.violation_counts[metric_type] >= threshold.consecutive_violations:
                self._create_alert(
                    level=level,
                    title=f"{metric_type.value} threshold exceeded",
                    message=f"{metric_type.value} is {value:.2f}, exceeding {level.value} threshold of {threshold_value:.2f}",
                    metric_type=metric_type,
                    metric_value=value,
                    threshold_value=threshold_value,
                )
                # Reset counter after alerting
                self.violation_counts[metric_type] = 0
        else:
            # Reset violation counter if not violated
            self.violation_counts[metric_type] = 0

    def _create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        metric_type: Optional[MetricType] = None,
        metric_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """Create and dispatch an alert"""
        alert = Alert(
            level=level,
            title=title,
            message=message,
            metric_type=metric_type,
            metric_value=metric_value,
            threshold_value=threshold_value,
            metadata=metadata or {},
        )

        self.active_alerts.append(alert)
        self.alert_history.append(alert)

        # Dispatch to handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

        logger.warning(f"Alert created: [{level.value}] {title}")

        return alert

    def _update_health_status(self, metrics: HealthMetrics) -> None:
        """Update overall health status based on metrics"""
        # Determine health based on metrics
        if metrics.cpu_percent >= 90 or metrics.memory_percent >= 90:
            new_status = HealthStatus.CRITICAL
        elif metrics.cpu_percent >= 70 or metrics.memory_percent >= 75:
            new_status = HealthStatus.WARNING
        elif metrics.success_rate < 0.5:
            new_status = HealthStatus.DEGRADED
        else:
            new_status = HealthStatus.HEALTHY

        if new_status != self.current_health:
            logger.info(f"Health status changed: {self.current_health} -> {new_status}")
            self.current_health = new_status

    def _cleanup_old_data(self) -> None:
        """Remove old metrics and alerts"""
        cutoff_time = datetime.now() - self.alert_retention

        # Remove resolved/old alerts
        self.active_alerts = [
            alert for alert in self.active_alerts
            if not alert.resolved and alert.timestamp > cutoff_time
        ]

    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Register an alert handler"""
        self.alert_handlers.append(handler)

    def acknowledge_alert(self, alert_id: UUID) -> bool:
        """Acknowledge an alert"""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert {alert_id} acknowledged")
                return True
        return False

    def resolve_alert(self, alert_id: UUID) -> bool:
        """Mark an alert as resolved"""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.resolved = True
                logger.info(f"Alert {alert_id} resolved")
                return True
        return False

    def get_health_status(self) -> HealthStatus:
        """Get current health status"""
        return self.current_health

    def get_latest_metrics(self) -> Optional[HealthMetrics]:
        """Get most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_metric_statistics(self, metric_type: MetricType) -> Dict[str, float]:
        """Get statistical summary for a metric"""
        return self.anomaly_detector.get_statistics(metric_type)

    def get_active_alerts(
        self,
        level: Optional[AlertLevel] = None,
        unacknowledged_only: bool = False,
    ) -> List[Alert]:
        """Get active alerts with optional filtering"""
        alerts = self.active_alerts

        if level:
            alerts = [a for a in alerts if a.level == level]

        if unacknowledged_only:
            alerts = [a for a in alerts if not a.acknowledged]

        return alerts

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        latest_metrics = self.get_latest_metrics()

        return {
            "agent_id": str(self.agent_id),
            "health_status": self.current_health,
            "monitoring_active": self.running,
            "latest_metrics": latest_metrics.model_dump() if latest_metrics else None,
            "active_alerts_count": len(self.active_alerts),
            "critical_alerts": len([a for a in self.active_alerts if a.level == AlertLevel.CRITICAL]),
            "warning_alerts": len([a for a in self.active_alerts if a.level == AlertLevel.WARNING]),
            "metrics_history_size": len(self.metrics_history),
            "monitoring_interval": self.monitoring_interval,
        }
