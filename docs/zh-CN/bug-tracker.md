# Bug 追踪器

本文档记录 ErisPulse SDK 的已知 Bug 及其修复情况，按修复版本时间顺序排列。

> **写给读者**
> 没有任何软件天生完美，再细心的开发者也会留下小错误。本追踪收录的都是对运行有实际影响的问题——那些过于细微、连「轻微」等级都达不到的瑕疵并不会出现在这里。清单中「严重」项看起来不少，但公开记录这些 Bug 的初衷是让排查与回溯更顺畅，而非制造焦虑：能被看见、被记录、被修复的问题，本身就是项目不断变好的证明。看到这份清单不必紧张，它是一份排查工具，而不是恐惧的来源。

> **如何阅读 & 维护约定**
> - 每条 Bug 记录包含问题描述、根因分析、影响版本范围、修复方案等结构化字段，建议升级前先检索「影响版本」是否覆盖当前使用的版本。
> - 如需新增 Bug 条目，请在对应位置补充内容，遵循下文字段规范与严重性/类型分类。

---

## 字段说明

### 必填字段

| 字段 | 说明 |
|------|------|
| **问题** | Bug 的外在表现、用户可观察到的异常现象。尽量给出报错信息或典型场景 |
| **原因** | 根因分析，指向具体的代码缺陷（含「根因链路」图示用于复杂场景） |
| **影响版本** | 受影响的版本区间，格式 `引入版本 - 修复版本`（含两端 dev 版本） |
| **修复版本** | 修复该 Bug 的具体版本号 |
| **修复内容** | 修复方案的简要描述，含关键代码变更点 |
| **修复日期** | 对应修复版本的发布日期，采用 `YYYY/MM/DD` 格式 |
| **严重性** | 按下文「严重性分级」标注 |
| **类型** | 按下文「类型分类」标注，可组合（如 `适配器 / 路由`） |

### 可选字段

| 字段 | 说明 | 适用场景 |
|------|------|---------|
| **复现步骤** | 触发该 Bug 的最小可复现路径 | 复杂 Bug、偶发性 Bug 建议补充 |
| **关联** | 相关 Issue / PR / Commit 链接 | 有外部讨论记录时补充 |
| **回归测试** | 验证修复、防止再次回归的测试用例位置 | 已编写对应 pytest 用例时补充 |

---

## 严重性分级

| 标识 | 级别 | 判定标准 | 典型表现 |
|------|------|---------|---------|
| 🔴 | 严重 | 导致进程崩溃、数据丢失/损坏、核心功能完全不可用、安全漏洞 | OOM Kill、消息无法发送、模块无法加载、热重载失败 |
| 🟡 | 中等 | 功能异常但有规避路径、非核心功能失效、偶发问题 | 状态判断错误、重复触发、缓存过期、错误提示不准 |
| 🟢 | 轻微 | 不影响核心功能、仅代码质量或体验问题、潜在风险未爆发 | 弃用 API、死代码、缺失 warning 日志 |

---

## 类型分类

| 类型 | 覆盖范围 |
|------|---------|
| 配置系统 | `ConfigManager`、配置读写、配置 Schema、热更新 |
| 事件系统 | `Event` 模块（command/message/notice/request/meta）、事件分发、处理器注册 |
| 适配器 | `AdapterManager`、`BaseAdapter`、账户解析、Bot 状态、中间件 |
| 路由 | `RouterManager`、HTTP/WebSocket/SSE 路由、限流、CORS |
| 客户端 | `HttpClient`、`ClientWebSocket`、aiohttp 封装 |
| 存储 | `StorageManager`、SQLite、SQL 构建器、嵌套键 |
| 加载系统 | `Loader`、`LazyModule`、`ModuleInitializer`、严格模式、模块发现 |
| CLI | `epsdk` 命令、`init`/`run`/`install`、参数解析、信号处理 |
| 运行时 | `sdk.run`/`restart`/`uninit`、生命周期、信号、子进程 |

---

## 条目模板

新增 Bug 条目请遵循以下格式：

```markdown
### [BUG-XXX] 标题

**问题**: 问题描述（报错信息或典型现象）
**原因**: 根因分析
**影响版本**: 引入版本 - 修复版本
**修复版本**: x.x.x
**修复内容**: 修复方案
**修复日期**: YYYY/MM/DD

<!-- 可选字段 -->
**复现步骤**: （复杂 Bug 建议补充）
**关联**: （Issue/PR 链接）
**回归测试**: （验证用例路径）

**严重性**: 🔴 严重 | 🟡 中等 | 🟢 轻微
**类型**: 配置系统 / 事件系统 / 适配器 / 路由 / 客户端 / 存储 / 加载系统 / CLI / 运行时
```

---

## 统计概览

| 严重性 | 数量 |
|--------|------|
| 🔴 严重 | 14 |
| 🟡 中等 | 12 |
| 🟢 轻微 | 2 |
| **合计** | **28** |

| 类型 | 数量 |
|------|------|
| 适配器 | 6 |
| 配置系统 | 5 |
| 事件系统 | 5 |
| CLI | 3 |
| 存储 | 3 |
| 加载系统 | 3 |
| 路由 | 2 |
| 客户端 | 1 |
| 运行时 | 1 |

> 注：单条 Bug 可归属多个类型，上表按主类型统计。

---

## 已修复的 Bug

### [BUG-001] 事件处理器重复注册导致事件被多次处理

**问题**: 使用多个 `@message` / `@notice` 等装饰器注册处理器时，同一事件会被重复触发多次，导致命令被执行多遍、日志重复输出。

**原因**: `BaseEventHandler` 向适配器事件总线注册处理器时缺少去重逻辑，每个装饰器都会向总线挂载一次，事件分发时被多次调用。

**影响版本**: 2.2.0-dev.0 - 2.2.1-dev.0

**修复版本**: 2.2.1-dev.0

**修复内容**: 优化 `BaseEventHandler`，确保每个事件类型只向适配器注册一次处理器，避免重复触发。

**修复日期**: 2025/08/18

**严重性**: 🔴 严重

**类型**: 事件系统

---

### [BUG-002] Init 命令适配器配置路径类型错误

**问题**: 使用 `ep init` 命令进行交互式初始化时，选择配置适配器会出现类型错误：

```
交互式初始化失败: unsupported operand type(s) for /: 'str' and 'str'
```

**原因**: 2.3.7 版本调整配置文件路径时，方法参数类型不一致。`_configure_adapters_interactive_sync` 接收 `str` 类型参数，但内部使用 `Path` 的 `/` 操作符拼接路径。

**影响版本**: 2.3.7 - 2.3.9-dev.1

**修复版本**: 2.3.9-dev.1

**修复内容**: 将 `_configure_adapters_interactive_sync` 方法的参数类型从 `str` 改为 `Path`，调用时直接传递 `Path` 对象。

**修复日期**: 2026/03/23

**严重性**: 🟡 中等

**类型**: CLI

---

### [BUG-003] 重启后命令事件失效

**问题**: 调用 `sdk.restart()` 后，通过 `@command` 注册的命令无法被触发，表现为发送命令后机器人无响应。

**原因**: `adapter.shutdown()` 清空事件总线后，`BaseEventHandler` 的 `_linked_to_adapter_bus` 状态未重置为 `False`，导致 `_process_event` 方法认为已经挂载到适配器总线，跳过重新挂载操作。

**影响版本**: 2.2.x - 2.4.0-dev.2

**修复版本**: 2.4.0-dev.3

**修复内容**: 引入 `_linked_to_adapter_bus` 状态追踪，`_clear_handlers()` 断开总线连接后，下次 `register()` 自动重新挂载，适配 shutdown/restart 场景。

**修复日期**: 2026/04/09

**严重性**: 🔴 严重

**类型**: 事件系统

---

### [BUG-004] 生命周期事件处理器未清理

**问题**: `sdk.restart()` 后，旧的生命周期事件处理器仍然存在并重复触发，导致同一个事件被多次处理。

**原因**: `lifecycle._handlers` 字典在 `uninit()` 时从未被清理，restart 后旧处理器与新处理器同时存在。

**影响版本**: 2.3.0 - 2.4.0-dev.2

**修复版本**: 2.4.0-dev.3

**修复内容**: 在 `Uninitializer` 的清理流程末尾（所有事件提交之后），清空 `lifecycle._handlers`。

**修复日期**: 2026/04/09

**严重性**: 🟡 中等

**类型**: 运行时

---

### [BUG-005] Event.is_friend_add/is_friend_delete 的 detail_type 与 OB12 标准不一致

**问题**: `Event.is_friend_add()` 检查 `detail_type == "friend_add"`，`Event.is_friend_delete()` 检查 `detail_type == "friend_delete"`，但 OneBot12 标准定义的 `detail_type` 值为 `"friend_increase"` 和 `"friend_decrease"`。与 `notice.py` 中 `on_friend_add`/`on_friend_remove` 装饰器使用的值不一致，导致通过装饰器注册的处理器触发时，对应的 `is_friend_add()`/`is_friend_delete()` 判断方法返回 `False`。

**原因**: `wrapper.py` 中使用了非标准的命名，而 `notice.py` 使用了正确的 OB12 标准命名。

**影响版本**: 实装至今

**修复版本**: 2.4.2-dev.1

**修复内容**: 将 `is_friend_add()` 的匹配值从 `"friend_add"` 改为 `"friend_increase"`，`is_friend_delete()` 从 `"friend_delete"` 改为 `"friend_decrease"`。

**修复日期**: 2026/04/13

**严重性**: 🟡 中等

**类型**: 事件系统

---

### [BUG-006] adapter.clear() 未清理 _started_instances 导致重启后状态不正确

**问题**: `AdapterManager.clear()` 方法清除了 `_adapters`、`_adapter_info`、处理器和 `_bots`，但遗漏了 `_started_instances` 集合。如果适配器正在运行时调用 `clear()`，`_started_instances` 会保留悬空引用，导致重启后状态判断错误。

**原因**: 2.4.0-dev.1 引入 `_started_instances` 时未在 `clear()` 中同步清理。

**影响版本**: 2.4.0-dev.1 - 2.4.2-dev.0

**修复版本**: 2.4.2-dev.1

**修复内容**: 在 `clear()` 方法中添加 `self._started_instances.clear()`。

**修复日期**: 2026/04/13

**严重性**: 🟡 中等

**类型**: 适配器

---

### [BUG-007] command.wait_reply() 使用已弃用的 asyncio.get_event_loop()

**问题**: `CommandHandler.wait_reply()` 方法使用 `asyncio.get_event_loop()` 创建 future 和获取时间戳，该方法在 Python 3.10+ 中已弃用，在异步上下文中应使用 `asyncio.get_running_loop()`。与同文件中 `wrapper.py` 的 `wait_for()` 方法使用的 `get_running_loop()` 不一致。

**原因**: 开发时使用了旧版 API，后续新增的 `wait_for()` 使用了正确的 API 但未回溯修复旧代码。

**影响版本**: 2.3.0-dev.0

**修复版本**: 2.4.2-dev.1

**修复内容**: 将 `command.py` 中两处 `asyncio.get_event_loop()` 替换为 `asyncio.get_running_loop()`。

**修复日期**: 2026/04/13

**严重性**: 🟢 轻微

**类型**: 事件系统

---

### [BUG-008] Bot 离线事件在 shutdown 过程中被重复提交

**问题**: 调用 `adapter.shutdown()` 关闭所有适配器时，`_update_bot_status()` 会在关闭流程中反复提交 Bot 离线事件，导致同一批 Bot 被多次标记离线并触发多次 `adapter.bot.offline` 生命周期事件。

**原因**: 2.4.0-dev.1 引入的 Bot 状态追踪系统未在 `shutdown()` 期间设置"正在关闭"标志，`_update_bot_status()` 无法区分正常离线与关闭流程中的级联离线。

**影响版本**: 2.4.0-dev.1 - 2.4.2-dev.1

**修复版本**: 2.4.2-dev.1

**修复内容**: 在 `AdapterManager` 中新增 `_is_being_shutdown` 标志，`shutdown()` 开始时置为 True、结束时清除；`_update_bot_status()` 检查该标志后跳过关闭过程中的重复提交。

**修复日期**: 2026/04/21

**严重性**: 🟡 中等

**类型**: 适配器

---

### [BUG-009] LazyModule 同步访问 BaseModule 导致未初始化完成

**问题**: 用户在同步上下文中访问懒加载的 BaseModule 属性时，模块使用 `loop.create_task()` 异步初始化但不等待，导致属性访问时可能未初始化完成，引发竞态条件。

**原因**: `_ensure_initialized()` 对 BaseModule 使用 `loop.create_task(self._initialize())` 后立即返回，未确保初始化完成。

**影响版本**: 2.4.0-dev.0 - 2.4.2-dev.1

**修复版本**: 2.4.2-dev.2

**修复内容**: 在同步上下文中，BaseModule 的初始化改为使用 `asyncio.run(self._initialize())`，确保初始化完成后再返回。保持透明代理特性，用户无需感知同步/异步差异。

**修复日期**: 2026/04/21

**严重性**: 🟡 中等

**类型**: 加载系统

---

### [BUG-010] 配置系统多线程写入导致数据丢失

**问题**: 在多线程环境下，多个线程同时调用 `config.setConfig()` 时，`_flush_config()` 读取-修改-写入操作不是原子性的，可能导致部分写入丢失。

**原因**: `_flush_config()` 虽然使用了 `RLock`，但文件读取和写入之间没有文件锁保护，且 `_schedule_write` 的 Timer 可能被多次触发导致覆盖。

**影响版本**: 2.3.0 - 2.4.2-dev.1

**修复版本**: 2.4.2-dev.2

**修复内容**:
1. 添加文件锁机制（`_file_lock`）确保文件操作原子性
2. 使用临时文件写入后原子性重命名（`os.replace`/`os.rename`）
3. 改进 `_schedule_write` 的 Timer 取消和重新调度逻辑

**修复日期**: 2026/04/21

**严重性**: 🔴 严重

**类型**: 配置系统

---

### [BUG-011] Windows 下 CTRL+C 无法停止程序

**问题**: 在 Windows 上直接运行 `python main.py` 时，按下 CTRL+C 无法终止程序。程序正常启动并输出路由服务器信息后，CTRL+C 完全无响应，只能通过任务管理器强杀进程。而通过 `epsdk run` 启动时可以正常停止——但 `epsdk run` 是通过子进程模型运行的。

**原因**: Hypercorn ASGI 服务器的 `serve()` 函数内部通过 `signal.signal(SIGINT, handler)` 注册了自己的 SIGINT 处理器，覆盖了 Python 默认的 `KeyboardInterrupt` 处理机制。当通过 `asyncio.create_task()` 启动 Hypercorn 作为后台任务时，Hypercorn 的内部 shutdown 流程无法正常触发（因为它期望的是 `worker_serve` 模式），导致 CTRL+C 信号被 Hypercorn 吞掉但不会引发任何清理动作。

**影响版本**: 2.3.6 - 2.4.2

**修复版本**: 2.4.3-dev.0

**修复内容**:
1. 将 ASGI 服务器从 Hypercorn 切换为 Uvicorn（`pyproject.toml` 依赖变更）
2. 使用 `uvicorn.Server._serve()` 直接启动服务器，**绕过** `capture_signals()` 信号处理上下文管理器
3. 通过 `server.should_exit = True` 实现优雅停止，超时则取消后台任务
4. 同步移除子进程运行模型和 `runtime/cleanup.py` 清理模块（子进程清理机制不再需要）

**修复日期**: 2026/04/28

**严重性**: 🔴 严重

**类型**: CLI / 运行时

---

### [BUG-012] 热重启后已更新模块的 Python 代码未生效

**问题**: 执行 `sdk.restart()` 软重启后，已通过 `epsdk install` 升级的模块/适配器的新代码（如新增 API 路由）不生效，仍运行旧版本逻辑。必须完全重启进程才能加载最新代码。

**原因**: `_do_restart()` 在重新初始化时调用 `entry_point.load()`，但该函数从 `sys.modules` 返回了缓存的旧版本模块对象，而非从磁盘重新加载。

**影响版本**: 早期版本 - 2.4.3-dev.1

**修复版本**: 2.4.3-dev.1

**修复内容**: 在 `uninit()` 后、`init()` 前清理 `sys.modules` 中已加载模块/适配器包的缓存，使 `entry_point.load()` 从磁盘加载最新代码。新增 `_collect_top_level_modules()` 与 `_invalidate_module_cache()` 辅助方法，通过 `top_level.txt` 或 entry-point value 推导顶层模块名。

**修复日期**: 2026/05/03

**严重性**: 🔴 严重

**类型**: 加载系统 / 运行时

---

### [BUG-013] 模块加载策略排序逻辑错误

**问题**: `ModuleLoadStrategy` 提供了 `priority` 字段用于声明模块的初始化优先级，但加载策略的实现存在失误，导致模块未按预期的优先级顺序初始化，实际按 `entry_points()` 的默认顺序加载。当模块间存在加载依赖时，无法通过 `priority` 确保正确的初始化先后关系。

**原因**: 加载策略的实现中排序逻辑有误，`initialize_modules()` 未使用 `priority` 对模块列表进行排序。

**影响版本**: 2.3.4 - 2.4.5-dev.2

**修复版本**: 2.4.5-dev.3

**修复内容**: 在 `initialize_modules()` 遍历前，按 `priority` 降序排序模块列表。同 priority 的模块保持原有相对顺序（稳定排序）。

**修复日期**: 2026/05/15

**严重性**: 🟡 中等

**类型**: 加载系统

---

### [BUG-014] 适配器中间件返回 None 导致事件数据丢失

**问题**: `adapter.emit()` 在执行 OneBot12 中间件链时，如果某个中间件返回 `None`（例如忘记 `return data`），后续中间件和所有事件处理器收到的 `processed_data` 变为 `None`，导致事件处理完全失效。

**原因**: 中间件链的实现 `processed_data = await middleware(processed_data)` 未检查返回值是否为 `None`，直接覆盖了上一步的处理结果。

**影响版本**: unknown - 2.4.5-dev.3

**修复版本**: 2.4.5-dev.4

**修复内容**: 中间件返回 `None` 时忽略该返回值，保留原数据继续传递，并输出 warning 级别日志。

**修复日期**: 2026/05/15

**严重性**: 🔴 严重

**类型**: 适配器 / 事件系统

---

### [BUG-015] 配置文件路径依赖工作目录

**问题**: `ConfigManager` 的配置文件路径默认为相对路径 `"config/config.toml"`，在运行时依赖 `os.getcwd()` 解析。如果工作目录在运行期间发生变化（例如通过 `os.chdir()`），配置文件的读写操作会指向错误的位置，导致配置丢失或读取到旧数据。

**原因**: `__init__` 中直接存储相对路径，未在初始化时将其解析为绝对路径。

**影响版本**: 2.3.7 - 2.4.5-dev.3

**修复版本**: 2.4.5-dev.4

**修复内容**: 在 `ConfigManager.__init__()` 中，如果传入的路径为相对路径，自动通过 `os.path.abspath()` 解析为绝对路径。

**修复日期**: 2026/05/15

**严重性**: 🟡 中等

**类型**: 配置系统

---

### [BUG-016] BaseStorage 将存储值 None 与键不存在混淆

**问题**: `BaseStorage.get_multi()` / `__getattr__()` 无法区分"键不存在"与"键的值就是 `None`"两种情况，用户显式存入 `None` 后再读取时会被当作键不存在处理。

**原因**: 取值逻辑直接用 `value is None` 判断键是否存在，缺少独立的"缺失"标记。

**影响版本**: 早期版本 - 2.4.6-dev.6

**修复版本**: 2.4.6-dev.6

**修复内容**: 引入 `_SENTINEL` 哨兵值区分"键不存在"与"值为 None"，二者不再混淆。

**修复日期**: 2026/06/07

**严重性**: 🟡 中等

**类型**: 存储

---

### [BUG-017] WebSocket 路由 auto_accept 标志在服务重启后丢失

**问题**: 服务重启（如 `sdk.restart()`）后，所有 WebSocket 路由的 `auto_accept` 配置都变回 `False`，原本期望自动 accept 的连接变为挂起状态，客户端长时间收不到响应，表现为 WS 连接卡死。

**原因**: `_restore_routes_from_records()` 在从持久化记录恢复路由时把 `auto_accept` 硬编码为 `False`，未读取原始记录中的值；同时路由存储元组也从二元组扩展为三元组时未同步更新恢复逻辑。

**影响版本**: 2.3.8-dev.0 - 2.4.6-dev.6

**修复版本**: 2.4.6-dev.6

**修复内容**: 路由存储元组扩展为 `(handler, auth_handler, auto_accept)`，`_restore_routes_from_records()` 从记录读取真实 `auto_accept` 值而非硬编码 `False`。

**修复日期**: 2026/06/07

**严重性**: 🔴 严重

**类型**: 路由

---

### [BUG-018] HTTP/WS 客户端并发调用导致崩溃与连接泄漏

**问题**: `Core/client.py` 的 HTTP 与 WebSocket 客户端在并发场景下存在多个稳定性缺陷，会导致连接泄漏或进程崩溃：
- 多协程并发调用 `ClientWebSocket.receive()` 时 aiohttp 抛出 `Concurrent call to receive() is not allowed`
- `_get_http_session()` / `_get_ws_session()` 并发调用可能创建多个 session 且 `_drain_sessions()` 未关闭旧连接，造成连接泄漏
- `request()` 的异常捕获顺序错误：`except ClientConnectionError`（ErisPulse 异常）永不触发，aiohttp 的连接错误被通用 `except Exception` 接住，导致"连接重试 + session 重建"逻辑（死代码）从未执行
- `send_json()` 忽略 `mode="binary"` 参数；`_get_ws_session()` 未传入默认请求头

**原因**: 客户端初次实现（2.4.6-dev.5）缺少并发保护与异常分类，对 aiohttp 异常体系与 ErisPulse 自定义异常的继承关系处理不当。

**影响版本**: 2.4.6-dev.5 - 2.4.8

**修复版本**: 2.4.8

**修复内容**:
1. 新增 `_recv_lock` 序列化所有 `receive()` / `receive_text()` / `receive_bytes()` 调用
2. 新增 `_session_lock` 保护 session 创建；`_drain_sessions()` 改为异步方法并真正关闭旧 session
3. 重构 `request()` 异常捕获顺序：`asyncio.TimeoutError` → `aiohttp.ClientConnectionError`（触发 session 重建）→ `aiohttp.ClientError` → `ClientError`（透传）→ `Exception`
4. 修复 `send_json()` 的 mode 处理、`_get_ws_session()` 默认请求头透传、`close()` 的并发竞态、`HttpResponse.__aexit__` 重复 `release()`

**修复日期**: 2026/06/12

**严重性**: 🔴 严重

**类型**: 客户端

---

### [BUG-019] 适配器热重载时路由冲突导致重载失败

**问题**: 第三方模块（如 Dashboard）触发适配器热重载，或适配器启动失败重试时，因上次注册的旧路由（如 `onebot11_default`）未清理，抛出 `WebSocket路径 ... 已注册` 冲突，导致重载失败。需要完全重启进程才能恢复。

**原因**: `AdapterManager.shutdown()` 仅以 `unregister_all_by_namespace(platform)` 清理路由，但适配器（如 OneBot11）以 `onebot11_{account_name}` 为命名空间注册 WS 路由，颗粒度不匹配导致清理为空操作；启动失败重试路径也未清理上次残留路由。

**影响版本**: 早期版本 - 2.4.9

**修复版本**: 2.4.9

**修复内容**:
1. 路由注册时通过 `current_owner` ContextVar 自动追踪 `owner → namespace` 归属关系
2. 新增 `unregister_all_by_owner(owner)`，停止/重启时同时按 owner 清理，覆盖细颗粒度命名空间
3. 新增 `_stop_adapter(platform)` 原语（"停止即清理"），将停止适配器与回收其注册的资源绑定在一次调用里，`restart()` 和启动失败重试均经此入口
4. 新增框架级 `adapter.restart(platform)` API，第三方模块应调用此方法而非直接操作适配器实例

**修复日期**: 2026/06/12

**严重性**: 🔴 严重

**类型**: 适配器 / 路由

---

### [BUG-020] 子进程模式 `ep run <script>` 找不到脚本所在目录的子包

**问题**: 使用 `ep r .\main.py` 非热重载模式运行脚本时，如果脚本有相对导入（如 `from qg import ...`），会报 `No module named 'qg'` 错误。而 `--reload` 模式可以正常运行。

**原因**: 非热重载模式直接调用 `runpy.run_path()` 执行脚本，该函数不会自动将脚本所在目录加入 `sys.path`。而 `--reload` 模式通过 `subprocess.Popen` 子进程运行，子进程自动继承当前工作目录，`sys.path[0]` 即为脚本所在目录，所以能正常工作。

**影响版本**: 2.5.0 - 2.5.2-dev.0

**修复版本**: 2.5.2-dev.0

**修复内容**: 在 `runpy.run_path()` 调用前，手动将脚本所在目录插入 `sys.path[0]`。

**修复日期**: 2026/06/27

**严重性**: 🟡 中等

**类型**: CLI

---

### [BUG-021] SQL 查询构建器拒绝合法通配符和列表达式

**问题**: `SQLiteQueryBuilder` 的 `_build_select_sql()` 对所有 SELECT 列调用 `_validate_identifier()`，该函数使用严格的白名单正则 `^[a-zA-Z_][a-zA-Z0-9_]*$`，导致合法 SQL 语法被误判为不安全列名：

- `SELECT *` — `*` 是 SQL 标准通配符
- `SELECT COUNT(*)` — 聚合函数
- `SELECT users.name` — 限定列名
- `SELECT col AS alias` — 列别名

其中 `Select("*")` 被 Cron 等模块使用，导致模块 `on_load` 执行失败，模块无法加载。

**原因**: 2.4.6 版本增强了 SQL 注入防护，引入了 `_validate_identifier()` 白名单校验。该校验应用于所有列名，但未区分读取端（SELECT/ORDER BY）和写入端（INSERT/UPDATE）。SELECT 列允许复杂的 SQL 表达式，不应受简单标识符白名单限制。

**影响版本**: 2.4.6 - 2.5.2-dev.1

**修复版本**: 2.5.2-dev.2

**修复内容**: 将 SELECT/ORDER BY 的列校验从白名单模式改为黑名单模式：
1. 新增 `_validate_select_column()` 函数，仅拦截 SQL 注入危险字符（`;` `'` `"` `--` `/*` `*/` `\x00` 换行符）
2. 允许任意合法 SQL 列表达式（`*`、`table.*`、`table.column`、`COUNT(*)`、`col AS alias` 等）
3. INSERT/UPDATE 列名仍保持严格白名单校验（仅允许简单标识符）

**修复日期**: 2026/06/29

**严重性**: 🔴 严重

**类型**: 存储

---

### [BUG-022] _resolve_account() 账户解析回归（_accounts_data 未填充）

**问题**: 2.5.2 配置系统重构后，声明了 `AccountConfigClass` 的多账户适配器在调用 `wait_reply`、`reply` 等需要发送消息的方法时，报错 `ValueError("未声明 AccountConfigClass，无法解析账户")`。即使适配器正确配置了多账户信息，账户解析仍然失败。

**原因**: 2.5.2-dev.5 将 `_load_accounts()`（负责读取配置 + 校验 + 填充 `_accounts_data`）重构为 `_ensure_accounts_exist()`（仅生成配置模板），但 `_resolve_account()` 仍检查 `self._accounts_data is None`。由于 `_ensure_accounts_exist()` 不再填充 `_accounts_data`，该属性始终为 `None`，导致 `_resolve_account()` 提前返回 `(None, None)`，账户解析完全失效。

**根因链路**:
```
_load_accounts() 被删除
  → __init__ 不再填充 _accounts_data
    → _accounts_data 恒为 None
      → _resolve_account() 检查 _accounts_data is None → return (None, None)
        → 下游调用 _resolve_account 的地方（如 call_api）拿到 None
          → 触发报错
```

**影响版本**: 2.5.2-dev.5 - 2.5.2

**修复版本**: 2.5.3

**修复内容**: 在 `BaseAdapter.__init__` 中，`_ensure_accounts_exist()` 之后恢复 `_accounts_data` 的填充：
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # 恢复填充，数据源为实时读取的 accounts 属性
```
`_resolve_account()` 逻辑保持不变，完全向后兼容：
- 不声明 `AccountConfigClass` 的适配器：`_accounts_data` 保持 `None` → 返回 `(None, None)`
- 声明了 `AccountConfigClass` 的适配器：`_accounts_data` 被填充 → 正常解析
- 覆写 `_load_accounts` 或手动设置 `_accounts_data` 的适配器：在 `super().__init__()` 后覆盖，优先级最高

**修复日期**: 2026/07/07

**严重性**: 🔴 严重

**类型**: 适配器 / 配置系统

---

### [BUG-023] 修改账户配置后适配器缓存未刷新导致账户解析失败

**问题**: 用户通过 Dashboard 修改多账户适配器的账户配置（如填写 token）后，适配器仍使用旧缓存，调用发送消息相关方法时报 `未找到可用账户 (account_id=default)`。必须重启进程才能让新配置生效。

**原因**: `_accounts_data` 仅在 `BaseAdapter.__init__` 时从配置存储读取一次，之后不再刷新。`AdapterManager._run_adapter()` 与 `restart()` 在调用 `adapter.start()` 前未重新读取账户配置，导致缓存与实际配置脱节。

**影响版本**: 2.4.6 - 2.5.4

**修复版本**: 2.5.4

**修复内容**: 在 `AdapterManager._run_adapter()` 和 `restart()` 中，调用 `adapter.start()` 之前刷新 `adapter._accounts_data = adapter.accounts`，确保每次启动时使用最新配置。

**修复日期**: 2026/07/09

**严重性**: 🔴 严重

**类型**: 适配器 / 配置系统

---

### [BUG-024] storage.set() 写入大数字 ID 键时触发 OOM Kill

**问题**: 调用 `storage.set()` 写入包含大纯数字段（如 QQ 群号 `871684833`）的嵌套键路径时，进程被容器 OOM Kill（退出码 -9），服务直接崩溃无法恢复。

**原因**: `_set_nested_value` 的递归实现中，嵌套键路径里的纯数字段被 `isdigit()` 误判为列表索引，触发 `current.extend([None] * (index - len(current) + 1))`，试图分配数亿元素的列表，瞬间耗尽内存。

**根因链路**:
```
键路径包含纯数字段（如群号 871684833）
  → isdigit() 误判为数组索引
    → extend([None] * (871684833 - len(current) + 1))
      → 尝试分配数亿元素
        → 内存耗尽 → 容器 OOM Kill（退出码 -9）
```

**影响版本**: 2.5.1 - 2.5.5

**修复版本**: 2.5.5

**修复内容**:
1. 预创建中间层时始终使用字典，不再根据下一段是否为数字猜测容器类型
2. 设置最终值时，仅当容器本身已是列表且索引小于 `STORAGE_MAX_LIST_INDEX`（10000）时才按索引处理，超大索引安全跳过
3. 将递归实现改为迭代实现，消除原代码中潜在的无限递归风险
4. 新增 `STORAGE_MAX_LIST_INDEX` 常量到 `Core/constants.py`，集中管理索引安全上限

**修复日期**: 2026/07/10

**复现步骤**:
```python
# 写入包含大数字段（如 QQ 群号）的嵌套键路径即可触发
await sdk.storage.aset("groups.871684833.name", "某群")
# → 进程内存瞬间飙升，被 OOM Kill
```

**回归测试**: `tests/unit/test_unit_storage.py` 新增 4 个回归用例
- `test_nested_key_numeric_segment_as_dict_key` — 精确复现 OOM 场景
- `test_nested_key_numeric_segment_multiple` — 多个连续数字段均作为字典键
- `test_nested_key_existing_list_index_set_within_limit` — 已有列表合理索引写入
- `test_nested_key_list_index_safety_limit` — 超大索引安全限制验证

**严重性**: 🔴 严重

**类型**: 存储

---

### [BUG-025] on_config_update 回调未被核心路由

**问题**: `on_config_update(old, new)` 回调在基类（`BaseModule` / `BaseAdapter`）中已定义，但框架核心未将其与配置变更事件关联。实际表现：通过配置管理面板改配置时可以触发，而手动编辑 `config.toml` 或代码调用 `setConfig()` 时不会触发 `on_config_update`。

**原因**: `ConfigManager` 在配置变更时会发射 `config.set` / `config.updated` 生命周期事件，但缺少将这些事件转发到各组件 `on_config_update` 方法的订阅逻辑。

**根因链路**:
```
核心未订阅 config.set / config.updated
  → 配置变更事件无转发
    → on_config_update 未被调用
      → 手动编辑文件 / 代码 setConfig 不触发热更新回调
```

**影响版本**: 全版本

**修复版本**: 2.6.2

**修复内容**: `ModuleManager` / `AdapterManager` 注册 `config.set`（覆盖代码 `setConfig()` 路径）与 `config.updated`（覆盖手动编辑文件路径）事件订阅，按配置键前缀匹配后调用对应组件的 `on_config_update`，传入类型安全的配置对象。同时修复 `_flush_config()` 写入文件后未同步 `_config_mtime` 的问题，避免框架自身写入被文件监听任务误判为外部修改而重复触发 `config.updated`。

**兼容性说明**: 配置热更新现由框架核心统一维护。此前由配置管理面板代为触发的逻辑已移除，升级框架后需同步升级配置管理面板，否则会出现重复触发（核心 + 面板各调一次）。`on_config_update` 方法签名与语义保持不变，子类无需修改。

**修复日期**: 2026/07/23

**严重性**: 🟡 中等

**类型**: 配置系统

---

### [BUG-026] notice/request 事件 reply 目标推断错误

**问题**: 在群通知事件（如成员加群 `group_member_increase`）中调用 `event.reply()`，消息被发送到触发事件的用户私聊，而非事件所在的群。好友通知事件同理，回复目标可能错乱。

**原因**: `infer_receive_type()` 将事件的 `detail_type` 直接当作会话类型返回。对于 message 事件这是正确的（`detail_type` 值 `private`/`group` 即会话类型），但 notice/request 事件的 `detail_type` 是语义子类型（如 `group_member_increase`、`friend_increase`），不是会话类型。后续的 `convert_to_send_type()` 和 `get_id_field()` 在映射表中找不到该值，回退到默认的 `"user"` / `"user_id"`，导致回复目标错乱。

**根因链路**:
```
notice 事件 detail_type="group_member_increase"
  → infer_receive_type() 直接返回 "group_member_increase"
    → convert_to_send_type("group_member_increase") 不在映射表 → 回退 "user"
    → get_id_field("group_member_increase") 不在映射表 → 回退 "user_id"
      → target_id = event["user_id"]  ← 新成员私聊（而非群）
```

**影响版本**: 全版本

**修复版本**: 2.7.0-dev.3

**修复内容**: `infer_receive_type()` 增加判断——`detail_type` 只有在是已知会话类型（标准类型或自定义类型）时才直接返回；否则根据 ID 字段（`group_id` / `channel_id` / `user_id` 等）推断正确的会话类型。

**回归测试**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference`（10 用例）

**修复日期**: 2026/07/29

**严重性**: 🟢 轻微

**类型**: 事件系统

---

### [BUG-027] 路由限流清理任务使用固定窗口导致长窗口限流规则失效

**问题**: 将路由限流配置为长窗口规则（如 `100/hour`、`{"requests": 100, "window": 3600}`）时，限流形同虚设——实际表现近似 `100/minute`（每小时可放过至约 6000 次请求），完全无法起到预期的小时级防护作用。

**原因**: `_apply_rate_limit` 解析得到每路由的实际 `window`（最高 3600 秒），per-request 检查也确实使用该窗口；但后台清理任务 `_cleanup_expired_rate_limits` 却用固定常量 `DEFAULT_RATE_LIMIT_WINDOW_SECS`（60 秒）作为**所有**路由的统一清理阈值。于是 `100/hour` 路由中早于 60 秒的时间戳被清理任务提前清除，小时窗口内永远累积不到接近 100 条记录，限流被严重削弱。

**根因链路**:
```
_apply_rate_limit 解析 window=3600（100/hour）
  → per-request 检查按 3600s 保留时间戳（正确）
  → 但 _cleanup_expired_rate_limits 用固定 max_window=60s 清理
    → 60s 前的时间戳被全部清除
      → 小时窗口永远只余最近 1 分钟的记录
        → 100/hour 实际退化为 ~100/minute（放宽约 60 倍）
```

**影响版本**: 2.6.0-dev.0 - 2.7.0-dev.4

**修复版本**: 2.7.0-dev.5

**修复内容**: 新增 `_rate_limit_windows: dict[str, int]` 按 store key 记录每路由实际窗口；`_apply_rate_limit` 首次创建条目时写入窗口；`_cleanup_expired_rate_limits` 改为按各 key 自身窗口清理（缺失时回退默认值）；清理删除条目与 `stop()` 时同步维护两个字典。

**修复日期**: 2026/07/31

**回归测试**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**严重性**: 🔴 严重

**类型**: 路由

---

### [BUG-029] 配置监听任务广播半成品 TOML 并静默吞掉异常

**问题**: 用户手动编辑 `config.toml` 保存到一半（产生瞬时的语法错误）时，配置监听后台线程会检测到 mtime 变化、重载配置，但加载失败后仍以空配置 `{}` 发射 `config.updated` 事件，导致适配器/模块的 `on_config_update` 收到空配置、误以为所有配置项被清空而回退默认值。此外监听循环用 `except Exception: pass` 静默吞掉所有异常，watcher 故障无从排查。

**原因**: 两个缺陷叠加：
1. `_load_config` 在 TOML 语法错误/权限错误时把 `self._cache` 擦写为 `{}`，但后台监听线程 `_watch_loop` 与缓存超时路径 `_check_cache_validity` 都在调用 `_load_config()` 后**无条件**执行 `_emit_config_updated()`，把"加载失败产生的空缓存"当作真实变更广播。
2. `_watch_loop` 的 `except Exception: pass` 不记录任何日志。

**根因链路**:
```
用户保存到一半 → TOML 语法错误
  → _load_config() 擦写 _cache = {}
    → _watch_loop 无条件 _emit_config_updated(new_config={})
      → 适配器/模块 on_config_update 收到空配置
        → 误判配置被清空，回退默认值
```

**影响版本**: 2.6.2-dev.1 - 2.7.0-dev.4

**修复版本**: 2.7.0-dev.5

**修复内容**:
1. `_load_config` 改为返回 `bool`；TOML 语法错误/权限/其他错误时**保留上次有效缓存**（不再擦写为 `{}`），仅记录诊断日志并返回 `False`
2. `_watch_loop` 与 `_check_cache_validity` 仅在 `_load_config()` 返回 `True` 时才发射 `config.updated`
3. `_watch_loop` 的 `except Exception` 改为以 warning 级别记录（新增 i18n 键 `core.config.watcher_error`，五语言同步）

**修复日期**: 2026/07/31

**回归测试**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`、`test_permission_denied_logs_clear_message`（更新为验证保留缓存 + 返回 False）

**严重性**: 🟡 中等

**类型**: 配置系统
