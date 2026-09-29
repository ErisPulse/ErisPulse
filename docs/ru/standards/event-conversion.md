# Стандартизированные правила преобразования адаптеров

## 1. Основные принципы
1. Строгое соответствие: все стандартные поля должны полностью соответствовать спецификации OneBot12.
2. Ясное расширение: платформенные расширения должны иметь префикс `{platform}_` (например, yunhu_form).
3. Полная сохранность данных: исходные данные события должны сохраняться в поле `{platform}_raw`, а тип исходного события — в поле `{platform}_raw_type`.
4. Единое время: все временные метки должны быть преобразованы в 10-значные Unix-время (в секундах).
5. Единое имя платформы: поле `platform` должно соответствовать зарегистрированному в ErisPulse имени/алиасу платформы.

## 2. Требования к стандартным полям

### 2.1 Обязательные поля
| Поле | Тип | Описание |
|------|------|------|
| id | string | Уникальный идентификатор события |
| time | integer | Unix-время (в секундах) |
| type | string | Тип события |
| detail_type | string | Подтип события (см. [Стандарт типов сессий](session-types.md)) |
| platform | string | Название платформы |
| self | object | Информация о боте |
| self.platform | string | Название платформы |
| self.user_id | string | Идентификатор пользователя бота |

**Правила для `detail_type`:**
- Должен использовать стандартные типы сессий ErisPulse (см. [Стандарт типов сессий](session-types.md))
- Поддерживаемые типы: `private`, `group`, `user`, `channel`, `guild`, `thread`
- Адаптер должен отображать платформенные типы в стандартные

### 2.2 Поля для событий сообщений
| Поле | Тип | Описание |
|------|------|------|
| message | array | Массив сообщений |
| alt_message | string | Текстовое представление сообщений (резервное) |
| user_id | string | Идентификатор пользователя |
| user_nickname | string | Имя пользователя (опционально) |

### 2.3 Поля для уведомлений
| Поле | Тип | Описание |
|------|------|------|
| user_id | string | Идентификатор пользователя |
| user_nickname | string | Имя пользователя (опционально) |
| operator_id | string | Идентификатор оператора (опционально) |

### 2.4 Поля для запросов
| Поле | Тип | Описание |
|------|------|------|
| user_id | string | Идентификатор пользователя |
| user_nickname | string | Имя пользователя (опционально) |
| comment | string | Комментарий к запросу (опционально) |
| request_id | string | Идентификатор запроса (рекомендуется) |

**Объяснение `request_id`:**
- `request_id` — уникальный идентификатор запроса, используется для подтверждения/отклонения запроса через DSL `HandleRequest`
- Адаптер должен сопоставлять платформенный идентификатор запроса с этим полем
- Если платформа не предоставляет `request_id`, адаптер должен сгенерировать уникальный идентификатор (например, хэш из timestamp и user_id)
- При отсутствии `request_id` методы `event.approve()` / `event.reject()` выбросят `ValueError`

## 3. Примеры форматов событий

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
        "text": "Розыгрыш: Суперприз"
      }
    }
  ],
  "alt_message": "Розыгрыш: Суперприз",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "Розыгрыш",
    "args": "Суперприз"
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
  "comment": "Пожалуйста, добавьте в друзья",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. Стандартные сообщения

### 4.1 Стандартные сообщения

Стандартные сообщения **не требуют** платформенного префикса.

| Тип | Описание | Поля data |
|------|------|----------|
| `text` | Текст | `text: str` |
| `image` | Изображение | `file`, `url: str` |
| `audio` | Аудио | `file`, `url: str` |
| `video` | Видео | `file`, `url: str` |
| `file` | Файл | `file`, `url: str`, `filename: str` |
| `mention` | Упоминание | `user_id: str`, `user_name: str` |
| `reply` | Ответ | `message_id: str` |
| `face` | Эмодзи | `id: str` |
| `location` | Местоположение | `latitude: float`, `longitude: float` |
| `keyboard` | Кнопки/инлайн-клавиатура | `rows: list[list[button]]` (см. 4.1.1) |

**Форматы поля `file` для медиа (направление отправки):**
| Формат | Пример | Требования адаптера |
|------|------|-----------|
| URL (HTTP(S)) | `https://example.com/a.png` | **Обязательно** |
| Локальный путь | `/tmp/a.png`, `C:\tmp\a.png` | **Обязательно** |
| Бинарные данные | `bytes` | **Обязательно** |
| URI `file://` / Base64 / Data URI | `file:///tmp/a.png`, `data:image/png;base64,...` | **Рекомендуется** |

> Полный протокол отправки медиа (порядок определения формата, вывод имени файла, понижение приоритетов) см. в [Спецификации методов отправки §2.1](send-method-spec.md#21-протокол-отправки-медиа-image--voice--video--file).

**Семантика направления полей:**

- `file`: **Направление отправки** — источник содержимого (см. выше); **Направление получения** — адаптер заполняет доступные платформе формы (обычно URL для скачивания или идентификатор ресурса для `get_file`)
- `url`: **Направление получения** — обратная ссылка платформы (адаптер заполняет при преобразовании событий платформы, чтобы модули могли напрямую использовать); **Направление отправки** — не обязательно
- `filename`: Имя файла для сегмента `file` (направление отправки — необязательно, если отсутствует, адаптер генерирует по [Спецификации методов отправки §2.1.3](send-method-spec.md); направление получения — **обязательно** заполнять оригинальное имя файла платформы)

```json
{
  "type": "text",
  "data": {
    "text": "Привет, мир"
  }
}
```

### 4.1.1 Сегмент `keyboard` (кнопки/инлайн-клавиатура, универсальный)

Кнопки/инлайн-клавиатура есть на многих платформах (Telegram / Yunhu / QQBot / Kook / Discord и др.), и это **универсальное понятие**, поэтому оно является стандартным сегментом (без платформенного префикса). Адаптер должен преобразовывать стандартный сегмент в платформенный формат; платформенные расширения (например, `telegram_inline_keyboard`) продолжают оставаться в прозрачном режиме.

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "Вариант A", "type": "callback", "data": "vote:A"},
        {"label": "Сайт", "type": "link", "data": "https://example.com"}
      ]
    ]
  }
}
```

**Описание полей:**

| Поле | Тип | Обязательно | Описание |
|------|------|------|------|
| `rows` | Двумерный массив | Да | Каждый подмассив — строка кнопок |
| `rows[][].label` | str | Да | Текст кнопки |
| `rows[][].type` | str | Да | `callback` (отправка данных при нажатии) / `link` (переход по URL) |
| `rows[][].data` | str | Да | Данные для callback (type=callback) или URL (type=link) |
| `rows[][].*` | Any | Нет | Платформенные дополнительные поля (например, `web_app`, `menus`), адаптер отображает или игнорирует |

**Примеры преобразования адаптера (полное отображение и стандарты взаимодействия с компонентами смотрите в [Стандарте кросс-платформенных компонентов взаимодействия](standardization-guide.md)):**

| Платформа | Стандартный сегмент → Платформенный |
|------|------------------|
| Telegram | `inline_keyboard`: `[{text, callback_data \| url}]` |
| Yunhu | `buttons`: `[{label, action_type: 2=callback \| 1=link, ...}]` |
| QQBot | `keyboard.content.rows`: `[{label, type: 2=callback \| 0=link, data}]` (требуется сообщение в формате markdown) |
| Kook | Модуль action-group в карточке |
| Discord | components: `action_row` + `buttons` (custom_id/url) |

### 4.2 Расширения сообщений платформы

Сегменты сообщений, специфичные для платформы, должны иметь платформенный префикс:

```json
// Yunhu - форма
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "Форма регистрации"}}

// Telegram - стикер
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**Требования к расширенным сегментам:**
1. **Поля внутри `data` не имеют префикса**: `{"type": "yunhu_form", "data": {"form_id": "..."}}`, а не `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **Предоставление резервного варианта**: Модуль может не распознавать расширенные сегменты, адаптер должен в `alt_message` предоставить текстовый резерв
3. **Документация**: Каждый расширенный сегмент должен быть описан в документации адаптера, включая `type`, структуру `data` и сценарии использования

## 5. Обработка неизвестных событий

Для неизвестных типов событий следует генерировать событие предупреждения:
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "Не поддерживаемый тип события: special_event",
  "alt_message": "Этот тип события не поддерживается данной системой."
}
```

---

## 6. Правила расширения именования

### 6.1 Именование полей

**Правило**: `{platform}_{field_name}`

```
Платформенный префикс    Имя поля            Полное имя поля
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**Требования:**
- `platform` должен полностью соответствовать зарегистрированному в адаптере имени платформы (чувствительно к регистру)
- `field_name` следует именовать в стиле `snake_case`
- Запрещено использовать двойное подчеркивание `__` в начале (зарезервировано Python)
- Запрещено использовать имена стандартных полей (например, `type`, `time`, `message` и т.д.)

### 6.2 Именование типов сегментов сообщений

**Правило**: `{platform}_{segment_type}`

Стандартные типы сегментов (`text`, `image`, `audio`, `video`, `mention`, `reply` и т.д.) **не должны** иметь платформенного префикса. Только платформенные специфичные типы сегментов сообщений должны иметь префикс.

### 6.3 Именование полей исходных данных

Следующие имена полей являются **зарезервированными**, и все адаптеры должны их соблюдать:

| Зарезервированное поле | Тип | Описание |
|---------|------|------|
| `{platform}_raw` | `any` | Полная копия исходных данных события платформы |
| `{platform}_raw_type` | `string` | Идентификатор типа исходного события платформы |

**Требования:**
- `{platform}_raw` должен быть глубокой копией исходных данных, а не ссылкой
- `{platform}_raw_type` должен быть строкой, даже если платформа использует числовые типы, они должны быть преобразованы в строки
- Эти два поля должны **всегда** присутствовать во всех событиях (если данные недоступны, устанавливать `null` и пустую строку `""`)

### 6.4 Примеры платформенных полей

```json
{
  "yunhu_command": {
    "name": "Розыгрыш",
    "args": "Суперприз"
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
    "title": "Моя группа"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**Требования к вложенным полям:**
- Верхний уровень ключей должен иметь платформенный префикс
- Вложенные внутренние поля **не должны** иметь платформенного префикса
- Рекомендуемая глубина вложения не превышает 3 уровней

### 6.6 Расширение поля `self`

Стандартные обязательные поля в объекте `self` (см. §2.1): `platform`, `user_id`. Ниже перечислены расширения ErisPulse, которые являются необязательными:

| Поле | Тип | Описание |
|------|------|------|
| `self.user_name` | `string` | Имя бота |
| `self.avatar` | `string` | URL аватара бота |
| `self.account_id` | `string` | Идентификатор аккаунта в режиме нескольких аккаунтов |

> **Отслеживание состояния бота**: Адаптер сообщает фреймворку о состоянии бота, отправляя событие `type: "meta"`. Поддерживаемые `detail_type`: `connect` (вход), `heartbeat` (сердцебиение), `disconnect` (выход). Система автоматически извлекает информацию о боте из поля `self` для отслеживания состояния. Кроме того, поле `self` в обычных событиях также автоматически обнаруживает бота. Подробнее см. [API адаптера - Управление состоянием бота](../api-reference/adapter-system.md).

---

## 7. Расширение типов сессий

ErisPulse расширяет стандартные OneBot12 типы `private`, `group` следующими типами сессий:

| Тип | OneBot12 стандарт | Расширение ErisPulse | Описание |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | Личный чат |
| `group` | ✅ | — | Групповой чат |
| `user` | — | ✅ | Тип пользователя (Telegram и др.) |
| `channel` | — | ✅ | Канал (вещание) |
| `guild` | — | ✅ | Сервер/сообщество |
| `thread` | — | ✅ | Тема/подканал |

**Расширение типов сессий адаптером:**

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# Регистрация при запуске адаптера
register_custom_type(
    receive_type="email",      # detail_type в событии получения
    send_type="email",         # тип цели при отправке
    id_field="email_id",       # соответствующее поле ID
    platform="email"           # идентификатор платформы
)
```

**Требования к пользовательским типам:**
- Должны быть зарегистрированы при запуске адаптера, и отменены при остановке
- `receive_type` не должен совпадать с уже существующими стандартными типами
- `id_field` должен соответствовать шаблону `{цель}_id`

> Полное определение и сопоставление типов сессий см. в [Стандарте типов сессий](session-types.md).

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

    # Доступ к платформенным расширенным полям - способ 1: прямой get
    yunhu_command = event.get("yunhu_command")

    # Доступ к платформенным расширенным полям - способ 2: точечный доступ (обёртка Event)
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

### 8.2 Обработка расширенных сообщений

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

1. **Предпочтительное использование стандартных полей**: Не предполагайте, что расширенные поля обязательно существуют
2. **Определение платформы**: Используйте `event.get_platform()` для определения платформы, а не проверку наличия расширенных полей
3. **Гладкое понижение**: При невозможности обработки расширенных сегментов используйте `alt_message` как резерв
4. **Не жёстко кодируйте префиксы**: Используйте переменную `platform` для динамического составления

```python
# ✅ Рекомендуется
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ Не рекомендуется
raw_data = event.get("yunhu_raw")
```

### 8.4 Обработка запросов

Разработчики модулей могут использовать `event.approve()` и `event.reject()` для обработки запросов:

```python
from ErisPulse.Core.Event import request

# Автоматическое принятие запроса на добавление в друзья
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # Принять запрос
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"Принято добавление {user_name} в друзья")
    else:
        print(f"Ошибка принятия запроса: {result.get('message')}")

# Запрос на группу: решение на основе условий
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # Отклонить запрос
    result = await event.reject(comment="Временно не присоединяюсь к новым группам")
```

**Прямое управление через адаптер** (для сценариев, не связанных с обработчиками событий):

```python
from ErisPulse import adapter

# Прямое управление по request_id
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Указание аккаунта бота
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# С комментарием
await adapter.myplatform.Request("req_abc123").accept(comment="Добро пожаловать")
```

---

## 9. Вывод типа сессии для событий notice / request

### 9.1 Проблемный фон

Типы `detail_type` для событий `notice` и `request` являются **семантическими подтипами** (например, `group_member_increase`, `friend_increase`), а не типами сессии (например, `group`, `private`).

```
type        detail_type                  Смысл            Тип сессии
────        ───────────                  ────            ────────
message     group                        Сообщение в группе         group (detail_type как тип сессии)
message     private                      Личное сообщение         private (detail_type как тип сессии)
notice      group_member_increase        Увеличение участников группы       group (выводится по group_id)
notice      friend_increase              Увеличение друзей         private (выводится по user_id)
request     friend                       Запрос на добавление в друзья         private (выводится по user_id)
request     group                        Запрос на вступление в группу           group (detail_type как тип сессии)
```

### 9.2 Правила вывода

Порядок вывода `infer_receive_type()`:

1. Если `detail_type` является известным типом сессии (`private`/`group`/`channel`/`guild`/`thread`/`user`), используйте его напрямую
2. Если `detail_type` является пользовательским типом сессии, используйте его напрямую
3. В противном случае (семантические подтипы `notice`/`request`), выведите тип сессии по ID-полям:
   - Наличие `group_id` → `"group"`
   - Наличие `channel_id` → `"channel"`
   - Наличие `guild_id` → `"guild"`
   - Наличие `thread_id` → `"thread"`
   - Наличие `user_id` → `"private"`

### 9.3 Вывод цели `event.reply()`

Цель отправки `event.reply()` в событиях `notice`/`request` определяется типом сессии:

- События уведомления о группе (с `group_id`) → отправка в **группу**
- События уведомления о друзьях (только `user_id`) → отправка в **личный чат**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() отправляется в группу (group/group_789)
    await event.reply("Добро пожаловать!")

    # Если нужно уведомить администратора (личный чат), явно укажите цель:
    await adapter.Send.To("user", "admin_id").Text(f"Новый участник {user_id} присоединился к {group_id}")
```

### 9.4 Рекомендации для разработчиков адаптеров

Убедитесь, что события `notice`/`request` содержат правильные ID-поля:

| detail_type | Обязательные ID-поля | Выведенный тип сессии |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend` (запрос) | `user_id` | `private` |
| `group` (запрос) | `group_id` | `group` |

---

## 10. Связанные документы

- [Документация по особенностям платформ](../platform-guide/README.md) - Вы можете посетить этот документ, чтобы узнать особенности каждой платформы, а также известные расширенные события и сегменты сообщений.
- [Стандарт типов сессий](session-types.md) - Определения и сопоставления типов сессий
- [Спецификация методов отправки](send-method-spec.md) - Названия методов Send, стандарт параметров и требования к обратному преобразованию
- [Стандарт ответов API](api-response.md) - Стандарт формата ответов API адаптера
- [Стандарт действий API](api-action-spec.md) - Единый интерфейс для действий API OneBot12