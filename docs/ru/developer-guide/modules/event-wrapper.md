# Документация по классу Event

> [!NOTE]
> **Обязательный материал уровня L1** — одна из пяти основных статей в разделе "Путь обучения" на главной странице. Необходима для разработки модулей.

Параметр `event` в обработчиках, который позволяет напрямую вызывать `.get_text()` / `.reply()` / `.wait_reply()`, работает благодаря классу-обёртке Event. В данной статье представлен полный список методов — используйте его при написании обработчиков событий, методы и их поведение должны соответствовать описанию ниже.

## Добавление аннотации типа для параметра event

Параметр `event` в обработчиках событий представляет собой **обёртку Event** (подкласс dict). **Рекомендуется** добавлять аннотацию типа `Event` (аннотации не влияют на выполнение, но помогают IDE и статической проверке):

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE автоматически подсказывает все удобные методы
    await event.reply(text)   # Опечатки будут обнаружены на этапе статической проверки
```

Без аннотации IDE не распознаёт методы Event (`get_text()` / `reply()` / `wait_reply()` / дополнительные методы платформы), и всё придётся запоминать наизусть.

> **Обратите внимание:** `event` в обработчике событий — это **обёртка Event** (аннотация `Event`); `event` в методах жизненного цикла модуля `on_load` / `on_unload` — это обычный **dict** (аннотация `dict`), не путайте их.

## Основные особенности

- **Полная совместимость с dict**: Event наследуется от dict
- **Удобные методы**: предоставляет множество удобных методов
- **Доступ точкой**: поддерживает доступ к полям события через точку
- **Обратная совместимость**: все методы являются необязательными

## Основные поля и методы

```python
from ErisPulse.Core.Event import command, Event

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, платформа: {platform}, время: {time}")
```

## Методы сообщений

```python
from ErisPulse.Core.Event import message, Event

@message.on_private_message()
async def private_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}!")
```

## Определение типа сообщения

```python
from ErisPulse.Core.Event import message, Event

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"Тип: {'личное сообщение' if is_private else 'группа'}")
```

## Ответы

```python
from ErisPulse.Core.Event import command, Event

@command("ask")
async def ask_command(event: Event):
    await event.reply("Пожалуйста, введите ваше имя:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")

@command("price")
async def price_command(event: Event):
    await event.reply("Пожалуйста, введите сумму (например: 5元):")
    # Ответ должен соответствовать регулярному выражению, иначе ждём дальше до тайм-аута
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"Получена сумма: {reply.get_text()}")
```

#### reply и send_chain

Для сценариев, где `reply()` не подходит — платформенные методы с модификаторами (например, Expire/Board), последовательные модификаторы, действия без параметров содержимого — используйте `event.send_chain`, чтобы получить цепочку отправки, уже настроенную на цель и аккаунт, и добавляйте модификаторы перед отправкой:

```python
await event.send_chain.At(event.user_id).Text("Содержимое")     # Цепочка модификаторов + отправка
```

Список методов модификаторов см. в [Спецификации методов отправки](../../standards/send-method-spec.md).

## Расширенная интерактивность

> [!NOTE]
> Эти возможности доступны в ErisPulse **2.8.0+**.

```python
# Напоминание: через 5 минут без ответа напоминаем, пользователь отвечает — отменяем
reminder = event.remind(300, "Ещё здесь? Если не хотите общаться, напишите «выход»")
reminder.cancel()  # Можно и вручную отменить

# Превышение тайм-аута: по истечении времени обязательно уведомить, например, если задача не обработана, уведомить администратора
event.escalate(1800, lambda e: notify_master("Задача просрочена"))

# Ожидание нескольких событий: одновременно ждём "согласие" и "отказ", первое поступившее событие — ответ
which, reply = await event.select(
    event.expect(pattern="согласие*", user="10001"),
    event.expect(pattern="отказ*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("Тайм-аут, ответ не получен")

# Ожидание в сессии: ответы от любого участника той же группы (для группового сотрудничества)
reply = await event.wait_reply(session=True, prompt="Кто-нибудь, помогите, ответьте, пожалуйста?")

# История сообщений в сессии: последние 20 сообщений в текущей сессии (включая сообщения бота, контекст для ИИ, база для предотвращения повторов)
messages = await event.history(20)

# Транзакции сообщений: при исключении автоматически отменяются отправленные сообщения в рамках транзакции
async with event.message_tx():
    await event.reply("Обработка, пожалуйста, подождите...")
    result = await do_something()
    await event.reply(f"Завершено: {result}")
```

## Получение информации о команде

```python
from ErisPulse.Core.Event import command, Event

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"Команда: {cmd_name}, аргументы: {cmd_args}")
```

## Методы уведомлений

```python
from ErisPulse.Core.Event import notice, Event

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("Добро пожаловать! Добавьте меня в друзья.")
```

## Справочник методов

### Основные методы

#### Информация об событии
- `get_id()` - Получить ID события
- `get_time()` - Получить временной штамп события (Unix в секундах)
- `get_type()` - Получить тип события (message/notice/request/meta)
- `get_detail_type()` - Получить подробный тип события (private/group/friend и т.д.)
- `get_platform()` - Получить название платформы

#### Информация о боте
- `get_self_platform()` - Получить название платформы бота
- `get_self_user_id()` - Получить ID пользователя бота
- `get_self_account_id()` - Получить ID аккаунта бота (режим множественных ботов)
- `get_self_info()` - Получить полную информацию о боте в виде словаря

#### Идентификаторы сессии
- `get_target_id()` - Получить уникальный идентификатор цели (для групповых чатов возвращает `group_id`, для каналов `channel_id`, для личных сообщений `user_id`, возвращается первый непустой из `group → channel → guild → thread → user`)
- `get_session_id()` - Получить уникальный идентификатор сессии, формат: `{platform}:{detail_type}:{target_id}`

### Методы сообщений

#### Содержимое сообщения
- `get_message()` - Получить массив сегментов сообщения (формат OneBot12)
- `get_alt_message()` - Получить альтернативный текст сообщения
- `get_text()` - Получить текстовое содержимое (псевдоним `get_alt_message()`)
- `get_message_text()` - Получить текстовое содержимое (псевдоним `get_alt_message()`)

#### Информация об отправителе
- `get_user_id()` - Получить ID отправителя
- `get_user_nickname()` - Получить никнейм отправителя
- `get_sender()` - Получить полную информацию об отправителе в виде словаря

#### Информация о группе/канале
- `get_group_id()` - Получить ID группы (для сообщений в группе)
- `get_channel_id()` - Получить ID канала (для сообщений в канале)
- `get_guild_id()` - Получить ID сервера (для сообщений на сервере)
- `get_thread_id()` - Получить ID темы/подканала (для сообщений в теме)

#### Относящиеся к упоминаниям
- `has_mention()` - Содержит ли сообщение упоминание бота
- `get_mentions()` - Получить список всех ID упомянутых пользователей

### Типы сообщений

#### Базовые проверки
- `is_message()` - Является ли событие сообщением
- `is_private_message()` - Является ли сообщение личным
- `is_group_message()` - Является ли сообщение групповым
- `is_at_message()` - Является ли сообщение упоминанием (псевдоним `has_mention()`)

### Методы уведомлений

#### Информация об операторе
- `get_operator_id()` - Получить ID оператора
- `get_operator_nickname()` - Получить никнейм оператора

#### Типы уведомлений
- `is_notice()` - Является ли событие уведомлением
- `is_group_member_increase()` - Событие увеличения участников группы
- `is_group_member_decrease()` - Событие уменьшения участников группы
- `is_friend_add()` - Событие добавления друга (соответствует `detail_type == "friend_increase"`)
- `is_friend_delete()` - Событие удаления друга (соответствует `detail_type == "friend_decrease"`)

### Методы запросов

#### Информация о запросе
- `get_comment()` - Получить комментарий к запросу

#### Типы запросов
- `is_request()` - Является ли событие запросом
- `is_friend_request()` - Является ли запросом дружбы
- `is_group_request()` - Является ли запросом группы

#### Одобрение/отклонение запроса (approve / reject)

Регистрация обработчика запроса и принятие решения:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend(event):
    request_id = event.get_request_id()   # Идентификатор запроса (при отсутствии приведёт к ValueError)
    if event.get_comment() == "пароль":
        result = await event.approve()    # Одобрить (можно добавить комментарий: approve(comment="добро пожаловать")）
    else:
        result = await event.reject()     # Отклонить
    if result.get("status") != "ok":
        # Стандартный формат ответа, при ошибке message объясняет причину (например, 34001 запрос просрочен)
        pass

@request.on_group_request()               # Запрос на вступление в группу / приглашение
async def handle_group(event):
    await event.approve()
```

> Действия одобрения/отклонения выполняются через DSL адаптера `Request`; формат ответа, коды ошибок и требования к реализации адаптера см. в [Спецификации действий запроса](../../standards/request-action-spec.md). Доступен также универсальный регистратор `request.on_request()` (без различения типов).

#### Контроль цепочки (done / is_processed / is_stopped)

- `done(claim=True)` - Заявить (по умолчанию) или просто заблокировать последующие обработчики с низким приоритетом
- `is_processed()` - Было ли событие уже заявлено
- `is_stopped()` - Была ли цепочка обработки события заблокирована

Полная семантика заявки и блокировки (взаимодействие приоритетов, заявка команд) см. в [Введение в обработку событий · Контроль цепочки: заявка и блокировка](../../getting-started/event-handling.md#链路控制认领与阻断).

### Ответы

#### Основные ответы
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - Общий метод ответа
  - `content`: содержимое отправки (текст, URL и т.д.)
  - `method`: метод отправки, по умолчанию "Text", можно "Image"/"Voice"/"Video"/"File" и т.д.
  - `at_sender`: упоминать ли отправителя (автоматически извлекается user_id)
  - `quote`: цитировать ли текущее сообщение (автоматически извлекается message_id)
  - `at_users`: список упоминаний пользователей, например `["user1", "user2"]`
  - `reply_to`: вручную указать ID сообщения для ответа
  - `at_all`: упоминать ли всех участников
  - `**kwargs`: дополнительные параметры (например, user_id для метода Mention)

- `reply_ob12(message)` - Ответ с использованием OneBot12 сегментов сообщения
  - `message`: список или словарь сегментов OneBot12, можно использовать MessageBuilder для построения

#### Проверка поддержки платформой
- `supports(method)` - Проверить, поддерживает ли платформа метод отправки (например, `"Image"`), возвращает `bool`
- `available_methods()` - Список всех доступных методов отправки на платформе, возвращает список названий методов

#### Пересылка

> **Внимание**: функция пересылки должна быть реализована через DSL отправки адаптера, Event-обёртка не предоставляет прямого метода пересылки.

```python
# Переслать сообщение в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или указать другой ID группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

> **Развертывание на нескольких аккаунтах**: отправка в рамках обработки события **не требует явного указания аккаунта** — фреймворк вносит идентификатор аккаунта, вызвавшего событие, в контекст вызова, и `Send` / `Api` / `Request` цепочки при отсутствии явного указания автоматически привязываются к аккаунту, вызвавшему событие (явный `Using()` всегда имеет приоритет; в сценариях таймеров и других без контекста события используется аккаунт по умолчанию). То есть, в примере выше пересылка будет выполнена от аккаунта, получившего это событие, без дополнительного кода.

#### Повторная обработка на разных аккаунтах

При развертывании нескольких аккаунтов в одной группе одно физическое сообщение может быть получено каждым аккаунтом. Фреймворк обрабатывает это по `ErisPulse.framework.cross_account_policy` (по умолчанию `off` — не ассоциировать):

- `mark`: последующие копии будут по-прежнему распределяться, но в верхнем уровне события будет вставлено поле `multi_receipt` (например, `{"event_id": id первого обработанного события, "self_id": первый обработанный аккаунт}`) — модуль может использовать это поле для принятия решения о пропуске ответа
- `drop`: копии будут отбрасываться на этапе распределения, модуль не будет знать об этом

### Ожидание ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - Ожидание ответа пользователя
  - `prompt`: сообщение-подсказка, если указано, будет отправлено пользователю
  - `timeout`: время ожидания (секунды), по умолчанию 60
  - `callback`: функция обратного вызова, выполняется при получении ответа
  - `validator`: функция проверки, для проверки, является ли ответ действительным
  - `method`: метод отправки подсказки, по умолчанию "Text", можно "Image"/"Markdown" и т.д.
  - `pattern`: шаблон подстановки (glob, `*` / `?` / `[seq]`), текст ответа должен соответствовать, иначе ожидание продолжается
  - `regex`: регулярное выражение, текст ответа должен соответствовать (один из `pattern` или `regex`), иначе ожидание продолжается
  - Возвращает объект Event ответа пользователя, при тайм-ауте возвращает `None`

#### Интерактивные методы

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Подтверждение диалога
  - Возвращает `True` (подтверждение), `False` (отказ), `None` (тайм-аут)
  - Встроенные слова подтверждения на китайском и английском языках автоматически распознаются, можно задать собственный набор слов
  - `method`: метод отправки, по умолчанию "Text"; поддерживает "Image"/"Markdown" и другие не-текстовые способы отправки подсказки
  - `hint`: добавлять ли в конец подсказки автоматически подсказку по словам подтверждения (например, "（是/否）"）， по умолчанию False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Выбор меню
  - `options`: список текстов вариантов
  - Возвращает индекс варианта (начиная с 0), при тайм-ауте возвращает `None`
  - `method`: метод отправки, по умолчанию "Text"; текстовые методы (Text/Markdown/md/Html/h5) по умолчанию объединяют варианты в конец
  - `options_format`: формат вариантов (по умолчанию: "auto", автоматически выбирается встроенный стиль в зависимости от method)
    - `"auto"`: Markdown→нумерованный список (например, `- 1. Вариант`), Html→упорядоченный список (например, `<ol>`), другие→простой список
    - `"list"`: каждый вариант на отдельной строке, например ``1. Вариант A\n2. Вариант B``
    - `"inline"`: варианты отображаются в одну строку, например ``1.A | 2.B``
    - `"md"`: Markdown нумерованный список
    - `"html"`: Html упорядоченный список
    - `callable`: пользовательская функция, принимает ``list[str]`` и возвращает ``str``
  - `merge_prompt`: принудительное объединение в одно сообщение, по умолчанию False
    - `False` (по умолчанию): текстовые методы объединяют автоматически; не-текстовые методы сначала отправляют prompt, затем Text-варианты
    - `True`: независимо от method объединяются в одно сообщение, отправляется с указанным method
  - `placeholder`: маркер для вставки вариантов, по умолчанию `{options}`; если в prompt встречается этот маркер, он заменяется на текст вариантов, если пустая строка, всегда добавляется в конец

- `collect(fields, timeout_per_field=60.0)` - Сбор формы
  - `fields`: список полей, каждое поле содержит `key`, `prompt`, необязательный `validator`, необязательный `method`
  - Возвращает словарь `{key: value}`, при тайм-ауте любого поля возвращает `None`
  - Каждое поле может иметь `method`, например, для сбора изображения: `{"key": "avatar", "prompt": "Пожалуйста, отправьте аватар", "method": "Image"}`
  - Каждое поле может иметь `options` (список), если задано, поле становится выбором (автоматически вызывается логика choose)
  - Каждое поле может иметь `options_format`, `merge_prompt`, `placeholder`, чтобы управлять форматом вариантов, поведением объединения сообщений и маркером

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Ожидание произвольного события
  - `condition`: фильтрующая функция, возвращает `True` при совпадении
  - Возвращает соответствующий Event, при тайм-ауте возвращает `None`

- `conversation(timeout=60.0)` - Создать контекст многократного диалога
  - Возвращает объект `Conversation`, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - Свойство `is_active` указывает, активен ли диалог

#### Примеры интерактивных методов

**confirm() - Подтверждение диалога:**

```python
from ErisPulse.Core.Event import Event
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
# hint=True добавит в конец подсказки "（是/否）"
if await event.confirm("Продолжить? ", hint=True):
    await event.reply("Продолжено")
# Пользователь увидит: Продолжить? （是/否）
```

**choose() - Выбор меню:**

```python
from ErisPulse.Core.Event import Event
@command("color", help="Выбрать цвет")
async def color_handler(event: Event):
    choice = await event.choose("Выберите цвет: ", ["красный", "зелёный", "синий"])
    if choice is not None:
        colors = ["красный", "зелёный", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
```

**choose() - Форматирование и объединение сообщений:**

```python
# inline формат: варианты отображаются в одной строке
choice = await event.choose("Выберите: ", ["A", "B", "C"], options_format="inline")
# Вывод: 1.A | 2.B | 3.C

# Пользовательская функция форматирования
choice = await event.choose("Выберите: ", ["кот", "собака"],
    options_format=lambda opts: " / ".join(opts))
# Вывод: кот / собака

# options_format="auto" (по умолчанию): в зависимости от method автоматически выбирается встроенный стиль
# Markdown → нумерованный список
choice = await event.choose(
    "## Выберите", ["кот", "собака"],
    method="Markdown",  # auto автоматически определяет как md список
)
# Вывод:
# ## Выберите
# - 1. кот
# - 2. собака

# Html → упорядоченный список
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
from ErisPulse.Core.Event import Event
@command("register", help="Зарегистрироваться")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "Введите имя: "},
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

> Полное использование многократного диалога с помощью Conversation см. в [Многократный диалог с помощью Conversation](../../advanced/conversation.md).

### Информация о команде

#### Основы команд
- `get_command_name()` - Получить имя команды
- `get_command_args()` - Получить список аргументов команды
- `get_command_raw()` - Получить исходный текст команды
- `get_command_info()` - Получить полную информацию о команде в виде словаря
- `is_command()` - Является ли событие командой

### Исходные данные

- `get_raw()` - Получить исходные данные события платформы
- `get_raw_type()` - Получить тип исходных данных события платформы

### Платформенные расширения

Адаптеры могут регистрировать платформенные методы для класса Event. Методы доступны только на Event-экземплярах соответствующей платформы, при попытке доступа с других платформ будет выброшено `AttributeError`.

Платформенные методы переопределяют встроенные методы через `Event.__getattribute__`, поэтому можно переопределить встроенные методы интеракции, такие как `confirm`, `choose`, `collect`, `wait_reply`, предоставляя специфичные реализации для платформы (например, кнопки, карточки). Встроенные реализации экспортируются как `_builtin_*` функции для переопределения.

```python
# Почтовое событие — только почтовые методы
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ Возвращает "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram событие — только Telegram методы
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
hasattr(event, "get_subject")   # Возвращает True только при platform="email"
"get_subject" in dir(event)     # То же самое
```

### Расширение для всех платформ (шаблон)

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве имени платформы, регистрируя методы, доступные на **всех платформах**. Подходит для функций, требующих кросс-платформенного повторного использования, таких как ИИ-диалоги, управление контекстом и т.д.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self — экземпляр Event, доступен к событиям и встроенным методам
    await self.reply(f"ИИ: {prompt}")
```

После регистрации любой обработчик события на любой платформе может вызывать `event.ai_chat(...)`. 

Приоритет методов (от высокого к низкому): методы платформы → методы шаблона → встроенные методы → доступ по ключу словаря.

> Способ регистрации расширений адаптерами см. в [API системы событий - Кросс-платформенное расширение (шаблон)](../../api-reference/event-system.md#跨平台扩展通配符).

## Связанные документы

### Продолжение пути разработки модулей

- [Начало разработки модулей](getting-started.md) - Создание первого модуля
- [Рекомендации по разработке модулей](best-practices.md) - Разработка качественных модулей

### Глубокое изучение интерактивных возможностей

- [Многократный диалог с помощью Conversation](../../advanced/conversation.md) - Полная система диалога на основе `wait_reply` (сбор, проверка, ветвление)