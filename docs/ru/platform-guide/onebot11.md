# Характеристики платформы OneBot11

OneBot11Adapter — это адаптер, основанный на протоколе OneBot V11.

---

## Информация о документации

- Версия соответствующего модуля: 4.0.0
- Разработчик: ErisPulse

## Основная информация

- Описание платформы: OneBot — это стандарт интерфейса для чат-ботов
- Название адаптера: OneBotAdapter
- Поддерживаемый протокол/версия API: OneBot V11
- Поддержка нескольких аккаунтов: Архитектура по умолчанию поддерживает несколько аккаунтов; возможность одновременной настройки и запуска нескольких аккаунтов OneBot
- Конфигурационный ключ: `OneBotAdapter`

## Типы поддерживаемой отправки сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# Использование учетной записи по умолчанию
await onebot.Send.To("group", group_id).Text("Hello World!")

# Отправка от указанной учетной записи
await onebot.Send.Using("main").To("group", group_id).Text("Сообщение от основной учетной записи")

# Цепочечные модификаторы: @пользователь + ответ
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Сообщение ответа")

# @всем участникам
await onebot.Send.To("group", group_id).AtAll().Text("Анонс")
```

### Базовые методы отправки

- `.Text(text: str)`: отправляет сообщение только с текстом.
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: отправляет изображение (поддерживаются URL, Base64 или байты).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`: отправляет голосовое сообщение.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: отправляет видеосообщение.
- `.Face(id: Union[str, int])`: отправляет QQ-эмоцию (стикер).
- `.File(file: Union[str, bytes], filename: str = "file.dat")`: отправляет файл (автоматическое определение типа).
- `.Raw_ob12(message: List[Dict], **kwargs)`: отправляет сообщение в формате OneBot12 (автоматически конвертируется в OB11).
- `.Recall(message_id: Union[str, int])`: отменяет отправленное сообщение.

### Методы управления группами

Следующие методы должны использоваться с `To("group", group_id)` для указания целевой группы:

- `.Kick(user_id, reject_add_request=False)`: исключает участника из группы.
- `.Ban(user_id, duration=1800)`: запрещает участнику отправлять сообщения (в секундах), 0 означает разрешение.
- `.WholeBan(enable=True)`: включает/отключает запрет всем участникам отправлять сообщения.
- `.SetAdmin(user_id, enable=True)`: назначает/снимает администратора.
- `.SetCard(user_id, card="")`: устанавливает имя участника в группе.
- `.SetGroupName(name)`: изменяет название группы.
- `.Leave(is_dismiss=False)`: покидает группу (группа может быть удалена).
- `.SetTitle(user_id, title="")`: устанавливает титул участника.
- `.SetPortrait(file)`: устанавливает аватар группы.

### Методы запросов

- `.GetMsg(message_id)`: получает содержимое сообщения.
- `.GetForwardMsg(id)`: получает пересланные сообщения.
- `.GetLoginInfo()`: получает информацию о текущем аккаунте.
- `.GetFriendList()`: получает список друзей.
- `.GetGroupInfo()` (требуется `To("group", group_id)`): получает информацию о группе.
- `.GetGroupList()`: получает список групп.
- `.GetGroupMemberInfo(user_id)` (требуется `To("group", group_id)`): получает информацию о участнике группы.
- `.GetGroupMemberList()` (требуется `To("group", group_id)`): получает список участников группы.

### Методы для друзей

- `.Like(user_id, times=1)`: отправляет лайк другу (максимум 10 раз).

### Методы цепочечных модификаторов (можно использовать комбинации)

Методы цепочечных модификаторов возвращают `self`, поддерживают цепочечный вызов и должны быть вызваны перед финальным методом отправки:

- `.At(user_id: Union[str, int], name: str = None)`: упоминает указанного пользователя (можно вызвать несколько раз).
- `.AtAll()`: упоминает всех участников.
- `.Reply(message_id: Union[str, int])`: отвечает на указанное сообщение.

### Примеры цепочечного вызова

```python
# Базовая отправка
await onebot.Send.To("group", 123456).Text("Привет")

# @один пользователь
await onebot.Send.To("group", 123456).At(789012).Text("Привет")

# @несколько пользователей
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("Привет всем")

# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# Лайк
await onebot.Send.Like(123456, times=10)

# Запрет участнику отправлять сообщения
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# Разрешение
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# Исключение участника
await onebot.Send.To("group", 123456).Kick(789012)

# Назначение администратора
await onebot.Send.To("group", 123456).SetAdmin(789012)

# Изменение названия группы
await onebot.Send.To("group", 123456).SetGroupName("Новое название")

# Получение информации о группе
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# Выбор учетной записи
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### Обработка не поддерживаемых типов

Если вызывается неопределенный метод отправки, адаптер вернет текстовое предупреждение:
```python
# Вызов несуществующего метода
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# Реальная отправка: "[Неизвестный тип отправки] Метод: SomeUnsupportedMethod, Аргументы: [...]"
```

## Запросы (Request DSL)

Адаптер предоставляет DSL для обработки запросов (друзья, группы) — подтверждение/отклонение.

### Упрощенные методы событий

Запросы поддерживают `event.approve()` и `event.reject()` для упрощения:

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

### Ручное использование Request DSL

```python
# Подтверждение запроса
await onebot.Request("flag_string").accept()

# Отклонение запроса
await onebot.Request("flag_string").reject()

# Выбор учетной записи
await onebot.Request("flag_string").Using("main").accept()
```

### Полный пример

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # Способ 1: Использование упрощенных методов
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

### Возвращаемые значения запросов

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}
```

## Отображение типов событий

### Стандартное отображение OB12

| OB11 исходный тип | Отображение detail_type | Описание |
|------------------|------------------------|----------|
| message_type: private | `private` | Личные сообщения |
| message_type: group | `group` | Групповые сообщения |
| request_type: friend | `friend` | Запросы на добавление в друзья |
| request_type: group | `group` | Запросы на вступление в группу |
| meta_event_type: heartbeat | `heartbeat` | Событие "сердцебиения" |
| notice_type: group_upload | `group_file_upload` | Загрузка файлов в группе |
| notice_type: group_admin | `group_admin_change` | Изменение статуса администратора |
| notice_type: group_increase | `group_member_increase` | Увеличение числа участников |
| notice_type: group_decrease | `group_member_decrease` | Уменьшение числа участников |
| notice_type: group_ban | `group_ban` | Запрет на отправку сообщений |
| notice_type: friend_add | `friend_increase` | Добавление в друзья |
| notice_type: friend_delete | `friend_decrease` | Удаление из друзей |
| notice_type: group_recall / friend_recall | `message_recall` | Отмена отправки сообщения |

### Платформенные события (префикс onebot11_)

| OB11 исходный тип | Отображение detail_type | Описание |
|------------------|------------------------|----------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | Жизненный цикл OneBot |
| notify + sub_type: honor | `onebot11_honor` | Изменение статуса в группе |
| notify + sub_type: poke | `onebot11_poke` | Клик по участнику |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | Победитель в групповом конверте |
| Неизвестный тип CQ-кода | Сегмент сообщения `onebot11_{type}` | Неизвестный CQ-код |

### Примеры событий

```json
// Запрос на добавление в друзья
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "Пожалуйста, добавьте меня",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// Событие "сердцебиения"
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

// Клик по участнику (платформенное событие)
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Победитель в групповом конверте (платформенное событие)
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// Изменение статуса в группе (платформенное событие)
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

- Все уникальные поля обозначены префиксом `onebot11_`
- Исходные сообщения CQ-кодов сохранены в поле `onebot11_raw_message`
- Исходные данные события сохранены в поле `onebot11_raw`
- CQ-коды в содержании сообщения конвертируются в соответствующие сегменты сообщения
- Сообщения ответов будут содержать сегмент сообщения типа `reply`
- Сообщения упоминаний будут содержать сегмент сообщения типа `mention`

## Расширенные методы событий

OneBot11 адаптер добавляет следующие методы к объекту событий:

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
|-------|----------------------------|----------|
| `get_raw_self_id()` | `str` | Получает исходный self_id (QQ-номер бота) |
| `get_sender_info()` | `dict` | Получает полную информацию о отправителе |
| `get_sender_role()` | `str` | Получает роль отправителя в группе |
| `get_sender_level()` | `int` | Получает уровень отправителя |
| `get_sender_title()` | `str` | Получает титул отправителя |
| `is_system_message()` | `bool` | Проверяет, является ли сообщение системным |

### Примеры использования

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("Администратор, привет!")

    title = event.get_sender_title()
    if title:
        await event.reply(f"Ваш титул: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "Неизвестно")
    level = event.get_sender_level()
    await event.reply(f"Никнейм: {nickname}, Уровень: {level}")
```

## Параметры конфигурации

OneBot11 адаптер использует архитектуру с несколькими аккаунтами, каждый из которых настраивается отдельно. Конфигурационный ключ: `OneBotAdapter`.

### Поля конфигурации аккаунта

| Поле | Тип | Обязательно | Значение по умолчанию | Описание |
|------|-----|-------------|------------------------|----------|
| `bot_id` | `str` | Да | `""` | QQ-номер бота, используется для идентификации аккаунта |
| `mode` | `str` | Нет | `"server"` | Режим работы: `"server"` (активно слушает) или `"client"` (подключается) |
| `url` | `str` | Нет | `"ws://127.0.0.1:3001"` | Адрес WebSocket для режима Client |
| `token` | `str` | Нет | `""` | Токен для аутентификации (для Client или Server) |
| `server_path` | `str` | Нет | `"/"` | Путь WebSocket для режима Server |
| `enabled` | `bool` | Нет | `true` | Включен ли аккаунт |
| `name` | `str` | Нет | `""` | Имя аккаунта (для удобства) |

### Встроенные значения по умолчанию

- Интервал повторного подключения: 30 секунд
- Тайм-аут вызова API: 30 секунд

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

Если не настроены аккаунты, адаптер создаст их автоматически:
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно дождаться для получения результата. Результаты соответствуют стандартизированным спецификациям возвращаемых значений адаптера ErisPulse:

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
# Выбор аккаунта
await onebot.Send.Using("main").To("group", 123456).Text("Сообщение от основной учетной записи")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# Вызов API
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### Приоритеты выбора аккаунта

Приоритеты при разрешении `account_id` в `call_api` и `Using()`:

1. Точное совпадение имени аккаунта
2. Совпадение `bot_id`
3. Совпадение любого `str` поля аккаунта
4. Возврат к первому включенному аккаунту

## Асинхронная обработка

OneBot11 адаптер использует асинхронный неблокирующий дизайн, чтобы гарантировать:

1. Отправка сообщений не блокирует цикл обработки событий
2. Множество одновременных операций отправки могут выполняться одновременно
3. Ответы API могут обрабатываться своевременно
4. Поддержание активности WebSocket-соединения
5. Обработка нескольких аккаунтов параллельно, каждый аккаунт работает независимо

## Обработка ошибок

Адаптер предоставляет надежную систему обработки ошибок:

1. Автоматическое повторное соединение при сбое сетевого подключения (поддерживается независимое повторное подключение для каждого аккаунта, с интервалом 30 секунд)
2. Обработка тайм-аутов вызова API (фиксированный тайм-аут 30 секунд)
3. Повторная попытка отправки при сбое сообщения (максимум 3 попытки)

## Улучшение обработки событий

В режиме множественных учетных записей все события автоматически получают информацию об учетной записи:
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... другие поля событий
}
```

Адаптер автоматически поддерживает `self_id → account_name` маппинг, и `event.reply()` может отправлять сообщения обратно на правильный аккаунт без указания.

## Интерфейс управления

```python
# Получение информации обо всех учетных записях
accounts = onebot.accounts

# Проверка состояния подключения учетной записи
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# Динамическое включение/выключение учетной записи (требует перезапуска адаптера)
onebot.accounts["test"].enabled = false
```

## Автоматическое сопоставление self_id

Адаптер автоматически создает сопоставление `self_id` (QQ-номер) → `account_name` для корректного маршрутизирования событий:

```python
# Адаптер автоматически управляет сопоставлением
# При получении события, self.user_id заполняется bot_id
# Адаптер запоминает: self_id("123456789") → account_name("main")

# Поэтому event.reply() автоматически отправляет сообщение на правильный аккаунт
@message.on_message()
async def handler(event):
    await event.reply("Сообщение отправлено на правильный аккаунт")