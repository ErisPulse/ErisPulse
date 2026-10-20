# `ErisPulse.sdk` 模块

---

## 模块概述


ErisPulse SDK 主类

提供统一的 SDK 接口，整合所有核心模块和加载器

> **提示**
> example:
> ```python
> from ErisPulse import sdk
> await sdk.init()
> await sdk.adapter.startup()
> ```
>

---

## 函数列表


### `_resolve_core(attr: str)`

**内部方法**
动态解析核心模块单例引用

每次访问时通过 import 系统获取最新单例，确保软重启后 SDK 始终
指向当前有效的模块级单例对象。

- **attr**: 核心属性名

**返回值**: 对应的单例对象

**异常**: `AttributeError` - 当属性名不在核心映射中时

---


## 类列表


### `class SDK`

ErisPulse SDK 主类

整合所有核心模块和加载器，提供统一的初始化和管理接口

设计说明:
核心模块属性（adapter, module, router, logger, lifecycle 等）
通过动态解析获取，不缓存在实例上。这确保软重启后 SDK 始终
指向最新的模块级单例，无需手动刷新引用。

> **提示**
> SDK 提供以下核心属性：
> - Event: 事件系统
> - lifecycle: 生命周期管理器
> - logger: 日志管理器
> - storage: 存储管理器
> - env: 存储管理器别名
> - config: 配置管理器
> - i18n: 国际化管理器
> - adapter: 适配器管理器
> - BaseAdapter: 适配器基类
> - SendDSL: DSL 发送接口基类
> - module: 模块管理器
> - router: 路由管理器
> - client: HTTP 客户端
> - master: 框架主人管理器
> - scope: 作用域管理器（模块 / 身份 / 出站 三维，"什么范围内生效"）
> - transcript: 会话收件箱（每会话近期消息流的记录与查询）
> - interaction: 交互会话管理器（wait_reply 等待表 / 会话租约 / 按归属取消）
> - Event: 事件模块包（command 命令处理器 / message / notice / request 等事件处理器）
> - context: 模块上下文管理（owner_scope / get_current_owner / trace-id / 消息事务账本）


#### 方法列表


##### `__init__()`

初始化 SDK 实例

不缓存任何核心模块引用。核心属性通过 __getattr__ 动态解析，
确保软重启后始终指向最新的模块级单例。

---


##### `version -> str`（property）

获取当前 ErisPulse 安装版本

每次访问实时查询 importlib.metadata，确保框架热更新后
能读到最新版本（如果框架本身被upgrade）。

**返回值** (`str`): 版本号字符串，未安装时返回 "UnknownVersion"

**示例**:

```python
print(sdk.version)
'2.6.2'
```

---


##### `__dir__() -> list[str]`

列出实例属性（含核心模块动态属性）

让 ``dir(sdk)`` 与交互式补全反映 ``__getattr__`` 提供的核心模块单例
（scope / command / master / adapter 等）。用类级 dir() 避免
触发 ``__getattr__`` 的递归解析。

**返回值**: 属性名列表（去重排序）

---


##### `__getattr__(name: str)`

动态解析核心模块属性

当属性不在实例 __dict__ 中时调用。对核心属性名使用动态 import 解析，
确保软重启后始终获取最新单例。对未知属性提供友好的错误提示。

- **name**: 属性名

**返回值**: 属性值

**异常**: `AttributeError` - 当属性不存在时

---


##### `__repr__() -> str`

返回 SDK 的字符串表示

展示版本、初始化状态、适配器/模块计数，便于调试时一眼查看运行状态。
适配器/模块计数失败时静默降级为只显示版本与初始化状态。

**返回值**: str SDK 的字符串表示

---


##### `_start_proactive_gc() -> None`

**内部方法**
启动主动 GC 后台任务（实现见 ``runtime/proactive_gc.start_proactive_gc``）

---


##### `_stop_proactive_gc() -> None`

**内部方法**
停止主动 GC 后台任务并反注册配置钩子（实现见 ``runtime/proactive_gc.stop_proactive_gc``）

---


##### `_read_gc_config() -> tuple[float, int, int, int, bool, int]`（staticmethod）

**内部方法**
读取并钳制主动 GC 框架配置（实现见 ``runtime/proactive_gc.read_gc_config``）

---


##### `_on_gc_config_event(_data: dict) -> None`

**内部方法**
proactive_gc_* 配置变更时重启 GC 任务（实现见 ``runtime/proactive_gc.on_gc_config_event``）

---


##### `_has_handler_backlog() -> bool`（staticmethod）

**内部方法**
事件处理器洪峰检测（实现见 ``runtime/proactive_gc.has_handler_backlog``）

---


##### `_run_full_gc_collection(gc_module: Any, baseline: float | None, growth_mb: int) -> tuple[int, float | None]`（staticmethod）

**内部方法**
执行一次全量回收（实现见 ``runtime/proactive_gc.run_full_gc_collection``）

---


##### `dump_state() -> dict`

导出框架当前运行状态的快照

**返回值** (`dict`): 包含所有子系统状态的字典

---


##### `async init(*, before_init: Callable[[], Any] | None = None, after_init: Callable[[], Any] | None = None) -> bool`

SDK 初始化入口

重复调用保护：若 SDK 已经初始化成功，重复调用不会重新初始化，
会记录一条警告并直接返回 True。如需强制重新初始化，请先
调用 ``sdk.uninit()`` 或使用 ``sdk.restart()``。

- **before_init**: 初始化前回调（同步或异步），在环境准备之前执行
- **after_init**: 初始化成功后回调（同步或异步），在初始化完成后执行

**返回值**: bool SDK 初始化是否成功（已初始化时返回 True）

**示例**:

```python
success = await sdk.init()
if success:
    await sdk.adapter.startup()

# 使用回调
async def setup():
    print("初始化前")
async def ready():
    print("初始化完成")
await sdk.init(before_init=setup, after_init=ready)
```

---


##### `async _prepare_environment() -> bool`

**内部方法**
准备运行环境

初始化配置和全局异常处理

**返回值** (`bool`): 环境准备是否成功

---


##### `init_sync(*, before_init: Callable[[], Any] | None = None, after_init: Callable[[], Any] | None = None) -> bool`

SDK 初始化入口（同步版本）

用于命令行直接调用，自动在事件循环中运行异步初始化

- **before_init**: 初始化前回调（同步或异步）
- **after_init**: 初始化成功后回调（同步或异步）

**返回值**: bool SDK 初始化是否成功

---


##### `init_task(*, before_init: Callable[[], Any] | None = None, after_init: Callable[[], Any] | None = None) -> asyncio.Task | concurrent.futures.Future`

SDK 初始化入口，返回 Task 对象

- **before_init**: 初始化前回调（同步或异步）
- **after_init**: 初始化成功后回调（同步或异步）

**返回值** (`asyncio.Task`): 初始化任务（在事件循环内调用时）；并发 Future

    （无运行循环但主循环已注册时，经线程安全方式调度回主循环）
**异常**: `RuntimeError` - 当前无运行中的事件循环且主循环未注册——

    此前本场景会新建一个永不运行的循环并返回永不完成的悬挂 Task

---


##### `async load_module(module_name: str) -> bool`

手动加载指定模块

- **module_name** (`str`): 要加载的模块名称

**返回值** (`bool`): 加载是否成功

**示例**:

```python
await sdk.load_module("MyModule")
```

---


##### `async run(keep_running: bool = True, *, before_init: Callable[[], Any] | None = None, after_init: Callable[[], Any] | None = None, on_ready: Callable[[], Any] | None = None) -> None`

无头模式运行 ErisPulse

内部调用 ``init()`` 完成初始化，然后在 ``on_ready`` 回调执行完毕后
挂起主程序（当 ``keep_running=True`` 时）。

硬重启（``hard_restart()``）通过退出码 42 契约交由**外部
监督者**（``epsdk run`` / systemd / Docker / PM2 等，见 startup.md
「监督者指南」）重新拉起。

> **提示**
> 异常处理原则：
> 1. 模块/适配器的任何错误都会被拦截，不会导致进程退出
> 2. 只有 KeyboardInterrupt（Ctrl+C）会正常向上传播，触发优雅关闭
> 3. 其他 BaseException（如 SystemExit）会被拦截并记录，防止意外终止
> 回调执行顺序:
> ```
> before_init → 初始化 → after_init → on_ready → [挂起]
> ```
>
> 回调可以是同步或异步函数，框架自动检测并 await。
> 回调中的异常会被捕获并记录日志，不会中断启动流程。

- **keep_running** (`bool`): 是否保持运行
- **before_init**: 初始化前回调，转发给 ``init()``
- **after_init**: 初始化成功后回调，转发给 ``init()``
- **on_ready**: 初始化完成且 ``after_init`` 执行后、挂起前的回调

**示例**:

```python
await sdk.run(keep_running=True)

# 使用 on_ready 回调
async def on_startup():
    print("SDK 就绪，开始业务逻辑")
await sdk.run(on_ready=on_startup)

# 分阶段回调
async def before():
    print("即将初始化")
async def after():
    print("初始化完成，适配器已就绪")
async def ready():
    print("一切就绪，开始挂起")
await sdk.run(before_init=before, after_init=after, on_ready=ready)
```

---


##### `shutdown() -> None`

请求优雅关闭

设置关闭事件，使正在 ``await sdk.run()`` 挂起的主循环返回，
进而触发 ``uninit()`` 完成资源清理。可由模块/适配器在运行时调用，
也用作 SIGTERM 等信号的处理入口。

**示例**:

```python
sdk.shutdown()  # 任意协程中调用，触发优雅退出
```

---


##### `enable_plugin_hot_reload(interval: float = 1.0) -> bool`

启用本地插件文件夹热重载（自动监控）

监控插件文件夹（默认 ``plugins/``，可通过 ``ErisPulse.framework.plugins_dir``
配置）下 ``.py`` 文件的变更，自动重新加载对应插件。
需在 ``await sdk.run()`` 之前调用。

> **提示**
> 自动监控仅覆盖本地插件目录；PyPI 安装包模块可通过
> :meth:`reload_module` 手动热重载（pip 升级后调用即可）。

- **interval**: 轮询间隔（秒，默认 1.0）

**返回值**: 是否启动成功（无插件目录或已在运行返回 False）

**示例**:

```python
await sdk.init()
sdk.enable_plugin_hot_reload()
await sdk.run()
```

---


##### `async reload_module(module_name: str, *, full: bool = True) -> bool`

热重载单个模块（手动触发，支持任意来源）

完整执行 语法预检 → 卸载旧实例 → 清理注册与 ``sys.modules`` 缓存
（按顶层包名 + ``invalidate_caches``，默认全量）→ 重新发现/导入 →
重新注册并加载 流程；依赖该模块的模块会**级联重载**并默认重导代码。
本地插件（``plugins/`` 目录）来源重扫描插件目录；运行时注册来源按
定义模块重导并按类名重取；PyPI 安装包来源重新查询 entry-point 并
重导入模块代码（pip 升级后调用即可生效）。

- **module_name**: 模块名（entry-point 名称、插件名或运行时注册名）
- **full**: 是否全量重载（默认 True；False 为轻量逃生门——仅按

    元数据清理缓存、PyPI 依赖者直接重新实例化，仅供超大依赖树的
    性能敏感场景）
**返回值**: 是否重载成功

**示例**:

```python
await sdk.reload_module("dice")      # 本地插件
await sdk.reload_module("MyRuntime") # 运行时注册模块
await sdk.reload_module("Weather")   # PyPI 安装包模块（默认全量）
```

---


##### `async reload_adapter(adapter_name: str, *, full: bool = True) -> bool`

热重载单个适配器（代码级，手动触发）

完整执行 语法预检 → 卸载（shutdown 即清理：路由/事件/任务/bot offline
+ 注销）→ 清理 ``sys.modules`` 子树与 ``__pycache__`` 字节码 → 重新
发现/导入 → 重新注册 → 原运行态则重新拉起 流程；任一步失败自动回滚
旧注册状态（尽力而为语义：断连等 unload 副作用不可撤销）。支持本地
插件（``plugins/`` 目录）与 PyPI 安装包两种来源。

- **adapter_name**: 适配器名（平台名称）
- **full**: 保留参数位（当前两种来源均执行全量清理，与模块语义对齐）

**返回值**: 是否重载成功（适配器被移除视为成功）

**示例**:

```python
await sdk.reload_adapter("aiocqhttp")  # pip 升级后调用即可生效
```

---


##### `async reload_all_modules() -> dict[str, bool]`

全量热重载所有已注册模块（尽力而为语义）

执行 卸载全部 → 清理全部 ``sys.modules`` 子树 → 重新发现/注册 →
按依赖拓扑序加载 → 此前已加载的懒加载模块重新激活 流程，一次刷新
全部模块代码（pip 批量升级后调用即可全部生效）。单模块失败仅记录
诊断并跳过，不影响其余模块；无整体回滚（on_unload 副作用不可撤销，
与单模块热重载语义一致）。

**返回值**: 模块注册名 → 是否重载成功（发现阶段即失败的模块不在结果中；

         SDK 未初始化时返回空字典）

**示例**:

```python
await sdk.reload_all_modules()
```

---


##### `async _reload_module(module_name: str) -> None`

**内部方法**
热重载回调（由 PluginReloadWatcher 调度），失败仅记录不抛异常

---


##### `stop_plugin_hot_reload() -> None`

停止本地插件热重载监控

---


##### `_register_signal_handlers() -> None`

**内部方法**
注册进程信号处理器，将 SIGTERM / SIGHUP 等信号转为优雅关闭

Windows 不支持 ``loop.add_signal_handler``，捕获异常后跳过
（Windows 下仍可通过 ``sdk.shutdown()`` 或 Ctrl+C 触发关闭）。

---


##### `async _do_restart() -> bool`

**内部方法**
实际执行软重启的内部方法（联动热重载系统）

在后台任务中运行，与调用 restart() 的事件处理器解耦，
确保即使调用者被取消，重启流程也能完整执行。

软重启 = **组件层代码级热重载**（2.11 起不再整体 uninit/init）：
1. 全部已加载模块走统一热重载管线（``reload_all_modules``：
   语法预检 → 卸载 → 清 sys.modules / __pycache__ → 重发现重导 →
   重新注册加载 → 懒激活；失败快照回滚，单模块失败不影响其余）
2. 全部适配器逐个走 ``reload_adapter``（卸载清理 → 清缓存重发现 →
   重新注册 → 原运行态重新拉起）

配置热更新由配置监听器处理；框架自身更新 / entry-point 增删等
整进程场景请使用 ``hard_restart()``。

**返回值** (`bool`): 软重启是否全部成功（任一组件失败即为 False，

         失败清单见日志）

---


##### `async restart() -> bool`

SDK 软重启（联动热重载系统）

全部已加载模块与适配器走统一**代码级热重载管线**（语法预检 → 卸载 →
清 ``sys.modules`` / ``__pycache__`` → 重发现重导 → 重新注册加载 /
拉起；失败快照回滚，单组件失败不影响其余），不再整体 ``uninit()`` /
``init()``——框架进程、路由与配置监听保持在线，组件代码（pip 升级后）
即刻生效。

> **提示**
> **重要设计说明**：
> 此方法使用后台任务将重启流程注册到事件循环调度器，与调用栈完全解耦
> （事件处理器内调用不会中断当前事件链路）；立即返回 ``True`` 表示
> "重启任务已成功调度"而非"重启已完成"。
> **语义分界**（2.11 起）：
> - ``restart()``：组件层代码热重载（模块 + 适配器；pip 升级组件后生效）
> - ``hard_restart()``：整进程重启（框架自身更新 / entry-point 增删 /
> 结构性配置变更等场景）

**返回值** (`bool`): 重启任务是否成功调度（并非重启是否完成）

**示例**:

```python
await sdk.restart()
```

---


##### `is_supervised() -> bool`

检测当前进程是否由外部监督者启动（CLI run 命令 / systemd / Docker 等）

监督者会在进程退出码为 42（``HARD_RESTART_EXIT_CODE``）时重新拉起新进程。
未被监督时硬重启后进程不会自动恢复，``hard_restart()`` 会打出警告提醒
配置外部监督者（见 startup.md「监督者指南」）。

**返回值**: 是否有外部监督者

---


##### `async hard_restart() -> bool`

硬重启：反初始化后退出进程，由外部监督者重新启动新实例

与 restart()（热重启）的区别：
- restart(): 在同一进程内反初始化再重新初始化
- hard_restart(): 反初始化后以退出码 42 退出进程，由外部监督者重新拉起全新进程

确保资源完全释放

硬重启依赖外部监督者（``epsdk run`` / systemd / Docker / PM2 / supervisord）
在退出码 42 时重新拉起进程；未被监督时进程退出后不会自动恢复，会打警告提醒。

**返回值** (`bool`): 硬重启任务是否成功调度

**示例**:

```python
await sdk.hard_restart()
```

---


##### `get_topology(*, json_safe: bool = True) -> dict[str, Any]`

获取完整的拓扑树数据（便于 Dashboard 等管理界面展示）

聚合模块、适配器与作用域的归属关系：
- ``modules``：每个模块拥有的命令 / 事件处理器 / 路由 / 生命周期钩子
- ``adapters``：每个适配器的运行状态、下属 Bot 状态与作用域绑定
- ``scope``：作用域（模块 / 身份 / 文本 / 出站动作）

- **json_safe**: 是否输出可直接 JSON 序列化的安全结构（默认 True）。

                  安全模式下模块 ``info`` 只保留纯数据 meta 子表，
                  并对整树做序列化兜底净化，返回值可直接 ``json.dumps``。

**返回值**: 拓扑树字典

    {"modules": {...}, "adapters": {...}, "scope": {...}}

**示例**:

```python
topology = sdk.get_topology()
topology["modules"]["Chat"]["commands"]
["chat"]
```

---


##### `async uninit() -> bool`

SDK 反初始化

执行以下操作：
1. 关闭所有适配器
2. 卸载所有模块
3. 清理所有事件处理器
4. 清理适配器管理器和模块管理器
5. 清理 SDK 对象上的模块属性

**返回值** (`bool`): 反初始化是否成功

**示例**:

```python
await sdk.uninit()
```

---

