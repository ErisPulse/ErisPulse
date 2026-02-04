# `ErisPulse.__init__` 模块

> 最后更新：2026-02-04 14:28:57

---

## 模块概述


ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

> **提示**
> 1. 使用前请确保已正确安装所有依赖
> 2. 调用await sdk.init()进行初始化
> 3. 模块加载采用懒加载机制

---

## 函数列表


### `async async init()`

SDK 初始化入口

:return: bool SDK 初始化是否成功

**示例**:
```python
>>> success = await sdk.init()
>>> if success:
>>>     await sdk.adapter.startup()
```

---


### `async async _prepare_environment()`

> **内部方法** 
准备运行环境

初始化项目环境文件和配置

:return: bool 环境准备是否成功

---


### `async async _init_progress()`

> **内部方法** 
初始化项目环境文件

:return: bool 是否创建了新的 main.py 文件

---


### `init_sync()`

SDK 初始化入口（同步版本）

用于命令行直接调用，自动在事件循环中运行异步初始化

:return: bool SDK 初始化是否成功

---


### `init_task()`

SDK 初始化入口，返回 Task 对象

:return: asyncio.Task 初始化任务

---


### `async async load_module(module_name: str)`

手动加载指定模块

:param module_name: str 要加载的模块名称
:return: bool 加载是否成功

**示例**:
```python
>>> await sdk.load_module("MyModule")
```

---


### `async async run(keep_running: bool = True)`

无头模式运行 ErisPulse

:param keep_running: bool 是否保持运行

**示例**:
```python
>>> await sdk.run(keep_running=True)
```

---


### `async async _restart_task()`

> **内部方法** 
实际执行重启逻辑的独立任务

此函数在后台任务中运行，与调用 restart() 的事件处理器解耦
确保即使调用者被取消，重启流程也能完整执行

:return: bool 重新加载是否成功

---


### `async async restart()`

SDK 重新启动

执行完整的反初始化后再初始化过程

注意：此函数使用后台任务执行重启流程，确保即使当前事件处理器被取消，
重启流程仍能完整执行。因此调用此函数后，重启会在后台异步进行。

:return: bool 重新加载是否成功（后台任务完成时返回）

**示例**:
```python
>>> await sdk.restart()
```

---


### `async async uninit()`

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

