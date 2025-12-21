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

from .base import BaseEventHandler
from .. import adapter, config, logger
from typing import Callable, Union, List, Dict, Any, Optional, Awaitable
import asyncio

class CommandHandler:
    """
    命令处理器
    
    提供命令注册、处理和管理功能
    """

    def __init__(self):
        self.commands: Dict[str, Dict] = {}
        self.aliases: Dict[str, str] = {}  # 别名映射
        self.groups: Dict[str, List[str]] = {}  # 命令组
        self.permissions: Dict[str, Callable] = {}  # 权限检查函数
        self.prefix = config.getConfig("ErisPulse.event.command.prefix", "/")
        self.case_sensitive = config.getConfig("ErisPulse.event.command.case_sensitive", True)
        self.allow_space_prefix = config.getConfig("ErisPulse.event.command.allow_space_prefix", False)
        
        # 等待回复相关
        self._waiting_replies = {}  # 存储等待回复的用户信息
        
        # 创建消息事件处理器
        self.handler = BaseEventHandler("message", "command")
        
        # 注册消息处理器
        if not hasattr(self.handler, '_command_handler_registered') or not self.handler._command_handler_registered:
            self.handler.register(self._handle_message)
            self.handler._command_handler_registered = True
    
    def __call__(self, 
                 name: Union[str, List[str]] = None, 
                 aliases: List[str] = None,
                 group: str = None,
                 priority: int = 0,
                 permission: Callable = None,
                 help: str = None,
                 usage: str = None,
                 hidden: bool = False):
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
                    "main_name": main_name
                }
                
                # 注册别名映射
                if cmd_name != main_name:
                    self.aliases[cmd_name] = main_name
                
                # 注册权限检查函数
                if permission and cmd_name not in self.permissions:
                    self.permissions[cmd_name] = permission
            
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
        # 从基础处理器中移除
        result = self.handler.unregister(handler)
        
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
            for group_name, group_commands in self.groups.items():
                if cmd_name in group_commands:
                    group_commands.remove(cmd_name)
            
            # 移除权限检查函数
            if cmd_name in self.permissions:
                del self.permissions[cmd_name]
            
            # 最后移除命令本身
            del self.commands[cmd_name]
        
        return result
    
    async def wait_reply(self, 
                        event: Dict[str, Any], 
                        prompt: str = None,
                        timeout: float = 60.0,
                        callback: Callable[[Dict[str, Any]], Awaitable[Any]] = None,
                        validator: Callable[[Dict[str, Any]], bool] = None) -> Optional[Dict[str, Any]]:
        """
        等待用户回复
        
        :param event: 原始事件数据
        :param prompt: 提示消息，如果提供会发送给用户
        :param timeout: 等待超时时间(秒)
        :param callback: 回调函数，当收到回复时执行
        :param validator: 验证函数，用于验证回复是否有效
        :return: 用户回复的事件数据，如果超时则返回None
        """
        platform = event.get("platform")
        user_id = event.get("user_id")
        group_id = event.get("group_id")
        detail_type = "group" if group_id else "private"
        target_id = group_id or user_id
        
        # 发送提示消息（如果提供）
        if prompt and platform:
            try:
                adapter_instance = getattr(adapter, platform)
                await adapter_instance.Send.To(detail_type, target_id).Text(prompt)
            except Exception as e:
                logger.warning(f"发送提示消息失败: {e}")
        
        # 创建等待 future
        future = asyncio.get_event_loop().create_future()
        
        # 存储等待信息
        wait_key = f"{platform}:{user_id}:{target_id}"
        self._waiting_replies[wait_key] = {
            "future": future,
            "callback": callback,
            "validator": validator,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        try:
            # 等待回复或超时
            result = await asyncio.wait_for(future, timeout=timeout)
            
            # 如果提供了回调函数，则执行
            if callback:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result)
                else:
                    callback(result)
            
            return result
        except asyncio.TimeoutError:
            # 清理超时的等待
            if wait_key in self._waiting_replies:
                del self._waiting_replies[wait_key]
            return None
        except Exception as e:
            # 清理异常情况
            if wait_key in self._waiting_replies:
                del self._waiting_replies[wait_key]
            logger.error(f"等待回复时发生错误: {e}")
            return None
    
    async def _handle_message(self, event: Dict[str, Any]):
        """
        处理消息事件中的命令
        
        {!--< internal-use >!--}
        内部使用的方法，用于从消息中解析并执行命令
        
        :param event: 消息事件数据
        """
        # 检查是否是系统消息或自身消息
        if event.get("self", {}).get("user_id") == event.get("user_id"):
            # 根据配置决定是否忽略自身消息
            ignore_self = config.getConfig("ErisPulse.event.message.ignore_self", True)
            if ignore_self:
                return
        
        # 检查是否已经被其他处理器标记为已处理
        if event.get("_processed"):
            return
            
        # 检查是否为文本消息
        if event.get("type") != "message":
            return
        
        message_segments = event.get("message", [])
        text_content = ""
        for segment in message_segments:
            if segment.get("type") == "text":
                text_content = segment.get("data", {}).get("text", "")
                break
        
        if not text_content:
            return
        
        # 处理大小写敏感性
        check_text = text_content if self.case_sensitive else text_content.lower()
        prefix = self.prefix if self.case_sensitive else self.prefix.lower()
        
        # 检查前缀
        if not check_text.startswith(prefix):
            # 检查是否允许空格前缀 (例如: "/ command")
            if self.allow_space_prefix and check_text.startswith(prefix + " "):
                pass
            else:
                # 检查是否是等待回复的消息
                await self._check_pending_reply(event)
                return
        
        # 解析命令和参数
        command_text = check_text[len(prefix):].strip()
        parts = command_text.split()
        if not parts:
            return
        
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
            permission_func = cmd_info.get("permission") or self.permissions.get(actual_cmd_name)
            if permission_func:
                try:
                    has_permission = permission_func(event) if not asyncio.iscoroutinefunction(permission_func) \
                                    else await permission_func(event)
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
                "group": cmd_info["group"]
            }
            
            event["command"] = command_info
            
            # 标记事件已被处理
            event["_processed"] = True
            
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"命令执行错误: {e}")
                await self._send_command_error(event, str(e))
    
    async def _check_pending_reply(self, event: Dict[str, Any]):
        """
        检查是否是等待回复的消息
        
        :param event: 消息事件数据
        """
        platform = event.get("platform")
        user_id = event.get("user_id")
        group_id = event.get("group_id")
        target_id = group_id or user_id
        
        wait_key = f"{platform}:{user_id}:{target_id}"
        
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
    
    async def _send_permission_denied(self, event: Dict[str, Any]):
        """
        发送权限拒绝消息
        
        {!--< internal-use >!--}
        内部使用的方法
        
        :param event: 事件数据
        """
        try:
            platform = event.get("platform")
            user_id = event.get("user_id")
            group_id = event.get("group_id")
            detail_type = "group" if group_id else "private"
            target_id = group_id or user_id
            
            if platform and hasattr(adapter, platform):
                adapter_instance = getattr(adapter, platform)
                await adapter_instance.Send.To(detail_type, target_id).Text("权限不足，无法执行该命令")
        except Exception as e:
            logger.error(f"发送权限拒绝消息失败: {e}")
    
    async def _send_command_error(self, event: Dict[str, Any], error: str):
        """
        发送命令错误消息
        
        {!--< internal-use >!--}
        内部使用的方法
        
        :param event: 事件数据
        :param error: 错误信息
        """
        try:
            platform = event.get("platform")
            user_id = event.get("user_id")
            group_id = event.get("group_id")
            detail_type = "group" if group_id else "private"
            target_id = group_id or user_id
            
            if platform and hasattr(adapter, platform):
                adapter_instance = getattr(adapter, platform)
                await adapter_instance.Send.To(detail_type, target_id).Text(f"命令执行出错: {error}")
        except Exception as e:
            logger.error(f"发送命令错误消息失败: {e}")

    def _clear_commands(self):
        """
        {!--< internal-use >!--}
        清除所有已注册的命令
        
        :return: 被清除的命令数量
        """
        count = len(self.commands)
        self.commands.clear()
        self.aliases.clear()
        self.groups.clear()
        self.permissions.clear()
        self._waiting_replies.clear()
        return count
    
    def get_command(self, name: str) -> Optional[Dict]:
        """
        获取命令信息
        
        :param name: 命令名称
        :return: 命令信息字典，如果不存在则返回None
        """
        actual_name = self.aliases.get(name, name)
        return self.commands.get(actual_name)
    
    def get_commands(self) -> Dict[str, Dict]:
        """
        获取所有命令
        
        :return: 命令信息字典
        """
        return self.commands
    
    def get_group_commands(self, group: str) -> List[str]:
        """
        获取命令组中的命令
        
        :param group: 命令组名称
        :return: 命令名称列表
        """
        return self.groups.get(group, [])
    
    def get_visible_commands(self) -> Dict[str, Dict]:
        """
        获取所有可见命令（非隐藏命令）
        
        :return: 可见命令信息字典
        """
        return {name: info for name, info in self.commands.items() 
                if not info.get("hidden", False) and name == info["main_name"]}
    
    def help(self, command_name: str = None, show_hidden: bool = False) -> str:
        """
        生成帮助信息
        
        :param command_name: 命令名称，如果为None则生成所有命令的帮助
        :param show_hidden: 是否显示隐藏命令
        :return: 帮助信息字符串
        """
        if command_name:
            cmd_info = self.get_command(command_name)
            if cmd_info:
                help_text = cmd_info.get("help", "无帮助信息")
                usage = cmd_info.get("usage", f"{self.prefix}{command_name}")
                return f"命令: {command_name}\n用法: {usage}\n说明: {help_text}"
            else:
                return f"未找到命令: {command_name}"
        else:
            # 生成所有命令的帮助
            commands_to_show = self.get_visible_commands() if not show_hidden else {
                name: info for name, info in self.commands.items() 
                if name == info["main_name"]
            }
            
            if not commands_to_show:
                return "暂无可用命令"
            
            help_lines = ["可用命令:"]
            for cmd_name, cmd_info in commands_to_show.items():
                help_text = cmd_info.get("help", "无说明")
                help_lines.append(f"  {self.prefix}{cmd_name} - {help_text}")
            return "\n".join(help_lines)

command = CommandHandler()