# Стандартизированный протокол преобразования адаптеров

## 1. Основные принципы
1. Строгое соответствие: все стандартные поля должны полностью соответствовать спецификации OneBot12.
2. Четкое расширение: платформенно-специфичные функции должны иметь префикс {platform}_ (например, yunhu_form).
3. Полнота данных: исходные данные события должны сохраняться в поле {platform}_raw, а исходный тип события — в поле {platform}_raw_type.
4. Единообразие времени: все временные метки должны быть преобразованы в 10-значный Unix-время-штамп (в секундах).
5. Единообразие платформы: имя поля platform должно совпадать с названием/алиасом, зарегистрированным в ErisPulse.

## 2. Требования к стандартным полям

### 2.1 Обязательные поля
| Поле | Тип | Описание |
|------|------|------|
| id | string | Уникальный идентификатор события |
| time | integer | Unix-время (секунды) |
| type | string | Тип события |
| detail_type | string | Подробный тип события (см. [Стандарт типов сессий](docs/ru/session-types.md)) |
| platform | string | Название платформы |
| self | object | Информация о боте |
| self.platform | string | Название платформы |
| self.user_id | string | ID пользователя бота |

**Правила для `detail_type`**:
- Должен использовать стандартные типы сессий ErisPulse (см. [Стандарт типов сессий](docs/ru/session-types.md))
- Поддерживаемые типы: `private`, `group`, `user`, `channel`, `guild`, `thread`
- Адаптер отвечает за преобразование типов платформы в стандартные типы

### 2.2 Поля событий сообщений
| Поле | Тип | Описание |
|------|------|------|
| message | array | Массив сегментов сообщения |
| alt_message | string | Альтернативный текст сообщения |
| user_id | string | ID пользователя |
| user_nickname | string | Никнейм пользователя (необязательно) |

### 2.3 Поля событий уведомлений
| Поле | Тип | Описание |
|------|------|------|
| user_id | string | ID пользователя |
| user_nickname | string | Никнейм пользователя (необязательно) |
| operator_id | string | ID оператора (необязательно) |

### 2.4 Поля событий запросов
| Поле | Тип | Описание |
|------|------|------|
| user_id | string | ID пользователя |
| user_nickname | string | Никнейм пользователя (необязательно) |
| comment | string | Комментарий к запросу (необязательно) |
| request_id | string | Идентификатор запроса (рекомендуется) — используется для подтверждения/отклонения запроса |

**Описание поля `request_id`**:
- `request_id` — уникальный идентификатор запроса, используемый для подтверждения/отклонения запроса через DSL `HandleRequest`
- Адаптер должен преобразовывать идентификатор запроса платформы в это поле
- Если платформа не предоставляет идентификатор запроса, адаптер должен сгенерировать уникальный идентификатор (например, хэш из временной метки и ID пользователя)
- При отсутствии `request_id` методы `event.approve()` / `event.reject()` выбросят исключение `ValueError`

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
        "text": "Розыгрыш суперприза"
      }
    }
  ],
  "alt_message": "Розыгрыш суперприза",
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

## 4. Стандартные элементы сообщений

### 4.1 Стандартные элементы сообщений

Стандартные элементы сообщений **не требуют** префикса платформы.

| Тип | Описание | Поля data |
|------|------|----------|
| `text` | Чистый текст | `text: str` |
| `image` | Изображение | `file: str/bytes`, `url: str` |
| `audio` | Аудио | `file: str/bytes`, `url: str` |
| `video` | Видео | `file: str/bytes`, `url: str` |
| `file` | Файл | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | Упоминание пользователя | `user_id: str`, `user_name: str` |
| `reply` | Ответ на сообщение | `message_id: str` |
| `face` | Эмодзи | `id: str` |
| `location` | Местоположение | `latitude: float`, `longitude: float` |
| `keyboard` | Кнопки / встроенная клавиатура | `rows: list[list[button]]` (см. 4.1.1) |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 Элемент клавиатуры/встроенной клавиатуры (keyboard) (универсальный для всех платформ)

Кнопки / встроенная клавиатура присутствуют на многих платформах (Telegram / Yunhu / QQBot / Kook / Discord и др.), и являются **универсальной концепцией**, поэтому они представлены как стандартный элемент сообщения (без префикса платформы). Адаптеры должны преобразовывать стандартный элемент в структуру, специфичную для платформы; расширенные элементы платформы (например, `telegram_inline_keyboard`) должны сохраняться и передаваться без изменений.

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "Опция A", "type": "callback", "data": "vote:A"},
        {"label": "Официальный сайт", "type": "link", "data": "https://example.com"}
      ]
    ]
  }
}
```

**Описание полей:**

| Поле | Тип | Обязательно | Описание |
|------|------|------|------|
| `rows` | Двумерный массив | Да | Каждый подмассив представляет строку кнопок |
| `rows[][].label` | str | Да | Текст, отображаемый на кнопке |
| `rows[][].type` | str | Да | `callback` (отправка данных при нажатии) / `link` (переход по URL) |
| `rows[][].data` | str | Да | Данные для обратного вызова (type=callback) или адрес перехода (type=link) |
| `rows[][].*` | Any | Нет | Платформенно-специфичные дополнительные поля (например, `web_app`, `menus`), адаптер должен соответствующим образом сопоставлять или игнорировать их |

**Примеры преобразования адаптера** (полное сопоставление и стандартные события обратного вызова для межплатформенной взаимодействия см. в [стандарте межплатформенных компонентов взаимодействия](standardization-guide.md)):

| Платформа | Стандартный элемент → платформенно-специфичный |
|------|------------------|
| Telegram | `inline_keyboard`: `[{text, callback_data \| url}]` |
| Yunhu | `buttons`: `[{label, action_type: 2=callback \| 1=link, ...}]` |
| QQBot | `keyboard.content.rows`: `[{label, type: 2=callback \| 0=link, data}]` (требуется сообщение в формате markdown) |
| Kook | Модуль action-group в карточке |
| Discord | components: `action_row` + `buttons` (custom_id/url) |

### 4.2 Расширенные элементы сообщений платформы

Специфичные для платформы элементы сообщений должны иметь префикс платформы:

```json
// Yunhu - форма
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "Форма регистрации"}}

// Telegram - стикер
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**Требования к расширенным элементам сообщений:**
1. **Поля внутри data не имеют префикса**: `{"type": "yunhu_form", "data": {"form_id": "..."}}`, а не `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **Обеспечение обратной совместимости**: Модуль может не распознавать расширенный элемент сообщения, адаптер должен предоставить текстовую альтернативу в `alt_message`
3. **Полная документация**: Каждый расширенный элемент сообщения должен быть подробно описан в документации адаптера, включая структуру `type`, `data` и сценарии использования

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

## 6. Расширение соглашений об именах

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
- `platform` должен полностью соответствовать имени платформы при регистрации адаптера (чувствительность к регистру)
- `field_name` используется в стиле `snake_case`
- Запрещено использовать двойное подчеркивание `__` в начале (зарезервировано Python)
- Запрещено использовать имена, совпадающие со стандартными полями (например `type`, `time`, `message` и т.д.)

### 6.2 Именование типов сегментов сообщений

**Правило**: `{platform}_{segment_type}`

Стандартные типы сегментов сообщений (`text`, `image`, `audio`, `video`, `mention`, `reply` и т.д.) **не должны** иметь префикса платформы. Только уникальные типы сегментов сообщений, специфичные для платформы, требуют префикса.

### 6.3 Именование полей исходных данных

Следующие имена полей являются **зарезервированными**, и все адаптеры должны следовать этим требованиям:

| Зарезервированное поле | Тип | Описание |
|---------|------|------|
| `{platform}_raw` | `any` | Полная копия исходных данных события платформы |
| `{platform}_raw_type` | `string` | Идентификатор типа исходного события платформы |

**Требования**:
- `{platform}_raw` должен быть глубокой копией исходных данных, а не ссылкой
- `{platform}_raw_type` должен быть строкой, даже если платформа использует числовой тип, его нужно преобразовать в строку
- Эти два поля **должны** присутствовать во всех событиях (если данные недоступны, использовать `null` и пустую строку `""`)

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
- Ключи верхнего уровня должны иметь префикс платформы
- Вложенные внутренние поля **не должны** иметь префикса платформы
- Рекомендуемая глубина вложенности не превышает 3 уровня

### 6.6 Расширение поля `self`

Стандартные обязательные поля объекта `self` (`platform`, `user_id`) см. в §2.1. Ниже перечислены дополнительные поля, расширенные ErisPulse:

| Поле | Тип | Описание |
|------|------|------|
| `self.user_name` | `string` | Ник бота |
| `self.avatar` | `string` | URL аватара бота |
| `self.account_id` | `string` | Идентификатор аккаунта в режиме мультиаккаунта |

> **Отслеживание состояния бота**: Адаптер сообщает фреймворку о состоянии подключения бота, отправляя событие `type: "meta"`. Поддерживаемые `detail_type`: `connect` (онлайн), `heartbeat` (пинг), `disconnect` (оффлайн). Система автоматически извлекает метаинформацию о боте из поля `self` для отслеживания состояния. Кроме того, объект `self` в обычных событиях также автоматически обнаруживается как бот. Подробнее см. [API системы адаптеров - Управление состоянием бота](../api-reference/adapter-system.md).

---

## 7. Расширение типов сессий

ErisPulse расширяет стандарт OneBot12, добавляя следующие типы сессий на основе `private` и `group`:

| Тип | Стандарт OneBot12 | Расширение ErisPulse | Описание |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | Личный чат один на один |
| `group` | ✅ | — | Групповой чат |
| `user` | — | ✅ | Тип пользователя (Telegram и др.) |
| `channel` | — | ✅ | Канал (вещание) |
| `guild` | — | ✅ | Сервер/сообщество |
| `thread` | — | ✅ | Тема/подканал |

**Расширение пользовательских типов адаптера**:

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# Регистрация при запуске адаптера
register_custom_type(
    receive_type="email",      # detail_type в событии получения
    send_type="email",         # тип цели при отправке
    id_field="email_id",       # соответствующее имя поля ID
    platform="email"           # идентификатор платформы
)
```

**Требования к пользовательским типам**:
- Должны быть зарегистрированы при запуске адаптера и отменены при его остановке
- `receive_type` не должен совпадать с именем стандартного типа
- `id_field` должен соответствовать шаблону `{цель}_id`

> Полное определение и сопоставление типов сессий см. в [Стандарте типов сессий](session-types.md).

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

    # Доступ к расширенным полям платформы - способ 2: точечный доступ (обёртка Event)
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

1. **Предпочитайте стандартные поля**: не предполагайте, что расширенные поля обязательно существуют
2. **Определение платформы**: используйте `event.get_platform()` для определения платформы, а не определение по наличию расширенных полей
3. **Грациозное понижение**: при невозможности обработки расширенных сегментов сообщений используйте `alt_message` в качестве резервного варианта
4. **Не жёстко кодируйте префиксы**: используйте переменную `platform` для динамического составления

```python
# ✅ Рекомендуется
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ Не рекомендуется
raw_data = event.get("yunhu_raw")
```

### 8.4 Обработка событий запросов

Разработчики модулей могут использовать `event.approve()` и `event.reject()` для обработки запросов:

```python
from ErisPulse.Core.Event import request

# Запрос на добавление в друзья: автоматическое принятие
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # Принятие запроса
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"Запрос на добавление в друзья от {user_name} принят")
    else:
        print(f"Ошибка принятия запроса на добавление в друзья: {result.get('message')}")

# Запрос на вступление в группу: принятие или отклонение в зависимости от условий
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # Отклонение запроса
    result = await event.reject(comment="Временно не присоединяюсь к новым группам")
```

**Операции напрямую через адаптер** (подходит для сценариев, не связанных с обработчиками событий):

```python
from ErisPulse import adapter

# Прямое управление по request_id
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Указание аккаунта бота для выполнения операции
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# Принятие с комментарием
await adapter.myplatform.Request("req_abc123").accept(comment="Добро пожаловать")
```

## 9. Вывод типа сессии для событий notice / request

### 9.1 Проблема

Типы `detail_type` для событий `notice` и `request` являются **семантическими подтипами** (например, `group_member_increase`, `friend_increase`), а не типами сессий (например, `group`, `private`).

```
Тип        detail_type                  Семантика         Тип сессии
────        ───────────                  ────            ────────
message     group                        Сообщение в группе         group (detail_type является типом сессии)
message     private                      Личное сообщение          private (detail_type является типом сессии)
notice      group_member_increase        Увеличение участников группы       group (необходимо вывести из group_id)
notice      friend_increase              Увеличение друзей         private (необходимо вывести из user_id)
request     friend                       Запрос на добавление в друзья         private (необходимо вывести из user_id)
request     group                        Запрос в группу           group (detail_type является типом сессии)
```

### 9.2 Правила вывода

Порядок вывода `infer_receive_type()`:

1. Если `detail_type` является известным типом сессии (`private`/`group`/`channel`/`guild`/`thread`/`user`), используйте его напрямую.
2. Если `detail_type` является пользовательским типом сессии, используйте его напрямую.
3. В противном случае (семантические подтипы notice/request), выведите тип сессии на основе полей ID:
   - Если есть `group_id` → `"group"`
   - Если есть `channel_id` → `"channel"`
   - Если есть `guild_id` → `"guild"`
   - Если есть `thread_id` → `"thread"`
   - Если есть `user_id` → `"private"`

### 9.3 Вывод цели `event.reply()`

Цель отправки `event.reply()` в событиях notice/request определяется выводом типа сессии:

- События уведомления о группе (содержат `group_id`) → отправка в **группу**
- События уведомления о друзьях (содержат только `user_id`) → отправка в **личное сообщение пользователю**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() отправляется в группу (group/group_789)
    await event.reply("Добро пожаловать в группу!")

    # Если необходимо уведомить администратора (лично), явно укажите цель:
    await adapter.Send.To("user", "admin_id").Text(f"Новый участник {user_id} присоединился к {group_id}")
```

### 9.4 Рекомендации для разработчиков адаптеров

Убедитесь, что события notice/request содержат правильные поля ID:

| detail_type | Обязательные поля ID | Выведенный тип сессии |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend` (запрос) | `user_id` | `private` |
| `group` (запрос) | `group_id` | `group` |

---

## 10. Связанные документы

- [Документация по особенностям каждой платформы](../platform-guide/README.md) - Вы можете обратиться к этому документу, чтобы узнать об особенностях каждой платформы, а также об известных расширенных событиях и сегментах сообщений.
- [Стандарт типов сессий](session-types.md) - Определения и сопоставления типов сессий
- [Спецификация методов отправки](send-method-spec.md) - Назначение имен методов класса Send, стандарт параметров и требования к обратному преобразованию
- [Стандарт ответов API](api-response.md) - Стандартный формат ответов API адаптера
- [Стандарт действий API](api-action-spec.md) - Единый интерфейс стандартных действий API OneBot12