# `ErisPulse.CLI.commands.install` 模块

---

## 模块概述


Install 命令实现

支持交互式和批量安装模块、适配器

---

## 类列表


### `class InstallCommand(Command)`

install 命令

安装模块/适配器包，支持交互式与批量安装


#### 方法列表


##### `__init__()`

初始化安装命令，创建包管理器实例

---


##### `_build_extra_pip_args(args)`

根据解析后的命令行参数构建额外的 pip 安装参数列表

- **args** (`Namespace`): 解析后的命令行参数

**返回值** (`list`): 额外的 pip 命令行参数列表

---


##### `_interactive_install(upgrade: bool = False, pre: bool = False)`

交互式安装向导，提供适配器、模块、搜索与自定义安装选项

- **upgrade** (`bool`): 是否升级已安装的包 (默认: False)
- **pre** (`bool`): 是否包含预发布版本 (默认: False)

---


##### `_install_adapters(remote_packages: dict, upgrade: bool, pre: bool)`

交互式选择并安装适配器

- **remote_packages** (`dict`): 远程包列表
- **upgrade** (`bool`): 是否升级已安装的包
- **pre** (`bool`): 是否包含预发布版本

---


##### `_install_modules(remote_packages: dict, upgrade: bool, pre: bool)`

交互式选择并安装模块

- **remote_packages** (`dict`): 远程包列表
- **upgrade** (`bool`): 是否升级已安装的包
- **pre** (`bool`): 是否包含预发布版本

---


##### `_install_search(remote_packages: dict, upgrade: bool, pre: bool)`

搜索并安装

> **内部方法** 

- **remote_packages** (`dict`): 远程包列表
- **upgrade** (`bool`): 是否升级
- **pre** (`bool`): 是否包含预发布版本

---


##### `_install_custom(upgrade: bool, pre: bool)`

自定义安装，提示用户输入包名并安装

- **upgrade** (`bool`): 是否升级已安装的包
- **pre** (`bool`): 是否包含预发布版本

---

