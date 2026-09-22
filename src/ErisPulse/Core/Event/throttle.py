"""
事件处理器节流（throttle=）与防抖（debounce=，EPRFC-2026-001 方向八）

同一键（用户 / 会话 / 全局）上的事件在最小间隔内只放行一条，其余静默
丢弃（throttle）；或窗口内只执行最后一条、取消前序（debounce）——手写
防刷屏 / 防抖逻辑的声明式替代。

{!--< tips >!--}
1. throttle 实现为处理器条件机制上的框架包装器（条件函数与 detail_type /
   pattern / regex 组合）；debounce 实现为处理器调用包装器（窗口内新事件
   取消前序的待执行任务）
2. 时长语法与命令 ``cooldown=`` / ``args=`` duration 一致（``2s`` / ``1h30m``）
3. throttle 状态存放于条件闭包内，处理器注销后随闭包被 GC 自动回收；
   debounce 的待执行任务随闭包存活，模块卸载后至多一个窗口期内自然结束
4. throttle 命中丢弃仅输出 TRACE 日志（对称于作用域静默）
{!--< /tips >!--}
"""

from __future__ import annotations

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any

from ..constants import GOVERNANCE_KEY_KINDS
from ..i18n import i18n
from .command_args import parse_duration


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
    if throttle_key not in GOVERNANCE_KEY_KINDS:
        raise ValueError(
            i18n.t(
                "core.event.throttle.invalid_key",
                key=throttle_key,
                kinds=", ".join(sorted(GOVERNANCE_KEY_KINDS)),
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


def make_debounce_wrapper(
    func: Callable,
    debounce: str,
    debounce_key: str = "user",
    handler_name: str = "",
) -> Callable:
    """
    构造防抖调用包装器（窗口内同键事件只执行最后一条）

    事件到达时取消同键前序的待执行任务，重新计时；窗口耗尽后才真正执行
    最后一条事件的处理。``functools.wraps`` 保留原签名（``__wrapped__``），
    使注册期 ``extract_depends`` 仍能从原函数提取 Depends 声明。

    :param func: 原事件处理器（async）
    :param debounce: 防抖窗口声明（如 ``"2s"``，duration 语法）
    :param debounce_key: 键粒度：``user``（默认）/ ``session`` / ``global``
    :param handler_name: 处理器名（日志展示用）
    :return: async 包装器——立即返回，真实执行延迟到窗口耗尽
    :raises ValueError: 声明非法（时长语法 / 粒度白名单）时装饰期抛出
    """
    delay = parse_duration(debounce)
    if debounce_key not in GOVERNANCE_KEY_KINDS:
        raise ValueError(
            i18n.t(
                "core.event.throttle.invalid_key",
                key=debounce_key,
                kinds=", ".join(sorted(GOVERNANCE_KEY_KINDS)),
            )
        )

    from ...runtime.context import current_owner

    _owner = current_owner.get()
    _pending: dict[str, asyncio.Task] = {}

    @functools.wraps(func)
    async def wrapper(event: Any, **kwargs: Any) -> None:
        key = _scope_key(debounce_key, event)
        old = _pending.pop(key, None)
        if old is not None and not old.done():
            old.cancel()

        async def _run():
            await asyncio.sleep(delay)
            _pending.pop(key, None)
            token = current_owner.set(_owner) if _owner else None
            try:
                await func(event, **kwargs)
            finally:
                if token is not None:
                    current_owner.reset(token)

        _pending[key] = asyncio.create_task(_run())

    return wrapper
