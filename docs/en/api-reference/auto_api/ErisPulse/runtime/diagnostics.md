# `ErisPulse.runtime.diagnostics` 模块

---

## 模块概述


ErisPulse 异常诊断模块

从异常的 traceback 中提取「用户代码帧」摘要，过滤掉框架内部帧，
让开发者在默认日志级别下即可定位模块/适配器加载或初始化失败的具体位置，
无需手动重开 DEBUG 级别查看完整堆栈。

> **提示**
> 1. extract_user_frame: 从异常对象提取结构化的用户代码帧信息
> 2. format_diagnostic_block: 生成可日志输出的多行诊断文本
> 3. log_diagnostic: 直接将诊断信息写入 logger（最常用）

---

## 函数列表


### `_get_framework_root()`

获取 ErisPulse 包根目录，用于判定框架内部帧

> **内部方法**
结果会被缓存，避免每次调用都查询 ``ErisPulse.__file__``

**返回值** (`Path`): ErisPulse 包目录（如 ``.../src/ErisPulse``）

---


### `_is_framework_frame(filename: str)`

判断给定文件是否属于 ErisPulse 框架内部代码

> **内部方法**
通过判断文件路径是否位于 ErisPulse 包目录下来识别框架帧。

- **filename** (`str`): 帧对应的文件路径
**返回值** (`bool`): 是否为框架内部帧

---


### `_short_filename(filename: str)`

将绝对路径缩短为更易读的相对路径表示

> **内部方法**
优先相对于当前工作目录；其次相对于 ErisPulse 包父目录；
都不可行时退化为文件名。

- **filename** (`str`): 绝对文件路径
**返回值** (`str`): 缩短后的路径（统一使用 ``/`` 分隔符）

---


### `extract_user_frame(exc: BaseException, depth: int = 3)`

从异常 traceback 提取「用户代码帧」摘要

过滤掉 ErisPulse 框架内部帧，保留最靠近错误发生点的 ``depth`` 个用户代码帧。
用于在加载/初始化失败时快速定位用户代码中的出错位置。

- **exc** (`BaseException`): 异常对象
- **depth** (`int`): 最多保留的用户帧数量（从最深处开始计数）
**返回值** (`dict`): 结构化诊断信息，包含:
    - ``frames``: 用户代码帧列表，每项含 ``file``/``lineno``/``func``/``source``
    - ``exc_type``: 异常类型名
    - ``exc_value``: 异常消息字符串
    - ``has_traceback``: 是否存在可用的 traceback

**示例**:
```python
>>> try:
...     1 / 0
... except Exception as e:
...     info = extract_user_frame(e)
...     info["exc_type"]
'ZeroDivisionError'
```

---


### `_t(key: str)`

尝试用 i18n 翻译，失败时回退到英文兜底

> **内部方法**
与 ``runtime.exceptions._t`` 相同的容错策略，确保 i18n 未就绪时
诊断信息仍可输出。

- **key** (`str`): i18n 键
- **kwargs** (`占位符参数`): **返回值** (`str`): 翻译后的文本

---


### `format_diagnostic_block(exc: BaseException)`

生成可日志输出的多行诊断文本

将 ``extract_user_frame`` 的结果格式化为带缩进引导符（``→``）的多行字符串，
末尾附加查看完整堆栈的提示行。

- **exc** (`BaseException`): 异常对象
- **hint_key** (`str`): | None 自定义提示行的 i18n key（默认使用通用提示）
- **candidates** (`list[str]`): | None 相似名称候选，用于附加「你是不是想写」提示
- **depth** (`int`): 最多保留的用户帧数量
**返回值** (`str`): 多行诊断文本；无可用信息时返回空字符串

**示例**:
```python
>>> try:
...     import nonexistent_module
... except Exception as e:
...     print(format_diagnostic_block(e))
```

---


### `log_diagnostic(exc: BaseException)`

将异常诊断信息写入日志

最常用的入口：在 ``except`` 块中调用，自动提取用户代码帧并以
``ERROR`` 级别输出多行诊断信息。

- **exc** (`BaseException`): 异常对象
- **hint_key** (`str`): | None 自定义提示行的 i18n key
- **candidates** (`list[str]`): | None 相似名称候选
- **depth** (`int`): 最多保留的用户帧数量
- **logger** (`Any`): 指定 logger 实例（默认使用 ``Core.logger.logger``）

**示例**:
```python
>>> try:
...     risky_init()
... except Exception as e:
...     log_diagnostic(e)
```

---

