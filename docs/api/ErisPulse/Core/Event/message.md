# `ErisPulse.Core.Event.message` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 消息处理模块

提供基于装饰器的消息事件处理功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持私聊、群聊消息分类处理
2. 支持@消息特殊处理
3. 支持自定义条件过滤</p></div>

---

## 类列表

### `class MessageHandler`

    消息事件处理器

提供不同类型消息事件的处理功能

    
#### 方法列表

##### `on_message(priority: int = 0)`

    消息事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_message_handler(handler: Callable)`

    取消注册消息事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `on_private_message(priority: int = 0)`

    私聊消息事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_private_message_handler(handler: Callable)`

    取消注册私聊消息事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `on_group_message(priority: int = 0)`

    群聊消息事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_group_message_handler(handler: Callable)`

    取消注册群聊消息事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `on_at_message(priority: int = 0)`

    @消息事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_at_message_handler(handler: Callable)`

    取消注册@消息事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `_clear_message_handlers()`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
清除所有已注册的消息处理器

:return: 被清除的处理器数量

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>