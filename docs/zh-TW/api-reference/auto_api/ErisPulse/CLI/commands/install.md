# `ErisPulse.CLI.commands.install` 模块

---

## 模块概述


Install 命令实现

支持交互式和批量安装模块、适配器

---

## 类列表


### `class InstallCommand(Command)`

InstallCommand 类提供相关功能。


#### 方法列表


##### `_install_search(remote_packages: dict, upgrade: bool, pre: bool)`

搜索并安装

> **内部方法** 

- **remote_packages** (`dict`): 远程包列表
- **upgrade** (`bool`): 是否升级
- **pre** (`bool`): 是否包含预发布版本

---

