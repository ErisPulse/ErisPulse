# Подробное объяснение Event-обертки

> [!NOTE]
> **Обязательное чтение на уровне L1** — одна из пяти основных документов в "пути чтения" на главной странице, необходима для разработки модулей.

Параметр `event` в обработчиках, благодаря Event-обертке, может напрямую использовать методы `.get_text()`, `.reply()`, `.wait_reply()`. В данной статье представлен полный список методов Event-обертки — обращайтесь к ней при написании обработчиков событий, все методы и их поведение должны соответствовать описанию здесь.

## Добавление аннотации типа для параметра `event`

Параметр `event` в обработчике событий является **Event-оберткой** (подклассом dict). Рекомендуется добавлять аннотацию типа:

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE автоматически подсказывает все удобные методы
    await event.reply(text)   # Опечатки будут выявлены на этапе статической проверки
```

Без аннотации IDE не сможет распознать методы Event-обертки (`get_text()`, `reply()`, `wait_reply()` и расширения для платформы), и придется полагаться на память.

> **Обратите внимание:** параметр `event` в обработчике событий — это **Event-обертка** (аннотация `Event`); параметр `event` в методах жизненного цикла модуля `on_load` / `on_unload` — это обычный **dict** (аннотация `dict`), не путайте их.

## Основные характеристики

- **Полная совместимость с dict**: Event наследуется от dict
- **Удобные методы**: предоставляет множество удобных методов
- **Доступ через точку**: поддерживает доступ к полям события через точку
- **Обратная совместимость**: все методы являются необязательными

## Основные методы полей

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, платформа: {platform}, время: {time}")
```

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

## Определение типа сообщения

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"Тип: {'личное сообщение' if is_private else 'группа'}")
```

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

@command("price")
async def price_command(event: Event):
    await event.reply("Пожалуйста, введите сумму (например: 5 юаней):")
    # Ответ должен соответствовать регулярному выражению, иначе ждем, пока не истечет таймаут
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"Получена сумма: {reply.get_text()}")
```

## Расширенные функции интерактивной сессии

> [!NOTE]
> Эта функциональность доступна начиная с ErisPulse **2.8.0+**.

```python
# Напоминание сессии: если 5 минут нет ответа, напоминаем, пользователь ответит, автоматически отменяется
reminder = event.remind(300, "Еще здесь? Если не хочешь общаться, ответь «выйти»")
reminder.cancel()  # Можно и вручную отменить

# Превышение времени: по истечении срока обязательно срабатывает (не отменяется ответом), например, уведомление владельцу при длительной обработке
event.escalate(1800, lambda e: notify_master("Заявка просрочена"))

# Ожидание нескольких путей: одновременно ждем "согласие" и "отказ", срабатывает первый пришедший
which, reply = await event.select(
    event.expect(pattern="согласие*", user="10001"),
    event.expect(pattern="отказ*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("Таймаут, ответ не получен")

# Ожидание сессии: любой пользователь в группе может ответить (сотрудничество в группе)
reply = await event.wait_reply(session=True, prompt="Кто-нибудь поможет ответить?")

# Ящик сессии: последние 20 сообщений текущей сессии (включая бота, контекст ИИ / база для предотвращения повторений)
messages = await event.history(20)

# Транзакция сообщений: при возникновении исключения автоматически отменяются отправленные сообщения в рамках транзакции
async with event.message_tx():
    await event.reply("Обработка, подождите...")
    result = await do_something()
    await event.reply(f"Завершено: {result}")
```

## Получение информации о команде

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"Команда: {cmd_name}, аргументы: {cmd_args}")
```

## Методы уведомлений

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("Добро пожаловать, добавьте меня в друзья!")
```

## Справочник методов

### Основные методы

#### Основная информация о событии
- `get_id()` - Получить ID события
- `get_time()` - Получить метку времени события (Unix в секундах)
- `get_type()` - Получить тип события (message/notice/request/meta)
- `get_detail_type()` - Получить подробный тип события (private/group/friend и т.д.)
- `get_platform()` - Получить название платформы

#### Информация о боте
- `get_self_platform()` - Получить название платформы бота
- `get_self_user_id()` - Получить ID пользователя бота
- `get_self_account_id()` - Получить ID аккаунта бота (режим с несколькими ботами)
- `get_self_info()` - Получить полную информацию о боте в виде словаря

#### Идентификаторы сессии
- `get_target_id()` - Получить уникальный идентификатор цели (для групповых чатов возвращает `group_id`, для каналов `channel_id`, для личных сообщений `user_id`, в порядке group → channel → guild → thread → user возвращает первое не пустое значение)
- `get_session_id()` - Получить уникальный идентификатор сессии, в формате `{platform}:{detail_type}:{target_id}`

### Методы событий сообщений

#### Содержимое сообщения
- `get_message()` - Получить массив сегментов сообщения (формат OneBot12)
- `get_alt_message()` - Получить резервный текст сообщения
- `get_text()` - Получить чистый текст (альтернативное имя `get_alt_message()`)
- `get_message_text()` - Получить чистый текст (альтернативное имя `get_alt_message()`)

#### Информация об отправителе
- `get_user_id()` - Получить ID пользователя-отправителя
- `get_user_nickname()` - Получить никнейм отправителя
- `get_sender()` - Получить полную информацию об отправителе в виде словаря

#### Информация о группе/канале
- `get_group_id()` - Получить ID группы (сообщения в группе)
- `get_channel_id()` - Получить ID канала (сообщения в канале)
- `get_guild_id()` - Получить ID сервера (сообщения на сервере)
- `get_thread_id()` - Получить ID темы/подканала (сообщения в теме)

#### Связанные с @ сообщениями
- `has_mention()` - Содержит ли сообщение упоминание бота
- `get_mentions()` - Получить список ID всех упомянутых пользователей

### Определение типа сообщения

#### Базовые проверки
- `is_message()` - Является ли событием сообщения
- `is_private_message()` - Является ли личным сообщением
- `is_group_message()` - Является ли групповым сообщением
- `is_at_message()` - Является ли сообщением с упоминанием (`has_mention()`)

### Методы уведомлений

#### Информация об операторе
- `get_operator_id()` - Получить ID оператора
- `get_operator_nickname()` - Получить никнейм оператора

#### Определение типа уведомления
- `is_notice()` - Является ли событием уведомления
- `is_group_member_increase()` - Событие добавления участника в группу
- `is_group_member_decrease()` - Событие удаления участника из группы
- `is_friend_add()` - Событие добавления друга (соответствует `detail_type == "friend_increase"`)
- `is_friend_delete()` - Событие удаления друга (соответствует `detail_type == "friend_decrease"`)

### Методы запросов

#### Информация о запросе
- `get_comment()` - Получить комментарий к запросу

#### Определение типа запроса
- `is_request()` - Является ли событием запроса
- `is_friend_request()` - Является ли запросом на добавление в друзья
- `is_group_request()` - Является ли запросом на вступление в группу

### Функции ответа

#### Основной ответ
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - Общий метод ответа
  - `content`: отправляемое содержимое (текст, URL и т.д.)
  - `method`: метод отправки, по умолчанию "Text", можно "Image"/"Voice"/"Video"/"File" и т.д.
  - `at_sender`: упоминать ли отправителя (автоматически извлекает user_id)
  - `quote`: цитировать ли текущее сообщение (автоматически извлекает message_id)
  - `at_users`: список упомянутых пользователей, например `["user1", "user2"]`
  - `reply_to`: вручную указать ID сообщения для ответа
  - `at_all`: упоминать ли всех участников
  - `**kwargs`: дополнительные параметры (например, для метода Mention user_id)

- `reply_ob12(message)` - Ответ с использованием OneBot12 сегментов сообщения
  - `message`: список или словарь OneBot12 сегментов, можно использовать MessageBuilder для построения

#### Проверка поддержки платформой
- `supports(method)` - Проверить, поддерживает ли платформа метод отправки (например, "Image", "Voice"), возвращает `bool`
- `available_methods()` - Получить список всех доступных методов отправки, возвращает список названий методов

#### Функция пересылки

> **Внимание:** функция пересылки должна реализовываться через DSL отправки адаптера, Event-обертка сама не предоставляет прямого метода пересылки.

```python
# Переслать сообщение в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или указать другой ID группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

> **Развертывание с несколькими аккаунтами:** при отправке в цепочке обработки события **не нужно явно указывать аккаунт** — фреймворк вставляет идентификатор аккаунта, вызвавшего событие, в контекст вызова, `Send` / `Api` / `Request` цепочка при отсутствии явного указания автоматически привязывается к аккаунту, вызвавшему событие (явное `Using()` всегда имеет приоритет; в сценариях без контекста событий, таких как таймеры, используется аккаунт по умолчанию). То есть в примере выше пересылка будет выполнена от аккаунта, получившего это событие, без дополнительного кода.

#### Повторное получение одного и того же события

При одновременном получении одного и того же физического сообщения несколькими аккаунтами, фреймворк обрабатывает это по `ErisPulse.framework.cross_account_policy` (по умолчанию `off` не связывает):

- `mark`: последующие копии по-прежнему дистрибутивируются, но в верхнем уровне события вставляется поле `multi_receipt` (`{"event_id": первый полученный event_id, "self_id": первый полученный аккаунт}`) — модуль читает это поле и самостоятельно решает, пропустить ли ответ
- `drop`: копии отбрасываются на входе дистрибуции, модуль не замечает

### Функция ожидания ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - Ожидать ответ пользователя
  - `prompt`: сообщение-подсказка, если задано, отправляется пользователю
  - `timeout`: время ожидания (секунды), по умолчанию 60 секунд
  - `callback`: функция-обратный вызов, выполняется при получении ответа
  - `validator`: функция-валидатор, проверяет, является ли ответ действительным
  - `method`: метод отправки подсказки, по умолчанию "Text"
  - `pattern`: шаблон glob (`*` / `?` / `[seq]`), текст ответа должен соответствовать, иначе продолжаем ожидать
  - `regex`: регулярное выражение, текст ответа должен соответствовать (один из `pattern` или `regex`), иначе продолжаем ожидать
  - Возвращает объект Event с ответом пользователя, при таймауте возвращает None

#### Интерактивные методы

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Подтверждение диалога
  - Возвращает `True` (подтверждение) / `False` (отрицание) / `None` (таймаут)
  - Встроенные слова подтверждения на китайском и английском языках автоматически распознаются, можно задать собственный набор слов
  - `method`: метод отправки, по умолчанию "Text"; поддерживает "Image"/"Markdown" и другие не-текстовые способы отправки подсказки
  - `hint`: добавлять ли автоматически подсказку с словами подтверждения в конец подсказки (например, "（是/否）" ), по умолчанию False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Выбор меню
  - `options`: список текста вариантов
  - Возвращает индекс выбранного варианта (начиная с 0), при таймауте возвращает `None`
  - `method`: метод отправки, по умолчанию "Text"; текстовые методы (Text/Markdown/md/Html/h5) по умолчанию объединяют варианты в конец
  - `options_format`: формат вариантов (по умолчанию: "auto", автоматически выбирается встроенный стиль в зависимости от method)
    - `"auto"`: Markdown→ненумерованный список (`- 1.вариант`), Html→нумерованный список (`<ol>`), другие→простой текстовый список
    - `"list"`: каждый вариант на отдельной строке, например ``1. вариантA\n2. вариантB``
    - `"inline"`: варианты отображаются в одной строке, например ``1.A | 2.B``
    - `"md"`: Markdown ненумерованный список
    - `"html"`: Html нумерованный список
    - `callable`: пользовательская функция, принимает ``list[str]`` и возвращает ``str``
  - `merge_prompt`: принудительно объединять в одно сообщение, по умолчанию False
    - `False` (по умолчанию): текстовые методы объединяют автоматически; не-текстовые методы сначала отправляют prompt, затем Text варианты
    - `True`: независимо от method объединяются в одно сообщение, отправляется с указанным method
  - `placeholder`: маркер для вставки вариантов, по умолчанию `{options}`; если в prompt встречается этот маркер, он заменяется на текст вариантов, если пустая строка, всегда добавляется в конец

- `collect(fields, timeout_per_field=60.0)` - Сбор формы
  - `fields`: список полей, каждое содержит `key`, `prompt`, необязательный `validator`, необязательный `method`
  - Возвращает словарь `{key: value}`, если любое поле вышло по таймауту, возвращает `None`
  - Каждое поле может содержать `method`, например, для сбора картинки: `{"key": "avatar", "prompt": "Пожалуйста, отправьте аватар", "method": "Image"}`
  - Каждое поле может содержать `options` (список), если задано, поле становится выборочным (автоматически вызывается логика choose)
  - Каждое поле может содержать `options_format`, `merge_prompt`, `placeholder`, контролирующие формат опций, поведение объединения сообщений и маркер замены

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Ожидать любое событие
  - `condition`: функция фильтрации, возвращает `True` при совпадении
  - Возвращает соответствующий Event объект, при таймауте возвращает `None`

- `conversation(timeout=60.0)` - Создать контекст многошагового диалога
  - Возвращает `Conversation` объект, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - Свойство `is_active` указывает, активен ли диалог

#### Примеры интерактивных методов

**confirm() - Подтверждение диалога:**

```python
@command("delete", help="Удалить данные")
async def delete_handler(event: Event):
    if await event.confirm("Вы уверены, что хотите удалить все данные?"):
        sdk.storage.delete("all_data")
        await event.reply("Данные удалены")
    else:
        await event.reply("Отменено")
```

**confirm() - С подсказками:**

```python
# hint=True добавляет в подсказку "（是/否）"
if await event.confirm("Продолжить?", hint=True):
    await event.reply("Продолжено")
# Пользователь видит: Продолжить?（是/否）
```

**choose() - Выбор меню:**

```python
@command("color", help="Выбрать цвет")
async def color_handler(event: Event):
    choice = await event.choose("Выберите цвет:", ["красный", "зеленый", "синий"])
    if choice is not None:
        colors = ["красный", "зеленый", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
```

**choose() - Форматирование и объединение опций:**

```python
# inline формат: опции отображаются в одной строке
choice = await event.choose("Выберите:", ["A", "B", "C"], options_format="inline")
# Вывод: 1.A | 2.B | 3.C

# Пользовательская функция форматирования
choice = await event.choose("Выберите:", ["кот", "собака"],
    options_format=lambda opts: " / ".join(opts))
# Вывод: кот / собака

# options_format="auto" (по умолчанию): автоматически выбирается встроенный стиль в зависимости от method
# Markdown → ненумерованный список
choice = await event.choose(
    "## Выберите", ["кот", "собака"],
    method="Markdown",  # auto автоматически определяет как md список
)
# Вывод:
# ## Выберите
# - 1. кот
# - 2. собака

# Html → нумерованный список
choice = await event.choose(
    "<h2>Выберите</h2>", ["кот", "собака"],
    method="Html", merge_prompt=True,  # auto автоматически определяет как html список
)
# Вывод:
# <h2>Выберите</h2>
# <ol><li>1. кот</li><li>2. собака</li></ol>

# Режим объединения + маркер
choice = await event.choose(
    "## Выберите\n{options}\nОтветьте номером",
    ["кот", "собака"],
    method="Markdown", merge_prompt=True,
)

# Пользовательский маркер
choice = await event.choose(
    "Выберите: [choices]",
    ["кот", "собака"],
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
        await event.reply(f"Успешно зарегистрировано! {data['name']}, {data['age']} лет")
```

**reply() с не-Text методами:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Посмотрите на эту картинку:").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Полное использование многошагового диалога с Conversation см. в [Многошаговый диалог Conversation](../../advanced/conversation.md).

### Информация о команде

#### Основа команды
- `get_command_name()` - Получить имя команды
- `get_command_args()` - Получить список аргументов команды
- `get_command_raw()` - Получить исходный текст команды
- `get_command_info()` - Получить полную информацию о команде в виде словаря
- `is_command()` - Является ли событием команды

### Исходные данные

- `get_raw()` - Получить исходные данные события платформы
- `get_raw_type()` - Получить тип исходного события платформы

### Платформенные расширенные методы

Адаптер может зарегистрировать платформенно-специфичные методы для Event-обертки. Методы доступны только на экземплярах Event соответствующей платформы, на других платформах вызов приведет к `AttributeError`.

Методы через `Event.__getattribute__` имеют приоритет над встроенными методами, поэтому можно переопределить `confirm`, `choose`, `collect`, `wait_reply` и другие встроенные методы интерактивности, предоставляя платформенно-специфичную реализацию (например, кнопки, карточки). Встроенная реализация экспортируется как `_builtin_*` функции для переопределения.

```python
# Почтовое событие - только методы email
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

### Проверка зарегистрированных методов

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

### Расширение для всех платформ (шаблон)

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве названия платформы, регистрируя методы, доступные на **всех платформах**. Подходит для функций, таких как ИИ-диалог, управление контекстом, требующих повторного использования на разных платформах.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self - экземпляр Event, доступен к событию и встроенным методам
    await self.reply(f"ИИ: {prompt}")
```

После регистрации, любой обработчик события на любой платформе может вызывать `event.ai_chat(...)`.

Приоритет разрешения методов (от высшего к низшему): платформенно-специфичный метод → шаблонный метод → встроенный метод → доступ по ключу словаря.

> Способ регистрации расширенных методов адаптерами см. в [API системы событий - Расширение для всех платформ (шаблон)](../../api-reference/event-system.md#расширение-для-всех-платформ-шаблон).

## Связанные документы

### Продолжение пути разработки модулей

- [Начало разработки модулей](getting-started.md) - Создание первого модуля
- [Лучшие практики разработки модулей](best-practices.md) - Разработка качественных модулей

### Глубокое изучение интерактивных возможностей

- [Многошаговый диалог Conversation](../../advanced/conversation.md) - Полная система диалога на основе `wait_reply` (сбор, проверка, переход по ветвям)