# `ErisPulse.CLI.commands.self_update` 模块

---

## 模块概述


Self-Update 命令实现

更新 ErisPulse SDK 本身

---

## 类列表


### `class SelfUpdateCommand(Command)`

self-update 命令

更新 ErisPulse SDK 本身


#### 方法列表


##### `__init__()`

初始化 SelfUpdateCommand，创建包管理器实例

---


##### `_select_target_version(versions, specified_version: str = None, include_pre: bool = False)`

交互式选择目标更新版本

- **versions** (`list`): 可用版本信息列表
- **specified_version** (`str`): 指定的版本号 (默认: None)
- **include_pre** (`bool`): 是否包含预发布版本 (默认: False)

**返回值** (`str`): 选定的目标版本号，取消时返回 None

---


##### `_select_from_version_list(versions, include_pre: bool = False)`

以分页列表形式展示版本并供用户选择

- **versions** (`list`): 可用版本信息列表
- **include_pre** (`bool`): 是否包含预发布版本 (默认: False)

**返回值** (`str`): 选定的目标版本号，返回时返回 None

---


##### `_parse_version_input(user_input: str, version_list: list)`

解析用户输入的版本序号或版本号字符串

- **user_input** (`str`): 用户输入内容
- **version_list** (`list`): 可用版本信息列表

**返回值** (`str`): 匹配到的版本号，无匹配时返回 None

---

