# `ErisPulse.CLI.commands.list` 模块

---

## 模块概述


List 命令实现

列出已安装的组件

---

## 类列表


### `class ListCommand(Command)`

list 命令

列出已安装的组件


#### 方法列表


##### `__init__()`

初始化 ListCommand，创建包管理器实例

---


##### `_print_installed_packages(pkg_type: str, outdated_only: bool = False)`

以表格形式打印已安装的模块或适配器

- **pkg_type** (`str`): 组件类型 (modules 或 adapters)
- **outdated_only** (`bool`): 是否仅显示可升级的包 (默认: False)

---


##### `_is_package_outdated(package_name: str, current_version: str)`

判断指定包是否存在较新的远程版本

- **package_name** (`str`): 包名
- **current_version** (`str`): 当前已安装的版本号

**返回值** (`bool`): 存在更新版本返回 True，否则返回 False

---


##### `_print_package_scripts(packages: dict)`

发现并展示已安装模块包注册的 console_scripts 入口

- **packages** (`dict`): 模块信息字典 {name: {package, version, ...}}

---

