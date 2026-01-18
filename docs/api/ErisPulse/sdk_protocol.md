# `ErisPulse.sdk_protocol` 模块

> 最后更新：2026-01-18 17:17:15

---

## 模块概述


ErisPulse SDK Protocol 定义

提供 SDK 的类型接口定义，用于 IDE 类型提示和静态类型检查

---

## 函数列表


### `check_sdk_compatible(obj: Any)`

检查对象是否符合 SDK Protocol

:param obj: 要检查的对象
:return: bool 是否符合协议

---


## 类列表


### `class SDKProtocol(Protocol)`

SDK 对象的 Protocol 接口定义

定义了 SDK 对象应该具有的所有属性和方法，用于类型检查


#### 方法列表


##### `async async init()`

SDK初始化入口

:return: bool SDK初始化是否成功

---


##### `init_task()`

SDK初始化入口，返回Task对象

:return: asyncio.Task 初始化任务

---


##### `async async load_module(module_name: str)`

手动加载指定模块

:param module_name: str 要加载的模块名称
:return: bool 加载是否成功

---


##### `async async run(keep_running: bool = True)`

无头模式运行ErisPulse

:param keep_running: bool 是否保持运行

---


##### `async async restart()`

SDK重新启动

:return: bool 重新加载是否成功

---


##### `async async uninit()`

SDK反初始化

:return: bool 反初始化是否成功

---

