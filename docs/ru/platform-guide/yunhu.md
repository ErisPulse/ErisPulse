# Документация по функциям платформы Yunhu

YunhuAdapter — это адаптер, построенный на протоколе Yunhu, объединяющий все функциональные модули Yunhu и предоставляющий единый интерфейс обработки событий и операций сообщений.

---

## Информация о документации

- Версия соответствующего модуля: 4.3.0
- Ответственный: ErisPulse

## Основная информация

- Краткое описание платформы: Yunhu — корпоративная платформа мгновенной коммуникации
- Название адаптера: YunhuAdapter
- Поддержка нескольких аккаунтов: поддержка идентификации и настройки нескольких аккаунтов роботов Yunhu через bot_id
- Поддержка цепочечных модификаторов: поддержка цепочечных методов модификации, таких как `.Reply()`
- Совместимость с OneBot12: поддержка отправки сообщений в формате OneBot12

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка текстового сообщения.
- `.Html(html: str)` — отправка сообщения в формате HTML.
- `.Markdown(markdown: str)` — отправка сообщения в формате Markdown.
- `.A2UI(text: str)` — отправка сообщения в формате A2UI.
- `.Image(file: bytes, stream: bool = False, filename: str = None)` — отправка изображения, поддержка потоковой загрузки и пользовательского имени файла.
- `.Video(file: bytes, stream: bool = False, filename: str = None)` — отправка видео, поддержка потоковой загрузки и пользовательского имени файла.
- `.File(file: bytes, stream: bool = False, filename: str = None)` — отправка файла, поддержка потоковой загрузки и пользовательского имени файла.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)` — массовая отправка сообщений.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)` — редактирование существующего сообщения.
- `.Recall(msg_id: str)` — отмена отправки сообщения.
- `.Board(content: str, content_type: str = "text")` — публикация на доске объявлений. Область действия определяется методом `To()` (указанный цель — локальная доска, не указано — глобальная доска). Цепочечные модификаторы: `.Expire(duration)` относительный срок действия (в секундах), `.ExpireAt(timestamp)` абсолютный срок действия (в секундах), `.ForMember(member_id)` доска для участника группы; **если содержимое пустое, автоматически превращается в отмену доски**. По-прежнему поддерживается старый стиль `Board("local", "Объявление")`.
- `.DismissBoard()` — отмена доски объявлений. Область действия определяется методом `To()`, поддержка `.ForMember(member_id)`; по-прежнему поддерживается старый стиль `DismissBoard("local")`.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)` — отправка потокового сообщения.

### Методы управления группами

Все методы управления группами необходимо использовать с цепочечным синтаксисом, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)` — исключение участника группы. Робот должен иметь права на исключение участников группы.
- `.Ban(user_id: str, duration: int = 600)` — запрет на отправку сообщений пользователю. `duration` — длительность запрета (в секундах), 0 означает разрешение, -1 — пожизненный запрет. Робот должен иметь права на запрет пользователей.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)` — создание тега группы. `color` имеет формат #RRGGBB, `sort` — чем меньше, тем выше в списке. Робот должен иметь права на управление тегами группы.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)` — изменение тега группы. Параметры не обязательны, если не указаны, не изменяются. Робот должен иметь права на управление тегами группы.
- `.DeleteTag(tag: str)` — удаление тега группы. Робот должен иметь права на управление тегами группы.
- `.GetTagList()` — получение списка тегов группы. Возвращает данные с массивом `list`.
- `.AddUserTag(user_id: str, tag: str)` — добавление тега пользователю. Робот должен иметь права на управление тегами группы.
- `.RemoveUserTag(user_id: str, tag: str)` — удаление тега у пользователя. Робот должен иметь права на управление тегами группы.
- `.SetMsgTypeLimit(types: str)` — ограничение типов сообщений в группе. `types` — имена типов сообщений, разделенные запятыми (например, `"text,image,video"`), пустая строка означает отсутствие ограничений. Робот должен иметь права на изменение информации о группе.

### Методы получения сообщений

Получение списка истории сообщений в конкретном диалоге (пользователь/группа) необходимо использовать цепочечный синтаксис, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)` — получение истории сообщений в диалоге. Возвращает данные с массивом `list` и общим количеством `total`.
  - `message_id` — идентификатор сообщения (необязательно). Если не указан, в сочетании с `before` возвращает последние N сообщений.
  - `before` — возвращает N сообщений до указанного идентификатора.
  - `after` — возвращает N сообщений после указанного идентификатора.
  - > **Внимание:** `before` и `after` должны быть указаны хотя бы один и больше нуля, иначе сервер не вернет никаких сообщений.

Область действия доски объявлений определяется методом `To()`:
- Указание `To(target_type, target_id)` → локальная доска (указанная группа/пользователь)
- Не указано `To()` → глобальная доска

```python
# Локальная доска (относительный срок действия 60 секунд)
await yunhu.Send.To("group", group_id).Expire(60).Board("Объявление", content_type="markdown")

# Доска для участника группы (видна только указанному участнику)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("Только ты видишь")

# Абсолютный срок действия по метке времени
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("Объявление по указанному времени")

# Глобальная доска
await yunhu.Send.Board("Глобальное объявление")

# Очистка локальной доски (пустое содержимое → автоматическая отмена)
await yunhu.Send.To("group", group_id).Board("")
```

### Пояснение параметров кнопок

Параметр `buttons` представляет собой вложенный список, описывающий макет и функциональность кнопок. Каждый объект кнопки содержит следующие поля:

| Поле         | Тип   | Обязательно | Описание                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Yes       | Текст на кнопке                                                         |
| `actionType` | int    | Yes       | Тип действия：<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отправка события |
| `url`        | string | No       | Используется, когда `actionType=1`, указывает целевой URL для перехода                         |
| `value`      | string | No       | Когда `actionType=2`, значение копируется в буфер обмена<br>Когда `actionType=3`, значение отправляется подписчику |

Пример:
```python
buttons = [
    [
        {"text": "Копировать", "actionType": 2, "value": "xxxx"},
        {"text": "Перейти", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Сообщить событие", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("Сообщение с кнопками")
```
> **Внимание:**
> - Только при нажатии кнопки **сообщить событие** будет отправлено уведомление, **копирование** и **переход по URL** не могут получить уведомления.

### Цепочечные модификаторы (можно комбинировать)

Цепочечные модификаторы возвращают `self`, поддерживают цепочечное использование и должны вызываться до окончательного метода отправки:

- `.Reply(message_id: str)` — ответить на указанное сообщение.
- `.At(user_id: str)` — упомянуть указанного пользователя.
- `.AtAll()` — упомянуть всех.
- `.Buttons(buttons: List)` — добавить кнопки.

### Примеры цепочечного вызова

```python
# Базовая отправка
await yunhu.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("Ответ на сообщение")

# Ответ + кнопки
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Сообщение с ответом и кнопками")
```

### Примеры управления группами

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Исключение участника группы
await yunhu.Send.To("group", group_id).Kick(user_id)

# Запрет на отправку сообщений пользователю (10 минут)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Разрешение запрета
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

# Ограничение типов сообщений в группе
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Отмена ограничения типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Примеры получения сообщений

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Получение последних 10 сообщений в группе (всего возвращается 10 сообщений)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Получение 10 сообщений до указанного идентификатора (всего возвращается 11 сообщений)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Получение по 10 сообщений до и после указанного идентификатора (всего возвращается 21 сообщение)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Получение истории сообщений в диалоге с пользователем
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку сообщений в формате OneBot12, что обеспечивает совместимость между платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответ на сообщение"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Стандартные API действия (ApiDSL)

> [!NOTE]
> Эта функция требует ErisPulse **2.7.0+** и YunhuAdapter **4.3.0+**.

Помимо `Send` цепочечной отправки, адаптер предоставляет внутренний класс `Api`, который раскрывает стандартные действия OneBot12 и расширенные действия платформы Yunhu. Все методы возвращают стандартный формат ответа.

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Информация (через публичный Web API, без аутентификации)
result = await yunhu.Api.get_self_info()              # Информация о роботе
result = await yunhu.Api.get_user_info("7058262")     # Информация о любом пользователе
result = await yunhu.Api.get_group_info("635409929")  # Информация о группе

# Файловые операции
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# Отмена сообщения (требуется дополнительный chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Многозадачность: указание учетной записи Bot
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Поддерживаемые стандартные действия

| Метод | Описание | Источник данных |
|------|------|---------|
| `get_self_info()` | Информация о роботе | Публичный Web API (bot-info) |
| `get_user_info(user_id)` | Информация о пользователе (любой пользователь может запросить) | Публичный Web API (user/homepage) |
| `get_group_info(group_id)` | Информация о группе | Публичный Web API (group-info) |
| `upload_file(*, type, name, ...)` | Загрузка файла (автоматически определяет image/video/file) | Bot открытый API |
| `get_file(file_id)` | Получение файла (file_id — это URL) | — |
| `delete_message(message_id, *, chat_id, chat_type)` | Отмена сообщения | Bot открытый API (/bot/recall) |

> **Внимание:** `get_self_info` / `get_user_info` / `get_group_info` реализованы через **непубличный публичный Web API** (chat-web-go.jwzhd.com). Эти интерфейсы не требуют аутентификации, но не являются официальной документацией и могут изменяться вместе с обновлениями платформы; в случае сбоя возвращается стандартный ответ об ошибке.

### Неподдерживаемые стандартные действия

Следующие стандартные действия не поддерживаются платформой Yunhu, вызов возвращает `retcode=10002` (не поддерживаемая операция):
- `get_friend_list` (Bot открытый API "список пользователей робота" еще не доступен)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Расширенные действия платформы

С помощью `Api.call("yunhu.xxx", **params)` вызываются расширенные действия Yunhu (параметры используют стиль именования OB12, адаптер автоматически переводит в поля Yunhu):

| Расширенное действие | Описание | Эквивалент Send метода |
|---------|------|---------------|
| `yunhu.recall` | Отмена сообщения (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Исключение участника группы (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Запрет (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Разрешение запрета (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | CRUD тегов группы (group_id, ...) | `Send.To("group", g).CreateTag(...)` и т.д. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Добавление/удаление тега у пользователя | `Send.To("group", g).AddUserTag(...)` и т.д. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Синоним семантики титула участника** (тег ≈ титул, внутреннее сопоставление к tag.relate) | — |
| `yunhu.msg_type_limit` | Ограничение типов сообщений в группе (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Получение истории сообщений (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Публичный запрос информации о bot (bot_id) | — |
| `yunhu.user_homepage` | Публичный запрос домашней страницы пользователя (user_id) | — |

```python
# Пример расширенного действия
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Теги и титулы:** Семантика "тегов" в Yunhu эквивалентна OneBot12 `title` участника группы. `yunhu.set_member_title` — это синоним семантический для `yunhu.tag.relate`, оба внутренне сопоставляются с одним и тем же конечным пунктом. В событиях сообщений роль отправителя отображается из `senderUserLevel` в стандартное поле `role` (`owner/admin/member`).

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно ожидать для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату ответа адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "self": {...},            // Информация о себе (включает bot_id)
    "message_id": "123456",   // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "yunhu_raw": {...}        // Оригинальные данные ответа
}
```

## Уникальные типы событий

Требуется platform=="yunhu" для использования функций данной платформы

### Основные отличия

1. Уникальные типы событий:
    - Формы (например, команды формы): yunhu_form
    - Эмодзи/стикер-сообщения: yunhu_expression
    - Нажатие кнопки: yunhu_button_click
    - Нажатие кнопки A2UI: yunhu_a2ui_button
    - Настройки робота: yunhu_bot_setting
    - Быстрые меню: yunhu_shortcut_menu
2. Расширение стандартных полей (4.3.0+):
    - В событиях сообщений добавлено стандартное поле `role` (отображается из `senderUserLevel` в `owner`/`admin`/`member`)
    - Добавлено поле `user_avatar` (URL аватара отправителя)
3. Расширенные поля:
    - Все уникальные поля имеют префикс yunhu_
    - Сохраняются исходные данные в поле yunhu_raw
    - В личных сообщениях self.user_id обозначает ID робота

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
        "label": "Название поля",
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

# Событие нажатия кнопки A2UI
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
    "interaction_json": "Строка JSON с данными взаимодействия"
  }
}

### Пример обработки события нажатия кнопки

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Обработка уведомления Yunhu

    Использование универсального декоратора on_notice() для обработки всех уведомлений,
    затем через detail_type различаем типы уведомлений
    event.reply() автоматически отправляет ответ через платформу Yunhu
    """
    # Проверка, является ли событие нажатия кнопки
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"Пользователь {user_nickname}({user_id}) нажал кнопку: {button_value}")

        # Использование event.reply() для автоматической отправки ответа (согласно платформе)
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
        await event.reply(f"Действие A2UI: {action_name}, данные формы: {form_context}")
```

### Использование цепочечного вызова для отправки сообщений с кнопками

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "Подтвердить", "actionType": 3, "value": "confirm"},
        {"text": "Отменить", "actionType": 3, "value": "cancel"},
        {"text": "Просмотреть подробности", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# Отправка сообщения с кнопками в группу
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Пожалуйста, подтвердите следующую операцию")

# Отправка сообщения с кнопками в личный чат
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Выберите свои предпочтения")
```

### Отправка A2UI сообщений

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# Отправка A2UI сообщений
await yunhu.Send.To("user", user_id).A2UI("Содержание интерактивной карточки A2UI")
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
      "value": "Значение параметра"
    }
  }
}

# Быстрое меню
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "ID пользователя, вызвавшего меню",
  "user_nickname": "Никнейм пользователя",
  "group_id": "ID группы (если это чат группы)",
  "yunhu_menu": {
    "id": "ID меню",
    "type": "Тип меню (целое число)",
    "action": "Действие меню (целое число)"
  }
}
```

## Расширенные методы Event Mixin

Адаптер зарегистрировал следующие платформенные методы, доступные только при `platform == "yunhu"`:

| Метод | Тип возвращаемого значения | Описание |
|------|----------|------|
| `get_raw_event()` | `dict` | Получить исходные данные события Yunhu (`yunhu_raw`) |
| `get_sender_level()` | `str` | Уровень отправителя на платформе Yunhu (`owner/administrator/member/unknown`) |
| `get_sender_role()` | `str` | Роль отправителя по стандарту OneBot12 (`owner/admin/member`) |
| `get_sender_title()` | `str` | Титул отправителя (доступ к стандартному полю `title`, зарезервировано) |
| `get_sender_avatar()` | `str` | URL аватара отправителя |
| `get_command()` | `dict` | Данные команды (только для событий команды, `yunhu_command`) |
| `get_button_value()` | `str` | Значение кнопки в событии нажатия кнопки (`yunhu_button.value`) |
| `get_a2ui_action()` | `str` | Действие A2UI в событии кнопки (`actionName`) |
| `get_a2ui_form_context()` | `dict` | Контекст формы A2UI в событии кнопки |
| `get_menu_id()` | `str` | ID события быстрого меню (`yunhu_menu.id`) |
| `get_setting()` | `dict` | Данные настроек в событии изменения настроек (`yunhu_setting`) |
| `is_command_message()` | `bool` | Является ли событие командой |
| `is_button_click()` | `bool` | Является ли событие нажатием кнопки |
| `is_a2ui_button()` | `bool` | Является ли событие нажатием кнопки A2UI |

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

## Пояснение расширенных полей

- Все уникальные поля имеют префикс `yunhu_`, чтобы избежать конфликта с стандартными полями
- Сохраняются исходные данные в поле `yunhu_raw`, для доступа к полным исходным данным платформы Yunhu
- `self.user_id` обозначает ID робота (получается из конфигурации bot_id)
- Команды формы предоставляются через поле `yunhu_command`
- События нажатия кнопки предоставляются через поле `yunhu_button`
- События нажатия кнопки A2UI предоставляются через поле `yunhu_a2ui`
- События изменения настроек робота предоставляются через поле `yunhu_setting`
- События быстрого меню предоставляются через поле `yunhu_menu`
- Эмодзи/стикер-сообщения предоставляются через сегмент `yunhu_expression` со стикер-данными (sticker_id, ID пакета стикеров, размер изображения и т.д.)

### Сегмент эмодзи/стикера (yunhu_expression)

При отправке пользователем эмодзи или стикера тип сегмента сообщения — `yunhu_expression`:

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

Адаптер Yunhu поддерживает одновременную конфигурацию и запуск нескольких роботов платформы Yunhu.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # API токен робота (обязательно)
mode = "ws"  # Режим приема (опционально, по умолчанию "ws", значения: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Путь для webhook (опционально, по умолчанию "/webhook")
enabled = true  # Включить ли аккаунт (опционально, по умолчанию true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # Токен второго робота
webhook_path = "/webhook/bot2"  # Отдельный путь для webhook
enabled = true
```

**Описание параметров конфигурации:**
- `token` — API токен, предоставленный платформой Yunhu (обязательно)
- `mode` — режим приема (опционально, по умолчанию "ws", значения: "ws", "webhook")
- `webhook_path` — HTTP путь для приема событий Yunhu (опционально, по умолчанию "/webhook", используется только в режиме webhook)
- `enabled` — включен ли аккаунт (опционально, по умолчанию true)

**Важные указания:**
1. ID робота платформы Yunhu автоматически определяется во время выполнения, не требуется указывать в конфигурации
2. В режиме webhook каждый робот должен иметь отдельный `webhook_path` для приема событий
3. При настройке webhook на платформе Yunhu, настройте соответствующий URL для каждого робота, например:
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

# Если не указать, используется первый включенный робот
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Примечание:** При использовании `bot_id` система автоматически находит соответствующий аккаунт в конфигурации. Это особенно полезно при обработке событий, где можно использовать `event["self"]["user_id"]` для ответа на то же аккаунт.

### ID робота в событиях

Полученные события автоматически содержат информацию об ID робота:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Получить ID робота, вызвавшего событие
        bot_id = event["self"]["user_id"]
        print(f"Сообщение от робота: {bot_id}")
        
        # Использовать того же робота для ответа
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответное сообщение")
```

### Информация в журнале

Адаптер автоматически включает `bot_id` в журнал для удобства отладки и отслеживания:

```
[INFO] [yunhu] [bot:30535459] Получено сообщение от пользователя user123
[INFO] [yunhu] [bot:12345678] Сообщение успешно отправлено, message_id: abc123
```

### Интерфейс управления

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

Старые конфигурации в формате `[Yunhu_Adapter.bots.*]` (с полем `bot_id`) автоматически мигрируются в формат `accounts` (`bot_id` теперь определяется во время выполнения, значения в конфигурации игнорируются); рекомендуется как можно скорее перейти на новый формат.