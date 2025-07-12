# ErisPulse 跨平台事件转换标准文档
## 1. 标准概述
ErisPulse 事件转换标准定义了如何将不同聊天平台的原生事件转换为统一的 OneBot12 兼容格式。本标准确保：
1. 跨平台兼容性：不同平台的事件可以转换为统一格式
2. 可扩展性：支持平台特有字段和功能
3. 一致性：所有适配器遵循相同的转换规则

## 2. 基础字段映射
### 2.1 必填字段
|标准字段|必填|描述|示例|
|-|-|-|-|
|id|是|事件唯一ID|"1234567890"|
|time|是|事件时间戳(秒)|1620000000|
|type|是|事件主类型|"message"|
|platform|是|来源平台标识|"telegram"|
|self|是|机器人自身信息|{"platform": "xx", "user_id": "123"}|

### 2.2 可选字段
|标准字段|描述|条件|
|-|-|-|
|detail_type|事件子类型|根据事件类型需要|
|sub_type|事件三级类型|根据detail_type需要|
|user_id|用户ID|涉及用户的事件|
|group_id|群组ID|群组相关事件|
|message_id|消息ID|消息相关事件|

## 3. 事件类型映射
### 3.1 通用事件类型
|标准类型|detail_type|描述|
|-|-|-|
|message|private|私聊消息|
|message|group|群聊消息|
|notice|friend_increase|好友增加|
|notice|friend_decrease|好友减少|
|notice|group_member_increase|群成员增加|
|notice|group_member_decrease|群成员减少|
|request|friend|好友请求|
|request|group|加群请求|

### 3.2 平台特有事件
平台特有事件应使用 {platform}_ 前缀：
```json
{
  "type": "notice",
  "detail_type": "platform_button_click",
  "platform_button": {
    "id": "btn_123",
    "data": "value"
  }
}
```
## 4. 消息段格式
### 4.1 通用消息段
```json
{
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Hello"
      }
    },
    {
      "type": "image",
      "data": {
        "url": "http://example.com/image.jpg",
        "file_name": "example.jpg"
      }
    }
  ]
}
```
### 4.2 支持的消息类型
|类型|字段要求|示例|
|-|-|-|
|text|text: string|{"type":"text","data":{"text":"hi"}}|
|image|url: string, file_name?: string|{"type":"image","data":{"url":"...","file_name":"img.jpg"}}|
|video|url: string, duration?: number|{"type":"video","data":{"url":"...","duration":60}}|
|file|url: string, size?: number|{"type":"file","data":{"url":"...","size":1024}}|

### 4.3 平台特有消息段
```json
{
  "message": [
    {
      "type": "platform_form",
      "data": {
        "id": "form_123",
        "fields": [...]
      }
    }
  ]
}
```

## 5. 错误处理规范
### 5.1 字段缺失处理
```python
# 伪代码示例
event_id = raw_event.get("id", str(uuid.uuid4()))  # 生成默认值
if "id" not in raw_event:
    logger.warning("Missing required field: id")
```
### 5.2 未知事件类型
```json
{
  "type": "unknown",
  "platform": "example",
  "example_raw": { /* 原始事件数据 */ }
}
```
## 6. 实施指南
### 6.1 转换器结构
```python
class PlatformConverter:
    def __init__(self):
        self.platform = "platform_name"
    
    def convert(self, raw_event: dict) -> dict:
        """主转换方法"""
        # 1. 基础字段映射
        # 2. 根据类型分发处理
        # 3. 返回标准格式事件
```
### 6.2 测试要求
必须测试：
1. 所有标准事件类型的转换
2. 平台特有事件的转换
3. 字段缺失的容错处理
4. 消息段的正确解析
## 7. 示例
### 7.1 标准消息事件
输入示例:
```json
{
  "eventType": "message.receive.normal",
  "chatType": "group",
  "message": {
    "contentType": "text",
    "content": {"text": "Hello"}
  },
  "sender": {"id": "user123"}
}
```
转换后:
```json
{
  "id": "event123",
  "time": 1620000000,
  "type": "message",
  "detail_type": "group",
  "platform": "example",
  "self": {"platform": "example", "user_id": "bot123"},
  "group_id": "group123",
  "user_id": "user123",
  "message": [
    {
      "type": "text",
      "data": {"text": "Hello"}
    }
  ]
}
```
### 7.2 平台特有功能
输入示例 (云湖的表单指令):
```json
{
  "eventType": "message.receive.instruction",
  "formData": {
    "id": "form_123",
    "fields": [...]
  }
}
```

转换后:
```json
{
  "id": "event456",
  "time": 1620000001,
  "type": "notice",
  "detail_type": "yunhu_form",
  "platform": "example",
  "self": {"platform": "example", "user_id": "bot123"},
  "example_form": {
    "id": "form_123",
    "fields": [...]
  }
}
```

## 8. 平台适配建议
1. 字段前缀：所有平台特有字段必须添加 {platform}_ 前缀
2. 文档要求：适配器文档必须包含：
    - 支持的事件类型映射表
    - 特有字段的详细说明
    - 已知限制和兼容性说明
3. 版本控制：当平台API更新时，应更新转换器版本号

## 9. 时间戳处理
所有时间字段必须转换为10位Unix时间戳（秒级）：
```python
# 毫秒转秒示例
timestamp = int(raw_event["time"]) // 1000
```
