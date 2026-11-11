# Документация по функциям Yunhu Platform

YunhuAdapter — это адаптер, построенный на протоколе Yunhu, объединяющий все функциональные модули Yunhu и предоставляющий единый интерфейс обработки событий и операций сообщений.

---

## Информация о документации

- Версия соответствующего модуля: 4.6.2
- Ответственный: ErisPulse
- Последнее обновление: 2026-11-10

## Основная информация

- Краткое описание платформы: Yunhu — это корпоративная платформа мгновенного обмена сообщениями
- Название адаптера: YunhuAdapter
- Поддержка нескольких аккаунтов: Поддержка идентификации и настройки нескольких аккаунтов ботов Yunhu по bot_id
- Поддержка цепочечных модификаторов: Поддержка цепочечных методов модификации, таких как `.Reply()`
- Совместимость с OneBot12: Поддержка отправки сообщений в формате OneBot12

## Обновление до парадигмы v5 (4.4.0)

Данный адаптер завершил выравнивание до парадигмы v5 (инкрементальное обновление, совместимость API):

- **Полный набор API официального сервера** (расширения Api DSL): редактирование сообщений, массовая отправка, список сообщений, панели пользователей/глобальные панели, запрет на сообщения в группе, удаление участников группы, контроль типов сообщений в группе, CRUD-операции с метками группы, добавление меток пользователям
- **Стандартный компонент keyboard** (стандартный компонент для межплатформенной взаимодействия): {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} автоматически преобразуется в buttons Yunhu; модификаторы .Buttons(rows) / .Keyboard(rows) принимают универсальную структуру (оригинальная структура обратная совместимость)
- **Стандартные поля для обратных вызовов взаимодействия**: события кнопки/взаимодействие A2UI включают стандартные поля interaction_id / button_data
- **Принадлежность задачи spawn_background**: задачи WS-соединения используют `runtime.spawn_background`
- **Мягкая зависимость фреймворка**: в runtime проверяется ErisPulse>=2.7.1 и выводится предупреждение; при запуске выводится лог версии

### Платформенные расширенные действия (call / Api методы)

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Api методы (официальный API сервера)
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
        data = event["button_data"]     # Единый способ получения для межплатформенной совместимости
        interaction_id = event["interaction_id"]
```

> Полное описание стандарта см. в [Стандарте межплатформенной взаимодействующей компоненты](../standards/standardization-guide.md).

## Стандартизация (4.6.2)

В этом релизе адаптер завершил стандартизацию, структура ответа и коды ошибок соответствуют [Спецификации API-ответа](../standards/api-response.md).

### Замкнутый цикл аккаунтов и многоаккаунтность

- **Внедрение `self.account_id` в события** (внутреннее имя аккаунта): полученные события `self` объекта содержат имя аккаунта, которое породило событие, `event.reply()` автоматически маршрутизируется на **аккаунт, обработавший событие**, для сценариев с несколькими аккаунтами больше не нужно вручную использовать `Using(bot_id)`
- **Двухсовместимые поля `call_api`**: `account_id` (стандартное имя) / `_account_id` (старое имя) могут указывать аккаунт, фреймворк ApiDSL (`Api.Using(...)`) автоматически адаптируется
- **`Send` читает `send_context`** (аккаунт события в качестве резервного): при вызове `Send` в контексте обработки события по умолчанию используется исходный аккаунт

### Стандартные коды ошибок

| retcode | Meaning | Description |
|---------|---------|-------------|
| 0 | Успех | — |
| 33001 | Сетевая ошибка | Ошибка подключения к серверу Yunhu и другие сетевые исключения |
| 34100 | Ошибка платформы | Yunhu возвращает ошибку; оригинальный ответ сохраняется в `yunhu_raw` |
| 10002 | Не поддерживается | Ресурс не существует (бот/пользователь/группа не существует) или платформа не поддерживает стандартное действие |
| 10003 | Ошибка параметров | Отсутствуют или недопустимые параметры |

> **Изменения в 4.6.2**: адаптер дополнил `_platform`, `make_response` автоматически включает `yunhu_raw`, ошибка платформы возвращает `34100`; "бот/пользователь/группа не существует" из `34001` изменено на `10002` (ресурс не существует).

### Структура ответа

Нестандартные поля верхнего уровня `self` перемещены в `data.self_info` (содержит bot_id), в верхнем уровне оставлены только стандартные поля и `yunhu_raw`:

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

### Неизвестные события больше не игнорируются

Непризнанные события Yunhu теперь генерируют событие `type="unknown"` (с `detail_type` как тип оригинального события, оригинальные данные сохраняются в `yunhu_raw`) и выводят предупреждающий лог, модуль может использовать это для отслеживания необработанных типов событий.

### Согласование платформенных расширенных методов

Исторические платформенные расширенные методы (`edit_message` / `batch_send` / `set_user_board` / `gag_group_member` / `create_group_tag` и т.д.) продолжают оставаться доступными; **новые платформенные расширения следует вызывать через `Api.call("yunhu.xxx", **params)`** (см. раздел «Платформенные расширенные действия» ниже).

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочечную синтаксическую конструкцию, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)` — отправка текстового сообщения.
- `.Html(html: str)` — отправка HTML-форматированного сообщения. `.HTML(html)` — псевдоним (для согласования с именем стандартного Send метода).
- `.Markdown(markdown: str)` — отправка Markdown-форматированного сообщения.
- `.MergeForward(nodes, title="Объединённая переписка")` — отправка объединённого пересланного сообщения (отображается как HTML-карточка с деталями, отправляется через html-канал).
- `.A2UI(text: str)` — отправка сообщения в формате A2UI.
- `.Image(file: bytes, stream: bool = False, filename: str = None)` — отправка изображения, поддержка потоковой загрузки и пользовательского имени файла.
- `.Video(file: bytes, stream: bool = False, filename: str = None)` — отправка видео, поддержка потоковой загрузки и пользовательского имени файла.
- `.File(file: bytes, stream: bool = False, filename: str = None)` — отправка файла, поддержка потоковой загрузки и пользовательского имени файла.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)` — массовая отправка сообщений.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)` — редактирование уже отправленного сообщения.
- `.Recall(msg_id: str)` — удаление сообщения.
- `.Board(content: str, content_type: str = "text")` — публикация объявления. Область действия определяется с помощью `To()` (указанный цели = локальная панель, не указано = глобальная панель). Цепочка модификаторов: `.Expire(duration)` относительное время истечения (секунды), `.ExpireAt(timestamp)` абсолютное время истечения (секундные временные метки), `.ForMember(member_id)` панель для участника группы; **если содержимое пустое, автоматически удаляется панель**. По-прежнему поддерживается старый стиль `Board("local", "объявление")`.
- `.DismissBoard()` — удаление объявления. Область действия также определяется с помощью `To()`, поддерживается `.ForMember(member_id)`; по-прежнему поддерживается старый стиль `DismissBoard("local")`.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)` — отправка потокового сообщения.

### Методы управления группами

Все методы управления группами требуют цепочечной синтаксической конструкции для указания группы, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)` — удаление участника группы. Бот должен иметь права "Разрешить удаление участников группы".
- `.Ban(user_id: str, duration: int = 600)` — запрет пользователя. `duration` — продолжительность запрета (в секундах), 0 — отмена запрета, -1 — пожизненный запрет. Бот должен иметь права "Разрешить запрет пользователей".
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)` — создание метки группы. `color` в формате #RRGGBB, `sort` — чем меньше, тем выше метка. Бот должен иметь права "Разрешить управление группой тегов".
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)` — изменение метки группы. Все параметры необязательны, если не переданы, не изменяются. Бот должен иметь права "Разрешить управление группой тегов".
- `.DeleteTag(tag: str)` — удаление метки группы. Бот должен иметь права "Разрешить управление группой тегов".
- `.GetTagList()` — получение списка меток группы. Возвращается ответ с массивом `list`.
- `.AddUserTag(user_id: str, tag: str)` — добавление метки пользователю. Бот должен иметь права "Разрешить управление группой тегов".
- `.RemoveUserTag(user_id: str, tag: str)` — удаление метки у пользователя. Бот должен иметь права "Разрешить управление группой тегов".
- `.SetMsgTypeLimit(types: str)` — ограничение типов сообщений в группе. `types` — имена типов сообщений, разделённые запятыми (например, "text,image,video"), пустая строка означает неограниченный тип. Бот должен иметь права "Разрешить изменение информации о группе".

### Методы получения сообщений

Получение истории сообщений в указанном диалоге (пользователь/группа), требует цепочечной синтаксической конструкции для указания цели, например:
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)` — получение истории сообщений. Возвращается ответ с массивом `list` и общим количеством `total`.
  - `message_id` — идентификатор сообщения (необязательно). Если не указан, в сочетании с `before` возвращает последние N сообщений.
  - `before` — возвращает N сообщений до указанного идентификатора сообщения.
  - `after` — возвращает N сообщений после указанного идентификатора сообщения.
  - > **Внимание:** `before` и `after` должны быть указаны хотя бы один и больше 0, иначе сервер не вернёт никаких сообщений.

Область действия панели определяется с помощью `To()`:
- Указание `To(target_type, target_id)` → локальная панель (указанный пользователь/группа)
- Не указание `To()` → глобальная панель

```python
# Локальная панель (истекает через 60 секунд)
await yunhu.Send.To("group", group_id).Expire(60).Board("Объявление", content_type="markdown")

# Панель для участника группы (видна только указанному участнику)
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("Только для вас")

# Абсолютное время истечения
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("Объявление с указанным временем истечения")

# Глобальная панель
await yunhu.Send.Board("Глобальное объявление")

# Очистка локальной панели (содержимое пустое → автоматически удаляется)
await yunhu.Send.To("group", group_id).Board("")
```

### Параметры кнопок

Параметр `buttons` представляет собой вложенный список, описывающий макет и функциональность кнопок. Каждый объект кнопки содержит следующие поля:

| Параметр         | Тип   | Обязательно | Описание                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | Да       | Текст на кнопке                                                         |
| `actionType` | int    | Да       | Тип действия：<br>`1`: переход по URL<br>`2`: копирование<br>`3`: отправка события            |
| `url`        | string | Нет       | Используется, когда `actionType=1`, указывает целевой URL для перехода                         |
| `value`      | string | Нет       | Когда `actionType=2`, это значение будет скопировано в буфер обмена<br>Когда `actionType=3`, это значение будет отправлено подписчику |

Пример:
```python
buttons = [
    [
        {"text": "Копировать", "actionType": 2, "value": "xxxx"},
        {"text": "Перейти", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Отправить событие", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("Сообщение с кнопками")
```
> **Внимание:**
> - Только пользователь, нажавший кнопку **отправки события**, получит уведомление; **копирование** и **переход по URL** не могут получить уведомление.

### Цепочечные модификаторы (можно комбинировать)

Цепочечные модификаторы возвращают `self` и поддерживают цепочечное использование, должны вызываться перед окончательным методом отправки:

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

# Удаление участника группы
await yunhu.Send.To("group", group_id).Kick(user_id)

# Запрет пользователя (10 минут)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Отмена запрета
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Пожизненный запрет
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Создание метки группы
await yunhu.Send.To("group", group_id).CreateTag("VIP-пользователь", color="#FF5733", desc="VIP-член")

# Изменение метки группы
await yunhu.Send.To("group", group_id).EditTag("VIP-пользователь", new_tag="SVIP-пользователь", color="#33C4FF")

# Удаление метки группы
await yunhu.Send.To("group", group_id).DeleteTag("VIP-пользователь")

# Получение списка меток группы
result = await yunhu.Send.To("group", group_id).GetTagList()

# Добавление метки пользователю
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP-пользователь")

# Удаление метки у пользователя
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP-пользователь")

# Ограничение типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Отмена ограничения типов сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### Примеры получения сообщений

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Получение последних 10 сообщений в группе (всего возвращается 10)
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# Получение 10 сообщений до указанного идентификатора сообщения (всего возвращается 11)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# Получение по 10 сообщений до и после указанного идентификатора сообщения (всего возвращается 21)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Получение истории сообщений в диалоге с пользователем
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### Поддержка OneBot12 сообщений

Адаптер поддерживает отправку OneBot12 форматированных сообщений, что облегчает межплатформенную совместимость:

- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка OneBot12 форматированного сообщения.

```python
# Отправка OneBot12 форматированного сообщения
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# В сочетании с цепочечными модификаторами
ob12_msg = [{"type": "text", "data": {"text": "Ответное сообщение"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Стандартные API действия (ApiDSL)

> [!NOTE]
> Эта функция требует ErisPulse **2.7.0+** и YunhuAdapter **4.3.0+**.

Помимо `Send` цепочечной отправки, адаптер предоставляет внутренний класс `Api`, который выставляет стандартные API действия OneBot12 и расширенные действия платформы Yunhu. Все методы возвращают стандартный формат ответа.

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

# Удаление сообщения (требуется дополнительное указание chat_id + chat_type)
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# Многоаккаунтность: указание аккаунта бота
info = await yunhu.Api.Using("bot1").get_self_info()
```

### Поддерживаемые стандартные действия

| Метод | Описание | Источник данных |
|------|------|---------|
| `get_self_info()` | Информация о самом боте | Открытый Web API (bot-info) |
| `get_user_info(user_id)` | Информация о пользователе (любой пользователь может запросить) | Открытый Web API (user/homepage) |
| `get_group_info(group_id)` | Информация о группе | Открытый Web API (group-info) |
| `upload_file(*, type, name, ...)` | Загрузка файла (автоматически определяет image/video/file) | Bot открытый API |
| `get_file(file_id)` | Получение файла (file_id — это URL, автоматически передаётся Referer и возвращается base64) | Прокси-загрузка |
| `delete_message(message_id, *, chat_id, chat_type)` | Удаление сообщения | Bot открытый API (/bot/recall) |

#### Медиа сообщения и защита от кражи (4.6.3)

CDN медиа Yunhu (`chat-img.jwznb.com` и др.) включает **защиту от кражи через Referer**: прямой `GET` всегда возвращает `403`, необходимо передавать `Referer: https://im.jwzhd.com/`.

- При получении медиа сообщения (image/video/file) в событии медиа-сегмент `data.headers.Referer` уже содержит это значение; модули, загружающие самостоятельно, должны передавать этот заголовок
- Или использовать `call_api("get_file", file_id=<url>)`, адаптер прокси-загрузит и вернёт base64 (автоматически обрабатывает защиту от кражи)

```python
seg = event["message"][0]          # {"type": "image", "data": {...}}
img = await bot.call_api("get_file", file_id=seg["data"]["url"])
raw_bytes = base64.b64decode(img["data"]["base64"])
```

> **Внимание**: `get_self_info` / `get_user_info` / `get_group_info` реализованы через **неофициальные открытые Web API** (chat-web-go.jwzhd.com), эти интерфейсы не требуют аутентификации, но не документированы официально и могут изменяться вместе с платформой; при сбое возвращается стандартный ответ об ошибке.

### Неподдерживаемые стандартные действия

Следующие стандартные действия отсутствуют в Yunhu, при вызове возвращается `retcode=10002` (не поддерживаемое действие):
- `get_friend_list` (бот-открытый API "список пользователей бота" находится в ожидании выхода)
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### Платформенные расширенные действия

Платформенные расширенные действия Yunhu вызываются через `Api.call("yunhu.xxx", **params)` (параметры используют стиль именования OB12, адаптер автоматически переводит в поля Yunhu):

| Расширенное действие | Описание | Эквивалентный Send метод |
|---------|------|---------------|
| `yunhu.recall` | Удаление сообщения (msg_id, chat_id, chat_type) | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | Удаление участника группы (group_id, user_id) | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | Запрет (group_id, user_id, duration) | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | Отмена запрета (group_id, user_id) | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | CRUD-операции с метками группы (group_id, ...) | `Send.To("group", g).CreateTag(...)` и т.д. |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | Добавление/удаление метки у пользователя | `Send.To("group", g).AddUserTag(...)` и т.д. |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **Синоним семантики титула участника** (метка ≈ титул, внутреннее отображение на tag.relate) | — |
| `yunhu.msg_type_limit` | Ограничение типов сообщений в группе (group_id, type) | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | Получение истории сообщений (chat_id, chat_type, message_id?, before?, after?) | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | Открытый запрос bot-info (bot_id) | — |
| `yunhu.user_homepage` | Открытый запрос пользовательской страницы (user_id) | — |

```python
# Пример платформенного расширения
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **Метки и титулы**: "Метка" в Yunhu семантически эквивалентна OneBot12 титулу участника группы (`title`). `yunhu.set_member_title` является синонимом семантического названия `yunhu.tag.relate`, оба внутренне отображаются на один и тот же конечный пункт. В событиях сообщений роль отправителя `senderUserLevel` отображается на стандартное поле `role` (owner/admin/member).

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно ожидать для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату ответа адаптера ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа (self_info содержит bot_id, см. раздел «Структура ответа»)
    "message_id": "123456",   // Идентификатор сообщения
    "message": "",            // Сообщение об ошибке
    "yunhu_raw": {...}        // Оригинальные данные ответа
}
```

> **Изменения в 4.6.2**: Нестандартное поле `self` верхнего уровня в ответе перемещено в `data.self_info`. Для получения bot_id используйте `result["data"]["self_info"]["user_id"]`.

## Специфические типы событий

Необходимо проверять `platform=="yunhu"`, чтобы использовать функции этой платформы

### Основные различия

1. Специфические типы событий:
    - Формы (например, команды формы): yunhu_form
    - Сегменты эмоций/стикеров: yunhu_expression
    - Нажатие кнопки: yunhu_button_click
    - Нажатие кнопки A2UI: yunhu_a2ui_button
    - Настройка бота: yunhu_bot_setting
    - Быстрое меню: yunhu_shortcut_menu
2. Расширение стандартных полей (4.3.0+):
    - В событиях сообщений добавлено стандартное поле `role` (отображается из `senderUserLevel` Yunhu в `owner`/`admin`/`member`)
    - Добавлено поле `user_avatar` (URL аватара отправителя)
3. Расширенные поля:
    - Все специфические поля имеют префикс `yunhu_`
    - Оригинальные данные сохраняются в поле `yunhu_raw`
    - В личных сообщениях `self.user_id` обозначает ID бота

### Примеры специальных полей

```python
# Команда формы
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "Имя команды формы",
    "id": "ID команды",
    "form": {
      "ID поля 1": {
        "id": "ID поля 1",
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
    "interaction_json": "Строка JSON с данными взаимодействия"
  }
}

### Пример обработки события нажатия кнопки

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Обработка уведомлений Yunhu

    Используйте универсальный декоратор on_notice() для обработки всех уведомлений,
    затем различайте типы уведомлений с помощью detail_type
    event.reply() автоматически ответит через платформу Yunhu
    """

# Проверка, является ли событие нажатием кнопки
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"Пользователь {user_nickname}({user_id}) нажал кнопку: {button_value}")

# Использование event.reply() для автоматического ответа (будет выбран правильный способ отправки в зависимости от платформы)
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

# Отправка сообщения с кнопками в группу
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Пожалуйста, подтвердите следующую операцию")

# Отправка сообщения с кнопками в личный чат
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Пожалуйста, выберите настройки предпочтений")
```

### Отправка A2UI сообщения

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# Отправка A2UI сообщения
await yunhu.Send.To("user", user_id).A2UI("Содержание карточки A2UI")
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

Адаптер зарегистрировал следующие платформенные методы, доступные только при `platform == "yunhu"`:

| Метод | Возвращаемый тип | Описание |
|------|----------|------|
| `get_raw_event()` | `dict` | Получить оригинальные данные события Yunhu (в `yunhu_raw`) |
| `get_sender_level()` | `str` | Уровень отправителя в Yunhu (owner/administrator/member/unknown) |
| `get_sender_role()` | `str` | Роль отправителя в OneBot12 стандарте (owner/admin/member) |
| `get_sender_title()` | `str` | Титул отправителя (доступ к стандартному полю `title`, зарезервирован) |
| `get_sender_avatar()` | `str` | URL аватара отправителя |
| `get_command()` | `dict` | Данные команды (только для событий команды, `yunhu_command`) |
| `get_button_value()` | `str` | Значение кнопки в событии нажатия кнопки (`yunhu_button.value`) |
| `get_a2ui_action()` | `str` | Название действия кнопки A2UI (`actionName`) |
| `get_a2ui_form_context()` | `dict` | Контекст формы кнопки A2UI (`form_context`) |
| `get_menu_id()` | `str` | ID события быстрого меню (`yunhu_menu.id`) |
| `get_setting()` | `dict` | Данные настроек события изменения настроек (`yunhu_setting`) |
| `is_command_message()` | `bool` | Является ли сообщение командой |
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
        await event.reply(f"Вы нажали кнопку: {value}")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()
```

## Объяснение расширенных полей

- Все специфические поля имеют префикс `yunhu_`, чтобы избежать конфликтов с стандартными полями
- Оригинальные данные сохраняются в поле `yunhu_raw`, для доступа к полной оригинальной информации платформы Yunhu
- `self.user_id` обозначает ID бота (получается из bot_id в конфигурации)
- Команды формы предоставляются в структурированных данных через `yunhu_command`
- События нажатия кнопки предоставляются через `yunhu_button`
- События кнопки A2UI предоставляются через `yunhu_a2ui`
- Изменения настроек бота предоставляются через `yunhu_setting`
- Операции быстрого меню предоставляются через `yunhu_menu`
- Сегменты эмоций/стикеров предоставляются через `yunhu_expression` (sticker_id, ID пакета стикеров, размер изображения и т.д.)

### Сегмент эмоций/стикеров (yunhu_expression)

Когда пользователь отправляет эмоцию или стикер, тип сегмента сообщения — `yunhu_expression`:

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
| `expression_id` | string | ID эмоции |
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
                print(f"Получена эмоция: sticker_id={data['sticker_id']}, ID пакета={data['sticker_pack_id']}")
```

---

## Конфигурация Multi-Bot

### Описание конфигурации

Адаптер Yunhu поддерживает одновременную конфигурацию и запуск нескольких аккаунтов ботов Yunhu.

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # API токен бота (обязательно)
mode = "ws"  # Режим приема (опционально, по умолчанию "ws", возможные значения: "ws", "webhook")
webhook_path = "/webhook/bot1"  # Путь для вебхука (опционально, по умолчанию "/webhook")
enabled = true  # Включен ли аккаунт (опционально, по умолчанию true)

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # Токен второго бота
webhook_path = "/webhook/bot2"  # Отдельный путь для вебхука
enabled = true
```

**Описание параметров конфигурации:**
- `token`: API токен, предоставленный платформой Yunhu (обязательно)
- `mode`: Режим приема (опционально, по умолчанию `"ws"`, возможные значения `"ws"`, `"webhook"`)
- `webhook_path`: HTTP путь для получения событий Yunhu (опционально, по умолчанию "/webhook", используется только в режиме webhook)
- `enabled`: Включен ли этот аккаунт (опционально, по умолчанию true)

**Важные замечания:**
1. ID бота платформы Yunhu определяется **во время выполнения**, не нужно указывать в конфигурации
2. В режиме webhook каждый бот должен иметь отдельный `webhook_path`, чтобы получать свои собственные события webhook
3. При настройке webhook на платформе Yunhu, для каждого бота нужно настроить соответствующий URL, например:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Использование Send DSL для указания бота

Можно использовать метод `Using()` для указания, с какого бота отправлять сообщение. Этот метод поддерживает два параметра:
- **Имя аккаунта**: имя бота в конфигурации (например, `bot1`, `bot2`)
- **bot_id**: значение `bot_id` в конфигурации

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Отправка сообщения с использованием имени аккаунта
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# Отправка сообщения с использованием bot_id (система автоматически найдёт соответствующий аккаунт)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# Без указания аккаунта используется первый включённый бот
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **Примечание:** При использовании `bot_id` система автоматически ищет соответствующий аккаунт в конфигурации. Это особенно полезно при обработке событий, где можно использовать `event["self"]["user_id"]` для ответа того же аккаунта.

### ID бота в событиях

Полученные события автоматически содержат информацию об ID бота (начиная с 4.6.2 также вставляется внутреннее имя аккаунта `self.account_id`):

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Получить ID бота, который породил событие
        bot_id = event["self"]["user_id"]
        account_id = event["self"].get("account_id", "")  # Внутреннее имя аккаунта (например, bot1)
        print(f"Сообщение пришло от бота: {bot_id} (аккаунт: {account_id})")

        # Начиная с 4.6.2 event.reply() автоматически маршрутизируется на обработанный аккаунт, можно просто ответить
        await event.reply("Ответное сообщение")

        # Также можно явно указать аккаунт для отправки
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответное сообщение")
```

> **Примечание:** `call_api` поддерживает двойное совместимое поле аккаунта: `account_id` (стандартное имя) и `_account_id` (старое имя), фреймворк ApiDSL `Using()` и аккаунт контекста отправки (`send_context`) автоматически адаптируются.

### Логи

Адаптер автоматически включает информацию об ID бота в логи, что облегчает отладку и отслеживание:

```
[INFO] [yunhu] [bot:30535459] Получено личное сообщение от пользователя user123
[INFO] [yunhu] [bot:12345678] Сообщение успешно отправлено, message_id: abc123
```

### Интерфейсы управления

```python
# Получить информацию обо всех ботах
bots = yunhu.bots

# Проверить состояние аккаунта
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# Динамически включить/отключить аккаунт (требуется перезапуск адаптера)
yunhu.bots["bot1"].enabled = False
```

### Совместимость старой конфигурации

Старая конфигурация `[Yunhu_Adapter.bots.*]` (с полем `bot_id`) автоматически мигрируется в формат `accounts` (`bot_id` теперь определяется автоматически во время выполнения, значение в конфигурации игнорируется); рекомендуется как можно скорее перейти на новый формат.