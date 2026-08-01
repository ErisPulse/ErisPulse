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


### `get_rss_mb()`

获取当前进程的驻留集大小（RSS），单位 MB

优先使用 ``psutil``；若不可用则在 Linux 上读取 ``/proc/self/status``；
其余平台返回 ``None``。

**返回值** (`RSS（MB），不可用时为`): ``None``

---


### `get_traced_mb()`

获取 tracemalloc 当前追踪的 Python 分配内存，单位 MB

**返回值** (`已追踪内存（MB），未启用`): tracemalloc 时为 ``None``

---


### `snapshot(label: str = '')`

采集一次内存快照

- **label** (`快照标签，用于跨次快照计算同名标签的`): RSS 增量
**返回值** (`包含`): ``label`` / ``rss_mb`` / ``traced_mb`` / ``delta_mb`` 的字典；
         无法采集的项为 ``None``

---


### `log_snapshot(label: str = '')`

记录一次内存快照到 TRACE 级日志

延迟导入 logger/i18n 以避免循环引用。当日志级别高于 TRACE 时，快照不会输出，
但仍会更新内部基线，以保证下次有效调用时的增量正确。

- **label**: 快照标签

---

