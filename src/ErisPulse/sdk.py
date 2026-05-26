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
import importlib
import sys
from typing import TYPE_CHECKING

# 导入核心模块
from .Core import Event, lifecycle, logger
from .Core import storage, env, config
from .Core import adapter, BaseAdapter, SendDSL, BaseStorage, BaseQueryBuilder
from .Core import module, router
from .Core.lifecycle import LifecycleManager
from .Core.adapter import AdapterManager
from .Core.storage import StorageManager
from .Core.Bases.storage import BaseStorage as _BaseStorage
from .Core.Bases.storage import BaseQueryBuilder as _BaseQueryBuilder
from .Core.logger import Logger
from .Core.module import ModuleManager
from .Core.router import RouterManager
from .Core.config import ConfigManager

# 导入懒加载模块类
from .loaders.module import LazyModule

# 导入加载器类
from .loaders.adapter import AdapterLoader
from .loaders.module import ModuleLoader

if TYPE_CHECKING:
    from types import ModuleType


class SDK:
    """
    ErisPulse SDK 主类

    整合所有核心模块和加载器，提供统一的初始化和管理接口

    {!--< tips >!--}
    SDK 提供以下核心属性：
    - Event: 事件系统
    - lifecycle: 生命周期管理器
    - logger: 日志管理器
    - storage: 存储管理器
    - env: 存储管理器别名
    - config: 配置管理器
    - adapter: 适配器管理器
    - BaseAdapter: 适配器基类
    - SendDSL: DSL 发送接口基类
    - module: 模块管理器
    - router: 路由管理器
    {!--< /tips >!--}
    """

    # ==================== 核心模块属性 ====================

    Event: ModuleType
    """事件系统"""

    lifecycle: LifecycleManager
    """生命周期管理器"""

    logger: Logger
    """日志管理器"""

    storage: StorageManager
    """存储管理器"""

    env: StorageManager
    """存储管理器别名"""

    config: ConfigManager
    """配置管理器"""

    adapter: AdapterManager
    """适配器管理器"""

    BaseAdapter: type[BaseAdapter]
    """适配器基类"""

    SendDSL: type[SendDSL]
    """DSL 发送接口基类"""

    BaseStorage: type[_BaseStorage]
    """存储后端抽象基类"""

    BaseQueryBuilder: type[_BaseQueryBuilder]
    """查询构建器抽象基类"""

    module: ModuleManager
    """模块管理器"""

    router: RouterManager
    """路由管理器"""

    def __init__(self):
        """
        初始化 SDK 实例

        挂载所有核心模块到 SDK 实例
        """
        self.Event = Event
        self.lifecycle = lifecycle
        self.logger = logger

        self.storage = storage
        self.env = env
        self.config = config

        self.adapter = adapter
        adapter.set_sdk_ref(self)

        self.BaseAdapter = BaseAdapter
        self.SendDSL = SendDSL

        self.BaseStorage = BaseStorage
        self.BaseQueryBuilder = BaseQueryBuilder

        self.module = module
        module.set_sdk_ref(self)

        self.router = router

        self._initializer: SDK.Initializer | None = None
        self._initialized: bool = False

    def __getattribute__(self, name: str):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            from .Core.logger import logger as _logger

            # 区分不同场景，提供更准确的错误提示
            if not name.startswith("_"):
                if name in self.module._module_classes:
                    _logger.error(
                        f"[SDK] 模块 '{name}' 已注册但未加载或未启用，请检查模块配置"
                    )
                elif name in self.adapter._adapters:
                    _logger.error(
                        f"[SDK] 适配器 '{name}' 已注册但未启用，请检查适配器配置"
                    )
                else:
                    _logger.error(
                        f"[SDK] 未找到属性或模块/适配器 '{name}'，请检查名称是否正确"
                    )

            raise AttributeError(f"ErisPulse SDK has no attribute '{name}'")

    def __repr__(self) -> str:
        """
        返回 SDK 的字符串表示

        :return: str SDK 的字符串表示
        """
        return f"<ErisPulse SDK initialized={self._initialized}>"

    # ==================== 内部协调器类 ====================

    class Initializer:
        """
        初始化协调器

        协调适配器和模块的加载流程，提供统一的初始化接口

        {!--< tips >!--}
        使用方式：
        >>> initializer = Initializer(sdk_instance)
        >>> success = await initializer.init()
        {!--< /tips >!--}
        """

        def __init__(self, sdk_instance: SDK) -> None:
            """
            初始化协调器

            :param sdk_instance: SDK 实例
            """
            self._sdk = sdk_instance
            self._adapter_loader = AdapterLoader()
            self._module_loader = ModuleLoader()

        async def init(self) -> bool:
            """
            初始化所有模块和适配器

            执行步骤:
            1. 并行发现适配器和模块
            2. 注册适配器
            3. 启动适配器
            4. 注册模块
            5. 初始化模块
            6. 启动路由服务器

            :return: bool 初始化是否成功

            :raises ImportError: 当加载失败时抛出
            """
            logger.info("SDK 正在初始化...")
            lifecycle.start_timer("core.init")

            try:
                # 1. 并行加载适配器和模块
                adapter_manager = self._sdk.adapter
                module_manager = self._sdk.module

                # 模块发现阶段
                logger.print_section_header("入口发现阶段")

                (adapter_result, module_result) = await asyncio.gather(
                    self._adapter_loader.load(adapter_manager),
                    self._module_loader.load(module_manager),
                    return_exceptions=True,
                )

                # 检查是否有异常，使用空结果继续而非终止
                if isinstance(adapter_result, Exception):
                    logger.error(f"适配器加载失败: {adapter_result}")
                    adapter_result = ({}, [], [])

                if isinstance(module_result, Exception):
                    logger.error(f"模块加载失败: {module_result}")
                    module_result = ({}, [], [])

                # 解包结果
                adapter_objs, enabled_adapters, disabled_adapters = adapter_result  # type: ignore
                module_objs, enabled_modules, disabled_modules = module_result  # type: ignore

                # 2. 注册适配器
                logger.print_section_header("适配器注册阶段")
                if not await self._adapter_loader.register_to_manager(
                    enabled_adapters, adapter_objs, adapter_manager
                ):
                    logger.warning("部分适配器注册失败，已跳过")

                # 3. 启动适配器
                if enabled_adapters:
                    logger.print_section_header("适配器启动阶段")
                    await adapter_manager.startup()

                # 4. 注册模块
                logger.print_section_header("模块注册阶段")
                if not await self._module_loader.register_to_manager(
                    enabled_modules, module_objs, module_manager
                ):
                    logger.warning("部分模块注册失败，已跳过")

                # 4. 初始化模块（创建实例并挂载到 SDK）
                logger.print_section_header("模块初始化阶段")
                if enabled_modules:
                    success = await self._module_loader.initialize_modules(
                        enabled_modules, module_objs, module_manager, self._sdk
                    )
                    if not success:
                        logger.warning("部分模块初始化失败，已跳过")
                else:
                    success = True

                # 6. 启动路由服务器
                logger.print_section_header("路由服务器启动")
                from ErisPulse.runtime import get_server_config

                _server_config = get_server_config()
                try:
                    await router.start(
                        host=_server_config["host"],
                        port=_server_config["port"],
                        ssl_certfile=_server_config.get("ssl_certfile"),
                        ssl_keyfile=_server_config.get("ssl_keyfile"),
                    )
                except Exception as e:
                    logger.warning(f"路由服务器启动失败: {e}")

                # 获取加载耗时
                load_duration = lifecycle.stop_timer("core.init")

                # 总结
                logger.print_section_header("初始化完成")

                # 显示耗时
                duration_str = (
                    f"{load_duration:.2f}s"
                    if load_duration >= 1
                    else f"{load_duration * 1000:.0f}ms"
                )
                logger.print_info(f"耗时: {duration_str}", level=1)

                if enabled_adapters:
                    logger.print_info(f"适配器: {len(enabled_adapters)} 个", level=1)
                    for i, adapter in enumerate(enabled_adapters):
                        is_last = i == len(enabled_adapters) - 1
                        logger.print_tree_item(adapter, level=1, is_last=is_last)
                else:
                    logger.print_info("适配器: 无", level=1)

                if enabled_modules:
                    logger.print_info(f"模块: {len(enabled_modules)} 个", level=1)
                    for i, module in enumerate(enabled_modules):
                        is_last = i == len(enabled_modules) - 1
                        logger.print_tree_item(module, level=1, is_last=is_last)
                else:
                    logger.print_info("模块: 无", level=1)

                logger.print_section_footer()

                logger.info(f"SDK初始化成功 (耗时: {duration_str})")

                await lifecycle.submit_event(
                    "core.init.complete",
                    msg="模块初始化完成" if success else "模块初始化部分失败",
                    data={
                        "duration": load_duration,
                        "success": success,
                        "adapters": {
                            "enabled": enabled_adapters,
                            "disabled": disabled_adapters,
                        },
                        "modules": {
                            "enabled": enabled_modules,
                            "disabled": disabled_modules,
                        },
                    },
                )
                return True

            except Exception as e:
                load_duration = lifecycle.stop_timer("core.init")
                await lifecycle.submit_event(
                    "core.init.complete",
                    msg="模块初始化失败",
                    data={"duration": load_duration, "success": False, "error": str(e)},
                )
                logger.critical(f"SDK初始化严重错误: {e}")
                return False  # 核心初始化级别的异常仍然返回 False

    class Uninitializer:
        """
        反初始化协调器

        协调适配器和模块的卸载流程，提供统一的反初始化接口

        {!--< tips >!--}
        使用方式：
        >>> uninitializer = Uninitializer(sdk_instance)
        >>> success = await uninitializer.uninit()
        {!--< /tips >!--}
        """

        def __init__(self, sdk_instance: SDK) -> None:
            """
            反初始化协调器

            :param sdk_instance: SDK 实例
            """
            self._sdk = sdk_instance

        async def uninit(self) -> bool:
            """
            执行反初始化

            执行步骤:
            1. 关闭所有适配器实例
            2. 卸载所有模块
            3. 停止路由服务器
            4. 清理所有事件处理器
            5. 清理适配器管理器和模块管理器
            6. 清理 LazyModule 引用
            7. 清理单例残留状态
            8. 清理 SDK 模块属性
            9. 重置初始化状态

            :return: bool 反初始化是否成功
            """
            lifecycle.start_timer("core.uninit")

            try:
                adapter_manager = self._sdk.adapter
                module_manager = self._sdk.module
                router_manager = self._sdk.router

                # 1. 关闭所有适配器
                registered_adapters = adapter_manager.list_registered()
                if registered_adapters:
                    await adapter_manager.shutdown()

                # 2. 卸载所有已加载模块
                loaded_modules = module_manager.list_loaded()
                if loaded_modules:
                    await module_manager.unload()

                # 3. 停止路由服务器
                if (
                    router_manager._server_task
                    and not router_manager._server_task.done()
                ):
                    await router_manager.stop()

                # 4. 收集 SDK 对象上的模块属性（在 clear 之前）
                instance_dict = object.__getattribute__(self._sdk, "__dict__")
                module_properties_to_clear = set()

                for module_name in loaded_modules:
                    if module_name in instance_dict:
                        module_properties_to_clear.add(module_name)

                # 处理 LazyModule（包括已初始化和未初始化的）
                for attr_name, attr_value in list(instance_dict.items()):
                    if attr_name.startswith("_"):
                        continue
                    if isinstance(attr_value, LazyModule):
                        lm_initialized = object.__getattribute__(
                            attr_value, "_initialized"
                        )
                        if lm_initialized:
                            lm_name = object.__getattribute__(
                                attr_value, "_module_name"
                            )
                            instance = object.__getattribute__(attr_value, "_instance")
                            if hasattr(instance, "on_unload"):
                                try:
                                    import inspect

                                    if inspect.iscoroutinefunction(instance.on_unload):
                                        await instance.on_unload(
                                            {"module_name": lm_name}
                                        )
                                    else:
                                        instance.on_unload({"module_name": lm_name})
                                except Exception as e:
                                    logger.warning(
                                        f"清理懒加载模块 {lm_name} 的 on_unload 失败: {e}"
                                    )
                        # 清除 LazyModule 内部引用，打破循环引用链
                        object.__setattr__(attr_value, "_sdk_ref", None)
                        object.__setattr__(attr_value, "_instance", None)
                        object.__setattr__(attr_value, "_manager_instance", None)
                        object.__setattr__(attr_value, "_module_class", None)
                        module_properties_to_clear.add(attr_name)

                # 5. 清理所有事件处理器
                Event._clear_all_handlers()

                # 6. 清理管理器
                adapter_manager.clear()
                module_manager.clear()

                # 获取清理耗时
                uninit_duration = lifecycle.stop_timer("core.uninit")

                # 7. 清理单例残留状态
                lifecycle._timers.clear()
                logger._logs.clear()
                logger._module_levels.clear()
                config.force_save()

                # 8. 清理 SDK 对象上的模块属性
                module_properties_cleared = 0
                for module_name in module_properties_to_clear:
                    try:
                        if module_name in instance_dict:
                            del instance_dict[module_name]
                            module_properties_cleared += 1
                    except Exception as e:
                        logger.warning(f"清理模块属性 {module_name} 失败: {e}")

                # 9. 重置初始化状态
                self._sdk._initialized = False
                self._sdk._initializer = None
                duration_str = (
                    f"{uninit_duration:.2f}s"
                    if uninit_duration >= 1
                    else f"{uninit_duration * 1000:.0f}ms"
                )

                # 提交生命周期事件
                await lifecycle.submit_event(
                    "core.uninit.complete",
                    msg="SDK反初始化完成",
                    data={
                        "duration": uninit_duration,
                        "success": True,
                        "adapters_closed": len(registered_adapters),
                        "modules_unloaded": len(loaded_modules),
                        "module_properties_cleared": module_properties_cleared,
                        "module_properties_to_clear": list(module_properties_to_clear),
                    },
                )

                # 等待一小段时间，确保事件处理完成
                await asyncio.sleep(0.1)

                # 9. 清理生命周期事件处理器（在所有事件完成之后）
                lifecycle._hooks.clear()

                logger.info(f"SDK反初始化成功 (耗时: {duration_str})")
                return True

            except Exception as e:
                uninit_duration = lifecycle.stop_timer("core.uninit")
                await lifecycle.submit_event(
                    "core.uninit.complete",
                    msg="SDK反初始化失败",
                    data={
                        "duration": uninit_duration,
                        "success": False,
                        "error": str(e),
                    },
                )

                # 等待一小段时间，确保事件处理完成
                await asyncio.sleep(0.1)

                # 清理生命周期事件处理器（即使在失败时也要清理）
                lifecycle._hooks.clear()

                if "attached to a different loop" in str(e):
                    # 这是一个常见的错误，通常是由于SDK在另一个事件循环中运行而导致的。
                    # 在这种情况下，我们直接返回True即可
                    return True
                logger.error(f"SDK反初始化严重错误: {e}")
                return False

    # ==================== SDK 逻辑方法 ====================

    async def init(self) -> bool:
        """
        SDK 初始化入口

        :return: bool SDK 初始化是否成功

        :example:
        >>> success = await sdk.init()
        >>> if success:
        >>>     await sdk.adapter.startup()
        """
        if not await self._prepare_environment():
            return False

        # 创建初始化协调器
        self._initializer = self.Initializer(self)

        # 执行初始化
        self._initialized = await self._initializer.init()
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

        await lifecycle.submit_event(
            "core.init.start",
            msg="开始初始化",
        )

        logger.info("准备初始化环境...")
        try:
            from .runtime import get_erispulse_config

            get_erispulse_config()
            logger.info("配置文件已加载")
            return True
        except Exception as e:
            load_duration = lifecycle.stop_timer("core.init")
            await lifecycle.submit_event(
                "core.init.complete",
                msg="模块初始化失败",
                data={
                    "duration": load_duration,
                    "success": False,
                },
            )
            logger.error(f"环境准备失败: {e}")
            return False

    def init_sync(self) -> bool:
        """
        SDK 初始化入口（同步版本）

        用于命令行直接调用，自动在事件循环中运行异步初始化

        :return: bool SDK 初始化是否成功
        """
        return asyncio.run(self.init())

    def init_task(self) -> asyncio.Task:
        """
        SDK 初始化入口，返回 Task 对象

        :return: asyncio.Task 初始化任务
        """

        async def _async_init():
            if not await self._prepare_environment():
                return False

            self._initializer = self.Initializer(self)
            self._initialized = await self._initializer.init()
            return self._initialized

        try:
            return asyncio.create_task(_async_init())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.create_task(_async_init())
            except Exception:
                loop.close()
                raise

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
                elif object.__getattribute__(
                    module_instance, "_initialized"
                ) and object.__getattribute__(module_instance, "_is_base_module"):
                    # 如果是 BaseModule 子类且已同步初始化，只需完成异步部分
                    await module_instance._complete_async_init()
                    return True
                else:
                    # 触发懒加载模块的完整初始化
                    await module_instance._initialize()
                    return True
            elif module_instance is not None:
                logger.warning(f"模块 {module_name} 已经加载")
                return False
            else:
                logger.error(f"模块 {module_name} 不存在")
                return False
        except Exception as e:
            logger.error(f"加载模块 {module_name} 失败: {e}")
            return False

    async def run(self, keep_running: bool = True) -> None:
        """
        无头模式运行 ErisPulse

        :param keep_running: bool 是否保持运行

        :example:
        >>> await sdk.run(keep_running=True)
        """
        try:
            isInit = await self.init()

            if not isInit:
                logger.error("ErisPulse 初始化失败，请检查日志")
                return

            if keep_running:
                shutdown_event = asyncio.Event()
                await shutdown_event.wait()
        except asyncio.CancelledError:
            logger.info("收到关闭信号，正在清理...")
        except Exception as e:
            logger.error(e)
        finally:
            if keep_running:
                try:
                    await self.uninit()
                except Exception:
                    pass

    async def _do_restart(self) -> bool:
        """
        {!--< internal-use >!--}
        实际执行重启逻辑的内部方法

        在后台任务中运行，与调用 restart() 的事件处理器解耦
        确保即使调用者被取消，重启流程也能完整执行

        重启流程:
        1. 收集已加载包的顶层模块名（必须在 uninit 之前）
        2. 反初始化（关闭适配器、卸载模块、清理状态）
        3. 清除外部包的 sys.modules 缓存
        4. 清除 ErisPulse 框架子模块缓存（支持框架自身热更新）
        5. 清除 importlib.metadata 缓存（确保 entry_points 返回最新数据）
        6. 重新初始化
        7. 重新启动适配器

        :return: bool 重新加载是否成功
        """
        try:
            # 获取所有已加载包的顶层 Python 模块名（必须在 uninit 之前，因为 uninit 会清除管理器注册信息）
            top_level_modules = self._collect_top_level_modules()
            logger.debug(f"[Reload] 收集到外部包顶层模块: {top_level_modules}")

            # 反初始化
            await self.uninit()

            # 清除外部包的 sys.modules 缓存
            self._invalidate_module_cache(top_level_modules)

            # 清除 ErisPulse 框架子模块缓存（支持框架自身热更新）
            self._invalidate_framework_cache()

            # 清除 importlib.metadata 缓存（确保 entry_points 返回最新数据）
            self._invalidate_metadata_cache()

            # 重新初始化
            if not await self.init():
                logger.error("[Reload] 初始化失败，请检查日志")
                return False

            logger.info("[Reload] 重新加载完成")
            logger.info("[Reload] ErisPulse已重新加载 [Reload]")
            return True
        except Exception as e:
            logger.error(f"[Reload] 重启失败: {e}")
            return False

    def _collect_top_level_modules(self) -> set[str]:
        """
        {!--< internal-use >!--}
        从模块和适配器管理器中收集所有已加载包的顶层 Python 模块名

        必须在 uninit() 之前调用，因为 uninit 会清除管理器中的注册信息

        :return: set[str] 顶层 Python 模块名集合
        """
        top_level_set = set()

        for module_name, info in self.module._module_info.items():
            tl = info.get("meta", {}).get("top_level", [])
            if tl:
                top_level_set.update(tl)
            else:
                fallback = self._infer_top_level(info)
                if fallback:
                    top_level_set.update(fallback)
                else:
                    logger.warning(
                        f"[Reload] 模块 '{module_name}' 无法推导顶层模块名，其缓存可能无法被清除"
                    )

        for adapter_name, info in self.adapter._adapter_info.items():
            tl = info.get("meta", {}).get("top_level", [])
            if tl:
                top_level_set.update(tl)
            else:
                fallback = self._infer_top_level(info)
                if fallback:
                    top_level_set.update(fallback)
                else:
                    logger.warning(
                        f"[Reload] 适配器 '{adapter_name}' 无法推导顶层模块名，其缓存可能无法被清除"
                    )

        logger.debug(f"[Reload] 收集到 top_level 模块: {top_level_set}")
        return top_level_set

    @staticmethod
    def _infer_top_level(info: dict) -> list[str]:
        """
        {!--< internal-use >!--}
        从模块/适配器信息中推导顶层 Python 模块名

        优先使用 top_level.txt，fallback 从 entry-point value 推导

        :param info: 模块或适配器信息字典
        :return: 顶层 Python 模块名列表
        """
        module_class = info.get("module_class") or info.get("adapter_class")
        if module_class and hasattr(module_class, "__module__"):
            top_level_name = module_class.__module__.split(".")[0]
            return [top_level_name]
        return []

    def _invalidate_module_cache(self, top_level_modules: set[str]) -> None:
        """
        {!--< internal-use >!--}
        清理 sys.modules 中属于已加载包的缓存，并刷新 importlib 缓存

        :param top_level_modules: 需要清理的顶层 Python 模块名集合
        """
        if not top_level_modules:
            return

        modules_to_remove = [
            key
            for key in sys.modules
            if any(
                key == name or key.startswith(name + ".") for name in top_level_modules
            )
        ]

        for key in modules_to_remove:
            del sys.modules[key]

        importlib.invalidate_caches()

        if modules_to_remove:
            logger.debug(
                f"[Reload] 已清理 {len(modules_to_remove)} 个外部包 sys.modules 缓存: {modules_to_remove}"
            )

    def _invalidate_framework_cache(self) -> None:
        """
        {!--< internal-use >!--}
        清理 ErisPulse 框架自身的子模块缓存，以支持框架热更新

        清除所有 ErisPulse.* 子模块的 sys.modules 缓存，但保留 ErisPulse 包本身。
        这样可以避免重新运行 __init__.py（防止创建新的 SDK 实例），
        同时确保后续的 import 语句从磁盘加载最新的框架代码。

        设计说明:
        - 保留 ErisPulse 包本身（不删除 sys.modules['ErisPulse']），
          防止 __init__.py 重新执行导致创建新的 SDK 单例
        - 清除所有 ErisPulse.* 子模块，使后续 import 从磁盘重新加载
        - 当前正在执行的代码（self 及其方法）不受影响，
          因为 Python 函数/方法持有对代码对象的直接引用
        - 新的 import 语句将加载更新后的框架代码
        """
        framework_modules = [key for key in sys.modules if key.startswith("ErisPulse.")]

        for key in framework_modules:
            del sys.modules[key]

        importlib.invalidate_caches()

        if framework_modules:
            logger.debug(f"[Reload] 已清理 {len(framework_modules)} 个框架子模块缓存")

    def _invalidate_metadata_cache(self) -> None:
        """
        {!--< internal-use >!--}
        清理 importlib.metadata 相关缓存，确保 entry_points() 返回最新数据

        当 pip install --upgrade 更新包后，importlib.metadata 的内部缓存
        可能仍然引用旧的分发元数据。清除这些缓存可以强制重新扫描
        .dist-info 目录，获取最新的 entry_points 数据。

        这对于以下场景至关重要:
        - Dashboard 热更新模块/适配器后，需要发现新安装的版本
        - 框架自身更新后，需要获取最新的 entry_points 配置
        """
        metadata_modules = [
            key for key in list(sys.modules) if key.startswith("importlib.metadata")
        ]

        for key in metadata_modules:
            try:
                del sys.modules[key]
            except KeyError:
                pass

        importlib.invalidate_caches()

        if metadata_modules:
            logger.debug(
                f"[Reload] 已清理 {len(metadata_modules)} 个 importlib.metadata 缓存"
            )

    async def restart(self) -> bool:
        """
        SDK 重新启动

        执行完整的反初始化后再初始化过程，并重新启动适配器。

        {!--< tips >!--}
        **重要设计说明**：

        此方法使用 `asyncio.ensure_future()` 将重启任务注册到事件循环调度器，
        与调用栈完全解耦。这是有意为之的设计，原因如下：

        1. **事件链路保护**：如果模块在事件处理器内部调用 `restart()`，而重启过程
           是同步等待的，那么重启会中断当前事件链路，导致事件处理不完整。

        2. **后台执行**：重启是一个耗时操作（需要关闭适配器、卸载模块、重新加载），
           使用 `ensure_future` 可以让它在后台执行，不阻塞调用者。

        3. **返回值语义**：方法立即返回 `True` 表示"重启任务已成功调度"，
           而不是"重启已完成"。实际的重启过程在后台进行。
        {!--< /tips >!--}

        :return: bool 重启任务是否成功调度（并非重启是否完成）

        :example:
        >>> await sdk.restart()
        """
        logger.info("[Reload] 开始重新加载SDK...")

        # 使用 ensure_future 将任务注册到事件循环调度器 - 不受上层协程取消影响
        asyncio.ensure_future(self._do_restart())

        return True

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
        uninitializer = self.Uninitializer(self)

        # 执行反初始化
        return await uninitializer.uninit()


# 创建全局 SDK 实例
sdk = SDK()

__all__ = ["SDK", "sdk"]
