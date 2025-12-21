# `ErisPulse.Core.lifecycle` 模块

<sup>更新时间: 2025-12-21 14:28:48</sup>

---

## 模块概述


ErisPulse 生命周期管理模块

提供统一的生命周期事件管理和触发机制

事件标准格式:
{
    "event": "事件名称",  # 必填
    "timestamp": float,  # 必填，Unix时间戳
    "data": dict,        # 可选，事件相关数据
    "source": str,       # 必填，事件来源
    "msg": str           # 可选，事件描述
}

---

## 类列表

### `class LifecycleManager`

    生命周期管理器

管理SDK的生命周期事件，提供事件注册和触发功能
支持点式结构事件监听，例如 module.init 可以被 module 监听到

    
#### 方法列表

##### `_validate_event(event_data: Dict[str, Any])`

    验证事件数据格式

:param event_data: 事件数据字典
:return: 是否有效

    ---
    
##### `on(event: str)`

    注册生命周期事件处理器

:param event: 事件名称，支持点式结构如 module.init
:return: 装饰器函数

<dt>异常</dt><dd><code>ValueError</code> 当事件名无效时抛出</dd>

    ---
    
##### `start_timer(timer_id: str)`

    开始计时

:param timer_id: 计时器ID

    ---
    
##### `get_duration(timer_id: str)`

    获取指定计时器的持续时间

:param timer_id: 计时器ID
:return: 持续时间(秒)

    ---
    
##### `stop_timer(timer_id: str)`

    停止计时并返回持续时间

:param timer_id: 计时器ID
:return: 持续时间(秒)

    ---
    
##### async `async submit_event(event_type: str)`

    提交生命周期事件

:param event: 事件名称
:param event_data: 事件数据字典

    ---
    
##### async `async _execute_handlers(event: str, event_data: Dict[str, Any])`

    执行事件处理器

:param event: 事件名称
:param event_data: 事件数据

    ---
    
<sub>文档最后更新于 2025-12-21 14:28:48</sub>