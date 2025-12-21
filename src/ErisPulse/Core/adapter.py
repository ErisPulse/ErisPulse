"""
ErisPulse 适配器系统

提供平台适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。
"""

import functools
import asyncio
from typing import (
    Callable, Any, Dict, List, Type, Optional, Set
)
from collections import defaultdict
from .logger import logger
from .Bases.adapter import BaseAdapter
from .config import config
from .lifecycle import lifecycle

class AdapterManager:
    """
    适配器管理器

    管理多个平台适配器的注册、启动和关闭，提供与模块管理器一致的接口

    {!--< tips >!--}
    1. 通过register方法注册适配器
    2. 通过startup方法启动适配器
    3. 通过shutdown方法关闭所有适配器
    4. 通过on装饰器注册OneBot12协议事件处理器
    {!--< /tips >!--}
    """

    def __init__(self):
        # 适配器存储 - 简化数据结构
        self._adapters: Dict[str, BaseAdapter] = {}  # 平台名到实例的映射
        self._started_instances: Set[BaseAdapter] = set()  # 已启动的实例
        self._adapter_info: Dict[str, Dict] = {}  # 适配器信息

        # OneBot12事件处理器
        self._onebot_handlers = defaultdict(list)
        self._onebot_middlewares = []
        # 原生事件处理器
        self._raw_handlers = defaultdict(list)

    # ==================== 适配器注册与管理 ====================

    def register(self, platform: str, adapter_class: Type[BaseAdapter], adapter_info: Optional[Dict] = None) -> bool:
        """
        注册新的适配器类（标准化注册方法）

        :param platform: 平台名称
        :param adapter_class: 适配器类
        :param adapter_info: 适配器信息
        :return: 注册是否成功

        :raises TypeError: 当适配器类无效时抛出

        :example:
        >>> adapter.register("MyPlatform", MyPlatformAdapter)
        """
        logger.info(f"注册适配器 {platform}（{adapter_class.__name__}）")
        if not issubclass(adapter_class, BaseAdapter):
            raise TypeError("适配器必须继承自BaseAdapter，否则我们无法加载这个适配器，它会导致未知的错误")

        # 检查是否已存在该平台的适配器
        if platform in self._adapters:
            logger.warning(f"平台 {platform} 已存在，将覆盖原适配器")
        
        if adapter_info:
            self._adapter_info[platform] = adapter_info

        # 检查是否已存在相同类的适配器实例
        existing_instance = None
        for existing_platform, existing_adapter in self._adapters.items():
            if existing_adapter.__class__ == adapter_class:
                existing_instance = existing_adapter
                break

        # 如果存在相同类的适配器实例，直接绑定到已注册的实例
        if existing_instance is not None:
            self._adapters[platform] = existing_instance
            logger.debug(f"适配器 {platform} 已绑定到已注册的实例 {existing_platform}")
        else:
            # 创建适配器实例
            from .. import sdk
            instance = adapter_class(sdk)
            self._adapters[platform] = instance
            logger.debug(f"适配器 {platform} 注册成功")
        
        # 注册平台名称的多种大小写形式作为属性
        self._register_platform_attributes(platform, self._adapters[platform])
        
        return True
    
    def _register_platform_attributes(self, platform: str, instance: BaseAdapter) -> None:
        """
        注册平台名称的多种大小写形式作为属性
        
        :param platform: 平台名称
        :param instance: 适配器实例
        """
        if len(platform) <= 10:
            from itertools import product
            combinations = [''.join(c) for c in product(*[(ch.lower(), ch.upper()) for ch in platform])]
            for name in set(combinations):
                setattr(self, name, instance)
        else:
            logger.warning(f"平台名 {platform} 过长，如果您是开发者，请考虑使用更短的名称")
            setattr(self, platform.lower(), instance)
            setattr(self, platform.upper(), instance)
            setattr(self, platform.capitalize(), instance)

    async def startup(self, platforms = None) -> None:
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
        if not isinstance(platforms, list):
            platforms = [platforms]
        for platform in platforms:
            if platform not in self._adapters:
                raise ValueError(f"平台 {platform} 未注册")

        logger.info(f"启动适配器 {platforms}")

        # 提交适配器启动开始事件
        await lifecycle.submit_event(
            "adapter.start",
            msg="开始启动适配器",
            data={
                "platforms": platforms
            }
        )

        from .router import router
        from ._self_config import get_server_config
        server_config = get_server_config()

        host = server_config["host"]
        port = server_config["port"]
        ssl_cert = server_config.get("ssl_certfile", None)
        ssl_key = server_config.get("ssl_keyfile", None)

        # 启动服务器
        await router.start(
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

        if not getattr(adapter, "_starting_lock", None):
            adapter._starting_lock = asyncio.Lock()

        async with adapter._starting_lock:
            # 再次确认是否已经被启动
            if adapter in self._started_instances:
                logger.info(f"适配器 {platform}（实例ID: {id(adapter)}）已被其他协程启动，跳过")
                return

            retry_count = 0
            fixed_delay = 3 * 60 * 60
            backoff_intervals = [60, 10 * 60, 30 * 60, 60 * 60]

            # 提交适配器状态变化事件（starting）
            await lifecycle.submit_event(
                "adapter.status.change",
                msg=f"适配器 {platform} 状态变化: starting",
                data={
                    "platform": platform,
                    "status": "starting",
                    "retry_count": retry_count
                }
            )

            while True:
                try:
                    await adapter.start()
                    self._started_instances.add(adapter)

                    # 提交适配器状态变化事件（started）
                    await lifecycle.submit_event(
                        "adapter.status.change",
                        msg=f"适配器 {platform} 状态变化: started",
                        data={
                            "platform": platform,
                            "status": "started"
                        }
                    )

                    return
                except Exception as e:
                    retry_count += 1
                    logger.error(f"平台 {platform} 启动失败（第{retry_count}次重试）: {e}")

                    # 提交适配器状态变化事件（start_failed）
                    await lifecycle.submit_event(
                        "adapter.status.change",
                        msg=f"适配器 {platform} 状态变化: start_failed",
                        data={
                            "platform": platform,
                            "status": "start_failed",
                            "retry_count": retry_count,
                            "error": str(e)
                        }
                    )

                    try:
                        await adapter.shutdown()
                    except Exception as stop_err:
                        logger.warning(f"停止适配器失败: {stop_err}")

                    # 计算等待时间
                    if retry_count <= len(backoff_intervals):
                        wait_time = backoff_intervals[retry_count - 1]
                    else:
                        wait_time = fixed_delay

                    logger.info(f"将在 {wait_time // 60} 分钟后再次尝试重启 {platform}")
                    await asyncio.sleep(wait_time)
    async def shutdown(self) -> None:
        """
        关闭所有适配器
        """
        # 提交适配器关闭开始事件
        await lifecycle.submit_event(
            "adapter.stop",
            msg="开始关闭适配器",
            data={}
        )

        for adapter in self._adapters.values():
            await adapter.shutdown()

        from .router import router
        await router.stop()

        # 提交适配器关闭完成事件
        await lifecycle.submit_event(
            "adapter.stopped",
            msg="适配器关闭完成"
        )

    # ==================== 适配器配置管理 ====================

    def _config_register(self, platform: str, enabled: bool = False) -> bool:
        """
        注册新平台适配器（仅当平台不存在时注册）

        :param platform: 平台名称
        :param enabled: [bool] 是否启用适配器
        :return: [bool] 操作是否成功
        """
        if self.exists(platform):
            return True

        # 平台不存在，进行注册
        config.setConfig(f"ErisPulse.adapters.status.{platform}", enabled)
        status = "启用" if enabled else "禁用"
        logger.info(f"平台适配器 {platform} 已注册并{status}")
        return True

    def exists(self, platform: str) -> bool:
        """
        检查平台是否存在

        :param platform: 平台名称
        :return: [bool] 平台是否存在
        """
        # 检查平台是否在配置中注册
        adapter_statuses = config.getConfig("ErisPulse.adapters.status", {})
        return platform in adapter_statuses

    def is_enabled(self, platform: str) -> bool:
        """
        检查平台适配器是否启用

        :param platform: 平台名称
        :return: [bool] 平台适配器是否启用
        """
        # 不使用默认值，如果配置不存在则返回 None
        status = config.getConfig(f"ErisPulse.adapters.status.{platform}")

        # 如果状态不存在，说明是新适配器
        if status is None:
            return False  # 新适配器默认不启用，需要在初始化时处理

        # 处理字符串形式的布尔值
        if isinstance(status, str):
            return status.lower() not in ('false', '0', 'no', 'off')

        return bool(status)

    def enable(self, platform: str) -> bool:
        """
        启用平台适配器

        :param platform: 平台名称
        :return: [bool] 操作是否成功
        """
        if not self.exists(platform):
            logger.error(f"平台 {platform} 不存在")
            return False

        config.setConfig(f"ErisPulse.adapters.status.{platform}", True)
        logger.info(f"平台 {platform} 已启用")
        return True

    def disable(self, platform: str) -> bool:
        """
        禁用平台适配器

        :param platform: 平台名称
        :return: [bool] 操作是否成功
        """
        if not self.exists(platform):
            logger.error(f"平台 {platform} 不存在")
            return False

        config.setConfig(f"ErisPulse.adapters.status.{platform}", False)
        logger.info(f"平台 {platform} 已禁用")
        return True

    def list_adapters(self) -> Dict[str, bool]:
        """
        列出所有平台适配器状态

        :return: [Dict[str, bool]] 平台适配器状态字典
        """
        return config.getConfig("ErisPulse.adapters.status", {})

    # ==================== 事件处理与消息发送 ====================

    def on(self, event_type: str = "*", *, raw: bool = False, platform: Optional[str] = None) -> Callable[[Callable], Callable]:
        """
        OneBot12协议事件监听装饰器

        :param event_type: OneBot12事件类型
        :param raw: 是否监听原生事件
        :param platform: 指定平台，None表示监听所有平台
        :return: 装饰器函数

        :example:
        >>> # 监听OneBot12标准事件（所有平台）
        >>> @sdk.adapter.on("message")
        >>> async def handle_message(data):
        >>>     print(f"收到OneBot12消息: {data}")
        >>>
        >>> # 监听特定平台的OneBot12标准事件
        >>> @sdk.adapter.on("message", platform="onebot11")
        >>> async def handle_onebot11_message(data):
        >>>     print(f"收到OneBot11标准消息: {data}")
        >>>
        >>> # 监听平台原生事件
        >>> @sdk.adapter.on("message", raw=True, platform="onebot11")
        >>> async def handle_raw_message(data):
        >>>     print(f"收到OneBot11原生事件: {data}")
        >>>
        >>> # 监听所有平台的原生事件
        >>> @sdk.adapter.on("message", raw=True)
        >>> async def handle_all_raw_message(data):
        >>>     print(f"收到原生事件: {data}")
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            # 创建带元信息的处理器包装器
            handler_wrapper = {
                'func': wrapper,
                'platform': platform
            }

            if raw:
                self._raw_handlers[event_type].append(handler_wrapper)
            else:
                self._onebot_handlers[event_type].append(handler_wrapper)
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

        :param data: 符合OneBot12标准的事件数据

        :example:
        >>> await sdk.adapter.emit({
        >>>     "id": "123",
        >>>     "time": 1620000000,
        >>>     "type": "message",
        >>>     "detail_type": "private",
        >>>     "message": [{"type": "text", "data": {"text": "Hello"}}],
        >>>     "platform": "myplatform",
        >>>     "myplatform_raw": {...平台原生事件数据...},
        >>>     "myplatform_raw_type": "text_message"
        >>> })
        """
        platform = data.get("platform", "unknown")
        event_type = data.get("type", "unknown")
        platform_raw = data.get(f"{platform}_raw", {})
        raw_event_type = data.get(f"{platform}_raw_type")

        # 先执行OneBot12中间件
        processed_data = data
        for middleware in self._onebot_middlewares:
            processed_data = await middleware(processed_data)

        # 分发到OneBot12事件处理器
        handlers_to_call = []

        # 处理特定事件类型的处理器
        if event_type in self._onebot_handlers:
            handlers_to_call.extend(self._onebot_handlers[event_type])

        # 处理通配符处理器
        handlers_to_call.extend(self._onebot_handlers.get("*", []))

        # 调用符合条件的标准事件处理器
        for handler_wrapper in handlers_to_call:
            handler_platform = handler_wrapper.get('platform')
            # 如果处理器没有指定平台，或者指定的平台与当前事件平台匹配
            if handler_platform is None or handler_platform == platform:
                await handler_wrapper['func'](processed_data)

        # 只有当存在原生事件数据时才分发原生事件
        if raw_event_type and platform_raw is not None:
            raw_handlers_to_call = []

            # 处理特定原生事件类型的处理器
            if raw_event_type in self._raw_handlers:
                raw_handlers_to_call.extend(self._raw_handlers[raw_event_type])

            # 处理原生事件的通配符处理器
            raw_handlers_to_call.extend(self._raw_handlers.get("*", []))

            # 调用符合条件的原生事件处理器
            for handler_wrapper in raw_handlers_to_call:
                handler_platform = handler_wrapper.get('platform')
                # 如果处理器没有指定平台，或者指定的平台与当前事件平台匹配
                if handler_platform is None or handler_platform == platform:
                    await handler_wrapper['func'](platform_raw)

    # ==================== 工具方法 ====================

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

    @property
    def platforms(self) -> List[str]:
        """
        获取所有已注册的平台列表

        :return: 平台名称列表

        :example:
        >>> print("已注册平台:", adapter.platforms)
        """
        return list(self._adapters.keys())

    def __getattr__(self, platform: str) -> BaseAdapter:
        """
        通过属性访问获取适配器实例

        :param platform: 平台名称
        :return: 适配器实例
        :raises AttributeError: 当平台不存在或未启用时
        """
        adapter_instance = self.get(platform)
        if adapter_instance is None:
            raise AttributeError(f"平台 {platform} 不存在或未启用")
        return adapter_instance

    def __contains__(self, platform: str) -> bool:
        """
        检查平台是否存在且处于启用状态

        :param platform: 平台名称
        :return: [bool] 平台是否存在且启用
        """
        return self.exists(platform) and self.is_enabled(platform)

adapter = AdapterManager()

__all__ = [
    "adapter"
]
