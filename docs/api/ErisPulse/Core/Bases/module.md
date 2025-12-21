# `ErisPulse.Core.Bases.module` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 模块基础模块

提供模块基类定义和标准接口

---

## 类列表

### `class BaseModule`

    模块基类

提供模块加载和卸载的标准接口

    
#### 方法列表

##### `should_eager_load()`

    模块是否应该在启动时加载
默认为False(即懒加载)

:return: 是否应该在启动时加载

    ---
    
##### async `async on_load(event: dict)`

    当模块被加载时调用

:param event: 事件内容
:return: 处理结果

<div class='admonition tip'><p class='admonition-title'>提示</p><p>其中，event事件内容为:
    `{ "module_name": "模块名" }`</p></div>

    ---
    
##### async `async on_unload(event: dict)`

    当模块被卸载时调用

:param event: 事件内容
:return: 处理结果

<div class='admonition tip'><p class='admonition-title'>提示</p><p>其中，event事件内容为:
    `{ "module_name": "模块名" }`</p></div>

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>