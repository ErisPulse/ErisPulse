# Характеристики платформы пользователей Cloud Lake (Yunhu)

YunhuUserAdapter — это адаптер, основанный на протоколе учетной записи пользователя Cloud Lake, позволяющий входить через почтовый аккаунт пользователя, получать события через WebSocket и предоставляющий единые интерфейсы обработки событий и операций с сообщениями.

---

## Информация о документе

- Версия соответствующего модуля: 1.4.0
- Владелец: wsu2059

## Основная информация

- Описание платформы: Cloud Lake (Yunhu) — это корпоративная платформа мгновенного обмена сообщениями; этот адаптер взаимодействует с ней через **учетную запись пользователя** (в отличие от учетной записи бота)
- Название адаптера: YunhuUserAdapter
- Поддержка нескольких учетных записей: поддерживает распознавание и настройку нескольких пользовательских учетных записей по имени пользователя
- Поддержка цепных методов (fluent interface): поддержка методов с цепочечными вызовами, таких как `.Reply()`
- Совместимость с OneBot12: поддержка отправки сообщений в формате OneBot12
- Способ связи: вход через почту для получения токена, получение событий через WebSocket, отправка сообщений через HTTP + Protobuf
- Типы сессий: поддерживает личные сообщения (user), групповые чаты (group), сессии бота (bot)

## Поддерживаемые типы сообщений при отправке

Все методы отправки реализованы через цепочечный синтаксис (fluent syntax), например:

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:

- `.Text(text: str, buttons: Optional[List] = None)`: отправка текстового сообщения.
- `.Html(html: str, buttons: Optional[List] = None)`: отправка сообщения в формате HTML.
- `.Markdown(markdown: str, buttons: Optional[List] = None)`: отправка сообщения в формате Markdown.
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`: отправка сообщения с изображением, поддерживает URL, локальный путь или двоичные данные.
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`: отправка сообщения с видео, поддерживает URL, локальный путь или двоичные данные.
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`: отправка голосового сообщения, поддерживает URL, локальный путь или двоичные данные, автоматическое определение длительности аудио.
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`: псевдоним для `.Audio()`.
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`: отправка сообщения с файлом, поддерживает URL, локальный путь или двоичные данные.
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`: отправка сообщения с эмодзи/стикером, поддерживает ID стикера, URL стикера или двоичные данные изображения.
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`: отправка сообщения A2UI (тип сообщения 14), данные JSON A2UI заполняются в поле `text` при отправке.
- `.Edit(msg_id: str, text: str, content_type: str = "text")`: редактирование существующего сообщения.
- `.Recall(msg_id: str)`: отзыв сообщения (отмена отправки).
- `.Raw_ob12(message: Union[List, Dict])`: отправка сообщения в формате OneBot12.

### Обработка медиафайлов

Все типы медиа (изображение, видео, аудио, файл) поддерживают следующие способы ввода:
- **URL**: `"https://example.com/image.jpg"` — загрузка после автоматического скачивания
- **Локальный путь**: `"/path/to/file.jpg"` — чтение после автоматического открытия
- **Двоичные данные**: `open("file.jpg", "rb").read()` — отправка напрямую

Медиафайлы автоматически загружаются в облачное хранилище Qiniu, поддерживают следующие возможности:
- Автоматическое определение типа файла и MIME через библиотеку `filetype`
- Автоматический расчет размера файла
- Автоматическое определение длительности аудиофайлов (поддержка форматов MP3, MP4/M4A)

### Описание параметра кнопок

Параметр `buttons` — это вложенный список, представляющий макет и функцию кнопок. Каждый объект кнопки содержит следующие поля:

| Поле | Тип | Обязательно | Описание |
|------|------|-------------|----------|
| `text` | string | Да | Текст на кнопке |
| `actionType` | int | Да | Тип действия: <br>`1`: переход по URL<br>`2`: копировать<br>`3`: отчет о нажатии |
| `url` | string | Нет | Используется, когда `actionType=1`, указывает целевой URL для перехода |
| `value` | string | Нет | При `actionType=2` значение копируется в буфер обмена.<br>При `actionType=3` значение отправляется на сторону подписчика |

Пример:

```python
buttons = [
    [
        {"text": "复制", "actionType": 2, "value": "xxxx"},
        {"text": "点击跳转", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "汇报事件", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("Сообщение с кнопками")
```

### Цепные методы (комбинируются)

Методы цепного вызова возвращают `self`, поддерживают цепочечное использование, должны вызываться перед финальным методом отправки:

- `.Reply(message_id: str)`: ответить на указанное сообщение.
- `.At(user_id: str)`: упомянуть указанного пользователя (в текстовом виде @user_id).
- `.AtAll()`: упомянуть всех (ложное упоминание всех, отправка текста "@all").
- `.Buttons(buttons: List)`: добавить кнопки.

> **Примечание:** Так как учетная запись пользователя имеет особый статус, даже не являясь администратором можно упомянуть всех, однако здесь `AtAll()` отправит только текстовое упоминание "@all", что является ложным упоминанием всех.

### Примеры цепочного вызова

```python
# Базовая отправка
await yunhu_user.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("Ответное сообщение")

# Ответ + кнопки
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Сообщение с ответом и кнопками")

# Указание учетной записи + ответ + кнопки
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Полный цепной вызов")
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12, что облегчает кроссплатформенную совместимость сообщений:

- `.Raw_ob12(message: List[Dict], **kwargs)`: отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепными методами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 поддерживает автоматическую группировку смешанных сегментов сообщений:
- Типы `text` и `mention` могут быть объединены в группу для отправки
- Типы `image`, `video`, `audio`, `file`, `face`, `markdown`, `html`, `a2ui` и т.д. формируют отдельные группы
- Тип `reply` может быть прикреплен к любой группе

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно получить напрямую через `await`. Возвращаемые результаты следуют стандартизированным нормам возвращаемых значений адаптеров ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "message_id": "123456",   // ID сообщения
    "message": "",            // Информация об ошибке
    "yunhu_user_raw": {...}   // Исходные данные ответа
}
```

## Специальные типы событий

Необходимо проверять `platform == "yunhu_user"` перед использованием характеристик этой платформы

### Основные отличия

1. Специальные типы событий:
    - Супер-делегирование файлов: `yunhu_user_file_send`
    - Доска объявлений бота: `yunhu_user_bot_board`
    - Уведомление об редактировании сообщения: `message_edit`
    - Уведомление об удалении сообщения: `message_delete` (отзыв)
2. Специальные типы сегментов сообщений:
    - Сегмент формы: `yunhu_user_form`
    - Сегмент статьи: `yunhu_user_post`
    - Сегмент стикера: `yunhu_user_sticker`
    - Сегмент кнопок: `yunhu_user_button`
    - Сегмент A2UI: `a2ui`
3. Расширенные поля:
    - Все специальные поля идентифицируются префиксом `yunhu_user_`
    - Исходные данные сохраняются в поле `yunhu_user_raw`
    - Исходный тип события записывается в поле `yunhu_user_raw_type`
    - В личных чатах `self.user_id` означает ID текущего вошедшего пользователя

### Поддерживаемые исходные типы событий

| Исходный тип события | OneBot12 Тип | Описание |
|-------------|--------------|------|
| `push_message` | `message` | Уведомление о сообщении (личный чат, групповой чат, сессия бота) |
| `edit_message` | `notice` (`message_edit`) | Событие редактирования сообщения |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Событие супер-делегирования файлов |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Событие доски объявлений бота |

> Другие типы событий (например, `heartbeat_ack`, `draft_input`, `stream_message` и т.д.) будут игнорироваться.

### Поддерживаемый OneBot12 detail_type

| OneBot12 detail_type | chat_type Cloud Lake | Описание |
|---------------------|---------------|------|
| `private` | 1 | Личное сообщение |
| `group` | 2 | Групповое сообщение |
| `bot` | 3 | Сессия бота |

### Пример события сообщения

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
    "user_nickname": "Отображаемое имя отправителя",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### Пример уведомления об редактировании сообщения

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
    "user_nickname": "Отображаемое имя отправителя",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### Пример события супер-делегирования файлов

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
    """Обработка сообщения Cloud Lake"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"Пользователь {user_nickname}({user_id}): {alt_message}")
    
    # Проверка особых типов в сегментах сообщений
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
            print(f"Получено сообщение A2UI: {a2ui_data}")
    
    # Автоматический ответ через event.reply()
    await event.reply(f"Эхо: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """Обработка уведомлений Cloud Lake"""
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
        print(f"Получено супер-делегирование файлов: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"Бот {bot_name} опубликовал объявление: {board_data.get('content', '')}")
```

## Описание расширенных полей

- Все специальные поля идентифицируются префиксом `yunhu_user_`, чтобы избежать конфликтов со стандартными полями
- Исходные данные сохраняются в поле `yunhu_user_raw`, что обеспечивает доступ к полным исходным данным платформы Cloud Lake
- Исходный тип события записывается в поле `yunhu_user_raw_type` (например, `push_message`, `edit_message` и т.д.)
- `self.user_id` означает ID текущего вошедшего пользователя (получается из ответа на вход)
- Супер-делегирование файлов предоставляет данные о делегировании через поле `yunhu_user_file_send`
- Доска объявлений бота предоставляет данные об объявлении через поле `yunhu_user_bot_board`

### Специальные типы сегментов сообщений

#### Сегмент формы (yunhu_user_form)

Когда content_type равен 5, тип сегмента сообщения — `yunhu_user_form`:

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "Данные формы"
    }
}
```

#### Сегмент статьи (yunhu_user_post)

Когда content_type равен 6, тип сегмента сообщения — `yunhu_user_post`:

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

#### Сегмент стикера (yunhu_user_sticker)

Когда content_type равен 7, тип сегмента сообщения — `yunhu_user_sticker`:

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

#### Сегмент кнопок (yunhu_user_button)

Когда в сообщении содержатся кнопки, добавляется сегмент сообщения `yunhu_user_button`:

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "Текст кнопки", "actionType": 3, "value": "значение"}]]
    }
}
```

#### Сегмент A2UI (a2ui)

Когда content_type равен 14, тип сегмента сообщения — `a2ui`:

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "Данные JSON A2UI"
    }
}
```

---

## Конфигурация нескольких учетных записей

### Описание конфигурации

YunhuUserAdapter поддерживает одновременную настройку и работу нескольких пользовательских учетных записей.

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # Интервал переподключения WebSocket (секунды)
ws_timeout = 70             # Тайм-аут WebSocket (секунды)

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # Почта пользователя (обязательно)
password = "password1"       # Пароль пользователя (обязательно)
platform = "windows"         # Платформа входа (необязательно, по умолчанию windows)
device_id = ""               # ID устройства (необязательно, автоматически при отсутствии)
enabled = true               # Включен ли аккаунт (необязательно, по умолчанию true)

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**Объяснение параметров конфигурации:**
- `email`: почта пользователя (обязательно), используется для входа на платформу Cloud Lake
- `password`: пароль пользователя (обязательно)
- `platform`: идентификатор платформы входа (необязательно, по умолчанию `windows`), возможные значения: `windows`、`macos`、`linux`、`ios`、`android`
- `device_id`: ID устройства (необязательно, автоматически при отсутствии), рекомендуется указывать фиксированное значение для сохранения согласованности сессии
- `enabled`: включен ли этот аккаунт (необязательно, по умолчанию `true`)

**Конфигурация на уровне адаптера:**
- `ws_reconnect_interval`: интервал переподключения WebSocket (секунды, по умолчанию 30)
- `ws_timeout`: тайм-аут WebSocket (секунды, по умолчанию 70)

**Важные примечания:**
1. Адаптер использует способ входа через почту для получения токена, после входа получает события через WebSocket
2. После разрыва соединения WebSocket произойдет автоматическое переподключение, максимум 3 попытки
3. Рекомендуется указывать фиксированный `device_id` для каждого аккаунта для сохранения согласованности сессии
4. Шаблонные аккаунты без изменений (пустая почта и пароль) будут пропущены автоматически

### Использование Send DSL для указания учетной записи

Можно указать, какой учетной записью отправлять сообщение, используя метод `Using()`. Метод поддерживает два параметра:
- **Имя учетной записи**: имя учетной записи в конфигурации (например, `default`、`account2`)
- **user_id**: ID пользователя, полученный после входа

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# Отправка сообщения с использованием имени учетной записи
await yunhu_user.Send.Using("default").To("user", "user123").Text("Привет от аккаунта 1!")

# Отправка сообщения с использованием user_id (автоматическое сопоставление соответствующего аккаунта)
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Привет от пользователя!")

# Не указано — использование первого включенного аккаунта
await yunhu_user.Send.To("user", "user123").Text("Привет от аккаунта по умолчанию!")
```

> **Подсказка:** При использовании `user_id` система автоматически найдет соответствующий аккаунт в конфигурации. Это особенно полезно при обработке ответов на события, можно напрямую использовать `event["self"]["user_id"]` для ответа от того же аккаунта.

### Идентификация учетной записи в событиях

Получаемые события автоматически включают соответствующую информацию о user_id:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # Получение ID текущего вошедшего пользователя
        my_user_id = event["self"]["user_id"]
        print(f"Сообщение от аккаунта: {my_user_id}")
        
        # Ответ на сообщение с использованием того же аккаунта
        yunhu_user = adapter.get("yunhu_user")
        await
```

## API 调用

Адаптер предоставляет метод `call_api`, поддерживающий прямой вызов платформенных API:

```python
# 发送消息
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# 编辑消息
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="新内容",
    content_type="text"
)

# 撤回消息
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# 批量撤回消息
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# 获取消息列表
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# 获取消息编辑记录
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# 按钮事件报告
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**Поддерживаемые API-конечные точки:**

| Конечная точка | Описание |
|------|------|
| `/send` | Отправка сообщения |
| `/edit` | Редактирование сообщения |
| `/recall` | Отзыв сообщения |
| `/recall_batch` | Массовый отзыв сообщения |
| `/list` | Получение списка сообщений |
| `/list_by_seq` | Получение сообщения по последовательности |
| `/list_by_mid_seq` | Получение сообщения по ID и последовательности |
| `/list_edit_record` | Получение записей редактирования сообщений |
| `/button_report` | Отчет о событиях кнопок |