# 邮件平台特性文档

EmailAdapter 是基于 SMTP/IMAP 协议的邮件适配器，支持邮件发送、接收和处理。

---

## 文档信息

- 对应模块版本: 4.1.0
- 维护者: ErisPulse

## 基本信息

- 平台简介：通过标准 SMTP/IMAP 协议收发邮件的通用适配器
- 适配器名称：EmailAdapter
- 多账户支持：支持同时配置多个邮箱账户
- 连接方式：IMAP 长轮询接收 + SMTP 发送
- 认证方式：邮箱地址 + 密码/授权码
- OneBot12 兼容：支持发送 OneBot12 格式消息

## 配置说明

### 全局配置（EmailAdapter）

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `imap_server` | str | `imap.example.com` | 默认 IMAP 服务器地址 |
| `imap_port` | int | `993` | 默认 IMAP 端口 |
| `smtp_server` | str | `smtp.example.com` | 默认 SMTP 服务器地址 |
| `smtp_port` | int | `465` | 默认 SMTP 端口 |
| `ssl` | bool | `true` | 是否默认启用 SSL |
| `timeout` | int | `30` | 默认连接超时（秒） |
| `poll_interval` | int | `60` | IMAP 轮询间隔（秒） |
| `max_retries` | int | `3` | 连接失败最大重试次数 |

### 账户配置（EmailAdapter.accounts）

每个账户对应一个独立邮箱。账户级配置优先于全局配置。

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # 可选，留空使用全局默认
imap_port = 993                      # 可选
smtp_server = "smtp.example.com"    # 可选
smtp_port = 465                      # 可选
ssl = true                           # 可选
timeout = 30                         # 可选
enabled = true

[EmailAdapter.accounts.backup]
email = "backup@example.com"
password = "another-password"
enabled = true
```

## 支持的消息发送类型

所有发送方法均通过链式语法实现：

```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# 简单文本邮件
await mail.Send.To("private", "to@example.com").Subject("测试").Text("内容")

# 带附件的 HTML 邮件
await mail.Send.To("private", "to@example.com") \
    .Subject("HTML邮件") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML内容</h1>")

# 使用 Raw_ob12 发送标准 OB12 消息
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "邮件正文"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# 指定发送账户（多账户）
await mail.Send.Using("default").To("private", "to@example.com").Text("内容")
```

> 注意：使用链式语法时，参数方法（Subject / Cc / Attachment 等）必须在发送方法（Text / Html / Raw_ob12）之前调用。

### 基础发送方法

| 方法 | 说明 |
|------|------|
| `.Text(text: str)` | 发送纯文本邮件 |
| `.Html(html: str)` | 发送 HTML 格式邮件 |
| `.Raw_ob12(message, **kwargs)` | 发送 OneBot12 格式消息 |

### 链式修饰方法（返回 self，可组合使用）

| 方法 | 说明 |
|------|------|
| `.Subject(subject: str)` | 设置邮件主题 |
| `.Cc(emails: Union[str, List[str]])` | 设置抄送地址 |
| `.Bcc(emails: Union[str, List[str]])` | 设置密送地址 |
| `.ReplyTo(email: str)` | 设置回复地址 |
| `.Attachment(file, filename: str = None)` | 添加附件 |

### OB12 消息段反向转换（Raw_ob12）

| OB12 消息段 | 转换为邮件内容 |
|------------|--------------|
| `text` | 纯文本正文 |
| `image` | 图片附件 |
| `video` | 视频附件 |
| `file` | 文件附件 |
| `audio` | 音频附件 |
| `markdown` | 转为 HTML 正文 |

## 特有事件类型

### 核心差异点

1. 邮件事件均为 `message` 类型，`detail_type` 固定为 `private`
2. `user_id` 为发件人**纯邮箱地址**，`user_nickname` 为发件人显示名
3. `message` 消息段为标准 OB12 格式（text 段 + file 段）
4. 邮件主题通过 `email_subject` 扩展字段获取
5. 完整原始数据保留在 `email_raw` 字段中

### 新邮件事件（email_new）

```json
{
  "id": "<message-id@example.com>",
  "time": 1751990446,
  "type": "message",
  "detail_type": "private",
  "platform": "email",
  "self": {
    "platform": "email",
    "user_id": "bot@example.com"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "邮件正文内容"
      }
    }
  ],
  "alt_message": "邮件主题",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### 带附件的邮件

```json
{
  "message": [
    {
      "type": "text",
      "data": {
        "text": "请查收附件"
      }
    },
    {
      "type": "file",
      "data": {
        "file_id": "document.pdf",
        "file_name": "document.pdf",
        "size": 102400
      }
    }
  ]
}
```

### 回复邮件事件（email_reply）

当邮件包含 `References` 或 `In-Reply-To` 头时，`email_raw_type` 为 `email_reply`：

```json
{
  "email_raw_type": "email_reply",
  "email_raw": {
    "references": "<original-msg-id@example.com>",
    "in_reply_to": "<original-msg-id@example.com>"
  }
}
```

## 扩展字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `email_raw` | dict | 完整原始邮件数据（subject/from/to/date/cc/bcc/text_content/html_content/attachments 等） |
| `email_raw_type` | str | 原始事件类型：`email_new`（新邮件）或 `email_reply`（回复邮件） |
| `email_subject` | str | 邮件主题（便捷访问） |
| `email_from` | str | 发件人纯邮箱地址（便捷访问） |
| `attachments` | list | 附件数据列表（含二进制 `data` 字段，向后兼容） |

## 标准事件示例

### 完整邮件事件

```json
{
  "id": "<abc123@example.com>",
  "time": 1751990446,
  "type": "message",
  "detail_type": "private",
  "platform": "email",
  "self": {
    "platform": "email",
    "user_id": "bot@example.com"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "请查收附件"
      }
    },
    {
      "type": "file",
      "data": {
        "file_id": "document.pdf",
        "file_name": "document.pdf",
        "size": 102400
      }
    }
  ],
  "alt_message": "会议通知",
  "user_id": "sender@example.com",
  "user_nickname": "Sender",
  "email_subject": "会议通知",
  "email_from": "sender@example.com",
  "email_raw": {
    "subject": "会议通知",
    "from": "\"Sender\" <sender@example.com>",
    "to": "<bot@example.com>",
    "date": "Wed, 9 Jul 2026 02:00:46 +0800",
    "message_id": "<abc123@example.com>",
    "references": "",
    "in_reply_to": "",
    "cc": "",
    "bcc": "",
    "text_content": "请查收附件",
    "html_content": "<p>请查收附件</p>",
    "attachments": ["document.pdf"]
  },
  "email_raw_type": "email_new",
  "attachments": [
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 102400,
      "data": "..."
    }
  ]
}
```

## 发送方法返回值

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "<sent-msg-id@example.com>",
    "time": 1751990446
  },
  "message_id": "<sent-msg-id@example.com>",
  "message": "",
  "email_raw": {
    "success": true,
    "message": "Email sent successfully"
  }
}
```

## 事件处理示例

```python
from ErisPulse import sdk

@sdk.on_message(platform="email")
async def handle_email(event):
    # 发件人纯邮箱地址
    sender = event["user_id"]              # sender@example.com
    
    # 发件人显示名
    nickname = event.get("user_nickname")  # Sender
    
    # 邮件主题
    subject = event.get("email_subject")   # 会议通知
    
    # 纯文本正文（第一个 text 段）
    text = event.get_text()
    
    # 完整原始数据
    raw = event.get("email_raw", {})
    html = raw.get("html_content", "")
    
    # 处理附件
    for seg in event.get("message", []):
        if seg["type"] == "file":
            filename = seg["data"]["file_name"]
            size = seg["data"]["size"]
    
    # 回复邮件
    await event.reply(f"已收到：{subject}")
```
