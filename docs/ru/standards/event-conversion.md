# Спецификация стандартизации преобразования адаптеров

## 1. Основные принципы
1. Строгое соответствие: Все стандартные поля должны полностью соответствовать спецификации OneBot12.
2. Явное расширение: Функции, специфичные для платформы, должны иметь префикс `{platform}_` (например, `yunhu_form`).
3. Целостность данных: Исходные данные события должны храниться в поле `{platform}_raw`, а исходный тип события — в поле `{platform}_raw_type`.
4. Унификация времени: Все временные метки должны быть преобразованы в 10-битные Unix-метки времени (секунды).
5. Унификация платформы: Значение `platform` должно соответствовать имени/псевдониму, под которым вы зарегистрировались в ErisPulse.

## 2. Требования к стандартным полям

### 2.1 Обязательные поля
| Поле | Тип | Описание |
|------|------|------|
| id | string | Уникальный идентификатор события |
| time | integer | Unix-метка времени (секунды) |
| type | string | Тип события |
| detail_type | string | Детальный тип события (см. [Стандарт типов сессий](session-types.md)) |
| platform | string | Название платформы |
| self | object | Информация о самом боте |
| self.platform | string | Название платформы |
| self.user_id | string | User ID бота |

**Правила `detail_type`**:
- Должен использоваться стандартный тип сессии ErisPulse (см. [Стандарт типов сессий](session-types.md)).
- Поддерживаемые типы: `private`, `group`, `user`, `channel`, `guild`, `thread`.
- Адаптер обязан сопоставлять нативные типы платформы со стандартными типами.

### 2.2 Поля события сообщения
| Поле | Тип | Описание |
|------|------|------|
| message | array | Массив сегментов сообщения |
| alt_message | string | Резервный текст сегментов сообщения |
| user_id | string | User ID пользователя |
| user_nickname | string | Никнейм пользователя (необязательно) |

### 2.3 Поля события уведомления
| Поле | Тип | Описание |
|------|------|------|
| user_id | string | User ID пользователя |
| user_nickname | string | Никнейм пользователя (необязательно) |
| operator_id | string | User ID оператора (необязательно) |

### 2.4 Поля события запроса
| Поле | Тип | Описание |
|------|------|------|
| user_id | string | User ID пользователя |
| user_nickname | string | Никнейм пользователя (необязательно) |
| comment | string | Комментарий к запросу (необязательно) |
| request_id | string | Идентификатор запроса (**сильное рекомендуемое поле**, для операций согласия/отказа) |

**Описание поля `request_id`**:
- `request_id` — это уникальный идентификатор операции для события запроса, используемый для выполнения операций согласия/отказа через DSL `HandleRequest`.
- При преобразовании события запроса адаптер должен сопоставить нативный идентификатор запроса платформы с этим полем.
- Если у платформы нет идентификатора запроса, адаптер должен сгенерировать уникальный идентификатор (например, хеш на основе временной метки + user_id).
- Если `request_id` отсутствует, `event.approve()` / `event.reject()` выбросит `ValueError`.

## 3. Примеры формата событий

### 3.1 Событие сообщения (message)
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽奖 超级大奖"
      }
    }
  ],
  "alt_message": "抽奖 超级大奖",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  }
}
```

### 3.2 Событие уведомления (notice)
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 Событие запроса (request)
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "请加好友",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. Стандарт сегментов сообщений

### 4.1 Стандартные сегменты сообщений

Стандартные типы сегментов сообщений **не должны** иметь префикс платформы:

| Тип | Описание | Поля данных |
|------|------|----------|
| `text` | Простой текст | `text: str` |
| `image` | Изображение | `file: str/bytes`, `url: str` |
| `audio` | Аудио | `file: str/bytes`, `url: str` |
| `video` | Видео | `file: str/bytes`, `url: str` |
| `file` | Файл | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | @пользователя | `user_id: str`, `user_name: str` |
| `reply` | Ответ | `message_id: str` |
| `face` | Смайлик | `id: str` |
| `location` | Локация | `latitude: float`, `longitude: float` |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.2 Расширенные сегменты сообщений платформы

Сегменты сообщений, специфичные для платформы, должны иметь префикс платформы:

```json
// Yunhu - Форма
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "报名表"}}

// Telegram - Стикер
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**Требования к расширенным сегментам**:
1. **Поля данных не должны иметь префиксов**: `{"type": "yunhu_form", "data": {"form_id": "..."}}` вместо `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`.
2. **Предоставлять резервный вариант**: Модуль может не распознавать расширенные сегменты сообщений, адаптер должен предоставлять текстовую альтернативу в `alt_message`.
3. **Полнота документации**: Каждый расширенный сегмент сообщения должен быть описан в документации адаптера: структура `type`, `data` и сценарии использования.

## 5. Обработка неизвестных событий

Для типов событий, которые невозможно распознать, следует генерировать событие предупреждения:
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```

---

## 6. Правила именования расширений

### 6.1 Именование полей

**Правило**: `{platform}_{field_name}`

```
Префикс платформы    Поле            Полное поле
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**Требования**:
- `platform` должно полностью совпадать с названием платформы при регистрации адаптера (с учетом регистра).
- `field_name` использует именование `snake_case`.
- Запрещено начинать с двойного подчеркивания `__` (зарезервировано в Python).
- Запрещено называть то же, что и стандартные поля (например, `type`, `time`, `message` и т.д.).

### 6.2 Именование типов сегментов сообщений

**Правило**: `{platform}_{segment_type}`

Стандартные типы сегментов сообщений (например, `text`, `image`, `audio`, `video`, `mention`, `reply` и т.д.) **не должны** иметь префикс платформы. Добавлять префикс нужно только для типов сегментов, специфичных для платформы.

### 6.3 Именование полей исходных данных

Ниже приведены **резервные поля**, которые должны соблюдать все адаптеры:

| Резервное поле | Тип | Описание |
|---------|------|------|
| `{platform}_raw` | `any` | Полная копия исходных данных события платформы |
| `{platform}_raw_type` | `string` | Идентификатор исходного типа события платформы |

**Требования**:
- `{platform}_raw` должен быть глубокой копией исходных данных, а не ссылкой.
- `{platform}_raw_type` должен быть строкой, даже если платформа использует числовой тип, его нужно преобразовать в строку.
- Эти два поля **должны существовать** во всех событиях (в случае отсутствия данных — `null` и пустая строка `""`).

### 6.4 Примеры полей, специфичных для платформы

```json
{
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 Вложенные расширенные поля

Расширенные поля могут быть простыми значениями или вложенными объектами:

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**Требования к вложенным полям**:
- Ключи верхнего уровня должны иметь префикс платформы.
- Внутренние поля вложенности **не должны** иметь префикс платформы.
- Рекомендуемая глубина вложенности не более 3 уровней.

### 6.6 Расширение поля `self`

Стандартные обязательные поля объекта `self` (поля `platform`, `user_id`) см. в §2.1. Ниже приведены необязательные поля, расширенные ErisPulse:

| Поле | Тип | Описание |
|------|------|------|
| `self.user_name` | `string` | Никнейм бота |
| `self.avatar` | `string` | URL аватара бота |
| `self.account_id` | `string` | Идентификатор аккаунта в режиме нескольких аккаунтов |

> **Отслеживание статуса бота**: Адаптер сообщает фреймворку о статусе подключения бота, отправляя событие `type: "meta"`. Поддерживаемые `detail_type`: `connect` (онлайн), `heartbeat` (сердцебиение), `disconnect` (оффлайн). Система автоматически извлекает метаинформацию бота из поля `self` для отслеживания состояния. Кроме того, поле `self` в обычных событиях также автоматически обнаруживает бота. Подробнее см. [API системы адаптеров - Управление статусом бота](../api-reference/adapter-system.md).

---

## 7. Расширение типов сессий

ErisPulse расширяет следующие типы сессий на основе стандартов OneBot12 `private` и `group`:

| Тип | OneBot12 стандарт | Расширение ErisPulse | Описание |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | Личный чат (1 на 1) |
| `group` | ✅ | — | Групповой чат |
| `user` | — | ✅ | Тип пользователя (Telegram и др.) |
| `channel` | — | ✅ | Канал (вещательный) |
| `guild` | — | ✅ | Сервер / сообщество |
| `thread` | — | ✅ | Тема / подпост |

**Расширение пользовательских типов адаптером**:

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# Регистрация при запуске адаптера
register_custom_type(
    receive_type="email",      # Тип сессии в событии получения
    send_type="email",         # Тип цели при отправке
    id_field="email_id",       # Имя соответствующего поля ID
    platform="email"           # Идентификатор платформы
)
```

**Требования к пользовательским типам**:
- Должны быть зарегистрированы при `start()` адаптера и отменены при `shutdown()`.
- `receive_type` не должно совпадать по имени со стандартными типами.
- `id_field` должно следовать шаблону именования `{цель}_id`.

> Полное определение типов сессий и отношения отображения см. в [Стандарте типов сессий](session-types.md).

---

## 8. Руководство для разработчиков модулей

### 8.1 Доступ к расширенным полям

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # Доступ к стандартным полям
    text = event.get_text()
    user_id = event.get_user_id()

    # Доступ к расширенным полям платформы - способ 1: прямой get
    yunhu_command = event.get("yunhu_command")

    # Доступ к расширенным полям платформы - способ 2: доступ через точку (класс-обертка Event)
    # event.yunhu_command

    # Доступ к исходным данным
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # Определение платформы
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 Обработка расширенных сегментов сообщений

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 Лучшие практики

1. **Приоритет стандартным полям**: Не предполагайте, что расширенные поля обязательно существуют.
2. **Определение платформы**: Определяйте платформу через `event.get_platform()`, а не путем вывода на основе наличия расширенных полей.
3. **Graceful degradation (Гибкий откат)**: При невозможности обработки расширенного сегмента сообщения используйте `alt_message` в качестве запасного варианта.
4. **Не используйте жестко заданные префиксы**: Динамически склеивайте префикс, используя переменную `platform`.

```python
# ✅ Рекомендуется
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ Не рекомендуется
raw_data = event.get("yunhu_raw")
```

### 8.4 Обработка событий запроса

Разработчики модулей могут управлять событиями запроса с помощью `event.approve()` и `event.reject()`:

```python
from ErisPulse.Core.Event import request

# Запрос на добавление в друзья: автоматически согласие
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # Согласие с запросом
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"Успешно согласен с запросом {user_name}")
    else:
        print(f"Не удалось согласиться с запросом в друзья: {result.get('message')}")

# Приглашение в группу: решение на основе условий
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # Отказ от запроса
    result = await event.reject(comment="Пока не присоединяюсь к новым группам")
```

**Прямое управление через адаптер** (подходит для сценариев, не использующих обработчики событий):

```python
from ErisPulse import adapter

# Управление напрямую через request_id
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Указание аккаунта бота для операции
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# С комментарием
await adapter.myplatform.Request("req_abc123").accept(comment="Добро пожаловать")
```

---

## 9. Связанные документы

- [Документация особенностей платформ](../platform-guide/README.md) - Вы можете обратиться к этому документу, чтобы узнать особенности каждой платформы, а также известные расширенные события и сегменты сообщений.
- [Стандарт типов сессий](session-types.md) - Определения типов сессий и отношения отображения
- [Спецификация методов отправки](send-method-spec.md) - Имена методов, именование параметров класса Send и требования к обратному преобразованию
- [Стандарт ответов API](api-response.md) - Стандарт формата ответов API адаптера

Пожалуйста, верните полный переведенный контент Markdown без каких-либо дополнительных слов.