"""
ErisPulse 管理器基类

提供适配器和模块管理器的统一接口定义

{!--< tips >!--}
适配器管理器和模块管理器都应继承此基类以保持接口一致性
{!--< /tips >!--}
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Type, Optional


class ManagerBase(ABC):
    """
    管理器基类
    
    定义适配器和模块管理器的统一接口
    
    {!--< tips >!--}
    统一方法：
    - register(): 注册类
    - unregister(): 取消注册
    - get(): 获取实例
    - exists(): 检查是否存在
    - enable()/disable(): 启用/禁用
    - is_enabled(): 检查是否启用
    - list_*(): 列出相关项
    {!--< /tips >!--}
    """
    
    # ==================== 注册与取消注册 ====================
    
    @abstractmethod
    def register(self, name: str, class_type: Type, info: Optional[Dict] = None) -> bool:
        """
        注册类
        
        :param name: 名称
        :param class_type: 类类型
        :param info: 额外信息
        :return: 是否注册成功
        """
        ...
    
    @abstractmethod
    def unregister(self, name: str) -> bool:
        """
        取消注册
        
        :param name: 名称
        :return: 是否取消成功
        """
        ...
    
    # ==================== 实例获取 ====================
    
    @abstractmethod
    def get(self, name: str) -> Any:
        """
        获取实例
        
        :param name: 名称
        :return: 实例或 None
        """
        ...
    
    # ==================== 存在性检查 ====================
    
    @abstractmethod
    def exists(self, name: str) -> bool:
        """
        检查是否存在（在配置中注册）
        
        :param name: 名称
        :return: 是否存在
        """
        ...
    
    # ==================== 启用/禁用管理 ====================
    
    @abstractmethod
    def is_enabled(self, name: str) -> bool:
        """
        检查是否启用
        
        :param name: 名称
        :return: 是否启用
        """
        ...
    
    @abstractmethod
    def enable(self, name: str) -> bool:
        """
        启用
        
        :param name: 名称
        :return: 是否成功
        """
        ...
    
    @abstractmethod
    def disable(self, name: str) -> bool:
        """
        禁用
        
        :param name: 名称
        :return: 是否成功
        """
        ...
    
    # ==================== 列表方法 ====================
    
    @abstractmethod
    def list_registered(self) -> List[str]:
        """
        列出所有已注册的项
        
        :return: 名称列表
        """
        ...
    
    @abstractmethod
    def list_items(self) -> Dict[str, bool]:
        """
        列出所有项及其状态
        
        :return: {名称: 是否启用} 字典
        """
        ...


__all__ = [
    "ManagerBase"
]
