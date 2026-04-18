"""
CLI 命令注册器

负责命令的注册、查找和管理
"""

from typing import Optional, List, Dict
from .base import Command


class CommandRegistry:
    """
    命令注册器
    
    管理所有已注册的 CLI 命令
    
    {!--< tips >!--}
    1. 使用单例模式确保全局唯一
    2. 支持命令的动态注册和查找
    {!--< /tips >!--}
    
    :ivar _commands: 已注册的命令字典 {name: Command}
    """
    
    _instance = None
    _commands: Dict[str, Command]
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._commands = {}
        return cls._instance
    
    def register(self, command: Command):
        """
        注册命令
        
        :param command: 要注册的命令实例
        :raises ValueError: 命令名称已存在时抛出
        """
        if command.name in self._commands:
            raise ValueError(f"命令 '{command.name}' 已存在")
        self._commands[command.name] = command
    
    def get(self, name: str) -> Optional[Command]:
        """
        获取命令
        
        :param name: 命令名称
        :return: 命令实例，未找到返回 None
        """
        return self._commands.get(name)
    
    def get_all(self) -> List[Command]:
        """
        获取所有命令
        
        :return: 所有命令列表
        """
        return list(self._commands.values())
    
    def list_all(self) -> List[str]:
        """
        列出所有命令名称
        
        :return: 命令名称列表
        """
        return list(self._commands.keys())
    
    def list_builtin(self) -> List[str]:
        """
        列出内置命令名称
        
        :return: 内置命令名称列表
        """
        return list(self._commands.keys())
    
    def exists(self, name: str) -> bool:
        """
        检查命令是否存在
        
        :param name: 命令名称
        :return: 命令是否存在
        """
        return name in self._commands
