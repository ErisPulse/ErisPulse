# `ErisPulse.finders.module` 模块

> 最后更新：2026-02-04 08:04:59

---

## 模块概述


ErisPulse 模块发现器

专门用于发现和查找 ErisPulse 模块的 entry-points

> **提示**
> 1. 查找 erispulse.module 组的 entry-points
> 2. 支持缓存机制，避免重复查询
> 3. 提供便捷的查询接口

---

## 类列表


### `class ModuleFinder(BaseFinder)`

模块发现器

负责发现 ErisPulse 模块的 entry-points

> **提示**
> 使用方式：
> >>> finder = ModuleFinder()
> >>> # 查找所有模块
> >>> modules = finder.find_all()
> >>> # 按名称查找
> >>> module = finder.find_by_name("my_module")
> >>> # 获取模块映射
> >>> module_map = finder.get_entry_point_map()
> >>> # 检查模块是否存在
> >>> if "my_module" in finder:
> ...     print("模块存在")


#### 方法列表


##### `_get_entry_point_group()`

获取 entry-point 组名

:return: "erispulse.module"

---


##### `get_all_names()`

获取所有模块名称

:return: 模块名称列表

---


##### `get_all_packages()`

获取所有模块所属的 PyPI 包名

:return: PyPI 包名列表

---


##### `get_package_for_module(module_name: str)`

获取指定模块所属的 PyPI 包名

:param module_name: 模块名称
:return: PyPI 包名，未找到返回 None

---


##### `get_module_info(module_name: str)`

获取模块的完整信息

:param module_name: 模块名称
:return: 模块信息字典，未找到返回 None

:return:
    Dict: {
        "name": 模块名称,
        "package": PyPI 包名,
        "version": 版本号,
        "entry_point": entry-point 对象
    }

---


##### `get_modules_by_package(package_name: str)`

获取指定 PyPI 包下的所有模块名称

:param package_name: PyPI 包名
:return: 模块名称列表

---

