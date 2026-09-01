# Документация по функциям платформы Discord

DiscordAdapter — это адаптер, построенный на основе протокола Discord Gateway (WebSocket) и REST API v10, объединяющий основные функции Discord Bot и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия соответствующего модуля: 4.1.0
- Ответственный: ErisPulse
- Версия Discord API: v10

## Основная информация

- Краткое описание платформы: Discord — популярная платформа для общения в сообществах, поддерживающая серверы, каналы, личные сообщения и другие формы диалогов, а также предоставляет полный интерфейс для разработки ботов.
- Название адаптера: DiscordAdapter
- Поддержка нескольких аккаунтов: Поддерживает настройку нескольких Discord-ботов одновременно
- Способ подключения: WebSocket Gateway (для получения событий) + REST API (для отправки сообщений/вызовов интерфейсов)
- Способ аутентификации: Bot Token (в HTTP-заголовке `Authorization: Bot {token}`, тело запроса IDENTIFY для Gateway содержит токен)
- Поддержка цепочки модификаторов: Поддерживает цепочку методов модификаторов, таких как `.Reply()`, `.At()`, `.AtAll()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Инструкция по настройке

DiscordAdapter поддерживает настройку нескольких аккаунтов, каждый аккаунт соответствует отдельному Discord Bot.

```toml
# config.toml

# Аккаунт 1
[DiscordAdapter.accounts.default]
token = "ВАШ_BOT_TOKEN"       # Discord Bot Token (обязательно)
intents = 33281                 # Gateway Intents (необязательно, по умолчанию 33281)
enabled = true                  # Включено ли (необязательно, по умолчанию true)

# Аккаунт 2
[DiscordAdapter.accounts.bot2]
token = "ДРУГОЙ_BOT_TOKEN"
intents = 33281
enabled = true
```

**Описание параметров (для каждого аккаунта):**

- `token`: Discord Bot Token (обязательно), получите в [Discord Developer Portal](https://discord.com/developers/applications)
- `intents`: Bitmask Gateway Intents (необязательно, по умолчанию `33281`), определяет типы событий, на которые подписывается Bot
- `bot_id`: ID пользователя Bot (необязательно, ID будет автоматически получаться во время запуска из события READY, не нужно вручную заполнять)
- `enabled`: Включён ли этот аккаунт (необязательно, по умолчанию `true`)

### Gateway Intents

Intents используют bitmask, вычисляются путем побитового объединения (OR) значений каждого Intent:

| Intent | Бит | Значение | Описание | Привилегированный |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | Изменения серверов (создание/удаление/обновление), каналов, ролей | Нет |
| GUILD_MEMBERS | `1 << 1` | 2 | Изменения участников (вступление/уход/обновление) | Да |
| GUILD_MESSAGES | `1 << 9` | 512 | Отправка и получение сообщений на серверах | Нет |
| MESSAGE_CONTENT | `1 << 15` | 32768 | Содержание сообщений (без этого Intent содержание будет пустым) | Да |

Значение по умолчанию `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`.

> **Внимание**: Привилегированные Intents необходимо включить в Discord Developer Portal → Bot → Privileged Gateway Intents. Если Bot находится на более чем 100 серверах, также требуется прохождение проверки Discord.

**Среда API:**
- Базовый адрес Discord REST API: `https://discord.com/api/v10`
- Адрес WebSocket Gateway: получается динамически через `GET /gateway/bot`, обычно `wss://gateway.discord.gg/?v=10&encoding=json`

## Типы поддерживаемых сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:
```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка обычного текстового сообщения.
- `.Embed(embed: dict | list)` — отправка встраиваемого сообщения Embed, поддерживает одно или несколько Embed.
- `.Image(file: bytes | str, filename: str = "image.png")` — отправка изображения, поддерживает бинарные данные или URL.
- `.File(file: bytes | str, filename: str = None)` — отправка файла, поддерживает бинарные данные или URL.
- `.Reply(content: str, message_id: str)` — ответ на указанное сообщение (удобный метод).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.
- `.Raw_json(json_str: str)` — отправка произвольного JSON-запроса Discord API.

### Цепочечные модификаторы (можно комбинировать)

Цепочечные модификаторы возвращают `self`, поддерживают цепочечное использование и должны вызываться до окончательного метода отправки:

- `.Reply(message_id: str)` — ответ (ссылка) на указанное сообщение, устанавливает `message_reference`.
- `.At(user_id: str)` — упоминание пользователя, преобразуется в `<@user_id>`, может вызываться несколько раз.
- `.AtAll()` — упоминание всех, преобразуется в `@everyone`.

### Примеры цепочечного вызова

```python
# Базовая отправка
await discord.Send.To("group", channel_id).Text("Hello")

# Ответ на сообщение
await discord.Send.To("group", channel_id).Reply(msg_id).Text("Ответное сообщение")

# Удобный ответ (одним шагом)
await discord.Send.To("group", channel_id).Reply("Содержимое ответа", msg_id)

# Упоминание пользователя
await discord.Send.To("group", channel_id).At("user_id").Text("Привет")

# Упоминание нескольких пользователей
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("Упоминание нескольких пользователей")

# Упоминание всех
await discord.Send.To("group", channel_id).AtAll().Text("Анонс")

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
await discord.Send.To("user", user_id).Text("Содержимое личного сообщения")
await discord.Send.To("user", user_id).Embed(embed)
```

### Операции с сообщениями

```python
# Отмена отправки сообщения
await discord.Send.To("group", channel_id).Recall(msg_id)

# Формат OneBot12
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно непосредственно ожидать для получения результата отправки. Результат соответствует стандартизированному возвращаемому значению адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата (0 означает успех)
    "data": {...},            // Оригинальный ответ Discord API
    "message_id": "xxx",      // Идентификатор сообщения (при отправке сообщения)
    "message": "",            // Сообщение об ошибке
    "discord_raw": {...}      // Оригинальные данные ответа
}
```

### Объяснение кодов ошибок

| retcode | Описание |
|---------|----------|
| 0 | Успех |
| 33001 | Ошибка сети (сбой подключения, таймаут и т.д.) |
| 34000 | Discord API возвращает ошибку (недостаточно прав, ошибка параметров и т.д.) |

## Типы событий, специфичные для Discord

Необходимо проверять `platform == "discord"`, чтобы использовать функции, специфичные для этой платформы.

### Основные отличия

1. **Система серверов/каналов**: Discord использует двухуровневую структуру серверов (Guild) и каналов (Channel), где канал является основным целевым объектом для отправки сообщений.
2. **События Gateway**: Все события получают через WebSocket Gateway, используя механизм Opcode + Dispatch.
3. **Подписка на события (Intents)**: Подписка на типы событий осуществляется с помощью битовой маски, а для `MESSAGE_CONTENT` требуется привилегированный доступ.
4. **Типы сообщений**: Поддержка текстовых, изображений, файлов, видео, аудио, Embed, стикеров и других типов сообщений.
5. **Формат упоминаний (Mention)**: Discord использует формат `<@user_id>` для обозначения упоминания пользователя.

### Расширенные поля

Все специфичные поля идентифицируются с префиксом `discord_`:
- `discord_raw`: исходные данные события Discord
- `discord_raw_type`: имя типа исходного события (например, `MESSAGE_CREATE`)
- `discord_guild_id`: идентификатор сервера
- `discord_channel_id`: идентификатор канала

### Отображение detail_type

| Сценарий Discord | detail_type | Описание |
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
  "discord_channel_id": "ID канала DM",
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
    {"type": "text", "data": {"text": "Посмотри на эту картинку"}},
    {"type": "image", "data": {"file": "URL изображения", "url": "URL изображения", "file_name": "image.png"}}
  ],
  "alt_message": "Посмотри на эту картинку[изображение]"
}
```

### Типы сообщений

Содержимое Discord-сообщений автоматически преобразуется в соответствующие типы сообщений на основе полей `content`, `attachments` и `embeds`:

| Источник | Тип преобразования | Описание |
|---|---|---|
| Текст content | `text` | Чистый текст |
| Упоминание `<@id>` | `mention` | Упоминание пользователя |
| Упоминание `<@&id>` | `discord_role_mention` | Упоминание роли |
| Упоминание `<#id>` | `discord_channel_mention` | Упоминание канала |
| Вложения (image/*) | `image` | Вложение изображения |
| Вложения (video/*) | `video` | Вложение видео |
| Вложения (audio/*) | `audio` | Вложение аудио |
| Вложения (другое) | `file` | Вложение файла |
| Вложения embeds | `discord_embed` | Встраиваемое сообщение |
| Вложения sticker_items | `discord_sticker` | Стикер |

### Сообщение discord_embed

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

## Подключение к шлюзу

### Процесс подключения

1. Вызовите `GET /gateway/bot`, чтобы получить URL WebSocket-шлюза
2. Подключитесь к `wss://gateway.discord.gg/?v=10&encoding=json`
3. Получите opcode 10 HELLO: содержит `heartbeat_interval`
4. Отправьте opcode 2 IDENTIFY: с токеном, intents и properties
5. Начните цикл отправки heartbeat: отправляйте opcode 1 Heartbeat с интервалом `heartbeat_interval`
6. Получите opcode 0 Dispatch: событие диспетчеризации (`t`=имя события, `s`=номер последовательности, `d`=данные)
7. Получите opcode 11 Heartbeat ACK: подтверждение heartbeat

### Описание opcodes

| Opcode | Название | Направление | Описание |
|--------|----------|-------------|----------|
| 0 | Dispatch | Получение | Диспетчеризация событий (с полями `t`, `s`, `d`) |
| 1 | Heartbeat | Отправка/Получение | Heartbeat (с последним seq) |
| 2 | Identify | Отправка | Аутентификация |
| 6 | Resume | Отправка | Восстановление сессии |
| 7 | Reconnect | Получение | Сервер требует переподключения |
| 9 | Invalid Session | Получение | Неверная сессия |
| 10 | Hello | Получение | Приветствие при подключении (с heartbeat_interval) |
| 11 | Heartbeat ACK | Получение | Подтверждение heartbeat |

### Переподключение и RESUME

- При разрыве соединения адаптер автоматически повторяет попытку подключения
- Если ранее существовал `session_id`, сначала попытайтесь восстановить сессию с помощью RESUME (opcode 6)
- RESUME содержит `token`, `session_id`, и последний `seq`, восстанавливая пропущенные события
- При получении opcode 7 (Reconnect) сохраняйте состояние сессии и переподключайтесь
- При получении opcode 9 (Invalid Session) и `d=false` очищайте сессию и повторно выполняйте IDENTIFY

### Механизм heartbeat

- После получения HELLO, подождите `heartbeat_interval * random()` миллисекунд, чтобы отправить первый heartbeat
- Затем отправляйте heartbeat каждые `heartbeat_interval` миллисекунд
- Heartbeat содержит последнее значение `seq` (opcode 1, `d: seq`)
- Если после отправки heartbeat в течение `heartbeat_interval` не получено подтверждение (opcode 11), соединение считается нарушенным и происходит переподключение

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

### Отправка Embed-сообщений

```python
embed = {
    "title": "Объявление сервера",
    "description": "Добро пожаловать в Discord-адаптер ErisPulse",
    "color": 3447003,
    "fields": [
        {"name": "Версия", "value": "4.0.0", "inline": True},
        {"name": "Фреймворк", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Разработано с помощью ErisPulse"},
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