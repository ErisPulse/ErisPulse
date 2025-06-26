# ErisPulse Adapter 文档

## 简介
ErisPulse 的 Adapter 系统旨在为不同的通信协议提供统一事件处理机制。目前支持的主要适配器包括：

- **TelegramAdapter**
- **OneBotAdapter**
- **YunhuAdapter**

每个适配器都实现了标准化的事件映射、消息发送方法和生命周期管理。以下将详细介绍现有适配器的功能、支持的方法以及推荐的开发实践。

---

## 适配器功能概述

### 1. YunhuAdapter
YunhuAdapter 是基于云湖协议构建的适配器，整合了所有云湖功能模块，提供统一的事件处理和消息操作接口。

#### 支持的事件类型

| 官方事件命名                  | 映射名称       | 说明                     |
|-------------------------------|----------------|--------------------------|
| `message.receive.normal`      | `message`      | 普通消息                 |
| `message.receive.instruction` | `command`      | 指令消息                 |
| `bot.followed`                | `follow`       | 用户关注机器人           |
| `bot.unfollowed`              | `unfollow`     | 用户取消关注机器人       |
| `group.join`                  | `group_join`   | 用户加入群组             |
| `group.leave`                 | `group_leave`  | 用户离开群组             |
| `button.report.inline`        | `button_click` | 按钮点击事件             |
| `bot.shortcut.menu`           | `shortcut_menu`| 快捷菜单触发事件         |

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
await yunhu.Send.To("user", user_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str, buttons: List = None)`：发送纯文本消息，可选添加按钮。
- `.Html(html: str, buttons: List = None)`：发送HTML格式消息。
- `.Markdown(markdown: str, buttons: List = None)`：发送Markdown格式消息。
- `.Image(file: bytes, buttons: List = None)`：发送图片消息。
- `.Video(file: bytes, buttons: List = None)`：发送视频消息。
- `.File(file: bytes, buttons: List = None)`：发送文件消息。
- `.Batch(target_ids: List[str], message: str)`：批量发送消息。
- `.Edit(msg_id: str, text: str)`：编辑已有消息。
- `.Recall(msg_id: str)`：撤回消息。
- `.Board(board_type: str, content: str, **kwargs)`：发布公告看板。
- `.Stream(content_type: str, generator: AsyncGenerator)`：发送流式消息。

#### 按钮参数说明
`buttons` 参数是一个嵌套列表，表示按钮的布局和功能。每个按钮对象包含以下字段：

| 字段         | 类型   | 是否必填 | 说明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | 按钮上的文字                                                         |
| `actionType` | int    | 是       | 动作类型：<br>`1`: 跳转 URL<br>`2`: 复制<br>`3`: 点击汇报            |
| `url`        | string | 否       | 当 `actionType=1` 时使用，表示跳转的目标 URL                         |
| `value`      | string | 否       | 当 `actionType=2` 时，该值会复制到剪贴板<br>当 `actionType=3` 时，该值会发送给订阅端 |

示例：
```python
buttons = [
    [
        {"text": "复制", "actionType": 2, "value": "xxxx"},
        {"text": "点击跳转", "actionType": 1, "url": "http://www.baidu.com"}
    ]
]
await yunhu.Send.To("user", user_id).Text("带按钮的消息", buttons=buttons)
```

#### 数据格式示例
```json
{
    "version": "1.0",
    "header": {
        "eventId": "xxxxx",
        "eventTime": 1647735644000,
        "eventType": "message.receive.instruction"
    },
    "event": {
        "sender": {
            "senderId": "xxxxx",
            "senderType": "user",
            "senderUserLevel": "member",
            "senderNickname": "昵称"
        },
        "chat": {
            "chatId": "xxxxx",
            "chatType": "group"
        },
        "message": {
            "msgId": "xxxxxx",
            "parentId": "xxxx",
            "sendTime": 1647735644000,
            "chatId": "xxxxxxxx",
            "chatType": "group",
            "contentType": "text",
            "content": {
                "text": "早上好"
            },
            "commandId": 98,
            "commandName": "计算器"
        }
    }
}
```

#### 注意：`chat` 与 `sender` 的误区

##### 常见问题：

| 字段 | 含义 |
|------|------|
| `data.event.chatType` | 当前聊天类型（`user`/`bot` 或 `group`） |
| `data.event.sender.senderType` | 发送者类型（通常为 `user`） |
| `data.event.sender.senderId` | 发送者唯一 ID |

> **注意：**  
> - 使用 `chatType` 判断消息是私聊还是群聊  
> - 群聊使用 `chatId`，私聊使用 `senderId` 作为目标地址  
> - `senderType` 通常为 `"user"`，不能用于判断是否为群消息  

---

##### 示例代码：

```python
@sdk.adapter.Yunhu.on("message")
async def handle_message(data):
    if data.event.chatType == "group":
        targetId = data.event.chat.chatId
        targeType = "group"
    else:
        targetId = data.event.sender.senderId
        targeType = "user"

    await sdk.adapter.Yunhu.Send.To(targeType, targetId).Text("收到你的消息！")
```

---

### 2. TelegramAdapter
TelegramAdapter 是基于 Telegram Bot API 构建的适配器，支持多种消息类型和事件处理。

#### 支持的事件类型

| Telegram 原生事件       | 映射名称           | 说明                     |
|-------------------------|--------------------|--------------------------|
| `message`               | `message`          | 普通消息                 |
| `edited_message`        | `message_edit`     | 消息被编辑               |
| `channel_post`          | `channel_post`     | 频道发布消息             |
| `edited_channel_post`   | `channel_post_edit`| 频道消息被编辑           |
| `inline_query`          | `inline_query`     | 内联查询                 |
| `chosen_inline_result`  | `chosen_inline_result` | 内联结果被选择       |
| `callback_query`        | `callback_query`   | 回调查询（按钮点击）     |
| `shipping_query`        | `shipping_query`   | 配送信息查询             |
| `pre_checkout_query`    | `pre_checkout_query` | 支付预检查询           |
| `poll`                  | `poll`             | 投票创建                 |
| `poll_answer`           | `poll_answer`      | 投票响应                 |

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
await telegram.Send.To("user", user_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: bytes, caption: str = "")`：发送图片消息。
- `.Video(file: bytes, caption: str = "")`：发送视频消息。
- `.Audio(file: bytes, caption: str = "")`：发送音频消息。
- `.Document(file: bytes, caption: str = "")`：发送文件消息。
- `.EditMessageText(message_id: int, text: str)`：编辑已有消息。
- `.DeleteMessage(message_id: int)`：删除指定消息。
- `.GetChat()`：获取聊天信息。

#### 数据格式示例
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 101,
    "from": {
      "id": 123456789,
      "is_bot": false,
      "first_name": "John",
      "last_name": "Doe",
      "username": "johndoe",
      "language_code": "en"
    },
    "chat": {
      "id": 123456789,
      "first_name": "John",
      "last_name": "Doe",
      "username": "johndoe",
      "type": "private"
    },
    "date": 1672531199,
    "text": "Hello!"
  }
}
```

---

### 3. OneBotAdapter
OneBotAdapter 是基于 OneBot V11 协议构建的适配器，适用于与 go-cqhttp 等服务端交互。

#### 支持的事件类型

| OneBot 原生事件       | 映射名称           | 说明                     |
|-----------------------|--------------------|--------------------------|
| `message`             | `message`          | 消息事件                 |
| `notice`              | `notice`           | 通知类事件（如群成员变动）|
| `request`             | `request`          | 请求类事件（如加群请求） |
| `meta_event`          | `meta_event`       | 元事件（如心跳包）       |

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
await onebot.Send.To("group", group_id).Text("Hello World!")
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本消息。
- `.Image(file: str)`：发送图片消息（支持 URL 或 Base64）。
- `.Voice(file: str)`：发送语音消息。
- `.Video(file: str)`：发送视频消息。
- `.Raw(message_list: List[Dict])`：发送原生 OneBot 消息结构。
- `.Recall(message_id: int)`：撤回消息。
- `.Edit(message_id: int, new_text: str)`：编辑消息。
- `.Batch(target_ids: List[str], text: str)`：批量发送消息。

#### 数据格式示例
```json
{
  "post_type": "message",
  "message_type": "group",
  "group_id": 123456,
  "user_id": 987654321,
  "message": "Hello!",
  "raw_message": "Hello!",
  "time": 1672531199,
  "self_id": 123456789
}
```

---

## 生命周期管理

### 启动适配器
```python
await sdk.adapter.startup()
```
此方法会根据配置启动适配器，并初始化必要的连接。

### 关闭适配器
```python
await sdk.adapter.shutdown()
```
确保资源释放，关闭 WebSocket 连接或其他网络资源。

---

## 开发者指南

### 如何编写新的 Adapter
1. **继承 BaseAdapter**  
   所有适配器需继承 `sdk.BaseAdapter` 类，并实现以下方法：
   - `start()`：启动适配器。
   - `shutdown()`：关闭适配器。
   - `call_api(endpoint: str, **params)`：调用底层 API。

2. **定义 Send 方法**  
   使用链式语法实现消息发送逻辑，推荐参考现有适配器的实现。

3. **注册事件映射**  
   在 `_setup_event_mapping()` 方法中定义事件映射表。

4. **测试与调试**  
   编写单元测试验证适配器的功能完整性，并在不同环境下进行充分测试。

### 推荐的文档结构
新适配器的文档应包含以下内容：
- **简介**：适配器的功能和适用场景。
- **事件映射表**：列出支持的事件及其映射名称。
- **发送方法**：详细说明支持的消息类型和使用示例。
- **数据格式**：展示典型事件的 JSON 数据格式。
- **配置说明**：列出适配器所需的配置项及默认值。
- **注意事项**：列出开发和使用过程中需要注意的事项。

---

## 参考链接
ErisPulse 项目：
- [主库](https://github.com/ErisPulse/ErisPulse/)
- [ErisPulse Yunhu 适配器库](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [ErisPulse Telegram 适配器库](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [ErisPulse OneBot 适配器库](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

官方文档：
- [OneBot V11 协议文档](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 官方文档](https://core.telegram.org/bots/api)
- [云湖官方文档](https://www.yhchat.com/document/1-3)

---

## 参与贡献

我们欢迎更多开发者参与编写和维护适配器文档！请按照以下步骤提交贡献：
1. Fork [ErisPuls](https://github.com/ErisPulse/ErisPulse) 仓库。
2. 在 `docs/` 目录下找到 ADAPTER.md 适配器文档。
3. 提交 Pull Request，并附上详细的描述。

感谢您的支持！
