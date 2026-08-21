# Подробное объяснение класса-обертки Event

Модуль Event предоставляет мощный класс-обертку Event, упрощающий обработку событий.

Пожалуйста, верните сразу переведенный полный Markdown-контент, не добавляя никаких других слов.

Еще раз напоминаю: если документ содержит строку с переключением языка (где названия языков разделены символом `` | ``), строго соблюдайте вышеуказанные правила форматирования, не создавайте ошибочных форматов вида ``[**Label**](file)``.

## Добавление аннотаций типов для параметра event

Параметр `event` обработчика событий является **обёрткой Event** (подкласс dict). Рекомендуется добавлять для него аннотации типов:

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE автоматически подсказывает все удобные методы
    await event.reply(text)   # Опечатки обнаруживаются на этапе статической проверки
```

Без аннотаций IDE не может распознавать методы Event (`get_text()` / `reply()` / `wait_reply()` / методы расширения платформы не подсказываются), и приходится полагаться на память при написании.

> **Важно различать**: `event` в обратном вызове обработчика событий — это **обёртка Event** (аннотация `Event`); `event` в методах жизненного цикла модуля `on_load` / `on_unload` — это обычный **dict** (аннотация `dict`), не следует их путать.

[**中文**](docs/ru/quick-start.md)

## Основные возможности

- **Полная совместимость со словарем**: Event наследуется от dict
- **Удобные методы**: Предоставляются много удобных методов
- **Доступ через точку**: Поддерживается доступ к полям события через точку
- **Обратная совместимость**: Все методы являются необязательными

- [Справочник](docs/ru/reference.md)
- [Руководство по быстрому старту](docs/ru/quick-start.md)
- [Руководство по установке](docs/ru/installation.md)
- [Примеры](docs/ru/examples.md)
- [Заметки о версиях](docs/ru/changelog.md)

## Основные методы полей

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, Платформа: {platform}, Время: {time}")
```

[**English**](docs/ru/quick-start.md)

## Методы событий сообщений

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}!")
```

[**English**](docs/ru/quick-start.md)

## Определение типа сообщения

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"Тип: {'Личное сообщение' if is_private else 'Группа'}")
```

[**中文**](docs/ru/message-type-detection.md) | [**English**](docs/en/message-type-detection.md) | [**Русский**](docs/ru/message-type-detection.md)

## Функция ответа

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event: Event):
    await event.reply("Пожалуйста, введите ваше имя:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")
```

[**English**](docs/ru/quick-start.md)

## Получение информации о команде

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"Команда: {cmd_name}, аргументы: {cmd_args}")
```

[**English**](docs/ru/quick-start.md) | [**Русский**](docs/ru/quick-start.md)

## Метод уведомления событий

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("Добро пожаловать, добавьте меня в друзья!")
```

[**English**](docs/ru/quick-start.md)

## Справочник методов

### Основные методы

#### Базовая информация об событии
- `get_id()` - Получить идентификатор события
- `get_time()` - Получить метку времени события (Unix в секундах)
- `get_type()` - Получить тип события (message/notice/request/meta)
- `get_detail_type()` - Получить подробный тип события (private/group/friend и т.д.)
- `get_platform()` - Получить название платформы

#### Информация о боте
- `get_self_platform()` - Получить название платформы бота
- `get_self_user_id()` - Получить идентификатор пользователя бота
- `get_self_account_id()` - Получить идентификатор аккаунта бота (режим множественных ботов)
- `get_self_info()` - Получить полный словарь информации о боте

#### Идентификаторы сессии
- `get_target_id()` - Получить единый идентификатор цели (для групповых чатов возвращает `group_id`, для каналов `channel_id`, для личных сообщений `user_id`, выбирает первый непустой по порядку group → channel → guild → thread → user)
- `get_session_id()` - Получить уникальный идентификатор сессии, формат: `{platform}:{detail_type}:{target_id}`

### Методы событий сообщений

#### Содержание сообщения
- `get_message()` - Получить массив сегментов сообщения (формат OneBot12)
- `get_alt_message()` - Получить резервный текст сообщения
- `get_text()` - Получить чистый текст (альтернативное имя для `get_alt_message()`)
- `get_message_text()` - Получить чистый текст (альтернативное имя для `get_alt_message()`)

#### Информация об отправителе
- `get_user_id()` - Получить идентификатор пользователя-отправителя
- `get_user_nickname()` - Получить никнейм отправителя
- `get_sender()` - Получить полный словарь информации об отправителе

#### Информация о группе/канале
- `get_group_id()` - Получить идентификатор группы (сообщения в группе)
- `get_channel_id()` - Получить идентификатор канала (сообщения в канале)
- `get_guild_id()` - Получить идентификатор сервера (сообщения на сервере)
- `get_thread_id()` - Получить идентификатор темы/подканала (сообщения в теме)

#### Связанные с упоминаниями
- `has_mention()` - Содержит ли сообщение упоминание бота
- `get_mentions()` - Получить список всех упомянутых пользователей

### Определение типа сообщения

#### Основные проверки
- `is_message()` - Является ли событием сообщения
- `is_private_message()` - Является ли личным сообщением
- `is_group_message()` - Является ли сообщением в группе
- `is_at_message()` - Является ли сообщением с упоминанием (альтернативное имя для `has_mention()`)

### Методы событий уведомлений

#### Информация об операторе
- `get_operator_id()` - Получить идентификатор оператора
- `get_operator_nickname()` - Получить никнейм оператора

#### Определение типа уведомления
- `is_notice()` - Является ли событием уведомления
- `is_group_member_increase()` - Событие увеличения участников группы
- `is_group_member_decrease()` - Событие уменьшения участников группы
- `is_friend_add()` - Событие добавления друга (соответствует `detail_type == "friend_increase"`)
- `is_friend_delete()` - Событие удаления друга (соответствует `detail_type == "friend_decrease"`)

### Методы событий запросов

#### Информация о запросе
- `get_comment()` - Получить комментарий к запросу

#### Определение типа запроса
- `is_request()` - Является ли событием запроса
- `is_friend_request()` - Является ли запросом дружбы
- `is_group_request()` - Является ли запросом группы

### Функции ответа

#### Базовый ответ
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - Общий метод ответа
  - `content`: содержимое отправки (текст, URL и т.д.)
  - `method`: метод отправки, по умолчанию "Text", возможные значения "Image"/"Voice"/"Video"/"File" и т.д.
  - `at_sender`: упоминать ли отправителя (автоматически извлекает user_id)
  - `quote`: цитировать ли текущее сообщение (автоматически извлекает message_id)
  - `at_users`: список пользователей для упоминания, например `["user1", "user2"]`
  - `reply_to`: вручную указать идентификатор сообщения для ответа
  - `at_all`: упоминать ли всех участников
  - `**kwargs`: дополнительные параметры (например user_id для метода Mention)

- `reply_ob12(message)` - Ответ с использованием OneBot12 сегментов сообщения
  - `message`: список или словарь сегментов OneBot12, можно использовать MessageBuilder для построения

#### Проверка возможностей платформы
- `supports(method)` - Проверить, поддерживает ли текущая платформа метод отправки (например `"Image"`, `"Voice"`), возвращает `bool`
- `available_methods()` - Получить список всех доступных методов отправки на текущей платформе, возвращает список названий методов

#### Пересылка сообщений

> **Внимание:** Функция пересылки должна реализовываться через DSL отправки адаптера, Event wrapper класс не предоставляет прямой метод пересылки.

```python
# Переслать сообщение в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или указать другой идентификатор группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### Функция ожидания ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text")` - Ожидать ответ пользователя
  - `prompt`: сообщение-подсказка, если указано, будет отправлено пользователю
  - `timeout`: время ожидания (в секундах), по умолчанию 60 секунд
  - `callback`: функция обратного вызова, выполняется при получении ответа
  - `validator`: функция проверки, используется для валидации ответа
  - `method`: метод отправки подсказки, по умолчанию "Text"
  - Возвращает Event объект с ответом пользователя, при таймауте возвращает None

#### Интерактивные методы

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Подтверждение диалога
  - Возвращает `True` (подтверждение) / `False` (отрицание) / `None` (таймаут)
  - Встроенные английские и китайские слова автоматически распознаются, можно задать собственные наборы слов
  - `method`: метод отправки, по умолчанию "Text"; поддерживает "Image"/"Markdown" и другие не текстовые способы отправки подсказки
  - `hint`: добавлять ли автоматически подсказку с вариантами ответа в конец сообщения (например "（是/否）"), по умолчанию False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Меню выбора
  - `options`: список текстов вариантов
  - Возвращает индекс выбранного варианта (от 0), при таймауте возвращает `None`
  - `method`: метод отправки, по умолчанию "Text"; текстовые методы (Text/Markdown/md/Html/h5) по умолчанию объединяют варианты в конец
  - `options_format`: формат вариантов (по умолчанию: "auto", автоматически выбирается встроенный стиль в зависимости от method)
    - `"auto"`: Markdown→неупорядоченный список (`- 1. вариант`), Html→упорядоченный список (`<ol>`), остальное→простой текстовый список
    - `"list"`: каждый вариант на отдельной строке, например ``1. ВариантA\n2. ВариантB``
    - `"inline"`: варианты отображаются в одной строке, например ``1.A | 2.B``
    - `"md"`: Markdown неупорядоченный список
    - `"html"`: Html упорядоченный список
    - `callable`: пользовательская функция, принимает ``list[str]`` и возвращает ``str``
  - `merge_prompt`: принудительно объединять ли в одно сообщение, по умолчанию False
    - `False` (по умолчанию): текстовые методы автоматически объединяют; для не текстовых методов сначала отправляется prompt, затем Text варианты
    - `True`: независимо от method объединяются в одно сообщение и отправляются с указанным method
  - `placeholder`: маркер для вставки вариантов, по умолчанию `{options}`; текст внутри prompt, где встречается этот маркер, заменяется на текст вариантов, если установить пустую строку, варианты всегда добавляются в конец

- `collect(fields, timeout_per_field=60.0)` - Сбор формы
  - `fields`: список полей, каждое содержит `key`, `prompt`, опционально `validator`, опционально `method`
  - Возвращает словарь `{key: value}`, при таймауте любого поля возвращает `None`
  - Каждое поле может иметь ключ `method` для указания метода отправки, например для сбора изображения: `{"key": "avatar", "prompt": "Пожалуйста, отправьте аватар", "method": "Image"}`
  - Каждое поле может иметь ключ `options` (список), при наличии этого ключа поле становится выборочным (автоматически вызывается choose логика)
  - Каждое поле может иметь ключи `options_format`, `merge_prompt`, `placeholder`, для управления форматом вариантов, поведением объединения сообщений и маркером

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Ожидать произвольного события
  - `condition`: фильтрующая функция, возвращает `True` при совпадении
  - Возвращает соответствующий Event объект, при таймауте возвращает `None`

- `conversation(timeout=60.0)` - Создать контекст многошагового диалога
  - Возвращает `Conversation` объект, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - Свойство `is_active` указывает, активен ли диалог

#### Примеры интерактивных методов

**confirm() - Подтверждение диалога:**

```python
@command("delete", help="Удалить данные")
async def delete_handler(event: Event):
    if await event.confirm("Вы действительно хотите удалить все данные?"):
        sdk.storage.delete("all_data")
        await event.reply("Данные удалены")
    else:
        await event.reply("Отменено")
```

**confirm() - С подсказкой:**

```python
# hint=True добавит в конец подсказки "（是/否）"
if await event.confirm("Продолжить?", hint=True):
    await event.reply("Продолжено")
# Пользователь увидит: Продолжить?（是/否）
```

**choose() - Меню выбора:**

```python
@command("color", help="Выбрать цвет")
async def color_handler(event: Event):
    choice = await event.choose("Выберите цвет:", ["红色", "绿色", "蓝色"])
    if choice is not None:
        colors = ["红色", "绿色", "蓝色"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
```

**choose() - Форматирование вариантов и объединение сообщений:**

```python
# inline формат: варианты отображаются в одной строке
choice = await event.choose("Выберите:", ["A", "B", "C"], options_format="inline")
# Вывод: 1.A | 2.B | 3.C

# Пользовательская функция форматирования
choice = await event.choose("Выберите:", ["猫", "狗"],
    options_format=lambda opts: " / ".join(opts))
# Вывод: 猫 / 狗

# options_format="auto" (по умолчанию): автоматически выбирается встроенный стиль в зависимости от method
# Markdown → неупорядоченный список
choice = await event.choose(
    "## Выберите", ["猫", "狗"],
    method="Markdown",  # auto автоматически распознает как md список
)
# Вывод:
# ## Выберите
# - 1. 猫
# - 2. 狗

# Html → упорядоченный список
choice = await event.choose(
    "<h2>Выберите</h2>", ["猫", "狗"],
    method="Html", merge_prompt=True,  # auto автоматически распознает как html список
)
# Вывод:
# <h2>Выберите</h2>
# <ol><li>1. 猫</li><li>2. 狗</li></ol>

# Режим объединения + маркер
choice = await event.choose(
    "## Выберите\n{options}\nПожалуйста, ответьте номером",
    ["猫", "狗"],
    method="Markdown", merge_prompt=True,
)

# Пользовательский маркер
choice = await event.choose(
    "Выберите: [choices]",
    ["猫", "狗"],
    placeholder="[choices]",
)
```

**collect() - Сбор формы:**

```python
@command("register", help="Регистрация")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "Введите имя:"},
        {"key": "age", "prompt": "Введите возраст:",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"Регистрация успешна! {data['name']}, {data['age']} лет")
```

**reply с не Text методами:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Посмотрите на эту картинку：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Полное использование многошагового диалога через Conversation см. в [Многошаговый диалог](../../advanced/conversation.md).

### Информация о команде

#### Основы команды
- `get_command_name()` - Получить имя команды
- `get_command_args()` - Получить список аргументов команды
- `get_command_raw()` - Получить исходный текст команды
- `get_command_info()` - Получить полный словарь информации о команде
- `is_command()` - Является ли событием команды

### Исходные данные

- `get_raw()` - Получить исходные данные события платформы
- `get_raw_type()` - Получить тип исходного события платформы

### Платформенные расширения

Адаптеры могут регистрировать платформенно-специфичные методы для Event wrapper класса. Методы доступны только на экземплярах Event соответствующей платформы, попытка доступа с других платформ вызывает `AttributeError`.

Платформенные методы имеют приоритет над встроенными методами через `Event.__getattribute__`, поэтому можно переопределить встроенные интерактивные методы (`confirm`, `choose`, `collect`, `wait_reply`), предоставив платформенно-специфичную реализацию (например, кнопки, карточки). Встроенная реализация экспортируется как `_builtin_*` функции для переопределения.

```python
# Почтовое событие - только почтовые методы
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ Возвращает "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram событие - только Telegram методы
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ Возвращает "private"
event.get_subject()      # ❌ AttributeError

# Встроенные методы всегда доступны
event.get_text()         # ✅ На любой платформе
event.reply("hi")        # ✅ На любой платформе
```

### Запрос зарегистрированных методов

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

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве названия платформы, регистрируя методы, доступные на **всех** платформах Event экземпляров. Подходит для функций, требующих переносимости между платформами, таких как AI диалоги, управление контекстом и т.д.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self - экземпляр Event, можно получить доступ к данным события и встроенным методам
    await self.reply(f"AI: {prompt}")
```

После регистрации, любой обработчик событий на любой платформе может вызвать `event.ai_chat(...)`.

Приоритет разрешения методов (от высшего к низшему): платформенно-специфичный метод → шаблонный метод → встроенный метод → доступ по ключу словаря.

> Способ регистрации расширений адаптерами см. в [API системы событий - Кросс-платформенное расширение (шаблон)](../../api-reference/event-system.md#跨平台扩展通配符).

## Связанные документы

- [Введение в разработку модулей](docs/ru/getting-started.md) - Создание первого модуля
- [Лучшие практики](docs/ru/best-practices.md) - Разработка качественных модулей