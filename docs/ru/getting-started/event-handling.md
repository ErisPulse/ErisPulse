# Введение в обработку событий

В этом руководстве описано, как обрабатывать различные события в ErisPulse.

## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | Сценарии использования |
|---------|------|---------|
| Событие сообщения | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Событие команды | Сообщение, начинающееся с префикса команды | Обработка команд, вход в функции |
| Событие уведомления | Системные уведомления (добавление в друзья, изменения участников группы и т.д.) | Приветствия, уведомления о статусе |
| Событие запроса | Запросы пользователей (запросы на добавление в друзья, приглашения в группу) | Автоматическая обработка запросов |
| Системное событие | Системные события (подключение, пинг) | Мониторинг подключения, проверка состояния |

## Обработка событий сообщений

> **Примечание**: Рекомендуется использовать аннотацию типа `Event` в обработчиках событий, чтобы получить поддержку автодополнения и проверки типов в IDE.

```python
from ErisPulse.Core.Event import Event  # Импорт типа события для аннотации
```

### Подписка на все сообщения

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"Получено сообщение от {user_id}: {text}")
```

### Подписка на личные сообщения

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"Привет, {user_id}! Это личное сообщение.")
```

### Подписка на сообщения в группе

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Сообщение отправлено в группу {group_id} пользователем {user_id}")
```

### Подписка на сообщения с упоминанием

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Получение списка упомянутых пользователей
    mentions = event.get_mentions()
    await event.reply(f"Вы упомянули следующих пользователей: {mentions}")
```

### Слушание с помощью подстановочных знаков и регулярных выражений

Четыре декоратора сообщений (`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`) поддерживают параметры `pattern` (подстановочные знаки glob) и `regex` (регулярные выражения). Сообщения, не соответствующие этим условиям, **не вызывают** обработчик:

```python
# Подстановочные знаки glob: * - любая последовательность, ? - один символ, [seq] - набор символов
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("Успешно зарегистрированы")

# Регулярное выражение: соответствует сумме
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"Получена сумма: {event.get_text()}")

# pattern и regex одновременно → оба условия должны совпадать
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

Параметры `wait_reply` также поддерживают эти два параметра (см. [Функция ожидания ответа](../developer-guide/modules/event-wrapper.md#ожидание-ответа)).

## Обработка событий команд

### Базовые команды

```python
from ErisPulse.Core.Event import command

@command("help", help="Показать справочную информацию")
async def help_handler(event):
    help_text = """
Доступные команды:
/help - Показать справку
/ping - Проверить соединение
/info - Посмотреть информацию
    """
    await event.reply(help_text)
```

### Псевдонимы команд

```python
@command(["help", "h"], aliases=["帮助"], help="Показать справочную информацию")
async def help_handler(event):
    await event.reply("Справочная информация...")
```

Пользователи могут вызывать команду следующими способами:
- `/help`
- `/h`
- `/帮助`

### Параметры команд

```python
@command("echo", help="Повторить сообщение")
async def echo_handler(event):
    # Получить параметры команды
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите сообщение, которое нужно повторить")
    else:
        await event.reply(f"Вы сказали: {' '.join(args)}")
```

### Группировка команд

```python
@command("admin.reload", group="admin", help="Перезагрузить модуль")
async def reload_handler(event):
    await event.reply("Модуль перезагружен")

@command("admin.stop", group="admin", help="Остановить бота")
async def stop_handler(event):
    await event.reply("Бот остановлен")
```

### Права доступа и контроль доступа к командам

Права доступа к командам определяются на трёх уровнях, с верхнего по нижний (если доступ запрещён на верхнем уровне, нижние уровни не проверяются):

```python
# ① ACL доступа к командам (конфигурация со стороны пользователя): по белому и чёрному списку пользователей команды, при запрете возвращается "Недостаточно прав"
# ② master=True — только владелец фреймворка может выполнить (фреймворк автоматически проверяет, при запрете возвращает "Недостаточно прав")
@command("restart", master=True, help="Перезапустить модуль")
async def restart_handler(event):
    await event.reply("Модуль перезапущен")

# ③ permission=функция — собственная логика контроля доступа к команде (выполняется только при возврате True)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Панель управления")
async def panel_handler(event):
    await event.reply("Добро пожаловать на панель управления")
```

**ACL пользователя команд** (`ErisPulse.event.command.acl`): пользователь может настроить белый и чёрный списки для любой команды, имена команд поддерживают точное и шаблонное сопоставление (например, `"roll*"`), при запрете возвращается "Недостаточно прав":

```toml
# config.toml — разрешить только 123456 выполнять restart; 666 всегда запрещено
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Порядок проверки: если есть совпадение в `deny` → запрет; если `allow` не пуст и совпадений нет → запрет; если ACL не настроен, применяется `event.command.default_allow` (`false` = строгий режим, без ACL запрет; `true` → передаётся на отдельную проверку `master=True` / `permission`). API для работы с ACL во время выполнения (поддержка шаблонов в имени команды):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # добавить в белый список
command.deny_user("restart", "onebot11", "666")       # добавить в чёрный список
command.remove_acl("restart")                          # удалить белый и чёрный списки
command.get_acl("restart")                             # получить текущий список
```

> Обработчики команд импортируются из пакета событий: `from ErisPulse.Core.Event import command`;
> также можно получить через пакет SDK: `sdk.Event.command` (оба являются одним и тем же синглтоном).
> В модулях обычно уже импортируются вместе с декоратором команды (`from ErisPulse.Core.Event import command`).

Контроль доступа на уровне событий (кто / какая группа / какой бот может получать сообщения) — через измерение идентичности в области действия (`scope.identity`); доступность на уровне модуля (какие модули можно использовать) — через измерение модуля в области действия (`scope.platforms / bots / sessions`).
См. [Область действия (scope)](../advanced/scope.md).

> Рекомендация: если внутри команды нужно взаимодействовать с бизнес-логикой, используйте `master=True` / `permission`; если нужно контролировать доступ по пользователю / группе, используйте измерение идентичности области действия; если нужно контролировать доступность модуля, используйте измерение модуля области действия.

### Приоритет команд

```python
# Чем больше значение приоритета, тем раньше выполнение
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("Обработчик высокого приоритета")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Обработчик низкого приоритета")
```

### Параллельная обработка событий

Система событий ErisPulse использует модель распределения задач с **параллельным выполнением на одном уровне приоритета и последовательным выполнением между уровнями приоритета**:

```
Событие пришло
    ↓
Группа priority=10: [Обработчик C || Обработчик D] параллельно → объединить результаты
    ↓ (если не прервано)
Группа priority=0: [Обработчик A || Обработчик B] параллельно → объединить результаты
    ↓
...
```

- **Параллельное выполнение на одном уровне приоритета**: обработчики с одинаковым приоритетом выполняются одновременно, повышая пропускную способность
- **Последовательное выполнение между уровнями приоритета**: группы с разными приоритетами выполняются последовательно (чем выше значение приоритета, тем раньше выполнение), гарантируя, что обработчики с высоким приоритетом выполняются первыми
- **Copy-On-Write**: обработчики не создают копию, если не вносят изменения, обеспечивая нулевой накладной расход
- **Обработка конфликтов**: при одновременном изменении одного и того же поля несколькими обработчиками одного уровня приоритета используется последнее значение с записью предупреждения в лог
- **Механизм прерывания**: после вызова `event.done()` (по умолчанию) или `event.done(claim=False)` любым обработчиком пропускаются последующие группы с более низким приоритетом. Разница между присвоением и блокировкой описана в разделе [Контроль маршрута: присвоение и блокировка](#контроль-маршрута-присвоение-и-блокировка)

```python
# Пример: параллельное выполнение обработчиков одного уровня приоритета
@message.on_message(priority=0)
async def handler_a(event):
    # Обработать задачу A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # Выполняется параллельно с handler_a
    event['result_b'] = process_b()

# Последовательное выполнение обработчиков разных уровней приоритета
@message.on_message(priority=10)
async def handler_c(event):
    # Наивысший приоритет, выполняется первым
    pass
```

> **Ограничение параллелизма**: все соответствующие обработчики сразу создаются в виде задач, но ограничиваются сигналом, ограничивающим количество одновременно выполняемых задач, по умолчанию 64 (настройка `ErisPulse.framework.handler_max_concurrency`, поддерживает горячую перезагрузку). Задачи, превышающие лимит, ждут в очереди на сигнале, пока предыдущие не завершатся. В моменты пикового трафика это как ваш "сброс давления".
>
> **Медленные логи**: если один обработчик выполняется дольше 1 секунды, фреймворк записывает предупреждение в лог (`handler_slow`). Время ожидания `wait_reply` исключается из времени выполнения, чтобы не ошибочно считать "ожидание ответа" медленным выполнением.

## Scope filtering: Why didn't my module receive the message

After the event arrives, there are two **silent** filters (neither reply nor error):

1. **Identity dimension** (`ErisPulse.scope.identity`): When an event enters the distribution entry point, it is determined whether to receive it based on User > Group > Bot > Adapter.
   The rejected **entire event** is directly discarded, and no handler (including the command dispatcher) will be triggered.
2. **Module dimension** (`ErisPulse.scope`): When an event reaches a module's handler/command, it is determined based on Session > Bot > Platform whether this module is available; if it **fails the check, it is silently skipped**.

```toml
# Example 1: Do not propagate all messages from a certain group
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Example 2: Block MyModule from a certain Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

At this point, when messages from this group arrive, the `MyModule` command and event handler **will not be scheduled**. This is not a bug, but a filtering mechanism—when troubleshooting "module not responding," prioritize checking the identity and module binding of the scope.

- Filter logs are only visible at the **TRACE** level (`core.scope.identity_denied` / `core.scope.denied`); by default, nothing is visible at the INFO level
- Framework-level handlers (such as the command dispatcher `scope_exempt=True`) are not affected by the **module dimension**, but are affected by the **identity dimension** (the entire event has already been discarded)
- There is a third filter before command execution: command user ACL (replies "insufficient permissions" when denied, see the previous section)
- The fourth is **event overwriting** (see the next section)

> For scope configuration, matching syntax, and runtime API, see [Scope](../../advanced/scope.md).

## Переопределение событий: изменение поведения любого типа событий без изменения кода модуля

> [!NOTE]
> Эта функция доступна начиная с ErisPulse **2.8.0+**.

Параметры обработчиков событий, объявленные при регистрации (`pattern` / `regex` / `master` / `hidden` и т.д.), являются **по умолчанию для разработчиков**.  
Система универсального переопределения позволяет пользователю переопределять поведение любого модуля по **типу события** — стандартные типы OneBot12 (`meta` / `message` / `notice` / `request`) и расширенные типы ErisPulse (`command`) имеют свои собственные переопределяемые параметры:

| Тип события | Переопределяемые параметры | Действие |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Условия триггера текста + белый список подтипов сообщений |
| `notice` | `detail_types` / `pattern` / `regex` | Белый список подтипов уведомлений + текстовое условие |
| `request` | `detail_types` / `pattern` / `regex` | Белый список подтипов запросов + текстовое условие |
| `meta` | `detail_types` | Белый список подтипов мета-событий (connect / heartbeat и т.д.) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Параметры реализации команды (приоритет пользователя) |
| `acl` (специфично для `command`) | `allow` / `deny` | Белый и чёрный списки пользователей команды (по шаблону команды) |

```toml
# message: переопределение условия триггера текста (AND с условиями в коде)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice: только определённые подтипы уведомлений
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command: переопределение параметров реализации (приоритет пользователя — можно ужесточить или ослабить по умолчанию разработчика)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl: чёрный и белый списки пользователей команды (глобально по шаблону команды)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL по умолчанию (false = строгий режим: без ACL — запрет)
acl_default_allow = true
```

API во время выполнения (`from ErisPulse.Core.Event import overrides` или `sdk.Event.overrides`, **пространства имён по типам** — симметричные три метода `set` / `get` / `delete` для каждого типа):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # Условие текста для message
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # Параметры команды
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # Чёрный список пользователей команды

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # Восстановление по умолчанию разработчика
```

- Переопределённые условия и условия в коде обработчика **действуют одновременно** (логическое AND); параметры `command` и объявления разработчика **глубоко сливаются** (приоритет переопределения)
- `detail_types`: события без `detail_type` пропускаются (не блокируются неизвестные события)
- `pattern` / `regex`: события без текста (connect / heartbeat и т.д.) не подпадают под ограничения, пропускаются напрямую
- Переопределённый ключ `master` для `command` синхронно отображается в хранилище ключа `must_master`; запрет команды проходит через `acl deny`
- Изменения конфигурации вступают в силу немедленно (горячая перезагрузка), формат проверяется и выводятся предупреждения (неизвестные параметры / некорректные элементы игнорируются)

## Управление цепочкой: присвоение и блокировка

> [!NOTE]
> Параметры `claim=` / `stop=` для `event.done()` / `event.mark_processed()` требуют ErisPulse **2.7.1+**.

ErisPulse разделяет два ортогональных семантических понятия — "присвоение" и "блокировка" — и объединяет их управление через `event.done()`, что позволяет добавлять слои наблюдения (например, логирование, аудит, права доступа) вокруг обработки команд.

**Точное определение двух понятий:**

- **Присвоение (claim)**: Пометка события как обработанного данным обработчиком (запись в `_processed`). Диспетчер команд видя уже присвоенное событие, **пропускает его** — избегая повторной обработки одного и того же сообщения несколькими обработчиками команд. Типичный сценарий: после успешного сопоставления команды, присвоить событие, чтобы диспетчер команд больше не вмешивался.
- **Блокировка (stop)**: Предотвращение распространения события **ниже по приоритету** (запись в `_propagation_stopped`). Обработчики с более низким приоритетом (например, `on_message`) больше не увидят это событие. Типичный сценарий: высокоприоритетный обработчик уже полностью обработал событие, и не желает, чтобы более низкоприоритетные обработчики его обрабатывали.

| `event.done(...)` | Присвоение | Блокировка | Сценарий |
|-------------------|-----------|------------|---------|
| `event.done()` | ✔ | ✔ | Стандартная практика после завершения обработки команды / обработчиком |
| `event.done(stop=False)` | ✔ | ✘ | Только присвоение: низкоприоритетные наблюдатели (логирование / статистика) продолжают видеть |
| `event.done(claim=False)` | ✘ | ✔ | Только блокировка (например, брандмауэр / ограничение частоты), но без удаления дубликатов команд |

`event.done(claim=, stop=)` — это псевдоним `event.mark_processed(claim=, stop=)`, параметры и поведение у них полностью идентичны.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Присвоение + блокировка (стандартная практика после обработки команды)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Только присвоение: низкоприоритетный обработчик все еще будет выполнен (логирование / статистика)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Только блокировка: низкоприоритетный обработчик не будет выполнен, но без удаления дубликатов
```

### Конфигурация `block` для команд и ответов

После успешного сопоставления команды / после того, как `wait_reply` сопоставил ответ, по умолчанию распространение блокируется (для обратной совместимости). Можно изменить конфигурацию, чтобы разрешить низкоприоритетным обработчикам (логирование / аудит / права доступа) продолжать наблюдать за этими сообщениями:

```toml
[ErisPulse.event.command]
block = false   # Сообщения команд продолжают поступать в низкоприоритетные обработчики

[ErisPulse.event.wait_reply]
block = false   # Ответы, потребленные wait_reply, продолжают поступать в низкоприоритетные обработчики
```

## Обработка уведомительных событий

### Добавление в друзья

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "Новый друг"
    await event.reply(f"Добро пожаловать, {nickname}, в друзья!")
```

### Увеличение числа участников в группе

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать, {user_id}, в группу {group_id}")
```

### Уменьшение числа участников в группе

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Пользователь {user_id} покинул группу {group_id}")
```

## Обработка событий запросов

### Запросы на добавление в друзья

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Получен запрос в друзья: {user_id}, комментарий: {comment}")
    
    # Можно обработать запрос через API адаптера
    # Подробнее смотрите документацию по каждому адаптеру
```

### Запросы на приглашение в группу

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Получено приглашение в группу {group_id}, от пользователя {user_id}")
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

### Запрос статуса бота

После отправки метасобытия адаптером, фреймворк автоматически отслеживает статус бота, и вы можете в любой момент запросить его:

```python
from ErisPulse import sdk

# Проверка, онлайн ли конкретный бот
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Бот в сети")

# Получение списка всех текущих онлайн-ботов
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Получение полной сводки статуса
summary = sdk.adapter.get_status_summary()
```

## Взаимодействие

### Отправка ответа с помощью метода reply

Метод `event.reply()` поддерживает различные параметры, облегчающие отправку сообщений с упоминаниями, ответами и т.д.:

```python
# Простой ответ
await event.reply("Привет")

# Отправка сообщений разных типов
await event.reply("http://example.com/image.jpg", method="Image")  # изображение
await event.reply("http://example.com/voice.mp3", method="Voice")  # голосовое сообщение

# Упоминание одного пользователя
await event.reply("Привет", at_users=["user123"])

# Упоминание нескольких пользователей
await event.reply("Всем привет", at_users=["user1", "user2", "user3"])

# Ответ на сообщение
await event.reply("Содержание ответа", reply_to="msg_id")

# Упоминание всех участников
await event.reply("Объявление", at_all=True)

# Комбинирование: упоминание пользователей + ответ на сообщение
await event.reply("Содержание", at_users=["user1"], reply_to="msg_id")
```

### Ожидание ответа от пользователя

```python
@command("ask", help="Запросить у пользователя")
async def ask_handler(event):
    await event.reply("Введите ваше имя:")
    
    # Ожидание ответа от пользователя, таймаут 30 секунд
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")
    else:
        await event.reply("Таймаут ожидания, пожалуйста, введите снова.")
```

### Ожидание ответа с проверкой

```python
@command("age", help="Запросить возраст")
async def age_handler(event):
    def validate_age(event_data):
        """Проверка корректности возраста"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("Введите ваш возраст (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"Ваш возраст: {age} лет")
    else:
        await event.reply("Ввод некорректен или истек таймаут")
```

### Ожидание ответа с обратным вызовом

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["yes", "y", "да", "д"]:
            await event.reply("Действие подтверждено!")
        else:
            await event.reply("Действие отменено.")
    
    await event.reply("Подтвердите выполнение этого действия? (да/нет)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Подтверждение диалога (confirm)

Ожидание подтверждения или отрицания от пользователя, автоматически распознаются встроенные слова подтверждения на китайском и английском языках:

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    if await event.confirm("Вы действительно хотите выполнить это действие?"):
        await event.reply("Подтверждено, выполняется...")
    else:
        await event.reply("Отменено")

# Пользовательские слова подтверждения
if await event.confirm("Продолжить?", yes_words={"go", "продолжить"}, no_words={"stop", "остановить"}):
    pass
```

### Выбор из меню (choose)

Пользователь может ответить номером опции или текстом:

```python
@command("choose", help="Выбор")
async def choose_handler(event):
    choice = await event.choose(
        "Выберите цвет:",
        ["красный", "зеленый", "синий"]
    )
    
    if choice is not None:
        colors = ["красный", "зеленый", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
    else:
        await event.reply("Таймаут выбора")
```

**Режим объединения**: `merge_prompt=True` объединяет опции в сообщение и отправляет одним сообщением с указанным `method`:

```python
# Отправка объединенного сообщения с опциями в формате Markdown
choice = await event.choose(
    "## Выберите цвет\n{options}\nОтветьте номером",
    ["красный", "зеленый", "синий"],
    method="Markdown",
    merge_prompt=True,
)
```

> Заполнитель `{options}` определяет место вставки опций; если не указан, опции добавляются в конец сообщения.
> Можно изменить заполнитель с помощью параметра `placeholder` (например, `placeholder="[choices]"`).
> `options_format="auto"` (по умолчанию) автоматически выбирает стиль в зависимости от `method`: Markdown → маркированный список, Html → нумерованный список, остальные → простой текстовый список.
> Для текстовых методов (Text/Markdown/Html и т.д.) опции по умолчанию объединяются в конец сообщения; для не-текстовых методов (Image и т.д.) опции по умолчанию отправляются отдельным сообщением.

### Сбор формы (collect)

Сбор информации от пользователя пошагово:

```python
@command("register", help="Регистрация")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "Введите имя:"},
        {"key": "age", "prompt": "Введите возраст:",
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "Введите email:"}
    ])
    
    if data:
        await event.reply(f"Регистрация успешна!\nИмя: {data['name']}\nВозраст: {data['age']}\nEmail: {data['email']}")
    else:
        await event.reply("Таймаут регистрации или некорректный ввод")
```

### Ожидание произвольного события (wait_for)

Ожидание события, соответствующего заданным условиям, не обязательно от того же пользователя:

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
        await event.reply("Таймаут ожидания")
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
            await conv.say("Диалог завершен по таймауту, до свидания!")
            break
        
        text = reply.get_text()
        
        if text == "выход":
            await conv.say("До свидания!")
            break
        
        await conv.say(f"Вы сказали: {text}, продолжайте или ответьте 'выход' для завершения")
```

### Встроенные слова подтверждения

ErisPulse содержит встроенные наборы слов подтверждения на китайском и английском языках:

- **Слова подтверждения** (`CONFIRM_YES_WORDS`): да, yes, y, подтверждение, определенно, хорошо, ok, true, правильно, да, хорошо, согласен, отлично, ...
- **Слова отрицания** (`CONFIRM_NO_WORDS`): нет, no, n, отмена, не, не надо, не получится, cancel, false, неправильно, отклонить, нельзя, ...

## Доступ к данным события

### Распространённые методы объекта Event

```python
@command("info")
async def info_handler(event):
    # Основная информация
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # Информация об отправителе
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
    
    # Определение типа сообщения
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Информация о команде
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Методы расширения платформы

Помимо встроенных методов, адаптеры для каждой платформы также регистрируют специфичные для платформы методы, что позволяет вам легко получить доступ к платформенно-специфичным данным.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов специфичных методов в зависимости от платформы
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Специфичный метод Telegram
    elif platform == "email":
        subject = event.get_subject()           # Специфичный метод электронной почты
```

Если вы не уверены, зарегистрирован ли для платформы определённый метод, вы можете проверить, какие методы зарегистрированы для конкретной платформы:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> Список специфичных методов для каждой платформы можно найти в соответствующем [документе по платформе](../platform-guide/).

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

### 2. Запись в журнал

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"Обработка сообщения: {user_id} - {text}")
    
    # Использование логгера модуля
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Подробная отладочная информация")
```

### 3. Условная обработка

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Условная обработка - проверка внутри обработчика"""
    # Обрабатывать только сообщения определённых пользователей
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Обрабатывать только сообщения с определёнными ключевыми словами
    if "ключевое слово" not in event.get_text():
        return
    
    await event.reply("Условие выполнено, обработка сообщения")
```

## Далее

- [Примеры распространённых задач](common-tasks.md) - Узнайте, как реализовать часто используемые функции (включая продвинутые функции отправки сообщений: повтор, таймаут, пакетная отправка)
- [Руководство по функциональным возможностям платформы](../platform-guide/README.md) - Полное описание Send DSL, цепочечной отправки, отправки правил, пакетного построения
- [Подробное объяснение обёртки Event](../developer-guide/modules/event-wrapper.md) - Глубокое понимание объекта Event
- [Руководство пользователя](../user-guide/) - Узнайте о конфигурации и управлении модулями