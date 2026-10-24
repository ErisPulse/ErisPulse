# Документация по функциональным возможностям платформы Matrix

MatrixAdapter — это адаптер, построенный на основе протокола [Matrix](https://spec.matrix.org/), объединяющий все основные функциональные модули протокола Matrix и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Соответствующая версия модуля: 4.4.0
- Ответственный: ErisPulse

## Основная информация

- Краткое описание платформы: Matrix — это открытый, децентрализованный протокол обмена сообщениями, поддерживающий личные сообщения, группы и другие сценарии
- Название адаптера: MatrixAdapter
- Поддержка нескольких аккаунтов: Поддерживает одновременную настройку нескольких аккаунтов Matrix
- Способ подключения: Long Polling (через API синхронизации Matrix `/sync`)
- Способ аутентификации: Получение токена через access_token или user_id + password
- Поддержка цепочечных модификаторов: Поддерживает методы цепочечных модификаторов, такие как `.Reply()`、`.At()`、`.AtAll()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Инструкция по настройке

MatrixAdapter поддерживает настройку нескольких аккаунтов, каждый из которых имеет отдельные настройки сервера homeserver и аутентификации.

```toml
# config.toml
# Аккаунт 1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Адрес сервера Matrix (обязательно)
access_token = "YOUR_ACCESS_TOKEN"          # Токен доступа (обязательно, если не указан user_id+password)
user_id = ""                                # ID пользователя Matrix (например, @bot:matrix.org)
password = ""                               # Пароль пользователя Matrix
auto_accept_invites = true                  # Автоматически принимать приглашения в комнаты (опционально, по умолчанию true)
enabled = true                              # Включить аккаунт (опционально, по умолчанию true)

# Аккаунт 2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> Совместимость со старыми настройками: Если обнаружена старая одиночная конфигурация `[Matrix_Adapter]` (с access_token), она автоматически переносится в `accounts.default`.

**Описание параметров (для каждого аккаунта):**
- `homeserver`: Адрес сервера Matrix (обязательно), по умолчанию `https://matrix.org`
- `access_token`: Токен доступа, можно получить в клиенте Matrix. Если уже есть токен, просто введите его
- `user_id`: ID пользователя Matrix (например, `@bot:matrix.org`), используется вместе с `password` для входа
- `password`: Пароль пользователя Matrix, используется для автоматического входа и получения access_token
- `auto_accept_invites`: Автоматически принимать приглашения в комнаты, по умолчанию `true`
- `enabled`: Включить этот аккаунт (опционально, по умолчанию true)

**Способы аутентификации:**
- Способ 1 (рекомендуется): Непосредственно предоставить `access_token`
- Способ 2: Предоставить `user_id` и `password`, адаптер автоматически вызовет интерфейс входа и получит токен

## Обновление до версии v5 (4.2.0)

- **Наследование BaseConverter**: Общие поля конвертера строятся с помощью build_base_event фреймворка
- **DSL API**: get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + метадействия
- **Дополнение к сообщению message_id** (event_id); таблица регистрации сообщений поддерживает delete_message
- **Принадлежность задачи spawn_background**: Синхронные/心跳-задачи используют runtime.spawn_background
- **Мягкая зависимость от фреймворка**: При запуске проверяется ErisPulse>=2.7.1 и выводится предупреждение; при запуске выводится лог версии
- Matrix не имеет встроенной поддержки кнопок, стандартный сегмент keyboard игнорируется (без ошибок)

## Защита конфиденциальности (4.3.0)

Начиная с версии 4.3.0, адаптер нативно поддерживает защиту конфиденциальности в зашифрованных комнатах (на основе matrix-nio[e2e] / vodozemac):

```toml
[Matrix_Adapter.accounts.default]
user_id = "@bot:matrix.org"
password = "YOUR_PASSWORD"
encryption_enabled = true       # Включить (по умолчанию false, существующие развертывания не затрагиваются)
trust_all_devices = true        # Автоматически доверять не проверенным устройствам (по умолчанию; false — строгий режим)
```

- Сообщения в зашифрованных комнатах автоматически шифруются и дешифруются, медиа-файлы также зашифрованы (`m.file.encrypted`)
- `device_id` автоматически анализируется и сохраняется; сессии хранятся в `store_path` (по умолчанию `data/matrix/<имя аккаунта>`, **не удалять**, иначе история сообщений не сможет быть дешифрована)
- Mixin событий добавляет `event.is_encrypted()`; медиа-сегмент содержит `matrix_encrypted_file` (JWK), можно расшифровать с помощью `MatrixAdapter.decrypt_media()`
- Не поддерживается кросс-подпись и резервное копирование ключей на стороне сервера; требуется Python >= 3.10
- При отключении или отсутствии matrix-nio адаптер автоматически переходит в режим без шифрования

Подробная информация доступна в [README адаптера](https://github.com/ErisPulse/ErisPulse-MatrixAdapter).

### Примеры стандартных API действий

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms
await matrix.Api.delete_message(event_id)            # redact (таблица регистрации дополняет room_id)
```

---

### Поддерживаемые возможности платформы

- **События**: Сообщения (m.room.message: текст, изображения, файлы, аудио/видео, ответы, редактирование), изменения участников (m.room.member), изменение названия комнаты и другие статусные события
- **Сессии**: Личные сообщения (DM-комнаты автоматически обнаруживаются) / группы (комнаты); отправка поддерживает Text/Image/File/Voice/Video/Markdown/Raw_ob12
- **API**: whoami/profile/joined_rooms/статус комнаты/список участников/leave/redact (см. выше DSL API)

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочечную синтаксическую конструкцию, например:
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`: Отправка текстового сообщения.
- `.Image(file: bytes | str)`: Отправка изображения, поддерживает путь к файлу, URL, MXC URI, бинарные данные.
- `.Voice(file: bytes | str)`: Отправка голосового сообщения, поддерживает путь к файлу, URL, MXC URI, бинарные данные.
- `.Video(file: bytes | str)`: Отправка видео, поддерживает путь к файлу, URL, MXC URI, бинарные данные.
- `.File(file: bytes | str, filename: str = "")`: Отправка файла, поддерживает путь к файлу, URL, MXC URI, бинарные данные.
- `.Notice(text: str)`: Отправка уведомления (тип m.notice в Matrix).
- `.Html(html: str, fallback: str = "")`: Отправка HTML-форматированного сообщения, поддерживает богатый текст.
- `.MergeForward(nodes, title="Слияние чат-записей")`: Отправка объединенного сообщения (formatted_body blockquote-формат; белый список удаляет details/внутренние стили).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Отправка сообщения в формате OneBot12.

### Цепочечные модификаторы (можно комбинировать)

Методы цепочечных модификаторов возвращают `self`, поддерживают цепочечное использование и должны вызываться до окончательного метода отправки:

- `.Reply(message_id: str)`: Ответ на указанное сообщение (через отношение Matrix `m.in_reply_to`).
- `.At(user_id: str)`: Упоминание указанного пользователя (через поле Matrix `m.mentions`).
- `.AtAll()`: Упоминание всех участников комнаты (через упоминание `@room` в Matrix).

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

# Комбинированное использование: ответ + упоминание
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("Составное сообщение")

# Отправка HTML-сообщения
await matrix.Send.To("group", room_id).Html("<h1>Заголовок</h1><p>Содержимое</p>", fallback="Заголовок\nСодержимое")

# Отправка уведомления
await matrix.Send.To("group", room_id).Notice("Системное уведомление")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость между платформами:

```python
# Отправка сообщения OneBot12
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

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно ожидать с помощью await для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату возврата адаптера ErisPulse:

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
| 32000 | Таймаут запроса или ошибка загрузки медиа |
| 33000 | Ошибка вызова API |
| 34000 | API вернул неожиданный формат или бизнес-ошибку |

## Уникальные типы событий

Необходимо использовать платформенные особенности с проверкой `platform=="matrix"`

### Основные отличия

1. **Децентрализованная архитектура**: Matrix — это децентрализованный протокол обмена сообщениями, формат ID пользователя: `@user:server.domain`, формат ID комнаты: `!room_id:server.domain`
2. **Концепция комнат**: Matrix не различает личные и групповые чаты, все сессии — это «комнаты». Адаптер автоматически определяет личные комнаты по данным аккаунта DM (Direct Message)
3. **Долгое опросное синхронизирование**: Используется API `/sync` для получения новых событий с помощью долгого опроса, а не WebSocket
4. **MXC URI**: Ссылки на медиа-файлы имеют формат `mxc://server.domain/media_id`
5. **HTML-форматированный текст**: Поддерживает отправку HTML-форматированных сообщений через `formatted_body`
6. **Реакции на сообщения**: Поддерживает реакции на уровне сообщений (Reaction), отличается от традиционного ответа
7. **Редактирование сообщений**: Поддерживает редактирование отправленных сообщений через отношение `m.replace`
8. **Удаление сообщений**: Поддерживает удаление/редактирование сообщений через `m.room.redaction`

### Расширенные поля

- Все специфические поля имеют префикс `matrix_`
- Оригинальные данные сохраняются в поле `matrix_raw`
- `matrix_raw_type` указывает тип исходного события Matrix (например, `m.room.message`, `m.room.member`)

### Примеры специальных полей

```python
# Групповое сообщение
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

# Сообщение в потоке
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### Типы сообщений

Сообщения Matrix автоматически преобразуются в соответствующие типы сообщений в зависимости от `msgtype`:

| msgtype | Преобразованный тип | Описание |
|---|---|---|
| m.text | `text` | Текстовое сообщение |
| m.notice | `text` | Уведомление |
| m.emote | `text` | Сообщение о действиях |
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
    "text": "Чистый текст",
    "html": "<b>HTML-контент</b>"
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

// Местоположение
{
  "type": "location",
  "data": {
    "latitude": 0.0,
    "longitude": 0.0,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "Пекин, Китай"
  }
}
```

### Методы Event Mixin

MatrixAdapter регистрирует следующие методы Mixin для событий, которые можно вызывать непосредственно в обработке событий:

| Метод | Возвращаемый тип | Описание |
|------|----------|------|
| `get_room_id()` | `str` | Получить ID комнаты |
| `get_matrix_event_type()` | `str` | Получить тип исходного события Matrix |
| `get_matrix_sender()` | `str` | Получить ID отправителя |
| `get_reaction_key()` | `str` | Получить реакцию |
| `is_edited()` | `bool` | Проверить, является ли сообщение отредактированным |
| `is_notice()` | `bool` | Проверить, является ли сообщение типом m.notice |

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

## Синхронизация через API

### Процесс синхронизации

1. Аутентификация с использованием access_token или user_id + password
2. Вызов `/_matrix/client/v3/account/whoami` для получения bot_user_id
3. Выдача метасобытия connect
4. Выполнение начальной синхронизации (`/_matrix/client/v3/sync?timeout=0`) для получения токена `next_batch`
5. Обнаружение DM-комнат (`/_matrix/client/v3/user/{user_id}/account_data/m.direct`)
6. Начало цикла синхронизации с Long Polling (`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`)
7. Обработка новых событий после каждой синхронизации и их преобразование

### Механизм таймера

- Адаптер каждые 30 секунд выдает метасобытие `heartbeat`
- При успешном подключении выдается метасобытие `connect`
- При отключении выдается метасобытие `disconnect`

### Приглашения в комнаты

- При получении приглашения в комнату (состояние `invite`), если `auto_accept_invites` настроено как `true` (по умолчанию), адаптер автоматически присоединяется к комнате
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

### Отправка медиа-сообщений

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

# Отправка файла (с именем)
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="Документ.pdf")
```

### Обработка редактированных сообщений

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