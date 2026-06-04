# Введение в обработку событий

Этот гид объясняет, как обрабатывать различные события в ErisPulse.

## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | Сценарии использования |
|---------|------|---------|
| Событие сообщения | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Событие команды | Сообщение, начинающееся с префикса команды | Обработка команд, входные точки функций |
| Событие уведомления | Системные уведомления (добавление в друзья, изменение участников группы и т.д.) | Приветственные сообщения, уведомления о статусе |
| Событие запроса | Запросы от пользователей (запрос на добавление в друзья, приглашение в группу) | Автоматическая обработка запросов |
| Мета-событие | Системные события (подключение, сердцебиение) | Мониторинг соединения, проверка статуса |

## Обработка событий сообщений

> **Совет**: Рекомендуется использовать аннотацию типа `Event` в обработчиках событий для получения поддержки автодополнения в IDE и проверки типов.

```python
from ErisPulse.Core.Event import Event  # Импорт типа события для аннотаций
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

### Слушать групповые сообщения

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Пользователь {user_id} отправил сообщение в группу {group_id}")
```

### Слушать сообщения с упоминанием @

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Получение списка пользователей, которым было отправлено @
    mentions = event.get_mentions()
    await event.reply(f"Вы упомянули этих пользователей: {mentions}")
```

## Обработка событий команд

### Базовые команды

```python
from ErisPulse.Core.Event import command

@command("help", help="Отображает справочную информацию")
async def help_handler(event):
    help_text = """
Доступные команды:
/help - Показать справку
/ping - Проверить соединение
/info - Показать информацию
    """
    await event.reply(help_text)
```

### Алиасы команд

```python
@command(["help", "h"], aliases=["帮助"], help="Отображает справочную информацию")
async def help_handler(event):
    await event.reply("Справочная информация...")
```

Пользователи могут вызвать команду одним из следующих способов:
- `/help`
- `/h`
- `/帮助`

### Аргументы команд

```python
@command("echo", help="Эхо-сообщение")
async def echo_handler(event):
    # Получение аргументов команды
    args = event.get_command_args()
    
    if not args:
        await event.reply("Пожалуйста, введите сообщение для эхо")
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
def is_admin(event):
    """Проверяет, является ли пользователь администратором"""
    admin_list = ["user123", "user456"]
    return event.get_user_id() in admin_list

@command("admin", permission=is_admin, help="Админ-команда")
async def admin_handler(event):
    await event.reply("Это админ-команда")
```

### Приоритет команд

```python
# Чем выше числовое значение, тем раньше выполняется
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("Обработчик с высоким приоритетом")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Обработчик с низким приоритетом")
```

### Параллельная обработка событий

Система событий ErisPulse использует модель планирования **параллельную на одном уровне приоритета, последовательную между уровнями**:

```
Получение события
    ↓
Группа priority=10: [ОбработчикC || ОбработчикD] параллельно → объединенный результат
    ↓ (если не прервано)
Группа priority=0: [ОбработчикA || ОбработчикB] параллельно → объединенный результат
    ↓
...
```

- **Параллельное выполнение на одном уровне приоритета**: Несколько обработчиков с одинаковым приоритетом выполняются одновременно, увеличивая пропускную способность.
- **Последовательное выполнение между уровнями**: Группы с разным приоритетом выполняются по порядку (число больше означает выполнение раньше), чтобы убедиться, что обработчики с высоким приоритетом запускаются первыми.
- **Copy-On-Write**: Копии не создаются, если обработчики не изменяют данные, что обеспечивает нулевую накладную нагрузку.
- **Обработка конфликтов**: Если несколько обработчиков с одинаковым приоритетом изменяют одно и то же поле, используется значение, измененное последним, с записью предупреждения в лог.
- **Механизм прерывания**: После того как любой обработчик вызовет `event.mark_processed()`, выполнение пропускается для последующих групп с низким приоритетом.

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
    await event.reply(f"Участник {user_id} вышел из группы {group_id}")
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
    
    # Запрос можно обработать через API адаптера
    # Конкретную реализацию см. в документации каждого адаптера
```

### Запрос в группу

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

### События пульса (Heartbeat)

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"Проверка пульса для платформы {platform}")
```

### Запрос состояния бота

После того как адаптер отправляет мета-событие, фреймворк автоматически отслеживает статус бота, вы можете запрашивать его в любое время:

```python
from ErisPulse import sdk

# Проверка, находится ли конкретный бот онлайн
if sdk.adapter.is_bot_online("telegram", "123456"):
    await adapter.Send.To("user", "123456").Text("Бот онлайн")

# Список всех онлайн ботов на данный момент
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Получение сводки полного статуса
summary = sdk.adapter.get_status_summary()
```

## Интерактивная обработка

### Отправка ответов с использованием метода reply

Метод `event.reply()` поддерживает множество модификаторов, что удобно для отправки сообщений с упоминаниями (@), ответами и т.д.:

```python
# Простое сообщение
await event.reply("Привет")

# Отправка сообщений разных типов
await event.reply("http://example.com/image.jpg", method="Image")  # Картинка
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

### Ожидание ответа от пользователя

```python
@command("ask", help="Спросить пользователя")
async def ask_handler(event):
    await event.reply("Пожалуйста, введите ваше имя:")
    
    # Ожидание ответа от пользователя, таймаут 30 секунд
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")
    else:
        await event.reply("Время ожидания истекло, пожалуйста, повторите ввод.")
```

### Ожидание ответа с валидацией

```python
@command("age", help="Спросить о возрасте")
async def age_handler(event):
    def validate_age(event_data):
        """Проверка валидности возраста"""
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
        await event.reply(f"Ваш возраст — {age} лет")
    else:
        await event.reply("Ввод недействителен или истекло время ожидания")
```

### Ожидание ответа с обратным вызовом

```python
@command("confirm", help="Подтвердить операцию")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("Операция подтверждена!")
        else:
            await event.reply("Операция отменена.")
    
    await event.reply("Подтвердить выполнение этой операции? (Да/Нет)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Подтверждение диалога (confirm)

Ожидание подтверждения или отрицания от пользователя, автоматическое распознавание встроенных слов подтверждения (китайских и английских):

```python
@command("confirm", help="Подтвердить операцию")
async def confirm_handler(event):
    if await event.confirm("Вы уверены, что хотите выполнить эту операцию?"):
        await event.reply("Подтверждено, выполняем...")
    else:
        await event.reply("Отменено")

# Пользовательские слова подтверждения
if await event.confirm("Продолжить?", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### Выбор из меню (choose)

Пользователь может ввести номер варианта или текст варианта:

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
        await event.reply("Выбор не сделан (истекло время)")
```

### Сбор формы (collect)

Многократный сбор ввода пользователя в несколько шагов:

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
        await event.reply("Время ожидания истекло или ввод недействителен")
```

### Ожидание любого события (wait_for)

Ожидание произвольного события, удовлетворяющего условию, не ограниченное тем же пользователем:

```python
@command("wait_member", help="Ожидание нового участника")
async def wait_member_handler(event):
    await event.reply("Ожидание добавления новых участников в группу...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Добро пожаловать, новый участник: {evt.get_user_id()}")
    else:
        await event.reply("Время ожидания истекло")
```

### Многократный диалог (conversation)

Создание контекста интерактивного многократного диалога:

```python
@command("survey", help="Опрос")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Добро пожаловать в опрос!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Время ожидания диалога истекло, пока!")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("Пока!")
            break
        
        await conv.say(f"Вы сказали: {text}, продолжайте ввод или напишите '退出' для выхода")
```

### Встроенные слова подтверждения

ErisPulse содержит набор встроенных слов подтверждения (китайских и английских):

- **Слова подтверждения** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **Слова отрицания** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## Доступ к данным события

### Общие методы объекта Event

```python
@command("info")
async def info_handler(event):
    # Базовая информация
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # Информация отправителя
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
    
    # Необработанные данные
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

### Расширенные методы платформ

Помимо встроенных методов, платформенные адаптеры регистрируют методы, специфичные для платформы, для удобства доступа к платформенным данным.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов специфичных методов в зависимости от платформы
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Специфичный метод для Telegram
    elif platform == "email":
        subject = event.get_subject()           # Специфичный метод для почты
```

Если вы не уверены, какие методы зарегистрированы для платформы, можно проверить список зарегистрированных методов:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> Специфичные методы, зарегистрированные каждой платформой, см. в соответствующей [документации платформы](../platform-guide/).

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
        # Предусмотренные бизнес-ошибки
        await event.reply(f"Ошибка параметров: {e}")
    except Exception as e:
        # Неожиданные ошибки
        sdk.logger.error(f"Сбой обработки: {e}")
        await event.reply("Сбой обработки, повторите попытку позже")
```

### 2. Логирование

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
    # Обработка только сообщений от конкретных пользователей
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Обработка только сообщений, содержащих определенные ключевые слова
    if "关键词" not in event.get_text():
        return
    
    await event.reply("Условие выполнено, сообщение обработано")
```

## Далее

- [Примеры распространенных задач](common-tasks.md) - Изучение реализации распространенных функций
- [Подробное описание класса Event Wrapper](../developer-guide/modules/event-wrapper.md) - Глубокое понимание объекта Event
- [Руководство для пользователей](../user-guide/) - Настройка и управление модулями