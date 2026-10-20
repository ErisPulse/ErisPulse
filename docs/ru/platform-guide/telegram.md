# Документация по функциям Telegram-платформы

TelegramAdapter — это адаптер, построенный на основе Telegram Bot API, поддерживающий различные типы сообщений и обработку событий.

---

## Информация о документации

- Версия соответствующего модуля: 4.3.0
- Ответственный: ErisPulse

## Основная информация

- Краткое описание платформы: Telegram — это мультиплатформенный мессенджер
- Название адаптера: TelegramAdapter
- Поддерживаемый протокол/API: Telegram Bot API
- Сопоставление типов сессий: `private` → при отправке используйте `user`, `group`/`supergroup` → `group`, `channel` → `channel`

## Стандартные действия API (DSL API)

Адаптер сопоставляет стандартные действия OB12 с Telegram Bot API и стандартизирует поле data:

| Стандартное действие OB12 | Telegram API | Поле data |
|--------------------------|--------------|-----------|
| get_self_info | getMe | user_id / user_name / user_displayname |
| get_user_info(user_id) | getChat | user_id / user_name / user_displayname |
| get_group_info(group_id) | getChat | group_id / group_name |
| get_group_member_info(group_id, user_id) | getChatMember | user_id / user_name / telegram_role |
| delete_message(message_id) | deleteMessage | Автоматически дополняет chat_id из таблицы сообщений |
| leave_group(group_id) | leaveChat | - |

Дополнительные действия: get_group_admin_list(group_id) (список администраторов), get_chat_member_count(chat_id) (количество участников).

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

result = await telegram.Api.get_self_info()
result = await telegram.Api.get_group_info(group_id=-100123)
result = await telegram.Api.get_group_admin_list(-100123)
await telegram.Api.delete_message(message_id=55)   # Автоматически дополняет chat_id
result = await telegram.Api.Using("main").get_self_info()
```

> Telegram Bot API не предоставляет интерфейс для получения списка друзей/групп, get_friend_list/get_group_list возвращает errorcode=10002.

---

## Операции запросов (DSL запросов)

Обработка запросов на присоединение к группе (событие chat_join_request), основанные на approveChatJoinRequest / declineChatJoinRequest:

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_join_request(event):
    if event.get("platform") != "telegram":
        return
    # event["request_id"] — синтезированный идентификатор (tjr_{chat_id}_{user_id}_{date})
    if event.get("user_nickname"):
        await event.approve()          # Подтвердить
    # await event.reject()             # Отклонить

# Ручной вызов (требуется предварительное получение соответствующего события запроса для регистрации контекста)
await telegram.Request(event["request_id"]).accept()
await telegram.Request(event["request_id"]).reject()
await telegram.Request(event["request_id"]).Using("main").accept()
```

---
## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечной синтаксической конструкции, например:
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### Основные методы отправки

| Метод | Описание | Параметры |
|-------|----------|-----------|
| `.Text(text)` | Отправка текстового сообщения | `text: str` |
| `.Face(emoji)` | Отправка эмодзи-кости | `emoji: str` (например 🎲 🎯 🏀) |
| `.Markdown(text, content_type)` | Отправка сообщения в формате Markdown | `content_type` по умолчанию `"MarkdownV2"` |
| `.HTML(text)` | Отправка сообщения в формате HTML | `text: str` |
| `.MergeForward(nodes, title)` | Отправка объединённого пересланного сообщения (заголовок + каждый блок blockquote, обрезка до 4096 символов) | `nodes: List[Dict]`, `title: str` |
| `.Sticker(file)` | Отправка стикера | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | Отправка геолокации | `latitude: float, longitude: float` |
| `.Venue(lat, lng, title, addr)` | Отправка места | Содержит заголовок и адрес |
| `.Contact(phone, first, last)` | Отправка контакта | Содержит номер телефона и имя |

### Методы отправки медиа

Все методы медиа поддерживают два типа входных данных: `bytes` (загрузка) и `str` (file_id / URL):

| Метод | Описание |
|-------|----------|
| `.Image(file, caption, content_type)` | Отправка изображения |
| `.Video(file, caption, content_type)` | Отправка видео |
| `.Voice(file, caption)` | Отправка голосового сообщения |
| `.Audio(file, caption, content_type)` | Отправка аудио |
| `.File(file, caption)` | Отправка файла |
| `.Document(file, caption, content_type)` | Псевдоним для метода File |

### Методы управления сообщениями

| Метод | Описание |
|-------|----------|
| `.Edit(message_id, text, content_type)` | Редактирование существующего сообщения |
| `.Recall(message_id)` | Удаление указанного сообщения |
| `.Forward(from_chat_id, message_id)` | Пересылка сообщения (сохраняя источник) |
| `.CopyMessage(from_chat_id, message_id)` | Копирование сообщения (без источника) |
| `.AnswerCallback(callback_query_id, text, show_alert)` | Ответ на запрос обратного вызова |

### Отправка оригинальных сообщений

- `.Raw_ob12(message: List[Dict])`: Отправка сообщения в формате OneBot12
- `.Raw_json(json_str: str)`: Отправка сообщения в формате JSON

### Методы цепочечного изменения

| Метод | Описание |
|-------|----------|
| `.At(user_id)` | Упоминание пользователя (реализовано через entities Telegram, можно вызывать несколько раз) |
| `.AtAll()` | Упоминание всех участников (отправка текста `@All`) |
| `.Reply(message_id)` | Ответ на указанное сообщение |
| `.Keyboard(inline_keyboard)` | Установка встроенной клавиатуры (`list[list[dict]]`) |
| `.ProtectContent(protect)` | Защита содержимого (предотвращает пересылку и сохранение) |
| `.Silent(silent)` | Тихая отправка (не уведомляет пользователя) |

### Примеры отправки

```python
# Базовая отправка текста
await telegram.Send.To("user", user_id).Text("Hello World!")

# Сообщение с встроенной клавиатурой
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "Кнопка1", "callback_data": "btn1"}, {"text": "Кнопка2", "callback_data": "btn2"}],
    [{"text": "Посетить сайт", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("Выберите:")

# Отправка медиа (через URL)
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="Изображение")

# Упоминание пользователя
await telegram.Send.To("group", group_id).At("6117725680").Text("Привет!")

# Ответ + защита содержимого
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("Секретное сообщение")

# Тихая отправка
await telegram.Send.To("group", group_id).Silent().Text("Тихое уведомление")

# Ответ на запрос обратного вызова
await telegram.Send.AnswerCallback(callback_query_id, text="Обработано", show_alert=False)

# Сложное сообщение OneBot12
ob12_message = [
    {"type": "text", "data": {"text": "Сложное сообщение: "}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "Имя пользователя"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# Отправка стикера
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id

# Отправка геолокации
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074)
```

## Уникальные типы событий

Преобразование событий Telegram соответствует стандарту OneBot12, а также предоставляет расширения платформы через префикс `telegram_`.

### Сопоставление detail_type событий сообщений

| Telegram chat.type | OneBot12 detail_type | Тип отправки |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### Уникальные типы событий

| detail_type | Описание |
|---|---|
| `telegram_callback_query` | Запрос обратного вызова (нажатие кнопки встроенной клавиатуры) |
| `telegram_inline_query` | Встроенный запрос |
| `telegram_chosen_inline_result` | Выбранный результат встроенной клавиатуры |
| `telegram_poll` | Событие голосования |
| `telegram_poll_answer` | Ответ на голосование |
| `telegram_my_chat_member` | Изменение статуса участника бота |
| `telegram_chat_member` | Изменение участника чата |
| `telegram_chat_join_request` | Запрос на присоединение к чату |
| `telegram_shipping_query` | Запрос доставки |
| `telegram_pre_checkout_query` | Предзаказный запрос |

### Стандартные типы сообщений

Преобразованные сообщения используют стандартный формат OneBot12:

| Тип сообщения | Описание | Поля data |
|---|---|---|
| `text` | Чистый текст (без упоминаний) | `text` |
| `mention` | Упоминание пользователя (стандарт OB12) | `user_id`, `user_name` |
| `reply` | Ответ на сообщение | `message_id`, `user_id` |
| `image` | Изображение | `file_id`, `url` |
| `video` | Видео | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | Голосовое сообщение | `file_id`, `url`, `duration` |
| `audio` | Аудио | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | Файл | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | Геолокация | `latitude`, `longitude`, опционально `title`, `address` |

### Расширенные сообщения платформы

Сообщения с расширенными полями, помеченные префиксом `telegram_`:

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
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### Событие запроса обратного вызова
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
    {"type": "text", "data": {"text": "Выберите:"}},
    {
      "type": "telegram_inline_keyboard",
      "data": {
        "inline_keyboard": [
          [{"text": "Кнопка1", "callback_data": "btn1"}],
          [{"text": "Перейти", "url": "https://example.com"}]
        ]
      }
    }
  ]
}
```

## Расширения Event Mixin

Адаптер зарегистрировал следующие методы, специфичные для платформы, доступные только при `platform == "telegram"`:

### Связанные с сообщениями

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `is_bot_message()` | `bool` | Проверка, исходит ли сообщение от бота |
| `is_edited_message()` | `bool` | Проверка, является ли сообщение отредактированным |
| `is_topic_message()` | `bool` | Проверка, является ли сообщение темой/Topic |
| `get_update_id()` | `int` | Получение ID обновления Telegram |
| `get_chat_title()` | `str` | Получение заголовка чата |
| `get_chat_username()` | `str` | Получение username чата |
| `get_forward_from()` | `dict` | Получение информации о источнике пересылки |
| `get_topic_id()` | `str` | Получение ID темы |

### Связанные с запросами обратного вызова

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_callback_data()` | `str` | Получение callback_data запроса обратного вызова |
| `get_callback_id()` | `str` | Получение ID запроса обратного вызова (для ответа) |

### Извлечение данных сообщений

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_inline_keyboard()` | `list` | Получение встроенной клавиатуры из сообщения |
| `get_sticker_info()` | `dict` | Получение информации о стикере |
| `get_contact_info()` | `dict` | Получение информации о контакте |
| `get_location()` | `dict` | Получение информации о геолокации |

### Пример использования

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # Свойства сообщения
    if event.is_bot_message():
        return  # Игнорировать сообщения от бота

    if event.is_edited_message():
        print("Это отредактированное сообщение")

    # Информация о чате
    title = event.get_chat_title()
    username = event.get_chat_username()

    # Источник пересылки
    forward = event.get_forward_from()

    # Данные сообщений
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

        # Ответ на запрос обратного вызова
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="Нажато")

        # Ответ на сообщение
        await event.reply(f"Вы нажали: {callback_data}")
```

## Описание расширенных полей

- Все уникальные поля помечены префиксом `telegram_`
- Оригинальные данные сохраняются в поле `telegram_raw`
- Оригинальный тип события сохраняется в поле `telegram_raw_type`
- Сообщения в канале используют `detail_type="channel"`
- Личные сообщения используют `detail_type="private"` (при отправке нужно преобразовать в `user`)
- Сообщения темы содержат поле `thread_id`
- Упоминания `@` используют стандартный тип сообщений `mention` (`type: "mention"`), текст не содержит @имени пользователя

## Параметры конфигурации

Адаптер Telegram поддерживает конфигурацию нескольких аккаунтов:

### Пример конфигурации
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true

[Telegram_Adapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
enabled = true
```

### Режимы работы

Адаптер Telegram поддерживает только режим **Polling (опрос)**, режим Webhook удален.

### Конфигурация прокси

Если требуется подключение к Telegram API через прокси, используйте системные настройки прокси (переменные окружения `ALL_PROXY` / `HTTPS_PROXY`).

### Перенос старой конфигурации

Старая конфигурация с одним токеном автоматически совместима:
```toml
# Старый формат (по-прежнему может использоваться, но рекомендуется миграция)
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

Рекомендуется перейти на новый формат:
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```