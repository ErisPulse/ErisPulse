# `ErisPulse.utils.cli.commands.adapter` 模块

> 最后更新：2026-01-26 15:55:43

---

## 模块概述


Adapter 命令实现

支持启用和禁用适配器

---

## 类列表


### `class AdapterCommand(Command)`

适配器管理命令


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


##### `_list_adapters(installed, show_all: bool)`

列出适配器状态

:param installed: 已安装的包信息
:param show_all: 是否显示所有适配器

---

