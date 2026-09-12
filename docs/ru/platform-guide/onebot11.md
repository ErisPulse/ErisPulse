# Документация по функциям платформы OneBot11

OneBot11Adapter — это адаптер, построенный на основе протокола OneBot V11.

---

## Информация о документации

- Версия соответствующего модуля: 4.3.0
- Ответственный: ErisPulse

## Основная информация

- Краткое описание платформы: OneBot — это стандарт интерфейса приложений для чат-ботов
- Название адаптера: OneBotAdapter
- Поддерживаемые версии протокола/API: OneBot V11
- Поддержка нескольких аккаунтов: По умолчанию используется архитектура с несколькими аккаунтами, поддерживается одновременная настройка и запуск нескольких аккаунтов OneBot
- Ключ конфигурации: `OneBotAdapter`

## Обновление парадигмы v5 (4.3.0)

Адаптер был обновлен до соответствия парадигме v5 (постепенное обновление, совместимость API):

- **Наследование BaseConverter**: Общие поля конвертера (id/time/platform/self/raw) создаются с помощью build_base_event фреймворка, и перекрываются именами полей OB11 (echo/time/self_id)
- **Принадлежность задачи spawn_background**: Задача подключения в режиме Client теперь использует runtime.spawn_background (принадлежность owner, автоматическая утилизация при завершении)
- **Мягкая зависимость от фреймворка**: При установке адаптера больше не требуется жесткая зависимость от ErisPulse, что предотвращает изменение версии фреймворка при разрешении pip; во время выполнения проверяется ErisPulse>=2.7.1, и при низкой версии выводится предупреждение в лог
- **Журнал версии при запуске**: При инициализации выводится сообщение "OneBotAdapter v4.3.0 loaded"

Существующие возможности (поддержка с 4.2.0): поддержка нескольких аккаунтов, стандартное сопоставление действий Api DSL (get_self_info→get_login_info и т.д.), Request DSL (одобрение/отклонение запросов от друзей/групп: event.approve() / event.reject()), EventMixin, i18n.

---

## Стандартные действия API (DSL API)

Адаптер автоматически сопоставляет стандартные имена действий OneBot12 с именами действий OB11, что позволяет модулям использовать единый интерфейс для всех платформ:

| Стандартное действие OB12 | Действие OB11 | Описание |
|--------------------------|---------------|----------|
| get_self_info | get_login_info | Поля стандартизированы: user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | Поля стандартизированы |
| delete_message | delete_msg | Отправка сообщения |
| leave_group | set_group_leave | Выход из группы |
| get_friend_list | get_friend_list | Имя действия совпадает, вызов прозрачно передается |
| get_group_info | get_group_info | Имя действия совпадает, вызов прозрачно передается |
| upload_file | upload_group_file / upload_private_file | Дополнительные необязательные параметры group_id/user_id, filetype автоматически определяет тип и перенаправляет на upload_group_file |

### Базовое использование

```python
from ErisPulse import sdk
onebot = sdk.adapter.get("onebot11")

# Получение информации о боте
result = await onebot.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# Отправка сообщения
await onebot.Api.delete_message(message_id=123456)

# Загрузка файла в группу (filetype автоматически определяет тип и перенаправляет на upload_group_file)
result = await onebot.Api.upload_file(group_id=123456, file="/path/to/file.zip")

# Указание аккаунта (множественные аккаунты)
result = await onebot.Api.Using("main").get_self_info()

# Несопоставленные действия OB11 вызываются через call() (универсальный метод для расширений, таких как NapCat/Lagrange)
result = await onebot.Api.call("send_poke", group_id=123, user_id=456)
```

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:

```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Отправка с использованием аккаунта по умолчанию
await onebot.Send.To("group", group_id).Text("Hello World!")

# Отправка с указанием конкретного аккаунта
await onebot.Send.Using("main").To("group", group_id).Text("Сообщение от основного аккаунта")

# Цепочка модификаторов: @пользователь + ответ
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Ответ на сообщение")

# @всех участников
await onebot.Send.To("group", group_id).AtAll().Text("Анонс")
```

### Основные методы отправки

- `.Text(text: str)` — отправка текстового сообщения.
- `.Image(file: Union[str, bytes], filename: str = "image.png")` — отправка изображения (поддерживает URL, Base64 или bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")` — отправка голосового сообщения.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` — отправка видео.
- `.Face(id: Union[str, int])` — отправка эмодзи QQ.
- `.File(file: Union[str, bytes], filename: str = "file.dat")` — отправка файла (тип определяется автоматически).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12 (автоматически преобразуется в OB11).
- `.Recall(message_id: Union[str, int])` — отмена отправки сообщения.

### Методы управления группой

Методы, требующие указания группы через `To("group", group_id)`, позволяют выполнять операции в контексте группы:

- `.Kick(user_id, reject_add_request=False)` — исключение участника из группы.
- `.Ban(user_id, duration=1800)` — временный запрет участнику отправлять сообщения (в секундах), 0 — разблокировка.
- `.WholeBan(enable=True)` — включение/отключение запрета всем участникам отправлять сообщения.
- `.SetAdmin(user_id, enable=True)` — назначение/снятие роли администратора.
- `.SetCard(user_id, card="")` — изменение отображаемого имени участника.
- `.SetGroupName(name)` — изменение названия группы.
- `.Leave(is_dismiss=False)` — выход из группы (группа может быть распущена только администратором).
- `.SetTitle(user_id, title="")` — установка титула участника.
- `.SetPortrait(file)` — установка аватара группы.

### Методы запросов

- `.GetMsg(message_id)` — получение содержания сообщения.
- `.GetForwardMsg(id)` — получение объединённого сообщения.
- `.GetLoginInfo()` — получение информации о текущем аккаунте.
- `.GetFriendList()` — получение списка друзей.
- `.GetGroupInfo()` — получение информации о группе (требует `To("group", group_id)`).
- `.GetGroupList()` — получение списка групп.
- `.GetGroupMemberInfo(user_id)` — получение информации о участнике группы (требует `To("group", group_id)`).
- `.GetGroupMemberList()` — получение списка участников группы (требует `To("group", group_id)`).

### Методы для работы с друзьями

- `.Like(user_id, times=1)` — отправка лайка другу (максимум 10 раз).

### Методы цепочечных модификаторов (можно комбинировать)

Методы цепочечных модификаторов возвращают `self`, позволяя использовать цепочечный вызов. Должны вызываться перед окончательным методом отправки:

- `.At(user_id: Union[str, int], name: str = None)` — упоминание пользователя (можно вызывать несколько раз).
- `.AtAll()` — упоминание всех участников.
- `.Reply(message_id: Union[str, int])` — ответ на указанное сообщение.

### Примеры цепочечных вызовов

```python
# Базовая отправка
await onebot.Send.To("group", 123456).Text("Hello")

# @одного пользователя
await onebot.Send.To("group", 123456).At(789012).Text("Привет")

# @нескольких пользователей
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("Всем привет")

# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# Лайк
await onebot.Send.Like(123456, times=10)

# Запрет участнику отправлять сообщения
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# Разблокировка
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# Исключение участника
await onebot.Send.To("group", 123456).Kick(789012)

# Назначение администратора
await onebot.Send.To("group", 123456).SetAdmin(789012)

# Изменение названия группы
await onebot.Send.To("group", 123456).SetGroupName("Новое название группы")

# Получение информации о группе
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# Операция с указанием аккаунта
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### Обработка не поддерживаемых типов

Если вызывается неопределённый метод отправки, адаптер возвращает текстовое уведомление:

```python
# Вызов несуществующего метода
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Фактически отправляется: "[Неподдерживаемый тип отправки] Имя метода: SomeUnsupportedMethod, Параметры: [...]"
```

## Операции с запросами (DSL для запросов)

Адаптер предоставляет DSL для обработки запросов от друзей и запросов в группы (вступление/приглашение), включая операции подтверждения и отклонения.

### Удобные методы Event

События запросов поддерживают удобные методы `event.approve()` и `event.reject()`, которые автоматически вызывают DSL для запросов:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

@request.on_group_request()
async def handle_group_request(event):
    group_id = event.get("group_id")
    await event.approve()
```

### Ручной вызов DSL для запросов

```python
# Подтверждение запроса
await onebot.Request("flag_string").accept()

# Отклонение запроса
await onebot.Request("flag_string").reject()

# Операции с указанием аккаунта
await onebot.Request("flag_string").Using("main").accept()
```

### Полный пример

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # Способ 1: Использование удобных методов Event
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # Способ 2: Использование DSL для запросов
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### Возвращаемые значения операций с запросами

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}
```

## Сопоставление типов событий

### Стандартное сопоставление OB12

| Тип OB11 | Сопоставленный detail_type | Описание |
|--------------|-------------------|------|
| message_type: private | `private` | Личное сообщение |
| message_type: group | `group` | Групповое сообщение |
| request_type: friend | `friend` | Запрос на добавление в друзья |
| request_type: group | `group` | Запрос в группу |
| meta_event_type: heartbeat | `heartbeat` | Пульс |
| notice_type: group_upload | `group_file_upload` | Загрузка файла в группу |
| notice_type: group_admin | `group_admin_change` | Изменение администратора группы |
| notice_type: group_increase | `group_member_increase` | Увеличение числа участников группы |
| notice_type: group_decrease | `group_member_decrease` | Уменьшение числа участников группы |
| notice_type: group_ban | `group_ban` | Запрет на отправку сообщений в группе |
| notice_type: friend_add | `friend_increase` | Добавление друга |
| notice_type: friend_delete | `friend_decrease` | Удаление друга |
| notice_type: group_recall / friend_recall | `message_recall` | Отмена отправки сообщения |

### Платформо-специфичные события (префикс onebot11_)

| OB11 исходный тип | Сопоставленный detail_type | Описание |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | Жизненный цикл реализации OneBot |
| notify + sub_type: honor | `onebot11_honor` | Изменение чести в группе |
| notify + sub_type: poke | `onebot11_poke` | Удар по человеку |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | Король удачи в группе |
| Неизвестный тип CQ-кода | Сообщение с типом `onebot11_{type}` | Неизвестный CQ-код |

### Примеры событий

```python
// Запрос на добавление друга
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "Пожалуйста, добавьте в друзья",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// Пульс
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// Жизненный цикл (платформо-специфичный)
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// Удар по человеку (платформо-специфичный)
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Король удачи в группе (платформо-специфичный)
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Изменение чести (платформо-специфичный)
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// Расширенный CQ-код
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### Описание расширенных полей

- Все специфичные поля имеют префикс `onebot11_`
- Исходные данные события сохраняются в поле `onebot11_raw`
- Исходный тип события сохраняется в поле `onebot11_raw_type`
- Содержимое сообщений с CQ-кодами преобразуется в соответствующие сообщения (стандартные типы без префикса, неизвестные типы с префиксом `onebot11_`)
- Ответное сообщение добавляет сообщение с типом `reply`
- Сообщения с упоминанием добавляют сообщение с типом `mention`

## Методы расширения событий

Адаптер OneBot11 зарегистрировал следующие специфичные для платформы методы для объектов событий, которые можно напрямую вызывать в обработчиках событий:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### Список методов

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_raw_event()` | `dict` | Получить полные исходные данные события OneBot11 |
| `get_raw_self_id()` | `str` | Получить исходный self_id (номер QQ бота) |
| `get_sender_info()` | `dict` | Получить полную информацию о отправителе (включая nickname, role, level и т.д.) |
| `get_sender_role()` | `str` | Получить роль отправителя в группе (owner/admin/member) |
| `get_sender_level()` | `int` | Получить уровень отправителя |
| `get_sender_title()` | `str` | Получить титул отправителя в группе |
| `is_system_message()` | `bool` | Определить, является ли сообщение системным (sub_type == "system") |

### Примеры использования

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("Администратор, здравствуйте!")

    title = event.get_sender_title()
    if title:
        await event.reply(f"Ваш титул: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "неизвестно")
    level = event.get_sender_level()
    await event.reply(f"Никнейм: {nickname}, уровень: {level}")
```

## Параметры конфигурации

Адаптер OneBot11 использует архитектуру с несколькими аккаунтами, каждый аккаунт имеет свою отдельную конфигурацию. Ключ конфигурации — `OneBotAdapter`.

### Поля конфигурации аккаунта

| Поле | Тип | Обязательное | Значение по умолчанию | Описание |
|------|------|------|--------|------|
| `bot_id` | `str` | Да | `""` | QQ-номер бота, используется для идентификации аккаунта |
| `mode` | `str` | Нет | `"server"` | Режим работы: `"server"` (активный режим ожидания) или `"client"` (активное подключение) |
| `url` | `str` | Нет | `"ws://127.0.0.1:3001"` | Адрес WebSocket для режима Client |
| `token` | `str` | Нет | `""` | Токен аутентификации (токен для подключения в режиме Client / токен проверки в режиме Server) |
| `server_path` | `str` | Нет | `"/"` | Путь WebSocket для режима Server |
| `enabled` | `bool` | Нет | `true` | Включён ли этот аккаунт |
| `name` | `str` | Нет | `""` | Заметка к аккаунту |

### Встроенные значения по умолчанию

- Интервал повторного подключения: 30 секунд
- Время ожидания вызова API: 30 секунд

### Пример конфигурации

```toml
[OneBotAdapter.accounts.main]
bot_id = "123456789"
mode = "server"
server_path = "/onebot-main"
token = "main_token"
enabled = true

[OneBotAdapter.accounts.backup]
bot_id = "987654321"
mode = "client"
url = "ws://127.0.0.1:3002"
token = "backup_token"
enabled = true

[OneBotAdapter.accounts.test]
bot_id = "111222333"
mode = "client"
url = "ws://127.0.0.1:3003"
enabled = false
```

### Конфигурация по умолчанию

Если не настроены никакие аккаунты, адаптер автоматически создаст следующую конфигурацию:
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно напрямую ожидать для получения результата отправки. Результат возвращается в соответствии со стандартизированным форматом ErisPulse-адаптера:

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "onebot11_raw": {...}
}
```

### Синтаксис отправки с несколькими аккаунтами

```python
# Метод выбора аккаунта
await onebot.Send.Using("main").To("group", 123456).Text("Сообщение от основного аккаунта")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# Выбор аккаунта по bot_id
await onebot.Send.Using("123456789").To("group", 123456).Text("Выбор по номеру QQ")

# Вызов API
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### Приоритет разрешения аккаунта

Приоритет разрешения параметра `account_id` в `call_api` и `Using()`:
1. Точное совпадение имени аккаунта
2. Совпадение по полю `bot_id`
3. Совпадение по любому строковому полю аккаунта
4. Возврат к первому включенному аккаунту

## Асинхронная обработка

Адаптер OneBot11 использует асинхронную неблокирующую модель, что обеспечивает:
1. Отправка сообщений не блокирует цикл обработки событий
2. Множественные операции отправки могут выполняться одновременно
3. API-ответы могут обрабатываться вовремя
4. Соединение WebSocket остается активным
5. Параллельная обработка нескольких аккаунтов, каждый аккаунт работает независимо

## Обработка ошибок

Адаптер предоставляет комплексную систему обработки ошибок:
1. Автоматическое повторное подключение при сетевых сбоях (поддерживается независимое повторное подключение для каждого аккаунта с интервалом 30 секунд)
2. Обработка тайм-аутов вызова API (фиксированный тайм-аут 30 секунд)
3. Автоматическая повторная попытка подключения при сбоях с заданным интервалом

## Расширенная обработка событий

В режиме нескольких аккаунтов все события автоматически сопровождаются информацией об аккаунте:
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... другие поля события
}
```

Адаптер автоматически поддерживает отображение `self_id → account_name`, и `event.reply()` не требует ручного указания аккаунта для корректного маршрутизирования к исходному аккаунту.

## Управление интерфейсом

```python
# Получение информации обо всех аккаунтах
accounts = onebot.accounts

# Проверка статуса подключения аккаунтов
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# Динамическое включение/отключение аккаунта (требуется перезапуск адаптера)
onebot.accounts["test"].enabled = False
```

## Автоматическое сопоставление self_id

Адаптер автоматически устанавливает сопоставление между `self_id` OneBot (номером QQ) и `account_name`, которое используется для маршрутизации событий:

```python
# Адаптер выполняет это автоматически
# При получении события поле self.user_id заполняется значением bot_id
# Адаптер автоматически записывает: self_id("123456789") → account_name("main")

# Поэтому event.reply() может автоматически найти правильный аккаунт для отправки сообщения
@message.on_message()
async def handler(event):
    await event.reply("Автоматически маршрутизировано к правильному аккаунту")
```