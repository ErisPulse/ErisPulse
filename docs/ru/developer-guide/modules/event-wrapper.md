# Подробное описание класса Event Wrapper

Модуль Event предоставляет мощный класс Event Wrapper, упрощающий обработку событий.

## Основные возможности

- **Полная совместимость с dict**: Event наследуется от dict
- **Удобные методы**: Предоставляет множество удобных методов
- **Доступ через точку**: Поддержка доступа к полям события через точку
- **Обратная совместимость**: Все методы являются необязательными

## Основные методы полей

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, Платформа: {platform}, Время: {time}")
```

## Методы для событий сообщений

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}！")
```

## Проверка типа сообщения

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"Тип: {'Личное сообщение' if is_private else 'Групповое сообщение'}")
```

## Функция ответа

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    await event.reply("Пожалуйста, введите ваше имя:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}！")
```

## Получение информации о командах

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"Команда: {cmd_name}, Аргументы: {cmd_args}")
```

## Методы для уведомительных событий

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("Добро пожаловать добавить меня в друзья！")
```

## Таблица методов-справочников

### Основные методы

#### Базовая информация о событии
- `get_id()` - получить ID события
- `get_time()` - получить метку времени события (Unix, секунды)
- `get_type()` - получить тип события (message/notice/request/meta)
- `get_detail_type()` - получить детальный тип события (private/group/friend и т.д.)
- `get_platform()` - получить название платформы

#### Информация о боте
- `get_self_platform()` - получить название платформы бота
- `get_self_user_id()` - получить ID пользователя бота
- `get_self_account_id()` - получить ID аккаунта бота (режим нескольких ботов)
- `get_self_info()` - получить полный словарь информации о боте

### Методы событий сообщений

#### Содержание сообщения
- `get_message()` - получить массив сегментов сообщения (формат OneBot12)
- `get_alt_message()` - получить альтернативный текст сообщения
- `get_text()` - получить чистый текстовый контент (псевдоним для `get_alt_message()`)
- `get_message_text()` - получить чистый текстовый контент (псевдоним для `get_alt_message()`)

#### Информация об отправителе
- `get_user_id()` - получить ID пользователя отправителя
- `get_user_nickname()` - получить никнейм отправителя
- `get_sender()` - получить полный словарь информации об отправителе

#### Информация о группе/канале
- `get_group_id()` - получить ID группы (сообщение из группы)
- `get_channel_id()` - получить ID канала (сообщение в канале)
- `get_guild_id()` - получить ID сервера (сообщение на сервере)
- `get_thread_id()` - получить ID ветки/подканала (сообщение в ветке)

#### Связанные с упоминаниями @
- `has_mention()` - содержит ли @ бота
- `get_mentions()` - получить список ID пользователей, на которых было @

### Проверка типа сообщения

#### Базовые проверки
- `is_message()` - является ли событие сообщением
- `is_private_message()` - является ли личным сообщением
- `is_group_message()` - является ли сообщением в группе
- `is_at_message()` - является ли сообщение с @ (псевдоним для `has_mention()`)

### Методы уведомительных событий

#### Оператор уведомления
- `get_operator_id()` - получить ID оператора
- `get_operator_nickname()` - получить никнейм оператора

#### Проверка типа уведомления
- `is_notice()` - является ли событие уведомлением
- `is_group_member_increase()` - событие увеличения участника группы
- `is_group_member_decrease()` - событие уменьшения участника группы
- `is_friend_add()` - событие добавления друга (соответствует `detail_type == "friend_increase"`)
- `is_friend_delete()` - событие удаления друга (соответствует `detail_type == "friend_decrease"`)

### Методы для событий запросов

#### Информация о запросе
- `get_comment()` - получить комментарий/приписку к запросу

#### Проверка типа запроса
- `is_request()` - является ли событие запросом
- `is_friend_request()` - является ли запросом от друга
- `is_group_request()` - является ли запросом группы

### Функция ответа

#### Базовый ответ
- `reply(content, method="Text", at_users=None, reply_to=None, at_all=False, **kwargs)` - общий метод ответа
  - `content`: отправляемый контент (текст, URL и т.д.)
  - `method`: метод отправки, по умолчанию "Text"
  - `at_users`: список пользователей для @, например `["user1", "user2"]`
  - `reply_to`: ID сообщения-ответа
  - `at_all`: упоминать ли всех участников
  - Поддерживает "Text", "Image", "Voice", "Video", "File", "Mention" и т.д.
  - `**kwargs`: дополнительные параметры (например, `user_id` для метода Mention)

- `reply_ob12(message)` - ответ, используя сегменты сообщений OneBot12
  - `message`: список или словарь сегментов сообщений OneBot12, может быть собран с помощью MessageBuilder

#### Функция пересылки

> **Внимание**: Функция пересылки должна быть реализована через Send DSL адаптера; сам класс Event Wrapper не предоставляет прямых методов для пересылки.

```python
# Пересылка сообщения в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или указать другой ID группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### Функция ожидания ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None)` - ожидание ответа пользователя
  - `prompt`: сообщение-запрос, если предоставлено, будет отправлено пользователю
  - `timeout`: время ожидания (в секундах), по умолчанию 60 секунд
  - `callback`: функция обратного вызова, выполняемая при получении ответа
  - `validator`: функция проверки, используемая для валидации ответа
  - Возвращает объект Event ответа пользователя, если время истекло, возвращает None

#### Методы взаимодействия

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None)` - подтверждение диалога
  - Возвращает `True` (подтверждение) / `False` (отрицание) / `None` (тайм-аут)
  - Автоматическое распознавание встроенных слов подтверждения на китайском и английском, настраиваемый набор слов

- `choose(prompt, options, timeout=60.0)` - меню выбора
  - `options`: список текстов опций
  - Возвращает индекс опции (0-based), если тайм-аут, возвращает `None`

- `collect(fields, timeout_per_field=60.0)` - сбор формы
  - `fields`: список полей, каждое поле содержит `key`, `prompt`, необязательный `validator`
  - Возвращает словарь `{key: value}`, если тайм-аут любого поля, возвращает `None`

- `wait_for(event_type="message", condition=None, timeout=60.0)` - ожидание произвольного события
  - `condition`: функция фильтрации, возвращает `True`, когда совпадает
  - Возвращает совпавший объект Event, если тайм-аут, возвращает `None`

- `conversation(timeout=60.0)` - создание контекста многоходового диалога
  - Возвращает объект `Conversation`, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - Атрибут `is_active` указывает, активен ли диалог

#### Методы взаимодействия 示例

**confirm() - подтверждение диалога:**

```python
@command("delete", help="удалить данные")
async def delete_handler(event):
    if await event.confirm("Вы действительно хотите удалить все данные?"):
        sdk.storage.delete("all_data")
        await event.reply("Данные удалены")
    else:
        await event.reply("Отменено")
```

**choose() - меню выбора:**

```python
@command("color", help="выбрать цвет")
async def color_handler(event):
    choice = await event.choose("Выберите цвет:", ["красный", "зеленый", "синий"])
    if choice is not None:
        colors = ["красный", "зеленый", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
```

**collect() - сбор формы:**

```python
@command("register", help="зарегистрироваться")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "Введите имя:"},
        {"key": "age", "prompt": "Введите возраст:",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"Регистрация прошла успешно! {data['name']}, {data['age']} лет")
```

**non-Text методы reply:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Посмотрите на эту картинку:").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Полное использование многошагового диалога с помощью Conversation см. в [Документации по многошаговому диалогу](../../advanced/conversation.md).

### Информация о командах

#### Базовая информация о команде
- `get_command_name()` - получить имя команды
- `get_command_args()` - получить список аргументов команды
- `get_command_raw()` - получить исходный текст команды
- `get_command_info()` - получить полный словарь информации о команде
- `is_command()` - является ли это командой

### Необработанные данные

- `get_raw()` - получить исходные данные события платформы
- `get_raw_type()` - получить исходный тип события платформы

### Расширенные методы платформы

Адаптеры регистрируют собственные методы для каждой платформы, ниже приведены типичные примеры (конкретные методы см. в документации по [платформе](../../platform-guide/)):

- `get_platform_event_methods(platform)` - запрос списка расширенных методов, зарегистрированных для указанной платформы
- Расширенные методы платформы доступны только на экземплярах Event для соответствующей платформы
- Доступ к методам можно безопасно проверить с помощью `hasattr(event, "method_name")`

### Утилитарные методы

- `to_dict()` - преобразовать в обычный словарь
- `is_processed()` - было ли обработано
- `mark_processed()` - пометить как обработанное

### Доступ через точку

Event наследуется от dict, поддерживает доступ через точку для всех ключей словаря:

```python
platform = event.platform          # эквивалент event["platform"]
user_id = event.user_id          # эквивалент event["user_id"]
message = event.message          # эквивалент event["message"]
```

## Расширенные методы платформы

Адаптер может регистрировать платформенные методы для класса Event Wrapper. Методы доступны только на экземплярах Event соответствующей платформы, при доступе с другой платформы выбрасывается `AttributeError`.

```python
# Email-событие - только методы для Email
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ возвращает "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram-событие - только методы для Telegram
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ возвращает "private"
event.get_subject()      # ❌ AttributeError

# Встроенные методы всегда доступны
event.get_text()         # ✅ для любой платформы
event.reply("hi")        # ✅ для любой платформы
```

### Поиск зарегистрированных методов

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### Поддержка `hasattr` и `dir`

```python
hasattr(event, "get_subject")   # возвращает True только
```
注意：源文档可能有更新，请以源文档为准进行翻译，但术语、用词风格应与参考翻译保持一致。

## Связанные документы

- [Введение в модульное программирование](getting-started.md) - создание первого модуля
- [Лучшие практики](best-practices.md) - разработка высококачественных модулей