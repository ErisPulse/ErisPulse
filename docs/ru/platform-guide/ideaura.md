# Документация по функциям платформы RockyChat (HuaFeng Coffee Shop)

IdeauraAdapter — это адаптер, построенный на основе API платформы RockyChat (HuaFeng Coffee Shop), объединяющий все модули функций платформы и предоставляющий единый интерфейс для обработки событий и операций с сообщениями.

---

Переход к документации: [**Русский**](docs/ru/quick-start.md)

## Информация о документации

- Соответствующий модуль: ErisPulse-Ideaura
- Версия модуля: 4.0.1
- Ответственный: ErisPulse

Вернуться к [**Содержание**](docs/ru/README.ru.md) | [**ErisPulse-Ideaura**](docs/ru/README.ru.md)

## Основная информация

- **Описание платформы:** RockyChat — это платформа для мгновенных сообщений
- **Название адаптера:** IdeauraAdapter
- **Поддержка нескольких аккаунтов:** Поддержка настройки нескольких аккаунтов через Bot Token
- **Поддержка цепочки модификаторов:** Поддержка цепочки методов модификаторов, таких как `.At()`、`.AtAll()`、`.Reply()`、`.Command()` и т.д.
- **Совместимость с OneBot12:** Поддержка отправки сообщений в формате OneBot12

[**Руководство по быстрому запуску**](docs/ru/quick-start.md)

## Типы поддерживаемых сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка чистого текстового сообщения.
- `.Image(file, filename: str = None)` — отправка сообщения с изображением, поддерживает bytes/URL/локальный путь.
- `.Video(file, filename: str = None)` — отправка сообщения с видео, поддерживает bytes/URL/локальный путь.
- `.File(file, filename: str = None)` — отправка сообщения с файлом, поддерживает bytes/URL/локальный путь.
- `.Voice(file, filename: str = None)` — отправка голосового сообщения (в виде файла).
- `.Face(face_id: str)` — отправка эмодзи (в виде чистого текста).
- `.Markdown(text: str)` — отправка сообщения в формате Markdown.
- `.Html(html: str)` — отправка сообщения в формате HTML.
- `.Edit(message_id: str, text: str, content_type: str = "text")` — редактирование существующего сообщения.
- `.Recall(message_id: str)` — отмена отправки сообщения.

### Методы цепочной модификации (можно комбинировать)

Методы цепочной модификации возвращают `self`, поддерживают цепочечное использование и должны вызываться перед окончательным методом отправки:

- `.At(user_id: str, name: str = None)` — упоминание конкретного пользователя.
- `.AtAll()` — упоминание всех пользователей.
- `.Reply(message_id: str)` — ответ на конкретное сообщение.
- `.Command(command_id: str)` — активация команды бота, используется в сочетании с методом отправки (сообщение отправляется как указанная команда).

### Примеры цепочечного вызова

```python
# Базовая отправка
await ideaura.Send.To("user", user_id).Text("Hello")

# Активация команды бота
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

### Отправка на разные цели

```python
# Отправка в чат-комнату
await ideaura.Send.To("group", "chatroom").Text("聊天室消息")

# Отправка в тему
await ideaura.Send.To("group", "topic_id").Text("话题消息")

# Личное сообщение
await ideaura.Send.To("user", "user_id").Text("私聊消息")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость сообщений между платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными методами
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно непосредственно ожидать, чтобы получить результат отправки. Возвращаемый результат соответствует стандартизированному спецификации возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Ответные данные
    "self": {...},            // Информация об авторе (содержит user_id)
    "message_id": "123456",   // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "ideaura_raw": {...}      // Исходные ответные данные
}
```

[**English**](docs/ru/quick-start.md) | [**Русский**](docs/ru/quick-start.md)

## Специфические типы событий

Необходимо использовать проверку `platform=="ideaura"` для использования функций этой платформы

### Основные отличия

1. Специфические типы событий:
    - Редактирование сообщения: ideaura_message_edit
    - Отзыв сообщения: ideaura_message_recall
    - Пересылка сообщения: ideaura_message_forward
    - Сообщение прочитано: ideaura_message_read
    - Друг отклонен: ideaura_friend_rejected
    - Друг онлайн: ideaura_friend_online
    - Друг оффлайн: ideaura_friend_offline
    - Изменение статуса пользователя: ideaura_user_status_change
    - Сегмент пересылаемого сообщения: ideaura_forwarded
    - Сегмент редактирования: ideaura_edited
    - Сегмент Markdown сообщения: ideaura_markdown
    - Сегмент HTML сообщения: ideaura_html
    - Сегмент команды бота: ideaura_command
2. Расширенные поля:
    - Все специфические поля имеют префикс `ideaura_`
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

### Событие отзыва сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "ID отзываемого сообщения",
  "user_id": "ID отзывающего",
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
  "user_id": "ID пересылающего",
  "ideaura_forward_to": "ID целевого топика",
  "ideaura_original_message_id": "ID исходного сообщения",
  "ideaura_forwarded_message_id": "ID нового сообщения после пересылки"
}
```

### Событие прочитанного сообщения

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

### Событие запроса друга

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "ID запроса",
  "user_nickname": "Имя запроса",
  "ideaura_request_id": "ID запроса",
  "ideaura_message": "Сообщение проверки"
}
```

### Событие отклонения друга

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "ID отклоняющего",
  "user_nickname": "Имя отклоняющего",
  "ideaura_request_id": "ID запроса",
  "ideaura_requester_id": "ID инициатора запроса",
  "ideaura_requester_name": "Имя инициатора запроса"
}
```

### Сегмент пересылаемого сообщения (ideaura_forwarded)

При получении пересылаемого сообщения, тип сегмента будет `ideaura_forwarded`:

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
| `original_message_id` | string | ID оригинального сообщения |

### Сегмент команды бота (ideaura_command)

При активации команды бота, тип сегмента будет `ideaura_command`:

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
                print(f"Пересылка сообщения, ID источника: {data['forward_source_id']}")

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
        print(f"Друг онлайн: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"Изменение статуса пользователя: {status}")

## Event Mixin расширения методов

Адаптер зарегистрировал следующие методы, специфичные для платформы, доступные только при `platform == "ideaura"`:

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_source_type()` | `str` | Тип источника сообщения (`chatroom`/`topic`/`private`) |
| `get_sender_name()` | `str` | Псевдоним отправителя |
| `get_sender_avatar()` | `str` | URL аватара отправителя |
| `is_sender_bot()` | `bool` | Является ли отправитель ботом |
| `is_receiver_bot()` | `bool` | Является ли получатель ботом |
| `get_command_id()` | `str` | ID активированной команды бота (если есть, `ideaura_command_id`) |
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

    # Получить ID активированной команды бота (если есть)
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"Получена команда: {cmd_id}")
```

---

docs/ru/quick-start.md

## Многоаккаунтная настройка

### Инструкции по настройке

IdeauraAdapter поддерживает одновременную конфигурацию и работу с несколькими аккаунтами, используя аутентификацию по **Bot Token**.

> [!WARNING]
> Начиная с версии 4.0.1 **удалена** аутентификация по электронной почте и паролю, теперь поддерживается только Bot Token. Bot Token можно получить на [открытом платформе MSCPO](https://open.mscpo.com/rockychat/bots) (начинается с `bot-token-`).

```toml
# config.toml
# Аккаунт 1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # API Token бота (обязательно)
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
- `token`: API Token бота (обязательно, начинается с `bot-token-`)
- `enabled`: Включить аккаунт (необязательно, по умолчанию true)

**Глобальные параметры:**
- `base_url`: Адрес API-сервера (необязательно, по умолчанию `https://api.mscpo.com/api/rockychat`)
- `ws_url`: Адрес WebSocket-сервера (необязательно, по умолчанию официальный адрес для Цветущего Кофейни)
- `heartbeat_interval`: Интервал отправки пингов в секундах (необязательно, по умолчанию 30 секунд)

### Использование Send DSL для указания аккаунта

Можно указать, какой аккаунт использовать для отправки сообщений с помощью метода `Using()`:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Отправка сообщения с использованием имени аккаунта
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# Отправка сообщения с использованием user_id (автоматически подбирается соответствующий аккаунт)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# Если не указано, используется первый включенный аккаунт
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### Идентификация аккаунта в событиях

Полученные события автоматически содержат информацию о соответствующем аккаунте:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["user_id"]
        print(f"Сообщение пришло от аккаунта: {account_id}")

## Описание расширенных полей

- Все специфические поля идентифицируются с префиксом `ideaura_`, чтобы избежать конфликтов со стандартными полями
- Оригинальные данные сохраняются в поле `ideaura_raw`, что позволяет получить доступ к полным исходным данным платформы
- `self.user_id` обозначает ID текущего авторизованного пользователя
- `ideaura_source_type`: тип источника сообщения (`chatroom`/`topic`/`private`)
- `ideaura_sender_name`: никнейм отправителя
- `ideaura_sender_avatar`: URL аватара отправителя
- `ideaura_sender_is_bot`: является ли отправитель ботом
- `ideaura_is_self`: является ли сообщение отправленным самим собой (самосообщения были отфильтрованы)
- `ideaura_topic_name`: название темы
- `ideaura_message_type`: тип сообщения (normal/edited/forwarded/quoted)
- `ideaura_message_subtype`: подтип сообщения (text/image/video/file/markdown/html)

### Особенности обработки файлов

- Ограничение размера файла: 10 МБ (ограничение действует как при скачивании, так и при локальном чтении)
- Автоматическая детекция типа файла: определение фактического типа по магическим байтам заголовка
- Интеллектуальное определение имени файла: автоматическая корректировка бессмысленных расширений, таких как `.bin`/`.dat`/`.tmp`
- Поддержка трёх способов ввода файла: bytes, URL, локальный путь
- Автоматическая загрузка URL-файлов и последующая загрузка на сервер

### Поддерживаемые типы файлов

Определение типа файла по магическим байтам:

| Тип | Расширение |
|------|--------|
| Изображение | png, jpg, gif, webp |
| Видео | mp4, avi, flv |
| Аудио | mp3, wav, ogg |
| Документ | pdf, docx |

## Примечания

1. Адрес API-сервера по умолчанию: `https://api.mscpo.com/api/rockychat` (можно настроить с помощью `base_url`); адрес WebSocket `wss://api-cofe.allons-y.uk:3009/mqtt` является фиксированным адресом платформы и не изменяется в зависимости от имени адаптера
2. Адаптер использует WebSocket-длинные соединения для получения событий и поддерживает автоматическое повторное подключение (фиксированная задержка 5 секунд)
3. Сообщения, отправленные самим адаптером (`isSelf: true`), автоматически фильтруются и не генерируют события
4. Упоминание всех (`AtAll()`) требует прав администратора
5. Ограничение на размер загружаемых файлов составляет 10 МБ
6. Аудиофайлы отправляются как подтип `file` (платформа не различает отдельные типы аудио)
7. Эмодзи (`Face()`) отправляются в виде обычного текста
8. При выходе из программы необходимо вызвать `shutdown()` для корректного освобождения ресурсов