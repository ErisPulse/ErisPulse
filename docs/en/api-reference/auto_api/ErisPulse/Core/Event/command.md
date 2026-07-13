# `ErisPulse.Core.Event.command` 模块

---

## 模块概述


ErisPulse 命令处理模块

提供基于装饰器的命令注册和处理功能

> **提示**
> 1. 支持命令别名和命令组
> 2. 支持命令权限控制
> 3. 支持命令帮助系统
> 4. 支持等待用户回复交互

---

## 类列表


### `class CommandHandler`

命令处理器

提供命令注册、处理和管理功能


#### 方法列表


##### `__call__(name: str | list[str] = None, aliases: list[str] = None, group: str = None, priority: int = 0, permission: Callable = None, help: str = None, usage: str = None, hidden: bool = False, master: bool = False)`

命令装饰器

- **name** (`命令名称，可以是字符串或字符串列表`): - **aliases**: 命令别名列表
- **group** (`命令组名称`): - **priority**: 处理器优先级
- **permission** (`权限检查函数，返回True时允许执行命令`): - **help**: 命令帮助信息
- **usage** (`命令使用方法`): - **hidden**: 是否在帮助中隐藏命令
- **master** (`是否仅允许框架主人执行（框架自动检查`): ``master.is_master(event)``）
**返回值**: 装饰器函数

---


##### `unregister(handler: Callable)`

注销命令处理器

- **handler** (`要注销的命令处理器`): **返回值**: 是否成功注销

---


##### `unregister_by_owner(owner: str)`

> **内部方法**
按归属者精确移除命令

- **owner** (`归属者（模块名）`): **返回值**: 移除的命令数量

---


##### `async wait_reply(event: dict[str, Any], prompt: str = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, callback: Callable[[dict[str, Any]], Awaitable[Any]] = None, validator: Callable[[dict[str, Any]], bool] = None, method: str = DEFAULT_SEND_METHOD)`

等待用户回复

- **event** (`原始事件数据`): - **prompt**: 提示消息，如果提供会发送给用户
- **timeout** (`等待超时时间(秒)`): - **callback**: 回调函数，当收到回复时执行
- **validator** (`验证函数，用于验证回复是否有效`): - **method**: 发送方法，默认为 "Text"
**返回值**: 用户回复的事件数据，如果超时则返回None

---


##### `async _handle_message(event: dict[str, Any])`

处理消息事件中的命令

> **内部方法**
内部使用的方法，用于从消息中解析并执行命令

- **event**: 消息事件数据

---


##### `async _try_execute_command(event: dict[str, Any], original_text: str, check_text: str, prefix: str)`

尝试执行命令

> **内部方法**
内部使用的方法，用于尝试解析和执行命令

- **event** (`消息事件数据`): - **original_text**: 原始文本内容
- **check_text** (`用于检查的文本内容（可能已转换为小写）`): - **prefix**: 已匹配的命令前缀（可能已转换为小写）
**返回值**: 是否成功执行命令

---


##### `async _check_pending_reply(event: dict[str, Any])`

检查是否是等待回复的消息

- **event**: 消息事件数据

---


##### `async _send_permission_denied(event: dict[str, Any])`

发送权限拒绝消息

> **内部方法**
内部使用的方法

- **event**: 事件数据

---


##### `async _send_command_error(event: dict[str, Any], error: str)`

发送命令错误消息

> **内部方法**
内部使用的方法

- **event** (`事件数据`): - **error**: 错误信息

---


##### `bind_message_handler(handler: BaseEventHandler)`

> **内部方法**
绑定到共享的消息事件处理器

将命令分发器 _handle_message 注册到共享的 BaseEventHandler 中，
使命令处理和通用消息处理共享同一个优先级队列。

- **handler** (`MessageHandler`): 持有的 BaseEventHandler 实例

---


##### `_register_dispatcher()`

> **内部方法**
将命令分发器注册到共享 handler（如尚未注册）

---


##### `_clear_commands()`

> **内部方法**
清除所有已注册的命令，并从共享 handler 中注销命令分发器

**返回值**: 被清除的命令数量

---


##### `get_command(name: str)`

获取命令信息

- **name** (`命令名称`): **返回值**: 命令信息字典，如果不存在则返回None

---


##### `get_commands()`

获取所有命令

**返回值**: 命令信息字典

---


##### `get_group_commands(group: str)`

获取命令组中的命令

- **group** (`命令组名称`): **返回值**: 命令名称列表

---


##### `get_visible_commands()`

获取所有可见命令（非隐藏命令）

**返回值**: 可见命令信息字典

---


##### `help(command_name: str = None, show_hidden: bool = False)`

生成帮助信息

- **command_name** (`命令名称，如果为None则生成所有命令的帮助`): - **show_hidden**: 是否显示隐藏命令
**返回值**: 帮助信息字符串

---

