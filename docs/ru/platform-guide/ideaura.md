# Документация по функциям платформы Ideaura (HuaFeng Coffeehouse)

IdeauraAdapter — это адаптер, построенный на API платформы HuaFeng Coffeehouse (Allons), интегрирующий все модули функций платформы и предоставляющий единый интерфейс для обработки событий и операций сообщений.

---

## Информация о документации

- Соответствующий модуль: ErisPulse-Ideaura
- Ответственный: ErisPulse

## Основная информация

- Краткое описание платформы: HuaFeng Coffeehouse (Allons) — это платформа мгновенного обмена сообщениями
- Название адаптера: IdeauraAdapter
- Поддержка нескольких аккаунтов: Поддерживает настройку нескольких аккаунтов через token или email/password
- Поддержка цепочечных модификаторов: Поддерживает цепочечные методы модификаторов, такие как `.At()`、`.AtAll()`、`.Reply()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочечную синтаксическую конструкцию, например:
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
- `.Voice(file, filename: str = None)` — отправка голосового сообщения (как файл).
- `.Face(face_id: str)` — отправка эмодзи (как чистый текст).
- `.Markdown(text: str)` — отправка сообщения в формате Markdown.
- `.Html(html: str)` — отправка сообщения в формате HTML.
- `.Edit(message_id: str, text: str, content_type: str = "text")` — редактирование существующего сообщения.
- `.Recall(message_id: str)` — отмена отправки сообщения.

### Цепочечные методы модификаторов (можно комбинировать)

Методы модификаторов возвращают `self`, поддерживают цепочечный вызов, должны вызываться перед окончательным методом отправки:

- `.At(user_id: str, name: str = None)` — упоминание указанного пользователя.
- `.AtAll()` — упоминание всех пользователей.
- `.Reply(message_id: str)` — ответ на указанное сообщение.

### Примеры цепочечного вызова

```python
# Базовая отправка
await ideaura.Send.To("user", user_id).Text("Hello")

# Упоминание пользователя
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# Упоминание нескольких пользователей
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@多人")

# Ответ на сообщение
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("回复消息")

# Ответ и упоминание
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("回复并@")
```

### Отправка в разные цели

```python
# Отправка в чат-комнату
await ideaura.Send.To("group", "chatroom").Text("聊天室消息")

# Отправка в тему
await ideaura.Send.To("group", "topic_id").Text("话题消息")

# Отправка личного сообщения
await ideaura.Send.To("user", "user_id").Text("私聊消息")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку OneBot12 форматированных сообщений, что облегчает совместимость сообщений между платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка OneBot12 форматированных сообщений.

```python
# Отправка OneBot12 форматированных сообщений
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# С цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно ожидать с помощью await для получения результата отправки. Возвращаемые результаты соответствуют стандартизированному формату возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "self": {...},            // Информация о себе (содержит user_id)
    "message_id": "123456",   // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "ideaura_raw": {...}      // Исходные данные ответа
}
```

## Уникальные типы событий

Необходимо использовать `platform=="ideaura"` для проверки перед использованием функций платформы

### Основные отличия

1. Уникальные типы событий:
    - Редактирование сообщения: ideaura_message_edit
    - Отмена отправки сообщения: ideaura_message_recall
    - Пересылка сообщения: ideaura_message_forward
    - Сообщение прочитано: ideaura_message_read
    - Запрос на добавление в друзья отклонен: ideaura_friend_rejected
    - Друг онлайн: ideaura_friend_online
    - Друг оффлайн: ideaura_friend_offline
    - Изменение статуса пользователя: ideaura_user_status_change
    - Сегмент пересланного сообщения: ideaura_forwarded
    - Сегмент отредактированного сообщения: ideaura_edited
    - Сегмент сообщения в формате Markdown: ideaura_markdown
    - Сегмент сообщения в формате HTML: ideaura_html
2. Расширенные поля:
    - Все уникальные поля имеют префикс `ideaura_`
    - Сохраняются исходные данные в поле `ideaura_raw`
    - `self.user_id` обозначает идентификатор текущего аккаунта пользователя

### Событие редактирования сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "Идентификатор сообщения",
  "user_id": "Идентификатор редактора",
  "ideaura_new_content": "Содержимое после редактирования",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### Событие отмены отправки сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "Идентификатор отмененного сообщения",
  "user_id": "Идентификатор отменяющего",
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
  "message_id": "Идентификатор исходного сообщения",
  "user_id": "Идентификатор пересылающего",
  "ideaura_forward_to": "Идентификатор целевой темы",
  "ideaura_original_message_id": "Идентификатор исходного сообщения",
  "ideaura_forwarded_message_id": "Идентификатор нового сообщения после пересылки"
}
```

### Событие прочитанного сообщения

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "Идентификатор сообщения",
  "ideaura_reader_id": "Идентификатор прочитавшего",
  "ideaura_reader_name": "Имя прочитавшего"
}
```

### Событие онлайн друга

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "Идентификатор друга",
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
  "user_id": "Идентификатор друга",
  "ideaura_presence_status": "offline"
}
```

### Событие изменения статуса пользователя

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "Идентификатор пользователя",
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
  "user_id": "Идентификатор запрашивающего",
  "user_nickname": "Имя запрашивающего",
  "ideaura_request_id": "Идентификатор запроса",
  "ideaura_message": "Сообщение проверки"
}
```

### Событие отклонения запроса на добавление в друзья

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "Идентификатор отклоняющего",
  "user_nickname": "Имя отклоняющего",
  "ideaura_request_id": "Идентификатор запроса",
  "ideaura_requester_id": "Идентификатор запрашивающего",
  "ideaura_requester_name": "Имя запрашивающего"
}
```

### Сегмент пересланного сообщения (ideaura_forwarded)

При получении пересланного сообщения тип сегмента сообщения будет `ideaura_forwarded`:

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
| `forward_source_id` | string | Идентификатор исходного сообщения |
| `original_message_id` | string | Идентификатор исходного сообщения |

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
        print(f"Сообщение отменено: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"Друг онлайн: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"Изменение статуса пользователя: {status}")
```

---

## Многоаккаунтная настройка

### Описание конфигурации

IdeauraAdapter поддерживает одновременную настройку и запуск нескольких аккаунтов, каждый аккаунт может выбрать вход по токену или по электронной почте и паролю (один из двух).

```toml
# config.toml
# Аккаунт 1: Вход по токену (рекомендуется, не требует электронной почты и пароля)
[IdeauraAdapter.accounts.default]
token = "your-token-here"        # Токен для входа (см. email+password, один из двух)
enabled = true                   # Включен ли аккаунт (опционально, по умолчанию true)

# Аккаунт 2: Вход по электронной почте и паролю
[IdeauraAdapter.accounts.bot2]
email = "user2@example.com"      # Электронная почта для входа
password = "password2"           # Пароль для входа
enabled = true

# Опционально: Настройка адреса сервера
[IdeauraAdapter]
base_url = "https://api-cofe.allons-y.uk:3009"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**Описание параметров конфигурации:**
- `token`: Токен для входа (опционально, при заполнении используется токен для входа, не требуется электронная почта и пароль)
- `email`: Электронная почта для входа (при входе по токену не требуется, при входе по электронной почте и паролю обязательна)
- `password`: Пароль для входа (при входе по токену не требуется, при входе по электронной почте и паролю обязательна)
- `enabled`: Включен ли аккаунт (опционально, по умолчанию true)

**Глобальные параметры конфигурации:**
- `base_url`: Адрес сервера API (опционально, по умолчанию адрес официального сервера HuaFeng Coffeehouse)
- `ws_url`: Адрес сервера WebSocket (опционально, по умолчанию адрес официального сервера HuaFeng Coffeehouse)
- `heartbeat_interval`: Интервал в секундах для心跳 (опционально, по умолчанию 30 секунд)

### Использование Send DSL для указания аккаунта

Можно использовать метод `Using()` для указания, какой аккаунт использовать для отправки сообщений:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# Отправка сообщения с использованием имени аккаунта
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# Отправка сообщения с использованием user_id (автоматически сопоставляется с соответствующим аккаунтом)
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# Без указания аккаунта используется первый включенный аккаунт
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### Идентификация аккаунта в событиях

События, полученные, автоматически содержат информацию об аккаунте:

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

- Все уникальные поля имеют префикс `ideaura_`, чтобы избежать конфликта с стандартными полями
- Сохраняются исходные данные в поле `ideaura_raw`, для удобного доступа к полным исходным данным платформы
- `self.user_id` обозначает идентификатор пользователя текущего входящего аккаунта
- `ideaura_source_type`: Тип источника сообщения (`chatroom`/`topic`/`private`)
- `ideaura_sender_name`: Имя отправителя
- `ideaura_sender_avatar`: URL аватара отправителя
- `ideaura_sender_is_bot`: Является ли отправитель ботом
- `ideaura_is_self`: Является ли сообщение отправленным самим собой (самосообщения отфильтрованы)
- `ideaura_topic_name`: Название темы
- `ideaura_message_type`: Тип сообщения (normal/edited/forwarded/quoted)
- `ideaura_message_subtype`: Подтип сообщения (text/image/video/file/markdown/html)

### Особенности обработки файлов

- Ограничение размера файлов: 10MB (ограничение на скачивание и локальное чтение)
- Автоматическая детекция типа файла: определение фактического типа по магическим байтам файла
- Интеллектуальное определение имени файла: автоматическая корректировка бессмысленных расширений, таких как `.bin`/`.dat`/`.tmp`
- Поддержка трех способов ввода файлов: bytes, URL, локальный путь
- Автоматическая загрузка и загрузка URL-файлов на сервер

### Поддерживаемые типы файлов

Определение типа файла по магическим байтам:

| Тип | Расширение |
|------|--------|
| Изображение | png, jpg, gif, webp |
| Видео | mp4, avi, flv |
| Аудио | mp3, wav, ogg |
| Документ | pdf, docx |

---

## Примечания

1. Адрес сервера `api-cofe.allons-y.uk` является адресом платформы, не меняется с изменением имени адаптера
2. Адаптер использует WebSocket-соединение для получения событий, поддерживает автоматическое повторное подключение (фиксированная задержка 5 секунд)
3. Сообщения, отправленные самим собой (`isSelf: true`), автоматически фильтруются и не генерируют события
4. Упоминание всех (`AtAll()`) требует прав администратора
5. Ограничение размера загружаемых файлов составляет 10MB
6. Аудиофайлы отправляются как подтип `file` (платформа не различает отдельные типы аудиофайлов)
7. Эмодзи (`Face()`) отправляются в виде чистого текста (эмодзи)
8. При выходе из программы необходимо вызвать `shutdown()` для освобождения ресурсов