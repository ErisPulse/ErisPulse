# `ErisPulse.runtime.file_watcher` 模块

---

## 模块概述


文件变更监控

提供文件系统变更检测能力

> **提示**
> 1. 通过定期比较 .py 文件的 mtime 检测变更
> 2. 接口与 watchdog.observers.Observer 保持一致 (schedule/start/stop/join)
> 3. 供运行时插件热重载（runtime/plugin_reload）与 CLI 热重载（CLI/commands/run）共用
> 4. 默认忽略 .venv/.git 等目录（FILE_WATCHER_IGNORED_DIRS），可经 ignore_dirs 覆盖

---

## 类列表


### `class FileSystemEventHandler`

文件事件处理器基类

子类可覆写 on_modified 等回调以响应文件变更事件。

**示例**:

```python
class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"changed: {event.src_path}")
```


#### 方法列表


##### `on_modified(event: 'FileChangeEvent') -> None`

文件修改事件回调

- **event** (`FileChangeEvent`): 文件变更事件

---


##### `on_created(event: 'FileChangeEvent') -> None`

文件创建事件回调

- **event** (`FileChangeEvent`): 文件变更事件

---


##### `on_deleted(event: 'FileChangeEvent') -> None`

文件删除事件回调

- **event** (`FileChangeEvent`): 文件变更事件

---


##### `on_moved(event: 'FileChangeEvent') -> None`

文件移动事件回调

> **提示**
> 轮询实现（PollingObserver）基于 mtime 比较，不触发本回调——移动
> 表现为旧路径 ``on_deleted`` + 新路径 ``on_created``。

- **event** (`FileChangeEvent`): 文件变更事件

---


### `class FileChangeEvent`

文件变更事件

- **src_path** (`str`): 发生变更的文件路径
- **event_type** (`str`): 事件类型（"modified" / "created" / "deleted"）


#### 方法列表


##### `__init__(src_path: str, event_type: str = 'modified')`

初始化文件变更事件

- **src_path** (`str`): 发生变更的文件路径
- **event_type** (`str`): 事件类型（"modified" / "created" / "deleted"）

---


### `class PollingObserver`

纯 Python 轮询文件监控器

通过定期遍历目录并比较 .py 文件的 mtime 检测变更

> **提示**
> 1. 接口与 watchdog.observers.Observer 一致 (schedule/start/stop/join)
> 2. 轮询运行在后台守护线程，不会阻止进程退出
> 3. 仅监控 .py 文件的变更，避免不必要的开销
> 4. 忽略目录按目录名在任意层级剪枝；键统一「绝对化 + normcase」规范化
> ——Windows 大小写不同的路径写法、以及以相对路径调度的监控目录
> （如默认的 ``plugins`` 或 ``.``）都不会产生虚假删除/创建事件，
> 删除检测的前缀匹配在任意调度路径写法下均成立
> 5. 单个 handler 回调抛异常只记 warning，不会杀死轮询线程

- **interval** (`float`): 轮询间隔（秒） (默认: FILE_WATCH_POLL_INTERVAL_SECS)
- **ignore_dirs** (`Iterable[str`): | None] 忽略的目录名集合；

    None = 使用内置默认清单（FILE_WATCHER_IGNORED_DIRS），
    显式传入列表 = 整体替换（空列表 = 不忽略任何目录）

**示例**:

```python
observer = PollingObserver()
observer.schedule(MyHandler(), ".", recursive=True)
observer.start()
```


#### 方法列表


##### `__init__(interval: float = FILE_WATCH_POLL_INTERVAL_SECS, ignore_dirs: Iterable[str] | None = None)`

初始化轮询监控器

- **interval** (`float`): 轮询间隔（秒） (默认: FILE_WATCH_POLL_INTERVAL_SECS)
- **ignore_dirs** (`Iterable[str`): | None] 忽略的目录名集合

    (None = 内置默认清单；显式列表 = 整体替换)

---


##### `is_running -> bool`（property）

轮询线程是否仍在运行

**返回值**: 是否运行中

---


##### `schedule(event_handler: FileSystemEventHandler, path: str, recursive: bool = False) -> None`

注册事件处理器与监控目录

- **event_handler** (`FileSystemEventHandler`): 文件事件处理器
- **path** (`str`): 要监控的目录路径
- **recursive** (`bool`): 是否递归监控子目录 (默认: False)

---


##### `start() -> None`

记录初始快照后启动后台轮询线程

---


##### `stop() -> None`

请求停止轮询线程

---


##### `join(timeout: float | None = None) -> None`

等待轮询线程结束

- **timeout**: 最长等待秒数；None = 一直等到线程退出。轮询线程

    为守护线程，超时返回后线程仍会随 ``stop()`` 自行退出，不会
    阻塞调用方（事件循环线程内停止监控时传入有限超时）

---


##### `_walk_py(path: str, recursive: bool)`

遍历目录下的 .py 文件（跳过忽略目录）

**内部方法**

- **path** (`str`): 目录路径
- **recursive** (`bool`): 是否递归子目录

**返回值** (`Generator`): .py 文件路径生成器

---


##### `_key(path: str) -> str`（staticmethod）

路径归一键：绝对化 + normcase

**内部方法**
监控目录允许以相对路径调度（默认 ``plugins`` / CLI 的 ``.``），
键必须与删除检测的前缀（同为绝对化归一）在同一坐标系比较，
否则相对调度路径下删除事件永不触发；绝对化同时保证重叠 watch
（"." 与 "plugins"）的跨 watch 去重键一致。

---


##### `_dispatch(handler: FileSystemEventHandler, method: str, event_type: str, src_path: str) -> None`（staticmethod）

派发单个事件到 handler，回调异常只记 warning（轮询线程不因此死亡）

**内部方法**

---


##### `_snapshot() -> None`

记录所有 .py 文件的当前 mtime，作为变更比较基准

**内部方法**

---


##### `_run() -> None`

轮询主循环：比较 mtime 并在变更时回调处理器

除修改外补发创建 / 删除事件：本轮新出现的文件回调 ``on_created``，
stat 失败（已删除）的文件回调 ``on_deleted``。移动 = 旧路径删除 +
新路径创建（``on_moved`` 在轮询实现下不触发）。

**内部方法**

---

