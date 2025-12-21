# `ErisPulse.Core.logger` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 日志系统

提供模块化日志记录功能，支持多级日志、模块过滤和内存存储。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持按模块设置不同日志级别
2. 日志可存储在内存中供后续分析
3. 自动识别调用模块名称</p></div>

---

## 类列表

### `class Logger`

    日志管理器

提供模块化日志记录和存储功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用set_module_level设置模块日志级别
2. 使用get_logs获取历史日志
3. 支持标准日志级别(DEBUG, INFO等)</p></div>

    
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
    
##### `get_logs(module_name: str = 'Unknown')`

    获取日志内容

:param module_name (可选): 模块名称
:return: dict 日志内容

    ---
    
##### `get_child(child_name: str = 'UnknownChild')`

    获取子日志记录器

:param child_name: 子模块名称(可选)
:return: LoggerChild 子日志记录器实例

    ---
    
##### `critical(msg)`

    记录 CRITICAL 级别日志
这是最高级别的日志，表示严重的系统错误
注意：此方法不会触发程序崩溃，仅记录日志

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 这是最高级别的日志，表示严重系统错误
2. 不会触发程序崩溃，如需终止程序请显式调用 sys.exit()
3. 会在日志文件中添加 CRITICAL 标记便于后续分析</p></div>

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
    
##### `critical(msg)`

    记录 CRITICAL 级别日志
这是最高级别的日志，表示严重的系统错误
注意：此方法不会触发程序崩溃，仅记录日志

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 这是最高级别的日志，表示严重系统错误
2. 不会触发程序崩溃，如需终止程序请显式调用 sys.exit()
3. 会在日志文件中添加 CRITICAL 标记便于后续分析</p></div>

    ---
    
##### `get_child(child_name: str)`

    获取子日志记录器的子记录器

:param child_name: 子模块名称
:return: LoggerChild 子日志记录器实例

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>