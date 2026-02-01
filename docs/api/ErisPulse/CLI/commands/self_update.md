# `ErisPulse.CLI.commands.self_update` 模块

> 最后更新：2026-02-02 05:58:18

---

## 模块概述


Self-Update 命令实现

更新 ErisPulse SDK 本身

---

## 类列表


### `class SelfUpdateCommand(Command)`

SelfUpdateCommand 类提供相关功能。


#### 方法列表


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

