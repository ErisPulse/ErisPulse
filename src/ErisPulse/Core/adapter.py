"""
ErisPulse 适配器系统

提供平台适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。
"""

import functools
import asyncio
import inspect
import time
from typing import (
    Callable, Any, Dict, List, Type, Optional, Set, Union
)
from collections import defaultdict
from .logger import logger
from .Bases.adapter import BaseAdapter
from .config import config
from .lifecycle import lifecycle
from .Bases.manager import ManagerBase

class AdapterManager(ManagerBase):
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
        self._sdk = None
        
        # Bot状态存储 - {platform: {bot_id: {"status": str, "last_active": float, "info": dict}}}
        self._bots: Dict[str, Dict[str, Dict]] = {}
        
    def set_sdk_ref(self, sdk) -> bool:
        """
        设置 SDK 引用
        
        :param sdk: SDK 实例
        :return: 是否设置成功
        """
        try:
            self._sdk = sdk
            return True
        except Exception as e:
            logger.error(f"设置SDK引用失败: {e}")
            return False
        
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
        else:
            # 创建适配器实例
            # 检查适配器类 __init__ 方法的参数
            init_signature = inspect.signature(adapter_class.__init__)
            params = [p for p in init_signature.parameters.values() if p.name != 'self']
            
            sdk_to_use = self._sdk
            if sdk_to_use is None:
                from .. import sdk
                sdk_to_use = sdk
                
            # 根据参数情况创建实例
            if params:
                instance = adapter_class(sdk_to_use)
            else:
                instance = adapter_class()

            self._adapters[platform] = instance
        
        return True
    
    async def startup(self, platforms: Optional[Union[str, List[str]]] = None) -> None:
        """
        启动指定的适配器

        :param platforms: 要启动的平台，可以是单个平台名、平台名列表或None（表示所有平台）
        :raises ValueError: 当平台未注册时抛出

        :example:
        >>> # 启动所有适配器
        >>> await adapter.startup()
        >>> # 启动单个适配器
        >>> await adapter.startup("Platform1")
        >>> # 启动多个适配器
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
        from ..runtime import get_server_config
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

        # 将所有Bot标记为离线
        for platform_name, bots in self._bots.items():
            for bot_id, bot_info in bots.items():
                bot_info["status"] = "offline"

        # 清空已启动实例集合
        self._started_instances.clear()
        
        # 清空事件处理器
        self._onebot_handlers.clear()
        self._raw_handlers.clear()
        self._onebot_middlewares.clear()

        # 提交适配器关闭完成事件
        await lifecycle.submit_event(
            "adapter.stopped",
            msg="适配器关闭完成"
        )
    
    def clear(self) -> None:
        """
        清除所有适配器实例和信息
        
        {!--< internal-use >!--}
        此方法用于反初始化时完全重置适配器管理器状态
        {!--< /internal-use >!--}
        """
        # 清除所有适配器实例
        self._adapters.clear()
        
        # 清除适配器信息
        self._adapter_info.clear()
        
        # 清除所有处理器
        self._onebot_handlers.clear()
        self._raw_handlers.clear()
        self._onebot_middlewares.clear()
        
        # 清除Bot状态
        self._bots.clear()
        
        logger.debug("适配器管理器已完全清理")

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
        logger.debug(f"平台适配器 {platform} 已注册并{status}")
        return True

    def exists(self, platform: str) -> bool:
        """
        检查平台是否存在

        :param platform: 平台名称
        :return: [bool] 平台是否存在
        """
        # 检查平台是否已注册（在 _adapters 中）
        return platform in self._adapters

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
        # 启用平台时自动在配置中注册
        if platform not in self._adapters:
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
        # 禁用平台时自动在配置中注册
        if platform not in self._adapters:
            logger.error(f"平台 {platform} 不存在")
            return False
        
        config.setConfig(f"ErisPulse.adapters.status.{platform}", False)
        logger.info(f"平台 {platform} 已禁用")
        return True

    def unregister(self, platform: str) -> bool:
        """
        取消注册适配器
        
        :param platform: 平台名称
        :return: 是否取消成功
        
        {!--< internal-use >!--}
        注意：此方法仅取消注册，不关闭已启动的适配器
        {!--< /internal-use >!--}
        """
        if platform not in self._adapters:
            logger.warning(f"平台 {platform} 未注册")
            return False
        
        # 移除适配器实例
        self._adapters.pop(platform)
        
        logger.info(f"平台 {platform} 已取消注册")
        return True
    
    def list_registered(self) -> List[str]:
        """
        列出所有已注册的平台
        
        :return: 平台名称列表
        """
        return list(self._adapters.keys())
    
    def list_items(self) -> Dict[str, bool]:
        """
        列出所有平台适配器状态
        
        :return: {平台名: 是否启用} 字典
        """
        return config.getConfig("ErisPulse.adapters.status", {})
    
    # 兼容性方法 - 保持向后兼容
    def list_adapters(self) -> Dict[str, bool]:
        """
        列出所有平台适配器状态
        
        {!--< deprecated >!--} 请使用 list_items() 代替
        
        :return: [Dict[str, bool]] 平台适配器状态字典
        """
        return self.list_items()

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

        # 处理 meta 事件：适配器通过 meta 事件提交 Bot 上下线信息
        # 同时也处理普通事件中的 self 字段（自动发现Bot）
        self_info = data.get("self")
        if isinstance(self_info, dict) and "user_id" in self_info:
            if event_type == "meta":
                detail_type = data.get("detail_type", "")
                if detail_type == "connect":
                    # Bot 连接上线
                    is_new_bot = self._auto_register_bot(platform, self_info)
                    bot_id = str(self_info["user_id"])
                    await lifecycle.submit_event(
                        "adapter.bot.online",
                        msg=f"Bot {platform}/{bot_id} 上线",
                        data={
                            "platform": platform,
                            "bot_id": bot_id,
                            "info": self._bots.get(platform, {}).get(bot_id, {}).get("info", {}),
                            "status": "online"
                        }
                    )
                elif detail_type == "disconnect":
                    # Bot 断开连接
                    self._update_bot_status(platform, str(self_info["user_id"]), "offline")
                elif detail_type == "heartbeat":
                    # 心跳，更新活跃时间
                    self._update_bot_heartbeat(platform, self_info)
            else:
                # 普通事件：自动发现Bot并更新活跃时间
                self._auto_register_bot(platform, self_info)

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

    # ==================== Bot状态管理 ====================

    def _auto_register_bot(self, platform: str, self_info: dict) -> bool:
        """
        {!--< internal-use >!--}
        自动注册Bot（从OB12事件self字段提取），提取所有扩展字段作为Bot元信息

        self字段标准扩展：
        - self.user_id (必须) - Bot用户ID
        - self.user_name (可选) - Bot昵称
        - self.avatar (可选) - Bot头像URL
        - self.account_id (可选) - 多账户标识

        :param platform: 平台名称
        :param self_info: 事件中的self字段内容
        :return: 是否为新注册的Bot
        """
        bot_id = str(self_info.get("user_id", ""))
        if not bot_id:
            return False

        if platform not in self._bots:
            self._bots[platform] = {}

        is_new = bot_id not in self._bots[platform]

        # 从self字段提取元信息（ErisPulse扩展的标准字段）
        bot_meta = {}
        if "user_name" in self_info:
            bot_meta["user_name"] = self_info["user_name"]
        if "nickname" in self_info:
            bot_meta["nickname"] = self_info["nickname"]
        if "avatar" in self_info:
            bot_meta["avatar"] = self_info["avatar"]
        if "account_id" in self_info:
            bot_meta["account_id"] = self_info["account_id"]

        existing = self._bots[platform].get(bot_id, {})

        # 合并已有元信息（新事件可更新元信息）
        existing_meta = existing.get("info", {})
        existing_meta.update(bot_meta)

        self._bots[platform][bot_id] = {
            "status": "online",
            "last_active": time.time(),
            "info": existing_meta
        }

        if is_new:
            logger.debug(f"自动发现Bot: {platform}/{bot_id}")

        return is_new

    def _update_bot_status(self, platform: str, bot_id: str, status: str) -> None:
        """
        {!--< internal-use >!--}
        更新Bot状态

        :param platform: 平台名称
        :param bot_id: Bot用户ID
        :param status: 状态值（online/offline）
        """
        if platform not in self._bots:
            self._bots[platform] = {}

        if bot_id not in self._bots[platform]:
            self._bots[platform][bot_id] = {"status": status, "last_active": time.time(), "info": {}}
        else:
            old_status = self._bots[platform][bot_id].get("status")
            self._bots[platform][bot_id]["status"] = status
            if old_status != status:
                logger.debug(f"Bot状态变更: {platform}/{bot_id} {old_status} -> {status}")

        if status == "offline":
            asyncio.ensure_future(lifecycle.submit_event(
                "adapter.bot.offline",
                msg=f"Bot {platform}/{bot_id} 离线",
                data={"platform": platform, "bot_id": bot_id, "status": "offline"}
            ))

    def _update_bot_heartbeat(self, platform: str, self_info: dict) -> None:
        """
        {!--< internal-use >!--}
        更新Bot心跳（更新活跃时间和元信息）

        :param platform: 平台名称
        :param self_info: 事件中的self字段内容
        """
        bot_id = str(self_info.get("user_id", ""))
        if not bot_id:
            return

        if platform not in self._bots:
            self._bots[platform] = {}

        if bot_id in self._bots[platform]:
            self._bots[platform][bot_id]["last_active"] = time.time()
            # 心跳也可更新元信息
            bot_meta = {}
            for key in ("user_name", "nickname", "avatar", "account_id"):
                if key in self_info:
                    bot_meta[key] = self_info[key]
            if bot_meta:
                self._bots[platform][bot_id].setdefault("info", {}).update(bot_meta)

    def get_bot_info(self, platform: str, bot_id: str) -> Optional[Dict]:
        """
        获取Bot详细信息

        :param platform: 平台名称
        :param bot_id: Bot用户ID
        :return: Bot信息字典，包含status/last_active/info，不存在则返回None

        :example:
        >>> info = adapter.get_bot_info("telegram", "123456")
        >>> # {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}
        """
        return self._bots.get(platform, {}).get(bot_id)

    def list_bots(self, platform: Optional[str] = None) -> Dict[str, Dict[str, Dict]]:
        """
        列出Bot信息

        :param platform: 平台名称，None表示列出所有平台的Bot
        :return: Bot信息字典 {platform: {bot_id: {status, last_active, info}}}

        :example:
        >>> # 列出所有Bot
        >>> all_bots = adapter.list_bots()
        >>> # 列出指定平台的Bot
        >>> tg_bots = adapter.list_bots("telegram")
        """
        if platform is not None:
            return {platform: dict(self._bots.get(platform, {}))}
        return {p: dict(bots) for p, bots in self._bots.items()}

    def is_bot_online(self, platform: str, bot_id: str) -> bool:
        """
        检查Bot是否在线

        :param platform: 平台名称
        :param bot_id: Bot用户ID
        :return: Bot是否在线

        :example:
        >>> if adapter.is_bot_online("telegram", "123456"):
        ...     print("Bot在线")
        """
        bot_info = self._bots.get(platform, {}).get(bot_id)
        if bot_info is None:
            return False
        return bot_info.get("status") == "online"

    def get_status_summary(self) -> Dict[str, Any]:
        """
        获取适配器与Bot的完整状态摘要

        返回所有适配器的运行状态及各适配器下的Bot状态，便于WebUI展示。

        :return: 状态摘要字典

        :example:
        >>> summary = adapter.get_status_summary()
        >>> # {
        >>> #     "adapters": {
        >>> #         "telegram": {
        >>> #             "status": "started",
        >>> #             "bots": {
        >>> #                 "123456": {
        >>> #                     "status": "online",
        >>> #                     "last_active": 1712345678.0,
        >>> #                     "info": {"nickname": "MyBot"}
        >>> #                 }
        >>> #             }
        >>> #         }
        >>> #     }
        >>> # }
        """
        adapters_summary = {}
        for platform_name in self._adapters:
            adapter_instance = self._adapters[platform_name]
            if adapter_instance in self._started_instances:
                adapter_status = "started"
            else:
                adapter_status = "stopped"

            adapters_summary[platform_name] = {
                "status": adapter_status,
                "bots": dict(self._bots.get(platform_name, {}))
            }

        return {
            "adapters": adapters_summary
        }

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

    def is_running(self, platform: str) -> bool:
        """
        检查适配器是否正在运行（已启动）

        :param platform: 平台名称
        :return: 适配器是否正在运行

        :example:
        >>> if adapter.is_running("onebot11"):
        >>>     print("onebot11 适配器正在运行")
        """
        adapter_instance = self.get(platform)
        if adapter_instance is None:
            return False
        return adapter_instance in self._started_instances

    def list_running(self) -> List[str]:
        """
        列出所有正在运行的适配器（已启动）

        :return: 平台名称列表

        :example:
        >>> running = adapter.list_running()
        >>> print("正在运行的适配器:", running)
        """
        running_platforms = []
        for platform, instance in self._adapters.items():
            if instance in self._started_instances:
                running_platforms.append(platform)
        return running_platforms


    def list_sends(self, platform: str) -> List[str]:
        """
        列出指定平台支持的发送方法

        :param platform: 平台名称
        :return: 发送方法名列表
        :raises ValueError: 当平台不存在时抛出

        :example:
        >>> methods = adapter.list_sends("onebot11")
        >>> print(methods)  # ["Text", "Image", "Voice", ...]
        """
        adapter_instance = self.get(platform)
        if adapter_instance is None:
            raise ValueError(f"平台 {platform} 不存在")
        
        # 获取Send类
        send_class = adapter_instance.Send.__class__
        
        # 获取SendDSL基类的所有方法名称
        from .Bases.adapter import SendDSL
        base_dsl_methods = set(dir(SendDSL))
        
        # 获取Send类中定义的方法，排除基类方法和私有方法
        send_methods = []
        for name in dir(send_class):
            # 跳过私有方法和魔法方法
            if name.startswith('_'):
                continue
            # 跳过基类中已有的方法
            if name in base_dsl_methods:
                continue
            # 获取属性，确保是方法或可调用对象
            attr = getattr(send_class, name)
            if callable(attr):
                send_methods.append(name)
        
        return sorted(send_methods)

    def send_info(self, platform: str, method_name: str) -> Dict[str, Any]:
        """
        获取指定发送方法的详细信息

        :param platform: 平台名称
        :param method_name: 发送方法名
        :return: 方法信息字典，包含name, parameters, return_type, docstring
        :raises ValueError: 当平台或方法不存在时抛出

        :example:
        >>> info = adapter.send_info("onebot11", "Text")
        >>> print(info)
        # {
        #     "name": "Text",
        #     "parameters": [
        #         {"name": "text", "type": "str", "default": null, "annotation": "str"}
        #     ],
        #     "return_type": "Awaitable[Any]",
        #     "docstring": "发送文本消息..."
        # }
        """
        adapter_instance = self.get(platform)
        if adapter_instance is None:
            raise ValueError(f"平台 {platform} 不存在")
        
        # 获取Send类
        send_class = adapter_instance.Send.__class__
        
        # 检查方法是否存在
        if not hasattr(send_class, method_name):
            raise ValueError(f"方法 {method_name} 不存在")
        
        method = getattr(send_class, method_name)
        
        # 提取参数信息
        parameters = []
        if inspect.ismethod(method) or inspect.isfunction(method):
            sig = inspect.signature(method)
            for param_name, param in sig.parameters.items():
                # 跳过self参数
                if param_name == 'self':
                    continue
                
                param_info = {
                    "name": param_name,
                    "type": None,
                    "default": None,
                    "annotation": None
                }
                
                # 获取类型注解
                if param.annotation != inspect.Parameter.empty:
                    param_info["annotation"] = str(param.annotation)
                    param_info["type"] = str(param.annotation)
                
                # 获取默认值
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = str(param.default)
                
                parameters.append(param_info)
        
        # 提取返回类型
        return_type = None
        if inspect.ismethod(method) or inspect.isfunction(method):
            sig = inspect.signature(method)
            if sig.return_annotation != inspect.Signature.empty:
                return_type = str(sig.return_annotation)
        
        # 提取文档字符串
        docstring = inspect.getdoc(method) or ""
        
        return {
            "name": method_name,
            "parameters": parameters,
            "return_type": return_type,
            "docstring": docstring
        }

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

adapter : AdapterManager = AdapterManager()

__all__ = [
    "adapter"
]
