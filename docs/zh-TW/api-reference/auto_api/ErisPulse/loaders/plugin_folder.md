# `ErisPulse.loaders.plugin_folder` 模块

---

## 模块概述


ErisPulse 本地插件文件夹加载器

提供本地插件目录加载：无需打包发布到 PyPI，将插件放入项目插件目录
（默认 ``plugins/``，可通过 ``ErisPulse.framework.plugins_dir`` 配置，支持多目录），
框架启动时自动发现并加载。

目录约定:
```
project/
├── main.py
└── plugins/                  # 默认插件目录
    ├── weather/              # 包形式模块插件（含 __init__.py）
    │   ├── __init__.py
    │   └── Core.py           # 定义 class Main(BaseModule)
    ├── my_adapter/           # 包形式适配器插件
    │   ├── __init__.py
    │   └── Core.py           # 定义 BaseAdapter 子类（推荐经 __init__ 导出）
    └── dice.py               # 单文件插件
```

> **提示**
> 1. 单 ``.py`` 文件 → 插件名 = 文件名；子目录（含 ``__init__.py``）→ 插件名 = 目录名
> 2. 模块类识别：优先 ``Main``（BaseModule 子类），兼容首个 BaseModule 子类
> 3. 适配器类识别：优先 ``Main``（BaseAdapter 子类），兼容插件内定义/导出的
> 首个 BaseAdapter 子类；由 :meth:`discover_adapters` 供适配器加载器消费
> 4. 与 PyPI 模块/适配器同名时**本地插件优先**（便于覆盖调试）
> 5. 插件与安装包模块/适配器共用同一套启用状态 / 作用域 / meta / i18n / 上下文

---

## 类列表


### `class PluginFolderLoader`

本地插件文件夹加载器

扫描插件目录、导入插件模块、识别模块类并构造与 entry-point 一致的
``moduleInfo`` 结构，并入 :class:`ModuleLoader` 的加载结果。


#### 方法列表


##### `set_strict_recorder(recorder: Any) -> None`

注入严格模式登记器（宿主加载器在 set_strict_manager 时同步传播）

- **recorder** (`StrictModeManager`): 实例（需提供 record_failure）

---


##### `get_plugins_dirs() -> list[Path]`

获取插件目录列表（从配置读取，相对项目根目录解析）

**返回值**: 插件目录 Path 列表（可能不存在）

---


##### `discover() -> dict[str, Any]`

扫描全部插件目录并加载插件

**返回值**: {插件名: 模块对象（带 moduleInfo 属性)}

---


##### `_plugin_name_of(entry: Path) -> str | None`（staticmethod）

**内部方法**
解析插件名；不符合约定的条目返回 None

- 单文件：必须为 .py，文件名（不含后缀）为插件名
- 子目录：必须含 __init__.py，目录名为插件名
- 忽略 __pycache__ 与 _ 开头的条目

---


##### `_load_plugin(name: str, path: Path) -> Any`

**内部方法**
导入单个插件并构造 moduleInfo

- **name**: 插件名
- **path**: 插件路径（.py 文件或包目录）

**返回值**: 模块对象（带 moduleInfo）；加载失败返回 None

---


##### `_import_plugin(name: str, path: Path) -> Any`

**内部方法**
导入插件模块

- 单文件：``spec_from_file_location`` 显式路径导入
- 包目录：将插件目录加入 sys.path 首位后 import_module
  （路径优先级保证本地包覆盖同名安装包）

---


##### `_find_module_class(module_obj: Any) -> type | None`（staticmethod）

**内部方法**
识别插件中的模块类

优先 ``Main``（BaseModule 子类）；否则回落到本模块内定义的
首个 BaseModule 子类。

- **module_obj**: 插件模块对象

**返回值**: 模块类；未找到返回 None

---


##### `_find_adapter_class(module_obj: Any) -> type | None`（staticmethod）

**内部方法**
识别插件中的适配器类

优先 ``Main``（BaseAdapter 子类）；否则回落到插件内定义或经包
``__init__`` 导出的首个 BaseAdapter 子类（``MyAdapter.Core`` 定义、
``MyAdapter.__init__`` 导出为模板惯例，故 ``__module__`` 匹配
插件名自身或其子模块均有效，但不接受外部包的重导出）。

- **module_obj**: 插件模块对象

**返回值**: 适配器类；未找到返回 None

---


##### `discover_adapters() -> dict[str, dict[str, Any]]`

扫描全部插件目录并识别适配器插件

与 :meth:`discover` 共享目录解析与导入机制；模块类插件静默跳过
（由模块加载侧消费）。发现结果同步登记到
:attr:`_loaded_adapter_paths` 供热重载查询源路径。

**返回值**: ``{适配器名: {"name", "path", "adapter_class", "module_obj", "meta"}}``

> **提示**
> meta 结构与 entry-point 加载路径的 ``adapterInfo.meta`` 一致，
> ``source`` 为 ``ADAPTER_SOURCE_PLUGIN_FOLDER``。

---


##### `_load_adapter_plugin(name: str, path: Path) -> dict[str, Any] | None`

**内部方法**
导入单个适配器插件并构造与 entry-point 加载路径一致的描述结构

- **name**: 适配器插件名
- **path**: 插件路径（.py 文件或包目录）

**返回值**: 适配器描述字典；非适配器插件或加载失败返回 None

---


##### `get_loaded_adapter_path(name: str) -> Path | None`

获取已加载适配器插件的源路径（热重载用）

- **name**: 适配器插件名

**返回值**: 插件路径；未知适配器返回 None

---


##### `_get_load_strategy(module_class: type) -> Any`（staticmethod）

**内部方法** 读取模块类的 get_load_strategy()

---


##### `get_loaded_path(name: str) -> Path | None`

获取已加载插件的源路径（热重载用）

- **name**: 插件名

**返回值**: 插件路径；未知插件返回 None

---

