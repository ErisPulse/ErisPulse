# `ErisPulse.runtime.metrics` 模块

---

## 模块概述


进程内指标计数器（轻量注册表）

为 ``/health`` 与 ``/metrics`` 提供事件量等运行计数。单进程内存态：
不落盘、不跨进程、无锁（计数写入仅发生在事件循环线程）。

> **提示**
> 1. 热路径成本为 dict 一次哈希查找 + 整数自增，可安全用于分发入口
> 2. 计数器名建议点分分层（``events.total`` / ``events.type.message``），
> ``snapshot()`` 原样返回；``/metrics`` 输出时做 Prometheus 名称净化
> 3. 实例身份与进程存活时长同源于本模块（``instance_id`` / ``uptime_seconds``）

---

## 类列表


### `class MetricsRegistry`

计数器注册表（模块级单例 ``metrics``）


#### 方法列表


##### `inc(name: str, amount: int = 1) -> None`

计数器自增（计数只增不减）

- **name**: 计数器名（建议点分分层）
- **amount**: 自增量（正整数）

---


##### `snapshot() -> dict[str, int]`

全量计数器快照

**返回值** (`dict`): 计数器名 → 当前值的副本

---


##### `instance_id -> str`（property）

实例身份（环境变量 ERISPULSE_INSTANCE_ID 覆盖优先）

---


##### `uptime_seconds -> float`（property）

进程运行时长（秒，基于 monotonic 时钟）

---


##### `render_prometheus(prefix: str = 'erispulse') -> str`

渲染 Prometheus 文本格式输出

计数器名的非 ``[a-zA-Z0-9_]`` 字符替换为下划线；每个计数器输出一行
``{prefix}_{净化名} {值}``（带 instance 标签），并附带 uptime gauge。

- **prefix**: 指标名前缀

**返回值** (`str`): 文本格式内容（不带结尾换行）

---

