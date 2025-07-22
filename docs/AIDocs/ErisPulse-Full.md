# ErisPulse 完整开发文档

本文件由多个开发文档合并而成，用于辅助 AI 理解 ErisPulse 的相关功能。

## 各文件对应内容说明

| 文件名 | 作用 |
|--------|------|
| quick-start.md | 快速开始指南 |
| UseCore.md | 核心功能使用说明 |
| PlatformFeatures.md | 平台功能说明 |
| Module.md | 模块开发指南 |
| Adapter.md | 适配器开发指南 |
| APIResponse.md | API响应标准 |
| EventConversion.md | 事件转换标准 |

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
| `env`/`sdk.env` | 获取/设置全局配置 |
| `mods`/`sdk.mods` | 模块管理器 |
| `adapter`/`sdk.adapter` | 适配器管理/获取实例 |
| `logger`/`sdk.logger` | 日志记录器 |
| `util`/`sdk.util` | 工具函数（缓存、重试等） |
| `BaseAdapter`/`sdk.BaseAdapter` | 适配器基类 |

```python
# 直接导入方式
from ErisPulse.Core import env, mods, logger, util, adapter, BaseAdapter

# 通过SDK对象方式
from ErisPulse import sdk
sdk.env  # 等同于直接导入的env
```

## 模块系统架构
- 所有模块通过`sdk`对象统一管理
- 模块间可通过`sdk.<ModuleName>`互相调用
- 模块基础结构示例：
```python
from ErisPulse import sdk

class MyModule:
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger
        
    def hello(self):
        self.logger.info("hello world")
        return "hello world"
```

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

# 监听底层的标准事件
@adapter.on("message")
async def on_message(data):
    platform = data.get("platform")
    detail_type = "user" if data.get("detail_type") == "private" else "group"
    detail_id = data.get("user_id") if detail_type == "user" else data.get("group_id")
    
    if hasattr(adapter, platform):
        await getattr(adapter, platform).To(detail_type, detail_id).Text(data.get("alt_message"))
```

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

# 模块配置操作（读写config.toml）
module_config = env.getConfig("MyModule")  # 获取模块配置
if module_config is None:
    env.setConfig("MyModule", {"MyKey": "MyValue"})  # 设置默认配置
```

### 3. 工具函数(util)
```python
# 自动重试
@util.retry(max_attempts=3, delay=1)
async def unreliable_function():
    ...

# 结果缓存
@util.cache
def expensive_operation(param):
    ...

# 异步执行
@util.run_in_executor
def sync_task():
    ...

# 同步调用异步
util.ExecAsync(sync_task)
```

## 建议
1. 模块配置应使用`getConfig/setConfig`操作config.toml
2. 持久信息存储使用`get/set`操作数据库
3. 关键操作使用事务保证原子性
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
   await adapter.AdapterName.To("user", "U1001").Text("Hello")
   ```
2. 仅指定ID: `To(id).Func()`
   ```python
   await adapter.AdapterName.To("U1001").Text("Hello")
   ```
3. 指定发送账号: `Using(account_id)`
   ```python
   await adapter.AdapterName.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接调用: `Func()`
   ```python
   await adapter.AdapterName.Text("Broadcast message")
   ```

### 事件监听
有两种事件监听方式：

1. 平台原生事件监听：
   ```python
   @adapter.AdapterName.on("event_type")
   async def handler(data):
       print(f"收到原生事件: {data}")
   ```

2. OneBot12标准事件监听：
   ```python
   @adapter.on("event_type")  # 所有平台的标准事件
   async def handler(data):
       if data["platform"] == "yunhu":
           print(f"收到云湖标准事件: {data}")
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

<!-- Module.md -->

# ErisPulse 模块开发指南

## 1. 模块结构
一个标准的模块包结构应该是：

```
MyModule/
├── pyproject.toml    # 项目配置
├── README.md         # 项目说明
├── LICENSE           # 许可证文件
└── MyModule/
    ├── __init__.py  # 模块入口
    └── Core.py      # 核心逻辑(只是推荐结构使用Core.py | 只要模块入口使用正确，你可以使用任何你喜欢的文件名)
```

## 2. `pyproject.toml` 文件
模块的配置文件, 包括模块信息、依赖项、模块/适配器入口点等信息

```toml
[project]
name = "ErisPulse-MyModule"     # 模块名称, 建议使用 ErisPulse-<模块名称> 的格式命名
version = "1.0.0"
description = "一个非常哇塞的模块"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = [
    
]

# 模块主页, 用于在模块管理器中显示模块信息 | 尽量使用仓库地址，以便模块商店显示文档时指定为仓库的 README.md 文件
[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

# 模块入口点，用于指定模块的入口类 当然也可以在一个包中定义多个模块，但并不建议这样做
[project.entry-points]
"erispulse.module" = { "MyModule" = "MyModule:Main" }

```

## 3. `MyModule/__init__.py` 文件

顾名思义,这只是使你的模块变成一个Python包, 你可以在这里导入模块核心逻辑, 当然也可以让他保持空白

示例这里导入了模块核心逻辑

```python
from .Core import Main
```

---

## 3. `MyModule/Core.py` 文件

实现模块主类 `Main`, 其中 `sdk` 参数的传入在 `2.x.x`版本 中不再是必须的，但推荐传入

```python
# 这也是一种可选的获取 `sdk`对象 的方式
# from ErisPulse import sdk

class Main:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
        self.env = sdk.env
        self.util = sdk.util

        self.logger.info("模块已加载")
        self.config = self._get_config()

    @staticmethod
    def should_eager_load(self):
        # 这适用于懒加载模块, 如果模块需要立即加载, 请返回 True | 比如一些监听器模块/定时器模块等等
        return False

    # 从环境变量中获取配置, 如果不存在则使用默认值
    def _get_config(self):
        config = env.getConfig("MyModule")
        if not config:
            default_config = {
                "my_config_key": "default_value"
            }
            env.setConfig("MyModule", default_config)
            self.logger.warning("未找到模块配置, 对应模块配置已经创建到config.toml中")
            return default_config
        return config

    def print_hello(self):
        self.logger.info("Hello World!")

```

- 所有 SDK 提供的功能都可通过 `sdk` 对象访问。
```python
# 这时候在其它地方可以访问到该模块
from ErisPulse import sdk
sdk.MyModule.print_hello()

# 运行模块主程序（推荐使用CLI命令）
# epsdk run main.py --reload
```
## 4. `LICENSE` 文件
`LICENSE` 文件用于声明模块的版权信息, 示例模块的声明默认为 `MIT` 协议。

---

## 开发建议

### 1. 使用异步编程模型
- **优先使用异步库**：如 `aiohttp`、`asyncpg` 等，避免阻塞主线程。
- **合理使用事件循环**：确保异步函数正确地被 `await` 或调度为任务（`create_task`）。

### 2. 异常处理与日志记录
- **统一异常处理机制**：直接 `raise` 异常，上层会自动捕获并记录日志。
- **详细的日志输出**：在关键路径上打印调试日志，便于问题排查。

### 3. 模块化与解耦设计
- **职责单一原则**：每个模块/类只做一件事，降低耦合度。
- **依赖注入**：通过构造函数传递依赖对象（如 `sdk`），提高可测试性。

### 4. 性能优化
- **缓存机制**：利用 `@sdk.util.cache` 缓存频繁调用的结果。
- **资源复用**：连接池、线程池等应尽量复用，避免重复创建销毁开销。

### 5. 安全与隐私
- **敏感数据保护**：避免将密钥、密码等硬编码在代码中，使用环境变量或配置中心。
- **输入验证**：对所有用户输入进行校验，防止注入攻击等安全问题。

---

*文档最后更新于 2025-07-17 07:12:26*

<!--- End of Module.md -->

<!-- Adapter.md -->

# ErisPulse 适配器开发指南

### 1. 目录结构
一个标准的适配器包结构应该是：

```
MyAdapter/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyAdapter/
    ├── __init__.py
    ├── Core.py
    └── Converter.py
```

### 2. `pyproject.toml` 文件
```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "MyAdapter是一个非常酷的平台，这个适配器可以帮你绽放更亮的光芒"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points]
"erispulse.adapter" = { "MyAdapter" = "MyAdapter:MyAdapter" }

```

### 3. `MyAdapter/__init__.py` 文件

顾名思义,这只是使你的模块变成一个Python包, 你可以在这里导入模块核心逻辑, 当然也可以让他保持空白

示例这里导入了模块核心逻辑

```python
from .Core import MyAdapter
```

### 4. `MyAdapter/Core.py`
实现适配器主类 `MyAdapter`，并提供适配器类继承 `BaseAdapter`, 实现嵌套类Send以实现例如 Send.To(type, id).Text("hello world") 的语法

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core import adapter_server

# 这里仅你使用 websocket 作为通信协议时需要 | 第一个作为参数的类型是 WebSocket, 第二个是 WebSocketDisconnect，当 ws 连接断开时触发你的捕捉
# 一般来说你不用在依赖中添加 fastapi, 因为它已经内置在 ErisPulse 中了
from fastapi import WebSocket, WebSocketDisconnect

class MyAdapter(BaseAdapter):
    def __init__(self, sdk):    # 这里是不强制传入sdk的，你可以选择不传入 
        self.sdk = sdk
        self.env = self.sdk.env
        self.logger = self.sdk.logger
        
        self.logger.info("MyModule 初始化完成")
        self.config = self._get_config()
        self.converter = self._setup_converter()  # 获取转换器实例
        self.convert = self.converter.convert

    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()

    def _get_config(self):
        # 加载配置方法，你需要在这里进行必要的配置加载逻辑
        config = self.env.getConfig("MyAdapter", {})

        if config is None:
            default_config = {...}
            # 这里默认配置会生成到用户的 config.toml 文件中
            self.env.setConfig("MyAdapter", default_config)
            return default_config
        return config

    class Send(BaseAdapter.Send):  # 继承BaseAdapter内置的Send类
        """
        Send消息发送DSL，支持四种调用方式(继承的Send类包含了To和Using方法):
        1. 指定类型和ID: To(type,id).Func() -> 设置_target_type和_target_id/_target_to
           示例: Send.To("group",123).Text("hi")
        2. 指定发送账号: Using(account_id).Func() -> 设置_account_id
           示例: Send.Using("bot1").Text("hi")
        3. 组合使用: Using(account_id).To(type,id).Func()
           示例: Send.Using("bot1").To("user","123").Text("hi")
        4. 直接调用: Func() -> 不设置目标属性
           示例: Send.Text("broadcast")
        """
        
        def Text(self, text: str):
            """发送文本消息（可重写实现）"""
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,    # 来自To()设置的属性
                    recvType=self._target_type # 来自To(type,id)设置的属性
                )
            )
            
        def Image(self, file: bytes):
            """发送图片消息"""
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send_image",
                    file=file,
                    recvId=self._target_id,    # 自动使用To()设置的属性
                    recvType=self._target_type
                )
            )

    # 这里的call_api方法需要被实现, 哪怕他是类似邮箱时一个轮询一个发送stmp无需请求api的实现
    # 因为这是必须继承的方法
    async def call_api(self, endpoint: str, **params):
        raise NotImplementedError()

    # 适配器设定了启动和停止的方法，用户可以直接通过 sdk.adapter.setup() 来启动所有适配器，
    # 当然在底层捕捉到adapter的错误时我们会尝试停止适配器再进行重启等操作
    # 启动方法，你需要在这里定义你的adapter启动时候的逻辑
    async def start(self):
        raise NotImplementedError()
    # 停止方法，你需要在这里进行必要的释放资源等逻辑
    async def shutdown(self):
        raise NotImplementedError()
```
### 接口规范说明

#### 必须实现的方法

| 方法 | 描述 |
|------|------|
| `call_api(endpoint: str, **params)` | 调用平台 API |
| `start()` | 启动适配器 |
| `shutdown()` | 关闭适配器资源 |

#### 可选实现的方法

| 方法 | 描述 |
|------|------|
| `on(event_type: str)` | 注册事件处理器 |
| `add_handler(event_type: str, func: Callable)/add_handler(func: Callable)` | 添加事件处理器 |
| `middleware(func: Callable)` | 添加中间件处理传入数据 |
| `emit(event_type: str, data: Any)` | 自定义事件分发逻辑 |

- 在适配器中如果需要向底层提交事件，请使用 `emit()` 方法。
- 这时用户可以通过 `on([事件类型])` 修饰器 或者 `add_handler()` 获取到你提交到adapter的事件。

> ⚠️ 注意：
> - 适配器类必须继承 `sdk.BaseAdapter`；
> - 必须实现 `call_api`, `start`, `shutdown` 方法 和 `Send`类并继承自 `super().Send`；
> - 推荐实现 `.Text(...)` 方法作为基础消息发送接口。
> - To中的接受者类型不允许例如 "private" 的格式，当然这是一个规范，但为了兼容性，请使用 "user" / "group" / other

### 4. DSL 风格消息接口（SendDSL）

每个适配器可定义一组链式调用风格的方法，例如：

```python
class Send((BaseAdapter.Send):
    def Text(self, text: str):
        return asyncio.create_task(
            self._adapter.call_api(...)
        )

    def Image(self, file: bytes):
        return asyncio.create_task(
            self._upload_file_and_call_api(...)
        )
```

调用方式支持以下组合：

1. 指定发送账号和接收目标：
```python
sdk.adapter.MyPlatform.Send.Using("bot1").To("user", "U1001").Text("你好")
```

2. 仅指定接收目标：
```python
sdk.adapter.MyPlatform.Send.To("user", "U1001").Text("你好")
```

3. 仅指定发送账号：
```python
sdk.adapter.MyPlatform.Send.Using("bot1").Text("广播消息")
```

4. 直接调用：
```python
sdk.adapter.MyPlatform.Send.Text("广播消息")
```

`Using`方法用于指定发送账号，会设置`self._account_id`属性，可以在后续API调用中使用。

---

## 5. 事件转换与路由注册

适配器需要处理平台原生事件并转换为OneBot12标准格式，同时需要向底层框架注册路由。以下是两种典型实现方式：

### 5.1 WebSocket 方式实现

```python
async def _ws_handler(self, websocket: WebSocket):
    """WebSocket连接处理器"""
    self.connection = websocket
    self.logger.info("客户端已连接")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                event = json.loads(data)
                # 提交原生事件到适配器
                # 原生事件需要通过指定平台来获取 比如 sdk.adapter.MyPlatform.on("事件类型")
                self.emit(data.get("event_type"), data)

                # 转换为OneBot12标准事件
                onebot_event = self.convert(event)
                if onebot_event:
                    # 提交标准事件到框架 | 这里直接通过 sdk.adaoter.on("事件类型") 便可以获取到事件，但是需要判断字段里面的platform字段来区分适配器
                    await self.sdk.adapter.emit(onebot_event)
            except json.JSONDecodeError:
                self.logger.error(f"JSON解析失败: {data}")
    except WebSocketDisconnect:
        self.logger.info("客户端断开连接")
    finally:
        self.connection = None

async def start(self):
    """注册WebSocket路由"""
    adapter_server.register_websocket(
        adapter_name="myplatform",  # 适配器名称
        path="/ws",  # 路由路径
        handler=self._ws_handler,  # 处理器
        auth_handler=self._auth_handler  # 认证处理器(可选)
    )
```

### 5.2 WebHook 方式实现

```python
async def _webhook_handler(self, request: Request):
    """WebHook请求处理器"""
    try:
        data = await request.json()

        # 提交原生事件到适配器
        # 原生事件需要通过指定平台来获取 比如 sdk.adapter.MyPlatform.on("事件类型")
        self.emit(data.get("event_type"), data)

        # 转换为OneBot12标准事件
        onebot_event = self.convert(data)=
        if onebot_event:
            # 提交标准事件到框架 | 这里直接通过 sdk.adaoter.on("事件类型") 便可以获取到事件，但是需要判断字段里面的platform字段来区分适配器
            await self.sdk.adapter.emit(onebot_event)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        self.logger.error(f"处理WebHook失败: {str(e)}")
        return JSONResponse({"status": "failed"}, status_code=400)

async def start(self):
    """注册WebHook路由"""
    adapter_server.register_webhook(
        adapter_name="myplatform",  # 适配器名称
        path="/webhook",  # 路由路径
        handler=self._webhook_handler,  # 处理器
        methods=["POST"]  # 支持的HTTP方法
    )
```

### 5.3 事件转换器实现

适配器应提供标准的事件转换器，将平台原生事件转换为OneBot12格式(具体实现请参考[事件转换标准文档](docs/AdapterStandards/EventConversion.md)：

```python
class MyPlatformConverter:
    def convert(self, raw_event: Dict) -> Optional[Dict]:
        """将平台原生事件转换为OneBot12标准格式"""
        if not isinstance(raw_event, dict):
            return None

        # 基础事件结构
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": "",  # message/notice/request/meta_event
            "detail_type": "",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event  # 保留原始数据
        }

        # 根据事件类型分发处理
        event_type = raw_event.get("type")
        if event_type == "message":
            return self._handle_message(raw_event, onebot_event)
        elif event_type == "notice":
            return self._handle_notice(raw_event, onebot_event)
        
        return None
```

## 6. API响应标准

适配器的`call_api`方法必须返回符合以下标准的响应结构：

### 6.1 成功响应格式

```python
{
    "status": "ok",  # 必须
    "retcode": 0,  # 必须，0表示成功
    "data": {  # 必须，成功时返回的数据
        "message_id": "123456",  # 消息ID(如果有)
        "time": 1632847927.599013  # 时间戳(如果有)
    },
    "message": "",  # 必须，成功时为空字符串
    "message_id": "123456",  # 可选，消息ID
    "echo": "1234",  # 可选，当请求中包含echo时返回
    "myplatform_raw": {...}  # 可选，原始响应数据
}
```

### 6.2 失败响应格式

```python
{
    "status": "failed",  # 必须
    "retcode": 10003,  # 必须，非0错误码
    "data": None,  # 必须，失败时为null
    "message": "缺少必要参数",  # 必须，错误描述
    "message_id": "",  # 可选，失败时为空字符串
    "echo": "1234",  # 可选，当请求中包含echo时返回
    "myplatform_raw": {...}  # 可选，原始响应数据
}
```

### 6.3 实现示例

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 调用平台API
        raw_response = await self._platform_api_call(endpoint, **params)
        
        # 标准化响应
        standardized = {
            "status": "ok" if raw_response["success"] else "failed",
            "retcode": 0 if raw_response["success"] else raw_response.get("code", 10001),
            "data": raw_response.get("data"),
            "message": raw_response.get("message", ""),
            "message_id": raw_response.get("data", {}).get("message_id", ""),
            "myplatform_raw": raw_response
        }
        
        if "echo" in params:
            standardized["echo"] = params["echo"]
            
        return standardized
        
    except Exception as e:
        return {
            "status": "failed",
            "retcode": 34000,  # 平台错误代码段
            "data": None,
            "message": str(e),
            "message_id": ""
        }
```

## 7. 错误代码规范

适配器应遵循以下错误代码范围：

| 代码范围 | 类型 | 说明 |
|---------|------|------|
| 0 | 成功 | 必须为0 |
| 1xxxx | 请求错误 | 无效参数、不支持的操作等 |
| 2xxxx | 处理器错误 | 适配器内部处理错误 |
| 3xxxx | 执行错误 | 平台API调用错误 |
| 34xxx | 平台错误 | 平台返回的错误 |

建议在适配器中定义常量：

```python
class ErrorCode:
    SUCCESS = 0
    INVALID_PARAMS = 10003
    UNSUPPORTED_ACTION = 10002
    INTERNAL_ERROR = 20001
    PLATFORM_ERROR = 34000
```

---

## 开发建议

### 1. 使用异步编程模型
- **优先使用异步库**：如 `aiohttp`、`asyncpg` 等，避免阻塞主线程。
- **合理使用事件循环**：确保异步函数正确地被 `await` 或调度为任务（`create_task`）。

### 2. 异常处理与日志记录
- **统一异常处理机制**：直接 `raise` 异常，上层会自动捕获并记录日志。
- **详细的日志输出**：在关键路径上打印调试日志，便于问题排查。

### 3. 模块化与解耦设计
- **职责单一原则**：每个模块/类只做一件事，降低耦合度。
- **依赖注入**：通过构造函数传递依赖对象（如 `sdk`），提高可测试性。

### 4. 性能优化
- **缓存机制**：利用 `@sdk.util.cache` 缓存频繁调用的结果。
- **资源复用**：连接池、线程池等应尽量复用，避免重复创建销毁开销。

### 5. 安全与隐私
- **敏感数据保护**：避免将密钥、密码等硬编码在代码中，使用环境变量或配置中心。
- **输入验证**：对所有用户输入进行校验，防止注入攻击等安全问题。

---

*文档最后更新于 2025-07-17 12:44:51*

<!--- End of Adapter.md -->

<!-- APIResponse.md -->

# ErisPulse 适配器标准化返回规范

## 1. 说明
为什么会有这个规范？

ErisPulse的适配器需要与OneBot12标准进行对接，而OneBot12标准中定义了消息发送的返回结构，因此ErisPulse的适配器也需要遵循这个标准。

但ErisPulse的协议有一些特殊性定义:
- 1. 基础字段中，message_id是必须的，但OneBot12标准中无此字段
- 2. 返回内容中需要添加 {platform_name}_raw 字段，用于存放原始响应数据

## 2. 基础返回结构
所有动作响应必须包含以下基础字段：

| 字段名 | 数据类型 | 必选 | 说明 |
|-------|---------|------|------|
| status | string | 是 | 执行状态，必须是"ok"或"failed" |
| retcode | int64 | 是 | 返回码，遵循OneBot12返回码规则 |
| data | any | 是 | 响应数据，成功时包含请求结果，失败时为null |
| message_id | string | 是 | 消息ID，用于标识消息, 没有则为空字符串 |
| message | string | 是 | 错误信息，成功时为空字符串 |
| {platform_name}_raw | any | 否 | 原始响应数据 |

可选字段：
| 字段名 | 数据类型 | 必选 | 说明 |
|-------|---------|------|------|
| echo | string | 否 | 当请求中包含echo字段时，原样返回 |

## 3. 完整字段规范

### 3.1 通用字段

#### 成功响应示例
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
    "telegram_raw": {...}
}
```

#### 失败响应示例
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "缺少必要参数: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 返回码规范

#### 0 成功（OK）
- 0: 成功（OK）

#### 1xxxx 动作请求错误（Request Error）
| 错误码 | 错误名 | 说明 |
|-------|-------|------|
| 10001 | Bad Request | 无效的动作请求 |
| 10002 | Unsupported Action | 不支持的动作请求 |
| 10003 | Bad Param | 无效的动作请求参数 |
| 10004 | Unsupported Param | 不支持的动作请求参数 |
| 10005 | Unsupported Segment | 不支持的消息段类型 |
| 10006 | Bad Segment Data | 无效的消息段参数 |
| 10007 | Unsupported Segment Data | 不支持的消息段参数 |
| 10101 | Who Am I | 未指定机器人账号 |
| 10102 | Unknown Self | 未知的机器人账号 |

#### 2xxxx 动作处理器错误（Handler Error）
| 错误码 | 错误名 | 说明 |
|-------|-------|------|
| 20001 | Bad Handler | 动作处理器实现错误 |
| 20002 | Internal Handler Error | 动作处理器运行时抛出异常 |

#### 3xxxx 动作执行错误（Execution Error）
| 错误码范围 | 错误类型 | 说明 |
|-----------|---------|------|
| 31xxx | Database Error | 数据库错误 |
| 32xxx | Filesystem Error | 文件系统错误 |
| 33xxx | Network Error | 网络错误 |
| 34xxx | Platform Error | 机器人平台错误 |
| 35xxx | Logic Error | 动作逻辑错误 |
| 36xxx | I Am Tired | 实现决定罢工 |

#### 保留错误段
- 4xxxx、5xxxx: 保留段，不应使用
- 6xxxx～9xxxx: 其他错误段，供实现自定义使用

## 4. 实现要求
1. 所有响应必须包含status、retcode、data和message字段
2. 当请求中包含非空echo字段时，响应必须包含相同值的echo字段
3. 返回码必须严格遵循OneBot12规范
4. 错误信息(message)应当是人类可读的描述

## 5. 注意事项
- 对于3xxxx错误码，低三位可由实现自行定义
- 避免使用保留错误段(4xxxx、5xxxx)
- 错误信息应当简洁明了，便于调试

<!--- End of APIResponse.md -->

<!-- EventConversion.md -->

# ErisPulse 适配器标准化转换规范

## 1. 核心原则
1. 严格兼容：所有标准字段必须完全遵循OneBot12规范
2. 明确扩展：平台特有功能必须添加 {platform}_ 前缀（如 yunhu_form）
3. 数据完整：原始事件数据必须保留在 {platform}_raw 字段中
4. 时间统一：所有时间戳必须转换为10位Unix时间戳（秒级）
5. 平台统一：platform项命名必须与你在ErisPulse中注册的名称/别称一致

## 2. 基础字段规范
### 2.1 必填字段（所有事件）
|字段|类型|要求|
|-|-|-|
|id|string|必须存在，原始事件无ID时使用UUID生成|
|time|int|10位秒级时间戳（毫秒级需转换）|
|type|string|必须为 message/notice/request 之一|
|platform|string|必须与适配器注册名完全一致|
|self|object|必须包含 platform 和 user_id|

### 2.2 条件字段
|字段|触发条件|示例|
|-|-|-|
|detail_type|所有事件必须|"group"/"private"|
|sub_type|需要细分时|"invite"/"leave"|
|message_id|消息事件|"msg_123"|
|user_id|涉及用户|"user_456"|
|group_id|群组事件|"group_789"|

### 2.3 非标准字段（非必须，但建议实现）
|字段|触发类型|示例|
|-|-|-|
|user_nickname|涉及用户|"用户昵称"|

## 3. 完整事件模板
### 3.1 消息事件 (message)
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "sub_type": "",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message_id": "msg_abc",
  "message": [
    {
      "type": "text",
      "data": {"text": "你好"}
    },
    {
      "type": "image",
      "data": {
        "file_id": "img_xyz",
        "url": "https://example.com/image.jpg",
        "file_name": "example.jpg",
        "size": 102400,
        "width": 800,
        "height": 600
      }
    }
  ],
  "alt_message": "你好[图片]",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  }
}
```
### 3.2 通知事件 (notice)
```json
{
  "id": "event_456",
  "time": 1752241221,
  "type": "notice",
  "detail_type": "group_member_increase",
  "sub_type": "invite",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
}
```
### 3.3 请求事件 (request)
```json
{
  "id": "event_789",
  "time": 1752241222,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "请加好友",
  "onebot11_raw": {...},
}
```
## 4. 消息段标准
### 4.1 通用消息段
|类型|必填字段|扩展字段|
|-|-|-|
|text|text|-|
|image|url|file_name, size, width, height|
|video|url|duration, file_name|
|file|url|size, file_name|

## 5. 错误处理规范
### 5.1 字段缺失处理
```python
def safe_get(data: dict, key: str, default=None):
    """安全获取字段并记录警告"""
    if key not in data:
        logger.warning(f"Missing field '{key}' in {data.get('eventType', 'unknown')}")
    return data.get(key, default)
```
### 5.2 未知事件处理
```json
{
  "id": "event_999",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```
## 6. 时间戳转换标准
```python
def convert_timestamp(ts: Any) -> int:
    """标准化时间戳处理"""
    if isinstance(ts, str):
        if len(ts) == 13:  # 毫秒级
            return int(ts) // 1000
        return int(ts)
    elif isinstance(ts, (int, float)):
        if ts > 9999999999:  # 毫秒级
            return int(ts // 1000)
        return int(ts)
    return int(time.time())  # 默认当前时间
```
## 7. 适配器实现检查清单
- [ ] 所有标准字段已正确映射
- [ ] 平台特有字段已添加前缀
- [ ] 时间戳已转换为10位秒级
- [ ] 原始数据保存在 {platform}_raw
- [ ] 消息段的 alt_message 已生成
- [ ] 所有事件类型已通过单元测试
- [ ] 文档包含完整示例和说明
## 8. 最佳实践示例
### 云湖表单消息处理
```python
def _convert_form_message(self, raw_form: dict) -> dict:
    """转换表单消息为标准格式"""
    return {
        "type": "yunhu_form",
        "data": {
            "id": raw_form.get("formId"),
            "fields": [
                {
                    "id": field.get("fieldId"),
                    "type": field.get("fieldType"),
                    "label": field.get("label"),
                    "value": field.get("value")
                }
                for field in raw_form.get("fields", [])
            ]
        }
    }
```
### 消息ID生成规则
```python
def generate_message_id(platform: str, raw_id: str) -> str:
    """标准化消息ID格式"""
    return f"{platform}_msg_{raw_id}" if raw_id else f"{platform}_msg_{uuid.uuid4()}"
```
本规范确保所有适配器：
1. 保持与OneBot12的完全兼容性
2. 平台特有功能可识别且不冲突
3. 转换过程可追溯（通过_raw字段）
4. 数据类型和格式统一
建议配合自动化测试验证所有转换场景，特别是：
- 边界值测试（如空消息、超大文件）
- 特殊字符测试（消息内容含emoji/特殊符号）
- 压力测试（连续事件转换）

<!--- End of EventConversion.md -->

<!-- API文档 -->

# API参考

## README.md

# ErisPulse API 文档

这个文档的内容是由 ErisPulse 核心模块API生成器 自动生成的。它们包含所有核心模块的API文档。


## ErisPulse\__init__.md

# 📦 `ErisPulse.__init__` 模块

*自动生成于 2025-07-22 16:35:31*

---

## 模块概述

ErisPulse SDK 主模块

提供SDK核心功能模块加载和初始化功能

💡 **提示**：

1. 使用前请确保已正确安装所有依赖
2. 调用sdk.init()进行初始化
3. 模块加载采用懒加载机制

---

## 🛠️ 函数

### `init_progress`

初始化项目环境文件

1. 检查并创建main.py入口文件
2. 确保基础目录结构存在

:return: bool 是否创建了新的main.py文件

💡 **提示**：

1. 如果main.py已存在则不会覆盖
2. 此方法通常由SDK内部调用

---

### `_prepare_environment`

⚠️ **内部方法**：

准备运行环境

1. 初始化项目环境文件
2. 加载环境变量配置

:return: bool 环境准备是否成功

---

### `init`

SDK初始化入口

执行步骤:
1. 准备运行环境
2. 初始化所有模块和适配器

:return: bool SDK初始化是否成功

💡 **提示**：

1. 这是SDK的主要入口函数
2. 如果初始化失败会抛出InitError异常
3. 建议在main.py中调用此函数

⚠️ **可能抛出**: `InitError` - 当初始化失败时抛出

---

### `load_module`

手动加载指定模块

:param module_name: str 要加载的模块名称
:return: bool 加载是否成功

💡 **提示**：

1. 可用于手动触发懒加载模块的初始化
2. 如果模块不存在或已加载会返回False

---

## 🏛️ 类

### `LazyModule`

懒加载模块包装器

当模块第一次被访问时才进行实例化

💡 **提示**：

1. 模块的实际实例化会在第一次属性访问时进行
2. 依赖模块会在被使用时自动初始化


#### 🧰 方法

##### `__init__`

初始化懒加载包装器

:param module_name: str 模块名称
:param module_class: Type 模块类
:param sdk_ref: Any SDK引用
:param module_info: Dict[str, Any] 模块信息字典

---

##### `_initialize`

实际初始化模块

⚠️ **可能抛出**: `LazyLoadError` - 当模块初始化失败时抛出

---

##### `__getattr__`

属性访问时触发初始化

:param name: str 要访问的属性名
:return: Any 模块属性值

---

##### `__call__`

调用时触发初始化

:param args: 位置参数
:param kwargs: 关键字参数
:return: Any 模块调用结果

---

##### `__bool__`

判断模块布尔值时触发初始化

:return: bool 模块布尔值

---

##### `__str__`

转换为字符串时触发初始化

:return: str 模块字符串表示

---

##### `__copy__`

浅拷贝时返回自身，保持懒加载特性

:return: self

---

##### `__deepcopy__`

深拷贝时返回自身，保持懒加载特性

:param memo: memo
:return: self

---

### `AdapterLoader`

适配器加载器

专门用于从PyPI包加载和初始化适配器

💡 **提示**：

1. 适配器必须通过entry-points机制注册到erispulse.adapter组
2. 适配器类必须继承BaseAdapter
3. 适配器不适用懒加载


#### 🧰 方法

##### `load`

从PyPI包entry-points加载适配器

:return: 
    Dict[str, object]: 适配器对象字典 {适配器名: 模块对象}
    List[str]: 启用的适配器名称列表
    List[str]: 停用的适配器名称列表
    
⚠️ **可能抛出**: `ImportError` - 当无法加载适配器时抛出

---

##### `_process_adapter`

⚠️ **内部方法**：

处理单个适配器entry-point

:param entry_point: entry-point对象
:param adapter_objs: 适配器对象字典
:param enabled_adapters: 启用的适配器列表
:param disabled_adapters: 停用的适配器列表

:return: 
    Dict[str, object]: 更新后的适配器对象字典
    List[str]: 更新后的启用适配器列表 
    List[str]: 更新后的禁用适配器列表
    
⚠️ **可能抛出**: `ImportError` - 当适配器加载失败时抛出

---

### `ModuleLoader`

模块加载器

专门用于从PyPI包加载和初始化普通模块

💡 **提示**：

1. 模块必须通过entry-points机制注册到erispulse.module组
2. 模块类名应与entry-point名称一致


#### 🧰 方法

##### `load`

从PyPI包entry-points加载模块

:return: 
    Dict[str, object]: 模块对象字典 {模块名: 模块对象}
    List[str]: 启用的模块名称列表
    List[str]: 停用的模块名称列表
    
⚠️ **可能抛出**: `ImportError` - 当无法加载模块时抛出

---

##### `_process_module`

⚠️ **内部方法**：

处理单个模块entry-point

:param entry_point: entry-point对象
:param module_objs: 模块对象字典
:param enabled_modules: 启用的模块列表
:param disabled_modules: 停用的模块列表

:return: 
    Dict[str, object]: 更新后的模块对象字典
    List[str]: 更新后的启用模块列表 
    List[str]: 更新后的禁用模块列表
    
⚠️ **可能抛出**: `ImportError` - 当模块加载失败时抛出

---

##### `_should_lazy_load`

检查模块是否应该懒加载

:param module_class: Type 模块类
:return: bool 如果返回 False，则立即加载；否则懒加载

---

### `ModuleInitializer`

模块初始化器

负责协调适配器和模块的初始化流程

💡 **提示**：

1. 初始化顺序：适配器 → 模块
2. 模块初始化采用懒加载机制


#### 🧰 方法

##### `init`

初始化所有模块和适配器

执行步骤:
1. 从PyPI包加载适配器
2. 从PyPI包加载模块
3. 预记录所有模块信息
4. 注册适配器
5. 初始化各模块

:return: bool 初始化是否成功
⚠️ **可能抛出**: `InitError` - 当初始化失败时抛出

---

##### `_initialize_modules`

⚠️ **内部方法**：

初始化模块

:param modules: List[str] 模块名称列表
:param module_objs: Dict[str, Any] 模块对象字典

:return: bool 模块初始化是否成功

---

##### `_register_adapters`

⚠️ **内部方法**：

注册适配器

:param adapters: List[str] 适配器名称列表
:param adapter_objs: Dict[str, Any] 适配器对象字典

:return: bool 适配器注册是否成功

---


*文档最后更新于 2025-07-22 16:35:31*

## ErisPulse\__main__.md

# 📦 `ErisPulse.__main__` 模块

*自动生成于 2025-07-22 16:35:31*

---

## 模块概述

ErisPulse SDK 命令行工具

提供ErisPulse生态系统的包管理、模块控制和开发工具功能。

💡 **提示**：

1. 需要Python 3.8+环境
2. Windows平台需要colorama支持ANSI颜色

---

## 🛠️ 函数

### `main`

CLI入口点

💡 **提示**：

1. 创建CLI实例并运行
2. 处理全局异常

---

## 🏛️ 类

### `CommandHighlighter`

高亮CLI命令和参数

💡 **提示**：

使用正则表达式匹配命令行参数和选项


### `PackageManager`

ErisPulse包管理器

提供包安装、卸载、升级和查询功能

💡 **提示**：

1. 支持本地和远程包管理
2. 包含1小时缓存机制


#### 🧰 方法

##### `__init__`

初始化包管理器

---

##### 🔹 `async` `_fetch_remote_packages`

从指定URL获取远程包数据

:param url: 远程包数据URL
:return: 解析后的JSON数据，失败返回None

⚠️ **可能抛出**: `ClientError` - 网络请求失败时抛出
⚠️ **可能抛出**: `JSONDecodeError` - JSON解析失败时抛出

---

##### 🔹 `async` `get_remote_packages`

获取远程包列表，带缓存机制

:param force_refresh: 是否强制刷新缓存
:return: 包含模块和适配器的字典

:return:
    dict: {
        "modules": {模块名: 模块信息},
        "adapters": {适配器名: 适配器信息},
        "cli_extensions": {扩展名: 扩展信息}
    }

---

##### `get_installed_packages`

获取已安装的包信息

:return: 已安装包字典，包含模块、适配器和CLI扩展

:return:
    dict: {
        "modules": {模块名: 模块信息},
        "adapters": {适配器名: 适配器信息},
        "cli_extensions": {扩展名: 扩展信息}
    }

---

##### `_is_module_enabled`

检查模块是否启用

:param module_name: 模块名称
:return: 模块是否启用

⚠️ **可能抛出**: `ImportError` - 核心模块不可用时抛出

---

##### `_run_pip_command`

执行pip命令

:param args: pip命令参数列表
:param description: 进度条描述
:return: 命令是否成功执行

---

##### `install_package`

安装指定包

:param package_name: 要安装的包名
:param upgrade: 是否升级已安装的包
:return: 安装是否成功

---

##### `uninstall_package`

卸载指定包

:param package_name: 要卸载的包名
:return: 卸载是否成功

---

##### `upgrade_all`

升级所有已安装的ErisPulse包

:return: 升级是否成功

⚠️ **可能抛出**: `KeyboardInterrupt` - 用户取消操作时抛出

---

### `ReloadHandler`

文件系统事件处理器

实现热重载功能，监控文件变化并重启进程

💡 **提示**：

1. 支持.py文件修改重载
2. 支持配置文件修改重载


#### 🧰 方法

##### `__init__`

初始化处理器

:param script_path: 要监控的脚本路径
:param reload_mode: 是否启用重载模式

---

##### `start_process`

启动监控进程

---

##### `_terminate_process`

终止当前进程

:raises subprocess.TimeoutExpired: 进程终止超时时抛出

---

##### `on_modified`

文件修改事件处理

:param event: 文件系统事件

---

##### `_handle_reload`

处理重载逻辑

:param event: 文件系统事件
:param reason: 重载原因描述

---

### `CLI`

ErisPulse命令行接口

提供完整的命令行交互功能

💡 **提示**：

1. 支持动态加载第三方命令
2. 支持模块化子命令系统


#### 🧰 方法

##### `__init__`

初始化CLI

---

##### `_create_parser`

创建命令行参数解析器

:return: 配置好的ArgumentParser实例

---

##### `_load_external_commands`

加载第三方CLI命令

:param subparsers: 子命令解析器

⚠️ **可能抛出**: `ImportError` - 加载命令失败时抛出

---

##### `_print_version`

打印版本信息

---

##### `_print_installed_packages`

打印已安装包信息

:param pkg_type: 包类型 (modules/adapters/cli/all)
:param outdated_only: 是否只显示可升级的包

---

##### `_print_remote_packages`

打印远程包信息

:param pkg_type: 包类型 (modules/adapters/cli/all)

---

##### `_is_package_outdated`

检查包是否过时

:param package_name: 包名
:param current_version: 当前版本
:return: 是否有新版本可用

---

##### `_resolve_package_name`

解析简称到完整包名

:param short_name: 模块/适配器简称
:return: 完整包名，未找到返回None

---

##### `_setup_watchdog`

设置文件监控

:param script_path: 要监控的脚本路径
:param reload_mode: 是否启用重载模式

---

##### `_cleanup`

清理资源

---

##### `run`

运行CLI

⚠️ **可能抛出**: `KeyboardInterrupt` - 用户中断时抛出
⚠️ **可能抛出**: `Exception` - 命令执行失败时抛出

---


*文档最后更新于 2025-07-22 16:35:31*

## ErisPulse\Core\adapter.md

# 📦 `ErisPulse.Core.adapter` 模块

*自动生成于 2025-07-22 16:35:31*

---

## 模块概述

ErisPulse 适配器系统

提供平台适配器基类、消息发送DSL和适配器管理功能。支持多平台消息处理、事件驱动和生命周期管理。

💡 **提示**：

1. 适配器必须继承BaseAdapter并实现必要方法
2. 使用SendDSL实现链式调用风格的消息发送接口
3. 适配器管理器支持多平台适配器的注册和生命周期管理
4. 支持OneBot12协议的事件处理

---

## 🏛️ 类

### `SendDSLBase`

消息发送DSL基类

用于实现 Send.To(...).Func(...) 风格的链式调用接口

💡 **提示**：

1. 子类应实现具体的消息发送方法(如Text, Image等)
2. 通过__getattr__实现动态方法调用


#### 🧰 方法

##### `__init__`

初始化DSL发送器

:param adapter: 所属适配器实例
:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:param _account_id: 发送账号(可选)

---

##### `To`

设置消息目标

:param target_type: 目标类型(可选)
:param target_id: 目标ID(可选)
:return: SendDSL实例

:example:
>>> adapter.Send.To("user", "123").Text("Hello")
>>> adapter.Send.To("123").Text("Hello")  # 简化形式

---

##### `Using`

设置发送账号

:param _account_id: 发送账号
:return: SendDSL实例

:example:
>>> adapter.Send.Using("bot1").To("123").Text("Hello")
>>> adapter.Send.To("123").Using("bot1").Text("Hello")  # 支持乱序

---

### `BaseAdapter`

适配器基类

提供与外部平台交互的标准接口，子类必须实现必要方法

💡 **提示**：

1. 必须实现call_api, start和shutdown方法
2. 可以自定义Send类实现平台特定的消息发送逻辑
3. 通过on装饰器注册事件处理器
4. 支持OneBot12协议的事件处理


#### 🧰 方法

##### `__init__`

初始化适配器

---

##### `on`

适配器事件监听装饰器

:param event_type: 事件类型
:return: 装饰器函数

---

##### `middleware`

添加中间件处理器

:param func: 中间件函数
:return: 中间件函数

:example:
>>> @adapter.middleware
>>> async def log_middleware(data):
>>>     print(f"处理数据: {data}")
>>>     return data

---

##### 🔹 `async` `call_api`

调用平台API的抽象方法

:param endpoint: API端点
:param params: API参数
:return: API调用结果
⚠️ **可能抛出**: `NotImplementedError` - 必须由子类实现

---

##### 🔹 `async` `start`

启动适配器的抽象方法

⚠️ **可能抛出**: `NotImplementedError` - 必须由子类实现

---

##### 🔹 `async` `shutdown`

关闭适配器的抽象方法

⚠️ **可能抛出**: `NotImplementedError` - 必须由子类实现

---

##### 🔹 `async` `emit`

触发原生协议事件

:param event_type: 事件类型
:param data: 事件数据

:example:
>>> await adapter.emit("message", {"text": "Hello"})

---

##### 🔹 `async` `send`

发送消息的便捷方法

:param target_type: 目标类型
:param target_id: 目标ID
:param message: 消息内容
:param kwargs: 其他参数
    - method: 发送方法名(默认为"Text")
:return: 发送结果

⚠️ **可能抛出**: `AttributeError` - 当发送方法不存在时抛出
    
:example:
>>> await adapter.send("user", "123", "Hello")
>>> await adapter.send("group", "456", "Hello", method="Markdown")

---

### `AdapterManager`

适配器管理器

管理多个平台适配器的注册、启动和关闭

💡 **提示**：

1. 通过register方法注册适配器
2. 通过startup方法启动适配器
3. 通过shutdown方法关闭所有适配器
4. 通过on装饰器注册OneBot12协议事件处理器


#### 🧰 方法

##### `Adapter`

获取BaseAdapter类，用于访问原始事件监听

:return: BaseAdapter类

:example:
>>> @sdk.adapter.Adapter.on("raw_event")
>>> async def handle_raw(data):
>>>     print("收到原始事件:", data)

---

##### `on`

OneBot12协议事件监听装饰器

:param event_type: OneBot12事件类型
:return: 装饰器函数

:example:
>>> @sdk.adapter.on("message")
>>> async def handle_message(data):
>>>     print(f"收到OneBot12消息: {data}")

---

##### `middleware`

添加OneBot12中间件处理器

:param func: 中间件函数
:return: 中间件函数

:example:
>>> @sdk.adapter.middleware
>>> async def onebot_middleware(data):
>>>     print("处理OneBot12数据:", data)
>>>     return data

---

##### 🔹 `async` `emit`

提交OneBot12协议事件到指定平台

:param platform: 平台名称
:param event_type: OneBot12事件类型
:param data: 符合OneBot12标准的事件数据

⚠️ **可能抛出**: `ValueError` - 当平台未注册时抛出
    
:example:
>>> await sdk.adapter.emit("MyPlatform", "message", {
>>>     "id": "123",
>>>     "time": 1620000000,
>>>     "type": "message",
>>>     "detail_type": "private",
>>>     "message": [{"type": "text", "data": {"text": "Hello"}}]
>>> })

---

##### `register`

注册新的适配器类

:param platform: 平台名称
:param adapter_class: 适配器类
:return: 注册是否成功

⚠️ **可能抛出**: `TypeError` - 当适配器类无效时抛出
    
:example:
>>> adapter.register("MyPlatform", MyPlatformAdapter)

---

##### 🔹 `async` `startup`

启动指定的适配器

:param platforms: 要启动的平台列表，None表示所有平台

⚠️ **可能抛出**: `ValueError` - 当平台未注册时抛出
    
:example:
>>> # 启动所有适配器
>>> await adapter.startup()
>>> # 启动指定适配器
>>> await adapter.startup(["Platform1", "Platform2"])

---

##### 🔹 `async` `_run_adapter`

⚠️ **内部方法**：

运行适配器实例

:param adapter: 适配器实例
:param platform: 平台名称

---

##### 🔹 `async` `shutdown`

关闭所有适配器

:example:
>>> await adapter.shutdown()

---

##### `get`

获取指定平台的适配器实例

:param platform: 平台名称
:return: 适配器实例或None
    
:example:
>>> adapter = adapter.get("MyPlatform")

---

##### `__getattr__`

通过属性访问获取适配器实例

:param platform: 平台名称
:return: 适配器实例

⚠️ **可能抛出**: `AttributeError` - 当平台未注册时抛出
    
:example:
>>> adapter = adapter.MyPlatform

---

##### `platforms`

获取所有已注册的平台列表

:return: 平台名称列表
    
:example:
>>> print("已注册平台:", adapter.platforms)

---


*文档最后更新于 2025-07-22 16:35:31*

## ErisPulse\Core\config.md

# 📦 `ErisPulse.Core.config` 模块

*自动生成于 2025-07-22 16:35:31*

---

## 模块概述

ErisPulse 配置中心

集中管理所有配置项，避免循环导入问题
提供自动补全缺失配置项的功能

---

## 🛠️ 函数

### `_ensure_config_structure`

确保配置结构完整，补全缺失的配置项

:param config: 当前配置
:return: 补全后的完整配置

---

### `get_config`

获取当前配置，自动补全缺失的配置项并保存

:return: 完整的配置字典

---

### `update_config`

更新配置，自动补全缺失的配置项

:param new_config: 新的配置字典
:return: 是否更新成功

---

### `get_server_config`

获取服务器配置，确保结构完整

:return: 服务器配置字典

---

### `get_logger_config`

获取日志配置，确保结构完整

:return: 日志配置字典

---


*文档最后更新于 2025-07-22 16:35:31*

## ErisPulse\Core\env.md

# 📦 `ErisPulse.Core.env` 模块

*自动生成于 2025-07-22 16:35:31*

---

## 模块概述

ErisPulse 环境配置模块

提供键值存储、事务支持、快照和恢复功能，用于管理框架配置数据。基于SQLite实现持久化存储，支持复杂数据类型和原子操作。

💡 **提示**：

1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 自动快照功能防止数据丢失

---

## 🏛️ 类

### `EnvManager`

环境配置管理器

单例模式实现，提供配置的增删改查、事务和快照管理

💡 **提示**：

1. 使用get/set方法操作配置项
2. 使用transaction上下文管理事务
3. 使用snapshot/restore管理数据快照


#### 🧰 方法

##### `_init_db`

⚠️ **内部方法**：

初始化数据库

---

##### `get`

获取配置项的值

:param key: 配置项键名
:param default: 默认值(当键不存在时返回)
:return: 配置项的值

:example:
>>> timeout = env.get("network.timeout", 30)
>>> user_settings = env.get("user.settings", {})

---

##### `get_all_keys`

获取所有配置项的键名

:return: 键名列表

:example:
>>> all_keys = env.get_all_keys()
>>> print(f"共有 {len(all_keys)} 个配置项")

---

##### `set`

设置配置项的值

:param key: 配置项键名
:param value: 配置项的值
:return: 操作是否成功

:example:
>>> env.set("app.name", "MyApp")
>>> env.set("user.settings", {"theme": "dark"})

---

##### `set_multi`

批量设置多个配置项

:param items: 键值对字典
:return: 操作是否成功

:example:
>>> env.set_multi({
>>>     "app.name": "MyApp",
>>>     "app.version": "1.0.0",
>>>     "app.debug": True
>>> })

---

##### `getConfig`

获取模块/适配器配置项
:param key: 配置项的键(支持点分隔符如"module.sub.key")
:param default: 默认值
:return: 配置项的值

---

##### `setConfig`

设置模块/适配器配置
:param key: 配置项键名(支持点分隔符如"module.sub.key")
:param value: 配置项值
:return: 操作是否成功

---

##### `delete`

删除配置项

:param key: 配置项键名
:return: 操作是否成功

:example:
>>> env.delete("temp.session")

---

##### `delete_multi`

批量删除多个配置项

:param keys: 键名列表
:return: 操作是否成功

:example:
>>> env.delete_multi(["temp.key1", "temp.key2"])

---

##### `get_multi`

批量获取多个配置项的值

:param keys: 键名列表
:return: 键值对字典

:example:
>>> settings = env.get_multi(["app.name", "app.version"])

---

##### `transaction`

创建事务上下文

:return: 事务上下文管理器

:example:
>>> with env.transaction():
>>>     env.set("key1", "value1")
>>>     env.set("key2", "value2")

---

##### `_check_auto_snapshot`

⚠️ **内部方法**：

检查并执行自动快照

---

##### `set_snapshot_interval`

设置自动快照间隔

:param seconds: 间隔秒数

:example:
>>> # 每30分钟自动快照
>>> env.set_snapshot_interval(1800)

---

##### `clear`

清空所有配置项

:return: 操作是否成功

:example:
>>> env.clear()  # 清空所有配置

---

##### `load_env_file`

加载env.py文件中的配置项

:return: 操作是否成功

:example:
>>> env.load_env_file()  # 加载env.py中的配置

---

##### `__getattr__`

通过属性访问配置项

:param key: 配置项键名
:return: 配置项的值

⚠️ **可能抛出**: `KeyError` - 当配置项不存在时抛出
    
:example:
>>> app_name = env.app_name

---

##### `__setattr__`

通过属性设置配置项

:param key: 配置项键名
:param value: 配置项的值
    
:example:
>>> env.app_name = "MyApp"

---

##### `snapshot`

创建数据库快照

:param name: 快照名称(可选)
:return: 快照文件路径

:example:
>>> # 创建命名快照
>>> snapshot_path = env.snapshot("before_update")
>>> # 创建时间戳快照
>>> snapshot_path = env.snapshot()

---

##### `restore`

从快照恢复数据库

:param snapshot_name: 快照名称或路径
:return: 恢复是否成功

:example:
>>> env.restore("before_update")

---

##### `list_snapshots`

列出所有可用的快照

:return: 快照信息列表(名称, 创建时间, 大小)

:example:
>>> for name, date, size in env.list_snapshots():
>>>     print(f"{name} - {date} ({size} bytes)")

---

##### `delete_snapshot`

删除指定的快照

:param snapshot_name: 快照名称
:return: 删除是否成功

:example:
>>> env.delete_snapshot("old_backup")

---


*文档最后更新于 2025-07-22 16:35:31*

## ErisPulse\Core\logger.md

# 📦 `ErisPulse.Core.logger` 模块

*自动生成于 2025-07-22 16:35:31*

---

## 模块概述

ErisPulse 日志系统

提供模块化日志记录功能，支持多级日志、模块过滤和内存存储。

💡 **提示**：

1. 支持按模块设置不同日志级别
2. 日志可存储在内存中供后续分析
3. 自动识别调用模块名称

---

## 🏛️ 类

### `Logger`

日志管理器

提供模块化日志记录和存储功能

💡 **提示**：

1. 使用set_module_level设置模块日志级别
2. 使用get_logs获取历史日志
3. 支持标准日志级别(DEBUG, INFO等)


#### 🧰 方法

##### `set_memory_limit`

设置日志内存存储上限

:param limit: 日志存储上限
:return: bool 设置是否成功

---

##### `set_level`

设置全局日志级别

:param level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
:return: bool 设置是否成功

---

##### `set_module_level`

设置指定模块日志级别

:param module_name: 模块名称
:param level: 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
:return: bool 设置是否成功

---

##### `set_output_file`

设置日志输出

:param path: 日志文件路径 Str/List
:return: bool 设置是否成功

---

##### `save_logs`

保存所有在内存中记录的日志

:param path: 日志文件路径 Str/List
:return: bool 设置是否成功

---

##### `get_logs`

获取日志内容

:param module_name (可选): 模块名称
:return: dict 日志内容

---


*文档最后更新于 2025-07-22 16:35:31*

## ErisPulse\Core\mods.md

# 📦 `ErisPulse.Core.mods` 模块

*自动生成于 2025-07-22 16:35:31*

---

## 模块概述

ErisPulse 模块管理器

提供模块的注册、状态管理和依赖关系处理功能。支持模块的启用/禁用、版本控制和依赖解析。

💡 **提示**：

1. 使用模块前缀区分不同模块的配置
2. 支持模块状态持久化存储
3. 自动处理模块间的依赖关系

---

## 🏛️ 类

### `ModuleManager`

模块管理器

管理所有模块的注册、状态和依赖关系

💡 **提示**：

1. 通过set_module/get_module管理模块信息
2. 通过set_module_status/get_module_status控制模块状态
3. 通过set_all_modules/get_all_modules批量操作模块


#### 🧰 方法

##### `_ensure_prefixes`

⚠️ **内部方法**：

确保模块前缀配置存在

---

##### `module_prefix`

获取模块数据前缀

:return: 模块数据前缀字符串

---

##### `status_prefix`

获取模块状态前缀

:return: 模块状态前缀字符串

---

##### `set_module_status`

设置模块启用状态

:param module_name: 模块名称
:param status: 启用状态

:example:
>>> # 启用模块
>>> mods.set_module_status("MyModule", True)
>>> # 禁用模块
>>> mods.set_module_status("MyModule", False)

---

##### `get_module_status`

获取模块启用状态

:param module_name: 模块名称
:return: 模块是否启用

:example:
>>> if mods.get_module_status("MyModule"):
>>>     print("模块已启用")

---

##### `set_module`

设置模块信息

:param module_name: 模块名称
:param module_info: 模块信息字典

:example:
>>> mods.set_module("MyModule", {
>>>     "version": "1.0.0",
>>>     "description": "我的模块",
>>> })

---

##### `get_module`

获取模块信息

:param module_name: 模块名称
:return: 模块信息字典或None

:example:
>>> module_info = mods.get_module("MyModule")
>>> if module_info:
>>>     print(f"模块版本: {module_info.get('version')}")

---

##### `set_all_modules`

批量设置多个模块信息

:param modules_info: 模块信息字典

:example:
>>> mods.set_all_modules({
>>>     "Module1": {"version": "1.0", "status": True},
>>>     "Module2": {"version": "2.0", "status": False}
>>> })

---

##### `get_all_modules`

获取所有模块信息

:return: 模块信息字典

:example:
>>> all_modules = mods.get_all_modules()
>>> for name, info in all_modules.items():
>>>     print(f"{name}: {info.get('status')}")

---

##### `update_module`

更新模块信息

:param module_name: 模块名称
:param module_info: 完整的模块信息字典

---

##### `remove_module`

移除模块

:param module_name: 模块名称
:return: 是否成功移除

:example:
>>> if mods.remove_module("OldModule"):
>>>     print("模块已移除")

---

##### `update_prefixes`

更新模块前缀配置

:param module_prefix: 新的模块数据前缀(可选)
:param status_prefix: 新的模块状态前缀(可选)

:example:
>>> # 更新模块前缀
>>> mods.update_prefixes(
>>>     module_prefix="custom.module.data:",
>>>     status_prefix="custom.module.status:"
>>> )

---


*文档最后更新于 2025-07-22 16:35:31*

## ErisPulse\Core\raiserr.md

# 📦 `ErisPulse.Core.raiserr` 模块

*自动生成于 2025-07-22 16:35:32*

---

## 模块概述

ErisPulse 错误管理系统

提供全局异常捕获功能。不再推荐使用自定义错误注册功能。

💡 **提示**：

1. 请使用Python原生异常抛出方法
2. 系统会自动捕获并格式化所有未处理异常
3. 注册功能已标记为弃用，将在未来版本移除

---

## 🛠️ 函数

### `global_exception_handler`

全局异常处理器

:param exc_type: 异常类型
:param exc_value: 异常值
:param exc_traceback: 追踪信息

---

### `async_exception_handler`

异步异常处理器

:param loop: 事件循环
:param context: 上下文字典

---

## 🏛️ 类

### `Error`

错误管理器

⚠️ **已弃用**：请使用Python原生异常抛出方法 | 2025-07-18

💡 **提示**：

1. 注册功能将在未来版本移除
2. 请直接使用raise Exception("message")方式抛出异常


#### 🧰 方法

##### `register`

注册新的错误类型

⚠️ **已弃用**：请使用Python原生异常抛出方法 | 2025-07-18

:param name: 错误类型名称
:param doc: 错误描述文档
:param base: 基础异常类
:return: 注册的错误类

---

##### `__getattr__`

动态获取错误抛出函数

⚠️ **已弃用**：请使用Python原生异常抛出方法 | 2025-07-18

:param name: 错误类型名称
:return: 错误抛出函数

⚠️ **可能抛出**: `AttributeError` - 当错误类型未注册时抛出

---

##### `info`

获取错误信息

⚠️ **已弃用**：此功能将在未来版本移除 | 2025-07-18

:param name: 错误类型名称(可选)
:return: 错误信息字典

---


*文档最后更新于 2025-07-22 16:35:32*

## ErisPulse\Core\server.md

# 📦 `ErisPulse.Core.server` 模块

*自动生成于 2025-07-22 16:35:32*

---

## 模块概述

ErisPulse Adapter Server
提供统一的适配器服务入口，支持HTTP和WebSocket路由

💡 **提示**：

1. 适配器只需注册路由，无需自行管理服务器
2. WebSocket支持自定义认证逻辑
3. 兼容FastAPI 0.68+ 版本

---

## 🏛️ 类

### `AdapterServer`

适配器服务器管理器

💡 **提示**：

核心功能：
- HTTP/WebSocket路由注册
- 生命周期管理
- 统一错误处理


#### 🧰 方法

##### `__init__`

初始化适配器服务器

💡 **提示**：

会自动创建FastAPI实例并设置核心路由

---

##### `_setup_core_routes`

设置系统核心路由

⚠️ **内部方法**：

此方法仅供内部使用
{!--< /internal-use >!--}

---

##### `register_webhook`

注册HTTP路由

:param adapter_name: str 适配器名称
:param path: str 路由路径(如"/message")
:param handler: Callable 处理函数
:param methods: List[str] HTTP方法列表(默认["POST"])

⚠️ **可能抛出**: `ValueError` - 当路径已注册时抛出

💡 **提示**：

路径会自动添加适配器前缀，如：/adapter_name/path

---

##### `register_websocket`

注册WebSocket路由

:param adapter_name: str 适配器名称
:param path: str WebSocket路径(如"/ws")
:param handler: Callable[[WebSocket], Awaitable[Any]] 主处理函数
:param auth_handler: Optional[Callable[[WebSocket], Awaitable[bool]]] 认证函数

⚠️ **可能抛出**: `ValueError` - 当路径已注册时抛出

💡 **提示**：

认证函数应返回布尔值，False将拒绝连接

---

##### `get_app`

获取FastAPI应用实例

:return: 
    FastAPI: FastAPI应用实例

---

##### 🔹 `async` `start`

启动适配器服务器

:param host: str 监听地址(默认"0.0.0.0")
:param port: int 监听端口(默认8000)
:param ssl_certfile: Optional[str] SSL证书路径
:param ssl_keyfile: Optional[str] SSL密钥路径

⚠️ **可能抛出**: `RuntimeError` - 当服务器已在运行时抛出

---

##### 🔹 `async` `stop`

停止服务器

💡 **提示**：

会等待所有连接正常关闭

---


*文档最后更新于 2025-07-22 16:35:32*

## ErisPulse\Core\util.md

# 📦 `ErisPulse.Core.util` 模块

*自动生成于 2025-07-22 16:35:32*

---

## 模块概述

ErisPulse 工具函数集合

提供常用工具函数，包括拓扑排序、缓存装饰器、异步执行等实用功能。

💡 **提示**：

1. 使用@cache装饰器缓存函数结果
2. 使用@run_in_executor在独立线程中运行同步函数
3. 使用@retry实现自动重试机制

---

## 🏛️ 类

### `Util`

工具函数集合

提供各种实用功能，简化开发流程

💡 **提示**：

1. 拓扑排序用于解决依赖关系
2. 装饰器简化常见模式实现
3. 异步执行提升性能


#### 🧰 方法

##### `ExecAsync`

异步执行函数

:param async_func: 异步函数
:param args: 位置参数
:param kwargs: 关键字参数
:return: 函数执行结果

:example:
>>> result = util.ExecAsync(my_async_func, arg1, arg2)

---

##### `cache`

缓存装饰器

:param func: 被装饰函数
:return: 装饰后的函数

:example:
>>> @util.cache
>>> def expensive_operation(param):
>>>     return heavy_computation(param)

---

##### `run_in_executor`

在独立线程中执行同步函数的装饰器

:param func: 被装饰的同步函数
:return: 可等待的协程函数

:example:
>>> @util.run_in_executor
>>> def blocking_io():
>>>     # 执行阻塞IO操作
>>>     return result

---

##### `retry`

自动重试装饰器

:param max_attempts: 最大重试次数 (默认: 3)
:param delay: 重试间隔(秒) (默认: 1)
:return: 装饰器函数

:example:
>>> @util.retry(max_attempts=5, delay=2)
>>> def unreliable_operation():
>>>     # 可能失败的操作

---


*文档最后更新于 2025-07-22 16:35:32*

<!--- End of API文档 -->
