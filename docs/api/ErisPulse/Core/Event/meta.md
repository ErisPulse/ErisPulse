# `ErisPulse.Core.Event.meta` 模块

<sup>更新时间: 2025-08-19 05:32:03</sup>

---

## 模块概述


ErisPulse 元事件处理模块

提供基于装饰器的元事件处理功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持连接、断开连接等生命周期事件
2. 适用于系统状态监控和初始化操作</p></div>

---

## 类列表

### `class MetaHandler`

    MetaHandler 类提供相关功能。

    
#### 方法列表

##### `on_meta(priority: int = 0)`

    通用元事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_meta_handler(handler: Callable)`

    取消注册通用元事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `on_connect(priority: int = 0)`

    连接事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_connect_handler(handler: Callable)`

    取消注册连接事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `on_disconnect(priority: int = 0)`

    断开连接事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_disconnect_handler(handler: Callable)`

    取消注册断开连接事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
##### `on_heartbeat(priority: int = 0)`

    心跳事件装饰器

:param priority: 处理器优先级
:return: 装饰器函数

    ---
    
##### `remove_heartbeat_handler(handler: Callable)`

    取消注册心跳事件处理器

:param handler: 要取消注册的处理器
:return: 是否成功取消注册

    ---
    
<sub>文档最后更新于 2025-08-19 05:32:03</sub>