"""
ErisPulse SDK 主类

提供统一的 SDK 接口，整合所有核心模块和加载器

{!--< tips >!--}
example:
    >>> from ErisPulse import sdk
    >>> await sdk.init()
    >>> await sdk.adapter.startup()
{!--< /tips >!--}
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import importlib
import inspect
import os
import sys
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .Core.constants import (
    ENV_SUPERVISED,
    HARD_RESTART_EXIT_CODE,
    LIFECYCLE_TIMER_CORE_INIT,
    SDK_HARD_RESTART_SETTLE_DELAY_SECS,
)
from .Core.i18n import i18n

# 导入加载器类
# 导入懒加载模块类
from .loaders.module import LazyModule
from .runtime import proactive_gc as _pgc
from .runtime import sdk_initializer as _sdk_initializer
from .runtime.kernel import Kernel

if TYPE_CHECKING:

    from .Core import (
        AdapterManager,
        ConfigManager,
        I18nManager,
        LifecycleManager,
        Logger,
        MasterManager,
        ModuleManager,
        RouterManager,
        ScopeManager,
        StorageManager,
        TranscriptManager,
    )
    from .Core import (
        BaseAdapter as _BaseAdapter,
    )
    from .Core import (
        BaseQueryBuilder as _BaseQueryBuilder,
    )
    from .Core import (
        BaseStorage as _BaseStorage,
    )
    from .Core import (
        Client as _Client,
    )
    from .Core import (
        SendDSL as _SendDSL,
    )
    from .Core.Event import InteractionManager


def _resolve_core(attr: str):
    """
    {!--< internal-use >!--}
    动态解析核心模块单例引用

    每次访问时通过 import 系统获取最新单例，确保软重启后 SDK 始终
    指向当前有效的模块级单例对象。

    :param attr: 核心属性名
    :return: 对应的单例对象
    :raises AttributeError: 当属性名不在核心映射中时
    """
    _CORE_MAP = {
        "Event": ("ErisPulse.Core", "Event"),
        "lifecycle": ("ErisPulse.Core", "lifecycle"),
        "logger": ("ErisPulse.Core", "logger"),
        "storage": ("ErisPulse.Core", "storage"),
        "env": ("ErisPulse.Core", "env"),
        "config": ("ErisPulse.Core", "config"),
        "i18n": ("ErisPulse.Core", "i18n"),
        "adapter": ("ErisPulse.Core", "adapter"),
        "module": ("ErisPulse.Core", "module"),
        "router": ("ErisPulse.Core", "router"),
        "client": ("ErisPulse.Core", "client"),
        "master": ("ErisPulse.Core", "master"),
        "scope": ("ErisPulse.Core", "scope"),
        "transcript": ("ErisPulse.Core", "transcript"),
        "interaction": ("ErisPulse.Core.Event", "interaction"),
        "context": ("ErisPulse.runtime", "context"),
        "BaseAdapter": ("ErisPulse.Core", "BaseAdapter"),
        "SendDSL": ("ErisPulse.Core", "SendDSL"),
        "BaseStorage": ("ErisPulse.Core.Bases.storage", "BaseStorage"),
        "BaseQueryBuilder": ("ErisPulse.Core.Bases.storage", "BaseQueryBuilder"),
    }

    if attr not in _CORE_MAP:
        raise AttributeError(attr)

    module_path, name = _CORE_MAP[attr]
    mod = importlib.import_module(module_path)
    return getattr(mod, name)


# 核心属性名称集合
_CORE_ATTR_NAMES = {
    "Event",
    "lifecycle",
    "logger",
    "storage",
    "env",
    "config",
    "i18n",
    "adapter",
    "module",
    "router",
    "client",
    "master",
    "scope",
    "transcript",
    "interaction",
    "context",
    "BaseAdapter",
    "SendDSL",
    "BaseStorage",
    "BaseQueryBuilder",
}


class SDK:
    """
    ErisPulse SDK 主类

    整合所有核心模块和加载器，提供统一的初始化和管理接口

    设计说明:
    核心模块属性（adapter, module, router, logger, lifecycle 等）
    通过动态解析获取，不缓存在实例上。这确保软重启后 SDK 始终
    指向最新的模块级单例，无需手动刷新引用。

    {!--< tips >!--}
    SDK 提供以下核心属性：
    - Event: 事件系统
    - lifecycle: 生命周期管理器
    - logger: 日志管理器
    - storage: 存储管理器
    - env: 存储管理器别名
    - config: 配置管理器
    - i18n: 国际化管理器
    - adapter: 适配器管理器
    - BaseAdapter: 适配器基类
    - SendDSL: DSL 发送接口基类
    - module: 模块管理器
    - router: 路由管理器
    - client: HTTP 客户端
    - master: 框架主人管理器
    - scope: 作用域管理器（模块 / 身份 / 出站 三维，"什么范围内生效"）
    - transcript: 会话收件箱（每会话近期消息流的记录与查询）
    - interaction: 交互会话管理器（wait_reply 等待表 / 会话租约 / 按归属取消）
    - Event: 事件模块包（command 命令处理器 / message / notice / request 等事件处理器）
    - context: 模块上下文管理（owner_scope / get_current_owner / trace-id / 消息事务账本）
    {!--< /tips >!--}
    """

    # ---- 类级别类型注解（仅供 IDE / 类型检查器使用）----
    # 注意：这些注解 *没有赋值*，不会创建实例属性，
    # 因此运行时仍然会触发 __getattr__ 进行动态解析。
    from types import ModuleType

    Event: ModuleType
    lifecycle: LifecycleManager
    logger: Logger
    storage: StorageManager
    env: StorageManager
    config: ConfigManager
    i18n: I18nManager
    adapter: AdapterManager
    module: ModuleManager
    router: RouterManager
    client: _Client
    BaseAdapter: type[_BaseAdapter]
    SendDSL: type[_SendDSL]
    BaseStorage: type[_BaseStorage]
    BaseQueryBuilder: type[_BaseQueryBuilder]
    master: MasterManager
    scope: ScopeManager
    transcript: TranscriptManager
    interaction: InteractionManager
    context: ModuleType

    def __init__(self):
        """
        初始化 SDK 实例

        不缓存任何核心模块引用。核心属性通过 __getattr__ 动态解析，
        确保软重启后始终指向最新的模块级单例。
        """
        self._kernel = Kernel(self)  # 统一编排内核（组合根：加载器与协调器的唯一组装点）
        self._initializer: SDK.Initializer | None = None
        self._module_loader: Any = None  # 模块加载器（Initializer 创建后注入，热重载使用）
        self._adapter_loader: Any = None  # 适配器加载器（Initializer 创建后注入，适配器热重载使用）
        self._initialized: bool = False
        self._gc_task: asyncio.Task | None = None  # 主动 GC 后台任务
        self._gc_config_snapshot: tuple | None = None  # 主动 GC 配置快照（变更检测）
        self._shutdown_event: asyncio.Event | None = None  # 优雅关闭事件

    @property
    def version(self) -> str:
        """
        获取当前 ErisPulse 安装版本

        每次访问实时查询 importlib.metadata，确保框架热更新后
        能读到最新版本（如果框架本身被upgrade）。

        :return: str 版本号字符串，未安装时返回 "UnknownVersion"

        :example:
        >>> print(sdk.version)
        '2.6.2'
        """
        import importlib.metadata

        try:
            return importlib.metadata.version("ErisPulse")
        except importlib.metadata.PackageNotFoundError:
            return "UnknownVersion"

    def __dir__(self) -> list[str]:
        """
        列出实例属性（含核心模块动态属性）

        让 ``dir(sdk)`` 与交互式补全反映 ``__getattr__`` 提供的核心模块单例
        （scope / command / master / adapter 等）。用类级 dir() 避免
        触发 ``__getattr__`` 的递归解析。

        :return: 属性名列表（去重排序）
        """
        try:
            base = list(dir(type(self)))
        except Exception:
            base = []
        return sorted(set(base) | set(_CORE_ATTR_NAMES))

    def __getattr__(self, name: str):
        """
        动态解析核心模块属性

        当属性不在实例 __dict__ 中时调用。对核心属性名使用动态 import 解析，
        确保软重启后始终获取最新单例。对未知属性提供友好的错误提示。

        :param name: 属性名
        :return: 属性值
        :raises AttributeError: 当属性不存在时
        """
        # 核心属性：动态解析
        if name in _CORE_ATTR_NAMES:
            try:
                return _resolve_core(name)
            except (ImportError, AttributeError) as _err:
                raise AttributeError(
                    i18n.t("core.sdk.attr.core_resolve_failed", name=name)
                ) from _err

        # 非核心属性：提供友好的错误提示
        try:
            from .Core.logger import logger as _logger

            err_logger = _logger.error
        except Exception:
            err_logger = lambda msg: None

        # 收集候选名称用于拼写检查
        candidates = list(_CORE_ATTR_NAMES)
        if not name.startswith("_"):
            try:
                mod_mgr = _resolve_core("module")
                adap_mgr = _resolve_core("adapter")
                candidates.extend(mod_mgr._module_classes.keys())
                candidates.extend(adap_mgr._adapters.keys())

                if name in mod_mgr._module_classes:
                    err_logger(i18n.t("core.sdk.attr.module_not_loaded", name=name))
                elif name in adap_mgr._adapters:
                    err_logger(i18n.t("core.sdk.attr.adapter_not_enabled", name=name))
                else:
                    err_logger(i18n.t("core.sdk.attr.not_found", name=name))
            except Exception:
                err_logger(i18n.t("core.sdk.attr.not_found", name=name))

        # 拼写检查：给出"你是不是想写 xxx"提示
        from .runtime.hints import best_match

        msg = i18n.t("core.sdk.attr.no_attribute", name=name)
        suggestion = best_match(name, candidates, cutoff=0.5)
        if suggestion and suggestion != name:
            msg += "\n" + i18n.t("core.sdk.attr.did_you_mean", name=suggestion)

        raise AttributeError(msg)

    def __repr__(self) -> str:
        """
        返回 SDK 的字符串表示

        展示版本、初始化状态、适配器/模块计数，便于调试时一眼查看运行状态。
        适配器/模块计数失败时静默降级为只显示版本与初始化状态。

        :return: str SDK 的字符串表示
        """
        base = f"<ErisPulse SDK v{self.version} initialized={self._initialized}"
        try:
            adapter_count = len(self.adapter._adapters)
            module_count = len(self.module._modules)
            return f"{base} adapters={adapter_count} modules={module_count}>"
        except Exception:
            return f"{base}>"

    # ==================== 内部协调器类 ====================

    # Initializer / Uninitializer 实现已拆分至 runtime/sdk_initializer，
    # 此处以类属性别名保持 SDK.Initializer / SDK.Uninitializer 既有用法不变
    Initializer = _sdk_initializer.Initializer
    Uninitializer = _sdk_initializer.Uninitializer

    # 主动 GC 实现拆分至 runtime/proactive_gc；保留同名方法以兼容测试/子类对 SDK 的 patch
    def _start_proactive_gc(self) -> None:
        """
        {!--< internal-use >!--}
        启动主动 GC 后台任务（实现见 ``runtime/proactive_gc.start_proactive_gc``）
        """
        _pgc.start_proactive_gc(self)

    def _stop_proactive_gc(self) -> None:
        """
        {!--< internal-use >!--}
        停止主动 GC 后台任务并反注册配置钩子（实现见 ``runtime/proactive_gc.stop_proactive_gc``）
        """
        _pgc.stop_proactive_gc(self)

    @staticmethod
    def _read_gc_config() -> tuple[float, int, int, int, bool, int]:
        """
        {!--< internal-use >!--}
        读取并钳制主动 GC 框架配置（实现见 ``runtime/proactive_gc.read_gc_config``）
        """
        return _pgc.read_gc_config()

    def _on_gc_config_event(self, _data: dict) -> None:
        """
        {!--< internal-use >!--}
        proactive_gc_* 配置变更时重启 GC 任务（实现见 ``runtime/proactive_gc.on_gc_config_event``）
        """
        _pgc.on_gc_config_event(self, _data)

    @staticmethod
    def _has_handler_backlog() -> bool:
        """
        {!--< internal-use >!--}
        事件处理器洪峰检测（实现见 ``runtime/proactive_gc.has_handler_backlog``）
        """
        return _pgc.has_handler_backlog()

    @staticmethod
    def _run_full_gc_collection(
        gc_module: Any, baseline: float | None, growth_mb: int
    ) -> tuple[int, float | None]:
        """
        {!--< internal-use >!--}
        执行一次全量回收（实现见 ``runtime/proactive_gc.run_full_gc_collection``）
        """
        return _pgc.run_full_gc_collection(gc_module, baseline, growth_mb)

    def dump_state(self) -> dict:
        """
        导出框架当前运行状态的快照

        :return: dict 包含所有子系统状态的字典
        """
        import sys

        state: dict = {
            "sdk": {
                "initialized": self._initialized,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": sys.platform,
                "timestamp": time.time(),
            },
            "adapters": {"registered": [], "started": [], "bots": {}},
            "modules": {"registered": [], "lazy": [], "enabled": [], "disabled": []},
            "events": {
                "message_handlers": 0,
                "notice_handlers": 0,
                "request_handlers": 0,
                "meta_handlers": 0,
                "commands": 0,
            },
            "router": {"running": False, "http_routes": 0, "ws_routes": 0},
        }

        try:
            adapter_mgr = self.adapter
            state["adapters"]["registered"] = list(adapter_mgr._adapters.keys())
            state["adapters"]["started"] = [getattr(a, "_platform", str(a)) for a in adapter_mgr._started_instances]
            state["adapters"]["bots"] = {}
            for platform, bots in adapter_mgr._bots.items():
                state["adapters"]["bots"][platform] = {
                    bid: {"status": info.get("status", "unknown"), "last_active": info.get("last_active", 0)}
                    for bid, info in bots.items()
                }
        except Exception:
            state["adapters"]["error"] = "failed to get adapter state"

        try:
            module_mgr = self.module
            state["modules"]["registered"] = list(module_mgr._module_classes.keys())
            state["modules"]["lazy"] = list(getattr(module_mgr, "_lazy_modules", {}).keys())
            state["modules"]["enabled"] = [n for n in module_mgr._module_classes if module_mgr.is_enabled(n)]
            state["modules"]["disabled"] = [n for n in module_mgr._module_classes if not module_mgr.is_enabled(n)]
        except Exception:
            state["modules"]["error"] = "failed to get module state"

        try:
            from .Core.Event import message, meta, notice, request
            from .Core.Event.command import command as cmd_handler

            state["events"] = {
                "message_handlers": len(message.handler.handlers),
                "notice_handlers": len(notice.handler.handlers),
                "request_handlers": len(request.handler.handlers),
                "meta_handlers": len(meta.handler.handlers),
                "commands": len(cmd_handler.commands),
            }
        except Exception:
            state["events"]["error"] = "failed to get event state"

        try:
            router_mgr = self.router
            state["router"]["running"] = getattr(router_mgr, "_uvicorn_server", None) is not None
            # _http_routes/_websocket_routes 均为 namespace → 路径表 的两级结构，按路径数累计
            http_routes = getattr(router_mgr, "_http_routes", {}) or {}
            state["router"]["http_routes"] = sum(len(paths) for paths in http_routes.values())
            ws_routes = getattr(router_mgr, "_websocket_routes", {}) or {}
            state["router"]["ws_routes"] = sum(len(paths) for paths in ws_routes.values())
        except Exception:
            state["router"]["error"] = "failed to get router state"

        return state

    async def init(
        self,
        *,
        before_init: Callable[[], Any] | None = None,
        after_init: Callable[[], Any] | None = None,
    ) -> bool:
        """
        SDK 初始化入口

        重复调用保护：若 SDK 已经初始化成功，重复调用不会重新初始化，
        会记录一条警告并直接返回 True。如需强制重新初始化，请先
        调用 ``sdk.uninit()`` 或使用 ``sdk.restart()``。

        :param before_init: 初始化前回调（同步或异步），在环境准备之前执行
        :param after_init: 初始化成功后回调（同步或异步），在初始化完成后执行
        :return: bool SDK 初始化是否成功（已初始化时返回 True）

        :example:
        >>> success = await sdk.init()
        >>> if success:
        >>>     await sdk.adapter.startup()
        >>>
        >>> # 使用回调
        >>> async def setup():
        ...     print("初始化前")
        >>> async def ready():
        ...     print("初始化完成")
        >>> await sdk.init(before_init=setup, after_init=ready)
        """
        if self._initialized:
            # 已初始化时仅警告并直接返回成功，避免重复初始化破坏内部状态。
            # 告警通道不可用（i18n/logger 未就绪）时降级 stderr，不允许静默。
            try:
                self.logger.warning(i18n.t("core.sdk.init.already_initialized"))
            except Exception:
                import sys

                print(
                    "[ErisPulse] sdk.init() called but already initialized",
                    file=sys.stderr,
                )
            return True

        # before_init 回调：在环境准备之前执行
        if before_init is not None:
            try:
                result = before_init()
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                self.logger.error(i18n.t("core.sdk.callback.before_init_failed", error=e))

        if not await self._prepare_environment():
            return False

        # 创建初始化协调器
        self._initializer = self._kernel.get_initializer()

        # 执行初始化
        self._initialized = await self._initializer.init()

        # after_init 回调：初始化成功后执行
        if self._initialized and after_init is not None:
            try:
                result = after_init()
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                self.logger.error(i18n.t("core.sdk.callback.after_init_failed", error=e))

        return self._initialized

    async def _prepare_environment(self) -> bool:
        """
        {!--< internal-use >!--}
        准备运行环境

        初始化配置和全局异常处理

        :return: bool 环境准备是否成功
        """
        from .runtime import setup_exception_handling

        setup_exception_handling()

        _lifecycle = self.lifecycle
        _logger = self.logger

        await _lifecycle.submit_event(
            "core.init.start",
            msg=i18n.t("core.sdk.prepare.start"),
        )

        _logger.info(i18n.t("core.sdk.prepare.starting"))
        try:
            from .runtime import get_erispulse_config

            get_erispulse_config()
            _logger.info(i18n.t("core.sdk.prepare.config_loaded"))

            # 确保 config.full.example 存在 / 随生成器版本刷新：未走 epsdk init
            # 直接运行（sdk.run / main.py）的用户同样获得完整配置参考
            try:
                from pathlib import Path as _Path

                from .Core.config import config as _config_manager
                from .runtime.example_config import ensure_full_example

                config_dir = _Path(getattr(_config_manager, "CONFIG_FILE", "config/config.toml")).parent
                if str(config_dir) == ".":
                    config_dir = _Path("config")
                ensure_full_example(config_dir=config_dir)
            except Exception:
                pass
            return True
        except Exception as e:
            load_duration = _lifecycle.stop_timer(LIFECYCLE_TIMER_CORE_INIT)
            await _lifecycle.submit_event(
                "core.init.complete",
                msg=i18n.t("core.sdk.init.module_init_failed"),
                data={
                    "duration": load_duration,
                    "success": False,
                },
            )
            _logger.error(i18n.t("core.sdk.prepare.failed", error=e))
            return False

    def init_sync(
        self,
        *,
        before_init: Callable[[], Any] | None = None,
        after_init: Callable[[], Any] | None = None,
    ) -> bool:
        """
        SDK 初始化入口（同步版本）

        用于命令行直接调用，自动在事件循环中运行异步初始化

        :param before_init: 初始化前回调（同步或异步）
        :param after_init: 初始化成功后回调（同步或异步）
        :return: bool SDK 初始化是否成功
        """
        return asyncio.run(
            self.init(before_init=before_init, after_init=after_init)
        )

    def init_task(
        self,
        *,
        before_init: Callable[[], Any] | None = None,
        after_init: Callable[[], Any] | None = None,
    ) -> asyncio.Task | concurrent.futures.Future:
        """
        SDK 初始化入口，返回 Task 对象

        :param before_init: 初始化前回调（同步或异步）
        :param after_init: 初始化成功后回调（同步或异步）
        :return: asyncio.Task 初始化任务（在事件循环内调用时）；并发 Future
            （无运行循环但主循环已注册时，经线程安全方式调度回主循环）
        :raises RuntimeError: 当前无运行中的事件循环且主循环未注册——
            此前本场景会新建一个永不运行的循环并返回永不完成的悬挂 Task
        """

        async def _async_init():
            if before_init is not None:
                try:
                    result = before_init()
                    if inspect.isawaitable(result):
                        await result
                except Exception as e:
                    self.logger.error(i18n.t("core.sdk.callback.before_init_failed", error=e))

            if not await self._prepare_environment():
                return False

            self._initializer = self._kernel.get_initializer()
            self._initialized = await self._initializer.init()

            if self._initialized and after_init is not None:
                try:
                    result = after_init()
                    if inspect.isawaitable(result):
                        await result
                except Exception as e:
                    self.logger.error(i18n.t("core.sdk.callback.after_init_failed", error=e))

            return self._initialized

        try:
            return asyncio.create_task(_async_init())
        except RuntimeError:
            from .runtime.tasks import _get_main_loop

            loop = _get_main_loop()
            if loop is not None and loop.is_running():
                return asyncio.run_coroutine_threadsafe(_async_init(), loop)
            raise RuntimeError(
                "init_task() requires a running event loop: call it from async code, "
                "or start the SDK main loop first (e.g. run()/init())"
            ) from None

    async def load_module(self, module_name: str) -> bool:
        """
        手动加载指定模块

        :param module_name: str 要加载的模块名称
        :return: bool 加载是否成功

        :example:
        >>> await sdk.load_module("MyModule")
        """
        try:
            module_instance = getattr(self, module_name, None)
            if isinstance(module_instance, LazyModule):
                # 检查模块是否需要异步初始化
                if hasattr(
                    module_instance, "_needs_async_init"
                ) and object.__getattribute__(module_instance, "_needs_async_init"):
                    # 对于需要异步初始化的模块，执行完整异步初始化
                    await module_instance._initialize()
                    object.__setattr__(module_instance, "_needs_async_init", False)
                    return True
                # 检查模块是否已经同步初始化但未完成异步部分
                if object.__getattribute__(
                    module_instance, "_initialized"
                ) and object.__getattribute__(module_instance, "_is_base_module"):
                    # 如果是 BaseModule 子类且已同步初始化，只需完成异步部分
                    await module_instance._complete_async_init()
                    return True
                # 触发懒加载模块的完整初始化
                await module_instance._initialize()
                return True
            if module_instance is not None:
                self.logger.warning(
                    i18n.t("core.sdk.module.already_loaded", name=module_name)
                )
                return False
            self.logger.error(i18n.t("core.sdk.module.not_found", name=module_name))
            return False
        except Exception as e:
            self.logger.error(
                i18n.t("core.sdk.module.load_failed", name=module_name, error=e)
            )
            return False

    async def run(
        self,
        keep_running: bool = True,
        *,
        before_init: Callable[[], Any] | None = None,
        after_init: Callable[[], Any] | None = None,
        on_ready: Callable[[], Any] | None = None,
    ) -> None:
        """
        无头模式运行 ErisPulse

        内部调用 ``init()`` 完成初始化，然后在 ``on_ready`` 回调执行完毕后
        挂起主程序（当 ``keep_running=True`` 时）。

        硬重启（``hard_restart()``）通过退出码 42 契约交由**外部
        监督者**（``epsdk run`` / systemd / Docker / PM2 等，见 startup.md
        「监督者指南」）重新拉起。

        {!--< tips >!--}
        异常处理原则：
        1. 模块/适配器的任何错误都会被拦截，不会导致进程退出
        2. 只有 KeyboardInterrupt（Ctrl+C）会正常向上传播，触发优雅关闭
        3. 其他 BaseException（如 SystemExit）会被拦截并记录，防止意外终止

        回调执行顺序::

            before_init → 初始化 → after_init → on_ready → [挂起]

        回调可以是同步或异步函数，框架自动检测并 await。
        回调中的异常会被捕获并记录日志，不会中断启动流程。
        {!--< /tips >!--}

        :param keep_running: bool 是否保持运行
        :param before_init: 初始化前回调，转发给 ``init()``
        :param after_init: 初始化成功后回调，转发给 ``init()``
        :param on_ready: 初始化完成且 ``after_init`` 执行后、挂起前的回调

        :example:
        >>> await sdk.run(keep_running=True)
        >>>
        >>> # 使用 on_ready 回调
        >>> async def on_startup():
        ...     print("SDK 就绪，开始业务逻辑")
        >>> await sdk.run(on_ready=on_startup)
        >>>
        >>> # 分阶段回调
        >>> async def before():
        ...     print("即将初始化")
        >>> async def after():
        ...     print("初始化完成，适配器已就绪")
        >>> async def ready():
        ...     print("一切就绪，开始挂起")
        >>> await sdk.run(before_init=before, after_init=after, on_ready=ready)
        """
        try:
            # 注册主事件循环，供后台线程（config watcher 等）把协程调度回主循环，
            # 避免热更新在临时事件循环中执行业务代码导致 "attached to a different loop"
            try:
                from .runtime.tasks import register_main_loop

                register_main_loop(asyncio.get_running_loop())
            except Exception:
                pass

            isInit = await self.init(
                before_init=before_init, after_init=after_init
            )

            if not isInit:
                self.logger.error(i18n.t("core.sdk.run.init_failed"))
                # 致命初始化失败（非端口占用——端口失败已降级为跳过服务器启动）：
                # 以非 0 退出码退出，让 Docker / ep run 运行器能正确识别为异常退出。
                sys.exit(1)

            # on_ready 回调：初始化完成后、挂起前执行
            if on_ready is not None:
                try:
                    result = on_ready()
                    if inspect.isawaitable(result):
                        await result
                except Exception as e:
                    self.logger.error(i18n.t("core.sdk.callback.on_ready_failed", error=e))

            if keep_running:
                self._shutdown_event = asyncio.Event()
                self._register_signal_handlers()
                await self._shutdown_event.wait()
        except asyncio.CancelledError:
            self.logger.info(i18n.t("core.sdk.run.shutdown_signal"))
        except KeyboardInterrupt:
            # Ctrl+C / SIGINT: 允许正常传播，触发优雅关闭
            self.logger.info(i18n.t("core.sdk.run.shutdown_signal"))
            raise
        except Exception as e:
            # 常规异常（模块/适配器错误等），记录但不向上传播
            self.logger.error(i18n.t("core.sdk.run.unhandled_error", error=repr(e)))
        except BaseException as e:
            # 其他 BaseException（SystemExit 等），拦截并记录
            # 模块/适配器不应能终止进程
            self.logger.error(i18n.t("core.sdk.run.unexpected_error", error=repr(e)))
        finally:
            if keep_running:
                try:
                    await self.uninit()
                except Exception:
                    pass

    def shutdown(self) -> None:
        """
        请求优雅关闭

        设置关闭事件，使正在 ``await sdk.run()`` 挂起的主循环返回，
        进而触发 ``uninit()`` 完成资源清理。可由模块/适配器在运行时调用，
        也用作 SIGTERM 等信号的处理入口。

        :example:
        >>> sdk.shutdown()  # 任意协程中调用，触发优雅退出
        """
        if self._shutdown_event is not None and not self._shutdown_event.is_set():
            self._shutdown_event.set()

    def enable_plugin_hot_reload(self, interval: float = 1.0) -> bool:
        """
        启用本地插件文件夹热重载（自动监控）

        监控插件文件夹（默认 ``plugins/``，可通过 ``ErisPulse.framework.plugins_dir``
        配置）下 ``.py`` 文件的变更，自动重新加载对应插件。
        需在 ``await sdk.run()`` 之前调用。

        {!--< tips >!--}
        自动监控仅覆盖本地插件目录；PyPI 安装包模块可通过
        :meth:`reload_module` 手动热重载（pip 升级后调用即可）。
        {!--< /tips >!--}

        :param interval: 轮询间隔（秒，默认 1.0）
        :return: 是否启动成功（无插件目录或已在运行返回 False）

        :example:
        >>> await sdk.init()
        >>> sdk.enable_plugin_hot_reload()
        >>> await sdk.run()
        """
        if getattr(self, "_plugin_watcher", None) is not None:
            return False

        from .runtime import PluginReloadWatcher

        watcher = PluginReloadWatcher(self._reload_module, interval=interval)
        ok = watcher.start()
        if ok:
            self._plugin_watcher = watcher
            self.logger.info(i18n.t("core.sdk.hot_reload.enabled"))
        return ok

    async def reload_module(self, module_name: str, *, full: bool = True) -> bool:
        """
        热重载单个模块（手动触发，支持任意来源）

        完整执行 语法预检 → 卸载旧实例 → 清理注册与 ``sys.modules`` 缓存
        （按顶层包名 + ``invalidate_caches``，默认全量）→ 重新发现/导入 →
        重新注册并加载 流程；依赖该模块的模块会**级联重载**并默认重导代码。
        本地插件（``plugins/`` 目录）来源重扫描插件目录；运行时注册来源按
        定义模块重导并按类名重取；PyPI 安装包来源重新查询 entry-point 并
        重导入模块代码（pip 升级后调用即可生效）。

        :param module_name: 模块名（entry-point 名称、插件名或运行时注册名）
        :param full: 是否全量重载（默认 True；False 为轻量逃生门——仅按
            元数据清理缓存、PyPI 依赖者直接重新实例化，仅供超大依赖树的
            性能敏感场景）
        :return: 是否重载成功

        :example:
        >>> await sdk.reload_module("dice")      # 本地插件
        >>> await sdk.reload_module("MyRuntime") # 运行时注册模块
        >>> await sdk.reload_module("Weather")   # PyPI 安装包模块（默认全量）
        """
        if getattr(self, "_module_loader", None) is None:
            self.logger.warning(i18n.t("core.sdk.hot_reload.no_loader"))
            return False
        from .runtime.reload_ops import run_reload_exclusive

        return await run_reload_exclusive(
            lambda: self._module_loader.reload_module(
                module_name, self.module, self, full=full
            )
        )

    async def reload_adapter(self, adapter_name: str, *, full: bool = True) -> bool:
        """
        热重载单个适配器（代码级，手动触发）

        完整执行 语法预检 → 卸载（shutdown 即清理：路由/事件/任务/bot offline
        + 注销）→ 清理 ``sys.modules`` 子树与 ``__pycache__`` 字节码 → 重新
        发现/导入 → 重新注册 → 原运行态则重新拉起 流程；任一步失败自动回滚
        旧注册状态（尽力而为语义：断连等 unload 副作用不可撤销）。支持本地
        插件（``plugins/`` 目录）与 PyPI 安装包两种来源。

        :param adapter_name: 适配器名（平台名称）
        :param full: 保留参数位（当前两种来源均执行全量清理，与模块语义对齐）
        :return: 是否重载成功（适配器被移除视为成功）

        :example:
        >>> await sdk.reload_adapter("aiocqhttp")  # pip 升级后调用即可生效
        """
        if getattr(self, "_adapter_loader", None) is None:
            self.logger.warning(i18n.t("core.sdk.hot_reload.no_loader"))
            return False
        from .runtime.reload_ops import run_reload_exclusive

        return await run_reload_exclusive(
            lambda: self._adapter_loader.reload_adapter(
                adapter_name, self.adapter, self, full=full
            )
        )

    async def reload_all_modules(self) -> dict[str, bool]:
        """
        全量热重载所有已注册模块（尽力而为语义）

        执行 卸载全部 → 清理全部 ``sys.modules`` 子树 → 重新发现/注册 →
        按依赖拓扑序加载 → 此前已加载的懒加载模块重新激活 流程，一次刷新
        全部模块代码（pip 批量升级后调用即可全部生效）。单模块失败仅记录
        诊断并跳过，不影响其余模块；无整体回滚（on_unload 副作用不可撤销，
        与单模块热重载语义一致）。

        :return: 模块注册名 → 是否重载成功（发现阶段即失败的模块不在结果中；
                 SDK 未初始化时返回空字典）

        :example:
        >>> await sdk.reload_all_modules()
        """
        if getattr(self, "_module_loader", None) is None:
            self.logger.warning(i18n.t("core.sdk.hot_reload.no_loader"))
            return {}
        from .runtime.reload_ops import run_reload_exclusive

        return await run_reload_exclusive(
            lambda: self._module_loader.reload_all(self.module, self)
        )

    async def _reload_module(self, module_name: str) -> bool:
        """
        {!--< internal-use >!--}
        插件热发现回调（由 PluginReloadWatcher 调度）：按名字路由

        已知模块 → 单模块热重载；已知适配器 → 适配器代码级热重载（适配器
        插件文件的保存/删除此前完全无自动反应）；全新文件（on_created）→
        先按模块插件热装载，不是模块插件再按适配器插件热装载。失败仅记录
        不抛异常。

        :param module_name: 插件名（由插件目录路径解析）
        :return: 是否成功（路由失败/异常为 False）
        """
        try:
            module_loader = getattr(self, "_module_loader", None)
            if (
                module_loader is not None
                and module_loader._last_module_objs.get(module_name) is not None
            ):
                return bool(await self.reload_module(module_name))
            adapter_loader = getattr(self, "_adapter_loader", None)
            if adapter_loader is not None and (
                module_name in (getattr(self.adapter, "_adapter_info", {}) or {})
                or module_name in adapter_loader._last_adapter_objs
            ):
                return bool(await self.reload_adapter(module_name))
            if module_loader is not None:
                result = await module_loader.load_new_plugin(
                    module_name, self.module, self
                )
                if result is not None:
                    return result
            if adapter_loader is not None:
                result = await adapter_loader.load_new_adapter_plugin(
                    module_name, self.adapter, self
                )
                return bool(result)
            return False
        except Exception as e:
            self.logger.error(i18n.t("core.sdk.hot_reload.failed", name=module_name, error=e))
            return False

    def stop_plugin_hot_reload(self) -> None:
        """
        停止本地插件热重载监控
        """
        watcher = getattr(self, "_plugin_watcher", None)
        if watcher is not None:
            watcher.stop()
            self._plugin_watcher = None

    def _register_signal_handlers(self) -> None:
        """
        {!--< internal-use >!--}
        注册进程信号处理器，将 SIGTERM / SIGHUP 等信号转为优雅关闭

        Windows 不支持 ``loop.add_signal_handler``，捕获异常后跳过
        （Windows 下仍可通过 ``sdk.shutdown()`` 或 Ctrl+C 触发关闭）。
        """
        import signal

        loop = asyncio.get_running_loop()

        def _on_signal():
            self.logger.info(i18n.t("core.sdk.run.shutdown_signal"))
            self.shutdown()

        for sig_name in ("SIGTERM", "SIGHUP"):
            sig = getattr(signal, sig_name, None)
            if sig is None:
                continue
            try:
                loop.add_signal_handler(sig, _on_signal)
            except (NotImplementedError, RuntimeError, ValueError):
                # Windows / 某些事件循环不支持 add_signal_handler
                pass

    async def _do_restart(self) -> bool:
        """
        {!--< internal-use >!--}
        实际执行软重启的内部方法（联动热重载系统）

        在后台任务中运行，与调用 restart() 的事件处理器解耦，
        确保即使调用者被取消，重启流程也能完整执行。

        软重启 = **组件层代码级热重载**（2.11 起不再整体 uninit/init）：
        1. 全部已加载模块走统一热重载管线（``reload_all_modules``：
           整体语法预检 → 卸载 → 清 sys.modules / __pycache__ → 重发现重导 →
           重新注册加载 → 懒激活；预检失败整轮拒绝，旧实例继续服务）
        2. 适配器层先重发现 entry-point（运行中 pip 新装/卸载的适配器即刻
           生效——装完即用），再逐个走 ``reload_adapter``（卸载清理 → 清缓存
           重发现 → 重新注册 → 原运行态重新拉起）

        全程持热重载互斥锁（与单模块重载/归眠串行）；保存风暴下 restart
        请求自动合并——进行中的请求置 dirty 标记，本轮完成后补跑至多一轮。

        配置热更新由配置监听器处理；框架自身更新等整进程场景请使用
        ``hard_restart()``。

        :return: bool 软重启是否全部成功（任一组件失败即为 False，
                 失败清单见日志）
        """
        from .runtime.reload_ops import reload_ops

        try:
            async with reload_ops:
                reload_ops.begin_restart_section()
                while True:
                    result = await self._execute_restart_once()
                    if not reload_ops.consume_restart_dirty():
                        return result
        except Exception as e:
            self.logger.error(i18n.t("core.sdk.reload.failed", error=e))
            return False

    async def _execute_restart_once(self) -> bool:
        """
        {!--< internal-use >!--}
        单轮软重启执行体（互斥与补跑循环由 ``_do_restart`` 负责）
        """
        self.logger.info(i18n.t("core.sdk.reload.starting"))

        # 1. 模块层：统一热重载管线（含整体预检 / 快照回滚 / 身份核对）
        module_results = await self.reload_all_modules()

        # 2. 适配器层：先重发现（新装/卸载即刻生效），再逐个代码级热重载
        adapter_results: dict[str, bool] = {}
        known_adapters = set(getattr(self.adapter, "_adapter_info", {}) or {})
        new_adapters: list[str] = []
        if getattr(self, "_adapter_loader", None) is not None:
            try:
                objs, _enabled, _disabled = await self._adapter_loader.load(
                    self.adapter, quiet=True
                )
                if objs:
                    await self._adapter_loader.register_to_manager(
                        list(objs.keys()), objs, self.adapter
                    )
                new_adapters = [n for n in objs if n not in known_adapters]
            except Exception as e:
                self.logger.error(
                    i18n.t("core.sdk.reload.adapter_rediscover_failed", error=e)
                )
        for adapter_name in list(getattr(self.adapter, "_adapter_info", {}) or {}):
            if adapter_name in new_adapters:
                # 新适配器：按启用状态拉起（装完即用）；启动失败不判重启失败
                try:
                    if self.adapter.is_enabled(adapter_name):
                        await self.adapter.startup(adapter_name)
                        self.logger.info(
                            i18n.t("core.sdk.reload.adapter_started", name=adapter_name)
                        )
                    adapter_results[adapter_name] = True
                except Exception as e:
                    self.logger.error(
                        i18n.t(
                            "core.sdk.reload.adapter_failed",
                            name=adapter_name,
                            error=e,
                        )
                    )
                    adapter_results[adapter_name] = False
                continue
            try:
                adapter_results[adapter_name] = await self.reload_adapter(adapter_name)
            except Exception as e:
                self.logger.error(
                    i18n.t(
                        "core.sdk.reload.adapter_failed",
                        name=adapter_name,
                        error=e,
                    )
                )
                adapter_results[adapter_name] = False

        failed_modules = sorted(
            n for n, ok in module_results.items() if not ok
        )
        failed_adapters = sorted(
            n for n, ok in adapter_results.items() if not ok
        )
        if failed_modules or failed_adapters:
            self.logger.warning(
                i18n.t(
                    "core.sdk.reload.partial_failed",
                    modules=", ".join(failed_modules) or "-",
                    adapters=", ".join(failed_adapters) or "-",
                )
            )

        self.logger.info(i18n.t("core.sdk.reload.complete"))
        return not failed_modules and not failed_adapters

    async def restart(self) -> bool:
        """
        SDK 软重启（联动热重载系统）

        全部已加载模块与适配器走统一**代码级热重载管线**（语法预检 → 卸载 →
        清 ``sys.modules`` / ``__pycache__`` → 重发现重导 → 重新注册加载 /
        拉起；失败快照回滚，单组件失败不影响其余），不再整体 ``uninit()`` /
        ``init()``——框架进程、路由与配置监听保持在线，组件代码（pip 升级后）
        即刻生效。

        {!--< tips >!--}
        **重要设计说明**：

        此方法使用后台任务将重启流程注册到事件循环调度器，与调用栈完全解耦
        （事件处理器内调用不会中断当前事件链路）；立即返回 ``True`` 表示
        "重启任务已成功调度"而非"重启已完成"。

        重启请求自动合并：已有 restart 进行中时，本次调用只置合并标记
        （进行中的一轮完成后补跑至多一轮），绝不并发交叉。

        **语义分界**（2.11 起）：

        - ``restart()``：组件层代码热重载（模块 + 适配器；pip 升级组件、
          新装适配器 entry-point 均即刻生效）
        - ``hard_restart()``：整进程重启（框架自身更新 / 结构性配置变更
          等需要全新解释器的场景）
        {!--< /tips >!--}

        :return: bool 重启任务是否成功调度（并非重启是否完成）

        :example:
        >>> await sdk.restart()
        """
        from .runtime.reload_ops import reload_ops

        # 使用 spawn_background 将任务注册到事件循环调度器 - 不受上层协程取消影响
        from .runtime.tasks import spawn_background

        if not reload_ops.mark_restart_pending():
            spawn_background(self._do_restart())

        return True

    RESTART_EXIT_CODE = HARD_RESTART_EXIT_CODE

    def is_supervised(self) -> bool:
        """
        检测当前进程是否由外部监督者启动（CLI run 命令 / systemd / Docker 等）

        监督者会在进程退出码为 42（``HARD_RESTART_EXIT_CODE``）时重新拉起新进程。
        未被监督时硬重启后进程不会自动恢复，``hard_restart()`` 会打出警告提醒
        配置外部监督者（见 startup.md「监督者指南」）。

        :return: 是否有外部监督者
        """
        import os

        return bool(os.environ.get(ENV_SUPERVISED))

    async def hard_restart(self, reason: str = "") -> bool:
        """
        硬重启：反初始化后退出进程，由外部监督者重新启动新实例

        与 restart() 的区别：

        - restart(): 组件层代码热重载——模块与适配器统一走热重载管线
          （含运行中新装适配器的重发现拉起），框架进程保持在线
        - hard_restart(): 反初始化后以退出码 42 退出进程，由外部监督者
          重新拉起全新进程——用于框架自身更新等只有新解释器才能清干净
          状态的场景（升级后的框架代码、C 扩展、累积泄漏）

        硬重启依赖外部监督者（``epsdk run`` / systemd / Docker / PM2 / supervisord）
        在退出码 42 时重新拉起进程；未被监督时进程退出后不会自动恢复，会打警告提醒。
        监督场景下退出前会把 ``reason`` 写入运行状态文件（``.erispulse/runtime.json``
        的 ``hard_restart_reason`` 字段），监督者重拉时向用户展示。

        :param reason: 硬重启原因（可选，供监督者展示与排障）
        :return: bool 硬重启任务是否成功调度

        :example:
        >>> await sdk.hard_restart("sdk self-update")
        """

        async def _do_hard_restart():
            # 让"重启中"的响应先送达再退出进程
            await asyncio.sleep(SDK_HARD_RESTART_SETTLE_DELAY_SECS)
            try:
                self.logger.info(i18n.t("core.sdk.hardrestart.starting"))
                await self.uninit()
                self.logger.info(i18n.t("core.sdk.hardrestart.uninit_done"))
            except Exception as e:
                self.logger.error(i18n.t("core.sdk.hardrestart.uninit_error", error=e))
            # os._exit 会跳过 atexit 钩子；uninit 中途异常可能错过 force_save，
            # 此处显式兜底刷盘脏配置，避免丢失未持久化的 setConfig 写入
            try:
                from .Core.config import config as _config_manager
                _config_manager.force_save()
            except Exception:
                pass
            if self.is_supervised():
                # 监督场景：退出前写入硬重启标记（原因/PID/时间），
                # 监督者重拉时展示——os._exit 绕过 finally，状态文件由新进程重写
                try:
                    from .runtime import process_state

                    process_state.mark_hard_restart(reason=reason, pid=os.getpid())
                except Exception:
                    pass
            else:
                self.logger.warning(
                    i18n.t(
                        "core.sdk.hardrestart.not_supervised",
                        code=self.RESTART_EXIT_CODE,
                    )
                )
            os._exit(self.RESTART_EXIT_CODE)

        from .runtime.tasks import spawn_background

        spawn_background(_do_hard_restart())
        return True


    def get_topology(self, *, json_safe: bool = True) -> dict[str, Any]:
        """
        获取完整的拓扑树数据（便于 Dashboard 等管理界面展示）

        聚合模块、适配器与作用域的归属关系：
        - ``modules``：每个模块拥有的命令 / 事件处理器 / 路由 / 生命周期钩子
        - ``adapters``：每个适配器的运行状态、下属 Bot 状态与作用域绑定
        - ``scope``：作用域（模块 / 身份 / 文本 / 出站动作）

        :param json_safe: 是否输出可直接 JSON 序列化的安全结构（默认 True）。
                          安全模式下模块 ``info`` 只保留纯数据 meta 子表，
                          并对整树做序列化兜底净化，返回值可直接 ``json.dumps``。

        :return: 拓扑树字典
            {"modules": {...}, "adapters": {...}, "scope": {...}}

        :example:
        >>> topology = sdk.get_topology()
        >>> topology["modules"]["Chat"]["commands"]
        ["chat"]
        """
        return {
            "modules": self.module.get_topology(json_safe=json_safe).get("modules", {}),
            "adapters": self.adapter.get_topology(json_safe=json_safe).get("adapters", {}),
            "scope": self.scope.topology(),
        }

    async def uninit(self) -> bool:
        """
        SDK 反初始化

        执行以下操作：
        1. 关闭所有适配器
        2. 卸载所有模块
        3. 清理所有事件处理器
        4. 清理适配器管理器和模块管理器
        5. 清理 SDK 对象上的模块属性

        :return: bool 反初始化是否成功

        :example:
        >>> await sdk.uninit()
        """
        # 创建反初始化协调器
        uninitializer = self._kernel.get_uninitializer()

        # 执行反初始化
        return await uninitializer.uninit()


# 创建全局 SDK 实例
sdk: SDK = SDK()

__all__ = ["SDK", "sdk"]
