# `ErisPulse.Core.module` 模块

---

## 模块概述


ErisPulse 模块系统

提供标准化的模块注册、加载和管理功能，与适配器系统保持一致的设计模式

---

## 类列表


### `class ModuleManager(ManagerBase)`

模块管理器

提供标准化的模块注册、加载和管理功能，模仿适配器管理器的模式

> **提示**
> 1. 使用register方法注册模块类
> 2. 使用load/unload方法加载/卸载模块
> 3. 通过get方法获取模块实例


#### 方法列表


##### `set_sdk_ref(sdk)`

设置 SDK 引用

:param sdk: SDK 实例
:return: 是否设置成功

---


##### `register(module_name: str, module_class: type, module_info: dict | None = None)`

注册模块类

:param module_name: 模块名称
:param module_class: 模块类
:param module_info: 模块信息
:return: 是否注册成功

**异常**: `TypeError` - 当模块类无效时抛出

**示例**:
```python
>>> module.register("MyModule", MyModuleClass)
```

---


##### `async async load(module_name: str)`

加载指定模块（标准化加载逻辑）

:param module_name: 模块名称
:return: 是否加载成功

**示例**:
```python
>>> await module.load("MyModule")
```

---


##### `async async unload(module_name: str | None = None)`

卸载指定模块或所有模块

:param module_name: 模块名称，None表示卸载所有模块（默认None）
:return: 是否卸载成功

**示例**:
```python
>>> await module.unload("MyModule")  # 卸载单个模块
>>> await module.unload()  # 卸载所有模块
```

---


##### `async async _unload_single_module(module_name: str)`

> **内部方法** 
卸载单个模块

:param module_name: 模块名称
:return: 是否卸载成功

---


##### `get(module_name: str)`

获取模块实例

:param module_name: 模块名称
:return: 模块实例或None

**示例**:
```python
>>> my_module = module.get("MyModule")
```

---


##### `exists(module_name: str)`

检查模块是否存在（已注册或在配置中）

- **module_name** (`str`): 模块名称
**返回值** (`bool`): 模块是否存在

---


##### `is_loaded(module_name: str)`

检查模块是否已加载

:param module_name: 模块名称
:return: 模块是否已加载

**示例**:
```python
>>> if module.is_loaded("MyModule"): ...
```

---


##### `is_running(module_name: str)`

检查模块是否正在运行（已加载）

:param module_name: 模块名称
:return: 模块是否正在运行

**示例**:
```python
>>> if module.is_running("MyModule"):
>>>     print("MyModule 正在运行")
```

---


##### `list_running()`

列出所有正在运行的模块（已加载）

:return: 模块名称列表

**示例**:
```python
>>> running = module.list_running()
>>> print("正在运行的模块:", running)
```

---


##### `list_registered()`

列出所有已注册的模块

:return: 模块名称列表

**示例**:
```python
>>> registered = module.list_registered()
```

---


##### `list_loaded()`

列出所有已加载的模块

:return: 模块名称列表

**示例**:
```python
>>> loaded = module.list_loaded()
```

---


##### `_config_register(module_name: str, enabled: bool = False)`

注册新模块信息

> **内部方法** 
此方法仅供内部使用

- **module_name** (`str`): 模块名称
- **enabled** (`bool`): 是否启用模块 (默认: False)
**返回值** (`bool`): 操作是否成功

---


##### `is_enabled(module_name: str)`

检查模块是否启用

- **module_name** (`str`): 模块名称
**返回值** (`bool`): 模块是否启用

---


##### `enable(module_name: str)`

启用模块

- **module_name** (`str`): 模块名称
**返回值** (`bool`): 操作是否成功

---


##### `disable(module_name: str)`

禁用模块

- **module_name** (`str`): 模块名称
**返回值** (`bool`): 操作是否成功

---


##### `unregister(module_name: str)`

取消注册模块

:param module_name: 模块名称
:return: 是否取消成功

> **内部方法** 
注意：此方法仅取消注册，不卸载已加载的模块

---


##### `clear()`

清除所有模块实例和类

> **内部方法** 
此方法用于反初始化时完全重置模块管理器状态

---


##### `list_items()`

列出所有模块状态

**返回值** (`dict[str, bool`): ] {模块名: 是否启用} 字典

---


##### `get_info(module_name: str)`

获取模块信息

:param module_name: 模块名称
:return: 模块信息字典，不存在则返回None

**示例**:
```python
>>> info = module.get_info("MyModule")
```

---


##### `get_status_summary()`

获取模块的完整状态摘要

便于WebUI展示所有模块的注册、加载和启用状态。

:return: 状态摘要字典

**示例**:
```python
>>> summary = module.get_status_summary()
>>> # {
>>> #     "modules": {
>>> #         "MyModule": {
>>> #             "status": "loaded",
>>> #             "enabled": True,
>>> #             "is_base_module": True
>>> #         }
>>> #     }
>>> # }
```

---


##### `list_modules()`

列出所有模块状态

> **已弃用** 请使用 list_items() 代替

**返回值** (`dict[str, bool`): ] 模块状态字典

---


##### `__getattr__(module_name: str)`

通过属性访问获取模块实例

- **module_name** (`str`): 模块名称
**返回值** (`Any`): 模块实例
**异常**: `AttributeError` - 当模块不存在或未启用时

**示例**:
```python
>>> my_module = module.MyModule
```

---


##### `__contains__(module_name: str)`

检查模块是否存在且处于启用状态

- **module_name** (`str`): 模块名称
**返回值** (`bool`): 模块是否存在且启用

**示例**:
```python
>>> if "MyModule" in module: ...
```

---

