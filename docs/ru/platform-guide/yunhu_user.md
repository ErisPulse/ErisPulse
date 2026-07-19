# Документация по функциям платформы Yunhu User

YunhuUserAdapter — это адаптер, построенный на основе протокола учетных записей Yunhu, который обеспечивает взаимодействие с платформой Yunhu через учетные записи пользователей (а не бота), используя веб-сокеты для получения событий и предоставляя унифицированные методы обработки событий и операций с сообщениями.

---

## Информация о документации

- Соответствующая версия модуля: 1.4.0
- Ответственный: wsu2059

## Основная информация

- Краткое описание платформы: Yunhu (云湖) — это корпоративная платформа мгновенного обмена сообщениями. Данный адаптер взаимодействует с ней через **учетные записи пользователей** (а не учетные записи бота).
- Название адаптера: YunhuUserAdapter
- Поддержка нескольких учетных записей: Поддерживает идентификацию и настройку нескольких учетных записей пользователей по имени учетной записи.
- Поддержка цепочечных модификаторов: Поддерживает цепочечные методы модификации, такие как `.Reply()`.
- Совместимость с OneBot12: Поддерживает отправку сообщений в формате OneBot12.
- Способ связи: Получение токена через вход по электронной почте, получение событий через WebSocket, отправка сообщений с использованием протокола HTTP + Protobuf.
- Типы сессий: Поддерживает личные сообщения (user), групповые сообщения (group), сессии бота (bot).

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечной синтаксиса, например:
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str, buttons: Optional[List] = None)` — отправка текстового сообщения.
- `.Html(html: str, buttons: Optional[List] = None)` — отправка HTML-форматированного сообщения.
- `.Markdown(markdown: str, buttons: Optional[List] = None)` — отправка Markdown-форматированного сообщения.
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с изображением, поддержка URL, локального пути или двоичных данных.
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с видео, поддержка URL, локального пути или двоичных данных.
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка аудиосообщения, поддержка URL, локального пути или двоичных данных, автоматическое определение длительности аудио.
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)` — псевдоним для `.Audio()`.
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)` — отправка сообщения с файлом, поддержка URL, локального пути или двоичных данных.
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с эмодзи/стикером, поддержка ID стикера, URL стикера или двоичных данных изображения.
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)` — отправка A2UI-сообщения (тип сообщения 14), A2UI JSON-данные будут отправлены в поле text.
- `.Edit(msg_id: str, text: str, content_type: str = "text")` — редактирование существующего сообщения.
- `.Recall(msg_id: str)` — отмена отправки сообщения.
- `.Raw_ob12(message: Union[List, Dict])` — отправка сообщения в формате OneBot12.

### Обработка медиафайлов

Все типы медиа (изображения, видео, аудио, файлы) поддерживают следующие способы ввода:
- **URL**: `"https://example.com/image.jpg"` — автоматическая загрузка и последующая загрузка на сервер
- **Локальный путь**: `"/path/to/file.jpg"` — автоматическое чтение и последующая загрузка на сервер
- **Двоичные данные**: `open("file.jpg", "rb").read()` — прямая загрузка на сервер

Медиафайлы автоматически загружаются на хранилище Qiniu Cloud и поддерживают следующие функции:
- Автоматическое определение типа файла и MIME с помощью библиотеки `filetype`
- Автоматическое вычисление размера файла
- Автоматическое определение длительности аудиофайла (поддержка форматов MP3, MP4/M4A)

### Описание параметра кнопок

Параметр `buttons` представляет собой вложенный список, описывающий макет и функции кнопок. Каждый объект кнопки содержит следующие поля:

| Поле         | Тип   | Обязательно | Описание                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Да       | Текст на кнопке                                                         |
| `actionType` | int    | Да       | Тип действия：<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отправка события            |
| `url`        | string | Нет       | Используется, когда `actionType=1`, указывает целевой URL для перехода                         |
| `value`      | string | Нет       | Когда `actionType=2`, значение будет скопировано в буфер обмена<br>Когда `actionType=3`, значение будет отправлено подписчикам |

Пример:
```python
buttons = [
    [
        {"text": "Копировать", "actionType": 2, "value": "xxxx"},
        {"text": "Перейти по ссылке", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Сообщить событие", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("Сообщение с кнопками")
```

### Цепочечные методы модификации (можно комбинировать)

Цепочечные методы модификации возвращают `self`, поддерживают цепочечные вызовы и должны вызываться до окончательного метода отправки:

- `.Reply(message_id: str)` — ответ на указанное сообщение.
- `.At(user_id: str)` — упоминание пользователя (в текстовом виде @user_id).
- `.AtAll()` — упоминание всех пользователей (псевдо-упоминание всех, отправка текста @all).
- `.Buttons(buttons: List)` — добавление кнопок.

> **Важно:** Поскольку учетные записи пользователей являются специальными, даже не администраторы могут упоминать всех, но здесь `AtAll()` будет отправлять только текст с упоминанием всех, это псевдо-упоминание всех.

### Примеры цепочечных вызовов

```python
# Основная отправка
await yunhu_user.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("Ответ на сообщение")

# Ответ + кнопки
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Сообщение с ответом и кнопками")

# Указание учетной записи + ответ + кнопки
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Полный цепочечный вызов")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12, что упрощает совместимость сообщений между платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщений в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными методами
ob12_msg = [{"type": "text", "data": {"text": "Ответ на сообщение"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 поддерживает автоматическую группировку смешанных сегментов сообщений:
- Типы `text` и `mention` могут быть объединены в одну группу
- Типы `image`, `video`, `audio`, `file`, `face`, `markdown`, `html`, `a2ui` отправляются отдельными группами
- Тип `reply` может быть прикреплен к любой группе

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно ожидать с помощью await для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "message_id": "123456",   // ID сообщения
    "message": "",            // Сообщение об ошибке
    "yunhu_user_raw": {...}   // Исходные данные ответа
}
```

## Уникальные типы событий

Необходимо использовать проверку `platform == "yunhu_user"`, чтобы использовать уникальные функции этой платформы

### Основные отличия

1. Уникальные типы событий:
    - Супер-файловый обмен: `yunhu_user_file_send`
    - Доска объявлений бота: `yunhu_user_bot_board`
    - Уведомление о редактировании сообщения: `message_edit`
    - Уведомление о удалении сообщения: `message_delete` (отмена отправки)
2. Уникальные типы сегментов сообщений:
    - Сегмент формы сообщений: `yunhu_user_form`
    - Сегмент статьи сообщений: `yunhu_user_post`
    - Сегмент стикера сообщений: `yunhu_user_sticker`
    - Сегмент кнопки сообщений: `yunhu_user_button`
    - Сегмент A2UI сообщений: `a2ui`
3. Расширенные поля:
    - Все уникальные поля имеют префикс `yunhu_user_`
    - Исходные данные сохраняются в поле `yunhu_user_raw`
    - Тип исходного события записывается в поле `yunhu_user_raw_type`
    - В личных сообщениях `self.user_id` указывает ID текущего входящего пользователя

### Поддерживаемые исходные типы событий

| Исходный тип события | Тип OneBot12 | Описание |
|-------------|--------------|------|
| `push_message` | `message` | Пуш-сообщение (личные сообщения, групповые сообщения, сессии бота) |
| `edit_message` | `notice` (`message_edit`) | Событие редактирования сообщения |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Событие супер-файлового обмена |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Событие доски объявлений бота |

> Другие типы событий (например, `heartbeat_ack`, `draft_input`, `stream_message` и т.д.) будут игнорироваться.

### Поддерживаемые detail_type OneBot12

| OneBot12 detail_type | chat_type Yunhu | Описание |
|---------------------|---------------|------|
| `private` | 1 | Личное сообщение |
| `group` | 2 | Групповое сообщение |
| `bot` | 3 | Сессия бота |

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
    "user_nickname": "Имя пользователя отправителя",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### Пример уведомления о редактировании сообщения

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
    "user_nickname": "Имя пользователя отправителя",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### Пример события супер-файлового обмена

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
    "bot_name": "Название бота",
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
    """Обработка сообщений пользователя Yunhu"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"Пользователь {user_nickname}({user_id}): {alt_message}")
    
    # Проверка специальных типов сегментов сообщений
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"Получено сообщение формы: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"Получено сообщение статьи: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"Получено сообщение стикера: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"Сообщение содержит кнопки: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"Получено A2UI-сообщение: {a2ui_data}")
    
    # Автоматический ответ с использованием event.reply()
    await event.reply(f"Эхо: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """Обработка уведомлений пользователя Yunhu"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"Пользователь {user_nickname} отредактировал сообщение {message_id}")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"Получено супер-файловое сообщение: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"Бот {bot_name} опубликовал объявление: {board_data.get('content', '')}")
```

## Описание расширенных полей

- Все уникальные поля имеют префикс `yunhu_user_`, чтобы избежать конфликтов со стандартными полями
- Исходные данные сохраняются в поле `yunhu_user_raw`, что позволяет получить полные исходные данные платформы Yunhu
- Тип исходного события записывается в поле `yunhu_user_raw_type` (например, `push_message`, `edit_message` и т.д.)
- `self.user_id` указывает ID текущего входящего пользователя (получен из ответа входа)
- Супер-файловый обмен предоставляется через поле `yunhu_user_file_send`, содержащее данные обмена файлами
- Доска объявлений бота предоставляется через поле `yunhu_user_bot_board`, содержащее данные объявлений

### Уникальные типы сегментов сообщений

#### Сегмент формы сообщений (yunhu_user_form)

Когда `content_type` равен 5, тип сегмента сообщения — `yunhu_user_form`:

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "Данные формы"
    }
}
```

#### Сегмент статьи сообщений (yunhu_user_post)

Когда `content_type` равен 6, тип сегмента сообщения — `yunhu_user_post`:

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "ID статьи",
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

#### Сегмент стикера сообщений (yunhu_user_sticker)

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

#### Сегмент кнопки сообщений (yunhu_user_button)

Когда в сообщении присутствуют кнопки, к сообщению добавляется сегмент `yunhu_user_button`:

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "Текст кнопки", "actionType": 3, "value": "Значение"}]]
    }
}
```

#### Сегмент A2UI сообщений (a2ui)

Когда `content_type` равен 14, тип сегмента сообщения — `a2ui`:

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSON-данные"
    }
}
```

---

## Конфигурация нескольких учетных записей

### Описание конфигурации

YunhuUserAdapter поддерживает одновременную настройку и работу нескольких учетных записей пользователей.

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # Интервал повторного подключения WebSocket (секунды)
ws_timeout = 70             # Время ожидания WebSocket (секунды)

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # Электронная почта пользователя (обязательно)
password = "password1"       # Пароль пользователя (обязательно)
platform = "windows"         # Идентификатор платформы входа (необязательно, по умолчанию windows)
device_id = ""               # ID устройства (необязательно, если не указан, будет сгенерирован)
enabled = true               # Активирована ли учетная запись (необязательно, по умолчанию true)

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**Описание конфигурационных параметров:**
- `email`: Электронная почта пользователя (обязательно), используется для входа на платформу Yunhu
- `password`: Пароль пользователя (обязательно)
- `platform`: Идентификатор платформы входа (необязательно, по умолчанию `windows`), возможные значения: `windows`, `macos`, `linux`, `ios`, `android`
- `device_id`: ID устройства (необязательно, если не указан, будет сгенерирован), рекомендуется указывать фиксированное значение для обеспечения согласованности сессии
- `enabled`: Активирована ли учетная запись (необязательно, по умолчанию `true`)

**Конфигурация на уровне адаптера:**
- `ws_reconnect_interval`: Интервал повторного подключения WebSocket (секунды, по умолчанию 30)
- `ws_timeout`: Время ожидания WebSocket (секунды, по умолчанию 70)

**Важные замечания:**
1. Адаптер использует способ входа по электронной почте для получения токена, после чего получает события через WebSocket
2. После разрыва соединения WebSocket адаптер автоматически переподключается, с максимальным количеством попыток 3
3. Рекомендуется задавать фиксированный `device_id` для каждой учетной записи, чтобы обеспечить согласованность сессии
4. Незамененные шаблонные учетные записи (по умолчанию почта и пароль) будут автоматически пропущены

### Использование Send DSL для указания учетной записи

Можно указать, какую учетную запись использовать для отправки сообщения с помощью метода `Using()`. Этот метод поддерживает два типа параметров:
- **Имя учетной записи**: Название учетной записи в конфигурации (например, `default`, `account2`)
- **user_id**: ID пользователя, полученный после входа

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# Отправка сообщения с использованием имени учетной записи
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# Отправка сообщения с использованием user_id (автоматически сопоставляется с соответствующей учетной записью)
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# Если не указано, используется первая активная учетная запись
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **Совет:** При использовании `user_id` система автоматически найдет соответствующую учетную запись в конфигурации. Это особенно полезно при обработке событий, где можно напрямую использовать `event["self"]["user_id"]` для ответа в той же учетной записи.

### Идентификатор учетной записи в событии

Полученные события автоматически содержат соответствующую информацию об ID пользователя:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # Получение ID текущей входящей учетной записи
        my_user_id = event["self"]["user_id"]
        print(f"Сообщение от аккаунта: {my_user_id}")
        
        # Отправка ответа с использованием той же учетной записи
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответ на сообщение")
```

### Логи

Адаптер автоматически включает информацию об учетной записи в логи, что упрощает отладку и отслеживание:

```
[INFO] Аккаунт default (user1@example.com) успешно вошел, ID пользователя: 12345678
[INFO] Задача прослушивания WebSocket для аккаунта default запущена
[INFO] Аккаунт account2 (user2@example.com) успешно вошел, ID пользователя: 87654321
```

### Управление через интерфейс

```python
# Получение информации обо всех учетных записях
accounts = yunhu_user.accounts
# Формат возврата: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# Проверка, включена ли учетная запись
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# Получение HTTP-клиента по имени учетной записи
http_client = yunhu_user._get_http_client("default")

# Поиск учетной записи по user_id
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## Вызовы API

Адаптер предоставляет метод `call_api`, который позволяет напрямую вызывать API платформы:

```python
# Отправка сообщения
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# Редактирование сообщения
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="Новое содержание",
    content_type="text"
)

# Отмена отправки сообщения
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# Массовая отмена отправки сообщений
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

**Поддерживаемые API-эндпоинты:**

| Эндпоинт | Описание |
|------|------|
| `/send` | Отправка сообщения |
| `/edit` | Редактирование сообщения |
| `/recall` | Отмена отправки сообщения |
| `/recall_batch` | Массовая отмена отправки сообщений |
| `/list` | Получение списка сообщений |
| `/list_by_seq` | Получение сообщений по последовательности |
| `/list_by_mid_seq` | Получение сообщений по ID и последовательности |
| `/list_edit_record` | Получение истории редактирования сообщений |
| `/button_report` | Отчет о событии кнопки |