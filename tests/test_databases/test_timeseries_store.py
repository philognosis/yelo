"""Test Suite for Time-Series Store"""

import pytest
import asyncio
from datetime import datetime, timedelta
from iras.databases.timeseries_store import TimeSeriesStore, TimeSeriesPoint, Aggregation


class TestTimeSeriesStore:
    """Test time-series database operations"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        ts = TimeSeriesStore()
        assert len(ts.series) == 0

    @pytest.mark.asyncio
    async def test_add_point(self):
        ts = TimeSeriesStore()
        timestamp = datetime.now()
        await ts.add_point("metric1", timestamp, 42.5, {"tag": "test"})
        assert "metric1" in ts.series

    @pytest.mark.asyncio
    async def test_query_range(self):
        ts = TimeSeriesStore()
        now = datetime.now()
        await ts.add_point("metric1", now, 1.0)
        await ts.add_point("metric1", now + timedelta(seconds=1), 2.0)

        points = await ts.query(
            "metric1",
            start_time=now - timedelta(seconds=1),
            end_time=now + timedelta(seconds=2)
        )
        assert len(points) == 2

    @pytest.mark.asyncio
    async def test_aggregate_mean(self):
        ts = TimeSeriesStore()
        now = datetime.now()
        await ts.add_point("metric1", now, 10.0)
        await ts.add_point("metric1", now + timedelta(seconds=1), 20.0)

        result = await ts.aggregate(
            "metric1",
            now - timedelta(seconds=1),
            now + timedelta(seconds=2),
            Aggregation.MEAN
        )
        assert result == 15.0

    @pytest.mark.asyncio
    async def test_downsample(self):
        ts = TimeSeriesStore()
        now = datetime.now()
        for i in range(10):
            await ts.add_point("metric1", now + timedelta(seconds=i), float(i))

        downsampled = await ts.downsample("metric1", interval_seconds=5.0)
        assert len(downsampled) < 10

    @pytest.mark.asyncio
    async def test_delete_series(self):
        ts = TimeSeriesStore()
        await ts.add_point("metric1", datetime.now(), 1.0)
        deleted = await ts.delete_series("metric1")
        assert deleted is True
        assert "metric1" not in ts.series
