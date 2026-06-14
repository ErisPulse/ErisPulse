"""
ErisPulse 适配器系统

提供平台适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。
"""

import asyncio
import functools
import inspect
import time
import warnings
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from .Bases.adapter import BaseAdapter
from .config import config
from .i18n import i18n
from .lifecycle import lifecycle
from .logger import logger

_msg_logger = logger.get_child("Message", relative=False)
from ..runtime.context import current_owner, handler_waits
from .Bases.manager import ManagerBase
from .constants import (
    ADAPTER_RETRY_BACKOFF_INTERVALS,
    ADAPTER_RETRY_FIXED_DELAY_SECS,
    CONFIG_KEY_ADAPTER_STATUS,
    CONFIG_KEY_ADAPTER_STATUS_OF,
    DEFAULT_ADAPTER_ENABLED,
    HANDLER_SLOW_THRESHOLD_SECS,
)


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

    @staticmethod
    def _is_subclass(cls: type, base_cls: type) -> bool:
        try:
            if issubclass(cls, base_cls):
                return True
        except TypeError:
            pass
        if base_cls.__name__ == cls.__name__:
            return False
        for parent in cls.__mro__:
            if (
                parent.__name__ == base_cls.__name__
                and parent.__module__ == base_cls.__module__
            ):
                return True
        return False

    def __init__(self):
        # 适配器存储
        self._adapters: dict[str, BaseAdapter] = {}  # 平台名到实例的映射
        self._started_instances: set[BaseAdapter] = set()  # 已启动的实例
        self._adapter_info: dict[str, dict] = {}  # 适配器信息

        # OneBot12事件处理器
        self._onebot_handlers = defaultdict(list)
        self._onebot_middlewares = []
        # 原生事件处理器
        self._raw_handlers = defaultdict(list)
        self._sdk = None

        # 后台任务追踪 - {platform: asyncio.Task}
        self._adapter_tasks: dict[str, asyncio.Task] = {}

        # Bot状态存储 - {platform: {bot_id: {"status": str, "last_active": float, "info": dict}}}
        self._bots: dict[str, dict[str, dict]] = {}

        # 标记是否正在关闭，避免重复提交离线事件
        self._is_being_shutdown = False

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
            logger.error(i18n.t("core.adapter.set_sdk_failed", error=e))
            return False

    # ==================== 适配器注册与管理 ====================

    def register(
        self,
        platform: str,
        adapter_class: type[BaseAdapter],
        adapter_info: dict | None = None,
    ) -> bool:
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
        if not self._is_subclass(adapter_class, BaseAdapter):
            raise TypeError(i18n.t("core.adapter.must_inherit_base"))

        # 检查是否已存在该平台的适配器
        if platform in self._adapters:
            logger.warning(i18n.t("core.adapter.platform_exists", platform=platform))

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
            try:
                # 创建适配器实例
                # 检查适配器类 __init__ 方法的参数
                init_signature = inspect.signature(adapter_class.__init__)
                params = [
                    p for p in init_signature.parameters.values() if p.name != "self"
                ]

                sdk_to_use = self._sdk
                if sdk_to_use is None:
                    from .. import sdk

                    sdk_to_use = sdk

                # 根据参数情况创建实例
                if params:
                    instance = adapter_class(sdk_to_use)
                else:
                    instance = adapter_class()

                instance._platform = platform
                self._adapters[platform] = instance
            except SystemExit as e:
                logger.error(
                    i18n.t(
                        "core.adapter.systemexit_skipped",
                        platform=platform,
                        code=e.code,
                    )
                )
                return False
            except Exception as e:
                logger.error(
                    i18n.t("core.adapter.create_failed", platform=platform, error=e)
                )
                return False

        return True

    async def startup(self, platforms: str | list[str] | None = None) -> None:
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
        skipped_platforms = []
        for platform in list(platforms):
            if platform not in self._adapters:
                logger.warning(i18n.t("core.adapter.not_registered", platform=platform))
                platforms.remove(platform)
                skipped_platforms.append(platform)

        logger.info(i18n.t("core.adapter.starting_platforms", platforms=platforms))

        await lifecycle.submit_event(
            "adapter.start",
            msg=i18n.t("core.adapter.start_msg"),
            data={"platforms": platforms},
        )

        scheduled_adapters = set()

        for platform in platforms:
            adapter = self._adapters[platform]

            # 如果该实例已经被启动或已调度，跳过
            if adapter in self._started_instances or adapter in scheduled_adapters:
                continue

            # 加入调度队列
            scheduled_adapters.add(adapter)
            task = asyncio.create_task(self._run_adapter(adapter, platform))
            self._adapter_tasks[platform] = task

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
                logger.info(
                    i18n.t(
                        "core.adapter.already_started",
                        platform=platform,
                        id=id(adapter),
                    )
                )
                return

            retry_count = 0
            fixed_delay = ADAPTER_RETRY_FIXED_DELAY_SECS
            backoff_intervals = ADAPTER_RETRY_BACKOFF_INTERVALS

            # 提交适配器状态变化事件（starting）
            await lifecycle.submit_event(
                "adapter.status.change",
                msg=i18n.t("core.adapter.state_starting", platform=platform),
                data={
                    "platform": platform,
                    "status": "starting",
                    "retry_count": retry_count,
                },
            )

            while True:
                try:
                    # 注入 owner，使适配器 start() 期间注册的资源（路由/事件处理器/命令）
                    # 自动归属到该平台，从而支持后续按 owner 兜底清理（与模块卸载对齐颗粒度）
                    token = current_owner.set(platform)
                    try:
                        await adapter.start()
                    finally:
                        current_owner.reset(token)
                    self._started_instances.add(adapter)

                    # 提交适配器状态变化事件（started）
                    await lifecycle.submit_event(
                        "adapter.status.change",
                        msg=i18n.t("core.adapter.state_started", platform=platform),
                        data={"platform": platform, "status": "started"},
                    )

                    return
                except asyncio.CancelledError:
                    logger.info(
                        i18n.t("core.adapter.task_cancelled", platform=platform)
                    )
                    return
                except Exception as e:
                    retry_count += 1
                    logger.error(
                        i18n.t(
                            "core.adapter.start_retry_failed",
                            platform=platform,
                            count=retry_count,
                            error=e,
                        )
                    )

                    # 提交适配器状态变化事件（start_failed）
                    await lifecycle.submit_event(
                        "adapter.status.change",
                        msg=i18n.t(
                            "core.adapter.state_start_failed", platform=platform
                        ),
                        data={
                            "platform": platform,
                            "status": "start_failed",
                            "retry_count": retry_count,
                            "error": str(e),
                        },
                    )

                    # 停止 + 清理（shutdown 即清理），避免重试时路由冲突
                    await self._stop_adapter(platform)

                    # 计算等待时间
                    if retry_count <= len(backoff_intervals):
                        wait_time = backoff_intervals[retry_count - 1]
                    else:
                        wait_time = fixed_delay

                    logger.info(
                        i18n.t(
                            "core.adapter.retry_wait",
                            minutes=wait_time // 60,
                            platform=platform,
                        )
                    )
                    await asyncio.sleep(wait_time)

    async def shutdown(self, platforms: str | list[str] | None = None) -> None:
        """
        关闭指定的适配器

        :param platforms: 要关闭的平台，可以是单个平台名、平台名列表或None（表示所有平台）
        :raises ValueError: 当平台未注册时抛出

        :example:
        >>> # 关闭所有适配器
        >>> await adapter.shutdown()
        >>> # 关闭单个适配器
        >>> await adapter.shutdown("Platform1")
        >>> # 关闭多个适配器
        >>> await adapter.shutdown(["Platform1", "Platform2"])
        """
        # 设置关闭标志，避免重复提交离线事件
        self._is_being_shutdown = True

        try:
            if platforms is None:
                platforms = list(self._adapters.keys())
            if not isinstance(platforms, list):
                platforms = [platforms]
            for platform in list(platforms):
                if platform not in self._adapters:
                    logger.warning(
                        i18n.t("core.adapter.not_registered", platform=platform)
                    )
                    platforms.remove(platform)

            logger.info(i18n.t("core.adapter.closing_platforms", platforms=platforms))

            # 提交适配器关闭开始事件
            await lifecycle.submit_event(
                "adapter.stop",
                msg=i18n.t("core.adapter.stop_msg"),
                data={"platforms": platforms},
            )

            from .router import router

            # 需要收集受影响的 adapter 实例（因为多个平台可能共享同一个实例）
            affected_adapters = set()
            bots_to_offline = []  # [(platform, bot_id), ...]

            # 取消目标平台的后台启动任务
            for platform in platforms:
                task = self._adapter_tasks.pop(platform, None)
                if task and not task.done():
                    task.cancel()
                    logger.debug(
                        i18n.t("core.adapter.task_cancelled_debug", platform=platform)
                    )

            for platform in platforms:
                adapter_instance = self._adapters[platform]
                affected_adapters.add(adapter_instance)

                # 收集该平台下需要标记为离线的 Bot
                if platform in self._bots:
                    for bot_id, bot_info in self._bots[platform].items():
                        if bot_info.get("status") != "offline":
                            bots_to_offline.append((platform, bot_id))

            # 对每个受影响的 adapter 实例执行 shutdown（如果尚未关闭）
            for adapter_instance in affected_adapters:
                if adapter_instance in self._started_instances:
                    # 找到该实例对应的平台名（用于事件提交）
                    instance_platforms = [
                        p for p, a in self._adapters.items() if a is adapter_instance
                    ]
                    platform_label = (
                        instance_platforms[0]
                        if instance_platforms
                        else str(id(adapter_instance))
                    )

                    # 提交适配器状态变化事件（stopping）
                    for p in instance_platforms:
                        if p in platforms:
                            await lifecycle.submit_event(
                                "adapter.status.change",
                                msg=i18n.t("core.adapter.state_stopping", platform=p),
                                data={"platform": p, "status": "stopping"},
                            )

                    try:
                        await adapter_instance.shutdown()
                        self._started_instances.remove(adapter_instance)

                        # 提交适配器状态变化事件（stopped）
                        for p in instance_platforms:
                            if p in platforms:
                                await lifecycle.submit_event(
                                    "adapter.status.change",
                                    msg=i18n.t(
                                        "core.adapter.state_stopped", platform=p
                                    ),
                                    data={"platform": p, "status": "stopped"},
                                )
                    except Exception as e:
                        logger.error(
                            i18n.t(
                                "core.adapter.stop_failed",
                                id=id(adapter_instance),
                                error=e,
                            )
                        )

                        # 提交适配器状态变化事件（stop_failed）
                        for p in instance_platforms:
                            if p in platforms:
                                await lifecycle.submit_event(
                                    "adapter.status.change",
                                    msg=i18n.t(
                                        "core.adapter.state_stop_failed", platform=p
                                    ),
                                    data={
                                        "platform": p,
                                        "status": "stop_failed",
                                        "error": str(e),
                                    },
                                )

            # 清理被关闭平台注册的资源（路由 + 命令 + 事件处理器），与模块卸载对齐颗粒度。
            # 同时覆盖"以平台名为 owner、用细颗粒度命名空间（如 onebot11_default）注册"的资源。
            for platform in platforms:
                self._cleanup_adapter_resources(platform)

            # 将相关 Bot 标记为离线
            for platform, bot_id in bots_to_offline:
                if platform in self._bots and bot_id in self._bots[platform]:
                    self._bots[platform][bot_id]["status"] = "offline"
                    await lifecycle.submit_event(
                        "adapter.bot.offline",
                        msg=i18n.t(
                            "core.adapter.bot_offline", platform=platform, bot_id=bot_id
                        ),
                        data={
                            "platform": platform,
                            "bot_id": bot_id,
                            "status": "offline",
                        },
                    )

            # 仅在关闭全部适配器时清理事件处理器，避免部分关闭影响其他适配器
            all_platforms = set(self._adapters.keys())
            if set(platforms) >= all_platforms:
                self._onebot_handlers.clear()
                self._raw_handlers.clear()
                self._onebot_middlewares.clear()

            # 提交适配器关闭完成事件
            await lifecycle.submit_event(
                "adapter.stopped",
                msg=i18n.t("core.adapter.shutdown_complete"),
                data={"platforms": platforms},
            )
        finally:
            # 清除关闭标志
            self._is_being_shutdown = False

    async def _stop_adapter(self, platform: str) -> None:
        """
        {!--< internal-use >!--}
        停止单个平台适配器——shutdown 即清理。

        将"停止适配器"与"回收其注册的资源"绑定在一次调用里：调用适配器自身的
        ``shutdown()`` 后立即清理该平台的路由/事件/命令。restart、启动失败重试等
        场景均经此入口，保证适配器一旦停止、归属资源必被回收，无需调用方再补清理。

        对未注册的平台直接返回；``shutdown()`` 与清理均幂等，半途失败的重试场景
        也能正确回收 start() 期间已注册的资源。

        :param platform: 平台名称
        {!--< /internal-use >!--}
        """
        adapter_instance = self._adapters.get(platform)
        if adapter_instance is None:
            return

        # 调用适配器自身 shutdown（未启动/半途失败的重试场景也需清理部分状态）
        try:
            await adapter_instance.shutdown()
        except Exception as e:
            logger.error(
                i18n.t("core.adapter.stop_adapter_failed", platform=platform, error=e)
            )
        self._started_instances.discard(adapter_instance)

        # 回收该平台运行期间注册的路由/事件/命令（幂等）
        self._cleanup_adapter_resources(platform)

    def _cleanup_adapter_resources(self, platform: str) -> None:
        """
        {!--< internal-use >!--}
        适配器资源兜底清理（与模块卸载对齐颗粒度）。

        清理该平台在运行期间注册的所有路由、命令与事件处理器。同时覆盖两种注册方式：
        - 直接以平台名为命名空间注册的路由（unregister_all_by_namespace）
        - 适配器以平台名为 owner、用细颗粒度命名空间（如 onebot11_default）注册的路由
          （unregister_all_by_owner，依赖 start() 期间注入的 current_owner）

        :param platform: 平台名称
        {!--< /internal-use >!--}
        """
        try:
            from .router import router

            result_ns = router.unregister_all_by_namespace(platform)
            result_owner = router.unregister_all_by_owner(platform)
            http_c = result_ns["http_count"] + result_owner["http_count"]
            ws_c = result_ns["websocket_count"] + result_owner["websocket_count"]
            sse_c = result_ns["sse_count"] + result_owner["sse_count"]
            if http_c or ws_c or sse_c:
                logger.debug(
                    i18n.t(
                        "core.adapter.routes_cleaned",
                        platform=platform,
                        http=http_c,
                        ws=ws_c,
                        sse=sse_c,
                    )
                )
        except Exception as e:
            logger.debug(
                i18n.t("core.adapter.routes_clean_failed", platform=platform, error=e)
            )

        try:
            from .Event import command, message, meta, notice, request

            cleaned = command.unregister_by_owner(platform)
            for event_handler in (message, notice, request, meta):
                cleaned += event_handler.handler.unregister_by_owner(platform)
            if cleaned > 0:
                logger.debug(
                    i18n.t(
                        "core.adapter.handlers_cleaned",
                        platform=platform,
                        count=cleaned,
                    )
                )
        except Exception as e:
            logger.debug(
                i18n.t("core.adapter.handlers_clean_failed", platform=platform, error=e)
            )

    async def restart(self, platform: str) -> bool:
        """
        重启指定平台适配器（shutdown + 资源兜底清理 + start）

        框架自动处理该平台在运行期间注册的路由/事件/命令清理（与模块卸载对齐颗粒度），
        并在重启时注入 owner，使新注册的资源可被后续按 owner 清理。
        第三方模块（如 Dashboard）的热重载应调用本方法，而非直接操作适配器实例。

        :param platform: 平台名称
        :return: 是否实际执行了重启（平台存在且原本在运行时为 True）

        :example:
        >>> await sdk.adapter.restart("OneBot11")
        """
        adapter_instance = self._adapters.get(platform)
        if adapter_instance is None:
            logger.warning(i18n.t("core.adapter.cannot_restart", platform=platform))
            return False
        if adapter_instance not in self._started_instances:
            logger.info(i18n.t("core.adapter.not_running_skip", platform=platform))
            return False

        # 1) 停止适配器（shutdown 即清理：路由/事件/命令随之回收）
        await lifecycle.submit_event(
            "adapter.status.change",
            msg=i18n.t("core.adapter.state_stopping", platform=platform),
            data={"platform": platform, "status": "stopping"},
        )
        await self._stop_adapter(platform)

        # 2) 重新启动，注入 owner 使 start() 期间注册的资源归属该平台
        await lifecycle.submit_event(
            "adapter.status.change",
            msg=i18n.t("core.adapter.state_starting", platform=platform),
            data={"platform": platform, "status": "starting"},
        )
        token = current_owner.set(platform)
        try:
            await adapter_instance.start()
        except Exception as e:
            logger.error(
                i18n.t("core.adapter.restart_start_failed", platform=platform, error=e)
            )
            # 启动失败：回滚（停止 + 清理本次注册的资源），避免下次冲突
            await self._stop_adapter(platform)
            return False
        finally:
            current_owner.reset(token)
        self._started_instances.add(adapter_instance)

        await lifecycle.submit_event(
            "adapter.status.change",
            msg=i18n.t("core.adapter.state_started", platform=platform),
            data={"platform": platform, "status": "started"},
        )
        return True

    def clear(self) -> None:
        """
        清除所有适配器实例和信息

        {!--< internal-use >!--}
        此方法用于反初始化时完全重置适配器管理器状态
        {!--< /internal-use >!--}
        """
        from .router import router

        # 清理所有适配器的路由
        for platform in list(self._adapters.keys()):
            result = router.unregister_all_by_namespace(platform)
            if result["http_count"] > 0 or result["websocket_count"] > 0:
                logger.debug(
                    i18n.t(
                        "core.adapter.clear_routes_result",
                        platform=platform,
                        http=result["http_count"],
                        ws=result["websocket_count"],
                    )
                )

        # 清除所有适配器实例
        self._adapters.clear()

        # 清除适配器信息
        self._adapter_info.clear()

        # 清除所有处理器
        self._onebot_handlers.clear()
        self._raw_handlers.clear()
        self._onebot_middlewares.clear()

        # 清除已启动实例追踪
        self._started_instances.clear()

        # 取消并清除所有后台任务
        for task in self._adapter_tasks.values():
            if not task.done():
                task.cancel()
        self._adapter_tasks.clear()

        # 清除Bot状态
        self._bots.clear()

        logger.debug(i18n.t("core.adapter.cleared"))

    # ==================== 适配器配置管理 ====================

    def _config_register(self, platform: str, enabled: bool = False) -> bool:
        """
        注册新平台适配器（仅当平台不存在时注册）

        :param platform: 平台名称
        :param enabled: [bool] 是否启用适配器
        :return: [bool] 操作是否成功
        """
        existing = config.getConfig(CONFIG_KEY_ADAPTER_STATUS_OF.format(platform))
        if existing is not None:
            return True

        config.setConfig(CONFIG_KEY_ADAPTER_STATUS_OF.format(platform), enabled)
        status = (
            i18n.t("core.adapter.status_enabled")
            if enabled
            else i18n.t("core.adapter.status_disabled")
        )
        logger.debug(
            i18n.t("core.adapter.registered_status", platform=platform, status=status)
        )
        return True

    def exists(self, platform: str) -> bool:
        """
        检查平台是否已注册

        :param platform: 平台名称
        :return: 平台是否已注册（即 adapter.register() 已被调用）
        """
        return platform in self._adapters

    def is_enabled(self, platform: str) -> bool:
        """
        检查平台适配器是否启用

        :param platform: 平台名称
        :return: 平台适配器是否启用

        {!--< tips >!--}
        适配器启用条件：
        1. 适配器在配置文件中（ErisPulse.adapters.status.{platform} 存在）
        2. 配置值为启用状态

        如果适配器未在配置中，返回 False
        {!--< /tips >!--}
        """
        from .config import parse_bool_config

        status = config.getConfig(CONFIG_KEY_ADAPTER_STATUS_OF.format(platform))

        # 适配器未在配置中，返回 False
        if status is None:
            return False

        return parse_bool_config(status)

    def enable(self, platform: str) -> bool:
        """
        启用平台适配器

        :param platform: 平台名称
        :return: [bool] 操作是否成功
        """
        # 启用平台时自动在配置中注册
        if platform not in self._adapters:
            logger.error(i18n.t("core.adapter.platform_not_exist", platform=platform))
            return False

        config.setConfig(CONFIG_KEY_ADAPTER_STATUS_OF.format(platform), True)
        logger.info(i18n.t("core.adapter.platform_enabled", platform=platform))
        return True

    def disable(self, platform: str) -> bool:
        """
        禁用平台适配器

        :param platform: 平台名称
        :return: [bool] 操作是否成功
        """
        # 禁用平台时自动在配置中注册
        if platform not in self._adapters:
            logger.error(i18n.t("core.adapter.platform_not_exist", platform=platform))
            return False

        config.setConfig(CONFIG_KEY_ADAPTER_STATUS_OF.format(platform), False)
        logger.info(i18n.t("core.adapter.platform_disabled", platform=platform))
        return True

    def unregister(self, platform: str) -> bool:
        """
        取消注册适配器

        :param platform: 平台名称
        :return: 是否取消成功

        {!--< internal-use >!--}
        注意: 此方法仅取消注册, 不关闭已启动的适配器
        {!--< /internal-use >!--}
        """
        if platform not in self._adapters:
            logger.warning(
                i18n.t("core.adapter.platform_unregistered_short", platform=platform)
            )
            return False

        # 移除适配器实例
        self._adapters.pop(platform)

        logger.info(i18n.t("core.adapter.platform_unregistered", platform=platform))
        return True

    def list_registered(self) -> list[str]:
        """
        列出所有已注册的平台

        :return: 平台名称列表
        """
        return list(self._adapters.keys())

    def list_items(self) -> dict[str, bool]:
        """
        列出所有平台适配器状态

        :return: {平台名: 是否启用} 字典
        """
        return config.getConfig(CONFIG_KEY_ADAPTER_STATUS, {})

    # 兼容性方法 - 保持向后兼容
    def list_adapters(self) -> dict[str, bool]:
        """
        兼容性方法 - 保持向后兼容

        :return: {平台名: 是否启用} 字典

        {!--< deprecated >!--} 此方法已弃用，请使用 list_items() 代替
        """
        warnings.warn(
            i18n.t("core.adapter.list_adapters_deprecated"),
            DeprecationWarning,
            stacklevel=2,
        )
        return self.list_items()

    # ==================== 事件处理与消息发送 ====================

    def on(
        self,
        event_type: str = "*",
        *,
        raw: bool = False,
        platform: str | None = None,
    ) -> Callable[[Callable], Callable]:
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
            handler_wrapper = {"func": wrapper, "platform": platform}

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

        每个事件处理器（handler）都在独立的 asyncio.Task 中执行，
        单个处理器阻塞不会影响框架的事件分发和其他处理器运行。

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
        detail_type = data.get("detail_type", "")
        platform_raw = data.get(f"{platform}_raw", {})
        raw_event_type = data.get(f"{platform}_raw_type")

        if event_type == "message":
            user_id = data.get("user_id", "")
            alt_msg = data.get("alt_message", "")
            if len(alt_msg) > 50:
                alt_msg = alt_msg[:50] + "..."
            _msg_logger.message(
                f"[Recv] {platform}/{detail_type}({user_id}): {alt_msg}"
            )
        else:
            _msg_logger.message(f"[Recv] {platform}/{event_type}/{detail_type}")

        # 钩子: 事件接收（最早期，所有事件都经过此处）
        await lifecycle.emit(
            "adapter.event.receive",
            {
                "platform": platform,
                "event_type": event_type,
                "raw_event_type": raw_event_type,
            },
        )

        # 处理 meta 事件：适配器通过 meta 事件提交 Bot 上下线信息
        # 同时也处理普通事件中的 self 字段（自动发现Bot）
        if (
            (self_info := data.get("self"))
            and isinstance(self_info, dict)
            and "user_id" in self_info
        ):
            if event_type == "meta":
                detail_type = data.get("detail_type", "")
                match detail_type:
                    case "connect":
                        # Bot 连接上线
                        is_new_bot = self._auto_register_bot(platform, self_info)
                        bot_id = str(self_info["user_id"])
                        await lifecycle.submit_event(
                            "adapter.bot.online",
                            msg=i18n.t(
                                "core.adapter.bot_online",
                                platform=platform,
                                bot_id=bot_id,
                            ),
                            data={
                                "platform": platform,
                                "bot_id": bot_id,
                                "info": self._bots.get(platform, {})
                                .get(bot_id, {})
                                .get("info", {}),
                                "status": "online",
                            },
                        )
                    case "disconnect":
                        # Bot 断开连接
                        self._update_bot_status(
                            platform, str(self_info["user_id"]), "offline"
                        )
                    case "heartbeat":
                        # 心跳，更新活跃时间
                        self._update_bot_heartbeat(platform, self_info)
                    case _:
                        # 其他 detail_type 不做特殊处理
                        pass
            else:
                # 普通事件：自动发现Bot并更新活跃时间
                is_new = self._auto_register_bot(platform, self_info)
                if is_new:
                    bot_id = str(self_info["user_id"])
                    await lifecycle.submit_event(
                        "adapter.bot.online",
                        msg=i18n.t(
                            "core.adapter.bot_online", platform=platform, bot_id=bot_id
                        ),
                        data={
                            "platform": platform,
                            "bot_id": bot_id,
                            "info": self._bots.get(platform, {})
                            .get(bot_id, {})
                            .get("info", {}),
                            "status": "online",
                        },
                    )

        # 先执行OneBot12中间件（中间件可以修改数据，必须顺序执行）
        processed_data = data
        for middleware in self._onebot_middlewares:
            result = await middleware(processed_data)
            if result is not None:
                processed_data = result
            else:
                logger.warning(
                    i18n.t(
                        "core.adapter.middleware_returned_none",
                        name=middleware.__qualname__,
                    )
                )

        # 分发到OneBot12事件处理器（每个 handler 在独立 Task 中执行，不阻塞框架）
        handlers_to_call = []

        # 处理特定事件类型的处理器
        if event_type in self._onebot_handlers:
            handlers_to_call.extend(self._onebot_handlers[event_type])

        # 处理通配符处理器
        handlers_to_call.extend(self._onebot_handlers.get("*", []))

        # 将符合条件的处理器分发到独立 Task
        for handler_wrapper in handlers_to_call:
            handler_platform = handler_wrapper.get("platform")
            if handler_platform is None or handler_platform == platform:
                self._dispatch_handler_task(
                    handler_wrapper["func"],
                    processed_data,
                    event_type=event_type,
                    platform=platform,
                )

        # 只有当存在原生事件数据时才分发原生事件
        if raw_event_type and (platform_raw := data.get(f"{platform}_raw")) is not None:
            raw_handlers_to_call = []

            # 处理特定原生事件类型的处理器
            if raw_event_type in self._raw_handlers:
                raw_handlers_to_call.extend(self._raw_handlers[raw_event_type])

            # 处理原生事件的通配符处理器
            raw_handlers_to_call.extend(self._raw_handlers.get("*", []))

            # 将符合条件的原生事件处理器分发到独立 Task
            for handler_wrapper in raw_handlers_to_call:
                handler_platform = handler_wrapper.get("platform")
                if handler_platform is None or handler_platform == platform:
                    self._dispatch_handler_task(
                        handler_wrapper["func"],
                        platform_raw,
                        event_type=raw_event_type,
                        platform=platform,
                    )

        # 钩子: 事件分发完成
        await lifecycle.emit(
            "adapter.event.dispatched",
            {
                "platform": platform,
                "event_type": event_type,
                "raw_event_type": raw_event_type,
                "onebot_handlers_count": len(handlers_to_call),
            },
        )

    def _dispatch_handler_task(
        self,
        func: Callable,
        data: Any,
        *,
        event_type: str = "unknown",
        platform: str = "unknown",
    ) -> asyncio.Task:
        """
        {!--< internal-use >!--}
        将事件处理器包装为独立 asyncio.Task 并调度执行

        处理器在独立 Task 中运行，不会阻塞 adapter.emit() 的后续流程。
        自动捕获处理器异常并记录日志，同时监控处理器执行耗时。

        :param func: 事件处理器函数
        :param data: 事件数据
        :param event_type: 事件类型（用于日志）
        :param platform: 平台名称（用于日志）
        :return: asyncio.Task
        """
        import time as _time

        _func_name = getattr(func, "__qualname__", getattr(func, "__name__", str(func)))

        # 在 Task 顶层准备 wait_reply 累计器（list 对象，可跨 ContextVar 共享）。
        # 注意：ContextVar 的 set()/reset() 必须在同一个 Task Context 内完成，
        # 所以下面把 .set() 移入 _safe_run，避免跨 Task token 错误。
        _task_waits: list[dict] = []

        async def _safe_run():
            _wait_token = handler_waits.set(_task_waits)
            t0 = _time.monotonic()
            try:
                await func(data)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(
                    i18n.t(
                        "core.adapter.handler_error",
                        handler=_func_name,
                        type=event_type,
                        platform=platform,
                        error=e,
                    )
                )
            finally:
                elapsed = _time.monotonic() - t0
                handler_waits.reset(_wait_token)

                _wait_total = sum(w.get("duration", 0.0) for w in _task_waits)
                _pure = max(0.0, elapsed - _wait_total)
                # 收集所有者（去重），归因到具体业务模块
                _owners = sorted(
                    {w.get("owner") for w in _task_waits if w.get("owner")}
                )
                _owner_tag = f" owners=[{','.join(_owners)}]" if _owners else ""

                if _task_waits:
                    # 调用过 wait_reply：纯等待属于交互白名单
                    if _pure > HANDLER_SLOW_THRESHOLD_SECS:
                        logger.warning(
                            f"事件处理器执行缓慢 [{_func_name}] "
                            f"耗时 {elapsed:.2f}s "
                            f"(wait_reply={_wait_total:.2f}s, pure={_pure:.2f}s)"
                            f" > {HANDLER_SLOW_THRESHOLD_SECS}s "
                            f"type={event_type} platform={platform}{_owner_tag}"
                        )
                    else:
                        logger.debug(
                            f"事件处理器 [{_func_name}] 耗时 {elapsed:.2f}s "
                            f"(wait_reply={_wait_total:.2f}s, pure={_pure:.2f}s) "
                            f"interactive-wait, suppressed slow-warning "
                            f"type={event_type} platform={platform}{_owner_tag}"
                        )
                else:
                    if elapsed > HANDLER_SLOW_THRESHOLD_SECS:
                        logger.warning(
                            i18n.t(
                                "core.adapter.handler_slow",
                                handler=_func_name,
                                elapsed=f"{elapsed:.2f}",
                                threshold=HANDLER_SLOW_THRESHOLD_SECS,
                                type=event_type,
                                platform=platform,
                                tag=_owner_tag,
                            )
                        )

        try:
            return asyncio.create_task(_safe_run())
        except RuntimeError:
            return asyncio.ensure_future(_safe_run())

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
            "info": existing_meta,
        }

        if is_new:
            logger.debug(
                i18n.t(
                    "core.adapter.auto_discover_bot", platform=platform, bot_id=bot_id
                )
            )

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
            self._bots[platform][bot_id] = {
                "status": status,
                "last_active": time.time(),
                "info": {},
            }
        else:
            old_status = self._bots[platform][bot_id].get("status")
            self._bots[platform][bot_id]["status"] = status
            if old_status != status:
                logger.debug(
                    i18n.t(
                        "core.adapter.bot_status_change",
                        platform=platform,
                        bot_id=bot_id,
                        old=old_status,
                        new=status,
                    )
                )

        if status == "offline":
            if not self._is_being_shutdown:
                try:
                    loop = asyncio.get_running_loop()
                    task_key = f"_bot_offline_{platform}_{bot_id}"

                    async def _offline_event():
                        try:
                            await lifecycle.submit_event(
                                "adapter.bot.offline",
                                msg=i18n.t(
                                    "core.adapter.bot_offline",
                                    platform=platform,
                                    bot_id=bot_id,
                                ),
                                data={
                                    "platform": platform,
                                    "bot_id": bot_id,
                                    "status": "offline",
                                },
                            )
                        finally:
                            self._adapter_tasks.pop(task_key, None)

                    task = loop.create_task(_offline_event())
                    self._adapter_tasks[task_key] = task
                except RuntimeError:
                    pass

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

    def get_bot_info(self, platform: str, bot_id: str) -> dict | None:
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

    def list_bots(self, platform: str | None = None) -> dict[str, dict[str, dict]]:
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
        if (bot_info := self._bots.get(platform, {}).get(bot_id)) is None:
            return False
        return bot_info.get("status") == "online"

    def get_status_summary(self) -> dict[str, Any]:
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
                "bots": dict(self._bots.get(platform_name, {})),
            }

        return {"adapters": adapters_summary}

    # ==================== 工具方法 ====================

    def get(self, platform: str) -> BaseAdapter | None:
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
        if (adapter_instance := self.get(platform)) is None:
            return False
        return adapter_instance in self._started_instances

    def list_running(self) -> list[str]:
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

    def get_connection_info(self, platform: str) -> dict[str, Any] | None:
        """
        获取适配器的连接信息（路由URL、状态等）

        结合路由管理器的路由数据，返回指定平台适配器的完整连接信息，
        包括 base_url、HTTP 路由、WebSocket 路由和 SSE 路由的完整 URL。

        路由注册时的 ``module_name`` 必须与适配器的 ``platform`` 名称完全一致，
        否则路由信息将无法被正确关联。

        :param platform: 平台名称
        :return: 连接信息字典，平台不存在时返回 None

        :example:
        >>> info = sdk.adapter.get_connection_info("onebot11")
        >>> # {
        >>> #     "platform": "onebot11",
        >>> #     "status": "started",
        >>> #     "connection": {
        >>> #         "base_url": "http://localhost:8080",
        >>> #         "http_routes": [
        >>> #             {"path": "/onebot11/webhook", "method": "POST",
        >>> #              "url": "http://localhost:8080/onebot11/webhook"}
        >>> #         ],
        >>> #         "websocket_routes": [
        >>> #             {"path": "/onebot11/ws",
        >>> #              "url": "ws://localhost:8080/onebot11/ws"}
        >>> #         ],
        >>> #         "sse_routes": [
        >>> #             {"path": "/onebot11/events",
        >>> #              "url": "http://localhost:8080/onebot11/events"}
        >>> #         ]
        >>> #     }
        >>> # }
        """
        if not self.exists(platform):
            return None

        from .router import router

        urls = router.get_module_urls(platform)
        has_routes = urls.get("http") or urls.get("websocket") or urls.get("sse")

        if not has_routes:
            urls = router.get_module_urls_matching(platform)
            has_routes = urls.get("http") or urls.get("websocket") or urls.get("sse")

        base_url = urls.get("base_url", "")

        status = "started" if self.is_running(platform) else "stopped"

        return {
            "platform": platform,
            "status": status,
            "connection": {
                "base_url": base_url,
                "http_routes": urls.get("http", []),
                "websocket_routes": urls.get("websocket", []),
                "sse_routes": urls.get("sse", []),
            },
        }

    def list_sends(self, platform: str) -> list[str]:
        """
        列出指定平台支持的发送方法

        :param platform: 平台名称
        :return: 发送方法名列表
        :raises ValueError: 当平台不存在时抛出

        :example:
        >>> methods = adapter.list_sends("onebot11")
        >>> print(methods)  # ["Text", "Image", "Voice", ...]
        """
        if (adapter_instance := self.get(platform)) is None:
            raise ValueError(
                i18n.t("core.adapter.platform_not_exist", platform=platform)
            )

        # 获取Send类
        send_class = adapter_instance.Send.__class__

        # 获取SendDSL基类的所有方法名称
        from .Bases.adapter import SendDSL

        base_dsl_methods = set(dir(SendDSL))

        # 获取Send类中定义的方法，排除基类方法和私有方法
        send_methods = []
        for name in dir(send_class):
            # 跳过私有方法和魔法方法
            if name.startswith("_"):
                continue
            # 跳过基类中已有的方法
            if name in base_dsl_methods:
                continue
            # 获取属性，确保是方法或可调用对象
            attr = getattr(send_class, name)
            if callable(attr):
                send_methods.append(name)

        return sorted(send_methods)

    def send_info(self, platform: str, method_name: str) -> dict[str, Any]:
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
        if (adapter_instance := self.get(platform)) is None:
            raise ValueError(
                i18n.t("core.adapter.platform_not_exist", platform=platform)
            )

        # 获取Send类
        send_class = adapter_instance.Send.__class__

        # 检查方法是否存在
        if not hasattr(send_class, method_name):
            raise ValueError(
                i18n.t("core.adapter.method_not_exist", method=method_name)
            )

        method = getattr(send_class, method_name)

        # 提取参数信息
        parameters = []
        if inspect.ismethod(method) or inspect.isfunction(method):
            sig = inspect.signature(method)
            for param_name, param in sig.parameters.items():
                # 跳过self参数
                if param_name == "self":
                    continue

                param_info = {
                    "name": param_name,
                    "type": None,
                    "default": None,
                    "annotation": None,
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
            "docstring": docstring,
        }

    @property
    def platforms(self) -> list[str]:
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
        if (adapter_instance := self.get(platform)) is None:
            raise AttributeError(
                i18n.t("core.adapter.platform_not_enabled", platform=platform)
            )
        return adapter_instance

    def __contains__(self, platform: str) -> bool:
        """
        检查平台是否存在且处于启用状态

        :param platform: 平台名称
        :return: [bool] 平台是否存在且启用
        """
        return self.exists(platform) and self.is_enabled(platform)

    def __repr__(self) -> str:
        registered = list(self._adapters.keys())
        running = [p for p, a in self._adapters.items() if a in self._started_instances]
        return f"<AdapterManager registered={registered} running={running}>"


adapter: AdapterManager = AdapterManager()

__all__ = ["adapter"]
