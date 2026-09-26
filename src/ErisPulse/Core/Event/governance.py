"""
ErisPulse 命令治理模块

命令治理（EPRFC-2026-001 方向七）的声明解析与运行时判定，自 CommandHandler 拆分：
注册期解析（parse_rate_limit / parse_usage / usage_period_key）、冷却作用域键计算，
以及分发期三段判定——冷却（cooldown=）/ 滑动窗口限流（rate_limit=）/ 自然周期配额
（usage_limit=）。状态表由 :class:`GovernanceGate` 持有，CommandHandler 以组合方式
挂载并经同名 property 透出，既有访问路径不变。

{!--< tips >!--}
1. 注册期：parse_rate_limit("5/minute") / parse_usage("3/day") 解析声明（fail-fast）
2. 分发期：gate.check_cooldown / check_rate_limit / check_usage 返回 True 即已拦截（静默或已回复）
3. 键粒度白名单复用 ``constants.GOVERNANCE_KEY_KINDS``（与 throttle 共用，本模块不重复定义）
{!--< /tips >!--}
"""

import asyncio
import re
import time
from collections import deque
from typing import TYPE_CHECKING, Any

from .. import logger
from ..constants import UNKNOWN_PLATFORM
from ..i18n import i18n
from .trace import trace_step

if TYPE_CHECKING:
    from .wrapper import Event

# 限流声明："次数/窗口"，窗口支持可选数值前缀与单字母/全称单位（如
# "5/minute"、"10/s"、"3/2m"）
_RATE_LIMIT_RE = re.compile(
    r"^(\d+)\s*/\s*((?:\d+(?:\.\d+)?)?\s*(?:seconds?|s|minutes?|m|hours?|h|days?|d))\s*$",
    re.IGNORECASE,
)
_WINDOW_AMOUNT_RE = re.compile(r"^(\d+(?:\.\d+)?)?\s*([a-zA-Z]+)$")
_RATE_LIMIT_UNITS = {
    "second": 1.0, "seconds": 1.0, "s": 1.0,
    "minute": 60.0, "minutes": 60.0, "m": 60.0,
    "hour": 3600.0, "hours": 3600.0, "h": 3600.0,
    "day": 86400.0, "days": 86400.0, "d": 86400.0,
}
# 配额声明的自然周期单位（minute / hour / day）与周期键格式
_USAGE_UNITS = {"minute": "minute", "minutes": "minute", "m": "minute",
                "hour": "hour", "hours": "hour", "h": "hour",
                "day": "day", "days": "day", "d": "day"}
_USAGE_PERIOD_FMT = {
    "minute": "%Y-%m-%dT%H:%M",
    "hour": "%Y-%m-%dT%H",
    "day": "%Y-%m-%d",
}


def parse_rate_limit(spec: str) -> "tuple[int, float]":
    """
    解析限流声明（如 ``"5/minute"``、``"10/s"``）为 (次数, 窗口秒)

    滑动窗口语义：窗口内至多放行 ``次数`` 次，超出静默丢弃。单位支持
    second / minute / hour / day（含单字母缩写与可选数值前缀，大小写不敏感）。

    :param spec: 限流声明字符串
    :return: (limit, window_seconds)
    :raises ValueError: 语法非法或数值非正时
    """
    match = _RATE_LIMIT_RE.match(spec or "")
    if not match:
        raise ValueError(f"invalid rate limit spec: {spec!r}")
    limit = int(match.group(1))
    window_str = match.group(2)
    # 窗口串 = 可选数值 + 单位词（如 "minute" / "0.3s" / "2 hours"）
    amount = _WINDOW_AMOUNT_RE.match(window_str)
    if amount is None:
        raise ValueError(f"invalid rate limit window: {window_str!r}")
    numeric = amount.group(1) or "1"
    window = float(numeric) * _RATE_LIMIT_UNITS[amount.group(2).lower()]
    if limit <= 0:
        raise ValueError(f"rate limit count must be positive: {spec!r}")
    if window <= 0:
        raise ValueError(f"rate limit window must be positive: {spec!r}")
    return limit, window


def parse_usage(spec: str) -> "tuple[int, str] | str":
    """
    解析配额声明（如 ``"3/day"``）为 (次数, 周期单位)

    自然周期语义：周期边界对齐本地时区的自然分钟 / 小时 / 日（如 day 为
    当日 00:00 起，次日自动重置），与 :func:`parse_rate_limit` 的滑动窗口
    相区分（rate_limit 防瞬时刷屏，usage_limit 管业务配额）。

    :param spec: 配额声明字符串
    :return: (limit, unit)；语法非法时返回错误描述字符串（调用方包装 ValueError）
    """
    match = _RATE_LIMIT_RE.match(spec or "")
    if not match:
        return f"invalid usage spec: {spec!r}"
    limit = int(match.group(1))
    unit = _USAGE_UNITS.get(match.group(2).lower().lstrip("0123456789. "))
    if unit is None:
        return f"unknown usage period: {spec!r} (minute/hour/day)"
    if limit <= 0:
        return f"usage count must be positive: {spec!r}"
    return limit, unit


# 配额周期键由 check_usage 分发期计算（服务器本地时区的自然周期）


def usage_period_key(unit: str) -> str:
    """
    计算当前自然周期的标识键（本地时区）

    {!--< internal-use >!--}
    供分发期配额判定使用；周期切换键随之变化即自动重置

    :param unit: 周期单位（minute / hour / day）
    :return: 周期键（如 ``"2026-09-21"``）
    {!--< /internal-use >!--}
    """
    return time.strftime(_USAGE_PERIOD_FMT[unit], time.localtime())


def cooldown_scope_key(kind: str, event: "Event") -> str:
    """
    {!--< internal-use >!--}
    计算冷却作用域键（复用 ``platform:bot:目标`` 会话键体系）

    :param kind: 粒度（user / session / global，注册期已校验）
    :param event: 事件数据
    :return: 作用域键字符串
    """
    if kind == "global":
        return "global"
    platform = event.get("platform", UNKNOWN_PLATFORM)
    bot_id = event.get_self_account_id() or ""
    if kind == "session":
        from ..scope import scope

        target = scope.session_id_from_event(event) or ""
        return f"{platform}:{bot_id}:{target}"
    return f"{platform}:{bot_id}:{event.get('user_id', '')}"


class GovernanceGate:
    """
    命令治理状态与判定

    持有冷却 / 限流 / 配额三张进程内状态表，提供分发期三段判定与生命周期清理。
    由 CommandHandler 组合持有（``self._gate``），状态表经其同名 property 透出。

    {!--< internal-use >!--}
    判定均位于全部权限检查与参数解析通过之后、实际执行之前：
    无权限用户不触发计时，参数错误不消耗；命中默认静默丢弃
    （命令已认领，不漏给低优先级消息处理器），声明了 ``*_reply=`` 时在
    状态翻转后的首次命中回复一次（边沿触发：同窗口 / 同周期的后续命中
    保持静默，避免连击时治理回复本身刷屏）。
    {!--< /internal-use >!--}
    """

    def __init__(self) -> None:
        # 键为 f"{main_name}\x00{scope_key}"（main_name 前缀供注销时按命令清理）
        # 冷却表：值为冷却结束时刻（time.monotonic() 秒）；限流表：窗口内放行时刻 deque；
        # 配额表：storage 持久化的读缓存/回退，键为 命令+键+周期
        self._cooldowns: dict[str, float] = {}
        self._rate_limits: dict[str, deque] = {}
        self._usage_counts: dict[str, int] = {}
        # 边沿回复标记：cooldown → 已回复窗口的截止时刻（窗口切换即失效）；
        # rate_limit → 已回复的键集合（窗口再次放行即清除，翻转后可重新回复）；
        # usage → 键 → 已回复的自然周期键（周期切换即失效）
        self._cooldown_replied: dict[str, float] = {}
        self._rate_limit_replied: "set[str]" = set()
        self._usage_replied: dict[str, str] = {}

    def clear_command(self, main_name: str) -> None:
        """
        {!--< internal-use >!--}
        按命令主名前缀清理三张状态表（模块卸载自动清理）

        :param main_name: 命令主名
        """
        prefix = main_name + "\x00"
        for table in (self._cooldowns, self._rate_limits, self._usage_counts):
            for key in [key for key in table if key.startswith(prefix)]:
                del table[key]
        for table in (self._cooldown_replied, self._usage_replied):
            for key in [key for key in table if key.startswith(prefix)]:
                del table[key]
        for key in [
            key for key in self._rate_limit_replied if key.startswith(prefix)
        ]:
            self._rate_limit_replied.discard(key)

    def clear_all(self) -> None:
        """{!--< internal-use >!--} 清空全部治理状态（_clear_commands 调用）"""
        self._cooldowns.clear()
        self._rate_limits.clear()
        self._usage_counts.clear()
        self._cooldown_replied.clear()
        self._rate_limit_replied.clear()
        self._usage_replied.clear()

    async def check_cooldown(
        self,
        main_name: str,
        actual_cmd_name: str,
        effective: dict[str, Any],
        event: "Event",
        send_reply: Any,
    ) -> bool:
        """
        {!--< internal-use >!--}
        冷却判定（cooldown=）：执行前即开始计时，实际冷却窗口不受处理耗时影响

        :param main_name: 命令主名（状态表键前缀）
        :param actual_cmd_name: 实际调用的命令名（日志 / trace 展示）
        :param effective: 合并覆写后的命令生效参数
        :param event: 事件数据
        :param send_reply: 回复回调（``await send_reply(event, text)``）
        :return: True 表示已拦截（静默丢弃或已回复）
        """
        if not effective.get("cooldown_seconds"):
            return False
        scope_key = cooldown_scope_key(effective.get("cooldown_key", "user"), event)
        cooldown_entry = f"{main_name}\x00{scope_key}"
        now = time.monotonic()
        deadline = self._cooldowns.get(cooldown_entry, 0.0)
        if now < deadline:
            trace_step(
                "cooldown",
                "dropped",
                "core.trace.cooldown_dropped",
                command=actual_cmd_name,
                remain=f"{deadline - now:.1f}",
            )
            logger.trace(
                i18n.t(
                    "core.command.cooldown_hit",
                    cmd_name=actual_cmd_name,
                    scope=scope_key,
                    remain=f"{deadline - now:.1f}",
                    platform=event.get("platform", UNKNOWN_PLATFORM),
                    user_id=event.get("user_id", ""),
                )
            )
            if effective.get("cooldown_reply"):
                if self._cooldown_replied.get(cooldown_entry) != deadline:
                    self._cooldown_replied[cooldown_entry] = deadline
                    await send_reply(event, effective["cooldown_reply"])
            return True
        self._cooldowns[cooldown_entry] = now + effective["cooldown_seconds"]
        return False

    async def check_rate_limit(
        self,
        main_name: str,
        actual_cmd_name: str,
        effective: dict[str, Any],
        event: "Event",
        send_reply: Any,
    ) -> bool:
        """
        {!--< internal-use >!--}
        限流判定（rate_limit=，滑动窗口）：与冷却同位次序——权限与参数通过后、
        实际执行前计数；窗口满时默认静默丢弃（可选回复）

        :param main_name: 命令主名（状态表键前缀）
        :param actual_cmd_name: 实际调用的命令名（日志 / trace 展示）
        :param effective: 合并覆写后的命令生效参数
        :param event: 事件数据
        :param send_reply: 回复回调（``await send_reply(event, text)``）
        :return: True 表示已拦截（静默丢弃或已回复）
        """
        if not effective.get("rate_limit_spec"):
            return False
        now = time.monotonic()
        limit, window = effective["rate_limit_spec"]
        rl_scope = cooldown_scope_key(effective.get("rate_limit_key", "user"), event)
        rl_entry = f"{main_name}\x00{rl_scope}"
        dq = self._rate_limits.setdefault(rl_entry, deque())
        while dq and dq[0] <= now - window:
            dq.popleft()
        if len(dq) >= limit:
            logger.trace(
                i18n.t(
                    "core.command.rate_limit_hit",
                    cmd_name=actual_cmd_name,
                    scope=rl_scope,
                    limit=limit,
                    window=window,
                    platform=event.get("platform", UNKNOWN_PLATFORM),
                    user_id=event.get("user_id", ""),
                )
            )
            trace_step(
                "rate_limit",
                "dropped",
                "core.trace.rate_limit_dropped",
                command=actual_cmd_name,
                limit=str(limit),
                window=f"{window:g}",
            )
            if effective.get("rate_limit_reply") and (
                rl_entry not in self._rate_limit_replied
            ):
                self._rate_limit_replied.add(rl_entry)
                await send_reply(event, effective["rate_limit_reply"])
            return True
        dq.append(now)
        self._rate_limit_replied.discard(rl_entry)
        return False

    async def check_usage(
        self,
        main_name: str,
        actual_cmd_name: str,
        effective: dict[str, Any],
        event: "Event",
        send_reply: Any,
    ) -> bool:
        """
        {!--< internal-use >!--}
        配额判定（usage=，自然周期）：与限流同位次序；计数经 storage KV
        持久化（重启不丢），存储异常时回退进程内内存计数（不阻塞命令）

        :param main_name: 命令主名（状态表键前缀）
        :param actual_cmd_name: 实际调用的命令名（日志 / trace 展示）
        :param effective: 合并覆写后的命令生效参数
        :param event: 事件数据
        :param send_reply: 回复回调（``await send_reply(event, text)``）
        :return: True 表示已拦截（静默丢弃或已回复）
        """
        if not effective.get("usage_spec"):
            return False
        u_limit, u_unit = effective["usage_spec"]
        u_scope = cooldown_scope_key(effective.get("usage_limit_key", "user"), event)
        u_period = usage_period_key(u_unit)
        sep = "\x00"
        u_key = sep.join((main_name, u_scope, u_period))
        used = self._usage_counts.get(u_key, 0)
        persisted = False
        from ..storage import storage

        try:
            # wait_for 兜底：后台桥接 loop 不可用（如裸 asyncio.run 测试
            # 场景）时限时回退内存计数，避免分发路径卡死
            stored = await asyncio.wait_for(
                storage.aget(f"erispulse.usage{chr(0)}{u_key}"), timeout=1.0
            )
            if isinstance(stored, int) and stored > used:
                used = stored
            persisted = True
        except Exception as e:
            logger.trace(f"usage quota storage fallback: {e}")
        if used >= u_limit:
            logger.trace(
                i18n.t(
                    "core.command.usage_hit",
                    cmd_name=actual_cmd_name,
                    scope=u_scope,
                    limit=u_limit,
                    period=u_period,
                    platform=event.get("platform", UNKNOWN_PLATFORM),
                    user_id=event.get("user_id", ""),
                )
            )
            trace_step(
                "usage",
                "dropped",
                "core.trace.usage_dropped",
                command=actual_cmd_name,
                limit=str(u_limit),
                period=u_period,
            )
            if effective.get("usage_limit_reply") and (
                self._usage_replied.get(u_key) != u_period
            ):
                self._usage_replied[u_key] = u_period
                await send_reply(event, effective["usage_limit_reply"])
            return True
        self._usage_counts[u_key] = used + 1
        if persisted:
            try:
                await asyncio.wait_for(
                    storage.aset(f"erispulse.usage{chr(0)}{u_key}", used + 1),
                    timeout=1.0,
                )
            except Exception as e:
                logger.trace(f"usage quota persist failed: {e}")
        return False
