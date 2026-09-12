# Документация по функциям платформы Yunhu

YunhuAdapter — это адаптер, построенный на базе протокола Yunhu, объединяющий все модули функций Yunhu и предоставляющий единый интерфейс обработки событий и операций сообщений.

---

## Информация о документации

- Версия соответствующего модуля: 4.4.0
- Ответственный: ErisPulse

## Основная информация

- Описание платформы: Yunhu (云湖) — это корпоративная платформа мгновенного обмена сообщениями
- Имя адаптера: YunhuAdapter
- Поддержка нескольких аккаунтов: поддержка распознавания и настройки нескольких аккаунтов роботов Yunhu посредством bot_id
- Поддержка цепочки модификаторов: поддержка цепочки модификаторов, таких как `.Reply()`
- Совместимость с OneBot12: поддержка отправки сообщений в формате OneBot12

## Обновление парадигмы v5 (4.4.0)

Адаптер был обновлен до соответствия парадигме v5 (инкрементальное обновление, совместимость API):

- **Полный набор официальных серверных API** (расширения методов DSL Api): редактирование сообщений, пакетная отправка, список сообщений, панели пользователей/глобальные панели, ограничение участников группы, удаление участников группы, контроль типов сообщений в группе, CRUD-операции с тегами групп, добавление тегов пользователям
- **Стандартный сегмент keyboard** (стандартный компонент взаимодействия между платформами): сегмент {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} автоматически преобразуется в buttons облака; декораторы .Buttons(rows) / .Keyboard(rows) принимают общую структуру (оригинальная структура обратно совместима)
- **Стандартные поля для обратного вызова взаимодействия**: события нажатия кнопок/A2UI включают стандартные поля interaction_id / button_data
- **Принадлежность задачи spawn_background**: задачи WS-подключения теперь используют runtime.spawn_background
- **Мягкие зависимости фреймворка**: во время выполнения проверяется наличие ErisPulse>=2.7.1 и выводится соответствующее уведомление; при запуске выводится лог версии

### Платформенные расширенные действия (call / методы Api)

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Методы Api (официальные серверные API)
await yunhu.Api.edit_message(msg_id, recv_id, "group", "text", {"text": "Новый контент"})
await yunhu.Api.batch_send(["userId1", "userId2"], "text", {"text": "Анонс"})
await yunhu.Api.get_message_list(group_id, "group", before=10)
await yunhu.Api.set_user_board(chat_id, "group", "Содержание панели", expire_time=3600)
await yunhu.Api.dismiss_global_board()
await yunhu.Api.gag_group_member(group_id, user_id, 600)      # Запрет на 600 секунд, 0=отмена
await yunhu.Api.remove_group_member(group_id, user_id)
await yunhu.Api.set_group_msg_type_limit(group_id, "text,image")
await yunhu.Api.create_group_tag(group_id, "VIP", color="#FF5733")
await yunhu.Api.add_user_tag(group_id, user_id, "VIP")

# Обратный вызов нажатия кнопки (стандартные поля)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "yunhu" and event.get("button_data"):
        data = event["button_data"]     # Единый доступ к данным между платформами
        interaction_id = event["interaction_id"]
```

> Подробное описание стандарта доступно в [Стандарте компонентов взаимодействия между платформами](../../standards/standardization-guide.md).

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка обычного текстового сообщения.
- `.Html(html: str)` — отправка HTML-форматированного сообщения.
- `.Markdown(markdown: str)` — отправка сообщения в формате Markdown.
- `.A2UI(text: str)` — отправка сообщения в формате A2UI.
- `.Image(file: bytes, stream: bool = False, filename: str = None)` — отправка изображения, поддержка потоковой загрузки и возможность указать имя файла.
- `.Video(file: bytes, stream: bool = False, filename: str = None)` — отправка видео, поддержка потоковой загрузки и возможность указать имя файла.
- `.File(file: bytes, stream: bool = False, filename: str = None)` — отправка файла, поддержка потоковой загрузки и возможность указать имя файла.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)` — массовая отправка сообщений.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)` — редактирование существующего сообщения.
- `.Recall(msg_id: str)` — отмена отправки сообщения.
- `.Board(content: str, content_type: str = "text")` — публикация сообщения на доске объявлений. Область действия определяется методом `To()` (указание цели = локальная доска, не указано = глобальная доска). Цепочка модификаторов: `.Expire(duration)` — относительное время истечения (в секундах), `.ExpireAt(timestamp)` — абсолютное время истечения (секундный временной штамп), `.ForMember(member_id)` — доска объявлений для участника группы; **при пустом содержимом автоматически преобразуется в отмену доски объявлений**. По-прежнему поддерживается старый способ явного указания области действия `Board("local", "公告")`.
- `.DismissBoard()` — отмена доски объявлений. Область действия определяется методом `To()` и поддерживает `.ForMember(member_id)`; по-прежнему поддерживается старый способ `DismissBoard("local")`.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)` — отправка потокового сообщения.

### Методы управления группами

Все методы управления группами требуют цепочечного синтаксиса для указания группы, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)` — исключение участника из группы. Робот должен иметь права `Разрешить исключение участников из группы`.
- `.Ban(user_id: str, duration: int = 600)` — мут участника. `duration` — длительность мута (в секундах), 0 — размут, -1 — пожизненный мут. Робот должен иметь права `Разрешить мутить участников`.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)` — создание тега группы. `color` в формате #RRGGBB, `sort` — чем меньше, тем выше в списке. Робот должен иметь права `Разрешить управлять тегами`.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)` — изменение тега группы. Каждый параметр необязателен, если не передан, то не изменяется. Робот должен иметь права `Разрешить управлять тегами`.
- `.DeleteTag(tag: str)` — удаление тега группы. Робот должен иметь права `Разрешить управлять тегами`.
- `.GetTagList()` — получение списка тегов группы. Возвращает данные с массивом `list`.
- `.AddUserTag(user_id: str, tag: str)` — добавление тега участнику. Робот должен иметь права `Разрешить управлять тегами`.
- `.RemoveUserTag(user_id: str, tag: str)` — удаление тега у участника. Робот должен иметь права `Разрешить управлять тегами`.
- `.SetMsgTypeLimit(types: str)` — ограничение типов сообщений в группе. `types` — имена типов сообщений, разделенные запятыми (например, `"text,image,video"`), пустая строка означает отсутствие ограничений. Робот должен иметь права `Разрешить изменять информацию о группе`.

### Методы запроса сообщений

Получение списка истории сообщений в указанном диалоге (пользователь/группа) требует цепочечного синтаксиса для указания цели, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)` — получение истории сообщений в диалоге. Возвращает данные с массивом `list` и общим количеством `total`.
  - `message_id` — идентификатор сообщения (необязательно). Если не указан, в сочетании с `before` возвращает последние N сообщений.
  - `before` — возвращает N сообщений до указанного идентификатора.
  - `after` — возвращает N сообщений после указанного идентификатора.
  - > **Примечание:** необходимо указать хотя бы один из параметров `before` или `after`, и значение должно быть больше 0, иначе сервер не вернет никаких сообщений.

Область действия доски объявлений определяется автоматически методом `To()`:
- Указание `To(target_type, target_id)` → локальная доска (указанная цель/группа)
- Не указано `To()` → глобальная доска

```python
# Локальная доска (относительное истечение через 60 секунд)
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# Доска для участника группы (видна только указанному участнику)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("仅你可见")

# Абсолютное время истечения
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("指定时间过期")

# Глобальная доска
await yunhu.Send.Board("全局公告")

# Очистка локальной доски (пустое содержимое → автоматическая отмена)
await yunhu.Send.To("group", group_id).Board("")
```

### Параметры кнопок

Параметр `buttons` представляет собой вложенный список, описывающий расположение и функции кнопок. Каждый объект кнопки содержит следующие поля:

| Поле         | Тип   | Обязательно | Описание                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Да       | Текст на кнопке                                                         |
| `actionType` | int    | Да       | Тип действия:<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отправка события            |
| `url`        | string | Нет       | Используется, когда `actionType=1`, указывает целевой URL для перехода                         |
| `value`      | string | Нет       | При `actionType=2` значение копируется в буфер обмена<br>При `actionType=3` значение отправляется подписчику |

Пример:
```python
buttons = [
    [
        {"text": "复制", "actionType": 2, "value": "xxxx"},
        {"text": "点击跳转", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "汇报事件", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("带按钮的消息")
```
> **Примечание:**
> - Только при нажатии кнопки типа **汇报事件** будет отправлено уведомление, кнопки **复制** и **跳转URL** не будут вызывать уведомления.

### Методы цепочечного модифицирования (можно комбинировать)

Методы цепочечного модифицирования возвращают `self`, поддерживают цепочечное использование и должны вызываться до окончательного метода отправки:

- `.Reply(message_id: str)` — ответ на указанное сообщение.
- `.At(user_id: str)` — упоминание указанного пользователя.
- `.AtAll()` — упоминание всех участников.
- `.Buttons(buttons: List)` — добавление кнопок.

### Примеры цепочечного вызова

```python
# Базовая отправка
await yunhu.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("回复消息")

# Ответ + кнопки
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("带回复和按钮的消息")
```

### Примеры управления группами

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Исключение участника из группы
await yunhu.Send.To("group", group_id).Kick(user_id)

# Мут участника (10 минут)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Размут
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Пожизненный мут
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Создание тега группы
await yunhu.Send.To("group", group_id).CreateTag("VIP用户", color="#FF5733", desc="VIP会员")

# Изменение тега группы
await yunhu.Send.To("group", group_id).EditTag("VIP用户", new_tag="SVIP用户", color="#33C4FF")

# Удаление тега группы
await yunhu.Send.To("group", group_id).DeleteTag("VIP用户")

# Получение списка тегов группы
result = await yunhu.Send.To("group", group_id).GetTagList()

# Добавление тега участнику
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP用户")

# Удаление тега у участника
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP用户")

# Ограничение типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Отмена ограничения типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Примеры запроса сообщений

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Получение последних 10 сообщений группы (всего 10 сообщений)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Получение 10 сообщений до указанного идентификатора (всего 11 сообщений)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Получение по 10 сообщений до и после указанного идентификатора (всего 21 сообщение)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Получение истории сообщений диалога с пользователем
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку OneBot12 формата сообщений, что обеспечивает совместимость между платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "回复消息"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Стандартные действия API (ApiDSL)

> [!NOTE]
> Эта функция требует ErisPulse **2.7.0+** и YunhuAdapter **4.3.0+**.

Помимо цепочечной отправки `Send`, адаптер также предоставляет внутренний класс `Api`, который предоставляет стандартные действия API OneBot12 и расширенные действия платформы Yunhu. Все методы возвращают стандартный формат ответа.

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Информационный запрос (через открытый Web API, без аутентификации)
result = await yunhu.Api.get_self_info()              # Информация о самом боте
result = await yunhu.Api.get_user_info("7058262")     # Информация о любом пользователе
result = await yunhu.Api.get_group_info("635409929")  # Информация о группе

# Операции с файлами
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# Отмена сообщения (требуется дополнительная передача chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Множественные аккаунты: указание учетной записи бота
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Поддерживаемые стандартные действия

| Метод | Описание | Источник данных |
|------|------|---------|
| `get_self_info()` | Информация о самом боте | Открытый Web API (bot-info) |
| `get_user_info(user_id)` | Информация о пользователе (любой пользователь может получить доступ) | Открытый Web API (user/homepage) |
| `get_group_info(group_id)` | Информация о группе | Открытый Web API (group-info) |
| `upload_file(*, type, name, ...)` | Загрузка файла (автоматическое определение image/video/file) | Open API бота |
| `get_file(file_id)` | Получение файла (file_id - это URL) | — |
| `delete_message(message_id, *, chat_id, chat_type)` | Отмена сообщения | Open API бота (/bot/recall) |

> **Внимание**: `get_self_info` / `get_user_info` / `get_group_info` реализованы через **неофициальные открытые Web API** (chat-web-go.jwzhd.com). Эти интерфейсы не требуют аутентификации, но не документированы официально и могут меняться с обновлениями платформы; при сбое возвращается стандартный ответ об ошибке.

### Не поддерживаемые стандартные действия

Следующие стандартные действия отсутствуют в API Yunhu, при вызове возвращается `retcode=10002` (не поддерживаемая операция):
- `get_friend_list` (список пользователей бота в Open API пока не доступен)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Расширенные действия платформы

Через `Api.call("yunhu.xxx", **params)` вызываются специфичные для Yunhu действия (параметры используют имена в стиле OB12, адаптер автоматически переводит их в поля Yunhu):

| Расширенное действие | Описание | Эквивалентный метод Send |
|---------|------|---------------|
| `yunhu.recall` | Отмена сообщения (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Исключение участника группы (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Запрет (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Отмена запрета (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | CRUD-операции с тегами группы (group_id, ...) | `Send.To("group", g).CreateTag(...)` и т.д. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Добавление/удаление тега для пользователя | `Send.To("group", g).AddUserTag(...)` и т.д. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Синоним семантики заголовка участника** (тег ≈ заголовок, внутреннее сопоставление к tag.relate) | — |
| `yunhu.msg_type_limit` | Ограничение типа сообщений в группе (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Получение истории сообщений (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Открытый запрос bot-info (bot_id) | — |
| `yunhu.user_homepage` | Открытый запрос домашней страницы пользователя (user_id) | — |

```python
# Примеры расширенных действий платформы
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Теги и заголовки**: Семантика "тегов" в Yunhu эквивалентна OneBot12 для участника группы `title`. `yunhu.set_member_title` является семантическим синонимом `yunhu.tag.relate`, оба внутренне сопоставляются к одному конечному пункту. Роль отправителя в событии сообщения группы отображается через `senderUserLevel` в стандартное поле `role` (owner/admin/member).

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект Task, который можно напрямую ожидать с помощью await для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату ответа адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "self": {...},            // Информация о себе (содержит bot_id)
    "message_id": "123456",   // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "yunhu_raw": {...}        // Необработанные данные ответа
}
```

## Типы событий, специфичные для платформы

Необходимо проверить platform=="yunhu", чтобы использовать функции данной платформы.

### Основные отличия

1. Специфичные типы событий:
    - Форма (например, форма-команда): yunhu_form
    - Эмодзи/стикер-сообщение: yunhu_expression
    - Нажатие кнопки: yunhu_button_click
    - Нажатие кнопки A2UI: yunhu_a2ui_button
    - Настройка бота: yunhu_bot_setting
    - Быстрое меню: yunhu_shortcut_menu
2. Расширение стандартных полей (4.3.0+):
    - В событиях сообщений добавлено стандартное поле `role` (отображается из yunhu `senderUserLevel` как `owner`/`admin`/`member`)
    - Добавлено поле `user_avatar` (URL аватара отправителя)
3. Расширенные поля:
    - Все специфичные поля имеют префикс yunhu_
    - Исходные данные сохраняются в поле yunhu_raw
    - В личных сообщениях self.user_id обозначает ID бота

### Примеры специальных полей

```python
# Команда формы
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "Название формы",
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
    "interaction_json": "JSON-строка с данными взаимодействия"
  }
}

### Пример обработки события нажатия кнопки

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Обработка уведомления платформы Yunhu

    Используйте общий декоратор on_notice() для обработки всех уведомлений,
    затем различайте типы уведомлений по detail_type.
    event.reply() автоматически отправит ответ через платформу Yunhu.
    """

# Проверка, является ли событие нажатием кнопки
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"Пользователь {user_nickname}({user_id}) нажал на кнопку: {button_value}")

# Автоматическая отправка ответа с помощью event.reply() (система автоматически выбирает правильный способ отправки в зависимости от платформы)
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

# Обработка изменений настроек бота
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"Настройки обновлены: {settings}")

# Обработка событий кнопок A2UI
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"Действие A2UI: {action_name}, данные формы: {form_context}")
```

### Использование цепочки вызовов для отправки сообщения с кнопками

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

# Отправка сообщения с кнопками в группу
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Пожалуйста, подтвердите следующее действие")

# Отправка сообщения с кнопками в личный чат пользователя  
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Пожалуйста, выберите свои предпочтительные настройки")  

### Отправка сообщения A2UI  

```python  
from ErisPulse import sdk  

yunhu = sdk.adapter.get("yunhu")  
```

# Отправка сообщения A2UI
await yunhu.Send.To("user", user_id).A2UI("Содержание интерактивной карточки A2UI")
```

# Настройка бота
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "ID группы (может быть пустым)",
  "user_nickname": "Имя пользователя",
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
  "user_id": "ID пользователя, запустившего меню",
  "user_nickname": "Имя пользователя",
  "group_id": "ID группы (если это групповой чат)",
  "yunhu_menu": {
    "id": "ID меню",
    "type": "Тип меню (целое число)",
    "action": "Действие меню (целое число)"
  }
}
```

## Event Mixin Расширения

Адаптер зарегистрировал следующие методы, специфичные для платформы, доступные только при `platform == "yunhu"`:

| Метод | Возвращаемый тип | Описание |
|------|----------|------|
| `get_raw_event()` | `dict` | Получить исходные данные события Yunhu (`yunhu_raw`) |
| `get_sender_level()` | `str` | Уровень отправителя Yunhu (owner/administrator/member/unknown) |
| `get_sender_role()` | `str` | Роль отправителя в стандартном формате OneBot12 (owner/admin/member) |
| `get_sender_title()` | `str` | Титул отправителя (резервный доступ к полю `title`) |
| `get_sender_avatar()` | `str` | URL аватара отправителя |
| `get_command()` | `dict` | Данные команды (только для событий сообщений команд, `yunhu_command`) |
| `get_button_value()` | `str` | Значение кнопки в событии нажатия (поле `yunhu_button.value`) |
| `get_a2ui_action()` | `str` | Название действия кнопки A2UI |
| `get_a2ui_form_context()` | `dict` | Контекст формы события кнопки A2UI |
| `get_menu_id()` | `str` | Идентификатор события быстрого меню (поле `yunhu_menu.id`) |
| `get_setting()` | `dict` | Данные настроек события робота (поле `yunhu_setting`) |
| `is_command_message()` | `bool` | Является ли сообщение командой |
| `is_button_click()` | `bool` | Является ли событием нажатия кнопки |
| `is_a2ui_button()` | `bool` | Является ли событием кнопки A2UI |

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

- Все специфические поля имеют префикс `yunhu_`, чтобы избежать конфликта с стандартными полями
- Исходные данные сохраняются в поле `yunhu_raw`, что позволяет получить доступ к полным исходным данным платформы Yunhu
- `self.user_id` обозначает ID бота (получается из конфигурации через bot_id)
- Команды формы предоставляются в виде структурированных данных через поле `yunhu_command`
- События нажатия кнопки предоставляются через поле `yunhu_button`, содержащее информацию о кнопке
- События кнопок A2UI предоставляются через поле `yunhu_a2ui`, содержащее информацию об A2UI-взаимодействии
- Изменения настроек бота предоставляются через поле `yunhu_setting`, содержащее данные настроек
- Операции с быстрым меню предоставляются через поле `yunhu_menu`, содержащее информацию о меню
- Сообщения с эмодзи/наклейками предоставляются через сегмент сообщения `yunhu_expression`, содержащий данные о наклейке (sticker_id, ID набора наклеек, размеры изображения и т.д.)

### Сегмент сообщения с эмодзи/наклейками (yunhu_expression)

Когда пользователь отправляет эмодзи или наклейку, тип сегмента сообщения будет `yunhu_expression`:

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
| `sticker_id` | string | Уникальный идентификатор наклейки |
| `sticker_pack_id` | string | ID набора наклеек |
| `expression_id` | string | ID эмодзи |
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
                print(f"Получен эмодзи: sticker_id={data['sticker_id']}, ID пака={data['sticker_pack_id']}")
```

## Многоботная конфигурация

### Описание конфигурации

Адаптер Yunhu поддерживает одновременную настройку и запуск нескольких аккаунтов ботов Yunhu.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # Токен бота (обязательно)
mode = "ws"  # Режим получения (необязательно, по умолчанию "ws", доступны значения: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Путь для webhook (необязательно, по умолчанию "/webhook")
enabled = true  # Включить аккаунт (необязательно, по умолчанию true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # Токен второго бота
webhook_path = "/webhook/bot2"  # Отдельный путь для webhook
enabled = true
```

**Описание параметров:**
- `token`: API-токен, предоставляемый платформой Yunhu (обязательно)
- `mode`: Режим получения (необязательно, по умолчанию "ws", доступны значения "ws", "webhook")
- `webhook_path`: HTTP-путь для получения событий Yunhu (необязательно, по умолчанию "/webhook", используется только в режиме webhook)
- `enabled`: Включить этот аккаунт (необязательно, по умолчанию true)

**Важные замечания:**
1. Идентификатор бота на платформе Yunhu **автоматически определяется во время запуска**, не нужно указывать его в конфигурации
2. В режиме webhook каждый бот должен иметь уникальный `webhook_path` для получения соответствующих событий webhook
3. При настройке webhook на платформе Yunhu, для каждого бота нужно указать соответствующий URL, например:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Использование Send DSL для указания бота

Можно использовать метод `Using()` для указания бота, через которого будет отправлено сообщение. Этот метод поддерживает два параметра:
- **Имя аккаунта**: имя бота из конфигурации (например, `bot1`, `bot2`)
- **bot_id**: значение `bot_id` из конфигурации

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Отправка сообщения через имя аккаунта
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# Отправка сообщения через bot_id (автоматически сопоставляется с соответствующим аккаунтом)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# Без указания бота используется первый включенный бот
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Подсказка:** При использовании `bot_id` система автоматически находит соответствующий аккаунт в конфигурации. Это особенно полезно при обработке ответов на события, где можно использовать `event["self"]["user_id"]` для ответа через тот же аккаунт.

### Идентификация бота в событиях

Полученные события автоматически содержат информацию о `bot_id`:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Получение ID бота, который вызвал событие
        bot_id = event["self"]["user_id"]
        print(f"Сообщение пришло от бота: {bot_id}")
        
        # Ответ через того же бота
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответ на сообщение")
```

### Информация в логах

Адаптер автоматически включает `bot_id` в логи, что облегчает отладку и отслеживание:

```
[INFO] [yunhu] [bot:30535459] Получено личное сообщение от пользователя user123
[INFO] [yunhu] [bot:12345678] Сообщение успешно отправлено, message_id: abc123
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

# Динамическое включение/выключение аккаунта (требуется перезапуск адаптера)
yunhu.bots["bot1"].enabled = False
```

### Совместимость со старой конфигурацией

Старая конфигурация `[Yunhu_Adapter.bots.*]` (с полем `bot_id`) автоматически мигрируется в формат `accounts` (`bot_id` теперь определяется во время запуска, значение в конфигурации игнорируется); рекомендуется как можно скорее перейти на новый формат.