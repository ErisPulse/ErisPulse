# Email Platform Features Documentation

EmailAdapter is an email adapter based on the SMTP/IMAP protocols, supporting email sending, receiving, and processing.

---

## Document Information

- Corresponding module version: 4.3.2
- Maintainer: ErisPulse
- Last updated: 2026-11-10

## Basic Information

- Platform overview: A universal adapter for sending and receiving emails via the standard SMTP/IMAP protocols
- Adapter name: EmailAdapter
- Multi-account support: Supports configuring multiple email accounts simultaneously
- Connection method: IMAP long-polling for receiving + SMTP for sending
- Authentication method: Email address + password/authorization code
- OneBot12 compatibility: Supports sending OneBot12 format messages

## Configuration

### Global Configuration (EmailAdapter)

| Option | Type | Default | Description |
|--------|------|--------|------|
| `imap_server` | str | `imap.example.com` | Default IMAP server address |
| `imap_port` | int | `993` | Default IMAP port |
| `smtp_server` | str | `smtp.example.com` | Default SMTP server address |
| `smtp_port` | int | `465` | Default SMTP port |
| `ssl` | bool | `true` | Whether SSL is enabled by default |
| `timeout` | int | `30` | Default connection timeout (seconds) |
| `poll_interval` | int | `60` | IMAP polling interval (seconds) |
| `max_retries` | int | `3` | Maximum number of retries on connection failure |

### Account Configuration (EmailAdapter.accounts)

Each account corresponds to an independent mailbox. Account-level configuration takes precedence over global configuration.

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # Optional, leave empty to use global defaults
imap_port = 993                      # Optional
smtp_server = "smtp.example.com"    # Optional
smtp_port = 465                      # Optional
ssl = true                           # Optional
timeout = 30                         # Optional
enabled = true

[EmailAdapter.accounts.backup]
email = "backup@example.com"
password = "another-password"
enabled = true
```

## v5 Paradigm Updates (4.2.0)

- **Api DSL minimal set**: get_self_info (email address) / get_status / get_version / get_supported_actions
- **spawn_background task ownership**: The IMAP polling task now uses runtime.spawn_background
- **Framework soft dependency**: Detects ErisPulse>=2.7.1 at runtime and issues a prompt; outputs a version log at startup
- Import paths updated to Core.Bases; _load_accounts retained (merging global defaults is logic specific to this adapter)

## Standardization Alignment (4.3.2)

The response structure and error codes follow the [API Response Specification](../standards/api-response.md).

### Events and Response Fields

- **Message events now include top-level `message_id`**: Taken from the email `Message-ID` header
- **Email events without `Message-ID` fall back to uuid for the id**: The event `id` and `message_id` are no longer empty, preventing events from being silently deduplicated downstream due to duplicate ids
- **The raw data of `get_self_info` is located in the top-level `email_raw` of the response**, and the standard fields include `user_id` (email address)

### HTML Sending Methods

- `.Html(html: str)`: Sends an email in HTML format
- `.HTML(html: str)`: Alias of `.Html()` (consistent with the standard Send method naming)

### Error Code Specification

| retcode | Meaning | Description |
|---------|------|------|
| 0 | Success | — |
| 33001 | Network error | SMTP/IMAP connection failures (timeout, connection refused, etc.) |
| 34100 | Platform failure | SMTP rejection (recipient/sender/data/authentication rejected); the original error is retained in `email_raw` |
| 10003 | Parameter error | Missing or invalid parameters |

### Accounts and Multi-Account

- `Send` reads `send_context` (event account fallback): When `Send` is called from an event context, it falls back to the source account by default
- For multi-account sending, explicitly specify the account with `Send.Using("account name")`

---


### Integrated Platform Capabilities

- **Receiving**: IMAP polling for incoming mail (body/HTML/attachments parsed into message segments), incremental unread detection
- **Sending**: SMTP outgoing mail (Subject/Text/Html/Cc/Bcc/ReplyTo/Attachment), multi-account supported
- **API**: Account information and running status (minimal set); concepts such as email recall/groups are not applicable

---

## Supported Message Sending Types

All sending methods are implemented via chained syntax:

```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# Simple text email
await mail.Send.To("private", "to@example.com").Subject("Test").Text("Content")

# HTML email with attachments
await mail.Send.To("private", "to@example.com") \
    .Subject("HTML Email") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML Content</h1>")

# Send standard OB12 messages using Raw_ob12
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "Email body text"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# Specify the sending account (multi-account)
await mail.Send.Using("default").To("private", "to@example.com").Text("Content")
```

> Note: When using chained syntax, parameter methods (Subject / Cc / Attachment, etc.) must be called before the sending method (Text / Html / Raw_ob12).

### Basic Sending Methods

| Method | Description |
|------|------|
| `.Text(text: str)` | Sends a plain text email |
| `.Html(html: str)` | Sends an email in HTML format (`.HTML(html)` is an alias) |
| `.MergeForward(nodes, title)` | Sends a merged-forward email (the body is a collapsible `<details>` HTML card; the subject defaults to the title) |
| `.Raw_ob12(message, **kwargs)` | Sends a OneBot12 format message |

### Chained Modifier Methods (return self, can be combined)

| Method | Description |
|------|------|
| `.Subject(subject: str)` | Sets the email subject |
| `.Cc(emails: Union[str, List[str]])` | Sets CC addresses |
| `.Bcc(emails: Union[str, List[str]])` | Sets BCC addresses |
| `.ReplyTo(email: str)` | Sets the reply-to address |
| `.Attachment(file, filename: str = None)` | Adds an attachment |

### OB12 Message Segment Reverse Conversion (Raw_ob12)

| OB12 Message Segment | Converted to Email Content |
|------------|--------------|
| `text` | Plain text body |
| `image` | Image attachment |
| `video` | Video attachment |
| `file` | File attachment |
| `audio` | Audio attachment |
| `markdown` | Converted to HTML body |

## Platform-Specific Event Types

### Key Differences

1. All email events are of `message` type, with `detail_type` fixed to `private`
2. `user_id` is the sender's **plain email address**, and `user_nickname` is the sender's display name
3. `message` segments are in standard OB12 format (text segment + file segment)
4. The email subject is obtained via the `email_subject` extension field
5. The complete raw data is retained in the `email_raw` field

### New Email Event (email_new)

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
  "message_id": "<message-id@example.com>",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Email body content"
      }
    }
  ],
  "alt_message": "Email subject",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### Email with Attachments

```json
{
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Please check the attachment"
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

### Reply Email Event (email_reply)

When an email contains `References` or `In-Reply-To` headers, `email_raw_type` is `email_reply`:

```json
{
  "email_raw_type": "email_reply",
  "email_raw": {
    "references": "<original-msg-id@example.com>",
    "in_reply_to": "<original-msg-id@example.com>"
  }
}
```

## Extension Field Descriptions

| Field | Type | Description |
|------|------|------|
| `email_raw` | dict | Complete raw email data (subject/from/to/date/cc/bcc/text_content/html_content/attachments, etc.) |
| `email_raw_type` | str | Raw event type: `email_new` (new email) or `email_reply` (reply email) |
| `email_subject` | str | Email subject (convenient access) |
| `email_from` | str | Sender's plain email address (convenient access) |
| `attachments` | list | List of attachment data (includes the binary `data` field, backward compatible) |

## Standard Event Example

### Complete Email Event

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
  "message_id": "<abc123@example.com>",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Please check the attachment"
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
  "alt_message": "Meeting Notice",
  "user_id": "sender@example.com",
  "user_nickname": "Sender",
  "email_subject": "Meeting Notice",
  "email_from": "sender@example.com",
  "email_raw": {
    "subject": "Meeting Notice",
    "from": "\"Sender\" <sender@example.com>",
    "to": "<bot@example.com>",
    "date": "Wed, 9 Jul 2026 02:00:46 +0800",
    "message_id": "<abc123@example.com>",
    "references": "",
    "in_reply_to": "",
    "cc": "",
    "bcc": "",
    "text_content": "Please check the attachment",
    "html_content": "<p>Please check the attachment</p>",
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

## Sending Method Return Value

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

## Event Handling Example

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_email(event):
    if event.get("platform") != "email":
        return
    # Sender's plain email address
    sender = event["user_id"]              # sender@example.com
    
    # Sender's display name
    nickname = event.get("user_nickname")  # Sender
    
    # Email subject
    subject = event.get("email_subject")   # Meeting Notice
    
    # Plain text body (the first text segment)
    text = event.get_text()
    
    # Complete raw data
    raw = event.get("email_raw", {})
    html = raw.get("html_content", "")
    
    # Handle attachments
    for seg in event.get("message", []):
        if seg["type"] == "file":
            filename = seg["data"]["file_name"]
            size = seg["data"]["size"]
    
    # Reply to the email
    await event.reply(f"Received: {subject}")
```