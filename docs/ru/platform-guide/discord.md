# Документация по функциям платформы Discord

DiscordAdapter — это адаптер, построенный на протоколах Discord Gateway (WebSocket) и REST API v10, объединяющий основные функции Discord Bot и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия соответствующего модуля: 4.2.0
- Ответственный: ErisPulse
- Версия Discord API: v10

## Основная информация

- Краткое описание платформы: Discord — это популярная платформа для коммуникации в сообществах, поддерживающая различные формы общения, такие как серверы, каналы, личные сообщения, а также предоставляет полный интерфейт разработки ботов
- Название адаптера: DiscordAdapter
- Поддержка нескольких аккаунтов: Поддерживает настройку нескольких Discord-ботов одновременно
- Способ подключения: Gateway WebSocket (для получения событий) + REST API (для отправки сообщений/вызова интерфейсов)
- Способ аутентификации: Bot Token (HTTP-заголовок `Authorization: Bot {token}`, в payload IDENTIFY для Gateway передается токен)
- Поддержка цепочечных модификаторов: Поддерживает цепочечные методы модификаторов, такие как `.Reply()`, `.At()`, `.AtAll()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Описание конфигурации

DiscordAdapter поддерживает конфигурацию нескольких аккаунтов, каждый аккаунт соответствует отдельному Discord-боту.

```toml
# config.toml

# Аккаунт 1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token (обязательно)
intents = 33281                 # Gateway Intents (необязательно, по умолчанию 33281)
enabled = true                  # Включить (необязательно, по умолчанию true)

# Аккаунт 2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**Описание параметров конфигурации (для каждого аккаунта):**

- `token`: Discord Bot Token (обязательно), получается в [Discord Developer Portal](https://discord.com/developers/applications)
- `intents`: Bitmask для Gateway Intents (необязательно, по умолчанию `33281`), определяет типы событий, на которые бот подписывается
- `bot_id`: ID пользователя бота (необязательно, ID бота автоматически получается во время выполнения из события READY, не нужно заполнять вручную)
- `enabled`: Включить этот аккаунт (необязательно, по умолчанию `true`)

### Gateway Intents

Intents используют bitmask, вычисляются путем побитового OR (`|`) значений каждого Intent:

| Intent | Bit | Значение | Описание | Привилегированный |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | Создание/удаление/обновление серверов, каналов, изменение ролей | Нет |
| GUILD_MEMBERS | `1 << 1` | 2 | Участие/выход/обновление участников | Да |
| GUILD_MESSAGES | `1 << 9` | 512 | Отправка/получение сообщений на сервере | Нет |
| MESSAGE_CONTENT | `1 << 15` | 32768 | Содержимое сообщений (без этого Intent значение content будет пустым) | Да |

Значение по умолчанию `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`.

> **Внимание:** Привилегированные Intents необходимо включить в Discord Developer Portal → Bot → Privileged Gateway Intents. Если бот находится на более чем 100 серверах, также требуется прохождение проверки Discord.

**API-среда:**
- Основной адрес REST API Discord: `https://discord.com/api/v10`
- Адрес WebSocket Gateway: получается динамически через `GET /gateway/bot`, обычно `wss://gateway.discord.gg/?v=10&encoding=json`

## Обновление до v5 (4.2.0)

Данный адаптер был обновлен до соответствия v5 (постепенное обновление, совместимость API сохранена):

- **BaseConverter наследование**: Общие поля конвертера строятся с помощью `build_base_event` из фреймворка
- **Api DSL**: Стандартное сопоставление API-действий (см. ниже)
- **Стандартный сегмент keyboard**: Преобразуется в Discord components (строка действий + кнопки); модификатор .Keyboard(rows) принимает общую структуру
- **Стандартные поля для взаимодействий**: Событие INTERACTION_CREATE содержит interaction_id / button_data
- **Задачи spawn_background**: Задачи подключения используют runtime.spawn_background
- **Мягкая зависимость от фреймворка**: Проверка на ErisPulse>=2.7.1 и вывод предупреждения при запуске; вывод версии в логах

### Стандартные API-действия

```python
from ErisPulse import sdk
discord = sdk.adapter.get("discord")

result = await discord.Api.get_self_info()                # GET /users/@me
result = await discord.Api.get_user_info(user_id)         # GET /users/{id}
result = await discord.Api.get_guild_info(guild_id)       # GET /guilds/{id}
result = await discord.Api.get_guild_list()               # GET /users/@me/guilds
result = await discord.Api.get_channel_list(guild_id)     # GET /guilds/{id}/channels
result = await discord.Api.get_guild_member_info(gid, uid)
await discord.Api.delete_message(message_id)              # Автоматически дополняется channel_id
await discord.Api.leave_guild(guild_id)
result = await discord.Api.Using("main").get_self_info()
```

### Кнопки (keyboard / components)

```python
rows = [[{"label": "Нажми", "type": "callback", "data": "btn:1"},
         {"label": "Сайт",  "type": "link",     "data": "https://example.com"}]]
await discord.Send.To("channel", channel_id).Keyboard(rows).Text("Выберите")
# Автоматически преобразуется в components: callback → custom_id / link → url
```

---
## Поддерживаемые типы отправки сообщений

Все методы отправки сообщений реализованы с использованием цепочечного синтаксиса, например:
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

Поддерживаемые типы отправки сообщений включают:
- `.Text(text: str)` — отправка текстового сообщения.
- `.Embed(embed: dict | list)` — отправка встроенных сообщений Embed, поддерживается как одно, так и несколько Embed.
- `.Image(file: bytes | str, filename: str = "image.png")` — отправка изображения, поддерживается бинарные данные или URL.
- `.File(file: bytes | str, filename: str = None)` — отправка файла, поддерживается бинарные данные или URL.
- `.Reply(content: str, message_id: str)` — ответ на указанное сообщение (удобный метод).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщений в формате OneBot12.
- `.Raw_json(json_str: str)` — отправка произвольных JSON-запросов Discord API.

### Цепочечные модификаторы (можно комбинировать)

Цепочечные модификаторы возвращают `self`, позволяя цепочечное использование, обязательно должны вызываться перед окончательным методом отправки:

- `.Reply(message_id: str)` — ответ (ссылка) на указанное сообщение, устанавливает `message_reference`.
- `.At(user_id: str)` — упоминание пользователя, преобразуется в `<@user_id>`, можно вызывать несколько раз.
- `.AtAll()` — упоминание всех, преобразуется в `@everyone`.

### Примеры цепочечного вызова

```python
# Базовая отправка
await discord.Send.To("group", channel_id).Text("Hello")

# Ответ на сообщение
await discord.Send.To("group", channel_id).Reply(msg_id).Text("Ответ на сообщение")

# Удобный ответ (одно действие)
await discord.Send.To("group", channel_id).Reply("Содержимое ответа", msg_id)

# Упоминание пользователя
await discord.Send.To("group", channel_id).At("user_id").Text("Привет")

# Упоминание нескольких пользователей
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("Упоминание нескольких пользователей")

# Упоминание всех
await discord.Send.To("group", channel_id).AtAll().Text("Анонс")

# Комбинированное использование
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Сложное сообщение")

# Встроенное сообщение
embed = {
    "title": "Уведомление",
    "description": "Это встроенное сообщение",
    "color": 5814783,
    "fields": [{"name": "Поле", "value": "Значение", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# Отправка изображения
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### Личные сообщения

При отправке личных сообщений адаптер автоматически создает DM-канал:

```python
# Отправка личного сообщения
await discord.Send.To("user", user_id).Text("Содержимое личного сообщения")
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

Все методы отправки возвращают объект Task, который можно await-ом получить результат отправки. Возвращаемый результат соответствует стандартизированному формату возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата (0 — успех)
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
| 34000 | Ошибка Discord API (недостаточно прав, неверные параметры и т.д.) |

## Уникальные типы событий

Необходимо использовать `platform == "discord"` для проверки и использования особенностей данной платформы.

### Основные различия

1. **Система серверов/каналов**: Discord использует двухуровневую структуру серверов (Guild) и каналов (Channel), канал является основной целью отправки сообщений
2. **События Gateway**: Все события получают через WebSocket Gateway, используя механизм Opcode + Dispatch
3. **Подписка на Intents**: Подписка на типы событий через bitmask, `MESSAGE_CONTENT` требует привилегированных прав
4. **Типы сообщений**: Поддерживаются текст, изображение, файл, видео, аудио, Embed, Sticker и другие типы сообщений
5. **Формат упоминания**: Discord использует формат `<@user_id>` для упоминания пользователей

### Расширенные поля

Все дополнительные поля имеют префикс `discord_`:
- `discord_raw`: Оригинальные данные события Discord
- `discord_raw_type`: Имя оригинального типа события (например, `MESSAGE_CREATE`)
- `discord_guild_id`: ID сервера
- `discord_channel_id`: ID канала

### Отображение detail_type

| Сцена Discord | detail_type | Описание |
|---|---|---|
| Сообщение в канале | `channel` | Расширенный тип ErisPulse |
| Личное сообщение (DM) | `private` | Стандартный тип OneBot12 |

### Отображение типов событий

| Событие Discord | OneBot12 type | detail_type | Описание |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | Создание сообщения |
| MESSAGE_UPDATE | message | channel/private | Редактирование сообщения |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | Удаление сообщения |
| GUILD_MEMBER_ADD | notice | group_member_increase | Участник присоединился |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | Участник покинул |
| GUILD_MEMBER_UPDATE | notice | group_member_update | Обновление информации о участнике |
| GUILD_ROLE_CREATE | notice | group_role_create | Создание роли |
| GUILD_ROLE_DELETE | notice | group_role_delete | Удаление роли |
| CHANNEL_CREATE | notice | channel_create | Создание канала |
| CHANNEL_DELETE | notice | channel_delete | Удаление канала |
| INTERACTION_CREATE | request | interaction | Взаимодействие (кнопки, команды и т.д.) |

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
  "discord_channel_id": "ID DM-канала",
  "message": [
    {"type": "text", "data": {"text": "Содержимое личного сообщения"}}
  ],
  "alt_message": "Содержимое личного сообщения"
}

# Сообщение с Embed
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "discord_embed", "data": {"embed": {...}}}
  ],
  "alt_message": "[Встроенное сообщение]"
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

Содержимое Discord-сообщений автоматически преобразуется в соответствующие типы сообщений на основе `content`, `attachments`, `embeds`:

| Источник | Тип преобразования | Описание |
|---|---|---|
| Текст content | `text` | Текстовое содержимое |
| Текст content `<@id>` | `mention` | Упоминание пользователя |
| Текст content `<@&id>` | `discord_role_mention` | Упоминание роли |
| Текст content `<#id>` | `discord_channel_mention` | Упоминание канала |
| attachments (image/*) | `image` | Вложение изображения |
| attachments (video/*) | `video` | Вложение видео |
| attachments (audio/*) | `audio` | Вложение аудио |
| attachments (другое) | `file` | Вложение файла |
| embeds | `discord_embed` | Встроенное сообщение |
| sticker_items | `discord_sticker` | Наклейка |

### Сообщение типа discord_embed

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
4. Отправка opcode 2 IDENTIFY: содержит token, intents, properties
5. Начало цикла心跳: отправка opcode 1 Heartbeat с интервалом `heartbeat_interval`
6. Получение opcode 0 Dispatch: событие распределения (`t`=имя события, `s`=номер, `d`=данные)
7. Получение opcode 11 Heartbeat ACK: подтверждение心跳

### Описание Opcode

| Opcode | Название | Направление | Описание |
|--------|------|------|------|
| 0 | Dispatch | Получение | Распределение событий (с полями `t`, `s`, `d`) |
| 1 | Heartbeat | Отправка/Получение |心跳 (содержит последний seq) |
| 2 | Identify | Отправка | Аутентификация |
| 6 | Resume | Отправка | Восстановление сессии |
| 7 | Reconnect | Получение | Сервер требует переподключения |
| 9 | Invalid Session | Получение | Недействительная сессия |
| 10 | Hello | Получение | Приветствие подключения (с heartbeat_interval) |
| 11 | Heartbeat ACK | Получение | Подтверждение心跳 |

### Переподключение и RESUME

- При разрыве соединения адаптер автоматически повторяет попытку подключения
- Если ранее был `session_id`, сначала попытка RESUME (opcode 6) для восстановления сессии
- RESUME содержит `token`, `session_id`, последний `seq`, после восстановления досылаются упущенные события
- При получении opcode 7 (Reconnect) сохраняется состояние сессии и переподключение
- При получении opcode 9 (Invalid Session) и `d=false` сессия удаляется и выполняется повторная идентификация

### Механизм心跳

- После получения HELLO, после `heartbeat_interval * random()` миллисекунд отправляется первый heartbeat
- Затем каждые `heartbeat_interval` миллисекунд отправляется heartbeat
- heartbeat содержит последний `seq` (opcode 1, `d: seq`)
- Если heartbeat отправлен, но в течение `heartbeat_interval` не получено ACK (opcode 11), считается, что соединение нестабильно, и выполняется переподключение

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

### Отправка встроенного сообщения

```python
embed = {
    "title": "Объявление сервера",
    "description": "Добро пожаловать в Discord-адаптер ErisPulse",
    "color": 3447003,
    "fields": [
        {"name": "Версия", "value": "4.0.0", "inline": True},
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
            f"Получено {len(embeds)} встроенных сообщений"
        )
```

### Обработка событий взаимодействия

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return

    interaction = event.get_interaction_data()
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("Кнопка была нажата!")
```