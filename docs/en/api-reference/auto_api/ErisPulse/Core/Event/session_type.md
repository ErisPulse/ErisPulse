# `ErisPulse.Core.Event.session_type` 模块

---

## 模块概述


ErisPulse 会话类型管理模块

提供会话类型的标准化定义、映射、转换和推断功能

> **提示**
> 1. 定义了通用的会话类型和ID字段映射
> 2. 提供接收类型到发送类型的自动转换（如 private → user）
> 3. 支持根据ID字段自动推断会话类型
> 4. 允许适配器注册自定义类型映射

---

## 函数列表


### `register_custom_type(receive_type: str, send_type: str, id_field: str, platform: str | None = None)`

注册自定义会话类型

:param receive_type: 接收事件类型（detail_type）
:param send_type: 发送目标类型
:param id_field: 对应的ID字段名
:param platform: 平台名称（可选，用于区分同名不同平台的类型）
:return: 是否注册成功

---


### `unregister_custom_type(receive_type: str, platform: str | None = None)`

注销自定义会话类型

:param receive_type: 接收事件类型
:param platform: 平台名称
:return: 是否注销成功

---


### `get_id_field(receive_type: str, platform: str | None = None)`

根据接收类型获取对应的ID字段名

:param receive_type: 接收事件类型
:param platform: 平台名称（可选）
:return: ID字段名

---


### `get_receive_type(id_field: str, platform: str | None = None)`

根据ID字段获取对应的接收类型

:param id_field: ID字段名
:param platform: 平台名称（可选）
:return: 接收类型

---


### `convert_to_send_type(receive_type: str, platform: str | None = None)`

将接收类型转换为发送目标类型

:param receive_type: 接收事件类型
:param platform: 平台名称（可选）
:return: 发送目标类型

**示例**:
```python
>>> convert_to_send_type("private")  # 返回 "user"
>>> convert_to_send_type("group")   # 返回 "group"
```

---


### `convert_to_receive_type(send_type: str, platform: str | None = None)`

将发送目标类型转换为接收类型

:param send_type: 发送目标类型
:param platform: 平台名称（可选）
:return: 接收类型

**示例**:
```python
>>> convert_to_receive_type("user")   # 返回 "private"
>>> convert_to_receive_type("group")  # 返回 "group"
```

---


### `infer_receive_type(event: dict, platform: str | None = None)`

根据事件数据自动推断接收类型

检查顺序：
1. 如果存在 detail_type，直接使用
2. 检查各种 ID 字段，按优先级返回

:param event: 事件数据字典
:param platform: 平台名称（可选）
:return: 推断的接收类型

**示例**:
```python
>>> event = {"group_id": "123"}
>>> infer_receive_type(event)  # 返回 "group"
```

---


### `get_target_id(event: dict, platform: str | None = None)`

获取事件的目标ID（根据推断的会话类型）

:param event: 事件数据字典
:param platform: 平台名称（可选）
:return: 目标ID

**示例**:
```python
>>> event = {"detail_type": "group", "group_id": "123"}
>>> get_target_id(event)  # 返回 "123"
```

---


### `get_send_type_and_target_id(event: dict, platform: str | None = None)`

获取发送类型和目标ID（一步完成类型转换和ID获取）

:param event: 事件数据字典
:param platform: 平台名称（可选）
:return: (发送类型, 目标ID)

**示例**:
```python
>>> event = {"detail_type": "private", "user_id": "123"}
>>> get_send_type_and_target_id(event)  # 返回 ("user", "123")
```

---


### `is_standard_type(receive_type: str)`

检查是否为标准接收类型

:param receive_type: 接收事件类型
:return: 是否为标准类型

---


### `is_valid_send_type(send_type: str)`

检查是否为有效的发送类型

:param send_type: 发送目标类型
:return: 是否为有效类型

---


### `get_standard_types()`

获取所有标准接收类型

:return: 标准类型集合

---


### `get_send_types()`

获取所有发送类型

:return: 发送类型集合

---


### `clear_custom_types(platform: str | None = None)`

清除自定义类型映射

:param platform: 平台名称（可选，如果指定则只清除该平台的类型）
:return: 清除的类型数量

---

