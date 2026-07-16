# `ErisPulse.runtime.hints` 模块

---

## 模块概述


ErisPulse 友好错误提示引擎

提供拼写检查、相似度匹配功能，帮助用户快速定位拼写错误。
被 CLI、全局异常钩子及核心模块的属性访问共同使用。

> **提示**
> 1. suggest_similar: 返回多个相似候选词
> 2. best_match: 返回单个最佳匹配
> 3. parse_attr_error: 从 AttributeError 中提取信息

---

## 函数列表


### `suggest_similar(name: str, candidates: Sequence[str])`

找出与给定名称最相似的候选词

使用 difflib 进行模糊匹配，适用于拼写纠错场景（如 my_moudle -> my_module）。
匹配时不区分大小写，但返回原始大小写的候选词。

- **name** (`用户输入的（可能有误的）名称`): - **candidates**: 候选词列表
- **max_suggestions** (`最多返回的建议数量`): - **cutoff**: 相似度阈值 (0.0 ~ 1.0)，低于此值的候选会被过滤
**返回值**: 按相似度从高到低排序的建议列表（保留原始大小写）

---


### `best_match(name: str, candidates: Sequence[str])`

返回单个最佳匹配建议

- **name** (`用户输入的名称`): - **candidates**: 候选词列表
- **cutoff** (`相似度阈值（默认`): 0.6，确保只返回高置信度匹配）
**返回值** (`最佳匹配的候选词，无匹配时返回`): None

---


### `best_match_with_prefix(name: str, candidates: Sequence[str])`

带前缀加成的模糊匹配

当输入是候选词的前缀时（如 ins -> install），给予更高的相似度分数。
适用于命令行补全、拼写纠错等场景，确保前缀匹配优先于字符重排匹配。

- **name** (`用户输入的名称`): - **candidates**: 候选词列表
- **cutoff** (`基础相似度阈值`): - **prefix_bonus**: 前缀匹配的最低分数（默认 0.85）
**返回值** (`最佳匹配的候选词，无匹配时返回`): None

---


### `parse_attr_error(exc: AttributeError)`

从 AttributeError 中提取对象类型名和属性名

优先使用 Python 3.10+ 的 exc.name 属性，
以及 exc.obj (3.12+) 推断类型名，
否则从错误消息中正则解析。

- **exc** (`AttributeError`): 异常实例
**返回值** (`(type_name,`): attr_name)，无法提取时对应位置为 None

---


### `get_object_from_traceback(tb: Any)`

尝试从 traceback 的最后一帧中获取出错的对象（通常是 self）

- **tb** (`traceback`): 对象
**返回值** (`出错的对象，无法获取时返回`): None

---


### `suggest_for_attribute_error(exc: AttributeError, tb: Any = None)`

为 AttributeError 生成拼写建议

尝试从异常对象或 traceback 中获取目标对象，
在其公共属性中查找最相似的。

- **exc** (`AttributeError`): 异常
- **tb** (`traceback`): 对象（可选）
**返回值** (`建议的属性名，无建议时返回`): None

---


### `suggest_for_import_error(exc: ImportError)`

为 ImportError / ModuleNotFoundError 生成拼写建议

利用 Python 动态特性：解析模块路径，动态 import 父包并检查
其实际包含的子模块/属性，给出最接近的匹配。

支持两种场景:
- ``import ErisPulse.Core.evnt`` -> 检查 ErisPulse.Core 下的子模块
- ``from ErisPulse.Core import evnt`` -> 检查 ErisPulse.Core 的导出属性

- **exc** (`ImportError`): 或 ModuleNotFoundError 异常
**返回值** (`建议的名称，无建议时返回`): None

---


### `suggest_for_key_error(exc: KeyError, tb: Any = None)`

为 KeyError 生成拼写建议

利用 Python 动态特性：遍历 traceback 帧的局部变量，
找到 dict-like 对象并在其 keys 中查找最相似的匹配。

- **exc** (`KeyError`): 异常
- **tb** (`traceback`): 对象
**返回值** (`建议的`): key，无建议时返回 None

---


### `suggest_for_name_error(exc: NameError, tb: Any = None)`

为 NameError 生成拼写建议

名字拼写错误（如 ``my_modlue`` -> ``my_module``）是最高频的失误之一。
从出错帧的局部变量、全局变量与内置名称中收集候选，给出最接近的匹配。

- **exc** (`NameError`): 异常
- **tb** (`traceback`): 对象（可选）
**返回值** (`建议的名称，无建议时返回`): None

---


### `suggest_for_coroutine_attribute(exc: AttributeError, tb: Any = None)`

检测“对协程对象访问属性”的常见错误（忘记 await）

例如 ``sdk.my_module`` 返回未 await 的协程时，访问其属性会抛
AttributeError。此函数返回一个标识符，由 exceptions.py 翻译为
“你是不是忘记 await 了？”的提示。

- **exc** (`AttributeError`): 异常
- **tb** (`traceback`): 对象（可选）
**返回值** (`诊断提示标识符，不匹配时返回`): None

---


### `suggest_for_missing_argument(exc: TypeError)`

为 TypeError: missing required positional argument 生成诊断提示

检测调用时位置参数不足的常见错误（如调用 ``f(a)`` 但定义需要两个参数）。

- **exc** (`TypeError`): 异常
**返回值** (`诊断提示标识符，不匹配时返回`): None

---


### `suggest_for_not_callable(exc: TypeError)`

为 TypeError: object is not callable / not subscriptable / not iterable 生成诊断提示

检测对不可调用 / 不可下标 / 不可迭代对象误用的常见错误，
多数情况下是因为覆盖了同名变量或忘记加括号。

- **exc** (`TypeError`): 异常
**返回值** (`诊断提示标识符，不匹配时返回`): None

---


### `suggest_for_event_loop_error(exc: RuntimeError)`

为 RuntimeError 中与事件循环相关的错误生成诊断提示

覆盖常见场景：
- 事件循环已被关闭（event loop is closed）
- 没有当前事件循环（There is no current event loop）
- 在已有事件循环中调用 asyncio.run()（cannot be called from a running event loop）

与拼写建议类函数不同，这里返回的是一个标识符字符串，
由 exceptions.py 通过 i18n 翻译为最终的多语言提示。

- **exc** (`RuntimeError`): 异常
**返回值** (`诊断提示标识符，不匹配时返回`): None

---


### `suggest_for_invalid_await(exc: TypeError)`

为 TypeError: object X can't be used in 'await' expression 生成诊断提示

检测对非协程对象使用 await 的常见原因。
与拼写建议类函数不同，这里返回的是一个标识符字符串，
由 exceptions.py 通过 i18n 翻译为最终的多语言提示。

- **exc** (`TypeError`): 异常
**返回值** (`诊断提示标识符，不匹配时返回`): None

---


### `suggest_for_recursion_error(exc: RecursionError)`

为 RecursionError 生成诊断提示

检测无限递归 / 缺少递归终止条件的常见错误。

- **exc** (`RecursionError`): 异常
**返回值**: 诊断提示标识符

---


### `suggest_for_timeout_error(exc: TimeoutError)`

为 TimeoutError 生成诊断提示

检测网络 / 异步操作超时的常见错误。

- **exc** (`TimeoutError`): 异常
**返回值**: 诊断提示标识符

---


### `suggest_for_connection_error(exc: ConnectionError)`

为 ConnectionError 及其子类生成诊断提示

覆盖 ConnectionRefusedError / ConnectionResetError / ConnectionAbortedError，
检测网络连接问题的常见原因。

- **exc** (`ConnectionError`): 异常
**返回值**: 诊断提示标识符

---


### `suggest_for_erispulse_client_error(exc: BaseException)`

为 ErisPulse 自定义客户端异常生成诊断提示

覆盖框架自身的 ClientConnectionError / ClientTimeoutError / HTTPStatusError，
使用户看到这些异常时能获得与原生网络异常一致的友好提示。
为避免循环导入，errors 模块在函数内部延迟导入。

- **exc** (`异常对象`): **返回值** (`诊断提示标识符，不匹配时返回`): None

---


### `suggest_for_websocket_disconnect(exc: BaseException)`

检测 WebSocket 断开是否为正常关闭

WebSocketDisconnect 的 code=1000（正常关闭）属于生命周期事件而非错误；
其他 code（如 1006 异常断开）才需要关注。为避免循环导入，
errors 模块在函数内部延迟导入。

- **exc** (`异常对象`): **返回值** (`标识符（'websocket_normal_close'`): / 'websocket_abnormal_close'），不匹配返回 None

---

