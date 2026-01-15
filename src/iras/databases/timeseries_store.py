"""
Time-Series Database for Metrics

Implements:
- Metric storage and retrieval
- Time-range queries
- Aggregations (mean, max, min, percentiles)
- Anomaly detection
- Trend analysis
"""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger


@dataclass
class DataPoint:
    """Time-series data point"""

    timestamp: datetime
    value: float
    tags: Dict[str, str]


@dataclass
class AggregationResult:
    """Aggregated time-series data"""

    start_time: datetime
    end_time: datetime
    count: int
    mean: float
    min: float
    max: float
    sum: float
    stddev: float


class TimeSeries:
    """Individual time series"""

    def __init__(self, name: str, max_points: int = 100000):
        self.name = name
        self.max_points = max_points
        self.data: Deque[DataPoint] = deque(maxlen=max_points)
        self._lock = asyncio.Lock()

    async def add_point(
        self,
        value: float,
        timestamp: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add data point"""
        async with self._lock:
            point = DataPoint(
                timestamp=timestamp or datetime.now(),
                value=value,
                tags=tags or {},
            )
            self.data.append(point)

    async def get_range(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[DataPoint]:
        """Get data points in time range"""
        async with self._lock:
            results = []

            for point in self.data:
                # Filter by time range
                if start and point.timestamp < start:
                    continue
                if end and point.timestamp > end:
                    continue

                # Filter by tags
                if tags:
                    if not all(point.tags.get(k) == v for k, v in tags.items()):
                        continue

                results.append(point)

            return results

    async def aggregate(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[AggregationResult]:
        """Aggregate data points"""
        points = await self.get_range(start, end, tags)

        if not points:
            return None

        values = [p.value for p in points]

        return AggregationResult(
            start_time=points[0].timestamp,
            end_time=points[-1].timestamp,
            count=len(values),
            mean=float(np.mean(values)),
            min=float(np.min(values)),
            max=float(np.max(values)),
            sum=float(np.sum(values)),
            stddev=float(np.std(values)),
        )

    async def downsample(
        self,
        interval: timedelta,
        aggregation: str = "mean",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Tuple[datetime, float]]:
        """
        Downsample time series by interval

        Args:
            interval: Time interval for each bucket
            aggregation: 'mean', 'max', 'min', 'sum', 'count'
            start: Start time
            end: End time

        Returns:
            List of (timestamp, value) tuples
        """
        points = await self.get_range(start, end)

        if not points:
            return []

        # Group by interval
        buckets: Dict[datetime, List[float]] = defaultdict(list)

        interval_seconds = interval.total_seconds()

        for point in points:
            # Round timestamp down to interval
            timestamp_seconds = point.timestamp.timestamp()
            bucket_seconds = (timestamp_seconds // interval_seconds) * interval_seconds
            bucket_time = datetime.fromtimestamp(bucket_seconds)

            buckets[bucket_time].append(point.value)

        # Aggregate each bucket
        results = []
        for bucket_time in sorted(buckets.keys()):
            values = buckets[bucket_time]

            if aggregation == "mean":
                agg_value = float(np.mean(values))
            elif aggregation == "max":
                agg_value = float(np.max(values))
            elif aggregation == "min":
                agg_value = float(np.min(values))
            elif aggregation == "sum":
                agg_value = float(np.sum(values))
            elif aggregation == "count":
                agg_value = float(len(values))
            else:
                raise ValueError(f"Unknown aggregation: {aggregation}")

            results.append((bucket_time, agg_value))

        return results


class TimeSeriesStore:
    """
    Time-series database for multi-agent systems

    Simplified implementation for demonstration.
    In production, use InfluxDB, Prometheus, or TimescaleDB.

    Features:
    - Multi-metric storage
    - Time-range queries
    - Aggregations
    - Downsampling
    - Anomaly detection
    - Forecasting
    """

    def __init__(self):
        self.series: Dict[str, TimeSeries] = {}
        self._lock = asyncio.Lock()

        logger.info("Time-series store initialized")

    async def write_point(
        self,
        metric: str,
        value: float,
        timestamp: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Write data point

        Args:
            metric: Metric name
            value: Metric value
            timestamp: Optional timestamp (default: now)
            tags: Optional tags for filtering
        """
        async with self._lock:
            if metric not in self.series:
                self.series[metric] = TimeSeries(metric)

        await self.series[metric].add_point(value, timestamp, tags)

    async def write_batch(
        self,
        points: List[Tuple[str, float, Optional[datetime], Optional[Dict[str, str]]]],
    ) -> None:
        """
        Write multiple points in batch

        Args:
            points: List of (metric, value, timestamp, tags) tuples
        """
        for metric, value, timestamp, tags in points:
            await self.write_point(metric, value, timestamp, tags)

    async def query(
        self,
        metric: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[DataPoint]:
        """
        Query time series data

        Args:
            metric: Metric name
            start: Start time
            end: End time
            tags: Tag filters

        Returns:
            List of data points
        """
        if metric not in self.series:
            return []

        return await self.series[metric].get_range(start, end, tags)

    async def aggregate(
        self,
        metric: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[AggregationResult]:
        """
        Aggregate metric over time range

        Args:
            metric: Metric name
            start: Start time
            end: End time
            tags: Tag filters

        Returns:
            Aggregation result
        """
        if metric not in self.series:
            return None

        return await self.series[metric].aggregate(start, end, tags)

    async def detect_anomalies(
        self,
        metric: str,
        window: timedelta = timedelta(hours=1),
        threshold: float = 3.0,
    ) -> List[Tuple[datetime, float, float]]:
        """
        Detect anomalies using z-score method

        Args:
            metric: Metric name
            window: Time window to analyze
            threshold: Z-score threshold (default: 3.0 = 3 standard deviations)

        Returns:
            List of (timestamp, value, z_score) for anomalous points
        """
        if metric not in self.series:
            return []

        # Get recent data
        end_time = datetime.now()
        start_time = end_time - window

        points = await self.series[metric].get_range(start_time, end_time)

        if len(points) < 10:  # Need minimum points
            return []

        # Calculate statistics
        values = np.array([p.value for p in points])
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:  # No variation
            return []

        # Find anomalies
        anomalies = []
        for point in points:
            z_score = abs((point.value - mean) / std)
            if z_score > threshold:
                anomalies.append((point.timestamp, point.value, float(z_score)))

        logger.info(f"Detected {len(anomalies)} anomalies in {metric}")
        return anomalies

    async def forecast(
        self,
        metric: str,
        horizon: timedelta = timedelta(hours=1),
        method: str = "moving_average",
        window: timedelta = timedelta(hours=6),
    ) -> List[Tuple[datetime, float]]:
        """
        Forecast future values

        Args:
            metric: Metric name
            horizon: How far ahead to forecast
            method: 'moving_average' or 'linear_regression'
            window: Historical window to use

        Returns:
            List of (timestamp, predicted_value) tuples
        """
        if metric not in self.series:
            return []

        # Get historical data
        end_time = datetime.now()
        start_time = end_time - window

        points = await self.series[metric].get_range(start_time, end_time)

        if len(points) < 10:
            return []

        # Simple moving average forecast
        if method == "moving_average":
            values = [p.value for p in points]
            avg = float(np.mean(values))

            # Generate forecast points (constant prediction)
            forecast_points = []
            current_time = end_time

            # Generate hourly forecasts
            num_hours = int(horizon.total_seconds() / 3600)
            for i in range(1, num_hours + 1):
                forecast_time = current_time + timedelta(hours=i)
                forecast_points.append((forecast_time, avg))

            return forecast_points

        # Linear trend forecast
        elif method == "linear_regression":
            # Convert timestamps to numerical values (hours since start)
            base_time = points[0].timestamp
            x = np.array([(p.timestamp - base_time).total_seconds() / 3600 for p in points])
            y = np.array([p.value for p in points])

            # Fit linear model: y = mx + b
            coeffs = np.polyfit(x, y, 1)
            m, b = coeffs[0], coeffs[1]

            # Generate forecast
            forecast_points = []
            current_time = end_time
            current_x = (current_time - base_time).total_seconds() / 3600

            num_hours = int(horizon.total_seconds() / 3600)
            for i in range(1, num_hours + 1):
                forecast_time = current_time + timedelta(hours=i)
                forecast_x = current_x + i
                forecast_value = float(m * forecast_x + b)
                forecast_points.append((forecast_time, forecast_value))

            return forecast_points

        else:
            raise ValueError(f"Unknown forecast method: {method}")

    async def get_metrics(self) -> List[str]:
        """Get list of all metrics"""
        return list(self.series.keys())

    async def delete_metric(self, metric: str) -> bool:
        """Delete entire metric"""
        async with self._lock:
            if metric in self.series:
                del self.series[metric]
                logger.info(f"Deleted metric: {metric}")
                return True
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get store statistics"""
        total_points = sum(len(ts.data) for ts in self.series.values())

        return {
            "num_metrics": len(self.series),
            "total_data_points": total_points,
            "metrics": list(self.series.keys()),
        }
