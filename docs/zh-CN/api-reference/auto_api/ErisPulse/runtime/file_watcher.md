# `ErisPulse.runtime.file_watcher` 模块

---

## 模块概述


文件变更监控

提供文件系统变更检测能力

> **提示**
> 1. 通过定期比较 .py 文件的 mtime 检测变更
> 2. 接口与 watchdog.observers.Observer 保持一致 (schedule/start/stop/join)
> 3. 供运行时插件热重载（runtime/plugin_reload）与 CLI 热重载（CLI/commands/run）共用

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


#### 方法列表


##### `__init__(src_path: str)`

初始化文件变更事件

- **src_path** (`str`): 发生变更的文件路径

---


### `class PollingObserver`

纯 Python 轮询文件监控器

通过定期遍历目录并比较 .py 文件的 mtime 检测变更

> **提示**
> 1. 接口与 watchdog.observers.Observer 一致 (schedule/start/stop/join)
> 2. 轮询运行在后台守护线程，不会阻止进程退出
> 3. 仅监控 .py 文件的变更，避免不必要的开销

- **interval** (`float`): 轮询间隔（秒） (默认: 1.0)

**示例**:

```python
observer = PollingObserver()
observer.schedule(MyHandler(), ".", recursive=True)
observer.start()
```


#### 方法列表


##### `__init__(interval: float = 1.0)`

初始化轮询监控器

- **interval** (`float`): 轮询间隔（秒） (默认: 1.0)

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


##### `join() -> None`

等待轮询线程结束

---


##### `_walk_py(path: str, recursive: bool)`（staticmethod）

遍历目录下的 .py 文件

**内部方法**

- **path** (`str`): 目录路径
- **recursive** (`bool`): 是否递归子目录

**返回值** (`Generator`): .py 文件路径生成器

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

