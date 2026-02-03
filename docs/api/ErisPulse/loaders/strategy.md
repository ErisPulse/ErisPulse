# `ErisPulse.loaders.strategy` 模块

> 最后更新：2026-02-03 22:38:11

---

## 模块概述


ErisPulse 模块加载策略

提供统一的模块加载策略配置类

> **提示**
> 1. 所有属性统一处理，没有预定义字段
> 2. 支持通过构造函数传入任意参数
> 3. 支持字典方式创建

---

## 类列表


### `class ModuleLoadStrategy`

模块加载策略配置

所有属性统一处理，通过魔术方法实现动态访问
没有预定义属性，完全由用户传入的内容决定

> **提示**
> 使用方式：
> >>> strategy = ModuleLoadStrategy(
> ...     lazy_load=False,
> ...     priority=100,
> ...     custom_option=123
> ... )
> eager_load 也是一个合法的属性，但不建议使用，其的han'y
> >>> strategy.lazy_load
> False
> >>> strategy.priority
> 100
> >>> strategy.custom_option
> 123
> 从字典创建：
> >>> config = {"lazy_load": False, "priority": 100}
> >>> strategy = ModuleLoadStrategy.from_dict(config)


#### 方法列表


##### `__init__()`

初始化策略，所有参数统一存储

:param kwargs: 策略配置项，任意键值对

> **提示**
> 常用配置项：
> - lazy_load: bool, 是否懒加载（默认 True）
> - priority: int, 加载优先级（默认 0，数值越大优先级越高）

---


##### `__getattr__(name: str)`

获取属性值

:param name: 属性名
:return: 属性值，如果不存在则返回 None

> **内部方法** 
内部方法，用于动态属性访问

---


##### `__setattr__(name: str, value: Any)`

设置属性值

:param name: 属性名
:param value: 属性值

> **内部方法** 
内部方法，用于动态属性设置

---


##### `__contains__(name: str)`

检查属性是否存在

:param name: 属性名
:return: 是否存在该属性

---


##### `__repr__()`

返回策略的字符串表示

:return: 字符串表示

---


##### `from_dict(config: Dict[str, Any])`

从字典创建策略实例

:param config: 配置字典
:return: 策略实例

> **提示**
> 示例：
> >>> config = {"lazy_load": False, "priority": 100}
> >>> strategy = ModuleLoadStrategy.from_dict(config)

---

