# `ErisPulse.utils.cli.commands.self_update` 模块

> 最后更新：2026-01-26 15:55:43

---

## 模块概述


Self-Update 命令实现

更新 ErisPulse SDK 本身

---

## 类列表


### `class SelfUpdateCommand(Command)`

自更新命令


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


##### `_select_target_version(versions, specified_version: str = None, include_pre: bool = False)`

选择目标版本

:param versions: 版本列表
:param specified_version: 用户指定的版本
:param include_pre: 是否包含预发布版本
:return: 目标版本号

---


##### `_select_from_version_list(versions, include_pre: bool = False)`

从版本列表中选择

:param versions: 版本列表
:param include_pre: 是否包含预发布版本
:return: 选中的版本号

---

