# `ErisPulse.Core.Bases.module` 模块

> 最后更新：2026-02-03 22:38:11

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


##### `get_load_strategy()`

获取模块加载策略

支持返回 ModuleLoadStrategy 对象或字典
所有属性统一处理，没有任何预定义字段

:return: 加载策略对象或字典

> **提示**
> 常用配置项：
> - lazy_load: bool, 是否懒加载（默认 True）
> - priority: int, 加载优先级（默认 0，数值越大优先级越高）
> 使用方式：
> >>> class MyModule(BaseModule):
> ...     @staticmethod
> ...     def get_load_strategy() -> ModuleLoadStrategy:
> ...         return ModuleLoadStrategy(
> ...             lazy_load=False,
> ...             priority=100
> ...         )
> 或使用字典：
> >>> class MyModule(BaseModule):
> ...     @staticmethod
> ...     def get_load_strategy() -> dict:
> ...         return {
> ...             "lazy_load": False,
> ...             "priority": 100
> ...         }

---


##### `should_eager_load()`

模块是否应该在启动时加载
默认为False(即懒加载)

兼容方法，实际调用 get_load_strategy()

:return: 是否应该在启动时加载

> **提示**
> 旧版方法，建议使用 get_load_strategy() 替代

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

