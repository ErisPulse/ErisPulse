# Документация по функциям платформы Discord

DiscordAdapter — это адаптер, построенный на основе протокола Discord Gateway (WebSocket) и REST API v10, объединяющий основные функции Discord Bot и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

[**English**](docs/ru/quick-start.md)

## Информация о документации

- Версия соответствующего модуля: 4.1.0
- Ответственный: ErisPulse
- Версия Discord API: v10

Пожалуйста, верните непосредственно переведённый полный Markdown-контент, не включая никаких других текстов.

Ещё раз напоминаем: если документация содержит строку переключения языка (где названия языков разделены символами `` | ``), необходимо строго соблюдать вышеуказанное правило №8, не записывая ошибочную форму вида ``[**Label**](file)``.

## Основная информация

- **Описание платформы**: Discord — популярная платформа для общения в сообществах, поддерживающая серверы, каналы, личные сообщения и другие формы общения, предоставляющая полный API для разработки ботов
- **Название адаптера**: DiscordAdapter
- **Поддержка нескольких аккаунтов**: Поддерживает настройку нескольких Discord-ботов одновременно
- **Способы подключения**: Gateway WebSocket (для получения событий) + REST API (для отправки сообщений/вызовов интерфейсов)
- **Способы аутентификации**: Bot Token (HTTP-заголовок `Authorization: Bot {token}`, токен передаётся в payload при идентификации через Gateway)
- **Поддержка цепочки методов**: Поддерживает цепочку методов, таких как `.Reply()`, `.At()`, `.AtAll()` и др.
- **Совместимость с OneBot12**: Поддерживает отправку сообщений в формате OneBot12

Ссылки на документацию:
- [Официальная документация Discord](https://discord.com/developers/docs/intro)
- [Официальный API Discord](https://discord.com/developers/docs/introduce)
- [Официальный Discord SDK](https://github.com/discord/discord-sdk)

Для получения дополнительной информации, пожалуйста, посетите [документацию](docs/ru/quick-start.md).

## Инструкция по настройке

DiscordAdapter поддерживает настройку нескольких аккаунтов, каждый аккаунт соответствует отдельному Discord Bot.

```toml
# config.toml

# Аккаунт 1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token (обязательно)
intents = 33281                 # Gateway Intents (необязательно, по умолчанию 33281)
enabled = true                  # Включен ли аккаунт (необязательно, по умолчанию true)

# Аккаунт 2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**Описание параметров (для каждого аккаунта):**

- `token`: Discord Bot Token (обязательно), получите из [Discord Developer Portal](https://discord.com/developers/applications)
- `intents`: Маска битов Gateway Intents (необязательно, по умолчанию `33281`), определяет типы событий, на которые подписывается Bot
- `bot_id`: ID пользователя Bot (необязательно, ID автоматически получается во время выполнения из события READY, не нужно заполнять вручную)
- `enabled`: Включен ли этот аккаунт (необязательно, по умолчанию `true`)

### Gateway Intents

Intents используются в виде маски битов, вычисляются путем побитового объединения (OR) значений каждого Intent:

| Intent | Бит | Значение | Описание | Привилегированный |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | Создание/удаление/обновление серверов, изменение каналов и ролей | Нет |
| GUILD_MEMBERS | `1 << 1` | 2 | Участие/выход/обновление участников | Да |
| GUILD_MESSAGES | `1 << 9` | 512 | Получение и отправка сообщений на серверах | Нет |
| MESSAGE_CONTENT | `1 << 15` | 32768 | Содержимое сообщений (без этого Intent содержимое пустое) | Да |

Значение по умолчанию `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`.

> **Важно**: Привилегированные Intents необходимо включить в Discord Developer Portal → Bot → Privileged Gateway Intents. Если Bot находится более чем в 100 серверах, необходимо пройти проверку Discord.

**Среда API:**
- Базовый адрес Discord REST API: `https://discord.com/api/v10`
- Адрес WebSocket Gateway: получается динамически через `GET /gateway/bot`, обычно `wss://gateway.discord.gg/?v=10&encoding=json`

## Типы поддерживаемых отправляемых сообщений

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
- `.Reply(content: str, message_id: str)` — ответ на указанное сообщение (удобный метод завершения).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.
- `.Raw_json(json_str: str)` — отправка произвольного JSON-запроса Discord API.

### Методы цепочечных модификаторов (можно комбинировать)

Методы цепочечных модификаторов возвращают `self`, поддерживают цепочечные вызовы и должны быть вызваны перед окончательным методом отправки:

- `.Reply(message_id: str)` — ответ (ссылка) на указанное сообщение, устанавливает `message_reference`.
- `.At(user_id: str)` — упоминание указанного пользователя, преобразуется в `<@user_id>`, может быть вызвано несколько раз.
- `.AtAll()` — упоминание всех участников, преобразуется в `@everyone`.

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
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("Упоминание нескольких пользователей@")

# Упоминание всех
await discord.Send.To("group", channel_id).AtAll().Text("Объявление")

# Комбинированный вызов
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Составное сообщение")

# Встраиваемое сообщение Embed
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

При отправке личных сообщений адаптер автоматически создает канал личных сообщений:

```python
# Отправка личного сообщения
await discord.Send.To("user", user_id).Text("Содержание личного сообщения")
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

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно напрямую использовать с await для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату возвращаемых значений адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата (0 означает успех)
    "data": {...},            // Исходный ответ Discord API
    "message_id": "xxx",      // Идентификатор сообщения (при отправке сообщения)
    "message": "",            // Сообщение об ошибке
    "discord_raw": {...}      // Исходные данные ответа
}
```

### Описание кодов ошибок

| retcode | Описание |
|---------|----------|
| 0 | Успех |
| 33001 | Сетевая ошибка (ошибка подключения, таймаут и т.д.) |
| 34000 | Ошибка, возвращённая Discord API (недостаточно прав, неверные параметры и т.д.) |

## Типы событий, специфичные для Discord

Для использования функций этой платформы необходимо проверять `platform == "discord"`.

### Основные отличия

1. **Система серверов/каналов**: Discord использует двухуровневую структуру из серверов (Guild) и каналов (Channel), где канал является основным целевым объектом для отправки сообщений
2. **События Gateway**: Все события получают через WebSocket Gateway, используя механизм Opcode + Dispatch
3. **Подписка на события (Intents)**: Подписка на типы событий осуществляется с помощью битовой маски, для `MESSAGE_CONTENT` требуется привилегированный доступ
4. **Типы сообщений**: Поддержка текстовых, изображений, файлов, видео, аудио, Embed, Sticker и других типов сообщений
5. **Формат упоминания (Mention)**: Discord использует формат `<@user_id>` для обозначения упоминания пользователей

### Расширенные поля

Все специфичные поля имеют префикс `discord_`:
- `discord_raw`: исходные данные события Discord
- `discord_raw_type`: имя типа исходного события (например, `MESSAGE_CREATE`)
- `discord_guild_id`: идентификатор сервера
- `discord_channel_id`: идентификатор канала

### Сопоставление detail_type

| Сценарий Discord | detail_type | Описание |
|---|---|---|
| Сообщение в канале | `channel` | Расширение ErisPulse |
| Личное сообщение (DM) | `private` | Стандартный тип OneBot12 |

### Сопоставление типов событий

| Событие Discord | OneBot12 type | detail_type | Описание |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | Создание сообщения |
| MESSAGE_UPDATE | message | channel/private | Редактирование сообщения |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | Удаление сообщения |
| GUILD_MEMBER_ADD | notice | group_member_increase | Участник присоединился |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | Участник покинул |
| GUILD_MEMBER_UPDATE | notice | group_member_update | Обновление информации участника |
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
  "alt_message": "[Встроенный элемент]"
}

# Сообщение с вложенным файлом
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "Посмотри на это изображение"}},
    {"type": "image", "data": {"file": "URL изображения", "url": "URL изображения", "file_name": "image.png"}}
  ],
  "alt_message": "Посмотри на это изображение[Изображение]"
}
```

### Типы элементов сообщений

Содержимое сообщений Discord автоматически преобразуется в соответствующие типы сообщений на основе полей `content`, `attachments` и `embeds`:

| Источник | Тип преобразования | Описание |
|---|---|---|
| Текст в content | `text` | Чистый текст |
| `<@id>` в content | `mention` | Упоминание пользователя |
| `<@&id>` в content | `discord_role_mention` | Упоминание роли |
| `<#id>` в content | `discord_channel_mention` | Упоминание канала |
| attachments (image/*) | `image` | Вложение изображения |
| attachments (video/*) | `video` | Вложение видео |
| attachments (audio/*) | `audio` | Вложение аудио |
| attachments (другое) | `file` | Вложение файла |
| embeds | `discord_embed` | Встроенный элемент |
| sticker_items | `discord_sticker` | Наклейка |

### Элемент сообщения discord_embed

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

## Подключение к шлюзу

### Процесс подключения

1. Вызовите `GET /gateway/bot`, чтобы получить URL WebSocket-шлюза
2. Подключитесь к `wss://gateway.discord.gg/?v=10&encoding=json`
3. Получите opcode 10 HELLO: содержит `heartbeat_interval`
4. Отправьте opcode 2 IDENTIFY: содержит токен, intents и properties
5. Начните цикл心跳: отправляйте opcode 1 Heartbeat с интервалом `heartbeat_interval`
6. Получите opcode 0 Dispatch: событие рассылки (`t`=имя события, `s`=номер последовательности, `d`=данные)
7. Получите opcode 11 Heartbeat ACK: подтверждение心跳

### Описание opcodes

| Opcode | Название | Направление | Описание |
|--------|----------|-------------|----------|
| 0 | Dispatch | Получение | Рассылка событий (с полями `t`, `s`, `d`) |
| 1 | Heartbeat | Отправка/Получение | Heartbeat (содержит последний seq) |
| 2 | Identify | Отправка | Аутентификация |
| 6 | Resume | Отправка | Восстановление сессии |
| 7 | Reconnect | Получение | Сервер требует повторного подключения |
| 9 | Invalid Session | Получение | Недействительная сессия |
| 10 | Hello | Получение | Приветствие при подключении (содержит heartbeat_interval) |
| 11 | Heartbeat ACK | Получение | Подтверждение heartbeat |

### Переподключение и RESUME

- После разрыва соединения адаптер автоматически повторяет попытку подключения
- Если ранее был `session_id`, сначала попытайтесь восстановить сессию с помощью RESUME (opcode 6)
- RESUME содержит `token`, `session_id` и последний `seq`, после восстановления повторно отправляются пропущенные события
- Получив opcode 7 (Reconnect), сохраните состояние сессии и повторно подключитесь
- Получив opcode 9 (Invalid Session) и `d=false`, очистите сессию и повторно выполните IDENTIFY

### Механизм heartbeat

- После получения HELLO, подождите `heartbeat_interval * random()` миллисекунд и отправьте первый heartbeat
- Затем отправляйте heartbeat каждые `heartbeat_interval` миллисекунд
- Heartbeat содержит последнее значение `seq` (opcode 1, `d: seq`)
- Если после отправки heartbeat в течение `heartbeat_interval` не получено ACK (opcode 11), соединение считается нарушенным и происходит повторное подключение

[**English**](docs/ru/quick-start.md)

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
    "footer": {"text": "Powered by ErisPulse"},
    "timestamp": "2025-01-01T00:00:00.000Z",
}
await discord.Send.To("group", channel_id).Embed(embed)
```

### Использование специфичных методов Discord

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