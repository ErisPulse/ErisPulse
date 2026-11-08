# Документация по функциям платформы SnowLuma

SnowLumaAdapter — это адаптер, построенный на основе бэкенда SnowLuma (NTQQ hook), использующий протокол OneBot v11 для связи.

---

## Информация о документации

- Версия соответствующего модуля: 0.3.0
- Разработчик: ErisPulse

## Основная информация

- Краткое описание платформы: SnowLuma — это реализация протокола QQ на основе NTQQ hook, API полностью совместим с NapCat, предоставляет доступ к службам через протокол OneBot v11 (порт по умолчанию: HTTP 3000, WS 3001)
- Название адаптера: SnowLumaAdapter
- Поддерживаемые версии протокола/API: OneBot V11 (всего 200 действий в стандартной директории, адаптер полностью покрывает; полная совместимость с NapCat, можно напрямую подключаться к бэкенду NapCat)
- Поддержка нескольких аккаунтов: по умолчанию используется архитектура с несколькими аккаунтами, позволяет настроить и запустить несколько аккаунтов одновременно
- Ключ конфигурации: `SnowLuma_Adapter`

### Отношения с адаптером OneBot11

SnowLuma использует протокол OB11, стандартные действия и события преобразуются в идентичную структуру с адаптером OneBot11 (имена стандартных действий OB12 автоматически мапятся).
Основные различия:

1. **Режим по умолчанию client**: активное подключение к SnowLuma WS (`ws://127.0.0.1:3001`), не требуется прослушивание публичного интернета; также поддерживается режим server (обратный WS) / http (API + опрос) / webhook (API + отчет), всего четыре режима
2. **Автоматическое определение bot_id**: нет необходимости указывать номер QQ в конфигурации аккаунта, адаптер автоматически определяет и поддерживает отображение `self_id → account_name` после запуска
3. **Полная реализация 200 действий**: 169 типизированных методов (127 общих расширений + 42 специфических для SnowLuma), остальные — прямой вызов Core / ApiDSL прозрачный / псевдонимы сервера, полное соответствие см. в репозитории адаптера [docs/api-coverage.md](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md)
4. **Цепочка расширения для объединения сообщений**: специальный конечный путь + `upload_forward_msg` (получение resid из узла) + `get_forward_msg` (разбор содержимого пересылки) с тремя уровнями возврата

---

## Стандартные действия API (Api DSL)

Адаптер автоматически мапит стандартные действия OB12 на OB11, модуль может вызывать их унифицированно на разных платформах:

| Стандартное действие OB12 | Действие OB11 | Описание |
|---------------------------|---------------|----------|
| get_self_info | get_login_info | Стандартизированные поля user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | Стандартизированные поля |
| delete_message | delete_msg | Отмена отправки сообщения |
| leave_group | set_group_leave | Выйти из группы |
| upload_file | upload_group_file / upload_private_file | Расширенные параметры group_id/user_id необязательны |

### Основное использование

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# Получение информации о боте
result = await snowluma.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# Отмена отправки сообщения
await snowluma.Api.delete_message(message_id=123456)

# Указание аккаунта (множественные аккаунты)
result = await snowluma.Api.Using("main").get_self_info()

# Некоторые действия с псевдонимами сервера через call() (общие для SnowLuma/NapCat)
result = await snowluma.Api.call("upload_foward_msg", messages=[...])  # псевдоним upload_forward_msg
```

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочечную синтаксическую конструкцию, например:

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# Отправка с использованием аккаунта по умолчанию
await snowluma.Send.To("group", group_id).Text("Hello World!")

# Отправка с указанием конкретного аккаунта
await snowluma.Send.Using("main").To("group", group_id).Text("Сообщение от основного аккаунта")

# Цепочечные модификаторы: @пользователь + ответ
await snowluma.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Ответ на сообщение")
```

### Основные методы отправки

- `.Text(text: str)` — отправка текстового сообщения.
- `.Image(file: Union[str, bytes], filename: str = "image.png")` — отправка изображения (поддержка URL, Base64 или bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")` — отправка голосового сообщения.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` — отправка видео сообщения.
- `.Face(id: Union[str, int])` — отправка эмодзи QQ.
- `.File(file: Union[str, bytes], filename: str = "file.dat")` — отправка файла.
- `.MergeForward(nodes, title="Объединённая переписка")` — отправка объединённого сообщения (см. следующий раздел).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12 (автоматически преобразуется в OB11; список node-сегментов автоматически маршрутизируется в объединённое сообщение).
- `.Recall(message_id: Union[str, int])` — отмена отправки сообщения.

### Объединённое сообщение

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

# Отправка объединённого сообщения (три уровня возврата, поддерживается бэкендами SnowLuma / NapCat):
# ① send_group/private_forward_msg специальный конечный путь (оригинальный NapCat, совместимость SnowLuma)
# ② upload_forward_msg получение resid → send_msg отправка forward-сегмента (расширение SnowLuma)
# ③ send_msg прямая отправка node-сегмента
await snowluma.Send.To("group", group_id).MergeForward(nodes)

# Анализ полученного объединённого сообщения (входящие forward-сегменты передаются как onebot11_forward, data.id — это resid)
result = await snowluma.Api.get_forward_msg(id="resid_xxx")
```

### Методы управления группой

Все методы должны быть вызваны через `To("group", group_id)` для указания целевой группы:

- `.Kick(user_id, reject_add_request=False)` — исключение участника из группы.
- `.Ban(user_id, duration=1800)` — ограничение участника в группе (в секундах), 0 означает разблокировку.
- `.WholeBan(enable=True)` — включение/выключение ограничения для всех участников.
- `.SetAdmin(user_id, enable=True)` — установка/удаление администратора группы.
- `.SetCard(user_id, card="")` — установка имени участника в группе.
- `.SetGroupName(name)` — изменение названия группы.
- `.Leave(is_dismiss=False)` — выход из группы (владелец может распустить).
- `.SetTitle(user_id, title="")` — установка титула участника в группе.
- `.SetPortrait(file)` — установка аватара группы.

### Кликнуть / Социальные функции

- `.GroupPoke(user_id)` — нажать на участника в группе (требуется `To("group", group_id)`).
- `.FriendPoke(user_id)` — нажать на друга.
- `.SendPoke(user_id)` — отправить нажатие (универсальный).
- `.SetMsgEmojiLike(message_id, emoji_id)` — реакция на сообщение с помощью эмодзи.

### QQ空间

- `.QzoneMsg(content)` — опубликовать пост в QQ空间.
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)` — поставить лайк/удалить лайк.
- `.QzoneComment(tid, content)` — оставить комментарий.
- `.QzoneDelete(tid)` — удалить пост.

### Файлы группы / История сообщений / Статус прочтения

- `.UploadGroupFile(file, name)` — загрузить файл в группу (требуется `To("group", group_id)`).
- `.GetGroupFileUrl(file_id)` — получить ссылку для скачивания файла группы.
- `.GetGroupMsgHistory(message_id=0, count=20)` — получить историю сообщений группы (message_id=0 с последнего).
- `.GetFriendMsgHistory(user_id, count=20)` — получить историю сообщений с другом.
- `.MarkMsgAsRead(message_id)` — отметить сообщение как прочитанное по ID.
- `.SetOnlineStatus(status)` — установить статус онлайн.

### Отправка в чат (расширение SnowLuma, автоматическая маршрутизация в групповой/личный чат)

- `.AIRecord(character, text, chat_type=1)` — отправить голосовое сообщение AI в группу (требуется `To("group", group_id)`; персонажи из `Api.get_ai_characters`).
- `.CustomFace(emoji_id, reply_to=None)` — отправить избранную эмодзи (сохраняет стиль отображения эмодзи).
- `.FlashMsg(fileset_id)` — отправить мгновенное сообщение (получивший может скачать).
- `.ForwardSingle(message_id)` — переслать одно сообщение в текущий чат.
- `.TuwenArk(title, desc, jump_url, summary="[Поделиться]", preview_url=...)` — отправить карточку Ark с изображением и текстом.

### Цепочечные модификаторы (можно комбинировать)

- `.At(user_id: Union[str, int])` — упомянуть пользователя (можно вызывать несколько раз).
- `.AtAll()` — упомянуть всех участников.
- `.Reply(message_id: Union[str, int])` — ответить на сообщение.

---

## OB11 расширенные действия (Api DSL)

Стандартная директория действий содержит **200 действий**, адаптер типизированно реализует 169 из них (`OB11ExtensionApi` 127 общих + `SnowLumaExtensionApi` 42 специфических для SnowLuma), остальные — прямой вызов Core / ApiDSL прозрачный / псевдонимы сервера, подробный статус см. в [таблице покрытия](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md).
Все действия можно вызывать напрямую через `Api.call("action_name", ...)`, общие для SnowLuma/NapCat части можно переносить между бэкендами. Группировка:

| Группа | Пример действия |
|--------|-----------------|
| Кликнуть / Социальные | send_poke / group_poke / friend_poke / send_like |
| Ответ на сообщение / Избранные | set_msg_emoji_like / get_msg_emoji_likes / fetch_emoji_like / set_essence_msg / get_essence_msg_list |
| Прочтение / Статус | mark_msg_as_read / mark_all_as_read / set_online_status / set_diy_online_status / set_input_status / nc_get_user_status |
| История сообщений | get_group_msg_history / get_friend_msg_history |
| Расширенное управление группой | set_group_reaction / set_group_remark / set_group_sign / set_group_todo（включая cancel/complete/list）/ get_group_info_ex / get_group_shut_list / get_group_at_all_remain / set_group_kick_members / set_group_member_invite_policy / set_group_search / set_group_robot_add_option |
| Теги группы / Настройки управления | add_group_tag / delete_group_tag / get_group_tags / get_group_admin_settings / set_group_add_option / set_group_member_permissions / set_group_new_member_history_visibility |
| Друзья / Контакты | set_friend_remark / delete_friend / set_friends_category / get_unidirectional_friend_list / get_friends_with_category / get_doubt_friends_add_request（включая обработку） |
| Файлы группы | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file（включая удаление/переименование папки）/ move_group_file / trans_group_file / get_group_file_system_info |
| Информация о группе | get_group_honor_info / get_group_share_link / get_group_system_msg / get_group_ignore_add_request / get_group_ignored_notifies |
| Групповые альбомы (список) | get_group_album_list / get_group_album_media_list |
| QQпространство | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds / like_qzone / unlike_qzone / comment_qzone / delete_qzone_msg |
| Объединённые сообщения / Пересылка | get_forward_msg / upload_forward_msg / send_forward_msg / forward_group_single_msg / forward_friend_single_msg |
| Ark-карточки / Мини-приложения | send_ark_share / send_group_ark_share / share_peer / share_group_ex / send_tuwen_ark / get_mini_app_ark / get_share_link |
| Голосовые сообщения AI | get_ai_characters / get_ai_record / send_group_ai_record |
| Анонсы группы / Модели / Одежда | get_group_notice / send_group_notice / delete_group_notice / get_model_show / set_model_show / get_friend_dress |
| Медиа / OCR | ocr_image / get_image / get_record / fetch_ptt_text |
| Токены / Возможности | get_cookies / get_csrf_token / get_credentials / get_clientkey / can_send_image / can_send_record / get_version_info |
| Инструменты / Разное | check_url_safely / clean_cache / get_file / get_rkey / get_rkey_server / translate_en2zh / get_online_clients / get_profile_like / click_inline_keyboard_button |

### Примеры использования

```python
snowluma = sdk.adapter.get("snowluma")

# Прочтение (по ID сообщения)
await snowluma.Api.mark_msg_as_read(message_id=123)

# Транскрибирование голоса (по ID сообщения)
result = await snowluma.Api.fetch_ptt_text(message_id=123)

# Детали реакции эмодзи
result = await snowluma.Api.get_msg_emoji_likes(message_id=123)

# Анонс группы
await snowluma.Api.send_group_notice(group_id=123456, content="Анонс", pinned=1)

# Голосовое сообщение AI
await snowluma.Api.send_group_ai_record(group_id=123456, character="1002", text="Привет")
```

## Специфические действия SnowLuma (SnowLumaExtensionApi)

Ниже перечислены действия, специфичные для бэкенда SnowLuma (не являются общими для NapCat/Lagrange), также предоставляются как типизированные методы:

### Расширения QQпространства

```python
# Детали поста и комментарии (требуется доступ)
result = await snowluma.Api.get_qzone_msg_detail(tid="tid_xxx", num=20)
# Изменение прав доступа к посту: 1=всем, 4=друзьям, 16=отдельным друзьям, 64=только себе, 128=некоторым друзьям недоступно
await snowluma.Api.set_qzone_msg_right(tid="tid_xxx", ugc_right=64)
# Заблокировать/разблокировать пользователя (чёрный список пространства бота)
await snowluma.Api.set_qzone_ban(user_id=789, enable=True)
```

### Групповые альбомы

```python
result = await snowluma.Api.get_qun_album_list(group_id=123456)
await snowluma.Api.upload_image_to_qun_album(group_id=123456, album_id="a1", album_name="Альбом", file="https://a.jpg")
await snowluma.Api.upload_video_to_qun_album(group_id=123456, album_id="a1", album_name="Альбом", file="./v.mp4")
await snowluma.Api.do_group_album_comment(group_id=123456, album_id="a1", lloc="xxx", content="Хорошо снято")
await snowluma.Api.del_group_album_media(group_id=123456, album_id="a1", lloc="xxx")
```

### Системные эмодзи

```python
result = await snowluma.Api.fetch_sys_faces()            # Полный каталог (по группам)
result = await snowluma.Api.search_sys_faces(query="Улыбка")  # Поиск по названию/alias/номеру
result = await snowluma.Api.fetch_face_entity(face_id=1)   # Поиск по номеру
result = await snowluma.Api.fetch_super_face_id(face_id=1) # Является ли супер-эмодзи
```

### Потоковые интерфейсы

```python
# Частичная загрузка файла на локальный робот (новый поток → по частям → is_complete объединение, возвращается локальный путь)
await snowluma.Api.upload_file_stream(stream_id="uuid", total_chunks=2, file_size=1024, filename="a.txt")
# Потоковая загрузка (file_info → file_chunk* → file_complete по фреймам)
await snowluma.Api.download_file_stream(file_id="cached-id", chunk_size=65536)
await snowluma.Api.download_file_image_stream(file="https://a.jpg")
await snowluma.Api.download_file_record_stream(file_id="cached-record")
await snowluma.Api.clean_stream_temp_file()
```

### Мгновенные сообщения / Избранные эмодзи / Низкоуровневые каналы

```python
# QQ мгновенные сообщения: код → fileset_id → отправка/список/прямая ссылка
fileset = await snowluma.Api.get_fileset_id(share_code="abcd1234")
await snowluma.Api.send_flash_msg(fileset_id="fs_xxx", group_id=123456)
result = await snowluma.Api.get_flash_file_list(fileset_id="fs_xxx")
result = await snowluma.Api.download_fileset(fileset_id="fs_xxx")

# Избранные эмодзи
await snowluma.Api.add_custom_face(file="https://a.gif")
result = await snowluma.Api.fetch_custom_face(count=10, return_type="url")
await snowluma.Api.send_custom_face(emoji_id="emoji_id_or_md5", group_id=123456)

# Низкоуровневые каналы (продвинутое использование)
await snowluma.Api.send_packet(cmd="Oidb.0xxxx", data="hex...")
await snowluma.Api.request_decrypt_key(db_path="./db")
await snowluma.Api.bot_exit()
```

---

## Сопоставление типов событий

### Стандартное сопоставление OB12

| Тип OB11 | Сопоставленный detail_type | Описание |
|----------|----------------------------|----------|
| message_type: private | `private` | Личное сообщение |
| message_type: group | `group` | Групповое сообщение |
| notice_type: group_upload | `group_file_upload` | Загрузка файла в группу |
| notice_type: group_admin | `group_admin_change` | Изменение администратора группы |
| notice_type: group_increase | `group_member_increase` | Увеличение участников группы |
| notice_type: group_decrease | `group_member_decrease` | Уменьшение участников группы |
| notice_type: group_ban | `group_ban` | Запрет участников группы |
| notice_type: friend_add | `friend_increase` | Добавление друга |
| notice_type: friend_delete | `friend_decrease` | Удаление друга |
| notice_type: group_recall / friend_recall | `message_recall` | Отмена отправки сообщения |

### Платформенно-специфичные события и расширенные сегменты

- Платформенно-специфичные события (poke/honor и т.д.) используют detail_type с префиксом `snowluma_`
- Неизвестные типы CQ-кодов передаются с префиксом `onebot11_{type}` (префикс на уровне протокола)
- Входящие объединённые сообщения передаются как `onebot11_forward` (data.id — это resid, можно использовать `Api.get_forward_msg(id=...)` для анализа содержимого)

### Объяснение расширенных полей

- Все специфические поля имеют префикс `snowluma_`
- Сохранённые исходные данные события находятся в поле `snowluma_raw`
- Сохранённый исходный тип события находится в поле `snowluma_raw_type`

---

## Методы расширения событий

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

| Метод | Тип возвращаемого значения | Описание |
|-------|----------------------------|----------|
| `get_raw_event()` | `dict` | Получить полные исходные данные события SnowLuma |
| `get_raw_self_id()` | `str` | Получить исходный self_id (номер QQ бота) |
| `get_sender_info()` | `dict` | Получить полную информацию об отправителе (включая nickname, role, level и т.д.) |
| `get_sender_role()` | `str` | Получить роль отправителя в группе (owner/admin/member) |
| `get_sender_level()` | `int` | Получить уровень отправителя |
| `get_sender_title()` | `str` | Получить титул отправителя в группе |
| `is_system_message()` | `bool` | Определить, является ли сообщение системным |

---

## Параметры конфигурации

Адаптер SnowLuma использует архитектуру с несколькими аккаунтами, каждый аккаунт настраивается отдельно. Ключ конфигурации: `SnowLuma_Adapter`.

### Поля конфигурации аккаунта

| Поле | Тип | Обязательно | Значение по умолчанию | Описание |
|------|-----|-------------|------------------------|----------|
| `mode` | `str` | Нет | `"client"` | `client`(активное подключение к WS) / `server`(обратный WS) / `http`(HTTP API+опрос) / `webhook`(HTTP API+отчет) |
| `url` | `str` | Нет | `"ws://127.0.0.1:3001"` | Адрес WebSocket для режима client (порт по умолчанию SnowLuma WS 3001) |
| `token` | `str` | Нет | `""` | Токен доступа (авторизация Bearer) |
| `server_path` | `str` | Нет | `"/"` | Путь WebSocket для режима server |
| `http_url` | `str` | Нет | `"http://127.0.0.1:3000"` | Адрес API для режимов http/webhook |
| `poll_interval` | `float` | Нет | `1.0` | Интервал опроса событий в режиме http (секунды) |
| `webhook_path` | `str` | Нет | `"/snowluma_{account}"` | Префикс маршрута отчета для режима webhook |
| `enabled` | `bool` | Нет | `true` | Включить ли этот аккаунт |
| `name` | `str` | Нет | `""` | Имя аккаунта |

> Номер bot_id (QQ) не требуется в конфигурации: адаптер автоматически определяет и поддерживает отображение `self_id → account_name`, `event.reply()` автоматически маршрутизируется к аккаунту отправителя.

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

## Возвращаемые значения методов отправки

Все методы отправки возвращают объект Task, который можно await для получения результата отправки. Возвращаемый результат соответствует стандартизированному формату возврата адаптера ErisPulse:

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
await snowluma.Send.Using("main").To("group", 123456).Text("Сообщение от основного аккаунта")

# Вызов API
await snowluma.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## Автоматическое отображение self_id

Адаптер автоматически устанавливает отображение OneBot `self_id` (номер QQ) в `account_name` для маршрутизации событий обратно:

```python
@message.on_message()
async def handler(event):
    # Автоматически маршрутизируется к правильному аккаунту
    await event.reply("Автоматически маршрутизируется к аккаунту отправителя")
```