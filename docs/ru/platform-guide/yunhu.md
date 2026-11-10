# Характеристики платформы Yunhu

YunhuAdapter — это адаптер, построенный на протоколе Yunhu, объединяющий все модули Yunhu и предоставляющий единый интерфейс для обработки событий и операций сообщений.

---

## Информация о документе

- Версия соответствующего модуля: 4.6.2
- Сопровождающий: ErisPulse
- Последнее обновление: 2026-11-10

## Основная информация

- Краткое описание платформы: Yunhu — это корпоративная платформа мгновенного обмена сообщениями
- Название адаптера: YunhuAdapter
- Поддержка нескольких аккаунтов: Поддержка идентификации и настройки нескольких аккаунтов бота Yunhu с помощью bot_id
- Поддержка цепочечных модификаторов: Поддержка цепочечных методов модификации, таких как `.Reply()`
- Совместимость с OneBot12: Поддержка отправки сообщений в формате OneBot12

## Обновление парадигмы v5 (4.4.0)

Данный адаптер завершил выравнивание по парадигме v5 (инкрементальное обновление, совместимость API):

- **Полный набор официальных серверных API** (методы-расширения Api DSL): редактирование сообщений, массовая отправка, список сообщений, пользовательские/глобальные доски, заглушение участников группы, удаление участников группы, контроль типов сообщений в группе, CRUD тегов группы, назначение тегов пользователям
- **Стандартная секция keyboard** (стандарт кроссплатформенных интерактивных компонентов): секция {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} автоматически преобразуется в кнопки Yunhu; модификаторы .Buttons(rows) / .Keyboard(rows) принимают универсальную структуру (обратная совместимость с нативной структурой сохранена)
- **Стандартные поля интерактивных колбэков**: события нажатий кнопок / A2UI содержат стандартные поля interaction_id / button_data
- **Принадлежность задач spawn_background**: задачи WS-соединений переведены на `runtime.spawn_background`
- **Мягкая зависимость от фреймворка**: проверка ErisPulse>=2.7.1 во время выполнения с уведомлением; вывод журнала версий при запуске

### Расширенные действия платформы (методы call / Api)

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Методы Api (официальные серверные API)
await yunhu.Api.edit_message(msg_id, recv_id, "group", "text", {"text": "Новое содержимое"})
await yunhu.Api.batch_send(["userId1", "userId2"], "text", {"text": "Объявление"})
await yunhu.Api.get_message_list(group_id, "group", before=10)
await yunhu.Api.set_user_board(chat_id, "group", "Содержимое доски", expire_time=3600)
await yunhu.Api.dismiss_global_board()
await yunhu.Api.gag_group_member(group_id, user_id, 600)      # Заглушение на 600 секунд, 0 = снять
await yunhu.Api.remove_group_member(group_id, user_id)
await yunhu.Api.set_group_msg_type_limit(group_id, "text,image")
await yunhu.Api.create_group_tag(group_id, "VIP", color="#FF5733")
await yunhu.Api.add_user_tag(group_id, user_id, "VIP")

# Колбэк нажатия кнопки (стандартные поля)
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "yunhu" and event.get("button_data"):
        data = event["button_data"]     # Универсальное получение значения для всех платформ
        interaction_id = event["interaction_id"]
```

> Полное описание стандарта см. в [Стандарте кроссплатформенных интерактивных компонентов](../standards/standardization-guide.md).

## Согласование со стандартами (4.6.2)

В этой версии завершена стандартизация адаптера: структура ответов и коды ошибок соответствуют [спецификации API-ответов](../standards/api-response.md).

### Аккаунты и полный цикл работы с несколькими аккаунтами

- **Инъекция `self.account_id` в событиях** (внутреннее имя аккаунта): объект `self` полученного события содержит имя аккаунта, породившего данное событие; `event.reply()` автоматически маршрутизируется на **аккаунт, принявший данное событие** — в сценариях с несколькими аккаунтами больше не требуется вручную использовать `Using(bot_id)`
- **Двойные совместимые поля в `call_api`**: `account_id` (стандартное имя) / `_account_id` (старое имя) — оба позволяют указать аккаунт; ApiDSL фреймворка (`Api.Using(...)`) адаптируется автоматически
- **`Send` читает `send_context`** (с fallback на аккаунт события): при вызове `Send` в контексте обработки события по умолчанию используется аккаунт-источник

### Спецификация кодов ошибок

| retcode | Значение | Описание |
|---------|------|------|
| 0 | Успех | — |
| 33001 | Сетевая ошибка | Сетевые исключения, например сбой подключения к серверам Yunhu |
| 34100 | Ошибка платформы | Yunhu вернул ошибку; исходный ответ сохраняется в `yunhu_raw` |
| 10002 | Не поддерживается | Ресурс не существует (бот/пользователь/группа отсутствует) либо платформа не имеет соответствующей возможности для стандартного действия |
| 10003 | Ошибка параметров | Отсутствующие или недействительные параметры |

> **Изменения в 4.6.2**: после добавления `_platform` в адаптер `make_response` автоматически включает `yunhu_raw` средствами фреймворка; при сбоях платформы единообразно возвращается `34100`; «бот/пользователь/группа не существует» изменено с `34001` на `10002` (ресурс не существует).

### Изменение структуры ответа

Нестандартное поле `self` верхнего уровня исходного ответа перенесено в `data.self_info` (включая bot_id); на верхнем уровне остаются только стандартные поля и `yunhu_raw`:

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "self_info": {"user_id": "bot_id"},
    "messageInfo": {"msgId": "..."}
  },
  "message_id": "123456",
  "message": "",
  "yunhu_raw": {}
}
```

### Неизвестные события больше не отбрасываются молча

Нераспознанные события Yunhu теперь порождают событие `type="unknown"` (`detail_type` содержит исходный тип события, исходные данные сохраняются в `yunhu_raw`) и выводят предупреждение (warning) в лог; модули могут использовать это для диагностики необработанных типов событий.

### Соглашение о методах расширения платформы

Исторические методы расширения платформы (`edit_message` / `batch_send` / `set_user_board` / `gag_group_member` / `create_group_tag` и т. д.) остаются доступными; **новые расширения платформы выполняются единообразно через `Api.call("yunhu.xxx", **params)`** (см. раздел «Действия расширения платформы» ниже).

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочечный синтаксис, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`: отправка текстового сообщения.
- `.Html(html: str)`: отправка сообщения в формате HTML. `.HTML(html)` является псевдонимом (для единообразия с именованием стандартного метода Send).
- `.Markdown(markdown: str)`: отправка сообщения в формате Markdown.
- `.MergeForward(nodes, title="Объединённая история чата")`: отправка объединённого пересылаемого сообщения (рендерится как сворачиваемая HTML-карточка `<details>` и отправляется через канал html).
- `.A2UI(text: str)`: отправка сообщения в формате A2UI.
- `.Image(file: bytes, stream: bool = False, filename: str = None)`: отправка изображения, поддерживает потоковую загрузку и пользовательское имя файла.
- `.Video(file: bytes, stream: bool = False, filename: str = None)`: отправка видео, поддерживает потоковую загрузку и пользовательское имя файла.
- `.File(file: bytes, stream: bool = False, filename: str = None)`: отправка файла, поддерживает потоковую загрузку и пользовательское имя файла.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`: массовая отправка сообщений.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`: редактирование существующего сообщения.
- `.Recall(msg_id: str)`: отзыв сообщения.
- `.Board(content: str, content_type: str = "text")`: публикация доски объявлений. Область действия определяется автоматически с помощью `To()` (цель указана = локальная доска, не указана = глобальная доска). Цепочка модификаторов: `.Expire(duration)` — относительный срок действия (в секундах), `.ExpireAt(timestamp)` — абсолютный срок действия (timestamp в секундах), `.ForMember(member_id)` — доска для участника группы; **при пустом содержимом автоматически преобразуется в отмену доски**. По-прежнему поддерживается старый стиль с явным указанием scope: `Board("local", "Объявление")`.
- `.DismissBoard()`: отмена доски объявлений. Область действия также определяется с помощью `To()`, поддерживается `.ForMember(member_id)`; по-прежнему поддерживается старый стиль записи `DismissBoard("local")`.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`: отправка потокового сообщения.

### Методы управления группой

Все методы управления группой требуют указания группы через цепочечный синтаксис, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`: удаление участника группы. Боту требуется разрешение `разрешить удалять участников группы`.
- `.Ban(user_id: str, duration: int = 600)`: мут пользователя. `duration` — длительность мута (в секундах), 0 — снятие мута, -1 — перманентный мут. Боту требуется разрешение `разрешить мутить пользователей`.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`: создание тега группы. Формат `color` — #RRGGBB, чем меньше значение `sort`, тем выше позиция. Боту требуется разрешение `разрешить управлять группами тегов`.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`: изменение тега группы. Все параметры необязательны, если не переданы — не изменяются. Боту требуется разрешение `разрешить управлять группами тегов`.
- `.DeleteTag(tag: str)`: удаление тега группы. Боту требуется разрешение `разрешить управлять группами тегов`.
- `.GetTagList()`: получение списка тегов группы. Возвращает данные ответа, содержащие массив `list`.
- `.AddUserTag(user_id: str, tag: str)`: добавление тега пользователю. Боту требуется разрешение `разрешить управлять группами тегов`.
- `.RemoveUserTag(user_id: str, tag: str)`: удаление тега у пользователя. Боту требуется разрешение `разрешить управлять группами тегов`.
- `.SetMsgTypeLimit(types: str)`: управление типами сообщений в группе. `types` — названия типов сообщений, несколько значений разделяются запятыми (например, `"text,image,video"`), пустая строка означает отсутствие ограничений. Боту требуется разрешение `разрешить изменять информацию о группе`.

### Методы запроса сообщений

Получение списка истории сообщений указанного диалога (пользователь/группа) требует указания цели через цепочечный синтаксис, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`: получение истории сообщений диалога. Возвращает данные ответа, содержащие массив `list` и общее количество `total`.
  - `message_id`: ID сообщения (необязательно). Если не указан, в сочетании с `before` возвращает последние N сообщений.
  - `before`: возвращает N сообщений перед указанным ID сообщения.
  - `after`: возвращает N сообщений после указанного ID сообщения.
  - > **Примечание:** необходимо указать хотя бы один из параметров `before` или `after`, и его значение должно быть больше 0, иначе сервер не вернёт ни одного сообщения.

Область действия Board определяется автоматически с помощью `To()`:
- Указано `To(target_type, target_id)` → локальная доска (указанный пользователь/группа)
- Не указано `To()` → глобальная доска

```python
# Локальная доска (относительный срок действия через 60 секунд)
await yunhu.Send.To("group", group_id).Expire(60).Board("Объявление", content_type="markdown")

# Доска для участника группы (видна только указанному участнику)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("Видно только тебе")

# Истечение по абсолютному timestamp
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("Истечение в указанное время")

# Глобальная доска
await yunhu.Send.Board("Глобальное объявление")

# Очистка локальной доски (пустое содержимое → автоматическая отмена)
await yunhu.Send.To("group", group_id).Board("")
```

### Описание параметров кнопок

Параметр `buttons` представляет собой вложенный список, описывающий расположение и функциональность кнопок. Каждый объект кнопки содержит следующие поля:

| Поле         | Тип    | Обязательно | Описание                                                             |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Да       | Текст на кнопке                                                         |
| `actionType` | int    | Да       | Тип действия:<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отчёт по клику            |
| `url`        | string | Нет      | Используется при `actionType=1`; указывает целевой URL для перехода                         |
| `value`      | string | Нет      | При `actionType=2` это значение копируется в буфер обмена<br>При `actionType=3` это значение отправляется подписчику |

Пример:
```python
buttons = [
    [
        {"text": "Копировать", "actionType": 2, "value": "xxxx"},
        {"text": "Клик для перехода", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Отчёт о событии", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("Сообщение с кнопками")
```
> **Примечание:**
> - Push-уведомление будет получено только при нажатии пользователем кнопки **отчёта о событии**; при **копировании** и **переходе по URL** получить push-уведомление невозможно.

### Цепочечные методы-модификаторы (можно комбинировать)

Цепочечные методы-модификаторы возвращают `self`, поддерживают цепочечный вызов и должны вызываться перед финальным методом отправки:

- `.Reply(message_id: str)`: ответ на указанное сообщение.
- `.At(user_id: str)`: упоминание (@) указанного пользователя.
- `.AtAll()`: упоминание (@) всех.
- `.Buttons(buttons: List)`: добавление кнопок.

### Примеры цепочечных вызовов

```python
# Базовая отправка
await yunhu.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("Ответ на сообщение")

# Ответ + кнопки
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Сообщение с ответом и кнопками")
```

### Примеры управления группой

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Удаление участника группы
await yunhu.Send.To("group", group_id).Kick(user_id)

# Мут пользователя (10 минут)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Снятие мута
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Перманентный мут
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

# Отмена ограничения типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Примеры запроса сообщений

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Получение последних 10 сообщений группы (всего возвращается 10 сообщений)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Получение 10 сообщений перед указанным ID сообщения в группе (всего возвращается 11 сообщений)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Получение по 10 сообщений до и после указанного ID сообщения в группе (всего возвращается 21 сообщение)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Получение истории сообщений диалога с пользователем
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12, что упрощает кроссплатформенную совместимость сообщений:

- `.Raw_ob12(message: List[Dict], **kwargs)`: отправка сообщений в формате OneBot12.

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

Все методы отправки возвращают объект Task, результат отправки можно получить напрямую через await. Возвращаемый результат следует стандартизированной спецификации возврата адаптеров ErisPulse:

```python
{
    "status": "ok",           // статус выполнения
    "retcode": 0,             // код возврата
    "data": {...},            // данные ответа (self_info содержит bot_id, см. «Корректировка структуры ответа»)
    "message_id": "123456",   // ID сообщения
    "message": "",            // сообщение об ошибке
    "yunhu_raw": {...}        // исходные данные ответа
}
```

> **Изменения в 4.6.2**: нестандартное поле `self` на верхнем уровне исходного ответа перемещено в `data.self_info`. Для получения bot_id используйте `result["data"]["self_info"]["user_id"]`.

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

Адаптер Yunhu поддерживает одновременную настройку и запуск нескольких аккаунтов ботов Yunhu.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # токен бота (обязательный)
mode = "ws"  # режим приёма (опционально, по умолчанию "ws", возможные значения: "ws", "webhook")
webhook_path = "/webhook/bot1"  # путь Webhook (опционально, по умолчанию "/webhook")
enabled = true  # включён ли (опционально, по умолчанию true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # токен второго бота
webhook_path = "/webhook/bot2"  # отдельный путь webhook
enabled = true
```

**Описание параметров конфигурации:**
- `token`: API-токен, предоставляемый платформой Yunhu (обязательный)
- `mode`: режим приёма (опционально, по умолчанию `"ws"`, возможные значения `"ws"`, `"webhook"`)
- `webhook_path`: HTTP-путь для приёма событий Yunhu (опционально, по умолчанию "/webhook", используется только в режиме webhook)
- `enabled`: включён ли данный аккаунт (опционально, по умолчанию true)

**Важные замечания:**
1. ID бота платформы Yunhu **автоматически определяется во время выполнения**, указывать его в конфигурации не требуется
2. В режиме webhook у каждого бота должен быть отдельный `webhook_path` для приёма соответствующих webhook-событий
3. При настройке webhook на платформе Yunhu укажите для каждого бота соответствующий URL, например:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Указание бота через Send DSL

Можно указать, какой бот будет отправлять сообщения, с помощью метода `Using()`. Этот метод поддерживает два типа параметров:
- **Имя аккаунта**: имя бота в конфигурации (например, `bot1`, `bot2`)
- **bot_id**: значение `bot_id` из конфигурации

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Отправка сообщения по имени аккаунта
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# Отправка сообщения по bot_id (соответствующий аккаунт определяется автоматически)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# Если не указано, используется первый включённый бот
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Примечание:** При использовании `bot_id` система автоматически находит соответствующий аккаунт в конфигурации. Это особенно полезно при обработке ответов на события: можно напрямую использовать `event["self"]["user_id"]` для ответа от того же аккаунта.

### Идентификация бота в событиях

Полученные события автоматически содержат соответствующую информацию `bot_id` (начиная с версии 4.6.2 также внедряется внутреннее имя аккаунта `self.account_id`):

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Получение ID бота, вызвавшего событие
        bot_id = event["self"]["user_id"]
        account_id = event["self"].get("account_id", "")  # внутреннее имя аккаунта (например, bot1)
        print(f"Сообщение от бота: {bot_id} (аккаунт: {account_id})")

        # Начиная с 4.6.2 event.reply() автоматически направляет ответ в обрабатывающий аккаунт, можно отвечать напрямую
        await event.reply("Ответное сообщение")

        # При необходимости можно явно указать аккаунт для отправки
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответное сообщение")
```

> **Примечание:** `call_api` поддерживает два совместимых поля аккаунта: `account_id` (стандартное имя) и `_account_id` (старое имя); как `Using()` в ApiDSL фреймворка, так и резервный механизм аккаунта события (`send_context`) адаптируются автоматически.

### Информация в журналах

Адаптер автоматически включает информацию `bot_id` в журналы для удобства отладки и отслеживания:

```
[INFO] [yunhu] [bot:30535459] Получено личное сообщение от пользователя user123
[INFO] [yunhu] [bot:12345678] Сообщение успешно отправлено, message_id: abc123
```

### Интерфейсы управления

```python
# Получение информации обо всех аккаунтах
bots = yunhu.bots

# Проверка, включён ли аккаунт
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# Динамическое включение/отключение аккаунта (требуется перезапуск адаптера)
yunhu.bots["bot1"].enabled = False
```

### Совместимость со старой конфигурацией

Старая конфигурация `[Yunhu_Adapter.bots.*]` (с полем `bot_id`) автоматически мигрирует в формат `accounts` (`bot_id` теперь определяется автоматически во время выполнения, значение в конфигурации игнорируется); рекомендуется как можно скорее перейти на новый формат.