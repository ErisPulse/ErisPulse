# Введение в обработку событий

В этом руководстве описано, как обрабатывать различные события в ErisPulse.

## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | Применение |
|---------|------|---------|
| Событие сообщения | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Событие команды | Сообщение, начинающееся с префикса команды | Обработка команд, вход в функции |
| Событие уведомления | Системные уведомления (добавление в друзья, изменения участников группы и т.д.) | Приветствия, уведомления о статусе |
| Событие запроса | Запросы пользователей (запросы на добавление в друзья, приглашения в группу) | Автоматическая обработка запросов |
| Системное событие | Системные события (подключение,heartbeat) | Мониторинг подключения, проверка состояния |

## Обработка событий сообщений

> **Примечание**: Рекомендуется использовать аннотацию типа `Event` в обработчиках событий, чтобы получить поддержку автодополнения и проверки типов в IDE.

```python
from ErisPulse.Core.Event import Event  # Импорт типа события для аннотации
```

### Обработка всех сообщений

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"Получено сообщение от {user_id}: {text}")
```

### Обработка личных сообщений

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"Привет, {user_id}! Это личное сообщение.")
```

### Обработка групповых сообщений

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Пользователь {user_id} отправил сообщение в группу {group_id}")
```

### Обработка сообщений с упоминанием (@)

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Получение списка упомянутых пользователей
    mentions = event.get_mentions()
    await event.reply(f"Вы упомянули следующих пользователей: {mentions}")
```

### Обработка с помощью подстановочных знаков и регулярных выражений

Четыре декоратора сообщений (`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`) поддерживают параметры `pattern` (подстановочные знаки glob) и `regex` (регулярные выражения). Сообщения, не соответствующие этим критериям, **не будут вызывать** обработчик:

```python
# Подстановочные знаки glob: * — любая последовательность, ? — один символ, [seq] — набор символов
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("Успешно зарегистрированы")

# Регулярное выражение: сопоставление суммы
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"Получена сумма: {event.get_text()}")

# Оба параметра pattern и regex заданы → оба должны совпадать
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

Параметры `wait_reply` также поддерживают эти два параметра (см. [Функция ожидания ответа](../developer-guide/modules/event-wrapper.md#ожидание-ответа-функция)).

## Обработка событий команд

### Базовые команды

```python
from ErisPulse.Core.Event import command

@command("help", help="Отображение справочной информации")
async def help_handler(event):
    help_text = """
Доступные команды:
/help - отображение справки
/ping - тестирование соединения
/info - просмотр информации
    """
    await event.reply(help_text)
```

### Псевдонимы команд

```python
@command(["help", "h"], aliases=["помощь"], help="Отображение справочной информации")
async def help_handler(event):
    await event.reply("Справочная информация...")
```

Пользователи могут вызывать команду следующими способами:
- `/help`
- `/h`
- `/помощь`

### Параметры команд

```python
@command("echo", help="Отправка сообщения обратно")
async def echo_handler(event):
    # Получение аргументов команды
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите сообщение для отправки обратно")
    else:
        await event.reply(f"Вы сказали: {' '.join(args)}")
```

### Группировка команд

```python
@command("admin.reload", group="admin", help="Перезагрузка модуля")
async def reload_handler(event):
    await event.reply("Модуль перезагружен")

@command("admin.stop", group="admin", help="Остановка бота")
async def stop_handler(event):
    await event.reply("Бот остановлен")
```

### Права доступа и контроль доступа к командам

Права доступа к командам проверяются по трем уровням, с верхнего на нижний (если доступ на верхнем уровне запрещён, проверка на нижнем уровне не производится):

```python
# ① ACL команды (конфигурация пользователя): пользовательский белый и чёрный списки, при запрете возвращается "Недостаточно прав"
# ② master=True — доступ только для владельца фреймворка (фреймворк автоматически проверяет, при запрете возвращается "Недостаточно прав")
@command("restart", master=True, help="Перезапуск модуля")
async def restart_handler(event):
    await event.reply("Модуль перезапущен")

# ③ permission=функция вызова — логика контроля доступа к команде (выполняется только при возврате True)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Панель управления")
async def panel_handler(event):
    await event.reply("Добро пожаловать на панель управления")
```

**ACL пользователя команды** (`ErisPulse.event.command.acl`): пользователь может настроить белый и чёрный списки для любой команды, имена команд поддерживают точное соответствие и шаблоны glob (например, `"roll*"`), при запрете возвращается "Недостаточно прав":

```toml
# config.toml — разрешено только 123456 выполнить restart; 666 всегда запрещён
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Порядок проверки: если есть совпадение в `deny` → запрет; если `allow` не пустой и нет совпадений → запрет; если ACL не настроен, используется `event.command.default_allow` (`false` = строгий режим, без ACL запрет; `true` → разрешение по умолчанию `master=True` / `permission`). API для работы с ACL во время выполнения (поддержка шаблонов glob для имени команды):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # Список разрешённых пользователей
command.deny_user("restart", "onebot11", "666")       # Список запрещённых пользователей
command.remove_acl("restart")                          # Удаление белого и чёрного списков
command.get_acl("restart")                             # Получение текущих списков
```

> Обработчики команд импортируются из пакета событий: `from ErisPulse.Core.Event import command`;
> Также доступны через пакет SDK: `sdk.Event.command` (это один и тот же синглтон).
> Обычно в модуле уже импортируется через декоратор команды (`from ErisPulse.Core.Event import command`).

Контроль доступа на уровне событий (например, принимать или нет сообщения от определённого пользователя / группы / бота) осуществляется через **идентификационные области** (`scope.identity`); доступность модулей (какие модули можно использовать) контролируется через **области модулей** (`scope.platforms / bots / sessions`).
См. [Области (scope)](../advanced/scope.md).

> Рекомендуется: использовать `master=True` / `permission` для внутренней бизнес-логики; использовать идентификационные области для контроля доступа по пользователю / группе; использовать области модулей для контроля доступности модулей.

### Приоритеты команд

```python
# Чем больше значение приоритета, тем раньше выполняется
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("Обработчик с высоким приоритетом")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Обработчик с низким приоритетом")
```

### Параллельная обработка событий

Система событий ErisPulse использует модель распределения задач: **параллельно в рамках одного приоритета, последовательно между разными приоритетами**:

```
Поступление события
    ↓
Группа priority=10: [Обработчик C || Обработчик D] параллельно → объединение результатов
    ↓ (если не прервано)
Группа priority=0: [Обработчик A || Обработчик B] параллельно → объединение результатов
    ↓
...
```

- **Параллельно в рамках одного приоритета**: обработчики с одинаковым приоритетом выполняются одновременно, повышая пропускную способность
- **Последовательно между приоритетами**: группы с разными приоритетами выполняются последовательно (чем выше значение приоритета, тем раньше он выполняется), обеспечивая выполнение обработчиков с высоким приоритетом первыми
- **Copy-On-Write**: обработчики не создают копий, если не изменяют данные, обеспечивая нулевые накладные расходы
- **Обработка конфликтов**: при одновременном изменении одного и того же поля несколькими обработчиками в рамках одного приоритета используется последнее значение, и записывается предупреждение в лог
- **Механизм прерывания**: вызов `event.done()` (по умолчанию) или `event.done(claim=False)` любым обработчиком приводит к пропуску последующих групп с более низким приоритетом. Разница между "признанием" и "прерыванием" описана ниже в разделе [«Управление цепочкой: признание и прерывание»](#управление-цепочкой-признание-и-прерывание)

```python
# Пример: параллельное выполнение обработчиков с одинаковым приоритетом
@message.on_message(priority=0)
async def handler_a(event):
    # Обработка задачи A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # Выполняется параллельно с handler_a
    event['result_b'] = process_b()

# Последовательное выполнение обработчиков с разными приоритетами
@message.on_message(priority=10)
async def handler_c(event):
    # Наивысший приоритет, выполняется первым
    pass
```

> **Ограничение параллелизма**: все соответствующие обработчики задач немедленно создаются, но ограничиваются сигналом, ограничивающим количество одновременно выполняемых задач, по умолчанию **64** (`ErisPulse.framework.handler_max_concurrency`, поддерживает горячую перенастройку). Задачи, превышающие лимит, ожидают в очереди, пока предыдущие задачи не завершатся. В пиковые нагрузки это работает как ваш «сброс давления».
>
> **Медленные логи**: если обработчик выполняется более **1 секунды**, фреймворк записывает предупреждение в лог (`handler_slow`). Время ожидания ответа (`wait_reply`) исключается из времени выполнения, чтобы избежать ложных предупреждений из-за ожидания ответа.

## Scope filtering: why my module didn't receive the message

After the event arrives, there are two **silent** filters (neither reply nor error):

1. **Identity dimension** (`ErisPulse.scope.identity`): When the event enters the distribution entry point, it is determined whether to receive it based on User > Group > Bot > Adapter.
   The rejected **entire event** is directly discarded, and no handler (including the command dispatcher) will be triggered.
2. **Module dimension** (`ErisPulse.scope`): When the event reaches the handler/command of a certain module, it is determined based on Session > Bot > Platform
   whether the module is available. If it **fails, it is silently skipped**.

```toml
# Example 1: All messages in a group are not propagated
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Example 2: Block MyModule from a certain Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

At this point, when messages from this group arrive, the command and event handlers of `MyModule` **will not be scheduled**. This is not a bug, but a filtering mechanism—when troubleshooting "module not responding," prioritize checking the identity and module binding of the scope.

- Filter logs are only visible at the **TRACE** level (`core.scope.identity_denied` / `core.scope.denied`), and no traces are visible by default at the INFO level.
- Framework-level handlers (such as the command dispatcher `scope_exempt=True`) are not affected by the **module dimension**, but are affected by the **identity dimension** (the entire event has already been discarded).
- There is a third filter before command execution: command user ACL (replies "insufficient permissions" when denied, see previous section).
- The fourth filter is **event overwriting** (see next section).

> Scope configuration, matching syntax, and runtime API can be found in [Scope](../../advanced/scope.md).

## Переопределение событий: изменение поведения любых типов событий без изменения кода модуля

> [!NOTE]
> Эта функция требует ErisPulse **2.8.0+**.

Параметры обработчиков событий, объявленные при регистрации (`pattern` / `regex` / `master` / `hidden` и т.д.), являются **по умолчанию для разработчиков**.  
Система универсального переопределения позволяет переопределять поведение любого модуля по **типу события** — стандартные типы OneBot12 (`meta` / `message` / `notice` / `request`) и расширенные типы ErisPulse (`command`) имеют собственные параметры, подлежащие переопределению:

| Тип события | Параметры, подлежащие переопределению | Назначение |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Условия текстового триггера + белый список подтипов сообщений |
| `notice` | `detail_types` / `pattern` / `regex` | Белый список подтипов уведомлений + текстовое условие |
| `request` | `detail_types` / `pattern` / `regex` | Белый список подтипов запросов + текстовое условие |
| `meta` | `detail_types` | Белый список подтипов метасобытий (connect / heartbeat и т.д.) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Параметры реализации команды (приоритет пользователя) |
| `acl` (специфично для `command`) | `allow` / `deny` | Белый и черный списки пользователей команды (по шаблону команды) |

```toml
# message: переопределение условия текстового триггера (AND с условиями в коде)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice: только определенные подтипы уведомлений
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command: переопределение параметров реализации (приоритет пользователя — можно ужесточить или ослабить настройки по умолчанию)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl: черный список пользователей команды (по шаблону команды)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL по умолчанию (false = строгий режим: без ACL — отклонить)
acl_default_allow = true
```

API во время выполнения (`from ErisPulse.Core.Event import overrides` или `sdk.Event.overrides`,  
**пространства имен подтипов** — симметричные наборы `set` / `get` / `delete` для каждого типа):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # Текстовое условие для message
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # Параметры команды
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # Черный список пользователей команды

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # Восстановление настроек по умолчанию
```

- Переопределенные условия и условия в коде обработчика событий **действуют одновременно** (AND-семантика); параметры `command` и объявленные разработчиком **глубоко объединяются** (приоритет переопределения)
- `detail_types`: события без `detail_type` разрешаются (не удаляются неизвестные события)
- `pattern` / `regex`: события без текста (connect / heartbeat и т.д.) не ограничиваются, сразу разрешаются
- Переопределение ключа `master` для `command` синхронно отображается в хранилище ключа `must_master`; запрет команды происходит через `acl` deny
- Изменения конфигурации применяются немедленно (горячая перезагрузка), формат проверяется (неизвестные параметры / битые записи игнорируются)

## Управление потоком: присвоение и блокировка

> [!NOTE]  
> Параметры `claim=` / `stop=` для `event.done()` / `event.mark_processed()` требуют ErisPulse **2.7.1+**.

ErisPulse разделяет два взаимно независимых семантических понятия — присвоение и блокировку — и объединяет их управление через `event.done()`, что позволяет добавлять слои наблюдения (например, логирование, аудит, права доступа) вокруг обработки команд.

**Точное определение двух понятий:**

- **Присвоение (claim):** пометка события как обработанного данным обработчиком (запись в `_processed`). Командный диспетчер, увидев уже присвоенное событие, **пропускает его** — избегая повторной обработки одного и того же сообщения несколькими обработчиками команд. Типичный сценарий: присвоение после успешного сопоставления команды, чтобы предотвратить вмешательство диспетчера команд.
- **Блокировка (stop):** предотвращение распространения события **ниже по приоритету** (запись в `_propagation_stopped`). Обработчики с более низким приоритетом (например, `on_message`) больше не увидят это событие. Типичный сценарий: высокоприоритетный обработчик полностью обработал событие и не хочет, чтобы его обрабатывали низкоприоритетные обработчики.

| `event.done(...)` | Присвоение | Блокировка | Сценарий |
|-------------------|------------|------------|----------|
| `event.done()` | ✔ | ✔ | Стандартный подход при завершении обработки команды / обработчика |
| `event.done(stop=False)` | ✔ | ✘ | Только присвоение: низкоприоритетные наблюдатели (логирование / статистика) по-прежнему видят событие |
| `event.done(claim=False)` | ✘ | ✔ | Только блокировка (например, как брандмауэр / ограничение скорости), но без удаления дубликатов команд |

`event.done(claim=, stop=)` — это псевдоним `event.mark_processed(claim=, stop=)`, параметры и поведение у них полностью идентичны.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Присвоение + блокировка (стандартный подход при завершении обработки команды)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Только присвоение: низкоприоритетный обработчик по-прежнему будет выполнен (логирование / статистика)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Только блокировка: низкоприоритетный обработчик не будет выполнен, но без удаления дубликатов
```

### Конфигурация `block` для команд и ответов

После успешного сопоставления команды или совпадения ответа в `wait_reply`, по умолчанию блокируется распространение события (для обратной совместимости). Можно настроить, чтобы низкоприоритетные обработчики (логирование / аудит / права доступа) также могли наблюдать эти сообщения:

```toml
[ErisPulse.event.command]
block = false   # Сообщения команд продолжают распространяться к обработчикам с более низким приоритетом

[ErisPulse.event.wait_reply]
block = false   # Ответы, потребленные wait_reply, продолжают распространяться к обработчикам с более низким приоритетом
```

## Обработка событий уведомлений

### Добавление в друзья

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "Новый друг"
    await event.reply(f"Добро пожаловать, {nickname}! Вы добавили меня в друзья.")
```

### Увеличение участников группы

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать, {user_id}, в группу {group_id}")
```

### Уменьшение участников группы

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Участник {user_id} покинул группу {group_id}")
```

## Обработка событий запросов

### Запрос на добавление в друзья

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Получен запрос на добавление в друзья: {user_id}, комментарий: {comment}")
    
    # Запросы можно обрабатывать через API адаптера
    # Подробнее смотрите в документации соответствующих адаптеров
```

### Запрос на приглашение в группу

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Получено приглашение в группу {group_id} от пользователя {user_id}")
```

## Обработка метасобытий

### События подключения

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} платформа подключена")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} платформа отключена")
```

### События пинга

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} пинг")
```

### Запрос состояния бота

После того, как адаптер отправляет метасобытие, фреймворк автоматически отслеживает состояние бота, и вы можете в любое время проверить:

```python
from ErisPulse import sdk

# Проверка, онлайн ли определённый бот
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Бот в сети")

# Получение списка всех текущих онлайн-ботов
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Получение полного сводного отчёта о состоянии
summary = sdk.adapter.get_status_summary()
```

## Интерактивная обработка

### Использование метода reply для отправки ответов

Метод `event.reply()` поддерживает различные модификаторы, что облегчает отправку сообщений с упоминаниями, ответами и т.д.:

```python
# Простой ответ
await event.reply("Привет")

# Отправка сообщений разных типов
await event.reply("http://example.com/image.jpg", method="Image")  # Изображение
await event.reply("http://example.com/voice.mp3", method="Voice")  # Голосовое сообщение

# Упоминание одного пользователя
await event.reply("Привет", at_users=["user123"])

# Упоминание нескольких пользователей
await event.reply("Привет всем", at_users=["user1", "user2", "user3"])

# Ответ на сообщение
await event.reply("Ответ", reply_to="msg_id")

# Упоминание всех участников
await event.reply("Анонс", at_all=True)

# Комбинирование: упоминание + ответ на сообщение
await event.reply("Сообщение", at_users=["user1"], reply_to="msg_id")
```

### Ожидание ответа пользователя

```python
@command("ask", help="Запросить имя у пользователя")
async def ask_handler(event):
    await event.reply("Пожалуйста, введите ваше имя:")
    
    # Ожидание ответа пользователя, таймаут 30 секунд
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")
    else:
        await event.reply("Таймаут ожидания, пожалуйста, повторите ввод.")
```

### Ожидание ответа с проверкой

```python
@command("age", help="Запросить возраст")
async def age_handler(event):
    def validate_age(event_data):
        """Проверка корректности введенного возраста"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("Пожалуйста, введите ваш возраст (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"Ваш возраст: {age} лет")
    else:
        await event.reply("Некорректный ввод или таймаут.")
```

### Ожидание ответа с обратным вызовом

```python
@command("confirm", help="Подтверждение действия")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["yes", "y", "да", "д"]:
            await event.reply("Действие подтверждено!")
        else:
            await event.reply("Действие отменено.")
    
    await event.reply("Подтвердите выполнение действия? (да/нет)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Подтверждение диалога (confirm)

Ожидание подтверждения или отрицания от пользователя, автоматическое распознавание встроенных слов подтверждения на китайском и английском языках:

```python
@command("confirm", help="Подтверждение действия")
async def confirm_handler(event):
    if await event.confirm("Вы уверены, что хотите выполнить это действие?"):
        await event.reply("Подтверждено, выполняется...")
    else:
        await event.reply("Отменено")

# Пользовательские слова подтверждения
if await event.confirm("Продолжить?", yes_words={"go", "продолжить"}, no_words={"stop", "остановить"}):
    pass
```

### Меню выбора (choose)

Пользователь может ответить номером или текстом опции:

```python
@command("choose", help="Выбор")
async def choose_handler(event):
    choice = await event.choose(
        "Пожалуйста, выберите цвет:",
        ["красный", "зелёный", "синий"]
    )
    
    if choice is not None:
        colors = ["красный", "зелёный", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
    else:
        await event.reply("Таймаут выбора")
```

**Режим объединения**: при `merge_prompt=True` опции добавляются в текст сообщения и отправляются одним сообщением с указанным `method`:

```python
# Отправка объединённого сообщения в формате Markdown
choice = await event.choose(
    "## Пожалуйста, выберите цвет\n{options}\nПожалуйста, ответьте номером",
    ["красный", "зелёный", "синий"],
    method="Markdown",
    merge_prompt=True,
)
```

> Заполнитель `{options}` определяет позицию вставки опций; если не указан, то опции добавляются в конец сообщения.  
> Можно настроить заполнитель через параметр `placeholder` (например, `placeholder="[choices]"`).  
> Параметр `options_format="auto"` (по умолчанию) автоматически выбирает формат в зависимости от `method`: Markdown → маркированный список, Html → нумерованный список, другие → обычный текстовый список.  
> Для текстовых методов (Text/Markdown/Html и т.д.) опции по умолчанию объединяются в конец сообщения; для не-текстовых методов (Image и т.д.) опции отправляются отдельным сообщением.

### Сбор анкеты (collect)

Сбор данных пошагово:

```python
@command("register", help="Регистрация")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "Пожалуйста, введите имя:"},
        {"key": "age", "prompt": "Пожалуйста, введите возраст:", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "Пожалуйста, введите email:"}
    ])
    
    if data:
        await event.reply(f"Регистрация прошла успешно!\nИмя: {data['name']}\nВозраст: {data['age']}\nEmail: {data['email']}")
    else:
        await event.reply("Таймаут регистрации или некорректный ввод")
```

### Ожидание произвольного события (wait_for)

Ожидание события, соответствующего заданным условиям, не ограничено одним пользователем:

```python
@command("wait_member", help="Ожидание нового участника")
async def wait_member_handler(event):
    await event.reply("Ожидание нового участника...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Добро пожаловать, новый участник: {evt.get_user_id()}")
    else:
        await event.reply("Таймаут ожидания.")
```

### Многошаговый диалог (conversation)

Создание интерактивного многошагового диалога:

```python
@command("survey", help="Опрос")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Добро пожаловать в опрос!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Диалог завершён по таймауту, до свидания!")
            break
        
        text = reply.get_text()
        
        if text == "выход":
            await conv.say("До свидания!")
            break
        
        await conv.say(f"Вы сказали: {text}, продолжайте ввод или ответьте 'выход' для завершения.")
```

### Встроенные слова подтверждения

ErisPulse включает в себя набор встроенных слов подтверждения на китайском и английском языках:

- **Слова подтверждения** (`CONFIRM_YES_WORDS`): да, yes, y, подтвердить, определить, хорошо, ok, true, верно, хм, хорошо, согласен, нет проблем...
- **Слова отрицания** (`CONFIRM_NO_WORDS`): нет, no, n, отменить, не, не надо, нельзя, cancel, false, ошибка, отклонить, нельзя...

## Доступ к данным событий

### Часто используемые методы объекта Event

```python
@command("info")
async def info_handler(event):
    # Основная информация
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # Информация о отправителе
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # Содержимое сообщения
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # Информация о группе
    group_id = event.get_group_id()
    
    # Информация о боте
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # Исходные данные
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # Информация о платформе
    platform = event.get_platform()
    
    # Проверка типа сообщения
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Информация о команде
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Платформенные расширенные методы

Помимо встроенных методов, адаптеры для каждой платформы регистрируют платформенно-специфичные методы, что позволяет вам получать доступ к платформенно-специфичным данным.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов платформенно-специфичных методов в зависимости от платформы
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Специфичный метод Telegram
    elif platform == "email":
        subject = event.get_subject()           # Специфичный метод электронной почты
```

Если вы не уверены, зарегистрирован ли для платформы определенный метод, вы можете проверить, какие методы зарегистрированы для конкретной платформы:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> Список платформенно-специфичных методов см. в соответствующей [документации платформы](../platform-guide/).

## Лучшие практики обработки событий

### 1. Обработка исключений

```python
@command("process")
async def process_handler(event):
    try:
        # Бизнес-логика
        result = await do_some_work()
        await event.reply(f"Результат: {result}")
    except ValueError as e:
        # Ожидаемая бизнес-ошибка
        await event.reply(f"Ошибка параметра: {e}")
    except Exception as e:
        # Неожиданная ошибка
        sdk.logger.error(f"Обработка не удалась: {e}")
        await event.reply("Обработка не удалась, попробуйте позже")
```

### 2. Запись логов

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"Обработка сообщения: {user_id} - {text}")
    
    # Использование собственного логгера модуля
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Подробная отладочная информация")
```

### 3. Условная обработка

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Условная обработка - проверка внутри обработчика"""
    # Обрабатываем только сообщения от определенных пользователей
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Обрабатываем только сообщения, содержащие определённые ключевые слова
    if "ключевое слово" not in event.get_text():
        return
    
    await event.reply("Условие выполнено, обработка сообщения")
```

## Далее

- [Примеры распространённых задач](common-tasks.md) - Узнайте, как реализовать часто используемые функции (включая продвинутые функции отправки сообщений: повтор/таймаут/пакетная отправка)
- [Руководство по функциям платформы](../platform-guide/README.md) - Подробное описание Send DSL, цепочечной отправки, правил отправки, пакетного построения
- [Подробное объяснение обёрток Event](../developer-guide/modules/event-wrapper.md) - Глубокое понимание объекта Event
- [Руководство для пользователей](../user-guide/) - Узнайте о конфигурации и управлении модулями