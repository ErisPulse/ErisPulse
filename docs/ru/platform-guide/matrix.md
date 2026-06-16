# Документация по функциям платформы Matrix

MatrixAdapter — это адаптер, основанный на [Matrix Protocol](https://spec.matrix.org/), который интегрирует все основные модули функциональности Matrix, предоставляя единые интерфейсы обработки событий и операций с сообщениями.

---

## Информация о документе

- Версия соответствующего модуля: 1.0.0
- Ответственный: ErisPulse

## Основная информация

- Описание платформы: Matrix — это открытый децентрализованный коммуникационный протокол, поддерживающий различные сценарии, такие как личные сообщения и группы.
- Имя адаптера: MatrixAdapter
- Поддержка нескольких учетных записей: Поддержка одновременной конфигурации нескольких учетных записей Matrix
- Способ подключения: Long Polling (через Matrix Sync API `/sync`)
- Способ аутентификации: Вход на основе access_token или user_id + password для получения токена.
- Поддержка цепных методов: Поддержка методов модификации цепочки `.Reply()`, `.At()`, `.AtAll()` и т.д.
- Совместимость с OneBot12: Поддержка отправки сообщений в формате OneBot12.

## Описание конфигурации

MatrixAdapter поддерживает конфигурацию нескольких учетных записей, для каждой учетной записи настраивается homeserver и информация об аутентификации независимо.

```toml
# config.toml
# Учетная запись 1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Адрес сервера Matrix (обязательно)
access_token = "YOUR_ACCESS_TOKEN"          # Маркер доступа (выберите один из user_id+password)
user_id = ""                                # ID пользователя Matrix (например, @bot:matrix.org)
password = ""                               # Пароль пользователя Matrix
auto_accept_invites = true                  # Автоматически принимать приглашения в комнату (необязательно, по умолчанию true)
enabled = true                              # Включить (необязательно, по умолчанию true)

# Учетная запись 2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> **Совместимость с устаревшей конфигурацией**: Если обнаружена устаревшая однопользовательская конфигурация `[Matrix_Adapter]` (содержащая access_token), она автоматически мигрируется в `accounts.default`.

**Описание параметров конфигурации (для каждой учетной записи):**
- `homeserver`：Адрес сервера Matrix (обязательно), по умолчанию `https://matrix.org`
- `access_token`：Маркер доступа, можно получить из клиента Matrix. Если токен уже есть, просто введите его.
- `user_id`：ID пользователя Matrix (например `@bot:matrix.org`), используется вместе с `password` для входа.
- `password`：Пароль пользователя Matrix, используется для автоматического входа и получения access_token.
- `auto_accept_invites`：Автоматически принимать ли приглашения в комнату, по умолчанию `true`
- `enabled`：Включить ли эту учетную запись (необязательно, по умолчанию true)

**Способы аутентификации:**
- Способ 1 (Рекомендуется): Прямая сдача `access_token`.
- Способ 2: Предоставление `user_id` и `password`, адаптер автоматически вызовет интерфейс входа для получения токена.

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепного синтаксиса, например:
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`：Отправка текстового сообщения.
- `.Image(file: bytes | str)`：Отправка изображения, поддерживает путь к файлу, URL, MXC URI, бинарные данные.
- `.Voice(file: bytes | str)`：Отправка голосового сообщения, поддерживает путь к файлу, URL, MXC URI, бинарные данные.
- `.Video(file: bytes | str)`：Отправка видеосообщения, поддерживает путь к файлу, URL, MXC URI, бинарные данные.
- `.File(file: bytes | str, filename: str = "")`：Отправка файла, поддерживает путь к файлу, URL, MXC URI, бинарные данные.
- `.Notice(text: str)`：Отправка уведомления (тип m.notice в Matrix).
- `.Html(html: str, fallback: str = "")`：Отправка сообщения в формате HTML, поддерживает богатый текст.
- `.Raw_ob12(message: List[Dict], **kwargs)`：Отправка сообщения в формате OneBot12.

### Методы цепного вызова (могут комбинироваться)

Методы цепного вызова возвращают `self`, поддерживают цепной вызов, должны быть вызваны перед финальным методом отправки:

- `.Reply(message_id: str)`：Ответить на указанное сообщение (через отношение Matrix `m.in_reply_to`).
- `.At(user_id: str)`：Упомянуть (@) указанного пользователя (через поле Matrix `m.mentions`).
- `.AtAll()`：Упомянуть всех участников комнаты (через упоминание Matrix `@room`).

### Примеры цепного вызова

```python
# Базовая отправка
await matrix.Send.To("user", dm_room_id).Text("Hello")

# Ответ на сообщение
await matrix.Send.To("group", room_id).Reply("$event_id").Text("回复消息")

# Упоминание пользователя
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("你好")

# Упоминание всех
await matrix.Send.To("group", room_id).AtAll().Text("公告通知")

# Комбинированное использование: ответ + упоминание
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("复合消息")

# Отправка HTML сообщения
await matrix.Send.To("group", room_id).Html("<h1>标题</h1><p>内容</p>", fallback="标题\n内容")

# Отправка уведомления
await matrix.Send.To("group", room_id).Notice("系统通知")
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12 для облегчения межплатформенной совместимости сообщений:

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# В сочетании с цепными методами
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# Сложное сообщение
ob12_msg = [
    {"type": "text", "data": {"text": "看这张图片："}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "不错吧？"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно использовать с await для получения результата отправки. Возвращаемый результат соответствует стандартизированному спецификации возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "message_id": "$event_id", // ID события Matrix
    "message": "",            // Информация об ошибке
    "matrix_raw": {...}       // Исходные данные ответа
}
```

### Описание кодов ошибок

| retcode | Описание |
|---------|------|
| 0 | Успех |
| 32000 | Тайм-аут запроса или сбой загрузки медиа |
| 33000 | Аномалия вызова API |
| 34000 | API вернул неожиданный формат или бизнес-ошибку |

## Специфические типы событий

Перед использованием функций этой платформы необходимо проверить `platform=="matrix"`

### Ключевые различия

1.  **Децентрализованная архитектура**: Matrix — это децентрализованный коммуникационный протокол, формат ID пользователя `@user:server.domain`, формат ID комнаты `!room_id:server.domain`
2.  **Понятие комнаты**: Matrix не различает групповые и личные чаты, все сессии являются "комнатами". Адаптер автоматически определяет комнаты личных сообщений (DM) по данным аккаунта
3.  **Синхронизация Long Polling**: Используется API `/sync` для получения новых событий с помощью Long Polling, а не WebSocket
4.  **MXC URI**: Файлы медиа ссылаются в формате `mxc://server.domain/media_id`
5.  **HTML богатый текст**: Поддержка отправки сообщений в формате HTML через `formatted_body`
6.  **Эмоциональные реакции**: Поддержка реакций (Reaction) на уровне сообщений, в отличие от традиционных ответных сообщений
7.  **Редактирование сообщений**: Поддержка редактирования отправленных сообщений через отношение `m.replace`
8.  **Отзыв сообщений**: Поддержка отката/удаления сообщений через `m.room.redaction`

### Расширенные поля

- Все специфические поля обозначены префиксом `matrix_`
- Исходные данные сохранены в поле `matrix_raw`
- `matrix_raw_type` определяет исходный тип события Matrix (например, `m.room.message`, `m.room.member`)

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

# Эмоциональная реакция
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# Отзыв сообщения
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

# Потоковое сообщение
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### Типы сегментов сообщений

Сегменты сообщений Matrix автоматически конвертируются в соответствующие типы сообщений на основе `msgtype`:

| msgtype | Тип конвертации | Описание |
|---|---|---|
| m.text | `text` | Текстовое сообщение |
| m.notice | `text` | Уведомление |
| m.emote | `text` | Сообщение действия |
| m.image | `image` | Изображение |
| m.audio | `voice` | Голосовое сообщение |
| m.video | `video` | Видеосообщение |
| m.file | `file` | Файл |
| m.location | `location` | Сообщение местоположения |

Пример структуры сообщения:

```json
// Текстовое сообщение (с HTML)
{
  "type": "text",
  "data": {
    "text": "纯文本内容",
    "html": "<b>HTML内容</b>"
  }
}

// Изображение
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

// Сообщение местоположения
{
  "type": "location",
  "data": {
    "latitude": 0.0,
    "longitude": 0.0,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "北京市"
  }
}
```

### Методы Event Mixin

MatrixAdapter зарегистрировал следующие методы миксина событий, которые можно вызывать напрямую при обработке событий:

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_room_id()` | `str` | Получить ID комнаты |
| `get_matrix_event_type()` | `str` | Получить исходный тип события Matrix |
| `get_matrix_sender()` | `str` | Получить исходный ID отправителя |
| `get_reaction_key()` | `str` | Получить эмодзи реакции |
| `is_edited()` | `bool` | Определить, является ли сообщение отредактированным |
| `is_notice()` | `bool` | Определить, является ли сообщение типом m.notice |

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

## Подключение Sync API

### Процесс синхронизации

1.  Аутентификация с использованием access_token или user_id + password
2.  Вызов `/_matrix/client/v3/account/whoami` для получения bot_user_id
3.  Выпуск мета-события connect
4.  Выполнение начальной синхронизации (`/_matrix/client/v3/sync?timeout=0`) для получения токена `next_batch`
5.  Обнаружение комнат DM (`/_matrix/client/v3/user/{user_id}/account_data/m.direct`)
6.  Запуск цикла синхронизации Long Polling (`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`)
7.  Обработка и трансляция новых событий, возвращаемых каждым сеансом синхронизации

### Механизм пульсации

- Адаптер отправляет мета-событие `heartbeat` каждые 30 секунд
- При успешном подключении отправляется мета-событие `connect`
- При закрытии отправляется мета-событие `disconnect`

### Приглашения в комнату

- При получении приглашения в комнату (комната со статусом `invite`), если `auto_accept_invites` настроен как `true` (по умолчанию), адаптер автоматически присоединится к комнате
- При присоединении к комнате вызывается интерфейс `/_matrix/client/v3/join/{room_id}`

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

### Обработка эмоциональных реакций

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
        # Обработка эмоциональной реакции...
```

### Отправка медиа сообщений

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

# Отправка файла (с именем файла)
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="文档.pdf")
```

### Обработка редактирования сообщений

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # Обработка отредактированного сообщения...
```

### Мониторинг изменений участников

```python
@notice.on_notice()
async def handle_member_change(event):
    if event.get("platform") != "matrix":
        return

    detail_type = event.get("detail_type")

    if detail_type == "group_member_increase":
        user_id = event.get("user_id")
        nickname = event.get("user_nickname")
        print(f"用户 {nickname} ({user_id}) 加入了房间")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"用户 {user_id} 被移除，操作者: {operator_id}")