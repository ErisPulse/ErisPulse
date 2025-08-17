"""
ErisPulse 命令处理模块

提供基于装饰器的命令注册和处理功能
"""

from .base import BaseEventHandler
from .manager import event_manager
from .. import config, logger
from typing import Callable, Union, List, Dict, Any, Optional
import asyncio

class CommandHandler:
    """
    命令处理器
    
    提供命令注册、解析和执行功能
    """
    
    def __init__(self):
        """
        初始化命令处理器
        """
        self.commands: Dict[str, Dict] = {}
        self.aliases: Dict[str, str] = {}  # 别名映射
        self.groups: Dict[str, List[str]] = {}  # 命令组
        self.prefix = config.getConfig("ErisPulse.event.command.prefix", "/")
        self.handler = event_manager.create_event_handler("message", "command")
        
        # 注册消息处理器
        self.handler.register(self._handle_message)
    
    def __call__(self, 
                 name: Union[str, List[str]] = None, 
                 aliases: List[str] = None,
                 group: str = None,
                 priority: int = 0,
                 help: str = None,
                 usage: str = None):
        """
        命令装饰器
        
        :param name: 命令名称，可以是字符串或字符串列表
        :param aliases: 命令别名列表
        :param group: 命令组名称
        :param priority: 处理器优先级
        :param help: 命令帮助信息
        :param usage: 命令使用方法
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
                    "main_name": main_name
                }
                
                # 注册别名映射
                if cmd_name != main_name:
                    self.aliases[cmd_name] = main_name
            
            # 添加到命令组
            if group:
                if group not in self.groups:
                    self.groups[group] = []
                for cmd_name in cmd_names:
                    if cmd_name not in self.groups[group]:
                        self.groups[group].append(cmd_name)
            
            return func
        return decorator
    
    async def _handle_message(self, event: Dict[str, Any]):
        """
        处理消息事件中的命令
        
        {!--< internal-use >!--}
        内部使用的方法，用于从消息中解析并执行命令
        
        :param event: 消息事件数据
        """
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
        
        # 检查前缀
        if not text_content.startswith(self.prefix):
            return
        
        # 解析命令和参数
        command_text = text_content[len(self.prefix):].strip()
        parts = command_text.split()
        if not parts:
            return
        
        cmd_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # 处理别名
        actual_cmd_name = self.aliases.get(cmd_name, cmd_name)
        
        # 查找命令处理器
        if actual_cmd_name in self.commands:
            cmd_info = self.commands[actual_cmd_name]
            handler = cmd_info["func"]
            
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
            
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"命令执行错误: {e}")
                # 可以发送错误信息给用户
    
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
    
    def help(self, command_name: str = None) -> str:
        """
        生成帮助信息
        
        :param command_name: 命令名称，如果为None则生成所有命令的帮助
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
            help_lines = ["可用命令:"]
            for cmd_name, cmd_info in self.commands.items():
                if cmd_name == cmd_info["main_name"]:  # 只显示主命令
                    help_text = cmd_info.get("help", "无说明")
                    help_lines.append(f"  {self.prefix}{cmd_name} - {help_text}")
            return "\n".join(help_lines)

command = CommandHandler()