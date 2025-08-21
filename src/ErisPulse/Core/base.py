import functools
from typing import (
    Callable, Any, Optional,
    Union, Awaitable
)
from collections import defaultdict
from .logger import logger

class SendDSL:
    """
    消息发送DSL基类
    
    用于实现 Send.To(...).Func(...) 风格的链式调用接口
    
    {!--< tips >!--}
    1. 子类应实现具体的消息发送方法(如Text, Image等)
    2. 通过__getattr__实现动态方法调用
    {!--< /tips >!--}
    """
    
    def __init__(self, adapter: 'BaseAdapter', target_type: Optional[str] = None, target_id: Optional[str] = None, account_id: Optional[str] = None):
        """
        初始化DSL发送器
        
        :param adapter: 所属适配器实例
        :param target_type: 目标类型(可选)
        :param target_id: 目标ID(可选)
        :param _account_id: 发送账号(可选)
        """
        self._adapter = adapter
        self._target_type = target_type
        self._target_id = target_id
        self._target_to = target_id
        self._account_id = account_id

    def To(self, target_type: str = None, target_id: Union[str, int] = None) -> 'SendDSL':
        """
        设置消息目标
        
        :param target_type: 目标类型(可选)
        :param target_id: 目标ID(可选)
        :return: SendDSL实例
        
        :example:
        >>> adapter.Send.To("user", "123").Text("Hello")
        >>> adapter.Send.To("123").Text("Hello")  # 简化形式
        """
        if target_id is None and target_type is not None:
            target_id = target_type
            target_type = None

        return self.__class__(self._adapter, target_type, target_id, self._account_id)

    def Using(self, account_id: Union[str, int]) -> 'SendDSL':
        """
        设置发送账号
        
        :param _account_id: 发送账号
        :return: SendDSL实例
        
        :example:
        >>> adapter.Send.Using("bot1").To("123").Text("Hello")
        >>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序
        """
        return self.__class__(self._adapter, self._target_type, self._target_id, account_id)


class BaseAdapter:
    """
    适配器基类
    
    提供与外部平台交互的标准接口，子类必须实现必要方法
    
    {!--< tips >!--}
    1. 必须实现call_api, start和shutdown方法
    2. 可以自定义Send类实现平台特定的消息发送逻辑
    3. 通过on装饰器注册事件处理器
    4. 支持OneBot12协议的事件处理
    {!--< /tips >!--}
    """
    
    class Send(SendDSL):
        """
        消息发送DSL实现
        
        {!--< tips >!--}
        1. 子类可以重写Text方法提供平台特定实现
        2. 可以添加新的消息类型(如Image, Voice等)
        {!--< /tips >!--}
        """
        
        def Example(self, text: str) -> Awaitable[Any]:
            """
            示例消息发送方法
            
            :param text: 文本内容
            :return: 异步任务
            :example:
            >>> await adapter.Send.To("123").Example("Hello")
            """
            logger.debug(f"适配器 {self._adapter.__class__.__name__} 发送了实例类型的消息: {text}")
            
        
    def __init__(self):
        """
        初始化适配器
        """
        self._handlers = defaultdict(list)
        self._middlewares = []
        self.Send = self.__class__.Send(self)

    def on(self, event_type: str = "*") -> Callable[[Callable], Callable]:
        """
        适配器事件监听装饰器
        
        :param event_type: 事件类型
        :return: 装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            self._handlers[event_type].append(wrapper)

            return wrapper
        return decorator

    def middleware(self, func: Callable) -> Callable:
        """
        添加中间件处理器
        
        :param func: 中间件函数
        :return: 中间件函数
        
        :example:
        >>> @adapter.middleware
        >>> async def log_middleware(data):
        >>>     print(f"处理数据: {data}")
        >>>     return data
        """
        self._middlewares.append(func)
        return func

    async def call_api(self, endpoint: str, **params: Any) -> Any:
        """
        调用平台API的抽象方法
        
        :param endpoint: API端点
        :param params: API参数
        :return: API调用结果
        :raises NotImplementedError: 必须由子类实现
        """
        raise NotImplementedError("适配器必须实现call_api方法")

    async def start(self) -> None:
        """
        启动适配器的抽象方法
        
        :raises NotImplementedError: 必须由子类实现
        """
        raise NotImplementedError("适配器必须实现start方法")

    async def shutdown(self) -> None:
        """
        关闭适配器的抽象方法
        
        :raises NotImplementedError: 必须由子类实现
        """
        raise NotImplementedError("适配器必须实现shutdown方法")
        
    async def emit(self, event_type: str, data: Any) -> None:
        """
        触发原生协议事件
        
        :param event_type: 事件类型
        :param data: 事件数据
        
        :example:
        >>> await adapter.emit("message", {"text": "Hello"})
        """
        # 先执行中间件
        for middleware in self._middlewares:
            data = await middleware(data)

        # 触发具体事件类型的处理器
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                await handler(data)

        # 触发通配符 "*" 的处理器
        for handler in self._handlers.get("*", []):
            await handler(data)

    async def send(self, target_type: str, target_id: str, message: Any, **kwargs: Any) -> Any:
        """
        发送消息的便捷方法
        
        :param target_type: 目标类型
        :param target_id: 目标ID
        :param message: 消息内容
        :param kwargs: 其他参数
            - method: 发送方法名(默认为"Text")
        :return: 发送结果
        
        :raises AttributeError: 当发送方法不存在时抛出
            
        :example:
        >>> await adapter.send("user", "123", "Hello")
        >>> await adapter.send("group", "456", "Hello", method="Markdown")
        """
        method_name = kwargs.pop("method", "Text")
        method = getattr(self.Send.To(target_type, target_id), method_name, None)
        if not method:
            raise AttributeError(f"未找到 {method_name} 方法，请确保已在 Send 类中定义")
        return await method(text=message, **kwargs)

__all__ = [
    "BaseAdapter",
    "SendDSL",
]