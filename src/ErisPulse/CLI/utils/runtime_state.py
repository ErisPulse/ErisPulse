"""
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

{!--< internal-use >!--}
供 CLI run / stop / restart 命令使用；状态文件损坏时按不存在处理。
{!--< /internal-use >!--}
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# 状态文件位置（相对当前工作目录；epsdk run / stop / restart 须在同一项目下执行）
STATE_DIR = Path(".erispulse")
STATE_FILE = STATE_DIR / "runtime.json"

# 优雅停止的等待预算（秒）：SIGINT 后等待监督进程自行收尾，超时逐级升级
GRACEFUL_TIMEOUT_SECS = 8.0
FORCE_TIMEOUT_SECS = 3.0


def state_path() -> Path:
    """
    获取状态文件绝对路径（当前工作目录维度）

    :return: Path 状态文件路径
    """
    return Path.cwd() / STATE_DIR / STATE_FILE


def read() -> "dict | None":
    """
    读取运行实例状态

    :return: 状态字典 ``{"pid", "child_pid", "argv", "cwd", "started_at"}``；
             不存在或损坏时返回 None
    """
    path = state_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("pid"), int):
            return data
    except Exception:
        pass
    return None


def write(pid: int, argv: "list[str] | None" = None, child_pid: "int | None" = None) -> None:
    """
    写入/覆盖运行实例状态

    :param pid: 监督进程 PID（``epsdk run`` 自身；``--reload`` 内联模式为当前进程）
    :param argv: 启动命令（restart 按此重放）
    :param child_pid: 当前框架子进程 PID（无则省略）
    """
    try:
        state_path().parent.mkdir(parents=True, exist_ok=True)
        state_path().write_text(
            json.dumps(
                {
                    "pid": pid,
                    "child_pid": child_pid,
                    "argv": list(argv or sys.argv),
                    "cwd": str(Path.cwd()),
                    "started_at": time.time(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


def update_child(child_pid: int) -> None:
    """
    更新当前框架子进程 PID（监督进程每次拉起新子进程时调用）

    :param child_pid: 子进程 PID
    """
    data = read()
    if data is None:
        return
    data["child_pid"] = child_pid
    try:
        state_path().write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def clear() -> None:
    """清除状态文件（不存在时静默）"""
    try:
        state_path().unlink(missing_ok=True)
    except Exception:
        pass


def pid_alive(pid: int) -> bool:
    """
    判断进程是否存活

    :param pid: 进程 PID
    :return: 是否存活
    """
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return exit_code.value == STILL_ACTIVE
            return False
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def terminate(pid: int, force: bool = False) -> bool:
    """
    终止进程

    POSIX：默认 SIGINT（监督进程按 Ctrl+C 同款路径优雅收尾）；``force=True``
    直接 SIGKILL。Windows：无优雅语义，``os.kill`` 即 TerminateProcess。

    :param pid: 目标进程 PID
    :param force: 是否跳过优雅信号直接强制终止
    :return: 是否已发送终止信号
    """
    try:
        if os.name == "nt":
            os.kill(pid, signal.SIGTERM)
            return True
        if force:
            os.kill(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGINT)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def wait_gone(pid: int, timeout: float) -> bool:
    """
    等待进程退出

    :param pid: 进程 PID
    :param timeout: 最长等待秒数
    :return: 是否已在时限内退出
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not pid_alive(pid):
            return True
        time.sleep(0.15)
    return not pid_alive(pid)


def kill_tree_hard(pid: int) -> None:
    """
    强制终止进程（Windows 下连带其直接子进程的兜底清理）

    :param pid: 进程 PID
    """
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
            return
        except Exception:
            pass
    terminate(pid, force=True)
