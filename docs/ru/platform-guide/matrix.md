# Документация по функциям платформы Matrix

MatrixAdapter — это адаптер, построенный на основе протокола [Matrix](https://spec.matrix.org/), объединяющий все основные модули протокола Matrix и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия модуля: 4.6.1
- Поддержка: ErisPulse
- Последнее обновление: 2026-11-10

## Основная информация

- Краткое описание платформы: Matrix — это открытый децентрализованный протокол связи, поддерживающий личные сообщения, группы и другие сценарии.
- Название адаптера: MatrixAdapter
- Поддержка нескольких аккаунтов: Поддерживает одновременную настройку нескольких аккаунтов Matrix.
- Способ подключения: Long Polling (через Matrix Sync API `/sync`)
- Способ аутентификации: Аутентификация по access_token или user_id + password для получения токена
- Поддержка цепочки модификаторов: Поддерживает методы цепочки модификаторов, такие как `.Reply()`, `.At()`, `.AtAll()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Инструкции по настройке

MatrixAdapter поддерживает настройку нескольких аккаунтов, каждый аккаунт имеет отдельные настройки homeserver и аутентификации.

```toml
# config.toml
# Аккаунт 1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Адрес сервера Matrix (обязательно)
access_token = "YOUR_ACCESS_TOKEN"          # Токен доступа (либо access_token, либо user_id+password)
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

> Совместимость со старыми настройками: Если обнаруживается старая одиночная конфигурация `[Matrix_Adapter]` (с access_token), она автоматически мигрируется в `accounts.default`.

**Описание параметров конфигурации (для каждого аккаунта):**
- `homeserver`: Адрес сервера Matrix (обязательно), по умолчанию `https://matrix.org`
- `access_token`: Токен доступа, можно получить из клиента Matrix. Если уже есть токен, просто введите его
- `user_id`: ID пользователя Matrix (например, `@bot:matrix.org`), используется вместе с `password` для входа
- `password`: Пароль пользователя Matrix, используется для автоматического входа и получения access_token
- `auto_accept_invites`: Автоматически принимать приглашения в комнаты, по умолчанию `true`
- `enabled`: Включить этот аккаунт (опционально, по умолчанию true)
- `encryption_enabled`: Включить конфиденциальное шифрование (E2EE), по умолчанию `false`
- `trust_all_devices`: Автоматически доверять не проверенным устройствам (E2EE), по умолчанию `true`
- `device_id`: ID устройства (E2EE, обычно автоматически получается, не нужно заполнять)
- `store_path`: Путь к хранилищу сессий шифрования (E2EE), по умолчанию `data/matrix/<имя аккаунта>`

**Способы аутентификации:**
- Способ 1 (рекомендуется): Просто предоставить `access_token`
- Способ 2: Предоставить `user_id` и `password`, адаптер автоматически вызовет интерфейс входа для получения токена

## Обновление до формата v5 (4.2.0)

- **Наследование BaseConverter**: Общие поля конвертера строятся с помощью фреймворка build_base_event
- **Api DSL**: get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + мета-действия
- **Дополнение message_id в сообщениях (event_id)**; таблица сообщений поддерживает delete_message
- **Задачи spawn_background**: Синхронные/心跳-задачи используют runtime.spawn_background
- **Мягкая зависимость фреймворка**: Проверка ErisPulse>=2.7.1 и вывод версии при запуске
- Matrix не имеет встроенной поддержки кнопок, стандартный сегмент keyboard игнорируется (без ошибок)

## Конфиденциальное шифрование (4.3.0)

Начиная с версии 4.3.0, адаптер нативно поддерживает конфиденциальное шифрование комнат Matrix (на основе matrix-nio[e2e]/vodozemac):

```toml
[Matrix_Adapter.accounts.default]
user_id = "@bot:matrix.org"
password = "YOUR_PASSWORD"
encryption_enabled = true       # Включить (по умолчанию false, существующие развертывания не затронуты)
trust_all_devices = true        # Автоматически доверять не проверенным устройствам (по умолчанию; false — строгий режим)
```

- Сообщения в зашифрованных комнатах автоматически расшифровываются и шифруются, медиа-файлы зашифрованы (m.file.encrypted)
- `device_id` автоматически анализируется и сохраняется; сессии хранятся в `store_path` (по умолчанию `data/matrix/<имя аккаунта>`, **не удаляйте**, иначе невозможно расшифровать историю сообщений)
- В Mixin событий добавлен метод `event.is_encrypted()`; медиа-сегменты содержат `matrix_encrypted_file` (JWK), можно расшифровать с помощью `MatrixAdapter.decrypt_media()`
- Не поддерживается перекрестное подписание и резервное копирование ключей на стороне сервера; требуется Python >= 3.10
- При отключении или отсутствии matrix-nio автоматически возвращается к режиму незашифрованных сообщений

Подробности см. в разделе [Конфиденциальное шифрование (E2EE)](#конфиденциальное-шифрование-e2ee) и [README адаптера](https://github.com/ErisPulse/ErisPulse-MatrixAdapter).

## Стандартизация

В этом разделе описаны действия адаптера, соответствующие стандартам ErisPulse. Подробности см. в документации SDK «Стандарты ответов API» (`docs/ru/standards/api-response.md`) и «Спецификации методов отправки» (`docs/ru/standards/send-method-spec.md`).

### Обработка нескольких аккаунтов (начиная с 4.6.1)

- Все события получают `self.account_id` (имя аккаунта-источника); аккаунты, аутентифицированные по access_token, корректно обрабатываются и маршрутизируются событий, даже если `user_id` пуст

### Стандартизация кодов ошибок (4.6.x)

- Ошибки при загрузке/скачивании медиа и таймауты запросов объединены в 33001 (ошибка сети)
- Ошибки платформы объединены в 34100 (ошибка платформы), код ошибки Matrix сохраняется в полях `message` и `matrix_raw`
- Отсутствие контекста для отмены 10003: `delete_message` возвращает ошибку параметра, если не найден контекст сообщения

| retcode | Описание |
|---------|----------|
| 0 | Успешно |
| 10002 | Не поддерживаемое действие (например, get_friend_list, у Matrix нет понятия друзей) |
| 10003 | Неверная цель отправки (невозможно распознать как комнату Matrix), отсутствие контекста для отмены |
| 33001 | Ошибка сети (ошибка загрузки/скачивания медиа, таймаут запроса) |
| 34100 | Ошибка платформы (код ошибки Matrix сохраняется в message и matrix_raw) |

### Спецификация метода Send

- Все методы Send читают `send_context`: в цепочке событий автоматически используется аккаунт источника, явно указанный `Using()` имеет приоритет
- HTML-методы: `.Html(html, fallback)` отправляет форматированное сообщение; `HTML` — стандартная форма написания (для совместимости с `Html` сохраняется)
- `get_group_list` возвращает каждое поле `group_name` (согласовано с `get_group_info`)

### Примеры стандартных действий API

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms (каждое поле содержит group_name)
await matrix.Api.delete_message(event_id)            # redact (запись дополнена room_id)
```

---

### Поддерживаемые возможности платформы

- **События**: Сообщения (m.room.message: текст/изображение/файл/аудио/видео/ответ/редактирование), изменение участников (m.room.member), изменение названия комнаты и другие статусные события
- **Сессии**: Личные сообщения (DM-комнаты автоматически обнаруживаются) / группы (комнаты); отправка поддерживает Text/Image/File/Voice/Video/Markdown/Raw_ob12
- **API**: whoami/profile/joined_rooms/статус комнаты/список участников/leave/redact (см. выше в Api DSL)

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с помощью цепочки вызовов, например:

```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:

- `.Text(text: str)` — отправка текстового сообщения.
- `.Image(file: bytes | str)` — отправка изображения, поддержка путей к файлам, URL, MXC URI, бинарных данных.
- `.Voice(file: bytes | str)` — отправка голосового сообщения, поддержка путей к файлам, URL, MXC URI, бинарных данных.
- `.Video(file: bytes | str)` — отправка видеосообщения, поддержка путей к файлам, URL, MXC URI, бинарных данных.
- `.File(file: bytes | str, filename: str = "")` — отправка файлового сообщения, поддержка путей к файлам, URL, MXC URI, бинарных данных.
- `.Notice(text: str)` — отправка уведомления (типа m.notice в Matrix).
- `.Html(html: str, fallback: str = "")` — отправка HTML-форматированного сообщения, поддержка богатого текста (HTML — стандартная форма написания, `Html` сохраняется для совместимости).
- `.MergeForward(nodes, title="Соединённые чат-записи")` — отправка объединённого пересылаемого сообщения (формат blockquote, белый список удаляет details/внутренние стили).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщений в формате OneBot12.

### Цепочные модификаторы (можно комбинировать)

Цепочные модификаторы возвращают `self`, поддерживают цепочку вызовов, должны вызываться до окончательного метода отправки:

- `.Reply(message_id: str)` — ответ на указанное сообщение (через отношение Matrix `m.in_reply_to`).
- `.At(user_id: str)` — упоминание пользователя (через поле Matrix `m.mentions`).
- `.AtAll()` — упоминание всех участников комнаты (через упоминание `@room` в Matrix).

### Примеры цепочечных вызовов

```python
# Базовая отправка ("user" поддерживает ID пользователя (@user:server, автоматически определяется DM-комната) или ID комнаты (!room:server)
await matrix.Send.To("user", "@alice:matrix.org").Text("Hello")

# Ответ на сообщение
await matrix.Send.To("group", room_id).Reply("$event_id").Text("Ответное сообщение")

# Упоминание пользователя
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("Привет")

# Упоминание всех
await matrix.Send.To("group", room_id).AtAll().Text("Анонс")

# Комбинированный вызов: ответ + упоминание
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("Сложное сообщение")

# Отправка HTML-сообщения
await matrix.Send.To("group", room_id).Html("<h1>Заголовок</h1><p>Содержимое</p>", fallback="Заголовок\nСодержимое")

# Отправка уведомления
await matrix.Send.To("group", room_id).Notice("Системное уведомление")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку OneBot12-сообщений, что упрощает совместимость между платформами:

```python
# Отправка OneBot12-сообщения
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# Сложное сообщение
ob12_msg = [
    {"type": "text", "data": {"text": "Посмотри на эту картинку: "}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "Неплохо?"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)

# Сообщение с местоположением (стандартный segment location → Matrix m.location; при совместном использовании с текстом разделяется на отдельные события)
ob12_msg = [
    {"type": "text", "data": {"text": "Я здесь"}},
    {"type": "location", "data": {"latitude": 39.9, "longitude": 116.4, "title": "Пекин"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно ожидать с помощью await. Возвращаемый результат соответствует стандартизированной схеме возврата адаптеров ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата
    "data": {...},            // Ответные данные
    "message_id": "$event_id", // ID события Matrix
    "message": "",            // Сообщение об ошибке
    "matrix_raw": {...}       // Исходные данные ответа
}
```

Схема кодов ошибок см. в разделе [Стандартизация](#стандартизация).

## Специфические типы событий

Необходимо использовать `platform=="matrix"` для проверки и использования специфических возможностей данной платформы

### Основные отличия

1. **Децентрализованная архитектура**: Matrix — это децентрализованный протокол связи, формат ID пользователя: `@user:server.domain`, формат ID комнаты: `!room_id:server.domain`
2. **Концепция комнат**: Matrix не различает личные и групповые чаты, все сессии — это "комнаты". Адаптер автоматически определяет личные комнаты по данным DM (Direct Message)
3. **Долгое опросное подключение**: Используется API `/sync` для получения новых событий, а не WebSocket
4. **MXC URI**: Ссылки на медиа-файлы в формате `mxc://server.domain/media_id`
5. **HTML-форматированный текст**: Поддержка отправки HTML-форматированных сообщений через `formatted_body`
6. **Эмоциональные реакции**: Поддержка реакций на сообщения (Reaction), отличается от традиционного ответа
7. **Редактирование сообщений**: Поддержка редактирования отправленных сообщений через `m.replace`
8. **Удаление сообщений**: Поддержка удаления/редактирования сообщений через `m.room.redaction`

### Дополнительные поля

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

# Эмоциональная реакция
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

### Типы сегментов сообщений

Matrix сообщения автоматически преобразуются в соответствующие сегменты в зависимости от `msgtype`:

| msgtype | Преобразованный тип | Описание |
|---|---|---|
| m.text | `text` | Текстовое сообщение |
| m.notice | `text` | Уведомление |
| m.emote | `text` | Сообщение действия |
| m.image | `image` | Изображение |
| m.audio | `audio` | Аудио (стандартный сегмент `audio`; `voice` — имя метода отправки, а не сегмент) |
| m.video | `video` | Видео |
| m.file | `file` | Файл |
| m.location | `location` | Местоположение (latitude/longitude извлекаются из geo URI) |

> Упоминания (mention): Содержание сообщения с `m.mentions` (стандарт Matrix v1.11+) преобразуется в стандартный сегмент `mention` — `m.mentions.user_ids` → `mention(user_id=...)`, `m.mentions.room` → `mention(user_id="all")`.

Пример структуры сегментов сообщений:

```json
// Текстовое сообщение (с HTML)
{
  "type": "text",
  "data": {
    "text": "Чистый текст",
    "html": "<b>HTML-содержимое</b>"
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

// Местоположение (latitude/longitude извлекаются из geo URI)
{
  "type": "location",
  "data": {
    "latitude": 39.9,
    "longitude": 116.4,
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

## Подключение через Sync API

### Процесс синхронизации

1. Аутентификация с помощью access_token или user_id + password
2. Вызов `/_matrix/client/v3/account/whoami` для получения bot_user_id
3. Выдача мета-события connect
4. Выполнение начальной синхронизации (`/_matrix/client/v3/sync?timeout=0`) для получения токена `next_batch`
5. Обнаружение DM-комнат (`/_matrix/client/v3/user/{user_id}/account_data/m.direct`)
6. Начало цикла синхронизации Long Polling (`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`)
7. Обработка новых событий и их преобразование

### Механизм heartbeat

- Адаптер каждые 30 секунд выдает мета-событие `heartbeat`
- При успешном подключении выдается событие `connect`
- При закрытии соединения выдается событие `disconnect`

### Приглашения в комнаты

- При получении приглашения в комнату (состояние `invite`) и если `auto_accept_invites` установлено в `true` (по умолчанию), адаптер автоматически присоединяется к комнате
- Присоединение к комнате вызывает интерфейс `/_matrix/client/v3/join/{room_id}`

## Конфиденциальное шифрование (E2EE)

Адаптер с версии 4.3.0 нативно поддерживает конфиденциальное шифрование комнат Matrix (на основе matrix-nio[e2e]/vodozemac), `encryption_enabled = true` включает его.

### Механизм работы

- **Синхронизация**: При включении используется сессия nio E2EE, ключи устройств загружаются, дополнительные ключи заполняются, to-device сообщения (Olm/Megolm сессионные ключи) обрабатываются автоматически; события `m.room.encrypted` в timeline автоматически расшифровываются в обычные события и проходят общее преобразование
- **Отправка**: При отправке в зашифрованную комнату автоматически обмениваются сессионные ключи Megolm и шифруются данные; события с ошибкой расшифровки пропускаются и записываются в журнал предупреждений
- **Медиа**: Медиа-файлы в зашифрованных комнатах загружаются как конфиденциальные (`m.file.encrypted`); на стороне получения медиа-сегменты содержат `matrix_encrypted_file` (JWK, с url/key/iv/hashes), после скачивания зашифрованного контента можно расшифровать с помощью `MatrixAdapter.decrypt_media()`
- **Устройства**: `device_id` автоматически анализируется (ответ входа → `/whoami` → локальное сохранение), при повторном входе с паролем используется то же устройство; `trust_all_devices = true` (по умолчанию) автоматически доверяет не проверенным устройствам (обычный сценарий для ботов), `false` — строгий режим
- **Снижение уровня**: При отключении E2EE или отсутствии matrix-nio автоматически возвращается к незашифрованному REST-пути, поведение полностью совпадает со старой версией

### Интерфейсы для модулей

- Event Mixin: `event.is_encrypted()` для проверки, является ли сообщение из зашифрованной комнаты
- Медиа-сегменты: `encrypted: true` и `matrix_encrypted_file` (JWK)
- Вспомогательный метод: `MatrixAdapter.decrypt_media(file_bytes, key, iv, hash_value) -> bytes`

### Известные ограничения

- Не поддерживается перекрестное подписание (cross-signing) и резервное копирование ключей на стороне сервера (room key backup)
- Локальное хранилище сессий (по умолчанию `data/matrix/<имя аккаунта>`) при удалении невозможно расшифровать историю сообщений
- Взаимодействие SAS (emoji) пока не поддерживается, планируется в последующих версиях

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
        # Обработка реакции...
```

### Отправка медиа-файлов

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

### Обработка редактирования сообщений

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # Обработка редактирования сообщения...
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