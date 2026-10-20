# Документация по функциям платформы Kook

KookAdapter — это адаптер, построенный на основе WebSocket-протокола бота Kook (开黑啦), объединяющий все функциональные модули Kook и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия соответствующего модуля: 4.2.0
- Ответственный: ShanFish

## Основная информация

- Описание платформы: Kook (ранее 开黑啦) — это платформа сообщества, поддерживающая текстовую, голосовую и видеосвязь, предоставляющая полный интерфейс разработки ботов.
- Название адаптера: KookAdapter
- Поддержка нескольких аккаунтов: Поддерживает одновременную настройку нескольких ботов Kook.
- Способ подключения: WebSocket-длинное соединение (через шлюз Kook).
- Способ аутентификации: Аутентификация на основе токена бота.
- Поддержка цепочки модификаторов: Поддерживает методы цепочки модификаторов, такие как `.Reply()`, `.At()`, `.AtAll()`.
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12.

## Описание конфигурации

KookAdapter поддерживает настройку нескольких аккаунтов, каждый из которых соответствует отдельному боту Kook.

```toml
# config.toml
# Аккаунт 1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Токен бота Kook (обязательно, формат: Bot xxx/xxx)
bot_id = ""                   # ID пользователя бота (необязательно, если не указано, будет извлечен из токена)
compress = true               # Включить сжатие WebSocket (необязательно, по умолчанию true)
enabled = true                # Включить аккаунт (необязательно, по умолчанию true)

# Аккаунт 2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> Совместимость со старой конфигурацией: Если обнаружена старая конфигурация `[KookAdapter]` (с token), она автоматически переносится в `accounts.default`.

**Описание параметров конфигурации (для каждого аккаунта):**
- `token`: Токен бота Kook (обязательно), получаемый на [разработческой платформе Kook](https://developer.kookapp.cn), формат: `Bot xxx/xxx`
- `bot_id`: ID пользователя бота (необязательно), если не указано, адаптер попытается автоматически извлечь его из токена. Рекомендуется вручную указывать для обеспечения точности
- `compress`: Включить сжатие данных WebSocket (необязательно, по умолчанию `true`), при включении используется zlib для распаковки данных
- `enabled`: Включить этот аккаунт (необязательно, по умолчанию true)

**API-среда:**
- Базовый адрес API Kook: `https://www.kookapp.cn/api/v3`
- WebSocket-шлюз получается динамически через API: `POST /gateway/index`

## Обновление до v5 (4.1.0)

Данный адаптер был обновлен до соответствия v5 (постепенное обновление, совместимый API):

- **Наследование BaseConverter**: Общие поля конвертера строятся с помощью `build_base_event` фреймворка
- **API DSL**: Стандартные действия API (см. ниже)
- **Стандартный сегмент keyboard**: `{"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}}` текст + клавиатура автоматически объединяются в карточное сообщение Kook (section + action-group); модификатор .Keyboard(rows) принимает общую структуру
- **Принадлежность задачи spawn_background**: Задачи подключения используют `untime.spawn_background`
- **Мягкая зависимость от фреймворка**: Временная проверка ErisPulse>=2.7.1 и вывод предупреждения; при запуске выводится лог версии

### Стандартные действия API

```python
from ErisPulse import sdk
kook = sdk.adapter.get("kook")

result = await kook.Api.get_self_info()              # GET /users/@me
result = await kook.Api.get_user_info(user_id)       # POST /user/view
result = await kook.Api.get_guild_info(guild_id)     # POST /guild/view
result = await kook.Api.get_guild_list()             # POST /guild/list
result = await kook.Api.get_channel_info(channel_id) # POST /channel/view
result = await kook.Api.get_channel_list(guild_id)   # POST /channel/list
await kook.Api.delete_message(msg_id)                # POST /message/delete
result = await kook.Api.Using("main").get_self_info()
```

### Кнопки (keyboard)

```python
rows = [[{"label": "Опция A", "type": "callback", "data": "vote:A"},
         {"label": "Официальный сайт",  "type": "link",     "data": "https://example.com"}]]
await kook.Send.To("channel", channel_id).Keyboard(rows).Text("Выберите")
# Текст и кнопки автоматически объединяются в карточное сообщение Kook (section + action-group)

# Обработка нажатия кнопки (стандартные поля)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "kook" and event.get("button_data"):
        data = event["button_data"]
```

---
## Поддерживаемые типы отправки сообщений

Все методы отправки сообщений реализованы через цепочечный синтаксис, например:
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка обычного текстового сообщения.
- `.Image(file: bytes | str)` — отправка изображения, поддержка путей к файлу, URL, двоичных данных.
- `.Video(file: bytes | str)` — отправка видео, поддержка путей к файлу, URL, двоичных данных.
- `.File(file: bytes | str, filename: str = None)` — отправка файла, поддержка путей к файлу, URL, двоичных данных.
- `.Voice(file: bytes | str)` — отправка голосового сообщения, поддержка путей к файлу, URL, двоичных данных.
- `.Markdown(text: str)` — отправка сообщения в формате KMarkdown.
- `.Card(card_data: dict)` — отправка карточного сообщения (CardMessage).
- `.MergeForward(nodes, title="Объединённая пересылка")` — отправка объединённого пересланного сообщения (отображается как карточка: заголовок header + каждый элемент сообщения как section, KMD-перекодировка, ≤40 элементов).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

### Методы цепочки модификаторов (можно комбинировать)

Методы цепочки модификаторов возвращают `self`, поддерживают цепочечное использование, должны вызываться до окончательного метода отправки:

- `.Reply(message_id: str)` — ответить (цитировать) на указанное сообщение.
- `.At(user_id: str)` — упомянуть пользователя, можно вызывать несколько раз для упоминания нескольких пользователей.
- `.AtAll()` — упомянуть всех.

### Примеры цепочечного вызова

```python
# Базовая отправка
await kook.Send.To("group", channel_id).Text("Hello")

# Ответ на сообщение
await kook.Send.To("group", channel_id).Reply(msg_id).Text("Ответ")

# Упоминание пользователя
await kook.Send.To("group", channel_id).At("user_id").Text("Привет")

# Упоминание нескольких пользователей
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("Упоминание нескольких пользователей")

# Упоминание всех
await kook.Send.To("group", channel_id).AtAll().Text("Анонс")

# Комбинированное использование
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Сложное сообщение")
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость между платформами:

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Использование сегментов упоминания и ответа в Raw_ob12
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### Дополнительные методы операций

Помимо отправки сообщений, адаптер Kook поддерживает следующие операции:

```python
# Редактирование сообщения (поддерживается только для KMarkdown type=9 и CardMessage type=10)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Обновлённое содержимое**")

# Отмена отправки сообщения
await kook.Send.To("group", channel_id).Recall(msg_id)

# Загрузка файла (получение URL файла)
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект задачи, который можно ожидать с помощью `await`. Возвращаемый результат соответствует стандартизированному формату возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата (код Kook API)
    "data": {...},            // Данные ответа
    "message_id": "xxx",      // ID сообщения
    "message": "",            // Сообщение об ошибке
    "kook_raw": {...}         // Исходные данные ответа
}
```

### Описание кодов ошибок

| retcode | Описание |
|---------|----------|
| 0 | Успешно |
| 40100 | Неверный или отсутствующий токен |
| 40101 | Токен истёк |
| 40102 | Токен не соответствует боту |
| 40103 | Отсутствует доступ |
| 40000 | Ошибка параметров |
| 40400 | Цель не существует |
| 40300 | Недостаточно прав для операции |
| 50000 | Внутренняя ошибка сервера |
| -1 | Внутренняя ошибка адаптера |

## Специфические типы событий

Необходимо использовать `platform=="kook"` для проверки перед использованием специфических функций платформы

### Основные различия

1. **Система каналов**: Kook использует двухуровневую структуру серверов (Guild) и каналов (Channel), канал является основной целью отправки сообщений
2. **Типы сообщений**: Kook поддерживает различные типы сообщений, такие как текст (1), изображение (2), видео (3), файл (4), голос (8), KMarkdown (9), карточные сообщения (10)
3. **Система личных сообщений**: Kook различает сообщения каналов и личные сообщения, используя разные API-эндпоинты
4. **Нумерация сообщений**: WebSocket Kook использует `sn` для обеспечения упорядоченности сообщений, поддерживает временный кэш и пересортировку неупорядоченных сообщений
5. **Редактирование и отмена сообщений**: Поддержка редактирования отправленных сообщений (только KMarkdown и CardMessage) и отмена сообщений

### Расширенные поля

- Все специфические поля имеют префикс `kook_`
- Оригинальные данные сохраняются в поле `kook_raw`
- `kook_raw_type` указывает номер оригинального типа сообщения Kook (например, `1` для текста, `255` для уведомления)

### Примеры специальных полей

```python
# Текстовое сообщение канала
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ID пользователя",
  "group_id": "ID канала",
  "channel_id": "ID канала",
  "message_id": "ID сообщения",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# Сообщение с изображением
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ID пользователя",
  "group_id": "ID канала",
  "channel_id": "ID канала",
  "message_id": "ID сообщения",
  "kook_raw": {...},
  "kook_raw_type": "2",
  "message": [
    {"type": "image", "data": {"file": "URL изображения", "url": "URL изображения"}}
  ],
  "alt_message": "Содержимое изображения"
}

# KMarkdown-сообщение
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ID пользователя",
  "group_id": "ID канала",
  "message_id": "ID сообщения",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "Разобранный текст"}}
  ]
}

# Карточное сообщение
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ID пользователя",
  "group_id": "ID канала",
  "message_id": "ID сообщения",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "Содержимое JSON карточки"}}
  ]
}

# Личное сообщение
{
  "type": "message",
  "detail_type": "private",
  "user_id": "ID пользователя",
  "message_id": "ID сообщения",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Содержимое личного сообщения"}}
  ]
}
```

### Типы сегментов сообщений

Типы сообщений Kook автоматически преобразуются в соответствующие сегменты сообщений по полю `type`:

| Тип Kook | Преобразованный тип | Описание |
|---|---|---|
| 1 | `text` | Текстовое сообщение |
| 2 | `image` | Сообщение с изображением |
| 3 | `video` | Сообщение с видео |
| 4 | `file` | Сообщение с файлом |
| 8 | `record` | Голосовое сообщение |
| 9 | `text` | KMarkdown-сообщение (извлекается текстовое содержимое) |
| 10 | `json` | Карточное сообщение (исходный JSON) |

Пример структуры сегмента сообщения:
```json
{
  "type": "image",
  "data": {
    "file": "URL изображения",
    "url": "URL изображения"
  }
}
```

### Сегмент упоминания

При наличии упоминаний в сообщении в начало сегментов добавляется сегмент `mention`:

```json
{
  "type": "mention",
  "data": {
    "user_id": "ID упомянутого пользователя"
  }
}
```

### Сегмент упоминания всех

При упоминании всех добавляется сегмент `mention_all`:

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket-соединение

### Процесс подключения

1. Используя токен бота, вызовите `POST /gateway/index`, чтобы получить адрес WebSocket-шлюза
2. Подключитесь к WebSocket-шлюзу
3. Получите сигнал HELLO (s=1), подтвердите состояние подключения
4. Начните цикл отправки пинга (PING, s=2, каждые 30 секунд)
5. Получите события сообщений (s=0), используя номер sn для обеспечения упорядоченности
6. Получите ответ PONG (s=3) на пинг

### Типы сигналов

| Сигнал | s-значение | Описание |
|------|-----|------|
| HELLO | 1 | Сигнал приветствия от сервера, получается после успешного подключения |
| PING | 2 | Пинг от клиента, отправляется каждые 30 секунд, содержит текущий sn |
| PONG | 3 | Ответ на пинг |
| RESUME | 4 | Сигнал возобновления подключения, содержит sn для восстановления сессии |
| RECONNECT | 5 | Сигнал от сервера о необходимости переподключения, требуется заново получить шлюз |
| RESUME_ACK | 6 | Ответ на успешное возобновление |

### Переподключение при разрыве соединения

- При неожиданном разрыве соединения адаптер автоматически пытается переподключиться
- Если ранее был `sn > 0`, сначала будет попытка RESUME (s=4) для восстановления соединения
- При неудаче RESUME, сбрасываются sn и очередь сообщений, и начинается полное новое подключение (процесс HELLO)
- При получении сигнала RECONNECT (s=5) состояние очищается и происходит переподключение

### Механизм нумерации сообщений

WebSocket Kook использует `sn` (последовательный номер) для обеспечения упорядоченности сообщений:

- При получении каждого сообщения (s=0), sn увеличивается
- Если получено сообщение с несопоставимым sn, переходит в режим временного хранения
- Сообщения в буфере сортируются по sn, ожидая поступления недостающих сообщений, после чего обрабатываются в порядке
- После очистки буфера автоматически выходит из режима временного хранения

## Примеры использования

### Обработка сообщений канала

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

kook = sdk.adapter.get("kook")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await kook.Send.To("group", channel_id).Text("Hello!")
```

### Обработка личных сообщений

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "private":
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await kook.Send.To("user", user_id).Text(f"Вы сказали: {text}")
```

### Обработка уведомлений (реакции и т.д.)

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "added_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"Пользователь {user_id} добавил реакцию к сообщению {msg_id}")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"Пользователь {user_id} удалил реакцию с сообщения {msg_id}")
```

### Отправка медиа-сообщений

```python
# Отправка изображения (URL)
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# Отправка изображения (байты)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# Отправка видео
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# Отправка файла
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# Отправка голосового сообщения
await kook.Send.To("group", channel_id).Voice("https://example.com/voice.mp3")
```

### Отправка сообщений KMarkdown и карточных сообщений

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**Жирный** *курсив* [ссылка](https://example.com)")

# Карточное сообщение
card = {
    "type": "card",
    "theme": "primary",
    "size": "lg",
    "modules": [
        {"type": "header", "text": {"type": "plain-text", "content": "Заголовок"}},
        {"type": "section", "text": {"type": "kmarkdown", "content": "Содержимое"}}
    ]
}
await kook.Send.To("group", channel_id).Card(card)
```

### Редактирование и отмена сообщений

```python
# Отправка сообщения
result = await kook.Send.To("group", channel_id).Markdown("**Оригинальное содержимое**")
msg_id = result["data"]["msg_id"]

# Редактирование сообщения (поддерживается только для KMarkdown и CardMessage)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Обновлённое содержимое**")

# Отмена сообщения
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### Обработка уведомлений о редактировании и удалении личных сообщений

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"Личное сообщение обновлено: {msg_id}, новое содержимое: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"Личное сообщение удалено: {msg_id}")
```