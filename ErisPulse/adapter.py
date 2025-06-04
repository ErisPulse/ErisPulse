import functools
import asyncio
from typing import Callable, Any, Dict, List, Type
from collections import defaultdict

class BaseAdapter:
    def __init__(self):
        self._handlers = defaultdict(list)
        self._middlewares = []

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

    async def send(self, target: Any, message: Any, **kwargs):
        raise NotImplementedError

    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError

    async def emit(self, event_type: str, data: Any):
        for middleware in self._middlewares:
            data = await middleware(data)

        for handler in self._handlers.get(event_type, []):
            await handler(data)

class AdapterManager:
    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}

    def register(self, platform: str, adapter_class: Type[BaseAdapter]) -> bool:
        if not issubclass(adapter_class, BaseAdapter):
            raise TypeError("适配器必须继承自BaseAdapter")
        from . import sdk
        self._adapters[platform] = adapter_class(sdk)
        return True

    async def startup(self):
        for platform, adapter in self._adapters.items():
            asyncio.create_task(self._run_adapter(adapter, platform))

    async def _run_adapter(self, adapter: BaseAdapter, platform: str):
        try:
            await adapter.start()
        except Exception as e:
            self.logger.error(f"平台 {platform} 停止时遇到了错误： {e}")

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
adapterbase = BaseAdapter