# Подробное руководство по классу-обёртке Event

> [!NOTE]
> **Обязательно к прочтению, ядро L1** — один из пяти ключевых документов в «пути чтения» на главной странице, необходим для разработки модулей.

Параметр `event` в обработчике может напрямую вызывать `.get_text()` / `.reply()` / `.wait_reply()` именно благодаря классу-обёртке Event. В этой статье приведён полный список его методов — обращайтесь к ней по мере необходимости при написании обработчиков событий; сигнатуры методов и их поведение определяются именно здесь.

## Добавление аннотации типа к параметру event

Параметр `event` обработчика событий — это **класс-обёртка Event** (подкласс dict). Настоятельно рекомендуется добавить для него аннотацию типа:

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE автоматически дополнит все удобные методы
    await event.reply(text)   # Опечатки будут обнаружены уже при статической проверке
```

Без аннотации IDE не сможет распознать методы Event (подсказки для `get_text()` / `reply()` / `wait_reply()` / методов расширений платформы не появятся), и их придётся писать по памяти.

> **Обратите внимание на различие**: `event` в колбэке обработчика событий — это **класс-обёртка Event** (аннотируется как `Event`); а `event` в методах жизненного цикла модуля `on_load` / `on_unload` — это обычный **dict** (аннотируется как `dict`). Не путайте их.

## Ключевые особенности

- **Полная совместимость со словарём**: Event наследуется от dict
- **Удобные методы**: предоставляет множество удобных методов
- **Доступ через точку**: поддерживает доступ к полям события через точку
- **Обратная совместимость**: все методы являются необязательными

## Методы основных полей

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
    await event.reply(f"Тип: {'личный чат' if is_private else 'групповой чат'}")
```

## Функции ответа

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event: Event):
    await event.reply("Введите своё имя:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")

@command("price")
async def price_command(event: Event):
    await event.reply("Введите сумму (например: 5 руб.):")
    # Ответ должен соответствовать регулярному выражению, иначе ожидание продолжится до таймаута
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*руб")
    if reply:
        await event.reply(f"Получена сумма: {reply.get_text()}")
```

## Продвинутые интерактивные сессии

> [!NOTE]
> Возможности этого раздела требуют ErisPulse **2.8.0+**.

```python
# Напоминание по таймеру в сессии: напоминание через 5 минут без ответа, автоматически отменяется после ответа пользователя
reminder = event.remind(300, "Вы ещё здесь? Если не хотите общаться, ответьте «выход»")
reminder.cancel()  # также можно отменить вручную

# Эскалация по таймауту: гарантированное срабатывание по истечении срока (не отменяется ответом), например уведомление владельца при долгой необработке
event.escalate(1800, lambda e: notify_master("Время обработки заявки истекло"))

# Многоканальное ожидание: одновременное ожидание «согласен» и «отказ»; побеждает первый пришедший ответ
which, reply = await event.select(
    event.expect(pattern="согласен*", user="10001"),
    event.expect(pattern="отказ*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("Время ожидания подтверждения истекло")

# Ожидание на уровне сессии: ответ любого участника группы может сработать (групповое взаимодействие)
reply = await event.wait_reply(session=True, prompt="Кто-нибудь может помочь с ответом?")

# Входящие сессии: последние 20 сообщений текущей сессии (включая бота; основа для контекста ИИ / защиты от повторов)
messages = await event.history(20)

# Транзакция сообщений: при исключении автоматически отзываются сообщения, отправленные в рамках транзакции
async with event.message_tx():
    await event.reply("Обработка, пожалуйста, подождите...")
    result = await do_something()
    await event.reply(f"Готово: {result}")
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

## Методы событий уведомлений

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("Спасибо, что добавили меня в друзья!")
```

## Краткий справочник методов

### Основные методы

#### Базовая информация о событии
- `get_id()` - получить ID события
- `get_time()` - получить временную метку события (Unix, секунды)
- `get_type()` - получить тип события (message/notice/request/meta)
- `get_detail_type()` - получить подробный тип события (private/group/friend и т.д.)
- `get_platform()` - получить название платформы

#### Информация о боте
- `get_self_platform()` - получить название платформы бота
- `get_self_user_id()` - получить ID пользователя бота
- `get_self_account_id()` - получить ID аккаунта бота (режим нескольких ботов)
- `get_self_info()` - получить полный словарь информации о боте

#### Идентификатор сессии
- `get_target_id()` - получить унифицированный ID цели (в групповом чате возвращает `group_id`, в канале — `channel_id`, в личном чате — `user_id`; берёт первое непустое значение в порядке group → channel → guild → thread → user)
- `get_session_id()` - получить уникальный идентификатор сессии в формате `{platform}:{detail_type}:{target_id}`

### Методы событий сообщений

#### Содержимое сообщения
- `get_message()` - получить массив сегментов сообщения (формат OneBot12)
- `get_alt_message()` - получить альтернативный текст сообщения
- `get_text()` - получить текстовое содержимое (псевдоним `get_alt_message()`)
- `get_message_text()` - получить текстовое содержимое (псевдоним `get_alt_message()`)

#### Информация об отправителе
- `get_user_id()` - получить ID пользователя-отправителя
- `get_user_nickname()` - получить ник отправителя
- `get_sender()` - получить полный словарь информации об отправителе

#### Информация о группе/канале
- `get_group_id()` - получить ID группы (сообщения группового чата)
- `get_channel_id()` - получить ID канала (сообщения канала)
- `get_guild_id()` - получить ID сервера (сообщения сервера)
- `get_thread_id()` - получить ID темы/подканала (сообщения темы)

#### Связанное с @-сообщениями
- `has_mention()` - содержит ли @-упоминание бота
- `get_mentions()` - получить список ID всех упомянутых пользователей

### Определение типа сообщения

#### Базовые проверки
- `is_message()` - является ли событием сообщения
- `is_private_message()` - является ли сообщением личного чата
- `is_group_message()` - является ли сообщением группового чата
- `is_at_message()` - является ли @-сообщением (псевдоним `has_mention()`)

### Методы событий уведомлений

#### Информация об операторе
- `get_operator_id()` - получить ID оператора
- `get_operator_nickname()` - получить ник оператора

#### Определение типа уведомления
- `is_notice()` - является ли событием уведомления
- `is_group_member_increase()` - событие увеличения числа участников группы
- `is_group_member_decrease()` - событие уменьшения числа участников группы
- `is_friend_add()` - событие добавления в друзья (соответствует `detail_type == "friend_increase"`)
- `is_friend_delete()` - событие удаления из друзей (соответствует `detail_type == "friend_decrease"`)

### Методы событий запросов

#### Информация о запросе
- `get_comment()` - получить сопроводительное сообщение запроса

#### Определение типа запроса
- `is_request()` - является ли событием запроса
- `is_friend_request()` - является ли запросом на добавление в друзья
- `is_group_request()` - является ли запросом к группе

### Функции ответа

#### Базовый ответ
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - универсальный метод ответа
  - `content`: отправляемое содержимое (текст, URL и т.д.)
  - `method`: метод отправки, по умолчанию "Text"; возможны "Image"/"Voice"/"Video"/"File" и т.д.
  - `at_sender`: упоминать ли отправителя (автоматически извлекает user_id)
  - `quote`: цитировать ли текущее сообщение в ответе (автоматически извлекает message_id)
  - `at_users`: список пользователей для @-упоминания, например `["user1", "user2"]`
  - `reply_to`: ручное указание ID сообщения для ответа
  - `at_all`: упоминать ли всех участников
  - `**kwargs`: дополнительные параметры (например, user_id для метода Mention)

- `reply_ob12(message)` - ответ с использованием сегментов сообщений OneBot12
  - `message`: список или словарь сегментов сообщений OneBot12, можно формировать с помощью MessageBuilder

#### Запрос возможностей платформы
- `supports(method)` - проверяет, поддерживает ли текущая платформа определённый метод отправки (например, `"Image"`, `"Voice"`), возвращает `bool`
- `available_methods()` - перечисляет все доступные методы отправки текущей платформы, возвращает список имён методов

#### Функция пересылки

> **Примечание**: функция пересылки должна быть реализована через Send DSL адаптера; сам класс-обёртка Event не предоставляет прямых методов пересылки.

```python
# Пересылка сообщения в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или укажите другой ID группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### Функции ожидания ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - ожидание ответа пользователя
  - `prompt`: подсказка-сообщение; если указана, будет отправлена пользователю
  - `timeout`: время ожидания до таймаута (в секундах), по умолчанию 60 секунд
  - `callback`: функция обратного вызова, выполняется при получении ответа
  - `validator`: функция проверки, используется для проверки валидности ответа
  - `method`: метод отправки подсказки, по умолчанию "Text"
  - `pattern`: glob-подстановочные знаки (`*` / `?` / `[seq]`); текст ответа должен соответствовать, иначе ожидание продолжается
  - `regex`: регулярное выражение; текст ответа должен ему соответствовать (используется либо `pattern`, либо `regex`), иначе ожидание продолжается
  - возвращает объект Event с ответом пользователя, при таймауте возвращает None

#### Интерактивные методы

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - диалог подтверждения
  - возвращает `True` (подтверждение) / `False` (отрицание) / `None` (таймаут)
  - встроенное автоматическое распознавание слов подтверждения на китайском и английском языках, можно задать собственный набор слов
  - `method`: метод отправки, по умолчанию "Text"; поддерживается отправка подсказки нетекстовыми способами, такими как "Image"/"Markdown"
  - `hint`: добавлять ли в конец подсказки автоматически подсказку со словами подтверждения (например, "(да/нет)"), по умолчанию False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - меню выбора
  - `options`: список текстов вариантов
  - возвращает индекс выбранного варианта (с нуля), при таймауте возвращает `None`
  - `method`: метод отправки, по умолчанию "Text"; текстовые методы (Text/Markdown/md/Html/h5) по умолчанию добавляют варианты в конец
  - `options_format`: формат вариантов (по умолчанию: "auto" — встроенный стиль выбирается автоматически в зависимости от method)
    - `"auto"`: Markdown → маркированный список (`- 1.вариант`), Html → нумерованный список (`<ol>`), остальное → простой текстовый список
    - `"list"`: по одному в строке, например ``1. Вариант A\n2. Вариант B``
    - `"inline"`: в одну строку, например ``1.A | 2.B``
    - `"md"`: маркированный список Markdown
    - `"html"`: нумерованный список Html
    - `callable`: пользовательская функция, принимает ``list[str]`` и возвращает ``str``
  - `merge_prompt`: принудительно объединять всё в одно сообщение при отправке, по умолчанию False
    - `False` (по умолчанию): текстовые методы объединяют автоматически; нетекстовые методы сначала отправляют prompt, затем варианты методом Text
    - `True`: при любом method всё объединяется в одно сообщение, которое отправляется указанным пользователем методом
  - `placeholder`: заполнитель для вставки вариантов, по умолчанию `{options}`; место в prompt, где встречается этот маркер, заменяется текстом вариантов; при задании пустой строки варианты всегда добавляются в конец

- `collect(fields, timeout_per_field=60.0)` - сбор данных формы
  - `fields`: список полей; каждый элемент содержит `key`, `prompt`, необязательный `validator` и необязательный `method`
  - возвращает словарь `{key: value}`; при таймауте любого поля возвращает `None`
  - каждое поле поддерживает ключ `method` для указания метода отправки, например при сборе изображений: `{"key": "avatar", "prompt": "Отправьте аватар", "method": "Image"}`
  - каждое поле может содержать необязательный ключ `options` (список); при его наличии поле становится вопросом с выбором вариантов (автоматически вызывается логика choose)
  - каждое поле может содержать необязательные ключи `options_format`, `merge_prompt`, `placeholder`, управляющие форматом вариантов, поведением объединения сообщений и заполнителем

- `wait_for(event_type="message", condition=None, timeout=60.0)` - ожидание произвольного события
  - `condition`: функция фильтрации; совпадение при возврате `True`
  - возвращает соответствующий объект Event, при таймауте возвращает `None`

- `conversation(timeout=60.0)` - создание контекста многоходового диалога
  - возвращает объект `Conversation`, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - свойство `is_active` указывает, активен ли диалог

#### Примеры интерактивных методов

**confirm() - диалог подтверждения:**

```python
@command("delete", help="удаление данных")
async def delete_handler(event: Event):
    if await event.confirm("Вы уверены, что хотите удалить все данные?"):
        sdk.storage.delete("all_data")
        await event.reply("Данные удалены")
    else:
        await event.reply("Отменено")
```

**confirm() - с подсказкой:**

```python
# hint=True добавит "(да/нет)" в конец подсказки
if await event.confirm("Продолжить?", hint=True):
    await event.reply("Продолжено")
# Пользователь видит: Продолжить? (да/нет)
```

**choose() - меню выбора:**

```python
@command("color", help="выбор цвета")
async def color_handler(event: Event):
    choice = await event.choose("Выберите цвет:", ["красный", "зелёный", "синий"])
    if choice is not None:
        colors = ["красный", "зелёный", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
```

**choose() - форматирование вариантов и объединение сообщений:**

```python
# формат inline: варианты отображаются в одной строке
choice = await event.choose("Выберите:", ["A", "B", "C"], options_format="inline")
# вывод: 1.A | 2.B | 3.C

# пользовательский формат
choice = await event.choose("Выберите:", ["кот", "пёс"],
    options_format=lambda opts: " / ".join(opts))
# вывод: кот / пёс

# options_format="auto" (по умолчанию): встроенный стиль выбирается автоматически в зависимости от method
# Markdown → маркированный список
choice = await event.choose(
    "## Выберите", ["кот", "пёс"],
    method="Markdown",  # auto автоматически распознаётся как md-список
)
# вывод:
# ## Выберите
# - 1. кот
# - 2. пёс

# Html → нумерованный список
choice = await event.choose(
    "<h2>Выберите</h2>", ["кот", "пёс"],
    method="Html", merge_prompt=True,  # auto автоматически распознаётся как html-список
)
# вывод:
# <h2>Выберите</h2>
# <ol><li>1. кот</li><li>2. пёс</li></ol>

# режим объединения + заполнитель
choice = await event.choose(
    "## Выберите\n{options}\nОтветьте номером",
    ["кот", "пёс"],
    method="Markdown", merge_prompt=True,
)

# пользовательский заполнитель
choice = await event.choose(
    "Выберите: [choices]",
    ["кот", "пёс"],
    placeholder="[choices]",
)
```

**collect() - сбор данных формы:**

```python
@command("register", help="регистрация")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "Введите имя:"},
        {"key": "age", "prompt": "Введите возраст:",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"Регистрация успешна! {data['name']}, {data['age']} лет")
```

**reply с методами, отличными от Text:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Взгляните на это изображение:").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Полную информацию об использовании многоходового диалога Conversation см. в разделе [Многоходовый диалог Conversation](../../advanced/conversation.md).

### Информация о команде

#### Основы команд
- `get_command_name()` - получить имя команды
- `get_command_args()` - получить список аргументов команды
- `get_command_raw()` - получить исходный текст команды
- `get_command_info()` - получить полный словарь информации о команде
- `is_command()` - является ли командой

### Необработанные данные

- `get_raw()` - получить необработанные данные события платформы
- `get_raw_type()` - получить необработанный тип события платформы

### Методы расширений платформы

Адаптеры могут регистрировать специфичные для платформы методы у класса-обёртки Event. Методы доступны только на экземплярах Event соответствующей платформы; при обращении с других платформ выбрасывается `AttributeError`.

Методы платформы через `Event.__getattribute__` имеют приоритет над встроенными методами, поэтому можно переопределять встроенные интерактивные методы, такие как `confirm`, `choose`, `collect`, `wait_reply`, предоставляя специфичные для платформы реализации (например, кнопки, карточки и т.д.). Встроенные реализации экспортируются в виде функций `_builtin_*` и доступны для вызова из переопределяющих методов.

```python
# Событие электронной почты - только почтовые методы
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ возвращает "Hello"
event.get_chat_type()    # ❌ AttributeError

# Событие Telegram - только методы Telegram
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ возвращает "private"
event.get_subject()      # ❌ AttributeError

# Встроенные методы доступны всегда
event.get_text()         # ✅ на любой платформе
event.reply("hi")        # ✅ на любой платформе
```

### Запрос зарегистрированных методов

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### Поддержка `hasattr` и `dir`

```python
hasattr(event, "get_subject")   # возвращает True, только если platform="email"
"get_subject" in dir(event)     # аналогично
```

### Кроссплатформенные расширения (подстановочный знак)

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве имени платформы; зарегистрированные таким образом методы доступны на экземплярах Event **всех платформ**. Подходит для функций, требующих кроссплатформенного переиспользования, таких как диалоги с ИИ, управление контекстом и т.д.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self — это экземпляр Event, с доступом к данным события и встроенным методам
    await self.reply(f"AI: {prompt}")
```

После регистрации обработчики событий любой платформы могут вызывать `event.ai_chat(...)`.

Приоритет разрешения методов (от высшего к низшему): специфичные для платформы методы → методы с подстановочным знаком → встроенные методы → доступ по ключам словаря.

> О том, как разработчики адаптеров регистрируют методы расширений, см. [API системы событий — Кроссплатформенные расширения](../../api-reference/event-system.md#кроссплатформенные-расширения-подстановочный-знак).

## Связанная документация

### Продолжение пути разработки модулей

- [Введение в разработку модулей](getting-started.md) - создание первого модуля
- [Лучшие практики разработки модулей](best-practices.md) - разработка качественных модулей

### Углубление интерактивных возможностей

- [Многоходовый диалог Conversation](../../advanced/conversation.md) - полноценный движок сессий поверх `wait_reply` (сбор данных, проверка, ветвление)