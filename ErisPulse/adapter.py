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

    def To(self, target_type: str, target_id: str) -> 'SendDSL':
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

    def on(self, event_type: str):
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

    async def emit(self, event_type: str, data: Any):
        for middleware in self._middlewares:
            data = await middleware(data)

        for handler in self._handlers.get(event_type, []):
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
        self._started_instances: Set[BaseAdapter] = set()
    def register(self, platform: str, adapter_class: Type[BaseAdapter]) -> bool:
        if not issubclass(adapter_class, BaseAdapter):
            raise TypeError("适配器必须继承自BaseAdapter")
        from . import sdk

        if adapter_class in self._adapter_instances:
            self._adapters[platform] = self._adapter_instances[adapter_class]
        else:
            instance = adapter_class(sdk)
            self._adapters[platform] = instance
            self._adapter_instances[adapter_class] = instance

        return True

    async def startup(self, platforms: List[str] = None):
        if platforms is None:
            platforms = list(self._adapters.keys())

        for platform in platforms:
            if platform not in self._adapters:
                raise ValueError(f"平台 {platform} 未注册")
            adapter = self._adapters[platform]

            # 如果该实例已经被启动过，跳过
            if adapter in self._started_instances:
                continue

            self._started_instances.add(adapter)
            asyncio.create_task(self._run_adapter(adapter, platform))

    async def _run_adapter(self, adapter: BaseAdapter, platform: str):
        from . import sdk
        retry_count = 0
        max_retry = 3
        while retry_count < max_retry:
            try:
                await adapter.start()
                sdk.logger.debug(f"尝试启动适配器 {platform}，实例ID: {id(adapter)}")
                if adapter in self._started_instances:
                    sdk.logger.info(f"适配器 {platform}（实例ID: {id(adapter)}）已启动，跳过")
                break
            except Exception as e:
                retry_count += 1
                sdk.logger.error(f"平台 {platform} 启动失败（第{retry_count}次重试）: {e}")
                try:
                    await adapter.shutdown()
                except Exception as stop_err:
                    sdk.logger.warning(f"停止适配器失败: {stop_err}")

                if retry_count >= max_retry:
                    sdk.logger.critical(f"平台 {platform} 达到最大重试次数，放弃重启")
                    sdk.raiserr.AdapterStartFailedError(f"平台 {platform} 适配器无法重写启动: {e}")

    async def shutdown(self):
        for adapter in self._adapters.values():
            await adapter.shutdown()

    def get(self, platform: str) -> BaseAdapter:
        return self._adapters.get(platform)

    def __getattr__(self, platform: str) -> BaseAdapter:
        if platform not in self._adapters:
            raise AttributeError(f"平台 {platform} 的适配器未注册")
        return self._adapters[platform]

    @property
    def platforms(self) -> list:
        return list(self._adapters.keys())


adapter = AdapterManager()
SendDSL = SendDSLBase
