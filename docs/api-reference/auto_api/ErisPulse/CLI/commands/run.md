# `ErisPulse.CLI.commands.run` 模块

---

## 模块概述


Run 命令实现

运行主程序

---

## 类列表


### `class ReloadHandler(FileSystemEventHandler)`

文件系统事件处理器

实现热重载功能，监控 .py 文件变更并自动重启

> **提示**
> 1. 仅在 --reload 模式下启用监控
> 2. 监控 .py 文件，修改后创建清理信号文件并重启
> 3. 子进程检测到清理信号文件后自动调用 sdk.uninit()
> 4. 进程终止时使用清理信号文件确保资源正确释放


#### 方法列表


##### `__init__(script_path: str, reload_mode: bool = False)`

初始化处理器

- **script_path** (`str`): 要监控的脚本路径
- **reload_mode** (`bool`): 是否启用重载模式 (默认: False)

---


##### `start_process()`

启动监控进程

注入环境变量，让子进程知道自己是由 CLI 启动的

---


##### `_terminate_process()`

终止当前进程

创建清理信号文件，通知子进程执行清理操作
等待最多 10 秒让进程正常退出

---


##### `on_modified(event)`

文件修改事件处理

仅在 --reload 模式下监控 .py 文件变更

- **event** (`FileSystemEvent`): 文件系统事件

---


##### `_handle_reload(event, reason: str)`

处理热重载逻辑

创建清理信号文件，通知子进程执行清理，然后重启进程

- **event** (`FileSystemEvent`): 文件系统事件
- **reason** (`str`): 重载原因

---


### `class RunCommand(Command)`

Run 命令

运行主程序，支持热重载模式


#### 方法列表


##### `add_arguments(parser: ArgumentParser)`

添加命令行参数

- **parser** (`ArgumentParser`): 参数解析器

---


##### `execute(args)`

执行命令

- **args** (`Namespace`): 命令行参数

---


##### `_setup_watchdog(script_path: str, reload_mode: bool)`

设置文件监控

- **script_path** (`str`): 要监控的脚本路径
- **reload_mode** (`bool`): 是否启用重载模式
**返回值** (`list`): 监控的目录列表

---


##### `_cleanup()`

清理资源

停止文件监控，终止子进程

---

