# 📦 `ErisPulse.Core.raiserr` 模块

*自动生成于 2025-07-22 16:35:32*

---

## 模块概述

ErisPulse 错误管理系统

提供全局异常捕获功能。不再推荐使用自定义错误注册功能。

💡 **提示**：

1. 请使用Python原生异常抛出方法
2. 系统会自动捕获并格式化所有未处理异常
3. 注册功能已标记为弃用，将在未来版本移除

---

## 🛠️ 函数

### `global_exception_handler`

全局异常处理器

:param exc_type: 异常类型
:param exc_value: 异常值
:param exc_traceback: 追踪信息

---

### `async_exception_handler`

异步异常处理器

:param loop: 事件循环
:param context: 上下文字典

---

## 🏛️ 类

### `Error`

错误管理器

⚠️ **已弃用**：请使用Python原生异常抛出方法 | 2025-07-18

💡 **提示**：

1. 注册功能将在未来版本移除
2. 请直接使用raise Exception("message")方式抛出异常


#### 🧰 方法

##### `register`

注册新的错误类型

⚠️ **已弃用**：请使用Python原生异常抛出方法 | 2025-07-18

:param name: 错误类型名称
:param doc: 错误描述文档
:param base: 基础异常类
:return: 注册的错误类

---

##### `__getattr__`

动态获取错误抛出函数

⚠️ **已弃用**：请使用Python原生异常抛出方法 | 2025-07-18

:param name: 错误类型名称
:return: 错误抛出函数

⚠️ **可能抛出**: `AttributeError` - 当错误类型未注册时抛出

---

##### `info`

获取错误信息

⚠️ **已弃用**：此功能将在未来版本移除 | 2025-07-18

:param name: 错误类型名称(可选)
:return: 错误信息字典

---


*文档最后更新于 2025-07-22 16:35:32*