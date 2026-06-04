# Документация по особенностям платформы Telegram

TelegramAdapter — это адаптер, основанный на Telegram Bot API, который поддерживает множество типов сообщений и обработку событий.

---

## Информация о документе

- Версия соответствующего модуля: 3.6.5
- Ответственный: ErisPulse

## Основная информация

- О платформе: Telegram — это кроссплатформенное программное обеспечение для мгновенного обмена сообщениями
- Имя адаптера: TelegramAdapter
- Поддерживаемый протокол/API-версия: Telegram Bot API
- Отображение типов сессий: `private` → отправка как `user`, `group`/`supergroup` → `group`, `channel` → `channel`

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечной (chain) нотации, например:
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### Основные методы отправки

| Метод | Описание | Параметр |
|------|------|------|
| `.Text(text)` | Отправить текстовое сообщение | `text: str` |
| `.Face(emoji)` | Отправить эмодзи-кость | `emoji: str` (например, 🎲 🎯 🏀) |
| `.Markdown(text, content_type)` | Отправить сообщение в формате Markdown | `content_type` по умолчанию `"MarkdownV2"` |
| `.HTML(text)` | Отправить сообщение в формате HTML | `text: str` |
| `.Sticker(file)` | Отправить стикер | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | Отправить местоположение | `latitude: float, longitude: float` |
| `.Venue(lat, lng, title, addr)` | Отправить локацию (место) | Включает заголовок и адрес |
| `.Contact(phone, first, last)` | Отправить контакт | Включает номер телефона и имя |

### Методы отправки медиа

Все методы для отправки медиа поддерживают два типа входных данных: `bytes` (для загрузки) и `str` (file_id / URL):

| Метод | Описание |
|------|------|
| `.Image(file, caption, content_type)` | Отправить изображение |
| `.Video(file, caption, content_type)` | Отправить видео |
| `.Voice(file, caption)` | Отправить голосовое сообщение |
| `.Audio(file, caption, content_type)` | Отправить аудио |
| `.File(file, caption)` | Отправить файл |
| `.Document(file, caption, content_type)` | Псевдоним для .File |

### Методы управления сообщениями

| Метод | Описание |
|------|------|
| `.Edit(message_id, text, content_type)` | Редактировать существующее сообщение |
| `.Recall(message_id)` | Удалить указанное сообщение |
| `.Forward(from_chat_id, message_id)` | Переслать сообщение (сохраняя источник) |
| `.CopyMessage(from_chat_id, message_id)` | Копировать сообщение (без источника) |
| `.AnswerCallback(callback_query_id, text, show_alert)` | Ответить на callback-запрос |

### Отправка исходных сообщений

- `.Raw_ob12(message: List[Dict])`: Отправить сообщение в стандартном формате OneBot12
- `.Raw_json(json_str: str)`: Отправить сообщение в исходном формате JSON

### Методы цепочечной модификации (Chain modifiers)

| Метод | Описание |
|------|------|
| `.At(user_id)` | Упомянуть пользователя (@user_id) (реализовано через Telegram entities, может вызываться несколько раз) |
| `.AtAll()` | Упомянуть всех участников (отправляет текст `@All`) |
| `.Reply(message_id)` | Ответить на указанное сообщение |
| `.Keyboard(inline_keyboard)` | Установить встроенную клавиатуру (`list[list[dict]]`) |
| `.ProtectContent(protect)` | Защитить контент (предотвращает пересылку и сохранение) |
| `.Silent(silent)` | Отправить без уведомлений (не уведомлять пользователя) |

### Примеры отправки

```python
# Базовая отправка текста
await telegram.Send.To("user", user_id).Text("Hello World!")

# Сообщение со встроенной клавиатурой
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "Кнопка1", "callback_data": "btn1"}, {"text": "Кнопка2", "callback_data": "btn2"}],
    [{"text": "Перейти на сайт", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("Пожалуйста, выберите:")

# Отправка медиа (способ URL)
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="Изображение")

# Упоминание пользователя
await telegram.Send.To("group", group_id).At("6117725680").Text("Привет!")

# Ответ + защита контента
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("Конфиденциальное сообщение")

# Отправка без уведомлений
await telegram.Send.To("group", group_id).Silent().Text("Тихое уведомление")

# Ответ на callback-запрос
await telegram.Send.AnswerCallback(callback_query_id, text="Обработано", show_alert=False)

# Составное сообщение OneBot12
ob12_message = [
    {"type": "text", "data": {"text": "Сложное сообщение:"}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "ИмяПользователя"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# Отправка стикера
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id

# Отправка местоположения
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074)
```

## Специфические типы событий

Трансформация событий Telegram следует стандарту OneBot12, а также предоставляет платформенные расширения через префикс `telegram_`.

### Отображение detail_type для событий сообщений

| Telegram chat.type | OneBot12 detail_type | Тип цели отправки |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### Специфические типы событий

| detail_type | Описание |
|---|---|
| `telegram_callback_query` | Callback-запрос (нажатие на кнопку встроенной клавиатуры) |
| `telegram_inline_query` | Inline-запрос |
| `telegram_chosen_inline_result` | Выбранный inline-результат |
| `telegram_poll` | Событие голосования (опрос) |
| `telegram_poll_answer` | Ответ на голосование |
| `telegram_my_chat_member` | Изменение статуса участника самого бота |
| `telegram_chat_member` | Изменение статуса участника чата |
| `telegram_chat_join_request` | Запрос на вступление в чат |
| `telegram_shipping_query` | Запрос стоимости доставки |
| `telegram_pre_checkout_query` | Предзаказный запрос |

### Стандартные типы сегментов сообщений

Преобразованные сегменты сообщений используют стандартный формат OneBot12:

| Тип сообщения | Описание | Поля данных |
|---|---|---|
| `text` | Текст (без @username) | `text` |
| `mention` | Упоминание пользователя (стандарт OB12) | `user_id`, `user_name` |
| `reply` | Ссылка на ответ | `message_id`, `user_id` |
| `image` | Изображение | `file_id`, `url` |
| `video` | Видео | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | Голосовое сообщение | `file_id`, `url`, `duration` |
| `audio` | Аудио | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | Файл | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | Местоположение | `latitude`, `longitude`, опционально `title`, `address` |

### Платформенные расширенные типы сообщений

Расширенные типы сообщений, идентифицируемые префиксом `telegram_`:

| Тип сообщения | Описание | Поля данных |
|---|---|---|
| `telegram_sticker` | Стикер | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | Анимация (GIF) | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | Контакт | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | Встроенная клавиатура | `inline_keyboard` |

### Примеры событий

#### Сообщение в групповом чате (с упоминанием @)
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

#### Событие callback-запроса
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

#### Событие inline-запроса
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

#### Сообщение со встроенной клавиатурой
```python
{
  "type": "message",
  "detail_type": "group",
  "message": [
    {"type": "text", "data": {"text": "Пожалуйста, выберите:"}},
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

## Методы расширения Event Mixin

Адаптер регистрирует следующие методы, специфичные для платформы, доступные только при `platform == "telegram"`:

### Связанные с сообщениями

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `is_bot_message()` | `bool` | Проверить, отправлено ли сообщение ботом |
| `is_edited_message()` | `bool` | Проверить, является ли сообщение редактированным |
| `is_topic_message()` | `bool` | Проверить, является ли сообщение по теме/Topic |
| `get_update_id()` | `int` | Получить Telegram update ID |
| `get_chat_title()` | `str` | Получить заголовок чата |
| `get_chat_username()` | `str` | Получить имя пользователя чата |
| `get_forward_from()` | `dict` | Получить информацию о источнике переслания |
| `get_topic_id()` | `str` | Получить ID темы (Topic) |

### Связанные с callback-запросами

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_callback_data()` | `str` | Получить callback_data из callback-запроса |
| `get_callback_id()` | `str` | Получить ID callback-запроса (для ответа) |

### Извлечение данных сегментов сообщений

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_inline_keyboard()` | `list` | Получить встроенную клавиатуру из сообщения |
| `get_sticker_info()` | `dict` | Получить информацию о стикере |
| `get_contact_info()` | `dict` | Получить информацию о контакте |
| `get_location()` | `dict` | Получить информацию о местоположении |

### Примеры использования

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

    # Информация о переслывании
    forward = event.get_forward_from()

    # Данные сегментов сообщений
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

        # Ответ на callback-запрос
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="Нажато")

        # Ответное сообщение
        await event.reply(f"Вы нажали: {callback_data}")
```

## Описание расширенных полей

- Все специальные поля идентифицируются префиксом `telegram_`
- Исходные данные сохраняются в поле `telegram_raw`
- Исходный тип события сохраняется в поле `telegram_raw_type`
- Для сообщений в каналах используется `detail_type="channel"`
- Для личных сообщений используется `detail_type="private"` (при отправке необходимо преобразовать в `user`)
- Сообщения по темам (Topics) содержат поле `thread_id`
- Упоминания `@` используют стандартный тип сегмента сообщения `mention` (`type: "mention"`), текст не содержит @username

## Параметры конфигурации

Telegram адаптер поддерживает следующие параметры конфигурации:

### Основная конфигурация
- `token`: Telegram Bot Token
- `proxy_enabled`: Включить ли прокси

### Конфигурация прокси
- `proxy.host`: Адрес прокси-сервера
- `proxy.port`: Порт прокси
- `proxy.type`: Тип прокси (`"socks4"` или `"socks5"`)

### Режим работы

Telegram адаптер поддерживает только режим **Polling (опрос)**, режим Webhook был удален.

Пример конфигурации:
```toml
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
proxy_enabled = false

[Telegram_Adapter.proxy]
host = "127.0.0.1"
port = 1080
type = "socks5"