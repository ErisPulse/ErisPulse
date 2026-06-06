# Руководство по реализации конвертера событий

Конвертер событий (Converter) является одним из ключевых компонентов адаптера, отвечающим за преобразование нативных событий платформы в унифицированный стандартный формат событий OneBot12.

## Обязанности конвертера

```
Событие нативной платформы ──→ Converter.convert() ──→ Стандартное событие OneBot12
```

Конвертер отвечает только за **прямое преобразование** (направление получения), то есть преобразование сырых данных событий нативной платформы в стандартный формат OneBot12. Обратное преобразование (направление отправки) обрабатывается методом `Send.Raw_ob12()`.

### Основные принципы

1.  **Без потерь (Lossless conversion)**: Исходные данные должны быть полностью сохранены в поле `{platform}_raw`.
2.  **Совместимость со стандартом (Standard compatibility)**: Преобразованное событие должно соответствовать стандартному формату OneBot12.
3.  **Расширение платформы (Platform extension)**: Данные, уникальные для платформы, должны храниться в полях с префиксом `{platform}_`.

## Метод convert()

### Сигнатура метода

```python
def convert(self, raw_event: dict) -> dict:
    """
    Преобразует событие нативной платформы в стандартный формат OneBot12

    :param raw_event: Данные события нативной платформы
    :return: Словарь события в стандартном формате OneBot12
    """
    pass
```

### Структура возвращаемого значения

Преобразованный словарь события должен содержать следующие стандартные поля:

```python
{
    "id": "Уникальный идентификатор события",
    "time": 1234567890,           # Unix timestamp (seconds)
    "type": "message",             # Тип события
    "detail_type": "private",      # Детальный тип
    "platform": "myplatform",      # Имя платформы
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # Поля события сообщения
    "user_id": "sender_id",
    "message": [...],              # Список сегментов сообщений OneBot12
    "alt_message": "Текстовое содержимое",

    # Исходные данные должны быть сохранены
    "myplatform_raw": { ... },     # Полные данные события нативной платформы
    "myplatform_raw_type": "Имя типа нативного события",
}
```

## Соответствие обязательных полей

### Общие поля (для всех типов событий)

| Поле OB12 | Тип | Описание |
|-----------|------|------|
| `id` | str | Уникальный идентификатор события |
| `time` | int | Unix timestamp (seconds) |
| `type` | str | Тип события: `message` / `notice` / `request` / `meta` |
| `detail_type` | str | Детальный тип: `private` / `group` / `friend` и др. |
| `platform` | str | Имя платформы, должно совпадать с именем, указанным при регистрации адаптера |
| `self` | dict | Информация о боте: `{"platform": "...", "user_id": "..."}` |

### Дополнительные поля события сообщения

| Поле OB12 | Тип | Описание |
|-----------|------|------|
| `user_id` | str | ID отправителя |
| `message` | list[dict] | Список сегментов сообщений OneBot12 |
| `alt_message` | str | Резервное текстовое содержимое |

### Дополнительные поля уведомлений

| Поле OB12 | Тип | Описание |
|-----------|------|------|
| `user_id` | str | ID связанного пользователя |
| `operator_id` | str | ID оператора (например, при изменении состава группы) |

## Преобразование сегментов сообщений

Стандарт OneBot12 определяет следующие типы сегментов сообщений:

```python
# Text
{"type": "text", "data": {"text": "Hello"}}

# Image
{"type": "image", "data": {"file": "https://example.com/img.jpg"}}

# Audio
{"type": "audio", "data": {"file": "https://example.com/audio.mp3"}}

# Video
{"type": "video", "data": {"file": "https://example.com/video.mp4"}}

# File
{"type": "file", "data": {"file": "https://example.com/doc.pdf"}}

# @mention
{"type": "mention", "data": {"user_id": "123"}}

# @everyone
{"type": "mention_all", "data": {}}

# Reply
{"type": "reply", "data": {"message_id": "msg_123"}}
```

Если платформа поддерживает сегменты сообщений, которых нет в стандарте OneBot12, их можно опустить или преобразовать в наиболее близкий стандартный тип.

## Расширенные поля платформы

Данные, специфичные для платформы, должны храниться с использованием префикса `{platform}_`, чтобы избежать конфликтов со стандартными полями:

```python
{
    # Стандартные поля
    "type": "message",
    "detail_type": "group",
    # ...

    # Расширенные поля платформы
    "myplatform_raw": { ... },          # Данные события (обязательно)
    "myplatform_raw_type": "chat",      # Тип события (обязательно)

    # Другие поля, специфичные для платформы
    "myplatform_group_name": "Название группы",
    "myplatform_sender_role": "admin",
}
```

> **Важно**: Поле `{platform}_raw` является обязательным. Система событий и модули ErisPulse могут полагаться на него для доступа к исходным данным платформы.

## Полный пример

Ниже приведен полный пример реализации конвертера:

```python
class MyConverter:
    def __init__(self, platform: str):
        self.platform = platform

    def convert(self, raw_event: dict) -> dict:
        event_type = raw_event.get("type", "")

        base_event = {
            "id": raw_event.get("id", ""),
            "time": raw_event.get("timestamp", 0),
            "platform": self.platform,
            "self": {
                "platform": self.platform,
                "user_id": raw_event.get("self_id", ""),
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": event_type,
        }

        if event_type == "chat":
            return self._convert_message(raw_event, base_event)
        elif event_type == "notification":
            return self._convert_notice(raw_event, base_event)
        elif event_type == "request":
            return self._convert_request(raw_event, base_event)

        return base_event

    def _convert_message(self, raw: dict, base: dict) -> dict:
        base["type"] = "message"
        base["detail_type"] = "group" if raw.get("group_id") else "private"
        base["user_id"] = raw.get("sender_id", "")
        base["message"] = self._convert_message_segments(raw.get("content", ""))
        base["alt_message"] = raw.get("content", "")

        if raw.get("group_id"):
            base["group_id"] = raw["group_id"]

        return base

    def _convert_message_segments(self, content: str) -> list:
        segments = []
        if content:
            segments.append({"type": "text", "data": {"text": content}})
        return segments

    def _convert_notice(self, raw: dict, base: dict) -> dict:
        base["type"] = "notice"
        notification_type = raw.get("notification_type", "")

        if notification_type == "member_join":
            base["detail_type"] = "group_member_increase"
            base["user_id"] = raw.get("user_id", "")
            base["group_id"] = raw.get("group_id", "")
            base["operator_id"] = raw.get("operator_id", "")
        elif notification_type == "friend_add":
            base["detail_type"] = "friend_increase"
            base["user_id"] = raw.get("user_id", "")

        return base

    def _convert_request(self, raw: dict, base: dict) -> dict:
        base["type"] = "request"
        request_type = raw.get("request_type", "")

        if request_type == "friend":
            base["detail_type"] = "friend"
            base["user_id"] = raw.get("user_id", "")
            base["comment"] = raw.get("message", "")
        elif request_type == "group_invite":
            base["detail_type"] = "group"
            base["group_id"] = raw.get("group_id", "")
            base["user_id"] = raw.get("inviter_id", "")

        return base
```

## 富媒体 сообщения

Реальные события платформы часто содержат богатый контент, такой как изображения, упоминания (@), ответы и т. д. Ниже приведен пример обработки `_convert_message_segments` для различных типов сообщений:

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """Преобразует список сегментов нативных сообщений платформы в стандартные сегменты OneBot12"""
    segments = []

    for item in raw_content:
        item_type = item.get("type", "")

        if item_type == "text":
            segments.append({
                "type": "text",
                "data": {"text": item.get("content", "")}
            })

        elif item_type == "image":
            file_url = item.get("url") or item.get("file_id", "")
            segments.append({
                "type": "image",
                "data": {"file": file_url}
            })

        elif item_type == "at":
            segments.append({
                "type": "mention",
                "data": {"user_id": item.get("target_id", "")}
            })

        elif item_type == "reply":
            segments.append({
                "type": "reply",
                "data": {"message_id": item.get("reply_to_id", "")}
            })

        elif item_type == "at_all":
            segments.append({"type": "mention_all", "data": {}})

        else:
            segments.append({
                "type": "text",
                "data": {"text": f"[Unsupported message type: {item_type}]"}
            })

    return segments
```

## Частые ошибки

### 1. Отсутствие поля `{platform}_raw`

Это наиболее распространенная ошибка. Отсутствие поля исходных данных не позволяет модулям получать доступ к специфической информации платформы.

```python
base_event["myplatform_raw"] = raw_event        # Обязательно!
base_event["myplatform_raw_type"] = event_type   # Обязательно!
```

### 2. Неверный формат timestamp

Стандарт OneBot12 требует, чтобы поле `time` было целым числом Unix timestamp в секундах. Если ваша платформа возвращает timestamp в миллисекундах или строку в ISO формате, необходимо преобразовать данные:

```python
import time

# Milliseconds → Seconds
"time": raw_event.get("timestamp", 0) // 1000

# ISO String → Seconds
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. Отсутствие поля `self`

Поле `self` содержит информацию о самом боте, где `user_id` — это ID аккаунта бота. В сценариях с несколькими ботами это поле критически важно:

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # ID самого бота
}
```

### 4. Использование некорректных значений detail_type

Поле `detail_type` должно использовать значения, определенные стандартом OneBot12, такие как `private`, `group`, `friend_increase`, `group_member_increase` и др. Не используйте названия, специфичные для платформы.

### 5. Согласованность преобразований

Убедитесь, что типы сегментов сообщений, созданные конвертером, соответствуют методам, поддерживаемым на стороне отправки (Send). Например, если конвертер преобразует сообщение изображения платформы в `{"type": "image", ...}`, то метод `Image()` на стороне отправки должен корректно обрабатывать отправку изображений.

## Рекомендуемые практики (Best Practices)

1.  **Всегда сохраняйте исходные данные**: Поле `{platform}_raw` не может быть опущено.
2.  **Используйте стандартные сегменты сообщений**: По возможности конвертируйте сообщения платформы в стандартные сегменты сообщений OneBot12.
3.  **Корректно устанавливайте detail_type**: Используйте стандартные типы (`private`/`group`/`channel` и др.), не создавайте собственные.
4.  **Обрабатывайте граничные случаи**: В исходном событии могут отсутствовать определенные поля, используйте `.get()` и предоставляйте разумные значения по умолчанию.
5.  **Учитывайте производительность**: Метод `convert()` вызывается для каждого события, избегайте выполнения трудоемких операций внутри него.

## Связанные документы

- [Концепции ядра адаптера](core-concepts.md) - Общая архитектура адаптера
- [Подробное описание SendDSL](send-dsl.md) - Обратное преобразование (направление отправки)
- [Стандарты преобразования событий](../../standards/event-conversion.md) - Официальные спецификации преобразования событий
- [Система типов сессий](../../advanced/session-types.md) - Правила сопоставления типов сессий