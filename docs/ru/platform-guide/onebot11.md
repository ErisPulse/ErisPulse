# Документация по функциям платформы OneBot11

OneBot11Adapter — это адаптер, построенный на основе протокола OneBot V11.

---

## Информация о документации

- Версия соответствующего модуля: 4.0.0
- Администратор: ErisPulse

## Основная информация

- Краткое описание платформы: OneBot — это стандарт интерфейса приложения для чат-ботов
- Название адаптера: OneBotAdapter
- Поддерживаемые протоколы/версии API: OneBot V11
- Поддержка нескольких аккаунтов: По умолчанию используется архитектура с несколькими аккаунтами, поддерживается одновременная настройка и работа нескольких аккаунтов OneBot
- Ключ конфигурации: `OneBotAdapter`

## Типы поддерживаемых отправляемых сообщений

Все методы отправки реализованы с использованием цепочки вызовов, например:

```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Отправка с использованием учетной записи по умолчанию
await onebot.Send.To("group", group_id).Text("Hello World!")

# Отправка с использованием определенной учетной записи
await onebot.Send.Using("main").To("group", group_id).Text("Сообщение от основной учетной записи")

# Цепочка модификаторов: @пользователь + ответ
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Ответ на сообщение")

# @всех участников
await onebot.Send.To("group", group_id).AtAll().Text("Анонс")
```

### Основные методы отправки

- `.Text(text: str)` — отправка текстового сообщения.
- `.Image(file: Union[str, bytes], filename: str = "image.png")` — отправка изображения (поддерживается URL, Base64 или bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")` — отправка голосового сообщения.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` — отправка видео.
- `.Face(id: Union[str, int])` — отправка эмодзи QQ.
- `.File(file: Union[str, bytes], filename: str = "file.dat")` — отправка файла (тип определяется автоматически).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12 (автоматически преобразуется в OB11).
- `.Recall(message_id: Union[str, int])` — отмена отправленного сообщения.

### Методы управления группой

Данные методы должны вызываться с помощью `To("group", group_id)` для указания целевой группы:

- `.Kick(user_id, reject_add_request=False)` — исключение участника из группы.
- `.Ban(user_id, duration=1800)` — временная блокировка участника (в секундах), 0 — разблокировка.
- `.WholeBan(enable=True)` — включение/выключение общей блокировки.
- `.SetAdmin(user_id, enable=True)` — назначение/снятие администратора.
- `.SetCard(user_id, card="")` — установка имени в группе.
- `.SetGroupName(name)` — изменение названия группы.
- `.Leave(is_dismiss=False)` — выход из группы (для владельца — возможность удалить группу).
- `.SetTitle(user_id, title="")` — установка титула участника.
- `.SetPortrait(file)` — установка аватара группы.

### Методы запросов

- `.GetMsg(message_id)` — получение содержимого сообщения.
- `.GetForwardMsg(id)` — получение пересылаемого сообщения.
- `.GetLoginInfo()` — информация о текущем аккаунте.
- `.GetFriendList()` — список друзей.
- `.GetGroupInfo()` — информация о группе (требуется `To("group", group_id)`).
- `.GetGroupList()` — список групп.
- `.GetGroupMemberInfo(user_id)` — информация о участнике группы (требуется `To("group", group_id)`).
- `.GetGroupMemberList()` — список участников группы (требуется `To("group", group_id)`).

### Методы управления контактами

- `.Like(user_id, times=1)` — отправка лайка (максимум 10 раз).

### Методы-модификаторы цепочки вызовов (могут комбинироваться)

Методы-модификаторы возвращают `self`, поддерживают цепочку вызовов и должны вызываться до окончательного метода отправки:

- `.At(user_id: Union[str, int], name: str = None)` — упоминание пользователя (может вызываться несколько раз).
- `.AtAll()` — упоминание всех участников.
- `.Reply(message_id: Union[str, int])` — ответ на сообщение.

### Примеры цепочки вызовов

```python
# Базовая отправка
await onebot.Send.To("group", 123456).Text("Hello")

# Упоминание одного пользователя
await onebot.Send.To("group", 123456).At(789012).Text("Привет")

# Упоминание нескольких пользователей
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("Всем привет")

# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# Лайк
await onebot.Send.Like(123456, times=10)

# Блокировка участника
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

# Использование определенной учетной записи
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### Обработка не поддерживаемых типов

Если вызывается неопределенный метод отправки, адаптер возвращает текстовое уведомление:
```python
# Вызов несуществующего метода
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Фактически отправляется: "[Неподдерживаемый тип отправки] Метод: SomeUnsupportedMethod, Параметры: [...]"
```

## Операции запроса (DSL для запросов)

Адаптер предоставляет DSL для операций запросов, используемый для обработки запросов от друзей и запросов на группу (вступление/приглашение), включая действия по согласию или отклонению.

### Ускоренные методы Event

События запросов поддерживают ускоренные методы `event.approve()` и `event.reject()`, которые автоматически вызывают DSL запроса:

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

### Ручной вызов DSL запроса

```python
# Согласие с запросом
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

    # Способ 1: Использование ускоренных методов Event
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # Способ 2: Использование DSL запроса
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### Возвращаемые значения операций запроса

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

| Тип OB11 | detail_type после преобразования | Описание |
|--------------|-------------------|------|
| message_type: private | `private` | Личное сообщение |
| message_type: group | `group` | Групповое сообщение |
| request_type: friend | `friend` | Запрос на добавление в друзья |
| request_type: group | `group` | Запрос в группу |
| meta_event_type: heartbeat | `heartbeat` | Пульс |
| notice_type: group_upload | `group_file_upload` | Загрузка файла в группе |
| notice_type: group_admin | `group_admin_change` | Изменение администратора группы |
| notice_type: group_increase | `group_member_increase` | Увеличение числа участников группы |
| notice_type: group_decrease | `group_member_decrease` | Уменьшение числа участников группы |
| notice_type: group_ban | `group_ban` | Запрет на отправку сообщений в группе |
| notice_type: friend_add | `friend_increase` | Добавление друга |
| notice_type: friend_delete | `friend_decrease` | Удаление друга |
| notice_type: group_recall / friend_recall | `message_recall` | Отмена отправки сообщения |

### Платформенные события (префикс onebot11_)

| Тип OB11 | detail_type после преобразования | Описание |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | Жизненный цикл реализации OneBot |
| notify + sub_type: honor | `onebot11_honor` | Изменение звания в группе |
| notify + sub_type: poke | `onebot11_poke` | Щелчок |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | Король удачи в групповом红包 |
| Неизвестный тип CQ-кода | Сообщение-сегмент `onebot11_{type}` | Неизвестный CQ-код |

### Примеры событий

```python
// Запрос на добавление в друзья
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

// Жизненный цикл (платформенное событие)
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// Щелчок (платформенное событие)
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Король удачи в групповом红包 (платформенное событие)
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Изменение звания (платформенное событие)
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// Расширенный сегмент сообщения CQ-кода
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### Описание расширенных полей

- Все специальные поля идентифицируются префиксом `onebot11_`
- Оригинальные данные события сохраняются в поле `onebot11_raw`
- Оригинальный тип события сохраняется в поле `onebot11_raw_type`
- Содержимое сообщения с CQ-кодами преобразуется в соответствующие сегменты сообщений (стандартные типы без префикса, неизвестные типы с префиксом `onebot11_`)
- Ответное сообщение добавляется в сегмент сообщения типа `reply`
- Упоминание в сообщении добавляется в сегмент сообщения типа `mention`

## Методы расширения событий

Адаптер OneBot11 зарегистрировал следующие специфические методы платформы для объектов событий, которые можно напрямую вызывать в обработчиках событий:

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
| `get_raw_self_id()` | `str` | Получить оригинальный self_id (QQ-номер бота) |
| `get_sender_info()` | `dict` | Получить полную информацию об отправителе (включая nickname, role, level и т.д.) |
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

Адаптер OneBot11 использует архитектуру с несколькими аккаунтами, каждый аккаунт имеет независимую конфигурацию. Ключ конфигурации: `OneBotAdapter`.

### Поля конфигурации аккаунта

| Поле | Тип | Обязательно | Значение по умолчанию | Описание |
|------|------|-------------|------------------------|----------|
| `bot_id` | `str` | Да | `""` | QQ-номер бота, используется для идентификации аккаунта |
| `mode` | `str` | Нет | `"server"` | Режим работы: `"server"` (активный слушатель) или `"client"` (активное подключение) |
| `url` | `str` | Нет | `"ws://127.0.0.1:3001"` | Адрес WebSocket для режима Client |
| `token` | `str` | Нет | `""` | Токен аутентификации (Token для подключения в режиме Client / Token для проверки в режиме Server) |
| `server_path` | `str` | Нет | `"/"` | Путь WebSocket для режима Server |
| `enabled` | `bool` | Нет | `true` | Включен ли данный аккаунт |
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

Если не настроен ни один аккаунт, адаптер автоматически создаст следующую конфигурацию:
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно напрямую ожидать для получения результата отправки. Возвращаемый результат соответствует стандартизированному спецификации возврата адаптера ErisPulse:

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

# Способ вызова API
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### Приоритет разрешения аккаунта

Приоритет разрешения параметра `account_id` в `call_api` и `Using()`:
1. Точное совпадение с именем аккаунта
2. Совпадение с полем `bot_id`
3. Совпадение с любым полем типа `str` аккаунта
4. Возврат к первому включенному аккаунту

## Асинхронная обработка

Адаптер OneBot11 использует асинхронную неблокирующую архитектуру, что обеспечивает:
1. Отправка сообщений не блокирует цикл обработки событий
2. Множественные операции отправки могут выполняться одновременно
3. Ответы API обрабатываются своевременно
4. WebSocket-соединение остаётся активным
5. Параллельная обработка нескольких аккаунтов, каждый аккаунт работает независимо

## Обработка ошибок

Адаптер предоставляет надежную систему обработки ошибок:
1. Автоматическое повторное подключение при сетевых сбоях (поддерживается независимое повторное подключение для каждого аккаунта с интервалом 30 секунд)
2. Обработка таймаутов вызова API (фиксированный таймаут 30 секунд)
3. Автоматические повторные попытки при неудачном подключении с заданным интервалом

## Улучшенная обработка событий

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

Адаптер автоматически поддерживает сопоставление `self_id → account_name`, и `event.reply()` не требует ручного указания аккаунта для корректного маршрутизирования к исходному аккаунту.

## Управление интерфейсом

```python
# Получить информацию обо всех аккаунтах
accounts = onebot.accounts

# Проверить состояние подключения аккаунта
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# Динамически включить/отключить аккаунт (требуется перезапуск адаптера)
onebot.accounts["test"].enabled = False
```

## Автоматическое сопоставление self_id

Адаптер автоматически устанавливает сопоставление между OneBot `self_id` (QQ-номер) и `account_name`, которое используется для маршрутизации событий:

```python
# Адаптер автоматически выполняет это внутренне
# При получении события поле self.user_id заполняется значением bot_id
# Адаптер автоматически записывает: self_id("123456789") → account_name("main")

# Таким образом, event.reply() может автоматически найти правильный аккаунт для отправки сообщения
@message.on_message()
async def handler(event):
    await event.reply("Автоматическая маршрутизация на правильный аккаунт")
```