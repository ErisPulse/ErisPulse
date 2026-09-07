# Документация по функциям платформы Kook

KookAdapter — это адаптер, построенный на основе WebSocket-протокола бота Kook (开黑啦), объединяющий все функциональные модули Kook и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия соответствующего модуля: 0.1.0
- Ответственный: ShanFish

## Основная информация

- Краткое описание платформы: Kook (ранее 开黑啦) — это платформа для сообществ, поддерживающая текстовую, голосовую и видеосвязь, с полным набором интерфейсов для разработки ботов.
- Название адаптера: KookAdapter
- Поддержка нескольких аккаунтов: Поддерживает одновременную настройку нескольких ботов Kook
- Способ подключения: WebSocket-соединение (через шлюз Kook)
- Способ аутентификации: Аутентификация на основе Bot Token
- Поддержка цепочки модификаторов: Поддерживает цепочку методов модификаторов, таких как `.Reply()`, `.At()`, `.AtAll()`
- Совместимость с OneBot12: Поддерживает отправку OneBot12-форматированных сообщений

## Инструкция по настройке

KookAdapter поддерживает настройку нескольких аккаунтов, каждый аккаунт соответствует отдельному боту Kook.

```toml
# config.toml
# Аккаунт 1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token (обязательно, формат: Bot xxx/xxx)
bot_id = ""                   # ID пользователя бота (необязательно, если не заполнено, будет извлечено из token)
compress = true               # Включить сжатие WebSocket (необязательно, по умолчанию true)
enabled = true                # Включить аккаунт (необязательно, по умолчанию true)

# Аккаунт 2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> Совместимость со старой конфигурацией: если обнаружена старая одиночная конфигурация `[KookAdapter]` (с token), она будет автоматически перенесена в `accounts.default`.

**Описание параметров (для каждого аккаунта):**
- `token`: Токен Kook Bot (обязательно), получите его в [Консоли разработчика Kook](https://developer.kookapp.cn), формат: `Bot xxx/xxx`
- `bot_id`: ID пользователя бота (необязательно), если не заполнено, адаптер попытается автоматически извлечь его из token. Рекомендуется вручную указывать для обеспечения точности
- `compress`: Включить сжатие WebSocket-данных (необязательно, по умолчанию `true`), при включении используется zlib для распаковки данных
- `enabled`: Включить этот аккаунт (необязательно, по умолчанию `true`)

**Среда API:**
- Базовый адрес API Kook: `https://www.kookapp.cn/api/v3`
- WebSocket-шлюз получается динамически через API: `POST /gateway/index`

## Типы отправляемых сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка текстового сообщения.
- `.Image(file: bytes | str)` — отправка сообщения с изображением, поддерживает пути к файлу, URL и бинарные данные.
- `.Video(file: bytes | str)` — отправка видео, поддерживает пути к файлу, URL и бинарные данные.
- `.File(file: bytes | str, filename: str = None)` — отправка файла, поддерживает пути к файлу, URL и бинарные данные.
- `.Voice(file: bytes | str)` — отправка голосового сообщения, поддерживает пути к файлу, URL и бинарные данные.
- `.Markdown(text: str)` — отправка сообщения в формате KMarkdown.
- `.Card(card_data: dict)` — отправка карточного сообщения (CardMessage).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

### Цепочечные модификаторы (можно комбинировать)

Цепочечные модификаторы возвращают `self` и поддерживают цепочечное использование, обязательно должны вызываться перед окончательным методом отправки:

- `.Reply(message_id: str)` — ответить (с цитированием) на указанное сообщение.
- `.At(user_id: str)` — упомянуть пользователя, можно вызывать несколько раз для нескольких пользователей.
- `.AtAll()` — упомянуть всех.

### Примеры цепочечного вызова

```python
# Базовая отправка
await kook.Send.To("group", channel_id).Text("Hello")

# Ответ на сообщение
await kook.Send.To("group", channel_id).Reply(msg_id).Text("Ответное сообщение")

# Упоминание пользователя
await kook.Send.To("group", channel_id).At("user_id").Text("Привет")

# Упоминание нескольких пользователей
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("Упоминание нескольких пользователей")

# Упоминание всех
await kook.Send.To("group", channel_id).AtAll().Text("Анонс")

# Комбинированный вызов
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Составное сообщение")
```

### Поддержка OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12 для обеспечения совместимости между платформами:

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Использование упоминаний и цитирования в Raw_ob12
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### Дополнительные методы

Помимо отправки сообщений, адаптер Kook поддерживает следующие действия:

```python
# Редактирование сообщения (поддерживается только для KMarkdown type=9 и CardMessage type=10)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Обновленный контент**")

# Отмена отправки сообщения
await kook.Send.To("group", channel_id).Recall(msg_id)

# Загрузка файла (получение URL файла)
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно напрямую ожидать с помощью await для получения результата отправки. Результат возвращения соответствует стандартизированному формату возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата (code от API Kook)
    "data": {...},            // Данные ответа
    "message_id": "xxx",      // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "kook_raw": {...}         // Исходные данные ответа
}
```

### Описание кодов ошибок

| retcode | Описание |
|---------|----------|
| 0 | Успешно |
| 40100 | Недействительный или отсутствующий токен |
| 40101 | Токен просрочен |
| 40102 | Токен не соответствует боту |
| 40103 | Недостаточно прав |
| 40000 | Ошибка параметров |
| 40400 | Цель не существует |
| 40300 | Недостаточно прав для операции |
| 50000 | Внутренняя ошибка сервера |
| -1 | Внутренняя ошибка адаптера |

## Типы событий, специфичные для платформы

Для использования функций этой платформы необходимо выполнить проверку `platform=="kook"`

### Основные отличия

1. **Система каналов**: Kook использует двухуровневую структуру серверов (Guild) и каналов (Channel), канал является основным целевым объектом для отправки сообщений
2. **Типы сообщений**: Kook поддерживает различные типы сообщений, такие как текст (1), изображения (2), видео (3), файлы (4), аудио (8), KMarkdown (9), сообщения-карточки (10) и другие
3. **Система личных сообщений**: Kook различает сообщения в каналах и личные сообщения, используя разные API-эндпоинты
4. **Порядковый номер сообщений**: WebSocket Kook использует порядковый номер `sn` для обеспечения последовательности сообщений, поддерживает временное хранение и перестановку сообщений
5. **Редактирование и удаление сообщений**: Поддерживается редактирование отправленных сообщений (только KMarkdown и CardMessage) и удаление сообщений

### Дополнительные поля

- Все специфичные поля имеют префикс `kook_`
- Исходные данные сохраняются в поле `kook_raw`
- `kook_raw_type` указывает номер исходного типа сообщения Kook (например, `1` — текст, `255` — уведомление)

### Примеры специальных полей

```python
# Сообщение текста в канале
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

# KMarkdown сообщение
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ID пользователя",
  "group_id": "ID канала",
  "message_id": "ID сообщения",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "Разобранный чистый текст"}}
  ]
}

# Сообщение-карточка
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ID пользователя",
  "group_id": "ID канала",
  "message_id": "ID сообщения",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "Содержимое JSON-карточки"}}
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

### Типы сообщений

Тип сообщения Kook автоматически преобразуется в соответствующий тип сообщения на основе поля `type`:

| Тип Kook | Преобразованный тип | Описание |
|---|---|---|
| 1 | `text` | Текстовое сообщение |
| 2 | `image` | Сообщение с изображением |
| 3 | `video` | Сообщение с видео |
| 4 | `file` | Сообщение с файлом |
| 8 | `record` | Аудиосообщение |
| 9 | `text` | KMarkdown сообщение (извлекается чистый текст) |
| 10 | `json` | Сообщение-карточка (исходный JSON) |

Пример структуры сообщения:
```json
{
  "type": "image",
  "data": {
    "file": "URL изображения",
    "url": "URL изображения"
  }
}
```

### Сообщение упоминания (mention)

При наличии упоминания в сообщении в начале сообщения добавляется сообщение типа `mention`:

```json
{
  "type": "mention",
  "data": {
    "user_id": "ID пользователя, упомянутого в сообщении"
  }
}
```

### Сообщение упоминания всех (mention_all)

При упоминании всех участников в сообщении добавляется сообщение типа `mention_all`:

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket-подключение

### Процесс подключения

1. Используйте токен бота для вызова `POST /gateway/index`, чтобы получить адрес WebSocket-шлюза
2. Подключитесь к WebSocket-шлюзу
3. Получите сигнал HELLO (s=1), чтобы проверить состояние подключения
4. Начните цикл отправки пингов (PING, s=2, раз в 30 секунд)
5. Получите события сообщений (s=0), используя номер sn для обеспечения последовательности
6. Получите ответ на пинг PONG (s=3)

### Типы сигналов

| Сигнал | s-значение | Описание |
|-------|------------|----------|
| HELLO | 1 | Серверное приветственное сообщение, получаемое после успешного подключения |
| PING | 2 | Клиентский пинг, отправляемый каждые 30 секунд, содержит текущий sn |
| PONG | 3 | Ответ на пинг |
| RESUME | 4 | Сигнал для восстановления подключения, содержит sn для восстановления сессии |
| RECONNECT | 5 | Сервер требует повторного подключения, необходимо заново получить шлюз |
| RESUME_ACK | 6 | Ответ на успешное восстановление сессии |

### Переподключение при разрыве соединения

- При неожиданном разрыве соединения адаптер автоматически пытается повторно подключиться
- Если ранее был `sn > 0`, адаптер сначала попытается восстановить соединение с помощью RESUME (s=4)
- При неудаче восстановления сбросьте sn и очередь сообщений, начните полное подключение заново (процесс HELLO)
- При получении сигнала RECONNECT (s=5) очистите состояние и повторно подключитесь

### Механизм нумерации сообщений

Kook WebSocket использует `sn` (последовательный номер) для обеспечения последовательности сообщений:

- При получении каждого сообщения (s=0) значение sn увеличивается
- Если получено сообщение с непоследовательным sn, запускается режим временного хранения
- Сообщения в режиме временного хранения сортируются по sn и обрабатываются по мере поступления недостающих сообщений
- После очистки временного хранилища автоматически завершается режим временного хранения

## Примеры использования

### Обработка сообщений в канале

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
        print(f"Пользователь {user_id} удалил реакцию к сообщению {msg_id}")
```

### Отправка медиафайлов

```python
# Отправка изображения (по URL)
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# Отправка изображения (в байтах)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# Отправка видео
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# Отправка файла
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# Отправка аудио
await kook.Send.To("group", channel_id).Voice("https://example.com/voice.mp3")
```

### Отправка сообщений в формате KMarkdown и карточек

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**жирный** *курсив* [ссылка](https://example.com)")

# Карточка
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

### Редактирование и удаление сообщений

```python
# Отправка сообщения
result = await kook.Send.To("group", channel_id).Markdown("**Исходное содержимое**")
msg_id = result["data"]["msg_id"]

# Редактирование сообщения (поддерживаются только KMarkdown и CardMessage)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Обновленное содержимое**")

# Удаление сообщения
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### Обработка уведомлений об редактировании и удалении личных сообщений

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