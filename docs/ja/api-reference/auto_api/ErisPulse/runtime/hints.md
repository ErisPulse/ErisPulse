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

:param name: 用户输入的（可能有误的）名称
:param candidates: 候选词列表
:param max_suggestions: 最多返回的建议数量
:param cutoff: 相似度阈值 (0.0 ~ 1.0)，低于此值的候选会被过滤
:return: 按相似度从高到低排序的建议列表（保留原始大小写）

---


### `best_match(name: str, candidates: Sequence[str])`

返回单个最佳匹配建议

:param name: 用户输入的名称
:param candidates: 候选词列表
:param cutoff: 相似度阈值（默认 0.6，确保只返回高置信度匹配）
:return: 最佳匹配的候选词，无匹配时返回 None

---


### `best_match_with_prefix(name: str, candidates: Sequence[str])`

带前缀加成的模糊匹配

当输入是候选词的前缀时（如 ins -> install），给予更高的相似度分数。
适用于命令行补全、拼写纠错等场景，确保前缀匹配优先于字符重排匹配。

:param name: 用户输入的名称
:param candidates: 候选词列表
:param cutoff: 基础相似度阈值
:param prefix_bonus: 前缀匹配的最低分数（默认 0.85）
:return: 最佳匹配的候选词，无匹配时返回 None

---


### `parse_attr_error(exc: AttributeError)`

从 AttributeError 中提取对象类型名和属性名

优先使用 Python 3.10+ 的 exc.name 属性，
以及 exc.obj (3.12+) 推断类型名，
否则从错误消息中正则解析。

:param exc: AttributeError 异常实例
:return: (type_name, attr_name)，无法提取时对应位置为 None

---


### `get_object_from_traceback(tb: Any)`

尝试从 traceback 的最后一帧中获取出错的对象（通常是 self）

:param tb: traceback 对象
:return: 出错的对象，无法获取时返回 None

---


### `suggest_for_attribute_error(exc: AttributeError, tb: Any = None)`

为 AttributeError 生成拼写建议

尝试从异常对象或 traceback 中获取目标对象，
在其公共属性中查找最相似的。

:param exc: AttributeError 异常
:param tb: traceback 对象（可选）
:return: 建议的属性名，无建议时返回 None

---


### `suggest_for_import_error(exc: ImportError)`

为 ImportError / ModuleNotFoundError 生成拼写建议

利用 Python 动态特性：解析模块路径，动态 import 父包并检查
其实际包含的子模块/属性，给出最接近的匹配。

支持两种场景:
- ``import ErisPulse.Core.evnt`` -> 检查 ErisPulse.Core 下的子模块
- ``from ErisPulse.Core import evnt`` -> 检查 ErisPulse.Core 的导出属性

:param exc: ImportError 或 ModuleNotFoundError 异常
:return: 建议的名称，无建议时返回 None

---


### `suggest_for_key_error(exc: KeyError, tb: Any = None)`

为 KeyError 生成拼写建议

利用 Python 动态特性：遍历 traceback 帧的局部变量，
找到 dict-like 对象并在其 keys 中查找最相似的匹配。

:param exc: KeyError 异常
:param tb: traceback 对象
:return: 建议的 key，无建议时返回 None

---


### `suggest_for_event_loop_error(exc: RuntimeError)`

为 RuntimeError: Event loop is closed 生成诊断提示

检测事件循环被意外关闭的常见原因，返回修复建议。
与拼写建议类函数不同，这里返回的是一个标识符字符串，
由 exceptions.py 通过 i18n 翻译为最终的多语言提示。

:param exc: RuntimeError 异常
:return: 诊断提示标识符，不匹配时返回 None

---


### `suggest_for_invalid_await(exc: TypeError)`

为 TypeError: object X can't be used in 'await' expression 生成诊断提示

检测对非协程对象使用 await 的常见原因。
与拼写建议类函数不同，这里返回的是一个标识符字符串，
由 exceptions.py 通过 i18n 翻译为最终的多语言提示。

:param exc: TypeError 异常
:return: 诊断提示标识符，不匹配时返回 None

---

