# `ErisPulse.Core.module` 模块

<sup>更新时间: 2025-08-18 12:43:21</sup>

---

## 模块概述


ErisPulse 模块管理模块

提供便捷的模块访问接口

---

## 类列表

### `class ModuleManager`

模块管理器

提供便捷的模块访问接口，支持获取模块实例、检查模块状态等操作


#### 方法列表

##### `get(module_name: str)`

获取指定模块的实例

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>Any</span> 模块实例或None</dd>

---

##### `exists(module_name: str)`

检查模块是否存在

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>bool</span> 模块是否存在</dd>

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

列出所有模块信息

<dt>返回值</dt><dd><span class='type-hint'>Dict[str, Dict[str, Any</span> ]] 模块信息字典</dd>

---

##### `get_info(module_name: str)`

获取模块详细信息

<dt><code>module_name</code> <span class='type-hint'>str</span></dt><dd>模块名称</dd>
<dt>返回值</dt><dd><span class='type-hint'>Optional[Dict[str, Any</span> ]] 模块信息字典</dd>

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

<sub>文档最后更新于 2025-08-18 12:43:21</sub>