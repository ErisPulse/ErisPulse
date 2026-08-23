# `ErisPulse.CLI.commands.init` 模块

---

## 模块概述


Init 命令实现

交互式初始化 ErisPulse 项目

---

## 函数列表


### `_validate_project_name(name: str)`

项目名称校验：仅允许字母、数字、下划线、连字符和点号

---


## 类列表


### `class InitCommand(Command)`

init 命令

交互式初始化 ErisPulse 项目


#### 方法列表


##### `__init__()`

初始化 InitCommand 实例，创建包管理器

---


##### `_init_project(project_name: str, adapter_list: list | None = None, in_current_dir: bool = False)`

创建项目目录结构并生成配置文件

- **project_name** (`str`): 项目名称
- **adapter_list** (`list`): 适配器名称列表 (默认: None)
- **in_current_dir** (`bool`): 是否在当前目录初始化 (默认: False)
**返回值** (`bool`): 初始化成功返回 True，失败返回 False

---


##### `_get_full_example_config(adapter_list = None)`

生成完整的配置示例文本

配置注释跟随 CLI 语言（缺失语言回退英文），
文案键集中于 ``scaffold_text`` 的 ``cfg.*`` 键族维护。

- **adapter_list** (`list`): 适配器名称列表 (默认: None)
**返回值** (`str`): 完整配置示例字符串

---


##### `async _fetch_available_adapters()`

获取可用的适配器列表

**返回值** (`dict`): 适配器名称到描述的映射，获取失败时返回内置默认列表

---


##### `_interactive_init(project_name: str | None = None, force: bool = False, here: bool = False)`

交互式初始化项目，引导用户配置项目位置及基本参数

- **project_name** (`str`): 项目名称 (默认: None)
- **force** (`bool`): 是否强制覆盖已存在目录 (默认: False)
- **here** (`bool`): 是否在当前目录初始化 (默认: False)
**返回值** (`bool`): 初始化成功返回 True，失败返回 False

---


##### `_configure_adapters(project_path: Path)`

交互式配置适配器

- **project_path** (`Path`): 项目路径

---


##### `_install_adapters(adapter_names, adapters_info)`

安装选中的适配器

- **adapter_names** (`list`): 适配器简称列表
- **adapters_info** (`dict`): 适配器信息

---

