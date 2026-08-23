# Руководство по реализации конвертера событий

Конвертер событий (Converter) — один из ключевых компонентов адаптера, отвечающий за преобразование нативных событий платформы в унифицированный формат событий OneBot12 от ErisPulse.

docs/ru/quick-start.md | docs/ru/guide.md | docs/ru/api.md

## Ответственность Converter

```
События платформы ──→ Converter.convert() ──→ Стандартные события OneBot12
```

Converter отвечает только за **прямое преобразование** (направление получения), то есть за преобразование данных событий платформы в стандартный формат OneBot12. Обратное преобразование (направление отправки) обрабатывается методом `Send.Raw_ob12()`.

### Основные принципы

1. **Без потерь**: исходные данные должны быть полностью сохранены в поле `{platform}_raw`
2. **Совместимость со стандартом**: преобразованные события должны соответствовать стандартному формату OneBot12
3. **Расширения платформы**: данные, специфичные для платформы, хранятся в полях с префиксом `{platform}_`

[**English**](docs/ru/quick-start.md) | [**简体中文**](docs/ru/quick-start.md)

## Базовый класс BaseConverter (рекомендуется)

Начиная с версии 2.7.0, фреймворк предоставляет базовый класс `BaseConverter` (`ErisPulse.Core.Bases`), который封装ует **общее построение полей событий OneBot12** и **помощь с часто используемыми сообщениями**, позволяя конвертеру сосредоточиться только на типовом отображении:

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

Заполненные общие поля `build_base_event()`:

| Поле | Источник |
|------|------|
| `id` | `raw_event["event_id"]`, по умолчанию генерируется UUID |
| `time` | `raw_event["timestamp"]`, по умолчанию текущее время |
| `platform` | переданный при создании `platform` |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | исходное событие (соответствует принципу "без потерь") |
| `{platform}_raw_type` | тип исходного события |

Часто используемые методы помощи с сообщениями (все статические, можно повторно использовать):

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> При ручной реализации конструктор общих полей `build_base_event` является обязательным шаблонным кодом, который нужно повторно писать. Использование `BaseConverter` позволяет избежать этой части, и при этом естественно удовлетворяет принципу "без потерь" (исходное событие всегда попадает в `{platform}_raw`).

[**README**](README.ru.md) | [**快速入门**](docs/ru/quick-start.md) | [**文档**](docs/ru/introduction.md) | [**贡献**](CONTRIBUTING.ru.md) | [**许可证**](LICENSE)

## Метод convert()

### Подпись метода

```python
def convert(self, raw_event: dict) -> dict:
    """
    Преобразует платформенно-специфичное событие в стандартный формат OneBot12

    :param raw_event: Данные платформенно-специфичного события
    :return: Словарь события в стандартизированном формате OneBot12
    """
    pass
```

### Структура возвращаемого значения

Преобразованный словарь события должен содержать следующие стандартные поля:

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
    "alt_message": "Содержимое в виде простого текста",

    # Обязательно сохранить исходные данные
    "myplatform_raw": { ... },     # Полные данные исходного события платформы
    "myplatform_raw_type": "Имя типа исходного события",
}

## Обязательные поля

### Общие поля (для всех типов событий)

| OB12 поле | Тип | Описание |
|-----------|------|------|
| `id` | str | Уникальный идентификатор события |
| `time` | int | Unix-время (в секундах) |
| `type` | str | Тип события: `message` / `notice` / `request` / `meta` |
| `detail_type` | str | Подтип: `private` / `group` / `friend` и т.д. |
| `platform` | str | Название платформы, совпадает с именем адаптера |
| `self` | dict | Информация о боте: `{"platform": "...", "user_id": "..."}` |

### Дополнительные поля для событий сообщений

| OB12 поле | Тип | Описание |
|-----------|------|------|
| `user_id` | str | ID отправителя |
| `message` | list[dict] | Список сообщений OneBot12 |
| `alt_message` | str | Запасной текстовый контент |

### Дополнительные поля для уведомлений

| OB12 поле | Тип | Описание |
|-----------|------|------|
| `user_id` | str | ID связанного пользователя |
| `operator_id` | str | ID оператора (например, при изменении участников группы) |

[**English**](docs/ru/quick-start.md) | [**简体中文**](docs/ru/quick-start.md) | [**Русский**](docs/ru/quick-start.md)

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

# Упоминание
{"type": "mention", "data": {"user_id": "123"}}

# Упоминание всех
{"type": "mention_all", "data": {}}

# Ответ
{"type": "reply", "data": {"message_id": "msg_123"}}
```

Если платформа не поддерживает определённый тип сегмента сообщения, этот сегмент можно опустить или преобразовать в наиболее близкий стандартный тип.

[**中文**](docs/ru/quick-start.md)

## Платформенные расширенные поля

Данные, специфичные для платформы, следует хранить с префиксом `{platform}_`, чтобы избежать конфликта с стандартными полями:

```python
{
    # Стандартные поля
    "type": "message",
    "detail_type": "group",
    # ...

    # Платформенные расширенные поля
    "myplatform_raw": { ... },          # Исходные данные события (обязательно)
    "myplatform_raw_type": "chat",      # Тип исходного события (обязательно)

    # Другие поля, специфичные для платформы
    "myplatform_group_name": "Название группы",
    "myplatform_sender_role": "admin",
}
```

> **Важно**: Поле `{platform}_raw` обязательно, система событий и модули ErisPulse могут зависеть от него для доступа к исходным данным платформы.

[**English**](docs/ru/quick-start.md)

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

## Пример преобразования мультимедийных сообщений

Сообщения, отправляемые на реальных платформах, обычно содержат мультимедийные элементы, такие как изображения, @-упоминания, ответы и т.д. Ниже приведен пример обработки `_convert_message_segments` для различных типов сообщений:

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """Преобразует список сегментов сообщений платформы в стандартные сегменты OneBot12"""
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

## Распространённые ошибки

### 1. Отсутствует поле `{platform}_raw`

Это самая распространённая ошибка. Отсутствие поля с исходными данными приводит к невозможности доступа к платформенно-специфической информации.

```python
base_event["myplatform_raw"] = raw_event        # Обязательно!
base_event["myplatform_raw_type"] = event_type   # Обязательно!
```

### 2. Неправильный формат временной метки

Стандарт OneBot12 требует, чтобы поле `time` было Unix-временем в секундах (целое число). Если платформа возвращает миллисекунды или строку в формате ISO, необходимо выполнить преобразование:

```python
import time

# Миллисекунды → секунды
"time": raw_event.get("timestamp", 0) // 1000

# Строка ISO → секунды
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. Отсутствует поле `self`

Поле `self` содержит информацию о самом боте, `user_id` — это ID аккаунта бота. В сценариях с несколькими ботами это поле имеет особое значение:

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # ID самого бота
}
```

### 4. Использование недопустимых значений `detail_type`

Значение `detail_type` должно соответствовать стандартным значениям, определённым в OneBot12, таким как `private`, `group`, `friend_increase`, `group_member_increase` и т.д. Не следует использовать платформенно-специфические названия.

### 5. Соответствие направлениям

Убедитесь, что типы сообщений, создаваемые Converter, соответствуют поддерживаемым методам в Send-части. Например, если Converter преобразует платформенное сообщение с изображением в `{"type": "image", ...}`, то метод `Image()` в Send-части должен уметь отправлять изображения.

[**Руководство**](docs/ru/quick-start.md)

## Лучшие практики

1. **Всегда сохраняйте исходные данные**: Поле `{platform}_raw` не должно опускаться
2. **Используйте стандартные сегменты сообщений**: Старайтесь преобразовывать сообщения платформы в стандартные сегменты OneBot12
3. **Разумно задавайте detail_type**: Используйте стандартные типы (`private`/`group`/`channel` и т.д.), не создавайте собственные
4. **Обрабатывайте граничные случаи**: Исходное событие может отсутствовать некоторых полей, используйте `.get()` и задавайте разумные значения по умолчанию
5. **Учитывайте производительность**: `convert()` вызывается для каждого события, избегайте выполнения в нем операций, требующих много времени

[**English**](docs/ru/quick-start.md)

## Связанные документы

- [Основные понятия адаптера](core-concepts.md) - Общая архитектура адаптера
- [Подробное руководство по SendDSL](send-dsl.md) - Обратное преобразование (направление отправки)
- [Стандарт преобразования событий](../../standards/event-conversion.md) - Официальный стандарт преобразования событий
- [Система типов сессий](../../standards/session-types.md) - Правила отображения типов сессий