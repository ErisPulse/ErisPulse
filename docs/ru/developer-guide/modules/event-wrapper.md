# Детальное объяснение класса-обертки Event

> [!NOTE]
> **Обязательно к прочтению на уровне L1** — один из пяти ключевых документов в "пути чтения" на главной странице, необходим для разработки модулей.

Модуль Event предоставляет мощный класс-обертку для обработки событий, упрощая процесс работы с ними.

## Добавление аннотаций типов для параметра event

Параметр `event` в обработчике событий представляет собой **класс-обертку Event** (подкласс dict). Рекомендуется добавлять аннотации типов:

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE автоматически подсказывает все удобные методы
    await event.reply(text)   # Опечатки будут обнаружены при статической проверке
```

Без аннотаций IDE не сможет распознать методы Event (`get_text()` / `reply()` / `wait_reply()` / расширения для платформы), и придется полагаться на запоминание.

> **Обратите внимание**: `event` в обработчике событий — это **класс-обертка Event** (аннотация `Event`); `event` в методах жизненного цикла модуля `on_load` / `on_unload` — обычный **dict** (аннотация `dict`), не путайте их.

## Основные характеристики

- **Полная совместимость с dict**: Event наследуется от dict
- **Удобные методы**: Предоставляет множество удобных методов
- **Доступ через точку**: Поддерживает доступ к полям событий через точку
- **Обратная совместимость**: Все методы являются необязательными

## Основные методы для полей

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, платформа: {platform}, время: {time}")
```

## Методы для событий сообщений

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
    await event.reply(f"Тип: {'личное сообщение' if is_private else 'групповое сообщение'}")
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
    # Ответ должен соответствовать регулярному выражению, иначе ожидание продолжается до тайм-аута
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*юаней")
    if reply:
        await event.reply(f"Получена сумма: {reply.get_text()}")
```

## Расширенные возможности интерактивных диалогов

> [!NOTE]
> Эти возможности требуют ErisPulse **2.8.0+**.

```python
# Напоминание с таймером: если в течение 5 минут нет ответа, отправить напоминание, пользовательский ответ автоматически отменяет
reminder = event.remind(300, "Ещё здесь? Если не хочешь продолжать, ответь «выход»")
reminder.cancel()  # Также можно отменить вручную

# Обновление тайм-аута: обязательное достижение срока (не отменяется ответом), например, уведомление администратора при длительном необработанном запросе
event.escalate(1800, lambda e: notify_master("Задержка в обработке"))

# Ожидание нескольких путей: одновременно ждем "одобрения" и "отказа", срабатывает первый поступивший
which, reply = await event.select(
    event.expect(pattern="одобрение*", user="10001"),
    event.expect(pattern="отказ*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("Тайм-аут, не получено подтверждение")

# Ожидание в рамках сессии: ответ любого участника в группе может быть принят (для группового сотрудничества)
reply = await event.wait_reply(session=True, prompt="Кто-нибудь может помочь ответить?")

# Ящик сообщений сессии: последние 20 сообщений текущей сессии (включая сообщения бота, контекст для ИИ / база для предотвращения повторения)
messages = await event.history(20)

# Транзакции сообщений: при возникновении исключений автоматически отменяются отправленные в транзакции сообщения
async with event.message_tx():
    await event.reply("Обработка, пожалуйста, подождите...")
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

## Методы для событий уведомлений

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("Добро пожаловать, добавьте меня в друзья!")
```

## Справочник методов

### Основные методы

#### Основная информация о событии
- `get_id()` - Получить идентификатор события
- `get_time()` - Получить метку времени события (Unix в секундах)
- `get_type()` - Получить тип события (message/notice/request/meta)
- `get_detail_type()` - Получить подробный тип события (private/group/friend и т.д.)
- `get_platform()` - Получить название платформы

#### Информация о боте
- `get_self_platform()` - Получить название платформы бота
- `get_self_user_id()` - Получить идентификатор пользователя бота
- `get_self_account_id()` - Получить идентификатор аккаунта бота (режим с несколькими ботами)
- `get_self_info()` - Получить полную информацию о боте в виде словаря

#### Идентификаторы сессии
- `get_target_id()` - Получить единый идентификатор цели (для групповых чатов возвращает `group_id`, для каналов `channel_id`, для личных сообщений `user_id`, в порядке group → channel → guild → thread → user возвращает первое непустое значение)
- `get_session_id()` - Получить уникальный идентификатор сессии, формат `{platform}:{detail_type}:{target_id}`

### Методы для событий сообщений

#### Содержимое сообщения
- `get_message()` - Получить массив сегментов сообщения (формат OneBot12)
- `get_alt_message()` - Получить резервный текст сообщения
- `get_text()` - Получить чистый текст (псевдоним `get_alt_message()`)
- `get_message_text()` - Получить чистый текст (псевдоним `get_alt_message()`)

#### Информация об отправителе
- `get_user_id()` - Получить идентификатор пользователя-отправителя
- `get_user_nickname()` - Получить никнейм отправителя
- `get_sender()` - Получить полную информацию об отправителе в виде словаря

#### Информация о группе/канале
- `get_group_id()` - Получить идентификатор группы (сообщения в группе)
- `get_channel_id()` - Получить идентификатор канала (сообщения в канале)
- `get_guild_id()` - Получить идентификатор сервера (сообщения на сервере)
- `get_thread_id()` - Получить идентификатор темы/подканала (сообщения в теме)

#### Связанные с @ сообщениями
- `has_mention()` - Содержит ли сообщение упоминание бота
- `get_mentions()` - Получить список всех упомянутых пользователей

### Методы для определения типа сообщения

#### Основные проверки
- `is_message()` - Является ли событие сообщением
- `is_private_message()` - Является ли сообщение личным
- `is_group_message()` - Является ли сообщение групповым
- `is_at_message()` - Является ли сообщение упоминанием (псевдоним `has_mention()`)

### Методы для событий уведомлений

#### Информация об операторе
- `get_operator_id()` - Получить идентификатор оператора
- `get_operator_nickname()` - Получить никнейм оператора

#### Проверка типа уведомления
- `is_notice()` - Является ли событие уведомлением
- `is_group_member_increase()` - Событие увеличения участников группы
- `is_group_member_decrease()` - Событие уменьшения участников группы
- `is_friend_add()` - Событие добавления в друзья (соответствует `detail_type == "friend_increase"`)
- `is_friend_delete()` - Событие удаления из друзей (соответствует `detail_type == "friend_decrease"`)

### Методы для событий запросов

#### Информация о запросе
- `get_comment()` - Получить комментарий к запросу

#### Проверка типа запроса
- `is_request()` - Является ли событие запросом
- `is_friend_request()` - Является ли запросом добавления в друзья
- `is_group_request()` - Является ли запросом добавления в группу

### Функция ответа

#### Основной ответ
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - Общая функция ответа
  - `content`: Отправляемое содержимое (текст, URL и т.д.)
  - `method`: Метод отправки, по умолчанию "Text", возможны "Image"/"Voice"/"Video"/"File" и т.д.
  - `at_sender`: @ отправителя (автоматически извлекает user_id)
  - `quote`: Ссылка на ответ на текущее сообщение (автоматически извлекает message_id)
  - `at_users`: Список пользователей для упоминания, например `["user1", "user2"]`
  - `reply_to`: Ручное указание идентификатора сообщения для ответа
  - `at_all`: @ всех участников
  - `**kwargs`: Дополнительные параметры (например, user_id для метода Mention)

- `reply_ob12(message)` - Ответ с использованием OneBot12 сегментов сообщения
  - `message`: Список или словарь сегментов OneBot12, можно использовать MessageBuilder для построения

#### Проверка поддержки платформой
- `supports(method)` - Проверка поддержки метода отправки платформой (например, `"Image"`, `"Voice"`), возвращает `bool`
- `available_methods()` - Список всех доступных методов отправки на текущей платформе, возвращает список названий методов

#### Функция пересылки

> **Важно**: Функция пересылки реализуется через DSL отправки адаптера, Event-обертка сама не предоставляет прямой метод пересылки.

```python
# Пересылка сообщения в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или указать другой идентификатор группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### Функция ожидания ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - Ожидание ответа пользователя
  - `prompt`: Текст подсказки, если указан, отправляется пользователю
  - `timeout`: Время ожидания (секунды), по умолчанию 60 секунд
  - `callback`: Функция обратного вызова, выполняется при получении ответа
  - `validator`: Функция проверки, используется для проверки корректности ответа
  - `method`: Метод отправки подсказки, по умолчанию "Text"
  - `pattern`: Шаблон glob (`*` / `?` / `[seq]`), текст ответа должен соответствовать, иначе ожидание продолжается
  - `regex`: Регулярное выражение, текст ответа должен соответствовать (только один из `pattern` и `regex`), иначе ожидание продолжается
  - Возвращает объект Event с ответом пользователя, при тайм-ауте возвращает None

#### Интерактивные методы

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Подтверждение диалога
  - Возвращает `True` (подтверждение) / `False` (отрицание) / `None` (тайм-аут)
  - Внутренние слова подтверждения на китайском и английском языках распознаются автоматически, можно задать собственные наборы слов
  - `method`: Метод отправки, по умолчанию "Text"; поддерживает "Image"/"Markdown" и другие не-текстовые методы отправки подсказки
  - `hint`: Добавлять ли в конец подсказки автоматически подсказку с вариантами подтверждения (например, "（да/нет）"），по умолчанию False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Меню выбора
  - `options`: Список текстов вариантов
  - Возвращает индекс выбранного варианта (от 0), при тайм-ауте возвращает `None`
  - `method`: Метод отправки, по умолчанию "Text"; текстовые методы (Text/Markdown/md/Html/h5) по умолчанию объединяют варианты в конец
  - `options_format`: Формат вариантов (по умолчанию: "auto", автоматически выбирается в зависимости от method)
    - `"auto"`: Markdown→нумерованный список (`- 1. вариант`), Html→упорядоченный список (`<ol>`), другие→простой текстовый список
    - `"list"`: Каждый вариант на отдельной строке, например ``1. вариантA\n2. вариантB``
    - `"inline"`: Варианты отображаются в одной строке, например ``1.A | 2.B``
    - `"md"`: Markdown нумерованный список
    - `"html"`: Html упорядоченный список
    - `callable`: Пользовательская функция, принимает ``list[str]`` и возвращает ``str``
  - `merge_prompt`: Принудительно объединять в одно сообщение, по умолчанию False
    - `False` (по умолчанию): Текстовые методы объединяют автоматически; не-текстовые методы сначала отправляют prompt, затем Text-варианты
    - `True`: Независимо от method объединяются в одно сообщение, отправляется с указанным method
  - `placeholder`: Заполнитель для вставки вариантов, по умолчанию `{options}`; текст в prompt с этим маркером заменяется на варианты, если пустая строка, варианты всегда добавляются в конец

- `collect(fields, timeout_per_field=60.0)` - Сбор формы
  - `fields`: Список полей, каждое содержит `key`, `prompt`, необязательный `validator`, необязательный `method`
  - Возвращает словарь `{key: value}`, если любое поле вышло по тайм-ауту возвращает `None`
  - Каждое поле может иметь ключ `method` для указания метода отправки, например при сборе изображения: `{"key": "avatar", "prompt": "Пожалуйста, отправьте аватарку", "method": "Image"}`
  - Каждое поле может иметь ключ `options` (список), при этом поле становится выборочным (автоматически вызывается логика choose)
  - Каждое поле может иметь ключи `options_format`, `merge_prompt`, `placeholder`, управляющие форматом вариантов, поведением объединения сообщений и заполнителем

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Ожидание любого события
  - `condition`: Фильтрующая функция, возвращает `True` при совпадении
  - Возвращает соответствующий Event, при тайм-ауте возвращает `None`

- `conversation(timeout=60.0)` - Создание контекста многократного диалога
  - Возвращает объект `Conversation`, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
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

**confirm() - С подсказкой:**

```python
# hint=True добавляет в конец подсказки "（да/нет）"
if await event.confirm("Продолжить?", hint=True):
    await event.reply("Продолжено")
# Пользователь видит: Продолжить?（да/нет）
```

**choose() - Меню выбора:**

```python
@command("color", help="Выбрать цвет")
async def color_handler(event: Event):
    choice = await event.choose("Выберите цвет:", ["красный", "зелёный", "синий"])
    if choice is not None:
        colors = ["красный", "зелёный", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
```

**choose() - Форматирование и объединение опций:**

```python
# inline формат: опции отображаются в одной строке
choice = await event.choose("Выберите:", ["A", "B", "C"], options_format="inline")
# Вывод: 1.A | 2.B | 3.C

# Пользовательская функция форматирования
choice = await event.choose("Выберите:", ["кошка", "собака"],
    options_format=lambda opts: " / ".join(opts))
# Вывод: кошка / собака

# options_format="auto" (по умолчанию): автоматически выбирается в зависимости от method
# Markdown → нумерованный список
choice = await event.choose(
    "## Выберите", ["кошка", "собака"],
    method="Markdown",  # auto автоматически распознаёт как md-список
)
# Вывод:
# ## Выберите
# - 1. кошка
# - 2. собака

# Html → упорядоченный список
choice = await event.choose(
    "<h2>Выберите</h2>", ["кошка", "собака"],
    method="Html", merge_prompt=True,  # auto автоматически распознаёт как html-список
)
# Вывод:
# <h2>Выберите</h2>
# <ol><li>1. кошка</li><li>2. собака</li></ol>

# Объединённый режим с заполнителем
choice = await event.choose(
    "## Выберите\n{options}\nОтветьте номером",
    ["кошка", "собака"],
    method="Markdown", merge_prompt=True,
)

# Пользовательский заполнитель
choice = await event.choose(
    "Выберите: [choices]",
    ["кошка", "собака"],
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
        await event.reply(f"Успешно зарегистрированы! {data['name']}, {data['age']} лет")
```

**reply с не-Text методами:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Посмотрите на эту картинку:").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Полное использование многократных диалогов с Conversation см. в [Многократные диалоги с Conversation](../../advanced/conversation.md).

### Информация о команде

#### Основные команды
- `get_command_name()` - Получить имя команды
- `get_command_args()` - Получить список аргументов команды
- `get_command_raw()` - Получить исходный текст команды
- `get_command_info()` - Получить полную информацию о команде в виде словаря
- `is_command()` - Является ли событием команды

### Исходные данные

- `get_raw()` - Получить исходные данные события платформы
- `get_raw_type()` - Получить тип исходного события платформы

### Платформенные расширения

Адаптеры могут зарегистрировать платформенно-специфические методы для класса-обертки Event. Методы доступны только на экземплярах Event соответствующей платформы, на других платформах вызов приведёт к `AttributeError`.

Методы, зарегистрированные через `Event.__getattribute__`, имеют приоритет над встроенными методами, поэтому можно переопределить встроенные методы взаимодействия, такие как `confirm`, `choose`, `collect`, `wait_reply`, предоставляя специфичные реализации для платформы (например, кнопки, карточки). Встроенные реализации доступны как `_builtin_*` функции для переопределения.

```python
# Почтовое событие — только методы email
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ Возвращает "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram событие — только методы Telegram
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ Возвращает "private"
event.get_subject()      # ❌ AttributeError

# Встроенные методы доступны всегда
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
hasattr(event, "get_subject")   # Возвращает True только при platform="email"
"get_subject" in dir(event)     # То же самое
```

### Расширение для всех платформ (шаблон)

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве названия платформы, регистрируя методы, доступные на **всех** экземплярах Event. Подходит для функций, таких как ИИ-диалоги, управление контекстом и т.д., требующих переносимости между платформами.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self — экземпляр Event, доступен к событию и встроенным методам
    await self.reply(f"AI: {prompt}")
```

После регистрации любой обработчик события на любой платформе сможет вызывать `event.ai_chat(...)`.

Приоритет методов (от высшего к низшему): платформенно-специфичные методы → методы с шаблоном → встроенные методы → доступ через ключ словаря.

> Способ регистрации расширений адаптерами см. в [API системы событий - Расширение для всех платформ (шаблон)](../../api-reference/event-system.md#расширение-для-всех-платформ-шаблон).

## Связанные документы

- [Введение в разработку модулей](getting-started.md) - Создание первого модуля
- [Лучшие практики](best-practices.md) - Разработка качественных модулей