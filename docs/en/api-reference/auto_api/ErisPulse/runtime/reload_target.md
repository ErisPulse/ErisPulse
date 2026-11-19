# `ErisPulse.runtime.reload_target` 模块

---

## 模块概述


热重载目标判定

按运行时注册表把变更文件映射为最小重载单元：

- ``plugin``：插件目录内的文件，交给插件热重载 watcher
- ``module``：唯一已加载模块的源码
- ``adapter``：唯一已注册适配器的源码
- ``restart``：入口脚本 / 框架源码 / 多匹配 / 无法归属，需进程级重启

判定基于 ``sys.modules`` 中对象的 ``__file__`` / ``__path__``，不按路径字符串猜。

---

## 函数列表


### `classify_reload_path(path: 'str | Path', sdk: Any, entry_paths: 'tuple[str | Path, ...]' = ()) -> ReloadTarget`

判定变更文件应触发的最小重载单元

- **path**: 变更文件路径
- **sdk** (`SDK`): 实例（读取模块 / 适配器注册表）
- **entry_paths**: 入口脚本路径；缺省取 ``sys.argv[0]``（存在且为 .py 时）

**返回值**: 重载目标

---


### `_resolve_entry_paths(entry_paths: 'tuple[str | Path, ...]') -> 'set[Path]'`

**内部方法** 解析入口脚本路径集合

---


### `_module_sources(sdk: Any) -> 'dict[str, list[Path]]'`

**内部方法** 已加载模块名 -> 源码根路径列表

---


### `_adapter_sources(sdk: Any) -> 'dict[str, list[Path]]'`

**内部方法** 已注册适配器名 -> 源码根路径列表

---


### `_source_roots(obj: Any) -> 'list[Path]'`

**内部方法** 解析类所属模块的源码文件 / 包目录

---


### `_matching_owners(sources: 'dict[str, list[Path]]', changed: Path) -> 'list[str]'`

**内部方法** 返回源码根包含变更文件的 owner 名

---


### `_is_relative_to(path: Path, root: Path) -> bool`

**内部方法** Python 3.10 兼容的 is_relative_to

---


### `_plugin_dirs() -> 'list[Path]'`

**内部方法** 插件目录绝对路径列表

---


### `_is_in_plugin_dir(path: Path) -> bool`

**内部方法** 变更文件是否位于插件目录内

---


### `_plugin_name(path: Path) -> 'str | None'`

**内部方法** 插件名（单文件取文件名，包取首段目录）

---


### `_framework_root() -> Path`

**内部方法** ErisPulse 包源码根目录

---


### `_is_in_framework(path: Path) -> bool`

**内部方法** 变更文件是否位于框架源码内

---


## 类列表


### `class ReloadTarget`

单个变更文件的重载目标

- **kind**: ``plugin`` / ``module`` / ``adapter`` / ``restart``
- **name**: 模块名或适配器平台名（``restart`` 时为 None）
- **reason**: 重启原因（仅 ``restart``）

