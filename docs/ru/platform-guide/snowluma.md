# Документация по функциям платформы SnowLuma

SnowLumaAdapter — это адаптер, построенный на основе SnowLuma-бэкенда (NTQQ hook), использующий протокол OneBot v11 для связи.

---

## Информация о документации

- Версия соответствующего модуля: 0.1.0
- Поддержка: ErisPulse

## Основная информация

- Краткое описание платформы: SnowLuma — это реализация протокола QQ на основе NTQQ hook, API полностью совместим с NapCat, предоставляет доступ через протокол OneBot v11 (порт по умолчанию: HTTP 3000, WS 3001)
- Название адаптера: SnowLumaAdapter
- Поддерживаемые протоколы/API: OneBot V11 (с расширениями SnowLuma, полная совместимость с NapCat, можно подключаться напрямую к бэкенду NapCat)
- Поддержка нескольких аккаунтов: по умолчанию используется архитектура с несколькими аккаунтами, позволяет одновременно настраивать и запускать несколько аккаунтов
- Ключ конфигурации: `SnowLuma_Adapter`

### Отношение к адаптеру OneBot11

SnowLuma использует протокол OB11, стандартные действия и события преобразуются идентично адаптеру OneBot11 (имена стандартных действий OB12 автоматически мапятся).
Основные различия:

1. **Режим client по умолчанию**: активное подключение к SnowLuma WS (`ws://127.0.0.1:3001`), не требуется публичное прослушивание
2. **Автоматическое определение bot_id**: не требуется указывать номер QQ в конфигурации аккаунта, после запуска адаптера автоматически определяется и поддерживается отображение `self_id → account_name`
3. **109 расширенных действий**: пощёчина, QQ-пространство, файлы/альбомы групп, история сообщений, закрепление, статус прочитанности и другие расширения SnowLuma/NapCat
4. **Расширенная цепочка объединённых пересылок**: специальный эндпоинт + `upload_forward_msg` (загрузка узлов по resid) + `get_forward_msg` (разбор содержимого) с трёхуровневой обратной совместимостью

---

## Стандартные API-действия (DSL)

Адаптер автоматически мапит стандартные имена действий OB12 в OB11, модуль может использовать единый интерфейс для всех платформ:

| Стандартное действие OB12 | Действие OB11 | Описание |
|---------------------------|---------------|----------|
| get_self_info             | get_login_info | Стандартизированные поля user_id/user_name/user_displayname |
| get_user_info             | get_stranger_info | Стандартизированные поля |
| delete_message            | delete_msg     | Отмена сообщения |
| leave_group               | set_group_leave | Выйти из группы |
| upload_file               | upload_group_file / upload_private_file | Дополнительные параметры group_id/user_id (необязательно) |

### Основное использование

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# Получить информацию о боте
result = await snowluma.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# Отменить сообщение
await snowluma.Api.delete_message(message_id=123456)

# Указать аккаунт (множественные аккаунты)
result = await snowluma.Api.Using("main").get_self_info()

# Расширенные действия через call() (универсальные для SnowLuma/NapCat)
result = await snowluma.Api.call("send_poke", group_id=123, user_id=456)
```

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# Отправить с использованием аккаунта по умолчанию
await snowluma.Send.To("group", group_id).Text("Hello World!")

# Отправить с указанием конкретного аккаунта
await snowluma.Send.Using("main").To("group", group_id).Text("Сообщение с основного аккаунта")

# Цепочка модификаторов: @пользователь + ответ
await snowluma.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Ответное сообщение")
```

### Основные методы отправки

- `.Text(text: str)` — отправить текстовое сообщение.
- `.Image(file: Union[str, bytes], filename: str = "image.png")` — отправить изображение (поддержка URL, Base64 или bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")` — отправить голосовое сообщение.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` — отправить видео.
- `.Face(id: Union[str, int])` — отправить эмодзи QQ.
- `.File(file: Union[str, bytes], filename: str = "file.dat")` — отправить файл.
- `.MergeForward(nodes, title="Объединённая пересылка")` — отправить объединённую пересылку (см. раздел ниже).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправить сообщение в формате OneBot12 (автоматически преобразуется в OB11; чистый список node-сегментов автоматически маршрутизируется в объединённую пересылку).
- `.Recall(message_id: Union[str, int])` — отменить сообщение.

### Объединённая пересылка

```python
nodes = [
    {
        "type": "node",
        "data": {
            "user_id": "10000",
            "nickname": "MyBot",
            "content": [{"type": "text", "data": {"text": "【1/3】Заголовок\nТекст…"}}],
        },
    },
]

# Отправить объединённую пересылку (трёхуровневая обратная совместимость, работает с бэкендами SnowLuma и NapCat):
# ① send_group/private_forward_msg специальный эндпоинт (оригинальный NapCat, совместимый SnowLuma)
# ② upload_forward_msg загрузка по resid → send_msg отправка forward-сегмента (расширенная цепочка SnowLuma)
# ③ send_msg прямая отправка node-сегмента
await snowluma.Send.To("group", group_id).MergeForward(nodes)

# Разбор полученного объединённого сообщения (входящие forward-сегменты передаются как onebot11_forward, data.id — это resid)
result = await snowluma.Api.get_forward_msg(id="resid_xxx")
```

### Методы управления группой

Все методы должны быть вызваны с помощью `To("group", group_id)` для указания целевой группы:

- `.Kick(user_id, reject_add_request=False)` — исключить участника из группы.
- `.Ban(user_id, duration=1800)` — временно заблокировать участника (в секундах), 0 означает разблокировку.
- `.WholeBan(enable=True)` — включить/отключить общую блокировку.
- `.SetAdmin(user_id, enable=True)` — назначить/снять администратора.
- `.SetCard(user_id, card="")` — установить имя участника в группе.
- `.SetGroupName(name)` — изменить название группы.
- `.Leave(is_dismiss=False)` — выйти из группы (владелец может распустить).
- `.SetTitle(user_id, title="")` — установить титул участника.
- `.SetPortrait(file)` — установить аватарку группы.

### Пощёчина / социальные действия

- `.GroupPoke(user_id)` — пощёчина в группе (требуется `To("group", group_id)`).
- `.FriendPoke(user_id)` — пощёчина другу.
- `.SendPoke(user_id)` — отправить пощёчина (универсально).
- `.SetMsgEmojiLike(message_id, emoji_id)` — реакция на сообщение с помощью эмодзи.

### QQ-пространство

- `.QzoneMsg(content)` — опубликовать пост в QQ-пространстве.
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)` — поставить/удалить лайк.
- `.QzoneComment(tid, content)` — оставить комментарий.
- `.QzoneDelete(tid)` — удалить пост.

### Файлы групп / история сообщений / статус прочитанности

- `.UploadGroupFile(file, name)` — загрузить файл в группу (требуется `To("group", group_id)`).
- `.GetGroupFileUrl(file_id)` — получить ссылку на скачивание файла.
- `.GetGroupMsgHistory(message_seq=0, count=20)` — получить историю сообщений в группе.
- `.GetFriendMsgHistory(user_id, count=20)` — получить историю сообщений с другом.
- `.MarkMsgAsRead()` — отметить текущий чат как прочитанный.
- `.SetOnlineStatus(status)` — установить статус онлайн.

### Методы цепочки модификаторов (можно комбинировать)

- `.At(user_id: Union[str, int])` — упомянуть пользователя (можно вызывать несколько раз).
- `.AtAll()` — упомянуть всех участников.
- `.Reply(message_id: Union[str, int])` — ответить на сообщение.

---

## Расширенные действия OB11 (DSL)

Помимо стандартных действий, `OB11ExtensionApi` предоставляет более 60 типизированных расширенных методов, все 109 расширенных действий можно вызвать через `Api.call("action_name", ...)` (универсально для SnowLuma/NapCat). Краткий обзор групп:

| Группа | Пример действия |
|--------|-----------------|
| Пощёчина / социальные | send_poke / group_poke / friend_poke / send_like |
| Ответы на сообщения / закрепление | set_msg_emoji_like / get_emoji_likes / set_essence_msg / get_essence_msg_list |
| Прочитанность / статус | mark_msg_as_read / mark_group_msg_as_read / mark_all_as_read / set_online_status / set_input_status |
| История сообщений | get_group_msg_history / get_friend_msg_history |
| Расширенное управление группой | set_group_reaction / set_group_remark / set_group_sign / set_group_todo / get_group_info_ex / get_group_shut_list / get_group_at_all_remain |
| Друзья / контакты | set_friend_remark / get_unidirectional_friend_list / get_friends_with_category / get_recent_contact |
| Файлы групп | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file |
| Альбомы групп | get_group_album_list / get_group_album_media_list |
| QQ-пространство | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds |
| Объединённая пересылка | get_forward_msg / upload_forward_msg |
| Медиа / OCR | ocr_image / get_image |

---

## Сопоставление типов событий

### Стандартное сопоставление OB12

| Оригинальный тип OB11 | Преобразованный detail_type | Описание |
|------------------------|-----------------------------|----------|
| message_type: private  | `private`                   | Личное сообщение |
| message_type: group    | `group`                     | Групповое сообщение |
| notice_type: group_upload | `group_file_upload`      | Загрузка файла в группу |
| notice_type: group_admin | `group_admin_change`     | Изменение администратора |
| notice_type: group_increase | `group_member_increase` | Увеличение участников |
| notice_type: group_decrease | `group_member_decrease` | Уменьшение участников |
| notice_type: group_ban   | `group_ban`               | Запрет в группе |
| notice_type: friend_add  | `friend_increase`         | Добавление друга |
| notice_type: friend_delete | `friend_decrease`       | Удаление друга |
| notice_type: group_recall / friend_recall | `message_recall` | Отмена сообщения |

### Платформо-специфические события и расширенные сегменты

- Платформо-специфические события (poke/honor и др.) используют detail_type с префиксом `snowluma_`
- Неизвестные CQ-коды передаются с префиксом `onebot11_{type}` (протокольный уровень)
- Входящие объединённые сообщения передаются как `onebot11_forward` (data.id — это resid, можно использовать `Api.get_forward_msg(id=...)` для разбора содержимого)

### Описание расширенных полей

- Все специфические поля имеют префикс `snowluma_`
- Сохранённые оригинальные данные события находятся в поле `snowluma_raw`
- Сохранённый оригинальный тип события находится в поле `snowluma_raw_type`

---

## Расширенные методы событий

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

| Метод | Тип возвращаемого значения | Описание |
|-------|-----------------------------|----------|
| `get_raw_event()` | `dict` | Получить полные исходные данные события SnowLuma |
| `get_raw_self_id()` | `str` | Получить исходный self_id (номер QQ бота) |
| `get_sender_info()` | `dict` | Получить полную информацию о отправителе (включая nickname, role, level и др.) |
| `get_sender_role()` | `str` | Получить роль отправителя в группе (owner/admin/member) |
| `get_sender_level()` | `int` | Получить уровень отправителя |
| `get_sender_title()` | `str` | Получить титул отправителя в группе |
| `is_system_message()` | `bool` | Определить, является ли сообщение системным |

---

## Параметры конфигурации

Адаптер SnowLuma использует архитектуру с несколькими аккаунтами, каждый аккаунт имеет отдельную конфигурацию. Ключ конфигурации: `SnowLuma_Adapter`.

### Поля конфигурации аккаунта

| Поле | Тип | Обязательно | Значение по умолчанию | Описание |
|------|-----|-------------|-----------------------|----------|
| `mode` | `str` | Нет | `"client"` | Режим работы: `"client"` (активное подключение, рекомендуется) или `"server"` (пассивное прослушивание) |
| `url` | `str` | Нет | `"ws://127.0.0.1:3001"` | Адрес WebSocket в режиме client (порт по умолчанию SnowLuma 3001) |
| `token` | `str` | Нет | `""` | Токен доступа (авторизация Bearer) |
| `server_path` | `str` | Нет | `"/"` | Путь WebSocket в режиме server |
| `enabled` | `bool` | Нет | `true` | Включён ли аккаунт |
| `name` | `str` | Нет | `""` | Заметка аккаунта |

> Номер bot_id (номер QQ) не требуется в конфигурации: адаптер автоматически определяет его и поддерживает отображение `self_id → account_name`, `event.reply()` автоматически маршрутизируется на аккаунт отправителя.

### Пример конфигурации

```toml
[SnowLuma_Adapter.accounts.main]
mode = "client"
url = "ws://127.0.0.1:3001"
token = ""
enabled = true

[SnowLuma_Adapter.accounts.second]
mode = "client"
url = "ws://192.168.1.100:3001"
token = "second_token"
enabled = true
```

---

## Значения возвращаемые методами отправки

Все методы отправки возвращают объект Task, который можно использовать с await для получения результата. Возвращаемый результат соответствует стандартизированной схеме ErisPulse-адаптера:

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "snowluma_raw": {...}
}
```

### Синтаксис отправки с несколькими аккаунтами

```python
# Метод выбора аккаунта
await snowluma.Send.Using("main").To("group", 123456).Text("Сообщение с основного аккаунта")

# Вызов API
await snowluma.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## Автоматическое отображение self_id

Адаптер автоматически устанавливает отображение OneBot `self_id` (номер QQ) в `account_name`, для маршрутизации событий обратно:

```python
@message.on_message()
async def handler(event):
    # Автоматически маршрутизируется на правильный аккаунт
    await event.reply("Автоматически маршрутизируется на аккаунт отправителя")
```