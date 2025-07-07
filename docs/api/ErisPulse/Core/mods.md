# `ErisPulse/Core/mods` 模块

ErisPulse 模块管理器

提供模块的注册、状态管理和依赖关系处理功能。支持模块的启用/禁用、版本控制和依赖解析。

> **提示**：
1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系

## 类

### `ModuleManager`

模块管理器

管理所有模块的注册、状态和依赖关系

> **提示**：
1. 通过set_module/get_module管理模块信息
2. 通过set_module_status/get_module_status控制模块状态
3. 通过set_all_modules/get_all_modules批量操作模块


#### 方法

##### `module_prefix`

获取模块数据前缀

:return: 模块数据前缀字符串


##### `status_prefix`

获取模块状态前缀

:return: 模块状态前缀字符串


##### `set_module_status`

设置模块启用状态

:param module_name: 模块名称
:param status: 启用状态

:example:
>>> # 启用模块
>>> mods.set_module_status("MyModule", True)
>>> # 禁用模块
>>> mods.set_module_status("MyModule", False)


##### `get_module_status`

获取模块启用状态

:param module_name: 模块名称
:return: 模块是否启用

:example:
>>> if mods.get_module_status("MyModule"):
>>>     print("模块已启用")


##### `set_module`

设置模块信息

:param module_name: 模块名称
:param module_info: 模块信息字典

:example:
>>> mods.set_module("MyModule", {
>>>     "version": "1.0.0",
>>>     "description": "我的模块",
>>>     "status": True
>>> })


##### `get_module`

获取模块信息

:param module_name: 模块名称
:return: 模块信息字典或None

:example:
>>> module_info = mods.get_module("MyModule")
>>> if module_info:
>>>     print(f"模块版本: {module_info.get('version')}")


##### `set_all_modules`

批量设置多个模块信息

:param modules_info: 模块信息字典

:example:
>>> mods.set_all_modules({
>>>     "Module1": {"version": "1.0", "status": True},
>>>     "Module2": {"version": "2.0", "status": False}
>>> })


##### `get_all_modules`

获取所有模块信息

:return: 模块信息字典

:example:
>>> all_modules = mods.get_all_modules()
>>> for name, info in all_modules.items():
>>>     print(f"{name}: {info.get('status')}")


##### `update_module`

更新模块信息

:param module_name: 模块名称
:param module_info: 完整的模块信息字典


##### `remove_module`

移除模块

:param module_name: 模块名称
:return: 是否成功移除

:example:
>>> if mods.remove_module("OldModule"):
>>>     print("模块已移除")


##### `update_prefixes`

更新模块前缀配置

:param module_prefix: 新的模块数据前缀(可选)
:param status_prefix: 新的模块状态前缀(可选)

:example:
>>> # 更新模块前缀
>>> mods.update_prefixes(
>>>     module_prefix="custom.module.data:",
>>>     status_prefix="custom.module.status:"
>>> )

