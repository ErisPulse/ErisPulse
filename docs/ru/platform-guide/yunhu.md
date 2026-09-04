# Документация по функциям платформы Yunhu

YunhuAdapter — это адаптер, построенный на протоколе Yunhu, объединяющий все модули функций Yunhu и предоставляющий единый интерфейс обработки событий и операций сообщений.

---

## Информация о документации

- Соответствующая версия модуля: 4.3.0
- Ответственный: ErisPulse

## Основная информация

- Краткое описание платформы: Yunhu — это корпоративная платформа мгновенного обмена сообщениями
- Название адаптера: YunhuAdapter
- Поддержка нескольких аккаунтов: поддержка идентификации и настройки нескольких аккаунтов роботов Yunhu через bot_id
- Поддержка цепочечных модификаторов: поддержка цепочечных методов модификации, таких как `.Reply()`
- Совместимость с OneBot12: поддержка отправки сообщений в формате OneBot12

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочечную синтаксическую конструкцию, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка обычного текста.
- `.Html(html: str)` — отправка HTML-форматированного сообщения.
- `.Markdown(markdown: str)` — отправка Markdown-форматированного сообщения.
- `.A2UI(text: str)` — отправка сообщения в формате A2UI.
- `.Image(file: bytes, stream: bool = False, filename: str = None)` — отправка изображения, поддержка потоковой загрузки и пользовательского имени файла.
- `.Video(file: bytes, stream: bool = False, filename: str = None)` — отправка видео, поддержка потоковой загрузки и пользовательского имени файла.
- `.File(file: bytes, stream: bool = False, filename: str = None)` — отправка файла, поддержка потоковой загрузки и пользовательского имени файла.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)` — массовая отправка сообщений.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)` — редактирование существующего сообщения.
- `.Recall(msg_id: str)` — отмена отправки сообщения.
- `.Board(content: str, content_type: str = "text")` — публикация объявления на доске. Область действия определяется `To()` (указанный целевой объект — локальная доска, не указано — глобальная доска). Цепочечные модификаторы: `.Expire(duration)` относительный срок действия (в секундах), `.ExpireAt(timestamp)` абсолютный срок действия (секундный временной штамп), `.ForMember(member_id)` доска для участника группы; **при пустом содержании автоматически превращается в отмену доски**. По-прежнему поддерживается старый стиль `Board("local", "объявление")` с явным указанием области действия.
- `.DismissBoard()` — отмена объявления на доске. Область действия определяется `To()` и поддерживает `.ForMember(member_id)`; по-прежнему поддерживается старый стиль `DismissBoard("local")`.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)` — отправка потокового сообщения.

### Методы управления группами

Все методы управления группами необходимо вызывать через цепочечную конструкцию, указывая группу, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)` — удаление участника группы. Робот должен иметь права "Разрешить удаление участников группы".
- `.Ban(user_id: str, duration: int = 600)` — запрет пользователя. `duration` — длительность запрета (в секундах), 0 — разрешить, -1 — пожизненный запрет. Робот должен иметь права "Разрешить запрет участников".
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)` — создание тега группы. `color` в формате #RRGGBB, `sort` — чем меньше, тем выше в списке. Робот должен иметь права "Разрешить управление тегами группы".
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)` — изменение тега группы. Все параметры необязательны, не передаются — не изменяются. Робот должен иметь права "Разрешить управление тегами группы".
- `.DeleteTag(tag: str)` — удаление тега группы. Робот должен иметь права "Разрешить управление тегами группы".
- `.GetTagList()` — получение списка тегов группы. Возвращает данные с массивом `list`.
- `.AddUserTag(user_id: str, tag: str)` — добавление тега пользователю. Робот должен иметь права "Разрешить управление тегами группы".
- `.RemoveUserTag(user_id: str, tag: str)` — удаление тега у пользователя. Робот должен иметь права "Разрешить управление тегами группы".
- `.SetMsgTypeLimit(types: str)` — ограничение типов сообщений в группе. `types` — имена типов сообщений, разделённые запятыми (например, `"text,image,video"`), пустая строка означает неограниченный доступ. Робот должен иметь права "Разрешить изменение информации группы".

### Методы получения истории сообщений

Получение списка истории сообщений для заданного диалога (пользователь/группа), необходимо указывать целевой объект через цепочечную конструкцию, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)` — получение истории сообщений диалога. Возвращает данные с массивом `list` и общим количеством `total`.
  - `message_id` — ID сообщения (необязательно). Если не указан, в сочетании с `before` возвращает последние N сообщений.
  - `before` — возвращает N сообщений до указанного ID.
  - `after` — возвращает N сообщений после указанного ID.
  - > **Примечание:** `before` и `after` должны быть указаны хотя бы один и быть больше 0, иначе сервер не вернёт никаких сообщений.

Область действия доски определяется `To()` автоматически:
- Указанный `To(target_type, target_id)` → локальная доска (указанный пользователь/группа)
- Не указано `To()` → глобальная доска

```python
# Локальная доска (относительный срок действия через 60 секунд)
await yunhu.Send.To("group", group_id).Expire(60).Board("объявление", content_type="markdown")

# Доска для участника группы (видна только указанному участнику)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("видно только тебе")

# Абсолютный срок действия по временному штампу
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("объявление с указанным сроком")

# Глобальная доска
await yunhu.Send.Board("глобальное объявление")

# Очистка локальной доски (пустое содержание → автоматически отмена)
await yunhu.Send.To("group", group_id).Board("")
```

### Описание параметров кнопок

Параметр `buttons` представляет собой вложенный список, описывающий расположение и функциональность кнопок. Каждый объект кнопки содержит следующие поля:

| Поле         | Тип   | Обязательно | Описание                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Да       | Текст на кнопке                                                         |
| `actionType` | int    | Да       | Тип действия:<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отправка события |
| `url`        | string | Нет       | Используется, когда `actionType=1`, указывает целевой URL для перехода                         |
| `value`      | string | Нет       | Используется, когда `actionType=2`, значение копируется в буфер обмена<br>Используется, когда `actionType=3`, значение отправляется подписчику |

Пример:
```python
buttons = [
    [
        {"text": "Копировать", "actionType": 2, "value": "xxxx"},
        {"text": "Перейти", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Сообщить событие", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("сообщение с кнопками")
```
> **Примечание:**
> - Только при нажатии кнопки **сообщить событие** будет отправлено уведомление, **копирование** и **переход по URL** не могут получить уведомление.

### Цепочечные модификаторы (можно комбинировать)

Цепочечные модификаторы возвращают `self`, поддерживают цепочечное вызов, должны быть вызваны перед окончательным методом отправки:

- `.Reply(message_id: str)` — ответить на указанное сообщение.
- `.At(user_id: str)` — упомянуть указанного пользователя.
- `.AtAll()` — упомянуть всех.
- `.Buttons(buttons: List)` — добавить кнопки.

### Примеры цепочечного вызова

```python
# Базовая отправка
await yunhu.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("ответ на сообщение")

# Ответ + кнопки
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("сообщение с ответом и кнопками")
```

### Примеры управления группами

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Удаление участника группы
await yunhu.Send.To("group", group_id).Kick(user_id)

# Запрет пользователя (10 минут)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Разрешение запрета
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Пожизненный запрет
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Создание тега группы
await yunhu.Send.To("group", group_id).CreateTag("VIP пользователь", color="#FF5733", desc="VIP-участник")

# Изменение тега группы
await yunhu.Send.To("group", group_id).EditTag("VIP пользователь", new_tag="SVIP пользователь", color="#33C4FF")

# Удаление тега группы
await yunhu.Send.To("group", group_id).DeleteTag("VIP пользователь")

# Получение списка тегов группы
result = await yunhu.Send.To("group", group_id).GetTagList()

# Добавление тега пользователю
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP пользователь")

# Удаление тега у пользователя
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP пользователь")

# Ограничение типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Снятие ограничения типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Примеры получения истории сообщений

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Получение последних 10 сообщений в группе (всего возвращается 10 сообщений)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Получение 10 сообщений до указанного ID в группе (всего возвращается 11 сообщений)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Получение по 10 сообщений до и после указанного ID в группе (всего возвращается 21 сообщение)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Получение истории сообщений в диалоге с пользователем
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку OneBot12 форматированных сообщений, что обеспечивает кроссплатформенную совместимость:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "ответное сообщение"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Стандартные API действия (ApiDSL)

> [!NOTE]
> Эта функция доступна только при использовании ErisPulse **2.7.0+** и YunhuAdapter **4.3.0+**.

Помимо цепочечной отправки `Send`, адаптер предоставляет внутренний класс `Api`, который раскрывает стандартные API действия OneBot12 и расширения платформы Yunhu. Все методы возвращают стандартный формат ответа.

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Информационный запрос (через открытый Web API, без аутентификации)
result = await yunhu.Api.get_self_info()              # Информация о роботе
result = await yunhu.Api.get_user_info("7058262")     # Информация о любом пользователе
result = await yunhu.Api.get_group_info("635409929")  # Информация о группе

# Файловые операции
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# Отмена сообщения (требуется предоставить chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Многоконтактная работа: указание аккаунта робота
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Поддерживаемые стандартные действия

| Метод | Описание | Источник данных |
|------|------|---------|
| `get_self_info()` | Информация о роботе | Открытый Web API (bot-info) |
| `get_user_info(user_id)` | Информация о пользователе (любой пользователь может запросить) | Открытый Web API (user/homepage) |
| `get_group_info(group_id)` | Информация о группе | Открытый Web API (group-info) |
| `upload_file(*, type, name, ...)` | Загрузка файла (автоматически определяет image/video/file) | Open API робота |
| `get_file(file_id)` | Получение файла (file_id — это URL) | — |
| `delete_message(message_id, *, chat_id, chat_type)` | Отмена сообщения | Open API робота (/bot/recall) |

> **Примечание:** `get_self_info` / `get_user_info` / `get_group_info` реализованы через **неофициальный открытый Web API** (chat-web-go.jwzhd.com). Эти интерфейсы не требуют аутентификации, но не являются официальной документацией и могут изменяться с обновлением платформы; при сбое возвращается стандартный ответ об ошибке.

### Неподдерживаемые стандартные действия

Следующие стандартные действия не поддерживаются платформой Yunhu, при вызове возвращается `retcode=10002` (не поддерживаемое действие):
- `get_friend_list` (Open API робота "список пользователей робота" пока находится в стадии разработки)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Расширения платформы

Через `Api.call("yunhu.xxx", **params)` вызываются расширения платформы Yunhu (параметры используют стилистику OB12, адаптер автоматически переводит в поля Yunhu):

| Расширение | Описание | Эквивалент Send метода |
|---------|------|---------------|
| `yunhu.recall` | Отмена сообщения (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Удаление участника группы (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Запрет (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Разрешение запрета (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | CRUD-действия с тегами группы (group_id, ...) | `Send.To("group", g).CreateTag(...)` и т.д. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Добавление/удаление тега у пользователя | `Send.To("group", g).AddUserTag(...)` и т.д. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Синоним семантики титула участника** (тег ≈ титул, внутреннее отображение на tag.relate) | — |
| `yunhu.msg_type_limit` | Ограничение типов сообщений в группе (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Получение истории сообщений (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Открытый запрос информации о роботе (bot_id) | — |
| `yunhu.user_homepage` | Открытый запрос домашней страницы пользователя (user_id) | — |

```python
# Пример расширения платформы
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Теги и титулы:** Семантика "тегов" в Yunhu эквивалентна OneBot12 полю `title` участника группы. `yunhu.set_member_title` является синонимом `yunhu.tag.relate`, оба внутренне отображаются на один и тот же эндпоинт. Роль отправителя в событиях сообщений отображается из `senderUserLevel` в стандартное поле `role` (`owner/admin/member`). 

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно ожидать для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату ответа адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "self": {...},            // Информация о себе (включая bot_id)
    "message_id": "123456",   // ID сообщения
    "message": "",            // Сообщение об ошибке
    "yunhu_raw": {...}        // Исходные данные ответа
}
```

## Уникальные типы событий

Требуется проверка platform=="yunhu" для использования функций этой платформы

### Основные отличия

1. Уникальные типы событий:
    - Формы (например, команды формы): yunhu_form
    - Эмодзи/стикеры: yunhu_expression
    - Нажатие кнопки: yunhu_button_click
    - Нажатие кнопки A2UI: yunhu_a2ui_button
    - Настройки робота: yunhu_bot_setting
    - Быстрое меню: yunhu_shortcut_menu
2. Расширение стандартных полей (4.3.0+):
    - В событиях сообщений добавлено стандартное поле `role` (отображается из Yunhu `senderUserLevel` в `owner`/`admin`/`member`)
    - Добавлено поле `user_avatar` (URL аватара отправителя)
3. Расширенные поля:
    - Все уникальные поля имеют префикс `yunhu_`
    - Оригинальные данные сохраняются в поле `yunhu_raw`
    - В личных сообщениях `self.user_id` обозначает ID робота

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
    "action_name": "имя действия",
    "source_component_id": "ID исходного компонента",
    "form_context": {},
    "interaction_json": "строка JSON с данными взаимодействия"
  }
}

### Пример обработки события нажатия кнопки

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Обработка уведомления Yunhu

    Используется общий декоратор on_notice() для обработки всех уведомлений,
    затем через detail_type различаются типы уведомлений
    event.reply() автоматически отвечает через платформу Yunhu
    """
    # Проверка, является ли событие нажатия кнопки
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"Пользователь {user_nickname}({user_id}) нажал кнопку: {button_value}")

        # Использование event.reply() для автоматической отправки ответа (в зависимости от платформы)
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

    # Обработка изменения настроек робота
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"Настройки обновлены: {settings}")

    # Обработка события кнопки A2UI
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI действие: {action_name}, данные формы: {form_context}")
```

### Использование цепочечного вызова для отправки сообщений с кнопками

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "Подтвердить", "actionType": 3, "value": "confirm"},
        {"text": "Отменить", "actionType": 3, "value": "cancel"},
        {"text": "Просмотреть", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# Отправка сообщения с кнопками в группу
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Пожалуйста, подтвердите следующую операцию")

# Отправка сообщения с кнопками в личный чат
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Выберите настройки")
```

### Отправка A2UI сообщений

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# Отправка A2UI сообщения
await yunhu.Send.To("user", user_id).A2UI("Содержимое интерактивной карточки A2UI")
```

# Настройки робота
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "ID группы (может быть пустым)",
  "user_nickname": "Никнейм пользователя",
  "yunhu_setting": {
    "ID_параметра": {
      "id": "ID параметра",
      "type": "input/radio/checkbox/select/switch",
      "value": "значение параметра"
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
    "type": "тип меню (целое число)",
    "action": "действие меню (целое число)"
  }
}
```

## Расширения Event Mixin

Адаптер регистрирует следующие специфичные методы платформы, доступные только при `platform == "yunhu"`:

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_raw_event()` | `dict` | Получение исходных данных события Yunhu (в `yunhu_raw`) |
| `get_sender_level()` | `str` | Уровень отправителя в Yunhu (owner/administrator/member/unknown) |
| `get_sender_role()` | `str` | Роль отправителя в OneBot12 стандарте (owner/admin/member) |
| `get_sender_title()` | `str` | Титул отправителя (доступ к стандартному полю title, зарезервирован) |
| `get_sender_avatar()` | `str` | URL аватара отправителя |
| `get_command()` | `dict` | Данные команды (только для событий команд, `yunhu_command`) |
| `get_button_value()` | `str` | Значение кнопки в событии нажатия кнопки (в `yunhu_button.value`) |
| `get_a2ui_action()` | `str` | Действие A2UI в событии нажатия кнопки A2UI |
| `get_a2ui_form_context()` | `dict` | Контекст формы A2UI в событии нажатия кнопки A2UI |
| `get_menu_id()` | `str` | ID события быстрого меню (в `yunhu_menu.id`) |
| `get_setting()` | `dict` | Данные настроек в событии изменения настроек робота (в `yunhu_setting`) |
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

- Все уникальные поля имеют префикс `yunhu_`, чтобы избежать конфликтов с стандартными полями
- Оригинальные данные сохраняются в поле `yunhu_raw`, для доступа к полной исходной информации платформы Yunhu
- `self.user_id` обозначает ID робота (получается из bot_id в конфигурации)
- Команды формы предоставляются через поле `yunhu_command` структурированной информации
- События нажатия кнопки предоставляются через поле `yunhu_button` информацию о кнопке
- События нажатия кнопки A2UI предоставляются через поле `yunhu_a2ui` информацию об A2UI взаимодействии
- Изменения настроек робота предоставляются через поле `yunhu_setting` данные настроек
- Операции быстрого меню предоставляются через поле `yunhu_menu` информацию о меню
- Эмодзи/стикеры предоставляются через поле сообщения `yunhu_expression` данные стикера (sticker_id, ID пакета стикеров, размеры изображения и т.д.)

### Поле сообщения эмодзи/стикера (yunhu_expression)

При отправке пользователем эмодзи или стикера тип сообщения — `yunhu_expression`:

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

## Конфигурация нескольких роботов

### Описание конфигурации

Адаптер Yunhu поддерживает одновременную конфигурацию и запуск нескольких аккаунтов роботов Yunhu.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # API token робота (обязательно)
mode = "ws"  # Режим получения (опционально, по умолчанию "ws", доступные значения: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Путь для webhook (опционально, по умолчанию "/webhook")
enabled = true  # Включен ли аккаунт (опционально, по умолчанию true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # API token второго робота
webhook_path = "/webhook/bot2"  # Отдельный путь для webhook
enabled = true
```

**Описание конфигурационных параметров:**
- `token` — API token, предоставленный платформой Yunhu (обязательно)
- `mode` — режим получения (опционально, по умолчанию `"ws"`, доступные значения `"ws"`, `"webhook"`)
- `webhook_path` — HTTP путь для получения событий Yunhu (опционально, по умолчанию "/webhook", используется только в режиме webhook)
- `enabled` — включен ли аккаунт (опционально, по умолчанию true)

**Важные замечания:**
1. ID робота платформы Yunhu автоматически определяется во время запуска, не нужно указывать в конфигурации
2. В режиме webhook каждый робот должен иметь отдельный `webhook_path`, чтобы получать свои собственные события webhook
3. При настройке webhook на платформе Yunhu необходимо указать соответствующий URL для каждого робота, например:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Использование Send DSL для указания робота

Можно использовать метод `Using()` для указания робота, через которого отправлять сообщение. Этот метод поддерживает два параметра:
- **Имя аккаунта** — имя робота в конфигурации (например, `bot1`, `bot2`)
- **bot_id** — значение `bot_id` в конфигурации

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Использование имени аккаунта для отправки сообщения
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# Использование bot_id для отправки сообщения (автоматически сопоставляется с соответствующим аккаунтом)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# Без указания — используется первый включенный робот
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Примечание:** При использовании `bot_id` система автоматически находит соответствующий аккаунт в конфигурации. Это особенно полезно при обработке событий, где можно использовать `event["self"]["user_id"]` для ответа того же робота.

### ID робота в событиях

Полученные события автоматически содержат информацию о соответствующем `bot_id`:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Получить ID робота, вызвавшего событие
        bot_id = event["self"]["user_id"]
        print(f"Сообщение от робота: {bot_id}")
        
        # Отправить сообщение с использованием того же робота
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответное сообщение")
```

### Логирование

Адаптер автоматически включает `bot_id` в логи, что упрощает отладку и отслеживание:

```
[INFO] [yunhu] [bot:30535459] Получено сообщение от пользователя user123
[INFO] [yunhu] [bot:12345678] Сообщение успешно отправлено, message_id: abc123
```

### Управление

```python
# Получить информацию обо всех аккаунтах
bots = yunhu.bots

# Проверить статус аккаунта
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# Динамически включить/отключить аккаунт (требуется перезапуск адаптера)
yunhu.bots["bot1"].enabled = False
```

### Совместимость со старой конфигурацией

Старая конфигурация `[Yunhu_Adapter.bots.*]` (с полем `bot_id`) автоматически мигрируется в формат `accounts` (поле `bot_id` теперь определяется во время запуска, значение в конфигурации игнорируется); рекомендуется как можно скорее перейти на новый формат.