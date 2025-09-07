"""
ErisPulse 模块基础模块

提供模块基类定义和标准接口
"""

class BaseModule:
    """
    模块基类
    
    提供模块加载和卸载的标准接口
    """
    
    @staticmethod
    def should_eager_load() -> bool:
        """
        模块是否应该在启动时加载
        默认为False(即懒加载)

        :return: 是否应该在启动时加载
        """
        return False
    
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
