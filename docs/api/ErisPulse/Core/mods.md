# 📦 `ErisPulse.Core.mods` 模块

<sup>自动生成于 2025-08-02 01:50:12</sup>

---

## 模块概述


ErisPulse 模块管理器

提供模块的注册、状态管理和依赖关系处理功能。支持模块的启用/禁用、版本控制和依赖解析。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系</p></div>

---

## 🏛️ 类

### `class ModuleManager`

模块管理器

管理所有模块的注册、状态和依赖关系

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 通过set_module/get_module管理模块信息
2. 通过set_module_status/get_module_status控制模块状态
3. 通过set_all_modules/get_all_modules批量操作模块</p></div>


#### 🧰 方法

##### `_ensure_prefixes()`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
确保模块前缀配置存在

---

##### `module_prefix()`

获取模块数据前缀

:return: 模块数据前缀字符串

---

##### `status_prefix()`

获取模块状态前缀

:return: 模块状态前缀字符串

---

##### `set_module_status(module_name: str, status: bool)`

设置模块启用状态

:param module_name: 模块名称
:param status: 启用状态

<details class='example'><summary>示例</summary>

```python
>>> # 启用模块
>>> mods.set_module_status("MyModule", True)
>>> # 禁用模块
>>> mods.set_module_status("MyModule", False)
```
</details>

---

##### `get_module_status(module_name: str)`

获取模块启用状态

:param module_name: 模块名称
:return: 模块是否启用

<details class='example'><summary>示例</summary>

```python
>>> if mods.get_module_status("MyModule"):
>>>     print("模块已启用")
```
</details>

---

##### `set_module(module_name: str, module_info: Dict[str, Any])`

设置模块信息

:param module_name: 模块名称
:param module_info: 模块信息字典

<details class='example'><summary>示例</summary>

```python
>>> mods.set_module("MyModule", {
>>>     "version": "1.0.0",
>>>     "description": "我的模块",
>>> })
```
</details>

---

##### `get_module(module_name: str)`

获取模块信息

:param module_name: 模块名称
:return: 模块信息字典或None

<details class='example'><summary>示例</summary>

```python
>>> module_info = mods.get_module("MyModule")
>>> if module_info:
>>>     print(f"模块版本: {module_info.get('version')}")
```
</details>

---

##### `set_all_modules(modules_info: Dict[str, Dict[str, Any]])`

批量设置多个模块信息

:param modules_info: 模块信息字典

<details class='example'><summary>示例</summary>

```python
>>> mods.set_all_modules({
>>>     "Module1": {"version": "1.0", "status": True},
>>>     "Module2": {"version": "2.0", "status": False}
>>> })
```
</details>

---

##### `get_all_modules()`

获取所有模块信息

:return: 模块信息字典

<details class='example'><summary>示例</summary>

```python
>>> all_modules = mods.get_all_modules()
>>> for name, info in all_modules.items():
>>>     print(f"{name}: {info.get('status')}")
```
</details>

---

##### `update_module(module_name: str, module_info: Dict[str, Any])`

更新模块信息

:param module_name: 模块名称
:param module_info: 完整的模块信息字典

---

##### `remove_module(module_name: str)`

移除模块

:param module_name: 模块名称
:return: 是否成功移除

<details class='example'><summary>示例</summary>

```python
>>> if mods.remove_module("OldModule"):
>>>     print("模块已移除")
```
</details>

---

##### `update_prefixes(module_prefix: Optional[str] = None, status_prefix: Optional[str] = None)`

更新模块前缀配置

:param module_prefix: 新的模块数据前缀(可选)
:param status_prefix: 新的模块状态前缀(可选)

<details class='example'><summary>示例</summary>

```python
>>> # 更新模块前缀
>>> mods.update_prefixes(
>>>     module_prefix="custom.module.data:",
>>>     status_prefix="custom.module.status:"
>>> )
```
</details>

---

<sub>文档最后更新于 2025-08-02 01:50:12</sub>