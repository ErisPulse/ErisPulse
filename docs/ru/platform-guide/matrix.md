# Документация по функциям платформы Matrix

MatrixAdapter — это адаптер, построенный на основе протокола [Matrix](https://spec.matrix.org/), объединяющий все основные функциональные модули протокола Matrix и предоставляющий единый интерфейс обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия соответствующего модуля: 4.2.0
- Ответственный: ErisPulse

## Основная информация

- Краткое описание платформы: Matrix — это открытый децентрализованный протокол связи, поддерживающий личные сообщения, группы и другие сценарии.
- Название адаптера: MatrixAdapter
- Поддержка нескольких аккаунтов: Поддерживает одновременную настройку нескольких аккаунтов Matrix
- Способ подключения: Long Polling (через API синхронизации Matrix `/sync`)
- Способ аутентификации: На основе access_token или user_id + password для получения токена
- Поддержка цепочки модификаторов: Поддерживает цепочечные методы модификации, такие как `.Reply()`, `.At()`, `.AtAll()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Описание конфигурации

MatrixAdapter поддерживает многоконтурную конфигурацию, где каждый аккаунт имеет отдельные настройки homeserver и аутентификации.

```toml
# config.toml
# Аккаунт 1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Адрес сервера Matrix (обязательно)
access_token = "YOUR_ACCESS_TOKEN"          # Токен доступа (обязательно, если не указан user_id и password)
user_id = ""                                # ID пользователя Matrix (например, @bot:matrix.org)
password = ""                               # Пароль пользователя Matrix
auto_accept_invites = true                  # Автоматически принимать приглашения в комнаты (необязательно, по умолчанию true)
enabled = true                              # Включить аккаунт (необязательно, по умолчанию true)

# Аккаунт 2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> Совместимость с предыдущей конфигурацией: Если обнаружена старая одноконтурная конфигурация `[Matrix_Adapter]` (с access_token), автоматически переносится в `accounts.default`.

**Описание параметров (для каждого аккаунта):**
- `homeserver`: Адрес сервера Matrix (обязательно), по умолчанию `https://matrix.org`
- `access_token`: Токен доступа, можно получить из клиента Matrix. Если уже есть токен, просто введите его
- `user_id`: ID пользователя Matrix (например, `@bot:matrix.org`), используется вместе с `password` для входа
- `password`: Пароль пользователя Matrix, используется для автоматического входа и получения access_token
- `auto_accept_invites`: Автоматически принимать приглашения в комнаты, по умолчанию `true`
- `enabled`: Включить аккаунт (необязательно, по умолчанию true)

**Способы аутентификации:**
- Способ 1 (рекомендуется): Прямое предоставление `access_token`
- Способ 2: Предоставление `user_id` и `password`, адаптер автоматически вызывает интерфейс входа для получения токена

## Обновление формата v5 (4.2.0)

- **BaseConverter наследование**: Общие поля конвертера строятся с помощью build_base_event фреймворка
- **Api DSL**: get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + мета-действия
- **Дополнение сообщений event message_id** (event_id); таблица регистрации сообщений поддерживает delete_message
- **Принадлежность задачи spawn_background**: Синхронные/сердцебиение задачи используют runtime.spawn_background
- **Мягкая зависимость фреймворка**: Проверка ErisPulse>=2.7.1 в процессе выполнения и вывод предупреждения; вывод версии лога при запуске
- Matrix не имеет встроенных кнопок, стандартный сегмент keyboard игнорируется (не вызывает ошибку)

## Криптография с конечной точкой (4.3.0)

Начиная с версии 4.3.0, адаптер нативно поддерживает конечную криптографию для комнат с шифрованием (на основе matrix-nio[e2e] / vodozemac):

```toml
[Matrix_Adapter.accounts.default]
user_id = "@bot:matrix.org"
password = "YOUR_PASSWORD"
encryption_enabled = true       # Включить (по умолчанию false, существующие развертывания не затрагиваются)
trust_all_devices = true        # Автоматически доверять не проверенным устройствам (по умолчанию; false для строгого режима)
```

- Сообщения в зашифрованных комнатах автоматически шифруются и расшифровываются, медиа-файлы шифруются с конечной точкой (m.file.encrypted)
- device_id автоматически анализируется и сохраняется; сессии хранятся в `store_path` (по умолчанию `data/matrix/<имя аккаунта>`, **не удаляйте**, иначе исторические сообщения невозможно будет расшифровать)
- Event Mixin добавляет `event.is_encrypted()`; медиа-сегмент содержит `matrix_encrypted_file` (JWK), можно расшифровать с помощью `MatrixAdapter.decrypt_media()`
- Не поддерживается кросс-подпись и резервное копирование ключей на стороне сервера; требуется Python >= 3.10
- При отключении или отсутствии matrix-nio автоматически возвращается к режиму незашифрованных сообщений

Подробное описание см. в [README адаптера](https://github.com/ErisPulse/ErisPulse-MatrixAdapter).

### Примеры стандартных API-действий

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms
await matrix.Api.delete_message(event_id)            # redact (заполнение таблицы room_id)
```

---

### Поддерживаемые возможности платформы

- **События**: Сообщения (m.room.message: текст/изображение/файл/аудио/видео/ответ/редактирование), изменения участников (m.room.member), изменение названия комнаты и другие статусные события
- **Сессии**: Личные сообщения (DM-комнаты автоматически обнаруживаются) / группы (комнаты); отправка поддерживает Text/Image/File/Voice/Video/Markdown/Raw_ob12
- **API**: whoami/profile/joined_rooms/состояние комнаты/список участников/leave/redact (см. выше Api DSL)

---

## Поддерживаемые типы отправки сообщений

Все методы отправки сообщений реализованы через цепочечный синтаксис, например:
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка текстового сообщения.
- `.Image(file: bytes | str)` — отправка изображения, поддерживает путь к файлу, URL, MXC URI, двоичные данные.
- `.Voice(file: bytes | str)` — отправка голосового сообщения, поддерживает путь к файлу, URL, MXC URI, двоичные данные.
- `.Video(file: bytes | str)` — отправка видеосообщения, поддерживает путь к файлу, URL, MXC URI, двоичные данные.
- `.File(file: bytes | str, filename: str = "")` — отправка файла, поддерживает путь к файлу, URL, MXC URI, двоичные данные.
- `.Notice(text: str)` — отправка уведомления (тип m.notice в Matrix).
- `.Html(html: str, fallback: str = "")` — отправка HTML-форматированного сообщения, поддерживает богатый текст.
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

### Цепочечные модификаторы (можно использовать вместе)

Цепочечные модификаторы возвращают `self`, поддерживают цепочечный вызов, должны быть вызваны перед окончательным методом отправки:

- `.Reply(message_id: str)` — ответить на указанное сообщение (через отношение Matrix `m.in_reply_to`).
- `.At(user_id: str)` — упомянуть пользователя (через поле Matrix `m.mentions`).
- `.AtAll()` — упомянуть всех пользователей в комнате (через упоминание `@room` в Matrix).

### Примеры цепочечного вызова

```python
# Базовая отправка
await matrix.Send.To("user", dm_room_id).Text("Hello")

# Ответ на сообщение
await matrix.Send.To("group", room_id).Reply("$event_id").Text("Ответное сообщение")

# Упоминание пользователя
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("Привет")

# Упоминание всех пользователей
await matrix.Send.To("group", room_id).AtAll().Text("Объявление")

# Комбинированное использование: ответ + упоминание
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("Сложное сообщение")

# Отправка HTML-сообщения
await matrix.Send.To("group", room_id).Html("<h1>Заголовок</h1><p>Содержание</p>", fallback="Заголовок\nСодержание")

# Отправка уведомления
await matrix.Send.To("group", room_id).Notice("Системное уведомление")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку OneBot12-сообщений, что упрощает совместимость сообщений между платформами:

```python
# Отправка OneBot12-сообщения
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# Сложное сообщение
ob12_msg = [
    {"type": "text", "data": {"text": "Посмотрите на это изображение: "}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "Неплохо, правда? "}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно ожидать для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "message_id": "$event_id", // ID события Matrix
    "message": "",            // Сообщение об ошибке
    "matrix_raw": {...}       // Оригинальные данные ответа
}
```

### Описание кодов ошибок

| retcode | Описание |
|---------|----------|
| 0 | Успешно |
| 32000 | Превышен таймаут запроса или не удалось загрузить медиафайл |
| 33000 | Ошибка вызова API |
| 34000 | API вернул неожиданный формат или бизнес-ошибка |

## Специфические типы событий

Необходимо использовать платформенные особенности с проверкой `platform=="matrix"`

### Основные отличия

1. **Децентрализованная архитектура**: Matrix — это децентрализованный протокол связи, формат ID пользователя: `@user:server.domain`, формат ID комнаты: `!room_id:server.domain`
2. **Концепция комнаты**: Matrix не различает чаты и личные сообщения, все сессии — это "комнаты". Адаптер автоматически определяет личные комнаты по данным учетной записи DM (Direct Message)
3. **Долгое опросное синхронизирование**: Используется API `/sync` для получения новых событий с помощью долгого опроса, а не WebSocket
4. **MXC URI**: Ссылки на медиафайлы через формат `mxc://server.domain/media_id`
5. **HTML-форматированный текст**: Поддержка отправки HTML-форматированных сообщений через `formatted_body`
6. **Реакции на сообщения**: Поддержка реакций на уровне сообщений (Reaction), отличается от традиционного ответа на сообщение
7. **Редактирование сообщений**: Поддержка редактирования отправленных сообщений через отношение `m.replace`
8. **Удаление сообщений**: Поддержка удаления/редактирования сообщений через `m.room.redaction`

### Расширенные поля

- Все специфические поля имеют префикс `matrix_`
- Оригинальные данные сохраняются в поле `matrix_raw`
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

### Типы сегментов сообщений

Matrix сообщения автоматически преобразуются в соответствующие сегменты сообщений в зависимости от `msgtype`:

| msgtype | Преобразованный тип | Описание |
|---|---|---|
| m.text | `text` | Текстовое сообщение |
| m.notice | `text` | Уведомление |
| m.emote | `text` | Сообщение действия |
| m.image | `image` | Сообщение изображения |
| m.audio | `voice` | Голосовое сообщение |
| m.video | `video` | Видеосообщение |
| m.file | `file` | Сообщение файла |
| m.location | `location` | Сообщение локации |

Пример структуры сегмента сообщения:

```json
// Текстовое сообщение (с HTML)
{
  "type": "text",
  "data": {
    "text": "Содержание текста",
    "html": "<b>HTML-содержание</b>"
  }
}

// Сообщение изображения
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

// Сообщение локации
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

MatrixAdapter зарегистрировал следующие методы Event Mixin, которые можно вызывать прямо в обработке событий:

| Метод | Возвращаемый тип | Описание |
|------|----------|------|
| `get_room_id()` | `str` | Получить ID комнаты |
| `get_matrix_event_type()` | `str` | Получить тип исходного события Matrix |
| `get_matrix_sender()` | `str` | Получить ID отправителя |
| `get_reaction_key()` | `str` | Получить ключ реакции |
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

## Sync API подключение

### Процесс синхронизации

1. Аутентификация с использованием access_token или user_id + password
2. Вызов `/_matrix/client/v3/account/whoami` для получения bot_user_id
3. Генерация мета-события connect
4. Выполнение начальной синхронизации (`/_matrix/client/v3/sync?timeout=0`) для получения токена `next_batch`
5. Обнаружение DM-комнат (`/_matrix/client/v3/user/{user_id}/account_data/m.direct`)
6. Начало цикла синхронизации с долгим опросом (`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`)
7. Обработка каждого нового события и его преобразование для отправки

### Механизм сердцебиения

- Адаптер генерирует событие `heartbeat` каждые 30 секунд
- При успешном подключении генерируется событие `connect`
- При отключении генерируется событие `disconnect`

### Приглашения в комнаты

- При получении приглашения в комнату (комната в состоянии `invite`), если параметр `auto_accept_invites` установлен в `true` (по умолчанию), адаптер автоматически присоединяется к комнате
- Присоединение к комнате вызывает интерфейс `/_matrix/client/v3/join/{room_id}`

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

### Отправка медиафайлов

```python
# Отправка изображения (URL)
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# Отправка изображения (MXC URI)
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# Отправка изображения (двоичные данные)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# Отправка изображения (локальный путь к файлу)
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# Отправка файла (с именем файла)
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

### Обработка изменений участников

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