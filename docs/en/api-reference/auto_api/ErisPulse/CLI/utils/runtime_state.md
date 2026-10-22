# `ErisPulse.CLI.utils.runtime_state` 模块

---

## 模块概述


运行实例状态文件（pidfile）工具

``epsdk run`` 启动时把监督进程 PID、当前子进程 PID 与原始 argv 写入
``.erispulse/runtime.json``（工作目录维度，多项目互不干扰）；
``epsdk stop`` / ``epsdk restart`` 据此定位并控制运行中的实例。

跨平台语义：
- POSIX：优先 SIGINT（监督进程按 Ctrl+C 同款路径优雅收尾——finally 链
  终止子进程），超时升级 SIGTERM → SIGKILL
- Windows：无进程信号语义，``os.kill(pid, SIGTERM)`` 即 TerminateProcess
  （强制终止）；stop 命令先断子进程再停监督进程，避免监督者把强杀误判
  为崩溃而重新拉起

**内部方法**
供 CLI run / stop / restart 命令使用；状态文件损坏时按不存在处理。

---

## 函数列表


### `state_path() -> Path`

获取状态文件绝对路径（当前工作目录维度）

**返回值** (`Path`): 状态文件路径

---


### `read() -> 'dict | None'`

读取运行实例状态

**返回值**: 状态字典 ``{"pid", "child_pid", "argv", "cwd", "started_at"}``；

         不存在或损坏时返回 None

---


### `write(pid: int, argv: 'list[str] | None' = None, child_pid: 'int | None' = None) -> None`

写入/覆盖运行实例状态

- **pid**: 监督进程 PID（``epsdk run`` 自身；``--reload`` 内联模式为当前进程）
- **argv**: 启动命令（restart 按此重放）
- **child_pid**: 当前框架子进程 PID（无则省略）

---


### `update_child(child_pid: int) -> None`

更新当前框架子进程 PID（监督进程每次拉起新子进程时调用）

- **child_pid**: 子进程 PID

---


### `clear() -> None`

清除状态文件（不存在时静默）

---


### `pid_alive(pid: int) -> bool`

判断进程是否存活

- **pid**: 进程 PID

**返回值**: 是否存活

---


### `terminate(pid: int, force: bool = False) -> bool`

终止进程

POSIX：默认 SIGINT（监督进程按 Ctrl+C 同款路径优雅收尾）；``force=True``
直接 SIGKILL。Windows：无优雅语义，``os.kill`` 即 TerminateProcess。

- **pid**: 目标进程 PID
- **force**: 是否跳过优雅信号直接强制终止

**返回值**: 是否已发送终止信号

---


### `wait_gone(pid: int, timeout: float) -> bool`

等待进程退出

- **pid**: 进程 PID
- **timeout**: 最长等待秒数

**返回值**: 是否已在时限内退出

---


### `kill_tree_hard(pid: int) -> None`

强制终止进程（Windows 下连带其直接子进程的兜底清理）

- **pid**: 进程 PID

---

