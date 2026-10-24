# `ErisPulse.CLI.commands.run` 模块

---

## 模块概述


Run 命令实现

直接运行主程序，支持热重载模式

> **提示**
> 1. `epsdk run` 以「监督进程 + 框架子进程」结构运行：子进程崩溃自动退避重试、
> 硬重启（退出码 42）自动重拉，监督进程自身只有 Ctrl+C 能停止
> 2. `epsdk run --reload` 同样走监督结构：worker 子进程内做文件监控与组件级
> 热重载（保存 .py 即触发热重载，不再整框架重启）；硬重启由监督进程重拉
> 全新 worker（框架新代码生效）
> 3. `epsdk run main.py --reload` 以脚本子进程 + 重载信号方式运行（脚本退出码
> 42 同样立即重拉）

---

## 函数列表


### `run_reload_worker(script: str | None) -> int`

reload worker 进程入口（由监督进程经 ``-c`` 引导拉起，跨进程公共入口）

SDK 模式（script=None）：dev 文件监控 + 自动启用插件热重载 + ``sdk.run``；
保存 .py 触发组件级热重载。硬重启（``hard_restart``）以退出码 42 退出，
由监督进程重拉全新 worker（框架新代码生效）。

不写运行状态文件（runtime.json 归监督进程维护）；argv 由监督进程透传。

- **script**: 保留参数位（脚本模式的 --reload 不走 worker，见

    ``RunCommand._run_script``）
**返回值**: 进程退出码

---


## 类列表


### `class ReloadHandler(FileSystemEventHandler)`

文件系统事件处理器

监控 .py 文件变更并触发 sdk.restart() 组件级热重载

> **提示**
> 1. 文件监控运行在独立线程，通过 run_coroutine_threadsafe 安全调度到事件循环
> 2. 合并去抖：首个事件立即触发，窗口（FILE_RELOAD_DEBOUNCE_SECS）内的后续
> 变更合并且窗口静默后统一补发一次（不丢弃）
> 3. 新建 .py 文件（on_created）同样触发热重载；删除不触发（插件目录的删除
> 清理由插件热重载 watcher 负责）


#### 方法列表


##### `__init__(loop: asyncio.AbstractEventLoop)`

初始化热重载处理器

- **loop** (`asyncio.AbstractEventLoop`): 用于调度重载协程的事件循环

---


##### `on_modified(event: FileChangeEvent) -> None`

文件修改事件回调，对 .py 文件触发热重载

- **event** (`FileChangeEvent`): 文件系统事件

---


##### `on_created(event: FileChangeEvent) -> None`

文件创建事件回调（新建 .py 文件同样触发热重载）

- **event** (`FileChangeEvent`): 文件系统事件

---


##### `_on_event(src_path: str) -> None`

**内部方法** 合并去抖入口

---


##### `_flush_pending() -> None`

去抖窗口到期：补发窗口内合并的变更（可为空）

---


##### `close() -> None`

停止补发定时器（监控停止时调用）

---


##### `_dispatch(paths: set[str]) -> None`

**内部方法**
先提示变更文件（在调度重载之前——用户应先看到触发原因），再调度热重载

---


### `class _DevWatchdog`

**内部方法**
dev 模式文件监控（reload worker 内运行）

忽略 .venv/.git 等目录；插件目录默认移交插件热重载 watcher 处理
（全量 restart 本就覆盖插件代码，避免双重触发）。


#### 方法列表


##### `_resolve_excludes() -> 'tuple[list[str] | None, list[str]]'`（staticmethod）

解析 dev 监控的忽略目录与插件目录移交清单

**返回值**: (PollingObserver ignore_dirs——None = 内置默认清单, 需移交

    插件 watcher 并从自身监控排除的插件目录名列表)

---


##### `start(watch_dir: str, loop: asyncio.AbstractEventLoop) -> None`

启动 dev 文件监控并打印模式面板

- **watch_dir**: 监控目录
- **loop**: 用于调度重载的事件循环

---


##### `stop() -> None`

停止 dev 文件监控（幂等）

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


##### `_print_hard_restart_reason() -> None`

**内部方法**
展示并消费硬重启观测标记（worker 退出前写入 runtime.json）

---


##### `_supervise(cmd: list[str], *, reload_worker: bool = False) -> None`

**内部方法**
监督循环：拉起并看护框架子进程

- 退出码 42（硬重启）：展示原因后重拉全新子进程
- 退出码 0：正常退出，停止监督
- 其它退出码：按递增退避自动重试；连续同码崩溃达到阈值输出排查指引

- **cmd**: 子进程命令行
- **reload_worker**: 子进程是否为 reload worker（注入 ENV_RELOAD_WORKER）

---


##### `_run_internal(reload_mode: bool)`

直接运行 SDK（不指定脚本时）

以「监督进程 + 框架子进程」结构运行：子进程崩溃自动重试，硬重启
（退出码 42）重拉全新进程。reload 模式的子进程为 reload worker
（dev 文件监控 + 组件级热重载），两种模式共享同一套监督语义。

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
退出时不会终止重载循环，而是等待下一次文件变更后再尝试重启；硬重启
（退出码 42）例外——立即重拉全新脚本进程。

- **script_path_abs** (`str`): 脚本的绝对路径

---

