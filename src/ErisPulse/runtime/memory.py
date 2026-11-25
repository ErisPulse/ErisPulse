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

from collections import OrderedDict
from typing import Any

from ..Core.constants import MEMORY_SNAPSHOT_LABELS_MAX

__all__ = [
    "ensure_tracing",
    "get_rss_mb",
    "get_traced_mb",
    "log_snapshot",
    "snapshot",
]

# 快照标签的最大缓存数。防止使用动态 label 调用 snapshot() 时
# _prev_rss 无限增长，超出部分按最早写入顺序淘汰。


# 各 label 上一次快照的 RSS（MB），用于计算增量。按写入顺序淘汰。
_prev_rss: OrderedDict[str, float] = OrderedDict()

# tracemalloc 惰性启用标记（进程级一次性）
_tracing_started = False


def ensure_tracing() -> None:
    """按配置惰性启用 tracemalloc（幂等，进程内只启动一次）

    读取 ``ErisPulse.framework.memory_tracing``（默认关闭）：开启后
    ``traced_mb`` 有值、proactive_gc 的增长门限不再误用 RSS，且
    ``snapshot(detail=True)`` 可输出 top 分配点。追踪带来约 2 倍分配
    路径 CPU 开销——排障时开启，常态关闭。开关支持热更新：重启追踪
    需重启进程（tracemalloc 不支持安全重置帧数）。
    """
    global _tracing_started
    if _tracing_started:
        return
    try:
        from ..Core.config import parse_bool_config
        from .frame_config import get_framework_config

        enabled = parse_bool_config(
            get_framework_config().get("memory_tracing", False)
        )
        if not enabled:
            _tracing_started = True  # 明确关闭：不再重试
            return
        import tracemalloc

        if not tracemalloc.is_tracing():
            tracemalloc.start(25)
        _tracing_started = True
    except Exception:
        _tracing_started = True  # 判定失败不反复重试（按关闭处理）


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


def snapshot(label: str = "", *, detail: bool = False) -> dict[str, Any]:
    """采集一次内存快照

    :param label: 快照标签，用于跨次快照计算同名标签的 RSS 增量
    :param detail: 是否附归因明细——框架内部各累积容器的长度（近零成本）
        与 tracemalloc top 分配点（需已开启 ``memory_tracing``）
    :return: 包含 ``label`` / ``rss_mb`` / ``traced_mb`` / ``delta_mb`` 的字典；
             无法采集的项为 ``None``。``detail=True`` 时附 ``containers`` 与
             ``top_allocations``
    """
    rss = get_rss_mb()
    traced = get_traced_mb()

    delta: float | None = None
    key = label or "__default__"
    if rss is not None:
        if key in _prev_rss:
            delta = rss - _prev_rss[key]
        # 记录并限制缓存上限，避免动态标签导致无界增长
        _prev_rss[key] = rss
        _prev_rss.move_to_end(key)
        while len(_prev_rss) > MEMORY_SNAPSHOT_LABELS_MAX:
            _prev_rss.popitem(last=False)

    result: dict[str, Any] = {
        "label": label,
        "rss_mb": round(rss, 1) if rss is not None else None,
        "traced_mb": round(traced, 1) if traced is not None else None,
        "delta_mb": round(delta, 1) if delta is not None else None,
    }
    if detail:
        result["containers"] = _container_counts()
        result["top_allocations"] = _top_allocations()
    return result


def _trace_probe_failure(lens: str, error: BaseException) -> None:
    """{!--< internal-use >!--} 容器归因探测失败留痕（惰性取 logger：runtime 层不顶层依赖 Core.logger）"""
    from ..Core.logger import logger

    logger.trace(f"memory.container_counts: {lens} probe failed: {error!r}")


def _container_counts() -> dict[str, int]:
    """{!--< internal-use >!--} 框架内部累积容器的长度归因（近零成本的 len 读取）"""
    counts: dict[str, int] = {}
    try:
        from ..Core.Event.interaction import interaction

        interaction_counts = interaction.counts()
        counts.update({f"interaction.{k}": v for k, v in interaction_counts.items()})
    except Exception as e:
        _trace_probe_failure("interaction", e)
    try:
        from ..Core.adapter import adapter

        counts["adapter.seen_event_ids"] = len(adapter._seen_event_ids)
        counts["adapter.cross_receipts"] = len(adapter._cross_receipts)
        counts["adapter.bots"] = len(adapter._bots)
        counts["adapter.pending_handler_tasks"] = len(adapter._pending_handler_tasks)
    except Exception as e:
        _trace_probe_failure("adapter", e)
    try:
        from .tasks import _owner_tasks, _owner_threads, _owner_timers

        counts["tasks.owner_tasks"] = sum(len(v) for v in _owner_tasks.values())
        counts["tasks.owner_timers"] = sum(len(v) for v in _owner_timers.values())
        counts["tasks.owner_threads"] = sum(len(v) for v in _owner_threads.values())
    except Exception as e:
        _trace_probe_failure("tasks", e)
    try:
        from ..Core.transcript import transcript

        counts["transcript.buffer"] = len(transcript._buffer)
    except Exception as e:
        _trace_probe_failure("transcript", e)
    return counts


def _top_allocations(limit: int | None = None) -> list[dict[str, Any]]:
    """{!--< internal-use >!--} tracemalloc top 分配点（未开启追踪时返回空列表）"""
    try:
        import tracemalloc

        if not tracemalloc.is_tracing():
            return []
        from ..Core.constants import MEMORY_SNAPSHOT_TOP_SITES

        top_n = limit if limit is not None else MEMORY_SNAPSHOT_TOP_SITES
        snapshot = tracemalloc.take_snapshot()
        stats = snapshot.statistics("lineno")[:top_n]
        return [
            {
                "where": f"{stat.traceback.format()[0]}",
                "size_mb": round(stat.size / 1024 / 1024, 2),
                "count": stat.count,
            }
            for stat in stats
        ]
    except Exception:
        return []


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
