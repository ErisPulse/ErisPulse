"""
分发决策链追踪（EPRFC-2026-001 方向五：模块排查的场景三）

把一条消息在分发链上的每个判定点（命令文本判定、命令命中、作用域 / ACL /
主人 / 权限检查、冷却、参数解析、执行结果、中间件否决）记录为一条因果链，
供测试工具（ErisPulse-Testing）与排查场景给出"命令为什么没触发"的结论。

{!--< tips >!--}
1. 默认零开销：未处于采集上下文时 trace_step() 直接返回
2. ``with start_dispatch_trace() as trace:`` 采集一次分发的全部决策点
3. 记录为机器可读的 dict（stage / verdict / message_key / params），
   展示层经 format_dispatch_trace() 以当前语言渲染
{!--< /tips >!--}
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_trace_records: ContextVar[list[dict[str, Any]] | None] = ContextVar(
    "erispulse_dispatch_trace", default=None
)


@contextmanager
def start_dispatch_trace() -> Iterator[list[dict[str, Any]]]:
    """
    开启一次分发决策链采集

    采集列表经 ContextVar 传播到本次分发派生的全部处理器 Task
    （ContextVar 在 Task 创建时复制），with 退出后恢复原状。

    :yields: 记录列表（采集期间持续追加，可在外部直接读取）
    """
    records: list[dict[str, Any]] = []
    token = _trace_records.set(records)
    try:
        yield records
    finally:
        _trace_records.reset(token)


def get_dispatch_trace() -> list[dict[str, Any]]:
    """
    读取当前采集上下文中的记录（不在采集上下文时返回空列表）

    :return: 决策记录列表
    """
    return list(_trace_records.get() or [])


def trace_step(
    stage: str,
    verdict: str,
    message_key: str | None = None,
    **details: Any,
) -> None:
    """
    记录一个判定点（未处于采集上下文时零开销直接返回）

    :param stage: 判定阶段标识（如 ``command_match`` / ``permission`` / ``cooldown``）
    :param verdict: 判定结论（``ok`` / ``rejected`` / ``dropped`` / ``failed`` / ``passed``）
    :param message_key: 该判定的本地化说明键（i18n，可空）
    :param details: 判定上下文参数（命令名、原因、耗时等）
    """
    records = _trace_records.get()
    if records is None:
        return
    records.append(
        {
            "stage": stage,
            "verdict": verdict,
            "message_key": message_key,
            "params": details,
        }
    )


def format_dispatch_trace(records: list[dict[str, Any]]) -> str:
    """
    将决策记录渲染为人类可读的因果链文本（当前语言）

    :param records: 决策记录列表
    :return: 逐行文本；无记录时返回提示文案
    """
    from ..i18n import i18n

    if not records:
        return i18n.t("core.trace.empty")
    lines: list[str] = []
    for record in records:
        key = record.get("message_key")
        params = record.get("params") or {}
        if key:
            try:
                text = i18n.t(key, **params)
            except Exception:
                text = i18n.t(key)
        else:
            text = f"{record.get('stage')} -> {record.get('verdict')}"
        marker = "✓" if record.get("verdict") == "ok" else ("✗" if record.get("verdict") in ("rejected", "failed", "dropped") else "·")
        lines.append(f"{marker} {text}")
    return "\n".join(lines)


def final_verdict(records: list[dict[str, Any]]) -> str:
    """
    从决策记录推断最终结论

    :param records: 决策记录列表
    :return: ``executed``（已执行）/ ``rejected``（被权限类判定拒绝）/
        ``dropped``（被冷却等静默丢弃）/ ``failed``（执行出错）/
        ``no_match``（带前缀但未命中任何命令）/ ``passed``（非命令文本，
        放行给消息处理器）/ ``unknown``（无记录）
    """
    if not records:
        return "unknown"
    verdicts = [r.get("verdict") for r in records]
    if "failed" in verdicts:
        return "failed"
    if "executed" in verdicts:
        return "executed"
    if "rejected" in verdicts:
        return "rejected"
    if "dropped" in verdicts:
        return "dropped"
    if any(r.get("stage") == "command_match" and r.get("verdict") == "missed" for r in records):
        return "no_match"
    if any(r.get("stage") == "dispatch" and r.get("verdict") == "passed" for r in records):
        return "passed"
    return "unknown"
