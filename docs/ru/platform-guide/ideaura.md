# Документация по функционалу платформы RockyChat

IdeauraAdapter — это адаптер, построенный на основе API платформы RockyChat, объединяющий все модули функциональности платформы и предоставляющий единый интерфейс обработки событий и операций с сообщениями.

---

## Информация о документации

- Соответствующий модуль: ErisPulse-Ideaura
- Версия модуля: 4.0.1
- Ответственный: ErisPulse

## Основная информация

- **Описание платформы:** RockyChat (Хуафэн Кофе) — это платформа мгновенных сообщений
- **Название адаптера:** IdeauraAdapter
- **Поддержка нескольких аккаунтов:** Поддерживает настройку нескольких аккаунтов через Bot Token
- **Поддержка цепочки модификаторов:** Поддерживает цепочечные методы модификаторов, такие как `.At()`、`.AtAll()`、`.Reply()`、`.Command()`
- **Совместимость с OneBot12:** Поддерживает отправку сообщений в формате OneBot12

## Типы поддерживаемых сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:
```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

Поддерживаемые типы отправки сообщений:
- `.Text(text: str)` — отправка обычного текстового сообщения.
- `.Image(file, filename: str = None)` — отправка сообщения с изображением, поддержка bytes/URL/локальный путь.
- `.Video(file, filename: str = None)` — отправка сообщения с видео, поддержка bytes/URL/локальный путь.
- `.File(file, filename: str = None)` — отправка сообщения с файлом, поддержка bytes/URL/локальный путь.
- `.Voice(file, filename: str = None)` — отправка голосового сообщения (в виде файла).
- `.Face(face_id: str)` — отправка эмодзи (в виде текста).
- `.Markdown(text: str)` — отправка сообщения в формате Markdown.
- `.Html(html: str)` — отправка сообщения в формате HTML.
- `.Edit(message_id: str, text: str, content_type: str = "text")` — редактирование существующего сообщения.
- `.Recall(message_id: str)` — отмена отправки сообщения.

### Методы цепочечного синтаксиса (можно комбинировать)

Методы цепочечного синтаксиса возвращают `self`, поддерживают цепочечное использование, должны вызываться до окончательного метода отправки:

- `.At(user_id: str, name: str = None)` — упоминание пользователя.
- `.AtAll()` — упоминание всех участников.
- `.Reply(message_id: str)` — ответ на указанное сообщение.
- `.Command(command_id: str)` — запуск команды бота, используется совместно с методом отправки (отправка сообщения как указанной команды).

### Примеры цепочечного синтаксиса

```python
# Базовая отправка
await ideaura.Send.To("user", user_id).Text("Hello")

# Запуск команды бота
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# Упоминание пользователя
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# Упоминание нескольких пользователей
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# Ответ на сообщение
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("Ответ на сообщение")

# Ответ + упоминание
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("Ответ с упоминанием")
```

### Отправка в разные цели

```python
# Отправка в чат-комнату
await ideaura.Send.To("group", "chatroom").Text("Сообщение в чат-комнате")

# Отправка в тему
await ideaura.Send.To("group", "topic_id").Text("Сообщение в теме")

# Личное сообщение
await ideaura.Send.To("user", "user_id").Text("Личное сообщение")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость сообщений между платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Использование цепочечного синтаксиса
ob12_msg = [{"type": "text", "data": {"text": "Ответ на сообщение"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно непосредственно ожидать с помощью await для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "self": {...},            // Информация о себе (включает user_id)
    "message_id": "123456",  // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "ideaura_raw": {...}      // Исходные данные ответа
}
```

## Типы событий, специфичные для платформы

Необходимо использовать проверку `platform=="ideaura"` для использования функций данной платформы

### Основные различия

1. Специфичные типы событий:
    - Редактирование сообщения: ideaura_message_edit
    - Отмена сообщения: ideaura_message_recall
    - Пересылка сообщения: ideaura_message_forward
    - Прочтение сообщения: ideaura_message_read
    - Отказ в добавлении в друзья: ideaura_friend_rejected
    - Онлайн друга: ideaura_friend_online
    - Оффлайн друга: ideaura_friend_offline
    - Изменение статуса пользователя: ideaura_user_status_change
    - Сегмент пересланного сообщения: ideaura_forwarded
    - Сегмент отредактированного сообщения: ideaura_edited
    - Сегмент Markdown-сообщения: ideaura_markdown
    - Сегмент HTML-сообщения: ideaura_html
    - Сегмент сообщения с командой бота: ideaura_command
2. Расширенные поля:
    - Все специфичные поля имеют префикс `ideaura_`
    - Исходные данные сохраняются в поле `ideaura_raw`
    - `self.user_id` обозначает ID текущего пользователя

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

### Событие отмены сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "ID отменённого сообщения",
  "user_id": "ID отменившего",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "Время отмены",
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

### Событие онлайн друга

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

### Событие оффлайн друга

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
  "ideaura_previous_status": "Старый статус"
}
```

### Событие запроса на добавление в друзья

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "ID запросившего",
  "user_nickname": "Ник запросившего",
  "ideaura_request_id": "ID запроса",
  "ideaura_message": "Сообщение для проверки"
}
```

### Событие отказа в добавлении в друзья

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "ID отклонившего",
  "user_nickname": "Ник отклонившего",
  "ideaura_request_id": "ID запроса",
  "ideaura_requester_id": "ID запросившего",
  "ideaura_requester_name": "Ник запросившего"
}
```

### Сегмент пересланного сообщения (ideaura_forwarded)

При получении пересланного сообщения тип сегмента будет `ideaura_forwarded`:

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
| `forward_source_id` | string | ID исходного сообщения |
| `original_message_id` | string | ID исходного сообщения |

### Сегмент сообщения с командой бота (ideaura_command)

При активации команды бота тип сегмента будет `ideaura_command`:

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
                print(f"Пересланный сегмент, ID источника: {data['forward_source_id']}")

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
        print(f"Сообщение отменено: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"Друг онлайн: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"Изменение статуса пользователя: {status}")
```

## Расширения Event Mixin

Адаптер зарегистрировал следующие методы, специфичные для платформы, доступные только при `platform == "ideaura"`:

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_source_type()` | `str` | Тип источника сообщения (`chatroom`/`topic`/`private`) |
| `get_sender_name()` | `str` | Никнейм отправителя |
| `get_sender_avatar()` | `str` | URL аватара отправителя |
| `is_sender_bot()` | `bool` | Является ли отправитель ботом |
| `is_receiver_bot()` | `bool` | Является ли получатель ботом |
| `get_command_id()` | `str` | ID вызванной команды бота (при наличии, `ideaura_command_id`) |
| `get_command()` | `str` | Алиас для `get_command_id()` |
| `get_topic_name()` | `str` | Название темы |
| `get_message_type()` | `str` | Тип сообщения (normal/edited/forwarded/quoted) |
| `get_message_subtype()` | `str` | Подтип сообщения (text/image/video/file/markdown/html) |
| `is_self_message()` | `bool` | Является ли сообщение отправленным самим пользователем |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # Получение ID вызванной команды бота (если есть)
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"Получена команда: {cmd_id}")
```

## Многоаккаунтная конфигурация

### Описание конфигурации

IdeauraAdapter поддерживает одновременную конфигурацию и работу с несколькими аккаунтами с использованием **Bot Token** для аутентификации.

> [!WARNING]
> Начиная с версии 4.0.1 **удалён вход по почте и паролю**, теперь поддерживается только Bot Token. Bot Token можно получить на [открытом платформе MSCPO](https://open.mscpo.com/rockychat/bots) (начинается с `bot-token-`).

```toml
# config.toml
# Аккаунт 1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # API токен бота (обязательно)
enabled = true                   # Включить аккаунт (необязательно, по умолчанию true)

# Аккаунт 2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
enabled = true

# Необязательно: пользовательский адрес сервера
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**Описание параметров:**
- `token`: API токен бота (обязательно, начинается с `bot-token-`)
- `enabled`: Включить этот аккаунт (необязательно, по умолчанию true)

**Глобальные параметры конфигурации:**
- `base_url`: Адрес API сервера (необязательно, по умолчанию `https://api.mscpo.com/api/rockychat`)
- `ws_url`: Адрес WebSocket сервера (необязательно, по умолчанию официальный адрес кофейни Хуафэн)
- `heartbeat_interval`: Интервал отправки心跳 в секундах (необязательно, по умолчанию 30 секунд)

### Использование Send DSL для указания аккаунта

Можно указать, какой аккаунт использовать для отправки сообщений с помощью метода `Using()`:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Отправить сообщение с использованием имени аккаунта
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# Отправить сообщение с использованием user_id (автоматически сопоставляется с соответствующим аккаунтом)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# Если не указать, будет использован первый включённый аккаунт
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### Идентификатор аккаунта в событиях

Полученные события автоматически содержат информацию об аккаунте:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"Сообщение пришло с аккаунта: {account_id}")
```

---

## Описание дополнительных полей

- Все специфические поля идентифицируются с префиксом `ideaura_`, чтобы избежать конфликта с стандартными полями
- Исходные данные сохраняются в поле `ideaura_raw`, что позволяет получить доступ к полным исходным данным платформы
- `self.user_id` указывает идентификатор пользователя текущего авторизованного аккаунта
- `ideaura_source_type`: тип источника сообщения (`chatroom`/`topic`/`private`)
- `ideaura_sender_name`: имя пользователя-отправителя
- `ideaura_sender_avatar`: URL-адрес аватара отправителя
- `ideaura_sender_is_bot`: является ли отправитель ботом
- `ideaura_is_self`: является ли сообщение отправленным самим собой (сообщения от пользователя уже отфильтрованы)
- `ideaura_topic_name`: название темы
- `ideaura_message_type`: тип сообщения (normal/edited/forwarded/quoted)
- `ideaura_message_subtype`: подтип сообщения (text/image/video/file/markdown/html)

### Особенности обработки файлов

- Ограничение размера файла: 10 МБ (ограничено как при скачивании, так и при локальном чтении)
- Автоматическая детекция типа файла: определение фактического типа по магическим байтам заголовка файла
- Интеллектуальное определение имени файла: автоматическая корректировка бессмысленных расширений, таких как `.bin`/`.dat`/`.tmp`
- Поддержка трёх способов ввода файла: bytes, URL и локальный путь
- Автоматическое скачивание и загрузка файла по URL на сервер

### Поддерживаемые типы файлов

Определение типа файла по магическим байтам заголовка:

| Тип | Расширение |
|------|--------|
| Изображение | png, jpg, gif, webp |
| Видео | mp4, avi, flv |
| Аудио | mp3, wav, ogg |
| Документ | pdf, docx |

## Примечания

1. Адрес API-сервера по умолчанию: `https://api.mscpo.com/api/rockychat` (может быть изменён с помощью `base_url`); адрес WebSocket-сервера `wss://api-cofe.allons-y.uk:3009/mqtt` является фиксированным и не зависит от имени адаптера.
2. Адаптер использует WebSocket-соединение для получения событий, поддерживает автоматическое повторное подключение (фиксированная задержка 5 секунд).
3. Собственные отправленные сообщения (`isSelf: true`) автоматически фильтруются и не генерируют события.
4. Упоминание всех (`AtAll()`) требует прав администратора.
5. Ограничение на размер загружаемых файлов составляет 10 МБ.
6. Аудиофайлы отправляются как подтип `file` (платформа не различает отдельные типы аудио).
7. Эмодзи (`Face()`) отправляются в виде обычного текста.
8. При выходе из программы необходимо вызвать `shutdown()` для корректного освобождения ресурсов.