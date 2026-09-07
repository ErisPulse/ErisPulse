# Документация по функциям платформы Discord

DiscordAdapter — это адаптер, построенный на основе протокола Discord Gateway (WebSocket) и REST API v10, объединяющий основные функции Discord Bot и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия модуля: 4.1.0
- Разработчик: ErisPulse
- Версия Discord API: v10

## Основная информация

- Краткое описание: Discord — популярная платформа для коммуникации в сообществах, поддерживающая серверы, каналы, личные сообщения и другие формы общения, а также предоставляет полный интерфейт для разработки ботов.
- Название адаптера: DiscordAdapter
- Поддержка нескольких аккаунтов: Поддерживает настройку нескольких Discord-ботов.
- Способ подключения: WebSocket Gateway (для получения событий) + REST API (для отправки сообщений/вызовов интерфейсов)
- Метод аутентификации: Bot Token (в HTTP-заголовке `Authorization: Bot {token}`, в payload IDENTIFY для Gateway)
- Поддержка цепочки модификаторов: Поддерживает цепочечные методы модификации, такие как `.Reply()`, `.At()`, `.AtAll()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Описание конфигурации

DiscordAdapter поддерживает настройку нескольких аккаунтов, каждый из которых соответствует отдельному Discord Bot.

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

**Описание параметров (для каждого аккаунта):**

- `token`: Discord Bot Token (обязательно), получается в [Discord Developer Portal](https://discord.com/developers/applications)
- `intents`: Bitmask Gateway Intents (необязательно, по умолчанию `33281`), определяет типы событий, которые бот подписывается
- `bot_id`: ID пользователя бота (необязательно, автоматически получается из события READY, не нужно вручную заполнять)
- `enabled`: Включить аккаунт (необязательно, по умолчанию `true`)

### Gateway Intents

Intents используются как bitmask, вычисляются путем побитового сложения (OR) значений Intent:

| Intent | Bit | Value | Description | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | Создание/удаление/обновление серверов, каналов, ролей | No |
| GUILD_MEMBERS | `1 << 1` | 2 | Участие/выход/обновление участников | Yes |
| GUILD_MESSAGES | `1 << 9` | 512 | Отправка/получение сообщений на серверах | No |
| MESSAGE_CONTENT | `1 << 15` | 32768 | Текст сообщений (если отсутствует этот Intent, content будет пустым) | Yes |

Значение по умолчанию `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`.

> **Внимание**: Privileged Intents должны быть включены в Discord Developer Portal → Bot → Privileged Gateway Intents. Если бот находится более чем на 100 серверах, также требуется прохождение проверки Discord.

**API-среда:**
- Основной адрес REST API Discord: `https://discord.com/api/v10`
- Адрес WebSocket Gateway: получается динамически через `GET /gateway/bot`, обычно `wss://gateway.discord.gg/?v=10&encoding=json`

## Поддерживаемые типы отправки сообщений

Все методы отправки сообщений реализованы с использованием цепочки вызовов, например:
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`: Отправка обычного текстового сообщения.
- `.Embed(embed: dict | list)`: Отправка встраиваемого сообщения Embed, поддерживает одно или несколько Embed.
- `.Image(file: bytes | str, filename: str = "image.png")`: Отправка изображения, поддерживает бинарные данные или URL.
- `.File(file: bytes | str, filename: str = None)`: Отправка файла, поддерживает бинарные данные или URL.
- `.Reply(content: str, message_id: str)` (удобный метод): Ответ на указанное сообщение.
- `.Raw_ob12(message: List[Dict], **kwargs)`: Отправка сообщения в формате OneBot12.
- `.Raw_json(json_str: str)`: Отправка произвольного JSON-запроса к Discord API.

### Цепочные модификаторы (можно комбинировать)

Методы модификации возвращают `self`, поддерживают цепочечные вызовы и должны вызываться перед окончательным методом отправки:

- `.Reply(message_id: str)`: Ответить (ссылка) на указанное сообщение, устанавливает `message_reference`.
- `.At(user_id: str)`: Упомянуть пользователя, преобразуется в `<@user_id>`, может вызываться несколько раз.
- `.AtAll()`: Упомянуть всех, преобразуется в `@everyone`.

### Примеры цепочечных вызовов

```python
# Базовая отправка
await discord.Send.To("group", channel_id).Text("Hello")

# Ответ на сообщение
await discord.Send.To("group", channel_id).Reply(msg_id).Text("Ответ на сообщение")

# Удобный ответ (одним вызовом)
await discord.Send.To("group", channel_id).Reply("Содержание ответа", msg_id)

# Упоминание пользователя
await discord.Send.To("group", channel_id).At("user_id").Text("Привет")

# Упоминание нескольких пользователей
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("Упоминание нескольких пользователей")

# Упоминание всех
await discord.Send.To("group", channel_id).AtAll().Text("Анонс")

# Комбинированный вызов
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Составное сообщение")

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

При отправке личных сообщений адаптер автоматически создает DM-канал:

```python
# Отправка личного сообщения
await discord.Send.To("user", user_id).Text("Содержание личного сообщения")
await discord.Send.To("user", user_id).Embed(embed)
```

### Операции с сообщениями

```python
# Отмена отправки сообщения
await discord.Send.To("group", channel_id).Recall(msg_id)

# Отправка в формате OneBot12
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## Возвращаемые значения методов отправки

Все методы отправки сообщений возвращают объект Task, который можно ожидать с помощью await. Результат соответствует стандартизированному формату возврата ErisPulse:

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
| 0 | Успех |
| 33001 | Ошибка сети (ошибка подключения, тайм-аут и т.д.) |
| 34000 | Ошибка, возвращенная Discord API (недостаточно прав, неверные параметры и т.д.) |

## Специфические типы событий

Необходимо проверять `platform == "discord"`, чтобы использовать особенности этой платформы.

### Основные различия

1. **Система серверов/каналов**: Discord использует двухуровневую структуру из серверов (Guild) и каналов (Channel), канал является основной целью отправки сообщений
2. **События Gateway**: Все события получают через WebSocket Gateway, используя механизм Opcode + Dispatch
3. **Подписка на события Intents**: Подписка на типы событий через bitmask, `MESSAGE_CONTENT` требует привилегированных прав
4. **Типы сообщений**: Поддерживает текст, изображения, файлы, видео, аудио, Embed, Sticker и другие типы сообщений
5. **Формат упоминаний**: Discord использует формат `<@user_id>` для упоминания пользователей

### Расширенные поля

Все специфические поля имеют префикс `discord_`:
- `discord_raw`: Оригинальные данные события Discord
- `discord_raw_type`: Имя типа события (например, `MESSAGE_CREATE`)
- `discord_guild_id`: ID сервера
- `discord_channel_id`: ID канала

### Отображение detail_type

| Сцена Discord | detail_type | Описание |
|---|---|---|
| Канал сообщений | `channel` | Расширенный тип ErisPulse |
| Личные сообщения (DM) | `private` | Стандартный тип OneBot12 |

### Отображение типов событий

| Событие Discord | OneBot12 type | detail_type | Описание |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | Создание сообщения |
| MESSAGE_UPDATE | message | channel/private | Редактирование сообщения |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | Удаление сообщения |
| GUILD_MEMBER_ADD | notice | group_member_increase | Участие пользователя |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | Уход пользователя |
| GUILD_MEMBER_UPDATE | notice | group_member_update | Обновление информации о пользователе |
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
    {"type": "text", "data": {"text": "Смотри на эту картинку"}},
    {"type": "image", "data": {"file": "URL изображения", "url": "URL изображения", "file_name": "image.png"}}
  ],
  "alt_message": "Смотри на эту картинку[изображение]"
}
```

### Типы сообщений

Содержимое сообщений Discord автоматически преобразуется в соответствующие типы сообщений на основе полей `content`, `attachments`, `embeds`:

| Источник | Тип преобразования | Описание |
|---|---|---|
| Текст в `content` | `text` | Обычный текст |
| Упоминание `<@id>` в `content` | `mention` | Упоминание пользователя |
| Упоминание `<@&id>` в `content` | `discord_role_mention` | Упоминание роли |
| Упоминание `<#id>` в `content` | `discord_channel_mention` | Упоминание канала |
| `attachments` (image/*) | `image` | Изображение |
| `attachments` (video/*) | `video` | Видео |
| `attachments` (audio/*) | `audio` | Аудио |
| `attachments` (другое) | `file` | Файл |
| `embeds` | `discord_embed` | Встраиваемое сообщение |
| `sticker_items` | `discord_sticker` | Стикер |

### Сообщение `discord_embed`

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

## Подключение через Gateway

### Процесс подключения

1. Вызов `GET /gateway/bot` для получения URL WebSocket-шлюза
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
| 1 | Heartbeat | Отправка/Получение |心跳 (с последним seq) |
| 2 | Identify | Отправка | Аутентификация |
| 6 | Resume | Отправка | Восстановление сессии |
| 7 | Reconnect | Получение | Сервер требует переподключения |
| 9 | Invalid Session | Получение | Недействительная сессия |
| 10 | Hello | Получение | Приветствие при подключении (с heartbeat_interval) |
| 11 | Heartbeat ACK | Получение | Подтверждение心跳 |

### Переподключение и RESUME

- При разрыве соединения адаптер автоматически переподключается
- Если была предыдущая сессия, сначала пытается восстановить сессию с помощью RESUME (opcode 6)
- RESUME содержит `token`, `session_id`, последний `seq`, после восстановления дополняет пропущенные события
- При получении opcode 7 (Reconnect) сохраняет состояние сессии и переподключается
- При получении opcode 9 (Invalid Session) с `d=false` сбрасывает сессию и выполняет новый IDENTIFY

### Механизм心跳

- После получения HELLO ждет `heartbeat_interval * random()` миллисекунд, затем отправляет первый heartbeat
- Затем отправляет heartbeat каждые `heartbeat_interval` миллисекунд
- heartbeat содержит последний `seq` (opcode 1, `d: seq`)
- Если heartbeat отправлен, но в течение `heartbeat_interval` не получено ACK (opcode 11), считается, что соединение нарушено и происходит переподключение

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

### Отправка Embed-сообщения

```python
embed = {
    "title": "Анонс сервера",
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
            f"Получено {len(embeds)} Embed-сообщений"
        )
```

### Обработка взаимодействий

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return

    interaction = event.get_interaction_data()
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("Кнопка нажата!")
```