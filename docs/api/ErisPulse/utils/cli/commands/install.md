# `ErisPulse.utils.cli.commands.install` 模块

> 最后更新：2026-01-26 15:55:43

---

## 模块概述


Install 命令实现

支持交互式和批量安装模块、适配器、CLI 扩展

---

## 类列表


### `class InstallCommand(Command)`

安装命令


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


##### `_interactive_install(upgrade: bool = False, pre: bool = False)`

交互式安装界面

:param upgrade: 是否升级模式
:param pre: 是否包含预发布版本

---


##### `_install_adapters(remote_packages: dict, upgrade: bool, pre: bool)`

安装适配器

---


##### `_install_modules(remote_packages: dict, upgrade: bool, pre: bool)`

安装模块

---


##### `_install_cli_extensions(remote_packages: dict, upgrade: bool, pre: bool)`

安装 CLI 扩展

---


##### `_install_custom(upgrade: bool, pre: bool)`

自定义安装

---

