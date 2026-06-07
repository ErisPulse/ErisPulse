# Документация по характеристикам платформы электронной почты

MailAdapter — это адаптер электронной почты, основанный на протоколах SMTP/IMAP, который поддерживает отправку, получение и обработку почты.

---

## Информация о документации

- Версия соответствующего модуля: 1.0.0
- Ответственный за поддержку: ErisPulse


## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочной (fluent) нотации, например:
```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# Простое текстовое письмо
await mail.Send.Using("from@example.com").To("to@example.com").Subject("Тест").Text("Содержание")

# HTML-письмо с вложениями
await mail.Send.Using("from@example.com")
    .To("to@example.com")
    .Subject("HTML-письмо")
    .Cc(["cc1@example.com", "cc2@example.com"])
    .Attachment("report.pdf")
    .Html("<h1>HTML-содержимое</h1>")

# Примечание: при использовании цепочной нотации методы параметров должны быть заданы до методов отправки (Text, Html)
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`: отправка текстового письма
- `.Html(html: str)`: отправка HTML-письма
- `.Attachment(file: str, filename: str = None)`: добавление вложения
- `.Cc(emails: Union[str, List[str]])`: установка копии (CC)
- `.Bcc(emails: Union[str, List[str]])`: установка скрытой копии (BCC)
- `.ReplyTo(email: str)`: установка адреса ответа

### Описание специальных параметров

| Параметр       | Тип               | Описание                          |
|----------------|--------------------|----------------------------------|
| Subject        | str                | Тема письма                      |
| From           | str                | Адрес отправителя (устанавливается через Using)      |
| To             | str                | Адрес получателя                    |
| Cc             | str или List[str]   | Список адресов для копии (CC)                  |
| Bcc            | str или List[str]   | Список скрытых копий (BCC)                  |
| Attachment     | str или Path        | Путь к файлу вложения                 |

## Специальные типы событий

Формат события получения почты:
```python
{
  "type": "message",
  "detail_type": "private",  # По умолчанию электронная почта
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
  "attachments": [  # Список данных вложений
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 1024,
      "data": b"..."  # Бинарные данные вложения
    }
  ]
}
```

## Описание расширенных полей

- `email_raw`: содержит исходные данные почты
- `attachments`: список данных вложений

## Информация о конвертации в протокол OneBot12

Конвертация событий почты в протокол OneBot12, основные отличия:

### Основные отличия

1. Специальные поля:
   - `email_raw`: содержит исходные данные почты
   - `attachments`: список данных вложений

2. Особая обработка:
   - Тема письма и информация об отправителе будут включены в текст сообщения
   - Данные вложений будут предоставлены в бинарном формате
   - HTML-содержимое будет сохранено в поле email_raw

### Пример

```python
{
  "type": "message",
  "platform": "email",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Subject: Уведомление о встрече\nFrom: sender@example.com\n\nПожалуйста, ознакомьтесь с вложением"
      }
    }
  ],
  "email_raw": {
    "subject": "Уведомление о встрече",
    "from": "sender@example.com",
    "to": "receiver@example.com",
    "html_content": "<p>Пожалуйста, ознакомьтесь с вложением</p>",
    "attachments": ["document.pdf"]
  },
  "attachments": [
    {
      "filename": "document.pdf",
      "data": b"...",  # Бинарные данные вложения
      "size": 1024
    }
  ]
}