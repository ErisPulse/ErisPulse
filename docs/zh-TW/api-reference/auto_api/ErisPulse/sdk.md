# `ErisPulse.sdk` 模块

---

## 模块概述


ErisPulse SDK 主类

提供统一的 SDK 接口，整合所有核心模块和加载器

> **提示**
> example:
> >>> from ErisPulse import sdk
> >>> await sdk.init()
> >>> await sdk.adapter.startup()

---

## 类列表


### `class SDK`

ErisPulse SDK 主类

整合所有核心模块和加载器，提供统一的初始化和管理接口

> **提示**
> SDK 提供以下核心属性：
> - Event: 事件系统
> - lifecycle: 生命周期管理器
> - logger: 日志管理器
> - storage: 存储管理器
> - env: 存储管理器别名
> - config: 配置管理器
> - adapter: 适配器管理器
> - BaseAdapter: 适配器基类
> - SendDSL: DSL 发送接口基类
> - module: 模块管理器
> - router: 路由管理器


#### 嵌套类


##### `class Initializer`

初始化协调器

协调适配器和模块的加载流程，提供统一的初始化接口

> **提示**
> 使用方式：
> >>> initializer = Initializer(sdk_instance)
> >>> success = await initializer.init()


###### 方法列表


####### `__init__(sdk_instance: SDK)`

初始化协调器

:param sdk_instance: SDK 实例

---


####### `async async init()`

初始化所有模块和适配器

执行步骤:
1. 从 PyPI 包加载适配器
2. 从 PyPI 包加载模块
3. 注册适配器
4. 注册模块
5. 初始化模块

:return: bool 初始化是否成功

**异常**: `ImportError` - 当加载失败时抛出

---


##### `class Uninitializer`

反初始化协调器

协调适配器和模块的卸载流程，提供统一的反初始化接口

> **提示**
> 使用方式：
> >>> uninitializer = Uninitializer(sdk_instance)
> >>> success = await uninitializer.uninit()


###### 方法列表


####### `__init__(sdk_instance: SDK)`

反初始化协调器

:param sdk_instance: SDK 实例

---


####### `async async uninit()`

执行反初始化

执行步骤:
1. 关闭所有适配器
2. 卸载所有模块
3. 清理事件处理器
4. 清理管理器
5. 清理 SDK 模块属性

:return: bool 反初始化是否成功

---


#### 方法列表


##### `__init__()`

初始化 SDK 实例

挂载所有核心模块到 SDK 实例

---


##### `__repr__()`

返回 SDK 的字符串表示

:return: str SDK 的字符串表示

---


##### `async async init()`

SDK 初始化入口

:return: bool SDK 初始化是否成功

**示例**:
```python
>>> success = await sdk.init()
>>> if success:
>>>     await sdk.adapter.startup()
```

---


##### `async async _prepare_environment()`

> **内部方法** 
准备运行环境

初始化配置和全局异常处理

:return: bool 环境准备是否成功

---


##### `init_sync()`

SDK 初始化入口（同步版本）

用于命令行直接调用，自动在事件循环中运行异步初始化

:return: bool SDK 初始化是否成功

---


##### `init_task()`

SDK 初始化入口，返回 Task 对象

:return: asyncio.Task 初始化任务

---


##### `async async load_module(module_name: str)`

手动加载指定模块

:param module_name: str 要加载的模块名称
:return: bool 加载是否成功

**示例**:
```python
>>> await sdk.load_module("MyModule")
```

---


##### `async async run(keep_running: bool = True)`

无头模式运行 ErisPulse

:param keep_running: bool 是否保持运行

**示例**:
```python
>>> await sdk.run(keep_running=True)
```

---


##### `async async _do_restart()`

> **内部方法** 
实际执行重启逻辑的内部方法

在后台任务中运行，与调用 restart() 的事件处理器解耦
确保即使调用者被取消，重启流程也能完整执行

:return: bool 重新加载是否成功

---


##### `_collect_top_level_modules()`

> **内部方法** 
从模块和适配器管理器中收集所有已加载包的顶层 Python 模块名

必须在 uninit() 之前调用，因为 uninit 会清除管理器中的注册信息

:return: set[str] 顶层 Python 模块名集合

---


##### `_infer_top_level(info: dict)`

> **内部方法** 
从模块/适配器信息中推导顶层 Python 模块名

优先使用 top_level.txt，fallback 从 entry-point value 推导

:param info: 模块或适配器信息字典
:return: 顶层 Python 模块名列表

---


##### `_invalidate_module_cache(top_level_modules: set[str])`

> **内部方法** 
清理 sys.modules 中属于已加载包的缓存，并刷新 importlib.metadata 缓存

:param top_level_modules: 需要清理的顶层 Python 模块名集合

---


##### `async async restart()`

SDK 重新启动

执行完整的反初始化后再初始化过程，并重新启动适配器。

> **提示**
> **重要设计说明**：
> 此方法使用 `asyncio.ensure_future()` 将重启任务注册到事件循环调度器，
> 与调用栈完全解耦。这是有意为之的设计，原因如下：
> 1. **事件链路保护**：如果模块在事件处理器内部调用 `restart()`，而重启过程
> 是同步等待的，那么重启会中断当前事件链路，导致事件处理不完整。
> 2. **后台执行**：重启是一个耗时操作（需要关闭适配器、卸载模块、重新加载），
> 使用 `ensure_future` 可以让它在后台执行，不阻塞调用者。
> 3. **返回值语义**：方法立即返回 `True` 表示"重启任务已成功调度"，
> 而不是"重启已完成"。实际的重启过程在后台进行。
> **使用场景示例**：
> >>> # 场景1: 在模块的事件处理器中调用重启
> >>> @Event.on("message")
> >>> async def handle_reload_command(event):
> >>>     if event["message"] == "/reload":
> >>>         # 使用 ensure_future 确保事件链路不被中断
> >>>         await sdk.restart()  # ✅ 正确
> >>>         # 不要使用 await sdk.restart()，这会导致事件链路中断
> >>>
> >>> # 场景2: 等待重启完成
> >>> # 如果需要等待重启完成，可以使用生命周期事件监听
> >>> @lifecycle.on("core.init.complete")
> >>> async def on_restart_complete(event):
> >>>     if event["data"]["success"]:
> >>>         logger.info("重启成功！")
> >>>
> >>> # 场景3: 命令触发重启
> >>> @command("restart")
> >>> async def restart_command():
> >>>     logger.info("正在重启 SDK...")
> >>>     await sdk.restart()
> >>>     logger.info("重启任务已调度，将在后台执行")

:return: bool 重启任务是否成功调度（并非重启是否完成）

**示例**:
```python
>>> await sdk.restart()
```

---


##### `async async uninit()`

SDK 反初始化

执行以下操作：
1. 关闭所有适配器
2. 卸载所有模块
3. 清理所有事件处理器
4. 清理适配器管理器和模块管理器
5. 清理 SDK 对象上的模块属性

:return: bool 反初始化是否成功

**示例**:
```python
>>> await sdk.uninit()
```

---

