# Mail Platform Feature Documentation

MailAdapter is an email adapter based on the SMTP/IMAP protocol, supporting email sending, receiving, and processing.

---

## Documentation Information

- Corresponding Module Version: 1.0.0
- Maintainer: ErisPulse


## Supported Message Sending Types

All sending methods are implemented using chained syntax, for example:
```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# Simple text email
await mail.Send.Using("from@example.com").To("to@example.com").Subject("测试").Text("内容")

# HTML email with attachments
await mail.Send.Using("from@example.com")
    .To("to@example.com")
    .Subject("HTML邮件")
    .Cc(["cc1@example.com", "cc2@example.com"])
    .Attachment("report.pdf")
    .Html("<h1>HTML内容</h1>")

# Note: When using chained syntax, parameter methods must be set before the sending methods (Text, Html)
```

Supported sending types include:
- `.Text(text: str)`: Send plain text email
- `.Html(html: str)`: Send HTML email
- `.Attachment(file: str, filename: str = None)`: Add attachment
- `.Cc(emails: Union[str, List[str]])`: Set CC
- `.Bcc(emails: Union[str, List[str]])`: Set BCC
- `.ReplyTo(email: str)`: Set reply-to address

### Special Parameters Explanation

| Parameter | Type | Description |
|-----------|------|-------------|
| Subject | str | Email subject |
| From | str | Sender address (set via Using) |
| To | str | Recipient address |
| Cc | str or List[str] | CC address list |
| Bcc | str or List[str] | BCC address list |
| Attachment | str or Path | Attachment file path |

## Special Event Types

Email receiving event format:
```python
{
  "type": "message",
  "detail_type": "private",  # Default private chat for email
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
  "attachments": [  # List of attachment data
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 1024,
      "data": b"..."  # Attachment binary data
    }
  ]
}
```

## Extended Field Descriptions

- `email_raw`: Contains raw email data
- `attachments`: List of attachment data

## OneBot12 Protocol Conversion Explanation

Conversion of email events to OneBot12 protocol, main differences:

### Core Differences

1. Special fields:
   - `email_raw`: Contains raw email data
   - `attachments`: List of attachment data

2. Special handling:
   - Email subject and sender information will be included in the message text
   - Attachment data will be provided in binary form
   - HTML content will be retained in the email_raw field

### Example

```python
{
  "type": "message",
  "platform": "email",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Subject: Meeting Notice\nFrom: sender@example.com\n\nPlease check the attachment"
      }
    }
  ],
  "email_raw": {
    "subject": "Meeting Notice",
    "from": "sender@example.com",
    "to": "receiver@example.com",
    "html_content": "<p>Please check the attachment</p>",
    "attachments": ["document.pdf"]
  },
  "attachments": [
    {
      "filename": "document.pdf",
      "data": b"...",  # Attachment binary data
      "size": 1024
    }
  ]
}