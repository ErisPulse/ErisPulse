# Введение в обработку событий

В этом руководстве рассказывается о том, как обрабатывать различные типы событий в ErisPulse.

## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | Применение |
|---------|------|---------|
| Сообщение | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Команда | Сообщение, начинающееся с префикса команды | Обработка команд, вход в функции |
| Уведомление | Системные уведомления (добавление друзей, изменения участников группы и т.д.) | Приветственные сообщения, уведомления о статусе |
| Запрос | Запросы пользователей (запросы на добавление в друзья, приглашения в группу) | Автоматическая обработка запросов |
| Мета-событие | Системные события (подключение, heartbeat) | Мониторинг подключения, проверка статуса |

## Обработка событий сообщений

> **Примечание**: Рекомендуется использовать аннотацию типа `Event` в обработчиках событий для поддержки автодополнения и проверки типов в IDE.

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
    await event.reply(f"Вы упомянули этих пользователей: {mentions}")
```

## Обработка командных событий

### Базовая команда

```python
from ErisPulse.Core.Event import command

@command("help", help="Отображает справочную информацию")
async def help_handler(event):
    help_text = """
Доступные команды:
/help - Отображает справку
/ping - Тестирование подключения
/info - Просмотр информации
    """
    await event.reply(help_text)
```

### Псевдонимы команд

```python
@command(["help", "h"], aliases=["помощь"], help="Отображает справочную информацию")
async def help_handler(event):
    await event.reply("Справочная информация...")
```

Пользователь может вызвать команду любым из следующих способов:
- `/help`
- `/h`
- `/помощь`

### Командные параметры

```python
@command("echo", help="Повторяет сообщение")
async def echo_handler(event):
    # Получение параметров команды
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите сообщение для повторения")
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

### Командные права доступа

```python
def is_admin(event):
    """Проверка, является ли пользователь администратором"""
    admin_list = ["user123", "user456"]
    return event.get_user_id() in admin_list

@command("admin", permission=is_admin, help="Команды администратора")
async def admin_handler(event):
    await event.reply("Это команда администратора")
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

Система событий ErisPulse использует модель планирования **параллельной обработки с одинаковым приоритетом и последовательной обработки с разным приоритетом**:

```
Событие поступило
    ↓
Группа с приоритетом=10: [Обработчик C || Обработчик D] параллельно → объединение результатов
    ↓ (если не прервано)
Группа с приоритетом=0: [Обработчик A || Обработчик B] параллельно → объединение результатов
    ↓
...
```

- **Параллельная обработка с одинаковым приоритетом**: Обработчики с одинаковым приоритетом выполняются одновременно, что повышает пропускную способность
- **Последовательная обработка с разным приоритетом**: Группы с разным приоритетом выполняются последовательно (чем больше значение приоритета, тем раньше он выполняется), обеспечивая выполнение обработчиков с высоким приоритетом первыми
- **Copy-On-Write**: Обработчики не создают копии, если не вносят изменения, что обеспечивает нулевые накладные расходы
- **Обработка конфликтов**: При изменении одного и того же поля несколькими обработчиками с одинаковым приоритетом используется последнее значение и записывается предупреждение в лог
- **Механизм прерывания**: При вызове `event.mark_processed()` любым обработчиком пропускаются последующие группы с низким приоритетом

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
    await event.reply(f"Добро пожаловать, {nickname}! Добавлены в друзья.")
```

### Увеличение числа участников группы

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать, {user_id}, в группу {group_id}")
```

### Уменьшение числа участников группы

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"{user_id} покинул группу {group_id}")
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
    # Конкретная реализация см. в документации каждого адаптера
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
    sdk.logger.info(f"Подключение к платформе {platform}")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"Отключение от платформы {platform}")
```

### События heartbeat

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"Проверка подключения к платформе {platform}")
```

### Запрос статуса бота

После отправки мета-события адаптером, фреймворк автоматически отслеживает статус бота, и вы можете в любой момент запросить его:

```python
from ErisPulse import sdk

# Проверка, онлайн ли бот
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Бот в сети")

# Вывод списка всех онлайн ботов
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Получение полного сводного отчета статуса
summary = sdk.adapter.get_status_summary()
```

## Интерактивная обработка

### Использование метода reply для отправки ответа

Метод `event.reply()` поддерживает различные параметры для удобной отправки сообщений с упоминаниями, ответами и т.д.:

```python
# Простой ответ
await event.reply("Привет")

# Отправка различных типов сообщений
await event.reply("http://example.com/image.jpg", method="Image")  # Изображение
await event.reply("http://example.com/voice.mp3", method="Voice")  # Голосовое сообщение

# Упоминание одного пользователя
await event.reply("Привет", at_users=["user123"])

# Упоминание нескольких пользователей
await event.reply("Привет всем", at_users=["user1", "user2", "user3"])

# Ответ на сообщение
await event.reply("Ответ", reply_to="msg_id")

# Упоминание всех участников
await event.reply("Объявление", at_all=True)

# Комбинирование: упоминание пользователей + ответ на сообщение
await event.reply("Сообщение", at_users=["user1"], reply_to="msg_id")
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
        await event.reply("Таймаут ожидания, повторите ввод.")
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
        
        if text in ["yes", "y", "yes", "y"]:
            await event.reply("Действие подтверждено!")
        else:
            await event.reply("Действие отменено.")
    
    await event.reply("Подтвердите выполнение действия? (yes/no)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Подтверждение диалога (confirm)

Ожидание подтверждения или отрицания от пользователя, автоматически распознаются встроенные английские и китайские слова подтверждения:

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    if await event.confirm("Вы действительно хотите выполнить это действие?"):
        await event.reply("Подтверждено, выполняется...")
    else:
        await event.reply("Отменено")

# Пользовательские слова подтверждения
if await event.confirm("Продолжить?", yes_words={"go", "continue"}, no_words={"stop", "stop"}):
    pass
```

### Выбор из меню (choose)

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

### Сбор формы (collect)

Многошаговый сбор пользовательского ввода:

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

Ожидание события, соответствующего заданным условиям, не ограничено одним пользователем:

```python
@command("wait_member", help="Ожидание нового участника")
async def wait_member_handler(event):
    await event.reply("Ожидание нового участника в группу...")
    
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
        
        await conv.say(f"Вы сказали: {text}, продолжайте ввод или ответьте 'выход' для завершения")
```

### Встроенные слова подтверждения

ErisPulse включает в себя набор встроенных английских и китайских слов подтверждения:

- **Слова подтверждения** (`CONFIRM_YES_WORDS`): yes, y, yes, y, confirm, confirm, ok, ok, true, true, right, right, agree, agree, no problem, no problem, etc.
- **Слова отрицания** (`CONFIRM_NO_WORDS`): no, n, no, n, cancel, cancel, no, no, don't, don't, no, no, cancel, cancel, false, false, wrong, wrong, refuse, refuse, not allowed, not allowed, etc.

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

### Платформенно-специфичные методы

Помимо встроенных методов, адаптеры платформы также регистрируют платформенно-специфичные методы, что позволяет вам получать доступ к платформенно-специфичным данным.

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

Если вы не уверены, зарегистрирован ли метод для платформы, вы можете проверить, какие методы зарегистрированы для платформы:

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
    
    # Использование собственного логгера модуля
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Детальная отладочная информация")
```

### 3. Условная обработка

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Условная обработка - проверка внутри обработчика"""
    # Обрабатывать только сообщения определенных пользователей
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Обрабатывать только сообщения, содержащие определенные ключевые слова
    if "ключевое слово" not in event.get_text():
        return
    
    await event.reply("Условие выполнено, обработка сообщения")
```

## Далее

- [Примеры распространенных задач](common-tasks.md) - Узнайте, как реализовать часто используемые функции (включая продвинутую отправку сообщений: повторы/таймауты/массовую отправку)
- [Руководство по особенностям платформ](../platform-guide/README.md) - Полное описание Send DSL цепной отправки, правил отправки, массового построения
- [Подробное объяснение Event-обертки](../developer-guide/modules/event-wrapper.md) - Глубокое понимание объекта Event
- [Руководство для пользователей](../user-guide/) - Узнайте о настройке и управлении модулями