# `ErisPulse.Core.exceptions` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 全局异常处理系统

提供统一的异常捕获和格式化功能，支持同步和异步代码的异常处理。

---

## 函数列表

### `global_exception_handler(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any)`

全局异常处理器

:param exc_type: 异常类型
:param exc_value: 异常值
:param exc_traceback: 追踪信息

---

### `async_exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any])`

异步异常处理器

:param loop: 事件循环
:param context: 上下文字典

---

### `setup_async_loop(loop: asyncio.AbstractEventLoop = None)`

为指定的事件循环设置异常处理器

:param loop: 事件循环实例，如果为None则使用当前事件循环

---

## 类列表

### `class ExceptionHandler`

    ExceptionHandler 类提供相关功能。

    
#### 方法列表

##### `format_exception(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any)`

    :param exc_type: 异常类型
:param exc_value: 异常值
:param exc_traceback: 追踪信息
:return: 格式化后的异常信息

    ---
    
##### `format_async_exception(exception: Exception)`

    :param exception: 异常对象
:return: 格式化后的异常信息

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>