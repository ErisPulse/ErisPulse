"""
ErisPulse 模块系统

提供标准化的模块注册、加载和管理功能，与适配器系统保持一致的设计模式
"""

import asyncio
import inspect
import time
import traceback
import warnings
from typing import Any, TypeVar

from ..runtime.context import current_caller, current_owner
from .Bases import BaseModule
from .Bases.errors import (
    ModuleCallError,
    ModuleCallTimeoutError,
    ModuleNotAvailableError,
    ServiceNotProvidedError,
)
from .Bases.manager import ManagerBase
from .config import config
from .constants import (
    CONFIG_KEY_MODULE_STATUS_OF,
    CONFIG_KEY_MODULES_STATUS,
    DEFAULT_MODULE_ENABLED,
    EVENT_MODULE_RELOAD,
    MODULE_SOURCE_PLUGIN_FOLDER,
    MODULE_SOURCE_RUNTIME,
)
from .di import call_with_depends, call_with_depends_sync
from .i18n import i18n
from .lifecycle import lifecycle
from .logger import logger

# 模块类型 TypeVar，用于 get() 的泛型返回，让用户可通过类型注解获得 IDE 补全
# 用法： my_module: MyModule = sdk.module.get("MyModule")
_TModule = TypeVar("_TModule", bound=BaseModule)


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

    # 已记录过的弃用警告（owner, old_kwarg），每个组合只警告一次，避免热路径日志刷屏
    _DEPRECATED_KWARG_WARNED: set[tuple[str, str]] = set()

    @staticmethod
    def _warn_deprecated_kwarg(owner: str, old: str, new: str) -> None:
        """
        {!--< internal-use >!--}
        当检测到使用已弃用的旧关键字参数时，记录一次弃用日志并说明迁移方式

        :param owner: 所属方法名（如 "ModuleManager.get"）
        :param old: 已弃用的旧参数名
        :param new: 推荐使用的新参数名
        """
        key = (owner, old)
        if key in ModuleManager._DEPRECATED_KWARG_WARNED:
            return
        ModuleManager._DEPRECATED_KWARG_WARNED.add(key)
        logger.warning(
            i18n.t(
                "core.deprecated.kwarg",
                owner=owner,
                old=old,
                new=new,
            )
        )

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
        self._module_services: dict[str, list[dict[str, Any]] | None] = {}  # meta.services 契约缓存（load 时解析，规范化 dict 列表）
        self._last_errors: dict[str, dict] = {}  # load 失败现场（last_error / get_info.last_error 消费）
        self._module_activity: dict[str, float] = {}  # 模块活跃时间戳（休眠清扫判定用）
        self._dormant_after: dict[str, float] = {}  # 休眠阈值（秒；initialize_modules 挂载时解析 dormant_after）
        self._dormancy_sweeper_started = False  # 休眠清扫器防重入标记
        # 注册配置变更路由：将 config.set / config.updated 事件转发到各模块的 on_config_update
        self._register_config_change_routing()

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
        if self.sdk_ref() is not None:
            sdk_dict = getattr(self.sdk_ref(), "__dict__", {})
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
            self._warn_deprecated_kwarg("ModuleManager.register", "module_name", "name")
            name = module_name
        if module_class is not None:
            self._warn_deprecated_kwarg("ModuleManager.register", "module_class", "class_type")
            class_type = module_class
        if module_info is not None:
            self._warn_deprecated_kwarg("ModuleManager.register", "module_info", "info")
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

        # 检查模块名是否已存在
        if module_name in self._module_classes:
            warn_msg = i18n.t("core.module.exists_overwrite", name=module_name)
            logger.warning(warn_msg)

        self._module_classes[module_name] = module_class
        if module_info:
            self._module_info[module_name] = module_info
        else:
            # 运行时注册（无加载器组装的 moduleInfo）：合成最小元信息——
            # top_level 由定义模块推导，使运行时注册的模块同样纳入热重载体系
            self._module_info[module_name] = {
                "meta": self._synthesize_runtime_meta(module_name, module_class),
                "module_class": module_class,
            }

        # 登记模块加载器的重载快照：注册即可重载（此前仅 loader.load() 写入
        # _last_module_objs，运行时注册模块 reload 会报 reload_unknown）。
        # loader 未就绪（SDK 早期注册）时跳过，行为与旧版一致。
        loader = getattr(self.sdk_ref(), "_module_loader", None) if self.sdk_ref() else None
        if loader is not None:
            try:
                self._register_reload_snapshot(loader, module_name, module_class)
            except Exception:
                pass

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

    @staticmethod
    def _synthesize_runtime_meta(module_name: str, module_class: type) -> dict[str, Any]:
        """
        {!--< internal-use >!--}
        为运行时注册的模块合成最小 meta（来源标记 / top_level / 定义模块）

        ``top_level`` 取定义模块 ``__module__`` 的顶层段（与 sdk 层推导规则
        一致），供 reload 清理 ``sys.modules`` 使用；描述 / 版本 / 作者字段
        从 ``get_meta()`` 尽力补全（不可用则省略）。
        """
        meta: dict[str, Any] = {
            "name": module_name,
            "source": MODULE_SOURCE_RUNTIME,
            "top_level": [module_class.__module__.split(".")[0]],
            "defining_module": module_class.__module__,
            "is_base_module": ModuleManager._is_subclass(module_class, BaseModule),
        }
        try:
            m = module_class.get_meta()
            for field_name in ("description", "version", "author"):
                value = getattr(m, field_name, None)
                if value:
                    meta.setdefault(field_name, value)
        except Exception:
            pass
        return meta

    def _register_reload_snapshot(self, loader: Any, module_name: str, module_class: type) -> None:
        """
        {!--< internal-use >!--}
        运行时注册后同步登记模块加载器的重载快照条目

        快照条目为模块类定义所在的模块对象（``sys.modules`` 项），并为其
        挂载合成 moduleInfo（若尚无）——reload 编排经该条目读取 meta 与
        top_level。定义模块不可用或已被占用 moduleInfo 时回退为轻量命名
        空间载体（reload 仅读取 ``__name__`` 与 ``moduleInfo``）。
        """
        import sys

        objs = getattr(loader, "_last_module_objs", None)
        if objs is None:
            return
        info = self._module_info.get(module_name) or {}
        defining = sys.modules.get(module_class.__module__)
        if defining is not None and not hasattr(defining, "moduleInfo"):
            defining.moduleInfo = info  # type: ignore[attr-defined]
            objs[module_name] = defining
            return
        from types import SimpleNamespace

        objs[module_name] = SimpleNamespace(__name__=module_class.__module__, moduleInfo=info)

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
            self._warn_deprecated_kwarg("ModuleManager.load", "module_name", "name")
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

        # 半卸载兜底用：提前绑定（except 路径上可能尚未走到构造语句）
        instance: Any = None
        try:
            module_class = self._module_classes[module_name]

            init_signature = inspect.signature(module_class.__init__)
            params = [
                p
                for p in init_signature.parameters.values()
                if p.name != "self" and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ]

            if (sdk_to_use := self.sdk_ref()) is None:
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
                        await call_with_depends(instance.on_load, {"module_name": module_name})
                    except Exception as e:
                        logger.error(i18n.t("core.module.on_load_failed", name=module_name, error=e))
                        self._record_load_error(module_name, e)
                        # 半卸载：on_load 半途注册的资源（处理器/路由/任务/i18n）
                        # 不回收会成为"有主孤儿"（实例从未进入注册表，purge 无从追踪）
                        await self._half_unload_failed_module(module_name, instance)
                        # 失败自清洗：失败模块的 import 缓存没有保留价值，
                        # 保证「改完代码再 load / reload」必定读到磁盘新代码
                        self._cleanup_failed_module_cache(module_name)
                        return False
            finally:
                current_owner.reset(token)

            # 缓存模块实例
            self._modules[module_name] = instance
            self._loaded_modules.add(module_name)
            # 解析并缓存 meta.services 服务契约（模块间调用白名单）
            self._module_services[module_name] = self._resolve_services(module_name)

            # 加载成功：清除失败现场；记录运行身份（stale 判定与重载后身份核对依据）；
            # 初始化活跃时间戳（休眠清扫判定起点）
            self._last_errors.pop(module_name, None)
            self._module_activity[module_name] = time.monotonic()
            try:
                meta = (self._module_info.get(module_name) or {}).get("meta") or {}
                instance._code_identity = (
                    module_class.__module__,
                    id(module_class),
                    meta.get("version"),
                )
            except Exception:
                pass

            # 冷启动事件回放（get_load_strategy(replay="5m") 声明时）：
            # 模块就绪后从会话收件箱回放最近消息，热插拔进进行中的聊天
            try:
                strat = module_class.get_load_strategy()
                replay = getattr(strat, "replay", None)
                if replay:
                    from ..runtime.tasks import spawn_background

                    spawn_background(self._replay_events(module_name, replay))
            except Exception:
                pass

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
                    "error": repr(e),
                    "traceback": traceback.format_exc(),
                },
                msg=i18n.t("core.module.systemexit", name=module_name, code=e.code),
            )
            logger.error(i18n.t("core.module.systemexit", name=module_name, code=e.code))
            self._record_load_error(module_name, e)
            self._cleanup_failed_module_cache(module_name)
            return False
        except Exception as e:
            # 半卸载：构造成功但后续阶段（moduleInfo 注入 / i18n 预注册 /
            # on_load 前的准备）抛异常时，实例与注册资源同样需要回收
            if instance is not None:
                try:
                    await self._half_unload_failed_module(module_name, instance)
                except Exception:
                    pass
            self._record_load_error(module_name, e)
            self._cleanup_failed_module_cache(module_name)
            await lifecycle.submit_event(
                "module.load",
                data={
                    "module_name": module_name,
                    "success": False,
                    "error": repr(e),
                    "traceback": traceback.format_exc(),
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
        reason: str = "unload",
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
        :param reason: 卸载来意标注，透传给 ``on_before_unload`` 钩子与
                 ``module.before_unload`` 事件（``"unload"`` / ``"reload"`` /
                 ``"disable"`` / ``"cascade"``；框架内部使用，常规调用保持默认）
        :return: 是否卸载成功

        :example:
        >>> await module.unload("MyModule")  # 卸载单个模块（依赖者级联卸载）
        >>> await module.unload("MyModule", purge=True)  # 彻底卸载（释放类引用）
        >>> await module.unload()  # 卸载所有模块
        """
        # 兼容旧关键字参数（已弃用）
        if module_name is not None:
            self._warn_deprecated_kwarg("ModuleManager.unload", "module_name", "name")
            name = module_name
        module_name = name
        # purge 模式下收集被卸载模块的弱引用，卸载完成后诊断是否可回收
        purge_refs: list[tuple[str, Any, Any]] = []
        if module_name is None:
            # 卸载所有模块
            success = True
            for loaded_name in list(self._loaded_modules):
                if not await self._unload_single_module(loaded_name, reason=reason):
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
                    if not await self._unload_single_module(dep_name, reason="cascade"):
                        success = False
                    if purge:
                        purge_refs.append(self._purge_module_stub(dep_name))
            if not await self._unload_single_module(module_name, reason=reason):
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

    async def sleep(self, name: str | None = None, *, module_name: str | None = None) -> bool:
        """
        归眠指定模块（懒加载休眠）

        与 unload 的差异：释放运行时资源（on_unload / 归属任务 / 连接 /
        注册资源），但**保留懒加载代理与注册存根**——模块回到"已注册未
        加载"状态（与从未激活不可区分），下次属性访问 / ``module.call`` /
        ``activate_on`` 事件将透明唤醒（重新实例化并 on_load）。

        归眠前触发 ``on_before_unload``（reason=``"dormant"``），模块可借
        此把状态保存到 storage，唤醒后在 ``on_load`` 中恢复。自动归眠需在
        加载策略中声明 ``get_load_strategy(dormant_after="30m")``；任何已
        加载模块均可手动归眠。

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 是否归眠成功（未加载/未注册返回 True——无事可做）

        :example:
        >>> await module.sleep("HeavyTool")   # 闲置归眠，释放资源
        """
        if module_name is not None:
            self._warn_deprecated_kwarg("ModuleManager.sleep", "module_name", "name")
            name = module_name
        if name is None or name not in self._loaded_modules:
            return True
        success = await self._unload_single_module(name, reason="dormant", sleep=True)
        self._module_activity.pop(name, None)
        return success

    def touch_activity(self, module_name: str) -> None:
        """
        {!--< internal-use >!--}
        记录模块活跃时间戳（休眠清扫判定用）

        埋点位置：事件处理器调用（Core/Event/base._invoke_handler）、
        命令执行（Core/Event/command）、``module.call`` 目标解析。

        :param module_name: 模块注册名
        """
        self._module_activity[module_name] = time.monotonic()

    def _ensure_dormancy_sweeper(self) -> None:
        """
        {!--< internal-use >!--}
        确保休眠清扫器后台循环已启动（幂等；无休眠声明时不启动）
        """
        if self._dormancy_sweeper_started or not self._dormant_after:
            return
        self._dormancy_sweeper_started = True
        from ..runtime.tasks import spawn_background

        spawn_background(self._dormancy_sweep_loop())

    async def _dormancy_sweep_loop(self) -> None:
        """
        {!--< internal-use >!--}
        休眠清扫循环：按固定间隔扫描已加载且声明 dormant_after 的模块，
        闲置超阈值即自动归眠（uninit 时随后台任务统一取消）
        """
        from .constants import MODULE_DORMANCY_SWEEP_INTERVAL_SECS

        while True:
            await asyncio.sleep(MODULE_DORMANCY_SWEEP_INTERVAL_SECS)
            try:
                await self._dormancy_sweep()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f"dormancy sweep failed: {e}")

    async def _dormancy_sweep(self) -> None:
        """
        {!--< internal-use >!--}
        单轮休眠扫描：对闲置超过阈值的已加载模块自动归眠

        依赖方策略：不级联、不跳过——懒模块的依赖方经由持久代理
        （``sdk.<Name>``）/ ``module.call`` 访问，归眠后与"从未激活"不可
        区分，唤醒路径照常生效。
        """
        now = time.monotonic()
        for name, threshold in list(self._dormant_after.items()):
            if name not in self._loaded_modules:
                continue
            last_active = self._module_activity.get(name)
            if last_active is None:
                self._module_activity[name] = now
                continue
            idle = now - last_active
            if idle < threshold:
                continue
            logger.info(
                i18n.t(
                    "loader.module.dormant_sweep",
                    name=name,
                    idle=int(idle),
                    threshold=int(threshold),
                )
            )
            await self.sleep(name)

    async def reload(self, name: str, *, full: bool = True) -> bool:
        """
        热重载单个模块（支持任意来源：本地插件 / 运行时注册 / PyPI 安装包）

        经模块加载器完整执行 语法预检 → 卸载旧实例 → 清理注册与
        ``sys.modules`` 缓存（按顶层包名 + ``invalidate_caches``，默认全量）
        → 重新发现/导入 → 重新注册并加载 流程；依赖该模块的模块会**级联
        重载**并默认重导代码。本地插件（``plugins/`` 目录）来源重扫描插件
        目录；运行时注册来源按定义模块重导并按类名重取；PyPI 安装包来源
        重新查询 entry-point 并重导入模块代码（pip 升级后调用即可生效）。

        ``full=False`` 切换为**轻量重载**：仅按元数据清理 ``sys.modules``，
        PyPI 依赖者卸载后直接重新实例化——仅供超大依赖树的性能敏感场景。

        :param name: 模块名（entry-point 名称、插件名或运行时注册名）
        :param full: 是否全量重载（默认 True；False 为轻量逃生门）
        :return: 是否重载成功（SDK 未初始化时返回 False）

        :example:
        >>> await sdk.module.reload("dice")      # 本地插件
        >>> await sdk.module.reload("MyRuntime") # 运行时注册模块
        >>> await sdk.module.reload("Weather")   # PyPI 安装包模块（默认全量）
        """
        loader = getattr(self.sdk_ref(), "_module_loader", None) if self.sdk_ref() else None
        if loader is None:
            logger.warning(i18n.t("core.sdk.hot_reload.no_loader"))
            return False
        started = time.monotonic()
        success = await loader.reload_module(name, self, self.sdk_ref(), full=full)
        payload: dict[str, Any] = {
            "module_name": name,
            "success": success,
            "full": full,
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
        # 加载器回填的重载明细（身份是否变化 / 版本迁移），透传给事件载荷
        details = getattr(loader, "_last_reload_details", None)
        if isinstance(details, dict):
            for key in ("identity_changed", "version_old", "version_new"):
                if key in details:
                    payload[key] = details[key]
        await lifecycle.emit(EVENT_MODULE_RELOAD, payload)
        return success

    async def reload_all(self) -> "dict[str, bool]":
        """
        全量热重载所有已注册模块（尽力而为语义）

        经模块加载器执行 卸载全部 → 清理全部 ``sys.modules`` 子树 →
        重新发现/注册 → 按依赖拓扑序加载 → 此前已加载的懒加载模块重新
        激活 流程，一次刷新全部模块代码（pip 批量升级后调用即可全部生效）。
        单模块失败仅记录诊断并跳过，不影响其余模块；无整体回滚——
        on_unload 副作用不可撤销，与单模块热重载语义一致。

        :return: 模块注册名 → 是否重载成功（发现阶段即失败的模块不在结果中；
                 SDK 未初始化时返回空字典）

        :example:
        >>> await sdk.module.reload_all()
        """
        loader = getattr(self.sdk_ref(), "_module_loader", None) if self.sdk_ref() else None
        if loader is None:
            logger.warning(i18n.t("core.sdk.hot_reload.no_loader"))
            return {}
        results = await loader.reload_all(self, self.sdk_ref())
        await lifecycle.emit(
            EVENT_MODULE_RELOAD,
            {
                "module_name": "All",
                "success": all(results.values()) if results else True,
                "results": results,
            },
        )
        return results

    async def _run_before_unload(self, module_name: str, instance: Any, reason: str, timeout: float) -> None:
        """
        {!--< internal-use >!--}
        触发卸载前钩子与 ``module.before_unload`` 事件（卸载/禁用流水线第一步）

        先广播事件（第三方状态管家模块可观测），再调用实例可选钩子
        ``on_before_unload(event)``——event 携带 ``module_name`` 与 ``reason``
        （``"reload"`` / ``"unload"`` / ``"disable"`` / ``"cascade"``）。
        任一失败仅告警，不阻塞后续卸载流程（与 on_unload 容忍语义一致）。

        :param module_name: 模块注册名
        :param instance: 模块实例（可为 None——仅广播事件）
        :param reason: 卸载来意
        :param timeout: 钩子优雅执行超时（秒）
        """
        try:
            await lifecycle.emit(
                "module.before_unload",
                data={"module_name": module_name, "reason": reason},
            )
        except Exception:
            pass
        if instance is None or not hasattr(instance, "on_before_unload"):
            return
        import asyncio

        try:
            await asyncio.wait_for(
                call_with_depends(
                    instance.on_before_unload,
                    {"module_name": module_name, "reason": reason},
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(
                i18n.t("core.module.on_unload_timeout", name=module_name, timeout=timeout)
            )
        except Exception as e:
            logger.warning(
                i18n.t("core.module.on_before_unload_failed", name=module_name, error=e)
            )

    async def _unload_single_module(
        self, module_name: str, *, reason: str = "unload", sleep: bool = False
    ) -> bool:
        """
        {!--< internal-use >!--}
        卸载单个模块（``sleep=True`` 时为归眠：释放资源但保留懒加载代理）

        :param module_name: 模块名称
        :param reason: 卸载来意（透传给 on_before_unload 钩子与 before_unload 事件）
        :param sleep: 归眠模式——保留懒加载代理与注册存根，模块回到"已注册未加载"状态
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

            # 卸载前钩子：流水线第一步（先于 on_unload 与任务取消 / 连接关闭）——
            # 模块借此把状态保存到 storage 等介质；reason 标注来意
            await self._run_before_unload(module_name, instance, reason, unload_timeout)

            if instance and hasattr(instance, "on_unload"):
                try:
                    # 优雅收尾超时保护：on_unload 卡死不再阻塞卸载/级联/重载/uninit
                    await asyncio.wait_for(
                        call_with_depends(instance.on_unload, {"module_name": module_name}),
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

            # 兜底关闭该模块名下的全部连接（服务端 WS/SSE 与客户端出站 WS）：
            # 连接是框架登记的一等资源，owner 卸载后不得残留（2.10 连接池化）
            from .connections import connections

            closed_conns = await connections.close_owner(module_name)
            if closed_conns > 0:
                logger.debug(
                    i18n.t(
                        "core.module.unload_connections_closed",
                        name=module_name,
                        count=closed_conns,
                    )
                )

            # 触发外部工具模块登记的归属清理钩子（on_cleanup）：
            # 工具模块借此抛弃内部持有的本模块句柄，使本模块实例可被 GC
            from ..runtime.owner_cleanup import run_owner_cleanups

            cleaned_hooks = await run_owner_cleanups(module_name)
            if cleaned_hooks > 0:
                logger.debug(
                    i18n.t(
                        "core.cleanup.executed",
                        owner=module_name,
                        count=cleaned_hooks,
                    )
                )

            # 清理模块在加载上下文内注册的全部框架资源（unload / disable 共用）
            self._cleanup_module_registrations(module_name)

            if sleep:
                # 归眠模式：保留身份（懒代理 + 注册存根），仅移除运行实例——
                # 与"从未激活"不可区分，下次访问走既有懒初始化路径透明复活
                self._modules.pop(module_name, None)
                self._loaded_modules.discard(module_name)
                proxy = self._lazy_modules.get(module_name)
                if proxy is not None:
                    # 经 type() 取方法：代理会把非下划线属性转发给实例，
                    # 实例上不存在 reset_for_sleep，直接 getattr 会漏掉重置
                    reset_for_sleep = getattr(type(proxy), "reset_for_sleep", None)
                    if reset_for_sleep is not None:
                        try:
                            reset_for_sleep(proxy)
                        except Exception:
                            pass
                    # sdk 属性若被真实实例覆盖（重载路径），换回代理保持透明
                    if self.sdk_ref() is not None:
                        sdk_dict = getattr(self.sdk_ref(), "__dict__", {})
                        if sdk_dict.get(module_name) is not proxy:
                            try:
                                setattr(self.sdk_ref(), module_name, proxy)
                            except Exception:
                                pass
                elif self.sdk_ref() is not None:
                    # 无代理（如运行时注册模块）：移除 sdk 属性，恢复未加载语义
                    getattr(self.sdk_ref(), "__dict__", {}).pop(module_name, None)
                await lifecycle.submit_event(
                    "module.sleep",
                    msg=i18n.t("loader.module.dormant_sleep", name=module_name),
                    data={"module_name": module_name, "success": True},
                )
                return True

            if self.sdk_ref() is not None:
                sdk_dict = getattr(self.sdk_ref(), "__dict__", {})
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

            # 自动轻审计：资源在册而 owner 已注销 = 泄漏实锤（gc 深普查仅
            # epsdk audit --deep 显式触发，此处只做零开销计数扫描）
            try:
                from .ownership import ownership as ownership_service

                orphans = ownership_service.orphans()
                if orphans:
                    logger.warning(
                        f"ownership audit: {len(orphans)} orphan owner(s) after unload "
                        f"of '{module_name}': {[o['owner'] for o in orphans]}"
                    )
            except Exception:
                pass

            return True

        except Exception as e:
            logger.error(i18n.t("core.module.unload_failed", name=module_name, error=e))
            return False

    def _record_load_error(self, module_name: str, e: BaseException) -> None:
        """
        {!--< internal-use >!--}
        记录模块加载失败现场（``last_error()`` / ``get_info().last_error`` 消费）

        :param module_name: 模块注册名
        :param e: 失败异常
        """
        self._last_errors[module_name] = {
            "exception": repr(e),
            "traceback": traceback.format_exc(),
            "at": time.time(),
        }

    def _cleanup_failed_module_cache(self, module_name: str) -> None:
        """
        {!--< internal-use >!--}
        加载失败后的缓存自清洗

        失败模块的 ``sys.modules`` 条目没有任何保留价值——主动弹出并刷新
        插件路径记录，保证「改完代码再 load / reload 一次」必定读到磁盘
        新代码，而不是复用失败存根 + 旧 import 缓存的组合。不影响注册表
        中已登记的模块类（重新 load 无需重新 register）。
        """
        import sys

        purge_names = {module_name}
        meta = (self._module_info.get(module_name) or {}).get("meta") or {}
        for n in meta.get("top_level") or []:
            # 守卫：__main__ / 无源文件的命名空间不可清除（存在重执行入口
            # 脚本的风险），仅清理可安全重建的 import 缓存
            if n == "__main__" or getattr(sys.modules.get(n), "__file__", None) is None:
                continue
            purge_names.add(n)
        for mod_name in list(sys.modules):
            if any(mod_name == n or mod_name.startswith(f"{n}.") for n in purge_names):
                sys.modules.pop(mod_name, None)
        loader = getattr(self.sdk_ref(), "_module_loader", None) if self.sdk_ref() else None
        plugin_loader = getattr(loader, "_plugin_loader", None) if loader is not None else None
        if plugin_loader is not None:
            try:
                getattr(plugin_loader, "_loaded_paths", {}).pop(module_name, None)
            except Exception:
                pass

    async def _half_unload_failed_module(self, module_name: str, instance: Any) -> None:
        """
        {!--< internal-use >!--}
        加载失败（on_load 异常 / 构造后阶段异常）时的半卸载

        对已构造实例按正常卸载同序触发资源回收（on_unload → 取消归属
        任务 → 外部清理钩子 → 框架资源注销），保证 ``__init__`` /
        ``on_load`` 半途注册的资源不成为"有主孤儿"。

        与正常卸载的差异：不触碰 ``_modules`` / ``_loaded_modules`` /
        ``_module_services`` 与 sdk 属性——失败路径从未写入这些注册表；
        ``on_unload`` 已执行的副作用（断连等）与正常卸载一致不可撤销，
        但实例与注册资源不再泄漏。

        :param module_name: 模块注册名
        :param instance: 已构造的实例（构造函数本身抛异常时为 None）
        """
        if instance is not None and hasattr(instance, "on_unload"):
            try:
                await asyncio.wait_for(
                    call_with_depends(instance.on_unload, {"module_name": module_name}),
                    timeout=self._unload_timeout(),
                )
            except asyncio.TimeoutError:
                logger.warning(
                    i18n.t(
                        "core.module.on_unload_timeout",
                        name=module_name,
                        timeout=self._unload_timeout(),
                    )
                )
            except Exception as e:
                logger.error(i18n.t("core.module.on_unload_failed", name=module_name, error=e))

        # 归属权统一回收：取消归属任务 → 外部清理钩子 → 全部注册类资源
        try:
            from .ownership import ownership

            await ownership.reclaim(module_name)
        except Exception:
            self._cleanup_module_registrations(module_name)

    def _cleanup_module_registrations(self, module_name: str) -> None:
        """
        {!--< internal-use >!--}
        清理模块在加载上下文内注册的全部框架资源（unload / disable 共用）

        委托归属权统一门面（``Core/ownership``）完成：i18n 翻译域、路由
        （命名空间 + owner 兜底：中间件 / 首页入口 / 非命名空间路由）、
        适配器事件处理器与中间件、命令与事件处理器、自定义会话类型、
        平台事件方法注入、事件覆写、scope 覆写、交互会话等待、主人身份源
        provider、生命周期钩子。每步失败仅记录日志，不中断后续清理。

        :param module_name: 模块名
        """
        try:
            from .ownership import ownership

            reclaimed = ownership.reclaim_sync(module_name)
            if reclaimed:
                logger.debug(f"ownership reclaimed for module '{module_name}': {reclaimed}")
        except Exception:
            # 门面不可用时退化为最小清理（i18n 域），保证卸载流程不中断
            try:
                i18n.unregister_domain(module_name)
            except Exception:
                pass

    def audit(self, module_name: str, deep: bool = False) -> "dict[str, Any]":
        """
        归属权泄漏审计（透传归属权统一门面）

        :param module_name: 目标模块名
        :param deep: 附带 gc 实例普查（weakref 存活检查 + 引用方类型；
                     有全局暂停开销，仅显式排障使用）
        :return: 审计报告 dict（owner / counts / orphans / 深普查结果）

        :example:
        >>> report = sdk.module.audit("roll", deep=True)
        >>> report["instance_recyclable"]
        True
        """
        from .ownership import ownership

        return ownership.audit(module_name, deep=deep)

    # ==================== 影子模块（方向十一） ====================

    def is_shadow_module(self, module_name: str) -> bool:
        """
        判断模块名是否为影子 owner（拓扑 / Dashboard 展示用）

        :param module_name: 模块名
        :return: 是否为影子 owner
        """
        try:
            from .shadow import shadow_manager

            return shadow_manager.real_name_of(module_name) is not None
        except Exception:
            return False

    async def shadow_start(
        self,
        module_name: str,
        source: "str | Any",
        owner: "str | None" = None,
    ) -> str:
        """
        启动影子：把新版代码以独立 owner 装载为 ``module_name`` 的影子实例
        （运行时 API；模块代码零改动，影子的出站被拦截记账、不真正发出）

        :param module_name: 被 shadow 的已加载模块名
        :param source: 新版代码路径（目录含 ``__init__.py`` 或单 ``.py`` 文件；
                       建议放在 plugins 目录之外）
        :param owner: 影子 owner 名（默认取路径名）
        :return: 影子 owner 名

        :example:
        >>> await sdk.module.shadow_start("roll", source="downloads/roll_v2")
        'roll_shadow'
        """
        from .shadow import shadow_manager

        return await shadow_manager.start(
            module_name, source, manager=self, sdk=self.sdk_ref(), owner=owner
        )

    async def promote_shadow(self, module_name: str) -> bool:
        """
        影子转正：卸载当前版本 → 影子以真名注册加载 → 失败自动回滚

        转正永远由人确认（无自动晋升）；复用重载快照机制保证失败时旧实例
        继续服务（尽力而为语义：on_unload 已执行的副作用不可撤销）。转正后
        请尽快持久化安装新版本（pip 升级 / 替换插件文件），使重启后仍生效。

        :param module_name: 原模块名
        :return: 是否转正成功
        :raises ValueError: 该模块未绑定影子时

        :example:
        >>> await sdk.module.promote_shadow("roll")
        """
        from .shadow import shadow_manager

        loader = getattr(self.sdk_ref(), "_module_loader", None) if self.sdk_ref() else None
        return await shadow_manager.promote(module_name, self, self.sdk_ref(), loader)

    async def dismiss_shadow(self, module_name: str) -> bool:
        """
        放弃影子：回收影子资源并解除绑定（原模块不受影响）

        :param module_name: 原模块名
        :return: 是否成功（未绑定影子时 False）

        :example:
        >>> await sdk.module.dismiss_shadow("roll")
        """
        from .shadow import shadow_manager

        return await shadow_manager.dismiss(module_name, self, self.sdk_ref())

    def shadow_diff(self, module_name: str) -> "dict[str, Any]":
        """
        影子与线上的行为对比（影子意向出站 × transcript 实际发送，按 trace_id 对齐）

        :param module_name: 原模块名
        :return: 对比报告 dict（shadow_owner / count / aligned）

        :example:
        >>> report = sdk.module.shadow_diff("roll")
        >>> report["count"]
        3
        """
        from .shadow import shadow_manager

        return shadow_manager.diff(module_name)

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
            self._warn_deprecated_kwarg("ModuleManager.get", "module_name", "name")
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
            self._warn_deprecated_kwarg("ModuleManager.exists", "module_name", "name")
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
            self._warn_deprecated_kwarg("ModuleManager.is_loaded", "module_name", "name")
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
            self._warn_deprecated_kwarg("ModuleManager.is_running", "module_name", "name")
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
            self._warn_deprecated_kwarg("ModuleManager.is_enabled", "module_name", "name")
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
            self._warn_deprecated_kwarg("ModuleManager.enable", "module_name", "name")
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
            self._warn_deprecated_kwarg("ModuleManager.disable", "module_name", "name")
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
        if instance is not None:
            # 卸载前钩子（禁用来意）：先于 on_unload 派发；disable 为同步
            # 入口，此处以后台任务并行触发（创建顺序在前，尽力而为保序）
            from ..runtime.tasks import spawn_background

            spawn_background(
                self._run_before_unload(module_name, instance, "disable", self._unload_timeout())
            )
        if instance and hasattr(instance, "on_unload"):
            from ..runtime.owner_cleanup import run_owner_cleanups
            from ..runtime.tasks import cancel_owner_tasks, spawn_background

            async def _fallback_cleanup() -> None:
                """兜底收尾：取消后台任务并触发外部归属清理钩子"""
                cancelled = await cancel_owner_tasks(module_name)
                if cancelled > 0:
                    logger.warning(
                        i18n.t(
                            "core.module.unload_tasks_cancelled",
                            name=module_name,
                            count=cancelled,
                        )
                    )
                cleaned_hooks = await run_owner_cleanups(module_name)
                if cleaned_hooks > 0:
                    logger.debug(
                        i18n.t(
                            "core.cleanup.executed",
                            owner=module_name,
                            count=cleaned_hooks,
                        )
                    )

            if inspect.iscoroutinefunction(instance.on_unload):

                async def _unload_then_cancel_tasks() -> None:
                    """异步 on_unload：完成后兜底取消（与 unload 时序一致）"""
                    import asyncio

                    unload_timeout = self._unload_timeout()
                    try:
                        await asyncio.wait_for(
                            call_with_depends(instance.on_unload, {"module_name": module_name}),
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
                    await _fallback_cleanup()

                spawn_background(_unload_then_cancel_tasks())
            else:
                # 同步 on_unload 内联执行（保持在路由/事件清理之前完成）
                try:
                    call_with_depends_sync(instance.on_unload, {"module_name": module_name})
                except TypeError as e:
                    # 同步上下文不支持异步依赖
                    logger.error(str(e))
                except Exception as e:
                    logger.error(i18n.t("core.module.on_unload_failed", name=module_name, error=e))
                spawn_background(_fallback_cleanup())

        # 清理模块在加载上下文内注册的全部框架资源（与 unload 共用，
        # 含 master provider / 适配器处理器 / 自定义会话类型等，保持卸载对等）
        self._cleanup_module_registrations(module_name)

        if self.sdk_ref() is not None:
            sdk_dict = getattr(self.sdk_ref(), "__dict__", {})
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
            self._warn_deprecated_kwarg("ModuleManager.unregister", "module_name", "name")
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

        # 移除服务契约缓存
        self._module_services.pop(module_name, None)

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

        # 清除服务契约缓存
        self._module_services.clear()

        # 清除休眠状态（活跃时间戳 / 阈值 / 清扫器标记）
        self._module_activity.clear()
        self._dormant_after.clear()
        self._dormancy_sweeper_started = False

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

    def last_error(self, name: str | None = None, *, module_name: str | None = None) -> dict | None:
        """
        查询模块最近一次加载失败现场

        ``load()`` 失败（构造 / on_load 异常 / SystemExit）时记录异常对象、
        完整 traceback 与时间戳；下次加载成功后自动清除。失败详情同时随
        ``get_info()`` 以 ``last_error`` 字段暴露——RPC / 编程调用方直接
        取用，无需翻日志文件。

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 失败现场字典 ``{"exception", "traceback", "at"}``，无记录返回 None

        :example:
        >>> await module.load("X")  # doctest: +SKIP
        False
        >>> module.last_error("X")["exception"]  # doctest: +SKIP
        "AttributeError('...')"
        """
        if module_name is not None:
            self._warn_deprecated_kwarg("ModuleManager.last_error", "module_name", "name")
            name = module_name
        if name is None:
            return None
        return self._last_errors.get(name)

    def get_info(self, name: str | None = None, *, module_name: str | None = None) -> dict | None:
        """
        获取模块信息

        返回值为注册元信息的浅拷贝，附加运行时诊断字段：

        - ``last_error``：最近一次加载失败现场（见 :meth:`last_error`）
        - ``running_identity``：实际在跑的代码身份（``{"module", "version"}``）
        - ``stale``：注册版本 ≠ 运行版本时为 True（"改了代码忘 reload" 一眼可见）

        :param name: 模块名称
        :param module_name: [已弃用] 兼容旧关键字参数，等同 name
        :return: 模块信息字典（含诊断字段），不存在则返回None

        :example:
        >>> info = module.get_info("MyModule")
        """
        if module_name is not None:
            self._warn_deprecated_kwarg("ModuleManager.get_info", "module_name", "name")
            name = module_name
        if name is None:
            return None
        info = self._module_info.get(name)
        if info is None:
            return None
        # 浅拷贝附加诊断字段，避免污染注册表原数据
        result = dict(info)
        last_error = self._last_errors.get(name)
        if last_error is not None:
            result["last_error"] = last_error
        instance = self._modules.get(name)
        identity = getattr(instance, "_code_identity", None) if instance is not None else None
        if identity is not None:
            result["running_identity"] = {"module": identity[0], "version": identity[2]}
            registered_version = (info.get("meta") or {}).get("version")
            result["stale"] = bool(
                registered_version and identity[2] and registered_version != identity[2]
            )
        return result

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
            self._warn_deprecated_kwarg("ModuleManager.get_meta", "module_name", "name")
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
                    meta.update(declared.to_dict())  # pyright: ignore[reportAttributeAccessIssue]
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
            entry: dict[str, Any] = {
                "status": "loaded" if name in self._loaded_modules else "registered",
                "enabled": self.is_enabled(name),
                "is_base_module": self._is_subclass(module_class, BaseModule),
                "failed": name in self._last_errors,
            }
            instance = self._modules.get(name)
            identity = getattr(instance, "_code_identity", None) if instance is not None else None
            if identity is not None:
                registered_version = ((self._module_info.get(name) or {}).get("meta") or {}).get("version")
                entry["stale"] = bool(
                    registered_version and identity[2] and registered_version != identity[2]
                )
            modules_summary[name] = entry

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

    def get_topology(self, *, json_safe: bool = True) -> dict[str, Any]:
        """
        获取模块的拓扑树数据（便于 WebUI 展示）

        聚合每个模块拥有的命令、事件处理器、路由与生命周期钩子，
        按 owner（模块名）归并，展示模块与资源的归属关系。

        :param json_safe: 是否输出可直接 JSON 序列化的安全结构（默认 True）。
                          安全模式下 ``info`` 只保留纯数据的 ``meta`` 子表
                          （丢弃 ``module_class`` / ``strategy`` 等运行时对象），
                          并对整树做序列化兜底净化。

        :return: 拓扑树字典
            {"modules": {name: {
                "loaded": bool, "enabled": bool,
                "load_strategy": {"lazy": bool|None, "priority": int|None},
                "info": dict|None,
                "commands": [str, ...],
                "services": [str, ...],
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
        from .config import json_safe as _json_safe
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
            service_names = self._service_names(name)
            info_entry = self._module_info.get(name)
            if json_safe and isinstance(info_entry, dict):
                # 安全模式只取纯数据的 meta 子表，丢弃 module_class / strategy 等运行时对象
                info_entry = _json_safe(info_entry.get("meta") or {})
            modules_summary[name] = {
                "loaded": name in self._loaded_modules,
                "enabled": parse_bool_config(config.getConfig(CONFIG_KEY_MODULE_STATUS_OF.format(name), True)),
                "load_strategy": strategy,
                "shadow": self.is_shadow_module(name),
                "info": info_entry,
                "commands": sorted(commands_by_owner.get(name, [])),
                "services": sorted(service_names or []),
                "handlers": handlers_by_owner.get(name, {}),
                "routes": {
                    "http": list(ns_routes.get("http", [])),
                    "ws": list(ns_routes.get("websocket", [])),
                    "sse": list(ns_routes.get("sse", [])),
                },
                "lifecycle_hooks": hook_counts.get(name, 0),
                "scope_applies": True,
            }

        result = {"modules": modules_summary}
        return _json_safe(result) if json_safe else result

    # ==================== 模块间通信 ====================

    _REPLAY_UNITS = {"s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0}

    @classmethod
    def _parse_replay_duration(cls, value: Any) -> float:
        """
        {!--< internal-use >!--}
        解析回放时长声明（``"5m"`` / ``"1h"`` / ``"300"``）

        :param value: 时长值
        :return: 秒数
        """
        text = str(value).strip().lower()
        if text and text[-1] in cls._REPLAY_UNITS:
            return float(text[:-1]) * cls._REPLAY_UNITS[text[-1]]
        return float(text)

    def _build_replay_event(self, record: dict[str, Any]) -> Any | None:
        """
        {!--< internal-use >!--}
        从收件箱记录构造回放合成事件

        合成事件带 ``replayed: True`` 标志（处理器可据此跳过副作用）；
        ``user_id`` 优先取记录的 sender，私聊场景回退为 target。

        :param record: 收件箱记录（role / text / ts / sender / session_key）
        :return: 合成事件（Event）；无法解析会话键时返回 None
        """
        from .Event.wrapper import Event

        parts = (record.get("session_key") or "").split(":")
        if len(parts) != 3 or not parts[0]:
            return None
        platform, detail_type, target_id = parts
        text = record.get("text", "")
        data: dict[str, Any] = {
            "id": f"replay-{record.get('ts', 0)}-{abs(hash((record.get('session_key'), text)))}",
            "time": record.get("ts", 0),
            "type": "message",
            "detail_type": detail_type,
            "platform": platform,
            "self": {"platform": platform},
            "user_id": record.get("sender") or target_id or "",
            "message": [{"type": "text", "data": {"text": text}}],
            "alt_message": text,
            "replayed": True,
        }
        if detail_type in ("private", "user"):
            data["user_id"] = target_id or data["user_id"]
        else:
            data["group_id"] = target_id
        return Event(data)

    async def _replay_events(self, module_name: str, replay: Any) -> None:
        """
        {!--< internal-use >!--}
        执行冷启动事件回放：收件箱最近消息 → 仅分发给该模块的处理器

        :param module_name: 模块名
        :param replay: 回放时长声明（"5m" / "1h" / 秒数）
        """
        from .Event import message as _message

        try:
            seconds = self._parse_replay_duration(replay)
        except ValueError:
            logger.warning(i18n.t("loader.module.replay_invalid", name=module_name, value=replay))
            return
        if seconds <= 0:
            return

        try:
            from .transcript import transcript as _transcript

            records = _transcript.recent(seconds)
        except Exception as e:
            logger.trace(i18n.t("loader.module.replay_failed", name=module_name, error=e))
            return
        if not records:
            return

        delivered = 0
        for record in records:
            synth = self._build_replay_event(record)
            if synth is None:
                continue
            try:
                delivered += await _message.handler.dispatch_to_owner(module_name, synth)
            except Exception as e:
                logger.trace(i18n.t("loader.module.replay_failed", name=module_name, error=e))
                break
        if delivered:
            logger.info(
                i18n.t(
                    "loader.module.replay_done",
                    name=module_name,
                    count=delivered,
                    seconds=int(seconds),
                )
            )

    def _resolve_services(self, module_name: str) -> "list[dict[str, Any]] | None":
        """
        {!--< internal-use >!--}
        解析模块的服务契约（get_meta().services），规范化为字典列表

        :param module_name: 模块名称
        :return: ``[{"name": ..., "description": <str|i18n dict|None>,
            "parameters": <dict|None>}, ...]``；未声明时返回 None（公开方法全开放）
        """
        module_class = self._module_classes.get(module_name)
        if module_class is None:
            return None
        try:
            get_meta = getattr(module_class, "get_meta", None)
            if get_meta is None:
                return None
            meta = get_meta()
            services = meta.get("services") if isinstance(meta, dict) else getattr(meta, "services", None)
            if isinstance(services, (list, tuple, set)):
                normalized: list[dict[str, Any]] = []
                seen: set[str] = set()
                for item in services:
                    if isinstance(item, dict) and item.get("name"):
                        parameters = item.get("parameters")
                        entry = {
                            "name": str(item["name"]),
                            "description": item.get("description"),
                            "parameters": parameters if isinstance(parameters, dict) else None,
                        }
                    elif item:
                        entry = {"name": str(item), "description": None, "parameters": None}
                    else:
                        continue
                    # 保序去重（重复声明取首个，含 description 的首个优先）
                    if entry["name"] in seen:
                        continue
                    seen.add(entry["name"])
                    normalized.append(entry)
                return normalized
        except Exception as e:
            logger.trace(i18n.t("core.module.services_resolve_failed", name=module_name, error=e))
        return None

    def _service_names(self, module_name: str) -> "list[str] | None":
        """
        {!--< internal-use >!--}
        获取服务白名单（名字列表）

        :param module_name: 模块名称
        :return: 服务名列表；未声明时返回 None
        """
        declared = self._module_services.get(module_name)
        if declared is None and module_name not in self._module_services:
            declared = self._resolve_services(module_name)
        if declared is None:
            return None
        return [entry["name"] for entry in declared]

    @staticmethod
    def _docstring_first_line(func: Any) -> str:
        """
        {!--< internal-use >!--}
        提取函数 docstring 的摘要行（服务介绍的自动兜底）

        兼容规范的多行 docstring（空行开头）：取**第一个非空行**，
        跳过 doctest 装饰行（``>>>`` / ``...``）。无 docstring 时返回空串。

        :param func: 函数 / 绑定方法
        :return: 摘要文本（可能为空串）
        """
        doc = inspect.getdoc(func) if func is not None else None
        if not doc:
            return ""
        for line in doc.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith((">>>", "...")):
                continue
            return stripped
        return ""

    def _service_description(self, module_name: str, entry: dict[str, Any]) -> str:
        """
        {!--< internal-use >!--}
        解析服务介绍：显式声明（i18n 字典解析）> 方法 docstring 首行 > 空串

        :param module_name: 模块名
        :param entry: 规范化服务条目（{"name", "description"}）
        :return: 介绍文本
        """
        desc = entry.get("description")
        if isinstance(desc, dict) and "i18n" in desc:
            desc = self._resolve_meta_value(desc)
        if desc:
            return str(desc)
        instance = self._modules.get(module_name)
        owner = instance if instance is not None else self._module_classes.get(module_name)
        func = getattr(owner, entry.get("name", ""), None)
        return self._docstring_first_line(func)

    @staticmethod
    def _docstring_params(func: Any) -> dict[str, str]:
        """
        {!--< internal-use >!--}
        从 docstring 提取参数说明（``:param name: 文本`` 行），作为服务参数提示的自动兜底

        兼容 Sphinx 带类型形态（``:param int n: ...``，取末位词为参数名）；
        每个参数取说明首行，重复声明取首个。

        :param func: 函数 / 绑定方法
        :return: ``{参数名: 说明文本}``（无 docstring 或无参数区时为空字典）
        """
        doc = inspect.getdoc(func) if func is not None else None
        if not doc:
            return {}
        hints: dict[str, str] = {}
        for line in doc.splitlines():
            stripped = line.strip()
            if not stripped.startswith(":param"):
                continue
            prefix, sep, text = stripped[len(":param"):].strip().partition(":")
            name_parts = prefix.split()
            if not sep or not name_parts:
                continue
            hints.setdefault(name_parts[-1], text.strip())
        return hints

    def _service_parameters(self, module_name: str, entry: dict[str, Any]) -> dict[str, str]:
        """
        {!--< internal-use >!--}
        解析服务参数提示：显式声明（i18n 字典解析）与方法 docstring ``:param:`` 行按参数合并，
        单参数内显式声明优先

        仅保留方法签名中实际存在的参数（首个 ``self`` / ``cls`` 与变长参数除外）——
        声明与签名不一致时以签名为准，保证提示不会描述不存在的调用面。

        :param module_name: 模块名
        :param entry: 规范化服务条目（{"name", "description", "parameters"}）
        :return: ``{参数名: 提示文本}``（无任何提示来源时为空字典）
        """
        declared: dict[str, str] = {}
        raw = entry.get("parameters")
        if isinstance(raw, dict):
            for key, value in raw.items():
                if isinstance(value, dict) and "i18n" in value:
                    value = self._resolve_meta_value(value)
                if value:
                    declared[str(key)] = str(value)

        instance = self._modules.get(module_name)
        owner = instance if instance is not None else self._module_classes.get(module_name)
        func = getattr(owner, entry.get("name", ""), None)

        # 无签名可依据（方法缺失等）：显式声明原样透出
        if func is None:
            return declared
        try:
            signature = inspect.signature(func)
        except (ValueError, TypeError):
            return declared

        doc_hints = self._docstring_params(func)
        hints: dict[str, str] = {}
        for index, param in enumerate(signature.parameters.values()):
            if index == 0 and param.name in ("self", "cls"):
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            hint = declared.get(param.name) or doc_hints.get(param.name)
            if hint:
                hints[param.name] = hint
        return hints

    def services(self, module_name: str | None = None) -> "dict[str, list[dict[str, Any]]]":
        """
        服务目录：列出模块通过 ``get_meta().services`` 声明的对外服务

        仅包含**显式声明**的模块（未声明的模块不出现在结果中）；
        每个服务附带方法签名字符串、介绍文本与参数提示：

        - **介绍来源**：``services`` 中 ``{"name", "description"}`` 的显式声明
          （支持 i18n 字典，解析为当前语言）> 方法 docstring 首行 > 空串
        - **签名**：``inspect.signature`` 提取
        - **参数提示**：``parameters`` 中 ``{参数名: 说明}`` 显式声明
          （支持 i18n 字典）与方法 docstring ``:param:`` 行按参数合并，
          单参数内显式声明优先；仅含签名内实际存在的参数

        懒加载（已注册未加载）模块同样进入目录——服务发现先于加载发生，
        调用方可据此决定是否 ``call()`` 唤醒目标模块。

        为后续 MCP 化（调用点暴露给 AI）与生态服务发现提供数据基础。

        :param module_name: 仅查询指定模块；None 时列出全部已注册模块中声明了服务的
        :return: ``{模块名: [{"name", "signature", "description", "parameters"}]}``

        :example:
        >>> sdk.module.services()
        {'Chat': [{'name': 'get_history',
                   'signature': '(session_id, n=20)',
                   'description': '查询会话历史',
                   'parameters': {'session_id': '会话 ID', 'n': '返回条数'}}]}
        >>> sdk.module.services("Chat")
        {'Chat': [{'name': 'get_history', ...}]}
        """
        result: dict[str, list[dict[str, Any]]] = {}
        targets = [module_name] if module_name else list(self._module_classes.keys())
        for name in targets:
            services_list = self._module_services.get(name)
            if services_list is None and name not in self._module_services:
                # 未加载（无缓存）时现场解析一次：懒加载模块已声明的服务同样进入目录
                services_list = self._resolve_services(name)
            if not services_list:
                continue
            entries: list[dict[str, Any]] = []
            for svc in services_list:
                svc_name = svc["name"]
                sig = ""
                instance = self._modules.get(name)
                owner = instance if instance is not None else self._module_classes.get(name)
                func = getattr(owner, svc_name, None)
                if func is not None:
                    try:
                        sig = str(inspect.signature(func))
                    except (ValueError, TypeError):
                        sig = "(...)"
                entries.append(
                    {
                        "name": svc_name,
                        "signature": sig,
                        "description": self._service_description(name, svc),
                        "parameters": self._service_parameters(name, svc),
                    }
                )
            result[name] = entries
        return result

    async def _resolve_call_target(self, module_name: str) -> Any:
        """
        {!--< internal-use >!--}
        解析模块间调用的目标实例（含懒加载模块唤醒）

        :param module_name: 模块名称
        :return: 模块实例
        :raises ModuleNotAvailableError: 模块未注册 / 未启用 / 唤醒失败时
        """
        if module_name not in self._module_classes:
            raise ModuleNotAvailableError(
                module_name, "", i18n.t("core.module.call_not_registered", name=module_name)
            )
        if not self.is_enabled(module_name):
            raise ModuleNotAvailableError(
                module_name, "", i18n.t("core.module.call_disabled", name=module_name)
            )

        # 已加载：直接返回实例
        if module_name in self._loaded_modules:
            return self._modules[module_name]

        # 懒加载代理唤醒（事件驱动模块走激活锁，普通懒模块走同步初始化）
        proxy = self._lazy_modules.get(module_name)
        if proxy is not None:
            activate = getattr(proxy, "_activate", None)
            if activate is not None:
                if not await activate():
                    raise ModuleNotAvailableError(
                        module_name,
                        "",
                        i18n.t("core.module.call_activate_failed", name=module_name),
                    )
            else:
                ensure = getattr(proxy, "_ensure_initialized", None)
                if ensure is not None:
                    ensure()
            instance = self.get(module_name)
            if instance is not None:
                return instance

        # 常规加载路径（幂等：已加载直接返回 True）
        if await self.load(module_name):
            instance = self.get(module_name)
            if instance is not None:
                return instance

        raise ModuleNotAvailableError(
            module_name, "", i18n.t("core.module.call_not_registered", name=module_name)
        )

    async def call(
        self,
        module_name: str,
        method: str,
        *args: Any,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        跨模块调用目标模块的服务方法（协议化 RPC）

        与 ``module.<Name>.<method>()`` 裸属性访问的差异：
        目标模块未注册 / 未启用时抛出类型化异常而非 AttributeError；
        懒加载模块自动唤醒；``get_meta().services`` 契约白名单校验；
        调用方经过 scope 出站维度（``actions.<caller>.call``）审计；
        被调方法执行期间 ``current_owner`` 归因到目标模块，
        其内部的 wait_reply / 出站发送 / 日志等正确归属；
        调用方身份保留在 ``current_caller`` 上下文中（``get_current_caller()``
        读取），供被调方识别调用来源；
        协程方法带超时语义（超时抛 :class:`ModuleCallTimeoutError`）。

        :param module_name: 目标模块名
        :param method: 目标方法名
        :param args: 位置参数（透传给目标方法）
        :param timeout: 超时秒数（默认 30 秒；None 表示不限时；仅对协程方法生效）
        :param kwargs: 关键字参数（透传给目标方法）
        :return: 目标方法的返回值
        :raises ModuleNotAvailableError: 目标模块未注册 / 未启用 / 唤醒失败
        :raises ServiceNotProvidedError: 方法不在目标模块的 ``services`` 白名单内（或为私有方法 / 不存在）
        :raises ModuleCallError: 调用方被 scope 出站规则拒绝
        :raises ModuleCallTimeoutError: 协程方法超时

        :example:
        >>> result = await sdk.module.call("Chat", "get_history", session_id, n=20)

        {!--< tips >!--}
        服务方在 ``get_meta().services`` 声明契约收紧调用面（缺省时公开方法全开放）::

            class ChatModule(BaseModule):
                @staticmethod
                def get_meta() -> ModuleMeta:
                    return ModuleMeta(services=["get_history", "translate"])

                async def get_history(self, session_id, n=20): ...
        {!--< /tips >!--}
        """
        if timeout is None:
            from .constants import DEFAULT_MODULE_CALL_TIMEOUT_SECS

            timeout = DEFAULT_MODULE_CALL_TIMEOUT_SECS

        # scope 出站审计（调用方维度：actions.<caller>.call，name=<module>.<method>）
        caller = current_owner.get()
        if caller:
            from .scope import scope as _scope

            if not _scope.is_action_allowed(caller, "call", name=f"{module_name}.{method}"):
                logger.trace(
                    i18n.t(
                        "core.module.call_denied",
                        caller=caller,
                        module=module_name,
                        method=method,
                    )
                )
                raise ModuleCallError(
                    module_name,
                    method,
                    i18n.t(
                        "core.module.call_denied",
                        caller=caller,
                        module=module_name,
                        method=method,
                    ),
                )

        instance = await self._resolve_call_target(module_name)

        # 契约检查：meta.services 白名单收紧；未声明时允许公开方法、始终禁私有
        provides = self._service_names(module_name)
        if method.startswith("_") or (provides is not None and method not in provides):
            raise ServiceNotProvidedError(
                module_name, method, i18n.t("core.module.call_not_provided", module=module_name, method=method)
            )

        func = getattr(instance, method, None)
        if func is None or not callable(func):
            raise ServiceNotProvidedError(
                module_name, method, i18n.t("core.module.call_method_missing", module=module_name, method=method)
            )

        # 执行：owner 归因到目标模块（与命令执行语义一致——执行谁的代码归因谁），
        # 调用方身份保留在 current_caller，供被调方识别调用来源
        # （同时记录活跃时间戳：休眠清扫判定）
        self._module_activity[module_name] = time.monotonic()
        owner_token = current_owner.set(module_name)
        caller_token = current_caller.set(caller)
        try:
            result = func(*args, **kwargs)
            if inspect.iscoroutine(result):
                try:
                    return await asyncio.wait_for(result, timeout=timeout)
                except asyncio.TimeoutError:
                    raise ModuleCallTimeoutError(
                        module_name,
                        method,
                        i18n.t("core.module.call_timeout", module=module_name, method=method, timeout=timeout),
                        timeout=timeout,
                    ) from None
            return result
        finally:
            current_owner.reset(owner_token)
            current_caller.reset(caller_token)

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
