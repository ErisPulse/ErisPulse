# Документация по функциональным возможностям платформы электронной почты

EmailAdapter представляет собой адаптер электронной почты, основанный на протоколах SMTP/IMAP, который поддерживает отправку, получение и обработку электронных писем.

---

Документация на других языках: [**English**](docs/ru/quick-start.md) | [**Русский**](docs/ru/quick-start.md)

## Информация о документации

- Соответствующая версия модуля: 4.1.0
- Ответственный: ErisPulse

Пожалуйста, верните полностью переведённый Markdown-документ, не включая никаких других текстов.

## Основная информация

- **Описание платформы:** Общий адаптер для отправки и получения почты с помощью стандартных протоколов SMTP/IMAP
- **Название адаптера:** EmailAdapter
- **Поддержка нескольких аккаунтов:** Поддерживает одновременную настройку нескольких почтовых аккаунтов
- **Способ подключения:** Получение с помощью IMAP-длинного опроса + отправка через SMTP
- **Способ аутентификации:** Адрес электронной почты + пароль/код авторизации
- **Совместимость с OneBot12:** Поддерживает отправку сообщений в формате OneBot12

Ссылки на документацию:
- [Основы](docs/ru/quick-start.md)
- [Руководство по адаптеру](docs/ru/adapter-guide.md)
- [Справочник API](docs/ru/api-reference.md)

## Описание конфигурации

### Глобальная конфигурация (EmailAdapter)

| Параметр | Тип | Значение по умолчанию | Описание |
|--------|------|--------|------|
| `imap_server` | str | `imap.example.com` | Адрес сервера IMAP по умолчанию |
| `imap_port` | int | `993` | Порт IMAP по умолчанию |
| `smtp_server` | str | `smtp.example.com` | Адрес сервера SMTP по умолчанию |
| `smtp_port` | int | `465` | Порт SMTP по умолчанию |
| `ssl` | bool | `true` | Включать ли SSL по умолчанию |
| `timeout` | int | `30` | Время ожидания соединения по умолчанию (секунды) |
| `poll_interval` | int | `60` | Интервал опроса IMAP (секунды) |
| `max_retries` | int | `3` | Максимальное количество попыток повторного подключения при сбое |

### Конфигурация аккаунтов (EmailAdapter.accounts)

Каждый аккаунт соответствует отдельной электронной почте. Конфигурация аккаунта имеет приоритет над глобальной конфигурацией.

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # Опционально, оставьте пустым для использования глобального значения по умолчанию
imap_port = 993                      # Опционально
smtp_server = "smtp.example.com"    # Опционально
smtp_port = 465                      # Опционально
ssl = true                           # Опционально
timeout = 30                         # Опционально
enabled = true

[EmailAdapter.accounts.backup]
email = "backup@example.com"
password = "another-password"
enabled = true
```

docs/ru/quick-start.md

## Типы поддерживаемых сообщений

Все методы отправки реализованы с помощью цепочечного синтаксиса:

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

# Использование Raw_ob12 для отправки стандартного OB12-сообщения
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "Текст письма"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# Указание аккаунта отправки (много аккаунтов)
await mail.Send.Using("default").To("private", "to@example.com").Text("Содержание")
```

> Примечание: при использовании цепочечного синтаксиса методы параметров (Subject / Cc / Attachment и т.д.) должны вызываться до методов отправки (Text / Html / Raw_ob12).

### Основные методы отправки

| Метод | Описание |
|------|------|
| `.Text(text: str)` | Отправка простого текстового письма |
| `.Html(html: str)` | Отправка письма в формате HTML |
| `.Raw_ob12(message, **kwargs)` | Отправка сообщения в формате OneBot12 |

### Методы цепочки (возвращают self, могут использоваться в комбинации)

| Метод | Описание |
|------|------|
| `.Subject(subject: str)` | Установка темы письма |
| `.Cc(emails: Union[str, List[str]])` | Установка адресов копии |
| `.Bcc(emails: Union[str, List[str]])` | Установка адресов скрытой копии |
| `.ReplyTo(email: str)` | Установка адреса для ответа |
| `.Attachment(file, filename: str = None)` | Добавление вложения |

### Обратное преобразование OB12-сегментов сообщений (Raw_ob12)

| OB12-сегмент | Преобразование в содержание письма |
|------------|--------------|
| `text` | Текстовое тело письма |
| `image` | Вложение изображения |
| `video` | Вложение видео |
| `file` | Вложение файла |
| `audio` | Вложение аудио |
| `markdown` | Преобразование в HTML-тело письма |

## Типы событий, специфичные для электронной почты

### Основные отличия

1. Все события электронной почты имеют тип `message`, `detail_type` фиксировано равно `private`
2. `user_id` — это **чистый адрес электронной почты** отправителя, `user_nickname` — отображаемое имя отправителя
3. Сегменты сообщения `message` находятся в стандартном формате OB12 (сегмент text + сегмент file)
4. Тема электронного письма получается через расширенное поле `email_subject`
5. Полные исходные данные сохраняются в поле `email_raw`

### Событие нового электронного письма (email_new)

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
        "text": "Содержимое тела письма"
      }
    }
  ],
  "alt_message": "Тема письма",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### Электронное письмо с вложениями

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

### Событие ответа на электронное письмо (email_reply)

Когда письмо содержит заголовки `References` или `In-Reply-To`, `email_raw_type` равно `email_reply`:

```json
{
  "email_raw_type": "email_reply",
  "email_raw": {
    "references": "<original-msg-id@example.com>",
    "in_reply_to": "<original-msg-id@example.com>"
  }
}

## Описание расширенных полей

| Поле | Тип | Описание |
|------|------|------|
| `email_raw` | dict | Полные исходные данные электронного письма (subject/from/to/date/cc/bcc/text_content/html_content/attachments и т.д.) |
| `email_raw_type` | str | Тип исходного события: `email_new` (новое письмо) или `email_reply` (ответ на письмо) |
| `email_subject` | str | Тема письма (удобный доступ) |
| `email_from` | str | Адрес электронной почты отправителя (удобный доступ) |
| `attachments` | list | Список данных вложений (содержит двоичное поле `data`, обратная совместимость) |

[**English**](docs/ru/quick-start.md)

## Примеры стандартных событий

### Полное событие электронной почты

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
  "user_nickname": "Отправитель",
  "email_subject": "Уведомление о встрече",
  "email_from": "sender@example.com",
  "email_raw": {
    "subject": "Уведомление о встрече",
    "from": "\"Отправитель\" <sender@example.com>",
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

## Возвращаемое значение метода отправки

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

## Пример обработки событий

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_email(event):
    if event.get("platform") != "email":
        return
    # Адрес отправителя (только почта)
    sender = event["user_id"]              # sender@example.com
    
    # Отображаемое имя отправителя
    nickname = event.get("user_nickname")  # Sender
    
    # Тема письма
    subject = event.get("email_subject")   # Уведомление о встрече
    
    # Текстовое тело письма (первый текстовый сегмент)
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

Документация: [docs/ru/quick-start.md](docs/ru/quick-start.md)