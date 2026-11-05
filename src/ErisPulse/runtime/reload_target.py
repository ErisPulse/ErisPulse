"""
热重载目标判定

按运行时注册表把变更文件映射为最小重载单元：

- ``plugin``：插件目录内的文件，交给插件热重载 watcher
- ``module``：唯一已加载模块的源码
- ``adapter``：唯一已注册适配器的源码
- ``restart``：入口脚本 / 框架源码 / 多匹配 / 无法归属，需进程级重启

判定基于 ``sys.modules`` 中对象的 ``__file__`` / ``__path__``，不按路径字符串猜。
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = ["ReloadTarget", "classify_reload_path"]


@dataclass(frozen=True)
class ReloadTarget:
    """
    单个变更文件的重载目标

    :param kind: ``plugin`` / ``module`` / ``adapter`` / ``restart``
    :param name: 模块名或适配器平台名（``restart`` 时为 None）
    :param reason: 重启原因（仅 ``restart``）
    """

    kind: str
    name: "str | None" = None
    reason: "str | None" = None


def classify_reload_path(
    path: "str | Path",
    sdk: Any,
    entry_paths: "tuple[str | Path, ...]" = (),
) -> ReloadTarget:
    """
    判定变更文件应触发的最小重载单元

    :param path: 变更文件路径
    :param sdk: SDK 实例（读取模块 / 适配器注册表）
    :param entry_paths: 入口脚本路径；缺省取 ``sys.argv[0]``（存在且为 .py 时）
    :return: 重载目标
    """
    changed = Path(path).resolve()
    if changed.suffix != ".py":
        return ReloadTarget("restart", reason="non-python")

    if _is_in_plugin_dir(changed):
        return ReloadTarget("plugin", _plugin_name(changed))

    if _is_in_framework(changed):
        return ReloadTarget("restart", reason="framework")

    entries = _resolve_entry_paths(entry_paths)
    if changed in entries:
        return ReloadTarget("restart", reason="entry")

    module_names = _matching_owners(_module_sources(sdk), changed)
    adapter_names = _matching_owners(_adapter_sources(sdk), changed)

    if module_names and adapter_names:
        return ReloadTarget("restart", reason="ambiguous")
    if len(module_names) > 1 or len(adapter_names) > 1:
        return ReloadTarget("restart", reason="ambiguous")
    if module_names:
        return ReloadTarget("module", module_names[0])
    if adapter_names:
        return ReloadTarget("adapter", adapter_names[0])
    return ReloadTarget("restart", reason="unmapped")


def _resolve_entry_paths(
    entry_paths: "tuple[str | Path, ...]",
) -> "set[Path]":
    """{!--< internal-use >!--} 解析入口脚本路径集合"""
    raw: list[Any] = list(entry_paths or ())
    if not raw:
        raw = [sys.argv[0] if sys.argv else ""]
    result: set[Path] = set()
    for item in raw:
        text = str(item or "").strip()
        if not text or not text.endswith(".py"):
            continue
        try:
            candidate = Path(text).resolve()
        except OSError:
            continue
        if candidate.exists():
            result.add(candidate)
    return result


def _module_sources(sdk: Any) -> "dict[str, list[Path]]":
    """{!--< internal-use >!--} 已加载模块名 -> 源码根路径列表"""
    result: dict[str, list[Path]] = {}
    manager = getattr(sdk, "module", None)
    classes = getattr(manager, "_module_classes", None)
    if not isinstance(classes, dict):
        return result
    for name, cls in list(classes.items()):
        roots = _source_roots(cls)
        if roots:
            result[str(name)] = roots
    return result


def _adapter_sources(sdk: Any) -> "dict[str, list[Path]]":
    """{!--< internal-use >!--} 已注册适配器名 -> 源码根路径列表"""
    result: dict[str, list[Path]] = {}
    manager = getattr(sdk, "adapter", None)
    instances = getattr(manager, "_adapters", None)
    if not isinstance(instances, dict):
        return result
    for name, instance in list(instances.items()):
        roots = _source_roots(type(instance))
        if roots:
            result[str(name)] = roots
    return result


def _source_roots(obj: Any) -> "list[Path]":
    """{!--< internal-use >!--} 解析类所属模块的源码文件 / 包目录"""
    module_name = getattr(obj, "__module__", "")
    if not module_name:
        return []
    module_obj = sys.modules.get(module_name)
    if module_obj is None:
        return []

    roots: set[Path] = set()
    file = getattr(module_obj, "__file__", None)
    if file:
        try:
            file_path = Path(file).resolve()
        except OSError:
            file_path = None
        if file_path is not None:
            roots.add(file_path)
            if file_path.name == "__init__.py":
                roots.add(file_path.parent)
    for entry in getattr(module_obj, "__path__", ()) or ():
        try:
            roots.add(Path(entry).resolve())
        except OSError:
            continue

    top_level = module_name.split(".", 1)[0]
    top_obj = sys.modules.get(top_level)
    if top_obj is not None:
        for entry in getattr(top_obj, "__path__", ()) or ():
            try:
                roots.add(Path(entry).resolve())
            except OSError:
                continue
    return [root for root in roots if root.exists()]


def _matching_owners(
    sources: "dict[str, list[Path]]", changed: Path
) -> "list[str]":
    """{!--< internal-use >!--} 返回源码根包含变更文件的 owner 名"""
    matched: list[str] = []
    for name, roots in sources.items():
        for root in roots:
            if changed == root or _is_relative_to(changed, root):
                matched.append(name)
                break
    return matched


def _is_relative_to(path: Path, root: Path) -> bool:
    """{!--< internal-use >!--} Python 3.10 兼容的 is_relative_to"""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _plugin_dirs() -> "list[Path]":
    """{!--< internal-use >!--} 插件目录绝对路径列表"""
    try:
        from ..loaders.plugin_folder import PluginFolderLoader

        raw_dirs = PluginFolderLoader().get_plugins_dirs()
    except Exception:
        raw_dirs = [Path("plugins")]
    result: list[Path] = []
    for item in raw_dirs:
        try:
            result.append(Path(item).resolve())
        except OSError:
            continue
    return result


def _is_in_plugin_dir(path: Path) -> bool:
    """{!--< internal-use >!--} 变更文件是否位于插件目录内"""
    return any(_is_relative_to(path, base) for base in _plugin_dirs())


def _plugin_name(path: Path) -> "str | None":
    """{!--< internal-use >!--} 插件名（单文件取文件名，包取首段目录）"""
    for base in _plugin_dirs():
        try:
            rel = path.relative_to(base)
        except ValueError:
            continue
        parts = list(rel.parts)
        if parts:
            return parts[0].removesuffix(".py")
    return None


def _framework_root() -> Path:
    """{!--< internal-use >!--} ErisPulse 包源码根目录"""
    return Path(__file__).resolve().parents[1]


def _is_in_framework(path: Path) -> bool:
    """{!--< internal-use >!--} 变更文件是否位于框架源码内"""
    return _is_relative_to(path, _framework_root())
