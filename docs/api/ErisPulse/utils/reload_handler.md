# `ErisPulse.utils.reload_handler` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse SDK 热重载处理器

实现热重载功能，监控文件变化并重启进程

---

## 类列表

### `class ReloadHandler(FileSystemEventHandler)`

    文件系统事件处理器

实现热重载功能，监控文件变化并重启进程

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持.py文件修改重载
2. 支持配置文件修改重载</p></div>

    
#### 方法列表

##### `__init__(script_path: str, reload_mode: bool = False)`

    初始化处理器

:param script_path: 要监控的脚本路径
:param reload_mode: 是否启用重载模式

    ---
    
##### `start_process()`

    启动监控进程

    ---
    
##### `_terminate_process()`

    终止当前进程

:raises subprocess.TimeoutExpired: 进程终止超时时抛出

    ---
    
##### `on_modified(event)`

    文件修改事件处理

:param event: 文件系统事件

    ---
    
##### `_handle_reload(event, reason: str)`

    处理热重载逻辑
:param event: 文件系统事件
:param reason: 重载原因

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>