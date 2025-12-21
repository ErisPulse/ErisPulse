# `ErisPulse.Core.Event.command` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 命令处理模块

提供基于装饰器的命令注册和处理功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持命令别名和命令组
2. 支持命令权限控制
3. 支持命令帮助系统
4. 支持等待用户回复交互</p></div>

---

## 类列表

### `class CommandHandler`

    命令处理器

提供命令注册、处理和管理功能

    
#### 方法列表

##### `__call__(name: Union[str, List[str]] = None, aliases: List[str] = None, group: str = None, priority: int = 0, permission: Callable = None, help: str = None, usage: str = None, hidden: bool = False)`

    命令装饰器

:param name: 命令名称，可以是字符串或字符串列表
:param aliases: 命令别名列表
:param group: 命令组名称
:param priority: 处理器优先级
:param permission: 权限检查函数，返回True时允许执行命令
:param help: 命令帮助信息
:param usage: 命令使用方法
:param hidden: 是否在帮助中隐藏命令
:return: 装饰器函数

    ---
    
##### `unregister(handler: Callable)`

    注销命令处理器

:param handler: 要注销的命令处理器
:return: 是否成功注销

    ---
    
##### async `async wait_reply(event: Dict[str, Any], prompt: str = None, timeout: float = 60.0, callback: Callable[[Dict[str, Any]], Awaitable[Any]] = None, validator: Callable[[Dict[str, Any]], bool] = None)`

    等待用户回复

:param event: 原始事件数据
:param prompt: 提示消息，如果提供会发送给用户
:param timeout: 等待超时时间(秒)
:param callback: 回调函数，当收到回复时执行
:param validator: 验证函数，用于验证回复是否有效
:return: 用户回复的事件数据，如果超时则返回None

    ---
    
##### async `async _handle_message(event: Dict[str, Any])`

    处理消息事件中的命令

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
内部使用的方法，用于从消息中解析并执行命令

:param event: 消息事件数据

    ---
    
##### async `async _check_pending_reply(event: Dict[str, Any])`

    检查是否是等待回复的消息

:param event: 消息事件数据

    ---
    
##### async `async _send_permission_denied(event: Dict[str, Any])`

    发送权限拒绝消息

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
内部使用的方法

:param event: 事件数据

    ---
    
##### async `async _send_command_error(event: Dict[str, Any], error: str)`

    发送命令错误消息

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
内部使用的方法

:param event: 事件数据
:param error: 错误信息

    ---
    
##### `_clear_commands()`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
清除所有已注册的命令

:return: 被清除的命令数量

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
    
##### `get_visible_commands()`

    获取所有可见命令（非隐藏命令）

:return: 可见命令信息字典

    ---
    
##### `help(command_name: str = None, show_hidden: bool = False)`

    生成帮助信息

:param command_name: 命令名称，如果为None则生成所有命令的帮助
:param show_hidden: 是否显示隐藏命令
:return: 帮助信息字符串

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>