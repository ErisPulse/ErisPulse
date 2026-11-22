# `ErisPulse.runtime.memory` 模块

---

## 模块概述


进程内存追踪工具

提供进程内存占用的快照采集与 TRACE 级日志记录，便于排查内存增长。

> **提示**
> 1. 在生命周期关键点（初始化、模块加载、服务器启动）调用 ``log_snapshot()`` 即可在 TRACE 日志中观察内存变化
> 2. RSS 采集优先使用 psutil（若已安装），否则回退到 ``/proc/self/status``（Linux）或仅报告 tracemalloc 追踪值
> 3. ``snapshot()`` 会按 ``label`` 记录上一次 RSS，从而在下次同标签快照中计算增量 ``delta_mb``

---

## 函数列表


### `ensure_tracing() -> None`

按配置惰性启用 tracemalloc（幂等，进程内只启动一次）

读取 ``ErisPulse.framework.memory_tracing``（默认关闭）：开启后
``traced_mb`` 有值、proactive_gc 的增长门限不再误用 RSS，且
``snapshot(detail=True)`` 可输出 top 分配点。追踪带来约 2 倍分配
路径 CPU 开销——排障时开启，常态关闭。开关支持热更新：重启追踪
需重启进程（tracemalloc 不支持安全重置帧数）。

---


### `get_rss_mb() -> float | None`

获取当前进程的驻留集大小（RSS），单位 MB

优先使用 ``psutil``；若不可用则在 Linux 上读取 ``/proc/self/status``；
其余平台返回 ``None``。

**返回值**: RSS（MB），不可用时为 ``None``

---


### `get_traced_mb() -> float | None`

获取 tracemalloc 当前追踪的 Python 分配内存，单位 MB

**返回值**: 已追踪内存（MB），未启用 tracemalloc 时为 ``None``

---


### `snapshot(label: str = '', *, detail: bool = False) -> dict[str, Any]`

采集一次内存快照

- **label**: 快照标签，用于跨次快照计算同名标签的 RSS 增量
- **detail**: 是否附归因明细——框架内部各累积容器的长度（近零成本）

    与 tracemalloc top 分配点（需已开启 ``memory_tracing``）
**返回值**: 包含 ``label`` / ``rss_mb`` / ``traced_mb`` / ``delta_mb`` 的字典；

         无法采集的项为 ``None``。``detail=True`` 时附 ``containers`` 与
         ``top_allocations``

---


### `_container_counts() -> dict[str, int]`

**内部方法** 框架内部累积容器的长度归因（近零成本的 len 读取）

---


### `_top_allocations(limit: int | None = None) -> list[dict[str, Any]]`

**内部方法** tracemalloc top 分配点（未开启追踪时返回空列表）

---


### `log_snapshot(label: str = '') -> None`

记录一次内存快照到 TRACE 级日志

延迟导入 logger/i18n 以避免循环引用。当日志级别高于 TRACE 时，快照不会输出，
但仍会更新内部基线，以保证下次有效调用时的增量正确。

- **label**: 快照标签

---

