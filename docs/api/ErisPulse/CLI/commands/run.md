# `ErisPulse.CLI.commands.run` 模块

---

## 模块概述


Run 命令实现

运行主程序

---

## 类列表


### `class ReloadHandler(FileSystemEventHandler)`

文件系统事件处理器

实现热重载功能，监控文件变化并重启进程

> **提示**
> 1. 支持.py文件修改重载
> 2. 支持配置文件修改重载


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


### `class RunCommand(Command)`

RunCommand 类提供相关功能。


#### 方法列表


##### `_setup_watchdog(script_path: str, reload_mode: bool)`

设置文件监控

:param script_path: 要监控的脚本路径
:param reload_mode: 是否启用重载模式

---


##### `_cleanup()`

清理资源

---

