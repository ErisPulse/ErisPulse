"""
ErisPulse 模块加载器

专门用于从 PyPI 包加载和初始化普通模块

{!--< tips >!--}
1. 模块必须通过 entry-points 机制注册到 erispulse.module 组
2. 模块类名应与 entry-point 名称一致
3. 模块支持懒加载机制
{!--< /tips >!--}
"""

import asyncio
import importlib.metadata
import inspect
import re
import sys
import threading
import weakref
from typing import TYPE_CHECKING, Any, cast

from ..Core.constants import ACTIVATION_STUB_PRIORITY, MODULE_ENTRY_POINT_GROUP
from ..Core.i18n import i18n
from ..Core.lifecycle import lifecycle
from ..Core.logger import logger
from ..finders import ModuleFinder
from .bases.loader import BaseLoader

if TYPE_CHECKING:
    pass

# SDK 保留属性名，禁止模块覆盖
_RESERVED_SDK_ATTRS = frozenset(
    {
        # Python 内部属性
        "__class__",
        "__dict__",
        "__init__",
        "__setattr__",
        "__getattr__",
        "__delattr__",
        "__getattribute__",
        "__repr__",
        "__str__",
        "__dir__",
        "__new__",
        "__doc__",
        "__module__",
        "__slots__",
        "__weakref__",
        # SDK 核心属性
        "Event",
        "lifecycle",
        "logger",
        "storage",
        "env",
        "config",
        "adapter",
        "module",
        "router",
        "client",
        "scope",
        "context",
        "BaseAdapter",
        "SendDSL",
        "BaseStorage",
        "BaseQueryBuilder",
        # SDK 实例内部属性
        "_initializer",
        "_initialized",
        "init",
        "init_sync",
        "init_task",
        "load_module",
        "run",
        "restart",
        "hard_restart",
        "uninit",
        "RESTART_EXIT_CODE",
        "_CORE_ATTR_NAMES",
    }
)

# 入口点名称合法模式
_SAFE_ENTRY_POINT_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


def _validate_sdk_attr_name(name: str) -> bool:
    """
    {!--< internal-use >!--}
    验证模块名称是否可以安全地作为 SDK 属性挂载

    :param name: 模块名称（entry-point name）
    :return: True 如果名称安全，False 如果应拒绝
    """
    if not name or not _SAFE_ENTRY_POINT_NAME_RE.match(name):
        logger.error(i18n.t("loader.module.invalid_identifier", name=name))
        return False
    if name.startswith("_"):
        logger.error(i18n.t("loader.module.invalid_name", name=name))
        return False
    if name in _RESERVED_SDK_ATTRS:
        logger.error(i18n.t("loader.module.reserved_name", name=name))
        return False
    return True


class ModuleLoader(BaseLoader):
    """
    模块加载器

    负责从 PyPI entry-points 加载模块，支持懒加载

    {!--< tips >!--}
    使用方式：
    >>> loader = ModuleLoader()
    >>> module_objs, enabled, disabled = await loader.load(module_manager)
    {!--< /tips >!--}
    """

    def __init__(self):
        """初始化模块加载器"""
        super().__init__("ErisPulse.modules")
        self._finder = ModuleFinder()
        # 本地插件文件夹加载器（复用实例便于热重载查询路径）
        from .plugin_folder import PluginFolderLoader

        self._plugin_loader = PluginFolderLoader()
        self._last_module_objs: dict[str, Any] = {}

    def _get_entry_point_group(self) -> str:
        """
        获取 entry-point 组名

        :return: 入口点组名字符串
        """
        return MODULE_ENTRY_POINT_GROUP

    async def load(
        self, manager_instance: Any
    ) -> tuple[dict[str, Any], list[str], list[str]]:
        """
        从 entry-points 加载对象（使用 ModuleFinder）

        :param manager_instance: 管理器实例
        :return:
            dict[str, Any]: 对象字典
            list[str]: 启用列表
            list[str]: 禁用列表

        :raises ImportError: 当加载失败时抛出
        """
        objs: dict[str, Any] = {}
        enabled_list: list[str] = []
        disabled_list: list[str] = []

        group_name = self._get_entry_point_group()

        try:
            # 使用 ModuleFinder 查找 entry-points
            if entries := self._finder.find_all():
                logger.print_info(
                    i18n.t("loader.module.discovered", count=len(entries)), level=1
                )
            elif self._finder.last_error:
                logger.print_info(
                    i18n.t(
                        "loader.module.discovery_failed",
                        error=self._finder.last_error,
                    ),
                    level=1,
                )
            else:
                logger.print_info(i18n.t("loader.module.none"), level=1)

            # 处理每个 entry-point
            for entry_point in entries:
                (
                    objs,
                    enabled_list,
                    disabled_list,
                    _is_new,
                ) = await self._process_entry_point(
                    entry_point, objs, enabled_list, disabled_list, manager_instance
                )

            # 本地插件文件夹：发现后并入结果，本地优先（同名覆盖 entry-point）
            self._merge_plugin_folder(objs, enabled_list, disabled_list, manager_instance)

            logger.print_section_separator()

        except SystemExit as e:
            logger.error(
                i18n.t(
                    "loader.module.systemexit_group",
                    group=group_name,
                    code=e.code,
                )
            )
        except Exception as e:
            logger.error(i18n.t("loader.module.load_failed", group=group_name, error=e))

        # 保留最近一次加载结果快照（插件热重载 / 增量重扫需要）
        self._last_module_objs = objs

        return objs, enabled_list, disabled_list

    def _merge_plugin_folder(
        self,
        objs: dict[str, Any],
        enabled_list: list[str],
        disabled_list: list[str],
        manager_instance: Any,
    ) -> None:
        """
        {!--< internal-use >!--}
        发现本地插件文件夹并并入加载结果

        本地插件优先：与 entry-point 模块同名时，本地插件覆盖安装包条目
        （便于本地覆盖调试）。启用状态沿用 ``ErisPulse.modules.status``。

        :param objs: 模块对象字典（原地修改）
        :param enabled_list: 启用列表（原地修改）
        :param disabled_list: 禁用列表（原地修改）
        :param manager_instance: 模块管理器实例
        """
        try:
            plugin_objs = self._plugin_loader.discover()
        except Exception as e:
            logger.error(i18n.t("loader.plugin.discovery_failed", error=e))
            return

        for plugin_name, plugin_module in plugin_objs.items():
            # 与 entry-point 一致：新模块写入启用状态配置
            if not manager_instance.exists(plugin_name):
                manager_instance._config_register(plugin_name)

            if not manager_instance.is_enabled(plugin_name):
                # 被禁用的本地插件：若覆盖了 entry-point 同名模块则一并移除
                if plugin_name in objs:
                    del objs[plugin_name]
                    if plugin_name in enabled_list:
                        enabled_list.remove(plugin_name)
                if plugin_name not in disabled_list:
                    disabled_list.append(plugin_name)
                continue

            # 本地优先：同名覆盖 entry-point
            if plugin_name in objs:
                logger.warning(
                    i18n.t("loader.plugin.override", name=plugin_name)
                )

            objs[plugin_name] = plugin_module
            if plugin_name not in enabled_list:
                enabled_list.append(plugin_name)
            if plugin_name in disabled_list:
                disabled_list.remove(plugin_name)

    async def reload_plugin(self, plugin_name: str, manager_instance: Any, sdk_instance: Any) -> bool:
        """
        热重载单个本地插件：卸载旧实例 → 清理注册 → 重新导入 → 重新注册并加载

        :param plugin_name: 插件名
        :param manager_instance: 模块管理器实例
        :param sdk_instance: SDK 实例
        :return: 是否重载成功

        {!--< tips >!--}
        仅适用于插件文件夹来源的插件（moduleInfo meta 的 source 为
        ``plugin_folder``）。PyPI 安装包模块不支持热重载。
        {!--< /tips >!--}
        """
        old_obj = self._last_module_objs.get(plugin_name)
        if old_obj is None:
            logger.warning(
                i18n.t("loader.plugin.reload_unknown", name=plugin_name)
            )
            return False

        meta = old_obj.moduleInfo.get("meta", {})
        if meta.get("source") != "plugin_folder":
            logger.warning(
                i18n.t("loader.plugin.reload_not_plugin", name=plugin_name)
            )
            return False

        # 1. 卸载旧实例（触发 on_unload）
        try:
            await manager_instance.unload(plugin_name)
        except Exception as e:
            logger.error(i18n.t("loader.plugin.reload_unload_failed", name=plugin_name, error=e))

        # 2. 清理注册（类 / info / 懒加载代理）
        try:
            manager_instance.unregister(plugin_name)
        except Exception:
            pass

        # 移除 SDK 上挂载的属性
        if hasattr(sdk_instance, plugin_name):
            try:
                delattr(sdk_instance, plugin_name)
            except Exception:
                pass

        # 3. 清理已导入的插件模块，强制重新导入
        self._purge_plugin_modules(plugin_name)

        # 4. 重新发现并加载该插件
        try:
            plugin_objs = self._plugin_loader.discover()
        except Exception as e:
            logger.error(i18n.t("loader.plugin.discovery_failed", error=e))
            return False

        new_module = plugin_objs.get(plugin_name)
        if new_module is None:
            # 插件被删除：确认从快照与配置中移除
            self._last_module_objs.pop(plugin_name, None)
            logger.info(i18n.t("loader.plugin.reload_removed", name=plugin_name))
            return True

        # 5. 重新注册并加载
        new_meta_name = new_module.moduleInfo["meta"]["name"]
        try:
            manager_instance.register(new_meta_name, new_module.moduleInfo["module_class"], new_module.moduleInfo)
        except Exception as e:
            logger.error(i18n.t("loader.plugin.register_failed", name=plugin_name, error=e))
            return False

        loaded = await manager_instance.load(new_meta_name)
        if not loaded:
            logger.error(i18n.t("loader.plugin.load_failed", name=plugin_name, error="load returned False"))
            return False

        setattr(sdk_instance, new_meta_name, manager_instance.get(new_meta_name))
        self._last_module_objs[plugin_name] = new_module
        logger.info(i18n.t("loader.plugin.reload_ok", name=plugin_name))
        return True

    def _purge_plugin_modules(self, plugin_name: str) -> None:
        """
        {!--< internal-use >!--}
        从 sys.modules 移除插件相关模块，强制下次导入重新执行

        :param plugin_name: 插件名
        """
        # 单文件插件：sys.modules[plugin_name]
        sys.modules.pop(plugin_name, None)
        # 包形式插件：子模块（如 weather.Core）
        for mod_name in list(sys.modules):
            if mod_name == plugin_name or mod_name.startswith(f"{plugin_name}."):
                sys.modules.pop(mod_name, None)
        # 刷新加载器路径记录，使 discover() 重新导入
        self._plugin_loader._loaded_paths.pop(plugin_name, None)

    async def _process_entry_point(
        self,
        entry_point: Any,
        objs: dict[str, Any],
        enabled_list: list[str],
        disabled_list: list[str],
        manager_instance: Any,
    ) -> tuple[dict[str, Any], list[str], list[str], bool]:
        """
        处理单个模块 entry-point

        :param entry_point: entry-point 对象
        :param objs: 模块对象字典
        :param enabled_list: 启用的模块列表
        :param disabled_list: 停用的模块列表
        :param manager_instance: 模块管理器实例

        :return:
            dict[str, Any]: 更新后的模块对象字典
            list[str]: 更新后的启用模块列表
            list[str]: 更新后的禁用模块列表
            bool: 是否为新模块

        :raises ImportError: 当模块加载失败时抛出
        """
        meta_name = entry_point.name
        is_new = False

        # 检查模块是否已经注册，如果未注册则进行注册（默认启用）
        if not manager_instance.exists(meta_name):
            manager_instance._config_register(meta_name)
            is_new = True

        # 获取模块当前状态
        if not manager_instance.is_enabled(meta_name):
            disabled_list.append(meta_name)
            return objs, enabled_list, disabled_list, is_new

        try:
            loaded_obj = entry_point.load()
            module_obj = sys.modules[loaded_obj.__module__]
            dist = (
                importlib.metadata.distribution(entry_point.dist.name)
                if entry_point.dist
                else None
            )

            # 检查模块是否继承自 BaseModule
            from ..Core.Bases.module import BaseModule

            is_base_module = inspect.isclass(loaded_obj) and issubclass(
                loaded_obj, BaseModule
            )

            if not is_base_module:
                # 严格模式：按级别决定容忍加载或拒绝（跳过）
                if self._strict().decide(meta_name, "module", "not_base_class"):
                    return objs, enabled_list, disabled_list, is_new

            # 获取模块加载策略
            strategy = self._get_load_strategy(loaded_obj)
            lazy_load = self._extract_strategy_value(strategy, "lazy_load", True)
            priority = self._extract_strategy_value(strategy, "priority", 0)

            top_level = []
            if entry_point.dist:
                top_level = self._finder.get_top_level_modules(entry_point.dist.name)

            module_info = {
                "meta": {
                    "name": meta_name,
                    "version": getattr(
                        module_obj, "__version__", dist.version if dist else "1.0.0"
                    ),
                    "description": getattr(module_obj, "__description__", ""),
                    "author": getattr(module_obj, "__author__", ""),
                    "license": getattr(module_obj, "__license__", ""),
                    "package": entry_point.dist.name if entry_point.dist else None,
                    "lazy_load": lazy_load,
                    "priority": priority,
                    "is_base_module": is_base_module,
                    "top_level": top_level,
                },
                "module_class": loaded_obj,
                "strategy": strategy,
            }

            cast("Any", module_obj).moduleInfo = module_info

            objs[meta_name] = module_obj
            enabled_list.append(meta_name)

        except SystemExit as e:
            self._strict().record_failure(
                meta_name, "module", "systemexit", detail=f"SystemExit({e.code})"
            )
            logger.error(
                i18n.t(
                    "loader.module.systemexit_single",
                    name=meta_name,
                    code=e.code,
                )
            )
        except Exception as e:
            self._strict().record_failure(
                meta_name, "module", "load_failed", detail=str(e)
            )
            logger.error(
                i18n.t("loader.module.load_single_failed", name=meta_name, error=e)
            )
            from ..runtime.diagnostics import log_diagnostic

            log_diagnostic(e, hint_key="loader.module.diag_hint")

        return objs, enabled_list, disabled_list, is_new

    def _extract_strategy_value(self, strategy: Any, key: str, default: Any) -> Any:
        """
        从策略对象或字典中提取值

        :param strategy: 策略对象（dict 或 ModuleLoadStrategy）
        :param key: 键名
        :param default: 默认值
        :return: 提取到的值或默认值

        {!--< internal-use >!--}
        内部方法，统一处理 dict 和 ModuleLoadStrategy 两种策略类型
        {!--< /internal-use >!--}
        """
        if isinstance(strategy, dict):
            return strategy.get(key, default)
        if hasattr(strategy, "_data"):
            return strategy._data.get(key, default)
        return default

    def _get_global_lazy_loading(self) -> bool:
        """
        获取全局懒加载配置

        :return: 是否启用懒加载（默认 True）

        {!--< internal-use >!--}
        内部方法，用于获取全局懒加载配置
        {!--< /internal-use >!--}
        """
        try:
            from ..runtime import get_framework_config

            framework_config = get_framework_config()
            return framework_config.get("enable_lazy_loading", True)
        except Exception as e:
            logger.debug(i18n.t("loader.module.config_failed", error=e))
            return True

    def _resolve_strategy(self, module_class: type) -> Any:
        """
        按优先级从模块类解析加载策略

        优先级：should_eager_load()（旧版兼容） → get_load_strategy()

        :param module_class: 模块类
        :return: 策略对象或 None

        {!--< internal-use >!--}
        内部方法，用于解析模块的加载策略
        {!--< /internal-use >!--}
        """
        # 优先检查旧方法 should_eager_load()
        if hasattr(module_class, "should_eager_load"):
            try:
                eager_load = module_class.should_eager_load()
                return {"lazy_load": not eager_load, "priority": 0}
            except Exception as e:
                logger.warning(
                    i18n.t(
                        "loader.module.strategy_failed",
                        method="should_eager_load",
                        name=module_class.__name__,
                        error=e,
                    )
                )

        # 检查新方法 get_load_strategy()
        if hasattr(module_class, "get_load_strategy"):
            try:
                return module_class.get_load_strategy()
            except Exception as e:
                logger.warning(
                    i18n.t(
                        "loader.module.strategy_failed",
                        method="get_load_strategy",
                        name=module_class.__name__,
                        error=e,
                    )
                )

        return None

    def _apply_global_lazy_loading(self, strategy: Any, lazy_load: bool) -> Any:
        """
        应用全局懒加载配置到策略

        :param strategy: 原始策略
        :param lazy_load: 懒加载值
        :return: 修改后的策略

        {!--< internal-use >!--}
        内部方法，用于应用全局配置覆盖
        {!--< /internal-use >!--}
        """
        if isinstance(strategy, dict):
            return dict(strategy, lazy_load=lazy_load)
        if hasattr(strategy, "_data"):
            from .strategy import ModuleLoadStrategy

            data = dict(strategy._data)
            data["lazy_load"] = lazy_load
            return ModuleLoadStrategy(**data)
        return strategy

    def _get_load_strategy(self, module_class: type) -> Any:
        """
        获取模块加载策略

        优先级：
        1. 模块的 should_eager_load() 方法（旧版兼容）
        2. 模块的 get_load_strategy() 方法
        3. 全局配置
        4. 默认策略

        全局配置会覆盖模块策略中的 lazy_load 设置

        :param module_class: Type 模块类
        :return: 加载策略对象或字典

        {!--< internal-use >!--}
        内部方法，用于获取模块的加载策略
        {!--< /internal-use >!--}
        """
        global_lazy_loading = self._get_global_lazy_loading()
        strategy = self._resolve_strategy(module_class)

        # 全局配置覆盖策略中的 lazy_load 设置
        if strategy is not None and not global_lazy_loading:
            strategy = self._apply_global_lazy_loading(strategy, False)

        return (
            strategy
            if strategy is not None
            else {"lazy_load": global_lazy_loading, "priority": 0}
        )

    async def register_to_manager(
        self, modules: list[str], module_objs: dict[str, Any], manager_instance: Any
    ) -> bool:
        """
        将模块类注册到管理器

        :param modules: 模块名称列表
        :param module_objs: 模块对象字典
        :param manager_instance: 模块管理器实例
        :return: 模块注册是否成功

        {!--< tips >!--}
        此方法由初始化协调器调用，仅注册模块类，不进行实例化
        {!--< /tips >!--}
        """
        register_tasks = []

        for module_name in modules:
            module_obj = module_objs[module_name]
            meta_name = module_obj.moduleInfo["meta"]["name"]
            module_class = module_obj.moduleInfo.get("module_class")

            async def register_module(name: str, obj: Any, cls: Any) -> bool:
                """注册单个模块"""
                try:
                    if cls is not None:
                        manager_instance.register(name, cls, obj.moduleInfo)
                        return True
                    if entry_point := self._finder.find_by_name(name):
                        module_class = entry_point.load()
                        manager_instance.register(name, module_class, obj.moduleInfo)
                        return True
                    return False
                except SystemExit as e:
                    self._strict().record_failure(
                        name,
                        "module",
                        "register_systemexit",
                        detail=f"SystemExit({e.code})",
                    )
                    logger.error(
                        i18n.t(
                            "loader.module.systemexit_single",
                            name=name,
                            code=e.code,
                        )
                    )
                    return False
                except Exception as e:
                    self._strict().record_failure(
                        name, "module", "register_failed", detail=str(e)
                    )
                    logger.error(
                        i18n.t("loader.module.register_failed", name=name, error=e)
                    )
                    return False

            register_tasks.append(register_module(meta_name, module_obj, module_class))

        # 等待所有注册任务完成
        register_results = await asyncio.gather(*register_tasks, return_exceptions=True)

        # 记录失败的模块并从列表中移除
        failed_modules = []
        for i, result in enumerate(register_results):
            module_name = modules[i]
            if isinstance(result, BaseException) or result is False:
                logger.warning(
                    i18n.t("loader.module.register_skipped", name=module_name)
                )
                failed_modules.append(module_name)

        for name in failed_modules:
            if name in modules:
                modules.remove(name)

        return True

    def _validate_dependencies(self, modules: list, module_objs: dict) -> dict:
        """
        验证所有模块的依赖是否满足

        :param modules: list 模块名称列表
        :param module_objs: dict 模块对象字典
        :return: dict 缺少依赖的模块映射 {模块名: [缺少的依赖列表]}

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        registered_names = set()
        for name in modules:
            meta = module_objs[name].moduleInfo["meta"]
            registered_names.add(meta["name"])

        missing = {}
        for name in modules:
            meta = module_objs[name].moduleInfo["meta"]
            meta_name = meta["name"]
            depends = meta.get("depends", [])
            if depends:
                unsatisfied = [d for d in depends if d not in registered_names]
                if unsatisfied:
                    missing[meta_name] = unsatisfied
        return missing

    def _topological_sort(self, modules: list, module_objs: dict) -> list:
        """
        基于依赖关系和优先级的拓扑排序

        :param modules: list 模块名称列表
        :param module_objs: dict 模块对象字典
        :return: list 排序后的模块 meta_name 列表

        :raises RuntimeError: 当检测到循环依赖时

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        meta_map = {}
        for name in modules:
            meta = module_objs[name].moduleInfo["meta"]
            meta_name = meta["name"]
            meta_map[meta_name] = meta

        all_names = set(meta_map.keys())
        graph = {}
        reverse_graph: dict[str, list[str]] = {name: [] for name in all_names}
        for name, meta in meta_map.items():
            deps = meta.get("depends", [])
            graph[name] = {d for d in deps if d in all_names}
            for dep in graph[name]:
                reverse_graph[dep].append(name)

        in_degree = {name: len(deps) for name, deps in graph.items()}
        queue = [name for name, deg in in_degree.items() if deg == 0]
        sorted_list = []

        while queue:
            queue.sort(
                key=lambda n: meta_map[n].get("priority", 0),
                reverse=True,
            )
            current = queue.pop(0)
            sorted_list.append(current)

            for name in reverse_graph[current]:
                in_degree[name] -= 1
                if in_degree[name] == 0:
                    queue.append(name)

        if len(sorted_list) != len(all_names):
            remaining = all_names - set(sorted_list)
            remaining_deps = {n: graph[n] & remaining for n in remaining}
            raise RuntimeError(i18n.t("core.module.circular_dependency", deps=remaining_deps))

        return sorted_list

    async def initialize_modules(
        self,
        modules: list[str],
        module_objs: dict[str, Any],
        manager_instance: Any,
        sdk_instance: Any,
    ) -> bool:
        """
        初始化模块（创建实例并挂载到 SDK）

        :param modules: 模块名称列表
        :param module_objs: 模块对象字典
        :param manager_instance: 模块管理器实例
        :param sdk_instance: SDK 实例
        :return: 模块初始化是否成功

        {!--< tips >!--}
        此方法处理模块的实际初始化和挂载
        支持模块间依赖声明和拓扑排序加载
        {!--< /tips >!--}
        """
        missing = self._validate_dependencies(modules, module_objs)
        if missing:
            for name, deps in missing.items():
                logger.warning(
                    i18n.t("loader.module.missing_deps", name=name, deps=deps)
                )

        skip_set = set()
        for name in modules:
            meta_name = module_objs[name].moduleInfo["meta"]["name"]
            if meta_name in missing:
                skip_set.add(name)
        valid_modules = [m for m in modules if m not in skip_set]

        try:
            sorted_meta_names = self._topological_sort(valid_modules, module_objs)
        except RuntimeError as e:
            logger.error(str(e))
            sorted_meta_names = [
                module_objs[m].moduleInfo["meta"]["name"] for m in valid_modules
            ]

        name_to_entry = {}
        for name in valid_modules:
            meta_name = module_objs[name].moduleInfo["meta"]["name"]
            name_to_entry[meta_name] = name

        for meta_name in sorted_meta_names:
            entry_name = name_to_entry[meta_name]

            # 安全校验：防止模块名称覆盖 SDK 关键属性
            if not _validate_sdk_attr_name(meta_name):
                logger.warning(i18n.t("loader.module.skip_invalid", name=meta_name))
                continue

            try:
                module_obj = module_objs[entry_name]
                meta = module_obj.moduleInfo["meta"]
                lazy_load = meta.get("lazy_load", True)

                if lazy_load:
                    strategy = module_obj.moduleInfo.get("strategy")
                    activate_on = self._extract_strategy_value(
                        strategy, "activate_on", None
                    )
                    if activate_on:
                        lazy_module = ModuleActivator(
                            meta_name,
                            module_obj.moduleInfo["module_class"],
                            sdk_instance,
                            module_obj.moduleInfo,
                            manager_instance,
                            activate_on=activate_on,
                        )
                        logger.trace(
                            i18n.t(
                                "loader.module.mount_activator",
                                name=meta_name,
                            )
                        )
                    else:
                        lazy_module = LazyModule(
                            meta_name,
                            module_obj.moduleInfo["module_class"],
                            sdk_instance,
                            module_obj.moduleInfo,
                            manager_instance,
                        )
                        logger.trace(i18n.t("loader.module.mount_lazy", name=meta_name))
                    setattr(sdk_instance, meta_name, lazy_module)
                    # 同步注册懒加载代理到管理器，使 module.get() 对未加载模块返回代理（透明懒加载）
                    manager_instance.register_lazy(meta_name, lazy_module)
                else:
                    result = await manager_instance.load(meta_name)
                    if result:
                        setattr(
                            sdk_instance, meta_name, manager_instance.get(meta_name)
                        )
                        logger.trace(
                            i18n.t("loader.module.mount_eager", name=meta_name)
                        )
                    else:
                        logger.warning(
                            i18n.t(
                                "loader.module.immediate_load_failed", name=meta_name
                            )
                        )
            except SystemExit as e:
                self._strict().record_failure(
                    meta_name,
                    "module",
                    "init_systemexit",
                    detail=f"SystemExit({e.code})",
                )
                logger.warning(
                    i18n.t(
                        "loader.module.systemexit_single",
                        name=meta_name,
                        code=e.code,
                    )
                )
            except Exception as e:
                self._strict().record_failure(
                    meta_name, "module", "init_failed", detail=str(e)
                )
                logger.warning(
                    i18n.t("loader.module.init_failed", name=meta_name, error=e)
                )
                from ..runtime.diagnostics import log_diagnostic

                log_diagnostic(e, hint_key="loader.module.diag_hint")

        return True


class LazyModule:
    """
    懒加载模块包装器

    当模块第一次被访问时才进行实例化

    {!--< tips >!--}
    1. 模块的实际实例化会在第一次属性访问时进行
    2. 依赖模块会在被使用时自动初始化
    3. 对于继承自 BaseModule 的模块，会自动调用生命周期方法
    {!--< /tips >!--}
    """

    # 使用 __slots__ 减少每个实例的内存占用（避免 __dict__）
    # 同时配合 _sdk_ref 的 weakref 设计，避免 SDK <-> LazyModule 循环引用
    # 从而减少分代 GC 的循环检测压力
    __slots__ = (
        "__weakref__",
        "_init_failed",
        "_init_needs_sdk",
        "_initialized",
        "_instance",
        "_is_base_module",
        "_manager_instance",
        "_module_class",
        "_module_info",
        "_module_name",
        "_needs_async_init",
        "_sdk_ref",
        "moduleInfo",
    )

    def __init__(
        self,
        module_name: str,
        module_class: type,
        sdk_ref: Any,
        module_info: dict[str, Any],
        manager_instance: Any,
    ) -> None:
        """
        初始化懒加载包装器

        :param module_name: str 模块名称
        :param module_class: Type 模块类
        :param sdk_ref: Any SDK 引用
        :param module_info: dict[str, Any] 模块信息字典
        :param manager_instance: 模块管理器实例
        """
        object.__setattr__(self, "_module_name", module_name)
        object.__setattr__(self, "_module_class", module_class)
        # SDK 对本包装器持有强引用（setattr 到 SDK 实例上），
        # 此处使用 weakref 反向引用 SDK，打破 SDK <-> LazyModule 的循环引用，
        # 避免触发 CPython 的循环引用检测（分代 GC 全量扫描）
        object.__setattr__(self, "_sdk_ref", weakref.ref(sdk_ref))
        object.__setattr__(self, "_module_info", module_info)
        object.__setattr__(self, "_instance", None)
        object.__setattr__(self, "_initialized", False)
        object.__setattr__(self, "_init_failed", False)
        object.__setattr__(self, "_manager_instance", manager_instance)
        object.__setattr__(
            self,
            "_is_base_module",
            module_info.get("meta", {}).get("is_base_module", False),
        )
        # 缓存 __init__ 签名分析结果，避免每次初始化重复调用 inspect.signature
        try:
            init_params = inspect.signature(module_class.__init__).parameters
            object.__setattr__(self, "_init_needs_sdk", "sdk" in init_params)
        except (ValueError, TypeError):
            object.__setattr__(self, "_init_needs_sdk", False)
        object.__setattr__(self, "_needs_async_init", False)

    async def _initialize(self) -> None:
        """
        实际初始化模块

        :raises Exception: 当模块初始化失败时抛出

        {!--< internal-use >!--}
        内部方法，执行实际的模块初始化
        {!--< /internal-use >!--}
        """
        if object.__getattribute__(self, "_initialized"):
            return
        # 失败后不再自动重试，避免每次属性访问都触发初始化开销
        if object.__getattribute__(self, "_init_failed"):
            return

        module_name = object.__getattribute__(self, "_module_name")
        logger.debug(i18n.t("loader.module.init_lazy_start", name=module_name))

        try:
            is_base_module = object.__getattribute__(self, "_is_base_module")

            if is_base_module:
                # BaseModule: 通过 manager.load() 统一处理实例化和 on_load
                # 避免 LazyModule 自行创建实例导致双重实例化
                manager_instance = object.__getattribute__(self, "_manager_instance")
                success = await manager_instance.load(module_name)

                if not success:
                    raise RuntimeError(
                        i18n.t("core.module.manager_load_failed", name=module_name)
                    )

                # 使用 manager 中创建的实例（唯一的真实实例）
                instance = manager_instance.get(module_name)
                if instance is None:
                    raise RuntimeError(
                        i18n.t("core.module.manager_get_none", name=module_name)
                    )

                # 确保 moduleInfo 已设置
                module_info = object.__getattribute__(self, "_module_info")
                if not hasattr(instance, "moduleInfo") or instance.moduleInfo is None:
                    instance.moduleInfo = module_info

                object.__setattr__(self, "_instance", instance)
            else:
                # 非 BaseModule: 保持原有行为，LazyModule 自行实例化
                module_class = object.__getattribute__(self, "_module_class")

                if object.__getattribute__(self, "_init_needs_sdk"):
                    sdk_ref = object.__getattribute__(self, "_sdk_ref")()
                    instance = module_class(sdk_ref)
                else:
                    instance = module_class()

                instance.moduleInfo = object.__getattribute__(self, "_module_info")

                object.__setattr__(self, "_instance", instance)

            object.__setattr__(self, "_initialized", True)
            # 清除异步初始化标志：手动 await load_module 成功后恢复正常属性访问
            object.__setattr__(self, "_needs_async_init", False)

            await lifecycle.submit_event(
                "module.init",
                msg=i18n.t(
                    "loader.module.init_complete",
                    name=object.__getattribute__(self, "_module_name"),
                ),
                data={
                    "module_name": object.__getattribute__(self, "_module_name"),
                    "success": True,
                },
            )
            logger.debug(
                i18n.t(
                    "loader.module.lazy_init_done",
                    name=object.__getattribute__(self, "_module_name"),
                )
            )

        except SystemExit as e:
            module_name = object.__getattribute__(self, "_module_name")
            await lifecycle.submit_event(
                "module.init",
                msg=i18n.t("loader.module.systemexit", name=module_name),
                data={"module_name": module_name, "success": False},
            )
            logger.error(
                i18n.t(
                    "loader.module.systemexit_single",
                    name=module_name,
                    code=e.code,
                )
            )
            object.__setattr__(self, "_initialized", False)
            object.__setattr__(self, "_init_failed", True)
        except Exception as e:
            await lifecycle.submit_event(
                "module.init",
                msg=i18n.t("loader.module.init_failed_msg", error=e),
                data={
                    "module_name": object.__getattribute__(self, "_module_name"),
                    "success": False,
                },
            )
            logger.error(
                i18n.t(
                    "loader.module.lazy_init_failed",
                    name=object.__getattribute__(self, "_module_name"),
                    error=e,
                )
            )
            from ..runtime.diagnostics import log_diagnostic

            log_diagnostic(e, hint_key="loader.module.diag_hint")
            object.__setattr__(self, "_initialized", False)
            object.__setattr__(self, "_init_failed", True)

    def _ensure_initialized(self) -> None:
        """
        确保模块已初始化

        {!--< internal-use >!--}
        内部方法，检查并确保模块已初始化
        {!--< internal-use >!--}

        设计说明：
        - 支持同步/异步透明的懒加载机制，用户无需感知差异
        - BaseModule 在异步上下文中通过辅助线程完成初始化
        - BaseModule 在同步上下文中使用 asyncio.run() 确保初始化完成
        - 非 BaseModule 保持原有逻辑，支持同步初始化
        {!--< internal-use >!--}
        """
        if object.__getattribute__(self, "_initialized"):
            return
        # 已失败则不再重试，避免每次属性访问都重新进入初始化逻辑
        if object.__getattribute__(self, "_init_failed"):
            return

        try:
            loop = asyncio.get_running_loop()

            if object.__getattribute__(self, "_is_base_module"):
                if loop.is_running():
                    self._init_in_background_thread()
                else:
                    loop.run_until_complete(self._initialize())
                return

            init_method = getattr(
                object.__getattribute__(self, "_module_class"), "__init__", None
            )

            if inspect.iscoroutinefunction(init_method):
                object.__setattr__(self, "_needs_async_init", True)
                logger.warning(
                    i18n.t(
                        "loader.module.async_init_hint",
                        name=object.__getattribute__(self, "_module_name"),
                    )
                )
                return
            self._initialize_sync()
        except RuntimeError:
            asyncio.run(self._initialize())

    def _init_in_background_thread(self) -> None:
        """
        在辅助线程中运行异步初始化，当前线程同步等待完成

        {!--< internal-use >!--}
        当 _ensure_initialized 在已有事件循环中被调用时，无法使用
        run_until_complete (会死锁)。通过在新线程中创建独立的事件循环
        来运行异步初始化，同时当前线程通过 threading.Event 同步等待。
        {!--< internal-use >!--}
        """
        init_done = threading.Event()
        init_error: list[SystemExit | Exception | None] = [None]

        def _run_init():
            new_loop = asyncio.new_event_loop()
            try:
                new_loop.run_until_complete(self._initialize())
            except SystemExit as e:
                init_error[0] = e
                object.__setattr__(self, "_init_failed", True)
            except Exception as e:
                init_error[0] = e
                object.__setattr__(self, "_init_failed", True)
            finally:
                new_loop.close()
                init_done.set()

        t = threading.Thread(target=_run_init, daemon=True)
        t.start()
        init_done.wait()

        if init_error[0] is not None:
            logger.warning(
                i18n.t(
                    "loader.module.background_init_failed",
                    name=object.__getattribute__(self, "_module_name"),
                    error=init_error[0],
                )
            )

    def _initialize_sync(self) -> None:
        """
        同步初始化模块

        {!--< internal-use >!--}
        内部方法，在同步上下文中初始化模块
        {!--< /internal-use >!--}
        """
        if object.__getattribute__(self, "_initialized"):
            return
        if object.__getattribute__(self, "_init_failed"):
            return

        logger.debug(
            i18n.t(
                "loader.module.sync_init_start",
                name=object.__getattribute__(self, "_module_name"),
            )
        )

        try:
            module_class = object.__getattribute__(self, "_module_class")

            if object.__getattribute__(self, "_init_needs_sdk"):
                sdk_ref = object.__getattribute__(self, "_sdk_ref")()
                instance = module_class(sdk_ref)
            else:
                instance = module_class()

            instance.moduleInfo = object.__getattribute__(self, "_module_info")
            object.__setattr__(self, "_instance", instance)
            object.__setattr__(self, "_initialized", True)
            object.__setattr__(self, "_needs_async_init", False)

            logger.debug(
                i18n.t(
                    "loader.module.sync_init_done",
                    name=object.__getattribute__(self, "_module_name"),
                )
            )

        except SystemExit as e:
            logger.error(
                i18n.t(
                    "loader.module.systemexit_single",
                    name=object.__getattribute__(self, "_module_name"),
                    code=e.code,
                )
            )
            object.__setattr__(self, "_initialized", False)
            object.__setattr__(self, "_init_failed", True)
        except Exception as e:
            logger.error(
                i18n.t(
                    "loader.module.sync_init_failed",
                    name=object.__getattribute__(self, "_module_name"),
                    error=e,
                )
            )
            object.__setattr__(self, "_initialized", False)
            object.__setattr__(self, "_init_failed", True)

    async def _complete_async_init(self) -> None:
        """
        完成异步初始化部分

        {!--< internal-use >!--}
        内部方法，处理模块的异步初始化部分
        {!--< /internal-use >!--}
        """
        if not object.__getattribute__(self, "_initialized"):
            return

        try:
            # _initialize 已经通过 manager.load() 完成了 BaseModule 的 on_load
            # 这里只需要提交生命周期事件即可
            await lifecycle.submit_event(
                "module.init",
                msg=i18n.t(
                    "loader.module.init_complete",
                    name=object.__getattribute__(self, "_module_name"),
                ),
                data={
                    "module_name": object.__getattribute__(self, "_module_name"),
                    "success": True,
                },
            )
            logger.debug(
                i18n.t(
                    "core.loader.lazy_async_init_done",
                    name=object.__getattribute__(self, "_module_name"),
                )
            )
        except Exception as e:
            await lifecycle.submit_event(
                "module.init",
                msg=i18n.t("loader.module.init_failed_msg", error=e),
                data={
                    "module_name": object.__getattribute__(self, "_module_name"),
                    "success": False,
                },
            )
            logger.error(
                i18n.t(
                    "core.loader.lazy_async_init_failed",
                    name=object.__getattribute__(self, "_module_name"),
                    error=e,
                )
            )
            from ..runtime.diagnostics import log_diagnostic

            log_diagnostic(e, hint_key="loader.module.diag_hint")

    def __getattr__(self, name: str) -> Any:
        """
        属性访问时触发初始化（仅在 __getattribute__ 未命中时调用）

        :param name: str 属性名
        :return: Any 属性值
        """
        # 注意：不要在此处添加 logger.trace 等热路径日志。
        # __getattr__ / __getattribute__ 会在每次属性访问时触发，
        # 额外的字符串格式化与日志调用会带来明显的 CPU 与 GC 开销。
        if object.__getattribute__(self, "_needs_async_init"):
            _module_name = object.__getattribute__(self, "_module_name")
            raise RuntimeError(
                i18n.t("loader.module.needs_async_load", name=_module_name)
            )

        self._ensure_initialized()
        return getattr(object.__getattribute__(self, "_instance"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        属性设置

        :param name: str 属性名
        :param value: Any 属性值
        """
        if name.startswith("_") or name == "moduleInfo":
            object.__setattr__(self, name, value)
            return

        if not object.__getattribute__(self, "_initialized"):
            # 未初始化时不要在这里隐式吞掉值落到包装器上，避免产生意外状态
            if object.__getattribute__(self, "_init_failed"):
                raise RuntimeError(
                    i18n.t(
                        "loader.module.init_failed_attr_set",
                        name=object.__getattribute__(self, "_module_name"),
                        attr=name,
                    )
                )
            self._ensure_initialized()

        setattr(object.__getattribute__(self, "_instance"), name, value)

    def __delattr__(self, name: str) -> None:
        """
        属性删除

        :param name: str 属性名
        """
        if name.startswith("_") or name == "moduleInfo":
            object.__delattr__(self, name)
            return

        self._ensure_initialized()
        delattr(object.__getattribute__(self, "_instance"), name)

    def __getattribute__(self, name: str) -> Any:
        """
        属性访问，初始化后直接委托给实际实例

        :param name: str 属性名
        :return: Any 属性值

        {!--< internal-use >!--}
        这是极热路径（Python 内部、hasattr、repr 等都会走这里），
        因此必须保持轻量：不做日志、不做多余的属性查找。
        {!--< /internal-use >!--}
        """
        if name.startswith("_") or name == "moduleInfo":
            return object.__getattribute__(self, name)

        if not object.__getattribute__(self, "_initialized"):
            if object.__getattribute__(self, "_init_failed"):
                raise RuntimeError(
                    i18n.t(
                        "loader.module.init_failed_attr_get",
                        name=object.__getattribute__(self, "_module_name"),
                        attr=name,
                    )
                )
            self._ensure_initialized()
            # 初始化可能刚刚失败（同步路径会在 _initialize_sync 中标记），
            # 此时给出明确的 RuntimeError，避免后续回落到 AttributeError 造成困惑
            if object.__getattribute__(self, "_init_failed"):
                raise RuntimeError(
                    i18n.t(
                        "loader.module.init_failed_attr_get",
                        name=object.__getattribute__(self, "_module_name"),
                        attr=name,
                    )
                )

        instance = object.__getattribute__(self, "_instance")
        if instance is not None:
            return getattr(instance, name)
        return object.__getattribute__(self, name)

    def __dir__(self) -> list[str]:
        """
        返回模块属性列表

        :return: list[str] 属性列表
        """
        if object.__getattribute__(self, "_initialized"):
            return dir(object.__getattribute__(self, "_instance"))
        return list(object.__getattribute__(self, "_module_class").__dict__.keys())

    def __repr__(self) -> str:
        """
        返回模块表示字符串

        :return: str 表示字符串
        """
        if object.__getattribute__(self, "_initialized"):
            return repr(object.__getattribute__(self, "_instance"))
        return f"<LazyModule {object.__getattribute__(self, '_module_name')} (not initialized)>"

    def __call__(self, *args, **kwargs):
        """
        代理函数调用

        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 调用结果
        """
        self._ensure_initialized()
        instance = object.__getattribute__(self, "_instance")
        return instance(*args, **kwargs)


# ==============================================================================
# 事件驱动懒激活（activate_on）
# ==============================================================================


def parse_activate_on(activate_on: Any) -> tuple[list[tuple[str, str | None]], list[str]]:
    """
    解析 activate_on 触发器声明

    支持 str / list / dict 三种形式的自由混合：

    - ``str``：事件类型级触发，如 ``"message"``、``"notice"``
    - ``dict``：单键映射，键为事件类型或 ``command``
      - ``{"message": "private"}``：事件类型 + detail_type（消息的 detail_type 即会话类型）
      - ``{"notice": "group_member_increase"}``：事件类型 + detail_type
      - ``{"command": "roll"}``：命令名触发，值为命令名或命令名列表
    - ``list``：以上各项的混合列表

    :param activate_on: activate_on 声明值（str / dict / list）
    :return: ``(event_triggers, command_triggers)``
        - event_triggers: ``[(event_type, detail_type | None), ...]``
        - command_triggers: ``[命令名, ...]``

    :example:
    >>> event_triggers, command_triggers = parse_activate_on(
    ...     ["message", {"notice": "group_member_increase"}, {"command": "roll"}]
    ... )
    >>> event_triggers
    [('message', None), ('notice', 'group_member_increase')]
    >>> command_triggers
    ['roll']
    """
    event_triggers: list[tuple[str, str | None]] = []
    command_triggers: list[str] = []

    if activate_on is None:
        return event_triggers, command_triggers

    items = activate_on if isinstance(activate_on, list) else [activate_on]
    for item in items:
        if isinstance(item, str):
            event_triggers.append((item, None))
        elif isinstance(item, dict):
            for key, value in item.items():
                if key == "command":
                    names = value if isinstance(value, list) else [value]
                    command_triggers.extend(str(n) for n in names)
                else:
                    details = value if isinstance(value, list) else [value]
                    event_triggers.extend((key, detail) for detail in details)
        else:
            logger.warning(
                i18n.t(
                    "loader.activate.unsupported_trigger",
                    trigger=item,
                )
            )
    return event_triggers, command_triggers


class ModuleActivator(LazyModule):
    """
    事件驱动懒激活模块包装器

    在 LazyModule 基础上，通过 ``get_load_strategy()`` 中声明的 ``activate_on``
    触发器，在首个匹配事件/命令到达时自动加载模块，而非等待属性访问。

    事件触发器 stub 以 owner 身份注册到对应事件管理器（message/notice/request/meta），
    参与模块作用域过滤；命令触发器 stub 以同名占位命令注册到命令管理器。

    {!--< tips >!--}
    1. stub 带 owner 走作用域过滤：模块未对该 Bot / 会话 / 平台启用时不触发
    2. 激活成功后自动注销所有 stub，模块按普通模块继续运行
    3. 激活失败不重试，stub 一并注销，避免每次事件都重复尝试
    {!--< /tips >!--}
    """

    # 使用 __slots__ 与基类保持一致，避免引入 __dict__
    __slots__ = (
        "_activated",
        "_activation_failed",
        "_activation_lock",
        "_command_stubs",
        "_command_triggers",
        "_event_stubs",
        "_event_triggers",
    )

    def __init__(
        self,
        module_name: str,
        module_class: type,
        sdk_ref: Any,
        module_info: dict[str, Any],
        manager_instance: Any,
        *,
        activate_on: Any,
    ) -> None:
        """
        初始化事件驱动懒激活包装器

        :param module_name: str 模块名称
        :param module_class: Type 模块类
        :param sdk_ref: Any SDK 引用
        :param module_info: dict[str, Any] 模块信息字典
        :param manager_instance: 模块管理器实例
        :param activate_on: 触发器声明（str / dict / list）
        """
        super().__init__(module_name, module_class, sdk_ref, module_info, manager_instance)
        object.__setattr__(self, "_activation_lock", asyncio.Lock())
        object.__setattr__(self, "_activated", False)
        object.__setattr__(self, "_activation_failed", False)
        object.__setattr__(self, "_event_stubs", [])
        object.__setattr__(self, "_command_stubs", [])

        event_triggers, command_triggers = parse_activate_on(activate_on)
        object.__setattr__(self, "_event_triggers", event_triggers)
        object.__setattr__(self, "_command_triggers", command_triggers)

        self._register_stubs()

    # ------------------------------------------------------------------
    # stub 注册
    # ------------------------------------------------------------------

    def _register_stubs(self) -> None:
        """注册事件与命令触发器 stub"""
        from ..Core.Event import message, meta, notice, request
        from ..runtime.context import owner_scope

        managers = {
            "message": message,
            "notice": notice,
            "request": request,
            "meta": meta,
        }

        module_name = object.__getattribute__(self, "_module_name")

        # 事件触发器：注册到对应事件管理器的 BaseEventHandler
        for event_type, detail_type in object.__getattribute__(self, "_event_triggers"):
            manager = managers.get(event_type)
            if manager is None:
                logger.warning(
                    i18n.t(
                        "loader.activate.unsupported_event_type",
                        event_type=event_type,
                        module=module_name,
                    )
                )
                continue

            event_handler = manager.handler
            condition = (
                (lambda e, dt=detail_type: e.get("detail_type") == dt)
                if detail_type
                else None
            )

            async def _stub_event(event: Any, _handler=event_handler) -> None:
                await self._activate_and_forward(_handler, event)

            with owner_scope(module_name):
                event_handler.register(
                    _stub_event,
                    priority=ACTIVATION_STUB_PRIORITY,
                    condition=condition,
                )
            self._event_stubs.append((event_handler, _stub_event))

        # 命令触发器：注册同名占位命令（hidden）
        for cmd_name in object.__getattribute__(self, "_command_triggers"):
            async def _stub_command(event: Any, _name=cmd_name) -> None:
                await self._activate_and_forward_command(_name, event)

            from ..Core.Event.command import command

            with owner_scope(module_name):
                command(cmd_name, hidden=True)(_stub_command)
            self._command_stubs.append(_stub_command)

    # ------------------------------------------------------------------
    # 激活流程
    # ------------------------------------------------------------------

    async def _activate(self) -> bool:
        """
        激活模块

        :return: bool 是否激活成功
        """
        if object.__getattribute__(self, "_activated"):
            return True
        async with object.__getattribute__(self, "_activation_lock"):
            if object.__getattribute__(self, "_activated"):
                return True
            await self._initialize()
            if object.__getattribute__(self, "_initialized"):
                object.__setattr__(self, "_activated", True)
                # 成功：注销所有 stub，避免转发时把 stub 自身当作目标递归
                self._deregister_stubs()
                return True
            # 失败不重试：注销 stub，避免后续事件重复尝试
            object.__setattr__(self, "_activation_failed", True)
            self._deregister_stubs()
            logger.error(
                i18n.t(
                    "loader.activate.activation_failed",
                    name=object.__getattribute__(self, "_module_name"),
                )
            )
            return False

    def _deregister_stubs(self) -> None:
        """注销所有触发器 stub"""
        from ..Core.Event.command import command

        for event_handler, stub in object.__getattribute__(self, "_event_stubs"):
            try:
                event_handler.unregister(stub)
            except Exception:
                pass
        for stub in object.__getattribute__(self, "_command_stubs"):
            try:
                command.unregister(stub)
            except Exception:
                pass
        self._event_stubs.clear()
        self._command_stubs.clear()

    # ------------------------------------------------------------------
    # 事件转发
    # ------------------------------------------------------------------

    async def _activate_and_forward(self, event_handler: Any, event: Any) -> None:
        """
        激活模块并把首个匹配事件转发给该模块的真实处理器

        :param event_handler: 事件管理器（BaseEventHandler）
        :param event: 触发事件
        """
        if not await self._activate():
            return
        await self._forward_event(event_handler, event)

    async def _forward_event(self, event_handler: Any, event: Any) -> None:
        """
        定向转发事件给本模块在事件管理器中注册的真实处理器

        按优先级降序逐个调用（stub 本身已注销，不会重复触发）

        :param event_handler: 事件管理器（BaseEventHandler）
        :param event: 事件数据
        """
        from ..Core.Event.base import _invoke_handler

        module_name = object.__getattribute__(self, "_module_name")
        targets = [
            h
            for h in event_handler.handlers
            if h.get("owner") == module_name
            and (not h.get("condition") or h["condition"](event))
        ]
        targets.sort(key=lambda h: h["priority"], reverse=True)

        for h in targets:
            if event.is_stopped():
                break
            await _invoke_handler(h, event)

    # ------------------------------------------------------------------
    # 命令转发
    # ------------------------------------------------------------------

    async def _activate_and_forward_command(self, cmd_name: str, event: Any) -> None:
        """
        激活模块并重跑命令匹配，使真实命令（已注册）接管本次触发

        命令 stub 已被占位匹配并认领事件，需清空认领标记后重新进入命令分发

        :param cmd_name: 命令名
        :param event: 消息事件
        """
        if not await self._activate():
            return

        # 清空 stub 匹配产生的认领标记，重新走完整命令分发
        event["_processed"] = False
        event["_propagation_stopped"] = False

        from ..Core.Event.command import command

        await command._handle_message(event)
