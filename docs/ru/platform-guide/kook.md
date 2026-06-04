# Документация по функциям платформы Kook

KookAdapter — это адаптер, основанный на WebSocket-протоколе бота Kook (Kaihei La). Он интегрирует все модули функций Kook, предоставляя унифицированные интерфейсы обработки событий и управления сообщениями.

---

## Информация о документации

- Версия соответствующего модуля: 0.1.0
- Ответственный: ShanFish

## Основная информация

- Описание платформы: Kook (ранее Kaihei La) — это сообщество с поддержкой текстовой, голосовой и видеосвязи, предоставляющее полный набор интерфейсов для разработки ботов.
- Название адаптера: KookAdapter
- Способ подключения: Долгое WebSocket-соединение (через Kook Gateway)
- Способ аутентификации: На основе токена бота (Bot Token)
- Поддержка цепочечных модификаторов: Поддержка цепных методов модификации, таких как `.Reply()`, `.At()`, `.AtAll()`
- Совместимость с OneBot12: Поддержка отправки сообщений в формате OneBot12

## Описание конфигурации

```toml
# config.toml
[KookAdapter]
token = "YOUR_BOT_TOKEN"     # Токен бота Kook (обязательное поле, формат: Bot xxx/xxx)
bot_id = ""                   # Идентификатор пользователя бота (необязательное поле, если не указано, будет из токена)
compress = true               # Включить ли сжатие WebSocket (необязательное поле, по умолчанию true)
```

**Описание параметров конфигурации:**
- `token`: Токен бота Kook (обязательное поле), полученный на [Центре разработчиков Kook](https://developer.kookapp.cn), формат `Bot xxx/xxx`
- `bot_id`: Идентификатор пользователя бота (необязательное поле). Если не заполнено, адаптер попытается автоматически разрешить из токена. Рекомендуется указать вручную для точности
- `compress`: Включать ли сжатие данных WebSocket (необязательное поле, по умолчанию `true`). После включения данные распаковываются с помощью zlib

**Окружение API:**
- Базовый адрес API Kook: `https://www.kookapp.cn/api/v3`
- WebSocket Gateway динамически получается через API: `POST /gateway/index`

## Поддерживаемые типы сообщений для отправки

Все методы отправки реализованы через цепочечный синтаксис, например:

```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:

- `.Text(text: str)`: Отправить текстовое сообщение.
- `.Image(file: bytes | str)`: Отправить изображение, поддерживает путь к файлу, URL, двоичные данные.
- `.Video(file: bytes | str)`: Отправить видео, поддерживает путь к файлу, URL, двоичные данные.
- `.File(file: bytes | str, filename: str = None)`: Отправить файл, поддерживает путь к файлу, URL, двоичные данные.
- `.Voice(file: bytes | str)`: Отправить голосовое сообщение, поддерживает путь к файлу, URL, двоичные данные.
- `.Markdown(text: str)`: Отправить сообщение в формате KMarkdown.
- `.Card(card_data: dict)`: Отправить карточное сообщение (CardMessage).
- `.Raw_ob12(message: List[Dict], **kwargs)`: Отправить сообщение в формате OneBot12.

### Методы цепочечного модификатора (комбинируются)

Методы цепочечного модификатора возвращают `self`, поддерживают цепной вызов, должны вызываться перед финальным методом отправки:

- `.Reply(message_id: str)`: Ответить (цитировать) на указанное сообщение.
- `.At(user_id: str)`: Упомянуть указанного пользователя, можно вызвать несколько раз для упоминания нескольких пользователей.
- `.AtAll()`: Упомянуть всех.

### Примеры цепного вызова

```python
# Базовая отправка
await kook.Send.To("group", channel_id).Text("Hello")

# Ответ на сообщение
await kook.Send.To("group", channel_id).Reply(msg_id).Text("回复消息")

# Упоминание пользователя
await kook.Send.To("group", channel_id).At("user_id").Text("你好")

# Упоминание нескольких пользователей
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("多用户@")

# Упоминание всех
await kook.Send.To("group", channel_id).AtAll().Text("公告")

# Комбинированное использование
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("复合消息")
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12 для удобства межплатформенной совместимости:

```python
# Отправить сообщение в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Использование сегментов mention и reply в Raw_ob12
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### Дополнительные методы операций

Помимо отправки сообщений, адаптер Kook также поддерживает следующие операции:

```python
# Редактирование сообщения (поддерживается только KMarkdown type=9 и CardMessage type=10)
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新后的内容**")

# Отмена отправки сообщения
await kook.Send.To("group", channel_id).Recall(msg_id)

# Загрузка файла (получение URL файла)
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можноAwait напрямую для получения результата отправки. Формат возвращаемых значений следует нормализация ErisPulse адаптера:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата (код Kook API)
    "data": {...},            // Данные ответа
    "message_id": "xxx",      // Идентификатор сообщения
    "message": "",            // Информация об ошибке
    "kook_raw": {...}         // Исходные данные ответа
}
```

### Описание кодов ошибок

| retcode | Описание |
|---------|------|
| 0 | Успех |
| 40100 | Неверный токен или не предоставлен |
| 40101 | Срок действия токена истек |
| 40102 | Токен не соответствует боту |
| 40103 | Отсутствуют права |
| 40000 | Ошибка параметров |
| 40400 | Цель не существует |
| 40300 | Нет прав на выполнение операции |
| 50000 | Внутренняя ошибка сервера |
| -1 | Внутренняя ошибка адаптера |

## Специфические типы событий

Необходимо проверить `platform=="kook"`, прежде чем использовать возможности этой платформы

### Ключевые отличия

1.  **Система каналов**: Kook использует двухуровневую структуру с серверами (Guild) и каналами (Channel), канал является основной целью отправки сообщений
2.  **Типы сообщений**: Kook поддерживает различные типы сообщений: текст (1), изображение (2), видео (3), файл (4), голос (8), KMarkdown (9), карточное сообщение (10)
3.  **Система личных сообщений**: Kook различает сообщения каналов и личные сообщения, используя разные API-конечные точки
4.  **Порядковые номера сообщений**: Kook WebSocket использует порядковые номера `sn` для обеспечения порядка сообщений, поддерживает буферизацию сообщений и повторную сортировку при нарушении порядка
5.  **Редактирование и отмена отправки сообщений**: Поддержка редактирования отправленных сообщений (только KMarkdown и CardMessage) и отмены отправки

### Расширенные поля

- Все специфические поля обозначены префиксом `kook_`
- Исходные данные сохраняются в поле `kook_raw`
- `kook_raw_type` указывает исходный номер типа сообщения Kook (например, `1` для текста, `255` для уведомлений)

### Примеры специальных полей

```python
# Текстовое сообщение в канале
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用户ID",
  "group_id": "频道ID",
  "channel_id": "频道ID",
  "message_id": "消息ID",
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
  "user_id": "用户ID",
  "group_id": "频道ID",
  "channel_id": "频道ID",
  "message_id": "消息ID",
  "kook_raw": {...},
  "kook_raw_type": "2",
  "message": [
    {"type": "image", "data": {"file": "图片URL", "url": "图片URL"}}
  ],
  "alt_message": "图片内容"
}

# Сообщение KMarkdown
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用户ID",
  "group_id": "频道ID",
  "message_id": "消息ID",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "解析后的纯文本"}}
  ]
}

# Карточное сообщение
{
  "type": "message",
  "detail_type": "group",
  "user_id": "用户ID",
  "group_id": "频道ID",
  "message_id": "消息ID",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "卡片JSON内容"}}
  ]
}

# Личное сообщение
{
  "type": "message",
  "detail_type": "private",
  "user_id": "用户ID",
  "message_id": "消息ID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "私聊内容"}}
  ]
}
```

### Типы сегментов сообщений

Типы сообщений Kook автоматически преобразуются в соответствующие сегменты сообщений на основе поля `type`:

| Тип Kook | Тип конверсии | Описание |
|---|---|---|
| 1 | `text` | Текстовое сообщение |
| 2 | `image` | Изображение |
| 3 | `video` | Видеосообщение |
| 4 | `file` | Файл |
| 8 | `record` | Голосовое сообщение |
| 9 | `text` | Сообщение KMarkdown (извлечение чистого текста) |
| 10 | `json` | Карточное сообщение (исходный JSON) |

Пример структуры сегмента сообщения:

```json
{
  "type": "image",
  "data": {
    "file": "图片URL",
    "url": "图片URL"
  }
}
```

### Сегмент mention

Когда сообщение содержит @-информацию, сегмент `mention` вставляется перед сегментом сообщения:

```json
{
  "type": "mention",
  "data": {
    "user_id": "被@用户ID"
  }
}
```

### Сегмент mention_all

Когда сообщение предназначено для упоминания всех, вставляется сегмент `mention_all`:

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket-соединение

### Процесс подключения

1.  Вызвать `POST /gateway/index` с токеном бота, чтобы получить адрес WebSocket Gateway
2.  Подключиться к WebSocket Gateway
3.  Получить сигнал HELLO (s=1) и проверить состояние соединения
4.  Начать цикл проверки связи (PING, s=2, каждые 30 секунд)
5.  Принять событие сообщения (s=0), использовать порядковый номер sn для обеспечения порядка
6.  Получить ответ PONG (s=3) на проверку связи

### Типы сигналов

| Сигнал | Значение s | Описание |
|------|-----|------|
| HELLO | 1 | Сигнал приветствия от сервера, получается после успешного подключения |
| PING | 2 | Проверка связи клиента, отправляется каждые 30 секунд, содержит текущий sn |
| PONG | 3 | Ответ на проверку связи |
| RESUME | 4 | Сигнал возобновления соединения, содержит sn для восстановления сессии |
| RECONNECT | 5 | Сервер требует переподключения, необходимо получить шлюз заново |
| RESUME_ACK | 6 | Ответ об успешном RESUME |

### Переподключение после разрыва соединения

- После внезапного разрыва соединения адаптер автоматически пытается переподключиться
- Если ранее было `sn > 0`, сначала пытается восстановить соединение через RESUME (s=4)
- После неудачи RESUME сбрасывает sn и очередь сообщений и начинает новое подключение (процесс HELLO)
- При получении сигнала RECONNECT (s=5) очищает состояние и переподключается

### Механизм порядковых номеров сообщений

Kook WebSocket использует `sn` (увеличивающийся порядковый номер) для обеспечения порядка сообщений:

- При получении каждого события сообщения (s=0), sn увеличивается
- Если полученное сообщение sn не является непрерывным, переходит в режим буферизации
- Сообщения в буфере сортируются по sn и обрабатываются по порядку после прибытия недостающих сообщений
- После очистки буфера автоматически выходит из режима буферизации

## Примеры использования

### Обработка сообщений каналов

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

    await kook.Send.To("user", user_id).Text(f"你说了: {text}")
```

### Обработка уведомлений событий (эмоции и т.д.)

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
        print(f"用户 {user_id} 对消息 {msg_id} 添加了表情回应")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"用户 {user_id} 移除了消息 {msg_id} 的表情回应")
```

### Отправка медиа-сообщений

```python
# Отправка изображения (URL)
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# Отправка изображения (двоичные данные)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)