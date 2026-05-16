# `ErisPulse.Core.metrics` 模块

---

## 模块概述


ErisPulse 指标监控管理器

提供计数器、仪表盘、直方图三种指标类型，支持标签维度
自动采集框架内置指标，可通过 /metrics 端点暴露

> **提示**
> 1. 使用 counter() / gauge() / histogram() 创建指标
> 2. 使用 @timed() 装饰器自动计时函数执行
> 3. 通过 get_all_metrics() 获取所有指标数据

---

## 类列表


### `class Counter`

计数器指标

> **提示**
> 只支持递增，适用于统计事件次数

**示例**:
```python
>>> c = sdk.metrics.counter("events.total", "事件总数")
>>> c.inc(tags={"type": "message"})
```


#### 方法列表


##### `__init__(name: str, description: str = '')`

初始化计数器

:param name: str 指标名称
:param description: str 指标描述

---


##### `_tags_key(tags: dict[str, str] | None)`

将标签转换为可哈希的键

> **内部方法**

---


##### `inc(value: int = 1, tags: dict[str, str] = None)`

增加计数

:param value: int 增加量 (默认: 1)
:param tags: dict 标签字典 (可选)

---


##### `get(tags: dict[str, str] = None)`

获取当前计数值

:param tags: dict 标签字典 (可选)
:return: int 计数值

---


##### `reset()`

重置计数器

---


##### `name()`

:return: str 指标名称

---


##### `to_dict()`

导出为字典

:return: dict 指标数据

---


### `class Gauge`

仪表盘指标

> **提示**
> 支持增减，适用于统计当前在线数量、温度等

**示例**:
```python
>>> g = sdk.metrics.gauge("bots.online", "在线Bot数量")
>>> g.inc()
>>> g.dec()
```


#### 方法列表


##### `__init__(name: str, description: str = '')`

初始化仪表盘

:param name: str 指标名称
:param description: str 指标描述

---


##### `set(value: float, tags: dict[str, str] = None)`

设置值

:param value: float 目标值
:param tags: dict 标签字典 (可选)

---


##### `inc(value: float = 1, tags: dict[str, str] = None)`

增加值

:param value: float 增加量 (默认: 1)
:param tags: dict 标签字典 (可选)

---


##### `dec(value: float = 1, tags: dict[str, str] = None)`

减少值

:param value: float 减少量 (默认: 1)
:param tags: dict 标签字典 (可选)

---


##### `get(tags: dict[str, str] = None)`

获取当前值

:param tags: dict 标签字典 (可选)
:return: float 当前值

---


##### `reset()`

重置仪表盘

---


##### `to_dict()`

导出为字典

:return: dict 指标数据

---


### `class Histogram`

直方图指标

> **提示**
> 适用于统计延迟分布、响应大小等
> 自动计算 P50/P95/P99 分位数

**示例**:
```python
>>> h = sdk.metrics.histogram("api.latency", "API延迟")
>>> h.observe(0.05, tags={"endpoint": "send"})
>>> h.get_summary()
```


#### 方法列表


##### `__init__(name: str, description: str = '', buckets: list[float] = None)`

初始化直方图

:param name: str 指标名称
:param description: str 指标描述
:param buckets: list[float] 分桶边界 (可选)

---


##### `observe(value: float, tags: dict[str, str] = None)`

记录一个观察值

:param value: float 观察值
:param tags: dict 标签字典 (可选)

---


##### `get_summary(tags: dict[str, str] = None)`

获取统计摘要

:param tags: dict 标签字典 (可选)
:return: dict 统计摘要, 包含 count/sum/avg/p50/p95/p99

**示例**:
```python
>>> h.get_summary()
{"count": 100, "sum": 5.0, "avg": 0.05, "p50": 0.03, "p95": 0.12, "p99": 0.25}
```

---


##### `reset()`

重置直方图

---


##### `to_dict()`

导出为字典

:return: dict 指标数据

---


### `class MetricsManager`

指标监控管理器

> **提示**
> 1. 使用 counter() / gauge() / histogram() 注册指标
> 2. 使用 @timed() 装饰器自动记录函数执行时间
> 3. 通过 get_all_metrics() 获取 JSON 格式的所有指标
> 4. 框架启动后自动注册内置指标

**示例**:
```python
>>> from ErisPulse import sdk
>>>
>>> c = sdk.metrics.counter("my_module.calls", "调用次数")
>>> c.inc()
>>>
>>> @sdk.metrics.timed("my_module.slow_operation")
... async def slow_operation():
...     await asyncio.sleep(1)
```


#### 方法列表


##### `counter(name: str, description: str = '')`

获取或创建计数器

:param name: str 指标名称
:param description: str 指标描述
:return: Counter 计数器实例

**示例**:
```python
>>> c = sdk.metrics.counter("events.total", "事件总数")
>>> c.inc(tags={"type": "message"})
```

---


##### `gauge(name: str, description: str = '')`

获取或创建仪表盘

:param name: str 指标名称
:param description: str 指标描述
:return: Gauge 仪表盘实例

**示例**:
```python
>>> g = sdk.metrics.gauge("bots.online", "在线Bot数量")
>>> g.inc()
```

---


##### `histogram(name: str, description: str = '', buckets: list[float] = None)`

获取或创建直方图

:param name: str 指标名称
:param description: str 指标描述
:param buckets: list[float] 分桶边界 (可选)
:return: Histogram 直方图实例

**示例**:
```python
>>> h = sdk.metrics.histogram("api.latency", "API延迟")
>>> h.observe(0.05)
```

---


##### `timed(name: str = None, tags: dict = None)`

计时装饰器

:param name: str 指标名称 (默认: "erispulse.operation.duration")
:param tags: dict 标签 (可选)
:return: Callable 装饰器

**示例**:
```python
>>> @sdk.metrics.timed("my_module.api_call", tags={"endpoint": "weather"})
... async def fetch_weather(city):
...     ...
```

---


##### `register_builtin_metrics()`

注册框架内置指标

> **内部方法**

---


##### `get_all_metrics()`

获取所有指标数据

:return: dict 所有指标的 JSON 数据

**示例**:
```python
>>> data = sdk.metrics.get_all_metrics()
```

---


##### `reset()`

重置所有指标

---

