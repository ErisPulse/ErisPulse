# Документация по функциям платформы Yunhu

YunhuAdapter — это адаптер, основанный на протоколе Yunhu, который объединяет все функциональные модули Yunhu, предоставляя унифицированный интерфейс для обработки событий и управления сообщениями.

---

## Информация о документе

- Версия соответствующего модуля: 4.0.0
- Поддерживающий: ErisPulse

## Основная информация

- Описание платформы: Yunhu — это корпоративная платформа мгновенных сообщений
- Имя адаптера: YunhuAdapter
- Поддержка нескольких аккаунтов: Поддержка идентификации и настройки нескольких учетных записей ботов Yunhu через bot_id
- Поддержка цепочки методов: Поддержка методов цепочки, таких как `.Reply()`
- Совместимость с OneBot12: Поддержка отправки сообщений в формате OneBot12

## Поддерживаемые типы отправляемых сообщений

Все методы отправки реализованы с использованием цепочного синтаксиса, например:

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

Поддерживаемые типы отправки включают:
- `.Text(text: str)`: Отправка простого текстового сообщения.
- `.Html(html: str)`: Отправка сообщения в формате HTML.
- `.Markdown(markdown: str)`: Отправка сообщения в формате Markdown.
- `.A2UI(text: str)`: Отправка сообщения в формате A2UI.
- `.Image(file: bytes, stream: bool = False, filename: str = None)`: Отправка сообщения с изображением, поддержка потоковой загрузки и пользовательского имени файла.
- `.Video(file: bytes, stream: bool = False, filename: str = None)`: Отправка сообщения с видео, поддержка потоковой загрузки и пользовательского имени файла.
- `.File(file: bytes, stream: bool = False, filename: str = None)`: Отправка сообщения с файлом, поддержка потоковой загрузки и пользовательского имени файла.
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`: Массовая отправка сообщений.
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`: Редактирование существующего сообщения.
- `.Recall(msg_id: str)`: Отзыв сообщения.
- `.Board(scope: str, content: str, **kwargs)`: Публикация дашборда объявлений, `scope` поддерживает `local` и `global`.
- `.DismissBoard(scope: str, **kwargs)`: Удаление дашборда объявлений.
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`: Отправка потокового сообщения.

### Методы управления группами

Все методы управления группами требуют указания группы через цепочной синтаксис, например:

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`: Удаление участника группы. Боту требуется разрешение `Разрешить удаление участников группы`.
- `.Ban(user_id: str, duration: int = 600)`: Бан пользователя. `duration` — это длительность бана в секундах, 0 для разбана, -1 для вечного бана. Боту требуется разрешение `Разрешить бан пользователей`.
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`: Создание тега группы. `color` должно быть в формате #RRGGBB, `sort` — чем меньше, тем выше приоритет. Боту требуется разрешение `Разрешить управление группами тегов`.
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`: Редактирование тега группы. Все параметры необязательны; если не переданы, изменения не вносятся. Боту требуется разрешение `Разрешить управление группами тегов`.
- `.DeleteTag(tag: str)`: Удаление тега группы. Боту требуется разрешение `Разрешить управление группами тегов`.
- `.GetTagList()`: Получение списка тегов группы. Возвращает ответные данные, содержащие массив `list`.
- `.AddUserTag(user_id: str, tag: str)`: Добавление тега пользователю. Боту требуется разрешение `Разрешить управление группами тегов`.
- `.RemoveUserTag(user_id: str, tag: str)`: Удаление тега у пользователя. Боту требуется разрешение `Разрешить управление группами тегов`.
- `.SetMsgTypeLimit(types: str)`: Управление типами сообщений в группе. `types` — это имя типа сообщения, несколько типов разделены запятыми (например, `"text,image,video"`), пустая строка означает отсутствие ограничений. Боту требуется разрешение `Разрешить изменение информации группы`.

### Методы запроса сообщений

Для получения списка истории сообщений в указанном сеансе (пользователь/группа) необходимо указать цель через цепочный синтаксис, например:

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`: Получение истории сообщений сеанса. Возвращает ответные данные, содержащие массив `list` и общее количество `total`.
  - `message_id`: ID сообщения (необязательно). Если не указано, возвращаются последние N сообщений вместе с `before`.
  - `before`: Возвращает N сообщений перед указанным ID сообщения.
  - `after`: Возвращает N сообщений после указанного ID сообщения.
  - > **Примечание:** `before` или `after` должно быть указано хотя бы одно и больше 0, иначе сервер не вернет никаких сообщений.

Типы дашбордов `Board` поддерживают следующие значения:
- `local`: Пользовательский дашборд
- `global`: Глобальный дашборд

### Описание параметров кнопок

Параметр `buttons` представляет собой вложенный список, обозначающий расположение и функциональность кнопок. Каждый объект кнопки содержит следующие поля:

| Поле         | Тип    | Обязательно | Описание                                                                 |
|--------------|--------|-------------|--------------------------------------------------------------------------|
| `text`       | string | Да          | Текст на кнопке                                                           |
| `actionType` | int    | Да          | Тип действия:<br>`1`: Перенаправление на URL<br>`2`: Копировать<br>`3`: Нажатие для отчета            |
| `url`        | string | Нет         | Используется при `actionType=1`, указывает целевой URL для перенаправления                         |
| `value`      | string | Нет         | При `actionType=2` значение будет скопировано в буфер обмена<br>При `actionType=3` значение будет отправлено в подписчики |

Пример:

```python
buttons = [
    [
        {"text": "Копировать", "actionType": 2, "value": "xxxx"},
        {"text": "Перейти", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "Отправить отчет", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("Сообщение с кнопками")
```
> **Примечание:**
> - Уведомление будут получены только в том случае, если пользователь нажмет на кнопку **Отправить отчет**. **Копирование** и **Перенаправление на URL** уведомлений не вызывают.

### Методы цепочки (можно комбинировать)

Методы цепочки возвращают `self`, поддерживают вызов по цепочке и должны быть вызваны перед окончательным методом отправки:

- `.Reply(message_id: str)`: Ответ на указанное сообщение.
- `.At(user_id: str)`: Упоминание указанного пользователя.
- `.AtAll()`: Упоминание всех пользователей.
- `.Buttons(buttons: List)`: Добавление кнопок.

### Примеры цепочного вызова

```python
# Базовая отправка
await yunhu.Send.To("user", user_id).Text("Hello")

# Ответ на сообщение
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("Ответ на сообщение")

# Ответ + Кнопки
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("Сообщение с ответом и кнопками")
```

### Примеры управления группами

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Удаление участника группы
await yunhu.Send.To("group", group_id).Kick(user_id)

# Бан пользователя (10 минут)
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# Разбан
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# Вечный бан
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# Создание тега группы
await yunhu.Send.To("group", group_id).CreateTag("VIP-пользователь", color="#FF5733", desc="VIP-член")

# Редактирование тега группы
await yunhu.Send.To("group", group_id).EditTag("VIP-пользователь", new_tag="SVIP-пользователь", color="#33C4FF")

# Удаление тега группы
await yunhu.Send.To("group", group_id).DeleteTag("VIP-пользователь")

# Получение списка тегов группы
result = await yunhu.Send.To("group", group_id).GetTagList()

# Добавление тега пользователю
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIP-пользователь")

# Удаление тега у пользователя
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIP-пользователь")

# Установка ограничений на типы сообщений
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# Отмена ограничений на типы сообщений
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

# Получение 10 сообщений до и после указанного ID сообщения в группе (всего возвращается 21 сообщение)
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# Получение истории сообщений сеанса пользователя
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### Поддержка сообщений OneBot12

Адаптер поддерживает отправку сообщений в формате OneBot12 для обеспечения совместимости сообщений между платформами:

- `.Raw_ob12(message: List[Dict], **kwargs)`: Отправка сообщения в формате OneBot12.

```python
# Отправка сообщения в формате OneBot12
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# Совместно с методом цепочки
ob12_msg = [{"type": "text", "data": {"text": "Ответ на сообщение"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## Возвращаемое значение методов отправки

Все методы отправки возвращают объект `Task`, который можно напрямую await для получения результата отправки. Возвращаемые данные соответствуют стандартизированному спецификации возврата адаптеров ErisPulse:

```python
{
    "status": "ok",           // Статус выполнения
    "retcode": 0,             // Код возврата
    "data": {...},            // Данные ответа
    "self": {...},            // Информация о себе (включая bot_id)
    "message_id": "123456",   // ID сообщения
    "message": "",            // Информация об ошибке
    "yunhu_raw": {...}        // Исходные данные ответа
}
```

## Уникальные типы событий

Необходимо проверять `platform=="yunhu"` перед использованием функций этой платформы

### Основные отличия

1. Уникальные типы событий:
    - Формы (например, команды форм): yunhu_form
    - Сегменты сообщений с стикерами/эмоциями: yunhu_expression
    - Нажатие на кнопку: yunhu_button_click
    - Нажатие на кнопку A2UI: yunhu_a2ui_button
    - Настройки бота: yunhu_bot_setting
    - Меню быстрого доступа: yunhu_shortcut_menu
2. Расширенные поля:
    - Все уникальные поля идентифицируются префиксом `yunhu_`
    - Исходные данные сохраняются в поле `yunhu_raw`
    - В личном общении `self.user_id` указывает ID бота

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
      "FieldID1": {
        "id": "FieldID1",
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
  "user_id": "ID пользователя, выполняющего действие",
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

    Используйте общий декоратор on_notice() для обработки всех событий уведомлений,
    затем различайте типы уведомлений через detail_type
    event.reply() автоматически отправляет ответ через платформу Yunhu
    """
    # Проверка, является ли событие нажатием кнопки
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"Пользователь {user_nickname}({user_id}) нажал кнопку: {button_value}")

        # Использование event.reply() для автоматического ответа (выберет правильный метод отправки в зависимости от платформы)
        if button_value == "confirm":
            await event.reply("Вы нажали кнопку подтверждения!")
        elif button_value == "cancel":
            await event.reply("Операция отменена")
        else:
            await event.reply(f"Получен ваш выбор: {button_value}")

    # Обработка события меню быстрого доступа
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"Сработало меню быстрого доступа: {menu_id}")

    # Обработка изменения настроек бота
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"Настройки обновлены: {settings}")

    # Обработка события кнопки A2UI
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"Действие A2UI: {action_name}, Данные формы: {form_context}")
```

### Отправка сообщения с кнопками с помощью цепочного вызова

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "Подтвердить", "actionType": 3, "value": "confirm"},
        {"text": "Отмена", "actionType": 3, "value": "cancel"},
        {"text": "Подробнее", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# Отправка сообщения с кнопками в группу
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("Пожалуйста, подтвердите следующую операцию")

# Отправка сообщения с кнопками в личный чат пользователя
await yunhu.Send.To("user", "789").Buttons(buttons).Text("Пожалуйста, выберите ваши предпочтения")
```

### Отправка сообщения A2UI

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# Отправка сообщения A2UI
await yunhu.Send.To("user", user_id).A2UI("Содержимое карточки взаимодействия A2UI")
```

# Настройки бота
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "ID группы (может быть пустым)",
  "user_nickname": "Никнейм пользователя",
  "yunhu_setting": {
    "ID_настройки": {
      "id": "ID настройки",
      "type": "input/radio/checkbox/select/switch",
      "value": "Значение настройки"
    }
  }
}

# Меню быстрого доступа
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "ID пользователя, инициировавшего меню",
  "user_nickname": "Никнейм пользователя",
  "group_id": "ID группы (если это групповой чат)",
  "yunhu_menu": {
    "id": "ID меню",
    "type": "Тип меню (целое число)",
    "action": "Действие меню (целое число)"
  }
}
```

## Описание расширенных полей

- Все уникальные поля идентифицируются префиксом `yunhu_`, чтобы избежать конфликта со стандартными полями
- Исходные данные сохраняются в поле `yunhu_raw` для удобства доступа к полным исходным данным платформы Yunhu
- `self.user_id` указывает ID бота (получается из bot_id в конфигурации)
- Команды форм предоставляют структурированные данные через поле `yunhu_command`
- События нажатия кнопок предоставляют информацию о кнопках через поле `yunhu_button`
- События кнопки A2UI предоставляют информацию об взаимодействии A2UI через поле `yunhu_a2ui`
- Изменения настроек бота предоставляют данные настроек через поле `yunhu_setting`
- Операции меню быстрого доступа предоставляют информацию о меню через поле `yunhu_menu`
- Сегменты сообщений со стикерами/эмодзи предоставляют данные стикера (sticker_id, ID набора стикеров, размер изображения и т.д.) через сегмент сообщения `yunhu_expression`

### Сегмент сообщения со стикером/эмоцией (yunhu_expression)

Когда пользователь отправляет стикер или эмоцию, типом сегмента сообщения является `yunhu_expression`:

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

| Поле          | Тип    | Описание                        |
|---------------|--------|---------------------------------|
| `sticker_id`  | string | Уникальный идентификатор стикера |
| `sticker_pack_id` | string | ID набора стикеров              |
| `expression_id`   | string | ID эмоции                      |
| `image_name`   | string | Путь к файлу изображения эмоции |
| `width`        | int    | Ширина изображения (необязательно) |
| `height`       | int    | Высота изображения (необязательно) |

Пример использования:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"Получен стикер: sticker_id={data['sticker_id']}, ID набора={data['sticker_pack_id']}")
```

---

## Конфигурация нескольких ботов

### Описание конфигурации

Адаптер Yunhu поддерживает настройку и одновременное выполнение нескольких учетных записей ботов Yunhu.

```toml
# config.toml
[Yunhu_Adapter.bots.bot1]
bot_id = "30535459"  # ID бота (обязательно)
token = "your_bot1_token"  # Токен бота (обязательно)
webhook_path = "/webhook/bot1"  # Путь Webhook (необязательно, по умолчанию "/webhook")
enabled = true  # Включен ли бот (необязательно, по умолчанию true)

[Yunhu_Adapter.bots.bot2]
bot_id = "12345678"  # ID второго бота
token = "your_bot2_token"  # Токен второго бота
webhook_path = "/webhook/bot2"  # Путь Webhook
enabled = true
```

**Описание конфигурации:**
- `bot_id`: Уникальный идентификационный ID бота (обязательно), используется для определения, какой бот инициировал событие
- `token`: API токен, предоставляемый платформой Yunhu (обязательно)
- `webhook_path`: HTTP-путь для получения событий Yunhu (необязательно, по умолчанию "/webhook")
- `enabled`: Включен ли бот (необязательно, по умолчанию true)

**Важные примечания:**
1. В событиях платформы Yunhu нет информации о ID бота, поэтому `bot_id` должно быть явно указано в конфигурации
2. У каждого бота должен быть независимый `webhook_path` для получения своих событий webhook
3. При настройке webhook в платформе Yunhu, пожалуйста, укажите соответствующий URL для каждого бота, например:
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Указание бота с помощью Send DSL

Можно указать, какого бота использовать для отправки сообщения, с помощью метода `Using()`. Этот метод поддерживает два параметра:
- **Имя аккаунта**: Имя бота в конфигурации (например, `bot1`, `bot2`)
- **bot_id**: Значение `bot_id` в конфигурации

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# Отправка сообщения с использованием имени аккаунта
await yunhu.Send.Using("bot1").To("user", "user123").Text("Привет от bot1!")

# Отправка сообщения с использованием bot_id (автоматическое сопоставление с аккаунтом)
await yunhu.Send.Using("30535459").To("group", "group456").Text("Привет от бота!")

# Использование первого включенного бота, если не указан
await yunhu.Send.To("user", "user123").Text("Привет от бота по умолчанию!")
```

> **Примечание:** При использовании `bot_id` система автоматически найдет соответствующий аккаунт в конфигурации. Это особенно полезно при обработке ответов на события, так как можно напрямую использовать `event["self"]["user_id"]` для ответа от того же аккаунта.

### Идентификация бота в событиях

События, полученные адаптером, автоматически содержат соответствующую информацию `bot_id`:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # Получение ID бота, инициировавшего событие
        bot_id = event["self"]["user_id"]
        print(f"Сообщение от бота: {bot_id}")
        
        # Использование того же бота для ответа
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("Ответ сообщения")
```

### Информация в логах

Адаптер автоматически включает информацию `bot_id` в логах для отладки и отслеживания:

```
[INFO] [yunhu] [bot:30535459] Получено личное сообщение от пользователя user123
[INFO] [yunhu] [bot:12345678] Успешная отправка сообщения, message_id: abc123
```

### Управляющий интерфейс

```python
# Получение информации обо всех аккаунтах
bots = yunhu.bots

# Проверка состояния аккаунта
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# Динамическое включение/отключение аккаунта (требует перезапуска адаптера)
yunhu.bots["bot1"].enabled = False
```

### Совместимость со старой конфигурацией

Система автоматически поддерживает старые форматы конфигурации, но рекомендуется перенести на новый формат для лучшей поддержки нескольких ботов.