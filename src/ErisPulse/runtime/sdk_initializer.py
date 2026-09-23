"""
ErisPulse SDK 初始化 / 反初始化协调器

Initializer（核心初始化编排）与 Uninitializer（优雅反初始化编排）的实现模块。
由 ``ErisPulse.SDK`` 以类属性别名暴露（``SDK.Initializer`` / ``SDK.Uninitializer``），
既有构造方式（``Initializer(sdk_instance)``）与签名不变。
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from ..Core.constants import (
    DEFAULT_UNINIT_TIMEOUT_SECS,
    EVENT_CORE_INIT_STAGE,
    LIFECYCLE_TIMER_CORE_INIT,
    LIFECYCLE_TIMER_CORE_UNINIT,
    UNINIT_SETTLE_DELAY_SECS,
)
from ..Core.i18n import i18n

# 导入加载器类
from ..loaders.adapter import AdapterLoader

# 导入懒加载模块类
from ..loaders.module import LazyModule, ModuleLoader
from ..loaders.strict import StrictModeManager

if TYPE_CHECKING:
    from ..sdk import SDK


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
        # 将加载器引用注入 SDK：热重载（sdk.reload_module / 热重载监控）
        # 经由 SDK 访问，若仅持有在 Initializer 内部则 SDK 侧永远读不到
        sdk_instance._module_loader = self._module_loader
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

        # 各阶段启动时长统计：core.init.stage 事件 + core.init.complete 汇总
        stage_marks: dict[str, float] = {}
        stage_durations: dict[str, float] = {}
        stage_order: list[str] = []
        current_stage = [""]

        async def _emit_stage(stage: str, msg_key: str) -> None:
            """记录阶段开始：发出 core.init.stage 事件（后台）并结算上一阶段耗时"""
            now = time.monotonic()
            prev = current_stage[0]
            if prev:
                stage_durations[prev] = now - stage_marks[prev]
            stage_marks[stage] = now
            stage_order.append(stage)
            current_stage[0] = stage
            await self.lifecycle.submit_event(
                EVENT_CORE_INIT_STAGE,
                msg=i18n.t(msg_key),
                data={"stage": stage},
                background=True,
            )

        def _settle_last_stage() -> None:
            """结算最后一个阶段的耗时（init.complete 汇总前调用）"""
            last = current_stage[0]
            if last and last not in stage_durations:
                stage_durations[last] = time.monotonic() - stage_marks[last]

        try:
            # 1. 并行加载适配器和模块
            adapter_manager = self.adapter
            module_manager = self.module

            # 模块发现阶段
            await _emit_stage("discovery", "core.sdk.init.discovery_phase")
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
            await _emit_stage("adapter_register", "core.sdk.init.adapter_register_phase")
            self.logger.print_section_header(
                i18n.t("core.sdk.init.adapter_register_phase")
            )
            if not await self._adapter_loader.register_to_manager(
                enabled_adapters, adapter_objs, adapter_manager
            ):
                self.logger.warning(
                    i18n.t("core.sdk.init.adapter_register_partial")
                )

            # 3. 启动适配器（声明模块硬依赖的适配器推迟到模块初始化完成后启动）
            deferred_platforms: list[str] = []
            dep_free_platforms: list[str] = []
            for _platform in enabled_adapters:
                _instance = adapter_manager._adapters.get(_platform)
                _depends = getattr(_instance, "depends", None) or {}
                if isinstance(_depends, dict) and _depends.get("modules"):
                    deferred_platforms.append(_platform)
                else:
                    dep_free_platforms.append(_platform)

            if dep_free_platforms:
                await _emit_stage("adapter_start", "core.sdk.init.adapter_start_phase")
                self.logger.print_section_header(
                    i18n.t("core.sdk.init.adapter_start_phase")
                )
                await adapter_manager.startup(dep_free_platforms)

            # 4. 注册模块
            await _emit_stage("module_register", "core.sdk.init.module_register_phase")
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
            await _emit_stage("module_init", "core.sdk.init.module_init_phase")
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

            # 5. 启动声明了模块硬依赖的适配器（此时依赖模块已初始化完成）
            if deferred_platforms:
                await _emit_stage(
                    "adapter_start_deferred",
                    "core.sdk.init.adapter_start_deferred_phase",
                )
                self.logger.print_section_header(
                    i18n.t("core.sdk.init.adapter_start_deferred_phase")
                )
                await adapter_manager.startup(deferred_platforms)

            # 6. 启动路由服务器
            await _emit_stage("router_start", "core.sdk.init.router_start")
            self.logger.print_section_header(i18n.t("core.sdk.init.router_start"))
            from ErisPulse.runtime import get_server_config

            _server_config = get_server_config()
            if not _server_config.get("auto_start", True):
                # 跳过 HTTP 服务器启动（适用于纯 WebSocket/轮询适配器）
                self.logger.info(i18n.t("core.sdk.init.router_start_skipped"))
            else:
                # 路由服务器启动失败（如端口被占用）不视为致命错误：
                # 服务器不启动，但适配器与模块继续运行。
                await self.router.start(
                    host=_server_config["host"],
                    port=_server_config["port"],
                    ssl_certfile=_server_config.get("ssl_certfile"),
                    ssl_keyfile=_server_config.get("ssl_keyfile"),
                    ssl_cert=_server_config.get("ssl_cert"),
                    ssl_key=_server_config.get("ssl_key"),
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
                from .memory import log_snapshot

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
                self.logger.print_info(
                    i18n.t("core.sdk.init.strict_action_hint"), level=1
                )

            # 严格模式被容忍的组件（宽松模式下仍在运行，单独列出便于排查）
            tolerated = self._strict_manager.tolerated
            if tolerated:
                self.logger.print_info(
                    i18n.t(
                        "core.sdk.init.strict_tolerated", count=len(tolerated)
                    ),
                    level=1,
                )
                for i, violation in enumerate(tolerated):
                    is_last = i == len(tolerated) - 1
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

            # 结算最后阶段耗时并输出各阶段启动时长（DEBUG，供启动优化分析）
            _settle_last_stage()
            for _stage in stage_order:
                _secs = stage_durations.get(_stage, 0.0)
                self.logger.debug(
                    f"[Init] stage '{_stage}': {_secs:.3f}s"
                )

            self.logger.info(i18n.t("core.sdk.init.success", duration=duration_str))

            await self.lifecycle.submit_event(
                "core.init.complete",
                msg=i18n.t("core.sdk.init.module_init_complete")
                if success
                else i18n.t("core.sdk.init.module_init_partial_failed"),
                data={
                    "duration": load_duration,
                    "success": success,
                    "stages": dict(stage_durations),
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

            # 冻结框架对象：将当前所有已跟踪对象移入永久代，
            # 后续 gc.collect() 不再扫描框架单例/缓存/模块/适配器实例，
            # 仅回收运行期新建的临时对象，降低 GC 暂停与误回收风险。
            import gc as _gc

            try:
                _gc.freeze()
            except Exception:
                pass

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
            from . import get_framework_config

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
                                from ..Core.di import call_with_depends

                                await call_with_depends(
                                    instance.on_unload,
                                    {"module_name": lm_name},
                                )
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

            # 5.5 兜底取消所有归属后台任务（fire-and-forget 钩子、异步生命周期
            # 处理器调度等），防止悬挂任务持有实例引用阻碍回收
            try:
                from .tasks import cancel_all_background_tasks

                await cancel_all_background_tasks()
            except Exception:
                pass

            # 6. 清理管理器
            adapter_manager.clear()
            module_manager.clear()

            # 6.5 立即回收一次，尽早释放模块/适配器实例与循环引用，
            # 降低 uninit 与 hard_restart 之间的内存驻留
            try:
                import gc

                gc.collect()
            except Exception:
                pass

            # 获取清理耗时
            uninit_duration = self.lifecycle.stop_timer(LIFECYCLE_TIMER_CORE_UNINIT)

            # 7. 清理单例残留状态
            self.lifecycle._timers.clear()
            self.logger._logs.clear()
            self.logger._module_levels.clear()
            self.config.force_save()

            # 7.5 关闭存储后端连接资源（须在 force_save 之后：持久化仍依赖存储；
            # 主循环 + 同步桥接循环两侧的连接池/共享连接都释放，避免退出期 GC 炸已关闭 loop）
            try:
                storage_backend = self.storage
                if hasattr(storage_backend, "aclose"):
                    await storage_backend.aclose()
                if hasattr(storage_backend, "close"):
                    storage_backend.close()
            except Exception as e:
                self.logger.warning(i18n.t("core.storage.aclose_failed", error=e))

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
            self._sdk._module_loader = None  # 加载器随 Initializer 生命周期一并失效
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
