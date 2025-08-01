# 📦 `ErisPulse.Core.exceptions` 模块

<sup>自动生成于 2025-08-01 14:55:50</sup>

---

## 模块概述


ErisPulse 全局异常处理系统

提供统一的异常捕获和格式化功能，支持同步和异步代码的异常处理。

---

## 🛠️ 函数

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

### `setup_async_exception_handler(loop: asyncio.AbstractEventLoop = None)`

设置异步异常处理器

:param loop: 事件循环，如果为None则使用当前事件循环

---

## 🏛️ 类

### `class ExceptionHandler`

异常处理器类


#### 🧰 方法

##### `format_exception(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any)`

格式化异常信息

:param exc_type: 异常类型
:param exc_value: 异常值
:param exc_traceback: 追踪信息
:return: 格式化后的异常信息

---

##### `format_async_exception(exception: Exception)`

格式化异步异常信息

:param exception: 异常对象
:return: 格式化后的异常信息

---

<sub>文档最后更新于 2025-08-01 14:55:50</sub>