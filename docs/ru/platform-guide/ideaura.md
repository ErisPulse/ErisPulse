# Документация по возможностям платформы «Кафе Хуафэн» (RockyChat)

IdeauraAdapter — адаптер, построенный на основе API платформы «Кафе Хуафэн» (RockyChat), объединяющий все функциональные модули платформы и предоставляющий единый интерфейс обработки событий и операций с сообщениями.

---

## Информация о документе

- Соответствующий модуль: ErisPulse-Ideaura
- Версия модуля: 4.3.2
- Сопровождающий: ErisPulse
- Последнее обновление: 2026-11-10

## Основная информация

- О платформе: «Кафе Хуафэн» (RockyChat) — платформа для мгновенного обмена сообщениями
- Название адаптера: IdeauraAdapter
- Поддержка нескольких аккаунтов: поддерживается настройка нескольких аккаунтов через Bot Token
- Поддержка цепочечных модификаторов: поддерживаются цепочные методы-модификаторы, такие как `.At()`, `.AtAll()`, `.Reply()`, `.Command()`
- Совместимость с OneBot12: поддерживается отправка сообщений в формате OneBot12

## Стандартизация (4.3.2)

### События и аккаунты

1. **Инъекция `self.account_id` в события**: все события содержат имя аккаунта, который их породил; при использовании нескольких аккаунтов `event.reply()` автоматически выполняет отправку через соответствующий аккаунт
2. **Новое необязательное поле `bot_id` в конфигурации аккаунта**: `IdeauraAccountConfig` поддерживает `bot_id` для явного указания ID пользователя Bot, соответствующего аккаунту
3. **Добавление стандартного `request_id` в события заявок в друзья**: в события `friend_request` / `friend_event` на верхнем уровне добавлено поле `request_id` (совпадает со значением `ideaura_request_id`); одобрение событий доступно через `event.approve()` / `event.reject()`

Пример обработки заявки в друзья:

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_friend_request(event):
    if event.get("platform") != "ideaura":
        return
    # event["request_id"] совпадает со значением ideaura_request_id
    if event.get("detail_type") == "friend":
        await event.approve()    # Принять заявку в друзья
    # await event.reject()       # Отклонить заявку в друзья
```

Соглашения интерфейса соответствуют стандартам SDK: [Спецификация действий запросов и одобрений](../standards/request-action-spec.md).

### Спецификация действий и кодов ошибок

1. **Стандартные имена действий больше не пересылаются как HTTP-пути**: при передаче в `call_api` нереализованного стандартного имени действия (например, `get_self_info`) явно возвращается 10002, и оно больше не пересылается платформе как HTTP-путь; для вызовов HTTP-путей платформы необходимо использовать префикс `/api/`
2. Коды ошибок стандартизированы (все старые значения — прежние HTTP-коды состояний, `-1`, `34000` и т.д. — полностью удалены):

| retcode | Описание |
|---------|------|
| 0 | Успех |
| 33001 | Сетевая ошибка (исключение при запросе, тайм-аут и т.д.) |
| 34100 | Ошибка платформы (исходный ответ сохраняется в поле `ideaura_raw`) |
| 10002 | Неподдерживаемое действие / сегмент сообщения (нереализованные стандартные действия, сегменты смайлов Face и т.д.) |

### Спецификация Send

- Имя HTML-метода — `HTML` (`Html` — зарезервированный псевдоним)
- Сегмент `Face` возвращает результат с ошибкой 10002 (больше не понижается до отправки обычным текстом) и записывает warning в лог
- В Raw_ob12 неизвестные сегменты сообщений пропускаются с записью warning в лог; если не может быть обработан ни один сегмент сообщения, возвращается 10002

## Обновление парадигмы v5 (4.1.0)

- **Наследование BaseConverter**: общие поля конвертера формируются фреймворком через build_base_event
- **Привязка задач spawn_background**: задачи подключения аккаунтов переведены на runtime.spawn_background
- **Мягкая зависимость от фреймворка**: во время выполнения проверяется версия ErisPulse>=2.7.1 с выводом предупреждения; при запуске выводится лог с версией
- Интерфейс запросов Request DSL (`Request(request_id)`) отложен; одобрение заявок в друзья уже доступно через события `event.approve()` / `event.reject()` (см. «Стандартизация (4.3.2)»)


### Реализованные возможности платформы

- **События**: редактирование/отзыв/пересылка/прочтение сообщений (ideaura_message_*), заявки в друзья (friend_request), добавление/удаление друзей (friend_increase/decrease), статусы онлайн (friend_online/offline)
- **Отправка**: Text / Image / Markdown / Raw_ob12 (с цепочечными модификаторами Reply/At/AtAll)
- **Одобрение заявок в друзья**: с 4.3.2 поддерживается через события `event.approve()` / `event.reject()`
- **Не реализовано**: Api DSL (будет добавлено после открытия REST-интерфейса платформы), интерфейс запросов Request DSL

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочный синтаксис, например:
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`: отправка обычного текстового сообщения.
- `.Image(file, filename: str = None)`: отправка изображения, поддерживает bytes/URL/локальный путь.
- `.Video(file, filename: str = None)`: отправка видео, поддерживает bytes/URL/локальный путь.
- `.File(file, filename: str = None)`: отправка файла, поддерживает bytes/URL/локальный путь.
- `.Voice(file, filename: str = None)`: отправка голосового сообщения (отправляется как файл).
- `.Face(face_id: str)`: отправка смайла (с версии 4.3.2 **не поддерживается платформой**, возвращает retcode=10002 и пропускается, больше не понижается до текста).
- `.Markdown(text: str)`: отправка сообщения в формате Markdown.
- `.HTML(html: str)`: отправка сообщения в формате HTML (`Html` — зарезервированный псевдоним).
- `.MergeForward(nodes, title="Объединённая переписка")`: отправка объединённого пересылаемого сообщения (отрисовывается как сворачиваемая HTML-карточка `<details>`).
- `.Edit(message_id: str, text: str, content_type: str = "text")`: редактирование существующего сообщения.
- `.Recall(message_id: str)`: отзыв сообщения.

### Цепочные методы-модификаторы (можно комбинировать)

Цепочные методы-модификаторы возвращают `self` и поддерживают цепочные вызовы; их необходимо вызывать перед финальным методом отправки:

- `.At(user_id: str, name: str = None)`: упоминание указанного пользователя (@).
- `.AtAll()`: упоминание всех (@all).
- `.Reply(message_id: str)`: ответ на указанное сообщение.
- `.Command(command_id: str)`: вызов команды Bot, используется вместе с методом отправки (сообщение отправляется как указанная команда).

### Примеры цепочных вызовов

```python
# Базовая отправка
await ideaura.Send.To("user", user_id).Text("Hello")

# Вызов команды Bot
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather Пекин")

# Упоминание пользователя
await ideaura.Send.To("group", "chatroom").At("456").Text("@Ли Сы, привет")

# Упоминание нескольких пользователей
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@несколько человек")

# Ответ на сообщение
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("Ответ на сообщение")

# Ответ + упоминание
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("Ответ и @")

# Сообщение в формате HTML
await ideaura.Send.To("group", "chatroom").HTML("<p>HTML сообщение</p>")
```

### Отправка различным получателям

```python
# Отправка в чат-комнату
await ideaura.Send.To("group", "chatroom").Text("Сообщение в чат-комнате")

# Отправка в топик
await ideaura.Send.To("group", "topic_id").Text("Сообщение в топике")

# Отправка личного сообщения
await ideaura.Send.To("user", "user_id").Text("Личное сообщение")
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12, что упрощает кроссплатформенную совместимость сообщений:

- `.Raw_ob12(message: List[Dict], **kwargs)`: отправка сообщений в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответ на сообщение"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

> Неизвестные сегменты сообщений пропускаются с записью warning в лог; если не может быть обработан ни один сегмент сообщения, возвращается retcode=10002.

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, результат отправки можно получить напрямую через await. Возвращаемый результат соответствует стандартизированной спецификации возврата адаптеров ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата (0 — успех; коды ошибок см. «Стандартизация (4.3.2)»)
    "data": {...},            // Данные ответа
    "self": {...},            // Информация о себе (включая user_id)
    "message_id": "123456",   // ID сообщения
    "message": "",            // Сообщение об ошибке
    "ideaura_raw": {...}      // Исходные данные ответа
}
```

## Специфические типы событий

Для использования специфичных возможностей платформы требуется проверка `platform=="ideaura"`

### Ключевые отличия

1. Специфические типы событий:
    - Редактирование сообщения: ideaura_message_edit
    - Отзыв сообщения: ideaura_message_recall
    - Пересылка сообщения: ideaura_message_forward
    - Прочтение сообщения: ideaura_message_read
    - Отклонение заявки в друзья: ideaura_friend_rejected
    - Вход друга в сеть: ideaura_friend_online
    - Выход друга из сети: ideaura_friend_offline
    - Изменение статуса пользователя: ideaura_user_status_change
    - Сегмент пересланного сообщения: ideaura_forwarded
    - Сегмент отметки редактирования: ideaura_edited
    - Сегмент Markdown-сообщения: ideaura_markdown
    - Сегмент HTML-сообщения: ideaura_html
    - Сегмент команды Bot: ideaura_command
2. Расширенные поля:
    - Все специфические поля имеют префикс `ideaura_`
    - Исходные данные сохраняются в поле `ideaura_raw`
    - `self.user_id` в событии означает ID пользователя текущего аккаунта, `self.account_id` — имя аккаунта

### Событие редактирования сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "ID сообщения",
  "user_id": "ID редактора",
  "ideaura_new_content": "Содержимое после редактирования",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### Событие отзыва сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "ID отозванного сообщения",
  "user_id": "ID отозвавшего",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "Время отзыва",
  "ideaura_is_self": false
}
```

### Событие пересылки сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "ID исходного сообщения",
  "user_id": "ID переславшего",
  "ideaura_forward_to": "ID целевого топика",
  "ideaura_original_message_id": "ID исходного сообщения",
  "ideaura_forwarded_message_id": "ID нового сообщения после пересылки"
}
```

### Событие прочтения сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "ID сообщения",
  "ideaura_reader_id": "ID прочитавшего",
  "ideaura_reader_name": "Ник прочитавшего"
}
```

### Событие входа друга в сеть

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "ID друга",
  "user_nickname": "Ник друга",
  "ideaura_friend_avatar": "URL аватара",
  "ideaura_presence_status": "online"
}
```

### Событие выхода друга из сети

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_offline",
  "platform": "ideaura",
  "user_id": "ID друга",
  "ideaura_presence_status": "offline"
}
```

### Событие изменения статуса пользователя

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "ID пользователя",
  "ideaura_status": "Новый статус",
  "ideaura_previous_status": "Прежний статус"
}
```

### Событие заявки в друзья

С версии 4.3.2 на верхнем уровне добавлено стандартное поле `request_id` (совпадает со значением `ideaura_request_id`), одобрение доступно через `event.approve()` / `event.reject()`:

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "ID отправителя запроса",
  "user_nickname": "Ник отправителя запроса",
  "request_id": "ID запроса",
  "ideaura_request_id": "ID запроса",
  "ideaura_message": "Проверочное сообщение"
}
```

### Событие отклонения заявки в друзья

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "ID отклонившего",
  "user_nickname": "Ник отклонившего",
  "ideaura_request_id": "ID запроса",
  "ideaura_requester_id": "ID инициатора запроса",
  "ideaura_requester_name": "Ник инициатора запроса"
}
```

### Сегмент пересланного сообщения (ideaura_forwarded)

При получении пересланного сообщения тип сегмента сообщения — `ideaura_forwarded`:

```json
{
  "type": "ideaura_forwarded",
  "data": {
    "forward_source_id": "1001",
    "original_message_id": "1001"
  }
}
```

| Поле | Тип | Описание |
|------|------|------|
| `forward_source_id` | string | ID исходного сообщения пересылки |
| `original_message_id` | string | ID исходного сообщения |

### Сегмент команды Bot (ideaura_command)

Когда пользователь вызывает команду Bot, тип сегмента сообщения — `ideaura_command`:

```json
{
  "type": "ideaura_command",
  "data": {
    "command_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| Поле | Тип | Описание |
|------|------|------|
| `command_id` | string | UUID команды |

### Пример обработки событий

```python
from ErisPulse.Core.Event import notice, message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "ideaura":
        # Обработка событий сообщений
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"Пересланное сообщение, исходный ID: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"Сообщение отредактировано: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"Сообщение отозвано: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"Друг в сети: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"Изменение статуса пользователя: {status}")
```

## Расширенные методы Event Mixin

Адаптер регистрирует следующие специфичные для платформы методы, доступные только при `platform == "ideaura"`:

| Метод | Тип возврата | Описание |
|------|----------|------|
| `get_source_type()` | `str` | Тип источника сообщения (`chatroom`/`topic`/`private`) |
| `get_sender_name()` | `str` | Ник отправителя |
| `get_sender_avatar()` | `str` | URL аватара отправителя |
| `is_sender_bot()` | `bool` | Является ли отправитель ботом |
| `is_receiver_bot()` | `bool` | Является ли получатель ботом |
| `get_command_id()` | `str` | ID вызванной команды Bot (если есть, `ideaura_command_id`) |
| `get_command()` | `str` | Псевдоним `get_command_id()` |
| `get_topic_name()` | `str` | Название топика |
| `get_message_type()` | `str` | Тип сообщения (normal/edited/forwarded/quoted) |
| `get_message_subtype()` | `str` | Подтип сообщения (text/image/video/file/markdown/html) |
| `is_self_message()` | `bool` | Является ли сообщение отправленным собой |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # Получить ID вызванной команды Bot (если есть)
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"Получена команда: {cmd_id}")
```

---

## Конфигурация нескольких аккаунтов

### Описание конфигурации

IdeauraAdapter поддерживает одновременную настройку и запуск нескольких аккаунтов с аутентификацией через **Bot Token**.

> [!WARNING]
> С версии 4.0.1 **вход по электронной почте и паролю удалён**, поддерживается только Bot Token. Получить Bot Token можно на [открытой платформе MSCPO](https://open.mscpo.com/rockychat/bots) (начинается с `bot-token-`).

```toml
# config.toml
# Аккаунт 1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # API Token бота (обязательно)
bot_id = ""                      # ID пользователя Bot (необязательно, явное указание Bot, соответствующего аккаунту)
enabled = true                   # Включён ли аккаунт (необязательно, по умолчанию true)

# Аккаунт 2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
bot_id = ""
enabled = true

# Необязательно: пользовательский адрес сервера
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**Описание параметров конфигурации:**
- `token`: API Token бота (обязательно, начинается с `bot-token-`)
- `bot_id`: ID пользователя Bot (необязательно, поддерживается с 4.3.2, для явного указания Bot, соответствующего аккаунту)
- `enabled`: включён ли данный аккаунт (необязательно, по умолчанию true)

**Глобальные параметры конфигурации:**
- `base_url`: адрес API-сервера (необязательно, по умолчанию `https://api.mscpo.com/api/rockychat`)
- `ws_url`: адрес WebSocket-сервера (необязательно, по умолчанию — официальный адрес «Кафе Хуафэн»)
- `heartbeat_interval`: интервал heartbeat в секундах (необязательно, по умолчанию 30 секунд)

### Указание аккаунта через Send DSL

С помощью метода `Using()` можно указать, какой аккаунт использовать для отправки сообщений:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Отправка сообщения по имени аккаунта
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# Отправка сообщения по user_id (автоматический подбор соответствующего аккаунта)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# Если аккаунт не указан, используется первый включённый аккаунт
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### Идентификатор аккаунта в событиях

Полученные события автоматически содержат соответствующую информацию об аккаунте (с 4.3.2 `self.account_id` — имя аккаунта):

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["account_id"]
        print(f"Сообщение от аккаунта: {account_id}")
```

---

## Описание расширенных полей

- Все специфические поля имеют префикс `ideaura_` во избежание конфликтов со стандартными полями
- Исходные данные сохраняются в поле `ideaura_raw` для удобного доступа к полным исходным данным платформы
- `self.user_id` означает ID пользователя текущего вошедшего аккаунта, `self.account_id` — имя аккаунта
- `ideaura_source_type`: тип источника сообщения (`chatroom`/`topic`/`private`)
- `ideaura_sender_name`: ник отправителя
- `ideaura_sender_avatar`: URL аватара отправителя
- `ideaura_sender_is_bot`: является ли отправитель ботом
- `ideaura_is_self`: является ли сообщение отправленным собой (собственные сообщения отфильтровываются)
- `ideaura_topic_name`: название топика
- `ideaura_message_type`: тип сообщения (normal/edited/forwarded/quoted)
- `ideaura_message_subtype`: подтип сообщения (text/image/video/file/markdown/html)

### Особенности обработки файлов

- Ограничение размера файлов: 10 МБ (ограничение действует как при скачивании, так и при локальном чтении)
- Автоопределение типа файла: фактический тип определяется по магическим байтам заголовка файла
- Интеллектуальный разбор имён файлов: автоматическое исправление бессмысленных расширений, таких как `.bin`/`.dat`/`.tmp`
- Поддерживаются три способа задания файлов: bytes, URL и локальный путь
- Файлы по URL автоматически скачиваются и загружаются на сервер

### Поддерживаемые типы файлов

Автоматическое определение по магическим байтам:

| Тип | Расширения |
|------|--------|
| Изображения | png, jpg, gif, webp |
| Видео | mp4, avi, flv |
| Аудио | mp3, wav, ogg |
| Документы | pdf, docx |

---

## Важные замечания

1. Адрес API-сервера по умолчанию — `https://api.mscpo.com/api/rockychat` (можно настроить через `base_url`); адрес WebSocket `wss://api-cofe.allons-y.uk:3009/mqtt` является фиксированным адресом платформы и не меняется в зависимости от имени адаптера
2. Адаптер использует постоянное WebSocket-соединение для приёма событий и поддерживает автоматическое переподключение (фиксированная задержка 5 секунд)
3. Сообщения, отправленные самим ботом (`isSelf: true`), автоматически фильтруются и не порождают события
4. Упоминание всех (`AtAll()`) требует прав администратора
5. Ограничение размера загружаемых файлов — 10 МБ
6. Аудиофайлы отправляются как подтип `file` (платформа не выделяет отдельный аудио-тип)
7. Смайлы (`Face()`) не поддерживаются платформой, возвращается retcode=10002 и сегмент пропускается (больше не понижается до обычного текста)
8. При завершении программы вызывайте `shutdown()`, чтобы гарантировать освобождение ресурсов