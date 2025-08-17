# `ErisPulse.Core.module_registry` 模块

<sup>更新时间: 2025-08-17 09:01:35</sup>

---

## 模块概述


ErisPulse 模块管理器

提供模块的注册、状态管理和依赖关系处理功能。支持模块的启用/禁用、版本控制和依赖解析。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系</p></div>

---

## 类列表

### `class ModuleRegistry`

ErisPulse 模块注册表

管理所有模块的注册信息和启用状态

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 模块信息通过 set_module/get_module 管理
2. 模块状态通过 set_module_status/get_module_status 控制
3. 支持批量操作模块信息</p></div>


#### 方法列表

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

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt><code>status</code> <span class='type-hint'>bool</span></dt><dd>启用状态 (True=启用, False=禁用)</dd>

<details class='example'><summary>示例</summary>

```python
>>> # 启用模块
>>> module_registry.set_module_status("MyModule", True)
>>> # 禁用模块
>>> module_registry.set_module_status("MyModule", False)
```
</details>

---

##### `get_module_status(module_name: str)`

获取模块启用状态

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 模块是否启用</dd>

<details class='example'><summary>示例</summary>

```python
>>> if module_registry.get_module_status("MyModule"):
>>>     print("模块已启用")
```
</details>

---

##### `set_module(module_name: str, module_info: Dict[str, Any])`

注册或更新模块信息

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt><code>module_info</code> <span class='type-hint'>Dict[str, Any</span></dt><dd>] 模块信息字典</dd>
    必须包含 version 和 description 字段

<details class='example'><summary>示例</summary>

```python
>>> module_registry.set_module("MyModule", {
>>>     "version": "1.0.0",
>>>     "description": "我的模块",
>>>     "dependencies": [],
>>>     "author": "开发者",
>>>     "license": "MIT"
>>> })
```
</details>

---

##### `get_module(module_name: str)`

获取模块信息

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>Optional[Dict[str, Any</span> ]] 模块信息字典或None</dd>

<details class='example'><summary>示例</summary>

```python
>>> module_info = module_registry.get_module("MyModule")
>>> if module_info:
>>>     print(f"模块版本: {module_info.get('version')}")
```
</details>

---

##### `set_all_modules(modules_info: Dict[str, Dict[str, Any]])`

批量设置模块信息

<dt><code>modules_info</code> <span class='type-hint'>Dict[str, Dict[str, Any</span></dt><dd>]] 模块信息字典</dd>
    格式: {模块名: 模块信息}

<details class='example'><summary>示例</summary>

```python
>>> module_registry.set_all_modules({
>>>     "Module1": {"version": "1.0", "status": True},
>>>     "Module2": {"version": "2.0", "status": False}
>>> })
```
</details>

---

##### `get_all_modules()`

获取所有已注册模块信息

<dt>返回值</dt><dd><span class='type-hint'>Dict[str, Dict[str, Any</span> ]] 所有模块信息字典</dd>

<details class='example'><summary>示例</summary>

```python
>>> all_modules = module_registry.get_all_modules()
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

移除模块注册信息

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 是否成功移除</dd>

<details class='example'><summary>示例</summary>

```python
>>> if module_registry.remove_module("OldModule"):
>>>     print("模块已移除")
```
</details>

---

##### `update_prefixes(module_prefix: Optional[str] = None, status_prefix: Optional[str] = None)`

更新模块存储前缀配置

<dt><code>module_prefix</code> <span class='type-hint'>Optional[str</span></dt><dd>] 模块数据前缀 (默认: "erispulse.data.modules.info:")</dd>
<dt><code>status_prefix</code> <span class='type-hint'>Optional[str</span></dt><dd>] 模块状态前缀 (默认: "erispulse.data.modules.status:")</dd>

<details class='example'><summary>示例</summary>

```python
>>> # 更新模块前缀
>>> module_registry.update_prefixes(
>>>     module_prefix="custom.module.data:",
>>>     status_prefix="custom.module.status:"
>>> )
```
</details>

---

<sub>文档最后更新于 2025-08-17 09:01:35</sub>