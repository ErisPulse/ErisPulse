"""
ErisPulse 命令处理模块

提供基于装饰器的命令注册和处理功能

命令是特殊的消息事件处理器（ErisPulse 扩展类型），其用户侧配置
由统一覆写系统持有（``ErisPulse.event.overrides``，见
:mod:`ErisPulse.Core.Event.overrides`）：**用户黑白名单（ACL）** 在
``overrides.acl`` 类别（命令名支持 glob，``acl_default_allow`` 兜底严格模式）；
**实现参数覆写**（master / hidden / aliases 等）在 ``overrides.command`` 类别
（用户优先语义）。本模块的命令判定链消费覆写系统的生效结果。

{!--< tips >!--}
1. 支持命令别名和命令组
2. 支持命令权限控制（master / permission 函数 / 覆写系统 ACL）
3. 支持命令帮助系统
4. 支持等待用户回复交互
5. 支持声明式参数与选项（``args=`` / ``options=``）：自动类型转换、本地化错误提示与 usage 生成
{!--< /tips >!--}
"""

import asyncio
import inspect
from collections import deque
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .wrapper import Event

from ...runtime import get_event_config
from ...runtime.context import current_owner, handler_waits
from .. import adapter, logger
from ..constants import (
    DEFAULT_COMMAND_ALLOW_SPACE_PREFIX,
    DEFAULT_COMMAND_BLOCK,
    DEFAULT_COMMAND_CASE_SENSITIVE,
    DEFAULT_COMMAND_DISPATCHER_PRIORITY,
    DEFAULT_COMMAND_MUST_AT_BOT,
    DEFAULT_COMMAND_PREFIX,
    DEFAULT_SEND_METHOD,
    DEFAULT_WAIT_TIMEOUT_SECS,
    DETAIL_TYPE_PRIVATE,
    DETAIL_TYPE_USER,
    GOVERNANCE_KEY_KINDS,
    UNKNOWN_PLATFORM,
)

# 冷却 / 限流键粒度白名单（cooldown_key= / rate_limit_key=，EPRFC-2026-001 方向七）：
# user=同一用户 / session=同一会话 / global=全局共享（与 throttle_key 共用 constants 定义）
from ..constants import GOVERNANCE_KEY_KINDS as _KEY_KINDS
from ..di import extract_depends, resolve_depends
from ..i18n import i18n
from . import overrides
from .base import BaseEventHandler
from .command_args import (
    CommandArgsError,
    bind_command_arguments,
    format_usage,
    parse_args_spec,
    parse_duration,
    parse_options_spec,
)
from .governance import (
    GovernanceGate,
    cooldown_scope_key,
)
from .governance import (
    parse_rate_limit as _parse_rate_limit_impl,
)
from .governance import (
    parse_usage as _parse_usage_impl,
)
from .governance import (
    usage_period_key as _usage_period_key_impl,
)
from .interaction import InteractionCancelled, interaction
from .session_type import get_send_type_and_target_id, infer_receive_type
from .trace import trace_step


class CommandHandler:
    """
    命令处理器

    提供命令注册、处理和管理功能
    """

    def __init__(self):
        self.commands: dict[str, dict] = {}
        self.aliases: dict[str, str] = {}  # 别名映射
        self.groups: dict[str, list[str]] = {}  # 命令组
        self.permissions: dict[str, Callable] = {}  # 权限检查函数
        # 影子命令目录（方向十一）：影子 owner 注册的命令进此目录而非真实
        # 分发表——避免静默顶掉 v1 的同名命令；供 diff 对比视图消费
        self._shadow_catalog: dict[str, dict] = {}
        # 命令治理状态（cooldown / rate_limit / usage，EPRFC-2026-001 方向七）：
        # 状态表与判定拆分至 GovernanceGate 持有，经下方同名 property 透出
        self._gate = GovernanceGate()
        # 已注册命令名/别名的最大 token 数（命令名支持空格分隔的子命令形式，
        # 如 "admin add"；匹配阶段据此决定最长前缀尝试次数，注册/注销时重算）
        self._max_name_tokens: int = 1

        # 从配置读取命令解析参数（并订阅热更新）
        self._refresh_command_config()
        try:
            from ..lifecycle import lifecycle

            lifecycle.register("config.updated", self._on_config_updated)
            lifecycle.register("config.set", self._on_config_updated)
        except Exception:
            pass

        # 等待回复：委托交互会话管理器（Core/Event/interaction.py），
        # 由其统一维护会话键索引 / owner 归属 / 平台索引与互斥租约
        # （历史属性 _waiting_replies 已迁移，不再在本类持有等待表）

        # 共享的消息事件处理器引用（由 bind_message_handler() 设置）
        # 命令分发器 _handle_message 以高优先级注册在同一个队列中，
        # 确保命令 /xxx 始终优先于 on_message / on_group_message 触发
        self._bound_handler: BaseEventHandler | None = None
        self._dispatcher_registered: bool = False

    # 命令治理状态表（真实持有在 GovernanceGate）：
    # property 透出保持既有访问路径（tests 直接 clear / 读写条目）不变
    @property
    def _cooldowns(self) -> dict[str, float]:
        """{!--< internal-use >!--} 命令冷却状态表（cooldown= 声明）"""
        return self._gate._cooldowns

    @property
    def _rate_limits(self) -> dict[str, deque]:
        """{!--< internal-use >!--} 命令限流状态表（rate_limit= 滑动窗口）"""
        return self._gate._rate_limits

    @property
    def _usage_counts(self) -> dict[str, int]:
        """{!--< internal-use >!--} 配额内存计数表（usage= 持久化读缓存）"""
        return self._gate._usage_counts

    def _refresh_command_config(self) -> None:
        """
        从配置读取命令解析相关参数

        支持配置热更新：``config.updated`` 事件触发后再次调用即可刷新
        前缀 / 大小写 / 空格前缀 / 是否须 @机器人 等解析参数。
        """
        command_config = get_event_config().get("command", {})
        # prefix 支持字符串（单个）或列表（多个），保持原始类型以向后兼容
        self.prefix = command_config.get("prefix", DEFAULT_COMMAND_PREFIX)
        # 归一化为列表，用于内部统一处理
        self._prefixes = list(self.prefix) if isinstance(self.prefix, list) else [self.prefix]
        self.case_sensitive = command_config.get("case_sensitive", DEFAULT_COMMAND_CASE_SENSITIVE)
        self.allow_space_prefix = command_config.get("allow_space_prefix", DEFAULT_COMMAND_ALLOW_SPACE_PREFIX)
        self.must_at_bot = command_config.get("must_at_bot", DEFAULT_COMMAND_MUST_AT_BOT)
        # 命令命中后是否阻断向低优先级处理器传播（认领不受此开关影响）
        self.block = command_config.get("block", DEFAULT_COMMAND_BLOCK)

    def _on_config_updated(self, _data: dict) -> None:
        """配置变更回调：刷新命令解析参数、实现参数覆盖与用户 ACL"""
        self._refresh_command_config()

    def _recompute_max_name_tokens(self) -> None:
        """
        {!--< internal-use >!--}
        重算已注册命令名 / 别名中的最大 token 数

        命令名支持空格分隔的子命令形式（如 ``"admin add"``），匹配阶段按
        最长前缀尝试；此缓存在注册与注销后重算，消息分发期只做字典查找。
        """
        self._max_name_tokens = max(
            (len(name.split()) for name in {**self.commands, **self.aliases}),
            default=1,
        )

    def _resolve_command_tokens(self, parts: list[str]) -> tuple[str | None, str | None, int]:
        """
        {!--< internal-use >!--}
        按"最长前缀匹配"从已切分的命令 token 中解析命令名

        依次尝试 ``parts[:n]``（n 从最大注册 token 数降到 1）组成的候选名，
        先查别名映射再查命令表；命中即返回，未命中继续降级尝试。

        :param parts: 空格切分后的命令 token 列表（大小写已按配置归一）
        :return: ``(命中的候选名（可能为别名形式）, 解析后的命令全名, 命中的 token 数)``；
                 全部未命中返回 ``(None, None, 0)``
        """
        for n in range(min(self._max_name_tokens, len(parts)), 0, -1):
            candidate = " ".join(parts[:n])
            # 命令名优先于别名：同名冲突时注册的命令生效（别名在注册期
            # 已告警并让位），消除别名静默劫持命令的歧义
            if candidate in self.commands:
                return candidate, candidate, n
            actual = self.aliases.get(candidate)
            if actual is not None and actual in self.commands:
                return candidate, actual, n
        return None, None, 0

    def _inherited_permission(self, name: str) -> Callable | None:
        """
        {!--< internal-use >!--}
        沿命令名父链向上查找最近声明了权限函数的祖先命令

        子命令（空格分隔的多 token 命令名，如 ``"admin add"``）自身未声明
        permission 时调用：逐级去掉末尾 token 查找已注册祖先，返回第一个
        声明了权限的祖先的权限函数——保护父命令即保护其下全部子命令
        （声明了权限的祖先会跳过未声明权限的中间祖先继续上溯）。
        仅读取注册值，不递归用户覆写。

        :param name: 已解析的命令全名
        :return: 祖先的权限检查函数；无可继承权限时返回 None
        """
        tokens = name.split()
        while len(tokens) > 1:
            tokens.pop()
            parent_info = self.commands.get(" ".join(tokens))
            if parent_info is None:
                continue
            permission = parent_info.get("permission")
            if permission:
                return permission
        return None

    # ==================== 命令治理声明解析（cooldown / rate_limit / usage）====================

    # 键粒度白名单（cooldown_key= / rate_limit_key=，与 throttle 共用 constants 定义）
    _KEY_KINDS = GOVERNANCE_KEY_KINDS

    @classmethod
    def parse_rate_limit(cls, spec: str) -> "tuple[int, float]":
        """
        解析限流声明（如 ``"5/minute"``、``"10/s"``）为 (次数, 窗口秒)

        滑动窗口语义：窗口内至多放行 ``次数`` 次，超出静默丢弃。单位支持
        second / minute / hour / day（含单字母缩写与可选数值前缀，大小写不敏感）。

        :param spec: 限流声明字符串
        :return: (limit, window_seconds)
        :raises ValueError: 语法非法或数值非正时
        """
        return _parse_rate_limit_impl(spec)

    @classmethod
    def parse_usage(cls, spec: str) -> "tuple[int, str] | str":
        """
        解析配额声明（如 ``"3/day"``）为 (次数, 周期单位)

        自然周期语义：周期边界对齐本地时区的自然分钟 / 小时 / 日（如 day 为
        当日 00:00 起，次日自动重置），与 :meth:`parse_rate_limit` 的滑动窗口
        相区分（rate_limit 防瞬时刷屏，usage_limit 管业务配额）。

        :param spec: 配额声明字符串
        :return: (limit, unit)；语法非法时返回错误描述字符串（调用方包装 ValueError）
        """
        return _parse_usage_impl(spec)

    @staticmethod
    def usage_period_key(unit: str) -> str:
        """
        计算当前自然周期的标识键（本地时区）

        {!--< internal-use >!--}
        供分发期配额判定使用；周期切换键随之变化即自动重置

        :param unit: 周期单位（minute / hour / day）
        :return: 周期键（如 ``"2026-09-21"``）
        {!--< /internal-use >!--}
        """
        return _usage_period_key_impl(unit)

    # ==================== 作用域上下文（scope 委托） ====================

    @staticmethod
    def _scope() -> Any:
        """
        {!--< internal-use >!--}
        延迟获取作用域单例（避免模块初始化阶段的循环依赖）

        用于模块维度作用域检查与事件上下文提取。

        :return: scope 单例（ScopeManager）
        """
        from ..scope import scope

        return scope

    def __call__(
        self,
        name: str | list[str] | None = None,
        aliases: list[str] | None = None,
        group: str | None = None,
        priority: int = 0,
        permission: Callable | None = None,
        help: str | None = None,
        usage: str | None = None,
        hidden: bool = False,
        master: bool = False,
        args: str | None = None,
        options: dict | None = None,
        cooldown: str | None = None,
        cooldown_key: str = "user",
        cooldown_reply: str | None = None,
        rate_limit: str | None = None,
        rate_limit_key: str = "user",
        rate_limit_reply: str | None = None,
        usage_limit: str | None = None,
        usage_limit_key: str = "user",
        usage_limit_reply: str | None = None,
        deprecated: str | None = None,
        deprecated_reject: bool = False,
    ):
        """
        命令装饰器

        :param name: 命令名称，可以是字符串或字符串列表
        :param aliases: 命令别名列表
        :param group: 命令组名称
        :param priority: 处理器优先级
        :param permission: 权限检查函数，返回True时允许执行命令
        :param help: 命令帮助信息
        :param usage: 命令使用方法
        :param hidden: 是否在帮助中隐藏命令
        :param master: 是否仅允许框架主人执行（框架自动检查 ``master.is_master(event)``）
        :param args: 声明式位置参数定义，如 ``"<count:int> [sides:int=6]"``。类型支持
            ``str`` / ``int`` / ``float`` / ``bool`` / ``literal``（枚举，``<mode:literal=fast|slow>``）/
            ``duration``（如 ``90s``、``1h30m``）/ ``rest``（剩余全部文本，须在最后）。
            可选条目未声明默认值（``[name:type]``）时回填处理器签名同名参数的默认值。
            声明后框架在权限检查通过后自动解析并按名注入处理器参数，用户输入错误时
            自动回复本地化提示与用法（不会抛异常崩溃）；不声明则保持原行为
        :param options: 声明式选项定义，如 ``{"verbose": "-v/--verbose", "label": "--label"}``。
            键为处理器参数名，值为旗标形式（多个别名以 ``/`` 分隔）：注解为 ``bool`` 的参数
            为布尔旗标；其余（缺省按 ``str``）为带值选项，支持 ``--label hello`` 与
            ``--label=hello`` 取值，类型跟随处理器注解。选项先于位置参数解析——``rest``
            覆盖剔除选项后的剩余文本。声明参数名必须存在于处理器签名中（否则注册期抛 ValueError）
        :param cooldown: 命令冷却声明（EPRFC-2026-001 方向七），时长语法与 ``args=`` 的
            ``duration`` 类型一致（如 ``"30s"``、``"1h30m"``、``"1d"``）。冷却命中时命令
            默认静默丢弃（对称于作用域静默），命令仍保持已认领状态（不漏给低优先级
            消息处理器）；冷却在全部权限检查与参数解析通过、命令实际执行前开始计时，
            参数错误不消耗冷却。进程内内存状态，模块卸载时自动清理
        :param cooldown_key: 冷却键粒度：``"user"``（默认，同一用户全局共享）/ ``"session"``
            （同一会话共享）/ ``"global"``（所有用户所有会话共享）。``user`` / ``session``
            复用 ``platform:bot:目标`` 会话键体系。非法值注册期抛 ValueError
        :param cooldown_reply: 冷却命中时的回复文案（可选）。缺省静默丢弃；指定后
            按边沿触发回复——进入冷却后的首次命中回复一次，同冷却窗口内的后续
            命中保持静默（避免连击时治理回复本身刷屏；原文发送，不做格式化）
        :param rate_limit: 滑动窗口限流声明（EPRFC-2026-001 方向七），如 ``"5/minute"`` /
            ``"10/s"`` / ``"100/day"``——窗口内至多执行次数，超出默认静默丢弃（命令仍被
            认领）；与 ``cooldown=`` 共享会话键体系，可同时声明（冷却先判、限流后判）
        :param rate_limit_key: 限流键粒度：``"user"``（默认）/ ``"session"`` / ``"global"``
        :param rate_limit_reply: 限流命中时的回复文案（可选，缺省静默丢弃；边沿触发——
            窗口从"未满"再次变为"已满"的首次命中才回复一次，窗口有放行即重置）
        :param usage_limit: 自然周期配额声明（如 ``"3/day"`` / ``"5/hour"`` / ``"10/minute"``）——
            每键在自然周期（分钟 / 小时 / 日，本地时区）内至多执行 ``次数``，周期切换自动
            重置；计数经 storage KV 持久化，重启不丢（与 ``rate_limit=`` 滑动窗口的
            区别：rate_limit 防瞬时刷屏，usage 管业务配额如"每日签到 3 次"）
        :param usage_limit_key: 配额键粒度：``"user"``（默认）/ ``"session"`` / ``"global"``
        :param usage_limit_reply: 配额用尽时的回复文案（可选，缺省静默丢弃；边沿触发——
            每个自然周期至多回复一次，周期切换后重新可回复）
        :param deprecated: 命令废弃声明（EPRFC-2026-001 方向七）：非空文案即标记废弃——
            调用时自动回复该文案（help 列表显示废弃标记），默认仍继续执行
        :param deprecated_reject: 废弃命令拒绝执行（默认 False 继续执行；True 时回复
            废弃文案后不再执行处理器）
        :return: 装饰器函数

        :example:
        >>> @command("roll", args="<count:int> [sides:int=6]",
        ...          options={"verbose": "-v/--verbose", "label": "--label"})
        ... async def roll(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
        ...     await event.reply(f"掷了 {count} 次 {sides} 面骰")
        >>> @command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今天已签到")
        ... async def daily(event):
        ...     await event.reply("签到成功！")
        >>> @command("search", rate_limit="5/minute", rate_limit_key="user")
        ... async def search(event): ...
        >>> @command("oldcmd", deprecated="请用 /newcmd", deprecated_reject=True)
        ... async def old(event): ...
        """

        def decorator(func: Callable):
            # 确保命令分发器已注册到共享 handler
            if not self._dispatcher_registered:
                self._register_dispatcher()

            cmd_names = []
            if isinstance(name, str):
                cmd_names = [name]
            elif isinstance(name, list):
                cmd_names = name
            else:
                # 使用函数名作为命令名
                cmd_names = [func.__name__]

            main_name = cmd_names[0]

            # 声明式参数/选项（args= / options=）注册期解析与校验（fail-fast）：
            # 语法错误或处理器签名不匹配直接抛 ValueError，避免到分发期才发现
            args_spec = parse_args_spec(args) if args else None
            options_spec = parse_options_spec(options, func) if options else None
            declared = [entry.name for entry in (args_spec or [])] + list((options_spec or {}).keys())

            # 冷却声明（cooldown=）注册期解析与校验（fail-fast）：
            # 时长语法复用 args= duration 的解析口径，粒度白名单校验
            cooldown_seconds: float | None = None
            if cooldown:
                try:
                    cooldown_seconds = parse_duration(cooldown)
                except ValueError as e:
                    raise ValueError(
                        i18n.t("core.command.cooldown.invalid", cmd=main_name, error=e)
                    ) from e
                if cooldown_key not in _KEY_KINDS:
                    raise ValueError(
                        i18n.t(
                            "core.command.cooldown.invalid_key",
                            cmd=main_name,
                            key=cooldown_key,
                            kinds=", ".join(sorted(_KEY_KINDS)),
                        )
                    )
            elif cooldown_reply:
                raise ValueError(
                    i18n.t("core.command.cooldown.reply_without_cooldown", cmd=main_name)
                )

            # 限流声明（rate_limit=）注册期解析与校验（fail-fast）
            rate_limit_spec: tuple[int, float] | None = None
            if rate_limit:
                try:
                    rate_limit_spec = self.parse_rate_limit(rate_limit)
                except ValueError as e:
                    raise ValueError(
                        i18n.t("core.command.rate_limit.invalid", cmd=main_name, error=e)
                    ) from e
                if rate_limit_key not in _KEY_KINDS:
                    raise ValueError(
                        i18n.t(
                            "core.command.rate_limit.invalid_key",
                            cmd=main_name,
                            key=rate_limit_key,
                            kinds=", ".join(sorted(_KEY_KINDS)),
                        )
                    )
            elif rate_limit_reply:
                raise ValueError(
                    i18n.t("core.command.rate_limit.reply_without_limit", cmd=main_name)
                )

            # 配额声明（usage=）注册期解析与校验（fail-fast）：自然周期
            usage_spec: tuple[int, str] | None = None
            if usage_limit:
                _parsed_usage = self.parse_usage(usage_limit)
                if isinstance(_parsed_usage, str):
                    raise ValueError(
                        i18n.t(
                            "core.command.usage.invalid", cmd=main_name, error=_parsed_usage
                        )
                    )
                usage_spec = _parsed_usage
                if usage_limit_key not in _KEY_KINDS:
                    raise ValueError(
                        i18n.t(
                            "core.command.usage.invalid_key",
                            cmd=main_name,
                            key=usage_limit_key,
                            kinds=", ".join(sorted(_KEY_KINDS)),
                        )
                    )
            elif usage_limit_reply:
                raise ValueError(
                    i18n.t("core.command.usage.reply_without_usage", cmd=main_name)
                )

            # 废弃声明（deprecated=）注册期校验：非空文案；reject 须搭配声明
            if deprecated is not None and not isinstance(deprecated, str):
                raise ValueError(
                    i18n.t("core.command.deprecated.invalid", cmd=main_name)
                )
            if deprecated is not None and not deprecated.strip():
                raise ValueError(
                    i18n.t("core.command.deprecated.invalid", cmd=main_name)
                )
            if deprecated_reject and not deprecated:
                raise ValueError(
                    i18n.t(
                        "core.command.deprecated.reject_without_deprecated", cmd=main_name
                    )
                )
            # 依赖注入声明（Depends）：与 args=/options= 参数重名即注册期冲突（fail-fast）
            depends = extract_depends(func)
            if declared:
                conflict = [n for n in declared if n in depends]
                if conflict:
                    raise ValueError(
                        i18n.t(
                            "core.command.args.depends_conflict",
                            cmd=main_name,
                            names=", ".join(conflict),
                        )
                    )
            if declared:
                sig_params = inspect.signature(func).parameters
                accepted = set(sig_params)
                if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in sig_params.values()):
                    accepted.add("*")
                missing = [n for n in declared if n not in accepted]
                if missing:
                    raise ValueError(
                        i18n.t(
                            "core.command.args.param_mismatch",
                            cmd=main_name,
                            names=", ".join(missing),
                        )
                    )

            # 影子命令分流（方向十一）：影子 owner 的命令不进真实分发表
            # （否则会静默顶掉 v1 的同名命令），只登记影子命令目录供对比视图。
            # 分流点位于全部 fail-fast 校验之后——影子与真实模块看到一致的
            # 注册期报错行为
            try:
                from ..ownership import ownership as _ownership

                if _ownership.is_shadow(current_owner.get()):
                    for cmd_name in cmd_names:
                        self._shadow_catalog[cmd_name] = {
                            "func": func,
                            "help": help,
                            "usage": usage,
                            "group": group,
                            "hidden": hidden,
                            "main_name": main_name,
                            "owner": current_owner.get(),
                            "args_spec": args_spec,
                            "options_spec": options_spec,
                        }
                    logger.debug(
                        i18n.t(
                            "core.command.shadow_command_cataloged",
                            cmd_name=main_name,
                            owner=current_owner.get() or "-",
                        )
                    )
                    return func
            except Exception:
                pass

            # 添加别名
            alias_list = aliases or []
            if len(cmd_names) > 1:
                alias_list.extend(cmd_names[1:])

            # 注册命令
            for cmd_name in cmd_names:
                # 跨模块重名检测：后注册者会静默顶掉先注册者（"命令没反应"
                # 的常见病灶）；同 owner 重注册属正常流程（如懒激活占位命令
                # 被真实命令替换），不告警
                _existing = self.commands.get(cmd_name)
                if _existing is not None and _existing.get("owner") != current_owner.get():
                    logger.warning(
                        i18n.t(
                            "core.command.duplicate_name",
                            cmd_name=cmd_name,
                            old_owner=_existing.get("owner") or "-",
                            new_owner=current_owner.get() or "-",
                        )
                    )
                # 命令名 vs 别名冲突：命令名优先，指向其它命令的既有别名
                # 被本命令遮蔽，移除该别名（否则它成为永远不可达的死条目）
                if cmd_name in self.aliases and self.aliases[cmd_name] != main_name:
                    logger.warning(
                        i18n.t(
                            "core.command.name_conflicts_alias",
                            cmd_name=cmd_name,
                            main_name=self.aliases[cmd_name],
                        )
                    )
                    self.aliases.pop(cmd_name, None)
                self.commands[cmd_name] = {
                    "func": func,
                    "help": help,
                    "usage": usage,
                    "group": group,
                    "permission": permission,
                    "hidden": hidden,
                    "must_master": master,
                    "main_name": main_name,
                    "owner": current_owner.get(),
                    "args_spec": args_spec,
                    "options_spec": options_spec,
                    "depends": depends,
                    "cooldown_seconds": cooldown_seconds,
                    "cooldown_key": cooldown_key,
                    "cooldown_reply": cooldown_reply,
                    "rate_limit_spec": rate_limit_spec,
                    "rate_limit_key": rate_limit_key,
                    "rate_limit_reply": rate_limit_reply,
                    "usage_spec": usage_spec,
                    "usage_limit_key": usage_limit_key,
                    "usage_limit_reply": usage_limit_reply,
                    "deprecated": deprecated,
                    "deprecated_reject": deprecated_reject,
                }

                # 注册别名映射（name列表中的额外名称）
                if cmd_name != main_name:
                    self.aliases[cmd_name] = main_name

                # 注册权限检查函数
                if permission and cmd_name not in self.permissions:
                    self.permissions[cmd_name] = permission

            # 注册aliases参数中的别名
            for alias in alias_list:
                if alias in self.commands:
                    # 别名与已注册命令重名：命令名优先，该别名不生效
                    logger.warning(
                        i18n.t(
                            "core.command.alias_conflicts_command",
                            alias=alias,
                            cmd_name=alias,
                        )
                    )
                    continue
                if alias in self.aliases:
                    # 同名别名已指向其它命令：保持先注册者生效
                    logger.warning(
                        i18n.t(
                            "core.command.alias_conflicts_alias",
                            alias=alias,
                            main_name=self.aliases[alias],
                        )
                    )
                    continue
                self.aliases[alias] = main_name

            # 添加到命令组
            if group:
                if group not in self.groups:
                    self.groups[group] = []
                for cmd_name in cmd_names:
                    if cmd_name not in self.groups[group]:
                        self.groups[group].append(cmd_name)

            # 命令名集合变化，重算最长前缀匹配的 token 数缓存
            self._recompute_max_name_tokens()

            return func

        return decorator

    def unregister(self, handler: Callable) -> bool:
        """
        注销命令处理器

        :param handler: 要注销的命令处理器
        :return: 是否成功注销
        """
        # 从共享 handler 中注销命令函数（如已注册）
        result = False
        if self._bound_handler is not None:
            result = self._bound_handler.unregister(handler)

        # 从命令映射中移除
        commands_to_remove = []
        for cmd_name, cmd_info in self.commands.items():
            if cmd_info["func"] == handler:
                commands_to_remove.append(cmd_name)

        for cmd_name in commands_to_remove:
            # 移除命令别名映射
            main_name = self.commands[cmd_name]["main_name"]
            aliases_to_remove = [alias for alias, name in self.aliases.items() if name == main_name]
            for alias in aliases_to_remove:
                del self.aliases[alias]

            # 从命令组中移除
            for group_commands in self.groups.values():
                if cmd_name in group_commands:
                    group_commands.remove(cmd_name)

            # 移除权限检查函数
            if cmd_name in self.permissions:
                del self.permissions[cmd_name]

            # 清理该命令的冷却 / 限流 / 配额状态（模块卸载自动清理）
            self._gate.clear_command(main_name)

            # 最后移除命令本身
            del self.commands[cmd_name]

        if commands_to_remove:
            # 命令名集合变化，重算最长前缀匹配的 token 数缓存
            self._recompute_max_name_tokens()

        # 共享 handler 注销与命令映射移除任一成功即视为注销成功
        return result or bool(commands_to_remove)

    def unregister_by_owner(self, owner: str) -> int:
        """
        {!--< internal-use >!--}
        按归属者精确移除命令

        :param owner: 归属者（模块名）
        :return: 移除的命令数量
        """
        # 同步取消该归属者挂起的交互等待（等待方立即收到取消而非干等超时）
        interaction.cancel_by_owner(owner)

        to_remove = [name for name, info in self.commands.items() if info.get("owner") == owner]
        for cmd_name in to_remove:
            cmd_info = self.commands[cmd_name]
            main_name = cmd_info.get("main_name", cmd_name)

            self.aliases = {a: n for a, n in self.aliases.items() if not (n == main_name and a != main_name)}

            for group_cmds in self.groups.values():
                if cmd_name in group_cmds:
                    group_cmds.remove(cmd_name)

            self.permissions.pop(cmd_name, None)

            # 清理该命令的冷却 / 限流 / 配额状态（模块卸载自动清理）
            self._gate.clear_command(main_name)

            del self.commands[cmd_name]

        # 清理空命令组
        self.groups = {k: v for k, v in self.groups.items() if v}

        if to_remove:
            # 命令名集合变化，重算最长前缀匹配的 token 数缓存
            self._recompute_max_name_tokens()

            from ..logger import logger as _logger

            _logger.trace(i18n.t("core.command.cleaned", owner=owner, count=len(to_remove), commands=to_remove))
        return len(to_remove)

    async def wait_reply(
        self,
        event: dict[str, Any],
        prompt: str | None = None,
        timeout: float = DEFAULT_WAIT_TIMEOUT_SECS,
        callback: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
        validator: Callable[[dict[str, Any]], bool] | None = None,
        method: str = DEFAULT_SEND_METHOD,
        pattern: str | None = None,
        regex: str | None = None,
        session: bool = False,
        cmdpass: bool | None = None,
    ) -> dict[str, Any] | None:
        """
        等待用户回复

        :param event: 原始事件数据
        :param prompt: 提示消息，如果提供会发送给用户
        :param timeout: 等待超时时间(秒)
        :param callback: 回调函数，当收到回复时执行
        :param validator: 验证函数，用于验证回复是否有效
        :param method: 发送方法，默认为 "Text"
        :param pattern: glob 通配符（``*`` / ``?`` / ``[seq]``），回复文本不匹配时继续等待
        :param regex: 正则表达式，回复文本不匹配时继续等待（与 pattern 同时给定时须都匹配）
        :param session: 会话级等待——同会话（群 / 频道）中**任何人**的回复均可命中
            （如群协作场景：" anyone 输入「开始」即开始"）；默认 False 仅等待原回复者
        :param cmdpass: 是否跳过命令匹配的三态（None=跟随全局配置，默认不跳过——
            等待期间命中已注册命令的消息放行给命令分发器执行，等待继续挂起；
            True=跳过命令匹配，等待期间消息一律作为回复消费）
        :return: 用户回复的事件数据，如果超时则返回None

        {!--< tips >!--}
        等待期间归属模块被卸载 / 适配器关闭 / 同会话被新的等待或租约取代 /
        回复者权限被撤销时，等待立即终止并返回 None（底层为
        :class:`~ErisPulse.Core.Event.interaction.InteractionCancelled`）。
        {!--< /tips >!--}
        """
        platform = event.get("platform")

        # 使用会话类型管理模块获取发送类型和目标ID
        send_type, target_id = get_send_type_and_target_id(event, platform)

        # 发送提示消息（如果提供）
        if prompt and platform:
            try:
                adapter_instance = getattr(adapter, platform)
                bot_id = event.get("self", {}).get("account_id", "") or event.get("self", {}).get("user_id", "")
                send_dsl = adapter_instance.Send.To(send_type, target_id)
                if bot_id:
                    send_dsl = send_dsl.Using(bot_id)
                send_func = getattr(send_dsl, method, None)
                if send_func and callable(send_func):
                    result = send_func(prompt)
                    if inspect.isawaitable(result):
                        await result
                else:
                    result = send_dsl.Text(prompt)
                    if inspect.isawaitable(result):
                        await result
            except Exception as e:
                logger.warning(i18n.t("core.event.command.send_prompt_failed", error=e))

        # 创建等待 future 并注册到交互会话管理器
        # （owner 从 current_owner 上下文自动捕获；同会话已有等待时旧等待被取消）
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        entry = interaction.register(
            event,
            future,
            callback=callback,
            validator=validator,
            pattern=pattern,
            regex=regex,
            session_scope=session,
            cmdpass=cmdpass,
        )
        wait_key = entry.key

        try:
            # 等待回复或超时
            import time as _time

            _wait_t0 = _time.monotonic()
            try:
                result = await asyncio.wait_for(future, timeout=timeout)
            finally:
                _wait_elapsed = _time.monotonic() - _wait_t0
                # 如果当前在 handler / Task 内，记录本次等待供 slow-log 扣除；
                # 不在则跳过（handler_waits 为 None，说明是独立调用）。
                _acc = handler_waits.get()
                if _acc is not None:
                    _acc.append(
                        {
                            "owner": current_owner.get(),
                            "duration": _wait_elapsed,
                            "wait_key": wait_key,
                        }
                    )

            # 如果提供了回调函数，则执行
            if callback:
                if inspect.iscoroutinefunction(callback):
                    await callback(result)
                else:
                    callback(result)

            return result
        except asyncio.TimeoutError:
            logger.trace(i18n.t("core.command.wait_reply_timeout", key=wait_key, timeout=timeout))
            return None
        except InteractionCancelled as e:
            logger.trace(i18n.t("core.interaction.wait_cancelled", reason=e.reason, wait_key=wait_key))
            return None
        except Exception as e:
            logger.error(i18n.t("core.command.wait_reply_error", error=e))
            return None
        finally:
            # 无论成功、超时、异常还是 CancelledError，都确保清理等待条目
            # （命中 / 取消路径条目已被移除，此处仅兜底超时路径的残留）
            interaction.cancel(wait_key)

    async def _handle_message(self, event: dict[str, Any]):
        """
        处理消息事件中的命令

        {!--< internal-use >!--}
        内部使用的方法，用于从消息中解析并执行命令

        :param event: 消息事件数据
        """
        # 防御性归一化：确保 event 为 Event 实例，使 mark_processed 等方法可用
        from .wrapper import Conversation as _Conversation, Event as _Event  # noqa: I001

        if not isinstance(event, _Event):
            event = _Event(event)

        # 回复命中优先判定（在 _processed 检查之前）：
        # 交互等待是框架级的会话延续机制而非竞争处理器，即使消息已被其他
        # 高优先级处理器认领，也应先尝试完成对话（修复等待方被饿死的问题）。
        # 命中后事件被 mark_processed，下方检查自然短路；未命中则继续命令匹配。
        if event.get("type", "") == "message":
            # 对话检查点自动恢复优先于一切：重启后首条命中消息续接挂起的对话
            try:
                if await _Conversation.try_auto_resume(event):
                    return
            except Exception:
                pass
            if await interaction.resolve(event):
                return

        # 检查是否已经被其他处理器标记为已处理
        if event.get("_processed"):
            logger.trace(
                i18n.t(
                    "core.command.skip_processed",
                    platform=event.get("platform", UNKNOWN_PLATFORM),
                    user_id=event.get("user_id", ""),
                )
            )
            return

        # 检查是否为文本消息
        event_type = event.get("type", "")
        if event_type != "message":
            logger.trace(
                i18n.t(
                    "core.command.skip_non_message",
                    event_type=event_type,
                    platform=event.get("platform", UNKNOWN_PLATFORM),
                )
            )
            return

        async def _process_text_for_command(event: "Event", text: str) -> bool:
            """
            处理文本内容，尝试匹配并执行命令

            {!--< internal-use >!--}
            内部使用的方法，用于处理文本内容并尝试执行命令

            :param event: 消息事件数据
            :param text: 要处理的文本内容
            :return: 是否成功执行命令
            """
            if not text:
                return False

            # 处理大小写敏感性
            check_text = text if self.case_sensitive else text.lower()
            prefixes = self._prefixes if self.case_sensitive else [p.lower() for p in self._prefixes]

            # 检查前缀，找出匹配的前缀（支持多个前缀）
            matched_prefix = None
            for prefix in prefixes:
                has_prefix = check_text.startswith(prefix)
                has_space_prefix = self.allow_space_prefix and check_text.startswith(prefix + " ")
                if has_prefix or has_space_prefix:
                    matched_prefix = prefix
                    break

            if matched_prefix is None:
                logger.trace(
                    i18n.t(
                        "core.command.prefix_not_matched",
                        platform=event.get("platform", UNKNOWN_PLATFORM),
                        user_id=event.get("user_id", ""),
                    )
                )
                return False

            # 检查是否必须@机器人
            if self.must_at_bot:
                detail_type = infer_receive_type(event)
                # 一对一场景（private或user）不需要检查@
                if detail_type not in (DETAIL_TYPE_PRIVATE, DETAIL_TYPE_USER):
                    message_segments = event.get("message", [])
                    self_id = event.get("self", {}).get("user_id")

                    has_mention = False
                    for segment in message_segments:
                        if segment.get("type") == "mention" and segment.get("data", {}).get("user_id") == self_id:
                            has_mention = True
                            break

                    if not has_mention:
                        logger.trace(
                            i18n.t(
                                "core.command.must_at_bot_failed",
                                platform=event.get("platform", UNKNOWN_PLATFORM),
                                user_id=event.get("user_id", ""),
                            )
                        )
                        return False

            # 尝试执行命令
            return await self._try_execute_command(event, text, matched_prefix)

        # 从 message 列表和 alt_message 中提取文本内容
        message_segments = event.get("message", [])
        message_text = ""
        for segment in message_segments:
            if segment.get("type") == "text":
                message_text = segment.get("data", {}).get("text", "")
                break

        alt_message = event.get("alt_message", "")

        # 尝试使用 message 列表的内容
        if message_text:
            command_matched = await _process_text_for_command(event, message_text)
            if command_matched:
                return

        # 尝试使用 alt_message
        if alt_message and alt_message != message_text:
            command_matched = await _process_text_for_command(event, alt_message)
            if command_matched:
                return

        # 决策链：带前缀的文本未命中任何注册命令（或非命令文本）——放行给消息处理器
        trace_step("dispatch", "passed", "core.trace.passed_to_message")
        # 如果都没有匹配，检查是否是等待回复的消息
        await self._check_pending_reply(event)
        return

    def _is_command_text(self, text: str) -> bool:
        """
        判定文本是否形如一条已注册命令（前缀 + 命令名/别名命中），不执行命令

        供交互等待（wait_reply）的命令穿透判定复用——等待期间命中命令的
        消息放行给命令分发器执行。判定口径与 :meth:`_try_execute_command`
        的匹配逻辑一致（前缀 / 大小写归一 / 子命令最长前缀匹配）。

        :param text: 待判定的消息文本
        :return: 是否形如已注册命令

        {!--< internal-use >!--}
        内部使用的方法
        {!--< /internal-use >!--}
        """
        if not text:
            return False

        check_text = text if self.case_sensitive else text.lower()
        prefixes = self._prefixes if self.case_sensitive else [p.lower() for p in self._prefixes]

        matched_prefix = None
        for prefix in prefixes:
            has_prefix = check_text.startswith(prefix)
            has_space_prefix = self.allow_space_prefix and check_text.startswith(prefix + " ")
            if has_prefix or has_space_prefix:
                matched_prefix = prefix
                break
        if matched_prefix is None:
            return False

        command_text = text[len(matched_prefix) :].strip()
        raw_parts = command_text.split()
        if not raw_parts:
            return False

        parts = raw_parts if self.case_sensitive else [part.lower() for part in raw_parts]
        cmd_name, _actual, _matched = self._resolve_command_tokens(parts)
        return cmd_name is not None

    async def _try_execute_command(self, event: "Event", original_text: str, prefix: str) -> bool:
        """
        尝试执行命令

        {!--< internal-use >!--}
        内部使用的方法，用于尝试解析和执行命令

        :param event: 消息事件数据
        :param original_text: 原始文本内容（命令名匹配时按配置做大小写归一，参数保留原文）
        :param prefix: 已匹配的命令前缀（可能已转换为小写）
        :return: 是否成功执行命令
        """
        # 解析命令和参数：参数与 raw 载荷保留用户原始大小写（取自 original_text，
        # 前缀为配置字面量、在大小写归一前后长度一致），仅命令名匹配候选做归一
        command_text = original_text[len(prefix) :].strip()
        raw_parts = command_text.split()
        if not raw_parts:
            return False

        # 处理大小写敏感性：候选名归一化用于匹配，参数列表保留原始形式
        parts = raw_parts if self.case_sensitive else [part.lower() for part in raw_parts]

        # 最长前缀匹配：命令名支持空格分隔的子命令形式（如 "admin add"），
        # 从最长候选逐级降级尝试；仅注册过单 token 命令时首轮即命中，
        # 开销与原先一致（/admin add x 同时注册了 admin 时优先命中子命令）
        cmd_name, actual_cmd_name, matched = self._resolve_command_tokens(parts)
        if cmd_name is None:
            # 决策链：有命令前缀但未命中任何注册命令（方向五：给出拼写建议）
            import difflib

            candidates = {**self.commands, **self.aliases}
            suggestion = (
                difflib.get_close_matches(parts[0], candidates, n=1, cutoff=0.6) or [None]
            )[0]
            trace_step(
                "command_match",
                "missed",
                "core.trace.command_not_found",
                text=f"{prefix}{raw_parts[0]}",
                suggestion=suggestion or "",
            )
            return False
        args = raw_parts[matched:]

        # 命中即认领：文本已解析为一条注册命令，无论后续作用域 / ACL /
        # 主人 / 权限判定结果如何，都不再漏给低优先级消息处理器——
        # 消除"命令被拒后 on_message 又响应一次"的双重响应歧义
        # （scope 拒绝仍保持静默不回复；ErisPulse.event.command.block=false
        #   可放行阻断，供日志 / 审计观察者继续看到）
        event.mark_processed(claim=True, stop=self.block)
        trace_step(
            "command_match",
            "ok",
            "core.trace.command_matched",
            command=actual_cmd_name,
        )

        logger.trace(
            i18n.t(
                "core.command.parsed",
                cmd_name=actual_cmd_name,
                args=args,
                platform=event.get("platform", UNKNOWN_PLATFORM),
                user_id=event.get("user_id", ""),
            )
        )

        # 查找命令处理器
        if actual_cmd_name in self.commands:
            logger.trace(
                i18n.t(
                    "core.command.matched",
                    cmd_name=actual_cmd_name,
                    alias=cmd_name if actual_cmd_name != cmd_name else "",
                    platform=event.get("platform", UNKNOWN_PLATFORM),
                    user_id=event.get("user_id", ""),
                )
            )
            cmd_info = self.commands[actual_cmd_name]
            handler = cmd_info["func"]

            # 作用域检查：模块未对该 Bot / 会话 / 平台启用时静默忽略（不回复、不认领）
            cmd_owner = cmd_info.get("owner")
            if cmd_owner:
                from ..scope import scope

                if not scope.is_allowed(
                    event.get("platform", UNKNOWN_PLATFORM),
                    event.get_self_account_id() or None,
                    cmd_owner,
                    scope.session_id_from_event(event) or None,
                ):
                    logger.trace(i18n.t("core.scope.denied", module=cmd_owner))
                    trace_step(
                        "scope",
                        "rejected",
                        "core.trace.scope_denied",
                        command=actual_cmd_name,
                        module=cmd_owner,
                    )
                    return False

            # 命令用户 ACL（event.overrides.acl）：命令名支持 glob
            # deny 命中 / allow 白名单未命中 / 严格模式无 ACL → 拒绝；
            # 否则（无 ACL 且默认放行）继续走开发者默认权限链
            _allowed = overrides.acl.is_allowed(
                actual_cmd_name,
                event.get("platform", UNKNOWN_PLATFORM),
                event.get("user_id", ""),
            )
            if _allowed is False:
                trace_step(
                    "acl",
                    "rejected",
                    "core.trace.acl_denied",
                    command=actual_cmd_name,
                    user_id=event.get("user_id", ""),
                )
                logger.trace(
                    i18n.t(
                        "core.command.acl_denied",
                        cmd_name=actual_cmd_name,
                        user_id=(f"{event.get('platform', UNKNOWN_PLATFORM)}:{event.get('user_id', '')}"),
                    )
                )
                await self._send_permission_denied(event)
                return False

            # 命令实现参数覆写（event.overrides.command）：覆盖 master / hidden / aliases / prefix 等
            # 覆写键 master 由 overrides.command.apply 统一映射到存储键 must_master（用户优先）
            # 注意：禁用不通过参数覆写，统一走 ACL deny（event.overrides.acl）
            _effective = cmd_info
            if cmd_owner:
                _effective = overrides.command.apply(cmd_owner, actual_cmd_name, cmd_info)

            # 检查框架主人权限（must_master）
            if _effective.get("must_master"):
                from ..master import master

                if not master.is_master(event):
                    trace_step(
                        "master",
                        "rejected",
                        "core.trace.master_denied",
                        command=actual_cmd_name,
                    )
                    logger.trace(
                        i18n.t(
                            "core.command.master_denied",
                            cmd_name=actual_cmd_name,
                            user_id=event.get("user_id", ""),
                            platform=event.get("platform", UNKNOWN_PLATFORM),
                        )
                    )
                    await self._send_permission_denied(event)
                    return False

            # 检查权限：子命令未声明权限时继承最近声明了权限的祖先命令
            # （如 /admin 声明权限后，/admin add 等子命令自动受同一权限保护）
            permission_func = (
                _effective.get("permission")
                or self.permissions.get(actual_cmd_name)
                or self._inherited_permission(actual_cmd_name)
            )
            if permission_func:
                try:
                    has_permission = (
                        permission_func(event)
                        if not inspect.iscoroutinefunction(permission_func)
                        else await permission_func(event)
                    )
                    if not has_permission:
                        logger.trace(
                            i18n.t(
                                "core.command.permission_denied",
                                cmd_name=actual_cmd_name,
                                user_id=event.get("user_id", ""),
                                platform=event.get("platform", UNKNOWN_PLATFORM),
                            )
                        )
                        trace_step(
                            "permission",
                            "rejected",
                            "core.trace.permission_denied",
                            command=actual_cmd_name,
                        )
                        await self._send_permission_denied(event)
                        return False
                except Exception as e:
                    logger.error(i18n.t("core.command.permission_check_error", error=e))
                    trace_step(
                        "permission",
                        "rejected",
                        "core.trace.permission_error",
                        command=actual_cmd_name,
                        error=str(e),
                    )
                    await self._send_permission_denied(event)
                    return False

            # 添加命令相关信息到事件（合并覆写后的有效参数）
            # owner：注册该命令的模块（懒激活占位命令即目标模块），
            # 供事件分发层的慢日志等归因到具体业务模块
            command_info = {
                "name": actual_cmd_name,
                "main_name": cmd_info["main_name"],
                "args": args,
                "raw": command_text,
                "help": _effective.get("help", cmd_info.get("help")),
                "usage": _effective.get("usage", cmd_info.get("usage")),
                "group": _effective.get("group", cmd_info.get("group")),
                "hidden": _effective.get("hidden", cmd_info.get("hidden", False)),
                "owner": cmd_info.get("owner"),
            }

            event["command"] = command_info

            # 认领已在命令命中时完成（见上方 mark_processed），
            # 此处直接进入权限钩子与执行阶段

            # 钩子: 命令匹配（后台发射，不阻塞命令分发）
            from ..lifecycle import lifecycle

            lifecycle.fire(
                "command.matched",
                {
                    "command": actual_cmd_name,
                    "args": args,
                    "platform": event.get("platform", UNKNOWN_PLATFORM),
                    "user_id": event.get("user_id", ""),
                },
            )

            # 声明式参数/选项解析（args= / options=）：位于全部权限检查之后——
            # 无权限用户不会触发解析；解析失败自动回复本地化错误与用法，
            # 命令仍保持已认领状态（不漏给低优先级消息处理器）
            kwargs: dict[str, Any] = {}
            if _effective.get("args_spec") or _effective.get("options_spec"):
                try:
                    kwargs = bind_command_arguments(
                        args, _effective.get("args_spec"), _effective.get("options_spec")
                    )
                except CommandArgsError as e:
                    error_text = str(e)
                    trace_step(
                        "args",
                        "failed",
                        "core.trace.args_failed",
                        command=actual_cmd_name,
                        error=error_text,
                    )
                    usage_line = i18n.t(
                        "core.command.args.usage",
                        usage=self._usage_line(actual_cmd_name, _effective),
                    )
                    logger.trace(
                        i18n.t(
                            "core.command.args_parse_failed",
                            cmd_name=actual_cmd_name,
                            error=error_text,
                            platform=event.get("platform", UNKNOWN_PLATFORM),
                            user_id=event.get("user_id", ""),
                        )
                    )
                    await self._send_args_error(event, f"{error_text}\n{usage_line}")
                    # 钩子: 命令执行失败（参数错误，后台发射）
                    from ..lifecycle import lifecycle

                    lifecycle.fire(
                        "command.executed",
                        {
                            "command": actual_cmd_name,
                            "args": args,
                            "platform": event.get("platform", UNKNOWN_PLATFORM),
                            "user_id": event.get("user_id", ""),
                            "success": False,
                            "error": error_text,
                        },
                    )
                    return True

            # 治理判定（cooldown / rate_limit / usage，EPRFC-2026-001 方向七）：
            # 位于全部权限检查与参数解析之后——无权限用户不触发计时，
            # 参数错误不消耗。命中默认静默丢弃（对称于作用域静默；声明了
            # *_reply= 时回复）；命令已在命中时认领，保持不漏给低优先级
            # 消息处理器。判定实现见 GovernanceGate（Core/Event/governance.py）
            if await self._gate.check_cooldown(
                cmd_info["main_name"], actual_cmd_name, _effective, event, self._send_args_error
            ):
                return True
            if await self._gate.check_rate_limit(
                cmd_info["main_name"], actual_cmd_name, _effective, event, self._send_args_error
            ):
                return True
            if await self._gate.check_usage(
                cmd_info["main_name"], actual_cmd_name, _effective, event, self._send_args_error
            ):
                return True

            # 废弃声明（deprecated=）：调用时自动回复废弃文案；默认继续执行，
            # deprecated_reject=True 时拒绝执行（命令已认领，不漏给消息处理器）
            if _effective.get("deprecated"):
                _dep_text = _effective["deprecated"]
                await self._send_args_error(event, _dep_text)
                if _effective.get("deprecated_reject"):
                    logger.trace(
                        i18n.t(
                            "core.command.deprecated_rejected",
                            cmd_name=actual_cmd_name,
                            platform=event.get("platform", UNKNOWN_PLATFORM),
                            user_id=event.get("user_id", ""),
                        )
                    )
                    trace_step(
                        "deprecated",
                        "rejected",
                        "core.trace.deprecated_rejected",
                        command=actual_cmd_name,
                    )
                    # 钩子: 命令执行失败（废弃拒绝，后台发射）
                    from ..lifecycle import lifecycle

                    lifecycle.fire(
                        "command.executed",
                        {
                            "command": actual_cmd_name,
                            "args": args,
                            "platform": event.get("platform", UNKNOWN_PLATFORM),
                            "user_id": event.get("user_id", ""),
                            "success": False,
                            "error": "deprecated",
                        },
                    )
                    return True
                trace_step(
                    "deprecated",
                    "notice",
                    "core.trace.deprecated_notice",
                    command=actual_cmd_name,
                )

            try:
                # 把注册时记录的 owner 注入上下文，让用户 handler 内部的
                # wait_reply / 日志等能正确归因到具体业务模块。
                logger.trace(
                    i18n.t(
                        "core.command.executing",
                        cmd_name=actual_cmd_name,
                        handler=handler.__qualname__,
                        platform=event.get("platform", UNKNOWN_PLATFORM),
                        user_id=event.get("user_id", ""),
                    )
                )
                cmd_owner = cmd_info.get("owner")
                _owner_token = current_owner.set(cmd_owner) if cmd_owner else None
                try:
                    # 依赖注入解析（Depends）：上下文为 Event；依赖异常走统一错误路径
                    _depends = _effective.get("depends")
                    if _depends:
                        dep_kwargs = await resolve_depends(_depends, event)
                        kwargs = {**kwargs, **dep_kwargs}
                    if inspect.iscoroutinefunction(handler):
                        await handler(event, **kwargs)
                    else:
                        handler(event, **kwargs)
                finally:
                    if _owner_token is not None:
                        current_owner.reset(_owner_token)

                trace_step("execute", "executed", "core.trace.executed", command=actual_cmd_name)
                # 钩子: 命令执行完成（后台发射）
                from ..lifecycle import lifecycle

                lifecycle.fire(
                    "command.executed",
                    {
                        "command": actual_cmd_name,
                        "args": args,
                        "platform": event.get("platform", UNKNOWN_PLATFORM),
                        "user_id": event.get("user_id", ""),
                        "success": True,
                    },
                )
            except Exception as e:
                logger.error(i18n.t("core.command.exec_error", error=e))
                trace_step(
                    "execute",
                    "failed",
                    "core.trace.execute_failed",
                    command=actual_cmd_name,
                    error=str(e),
                )
                await self._send_command_error(event, str(e))

                # 钩子: 命令执行失败（后台发射）
                from ..lifecycle import lifecycle

                lifecycle.fire(
                    "command.executed",
                    {
                        "command": actual_cmd_name,
                        "args": args,
                        "platform": event.get("platform", UNKNOWN_PLATFORM),
                        "user_id": event.get("user_id", ""),
                        "success": False,
                        "error": str(e),
                    },
                )

            return True

        logger.trace(
            i18n.t(
                "core.command.not_registered",
                cmd_name=actual_cmd_name,
                platform=event.get("platform", UNKNOWN_PLATFORM),
                user_id=event.get("user_id", ""),
            )
        )
        return False

    async def _check_pending_reply(self, event: "Event"):
        """
        检查是否是等待回复的消息

        判定链（会话键命中 → pattern/regex 过滤 → validator 校验 →
        权限复查 → 唤醒等待方并认领事件）委托交互会话管理器
        :meth:`~ErisPulse.Core.Event.interaction.InteractionManager.resolve`。

        :param event: 消息事件数据
        """
        await interaction.resolve(event)

    async def _send_event_text(self, event: dict[str, Any], text: str, *, error_log_key: str) -> None:
        """
        {!--< internal-use >!--}
        向事件来源会话发送文本（各 _send_* 提示的公共发送通道）

        :param event: 事件数据
        :param text: 已本地化的待发送文本
        :param error_log_key: 发送失败时的错误日志 i18n 键
        """
        try:
            platform = event.get("platform")

            # 使用会话类型管理模块获取发送类型和目标ID
            send_type, target_id = get_send_type_and_target_id(event, platform)

            if platform and hasattr(adapter, platform):
                adapter_instance = getattr(adapter, platform)
                bot_id = event.get("self", {}).get("account_id", "") or event.get("self", {}).get("user_id", "")
                send_dsl = adapter_instance.Send.To(send_type, target_id)
                if bot_id:
                    send_dsl = send_dsl.Using(bot_id)
                await send_dsl.Text(text)
        except Exception as e:
            logger.error(i18n.t(error_log_key, error=e))

    async def _send_permission_denied(self, event: dict[str, Any]):
        """
        发送权限拒绝消息

        {!--< internal-use >!--}
        内部使用的方法

        :param event: 事件数据
        """
        await self._send_event_text(
            event,
            i18n.t("core.event.command.permission_denied"),
            error_log_key="core.event.command.send_permission_denied_failed",
        )

    async def _send_command_error(self, event: dict[str, Any], error: str):
        """
        发送命令错误消息

        {!--< internal-use >!--}
        内部使用的方法

        :param event: 事件数据
        :param error: 错误信息
        """
        await self._send_event_text(
            event,
            i18n.t("core.event.command.execution_failed", error=error),
            error_log_key="core.event.command.send_error_failed",
        )

    async def _send_args_error(self, event: dict[str, Any], text: str):
        """
        发送命令参数错误消息（args= / options= 解析失败时的本地化提示 + 用法）

        {!--< internal-use >!--}
        内部使用的方法

        :param event: 事件数据
        :param text: 已本地化的错误文本（含用法行）
        """
        await self._send_event_text(
            event,
            text,
            error_log_key="core.event.command.send_error_failed",
        )

    @staticmethod
    def _cooldown_scope_key(kind: str, event: "Event") -> str:
        """
        {!--< internal-use >!--}
        计算冷却作用域键（复用 ``platform:bot:目标`` 会话键体系）

        :param kind: 粒度（user / session / global，注册期已校验）
        :param event: 事件数据
        :return: 作用域键字符串
        """
        return cooldown_scope_key(kind, event)

    def _usage_line(self, cmd_name: str, effective: dict, display_prefix: str | None = None) -> str:
        """
        {!--< internal-use >!--}
        计算命令的生效 usage 行（帮助展示与参数错误提示共用）

        优先取开发者声明的 ``usage=``（含覆写）；未声明且注册了 ``args=`` /
        ``options=`` 时按声明自动生成；否则回退 ``{前缀}{命令名}``。

        :param cmd_name: 命令名
        :param effective: 合并覆写后的命令生效参数
        :param display_prefix: 显示用前缀（None 时取配置前缀首个）
        :return: usage 字符串
        """
        usage = effective.get("usage")
        if usage:
            return usage
        if display_prefix is None:
            display_prefix = self.prefix[0] if isinstance(self.prefix, list) else self.prefix
        tail = format_usage(effective.get("args_spec"), effective.get("options_spec"))
        return f"{display_prefix}{cmd_name} {tail}".rstrip() if tail else f"{display_prefix}{cmd_name}"

    def bind_message_handler(self, handler: BaseEventHandler) -> None:
        """
        {!--< internal-use >!--}
        绑定到共享的消息事件处理器

        将命令分发器 _handle_message 注册到共享的 BaseEventHandler 中，
        使命令处理和通用消息处理共享同一个优先级队列。

        :param handler: MessageHandler 持有的 BaseEventHandler 实例
        """
        self._bound_handler = handler
        self._register_dispatcher()

    def _register_dispatcher(self) -> None:
        """
        {!--< internal-use >!--}
        将命令分发器注册到共享 handler（如尚未注册）
        """
        if self._bound_handler is not None and not self._dispatcher_registered:
            # 命令分发器为框架级处理器：豁免作用域过滤，
            # 具体命令在 _try_execute_command 中按 owner 逐个判定
            self._bound_handler.register(
                self._handle_message,
                priority=DEFAULT_COMMAND_DISPATCHER_PRIORITY,
                scope_exempt=True,
            )
            self._dispatcher_registered = True

    def _clear_commands(self):
        """
        {!--< internal-use >!--}
        清除所有已注册的命令，并从共享 handler 中注销命令分发器

        :return: 被清除的命令数量
        """
        count = len(self.commands)
        self.commands.clear()
        self.aliases.clear()
        self.groups.clear()
        self.permissions.clear()
        self._gate.clear_all()
        self._recompute_max_name_tokens()
        interaction.clear()
        # 从共享 handler 中注销命令分发器（不清除其他 handler 的消息处理器）
        if self._bound_handler is not None and self._dispatcher_registered:
            self._bound_handler.unregister(self._handle_message)
            self._dispatcher_registered = False
        return count

    def get_command(
        self,
        name: str,
        *,
        event: Any = None,
        platform: str | None = None,
        bot_id: str | None = None,
        session_id: str | None = None,
    ) -> dict | None:
        """
        获取命令信息（返回合并覆写系统命令参数后的**生效参数**）

        传入作用域上下文（``event`` 或 ``platform`` / ``bot_id`` / ``session_id``
        任一）时，命令归属模块在当前会话不可用则返回 ``None``（与分发静默语义一致）。

        :param name: 命令名称（支持别名）
        :param event: 可选，事件上下文（Event 或 dict）
        :param platform: 可选，平台名（与 event 二选一或叠加，显式参数优先）
        :param bot_id: 可选，Bot 标识
        :param session_id: 可选，会话标识
        :return: 合并覆盖后的命令信息字典；不存在或该会话不可用返回 None

        :example:
        >>> command.get_command("admin")
        >>> command.get_command("admin", event=event)   # 会话不可用时返回 None
        """
        # 命令名优先于别名（与分发解析一致）
        actual_name = name if name in self.commands else self.aliases.get(name, name)
        info = self.commands.get(actual_name)
        if info is None:
            return None
        ctx = self._resolve_query_context(event, platform, bot_id, session_id)
        if ctx and self._owner_blocked(info, ctx):
            return None
        return self._effective_info(actual_name, info)

    def get_commands(
        self,
        *,
        event: Any = None,
        platform: str | None = None,
        bot_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, dict]:
        """
        获取所有命令

        传入作用域上下文时，过滤掉当前会话不可用模块的命令（值为原始注册信息，
        需要覆盖合并后的生效参数请用 :meth:`get_command` / :meth:`get_visible_commands`）；
        不传上下文时返回完整注册表（与原行为一致）。

        :param event: 可选，事件上下文（Event 或 dict）
        :param platform: 可选，平台名
        :param bot_id: 可选，Bot 标识
        :param session_id: 可选，会话标识
        :return: 命令信息字典
        """
        ctx = self._resolve_query_context(event, platform, bot_id, session_id)
        if ctx is None:
            return self.commands
        filtered: dict[str, dict] = {}
        for cmd_name, info in self.commands.items():
            if self._owner_blocked(info, ctx):
                continue
            filtered[cmd_name] = info
        return filtered

    def get_group_commands(
        self,
        group: str,
        *,
        event: Any = None,
        platform: str | None = None,
        bot_id: str | None = None,
        session_id: str | None = None,
    ) -> list[str]:
        """
        获取命令组中的命令

        传入作用域上下文时，过滤掉当前会话不可用模块的命令。

        :param group: 命令组名称
        :param event: 可选，事件上下文（Event 或 dict）
        :param platform: 可选，平台名
        :param bot_id: 可选，Bot 标识
        :param session_id: 可选，会话标识
        :return: 命令名称列表
        """
        names = self.groups.get(group, [])
        ctx = self._resolve_query_context(event, platform, bot_id, session_id)
        if ctx is None:
            return names
        return [
            cmd_name
            for cmd_name in names
            if (info := self.commands.get(cmd_name)) is not None
            and not self._owner_blocked(info, ctx)
        ]

    def get_visible_commands(
        self,
        *,
        event: Any = None,
        platform: str | None = None,
        bot_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, dict]:
        """
        获取所有可见命令（非隐藏命令）

        可见性判定读取覆写系统命令参数（``event.overrides.command.<module>.<command>.hidden``）：
        用户显式覆盖 ``hidden`` 后，帮助列表随之变化（用户优先）。
        传入作用域上下文（``event`` 或 ``platform`` / ``bot_id`` / ``session_id``
        任一）时，额外按模块维度过滤该会话不可用模块的命令（与分发静默语义一致）。

        :param event: 可选，事件上下文（Event 或 dict）
        :param platform: 可选，平台名（与 event 叠加时显式参数优先）
        :param bot_id: 可选，Bot 标识
        :param session_id: 可选，会话标识
        :return: 可见命令信息字典（值为合并覆盖后的生效参数）
        """
        ctx = self._resolve_query_context(event, platform, bot_id, session_id)
        visible: dict[str, dict] = {}
        for name, info in self.commands.items():
            if name != info["main_name"]:
                continue
            if ctx and self._owner_blocked(info, ctx):
                continue
            effective = self._effective_info(name, info)
            if not effective.get("hidden", False):
                visible[name] = effective
        return visible

    def _context_from_event(self, event: Any) -> dict[str, str | None]:
        """
        {!--< internal-use >!--}
        从事件提取作用域查询上下文（platform / bot / session）
        """
        from ..scope import scope as _scope_mod

        return {
            "platform": event.get("platform") or "",
            "bot_id": _scope_mod.bot_id_from_event(event) or None,
            "session_id": _scope_mod.session_id_from_event(event) or None,
        }

    def _resolve_query_context(
        self,
        event: Any = None,
        platform: str | None = None,
        bot_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, str | None] | None:
        """
        {!--< internal-use >!--}
        归一查询上下文：event 与显式关键字参数合并（显式参数优先）

        :return: {"platform": str, "bot_id": str|None, "session_id": str|None}；
                 完全未提供任何上下文时返回 None（不做会话过滤）
        """
        if event is not None:
            ctx = self._context_from_event(event)
        elif platform is None and bot_id is None and session_id is None:
            return None
        else:
            ctx = {"platform": "", "bot_id": None, "session_id": None}
        if platform is not None:
            ctx["platform"] = platform
        if bot_id is not None:
            ctx["bot_id"] = bot_id
        if session_id is not None:
            ctx["session_id"] = session_id
        return {"platform": ctx.get("platform") or "", "bot_id": ctx.get("bot_id"), "session_id": ctx.get("session_id")}

    def _effective_info(self, name: str, info: dict) -> dict:
        """
        {!--< internal-use >!--}
        合并实现参数覆盖后的命令生效参数（帮助渲染与可见性判定用）

        :param name: 命令主名
        :param info: 注册时的命令信息字典
        :return: 与执行路径同源的覆盖合并结果（无覆盖时原样返回）
        """
        owner = info.get("owner")
        if not owner:
            return info
        return overrides.command.apply(owner, name, info)

    def help(
        self,
        command_name: str | None = None,
        show_hidden: bool = False,
        event: Any = None,
    ) -> str:
        """
        生成帮助信息

        传入 ``event`` 时按作用域对输出做会话感知调整：① 模块维度——
        该会话（platform / bot / session）下被作用域禁用的模块，其命令不再列出
        （与分发静默语义一致）；② 覆盖——帮助文本 / usage / 可见性读取
        ``event.overrides.command`` 覆写值（用户优先）。
        子命令（空格分隔多 token 命令名）在其可见父命令下缩进展示。

        :param command_name: 命令名称，如果为None则生成所有命令的帮助
        :param show_hidden: 是否显示隐藏命令
        :param event: 可选，事件上下文（Event 或 dict）。提供时按作用域过滤
                      当前会话不可用模块的命令；None 时不过滤（保持原行为）
        :return: 帮助信息字符串

        :example:
        >>> # 全量帮助（不感知会话）
        >>> command.help()
        >>> # 会话感知帮助：只列出当前会话可用的命令
        >>> command.help(event=event)
        """
        # 用于显示的前缀：单个时保持原始字符串，多个时取第一个
        display_prefix = self.prefix[0] if isinstance(self.prefix, list) else self.prefix

        # 归一作用域查询上下文（event 驱动），用于模块维度过滤
        ctx = self._resolve_query_context(event=event)

        if command_name:
            # 会话不可用（ctx 过滤）或未注册 → 统一按"未注册"处理（静默语义一致）
            effective = self.get_command(command_name, event=event)
            if effective:
                help_text = effective.get("help", i18n.t("core.event.command.no_help"))
                # 废弃命令：帮助文本前加废弃标记与文案
                if effective.get("deprecated"):
                    help_text = (
                        i18n.t("core.event.command.deprecated_mark")
                        + " "
                        + help_text
                        + "\n"
                        + i18n.t(
                            "core.event.command.help_deprecated",
                            text=effective["deprecated"],
                        )
                    )
                # usage 优先取声明值；注册了 args=/options= 且未声明 usage 时自动生成
                usage = self._usage_line(command_name, effective, display_prefix)
                return i18n.t(
                    "core.event.command.help_command",
                    command_name=command_name,
                    usage=usage,
                    help_text=help_text,
                )
            return i18n.t("core.event.command.not_found", command_name=command_name)
        # 生成所有命令的帮助
        commands_to_show = (
            self.get_visible_commands(event=event)
            if not show_hidden
            else {
                name: self._effective_info(name, info)
                for name, info in self.commands.items()
                if name == info["main_name"]
                and not (ctx and self._owner_blocked(info, ctx))
            }
        )

        if not commands_to_show:
            return i18n.t("core.event.command.no_commands")

        help_lines = [i18n.t("core.event.command.available_commands")]

        # 子命令（空格分隔多 token 命令名）挂到最近的可见祖先下先序展示：
        # 父命令始终位于子命令之前（与注册顺序无关），兄弟命令保持注册顺序
        _children: dict[str | None, list[str]] = {}
        for _name in commands_to_show:
            _tokens = _name.split()
            _anchor = None
            while len(_tokens) > 1:
                _tokens.pop()
                if " ".join(_tokens) in commands_to_show:
                    _anchor = " ".join(_tokens)
                    break
            _children.setdefault(_anchor, []).append(_name)

        def _emit_tree(anchor: str | None, depth: int) -> None:
            for _name in _children.get(anchor, []):
                _help_text = commands_to_show[_name].get(
                    "help", i18n.t("core.event.command.no_help_item")
                )
                if commands_to_show[_name].get("deprecated"):
                    _help_text = i18n.t("core.event.command.deprecated_mark") + " " + _help_text
                if depth:
                    help_lines.append(
                        "  " * (depth + 1)
                        + i18n.t(
                            "core.event.command.list_item_child",
                            prefix=display_prefix,
                            cmd_name=_name,
                            help_text=_help_text,
                        )
                    )
                else:
                    help_lines.append(
                        i18n.t(
                            "core.event.command.list_item",
                            prefix=display_prefix,
                            cmd_name=_name,
                            help_text=_help_text,
                        )
                    )
                _emit_tree(_name, depth + 1)

        _emit_tree(None, 0)
        return "\n".join(help_lines)

    def _owner_blocked(self, info: dict, ctx: dict[str, str | None]) -> bool:
        """
        {!--< internal-use >!--}
        判断命令归属模块在给定作用域上下文下是否被模块维度禁用

        :param info: 命令信息字典
        :param ctx: {"platform": str, "bot_id": str|None, "session_id": str|None}
        :return: 是否被禁用（owner 为空视为框架层资源，恒不阻止）
        """
        owner = info.get("owner")
        if not owner:
            return False
        from ..scope import scope

        return not scope.is_allowed(ctx.get("platform") or "", ctx.get("bot_id"), owner, ctx.get("session_id"))


command: CommandHandler = CommandHandler()
