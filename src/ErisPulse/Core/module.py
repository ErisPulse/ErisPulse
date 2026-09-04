"""
ErisPulse 模块系统

提供标准化的模块注册、加载和管理功能，与适配器系统保持一致的设计模式
"""

import inspect
import warnings
from typing import Any, TypeVar

from ..runtime.context import current_owner
from .Bases import BaseModule
from .Bases.manager import ManagerBase
from .config import config
from .constants import (
    CONFIG_KEY_MODULE_STATUS_OF,
    CONFIG_KEY_MODULES_STATUS,
    DEFAULT_MODULE_ENABLED,
    MODULE_SOURCE_PLUGIN_FOLDER,
)
from .i18n import i18n
from .lifecycle import lifecycle
from .logger import logger

# 已记录过的弃用警告（owner, old_kwarg），每个组合只警告一次，避免热路径日志刷屏
_DEPRECATED_KWARG_WARNED: set[tuple[str, str]] = set()

# 模块类型 TypeVar，用于 get() 的泛型返回，让用户可通过类型注解获得 IDE 补全
# 用法： my_module: MyModule = sdk.module.get("MyModule")
_TModule = TypeVar("_TModule", bound=BaseModule)


def _warn_deprecated_kwarg(owner: str, old: str, new: str) -> None:
    """
    {!--< internal-use >!--}
    当检测到使用已弃用的旧关键字参数时，记录一次弃用日志并说明迁移方式

    :param owner: 所属方法名（如 "ModuleManager.get"）
    :param old: 已弃用的旧参数名
    :param new: 推荐使用的新参数名
    """
    key = (owner, old)
    if key in _DEPRECATED_KWARG_WARNED:
        return
    _DEPRECATED_KWARG_WARNED.add(key)
    logger.warning(
        i18n.t(
            "core.deprecated.kwarg",
            owner=owner,
            old=old,
            new=new,
        )
    )


class ModuleManager(ManagerBase):
    """
    模块管理器

    提供标准化的模块注册、加载和管理功能，模仿适配器管理器的模式

    {!--< tips >!--}
    1. 使用register方法注册模块类
    2. 使用load/unload方法加载/卸载模块
    3. 通过get方法获取模块实例
    {!--< /tips >!--}
    """

    @staticmethod
    def _is_subclass(klass: type, base_cls: type) -> bool:
        try:
            if issubclass(klass, base_cls):
                return True
        except TypeError:
            pass
        if base_cls.__name__ == klass.__name__:
            return False
        for parent in klass.__mro__:
            if parent.__name__ == base_cls.__name__ and parent.__module__ == base_cls.__module__:
                return True
        return False

    @staticmethod
    def _unload_timeout() -> float:
        """
        {!--< internal-use >!--}
        读取模块 on_unload 优雅收尾的超时（秒）

        复用 ``ErisPulse.framework.uninit_timeout`` 配置（反初始化流程的统一超时预算，
        整体仍有 uninit 的 wait_for 兜底）；未配置或非法时回退常量默认值。

        :return: 超时秒数（>0）
        """
        from ..runtime import get_framework_config
        from .constants import DEFAULT_UNINIT_TIMEOUT_SECS

        try:
            value = get_framework_config().get("uninit_timeout")
            if isinstance(value, (int, float)) and value > 0:
                return float(value)
        except Exception:
            pass
        return float(DEFAULT_UNINIT_TIMEOUT_SECS)

    def __init__(self):
        # 模块存储
        self._modules: dict[str, Any] = {}  # 已加载的模块实例
        self._module_classes: dict[str, type] = {}  # 模块类映射
        self._loaded_modules: set = set()  # 已加载的模块名称
        self._module_info: dict[str, dict] = {}  # 模块信息
        self._lazy_modules: dict[str, Any] = {}  # 懒加载代理（未触发初始化时 get() 返回它）
        self._sdk = None
        # 注册配置变更路由：将 config.set / config.updated 事件转发到各模块的 on_config_update
        self._register_config_change_routing()

    def set_sdk_ref(self, sdk) -> bool:
        """
        设置 SDK 引用

        :param sdk: SDK 实例
        :return: bool 是否设置成功
        """
        try:
            self._sdk = sdk
            return True
        except Exception as e:
            from .logger import logger

            logger.error(i18n.t("core.module.set_sdk_failed", error=e))
            return False

    # ==================== 配置变更路由 ====================

    def _register_config_change_routing(self) -> None:
        """
        {!--< internal-use >!--}
        注册 config.set / config.updated 事件订阅，将配置变更路由到各模块的 on_config_update

        - ``config.set``：代码或 Dashboard 调用 setConfig 时即时触发（单 key 变更）
        - ``config.updated``：用户手动编辑配置文件后由文件监听任务触发（整树变更）
        """
        lifecycle.register("config.set", self._on_config_set)
        lifecycle.register("config.updated", self._on_config_updated)

    def _on_config_set(self, data: dict) -> None:
        """
        {!--< internal-use >!--}
        处理 config.set 事件：找出受影响的模块并触发 on_config_update
        """
        key = data.get("key", "")
        if not key:
            return
        for module_name in list(self._loaded_modules):
            instance = self._modules.get(module_name)
            if not instance or not hasattr(instance, "on_config_update"):
                continue
            config_key = self._resolve_config_key(instance)
            # key 形如 "MyModule" 或 "MyModule.field"
            if key == config_key or key.startswith(config_key + "."):
                new_dict = config.getConfig(config_key) or {}
                self._notify_config_update(instance, module_name, None, new_dict)

    def _on_config_updated(self, data: dict) -> None:
        """
        {!--< internal-use >!--}
        处理 config.updated 事件：对比新旧配置树，找出配置变化的模块并触发 on_config_update
        """
        old_config = data.get("old_config", {}) or {}
        new_config = data.get("new_config", {}) or {}
        for module_name in list(self._loaded_modules):
            instance = self._modules.get(module_name)
            if not instance or not hasattr(instance, "on_config_update"):
                continue
            config_key = self._resolve_config_key(instance)
            old_dict = old_config.get(config_key)
            new_dict = new_config.get(config_key)
            if old_dict != new_dict:
                self._notify_config_update(instance, module_name, old_dict, new_dict)

    def _cleanup_lazy(self, module_name: str) -> None:
        """
        {!--< internal-use >!--}
        清理模块的懒加载代理与 SDK 属性（模块未实例化时也有效）

        :param module_name: 模块名称
        """
        self.unregister_lazy(module_name)
        if self._sdk is not None:
            sdk_dict = getattr(self._sdk, "__dict__", {})
            if module_name in sdk_dict:
                try:
                    del sdk_dict[module_name]
                except Exception:
                    pass

    @staticmethod
    def _resolve_config_key(instance: Any) -> str:
        """
        {!--< internal-use >!--}
        解析模块的配置键名（优先用注入的注册名，回退类名）
        """
        return getattr(instance, "_module_name", None) or instance.__class__.__name__

    def _notify_config_update(
        self,
        instance: Any,
        module_name: str,
        old_dict: dict | None,
        new_dict: dict | None,
    ) -> None:
        """
        {!--< internal-use >!--}
        调用模块的 on_config_update 回调，传入类型安全的配置对象

        :param instance: 模块实例
        :param module_name: 模块名（用于日志）
        :param old_dict: 变更前的配置字典（可能为 None）
        :param new_dict: 变更后的配置字典（可能为 None）
        """
        from ..Core.Bases.config_schema import _notify_instance_config_update

        _notify_instance_config_update(
            instance,
            old_dict,
            new_dict,
            i18n_key="core.module.config_update_failed",
            log_params={"name": module_name},
        )

    # ==================== 模块注册与管理 ====================

    def register(
        self,
        name: str | None = None,
        class_type: type | None = None,
        info: dict | None = None,
        *,
        module_name: str | None = None,
        module_class: type | None = None,
        module_info: dict | None = None,
    ) -> bool:
        """
        注册模块类

        :param name: 模块名称
        :param class_type: 模块类
        :param info: 模块信息
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :param module_class: [已弃用] 兼容旧关键字参数，等同 class_type
        :param module_info: [已弃用] 兼容旧关键字参数，等同 info
        :return: 是否注册成功

        :raises TypeError: 当模块类无效时抛出

        :example:
        >>> module.register("MyModule", MyModuleClass)
        """
        # 兼容旧关键字参数（已弃用，建议改用位置参数或新参数名）
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.register", "module_name", "name")
            name = module_name
        if module_class is not None:
            _warn_deprecated_kwarg("ModuleManager.register", "module_class", "class_type")
            class_type = module_class
        if module_info is not None:
            _warn_deprecated_kwarg("ModuleManager.register", "module_info", "info")
            info = module_info
        # 缺少必要参数时按原契约报错
        if not isinstance(name, str) or not name:
            error_msg = i18n.t("core.module.name_required")
            logger.error(error_msg)
            raise TypeError(error_msg)
        if class_type is None:
            raise TypeError(
                i18n.t(
                    "core.module.param_must_be_class",
                    name=name,
                    type="NoneType",
                )
            )
        # 方法体沿用语义化变量名
        module_name = name
        module_class = class_type
        module_info = info
        # 严格验证模块类，确保继承自BaseModule
        # 先检查是否为类对象
        if not isinstance(module_class, type):
            error_msg = i18n.t(
                "core.module.param_must_be_class",
                name=module_name,
                type=type(module_class).__name__,
            )
            logger.error(error_msg)
            raise TypeError(error_msg)

        if not self._is_subclass(module_class, BaseModule):
            warn_msg = i18n.t(
                "core.module.not_inherit_base",
                name=module_name,
                classname=module_class.__name__,
            )
            logger.warning(warn_msg)
            # error_msg = f"模块 {module_name} 的类 {module_class.__name__} 必须继承自BaseModule"
            # logger.error(error_msg)
            # raise TypeError(error_msg)

        # 验证模块名是否合法
        if not module_name or not isinstance(module_name, str):
            error_msg = i18n.t("core.module.name_required")
            logger.error(error_msg)
            raise TypeError(error_msg)

        # 检查模块名是否已存在
        if module_name in self._module_classes:
            warn_msg = i18n.t("core.module.exists_overwrite", name=module_name)
            logger.warning(warn_msg)

        self._module_classes[module_name] = module_class
        if module_info:
            self._module_info[module_name] = module_info

        # 触发模块注册事件
        lifecycle.emit_sync(
            "module.register",
            {
                "module_name": module_name,
                "success": True,
            },
        )

        logger.info(i18n.t("core.module.registered", name=module_name))
        return True

    def register_lazy(self, name: str, lazy_proxy: Any) -> None:
        """
        注册懒加载代理

        :param name: 模块名称
        :param lazy_proxy: 懒加载代理对象（LazyModule）

        {!--< internal-use >!--}
        由加载器在创建 LazyModule 后调用。注册后 get() 会返回该代理，
        从而使“懒加载对用户透明”：已注册但未加载的模块不再返回 None。
        {!--< /internal-use >!--}
        """
        self._lazy_modules[name] = lazy_proxy

    def unregister_lazy(self, name: str) -> None:
        """
        取消注册懒加载代理

        :param name: 模块名称

        {!--< internal-use >!--}
        卸载/取消注册模块时调用，保持 _lazy_modules 与实际挂载状态一致。
        {!--< /internal-use >!--}
        """
        self._lazy_modules.pop(name, None)

    async def load(self, name: str | None = None, *, module_name: str | None = None) -> bool:
        """
        加载指定模块（标准化加载逻辑）

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 是否加载成功

        :example:
        >>> await module.load("MyModule")
        """
        # 兼容旧关键字参数（已弃用）
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.load", "module_name", "name")
            name = module_name
        if name is None:
            return False
        module_name = name
        # 检查模块是否已注册
        if module_name not in self._module_classes:
            logger.error(i18n.t("core.module.not_registered", name=module_name))
            return False

        # 检查模块是否已加载
        if module_name in self._loaded_modules:
            logger.info(i18n.t("core.module.already_loaded", name=module_name))
            return True

        logger.trace(i18n.t("core.module.start_loading", name=module_name))

        try:
            module_class = self._module_classes[module_name]

            init_signature = inspect.signature(module_class.__init__)
            params = [
                p
                for p in init_signature.parameters.values()
                if p.name != "self" and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ]

            if (sdk_to_use := self._sdk) is None:
                from .. import sdk

                sdk_to_use = sdk

            token = current_owner.set(module_name)
            try:
                if params:
                    instance = module_class(sdk_to_use)
                else:
                    instance = module_class()

                if module_name in self._module_info:
                    instance.moduleInfo = self._module_info[module_name]

                # 注入模块注册名，用于配置键解析等
                instance._module_name = module_name

                # 预注册模块声明的 i18n 键（在用户代码可能访问配置/翻译之前）
                # 幂等：即使后续 _ensure_config_exists() 再次调用也不会产生副作用
                if hasattr(instance, "_ensure_i18n_registered"):
                    try:
                        instance._ensure_i18n_registered()
                    except Exception:
                        logger.debug(
                            i18n.t("core.module.i18n_register_exception", name=module_name),
                            exc_info=True,
                        )

                if hasattr(instance, "on_load"):
                    try:
                        if inspect.iscoroutinefunction(instance.on_load):
                            await instance.on_load({"module_name": module_name})
                        else:
                            instance.on_load({"module_name": module_name})
                    except Exception as e:
                        logger.error(i18n.t("core.module.on_load_failed", name=module_name, error=e))
                        return False
            finally:
                current_owner.reset(token)

            # 缓存模块实例
            self._modules[module_name] = instance
            self._loaded_modules.add(module_name)

            await lifecycle.submit_event(
                "module.load",
                data={
                    "module_name": module_name,
                    "success": True,
                },
                msg=i18n.t(
                    "core.module.load_success_msg",
                    name=module_name or "All",
                ),
            )

            await lifecycle.submit_event(
                "module.init",
                data={
                    "module_name": module_name,
                    "success": True,
                },
                msg=i18n.t("core.module.init_done_msg", name=module_name),
            )

            logger.info(i18n.t("core.module.load_success", name=module_name))
            return True

        except SystemExit as e:
            await lifecycle.submit_event(
                "module.load",
                data={
                    "module_name": module_name,
                    "success": False,
                },
                msg=i18n.t("core.module.systemexit", name=module_name, code=e.code),
            )
            logger.error(i18n.t("core.module.systemexit", name=module_name, code=e.code))
            return False
        except Exception as e:
            await lifecycle.submit_event(
                "module.load",
                data={
                    "module_name": module_name,
                    "success": False,
                },
                msg=i18n.t(
                    "core.module.load_failed",
                    name=module_name or "All",
                    error=e,
                ),
            )
            logger.error(i18n.t("core.module.load_failed", name=module_name, error=e))
            return False

    def _collect_dependents(self, name: str) -> list[str]:
        """
        {!--< internal-use >!--}
        收集直接或间接依赖指定模块的模块闭包（BFS）

        返回顺序为由近及远（直接依赖者在前、间接依赖者在后）；
        卸载时应按相反顺序执行，保证每个依赖者卸载时其依赖仍可用。

        :param name: 目标模块名
        :return: 依赖者模块名列表（不含 name 本身）
        """
        dependents: list[str] = []
        visited: set[str] = {name}
        queue: list[str] = [name]
        while queue:
            current = queue.pop(0)
            for mod_name, mod_info in self._module_info.items():
                if mod_name in visited:
                    continue
                deps = ((mod_info or {}).get("meta", {}) or {}).get("depends") or []
                if current in deps:
                    visited.add(mod_name)
                    dependents.append(mod_name)
                    queue.append(mod_name)
        return dependents

    async def unload(
        self,
        name: str | None = None,
        *,
        module_name: str | None = None,
        purge: bool = False,
    ) -> bool:
        """
        卸载指定模块或所有模块

        卸载被其它模块依赖的模块时，依赖它的模块会**级联卸载**
        （依赖者先卸载，日志说明级联链），避免依赖者持有失效引用继续运行。

        ``purge`` 控制是否**一并删除注册存根**：

        - ``purge=False``（默认）：只取消加载——卸载实例与资源，但保留
          注册存根（模块类与元信息），模块仍可被 discover 重新发现、`load()`
          重新实例化，无需重新 `register()`
        - ``purge=True``：彻底卸载——同时删除注册存根（释放模块类引用），
          并对插件文件夹来源的模块清理 ``sys.modules``，使插件及其独占依赖
          可被 GC 回收（解决 NoneBot 式卸载后插件与依赖内存不释放的问题）；
          级联卸载的依赖者同样被 purge。卸载后重新加载需重新 `register()`

        :param name: 模块名称，None表示卸载所有模块（默认None）
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :param purge: 是否一并删除注册存根并清理 sys.modules（默认 False）
        :return: 是否卸载成功

        :example:
        >>> await module.unload("MyModule")  # 卸载单个模块（依赖者级联卸载）
        >>> await module.unload("MyModule", purge=True)  # 彻底卸载（释放类引用）
        >>> await module.unload()  # 卸载所有模块
        """
        # 兼容旧关键字参数（已弃用）
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.unload", "module_name", "name")
            name = module_name
        module_name = name
        # purge 模式下收集被卸载模块的弱引用，卸载完成后诊断是否可回收
        purge_refs: list[tuple[str, Any, Any]] = []
        if module_name is None:
            # 卸载所有模块
            success = True
            for loaded_name in list(self._loaded_modules):
                if not await self._unload_single_module(loaded_name):
                    success = False
                if purge:
                    purge_refs.append(self._purge_module_stub(loaded_name))
            # 一并清理未初始化的懒加载代理，避免卸载后仍可通过代理访问
            for lazy_name in list(self._lazy_modules):
                self._cleanup_lazy(lazy_name)
                if purge:
                    purge_refs.append(self._purge_module_stub(lazy_name))
            module_name = "All"
        else:
            # 级联卸载：依赖者先卸载，最后卸载目标模块
            dependents = self._collect_dependents(module_name)
            if dependents:
                logger.warning(
                    i18n.t(
                        "core.module.unload_cascade",
                        name=module_name,
                        deps=", ".join(dependents),
                    )
                )
            success = True
            # BFS 产出由近及远（直接依赖者在前），卸载按相反顺序执行：
            # 最深层的间接依赖者先卸载，保证每个模块卸载时其依赖仍可用
            for dep_name in reversed(dependents):
                if dep_name in self._loaded_modules or dep_name in self._lazy_modules:
                    if not await self._unload_single_module(dep_name):
                        success = False
                    if purge:
                        purge_refs.append(self._purge_module_stub(dep_name))
            if not await self._unload_single_module(module_name):
                success = False
            if purge:
                purge_refs.append(self._purge_module_stub(module_name))

        if purge and purge_refs:
            self._report_purge_recyclability(purge_refs)

        await lifecycle.submit_event(
            "module.unload",
            msg=i18n.t("core.module.unload_complete", name=module_name)
            if success
            else i18n.t("core.module.unload_failed_msg", name=module_name),
            data={
                "module_name": module_name,
                "success": success,
            },
        )
        return success

    async def _unload_single_module(self, module_name: str) -> bool:
        """
        {!--< internal-use >!--}
        卸载单个模块

        :param module_name: 模块名称
        :return: 是否卸载成功
        """
        # 模块未加载，返回 True（表示没有需要卸载的模块，这不是错误）。
        # 但仍需清理懒加载代理与 SDK 属性，确保禁用/卸载对懒加载模块同样生效
        if module_name not in self._loaded_modules:
            if module_name in self._lazy_modules:
                self._cleanup_lazy(module_name)
            else:
                logger.warning(i18n.t("core.module.unload_not_loaded", name=module_name))
            return True

        try:
            import asyncio

            unload_timeout = self._unload_timeout()
            instance = self._modules.get(module_name)
            if instance and hasattr(instance, "on_unload"):
                try:
                    if inspect.iscoroutinefunction(instance.on_unload):
                        # 优雅收尾超时保护：on_unload 卡死不再阻塞卸载/级联/重载/uninit
                        await asyncio.wait_for(
                            instance.on_unload({"module_name": module_name}),
                            timeout=unload_timeout,
                        )
                    else:
                        instance.on_unload({"module_name": module_name})
                except asyncio.TimeoutError:
                    logger.warning(
                        i18n.t(
                            "core.module.on_unload_timeout",
                            name=module_name,
                            timeout=unload_timeout,
                        )
                    )
                except Exception as e:
                    logger.error(i18n.t("core.module.on_unload_failed", name=module_name, error=e))

            # on_unload 之后兜底取消该模块名下的后台任务：
            # 模块未自行取消的任务可能持有实例引用，导致卸载后无法被 GC
            from ..runtime.tasks import cancel_owner_tasks

            cancelled_tasks = await cancel_owner_tasks(module_name)
            if cancelled_tasks > 0:
                logger.warning(
                    i18n.t(
                        "core.module.unload_tasks_cancelled",
                        name=module_name,
                        count=cancelled_tasks,
                    )
                )

            # 清理该模块注册的 i18n 翻译键（防止热重载后翻译键泄漏）
            try:
                i18n.unregister_domain(module_name)
            except Exception:
                pass

            from .router import router

            result = router.unregister_all_by_namespace(module_name)
            if result["http_count"] > 0 or result["websocket_count"] > 0:
                logger.debug(
                    i18n.t(
                        "core.module.unload_routes_cleaned",
                        name=module_name,
                        http=result["http_count"],
                        ws=result["websocket_count"],
                    )
                )

            from .Event import command, message, meta, notice, request

            total_cleaned = 0
            total_cleaned += command.unregister_by_owner(module_name)
            for event_handler in [message, notice, request, meta]:
                total_cleaned += event_handler.handler.unregister_by_owner(module_name)
            if total_cleaned > 0:
                logger.debug(
                    i18n.t(
                        "core.module.unload_handlers_cleaned",
                        name=module_name,
                        count=total_cleaned,
                    )
                )

            # 自动注销模块在加载上下文内注册的主人身源 provider（作用域清理）
            try:
                from .master import master

                provider_removed = master.unregister_by_owner(module_name)
                if provider_removed > 0:
                    logger.debug(
                        i18n.t(
                            "core.module.unload_providers_cleaned",
                            name=module_name,
                            count=provider_removed,
                        )
                    )
            except Exception:
                pass

            # 清理该模块注册的生命周期钩子，避免闭包引用导致内存泄漏
            lifecycle_removed = lifecycle.unregister_by_owner(module_name)
            if lifecycle_removed > 0:
                logger.debug(
                    i18n.t(
                        "core.module.lifecycle_hooks_cleaned",
                        name=module_name,
                        count=lifecycle_removed,
                    )
                )

            if self._sdk is not None:
                sdk_dict = getattr(self._sdk, "__dict__", {})
                if module_name in sdk_dict:
                    try:
                        del sdk_dict[module_name]
                    except Exception:
                        pass

            del self._modules[module_name]
            self._loaded_modules.discard(module_name)
            # 同步移除懒加载代理，保持与 SDK 属性被删除的状态一致
            self.unregister_lazy(module_name)

            logger.info(i18n.t("core.module.unload_success", name=module_name))
            return True

        except Exception as e:
            logger.error(i18n.t("core.module.unload_failed", name=module_name, error=e))
            return False

    def _purge_module_stub(self, module_name: str) -> tuple[str, Any, Any]:
        """
        {!--< internal-use >!--}
        删除模块注册存根，释放模块类引用（并清理插件来源的 sys.modules）

        返回 (module_name, class_weakref, instance_weakref) 供回收诊断。

        :param module_name: 模块名
        :return: 供 `_report_purge_recyclability` 消费的弱引用三元组
        """
        import weakref

        module_class = self._module_classes.get(module_name)
        instance = self._modules.get(module_name)
        info = self._module_info.get(module_name)

        class_ref = weakref.ref(module_class) if module_class is not None else None
        instance_ref = weakref.ref(instance) if instance is not None else None

        # 释放注册存根（类引用 + 元信息 + 懒加载代理）
        self._module_classes.pop(module_name, None)
        self._module_info.pop(module_name, None)
        self.unregister_lazy(module_name)

        # 保守清理 sys.modules：仅插件文件夹来源（本地插件），不碰已安装包/共享库
        meta = (info or {}).get("meta", {}) or {}
        if meta.get("source") == MODULE_SOURCE_PLUGIN_FOLDER:
            self._purge_sys_modules(module_name, meta.get("top_level") or [module_name])

        logger.info(i18n.t("core.module.purged", name=module_name))
        return module_name, class_ref, instance_ref

    @staticmethod
    def _purge_sys_modules(module_name: str, top_level: list[str]) -> None:
        """
        {!--< internal-use >!--}
        从 sys.modules 移除插件自身模块与其子包（保守：不清理第三方/共享库）

        :param module_name: 插件模块名
        :param top_level: 顶层包名列表（用于清理包内子模块）
        """
        import sys

        purge_names = {module_name}
        purge_names.update(top_level or [])
        for mod_name in list(sys.modules):
            if any(mod_name == n or mod_name.startswith(f"{n}.") for n in purge_names):
                sys.modules.pop(mod_name, None)

    def _report_purge_recyclability(self, refs: list[tuple[str, Any, Any]]) -> None:
        """
        {!--< internal-use >!--}
        purge 卸载后诊断模块类/实例是否可回收，泄漏时告警并列出引用方

        :param refs: `_purge_module_stub` 产出的 (name, class_ref, instance_ref) 列表
        """
        import gc

        gc.collect()
        for name, class_ref, instance_ref in refs:
            leaked_class = class_ref is not None and class_ref() is not None
            leaked_instance = instance_ref is not None and instance_ref() is not None
            if not leaked_class and not leaked_instance:
                continue
            logger.warning(
                i18n.t(
                    "core.module.purge_leaked",
                    name=name,
                    kind=(
                        "class+instance"
                        if leaked_class and leaked_instance
                        else "class"
                        if leaked_class
                        else "instance"
                    ),
                )
            )
            # 引用方定位（截断，避免刷屏）：仅 DEBUG 级输出
            for leaked_obj in (x() for x in (class_ref, instance_ref) if x is not None and x() is not None):
                try:
                    referrers = [type(r).__name__ for r in gc.get_referrers(leaked_obj)[:8]]
                    logger.debug(
                        i18n.t(
                            "core.module.purge_leaked_referrers",
                            name=name,
                            referrers=", ".join(referrers) or "?",
                        )
                    )
                except Exception:
                    pass

    def get(self, name: str | None = None, *, module_name: str | None = None) -> "_TModule | Any | None":
        """
        获取模块实例或懒加载代理

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 模块实例 / 懒加载代理 / None

        {!--< tips >!--}
        不会触发加载。返回值优先级：
        1. 已加载的真实实例（_modules）
        2. 懒加载代理（_lazy_modules，访问其属性才会触发初始化）
        3. None（模块未注册或未挂载）
        这使得 ``module.get()`` 与 ``sdk.xxx`` / ``module.MyModule``
        在“懒加载对用户透明”上保持一致：已注册但未加载的模块不再返回 None。

        由于框架通过 entry_points 动态发现模块，入口点无法静态获知
        具体模块类型；返回值为泛型 ``_TModule``（默认基类）。
        若调用方与模块同项目且能导入模块类，可添加类型注解获得更精确补全：

        >>> my_module: MyModule = sdk.module.get("MyModule")
        {!--< /tips >!--}

        :example:
        >>> my_module = module.get("MyModule")
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.get", "module_name", "name")
            name = module_name
        if name is None:
            return None
        instance = self._modules.get(name)
        if instance is not None:
            return instance
        return self._lazy_modules.get(name)

    def exists(self, name: str | None = None, *, module_name: str | None = None) -> bool:
        """
        检查模块是否已注册

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 模块是否已注册（即 module.register() 已被调用）

        {!--< tips >!--}
        exists() 只检查模块类是否已注册到管理器，用于验证模块是否可以加载。
        如需检查模块是否启用，请使用 is_enabled()。
        {!--< /tips >!--}
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.exists", "module_name", "name")
            name = module_name
        if name is None:
            return False
        return name in self._module_classes

    def is_loaded(self, name: str | None = None, *, module_name: str | None = None) -> bool:
        """
        检查模块是否已加载

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 模块是否已加载

        :example:
        >>> if module.is_loaded("MyModule"):
        ...     ...
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.is_loaded", "module_name", "name")
            name = module_name
        if name is None:
            return False
        return name in self._loaded_modules

    def is_running(self, name: str | None = None, *, module_name: str | None = None) -> bool:
        """
        检查模块是否正在运行（已加载）

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 模块是否正在运行

        :example:
        >>> if module.is_running("MyModule"):
        >>>     print("MyModule 正在运行")
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.is_running", "module_name", "name")
            name = module_name
        if name is None:
            return False
        return self.is_loaded(name)

    def list_running(self) -> list[str]:
        """
        列出所有正在运行的模块（已加载）

        :return: 模块名称列表

        :example:
        >>> running = module.list_running()
        >>> print("正在运行的模块:", running)
        """
        return self.list_loaded()

    def list_registered(self) -> list[str]:
        """
        列出所有已注册的模块

        :return: 模块名称列表

        :example:
        >>> registered = module.list_registered()
        """
        return list(self._module_classes.keys())

    def list_loaded(self) -> list[str]:
        """
        列出所有已加载的模块

        :return: 模块名称列表

        :example:
        >>> loaded = module.list_loaded()
        """
        return list(self._loaded_modules)

    # ==================== 模块配置管理 ====================

    def _config_register(self, module_name: str, enabled: bool = DEFAULT_MODULE_ENABLED) -> bool:
        """
        注册新模块信息

        {!--< internal-use >!--}
        此方法仅供内部使用

        :param module_name: 模块名称
        :param enabled: 是否启用模块 (默认: DEFAULT_MODULE_ENABLED)
        :return: 是否操作成功
        """
        existing = config.getConfig(CONFIG_KEY_MODULE_STATUS_OF.format(module_name))
        if existing is not None:
            return True

        # 模块不存在，进行注册
        config.setConfig(CONFIG_KEY_MODULE_STATUS_OF.format(module_name), enabled)
        status = i18n.t("core.adapter.status_enabled") if enabled else i18n.t("core.adapter.status_disabled")
        logger.info(i18n.t("core.module.registered_status", name=module_name, status=status))
        return True

    def is_enabled(self, name: str | None = None, *, module_name: str | None = None) -> bool:
        """
        检查模块是否启用

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 模块是否启用

        {!--< tips >!--}
        模块启用条件：
        1. 模块在配置文件中（ErisPulse.modules.status.{module_name} 存在）
        2. 配置值为启用状态

        如果模块未在配置中，默认启用并自动写入配置
        {!--< /tips >!--}
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.is_enabled", "module_name", "name")
            name = module_name
        if name is None:
            return False
        module_name = name
        from .config import parse_bool_config

        status = config.getConfig(CONFIG_KEY_MODULE_STATUS_OF.format(module_name))

        # 模块未在配置中，默认启用并写入配置
        if status is None:
            config.setConfig(CONFIG_KEY_MODULE_STATUS_OF.format(module_name), True)
            return True

        # 解析配置值
        return parse_bool_config(status)

    def enable(self, name: str | None = None, *, module_name: str | None = None) -> bool:
        """
        启用模块

        :param name: [str] 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: [bool] 操作是否成功
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.enable", "module_name", "name")
            name = module_name
        if name is None:
            return False
        module_name = name
        if module_name not in self._module_classes:
            logger.error(i18n.t("core.module.module_not_exist", name=module_name))
            return False

        config.setConfig(CONFIG_KEY_MODULE_STATUS_OF.format(module_name), True, immediate=True)
        logger.info(i18n.t("core.module.module_enabled", name=module_name))
        return True

    def disable(self, name: str | None = None, *, module_name: str | None = None) -> bool:
        """
        禁用模块

        :param name: [str] 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: [bool] 操作是否成功
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.disable", "module_name", "name")
            name = module_name
        if name is None:
            return False
        module_name = name
        config.setConfig(CONFIG_KEY_MODULE_STATUS_OF.format(module_name), False, immediate=True)
        logger.info(i18n.t("core.module.module_disabled", name=module_name))

        # 级联禁用依赖者（最深层依赖者先处理），与 unload 的级联语义一致
        dependents = self._collect_dependents(module_name)
        if dependents:
            logger.warning(
                i18n.t(
                    "core.module.unload_cascade",
                    name=module_name,
                    deps=", ".join(dependents),
                )
            )
        for dep_name in reversed(dependents):
            if dep_name in self._loaded_modules or dep_name in self._lazy_modules:
                self.disable(dep_name)

        if module_name not in self._loaded_modules:
            # 即使模块尚未实例化（懒加载代理），也要清理代理与 SDK 属性
            self._cleanup_lazy(module_name)
            return True

        instance = self._modules.get(module_name)
        if instance and hasattr(instance, "on_unload"):
            from ..runtime.tasks import cancel_owner_tasks, spawn_background

            async def _report_cancelled() -> None:
                """兜底取消模块后台任务并记录数量"""
                cancelled = await cancel_owner_tasks(module_name)
                if cancelled > 0:
                    logger.warning(
                        i18n.t(
                            "core.module.unload_tasks_cancelled",
                            name=module_name,
                            count=cancelled,
                        )
                    )

            if inspect.iscoroutinefunction(instance.on_unload):

                async def _unload_then_cancel_tasks() -> None:
                    """异步 on_unload：完成后兜底取消（与 unload 时序一致）"""
                    import asyncio

                    unload_timeout = self._unload_timeout()
                    try:
                        await asyncio.wait_for(
                            instance.on_unload({"module_name": module_name}),
                            timeout=unload_timeout,
                        )
                    except asyncio.TimeoutError:
                        logger.warning(
                            i18n.t(
                                "core.module.on_unload_timeout",
                                name=module_name,
                                timeout=unload_timeout,
                            )
                        )
                    except Exception as e:
                        logger.error(
                            i18n.t(
                                "core.module.on_unload_failed",
                                name=module_name,
                                error=e,
                            )
                        )
                    await _report_cancelled()

                spawn_background(_unload_then_cancel_tasks())
            else:
                # 同步 on_unload 内联执行（保持在路由/事件清理之前完成）
                try:
                    instance.on_unload({"module_name": module_name})
                except Exception as e:
                    logger.error(i18n.t("core.module.on_unload_failed", name=module_name, error=e))
                spawn_background(_report_cancelled())

        from .router import router

        router.unregister_all_by_namespace(module_name)

        from .Event import command, message, meta, notice, request

        command.unregister_by_owner(module_name)
        for event_handler in [message, notice, request, meta]:
            event_handler.handler.unregister_by_owner(module_name)

        # 清理该模块注册的生命周期钩子（与 _unload_single_module 保持一致）
        lifecycle.unregister_by_owner(module_name)

        # 清理该模块注册的 i18n 翻译键
        try:
            i18n.unregister_domain(module_name)
        except Exception:
            pass

        if self._sdk is not None:
            sdk_dict = getattr(self._sdk, "__dict__", {})
            if module_name in sdk_dict:
                try:
                    del sdk_dict[module_name]
                except Exception:
                    pass

        if module_name in self._modules:
            del self._modules[module_name]
        self._loaded_modules.discard(module_name)
        # 同步移除懒加载代理，保持与 SDK 属性被删除的状态一致
        self.unregister_lazy(module_name)
        return True

    def unregister(self, name: str | None = None, *, module_name: str | None = None) -> bool:
        """
        取消注册模块

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 是否取消成功

        {!--< internal-use >!--}
        注意：此方法仅取消注册，不卸载已加载的模块
        {!--< /internal-use >!--}
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.unregister", "module_name", "name")
            name = module_name
        if name is None:
            return False
        module_name = name
        if module_name not in self._module_classes:
            logger.warning(i18n.t("core.module.not_registered", name=module_name))
            return False

        # 移除模块类
        self._module_classes.pop(module_name)

        # 移除模块信息
        if module_name in self._module_info:
            self._module_info.pop(module_name)

        # 移除懒加载代理（若存在）
        self.unregister_lazy(module_name)

        logger.info(i18n.t("core.module.module_unregistered", name=module_name))
        return True

    def clear(self) -> None:
        """
        清除所有模块实例和类

        {!--< internal-use >!--}
        此方法用于反初始化时完全重置模块管理器状态
        {!--< /internal-use >!--}
        """
        from .router import router

        # 清理所有模块的路由
        for module_name in list(self._module_classes.keys()):
            result = router.unregister_all_by_namespace(module_name)
            if result["http_count"] > 0 or result["websocket_count"] > 0:
                logger.debug(
                    i18n.t(
                        "core.module.unload_routes_cleaned",
                        name=module_name,
                        http=result["http_count"],
                        ws=result["websocket_count"],
                    )
                )

        # 清除所有模块实例
        self._modules.clear()

        # 清除所有已加载的模块名称
        self._loaded_modules.clear()

        # 清除所有模块类
        self._module_classes.clear()

        # 清除所有模块信息
        self._module_info.clear()

        # 清除所有懒加载代理
        self._lazy_modules.clear()

        logger.debug(i18n.t("core.module.cleared"))

    def list_items(self) -> dict[str, bool]:
        """
        列出所有模块状态

        合并配置项与已注册模块，确保禁用模块也可见。

        :return: [dict[str, bool]] {模块名: 是否启用} 字典
        """
        items = dict(config.getConfig(CONFIG_KEY_MODULES_STATUS, {}))
        # 补充已在管理器中注册但配置中不存在的模块
        for name in self._module_classes:
            if name not in items:
                items[name] = self.is_enabled(name)
        return items

    def get_info(self, name: str | None = None, *, module_name: str | None = None) -> dict | None:
        """
        获取模块信息

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 模块信息字典，不存在则返回None

        :example:
        >>> info = module.get_info("MyModule")
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.get_info", "module_name", "name")
            name = module_name
        if name is None:
            return None
        return self._module_info.get(name)

    def get_meta(
        self,
        name: str | None = None,
        *,
        resolve_i18n: bool = True,
        module_name: str | None = None,
    ) -> dict | None:
        """
        获取模块的介绍元信息（描述这个模块是什么、属于哪一类等）

        元信息是模块的**通用介绍数据**，供 help 模块、Dashboard 模块列表、
        模块商店等各类界面 / 生态模块消费。

        **i18n 支持**：元信息字段值可为纯字符串，或 i18n 字典
        ``{"i18n": "key.path", "default": "兜底文本"}``（与配置 description 约定一致）。
        翻译键通过模块的 ``I18nClass`` 声明注册（键路径 ``<模块名>.<属性名>``）。
        ``resolve_i18n=True``（默认）时解析为当前语言文本；``False`` 时透传原始字典。

        解析优先级：模块类声明的 ``get_meta()`` > 注册时传入的 ``info``，缺失字段自动补全。

        :param name: 模块名称
        :param resolve_i18n: 是否解析 i18n 字典为当前语言文本（默认 True）
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 元信息字典，模块未注册时返回 None

        :example:
        >>> meta = module.get_meta("Weather")
        >>> meta["description"]  # 当前语言下的模块简介
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.get_meta", "module_name", "name")
            name = module_name
        if name is None or name not in self._module_classes:
            return None

        meta: dict[str, Any] = {}
        # 1. 模块类声明的 get_meta()（支持 ModuleMeta 声明类或 dict）
        module_class = self._module_classes[name]
        get_meta_method = getattr(module_class, "get_meta", None)
        if callable(get_meta_method):
            try:
                declared = get_meta_method()
                if isinstance(declared, dict):
                    meta.update(declared)
                elif declared is not None and hasattr(declared, "to_dict"):
                    # ModuleMeta 声明类：内部解析只依赖 to_dict() 输出
                    meta.update(declared.to_dict())
            except Exception:
                pass
        # 2. 注册时传入的 info
        info = self._module_info.get(name)
        if isinstance(info, dict):
            for key, value in info.items():
                meta.setdefault(key, value)
        # 3. 自动补全
        meta.setdefault("name", name)
        if "commands" not in meta:
            meta["commands"] = self._commands_of(name)
        # 4. i18n 解析
        if resolve_i18n:
            meta = {k: self._resolve_meta_value(v) for k, v in meta.items()}
        return meta

    @staticmethod
    def _resolve_meta_value(value: Any) -> Any:
        """
        {!--< internal-use >!--}
        解析元信息字段值：i18n 字典 → 当前语言文本；其余原样返回

        :param value: 原始值（str 或 {"i18n": ..., "default": ...}）
        :return: 解析后的值
        """
        if isinstance(value, dict) and "i18n" in value:
            from .i18n import i18n

            key = value["i18n"]
            default = value.get("default", key)
            return i18n.t(key, default=default)
        return value

    def _commands_of(self, module_name: str) -> list[str]:
        """{!--< internal-use >!--} 列出该模块注册的主命令名"""
        try:
            from .Event import command

            return sorted(
                cmd_name
                for cmd_name, cmd_info in command.get_commands().items()
                if cmd_info.get("owner") == module_name and cmd_name == cmd_info.get("main_name")
            )
        except Exception:
            return []

    def get_commands_overview(
        self,
        *,
        event: Any = None,
        platform: str | None = None,
        bot_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        获取命令总览（模块 meta + 其注册的命令，按模块聚合）

        聚合每个模块的**介绍元信息**与其**注册的命令**（含别名 / 分组 / 帮助文本），
        便于 help 模块、管理界面等按模块展示"这个模块是干什么的 + 有哪些命令"。
        命令的 help / hidden 字段为合并控制面覆盖后的生效值（用户优先）。

        传入作用域上下文（``event`` 或 ``platform`` / ``bot_id`` / ``session_id``
        任一）时，当前会话不可用模块不进入总览（会话感知总览）。

        :param event: 可选，事件上下文（Event 或 dict）
        :param platform: 可选，平台名（与 event 叠加时显式参数优先）
        :param bot_id: 可选，Bot 标识
        :param session_id: 可选，会话标识
        :return: {模块名: {"meta": {...}, "commands": [{name, aliases, group, help, hidden}]}}

        :example:
        >>> overview = module.get_commands_overview()
        >>> overview["Weather"]["meta"]["description"]
        "查询城市天气"
        >>> overview["Weather"]["commands"][0]["name"]
        "weather"
        >>> overview = module.get_commands_overview(event=event)   # 会话感知
        """
        from .Event import command

        commands = command.get_commands(event=event, platform=platform, bot_id=bot_id, session_id=session_id)
        commands_by_owner: dict[str, list[dict[str, Any]]] = {}
        for cmd_name, cmd_info in commands.items():
            owner = cmd_info.get("owner")
            if not owner or cmd_name != cmd_info.get("main_name"):
                continue
            # 生效值：读合并覆盖后的参数（与帮助渲染 / 执行判定同源）
            effective = command.get_command(cmd_name) or cmd_info
            aliases = sorted(alias for alias, main in command.aliases.items() if main == cmd_name and alias != cmd_name)
            commands_by_owner.setdefault(owner, []).append(
                {
                    "name": cmd_name,
                    "aliases": aliases,
                    "group": effective.get("group"),
                    "help": effective.get("help"),
                    "hidden": bool(effective.get("hidden", False)),
                }
            )

        result: dict[str, dict[str, Any]] = {}
        for owner, cmds in commands_by_owner.items():
            result[owner] = {
                "meta": self.get_meta(owner) or {},
                "commands": cmds,
            }
        return result

    def get_status_summary(self) -> dict[str, Any]:
        """
        获取模块的完整状态摘要

        便于WebUI展示所有模块的注册、加载和启用状态，
        包含已禁用模块以便于管理。

        :return: 状态摘要字典

        :example:
        >>> summary = module.get_status_summary()
        >>> # {
        >>> #     "modules": {
        >>> #         "MyModule": {
        >>> #             "status": "loaded",
        >>> #             "enabled": True,
        >>> #             "is_base_module": True
        >>> #         },
        >>> #         "DisabledModule": {
        >>> #             "status": "disabled",
        >>> #             "enabled": False,
        >>> #             "is_base_module": None
        >>> #         }
        >>> #     }
        >>> # }
        """
        from .config import parse_bool_config

        modules_summary = {}
        for name in self._module_classes:
            module_class = self._module_classes[name]
            modules_summary[name] = {
                "status": "loaded" if name in self._loaded_modules else "registered",
                "enabled": self.is_enabled(name),
                "is_base_module": self._is_subclass(module_class, BaseModule),
            }

        # 补充配置中存在但未加载的模块（被禁用的模块），方便管理界面显示并开启
        config_status = config.getConfig(CONFIG_KEY_MODULES_STATUS, {})
        for name in config_status:
            if name not in modules_summary:
                modules_summary[name] = {
                    "status": "disabled",
                    "enabled": parse_bool_config(config_status[name]),
                    "is_base_module": None,
                }

        return {"modules": modules_summary}

    def get_topology(self) -> dict[str, Any]:
        """
        获取模块的拓扑树数据（便于 WebUI 展示）

        聚合每个模块拥有的命令、事件处理器、路由与生命周期钩子，
        按 owner（模块名）归并，展示模块与资源的归属关系。

        :return: 拓扑树字典
            {"modules": {name: {
                "loaded": bool, "enabled": bool,
                "load_strategy": {"lazy": bool|None, "priority": int|None},
                "info": dict|None,
                "commands": [str, ...],
                "handlers": {event_type: count},
                "routes": {"http": [...], "ws": [...], "sse": [...]},
                "lifecycle_hooks": int,
                "scope_applies": bool,
            }}}

        :example:
        >>> topology = module.get_topology()
        >>> print(topology["modules"]["Chat"]["commands"])
        ["chat"]
        """
        from .config import parse_bool_config
        from .Event import command, message, meta, notice, request
        from .lifecycle import lifecycle
        from .router import router

        # 命令：{owner: [主命令名, ...]}
        commands_by_owner: dict[str, list[str]] = {}
        for cmd_name, cmd_info in command.get_commands().items():
            owner = cmd_info.get("owner")
            if not owner or cmd_name != cmd_info.get("main_name"):
                continue
            commands_by_owner.setdefault(owner, []).append(cmd_name)

        # 事件处理器：{owner: {event_type: count}}
        handlers_by_owner: dict[str, dict[str, int]] = {}
        for event_type, event_handler in (
            ("message", message.handler),
            ("notice", notice.handler),
            ("request", request.handler),
            ("meta", meta.handler),
        ):
            for handler_info in event_handler.handlers:
                owner = handler_info.get("owner")
                if not owner:
                    continue
                handlers_by_owner.setdefault(owner, {}).setdefault(event_type, 0)
                handlers_by_owner[owner][event_type] += 1

        # 路由：{namespace: {"http": [...], "ws": [...], "sse": [...]}}
        routes_by_namespace = router.list_namespaces()

        # 生命周期钩子：{owner: count}
        hook_counts = lifecycle.get_owner_counts()

        modules_summary: dict[str, Any] = {}
        for name in self._module_classes:
            module_class = self._module_classes[name]
            strategy = {"lazy": None, "priority": None}
            if hasattr(module_class, "get_load_strategy"):
                try:
                    strat = module_class.get_load_strategy()
                    strategy = {
                        "lazy": getattr(strat, "lazy_load", None),
                        "priority": getattr(strat, "priority", None),
                    }
                except Exception:
                    pass
            ns_routes = routes_by_namespace.get(name, {})
            modules_summary[name] = {
                "loaded": name in self._loaded_modules,
                "enabled": parse_bool_config(config.getConfig(CONFIG_KEY_MODULE_STATUS_OF.format(name), True)),
                "load_strategy": strategy,
                "info": self._module_info.get(name),
                "commands": sorted(commands_by_owner.get(name, [])),
                "handlers": handlers_by_owner.get(name, {}),
                "routes": {
                    "http": list(ns_routes.get("http", [])),
                    "ws": list(ns_routes.get("websocket", [])),
                    "sse": list(ns_routes.get("sse", [])),
                },
                "lifecycle_hooks": hook_counts.get(name, 0),
                "scope_applies": True,
            }

        return {"modules": modules_summary}

    # 兼容性方法 - 保持向后兼容
    def list_modules(self) -> dict[str, bool]:
        warnings.warn(
            i18n.t("core.module.list_modules_deprecated"),
            DeprecationWarning,
            stacklevel=2,
        )
        return self.list_items()

    # ==================== 工具方法 ====================

    def __getattr__(self, module_name: str) -> Any:
        """
        通过属性访问获取模块实例

        :param module_name: [str] 模块名称
        :return: [Any] 模块实例
        :raises AttributeError: 当模块不存在或未启用时

        :example:
        >>> my_module = module.MyModule
        """
        if (module_instance := self.get(module_name)) is None:
            raise AttributeError(i18n.t("core.module.module_not_enabled", name=module_name))
        return module_instance

    def __contains__(self, module_name: str) -> bool:
        """
        检查模块是否存在且处于启用状态

        :param module_name: [str] 模块名称
        :return: [bool] 模块是否存在且启用

        :example:
        >>> if "MyModule" in module:
        ...     ...
        """
        return self.exists(module_name) and self.is_enabled(module_name)

    def __repr__(self) -> str:
        registered = list(self._module_classes.keys())
        loaded = list(self._loaded_modules)
        return f"<ModuleManager registered={registered} loaded={loaded}>"


module: ModuleManager = ModuleManager()

__all__ = ["module"]
