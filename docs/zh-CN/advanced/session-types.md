# 会话类型系统

ErisPulse 会话类型系统负责定义和管理消息的会话类型（私聊、群聊、频道等），并提供接收类型与发送类型之间的自动转换。

## 类型定义

### 接收类型 (ReceiveType)

接收类型来自 OneBot12 事件中的 `detail_type` 字段，表示事件的会话场景：

| 类型 | 说明 | ID 字段 |
|------|------|---------|
| `private` | 私聊消息 | `user_id` |
| `group` | 群聊消息 | `group_id` |
| `channel` | 频道消息 | `channel_id` |
| `guild` | 服务器消息 | `guild_id` |
| `thread` | 话题/子频道消息 | `thread_id` |
| `user` | 用户消息（扩展） | `user_id` |

### 发送类型 (SendType)

发送类型用于 `Send.To(type, id)` 中指定发送目标：

| 类型 | 说明 |
|------|------|
| `user` | 发送给用户 |
| `group` | 发送到群组 |
| `channel` | 发送到频道 |
| `guild` | 发送到服务器 |
| `thread` | 发送到话题 |

## 类型映射

接收类型和发送类型之间存在默认映射关系：

```
接收 (Receive)          发送 (Send)
─────────────          ──────────
private        ──→     user
group          ──→     group
channel        ──→     channel
guild          ──→     guild
thread         ──→     thread
user           ──→     user
```

关键区别：**接收时用 `private`，发送时用 `user`**。这是 OneBot12 标准的设计——事件描述的是"私聊场景"，而发送描述的是"用户目标"。

## 自动推断

当事件没有明确的 `detail_type` 字段时，系统会根据事件中存在的 ID 字段自动推断会话类型：

**优先级**：`group_id` > `channel_id` > `guild_id` > `thread_id` > `user_id`

```python
from ErisPulse.Core.Event.session_type import infer_receive_type

# 有 group_id → 推断为 group
event1 = {"group_id": "123", "user_id": "456"}
print(infer_receive_type(event1))  # "group"

# 只有 user_id → 推断为 private
event2 = {"user_id": "456"}
print(infer_receive_type(event2))  # "private"
```

## 核心 API

### 类型转换

```python
from ErisPulse.Core.Event.session_type import (
    convert_to_send_type,
    convert_to_receive_type,
)

# 接收类型 → 发送类型
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# 发送类型 → 接收类型
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### ID 字段查询

```python
from ErisPulse.Core.Event.session_type import get_id_field, get_receive_type

# 根据类型获取 ID 字段名
get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

# 根据 ID 字段获取类型
get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 一步获取发送信息

```python
from ErisPulse.Core.Event.session_type import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# 直接用于 Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 获取目标 ID

```python
from ErisPulse.Core.Event.session_type import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 自定义类型注册

适配器可以为平台特有的会话类型注册自定义映射：

```python
from ErisPulse.Core.Event.session_type import register_custom_type, unregister_custom_type

# 注册自定义类型
register_custom_type(
    receive_type="thread_reply",     # 接收类型名
    send_type="thread",              # 对应的发送类型
    id_field="thread_reply_id",      # 对应的 ID 字段
    platform="discord"               # 平台名称（可选）
)

# 使用自定义类型
convert_to_send_type("thread_reply", platform="discord")  # → "thread"
get_id_field("thread_reply", platform="discord")          # → "thread_reply_id"

# 注销自定义类型
unregister_custom_type("thread_reply", platform="discord")
```

> **指定 platform 时**，注册的接收类型会加上平台前缀（如 `discord_thread_reply`），避免不同平台之间的类型冲突。

## 工具方法

```python
from ErisPulse.Core.Event.session_type import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

# 检查是否为标准类型
is_standard_type("private")  # True
is_standard_type("custom_type")  # False

# 检查发送类型是否有效
is_valid_send_type("user")  # True
is_valid_send_type("invalid")  # False

# 获取所有标准类型
get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

# 清除自定义类型
clear_custom_types()                # 清除所有
clear_custom_types(platform="discord")  # 只清除指定平台的
```

## 相关文档

- [事件转换标准](../standards/event-conversion.md) - 事件转换规范
- [会话类型标准](../standards/session-types.md) - 会话类型正式定义
- [事件转换器实现](../../developer-guide/adapters/converter.md) - Converter 开发指南
