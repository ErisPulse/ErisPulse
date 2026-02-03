"""
ErisPulse 模块基础模块

提供模块基类定义和标准接口
"""

from typing import Union, Dict, Any
from ...loaders.strategy import ModuleLoadStrategy


class BaseModule:
    """
    模块基类
    
    提供模块加载和卸载的标准接口
    """
    
    @staticmethod
    def get_load_strategy() -> Union[ModuleLoadStrategy, Dict[str, Any]]:
        """
        获取模块加载策略
        
        支持返回 ModuleLoadStrategy 对象或字典
        所有属性统一处理，没有任何预定义字段
        
        :return: 加载策略对象或字典
        
        {!--< tips >!--}
        常用配置项：
        - lazy_load: bool, 是否懒加载（默认 True）
        - priority: int, 加载优先级（默认 0，数值越大优先级越高）
        
        使用方式：
        >>> class MyModule(BaseModule):
        ...     @staticmethod
        ...     def get_load_strategy() -> ModuleLoadStrategy:
        ...         return ModuleLoadStrategy(
        ...             lazy_load=False,
        ...             priority=100
        ...         )
        
        或使用字典：
        >>> class MyModule(BaseModule):
        ...     @staticmethod
        ...     def get_load_strategy() -> dict:
        ...         return {
        ...             "lazy_load": False,
        ...             "priority": 100
        ...         }
        {!--< /tips >!--}
        """
        return ModuleLoadStrategy(
            lazy_load=True,   # 默认懒加载
            priority=0        # 默认优先级
        )
    
    @staticmethod
    def should_eager_load() -> bool:
        """
        模块是否应该在启动时加载
        默认为False(即懒加载)
        
        兼容方法，实际调用 get_load_strategy()

        :return: 是否应该在启动时加载
        
        {!--< tips >!--}
        旧版方法，建议使用 get_load_strategy() 替代
        {!--< /tips >!--}
        """
        strategy = BaseModule.get_load_strategy()
        if isinstance(strategy, dict):
            return not strategy.get('lazy_load', True)
        return not (strategy.lazy_load if 'lazy_load' in strategy else True)
    
    async def on_load(self, event: dict) -> bool:
        """
        当模块被加载时调用

        :param event: 事件内容
        :return: 处理结果

        {!--< tips >!--}
        其中，event事件内容为:
            `{ "module_name": "模块名" }`
        {!--< /tips >!--}
        """
        raise NotImplementedError
    
    async def on_unload(self, event: dict) -> bool:
        """
        当模块被卸载时调用

        :param event: 事件内容
        :return: 处理结果

        {!--< tips >!--}
        其中，event事件内容为:
            `{ "module_name": "模块名" }`
        {!--< /tips >!--}
        """
        raise NotImplementedError

__all__ = [
    "BaseModule"
]
