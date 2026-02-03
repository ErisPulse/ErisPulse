"""
ErisPulse 模块加载策略

提供统一的模块加载策略配置类

{!--< tips >!--}
1. 所有属性统一处理，没有预定义字段
2. 支持通过构造函数传入任意参数
3. 支持字典方式创建
{!--< /tips >!--}
"""

from typing import Any, Dict, Union


class ModuleLoadStrategy:
    """
    模块加载策略配置
    
    所有属性统一处理，通过魔术方法实现动态访问
    没有预定义属性，完全由用户传入的内容决定
    
    {!--< tips >!--}
    使用方式：
    >>> strategy = ModuleLoadStrategy(
    ...     lazy_load=False,
    ...     priority=100,
    ...     custom_option=123
    ... )

    eager_load 也是一个合法的属性，但不建议使用，其的han'y
    >>> strategy.lazy_load
    False
    >>> strategy.priority
    100
    >>> strategy.custom_option
    123
    
    从字典创建：
    >>> config = {"lazy_load": False, "priority": 100}
    >>> strategy = ModuleLoadStrategy.from_dict(config)
    {!--< /tips >!--}
    """
    
    def __init__(self, **kwargs):
        """
        初始化策略，所有参数统一存储
        
        :param kwargs: 策略配置项，任意键值对
        
        {!--< tips >!--}
        常用配置项：
        - lazy_load: bool, 是否懒加载（默认 True）
        - priority: int, 加载优先级（默认 0，数值越大优先级越高）
        {!--< /tips >!--}
        """
        object.__setattr__(self, '_data', kwargs)
    
    def __getattr__(self, name: str) -> Any:
        """
        获取属性值
        
        :param name: 属性名
        :return: 属性值，如果不存在则返回 None
        
        {!--< internal-use >!--}
        内部方法，用于动态属性访问
        {!--< /internal-use >!--}
        """
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
        data = object.__getattribute__(self, '_data')
        if name not in data:
            return None
        return data[name]
    
    def __setattr__(self, name: str, value: Any) -> Any:
        """
        设置属性值
        
        :param name: 属性名
        :param value: 属性值
        
        {!--< internal-use >!--}
        内部方法，用于动态属性设置
        {!--< /internal-use >!--}
        """
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            self._data[name] = value
    
    def __contains__(self, name: str) -> bool:
        """
        检查属性是否存在
        
        :param name: 属性名
        :return: 是否存在该属性
        """
        return name in self._data
    
    def __repr__(self) -> str:
        """
        返回策略的字符串表示
        
        :return: 字符串表示
        """
        return f"ModuleLoadStrategy({self._data})"
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'ModuleLoadStrategy':
        """
        从字典创建策略实例
        
        :param config: 配置字典
        :return: 策略实例
        
        {!--< tips >!--}
        示例：
        >>> config = {"lazy_load": False, "priority": 100}
        >>> strategy = ModuleLoadStrategy.from_dict(config)
        {!--< /tips >!--}
        """
        return cls(**config)


__all__ = [
    "ModuleLoadStrategy"
]
