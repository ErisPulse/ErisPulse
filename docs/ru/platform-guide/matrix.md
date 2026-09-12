# Документация по функциям платформы Matrix

MatrixAdapter - это адаптер, построенный на основе [протокола Matrix](https://spec.matrix.org/), который объединяет все основные модули протокола Matrix и предоставляет единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Соответствующая версия модуля: 4.2.0
- Ответственный: ErisPulse

## Основная информация

- Описание платформы: Matrix — это открытый, децентрализованный протокол коммуникации, поддерживающий личные сообщения, группы и другие сценарии.
- Название адаптера: MatrixAdapter
- Поддержка нескольких аккаунтов: Поддерживает настройку нескольких аккаунтов Matrix одновременно.
- Способ подключения: Long Polling (через Matrix Sync API `/sync`)
- Способ аутентификации: Аутентификация на основе `access_token` или через `user_id` + `password` для получения токена
- Поддержка цепочки модификаторов: Поддерживает цепочку методов модификаторов, таких как `.Reply()`, `.At()`, `.AtAll()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Конфигурация

MatrixAdapter поддерживает конфигурацию нескольких аккаунтов, каждый аккаунт имеет собственную конфигурацию сервера homeserver и данных аутентификации.

```toml
# config.toml
# Аккаунт 1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Адрес сервера Matrix (обязательно)
access_token = "YOUR_ACCESS_TOKEN"          # Токен доступа (обязательно, либо с user_id+password)
user_id = ""                                # ID пользователя Matrix (например @bot:matrix.org)
password = ""                               # Пароль пользователя Matrix
auto_accept_invites = true                  # Автоматически принимать приглашения в комнаты (опционально, по умолчанию true)
enabled = true                              # Включить аккаунт (опционально, по умолчанию true)

# Аккаунт 2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> Совместимость со старой конфигурацией: если обнаружена старая одиночная конфигурация `[Matrix_Adapter]` (с access_token), она автоматически переносится в `accounts.default`.

**Описание параметров (для каждого аккаунта):**
- `homeserver`: Адрес сервера Matrix (обязательно), по умолчанию `https://matrix.org`
- `access_token`: Токен доступа, можно получить из клиента Matrix. Если токен уже известен, просто введите его
- `user_id`: ID пользователя Matrix (например `@bot:matrix.org`), используется вместе с `password` для входа
- `password`: Пароль пользователя Matrix, используется для автоматического входа и получения access_token
- `auto_accept_invites`: Автоматически принимать приглашения в комнаты, по умолчанию `true`
- `enabled`: Включить этот аккаунт (опционально, по умолчанию true)

**Способы аутентификации:**
- Способ 1 (рекомендуется): Прямое указание `access_token`
- Способ 2: Указание `user_id` и `password`, адаптер автоматически вызывает интерфейс входа для получения токена

## Обновление парадигмы v5 (4.2.0)

- **Наследование BaseConverter**: общие поля конвертера строятся фреймворком build_base_event
- **DSL API**: get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + метадействия
- **Дополнение к событию сообщения message_id** (event_id); таблица регистрации сообщений поддерживает delete_message
- **Принадлежность задачи spawn_background**: синхронные/пинговые задачи используют runtime.spawn_background
- **Мягкая зависимость фреймворка**: проверка версии ErisPulse>=2.7.1 и вывод подсказки; вывод логов версии при запуске
- У Matrix нет встроенной возможности кнопок, стандартный сегмент keyboard игнорируется (без ошибок)

### Примеры стандартных действий API

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms
await matrix.Api.delete_message(event_id)            # redact (таблица регистрации дополняет room_id)
```

---

### Поддерживаемые возможности платформ

- **События**: сообщения (m.room.message: текст/изображение/файл/аудио/видео/ответ/редактирование), изменение участников (m.room.member), изменение названия комнаты и другие статусные события
- **Сессии**: личные сообщения (автоматическое обнаружение комнат DM) / группы (комнаты); отправка поддерживает Text/Image/File/Voice/Video/Markdown/Raw_ob12
- **API**: whoami/profile/joined_rooms/статус комнаты/список участников/leave/redact (см. выше DSL API)

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочки вызовов, например:
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка обычного текстового сообщения.
- `.Image(file: bytes | str)` — отправка сообщения с изображением, поддержка путей к файлу, URL, MXC URI, двоичных данных.
- `.Voice(file: bytes | str)` — отправка сообщения с голосовым сообщением, поддержка путей к файлу, URL, MXC URI, двоичных данных.
- `.Video(file: bytes | str)` — отправка сообщения с видео, поддержка путей к файлу, URL, MXC URI, двоичных данных.
- `.File(file: bytes | str, filename: str = "")` — отправка сообщения с файлом, поддержка путей к файлу, URL, MXC URI, двоичных данных.
- `.Notice(text: str)` — отправка уведомления (типа m.notice в Matrix).
- `.Html(html: str, fallback: str = "")` — отправка сообщения в формате HTML, поддержка содержимого с разметкой.
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

### Цепочные методы модификации (можно комбинировать)

Цепочные методы возвращают `self`, поддерживают цепочку вызовов, должны быть вызваны перед окончательным методом отправки:

- `.Reply(message_id: str)` — ответ на указанное сообщение (используется связь Matrix `m.in_reply_to`).
- `.At(user_id: str)` — упоминание пользователя (реализуется через поле Matrix `m.mentions`).
- `.AtAll()` — упоминание всех пользователей в комнате (реализуется через упоминание `@room` в Matrix).

### Примеры цепочечного вызова

```python
# Базовая отправка
await matrix.Send.To("user", dm_room_id).Text("Hello")

# Ответ на сообщение
await matrix.Send.To("group", room_id).Reply("$event_id").Text("Ответ на сообщение")

# Упоминание пользователя
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("Привет")

# Упоминание всех пользователей
await matrix.Send.To("group", room_id).AtAll().Text("Объявление")

# Комбинация: ответ + упоминание
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("Составное сообщение")

# Отправка HTML-сообщения
await matrix.Send.To("group", room_id).Html("<h1>Заголовок</h1><p>Содержимое</p>", fallback="Заголовок\nСодержимое")

# Отправка уведомления
await matrix.Send.To("group", room_id).Notice("Системное уведомление")
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость сообщений между платформами:

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# Сложное сообщение
ob12_msg = [
    {"type": "text", "data": {"text": "Посмотри на это изображение: "}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "Круто, да?"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно непосредственно ожидать, чтобы получить результат отправки. Возвращаемый результат соответствует стандартизированному спецификации возврата адаптера ErisPulse:

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
| 32000 | Таймаут запроса или ошибка при загрузке медиафайла |
| 33000 | Аномалия вызова API |
| 34000 | API вернул неожиданный формат или произошла бизнес-ошибка |

## Типы событий, специфичные для Matrix

Необходимо проверить `platform=="matrix"`, чтобы использовать функции, специфичные для этой платформы.

### Основные отличия

1. **Децентрализованная архитектура**: Matrix - это децентрализованный протокол обмена сообщениями. Формат идентификатора пользователя: `@user:server.domain`, формат идентификатора комнаты: `!room_id:server.domain`
2. **Концепция комнат**: В Matrix нет различия между групповыми и личными чатами, все переговоры представляются как "комнаты". Адаптер автоматически определяет личные комнаты по данным аккаунта DM (Direct Message)
3. **Синхронизация с Long Polling**: Используется API `/sync` для получения новых событий с помощью длинного опроса, а не WebSocket
4. **MXC URI**: Ссылки на медиафайлы имеют формат `mxc://server.domain/media_id`
5. **HTML-форматированный текст**: Поддерживается отправка сообщений в формате HTML через `formatted_body`
6. **Реакции на сообщения**: Поддерживается реакция на сообщения с помощью эмодзи (Reaction), отличная от традиционного ответа на сообщение
7. **Редактирование сообщений**: Поддерживается редактирование отправленных сообщений через `m.replace`
8. **Отмена сообщений**: Поддерживается отмена/удаление сообщений с помощью `m.room.redaction`

### Расширенные поля

- Все специфичные поля имеют префикс `matrix_`
- Исходные данные сохраняются в поле `matrix_raw`
- `matrix_raw_type` указывает тип исходного события Matrix (например, `m.room.message`, `m.room.member`)

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

# Отмена сообщения
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

Сообщения Matrix автоматически преобразуются в соответствующие типы сообщений в зависимости от `msgtype`:

| msgtype | Тип сообщения | Описание |
|---|---|---|
| m.text | `text` | Текстовое сообщение |
| m.notice | `text` | Уведомление |
| m.emote | `text` | Сообщение о действии |
| m.image | `image` | Сообщение с изображением |
| m.audio | `voice` | Аудиосообщение |
| m.video | `video` | Видеосообщение |
| m.file | `file` | Сообщение с файлом |
| m.location | `location` | Сообщение с геолокацией |

Пример структуры сообщения:

```json
// Текстовое сообщение (с HTML)
{
  "type": "text",
  "data": {
    "text": "Содержание текста",
    "html": "<b>Содержание HTML</b>"
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

// Сообщение с геолокацией
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

MatrixAdapter регистрирует следующие методы Event Mixin, которые можно вызывать непосредственно в обработчике событий:

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_room_id()` | `str` | Получить идентификатор комнаты |
| `get_matrix_event_type()` | `str` | Получить тип исходного события Matrix |
| `get_matrix_sender()` | `str` | Получить идентификатор отправителя |
| `get_reaction_key()` | `str` | Получить эмодзи реакции |
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

## Синхронизация API

### Синхронный процесс

1. Аутентификация с использованием `access_token` или `user_id` + `password`
2. Вызов `/_matrix/client/v3/account/whoami` для получения `bot_user_id`
3. Отправка метасобытия `connect`
4. Выполнение начальной синхронизации (`/_matrix/client/v3/sync?timeout=0`) для получения токена `next_batch`
5. Обнаружение личных чатов (DM) (отправка запроса `/_matrix/client/v3/user/{user_id}/account_data/m.direct`)
6. Начало цикла Long Polling синхронизации (отправка запроса `/_matrix/client/v3/sync?since={next_batch}&timeout=30000`)
7. Обработка новых событий, возвращаемых при каждой синхронизации, и их преобразование для отправки

### Механизм поддержания соединения

- Адаптер отправляет метасобытие `heartbeat` каждые 30 секунд
- При успешном подключении отправляется метасобытие `connect`
- При закрытии соединения отправляется метасобытие `disconnect`

### Приглашения в комнаты

- При получении приглашения в комнату (комната с состоянием `invite`), если в конфигурации `auto_accept_invites` установлено значение `true` (по умолчанию), адаптер автоматически присоединяется к комнате
- Для присоединения к комнате вызывается интерфейс `/_matrix/client/v3/join/{room_id}`

## Примеры использования

### Обработка групповых сообщений

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

### Отправка медиа-сообщений

```python
# Отправка изображения (по URL)
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# Отправка изображения (по MXC URI)
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# Отправка изображения (по бинарным данным)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# Отправка изображения (по локальному пути)
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
        # Обработка отредактированного сообщения...
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
        print(f"Пользователь {user_id} был исключён, оператор: {operator_id}")
```