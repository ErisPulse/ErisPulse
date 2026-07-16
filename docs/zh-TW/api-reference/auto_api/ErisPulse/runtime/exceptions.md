# `ErisPulse.runtime.exceptions` 模块

---

## 模块概述


ErisPulse 全局异常处理系统

提供统一的异常捕获和格式化功能，支持同步和异步代码的异常处理。
在异常发生时自动生成友好的拼写纠错提示（"你是不是想写 xxx？"）。

---

## 函数列表


### `_t(key: str)`

> **内部方法**
尝试用 i18n 翻译，失败时用英文 fallback

---


### `_get_error_logger()`

> **内部方法**
获取错误日志输出函数，优先使用框架 logger，失败时 fallback 到 stderr

---


### `global_exception_handler(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any)`

全局异常处理器

- **exc_type** (`异常类型`): - **exc_value**: 异常值
- **exc_traceback**: 追踪信息

---


### `async_exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any])`

异步异常处理器

- **loop** (`事件循环`): - **context**: 上下文字典

---


### `setup_exception_handling()`

设置全局异常处理系统

包括同步异常和异步异常的处理钩子

---


## 类列表


### `class ExceptionHandler`

ExceptionHandler 类提供相关功能。


#### 方法列表


##### `format_exception(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any)`

格式化异常信息

- **exc_type** (`异常类型`): - **exc_value**: 异常值
- **exc_traceback** (`追踪信息`): **返回值**: 格式化后的异常信息

---


##### `format_async_exception(exception: Exception)`

格式化异步异常信息

- **exception** (`异常对象`): **返回值**: 格式化后的异常信息

---


##### `generate_hints(exc_value: BaseException, exc_traceback: Any = None)`

为异常生成友好的提示行

根据异常类型智能推断：
- BaseException 子类（CancelledError / KeyboardInterrupt）：关停/取消场景
- AttributeError: 查找对象上最相似的属性，给出“你是不是想写 xxx”
- ImportError / ModuleNotFoundError: 给出拼写建议
- NameError / KeyError: 从上下文中找最相近的名称
- TypeError: 多种子场景（await / 缺参 / 不可调用 / 不可下标）
- RuntimeError: 事件循环相关多种场景
- RecursionError / TimeoutError / ConnectionError: 常见运行期错误

- **exc_value** (`异常对象`): - **exc_traceback**: traceback 对象（可选，用于上下文推断）
**返回值**: 提示行列表，无提示时为空列表

---


##### `format_exception_with_hints(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any)`

格式化异常信息并附带友好提示

- **exc_type** (`异常类型`): - **exc_value**: 异常值
- **exc_traceback** (`追踪信息`): **返回值**: 格式化后的异常信息（可能包含多行提示）

---

