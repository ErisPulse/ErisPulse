# Документация по особенностям платформы OneBot11

OneBot11Adapter — это адаптер, построенный на основе протокола OneBot V11.

---

## Информация о документе

- Соответствующая версия модуля: 4.6.2
- Сопровождающий: ErisPulse
- Последнее обновление: 2026-11-10

## Основная информация

- Описание платформы: OneBot — стандарт интерфейса приложений чат-ботов
- Название адаптера: OneBotAdapter
- Поддерживаемая версия протокола/API: OneBot V11
- Поддержка нескольких аккаунтов: мультиаккаунтная архитектура по умолчанию, поддерживает одновременную настройку и запуск нескольких аккаунтов OneBot
- Имя ключа конфигурации: `OneBotAdapter`

## Обновление до парадигмы v5 (начиная с 4.3.0)

Данный адаптер завершил выравнивание с парадигмой v5 (инкрементное обновление, совместимость API):

- **Наследование BaseConverter**: общие поля конвертера (id/time/platform/self/raw) строятся методом build_base_event фреймворка и переопределяются по именам полей OB11 (echo/time/self_id)
- **Принадлежность задач spawn_background**: задачи подключения в режиме Client переведены на Runtime.spawn_background (привязка owner, автоматическая очистка при shutdown)
- **Мягкая зависимость от фреймворка**: установка адаптера больше не объявляет жёсткую зависимость от ErisPulse, чтобы избежать изменения версии фреймворка при разрешении pip; во время выполнения проверяется ErisPulse>=2.7.1, и при слишком низкой версии выводится предупреждение в лог
- **Журнал версии при запуске**: при инициализации выводится OneBotAdapter vX.Y.Z загружен

Существующие возможности (поддерживаются с 4.2.0): мультиаккаунтность, маппинг стандартных действий Api DSL (get_self_info→get_login_info и т.д.), Request DSL (одобрение запросов друзей/групп: event.approve() / event.reject()), EventMixin, i18n.

Начиная с 4.3.1 обработка событий запросов реализована в соответствии со спецификацией, подробности см. в разделе [Соответствие стандартам](#соответствие-стандартам) ниже.

---

## Стандартные действия API (Api DSL)

Адаптер автоматически сопоставляет стандартные имена действий OneBot12 с именами действий OB11, что позволяет модулям единообразно вызывать их на разных платформах:

| Стандартное действие OB12 | Действие OB11 | Описание |
|--------------|-----------|------|
| get_self_info | get_login_info | Нормализация полей user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | Нормализация полей |
| delete_message | delete_msg | Отзыв сообщения |
| leave_group | set_group_leave | Выход из группы |
| get_friend_list | get_friend_list | Имена действий совпадают, по умолчанию передаётся напрямую |
| get_group_info | get_group_info | Имена действий совпадают, по умолчанию передаётся напрямую |
| upload_file | upload_group_file / upload_private_file | Расширенные необязательные параметры group_id/user_id, filetype автоматически определяет тип и выполняет маршрутизацию |

### Основы использования

```python
from ErisPulse import sdk
onebot = sdk.adapter.get("onebot11")

# Получение информации о боте
result = await onebot.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# Отзыв сообщения
await onebot.Api.delete_message(message_id=123456)

# Загрузка файла в группу (filetype автоматически определяет тип и направляет в upload_group_file)
result = await onebot.Api.upload_file(group_id=123456, file="/path/to/file.zip")

# Указание аккаунта (мультиаккаунтность)
result = await onebot.Api.Using("main").get_self_info()

# Несопоставленные действия OB11 вызываются через escape-hatch call() (универсально для расширений NapCat/Lagrange и т.д.)
result = await onebot.Api.call("send_poke", group_id=123, user_id=456)
```

### Расширения протокола OB11 (общие для NapCat/go-cqhttp/SnowLuma)

Часто используемые расширенные действия инкапсулированы в типизированные методы (mixin `OB11ExtensionApi`) с поддержкой автодополнения в IDE:

```python
await onebot.Api.send_poke(user_id=789, group_id=123456)
await onebot.Api.set_msg_emoji_like(message_id=123, emoji_id="76")
await onebot.Api.mark_msg_as_read(group_id=123456)
result = await onebot.Api.get_group_msg_history(group_id=123456, count=20)
await onebot.Api.set_essence_msg(message_id=123)
result = await onebot.Api.ocr_image(image="https://example.com/img.png")
```

> Расширенные действия используют имена действий OB11 напрямую, без платформенного префикса. Немногочисленные неинкапсулированные действия вызываются через `Api.call("action_name", ...)`.

### Методы запросов Send (устарели)

Следующие методы Send всё ещё доступны, но помечены как устаревшие; рекомендуется использовать вместо них Api DSL:

| Метод Send (устарел) | Замена через Api DSL |
|------------------|-------------|
| `Send.GetLoginInfo()` | `Api.get_self_info()` |
| `Send.GetFriendList()` | `Api.get_friend_list()` |
| `Send.GetGroupInfo()` | `Api.get_group_info(group_id)` |
| `Send.GetGroupList()` | `Api.get_group_list()` |
| `Send.GetGroupMemberInfo(uid)` | `Api.get_group_member_info(gid, uid)` |
| `Send.GetGroupMemberList()` | `Api.get_group_member_list(gid)` |
| `Send.GetMsg(mid)` | `Api.call("get_msg", message_id=mid)` |
| `Send.GetForwardMsg(id)` | `Api.call("get_forward_msg", id=id)` |

## Соответствие стандартам

В этом разделе описывается поведение адаптера, выровненное со стандартами спецификаций ErisPulse. Подробности спецификаций см. в документации SDK «Спецификация операций с запросами» (`docs/ru/standards/request-action-spec.md`) и «Спецификация ответов API» (`docs/ru/standards/api-response.md`).

### Обработка событий запросов (начиная с 4.3.1)

Адаптер реализует приём и ответ на события запросов в соответствии со спецификацией операций с запросами:

- **Сохранение контекста**: на входе событий `request_id` отображается в `{request_type, sub_type, group_id, account, ts}` и кэшируется (TTL 3600 секунд, максимум 512 записей, очистка после успешной обработки запроса) для последующей маршрутизации в `accept()`/`reject()`
- **Приоритет маршрутизации эндпоинтов**: явно переданные kwargs в `accept()`/`reject()` (`request_type`/`sub_type`/`group_id` — зарезервированные имена) > сохранённый контекст события > откат к эндпоинту для друзей (`set_friend_add_request`) с выводом WARNING
- **Приглашения в группу / заявки на вступление**: при `request_type == "group"` выполняется корректная маршрутизация в `set_group_add_request` (вступление — `sub_type="add"`, приглашение — `sub_type="invite"`)
- **Примечание об устаревании**: способ указания типа запроса через приватный параметр `_request_type`, применявшийся до 4.3.1, устарел и будет игнорироваться

### Обработка ошибок call_api

- Когда аккаунт не подключён или соединение закрыто, `call_api` больше не выбрасывает `ConnectionError`, а возвращает стандартный ответ об ошибке (`status="failed"`, `retcode=33001`)
- При таймауте вызова API также возвращается стандартный ответ об ошибке (`retcode=33001`)

### Двойная совместимость поля аккаунта

- `call_api` принимает как стандартное поле `account_id`, так и старое имя поля `_account_id` (стандартное имя имеет приоритет); ApiDSL фреймворка адаптируется автоматически, в коде модулей рекомендуется использовать `account_id`
- Все методы Send DSL читают `send_context`: внутри цепочки событий автоматически используется аккаунт-источник текущего события; аккаунт, явно указанный через `Using()`, имеет приоритет

### Спецификация кодов ошибок

| retcode | Значение | Сценарий возникновения |
|---------|------|----------|
| 0 | Успех | Действие выполнено успешно |
| 33001 | Сетевая ошибка | Аккаунт не подключён, соединение закрыто, таймаут вызова API |
| 10002 | Неподдерживаемое действие | Вызов нереализованного действия |
| 10003 | Ошибка параметров | Отсутствуют обязательные параметры |

> Исходные данные ответа платформы сохраняются в поле `onebot11_raw`.

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочечный синтаксис, например:
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Отправка через аккаунт по умолчанию
await onebot.Send.To("group", group_id).Text("Hello World!")

# Отправка через конкретный аккаунт
await onebot.Send.Using("main").To("group", group_id).Text("Сообщение от главного аккаунта")

# Цепочка модификаторов: @пользователь + ответ
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Ответ на сообщение")

# @все участники
await onebot.Send.To("group", group_id).AtAll().Text("Объявление")
```

### Базовые методы отправки

- `.Text(text: str)`: отправка текстового сообщения.
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: отправка изображения (поддерживаются URL, Base64 или bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`: отправка голосового сообщения.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: отправка видео.
- `.Face(id: Union[str, int])`: отправка смайлика QQ.
- `.File(file: Union[str, bytes], filename: str = "file.dat")`: отправка файла (тип определяется автоматически).
- `.Raw_ob12(message: List[Dict], **kwargs)`: отправка сообщения в формате OneBot12 (автоматически преобразуется в OB11).
- `.Recall(message_id: Union[str, int])`: отзыв сообщения.

### Методы операций с группой

Для следующих методов целевую группу нужно указать через `To("group", group_id)`, операции выполняются в контексте группы:

- `.Kick(user_id, reject_add_request=False)`: исключение участника из группы.
- `.Ban(user_id, duration=1800)`: заглушение участника группы (в секундах), 0 — снятие заглушения.
- `.WholeBan(enable=True)`: включение/выключение заглушения для всех.
- `.SetAdmin(user_id, enable=True)`: назначение/снятие администратора группы.
- `.SetCard(user_id, card="")`: установка карточки участника группы.
- `.SetGroupName(name)`: изменение названия группы.
- `.Leave(is_dismiss=False)`: выход из группы (владелец может распустить).
- `.SetTitle(user_id, title="")`: установка группового титула.
- `.SetPortrait(file)`: установка аватара группы.

### Методы получения данных

- `.GetMsg(message_id)`: получение содержимого сообщения.
- `.GetForwardMsg(id)`: получение объединённых пересланных сообщений.
- `.GetLoginInfo()`: получение информации о текущем вошедшем аккаунте.
- `.GetFriendList()`: получение списка друзей.
- `.GetGroupInfo()`: получение информации о группе (требуется `To("group", group_id)`).
- `.GetGroupList()`: получение списка групп.
- `.GetGroupMemberInfo(user_id)`: получение информации об участнике группы (требуется `To("group", group_id)`).
- `.GetGroupMemberList()`: получение списка участников группы (требуется `To("group", group_id)`).

### Методы операций с друзьями

- `.Like(user_id, times=1)`: отправка лайка другу (максимум 10 раз).

### Цепочечные методы-модификаторы (можно комбинировать)

Цепочечные методы-модификаторы возвращают `self`, поддерживают цепочечные вызовы и должны вызываться перед финальным методом отправки:

- `.At(user_id: Union[str, int], name: str = None)`: упоминание указанного пользователя (можно вызывать несколько раз).
- `.AtAll()`: упоминание всех участников.
- `.Reply(message_id: Union[str, int])`: ответ на указанное сообщение.

### Примеры цепочечных вызовов

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

# Заглушение участника группы
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# Снятие заглушения
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# Исключение участника
await onebot.Send.To("group", 123456).Kick(789012)

# Назначение администратора группы
await onebot.Send.To("group", 123456).SetAdmin(789012)

# Изменение названия группы
await onebot.Send.To("group", 123456).SetGroupName("Новое название группы")

# Получение информации о группе
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# Операция с указанным аккаунтом
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### Обработка неподдерживаемых типов

При вызове неопределённого метода отправки адаптер вернёт текстовую подсказку:
```python
# Вызов несуществующего метода
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Фактическая отправка: "[Неподдерживаемый тип отправки] Имя метода: SomeUnsupportedMethod, Параметры: [...]"
```

## Операции с запросами (Request DSL)

Адаптер предоставляет DSL операций с запросами для обработки одобрения/отклонения запросов в друзья и групповых запросов (вступление в группу/приглашение).

### Быстрые методы Event

События запросов поддерживают быстрые методы `event.approve()` и `event.reject()`, внутри автоматически вызывающие Request DSL:

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
# Одобрение запроса
await onebot.Request("flag_string").accept()

# Отклонение запроса
await onebot.Request("flag_string").reject()

# Операция с указанным аккаунтом
await onebot.Request("flag_string").Using("main").accept()
```

### Полный пример

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # Способ 1: использование быстрых методов Event
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # Способ 2: использование Request DSL
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### Возвращаемое значение операций с запросами

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}
```

## Маппинг типов событий

### Стандартный маппинг OB12

| Исходный тип OB11 | detail_type после преобразования | Описание |
|--------------|-------------------|------|
| message_type: private | `private` | Личное сообщение |
| message_type: group | `group` | Сообщение в группе |
| request_type: friend | `friend` | Запрос в друзья |
| request_type: group | `group` | Групповой запрос |
| meta_event_type: heartbeat | `heartbeat` | Сердцебиение (heartbeat) |
| notice_type: group_upload | `group_file_upload` | Загрузка файла в группу |
| notice_type: group_admin | `group_admin_change` | Изменение администратора группы |
| notice_type: group_increase | `group_member_increase` | Добавление участника группы |
| notice_type: group_decrease | `group_member_decrease` | Удаление участника группы |
| notice_type: group_ban | `group_ban` | Заглушение в группе |
| notice_type: friend_add | `friend_increase` | Добавление друга |
| notice_type: friend_delete | `friend_decrease` | Удаление друга |
| notice_type: group_recall / friend_recall | `message_recall` | Отзыв сообщения |

### Специфические для платформы события (префикс onebot11_)

| Исходный тип OB11 | detail_type после преобразования | Описание |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | Жизненный цикл реализации OneBot |
| notify + sub_type: honor | `onebot11_honor` | Изменение групповых почётных званий |
| notify + sub_type: poke | `onebot11_poke` | «Тык» (poke) |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | Счастливчик красного конверта в группе |
| Неизвестный тип CQ-кода | Сегмент сообщения `onebot11_{type}` | Нераспознанный CQ-код |

### Примеры событий

```json
// Запрос в друзья
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "Прошу добавить меня в друзья",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// Сердцебиение
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// Жизненный цикл (специфично для платформы)
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// «Тык» (специфично для платформы)
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Счастливчик красного конверта (специфично для платформы)
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Изменение почётного звания (специфично для платформы)
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

- Все специфические поля помечены префиксом `onebot11_`
- Исходные данные события сохраняются в поле `onebot11_raw`
- Исходный тип события сохраняется в поле `onebot11_raw_type`
- CQ-коды в содержимом сообщения преобразуются в соответствующие сегменты сообщения (стандартные типы без префикса, неизвестные типы с префиксом `onebot11_`)
- Ответные сообщения добавляют сегмент сообщения типа `reply`
- Упоминания добавляют сегмент сообщения типа `mention`

## Расширенные методы событий

Адаптер OneBot11 регистрирует для объектов событий следующие платформенно-специфичные методы, которые можно вызывать напрямую в обработчиках событий:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_event = event.get_raw_event()
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### Список методов

| Метод | Возвращаемый тип | Описание |
|------|----------|------|
| `get_raw_event()` | `dict` | Получение полных исходных данных события OneBot11 |
| `get_raw_self_id()` | `str` | Получение исходного self_id (QQ-номер бота) |
| `get_sender_info()` | `dict` | Получение полной информации об отправителе (включая nickname, role, level и т.д.) |
| `get_sender_role()` | `str` | Получение роли отправителя в группе (owner/admin/member) |
| `get_sender_level()` | `int` | Получение уровня отправителя |
| `get_sender_title()` | `str` | Получение группового титула отправителя |
| `is_system_message()` | `bool` | Определение, является ли сообщение системным (sub_type == "system") |

### Пример использования

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("Привет, администратор!")

    title = event.get_sender_title()
    if title:
        await event.reply(f"Ваш титул: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "Неизвестно")
    level = event.get_sender_level()
    await event.reply(f"Ник: {nickname}, Уровень: {level}")
```

## Параметры конфигурации

Адаптер OneBot11 использует мультиаккаунтную архитектуру, каждый аккаунт настраивается независимо. Имя ключа конфигурации — `OneBotAdapter`.

### Поля конфигурации аккаунта

| Поле | Тип | Обязательное | По умолчанию | Описание |
|------|------|------|--------|------|
| `bot_id` | `str` | Да | `""` | QQ-номер бота, используется для идентификации аккаунта |
| `mode` | `str` | Нет | `"server"` | Режим работы: `"server"` (пассивное прослушивание) или `"client"` (активное подключение) |
| `url` | `str` | Нет | `"ws://127.0.0.1:3001"` | Адрес WebSocket для режима Client |
| `token` | `str` | Нет | `""` | Токен аутентификации (токен подключения в режиме Client / токен проверки в режиме Server) |
| `server_path` | `str` | Нет | `"/"` | Путь WebSocket для режима Server |
| `enabled` | `bool` | Нет | `true` | Включён ли аккаунт |
| `name` | `str` | Нет | `""` | Заметка/название аккаунта |

### Встроенные значения по умолчанию

- Интервал переподключения: 30 секунд
- Таймаут вызова API: 30 секунд

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

Если аккаунты не настроены, адаптер автоматически создаёт:
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно напрямую await для получения результата отправки. Результат следует стандартизированной спецификации возврата адаптеров ErisPulse:

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

### Синтаксис отправки для нескольких аккаунтов

```python
# Метод выбора аккаунта
await onebot.Send.Using("main").To("group", 123456).Text("Сообщение от главного аккаунта")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# Выбор аккаунта по bot_id
await onebot.Send.Using("123456789").To("group", 123456).Text("Выбор по QQ-номеру")

# Способ вызова API
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### Приоритет разрешения аккаунтов

Приоритет разрешения параметра `account_id` в `call_api` и `Using()`:
1. Точное совпадение имени аккаунта
2. Совпадение поля `bot_id`
3. Совпадение любого поля аккаунта типа `str`
4. Откат к первому включённому аккаунту

## Механизм асинхронной обработки

Адаптер OneBot11 использует асинхронный неблокирующий дизайн, что гарантирует:
1. Отправка сообщений не блокирует цикл обработки событий
2. Несколько параллельных операций отправки могут выполняться одновременно
3. Ответы API обрабатываются своевременно
4. Соединения WebSocket остаются активными
5. Параллельная обработка нескольких аккаунтов, каждый аккаунт работает независимо

## Обработка ошибок

Адаптер предоставляет полноценный механизм обработки ошибок:
1. Автоматическое переподключение при сетевых сбоях (поддерживается независимое переподключение для каждого аккаунта, интервал 30 секунд)
2. Обработка таймаута вызова API (фиксированный таймаут 30 секунд, при таймауте возвращается стандартный ответ об ошибке с `retcode=33001`)
3. Когда аккаунт не подключён/соединение закрыто, `call_api` возвращает стандартный ответ об ошибке с `retcode=33001` и больше не выбрасывает `ConnectionError`
4. Автоматические повторные попытки с заданным интервалом при сбое подключения

## Улучшения обработки событий

В мультиаккаунтном режиме ко всем событиям автоматически добавляется информация об аккаунте:
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... другие поля события
}
```

Адаптер автоматически поддерживает маппинг `self_id → account_name`, поэтому `event.reply()` корректно маршрутизируется на аккаунт-источник без ручного указания аккаунта.

## Интерфейс управления

```python
# Получение информации обо всех аккаунтах
accounts = onebot.accounts

# Проверка состояния подключения аккаунтов
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# Динамическое включение/отключение аккаунта (требуется перезапуск адаптера)
onebot.accounts["test"].enabled = False
```

## Автоматический маппинг self_id

Адаптер автоматически устанавливает соответствие между OneBot `self_id` (QQ-номером) и `account_name` для обратной маршрутизации событий:

```python
# Выполняется автоматически внутри адаптера
# При получении события поле self.user_id заполняется значением bot_id
# Адаптер автоматически записывает: self_id("123456789") → account_name("main")

# Поэтому event.reply() может автоматически находить правильный аккаунт для отправки сообщений
@message.on_message()
async def handler(event):
    await event.reply("Автоматическая маршрутизация на правильный аккаунт")
```