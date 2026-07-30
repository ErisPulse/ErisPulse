"""
进程内存追踪工具

提供进程内存占用的快照采集与 TRACE 级日志记录，便于排查内存增长。

{!--< tips >!--}
1. 在生命周期关键点（初始化、模块加载、服务器启动）调用 ``log_snapshot()`` 即可在 TRACE 日志中观察内存变化
2. RSS 采集优先使用 psutil（若已安装），否则回退到 ``/proc/self/status``（Linux）或仅报告 tracemalloc 追踪值
3. ``snapshot()`` 会按 ``label`` 记录上一次 RSS，从而在下次同标签快照中计算增量 ``delta_mb``
{!--< /tips >!--}
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "get_rss_mb",
    "get_traced_mb",
    "log_snapshot",
    "snapshot",
]

# 各 label 上一次快照的 RSS（MB），用于计算增量
_prev_rss: dict[str, float] = {}


def get_rss_mb() -> float | None:
    """获取当前进程的驻留集大小（RSS），单位 MB

    优先使用 ``psutil``；若不可用则在 Linux 上读取 ``/proc/self/status``；
    其余平台返回 ``None``。

    :return: RSS（MB），不可用时为 ``None``
    """
    try:
        import psutil

        return psutil.Process().memory_info().rss / 1024 / 1024
    except Exception:
        pass

    try:
        from pathlib import Path

        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024
    except Exception:
        pass

    return None


def get_traced_mb() -> float | None:
    """获取 tracemalloc 当前追踪的 Python 分配内存，单位 MB

    :return: 已追踪内存（MB），未启用 tracemalloc 时为 ``None``
    """
    try:
        import tracemalloc

        if tracemalloc.is_tracing():
            current, _peak = tracemalloc.get_traced_memory()
            return current / 1024 / 1024
    except Exception:
        pass

    return None


def snapshot(label: str = "") -> dict[str, Any]:
    """采集一次内存快照

    :param label: 快照标签，用于跨次快照计算同名标签的 RSS 增量
    :return: 包含 ``label`` / ``rss_mb`` / ``traced_mb`` / ``delta_mb`` 的字典；
             无法采集的项为 ``None``
    """
    rss = get_rss_mb()
    traced = get_traced_mb()

    delta: float | None = None
    key = label or "__default__"
    if rss is not None and key in _prev_rss:
        delta = rss - _prev_rss[key]
    if rss is not None:
        _prev_rss[key] = rss

    return {
        "label": label,
        "rss_mb": round(rss, 1) if rss is not None else None,
        "traced_mb": round(traced, 1) if traced is not None else None,
        "delta_mb": round(delta, 1) if delta is not None else None,
    }


def log_snapshot(label: str = "") -> None:
    """记录一次内存快照到 TRACE 级日志

    延迟导入 logger/i18n 以避免循环引用。当日志级别高于 TRACE 时，快照不会输出，
    但仍会更新内部基线，以保证下次有效调用时的增量正确。

    :param label: 快照标签
    """
    snap = snapshot(label)
    from ..Core.i18n import i18n
    from ..Core.logger import logger

    rss_s = f"{snap['rss_mb']}MB" if snap["rss_mb"] is not None else "N/A"
    traced_s = f"{snap['traced_mb']}MB" if snap["traced_mb"] is not None else "N/A"
    delta_s = f"Δ{snap['delta_mb']:+.1f}MB" if snap["delta_mb"] is not None else ""

    logger.trace(
        i18n.t(
            "core.memory.snapshot",
            label=snap["label"] or "snapshot",
            rss=rss_s,
            traced=traced_s,
            delta=delta_s,
        )
    )
