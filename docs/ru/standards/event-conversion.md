# Спецификация стандартизации адаптера

## 1. Основные принципы
1. Строгая совместимость: Все стандартные поля должны строго следовать спецификации OneBot12.
2. Явное расширение: Платформенно-специфичные функции должны добавлять префикс `{platform}_` (например, yunhu_form).
3. Целостность данных: Исходные данные события должны сохраняться в поле `{platform}_raw`, а исходный тип события — в поле `{platform}_raw_type`.
4. Единообразие времени: Все временные метки должны быть преобразованы в 10-значный временной штамп Unix (секунды).
5. Единообразие платформ: Имя поля `platform` должно соответствовать имени/алиасу, под которым вы зарегистрировались в ErisPulse.

## 2. Требования к стандартным полям

### 2.1 Обязательные поля
| Поле | Тип | Описание |
|------|------|------|
| id | string | Уникальный идентификатор события |
| time | integer | Временной штамп Unix (секунды) |
| type | string | Тип события |
| detail_type | string | Детальный тип события (подробнее см. [Стандарт типов сессий](session-types.md)) |
| platform | string | Название платформы |
| self | object | Информация о самом боте |
| self.platform | string | Название платформы |
| self.user_id | string | User ID бота |

**Правила для `detail_type`**:
- Должны использоваться стандартные типы сессий ErisPulse (подробнее см. [Стандарт типов сессий](session-types.md))
- Поддерживаемые типы: `private`, `group`, `user`, `channel`, `guild`, `thread`
- Адаптер должен отвечать за отображение нативных типов платформ на стандартные типы

### 2.2 Поля сообщений
| Поле | Тип | Описание |
|------|------|------|
| message | array | Массив сегментов сообщения |
| alt_message | string | Резервный текст сегментов сообщения |
| user_id | string | User ID |
| user_nickname | string | Никнейм пользователя (необязательно) |

### 2.3 Поля уведомлений
| Поле | Тип | Описание |
|------|------|------|
| user_id | string | User ID |
| user_nickname | string | Никнейм пользователя (необязательно) |
| operator_id | string | ID оператора (необязательно) |

### 2.4 Поля запросов
| Поле | Тип | Описание |
|------|------|------|
| user_id | string | User ID |
| user_nickname | string | Никнейм пользователя (необязательно) |
| comment | string | Комментарий к запросу (необязательно) |
| request_id | string | Идентификатор запроса (сильно рекомендуется, для операций принятия/отклонения) |

**Объяснение поля `request_id`**:
- `request_id` — это уникальный идентификатор операции для событий запроса, используется для выполнения операций принятия/отклонения через DSL `HandleRequest`.
- При преобразовании события запроса адаптер должен сопоставить нативный идентификатор запроса платформы с этим полем.
- Если платформа сама по себе не имеет идентификатора запроса, адаптер должен сгенерировать уникальный идентификатор (например, хеш на основе временной метки + user_id).
- Когда `request_id` отсутствует, `event.approve()` / `event.reject()` выбросят `ValueError`.

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

Типы стандартных сегментов сообщений **не должны** иметь префикс платформы:

| Тип | Описание | Поля данных |
|------|------|----------|
| `text` | Текст | `text: str` |
| `image` | Изображение | `file: str/bytes`, `url: str` |
| `audio` | Аудио | `file: str/bytes`, `url: str` |
| `video` | Видео | `file: str/bytes`, `url: str` |
| `file` | Файл | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | Упоминание пользователя | `user_id: str`, `user_name: str` |
| `reply` | Ответ | `message_id: str` |
| `face` | Смайлик | `id: str` |
| `location` | Местоположение | `latitude: float`, `longitude: float` |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.2 Расширенные сегменты сообщений платформ

Платформенно-специфичные сегменты сообщений должны иметь префикс платформы:

```json
// 云湖 - Форма
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "报名表"}}

// Telegram - Стикер
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**Требования к расширенным сегментам**:
1. **Внутри полей `data` не добавлять префикс**: `{"type": "yunhu_form", "data": {"form_id": "..."}}` вместо `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **Предоставлять план downgrade**: модуль может не распознавать расширенные сегменты, адаптер должен предоставлять текстовую замену в `alt_message`.
3. **Полнота документации**: каждый расширенный сегмент должен быть описан в документации адаптера с указанием `type`, структуры `data` и сценария использования.

## 5. Обработка неизвестных событий

Для типов событий, которые не могут быть распознаны, должны создаваться события предупреждения:
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

## 6. Спецификации именования расширений

### 6.1 Именование полей

**Правило**: `{platform}_{field_name}`

```
Префикс платформы    Имя поля            Полное имя поля
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**Требования**:
- `platform` должно точно совпадать с именем платформы при регистрации адаптера (с учетом регистра).
- `field_name` использует именование `snake_case`.
- Запрещено использовать двойное подчеркивание в начале `__` (зарезервировано Python).
- Запрещено иметь то же имя, что и стандартные поля (например, `type`, `time`, `message` и т.д.).

### 6.2 Именование типов сегментов сообщений

**Правило**: `{platform}_{segment_type}`

Типы стандартных сегментов сообщений (`text`, `image`, `audio`, `video`, `mention`, `reply` и т.д.) **не должны** иметь префикс платформы. Требуется добавлять префикс только для типов сегментов сообщений, уникальных для платформы.

### 6.3 Именование полей исходных данных

Ниже приведены имена полей **сохраняемых полей**, которые все адаптеры должны соблюдать:

| Сохраняемое поле | Тип | Описание |
|---------|------|------|
| `{platform}_raw` | `any` | Полная копия исходных данных события платформы |
| `{platform}_raw_type` | `string` | Строковый идентификатор исходного типа события платформы |

**Требования**:
- `{platform}_raw` должен быть глубокой копией исходных данных, а не ссылкой.
- `{platform}_raw_type` должен быть строкой, даже если платформа использует числовой тип, он должен быть преобразован в строку.
- Эти два поля **обязательны** для всех событий (если не удается получить, то `null` и пустая строка `""`).

### 6.4 Примеры полей платформы

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

**Требования для вложенных полей**:
- Ключи верхнего уровня должны иметь префикс платформы.
- Внутренние поля вложения **не должны** иметь префикс платформы.
- Рекомендуемая глубина вложения не более 3 уровней.

### 6.6 Расширение поля `self`

Стандартные обязательные поля объекта `self` (`platform`, `user_id`) см. §2.1. Ниже приведены необязательные поля расширений ErisPulse:

| Поле | Тип | Описание |
|------|------|------|
| `self.user_name` | `string` | Никнейм бота |
| `self.avatar` | `string` | URL аватара бота |
| `self.account_id` | `string` | Идентификатор учетной записи в режиме нескольких аккаунтов |

> **Отслеживание статуса бота**: Адаптер сообщает фреймворку о статусе соединения бота через отправку события `type: "meta"`. Поддерживаемые `detail_type`: `connect` (подключение), `heartbeat` (сердцебиение), `disconnect` (отключение). Система автоматически извлекает метаданные бота из поля `self` для отслеживания состояния. Кроме того, поле `self` в обычных событиях также автоматически обнаруживается ботом. Подробнее см. [API системы адаптера - Управление статусом бота](../api-reference/adapter-system.md).

---

## 7. Расширения типов сессий

ErisPulse расширил следующие типы сессий на основе стандартов OneBot12 `private`, `group`:

| Тип | OneBot12 Стандарт | Расширение ErisPulse | Описание |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | Личный чат |
| `group` | ✅ | — | Групповой чат |
| `user` | — | ✅ | Тип пользователя (Telegram и т.д.) |
| `channel` | — | ✅ | Канал (вещательный) |
| `guild` | — | ✅ | Сервер / Сообщество |
| `thread` | — | ✅ | Тема / Подканал |

**Расширения пользовательских типов адаптера**:

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# Регистрация при запуске адаптера
register_custom_type(
    receive_type="email",      # detail_type в событии получения
    send_type="email",         # целевой тип при отправке
    id_field="email_id",       # имя соответствующего поля ID
    platform="email"           # идентификатор платформы
)
```

**Требования к пользовательским типам**:
- Должны быть зарегистрированы при запуске адаптера `start()` и отменены при `shutdown()`.
- `receive_type` не должно совпадать с именем стандартного типа.
- `id_field` должен следовать шаблону именования `{target}_id`.

> Полное определение типов сессий и отношения сопоставления см. в [Стандарте типов сессий](session-types.md).

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

    # Доступ к расширенным полям платформы - способ 1: прямое get
    yunhu_command = event.get("yunhu_command")

    # Доступ к расширенным полям платформы - способ 2: точечный доступ (класс Event)
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

1. **Приоритет использования стандартных полей**: Не предполагайте, что расширенные поля обязательно существуют.
2. **Определение платформы**: Определяйте платформу через `event.get_platform()`, а не по наличию расширенных полей.
3. **Умный downgrade**: Если расширенный сегмент сообщения не может быть обработан, используйте `alt_message` как запасной вариант.
4. **Не используйте хардкод префиксов**: Динамически конкатенируйте с помощью переменной `platform`.

```python
# ✅ Рекомендуется
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ Не рекомендуется
raw_data = event.get("yunhu_raw")
```

### 8.4 Обработка событий запросов

Разработчики модулей могут выполнять операции над событиями запроса через `event.approve()` и `event.reject()`:

```python
from ErisPulse.Core.Event import request

# Запрос в друзья: автоматическое принятие
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # Принятие запроса
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"已同意 {user_name} 的好友请求")
    else:
        print(f"同意好友请求失败: {result.get('message')}")

# Приглашение в группу: решение по условию
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # Отклонение запроса
    result = await event.reject(comment="暂不加入新群")
```

**Непосредственное выполнение через адаптер** (подходит для сценариев, не являющихся обработчиками событий):

```python
from ErisPulse import adapter

# Непосредственная операция через request_id
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Операция с указанием учетной записи бота
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# С примечанием
await adapter.myplatform.Request("req_abc123").accept(comment="欢迎")
```

---

## 9. Вывод типа сессии для событий notice / request

### 9.1 Контекст проблемы

`detail_type` событий notice и request являются **семантическими подтипами** (например, `group_member_increase`, `friend_increase`), а не типами сессии (например, `group`, `private`).

```
type        detail_type                  Смысл            Тип сессии
────        ───────────                  ────            ────────
message     group                        Сообщение в группе  group (detail_type = тип сессии)
message     private                      Личное сообщение  private (detail_type = тип сессии)
notice      group_member_increase        Увеличение участника группы group (выводится из group_id)
notice      friend_increase              Увеличение друзей private (выводится из user_id)
request     friend                       Запрос в друзья private (выводится из user_id)
request     group                        Запрос в группу group (detail_type = тип сессии)
```

### 9.2 Правила вывода

Порядок вывода `infer_receive_type()`:

1. Если `detail_type` является известным типом сессии (`private`/`group`/`channel`/`guild`/`thread`/`user`), используйте его напрямую.
2. Если `detail_type` является пользовательским типом сессии, используйте его напрямую.
3. В противном случае (семантические подтипы notice/request), выведите на основе полей ID:
   - Есть `group_id` → `"group"`
   - Есть `channel_id` → `"channel"`
   - Есть `guild_id` → `"guild"`
   - Есть `thread_id` → `"thread"`
   - Есть `user_id` → `"private"`

### 9.3 Вывод цели для `event.reply()`

Цель отправки `event.reply()` в событиях notice/request определяется выводом типа сессии:

- Событие уведомления группы (содержащее `group_id`) → Ответ в **группу**
- Событие уведомления друга (содержащее только `user_id`) → Ответ в **личный чат пользователя**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() отправляется в группу (group/group_789)
    await event.reply("欢迎入群！")

    # Для уведомления администратора (личный чат), явно укажите цель:
    await adapter.Send.To("user", "admin_id").Text(f"新成员 {user_id} 加入了 {group_id}")
```

### 9.4 Рекомендации для разработчиков адаптеров

Убедитесь, что события notice/request содержат правильные поля ID:

| detail_type | Обязательные поля ID | Вывод типа сессии |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend` (запрос) | `user_id` | `private` |
| `group` (запрос) | `group_id` | `group` |

---

## 10. Связанные документы

- [Документы особенностей платформ](../platform-guide/README.md) - Вы можете обратиться к этому документу, чтобы узнать о возможностях различных платформ, а также известных расширенных событиях и сегментах сообщений.
- [Стандарт типов сессий](session-types.md) - Определения и отношения отображения типов сессий
- [Спецификация методов отправки](send-method-spec.md) - Имена методов, спецификации параметров класса Send и требования к обратному преобразованию
- [Стандарт ответов API](api-response.md) - Стандарт формата ответов API адаптера
- [Стандарт действий API](api-action-spec.md) - Унифицированный интерфейс стандартных действий API OneBot12