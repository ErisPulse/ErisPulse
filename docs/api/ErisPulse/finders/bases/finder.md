# `ErisPulse.finders.bases.finder` 模块

> 最后更新：2026-02-04 08:04:59

---

## 模块概述


ErisPulse 基础发现器

定义发现器的抽象基类，提供通用的发现器接口和结构

> **提示**
> 1. 所有具体发现器应继承自 BaseFinder
> 2. 子类需实现 _get_entry_point_group 方法
> 3. 支持缓存机制，避免重复查询

---

## 类列表


### `class BaseFinder(ABC)`

基础发现器抽象类

提供通用的发现器接口和缓存功能

> **提示**
> 子类需要实现：
> - _get_entry_point_group: 返回 entry-point 组名

> **内部方法** 
此类仅供内部使用，不应直接实例化


#### 方法列表


##### `__init__()`

初始化基础发现器

---


##### `_get_entry_point_group()`

获取 entry-point 组名

:return: entry-point 组名

> **内部方法** 
子类必须实现此方法

---


##### `_get_entry_points()`

获取所有 entry-points

:return: entry-point 对象列表

> **内部方法** 
内部方法，使用缓存机制获取 entry-points

---


##### `find_all()`

查找所有 entry-points

:return: entry-point 对象列表

---


##### `find_by_name(name: str)`

按名称查找 entry-point

:param name: entry-point 名称
:return: entry-point 对象，未找到返回 None

---


##### `get_entry_point_map()`

获取 entry-point 映射字典

:return: {name: entry_point} 字典

---


##### `get_group_name()`

获取 entry-point 组名

:return: entry-point 组名

---


##### `clear_cache()`

清除缓存

> **提示**
> 当安装/卸载包后调用此方法清除缓存

---


##### `set_cache_expiry(expiry: int)`

设置缓存过期时间

:param expiry: 过期时间（秒）

> **内部方法** 
内部方法，用于调整缓存策略

---


##### `__iter__()`

迭代器接口

:return: entry-point 迭代器

---


##### `__len__()`

返回 entry-point 数量

:return: entry-point 数量

---


##### `__contains__(name: str)`

检查 entry-point 是否存在

:param name: entry-point 名称
:return: 是否存在

---


##### `__repr__()`

返回发现器的字符串表示

:return: 字符串表示

---

