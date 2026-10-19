# Характеристики платформы Yunhu

YunhuAdapter — это адаптер, построенный на протоколе Yunhu, объединяющий все модули Yunhu и предоставляющий единый интерфейс для обработки событий и операций сообщений.

---

## Информация о документации

- Соответствующая версия модуля: 4.5.0
- Ответственный: ErisPulse

## Основная информация

- Краткое описание платформы: Yunhu — это корпоративная платформа мгновенного обмена сообщениями
- Название адаптера: YunhuAdapter
- Поддержка нескольких аккаунтов: Поддержка идентификации и настройки нескольких аккаунтов бота Yunhu с помощью bot_id
- Поддержка цепочечных модификаторов: Поддержка цепочечных методов модификации, таких как `.Reply()`
- Совместимость с OneBot12: Поддержка отправки сообщений в формате OneBot12

## Обновление до парадигмы v5 (4.4.0)

Данный адаптер завершил согласование с парадигмой v5 (постепенное обновление, совместимость API):

- **Полный набор API-интерфейсов официального сервера** (расширения DSL-методов API): редактирование сообщений, массовая отправка, список сообщений, пользовательские/глобальные доски, ограничение участников группы, удаление участников группы, управление типами сообщений в группе, CRUD-операции с тегами группы, добавление тегов пользователя
- **Стандартный сегмент keyboard** (стандартный компонент взаимодействия между платформами): {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} автоматически преобразуется в кнопки Yunhu; модификаторы .Buttons(rows) / .Keyboard(rows) принимают общую структуру (оригинальная структура обратно совместима)
- **Стандартные поля обратного вызова взаимодействия**: события кнопки/ A2UI включают стандартные поля interaction_id / button_data
- **Принадлежность задачи spawn_background**: задачи подключения WS используют runtime.spawn_background
- **Мягкая зависимость от фреймворка**: во время выполнения проверяется ErisPulse>=2.7.1 и выводится предупреждение; при запуске выводится лог версии

### Расширенные действия платформы (методы call / Api)

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Методы Api (официальные API сервера)
await yunhu.Api.edit_message(msg_id, recv_id, "group", "text", {"text": "новое содержание"})
await yunhu.Api.batch_send(["userId1", "userId2"], "text", {"text": "объявление"})
await yunhu.Api.get_message_list(group_id, "group", before=10)
await yunhu.Api.set_user_board(chat_id, "group", "содержание доски", expire_time=3600)
await yunhu.Api.dismiss_global_board()
await yunhu.Api.gag_group_member(group_id, user_id, 600)      # ограничение на 600 секунд, 0=снять
await yunhu.Api.remove_group_member(group_id, user_id)
await yunhu.Api.set_group_msg_type_limit(group_id, "text,image")
await yunhu.Api.create_group_tag(group_id, "VIP", color="#FF5733")
await yunhu.Api.add_user_tag(group_id, user_id, "VIP")

# Обратный вызов нажатия кнопки (стандартные поля)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "yunhu" and event.get("button_data"):
        data = event["button_data"]     # унифицированное получение значений
        interaction_id = event["interaction_id"]
```

> Полное описание стандарта см. в [стандарте компонента взаимодействия между платформами](../standards/standardization-guide.md).

---
## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с помощью цепочечной синтаксис, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка текстового сообщения.
- `.Html(html: str)` — отправка HTML-форматированного сообщения.
- `.Markdown(markdown: str)` — отправка Markdown-форматированного сообщения.
- `.MergeForward(nodes, title="объединённая переписка")` — отправка объединённого пересланного сообщения (отображается как карточка HTML с раскрытием, отправляется через канал HTML).
- `.A2UI(text: str)` — отправка сообщения в формате A2UI.
- `.Image(file: bytes, stream: bool = False, filename: str = None)` — отправка изображения, поддержка потоковой загрузки и пользовательского имени файла.
- `.Video(file: bytes, stream: bool = False, filename: str = None)` — отправка видео, поддержка потоковой загрузки и пользовательского имени файла.
- `.File(file: bytes, stream: bool = False, filename: str = None)` — отправка файла, поддержка потоковой загрузки и пользовательского имени файла.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)` — массовая отправка сообщений.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)` — редактирование существующего сообщения.
- `.Recall(msg_id: str)` — отмена отправки сообщения.
- `.Board(content: str, content_type: str = "text")` — публикация доски объявлений. Область действия определяется методом `To()` (указанный целевой объект=локальная доска, не указан=глобальная доска). Цепочечные модификаторы: `.Expire(duration)` относительный срок истечения (в секундах), `.ExpireAt(timestamp)` абсолютный срок истечения (в секундах), `.ForMember(member_id)` доска для участника группы; при пустом содержании автоматически отменяется доска. По-прежнему поддерживается старый формат `Board("local", "объявление")`.
- `.DismissBoard()` — отмена доски объявлений. Область действия определяется методом `To()`; поддерживается `.ForMember(member_id)`; по-прежнему поддерживается старый формат `DismissBoard("local")`.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)` — отправка потокового сообщения.

### Методы управления группой

Все методы управления группой необходимо использовать с цепочечным синтаксисом для указания группы, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)` — удаление участника группы. Бот должен иметь права "разрешить удаление участников группы".
- `.Ban(user_id: str, duration: int = 600)` — ограничение участника. `duration` — продолжительность ограничения (в секундах), 0 — снять ограничение, -1 — пожизненное ограничение. Бот должен иметь права "разрешить ограничение участников".
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)` — создание тега группы. `color` в формате #RRGGBB, `sort` — чем меньше, тем выше тег. Бот должен иметь права "разрешить управление тегами".
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)` — изменение тега группы. Параметры необязательны, если не переданы, то не изменяются. Бот должен иметь права "разрешить управление тегами".
- `.DeleteTag(tag: str)` — удаление тега группы. Бот должен иметь права "разрешить управление тегами".
- `.GetTagList()` — получение списка тегов группы. Возвращает ответ с массивом `list`.
- `.AddUserTag(user_id: str, tag: str)` — добавление тега пользователю. Бот должен иметь права "разрешить управление тегами".
- `.RemoveUserTag(user_id: str, tag: str)` — удаление тега у пользователя. Бот должен иметь права "разрешить управление тегами".
- `.SetMsgTypeLimit(types: str)` — ограничение типов сообщений в группе. `types` — имена типов сообщений, разделённые запятыми (например, "text,image,video"), пустая строка означает отсутствие ограничений. Бот должен иметь права "разрешить изменение информации о группе".

### Методы запроса сообщений

Получение истории сообщений в указанном диалоге (пользователь/группа) необходимо использовать с цепочечным синтаксисом для указания цели, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)` — получение истории сообщений в диалоге. Возвращает ответ с массивом `list` и общим количеством `total`.
  - `message_id` — идентификатор сообщения (необязательно). Если не указан, в сочетании с `before` возвращает последние N сообщений.
  - `before` — возвращает N сообщений до указанного идентификатора.
  - `after` — возвращает N сообщений после указанного идентификатора.
  - > **Примечание:** нужно указать хотя бы одно из `before` и `after`, и значение должно быть больше 0, иначе сервер не вернёт никаких сообщений.

Доска объявлений определяется автоматически методом `To()`:
- Указание `To(target_type, target_id)` → локальная доска (указанная группа/пользователь)
- Не указание `To()` → глобальная доска

```python
# Локальная доска (относительный срок истечения через 60 секунд)
await yunhu.Send.To("group", group_id).Expire(60).Board("объявление", content_type="markdown")

# Доска для участника группы (видна только указанному участнику)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("видно только тебе")

# Абсолютный срок истечения
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("объявление с указанным временем")

# Глобальная доска
await yunhu.Send.Board("глобальное объявление")

# Очистка локальной доски (пустое содержание → автоматическая отмена)
await yunhu.Send.To("group", group_id).Board("")
```

### Описание параметров кнопок

Параметр `buttons` — это вложенный список, обозначающий макет кнопок. Каждый объект кнопки содержит следующие поля:

| Поле         | Тип   | Обязательно | Описание                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Да       | Текст на кнопке                                                         |
| `actionType` | int    | Да       | Тип действия:<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отправка события            |
| `url`        | string | Нет       | Используется, когда `actionType=1`, обозначает целевой URL для перехода                         |
| `value`      | string | Нет       | Используется, когда `actionType=2`, значение копируется в буфер обмена<br>Используется, когда `actionType=3`, значение отправляется подписчику |

Пример:
```python
buttons = [
    [
        {"text": "копировать", "actionType": 2, "value": "xxxx"},
        {"text": "перейти", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "отправить событие", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("сообщение с кнопками")
```
> **Примечание:**
> - Только при нажатии кнопки типа "отправить событие" пользователь получит уведомление, на кнопки "копировать" и "перейти" уведомление не приходит.

### Цепочечные модификаторы (можно комбинировать)

Цепочечные модификаторы возвращают `self`, поддерживают цепочечное использование, должны вызываться перед окончательным методом отправки:

- `.Reply(message_id: str)` — ответ на указанное сообщение.
- `.At(user_id: str)` — упоминание указанного пользователя.
- `.AtAll()` — упоминание всех участников.
- `.Buttons(buttons: List)` — добавление кнопок.

### Примеры цепочечного вызова

```python
# Базовая отправка
await yunhu.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("ответ на сообщение")

# Ответ + кнопки
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("сообщение с ответом и кнопками")
```

### Примеры управления группой

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Удаление участника группы
await yunhu.Send.To("group", group_id).Kick(user_id)

# Ограничение пользователя (10 минут)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Снятие ограничения
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Пожизненное ограничение
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Создание тега группы
await yunhu.Send.To("group", group_id).CreateTag("VIP-пользователь", color="#FF5733", desc="VIP-член")

# Изменение тега группы
await yunhu.Send.To("group", group_id).EditTag("VIP-пользователь", new_tag="SVIP-пользователь", color="#33C4FF")

# Удаление тега группы
await yunhu.Send.To("group", group_id).DeleteTag("VIP-пользователь")

# Получение списка тегов группы
result = await yunhu.Send.To("group", group_id).GetTagList()

# Добавление тега пользователю
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP-пользователь")

# Удаление тега у пользователя
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP-пользователь")

# Ограничение типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Снятие ограничения типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Примеры запроса сообщений

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Получение последних 10 сообщений в группе (всего возвращается 10)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Получение 10 сообщений перед указанным ID (всего возвращается 11)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Получение по 10 сообщений до и после указанного ID (всего возвращается 21)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Получение истории сообщений в диалоге с пользователем
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12, что упрощает кроссплатформенную совместимость сообщений:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "ответ на сообщение"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Стандартные API действия (ApiDSL)

> [!NOTE]
> Эта функция требует ErisPulse **2.7.0+** и YunhuAdapter **4.3.0+**.

Помимо `Send` цепочечной отправки, адаптер предоставляет внутренний класс `Api`, который экспортирует стандартные API действия OneBot12 и расширенные действия платформы Yunhu. Все методы возвращают стандартный формат ответа.

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Информация (через публичный Web API, без аутентификации)
result = await yunhu.Api.get_self_info()              # информация о боте
result = await yunhu.Api.get_user_info("7058262")     # информация о пользователе
result = await yunhu.Api.get_group_info("635409929")  # информация о группе

# Файловые операции
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# Отмена сообщения (требуется предоставить chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Многоаккаунтность: указание аккаунта бота
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Поддерживаемые стандартные действия

| Метод | Описание | Источник данных |
|------|------|---------|
| `get_self_info()` | Информация о боте | Публичный Web API (bot-info) |
| `get_user_info(user_id)` | Информация о пользователе (любой пользователь может получить) | Публичный Web API (user/homepage) |
| `get_group_info(group_id)` | Информация о группе | Публичный Web API (group-info) |
| `upload_file(*, type, name, ...)` | Загрузка файла (автоматически определяется image/video/file) | Bot открытый API |
| `get_file(file_id)` | Получение файла (file_id — это URL) | — |
| `delete_message(message_id, *, chat_id, chat_type)` | Отмена сообщения | Bot открытый API (/bot/recall) |

> **Примечание:** `get_self_info` / `get_user_info` / `get_group_info` реализованы через **непубличный публичный Web API** (chat-web-go.jwzhd.com), эти интерфейсы не требуют аутентификации, но не являются официальной документацией и могут изменяться с обновлением платформы; в случае сбоя возвращается стандартный ответ об ошибке.

### Неподдерживаемые стандартные действия

Следующие стандартные действия не поддерживаются платформой Yunhu, при вызове возвращается `retcode=10002` (не поддерживаемая операция):
- `get_friend_list` (бот открытый API "список пользователей бота" находится в ожидании выхода)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Расширенные действия платформы

С помощью `Api.call("yunhu.xxx", **params)` вызываются расширенные действия платформы Yunhu (параметры используют стиль именования OB12, адаптер автоматически переводит их в поля Yunhu):

| Расширенное действие | Описание | Эквивалентный метод Send |
|---------|------|---------------|
| `yunhu.recall` | Отмена сообщения (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Удаление участника группы (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Ограничение (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Снятие ограничения (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | CRUD тегов группы (group_id, ...) | `Send.To("group", g).CreateTag(...)` и т.д. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Добавление/удаление тега у пользователя | `Send.To("group", g).AddUserTag(...)` и т.д. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Синоним семантики титула участника** (тег ≈ титул, внутреннее отображение на tag.relate) | — |
| `yunhu.msg_type_limit` | Ограничение типов сообщений в группе (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Получение истории сообщений (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Открытый запрос информации о боте (bot_id) | — |
| `yunhu.user_homepage` | Открытый запрос домашней страницы пользователя (user_id) | — |

```python
# Пример расширенных действий
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Теги и титулы:** Семантика "тегов" в Yunhu эквивалентна OneBot12 "титулу" участника группы. `yunhu.set_member_title` — это синоним семантического названия `yunhu.tag.relate`, оба внутренне отображаются на один и тот же конечный точку. Роль отправителя в событии сообщения отображается из `senderUserLevel` в стандартное поле `role` (`owner/admin/member`). 

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект задачи, который можно ожидать с помощью await для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "self": {...},            // Информация о себе (содержит bot_id)
    "message_id": "123456",   // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "yunhu_raw": {...}        // Исходные данные ответа
}
```

## Специфические типы событий

Необходимо проверять platform=="yunhu" перед использованием функций платформы

### Основные отличия

1. Специфические типы событий:
    - Формы (например, команды формы): yunhu_form
    - Эмодзи/стикеры: yunhu_expression
    - Нажатие кнопки: yunhu_button_click
    - Нажатие кнопки A2UI: yunhu_a2ui_button
    - Настройки бота: yunhu_bot_setting
    - Быстрое меню: yunhu_shortcut_menu
2. Расширение стандартных полей (4.3.0+):
    - В событиях сообщений добавлено стандартное поле `role` (отображается из `senderUserLevel` в `owner`/`admin`/`member`)
    - Добавлено поле `user_avatar` (URL аватара отправителя)
3. Расширенные поля:
    - Все специфические поля имеют префикс yunhu_
    - Оригинальные данные сохраняются в поле yunhu_raw
    - В личных сообщениях self.user_id обозначает ID бота

### Примеры специальных полей

```python
# Команда формы
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "имя команды формы",
    "id": "ID команды",
    "form": {
      "ID_поля1": {
        "id": "ID_поля1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "метка поля",
        "value": "значение поля"
      }
    }
  }
}

# Событие нажатия кнопки
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "ID пользователя, нажавшего кнопку",
  "user_nickname": "никнейм пользователя",
  "message_id": "ID сообщения",
  "yunhu_button": {
    "id": "ID кнопки (может быть пустым)",
    "value": "значение кнопки"
  }
}

# Событие нажатия кнопки A2UI
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "ID пользователя, выполнившего действие",
  "user_nickname": "никнейм пользователя",
  "message_id": "ID сообщения",
  "yunhu_a2ui": {
    "recv_id": "ID получателя",
    "recv_type": "тип получателя",
    "action_name": "название действия",
    "source_component_id": "ID исходного компонента",
    "form_context": {},
    "interaction_json": "JSON-строка данных взаимодействия"
  }
}

### Пример обработки события нажатия кнопки

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Обработка уведомлений платформы Yunhu

    Использование универсального декоратора on_notice() для обработки всех уведомлений,
    затем с помощью detail_type различать типы уведомлений
    event.reply() автоматически отправит ответ через платформу Yunhu
    """
    # Проверка, является ли это событием нажатия кнопки
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"Пользователь {user_nickname}({user_id}) нажал кнопку: {button_value}")

        # Использование event.reply() для автоматической отправки ответа (в зависимости от платформы будет выбран правильный способ отправки)
        if button_value == "confirm":
            await event.reply("Вы нажали кнопку подтверждения!")
        elif button_value == "cancel":
            await event.reply("Операция отменена")
        else:
            await event.reply(f"Получен ваш выбор: {button_value}")

    # Обработка события быстрого меню
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"Запущено быстрое меню: {menu_id}")

    # Обработка изменения настроек бота
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"Настройки обновлены: {settings}")

    # Обработка события кнопки A2UI
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"Действие A2UI: {action_name}, данные формы: {form_context}")
```

### Использование цепочечного вызова для отправки сообщения с кнопками

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "Подтвердить", "actionType": 3, "value": "confirm"},
        {"text": "Отменить", "actionType": 3, "value": "cancel"},
        {"text": "Посмотреть подробнее", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# Отправка сообщения с кнопками в группе
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Пожалуйста, подтвердите следующую операцию")

# Отправка сообщения с кнопками в личном чате
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Выберите свои предпочтения")
```

### Отправка сообщения A2UI

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# Отправка сообщения A2UI
await yunhu.Send.To("user", user_id).A2UI("Содержание карточки A2UI")
```

# Настройки бота
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "ID группы (может быть пустым)",
  "user_nickname": "Никнейм пользователя",
  "yunhu_setting": {
    "ID_параметра": {
      "id": "ID параметра",
      "type": "input/radio/checkbox/select/switch",
      "value": "Значение параметра"
    }
  }
}

# Быстрое меню
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "ID пользователя, запустившего меню",
  "user_nickname": "Никнейм пользователя",
  "group_id": "ID группы (если это групповой чат)",
  "yunhu_menu": {
    "id": "ID меню",
    "type": "Тип меню (целое число)",
    "action": "Действие меню (целое число)"
  }
}
```

## Расширенные методы Event Mixin

Адаптер зарегистрировал следующие платформо-специфичные методы, доступные только при `platform == "yunhu"`:

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_raw_event()` | `dict` | Получение исходных данных события Yunhu (в `yunhu_raw`) |
| `get_sender_level()` | `str` | Уровень отправителя в Yunhu (owner/administrator/member/unknown) |
| `get_sender_role()` | `str` | Роль отправителя в стандарте OneBot12 (owner/admin/member) |
| `get_sender_title()` | `str` | Титул отправителя (доступ к стандартному полю title, зарезервирован) |
| `get_sender_avatar()` | `str` | URL аватара отправителя |
| `get_command()` | `dict` | Данные команды (только для событий команд, `yunhu_command`) |
| `get_button_value()` | `str` | Значение кнопки в событии нажатия (в `yunhu_button.value`) |
| `get_a2ui_action()` | `str` | Действие A2UI в событии нажатия кнопки A2UI |
| `get_a2ui_form_context()` | `dict` | Контекст формы в событии нажатия кнопки A2UI |
| `get_menu_id()` | `str` | ID события быстрого меню (в `yunhu_menu.id`) |
| `get_setting()` | `dict` | Данные настроек в событии настройки бота (в `yunhu_setting`) |
| `is_command_message()` | `bool` | Является ли сообщение командой |
| `is_button_click()` | `bool` | Является ли событием нажатия кнопки |
| `is_a2ui_button()` | `bool` | Является ли событием нажатия кнопки A2UI |

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    if event.get("platform") != "yunhu":
        return

    if event.is_button_click():
        value = event.get_button_value()
        await event.reply(f"Вы нажали кнопку: {value}")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()
```

## Описание расширенных полей

- Все специфические поля имеют префикс `yunhu_`, чтобы избежать конфликтов с обычными полями
- Оригинальные данные сохраняются в поле `yunhu_raw`, что позволяет получить полные исходные данные платформы Yunhu
- `self.user_id` обозначает ID бота (получается из bot_id в конфигурации)
- Команды через `yunhu_command` предоставляют структурированные данные
- Нажатие кнопок через `yunhu_button` предоставляет информацию о кнопке
- Нажатие кнопок A2UI через `yunhu_a2ui` предоставляет информацию о взаимодействии A2UI
- Изменение настроек бота через `yunhu_setting` предоставляет данные настроек
- Операции быстрого меню через `yunhu_menu` предоставляют информацию о меню
- Эмодзи/стикеры через `yunhu_expression` предоставляют данные стикера (sticker_id, ID пакета стикеров, размер изображения и т.д.)

### Сегмент эмодзи/стикера (yunhu_expression)

Когда пользователь отправляет эмодзи или стикер, тип сегмента сообщения — `yunhu_expression`:

```json
{
  "type": "yunhu_expression",
  "data": {
    "sticker_id": "35154",
    "sticker_pack_id": "1670",
    "expression_id": "0",
    "image_name": "sticker/fabb9077f2ba302402ea871cab3686ad7a3fc52c.gif",
    "width": 500,
    "height": 500
  }
}
```

| Поле | Тип | Описание |
|------|------|------|
| `sticker_id` | string | Уникальный идентификатор стикера |
| `sticker_pack_id` | string | ID пакета стикеров |
| `expression_id` | string | ID эмодзи |
| `image_name` | string | Путь к файлу изображения стикера |
| `width` | int | Ширина изображения (опционально) |
| `height` | int | Высота изображения (опционально) |

Пример использования:
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"Получен стикер: sticker_id={data['sticker_id']}, ID пакета={data['sticker_pack_id']}")
```

---

## Конфигурация нескольких ботов

### Описание конфигурации

Адаптер Yunhu поддерживает одновременную конфигурацию и запуск нескольких аккаунтов ботов Yunhu.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # API token бота (обязательно)
mode = "ws"  # Режим получения (опционально, по умолчанию "ws", значения: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Путь для webhook (опционально, по умолчанию "/webhook")
enabled = true  # Включено ли (опционально, по умолчанию true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # API token второго бота
webhook_path = "/webhook/bot2"  # Отдельный путь webhook
enabled = true
```

**Описание параметров:**
- `token` — API token, предоставленный платформой Yunhu (обязательно)
- `mode` — режим получения (опционально, по умолчанию "ws", значения: "ws", "webhook")
- `webhook_path` — HTTP путь для получения событий Yunhu (опционально, по умолчанию "/webhook", используется только в режиме webhook)
- `enabled` — включён ли этот аккаунт (опционально, по умолчанию true)

**Важное замечание:**
1. ID бота на платформе Yunhu автоматически определяется во время выполнения, не нужно указывать его в конфигурации
2. В режиме webhook каждый бот должен иметь отдельный `webhook_path`, чтобы получать свои события webhook
3. При настройке webhook на платформе Yunhu нужно указать соответствующие URL для каждого бота, например:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Использование Send DSL для указания бота

Можно использовать метод `Using()` для указания, каким ботом отправлять сообщение. Этот метод поддерживает два параметра:
- **Имя аккаунта** — имя бота в конфигурации (например, `bot1`, `bot2`)
- **bot_id** — значение `bot_id` в конфигурации

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Отправка сообщения с помощью имени аккаунта
await yunhu.Send.Using("bot1").To("user", "user123").Text("Привет от bot1!")

# Отправка сообщения с помощью bot_id (автоматически сопоставляется с соответствующим аккаунтом)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Привет от бота!")

# Не указывая, используется первый включённый бот
await yunhu.Send.To("user", "user123").Text("Привет от бота по умолчанию!")
```

> **Примечание:** При использовании `bot_id` система автоматически находит соответствующий аккаунт в конфигурации. Это особенно полезно при обработке событий, где можно использовать `event["self"]["user_id"]` для ответа от того же аккаунта.

### Идентификатор бота в событиях

Полученные события автоматически содержат информацию о `bot_id`:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Получение ID бота, вызвавшего событие
        bot_id = event["self"]["user_id"]
        print(f"Сообщение от бота: {bot_id}")
        
        # Использование того же бота для ответа
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответное сообщение")
```

### Логирование

Адаптер автоматически включает информацию о `bot_id` в логи, что упрощает отладку и отслеживание:

```
[INFO] [yunhu] [bot:30535459] Получено сообщение от пользователя user123
[INFO] [yunhu] [bot:12345678] Сообщение отправлено успешно, message_id: abc123
```

### Интерфейс управления

```python
# Получение информации обо всех аккаунтах
bots = yunhu.bots

# Проверка статуса аккаунта
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# Динамическое включение/отключение аккаунта (требуется перезапуск адаптера)
yunhu.bots["bot1"].enabled = False
```

### Совместимость со старой конфигурацией

Старая конфигурация `[Yunhu_Adapter.bots.*]` (с полем `bot_id`) автоматически мигрируется в формат `accounts` (поле `bot_id` теперь определяется во время выполнения, значение в конфигурации игнорируется); рекомендуется как можно скорее перейти на новый формат.