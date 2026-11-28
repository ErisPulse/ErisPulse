# Документация по функциям Telegram

TelegramAdapter — это адаптер, построенный на базе Telegram Bot API, поддерживающий различные типы сообщений и обработку событий.

---

## Информация о документации

- Соответствующая версия модуля: 4.3.3
- Поддержка: ErisPulse
- Последнее обновление: 2026-11-10

## Основная информация

- Краткое описание платформы: Telegram — это мультиплатформенное приложение для обмена мгновенными сообщениями.
- Название адаптера: TelegramAdapter
- Поддерживаемые протоколы/API-версии: Telegram Bot API
- Соответствие типов сессий: `private` → при отправке используется `user`, `group`/`supergroup` → `group`, `channel` → `channel`

## Стандартизация выравнивания (4.3.3)

В этом разделе описаны изменения, внесённые в версии 4.3.3: изменения событий, соглашения по нескольким аккаунтам, стандарт кодов ошибок и соглашения по отправке.

### Изменения событий

1. **Стандартизация события запроса на вступление в группу**:
   - `detail_type` изменён с `telegram_chat_join_request` на стандартное значение `"group"`, `sub_type="join"`
   - `@request.on_group_request()` теперь может напрямую обрабатывать это событие
   - Правило синтеза `request_id` осталось неизменным: `tjr_{chat_id}_{user_id}_{date}`
   - Событие можно утвердить или отклонить с помощью `event.approve()` / `event.reject()` (соответствует `approveChatJoinRequest` / `declineChatJoinRequest`)
2. **Внедрение `self.account_id` в события**: все события содержат имя аккаунта, который их вызвал; в режиме нескольких аккаунтов `event.reply()` автоматически отправляется через этот аккаунт
3. **Неизвестные события**: `self.user_id` заполняется `bot_id` (поведение аналогично событиям сообщений)

Соглашения по интерфейсу запросов событий соответствуют стандарту SDK: [Соглашение по действиям запросов и утверждений](../standards/request-action-spec.md).

### Аккаунты и несколько аккаунтов

`call_api` поддерживает двойное соответствие поля аккаунта: стандартное поле `account_id` (передаётся как `ApiDSL.Using`) / старое альтернативное имя `_account_id`; фреймворк ApiDSL автоматически адаптируется к новым и старым адаптерам.

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

await telegram.Api.Using("main").get_self_info()        # Стандартный способ указания аккаунта
await telegram.Api.get_self_info(account_id="main")     # Явное указание стандартного поля account_id
```

### Стандарт кодов ошибок

| retcode | Описание |
|---------|----------|
| 0 | Успешно |
| 33001 | Ошибка сети (ошибка подключения, тайм-аут и т.д.) |
| 34100 | Отказ платформы (оригинальный ответ сохраняется в поле `telegram_raw`) |
| 10002 | Действие не поддерживается (например, `get_friend_list` / `get_group_list`, Telegram Bot API не имеет соответствующего интерфейса) |

### Соглашение по отправке

- Метод HTML называется `HTML`, `Html` является резервным алиасом
- Подпись `Location` дополнена необязательными параметрами `title` / `content`
- `AnswerCallback` / `Raw_json` используют send_context аккаунта: при вызове DSL отправки в цепочке обработки событий автоматически используется аккаунт, которому принадлежит текущее событие

## Стандартные действия API (DSL API)

Адаптер сопоставляет стандартные действия OB12 с Telegram Bot API и стандартизирует поле data:

| Стандартное действие OB12 | Telegram API | Поле data |
|--------------------------|--------------|----------|
| get_self_info | getMe | user_id / user_name / user_displayname |
| get_user_info(user_id) | getChat | user_id / user_name / user_displayname |
| get_group_info(group_id) | getChat | group_id / group_name |
| get_group_member_info(group_id, user_id) | getChatMember | user_id / user_name / telegram_role |
| delete_message(message_id) | deleteMessage | chat_id автоматически дополняется по таблице сообщений |
| leave_group(group_id) | leaveChat | - |

Дополнительные действия: get_group_admin_list(group_id) (список администраторов), get_chat_member_count(chat_id) (количество участников).

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

result = await telegram.Api.get_self_info()
result = await telegram.Api.get_group_info(group_id=-100123)
result = await telegram.Api.get_group_admin_list(-100123)
await telegram.Api.delete_message(message_id=55)   # Автоматическое дополнение chat_id
result = await telegram.Api.Using("main").get_self_info()
```

> В Telegram Bot API нет интерфейса для получения списка друзей/списка групп, get_friend_list/get_group_list явно возвращает retcode=10002 (неподдерживаемое действие).

---

## Операции с запросами (Request DSL)

Обработка запросов на добавление в группу, основанная на approveChatJoinRequest / declineChatJoinRequest. Начиная с версии 4.3.3, `chat_join_request` отображается как стандартное событие запроса группы (`sub_type="join"`), и `@request.on_group_request()` теперь может напрямую обрабатывать такие запросы:

```python
from ErisPulse.Core.Event import request

@request.on_group_request()
async def handle_join_request(event):
    if event.get("platform") != "telegram":
        return
    # event["request_id"] является синтетическим идентификатором (tjr_{chat_id}_{user_id}_{date}, правила остаются неизменными)
    if event.get("sub_type") == "join":
        await event.approve()          # Согласиться (approveChatJoinRequest)
    # await event.reject()             # Отклонить (declineChatJoinRequest)

# Ручной вызов (необходимо предварительно получить соответствующее событие запроса для регистрации контекста)
await telegram.Request(event["request_id"]).accept()
await telegram.Request(event["request_id"]).reject()
await telegram.Request(event["request_id"]).Using("main").accept()
```

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### Основные методы отправки

| Метод | Описание | Параметры |
|------|------|------|
| `.Text(text)` | Отправка обычного текстового сообщения | `text: str` |
| `.Face(emoji)` | Отправка эмодзи-кубика | `emoji: str` (например, 🎲 🎯 🏀) |
| `.Markdown(text, content_type)` | Отправка сообщения в формате Markdown | `content_type` по умолчанию `"MarkdownV2"` |
| `.HTML(text)` | Отправка сообщения в формате HTML (`Html` — устаревшее имя) | `text: str` |
| `.MergeForward(nodes, title)` | Отправка объединённого пересланного сообщения (заголовок + каждый блок `blockquote`, обрезка до 4096 символов) | `nodes: List[Dict]`, `title: str` |
| `.Sticker(file)` | Отправка стикера | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng, title="", content="")` | Отправка геолокации (необязательный заголовок и описание) | `latitude: float, longitude: float, title: str, content: str` |
| `.Venue(lat, lng, title, addr)` | Отправка места | Заголовок и адрес |
| `.Contact(phone, first, last)` | Отправка контакта | Номер телефона и имя |

### Методы отправки медиафайлов

Все методы медиа поддерживают два типа входных данных: `bytes` (загрузка) и `str` (file_id / URL):

| Метод | Описание |
|------|------|
| `.Image(file, caption, content_type)` | Отправка изображения |
| `.Video(file, caption, content_type)` | Отправка видео |
| `.Voice(file, caption)` | Отправка голосового сообщения |
| `.Audio(file, caption, content_type)` | Отправка аудио |
| `.File(file, caption)` | Отправка файла |
| `.Document(file, caption, content_type)` | Алиас для `File` |

### Методы управления сообщениями

| Метод | Описание |
|------|------|
| `.Edit(message_id, text, content_type)` | Редактирование существующего сообщения |
| `.Recall(message_id)` | Удаление указанного сообщения |
| `.Forward(from_chat_id, message_id)` | Пересылка сообщения (сохранение источника) |
| `.CopyMessage(from_chat_id, message_id)` | Копирование сообщения (без источника) |
| `.AnswerCallback(callback_query_id, text, show_alert)` | Ответ на обратный запрос (используется аккаунт send_context) |

### Отправка сообщений в формате OneBot12

- `.Raw_ob12(message: List[Dict])`: Отправка сообщения в формате OneBot12
- `.Raw_json(json_str: str)`: Отправка сообщения в формате JSON (используется аккаунт send_context)

### Методы цепочечного форматирования

| Метод | Описание |
|------|------|
| `.At(user_id)` | Упоминание пользователя (реализовано через entities Telegram, может вызываться несколько раз) |
| `.AtAll()` | Упоминание всех участников (отправка текста `@All`) |
| `.Reply(message_id)` | Ответ на указанное сообщение |
| `.Keyboard(inline_keyboard)` | Установка инлайн-клавиатуры (`list[list[dict]]`) |
| `.ProtectContent(protect)` | Защита контента (предотвращение пересылки и сохранения) |
| `.Silent(silent)` | Отправка в тихом режиме (не уведомлять пользователя) |

### Примеры отправки сообщений

```python
# Базовая отправка текста
await telegram.Send.To("user", user_id).Text("Hello World!")

# Сообщение с инлайн-клавиатурой
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "Кнопка 1", "callback_data": "btn1"}, {"text": "Кнопка 2", "callback_data": "btn2"}],
    [{"text": "Посетить сайт", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("Выберите:")

# Отправка медиафайла (по URL)
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="Изображение")

# Упоминание пользователя
await telegram.Send.To("group", group_id).At("6117725680").Text("Привет!")

# Ответ и защита контента
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("Секретное сообщение")

# Тихая отправка
await telegram.Send.To("group", group_id).Silent().Text("Тихое уведомление")

# Отправка HTML-форматированного сообщения (Html — устаревшее имя)
await telegram.Send.To("user", user_id).HTML("<b>Жирный</b> <i>Курсив</i>")

# Отправка геолокации (с заголовком)
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074, title="Тяньаньмэнь", content="Центр Пекина")

# Ответ на обратный запрос
await telegram.Send.AnswerCallback(callback_query_id, text="Обработано", show_alert=False)

# Комбинированное сообщение в формате OneBot12
ob12_message = [
    {"type": "text", "data": {"text": "Сложное сообщение: "}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "Имя пользователя"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# Отправка стикера
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id
```

## Специфические типы событий

Преобразование событий Telegram следует стандарту OneBot12, а расширения платформы предоставляются с префиксом `telegram_`.

### Сопоставление detail_type для событий сообщений

| Telegram chat.type | OneBot12 detail_type | Тип получателя |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### Специфические типы событий

| detail_type | Описание |
|---|---|
| `telegram_callback_query` | Запрос обратной связи (нажатие кнопки встроенной клавиатуры) |
| `telegram_inline_query` | Встроенный запрос |
| `telegram_chosen_inline_result` | Выбранный результат встроенного запроса |
| `telegram_poll` | Событие голосования |
| `telegram_poll_answer` | Ответ на голосование |
| `telegram_my_chat_member` | Изменение статуса участника бота в чате |
| `telegram_chat_member` | Изменение участника чата |
| `telegram_shipping_query` | Запрос доставки |
| `telegram_pre_checkout_query` | Запрос предоплаты |

> Запросы на присоединение к чату (chat_join_request) стандартизированы как событие запроса `group` (`sub_type="join"`), `telegram_chat_join_request` больше не используется как detail_type; соответствующие поля платформы (`telegram_chat_join_request_id`, `telegram_chat` и т.д.) по-прежнему сохраняются.

### Стандартные типы сообщений

Преобразованные сообщения используют стандартный формат OneBot12:

| Тип сообщения | Описание | Поля data |
|---|---|---|
| `text` | Чистый текст (без @имени пользователя) | `text` |
| `mention` | Упоминание пользователя (стандарт OB12) | `user_id`, `user_name` |
| `reply` | Ссылка на ответ | `message_id`, `user_id` |
| `image` | Изображение | `file_id`, `url` |
| `video` | Видео | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | Голосовое сообщение | `file_id`, `url`, `duration` |
| `audio` | Аудиофайл | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | Файл | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | Местоположение | `latitude`, `longitude`, необязательно `title`, `address` |

### Расширенные сообщения платформы

Расширенные сообщения с префиксом `telegram_`:

| Тип сообщения | Описание | Поля data |
|---|---|---|
| `telegram_sticker` | Стикер | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | Анимация GIF | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | Контакт | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | Встроенная клавиатура | `inline_keyboard` |

### Примеры событий

#### Сообщение в группе (с упоминанием)
```python
{
  "type": "message",
  "detail_type": "group",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "WSu2059",
  "group_id": "-1002850921906",
  "message_id": "172",
  "message": [
    {"type": "text", "data": {"text": "/it.echo "}},
    {"type": "mention", "data": {"user_id": "", "user_name": "@nm123_91178"}}
  ],
  "alt_message": "/it.echo @nm123_91178",
  "self": {
    "platform": "telegram",
    "user_id": "6117725680",
    "account_id": "default"
  },
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### Событие запроса на присоединение к группе (после стандартизации)
```python
{
  "type": "request",
  "detail_type": "group",
  "sub_type": "join",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "Имя просьбы",
  "request_id": "tjr_-1002850921906_6117725680_1731212345",
  "group_id": "-1002850921906",
  "comment": "Название ссылки приглашения",
  "self": {
    "platform": "telegram",
    "user_id": "6117725680",
    "account_id": "default"
  },
  "telegram_chat_join_request_id": "",
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "type": "supergroup"
  }
}
```

#### Событие запроса обратной связи
```python
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_id": "cb_123",
  "telegram_callback_data": "callback_data",
  "message_id": "msg_456"
}
```

#### Событие встроенного запроса
```python
{
  "type": "request",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_query_id": "iq_789",
  "telegram_query_text": "search_text",
  "telegram_query_offset": "0"
}
```

#### Сообщение с встроенной клавиатурой
```python
{
  "type": "message",
  "detail_type": "group",
  "message": [
    {"type": "text", "data": {"text": "Выберите: "}},
    {
      "type": "telegram_inline_keyboard",
      "data": {
        "inline_keyboard": [
          [{"text": "Кнопка 1", "callback_data": "btn1"}],
          [{"text": "Перейти", "url": "https://example.com"}]
        ]
      }
    }
  ]
}
```

## Event Mixin расширения методов

Адаптер зарегистрировал следующие методы, специфичные для платформы, доступные только при `platform == "telegram"`:

### Связанные с сообщениями

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `is_bot_message()` | `bool` | Определяет, исходит ли сообщение от бота |
| `is_edited_message()` | `bool` | Определяет, является ли сообщение отредактированным |
| `is_topic_message()` | `bool` | Определяет, является ли сообщение темой/Topic |
| `get_update_id()` | `int` | Получить ID обновления Telegram |
| `get_chat_title()` | `str` | Получить заголовок чата |
| `get_chat_username()` | `str` | Получить имя пользователя чата |
| `get_forward_from()` | `dict` | Получить информацию о转发 источнике |
| `get_topic_id()` | `str` | Получить идентификатор темы |

### Связанные с обратными запросами

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_callback_data()` | `str` | Получить callback_data обратного запроса |
| `get_callback_id()` | `str` | Получить идентификатор обратного запроса (используется для ответа) |

### Извлечение данных сегментов сообщений

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_inline_keyboard()` | `list` | Получить встроенные клавиатуры сообщения |
| `get_sticker_info()` | `dict` | Получить информацию о наклейке |
| `get_contact_info()` | `dict` | Получить информацию о контакте |
| `get_location()` | `dict` | Получить информацию о местоположении |

### Пример использования

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # Свойства сообщения
    if event.is_bot_message():
        return  # Пропустить сообщения от бота

    if event.is_edited_message():
        print("Это отредактированное сообщение")

    # Информация о чате
    title = event.get_chat_title()
    username = event.get_chat_username()

    # Источник转发
    forward = event.get_forward_from()

    # Данные сегментов сообщения
    sticker = event.get_sticker_info()
    contact = event.get_contact_info()
    location = event.get_location()
    keyboard = event.get_inline_keyboard()

    # Тема
    if event.is_topic_message():
        topic_id = event.get_topic_id()

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "telegram":
        return

    if event.get("detail_type") == "telegram_callback_query":
        callback_data = event.get_callback_data()
        callback_id = event.get_callback_id()

        # Ответить на обратный запрос
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="已点击")

        # Ответить на сообщение (в случае нескольких аккаунтов автоматически обрабатывается аккаунтом, к которому относится событие)
        await event.reply(f"你点击了：{callback_data}")
```

## Описание расширенных полей

- Все специфические поля идентифицируются с префиксом `telegram_`
- Исходные данные сохраняются в поле `telegram_raw`
- Тип исходного события сохраняется в поле `telegram_raw_type`
- Поле `self.account_id` события содержит имя аккаунта, который инициировал событие (в случае нескольких аккаунтов, `event.reply()` автоматически обрабатывается по этому аккаунту)
- Сообщения из каналов используют `detail_type="channel"`
- Личные сообщения используют `detail_type="private"` (при отправке необходимо преобразовать в `user`)
- Сообщения в темах содержат поле `thread_id`
- Упоминания с помощью `@` используют стандартный тип сообщения `mention` (`type: "mention"`), текст не содержит @имени пользователя

## Параметры конфигурации

Адаптер Telegram поддерживает конфигурацию нескольких аккаунтов:

### Пример конфигурации
```toml
[Telegram_Adapter.accounts.default]
token = "ВАШ_ТОКЕН_БОТА"
enabled = true

[Telegram_Adapter.accounts.bot2]
token = "ДРУГОЙ_ТОКЕН_БОТА"
enabled = true
```

### Режимы работы

Адаптер Telegram поддерживает только режим **Polling (опрос)**, режим Webhook был удален.

### Настройка прокси

Если необходимо подключиться к Telegram API через прокси, используйте системный прокси (переменные окружения `ALL_PROXY` / `HTTPS_PROXY`).

### Перенос старой конфигурации

Старый формат однотокеновой конфигурации будет автоматически поддерживаться:
```toml
# Старый формат (по-прежнему может использоваться, но рекомендуется перейти на новый)
[Telegram_Adapter]
token = "ВАШ_ТОКЕН_БОТА"
```

Рекомендуется перейти на новый формат:
```toml
[Telegram_Adapter.accounts.default]
token = "ВАШ_ТОКЕН_БОТА"
enabled = true
```