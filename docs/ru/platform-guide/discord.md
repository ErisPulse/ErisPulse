# Документация по функциям платформы Discord

DiscordAdapter — это адаптер, построенный на протоколах Discord Gateway (WebSocket) и REST API v10, который интегрирует основные функции бота Discord, предоставляя унифицированные интерфейсы обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия соответствующего модуля: 4.0.0
- Ответственный за поддержку: ErisPulse
- Версия Discord API: v10

## Основная информация

- Описание платформы: Discord — популярная платформа общения для сообщества, поддерживающая серверы, каналы, личные сообщения и другие формы диалога, предоставляющая полные интерфейсы для разработки ботов.
- Название адаптера: DiscordAdapter
- Поддержка нескольких аккаунтов: поддержка настройки нескольких ботов Discord одновременно.
- Способ подключения: Gateway WebSocket (для получения событий) + REST API (для отправки сообщений / вызова интерфейсов).
- Способ авторизации: Bot Token (HTTP заголовок `Authorization: Bot {token}`, payload IDENTIFY в Gateway содержит token).
- Поддержка цепочки методов: поддержка цепных методов-модификаторов, таких как `.Reply()`, `.At()`, `.AtAll()`.
- Совместимость с OneBot12: поддержка отправки сообщений в формате OneBot12.

## Описание конфигурации

DiscordAdapter поддерживает конфигурацию нескольких аккаунтов, каждый из которых соответствует отдельному боту Discord.

```toml
# config.toml

# Аккаунт 1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token (обязательно)
intents = 33281                 # Gateway Intents (необязательно, по умолчанию 33281)
enabled = true                  # Включен (необязательно, по умолчанию true)

# Аккаунт 2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**Описание параметров конфигурации (для каждого аккаунта):**

- `token`: Discord Bot Token (обязательно), получен на [Discord Developer Portal](https://discord.com/developers/applications).
- `intents`: битовая маска Gateway Intents (необязательно, по умолчанию `33281`), определяет типы событий, на которые подписывается бот.
- `bot_id`: ID пользователя бота (необязательно, автоматически получается во время выполнения из события READY, заполнять вручную не нужно).
- `enabled`: включен ли этот аккаунт (необязательно, по умолчанию `true`).

### Gateway Intents

Intents используют битовые маски, расчет которых производится путем побитового ИЛИ (`|`) значений Intent:

| Intent | Бит | Значение | Описание | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | Создание/удаление/обновление серверов, каналов, ролей | Нет |
| GUILD_MEMBERS | `1 << 1` | 2 | Присоединение/покидание/обновление участников | Да |
| GUILD_MESSAGES | `1 << 9` | 512 | Прием/отправка сообщений на серверах | Нет |
| MESSAGE_CONTENT | `1 << 15` | 32768 | Содержимое сообщений (без этого Intent поле content пустое) | Да |

Значение по умолчанию `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`.

> **Примечание**: Privileged Intents необходимо включить на Discord Developer Portal → Bot → Privileged Gateway Intents. Если бот работает на более чем 100 серверах, требуется прохождение проверки Discord.

**Окружение API:**
- Базовый адрес Discord REST API: `https://discord.com/api/v10`
- Адрес Gateway WebSocket: динамически получается через `GET /gateway/bot`, обычно `wss://gateway.discord.gg/?v=10&encoding=json`

## Типы поддерживаемых сообщений для отправки

Все методы отправки реализованы с использованием цепочного синтаксиса, например:
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`: отправка текстового сообщения.
- `.Embed(embed: dict | list)`: отправка сообщения с встраиваемым Embed, поддерживает один или несколько Embed.
- `.Image(file: bytes | str, filename: str = "image.png")`: отправка изображения, поддерживает двоичные данные или URL.
- `.File(file: bytes | str, filename: str = None)`: отправка файла, поддерживает двоичные данные или URL.
- `.Reply(content: str, message_id: str)`: ответ на указанное сообщение (удобный терминальный метод).
- `.Raw_ob12(message: List[Dict], **kwargs)`: отправка сообщения в формате OneBot12.
- `.Raw_json(json_str: str)`: отправка произвольного JSON-запроса Discord API.

### Цепные методы-модификаторы (можно комбинировать)

Методы-модификаторы возвращают `self`, поддерживают цепной вызов, должны вызываться перед конечным методом отправки:

- `.Reply(message_id: str)`: ответ (цитирование) на указанное сообщение, устанавливает `message_reference`.
- `.At(user_id: str)`: упоминание указанного пользователя, преобразуется в `<@user_id>`, можно вызывать несколько раз.
- `.AtAll()`: упоминание всех, преобразуется в `@everyone`.

### Примеры цепных вызовов

```python
# Базовая отправка
await discord.Send.To("group", channel_id).Text("Hello")

# Ответ на сообщение
await discord.Send.To("group", channel_id).Reply(msg_id).Text("Ответ на сообщение")

# Удобный ответ (за один шаг)
await discord.Send.To("group", channel_id).Reply("Содержимое ответа", msg_id)

# Упоминание пользователя
await discord.Send.To("group", channel_id).At("user_id").Text("Привет")

# Упоминание нескольких пользователей
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("Мультиупоминание")

# Упоминание всех
await discord.Send.To("group", channel_id).AtAll().Text("Объявление")

# Комбинированное использование
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Сложное сообщение")

# Сообщение с Embed
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
await discord.Send.To("user", user_id).Text("Содержимое личного сообщения")
await discord.Send.To("user", user_id).Embed(embed)
```

### Операции с сообщениями

```python
# Отзыв сообщения
await discord.Send.To("group", channel_id).Recall(msg_id)

# В формате OneBot12
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно напрямую await для получения результата. Результат возвращаемого значения следует стандартной спецификации возвращаемых значений адаптеров ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата (0 — успех)
    "data": {...},            // Исходный ответ Discord API
    "message_id": "xxx",      // ID сообщения (при отправке сообщения)
    "message": "",            // Информация об ошибке
    "discord_raw": {...}      // Исходные данные ответа
}
```

### Описание кодов ошибок

| retcode | Описание |
|---------|------|
| 0 | Успех |
| 33001 | Ошибка сети (сбой соединения, тайм-аут и т.д.) |
| 34000 | Ошибка Discord API (нет прав, неверные параметры и т.д.) |

## Специфические типы событий

Для использования функций этой платформы требуется проверка `platform == "discord"`.

### Ключевые различия

1. **Система серверов/каналов**: Discord использует двухуровневую структуру серверов (Guild) и каналов (Channel), канал является основной целью отправки сообщений.
2. **События Gateway**: все события принимаются через WebSocket Gateway с использованием механизма Opcode + Dispatch.
3. **Подписка на Intents**: подписка на типы событий через битовые маски, для `MESSAGE_CONTENT` требуется привилегированный доступ.
4. **Типы сегментов сообщений**: поддерживаются текст, изображения, файлы, видео, аудио, Embed, Sticker и другие сегменты сообщений.
5. **Формат упоминаний**: Discord использует формат `<@user_id>` для обозначения упоминаний пользователей.

### Расширенные поля

Все специфические поля помечены префиксом `discord_`:
- `discord_raw`: исходные данные события Discord.
- `discord_raw_type`: имя исходного типа события (например, `MESSAGE_CREATE`).
- `discord_guild_id`: ID сервера.
- `discord_channel_id`: ID канала.

### Отображение detail_type

| Discord сценарий | detail_type | Описание |
|---|---|---|
| Сообщение в канале | `channel` | Расширенный тип ErisPulse |
| Личное сообщение (DM) | `private` | Стандартный тип OneBot12 |

### Отображение типов событий

| Discord событие | OneBot12 type | detail_type | Описание |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | Создание сообщения |
| MESSAGE_UPDATE | message | channel/private | Редактирование сообщения |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | Удаление сообщения |
| GUILD_MEMBER_ADD | notice | group_member_increase | Участник присоединился |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | Участник вышел |
| GUILD_MEMBER_UPDATE | notice | group_member_update | Обновление информации об участнике |
| GUILD_ROLE_CREATE | notice | group_role_create | Создание роли |
| GUILD_ROLE_DELETE | notice | group_role_delete | Удаление роли |
| CHANNEL_CREATE | notice | channel_create | Создание канала |
| CHANNEL_DELETE | notice | channel_delete | Удаление канала |
| INTERACTION_CREATE | request | interaction | Взаимодействие (кнопки, команды и т.д.) |

### Примеры специфических полей

```python
# Текстовое сообщение в канале
{
  "type": "message",
  "detail_type": "channel",
  "user_id": "ID_отправителя",
  "user_nickname": "Никнейм",
  "group_id": "ID_канала",
  "message_id": "ID_сообщения",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_guild_id": "ID_сервера",
  "discord_channel_id": "ID_канала",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# Личное сообщение
{
  "type": "message",
  "detail_type": "private",
  "user_id": "ID_отправителя",
  "user_nickname": "Никнейм",
  "message_id": "ID_сообщения",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_channel_id": "ID_DM_канала",
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
  "alt_message": "[Встраиваемое сообщение]"
}

# Сообщение с вложениями
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "Посмотрите на эту картину"}},
    {"type": "image", "data": {"file": "URL_изображения", "url": "URL_изображения", "file_name": "image.png"}}
  ],
  "alt_message": "Посмотрите на эту картину[Изображение]"
}
```

### Типы сегментов сообщений

Содержимое сообщения Discord автоматически преобразуется в соответствующие сегменты сообщений на основе полей `content`, `attachments`, `embeds`:

| Источник | Тип конверсии | Описание |
|---|---|---|
| Текст content | `text` | Простой текст |
| Content `<@id>` | `mention` | Упоминание пользователя |
| Content `<@&id>` | `discord_role_mention` | Упоминание роли |
| Content `<#id>` | `discord_channel_mention` | Упоминание канала |
| attachments (image/*) | `image` | Вложение-изображение |
| attachments (video/*) | `video` | Вложение-видео |
| attachments (audio/*) | `audio` | Вложение-аудио |
| attachments (другое) | `file` | Вложение-файл |
| embeds | `discord_embed` | Встраиваемое сообщение |
| sticker_items | `discord_sticker` | Стикер |

### Сегмент сообщения discord_embed

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

## Подключение Gateway

### Процесс подключения

1. Вызвать `GET /gateway/bot` для получения URL WebSocket Gateway.
2. Подключиться к `wss://gateway.discord.gg/?v=10&encoding=json`.
3. Получить opcode 10 HELLO: содержит `heartbeat_interval`.
4. Отправить opcode 2 IDENTIFY: содержит token, intents, properties.
5. Начать цикл heartbeat: отправлять opcode 1 Heartbeat с интервалом `heartbeat_interval`.
6. Получить opcode 0 Dispatch: распределение событий (`t` = имя события, `s` = порядковый номер, `d` = данные).
7. Получить opcode 11 Heartbeat ACK: подтверждение heartbeat.

### Описание opcode

| Opcode | Название | Направление | Описание |
|--------|------|------|
| 0 | Dispatch | Получение | Распределение событий (содержит поля `t`, `s`, `d`) |
| 1 | Heartbeat | Отправка/Получение | Heartbeat (содержит последний `seq`) |
| 2 | Identify | Отправка | Аутентификация идентификации |
| 6 | Resume | Отправка | Возобновление сессии |
| 7 | Reconnect | Получение | Сервер требует переподключения |
| 9 | Invalid Session | Получение | Недействительная сессия |
| 10 | Hello | Получение | Приветствие (рукопожатие, содержит `heartbeat_interval`) |
| 11 | Heartbeat ACK | Получение | Подтверждение heartbeat |

### Переподключение и RESUME

- После разрыва соединения адаптер автоматически пытается переподключиться.
- Если ранее был получен `session_id`, приоритетом является попытка возобновить сессию через RESUME (opcode 6).
- RESUME содержит `token`, `session_id`, последний `seq`, после восстановления отправляет пропущенные события.
- При получении opcode 7 (Reconnect) сохраняется состояние сессии и выполняется переподключение.
- При получении opcode 9 (Invalid Session) и `d=false` сессия очищается и выполняется повторная идентификация.

### Механизм heartbeat

- После получения HELLO задержка отправки первого heartbeat составляет `heartbeat_interval * random()` миллисекунд.
- Затем каждый `heartbeat_interval` миллисекунд отправляется один heartbeat.
- Heartbeat содержит последний `seq` (opcode 1, `d: seq`).
- Если после отправки heartbeat в течение `heartbeat_interval` не получен ACK (opcode 11), соединение считается поврежденным и выполняется переподключение.

## Примеры использования

### Обработка сообщений в каналах

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

    await discord.Send.To("user", user_id).Text(f"Ты сказал: {text}")
```

### Отправка Embed-сообщений

```python
embed = {
    "title": "Объявление сервера",
    "description": "Добро пожаловать в адаптер Discord ErisPulse",
    "color": 3447003,
    "fields": [
        {"name": "Версия", "value": "4.0.0", "inline": True},
        {"name": "Фреймворк", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Работает на ErisPulse"},
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
            f"Получено {len(embeds)} Embed"
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