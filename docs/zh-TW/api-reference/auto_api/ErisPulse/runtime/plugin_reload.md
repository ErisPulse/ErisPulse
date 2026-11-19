# `ErisPulse.runtime.plugin_reload` 模块

---

## 模块概述


ErisPulse 本地插件热重载监控

监控插件文件夹（默认 ``plugins/``，可通过 ``ErisPulse.framework.plugins_dir``
配置）下 ``.py`` 文件的变更，变化时自动重新加载对应插件。

设计要点：
- 复用 :class:`~ErisPulse.runtime.file_watcher.PollingObserver`（纯 Python mtime 轮询，后台守护线程）
- 消费 created / modified / deleted 三类事件：新增插件热装载、删除插件热卸载
  （复用加载器「发现不到即移除」语义）、修改触发热重载
- 文件变更回调在线程中触发，通过 :func:`asyncio.run_coroutine_threadsafe`
  把重载协程调度回主事件循环执行，避免线程内直接 await；事件循环支持延迟
  解析（启动早于 ``sdk.run()`` 时先记住 None，触发时经主循环注册表回查）
- 变更合并去抖：首个事件立即触发，窗口（FILE_RELOAD_DEBOUNCE_SECS）内的
  后续变更合并且窗口静默后统一补发一次（不丢弃）
- 重载失败且文件 mtime 又变化（编辑器原子保存的半写窗口）时单次重试

---

## 函数列表


### `resolve_plugin_name(src_path: str, plugin_dirs: list[str] | None = None) -> str | None`

**内部方法**
将插件文件路径解析为插件名（单文件取文件名，包形式取首段目录名）

供插件热重载的调度线程与 PluginReloadWatcher 回调共用。

---


## 类列表


### `class _PluginChangeHandler(FileSystemEventHandler)`

**内部方法**
插件文件变更处理器：created/modified/deleted 合并去抖后调度重载协程


#### 方法列表


##### `_stat_mtime(path: str) -> float | None`（staticmethod）

**内部方法** 读取文件 mtime，失败（已删除等）返回 None

---


##### `on_modified(event) -> None`

文件修改回调：合并去抖后调度重载

---


##### `on_created(event) -> None`

文件创建回调：新插件文件纳入热装载

---


##### `on_deleted(event) -> None`

文件删除回调：复用加载器「发现不到即移除」语义热卸载

---


##### `on_moved(event) -> None`

文件移动回调（轮询实现不触发，watchdog 实现接入时等价删除+创建）

---


##### `_flush_pending() -> None`

去抖窗口到期：补发窗口内合并的变更（可为空）

---


##### `close() -> None`

停止补发定时器（监控停止时调用）

---


##### `_resolve_loop() -> asyncio.AbstractEventLoop | None`

解析可用事件循环：构造时捕获的循环优先，其次主循环注册表延迟解析

---


##### `async _drain(paths: set[str]) -> None`

逐个触发重载回调；失败且文件仍在变化（半写窗口）时单次重试

---


### `class PluginReloadWatcher`

本地插件热重载监控器

封装轮询文件监控器，监控插件文件夹变更并触发对应插件的重载回调。

- **on_reload**: 重载回调（接收插件名，返回协程），在主事件循环中执行
- **interval**: 轮询间隔（秒，默认 FILE_WATCH_POLL_INTERVAL_SECS）

**示例**:

```python
async def handle(name):
    await sdk.reload_module(name)
watcher = PluginReloadWatcher(handle)
watcher.start()
# ... 运行中 ...
watcher.stop()
```


#### 方法列表


##### `is_running -> bool`（property）

监控器是否已启动

**返回值**: 是否运行中

---


##### `_plugin_dirs() -> list[str]`

解析插件目录列表（与 PluginFolderLoader 同源）

**返回值**: 插件目录字符串列表

---


##### `_resolve_ignore_dirs() -> list[str] | None`

**内部方法**
解析文件监控忽略目录：ErisPulse.framework.watch_ignore_dirs
（None = 内置默认清单；列表 = 整体替换；[] = 不忽略）

---


##### `start() -> bool`

启动插件文件监控

> **提示**
> 无运行事件循环时仍返回 True：事件循环经主循环注册表延迟解析
> （``sdk.run()`` 启动后自动可用），此前触发的变更会记 warning 跳过。

**返回值**: 是否启动成功（无插件目录或已在运行返回 False）

---


##### `stop() -> None`

停止插件文件监控

---


##### `async _handle_change(src_path: str) -> Any`

**内部方法**
将文件路径解析为插件名并触发重载回调（透传回调返回值）

---


##### `async close() -> None`

停止监控并等待后台线程结束

---

