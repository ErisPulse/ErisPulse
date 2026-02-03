# `ErisPulse.CLI.commands.init` 模块

> 最后更新：2026-02-03 22:38:11

---

## 模块概述


Init 命令实现

交互式初始化 ErisPulse 项目

---

## 类列表


### `class InitCommand(Command)`

InitCommand 类提供相关功能。


#### 方法列表


##### `_init_project(project_name: str, adapter_list: list = None)`

初始化新项目

:param project_name: 项目名称
:param adapter_list: 需要初始化的适配器列表
:return: 是否初始化成功

---


##### `async async _fetch_available_adapters()`

从云端获取可用适配器列表

:return: 适配器名称到描述的映射

---


##### `_configure_adapters_interactive_sync(project_path: str = None)`

交互式配置适配器的同步版本

:param project_path: 项目路径

---


##### `_install_adapters(adapter_names, adapters_info)`

安装选中的适配器

:param adapter_names: 适配器名称列表
:param adapters_info: 适配器信息字典

---


##### `_interactive_init(project_name: str = None, force: bool = False)`

交互式初始化项目

:param project_name: 项目名称
:param force: 是否强制覆盖
:return: 是否初始化成功

---

