"""
指标监控单元测试

测试 Counter / Gauge / Histogram 指标类型及 MetricsManager 管理器
"""

import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock

from ErisPulse.Core.metrics import Counter, Gauge, Histogram, MetricsManager, metrics


# ==================== Counter 测试 ====================

class TestCounter:
    """计数器指标测试"""

    def test_inc_default(self):
        """测试默认递增"""
        c = Counter("test.counter")
        c.inc()
        assert c.get() == 1

    def test_inc_with_value(self):
        """测试指定递增量"""
        c = Counter("test.counter")
        c.inc(5)
        assert c.get() == 5

    def test_inc_multiple(self):
        """测试多次递增"""
        c = Counter("test.counter")
        c.inc()
        c.inc()
        c.inc()
        assert c.get() == 3

    def test_inc_with_tags(self):
        """测试带标签的计数"""
        c = Counter("test.counter")
        c.inc(tags={"type": "a"})
        c.inc(tags={"type": "a"})
        c.inc(tags={"type": "b"})
        assert c.get(tags={"type": "a"}) == 2
        assert c.get(tags={"type": "b"}) == 1
        assert c.get() == 0

    def test_get_default_zero(self):
        """测试未递增时返回0"""
        c = Counter("test.counter")
        assert c.get() == 0

    def test_reset(self):
        """测试重置"""
        c = Counter("test.counter")
        c.inc(10)
        c.reset()
        assert c.get() == 0

    def test_name_property(self):
        """测试名称属性"""
        c = Counter("my.counter", "描述")
        assert c.name == "my.counter"

    def test_to_dict(self):
        """测试导出字典"""
        c = Counter("test.counter")
        c.inc()
        c.inc(tags={"type": "a"})
        d = c.to_dict()
        assert "total" in d
        assert d["total"] == 1

    def test_to_dict_empty(self):
        """测试空计数器导出"""
        c = Counter("test.counter")
        d = c.to_dict()
        assert d == {}


# ==================== Gauge 测试 ====================

class TestGauge:
    """仪表盘指标测试"""

    def test_set(self):
        """测试设置值"""
        g = Gauge("test.gauge")
        g.set(42)
        assert g.get() == 42

    def test_inc(self):
        """测试递增"""
        g = Gauge("test.gauge")
        g.inc()
        assert g.get() == 1

    def test_dec(self):
        """测试递减"""
        g = Gauge("test.gauge")
        g.inc(10)
        g.dec(3)
        assert g.get() == 7

    def test_set_overwrites(self):
        """测试set覆盖inc"""
        g = Gauge("test.gauge")
        g.inc(10)
        g.set(42)
        assert g.get() == 42

    def test_with_tags(self):
        """测试带标签"""
        g = Gauge("test.gauge")
        g.set(1, tags={"host": "a"})
        g.set(2, tags={"host": "b"})
        assert g.get(tags={"host": "a"}) == 1
        assert g.get(tags={"host": "b"}) == 2

    def test_get_default_zero(self):
        """测试默认值为0"""
        g = Gauge("test.gauge")
        assert g.get() == 0

    def test_reset(self):
        """测试重置"""
        g = Gauge("test.gauge")
        g.set(100)
        g.reset()
        assert g.get() == 0

    def test_name_property(self):
        """测试名称属性"""
        g = Gauge("my.gauge")
        assert g.name == "my.gauge"

    def test_to_dict(self):
        """测试导出字典"""
        g = Gauge("test.gauge")
        g.set(42)
        d = g.to_dict()
        assert d["total"] == 42

    def test_negative_values(self):
        """测试负值"""
        g = Gauge("test.gauge")
        g.set(-5)
        assert g.get() == -5
        g.dec(10)
        assert g.get() == -15


# ==================== Histogram 测试 ====================

class TestHistogram:
    """直方图指标测试"""

    def test_observe_single(self):
        """测试单次观察"""
        h = Histogram("test.hist")
        h.observe(0.5)
        s = h.get_summary()
        assert s["count"] == 1
        assert s["sum"] == 0.5

    def test_observe_multiple(self):
        """测试多次观察"""
        h = Histogram("test.hist")
        for v in [0.1, 0.2, 0.3, 0.4, 0.5]:
            h.observe(v)
        s = h.get_summary()
        assert s["count"] == 5
        assert abs(s["sum"] - 1.5) < 0.001
        assert abs(s["avg"] - 0.3) < 0.001

    def test_percentiles(self):
        """测试百分位计算"""
        h = Histogram("test.hist")
        for v in [0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 2.0, 5.0]:
            h.observe(v)
        s = h.get_summary()
        assert s["count"] == 10
        assert s["p50"] >= 0.2
        assert s["p95"] >= 1.0
        assert s["p99"] >= 2.0

    def test_empty_summary(self):
        """测试空直方图摘要"""
        h = Histogram("test.hist")
        s = h.get_summary()
        assert s["count"] == 0
        assert s["sum"] == 0
        assert s["avg"] == 0
        assert s["p50"] == 0

    def test_with_tags(self):
        """测试带标签"""
        h = Histogram("test.hist")
        h.observe(0.1, tags={"endpoint": "api"})
        h.observe(0.2, tags={"endpoint": "api"})
        h.observe(0.3, tags={"endpoint": "ws"})
        s_api = h.get_summary(tags={"endpoint": "api"})
        assert s_api["count"] == 2
        s_ws = h.get_summary(tags={"endpoint": "ws"})
        assert s_ws["count"] == 1

    def test_reset(self):
        """测试重置"""
        h = Histogram("test.hist")
        h.observe(0.5)
        h.reset()
        assert h.get_summary()["count"] == 0

    def test_to_dict(self):
        """测试导出字典"""
        h = Histogram("test.hist")
        h.observe(0.1)
        h.observe(0.2)
        d = h.to_dict()
        assert "total" in d
        assert d["total"]["count"] == 2

    def test_name_property(self):
        """测试名称属性"""
        h = Histogram("my.hist")
        assert h.name == "my.hist"

    def test_custom_buckets(self):
        """测试自定义分桶"""
        h = Histogram("test.hist", buckets=[0.1, 0.5, 1.0])
        h.observe(0.3)
        assert h.get_summary()["count"] == 1


# ==================== MetricsManager 测试 ====================

class TestMetricsManager:
    """指标管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        m = MetricsManager()
        return m

    def test_counter_factory(self, manager):
        """测试计数器工厂"""
        c = manager.counter("test.c", "描述")
        assert isinstance(c, Counter)
        assert c.name == "test.c"

    def test_counter_idempotent(self, manager):
        """测试重复获取同一计数器"""
        c1 = manager.counter("test.c")
        c2 = manager.counter("test.c")
        assert c1 is c2

    def test_gauge_factory(self, manager):
        """测试仪表盘工厂"""
        g = manager.gauge("test.g", "描述")
        assert isinstance(g, Gauge)
        assert g.name == "test.g"

    def test_gauge_idempotent(self, manager):
        """测试重复获取同一仪表盘"""
        g1 = manager.gauge("test.g")
        g2 = manager.gauge("test.g")
        assert g1 is g2

    def test_histogram_factory(self, manager):
        """测试直方图工厂"""
        h = manager.histogram("test.h", "描述")
        assert isinstance(h, Histogram)
        assert h.name == "test.h"

    def test_histogram_idempotent(self, manager):
        """测试重复获取同一直方图"""
        h1 = manager.histogram("test.h")
        h2 = manager.histogram("test.h")
        assert h1 is h2

    def test_get_all_metrics_empty(self, manager):
        """测试空管理器导出"""
        data = manager.get_all_metrics()
        assert data == {"counters": {}, "gauges": {}, "histograms": {}}

    def test_get_all_metrics_with_data(self, manager):
        """测试有数据时导出"""
        manager.counter("c1").inc(5)
        manager.gauge("g1").set(42)
        manager.histogram("h1").observe(0.1)
        data = manager.get_all_metrics()
        assert "c1" in data["counters"]
        assert "g1" in data["gauges"]
        assert "h1" in data["histograms"]

    def test_reset_all(self, manager):
        """测试重置所有指标"""
        c = manager.counter("c1")
        g = manager.gauge("g1")
        h = manager.histogram("h1")
        c.inc(10)
        g.set(42)
        h.observe(0.5)
        manager.reset()
        assert c.get() == 0
        assert g.get() == 0
        assert h.get_summary()["count"] == 0

    def test_register_builtin_metrics(self, manager):
        """测试注册内置指标"""
        manager.register_builtin_metrics()
        data = manager.get_all_metrics()
        assert "erispulse.events.received" in data["counters"]
        assert "erispulse.adapters.online" in data["gauges"]
        assert "erispulse.event.process_time" in data["histograms"]

    def test_register_builtin_idempotent(self, manager):
        """测试内置指标注册幂等"""
        manager.register_builtin_metrics()
        manager.register_builtin_metrics()
        assert "erispulse.events.received" in manager._counters
        assert "erispulse.adapters.online" in manager._gauges
        assert "erispulse.event.process_time" in manager._histograms

    @pytest.mark.asyncio
    async def test_timed_decorator(self, manager):
        """测试@timed装饰器"""
        @manager.timed("test.op")
        async def slow_op():
            await asyncio.sleep(0.01)
            return "done"

        result = await slow_op()
        assert result == "done"

        h = manager.histogram("test.op")
        s = h.get_summary()
        assert s["count"] == 1
        assert s["sum"] >= 0.01

    @pytest.mark.asyncio
    async def test_timed_decorator_default_name(self, manager):
        """测试@timed使用默认名称"""
        @manager.timed()
        async def some_op():
            return "ok"

        await some_op()
        h = manager.histogram("erispulse.operation.duration")
        assert h.get_summary()["count"] == 1

    @pytest.mark.asyncio
    async def test_timed_decorator_with_tags(self, manager):
        """测试@timed带标签"""
        @manager.timed("test.tagged", tags={"env": "test"})
        async def tagged_op():
            return "ok"

        await tagged_op()
        s = manager.histogram("test.tagged").get_summary(tags={"env": "test"})
        assert s["count"] == 1

    @pytest.mark.asyncio
    async def test_timed_decorator_on_exception(self, manager):
        """测试@timed在异常时仍记录"""
        @manager.timed("test.error_op")
        async def failing_op():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            await failing_op()

        h = manager.histogram("test.error_op")
        assert h.get_summary()["count"] == 1


# ==================== 全局实例测试 ====================

class TestGlobalMetrics:
    """全局指标实例测试"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert metrics is not None
        assert isinstance(metrics, MetricsManager)

    def test_global_singleton(self):
        """测试全局单例"""
        from ErisPulse.Core.metrics import metrics as m1
        from ErisPulse.Core.metrics import metrics as m2
        assert m1 is m2


# ==================== 线程安全测试 ====================

class TestThreadSafety:
    """线程安全测试"""

    def test_counter_concurrent_inc(self):
        """测试计数器并发递增"""
        import threading

        c = Counter("test.concurrent")
        threads = []
        for _ in range(10):
            t = threading.Thread(target=lambda: c.inc(100))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

        assert c.get() == 1000

    def test_gauge_concurrent_set(self):
        """测试仪表盘并发设置"""
        import threading

        g = Gauge("test.concurrent")
        threads = []
        for i in range(10):
            t = threading.Thread(target=lambda v=i: g.set(v))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

        assert 0 <= g.get() <= 9

    def test_histogram_concurrent_observe(self):
        """测试直方图并发观察"""
        import threading

        h = Histogram("test.concurrent")
        threads = []
        for _ in range(10):
            t = threading.Thread(target=lambda: h.observe(0.1))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

        assert h.get_summary()["count"] == 10
