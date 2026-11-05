# Документация по функциям платформы пользователей Yunhu

YunhuUserAdapter — это адаптер, построенный на основе протокола учетных записей пользователей Yunhu, который обеспечивает вход с помощью учетной записи электронной почты, получение событий через WebSocket и предоставляет единый интерфейс обработки событий и операций сообщений.

---

## Информация о документации

- Версия соответствующего модуля: 4.4.0
- Ответственный: wsu2059

## Основная информация

- Описание платформы: Yunhu — это корпоративная платформа мгновенного обмена сообщениями. Данный адаптер взаимодействует с платформой через **учетную запись пользователя** (а не бота).
- Название адаптера: YunhuUserAdapter
- Поддержка нескольких учетных записей: поддержка распознавания и настройки нескольких учетных записей пользователей по имени учетной записи.
- Поддержка цепочки модификаторов: поддержка цепочки методов модификаторов, таких как `.Reply()`
- Совместимость с OneBot12: поддержка отправки сообщений в формате OneBot12
- Способ связи: получение токена через вход с помощью электронной почты, получение событий через WebSocket, отправка сообщений с использованием протокола HTTP + Protobuf
- Типы сессий: поддержка личных сообщений (user), групповых сообщений (group), сессий бота (bot)

## Обновление до версии v5 (4.2.0)

- **Наследование BaseConverter**; **задача spawn_background** (задача прослушивания WS)
- **Полный API для пользователей** (на основе yhchatAPI full.proto / v1 конечной точки, protobuf over HTTP):
  - Пользователь: get_user / edit_nickname / edit_avatar
  - Друзья: адресная книга / список заявок / заявка / согласие / игнорирование / удаление
  - Группы: информация о группе / список участников / создание / роспуск / приглашение / исключение / замолчание / список ботов
  - Сессии: список сессий; сообщения: список / отмена / отчет о кнопке
- **Мягкая зависимость от фреймворка**: во время выполнения проверяется наличие ErisPulse>=2.7.1 и выводится предупреждение; при запуске выводится лог версии

## Перечень подключенных функций платформы

### Получение событий (WebSocket, кодировка protobuf)

| WS cmd | Событие | Описание |
|--------|---------|----------|
| `push_message` | `message` | Личные/групповые/бот-сессионные сообщения (текст/HTML/Markdown/изображения/видео/аудио/файлы/эмодзи/формы/статьи/стикеры/кнопки/A2UI) |
| `edit_message` | `notice` (`message_edit`) | Уведомление об изменении сообщения |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Супер-файловый обмен |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Доска объявлений бота |

### Сопоставление методов Api DSL (YunhuHTTPClient → конечная точка v1 API пользователя)

| Категория | Метод Api | Конечная точка | Описание |
|-----------|-----------|----------------|----------|
| Учетная запись | `get_self_info()` | `/user/info` | Информация о пользователе (ник/аватар/user_id) |
| Пользователь | `get_user(user_id)` | `/user/get-user` | Подробная информация о пользователе |
| Пользователь | `edit_nickname(nickname)` | `/user/edit-nickname` | Изменение своего никнейма |
| Пользователь | `edit_avatar(url)` | `/user/edit-avatar` | Изменение своего аватара |
| Друзья | `get_friend_address_book(md5)` | `/friend/address-book-list` | Адресная книга (страничный просмотр) |
| Друзья | `get_friend_requests()` | `/friend/request-list` | Список заявок на добавление в друзья/в группы |
| Друзья | `friend_apply(user_id, desc)` | `/friend/apply` | Заявка на добавление в друзья |
| Друзья | `friend_agree_apply(user_id)` | `/friend/agree-apply` | Согласие на заявку в друзья |
| Друзья | `friend_ignore_apply(user_id)` | `/friend/ignore-apply` | Игнорирование заявки в друзья |
| Друзья | `friend_delete(user_id)` | `/friend/delete-friend` | Удаление друга |
| Группы | `get_group_info(group_id)` | `/group/info` | Информация о группе |
| Группы | `get_group_member_list(group_id)` | `/group/list-member` | Список участников группы (поддержка поиска по ключевым словам) |
| Группы | `create_group(name, ...)` | `/group/create-group` | Создание группы |
| Группы | `dismiss_group(group_id)` | `/group/dismiss-group` | Расформирование группы |
| Группы | `group_invite(group_id, user_ids)` | `/group/invite` | Приглашение в группу |
| Группы | `group_remove_member(group_id, user_id)` | `/group/remove-member` | Исключение участника из группы |
| Группы | `group_gag_member(group_id, user_id, секунды)` | `/group/gag-member` | Замолчание участника группы (0=отмена) |
| Группы | `get_group_bot_list(group_id)` | `/group/bot-list` | Список ботов в группе |
| Сессии | `get_conversation_list(md5)` | `/conversation/list` | Список сессий (страничный просмотр) |
| Сообщения | `get_message_list(chat_id, chat_type, ...)` | `/msg/list-message` | Список сообщений (различные варианты страничного просмотра см. в HTTP-клиенте) |
| Сообщения | `delete_message(msg_id, chat_id, chat_type)` | `/msg/recall-msg` | Отмена сообщения (массовая отмена см. в HTTP-клиенте) |
| Сообщения | `button_report(...)` | `/msg/button-report` | Отчет о нажатии кнопки |
| Мета-действия | `get_status` / `get_version` / `get_supported_actions` | - | Статус выполнения/версия/поддерживаемые действия |

### Не реализованные функции (конечные точки известны, сообщения в full.proto полны, можно расширять по требованию)

- Пользователь: вход по коду подтверждения, значки, записи о золотых бобах, привязка телефона/почты, настройки уведомлений, хранение пользовательских данных
- Друзья: без уведомлений (no-notify), удаление записей заявок
- Группы: список команд, категории, рекомендации, прямые трансляции, редактирование информации о группе/никнейма/ключевых слов, автоматическое согласование при вступлении в группу, ограничения на файлы группы, события SSE
- Сессии: фиксация/сортировка/удаление, без уведомлений
- Сообщения: пересылка, отправка A2UI, получение изображений из списка сообщений, запись загрузки файлов
- Групповые теги: list / relate / relate-cancel / create / edit / delete / members (конечная точка `/group-tag/*`)

> Способ расширения: добавьте методы в `YunhuHTTPClient` в соответствии с существующим шаблоном (общие обёртки `_proto_request` / `_json_request`), затем опубликуйте их в классе `Api`. Конечные точки и определения сообщений см. в `yhchatAPI/src/api/v1/*.md` и `yhchatAPI/src/full.proto`.

### Примеры API для пользователей

```python
from ErisPulse import sdk
yunhu_user = sdk.adapter.get("yunhu_user")

result = await yunhu_user.Api.get_self_info()
result = await yunhu_user.Api.get_friend_requests()          # Список заявок на добавление в друзья
await yunhu_user.Api.friend_agree_apply(user_id)             # Согласие на заявку в друзья
result = await yunhu_user.Api.get_group_member_list(group_id)
result = await yunhu_user.Api.get_conversation_list()        # Список сессий
await yunhu_user.Api.delete_message(msg_id, chat_id, chat_type)  # Отмена сообщения
```

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочки вызовов, например:
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str, buttons: Optional[List] = None)` — отправка сообщения в виде простого текста.
- `.Html(html: str, buttons: Optional[List] = None)` — отправка сообщения в формате HTML.
- `.Markdown(markdown: str, buttons: Optional[List] = None)` — отправка сообщения в формате Markdown.
- `.MergeForward(nodes, title="Совместная пересылка")` — отправка сообщения в виде объединённой пересылки (отображается как карточка HTML-свертывания, отправляется через канал HTML с msg_type=8).
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с изображением, поддержка URL, локального пути или двоичных данных.
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с видео, поддержка URL, локального пути или двоичных данных.
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с аудио, поддержка URL, локального пути или двоичных данных, автоматическое определение продолжительности аудио.
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)` — псевдоним для `.Audio()`.
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)` — отправка сообщения с файлом, поддержка URL, локального пути или двоичных данных.
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)` — отправка сообщения с эмодзи/стикером, поддержка ID стикера, URL стикера или двоичных изображений.
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)` — отправка сообщения A2UI (тип сообщения 14), данные JSON A2UI будут отправлены в поле text.
- `.Edit(msg_id: str, text: str, content_type: str = "text")` — редактирование существующего сообщения.
- `.Recall(msg_id: str)` — отмена сообщения.
- `.Raw_ob12(message: Union[List, Dict])` — отправка сообщения в формате OneBot12.

### Обработка медиафайлов

Все типы медиа (изображения, видео, аудио, файлы) поддерживают следующие способы ввода:
- **URL**: `"https://example.com/image.jpg"` — автоматически скачивается и загружается
- **Локальный путь**: `"/path/to/file.jpg"` — автоматически читается и загружается
- **Двоичные данные**: `open("file.jpg", "rb").read()` — напрямую загружается

Медиафайлы автоматически загружаются на хранилище Qiniu Cloud, поддерживаются следующие функции:
- Автоматическое определение типа файла и MIME с помощью библиотеки filetype
- Автоматическое вычисление размера файла
- Автоматическое определение продолжительности аудиофайла (поддержка форматов MP3, MP4/M4A)

### Описание параметров кнопок

Параметр `buttons` представляет собой вложенный список, описывающий макет и функции кнопок. Каждый объект кнопки содержит следующие поля:

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `text` | string | Да | Текст на кнопке |
| `actionType` | int | Да | Тип действия:<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отправка отчета |
| `url` | string | Нет | Используется, когда `actionType=1`, указывает целевой URL перехода |
| `value` | string | Нет | Когда `actionType=2`, это значение будет скопировано в буфер обмена<br>Когда `actionType=3`, это значение будет отправлено подписчику |

Пример:
```python
buttons = [
    [
        {"text": "Копировать", "actionType": 2, "value": "xxxx"},
        {"text": "Перейти", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Отправить событие", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("Сообщение с кнопками")
```

### Цепочные модификаторы (можно комбинировать)

Цепочные модификаторы возвращают `self`, поддерживают цепочечный вызов, должны быть вызваны до окончательного метода отправки:

- `.Reply(message_id: str)` — ответить на указанное сообщение.
- `.At(user_id: str)` — упомянуть пользователя (в тексте @user_id).
- `.AtAll()` — упомянуть всех (псевдо @всех, отправляется текст @all).
- `.Buttons(buttons: List)` — добавить кнопки.

> **Важно:** поскольку учетная запись пользователя является особой, даже не администратор может упомянуть всех, но здесь `AtAll()` просто отправит текст, содержащий упоминание всех, это псевдо-упоминание всех.

### Примеры цепочечного вызова

```python
# Базовая отправка
await yunhu_user.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("Ответ на сообщение")

# Ответ + кнопки
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Сообщение с ответом и кнопками")

# Указание аккаунта + ответ + кнопки
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Цепочка вызовов")
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость между платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 поддерживает автоматическую группировку смешанных сообщений:
- Типы `text`, `mention` могут быть объединены в одну группу
- Типы `image`, `video`, `audio`, `file`, `face`, `markdown`, `html`, `a2ui` отправляются отдельными группами
- Тип `reply` может быть добавлен к любой группе

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект задачи, который можно ожидать с помощью await. Возвращаемый результат соответствует стандартизированному формату возврата адаптера ErisPulse:

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

## Специфичные типы событий

Необходимо использовать `platform == "yunhu_user"` для проверки и применения специфичных функций данной платформы

### Основные отличия

1. Специфичные типы событий:
    - Супер-файловый обмен: `yunhu_user_file_send`
    - Доска объявлений бота: `yunhu_user_bot_board`
    - Уведомление об изменении сообщения: `message_edit`
    - Уведомление об удалении сообщения: `message_delete` (отмена)
2. Специфичные типы сообщений:
    - Сообщение формы: `yunhu_user_form`
    - Сообщение статьи: `yunhu_user_post`
    - Сообщение стикера: `yunhu_user_sticker`
    - Сообщение кнопки: `yunhu_user_button`
    - Сообщение A2UI: `a2ui`
3. Расширенные поля:
    - Все специфичные поля имеют префикс `yunhu_user_`
    - Исходные данные сохраняются в поле `yunhu_user_raw`
    - Тип исходного события сохраняется в поле `yunhu_user_raw_type`
    - В личных сообщениях `self.user_id` указывает ID текущего пользователя

### Поддерживаемые исходные типы событий

| Исходный тип события | Тип OneBot12 | Описание |
|---------------------|--------------|----------|
| `push_message` | `message` | Получение сообщения (личные сообщения, групповые сообщения, бот-сессии) |
| `edit_message` | `notice` (`message_edit`) | Событие редактирования сообщения |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Событие супер-файлового обмена |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Событие доски объявлений бота |

> Другие типы событий (например, `heartbeat_ack`, `draft_input`, `stream_message` и т.д.) будут игнорироваться.

### Поддерживаемые detail_type OneBot12

| detail_type OneBot12 | chat_type Yunhu | Описание |
|---------------------|----------------|----------|
| `private` | 1 | Личное сообщение |
| `group` | 2 | Групповое сообщение |
| `bot` | 3 | Бот-сессия |

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
        {"type": "text", "data": {"text": "Сообщение"}}
    ],
    "alt_message": "Сообщение",
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
    """Обработка сообщений пользователя Yunhu"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"Пользователь {user_nickname}({user_id}): {alt_message}")
    
    # Проверка специфичных типов сегментов сообщений
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
    
    # Использование event.reply() для автоматического ответа
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

- Все специфичные поля имеют префикс `yunhu_user_`, чтобы избежать конфликтов со стандартными полями
- Исходные данные сохраняются в поле `yunhu_user_raw`, что позволяет получить полные исходные данные платформы Yunhu
- Тип исходного события сохраняется в поле `yunhu_user_raw_type` (например, `push_message`, `edit_message` и т.д.)
- `self.user_id` указывает ID текущего пользователя (получается из ответа входа)
- Супер-файловый обмен предоставляется через поле `yunhu_user_file_send`
- Доска объявлений бота предоставляется через поле `yunhu_user_bot_board`

### Специфичные типы сообщений

#### Сообщение формы (yunhu_user_form)

Когда content_type равен 5, тип сообщения — `yunhu_user_form`:

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "Данные формы"
    }
}
```

#### Сообщение статьи (yunhu_user_post)

Когда content_type равен 6, тип сообщения — `yunhu_user_post`:

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
|------|-----|----------|
| `post_id` | string | Уникальный идентификатор статьи |
| `post_title` | string | Заголовок статьи |
| `post_content` | string | Содержание статьи |

#### Сообщение стикера (yunhu_user_sticker)

Когда content_type равен 7, тип сообщения — `yunhu_user_sticker`:

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "URL изображения стикера"
    }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `file_id` | string | URL изображения стикера |

#### Сообщение кнопки (yunhu_user_button)

Когда сообщение содержит кнопки, будет добавлен специфичный сегмент `yunhu_user_button`:

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "Текст кнопки", "actionType": 3, "value": "Значение"}]]
    }
}
```

#### Сообщение A2UI (a2ui)

Когда content_type равен 14, тип сообщения — `a2ui`:

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

YunhuUserAdapter поддерживает одновременную конфигурацию и запуск нескольких учетных записей пользователей.

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # Интервал повторного подключения WebSocket (секунды)
ws_timeout = 70             # Время ожидания WebSocket (секунды)

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # Электронная почта пользователя (обязательно)
password = "password1"       # Пароль пользователя (обязательно)
platform = "windows"         # Идентификатор платформы входа (необязательно, по умолчанию windows)
device_id = ""               # Идентификатор устройства (необязательно, если не заполнено, генерируется автоматически)
enabled = true               # Включена ли учетная запись (необязательно, по умолчанию true)

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**Описание параметров конфигурации:**
- `email`: Электронная почта пользователя (обязательно), используется для входа на платформу Yunhu
- `password`: Пароль пользователя (обязательно)
- `platform`: Идентификатор платформы входа (необязательно, по умолчанию `windows`), возможные значения: `windows`, `macos`, `linux`, `ios`, `android`
- `device_id`: Идентификатор устройства (необязательно, если не заполнено, генерируется автоматически), рекомендуется заполнять фиксированным значением для поддержания консистентности сессии
- `enabled`: Включена ли учетная запись (необязательно, по умолчанию `true`)

**Конфигурация на уровне адаптера:**
- `ws_reconnect_interval`: Интервал повторного подключения WebSocket (секунды, по умолчанию 30)
- `ws_timeout`: Время ожидания WebSocket (секунды, по умолчанию 70)

**Важное замечание:**
1. Адаптер использует вход с помощью электронной почты для получения токена, после чего получает события через WebSocket
2. При разрыве соединения WebSocket происходит автоматическое повторное подключение, максимум 3 попытки
3. Рекомендуется для каждой учетной записи задавать фиксированный `device_id`, чтобы поддерживать консистентность сессии
4. Незамененные шаблонные учетные записи (по умолчанию почта и пароль) будут автоматически пропущены

### Использование DSL Send для указания учетной записи

Метод `Using()` можно использовать для указания учетной записи, через которую отправляются сообщения. Этот метод поддерживает два типа параметров:
- **Имя учетной записи**: имя учетной записи из конфигурации (например, `default`, `account2`)
- **user_id**: ID пользователя, полученный после входа

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# Отправка сообщения с использованием имени учетной записи
await yunhu_user.Send.Using("default").To("user", "user123").Text("Привет от учетной записи 1!")

# Отправка сообщения с использованием user_id (автоматически сопоставляется с соответствующей учетной записью)
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Привет от пользователя!")

# Если не указать, будет использована первая включенная учетная запись
await yunhu_user.Send.To("user", "user123").Text("Привет от учетной записи по умолчанию!")
```

> **Примечание:** При использовании `user_id` система автоматически находит соответствующую учетную запись из конфигурации. Это особенно полезно при обработке ответов на события, где можно использовать `event["self"]["user_id"]` для отправки ответа той же учетной записи.

### Учетная запись в событиях

Полученные события автоматически содержат информацию об ID пользователя:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # Получение ID текущей учетной записи
        my_user_id = event["self"]["user_id"]
        print(f"Сообщение от аккаунта: {my_user_id}")
        
        # Использование той же учетной записи для отправки ответа
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответное сообщение")
```

### Логи

Адаптер автоматически включает информацию об учетной записи в логи, что облегчает отладку и отслеживание:

```
[INFO] Учетная запись default (user1@example.com) успешно вошла, ID пользователя: 12345678
[INFO] Задача прослушивания WebSocket для учетной записи default запущена
[INFO] Учетная запись account2 (user2@example.com) успешно вошла, ID пользователя: 87654321
```

### Интерфейс управления

```python
# Получение информации обо всех учетных записях
accounts = yunhu_user.accounts
# Формат возвращаемого значения: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# Проверка включения учетной записи
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# Получение HTTP-клиента по имени учетной записи
http_client = yunhu_user._get_http_client("default")

# Поиск учетной записи по user_id
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## Вызов API

Адаптер предоставляет метод `call_api`, который поддерживает прямой вызов платформенных API:

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
    text="Новое содержимое",
    content_type="text"
)

# Отмена сообщения
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# Массовая отмена сообщений
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

# Получение списка редактирований сообщений
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

**Поддерживаемые конечные точки API:**

| Конечная точка | Описание |
|----------------|----------|
| `/send` | Отправка сообщения |
| `/edit` | Редактирование сообщения |
| `/recall` | Отмена сообщения |
| `/recall_batch` | Массовая отмена сообщений |
| `/list` | Получение списка сообщений |
| `/list_by_seq` | Получение сообщений по последовательности |
| `/list_by_mid_seq` | Получение сообщений по ID и последовательности |
| `/list_edit_record` | Получение списка редактирований сообщений |
| `/button_report` | Отчет о событии кнопки |