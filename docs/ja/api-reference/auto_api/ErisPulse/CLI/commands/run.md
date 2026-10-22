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


##### `on_modified(event: FileChangeEvent) -> None`

文件修改事件回调，对 .py 文件触发热重载

- **event** (`FileChangeEvent`): 文件系统事件

---


##### `_schedule_reload(event: FileChangeEvent)`

在事件循环中调度 SDK 重启以执行热重载

- **event** (`FileChangeEvent`): 触发重载的文件系统事件

---


### `class RunCommand(Command)`

Run 命令

运行主程序，支持热重载模式


#### 方法列表


##### `_read_strict_mode() -> int`

读取框架严格模式配置级别（``ErisPulse.framework.strict_mode``）

走 frame_config 的内存合并默认值通道（不要求配置文件存在该键），
环境变量 ``ERISPULSE_FRAMEWORK_STRICT_MODE`` 的覆盖同样生效。

**返回值** (`int`): 0=宽松 / 1=跳过 / 2=致命；读取失败按宽松(0)处理

---


##### `_resolve_strict(strict_arg: bool | None) -> tuple[bool, int | None]`

解析严格模式三态：显式参数临时覆盖，缺省跟随框架配置

- **strict_arg** (`bool | None`): ``--strict`` / ``--no-strict`` 的解析值，

    None 表示未传参
**返回值**: ([tuple]) ``(预检是否严格, 框架级别注入值)``——注入值非 None 时

    写入 ``ERISPULSE_FRAMEWORK_STRICT_MODE`` 临时覆盖本次运行的框架
    严格级别（不落盘，子进程经环境继承）；None 表示框架级别不动

---


##### `_preflight(strict: bool)`

启动前快速自检：配置文件可解析性与已装组件必填项完整性

严格性来源：``--strict`` / ``--no-strict`` 显式指定，缺省跟随
``ErisPulse.framework.strict_mode``（>=1 视为严格）。检查失败默认仅
警告并继续启动——框架对缺失配置按"正常首次启动"容忍，警告不应
挡住运行；``strict=True`` 时打印失败项并以退出码 1 终止。自检自身
出现任何异常（依赖缺失、组件发现失败等）一律跳过，绝不阻塞启动。
不含任何网络探测。

- **strict** (`bool`): 检查失败时是否强制退出

---


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

