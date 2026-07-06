"""
ErisPulse 模块系统

提供标准化的模块注册、加载和管理功能，与适配器系统保持一致的设计模式
"""

import inspect
import warnings
from typing import Any

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
        # 模块存储
        self._modules: dict[str, Any] = {}  # 已加载的模块实例
        self._module_classes: dict[str, type] = {}  # 模块类映射
        self._loaded_modules: set = set()  # 已加载的模块名称
        self._module_info: dict[str, dict] = {}  # 模块信息
        self._sdk = None

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
            logger.error(i18n.t("core.module.set_sdk_failed", error=e))
            return False

    # ==================== 模块注册与管理 ====================

    def register(
        self, module_name: str, module_class: type, module_info: dict | None = None
    ) -> bool:
        """
        注册模块类

        :param module_name: 模块名称
        :param module_class: 模块类
        :param module_info: 模块信息
        :return: 是否注册成功

        :raises TypeError: 当模块类无效时抛出

        :example:
        >>> module.register("MyModule", MyModuleClass)
        """
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

    async def load(self, module_name: str) -> bool:
        """
        加载指定模块（标准化加载逻辑）

        :param module_name: 模块名称
        :return: 是否加载成功

        :example:
        >>> await module.load("MyModule")
        """
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
                    setattr(instance, "moduleInfo", self._module_info[module_name])

                # 注入模块注册名，用于配置键解析等
                setattr(instance, "_module_name", module_name)

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
                    name=module_name if module_name else "All",
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
                    name=module_name if module_name else "All",
                    error=e,
                ),
            )
            logger.error(i18n.t("core.module.load_failed", name=module_name, error=e))
            return False

    async def unload(self, module_name: str | None = None) -> bool:
        """
        卸载指定模块或所有模块

        :param module_name: 模块名称，None表示卸载所有模块（默认None）
        :return: 是否卸载成功

        :example:
        >>> await module.unload("MyModule")  # 卸载单个模块
        >>> await module.unload()  # 卸载所有模块
        """
        if module_name is None:
            # 卸载所有模块
            success = True
            for name in list(self._loaded_modules):
                if not await self._unload_single_module(name):
                    success = False
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
        # 模块未加载，返回 True（表示没有需要卸载的模块，这不是错误）
        if module_name not in self._loaded_modules:
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

            if self._sdk is not None:
                sdk_dict = getattr(self._sdk, "__dict__", {})
                if module_name in sdk_dict:
                    try:
                        del sdk_dict[module_name]
                    except Exception:
                        pass

            del self._modules[module_name]
            self._loaded_modules.discard(module_name)

            logger.info(i18n.t("core.module.unload_success", name=module_name))
            return True

        except Exception as e:
            logger.error(i18n.t("core.module.unload_failed", name=module_name, error=e))
            return False

    def get(self, module_name: str) -> Any:
        """
        获取模块实例

        :param module_name: 模块名称
        :return: 模块实例或None

        :example:
        >>> my_module = module.get("MyModule")
        """
        return self._modules.get(module_name)

    def exists(self, module_name: str) -> bool:
        """
        检查模块是否已注册

        :param module_name: 模块名称
        :return: 模块是否已注册（即 module.register() 已被调用）

        {!--< tips >!--}
        exists() 只检查模块类是否已注册到管理器，用于验证模块是否可以加载。
        如需检查模块是否启用，请使用 is_enabled()。
        {!--< /tips >!--}
        """
        return module_name in self._module_classes

    def is_loaded(self, module_name: str) -> bool:
        """
        检查模块是否已加载

        :param module_name: 模块名称
        :return: 模块是否已加载

        :example:
        >>> if module.is_loaded("MyModule"): ...
        """
        return module_name in self._loaded_modules

    def is_running(self, module_name: str) -> bool:
        """
        检查模块是否正在运行（已加载）

        :param module_name: 模块名称
        :return: 模块是否正在运行

        :example:
        >>> if module.is_running("MyModule"):
        >>>     print("MyModule 正在运行")
        """
        return self.is_loaded(module_name)

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

    def _config_register(self, module_name: str, enabled: bool = True) -> bool:
        """
        注册新模块信息

        {!--< internal-use >!--}
        此方法仅供内部使用

        :param module_name: 模块名称
        :param enabled: 是否启用模块 (默认: True，新模块默认启用)
        :return: 操作是否成功
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

    def is_enabled(self, module_name: str) -> bool:
        """
        检查模块是否启用

        :param module_name: 模块名称
        :return: 模块是否启用

        {!--< tips >!--}
        模块启用条件：
        1. 模块在配置文件中（ErisPulse.modules.status.{module_name} 存在）
        2. 配置值为启用状态

        如果模块未在配置中，默认启用并自动写入配置
        {!--< /tips >!--}
        """
        from .config import parse_bool_config

        status = config.getConfig(CONFIG_KEY_MODULE_STATUS_OF.format(module_name))

        # 模块未在配置中，默认启用并写入配置
        if status is None:
            config.setConfig(CONFIG_KEY_MODULE_STATUS_OF.format(module_name), True)
            return True

        # 解析配置值
        return parse_bool_config(status)

    def enable(self, module_name: str) -> bool:
        """
        启用模块

        :param module_name: [str] 模块名称
        :return: [bool] 操作是否成功
        """
        if module_name not in self._module_classes:
            logger.error(i18n.t("core.module.module_not_exist", name=module_name))
            return False

        config.setConfig(CONFIG_KEY_MODULE_STATUS_OF.format(module_name), True)
        logger.info(i18n.t("core.module.module_enabled", name=module_name))
        return True

    def disable(self, module_name: str) -> bool:
        """
        禁用模块

        :param module_name: [str] 模块名称
        :return: [bool] 操作是否成功
        """
        config.setConfig(CONFIG_KEY_MODULE_STATUS_OF.format(module_name), False)
        logger.info(i18n.t("core.module.module_disabled", name=module_name))

        if module_name not in self._loaded_modules:
            return True

        instance = self._modules.get(module_name)
        if instance and hasattr(instance, "on_unload"):
            try:
                if inspect.iscoroutinefunction(instance.on_unload):
                    import asyncio

                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(
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
        return True

    def unregister(self, module_name: str) -> bool:
        """
        取消注册模块

        :param module_name: 模块名称
        :return: 是否取消成功

        {!--< internal-use >!--}
        注意：此方法仅取消注册，不卸载已加载的模块
        {!--< /internal-use >!--}
        """
        if module_name not in self._module_classes:
            logger.warning(i18n.t("core.module.not_registered", name=module_name))
            return False

        # 移除模块类
        self._module_classes.pop(module_name)

        # 移除模块信息
        if module_name in self._module_info:
            self._module_info.pop(module_name)

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

    def get_info(self, module_name: str) -> dict | None:
        """
        获取模块信息

        :param module_name: 模块名称
        :return: 模块信息字典，不存在则返回None

        :example:
        >>> info = module.get_info("MyModule")
        """
        return self._module_info.get(module_name)

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
