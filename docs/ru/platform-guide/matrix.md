# Документация по функциям платформы Matrix

MatrixAdapter — адаптер, построенный на протоколе [Matrix](https://spec.matrix.org/), объединяющий все основные функциональные модули протокола Matrix и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия соответствующего модуля: 4.1.0
- Ответственный: ErisPulse

## Основная информация

- Краткое описание платформы: Matrix — это открытый децентрализованный протокол общения, поддерживающий личные сообщения, группы и другие сценарии.
- Название адаптера: MatrixAdapter
- Поддержка нескольких аккаунтов: Поддерживает настройку нескольких аккаунтов Matrix.
- Способ подключения: Long Polling (через API синхронизации Matrix `/sync`).
- Способ аутентификации: Получение токена по access_token или user_id + password.
- Поддержка цепочечных модификаторов: Поддерживает цепочечные методы модификации, такие как `.Reply()`, `.At()`, `.AtAll()`.
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12.

## Описание конфигурации

MatrixAdapter поддерживает настройку нескольких аккаунтов, каждый аккаунт имеет отдельные настройки homeserver и аутентификации.

```toml
# config.toml
# Аккаунт 1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Адрес сервера Matrix (обязательно)
access_token = "YOUR_ACCESS_TOKEN"          # Токен доступа (должен быть указан один из access_token или user_id+password)
user_id = ""                                # ID пользователя Matrix (например @bot:matrix.org)
password = ""                               # Пароль пользователя Matrix
auto_accept_invites = true                  # Автоматически принимать приглашения в комнаты (необязательно, по умолчанию true)
enabled = true                              # Включить аккаунт (необязательно, по умолчанию true)

# Аккаунт 2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> Совместимость со старой конфигурацией: Если обнаружена старая конфигурация с одним аккаунтом `[Matrix_Adapter]` (с access_token), она будет автоматически перенесена в `accounts.default`.

**Описание параметров конфигурации (для каждого аккаунта):**
- `homeserver`: Адрес сервера Matrix (обязательно), по умолчанию `https://matrix.org`.
- `access_token`: Токен доступа, можно получить из клиента Matrix. Если токен уже известен, его можно указать напрямую.
- `user_id`: ID пользователя Matrix (например `@bot:matrix.org`), используется вместе с `password` для входа.
- `password`: Пароль пользователя Matrix, используется для автоматического входа и получения access_token.
- `auto_accept_invites`: Автоматически принимать приглашения в комнаты, по умолчанию `true`.
- `enabled`: Включить аккаунт (необязательно, по умолчанию `true`).

**Способы аутентификации:**
- Способ 1 (рекомендуется): Указать `access_token`.
- Способ 2: Указать `user_id` и `password`, адаптер автоматически вызовет интерфейс входа для получения токена.

## Поддерживаемые типы отправки сообщений

Все методы отправки сообщений реализованы с использованием цепочечной синтаксической конструкции, например:
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

Поддерживаемые типы отправки сообщений включают:
- `.Text(text: str)` — отправка обычного текстового сообщения.
- `.Image(file: bytes | str)` — отправка изображения, поддерживает файлы, URL, MXC URI, бинарные данные.
- `.Voice(file: bytes | str)` — отправка голосового сообщения, поддерживает файлы, URL, MXC URI, бинарные данные.
- `.Video(file: bytes | str)` — отправка видео, поддерживает файлы, URL, MXC URI, бинарные данные.
- `.File(file: bytes | str, filename: str = "")` — отправка файла, поддерживает файлы, URL, MXC URI, бинарные данные.
- `.Notice(text: str)` — отправка уведомления (типа m.notice в Matrix).
- `.Html(html: str, fallback: str = "")` — отправка HTML-форматированного сообщения, поддерживает разметку.
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

### Цепочечные методы модификации (можно комбинировать)

Методы модификации возвращают `self`, поддерживается цепочечное использование, должны вызываться перед окончательным методом отправки:

- `.Reply(message_id: str)` — ответ на указанное сообщение (через связь `m.in_reply_to` в Matrix).
- `.At(user_id: str)` — упоминание указанного пользователя (через поле `m.mentions` в Matrix).
- `.AtAll()` — упоминание всех участников комнаты (через упоминание `@room` в Matrix).

### Примеры цепочечного вызова

```python
# Базовая отправка
await matrix.Send.To("user", dm_room_id).Text("Hello")

# Ответ на сообщение
await matrix.Send.To("group", room_id).Reply("$event_id").Text("Ответное сообщение")

# Упоминание пользователя
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("Привет")

# Упоминание всех
await matrix.Send.To("group", room_id).AtAll().Text("Объявление")

# Комбинирование: ответ + упоминание
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("Составное сообщение")

# Отправка HTML-сообщения
await matrix.Send.To("group", room_id).Html("<h1>Заголовок</h1><p>Содержимое</p>", fallback="Заголовок\nСодержимое")

# Отправка уведомления
await matrix.Send.To("group", room_id).Notice("Системное уведомление")
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость между платформами:

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными методами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# Сложное сообщение
ob12_msg = [
    {"type": "text", "data": {"text": "Посмотри на эту картинку: "}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "Круто, правда? "}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## Возвращаемые значения методов отправки

Все методы отправки сообщений возвращают объект задачи (Task), который можно ожидать с помощью `await`. Возвращаемые результаты соответствуют стандартизированному формату возврата ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "message_id": "$event_id", // ID события Matrix
    "message": "",            // Сообщение об ошибке
    "matrix_raw": {...}       // Исходные данные ответа
}
```

### Описание кодов ошибок

| retcode | Описание |
|---------|----------|
| 0 | Успешно |
| 32000 | Превышено время ожидания или ошибка при загрузке медиафайла |
| 33000 | Ошибка вызова API |
| 34000 | API вернул неожидаемый формат или бизнес-ошибку |

## Уникальные типы событий

Необходимо использовать `platform=="matrix"` для проверки и применения уникальных функций данной платформы.

### Основные отличия

1. **Децентрализованная архитектура**: Matrix — это децентрализованный протокол общения, формат ID пользователя: `@user:server.domain`, формат ID комнаты: `!room_id:server.domain`.
2. **Концепция комнат**: Matrix не различает чаты и личные сообщения, все переговоры — это "комнаты". Адаптер автоматически определяет личные комнаты по данным DM (Direct Message).
3. **Синхронизация Long Polling**: Используется API `/sync` для получения новых событий, а не WebSocket.
4. **MXC URI**: Ссылки на медиафайлы в формате `mxc://server.domain/media_id`.
5. **HTML-форматированный текст**: Поддержка отправки HTML-форматированных сообщений через `formatted_body`.
6. **Реакции на сообщения**: Поддержка реакций на сообщения (Reaction), отличается от традиционных ответов.
7. **Редактирование сообщений**: Поддержка редактирования отправленных сообщений через связь `m.replace`.
8. **Удаление сообщений**: Поддержка удаления/отмены сообщений через `m.room.redaction`.

### Расширенные поля

- Все специфические поля имеют префикс `matrix_`.
- Сохраняются исходные данные в поле `matrix_raw`.
- `matrix_raw_type` определяет тип исходного события Matrix (например `m.room.message`, `m.room.member`).

### Примеры специальных полей

```python
# Сообщение в группе
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# Личное сообщение
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# Реакция на сообщение
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# Удаление сообщения
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# Редактирование сообщения
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": true,
  "matrix_original_event_id": "$original_event_id"
}

# Сообщение в теме
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### Типы сообщений

Matrix-сообщения автоматически преобразуются в соответствующие типы сообщений на основе `msgtype`:

| msgtype | Тип сообщения | Описание |
|---|---|---|
| m.text | `text` | Текстовое сообщение |
| m.notice | `text` | Уведомление |
| m.emote | `text` | Сообщение действия |
| m.image | `image` | Изображение |
| m.audio | `voice` | Голосовое сообщение |
| m.video | `video` | Видеосообщение |
| m.file | `file` | Файл |
| m.location | `location` | Местоположение |

Пример структуры сообщения:

```json
// Текстовое сообщение (с HTML)
{
  "type": "text",
  "data": {
    "text": "Текстовое содержимое",
    "html": "<b>HTML-содержимое</b>"
  }
}

// Сообщение с изображением
{
  "type": "image",
  "data": {
    "url": "mxc://matrix.org/abc123",
    "filename": "photo.png",
    "matrix_mxc": "mxc://matrix.org/abc123",
    "info": {
      "mimetype": "image/png",
      "w": 800,
      "h": 600,
      "size": 123456
    }
  }
}

// Сообщение с местоположением
{
  "type": "location",
  "data": {
    "latitude": 0.0,
    "longitude": 0.0,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "Пекин"
  }
}
```

### Методы Event Mixin

MatrixAdapter зарегистрировал следующие методы Event Mixin, которые можно использовать непосредственно в обработке событий:

| Метод | Возвращаемый тип | Описание |
|------|----------|------|
| `get_room_id()` | `str` | Получить ID комнаты |
| `get_matrix_event_type()` | `str` | Получить тип исходного события Matrix |
| `get_matrix_sender()` | `str` | Получить ID отправителя |
| `get_reaction_key()` | `str` | Получить ключ реакции |
| `is_edited()` | `bool` | Проверить, является ли сообщение отредактированным |
| `is_notice()` | `bool` | Проверить, является ли сообщение типа m.notice |

```python
@message.on_message()
async def handle_message(event):
    if event.get("platform") != "matrix":
        return

    room_id = event.get_room_id()
    event_type = event.get_matrix_event_type()
    sender = event.get_matrix_sender()
    is_edited = event.is_edited()
    is_notice = event.is_notice()
```

## Подключение через Sync API

### Процесс синхронизации

1. Аутентификация с использованием access_token или user_id + password.
2. Вызов `/_matrix/client/v3/account/whoami` для получения bot_user_id.
3. Вызов метасобытия `connect`.
4. Выполнение начальной синхронизации (`/_matrix/client/v3/sync?timeout=0`) для получения `next_batch` токена.
5. Обнаружение DM-комнат (`/_matrix/client/v3/user/{user_id}/account_data/m.direct`).
6. Начало цикла Long Polling синхронизации (`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`).
7. Обработка новых событий и их преобразование.

### Механизм таймера

- Адаптер каждые 30 секунд генерирует метасобытие `heartbeat`.
- При успешном подключении генерируется событие `connect`.
- При отключении генерируется событие `disconnect`.

### Приглашения в комнаты

- При получении приглашения в комнату (комната в состоянии `invite`), если в конфигурации `auto_accept_invites` установлено в `true` (по умолчанию), адаптер автоматически присоединяется к комнате.
- Присоединение к комнате выполняется через вызов интерфейса `/_matrix/client/v3/join/{room_id}`.

## Примеры использования

### Обработка сообщений в группе

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

matrix = sdk.adapter.get("matrix")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "matrix":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    room_id = event.get("group_id")

    if text == "hello":
        await matrix.Send.To("group", room_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### Обработка реакций

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_reaction(event):
    if event.get("platform") != "matrix":
        return

    if event.get("detail_type") == "matrix_reaction":
        reaction_key = event.get("matrix_reaction_key")
        reacted_event_id = event.get("matrix_reaction_event_id")
        room_id = event.get_room_id()
        # Обработка реакции...
```

### Отправка медиафайлов

```python
# Отправка изображения (URL)
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# Отправка изображения (MXC URI)
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# Отправка изображения (бинарные данные)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# Отправка изображения (локальный путь)
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# Отправка файла (с указанием имени)
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="Документ.pdf")
```

### Обработка редактирования сообщений

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # Обработка редактированного сообщения...
```

### Отслеживание изменений участников

```python
@notice.on_notice()
async def handle_member_change(event):
    if event.get("platform") != "matrix":
        return

    detail_type = event.get("detail_type")

    if detail_type == "group_member_increase":
        user_id = event.get("user_id")
        nickname = event.get("user_nickname")
        print(f"Пользователь {nickname} ({user_id}) присоединился к комнате")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"Пользователь {user_id} был исключен, оператор: {operator_id}")
```