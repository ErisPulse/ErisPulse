# 📦 `ErisPulse.Core.raiserr` 模块

<sup>自动生成于 2025-07-28 05:47:33</sup>

---

## 模块概述


ErisPulse 错误管理系统

提供全局异常捕获功能。不再推荐使用自定义错误注册功能。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 请使用Python原生异常抛出方法
2. 系统会自动捕获并格式化所有未处理异常
3. 注册功能已标记为弃用，将在未来版本移除</p></div>

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

## 🏛️ 类

### `class Error`

错误管理器

<div class='admonition attention'><p class='admonition-title'>已弃用</p><p>请使用Python原生异常抛出方法 | 2025-07-18</p></div>

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 注册功能将在未来版本移除
2. 请直接使用raise Exception("message")方式抛出异常</p></div>


#### 🧰 方法

##### `register(name: str, doc: str = '', base: Type[Exception] = Exception)`

注册新的错误类型

<div class='admonition attention'><p class='admonition-title'>已弃用</p><p>请使用Python原生异常抛出方法 | 2025-07-18</p></div>

:param name: 错误类型名称
:param doc: 错误描述文档
:param base: 基础异常类
:return: 注册的错误类

---

##### `__getattr__(name: str)`

动态获取错误抛出函数

<div class='admonition attention'><p class='admonition-title'>已弃用</p><p>请使用Python原生异常抛出方法 | 2025-07-18</p></div>

:param name: 错误类型名称
:return: 错误抛出函数

<dt>异常</dt><dd><code>AttributeError</code> 当错误类型未注册时抛出</dd>

---

##### `info(name: Optional[str] = None)`

获取错误信息

<div class='admonition attention'><p class='admonition-title'>已弃用</p><p>此功能将在未来版本移除 | 2025-07-18</p></div>

:param name: 错误类型名称(可选)
:return: 错误信息字典

---

<sub>文档最后更新于 2025-07-28 05:47:33</sub>