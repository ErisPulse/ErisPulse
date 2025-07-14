"""
ErisPulse 适配器系统

提供平台适配器基类、消息发送DSL和适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。

{!--< tips >!--}
1. 适配器必须继承BaseAdapter并实现必要方法
2. 使用SendDSL实现链式调用风格的消息发送接口
3. 适配器管理器支持多平台适配器的注册和生命周期管理
4. 支持OneBot12协议的事件处理
{!--< /tips >!--}
"""

import functools
import asyncio
import uuid
import time
from typing import (
    Callable, Any, Dict, List, Type, Optional, Set, 
    Union, Awaitable, TypeVar, Generic, Tuple, Coroutine, FrozenSet
)
from collections import defaultdict


class SendDSLBase:
    """
    消息发送DSL基类
    
    用于实现 Send.To(...).Func(...) 风格的链式调用接口
    
    {!--< tips >!--}
    1. 子类应实现具体的消息发送方法(如Text, Image等)
    2. 通过__getattr__实现动态方法调用
    {!--< /tips >!--}
    """
    
    def __init__(self, adapter: 'BaseAdapter', target_type: Optional[str] = None, target_id: Optional[str] = None):
        """
        初始化DSL发送器
        
        :param adapter: 所属适配器实例
        :param target_type: 目标类型(可选)
        :param target_id: 目标ID(可选)
        """
        self._adapter = adapter
        self._target_type = target_type
        self._target_id = target_id
        self._target_to = target_id

    def To(self, target_type: str = None, target_id: str = None) -> 'SendDSL':
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

        return self.__class__(self._adapter, target_type, target_id)


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
    
    class Send(SendDSLBase):
        """
        消息发送DSL实现
        
        {!--< tips >!--}
        1. 子类可以重写Text方法提供平台特定实现
        2. 可以添加新的消息类型(如Image, Voice等)
        {!--< /tips >!--}
        """
        
        def Text(self, text: str) -> Awaitable[Any]:
            """
            基础文本消息发送方法
            
            :param text: 文本内容
            :return: 异步任务
            
            :example:
            >>> await adapter.Send.To("123").Text("Hello")
            """
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
        
    def __init__(self):
        """
        初始化适配器
        """
        self._handlers = defaultdict(list)  # 原生事件处理器
        self._onebot_handlers = defaultdict(list)  # OneBot12事件处理器
        self._middlewares = []
        self.Send = self.__class__.Send(self)

    def on(self, event_type: str = "*", *, onebot12: bool = False) -> Callable[[Callable], Callable]:
        """
        适配器事件监听装饰器
        
        :param event_type: 事件类型
        :param onebot12: 是否监听OneBot12协议事件
        :return: 装饰器函数
        
        :example:
        >>> @adapter.on("message")
        >>> async def handle_message(data):
        >>>     print(f"收到消息: {data}")
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            if onebot12:
                self._onebot_handlers[event_type].append(wrapper)
            else:
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

    def add_handler(self, *args: Any) -> None:
        """
        添加事件处理器
        
        :param args: 参数列表
            - 1个参数: 处理器函数(监听所有事件)
            - 2个参数: 事件类型和处理器函数
            
        :raises TypeError: 当参数数量无效时抛出
            
        :example:
        >>> # 监听所有事件
        >>> adapter.add_handler(handle_all_events)
        >>> # 监听特定事件
        >>> adapter.add_handler("message", handle_message)
        """
        if len(args) == 1:
            event_type = "*"
            handler = args[0]
        elif len(args) == 2:
            event_type, handler = args
        else:
            raise TypeError("add_handler() 接受 1 个（监听所有事件）或 2 个参数（指定事件类型）")

        @functools.wraps(handler)
        async def wrapper(*handler_args, **handler_kwargs):
            return await handler(*handler_args, **handler_kwargs)

        self._handlers[event_type].append(wrapper)
        
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

    async def emit_onebot12(self, event_type: str, onebot_data: Dict) -> None:
        """
        提交OneBot12协议事件
        
        :param event_type: OneBot12事件类型
        :param onebot_data: 符合OneBot12标准的事件数据
        
        :example:
        >>> await adapter.emit_onebot12("message", {
        >>>     "id": "123",
        >>>     "time": 1620000000,
        >>>     "type": "message",
        >>>     "detail_type": "private",
        >>>     "message": [{"type": "text", "data": {"text": "Hello"}}]
        >>> })
        """
        # 先执行中间件
        for middleware in self._middlewares:
            onebot_data = await middleware(onebot_data)

        # 触发OneBot12事件处理器
        if event_type in self._onebot_handlers:
            for handler in self._onebot_handlers[event_type]:
                await handler(onebot_data)

        # 触发通配符 "*" 的处理器
        for handler in self._onebot_handlers.get("*", []):
            await handler(onebot_data)

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


class AdapterManager:
    """
    适配器管理器
    
    管理多个平台适配器的注册、启动和关闭
    
    {!--< tips >!--}
    1. 通过register方法注册适配器
    2. 通过startup方法启动适配器
    3. 通过shutdown方法关闭所有适配器
    4. 通过on装饰器注册OneBot12协议事件处理器
    {!--< /tips >!--}
    """
    
    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}
        self._adapter_instances: Dict[Type[BaseAdapter], BaseAdapter] = {}
        self._platform_to_instance: Dict[str, BaseAdapter] = {}
        self._started_instances: Set[BaseAdapter] = set()
        
        # OneBot12事件处理器
        self._onebot_handlers = defaultdict(list)
        self._onebot_middlewares = []

    @property
    def Adapter(self) -> Type[BaseAdapter]:
        """
        获取BaseAdapter类，用于访问原始事件监听
        
        :return: BaseAdapter类
        
        :example:
        >>> @sdk.adapter.Adapter.on("raw_event")
        >>> async def handle_raw(data):
        >>>     print("收到原始事件:", data)
        """
        return BaseAdapter

    def on(self, event_type: str = "*") -> Callable[[Callable], Callable]:
        """
        OneBot12协议事件监听装饰器
        
        :param event_type: OneBot12事件类型
        :return: 装饰器函数
        
        :example:
        >>> @sdk.adapter.on("message")
        >>> async def handle_message(data):
        >>>     print(f"收到OneBot12消息: {data}")
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            self._onebot_handlers[event_type].append(wrapper)
            return wrapper
        return decorator

    def middleware(self, func: Callable) -> Callable:
        """
        添加OneBot12中间件处理器
        
        :param func: 中间件函数
        :return: 中间件函数
        
        :example:
        >>> @sdk.adapter.middleware
        >>> async def onebot_middleware(data):
        >>>     print("处理OneBot12数据:", data)
        >>>     return data
        """
        self._onebot_middlewares.append(func)
        return func

    async def emit(self, data: Any) -> None:
        """
        提交OneBot12协议事件到指定平台
        
        :param platform: 平台名称
        :param event_type: OneBot12事件类型
        :param data: 符合OneBot12标准的事件数据
        
        :raises ValueError: 当平台未注册时抛出
            
        :example:
        >>> await sdk.adapter.emit("MyPlatform", "message", {
        >>>     "id": "123",
        >>>     "time": 1620000000,
        >>>     "type": "message",
        >>>     "detail_type": "private",
        >>>     "message": [{"type": "text", "data": {"text": "Hello"}}]
        >>> })
        """
        platform = data.get("platform", "unknown")
        event_type = data.get("type", "unknown")

        if platform not in self._adapters:
            raise ValueError(f"平台 {platform} 未注册")
        
        # 先执行OneBot12中间件
        processed_data = data
        for middleware in self._onebot_middlewares:
            processed_data = await middleware(processed_data)

        # 分发到OneBot12事件处理器
        if event_type in self._onebot_handlers:
            for handler in self._onebot_handlers[event_type]:
                await handler(processed_data)
        for handler in self._onebot_handlers.get("*", []):
            await handler(processed_data)

    def register(self, platform: str, adapter_class: Type[BaseAdapter]) -> bool:
        """
        注册新的适配器类
        
        :param platform: 平台名称
        :param adapter_class: 适配器类
        :return: 注册是否成功
        
        :raises TypeError: 当适配器类无效时抛出
            
        :example:
        >>> adapter.register("MyPlatform", MyPlatformAdapter)
        """
        if not issubclass(adapter_class, BaseAdapter):
            raise TypeError("适配器必须继承自BaseAdapter")
        from .. import sdk

        # 如果该类已经创建过实例，复用
        if adapter_class in self._adapter_instances:
            instance = self._adapter_instances[adapter_class]
        else:
            instance = adapter_class(sdk)
            self._adapter_instances[adapter_class] = instance

        # 注册平台名，并统一映射到该实例
        self._adapters[platform] = instance
        self._platform_to_instance[platform] = instance

        if len(platform) <= 10:
            from itertools import product
            combinations = [''.join(c) for c in product(*[(ch.lower(), ch.upper()) for ch in platform])]
            for name in set(combinations):
                setattr(self, name, instance)
        else:
            self.logger.warning(f"平台名 {platform} 过长，如果您是开发者，请考虑使用更短的名称")
            setattr(self, platform.lower(), instance)
            setattr(self, platform.upper(), instance)
            setattr(self, platform.capitalize(), instance)

        return True

    async def startup(self, platforms: List[str] = None) -> None:
        """
        启动指定的适配器
        
        :param platforms: 要启动的平台列表，None表示所有平台
        
        :raises ValueError: 当平台未注册时抛出
            
        :example:
        >>> # 启动所有适配器
        >>> await adapter.startup()
        >>> # 启动指定适配器
        >>> await adapter.startup(["Platform1", "Platform2"])
        """
        if platforms is None:
            platforms = list(self._adapters.keys())

        from .env import env
        from .logger import logger
        from .server import adapter_server

        server_config = env.getConfig("Server")

        if server_config is None:
            server_config = {
                "host": "0.0.0.0",
                "port": 8000,
                "ssl_certfile": None,
                "ssl_keyfile": None
            }
            env.setConfig("Server", server_config)
            logger.info("已创建服务器配置")
        
        host = server_config["host"]
        port = server_config["port"]
        ssl_cert = server_config.get("ssl_certfile", None)
        ssl_key = server_config.get("ssl_keyfile", None)

        # 启动服务器
        await adapter_server.start(
            host=host,
            port=port,
            ssl_certfile=ssl_cert,
            ssl_keyfile=ssl_key
        )
        # 已经被调度过的 adapter 实例集合（防止重复调度）
        scheduled_adapters = set()

        for platform in platforms:
            if platform not in self._adapters:
                raise ValueError(f"平台 {platform} 未注册")
            adapter = self._adapters[platform]

            # 如果该实例已经被启动或已调度，跳过
            if adapter in self._started_instances or adapter in scheduled_adapters:
                continue

            # 加入调度队列
            scheduled_adapters.add(adapter)
            asyncio.create_task(self._run_adapter(adapter, platform))

    async def _run_adapter(self, adapter: BaseAdapter, platform: str) -> None:
        """
        {!--< internal-use >!--}
        运行适配器实例
        
        :param adapter: 适配器实例
        :param platform: 平台名称
        """
        from .. import sdk

        # 加锁防止并发启动
        if not getattr(adapter, "_starting_lock", None):
            adapter._starting_lock = asyncio.Lock()

        async with adapter._starting_lock:
            # 再次确认是否已经被启动
            if adapter in self._started_instances:
                sdk.logger.info(f"适配器 {platform}（实例ID: {id(adapter)}）已被其他协程启动，跳过")
                return

            retry_count = 0
            fixed_delay = 3 * 60 * 60
            backoff_intervals = [60, 10 * 60, 30 * 60, 60 * 60]

            while True:
                try:
                    await adapter.start()
                    self._started_instances.add(adapter)
                    return
                except Exception as e:
                    retry_count += 1
                    sdk.logger.error(f"平台 {platform} 启动失败（第{retry_count}次重试）: {e}")

                    try:
                        await adapter.shutdown()
                    except Exception as stop_err:
                        sdk.logger.warning(f"停止适配器失败: {stop_err}")

                    # 计算等待时间
                    if retry_count <= len(backoff_intervals):
                        wait_time = backoff_intervals[retry_count - 1]
                    else:
                        wait_time = fixed_delay

                    sdk.logger.info(f"将在 {wait_time // 60} 分钟后再次尝试重启 {platform}")
                    await asyncio.sleep(wait_time)

    async def shutdown(self) -> None:
        """
        关闭所有适配器
        
        :example:
        >>> await adapter.shutdown()
        """
        for adapter in self._adapters.values():
            await adapter.shutdown()
        
        from .server import adapter_server
        adapter_server.stop()

    def get(self, platform: str) -> Optional[BaseAdapter]:
        """
        获取指定平台的适配器实例
        
        :param platform: 平台名称
        :return: 适配器实例或None
            
        :example:
        >>> adapter = adapter.get("MyPlatform")
        """
        platform_lower = platform.lower()
        for registered, instance in self._adapters.items():
            if registered.lower() == platform_lower:
                return instance
        return None

    def __getattr__(self, platform: str) -> BaseAdapter:
        """
        通过属性访问获取适配器实例
        
        :param platform: 平台名称
        :return: 适配器实例
        
        :raises AttributeError: 当平台未注册时抛出
            
        :example:
        >>> adapter = adapter.MyPlatform
        """
        platform_lower = platform.lower()
        for registered, instance in self._adapters.items():
            if registered.lower() == platform_lower:
                return instance
        raise AttributeError(f"平台 {platform} 的适配器未注册")

    @property
    def platforms(self) -> List[str]:
        """
        获取所有已注册的平台列表
        
        :return: 平台名称列表
            
        :example:
        >>> print("已注册平台:", adapter.platforms)
        """
        return list(self._adapters.keys())


AdapterFather = BaseAdapter
adapter = AdapterManager()
SendDSL = SendDSLBase
