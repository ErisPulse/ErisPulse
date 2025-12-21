# `ErisPulse.Core.Event.exceptions` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 事件系统异常处理模块

提供事件系统中可能发生的各种异常类型定义

---

## 类列表

### `class EventException(Exception)`

    事件系统基础异常

所有事件系统相关异常的基类

    
### `class CommandException(EventException)`

    命令处理异常

当命令处理过程中发生错误时抛出

    
### `class EventHandlerException(EventException)`

    事件处理器异常

当事件处理器执行过程中发生错误时抛出

    
### `class EventNotFoundException(EventException)`

    事件未找到异常

当尝试获取不存在的事件处理器时抛出

    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>