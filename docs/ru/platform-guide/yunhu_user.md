# Документация по возможностям пользовательской платформы Yunhu

YunhuUserAdapter — это адаптер, построенный на основе протокола пользовательских аккаунтов Yunhu. Он выполняет вход через почтовый аккаунт пользователя, получает события через WebSocket и предоставляет унифицированный интерфейс обработки событий и операций с сообщениями.

---

## Информация о документе

- Версия модуля: 4.6.1
- Ответственный за поддержку: wsu2059
- Последнее обновление: 2026-11-10

## Основная информация

- О платформе: Yunhu — корпоративная платформа мгновенного обмена сообщениями; данный адаптер взаимодействует с ней через **пользовательский аккаунт** (а не аккаунт бота)
- Название адаптера: YunhuUserAdapter
- Поддержка нескольких аккаунтов: поддерживается идентификация и настройка нескольких пользовательских аккаунтов по имени аккаунта
- Поддержка цепочек модификаторов: поддерживаются цепочные методы модификации, такие как `.Reply()`
- Совместимость с OneBot12: поддерживается отправка сообщений в формате OneBot12
- Способ связи: получение token через вход по электронной почте, приём событий через WebSocket, отправка сообщений по протоколу HTTP + Protobuf
- Типы диалогов: поддерживаются личный чат (user), групповой чат (group), диалог с ботом (chat_type=3, начиная с 4.6.1 отображается как `private`)

## Обновление парадигмы v5 (4.2.0)

- **Наследование BaseConverter**; **принадлежность задач spawn_background** (задачи прослушивания WS)
- **Полный набор пользовательских API** (на основе yhchatAPI full.proto / эндпоинтов v1, protobuf over HTTP):
  - Пользователи: get_user / edit_nickname / edit_avatar
  - Друзья: адресная книга / список заявок / заявка / согласие / игнорирование / удаление
  - Группы: информация о группе / список участников / создание / роспуск / приглашение / исключение / мут / список ботов
  - Диалоги: список диалогов; сообщения: список / отзыв / отчёт о нажатии кнопок
- **Мягкая зависимость от фреймворка**: проверка ErisPulse>=2.7.1 во время выполнения с уведомлением; вывод журнала версий при запуске

## Список интегрированных функций платформы

### Приём событий (WebSocket, кодирование protobuf)

| Команда WS | Событие | Описание |
|--------|------|------|
| `push_message` | `message` | Сообщения личного чата/группового чата/диалога с ботом (текст/HTML/Markdown/изображения/видео/аудио/файлы/эмодзи/формы/статьи/стикеры/кнопки/A2UI) |
| `edit_message` | `notice` (`message_edit`) | Уведомление о редактировании сообщения |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Супер-передача файлов |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Доска объявлений бота |

### Соответствие методов Api DSL ( YunhuHTTPClient → пользовательские API v1 эндпоинты )

| Категория | Метод Api | Эндпоинт | Описание |
|------|---------|------|------|
| Аккаунт | `get_self_info()` | `/user/info` | Информация о вошедшем пользователе (ник/аватар/user_id) |
| Пользователь | `get_user(user_id)` | `/user/get-user` | Подробная информация о пользователе |
| Пользователь | `edit_nickname(nickname)` | `/user/edit-nickname` | Изменение своего ника |
| Пользователь | `edit_avatar(url)` | `/user/edit-avatar` | Изменение своего аватара |
| Друг | `get_friend_address_book(md5)` | `/friend/address-book-list` | Адресная книга (курсорная пагинация) |
| Друг | `get_friend_requests()` | `/friend/request-list` | Список заявок в друзья/в группу |
| Друг | `friend_apply(user_id, desc)` | `/friend/apply` | Отправка заявки в друзья |
| Друг | `friend_agree_apply(user_id)` | `/friend/agree-apply` | Принятие заявки в друзья |
| Друг | `friend_ignore_apply(user_id)` | `/friend/ignore-apply` | Игнорирование заявки в друзья |
| Друг | `friend_delete(user_id)` | `/friend/delete-friend` | Удаление друга |
| Группа | `get_group_info(group_id)` | `/group/info` | Информация о группе |
| Группа | `get_group_member_list(group_id)` | `/group/list-member` | Список участников группы (с поддержкой ключевых слов) |
| Группа | `create_group(name, ...)` | `/group/create-group` | Создание группы |
| Группа | `dismiss_group(group_id)` | `/group/dismiss-group` | Роспуск группы |
| Группа | `group_invite(group_id, user_ids)` | `/group/invite` | Приглашение в группу |
| Группа | `group_remove_member(group_id, user_id)` | `/group/remove-member` | Исключение участника из группы |
| Группа | `group_gag_member(group_id, user_id, секунд)` | `/group/gag-member` | Мут участника группы (0=снятие) |
| Группа | `get_group_bot_list(group_id)` | `/group/bot-list` | Список ботов в группе |
| Диалог | `get_conversation_list(md5)` | `/conversation/list` | Список диалогов (курсорная пагинация) |
| Сообщение | `get_message_list(chat_id, chat_type, ...)` | `/msg/list-message` | Список сообщений (различные варианты пагинации см. в HTTP-клиенте) |
| Сообщение | `delete_message(msg_id, chat_id, chat_type)` | `/msg/recall-msg` | Отзыв сообщения (массовый отзыв см. в HTTP-клиенте) |
| Сообщение | `button_report(...)` | `/msg/button-report` | Отчёт о нажатии кнопки |
| Мета-действия | `get_status` / `get_version` / `get_supported_actions` | - | Состояние работы/версия/поддерживаемые действия |

### Ещё не интегрировано (эндпоинты известны, сообщения full.proto полностью описаны, можно расширять по мере необходимости)

- Пользователи: вход по коду подтверждения, медали, история золотых бобов, привязка телефона/почты, настройки уведомлений, доступ к пользовательским данным
- Друзья: «не беспокоить» (no-notify), удаление записей заявок
- Группы: список команд, категории, рекомендации, прямые эфиры, редактирование информации о группе/ники в группе/ключевых слов, автоматическое одобрение заявок в группу, ограничения на файлы группы, SSE событий
- Диалоги: закрепление/сортировка/удаление, «не беспокоить»
- Сообщения: пересылка, отправка A2UI, получение изображений из списка сообщений, история скачивания файлов
- Теги групп: list / relate / relate-cancel / create / edit / delete / members (эндпоинты `/group-tag/*`)

> Способ расширения: добавьте методы в `YunhuHTTPClient` по существующим шаблонам (универсальные обёртки `_proto_request` / `_json_request`), а затем откройте их в классе `Api`. Определения эндпоинтов и сообщений см. в `yhchatAPI/src/api/v1/*.md` и `yhchatAPI/src/full.proto`.

### Пример пользовательских API

```python
from ErisPulse import sdk
yunhu_user = sdk.adapter.get("yunhu_user")

result = await yunhu_user.Api.get_self_info()
result = await yunhu_user.Api.get_friend_requests()          # список заявок в друзья
await yunhu_user.Api.friend_agree_apply(user_id)             # принять заявку в друзья
result = await yunhu_user.Api.get_group_member_list(group_id)
result = await yunhu_user.Api.get_conversation_list()        # список диалогов
await yunhu_user.Api.delete_message(msg_id, chat_id, chat_type)  # отзыв
```

## Обработка заявок в друзья (добавлено в 4.6.0)

WebSocket пользовательского клиента Yunhu **не отправляет события заявок в друзья**, поэтому адаптер по умолчанию включает опрос для получения списка заявок и синтезирует стандартное событие запроса (в соответствии со [спецификацией операций с запросами](../standards/request-action-spec.md)):

- **Настройка аккаунта**: `poll_friend_requests = true` (включено по умолчанию), `poll_interval = 60` (интервал опроса в секундах, минимум 5 секунд); установите `false`, чтобы отключить опрос
- **Логика опроса**: по интервалу запрашивается `/friend/request-list`, после вычисления diff определяются **новые заявки** и синтезируется стандартное событие request:
  - `type="request"`, `detail_type="friend"`
  - `request_id` = **user_id отправителя заявки**
  - `user_nickname` / `comment` берутся из данных заявки, исходная запись сохраняется в `yunhu_user_raw`
- **Дедупликация событий**: обработанные заявки не генерируют повторных событий

### Одобрение на стороне модуля (через события)

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    if event.get("platform") != "yunhu_user":
        return

    applicant = event.get("user_id")
    nickname = event.get("user_nickname", "")
    comment = event.get("comment", "")
    print(f"Заявка в друзья: {nickname}({applicant}) сообщение: {comment}")

    # Принять заявку в друзья (accept = принять в друзья)
    await event.approve()
    # Или игнорировать заявку (reject = игнорировать)
    # await event.reject()
```

### Прямой вызов адаптера (Request DSL)

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# request_id — это user_id отправителя заявки
await yunhu_user.Request("user_id_отправителя").accept()   # accept = принять в друзья
await yunhu_user.Request("user_id_отправителя").reject()   # reject = игнорировать заявку

# Несколько аккаунтов: одобрение с указанием аккаунта
await yunhu_user.Request("user_id_отправителя").Using("default").accept()
```

> `accept()` внутри вызывает `/friend/agree-apply`, `reject()` вызывает `/friend/ignore-apply`; оба возвращают стандартный ответ (`status` / `retcode` / `message` / `yunhu_user_raw`).

## Соответствие стандартизации (4.6.1)

Структура ответов и коды ошибок следуют [спецификации ответов API](../standards/api-response.md).

### Стандартный ответ

Все 20 методов Api DSL возвращают стандартный ответ: `status` / `retcode` / `data` / `message_id` / `message`; исходные данные платформы находятся одновременно в `data` и в `yunhu_user_raw` верхнего уровня. Исходные данные `get_self_info` перемещены в `yunhu_user_raw` верхнего уровня ответа.

### Спецификация кодов ошибок

| retcode | Значение | Описание |
|---------|------|------|
| 0 | Успех | — |
| 33001 | Сетевая ошибка | Ошибки соединения HTTP/WS |
| 34100 | Сбой платформы | Пользовательский клиент Yunhu вернул сбой; исходный ответ сохраняется в `yunhu_user_raw` |
| 10002 | Не поддерживается | Стандартное действие, для которого у платформы нет соответствующей возможности |
| 10003 | Ошибка параметров | Отсутствует request_id, нет доступного аккаунта и т.д. |

### Исправления полей событий

- **`chat_type=3` (диалог с ботом) отображается как `private`** (прежний `"bot"` не является стандартным типом приёма; исходный chat_type сохраняется в `yunhu_user_raw`)
- **id события `edit_message` получает префикс `edit:`**: больше не возникает совпадение id с событием create, из-за которого события поглощались дедупликацией на нижележащем уровне
- **`message_id` присутствует всегда**: при отсутствии подставляется пустая строка
- **`time` события использует временную метку самого сообщения** (с точностью до секунды), вместо единого момента обработки адаптером

### Аккаунты и несколько аккаунтов

- `call_api` поддерживает два совместимых поля аккаунта: `account_id` (стандартное имя) / `_account_id` (старое имя), ApiDSL фреймворка (`Api.Using(...)`) адаптируется автоматически
- `Send` читает `send_context` (резервный аккаунт события): при вызове `Send` из контекста события по умолчанию происходит откат к исходному аккаунту
- Для ответов на события рекомендуется использовать `event.reply()`, который автоматически маршрутизирует к обрабатывающему аккаунту

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочный синтаксис, например:
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str, buttons: Optional[List] = None)`: отправка обычного текстового сообщения.
- `.Html(html: str, buttons: Optional[List] = None)`: отправка сообщения в формате HTML.
- `.Markdown(markdown: str, buttons: Optional[List] = None)`: отправка сообщения в формате Markdown.
- `.MergeForward(nodes, title="Объединённая история чата")`: отправка объединённого пересылаемого сообщения (рендерится как сворачиваемая HTML-карточка `<details>`, отправляется через HTML-канал msg_type=8).
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`: отправка изображения, поддерживает URL, локальный путь или бинарные данные.
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`: отправка видео, поддерживает URL, локальный путь или бинарные данные.
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`: отправка аудиосообщения, поддерживает URL, локальный путь или бинарные данные, автоматически определяет длительность аудио.
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`: псевдоним `.Audio()`.
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`: отправка файла, поддерживает URL, локальный путь или бинарные данные.
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`: отправка эмодзи/стикеров, поддерживает ID стикера, URL стикера или бинарные данные изображения.
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`: отправка сообщения A2UI (тип сообщения 14), данные JSON A2UI заполняются в поле text при отправке.
- `.Edit(msg_id: str, text: str, content_type: str = "text")`: редактирование существующего сообщения.
- `.Recall(msg_id: str)`: отзыв сообщения.
- `.Raw_ob12(message: Union[List, Dict])`: отправка сообщения в формате OneBot12.

### Обработка медиафайлов

Все типы медиа (изображения, видео, аудио, файлы) поддерживают следующие способы ввода:
- **URL**: `"https://example.com/image.jpg"` — автоматическая загрузка с последующей выгрузкой
- **Локальный путь**: `"/path/to/file.jpg"` — автоматическое чтение с последующей выгрузкой
- **Бинарные данные**: `open("file.jpg", "rb").read()` — прямая выгрузка

Медиафайлы автоматически загружаются в облачное хранилище Qiniu со следующими возможностями:
- Автоматическое определение типа файла и MIME через библиотеку `filetype`
- Автоматическое вычисление размера файла
- Автоматическое определение длительности аудиофайлов (поддержка форматов MP3, MP4/M4A)

### Описание параметра кнопок

Параметр `buttons` представляет собой вложенный список, описывающий компоновку и функциональность кнопок. Каждый объект кнопки содержит следующие поля:

| Поле | Тип | Обязательное | Описание |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Да       | Текст на кнопке |
| `actionType` | int    | Да       | Тип действия:<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отчёт о нажатии |
| `url`        | string | Нет      | Используется при `actionType=1`, указывает целевой URL перехода |
| `value`      | string | Нет      | При `actionType=2` это значение копируется в буфер обмена<br>При `actionType=3` это значение отправляется подписчику |

Пример:
```python
buttons = [
    [
        {"text": "Копировать", "actionType": 2, "value": "xxxx"},
        {"text": "Нажмите для перехода", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Отчёт о событии", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("Сообщение с кнопками")
```

### Цепочные методы модификации (можно комбинировать)

Цепочные методы модификации возвращают `self`, поддерживают цепочные вызовы и должны вызываться перед финальным методом отправки:

- `.Reply(message_id: str)`: ответ на указанное сообщение.
- `.At(user_id: str)`: упоминание указанного пользователя (текстовая форма @user_id).
- `.AtAll()`: упоминание всех (псевдо-@всех, отправка текста @all).
- `.Buttons(buttons: List)`: добавление кнопок.

> **Внимание:** поскольку пользовательский аккаунт довольно специфичен, упоминать всех можно даже без прав администратора, однако `AtAll()` здесь отправляет только текст упоминания всех, это псевдо-@всех.

### Примеры цепочных вызовов

```python
# Базовая отправка
await yunhu_user.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("Ответное сообщение")

# Ответ + кнопки
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Сообщение с ответом и кнопками")

# Указанный аккаунт + ответ + кнопки
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Полный цепочный вызов")
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12 для упрощения кроссплатформенной совместимости сообщений:

- `.Raw_ob12(message: List[Dict], **kwargs)`: отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 поддерживает автоматическую группировку смешанных сегментов сообщений:
- типы `text`, `mention` могут быть объединены в одну группу при отправке
- типы `image`, `video`, `audio`, `file`, `face`, `markdown`, `html`, `a2ui` и другие образуют независимые группы
- тип `reply` может быть добавлен к любой группе

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, результат отправки можно получить напрямую через await. Возвращаемый результат соответствует стандарту возврата адаптеров ErisPulse:

```python
{
    "status": "ok",           // статус выполнения
    "retcode": 0,             // код возврата
    "data": {...},            // данные ответа
    "message_id": "123456",   // ID сообщения
    "message": "",            // сообщение об ошибке
    "yunhu_user_raw": {...}   // исходные данные ответа
}
```

## Особые типы событий

Для использования особенностей данной платформы требуется проверка `platform == "yunhu_user"`

### Ключевые отличия

1. Особые типы событий:
    - Супер-передача файлов: `yunhu_user_file_send`
    - Доска объявлений бота: `yunhu_user_bot_board`
    - Уведомление о редактировании сообщения: `message_edit`
    - Уведомление об удалении сообщения: `message_delete` (отзыв)
2. Особые типы сегментов сообщений:
    - Сегмент формы: `yunhu_user_form`
    - Сегмент статьи: `yunhu_user_post`
    - Сегмент стикера: `yunhu_user_sticker`
    - Сегмент кнопок: `yunhu_user_button`
    - Сегмент A2UI: `a2ui`
3. Расширенные поля:
    - Все особые поля помечены префиксом `yunhu_user_`
    - Исходные данные сохраняются в поле `yunhu_user_raw`
    - Исходный тип события записывается в поле `yunhu_user_raw_type`
    - В личном чате `self.user_id` обозначает ID текущего вошедшего пользователя

### Поддерживаемые исходные типы событий

| Исходный тип события | Тип OneBot12 | Описание |
|-------------|--------------|------|
| `push_message` | `message` | Push-сообщение (личный чат, групповой чат, диалог с ботом) |
| `edit_message` | `notice` (`message_edit`) | Событие редактирования сообщения |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | Событие супер-передачи файлов |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | Событие доски объявлений бота |

> Другие типы событий (например, `heartbeat_ack`, `draft_input`, `stream_message` и т.д.) игнорируются.

### detail_type, поддерживаемые OneBot12

| OneBot12 detail_type | chat_type Yunhu | Описание |
|---------------------|---------------|------|
| `private` | 1 | Сообщения личного чата |
| `group` | 2 | Сообщения группового чата |
| `private` | 3 | Диалог с ботом (начиная с 4.6.1 отображается как `private`, прежний `"bot"` нестандартный; исходный chat_type сохраняется в `yunhu_user_raw`) |

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
        {"type": "text", "data": {"text": "Содержимое сообщения"}}
    ],
    "alt_message": "Содержимое сообщения",
    "user_id": "sender_user_id",
    "user_nickname": "Ник отправителя",
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
    "user_nickname": "Ник отправителя",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### Пример события супер-передачи файлов

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
        "content": "Содержимое объявления",
        "content_type": 1,
        "last_update_time": 1234567890
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "bot_board_message"
}
```

### Примеры обработки событий

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
    
    # Проверка особых типов в сегментах сообщения
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"Получено сообщение с формой: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"Получено сообщение со статьёй: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"Получено сообщение со стикером: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"Сообщение содержит кнопки: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"Получено сообщение A2UI: {a2ui_data}")
    
    # Автоответ с использованием event.reply()
    await event.reply(f"Echo: {alt_message}")

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
        print(f"Получена супер-передача файла: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"Бот {bot_name} опубликовал объявление: {board_data.get('content', '')}")
```

## Описание расширенных полей

- Все особые поля помечены префиксом `yunhu_user_` во избежание конфликтов со стандартными полями
- Исходные данные сохраняются в поле `yunhu_user_raw`, что облегчает доступ к полным исходным данным платформы Yunhu
- Исходный тип события записывается в поле `yunhu_user_raw_type` (например, `push_message`, `edit_message` и т.д.)
- `self.user_id` обозначает ID текущего вошедшего пользователя (получается из ответа на вход)
- Супер-передача файлов предоставляет данные о передаче через поле `yunhu_user_file_send`
- Доска объявлений бота предоставляет данные объявлений через поле `yunhu_user_bot_board`

### Особые типы сегментов сообщений

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
        "post_content": "Содержимое статьи"
    }
}
```

| Поле | Тип | Описание |
|------|------|------|
| `post_id` | string | Уникальный идентификатор статьи |
| `post_title` | string | Заголовок статьи |
| `post_content` | string | Содержимое статьи |

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

Когда сообщение содержит кнопки, добавляется сегмент `yunhu_user_button`:

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

## Конфигурация нескольких аккаунтов

### Описание конфигурации

YunhuUserAdapter поддерживает одновременную настройку и запуск нескольких пользовательских аккаунтов.

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # интервал переподключения WebSocket (секунды)
ws_timeout = 70             # тайм-аут WebSocket (секунды)

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # почта пользователя (обязательно)
password = "password1"       # пароль пользователя (обязательно)
platform = "windows"         # платформа входа (необязательно, по умолчанию windows)
device_id = ""               # ID устройства (необязательно, генерируется автоматически, если не указано)
poll_friend_requests = true  # опрос заявок в друзья (необязательно, по умолчанию true)
poll_interval = 60           # интервал опроса заявок в друзья (секунды, необязательно, по умолчанию 60)
enabled = true               # включён ли (необязательно, по умолчанию true)

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**Описание параметров конфигурации:**
- `email`: почта пользователя (обязательно), используется для входа на платформу Yunhu
- `password`: пароль пользователя (обязательно)
- `platform`: идентификатор платформы входа (необязательно, по умолчанию `windows`), возможные значения: `windows`, `macos`, `linux`, `ios`, `android`
- `device_id`: ID устройства (необязательно, генерируется автоматически, если не указано), рекомендуется указать фиксированное значение для консистентности сессии
- `poll_friend_requests`: опрашивать ли заявки в друзья (необязательно, по умолчанию `true`; см. раздел «Обработка заявок в друзья»)
- `poll_interval`: интервал опроса заявок в друзья (секунды, необязательно, по умолчанию 60, минимум 5)
- `enabled`: включён ли данный аккаунт (необязательно, по умолчанию `true`)

**Конфигурация уровня адаптера:**
- `ws_reconnect_interval`: интервал переподключения WebSocket (секунды, по умолчанию 30)
- `ws_timeout`: тайм-аут WebSocket (секунды, по умолчанию 70)

**Важные замечания:**
1. Адаптер получает token через вход по электронной почте, после входа получает события через WebSocket
2. При разрыве WebSocket-соединения выполняется автоматическое переподключение, не более 3 попыток
3. Рекомендуется устанавливать фиксированный `device_id` для каждого аккаунта, чтобы сохранить консистентность сессии
4. Немодифицированные шаблонные аккаунты (почта и пароль по умолчанию) автоматически пропускаются

### Указание аккаунта через Send DSL

Можно указать, какой аккаунт использовать для отправки сообщений, через метод `Using()`. Метод поддерживает два типа параметров:
- **Имя аккаунта**: имя аккаунта из конфигурации (например, `default`, `account2`)
- **user_id**: ID пользователя, полученный после входа

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# Отправка сообщения с указанием имени аккаунта
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# Отправка сообщения по user_id (автоматически сопоставляется с соответствующим аккаунтом)
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# Если не указано, используется первый включённый аккаунт
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **Подсказка:** при использовании `user_id` система автоматически ищет соответствующий аккаунт в конфигурации. Это особенно полезно при обработке ответов на события — можно напрямую использовать `event["self"]["user_id"]` для ответа от того же аккаунта.

### Идентификация аккаунта в событиях

Полученные события автоматически содержат соответствующую информацию об ID пользователя:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # Получить ID текущего вошедшего пользователя
        my_user_id = event["self"]["user_id"]
        print(f"Сообщение от аккаунта: {my_user_id}")
        
        # Ответить с использованием того же аккаунта
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответное сообщение")
```

### Информация в журнале

Адаптер автоматически включает информацию об аккаунте в журнал для упрощения отладки и отслеживания:

```
[INFO] Аккаунт default (user1@example.com) успешно вошёл, ID пользователя: 12345678
[INFO] Задача прослушивания WebSocket для аккаунта default запущена
[INFO] Аккаунт account2 (user2@example.com) успешно вошёл, ID пользователя: 87654321
```

### Интерфейсы управления

```python
# Получить информацию обо всех аккаунтах
accounts = yunhu_user.accounts
# Формат возврата: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# Проверить, включён ли аккаунт
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# Получить HTTP-клиент по имени аккаунта
http_client = yunhu_user._get_http_client("default")

# Найти аккаунт по user_id
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## Вызовы API

Адаптер предоставляет метод `call_api`, поддерживающий прямые вызовы API платформы:

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

# Отзыв сообщения
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# Массовый отзыв сообщений
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

# Получение истории редактирований сообщения
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# Отчёт о событии нажатия кнопки
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
| `/recall` | Отзыв сообщения |
| `/recall_batch` | Массовый отзыв сообщений |
| `/list` | Получение списка сообщений |
| `/list_by_seq` | Получение сообщений по последовательности |
| `/list_by_mid_seq` | Получение сообщений по ID сообщения и последовательности |
| `/list_edit_record` | Получение истории редактирований сообщения |
| `/button_report` | Отчёт о событии нажатия кнопки |