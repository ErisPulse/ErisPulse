# `ErisPulse.Core.Event.message_builder` 模块

---

## 模块概述


ErisPulse 消息构建器

提供链式调用风格的 OneBot12 标准消息段构建工具

> **提示**
> 1. 用于构建 OneBot12 标准消息段列表（list[dict]）
> 2. 配合 Raw_ob12 使用，是反向转换的搭档工具
> 3. 支持链式调用和快速构建两种模式

---

## 类列表


### `class _DualMethod`

双模式方法描述符

通过类访问时返回静态工厂方法（返回 list），
通过实例访问时返回链式实例方法（返回 self）。


### `class MessageBuilder`

OneBot12 消息段构建器

提供链式调用风格构建标准消息段列表，配合 `Send.Raw_ob12()` 使用。

> **提示**
> 使用方式：
> 1. 链式调用：MessageBuilder().text("Hi").image("url").build()
> 2. 快速构建：MessageBuilder.text("Hi")
> 3. 配合发送：await send.To("group","123").Raw_ob12(MessageBuilder().text("Hi").build())


#### 方法列表


##### `custom(segment_type: str, data: dict[str, Any])`

添加自定义消息段

用于添加平台扩展消息段或其他非标准消息段

:param segment_type: 消息段类型（如 "yunhu_form"）
:param data: 消息段数据
:return: MessageBuilder 实例

**示例**:
```python
>>> MessageBuilder().custom("yunhu_form", {"form_id": "123"}).build()
```

---


##### `build()`

构建消息段列表

:return: OneBot12 标准消息段列表

**示例**:
```python
>>> segments = MessageBuilder().text("Hello").image("url").build()
>>> # [{"type": "text", "data": {"text": "Hello"}}, {"type": "image", "data": {"file": "url"}}]
```

---


##### `copy()`

复制当前构建器（深拷贝消息段列表）

:return: 新的 MessageBuilder 实例

**示例**:
```python
>>> base = MessageBuilder().text("基础内容")
>>> msg1 = base.copy().image("img1").build()
>>> msg2 = base.copy().image("img2").build()
```

---


##### `clear()`

清空已添加的消息段

:return: MessageBuilder 实例自身

**示例**:
```python
>>> builder = MessageBuilder().text("将被清除")
>>> builder.clear().text("新内容").build()
```

---


##### `__len__()`

返回已添加的消息段数量

---


##### `__bool__()`

是否有消息段

---

