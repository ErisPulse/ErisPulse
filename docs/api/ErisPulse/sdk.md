# `ErisPulse.sdk` 模块

> 最后更新：2026-01-31 19:10:04

---

## 模块概述


ErisPulse SDK 主类

提供统一的 SDK 接口，整合所有核心模块和加载器

> **提示**
> 使用方式：
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
> - exceptions: 异常处理模块
> - storage: 存储管理器
> - env: 存储管理器别名
> - config: 配置管理器
> - adapter: 适配器管理器
> - AdapterFather: 适配器基类别名
> - BaseAdapter: 适配器基类
> - SendDSL: DSL 发送接口基类
> - module: 模块管理器
> - router: 路由管理器
> - adapter_server: 路由管理器别名


#### 方法列表


##### `__init__()`

初始化 SDK 实例

挂载所有核心模块到 SDK 实例

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

初始化项目环境文件和配置

:return: bool 环境准备是否成功

---


##### `async async _init_progress()`

> **内部方法** 
初始化项目环境文件

:return: bool 是否创建了新的 main.py 文件

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


##### `async async restart()`

SDK 重新启动

执行完整的反初始化后再初始化过程

:return: bool 重新加载是否成功

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
4. 清理僵尸线程

:return: bool 反初始化是否成功

**示例**:
```python
>>> await sdk.uninit()
```

---


##### `__repr__()`

返回 SDK 的字符串表示

:return: str SDK 的字符串表示

---

