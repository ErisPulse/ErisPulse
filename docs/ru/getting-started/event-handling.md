# Введение в обработку событий

В этом руководстве рассказывается о том, как обрабатывать различные типы событий в ErisPulse.

## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | Применение |
|---------|------|---------|
| Событие сообщения | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Событие команды | Сообщение, начинающееся с префикса команды | Обработка команд, точка входа |
| Событие уведомления | Системные уведомления (добавление в друзья, изменения участников группы и т.д.) | Приветствия, уведомления о состоянии |
| Событие запроса | Запросы пользователей (запросы на добавление в друзья, приглашения в группы) | Автоматическая обработка запросов |
| Событие мета | Системные события (подключение, сердцебиение) | Мониторинг подключения, проверка состояния |

## Обработка событий сообщений

> **Примечание**: Рекомендуется использовать аннотацию типа `Event` в обработчиках событий, чтобы получить поддержку автодополнения и проверки типов в IDE.

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
    sdk.logger.info(f"Пользователь {user_id} отправил сообщение в группу {group_id}")
```

### Отслеживание сообщений с упоминанием

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Получение списка упомянутых пользователей
    mentions = event.get_mentions()
    await event.reply(f"Вы упомянули следующих пользователей: {mentions}")
```

### Отслеживание с помощью подстановок и регулярных выражений

Четыре декоратора сообщений (`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`) поддерживают `pattern` (подстановочные знаки glob) и `regex` (регулярные выражения), сообщения, которые не соответствуют этим условиям, **не будут запускать** обработчики:

```python
# Подстановочные знаки glob: * - любая последовательность, ? - один символ, [seq] - набор символов
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("Успешная регистрация")

# Регулярное выражение: соответствует сумме
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

### Базовые команды

```python
from ErisPulse.Core.Event import command

@command("help", help="Отображает справочную информацию")
async def help_handler(event):
    help_text = """
Доступные команды:
/help - Отображает справку
/ping - Тест подключения
/info - Просмотр информации
    """
    await event.reply(help_text)
```

### Синонимы команд

```python
@command(["help", "h"], aliases=["帮助"], help="Отображает справочную информацию")
async def help_handler(event):
    await event.reply("Справочная информация...")
```

Пользователь может вызвать команду любым из следующих способов:
- `/help`
- `/h`
- `/帮助`

### Параметры команд

```python
@command("echo", help="Возвращает сообщение")
async def echo_handler(event):
    # Получение параметров команды
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите сообщение для повторения")
    else:
        await event.reply(f"Вы сказали: {' '.join(args)}")
```

### Группы команд

```python
@command("admin.reload", group="admin", help="Перезагрузить модуль")
async def reload_handler(event):
    await event.reply("Модуль перезагружен")

@command("admin.stop", group="admin", help="Остановить бота")
async def stop_handler(event):
    await event.reply("Бот остановлен")
```

### Права доступа и управление доступом

Права доступа к командам разделены на три уровня, проверка происходит по уровням сверху вниз (если верхний уровень отклоняет, нижние уровни не проверяются):

```python
# ① ACL команды (настройка со стороны пользователя): по белому и черному списку пользователей, при отклонении возвращается "Недостаточно прав"
# ② master=True — только владелец фреймворка может выполнять (фреймворк автоматически проверяет, при отклонении возвращается "Недостаточно прав")
@command("restart", master=True, help="Перезапустить модуль")
async def restart_handler(event):
    await event.reply("Модуль перезапущен")

# ③ permission=функция вызова — логика управления доступом к команде (возвращает True для выполнения)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Панель управления")
async def panel_handler(event):
    await event.reply("Добро пожаловать на панель управления")
```

**ACL команды** (в интерфейсе управления `ErisPulse.scope.commands`): пользователь может настроить белый и черный список для любой команды, имя команды поддерживает точное и подстановочные совпадения (например, `"roll*"`), при отклонении возвращается "Недостаточно прав":

```toml
# config.toml — разрешить выполнение restart только для 123456; 666 всегда отклонять
[ErisPulse.scope.commands.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Порядок проверки: если `deny` совпадает → отклонить; если `allow` не пуст и не совпадает → отклонить; в противном случае передать разработчику по умолчанию (`master=True` / `permission`). Интерфейс управления во время выполнения (поддержка подстановок по имени команды):

```python
from ErisPulse import sdk
sdk.scope.allow_user("restart", "onebot11", "123456")   # белый список
sdk.scope.deny_user("restart", "onebot11", "666")       # черный список
sdk.scope.remove_acl("restart")                          # очистить белый и черный список
sdk.scope.get_acl("restart")                             # получить текущий список
```

**Уровень доступа на уровне событий** (для конкретного человека / группы / бота, получает ли сообщение) — идет через **уровень идентификации** интерфейса управления (`scope.identity`); **уровень доступности модуля** (какие модули могут использоваться) — идет через **уровень модуля** интерфейса управления (`scope.platforms / bots / sessions`). Подробнее см. [Единый интерфейс управления](../advanced/scope.md).

> Рекомендуется: использовать `master=True` / `permission` для команд, требующих взаимодействия с бизнес-логикой; использовать уровень идентификации интерфейса управления для доступа по пользователю / группе; использовать уровень модуля интерфейса управления для контроля доступности модуля.

### Приоритет команд

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

Система событий ErisPulse использует модель **параллельной обработки с одинаковым приоритетом и последовательной обработки с разным приоритетом**:

```
Событие приходит
    ↓
Группа с приоритетом 10: [Обработчик C || Обработчик D] параллельно → объединить результаты
    ↓ (если не прервано)
Группа с приоритетом 0: [Обработчик A || Обработчик B] параллельно → объединить результаты
    ↓
...
```

- **Параллельная обработка с одинаковым приоритетом**: обработчики с одинаковым приоритетом выполняются одновременно, повышая пропускную способность
- **Последовательная обработка с разным приоритетом**: группы с разным приоритетом выполняются последовательно (чем больше значение приоритета, тем раньше выполняется), обеспечивая выполнение обработчиков с высоким приоритетом первыми
- **Copy-On-Write**: обработчики не создают копию, если не изменяют данные, обеспечивая нулевые накладные расходы
- **Обработка конфликтов**: при изменении одного и того же поля несколькими обработчиками с одинаковым приоритетом используется последнее значение и записывается предупреждение в лог
- **Механизм прерывания**: после вызова `event.done()` (по умолчанию) или `event.done(claim=False)` любым обработчиком, пропускаются последующие группы с более низким приоритетом. Разница между присвоением и блокировкой описана ниже в разделе [Управление цепочкой: присвоение и блокировка](#управление-цепочкой-присвоение-и-блокировка)

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

# Последовательное выполнение с разным приоритетом
@message.on_message(priority=10)
async def handler_c(event):
    # Приоритет самый высокий, выполняется первым
    pass
```

> **Ограничение параллелизма**: все соответствующие обработчики задач немедленно создаются, но ограничиваются сигналом, ограничивающим **количество одновременно выполняемых задач** по умолчанию **64** (`ErisPulse.framework.handler_max_concurrency`, поддерживает горячую перезагрузку). Задачи, превышающие лимит, ждут в очереди на сигнале, пока предыдущие не завершатся. Во время пиковых нагрузок это ваш "сброс давления".
>
> **Медленные логи**: если одиночный обработчик занимает более **1 секунды**, фреймворк записывает предупреждение в лог (`handler_slow`). Время ожидания `wait_reply` исключается из времени выполнения, чтобы не ошибаться в "ожидании ответа".

## Фильтрация через интерфейс управления: почему мой модуль не получает сообщения

После поступления события есть две **тихие** фильтрации (ни один не отвечает, не генерирует ошибку):

1. **Уровень идентификации** (`ErisPulse.scope.identity`): при входе события в точку распределения, определяется, получит ли событие пользователь > группа > бот > адаптер. Отклоненные **все события** просто отбрасываются, и никакие обработчики (включая диспетчер команд) не запускаются.
2. **Уровень модуля** (`ErisPulse.scope`): когда событие достигает обработчика или команды модуля, определяется, доступен ли этот модуль, по сессии > боту > платформе, **если не проходит, тихо пропускается**.

```toml
# Пример 1: все сообщения в определенной группе не распространяются
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Пример 2: отключить MyModule для определенного бота
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

В этом случае, когда сообщение из этой группы поступает, обработчики команд и событий `MyModule` **не будут вызваны**. Это не ошибка, а механизм фильтрации — при диагностике "модуль не реагирует" сначала проверьте привязку идентификации и модуля в интерфейсе управления.

- Логи фильтрации видны только на уровне **TRACE** (`core.scope.identity_denied` / `core.scope.denied`), по умолчанию на уровне INFO ничего не видно
- Обработчики на уровне фреймворка (например, диспетчер команд `scope_exempt=True`) не подвержены влиянию **уровня модуля**, но подвержены влиянию **уровня идентификации** (все событие уже отброшено)
- Перед выполнением команды есть еще один фильтр: ACL команды (при отклонении возвращается "Недостаточно прав", см. предыдущий раздел)

> Пять уровней конфигурации, синтаксис совпадения, API во время выполнения см. в [Едином интерфейсе управления](../../advanced/scope.md).

## Управление цепочкой: присвоение и блокировка

> **Примечание**
> Параметры `claim=` / `stop=` в `event.done()` / `event.mark_processed()` требуют ErisPulse **2.7.1+**.

ErisPulse разделяет два семантически ортогональных понятия: "присвоение" и "блокировка", объединяя их через `event.done()`, что удобно для добавления слоев наблюдения, таких как логирование, аудит, права доступа, вокруг обработки команд.

**Точное определение двух понятий:**

- **Присвоение (claim)**: пометка события как обработанного данным обработчиком (запись в `_processed`). Диспетчер команд, увидевший уже присвоенное событие, **пропустит** повторную обработку — предотвращая повторное выполнение одного и того же сообщения несколькими обработчиками команд. Типичный сценарий: после успешного сопоставления команды присвоить, чтобы диспетчер команд больше не вмешивался.
- **Блокировка (stop)**: предотвращение распространения события **на обработчики с более низким приоритетом** (запись в `_propagation_stopped`). Обработчики с более низким приоритетом (например, `on_message`) больше не увидят это событие. Типичный сценарий: высокоприоритетный обработчик полностью обработал событие, и не хочет, чтобы низкоприоритетные обработчики выполнялись снова.

| `event.done(...)` | Присвоение | Блокировка | Сценарий |
|-------------------|------------|------------|----------|
| `event.done()` | ✔ | ✔ | Стандартная практика для завершения обработки команды / обработчика |
| `event.done(stop=False)` | ✔ | ✘ | Только присвоение: низкоприоритетные обработчики (логирование / статистика) по-прежнему увидят |
| `event.done(claim=False)` | ✘ | ✔ | Только блокировка (например, брандмауэр / ограничение скорости), но без удаления повторной обработки |

`event.done(claim=, stop=)` — это псевдоним `event.mark_processed(claim=, stop=)`, параметры и поведение полностью эквивалентны.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Присвоение + блокировка (стандартная практика для завершения обработки команды)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Только присвоение: низкоприоритетные обработчики по-прежнему будут выполняться (логирование / статистика)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Только блокировка: низкоприоритетные обработчики не выполняются, но без удаления повторной обработки
```

### Конфигурация block для команд и ответов

После успешного сопоставления команды или после `wait_reply` блокируется распространение (для обратной совместимости). Можно разрешить низкоприоритетным обработчикам (логирование / аудит / права) наблюдать эти сообщения:

```toml
[ErisPulse.event.command]
block = false   # Сообщения команд продолжают распространяться на низкоприоритетные обработчики

[ErisPulse.event.wait_reply]
block = false   # Ответы, потребленные wait_reply, продолжают распространяться на низкоприоритетные обработчики
```

## Обработка событий уведомлений

### Добавление в друзья

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "Новый друг"
    await event.reply(f"Добро пожаловать, {nickname}! Добавьте меня в друзья.")
```

### Увеличение участников группы

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать, {user_id}! Добро пожаловать в группу {group_id}.")
```

### Уменьшение участников группы

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"{user_id} покинул группу {group_id}.")
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
    
    # Можно обработать запрос через API адаптера
    # Конкретная реализация см. в документации адаптеров
```

### Запрос на приглашение в группу

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Получено приглашение в группу {group_id} от {user_id}.")
```

## Обработка мета-событий

### События подключения

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"Подключение к платформе {platform}")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"Отключение от платформы {platform}")
```

### События сердцебиения

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"Проверка сердцебиения для платформы {platform}")
```

### Запрос состояния бота

После отправки мета-события адаптером, фреймворк автоматически отслеживает состояние бота, и вы можете в любое время проверить:

```python
from ErisPulse import sdk

# Проверка, онлайн ли бот
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Бот онлайн")

# Получение списка всех онлайн ботов
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Получение полного сводного состояния
summary = sdk.adapter.get_status_summary()
```

## Интерактивная обработка

### Использование метода reply для отправки ответов

Метод `event.reply()` поддерживает различные параметры, удобные для отправки сообщений с упоминанием, ответом и т.д.:

```python
# Простой ответ
await event.reply("Привет")

# Отправка различных типов сообщений
await event.reply("http://example.com/image.jpg", method="Image")  # Изображение
await event.reply("http://example.com/voice.mp3", method="Voice")  # Голосовое сообщение

# Упоминание одного пользователя
await event.reply("Привет", at_users=["user123"])

# Упоминание нескольких пользователей
await event.reply("Всем привет", at_users=["user1", "user2", "user3"])

# Ответ на сообщение
await event.reply("Содержание ответа", reply_to="msg_id")

# Упоминание всех участников
await event.reply("Объявление", at_all=True)

# Комбинированное использование: упоминание пользователей + ответ на сообщение
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
        
        if text in ["yes", "y", "是", "确认"]:
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

Ожидание подтверждения или отрицания пользователя, автоматически распознаются встроенные подтверждения на китайском и английском языках:

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    if await event.confirm("Вы уверены, что хотите выполнить это действие?"):
        await event.reply("Подтверждено, выполняется...")
    else:
        await event.reply("Отменено")

# Пользовательские подтверждения
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
        ["красный", "зеленый", "синий"]
    )
    
    if choice is not None:
        colors = ["красный", "зеленый", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
    else:
        await event.reply("Таймаут выбора")
```

**Режим объединения:** `merge_prompt=True` объединяет опции в текст сообщения и отправляет все одним сообщением с указанным `method`:

```python
# Отправка объединенного сообщения в формате Markdown
choice = await event.choose(
    "## Выберите цвет\n{options}\nПожалуйста, введите номер",
    ["красный", "зеленый", "синий"],
    method="Markdown",
    merge_prompt=True,
)
```

> Заполнитель `{options}` контролирует положение вставки опций; если не указан, опции добавляются в конец текста. Можно использовать параметр `placeholder` для настройки заполнителя (например, `placeholder="[выборы]"`). `options_format="auto"` (по умолчанию) автоматически выбирает стиль в зависимости от метода: Markdown → маркированный список, Html → нумерованный список, остальные → текстовый список. Для текстовых методов (Text/Markdown/Html и др.) по умолчанию опции объединяются в конец; для не-текстовых методов (Image и др.) по умолчанию опции отправляются раздельно.

### Сбор формы (collect)

Многошаговый сбор данных от пользователя:

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
        await event.reply("Регистрация завершилась таймаутом или некорректным вводом")
```

### Ожидание произвольного события (wait_for)

Ожидание события, соответствующего заданным условиям, не ограничиваясь одним пользователем:

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
        await event.reply(f"Добро пожаловать, {evt.get_user_id()}!")
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
        
        await conv.say(f"Вы сказали: {text}, продолжайте или введите 'выход' для завершения")
```

### Встроенные подтверждения

ErisPulse включает в себя набор встроенных подтверждений на китайском и английском языках:

- **Подтверждения** (`CONFIRM_YES_WORDS`): да, yes, y, подтвердить, определить, хорошо, хорошо, ok, true, правильно, м-м, хорошо, согласиться, нет проблем...
- **Отрицания** (`CONFIRM_NO_WORDS`): нет, no, n, отменить, не, не нужно, нет, отменить, false, неправильно, отказать, нельзя...

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
    
    # Содержание сообщения
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
    
    # Платформа
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

### Методы расширения платформы

Помимо встроенных методов, адаптеры платформы также регистрируют платформенно-специфические методы, что позволяет вам получать доступ к специфическим данным платформы.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов платформенно-специфических методов в зависимости от платформы
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram специфический метод
    elif platform == "email":
        subject = event.get_subject()           # Email специфический метод
```

Если вы не уверены, зарегистрирован ли метод для определенной платформы, вы можете проверить, какие методы зарегистрированы для платформы:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> Платформенно-специфические методы см. в соответствующей [документации платформы](../platform-guide/).

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
        await event.reply("Обработка не удалась, попробуйте позже")
```

### 2. Логирование

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
    """Условная обработка — внутри обработчика"""
    # Обрабатывать только сообщения определенных пользователей
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Обрабатывать только сообщения, содержащие определенные ключевые слова
    if "ключевое слово" not in event.get_text():
        return
    
    await event.reply("Условие выполнено, обработка сообщения")
```

## Далее

- [Примеры распространенных задач](common-tasks.md) - Узнайте, как реализовать распространенные функции (включая продвинутую отправку сообщений: повторы/таймауты/пакетную отправку)
- [Руководство по особенностям платформы](../platform-guide/README.md) - Полное описание Send DSL цепного отправки, правил отправки, пакетного построения
- [Подробное объяснение Event-обертки](../developer-guide/modules/event-wrapper.md) - Глубокое понимание объекта Event
- [Руководство пользователя](../user-guide/) - Ознакомьтесь с настройкой и управлением модулями