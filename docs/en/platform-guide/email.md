# Email Platform Feature Document

EmailAdapter is a mail adapter based on the SMTP/IMAP protocols, supporting mail sending, receiving, and processing.

---



## Documentation Information

- Corresponding Module Version: 4.1.0
- Maintainer: ErisPulse


## Basic Information

- Platform Introduction: A general adapter for sending and receiving emails via standard SMTP/IMAP protocols
- Adapter Name: EmailAdapter
- Multi-account Support: Supports configuring multiple email accounts simultaneously
- Connection Method: IMAP long-polling for receiving + SMTP for sending
- Authentication Method: Email address + password/authorization code
- OneBot12 Compatibility: Supports sending OneBot12 formatted messages

docs/en/quick-start.md

## Configuration Guide

### Global Configuration (EmailAdapter)

| Configuration Item | Type | Default Value | Description |
|--------------------|------|---------------|-------------|
| `imap_server` | str | `imap.example.com` | Default IMAP server address |
| `imap_port` | int | `993` | Default IMAP port |
| `smtp_server` | str | `smtp.example.com` | Default SMTP server address |
| `smtp_port` | int | `465` | Default SMTP port |
| `ssl` | bool | `true` | Whether to enable SSL by default |
| `timeout` | int | `30` | Default connection timeout (seconds) |
| `poll_interval` | int | `60` | IMAP polling interval (seconds) |
| `max_retries` | int | `3` | Maximum number of retries on connection failure |

### Account Configuration (EmailAdapter.accounts)

Each account corresponds to a separate email. Account-level configuration takes precedence over global configuration.

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # Optional, leave blank to use global default
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

[**English**](docs/en/quick-start.md)

## Supported Message Sending Types

All sending methods are implemented through a fluent syntax:

```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# Simple plain text email
await mail.Send.To("private", "to@example.com").Subject("Test").Text("Content")

# HTML email with attachment
await mail.Send.To("private", "to@example.com") \
    .Subject("HTML Email") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML Content</h1>")

# Use Raw_ob12 to send standard OB12 message
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "Email body"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# Specify sending account (for multiple accounts)
await mail.Send.Using("default").To("private", "to@example.com").Text("Content")
```

> Note: When using fluent syntax, parameter methods (Subject / Cc / Attachment, etc.) must be called before the sending method (Text / Html / Raw_ob12).

### Basic Sending Methods

| Method | Description |
|------|------|
| `.Text(text: str)` | Send plain text email |
| `.Html(html: str)` | Send HTML formatted email |
| `.Raw_ob12(message, **kwargs)` | Send OneBot12 formatted message |

### Fluent Modifier Methods (return self, can be combined)

| Method | Description |
|------|------|
| `.Subject(subject: str)` | Set email subject |
| `.Cc(emails: Union[str, List[str]])` | Set CC addresses |
| `.Bcc(emails: Union[str, List[str]])` | Set BCC addresses |
| `.ReplyTo(email: str)` | Set reply address |
| `.Attachment(file, filename: str = None)` | Add attachment |

### OB12 Message Segment Reverse Conversion (Raw_ob12)

| OB12 Message Segment | Converted to Email Content |
|------------|--------------|
| `text` | Plain text body |
| `image` | Image attachment |
| `video` | Video attachment |
| `file` | File attachment |
| `audio` | Audio attachment |
| `markdown` | Converted to HTML body |

## Specific Event Types

### Core Differences

1. All email events are of type `message`, with `detail_type` fixed as `private`.
2. `user_id` is the sender's **raw email address**, and `user_nickname` is the sender's display name.
3. The `message` segment is in standard OB12 format (text segment + file segment).
4. The email subject is obtained via the `email_subject` extension field.
5. The complete raw data is preserved in the `email_raw` field.

### New Mail Event (email_new)

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
        "text": "Mail body content"
      }
    }
  ],
  "alt_message": "Mail subject",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### Mail with Attachment

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

### Reply Mail Event (email_reply)

When the email contains `References` or `In-Reply-To` headers, `email_raw_type` is `email_reply`:

```json
{
  "email_raw_type": "email_reply",
  "email_raw": {
    "references": "<original-msg-id@example.com>",
    "in_reply_to": "<original-msg-id@example.com>"
  }
}

## Extension Field Description

| Field | Type | Description |
|------|------|------|
| `email_raw` | dict | Complete raw email data (subject/from/to/date/cc/bcc/text_content/html_content/attachments, etc.) |
| `email_raw_type` | str | Raw event type: `email_new` (new email) or `email_reply` (replied email) |
| `email_subject` | str | Email subject (convenient access) |
| `email_from` | str | Sender's pure email address (convenient access) |
| `attachments` | list | List of attachment data (includes binary `data` field, backward compatible) |


## Standard Event Examples

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

## Send Method Return Value

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

## Event Handling Example

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_email(event):
    if event.get("platform") != "email":
        return
    # Sender's pure email address
    sender = event["user_id"]              # sender@example.com
    
    # Sender's display name
    nickname = event.get("user_nickname")  # Sender
    
    # Email subject
    subject = event.get("email_subject")   # Meeting Notice
    
    # Plain text body (first text segment)
    text = event.get_text()
    
    # Complete raw data
    raw = event.get("email_raw", {})
    html = raw.get("html_content", "")
    
    # Process attachments
    for seg in event.get("message", []):
        if seg["type"] == "file":
            filename = seg["data"]["file_name"]
            size = seg["data"]["size"]
    
    # Reply to the email
    await event.reply(f"Received: {subject}")