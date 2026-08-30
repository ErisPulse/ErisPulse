# Введение в обработку событий

В этом руководстве описывается, как обрабатывать различные типы событий в ErisPulse.

Пожалуйста, верните полный перевод Markdown без дополнительных слов.


## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | 适用场景 |
|---------|------|---------|
| Событие сообщения | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Событие команды | Сообщение, начинающееся с префикса команды | Обработка команд, точка входа функций |
| Событие уведомления | Системные уведомления (добавление друга, изменения в группе и т. д.) | Приветственные сообщения, уведомления о статусе |
| Событие запроса | Запросы пользователей (запрос на добавление в друзья, приглашение в группу) | Автоматическая обработка запросов |
| Метасобытие | Системные события (подключение, сердцебиение) | Мониторинг соединения, проверка статуса |

## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | 适用场景 |
|---------|------|---------|
| Событие сообщения | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Событие команды | Сообщение, начинающееся с префикса команды | Обработка команд, точка входа функций |
| Событие уведомления | Системные уведомления (добавление друга, изменения в группе и т. д.) | Приветственные сообщения, уведомления о статусе |
| Событие запроса | Запросы пользователей (запрос на добавление в друзья, приглашение в группу) | Автоматическая обработка запросов |
| Метасобытие | Системные события (подключение, сердцебиение) | Мониторинг соединения, проверка статуса |

## Обработка сообщений о событиях

> **Примечание**: Рекомендуется использовать аннотацию типа `Event` в обработчиках событий для получения поддержки автодополнения в IDE и проверки типов.

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

### Отслеживание сообщений в группах

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Пользователь {user_id} отправил сообщение в группе {group_id}")
```

### Отслеживание сообщений с упоминаниями (@)

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Получение списка пользователей, которых упомянули
    mentions = event.get_mentions()
    await event.reply(f"Вы упомянули этих пользователей: {mentions}")

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

### Псевдонимы команд

```python
@command(["help", "h"], aliases=["帮助"], help="Отображает справочную информацию")
async def help_handler(event):
    await event.reply("Справочная информация...")
```

Пользователи могут вызывать команду следующими способами:
- `/help`
- `/h`
- `/帮助`

### Параметры команд

```python
@command("echo", help="Повторяет сообщение")
async def echo_handler(event):
    # Получение параметров команды
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите сообщение для повтора")
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

### Права доступа к командам

```python
def is_master(event):
    """Проверяет, является ли пользователь владельцем фреймворка"""
    master_list = ["user123", "user456"]
    return event.get_user_id() in master_list

@command("master", permission=is_master, help="Команда владельца фреймворка")
async def master_handler(event):
    await event.reply("Это команда владельца фреймворка")
```

### Приоритеты команд

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

Система событий ErisPulse использует модель планирования **параллельной обработки с одинаковым приоритетом и последовательной обработки с разным приоритетом**:

```
Событие поступило
    ↓
Группа priority=10: [Обработчик C || Обработчик D] параллельно → объединить результаты
    ↓ (если не прервано)
Группа priority=0: [Обработчик A || Обработчик B] параллельно → объединить результаты
    ↓
...
```

- **Параллельная обработка с одинаковым приоритетом**: Несколько обработчиков с одинаковым приоритетом выполняются одновременно, что увеличивает пропускную способность
- **Последовательная обработка с разным приоритетом**: Группы с разным приоритетом выполняются последовательно (чем выше значение, тем раньше выполняется), обеспечивая выполнение обработчиков высокого приоритета первыми
- **Copy-On-Write**: Обработчики не создают копии, если не вносят изменения, что обеспечивает нулевые накладные расходы
- **Обработка конфликтов**: При изменении одного и того же поля несколькими обработчиками с одинаковым приоритетом используется последнее значение и записывается предупреждающее сообщение в лог
- **Механизм прерывания**: После вызова любого обработчиком `event.done()` (по умолчанию) или `event.done(claim=False)` пропускаются последующие группы с более низким приоритетом. Разница между "признанием" и "блокировкой" описана в разделе [**Управление цепочкой: признание и блокировка**](#управление-цепочкой-признание-и-блокировка)

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
    # Самый высокий приоритет, выполняется первым
    pass
```

> **Ограничение параллелизма**: Все соответствующие handler-ы немедленно создают задачи, но ограничиваются сигналом, ограничивающим **количество одновременно выполняемых задач** по умолчанию **64** (`ErisPulse.framework.handler_max_concurrency`, поддерживает горячее обновление). Задачи, превышающие лимит, ожидают в очереди на сигнале, пока предыдущие не завершатся. Во время пиковых нагрузок это ваш «сброс давления».
>
> **Медленные логи**: Если один обработчик выполняется более **1 секунды**, фреймворк записывает предупреждение в лог (`handler_slow`). Время ожидания ответа (`wait_reply`) исключается из времени выполнения, чтобы не ошибочно помечать ожидание ответа как медленное.

## Фильтрация области видимости: почему мой модуль не получает сообщения

Рассылка событий выполняется **до создания задачи обработчика** — сначала производится фильтрация области видимости, определяется `scope.is_allowed` на основе владельца модуля (уровень сессии > уровень бота > уровень платформы), **если проверка не пройдена, обработка происходит молча**, без ошибок и ответа.

```python
# Предположим, в config.toml MyModule был заблокирован в определённой группе:
[ErisPulse.scope]
block = { yunhu = { group_123 = ["MyModule"] } }
```

В этом случае, когда сообщения приходят из этой группы, **ни команды, ни обработчики событий MyModule не будут запущены**. Это не ошибка, а работа механизма области видимости — при диагностике "модуль не реагирует" сначала проверяйте привязку области видимости.

- Три уровня фильтрации: уровень шины адаптера (до создания задачи), уровень модуля события (внутри каждой группы приоритетов), уровень команды (до проверки прав)
- Журнал фильтрации доступен только на уровне **TRACE** (`core.scope.denied`), на уровне INFO по умолчанию никаких следов не видно
- Обработчики на уровне фреймворка (например, диспетчер команд с `scope_exempt=True`) не подвержены влиянию области видимости

> Подробнее о трёх уровнях привязки области видимости, белом и чёрном списках, приоритетах перекрытия и скрытом механизме отклонения по умолчанию см. в [Системе области видимости](../../advanced/scope.md).

[**中文**](docs/ru/quick-start.md)

## Управление цепочкой: присвоение и блокировка

> [!NOTE]
> Параметры `claim=` / `stop=` для `event.done()` / `event.mark_processed()` требуют ErisPulse **2.7.1+**.

ErisPulse разделяет два ортогональных семантических понятия — «присвоение» и «блокировка» — и объединяет их управление через `event.done()`, что позволяет добавлять слои наблюдения (например, логирование, аудит, права доступа) вокруг обработки команд.

**Точные определения двух понятий:**

- **Присвоение (claim)**: пометка того, что событие было обработано данным обработчиком (запись в `_processed`). Командный диспетчер, увидев присвоенное событие, **пропускает его повторную обработку** — предотвращая повторную обработку одного и того же сообщения несколькими обработчиками команд. Типичный сценарий: после успешного сопоставления команды присвоить событие, чтобы диспетчер команд больше не вмешивался.
- **Блокировка (stop)**: предотвращение распространения события к обработчикам с **меньшим приоритетом** (запись в `_propagation_stopped`). Обработчики с низким приоритетом (например, `on_message`) больше не увидят это событие. Типичный сценарий: высокоприоритетный обработчик уже полностью обработал событие, и не хочет, чтобы низкоприоритетные обработчики выполнялись.

| `event.done(...)` | Присвоение | Блокировка | Сценарий |
|-------------------|-----------|------------|----------|
| `event.done()` | ✔ | ✔ | Стандартная практика после обработки команды / обработчика |
| `event.done(stop=False)` | ✔ | ✘ | Только присвоение: низкоприоритетные наблюдатели (логирование / статистика) продолжают видеть событие |
| `event.done(claim=False)` | ✘ | ✔ | Только блокировка (например, фаервол / ограничение скорости), но без дедупликации команд |

`event.done(claim=, stop=)` — это псевдоним `event.mark_processed(claim=, stop=)`, и параметры и поведение у них полностью идентичны.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Присвоение + блокировка (стандартная практика после обработки команды)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Только присвоение: низкоприоритетный обработчик все еще будет выполняться (логирование / статистика)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Только блокировка: низкоприоритетный обработчик не будет выполняться, но дедупликация не происходит
```

### Конфигурация block для команд и ответов

После успешного сопоставления команды или после сопоставления ответа в `wait_reply` по умолчанию распространение блокируется (для обратной совместимости). Можно настроить разрешение, чтобы низкоприоритетные обработчики (логирование / аудит / права доступа) также могли наблюдать эти сообщения:

```toml
[ErisPulse.event.command]
block = false   # Сообщения команд продолжают поступать к обработчикам с низким приоритетом

[ErisPulse.event.wait_reply]
block = false   # Ответы, потребленные wait_reply, продолжают поступать к обработчикам с низким приоритетом

## Обработка событий уведомлений

### Добавление в друзья

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "Новый друг"
    await event.reply(f"Добро пожаловать в друзья, {nickname}!")
```

### Приглашение участника в группу

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать, новый участник {user_id}, в группу {group_id}")
```

### Покидание участником группы

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Участник {user_id} покинул группу {group_id}")

## Обработка событий запроса

### Запросы на добавление в друзья

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Получен запрос на добавление в друзья: {user_id}, Комментарий: {comment}")
    
    # Запрос можно обработать через адаптер API
    # Смотрите документацию по конкретным адаптерам для деталей реализации
```

### Запросы на вступление в группу

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Получен запрос на вступление в группу {group_id} от пользователя {user_id}")

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

### Событие сердечного импульса

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} проверка сердечного импульса")
```

### Запрос статуса бота

После того как адаптер отправляет мета-событие, фреймворк автоматически отслеживает статус бота, вы можете проверить его в любое время:

```python
from ErisPulse import sdk

# Проверить, работает ли определенный бот
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Бот онлайн")

# Вывести список всех текущих активных ботов
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Получить сводку полного статуса
summary = sdk.adapter.get_status_summary()

## Интерактивная обработка

### Отправка ответа с использованием метода reply

Метод `event.reply()` поддерживает множество модификаторов, удобных для отправки сообщений с упоминаниями (@), ответами на другие сообщения и другими функциями:

```python
# Простой ответ
await event.reply("Привет")

# Отправка сообщений разных типов
await event.reply("http://example.com/image.jpg", method="Image")  # Изображение
await event.reply("http://example.com/voice.mp3", method="Voice")  # Голосовое сообщение

# Упоминание одного пользователя
await event.reply("Привет", at_users=["user123"])

# Упоминание нескольких пользователей
await event.reply("Всем привет", at_users=["user1", "user2", "user3"])

# Ответ на сообщение
await event.reply("Текст ответа", reply_to="msg_id")

# Упоминание всех участников группы
await event.reply("Уведомление", at_all=True)

# Комбинированное использование: упоминание пользователя + ответ на сообщение
await event.reply("Текст сообщения", at_users=["user1"], reply_to="msg_id")
```

### Ожидание ответа пользователя

```python
@command("ask", help="Спросить пользователя")
async def ask_handler(event):
    await event.reply("Введите ваше имя:")
    
    # Ожидание ответа пользователя, таймаут 30 секунд
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")
    else:
        await event.reply("Время ожидания истекло, пожалуйста, введите еще раз.")
```

### Ожидание ответа с проверкой (validation)

```python
@command("age", help="Запросить возраст")
async def age_handler(event):
    def validate_age(event_data):
        """Проверка, что возраст корректный"""
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
        await event.reply(f"Ваш возраст {age} лет")
    else:
        await event.reply("Ввод недействителен или истек таймаут")
```

### Ожидание ответа с обратным вызовом (callback)

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["Да", "yes", "y"]:
            await event.reply("Действие подтверждено!")
        else:
            await event.reply("Действие отменено.")
    
    await event.reply("Подтвердить выполнение этой операции? (Да/Нет)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Подтверждение диалога (confirm)

Ожидание подтверждения или отказа от пользователем, автоматическое распознавание встроенных слов подтверждения на китайском и английском языках:

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    if await event.confirm("Вы уверены, что хотите выполнить это действие?"):
        await event.reply("Подтверждено, выполняем...")
    else:
        await event.reply("Отменено")

# Пользовательские слова подтверждения
if await event.confirm("Продолжить?", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### Меню выбора (choose)

Пользователь может ответить номером опции или текстом опции:

```python
@command("choose", help="Выбор")
async def choose_handler(event):
    choice = await event.choose(
        "Пожалуйста, выберите цвет:",
        ["Красный", "Зеленый", "Синий"]
    )
    
    if choice is not None:
        colors = ["Красный", "Зеленый", "Синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
    else:
        await event.reply("Время ожидания истекло, выбор не сделан")
```

**Режим объединения**: при `merge_prompt=True` опции объединяются в сообщение приглашения и отправляются одним сообщением с использованием указанного пользователем метода `method`:

```python
# Отправка объединенного приглашения + опций с использованием Markdown
choice = await event.choose(
    "## Пожалуйста, выберите цвет\n{options}\nПожалуйста, ответьте номером",
    ["Красный", "Зеленый", "Синий"],
    method="Markdown",
    merge_prompt=True,
)
```

> Заполнитель `{options}` управляет положением вставки опций; если не указан, они добавляются в конец приглашения.
> Можно настроить заполнитель через параметр `placeholder` (например, `placeholder="[choices]"`).
> `options_format="auto"` (по умолчанию) автоматически выбирает стиль в зависимости от метода: Markdown→неупорядоченный список, Html→упорядоченный список, остальные→простой текстовый список.
> Текстовые методы (Text/Markdown/Html и т.д.) по умолчанию объединяют опции в конец; не текстовые методы (Image и т.д.) по умолчанию разбивают их на два сообщения.

### Сбор формы (collect)

Многошаговый сбор ввода пользователя:

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
        await event.reply("Время ожидания истекло или ввод недействителен")
```

### Ожидание любого события (wait_for)

Ожидание произвольного события, удовлетворяющего условию, не ограничиваясь одним и тем же пользователем:

```python
@command("wait_member", help="Ожидание нового участника")
async def wait_member_handler(event):
    await event.reply("Ожидание вступления новых участников группы...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Добро пожаловать новому участнику: {evt.get_user_id()}")
    else:
        await event.reply("Время ожидания истекло")
```

### Многоразовый диалог (conversation)

Создание контекста интерактивного многоразового диалога:

```python
@command("survey", help="Анкетирование")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Добро пожаловать в опрос!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Время ожидания истекло, пока!")
            break
        
        text = reply.get_text()
        
        if text == "Выйти":
            await conv.say("До свидания!")
            break
        
        await conv.say(f"Вы сказали: {text}, продолжайте ввод или ответьте 'Выйти', чтобы закончить")
```

### Встроенные слова подтверждения

ErisPulse содержит наборы слов подтверждения на китайском и английском языках:

- **Слова подтверждения** (`CONFIRM_YES_WORDS`): Да, yes, y, подтверждено, точно, хорошо, ок, true, да, м, хорошо, согласен, без проблем...
- **Слова отрицания** (`CONFIRM_NO_WORDS`): Нет, no, n, отменено, не, не нужно, нельзя, cancel, false, ошибка, отказ, нельзя...

## Доступ к событийным данным

### Общие методы объекта Event

```python
@command("info")
async def info_handler(event):
    # Базовая информация
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # Информация об отправителе
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # Контекст сообщения
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

### Расширенные методы платформ

Помимо встроенных методов, адаптеры различных платформ также регистрируют методы, уникальные для каждой платформы, чтобы упростить доступ к специфичным данным платформ.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов специфичных методов в зависимости от платформы
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Метод, уникальный для Telegram
    elif platform == "email":
        subject = event.get_subject()           # Метод, уникальный для электронной почты
```

Если вы не уверены, какие методы были зарегистрированы определенной платформой, вы можете проверить список зарегистрированных методов для конкретной платформы:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> За дополнительной информацией о методах, специфичных для платформ, обратитесь к соответствующей [документации платформы](../platform-guide/).

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
        await event.reply(f"Ошибка параметров: {e}")
    except Exception as e:
        # Неожиданная ошибка
        sdk.logger.error(f"Сбой обработки: {e}")
        await event.reply("Ошибка обработки, попробуйте позже")
```

### 2. Логирование

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"Обработка сообщения: {user_id} - {text}")
    
    # Использовать собственный логгер модуля
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Подробная информация для отладки")
```

### 3. Условная обработка

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Условная обработка - определение внутри обработчика"""
    # Обрабатывать только сообщения от определенных пользователей
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Обрабатывать только сообщения, содержащие определенные ключевые слова
    if "ключевое слово" not in event.get_text():
        return
    
    await event.reply("Условие выполнено, сообщение обработано")

## Следующие шаги

- [Примеры типовых задач](common-tasks.md) - Изучение реализации распространенных функций (включая расширенную отправку сообщений: повторные попытки/тайм-ауты/пачки)
- [Руководство по возможностям платформы](../platform-guide/README.md) - Полное описание Send DSL цепочной отправки, правил отправки и построения пакетов
- [Подробное описание класса-обертки Event](../developer-guide/modules/event-wrapper.md) - Глубокое понимание объекта Event
- [Руководство пользователя](../user-guide/) - Узнайте о настройке и управлении модулями