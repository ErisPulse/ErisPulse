# Документация по классу Event

> [!NOTE]
> **Обязательное чтение для разработчиков L1** — одна из пяти ключевых статей в "Читательской дорожке" главной страницы. Необходимо для разработки модулей.

Параметр `event` в обработчиках, благодаря классу Event, может напрямую использовать `.get_text()` / `.reply()` / `.wait_reply()`. В этой статье представлен полный список методов — обращайтесь к ней при написании обработчиков событий, все методы и их поведение здесь описаны.

## Добавление аннотаций типа для параметра event

Параметр `event` в обработчиках событий — это **обёртка Event** (подкласс dict). **Рекомендуется** добавлять аннотацию `Event` (работает и без аннотации, но она полезна для автодополнения в IDE и статической проверки):

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE автоматически подсказывает все удобные методы
    await event.reply(text)   # Опечатки будут обнаружены на этапе статической проверки
```

Без аннотации IDE не распознаёт методы Event (`get_text()` / `reply()` / `wait_reply()` / методы расширения платформы не подсказываются), приходится полагаться на память.

> **Внимание:** `event` в обработчиках событий — это **обёртка Event** (аннотация `Event`); `event` в методах жизненного цикла модуля `on_load` / `on_unload` — это обычный **dict** (аннотация `dict`), не путайте их.

## Основные особенности

- **Полная совместимость со словарём**: Event наследуется от dict
- **Удобные методы**: Предоставляются множество удобных методов
- **Доступ через точку**: Поддерживается доступ к полям события через точку
- **Обратная совместимость**: Все методы необязательны

## Основные методы и поля

```python
from ErisPulse.Core.Event import command, Event

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, Платформа: {platform}, Время: {time}")
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
    await event.reply(f"Тип: {'Личное сообщение' if is_private else 'Группа'}")
```

## Ответы

```python
from ErisPulse.Core.Event import command, Event

@command("ask")
async def ask_command(event: Event):
    await event.reply("Введите ваше имя:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")

@command("price")
async def price_command(event: Event):
    await event.reply("Введите сумму (например: 5元):")
    # Ответ должен соответствовать регулярному выражению, иначе ждём до таймаута
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"Получена сумма: {reply.get_text()}")
```

#### Помимо reply: send_chain

Для сценариев, где `reply()` не подходит — специальные методы платформы (например, Expire/Board), последовательные модификаторы, отправка без содержимого — используйте `event.send_chain`, чтобы получить цепочку отправки с уже заданным целевым и отправляющим аккаунтом, свободно добавляйте модификаторы и отправляйте:

```python
await event.send_chain.At(event.user_id).Text("Содержимое")     # Цепочка модификаторов + отправка
```

Список методов модификаторов см. в [Спецификации методов отправки](../../standards/send-method-spec.md).

## Расширенные возможности интерактивных сессий

> [!NOTE]
> Эти возможности доступны в ErisPulse **2.8.0+**.

```python
# Напоминание сессии: если 5 минут без ответа, напомнить, после ответа отменить
reminder = event.remind(300, "Ещё здесь? Если не хочешь, напиши «выход»")
reminder.cancel()  # Можно также отменить вручную

# Повышение приоритета: при таймауте обязательно выполнить, например, уведомить администратора
event.escalate(1800, lambda e: notify_master("Тикет просрочен"))

# Ожидание нескольких ответов: ждём "подтверждение" и "отказ", срабатывает первый
which, reply = await event.select(
    event.expect(pattern="подтверждение*", user="10001"),
    event.expect(pattern="отказ*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("Таймаут, не получено одобрение")

# Ожидание в сессии: ответы из любой переписки в группе подходят (совместная работа)
reply = await event.wait_reply(session=True, prompt="Кто-нибудь поможет?")

# История сообщений сессии: последние 20 сообщений текущей сессии (включая бота, контекст для ИИ, база для предотвращения повтора)
messages = await event.history(20)

# Транзакции сообщений: при ошибке автоматически отменяются отправленные в транзакции сообщения
async with event.message_tx():
    await event.reply("Обработка, подождите...")
    result = await do_something()
    await event.reply(f"Готово: {result}")
```

## Получение информации о команде

```python
from ErisPulse.Core.Event import command, Event

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"Команда: {cmd_name}, Параметры: {cmd_args}")
```

## Методы уведомлений

```python
from ErisPulse.Core.Event import notice, Event

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("Добро пожаловать в друзья!")
```

## Справочник методов

### Основные методы

#### Основная информация о событии
- `get_id()` - Получить идентификатор события
- `get_time()` - Получить временную метку события (Unix, секунды)
- `get_type()` - Получить тип события (message/notice/request/meta)
- `get_detail_type()` - Получить подробный тип события (private/group/friend и т.д.)
- `get_platform()` - Получить название платформы

#### Информация о боте
- `get_self_platform()` - Получить название платформы бота
- `get_self_user_id()` - Получить идентификатор пользователя бота
- `get_self_account_id()` - Получить идентификатор аккаунта бота (режим с несколькими ботами)
- `get_self_info()` - Получить полную информацию о боте в виде словаря

#### Идентификаторы сессии
- `get_target_id()` - Получить уникальный идентификатор цели (для групповых чатов возвращает `group_id`, для каналов `channel_id`, для личных сообщений `user_id`, берёт первый непустой из `group → channel → guild → thread → user`)
- `get_session_id()` - Получить уникальный идентификатор сессии, формат: `{platform}:{detail_type}:{target_id}`

### Методы сообщений

#### Содержимое сообщения
- `get_message()` - Получить массив сообщений (в формате OneBot12)
- `get_alt_message()` - Получить альтернативный текст сообщения
- `get_text()` - Получить чистый текст (别名 для `get_alt_message()`)
- `get_message_text()` - Получить чистый текст (别名 для `get_alt_message()`)

#### Информация отправителя
- `get_user_id()` - Получить идентификатор отправителя
- `get_user_nickname()` - Получить никнейм отправителя
- `get_sender()` - Получить полную информацию об отправителе в виде словаря

#### Информация о группе/канале
- `get_group_id()` - Получить идентификатор группы (для групповых сообщений)
- `get_channel_id()` - Получить идентификатор канала (для сообщений в каналах)
- `get_guild_id()` - Получить идентификатор сервера (для сообщений на серверах)
- `get_thread_id()` - Получить идентификатор темы/подканала (для сообщений в темах)

#### Относящиеся к @ сообщениям
- `has_mention()` - Содержит ли сообщение упоминание бота
- `get_mentions()` - Получить список всех упомянутых пользователей

### Типы сообщений

#### Основные проверки
- `is_message()` - Является ли событие сообщением
- `is_private_message()` - Является ли сообщение личным
- `is_group_message()` - Является ли сообщение групповым
- `is_at_message()` - Является ли сообщение упоминанием (别名 для `has_mention()`)

### Методы уведомлений

#### Информация об операторе
- `get_operator_id()` - Получить идентификатор оператора
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

#### Одобрение запроса (approve / reject)

Регистрация обработчика запроса и принятие решения:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend(event):
    request_id = event.get_request_id()   # Идентификатор запроса (при отсутствии приведёт к ValueError)
    if event.get_comment() == "секрет":
        result = await event.approve()    # Принять (можно с комментарием: approve(comment="добро пожаловать")）
    else:
        result = await event.reject()     # Отклонить
    if result.get("status") != "ok":
        # Стандартный формат ответа, при ошибке message объясняет причину (например 34001 запрос просрочен)
        pass

@request.on_group_request()               # Запрос на вступление в группу / приглашение
async def handle_group(event):
    await event.approve()
```

> Действия по одобрению выполняются через DSL адаптера `Request`; формат ответа, коды ошибок и требования к реализации адаптера смотрите в [Спецификации действий запроса](../../standards/request-action-spec.md). Также доступен универсальный регистратор `request.on_request()` (без различения типов).

#### Управление цепочкой (done / is_processed / is_stopped)

- `done(claim=True)` - Заявить (по умолчанию) или просто заблокировать последующие обработчики с низким приоритетом
- `is_processed()` - Было ли событие уже заявлено
- `is_stopped()` - Была ли цепочка обработки события заблокирована

Полная семантика заявки и блокировки (взаимодействие приоритетов, заявка команды) смотрите в [Введение в обработку событий · Управление цепочкой: заявка и блокировка](../../getting-started/event-handling.md#цепочка-управления-заявка-и-блокировка).

### Ответы

#### Основные ответы
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - Общий метод ответа
  - `content`: Содержимое отправки (текст, URL и т.д.)
  - `method`: Метод отправки, по умолчанию "Text", можно "Image"/"Voice"/"Video"/"File" и т.д.
  - `at_sender`: Ответить отправителю (автоматически извлекает user_id)
  - `quote`: Цитировать текущее сообщение (автоматически извлекает message_id)
  - `at_users`: Список @ пользователей, например `["user1", "user2"]`
  - `reply_to`: Указать ID сообщения для ответа
  - `at_all`: Ответить всем
  - `**kwargs`: Дополнительные параметры (например, user_id для метода Mention)

- `reply_ob12(message)` - Ответить с использованием OneBot12 сообщений
  - `message`: Список или словарь сегментов OneBot12, можно использовать MessageBuilder

#### Проверка поддержки платформой
- `supports(method)` - Проверить, поддерживает ли платформа метод отправки (например, `"Image"`), возвращает `bool`
- `available_methods()` - Получить список всех доступных методов отправки на платформе, возвращает список имен методов

#### Функция пересылки

> **Внимание**: Функция пересылки реализуется через DSL Send адаптера, Event обёртка сама не предоставляет прямой метод пересылки.

```python
# Переслать сообщение в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или указать другой ID группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

> **Развертывание на нескольких аккаунтах**: При отправке в цепочке обработки события **не нужно явно указывать аккаунт** — фреймворк вводит идентификатор аккаунта, вызвавшего событие, в контекст вызова, `Send` / `Api` / `Request` цепочки автоматически привязываются к аккаунту, вызвавшему событие (явное `Using()` всегда имеет приоритет; в сценариях таймеров без контекста события используется аккаунт по умолчанию). То есть пример выше отправит из аккаунта, получившего это событие, без дополнительного кода.

#### Повторная обработка на разных аккаунтах

При развертывании нескольких аккаунтов в одной группе одно физическое сообщение может быть получено каждым аккаунтом. Поведение фреймворка определяется `ErisPulse.framework.cross_account_policy` (по умолчанию `off` — не связываться):

- `mark`: Последующие копии по-прежнему распределяются, но в верхнем событии добавляется поле `multi_receipt` (`{"event_id": id первого события, "self_id": первый аккаунт}`) — модуль может использовать это поле для принятия решения о пропуске ответа
- `drop`: Копии отбрасываются на этапе распределения, модуль не замечает
- **Преимущество при упоминании**: Копии, упоминающие текущий аккаунт (`self.user_id` / `self.account_id`), не участвуют в связывании (не добавляется `multi_receipt`, не отбрасываются) — модуль, отвечающий на упоминание (`on_at_message`), всегда получает своё событие
- **Привязка аккаунта к сессии**: `ErisPulse.framework.session_accounts` может привязать сессию к единственному аккаунту (только привязанному аккаунту будет распределяться сессия, другие аккаунты отбрасываются; независимо от политики, преимущество упоминания сохраняется)

> Формат конфигурации, префиксы ключей и трёхуровневое разделение дубликатов см. в [Основных понятиях адаптера](../adapters/core-concepts.md) и [Описание файла конфигурации](../../user-guide/configuration.md).

### Функция ожидания ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - Ожидать ответ пользователя
  - `prompt`: Подсказка, если указана, отправляется пользователю
  - `timeout`: Время ожидания (секунды), по умолчанию 60 секунд
  - `callback`: Функция-обратный вызов, выполняется при получении ответа
  - `validator`: Функция проверки, используется для валидации ответа
  - `method`: Метод отправки подсказки, по умолчанию "Text"
  - `pattern`: Шаблон с подстановкой (`*` / `?` / `[seq]`), текст ответа должен соответствовать, иначе продолжаем ожидать
  - `regex`: Регулярное выражение, текст ответа должен соответствовать (один из `pattern` или `regex`), иначе продолжаем ожидать
  - Возвращает объект Event с ответом пользователя, при таймауте возвращает None

#### Интерактивные методы

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Подтверждение диалога
  - Возвращает `True` (подтверждение) / `False` (отрицание) / `None` (таймаут)
  - Встроенные слова подтверждения на китайском и английском автоматически распознаются, можно задать собственный набор слов
  - `method`: Метод отправки, по умолчанию "Text"; поддерживает "Image"/"Markdown" и другие не текстовые методы отправки
  - `hint`: Добавлять ли автоматически подсказку слов подтверждения в конец подсказки (например, "（是/否）" ), по умолчанию False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Выбор меню
  - `options`: Список текстов вариантов
  - Возвращает индекс варианта (0-based), при таймауте возвращает `None`
  - `method`: Метод отправки, по умолчанию "Text"; текстовые методы (Text/Markdown/md/Html/h5) по умолчанию объединяют варианты в конец
  - `options_format`: Формат вариантов (по умолчанию: "auto", автоматически выбирается встроенный стиль в зависимости от method)
    - `"auto"`: Markdown→неперенумерованный список (`- 1. вариант`), Html→упорядоченный список (`<ol>`), другие→простой перечень
    - `"list"`: Каждый вариант на отдельной строке, например ``1. вариантA\n2. вариантB``
    - `"inline"`: Варианты отображаются в одной строке, например ``1.A | 2.B``
    - `"md"`: Markdown неперенумерованный список
    - `"html"`: Html упорядоченный список
    - `callable`: Пользовательская функция, принимает ``list[str]`` и возвращает ``str``
  - `merge_prompt`: Принудительно объединять в одно сообщение, по умолчанию False
    - `False` (по умолчанию): Текстовые методы объединяют автоматически; не текстовые методы сначала отправляют prompt, затем Text с вариантами
    - `True`: Независимо от method объединяются в одно сообщение, отправляется с указанным method
  - `placeholder`: Заменяемый маркер для вариантов, по умолчанию `{options}`; если в prompt встречается этот маркер, он заменяется на текст вариантов, если пустая строка, всегда добавляется в конец

- `collect(fields, timeout_per_field=60.0)` - Сбор формы
  - `fields`: Список полей, каждое содержит `key`, `prompt`, опционально `validator`, опционально `method`
  - Возвращает словарь `{key: value}`, при таймауте любого поля возвращает `None`
  - Каждое поле может иметь ключ `method` для указания метода отправки, например, для сбора изображения: `{"key": "avatar", "prompt": "Отправьте аватар", "method": "Image"}`
  - Каждое поле может иметь ключ `options` (список), при этом поле становится выбором (автоматически вызывается логика choose)
  - Каждое поле может иметь ключи `options_format`, `merge_prompt`, `placeholder` для управления форматом вариантов, поведением объединения сообщений и маркером

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Ожидать произвольного события
  - `condition`: Фильтрующая функция, возвращает `True` при совпадении
  - Возвращает соответствующий Event, при таймауте возвращает None

- `conversation(timeout=60.0)` - Создать контекст многошагового диалога
  - Возвращает объект `Conversation`, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - Свойство `is_active` указывает, активен ли диалог

#### Примеры интерактивных методов

**confirm() - Подтверждение диалога:**

```python
from ErisPulse.Core.Event import Event
@command("delete", help="Удалить данные")
async def delete_handler(event: Event):
    if await event.confirm("Действительно удалить все данные?"):
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

**choose() - Выбор меню:**

```python
from ErisPulse.Core.Event import Event
@command("color", help="Выбрать цвет")
async def color_handler(event: Event):
    choice = await event.choose("Выберите цвет:", ["красный", "зелёный", "синий"])
    if choice is not None:
        colors = ["красный", "зелёный", "синий"]
        await event.reply(f"Выбран: {colors[choice]}")
```

**choose() - Форматирование и объединение сообщений:**

```python
# inline формат: варианты отображаются в одной строке
choice = await event.choose("Выберите:", ["A", "B", "C"], options_format="inline")
# Вывод: 1.A | 2.B | 3.C

# Пользовательская функция форматирования
choice = await event.choose("Выберите:", ["кот", "собака"],
    options_format=lambda opts: " / ".join(opts))
# Вывод: кот / собака

# options_format="auto" (по умолчанию): автоматически выбирается встроенный стиль в зависимости от method
# Markdown → неперенумерованный список
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

**collect() - Сбор формы:**

```python
from ErisPulse.Core.Event import Event
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

**Отправка с помощью non-Text методов:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Посмотрите на это изображение:").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Полное использование многошагового диалога через Conversation смотрите в [Многошаговый диалог Conversation](../../advanced/conversation.md).

### Информация о команде

#### Основная информация о команде
- `get_command_name()` - Получить имя команды
- `get_command_args()` - Получить список аргументов команды
- `get_command_raw()` - Получить исходный текст команды
- `get_command_info()` - Получить полную информацию о команде в виде словаря
- `is_command()` - Является ли событие командой

### Исходные данные

- `get_raw()` - Получить исходные данные события платформы
- `get_raw_type()` - Получить исходный тип события платформы

### Платформенные расширения

Адаптеры могут регистрировать платформенные методы для класса Event. Методы доступны только на Event экземплярах соответствующей платформы, на других платформах вызов приводит к `AttributeError`.

Методы через `Event.__getattribute__` имеют приоритет над встроенными методами, поэтому можно переопределить `confirm`/`choose`/`collect`/`wait_reply` и другие встроенные методы, предоставляя платформенно-специфичную реализацию (например, кнопки, карточки). Встроенная реализация экспортируется как `_builtin_*` функции для переопределения.

```python
# Почтовое событие — только методы email
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ Возвращает "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram событие — только методы Telegram
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
hasattr(event, "get_subject")   # Только если platform="email", возвращает True
"get_subject" in dir(event)     # То же самое
```

### Расширение для всех платформ (подстановочный знак)

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве названия платформы, регистрируя методы, доступные на **всех** платформах Event экземплярах. Подходит для функций, требующих переиспользования между платформами, таких как диалоги с ИИ, управление контекстом.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self — экземпляр Event, можно получить доступ к данным события и встроенным методам
    await self.reply(f"ИИ: {prompt}")
```

После регистрации любой обработчик события на любой платформе может вызвать `event.ai_chat(...)`.

Приоритет разрешения методов (от высшего к низшему): методы платформы → методы подстановочного знака → встроенные методы → доступ по ключу словаря.

> Способ регистрации расширений адаптерами смотрите в [API системы событий - Расширение для всех платформ (подстановочный знак)](../../api-reference/event-system.md#расширение-для-всех-платформ-подстановочный-знак).

## Связанные документы

### Продолжение пути разработки модулей

- [Введение в разработку модулей](getting-started.md) - Создание первого модуля
- [Лучшие практики разработки модулей](best-practices.md) - Разработка качественных модулей

### Глубокое изучение интерактивных возможностей

- [Многошаговый диалог Conversation](../../advanced/conversation.md) - Полная система диалога, основанная на `wait_reply` (сбор, проверка, ветвление)