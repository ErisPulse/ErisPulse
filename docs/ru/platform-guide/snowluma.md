# Документация по функциям платформы SnowLuma

SnowLumaAdapter — это адаптер, построенный на базе бэкенда SnowLuma (NTQQ hook), использующий протокол OneBot v11. Он устанавливается как необязательное расширение для `ErisPulse-OneBot11Adapter[snowluma]` (команда установки: `pip install "ErisPulse-OneBot11Adapter[snowluma]"`).

---

## Информация о документации

- Версия соответствующего модуля: 0.3.4
- Поддержка: ErisPulse
- Версия протокола: OneBot v11 (расширение совместимости с NapCat/go-cqhttp)
- Последнее обновление: 2026-11-10

## Основная информация

- Краткое описание платформы: SnowLuma — реализация протокола QQ на основе NTQQ hook, с API, полностью совместимым с NapCat, предоставляющим сервис через протокол OneBot v11 (порт по умолчанию: HTTP 3000, WS 3001)
- Название адаптера: SnowLumaAdapter
- Поддерживаемые протоколы/API: OneBot V11 (всего 200 действий, адаптер полностью покрывает, полностью совместим с NapCat, можно напрямую подключаться к бэкенду NapCat)
- Поддержка нескольких аккаунтов: по умолчанию архитектура с несколькими аккаунтами, поддерживает одновременную настройку и запуск нескольких аккаунтов
- Имя ключа конфигурации: `SnowLuma_Adapter`
- Поддержка локализации: 5 языков (zh-CN / zh-TW / en / ja / ru)

### Отношения с адаптером OneBot11

SnowLuma использует протокол OB11, стандартные действия и события преобразуются в структуру, идентичную адаптеру OneBot11 (имена стандартных действий OB12 автоматически сопоставляются). Основные различия:

1. **Режим client по умолчанию**: активное подключение к SnowLuma WS (`ws://127.0.0.1:3001`), не требуется публичное прослушивание; также поддерживаются режимы server (обратный WS), http (API + опрос) и webhook (API + отчет), всего четыре режима
2. **Автоматическое определение bot_id**: нет необходимости вручную указывать номер QQ в конфигурации аккаунта, адаптер автоматически определяет и поддерживает отображение `self_id → account_name` после запуска
3. **Полная упаковка 200 действий**: 169 типизированных методов (127 общих + 42 специфических для SnowLuma), остальные — прямые вызовы Core / прозрачный пересыл / псевдонимы сервера, полное соответствие см. в репозитории адаптера [docs/api-coverage.md](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md)
4. **Расширенная цепочка объединенных пересылок**: специальный конечный путь + `upload_forward_msg` (получение resid из узла) + `get_forward_msg` (анализ содержимого пересылки), три уровня возврата

---

## Стандартные действия API (Api DSL)

Адаптер автоматически сопоставляет стандартные действия OB12 с OB11, модуль может использовать единый вызов для кроссплатформенной работы:

| Стандартное действие OB12 | Действие OB11 | Описание |
|--------------|-----------|------|
| get_self_info | get_login_info | Стандартизированные поля user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | Стандартизированные поля |
| delete_message | delete_msg | Отмена сообщения |
| leave_group | set_group_leave | Покидание группы |
| upload_file | upload_group_file / upload_private_file | Расширенные параметры group_id/user_id |

### Основное использование

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# Получение информации о боте
result = await snowluma.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# Отмена сообщения
await snowluma.Api.delete_message(message_id=123456)

# Расширенные параметры upload_file (OB11 привязка файла к цели, необязательные параметры group_id/user_id)
await snowluma.Api.upload_file(type="path", name="doc.pdf", path="./doc.pdf", group_id="123456")
await snowluma.Api.upload_file(type="url", name="img.jpg", url="https://...", user_id="789")

# Указание аккаунта (множественные аккаунты)
result = await snowluma.Api.Using("main").get_self_info()

# Редкие действия через call() (универсальные для SnowLuma/NapCat)
result = await snowluma.Api.call("upload_foward_msg", messages=[...])  # псевдоним upload_forward_msg
```

> **Назначение имен**: расширения протокола OB11 используют непосредственно имя действия (например, `send_poke`), без префикса `snowluma.`. Только действительно уникальные функции платформы используют `{prefix}.xxx`.

## Стандартизированное соответствие

Этот раздел описывает поведение адаптера, соответствующего стандартам ErisPulse. Подробности спецификаций см. в документации SDK «Спецификация запросов и действий» (docs/ru/standards/request-action-spec.md) и «Спецификация ответов API» (docs/ru/standards/api-response.md).

### Обработка запросов и событий (начиная с 0.3.3)

Адаптер реализует получение и ответ на запросы и события в соответствии со спецификацией запросов и действий (идентична адаптеру OneBot11):

- **Сохранение контекста**: при входе в событие `request_id` сопоставляется с `{request_type, sub_type, group_id, account, ts}` и кэшируется (TTL 3600 секунд, максимум 512 записей, после успешной обработки запроса удаляется), используется для последующего маршрутизирования `accept()`/`reject()`
- **Приоритет маршрутизации конечных точек**: явный передачи kwargs в `accept()`/`reject()` (`request_type`/`sub_type`/`group_id` зарезервированы) > сохраненный контекст события > резервный конечный пункт друга (set_friend_add_request) с выводом WARNING
- **Запросы на приглашение/вступление в группу**: при `request_type == "group"` корректно маршрутизируется в `set_group_add_request` (вступление `sub_type="add"`, приглашение `sub_type="invite"`)
- **Устаревшее объявление**: использование приватного параметра `_request_type` для указания типа запроса устарело, передача будет проигнорирована

### Коды ошибок call_api

- Ошибка HTTP вызова (ошибка подключения/таймаут) возвращает `retcode=33001` стандартный ответ об ошибке
- Некорректный формат ответа (невозможно распарсить в стандартную структуру) возвращает `retcode=34100`, исходные данные сохраняются в поле `snowluma_raw`

| retcode | Смысл | Сценарий |
|---------|------|----------|
| 0 | Успешно | Действие выполнено успешно |
| 33001 | Ошибка сети | Ошибка HTTP вызова, таймаут API |
| 34100 | Ошибка платформы | Некорректный формат ответа (исходные данные сохраняются в `snowluma_raw`) |

### Двухсторонняя совместимость с полями аккаунта и send_context

- `call_api` принимает как стандартные поля `account_id`, так и старые названия полей `_account_id` (приоритет стандартного имени); фреймворк ApiDSL автоматически адаптирует, рекомендуется использовать `account_id` в коде модуля
- Все методы Send DSL читают `send_context`: в цепочке событий автоматически используется аккаунт источника события, при явном указании `Using()` аккаунт имеет приоритет

### Стандартизация полей событий

- В верхнем уровне мета-события `type` унифицируется в `"meta"` (старое `meta_event` больше не используется)
- Все специфические поля имеют префикс `snowluma_`, исходные данные сохраняются в `snowluma_raw`

---

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы через цепочечную синтаксис, например:

```python
from ErisPulse import sdk
snowluma = sdk.adapter.get("snowluma")

# Использование аккаунта по умолчанию
await snowluma.Send.To("group", group_id).Text("Hello World!")

# Отправка с указанием конкретного аккаунта
await snowluma.Send.Using("main").To("group", group_id).Text("Сообщение от основного аккаунта")

# Цепочечные модификаторы: @пользователь + ответ
await snowluma.Send.To("group", group_id).At(123456).Reply(msg_id).Text("Ответное сообщение")
```

### Основные методы отправки

- `.Text(text: str)` — отправка текстового сообщения.
- `.Image(file: Union[str, bytes], filename: str = "image.png")` — отправка изображения (поддержка URL, Base64 или bytes).
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")` — отправка голосового сообщения.
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` — отправка видео сообщения.
- `.Face(id: Union[str, int])` — отправка эмодзи QQ.
- `.File(file: Union[str, bytes], filename: str = "file.dat")` — отправка файла.
- `.MergeForward(nodes, title="Объединённая история чата")` — отправка объединённой пересылки сообщений (см. следующий раздел).
- `.Raw_ob12(message: List[Dict], **kwargs)` — отправка сообщения в формате OneBot12 (автоматически преобразуется в OB11; список узлов node автоматически маршрутизируется в объединённую пересылку).
- `.Recall(message_id: Union[str, int])` — отмена сообщения.

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

# Отправка объединённой пересылки (три уровня возврата, работает с бэкендами SnowLuma и NapCat):
# ① send_group/private_forward_msg специальный конечный путь (оригинальный NapCat, совместимость SnowLuma)
# ② upload_forward_msg получение resid → send_msg отправка сегмента forward (расширенная цепочка SnowLuma)
# ③ send_msg прямая отправка сегмента node
await snowluma.Send.To("group", group_id).MergeForward(nodes)

# Анализ полученного объединённого сообщения пересылки (входящий сегмент forward передаётся как onebot11_forward, data.id — это resid, можно использовать Api.get_forward_msg(id=...) для анализа содержимого)
result = await snowluma.Api.get_forward_msg(id="resid_xxx")
```

### Методы управления группой

Все методы должны быть вызваны через `To("group", group_id)` для указания целевой группы:

- `.Kick(user_id, reject_add_request=False)` — исключение участника из группы.
- `.Ban(user_id, duration=1800)` — запрет участнику говорить (в секундах), 0 означает разблокировку.
- `.WholeBan(enable=True)` — включить/выключить запрет всем участникам говорить.
- `.SetAdmin(user_id, enable=True)` — установить/снять администратора группы.
- `.SetCard(user_id, card="")` — установить имя участника в группе.
- `.SetGroupName(name)` — изменить название группы.
- `.Leave(is_dismiss=False)` — выйти из группы (владелец может распустить).
- `.SetTitle(user_id, title="")` — установить титул участника в группе.
- `.SetPortrait(file)` — установить аватар группы.

### Удары / Социальные действия

- `.GroupPoke(user_id)` — ударить участника в группе (требуется `To("group", group_id)`).
- `.FriendPoke(user_id)` — ударить участника в好友.
- `.SendPoke(user_id)` — отправить удар (универсальный).
- `.SetMsgEmojiLike(message_id, emoji_id)` — эмоциональный ответ на сообщение.

### QQ Пространство

- `.QzoneMsg(content)` — опубликовать сообщение в QQ Пространстве.
- `.QzoneLike(tid)` / `.QzoneUnlike(tid)` — поставить/удалить лайк.
- `.QzoneComment(tid, content)` — оставить комментарий.
- `.QzoneDelete(tid)` — удалить сообщение.

### Файлы группы / История сообщений / Статус прочтения

- `.UploadGroupFile(file, name)` — загрузить файл в группу (требуется `To("group", group_id)`).
- `.GetGroupFileUrl(file_id)` — получить ссылку на скачивание файла группы.
- `.GetGroupMsgHistory(message_id=0, count=20)` — получить историю сообщений группы (message_id=0 от последнего).
- `.GetFriendMsgHistory(user_id, count=20)` — получить историю сообщений好友.
- `.MarkMsgAsRead(message_id)` — отметить сообщение как прочитанное по ID.
- `.SetOnlineStatus(status)` — установить статус онлайн.

### Отправка в сессию (расширение SnowLuma, автоматически маршрутизируется в группу/личный чат)

- `.AIRecord(character, text, chat_type=1)` — отправить AI голос в группу (требуется `To("group", group_id)`; персонаж из `Api.get_ai_characters`).
- `.CustomFace(emoji_id, reply_to=None)` — отправить сохранённый эмодзи (сохраняет стиль отображения).
- `.FlashMsg(fileset_id)` — отправить мгновенную передачу (получатель может скачать).
- `.ForwardSingle(message_id)` — переслать одно сообщение в текущую сессию.
- `.TuwenArk(title, desc, jump_url, summary="[Share]", preview_url=...)` — отправить карточку с изображением и текстом.

### Дополнительные удобные методы Send

| Метод | Соответствующее действие | Описание |
|------|---------|------|
| `.GroupReaction(msg_id, emoji_id)` | `set_group_reaction` | Реакция на сообщение в группе |
| `.SetEssenceMsg(msg_id)` | `set_essence_msg` | Установить эссенцию сообщения |
| `.DeleteEssenceMsg(msg_id)` | `delete_essence_msg` | Удалить эссенцию сообщения |
| `.SetFriendRemark(uid, remark)` | `set_friend_remark` | Установить заметку好友 |
| `.OcrImage(image)` | `ocr_image` | OCR распознавание изображения |
| `.GetImage(file)` | `get_image` | Получить информацию об изображении |
| `.GetRecord(file)` | `get_record` | Получить информацию о голосовом сообщении |
| `.FetchPttText(message_id)` | `fetch_ptt_text` | Преобразование голоса в текст |

### Цепочечные модификаторы (можно комбинировать)

- `.At(user_id: Union[str, int])` — @указать пользователя (можно вызывать несколько раз).
- `.AtAll()` — @всех участников.
- `.Reply(message_id: Union[str, int])` — ответить на сообщение.

---

## OB11 расширенные действия (Api DSL)

В официальном каталоге действий всего **200 действий**, адаптер типизированно封装ирует 169 из них (`OB11ExtensionApi` 127 общих + `SnowLumaExtensionApi` 42 специфических для SnowLuma), остальные — прямые вызовы Core / прозрачный пересыл / псевдонимы сервера, подробный статус см. в репозитории адаптера [таблица покрытия](https://github.com/ErisPulse/ErisPulse-SnowLumaAdapter/blob/main/docs/api-coverage.md).
Все действия можно напрямую вызывать через `Api.call("action_name", ...)`, общие для SnowLuma/NapCat части переносимы между бэкендами. Группировка:

| Группа | Пример действия |
|------|----------|
| Удары / Социальные | send_poke / group_poke / friend_poke / send_like |
| Ответы на сообщения / Эссенции | set_msg_emoji_like / get_msg_emoji_likes / fetch_emoji_like / set_essence_msg / get_essence_msg_list |
| Прочтение / Статус | mark_msg_as_read / mark_all_as_read / set_online_status / set_diy_online_status / set_input_status / nc_get_user_status |
| История сообщений | get_group_msg_history / get_friend_msg_history |
| Расширенное управление группой | set_group_reaction / set_group_remark / set_group_sign / set_group_todo (с cancel/complete/list) / get_group_info_ex / get_group_shut_list / get_group_at_all_remain / set_group_kick_members / set_group_member_invite_policy / set_group_search / set_group_robot_add_option |
| Теги группы / Настройки управления | add_group_tag / delete_group_tag / get_group_tags / get_group_admin_settings / set_group_add_option / set_group_member_permissions / set_group_new_member_history_visibility |
|好友 / Контакты | set_friend_remark / delete_friend / set_friends_category / get_unidirectional_friend_list / get_friends_with_category / get_doubt_friends_add_request (с обработкой) |
| Файлы группы | get_group_file_url / get_private_file_url / get_group_root_files / get_group_files_by_folder / create_group_file_folder / delete_group_file (с удалением/переименованием папки) / move_group_file / trans_group_file / get_group_file_system_info |
| Информация группы | get_group_honor_info / get_group_share_link / get_group_system_msg / get_group_ignore_add_request / get_group_ignored_notifies |
| Галерея группы (список) | get_group_album_list / get_group_album_media_list |
| QQ Пространство | send_qzone_msg / get_qzone_msg_list / get_qzone_feeds / like_qzone / unlike_qzone / comment_qzone / delete_qzone_msg |
| Объединённая пересылка / Одиночная пересылка | get_forward_msg / upload_forward_msg / send_forward_msg / forward_group_single_msg / forward_friend_single_msg |
| Ark карточки / Мини-приложения | send_ark_share / send_group_ark_share / share_peer / share_group_ex / send_tuwen_ark / get_mini_app_ark / get_share_link |
| AI голос | get_ai_characters / get_ai_record / send_group_ai_record |
| Групповые объявления / Модели / Одежда | get_group_notice / send_group_notice / delete_group_notice / get_model_show / set_model_show / get_friend_dress |
| Медиа / OCR | ocr_image / get_image / get_record / fetch_ptt_text |
| Токены / Способности | get_cookies / get_csrf_token / get_credentials / get_clientkey / can_send_image / can_send_record / get_version_info |
| Инструменты / Разное | check_url_safely / clean_cache / get_file / get_rkey / get_rkey_server / translate_en2zh / get_online_clients / get_profile_like / click_inline_keyboard_button |

### Пример использования

```python
snowluma = sdk.adapter.get("snowluma")

# Прочтение (по ID сообщения)
await snowluma.Api.mark_msg_as_read(message_id=123)

# Преобразование голоса в текст (по ID сообщения)
result = await snowluma.Api.fetch_ptt_text(message_id=123)

# Подробности реакции на эмодзи
result = await snowluma.Api.get_msg_emoji_likes(message_id=123)

# Групповое объявление
await snowluma.Api.send_group_notice(group_id=123456, content="Объявление", pinned=1)

# AI голос
await snowluma.Api.send_group_ai_record(group_id=123456, character="1002", text="Привет")
```

## Специфические действия SnowLuma (SnowLumaExtensionApi)

Ниже перечислены действия, уникальные для сервера SnowLuma (не являются общими для NapCat/Lagrange), также предоставляются в виде типизированных методов:

### Расширения QQ Пространства

```python
# Детали сообщения и страница комментариев (требуется разрешение)
result = await snowluma.Api.get_qzone_msg_detail(tid="tid_xxx", num=20)
# Изменение прав доступа к опубликованному сообщению: 1=всем, 4=друзьям, 16=части друзей, 64=только себе, 128=некоторым друзьям недоступно
await snowluma.Api.set_qzone_msg_right(tid="tid_xxx", ugc_right=64)
# Заблокировать/разблокировать пользователя (чёрный список QQ Пространства бота)
await snowluma.Api.set_qzone_ban(user_id=789, enable=True)
```

### Галерея группы

```python
result = await snowluma.Api.get_qun_album_list(group_id=123456)
await snowluma.Api.upload_image_to_qun_album(group_id=123456, album_id="a1", album_name="Галерея", file="https://a.jpg")
await snowluma.Api.upload_video_to_qun_album(group_id=123456, album_id="a1", album_name="Галерея", file="./v.mp4")
await snowluma.Api.do_group_album_comment(group_id=123456, album_id="a1", lloc="xxx", content="Отлично снято")
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
# Постепенная загрузка файла на локальный сервер бота (новый поток → блоки → is_complete объединение, возвращается путь к локальному файлу)
await snowluma.Api.upload_file_stream(stream_id="uuid", total_chunks=2, file_size=1024, filename="a.txt")
# Потоковая загрузка (file_info → file_chunk* → file_complete возвращаются фреймы)
await snowluma.Api.download_file_stream(file_id="cached-id", chunk_size=65536)
await snowluma.Api.download_file_image_stream(file="https://a.jpg")
await snowluma.Api.download_file_record_stream(file_id="cached-record")
await snowluma.Api.clean_stream_temp_file()
```

### Мгновенная передача / Коллекция эмодзи / Низкоуровневые каналы

```python
# QQ Мгновенная передача: код → fileset_id → отправка/список/прямая ссылка
fileset = await snowluma.Api.get_fileset_id(share_code="abcd1234")
await snowluma.Api.send_flash_msg(fileset_id="fs_xxx", group_id=123456)
result = await snowluma.Api.get_flash_file_list(fileset_id="fs_xxx")
result = await snowluma.Api.download_fileset(fileset_id="fs_xxx")

# Коллекция эмодзи
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

| Тип OB11 | Преобразованный detail_type | Описание |
|--------------|-------------------|------|
| message_type: private | `private` | Личное сообщение |
| message_type: group | `group` | Групповое сообщение |
| request_type: friend | `friend` | Запрос好友 |
| request_type: group | `group` | Запрос группы (вступление/приглашение) |
| notice_type: group_upload | `group_file_upload` | Загрузка файла в группу |
| notice_type: group_admin | `group_admin_change` | Изменение администратора группы |
| notice_type: group_increase | `group_member_increase` | Увеличение участников группы |
| notice_type: group_decrease | `group_member_decrease` | Уменьшение участников группы |
| notice_type: group_ban | `group_ban` | Запрет в группе |
| notice_type: friend_add | `friend_increase` | Добавление好友 |
| notice_type: friend_delete | `friend_decrease` | Удаление好友 |
| notice_type: group_recall / friend_recall | `message_recall` | Отмена сообщения |

### Платформо-специфические события и расширенные сегменты

- Платформо-специфические события (poke/honor и др.) используют `snowluma_` префикс detail_type
- Не распознанные CQ-коды типов передаются как `onebot11_{type}` префикс (протокольный префикс)
- Входящие объединённые пересылки сообщений имеют сегмент `onebot11_forward` (`data.id` — это resid, можно использовать `Api.get_forward_msg(id=...)` для анализа содержимого)

### Объяснение расширенных полей

- Все специфические поля имеют префикс `snowluma_`
- Исходные данные события сохраняются в поле `snowluma_raw`
- Тип события сохраняется в поле `snowluma_raw_type`
- В верхнем уровне мета-событий `type` унифицируется в `"meta"`

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
|------|----------|------|
| `get_raw_event()` | `dict` | Получить полные исходные данные события SnowLuma |
| `get_raw_self_id()` | `str` | Получить исходный self_id (номер QQ бота) |
| `get_sender_info()` | `dict` | Получить полную информацию об отправителе (включая nickname, role, level и др.) |
| `get_sender_role()` | `str` | Получить роль отправителя в группе (owner/admin/member) |
| `get_sender_level()` | `int` | Получить уровень отправителя |
| `get_sender_title()` | `str` | Получить титул отправителя в группе |
| `is_system_message()` | `bool` | Определить, является ли сообщение системным |

---

## Параметры конфигурации

Адаптер SnowLuma использует архитектуру с несколькими аккаунтами, каждый аккаунт настраивается независимо. Имя ключа конфигурации: `SnowLuma_Adapter`.

### Поля конфигурации аккаунта

| Поле | Тип | Обязательно | Значение по умолчанию | Описание |
|------|------|------|------|------|
| `mode` | `str` | Нет | `"client"` | `client`(активное подключение WS) / `server`(обратный WS) / `http`(HTTP API+опрос) / `webhook`(HTTP API+отчет) |
| `url` | `str` | Нет | `"ws://127.0.0.1:3001"` | Адрес WebSocket для режима client (порт WebSocket по умолчанию SnowLuma 3001) |
| `token` | `str` | Нет | `""` | Токен доступа (авторизация Bearer) |
| `server_path` | `str` | Нет | `"/"` | Путь WebSocket для режима server |
| `http_url` | `str` | Нет | `"http://127.0.0.1:3000"` | Адрес API для режимов http/webhook |
| `poll_interval` | `float` | Нет | `1.0` | Интервал опроса событий для режима http (секунды) |
| `webhook_path` | `str` | Нет | `"/snowluma_{account}"` | Префикс маршрута отчета для режима webhook |
| `enabled` | `bool` | Нет | `true` | Включен ли этот аккаунт |
| `name` | `str` | Нет | `""` | Имя аккаунта |

> self_id (номер QQ) не требует настройки: адаптер автоматически определяет и поддерживает отображение `self_id → account_name`, `event.reply()` автоматически маршрутизируется к аккаунту источника.

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

Все методы отправки возвращают объект задачи, который можно ожидать для получения результата отправки. Результаты соответствуют стандартизированному возвращаемому формату адаптера ErisPulse:

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

# Способ вызова API
await snowluma.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## Автоматическое сопоставление self_id

Адаптер автоматически устанавливает сопоставление OneBot `self_id` (номер QQ) с `account_name` для маршрутизации ответов событий:

```python
@message.on_message()
async def handler(event):
    # Автоматически маршрутизируется к правильному аккаунту
    await event.reply("Автоматически маршрутизируется к аккаунту источника")
```