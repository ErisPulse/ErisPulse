# 事件转换器实现指南

事件转换器 (Converter) 是适配器的核心组件之一，负责将平台原生事件转换为 ErisPulse 统一的 OneBot12 标准事件格式。

## Converter 职责

```
平台原生事件 ──→ Converter.convert() ──→ OneBot12 标准事件
```

Converter 只负责**正向转换**（接收方向），即将平台的原生事件数据转换为 OneBot12 标准格式。反向转换（发送方向）由 `Send.Raw_ob12()` 方法处理。

### 核心原则

1. **无损转换**：原始数据必须完整保留在 `{platform}_raw` 字段中
2. **标准兼容**：转换后的事件必须符合 OneBot12 标准格式
3. **平台扩展**：平台特有数据使用 `{platform}_` 前缀字段存储

## convert() 方法

### 方法签名

```python
def convert(self, raw_event: dict) -> dict:
    """
    将平台原生事件转换为 OneBot12 标准格式

    :param raw_event: 平台原生事件数据
    :return: OneBot12 标准格式事件字典
    """
    pass
```

### 返回值结构

转换后的事件字典应包含以下标准字段：

```python
{
    "id": "事件唯一ID",
    "time": 1234567890,           # Unix 时间戳（秒）
    "type": "message",             # 事件类型
    "detail_type": "private",      # 详细类型
    "platform": "myplatform",      # 平台名称
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # 消息事件字段
    "user_id": "sender_id",
    "message": [...],              # OneBot12 消息段列表
    "alt_message": "纯文本内容",

    # 必须保留原始数据
    "myplatform_raw": { ... },     # 平台原生事件完整数据
    "myplatform_raw_type": "原生事件类型名",
}
```

## 必填字段映射

### 通用字段（所有事件类型）

| OB12 字段 | 类型 | 说明 |
|-----------|------|------|
| `id` | str | 事件唯一标识符 |
| `time` | int | Unix 时间戳（秒） |
| `type` | str | 事件类型：`message` / `notice` / `request` / `meta` |
| `detail_type` | str | 详细类型：`private` / `group` / `friend` 等 |
| `platform` | str | 平台名称，与适配器注册名一致 |
| `self` | dict | 机器人信息：`{"platform": "...", "user_id": "..."}` |

### 消息事件额外字段

| OB12 字段 | 类型 | 说明 |
|-----------|------|------|
| `user_id` | str | 发送者 ID |
| `message` | list[dict] | OneBot12 消息段列表 |
| `alt_message` | str | 纯文本备用内容 |

### 通知事件额外字段

| OB12 字段 | 类型 | 说明 |
|-----------|------|------|
| `user_id` | str | 相关用户 ID |
| `operator_id` | str | 操作者 ID（如群成员变动） |

## 消息段转换

OneBot12 标准定义了以下消息段类型：

```python
# 文本
{"type": "text", "data": {"text": "Hello"}}

# 图片
{"type": "image", "data": {"file": "https://example.com/img.jpg"}}

# 音频
{"type": "audio", "data": {"file": "https://example.com/audio.mp3"}}

# 视频
{"type": "video", "data": {"file": "https://example.com/video.mp4"}}

# 文件
{"type": "file", "data": {"file": "https://example.com/doc.pdf"}}

# @提及
{"type": "mention", "data": {"user_id": "123"}}

# @全体
{"type": "mention_all", "data": {}}

# 回复
{"type": "reply", "data": {"message_id": "msg_123"}}
```

如果平台有不支持的消息段类型，可以省略该段或转换为最接近的标准类型。

## 平台扩展字段

平台特有的数据应使用 `{platform}_` 前缀存储，避免与标准字段冲突：

```python
{
    # 标准字段
    "type": "message",
    "detail_type": "group",
    # ...

    # 平台扩展字段
    "myplatform_raw": { ... },          # 原始事件数据（必须）
    "myplatform_raw_type": "chat",      # 原始事件类型（必须）

    # 其他平台特有字段
    "myplatform_group_name": "群名称",
    "myplatform_sender_role": "admin",
}
```

> **重要**：`{platform}_raw` 字段是必须的，ErisPulse 的事件系统和模块可能依赖它来访问平台原始数据。

## 完整示例

以下是一个完整的 Converter 实现：

```python
class MyConverter:
    def __init__(self, platform: str):
        self.platform = platform

    def convert(self, raw_event: dict) -> dict:
        event_type = raw_event.get("type", "")

        base_event = {
            "id": raw_event.get("id", ""),
            "time": raw_event.get("timestamp", 0),
            "platform": self.platform,
            "self": {
                "platform": self.platform,
                "user_id": raw_event.get("self_id", ""),
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": event_type,
        }

        if event_type == "chat":
            return self._convert_message(raw_event, base_event)
        elif event_type == "notification":
            return self._convert_notice(raw_event, base_event)
        elif event_type == "request":
            return self._convert_request(raw_event, base_event)

        return base_event

    def _convert_message(self, raw: dict, base: dict) -> dict:
        base["type"] = "message"
        base["detail_type"] = "group" if raw.get("group_id") else "private"
        base["user_id"] = raw.get("sender_id", "")
        base["message"] = self._convert_message_segments(raw.get("content", ""))
        base["alt_message"] = raw.get("content", "")

        if raw.get("group_id"):
            base["group_id"] = raw["group_id"]

        return base

    def _convert_message_segments(self, content: str) -> list:
        segments = []
        if content:
            segments.append({"type": "text", "data": {"text": content}})
        return segments

    def _convert_notice(self, raw: dict, base: dict) -> dict:
        base["type"] = "notice"
        notification_type = raw.get("notification_type", "")

        if notification_type == "member_join":
            base["detail_type"] = "group_member_increase"
            base["user_id"] = raw.get("user_id", "")
            base["group_id"] = raw.get("group_id", "")
            base["operator_id"] = raw.get("operator_id", "")
        elif notification_type == "friend_add":
            base["detail_type"] = "friend_increase"
            base["user_id"] = raw.get("user_id", "")

        return base

    def _convert_request(self, raw: dict, base: dict) -> dict:
        base["type"] = "request"
        request_type = raw.get("request_type", "")

        if request_type == "friend":
            base["detail_type"] = "friend"
            base["user_id"] = raw.get("user_id", "")
            base["comment"] = raw.get("message", "")
        elif request_type == "group_invite":
            base["detail_type"] = "group"
            base["group_id"] = raw.get("group_id", "")
            base["user_id"] = raw.get("inviter_id", "")

        return base
```

## 最佳实践

1. **总是保留原始数据**：`{platform}_raw` 字段不能省略
2. **使用标准消息段**：尽量将平台消息转换为 OneBot12 标准消息段
3. **合理设置 detail_type**：使用标准类型（`private`/`group`/`channel` 等），不要自定义
4. **处理边界情况**：原始事件可能缺少某些字段，使用 `.get()` 并提供合理默认值
5. **性能考虑**：`convert()` 在每个事件上调用，避免在其中执行耗时操作

## 相关文档

- [适配器核心概念](core-concepts.md) - 适配器整体架构
- [SendDSL 详解](send-dsl.md) - 反向转换（发送方向）
- [事件转换标准](../../standards/event-conversion.md) - 正式的事件转换规范
- [会话类型系统](../../advanced/session-types.md) - 会话类型映射规则
