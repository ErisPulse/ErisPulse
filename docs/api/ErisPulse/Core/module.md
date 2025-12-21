# `ErisPulse.Core.module` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 模块系统

提供标准化的模块注册、加载和管理功能，与适配器系统保持一致的设计模式

---

## 类列表

### `class ModuleManager`

    模块管理器

提供标准化的模块注册、加载和管理功能，模仿适配器管理器的模式

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用register方法注册模块类
2. 使用load/unload方法加载/卸载模块
3. 通过get方法获取模块实例</p></div>

    
#### 方法列表

##### `register(module_name: str, module_class: Type, module_info: Optional[Dict] = None)`

    注册模块类

:param module_name: 模块名称
:param module_class: 模块类
:param module_info: 模块信息
:return: 是否注册成功

<dt>异常</dt><dd><code>TypeError</code> 当模块类无效时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> module.register("MyModule", MyModuleClass)
```
</details>

    ---
    
##### async `async load(module_name: str)`

    加载指定模块（标准化加载逻辑）

:param module_name: 模块名称
:return: 是否加载成功
    
<details class='example'><summary>示例</summary>

```python
>>> await module.load("MyModule")
```
</details>

    ---
    
##### async `async unload(module_name: str = 'Unknown')`

    卸载指定模块或所有模块

:param module_name: 模块名称，如果为None则卸载所有模块
:return: 是否卸载成功
    
<details class='example'><summary>示例</summary>

```python
>>> await module.unload("MyModule")
>>> await module.unload()  # 卸载所有模块
```
</details>

    ---
    
##### async `async _unload_single_module(module_name: str)`

    <div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
卸载单个模块

:param module_name: 模块名称
:return: 是否卸载成功

    ---
    
##### `get(module_name: str)`

    获取模块实例

:param module_name: 模块名称
:return: 模块实例或None
    
<details class='example'><summary>示例</summary>

```python
>>> my_module = module.get("MyModule")
```
</details>

    ---
    
##### `exists(module_name: str)`

    检查模块是否存在（在配置中注册）

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 模块是否存在</dd>

    ---
    
##### `is_loaded(module_name: str)`

    检查模块是否已加载

:param module_name: 模块名称
:return: 模块是否已加载
    
<details class='example'><summary>示例</summary>

```python
>>> if module.is_loaded("MyModule"): ...
```
</details>

    ---
    
##### `list_registered()`

    列出所有已注册的模块

:return: 模块名称列表
    
<details class='example'><summary>示例</summary>

```python
>>> registered = module.list_registered()
```
</details>

    ---
    
##### `list_loaded()`

    列出所有已加载的模块

:return: 模块名称列表
    
<details class='example'><summary>示例</summary>

```python
>>> loaded = module.list_loaded()
```
</details>

    ---
    
##### `_config_register(module_name: str, enabled: bool = False)`

    注册新模块信息

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt><code>enabled</code> <span class='type-hint'>bool</span></dt><dd>是否启用模块</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 操作是否成功</dd>

    ---
    
##### `is_enabled(module_name: str)`

    检查模块是否启用

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 模块是否启用</dd>

    ---
    
##### `enable(module_name: str)`

    启用模块

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 操作是否成功</dd>

    ---
    
##### `disable(module_name: str)`

    禁用模块

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 操作是否成功</dd>

    ---
    
##### `list_modules()`

    列出所有模块状态

<dt>返回值</dt><dd><span class='type-hint'>Dict[str, bool</span> ] 模块状态字典</dd>

    ---
    
##### `__getattr__(module_name: str)`

    通过属性访问获取模块实例

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>Any</span> 模块实例</dd>
<dt>异常</dt><dd><code>AttributeError</code> 当模块不存在或未启用时</dd>

    ---
    
##### `__contains__(module_name: str)`

    检查模块是否存在且处于启用状态

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 模块是否存在且启用</dd>

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>