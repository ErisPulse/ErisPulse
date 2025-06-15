import functools
import asyncio
from typing import Callable, Any, Dict, List, Type, Optional, Set
from collections import defaultdict


# DSL 基类，用于实现 Send.To(...).Func(...) 风格
class SendDSLBase:
    def __init__(self, adapter: 'BaseAdapter', target_type: Optional[str] = None, target_id: Optional[str] = None):
        self._adapter = adapter
        self._target_type = target_type
        self._target_id = target_id
        self._target_to = target_id

    def To(self, target_type: str = None, target_id: str = None) -> 'SendDSL':
        if target_id is None and target_type is not None:
            target_id = target_type
            target_type = None

        return self.__class__(self._adapter, target_type, target_id)

    def __getattr__(self, name: str):
        def wrapper(*args, **kwargs):
            return asyncio.create_task(
                self._adapter._real_send(
                    target_type=self._target_type,
                    target_id=self._target_id,
                    action=name,
                    data={
                        "args": args,
                        "kwargs": kwargs
                    }
                )
            )
        return wrapper


class BaseAdapter:
    def __init__(self):
        self._handlers = defaultdict(list)
        self._middlewares = []

        # 检测是否有 Send 子类定义
        if not hasattr(self.__class__, 'Send') or not issubclass(self.__class__.Send, SendDSL):
            raise TypeError(f"{self.__class__.__name__} 必须定义 Send 嵌套类并继承 SendDSL")

        # 绑定当前适配器的 Send 实例
        self.Send = self.__class__.Send(self)

    def on(self, event_type: str = "*"):
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            self._handlers[event_type].append(wrapper)
            return wrapper
        return decorator

    def middleware(self, func: Callable):
        self._middlewares.append(func)
        return func

    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError

    async def start(self):
        raise NotImplementedError

    async def shutdown(self):
        raise NotImplementedError

    def add_handler(self, *args):
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
    async def emit(self, event_type: str, data: Any):
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

    async def send(self, target_type: str, target_id: str, message: Any, **kwargs):
        method_name = kwargs.pop("method", "Text")
        method = getattr(self.Send.To(target_type, target_id), method_name, None)
        if not method:
            raise AttributeError(f"未找到 {method_name} 方法，请确保已在 Send 类中定义")
        return await method(text=message, **kwargs)


class AdapterManager:
    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}
        self._adapter_instances: Dict[Type[BaseAdapter], BaseAdapter] = {}
        self._platform_to_instance: Dict[str, BaseAdapter] = {}
        self._started_instances: Set[BaseAdapter] = set()

    def register(self, platform: str, adapter_class: Type[BaseAdapter]) -> bool:
        if not issubclass(adapter_class, BaseAdapter):
            raise TypeError("适配器必须继承自BaseAdapter")
        from . import sdk

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

    async def startup(self, platforms: List[str] = None):
        if platforms is None:
            platforms = list(self._adapters.keys())

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

    async def _run_adapter(self, adapter: BaseAdapter, platform: str):
        from . import sdk

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
                    sdk.logger.info(f"适配器 {platform}（实例ID: {id(adapter)}）已启动")
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

    async def shutdown(self):
        for adapter in self._adapters.values():
            await adapter.shutdown()

    def get(self, platform: str) -> BaseAdapter:
        platform_lower = platform.lower()
        for registered, instance in self._adapters.items():
            if registered.lower() == platform_lower:
                return instance
        return None

    def __getattr__(self, platform: str) -> BaseAdapter:
        platform_lower = platform.lower()
        for registered, instance in self._adapters.items():
            if registered.lower() == platform_lower:
                return instance
        raise AttributeError(f"平台 {platform} 的适配器未注册")

    @property
    def platforms(self) -> list:
        return list(self._adapters.keys())


adapter = AdapterManager()
SendDSL = SendDSLBase
