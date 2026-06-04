# API системы событий

В этом документе подробно описывается API системы событий ErisPulse.

## Модуль команд Command

### Регистрация команд

```python
from ErisPulse.Core.Event import command

# Базовая команда
@command("hello", help="Показать приветствие")
async def hello_handler(event):
    await event.reply("Привет!")

# Команда с псевдонимами
@command(["help", "h"], aliases=["помощь"], help="Показать справку")
async def help_handler(event):
    pass

# Команда с правами доступа
def is_admin(event):
    return event.get("user_id") in admin_ids

@command("admin", permission=is_admin, help="Команда администратора")
async def admin_handler(event):
    pass

# Скрытая команда
@command("secret", hidden=True, help="Секретная команда")
async def secret_handler(event):
    pass

# Группа команд
@command("admin.reload", group="admin", help="Перезагрузить модуль")
async def reload_handler(event):
    pass
```

### Информация о командах

```python
# Получить справку по команде
help_text = command.help()

# Получить конкретную команду
cmd_info = command.get_command("admin")

# Получить все команды в группе
admin_commands = command.get_group_commands("admin")

# Получить все видимые команды
visible_commands = command.get_visible_commands()
```

### Ожидание ответа

```python
# Ожидание ответа пользователя
@command("ask", help="Запрос информации у пользователя")
async def ask_command(event):
    reply = await command.wait_reply(
        event,
        prompt="Введите ваше имя:",  # Отправлено выше
        timeout=30.0
    )
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")

# Ожидание ответа с валидацией
def validate_age(event_data):
    try:
        age = int(event_data.get_text())
        return 0 <= age <= 150
    except ValueError:
        return False

@command("age", help="Запросить возраст пользователя")
async def age_command(event):
    await event.reply("Введите ваш возраст:")
    
    reply = await command.wait_reply(
        event,
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"Ваш возраст — {age} лет")

# Ожидание ответа с колбэком
async def handle_confirmation(reply_event):
    text = reply_event.get_text().lower()
    if text in ["да", "yes", "y"]:
        await event.reply("Операция подтверждена!")
    else:
        await event.reply("Операция отменена.")

@command("confirm", help="Подтвердить операцию")
async def confirm_command(event):
    await command.wait_reply(
        event,
        prompt="Введите 'да' или 'нет':",
        callback=handle_confirmation
    )
```

## Модуль сообщений Message

### Событие сообщения

```python
from ErisPulse.Core.Event import message

# Слушать все сообщения
@message.on_message()
async def message_handler(event):
    sdk.logger.info(f"Получено сообщение: {event.get_text()}")

# Слушать личные сообщения
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"Личное сообщение от: {user_id}")

# Слушать сообщения в группах
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    sdk.logger.info(f"Сообщение из группы: {group_id}")

# Слушать сообщения с упоминанием (@)
@message.on_at_message()
async def at_handler(event):
    mentions = event.get_mentions()
    sdk.logger.info(f"Упомянутый пользователь: {mentions}")
```

### Условные слушатели

```python
# Использование приоритета для управления порядком выполнения
@message.on_message(priority=10)  # Чем больше число, тем выше приоритет
async def high_priority_handler(event):
    pass

# Реализация условной фильтрации внутри обработчика
@message.on_message()
async def filtered_handler(event):
    if "ключевое слово" not in event.get_text():
        return
    # Обработка сообщения, содержащего ключевое слово
    pass
```

## Модуль уведомлений Notice

### События уведомлений

```python
from ErisPulse.Core.Event import notice

# Добавление в друзья
@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    await event.reply("Добро пожаловать в друзья!")

# Удаление из друзей
@notice.on_friend_remove()
async def friend_remove_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"Удаление из друзей: {user_id}")

# Увеличение участников группы
@notice.on_group_increase()
async def member_increase_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать, новый участник!")

# Уменьшение участников группы
@notice.on_group_decrease()
async def member_decrease_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"Участник вышел из группы: {user_id}")
```

## Модуль запросов Request

### События запросов

```python
from ErisPulse.Core.Event import request

# Запрос на добавление в друзья
@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    sdk.logger.info(f"Запрос в друзья: {user_id}, примечание: {comment}")

# Запрос на приглашение в группу
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Приглашение в группу: {group_id}, от: {user_id}")
```

## Модуль метасобытий Meta

### Метасобытия

```python
from ErisPulse.Core.Event import meta

# Событие подключения
@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"Платформа {platform} подключена успешно")

# Событие отключения
@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"Платформа {platform} отключена")

# Событие пульса (Heartbeat)
@meta.on_heartbeat()
async def heartbeat_handler(event):
    sdk.logger.debug("Получен пульс")
```

### Запрос статуса бота

После того как адаптер отправляет метасобытие, фреймворк автоматически отслеживает статус бота. Вы можете запросить информацию через менеджер адаптера:

```python
from ErisPulse import sdk

# Получить информацию об одном боте
info = sdk.adapter.get_bot_info("telegram", "123456")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# Вывести список всех ботов
all_bots = sdk.adapter.list_bots()

# Вывести список ботов для указанной платформы
tg_bots = sdk.adapter.list_bots("telegram")

# Проверить, онлайн ли бот
is_online = sdk.adapter.is_bot_online("telegram", "123456")

# Получить сводный статус
summary = sdk.adapter.get_status_summary()
```

Также можно отслеживать онлайн и офлайн статусы бота через события жизненного цикла:

```python
@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(data):
    sdk.logger.info(f"Бот онлайн: {data['platform']}/{data['bot_id']}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    sdk.logger.info(f"Бот офлайн: {data['platform']}/{data['bot_id']}")
```

## Объект-обертка события Event

Обработчики событий модуля Event принимают экземпляр класса-обертки Event, который наследуется от dict и предоставляет удобные методы.

### Основные методы

```python
# Получение информации о событии
event_id = event.get_id()
event_time = event.get_time()
event_type = event.get_type()
detail_type = event.get_detail_type()
platform = event.get_platform()

# Получение информации о боте
self_platform = event.get_self_platform()
self_user_id = event.get_self_user_id()
self_info = event.get_self_info()
```

### Методы сообщений

```python
# Получение содержимого сообщения
message_segments = event.get_message()
alt_message = event.get_alt_message()
text = event.get_text()

# Получение информации об отправителе
user_id = event.get_user_id()
nickname = event.get_user_nickname()
sender = event.get_sender()

# Получение информации о группе
group_id = event.get_group_id()

# Определение типа сообщения
is_msg = event.is_message()
is_private = event.is_private_message()
is_group = event.is_group_message()

# События с упоминанием (@)
is_at = event.is_at_message()
has_mention = event.has_mention()
mentions = event.get_mentions()
```

### Информация о командах

```python
# Получение информации о команде
cmd_name = event.get_command_name()
cmd_args = event.get_command_args()
cmd_raw = event.get_command_raw()

# Проверка, является ли это командой
is_cmd = event.is_command()
```

### Функция ответа

```python
# Базовый ответ
await event.reply("Это сообщение")

# Указать метод отправки
await event.reply("http://example.com/image.jpg", method="Image")

# Ответ с упоминанием пользователя и текстом сообщения
await event.reply("Привет", at_users=["user1"], reply_to="msg_id")

# @all (упоминание всех)
await event.reply("Уведомление", at_all=True)

# Ответ с использованием сегментов сообщений OneBot12
from ErisPulse.Core.Event import MessageBuilder
msg = MessageBuilder().text("Hello").image("url").build()
await event.reply_ob12(msg)

# Ожидание ответа
reply = await event.wait_reply(timeout=30)
```

### Взаимодействующие методы

```python
# confirm — подтверждение диалога
if await event.confirm("Вы уверены, что хотите выполнить это действие?"):
    await event.reply("Подтверждено")
else:
    await event.reply("Отменено")

# Пользовательские слова подтверждения
if await event.confirm("Продолжить?", yes_words={"go", "продолжить"}, no_words={"stop", "стоп"}):
    pass

# choose — выбор из меню
choice = await event.choose("Выберите цвет:", ["красный", "зеленый", "синий"])
if choice is not None:
    colors = ["красный", "зеленый", "синий"]
    await event.reply(f"Вы выбрали: {colors[choice]}")

# collect — сбор формы
data = await event.collect([
    {"key": "name", "prompt": "Введите имя:"},
    {"key": "age", "prompt": "Введите возраст:",
     "validator": lambda e: e.get_text().isdigit()},
])
if data:
    await event.reply(f"Имя: {data['name']}, Возраст: {data['age']}")

# wait_for — ожидание любого события
evt = await event.wait_for(
    event_type="notice",
    condition=lambda e: e.get_detail_type() == "group_member_increase",
    timeout=120
)
if evt:
    await event.reply(f"Новый участник: {evt.get_user_id()}")

# conversation — многоходовой диалог
conv = event.conversation(timeout=60)
await conv.say("Добро пожаловать! Введите 'выход' для завершения.")
while conv.is_active:
    reply = await conv.wait()
    if reply is None or reply.get_text() == "выход":
        conv.stop()
        break
    await conv.say(f"Вы сказали: {reply.get_text()}")
```

### Утилитные методы

```python
# Преобразовать в словарь
event_dict = event.to_dict()

# Проверить, обработано ли событие
if not event.is_processed():
    event.mark_processed()

# Получить исходные данные
raw = event.get_raw()
raw_type = event.get_raw_type()
```

### Расширения платформы

Адаптер может регистрировать платформо-специфичные методы для Event, которые доступны только на экземплярах соответствующей платформы.

#### Пользователь: Использование расширений платформы

Когда адаптер регистрирует платформо-специфичные методы, вы можете вызывать их напрямую в обработчике событий. Методы разных платформ различаются, обратитесь к соответствующей [документации по платформе](../platform-guide/).

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов специфичных методов в зависимости от платформы
    if platform == "email":
        subject = event.get_subject()           # Специфично для почты
        attachments = event.get_attachments()   # Специфично для почты
```

#### Запрос зарегистрированных методов платформы

```python
from ErisPulse.Core.Event import get_platform_event_methods

# Просмотр методов, зарегистрированных для платформы
methods = get_platform_event_methods("email")
# ["get_subject", "get_from", "get_attachments", ...]

# Динамическое определение и вызов
for method_name in get_platform_event_methods(event.get_platform()):
    method = getattr(event, method_name)
    print(f"{method_name}: {method()}")
```

#### Изоляция платформенных методов

Методы, зарегистрированные для разных платформ, не мешают друг другу:

```python
# Событие почты — только методы почты
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello"
event.get_chat_type()    # ❌ AttributeError

# Событие Telegram — только методы Telegram
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private"
event.get_subject()      # ❌ AttributeError
```

#### Поддержка hasattr / dir

```python
hasattr(event, "get_subject")   # Возвращает True только если platform="email"
"get_subject" in dir(event)     # То же самое
```

### Адаптер: Регистрация расширений платформы

Адаптер может регистрировать платформо-специфичные методы для Event с помощью декораторов. Первый параметр метода