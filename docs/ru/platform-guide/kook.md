# Документация по функциям платформы Kook

KookAdapter — это адаптер, построенный на основе WebSocket-протокола ботов Kook (开黑啦), объединяющий все функциональные модули Kook и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Версия соответствующего модуля: 0.1.0
- Ответственный: ShanFish

## Основная информация

- Краткое описание платформы: Kook (ранее 开黑啦) — это платформа сообщества, поддерживающая текстовую, голосовую и видеосвязь, предоставляющая полный интерфейс разработки ботов
- Название адаптера: KookAdapter
- Поддержка нескольких аккаунтов: Поддерживает одновременную настройку нескольких ботов Kook
- Способ подключения: WebSocket-длинное подключение (через шлюз Kook)
- Способ аутентификации: Аутентификация по Bot Token
- Поддержка цепочечных модификаторов: Поддерживает цепочечные методы модификации, такие как `.Reply()`, `.At()`, `.AtAll()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Описание конфигурации

KookAdapter поддерживает настройку нескольких аккаунтов, каждый из которых соответствует отдельному боту Kook.

```toml
# config.toml
# Аккаунт 1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token (обязательно, формат: Bot xxx/xxx)
bot_id = ""                   # ID пользователя бота (необязательно, если не заполнено, будет извлечен из token)
compress = true               # Включить сжатие WebSocket (необязательно, по умолчанию true)
enabled = true                # Включить (необязательно, по умолчанию true)

# Аккаунт 2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> Совместимость со старой конфигурацией: если обнаружена старая одиночная конфигурация `[KookAdapter]` (с token), она автоматически будет перенесена в `accounts.default`.

**Описание параметров (для каждого аккаунта):**
- `token`: Token бота Kook (обязательно), получается из [разработческого центра Kook](https://developer.kookapp.cn), формат `Bot xxx/xxx`
- `bot_id`: ID пользователя бота (необязательно), если не заполнено, адаптер попытается автоматически извлечь из token. Рекомендуется вручную заполнить для обеспечения точности
- `compress`: Включить сжатие данных WebSocket (необязательно, по умолчанию `true`), при включении используется zlib для распаковки данных
- `enabled`: Включить этот аккаунт (необязательно, по умолчанию `true`)

**API-окружение:**
- Базовый адрес API Kook: `https://www.kookapp.cn/api/v3`
- WebSocket-шлюз получается динамически через API: `POST /gateway/index`

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`: Отправка обычного текстового сообщения.
- `.Image(file: bytes | str)`: Отправка сообщения с изображением, поддерживает пути к файлу, URL, двоичные данные.
- `.Video(file: bytes | str)`: Отправка сообщения с видео, поддерживает пути к файлу, URL, двоичные данные.
- `.File(file: bytes | str, filename: str = None)`: Отправка сообщения с файлом, поддерживает пути к файлу, URL, двоичные данные.
- `.Voice(file: bytes | str)`: Отправка сообщения с голосовым сообщением, поддерживает пути к файлу, URL, двоичные данные.
- `.Markdown(text: str)`: Отправка сообщения в формате KMarkdown.
- `.Card(card_data: dict)`: Отправка сообщения-карточки (CardMessage).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Отправка сообщения в формате OneBot12.

### Цепочечные модификаторы (можно комбинировать)

Цепочечные модификаторы возвращают `self`, поддерживают цепочечное использование, должны быть вызваны перед окончательным методом отправки:

- `.Reply(message_id: str)`: Ответить (цитировать) на указанное сообщение.
- `.At(user_id: str)`: Упомянуть определенного пользователя, можно вызывать несколько раз для упоминания нескольких пользователей.
- `.AtAll()`: Упомянуть всех.

### Примеры цепочечного вызова

```python
# Базовая отправка
await kook.Send.To("group", channel_id).Text("Hello")

# Ответ на сообщение
await kook.Send.To("group", channel_id).Reply(msg_id).Text("Ответ на сообщение")

# Упоминание пользователя
await kook.Send.To("group", channel_id).At("user_id").Text("Привет")

# Упоминание нескольких пользователей
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("Упоминание нескольких пользователей")

# Упоминание всех
await kook.Send.To("group", channel_id).AtAll().Text("Анонс")

# Комбинированный вызов
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("Сложное сообщение")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость между платформами:

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответ на сообщение"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Использование упоминаний и цитат в Raw_ob12
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
await kook.Send.To("group", channel_id).Edit(msg_id, "**Обновленное содержимое**")

# Удаление сообщения
await kook.Send.To("group", channel_id).Recall(msg_id)

# Загрузка файла (получение URL файла)
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно ожидать с помощью `await` для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата (код от API Kook)
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
| 40100 | Неверный или не предоставлен Token |
| 40101 | Token истек |
| 40102 | Token не соответствует боту |
| 40103 | Недостаточно прав |
| 40000 | Ошибка параметров |
| 40400 | Цель не существует |
| 40300 | Нет прав для операции |
| 50000 | Ошибка сервера |
| -1 | Ошибка внутри адаптера |

## Специфические типы событий

Необходимо использовать проверку `platform=="kook"` для использования специфических возможностей данной платформы

### Основные различия

1. **Система каналов**: Kook использует двухуровневую структуру серверов (Guild) и каналов (Channel), каналы являются основной целью отправки сообщений
2. **Типы сообщений**: Kook поддерживает различные типы сообщений, такие как текст (1), изображение (2), видео (3), файл (4), голосовое сообщение (8), KMarkdown (9), сообщение-карточка (10)
3. **Система личных сообщений**: Kook различает сообщения каналов и личные сообщения, используя разные API-эндпоинты
4. **Нумерация сообщений**: WebSocket Kook использует `sn` для обеспечения упорядоченности сообщений, поддерживает временное хранение и перестановку сообщений
5. **Редактирование и удаление сообщений**: Поддерживает редактирование отправленных сообщений (только KMarkdown и CardMessage) и удаление сообщений

### Расширенные поля

- Все специфические поля имеют префикс `kook_`
- Сохраняются исходные данные в поле `kook_raw`
- `kook_raw_type` указывает номер типа исходного сообщения Kook (например, `1` — текст, `255` — событие уведомления)

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
    {"type": "text", "data": {"text": "Разобранный текст"}}
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

### Типы сообщений

Типы сообщений Kook автоматически преобразуются в соответствующие типы сообщений в зависимости от поля `type`:

| Тип Kook | Преобразованный тип | Описание |
|---|---|---|
| 1 | `text` | Текстовое сообщение |
| 2 | `image` | Сообщение с изображением |
| 3 | `video` | Сообщение с видео |
| 4 | `file` | Сообщение с файлом |
| 8 | `record` | Голосовое сообщение |
| 9 | `text` | KMarkdown сообщение (извлекается чистый текст) |
| 10 | `json` | Сообщение-карточка (оригинальный JSON) |

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

Когда сообщение содержит упоминания, перед сообщением вставляется сообщение `mention`:

```json
{
  "type": "mention",
  "data": {
    "user_id": "ID пользователя, которого упомянули"
  }
}
```

### Сообщение упоминания всех (mention_all)

Когда сообщение является упоминанием всех, вставляется сообщение `mention_all`:

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket-соединение

### Процесс подключения

1. Используя Token бота, вызывается `POST /gateway/index` для получения адреса WebSocket-шлюза
2. Подключение к WebSocket-шлюзу
3. Получение сигнала HELLO (s=1), проверка статуса подключения
4. Начало цикла пингов (PING, s=2, каждые 30 секунд)
5. Получение событий сообщений (s=0), использование `sn` для обеспечения упорядоченности
6. Получение ответа на пинг PONG (s=3)

### Типы сигнала

| Сигнал | s-значение | Описание |
|------|-----|------|
| HELLO | 1 | Сигнал приветствия сервера, получается после успешного подключения |
| PING | 2 | Пинг клиента, отправляется каждые 30 секунд, содержит текущий `sn` |
| PONG | 3 | Ответ на пинг |
| RESUME | 4 | Сигнал возобновления подключения, содержит `sn` для восстановления сессии |
| RECONNECT | 5 | Сигнал от сервера для переподключения, необходимо заново получить шлюз |
| RESUME_ACK | 6 | Ответ на успешное возобновление |

### Переподключение при разрыве

- При неожиданном разрыве соединения адаптер автоматически пытается переподключиться
- Если ранее `sn > 0`, сначала будет попытка RESUME (s=4) для возобновления соединения
- При неудаче RESUME сбрасывается `sn` и очередь сообщений, и начинается новое подключение (процесс HELLO)
- При получении сигнала RECONNECT (s=5) состояние очищается и происходит переподключение

### Механизм нумерации сообщений

Kook WebSocket использует `sn` (последовательный номер) для обеспечения упорядоченности сообщений:

- При получении каждого сообщения (s=0) `sn` увеличивается
- Если получено сообщение с не последовательным `sn`, переходит в режим временного хранения
- Сообщения в буфере сортируются по `sn`, и обрабатываются в порядке поступления после получения недостающих сообщений
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
        print(f"Пользователь {user_id} удалил реакцию к сообщению {msg_id}")
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

### Отправка сообщений KMarkdown и карточек

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**Жирный** *курсив* [ссылка](https://example.com)")

# Сообщение-карточка
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

# Редактирование сообщения (поддерживается только KMarkdown и CardMessage)
await kook.Send.To("group", channel_id).Edit(msg_id, "**Обновленное содержимое**")

# Удаление сообщения
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### Обработка уведомлений об изменении и удалении личных сообщений

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