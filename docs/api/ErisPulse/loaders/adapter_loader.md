# `ErisPulse.loaders.adapter_loader` 模块

> 最后更新：2026-01-31 19:10:05

---

## 模块概述


ErisPulse 适配器加载器

专门用于从 PyPI 包加载和初始化适配器

> **提示**
> 1. 适配器必须通过 entry-points 机制注册到 erispulse.adapter 组
> 2. 适配器类必须继承 BaseAdapter
> 3. 适配器不适用懒加载

---

## 类列表


### `class AdapterLoader(BaseLoader)`

适配器加载器

负责从 PyPI entry-points 加载适配器

> **提示**
> 使用方式：
> >>> loader = AdapterLoader()
> >>> adapter_objs, enabled, disabled = await loader.load(adapter_manager)


#### 方法列表


##### `__init__()`

初始化适配器加载器

---


##### `_get_entry_point_group()`

获取 entry-point 组名

:return: "erispulse.adapter"

---


##### `async async _process_entry_point(entry_point: Any, objs: Dict[str, Any], enabled_list: List[str], disabled_list: List[str], manager_instance: Any)`

处理单个适配器 entry-point

:param entry_point: entry-point 对象
:param objs: 适配器对象字典
:param enabled_list: 启用的适配器列表
:param disabled_list: 停用的适配器列表
:param manager_instance: 适配器管理器实例

:return: 
    Dict[str, Any]: 更新后的适配器对象字典
    List[str]: 更新后的启用适配器列表 
    List[str]: 更新后的禁用适配器列表
    
**异常**: `ImportError` - 当适配器加载失败时抛出

---


##### `async async register_to_manager(adapters: List[str], adapter_objs: Dict[str, Any], manager_instance: Any)`

将适配器注册到管理器

:param adapters: 适配器名称列表
:param adapter_objs: 适配器对象字典
:param manager_instance: 适配器管理器实例
:return: 适配器注册是否成功

> **提示**
> 此方法由初始化协调器调用

---

