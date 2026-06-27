# `ErisPulse.CLI.commands.run` 模块

---

## 模块概述


Run 命令实现

直接运行主程序，支持热重载模式

---

## 类列表


### `class ReloadHandler(FileSystemEventHandler)`

文件系统事件处理器

监控 .py 文件变更并触发 sdk.restart() 热重载

> **提示**
> 1. 文件监控运行在独立线程
> 2. 通过 run_coroutine_threadsafe 安全调度到事件循环
> 3. 内置 1 秒防抖，避免短时间内多次重载


#### 方法列表


##### `__init__(loop: asyncio.AbstractEventLoop)`

初始化热重载处理器

- **loop** (`asyncio.AbstractEventLoop`): 用于调度重载协程的事件循环

---


##### `on_modified(event)`

文件修改事件回调，对 .py 文件触发热重载

- **event** (`FileSystemEvent`): 文件系统事件

---


##### `_schedule_reload(event)`

在事件循环中调度 SDK 重启以执行热重载

- **event** (`FileSystemEvent`): 触发重载的文件系统事件

---


### `class RunCommand(Command)`

Run 命令

运行主程序，支持热重载模式


#### 方法列表


##### `_run_internal(reload_mode: bool)`

直接运行 SDK（不指定脚本时）

以子进程方式运行 SDK，支持硬重启。

> **提示**
> 重要设计原则：
> 1. 只有硬重启（退出码 42）或 KeyboardInterrupt 才能停止主进程
> 2. 模块/适配器的任何错误都**不会**导致主进程退出
> 3. 子进程异常退出时自动重试，使用递增退避策略避免刷屏

---


##### `_run_script(script_path: str, reload_mode: bool)`

运行指定的脚本文件，可选启用热重载

- **script_path** (`str`): 脚本文件路径
- **reload_mode** (`bool`): 是否启用热重载模式

---


##### `_run_script_with_reload(script_path_abs: str)`

以子进程方式运行脚本并监控文件变更以自动重启

进程的所有终止与重启均在主线程完成；文件监控线程仅负责发出重载信号，
避免双线程同时操作子进程导致的竞态。脚本进程因错误（如语法错误、异常）
退出时不会终止重载循环，而是等待下一次文件变更后再尝试重启。

- **script_path_abs** (`str`): 脚本的绝对路径

---


##### `_setup_watchdog(watch_dir: str, loop: asyncio.AbstractEventLoop)`

配置 watchdog 监控指定目录的文件变更以实现热重载

- **watch_dir** (`str`): 要监控的目录路径
- **loop** (`asyncio.AbstractEventLoop`): 用于调度重载的事件循环

---

