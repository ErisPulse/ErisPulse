"""
CLI 命令基类

定义所有命令的统一接口
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser


class Command(ABC):
    """
    命令基类
    
    所有 CLI 命令都应继承此类并实现抽象方法
    
    {!--< tips >!--}
    1. 每个命令类必须实现 add_arguments 和 execute 方法
    2. name 和 description 为类属性，必须在子类中定义
    3. execute 方法接收解析后的 args 对象
    {!--< /tips >!--}
    """
    
    name: str = ""  # 命令名称
    description: str = ""  # 命令描述
    
    @abstractmethod
    def add_arguments(self, parser: ArgumentParser):
        """
        添加命令参数
        
        :param parser: ArgumentParser 实例
        """
        pass
    
    @abstractmethod
    def execute(self, args):
        """
        执行命令
        
        :param args: 解析后的参数对象
        """
        pass
    
    @property
    def help(self) -> str:
        """
        获取帮助信息
        
        :return: 命令描述
        """
        return self.description
