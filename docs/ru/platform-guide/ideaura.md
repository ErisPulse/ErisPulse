# Документация по функциям платформы RockyChat (IdeauraAdapter)

IdeauraAdapter — это адаптер, построенный на API платформы RockyChat (花枫咖啡馆), объединяющий все модули функций платформы и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

## Информация о документации

- Соответствующий модуль: ErisPulse-Ideaura
- Версия модуля: 4.0.1
- Поддержка: ErisPulse

## Основная информация

- Описание платформы: RockyChat — это платформа для мгновенных сообщений
- Название адаптера: IdeauraAdapter
- Поддержка нескольких аккаунтов: Поддержка нескольких аккаунтов через конфигурацию Bot Token
- Поддержка цепных модификаторов: Поддержка цепных методов модификаторов, таких как `.At()`、`.AtAll()`、`.Reply()`、`.Command()`
- Совместимость с OneBot12: Поддержка отправки сообщений в формате OneBot12

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепной синтаксис, например:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка текстового сообщения.
- `.Image(file, filename: str = None)` — отправка изображения, поддержка bytes/URL/локального пути.
- `.Video(file, filename: str = None)` — отправка видео, поддержка bytes/URL/локального пути.
- `.File(file, filename: str = None)` — отправка файла, поддержка bytes/URL/локального пути.
- `.Voice(file, filename: str = None)` — отправка голосового сообщения (в виде файла).
- `.Face(face_id: str)` — отправка эмодзи (в виде текста).
- `.Markdown(text: str)` — отправка сообщения в формате Markdown.
- `.Html(html: str)` — отправка сообщения в формате HTML.
- `.Edit(message_id: str, text: str, content_type: str = "text")` — редактирование существующего сообщения.
- `.Recall(message_id: str)` — удаление сообщения.

### Цепные модификаторы (можно комбинировать)

Методы цепных модификаторов возвращают `self`, поддерживают цепное использование и должны вызываться перед окончательным методом отправки:

- `.At(user_id: str, name: str = None)` — упоминание определенного пользователя.
- `.AtAll()` — упоминание всех пользователей.
- `.Reply(message_id: str)` — ответ на определенное сообщение.
- `.Command(command_id: str)` — запуск команды бота, совместно с методом отправки (отправка сообщения как определенной команды).

### Примеры цепного вызова

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
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回复消息")

# Ответ + упоминание
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回复并@")
```

### Отправка в разные цели

```python
# Отправка в чат-комнату
await ideaura.Send.To("group", "chatroom").Text("聊天室消息")

# Отправка в топик
await ideaura.Send.To("group", "topic_id").Text("话题消息")

# Личное сообщение
await ideaura.Send.To("user", "user_id").Text("私聊消息")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку OneBot12 формата сообщений, что обеспечивает совместимость с другими платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка OneBot12 формата сообщений.

```python
# Отправка OneBot12 формата сообщений
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно ожидать с помощью await для получения результата отправки. Результат соответствует стандартизированному формату возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "self": {...},            // Информация о себе (включая user_id)
    "message_id": "123456",   // ID сообщения
    "message": "",            // Сообщение об ошибке
    "ideaura_raw": {...}      // Исходные данные ответа
}
```

## Уникальные типы событий

Необходимо проверять `platform=="ideaura"`, чтобы использовать особенности данной платформы

### Основные отличия

1. Уникальные типы событий:
    - Редактирование сообщения: ideaura_message_edit
    - Удаление сообщения: ideaura_message_recall
    - Пересылка сообщения: ideaura_message_forward
    - Прочтение сообщения: ideaura_message_read
    - Отказ в добавлении в друзья: ideaura_friend_rejected
    - Онлайн друга: ideaura_friend_online
    - Оффлайн друга: ideaura_friend_offline
    - Изменение статуса пользователя: ideaura_user_status_change
    - Сегмент пересланного сообщения: ideaura_forwarded
    - Сегмент отредактированного сообщения: ideaura_edited
    - Сегмент Markdown сообщения: ideaura_markdown
    - Сегмент HTML сообщения: ideaura_html
    - Сегмент команды бота: ideaura_command
2. Расширенные поля:
    - Все уникальные поля имеют префикс `ideaura_`
    - Сохраненные исходные данные находятся в поле `ideaura_raw`
    - `self.user_id` указывает ID текущего аккаунта пользователя

### Событие редактирования сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "ID сообщения",
  "user_id": "ID редактора",
  "ideaura_new_content": "Отредактированное содержимое",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### Событие удаления сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "ID удаленного сообщения",
  "user_id": "ID удалившего",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "Время удаления",
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
  "user_id": "ID пересылающего",
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
  "ideaura_reader_name": "Имя прочитавшего"
}
```

### Событие онлайн друга

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "ID друга",
  "user_nickname": "Имя друга",
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
  "user_id": "ID запрашивающего",
  "user_nickname": "Имя запрашивающего",
  "ideaura_request_id": "ID запроса",
  "ideaura_message": "Сообщение подтверждения"
}
```

### Событие отказа в добавлении в друзья

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "ID отказавшего",
  "user_nickname": "Имя отказавшего",
  "ideaura_request_id": "ID запроса",
  "ideaura_requester_id": "ID инициировавшего запрос",
  "ideaura_requester_name": "Имя инициировавшего запрос"
}
```

### Сегмент пересланного сообщения (ideaura_forwarded)

При получении пересланного сообщения тип сегмента — `ideaura_forwarded`:

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

### Сегмент команды бота (ideaura_command)

При активации команды бота тип сегмента — `ideaura_command`:

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
        # Обработка сообщений
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"Пересланные сообщения, исходный ID: {data['forward_source_id']}")

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
        print(f"Сообщение удалено: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"Друг онлайн: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"Изменение статуса пользователя: {status}")
```

## Расширенные методы Event Mixin

Адаптер зарегистрировал следующие методы, специфичные для платформы, доступные только при `platform == "ideaura"`:

| Метод | Возвращаемый тип | Описание |
|------|----------|------|
| `get_source_type()` | `str` | Тип источника сообщения (`chatroom`/`topic`/`private`) |
| `get_sender_name()` | `str` | Имя отправителя |
| `get_sender_avatar()` | `str` | URL аватара отправителя |
| `is_sender_bot()` | `bool` | Является ли отправитель ботом |
| `is_receiver_bot()` | `bool` | Является ли получатель ботом |
| `get_command_id()` | `str` | ID активированной команды бота (если есть, `ideaura_command_id`) |
| `get_command()` | `str` | Алиас `get_command_id()` |
| `get_topic_name()` | `str` | Название топика |
| `get_message_type()` | `str` | Тип сообщения (normal/edited/forwarded/quoted) |
| `get_message_subtype()` | `str` | Подтип сообщения (text/image/video/file/markdown/html) |
| `is_self_message()` | `bool` | Является ли сообщение отправленным самим |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # Получение ID активированной команды бота (если есть)
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"Получена команда: {cmd_id}")
```

---

## Многоконтурная конфигурация

### Описание конфигурации

IdeauraAdapter поддерживает одновременную конфигурацию и запуск нескольких аккаунтов с использованием **Bot Token** для аутентификации.

> [!WARNING]
> Начиная с версии 4.0.1 **удалена поддержка входа по почте и паролю**, используется только Bot Token. Bot Token можно получить на [открытом платформе MSCPO](https://open.mscpo.com/rockychat/bots) (начинается с `bot-token-`).

```toml
# config.toml
# Аккаунт 1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # API Token бота (обязательно)
enabled = true                   # Включить аккаунт (опционально, по умолчанию true)

# Аккаунт 2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
enabled = true

# Опционально: пользовательский адрес сервера
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**Описание параметров конфигурации:**
- `token`: API Token бота (обязательно, начинается с `bot-token-`)
- `enabled`: Включить аккаунт (опционально, по умолчанию true)

**Глобальные параметры конфигурации:**
- `base_url`: Адрес API сервера (опционально, по умолчанию `https://api.mscpo.com/api/rockychat`)
- `ws_url`: Адрес WebSocket сервера (опционально, по умолчанию адрес официального RockyChat)
- `heartbeat_interval`: Интервал в секундах для пинга (опционально, по умолчанию 30 секунд)

### Использование Send DSL для указания аккаунта

Можно использовать метод `Using()` для указания аккаунта, через который будет отправлено сообщение:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Отправка сообщения с указанием имени аккаунта
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# Отправка сообщения с указанием user_id (автоматически подбирается соответствующий аккаунт)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# Без указания аккаунта используется первый включенный аккаунт
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### Идентификатор аккаунта в событиях

Полученные события автоматически содержат информацию о соответствующем аккаунте:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"Сообщение от аккаунта: {account_id}")
```

---

## Описание расширенных полей

- Все уникальные поля имеют префикс `ideaura_`, чтобы избежать конфликтов с стандартными полями
- Исходные данные сохраняются в поле `ideaura_raw`, для доступа к полным исходным данным платформы
- `self.user_id` указывает ID текущего аккаунта пользователя
- `ideaura_source_type`: Тип источника сообщения (`chatroom`/`topic`/`private`)
- `ideaura_sender_name`: Имя отправителя
- `ideaura_sender_avatar`: URL аватара отправителя
- `ideaura_sender_is_bot`: Является ли отправитель ботом
- `ideaura_is_self`: Является ли сообщение отправленным самим (собственные сообщения отфильтрованы)
- `ideaura_topic_name`: Название топика
- `ideaura_message_type`: Тип сообщения (normal/edited/forwarded/quoted)
- `ideaura_message_subtype`: Подтип сообщения (text/image/video/file/markdown/html)

### Характеристики обработки файлов

- Ограничение размера файлов: 10 МБ (ограничение при загрузке и локальном чтении)
- Автоматическая детекция типа файла: определение фактического типа по магическим байтам файла
- Интеллектуальное определение имени файла: автоматическая корректировка расширений типа `.bin`/`.dat`/`.tmp` и т.д.
- Поддержка трех способов ввода файла: bytes, URL, локальный путь
- Автоматическая загрузка URL-файлов и последующая загрузка на сервер

### Поддерживаемые типы файлов

Определяются по магическим байтам:

| Тип | Расширение |
|------|--------|
| Изображение | png, jpg, gif, webp |
| Видео | mp4, avi, flv |
| Аудио | mp3, wav, ogg |
| Документ | pdf, docx |

---

## Примечания

1. Адрес API сервера по умолчанию — `https://api.mscpo.com/api/rockychat` (можно изменить с помощью `base_url`); адрес WebSocket `wss://api-cofe.allons-y.uk:3009/mqtt` — это адрес платформы, не меняется с изменением имени адаптера
2. Адаптер использует WebSocket для получения событий, поддерживает автоматическое повторное подключение (фиксированная задержка 5 секунд)
3. Сообщения, отправленные самим ботом (`isSelf: true`), автоматически фильтруются и не генерируют события
4. Упоминание всех пользователей (`AtAll()`) требует прав администратора
5. Ограничение размера загружаемого файла — 10 МБ
6. Аудиофайлы отправляются как подтип `file` (платформа не различает отдельные типы аудиофайлов)
7. Эмодзи (`Face()`) отправляются в виде текста (как emoji)
8. При завершении программы необходимо вызвать `shutdown()` для корректного освобождения ресурсов