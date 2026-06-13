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
    :ivar _aliases: 命令别名到命令名的映射 {alias: command_name}
    """

    _instance = None
    _commands: Dict[str, Command]
    _aliases: Dict[str, str]

    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._commands = {}
            cls._instance._aliases = {}
        return cls._instance

    def register(self, command: Command):
        """
        注册命令

        :param command: 要注册的命令实例
        :raises ValueError: 命令名称已存在时抛出
        """
        if command.name in self._commands:
            return
        self._commands[command.name] = command
        # 注册命令别名（简化形式），冲突时保留先注册者
        for alias in getattr(command, "aliases", None) or []:
            if alias and alias not in self._commands and alias not in self._aliases:
                self._aliases[alias] = command.name

    def resolve(self, name: str) -> Optional[str]:
        """
        将命令名或别名解析为规范命令名

        :param name: 命令名或别名
        :return: [str] 规范命令名，未找到返回 None
        """
        if name in self._commands:
            return name
        return self._aliases.get(name)

    def get(self, name: str) -> Optional[Command]:
        """
        获取命令（支持通过别名查找）

        :param name: 命令名称或别名
        :return: 命令实例，未找到返回 None
        """
        canonical = self.resolve(name)
        if canonical is None:
            return None
        return self._commands.get(canonical)

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

    def list_aliases(self) -> Dict[str, str]:
        """
        列出所有命令别名映射

        :return: [dict] 别名到规范命令名的映射 {alias: command_name}
        """
        return dict(self._aliases)

    def exists(self, name: str) -> bool:
        """
        检查命令是否存在（支持别名）

        :param name: 命令名称或别名
        :return: 命令是否存在
        """
        return self.resolve(name) is not None
