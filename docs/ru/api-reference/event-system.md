# API системы событий

В этой документации подробно описывается API системы событий ErisPulse.

## Модуль команд Command

### Регистрация команд

```python
from ErisPulse.Core.Event import command

# Базовая команда
@command("hello", help="Отправить приветствие")
async def hello_handler(event):
    await event.reply("Привет!")

# Команда с псевдонимами
@command(["help", "h"], aliases=["помощь"], help="Показать справку")
async def help_handler(event):
    pass

# Команда с проверкой прав доступа
def is_admin(event):
    return event.get("user_id") in admin_ids

@command("admin", permission=is_admin, help="Команда для администраторов")
async def admin_handler(event):
    pass

# Скрытая команда
@command("secret", hidden=True, help="Секретная команда")
async def secret_handler(event):
    pass

# Командная группа
@command("admin.reload", group="admin", help="Перезагрузить модуль")
async def reload_handler(event):
    pass
```

### Информация о командах

```python
# Получить справку по команде
help_text = command.help()

# Получить информацию о конкретной команде
cmd_info = command.get_command("admin")

# Получить все команды из группы
admin_commands = command.get_group_commands("admin")

# Получить все видимые команды
visible_commands = command.get_visible_commands()
```

### Ожидание ответа

```python
# Ожидание ответа от пользователя
@command("ask", help="Запросить информацию о пользователе")
async def ask_command(event):
    reply = await command.wait_reply(
        event,
        prompt="Пожалуйста, введите ваше имя:",  # Отправлено выше
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
    await event.reply("Пожалуйста, введите ваш возраст:")
    
    reply = await command.wait_reply(
        event,
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"Ваш возраст: {age} лет")

# Ожидание ответа с обратным вызовом
async def handle_confirmation(reply_event):
    text = reply_event.get_text().lower()
    if text in ["да", "yes", "y"]:
        await event.reply("Действие подтверждено!")
    else:
        await event.reply("Действие отменено.")

@command("confirm", help="Подтвердить действие")
async def confirm_command(event):
    await command.wait_reply(
        event,
        prompt="Пожалуйста, введите 'да' или 'нет':",
        callback=handle_confirmation
    )
```

## Модуль сообщений Message

### События сообщений

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

# Слушать групповые сообщения
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    sdk.logger.info(f"Групповое сообщение от: {group_id}")

# Слушать @упоминания
@message.on_at_message()
async def at_handler(event):
    mentions = event.get_mentions()
    sdk.logger.info(f"Упомянутый пользователь: {mentions}")
```

### Условный прослушиватель

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
    # Обработка сообщений, содержащих ключевое слово
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
    sdk.logger.info(f"Удаление друга: {user_id}")

# Участие в группе
@notice.on_group_increase()
async def member_increase_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать, новый участник!")

# Выход из группы
@notice.on_group_decrease()
async def member_decrease_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"Участник вышел из группы: {user_id}")
```

## Модуль запросов Request

### События запросов

```python
from ErisPulse.Core.Event import request

# Запросы на добавление в друзья
@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    sdk.logger.info(f"Запрос на добавление в друзья: {user_id}, комментарий: {comment}")

# Запросы на приглашение в группу
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

# Событие сердечного импульса
@meta.on_heartbeat()
async def heartbeat_handler(event):
    sdk.logger.debug("Получен сердечный импульс")
```

### Запрос статуса бота

После того как адаптер отправляет метасобытие, фреймворк автоматически отслеживает статус бота. Ссылайтесь на [API системы адаптера - управление статусом бота](adapter-system.md#bot-状态管理), чтобы узнать об API запроса статуса и событиях жизненного цикла.

## Класс-обертка Event

Обработчики событий модуля Event принимают экземпляр класса-обертки Event, который наследуется от dict и предоставляет удобные методы.

### Основные методы

```python
# Получить информацию о событии
event_id = event.get_id()
event_time = event.get_time()
event_type = event.get_type()
detail_type = event.get_detail_type()
platform = event.get_platform()

# Получить информацию о боте
self_platform = event.get_self_platform()
self_user_id = event.get_self_user_id()
self_info = event.get_self_info()
```

### Идентификаторы сессии

```python
# Унифицированный ID цели: для групп возвращает group_id, для личных — user_id и т. д.
target_id = event.get_target_id()

# Уникальный идентификатор сессии, формат: {platform}:{detail_type}:{target_id}
session_id = event.get_session_id()
# Пример: "telegram:private:12345", "qq:group:67890"
```

`get_target_id()` возвращает первое непустое значение в следующем порядке: `group_id` → `channel_id` → `guild_id` → `thread_id` → `user_id`. Подходит для сценариев, требующих унифицированной идентификации сессии, таких как управление контекстом и хранение состояния.

### Методы сообщений

```python
# Получить содержимое сообщения
message_segments = event.get_message()
alt_message = event.get_alt_message()
text = event.get_text()

# Получить информацию об отправителе
user_id = event.get_user_id()
nickname = event.get_user_nickname()
sender = event.get_sender()

# Получить информацию о группе
group_id = event.get_group_id()

# Определить тип сообщения
is_msg = event.is_message()
is_private = event.is_private_message()
is_group = event.is_group_message()

# Связано с @упоминаниями
is_at = event.is_at_message()
has_mention = event.has_mention()
mentions = event.get_mentions()
```

### Информация о командах

```python
# Получить информацию о команде
cmd_name = event.get_command_name()
cmd_args = event.get_command_args()
cmd_raw = event.get_command_raw()

# Проверить, является ли событие командой
is_cmd = event.is_command()
```

### Функции ответа

```python
# Базовый ответ
await event.reply("Это сообщение")

# Указать метод отправки
await event.reply("http://example.com/image.jpg", method="Image")

# Ответ с @пользователем и ссылка на сообщение
await event.reply("Привет", at_users=["user1"], reply_to="msg_id")

# @всем членам
await event.reply("Объявление", at_all=True)

# Ответ с использованием сегментов сообщений OneBot12
from ErisPulse.Core.Event import MessageBuilder
msg = MessageBuilder().text("Hello").image("url").build()
await event.reply_ob12(msg)

# Ожидание ответа
reply = await event.wait_reply(timeout=30)
```

### Запрос возможностей платформы

```python
# Проверить, поддерживает ли текущая платформа определенный метод отправки
if event.supports("Image"):
    await event.reply(url, method="Image")

# Вывести все доступные методы отправки на текущей платформе
methods = event.available_methods()
# ["Text", "Image", "Voice", ...]
```

### Методы ответа

Метод `reply()` поддерживает указание типа отправки через параметр `method`, а также два удобных булевых параметра:

```python
# Простой текстовый ответ
await event.reply("Привет")

# Ответ и @отправителя
await event.reply("Привет", at_sender=True)

# Ответ и цитирование текущего сообщения
await event.reply("Получено", reply_to_message=True)

# Комбинированное использование
await event.reply("Получено", at_sender=True, reply_to_message=True)

# Отправка изображения (с использованием параметра method)
if event.supports("Image"):
    await event.reply("http://example.com/img.jpg", method="Image")
else:
    await event.reply("[Изображение] http://example.com/img.jpg")
```

**Описание параметров**：

| Параметр | Тип | Описание |
|------|------|------|
| `content` | str | Содержимое для отправки |
| `method` | str | Метод отправки, по умолчанию "Text", можно выбрать "Image"/"Voice"/"Video"/"File" и др. |
| `at_sender` | bool | @упомянуть отправителя (автоматическое извлечение user_id) |
| `quote` | bool | Цитировать ответ на текущее сообщение (автоматическое извлечение message_id) |
| `at_users` | list[str] | Список пользователей для @упоминания |
| `reply_to` | str | Ручное указание ID сообщения для ответа |
| `at_all` | bool | @упомянуть всех участников |

### Методы взаимодействия

```python
# confirm — подтверждение диалога (возвращает True/False/None)
if await event.confirm("Вы уверены, что хотите выполнить это действие?"):
    await event.reply("Подтверждено")

# Отправка подтверждения через метод, отличный от Text
if await event.confirm("http://example.com/image.jpg", method="Image"):
    await event.reply("Подтверждено изображение")

# choose — выбор из меню (возвращает индекс опции или None)
choice = await event.choose("Пожалуйста, выберите цвет:", ["красный", "зеленый", "синий"])

# options_format="auto" (по умолчанию) автоматически выбирает стиль в зависимости от method:
# Markdown→неупорядоченный список (- 1. опция), Html→упорядоченный список (<ol>), другие→простой текстовый список
# Методы текстового типа (Markdown/Html и др.) по умолчанию объединяют опции в конце
# merge_prompt=True может принудительно объединить любой method; placeholder можно настроить
choice = await event.choose(
    "## Пожалуйста, выберите\n{options}", ["A", "B"],
    method="Markdown", merge_prompt=True,
)

# collect — сбор формы (возвращает словарь {key: value} или None)
data = await event.collect([
    {"key": "name", "prompt": "Введите имя:"},
    {"key": "age", "prompt": "Введите возраст:",
     "validator": lambda e: e.get_text().isdigit()},
    {"key": "avatar", "prompt": "Отправьте аватар:", "method": "Image"},
])

# wait_for — ожидание любого события, удовлетворяющего условию
evt = await event.wait_for(event_type="notice", condition=lambda e: ..., timeout=120)

# conversation — контекст многоходового диалога
conv = event.conversation(timeout=60)
await conv.say("Добро пожаловать!")
```

> Более подробное описание параметров и дополнительные примеры см. в разделе [Подробное описание класса-обертки Event](../developer-guide/modules/event-wrapper.md) и [Многоходовой диалог Conversation](../advanced/conversation.md).

### Вспомогательные методы

```python
# Преобразовать в словарь
event_dict = event.to_dict()

# Проверить, был ли обработан
if not event.is_processed():
    event.mark_processed()

# Получить исходные данные
raw = event.get_raw()
raw_type = event.get_raw_type()
```

### Методы расширения платформы

Адаптеры могут регистрировать платформенно-специфичные методы для Event, которые будут доступны только на экземплярах соответствующей платформы.

#### Пользователь: использование методов расширения платформы

После того как адаптер зарегистрировал платформенно-специфичные методы, вы можете вызывать их напрямую в обработчиках событий. Методы для разных платформ различаются, обратитесь к соответствующей [документации по платформе](../platform-guide/).

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов специфичных методов в зависимости от платформы
    if platform == "email":
        subject = event.get_subject()           # Платформа email
        attachments = event.get_attachments()   # Платформа email
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

#### Изоляция методов платформы

Методы, зарегистрированные на разных платформах, не мешают друг другу:

```python
# Событие email — доступны только методы email
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello"
event.get_chat_type()    # ❌ AttributeError

# Событие Telegram — доступны только методы Telegram
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private"
event.get_subject()      # ❌ AttributeError
```

#### Поддержка hasattr / dir

```python
hasattr(event, "get_subject")   # Возвращает True только при platform="email"
"get_subject" in dir(event)     # То же самое
```

### Адаптер: регистрация методов расширения платформы

Адаптеры могут регистрировать платформенно-специфичные методы для Event через декораторы; первым параметром метода является `self` (экземпляр Event), что позволяет свободно обращаться к данным события.

#### Регистрация одного метода

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("email")
def get_subject(self):
    """Получить тему письма"""
    return self.get("email_raw", {}).get("subject", "")

@register_event_method("email")
def get_from(self):
    """Получить отправителя"""
    return self.get("email_raw", {}).get("from", {})
```

#### Пакетная регистрация (класс Mixin)

При наличии множества методов рекомендуется использовать класс Mixin для пакетной регистрации:

```python
from ErisPulse.Core.Event import register_event_mixin

class EmailEventMixin:
    def get_subject(self):
        return self.get("email_raw", {}).get("subject", "")

    def get_from(self):
        return self.get("email_raw", {}).get("from", {})

    def get_attachments(self):
        return self.get("email_raw", {}).get("attachments", [])

# Регистрация всех методов сразу
register_event_mixin("email", EmailEventMixin)
```

#### Спецификация возвращаемых значений

| Сценарий | Возвращаемое значение | Способ использования пользователем |
|------|--------|------------|
| Возврат данных (текст, словарь и т. д.) | Прямое возвращаемое значение | `subject = event.get_subject()` |
| Выполнение операций (отправка сообщений и т. д.) | Возвращает `asyncio.Task` | `task = event.do_something()` можно опционально `await` |

> **Рекомендация**. Для методов, не возвращающих данные, следует возвращать `asyncio.Task`, чтобы пользователь мог самостоятельно решить, нужно ли использовать `await`; даже без `await` операция будет выполнена.

```python
@register_event_method("email")
def forward_email(self, to_address: str):
    """Переслать письмо — возвращает Task, пользователь может сам решить, нужно ли await"""
    import asyncio
    return asyncio.create_task(
        self._do_forward(to_address)
    )

# Пользователь может использовать await для ожидания результата
await event.forward_email("user@example.com")

# Можно и не await, операция будет выполнена в фоне
event.forward_email("user@example.com")
```

#### Отмена регистрации метода

```python
from ErisPulse.Core.Event import unregister_event_method, unregister_platform_event_methods

# Отмена регистрации одного метода
unregister_event_method("email", "get_subject")

# Отмена регистрации всех методов для платформы (вызывается при выключении адаптера)
unregister_platform_event_methods("email")
```

#### Переопределение встроенных методов

`register_event_mixin` / `register_event_method` поддерживают переопределение встроенных методов Event (таких как `confirm`、`choose`、`collect`、`wait_reply`、`reply` и др.). Регистрируемые платформенные методы имеют приоритет над встроенными методами благодаря `Event.__getattribute__`, поэтому адаптеры могут предоставлять специфичные для платформы реализации взаимодействия.

Встроенная реализация экспортируется как функция `_builtin_*`, переопределяющая сторона может вызывать их как резервный вариант:

```python
from ErisPulse.Core.Event import register_event_mixin, _builtin_choose

class YunhuEventMixin:
    async def choose(self, prompt, options, timeout=60, method="Text"):
        # Платформа Yunhu использует компоненты кнопок
        buttons = [[{"text": opt} for opt in options]]
        await self.reply(prompt)
        # ...ожидание обратного вызова кнопок или текстового ответа...
        # Резервная логика
        return await _builtin_choose(self, None, options, timeout, "Text")

register_event_mixin("yunhu", YunhuEventMixin)
```

## Расширение для нескольких платформ (шаблонные символы)

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве названия платформы; методы, зарегистрированные таким образом, будут доступны на всех экземплярах Event. Подходит для функциональных модулей, требующих многократного использования на разных платформах, таких как диалоги AI и управление контекстом.

### Регистрация методов для нескольких платформ

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    """self — экземпляр Event, можно свободно обращаться к данным события и встроенным методам"""
    await self.reply(f"AI: {prompt}")
```

После регистрации все обработчики событий на всех платформах смогут вызывать этот метод:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handler(event):
    await event.ai_chat(event.get_text())
```

### Приоритет разрешения методов

При доступе к методам Event через свойства порядок разрешения следующий:

1. **Платформенно-специфичные методы** (переопределение для текущей платформы)
2. **Методы шаблона** (методы, зарегистрированные для `"*"`)
3. **Встроенные методы** (`reply`、`confirm` и др.)
4. **Доступ по ключам словаря**

> Таким образом, методы шаблона могут переопределять встроенные методы (например, `reply`), но будут снова переопределены платформенно-специфичными методами с тем же именем.

## Система приоритетов

Обработчики событий поддерживают приоритеты; чем больше значение, тем выше приоритет:

```python
# Обработчик с высоким приоритетом выполняется первым
@message.on_message(priority=10)
async def high_priority_handler(event):
    pass

# Обработчик с низким приоритетом выполняется позже
@message.on_message(priority=0)
async def low_priority_handler(event):
    pass
```

## Связанные документы

- [API основных модулей](core-modules.md) - API основных модулей
- [API системы адаптера](adapter-system.md) - API управления адаптерами
- [Руководство по разработке модулей](../developer-guide/modules/) - Разработка пользовательских модулей