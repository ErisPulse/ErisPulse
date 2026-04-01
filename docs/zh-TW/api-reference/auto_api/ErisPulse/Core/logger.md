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

## 类列表


### `class Logger`

日志管理器

提供模块化日志记录和存储功能

> **提示**
> 1. 使用set_module_level设置模块日志级别
> 2. 使用get_logs获取历史日志
> 3. 支持标准日志级别(DEBUG, INFO等)


#### 方法列表


##### `set_memory_limit(limit: int)`

设置日志内存存储上限

:param limit: 日志存储上限
:return: bool 设置是否成功

---


##### `set_level(level: str)`

设置全局日志级别

:param level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
:return: bool 设置是否成功

---


##### `set_module_level(module_name: str, level: str)`

设置指定模块日志级别

:param module_name: 模块名称
:param level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
:return: bool 设置是否成功

---


##### `set_output_file(path)`

设置日志输出

:param path: 日志文件路径 Str/List
:return: bool 设置是否成功

---


##### `save_logs(path)`

保存所有在内存中记录的日志

:param path: 日志文件路径 Str/List
:return: bool 设置是否成功

---


##### `get_logs(module_name: str = None)`

获取日志内容

:param module_name (可选): 模块名称，None表示获取所有日志
:return: dict 日志内容

---


##### `_log(level_name: str, level_const: int, msg)`

内部日志方法，统一处理日志记录流程

:param level_name: 日志级别名称（对应logging模块的方法名）
:param level_const: 日志级别常量
:param msg: 日志消息
:param args: 额外的格式化参数
:param kwargs: 额外的关键字参数

---


##### `get_child(child_name: str = 'UnknownChild')`

获取子日志记录器

:param child_name: 子模块名称(可选)
:param relative: 是否相对于调用者模块（默认True）
    - True: 使用"调用模块.子模块"作为完整名称
    - False: 直接使用child_name作为完整名称
:return: LoggerChild 子日志记录器实例

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


##### `print_section_header(title: str)`

打印日志分组标题（树状结构）

:param title: 分组标题

---


##### `print_section_footer()`

打印分组结束标记

---


##### `print_tree_item(text: str, level: int = 0, is_last: bool = False)`

打印树状结构项目

:param text: 文本内容
:param level: 缩进层级
:param is_last: 是否是最后一项

---


##### `print_info(text: str, level: int = 1)`

打印信息（树状结构）

:param text: 文本内容
:param level: 缩进层级

---


##### `print_section_separator()`

打印简单的分隔线

---


##### `__getattr__(name: str)`

通过属性访问自动创建子logger

:param name: 子logger名称
:return: LoggerChild 子logger实例
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

:param parent_logger: 父日志记录器实例
:param name: 子日志记录器名称

---


##### `_log(level_name: str, level_const: int, msg)`

内部日志方法

:param level_name: 日志级别名称
:param level_const: 日志级别常量
:param msg: 日志消息

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

:param child_name: 子模块名称
:return: LoggerChild 子日志记录器实例

---


##### `__getattr__(name: str)`

通过属性访问自动创建子logger

:param name: 子logger名称
:return: LoggerChild 子logger实例
**异常**: `AttributeError` - 当访问无效属性时抛出
    

**示例**:
```python
>>> # 嵌套创建子logger
>>> child = logger.mymodule
>>> nested_child = child.database  # 相当于 logger.mymodule.database
>>> nested_child.info("db message")
```

---

