# Документация по функциональности почтовой платформы

EmailAdapter — это почтовый адаптер на основе протоколов SMTP/IMAP, поддерживающий отправку, получение и обработку электронной почты.

---

## Информация о документации

- Версия соответствующего модуля: 4.1.0
- Ответственный: ErisPulse

## Основная информация

- Краткое описание: Общий адаптер для отправки и получения почты с использованием стандартных протоколов SMTP/IMAP
- Название адаптера: EmailAdapter
- Поддержка нескольких аккаунтов: Поддерживает одновременную настройку нескольких почтовых аккаунтов
- Способ подключения: Получение по протоколу IMAP с использованием длинного опроса + отправка по SMTP
- Способ аутентификации: Адрес электронной почты + пароль/код авторизации
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Описание конфигурации

### Глобальная конфигурация (EmailAdapter)

| Параметр | Тип | Значение по умолчанию | Описание |
|----------|-----|-----------------------|----------|
| `imap_server` | str | `imap.example.com` | Адрес сервера IMAP по умолчанию |
| `imap_port` | int | `993` | Порт IMAP по умолчанию |
| `smtp_server` | str | `smtp.example.com` | Адрес сервера SMTP по умолчанию |
| `smtp_port` | int | `465` | Порт SMTP по умолчанию |
| `ssl` | bool | `true` | Использовать ли SSL по умолчанию |
| `timeout` | int | `30` | Время ожидания подключения (секунды) |
| `poll_interval` | int | `60` | Интервал опроса IMAP (секунды) |
| `max_retries` | int | `3` | Максимальное количество попыток при неудачном подключении |

### Конфигурация аккаунтов (EmailAdapter.accounts)

Каждый аккаунт соответствует отдельной почте. Настройки аккаунта имеют приоритет над глобальными.

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # Необязательно, оставьте пустым, чтобы использовать глобальное значение по умолчанию
imap_port = 993                      # Необязательно
smtp_server = "smtp.example.com"    # Необязательно
smtp_port = 465                      # Необязательно
ssl = true                           # Необязательно
timeout = 30                         # Необязательно
enabled = true

[EmailAdapter.accounts.backup]
email = "backup@example.com"
password = "another-password"
enabled = true
```

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса:

```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# Простое текстовое письмо
await mail.Send.To("private", "to@example.com").Subject("Тест").Text("Содержание")

# HTML-письмо с вложениями
await mail.Send.To("private", "to@example.com") \
    .Subject("HTML-письмо") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML-содержание</h1>")

# Отправка стандартного сообщения OB12 с помощью Raw_ob12
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "Текст письма"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# Указание аккаунта отправки (множественные аккаунты)
await mail.Send.Using("default").To("private", "to@example.com").Text("Содержание")
```

> Примечание: При использовании цепочечного синтаксиса методы параметров (Subject / Cc / Attachment и т.д.) должны вызываться до метода отправки (Text / Html / Raw_ob12).

### Основные методы отправки

| Метод | Описание |
|-------|----------|
| `.Text(text: str)` | Отправка простого текстового письма |
| `.Html(html: str)` | Отправка письма в формате HTML |
| `.Raw_ob12(message, **kwargs)` | Отправка сообщения в формате OneBot12 |

### Методы цепочки (возвращают self, могут использоваться вместе)

| Метод | Описание |
|-------|----------|
| `.Subject(subject: str)` | Установка темы письма |
| `.Cc(emails: Union[str, List[str]])` | Установка адресов копии (Cc) |
| `.Bcc(emails: Union[str, List[str]])` | Установка адресов скрытой копии (Bcc) |
| `.ReplyTo(email: str)` | Установка адреса ответа |
| `.Attachment(file, filename: str = None)` | Добавление вложения |

### Обратное преобразование сообщений OB12 (Raw_ob12)

| Сегмент OB12 | Преобразование в содержание письма |
|-------------|----------------------------------|
| `text` | Текстовое содержание письма |
| `image` | Вложение с изображением |
| `video` | Вложение с видео |
| `file` | Вложение с файлом |
| `audio` | Вложение с аудио |
| `markdown` | Преобразование в HTML-содержание письма |

## Специфические типы событий

### Основные отличия

1. Все события почты имеют тип `message`, `detail_type` фиксирован как `private`
2. `user_id` — это чистый адрес электронной почты отправителя, `user_nickname` — имя отправителя
3. `message` — сегменты стандартного формата OB12 (сегмент text + сегмент file)
4. Тема письма доступна через расширенное поле `email_subject`
5. Полные исходные данные сохраняются в поле `email_raw`

### Событие нового письма (email_new)

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
        "text": "Содержание письма"
      }
    }
  ],
  "alt_message": "Тема письма",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### Письмо с вложениями

```json
{
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Пожалуйста, проверьте вложение"
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

### Событие ответа на письмо (email_reply)

Когда письмо содержит заголовки `References` или `In-Reply-To`, `email_raw_type` имеет значение `email_reply`:

```json
{
  "email_raw_type": "email_reply",
  "email_raw": {
    "references": "<original-msg-id@example.com>",
    "in_reply_to": "<original-msg-id@example.com>"
  }
}
```

## Описание расширенных полей

| Поле | Тип | Описание |
|------|-----|----------|
| `email_raw` | dict | Полные исходные данные письма (subject/from/to/date/cc/bcc/text_content/html_content/attachments и т.д.) |
| `email_raw_type` | str | Тип исходного события: `email_new` (новое письмо) или `email_reply` (ответ на письмо) |
| `email_subject` | str | Тема письма (удобный доступ) |
| `email_from` | str | Адрес отправителя (удобный доступ) |
| `attachments` | list | Список данных вложений (содержит двоичные данные `data`, обратная совместимость) |

## Примеры стандартных событий

### Полное событие письма

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
        "text": "Пожалуйста, проверьте вложение"
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
  "alt_message": "Уведомление о встрече",
  "user_id": "sender@example.com",
  "user_nickname": "Sender",
  "email_subject": "Уведомление о встрече",
  "email_from": "sender@example.com",
  "email_raw": {
    "subject": "Уведомление о встрече",
    "from": "\"Sender\" <sender@example.com>",
    "to": "<bot@example.com>",
    "date": "Wed, 9 Jul 2026 02:00:46 +0800",
    "message_id": "<abc123@example.com>",
    "references": "",
    "in_reply_to": "",
    "cc": "",
    "bcc": "",
    "text_content": "Пожалуйста, проверьте вложение",
    "html_content": "<p>Пожалуйста, проверьте вложение</p>",
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

## Возвращаемые значения методов отправки

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

## Примеры обработки событий

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_email(event):
    if event.get("platform") != "email":
        return
    # Адрес отправителя
    sender = event["user_id"]              # sender@example.com
    
    # Имя отправителя
    nickname = event.get("user_nickname")  # Sender
    
    # Тема письма
    subject = event.get("email_subject")   # Уведомление о встрече
    
    # Текстовое содержание (первый сегмент text)
    text = event.get_text()
    
    # Полные исходные данные
    raw = event.get("email_raw", {})
    html = raw.get("html_content", "")
    
    # Обработка вложений
    for seg in event.get("message", []):
        if seg["type"] == "file":
            filename = seg["data"]["file_name"]
            size = seg["data"]["size"]
    
    # Ответ на письмо
    await event.reply(f"Получено: {subject}")
```