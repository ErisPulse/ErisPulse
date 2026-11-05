# `ErisPulse.runtime.process_state` 模块

---

## 模块概述


跨进程运行状态契约（SDK 侧）

SDK 侧对 ``.erispulse/runtime.json`` 的最小写入面：硬重启退出前写入
观测标记（原因 / PID / 时间），供监督者（CLI run 命令）在重拉新进程时
向用户展示「为什么硬重启」。

> **提示**
> 1. **stdlib-only**：本模块禁止 import ErisPulse 任何其它模块——CLI 侧
> （CLI/utils/runtime_state.py）以独立实现消费同一 JSON 契约，依赖
> 方向为「SDK 不感知 CLI、CLI 不加载 SDK」
> 2. 路径与字段名是跨进程契约，由 tests 的 TestCrossProcessContracts 钉死
> （与 HARD_RESTART_EXIT_CODE 镜像同模式）

---

## 函数列表


### `_state_path() -> Path`

**内部方法** 运行状态文件路径

---


### `read() -> 'dict[str, Any] | None'`

读取运行状态文件

**返回值**: 状态字典；文件不存在或损坏时返回 None

---


### `_write(data: 'dict[str, Any]') -> None`

**内部方法** 原子写入运行状态文件（best-effort）

---


### `mark_hard_restart(reason: str, pid: int | None = None) -> None`

写入硬重启观测标记（hard_restart 退出前调用，best-effort 不抛异常）

在既有状态文件上附加 ``hard_restart_reason`` / ``hard_restart_at`` /
``hard_restart_pid`` 三个可选字段；监督者读取展示后经
:func:`clear_mark` 清除。

- **reason**: 硬重启原因（空串也写入——「未指定」本身是信息）
- **pid**: 请求硬重启的进程 PID（默认当前进程）

---


### `clear_mark() -> None`

清除硬重启标记（标记只应消费一次；best-effort 不抛异常）

---

