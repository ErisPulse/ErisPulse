# `ErisPulse.loaders.manager_base` 模块

> 最后更新：2026-01-31 19:10:05

---

## 模块概述


ErisPulse 管理器基类

提供适配器和模块管理器的统一接口定义

> **提示**
> 适配器管理器和模块管理器都应继承此基类以保持接口一致性

---

## 类列表


### `class ManagerBase(ABC)`

管理器基类

定义适配器和模块管理器的统一接口

> **提示**
> 统一方法：
> - register(): 注册类
> - unregister(): 取消注册
> - get(): 获取实例
> - exists(): 检查是否存在
> - enable()/disable(): 启用/禁用
> - is_enabled(): 检查是否启用
> - list_*(): 列出相关项


#### 方法列表


##### `register(name: str, class_type: Type, info: Optional[Dict] = None)`

注册类

:param name: 名称
:param class_type: 类类型
:param info: 额外信息
:return: 是否注册成功

---


##### `unregister(name: str)`

取消注册

:param name: 名称
:return: 是否取消成功

---


##### `get(name: str)`

获取实例

:param name: 名称
:return: 实例或 None

---


##### `exists(name: str)`

检查是否存在（在配置中注册）

:param name: 名称
:return: 是否存在

---


##### `is_enabled(name: str)`

检查是否启用

:param name: 名称
:return: 是否启用

---


##### `enable(name: str)`

启用

:param name: 名称
:return: 是否成功

---


##### `disable(name: str)`

禁用

:param name: 名称
:return: 是否成功

---


##### `list_registered()`

列出所有已注册的项

:return: 名称列表

---


##### `list_items()`

列出所有项及其状态

:return: {名称: 是否启用} 字典

---

