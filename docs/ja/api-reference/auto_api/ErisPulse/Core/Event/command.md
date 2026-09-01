# `ErisPulse.Core.Event.command` 模块

---

## 模块概述


ErisPulse 命令处理模块

提供基于装饰器的命令注册和处理功能

命令的**用户权限 ACL**（谁/谁不能执行）统一收敛到控制面 ``ErisPulse.scope.commands``
（运行时 ``scope.allow_user`` / ``scope.deny_user``，命令名支持 glob），
本模块不再单独维护权限配置。

> **提示**
> 1. 支持命令别名和命令组
> 2. 支持命令权限控制（master / permission 函数 / 控制面 ACL）
> 3. 支持命令帮助系统
> 4. 支持等待用户回复交互

---

## 类列表


### `class CommandHandler`

命令处理器

提供命令注册、处理和管理功能


#### 方法列表


##### `_refresh_command_config()`

从配置读取命令解析相关参数

支持配置热更新：``config.updated`` 事件触发后再次调用即可刷新
前缀 / 大小写 / 空格前缀 / 是否须 @机器人 等解析参数。

---


##### `_on_config_updated(_data: dict)`

配置变更回调：刷新命令解析参数，实现热更新

---


##### `_scope()`

> **内部方法**
延迟获取控制面单例（避免模块初始化阶段的循环依赖）

**返回值** (`scope`): 单例（ScopeManager）

---


##### `allow_user(command_name: str, platform: str, user_id: str, persist: bool = True)`

将用户加入命令的 allow 名单（白名单非空时仅名单内用户可执行）

委托给控制面 ``scope.allow_user``；命令名支持 glob。

- **command_name** (`命令名称（支持`): glob / ``re:`` 正则）
- **platform** (`用户所属平台`): - **user_id**: 用户 ID
- **persist** (`是否持久化到配置`): (默认: True)

**示例**:
```python
>>> command.allow_user("restart", "onebot11", "123456")
```

---


##### `deny_user(command_name: str, platform: str, user_id: str, persist: bool = True)`

将用户加入命令的 deny 名单（deny 优先于 allow 与默认权限）

委托给控制面 ``scope.deny_user``；命令名支持 glob。

- **command_name** (`命令名称（支持`): glob / ``re:`` 正则）
- **platform** (`用户所属平台`): - **user_id**: 用户 ID
- **persist** (`是否持久化到配置`): (默认: True)

**示例**:
```python
>>> command.deny_user("restart", "onebot11", "666")
```

---


##### `remove_acl(command_name: str, persist: bool = True)`

清除命令的用户黑白名单（恢复开发者默认权限逻辑）

委托给控制面 ``scope.remove_acl``；命令名支持 glob。

- **command_name** (`命令名称（支持`): glob / ``re:`` 正则）
- **persist** (`是否持久化到配置`): (默认: True)
**返回值** (`是否存在并被清除`): 
**示例**:
```python
>>> command.remove_acl("restart")
True
```

---


##### `get_acl(command_name: str)`

查询命令当前的用户黑白名单

委托给控制面 ``scope.get_acl``；命令名支持 glob。

- **command_name** (`命令名称（支持`): glob / ``re:`` 正则）
**返回值** (`{"allow":`): [...], "deny": [...]}（用户标识 "platform:user_id"）

**示例**:
```python
>>> command.get_acl("restart")
{'allow': ['onebot11:123456'], 'deny': []}
```

---


##### `__call__(name: str | list[str] | None = None, aliases: list[str] | None = None, group: str | None = None, priority: int = 0, permission: Callable | None = None, help: str | None = None, usage: str | None = None, hidden: bool = False, master: bool = False)`

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


##### `async wait_reply(event: dict[str, Any], prompt: str | None = None, timeout: float = DEFAULT_WAIT_TIMEOUT_SECS, callback: Callable[[dict[str, Any]], Awaitable[Any]] | None = None, validator: Callable[[dict[str, Any]], bool] | None = None, method: str = DEFAULT_SEND_METHOD, pattern: str | None = None, regex: str | None = None)`

等待用户回复

- **event** (`原始事件数据`): - **prompt**: 提示消息，如果提供会发送给用户
- **timeout** (`等待超时时间(秒)`): - **callback**: 回调函数，当收到回复时执行
- **validator** (`验证函数，用于验证回复是否有效`): - **method**: 发送方法，默认为 "Text"
- **pattern** (`glob`): 通配符（``*`` / ``?`` / ``[seq]``），回复文本不匹配时继续等待
- **regex** (`正则表达式，回复文本不匹配时继续等待（与`): pattern 同时给定时须都匹配）
**返回值**: 用户回复的事件数据，如果超时则返回None

---


##### `async _handle_message(event: dict[str, Any])`

处理消息事件中的命令

> **内部方法**
内部使用的方法，用于从消息中解析并执行命令

- **event**: 消息事件数据

---


##### `async _try_execute_command(event: 'Event', original_text: str, check_text: str, prefix: str)`

尝试执行命令

> **内部方法**
内部使用的方法，用于尝试解析和执行命令

- **event** (`消息事件数据`): - **original_text**: 原始文本内容
- **check_text** (`用于检查的文本内容（可能已转换为小写）`): - **prefix**: 已匹配的命令前缀（可能已转换为小写）
**返回值**: 是否成功执行命令

---


##### `async _check_pending_reply(event: 'Event')`

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


##### `help(command_name: str | None = None, show_hidden: bool = False)`

生成帮助信息

- **command_name** (`命令名称，如果为None则生成所有命令的帮助`): - **show_hidden**: 是否显示隐藏命令
**返回值**: 帮助信息字符串

---

