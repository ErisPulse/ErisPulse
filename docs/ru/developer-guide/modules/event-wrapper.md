# Подробное объяснение обёртки события

> [!NOTE]
> **Обязательное для понимания уровня L1** — одна из пяти основных статей в "пути чтения" на главной странице, необходима для разработки модулей.

Параметр `event` в обработчике событий может напрямую использовать `.get_text()` / `.reply()` / `.wait_reply()`, благодаря обёртке события. В этой статье представлен полный список методов — обращайтесь к ней при написании обработчиков событий, все сигнатуры методов и поведение должны соответствовать этой статье.

## Добавление аннотаций типа для параметра event

Параметр `event` в обработчике событий является **обёрткой события** (подклассом dict). Рекомендуется добавлять аннотации типа:

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE автоматически подсказывает все удобные методы
    await event.reply(text)   # Ошибки в написании методов обнаруживаются при статической проверке
```

Без аннотаций IDE не распознаёт методы в Event (`get_text()` / `reply()` / `wait_reply()` / расширения платформы не подсказываются), и приходится полагаться на память.

> **Обратите внимание**: в обработчике событий `event` является **обёрткой события** (аннотация `Event`); в методах жизненного цикла модуля `on_load` / `on_unload` `event` является обычным **dict** (аннотация `dict`), не путайте их.

## Основные особенности

- **Полная совместимость с dict**: Event наследуется от dict
- **Удобные методы**: предоставляет множество удобных методов
- **Доступ через точку**: поддерживает доступ к полям события через точку
- **Обратная совместимость**: все методы являются необязательными

## Основные методы полей события

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
    await event.reply("Введите ваше имя:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")

@command("price")
async def price_command(event: Event):
    await event.reply("Введите сумму (например: 5 юаней):")
    # Ответ должен соответствовать регулярному выражению, иначе ожидание продолжается до истечения таймаута
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"Получена сумма: {reply.get_text()}")
```

## Расширенные возможности интерактивных сессий

> [!NOTE]
> Эта функция доступна в ErisPulse **2.8.0+**.

```python
# Напоминание сессии: если в течение 5 минут нет ответа, отправить напоминание, после ответа пользователя автоматически отменить
reminder = event.remind(300, "Ещё здесь? Если не хочешь продолжать, напиши «выход»")
reminder.cancel()  # Также можно отменить вручную

# Повышение при таймауте: по истечении времени обязательно сработает (не отменяется ответом), например, если обработка длительная, уведомить владельца
event.escalate(1800, lambda e: notify_master("Заявка просрочена"))

# Ожидание нескольких путей: одновременно ждать "согласия" и "отказа", сработает первый пришедший
which, reply = await event.select(
    event.expect(pattern="согласен*", user="10001"),
    event.expect(pattern="отказ*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("Таймаут, ответ не получен")

# Ожидание в сессии: ответ любого пользователя в группе может быть принят (сотрудничество в группе)
reply = await event.wait_reply(session=True, prompt="Кто-нибудь может помочь ответить?")

# Почтовый ящик сессии: последние 20 сообщений текущей сессии (включая бота, контекст для ИИ / база для предотвращения повторов)
messages = await event.history(20)

# Транзакции сообщений: при возникновении ошибки автоматически отменяются отправленные сообщения в рамках транзакции
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
    await event.reply(f"Команда: {cmd_name}, параметры: {cmd_args}")
```

## Методы событий уведомлений

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("Добро пожаловать в друзья!")
```

## Справочник методов

### Основные методы

#### Основная информация о событии
- `get_id()` - получить идентификатор события
- `get_time()` - получить временную метку события (Unix, секунды)
- `get_type()` - получить тип события (message/notice/request/meta)
- `get_detail_type()` - получить подробный тип события (private/group/friend и т.д.)
- `get_platform()` - получить название платформы

#### Информация о боте
- `get_self_platform()` - получить название платформы бота
- `get_self_user_id()` - получить идентификатор пользователя бота
- `get_self_account_id()` - получить идентификатор аккаунта бота (режим множественных ботов)
- `get_self_info()` - получить полную информацию о боте в виде словаря

#### Идентификаторы сессии
- `get_target_id()` - получить единый идентификатор цели (для групповых чатов возвращает `group_id`, для каналов `channel_id`, для личных сообщений `user_id`, в порядке group → channel → guild → thread → user возвращает первый непустой)
- `get_session_id()` - получить уникальный идентификатор сессии, формат `{platform}:{detail_type}:{target_id}`

### Методы событий сообщений

#### Содержимое сообщения
- `get_message()` - получить массив сегментов сообщения (формат OneBot12)
- `get_alt_message()` - получить альтернативный текст сообщения
- `get_text()` - получить текстовое содержимое (псевдоним `get_alt_message()`)
- `get_message_text()` - получить текстовое содержимое (псевдоним `get_alt_message()`)

#### Информация об отправителе
- `get_user_id()` - получить идентификатор пользователя-отправителя
- `get_user_nickname()` - получить никнейм отправителя
- `get_sender()` - получить полную информацию об отправителе в виде словаря

#### Информация о группе/канале
- `get_group_id()` - получить идентификатор группы (для сообщений в группе)
- `get_channel_id()` - получить идентификатор канала (для сообщений в канале)
- `get_guild_id()` - получить идентификатор сервера (для сообщений на сервере)
- `get_thread_id()` - получить идентификатор темы/подканала (для сообщений в теме)

#### Связанные с @ сообщениями
- `has_mention()` - содержит ли сообщение упоминание бота
- `get_mentions()` - получить список всех упомянутых идентификаторов пользователей

### Определение типа сообщения

#### Основные проверки
- `is_message()` - является ли событие сообщением
- `is_private_message()` - является ли сообщение личным
- `is_group_message()` - является ли сообщение групповым
- `is_at_message()` - является ли сообщение с упоминанием бота (`has_mention()` alias)

### Методы событий уведомлений

#### Информация об операторе
- `get_operator_id()` - получить идентификатор оператора
- `get_operator_nickname()` - получить никнейм оператора

#### Определение типа уведомления
- `is_notice()` - является ли событие уведомлением
- `is_group_member_increase()` - событие увеличения участников группы
- `is_group_member_decrease()` - событие уменьшения участников группы
- `is_friend_add()` - событие добавления друга (соответствует `detail_type == "friend_increase"`)
- `is_friend_delete()` - событие удаления друга (соответствует `detail_type == "friend_decrease"`)

### Методы событий запросов

#### Информация о запросе
- `get_comment()` - получить комментарий к запросу

#### Определение типа запроса
- `is_request()` - является ли событие запросом
- `is_friend_request()` - является ли запросом добавления друга
- `is_group_request()` - является ли запросом добавления в группу

### Функция ответа

#### Основной ответ
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - универсальный метод ответа
  - `content`: содержимое отправки (текст, URL и т.д.)
  - `method`: метод отправки, по умолчанию "Text", можно выбрать "Image"/"Voice"/"Video"/"File" и т.д.
  - `at_sender`: упоминать ли отправителя (автоматически извлекает user_id)
  - `quote`: цитировать ли текущее сообщение (автоматически извлекает message_id)
  - `at_users`: список упоминаний пользователей, например `["user1", "user2"]`
  - `reply_to`: вручную указать идентификатор сообщения для ответа
  - `at_all`: упоминать ли всех участников
  - `**kwargs`: дополнительные параметры (например, для метода Mention user_id)

- `reply_ob12(message)` - ответ с использованием OneBot12 сегментов сообщения
  - `message`: список или словарь сегментов OneBot12, можно использовать MessageBuilder для построения

#### Проверка поддержки платформой
- `supports(method)` - проверить, поддерживает ли текущая платформа метод отправки (например, `"Image"`, `"Voice"`), возвращает `bool`
- `available_methods()` - перечислить все доступные методы отправки на текущей платформе, возвращает список названий методов

#### Функция пересылки

> **Внимание**: функция пересылки должна реализовываться через DSL отправки адаптера, Event wrapper сам не предоставляет прямого метода пересылки.

```python
# Переслать сообщение в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или указать другой идентификатор группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### Функция ожидания ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - ожидать ответ пользователя
  - `prompt`: сообщение-подсказка, если указано, отправляется пользователю
  - `timeout`: время ожидания (секунды), по умолчанию 60 секунд
  - `callback`: функция-обратный вызов, выполняется при получении ответа
  - `validator`: функция проверки, используется для проверки корректности ответа
  - `method`: метод отправки подсказки, по умолчанию "Text"
  - `pattern`: шаблон glob (`*` / `?` / `[seq]`), текст ответа должен соответствовать, иначе ожидание продолжается
  - `regex`: регулярное выражение, текст ответа должен соответствовать (один из `pattern` или `regex`), иначе ожидание продолжается
  - Возвращает объект Event с ответом пользователя, в случае таймаута возвращает None

#### Интерактивные методы

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - метод подтверждения
  - Возвращает `True` (подтверждение) / `False` (отрицание) / `None` (таймаут)
  - Встроенные слова подтверждения на английском и китайском автоматически распознаются, можно настроить собственный набор слов
  - `method`: метод отправки, по умолчанию "Text"; поддерживает "Image"/"Markdown" и другие не-текстовые методы
  - `hint`: добавлять ли автоматически подсказку в конце (например, "（да/нет）" в конце), по умолчанию False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - метод выбора меню
  - `options`: список текстов опций
  - Возвращает индекс выбранной опции (начиная с 0), в случае таймаута возвращает `None`
  - `method`: метод отправки, по умолчанию "Text"; текстовые методы (Text/Markdown/md/Html/h5) по умолчанию объединяют опции в конец
  - `options_format`: формат опций (по умолчанию: "auto", автоматически выбирается встроенный стиль в зависимости от метода)
    - `"auto"`: Markdown→нумерованный список (`- 1. опция`), Html→упорядоченный список (`<ol>`), остальные→простой список
    - `"list"`: по одному на строку, например ``1. опцияA\n2. опцияB``
    - `"inline"`: отображение в одной строке, например ``1.A | 2.B``
    - `"md"`: Markdown нумерованный список
    - `"html"`: Html упорядоченный список
    - `callable`: пользовательская функция, принимает ``list[str]`` и возвращает ``str``
  - `merge_prompt`: принудительно объединять ли в одно сообщение, по умолчанию False
    - `False` (по умолчанию): текстовые методы объединяют автоматически; не-текстовые методы сначала отправляют prompt, затем Text с опциями
    - `True`: независимо от метода объединяются в одно сообщение, отправляется с указанным методом
  - `placeholder`: маркер для вставки опций, по умолчанию `{options}`; текст с этим маркером заменяется на список опций, если пустая строка, то всегда добавляется в конец

- `collect(fields, timeout_per_field=60.0)` - сбор формы
  - `fields`: список полей, каждое содержит `key`, `prompt`, необязательный `validator`, необязательный `method`
  - Возвращает словарь `{key: value}`, если любое поле вышло за таймаут, возвращает `None`
  - Каждое поле может иметь ключ `method` для указания метода отправки, например, при сборе изображения: `{"key": "avatar", "prompt": "Пожалуйста, отправьте аватар", "method": "Image"}`
  - Каждое поле может иметь ключ `options` (список), при наличии становится выбором (автоматически вызывается логика choose)
  - Каждое поле может иметь ключи `options_format`, `merge_prompt`, `placeholder`, управляющие форматом опций, поведением объединения сообщений и маркером

- `wait_for(event_type="message", condition=None, timeout=60.0)` - ожидать произвольного события
  - `condition`: фильтрующая функция, возвращает `True` при совпадении
  - Возвращает соответствующий Event объект, в случае таймаута возвращает None

- `conversation(timeout=60.0)` - создать контекст многошагового диалога
  - Возвращает объект `Conversation`, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - Атрибут `is_active` указывает, активен ли диалог

#### Примеры интерактивных методов

**confirm() - подтверждение диалога:**

```python
@command("delete", help="Удалить данные")
async def delete_handler(event: Event):
    if await event.confirm("Вы уверены, что хотите удалить все данные?"):
        sdk.storage.delete("all_data")
        await event.reply("Данные удалены")
    else:
        await event.reply("Отменено")
```

**confirm() - с подсказкой:**

```python
# hint=True добавит "（да/нет）" в конец подсказки
if await event.confirm("Продолжить?", hint=True):
    await event.reply("Продолжено")
# Пользователь увидит: Продолжить?（да/нет）
```

**choose() - выбор меню:**

```python
@command("color", help="Выбрать цвет")
async def color_handler(event: Event):
    choice = await event.choose("Выберите цвет:", ["красный", "зелёный", "синий"])
    if choice is not None:
        colors = ["красный", "зелёный", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
```

**choose() - форматирование и объединение опций:**

```python
# inline формат: опции отображаются в одной строке
choice = await event.choose("Выберите:", ["A", "B", "C"], options_format="inline")
# Вывод: 1.A | 2.B | 3.C

# Пользовательская функция форматирования
choice = await event.choose("Выберите:", ["кот", "собака"],
    options_format=lambda opts: " / ".join(opts))
# Вывод: кот / собака

# options_format="auto" (по умолчанию): в зависимости от method автоматически выбирается встроенный стиль
# Markdown → нумерованный список
choice = await event.choose(
    "## Выберите", ["кот", "собака"],
    method="Markdown",  # auto автоматически распознаёт как md-список
)
# Вывод:
# ## Выберите
# - 1. кот
# - 2. собака

# Html → упорядоченный список
choice = await event.choose(
    "<h2>Выберите</h2>", ["кот", "собака"],
    method="Html", merge_prompt=True,  # auto автоматически распознаёт как html-список
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

**collect() - сбор формы:**

```python
@command("register", help="Регистрация")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "Введите имя:"},
        {"key": "age", "prompt": "Введите возраст:",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"Регистрация прошла успешно! {data['name']}, {data['age']} лет")
```

**reply с методами, отличными от Text:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Посмотрите на эту картинку:").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Полное использование многошагового диалога через Conversation см. в [Многошаговый диалог Conversation](../../advanced/conversation.md).

### Информация о команде

#### Основные команды
- `get_command_name()` - получить название команды
- `get_command_args()` - получить список аргументов команды
- `get_command_raw()` - получить исходный текст команды
- `get_command_info()` - получить полную информацию о команде в виде словаря
- `is_command()` - является ли событие командой

### Исходные данные

- `get_raw()` - получить исходные данные события платформы
- `get_raw_type()` - получить тип исходного события платформы

### Методы расширения платформы

Адаптеры могут регистрировать специфичные для платформы методы для обёртки события. Методы доступны только на экземплярах Event соответствующей платформы, попытка доступа с других платформ вызывает `AttributeError`.

Методы платформы имеют приоритет над встроенными методами через `Event.__getattribute__`, поэтому можно переопределить встроенные методы `confirm`、`choose`、`collect`、`wait_reply` и др., предоставив реализацию с функционалом платформы (например, кнопки, карточки). Встроенная реализация экспортируется как `_builtin_*` функции для переопределения.

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
event.get_text()         # ✅ В любой платформе
event.reply("hi")        # ✅ В любой платформе
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

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве названия платформы, методы будут доступны на **всех** платформах. Подходит для функций, требующих переносимости, таких как ИИ-диалоги, управление контекстом и т.д.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self — экземпляр Event, можно получить доступ к данным события и встроенным методам
    await self.reply(f"ИИ: {prompt}")
```

После регистрации, метод `event.ai_chat(...)` будет доступен в обработчиках событий любой платформы.

Приоритет разрешения методов (от высшего к низшему): методы платформы → методы шаблона → встроенные методы → доступ по ключу словаря.

> Способ регистрации расширений адаптерами см. в [API системы событий - Расширение для всех платформ (шаблон)](../../api-reference/event-system.md#расширение-для-всех-платформ-шаблон).

## Связанные документы

### Продолжение пути разработки модуля

- [Начало разработки модуля](getting-started.md) - Создание первого модуля
- [Лучшие практики разработки модуля](best-practices.md) - Разработка модуля высокого качества

### Глубокое изучение интерактивных возможностей

- [Многошаговый диалог Conversation](../../advanced/conversation.md) - Полная система сессий на основе `wait_reply` (сбор, проверка, ветвление)
- [Руководство по отладке модуля](../module-troubleshooting.md) - Поиск и устранение проблем, когда событие не отвечает