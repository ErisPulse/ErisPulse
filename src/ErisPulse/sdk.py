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
import importlib.metadata
import inspect
import os
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .Core.constants import (
    DEFAULT_PROACTIVE_GC_INTERVAL_SECS,
    DEFAULT_UNINIT_TIMEOUT_SECS,
    LIFECYCLE_TIMER_CORE_INIT,
    LIFECYCLE_TIMER_CORE_UNINIT,
    UNINIT_SETTLE_DELAY_SECS,
)
from .Core.i18n import i18n

# 导入加载器类
from .loaders.adapter import AdapterLoader

# 导入懒加载模块类
from .loaders.module import LazyModule, ModuleLoader
from .loaders.strict import StrictModeManager

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
        StorageManager,
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
        HttpClient as _HttpClient,
    )
    from .Core import (
        SendDSL as _SendDSL,
    )


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
    client: _HttpClient
    BaseAdapter: type[_BaseAdapter]
    SendDSL: type[_SendDSL]
    BaseStorage: type[_BaseStorage]
    BaseQueryBuilder: type[_BaseQueryBuilder]
    master: MasterManager

    def __init__(self):
        """
        初始化 SDK 实例

        不缓存任何核心模块引用。核心属性通过 __getattr__ 动态解析，
        确保软重启后始终指向最新的模块级单例。
        """
        self._initializer: SDK.Initializer | None = None
        self._initialized: bool = False
        self._gc_task: asyncio.Task | None = None  # 主动 GC 后台任务

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
        try:
            return importlib.metadata.version("ErisPulse")
        except importlib.metadata.PackageNotFoundError:
            return "UnknownVersion"

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
            # 创建共享的严格模式管理器并注入到两个加载器，
            # 确保跨加载器统一收集违规、在检查点统一报告
            self._strict_manager = StrictModeManager.from_config()
            self._adapter_loader.set_strict_manager(self._strict_manager)
            self._module_loader.set_strict_manager(self._strict_manager)

        def __getattr__(self, name: str):
            """将未找到的属性委托给 SDK 实例（如 logger、adapter 等）"""
            return getattr(self._sdk, name)

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
            self.logger.info(i18n.t("core.sdk.init.starting"))
            self.lifecycle.start_timer(LIFECYCLE_TIMER_CORE_INIT)

            try:
                # 1. 并行加载适配器和模块
                adapter_manager = self.adapter
                module_manager = self.module

                # 模块发现阶段
                self.logger.print_section_header(
                    i18n.t("core.sdk.init.discovery_phase")
                )

                (adapter_result, module_result) = await asyncio.gather(
                    self._adapter_loader.load(adapter_manager),
                    self._module_loader.load(module_manager),
                    return_exceptions=True,
                )

                # 检查是否有异常，使用空结果继续而非终止
                if isinstance(adapter_result, Exception):
                    self.logger.error(
                        i18n.t(
                            "core.sdk.init.adapter_load_failed", error=adapter_result
                        )
                    )
                    adapter_result = ({}, [], [])

                if isinstance(module_result, Exception):
                    self.logger.error(
                        i18n.t("core.sdk.init.module_load_failed", error=module_result)
                    )
                    module_result = ({}, [], [])

                # 解包结果
                adapter_objs, enabled_adapters, disabled_adapters = adapter_result  # type: ignore
                module_objs, enabled_modules, disabled_modules = module_result  # type: ignore

                # 严格模式检查点 1：加载阶段违规统一报告与中止（在任何副作用前）
                self._strict_manager.raise_if_fatal()

                # 2. 注册适配器
                self.logger.print_section_header(
                    i18n.t("core.sdk.init.adapter_register_phase")
                )
                if not await self._adapter_loader.register_to_manager(
                    enabled_adapters, adapter_objs, adapter_manager
                ):
                    self.logger.warning(
                        i18n.t("core.sdk.init.adapter_register_partial")
                    )

                # 3. 启动适配器
                if enabled_adapters:
                    self.logger.print_section_header(
                        i18n.t("core.sdk.init.adapter_start_phase")
                    )
                    await adapter_manager.startup()

                # 4. 注册模块
                self.logger.print_section_header(
                    i18n.t("core.sdk.init.module_register_phase")
                )
                if not await self._module_loader.register_to_manager(
                    enabled_modules, module_objs, module_manager
                ):
                    self.logger.warning(i18n.t("core.sdk.init.module_register_partial"))

                # 严格模式检查点 2：注册阶段违规统一报告与中止（在模块初始化前）
                self._strict_manager.raise_if_fatal()

                # 4. 初始化模块（创建实例并挂载到 SDK）
                self.logger.print_section_header(
                    i18n.t("core.sdk.init.module_init_phase")
                )
                if enabled_modules:
                    success = await self._module_loader.initialize_modules(
                        enabled_modules, module_objs, module_manager, self._sdk
                    )
                    if not success:
                        self.logger.warning(i18n.t("core.sdk.init.module_init_partial"))
                else:
                    success = True

                # 6. 启动路由服务器
                self.logger.print_section_header(i18n.t("core.sdk.init.router_start"))
                from ErisPulse.runtime import get_server_config

                _server_config = get_server_config()
                if not _server_config.get("auto_start", True):
                    # 跳过 HTTP 服务器启动（适用于纯 WebSocket/轮询适配器）
                    self.logger.info(i18n.t("core.sdk.init.router_start_skipped"))
                else:
                    try:
                        await self.router.start(
                            host=_server_config["host"],
                            port=_server_config["port"],
                            ssl_certfile=_server_config.get("ssl_certfile"),
                            ssl_keyfile=_server_config.get("ssl_keyfile"),
                        )
                    except Exception as e:
                        self.logger.warning(
                            i18n.t("core.sdk.init.router_start_failed", error=e)
                        )

                # 获取加载耗时
                load_duration = self.lifecycle.stop_timer(LIFECYCLE_TIMER_CORE_INIT)

                # 总结
                self.logger.print_section_header(i18n.t("core.sdk.init.complete"))

                # 显示耗时
                duration_str = (
                    f"{load_duration:.2f}s"
                    if load_duration >= 1
                    else f"{load_duration * 1000:.0f}ms"
                )
                self.logger.print_info(
                    i18n.t("core.sdk.init.duration", duration=duration_str), level=1
                )

                # 初始化完成后的内存快照（TRACE）
                try:
                    from .runtime.memory import log_snapshot

                    log_snapshot("after_init")
                except Exception:
                    pass

                if enabled_adapters:
                    self.logger.print_info(
                        i18n.t(
                            "core.sdk.init.adapter_count", count=len(enabled_adapters)
                        ),
                        level=1,
                    )
                    for i, adapter_name in enumerate(enabled_adapters):
                        is_last = i == len(enabled_adapters) - 1
                        self.logger.print_tree_item(
                            adapter_name, level=1, is_last=is_last
                        )
                    if disabled_adapters:
                        self.logger.print_info(
                            i18n.t(
                                "core.sdk.init.disabled_adapters",
                                names=", ".join(disabled_adapters),
                            ),
                            level=1,
                        )
                else:
                    self.logger.print_info(
                        i18n.t("core.sdk.init.adapter_none"), level=1
                    )

                if enabled_modules:
                    self.logger.print_info(
                        i18n.t(
                            "core.sdk.init.module_count", count=len(enabled_modules)
                        ),
                        level=1,
                    )
                    for i, module_name in enumerate(enabled_modules):
                        is_last = i == len(enabled_modules) - 1
                        # 标注懒加载/立即加载
                        lazy_tag = ""
                        module_obj = module_objs.get(module_name)
                        if module_obj is not None and getattr(
                            module_obj, "moduleInfo", None
                        ):
                            is_lazy = module_obj.moduleInfo.get("meta", {}).get(
                                "lazy_load", True
                            )
                            lazy_tag = (
                                i18n.t("core.sdk.init.tag_lazy")
                                if is_lazy
                                else i18n.t("core.sdk.init.tag_eager")
                            )
                        self.logger.print_tree_item(
                            module_name, level=1, is_last=is_last, tag=lazy_tag
                        )
                    if disabled_modules:
                        self.logger.print_info(
                            i18n.t(
                                "core.sdk.init.disabled_modules",
                                names=", ".join(disabled_modules),
                            ),
                            level=1,
                        )
                else:
                    self.logger.print_info(i18n.t("core.sdk.init.module_none"), level=1)

                # 严格模式已拒绝的组件
                rejected = self._strict_manager.rejections
                if rejected:
                    self.logger.print_info(
                        i18n.t("core.sdk.init.strict_rejected", count=len(rejected)),
                        level=1,
                    )
                    for i, violation in enumerate(rejected):
                        is_last = i == len(rejected) - 1
                        self.logger.print_tree_item(
                            violation.name,
                            level=1,
                            is_last=is_last,
                            tag=i18n.t(
                                "core.sdk.init.strict_rejected_reason",
                                reason=violation.reason,
                            ),
                            tag_style="yellow",
                        )

                self.logger.print_section_footer()

                self.logger.info(i18n.t("core.sdk.init.success", duration=duration_str))

                await self.lifecycle.submit_event(
                    "core.init.complete",
                    msg=i18n.t("core.sdk.init.module_init_complete")
                    if success
                    else i18n.t("core.sdk.init.module_init_partial_failed"),
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

                # 启动主动 GC 后台任务
                self._sdk._start_proactive_gc()

                return True

            except Exception as e:
                load_duration = self.lifecycle.stop_timer(LIFECYCLE_TIMER_CORE_INIT)
                await self.lifecycle.submit_event(
                    "core.init.complete",
                    msg=i18n.t("core.sdk.init.module_init_failed"),
                    data={"duration": load_duration, "success": False, "error": str(e)},
                )
                self.logger.critical(i18n.t("core.sdk.init.critical_error", error=e))
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

        def __getattr__(self, name: str):
            """将未找到的属性委托给 SDK 实例（如 logger、adapter 等）"""
            return getattr(self._sdk, name)

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
            self.lifecycle.start_timer(LIFECYCLE_TIMER_CORE_UNINIT)

            uninit_timeout = DEFAULT_UNINIT_TIMEOUT_SECS
            try:
                from .runtime import get_framework_config

                framework_config = get_framework_config()
                uninit_timeout = framework_config.get("uninit_timeout", uninit_timeout)
            except Exception:
                pass

            async def _do_uninit():
                adapter_manager = self.adapter
                module_manager = self.module
                router_manager = self.router

                # 1. 关闭所有适配器
                registered_adapters = adapter_manager.list_registered()
                if registered_adapters:
                    await adapter_manager.shutdown()

                # 2. 卸载所有已加载模块
                loaded_modules = module_manager.list_loaded()
                if loaded_modules:
                    await module_manager.unload()

                # 3. 停止路由服务器
                if router_manager._server_task is not None:
                    await router_manager.stop()

                # 3.5. 关闭 HTTP 客户端连接池
                try:
                    client = self.client
                    if hasattr(client, "close"):
                        await client.close()
                except Exception as e:
                    self.logger.warning(i18n.t("core.sdk.uninit.client_close_failed", error=e))

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
                                    self.logger.warning(
                                        i18n.t(
                                            "core.sdk.uninit.unload_failed",
                                            name=lm_name,
                                            error=e,
                                        )
                                    )
                        # 清除 LazyModule 内部引用，打破循环引用链
                        object.__setattr__(attr_value, "_sdk_ref", None)
                        object.__setattr__(attr_value, "_instance", None)
                        object.__setattr__(attr_value, "_manager_instance", None)
                        object.__setattr__(attr_value, "_module_class", None)
                        object.__setattr__(attr_value, "_module_info", None)
                        module_properties_to_clear.add(attr_name)

                # 5. 清理所有事件处理器
                self.Event._clear_all_handlers()

                # 6. 清理管理器
                adapter_manager.clear()
                module_manager.clear()

                # 获取清理耗时
                uninit_duration = self.lifecycle.stop_timer(LIFECYCLE_TIMER_CORE_UNINIT)

                # 7. 清理单例残留状态
                self.lifecycle._timers.clear()
                self.logger._logs.clear()
                self.logger._module_levels.clear()
                self.config.force_save()

                # 8. 清理 SDK 对象上的模块属性
                module_properties_cleared = 0
                for module_name in module_properties_to_clear:
                    try:
                        if module_name in instance_dict:
                            del instance_dict[module_name]
                            module_properties_cleared += 1
                    except Exception as e:
                        self.logger.warning(
                            i18n.t(
                                "core.sdk.uninit.attr_clean_failed",
                                name=module_name,
                                error=e,
                            )
                        )

                # 9. 重置初始化状态
                self._sdk._initialized = False
                self._sdk._initializer = None
                # 停止主动 GC 后台任务
                self._sdk._stop_proactive_gc()
                duration_str = (
                    f"{uninit_duration:.2f}s"
                    if uninit_duration >= 1
                    else f"{uninit_duration * 1000:.0f}ms"
                )

                # 提交生命周期事件
                await self.lifecycle.submit_event(
                    "core.uninit.complete",
                    msg=i18n.t("core.sdk.uninit.complete"),
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
                await asyncio.sleep(UNINIT_SETTLE_DELAY_SECS)

                # 9. 清理生命周期事件处理器（在所有事件完成之后）
                self.lifecycle._hooks.clear()

                self.logger.info(
                    i18n.t("core.sdk.uninit.success", duration=duration_str)
                )
                return True

            try:
                if uninit_timeout > 0:
                    return await asyncio.wait_for(
                        _do_uninit(), timeout=uninit_timeout
                    )
                return await _do_uninit()
            except asyncio.TimeoutError:
                uninit_duration = self.lifecycle.stop_timer(LIFECYCLE_TIMER_CORE_UNINIT)
                self.logger.warning(
                    i18n.t("core.sdk.uninit.timeout", timeout=uninit_timeout)
                )
                await self.lifecycle.submit_event(
                    "core.uninit.complete",
                    msg=i18n.t("core.sdk.uninit.timeout_msg"),
                    data={
                        "duration": uninit_duration,
                        "success": False,
                        "error": f"Uninit timeout after {uninit_timeout}s",
                    },
                )
                self.lifecycle._hooks.clear()
                return False
            except Exception as e:
                uninit_duration = self.lifecycle.stop_timer(LIFECYCLE_TIMER_CORE_UNINIT)
                await self.lifecycle.submit_event(
                    "core.uninit.complete",
                    msg=i18n.t("core.sdk.uninit.failed_msg"),
                    data={
                        "duration": uninit_duration,
                        "success": False,
                        "error": str(e),
                    },
                )

                # 等待一小段时间，确保事件处理完成
                await asyncio.sleep(UNINIT_SETTLE_DELAY_SECS)

                # 清理生命周期事件处理器（即使在失败时也要清理）
                self.lifecycle._hooks.clear()

                if "attached to a different loop" in str(e):
                    # 这是一个常见的错误，通常是由于SDK在另一个事件循环中运行而导致的。
                    # 在这种情况下，我们直接返回True即可
                    return True
                self.logger.error(i18n.t("core.sdk.uninit.critical_error", error=e))
                return False

    # ==================== SDK 逻辑方法 ====================

    def _start_proactive_gc(self) -> None:
        """
        {!--< internal-use >!--}
        启动主动 GC 后台任务

        定期执行 Python GC 和内部资源回收（离线 Bot 清理等），
        防止长期运行时的内存增长。间隔由框架配置 proactive_gc_interval 控制。
        """
        # 停止已有的 GC 任务
        self._stop_proactive_gc()

        gc_interval = DEFAULT_PROACTIVE_GC_INTERVAL_SECS
        try:
            from .runtime import get_framework_config

            framework_config = get_framework_config()
            gc_interval = framework_config.get("proactive_gc_interval", gc_interval)
        except Exception:
            pass

        if gc_interval <= 0:
            return  # 配置禁用

        async def _gc_loop():
            import gc

            while True:
                try:
                    await asyncio.sleep(gc_interval)
                    # 1. Python GC
                    collected = gc.collect()
                    # 2. 内部资源回收
                    try:
                        adapter_mgr = self.adapter
                        evicted = adapter_mgr._evict_offline_bots()
                        if collected > 0 or evicted > 0:
                            self.logger.trace(
                                i18n.t("core.sdk.gc.collected", collected=collected, evicted=evicted)
                            )
                    except Exception:
                        pass
                    # 3. 内存快照（TRACE），便于长期观察内存变化趋势
                    try:
                        from .runtime.memory import log_snapshot

                        log_snapshot("gc")
                    except Exception:
                        pass
                except asyncio.CancelledError:
                    break
                except Exception:
                    # GC 异常不应中断循环
                    continue

        try:
            self._gc_task = asyncio.create_task(_gc_loop())
        except RuntimeError:
            pass

    def _stop_proactive_gc(self) -> None:
        """
        {!--< internal-use >!--}
        停止主动 GC 后台任务
        """
        if self._gc_task is not None and not self._gc_task.done():
            self._gc_task.cancel()
        self._gc_task = None

    def dump_state(self) -> dict:
        """
        导出框架当前运行状态的快照

        :return: dict 包含所有子系统状态的字典
        """
        import sys
        import time

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
            state["router"]["running"] = getattr(router_mgr, "_server_started", False)
            state["router"]["http_routes"] = len(getattr(router_mgr, "_http_routes", []))
            state["router"]["ws_routes"] = len(getattr(router_mgr, "_ws_routes", []))
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
            # 已初始化时仅警告并直接返回成功，避免重复初始化破坏内部状态
            try:
                self.logger.warning(i18n.t("core.sdk.init.already_initialized"))
            except Exception:
                pass
            return True

        # before_init 回调：在环境准备之前执行
        if before_init is not None:
            try:
                result = before_init()
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                self.logger.error(f"before_init 回调执行失败: {e}")

        if not await self._prepare_environment():
            return False

        # 创建初始化协调器
        self._initializer = self.Initializer(self)

        # 执行初始化
        self._initialized = await self._initializer.init()

        # after_init 回调：初始化成功后执行
        if self._initialized and after_init is not None:
            try:
                result = after_init()
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                self.logger.error(f"after_init 回调执行失败: {e}")

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
    ) -> asyncio.Task:
        """
        SDK 初始化入口，返回 Task 对象

        :param before_init: 初始化前回调（同步或异步）
        :param after_init: 初始化成功后回调（同步或异步）
        :return: asyncio.Task 初始化任务
        """

        async def _async_init():
            if before_init is not None:
                try:
                    result = before_init()
                    if inspect.isawaitable(result):
                        await result
                except Exception as e:
                    self.logger.error(f"before_init 回调执行失败: {e}")

            if not await self._prepare_environment():
                return False

            self._initializer = self.Initializer(self)
            self._initialized = await self._initializer.init()

            if self._initialized and after_init is not None:
                try:
                    result = after_init()
                    if inspect.isawaitable(result):
                        await result
                except Exception as e:
                    self.logger.error(f"after_init 回调执行失败: {e}")

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
            isInit = await self.init(
                before_init=before_init, after_init=after_init
            )

            if not isInit:
                self.logger.error(i18n.t("core.sdk.run.init_failed"))
                return

            # on_ready 回调：初始化完成后、挂起前执行
            if on_ready is not None:
                try:
                    result = on_ready()
                    if inspect.isawaitable(result):
                        await result
                except Exception as e:
                    self.logger.error(f"on_ready 回调执行失败: {e}")

            if keep_running:
                shutdown_event = asyncio.Event()
                await shutdown_event.wait()
        except asyncio.CancelledError:
            self.logger.info(i18n.t("core.sdk.run.shutdown_signal"))
        except KeyboardInterrupt:
            # Ctrl+C / SIGINT: 允许正常传播，触发优雅关闭
            self.logger.info(i18n.t("core.sdk.run.shutdown_signal"))
            raise
        except Exception as e:
            # 常规异常（模块/适配器错误等），记录但不向上传播
            self.logger.error(e)
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
            self.logger.debug(
                i18n.t(
                    "core.sdk.reload.collected_top_modules", modules=top_level_modules
                )
            )

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
                self.logger.error(i18n.t("core.sdk.reload.init_failed"))
                return False

            # SDK 核心属性通过 __getattr__ 动态解析，无需手动刷新引用。
            # init() 触发的新 import 会创建新单例，
            # 后续 self.logger / self.adapter 等访问自动获取最新单例。

            self.logger.info(i18n.t("core.sdk.reload.complete"))
            self.logger.info(i18n.t("core.sdk.reload.done"))
            return True
        except Exception as e:
            self.logger.error(i18n.t("core.sdk.reload.failed", error=e))
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
                    self.logger.warning(
                        i18n.t("core.sdk.reload.module_top_infer", name=module_name)
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
                    self.logger.warning(
                        i18n.t("core.sdk.reload.adapter_top_infer", name=adapter_name)
                    )

        self.logger.debug(
            i18n.t("core.sdk.reload.collected_top", modules=top_level_set)
        )
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
            self.logger.debug(
                i18n.t(
                    "core.sdk.reload.cleaned_modules",
                    count=len(modules_to_remove),
                    modules=modules_to_remove,
                )
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
            self.logger.debug(
                i18n.t(
                    "core.sdk.reload.cleaned_framework", count=len(framework_modules)
                )
            )

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
            self.logger.debug(
                i18n.t("core.sdk.reload.cleaned_metadata", count=len(metadata_modules))
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
        self.logger.info(i18n.t("core.sdk.reload.starting"))

        # 使用 spawn_background 将任务注册到事件循环调度器 - 不受上层协程取消影响
        from .runtime.tasks import spawn_background

        spawn_background(self._do_restart())

        return True

    RESTART_EXIT_CODE = 42

    async def hard_restart(self) -> bool:
        """
        硬重启：反初始化后退出进程，由父进程（run.py）重新启动新实例

        与 restart()（热重启）的区别：
        - restart(): 在同一进程内反初始化再重新初始化
        - hard_restart(): 反初始化后退出进程，由父进程重新启动全新进程

        确保资源完全释放

        需要通过 epsdk run 启动才生效，否则进程退出后不会自动重启。

        :return: bool 硬重启任务是否成功调度

        :example:
        >>> await sdk.hard_restart()
        """

        async def _do_hard_restart():
            await asyncio.sleep(0.5)
            try:
                self.logger.info(i18n.t("core.sdk.hardrestart.starting"))
                await self.uninit()
                self.logger.info(i18n.t("core.sdk.hardrestart.uninit_done"))
            except Exception as e:
                self.logger.error(i18n.t("core.sdk.hardrestart.uninit_error", error=e))
            os._exit(self.RESTART_EXIT_CODE)

        from .runtime.tasks import spawn_background

        spawn_background(_do_hard_restart())
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
sdk: SDK = SDK()

__all__ = ["SDK", "sdk"]
