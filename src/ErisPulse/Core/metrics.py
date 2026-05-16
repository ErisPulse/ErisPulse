"""
ErisPulse 指标监控管理器

提供计数器、仪表盘、直方图三种指标类型，支持标签维度
自动采集框架内置指标，可通过 /metrics 端点暴露

{!--< tips >!--}
1. 使用 counter() / gauge() / histogram() 创建指标
2. 使用 @timed() 装饰器自动计时函数执行
3. 通过 get_all_metrics() 获取所有指标数据
{!--< /tips >!--}
"""

import functools
import threading
import time
from typing import Any, Callable


class Counter:
    """
    计数器指标

    {!--< tips >!--}
    只支持递增，适用于统计事件次数
    {!--< /tips >!--}

    :example:
    >>> c = sdk.metrics.counter("events.total", "事件总数")
    >>> c.inc(tags={"type": "message"})
    """

    def __init__(self, name: str, description: str = ""):
        """
        初始化计数器

        :param name: str 指标名称
        :param description: str 指标描述
        """
        self._name = name
        self._description = description
        self._values: dict[tuple, int] = {}
        self._lock = threading.Lock()

    def _tags_key(self, tags: dict[str, str] | None) -> tuple:
        """
        将标签转换为可哈希的键

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if not tags:
            return ()
        return tuple(sorted(tags.items()))

    def inc(self, value: int = 1, tags: dict[str, str] = None):
        """
        增加计数

        :param value: int 增加量 (默认: 1)
        :param tags: dict 标签字典 (可选)
        """
        with self._lock:
            key = self._tags_key(tags)
            self._values[key] = self._values.get(key, 0) + value

    def get(self, tags: dict[str, str] = None) -> int:
        """
        获取当前计数值

        :param tags: dict 标签字典 (可选)
        :return: int 计数值
        """
        with self._lock:
            return self._values.get(self._tags_key(tags), 0)

    def reset(self):
        """
        重置计数器
        """
        with self._lock:
            self._values.clear()

    @property
    def name(self) -> str:
        """
        :return: str 指标名称
        """
        return self._name

    def to_dict(self) -> dict:
        """
        导出为字典

        :return: dict 指标数据
        """
        with self._lock:
            result = {}
            for tags_key, value in self._values.items():
                tag_str = ",".join(f"{k}={v}" for k, v in tags_key)
                result[tag_str or "total"] = value
            return result


class Gauge:
    """
    仪表盘指标

    {!--< tips >!--}
    支持增减，适用于统计当前在线数量、温度等
    {!--< /tips >!--}

    :example:
    >>> g = sdk.metrics.gauge("bots.online", "在线Bot数量")
    >>> g.inc()
    >>> g.dec()
    """

    def __init__(self, name: str, description: str = ""):
        """
        初始化仪表盘

        :param name: str 指标名称
        :param description: str 指标描述
        """
        self._name = name
        self._description = description
        self._values: dict[tuple, float] = {}
        self._lock = threading.Lock()

    def _tags_key(self, tags: dict[str, str] | None) -> tuple:
        if not tags:
            return ()
        return tuple(sorted(tags.items()))

    def set(self, value: float, tags: dict[str, str] = None):
        """
        设置值

        :param value: float 目标值
        :param tags: dict 标签字典 (可选)
        """
        with self._lock:
            self._values[self._tags_key(tags)] = value

    def inc(self, value: float = 1, tags: dict[str, str] = None):
        """
        增加值

        :param value: float 增加量 (默认: 1)
        :param tags: dict 标签字典 (可选)
        """
        with self._lock:
            key = self._tags_key(tags)
            self._values[key] = self._values.get(key, 0) + value

    def dec(self, value: float = 1, tags: dict[str, str] = None):
        """
        减少值

        :param value: float 减少量 (默认: 1)
        :param tags: dict 标签字典 (可选)
        """
        with self._lock:
            key = self._tags_key(tags)
            self._values[key] = self._values.get(key, 0) - value

    def get(self, tags: dict[str, str] = None) -> float:
        """
        获取当前值

        :param tags: dict 标签字典 (可选)
        :return: float 当前值
        """
        with self._lock:
            return self._values.get(self._tags_key(tags), 0)

    def reset(self):
        """
        重置仪表盘
        """
        with self._lock:
            self._values.clear()

    @property
    def name(self) -> str:
        return self._name

    def to_dict(self) -> dict:
        """
        导出为字典

        :return: dict 指标数据
        """
        with self._lock:
            result = {}
            for tags_key, value in self._values.items():
                tag_str = ",".join(f"{k}={v}" for k, v in tags_key)
                result[tag_str or "total"] = value
            return result


class Histogram:
    """
    直方图指标

    {!--< tips >!--}
    适用于统计延迟分布、响应大小等
    自动计算 P50/P95/P99 分位数
    {!--< /tips >!--}

    :example:
    >>> h = sdk.metrics.histogram("api.latency", "API延迟")
    >>> h.observe(0.05, tags={"endpoint": "send"})
    >>> h.get_summary()
    """

    def __init__(self, name: str, description: str = "",
                 buckets: list[float] = None):
        """
        初始化直方图

        :param name: str 指标名称
        :param description: str 指标描述
        :param buckets: list[float] 分桶边界 (可选)
        """
        self._name = name
        self._description = description
        self._buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self._observations: dict[tuple, list[float]] = {}
        self._lock = threading.Lock()

    def _tags_key(self, tags: dict[str, str] | None) -> tuple:
        if not tags:
            return ()
        return tuple(sorted(tags.items()))

    def observe(self, value: float, tags: dict[str, str] = None):
        """
        记录一个观察值

        :param value: float 观察值
        :param tags: dict 标签字典 (可选)
        """
        with self._lock:
            key = self._tags_key(tags)
            if key not in self._observations:
                self._observations[key] = []
            self._observations[key].append(value)

    def get_summary(self, tags: dict[str, str] = None) -> dict[str, Any]:
        """
        获取统计摘要

        :param tags: dict 标签字典 (可选)
        :return: dict 统计摘要, 包含 count/sum/avg/p50/p95/p99

        :example:
        >>> h.get_summary()
        {"count": 100, "sum": 5.0, "avg": 0.05, "p50": 0.03, "p95": 0.12, "p99": 0.25}
        """
        with self._lock:
            data = self._observations.get(self._tags_key(tags), [])
            if not data:
                return {"count": 0, "sum": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}

            sorted_data = sorted(data)
            count = len(sorted_data)
            total = sum(sorted_data)

            def percentile(p: float) -> float:
                idx = int(count * p / 100)
                return sorted_data[min(idx, count - 1)]

            return {
                "count": count,
                "sum": total,
                "avg": total / count if count > 0 else 0,
                "p50": percentile(50),
                "p95": percentile(95),
                "p99": percentile(99),
            }

    def reset(self):
        """
        重置直方图
        """
        with self._lock:
            self._observations.clear()

    @property
    def name(self) -> str:
        return self._name

    def to_dict(self) -> dict:
        """
        导出为字典

        :return: dict 指标数据
        """
        with self._lock:
            result = {}
            for tags_key, data in self._observations.items():
                tag_str = ",".join(f"{k}={v}" for k, v in tags_key)
                result[tag_str or "total"] = {
                    "count": len(data),
                    "sum": sum(data),
                    "avg": sum(data) / len(data) if data else 0,
                }
            return result


class MetricsManager:
    """
    指标监控管理器

    {!--< tips >!--}
    1. 使用 counter() / gauge() / histogram() 注册指标
    2. 使用 @timed() 装饰器自动记录函数执行时间
    3. 通过 get_all_metrics() 获取 JSON 格式的所有指标
    4. 框架启动后自动注册内置指标
    {!--< /tips >!--}

    :example:
    >>> from ErisPulse import sdk
    >>>
    >>> c = sdk.metrics.counter("my_module.calls", "调用次数")
    >>> c.inc()
    >>>
    >>> @sdk.metrics.timed("my_module.slow_operation")
    ... async def slow_operation():
    ...     await asyncio.sleep(1)
    """

    def __init__(self):
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = threading.Lock()
        self._registered_builtin = False

    def counter(self, name: str, description: str = "") -> Counter:
        """
        获取或创建计数器

        :param name: str 指标名称
        :param description: str 指标描述
        :return: Counter 计数器实例

        :example:
        >>> c = sdk.metrics.counter("events.total", "事件总数")
        >>> c.inc(tags={"type": "message"})
        """
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description)
            return self._counters[name]

    def gauge(self, name: str, description: str = "") -> Gauge:
        """
        获取或创建仪表盘

        :param name: str 指标名称
        :param description: str 指标描述
        :return: Gauge 仪表盘实例

        :example:
        >>> g = sdk.metrics.gauge("bots.online", "在线Bot数量")
        >>> g.inc()
        """
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description)
            return self._gauges[name]

    def histogram(self, name: str, description: str = "",
                  buckets: list[float] = None) -> Histogram:
        """
        获取或创建直方图

        :param name: str 指标名称
        :param description: str 指标描述
        :param buckets: list[float] 分桶边界 (可选)
        :return: Histogram 直方图实例

        :example:
        >>> h = sdk.metrics.histogram("api.latency", "API延迟")
        >>> h.observe(0.05)
        """
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, buckets)
            return self._histograms[name]

    def timed(self, name: str = None, tags: dict = None):
        """
        计时装饰器

        :param name: str 指标名称 (默认: "erispulse.operation.duration")
        :param tags: dict 标签 (可选)
        :return: Callable 装饰器

        :example:
        >>> @sdk.metrics.timed("my_module.api_call", tags={"endpoint": "weather"})
        ... async def fetch_weather(city):
        ...     ...
        """
        hist_name = name or "erispulse.operation.duration"

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                hist = self.histogram(hist_name)
                start = time.monotonic()
                try:
                    return await func(*args, **kwargs)
                finally:
                    hist.observe(time.monotonic() - start, tags=tags)
            return wrapper
        return decorator

    def register_builtin_metrics(self):
        """
        注册框架内置指标

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if self._registered_builtin:
            return
        self._registered_builtin = True

        self.counter("erispulse.events.received", "收到的事件总数")
        self.counter("erispulse.events.handled", "处理的事件总数")
        self.counter("erispulse.commands.executed", "命令执行次数")
        self.counter("erispulse.commands.errors", "命令执行错误次数")
        self.counter("erispulse.messages.sent", "发送消息总数")

        self.gauge("erispulse.adapters.online", "在线适配器数量")
        self.gauge("erispulse.bots.online", "在线Bot数量")
        self.gauge("erispulse.modules.loaded", "已加载模块数量")

        self.histogram("erispulse.event.process_time", "事件处理延迟")
        self.histogram("erispulse.api.latency", "API调用延迟")

    def get_all_metrics(self) -> dict[str, Any]:
        """
        获取所有指标数据

        :return: dict 所有指标的 JSON 数据

        :example:
        >>> data = sdk.metrics.get_all_metrics()
        """
        result = {
            "counters": {},
            "gauges": {},
            "histograms": {},
        }
        for name, c in self._counters.items():
            result["counters"][name] = c.to_dict()
        for name, g in self._gauges.items():
            result["gauges"][name] = g.to_dict()
        for name, h in self._histograms.items():
            result["histograms"][name] = h.to_dict()
        return result

    def reset(self):
        """
        重置所有指标
        """
        with self._lock:
            for c in self._counters.values():
                c.reset()
            for g in self._gauges.values():
                g.reset()
            for h in self._histograms.values():
                h.reset()


metrics: MetricsManager = MetricsManager()

__all__ = [
    "metrics",
    "MetricsManager",
    "Counter",
    "Gauge",
    "Histogram",
]
