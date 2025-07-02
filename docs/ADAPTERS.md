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

#### env.py 配置示例
```python
sdk.env.set("YunhuAdapter", {
    "token": "",       # 机器人 Token
    "mode": "server",  # server / polling (polling使用社区脚本支持)
    "server": {
        "host": "0.0.0.0",
        "port": 25888,
        "path": "/yunhu/webhook"
    },
    "polling": {
        "url": "https://example.com/",
    }
})
```
> **注意：**
> - 云湖适配器使用 `server` 模式时，需要配置 `server` 字段；使用 `polling` 模式时，需要配置 `polling` 字段。
> - 云湖需要在控制台指向我们开启的 `server` 地址，否则无法正常接收消息。

#### 数据格式示例
云湖目前有9种事件会推送给机器人：

|事件字段名称|事件用途|
|:---:|:---:|
|message.receive.normal|普通消息|
|message.receive.instruction|指令消息|
|group.join|用户加群|
|group.leave|用户退群|
|bot.followed|机器人关注|
|bot.unfollowed|机器人取关|
|bot.shortcut.menu|快捷菜单|
|button.report.inline|按钮汇报|
|bot.setting|机器人设置|

每个事件的触发条件以及数据结构如下：

##### 普通消息事件
当用户向机器人或机器人所在的群聊发送消息，且没有选择指令时，将会触发该事件。
```json
{
  "version": "1.0",
  "header": 
    "eventId": "c192ccc83d5147f2859ca77bcfafc9f9",
    "eventType": "message.receive.normal",
    "eventTime": 1748613099002
  }
  "event": {
    "sender": 
      "senderId": "6300451",
      "senderType": "user",
      "senderUserLevel": "owner",
      "senderNickname": "ShanFish"
    },
    "chat": {
      "chatId": "49871624",
      "chatType": "bot"
    },
    "message": {
      "msgId": "5c887bc0a82244c7969c08000f5b3ae8",
      "parentId": "",
      "sendTime": 1748613098989,
      "chatId": "49871624",
      "chatType": "bot",
      "contentType": "text",
      "content": {
        "text": "你好"
      },
      "instructionId": 0,
      "instructionName": "",
      "commandId": 0,
      "comandName": ""
    }
  }
}
```
##### 指令消息事件
当用户点击聊天栏的"/"图标时，将列出该机器人/群聊可用的所有指令。用户发送带有指令的消息后，将会触发该事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "ee74aded326b4578959073fe88f0076a",
        "eventType": "message.receive.instruction",
        "eventTime": 1749442433069
    },
    "event": {
        "sender": {
            "senderId": "6300451",
            "senderType": "user",
            "senderUserLevel": "owner",
            "senderNickname": "ShanFish"
        },
        "chat": {
            "chatId": "49871624",
            "chatType": "bot"
        },
        "message": {
            "msgId": "1d879c6ec68c4c52b78f87d83084955e",
            "parentId": "",
            "sendTime": 1749442433057,
            "chatId": "49871624",
            "chatType": "bot",
            "contentType": "text",
            "content": {
                "text": "/抽奖信息",
                "menu": {}
            },
            "instructionId": 1505,
            "instructionName": "抽奖信息",
            "commandId": 1505,
            "commandName": "抽奖信息"
        }
    }
}
```
##### 用户加群事件
当用户加入机器人所在的群聊后，将会触发该事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "d5429cb5e4654fbcaeee9e4adb244741",
        "eventType": "group.join",
        "eventTime": 1749442891943
    },
    "event": {
        "time": 1749442891843,
        "chatId": "985140593",
        "chatType": "group",
        "userId": "3707697",
        "nickname": "ShanFishApp",
        "avatarUrl": "https://chat-storage1.jwznb.com/defalut-avatars/Ma%20Rainey.png?sign=b19c8978f4e0d9e43a8aec4f1e3c82ef&t=68466f5b"
    }
}
```
##### 用户退群事件
```json
{
    "version": "1.0",
    "header": {
        "eventId": "06959e95aaf547078367104ba754c554",
        "eventType": "group.leave",
        "eventTime": 1749442644367
    },
    "event": {
        "time": 1749442644343,
        "chatId": "985140593",
        "chatType": "group",
        "userId": "3707697",
        "nickname": "ShanFishApp",
        "avatarUrl": "https://chat-storage1.jwznb.com/defalut-avatars/Ma%20Rainey.png?sign=92fdef22a240a05de78b13afdab5ac51&t=68466e64"
    }
}
```
##### 用户关注机器人事件
当用户在机器人ID或机器人推荐处添加机器人后，将会触发该事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "3fe280a400f9460daa03a642d1fad39b",
        "eventType": "bot.followed",
        "eventTime": 1749443049592
    },
    "event": {
        "time": 1749443049580,
        "chatId": "49871624",
        "chatType": "bot",
        "userId": "3707697",
        "nickname": "ShanFishApp",
        "avatarUrl": "https://chat-storage1.jwznb.com/defalut-avatars/Ma%20Rainey.png?sign=33bb173f1b22ed0e44da048b175767c6&t=68466ff9"
    }
}
```
##### 用户取关机器人事件
当用户点击删除机器人按钮后，将会触发该事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "b4f51386d916464b99782052c030c5b7",
        "eventType": "bot.unfollowed",
        "eventTime": 1749443036382
    },
    "event": {
        "time": 1749443036373,
        "chatId": "49871624",
        "chatType": "bot",
        "userId": "3707697",
        "nickname": "ShanFishApp",
        "avatarUrl": "https://chat-storage1.jwznb.com/defalut-avatars/Ma%20Rainey.png?sign=07cf8e9d6ca0875835f9a4a6811b6b4c&t=68466fec"
    }
}
```
##### 按钮汇报事件
机器人可以发送带按钮的消息。当用户按下按钮actionType为3(汇报类按钮)的按钮时，将会触发该事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "0d6d269ff7f046828c8562f905f9ee08",
        "eventType": "button.report.inline",
        "eventTime": 1749446185273
    },
    "event": {
        "time": 1749446185268,
        "msgId": "1838c3dd84474e9e9e1e00ca64e72065",
        "recvId": "6300451",
        "recvType": "user",
        "userId": "6300451",
        "value": "xxxx"
    }
}
```

##### 快捷菜单事件
当用户点击了开发者自行配置的快捷菜单时，且该快捷菜单类型为普通菜单，将会触发本事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "93d0e36ce0334da58448409fd0527590",
        "eventType": "bot.shortcut.menu",
        "eventTime": 1749445822197
    },
    "event": {
        "botId": "49871624",
        "menuId": "HNH1LDHF",
        "menuType": 1,
        "menuAction": 1,
        "chatId": "985140593",
        "chatType": "group",
        "senderType": "user",
        "senderId": "6300451",
        "sendTime": 1749445822
    }
}

```
##### 机器人设置事件
当开发者配置了机器人设置项时，在机器人列表处将会出现"设置"按钮。用户设置完成后，将会触发本事件。
```json
{
    "version": "1.0",
    "header": {
        "eventId": "5ad7e23399ef46a685cead1abe2efa19",
        "eventType": "bot.setting",
        "eventTime": 1749446299131
    },
    "event": {
        "time": 1749446299128,
        "chatId": "49871624",
        "chatType": "bot",
        "groupId": "985140593",
        "groupName": "云湖测试群",
        "avatarUrl": "https://chat-img.jwznb.com/77db590d9cee77de13e7c8cf0887b5ba.jpg",
        "settingJson": {
            "wezzrm": {
                "id": "wezzrm",
                "type": "switch",
                "label": "测试",
                "value": true
            }
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

#### env.py 配置示例
```python
sdk.env.set("TelegramAdapter", {
    # 必填：Telegram Bot Token
    "token": "YOUR_BOT_TOKEN",

    # Webhook 模式下的服务配置（如使用 webhook）
    "server": {
        "host": "127.0.0.1",            # 推荐监听本地，防止外网直连
        "port": 8443,                   # 监听端口
        "path": "/telegram/webhook"     # Webhook 路径
    },
    "webhook": {
        "host": "example.com",          # Telegram API 监听地址（外部地址）
        "port": 8443,                   # 监听端口
        "path": "/telegram/webhook"     # Webhook 路径
    }

    # 启动模式: webhook 或 polling
    "mode": "webhook",

    # 可选：代理配置（用于连接 Telegram API）
    "proxy": {
        "host": "127.0.0.1",
        "port": 1080,
        "type": "socks5"  # 支持 socks4 / socks5
    }
})
```

#### 数据格式示例
> 略: 使用你了解的 TG 事件数据格式即可,这里不进行演示

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

#### env.py 配置示例
```python
sdk.env.set("OneBotAdapter", {
    "mode": "client", # 或者 "server"
    "server": {
        "host": "127.0.0.1",
        "port": 8080,
        "path": "/",
        "token": ""
    },
    "client": {
        "url": "ws://127.0.0.1:3001",
        "token": ""
    }
})
```

#### 数据格式示例
> 略: 使用你了解的 OneBot v11 事件数据格式即可,这里不进行演示

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