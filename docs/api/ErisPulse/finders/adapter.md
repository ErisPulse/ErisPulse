# `ErisPulse.finders.adapter` 模块

> 最后更新：2026-02-04 08:04:59

---

## 模块概述


ErisPulse 适配器发现器

专门用于发现和查找 ErisPulse 适配器的 entry-points

> **提示**
> 1. 查找 erispulse.adapter 组的 entry-points
> 2. 支持缓存机制，避免重复查询
> 3. 提供便捷的查询接口

---

## 类列表


### `class AdapterFinder(BaseFinder)`

适配器发现器

负责发现 ErisPulse 适配器的 entry-points

> **提示**
> 使用方式：
> >>> finder = AdapterFinder()
> >>> # 查找所有适配器
> >>> adapters = finder.find_all()
> >>> # 按名称查找
> >>> adapter = finder.find_by_name("my_adapter")
> >>> # 获取适配器映射
> >>> adapter_map = finder.get_entry_point_map()
> >>> # 检查适配器是否存在
> >>> if "my_adapter" in finder:
> ...     print("适配器存在")


#### 方法列表


##### `_get_entry_point_group()`

获取 entry-point 组名

:return: "erispulse.adapter"

---


##### `get_all_names()`

获取所有适配器名称

:return: 适配器名称列表

---


##### `get_all_packages()`

获取所有适配器所属的 PyPI 包名

:return: PyPI 包名列表

---


##### `get_package_for_adapter(adapter_name: str)`

获取指定适配器所属的 PyPI 包名

:param adapter_name: 适配器名称
:return: PyPI 包名，未找到返回 None

---


##### `get_adapter_info(adapter_name: str)`

获取适配器的完整信息

:param adapter_name: 适配器名称
:return: 适配器信息字典，未找到返回 None

:return:
    Dict: {
        "name": 适配器名称,
        "package": PyPI 包名,
        "version": 版本号,
        "entry_point": entry-point 对象
    }

---


##### `get_adapters_by_package(package_name: str)`

获取指定 PyPI 包下的所有适配器名称

:param package_name: PyPI 包名
:return: 适配器名称列表

---

