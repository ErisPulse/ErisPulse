# Документация по функциям платформы Yunhu

YunhuAdapter — это адаптер, построенный на основе протокола Yunhu, объединяющий все функциональные модули Yunhu и предоставляющий единый интерфейс обработки событий и операций сообщений.

---

Пожалуйста, верните непосредственно переведённый полный Markdown-контент, не добавляя никаких других текстов.


## Информация о документации

- Соответствующая версия модуля: 4.3.0
- Ответственный: ErisPulse

Пожалуйста, верните полностью переведённый Markdown-документ, не добавляя никаких других текстов.

## Основная информация

- **Описание платформы:** Yunhu (云湖) - корпоративная платформа мгновенных сообщений
- **Название адаптера:** YunhuAdapter
- **Поддержка нескольких аккаунтов:** Поддерживает идентификацию и настройку нескольких аккаунтов роботов Yunhu с помощью bot_id
- **Поддержка цепочки модификаторов:** Поддерживает методы цепочек модификаторов, такие как `.Reply()`
- **Совместимость с OneBot12:** Поддерживает отправку сообщений в формате OneBot12

docs/ru/quick-start.md

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепного синтаксиса, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Привет, мир!")
```

Поддерживаемые типы отправки сообщений включают:
- `.Text(text: str)` — отправка обычного текстового сообщения.
- `.Html(html: str)` — отправка сообщения в формате HTML.
- `.Markdown(markdown: str)` — отправка сообщения в формате Markdown.
- `.A2UI(text: str)` — отправка сообщения в формате A2UI.
- `.Image(file: bytes, stream: bool = False, filename: str = None)` — отправка сообщения с изображением, поддержка потоковой загрузки и пользовательского имени файла.
- `.Video(file: bytes, stream: bool = False, filename: str = None)` — отправка сообщения с видео, поддержка потоковой загрузки и пользовательского имени файла.
- `.File(file: bytes, stream: bool = False, filename: str = None)` — отправка сообщения с файлом, поддержка потоковой загрузки и пользовательского имени файла.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)` — массовая отправка сообщений.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)` — редактирование уже отправленного сообщения.
- `.Recall(msg_id: str)` — отмена отправки сообщения.
- `.Board(content: str, content_type: str = "text")` — публикация объявления на доске. Область действия определяется методом `To()` (указание цели = локальная доска, без указания = глобальная доска). Цепное изменение: `.Expire(duration)` — относительное время истечения (секунды), `.ExpireAt(timestamp)` — абсолютное время истечения (секундный таймстамп), `.ForMember(member_id)` — доска для участника группы; **при пустом содержании автоматически отменяется публикация доски**. По-прежнему поддерживается старый способ явного указания области `Board("local", "объявление")`.
- `.DismissBoard()` — отмена публикации объявления на доске. Область действия также определяется методом `To()`, поддерживается `.ForMember(member_id)`; по-прежнему поддерживается старый способ `DismissBoard("local")`.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)` — отправка потокового сообщения.

### Методы управления группами

Все методы управления группами требуют указания группы через цепной синтаксис, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)` — удаление участника из группы. Робот должен иметь права `разрешить удаление участников группы`.
- `.Ban(user_id: str, duration: int = 600)` — запрет на отправку сообщений пользователю. `duration` — длительность запрета (в секундах), 0 — снятие запрета, -1 — пожизненный запрет. Робот должен иметь права `разрешить запрет пользователей`.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)` — создание тега для группы. `color` имеет формат #RRGGBB, `sort` — чем меньше, тем выше в списке. Робот должен иметь права `разрешить управление тегами`.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)` — изменение тега группы. Параметры не обязательны, если не переданы, изменение не производится. Робот должен иметь права `разрешить управление тегами`.
- `.DeleteTag(tag: str)` — удаление тега группы. Робот должен иметь права `разрешить управление тегами`.
- `.GetTagList()` — получение списка тегов группы. Возвращает данные с массивом `list`.
- `.AddUserTag(user_id: str, tag: str)` — добавление тега пользователю. Робот должен иметь права `разрешить управление тегами`.
- `.RemoveUserTag(user_id: str, tag: str)` — удаление тега у пользователя. Робот должен иметь права `разрешить управление тегами`.
- `.SetMsgTypeLimit(types: str)` — ограничение типов сообщений в группе. `types` — список типов сообщений, разделённых запятой (например, `"text,image,video"`), пустая строка означает отсутствие ограничений. Робот должен иметь права `разрешить изменение информации о группе`.

### Методы запроса сообщений

Для получения списка исторических сообщений в указанном диалоге (пользователь/группа) необходимо указать цель через цепной синтаксис, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)` — получение истории сообщений в диалоге. Возвращает данные с массивом `list` и общим числом `total`.
  - `message_id` — идентификатор сообщения (необязательно). Если не указан, в сочетании с `before` возвращает последние N сообщений.
  - `before` — возвращает N сообщений до указанного идентификатора.
  - `after` — возвращает N сообщений после указанного идентификатора.
  - > **Примечание:** `before` и `after` должны быть заданы хотя бы один и быть больше 0, иначе сервер не вернёт никаких сообщений.

Область действия доски определяется автоматически методом `To()`:
- Указание `To(target_type, target_id)` → локальная доска (указана цель — пользователь/группа)
- Без указания `To()` → глобальная доска

```python
# Локальная доска (относительное истечение через 60 секунд)
await yunhu.Send.To("group", group_id).Expire(60).Board("объявление", content_type="markdown")

# Доска для участника группы (видна только указанному пользователю)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("видно только вам")

# Абсолютное время истечения
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("объявление с указанным временем")

# Глобальная доска
await yunhu.Send.Board("глобальное объявление")

# Очистка локальной доски (пустое содержимое → автоматическая отмена публикации)
await yunhu.Send.To("group", group_id).Board("")
```

### Описание параметров кнопок

Параметр `buttons` представляет собой вложенный список, определяющий расположение и функциональность кнопок. Каждый объект кнопки содержит следующие поля:

| Поле         | Тип   | Обязательно | Описание                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Да       | Текст на кнопке                                                         |
| `actionType` | int    | Да       | Тип действия:<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отправка события |
| `url`        | string | Нет       | Используется при `actionType=1`, определяет целевой URL для перехода                         |
| `value`      | string | Нет       | При `actionType=2` значение копируется в буфер обмена<br>При `actionType=3` значение отправляется подписчику |

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
> - Только при нажатии кнопки типа **Сообщить событие** будет отправлено уведомление, кнопки **Копировать** и **Перейти** не отправляют уведомления.

### Цепные методы изменения (можно комбинировать)

Цепные методы изменения возвращают `self`, поддерживают цепное вызов, должны вызываться перед окончательным методом отправки:

- `.Reply(message_id: str)` — ответ на указанное сообщение.
- `.At(user_id: str)` — упоминание указанного пользователя.
- `.AtAll()` — упоминание всех участников.
- `.Buttons(buttons: List)` — добавление кнопок.

### Примеры цепного вызова

```python
# Базовая отправка
await yunhu.Send.To("user", user_id).Text("Привет")

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

# Запрет на отправку сообщений пользователю (10 минут)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Снятие запрета
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Пожизненный запрет
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Создание тега группы
await yunhu.Send.To("group", group_id).CreateTag("VIP-пользователь", color="#FF5733", desc="VIP-участник")

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

# Установка ограничения типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Снятие ограничения типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Примеры запроса сообщений

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Получение последних 10 сообщений в группе (всего 10 сообщений)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Получение 10 сообщений до указанного идентификатора в группе (всего 11 сообщений)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Получение по 10 сообщений до и после указанного идентификатора в группе (всего 21 сообщение)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Получение истории сообщений в диалоге с пользователем
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость сообщений между платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Привет"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепными методами изменения
ob12_msg = [{"type": "text", "data": {"text": "ответное сообщение"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)

## Стандартные действия API (ApiDSL)

> [!NOTE]
> Эта функция требует ErisPulse **2.7.0+** и YunhuAdapter **4.3.0+**.

Помимо цепочки отправки `Send`, адаптер также предоставляет внутренний класс `Api`, который предоставляет стандартные действия API OneBot12 и расширения платформы Yunhu. Все методы возвращают стандартный формат ответа.

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Информационный запрос (через открытый Web API, без аутентификации)
result = await yunhu.Api.get_self_info()              # Информация о боте
result = await yunhu.Api.get_user_info("7058262")     # Информация о любом пользователе
result = await yunhu.Api.get_group_info("635409929")  # Информация о группе

# Операции с файлами
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# Отмена сообщения (требуется дополнительное указание chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Множественные аккаунты: указание учетной записи бота
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Поддерживаемые стандартные действия

| Метод | Описание | Источник данных |
|------|------|---------|
| `get_self_info()` | Информация о боте | Открытый Web API (bot-info) |
| `get_user_info(user_id)` | Информация о пользователе (любой пользователь может запросить) | Открытый Web API (user/homepage) |
| `get_group_info(group_id)` | Информация о группе | Открытый Web API (group-info) |
| `upload_file(*, type, name, ...)` | Загрузка файла (автоматически определяет image/video/file) | Открытый API бота |
| `get_file(file_id)` | Получение файла (file_id - это URL) | — |
| `delete_message(message_id, *, chat_id, chat_type)` | Отмена сообщения | Открытый API бота (/bot/recall) |

> **Внимание**: `get_self_info` / `get_user_info` / `get_group_info` реализуются через **неофициальные открытые Web API** (chat-web-go.jwzhd.com). Эти интерфейсы не требуют аутентификации, но не документированы официально и могут меняться с обновлением платформы; при сбое возвращается стандартный ответ об ошибке.

### Неподдерживаемые стандартные действия

Следующие стандартные действия не имеют соответствующих API в Yunhu, при вызове возвращается `retcode=10002` (операция не поддерживается):
- `get_friend_list` (Список пользователей бота в открытом API бота еще не доступен)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Расширения платформы

Расширенные действия Yunhu вызываются через `Api.call("yunhu.xxx", **params)` (параметры именуются в стиле OB12, адаптер автоматически переводит их в поля Yunhu):

| Расширенное действие | Описание | Эквивалентный метод Send |
|---------|------|---------------|
| `yunhu.recall` | Отмена сообщения (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Исключение участника группы (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Запрет на сообщения (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Снятие запрета (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | CRUD-операции с тегами группы (group_id, ...) | `Send.To("group", g).CreateTag(...)` и т.д. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Добавление/удаление тега пользователю | `Send.To("group", g).AddUserTag(...)` и т.д. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Синоним семантики титула участника** (тег ≈ титул, внутреннее отображение на tag.relate) | — |
| `yunhu.msg_type_limit` | Ограничение типа сообщений в группе (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Получение истории сообщений (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Открытый запрос bot-info (bot_id) | — |
| `yunhu.user_homepage` | Открытый запрос домашней страницы пользователя (user_id) | — |

```python
# Примеры расширений платформы
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Теги и титулы**: Семантика "тегов" в Yunhu эквивалентна OneBot12 `title` участника группы. `yunhu.set_member_title` является синонимом семантики `yunhu.tag.relate`, оба внутренне отображаются на один и тот же конечный узел. Роль отправителя в событии сообщения группы отображается в стандартное поле `role` (owner/admin/member) через `senderUserLevel`.

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно напрямую ожидать, чтобы получить результат отправки. Возвращаемый результат соответствует стандартизированной спецификации возврата адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Ответные данные
    "self": {...},            // Информация о себе (содержит bot_id)
    "message_id": "123456",   // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "yunhu_raw": {...}        // Исходные ответные данные
}
```

docs/ru/quick-start.md

## Типы специфических событий

Необходимо проверить platform=="yunhu", чтобы использовать особенности данной платформы

### Основные отличия

1. Специфические типы событий:
    - Формы (например, команды формы): yunhu_form
    - Эмодзи/стикеры: yunhu_expression
    - Нажатие кнопки: yunhu_button_click
    - Кнопка A2UI: yunhu_a2ui_button
    - Настройка бота: yunhu_bot_setting
    - Быстрое меню: yunhu_shortcut_menu
2. Расширение стандартных полей (4.3.0+):
    - В событиях сообщений добавлено стандартное поле `role` (отображается из senderUserLevel в `owner`/`admin`/`member`)
    - Добавлено поле `user_avatar` (URL аватара отправителя)
3. Расширение полей:
    - Все специфические поля идентифицируются с префиксом yunhu_
    - Исходные данные сохраняются в поле yunhu_raw
    - В личных сообщениях self.user_id обозначает ID бота

### Примеры специальных полей

```python
# Команда формы
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "Название команды формы",
    "id": "ID команды",
    "form": {
      "ID_поля1": {
        "id": "ID_поля1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "Метка поля",
        "value": "Значение поля"
      }
    }
  }
}

# Событие нажатия кнопки
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "ID пользователя, нажавшего кнопку",
  "user_nickname": "Никнейм пользователя",
  "message_id": "ID сообщения",
  "yunhu_button": {
    "id": "ID кнопки (может быть пустым)",
    "value": "Значение кнопки"
  }
}

# Событие кнопки A2UI
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "ID пользователя, выполнившего действие",
  "user_nickname": "Никнейм пользователя",
  "message_id": "ID сообщения",
  "yunhu_a2ui": {
    "recv_id": "ID получателя",
    "recv_type": "Тип получателя",
    "action_name": "Название действия",
    "source_component_id": "ID исходного компонента",
    "form_context": {},
    "interaction_json": "JSON строка с данными взаимодействия"
  }
}

### Пример обработки события нажатия кнопки

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Обработка уведомления платформы Yunhu

    Использование универсального декоратора on_notice() для обработки всех уведомлений,
    а затем различение типов уведомлений по detail_type
    event.reply() автоматически отправляет ответ через платформу Yunhu
    """

# Проверка, является ли событие нажатием кнопки
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"Пользователь {user_nickname}({user_id}) нажал на кнопку: {button_value}")

# Автоматическая отправка ответа с использованием event.reply() (в зависимости от платформы будет выбран правильный способ отправки)
        if button_value == "confirm":
            await event.reply("Вы нажали кнопку подтверждения!")
        elif button_value == "cancel":
            await event.reply("Операция отменена")
        else:
            await event.reply(f"Получен ваш выбор: {button_value}")

# Обработка событий контекстного меню
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"Сработало контекстное меню: {menu_id}")

docs/ru/quick-start.md

# Обработка изменений настроек бота
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"Настройки обновлены: {settings}")

Пожалуйста, напрямую верните переведенный полный Markdown-контент, не включая никакого другого текста.


# Обработка событий кнопок A2UI

```python
elif event.get("detail_type") == "yunhu_a2ui_button":
    a2ui = event.get("yunhu_a2ui", {})
    action_name = a2ui.get("action_name", "")
    form_context = a2ui.get("form_context", {})
    await event.reply(f"Действие A2UI: {action_name}, данные формы: {form_context}")
```

### Отправка сообщения с кнопками с использованием цепочки вызовов

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "Подтвердить", "actionType": 3, "value": "confirm"},
        {"text": "Отменить", "actionType": 3, "value": "cancel"},
        {"text": "Просмотреть подробнее", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# Отправка сообщений с кнопками в группу  
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Пожалуйста, подтвердите следующее действие")

# Отправка сообщений с кнопками в личные сообщения пользователя  
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Пожалуйста, выберите свои предпочтительные настройки")  

### Отправка A2UI сообщений  

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# Отправка сообщений A2UI
await yunhu.Send.To("user", user_id).A2UI("Содержимое интерактивной карточки A2UI")

```
# Настройки бота
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "ID группы (может быть пустым)",
  "user_nickname": "Никнейм пользователя",
  "yunhu_setting": {
    "ID настройки": {
      "id": "ID настройки",
      "type": "input/radio/checkbox/select/switch",
      "value": "Значение настройки"
    }
  }
}

# Быстрое меню
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "ID пользователя, вызвавшего меню",
  "user_nickname": "Никнейм пользователя",
  "group_id": "ID группы (если это групповой чат)",
  "yunhu_menu": {
    "id": "ID меню",
    "type": "Тип меню (целое число)",
    "action": "Действие меню (целое число)"
  }
}

## Миксин событий: расширенные методы

Адаптер регистрирует следующие методы, специфичные для платформы, доступные только при `platform == "yunhu"`:

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_raw_event()` | `dict` | Получить исходные данные события Yunhu (`yunhu_raw`) |
| `get_sender_level()` | `str` | Уровень отправителя Yunhu (owner/administrator/member/unknown) |
| `get_sender_role()` | `str` | Роль отправителя по стандарту OneBot12 (owner/admin/member) |
| `get_sender_title()` | `str` | Звание отправителя (резервный доступ к стандартному полю `title`) |
| `get_sender_avatar()` | `str` | URL аватара отправителя |
| `get_command()` | `dict` | Данные команды (только для событий сообщений команд, `yunhu_command`) |
| `get_button_value()` | `str` | Значение `value` события нажатия кнопки (`yunhu_button.value`) |
| `get_a2ui_action()` | `str` | Название действия `actionName` события кнопки A2UI |
| `get_a2ui_form_context()` | `dict` | Контекст формы события кнопки A2UI |
| `get_menu_id()` | `str` | Идентификатор события быстрого меню (`yunhu_menu.id`) |
| `get_setting()` | `dict` | Данные настроек события настройки бота (`yunhu_setting`) |
| `is_command_message()` | `bool` | Является ли событие сообщением команды |
| `is_button_click()` | `bool` | Является ли событие нажатием кнопки |
| `is_a2ui_button()` | `bool` | Является ли событие кнопкой A2UI |

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    if event.get("platform") != "yunhu":
        return

    if event.is_button_click():
        value = event.get_button_value()
        await event.reply(f"Вы нажали на кнопку: {value}")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()
```

[**English**](docs/ru/quick-start.md)

## Описание расширенных полей

- Все специфические поля идентифицируются с префиксом `yunhu_`, чтобы избежать конфликта с стандартными полями
- Сохранение исходных данных в поле `yunhu_raw`, для удобного доступа к полным исходным данным платформы Yunhu
- `self.user_id` обозначает идентификатор бота (получается из bot_id в конфигурации)
- Команды формы предоставляются в виде структурированных данных через поле `yunhu_command`
- Информация о событиях нажатия кнопки предоставляется через поле `yunhu_button`
- Информация о событиях A2UI предоставляется через поле `yunhu_a2ui`
- Изменения настроек бота предоставляются через поле `yunhu_setting`
- Операции с быстрым меню предоставляются через поле `yunhu_menu`
- Сообщения с эмодзи/стикерами предоставляются через сегмент сообщений `yunhu_expression`, содержащий данные стикера (sticker_id, идентификатор пака стикеров, размер изображения и т.д.)

### Сегмент сообщений с эмодзи/стикерами (yunhu_expression)

Когда пользователь отправляет эмодзи или стикер, тип сегмента сообщений равен `yunhu_expression`:

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
| `sticker_pack_id` | string | Идентификатор пака стикеров |
| `expression_id` | string | Идентификатор эмодзи |
| `image_name` | string | Путь к файлу изображения эмодзи |
| `width` | int | Ширина изображения (необязательно) |
| `height` | int | Высота изображения (необязательно) |

Пример использования:
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"Получен стикер: sticker_id={data['sticker_id']}, ID пака={data['sticker_pack_id']}")

## Многоботная конфигурация

### Описание конфигурации

Адаптер Yunhu поддерживает одновременную конфигурацию и запуск нескольких аккаунтов ботов Yunhu.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # Токен бота (обязательно)
mode = "ws"  # Режим получения (необязательно, по умолчанию "ws", возможные значения: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Путь вебхука (необязательно, по умолчанию "/webhook")
enabled = true  # Включено ли (необязательно, по умолчанию true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # Токен второго бота
webhook_path = "/webhook/bot2"  # Отдельный путь вебхука
enabled = true
```

**Описание параметров:**
- `token`: API токен, предоставленный платформой Yunhu (обязательно)
- `mode`: Режим получения (необязательно, по умолчанию `"ws"`, возможные значения `"ws"`, `"webhook"`)
- `webhook_path`: HTTP путь для получения событий Yunhu (необязательно, по умолчанию "/webhook", используется только в режиме webhook)
- `enabled`: Включен ли этот аккаунт (необязательно, по умолчанию true)

**Важное замечание:**
1. ID бота на платформе Yunhu автоматически определяется **во время выполнения**, не нужно указывать его в конфигурации
2. В режиме webhook каждый бот должен иметь отдельный `webhook_path`, чтобы получать свои собственные события вебхука
3. При настройке вебхука на платформе Yunhu, для каждого бота нужно указать соответствующий URL, например:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Использование Send DSL для указания бота

Можно указать, какой бот должен отправить сообщение, используя метод `Using()`. Этот метод поддерживает два параметра:
- **Имя аккаунта**: Имя бота из конфигурации (например, `bot1`, `bot2`)
- **bot_id**: Значение `bot_id` из конфигурации

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Отправка сообщения с использованием имени аккаунта
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# Отправка сообщения с использованием bot_id (система автоматически найдёт соответствующий аккаунт)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# Если не указано, используется первый включённый бот
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Примечание:** При использовании `bot_id` система автоматически находит соответствующий аккаунт в конфигурации. Это особенно полезно при обработке ответов на события, где можно напрямую использовать `event["self"]["user_id"]` для ответа с того же аккаунта.

### Идентификация бота в событиях

Полученные события автоматически содержат информацию о соответствующем `bot_id`:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Получение ID бота, вызвавшего событие
        bot_id = event["self"]["user_id"]
        print(f"Сообщение от бота: {bot_id}")
        
        # Отправка ответа с использованием того же бота
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответ на сообщение")
```

### Информация в логах

Адаптер автоматически включает информацию о `bot_id` в логи, что облегчает отладку и отслеживание:

```
[INFO] [yunhu] [bot:30535459] Получено личное сообщение от пользователя user123
[INFO] [yunhu] [bot:12345678] Сообщение успешно отправлено, message_id: abc123
```

### Управление через интерфейс

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

Старые конфигурации `[Yunhu_Adapter.bots.*]` (с полем `bot_id`) автоматически мигрируются в формат `accounts` (значение `bot_id` теперь определяется автоматически во время выполнения, и значение в конфигурации игнорируется); рекомендуется как можно скорее перейти на новый формат.