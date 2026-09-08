# Подробное описание обёртки событий

Модуль Event предоставляет мощный класс обёртки событий, который упрощает обработку событий.

## Добавление аннотаций типов для параметра event

Параметр `event` обработчика событий является **обёрткой Event** (подкласс dict). Рекомендуется добавлять аннотации типов для него:

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE автоматически подсказывает все удобные методы
    await event.reply(text)   # Опечатки будут обнаружены при статической проверке
```

Без аннотаций IDE не сможет распознать методы Event (`get_text()` / `reply()` / `wait_reply()` / методы расширения платформы не будут подсвечиваться), и приходится полагаться на память при написании.

> **Обратите внимание на различие**: `event` в обратном вызове обработчика событий является **обёрткой Event** (аннотация типа `Event`); `event` в методах жизненного цикла модуля `on_load` / `on_unload` является обычным **dict** (аннотация типа `dict`), не следует их путать.

## Основные возможности

- **Полная совместимость со словарём**: Event наследуется от dict
- **Удобные методы**: Предоставляются много удобных методов
- **Доступ через точку**: Поддерживается доступ к полям события через точку
- **Обратная совместимость**: Все методы являются необязательными

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

## Типы сообщений

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"Тип: {'Личное сообщение' if is_private else 'Групповое сообщение'}")
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
    await event.reply("Пожалуйста, введите сумму (например: 5元):")
    # Ответ должен соответствовать регулярному выражению, иначе продолжаем ожидать до истечения таймаута
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"Получена сумма: {reply.get_text()}")
```

## Расширенные возможности интерактивных диалогов

> [!NOTE]
> Для использования этих функций требуется ErisPulse **2.8.0+**.

```python
# Повторное напоминание: если в течение 5 минут нет ответа, отправить напоминание, при ответе отменить автоматически
reminder = event.remind(300, "Ещё здесь? Чтобы прекратить общение, напишите «Выход»")
reminder.cancel()  # Также можно отменить вручную

# Продление тайм-аута: обязательное достижение срока (не отменяется ответом), например, для уведомления владельца, если задача не обработана в течение длительного времени
event.escalate(1800, lambda e: notify_master("Задача просрочена"))

# Ожидание нескольких путей: одновременно ждём "одобрить" и "отклонить", срабатывает первый поступивший ответ
which, reply = await event.select(
    event.expect(pattern="одобрить*", user="10001"),
    event.expect(pattern="отклонить*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("Тайм-аут, ответа на запрос не получено")

# Ожидание на уровне сессии: ответ любого участника в группе может быть принят (для совместной работы в группе)
reply = await event.wait_reply(session=True, prompt="Кто-нибудь, помогите ответить?")

# Ящик сообщений сессии: последние 20 сообщений текущей сессии (включая сообщения бота, контекст ИИ / база для предотвращения повторения)
messages = await event.history(20)

# Транзакция сообщений: при возникновении ошибки автоматически отменяются отправленные сообщения в рамках транзакции
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
    await event.reply(f"Команда: {cmd_name}, аргументы: {cmd_args}")
```

## Метод уведомления события

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("Добро пожаловать, добавьте меня в друзья!")
```

## Справочник методов

### Основные методы

#### Базовая информация о событии
- `get_id()` - Получить ID события
- `get_time()` - Получить метку времени события (Unix, секунды)
- `get_type()` - Получить тип события (message/notice/request/meta)
- `get_detail_type()` - Получить подробный тип события (private/group/friend и т.д.)
- `get_platform()` - Получить название платформы

#### Информация о боте
- `get_self_platform()` - Получить название платформы бота
- `get_self_user_id()` - Получить ID пользователя бота
- `get_self_account_id()` - Получить ID аккаунта бота (режим с несколькими ботами)
- `get_self_info()` - Получить полную информацию о боте в виде словаря

#### Идентификаторы сессии
- `get_target_id()` - Получить единый идентификатор цели (для групповых чатов возвращает `group_id`, для каналов `channel_id`, для личных сообщений `user_id`, возвращает первое непустое значение в порядке group → channel → guild → thread → user)
- `get_session_id()` - Получить уникальный идентификатор сессии, формат: `{platform}:{detail_type}:{target_id}`

### Методы событий сообщений

#### Текст сообщения
- `get_message()` - Получить массив сообщений (формат OneBot12)
- `get_alt_message()` - Получить альтернативный текст сообщения
- `get_text()` - Получить чистый текст (псевдоним `get_alt_message()`)
- `get_message_text()` - Получить чистый текст (псевдоним `get_alt_message()`)

#### Информация об отправителе
- `get_user_id()` - Получить ID пользователя-отправителя
- `get_user_nickname()` - Получить никнейм отправителя
- `get_sender()` - Получить полную информацию об отправителе в виде словаря

#### Информация о группе/канале
- `get_group_id()` - Получить ID группы (для сообщений в группе)
- `get_channel_id()` - Получить ID канала (для сообщений в канале)
- `get_guild_id()` - Получить ID сервера (для сообщений на сервере)
- `get_thread_id()` - Получить ID темы/подканала (для сообщений в теме)

#### Упоминания
- `has_mention()` - Содержит ли сообщение упоминание бота
- `get_mentions()` - Получить список ID всех упомянутых пользователей

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
- `is_group_member_increase()` - Событие добавления участника в группу
- `is_group_member_decrease()` - Событие удаления участника из группы
- `is_friend_add()` - Событие добавления друга (соответствует `detail_type == "friend_increase"`)
- `is_friend_delete()` - Событие удаления друга (соответствует `detail_type == "friend_decrease"`)

### Методы запросов

#### Информация о запросе
- `get_comment()` - Получить комментарий к запросу

#### Типы запросов
- `is_request()` - Является ли событие запросом
- `is_friend_request()` - Является ли запросом добавления друга
- `is_group_request()` - Является ли запросом добавления в группу

### Ответы

#### Основные ответы
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - Общий метод ответа
  - `content`: Содержимое отправки (текст, URL и т.д.)
  - `method`: Метод отправки, по умолчанию "Text", возможные значения: "Image"/"Voice"/"Video"/"File" и т.д.
  - `at_sender`: Упоминать ли отправителя (автоматически извлекает user_id)
  - `quote`: Цитировать ли текущее сообщение (автоматически извлекает message_id)
  - `at_users`: Список пользователей для упоминания, например `["user1", "user2"]`
  - `reply_to`: Ручное указание ID сообщения для ответа
  - `at_all`: Упоминать ли всех участников
  - `**kwargs`: Дополнительные параметры (например, user_id для метода Mention)

- `reply_ob12(message)` - Ответ с использованием OneBot12-сегментов сообщения
  - `message`: Список или словарь OneBot12-сегментов, можно использовать MessageBuilder для построения

#### Проверка поддержки платформой
- `supports(method)` - Проверить, поддерживает ли текущая платформа метод отправки (например, `"Image"`, `"Voice"`), возвращает `bool`
- `available_methods()` - Получить список всех доступных методов отправки на текущей платформе, возвращает список названий методов

#### Пересылка сообщений

> **Важно**: Функция пересылки реализуется через DSL отправки адаптера, Event-обёртка не предоставляет прямого метода пересылки.

```python
# Пересылка сообщения в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или указать другой ID группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### Ожидание ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - Ожидание ответа пользователя
  - `prompt`: Текст подсказки, если указан, будет отправлен пользователю
  - `timeout`: Время ожидания (секунды), по умолчанию 60 секунд
  - `callback`: Функция обратного вызова, выполняется при получении ответа
  - `validator`: Функция валидации, проверяет корректность ответа
  - `method`: Метод отправки подсказки, по умолчанию "Text"
  - `pattern`: Шаблон glob (`*` / `?` / `[seq]`), текст ответа должен соответствовать, иначе ожидание продолжается
  - `regex`: Регулярное выражение, текст ответа должен соответствовать (только один из `pattern` или `regex` может быть указан), иначе ожидание продолжается
  - Возвращает объект Event с ответом пользователя, при таймауте возвращает None

#### Интерактивные методы

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Подтверждение
  - Возвращает `True` (подтверждение) / `False` (отказ) / `None` (таймаут)
  - Встроенные английские и китайские слова подтверждения автоматически распознаются, можно задать собственные наборы слов
  - `method`: Метод отправки, по умолчанию "Text", поддерживает "Image"/"Markdown" и другие не-текстовые способы отправки подсказки
  - `hint`: Добавлять ли автоматически подсказку с вариантами ответа в конец подсказки (например, "（是/否）"), по умолчанию False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Меню выбора
  - `options`: Список текстовых вариантов
  - Возвращает индекс выбранного варианта (начиная с 0), при таймауте возвращает `None`
  - `method`: Метод отправки, по умолчанию "Text", текстовые методы (Text/Markdown/md/Html/h5) по умолчанию объединяют варианты в конец
  - `options_format`: Формат вариантов (по умолчанию: "auto", автоматически выбирается встроенный стиль в зависимости от метода)
    - `"auto"`: Markdown→неупорядоченный список (`- 1.选项`), Html→упорядоченный список (`<ol>`), другие→простой текстовый список
    - `"list"`: Каждый вариант на отдельной строке, например ``1. 选项A\n2. 选项B``
    - `"inline"`: Варианты отображаются в одной строке, например ``1.A | 2.B``
    - `"md"`: Markdown неупорядоченный список
    - `"html"`: Html упорядоченный список
    - `callable`: Пользовательская функция, принимает ``list[str]`` и возвращает ``str``
  - `merge_prompt`: Принудительно объединять в одно сообщение, по умолчанию False
    - `False` (по умолчанию): Текстовые методы объединяют автоматически; для не-текстовых методов сначала отправляется подсказка, затем текстовые варианты
    - `True`: Независимо от метода объединяются в одно сообщение, отправляется с указанным методом
  - `placeholder`: Заполнитель для вставки вариантов, по умолчанию `{options}`; текст подсказки с этим маркером заменяется на варианты, если установить пустую строку, варианты всегда добавляются в конец

- `collect(fields, timeout_per_field=60.0)` - Сбор формы
  - `fields`: Список полей, каждое поле содержит `key`, `prompt`, необязательный `validator`, необязательный `method`
  - Возвращает словарь `{key: value}`, при таймауте любого поля возвращает `None`
  - Каждое поле может иметь ключ `method` для указания метода отправки, например при сборе изображения: `{"key": "avatar", "prompt": "请发送头像", "method": "Image"}`
  - Каждое поле может иметь ключ `options` (список), при наличии этого ключа поле становится выборочным (автоматически вызывается choose)
  - Каждое поле может иметь ключи `options_format`, `merge_prompt`, `placeholder` для управления форматом вариантов, поведением объединения сообщений и заполнителем

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Ожидание произвольного события
  - `condition`: Функция фильтрации, возвращает `True` при совпадении
  - Возвращает соответствующий объект Event, при таймауте возвращает `None`

- `conversation(timeout=60.0)` - Создание контекста многошагового диалога
  - Возвращает объект `Conversation`, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - Свойство `is_active` указывает, активен ли диалог

#### Примеры интерактивных методов

**confirm() - Подтверждение:**

```python
@command("delete", help="删除数据")
async def delete_handler(event: Event):
    if await event.confirm("确定要删除所有数据吗？"):
        sdk.storage.delete("all_data")
        await event.reply("数据已删除")
    else:
        await event.reply("已取消")
```

**confirm() - С подсказкой:**

```python
# hint=True добавит "（是/否）" в конец подсказки
if await event.confirm("确定继续？", hint=True):
    await event.reply("已继续")
# Пользователь увидит: 确定继续？（是/否）
```

**choose() - Меню выбора:**

```python
@command("color", help="选择颜色")
async def color_handler(event: Event):
    choice = await event.choose("请选择颜色：", ["红色", "绿色", "蓝色"])
    if choice is not None:
        colors = ["红色", "绿色", "蓝色"]
        await event.reply(f"你选择了：{colors[choice]}")
```

**choose() - Форматирование и объединение:**

```python
# inline формат: варианты отображаются в одной строке
choice = await event.choose("请选择：", ["A", "B", "C"], options_format="inline")
# Вывод: 1.A | 2.B | 3.C

# Пользовательская функция
choice = await event.choose("请选择：", ["猫", "狗"],
    options_format=lambda opts: " / ".join(opts))
# Вывод: 猫 / 狗

# options_format="auto" (по умолчанию): автоматически выбирается встроенный стиль в зависимости от метода
# Markdown → неупорядоченный список
choice = await event.choose(
    "## 请选择", ["猫", "狗"],
    method="Markdown",  # auto автоматически распознает как md список
)
# Вывод:
# ## 请选择
# - 1. 猫
# - 2. 狗

# Html → упорядоченный список
choice = await event.choose(
    "<h2>请选择</h2>", ["猫", "狗"],
    method="Html", merge_prompt=True,  # auto автоматически распознает как html список
)
# Вывод:
# <h2>请选择</h2>
# <ol><li>1. 猫</li><li>2. 狗</li></ol>

# Режим объединения + заполнитель
choice = await event.choose(
    "## 请选择\n{options}\n请回复编号",
    ["猫", "狗"],
    method="Markdown", merge_prompt=True,
)

# Пользовательский заполнитель
choice = await event.choose(
    "请选择: [choices]",
    ["猫", "狗"],
    placeholder="[choices]",
)
```

**collect() - Сбор формы:**

```python
@command("register", help="注册")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "请输入姓名："},
        {"key": "age", "prompt": "请输入年龄：",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"注册成功！{data['name']}，{data['age']}岁")
```

**reply с не-Text методами:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("看这张图：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Полное использование многошагового диалога через Conversation см. в [Conversation: Многошаговый диалог](../../advanced/conversation.md).

### Информация о команде

#### Основы команд
- `get_command_name()` - Получить имя команды
- `get_command_args()` - Получить список аргументов команды
- `get_command_raw()` - Получить исходный текст команды
- `get_command_info()` - Получить полную информацию о команде в виде словаря
- `is_command()` - Является ли событие командой

### Исходные данные

- `get_raw()` - Получить исходные данные события платформы
- `get_raw_type()` - Получить тип исходного события платформы

### Платформенные расширения

Адаптеры могут регистрировать платформенно-специфичные методы для Event-обёртки. Методы доступны только на Event-экземплярах соответствующей платформы, при доступе с других платформ выбрасывается `AttributeError`.

Платформенные методы через `Event.__getattribute__` имеют приоритет над встроенными методами, поэтому можно переопределить встроенные интерактивные методы, такие как `confirm`、`choose`、`collect`、`wait_reply`, предоставляя специфичные реализации для платформы (например, кнопки, карточки). Встроенная реализация экспортируется как `_builtin_*` функции для переопределения.

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
hasattr(event, "get_subject")   # Только при platform="email" возвращает True
"get_subject" in dir(event)     # То же самое
```

### Расширение для всех платформ (шаблон "*")

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве названия платформы, регистрируя методы, доступные на **всех** платформах Event-экземпляров. Подходит для функций, требующих кросс-платформенного повторного использования, таких как AI-диалоги, управление контекстом и т.д.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self - экземпляр Event, доступен к данным события и встроенным методам
    await self.reply(f"AI: {prompt}")
```

После регистрации, `event.ai_chat(...)` можно вызывать из любого обработчика событий на любой платформе.

Приоритет разрешения методов (от высшего к низшему): платформенно-специфичные методы → методы шаблона → встроенные методы → доступ через ключ словаря.

> Способы регистрации расширений адаптерами см. в [API системы событий - Расширение для всех платформ (шаблон)](../../api-reference/event-system.md#跨平台扩展通配符).

## Связанные документы

- [Введение в разработку модулей](docs/ru/getting-started.md) - Создание первого модуля
- [Лучшие практики](docs/ru/best-practices.md) - Разработка качественных модулей