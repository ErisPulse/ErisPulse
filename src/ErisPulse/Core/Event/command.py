"""
ErisPulse 命令处理模块

提供基于装饰器的命令注册和处理功能

命令的**用户权限 ACL**（谁/谁不能执行）统一收敛到控制面 ``ErisPulse.scope.commands``
（运行时 ``scope.allow_user`` / ``scope.deny_user``，命令名支持 glob），
本模块不再单独维护权限配置。

{!--< tips >!--}
1. 支持命令别名和命令组
2. 支持命令权限控制（master / permission 函数 / 控制面 ACL）
3. 支持命令帮助系统
4. 支持等待用户回复交互
{!--< /tips >!--}
"""

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .wrapper import Event

from ...runtime import get_event_config
from ...runtime.context import current_owner, handler_waits
from .. import adapter, logger
from ..constants import (
    DEFAULT_COMMAND_ALLOW_SPACE_PREFIX,
    DEFAULT_COMMAND_CASE_SENSITIVE,
    DEFAULT_COMMAND_DISPATCHER_PRIORITY,
    DEFAULT_COMMAND_MUST_AT_BOT,
    DEFAULT_COMMAND_PREFIX,
    DEFAULT_SEND_METHOD,
    DEFAULT_WAIT_TIMEOUT_SECS,
    DETAIL_TYPE_PRIVATE,
    DETAIL_TYPE_USER,
    UNKNOWN_PLATFORM,
)
from ..i18n import i18n
from ..text_match import compile_text_matcher, extract_text
from .base import BaseEventHandler
from .session_type import get_send_type_and_target_id, infer_receive_type


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

        # 从配置读取命令解析参数（并订阅热更新）
        self._refresh_command_config()
        try:
            from ..lifecycle import lifecycle

            lifecycle.register("config.updated", self._on_config_updated)
            lifecycle.register("config.set", self._on_config_updated)
        except Exception:
            pass

        # 等待回复相关
        self._waiting_replies = {}  # 存储等待回复的用户信息

        # 共享的消息事件处理器引用（由 bind_message_handler() 设置）
        # 命令分发器 _handle_message 以高优先级注册在同一个队列中，
        # 确保命令 /xxx 始终优先于 on_message / on_group_message 触发
        self._bound_handler: BaseEventHandler | None = None
        self._dispatcher_registered: bool = False

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
        self._prefixes = (
            list(self.prefix) if isinstance(self.prefix, list) else [self.prefix]
        )
        self.case_sensitive = command_config.get(
            "case_sensitive", DEFAULT_COMMAND_CASE_SENSITIVE
        )
        self.allow_space_prefix = command_config.get(
            "allow_space_prefix", DEFAULT_COMMAND_ALLOW_SPACE_PREFIX
        )
        self.must_at_bot = command_config.get(
            "must_at_bot", DEFAULT_COMMAND_MUST_AT_BOT
        )

    def _on_config_updated(self, _data: dict) -> None:
        """配置变更回调：刷新命令解析参数，实现热更新"""
        self._refresh_command_config()

    # ==================== 命令权限 ACL（控制面 scope.commands） ====================

    @staticmethod
    def _scope() -> Any:
        """
        {!--< internal-use >!--}
        延迟获取控制面单例（避免模块初始化阶段的循环依赖）

        :return: scope 单例（ScopeManager）
        """
        from ..scope import scope

        return scope

    def allow_user(
        self, command_name: str, platform: str, user_id: str, persist: bool = True
    ) -> None:
        """
        将用户加入命令的 allow 名单（白名单非空时仅名单内用户可执行）

        委托给控制面 ``scope.allow_user``；命令名支持 glob。

        :param command_name: 命令名称（支持 glob / ``re:`` 正则）
        :param platform: 用户所属平台
        :param user_id: 用户 ID
        :param persist: 是否持久化到配置 (默认: True)

        :example:
        >>> command.allow_user("restart", "onebot11", "123456")
        """
        self._scope().allow_user(command_name, platform, user_id, persist=persist)

    def deny_user(
        self, command_name: str, platform: str, user_id: str, persist: bool = True
    ) -> None:
        """
        将用户加入命令的 deny 名单（deny 优先于 allow 与默认权限）

        委托给控制面 ``scope.deny_user``；命令名支持 glob。

        :param command_name: 命令名称（支持 glob / ``re:`` 正则）
        :param platform: 用户所属平台
        :param user_id: 用户 ID
        :param persist: 是否持久化到配置 (默认: True)

        :example:
        >>> command.deny_user("restart", "onebot11", "666")
        """
        self._scope().deny_user(command_name, platform, user_id, persist=persist)

    def remove_acl(self, command_name: str, persist: bool = True) -> bool:
        """
        清除命令的用户黑白名单（恢复开发者默认权限逻辑）

        委托给控制面 ``scope.remove_acl``；命令名支持 glob。

        :param command_name: 命令名称（支持 glob / ``re:`` 正则）
        :param persist: 是否持久化到配置 (默认: True)
        :return: 是否存在并被清除

        :example:
        >>> command.remove_acl("restart")
        True
        """
        return self._scope().remove_acl(command_name, persist=persist)

    def get_acl(self, command_name: str) -> dict[str, list[str]]:
        """
        查询命令当前的用户黑白名单

        委托给控制面 ``scope.get_acl``；命令名支持 glob。

        :param command_name: 命令名称（支持 glob / ``re:`` 正则）
        :return: {"allow": [...], "deny": [...]}（用户标识 "platform:user_id"）

        :example:
        >>> command.get_acl("restart")
        {'allow': ['onebot11:123456'], 'deny': []}
        """
        return self._scope().get_acl(command_name)

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
        :return: 装饰器函数
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

            # 添加别名
            alias_list = aliases or []
            if len(cmd_names) > 1:
                alias_list.extend(cmd_names[1:])

            # 注册命令
            for cmd_name in cmd_names:
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
                }

                # 注册别名映射（name列表中的额外名称）
                if cmd_name != main_name:
                    self.aliases[cmd_name] = main_name

                # 注册权限检查函数
                if permission and cmd_name not in self.permissions:
                    self.permissions[cmd_name] = permission

            # 注册aliases参数中的别名
            for alias in alias_list:
                if alias not in self.aliases:
                    self.aliases[alias] = main_name

            # 添加到命令组
            if group:
                if group not in self.groups:
                    self.groups[group] = []
                for cmd_name in cmd_names:
                    if cmd_name not in self.groups[group]:
                        self.groups[group].append(cmd_name)

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
            aliases_to_remove = [
                alias for alias, name in self.aliases.items() if name == main_name
            ]
            for alias in aliases_to_remove:
                del self.aliases[alias]

            # 从命令组中移除
            for group_commands in self.groups.values():
                if cmd_name in group_commands:
                    group_commands.remove(cmd_name)

            # 移除权限检查函数
            if cmd_name in self.permissions:
                del self.permissions[cmd_name]

            # 最后移除命令本身
            del self.commands[cmd_name]

        return result

    def unregister_by_owner(self, owner: str) -> int:
        """
        {!--< internal-use >!--}
        按归属者精确移除命令

        :param owner: 归属者（模块名）
        :return: 移除的命令数量
        """
        to_remove = [
            name for name, info in self.commands.items() if info.get("owner") == owner
        ]
        for cmd_name in to_remove:
            cmd_info = self.commands[cmd_name]
            main_name = cmd_info.get("main_name", cmd_name)

            self.aliases = {
                a: n
                for a, n in self.aliases.items()
                if not (n == main_name and a != main_name)
            }

            for group_cmds in self.groups.values():
                if cmd_name in group_cmds:
                    group_cmds.remove(cmd_name)

            self.permissions.pop(cmd_name, None)
            del self.commands[cmd_name]

        # 清理空命令组
        self.groups = {k: v for k, v in self.groups.items() if v}

        if to_remove:
            from ..logger import logger as _logger

            _logger.trace(
                i18n.t("core.command.cleaned", owner=owner, count=len(to_remove), commands=to_remove)
            )
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
        :return: 用户回复的事件数据，如果超时则返回None
        """
        platform = event.get("platform")
        user_id = event.get("user_id")

        # 使用会话类型管理模块获取发送类型和目标ID
        send_type, target_id = get_send_type_and_target_id(event, platform)

        # 发送提示消息（如果提供）
        if prompt and platform:
            try:
                adapter_instance = getattr(adapter, platform)
                bot_id = event.get("self", {}).get("account_id", "") or event.get(
                    "self", {}
                ).get("user_id", "")
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

        # 创建等待 future
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        # 存储等待信息
        bot_id = event.get("self", {}).get("account_id", "") or event.get(
            "self", {}
        ).get("user_id", "")
        wait_key = f"{platform}:{bot_id}:{user_id}:{target_id}"
        self._waiting_replies[wait_key] = {
            "future": future,
            "callback": callback,
            "validator": validator,
            "pattern": pattern,
            "regex": regex,
            "timestamp": loop.time(),
        }

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
        except Exception as e:
            logger.error(i18n.t("core.command.wait_reply_error", error=e))
            return None
        finally:
            # 无论成功、超时、异常还是 CancelledError，都确保清理等待条目
            self._waiting_replies.pop(wait_key, None)

    async def _handle_message(self, event: dict[str, Any]):
        """
        处理消息事件中的命令

        {!--< internal-use >!--}
        内部使用的方法，用于从消息中解析并执行命令

        :param event: 消息事件数据
        """
        # 防御性归一化：确保 event 为 Event 实例，使 mark_processed 等方法可用
        from .wrapper import Event as _Event

        if not isinstance(event, _Event):
            event = _Event(event)

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
            prefixes = (
                self._prefixes
                if self.case_sensitive
                else [p.lower() for p in self._prefixes]
            )

            # 检查前缀，找出匹配的前缀（支持多个前缀）
            matched_prefix = None
            for prefix in prefixes:
                has_prefix = check_text.startswith(prefix)
                has_space_prefix = self.allow_space_prefix and check_text.startswith(
                    prefix + " "
                )
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
                        if (
                            segment.get("type") == "mention"
                            and segment.get("data", {}).get("user_id") == self_id
                        ):
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
            return await self._try_execute_command(
                event, text, check_text, matched_prefix
            )

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

        # 如果都没有匹配，检查是否是等待回复的消息
        await self._check_pending_reply(event)
        return

    async def _try_execute_command(
        self, event: "Event", original_text: str, check_text: str, prefix: str
    ) -> bool:
        """
        尝试执行命令

        {!--< internal-use >!--}
        内部使用的方法，用于尝试解析和执行命令

        :param event: 消息事件数据
        :param original_text: 原始文本内容
        :param check_text: 用于检查的文本内容（可能已转换为小写）
        :param prefix: 已匹配的命令前缀（可能已转换为小写）
        :return: 是否成功执行命令
        """
        # 解析命令和参数
        command_text = check_text[len(prefix) :].strip()
        parts = command_text.split()
        if not parts:
            return False

        cmd_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # 处理大小写敏感性
        if not self.case_sensitive:
            cmd_name = cmd_name.lower()

        # 处理别名
        actual_cmd_name = self.aliases.get(cmd_name, cmd_name)

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
                    logger.trace(
                        i18n.t("core.scope.denied", module=cmd_owner)
                    )
                    return False

            # 命令权限 ACL（控制面 scope.commands）：命令名支持 glob
            # deny 命中 / allow 白名单未命中 / 严格模式无 ACL → 拒绝；
            # 否则（无 ACL 且默认放行）继续走开发者默认权限链
            _allowed = self._scope().is_command_allowed(
                actual_cmd_name,
                event.get("platform", UNKNOWN_PLATFORM),
                event.get("user_id", ""),
            )
            if _allowed is False:
                logger.trace(
                    i18n.t(
                        "core.command.acl_denied",
                        cmd_name=actual_cmd_name,
                        user_id=(
                            f"{event.get('platform', UNKNOWN_PLATFORM)}:"
                            f"{event.get('user_id', '')}"
                        ),
                    )
                )
                await self._send_permission_denied(event)
                return False

            # 控制面实现参数覆盖（scope.overrides）：覆盖 master / hidden / aliases / prefix 等
            # 注意：禁用不通过 overrides，统一走命令 deny（scope.commands）
            from ..scope import scope as _scope

            _effective = cmd_info
            if cmd_owner:
                _override = _scope.get_override(cmd_owner, actual_cmd_name)
                if _override:
                    _effective = dict(cmd_info)
                    _effective.update(_override)

            # 检查框架主人权限（must_master）
            if _effective.get("must_master"):
                from ..master import master

                if not master.is_master(event):
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

            # 检查权限
            permission_func = _effective.get("permission") or self.permissions.get(
                actual_cmd_name
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
                        await self._send_permission_denied(event)
                        return False
                except Exception as e:
                    logger.error(i18n.t("core.command.permission_check_error", error=e))
                    await self._send_permission_denied(event)
                    return False

            # 添加命令相关信息到事件（合并控制面覆盖后的有效参数）
            command_info = {
                "name": actual_cmd_name,
                "main_name": cmd_info["main_name"],
                "args": args,
                "raw": command_text,
                "help": _effective.get("help", cmd_info.get("help")),
                "usage": _effective.get("usage", cmd_info.get("usage")),
                "group": _effective.get("group", cmd_info.get("group")),
                "hidden": _effective.get("hidden", cmd_info.get("hidden", False)),
            }

            event["command"] = command_info

            # 标记事件已被处理（认领 + 阻断，阻止低优先级处理器再介入）
            event.mark_processed()

            # 钩子: 命令匹配
            from ..lifecycle import lifecycle

            await lifecycle.emit(
                "command.matched",
                {
                    "command": actual_cmd_name,
                    "args": args,
                    "platform": event.get("platform", UNKNOWN_PLATFORM),
                    "user_id": event.get("user_id", ""),
                },
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
                    if inspect.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                finally:
                    if _owner_token is not None:
                        current_owner.reset(_owner_token)

                # 钩子: 命令执行完成
                from ..lifecycle import lifecycle

                await lifecycle.emit(
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
                await self._send_command_error(event, str(e))

                # 钩子: 命令执行失败
                from ..lifecycle import lifecycle

                await lifecycle.emit(
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

        :param event: 消息事件数据
        """
        platform = event.get("platform")
        user_id = event.get("user_id")

        # 使用会话类型管理模块获取发送类型和目标ID
        _send_type, target_id = get_send_type_and_target_id(event, platform)

        bot_id = event.get("self", {}).get("account_id", "") or event.get(
            "self", {}
        ).get("user_id", "")
        wait_key = f"{platform}:{bot_id}:{user_id}:{target_id}"

        # 检查是否有等待的处理器
        if wait_key in self._waiting_replies:
            logger.trace(
                i18n.t(
                    "core.command.reply_matched",
                    wait_key=wait_key,
                    user_id=user_id,
                    platform=platform,
                )
            )
            wait_info = self._waiting_replies[wait_key]
            validator = wait_info.get("validator")

            # pattern（glob）/ regex（正则）过滤：不匹配则继续等待（不消费 future）
            _pattern = wait_info.get("pattern")
            _regex = wait_info.get("regex")
            if _pattern or _regex:
                _text_cond = compile_text_matcher(_pattern, _regex)
                _matched = _text_cond is None or _text_cond(event)
                if not _matched:
                    logger.trace(
                        i18n.t(
                            "core.command.reply_pattern_not_matched",
                            wait_key=wait_key,
                            user_id=user_id,
                            platform=platform,
                        )
                    )
                    return

            # 如果有验证器，验证回复是否有效
            if validator:
                if not validator(event):
                    # 验证失败，不处理此回复，继续等待
                    logger.trace(
                        i18n.t(
                            "core.command.reply_validation_failed",
                            wait_key=wait_key,
                            user_id=user_id,
                            platform=platform,
                        )
                    )
                    return

            # 设置 future 结果
            if not wait_info["future"].done():
                wait_info["future"].set_result(event)

            # 清理等待信息
            del self._waiting_replies[wait_key]

            # 标记事件已被处理（认领 + 阻断，阻止低优先级处理器再介入）
            event.mark_processed()

    async def _send_permission_denied(self, event: dict[str, Any]):
        """
        发送权限拒绝消息

        {!--< internal-use >!--}
        内部使用的方法

        :param event: 事件数据
        """
        try:
            platform = event.get("platform")

            # 使用会话类型管理模块获取发送类型和目标ID
            send_type, target_id = get_send_type_and_target_id(event, platform)

            if platform and hasattr(adapter, platform):
                adapter_instance = getattr(adapter, platform)
                bot_id = event.get("self", {}).get("account_id", "") or event.get(
                    "self", {}
                ).get("user_id", "")
                send_dsl = adapter_instance.Send.To(send_type, target_id)
                if bot_id:
                    send_dsl = send_dsl.Using(bot_id)
                await send_dsl.Text(i18n.t("core.event.command.permission_denied"))
        except Exception as e:
            logger.error(i18n.t("core.event.command.send_permission_denied_failed", error=e))

    async def _send_command_error(self, event: dict[str, Any], error: str):
        """
        发送命令错误消息

        {!--< internal-use >!--}
        内部使用的方法

        :param event: 事件数据
        :param error: 错误信息
        """
        try:
            platform = event.get("platform")

            # 使用会话类型管理模块获取发送类型和目标ID
            send_type, target_id = get_send_type_and_target_id(event, platform)

            if platform and hasattr(adapter, platform):
                adapter_instance = getattr(adapter, platform)
                bot_id = event.get("self", {}).get("account_id", "") or event.get(
                    "self", {}
                ).get("user_id", "")
                send_dsl = adapter_instance.Send.To(send_type, target_id)
                if bot_id:
                    send_dsl = send_dsl.Using(bot_id)
                await send_dsl.Text(i18n.t("core.event.command.execution_failed", error=error))
        except Exception as e:
            logger.error(i18n.t("core.event.command.send_error_failed", error=e))

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
        self._waiting_replies.clear()
        # 从共享 handler 中注销命令分发器（不清除其他 handler 的消息处理器）
        if self._bound_handler is not None and self._dispatcher_registered:
            self._bound_handler.unregister(self._handle_message)
            self._dispatcher_registered = False
        return count

    def get_command(self, name: str) -> dict | None:
        """
        获取命令信息

        :param name: 命令名称
        :return: 命令信息字典，如果不存在则返回None
        """
        actual_name = self.aliases.get(name, name)
        return self.commands.get(actual_name)

    def get_commands(self) -> dict[str, dict]:
        """
        获取所有命令

        :return: 命令信息字典
        """
        return self.commands

    def get_group_commands(self, group: str) -> list[str]:
        """
        获取命令组中的命令

        :param group: 命令组名称
        :return: 命令名称列表
        """
        return self.groups.get(group, [])

    def get_visible_commands(self) -> dict[str, dict]:
        """
        获取所有可见命令（非隐藏命令）

        :return: 可见命令信息字典
        """
        return {
            name: info
            for name, info in self.commands.items()
            if not info.get("hidden", False) and name == info["main_name"]
        }

    def help(self, command_name: str | None = None, show_hidden: bool = False) -> str:
        """
        生成帮助信息

        :param command_name: 命令名称，如果为None则生成所有命令的帮助
        :param show_hidden: 是否显示隐藏命令
        :return: 帮助信息字符串
        """
        # 用于显示的前缀：单个时保持原始字符串，多个时取第一个
        display_prefix = (
            self.prefix[0] if isinstance(self.prefix, list) else self.prefix
        )

        if command_name:
            cmd_info = self.get_command(command_name)
            if cmd_info:
                help_text = cmd_info.get("help", i18n.t("core.event.command.no_help"))
                usage = cmd_info.get("usage", f"{display_prefix}{command_name}")
                return i18n.t(
                    "core.event.command.help_command",
                    command_name=command_name,
                    usage=usage,
                    help_text=help_text,
                )
            return i18n.t("core.event.command.not_found", command_name=command_name)
        # 生成所有命令的帮助
        commands_to_show = (
            self.get_visible_commands()
            if not show_hidden
            else {
                name: info
                for name, info in self.commands.items()
                if name == info["main_name"]
            }
        )

        if not commands_to_show:
            return i18n.t("core.event.command.no_commands")

        help_lines = [i18n.t("core.event.command.available_commands")]
        for cmd_name, cmd_info in commands_to_show.items():
            help_text = cmd_info.get("help", i18n.t("core.event.command.no_help_item"))
            help_lines.append(
                i18n.t(
                    "core.event.command.list_item",
                    prefix=display_prefix,
                    cmd_name=cmd_name,
                    help_text=help_text,
                )
            )
        return "\n".join(help_lines)


command: CommandHandler = CommandHandler()
