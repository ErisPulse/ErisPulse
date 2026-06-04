# Документ по характеристикам платформы Кофейня «Хуафэн» (Ideaura)

Адаптер IdeauraAdapter построен на базе API платформы Кофейня «Хуафэн» (Allons), интегрирующий все функциональные модули платформы и предоставляющий унифицированные интерфейсы для обработки событий и операций с сообщениями.

---

## Информация о документе

- Соответствующий модуль: ErisPulse-Ideaura
- Поддерживающий: ErisPulse

## Базовая информация

- Описание платформы: Кофейня «Хуафэн» (Allons) — это платформа мгновенного обмена сообщениями.
- Название адаптера: IdeauraAdapter
- Поддержка нескольких учетных записей: Поддержка конфигурации нескольких учетных записей через email/password.
- Поддержка цепных модификаторов: Поддержка цепных методов, таких как `.At()`, `.AtAll()`, `.Reply()`.
- Совместимость с OneBot12: Поддержка отправки сообщений в формате OneBot12.

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочного синтаксиса, например:
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`: Отправка сообщения только с текстом.
- `.Image(file, filename: str = None)`: Отправка сообщения с изображением, поддерживает bytes/URL/локальный путь.
- `.Video(file, filename: str = None)`: Отправка сообщения с видео, поддерживает bytes/URL/локальный путь.
- `.File(file, filename: str = None)`: Отправка сообщения с файлом, поддерживает bytes/URL/локальный путь.
- `.Voice(file, filename: str = None)`: Отправка голосового сообщения (отправляется как файл).
- `.Face(face_id: str)`: Отправка эмодзи (в виде текста).
- `.Markdown(text: str)`: Отправка сообщения в формате Markdown.
- `.Html(html: str)`: Отправка сообщения в формате HTML.
- `.Edit(message_id: str, text: str, content_type: str = "text")`: Редактирование существующего сообщения.
- `.Recall(message_id: str)`: Отзыв сообщения.

### Цепные модификаторы (можно комбинировать)

Цепные модификаторы возвращают `self`, поддерживают цепной вызов и должны быть вызваны перед окончательным методом отправки:

- `.At(user_id: str, name: str = None)`: @ указанного пользователя.
- `.AtAll()`: @ всех пользователей.
- `.Reply(message_id: str)`: Ответ на указанное сообщение.

### Примеры цепного вызова

```python
# Базовая отправка
await ideaura.Send.To("user", user_id).Text("Hello")

# @ пользователя
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# @ нескольких пользователей
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# Ответ на сообщение
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回复消息")

# Ответ + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回复并@")
```

### Отправка в разные цели

```python
# Отправка в чат-комнату
await ideaura.Send.To("group", "chatroom").Text("聊天室消息")

# Отправка в тему (topic)
await ideaura.Send.To("group", "topic_id").Text("话题消息")

# Отправка личного сообщения
await ideaura.Send.To("user", "user_id").Text("私聊消息")
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12 для удобства межплатформенной совместимости:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно напрямую ожидать (`await`) для получения результата отправки. Возвращаемый результат соответствует стандартизированной спецификации возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "self": {...},            // Информация о себе (содержит user_id)
    "message_id": "123456",   // ID сообщения
    "message": "",            // Информация об ошибке
    "ideaura_raw": {...}      // Исходные данные ответа
}
```

## Специфические типы событий

Для использования характеристик этой платформы необходимо проверять `platform=="ideaura"`.

### Ключевые отличия

1. Специфические типы событий:
    - Редактирование сообщения: ideaura_message_edit
    - Отзыв сообщения: ideaura_message_recall
    - Пересылка сообщения: ideaura_message_forward
    - Прочитано сообщение: ideaura_message_read
    - Друг отклонен: ideaura_friend_rejected
    - Друг онлайн: ideaura_friend_online
    - Друг офлайн: ideaura_friend_offline
    - Изменение статуса пользователя: ideaura_user_status_change
    - Сегмент пересланного сообщения: ideaura_forwarded
    - Сегмент отредактированного сообщения: ideaura_edited
    - Сегмент сообщения Markdown: ideaura_markdown
    - Сегмент сообщения HTML: ideaura_html
2. Расширенные поля:
    - Все специфические поля идентифицируются префиксом `ideaura_`
    - Исходные данные сохраняются в поле `ideaura_raw`
    - `self.user_id` представляет ID пользователя текущей учетной записи

### Событие редактирования сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "ID сообщения",
  "user_id": "ID редактора",
  "ideaura_new_content": "Содержимое после редактирования",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### Событие отзыва сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "ID отзываемого сообщения",
  "user_id": "ID отзывающего",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "Время отзыва",
  "ideaura_is_self": false
}
```

### Событие пересылки сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "ID исходного сообщения",
  "user_id": "ID пересылающего",
  "ideaura_forward_to": "ID целевой темы",
  "ideaura_original_message_id": "ID исходного сообщения",
  "ideaura_forwarded_message_id": "ID нового сообщения после пересылки"
}
```

### Событие прочтения сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "ID сообщения",
  "ideaura_reader_id": "ID читателя",
  "ideaura_reader_name": "Никнейм читателя"
}
```

### Событие появления друга онлайн

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "ID друга",
  "user_nickname": "Никнейм друга",
  "ideaura_friend_avatar": "URL аватара",
  "ideaura_presence_status": "online"
}
```

### Событие отсутствия друга (офлайн)

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_offline",
  "platform": "ideaura",
  "user_id": "ID друга",
  "ideaura_presence_status": "offline"
}
```

### Событие изменения статуса пользователя

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "ID пользователя",
  "ideaura_status": "Новый статус",
  "ideaura_previous_status": "Старый статус"
}
```

### Событие запроса в друзья

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "ID запрашивающего",
  "user_nickname": "Никнейм запрашивающего",
  "ideaura_request_id": "ID запроса",
  "ideaura_message": "Сообщение для подтверждения"
}
```

### Событие отказа в дружбе

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "ID отклонившего",
  "user_nickname": "Никнейм отклонившего",
  "ideaura_request_id": "ID запроса",
  "ideaura_requester_id": "ID иницииатора запроса",
  "ideaura_requester_name": "Никнейм иницииатора запроса"
}
```

### Сегмент пересланного сообщения (ideaura_forwarded)

При получении пересланного сообщения тип сегмента — `ideaura_forwarded`:

```json
{
  "type": "ideaura_forwarded",
  "data": {
    "forward_source_id": "1001",
    "original_message_id": "1001"
  }
}
```

| Поле | Тип | Описание |
|------|------|------|
| `forward_source_id` | string | ID исходного пересланного сообщения |
| `original_message_id` | string | ID исходного сообщения |

### Пример обработки событий

```python
from ErisPulse.Core.Event import notice, message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "ideaura":
        # Обработка события сообщения
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"Пересланное сообщение, ID источника: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"Сообщение было отредактировано: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"Сообщение было отозвано: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"Друг появился в сети: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"Изменение статуса пользователя: {status}")
```

---

## Конфигурация нескольких учетных записей

### Описание конфигурации

Адаптер IdeauraAdapter поддерживает одновременную настройку и работу нескольких учетных записей.

```toml
# config.toml
[IdeauraAdapter.accounts.default]
email = "user1@example.com"     # E-mail для входа (обязательно)
password = "password1"          # Пароль для входа (обязательно)
enabled = true                  # Включить (опционально, по умолчанию true)

[IdeauraAdapter.accounts.bot2]
email = "user2@example.com"
password = "password2"
enabled = true

# Необязательно: пользовательский адрес сервера
[IdeauraAdapter]
base_url = "https://api-cofe.allons-y.uk:3009"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**Описание конфигурации:**
- `email`: E-mail для входа в учетную запись (обязательно).
- `password`: Пароль для входа в учетную запись (обязательно).
- `enabled`: Включить ли эту учетную запись (опционально, по умолчанию true).

**Глобальные параметры конфигурации:**
- `base_url`: Адрес API-сервера (опционально, по умолчанию официальный адрес Кофейни «Хуафэн»).
- `ws_url`: Адрес WebSocket-сервера (опционально, по умолчанию официальный адрес Кофейни «Хуафэн»).
- `heartbeat_interval`: Интервал пульсирования в секундах (опционально, по умолчанию 30 секунд).

### Использование Send DSL для указания учетной записи

Можно указать, какой учетной записью отправлять сообщение, с помощью метода `Using()`:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Отправка сообщением от имени учетной записи
await ideaura.Send.Using("default").To("user", "user123").Text("Привет от аккаунта 1!")

# Отправка от user_id (автоматически сопоставляет с соответствующей учетной записью)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Привет от аккаунта 2!")

# При отсутствии указания используется первый включенный аккаунт
await ideaura.Send.To("user", "user123").Text("Привет от аккаунта по умолчанию!")
```

### Идентификатор учетной записи в событиях

Получаемые события автоматически содержат соответствующую информацию об учетной записи:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"Сообщение от аккаунта: {account_id}")
```

---

## Описание расширенных полей

- Все специфические поля идентифицируются префиксом `ideaura_`, чтобы избежать конфликтов со стандартными полями.
- Исходные данные сохраняются в поле `ideaura_raw`, для удобства доступа к полным исходным данным платформы.
- `self.user_id` представляет ID пользователя текущей вошедшей учетной записи.
- `ideaura_source_type`: Тип источника сообщения (`chatroom`/`topic`/`private`).
- `ideaura_sender_name`: Никнейм отправителя.
- `ideaura_sender_avatar`: URL аватара отправителя.
- `ideaura_sender_is_bot`: Является ли отправитель ботом.
- `ideaura_is_self`: Отправлено ли это сообщение самим пользователем (само-сообщения отфильтрованы).
- `ideaura_topic_name`: Название темы.
- `ideaura_message_type`: Тип сообщения (normal/edited/forwarded/quoted).
- `ideaura_message_subtype`: Подтип сообщения (text/image/video/file/markdown/html).

### Особенности обработки файлов

- Ограничение размера файла: 10 МБ (есть ограничения и при скачивании, и при локальном чтении).
- Автоматическое определение типа файла: определение фактического типа через заголовок (магические байты).
- Интеллектуальный разбор имени файла: автоматическое исправление бессмысленных расширений, таких как `.bin`/`.dat`/`.tmp`.
- Поддержка трех способов ввода файла: bytes, URL, локальный путь.
- Автоматическая загрузка файлов по URL и их загрузка на сервер.

### Поддерживаемые типы файлов

Определение типа через магические байты:

| Тип | Расширение |
|------|--------|
| Изображение | png, jpg, gif, webp |
| Видео | mp4, avi, flv |
| Аудио | mp3, wav, ogg |
| Документ | pdf, docx |

---

## Меры предосторожности

1. Адрес сервера `api-cofe.allons-y.uk` является фиксированным адресом платформы и не меняется в зависимости от названия адаптера.
2. Адаптер использует длинное WebSocket-соединение для приема событий и поддерживает автоматическое переподключение (фиксированная задержка 5 секунд).
3. Сообщения, отправленные самим пользователем (`isSelf: true`), автоматически отфильтровываются и события не создаются.
4. `@全体` (AtAll()) требует прав администратора.
5. Ограничение размера загрузки файлов составляет 10 МБ.
6. Файлы аудио отправляются как подтип `file` (платформа не различает отдельные типы аудио).
7. Эмодзи отправляются в виде текста (Face()).
8. При выходе из программы убедитесь, что вызван `shutdown()`, для освобождения ресурсов.