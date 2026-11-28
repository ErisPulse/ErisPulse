# `ErisPulse.runtime.dev_watch` 模块

---

## 模块概述


开发模式细粒度热重载监控

供 ``epsdk run --reload`` 的 worker 与脚本模式子进程共用：

- 按 :func:`runtime.reload_target.classify_reload_path` 判定变更文件的最小
  重载单元（单模块 / 单适配器 / 插件 / 进程重启）
- 合并去抖：首个事件立即触发，窗口内后续变更在窗口静默后统一补发
- 插件目录默认移交 ``PluginReloadWatcher``，本监控排除以免双重触发

---

## 类列表


### `class DevReloadHandler(FileSystemEventHandler)`

细粒度热重载文件事件处理器

> **提示**
> 1. 文件监控运行在独立线程，通过 run_coroutine_threadsafe 调度到事件循环
> 2. 去抖窗口由 ``FILE_RELOAD_DEBOUNCE_SECS`` 控制
> 3. 同一批变更按 ``(kind, name, reason)`` 去重，避免重复重载


#### 方法列表


##### `__init__(loop: asyncio.AbstractEventLoop, sdk: Any, *, entry_paths: 'tuple[str | Path, ...]' = (), notify: 'Callable[[set[str]], None] | None' = None)`

初始化处理器

- **loop**: 调度重载协程的事件循环
- **sdk** (`SDK`): 实例（读取注册表并执行重载）
- **entry_paths**: 入口脚本路径（缺省从 ``sys.argv[0]`` 推断）
- **notify**: 文件变更提示回调（接收本批变更路径）

---


##### `on_modified(event: FileChangeEvent) -> None`

文件修改事件回调

- **event**: 文件系统事件

---


##### `on_created(event: FileChangeEvent) -> None`

文件创建事件回调

- **event**: 文件系统事件

---


##### `_on_event(src_path: str) -> None`

**内部方法** 合并去抖入口

---


##### `_flush_pending() -> None`

**内部方法** 去抖窗口到期补发合并变更

---


##### `close() -> None`

停止补发定时器并清空待发队列

---


##### `_dispatch(paths: set[str]) -> None`

**内部方法** 判定目标并调度重载

---


##### `async _apply(target: ReloadTarget) -> None`

**内部方法** 执行单个重载目标

---


### `class DevWatcher`

开发模式文件监控器

监控指定目录（默认当前目录）下的 ``.py`` 变更，按判定结果执行单模块 /
单适配器重载或进程级重启。

> **提示**
> 1. 忽略目录取自 ``ErisPulse.framework.watch_ignore_dirs``；插件目录
> 默认追加到忽略清单，由其专用 watcher 处理
> 2. 与 ``PluginReloadWatcher`` 可同时运行，二者监控范围互补


#### 方法列表


##### `__init__(sdk: Any, *, entry_paths: 'tuple[str | Path, ...]' = ())`

初始化监控器

- **sdk** (`SDK`): 实例
- **entry_paths**: 入口脚本路径

---


##### `start(watch_dir: str = '.', loop: 'asyncio.AbstractEventLoop | None' = None, notify: 'Callable[[set[str]], None] | None' = None) -> bool`

启动监控

- **watch_dir**: 监控目录
- **loop**: 调度重载的事件循环（缺省取当前运行循环）
- **notify**: 文件变更提示回调

**返回值**: 是否启动成功

---


##### `stop() -> None`

停止监控（幂等）

---


##### `_resolve_ignore_dirs() -> 'list[str] | None'`（staticmethod）

**内部方法** 解析忽略目录（含插件目录）

---

