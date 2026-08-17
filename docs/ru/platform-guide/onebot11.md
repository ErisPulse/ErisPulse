# Документация по функциям платформы OneBot11

OneBot11Adapter — это адаптер, построенный на основе протокола OneBot V11.

---

Пожалуйста, верните полностью переведенный Markdown-документ, не добавляя никаких других текстов.

## Информация о документации

- Версия соответствующего модуля: 4.0.0
- Ответственный: ErisPulse

Пожалуйста, верните полностью переведённый Markdown-документ, не добавляя никаких других текстов.

## Основная информация

- **Описание платформы:** OneBot — это стандартный интерфейс приложения для чат-ботов.
- **Название адаптера:** OneBotAdapter
- **Поддерживаемые протоколы/версии API:** OneBot V11
- **Поддержка нескольких аккаунтов:** По умолчанию используется архитектура с несколькими аккаунтами, позволяет настроить и запустить несколько аккаунтов OneBot одновременно.
- **Ключ конфигурации:** `OneBotAdapter`

Ссылки на документацию:
- [Одностраничное руководство](docs/ru/quick-start.md)
- [Руководство по настройке](docs/ru/configuration.md)
- [Справочник по API](docs/ru/api-reference.md)

## Типы поддерживаемых отправляемых сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:

```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Отправка с использованием аккаунта по умолчанию
await onebot.Send.To("group", group_id).Text("Hello World!")

# Отправка с указанием конкретного аккаунта
await onebot.Send.Using("main").To("group", group_id).Text("Сообщение от основного аккаунта")

# Цепочечные модификаторы: @пользователь + ответ
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Ответное сообщение")

# @всех участников
await onebot.Send.To("group", group_id).AtAll().Text("Анонс")
```

### Базовые методы отправки

- `.Text(text: str)` — отправка обычного текстового сообщения.
- `.Image(file: Union[str, bytes], filename: str = "image.png")` — отправка изображения (поддерживается URL, Base64 или bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")` — отправка голосового сообщения.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` — отправка видео.
- `.Face(id: Union[str, int])` — отправка эмодзи QQ.
- `.File(file: Union[str, bytes], filename: str = "file.dat")` — отправка файла (тип определяется автоматически).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12 (автоматически преобразуется в OB11).
- `.Recall(message_id: Union[str, int])` — отмена отправки сообщения.

### Методы управления группой

Методы, требующие указания целевой группы с помощью `To("group", group_id)`, выполняются в контексте группы:

- `.Kick(user_id, reject_add_request=False)` — исключение участника из группы.
- `.Ban(user_id, duration=1801)` — временная блокировка участника (в секундах), 0 — разблокировка.
- `.WholeBan(enable=True)` — включение/выключение блокировки всех участников.
- `.SetAdmin(user_id, enable=True)` — назначение/снятие администратора.
- `.SetCard(user_id, card="")` — установка имени участника в группе.
- `.SetGroupName(name)` — изменение названия группы.
- `.Leave(is_dismiss=False)` — выход из группы (глава может распустить группу).
- `.SetTitle(user_id, title="")` — установка титула участника.
- `.SetPortrait(file)` — установка аватара группы.

### Методы запросов

- `.GetMsg(message_id)` — получение содержимого сообщения.
- `.GetForwardMsg(id)` — получение пересланного сообщения.
- `.GetLoginInfo()` — получение информации о текущем аккаунте.
- `.GetFriendList()` — получение списка друзей.
- `.GetGroupInfo()` — получение информации о группе (требуется `To("group", group_id)`).
- `.GetGroupList()` — получение списка групп.
- `.GetGroupMemberInfo(user_id)` — получение информации о участнике группы (требуется `To("group", group_id)`).
- `.GetGroupMemberList()` — получение списка участников группы (требуется `To("group", group_id)`).

### Методы управления друзьями

- `.Like(user_id, times=1)` — отправка лайка другу (максимум 10 раз).

### Цепочечные модификаторы (можно комбинировать)

Методы возвращают `self`, позволяя цепочечное использование, и должны вызываться перед окончательным методом отправки:

- `.At(user_id: Union[str, int], name: str = None)` — упоминание пользователя (можно вызывать несколько раз).
- `.AtAll()` — упоминание всех участников.
- `.Reply(message_id: Union[str, int])` — ответ на сообщение.

### Примеры цепочечного вызова

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

# Блокировка участника
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# Разблокировка
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# Исключение участника
await onebot.Send.To("group", 123456).Kick(789012)

# Назначение администратора
await onebot.Send.To("group", 123456).SetAdmin(789012)

# Изменение названия группы
await onebot.Send.To("group", 123456).SetGroupName("Новое название")

# Получение информации о группе
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# Операция с указанием аккаунта
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### Обработка не поддерживаемых типов

Если вызывается неопределённый метод отправки, адаптер вернёт текстовое уведомление:

```python
# Вызов несуществующего метода
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Фактически отправляется: "[Неподдерживаемый тип отправки] Метод: SomeUnsupportedMethod, Параметры: [...]"

## Операции с запросами (Request DSL)

Адаптер предоставляет DSL-операции запросов, предназначенные для обработки запросов на добавление в друзья и запросов в группы (вступление/приглашение) с возможностью подтверждения/отклонения.

### Ускоренные методы Event

События запросов поддерживают ускоренные методы `event.approve()` и `event.reject()`, которые автоматически вызывают Request DSL:

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

### Ручной вызов Request DSL

```python
# Подтверждение запроса
await onebot.Request("flag_string").accept()

# Отклонение запроса
await onebot.Request("flag_string").reject()

# Операция с указанием аккаунта
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

    # Способ 2: Использование Request DSL
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### Возвращаемые значения операций запросов

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}

## Сопоставление типов событий

### Стандартное сопоставление OB12

| Тип OB11 | Сопоставленный detail_type | Описание |
|--------------|-------------------|------|
| message_type: private | `private` | Личное сообщение |
| message_type: group | `group` | Сообщение в группе |
| request_type: friend | `friend` | Запрос на добавление в друзья |
| request_type: group | `group` | Запрос в группу |
| meta_event_type: heartbeat | `heartbeat` | Пинг |
| notice_type: group_upload | `group_file_upload` | Загрузка файла в группе |
| notice_type: group_admin | `group_admin_change` | Изменение администратора группы |
| notice_type: group_increase | `group_member_increase` | Добавление участника в группу |
| notice_type: group_decrease | `group_member_decrease` | Удаление участника из группы |
| notice_type: group_ban | `group_ban` | Запрет на отправку сообщений в группе |
| notice_type: friend_add | `friend_increase` | Добавление в друзья |
| notice_type: friend_delete | `friend_decrease` | Удаление из друзей |
| notice_type: group_recall / friend_recall | `message_recall` | Отмена отправки сообщения |

### Платформенно-специфичные события (префикс onebot11_)

| OB11 Тип | Сопоставленный detail_type | Описание |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | Жизненный цикл реализации OneBot |
| notify + sub_type: honor | `onebot11_honor` | Изменение награды в группе |
| notify + sub_type: poke | `onebot11_poke` | Клик по участнику |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | Победитель в групповом розыгрыше |
| Неизвестный тип CQ-кода | Сообщение `onebot11_{type}` | Неизвестный CQ-код |

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

// Пинг
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// Жизненный цикл (платформенно-специфичный)
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// Клик по участнику (платформенно-специфичный)
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Победитель в групповом розыгрыше (платформенно-специфичный)
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Изменение награды (платформенно-специфичный)
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

- Все специфичные поля идентифицируются с префиксом `onebot11_`
- Исходные данные события сохраняются в поле `onebot11_raw`
- Исходный тип события сохраняется в поле `onebot11_raw_type`
- Содержимое сообщения с CQ-кодами преобразуется в соответствующие сообщения (стандартные типы без префикса, неизвестные с префиксом `onebot11_`)
- Ответ на сообщение добавляет сообщение типа `reply`
- Упоминание пользователя добавляет сообщение типа `mention`

## Методы расширения событий

Адаптер OneBot11 зарегистрировал следующие методы, специфичные для платформы, для объектов событий, которые можно вызывать непосредственно в обработчиках событий:

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
| `get_sender_info()` | `dict` | Получить полную информацию о отправителе (включая nickname, role, level и т. д.) |
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
    nickname = info.get("nickname", "неизвестный")
    level = event.get_sender_level()
    await event.reply(f"Никнейм: {nickname}, уровень: {level}")

## Параметры конфигурации

Адаптер OneBot11 использует архитектуру с несколькими аккаунтами, каждый аккаунт имеет свою независимую конфигурацию. Ключи конфигурации имеют имя `OneBotAdapter`.

### Поля конфигурации аккаунта

| Поле | Тип | Обязательно | Значение по умолчанию | Описание |
|------|------|-------------|-----------------------|----------|
| `bot_id` | `str` | Да | `""` | QQ-номер робота, используется для идентификации аккаунта |
| `mode` | `str` | Нет | `"server"` | Режим работы: `"server"` (пассивное прослушивание) или `"client"` (активное подключение) |
| `url` | `str` | Нет | `"ws://127.0.0.1:3001"` | Адрес WebSocket для режима Client |
| `token` | `str` | Нет | `""` | Токен аутентификации (требуется для подключения в режиме Client / для проверки токена в режиме Server) |
| `server_path` | `str` | Нет | `"/"` | Путь WebSocket для режима Server |
| `enabled` | `bool` | Нет | `true` | Включен ли данный аккаунт |
| `name` | `str` | Нет | `""` | Заметка/имя аккаунта |

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

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно напрямую ожидать для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату ответа адаптера ErisPulse:

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

### Приоритет разбора аккаунта

Приоритет разбора параметра `account_id` в `call_api` и `Using()`:
1. Точное совпадение с именем аккаунта
2. Совпадение с полем `bot_id`
3. Совпадение с любым полем типа `str` аккаунта
4. Возврат к первому включенному аккаунту

## Асинхронная обработка

Адаптер OneBot11 использует асинхронную неблокирующую модель, что обеспечивает:
1. Отправка сообщений не блокирует цикл обработки событий
2. Множественные операции отправки могут выполняться одновременно
3. API-ответы обрабатываются своевременно
4. WebSocket-соединение остается активным
5. Параллельная обработка нескольких аккаунтов, каждый аккаунт работает независимо

[**中文**](docs/ru/async-processing.md) | [**English**](docs/en/async-processing.md)

## Обработка ошибок

Адаптер предоставляет комплексную систему обработки ошибок:
1. Автоматическое повторное подключение при сетевых сбоях (поддержка независимого повторного подключения для каждого аккаунта с интервалом 30 секунд)
2. Обработка тайм-аута вызова API (фиксированный тайм-аут 30 секунд)
3. Автоматическая повторная попытка подключения с заданным интервалом при ошибках подключения

[**中文**](docs/ru/quick-start.md)

## Улучшение обработки событий

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

Адаптер автоматически поддерживает сопоставление `self_id → account_name`, и `event.reply()` может корректно направлять ответ на исходный аккаунт без необходимости ручного указания аккаунта.

[**中文**](docs/ru/event-handling-enhancement.md) | [**English**](docs/en/event-handling-enhancement.md) | [**Русский**](docs/ru/event-handling-enhancement.md)

## Управление интерфейсом

```python
# Получить информацию обо всех аккаунтах
accounts = onebot.accounts

# Проверить статус подключения аккаунта
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# Динамически включить/отключить аккаунт (требуется перезапуск адаптера)
onebot.accounts["test"].enabled = False

## Автоматическое сопоставление self_id

Адаптер автоматически устанавливает сопоставление между OneBot `self_id` (номером QQ) и `account_name`, которое используется для маршрутизации событий:

```python
# Адаптер автоматически выполняет это внутренне
# При получении события поле self.user_id заполняется значением bot_id
# Адаптер автоматически записывает: self_id("123456789") → account_name("main")

# Таким образом event.reply() может автоматически найти правильный аккаунт для отправки сообщения
@message.on_message()
async def handler(event):
    await event.reply("Автоматическая маршрутизация к правильному аккаунту")
```

Документация: [docs/ru/quick-start.md](docs/ru/quick-start.md)