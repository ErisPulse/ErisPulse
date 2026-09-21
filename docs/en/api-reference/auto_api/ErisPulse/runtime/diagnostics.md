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


### `_is_stdlib_frame(filename: str)`

判断给定文件是否属于 Python 标准库

> **内部方法**
用于协程等待链采样时跳过 asyncio 等标准库帧（如 ``sleep``），直接
定位业务代码的等待点。venv 环境下 ``sys.base_prefix`` 指向真实
Python 安装目录，site-packages（第三方库）不在其中、不受影响。

---


### `_is_internal_frame(filename: str)`

判断给定文件是否为框架或标准库内部帧（非业务代码）

> **内部方法**
框架帧与标准库帧统一视为非业务帧；协程等待链采样时两者都跳过。
第三方库（site-packages）不在此列——卡在第三方库内部同样具有定位价值。

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
- **hint_params** (`dict[str,`): Any] | None 提示行模板的填充参数
    （如 ``{"name": module_name}``，对应提示文案中的 ``{name}`` 占位符）
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
- **hint_params** (`dict[str,`): Any] | None 提示行模板的填充参数
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


### `handler_source_loc(handler: Any)`

生成事件处理器的定义位置标注（慢日志归因用）

返回形如 ``" (module.path:123)"`` 的标注串，拼接在处理器名后，
让 ``Main._handle_message`` 这类自定方法名能一眼定位到定义文件。
对 ``functools.wraps`` 包装的处理器自动经 ``__wrapped__`` 下钻到原始
函数取位置（包装函数的 ``__module__`` 被复制自原函数而 ``__code__``
是框架内包装定义处，直接取会错配）；对绑定方法取底层函数。
无源码信息（内置函数 / partial 等）时返回空串。

- **handler** (`事件处理器（函数`): / 绑定方法 / wraps 包装函数）
**返回值** (`位置标注串（含前导空格；无源码信息时为空串）`): 
**示例**:
```python
>>> handler_source_loc(my_handler)
' (my_module.views:42)'
```

---


### `_coro_await_frames(coro: Any, max_depth: int = 64)`

沿协程 ``cr_await`` 等待链收集帧（从最外层到最深挂起点）

> **内部方法**
``Task.get_stack()`` 只返回协程根帧的 ``f_back`` 调用链——协程 ``await``
另一个协程时不产生调用栈关系，内层帧拿不到；等待链须沿 ``cr_await``
逐级下钻（即 asyncio 调试输出挂起位置的同一机制）。

- **coro** (`协程对象（Task`): 的根协程）
- **max_depth** (`最大下钻深度（防循环引用兜底）`): **返回值** (`帧列表（frames[0]`): 最外层，末位为最深挂起帧）

---


### `deepest_user_frame(task: Any)`

抓取运行中 Task 协程等待链最深的用户代码帧（慢执行定位）

事件处理器执行超过阈值时，结束统计只能给出总耗时；本函数在执行中
沿 Task 根协程的 ``cr_await`` 等待链下钻，返回最靠近挂起点（await 处）
的非框架帧描述，直接定位业务代码的等待位置——无论等待的是 AI /
HTTP 还是任何第三方库。Task 未在等待（CPU 密集 / 已结束 / 无用户帧）
时返回空串。

- **task** (`运行中的`): asyncio.Task
**返回值** (`形如`): ``"my_module/client.py:88 in chat"`` 的描述串；无法采样时为空串

**示例**:
```python
>>> deepest_user_frame(asyncio.current_task())
'QvQChat/AIEngine/client.py:88 in chat'
```

---

