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

## 函数列表


### `_resolve_core(attr: str)`

> **内部方法** 
动态解析核心模块单例引用

每次访问时通过 import 系统获取最新单例，确保软重启后 SDK 始终
指向当前有效的模块级单例对象。

:param attr: 核心属性名
:return: 对应的单例对象
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


####### `__getattr__(name: str)`

将未找到的属性委托给 SDK 实例（如 logger、adapter 等）

---


####### `async async init()`

初始化所有模块和适配器

执行步骤:
1. 并行发现适配器和模块
2. 注册适配器
3. 启动适配器
4. 注册模块
5. 初始化模块
6. 启动路由服务器

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


####### `__getattr__(name: str)`

将未找到的属性委托给 SDK 实例（如 logger、adapter 等）

---


####### `async async uninit()`

执行反初始化

执行步骤:
1. 关闭所有适配器实例
2. 卸载所有模块
3. 停止路由服务器
4. 清理所有事件处理器
5. 清理适配器管理器和模块管理器
6. 清理 LazyModule 引用
7. 清理单例残留状态
8. 清理 SDK 模块属性
9. 重置初始化状态

:return: bool 反初始化是否成功

---


#### 方法列表


##### `__init__()`

初始化 SDK 实例

不缓存任何核心模块引用。核心属性通过 __getattr__ 动态解析，
确保软重启后始终指向最新的模块级单例。

---


##### `__getattr__(name: str)`

动态解析核心模块属性

当属性不在实例 __dict__ 中时调用。对核心属性名使用动态 import 解析，
确保软重启后始终获取最新单例。对未知属性提供友好的错误提示。

:param name: 属性名
:return: 属性值
**异常**: `AttributeError` - 当属性不存在时

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

> **提示**
> 异常处理原则：
> 1. 模块/适配器的任何错误都会被拦截，不会导致进程退出
> 2. 只有 KeyboardInterrupt（Ctrl+C）会正常向上传播，触发优雅关闭
> 3. 其他 BaseException（如 SystemExit）会被拦截并记录，防止意外终止

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

重启流程:
1. 收集已加载包的顶层模块名（必须在 uninit 之前）
2. 反初始化（关闭适配器、卸载模块、清理状态）
3. 清除外部包的 sys.modules 缓存
4. 清除 ErisPulse 框架子模块缓存（支持框架自身热更新）
5. 清除 importlib.metadata 缓存（确保 entry_points 返回最新数据）
6. 重新初始化
7. 重新启动适配器

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
清理 sys.modules 中属于已加载包的缓存，并刷新 importlib 缓存

:param top_level_modules: 需要清理的顶层 Python 模块名集合

---


##### `_invalidate_framework_cache()`

> **内部方法** 
清理 ErisPulse 框架自身的子模块缓存，以支持框架热更新

清除所有 ErisPulse.* 子模块的 sys.modules 缓存，但保留 ErisPulse 包本身。
这样可以避免重新运行 __init__.py（防止创建新的 SDK 实例），
同时确保后续的 import 语句从磁盘加载最新的框架代码。

设计说明:
- 保留 ErisPulse 包本身（不删除 sys.modules['ErisPulse']），
  防止 __init__.py 重新执行导致创建新的 SDK 单例
- 清除所有 ErisPulse.* 子模块，使后续 import 从磁盘重新加载
- 当前正在执行的代码（self 及其方法）不受影响，
  因为 Python 函数/方法持有对代码对象的直接引用
- 新的 import 语句将加载更新后的框架代码

---


##### `_invalidate_metadata_cache()`

> **内部方法** 
清理 importlib.metadata 相关缓存，确保 entry_points() 返回最新数据

当 pip install --upgrade 更新包后，importlib.metadata 的内部缓存
可能仍然引用旧的分发元数据。清除这些缓存可以强制重新扫描
.dist-info 目录，获取最新的 entry_points 数据。

这对于以下场景至关重要:
- Dashboard 热更新模块/适配器后，需要发现新安装的版本
- 框架自身更新后，需要获取最新的 entry_points 配置

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

:return: bool 重启任务是否成功调度（并非重启是否完成）

**示例**:
```python
>>> await sdk.restart()
```

---


##### `async async hard_restart()`

硬重启：反初始化后退出进程，由父进程（run.py）重新启动新实例

与 restart()（热重启）的区别：
- restart(): 在同一进程内反初始化再重新初始化
- hard_restart(): 反初始化后退出进程，由父进程重新启动全新进程

确保资源完全释放

需要通过 epsdk run 启动才生效，否则进程退出后不会自动重启。

:return: bool 硬重启任务是否成功调度

**示例**:
```python
>>> await sdk.hard_restart()
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

