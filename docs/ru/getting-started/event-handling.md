# Введение в обработку событий

В этом руководстве рассказывается, как обрабатывать различные типы событий в ErisPulse.

## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | Сценарий использования |
|---------|------|---------|
| Событие сообщения | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Событие команды | Сообщение, начинающееся с префикса команды | Обработка команд, вход в функции |
| Событие уведомления | Системные уведомления (добавление друзей, изменение участников группы и т.д.) | Приветствия, уведомления о состоянии |
| Событие запроса | Запросы пользователей (запросы на добавление в друзья, приглашения в группу) | Автоматическая обработка запросов |
| Мета-событие | Системные события (подключение, тайм-аут) | Мониторинг подключения, проверка состояния |

## Обработка событий сообщений

> **Примечание**: Рекомендуется использовать аннотацию типа `Event` в обработчиках событий для поддержки автодополнения и проверки типов в IDE.

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
    sdk.logger.info(f"Пользователь {user_id} отправил сообщение в группу {group_id}")
```

### Подписка на сообщения с упоминанием

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Получить список упомянутых пользователей
    mentions = event.get_mentions()
    await event.reply(f"Вы упомянули следующих пользователей: {mentions}")
```

### Обработка с помощью подстановочных знаков и регулярных выражений

Четыре декоратора сообщений (`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`) поддерживают параметры `pattern` (подстановочные знаки glob) и `regex` (регулярные выражения), несоответствующие сообщения **не запускают** обработчики:

```python
# Подстановочные знаки glob: * любая строка, ? один символ, [seq] набор символов
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("Подтверждение посещения успешно")

# Регулярное выражение: сопоставление суммы
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"Получена сумма: {event.get_text()}")

# Оба параметра pattern и regex заданы → оба должны совпадать
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` также поддерживает эти два параметра (см. [Функция ожидания ответа](../developer-guide/modules/event-wrapper.md#ожидание-ответа)).

## Обработка событий команд

### Базовая команда

```python
from ErisPulse.Core.Event import command

@command("help", help="Показать справочную информацию")
async def help_handler(event):
    help_text = """
Доступные команды:
/help - Показать справку
/ping - Проверить подключение
/info - Просмотр информации
    """
    await event.reply(help_text)
```

### Алиасы команд

```python
@command(["help", "h"], aliases=["帮助"], help="Показать справочную информацию")
async def help_handler(event):
    await event.reply("Справочная информация...")
```

Пользователь может вызвать команду любым из следующих способов:
- `/help`
- `/h`
- `/帮助`

### Параметры команды

```python
@command("echo", help="Отразить сообщение")
async def echo_handler(event):
    # Получить параметры команды
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите текст для отражения")
    else:
        await event.reply(f"Вы сказали: {' '.join(args)}")
```

Параметры сохраняют исходный регистр ввода пользователя (даже если настройки чувствительны к регистру, нормализация имени команды не влияет на содержимое параметров).

### Группы команд

```python
@command("admin.reload", group="admin", help="Перезагрузить модуль")
async def reload_handler(event):
    await event.reply("Модуль перезагружен")

@command("admin.stop", group="admin", help="Остановить бота")
async def stop_handler(event):
    await event.reply("Бот остановлен")
```

Параметр `group` используется только для группировки справки; в примере выше `admin.reload` — это **полное имя команды** (точка — это стиль именования, пользователь должен ввести `/admin.reload`).

### Подкоманды

Имена команд поддерживают **многотокеновую форму с разделением пробелами**, реализуя подкоманды вроде `/admin add`, `/admin user ban`:

```python
@command("admin", help="Команды администратора")
async def admin_handler(event):
    await event.reply("Использование: /admin add | /admin remove")

@command("admin add", help="Добавить администратора")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"Добавлен {target}")

@command("admin remove", aliases=["a remove"], help="Удалить администратора")
async def admin_remove_handler(event):
    await event.reply("Удален")
```

Правила сопоставления (**самое длинное совпадение по префиксу**):

- `/admin add x` сначала соответствует `admin add`, `event.get_command_args()` возвращает `["x"]` (параметры после подкоманды)
- Только зарегистрированная `admin` при `/admin add x` соответствует `admin`, `get_command_args()` возвращает `["add", "x"]` (историческое поведение не изменилось)
- Алиасы поддерживают многотокеновую форму (например, `a remove`), также можно использовать однотокеновые алиасы (например, `a`) для указания подкоманды
- При регистрации родительской и подкоманды, ввод не зарегистрированной подкоманды (например, `/admin list x`) возвращается к родительской команде

**Наследование прав:** Если подкоманда не объявляет `permission`, она автоматически наследует право последней родительской команды, которая объявляла права — защита `/admin` автоматически защищает все его подкоманды; права подкоманды имеют приоритет:

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="Команды администратора")
async def admin_handler(event):
    ...

# Не нужно повторно объявлять permission, автоматически наследуется is_admin
@command("admin add", help="Добавить администратора")
async def admin_add_handler(event):
    ...
```

Обратите внимание: `master=True` и `hidden` **не** наследуются, при необходимости объявите их отдельно в подкоманде; пользовательские ACL (белый и черный списки) проверяются по полному имени команды, шаблоны glob (например, `"admin*"`), могут охватить целую группу подкоманд.

В справке `/help`, подкоманды автоматически вкладываются в видимые родительские команды с отступом (например, `admin` → `admin add` с отступом на один уровень, `admin user` → `admin user ban` с отступом на два уровня).

### Права доступа и контроль доступа команд

Права доступа к командам разделены на три уровня, проверяются сверху вниз (если верхний уровень отклоняет, то нижний не проверяется):

```python
# ① ACL команды (пользовательская настройка): по белому и черному спискам пользователей команды, при отклонении возвращается "Недостаточно прав"
# ② master=True — только владелец фреймворка может выполнить (фреймворк автоматически проверяет, при отклонении возвращается "Недостаточно прав")
@command("restart", master=True, help="Перезапустить модуль")
async def restart_handler(event):
    await event.reply("Модуль перезапущен")

# ③ permission=вызов функции — логика контроля доступа команды (возвращает True для выполнения)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Панель управления")
async def panel_handler(event):
    await event.reply("Добро пожаловать на панель управления")
```

**ACL пользователей команды** (`ErisPulse.event.command.acl`): пользователь может настроить белый и черный списки для любой команды, имена команд поддерживают точное и шаблонное сопоставление (например, `"roll*"`), при отклонении возвращается "Недостаточно прав":

```toml
# config.toml — разрешить только 123456 выполнить restart; 666 всегда запрещен
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Порядок проверки: если `deny` совпадает → запрет; если `allow` не пуст и не совпадает → запрет; если ACL не настроена, используется `event.command.default_allow` (false = строгий режим, без ACL запрет; true = передается разработчику по умолчанию `master=True` / `permission`). API во время выполнения (имена команд поддерживают шаблоны glob):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # Список разрешенных
command.deny_user("restart", "onebot11", "666")       # Список запрещенных
command.remove_acl("restart")                          # Очистить белый и черный списки
command.get_acl("restart")                             # Получить текущий список
```

> Командные обработчики импортируются из пакета событий: `from ErisPulse.Core.Event import command`;
> Также можно получить через пакет событий SDK: `sdk.Event.command` (оба являются одной и той же единственной инстанцией).
> В модулях обычно уже импортируются вместе с декоратором команды (``from ErisPulse.Core.Event import command``).

Кросс-командный / кросс-пользовательский **уровень события** контроля доступа (какие сообщения получает тот или иной человек / группа / бот) проходит через **идентификационные измерения области** (`scope.identity`); **модульный** доступ (какие модули могут использоваться) проходит через **модульные измерения области** (`scope.platforms / bots / sessions`).
См. [Область (scope)](../advanced/scope.md).

> Рекомендуется: если внутри команды требуется взаимодействие с бизнес-логикой, используйте `master=True` / `permission`; для простого контроля доступа по пользователю / группе используйте измерения идентификации области; для контроля доступности модуля используйте измерения области модуля.

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

Система событий ErisPulse использует модель планирования **параллельной обработки с одинаковым приоритетом и последовательной обработки с разным приоритетом**:

```
Событие пришло
    ↓
Группа с приоритетом=10: [Обработчик C || Обработчик D] параллельно → объединить результаты
    ↓ (если не прервано)
Группа с приоритетом=0: [Обработчик A || Обработчик B] параллельно → объединить результаты
    ↓
...
```

- **Параллельная обработка с одинаковым приоритетом**: Обработчики с одинаковым приоритетом выполняются одновременно, повышая пропускную способность
- **Последовательная обработка с разным приоритетом**: Группы с разными приоритетами выполняются последовательно (чем больше значение, тем раньше выполняется), обеспечивая выполнение обработчиков высокого приоритета первыми
- **Copy-On-Write**: Обработчики не создают копии, если не изменяют данные, обеспечивая нулевые накладные расходы
- **Обработка конфликтов**: При изменении одного и того же поля несколькими обработчиками с одинаковым приоритетом используется последнее значение и записывается предупреждение в лог
- **Механизм прерывания**: При вызове `event.done()` (по умолчанию) или `event.done(claim=False)` любым обработчиком, последующие группы с более низким приоритетом пропускаются. Разница между присвоением и блокировкой см. ниже в разделе [Контроль цепочки: присвоение и блокировка](#контроль-цепочки-присвоение-и-блокировка)

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

# Последовательное выполнение с разными приоритетами
@message.on_message(priority=10)
async def handler_c(event):
    # Наивысший приоритет, выполняется первым
    pass
```

> **Предел параллелизма**: Все соответствующие обработчики задач немедленно создаются, но ограничиваются семафором, ограничивающим **количество одновременно выполняемых задач**, по умолчанию **64** (`ErisPulse.framework.handler_max_concurrency`, поддерживает горячую перезагрузку). Задачи, превышающие этот предел, ждут в очереди на семафоре, пока предыдущие не завершатся. В моменты пикового трафика это ваш "сброс давления".
>
> **Медленные логи**: Если один обработчик тратит более **1 секунды**, фреймворк выдает предупреждение в лог (``handler_slow``). Время ожидания `wait_reply` исключается из времени выполнения, чтобы избежать ложных срабатываний из-за "ожидания ответа".

## Фильтрация по области: почему мой модуль не получает сообщения

После поступления события происходит две **тихие** фильтрации (ничего не возвращают, не сообщают об ошибках):

1. **Измерение идентичности** (`ErisPulse.scope.identity`): при входе события в распределитель, по **пользователю > группе > боту > адаптеру** определяется, принимать или нет. Отклоненные **все события** просто отбрасываются, и никакие обработчики (включая диспетчер команд) не запускаются.
2. **Измерение модуля** (`ErisPulse.scope`): когда событие достигает обработчика/команды модуля, по **сессии > боту > платформе** определяется, доступен ли этот модуль, **если не проходит, тихо пропускается**.

```toml
# Пример 1: все сообщения в определенной группе не распространяются
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Пример 2: блокировка MyModule для определенного бота
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

В этом случае сообщения из этой группы, достигая, `MyModule` обработчики команд и событий **не будут запускаться**. Это не ошибка, а механизм фильтрации — при поиске "модуль не реагирует" сначала проверяйте привязку области идентичности и модуля.

- Логи фильтрации видны только на уровне **TRACE** (`core.scope.identity_denied` / `core.scope.denied`), по умолчанию на уровне INFO ничего не видно
- Фреймворк-обработчики (например, диспетчер команд `scope_exempt=True`) не подвержены влиянию **модульного измерения**, но подвержены влиянию **измерения идентичности** (все событие уже отброшено)
- Перед выполнением команды есть третий уровень: ACL пользователя команды (при отклонении возвращается "Недостаточно прав", см. предыдущий раздел)
- Четвертый уровень — **перезапись события** (см. следующий раздел)

> Конфигурация области, синтаксис сопоставления, API во время выполнения см. в [Области (scope)](../../advanced/scope.md).

## Перезапись события: изменение поведения любого типа события без изменения кода модуля

> [!NOTE]
> Эта функция доступна в ErisPulse **2.8.0+**.

При регистрации обработчиков событий параметры, объявленные в декораторе (pattern / regex / master / hidden и т.д.), являются **по умолчанию для разработчика**. Система универсальной перезаписи позволяет пользователю перезаписать поведение любого модуля по **типу события** — стандартные типы OneBot12 (meta / message / notice / request) и расширенные типы ErisPulse (command) имеют собственные перезаписываемые параметры:

| Тип события | Перезаписываемые параметры | Действие |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Условия срабатывания текста + белый список подтипов сообщений |
| `notice` | `detail_types` / `pattern` / `regex` | Белый список подтипов уведомлений + условия текста |
| `request` | `detail_types` / `pattern` / `regex` | Белый список подтипов запросов + условия текста |
| `meta` | `detail_types` | Белый список подтипов мета-событий (connect / heartbeat и т.д.) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Параметры реализации команды (приоритет пользователя) |
| `acl` (специфично для команд) | `allow` / `deny` | Белый и черный списки пользователей команды (по шаблону имени команды) |

```toml
# message: перезапись условия срабатывания текста (и условия в коде AND)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice: только определенные подтипы уведомлений
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command: перезапись параметров реализации (приоритет пользователя — можно ужесточить или ослабить настройки разработчика)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl: белый и черный списки пользователей команды (по шаблону команды)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL по умолчанию (false = строгий режим: без ACL — запрет)
acl_default_allow = true
```

API во время выполнения (`from ErisPulse.Core.Event import overrides` или `sdk.Event.overrides`,
**подпространства имен по типам** — симметричные наборы `set` / `get` / `delete` для каждого типа):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # Условие текста для message
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # Параметры команды
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # Черный список пользователей команды

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # Восстановить настройки по умолчанию разработчика
```

- Условия перезаписи и условия в коде обработчика **одновременно действуют** (логическое И); параметры `command` и объявленные разработчиком **глубоко объединяются** (приоритет перезаписи)
- `detail_types`: событие без `detail_type` разрешается (не убивает неизвестные события)
- `pattern` / `regex`: события без текста (connect / heartbeat и т.д.) не ограничиваются, сразу разрешаются
- Ключ `master` для перезаписи команды синхронно отображается в хранилище `must_master`; запрет команды реализуется через `acl` deny
- Изменения конфигурации применяются немедленно (горячая перезагрузка), проверка формата предупреждает (неизвестные параметры / плохие записи игнорируются)

## Управление цепочкой: присвоение и блокировка

> [!NOTE]
> Параметры `event.done(...)` / `event.mark_processed()` `claim=` / `stop=` требуют ErisPulse **2.7.1+**.

ErisPulse декомпозирует два понятия — "присвоение" и "блокировка" — и объединяет их в единую систему управления с помощью `event.done()`, что позволяет добавлять слои наблюдения, такие как логирование, аудит, права доступа, вокруг обработки команд.

**Точные определения двух понятий:**

- **Присвоение (claim)**: пометить событие как обработанное данным обработчиком (запись в `_processed`). Диспетчер команд, увидев присвоенное событие, **пропускает** его повторную обработку — предотвращает повторную обработку одного и того же сообщения несколькими обработчиками команд. Типичный сценарий: после успешного сопоставления команды присвоить, предотвратить вмешательство диспетчера команд.
- **Блокировка (stop)**: предотвратить распространение события **ниже по приоритету** (запись в `_propagation_stopped`). Обработчики с более низким приоритетом больше не увидят это событие. Типичный сценарий: высокоприоритетный обработчик полностью обработал событие, и не хочет, чтобы низкоприоритетные обработчики выполнялись.

| `event.done(...)` | Присвоение | Блокировка | Сценарий |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | Стандартная практика после обработки команды / обработчика |
| `event.done(stop=False)` | ✔ | ✘ | Только присвоение: низкоприоритетные обработчики (логирование / статистика) продолжают видеть |
| `event.done(claim=False)` | ✘ | ✔ | Только блокировка (например, как фаервол / лимит), но не делает дедупликацию |

`event.done(claim=, stop=)` — это псевдоним `event.mark_processed(claim=, stop=)`, параметры и поведение полностью эквивалентны.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Присвоение + блокировка (стандартная практика после обработки команды)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Только присвоение: низкоприоритетные обработчики продолжают выполняться (логирование / статистика)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Только блокировка: низкоприоритетные обработчики не выполняются, но дедупликация не делается
```

### Блокировка команд и ответов

После успешного сопоставления команды / `wait_reply` совпадения ответа по умолчанию блокируется распространение (обратная совместимость). Можно настроить, чтобы низкоприоритетные обработчики (логирование / аудит / права) по-прежнему могли наблюдать эти сообщения:

```toml
[ErisPulse.event.command]
block = false   # Сообщения команд продолжают распространяться на низкоприоритетные обработчики

[ErisPulse.event.wait_reply]
block = false   # Ответы, потребленные wait_reply, продолжают распространяться на низкоприоритетные обработчики
```

## Обработка уведомлений

### Добавление друга

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "Новый друг"
    await event.reply(f"Добро пожаловать, {nickname}!")
```

### Увеличение участников группы

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать, {user_id}!")
```

### Уменьшение участников группы

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Пользователь {user_id} покинул группу {group_id}")
```

## Обработка запросов

### Запрос на добавление друга

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Получен запрос на добавление друга: {user_id}, комментарий: {comment}")
    
    # Можно обработать запрос с помощью API адаптера
    # Конкретная реализация см. в документации соответствующих адаптеров
```

### Запрос на приглашение в группу

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Получено приглашение в группу {group_id} от {user_id}")
```

## Обработка мета-событий

### События подключения

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"Подключена платформа {platform}")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"Отключена платформа {platform}")
```

### События тайм-аута

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"Проверка тайм-аута для платформы {platform}")
```

### Проверка состояния бота

После отправки мета-события адаптером, фреймворк автоматически отслеживает состояние бота, и вы можете в любой момент проверить:

```python
from ErisPulse import sdk

# Проверить, онлайн ли определенный бот
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Бот онлайн")

# Вывести список всех текущих онлайн ботов
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Получить полную сводку состояния
summary = sdk.adapter.get_status_summary()
```

## Интерактивная обработка

### Использование метода reply для отправки ответа

Метод `event.reply()` поддерживает различные параметры модификации, удобные для отправки сообщений с упоминаниями, ответами и т.д.:

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
await event.reply("Содержание ответа", reply_to="msg_id")

# Упоминание всех участников
await event.reply("Объявление", at_all=True)

# Комбинирование: упоминание пользователей и ответ на сообщение
await event.reply("Содержание", at_users=["user1"], reply_to="msg_id")
```

### Ожидание ответа пользователя

```python
@command("ask", help="Запросить у пользователя")
async def ask_handler(event):
    await event.reply("Пожалуйста, введите ваше имя:")
    
    # Ожидание ответа пользователя, таймаут 30 секунд
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
    
    await event.reply("Пожалуйста, введите ваш возраст (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"Ваш возраст {age} лет")
    else:
        await event.reply("Введено неверное значение или превышен таймаут")
```

### Ожидание ответа с обратным вызовом

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["yes", "y", "确认", "确定", "是", "好", "好的", "ok", "true", "对", "嗯", "行", "同意", "没问题"]:
            await event.reply("Действие подтверждено!")
        else:
            await event.reply("Действие отменено.")
    
    await event.reply("Подтвердите выполнение этого действия? (yes/no)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Подтверждение диалога (confirm)

Ожидание подтверждения или отрицания пользователя, автоматически распознаются встроенные слова подтверждения на китайском и английском языках:

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    if await event.confirm("Вы уверены, что хотите выполнить это действие?"):
        await event.reply("Подтверждено, выполняется...")
    else:
        await event.reply("Отменено")

# Пользовательские слова подтверждения
if await event.confirm("Продолжить?", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### Выбор меню (choose)

Пользователь может ответить номером или текстом опции:

```python
@command("choose", help="Выбрать")
async def choose_handler(event):
    choice = await event.choose(
        "Пожалуйста, выберите цвет:",
        ["красный", "зеленый", "синий"]
    )
    
    if choice is not None:
        colors = ["красный", "зеленый", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
    else:
        await event.reply("Таймаут выбора")
```

**Режим объединения**: `merge_prompt=True` помещает опции в подсказку сообщения, отправляя их одним сообщением с указанным `method`:

```python
# Отправка объединенной подсказки + опций в Markdown
choice = await event.choose(
    "## Пожалуйста, выберите цвет\n{options}\nПожалуйста, ответьте номером",
    ["красный", "зеленый", "синий"],
    method="Markdown",
    merge_prompt=True,
)
```

> Заполнитель `{options}` контролирует позицию вставки опций; если не указан, опции добавляются в конец подсказки.
> Можно настроить пользовательский заполнитель с помощью параметра `placeholder` (например, `placeholder="[выборы]"`).
> `options_format="auto"` (по умолчанию) автоматически выбирает стиль в зависимости от метода: Markdown → маркированный список, Html → нумерованный список, другие → простой текстовый список.
> Для текстовых методов (Text/Markdown/Html и т.д.) опции по умолчанию объединяются в конец; для не-текстовых методов (Image и т.д.) по умолчанию разделяются на два сообщения.

### Сбор формы (collect)

Сбор ввода пользователя в несколько шагов:

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
        await event.reply("Таймаут регистрации или неверный ввод")
```

### Ожидание произвольного события (wait_for)

Ожидание события, удовлетворяющего условию, не ограничено одним пользователем:

```python
@command("wait_member", help="Ожидание нового участника")
async def wait_member_handler(event):
    await event.reply("Ожидание нового участника в группе...")
    
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

Создание интерактивного многошагового контекста диалога:

```python
@command("survey", help="Опрос")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Добро пожаловать в опрос!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Диалог завершен, до свидания!")
            break
        
        text = reply.get_text()
        
        if text == "выход":
            await conv.say("До свидания!")
            break
        
        await conv.say(f"Вы сказали: {text}, продолжайте ввод или ответьте 'выход' для завершения")
```

### Встроенные слова подтверждения

ErisPulse включает в себя встроенные наборы слов подтверждения на китайском и английском языках:

- **Слова подтверждения** (`CONFIRM_YES_WORDS`): 是, yes, y, 确认, 确定, 好, 好的, ok, true, 对, 嗯, 行, 同意, 没问题...
- **Слова отрицания** (`CONFIRM_NO_WORDS`): 否, no, n, 取消, 不, 不要, 不行, cancel, false, 错, 拒绝, 不可以...

## Доступ к данным события

### Часто используемые методы объекта Event

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
    
    # Содержание сообщения
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # Информация о группе
    group_id = event.get_group_id()
    
    # Информация о боте
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # Оригинальные данные
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # Информация о платформе
    platform = event.get_platform()
    
    # Тип сообщения
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Информация о команде
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Платформенные расширения

Помимо встроенных методов, адаптеры платформы регистрируют платформенно-специфичные методы, облегчая доступ к платформенно-специфичным данным.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов платформенно-специфичных методов в зависимости от платформы
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram специфичный метод
    elif platform == "email":
        subject = event.get_subject()           # Email специфичный метод
```

Если вы не уверены, зарегистрирован ли для платформы какой-либо метод, вы можете запросить, какие методы зарегистрированы для определенной платформы:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> Специфичные методы, зарегистрированные для каждой платформы, см. в соответствующей [документации по платформе](../platform-guide/)。

## Лучшие практики обработки событий

### 1. Обработка исключений

```python
@command("process")
async def process_handler(event):
    try:
        # бизнес-логика
        result = await do_some_work()
        await event.reply(f"Результат: {result}")
    except ValueError as e:
        # ожидаемая бизнес-ошибка
        await event.reply(f"Ошибка параметра: {e}")
    except Exception as e:
        # неожиданная ошибка
        sdk.logger.error(f"Обработка не удалась: {e}")
        await event.reply("Произошла ошибка, попробуйте позже")
```

### 2. Запись в лог

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"Обработка сообщения: {user_id} - {text}")
    
    # Использование модульного логгера
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Подробная отладочная информация")
```

### 3. Условная обработка

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Условная обработка - внутри обработчика"""
    # Обрабатывать только сообщения определенных пользователей
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Обрабатывать только сообщения с определенным ключевым словом
    if "ключевое слово" not in event.get_text():
        return
    
    await event.reply("Условие выполнено, обработка сообщения")
```

## Далее

- [Примеры распространенных задач](common-tasks.md) - Изучите реализацию часто используемых функций (включая расширенную отправку сообщений: повтор, таймаут, пакетная отправка)
- [Руководство по особенностям платформы](../platform-guide/README.md) - Полное описание Send DSL, правил отправки, пакетного построения
- [Подробное объяснение Event-обертки](../developer-guide/modules/event-wrapper.md) - Глубокое изучение объекта Event
- [Руководство пользователя](../user-guide/) - Ознакомьтесь с конфигурацией и управлением модулями