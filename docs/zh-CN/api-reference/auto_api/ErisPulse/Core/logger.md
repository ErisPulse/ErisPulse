# `ErisPulse.Core.logger` 模块

---

## 模块概述


ErisPulse 日志系统

提供模块化日志记录功能，支持多级日志、模块过滤和内存存储。

> **提示**
> 1. 支持按模块设置不同日志级别
> 2. 日志可存储在内存中供后续分析
> 3. 自动识别调用模块名称

---

## 函数列表


### `_format_message(msg: object, args: tuple)`

将日志消息与位置参数按 ``%`` 风格格式化

有 args 时应用 ``str(msg) % args``，无 args 时保持原文不变（``%s`` 字面量保留），
格式化失败时回退到原始字符串。控制台路径仍由 Python logging 自行格式化，
此处仅为内存副本 / 订阅器提供与之一致的文本。

> **内部方法**

- **msg** (`原始日志消息`): - **args**: 位置参数元组
**返回值**: 格式化后的日志文本

---


## 类列表


### `class _JsonFormatter(logging.Formatter)`

JSON 日志格式化器

> **内部方法**


### `class Logger`

日志管理器

提供模块化日志记录和存储功能

> **提示**
> 1. 使用set_module_level设置模块日志级别
> 2. 使用get_logs获取历史日志
> 3. 支持标准日志级别(DEBUG, INFO等)


#### 方法列表


##### `handler(handler_id: str = '')`

日志订阅装饰器

订阅器的 ``min_level`` 可低于全局日志级别，从而显式订阅 DEBUG / TRACE
等低级别日志。此时低级别日志仅推送给匹配的订阅器，不会输出到控制台，
也不会写入内存（历史补发仍受全局 ``memory_limit`` 限制）。

>>> @sdk.logger.handler("dashboard", min_level="INFO")
... def on_log(log_data: dict): ...

>>> # 显式订阅低于全局级别的日志（如全局为 INFO，仍可收到 DEBUG）
>>> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
... def on_debug(log_data: dict): ...

>>> sdk.logger.handler("dashboard", min_level="INFO")(on_log)

- **handler_id** (`订阅器唯一标识，为空时使用函数名`): - **min_level**: 最低日志级别

---


##### `_register_handler(handler_id: str, callback: Callable[[dict], None], min_level: str)`

> **内部方法**
内部注册逻辑

---


##### `remove_handler(handler_id: str)`

移除日志订阅器

- **handler_id** (`注册时使用的标识`): **返回值** (`bool`): 是否成功移除

---


##### `_notify_handlers(level_name: str, level_const: int, module: str, msg: str)`

> **内部方法**
向所有符合条件的订阅器推送结构化日志

---


##### `_has_handler_for(level_const: int)`

判断是否存在订阅器愿意接收给定级别的日志

订阅器的 ``min_level`` 可低于全局日志级别，从而显式订阅 DEBUG / TRACE
等低级别日志。命中时仅推送给订阅器，不输出控制台、不写入内存。

> **内部方法**

- **level_const** (`日志级别数值`): **返回值** (`存在`): ``min_level <= level_const`` 的订阅器时返回 True

---


##### `set_memory_limit(limit: int)`

设置日志内存存储上限

- **limit** (`日志存储上限`): **返回值** (`bool`): 设置是否成功

---


##### `_resolve_level(level: str)`

将字符串级别名解析为对应的数值常量

- **level** (`日志级别名称`): **返回值** (`对应的`): logging 级别数值，无效时返回 None

> **内部方法**

---


##### `set_level(level: str)`

设置全局日志级别

支持标准级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
及自定义级别 (TRACE/EVENT)

- **level** (`日志级别名称`): **返回值** (`bool`): 设置是否成功

---


##### `set_module_level(module_name: str, level: str)`

设置指定模块日志级别

支持标准级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
及自定义级别 (TRACE/EVENT)

- **module_name** (`模块名称`): - **level**: 日志级别名称
**返回值** (`bool`): 设置是否成功

---


##### `set_excluded_levels(levels: list[str])`

设置被屏蔽的日志等级列表

被屏蔽等级的日志将被完全丢弃：不写入内存、不推送给订阅器、
不输出控制台、不写入日志文件。常用于隐私保护场景，
例如 ``exclude_levels = ["EVENT"]`` 可隐藏消息收发内容
（消息收发日志使用 EVENT 等级记录）。

- **levels** (`日志等级名称列表（如`): ["EVENT", "DEBUG"]），空列表表示不屏蔽
**返回值** (`bool`): 设置是否成功（含非法等级时返回 False 且不生效）

**示例**:
```python
>>> # 屏蔽 EVENT 等级（隐藏消息收发内容）
>>> logger.set_excluded_levels(["EVENT"])
>>> # 恢复所有等级
>>> logger.set_excluded_levels([])
```

---


##### `exclude_level(level: str)`

屏蔽单个日志等级

被屏蔽等级的日志将被完全丢弃（内存 / 订阅器 / 控制台 / 文件）。

- **level** (`日志等级名称（如`): "EVENT"）
**返回值** (`bool`): 是否设置成功

---


##### `allow_level(level: str)`

取消屏蔽单个日志等级

- **level** (`日志等级名称（如`): "EVENT"）
**返回值** (`bool`): 是否成功（等级原本未被屏蔽时返回 False）

---


##### `list_excluded_levels()`

列出当前被屏蔽的日志等级名称

**返回值** (`list[str]`): 被屏蔽的等级名称列表

---


##### `set_output_file(path)`

设置日志输出

- **path** (`日志文件路径`): Str/List
**返回值** (`bool`): 设置是否成功

---


##### `set_format(fmt: str = 'rich')`

设置日志输出格式

支持三种格式：
- ``rich``（默认）：彩色带时间的 Rich 输出
- ``plain``：纯文本无颜色（适合日志采集 / 管道重定向）
- ``json``：JSON 结构化输出（适合 ELK / Grafana Loki / Datadog 等）

- **fmt** (`日志格式名称：``rich```): / ``plain`` / ``json`` (默认: "rich")
**返回值** (`bool`): 设置是否成功

**示例**:
```python
>>> # 在 config.toml 中配置
>>> [ErisPulse.logger]
>>> format = "plain"
>>>
>>> # 或代码中动态切换
>>> logger.set_format("plain")
```

---


##### `set_json_format(enabled: bool = True)`

启用或禁用 JSON 结构化日志输出

启用后，所有日志（控制台和文件）将以 JSON 格式输出，
适合 ELK / Grafana Loki / Datadog 等日志聚合系统。

- **enabled** (`是否启用`): JSON 格式（默认 True）
**返回值** (`bool`): 设置是否成功

**示例**:
```python
>>> # 在 config.toml 中配置
>>> [ErisPulse.logger]
>>> format = "json"
>>>
>>> # 或代码中动态切换
>>> logger.set_json_format(True)
```

---


##### `save_logs(path)`

保存所有在内存中记录的日志

- **path** (`日志文件路径`): Str/List
**返回值** (`bool`): 设置是否成功

---


##### `get_logs(module_name: str | None = None)`

获取日志内容

JSON 模式下返回结构化 dict 列表，Rich 模式下返回字符串列表。

:param module_name (可选): 模块名称，None表示获取所有日志
**返回值** (`dict`): 日志内容

---


##### `iter_logs(module_name: str | None = None)`

流式迭代日志（生成器）

适合处理大量日志或推送到 SSE / WebSocket。

- **module_name** (`str`): 模块名称，None 表示所有模块
**返回值** (`Iterator[dict | str`): ] JSON 模式下为 dict，Rich 模式下为 str

**示例**:
```python
>>> for log in logger.iter_logs():
...     print(log)
```

---


##### `_format_for_output(entries: list)`

> **内部方法**
将内部 dict 转换为向后兼容的输出格式

---


##### `_save_in_memory(module_name: str, level_name: str, level_const: int, msg: str)`

> **内部方法**
将日志保存到内存

---


##### `_on_config_updated(_data: dict)`

配置变更回调：仅在 logger 段实际变化时重新应用配置

---


##### `_log(level_name: str, level_const: int, msg)`

内部日志方法，统一处理日志记录流程

- **level_name** (`日志级别名称（对应logging模块的方法名）`): - **level_const**: 日志级别常量
- **msg** (`日志消息`): - **args**: 额外的格式化参数
- **kwargs**: 额外的关键字参数

---


##### `get_child(child_name: str = 'UnknownChild')`

获取子日志记录器

- **child_name** (`子模块名称(可选)`): - **relative**: 是否相对于调用者模块（默认True）
    - True: 使用"调用模块.子模块"作为完整名称
    - False: 直接使用child_name作为完整名称
**返回值** (`LoggerChild`): 子日志记录器实例

**示例**:
```python
>>> # 相对模式（默认）：自动添加调用模块前缀
>>> child_logger = logger.get_child("database")
>>> # 假设调用者是"mymodule"，完整名称将是"mymodule.database"
>>>
>>> # 绝对模式：直接使用指定名称
>>> child_logger = logger.get_child("custom.module.name", relative=False)
>>> # 完整名称将是"custom.module.name"
>>>
>>> # 获取当前模块的日志记录器
>>> my_logger = logger.get_child()
```

---


##### `trace(msg)`

记录 TRACE 级别日志（比 DEBUG 更细粒度）

---


##### `event(msg)`

记录 EVENT 级别日志（事件收发专用，级别等同 INFO）

---


##### `debug(msg)`

记录 DEBUG 级别日志

---


##### `info(msg)`

记录 INFO 级别日志

---


##### `warning(msg)`

记录 WARNING 级别日志

---


##### `error(msg)`

记录 ERROR 级别日志

---


##### `critical(msg)`

记录 CRITICAL 级别日志
这是最高级别的日志，表示严重的系统错误
注意：此方法不会触发程序崩溃，仅记录日志

> **提示**
> 1. 不会触发程序崩溃，如需终止程序请显式调用 sys.exit()
> 2. 会在日志文件中添加 CRITICAL 标记便于后续分析

---


##### `_store_ui_line(text: str)`

将 UI 输出行写入内存、订阅器与日志文件

视觉输出方法（``print_*``）原本直接打印到控制台、绕过日志管道，
导致 Dashboard 等日志订阅器收不到启动阶段的阶段标题/数量/组件树，
也无法在订阅器注册时补发历史。此方法将文本按 INFO 级别写入内存
（``_save_in_memory``）、推送给订阅器（``_notify_handlers``）并写入
日志文件，同时不重复输出控制台。

> **内部方法**
仅由 ``print_section_header`` / ``print_info`` / ``print_tree_item`` 调用。

- **text** (`str`): 需要写入日志管道的 UI 文本

---


##### `print_section_header(title: str)`

打印日志分组标题

- **title**: 分组标题

---


##### `print_section_footer()`

打印分组结束标记

---


##### `print_tree_item(text: str, level: int = 0, is_last: bool = False, tag: str = '', tag_style: str = 'dim')`

打印树状结构项目

- **text** (`文本内容`): - **level**: 缩进层级
- **is_last** (`是否是最后一项`): - **tag**: 可选的样式化后缀标签（如 "[懒加载]"）
- **tag_style** (`标签的`): rich 样式（默认 dim）

---


##### `print_info(text: str, level: int = 1)`

打印信息

- **text** (`文本内容`): - **level**: 缩进层级

---


##### `print_section_separator()`

打印简单的分隔线

---


##### `__getattr__(name: str)`

通过属性访问自动创建子logger

- **name** (`子logger名称`): **返回值** (`LoggerChild`): 子logger实例
**异常**: `AttributeError` - 当访问无效属性时抛出

**示例**:
```python
>>> # 自动创建子logger并记录日志
>>> logger.mymodule.info("message")
>>>
>>> # 支持嵌套访问
>>> logger.mymodule.database.info("db message")
>>>
>>> # 相当于 logger.get_child("mymodule").info("message")
```

---


### `class LoggerChild`

子日志记录器

用于创建具有特定名称的子日志记录器，仅改变模块名称，其他功能全部委托给父日志记录器


#### 方法列表


##### `__init__(parent_logger: Logger, name: str)`

初始化子日志记录器

- **parent_logger** (`父日志记录器实例`): - **name**: 子日志记录器名称

---


##### `_log(level_name: str, level_const: int, msg)`

内部日志方法

- **level_name** (`日志级别名称`): - **level_const**: 日志级别常量
- **msg**: 日志消息

---


##### `trace(msg)`

记录 TRACE 级别日志（比 DEBUG 更细粒度）

---


##### `event(msg)`

记录 EVENT 级别日志（事件收发专用，级别等同 INFO）

---


##### `debug(msg)`

记录 DEBUG 级别日志

---


##### `info(msg)`

记录 INFO 级别日志

---


##### `warning(msg)`

记录 WARNING 级别日志

---


##### `error(msg)`

记录 ERROR 级别日志

---


##### `critical(msg)`

记录 CRITICAL 级别日志
这是最高级别的日志，表示严重的系统错误
注意：此方法不会触发程序崩溃，仅记录日志

---


##### `get_child(child_name: str)`

获取子日志记录器的子记录器

- **child_name** (`子模块名称`): **返回值** (`LoggerChild`): 子日志记录器实例

---


##### `__getattr__(name: str)`

通过属性访问自动创建子logger

- **name** (`子logger名称`): **返回值** (`LoggerChild`): 子logger实例
**异常**: `AttributeError` - 当访问无效属性时抛出

**示例**:
```python
>>> # 嵌套创建子logger
>>> child = logger.mymodule
>>> nested_child = child.database  # 相当于 logger.mymodule.database
>>> nested_child.info("db message")
```

---

