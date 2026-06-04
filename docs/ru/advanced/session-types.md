# Система типов сессий

Система типов сессий ErisPulse отвечает за определение и управление типами сессий сообщений (личный чат, групповой чат, каналы и т.д.), а также предоставляет автоматическое преобразование между типами получения и типами отправки.

## Определение типов

### Типы получения (ReceiveType)

Типы получения берутся из поля `detail_type` событий OneBot12 и описывают сцену сессии события:

| Тип | Описание | Поле ID |
|------|----------|---------|
| `private` | Сообщение личного чата | `user_id` |
| `group` | Сообщение группового чата | `group_id` |
| `channel` | Сообщение канала | `channel_id` |
| `guild` | Сообщение сервера | `guild_id` |
| `thread` | Сообщение темы / подканала | `thread_id` |
| `user` | Сообщение пользователя (расширенное) | `user_id` |

### Типы отправки (SendType)

Типы отправки используются для указания цели отправки в `Send.To(type, id)`:

| Тип | Описание |
|------|----------|
| `user` | Отправить пользователю |
| `group` | Отправить в группу |
| `channel` | Отправить в канал |
| `guild` | Отправить на сервер |
| `thread` | Отправить в тему |

## Картирование типов

Существует стандартное отношение отображения между типами получения и типами отправки:

```
Получение (Receive)          Отправка (Send)
─────────────          ──────────
private        ──→     user
group          ──→     group
channel        ──→     channel
guild          ──→     guild
thread         ──→     thread
user           ──→     user
```

Ключевое различие: **используйте "private" при получении и "user" при отправке**. Это стандартный дизайн OneBot12 — событие описывает "сценарий личного чата", а отправка описывает "цель пользователя".

## Автоматическое определение

Когда у события нет четкого поля `detail_type`, система автоматически определит тип сессии на основе полей ID, присутствующих в событии:

**Приоритет**: `group_id` > `channel_id` > `guild_id` > `thread_id` > `user_id`

```python
from ErisPulse.Core.Event.session_type import infer_receive_type

# Есть group_id → определяется как group
event1 = {"group_id": "123", "user_id": "456"}
print(infer_receive_type(event1))  # "group"

# Есть только user_id → определяется как private
event2 = {"user_id": "456"}
print(infer_receive_type(event2))  # "private"
```

## Основные API

### Преобразование типов

```python
from ErisPulse.Core.Event.session_type import (
    convert_to_send_type,
    convert_to_receive_type,
)

# Тип получения → Тип отправки
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# Тип отправки → Тип получения
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### Запрос полей ID

```python
from ErisPulse.Core.Event.session_type import get_id_field, get_receive_type

# Получить имя поля ID по типу
get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

# Получить тип по полю ID
get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### Получение информации об отправке за один шаг

```python
from ErisPulse.Core.Event.session_type import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# Использовать прямо в Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### Получение целевого ID

```python
from ErisPulse.Core.Event.session_type import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## Регистрация пользовательских типов

Адаптер может регистрировать пользовательские сопоставления для типов сессий, специфичных для платформы:

```python
from ErisPulse.Core.Event.session_type import register_custom_type, unregister_custom_type

# Регистрация пользовательского типа
register_custom_type(
    receive_type="thread_reply",     # Имя типа получения
    send_type="thread",              # Соответствующий тип отправки
    id_field="thread_reply_id",      # Соответствующее поле ID
    platform="discord"               # Имя платформы (необязательно)
)

# Использование пользовательского типа
convert_to_send_type("thread_reply", platform="discord")  # → "thread"
get_id_field("thread_reply", platform="discord")          # → "thread_reply_id"

# Отмена регистрации пользовательского типа
unregister_custom_type("thread_reply", platform="discord")
```

> **При указании `platform`** зарегистрированные типы получения будут иметь префикс платформы (например, `discord_thread_reply`), чтобы избежать конфликтов типов между разными платформами.

## Утилиты

```python
from ErisPulse.Core.Event.session_type import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

# Проверка, является ли это стандартным типом
is_standard_type("private")  # True
is_standard_type("custom_type")  # False

# Проверка, является ли тип отправки допустимым
is_valid_send_type("user")  # True
is_valid_send_type("invalid")  # False

# Получение всех стандартных типов
get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

# Очистка пользовательских типов
clear_custom_types()                # очистить все
clear_custom_types(platform="discord")  # очистить только для указанной платформы
```

## Связанные документы

- [Стандарты преобразования событий](../standards/event-conversion.md) - спецификации преобразования событий
- [Стандарты типов сессий](../standards/session-types.md) - официальное определение типов сессий
- [Реализация преобразователей событий](../developer-guide/adapters/getting-started.md) - руководство по разработке адаптеров