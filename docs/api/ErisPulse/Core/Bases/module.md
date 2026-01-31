# `ErisPulse.Core.Bases.module` 模块

> 最后更新：2026-02-01 03:21:24

---

## 模块概述


ErisPulse 模块基础模块

提供模块基类定义和标准接口

---

## 类列表


### `class BaseModule`

模块基类

提供模块加载和卸载的标准接口


#### 方法列表


##### `should_eager_load()`

模块是否应该在启动时加载
默认为False(即懒加载)

:return: 是否应该在启动时加载

---


##### `async async on_load(event: dict)`

当模块被加载时调用

:param event: 事件内容
:return: 处理结果

> **提示**
> 其中，event事件内容为:
> `{ "module_name": "模块名" }`

---


##### `async async on_unload(event: dict)`

当模块被卸载时调用

:param event: 事件内容
:return: 处理结果

> **提示**
> 其中，event事件内容为:
> `{ "module_name": "模块名" }`

---

