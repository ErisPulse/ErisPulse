# `ErisPulse.loaders.plugin_folder` 模块

---

## 模块概述


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

> **提示**
> 1. 单 ``.py`` 文件 → 插件名 = 文件名；子目录（含 ``__init__.py``）→ 插件名 = 目录名
> 2. 模块类识别：优先 ``Main``（BaseModule 子类），兼容首个 BaseModule 子类
> 3. 与 PyPI 模块同名时**本地插件优先**（便于覆盖调试）
> 4. 插件与安装包模块共用同一套启用状态 / 作用域 / meta / i18n / 上下文

---

## 类列表


### `class PluginFolderLoader`

本地插件文件夹加载器

扫描插件目录、导入插件模块、识别模块类并构造与 entry-point 一致的
``moduleInfo`` 结构，并入 :class:`ModuleLoader` 的加载结果。


#### 方法列表


##### `get_plugins_dirs()`

获取插件目录列表（从配置读取，相对项目根目录解析）

**返回值** (`插件目录`): Path 列表（可能不存在）

---


##### `discover()`

扫描全部插件目录并加载插件

**返回值** (`{插件名:`): 模块对象（带 moduleInfo 属性)}

---


##### `_plugin_name_of(entry: Path)`

> **内部方法**
解析插件名；不符合约定的条目返回 None

- 单文件：必须为 .py，文件名（不含后缀）为插件名
- 子目录：必须含 __init__.py，目录名为插件名
- 忽略 __pycache__ 与 _ 开头的条目

---


##### `_load_plugin(name: str, path: Path)`

> **内部方法**
导入单个插件并构造 moduleInfo

- **name** (`插件名`): - **path**: 插件路径（.py 文件或包目录）
**返回值** (`模块对象（带`): moduleInfo）；加载失败返回 None

---


##### `_import_plugin(name: str, path: Path)`

> **内部方法**
导入插件模块

- 单文件：``spec_from_file_location`` 显式路径导入
- 包目录：将插件目录加入 sys.path 首位后 import_module
  （路径优先级保证本地包覆盖同名安装包）

---


##### `_find_module_class(module_obj: Any)`

> **内部方法**
识别插件中的模块类

优先 ``Main``（BaseModule 子类）；否则回落到本模块内定义的
首个 BaseModule 子类。

- **module_obj** (`插件模块对象`): **返回值** (`模块类；未找到返回`): None

---


##### `_get_load_strategy(module_class: type)`

> **内部方法** 读取模块类的 get_load_strategy()

---


##### `get_loaded_path(name: str)`

获取已加载插件的源路径（热重载用）

- **name** (`插件名`): **返回值** (`插件路径；未知插件返回`): None

---

