# Документация по функциональным возможностям платформы Discord

DiscordAdapter — это адаптер, построенный на протоколах Discord Gateway (WebSocket) и REST API v10, объединяющий основные функции Discord Bot и предоставляющий унифицированные интерфейсы для обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия соответствующего модуля: 4.4.3
- Ответственный: ErisPulse
- Версия Discord API: v10
- Последнее обновление: 2026-11-10

## Основная информация

- Краткое описание платформы: Discord — это популярная платформа для общения в сообществах, поддерживающая серверы, каналы, личные сообщения и другие формы общения, а также предоставляет полный интерфейт для разработки ботов.
- Название адаптера: DiscordAdapter
- Поддержка нескольких аккаунтов: Поддерживает одновременную настройку нескольких Discord-ботов
- Способ подключения: Gateway WebSocket (для получения событий) + REST API (для отправки сообщений/вызовов интерфейсов)
- Способ аутентификации: Bot Token (HTTP-заголовок `Authorization: Bot {token}`, в payload IDENTIFY для Gateway передается токен)
- Поддержка цепочки методов: Поддерживает цепочные методы, такие как `.Reply()`, `.At()`, `.AtAll()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Описание конфигурации

DiscordAdapter поддерживает конфигурацию нескольких аккаунтов, каждый аккаунт соответствует отдельному Discord Bot.

```toml
# config.toml

# Аккаунт 1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token (обязательно)
intents = 33281                 # Gateway Intents (необязательно, по умолчанию 33281)
enabled = true                  # Включить аккаунт (необязательно, по умолчанию true)

# Аккаунт 2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**Описание параметров конфигурации (для каждого аккаунта):**

- `token`: Discord Bot Token (обязательно), получается из [Discord Developer Portal](https://discord.com/developers/applications)
- `intents`: Bitmask для Gateway Intents (необязательно, по умолчанию `33281`), определяет типы событий, на которые подписан бот
- `bot_id`: ID пользователя бота (необязательно, ID автоматически получается из события READY во время выполнения, не нужно вручную указывать)
- `enabled`: Включить аккаунт (необязательно, по умолчанию `true`)

### Gateway Intents

Intents используют bitmask, вычисляются посредством побитового OR (`|`):

| Intent | Бит | Значение | Описание | Привилегированный |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | Создание/удаление/обновление серверов, каналов, ролей | Нет |
| GUILD_MEMBERS | `1 << 1` | 2 | Участие/выход/обновление участников | Да |
| GUILD_MESSAGES | `1 << 9` | 512 | Отправка/получение сообщений на сервере | Нет |
| MESSAGE_CONTENT | `1 << 15` | 32768 | Текст сообщения (без этого Intents поле content будет пустым) | Да |

Значение по умолчанию `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`.

> **Важно**: Привилегированные Intents должны быть включены в Discord Developer Portal → Bot → Privileged Gateway Intents. Если бот находится более чем в 100 серверах, необходимо пройти проверку Discord.

**API-окружение:**
- Базовый адрес Discord REST API: `https://discord.com/api/v10`
- Адрес WebSocket Gateway: получается динамически через `GET /gateway/bot`, обычно `wss://gateway.discord.gg/?v=10&encoding=json`

## Стандартизация (4.4.3)

### Изменения в событиях

1. **Уникальность идентификаторов событий**: `MESSAGE_UPDATE` / `MESSAGE_DELETE`, `REACTION_ADD` / `REMOVE` (включая `REMOVE_ALL` / `REMOVE_EMOJI`) и другие производные события имеют `id` в формате `"имя_события:оригинальный_id"` (например, `MESSAGE_UPDATE:123456`), чтобы избежать коллизий с идентификаторами событий `CREATE`, которые могут быть удалены фреймворком.
2. **Внедрение `self.account_id` в события**: Все события содержат имя аккаунта, который их породил, и в режиме нескольких аккаунтов `event.reply()` автоматически отправляется через соответствующий аккаунт.
3. **Исправление события INTERACTION_CREATE**: Изначально ошибочно помечалось как `type="request"` (подтип `interaction`), теперь изменено на `type="notice"` и `detail_type="discord_interaction"`; данные взаимодействия сохраняются в поле `discord_interaction`.

### Сопоставление сигнатур API

| Действие | Сигнатура | Описание |
|------|------|------|
| get_channel_info | `(guild_id, channel_id)` | Новая сигнатура с `guild_id` первым аргументом; при передаче одного аргумента используется старая сигнатура (считается `channel_id`) |
| get_channel_list | `(guild_id, joined_only=False)` | Добавлен необязательный аргумент `joined_only` |
| get_guild_info / get_guild_list | - | Используются поля `guild_id` / `guild_name` (старые поля `group_id` / `group_name` сохраняются, чтобы не нарушить существующие вызовы) |

### Стандартизация кодов ошибок

Коды ошибок стандартизированы по SDK (старый код `34000` больше не используется):

| retcode | Описание |
|---------|------|
| 0 | Успешно |
| 33001 | Ошибка сети (ошибка подключения, таймаут и т.д.) |
| 34100 | Платформа отклонила запрос (оригинальный ответ сохраняется в поле `discord_raw`) |
| 10002 | Не поддерживаемое действие (`get_guild_member_list` / `set_guild_name` / `get_channel_member_info` / `get_channel_member_list` / `leave_channel` явно возвращают ошибку, Discord REST не имеет соответствующей семантики) |
| 10003 | Ошибка параметров (например, отсутствие соответствующего контекста в таблице сообщений, что приводит к невозможности отмены) |

## Обновление до v5 (4.2.0)

Адаптер был обновлен до стандарта v5 (обновление постепенное, API совместим):

- **Наследование BaseConverter**: Общие поля конвертеров создаются фреймворком `build_base_event`
- **API DSL**: Стандартные действия API (см. ниже)
- **Стандартный сегмент keyboard**: Преобразуется в компоненты Discord (строка действий + кнопки); модификатор `.Keyboard(rows)` принимает общую структуру
- **Стандартные поля обратного вызова**: Событие INTERACTION_CREATE содержит `interaction_id` / `button_data`
- **Принадлежность задач spawn_background**: Задачи подключения используют `runtime.spawn_background`
- **Мягкая зависимость от фреймворка**: Время выполнения проверяет наличие ErisPulse>=2.7.1 и выводит предупреждение; при запуске выводится лог версии

### Стандартные действия API

```python
from ErisPulse import sdk
discord = sdk.adapter.get("discord")

result = await discord.Api.get_self_info()                # GET /users/@me
result = await discord.Api.get_user_info(user_id)         # GET /users/{id}
result = await discord.Api.get_guild_info(guild_id)       # GET /guilds/{id} (используется data с guild_id / guild_name)
result = await discord.Api.get_guild_list()               # GET /users/@me/guilds
result = await discord.Api.get_channel_info(guild_id, channel_id)  # GET /channels/{id} (новая сигнатура с guild_id первым аргументом)
result = await discord.Api.get_channel_list(guild_id)     # GET /guilds/{id}/channels
result = await discord.Api.get_guild_member_info(gid, uid)
await discord.Api.delete_message(message_id)              # Таблица регистрации автоматически дополняет channel_id
await discord.Api.leave_guild(guild_id)
result = await discord.Api.Using("main").get_self_info()
```

### Кнопки (keyboard / components)

```python
rows = [[{"label": "Нажать", "type": "callback", "data": "btn:1"},
         {"label": "Сайт",  "type": "link",     "data": "https://example.com"}]]
await discord.Send.To("channel", channel_id).Keyboard(rows).Text("Выберите")
# Автоматически преобразуется в components: callback → custom_id / link → url
```

---

## Поддерживаемые типы отправки сообщений

Все методы отправки сообщений реализованы через цепочку вызовов, например:
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка текстового сообщения.
- `.Embed(embed: dict | list)` — отправка встраиваемого сообщения Embed, поддерживает одно или несколько Embed.
- `.MergeForward(nodes, title="Сообщения вложений")` — отправка сообщения с объединёнными вложениями (Embed: заголовок + каждое сообщение в поле, ≤25 полей, значение ≤1024).
- `.Image(file: bytes | str, filename: str = "image.png")` — отправка изображения, поддерживает бинарные данные или URL.
- `.File(file: bytes | str, filename: str = None)` — отправка файла, поддерживает бинарные данные или URL.
- `.Reply(content: str, message_id: str)` — ответ на указанное сообщение (удобный метод).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.
- `.Raw_json(json_str: str)` — отправка произвольного JSON-запроса Discord API.

### Цепочные методы (можно комбинировать)

Цепочные методы возвращают `self`, поддерживают цепочку вызовов, должны быть вызваны перед окончательным методом отправки:

- `.Reply(message_id: str)` — ответ (ссылка) на указанное сообщение, устанавливает `message_reference`.
- `.At(user_id: str)` — упоминание пользователя, преобразуется в `<@user_id>`, можно вызывать несколько раз.
- `.AtAll()` — упоминание всех пользователей, преобразуется в `@everyone`.

### Примеры цепочечных вызовов

```python
# Базовая отправка
await discord.Send.To("group", channel_id).Text("Hello")

# Ответ на сообщение
await discord.Send.To("group", channel_id).Reply(msg_id).Text("Ответ на сообщение")

# Удобный ответ (в один шаг)
await discord.Send.To("group", channel_id).Reply("Содержание ответа", msg_id)

# Упоминание пользователя
await discord.Send.To("group", channel_id).At("user_id").Text("Привет")

# Упоминание нескольких пользователей
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("Упоминание нескольких пользователей")

# Упоминание всех
await discord.Send.To("group", channel_id).AtAll().Text("Объявление")

# Комбинированный вызов
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Сложное сообщение")

# Встраиваемое сообщение
embed = {
    "title": "Уведомление",
    "description": "Это встраиваемое сообщение",
    "color": 5814783,
    "fields": [{"name": "Поле", "value": "Значение", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# Отправка изображения
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### Отправка личных сообщений

При отправке личных сообщений адаптер автоматически создает канал DM:

```python
# Отправка личного сообщения
await discord.Send.To("user", user_id).Text("Содержание личного сообщения")
await discord.Send.To("user", user_id).Embed(embed)
```

### Операции с сообщениями

```python
# Отмена отправки сообщения
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12 формат
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно ожидать для получения результата отправки. Возвращаемые результаты соответствуют стандартизированному формату возвратов адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата (0 — успешный)
    "data": {...},            // Оригинальный ответ Discord API
    "message_id": "xxx",      // ID сообщения (при отправке сообщения)
    "message": "",            // Сообщение об ошибке
    "discord_raw": {...}      // Оригинальные данные ответа
}
```

### Описание кодов ошибок

| retcode | Описание |
|---------|------|
| 0 | Успешно |
| 33001 | Ошибка сети (ошибка подключения, таймаут и т.д.) |
| 34100 | Платформа отклонила запрос (недостаточно прав, ошибка параметров и т.д., оригинальный ответ сохраняется в поле `discord_raw`) |
| 10002 | Не поддерживаемое действие (см. раздел "Стандартизация (4.4.3)" в описании кодов ошибок) |
| 10003 | Ошибка параметров (например, при отмене отсутствует соответствующий контекст сообщения) |

## Специфические типы событий

Необходимо использовать `platform == "discord"` для проверки и использования специфических функций данной платформы.

### Основные отличия

1. **Система серверов/каналов**: Discord использует двухуровневую структуру серверов (Guild) и каналов (Channel), канал является основным целевым объектом для отправки сообщений
2. **События Gateway**: Все события получаются через WebSocket Gateway, механизм Opcode + Dispatch
3. **Подписка на события**: Используется bitmask для подписки на типы событий, `MESSAGE_CONTENT` требует привилегированных прав
4. **Типы сообщений**: Поддерживает текст, изображения, файлы, видео, аудио, Embed, Sticker и другие типы сообщений
5. **Формат упоминания**: Discord использует формат `<@user_id>` для упоминания пользователей

### Расширенные поля

Все специфические поля обозначаются префиксом `discord_`:
- `discord_raw`: Оригинальные данные события Discord
- `discord_raw_type`: Оригинальное имя типа события (например, `MESSAGE_CREATE`)
- `discord_guild_id`: ID сервера
- `discord_channel_id`: ID канала
- `discord_interaction`: Данные события взаимодействия (INTERACTION_CREATE)

### Сопоставление detail_type

| Сценарий Discord | detail_type | Описание |
|---|---|---|
| Канал сообщения | `channel` | Расширение ErisPulse |
| Личное сообщение (DM) | `private` | Стандартный тип OneBot12 |

### Сопоставление типов событий

| Событие Discord | OneBot12 type | detail_type | Описание |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | Создание сообщения |
| MESSAGE_UPDATE | message | channel/private | Редактирование сообщения (id имеет вид `MESSAGE_UPDATE:оригинальный_id`) |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | Удаление сообщения (id имеет вид `MESSAGE_DELETE:оригинальный_id`) |
| MESSAGE_REACTION_ADD | notice | group_message_reaction_add | Добавление реакции (id имеет вид `MESSAGE_REACTION_ADD:оригинальный_id`) |
| MESSAGE_REACTION_REMOVE | notice | group_message_reaction_remove | Удаление реакции (id имеет вид `MESSAGE_REACTION_REMOVE:оригинальный_id`) |
| GUILD_MEMBER_ADD | notice | group_member_increase | Участник присоединился |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | Участник покинул |
| GUILD_MEMBER_UPDATE | notice | group_member_update | Обновление информации о участнике |
| GUILD_ROLE_CREATE | notice | group_role_create | Создание роли |
| GUILD_ROLE_DELETE | notice | group_role_delete | Удаление роли |
| CHANNEL_CREATE | notice | channel_create | Создание канала |
| CHANNEL_DELETE | notice | channel_delete | Удаление канала |
| INTERACTION_CREATE | notice | discord_interaction | Взаимодействие (кнопки, команды и т.д.) |

> Начиная с версии 4.4.3, идентификаторы несоздающих событий, таких как MESSAGE_UPDATE / MESSAGE_DELETE, REACTION_ADD / REMOVE и т.д., были изменены на формат `"имя_события:оригинальный_id"`, чтобы избежать конфликтов с идентификаторами событий MESSAGE_CREATE, которые могут быть удалены фреймворком.

### Примеры специальных полей

```python
# Текстовое сообщение в канале
{
  "type": "message",
  "detail_type": "channel",
  "user_id": "ID отправителя",
  "user_nickname": "Имя пользователя",
  "group_id": "ID канала",
  "message_id": "ID сообщения",
  "self": {
    "platform": "discord",
    "user_id": "ID бота",
    "account_id": "default"
  },
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_guild_id": "ID сервера",
  "discord_channel_id": "ID канала",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# Личное сообщение
{
  "type": "message",
  "detail_type": "private",
  "user_id": "ID отправителя",
  "user_nickname": "Имя пользователя",
  "message_id": "ID сообщения",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_channel_id": "ID канала DM",
  "message": [
    {"type": "text", "data": {"text": "Содержание личного сообщения"}}
  ],
  "alt_message": "Содержание личного сообщения"
}

# Сообщение с Embed
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "discord_embed", "data": {"embed": {...}}}
  ],
  "alt_message": "[Встраиваемое сообщение]"
}

# Сообщение с вложениями
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "Посмотри на это изображение"}},
    {"type": "image", "data": {"file": "URL изображения", "url": "URL изображения", "file_name": "image.png"}}
  ],
  "alt_message": "Посмотри на это изображение[изображение]"
}
```

### Типы сообщений

Содержимое Discord-сообщений автоматически преобразуется в соответствующие типы сообщений на основе полей `content`, `attachments`, `embeds`:

| Источник | Тип преобразования | Описание |
|---|---|---|
| Текст в content | `text` | Чистый текст |
| Упоминания `<@id>` в content | `mention` | Упоминание пользователя |
| Упоминания `<@&id>` в content | `discord_role_mention` | Упоминание роли |
| Упоминания `<#id>` в content | `discord_channel_mention` | Упоминание канала |
| Вложения (image/*) | `image` | Изображение |
| Вложения (video/*) | `video` | Видео |
| Вложения (audio/*) | `audio` | Аудио |
| Вложения (другое) | `file` | Файл |
| Вложения (embeds) | `discord_embed` | Встраиваемое сообщение |
| Вложения (sticker_items) | `discord_sticker` | Стикер |

### Сообщения с типом discord_embed

```json
{
  "type": "discord_embed",
  "data": {
    "embed": {
      "title": "Заголовок",
      "description": "Описание",
      "color": 12345,
      "fields": [...],
      "image": {"url": "..."},
      "thumbnail": {"url": "..."},
      "footer": {"text": "..."}
    }
  }
}
```

## Подключение к Gateway

### Процесс подключения

1. Вызов `GET /gateway/bot` для получения URL WebSocket Gateway
2. Подключение к `wss://gateway.discord.gg/?v=10&encoding=json`
3. Получение opcode 10 HELLO: содержит `heartbeat_interval`
4. Отправка opcode 2 IDENTIFY: содержит token, intents и properties
5. Начало цикла отправки heartbeat: отправлять opcode 1 Heartbeat с интервалом `heartbeat_interval`
6. Получение opcode 0 Dispatch: событие dispatch (с полями `t`=имя события, `s`=номер, `d`=данные)
7. Получение opcode 11 Heartbeat ACK: подтверждение heartbeat

### Описание Opcode

| Opcode | Название | Направление | Описание |
|--------|------|------|------|
| 0 | Dispatch | Прием | Распределение событий (с полями `t`, `s`, `d`) |
| 1 | Heartbeat | Отправка/Прием | Heartbeat (содержит последний seq) |
| 2 | Identify | Отправка | Аутентификация |
| 6 | Resume | Отправка | Восстановление сессии |
| 7 | Reconnect | Прием | Сервер требует переподключения |
| 9 | Invalid Session | Прием | Невалидная сессия |
| 10 | Hello | Прием | Приветствие подключения (содержит heartbeat_interval) |
| 11 | Heartbeat ACK | Прием | Подтверждение heartbeat |

### Переподключение и RESUME

- При разрыве соединения адаптер автоматически пытается переподключиться
- Если ранее был `session_id`, сначала пытается восстановить сессию с помощью RESUME (opcode 6)
- RESUME содержит `token`, `session_id`, последний `seq`, после восстановления дополняет пропущенные события
- При получении opcode 7 (Reconnect) сохраняет состояние сессии и переподключается
- При получении opcode 9 (Invalid Session) и `d=false`, сбрасывает сессию и выполняет новый IDENTIFY

### Механизм heartbeat

- После получения HELLO, ждёт `heartbeat_interval * random()` миллисекунд и отправляет первый heartbeat
- Затем отправляет heartbeat каждые `heartbeat_interval` миллисекунд
- Heartbeat содержит последний `seq` (opcode 1, `d: seq`)
- Если после отправки heartbeat в течение `heartbeat_interval` не получено подтверждение ACK (opcode 11), считается, что соединение нестабильно, и происходит переподключение

## Примеры использования

### Обработка сообщений в канале

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

discord = sdk.adapter.get("discord")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "discord":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await discord.Send.To("group", channel_id).Text("Hello!")
```

### Обработка личных сообщений

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "discord":
        return
    if not event.is_dm():
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await discord.Send.To("user", user_id).Text(f"Вы сказали: {text}")
```

### Отправка встраиваемого сообщения

```python
embed = {
    "title": "Объявление сервера",
    "description": "Добро пожаловать в ErisPulse Discord адаптер",
    "color": 3447003,
    "fields": [
        {"name": "Версия", "value": "4.4.3", "inline": True},
        {"name": "Фреймворк", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Powered by ErisPulse"},
    "timestamp": "2025-01-01T00:00:00.000Z",
}
await discord.Send.To("group", channel_id).Embed(embed)
```

### Использование специфических методов Discord

```python
@message.on_message()
async def handle(event):
    if event.get("platform") != "discord":
        return

    channel_id = event.get_channel_id()
    guild_id = event.get_guild_id()
    is_dm = event.is_dm()
    embeds = event.get_embeds()
    attachments = event.get_attachments()

    if embeds:
        await discord.Send.To("group", channel_id).Text(
            f"Получено {len(embeds)} встраиваемых сообщений"
        )
```

### Обработка событий взаимодействия

Начиная с 4.4.3, событие INTERACTION_CREATE распределяется как `notice` / `discord_interaction`:

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return
    if event.get("detail_type") != "discord_interaction":
        return

    interaction = event.get_interaction_data()  # Эквивалентно event["discord_interaction"]
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("Кнопка нажата!")
```