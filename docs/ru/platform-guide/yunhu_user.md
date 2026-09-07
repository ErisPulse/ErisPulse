# Характеристики платформы пользователей Yunhu

YunhuUserAdapter представляет собой адаптер, построенный на основе протокола учетных записей пользователей Yunhu. Он обеспечивает вход пользователя по электронной почте, получение событий через WebSocket и предоставляет единый интерфейс для обработки событий и операций сообщений.

## Информация о документации

- Соответствующая версия модуля: 1.4.0
- Ответственный: wsu2059

## Основная информация

- Краткое описание платформы: Yunhu (云湖) - это корпоративная платформа мгновенного обмена сообщениями. Данный адаптер взаимодействует с платформой через **пользовательские аккаунты** (а не аккаунты ботов)
- Название адаптера: YunhuUserAdapter
- Поддержка нескольких аккаунтов: Поддерживает идентификацию и настройку нескольких пользовательских аккаунтов по имени аккаунта
- Поддержка цепочки методов: Поддерживает цепочечные методы, такие как `.Reply()`
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12
- Способ связи: Авторизация через электронную почту для получения токена, получение событий через WebSocket, отправка сообщений через HTTP + Protobuf
- Типы сессий: Поддерживает личные сообщения (user), групповые чаты (group), сессии бота (bot)

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str, buttons: Optional[List] = None)` — отправка обычного текстового сообщения.
- `.Html(html: str, buttons: Optional[List] = None)` — отправка сообщения в формате HTML.
- `.Markdown(markdown: str, buttons: Optional[List] = None)` — отправка сообщения в формате Markdown.
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с изображением, поддержка URL, локальных путей или двоичных данных.
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с видео, поддержка URL, локальных путей или двоичных данных.
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с аудио, поддержка URL, локальных путей или двоичных данных, автоматическое определение продолжительности аудио.
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)` — псевдоним для `.Audio()`.
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)` — отправка сообщения с файлом, поддержка URL, локальных путей или двоичных данных.
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с эмодзи/стикером, поддержка ID стикера, URL стикера или двоичных данных изображения.
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)` — отправка сообщения в формате A2UI (тип сообщения 14), данные A2UI в формате JSON будут отправлены в поле text.
- `.Edit(msg_id: str, text: str, content_type: str = "text")` — редактирование существующего сообщения.
- `.Recall(msg_id: str)` — удаление сообщения.
- `.Raw_ob12(message: Union[List, Dict])` — отправка сообщения в формате OneBot12.

### Обработка медиафайлов

Все типы медиа (изображения, видео, аудио, файлы) поддерживают следующие способы ввода:
- **URL**: `"https://example.com/image.jpg"` — автоматическая загрузка и последующая отправка
- **Локальный путь**: `"/path/to/file.jpg"` — автоматическое чтение и последующая отправка
- **Двоичные данные**: `open("file.jpg", "rb").read()` — прямая отправка

Медиафайлы автоматически загружаются в хранилище Qiniu, поддерживаются следующие функции:
- Автоматическое определение типа файла и MIME с помощью библиотеки `filetype`
- Автоматическое вычисление размера файла
- Автоматическое определение продолжительности аудиофайлов (поддержка форматов MP3, MP4/M4A)

### Описание параметра кнопок

Параметр `buttons` представляет собой вложенный список, описывающий расположение и функции кнопок. Каждый объект кнопки содержит следующие поля:

| Поле         | Тип   | Обязательно | Описание                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Да       | Текст на кнопке                                                         |
| `actionType` | int    | Да       | Тип действия:<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отправка события            |
| `url`        | string | Нет       | Используется, когда `actionType=1`, указывает целевой URL для перехода                         |
| `value`      | string | Нет       | Когда `actionType=2`, значение копируется в буфер обмена<br>Когда `actionType=3`, значение отправляется подписчику |

Пример:
```python
buttons = [
    [
        {"text": "Копировать", "actionType": 2, "value": "xxxx"},
        {"text": "Перейти по ссылке", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Отправить событие", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("Сообщение с кнопками")
```

### Методы цепочечного форматирования (можно комбинировать)

Методы цепочечного форматирования возвращают `self`, поддерживают цепочечное использование и должны вызываться до окончательного метода отправки:

- `.Reply(message_id: str)` — ответ на указанное сообщение.
- `.At(user_id: str)` — упоминание пользователя (в тексте @user_id).
- `.AtAll()` — упоминание всех (псевдо-упоминание всех, отправка текста @all).
- `.Buttons(buttons: List)` — добавление кнопок.

> **Примечание:** Поскольку учетная запись пользователя является особой, даже неадминистратор может упоминать всех, но `AtAll()` просто отправляет текст с упоминанием всех, это псевдоупоминание всех.

### Примеры цепочечного вызова

```python
# Базовая отправка
await yunhu_user.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("Ответ на сообщение")

# Ответ + кнопки
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Сообщение с ответом и кнопками")

# Указание аккаунта + ответ + кнопки
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Полный цепочечный вызов")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость сообщений между платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщений в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными методами
ob12_msg = [{"type": "text", "data": {"text": "Ответ на сообщение"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

`.Raw_ob12` поддерживает автоматическую группировку смешанных сообщений:
- Типы `text` и `mention` могут быть объединены в одну группу
- Типы `image`, `video`, `audio`, `file`, `face`, `markdown`, `html`, `a2ui` отправляются отдельными группами
- Тип `reply` может быть добавлен к любой группе

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно напрямую ожидать с помощью await, чтобы получить результат отправки. Возвращаемый результат соответствует стандартизированному формату ответа адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Ответные данные
    "message_id": "123456",   // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "yunhu_user_raw": {...}   // Необработанные данные ответа
}
```

## Специфические типы событий

Необходимо проверять `platform == "yunhu_user"`, чтобы использовать функции данной платформы.

### Основные отличия

1. Специфические типы событий:
    - Супер-файлы-раздача: `yunhu_user_file_send`
    - Доска объявлений бота: `yunhu_user_bot_board`
    - Уведомление об изменении сообщения: `message_edit`
    - Уведомление об удалении сообщения: `message_delete` (отмена отправки)
2. Специфические типы сообщений:
    - Форма сообщения: `yunhu_user_form`
    - Статья сообщения: `yunhu_user_post`
    - Наклейка сообщения: `yunhu_user_sticker`
    - Кнопка сообщения: `yunhu_user_button`
    - Сообщение A2UI: `a2ui`
3. Расширенные поля:
    - Все специфические поля имеют префикс `yunhu_user_`
    - Исходные данные сохраняются в поле `yunhu_user_raw`
    - Оригинальный тип события сохраняется в поле `yunhu_user_raw_type`
    - В личных сообщениях `self.user_id` указывает на ID текущего пользователя

### Поддерживаемые оригинальные типы событий

| Оригинальный тип события | Тип OneBot12 | Описание |
|-------------------------|--------------|----------|
| `push_message` | `message` | Отправка сообщения (личный чат, групповой чат, чат с ботом) |
| `edit_message` | `notice` (`message_edit`) | Событие редактирования сообщения |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Событие супер-файла-раздачи |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Событие доски объявлений бота |

> Другие типы событий (например, `heartbeat_ack`, `draft_input`, `stream_message` и т.д.) будут проигнорированы.

### Поддерживаемые detail_type OneBot12

| detail_type OneBot12 | chat_type yunhu | Описание |
|----------------------|----------------|----------|
| `private` | 1 | Личное сообщение |
| `group` | 2 | Групповое сообщение |
| `bot` | 3 | Чат с ботом |

### Примеры событий сообщений

```python
{
    "id": "event_id",
    "time": 1234567890,
    "type": "message",
    "detail_type": "group",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message": [
        {"type": "text", "data": {"text": "Содержание сообщения"}}
    ],
    "alt_message": "Содержание сообщения",
    "user_id": "sender_user_id",
    "user_nickname": "Имя отправителя",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### Пример уведомления об изменении сообщения

```python
{
    "type": "notice",
    "detail_type": "message_edit",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message_id": "msg_id",
    "user_id": "sender_user_id",
    "user_nickname": "Имя отправителя",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### Пример события супер-файла-раздачи

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_file_send",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "user_id": "send_user_id",
    "user_nickname": "",
    "yunhu_user_file_send": {
        "send_user_id": "ID отправителя",
        "user_id": "ID получателя",
        "send_type": "Тип отправки",
        "data": "Данные файла"
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "file_send_message"
}
```

### Пример события доски объявлений бота

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_bot_board",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "bot_id": "bot_id",
    "bot_name": "Имя бота",
    "yunhu_user_bot_board": {
        "bot_id": "bot_id",
        "chat_id": "chat_id",
        "chat_type": 1,
        "content": "Содержание объявления",
        "content_type": 1,
        "last_update_time": 1234567890
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "bot_board_message"
}
```

### Пример обработки событий

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_yunhu_user_message(event):
    """Обработка сообщений пользователя yunhu"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"Пользователь {user_nickname}({user_id}): {alt_message}")
    
    # Проверка специфических типов сообщений
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"Получено сообщение-форма: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"Получено сообщение-статья: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"Получено сообщение-наклейка: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"Сообщение содержит кнопки: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"Получено сообщение A2UI: {a2ui_data}")
    
    # Автоматическая отправка ответа
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """Обработка уведомлений пользователя yunhu"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"Пользователь {user_nickname} изменил сообщение {message_id}")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"Получено сообщение супер-файла-раздачи: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"Бот {bot_name} опубликовал объявление: {board_data.get('content', '')}")
```

## Описание расширенных полей

- Все уникальные поля идентифицируются с префиксом `yunhu_user_`, чтобы избежать конфликта с стандартными полями
- Исходные данные сохраняются в поле `yunhu_user_raw`, что позволяет получить доступ к полным исходным данным платформы Yunhu
- Тип исходного события записывается в поле `yunhu_user_raw_type` (например, `push_message`, `edit_message` и т.д.)
- `self.user_id` представляет идентификатор текущего пользователя (получается из ответа на вход)
- Обмен суперфайлов осуществляется через поле `yunhu_user_file_send`, которое содержит данные о файле
- Данные для доски объявлений бота предоставляются через поле `yunhu_user_bot_board`

### Типы уникальных сегментов сообщений

#### Сегмент сообщения формы (yunhu_user_form)

Когда `content_type` равен 5, тип сегмента сообщения — `yunhu_user_form`:

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "Данные формы"
    }
}
```

#### Сегмент сообщения статьи (yunhu_user_post)

Когда `content_type` равен 6, тип сегмента сообщения — `yunhu_user_post`:

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "Идентификатор статьи",
        "post_title": "Заголовок статьи",
        "post_content": "Содержание статьи"
    }
}
```

| Поле | Тип | Описание |
|------|------|------|
| `post_id` | string | Уникальный идентификатор статьи |
| `post_title` | string | Заголовок статьи |
| `post_content` | string | Содержание статьи |

#### Сегмент сообщения стикера (yunhu_user_sticker)

Когда `content_type` равен 7, тип сегмента сообщения — `yunhu_user_sticker`:

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "URL изображения стикера"
    }
}
```

| Поле | Тип | Описание |
|------|------|------|
| `file_id` | string | URL изображения стикера |

#### Сегмент сообщения кнопки (yunhu_user_button)

При наличии кнопок в сообщении добавляется сегмент `yunhu_user_button`:

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "Текст кнопки", "actionType": 3, "value": "Значение"}]]
    }
}
```

#### Сегмент сообщения A2UI (a2ui)

Когда `content_type` равен 14, тип сегмента сообщения — `a2ui`:

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "JSON-данные A2UI"
    }
}
```

---

## Многоаккаунтная конфигурация

### Описание конфигурации

YunhuUserAdapter поддерживает одновременную настройку и работу нескольких пользовательских аккаунтов.

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # Интервал переподключения WebSocket (секунды)
ws_timeout = 70             # Время ожидания WebSocket (секунды)

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # Электронная почта пользователя (обязательно)
password = "password1"       # Пароль пользователя (обязательно)
platform = "windows"         # Идентификатор платформы (опционально, по умолчанию windows)
device_id = ""               # Идентификатор устройства (опционально, генерируется автоматически)
enabled = true               # Включен ли аккаунт (опционально, по умолчанию true)

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**Описание параметров:**
- `email`: Электронная почта пользователя (обязательно), используется для входа в платформу Yunhu
- `password`: Пароль пользователя (обязательно)
- `platform`: Идентификатор платформы (опционально, по умолчанию `windows`), возможные значения: `windows`, `macos`, `linux`, `ios`, `android`
- `device_id`: Идентификатор устройства (опционально, генерируется автоматически), рекомендуется использовать фиксированное значение для поддержания консистентности сессии
- `enabled`: Включен ли аккаунт (опционально, по умолчанию `true`)

**Конфигурация уровня адаптера:**
- `ws_reconnect_interval`: Интервал переподключения WebSocket (секунды, по умолчанию 30)
- `ws_timeout`: Время ожидания WebSocket (секунды, по умолчанию 70)

**Важное уведомление:**
1. Адаптер использует электронную почту для входа и получения токена, после чего получает события через WebSocket
2. При разрыве соединения WebSocket будет автоматически переподключаться, максимум 3 попытки
3. Рекомендуется назначать каждому аккаунту фиксированный `device_id` для поддержания консистентности сессии
4. Аккаунты с неизменёнными шаблонными данными (стандартные почта и пароль) будут автоматически пропущены

### Использование Send DSL для указания аккаунта

Можно использовать метод `Using()` для указания аккаунта, через который будут отправлены сообщения. Этот метод поддерживает два типа параметров:
- **Имя аккаунта**: Название аккаунта из конфигурации (например, `default`, `account2`)
- **user_id**: Идентификатор пользователя, полученный после входа

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# Использование имени аккаунта для отправки сообщения
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# Использование user_id для отправки сообщения (автоматически подбирает соответствующий аккаунт)
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# Без указания аккаунта используется первый включённый аккаунт
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **Подсказка:** При использовании `user_id` система автоматически находит соответствующий аккаунт из конфигурации. Это особенно полезно при обработке ответов на события, где можно использовать `event["self"]["user_id"]` для ответа от того же аккаунта.

### Идентификатор аккаунта в событиях

Получаемые события автоматически содержат информацию об идентификаторе пользователя:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # Получение идентификатора текущего пользователя
        my_user_id = event["self"]["user_id"]
        print(f"Сообщение получено от аккаунта: {my_user_id}")
        
        # Ответ от того же аккаунта
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответ на сообщение")
```

### Информация в журнале

Адаптер автоматически включает информацию об аккаунте в журнал, что облегчает отладку и отслеживание:

```
[INFO] Аккаунт default (user1@example.com) успешно вошёл, идентификатор пользователя: 12345678
[INFO] Аккаунт default WebSocket задача прослушивания запущена
[INFO] Аккаунт account2 (user2@example.com) успешно вошёл, идентификатор пользователя: 87654321
```

### Интерфейс управления

```python
# Получение информации обо всех аккаунтах
accounts = yunhu_user.accounts
# Формат ответа: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# Проверка, включен ли аккаунт
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# Получение HTTP-клиента по имени аккаунта
http_client = yunhu_user._get_http_client("default")

# Поиск аккаунта по user_id
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API вызовы

Адаптер предоставляет метод `call_api`, который поддерживает прямой вызов API платформы:

```python
# Отправка сообщения
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Привет", "msg_type": 1}
)

# Редактирование сообщения
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="Новое содержимое",
    content_type="text"
)

# Отмена сообщения
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# Пакетная отмена сообщений
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# Получение списка сообщений
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# Получение истории редактирования сообщений
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# Отчет о событии кнопки
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**Поддерживаемые API эндпоинты:**

| Эндпоинт | Описание |
|------|------|
| `/send` | Отправка сообщения |
| `/edit` | Редактирование сообщения |
| `/recall` | Отмена сообщения |
| `/recall_batch` | Пакетная отмена сообщений |
| `/list` | Получение списка сообщений |
| `/list_by_seq` | Получение сообщений по последовательности |
| `/list_by_mid_seq` | Получение сообщений по ID сообщения и последовательности |
| `/list_edit_record` | Получение истории редактирования сообщений |
| `/button_report` | Отчет о событии кнопки |