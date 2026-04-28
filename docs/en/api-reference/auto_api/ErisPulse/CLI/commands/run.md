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


### `class RunCommand(Command)`

Run 命令

运行主程序，支持热重载模式


#### 方法列表


##### `_run_internal(reload_mode: bool)`

直接运行 SDK（不指定脚本时）

---


##### `_run_script(script_path: str, reload_mode: bool)`

运行指定脚本文件

---

