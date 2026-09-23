"""
ErisPulse 主动 GC 周期任务

SDK 主动垃圾回收后台任务的实现：周期性 Python GC 与内部资源回收（离线 Bot 清理）、
框架配置读取与钳制、配置热更新即时重启联动、事件洪峰门控。
由 ``ErisPulse.SDK`` 的同名私有方法薄委托调用；SDK 上保留方法形态，
以便测试与子类按 ``patch.object(SDK, "_start_proactive_gc")`` 方式补丁。
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ..Core.constants import (
    DEFAULT_PROACTIVE_GC_FULL_EVERY,
    DEFAULT_PROACTIVE_GC_GEN0_MIN,
    DEFAULT_PROACTIVE_GC_GENERATION,
    DEFAULT_PROACTIVE_GC_IDLE_ONLY,
    DEFAULT_PROACTIVE_GC_INTERVAL_SECS,
    DEFAULT_PROACTIVE_GC_MEMORY_GROWTH_MB,
)
from ..Core.i18n import i18n

if TYPE_CHECKING:
    from ..sdk import SDK


def start_proactive_gc(sdk: SDK) -> None:
    """
    {!--< internal-use >!--}
    启动主动 GC 后台任务

    定期执行 Python GC 和内部资源回收（离线 Bot 清理等），
    防止长期运行时的内存增长。

    GC 行为由多项框架配置控制（均支持热更新，变更时即时重启任务）：

    - ``proactive_gc_interval``: 回收间隔秒数（0 禁用）
    - ``proactive_gc_generation``: 常规轮次回收分代（0/1/2，钳制到 0..2）
    - ``proactive_gc_full_every``: 每 N 轮做一次全量回收（0 禁用）
    - ``proactive_gc_memory_growth_mb``: 全量回收的内存增长门限（0 不设限）
    - ``proactive_gc_idle_only``: 事件洪峰时跳过 Python GC（避免停顿竞争）
    - ``proactive_gc_gen0_min``: gen0 垃圾量下限，低于则跳过回收（空转轮次零开销）

    初始化阶段已调用 ``gc.freeze()`` 将框架对象移入永久代，
    此处 ``gc.collect()`` 仅扫描运行期新建对象。
    """
    # 停止已有的 GC 任务（含反注册配置钩子）
    sdk._stop_proactive_gc()

    # 注册配置变更钩子：proactive_gc_* 变化时即时重启任务。
    # 修复旧实现"interval 切到 0 后无法再启用"的问题。
    try:
        sdk.lifecycle.register("config.set", sdk._on_gc_config_event)
        sdk.lifecycle.register("config.updated", sdk._on_gc_config_event)
    except Exception:
        pass

    sdk._gc_config_snapshot = sdk._read_gc_config()
    if sdk._gc_config_snapshot[0] <= 0:
        return  # 配置禁用

    async def _gc_loop():
        import gc

        round_count = 0
        memory_baseline: float | None = None
        while True:
            try:
                # 每轮重新读取配置，支持热更新；常规变更已由配置钩子即时重启任务
                cfg = sdk._read_gc_config()
                interval = cfg[0]
                if interval <= 0:
                    # 配置运行时禁用了 GC，停止循环
                    break
                await asyncio.sleep(interval)
                round_count += 1

                # 1. 内部资源回收（廉价，始终执行）
                evicted = 0
                try:
                    evicted = sdk.adapter._evict_offline_bots()
                except Exception:
                    pass

                # 2. 空闲门控：事件洪峰时跳过 Python GC，避免停顿与消息处理竞争
                if cfg[4] and sdk._has_handler_backlog():
                    sdk.logger.trace(
                        i18n.t("core.sdk.gc.skipped", reason="busy")
                    )
                    if evicted > 0:
                        sdk.logger.trace(
                            i18n.t(
                                "core.sdk.gc.collected", collected=0, evicted=evicted
                            )
                        )
                    continue

                # 3. 垃圾量门控：gen0 无足够垃圾时跳过回收（空转轮次近乎零开销）
                if gc.get_count()[0] < cfg[5]:
                    if evicted > 0:
                        sdk.logger.trace(
                            i18n.t(
                                "core.sdk.gc.collected", collected=0, evicted=evicted
                            )
                        )
                    continue

                # 4. 周期性全量（受内存增长门限约束）或常规分代回收
                is_full = cfg[2] > 0 and round_count % cfg[2] == 0
                if is_full:
                    collected, memory_baseline = sdk._run_full_gc_collection(
                        gc, memory_baseline, cfg[3]
                    )
                else:
                    collected = gc.collect(cfg[1])

                if collected > 0 or evicted > 0:
                    sdk.logger.trace(
                        i18n.t(
                            "core.sdk.gc.collected",
                            collected=collected,
                            evicted=evicted,
                        )
                    )
                # 5. 内存快照（TRACE），便于长期观察内存变化趋势
                try:
                    from .memory import log_snapshot

                    log_snapshot("gc")
                except Exception:
                    pass
            except asyncio.CancelledError:
                break
            except Exception:
                # GC 异常不应中断循环
                continue

    try:
        sdk._gc_task = asyncio.create_task(_gc_loop())
    except RuntimeError:
        pass

def stop_proactive_gc(sdk: SDK) -> None:
    """
    {!--< internal-use >!--}
    停止主动 GC 后台任务，并反注册配置变更钩子
    """
    try:
        sdk.lifecycle.unregister("config.set", sdk._on_gc_config_event)
        sdk.lifecycle.unregister("config.updated", sdk._on_gc_config_event)
    except Exception:
        pass
    sdk._gc_config_snapshot = None
    if sdk._gc_task is not None and not sdk._gc_task.done():
        sdk._gc_task.cancel()
    sdk._gc_task = None

def read_gc_config() -> tuple[float, int, int, int, bool, int]:
    """
    {!--< internal-use >!--}
    读取并钳制主动 GC 相关框架配置

    :return: ``(interval, generation, full_every, growth_mb, idle_only, gen0_min)``
             元组，值均已钳制到合法范围；``interval`` 为秒（支持小数）
    """
    interval = DEFAULT_PROACTIVE_GC_INTERVAL_SECS
    generation = DEFAULT_PROACTIVE_GC_GENERATION
    full_every = DEFAULT_PROACTIVE_GC_FULL_EVERY
    growth_mb = DEFAULT_PROACTIVE_GC_MEMORY_GROWTH_MB
    idle_only = DEFAULT_PROACTIVE_GC_IDLE_ONLY
    gen0_min = DEFAULT_PROACTIVE_GC_GEN0_MIN
    try:
        from . import get_framework_config

        fw = get_framework_config()
        raw_interval = fw.get("proactive_gc_interval", interval)
        interval = float(raw_interval) if raw_interval is not None else interval
        generation = int(fw.get("proactive_gc_generation", generation))
        full_every = int(fw.get("proactive_gc_full_every", full_every))
        growth_mb = int(fw.get("proactive_gc_memory_growth_mb", growth_mb))
        idle_only = bool(fw.get("proactive_gc_idle_only", idle_only))
        gen0_min = int(fw.get("proactive_gc_gen0_min", gen0_min))
    except Exception:
        pass
    return (
        max(0.0, float(interval)),
        max(0, min(2, generation)),
        max(0, full_every),
        max(0, growth_mb),
        idle_only,
        max(0, gen0_min),
    )

def on_gc_config_event(sdk: SDK, _data: dict) -> None:
    """
    {!--< internal-use >!--}
    ``config.set`` / ``config.updated`` 回调：proactive_gc_* 配置变化时重启 GC 任务

    相比旧实现"每轮重读"，此钩子使配置变更（含 0→N 重新启用）即时生效。
    从后台线程（如 config watcher）触发时，调度回主事件循环再重启。
    """
    try:
        current = sdk._read_gc_config()
        if (
            sdk._gc_config_snapshot is None
            or current == sdk._gc_config_snapshot
        ):
            return
    except Exception:
        return

    def _restart() -> None:
        try:
            sdk._start_proactive_gc()
        except Exception:
            pass

    try:
        # 当前线程有运行中的事件循环：直接重启
        asyncio.get_running_loop()
        _restart()
    except RuntimeError:
        # 非事件循环线程（如 config watcher）：调度回主循环执行
        from .tasks import _get_main_loop

        main_loop = _get_main_loop()
        if main_loop is not None and main_loop.is_running():
            main_loop.call_soon_threadsafe(_restart)
        else:
            # 无可用主循环：跳过本次重启，循环自身每轮重读配置兜底
            pass

def has_handler_backlog() -> bool:
    """
    {!--< internal-use >!--}
    事件处理器洪峰检测

    :return: 存在未完成的 pending handler task 时返回 True
    """
    try:
        from ..Core.adapter import adapter as _adapter

        return len(getattr(_adapter, "_pending_handler_tasks", ())) > 0
    except Exception:
        return False

def run_full_gc_collection(
    gc_module: Any, baseline: float | None, growth_mb: int
) -> tuple[int, float | None]:
    """
    {!--< internal-use >!--}
    执行一次全量回收（受内存增长门限约束）

    优先使用 tracemalloc 追踪值，不可用则回退 RSS。当 ``growth_mb > 0``
    且距上次全量回收基线增长不足时跳过回收，避免内存稳定时空转。

    :param gc_module: ``gc`` 模块（便于测试注入）
    :param baseline: 上次全量回收后的内存基线（MB），None 表示首次
    :param growth_mb: 内存增长门限（MB），0 表示不设门限
    :return: ``(collected, 新基线)``
    """
    current: float | None = None
    try:
        from .memory import get_rss_mb, get_traced_mb

        current = get_traced_mb()
        if current is None:
            current = get_rss_mb()
    except Exception:
        pass

    if current is not None:
        if growth_mb > 0 and baseline is not None:
            # 内存稳定：增长未达门限，跳过本次全量回收
            if (current - baseline) < growth_mb:
                return 0, baseline
        baseline = current

    try:
        collected = gc_module.collect()
    except Exception:
        collected = 0
    return collected, baseline
