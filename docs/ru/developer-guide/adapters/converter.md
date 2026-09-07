# Руководство по реализации конвертера событий

Конвертер событий (Converter) — один из ключевых компонентов адаптера, отвечающий за преобразование нативных событий платформы в унифицированный формат событий OneBot12, используемый ErisPulse.

## Ответственность Converter

```
Платформенные нативные события ──→ Converter.convert() ──→ События в стандарте OneBot12
```

Converter отвечает только за **прямое преобразование** (направление получения), то есть за преобразование данных платформенных нативных событий в стандартный формат OneBot12. Обратное преобразование (направление отправки) обрабатывается методом `Send.Raw_ob12()`.

### Основные принципы

1. **Без потерь**: исходные данные должны быть полностью сохранены в поле `{platform}_raw`
2. **Совместимость со стандартом**: преобразованные события должны соответствовать стандартному формату OneBot12
3. **Платформенные расширения**: платформенно-специфические данные хранятся в полях с префиксом `{platform}_`

## Базовый класс BaseConverter (рекомендуется)

Начиная с версии 2.7.0, фреймворк предоставляет базовый класс `BaseConverter` (`ErisPulse.Core.Bases`), который封装ует общие поля событий OneBot12 и вспомогательные методы для часто используемых сообщений, позволяя конвертеру фокусироваться только на типовом преобразовании:

```python
from ErisPulse.Core.Bases import BaseConverter


class MyConverter(BaseConverter):
    def __init__(self):
        super().__init__(platform="myplatform")

    def convert(self, raw_event: dict) -> dict | None:
        if not isinstance(raw_event, dict):
            return None
        event_type = raw_event.get("type", "")
        base = self.build_base_event(raw_event, event_type)  # id/time/platform/self/raw
        if event_type == "message":
            base["type"] = "message"
            base["detail_type"] = "group" if raw_event.get("group_id") else "private"
            base["user_id"] = str(raw_event.get("sender_id", ""))
            base["message"] = [self.text(raw_event.get("content", ""))]
            base["alt_message"] = raw_event.get("content", "")
            return base
        return None
```

Поле `build_base_event()` уже заполнено общими полями:

| Поле | Источник |
|------|------|
| `id` | `raw_event["event_id"]`, если отсутствует, генерируется UUID |
| `time` | `raw_event["timestamp"]`, если отсутствует, устанавливается текущее время |
| `platform` | Переданное при создании `platform` |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | Исходное событие (соответствует принципу "без потерь") |
| `{platform}_raw_type` | Тип исходного события |

Общие вспомогательные методы для сообщений (все статические, можно напрямую использовать):

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> При ручной реализации конструирование общих полей `build_base_event` является обязательным и повторяющимся шаблонным кодом, использование `BaseConverter` позволяет избежать этой части и обеспечивает "без потерь" преобразование (исходное событие всегда попадает в `{platform}_raw`).

## Метод convert()

### Подпись метода

```python
def convert(self, raw_event: dict) -> dict:
    """
    Преобразует событие платформы в стандартный формат OneBot12

    :param raw_event: Данные события платформы
    :return: Словарь события в стандартном формате OneBot12
    """
    pass
```

### Структура возвращаемого значения

Словарь события после преобразования должен содержать следующие стандартные поля:

```python
{
    "id": "Уникальный ID события",
    "time": 1234567890,           # Unix-время (секунды)
    "type": "message",             # Тип события
    "detail_type": "private",      # Подтип события
    "platform": "myplatform",      # Название платформы
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # Поля сообщения
    "user_id": "id_отправителя",
    "message": [...],              # Список сегментов сообщения в формате OneBot12
    "alt_message": "Содержимое в виде обычного текста",

    # Должны сохраняться исходные данные
    "myplatform_raw": { ... },     # Полные исходные данные события платформы
    "myplatform_raw_type": "Имя типа исходного события",
}
```

## Обязательные поля

### Общие поля (для всех типов событий)

| OB12 поле | Тип | Описание |
|-----------|------|------|
| `id` | str | Уникальный идентификатор события |
| `time` | int | Временная метка Unix (в секундах) |
| `type` | str | Тип события: `message` / `notice` / `request` / `meta` |
| `detail_type` | str | Детальный тип: `private` / `group` / `friend` и т.д. |
| `platform` | str | Название платформы, совпадает с именем адаптера |
| `self` | dict | Информация о боте: `{"platform": "...", "user_id": "..."}` |

### Дополнительные поля для событий сообщений

| OB12 поле | Тип | Описание |
|-----------|------|------|
| `user_id` | str | ID отправителя |
| `message` | list[dict] | Список сегментов сообщений OneBot12 |
| `alt_message` | str | Резервный текстовый контент |

### Дополнительные поля для уведомлений

| OB12 поле | Тип | Описание |
|-----------|------|------|
| `user_id` | str | ID связанного пользователя |
| `operator_id` | str | ID оператора (например, при изменении участников группы) |

## Преобразование сегментов сообщений

Стандарт OneBot12 определяет следующие типы сегментов сообщений:

```python
# Текст
{"type": "text", "data": {"text": "Привет"}}

# Изображение
{"type": "image", "data": {"file": "https://example.com/img.jpg"}}

# Аудио
{"type": "audio", "data": {"file": "https://example.com/audio.mp3"}}

# Видео
{"type": "video", "data": {"file": "https://example.com/video.mp4"}}

# Файл
{"type": "file", "data": {"file": "https://example.com/doc.pdf"}}

# Упоминание пользователя
{"type": "mention", "data": {"user_id": "123"}}

# Упоминание всех
{"type": "mention_all", "data": {}}

# Ответ на сообщение
{"type": "reply", "data": {"message_id": "msg_123"}}
```

Если платформа не поддерживает определённый тип сегмента сообщений, этот сегмент можно опустить или преобразовать в наиболее близкий стандартный тип.

## Расширения платформы

Данные, специфичные для платформы, должны храниться с префиксом `{platform}_`, чтобы избежать конфликта с стандартными полями:

```python
{
    # Стандартные поля
    "type": "message",
    "detail_type": "group",
    # ...

    # Расширения платформы
    "myplatform_raw": { ... },          # Исходные данные события (обязательно)
    "myplatform_raw_type": "chat",      # Тип исходного события (обязательно)

    # Другие специфические для платформы поля
    "myplatform_group_name": "Название группы",
    "myplatform_sender_role": "администратор",
}
```

> **Важно**: Поле `{platform}_raw` обязательно, так как система событий и модули ErisPulse могут зависеть от него для доступа к исходным данным платформы.

## Полный пример

Ниже представлен полный пример реализации Converter:

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

## Пример преобразования мультимедийного сообщения

Сообщения, отправленные на реальных платформах, обычно содержат мультимедийные элементы, такие как изображения, упоминания пользователей и ответы. Ниже приведён пример обработки `_convert_message_segments` для различных типов сообщений:

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """Преобразует список сегментов сообщений платформы в стандартный формат OneBot12"""
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
                "data": {"text": f"[Неподдерживаемый тип сообщения: {item_type}]"}
            })

    return segments
```

## Common Pitfalls

### 1. Missing `{platform}_raw` Field

This is the most common mistake. Missing the raw data field prevents the module from accessing platform-specific information.

```python
base_event["myplatform_raw"] = raw_event        # Required!
base_event["myplatform_raw_type"] = event_type   # Required!
```

### 2. Incorrect Timestamp Format

OneBot12 standard requires the `time` field to be a Unix timestamp in seconds (integer). If your platform returns a millisecond timestamp or an ISO-formatted string, you need to convert it:

```python
import time

# Milliseconds → Seconds
"time": raw_event.get("timestamp", 0) // 1000

# ISO string → Seconds
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. Missing `self` Field

The `self` field contains information about the bot itself, with `user_id` being the bot's account ID. This field is crucial in multi-bot scenarios:

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # ID of the bot itself
}
```

### 4. Using Non-Standard `detail_type` Values

The `detail_type` must use values defined by the OneBot12 standard, such as `private`, `group`, `friend_increase`, `group_member_increase`, etc. Do not use platform-specific naming.

### 5. Round-Trip Consistency

Ensure that the message segment types generated by the Converter correspond to the methods supported by the Send endpoint. For example, if the Converter converts the platform's image message to `{"type": "image", ...}`, then the `Image()` method in the Send endpoint must be able to handle image sending.

## Рекомендуемые практики

1. **Всегда сохраняйте исходные данные**: поле `{platform}_raw` не должно быть опущено
2. **Используйте стандартные сообщения**: по возможности преобразуйте сообщения платформы в стандартные сообщения OneBot12
3. **Рационально настройте detail_type**: используйте стандартные типы (`private`/`group`/`channel` и т.д.), не создавайте собственные
4. **Обрабатывайте граничные случаи**: исходное событие может не содержать некоторых полей, используйте `.get()` и задавайте разумные значения по умолчанию
5. **Учитывайте производительность**: `convert()` вызывается для каждого события, избегайте выполнения длительных операций внутри него

## Связанные документы

- [Основные понятия адаптера](core-concepts.md) - Общая архитектура адаптера
- [Подробное руководство SendDSL](send-dsl.md) - Обратное преобразование (направление отправки)
- [Стандарт преобразования событий](../../standards/event-conversion.md) - Официальный стандарт преобразования событий
- [Система типов сессий](../../standards/session-types.md) - Правила отображения типов сессий