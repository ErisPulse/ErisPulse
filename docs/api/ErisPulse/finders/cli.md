# `ErisPulse.finders.cli` 模块

---

## 模块概述


ErisPulse CLI扩展发现器

专门用于发现和查找 ErisPulse CLI 扩展的 entry-points

> **提示**
> 1. 查找 erispulse.cli 组的 entry-points
> 2. 支持缓存机制，避免重复查询
> 3. 提供便捷的查询接口

---

## 类列表


### `class CLIFinder(BaseFinder)`

CLI扩展发现器

负责发现 ErisPulse CLI 扩展的 entry-points

> **提示**
> 使用方式：
> >>> finder = CLIFinder()
> >>> # 查找所有CLI扩展
> >>> cli_extensions = finder.find_all()
> >>> # 按名称查找
> >>> extension = finder.find_by_name("my_extension")
> >>> # 获取CLI扩展映射
> >>> extension_map = finder.get_entry_point_map()
> >>> # 检查CLI扩展是否存在
> >>> if "my_extension" in finder:
> ...     print("CLI扩展存在")


#### 方法列表


##### `_get_entry_point_group()`

获取 entry-point 组名

:return: "erispulse.cli"

---


##### `get_all_names()`

获取所有CLI扩展名称

:return: CLI扩展名称列表

---


##### `get_all_packages()`

获取所有CLI扩展所属的 PyPI 包名

:return: PyPI 包名列表

---


##### `get_package_for_extension(extension_name: str)`

获取指定CLI扩展所属的 PyPI 包名

:param extension_name: CLI扩展名称
:return: PyPI 包名，未找到返回 None

---


##### `get_extension_info(extension_name: str)`

获取CLI扩展的完整信息

:param extension_name: CLI扩展名称
:return: CLI扩展信息字典，未找到返回 None

:return:
    Dict: {
        "name": CLI扩展名称,
        "package": PyPI 包名,
        "version": 版本号,
        "entry_point": entry-point 对象
    }

---


##### `get_extensions_by_package(package_name: str)`

获取指定 PyPI 包下的所有CLI扩展名称

:param package_name: PyPI 包名
:return: CLI扩展名称列表

---

