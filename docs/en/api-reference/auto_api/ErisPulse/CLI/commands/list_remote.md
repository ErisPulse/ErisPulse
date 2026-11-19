# `ErisPulse.CLI.commands.list_remote` 模块

---

## 模块概述


List-Remote 命令实现

列出远程可用的组件

---

## 类列表


### `class ListRemoteCommand(Command)`

list-remote 命令

列出远程可用的组件


#### 方法列表


##### `__init__()`

初始化 ListRemoteCommand，创建包管理器实例

---


##### `_print_group(title: str, items: dict, style: str, name_col: str)`

以表格形式打印一组远程组件

- **title** (`str`): 分组标题
- **items** (`dict`): 组件信息字典
- **style** (`str`): 名称列的显示样式
- **name_col** (`str`): 名称列的列标题

---

