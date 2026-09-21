# Введение в обработку событий

В этом руководстве описано, как обрабатывать различные типы событий в ErisPulse.

## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | Сценарии использования |
|---------|------|---------|
| Событие сообщения | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Событие команды | Сообщение, начинающееся с префикса команды | Обработка команд, вход в функционал |
| Событие уведомления | Системные уведомления (добавление друзей, изменения участников группы и т.д.) | Приветственные сообщения, уведомления о состоянии |
| Событие запроса | Запросы от пользователей (запросы на добавление в друзья, приглашения в группу) | Автоматическая обработка запросов |
| Мета-событие | Системные события (подключение,heartbeat) | Мониторинг подключения, проверка состояния |

## Обработка событий сообщений

> **Примечание**: Рекомендуется использовать аннотацию типа `Event` в обработчиках событий для обеспечения автодополнения и проверки типов в IDE.

```python
from ErisPulse.Core.Event import Event  # Импорт типа события для аннотации
```

### Отслеживание всех сообщений

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"Получено сообщение от {user_id}: {text}")
```

### Отслеживание личных сообщений

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"Привет, {user_id}! Это личное сообщение.")
```

### Отслеживание групповых сообщений

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Сообщение отправлено в группу {group_id} пользователем {user_id}")
```

### Отслеживание сообщений с упоминанием

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Получение списка упомянутых пользователей
    mentions = event.get_mentions()
    await event.reply(f"Вы упомянули пользователей: {mentions}")
```

### Обработка с помощью подстановок и регулярных выражений

Четыре декоратора сообщений (`on_message` / `on_private_message` / `on_group_message` / `on_at_message`) поддерживают параметры `pattern` (подстановки glob) и `regex` (регулярные выражения). Сообщения, не соответствующие условиям, **не будут** вызывать обработчик:

```python
# Подстановки glob: * - любая строка, ? - один символ, [seq] - набор символов
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("签到成功")

# Регулярное выражение: совпадение суммы
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"Получена сумма: {event.get_text()}")

# Оба параметра pattern и regex заданы → оба условия должны совпадать
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
/ping - Тест подключения
/info - Показать информацию
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

### Параметры команд

```python
@command("echo", help="Повторить сообщение")
async def echo_handler(event):
    # Получение параметров команды
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите сообщение для повторения")
    else:
        await event.reply(f"Вы сказали: {' '.join(args)}")
```

Параметры сохраняют исходный регистр ввода пользователя (даже если конфигурация чувствительна к регистру, нормализация имени команды не влияет на содержимое параметров).

### Группы команд

```python
@command("admin.reload", group="admin", help="Перезагрузить модуль")
async def reload_handler(event):
    await event.reply("Модуль перезагружен")

@command("admin.stop", group="admin", help="Остановить бота")
async def stop_handler(event):
    await event.reply("Бот остановлен")
```

Параметр `group` используется только для группировки в справке; `admin.reload` — это **целое имя команды** (точка — просто стиль именования, пользователь должен ввести `/admin.reload`).

### Подкоманды

Имена команд поддерживают **многословную** форму с разделителями пробелом, реализуя подкоманды вроде `/admin add`, `/admin user ban`:

```python
@command("admin", help="Команды управления")
async def admin_handler(event):
    await event.reply("Использование: /admin add | /admin remove")

@command("admin add", help="Добавить администратора")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"Добавлен: {target}")

@command("admin remove", aliases=["a remove"], help="Удалить администратора")
async def admin_remove_handler(event):
    await event.reply("Удален")
```

Правила сопоставления (максимальное соответствие префиксу):

- `/admin add x` сначала соответствует `admin add`, `event.get_command_args()` возвращает `["x"]` (параметры после имени подкоманды)
- Только зарегистрирована `admin`, `/admin add x` соответствует `admin`, `get_command_args()` возвращает `["add", "x"]` (историческое поведение не изменилось)
- Алиасы поддерживают многословную форму (например, `a remove`), также можно использовать односимвольные алиасы (например, `a`) для подкоманд
- При регистрации родительской и подкоманды, не зарегистрированная подкоманда (например, `/admin list x`) возвращается к родительской команде

**Наследование прав доступа**: Подкоманда, не объявившая `permission`, автоматически наследует права доступа самого ближайшего предка, объявившего permission — защита `/admin` автоматически защищает все его подкоманды; права доступа, объявленные самой подкомандой, имеют приоритет:

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="Команды управления")
async def admin_handler(event):
    ...

# Нет необходимости повторно объявлять permission, автоматически наследуется is_admin
@command("admin add", help="Добавить администратора")
async def admin_add_handler(event):
    ...
```

Примечание: `master=True` и `hidden` **не** наследуются, при необходимости объявите их отдельно в подкоманде; пользовательский ACL (белый и черный списки) соответствует полному имени команды, шаблоны glob, такие как `"admin*"` могут охватывать все подкоманды.

В справке `/help` подкоманды автоматически отображаются вложенно под видимыми родительскими командами (например, `admin` → `admin add` с отступом на один уровень, `admin user` → `admin user ban` с отступом на два уровня).

### Права доступа и управление доступом к командам

Права доступа к командам разделены на три уровня, которые проверяются сверху вниз (если верхний уровень отклоняет, нижние уровни не проверяются):

```python
# ① ACL пользователей команды (настройка со стороны пользователя): по белому и черному списку пользователей для команды, при отказе возвращается "Недостаточно прав"
# ② master=True — только владелец фреймворка может выполнить (фреймворк автоматически проверяет, при отказе возвращается "Недостаточно прав")
@command("restart", master=True, help="Перезапустить модуль")
async def restart_handler(event):
    await event.reply("Модуль перезапущен")

# ③ permission=вызов функции — логика управления самой командой (возвращает True для выполнения)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Панель управления")
async def panel_handler(event):
    await event.reply("Добро пожаловать на панель управления")
```

**ACL пользователей команды** (`ErisPulse.event.command.acl`): пользователь может настроить белый и черный списки для любой команды, имена команд поддерживают точное и шаблонное соответствие (например, `"roll*"`), при отказе возвращается "Недостаточно прав":

```toml
# config.toml — разрешить выполнение restart только пользователю 123456; запретить 666
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Порядок проверки: если `deny` совпадает → отказ; если `allow` не пустой и не совпадает → отказ; если ACL не настроена, используется `event.command.default_allow` (`false` = строгий режим, без ACL — отказ; `true` — передается разработчику по умолчанию `master=True` / `permission`). API во время выполнения (поддержка шаблонов команд):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # Список разрешенных
command.deny_user("restart", "onebot11", "666")       # Список запрещенных
command.remove_acl("restart")                          # Очистить белый и черный списки
command.get_acl("restart")                             # Получить текущий список
```

> Командный обработчик импортируется из пакета событий: `from ErisPulse.Core.Event import command`;
> Также можно получить через пакет SDK: `sdk.Event.command` (оба являются одной и той же единственной копией).
> В модуле обычно уже импортируется вместе с декоратором команды (из `from ErisPulse.Core.Event import command`).

**Уровень события** (доступ к сообщениям от одного пользователя / группы / бота) — идет через **идентификационные** области (`scope.identity`); **уровень модуля** (какие модули можно использовать) — идет через **области модуля** (`scope.platforms / bots / sessions`).
См. [Области (scope)](../advanced/scope.md).

> Рекомендуется: если внутри команды нужно взаимодействовать с бизнес-логикой, используйте `master=True` / `permission`; для доступа по пользователю / группе используйте идентификационные области; для управления доступностью модуля используйте области модуля.

### Приоритет команд

```python
# Чем больше значение приоритета, тем раньше выполняется
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("Обработчик высокого приоритета")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Обработчик низкого приоритета")
```

### Параллельная обработка событий

Система событий ErisPulse использует модель планирования: **параллельно в рамках одного приоритета, последовательно между разными приоритетами**:

```
Событие поступило
    ↓
Группа с приоритетом 10: [Обработчик C || Обработчик D] параллельно → Объединить результаты
    ↓ (если не прервано)
Группа с приоритетом 0: [Обработчик A || Обработчик B] параллельно → Объединить результаты
    ↓
...
```

- **Параллельно в рамках одного приоритета**: Обработчики с одинаковым приоритетом выполняются одновременно, повышая пропускную способность
- **Последовательно между разными приоритетами**: Группы с разными приоритетами выполняются последовательно (чем больше значение, тем раньше выполняется), обеспечивая выполнение обработчиков высокого приоритета
- **Copy-On-Write**: Обработчики не создают копию, если не вносят изменений, обеспечивая нулевые накладные расходы
- **Обработка конфликтов**: При изменении одного и того же поля несколькими обработчиками одного приоритета используется последнее значение и записывается предупреждение в лог
- **Механизм прерывания**: При вызове `event.done()` (по умолчанию) или `event.done(claim=False)` любым обработчиком, последующие группы с более низким приоритетом пропускаются. Разница между присвоением и блокировкой описана ниже в разделе [Контроль цепочки: присвоение и блокировка](#контроль-цепочки-присвоение-и-блокировка)

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
    # Самый высокий приоритет, выполняется первым
    pass
```

> **Лимит параллелизма**: Все соответствующие обработчики задач немедленно создаются, но ограничиваются сигналом, ограничивающим **количество одновременно выполняемых задач** по умолчанию **64** (`ErisPulse.framework.handler_max_concurrency`, поддерживает горячее обновление). Задачи, превышающие лимит, ждут в очереди на сигнале, пока предыдущие не завершатся. Во время пикового трафика это ваш "сброс давления".
>
> **Медленный лог**: Если одиночный обработчик занимает более **1 секунды**, фреймворк записывает предупреждение в лог (`handler_slow`). Время ожидания `wait_reply` вычитается из времени выполнения, чтобы избежать ложных срабатываний из-за ожидания ответа от пользователя.

## Фильтрация области: почему мой модуль не получает сообщения

После того, как событие достигает точки распределения, оно проходит через два **тихих** фильтра (ни один из них не возвращает ответ и не генерирует ошибку):

1. **Фильтрация по идентичности** (`ErisPulse.scope.identity`): при входе события в распределительную точку определяется, будет ли оно доставлено, по иерархии пользователь > группа > бот > адаптер.  
   Отказанные события **полностью отбрасываются**, и ни один обработчик (включая диспетчер команд) не будет запущен.
2. **Фильтрация по модулю** (`ErisPulse.scope`): когда событие достигает обработчика или команды модуля, определяется, доступен ли этот модуль, по иерархии сессия > бот > платформа.  
   Если модуль не проходит проверку, он **тихо пропускается**.

```toml
# Пример 1: все сообщения в определённой группе не распространяются
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Пример 2: блокировка MyModule для определённого бота
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

В этом случае, когда сообщения из этой группы достигают системы, обработчики команд и событий `MyModule` **не будут вызваны**. Это не ошибка, а механизм фильтрации — при диагностике отсутствия реакции модуля, сначала проверяйте привязку области и идентичности.

- Журнал фильтрации доступен только на уровне **TRACE** (`core.scope.identity_denied` / `core.scope.denied`), по умолчанию на уровне INFO никаких следов не видно.
- Обработчики на уровне фреймворка (например, диспетчер команд с `scope_exempt=True`) не подвержены влиянию **модульной фильтрации**, но подвержены влиянию **фильтрации идентичности** (всё событие уже отброшено).
- Перед выполнением команды существует ещё третий уровень: ACL пользователя команды (при отказе возвращается сообщение "Недостаточно прав", см. предыдущий раздел).
- Четвёртый уровень — **перезапись события** (см. следующий раздел).

> [!NOTE]
> **Отношение между фильтрацией области и присвоением события (claim)**: оба тихих фильтра применяются до **вызова обработчика** — обработчики, отфильтрованные таким образом, не имеют возможности выполниться и, следовательно, не участвуют в статусе присвоения (`event.done()` / `mark_processed()`). Статус присвоения события определяется только **фактически выполненными** обработчиками (присвоение при срабатывании команды, присвоение при ответе, явный вызов); отказ по области не присваивает и не блокирует (тихо пропускается, сообщение продолжает движение по оставшейся цепочке распределения).

> Дополнительные сведения о конфигурации области, синтаксисе сопоставления и API во время выполнения см. в разделе [Область (scope)](../../advanced/scope.md).

## Переопределение событий: изменение поведения произвольных типов событий без изменения кода модуля

> [!NOTE]
> Эта функция требует ErisPulse **2.8.0+**.

Параметры, объявленные при регистрации обработчиков событий (`pattern` / `regex` / `master` / `hidden` и т.д.), являются **по умолчанию разработчика**.
Система унифицированного переопределения позволяет пользователям переопределять поведение любого модуля по **типу события** — стандартные типы OneBot12 (`meta` / `message` / `notice` / `request`) и расширенные типы ErisPulse (`command`) имеют собственные параметры, доступные для переопределения:

| Тип события | Параметры, доступные для переопределения | Действие |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Условия триггера текста + белый список подтипов сообщений |
| `notice` | `detail_types` / `pattern` / `regex` | Белый список подтипов уведомлений + текстовые условия |
| `request` | `detail_types` / `pattern` / `regex` | Белый список подтипов запросов + текстовые условия |
| `meta` | `detail_types` | Белый список подтипов метасобытий (connect / heartbeat и т.д.) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Параметры реализации команды (приоритет пользователя) |
| `acl` (специфично для `command`) | `allow` / `deny` | Белый и черный списки пользователей команды (по шаблону имени команды) |

```toml
# message: переопределение условий триггера текста (AND с условиями в коде модуля)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice: обрабатывать только определенные подтипы уведомлений
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command: переопределение параметров реализации (приоритет пользователя — можно ужесточить или ослабить настройки по умолчанию разработчика)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl: черный и белый списки пользователей команды (по шаблону имени команды)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL по умолчанию (false = строгий режим: без ACL — запрет)
acl_default_allow = true
```

API во время выполнения (`from ErisPulse.Core.Event import overrides` или `sdk.Event.overrides`,
**пространство имен подтипов** — для каждого типа симметричные три метода `set` / `get` / `delete`):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # текстовое условие для message
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # параметры команды
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # черный список пользователей команды

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # восстановление настроек по умолчанию разработчика
```

- Переопределенные условия и условия в коде обработчика **оба действуют одновременно** (AND-семантика); параметры `command` и объявленные разработчиком **глубоко сливаются** (приоритет переопределения)
- `detail_types`: события без `detail_type` разрешаются (не приводят к случайному блокированию неизвестных событий)
- `pattern` / `regex`: события без текста (connect / heartbeat и т.д.) не ограничиваются, сразу разрешаются
- Ключ `master` в переопределении `command` синхронно отображается в хранилище как `must_master`; отключение команды следует через `acl` deny
- **Описание сопоставления ключей**: `overrides.command.set("My", "restart", master=True)` параметр `master` является лишь псевдонимом конфигурации, фактический ключ хранения и ключ возвращаемый `get()` унифицирован как **`must_master`**
  (в `get()` возвращается `{"must_master": true}`) — при проверке во время выполнения читается именно ключ хранения, не следует читать по ключу `master`
- Изменения конфигурации применяются немедленно (горячая перезагрузка), с предупреждениями при проверке формата (неизвестные параметры / битые записи игнорируются)

## Управление цепочкой: присвоение и блокировка

> [!NOTE]
> Параметры `event.done()` / `event.mark_processed()` `claim=` / `stop=` требуют ErisPulse **2.7.1+**.

ErisPulse разделяет понятия "присвоение" и "блокировка" и объединяет их в `event.done()`, что позволяет добавлять слои наблюдения, такие как логирование, аудит и права доступа, вокруг обработки команд.

**Точные определения двух понятий:**

- **Присвоение (claim)**: пометка события как обработанного данным обработчиком (запись в `_processed`). Диспетчер команд видит уже присвоенное событие и **пропускает** его — предотвращает повторную обработку одного и того же сообщения несколькими обработчиками команд. Типичный сценарий: после успешного сопоставления команды присвоить, чтобы диспетчер команд не вмешивался.
- **Блокировка (stop)**: предотвращение распространения события на **менее приоритетные** обработчики (запись в `_propagation_stopped`). Менее приоритетные обработчики (например, `on_message`) больше не увидят это событие. Типичный сценарий: высокоприоритетный обработчик полностью обработал событие, не хочет, чтобы низкоприоритетные обработчики выполнялись.

| `event.done(...)` | Присвоение | Блокировка | Сценарий |
|-------------------|------------|------------|----------|
| `event.done()`    | ✔          | ✔          | Стандартный способ завершения обработки команды / обработчика |
| `event.done(stop=False)` | ✔          | ✘          | Только присвоение: низкоприоритетные обработчики (логирование / статистика) по-прежнему видят |
| `event.done(claim=False)` | ✘          | ✔          | Только блокировка (например, как фаервол / лимитирование), но без дублирования команд |

`event.done(claim=, stop=)` — это синоним `event.mark_processed(claim=, stop=)`, параметры и поведение полностью эквивалентны.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Присвоение + блокировка (стандартный способ завершения обработки команды)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Только присвоение: низкоприоритетные обработчики по-прежнему будут выполняться (логирование / статистика)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Только блокировка: низкоприоритетные обработчики не выполняются, но дублирование не происходит
```

### block-настройка для команд и ответов

**Команда сразу присваивается**: как только сообщение сопоставляется с зарегистрированным именем команды (включая подкоманды / алиасы), независимо от результатов последующих проверок областей или прав доступа, оно будет присвоено и по умолчанию заблокировано для распространения — команды, отклоненные по правам, больше не будут повторно обрабатываться низкоприоритетными обработчиками сообщений (устраняет "повторную обработку сообщения, когда команда отклонена, а on_message срабатывает еще раз").

Блокировку распространения можно отключить, чтобы низкоприоритетные наблюдатели (логирование / аудит / права) все еще могли видеть эти сообщения:

```toml
[ErisPulse.event.command]
block = false   # Командные сообщения продолжают распространяться на низкоприоритетные обработчики (присвоение не затрагивается, дублирование не произойдет)

[ErisPulse.event.wait_reply]
block = false   # Ответы, потребленные wait_reply, продолжают распространяться на низкоприоритетные обработчики
```

> Примечание: `block` контролирует только **блокировку** (stop), не влияет на **присвоение** (claim) —命中 команды никогда не будут повторно потреблены обработчиками сообщений; сообщения, не соответствующие ни одной команде, по-прежнему распространяются на обработчики сообщений.

## Обработка событий уведомлений

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
    await event.reply(f"Добро пожаловать, {user_id}, в группу {group_id}")
```

### Уменьшение участников группы

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Пользователь {user_id} покинул группу {group_id}")
```

## Обработка событий запросов

### Запрос на добавление друга

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Получен запрос на добавление друга: {user_id}, комментарий: {comment}")
    
    # Можно обработать запрос через API адаптера
    # Конкретная реализация см. в документации каждого адаптера
```

### Запрос на групповое приглашение

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
    sdk.logger.info(f"Платформа {platform} подключена")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"Платформа {platform} отключена")
```

### События heartbeat

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"Проверка состояния платформы {platform}")
```

### Запрос состояния бота

После отправки мета-событий адаптером фреймворк автоматически отслеживает состояние бота, и вы можете проверять его в любое время:

```python
from ErisPulse import sdk

# Проверка онлайн-статуса бота
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Бот онлайн")

# Список всех онлайн-ботов
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Получить полную сводку состояния
summary = sdk.adapter.get_status_summary()
```

## Интерактивная обработка

### Использование метода reply для отправки ответа

Метод `event.reply()` поддерживает различные параметры модификации, что упрощает отправку сообщений с упоминаниями, ответами и т.д.:

```python
# Простой ответ
await event.reply("Привет")

# Отправка сообщений различных типов
await event.reply("http://example.com/image.jpg", method="Image")  # изображение
await event.reply("http://example.com/voice.mp3", method="Voice")  # голосовое сообщение

# Упоминание одного пользователя
await event.reply("Привет", at_users=["user123"])

# Упоминание нескольких пользователей
await event.reply("Всем привет", at_users=["user1", "user2", "user3"])

# Ответ на сообщение
await event.reply("Содержание ответа", reply_to="msg_id")

# Упоминание всех участников
await event.reply("Анонс", at_all=True)

# Комбинированный вариант: упоминание пользователя + ответ на сообщение
await event.reply("Содержание", at_users=["user1"], reply_to="msg_id")
```

### Ожидание ответа пользователя

```python
@command("ask", help="Запросить у пользователя")
async def ask_handler(event):
    await event.reply("Введите ваше имя:")
    
    # Ожидание ответа пользователя, таймаут 30 секунд
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")
    else:
        await event.reply("Таймаут ожидания, пожалуйста, повторите ввод.")
```

> [!TIP]
> **Команды остаются доступными во время ожидания** (2.8.3+): сообщения, начинающиеся с префикса команды и соответствующие зарегистрированной команде (например, `/cancel`), будут **выполнены**, а не использованы как ответ, ожидание будет продолжаться — пользователь может в любой момент отменить или переключиться, после выполнения команды ожидание продолжится. Для получения старого поведения "ожидание поглощает весь текст": настройте `ErisPulse.event.wait_reply.cmdpass = true`, или однократно `wait_reply(cmdpass=True)`.

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
        await event.reply("Некорректный ввод или таймаут")
```

### Ожидание ответа с обратным вызовом

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["yes", "y", "是", "确认", "确定", "好", "好的", "ok", "true", "对", "嗯", "行", "同意", "没问题"]:
            await event.reply("Действие подтверждено!")
        else:
            await event.reply("Действие отменено.")
    
    await event.reply("Подтвердите выполнение действия? (Да/Нет)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Подтверждение диалога (confirm)

Ожидание подтверждения или отрицания от пользователя, автоматическое распознавание встроенных слов подтверждения на китайском и английском:

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
@command("choose", help="Выбор")
async def choose_handler(event):
    choice = await event.choose(
        "Выберите цвет:",
        ["красный", "зелёный", "синий"]
    )
    
    if choice is not None:
        colors = ["красный", "зелёный", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
    else:
        await event.reply("Таймаут, выбор не сделан")
```

**Режим объединения**: `merge_prompt=True` объединяет опции в текст сообщения и отправляет одним сообщением с указанным `method`:

```python
# Отправка объединённого текста и опций в Markdown
choice = await event.choose(
    "## Выберите цвет\n{options}\nОтветьте номером",
    ["красный", "зелёный", "синий"],
    method="Markdown",
    merge_prompt=True,
)
```

> Заполнитель `{options}` определяет место вставки опций; если не указан, опции добавляются в конец prompt. Можно настроить через параметр `placeholder` (например, `placeholder="[choices]"`). `options_format="auto"` (по умолчанию) автоматически выбирает стиль в зависимости от `method`: Markdown → маркированный список, Html → нумерованный список, остальные → простой текстовый список. Для текстовых методов (Text/Markdown/Html и т.д.) по умолчанию опции объединяются в конец; для не-текстовых методов (Image и т.д.) по умолчанию опции отправляются отдельным сообщением.

### Сбор формы (collect)

Сбор данных в несколько шагов:

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

Ожидание события, удовлетворяющего условиям, не ограничиваясь одним пользователем:

```python
@command("wait_member", help="Ожидание нового участника")
async def wait_member_handler(event):
    await event.reply("Ожидание добавления участника в группу...")
    
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
            await conv.say("Диалог завершён по таймауту, до свидания!")
            break
        
        text = reply.get_text()
        
        if text == "выход":
            await conv.say("До свидания!")
            break
        
        await conv.say(f"Вы сказали: {text}, продолжайте ввод или ответьте 'выход' для завершения")
```

### Встроенные слова подтверждения

ErisPulse включает в себя набор встроенных слов подтверждения на китайском и английском:

- **Слова подтверждения** (`CONFIRM_YES_WORDS`): yes, y, 是, 确认, 确定, 好, 好的, ok, true, 对, 嗯, 行, 同意, 没问题...
- **Слова отрицания** (`CONFIRM_NO_WORDS`): no, n, 否, 取消, 不, 不要, 不行, cancel, false, 错, 拒绝, 不可以...

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

Помимо встроенных методов, адаптеры платформы регистрируют платформенно-специфические методы, позволяя вам получать доступ к платформенно-специфическим данным.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов платформенно-специфических методов в зависимости от платформы
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram специфичный метод
    elif platform == "email":
        subject = event.get_subject()           # Email специфичный метод
```

Если вы не уверены, зарегистрирован ли для платформы метод, вы можете запросить, какие методы зарегистрированы:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> Список платформенно-специфических методов см. в соответствующей [документации платформы](../platform-guide/)。

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

### 2. Логирование

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
    """Условная обработка — внутри обработчика"""
    # Обрабатываем только сообщения определенного пользователя
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Обрабатываем только сообщения, содержащие определённые ключевые слова
    if "ключевое слово" not in event.get_text():
        return
    
    await event.reply("Условие выполнено, обработка сообщения")
```

## Далее

- [Примеры распространённых задач](common-tasks.md) - Изучите реализацию часто используемых функций (включая продвинутую отправку сообщений: повтор, таймаут, пакетная отправка)
- [Руководство по особенностям платформ](../platform-guide/README.md) - Полное описание Send DSL цепочечной отправки, правил отправки, пакетного построения
- [Подробное объяснение Event обёртки](../developer-guide/modules/event-wrapper.md) - Глубокое изучение объекта Event
- [Руководство пользователя](../user-guide/) - Ознакомьтесь с конфигурацией и управлением модулями