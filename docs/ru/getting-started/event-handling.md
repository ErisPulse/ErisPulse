# Введение в обработку событий

В этом руководстве описывается, как обрабатывать различные типы событий в ErisPulse.

## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | Сценарии применения |
|---------|------|---------|
| Событие сообщения | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Событие команды | Сообщение, начинающееся с префикса команды | Обработка команд, входные точки функций |
| Событие уведомления | Системные уведомления (добавление в друзья, изменения участников группы и т.д.) | Приветственные сообщения, уведомления о статусе |
| Событие запроса | Запросы от пользователей (запрос на добавление в друзья, приглашение в группу) | Автоматическая обработка запросов |
| Метасобытие | Системные события (подключение, сердцебиение) | Мониторинг соединения, проверка статуса |

## Обработка событий сообщений

> **Подсказка**: Рекомендуется использовать аннотацию типа `Event` в обработчиках событий для получения автодополнения в IDE и поддержки проверки типов.

```python
from ErisPulse.Core.Event import Event  # Импорт типа события для аннотации
```

### Слушать все сообщения

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"Получено сообщение от {user_id}: {text}")
```

### Слушать личные сообщения

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"Привет, {user_id}! Это личное сообщение.")
```

### Слушать сообщения группы

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Пользователь {user_id} отправил сообщение в группу {group_id}")
```

### Слушать сообщения с упоминанием (@)

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Получить список упомянутых пользователей
    mentions = event.get_mentions()
    await event.reply(f"Вы упомянули этих пользователей: {mentions}")
```

## Обработка событий команд

### Базовые команды

```python
from ErisPulse.Core.Event import command

@command("help", help="Отображение справки")
async def help_handler(event):
    help_text = """
Доступные команды:
/help - Показать справку
/ping - Проверить соединение
/info - Просмотреть информацию
    """
    await event.reply(help_text)
```

### Алиасы команд

```python
@command(["help", "h"], aliases=["帮助"], help="Отображение справки")
async def help_handler(event):
    await event.reply("Справка...")
```

Пользователи могут использовать любой из следующих способов вызова:
- `/help`
- `/h`
- `/帮助`

### Аргументы команды

```python
@command("echo", help="Эхо сообщения")
async def echo_handler(event):
    # Получить аргументы команды
    args = event.get_command_args()
    
    if not args:
        await event.reply("Пожалуйста, введите сообщение для эха")
    else:
        await event.reply(f"Вы сказали: {' '.join(args)}")
```

### Командные группы

```python
@command("admin.reload", group="admin", help="Перезагрузить модуль")
async def reload_handler(event):
    await event.reply("Модуль перезагружен")

@command("admin.stop", group="admin", help="Остановить бота")
async def stop_handler(event):
    await event.reply("Бот остановлен")
```

### Права команд

```python
def is_master(event):
    """Проверить, является ли пользователь владельцем фреймворка"""
    master_list = ["user123", "user456"]
    return event.get_user_id() in master_list

@command("master", permission=is_master, help="Команда владельца фреймворка")
async def master_handler(event):
    await event.reply("Это команда владельца фреймворка")
```

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

Система событий ErisPulse использует модель планирования **параллельная на одном уровне приоритета, последовательная на разных**:

```
Событие поступает
    ↓
priority=10 группа: [обработчик C || обработчик D] параллельно → объединенный результат
    ↓ (если не прервано)
priority=0 группа: [обработчик A || обработчик B] параллельно → объединенный результат
    ↓
...
```

- **Параллелизм на одном уровне приоритета**: несколько обработчиков с одинаковым приоритетом выполняются одновременно, что увеличивает пропускную способность.
- **Последовательность между уровнями**: группы с разным приоритетом выполняются по порядку (чем больше значение, тем раньше), что гарантирует, что обработчики с высоким приоритетом выполняются первыми.
- **Copy-On-Write**: копии не создаются при отсутствии модификаций обработчиками, что гарантирует нулевые накладные расходы.
- **Обработка конфликтов**: при модификации обработчиками одного и того же поля на одном уровне приоритета используется последнее измененное значение и записывается предупреждение в лог.
- **Механизм прерывания**: после вызова обработчиком `event.mark_processed()` пропускаются последующие группы с более низким приоритетом.

```python
# Пример: параллельное выполнение обработчиков на одном уровне приоритета
@message.on_message(priority=0)
async def handler_a(event):
    # Обработка задачи A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # Выполняется параллельно с handler_a
    event['result_b'] = process_b()

# Последовательное выполнение на разных уровнях приоритета
@message.on_message(priority=10)
async def handler_c(event):
    # Наивысший приоритет, выполняется первым
    pass
```

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

### Увеличение участников группы

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать, новый участник {user_id}, в группу {group_id}")
```

### Уменьшение участников группы

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Участник {user_id} покинул группу {group_id}")
```

## Обработка событий запроса

### Запрос на добавление в друзья

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Получен запрос на добавление в друзья: {user_id}, комментарий: {comment}")
    
    # Запрос можно обработать через API адаптера
    # Конкретная реализация см. документацию для каждого адаптера
```

### Запрос на приглашение в группу

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Получено приглашение в группу {group_id} от {user_id}")
```

## Обработка метасобытий

### Событие подключения

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

### Событие сердцебиения

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"Проверка сердцебиения {platform}")
```

### Запрос статуса бота

После того как адаптер отправляет метасобытие, фреймворк автоматически отслеживает статус бота; вы можете проверить его в любое время:

```python
from ErisPulse import sdk

# Проверить, находится ли определенный бот в сети
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Бот в сети")

# Вывести список всех онлайн-ботов
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Получить сводку полного статуса
summary = sdk.adapter.get_status_summary()
```

## Интерактивная обработка

### Использование метода reply для отправки ответа

Метод `event.reply()` поддерживает различные модифицирующие параметры, что удобно для отправки сообщений с упоминаниями (@), ответами и другими функциями:

```python
# Простая реакция
await event.reply("Привет")

# Отправка сообщений разных типов
await event.reply("http://example.com/image.jpg", method="Image")  # Изображение
await event.reply("http://example.com/voice.mp3", method="Voice")  # Голосовое

# Упоминание одного пользователя
await event.reply("Привет", at_users=["user123"])

# Упоминание нескольких пользователей
await event.reply("Всем привет", at_users=["user1", "user2", "user3"])

# Ответ на сообщение
await event.reply("Текст ответа", reply_to="msg_id")

# Упоминание всех участников
await event.reply("Объявление", at_all=True)

# Комбинированное использование: упоминание пользователя + ответ на сообщение
await event.reply("Содержание", at_users=["user1"], reply_to="msg_id")
```

### Ожидание ответа пользователя

```python
@command("ask", help="Спросить пользователя")
async def ask_handler(event):
    await event.reply("Пожалуйста, введите ваше имя:")
    
    # Ожидать ответа пользователя, тайм-аут 30 секунд
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")
    else:
        await event.reply("Тайм-аут ожидания, пожалуйста, введите снова.")
```

### Ожидание ответа с валидацией

```python
@command("age", help="Спросить о возрасте")
async def age_handler(event):
    def validate_age(event_data):
        """Проверить, что возраст действителен"""
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
        await event.reply("Неверный ввод или тайм-аут")
```

### Ожидание ответа с колбэком

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("Действие подтверждено!")
        else:
            await event.reply("Действие отменено.")
    
    await event.reply("Подтвердить выполнение этого действия? (Да/Нет)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Диалог подтверждения (confirm)

Ожидание подтверждения или отрицания от пользователя, автоматическое распознавание встроенных слов подтверждения на китайском и английском языках:

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    if await event.confirm("Действительно выполнить это действие?"):
        await event.reply("Подтверждено, выполнение...")
    else:
        await event.reply("Отменено")

# Пользовательские слова подтверждения
if await event.confirm("Продолжить?", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### Меню выбора (choose)

Пользователи могут ответить номером варианта или текстом варианта:

```python
@command("choose", help="Выбор")
async def choose_handler(event):
    choice = await event.choose(
        "Пожалуйста, выберите цвет:",
        ["红色", "绿色", "蓝色"]
    )
    
    if choice is not None:
        colors = ["红色", "绿色", "蓝色"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
    else:
        await event.reply("Тайм-аут выбора")
```

**Режим объединения**: когда `merge_prompt=True`, варианты добавляются в сообщение подсказки и отправляются одним сообщением с указанным пользователем `method`:

```python
# Отправить объединенную подсказку + варианты в Markdown
choice = await event.choose(
    "## Пожалуйста, выберите цвет\n{options}\nПожалуйста, введите номер",
    ["红色", "绿色", "蓝色"],
    method="Markdown",
    merge_prompt=True,
)
```

> Заполнитель `{options}` контролирует позицию вставки вариантов; если не указан, они добавляются в конец подсказки.
> Позицию заполнителя можно настроить через параметр `placeholder` (например, `placeholder="[choices]"`).
> `options_format="auto"` (по умолчанию) автоматически выбирает стиль в зависимости от method: Markdown→незамкнутый список, Html→замкнутый список, остальные→простой текстовый список.
> Текстовые методы (Text/Markdown/Html и др.) по умолчанию объединяют варианты в конец; не текстовые методы (Image и др.) по умолчанию разбивают на два сообщения.

### Сбор формы (collect)

Многократный сбор входных данных от пользователя:

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
        await event.reply(f"Регистрация успешна!\nИмя: {data['name']}\nВозраст: {data['age']}\nEmail: {data['email']}")
    else:
        await event.reply("Тайм-аут регистрации или неверный ввод")
```

### Ожидание любого события (wait_for)

Ожидание любого события, удовлетворяющего условию, не ограничиваясь одним пользователем:

```python
@command("wait_member", help="Ожидать нового участника")
async def wait_member_handler(event):
    await event.reply("Ожидание вступления участника в группу...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Добро пожаловать, новый участник: {evt.get_user_id()}")
    else:
        await event.reply("Тайм-аут ожидания")
```

### Многоступенчатый диалог (conversation)

Создание интерактивного контекста многоступенчатого диалога:

```python
@command("survey", help="Опрос")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Добро пожаловать в опрос!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Тайм-аут диалога, пока!")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("Пока!")
            break
        
        await conv.say(f"Вы сказали: {text}, продолжайте вводить или введите '退出' для выхода")
```

### Встроенные слова подтверждения

ErisPulse включает встроенный набор слов подтверждения на китайском и английском языках:

- **Слова подтверждения** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **Слова отрицания** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## Доступ к данным события

### Общие методы объекта Event

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
    
    # Контент сообщения
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

Помимо встроенных методов, адаптеры платформ также регистрируют платформенно-специфичные методы, что упрощает доступ к данным, уникальным для платформы.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов специфичных методов в зависимости от платформы
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Платформенно-специфичный метод Telegram
    elif platform == "email":
        subject = event.get_subject()           # Платформенно-специфичный метод Email
```

Если вы не уверены, зарегистрировала ли платформа определенный метод, вы можете узнать, какие методы зарегистрированы:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> За специфичными для платформы методами, зарегистрированными каждой платформой, обратитесь к соответствующей [документации платформы](../platform-guide/).