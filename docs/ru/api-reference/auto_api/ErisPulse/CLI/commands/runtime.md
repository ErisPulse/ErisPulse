# `ErisPulse.CLI.commands.runtime` 模块

---

## 模块概述


Stop / Restart 命令实现

控制由 ``epsdk run`` 启动的运行实例：``.erispulse/runtime.json`` 状态文件
记录监督进程 PID、当前子进程 PID 与原始启动命令，``stop`` 优雅终止实例，
``restart`` 停止后按原参数重新启动。

POSIX 停止走 SIGINT（监督进程按 Ctrl+C 同款路径收尾，finally 链终止子进程），
超时逐级升级 SIGTERM / SIGKILL；Windows 无优雅信号语义，先断子进程再终止
监督进程（避免监督者把强杀误判为崩溃重新拉起）。

---

## 函数列表


### `_stop_instance(state: dict, force: bool = False) -> bool`

停止一个运行实例（子进程先断，监督进程优雅收尾后逐级升级）

- **state**: 状态字典（pid / child_pid）
- **force**: 跳过优雅信号直接强制终止

**返回值**: 是否成功停止

---


### `os_needs_force() -> bool`

Windows 无优雅信号语义：子进程直接强停

---


## 类列表


### `class StopCommand(Command)`

stop 命令

停止正在运行的 ErisPulse 实例（由 ``epsdk run`` 启动）


### `class RestartCommand(Command)`

restart 命令

重启正在运行的 ErisPulse 实例（停止后按原参数重新启动，前台接管控制台）

