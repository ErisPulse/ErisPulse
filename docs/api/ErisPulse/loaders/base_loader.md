# `ErisPulse.loaders.base_loader` 模块

> 最后更新：2026-02-01 03:21:24

---

## 模块概述


ErisPulse 基础加载器

定义加载器的抽象基类，提供通用的加载器接口和结构

> **提示**
> 1. 所有具体加载器应继承自 BaseLoader
> 2. 子类需实现 _process_entry_point 方法
> 3. 支持启用/禁用配置管理

---

## 类列表


### `class BaseLoader(ABC)`

基础加载器抽象类

提供通用的加载器接口和配置管理功能

> **提示**
> 子类需要实现：
> - _get_entry_point_group: 返回 entry-point 组名
> - _process_entry_point: 处理单个 entry-point
> - _should_eager_load: 判断是否立即加载

> **内部方法** 
此类仅供内部使用，不应直接实例化


#### 方法列表


##### `__init__(config_prefix: str)`

初始化基础加载器

:param config_prefix: 配置前缀（如 "ErisPulse.adapters" 或 "ErisPulse.modules"）

---


##### `_get_entry_point_group()`

获取 entry-point 组名

:return: entry-point 组名

> **内部方法** 
子类必须实现此方法

---


##### `async async _process_entry_point(entry_point: Any, objs: Dict[str, Any], enabled_list: List[str], disabled_list: List[str], manager_instance: Any)`

处理单个 entry-point

:param entry_point: entry-point 对象
:param objs: 对象字典
:param enabled_list: 启用列表
:param disabled_list: 禁用列表
:param manager_instance: 管理器实例（用于调用 exists/is_enabled 等方法）
:return: (更新后的对象字典, 更新后的启用列表, 更新后的禁用列表)

> **内部方法** 
子类必须实现此方法

---


##### `async async load(manager_instance: Any)`

从 entry-points 加载对象

:param manager_instance: 管理器实例
:return: 
    Dict[str, Any]: 对象字典
    List[str]: 启用列表
    List[str]: 禁用列表
    
**异常**: `ImportError` - 当加载失败时抛出

---


##### `_register_config(name: str, enabled: bool = False)`

注册配置项

:param name: 名称
:param enabled: 是否启用
:return: 操作是否成功

> **内部方法** 
内部方法，用于注册新的配置项

---


##### `_get_config_status(name: str)`

获取配置状态

:param name: 名称
:return: 是否启用

> **内部方法** 
内部方法，用于获取配置状态

---

