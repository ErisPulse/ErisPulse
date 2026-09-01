# Руководство по реализации конвертера событий

Конвертер событий (Converter) — один из ключевых компонентов адаптера, отвечающий за преобразование событий платформы в унифицированный формат событий OneBot12 от ErisPulse.

## Ответственность Converter

```
События платформы ──→ Converter.convert() ──→ События стандарта OneBot12
```

Converter отвечает только за **прямое преобразование** (направление получения), то есть за преобразование данных событий платформы в стандартный формат OneBot12. Обратное преобразование (направление отправки) обрабатывается методом `Send.Raw_ob12()`.

### Основные принципы

1. **Без потерь**: исходные данные должны быть полностью сохранены в поле `{platform}_raw`
2. **Совместимость со стандартом**: преобразованные события должны соответствовать стандартному формату OneBot12
3. **Расширения платформы**: платформенно-специфичные данные хранятся в полях с префиксом `{platform}_`

## Базовый класс BaseConverter (рекомендуется)

Начиная с версии 2.7.0, фреймворк предоставляет базовый класс `BaseConverter` (`ErisPulse.Core.Bases`), который封装ует общие поля событий OneBot12 и вспомогательные методы для часто используемых сообщений, позволяя конвертеру сосредоточиться только на маппинге типов:

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
|------|----------|
| `id` | `raw_event["event_id"]`, если отсутствует, генерируется UUID |
| `time` | `raw_event["timestamp"]`, если отсутствует, используется текущее время |
| `platform` | переданный при создании `platform` |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | исходное событие (соответствует принципу "без потерь") |
| `{platform}_raw_type` | тип исходного события |

Общие вспомогательные методы для сообщений (все статические методы, можно использовать напрямую):

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> При ручной реализации конструирование общих полей в `build_base_event` является обязательным шаблонным кодом, использование `BaseConverter` позволяет избежать этой части и автоматически обеспечивает "без потерь" (исходное событие всегда попадает в `{platform}_raw`).

## Метод convert()

### Подпись метода

```python
def convert(self, raw_event: dict) -> dict:
    """
    Преобразует событие с платформы в стандартный формат OneBot12

    :param raw_event: Данные события с платформы
    :return: Словарь события в стандарте OneBot12
    """
    pass
```

### Структура возвращаемого значения

Словарь события после преобразования должен содержать следующие стандартные поля:

```python
{
    "id": "Уникальный идентификатор события",
    "time": 1234567890,           # Unix-время (секунды)
    "type": "message",             # Тип события
    "detail_type": "private",      # Подтип события
    "platform": "myplatform",      # Название платформы
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # Поля события сообщения
    "user_id": "sender_id",
    "message": [...],              # Список сообщений OneBot12
    "alt_message": "Содержимое в виде обычного текста",

    # Обязательно сохранить исходные данные
    "myplatform_raw": { ... },     # Полные данные события с платформы
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
| `detail_type` | str | Подробный тип: `private` / `group` / `friend` и т.д. |
| `platform` | str | Название платформы, совпадает с именем адаптера |
| `self` | dict | Информация о боте: `{"platform": "...", "user_id": "..."}` |

### Дополнительные поля для событий сообщений

| OB12 поле | Тип | Описание |
|-----------|------|------|
| `user_id` | str | ID отправителя |
| `message` | list[dict] | Список сообщений OneBot12 |
| `alt_message` | str | Запасное содержимое в виде текста |

### Дополнительные поля для уведомлений

| OB12 поле | Тип | Описание |
|-----------|------|------|
| `user_id` | str | ID связанного пользователя |
| `operator_id` | str | ID оператора (например, при изменении участников группы) |

## Преобразование сегментов сообщений

Однобот-12 стандарт определяет следующие типы сегментов сообщений:

```python
# Текст
{"type": "text", "data": {"text": "Hello"}}

# Изображение
{"type": "image", "data": {"file": "https://example.com/img.jpg"}}

# Аудио
{"type": "audio", "data": {"file": "https://example.com/audio.mp3"}}

# Видео
{"type": "video", "data": {"file": "https://example.com/video.mp4"}}

# Файл
{"type": "file", "data": {"file": "https://example.com/doc.pdf"}}

# Упоминание
{"type": "mention", "data": {"user_id": "123"}}

# Упоминание всех
{"type": "mention_all", "data": {}}

# Ответ
{"type": "reply", "data": {"message_id": "msg_123"}}
```

Если платформа не поддерживает определённый тип сегмента сообщения, этот сегмент можно опустить или преобразовать в наиболее близкий стандартный тип.

## Пользовательские поля платформы

Данные, специфичные для платформы, следует хранить с префиксом `{platform}_`, чтобы избежать конфликтов со стандартными полями:

```python
{
    # Стандартные поля
    "type": "message",
    "detail_type": "group",
    # ...

    # Пользовательские поля платформы
    "myplatform_raw": { ... },          # Исходные данные события (обязательно)
    "myplatform_raw_type": "chat",      # Тип исходного события (обязательно)

    # Другие специфичные для платформы поля
    "myplatform_group_name": "Название группы",
    "myplatform_sender_role": "администратор",
}
```

> **Важно**: Поле `{platform}_raw` обязательно, так как система событий и модули ErisPulse могут полагаться на него для доступа к исходным данным платформы.

## Полный пример

Ниже приведена полная реализация Converter:

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

## Пример преобразования богато форматированного сообщения

Сообщения на реальных платформах обычно содержат богато форматированные элементы, такие как изображения, упоминания пользователей (@), ответы и т. д. Ниже приведён пример обработки `_convert_message_segments` для различных типов сообщений:

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """Преобразование списка сообщений платформы в стандартный формат OneBot12"""
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

## Распространённые ошибки

### 1. Отсутствие поля `{platform}_raw`

Это самая распространённая ошибка. Отсутствие поля с исходными данными приводит к невозможности модуля получить информацию, специфичную для платформы.

```python
base_event["myplatform_raw"] = raw_event        # Обязательно!
base_event["myplatform_raw_type"] = event_type   # Обязательно!
```

### 2. Неправильный формат временной метки

Стандарт OneBot12 требует, чтобы поле `time` было Unix-меткой времени в секундах (целое число). Если ваша платформа возвращает метку в миллисекундах или в формате ISO-строки, необходимо выполнить преобразование:

```python
import time

# Миллисекунды → секунды
"time": raw_event.get("timestamp", 0) // 1000

# ISO-строка → секунды
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. Отсутствие поля `self`

Поле `self` содержит информацию о самом боте, `user_id` — это идентификатор бота. В сценариях с несколькими ботами это поле имеет особое значение:

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # ID самого бота
}
```

### 4. Использование недопустимых значений `detail_type`

Значение `detail_type` должно быть одним из стандартных значений, определённых в OneBot12, таких как `private`, `group`, `friend_increase`, `group_member_increase` и т.д. Не используйте платформенно-специфичные имена.

### 5. Согласованность при обмене сообщениями

Убедитесь, что типы сообщений, создаваемые Converter, соответствуют методам, поддерживаемым Send-модулем. Например, если Converter преобразует платформенное сообщение с изображением в `{"type": "image", ...}`, то метод `Image()` в Send-модуле должен уметь отправлять изображения.

## Рекомендуемые практики

1. **Всегда сохраняйте исходные данные**: поле `{platform}_raw` не должно опускаться
2. **Используйте стандартные сегменты сообщений**: по возможности преобразуйте сообщения платформы в стандартные сегменты OneBot12
3. **Разумно задавайте detail_type**: используйте стандартные типы (`private`/`group`/`channel` и т.д.), не создавайте собственные
4. **Обрабатывайте граничные случаи**: в исходном событии могут отсутствовать некоторые поля, используйте `.get()` и задавайте разумные значения по умолчанию
5. **Учитывайте производительность**: `convert()` вызывается для каждого события, избегайте выполнения длительных операций внутри него

## Связанные документы

- [Основные понятия адаптера](core-concepts.md) - Общая архитектура адаптера
- [Подробное описание SendDSL](send-dsl.md) - Обратное преобразование (направление отправки)
- [Стандарт преобразования событий](../../standards/event-conversion.md) - Официальный стандарт преобразования событий
- [Система типов сеанса](../../standards/session-types.md) - Правила отображения типов сеанса