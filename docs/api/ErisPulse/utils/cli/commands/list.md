# `ErisPulse.utils.cli.commands.list` 模块

> 最后更新：2026-01-26 15:55:43

---

## 模块概述


List 命令实现

列出已安装的组件

---

## 类列表


### `class ListCommand(Command)`

列表命令


#### 方法列表


##### `__init__()`

初始化命令

---


##### `add_arguments(parser: ArgumentParser)`

添加命令参数

---


##### `execute(args)`

执行命令

---


##### `_print_installed_packages(pkg_type: str, outdated_only: bool = False)`

打印已安装包信息

:param pkg_type: 包类型 (modules/adapters/cli)
:param outdated_only: 是否只显示可升级的包

---


##### `_is_package_outdated(package_name: str, current_version: str)`

检查包是否过时

:param package_name: 包名
:param current_version: 当前版本
:return: 是否有新版本可用

---

