# 郵件平台特性文件

EmailAdapter 是基於 SMTP/IMAP 協議的郵件適配器，支援郵件發送、接收和處理。

---



## 文件資訊

- 對應模組版本: 4.1.0
- 維護者: ErisPulse



## 基本資訊

- 平台簡介：透過標準 SMTP/IMAP 協議收發郵件的通用適配器
- 適配器名稱：EmailAdapter
- 多帳戶支援：支援同時設定多個郵箱帳戶
- 連接方式：IMAP 長輪詢接收 + SMTP 發送
- 認證方式：郵箱地址 + 密碼/授權碼
- OneBot12 兼容：支援發送 OneBot12 格式訊息


## 配置說明

### 全局配置（EmailAdapter）

| 配置項目 | 類型 | 預設值 | 說明 |
|--------|------|--------|------|
| `imap_server` | str | `imap.example.com` | 預設 IMAP 伺服器位址 |
| `imap_port` | int | `993` | 預設 IMAP 端口 |
| `smtp_server` | str | `smtp.example.com` | 預設 SMTP 伺服器位址 |
| `smtp_port` | int | `465` | 預設 SMTP 端口 |
| `ssl` | bool | `true` | 是否預設啟用 SSL |
| `timeout` | int | `30` | 預設連線超時（秒） |
| `poll_interval` | int | `60` | IMAP 輪詢間隔（秒） |
| `max_retries` | int | `3` | 連線失敗最大重試次數 |

### 帳戶配置（EmailAdapter.accounts）

每個帳戶對應一個獨立的電子信箱。帳戶層級的設定優先於全域設定。

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # 可選，留空使用全域預設
imap_port = 993                      # 可選
smtp_server = "smtp.example.com"    # 可選
smtp_port = 465                      # 可選
ssl = true                           # 可選
timeout = 30                         # 可選
enabled = true

[EmailAdapter.accounts.backup]
email = "backup@example.com"
password = "another-password"
enabled = true

## 支援的消息傳送類型

所有發送方法均透過鏈式語法實現：

```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# 簡單純文字郵件
await mail.Send.To("private", "to@example.com").Subject("測試").Text("內容")

# 帶附件的 HTML 郵件
await mail.Send.To("private", "to@example.com") \
    .Subject("HTML郵件") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML內容</h1>")

# 使用 Raw_ob12 發送標準 OB12 消息
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "郵件正文"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# 指定發送帳戶（多帳戶）
await mail.Send.Using("default").To("private", "to@example.com").Text("內容")
```

> 注意：使用鏈式語法時，參數方法（Subject / Cc / Attachment 等）必須在發送方法（Text / Html / Raw_ob12）之前呼叫。

### 基礎發送方法

| 方法 | 說明 |
|------|------|
| `.Text(text: str)` | 發送純文字郵件 |
| `.Html(html: str)` | 發送 HTML 格式郵件 |
| `.Raw_ob12(message, **kwargs)` | 發送 OneBot12 格式訊息 |

### 鏈式修飾方法（返回 self，可組合使用）

| 方法 | 說明 |
|------|------|
| `.Subject(subject: str)` | 設定郵件主旨 |
| `.Cc(emails: Union[str, List[str]])` | 設定抄送地址 |
| `.Bcc(emails: Union[str, List[str]])` | 設定密送地址 |
| `.ReplyTo(email: str)` | 設定回覆地址 |
| `.Attachment(file, filename: str = None)` | 添加附件 |

### OB12 消息段反向轉換（Raw_ob12）

| OB12 消息段 | 轉換為郵件內容 |
|------------|--------------|
| `text` | 純文字正文 |
| `image` | 圖片附件 |
| `video` | 影片附件 |
| `file` | 檔案附件 |
| `audio` | 音訊附件 |
| `markdown` | 轉為 HTML 正文 |

## 特有事件類型

### 核心差異點

1. 郵件事件均為 `message` 類型，`detail_type` 固定為 `private`
2. `user_id` 為寄件人**純郵箱地址**，`user_nickname` 為寄件人顯示名
3. `message` 消息段為標準 OB12 格式（text 段 + file 段）
4. 郵件主題透過 `email_subject` 擴展欄位獲取
5. 完整原始資料保留在 `email_raw` 欄位中

### 新郵件事件（email_new）

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
        "text": "郵件正文內容"
      }
    }
  ],
  "alt_message": "郵件主題",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### 帶附件的郵件

```json
{
  "message": [
    {
      "type": "text",
      "data": {
        "text": "請查收附件"
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

### 回覆郵件事件（email_reply）

當郵件包含 `References` 或 `In-Reply-To` 標頭時，`email_raw_type` 為 `email_reply`：

```json
{
  "email_raw_type": "email_reply",
  "email_raw": {
    "references": "<original-msg-id@example.com>",
    "in_reply_to": "<original-msg-id@example.com>"
  }
}

## 擴展欄位說明

| 欄位 | 類型 | 說明 |
|------|------|------|
| `email_raw` | dict | 完整原始郵件資料（subject/from/to/date/cc/bcc/text_content/html_content/attachments 等） |
| `email_raw_type` | str | 原始事件類型：`email_new`（新郵件）或 `email_reply`（回覆郵件） |
| `email_subject` | str | 郵件主旨（方便存取） |
| `email_from` | str | 寄件人純郵箱地址（方便存取） |
| `attachments` | list | 附件資料清單（包含二進位 `data` 欄位，向後相容） |

docs/zh-TW/quick-start.md

## 標準事件示例

### 完整郵件事件

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
        "text": "請查收附件"
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
  "alt_message": "會議通知",
  "user_id": "sender@example.com",
  "user_nickname": "Sender",
  "email_subject": "會議通知",
  "email_from": "sender@example.com",
  "email_raw": {
    "subject": "會議通知",
    "from": "\"Sender\" <sender@example.com>",
    "to": "<bot@example.com>",
    "date": "Wed, 9 Jul 2026 02:00:46 +0800",
    "message_id": "<abc123@example.com>",
    "references": "",
    "in_reply_to": "",
    "cc": "",
    "bcc": "",
    "text_content": "請查收附件",
    "html_content": "<p>請查收附件</p>",
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

## 發送方法返回值

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

7. **重要：路徑替換規則**
   - 將文件鏈接中的 `docs/zh-TW/` 替換為 `docs/zh-TW/`
   - 例如：`docs/zh-TW/quick-start.md` 應改為 `docs/zh-TW/quick-start.md`
   - 對於指向非當前語言版本文件的鏈接（如 `README.xx.md` 形式的鏈接），保持原樣不要修改
   - 這確保了鏈接指向正確語言的文件版本

## 事件處理範例

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_email(event):
    if event.get("platform") != "email":
        return
    # 寄件人純郵件地址
    sender = event["user_id"]              # sender@example.com
    
    # 寄件人顯示名
    nickname = event.get("user_nickname")  # Sender
    
    # 郵件主題
    subject = event.get("email_subject")   # 會議通知
    
    # 純文字正文（第一個 text 段）
    text = event.get_text()
    
    # 完整原始資料
    raw = event.get("email_raw", {})
    html = raw.get("html_content", "")
    
    # 處理附件
    for seg in event.get("message", []):
        if seg["type"] == "file":
            filename = seg["data"]["file_name"]
            size = seg["data"]["size"]
    
    # 回覆郵件
    await event.reply(f"已收到：{subject}")
```

[**English**](docs/zh-TW/quick-start.md)