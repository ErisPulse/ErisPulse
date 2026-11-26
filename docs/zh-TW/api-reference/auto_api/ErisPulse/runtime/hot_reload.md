# `ErisPulse.runtime.hot_reload` 模块

---

## 模块概述


热重载监控器基类

收敛各热重载监控器的共用骨架：

- 生命周期状态机：幂等启停（重复 start 返回 False、重复 stop 无操作）、
  启动前准备（无可监控对象返回 False）、停止清理
- 事件循环解析：构造 / 启动时捕获的循环优先，其次主循环注册表延迟回查
- 跨线程调度：重载协程经 ``run_coroutine_threadsafe`` 投递回主事件循环，
  循环未就绪时留痕跳过

子类实现检测机制与重载路由：轮询形态（后台线程 + ``_poll_once``）或
事件形态（外部监控器回调）；对应覆写 :meth:`_begin` / :meth:`_shutdown`。

**内部方法**

---

## 函数列表


### `_normalize_dist_name(name: str) -> str`

名称按 PEP 503 归一（``-`` / ``_`` / ``.`` 等价、小写；glob 场景同样适用）

---


## 类列表


### `class HotReloadWatcherBase(ABC)`

热重载监控器基类

内置监控范围 ACL（与 strict_mode_exceptions / watch_ignore_dirs 同族）：
deny 优先于 allow；allow 为空表示"除 deny 外全部"。名单元素支持 glob，
按组件名（插件名 / entry-point 名）与来源名（发行版名）归一后匹配——
子类在解析出组件名后经 :meth:`_target_matches` 过滤。

- **interval**: 轮询间隔秒数（语义随子类检测机制）
- **allow**: 白名单（组件名或来源名，glob 支持；空 = 全部）
- **deny**: 黑名单（优先于 allow）


#### 方法列表


##### `_list_hits(*names: str, patterns: tuple[str, ...]) -> bool`

名单匹配：任一模式（归一后 fnmatch）命中任一给定名字

---


##### `_target_matches(*names: str) -> bool`

监控范围 ACL：deny 命中即排除；allow 空表示全部，非空则须命中

---


##### `is_running -> bool`（property）

监控器是否已启动

**返回值**: 是否运行中

---


##### `start() -> bool`

启动监控（幂等）

**返回值**: 是否启动成功（已在运行或 :meth:`_prepare` 判定无可监控对象时为 False）

---


##### `stop() -> None`

停止监控（幂等）

---


##### `_prepare() -> bool`

**内部方法**
启动前准备：解析监控对象并建立初始状态

**返回值**: 是否存在可监控对象（False 时 :meth:`start` 不启动）

---


##### `_begin() -> None`

**内部方法**
启动检测机制（后台守护线程或外部监控器）；抛异常时 :meth:`start`
回滚运行状态

---


##### `_shutdown() -> None`

**内部方法** 停止检测机制并释放资源

---


##### `_run_polling_loop() -> None`

**内部方法**
轮询形态的线程入口：按间隔调用 :meth:`_poll_once`，异常 debug 留痕
不中断循环

---


##### `_poll_once() -> None`

**内部方法** 单轮扫描（轮询形态子类实现；事件形态子类无需覆写）

---


##### `_start_polling_thread(name: str) -> None`

**内部方法** 启动轮询守护线程（轮询形态子类的 _begin 实现）

---


##### `_shutdown_polling_thread(join_timeout: float) -> None`

**内部方法** 停止轮询守护线程（轮询形态子类的 _shutdown 实现）

---


##### `_capture_loop() -> None`

**内部方法**
捕获当前线程的运行中事件循环（构造 / 启动早于 ``sdk.run()`` 时无循环，
经 :meth:`_resolve_loop` 延迟回查）

---


##### `_resolve_loop() -> asyncio.AbstractEventLoop | None`

解析可用事件循环：捕获的循环优先，其次主循环注册表延迟回查

---


##### `_schedule(coro: Any, *, skip_log_key: str) -> None`

把重载协程调度回主事件循环

- **coro**: 重载协程（所有权移交本方法）
- **skip_log_key**: 循环未就绪时的留痕文案 i18n 键

---

