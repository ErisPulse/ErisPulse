# `ErisPulse.CLI.commands.install` 模块

> 最后更新：2026-02-03 22:38:11

---

## 模块概述


Install 命令实现

支持交互式和批量安装模块、适配器、CLI 扩展

---

## 类列表


### `class InstallCommand(Command)`

InstallCommand 类提供相关功能。


#### 方法列表


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

