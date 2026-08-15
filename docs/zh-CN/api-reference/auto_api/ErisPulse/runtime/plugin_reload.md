# `ErisPulse.runtime.plugin_reload` 模块

---

## 模块概述


ErisPulse 本地插件热重载监控

监控插件文件夹（默认 ``plugins/``，可通过 ``ErisPulse.framework.plugins_dir``
配置）下 ``.py`` 文件的变更，变化时自动重新加载对应插件。

设计要点：
- 复用 CLI 的 :class:`PollingObserver`（纯 Python mtime 轮询，后台守护线程）
- 文件变更回调在线程中触发，通过 :func:`asyncio.run_coroutine_threadsafe`
  把重载协程调度回主事件循环执行，避免线程内直接 await
- 变更去抖：短时间（默认 1 秒）内的连续变更只触发一次重载

---

## 类列表


### `class _PluginChangeHandler(FileSystemEventHandler)`

> **内部方法**
插件文件变更处理器：.py 变更时调度重载协程


#### 方法列表


##### `on_modified(event)`

文件修改回调：去抖后调度重载

---


### `class PluginReloadWatcher`

本地插件热重载监控器

封装轮询文件监控器，监控插件文件夹变更并触发对应插件的重载回调。

- **on_reload** (`重载回调（接收插件名，返回协程），在主事件循环中执行`): - **interval**: 轮询间隔（秒，默认 1.0）

**示例**:
```python
>>> async def handle(name):
...     await sdk.reload_plugin(name)
>>> watcher = PluginReloadWatcher(handle)
>>> watcher.start()
>>> # ... 运行中 ...
>>> watcher.stop()
```


#### 方法列表


##### `is_running()`

监控器是否已启动

**返回值**: 是否运行中

---


##### `_plugin_dirs()`

解析插件目录列表（与 PluginFolderLoader 同源）

**返回值**: 插件目录字符串列表

---


##### `start()`

启动插件文件监控

**返回值** (`是否启动成功（无插件目录或已在运行返回`): False）

---


##### `stop()`

停止插件文件监控

---


##### `async _handle_change(src_path: str)`

> **内部方法**
将文件路径解析为插件名并触发重载回调

---


##### `async close()`

停止监控并等待后台线程结束

---

