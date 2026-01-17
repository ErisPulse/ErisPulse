# `ErisPulse.Core.module` 模块

> 最后更新：2026-01-17 19:15:33

---

## 模块概述


ErisPulse 模块系统

提供标准化的模块注册、加载和管理功能，与适配器系统保持一致的设计模式

---

## 类列表


### `class ModuleManager`

模块管理器

提供标准化的模块注册、加载和管理功能，模仿适配器管理器的模式

> **提示**
> 1. 使用register方法注册模块类
> 2. 使用load/unload方法加载/卸载模块
> 3. 通过get方法获取模块实例


#### 方法列表


##### `register(module_name: str, module_class: Type, module_info: Optional[Dict] = None)`

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


##### `async async unload(module_name: str = 'Unknown')`

卸载指定模块或所有模块

:param module_name: 模块名称，如果为None则卸载所有模块
:return: 是否卸载成功
    

**示例**:
```python
>>> await module.unload("MyModule")
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

检查模块是否存在（在配置中注册）

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

- **module_name** (`str`): 模块名称
- **enabled** (`bool`): 是否启用模块
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


##### `list_modules()`

列出所有模块状态

**返回值** (`Dict[str, bool`): ] 模块状态字典

---


##### `__getattr__(module_name: str)`

通过属性访问获取模块实例

- **module_name** (`str`): 模块名称
**返回值** (`Any`): 模块实例
**异常**: `AttributeError` - 当模块不存在或未启用时

---


##### `__contains__(module_name: str)`

检查模块是否存在且处于启用状态

- **module_name** (`str`): 模块名称
**返回值** (`bool`): 模块是否存在且启用

---

