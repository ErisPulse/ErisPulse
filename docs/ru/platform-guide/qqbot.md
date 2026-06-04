# Документация по функциональным особенностям платформы QQBot

QQBotAdapter — это адаптер, построенный на протоколе QQBot (документация по QQ-роботам), который интегрирует все модули функций QQBot и предоставляет унифицированные интерфейсы для обработки событий и операций с сообщениями.

---

## Информация о документе

- Версия соответствующего модуля: 1.0.0
- Поддерживающий: ErisPulse

## Основная информация

- Описание платформы: QQBot — это интерфейс разработки роботов, предоставленный официальным QQ, поддерживающий групповые чаты, личные чаты, каналы и другие сценарии.
- Название адаптера: QQBotAdapter
- Режим подключения: WebSocket с поддержкой длинного соединения (через шлюз QQBot)
- Способ аутентификации: базируется на appId + clientSecret для получения access_token
- Поддержка цепочечных модификаторов: поддержка методов цепочки, таких как `.Reply()`, `.At()`, `.AtAll()`, `.Keyboard()` и т.д.
- Совместимость с OneBot12: поддержка отправки сообщений в формате OneBot12

## Описание конфигурации

```toml
# config.toml
[QQBot_Adapter]
appid = "YOUR_APPID"          # App ID QQ-робота (обязательно)
secret = "YOUR_CLIENT_SECRET"  # Секретный ключ клиента QQ-робота (обязательно)
sandbox = false                 # Использовать ли песочническую среду (необязательно, по умолчанию false)
intents = [1, 30, 25]          # биты подписываемых событий intents (необязательно)
gateway_url = "wss://api.sgroup.qq.com/websocket/"  # Адрес пользовательского шлюза (необязательно)
```

**Пояснения к конфигурационным параметрам:**
- `appid`：App ID QQ-робота (обязательно), получено с платформы QQ Open.
- `secret`：Секретный ключ клиента QQ-робота (обязательно), получено с платформы QQ Open.
- `sandbox`：Использовать ли песочническую среду, адрес API песочнической среды — `https://sandbox.api.sgroup.qq.com`.
- `intents`：Список подписок на события intents, каждое значение сдвигается влево и выполняется побитовое ИЛИ.
  - `1`：События, связанные с каналами.
  - `25`：События сообщений в каналах.
  - `30`：События сообщений с упоминанием в группе.
- `gateway_url`：Адрес WebSocket шлюза, по умолчанию `wss://api.sgroup.qq.com/websocket/`.

**Среда API:**
- Официальная среда: `https://api.sgroup.qq.com`
- Песочническая среда: `https://sandbox.api.sgroup.qq.com`

## Поддерживаемые типы сообщений для отправки

Все методы отправки реализованы с помощью цепочечного синтаксиса, например:

```python
from ErisPulse.Core import adapter
qqbot = adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`: Отправка сообщения только с текстом.
- `.Image(file: bytes | str)`: Отправка сообщения с изображением, поддерживаются путь к файлу, URL и двоичные данные.
- `.Markdown(content: str)`: Отправка сообщения в формате Markdown.
- `.Ark(template_id: int, kv: list)`: Отправка шаблонного сообщения Ark.
- `.Embed(embed_data: dict)`: Отправка сообщения Embed.
- `.Raw_ob12(message: List[Dict], **kwargs)`: Отправка сообщения в формате OneBot12.

### Методы цепочечных модификаторов (можно комбинировать)

Методы цепочечных модификаторов возвращают `self`, поддерживают цепной вызов и должны вызываться перед финальным методом отправки:

- `.Reply(message_id: str)`: Ответ на указанное сообщение.
- `.At(user_id: str)`: Упоминание указанного пользователя (вставляет содержимое в формате `<@user_id>`).
- `.AtAll()`: Упоминание всех участников (вставляет текст `@所有人`).
- `.Keyboard(keyboard: dict)`: Добавление кнопок клавиатуры.

### Примеры цепочного вызова

```python
# Базовая отправка
await qqbot.Send.To("user", user_openid).Text("Hello")

# Ответ на сообщение
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("Ответное сообщение")

# Ответ + кнопки
await qqbot.Send.To("group", group_openid).Reply(msg_id).Keyboard(keyboard).Text("Сообщение с ответом и клавиатурой")

# Упоминание пользователя
await qqbot.Send.To("group", group_openid).At("member_openid").Text("Привет")

# Комбинированное использование
await qqbot.Send.To("group", group_openid).Reply(msg_id).At("member_openid").Keyboard(keyboard).Text("Сложное сообщение")
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12 для удобства кроссплатформенной совместимости сообщений:

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await qqbot.Send.To("user", user_openid).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await qqbot.Send.To("group", group_openid).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно напрямую await для получения результата отправки. Результаты возврата следуют стандартным правилам возврата адаптеров ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения: "ok" или "failed"
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "message_id": "123456",   // ID сообщения
    "message": "",            // Информация об ошибке
    "qqbot_raw": {...}        // Данные исходного ответа
}
```

### Пояснение кодов ошибок

| retcode | Описание |
|---------|------|
| 0 | Успех |
| 10003 | Не удается определить цель отправки |
| 32000 | Тайм-аут запроса |
| 33000 | Аномалия вызова API |
| 34000 | API вернул неожиданный формат или бизнес-ошибку |

## Уникальные типы событий

Требуется проверка `platform=="qqbot"` перед использованием функций этой платформы

### Ключевые различия

1. **Система OpenID**: QQBot использует OpenID вместо QQ-номеров, идентификаторы как пользователей, так и групп являются строками OpenID.
2. **Обязательное упоминание в группах**: Сообщения в группах принимаются только тогда, когда пользователь упоминает бота (`GROUP_AT_MESSAGE_CREATE`).
3. **Система каналов**: QQBot поддерживает сообщения и события для каналов (Guild) и подканалов (Channel).
4. **Проверка сообщений**: Отправляемые сообщения могут потребовать проверки, результаты передаются через события `qqbot_audit_pass`/`qqbot_audit_reject`.
5. **Реактивный ответ**: Сообщения в группах и личные сообщения поддерживают механизм реактивного ответа, при отправке необходимо указать `msg_id`.

### Расширенные поля

- Все уникальные поля идентифицируются префиксом `qqbot_`
- Исходные данные сохраняются в поле `qqbot_raw`
- `qqbot_raw_type` идентифицирует исходный тип события QQBot (например, `C2C_MESSAGE_CREATE`)
- Данные вложений сохраняются в поле `qqbot_attachment` с исходной информацией о вложении

### Примеры особых полей

```python
# Упоминание в группе
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
  "message_id": "ID удаляемого сообщения",
  "operator_id": "ID оператора"
}

# Реакция на эмодзи
{
  "type": "notice",
  "detail_type": "qqbot_reaction_add",
  "qqbot_raw": {
    "...": "Исходные данные"
  }
}
```

### Сегменты сообщений канала

Сообщения каналов поддерживают поле `mentions`, которое после преобразования представляется в виде сегмента сообщения `mention`:

```json
{
  "type": "mention",
  "data": {
    "user_id": "ID упомянутого пользователя",
    "user_name": "Ник упомянутого пользователя"
  }
}
```

### Сегменты вложений

Вложения QQBot автоматически преобразуются в соответствующие сегменты сообщений в зависимости от `content_type`:

| Префикс content_type | Тип преобразования | Описание |
|---|---|---|
| `image` | `image` | Сообщение с изображением |
| `video` | `video` | Сообщение с видео |
| `audio` | `voice` | Сообщение со звуком |
| Другое | `file` | Сообщение с файлом |

Структура сегмента вложения:
```json
{
  "type": "image",
  "data": {
    "url": "URL вложения",
    "qqbot_attachment": {
      "content_type": "image/png",
      "url": "URL исходного вложения"
    }
  }
}
```

## Подключение WebSocket

### Процесс подключения

1. Используйте appId + clientSecret для получения access_token.
2. Подключитесь к WebSocket шлюзу.
3. Получите сообщение OP_HELLO (op=10) и определите интервал сердцебиения.
4. Отправьте OP_IDENTIFY (op=2) для аутентификации.
5. Получите событие READY, чтобы получить session_id и bot_id.
6. Начните цикл сердцебиения (OP_HEARTBEAT, op=1).
7. Принимайте события и распределяйте их (OP_DISPATCH, op=0).

### Повторное подключение при обрыве

- Поддерживается автоматическое повторное подключение, максимальное количество попыток — 50.
- Время ожидания при повторном подключении использует экспоненциальный алгоритм задержки: `min(5 * 2^min(count, 6), 300)` секунд.
- Поддерживается восстановление сессии (OP_RESUME, op=6), для восстановления используются session_id + seq.
- Автоматическое триггерирование повторного подключения при получении OP_RECONNECT (op=7) или OP_INVALID_SESSION (op=9).

### Обновление токена

- Срок действия access_token обычно составляет 7200 секунд.
- Адаптер автоматически обновляет токен каждые 7080 секунд (7200-120).
- Интерфейс обновления: `POST https://bots.qq.com/app/getAppAccessToken`

## Подписка на события (Intents)

Значения intents объединяются с помощью побитовой операции:

```python
intents = [1, 30, 25]
value = 0
for intent in intents:
    value |= (1 << intent)
```

Часто используемые биты намерений:
| Значение intent | Описание |
|----------|------|
| 1 | События, связанные с каналами (GUILD_CREATE и т.д.) |
| 25 | События сообщений в каналах (AT_MESSAGE_CREATE и т.д.) |
| 30 | События сообщений с упоминанием в группе (GROUP_AT_MESSAGE_CREATE и т.д.) |

## Примеры использования

### Обработка сообщений в группе

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

### Отправка мультимедийных сообщений

```python
# Отправка изображения (URL)
await qqbot.Send.To("group", group_openid).Image("https://example.com/image.png")

# Отправка изображения (двоичные данные)
with open("image.png", "rb") as f:
    image_bytes = f.read()
await qqbot.Send.To("user", user_openid).Image(image_bytes)
```

### Мониторинг результатов проверки сообщений

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
        print(f"Сообщение отклонено при проверке: {reason}")