# 📦 `ErisPulse.Core.logger` 模块

<sup>自动生成于 2025-08-02 01:50:12</sup>

---

## 模块概述


ErisPulse 日志系统

提供模块化日志记录功能，支持多级日志、模块过滤和内存存储。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持按模块设置不同日志级别
2. 日志可存储在内存中供后续分析
3. 自动识别调用模块名称</p></div>

---

## 🏛️ 类

### `class Logger`

日志管理器

提供模块化日志记录和存储功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用set_module_level设置模块日志级别
2. 使用get_logs获取历史日志
3. 支持标准日志级别(DEBUG, INFO等)</p></div>


#### 🧰 方法

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

:param module_name (可选): 模块名称
:return: dict 日志内容

---

<sub>文档最后更新于 2025-08-02 01:50:12</sub>