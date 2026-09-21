"""
事件处理器节流（throttle=，EPRFC-2026-001 方向八）

同一键（用户 / 会话 / 全局）上的事件在最小间隔内只放行一条，其余静默
丢弃——手写防刷屏逻辑的声明式替代。实现为既有处理器条件机制上的框架
包装器：装饰器注册期生成一个条件函数，与其它条件（detail_type /
pattern / regex）组合。

{!--< tips >!--}
1. 时长语法与命令 ``cooldown=`` / ``args=`` duration 一致（``2s`` / ``1h30m``）
2. 节流状态存放于条件闭包内，处理器注销后随闭包被 GC 自动回收
3. 命中丢弃仅输出 TRACE 日志（对称于作用域静默）
{!--< /tips >!--}
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ..constants import GOVERNANCE_KEY_KINDS
from ..i18n import i18n
from .command_args import parse_duration

# 节流键粒度（与命令冷却 / 限流共用一份白名单）
_KEY_KINDS = GOVERNANCE_KEY_KINDS


def _scope_key(kind: str, event: Any) -> str:
    """
    计算节流作用域键（复用 ``platform:bot:目标`` 会话键体系）

    :param kind: 粒度（user / session / global，装饰期已校验）
    :param event: 事件数据（Event 包装或原始 dict 均可）
    :return: 作用域键字符串
    """
    if kind == "global":
        return "global"
    from ..scope import scope

    platform = event.get("platform", "")
    self_info = event.get("self") or {}
    bot_id = self_info.get("account_id") or self_info.get("user_id") or ""
    if kind == "session":
        target = scope.session_id_from_event(event) or ""
        return f"{platform}:{bot_id}:{target}"
    return f"{platform}:{bot_id}:{event.get('user_id', '')}"


def make_throttle_condition(
    throttle: str,
    throttle_key: str = "user",
    handler_name: str = "",
) -> Callable[[Any], bool]:
    """
    构造节流条件函数（处理器条件机制的包装器）

    :param throttle: 节流间隔声明（如 ``"2s"`` / ``"1h30m"``，与 duration 语法一致）
    :param throttle_key: 键粒度：``user``（默认）/ ``session`` / ``global``
    :param handler_name: 处理器名（TRACE 日志展示用）
    :return: 条件函数——间隔已过返回 True（放行并刷新时间戳），
        间隔内返回 False（处理器被跳过，事件静默丢弃）
    :raises ValueError: 声明非法（时长语法 / 粒度白名单）时装饰期抛出
    """
    try:
        interval = parse_duration(throttle)
    except ValueError as e:
        raise ValueError(i18n.t("core.event.throttle.invalid", error=e)) from e
    if throttle_key not in _KEY_KINDS:
        raise ValueError(
            i18n.t(
                "core.event.throttle.invalid_key",
                key=throttle_key,
                kinds=", ".join(sorted(_KEY_KINDS)),
            )
        )

    # 节流状态随条件闭包存活：处理器注销（闭包无引用）后由 GC 回收
    _last_pass: dict[str, float] = {}

    from .. import logger

    def condition(event: Any) -> bool:
        key = _scope_key(throttle_key, event)
        now = time.monotonic()
        last = _last_pass.get(key)
        if last is not None and now - last < interval:
            logger.trace(
                i18n.t(
                    "core.event.throttle.dropped",
                    handler=handler_name or "handler",
                    key=key,
                    remain=f"{interval - (now - last):.1f}",
                )
            )
            return False
        _last_pass[key] = now
        return True

    return condition
