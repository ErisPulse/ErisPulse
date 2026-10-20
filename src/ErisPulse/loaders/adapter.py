"""
ErisPulse 适配器加载器

从 PyPI entry-points 与本地插件文件夹加载和初始化适配器

{!--< tips >!--}
1. 适配器必须通过 entry-points 机制注册到 erispulse.adapter 组，
   或放入本地插件目录（默认 ``plugins/``，经 ``discover_adapters`` 发现）
2. 适配器类必须继承 BaseAdapter
3. 适配器不适用懒加载
{!--< /tips >!--}
"""

import asyncio
import inspect
import sys
from dataclasses import dataclass, field
from typing import Any, cast

from ..Core.constants import (
    ADAPTER_ENTRY_POINT_GROUP,
    ADAPTER_SOURCE_PLUGIN_FOLDER,
    MODULE_RELOAD_PRECHECK_MAX_FILES,
)
from ..Core.i18n import i18n
from ..Core.lifecycle import lifecycle
from ..Core.logger import logger
from ..finders import AdapterFinder
from .bases.loader import BaseLoader, resolve_min_sdk_version


@dataclass
class _AdapterReloadSnapshot:
    """
    {!--< internal-use >!--}
    适配器热重载回滚快照（引用级别）

    记录重载前与目标适配器相关的全部注册状态：adapterInfo（含类引用）、
    实例、启动态、启动任务、bots 记录与将被清除的 ``sys.modules`` 条目。
    任一重载步骤失败时按序恢复，旧适配器继续服务。

    尽力而为语义：unload 已执行的副作用（断连 / bot offline / 事件注销）
    不可撤销——恢复后旧实例处于"已收尾"状态，快照中的 bots 记录仅为登记。
    {!--< /internal-use >!--}
    """

    adapter_info: Any = None            # _adapter_info 旧条目（含 adapter_class）
    adapter_class: Any = None           # 旧适配器类
    instance: Any = None                # 旧适配器实例（未注册时为 None）
    was_started: bool = False           # 快照时是否处于已启动态
    task: Any = None                    # _adapter_tasks 旧启动任务
    bots: Any = None                    # _bots 平台记录（登记用）
    module_obj: Any = None              # _last_adapter_objs 旧条目（模块对象）
    sys_modules: "dict[str, Any]" = field(default_factory=dict)  # 将被清除的条目


class AdapterLoader(BaseLoader):
    """
    适配器加载器

    负责从 PyPI entry-points 与本地插件文件夹加载适配器
    （本地插件优先：与 entry-point 适配器同名时覆盖，便于本地覆盖调试）

    {!--< tips >!--}
    使用方式：
    >>> loader = AdapterLoader()
    >>> adapter_objs, enabled, disabled = await loader.load(adapter_manager)
    {!--< /tips >!--}
    """

    def __init__(self):
        """初始化适配器加载器"""
        super().__init__("ErisPulse.adapters")
        self._finder = AdapterFinder()
        # 本地适配器插件扫描器（与模块插件共享 plugins/ 目录约定与导入机制）
        from .plugin_folder import PluginFolderLoader

        self._plugin_loader = PluginFolderLoader()
        # 最近一次加载发现的本地适配器插件（供后续热重载等能力使用）
        self._local_adapters: dict[str, dict[str, Any]] = {}
        # 最近一次加载结果快照（适配器热重载需要）
        self._last_adapter_objs: dict[str, Any] = {}
        # 最近一次适配器重载的明细（身份是否变化 / 版本迁移），事件载荷消费
        self._last_adapter_reload_details: dict[str, Any] = {}

    def _get_entry_point_group(self) -> str:
        """
        获取 entry-point 组名

        :return: 入口点组名字符串
        """
        return ADAPTER_ENTRY_POINT_GROUP

    async def load(
        self, manager_instance: Any
    ) -> tuple[dict[str, Any], list[str], list[str]]:
        """
        从 entry-points 加载对象（使用 AdapterFinder）

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
            # 使用 AdapterFinder 查找 entry-points
            entries = self._finder.find_all()

            if entries:
                logger.print_info(
                    i18n.t("loader.adapter.discovered", count=len(entries)), level=1
                )
            elif self._finder.last_error:
                logger.print_info(
                    i18n.t(
                        "loader.adapter.discovery_failed",
                        error=self._finder.last_error,
                    ),
                    level=1,
                )
            else:
                logger.print_info(i18n.t("loader.adapter.none"), level=1)

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

            # 本地适配器插件：发现后并入结果，本地优先（同名覆盖 entry-point）
            self._merge_plugin_folder(objs, enabled_list, disabled_list, manager_instance)

            logger.print_section_separator()

        except KeyboardInterrupt:
            raise  # 允许用户中断
        except SystemExit as e:
            logger.error(
                i18n.t("loader.adapter.systemexit", group=group_name, code=e.code)
            )
        except Exception as e:
            logger.error(
                i18n.t("loader.adapter.load_failed", group=group_name, error=e)
            )

        # 保留最近一次加载结果快照（适配器热重载需要）
        self._last_adapter_objs = objs
        return objs, enabled_list, disabled_list

    async def _process_entry_point(
        self,
        entry_point: Any,
        objs: dict[str, Any],
        enabled_list: list[str],
        disabled_list: list[str],
        manager_instance: Any,
    ) -> tuple[dict[str, Any], list[str], list[str], bool]:
        """
        处理单个适配器 entry-point

        :param entry_point: entry-point 对象
        :param objs: 适配器对象字典
        :param enabled_list: 启用的适配器列表
        :param disabled_list: 停用的适配器列表
        :param manager_instance: 适配器管理器实例

        :return:
            dict[str, Any]: 更新后的适配器对象字典
            list[str]: 更新后的启用适配器列表
            list[str]: 更新后的禁用适配器列表
            bool: 是否为新适配器

        :raises ImportError: 当适配器加载失败时抛出
        """
        meta_name = entry_point.name
        is_new = False

        # 检查适配器是否已经注册，如果未注册则进行注册（默认启用）
        if not manager_instance.exists(meta_name):
            manager_instance._config_register(meta_name)
            is_new = True

        # 获取适配器当前状态
        adapter_status = manager_instance.is_enabled(meta_name)

        if not adapter_status:
            disabled_list.append(meta_name)
            return objs, enabled_list, disabled_list, is_new

        try:
            loaded_class = entry_point.load()
            adapter_obj = sys.modules[loaded_class.__module__]
            import importlib.metadata

            dist = (
                importlib.metadata.distribution(entry_point.dist.name)
                if entry_point.dist
                else None
            )

            # 检查适配器是否继承自 BaseAdapter
            from ..Core.Bases.adapter import BaseAdapter

            is_base_adapter = inspect.isclass(loaded_class) and issubclass(
                loaded_class, BaseAdapter
            )

            if not is_base_adapter:
                # 严格模式：按级别决定容忍加载或拒绝（跳过）
                if self._strict().decide(meta_name, "adapter", "not_base_class"):
                    return objs, enabled_list, disabled_list, is_new

            # 运行时最低 SDK 版本检查：不满足时明确报错并跳过（声明缺失则放行）
            if not self._check_sdk_version(meta_name, "adapter", loaded_class):
                return objs, enabled_list, disabled_list, is_new

            # 依赖声明与可选模块由 _build_adapter_info 从类属性读取
            adapter_info = self._build_adapter_info(
                entry_point, loaded_class, adapter_obj, meta_name, dist
            )

            if not hasattr(adapter_obj, "adapterInfo"):
                cast("Any", adapter_obj).adapterInfo = {}

            cast("Any", adapter_obj).adapterInfo[meta_name] = adapter_info

            objs[meta_name] = adapter_obj
            enabled_list.append(meta_name)

        except SystemExit as e:
            self._strict().record_failure(
                meta_name, "adapter", "systemexit", detail=f"SystemExit({e.code})"
            )
            logger.error(
                i18n.t("loader.adapter.systemexit_single", name=meta_name, code=e.code)
            )
        except Exception as e:
            self._strict().record_failure(
                meta_name, "adapter", "load_failed", detail=str(e)
            )
            logger.error(
                i18n.t("loader.adapter.load_single_failed", name=meta_name, error=e)
            )
            from ..runtime.diagnostics import log_diagnostic

            log_diagnostic(
                e,
                hint_key="loader.adapter.diag_hint",
                hint_params={"name": meta_name},
            )

        return objs, enabled_list, disabled_list, is_new

    # ==================== 本地适配器插件 ====================

    def _merge_plugin_folder(
        self,
        objs: dict[str, Any],
        enabled_list: list[str],
        disabled_list: list[str],
        manager_instance: Any,
    ) -> None:
        """
        {!--< internal-use >!--}
        发现本地适配器插件并并入加载结果

        本地插件优先：与 entry-point 适配器同名时，本地插件覆盖安装包条目
        （便于本地覆盖调试）。启用状态沿用 ``ErisPulse.adapters.status``。

        :param objs: 适配器对象字典（原地修改）
        :param enabled_list: 启用列表（原地修改）
        :param disabled_list: 禁用列表（原地修改）
        :param manager_instance: 适配器管理器实例
        """
        try:
            found = self._plugin_loader.discover_adapters()
        except Exception as e:
            logger.error(i18n.t("loader.plugin.discovery_failed", error=e))
            return

        self._local_adapters = found

        for plugin_name, item in found.items():
            # 与 entry-point 一致：新适配器写入启用状态配置
            if not manager_instance.exists(plugin_name):
                manager_instance._config_register(plugin_name)

            if not manager_instance.is_enabled(plugin_name):
                # 被禁用的本地适配器：若覆盖了 entry-point 同名适配器则一并移除
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
                    i18n.t("loader.adapter.plugin_override", name=plugin_name)
                )

            # 构造与 entry-point 加载路径同构的 adapterInfo 并挂载到模块对象
            module_obj = item["module_obj"]
            if not hasattr(module_obj, "adapterInfo") or not isinstance(
                module_obj.adapterInfo, dict
            ):
                module_obj.adapterInfo = {}
            module_obj.adapterInfo[plugin_name] = {
                "meta": item["meta"],
                "adapter_class": item["adapter_class"],
            }

            objs[plugin_name] = module_obj
            if plugin_name not in enabled_list:
                enabled_list.append(plugin_name)
            if plugin_name in disabled_list:
                disabled_list.remove(plugin_name)

    # ==================== 适配器热重载 ====================

    def _build_adapter_info(
        self,
        entry_point: Any,
        loaded_class: type,
        adapter_obj: Any,
        meta_name: str,
        dist: Any = None,
    ) -> dict[str, Any]:
        """
        {!--< internal-use >!--}
        构造适配器 adapterInfo（首次加载与热重载共用）

        :param entry_point: entry-point 对象
        :param loaded_class: entry-point 加载出的适配器类
        :param adapter_obj: 适配器类定义所在的模块对象
        :param meta_name: 平台名
        :param dist: 发行版元数据（可为 None）
        :return: adapterInfo 字典
        """
        depends_decl = dict(getattr(loaded_class, "depends", None) or {})
        optional_modules = list(getattr(loaded_class, "optional_modules", None) or [])
        return {
            "meta": {
                "name": meta_name,
                "version": getattr(
                    adapter_obj, "__version__", dist.version if dist else "1.0.0"
                ),
                "description": getattr(adapter_obj, "__description__", ""),
                "author": getattr(adapter_obj, "__author__", ""),
                "license": getattr(adapter_obj, "__license__", ""),
                "package": entry_point.dist.name if entry_point.dist else None,
                "min_sdk_version": resolve_min_sdk_version(loaded_class, meta_name),
                "depends": depends_decl,
                "optional_modules": optional_modules,
                "top_level": self._finder.get_top_level_modules(
                    entry_point.dist.name
                )
                if entry_point.dist
                else [],
            },
            "adapter_class": loaded_class,
        }

    @staticmethod
    def _infer_adapter_top_level(info: "dict | None") -> "list[str]":
        """
        {!--< internal-use >!--}
        适配器清理范围兜底推导：适配器类 ``__module__`` 的顶层段

        :param info: adapterInfo 字典（可为 None）
        :return: 顶层模块名列表（无法推导时为空）
        """
        adapter_class = (info or {}).get("adapter_class")
        module = getattr(adapter_class, "__module__", None)
        if module and module.split(".")[0]:
            return [module.split(".")[0]]
        return []

    @staticmethod
    def _invalidate_source_caches_from(entries: "dict[str, Any]") -> None:
        """
        {!--< internal-use >!--}
        按捕获的 ``sys.modules`` 条目清除源文件字节码缓存（``__pycache__``）

        同秒内且字节数不变的源码改写不会使 pyc 失效（mtime 秒级粒度 + size
        校验），重载路径必须显式清除。须在 purge ``sys.modules`` **之前**用
        快照条目调用（快照条目持有 ``__file__``）。

        :param entries: 将被清除的 sys.modules 条目快照
        """
        import importlib.util
        from pathlib import Path

        for mod in entries.values():
            file_attr = getattr(mod, "__file__", None)
            if not file_attr:
                continue
            path = Path(file_attr)
            if path.name == "__init__.py":
                candidates: list[Path] = sorted(path.parent.rglob("*.py"))
            else:
                candidates = [path]
            for py in candidates:
                try:
                    cache = importlib.util.cache_from_source(str(py))
                    if cache:
                        Path(cache).unlink(missing_ok=True)
                except Exception:
                    pass

    def _precheck_adapter_sources(
        self, adapter_name: str, old_obj: Any, old_info: "dict | None", purge_names: "list[str]"
    ) -> bool:
        """
        {!--< internal-use >!--}
        重载卸载前的语法预检：对目标源码树逐文件 ``ast.parse``

        失败（语法错误）即拒绝重载——旧适配器未卸载、继续服务。源码无法
        定位或超过 ``MODULE_RELOAD_PRECHECK_MAX_FILES`` 时跳过预检并记 debug。

        :param adapter_name: 适配器名（日志用）
        :param old_obj: 重载前的快照条目（适配器模块对象）
        :param old_info: 重载前的 adapterInfo
        :param purge_names: 清理名单
        :return: 是否通过（True = 允许继续重载流程）
        """
        import ast

        candidates: list[Any] = []
        # 本地插件：以插件加载器记录的路径为准（比模块对象 __file__ 更可靠）
        try:
            plugin_path = self._plugin_loader.get_loaded_adapter_path(adapter_name)
        except Exception:
            plugin_path = None
        if plugin_path:
            candidates.append(plugin_path)
        if old_obj is not None:
            candidates.append(getattr(old_obj, "__file__", None))
        for name in purge_names:
            mod = sys.modules.get(name)
            if mod is not None:
                candidates.append(getattr(mod, "__file__", None))

        from pathlib import Path

        source_files: list[Path] = []
        for file_attr in candidates:
            if not file_attr:
                continue
            path = Path(file_attr)
            if path.name == "__init__.py":
                source_files.extend(sorted(path.parent.rglob("*.py")))
            elif path.suffix == ".py":
                source_files.append(path)
        if not source_files:
            return True

        try:
            for checked, py in enumerate(source_files, start=1):
                if checked > MODULE_RELOAD_PRECHECK_MAX_FILES:
                    logger.debug(
                        f"adapter reload precheck skipped after {checked - 1} files "
                        f"for '{adapter_name}'"
                    )
                    return True
                try:
                    ast.parse(py.read_text(encoding="utf-8", errors="replace"), filename=str(py))
                except (SyntaxError, ValueError, UnicodeDecodeError) as e:
                    logger.error(
                        i18n.t(
                            "loader.adapter.reload_precheck_failed",
                            name=adapter_name,
                            error=e,
                        )
                    )
                    return False
            return True
        except Exception as e:
            logger.debug(f"adapter reload precheck unavailable for '{adapter_name}': {e}")
            return True

    def _capture_adapter_state(
        self, adapter_name: str, manager_instance: Any, purge_names: "list[str]"
    ) -> "_AdapterReloadSnapshot":
        """
        {!--< internal-use >!--}
        采集适配器重载回滚快照（引用级别）

        :param adapter_name: 适配器名
        :param manager_instance: 适配器管理器实例
        :param purge_names: 将要清除的 sys.modules 顶层名
        :return: 回滚快照
        """
        sys_entries = {
            mod_name: mod
            for mod_name, mod in list(sys.modules.items())
            if any(mod_name == n or mod_name.startswith(f"{n}.") for n in purge_names)
        }
        info = (getattr(manager_instance, "_adapter_info", {}) or {}).get(adapter_name)
        instance = manager_instance._adapters.get(adapter_name)
        return _AdapterReloadSnapshot(
            adapter_info=info,
            adapter_class=(info or {}).get("adapter_class"),
            instance=instance,
            was_started=bool(
                instance is not None
                and instance in getattr(manager_instance, "_started_instances", set())
            ),
            task=(getattr(manager_instance, "_adapter_tasks", {}) or {}).get(adapter_name),
            bots=(getattr(manager_instance, "_bots", {}) or {}).get(adapter_name),
            module_obj=self._last_adapter_objs.get(adapter_name),
            sys_modules=sys_entries,
        )

    def _restore_adapter_snapshot(
        self, snapshot: "_AdapterReloadSnapshot", adapter_name: str, manager_instance: Any
    ) -> None:
        """
        {!--< internal-use >!--}
        恢复适配器重载快照（重发现 / 注册失败时调用）

        恢复顺序：sys.modules 条目 → 注册存根与实例 → 启动态 / bots /
        启动任务。尽力而为语义：unload 已执行的副作用（断连 / bot offline）
        不可撤销，恢复后旧实例处于"已收尾"状态。

        :param snapshot: 重载前采集的快照
        :param adapter_name: 适配器名
        :param manager_instance: 适配器管理器实例
        """
        logger.warning(i18n.t("loader.adapter.reload_rolled_back", name=adapter_name))
        for mod_name, mod in snapshot.sys_modules.items():
            sys.modules[mod_name] = mod
        info = snapshot.adapter_info
        cls = snapshot.adapter_class
        # 直接写注册表（register 会重新实例化且可能在回滚场景再次失败）
        if info is not None or cls is not None:
            try:
                registry = getattr(manager_instance, "_adapter_info", None)
                if isinstance(registry, dict):
                    registry[adapter_name] = info or {}
                else:
                    manager_instance.register(adapter_name, cls, info)
            except Exception:
                pass
        if snapshot.instance is not None:
            try:
                manager_instance._adapters[adapter_name] = snapshot.instance
                if snapshot.was_started:
                    manager_instance._started_instances.add(snapshot.instance)
                if snapshot.bots:
                    manager_instance._bots[adapter_name] = snapshot.bots
                if snapshot.task is not None and not snapshot.task.done():
                    manager_instance._adapter_tasks[adapter_name] = snapshot.task
                else:
                    manager_instance._adapter_tasks.pop(adapter_name, None)
            except Exception:
                pass
        if snapshot.module_obj is not None:
            self._last_adapter_objs[adapter_name] = snapshot.module_obj

    async def reload_adapter(
        self, adapter_name: str, manager_instance: Any, sdk_instance: Any, *, full: bool = True
    ) -> bool:
        """
        热重载单个适配器（支持本地插件 / PyPI 安装包两种来源）

        完整执行 语法预检 → 卸载（shutdown 即清理 + 注销）→ 清理源码字节码
        缓存与 ``sys.modules`` 子树 → 重新发现/导入 → 重新注册 → 原运行态则
        重新拉起 流程；任一步失败自动回滚旧注册状态（尽力而为语义：断连 /
        bot offline 等 unload 副作用不可撤销）。不重载依赖它的其它适配器
        （仅告警）。

        :param adapter_name: 适配器名（平台名）
        :param manager_instance: 适配器管理器实例
        :param sdk_instance: SDK 实例
        :param full: 保留参数位（当前两种来源均执行全量清理，与模块语义对齐）
        :return: 是否重载成功（适配器被移除视为成功）
        """
        self._last_adapter_reload_details = {}
        old_info = (getattr(manager_instance, "_adapter_info", {}) or {}).get(adapter_name)
        old_obj = self._last_adapter_objs.get(adapter_name)
        if old_info is None and old_obj is None:
            logger.warning(i18n.t("loader.adapter.reload_unknown", name=adapter_name))
            return False

        meta = (old_info or {}).get("meta", {}) or {}
        is_plugin = meta.get("source") == ADAPTER_SOURCE_PLUGIN_FOLDER

        # 清理范围：插件取插件名；安装包取 top_level → 类 __module__ 前缀兜底
        if is_plugin:
            purge_names = [adapter_name]
        else:
            purge_names = list(meta.get("top_level") or [])
            if not purge_names and old_obj is not None:
                prefix = getattr(old_obj, "__name__", None)
                if prefix and prefix.split(".")[0]:
                    purge_names = [prefix.split(".")[0]]
            if not purge_names:
                purge_names = self._infer_adapter_top_level(old_info)
            if not purge_names:
                logger.warning(
                    i18n.t("loader.adapter.reload_top_missing", name=adapter_name)
                )
                purge_names = [adapter_name]

        # 语法预检：unload 之前拦截语法错误——失败即拒绝重载，旧适配器继续服务
        if not self._precheck_adapter_sources(adapter_name, old_obj, old_info, purge_names):
            return False

        # 依赖者提示（v1 不级联：适配器依赖方经注册表间接消费，无实例级联）
        dependents = [
            dep
            for dep, info in (getattr(manager_instance, "_adapter_info", {}) or {}).items()
            if dep != adapter_name
            and adapter_name in (
                ((info or {}).get("meta", {}) or {}).get("depends", {}) or {}
            ).get("adapters", [])
        ]
        if dependents:
            logger.warning(
                i18n.t(
                    "loader.adapter.reload_dependents",
                    name=adapter_name,
                    deps=", ".join(dependents),
                )
            )

        snapshot = self._capture_adapter_state(adapter_name, manager_instance, purge_names)

        # 1. 卸载（shutdown 即清理：路由/事件/任务/bot offline + 注销注册表）
        try:
            await manager_instance.unload(adapter_name)
        except Exception as e:
            logger.error(
                i18n.t("loader.adapter.reload_unload_failed", name=adapter_name, error=e)
            )

        # 2. 清缓存：pyc → sys.modules 子树 → 导入系统 → finder 缓存 → 插件路径
        self._invalidate_source_caches_from(snapshot.sys_modules)
        for mod_name in snapshot.sys_modules:
            sys.modules.pop(mod_name, None)
        import importlib

        importlib.invalidate_caches()
        self._finder.clear_cache()
        if is_plugin:
            try:
                self._plugin_loader._loaded_adapter_paths.pop(adapter_name, None)
            except Exception:
                pass
            self._local_adapters.pop(adapter_name, None)

        # 3. 重新发现并组装 adapterInfo（按来源选择发现路径）
        new_info: dict[str, Any] | None = None
        new_obj: Any = None
        removed = False
        if is_plugin:
            try:
                found = self._plugin_loader.discover_adapters()
            except Exception as e:
                logger.error(i18n.t("loader.plugin.discovery_failed", error=e))
                found = {}
            item = found.get(adapter_name)
            if item is None:
                removed = True
            else:
                module_obj = item["module_obj"]
                if not hasattr(module_obj, "adapterInfo") or not isinstance(
                    module_obj.adapterInfo, dict
                ):
                    module_obj.adapterInfo = {}
                new_info = {"meta": item["meta"], "adapter_class": item["adapter_class"]}
                module_obj.adapterInfo[adapter_name] = new_info
                new_obj = module_obj
        else:
            entry = self._finder.find_by_name(adapter_name)
            if entry is None:
                removed = True
            else:
                try:
                    loaded_class = entry.load()
                    adapter_obj = sys.modules[loaded_class.__module__]
                    new_info = self._build_adapter_info(
                        entry, loaded_class, adapter_obj, adapter_name
                    )
                    if not hasattr(adapter_obj, "adapterInfo"):
                        cast("Any", adapter_obj).adapterInfo = {}
                    cast("Any", adapter_obj).adapterInfo[adapter_name] = new_info
                    new_obj = adapter_obj
                except Exception as e:
                    logger.error(
                        i18n.t(
                            "loader.adapter.reload_load_failed", name=adapter_name, error=e
                        )
                    )
                    from ..runtime.diagnostics import log_diagnostic

                    log_diagnostic(
                        e,
                        hint_key="loader.adapter.diag_hint",
                        hint_params={"name": adapter_name},
                    )
                    self._restore_adapter_snapshot(
                        snapshot, adapter_name, manager_instance
                    )
                    return False

        # 适配器已被移除（pip 卸载 / 插件删除）：确认从快照移除
        if removed:
            self._last_adapter_objs.pop(adapter_name, None)
            self._last_adapter_reload_details = {
                "identity_changed": True,
                "was_started": snapshot.was_started,
                "source": "plugin" if is_plugin else "pypi",
            }
            logger.info(i18n.t("loader.adapter.reload_removed", name=adapter_name))
            return True

        # 禁用状态：仅重建发现快照，不注册不拉起（与首次加载的禁用语义一致）
        if new_info is None or new_obj is None:
            return False
        if not manager_instance.is_enabled(adapter_name):
            self._last_adapter_objs[adapter_name] = new_obj
            self._last_adapter_reload_details = {
                "identity_changed": new_info.get("adapter_class")
                is not snapshot.adapter_class,
                "was_started": False,
                "source": "plugin" if is_plugin else "pypi",
            }
            logger.info(i18n.t("loader.adapter.reload_ok", name=adapter_name))
            return True

        # 4. 重新注册（实例重用陷阱由身份核对兜底：类同对象则旧实例被复用）
        try:
            manager_instance.register(
                adapter_name, new_info["adapter_class"], new_info
            )
        except Exception as e:
            logger.error(
                i18n.t("loader.adapter.reload_register_failed", name=adapter_name, error=e)
            )
            self._restore_adapter_snapshot(snapshot, adapter_name, manager_instance)
            return False

        # 5. 原运行态则重新拉起（状态事件由 startup / _run_adapter 全链路播报；
        #    启动失败不判重载失败——代码已换新，异步重试链接管）
        if snapshot.was_started:
            try:
                await manager_instance.startup(adapter_name)
            except Exception as e:
                logger.error(
                    i18n.t(
                        "loader.adapter.reload_start_failed", name=adapter_name, error=e
                    )
                )

        # 6. 身份核对 + 明细回填（事件载荷消费）
        new_class = (
            (getattr(manager_instance, "_adapter_info", {}) or {}).get(adapter_name) or {}
        ).get("adapter_class")
        identity_changed = bool(
            new_class is not None and new_class is not snapshot.adapter_class
        )
        if not identity_changed:
            logger.warning(
                i18n.t("loader.adapter.reload_identity_unchanged", name=adapter_name)
            )
        self._last_adapter_reload_details = {
            "identity_changed": identity_changed,
            "version_old": meta.get("version"),
            "version_new": (new_info.get("meta") or {}).get("version")
            or meta.get("version"),
            "was_started": snapshot.was_started,
            "source": "plugin" if is_plugin else "pypi",
        }

        self._last_adapter_objs[adapter_name] = new_obj
        logger.info(i18n.t("loader.adapter.reload_ok", name=adapter_name))
        return True

    async def register_to_manager(
        self, adapters: list[str], adapter_objs: dict[str, Any], manager_instance: Any
    ) -> bool:
        """
        将适配器注册到管理器

        :param adapters: 适配器名称列表
        :param adapter_objs: 适配器对象字典
        :param manager_instance: 适配器管理器实例
        :return: 适配器注册是否成功

        {!--< tips >!--}
        此方法由初始化协调器调用
        {!--< /tips >!--}
        """
        # 并行注册所有适配器
        register_tasks = []

        for adapter_name in adapters:
            adapter_obj = adapter_objs[adapter_name]

            async def register_single_adapter(name: str, obj: Any) -> bool:
                """注册单个适配器"""
                try:
                    success = True
                    if hasattr(obj, "adapterInfo") and isinstance(
                        obj.adapterInfo, dict
                    ):
                        for platform, adapter_info in obj.adapterInfo.items():
                            # 使用管理器的方法检查是否已存在
                            if platform in manager_instance._adapters:
                                continue

                            adapter_class = adapter_info["adapter_class"]

                            # 调用管理器的 register 方法
                            manager_instance.register(
                                platform, adapter_class, adapter_info
                            )

                            # 提交适配器加载完成事件
                            await lifecycle.submit_event(
                                "adapter.load",
                                msg=i18n.t(
                                    "loader.adapter.load_complete", name=platform
                                ),
                                data={"platform": platform, "success": True},
                            )
                    return success
                except SystemExit as e:
                    self._strict().record_failure(
                        name,
                        "adapter",
                        "register_systemexit",
                        detail=f"SystemExit({e.code})",
                    )
                    logger.error(
                        i18n.t(
                            "loader.adapter.register_systemexit", name=name, code=e.code
                        )
                    )
                    await lifecycle.submit_event(
                        "adapter.load",
                        msg=i18n.t("loader.adapter.register_systemexit_msg", name=name),
                        data={"platform": name, "success": False},
                    )
                    return False
                except Exception as e:
                    self._strict().record_failure(
                        name, "adapter", "register_failed", detail=str(e)
                    )
                    logger.error(
                        i18n.t("loader.adapter.register_failed", name=name, error=e)
                    )
                    from ..runtime.diagnostics import log_diagnostic

                    log_diagnostic(
                        e,
                        hint_key="loader.adapter.diag_hint",
                        hint_params={"name": name},
                    )
                    # 提交适配器加载失败事件
                    await lifecycle.submit_event(
                        "adapter.load",
                        msg=i18n.t(
                            "loader.adapter.load_failed_msg", name=name, error=e
                        ),
                        data={"platform": name, "success": False},
                    )
                    return False

            register_tasks.append(register_single_adapter(adapter_name, adapter_obj))

        # 等待所有注册任务完成
        register_results = await asyncio.gather(*register_tasks, return_exceptions=True)

        # 记录失败的适配器并从列表中移除
        failed_adapters = []
        for i, result in enumerate(register_results):
            adapter_name = adapters[i]
            if isinstance(result, BaseException) or result is False:
                logger.warning(
                    i18n.t("loader.adapter.register_skipped", name=adapter_name)
                )
                failed_adapters.append(adapter_name)

        for name in failed_adapters:
            if name in adapters:
                adapters.remove(name)

        return True
