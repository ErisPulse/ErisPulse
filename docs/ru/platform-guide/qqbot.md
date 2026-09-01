# Документация по функциональным возможностям платформы QQBot

QQBotAdapter — это адаптер, построенный на основе протокола QQBot (документация по QQ-ботам), объединяющий все функциональные модули QQBot и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Соответствующая версия модуля: 1.0.0
- Поддержка: ErisPulse

## Основная информация

- Описание платформы: QQBot — это официальный интерфейс разработки для ботов QQ, поддерживающий различные сценарии, такие как групповые чаты, личные сообщения и каналы.
- Название адаптера: QQBotAdapter
- Способ подключения: WebSocket-соединение (через шлюз QQBot)
- Способ аутентификации: получение access_token на основе appId + clientSecret
- Поддержка цепочки модификаторов: поддержка цепочки методов модификаторов, таких как `.Reply()`, `.At()`, `.AtAll()`, `.Keyboard()`
- Совместимость с OneBot12: поддержка отправки сообщений в формате OneBot12

## Конфигурация

```toml
# config.toml
[QQBot_Adapter]
appid = "YOUR_APPID"          # ID приложения QQ-бота (обязательно)
secret = "YOUR_CLIENT_SECRET"  # Ключ клиента QQ-бота (обязательно)
sandbox = false                 # Использовать ли песочницу (опционально, по умолчанию false)
intents = [1, 30, 25]          # Список подписанных событий intents (опционально)
gateway_url = "wss://api.sgroup.qq.com/websocket/"  # Адрес вебсокет-шлюза (опционально)
```

**Описание параметров:**
- `appid`: ID приложения QQ-бота (обязательно), получается на платформе открытых API QQ
- `secret`: Ключ клиента QQ-бота (обязательно), получается на платформе открытых API QQ
- `sandbox`: Использовать ли песочницу, адрес API песочницы: `https://sandbox.api.sgroup.qq.com`
- `intents`: Список подписанных событий intents, каждое значение сдвигается влево и объединяется по битам
  - `1`: События, связанные с каналом
  - `25`: События сообщений канала
  - `30`: События упоминания в группе
- `gateway_url`: Адрес вебсокет-шлюза, по умолчанию `wss://api.sgroup.qq.com/websocket/`

**Среда API:**
- Официальная среда: `https://api.sgroup.qq.com`
- Песочная среда: `https://sandbox.api.sgroup.qq.com`

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:
```python
from ErisPulse.Core import adapter
qqbot = adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка обычного текстового сообщения.
- `.Image(file: bytes | str)` — отправка сообщения с изображением, поддерживает пути к файлам, URL и двоичные данные.
- `.Markdown(content: str)` — отправка сообщения в формате Markdown.
- `.Ark(template_id: int, kv: list)` — отправка сообщения с использованием шаблона Ark.
- `.Embed(embed_data: dict)` — отправка встраиваемого сообщения (Embed).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

### Модификаторы цепочки (можно комбинировать)

Модификаторы цепочки возвращают `self`, поддерживают цепочечные вызовы и должны использоваться до окончательного отправки:

- `.Reply(message_id: str)` — ответ на указанное сообщение.
- `.At(user_id: str)` — упоминание пользователя (вставляет текст `<@user_id>`).
- `.AtAll()` — упоминание всех участников (вставляет текст `@всех`).
- `.Keyboard(keyboard: dict)` — добавление кнопок клавиатуры.

### Примеры цепочечных вызовов

```python
# Базовая отправка
await qqbot.Send.To("user", user_openid).Text("Hello")

# Ответ на сообщение
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("Ответ на сообщение")

# Ответ + кнопки
await qqbot.Send.To("group", group_openid).Reply(msg_id).Keyboard(keyboard).Text("Сообщение с ответом и клавиатурой")

# Упоминание пользователя
await qqbot.Send.To("group", group_openid).At("member_openid").Text("Привет")

# Комбинированный вызов
await qqbot.Send.To("group", group_openid).Reply(msg_id).At("member_openid").Keyboard(keyboard).Text("Составное сообщение")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12 для обеспечения совместимости между платформами:

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await qqbot.Send.To("user", user_openid).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответ на сообщение"}}]
await qqbot.Send.To("group", group_openid).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно напрямую ожидать для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату ответа адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "message_id": "123456",   // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "qqbot_raw": {...}        // Исходные данные ответа
}
```

### Описание кодов ошибок

| retcode | Описание |
|---------|----------|
| 0 | Успешно |
| 10003 | Невозможно определить цель отправки |
| 32000 | Время ожидания запроса истекло |
| 33000 | Ошибка вызова API |
| 34000 | API вернул неожиданный формат или произошла бизнес-ошибка |

## Типы событий, специфичные для QQBot

Необходимо проверять `platform=="qqbot"`, чтобы использовать особенности данной платформы

### Основные отличия

1. **Система openid**: QQBot использует openid вместо номера QQ, идентификаторы пользователей и групп — это строки openid
2. **Сообщения в группе должны содержать упоминание (@)**: В группе сообщения будут получены только в том случае, если пользователь упомянет бота (событие `GROUP_AT_MESSAGE_CREATE`)
3. **Система каналов**: QQBot поддерживает сообщения и события в каналах (Guild) и подканалах (Channel)
4. **Проверка сообщений**: Отправленные сообщения могут требовать проверки, результат будет уведомлен через события `qqbot_audit_pass`/`qqbot_audit_reject`
5. **Пассивный ответ**: Поддерживается механизм пассивного ответа на сообщения в группе и личные сообщения, при отправке необходимо указывать `msg_id`

### Расширенные поля

- Все специфичные поля имеют префикс `qqbot_`
- Сохраненные исходные данные находятся в поле `qqbot_raw`
- `qqbot_raw_type` указывает тип исходного события QQBot (например, `C2C_MESSAGE_CREATE`)
- Информация об вложениях сохраняется в поле `qqbot_attachment`

### Примеры специальных полей

```python
# Сообщение @ в группе
{
  "type": "message",
  "detail_type": "group",
  "user_id": "MEMBER_OPENID",
  "group_id": "GROUP_OPENID",
  "qqbot_group_openid": "GROUP_OPENID",
  "qqbot_member_openid": "MEMBER_OPENID",
  "qqbot_event_id": "ID события сообщения",
  "qqbot_reply_token": "Токен ответа"
}

# Личное сообщение
{
  "type": "message",
  "detail_type": "private",
  "user_id": "USER_OPENID",
  "qqbot_openid": "USER_OPENID",
  "qqbot_event_id": "ID события сообщения",
  "qqbot_reply_token": "Токен ответа"
}

# Событие взаимодействия
{
  "type": "notice",
  "detail_type": "qqbot_interaction",
  "qqbot_interaction_id": "ID взаимодействия",
  "qqbot_interaction_type": "Тип взаимодействия",
  "qqbot_interaction_data": {
    "...": "Данные взаимодействия"
  }
}

# Проверка сообщения
{
  "type": "notice",
  "detail_type": "qqbot_audit_pass",
  "qqbot_audit_id": "ID проверки",
  "qqbot_message_id": "ID сообщения"
}

# Удаление сообщения
{
  "type": "notice",
  "detail_type": "qqbot_message_delete",
  "message_id": "ID удаленного сообщения",
  "operator_id": "ID оператора"
}

# Ответ эмоциональным символом
{
  "type": "notice",
  "detail_type": "qqbot_reaction_add",
  "qqbot_raw": {
    "...": "Исходные данные"
  }
}
```

### Сообщения в каналах

Сообщения в каналах поддерживают поле `mentions`, которое преобразуется в сообщение типа `mention`:

```json
{
  "type": "mention",
  "data": {
    "user_id": "ID упомянутого пользователя",
    "user_name": "Никнейм упомянутого пользователя"
  }
}
```

### Сообщения с вложениями

Вложения в QQBot автоматически преобразуются в соответствующие типы сообщений в зависимости от `content_type`:

| Префикс content_type | Тип преобразования | Описание |
|---|---|---|
| `image` | `image` | Сообщение с изображением |
| `video` | `video` | Сообщение с видео |
| `audio` | `voice` | Голосовое сообщение |
| Другое | `file` | Сообщение с файлом |

Структура сообщения с вложениями:
```json
{
  "type": "image",
  "data": {
    "url": "URL вложения",
    "qqbot_attachment": {
      "content_type": "image/png",
      "url": "Исходный URL вложения"
    }
  }
}
```

## WebSocket соединение

### Процесс подключения

1. Получите access_token с помощью appId + clientSecret
2. Подключитесь к WebSocket-шлюзу
3. Получите сообщение OP_HELLO (op=10) и узнайте интервал для опроса
4. Отправьте OP_IDENTIFY (op=2) для аутентификации
5. Получите событие READY и узнайте session_id и bot_id
6. Начните цикл опроса (OP_HEARTBEAT, op=1)
7. Получайте события (OP_DISPATCH, op=0)

### Автоматическое повторное подключение при разрыве соединения

- Поддерживается автоматическое повторное подключение, максимальное количество попыток — 50
- Время ожидания повторного подключения рассчитывается по алгоритму экспоненциального отступления: `min(5 * 2^min(count, 6), 300)` секунд
- Поддерживается восстановление сессии (OP_RESUME, op=6), с использованием session_id и seq
- При получении OP_RECONNECT (op=7) или OP_INVALID_SESSION (op=9) автоматически запускается повторное подключение

### Обновление токена

- Срок действия access_token обычно составляет 7200 секунд
- Адаптер автоматически обновляет токен каждые 7080 секунд (7200-120)
- Интерфейс обновления: `POST https://bots.qq.com/app/getAppAccessToken`

## События подписки (Intents)

Значения intents объединяются с помощью побитовой операции:

```python
intents = [1, 30, 25]
value = 0
for intent in intents:
    value |= (1 << intent)
```

Часто используемые значения intent:
| intent | Описание |
|--------|----------|
| 1 | События, связанные с каналами (GUILD_CREATE и т.д.) |
| 25 | События сообщений в канале (AT_MESSAGE_CREATE и т.д.) |
| 30 | События упоминания в группе (GROUP_AT_MESSAGE_CREATE и т.д.) |

## Примеры использования

### Обработка групповых сообщений

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

qqbot = sdk.adapter.get("qqbot")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    group_id = event.get("group_id")

    if text == "hello":
        await qqbot.Send.To("group", group_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### Обработка событий взаимодействия

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return

    if event.get("detail_type") == "qqbot_interaction":
        interaction_id = event.get("qqbot_interaction_id", "")
        interaction_data = event.get("qqbot_interaction_data", {})
        # Обработка взаимодействия...
```

### Отправка медиа-сообщений

```python
# Отправка изображения (по URL)
await qqbot.Send.To("group", group_openid).Image("https://example.com/image.png")

# Отправка изображения (по байтам)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await qqbot.Send.To("user", user_openid).Image(image_bytes)
```

### Наблюдение за результатами проверки сообщений

```python
@notice.on_notice()
async def handle_audit(event):
    if event.get("platform") != "qqbot":
        return

    detail_type = event.get("detail_type")

    if detail_type == "qqbot_audit_pass":
        msg_id = event.get("qqbot_message_id")
        print(f"Сообщение прошло проверку: {msg_id}")

    elif detail_type == "qqbot_audit_reject":
        reason = event.get("qqbot_audit_reject_reason", "")
        print(f"Сообщение отклонено: {reason}")
```