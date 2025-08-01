# ErisPulse 核心功能文档

本文件由多个开发文档合并而成，用于辅助 AI 理解 ErisPulse 的相关功能。

## 各文件对应内容说明

| 文件名 | 作用 |
|--------|------|
| quick-start.md | 快速开始指南 |
| UseCore.md | 核心功能使用说明 |
| PlatformFeatures.md | 平台功能说明 |

## 合并内容开始

<!-- quick-start.md -->

# 快速开始

## 安装ErisPulse

### 使用 pip 安装
确保你的 Python 版本 >= 3.8，然后使用 pip 安装 ErisPulse：
```bash
pip install ErisPulse
```

### 更先进的安装方法
> 采用 [`uv`](https://github.com/astral-sh/uv) 作为 Python 工具链

### 1. 安装 uv

#### 通用方法 (pip):
```bash
pip install uv
```

#### macOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

验证安装:
```bash
uv --version
```

### 2. 创建虚拟环境,并安装 ErisPulse

```bash
uv python install 3.12              # 安装 Python 3.12
uv venv                             # 创建虚拟环境
source .venv/bin/activate           # 激活环境 (Windows: .venv\Scripts\activate)
uv pip install ErisPulse --upgrade  # 安装框架
```

---

## 初始化项目

1. 创建项目目录并进入：

```bash
mkdir my_bot && cd my_bot
```

2. 初始化 SDK 并生成配置文件：

```bsah
ep-init
```
这将在当前目录下生成 `config.yml` 和 `main.py` 入口。

---

## 安装模块

你可以通过 CLI 安装所需模块：

```bash
epsdk install Yunhu AIChat
```

你也可以手动编写模块逻辑，参考开发者文档进行模块开发。

---

## 运行你的机器人
运行我们自动生成的程序入口：
```bash
epsdk run main.py
```

或者使用热重载模式（开发时推荐）：

```bash
epsdk run main.py --reload
```


<!--- End of quick-start.md -->

<!-- UseCore.md -->

# ErisPulse 核心模块使用指南

## 核心模块
| 名称 | 用途 |
|------|------|
| `sdk` | SDK对象 |
| `env`/`sdk.env` | 获取/设置数据库配置 |
| `config`/`sdk.config` | 获取/设置模块配置 |
| `mods`/`sdk.mods` | 模块管理器 |
| `adapter`/`sdk.adapter` | 适配器管理/获取实例 |
| `logger`/`sdk.logger` | 日志记录器 |
| `BaseAdapter`/`sdk.BaseAdapter` | 适配器基类 |

```python
# 直接导入方式
from ErisPulse.Core import env, mods, logger, adapter, BaseAdapter

# 通过SDK对象方式
from ErisPulse import sdk
sdk.env  # 等同于直接导入的env
```

## 模块使用
- 所有模块通过`sdk`对象统一管理
- 每个模块拥有独立命名空间，使用`sdk`进行调用
- 可以在模块间使用 `sdk.<module_name>.<func>` 的方式调用其他模块中的方法

## 适配器使用
- 适配器是ErisPulse的核心，负责与平台进行交互

适配器事件分为两类：
- 标准事件：平台转换为的标准事件，其格式为标准的 OneBot12 事件格式 | 需要判断接收到的消息的 `platform` 字段，来确定消息来自哪个平台
- 原生事件：平台原生事件 通过 sdk.adapter.<Adapter>.on() 监听对应平台的原生事件
适配器标准事件的拓展以及支持的消息发送类型，请参考 [PlatformFeatures.md](docs/PlatformFeatures.md)

建议使用标准事件进行事件的处理，适配器会自动将原生事件转换为标准事件

```python
# 启动适配器
await sdk.adapter.startup("MyAdapter")  # 不指定名称则启动所有适配器
# 另外可以传入列表，例如 sdk.adapter.startup(["Telegram", "Yunhu"])

# 监听 OneBot12 标准事件
@adapter.on("message")
async def on_message(data):
    platform = data.get("platform")
    detail_type = "user" if data.get("detail_type") == "private" else "group"
    detail_id = data.get("user_id") if detail_type == "user" else data.get("group_id")
    Sender = None

    if hasattr(adapter, platform):
        Sender = getattr(adapter, platform).To(detail_type, detail_id)
    
    Sender.Text(data.get("alt_message"))

# 监听平台原生事件
@adapter.Telegram.on("message")
async def on_raw_message(data):
    # Do something ...
```
平台原生事件监听并不建议使用，因为格式不保证与 OneBot12 兼容，另外 OneBot12 的标准事件规定了一个拓展字段 `{{platform}}_raw` 用于传输平台原生数据

## 核心模块功能详解

### 1. 日志模块(logger)
```python
logger.set_module_level("MyModule", "DEBUG")  # 设置模块日志级别
logger.save_logs("log.txt")  # 保存日志到文件

# 日志级别
logger.debug("调试信息")
logger.info("运行状态")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("致命错误")  # 会触发程序崩溃
```

### 2. 环境配置(env)
```python
# 数据库配置操作
env.set("key", "value")  # 设置配置项
value = env.get("key", "default")  # 获取配置项
env.delete("key")  # 删除配置项

# 事务操作
with env.transaction():
    env.set('important_key', 'value')
    env.delete('temp_key')  # 异常时自动回滚
```

### 3. 配置模块(config)
```python
# 模块配置操作（读写config.toml）
module_config = config.getConfig("MyModule")  # 获取模块配置
if module_config is None:
    config.setConfig("MyModule", {"MyKey": "MyValue"})  # 设置默认配置
```

### 4. 异常处理模块(exceptions)
```python
# ErisPulse提供了统一的异常处理机制，可以自动捕获和格式化异常信息
# 对于异步代码，可以为特定事件循环设置异常处理器

import asyncio
from ErisPulse.Core import exceptions

# 为当前运行的事件循环设置异常处理器
loop = asyncio.get_running_loop()
exceptions.setup_async_loop(loop)

# 或者不传参数，自动获取当前事件循环 || 但不建议这么做，因为运行主程序时可能使用了其他的异步库
exceptions.setup_async_loop()

# 这样设置后，异步代码中的未捕获异常会被统一处理并格式化输出
```

### 建议
1. 模块配置应使用`getConfig/setConfig`操作config.toml
2. 持久信息存储使用`get/set`操作数据库
3. 关键操作使用事务保证原子性
4. 对于自定义事件循环，使用`exceptions.setup_async_loop()`方法确保异常被正确处理
> 其中，1-2 步骤可以实现配合，比如硬配置让用户设置后，和数据库中的配置进行合并，实现配置的动态更新

更多详细信息请参考[API文档](docs/api/)


<!--- End of UseCore.md -->

<!-- PlatformFeatures.md -->

# ErisPulse PlatformFeatures 文档
> 基线协议：(OneBot12)[https://12.onebot.dev/] 
> 
> 本文档为**快速使用指南**，包含：
> - 通用接口使用方法
> - 各适配器支持的Send方法链式调用示例
> - 平台特有的事件/消息格式说明
> 
> 正式适配器开发请参考：
> - [适配器开发指南](docs/Development/Adapter.md)
> - [事件转换标准](docs/AdapterStandards/event-conversion.md)  
> - [API响应规范](docs/AdapterStandards/api-response.md)

---

## 通用接口

### Send 链式调用
所有适配器都支持以下标准调用方式：

1. 指定类型和ID: `To(type,id).Func()`
   ```python
   await adapter.AdapterName.Send.To("user", "U1001").Text("Hello")
   ```
2. 仅指定ID: `To(id).Func()`
   ```python
   await adapter.AdapterName.Send.To("U1001").Text("Hello")
   ```
3. 指定发送账号: `Using(account_id)`
   ```python
   await adapter.AdapterName.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接调用: `Func()`
   ```python
   await adapter.AdapterName.Send.Text("Broadcast message")
   ```

### 事件监听
有两种事件监听方式：

1. 平台原生事件监听：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.AdapterName.on("event_type")
   async def handler(data):
       logger.info(f"收到原生事件: {data}")
   ```

2. OneBot12标准事件监听：
   ```python
   from ErisPulse.Core import adapter, logger

   @adapter.on("event_type")  # 所有平台的标准事件
   async def handler(data):
       if data["platform"] == "yunhu":
           logger.info(f"收到云湖标准事件: {data}")
   ```

---

## 标准格式
为方便参考，这里给出了简单的事件格式，如果需要详细信息，请参考上方的链接。

### 标准事件格式
所有适配器必须实现的事件转换格式：
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {"platform": "yunhu", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789"
}
```

### 标准响应格式
#### 消息发送成功
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### 消息发送失败
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "缺少必要参数",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

### 1. YunhuAdapter
YunhuAdapter 是基于云湖协议构建的适配器，整合了所有云湖功能模块，提供统一的事件处理和消息操作接口。

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

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

Borard board_type 支持以下类型：
- `local`：指定用户看板
- `global`：全局看板

##### 按钮参数说明
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
        {"text": "点击跳转", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "汇报事件", "actionType": 3, "value", "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Text("带按钮的消息", buttons=buttons)
```
> **注意：**
> - 只有用户点击了**按钮汇报事件**的按钮才会收到推送，**复制***和**跳转URL**均无法收到推送。

#### OneBot12协议转换说明
云湖事件转换到OneBot12协议，其中标准字段完全遵守OneBot12协议，但存在一些差异，你需要阅读以下内容：
需要 platform=="yunhu" 检测再使用本平台特性

##### 核心差异点
1. 特有事件类型：
    - 表单（如表单指令）：yunhu_form
    - 按钮点击：yunhu_button_click
    - 机器人设置：yunhu_bot_setting
    - 快捷菜单：yunhu_shortcut_menu
2. 扩展字段：
    - 所有特有字段均以yunhu_前缀标识
    - 保留原始数据在yunhu_raw字段
    - 私聊中self.user_id表示机器人ID

3. 特殊字段示例：
```python
# 表单命令
{
  "type": "yunhu_form",
  "data": {
    "id": "1766",
    "name": "123123",
    "fields": [
      {
        "id": "abgapt",
        "type": "textarea",
        "value": ""
      },
      {
        "id": "mnabyo", 
        "type": "select",
        "value": ""
      }
    ]
  },
  "yunhu_command": {
    "name": "123123",
    "id": "1766",
    "form": {
      "abgapt": {
        "id": "abgapt",
        "type": "textarea",
        "value": ""
      },
      "mnabyo": {
        "id": "mnabyo",
        "type": "select",
        "value": ""
      }
    }
  }
}

# 按钮事件
{
  "detail_type": "yunhu_button_click",
  "yunhu_button": {
    "id": "",
    "value": "test_button_value"
  }
}

# 机器人设置
{
  "detail_type": "yunhu_bot_setting",
  "yunhu_setting": {
    "lokola": {
      "id": "lokola",
      "type": "radio",
      "value": ""
    },
    "ngcezg": {
      "id": "ngcezg",
      "type": "input",
      "value": null
    }
  }
}

# 快捷菜单
{
  "detail_type": "yunhu_shortcut_menu", 
  "yunhu_menu": {
    "id": "B4X00M5B",
    "type": 1,
    "action": 1
  }
}
```

---

### 2. TelegramAdapter
TelegramAdapter 是基于 Telegram Bot API 构建的适配器，支持多种消息类型和事件处理。

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

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
> 略: 使用你了解的 TG 事件数据格式即可,这里不进行演示

#### OneBot12协议转换说明
Telegram事件转换到OneBot12协议，其中标准字段完全遵守OneBot12协议，但存在以下差异：

##### 核心差异点
1. 特有事件类型：
   - 内联查询：telegram_inline_query
   - 回调查询：telegram_callback_query
   - 投票事件：telegram_poll
   - 投票答案：telegram_poll_answer

2. 扩展字段：
   - 所有特有字段均以telegram_前缀标识
   - 保留原始数据在telegram_raw字段
   - 频道消息使用detail_type="channel"

3. 特殊字段示例：
```python
# 回调查询事件
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback": {
    "id": "cb_123",
    "data": "callback_data",
    "message_id": "msg_456"
  }
}

# 内联查询事件
{
  "type": "notice",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_inline": {
    "id": "iq_789",
    "query": "search_text",
    "offset": "0"
  }
}

# 频道消息
{
  "type": "message",
  "detail_type": "channel",
  "message_id": "msg_345",
  "channel_id": "channel_123",
  "telegram_channel": {
    "title": "News Channel",
    "username": "news_official"
  }
}
```

---

### 3. OneBot11Adapter
OneBot11Adapter 是基于 OneBot V11 协议构建的适配器。

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

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
> 略: 使用你了解的 OneBot v11 事件数据格式即可,这里不进行演示
#### OneBot12协议转换说明
OneBot11事件转换到OneBot12协议，其中标准字段完全遵守OneBot12协议，但存在以下差异：

##### 核心差异点
1. 特有事件类型：
   - CQ码扩展事件：onebot11_cq_{type}
   - 荣誉变更事件：onebot11_honor
   - 戳一戳事件：onebot11_poke

2. 扩展字段：
   - 所有特有字段均以onebot11_前缀标识
   - 保留原始CQ码消息在onebot11_raw_message字段
   - 保留原始事件数据在onebot11_raw字段

3. 特殊字段示例：
```python
# 荣誉变更事件
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "onebot11_honor_type": "talkative",
  "onebot11_operation": "set"
}

# 戳一戳事件
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678",
  "onebot11_poke_type": "normal"
}

# CQ码消息段
{
  "type": "message",
  "message": [
    {
      "type": "onebot11_face",
      "data": {"id": "123"}
    },
    {
      "type": "onebot11_shake",
      "data": {} 
    }
  ]
}
```

---

### 4. MailAdapter
MailAdapter 是基于SMTP/IMAP协议的邮件适配器，支持邮件发送、接收和处理。

#### 支持的消息发送类型
所有发送方法均通过链式语法实现，例如：
```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# 简单文本邮件
await mail.Send.Using("from@example.com").To("to@example.com").Subject("测试").Text("内容")

# 带附件的HTML邮件
await mail.Send.Using("from@example.com") \
    .To("to@example.com") \
    .Subject("HTML邮件") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML内容</h1>")

# 注意：使用链式语法时，参数方法必须在发送方法（Text，Html）之前设置
```

支持的发送类型包括：
- `.Text(text: str)`：发送纯文本邮件
- `.Html(html: str)`：发送HTML格式邮件
- `.Attachment(file: str, filename: str = None)`：添加附件
- `.Cc(emails: Union[str, List[str]])`：设置抄送
- `.Bcc(emails: Union[str, List[str]])`：设置密送
- `.ReplyTo(email: str)`：设置回复地址

#### 特有参数说明
| 参数       | 类型               | 说明                          |
|------------|--------------------|-----------------------------|
| Subject    | str                | 邮件主题                      |
| From       | str                | 发件人地址(通过Using设置)      |
| To         | str                | 收件人地址                    |
| Cc         | str 或 List[str]   | 抄送地址列表                  |
| Bcc        | str 或 List[str]   | 密送地址列表                  |
| Attachment | str 或 Path        | 附件文件路径                 |

#### 事件格式
邮件接收事件格式：
```python
{
  "type": "message",
  "detail_type": "private",  # 邮件默认为私聊
  "platform": "email",
  "self": {"platform": "email", "user_id": account_id},
  "message": [
    {
      "type": "text",
      "data": {
        "text": f"Subject: {subject}\nFrom: {from_}\n\n{text_content}"
      }
    }
  ],
  "email_raw": {
    "subject": subject,
    "from": from_,
    "to": to,
    "date": date,
    "text_content": text_content,
    "html_content": html_content,
    "attachments": [att["filename"] for att in attachments]
  },
  "attachments": [  # 附件数据列表
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 1024,
      "data": b"..."  # 附件二进制数据
    }
  ]
}
```

#### OneBot12协议转换说明
邮件事件转换到OneBot12协议，主要差异点：

1. 特有字段：
   - `email_raw`: 包含原始邮件数据
   - `attachments`: 附件数据列表

2. 特殊处理：
   - 邮件主题和发件人信息会包含在消息文本中
   - 附件数据会以二进制形式提供
   - HTML内容会保留在email_raw字段中

3. 示例：
```python
{
  "type": "message",
  "platform": "email",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Subject: 会议通知\nFrom: sender@example.com\n\n请查收附件"
      }
    }
  ],
  "email_raw": {
    "subject": "会议通知",
    "from": "sender@example.com",
    "to": "receiver@example.com",
    "html_content": "<p>请查收附件</p>",
    "attachments": ["document.pdf"]
  },
  "attachments": [
    {
      "filename": "document.pdf",
      "data": b"...",  # 附件二进制数据
      "size": 1024
    }
  ]
}
```

---

## 参考链接
ErisPulse 项目：
- [主库](https://github.com/ErisPulse/ErisPulse/)
- [ErisPulse Yunhu 适配器库](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [ErisPulse Telegram 适配器库](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [ErisPulse OneBot 适配器库](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

相关官方文档：
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

<!--- End of PlatformFeatures.md -->

<!-- API文档 -->

# API参考

## adapter.md

# 📦 `ErisPulse.Core.adapter` 模块

<sup>自动生成于 2025-08-02 01:50:12</sup>

---

## 模块概述


ErisPulse 适配器系统

提供平台适配器基类、消息发送DSL和适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 适配器必须继承BaseAdapter并实现必要方法
2. 使用SendDSL实现链式调用风格的消息发送接口
3. 适配器管理器支持多平台适配器的注册和生命周期管理
4. 支持OneBot12协议的事件处理</p></div>

---

## 🏛️ 类

### `class SendDSLBase`

消息发送DSL基类

用于实现 Send.To(...).Func(...) 风格的链式调用接口

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 子类应实现具体的消息发送方法(如Text, Image等)
2. 通过__getattr__实现动态方法调用</p></div>


#### 🧰 方法

##### `__init__(adapter: 'BaseAdapter', target_type: Optional[str] = None, target_id: Optional[str] = None, account_id: Optional[str] = None)`

初始化DSL发送器

:param adapter: 所属适配器实例
:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:param _account_id: 发送账号(可选)

---

##### `To(target_type: str = None, target_id: Union[str, int] = None)`

设置消息目标

:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:return: SendDSL实例

<details class='example'><summary>示例</summary>

```python
>>> adapter.Send.To("user", "123").Text("Hello")
>>> adapter.Send.To("123").Text("Hello")  # 简化形式
```
</details>

---

##### `Using(account_id: Union[str, int])`

设置发送账号

:param _account_id: 发送账号
:return: SendDSL实例

<details class='example'><summary>示例</summary>

```python
>>> adapter.Send.Using("bot1").To("123").Text("Hello")
>>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序
```
</details>

---

### `class BaseAdapter`

适配器基类

提供与外部平台交互的标准接口，子类必须实现必要方法

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 必须实现call_api, start和shutdown方法
2. 可以自定义Send类实现平台特定的消息发送逻辑
3. 通过on装饰器注册事件处理器
4. 支持OneBot12协议的事件处理</p></div>


#### 🧰 方法

##### `__init__()`

初始化适配器

---

##### `on(event_type: str = '*')`

适配器事件监听装饰器

:param event_type: 事件类型
:return: 装饰器函数

---

##### `middleware(func: Callable)`

添加中间件处理器

:param func: 中间件函数
:return: 中间件函数

<details class='example'><summary>示例</summary>

```python
>>> @adapter.middleware
>>> async def log_middleware(data):
>>>     print(f"处理数据: {data}")
>>>     return data
```
</details>

---

##### 🔷 `async call_api(endpoint: str)`

调用平台API的抽象方法

:param endpoint: API端点
:param params: API参数
:return: API调用结果
<dt>异常</dt><dd><code>NotImplementedError</code> 必须由子类实现</dd>

---

##### 🔷 `async start()`

启动适配器的抽象方法

<dt>异常</dt><dd><code>NotImplementedError</code> 必须由子类实现</dd>

---

##### 🔷 `async shutdown()`

关闭适配器的抽象方法

<dt>异常</dt><dd><code>NotImplementedError</code> 必须由子类实现</dd>

---

##### 🔷 `async emit(event_type: str, data: Any)`

触发原生协议事件

:param event_type: 事件类型
:param data: 事件数据

<details class='example'><summary>示例</summary>

```python
>>> await adapter.emit("message", {"text": "Hello"})
```
</details>

---

##### 🔷 `async send(target_type: str, target_id: str, message: Any)`

发送消息的便捷方法

:param target_type: 目标类型
:param target_id: 目标ID
:param message: 消息内容
:param kwargs: 其他参数
    - method: 发送方法名(默认为"Text")
:return: 发送结果

<dt>异常</dt><dd><code>AttributeError</code> 当发送方法不存在时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> await adapter.send("user", "123", "Hello")
>>> await adapter.send("group", "456", "Hello", method="Markdown")
```
</details>

---

### `class AdapterManager`

适配器管理器

管理多个平台适配器的注册、启动和关闭

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 通过register方法注册适配器
2. 通过startup方法启动适配器
3. 通过shutdown方法关闭所有适配器
4. 通过on装饰器注册OneBot12协议事件处理器</p></div>


#### 🧰 方法

##### `Adapter()`

获取BaseAdapter类，用于访问原始事件监听

:return: BaseAdapter类

<details class='example'><summary>示例</summary>

```python
>>> @sdk.adapter.Adapter.on("raw_event")
>>> async def handle_raw(data):
>>>     print("收到原始事件:", data)
```
</details>

---

##### `on(event_type: str = '*')`

OneBot12协议事件监听装饰器

:param event_type: OneBot12事件类型
:return: 装饰器函数

<details class='example'><summary>示例</summary>

```python
>>> @sdk.adapter.on("message")
>>> async def handle_message(data):
>>>     print(f"收到OneBot12消息: {data}")
```
</details>

---

##### `middleware(func: Callable)`

添加OneBot12中间件处理器

:param func: 中间件函数
:return: 中间件函数

<details class='example'><summary>示例</summary>

```python
>>> @sdk.adapter.middleware
>>> async def onebot_middleware(data):
>>>     print("处理OneBot12数据:", data)
>>>     return data
```
</details>

---

##### 🔷 `async emit(data: Any)`

提交OneBot12协议事件到指定平台

:param platform: 平台名称
:param event_type: OneBot12事件类型
:param data: 符合OneBot12标准的事件数据

<dt>异常</dt><dd><code>ValueError</code> 当平台未注册时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> await sdk.adapter.emit("MyPlatform", "message", {
>>>     "id": "123",
>>>     "time": 1620000000,
>>>     "type": "message",
>>>     "detail_type": "private",
>>>     "message": [{"type": "text", "data": {"text": "Hello"}}]
>>> })
```
</details>

---

##### `register(platform: str, adapter_class: Type[BaseAdapter])`

注册新的适配器类

:param platform: 平台名称
:param adapter_class: 适配器类
:return: 注册是否成功

<dt>异常</dt><dd><code>TypeError</code> 当适配器类无效时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> adapter.register("MyPlatform", MyPlatformAdapter)
```
</details>

---

##### 🔷 `async startup(platforms: List[str] = None)`

启动指定的适配器

:param platforms: 要启动的平台列表，None表示所有平台

<dt>异常</dt><dd><code>ValueError</code> 当平台未注册时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> # 启动所有适配器
>>> await adapter.startup()
>>> # 启动指定适配器
>>> await adapter.startup(["Platform1", "Platform2"])
```
</details>

---

##### 🔷 `async _run_adapter(adapter: BaseAdapter, platform: str)`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
运行适配器实例

:param adapter: 适配器实例
:param platform: 平台名称

---

##### 🔷 `async shutdown()`

关闭所有适配器

<details class='example'><summary>示例</summary>

```python
>>> await adapter.shutdown()
```
</details>

---

##### `get(platform: str)`

获取指定平台的适配器实例

:param platform: 平台名称
:return: 适配器实例或None
    
<details class='example'><summary>示例</summary>

```python
>>> adapter = adapter.get("MyPlatform")
```
</details>

---

##### `__getattr__(platform: str)`

通过属性访问获取适配器实例

:param platform: 平台名称
:return: 适配器实例

<dt>异常</dt><dd><code>AttributeError</code> 当平台未注册时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> adapter = adapter.MyPlatform
```
</details>

---

##### `platforms()`

获取所有已注册的平台列表

:return: 平台名称列表
    
<details class='example'><summary>示例</summary>

```python
>>> print("已注册平台:", adapter.platforms)
```
</details>

---

<sub>文档最后更新于 2025-08-02 01:50:12</sub>

## config.md

# 📦 `ErisPulse.Core.config` 模块

<sup>自动生成于 2025-08-02 01:50:12</sup>

---

## 模块概述


ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能

---

<sub>文档最后更新于 2025-08-02 01:50:12</sub>

## env.md

# 📦 `ErisPulse.Core.env` 模块

<sup>自动生成于 2025-08-02 01:50:12</sup>

---

## 模块概述


ErisPulse 环境配置模块

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 自动快照功能防止数据丢失</p></div>

---

## 🏛️ 类

### `class EnvManager`

环境配置管理器

单例模式实现，提供配置的增删改查、事务和快照管理

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用get/set方法操作配置项
2. 使用transaction上下文管理事务
3. 使用snapshot/restore管理数据快照</p></div>


#### 🧰 方法

##### `_init_db()`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
初始化数据库

---

##### `get(key: str, default: Any = None)`

获取配置项的值

:param key: 配置项键名
:param default: 默认值(当键不存在时返回)
:return: 配置项的值

<details class='example'><summary>示例</summary>

```python
>>> timeout = env.get("network.timeout", 30)
>>> user_settings = env.get("user.settings", {})
```
</details>

---

##### `get_all_keys()`

获取所有配置项的键名

:return: 键名列表

<details class='example'><summary>示例</summary>

```python
>>> all_keys = env.get_all_keys()
>>> print(f"共有 {len(all_keys)} 个配置项")
```
</details>

---

##### `set(key: str, value: Any)`

设置配置项的值

:param key: 配置项键名
:param value: 配置项的值
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> env.set("app.name", "MyApp")
>>> env.set("user.settings", {"theme": "dark"})
```
</details>

---

##### `set_multi(items: Dict[str, Any])`

批量设置多个配置项

:param items: 键值对字典
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> env.set_multi({
>>>     "app.name": "MyApp",
>>>     "app.version": "1.0.0",
>>>     "app.debug": True
>>> })
```
</details>

---

##### `getConfig(key: str, default: Any = None)`

获取模块/适配器配置项
:param key: 配置项的键(支持点分隔符如"module.sub.key")
:param default: 默认值
:return: 配置项的值

---

##### `setConfig(key: str, value: Any)`

设置模块/适配器配置
:param key: 配置项键名(支持点分隔符如"module.sub.key")
:param value: 配置项值
:return: 操作是否成功

---

##### `delete(key: str)`

删除配置项

:param key: 配置项键名
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> env.delete("temp.session")
```
</details>

---

##### `delete_multi(keys: List[str])`

批量删除多个配置项

:param keys: 键名列表
:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> env.delete_multi(["temp.key1", "temp.key2"])
```
</details>

---

##### `get_multi(keys: List[str])`

批量获取多个配置项的值

:param keys: 键名列表
:return: 键值对字典

<details class='example'><summary>示例</summary>

```python
>>> settings = env.get_multi(["app.name", "app.version"])
```
</details>

---

##### `transaction()`

创建事务上下文

:return: 事务上下文管理器

<details class='example'><summary>示例</summary>

```python
>>> with env.transaction():
>>>     env.set("key1", "value1")
>>>     env.set("key2", "value2")
```
</details>

---

##### `_check_auto_snapshot()`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
检查并执行自动快照

---

##### `set_snapshot_interval(seconds: int)`

设置自动快照间隔

:param seconds: 间隔秒数

<details class='example'><summary>示例</summary>

```python
>>> # 每30分钟自动快照
>>> env.set_snapshot_interval(1800)
```
</details>

---

##### `clear()`

清空所有配置项

:return: 操作是否成功

<details class='example'><summary>示例</summary>

```python
>>> env.clear()  # 清空所有配置
```
</details>

---

##### `__getattr__(key: str)`

通过属性访问配置项

:param key: 配置项键名
:return: 配置项的值

<dt>异常</dt><dd><code>KeyError</code> 当配置项不存在时抛出</dd>
    
<details class='example'><summary>示例</summary>

```python
>>> app_name = env.app_name
```
</details>

---

##### `__setattr__(key: str, value: Any)`

通过属性设置配置项

:param key: 配置项键名
:param value: 配置项的值
    
<details class='example'><summary>示例</summary>

```python
>>> env.app_name = "MyApp"
```
</details>

---

##### `snapshot(name: Optional[str] = None)`

创建数据库快照

:param name: 快照名称(可选)
:return: 快照文件路径

<details class='example'><summary>示例</summary>

```python
>>> # 创建命名快照
>>> snapshot_path = env.snapshot("before_update")
>>> # 创建时间戳快照
>>> snapshot_path = env.snapshot()
```
</details>

---

##### `restore(snapshot_name: str)`

从快照恢复数据库

:param snapshot_name: 快照名称或路径
:return: 恢复是否成功

<details class='example'><summary>示例</summary>

```python
>>> env.restore("before_update")
```
</details>

---

##### `list_snapshots()`

列出所有可用的快照

:return: 快照信息列表(名称, 创建时间, 大小)

<details class='example'><summary>示例</summary>

```python
>>> for name, date, size in env.list_snapshots():
>>>     print(f"{name} - {date} ({size} bytes)")
```
</details>

---

##### `delete_snapshot(snapshot_name: str)`

删除指定的快照

:param snapshot_name: 快照名称
:return: 删除是否成功

<details class='example'><summary>示例</summary>

```python
>>> env.delete_snapshot("old_backup")
```
</details>

---

<sub>文档最后更新于 2025-08-02 01:50:12</sub>

## erispulse_config.md

# 📦 `ErisPulse.Core.erispulse_config` 模块

<sup>自动生成于 2025-08-02 01:50:12</sup>

---

## 模块概述


ErisPulse 框架配置管理

专门管理 ErisPulse 框架自身的配置项。

---

## 🛠️ 函数

### `_ensure_erispulse_config_structure(config_dict: Dict[str, Any])`

确保 ErisPulse 配置结构完整，补全缺失的配置项

:param config_dict: 当前配置
:return: 补全后的完整配置

---

### `get_erispulse_config()`

获取 ErisPulse 框架配置，自动补全缺失的配置项并保存

:return: 完整的 ErisPulse 配置字典

---

### `update_erispulse_config(new_config: Dict[str, Any])`

更新 ErisPulse 配置，自动补全缺失的配置项

:param new_config: 新的配置字典
:return: 是否更新成功

---

### `get_server_config()`

获取服务器配置，确保结构完整

:return: 服务器配置字典

---

### `get_logger_config()`

获取日志配置，确保结构完整

:return: 日志配置字典

---

<sub>文档最后更新于 2025-08-02 01:50:12</sub>

## exceptions.md

# 📦 `ErisPulse.Core.exceptions` 模块

<sup>自动生成于 2025-08-02 01:50:12</sup>

---

## 模块概述


ErisPulse 全局异常处理系统

提供统一的异常捕获和格式化功能，支持同步和异步代码的异常处理。

---

## 🛠️ 函数

### `global_exception_handler(exc_type: Type[Exception], exc_value: Exception, exc_traceback: Any)`

全局异常处理器

:param exc_type: 异常类型
:param exc_value: 异常值
:param exc_traceback: 追踪信息

---

### `async_exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any])`

异步异常处理器

:param loop: 事件循环
:param context: 上下文字典

---

### `setup_async_loop(loop: asyncio.AbstractEventLoop = None)`

为指定的事件循环设置异常处理器

:param loop: 事件循环实例，如果为None则使用当前事件循环

---

<sub>文档最后更新于 2025-08-02 01:50:12</sub>

## logger.md

# 📦 `ErisPulse.Core.logger` 模块

<sup>自动生成于 2025-08-02 01:50:12</sup>

---

## 模块概述


ErisPulse 日志系统

提供模块化日志记录功能，支持多级日志、模块过滤和内存存储。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 支持按模块设置不同日志级别
2. 日志可存储在内存中供后续分析
3. 自动识别调用模块名称</p></div>

---

## 🏛️ 类

### `class Logger`

日志管理器

提供模块化日志记录和存储功能

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用set_module_level设置模块日志级别
2. 使用get_logs获取历史日志
3. 支持标准日志级别(DEBUG, INFO等)</p></div>


#### 🧰 方法

##### `set_memory_limit(limit: int)`

设置日志内存存储上限

:param limit: 日志存储上限
:return: bool 设置是否成功

---

##### `set_level(level: str)`

设置全局日志级别

:param level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
:return: bool 设置是否成功

---

##### `set_module_level(module_name: str, level: str)`

设置指定模块日志级别

:param module_name: 模块名称
:param level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
:return: bool 设置是否成功

---

##### `set_output_file(path)`

设置日志输出

:param path: 日志文件路径 Str/List
:return: bool 设置是否成功

---

##### `save_logs(path)`

保存所有在内存中记录的日志

:param path: 日志文件路径 Str/List
:return: bool 设置是否成功

---

##### `get_logs(module_name: str = None)`

获取日志内容

:param module_name (可选): 模块名称
:return: dict 日志内容

---

<sub>文档最后更新于 2025-08-02 01:50:12</sub>

## mods.md

# 📦 `ErisPulse.Core.mods` 模块

<sup>自动生成于 2025-08-02 01:50:12</sup>

---

## 模块概述


ErisPulse 模块管理器

提供模块的注册、状态管理和依赖关系处理功能。支持模块的启用/禁用、版本控制和依赖解析。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系</p></div>

---

## 🏛️ 类

### `class ModuleManager`

模块管理器

管理所有模块的注册、状态和依赖关系

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 通过set_module/get_module管理模块信息
2. 通过set_module_status/get_module_status控制模块状态
3. 通过set_all_modules/get_all_modules批量操作模块</p></div>


#### 🧰 方法

##### `_ensure_prefixes()`

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
确保模块前缀配置存在

---

##### `module_prefix()`

获取模块数据前缀

:return: 模块数据前缀字符串

---

##### `status_prefix()`

获取模块状态前缀

:return: 模块状态前缀字符串

---

##### `set_module_status(module_name: str, status: bool)`

设置模块启用状态

:param module_name: 模块名称
:param status: 启用状态

<details class='example'><summary>示例</summary>

```python
>>> # 启用模块
>>> mods.set_module_status("MyModule", True)
>>> # 禁用模块
>>> mods.set_module_status("MyModule", False)
```
</details>

---

##### `get_module_status(module_name: str)`

获取模块启用状态

:param module_name: 模块名称
:return: 模块是否启用

<details class='example'><summary>示例</summary>

```python
>>> if mods.get_module_status("MyModule"):
>>>     print("模块已启用")
```
</details>

---

##### `set_module(module_name: str, module_info: Dict[str, Any])`

设置模块信息

:param module_name: 模块名称
:param module_info: 模块信息字典

<details class='example'><summary>示例</summary>

```python
>>> mods.set_module("MyModule", {
>>>     "version": "1.0.0",
>>>     "description": "我的模块",
>>> })
```
</details>

---

##### `get_module(module_name: str)`

获取模块信息

:param module_name: 模块名称
:return: 模块信息字典或None

<details class='example'><summary>示例</summary>

```python
>>> module_info = mods.get_module("MyModule")
>>> if module_info:
>>>     print(f"模块版本: {module_info.get('version')}")
```
</details>

---

##### `set_all_modules(modules_info: Dict[str, Dict[str, Any]])`

批量设置多个模块信息

:param modules_info: 模块信息字典

<details class='example'><summary>示例</summary>

```python
>>> mods.set_all_modules({
>>>     "Module1": {"version": "1.0", "status": True},
>>>     "Module2": {"version": "2.0", "status": False}
>>> })
```
</details>

---

##### `get_all_modules()`

获取所有模块信息

:return: 模块信息字典

<details class='example'><summary>示例</summary>

```python
>>> all_modules = mods.get_all_modules()
>>> for name, info in all_modules.items():
>>>     print(f"{name}: {info.get('status')}")
```
</details>

---

##### `update_module(module_name: str, module_info: Dict[str, Any])`

更新模块信息

:param module_name: 模块名称
:param module_info: 完整的模块信息字典

---

##### `remove_module(module_name: str)`

移除模块

:param module_name: 模块名称
:return: 是否成功移除

<details class='example'><summary>示例</summary>

```python
>>> if mods.remove_module("OldModule"):
>>>     print("模块已移除")
```
</details>

---

##### `update_prefixes(module_prefix: Optional[str] = None, status_prefix: Optional[str] = None)`

更新模块前缀配置

:param module_prefix: 新的模块数据前缀(可选)
:param status_prefix: 新的模块状态前缀(可选)

<details class='example'><summary>示例</summary>

```python
>>> # 更新模块前缀
>>> mods.update_prefixes(
>>>     module_prefix="custom.module.data:",
>>>     status_prefix="custom.module.status:"
>>> )
```
</details>

---

<sub>文档最后更新于 2025-08-02 01:50:12</sub>

## router.md

# 📦 `ErisPulse.Core.router` 模块

<sup>自动生成于 2025-08-02 01:50:12</sup>

---

## 模块概述


ErisPulse 路由系统

提供统一的HTTP和WebSocket路由管理，支持多适配器路由注册和生命周期管理。

<div class='admonition tip'><p class='admonition-title'>提示</p><p>1. 适配器只需注册路由，无需自行管理服务器
2. WebSocket支持自定义认证逻辑
3. 兼容FastAPI 0.68+ 版本</p></div>

---

## 🏛️ 类

### `class RouterManager`

路由管理器

<div class='admonition tip'><p class='admonition-title'>提示</p><p>核心功能：
- HTTP/WebSocket路由注册
- 生命周期管理
- 统一错误处理</p></div>


#### 🧰 方法

##### `__init__()`

初始化路由管理器

<div class='admonition tip'><p class='admonition-title'>提示</p><p>会自动创建FastAPI实例并设置核心路由</p></div>

---

##### `_setup_core_routes()`

设置系统核心路由

<div class='admonition warning'><p class='admonition-title'>内部方法</p><p></p></div>
此方法仅供内部使用
{!--< /internal-use >!--}

---

##### `register_http_route(module_name: str, path: str, handler: Callable, methods: List[str] = ['POST'])`

注册HTTP路由

:param module_name: str 模块名称
:param path: str 路由路径
:param handler: Callable 处理函数
:param methods: List[str] HTTP方法列表(默认["POST"])

<dt>异常</dt><dd><code>ValueError</code> 当路径已注册时抛出</dd>

---

##### `register_webhook()`

兼容性方法：注册HTTP路由（适配器旧接口）

---

##### `register_websocket(module_name: str, path: str, handler: Callable[[WebSocket], Awaitable[Any]], auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] = None)`

注册WebSocket路由

:param module_name: str 模块名称
:param path: str WebSocket路径
:param handler: Callable[[WebSocket], Awaitable[Any]] 主处理函数
:param auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] 认证函数

<dt>异常</dt><dd><code>ValueError</code> 当路径已注册时抛出</dd>

---

##### `get_app()`

获取FastAPI应用实例

:return: FastAPI应用实例

---

##### 🔷 `async start(host: str = '0.0.0.0', port: int = 8000, ssl_certfile: Optional[str] = None, ssl_keyfile: Optional[str] = None)`

启动路由服务器

:param host: str 监听地址(默认"0.0.0.0")
:param port: int 监听端口(默认8000)
:param ssl_certfile: Optional[str] SSL证书路径
:param ssl_keyfile: Optional[str] SSL密钥路径

<dt>异常</dt><dd><code>RuntimeError</code> 当服务器已在运行时抛出</dd>

---

##### 🔷 `async stop()`

停止服务器

---

<sub>文档最后更新于 2025-08-02 01:50:12</sub>

<!--- End of API文档 -->
