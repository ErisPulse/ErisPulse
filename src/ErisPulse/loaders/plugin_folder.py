"""
ErisPulse 本地插件文件夹加载器

提供本地插件目录加载：无需打包发布到 PyPI，将插件放入项目插件目录
（默认 ``plugins/``，可通过 ``ErisPulse.framework.plugins_dir`` 配置，支持多目录），
框架启动时自动发现并加载。

目录约定::

    project/
    ├── main.py
    └── plugins/                  # 默认插件目录
        ├── weather/              # 包形式插件（含 __init__.py）
        │   ├── __init__.py
        │   └── Core.py           # 定义 class Main(BaseModule)
        └── dice.py               # 单文件插件

{!--< tips >!--}
1. 单 ``.py`` 文件 → 插件名 = 文件名；子目录（含 ``__init__.py``）→ 插件名 = 目录名
2. 模块类识别：优先 ``Main``（BaseModule 子类），兼容首个 BaseModule 子类
3. 与 PyPI 模块同名时**本地插件优先**（便于覆盖调试）
4. 插件与安装包模块共用同一套启用状态 / 作用域 / meta / i18n / 上下文
{!--< /tips >!--}
"""

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any

from ..Core.constants import MODULE_SOURCE_PLUGIN_FOLDER
from ..Core.i18n import i18n
from ..Core.logger import logger

# 默认插件目录名
DEFAULT_PLUGINS_DIR = "plugins"


class PluginFolderLoader:
    """
    本地插件文件夹加载器

    扫描插件目录、导入插件模块、识别模块类并构造与 entry-point 一致的
    ``moduleInfo`` 结构，并入 :class:`ModuleLoader` 的加载结果。
    """

    def __init__(self):
        self._loaded_paths: dict[str, Path] = {}

    # ==================== 目录解析 ====================

    def get_plugins_dirs(self) -> list[Path]:
        """
        获取插件目录列表（从配置读取，相对项目根目录解析）

        :return: 插件目录 Path 列表（可能不存在）
        """
        try:
            from ..runtime import get_framework_config

            framework_config = get_framework_config()
        except Exception:
            framework_config = {}

        raw = framework_config.get("plugins_dir", DEFAULT_PLUGINS_DIR)
        if isinstance(raw, str):
            dirs = [raw]
        elif isinstance(raw, (list, tuple)):
            dirs = [str(d) for d in raw]
        else:
            dirs = [DEFAULT_PLUGINS_DIR]

        return [Path(d) for d in dirs]

    # ==================== 发现与加载 ====================

    def discover(self) -> dict[str, Any]:
        """
        扫描全部插件目录并加载插件

        :return: {插件名: 模块对象（带 moduleInfo 属性)}
        """
        results: dict[str, Any] = {}
        plugin_dirs = self.get_plugins_dirs()

        for base in plugin_dirs:
            if not base.is_dir():
                logger.trace(
                    i18n.t("loader.plugin.dir_not_found", dir=str(base))
                )
                continue

            for entry in sorted(base.iterdir()):
                name = self._plugin_name_of(entry)
                if name is None:
                    continue

                # 同名插件先到先得（跨目录重复声明时警告）
                if name in results:
                    logger.warning(
                        i18n.t("loader.plugin.duplicate", name=name)
                    )
                    continue

                module_obj = self._load_plugin(name, entry)
                if module_obj is not None:
                    results[name] = module_obj

        if results:
            logger.print_info(
                i18n.t("loader.plugin.discovered", count=len(results)), level=1
            )

        return results

    @staticmethod
    def _plugin_name_of(entry: Path) -> str | None:
        """
        {!--< internal-use >!--}
        解析插件名；不符合约定的条目返回 None

        - 单文件：必须为 .py，文件名（不含后缀）为插件名
        - 子目录：必须含 __init__.py，目录名为插件名
        - 忽略 __pycache__ 与 _ 开头的条目
        """
        if entry.name.startswith("_") or entry.name == "__pycache__":
            return None
        if entry.is_file():
            if entry.suffix != ".py":
                return None
            return entry.stem
        if entry.is_dir():
            if not (entry / "__init__.py").is_file():
                return None
            return entry.name
        return None

    def _load_plugin(self, name: str, path: Path) -> Any:
        """
        {!--< internal-use >!--}
        导入单个插件并构造 moduleInfo

        :param name: 插件名
        :param path: 插件路径（.py 文件或包目录）
        :return: 模块对象（带 moduleInfo）；加载失败返回 None
        """
        try:
            module_obj = self._import_plugin(name, path)
            module_class = self._find_module_class(module_obj)
            if module_class is None:
                logger.warning(
                    i18n.t("loader.plugin.no_module_class", name=name)
                )
                return None

            from .strategy import ModuleLoadStrategy

            strategy = self._get_load_strategy(module_class)
            if isinstance(strategy, ModuleLoadStrategy) and hasattr(strategy, "_data"):
                lazy_load = strategy._data.get("lazy_load", True)
                priority = strategy._data.get("priority", 0)
                depends = strategy._data.get("depends", None) or []
            elif isinstance(strategy, dict):
                lazy_load = strategy.get("lazy_load", True)
                priority = strategy.get("priority", 0)
                depends = strategy.get("depends", None) or []
            else:
                lazy_load = True
                priority = 0
                depends = []

            from ..Core.Bases.module import BaseModule

            is_base_module = inspect.isclass(module_class) and issubclass(
                module_class, BaseModule
            )

            module_info = {
                "meta": {
                    "name": name,
                    "version": getattr(module_obj, "__version__", "1.0.0"),
                    "description": getattr(module_obj, "__description__", ""),
                    "author": getattr(module_obj, "__author__", ""),
                    "license": getattr(module_obj, "__license__", ""),
                    "package": None,  # 本地插件非安装包
                    "lazy_load": lazy_load,
                    "priority": priority,
                    "depends": list(depends),
                    "is_base_module": is_base_module,
                    "top_level": [name],
                    "source": MODULE_SOURCE_PLUGIN_FOLDER,
                },
                "module_class": module_class,
                "strategy": strategy,
            }

            module_obj.moduleInfo = module_info
            self._loaded_paths[name] = path
            return module_obj
        except SystemExit as e:
            logger.error(
                i18n.t("loader.plugin.systemexit", name=name, code=e.code)
            )
            return None
        except Exception as e:
            logger.error(
                i18n.t("loader.plugin.load_failed", name=name, error=e)
            )
            from ..runtime.diagnostics import log_diagnostic

            log_diagnostic(e, hint_key="loader.plugin.diag_hint")
            return None

    def _import_plugin(self, name: str, path: Path) -> Any:
        """
        {!--< internal-use >!--}
        导入插件模块

        - 单文件：``spec_from_file_location`` 显式路径导入
        - 包目录：将插件目录加入 sys.path 首位后 import_module
          （路径优先级保证本地包覆盖同名安装包）
        """
        if path.is_file():
            spec = importlib.util.spec_from_file_location(name, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load plugin file: {path}")
            module_obj = importlib.util.module_from_spec(spec)
            sys.modules[name] = module_obj
            spec.loader.exec_module(module_obj)
            return module_obj

        base_str = str(path.parent)
        if base_str not in sys.path:
            sys.path.insert(0, base_str)
        return importlib.import_module(name)

    @staticmethod
    def _find_module_class(module_obj: Any) -> type | None:
        """
        {!--< internal-use >!--}
        识别插件中的模块类

        优先 ``Main``（BaseModule 子类）；否则回落到本模块内定义的
        首个 BaseModule 子类。

        :param module_obj: 插件模块对象
        :return: 模块类；未找到返回 None
        """
        from ..Core.Bases.module import BaseModule

        main_class = getattr(module_obj, "Main", None)
        if (
            inspect.isclass(main_class)
            and issubclass(main_class, BaseModule)
            and main_class is not BaseModule
        ):
            return main_class

        module_name = getattr(module_obj, "__name__", "")
        for obj in vars(module_obj).values():
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseModule)
                and obj is not BaseModule
                and getattr(obj, "__module__", "") == module_name
            ):
                return obj
        return None

    @staticmethod
    def _get_load_strategy(module_class: type) -> Any:
        """{!--< internal-use >!--} 读取模块类的 get_load_strategy()"""
        method = getattr(module_class, "get_load_strategy", None)
        if callable(method):
            try:
                return method()
            except Exception:
                pass
        from .strategy import ModuleLoadStrategy

        return ModuleLoadStrategy()

    def get_loaded_path(self, name: str) -> Path | None:
        """
        获取已加载插件的源路径（热重载用）

        :param name: 插件名
        :return: 插件路径；未知插件返回 None
        """
        return self._loaded_paths.get(name)


__all__ = [
    "DEFAULT_PLUGINS_DIR",
    "PluginFolderLoader",
]
