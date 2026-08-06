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
            if (
                parent.__name__ == base_cls.__name__
                and parent.__module__ == base_cls.__module__
            ):
                return True
        return False

    def __init__(self):
        # 模块存储
        self._modules: dict[str, Any] = {}  # 已加载的模块实例
        self._module_classes: dict[str, type] = {}  # 模块类映射
        self._loaded_modules: set = set()  # 已加载的模块名称
        self._module_info: dict[str, dict] = {}  # 模块信息
        self._lazy_modules: dict[
            str, Any
        ] = {}  # 懒加载代理（未触发初始化时 get() 返回它）
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
            _warn_deprecated_kwarg(
                "ModuleManager.register", "module_class", "class_type"
            )
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

    async def load(
        self, name: str | None = None, *, module_name: str | None = None
    ) -> bool:
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

        logger.trace(f"开始加载模块: {module_name}")

        try:
            module_class = self._module_classes[module_name]

            init_signature = inspect.signature(module_class.__init__)
            params = [p for p in init_signature.parameters.values() if p.name != "self"]

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
                            f"模块 {module_name} i18n 注册阶段异常",
                            exc_info=True,
                        )

                if hasattr(instance, "on_load"):
                    try:
                        if inspect.iscoroutinefunction(instance.on_load):
                            await instance.on_load({"module_name": module_name})
                        else:
                            instance.on_load({"module_name": module_name})
                    except Exception as e:
                        logger.error(
                            i18n.t(
                                "core.module.on_load_failed", name=module_name, error=e
                            )
                        )
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
            logger.error(
                i18n.t("core.module.systemexit", name=module_name, code=e.code)
            )
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

    async def unload(
        self, name: str | None = None, *, module_name: str | None = None
    ) -> bool:
        """
        卸载指定模块或所有模块

        :param name: 模块名称，None表示卸载所有模块（默认None）
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 是否卸载成功

        :example:
        >>> await module.unload("MyModule")  # 卸载单个模块
        >>> await module.unload()  # 卸载所有模块
        """
        # 兼容旧关键字参数（已弃用）
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.unload", "module_name", "name")
            name = module_name
        module_name = name
        if module_name is None:
            # 卸载所有模块
            success = True
            for loaded_name in list(self._loaded_modules):
                if not await self._unload_single_module(loaded_name):
                    success = False
            # 一并清理未初始化的懒加载代理，避免卸载后仍可通过代理访问
            for lazy_name in list(self._lazy_modules):
                self._cleanup_lazy(lazy_name)
            module_name = "All"
        else:
            success = await self._unload_single_module(module_name)

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
            instance = self._modules.get(module_name)
            if instance and hasattr(instance, "on_unload"):
                try:
                    if inspect.iscoroutinefunction(instance.on_unload):
                        await instance.on_unload({"module_name": module_name})
                    else:
                        instance.on_unload({"module_name": module_name})
                except Exception as e:
                    logger.error(
                        i18n.t(
                            "core.module.on_unload_failed", name=module_name, error=e
                        )
                    )

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

    def exists(
        self, name: str | None = None, *, module_name: str | None = None
    ) -> bool:
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

    def is_loaded(
        self, name: str | None = None, *, module_name: str | None = None
    ) -> bool:
        """
        检查模块是否已加载

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 模块是否已加载

        :example:
        >>> if module.is_loaded("MyModule"): ...
        """
        if module_name is not None:
            _warn_deprecated_kwarg("ModuleManager.is_loaded", "module_name", "name")
            name = module_name
        if name is None:
            return False
        return name in self._loaded_modules

    def is_running(
        self, name: str | None = None, *, module_name: str | None = None
    ) -> bool:
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
        status = (
            i18n.t("core.adapter.status_enabled")
            if enabled
            else i18n.t("core.adapter.status_disabled")
        )
        logger.info(
            i18n.t("core.module.registered_status", name=module_name, status=status)
        )
        return True

    def is_enabled(
        self, name: str | None = None, *, module_name: str | None = None
    ) -> bool:
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

    def enable(
        self, name: str | None = None, *, module_name: str | None = None
    ) -> bool:
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

        config.setConfig(
            CONFIG_KEY_MODULE_STATUS_OF.format(module_name), True, immediate=True
        )
        logger.info(i18n.t("core.module.module_enabled", name=module_name))
        return True

    def disable(
        self, name: str | None = None, *, module_name: str | None = None
    ) -> bool:
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
        config.setConfig(
            CONFIG_KEY_MODULE_STATUS_OF.format(module_name), False, immediate=True
        )
        logger.info(i18n.t("core.module.module_disabled", name=module_name))

        if module_name not in self._loaded_modules:
            # 即使模块尚未实例化（懒加载代理），也要清理代理与 SDK 属性
            self._cleanup_lazy(module_name)
            return True

        instance = self._modules.get(module_name)
        if instance and hasattr(instance, "on_unload"):
            try:
                if inspect.iscoroutinefunction(instance.on_unload):
                    import asyncio

                    try:
                        from ..runtime.tasks import spawn_background

                        spawn_background(
                            instance.on_unload({"module_name": module_name})
                        )
                    except RuntimeError:
                        asyncio.run(instance.on_unload({"module_name": module_name}))
                else:
                    instance.on_unload({"module_name": module_name})
            except Exception as e:
                logger.error(
                    i18n.t("core.module.on_unload_failed", name=module_name, error=e)
                )

        from .router import router

        router.unregister_all_by_namespace(module_name)

        from .Event import command, message, meta, notice, request

        command.unregister_by_owner(module_name)
        for event_handler in [message, notice, request, meta]:
            event_handler.handler.unregister_by_owner(module_name)

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

    def unregister(
        self, name: str | None = None, *, module_name: str | None = None
    ) -> bool:
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

    def get_info(
        self, name: str | None = None, *, module_name: str | None = None
    ) -> dict | None:
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
            raise AttributeError(
                i18n.t("core.module.module_not_enabled", name=module_name)
            )
        return module_instance

    def __contains__(self, module_name: str) -> bool:
        """
        检查模块是否存在且处于启用状态

        :param module_name: [str] 模块名称
        :return: [bool] 模块是否存在且启用

        :example:
        >>> if "MyModule" in module: ...
        """
        return self.exists(module_name) and self.is_enabled(module_name)

    def __repr__(self) -> str:
        registered = list(self._module_classes.keys())
        loaded = list(self._loaded_modules)
        return f"<ModuleManager registered={registered} loaded={loaded}>"


module: ModuleManager = ModuleManager()

__all__ = ["module"]
