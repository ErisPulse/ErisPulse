# Характеристики платформы Telegram

TelegramAdapter — это адаптер, построенный на основе Telegram Bot API, поддерживающий различные типы сообщений и обработку событий.

---

## Информация о документации

- Соответствующая версия модуля: 4.1.1
- Поддержка: ErisPulse

## Основная информация

- Краткое описание платформы: Telegram — это мультиплатформенное приложение для обмена сообщениями в реальном времени
- Название адаптера: TelegramAdapter
- Поддерживаемые протоколы/версии API: Telegram Bot API
- Сопоставление типов сеансов: `private` → при отправке используйте `user`, `group`/`supergroup` → `group`, `channel` → `channel`

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочки вызовов, например:
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### Основные методы отправки

| Метод | Описание | Параметры |
|------|------|------|
| `.Text(text)` | Отправить текстовое сообщение | `text: str` |
| `.Face(emoji)` | Отправить эмодзи-кубик | `emoji: str` (например 🎲 🎯 🏀) |
| `.Markdown(text, content_type)` | Отправить сообщение в формате Markdown | `content_type` по умолчанию `"MarkdownV2"` |
| `.HTML(text)` | Отправить сообщение в формате HTML | `text: str` |
| `.Sticker(file)` | Отправить стикер | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | Отправить геолокацию | `latitude: float, longitude: float` |
| `.Venue(lat, lng, title, addr)` | Отправить место | С заголовком и адресом |
| `.Contact(phone, first, last)` | Отправить контакт | С номером телефона и именем |

### Методы отправки медиа

Все методы медиа поддерживают два типа входных данных: `bytes` (загрузка) и `str` (file_id / URL):

| Метод | Описание |
|------|------|
| `.Image(file, caption, content_type)` | Отправить изображение |
| `.Video(file, caption, content_type)` | Отправить видео |
| `.Voice(file, caption)` | Отправить голосовое сообщение |
| `.Audio(file, caption, content_type)` | Отправить аудио |
| `.File(file, caption)` | Отправить файл |
| `.Document(file, caption, content_type)` | Псевдоним для `File` |

### Методы управления сообщениями

| Метод | Описание |
|------|------|
| `.Edit(message_id, text, content_type)` | Изменить существующее сообщение |
| `.Recall(message_id)` | Удалить указанное сообщение |
| `.Forward(from_chat_id, message_id)` | Переслать сообщение (с сохранением источника) |
| `.CopyMessage(from_chat_id, message_id)` | Скопировать сообщение (без источника) |
| `.AnswerCallback(callback_query_id, text, show_alert)` | Ответить на запрос обратной связи |

### Отправка сообщений в необработанном виде

- `.Raw_ob12(message: List[Dict])`: Отправить сообщение в формате OneBot12
- `.Raw_json(json_str: str)`: Отправить сообщение в формате JSON

### Методы цепочечного форматирования

| Метод | Описание |
|------|------|
| `.At(user_id)` | Упомянуть пользователя (через сущности Telegram, можно вызывать несколько раз) |
| `.AtAll()` | Упомянуть всех участников (отправить текст `@All`) |
| `.Reply(message_id)` | Ответить на указанное сообщение |
| `.Keyboard(inline_keyboard)` | Установить встроенную клавиатуру (`list[list[dict]]`) |
| `.ProtectContent(protect)` | Защитить содержимое (предотвратить пересылку и сохранение) |
| `.Silent(silent)` | Отправить в тихом режиме (не уведомлять пользователя) |

### Примеры отправки сообщений

```python
# Базовая отправка текста
await telegram.Send.To("user", user_id).Text("Hello World!")

# Сообщение с встроенной клавиатурой
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "Кнопка 1", "callback_data": "btn1"}, {"text": "Кнопка 2", "callback_data": "btn2"}],
    [{"text": "Перейти на сайт", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("Выберите:")

# Отправка медиа (по URL)
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="Изображение")

# Упоминание пользователя
await telegram.Send.To("group", group_id).At("6117725680").Text("Привет!")

# Ответ с защитой содержимого
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("Секретное сообщение")

# Отправка в тихом режиме
await telegram.Send.To("group", group_id).Silent().Text("Тихое уведомление")

# Ответ на запрос обратной связи
await telegram.Send.AnswerCallback(callback_query_id, text="Обработано", show_alert=False)

# Сложное сообщение в формате OneBot12
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
| `telegram_my_chat_member` | Изменение статуса участника бота |
| `telegram_chat_member` | Изменение участника чата |
| `telegram_chat_join_request` | Запрос на присоединение к чату |
| `telegram_shipping_query` | Запрос доставки |
| `telegram_pre_checkout_query` | Запрос предоплаты |

### Стандартные типы сообщений

Преобразованные сообщения используют стандартный формат OneBot12:

| Тип сообщения | Описание | Поля data |
|---|---|---|
| `text` | Простой текст (без @имени пользователя) | `text` |
| `mention` | Упоминание пользователя (стандарт OB12) | `user_id`, `user_name` |
| `reply` | Ссылка на ответ | `message_id`, `user_id` |
| `image` | Изображение | `file_id`, `url` |
| `video` | Видео | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | Голосовое сообщение | `file_id`, `url`, `duration` |
| `audio` | Аудио | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | Файл | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | Местоположение | `latitude`, `longitude`, необязательно `title`, `address` |

### Расширенные сообщения платформы

Расширения сообщений с префиксом `telegram_`:

| Тип сообщения | Описание | Поля data |
|---|---|---|
| `telegram_sticker` | Наклейка | `file_id`, `emoji`, `sticker_type`, `url` |
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

## Расширения Event Mixin

Адаптер зарегистрировал следующие методы, специфичные для платформы, доступные только при `platform == "telegram"`:

### Связанные с сообщениями

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `is_bot_message()` | `bool` | Определяет, пришло ли сообщение от бота |
| `is_edited_message()` | `bool` | Определяет, является ли сообщение отредактированным |
| `is_topic_message()` | `bool` | Определяет, является ли сообщение тематическим/Topic |
| `get_update_id()` | `int` | Получает идентификатор обновления Telegram |
| `get_chat_title()` | `str` | Получает заголовок чата |
| `get_chat_username()` | `str` | Получает имя пользователя чата |
| `get_forward_from()` | `dict` | Получает информацию о источнике пересылки |
| `get_topic_id()` | `str` | Получает идентификатор темы |

### Связанные с обратными запросами

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_callback_data()` | `str` | Получает callback_data обратного запроса |
| `get_callback_id()` | `str` | Получает идентификатор обратного запроса (для ответа) |

### Извлечение данных сегментов сообщений

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_inline_keyboard()` | `list` | Получает встроенную клавиатуру в сообщении |
| `get_sticker_info()` | `dict` | Получает информацию о стикере |
| `get_contact_info()` | `dict` | Получает информацию о контакте |
| `get_location()` | `dict` | Получает информацию о местоположении |

### Пример использования

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # Свойства сообщения
    if event.is_bot_message():
        return  # Пропускаем сообщения от бота

    if event.is_edited_message():
        print("Это отредактированное сообщение")

    # Информация о чате
    title = event.get_chat_title()
    username = event.get_chat_username()

    # Источник пересылки
    forward = event.get_forward_from()

    # Данные сегментов сообщения
    sticker = event.get_sticker_info()
    contact = event.get_contact_info()
    location = event.get_location()
    keyboard = event.get_inline_keyboard()

    # Темы
    if event.is_topic_message():
        topic_id = event.get_topic_id()

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "telegram":
        return

    if event.get("detail_type") == "telegram_callback_query":
        callback_data = event.get_callback_data()
        callback_id = event.get_callback_id()

        # Ответ на обратный запрос
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="Нажато")

        # Ответ на сообщение
        await event.reply(f"Вы нажали: {callback_data}")
```

## Пояснения к расширенным полям

- Все специфические поля идентифицируются с префиксом `telegram_`
- Исходные данные сохраняются в поле `telegram_raw`
- Тип исходного события сохраняется в поле `telegram_raw_type`
- Сообщения в каналах используют `detail_type="channel"`
- Личные сообщения используют `detail_type="private"` (при отправке необходимо преобразовать в `user`)
- Сообщения в темах содержат поле `thread_id`
- Упоминания с помощью `@` используют стандартный тип сообщения упоминания (`type: "mention"`), текст не содержит @имя_пользователя

## Параметры конфигурации

Адаптер Telegram поддерживает настройку нескольких аккаунтов:

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

Адаптер Telegram поддерживает только **режим опроса (Polling)**, режим вебхуков (Webhook) был удалён.

### Настройка прокси

Если необходимо подключиться к Telegram API через прокси, используйте системные настройки прокси (переменные окружения `ALL_PROXY` / `HTTPS_PROXY`).

### Перенос старой конфигурации

Старый формат конфигурации с одним токеном будет автоматически поддерживаться:
```toml
# Старый формат (по-прежнему работает, но рекомендуется перейти на новый)
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

Рекомендуется перейти на новый формат:
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```