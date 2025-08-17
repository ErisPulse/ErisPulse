# `ErisPulse.Core.Event.cmd` 模块

<sup>更新时间: 2025-08-17 09:01:35</sup>

---

## 模块概述


ErisPulse 命令处理模块

提供基于装饰器的命令注册和处理功能

---

## 类列表

### `class CommandHandler`

命令处理器

提供命令注册、解析和执行功能


#### 方法列表

##### `__init__()`

初始化命令处理器

---

##### `__call__(name: Union[str, List[str]] = None, aliases: List[str] = None, group: str = None, priority: int = 0, help: str = None, usage: str = None)`

命令装饰器

:param name: 命令名称，可以是字符串或字符串列表
:param aliases: 命令别名列表
:param group: 命令组名称
:param priority: 处理器优先级
:param help: 命令帮助信息
:param usage: 命令使用方法
:return: 装饰器函数

---

##### async `async _handle_message(event: Dict[str, Any])`

处理消息事件中的命令

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
内部使用的方法，用于从消息中解析并执行命令

:param event: 消息事件数据

---

##### `get_command(name: str)`

获取命令信息

:param name: 命令名称
:return: 命令信息字典，如果不存在则返回None

---

##### `get_commands()`

获取所有命令

:return: 命令信息字典

---

##### `get_group_commands(group: str)`

获取命令组中的命令

:param group: 命令组名称
:return: 命令名称列表

---

##### `help(command_name: str = None)`

生成帮助信息

:param command_name: 命令名称，如果为None则生成所有命令的帮助
:return: 帮助信息字符串

---

<sub>文档最后更新于 2025-08-17 09:01:35</sub>