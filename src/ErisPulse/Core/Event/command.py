"""
ErisPulse 命令处理模块

提供基于装饰器的命令注册和处理功能

{!--< tips >!--}
1. 支持命令别名和命令组
2. 支持命令权限控制
3. 支持命令帮助系统
4. 支持等待用户回复交互
{!--< /tips >!--}
"""

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from ...runtime import get_event_config
from ...runtime.context import current_owner, handler_waits
from .. import adapter, logger
from ..constants import (
    DEFAULT_COMMAND_ALLOW_SPACE_PREFIX,
    DEFAULT_COMMAND_DISPATCHER_PRIORITY,
    DEFAULT_COMMAND_MUST_AT_BOT,
    DEFAULT_SEND_METHOD,
    DEFAULT_WAIT_TIMEOUT_SECS,
    DETAIL_TYPE_PRIVATE,
    DETAIL_TYPE_USER,
    UNKNOWN_PLATFORM,
)
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

        # 从 _bootstrap 获取配置
        event_config = get_event_config()
        command_config = event_config.get("command", {})
        # prefix 支持字符串（单个）或列表（多个），保持原始类型以向后兼容
        self.prefix = command_config.get("prefix", "/")
        # 归一化为列表，用于内部统一处理
        self._prefixes = (
            list(self.prefix) if isinstance(self.prefix, list) else [self.prefix]
        )
        self.case_sensitive = command_config.get("case_sensitive", True)
        self.allow_space_prefix = command_config.get(
            "allow_space_prefix", DEFAULT_COMMAND_ALLOW_SPACE_PREFIX
        )
        self.must_at_bot = command_config.get(
            "must_at_bot", DEFAULT_COMMAND_MUST_AT_BOT
        )

        # 等待回复相关
        self._waiting_replies = {}  # 存储等待回复的用户信息

        # 共享的消息事件处理器引用（由 bind_message_handler() 设置）
        # 命令分发器 _handle_message 以高优先级注册在同一个队列中，
        # 确保命令 /xxx 始终优先于 on_message / on_group_message 触发
        self._bound_handler: BaseEventHandler | None = None
        self._dispatcher_registered: bool = False

    def __call__(
        self,
        name: str | list[str] = None,
        aliases: list[str] = None,
        group: str = None,
        priority: int = 0,
        permission: Callable = None,
        help: str = None,
        usage: str = None,
        hidden: bool = False,
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
            for group_name, group_commands in self.groups.items():
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
                f"[Command] 已清理 {owner} 的 {len(to_remove)} 个命令: {to_remove}"
            )
        return len(to_remove)

    async def wait_reply(
        self,
        event: dict[str, Any],
        prompt: str = None,
        timeout: float = DEFAULT_WAIT_TIMEOUT_SECS,
        callback: Callable[[dict[str, Any]], Awaitable[Any]] = None,
        validator: Callable[[dict[str, Any]], bool] = None,
        method: str = DEFAULT_SEND_METHOD,
    ) -> dict[str, Any] | None:
        """
        等待用户回复

        :param event: 原始事件数据
        :param prompt: 提示消息，如果提供会发送给用户
        :param timeout: 等待超时时间(秒)
        :param callback: 回调函数，当收到回复时执行
        :param validator: 验证函数，用于验证回复是否有效
        :param method: 发送方法，默认为 "Text"
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
                    await send_func(prompt)
                else:
                    await send_dsl.Text(prompt)
            except Exception as e:
                logger.warning(f"发送提示消息失败: {e}")

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
            # 清理超时的等待
            if wait_key in self._waiting_replies:
                del self._waiting_replies[wait_key]
            logger.trace(f"wait_reply 超时: key={wait_key}, timeout={timeout}s")
            return None
        except Exception as e:
            # 清理异常情况
            if wait_key in self._waiting_replies:
                del self._waiting_replies[wait_key]
            logger.error(f"等待回复时发生错误: {e}")
            return None

    async def _handle_message(self, event: dict[str, Any]):
        """
        处理消息事件中的命令

        {!--< internal-use >!--}
        内部使用的方法，用于从消息中解析并执行命令

        :param event: 消息事件数据
        """

        # 检查是否已经被其他处理器标记为已处理
        if event.get("_processed"):
            return

        # 检查是否为文本消息
        if event.get("type") != "message":
            return

        async def _process_text_for_command(event: dict[str, Any], text: str) -> bool:
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
        self, event: dict[str, Any], original_text: str, check_text: str, prefix: str
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

        # 查找命令处理器
        if actual_cmd_name in self.commands:
            cmd_info = self.commands[actual_cmd_name]
            handler = cmd_info["func"]

            # 检查权限
            permission_func = cmd_info.get("permission") or self.permissions.get(
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
                        await self._send_permission_denied(event)
                        return
                except Exception as e:
                    logger.error(f"权限检查错误: {e}")
                    await self._send_permission_denied(event)
                    return

            # 添加命令相关信息到事件
            command_info = {
                "name": actual_cmd_name,
                "main_name": cmd_info["main_name"],
                "args": args,
                "raw": command_text,
                "help": cmd_info["help"],
                "usage": cmd_info["usage"],
                "group": cmd_info["group"],
            }

            event["command"] = command_info

            # 标记事件已被处理
            event["_processed"] = True

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
                logger.error(f"命令执行错误: {e}")
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

        return False

    async def _check_pending_reply(self, event: dict[str, Any]):
        """
        检查是否是等待回复的消息

        :param event: 消息事件数据
        """
        platform = event.get("platform")
        user_id = event.get("user_id")

        # 使用会话类型管理模块获取发送类型和目标ID
        send_type, target_id = get_send_type_and_target_id(event, platform)

        bot_id = event.get("self", {}).get("account_id", "") or event.get(
            "self", {}
        ).get("user_id", "")
        wait_key = f"{platform}:{bot_id}:{user_id}:{target_id}"

        # 检查是否有等待的处理器
        if wait_key in self._waiting_replies:
            wait_info = self._waiting_replies[wait_key]
            validator = wait_info.get("validator")

            # 如果有验证器，验证回复是否有效
            if validator:
                if not validator(event):
                    # 验证失败，不处理此回复，继续等待
                    return

            # 设置 future 结果
            if not wait_info["future"].done():
                wait_info["future"].set_result(event)

            # 清理等待信息
            del self._waiting_replies[wait_key]

            # 标记事件已被处理
            event["_processed"] = True

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
                await send_dsl.Text("权限不足，无法执行该命令")
        except Exception as e:
            logger.error(f"发送权限拒绝消息失败: {e}")

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
                await send_dsl.Text(f"命令执行出错: {error}")
        except Exception as e:
            logger.error(f"发送命令错误消息失败: {e}")

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
            self._bound_handler.register(
                self._handle_message,
                priority=DEFAULT_COMMAND_DISPATCHER_PRIORITY,
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

    def help(self, command_name: str = None, show_hidden: bool = False) -> str:
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
                help_text = cmd_info.get("help", "无帮助信息")
                usage = cmd_info.get("usage", f"{display_prefix}{command_name}")
                return f"命令: {command_name}\n用法: {usage}\n说明: {help_text}"
            else:
                return f"未找到命令: {command_name}"
        else:
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
                return "暂无可用命令"

            help_lines = ["可用命令:"]
            for cmd_name, cmd_info in commands_to_show.items():
                help_text = cmd_info.get("help", "无说明")
                help_lines.append(f"  {display_prefix}{cmd_name} - {help_text}")
            return "\n".join(help_lines)


command: CommandHandler = CommandHandler()
