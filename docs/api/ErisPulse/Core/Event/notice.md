# `ErisPulse.Core.Event.notice` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 通知处理模块

提供基于装饰器的通知事件处理功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持好友、群组等不同类型通知
2. 支持成员变动等细粒度事件</p></div>

---

## 类列表

### `class NoticeHandler`

    通知事件处理器

提供通知事件处理功能

    
#### 方法列表

##### `on_notice(priority: int = 0)`

    通用通知事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_notice_handler(handler: Callable)`

    取消注册通用通知事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `on_friend_add(priority: int = 0)`

    好友添加通知事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_friend_add_handler(handler: Callable)`

    取消注册好友添加通知事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `on_friend_remove(priority: int = 0)`

    好友删除通知事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_friend_remove_handler(handler: Callable)`

    取消注册好友删除通知事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `on_group_increase(priority: int = 0)`

    群成员增加通知事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_group_increase_handler(handler: Callable)`

    取消注册群成员增加通知事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `on_group_decrease(priority: int = 0)`

    群成员减少通知事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_group_decrease_handler(handler: Callable)`

    取消注册群成员减少通知事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `_clear_notice_handlers()`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
清除所有已注册的通知处理器

:return: 被清除的处理器数量

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>