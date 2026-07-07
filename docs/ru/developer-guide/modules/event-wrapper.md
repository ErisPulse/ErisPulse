# Подробное объяснение класса обертки Event

Модуль Event предоставляет мощный класс обертки Event, упрощающий обработку событий.

## Основные характеристики

- **Полная совместимость со словарем**: Event наследуется от dict
- **Удобные методы**: Предоставляются множество удобных методов
- **Доступ через точку**: Поддерживается доступ к полям события с помощью точки
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

## Методы событий сообщений

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}!")
```

## Определение типа сообщения

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"Тип: {'Личное сообщение' if is_private else 'Группа'}")
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
        await event.reply(f"Привет, {name}!")
```

## Получение информации о команде

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"Команда: {cmd_name}, Параметры: {cmd_args}")
```

## Методы событий уведомлений

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("Добро пожаловать в друзья!")
```

## Справочник методов

### Основные методы

#### Основная информация о событии
- `get_id()` - Получить ID события
- `get_time()` - Получить временную метку события (Unix в секундах)
- `get_type()` - Получить тип события (message/notice/request/meta)
- `get_detail_type()` - Получить подробный тип события (private/group/friend и т.д.)
- `get_platform()` - Получить название платформы

#### Информация о боте
- `get_self_platform()` - Получить название платформы бота
- `get_self_user_id()` - Получить ID пользователя бота
- `get_self_account_id()` - Получить ID учетной записи бота (режим нескольких ботов)
- `get_self_info()` - Получить полную информацию о боте в виде словаря

#### Идентификатор сессии
- `get_target_id()` - Получить единый идентификатор цели (для групповых сообщений возвращает `group_id`, для каналов `channel_id`, для личных сообщений `user_id`, возвращается первый непустой из: group → channel → guild → thread → user)
- `get_session_id()` - Получить уникальный идентификатор сессии, формат: `{platform}:{detail_type}:{target_id}`

### Методы событий сообщений

#### Содержимое сообщения
- `get_message()` - Получить массив сегментов сообщения (формат OneBot12)
- `get_alt_message()` - Получить альтернативный текст сообщения
- `get_text()` - Получить чистый текст (псевдоним для `get_alt_message()`)
- `get_message_text()` - Получить чистый текст (псевдоним для `get_alt_message()`)

#### Информация отправителя
- `get_user_id()` - Получить ID пользователя-отправителя
- `get_user_nickname()` - Получить никнейм отправителя
- `get_sender()` - Получить полную информацию об отправителе в виде словаря

#### Информация о группе/канале
- `get_group_id()` - Получить ID группы (для сообщений в группе)
- `get_channel_id()` - Получить ID канала (для сообщений в канале)
- `get_guild_id()` - Получить ID сервера (для сообщений на сервере)
- `get_thread_id()` - Получить ID темы/подканала (для сообщений в теме)

#### Связанные с @ сообщениями
- `has_mention()` - Содержит ли сообщение упоминание бота
- `get_mentions()` - Получить список ID всех упомянутых пользователей

### Определение типа сообщения

#### Основные проверки
- `is_message()` - Является ли событием сообщения
- `is_private_message()` - Является ли личным сообщением
- `is_group_message()` - Является ли групповым сообщением
- `is_at_message()` - Является ли сообщением с упоминанием (`has_mention()`)

### Методы событий уведомлений

#### Информация об операторе
- `get_operator_id()` - Получить ID оператора
- `get_operator_nickname()` - Получить никнейм оператора

#### Определение типа уведомления
- `is_notice()` - Является ли событием уведомления
- `is_group_member_increase()` - Событие увеличения участников группы
- `is_group_member_decrease()` - Событие уменьшения участников группы
- `is_friend_add()` - Событие добавления в друзья (соответствует `detail_type == "friend_increase"`)
- `is_friend_delete()` - Событие удаления из друзей (соответствует `detail_type == "friend_decrease"`)

### Методы событий запросов

#### Информация о запросе
- `get_comment()` - Получить комментарий к запросу

#### Определение типа запроса
- `is_request()` - Является ли событием запроса
- `is_friend_request()` - Является ли запросом на добавление в друзья
- `is_group_request()` - Является ли запросом на добавление в группу

### Функция ответа

#### Базовый ответ
- `reply(content, method="Text", at_sender=False, reply_to_message=False, at_users=None, reply_to=None, at_all=False, **kwargs)` - Общий метод ответа
  - `content`: Содержимое для отправки (текст, URL и т.д.)
  - `method`: Метод отправки, по умолчанию "Text", можно использовать "Image"/"Voice"/"Video"/"File" и т.д.
  - `at_sender`: Упоминать ли отправителя (автоматически извлекает user_id)
  - `quote`: Цитировать ли текущее сообщение (автоматически извлекает message_id)
  - `at_users`: Список упомянутых пользователей, например `["user1", "user2"]`
  - `reply_to`: Ручное указание ID сообщения для ответа
  - `at_all`: Упоминать ли всех участников
  - `**kwargs`: Дополнительные параметры (например, user_id для метода Mention)

- `reply_ob12(message)` - Ответ с использованием OneBot12 сегментов сообщения
  - `message`: Список или словарь сегментов OneBot12, можно использовать MessageBuilder для построения

#### Проверка возможностей платформы
- `supports(method)` - Проверить, поддерживает ли текущая платформа метод отправки (например, `"Image"`, `"Voice"`), возвращает `bool`
- `available_methods()` - Получить список всех доступных методов отправки на текущей платформе, возвращает список названий методов

#### Функция пересылки

> **Внимание**: Функция пересылки должна реализовываться через DSL отправки адаптера, Event wrapper не предоставляет прямых методов пересылки.

```python
# Переслать сообщение в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или указать другой ID группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### Функция ожидания ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text")` - Ожидание ответа пользователя
  - `prompt`: Сообщение-подсказка, если указано, будет отправлено пользователю
  - `timeout`: Время ожидания (секунды), по умолчанию 60 секунд
  - `callback`: Функция обратного вызова, выполняется при получении ответа
  - `validator`: Функция проверки, используется для валидации ответа
  - `method`: Метод отправки, по умолчанию "Text"
  - Возвращает объект Event с ответом пользователя, при таймауте возвращает None

#### Интерактивные методы

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Подтверждение диалога
  - Возвращает `True` (подтверждение) / `False` (отрицание) / `None` (таймаут)
  - Встроенные слова подтверждения на китайском и английском языках, можно настроить собственные наборы слов
  - `method`: Метод отправки, по умолчанию "Text"; поддерживает "Image"/"Markdown" и другие не-текстовые способы отправки подсказки
  - `hint`: Добавлять ли автоматически подсказку с словами подтверждения в конце подсказки (например, "（是/否）" ), по умолчанию False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="list", merge_prompt=False)` - Меню выбора
  - `options`: Список текстовых вариантов
  - Возвращает индекс выбранного варианта (начиная с 0), при таймауте возвращает `None`
  - `method`: Метод отправки; текстовые методы (Text/Markdown/Html) объединяют варианты с prompt в одно сообщение; методы с мультимедиа сначала отправляют мультимедийное содержимое, затем Text-список вариантов
  - `options_format`: Формат вариантов, поддерживает `"list"` (по умолчанию, по одному варианту в строке), `"inline"` (все варианты в одной строке `1.A | 2.B`) или пользовательскую функцию `(list[str]) -> str`
  - `merge_prompt`: Принудительно объединять ли варианты в одно Text-сообщение при не-текстовых методах, по умолчанию False

- `collect(fields, timeout_per_field=60.0)` - Сбор формы
  - `fields`: Список полей, каждое поле содержит `key`, `prompt`, необязательный `validator`, необязательный `method`
  - Возвращает словарь `{key: value}`, при таймауте любого поля возвращает `None`
  - Каждое поле может иметь ключ `method`, чтобы указать метод отправки, например, при сборе изображения: `{"key": "avatar", "prompt": "Пожалуйста, отправьте аватар", "method": "Image"}`
  - Каждое поле может иметь ключ `options` (список), при наличии этот тип поля становится выборочным (автоматически вызывается логика choose)
  - Каждое поле может иметь ключи `options_format` и `merge_prompt`, чтобы контролировать формат вариантов и поведение объединения сообщений

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Ожидание произвольного события
  - `condition`: Фильтрующая функция, возвращает `True` при совпадении
  - Возвращает соответствующий объект Event, при таймауте возвращает `None`

- `conversation(timeout=60.0)` - Создать контекст многошагового диалога
  - Возвращает объект `Conversation`, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - Свойство `is_active` указывает, активен ли диалог

#### Примеры интерактивных методов

**confirm() - Подтверждение диалога:**

```python
@command("delete", help="Удалить данные")
async def delete_handler(event):
    if await event.confirm("Вы действительно хотите удалить все данные?"):
        sdk.storage.delete("all_data")
        await event.reply("Данные удалены")
    else:
        await event.reply("Отменено")
```

**confirm() - С подсказкой:**

```python
# hint=True добавляет в конец подсказки "（是/否）"
if await event.confirm("Продолжить?", hint=True):
    await event.reply("Продолжено")
# Пользователь видит: Продолжить?（是/否）
```

**choose() - Меню выбора:**

```python
@command("color", help="Выбрать цвет")
async def color_handler(event):
    choice = await event.choose("Выберите цвет:", ["Красный", "Зеленый", "Синий"])
    if choice is not None:
        colors = ["Красный", "Зеленый", "Синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
```

**choose() - Форматирование и объединение вариантов:**

```python
# inline формат: варианты отображаются в одной строке
choice = await event.choose("Выберите:", ["A", "B", "C"], options_format="inline")
# Вывод: 1.A | 2.B | 3.C

# Пользовательская функция форматирования
choice = await event.choose("Выберите:", ["Кошка", "Собака"],
    options_format=lambda opts: " / ".join(opts))
# Вывод: Кошка / Собака

# Не-текстовый метод + объединение вариантов в текст
choice = await event.choose("Выберите по картинке:", ["Кошка", "Собака"],
    method="Image", merge_prompt=True)
```

**collect() - Сбор формы:**

```python
@command("register", help="Регистрация")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "Введите имя:"},
        {"key": "age", "prompt": "Введите возраст:",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"Регистрация успешна! {data['name']}, {data['age']} лет")
```

**reply с не-Text методами:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Посмотрите на эту картинку:").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Полное использование многошагового диалога через Conversation см. в [Многошаговый диалог](../../advanced/conversation.md).

### Информация о команде

#### Основа команды
- `get_command_name()` - Получить название команды
- `get_command_args()` - Получить список параметров команды
- `get_command_raw()` - Получить исходный текст команды
- `get_command_info()` - Получить полную информацию о команде в виде словаря
- `is_command()` - Является ли событием команды

### Исходные данные

- `get_raw()` - Получить исходные данные события платформы
- `get_raw_type()` - Получить тип исходного события платформы

### Платформенные расширения

Адаптеры могут регистрировать платформенно-специфичные методы для класса обертки Event. Методы доступны только на экземплярах Event для соответствующей платформы, при доступе с других платформ будет выброшено исключение `AttributeError`.

Платформенные методы через `Event.__getattribute__` имеют приоритет над встроенными методами, поэтому можно переопределить встроенные интерактивные методы, такие как `confirm`、`choose`、`collect`、`wait_reply`, предоставив платформенно-специфичную реализацию (например, кнопки, карточки). Встроенная реализация экспортируется как `_builtin_*` функции для переопределения.

```python
# Событие электронной почты - только методы электронной почты
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ Возвращает "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram событие - только методы Telegram
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ Возвращает "private"
event.get_subject()      # ❌ AttributeError

# Встроенные методы всегда доступны
event.get_text()         # ✅ На любой платформе
event.reply("hi")        # ✅ На любой платформе
```

### Получение зарегистрированных методов

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### Поддержка hasattr и dir

```python
hasattr(event, "get_subject")   # Возвращает True только если platform="email"
"get_subject" in dir(event)     # То же самое
```

### Кросс-платформенное расширение (шаблон)

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве названия платформы, регистрируя методы, доступные на **всех** платформах. Подходит для функций, требующих кросс-платформенного повторного использования, таких как AI-диалоги, управление контекстом и т.д.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self - экземпляр Event, доступ к данным события и встроенным методам
    await self.reply(f"AI: {prompt}")
```

После регистрации, любой обработчик событий на любой платформе может вызывать `event.ai_chat(...)`.

Приоритет разрешения методов (от высшего к низшему): платформенно-специфичные методы → шаблонные методы → встроенные методы → доступ через ключ словаря.

> Способ регистрации расширенных методов адаптерами см. в [API системы событий - Кросс-платформенное расширение (шаблон)](../../api-reference/event-system.md#кросс-платформенное-расширение-шаблон).

## Связанные документы

- [Введение в разработку модулей](getting-started.md) - Создание первого модуля
- [Лучшие практики](best-practices.md) - Разработка высококачественных модулей