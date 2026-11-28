# Документация по функциям платформы QQBot

QQBotAdapter — это адаптер, построенный на основе официального протокола QQ для роботов (QQ OpenAPI), объединяющий функции для чатов в группах, личных сообщениях и каналах, предоставляющий стандартные события OneBot12, стандартные API-действия и интерфейсы для запросов.

---

## Информация о документации

- Версия соответствующего модуля: 5.3.3
- Поддержка: ErisPulse
- Последнее обновление: 2026-11-10

## Основная информация

- Краткое описание платформы: Официальный интерфейс разработки роботов QQ, поддерживающий различные сценарии, такие как групповые чаты, личные сообщения и каналы
- Название адаптера: QQBotAdapter
- Способ подключения: **WebSocket-длинное соединение** (по умолчанию) или **Webhook HTTP-вызов обратной связи** (в зависимости от настроек аккаунта, проверка подписи Ed25519)
- Способ аутентификации: appId + clientSecret для получения access_token (7200 секунд, автоматическое обновление за 45 секунд до истечения срока)
- Корневой адрес API: `https://api.bot.qq.com` (с v5 официальный единый домен, sandbox устарел)
- Совместимость с OneBot12: Полное покрытие отправки и получения сообщений, событий, **стандартных API-действий** и **запросов**
- Множественные аккаунты: Поддержка, произвольные аккаунты в `accounts` могут работать параллельно (возможна смешанная модель websocket/webhook)

## Описание конфигурации

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # Глобальные: подписка на события intents (JSON-массив, поддержка имен событий)

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # ID приложения робота QQ (обязательно)
secret = "YOUR_CLIENT_SECRET"        # Секретный ключ клиента робота QQ (обязательно)
mode = "websocket"                   # Способ получения событий: websocket / webhook
bot_id = ""                          # ID робота (оставьте пустым для автоматического получения; можно вручную заполнить для использования в Using())
gateway_url = ""                     # URL WebSocket-шлюза (оставьте пустым для получения динамически через /gateway/bot)
api_base_url = "https://api.bot.qq.com"  # Корневой адрес API (можно настроить для прокси)
access_token_url = ""                # Пользовательский URL для получения токена (оставьте пустым для использования официального)
webhook_path = "/webhook"            # Путь обратной связи webhook (действует при mode=webhook)
enabled = true
```

**Разрушительные изменения v5:**
- Поле `sandbox` устарело: официально используется `api.bot.qq.com`, старые настройки с sandbox автоматически переносятся и игнорируются (выводится предупреждение)
- Старая плоская конфигурация (appid/secret непосредственно в `[QQBot_Adapter]`) автоматически переносится в `accounts.default`
- Рамка является **мягкой зависимостью**: установка адаптера не тянет версию рамки; во время выполнения проверяется наличие `ErisPulse>=2.7.1` и выводится сообщение

**Описание intents (поддержка позиционных номеров или имен событий):**

| Позиция | Имя события | Описание |
|----|--------|------|
| 0 | GUILDS | Изменения канала |
| 1 | GUILD_MEMBERS | Изменения участников канала |
| 9 | GUILD_MESSAGES | Сообщения канала (требуется проверка для частных каналов) |
| 10 | GUILD_MESSAGE_REACTIONS | Реакции на сообщения канала |
| 12 | DIRECT_MESSAGE | Личные сообщения канала |
| 24 | GROUP_MEMBER | Изменения участников группы (введено в v5) |
| 25 | GROUP_AND_C2C_EVENT | Сообщения упоминания в группе и личные сообщения |
| 26 | INTERACTION | Взаимодействие (кнопки и т.д.) |
| 27 | MESSAGE_AUDIT | События проверки сообщений |
| 28 | FORUMS_EVENT | События форума (только для частных каналов) |
| 29 | AUDIO_ACTION | Действия аудио |
| 30 | PUBLIC_GUILD_MESSAGES | Сообщения канала (общедоступные) |

```toml
# Два способа записи эквивалентны
intents = "[0, 9, 12, 25, 26, 27]"
intents = '["GUILDS", "GUILD_MESSAGES", "DIRECT_MESSAGE", "GROUP_AND_C2C_EVENT", "INTERACTION", "MESSAGE_AUDIT"]'
```

## Стандартизация

В этом разделе описано, как адаптер соответствует стандартам ErisPulse. Подробности см. в документации SDK «Спецификация запросов» (`docs/ru/standards/request-action-spec.md`) и «Спецификация ответов API» (`docs/ru/standards/api-response.md`).

### Стандартизация кодов ошибок (5.3.x)

- **Единый код ошибки платформы 34100**: При возврате ошибки API QQ возвращается `retcode=34100`, оригинальный ответ (с кодом/сообщением QQ) сохраняется в поле `qqbot_raw` (ошибка при загрузке медиа также использует 34100)
- **Тайм-аут 33001**: При таймауте API возвращается `retcode=33001` (старый 32000 больше не используется)
- **Отсутствие контекста для удаления 10003**: При отсутствии контекста для удаления сообщения в `delete_message` возвращается `retcode=10003` (ошибка параметра)
- **Резервные коды для запросов 34001/34003**: При отсутствии или истечении срока запроса возвращается `34001`; при отсутствии маршрута в контексте запроса возвращается `34003`

| retcode | Описание |
|---------|------|
| 0 | Успешно |
| 10001 | Отсутствуют параметры/пустой эндпоинт |
| 10002 | Не поддерживаемое действие |
| 10003 | Невозможно определить цель отправки/аккаунт, отсутствие контекста для удаления и т.д. ошибка параметра |
| 33000 | Сетевая/ошибка вызова API |
| 33001 | Тайм-аут запроса |
| 34001 | Запрос отсутствует или истек (Request DSL) |
| 34003 | В контексте запроса отсутствует маршрутный параметр (Request DSL) |
| 34100 | Ошибка бизнес-логики платформы (оригинальный ответ и код QQ сохраняются в `qqbot_raw`) |

### Стандартизация имен уведомлений (5.3.x)

События добавления/удаления друзей унифицированы:

| Оригинальное событие | Преобразованное detail_type | Описание |
|----------|-------------------|------|
| FRIEND_ADD | `friend_increase` | Добавление друга (старое `friend_add` устарело) |
| FRIEND_DEL | `friend_decrease` | Удаление друга (старое `friend_del` устарело) |

### Сохранение контекста запроса (начиная с 5.3.2)

Входящие события запроса на вступление в группу будут сопоставлять `request_id` с контекстом запроса (группа/открытый идентификатор участника) и кэшировать (TTL 3600 секунд, максимальное количество 512 записей, очистка после успешной обработки), при выполнении одобрения маршрутизация к `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`.

### Маршрутизация расширенных действий (5.3.x)

Проверка прав участника канала предоставляется через расширенные действия с префиксом платформы:

```python
result = await qqbot.Api.call("qqbot.get_channel_member_permissions", channel_id="...", member_id="...")
```

### send_context для потоковой отправки

Потоковые сообщения (`.Stream()`) используют `send_context`: в цепочке событий автоматически используется текущий аккаунт источника, явно указанный аккаунт в `Using()` имеет приоритет.

## Отправка сообщений

### Базовая отправка

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

# Отправка текста
await qqbot.Send.To("user", user_openid).Text("Hello World!")

# Упоминание в группе (автоматически использует формат <qqbot-at-user id="x" />)
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@you")
await qqbot.Send.To("group", group_openid).AtAll().Text("Анонс")

# Сообщение в канале (упоминание автоматически использует формат <@user_id>)
await qqbot.Send.To("channel", channel_id).Text("Сообщение канала")

# Личное сообщение в канале (сначала создайте сессию)
dms = await qqbot.create_dms(user_id, source_guild_id)
await qqbot.Send.To("dms", dms["data"]["guild_id"]).Text("Личное сообщение")

# Ответ на сообщение (ответное сообщение, автоматически включает msg_id)
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("Содержание ответа")

# Множественные аккаунты (указание имени аккаунта или bot_id в Using/Account)
await qqbot.Send.Using("account2").To("group", group_openid).Text("От второго робота")
```

### Мультимедиа

```python
# Поддержка URL / локального пути / бинарных данных; при превышении 5 МБ автоматически разбивается на части
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")
await qqbot.Send.To("user", uid).Image("/path/to/local.png")
await qqbot.Send.To("user", uid).Voice(open("audio.mp3", "rb").read())
await qqbot.Send.To("user", uid).Video("https://example.com/v.mp4")
await qqbot.Send.To("user", uid).File(b"...", filename="doc.pdf")

# Изображения каналов отправляются напрямую через multipart (file_image)
await qqbot.Send.To("channel", cid).Image(open("img.png", "rb").read())
```

`file_type` отображается: изображение=1, видео=2, аудио=3, файл=4 (по типу сообщения автоматически определяется, `file` по расширению файла)

### Markdown / Ark / Embed / Keyboard

```python
# Оригинальный Markdown
await qqbot.Send.To("group", gid).Markdown("# Заголовок\n- Элемент списка")

# Markdown с шаблоном
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "Уведомление"}])
await qqbot.Send.To("user", uid).Markdown(custom_template_id="23456", kv=[...])

# Ark-шаблон
await qqbot.Send.To("user", uid).Ark(23, [{"key": "a", "value": "b"}])

# Embed (только для каналов/личных сообщений)
await qqbot.Send.To("channel", cid).Embed({"title": "Заголовок", "content": "Содержание"})

# Клавиатура (автоматически устанавливается тип markdown и добавляется bot_appid)
keyboard = {"content": {"rows": [[{"label": "Подтвердить", "type": 2, "data": "ok"}]]}}
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("Выберите")

# Объединение пересылки (официальный md не поддерживает складной синтаксис, отображается как список цитат; требует разрешения на оригинальный Markdown, в случае неудачи автоматически возвращается текст)
await qqbot.Send.To("group", gid).MergeForward(nodes)
```

### Потоковая отправка (ново в v5, личные сообщения)

```python
# Однократная потоковая отправка (input_state=10 завершает сразу)
await qqbot.Send.To("user", openid).Stream("Содержание ответа")

# Многократная потоковая отправка
r = await qqbot.stream_message(openid, "Первая часть", input_state=1, msg_id=активный_msg_id)
stream_id = r["data"]["id"]
r = await qqbot.stream_message(openid, "Вторая часть", stream_msg_id=stream_id, index=1, input_state=1)
r = await qqbot.stream_message(openid, "Последняя часть", stream_msg_id=stream_id, index=2, input_state=10)
```

### Отмена сообщения

```python
# Стандартное API-действие: автоматически маршрутизируется по источнику сообщения (группа/личное сообщение/канал/личное) к соответствующему конечному пункту отмены
await qqbot.Api.delete_message(message_id)
```

Адаптер автоматически регистрирует отправку и получение сообщений, не требуя ручного передачи group_id/channel_id; при отсутствии контекста возвращается `retcode=10003`.

## Стандартные API-действия OneBot12 (ново в v5)

```python
# Информация о роботе
result = await qqbot.Api.get_self_info()

# Управление группой
result = await qqbot.Api.get_group_info(group_openid)          # {group_id, group_name}
result = await qqbot.Api.get_group_member_list(group_openid)   # автоматическая пагинация и объединение
result = await qqbot.Api.get_group_member_info(group_openid, member_openid)

# Канал
result = await qqbot.Api.get_guild_list()
result = await qqbot.Api.get_guild_info(guild_id)
result = await qqbot.Api.get_guild_member_list(guild_id)
result = await qqbot.Api.get_channel_list(guild_id)
result = await qqbot.Api.get_channel_info(guild_id, channel_id)
await qqbot.Api.set_channel_name(guild_id, channel_id, "Новое название")
await qqbot.Api.leave_channel(guild_id, channel_id)            # удаление подканала

# Основные действия
result = await qqbot.Api.get_status()   # {"good": bool, "bots": [...]}
result = await qqbot.Api.get_version()  # {"impl": "ErisPulse-QQBotAdapter", "onebot_version": "12"}

# Множественные аккаунты
result = await qqbot.Api.Using("account2").get_self_info()
```

Поддерживаемые стандартные действия: `get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`. Действия, которые не поддерживаются, возвращают `retcode=10002` (например, `get_friend_list`, так как у QQ нет соответствующего API).

## Запросы и операции (Request DSL, ново в v5)

Событие `GROUP_JOIN_REQUEST` (запрос на вступление в группу) преобразуется в событие `request` однозначного взаимодействия, поддерживающее стандартизированное одобрение:

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join_request(event):
    if event.get("platform") != "qqbot":
        return
    # автоматическое одобрение
    result = await event.approve()
    # или отклонение: await event.reject(comment="не соответствует условиям")
    # или указание аккаунта: await qqbot.Request(event["request_id"]).Using("account2").accept()
```

- `request_id` = официальный `join_request_id`
- адаптер автоматически кэширует контекст запроса (группа/открытый идентификатор участника), при выполнении маршрутизируется к `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`
- отклонение может сопровождаться `reject_reason`; при истечении срока контекста возвращается `retcode=34001`

Также можно напрямую вызывать методы платформы:

```python
await qqbot.approve_group_join(group_openid, member_openid, join_request_id, approve=True)
await qqbot.approve_group_join(group_openid, member_openid, approve=False, reject_reason="причина")
```

## Пользовательские методы API платформы

Адаптер предоставляет полный набор API QQ (первый параметр — ID цели, `account_id` — необязательный, для указания аккаунта):

### Робот / Взаимодействие
`get_me()`、`reply_interaction(interaction_id, code=0)`

### Канал (Guild)
`get_guilds()`、`get_guild(guild_id)`、`mute_guild_all(guild_id, mute_seconds)`、
`get_guild_roles` / `create_guild_role` / `update_guild_role` / `delete_guild_role`、
`get_guild_api_permission`、`demand_guild_api_permission(guild_id, channel_id, path, method, desc)`

### Подканал (Channel)
`get_channels`、`get_channel`、`create_channel(guild_id, name, type=0, ...)`、`update_channel(channel_id, name=..., ...)`、`delete_channel`、
`get_channel_pins`、`pin_message`、`unpin_message`

### Участники канала
`get_guild_members`、`get_guild_member`、`mute_guild_members` (массово/всей группе), `mute_guild_member`、
`add_guild_member_role` / `remove_guild_member_role`、`kick_guild_member`

### Разрешения / Объявления / Реакции
`get_channel_role_permissions`、`update_channel_role_permissions`、`get_channel_member_permissions` (расширенное действие `qqbot.get_channel_member_permissions`)、`update_channel_member_permissions`、`create_announce`、
`add_reaction`、`delete_reaction`、`get_reaction_users`

### Расписания / Темы / Аудио
`get_schedules`、`get_schedule`、`create_schedule`、`update_schedule`、`delete_schedule`、
`get_threads`、`get_thread`、`publish_thread(channel_id, title, content, format=3)`、`delete_thread`、
`control_audio(channel_id, audio_url, text, status)`、`mic_online`、`mic_offline`

### Управление группами (v2, **некоторые интерфейсы доступны только для роботов в белом списке**)
```python
await qqbot.get_group_info_raw(group_openid)          # Информация о группе
await qqbot.get_group_bot_state(group_openid)         # Состояние робота в группе
await qqbot.get_group_members(group_openid)           # Список участников (с next_cursor)
await qqbot.get_group_member(group_openid, member_openid)
await qqbot.batch_remove_group_members(group_openid, [member_openid], add_to_blacklist=False)
await qqbot.get_group_member_blacklist(group_openid)
await qqbot.update_group_member_blacklist(group_openid, "add", [member_openid])
await qqbot.get_group_join_requests(group_openid)     # Список запросов на вступление в группу
await qqbot.approve_group_join(...)                   # Одобрение запроса на вступление
await qqbot.get_group_restrict_setting(group_openid)  # Настройки запрета
await qqbot.set_group_restrict(group_openid, [{"op": "add", "member_openid": "...", "mute_expire_at": 123}])
# Стратегии одобрения вступления
await qqbot.get_join_approval_strategies()
await qqbot.create_join_approval_strategy(strategy_dict)
await qqbot.update_join_approval_strategy(strategy_id, **fields)
await qqbot.delete_join_approval_strategy(strategy_id)
await qqbot.execute_join_approval_strategy(strategy_id)
await qqbot.update_join_approval_strategy_whitelist(strategy_id, "add", [user_ids])
```

### Пользовательские меню / Панели команд (ново в v5)
```python
# Глобальное пользовательское меню (действует только для C2C; подменю максимум 5, не вложенные)
menu_items = [
    {"type": "send_message", "content": {"label": "Помощь", "content": "/help"}},
    {"type": "link", "content": {"label": "Официальный сайт", "content": "https://example.com"}},
]
await qqbot.update_custom_menu(menu_items)
result = await qqbot.get_custom_menu()

# Панель команд (scope: c2c/group/channel/dm; максимум 20 на робота)
await qqbot.create_command_panel("c2c", [
    {"type": "command", "content": {"label": "Погода", "content": "/weather"}},
    {"type": "link", "content": {"label": "Больше", "content": "https://example.com"}},
], remark="Заметка панели", target_type="all")
await qqbot.get_command_panels("c2c")
await qqbot.get_command_panel(panel_id)
await qqbot.update_command_panel(panel_id, items)
await qqbot.delete_command_panel(panel_id)
await qqbot.update_command_panel_targets(panel_id, "add", user_openids=[...])
```

## WebSocket-соединение

### Процесс подключения

1. appId + clientSecret получают access_token (POST https://bots.qq.com/app/getAppAccessToken)
2. Через GET /gateway/bot получают адрес шлюза (при настройке gateway_url используется напрямую)
3. Получают OP_HELLO (op=10), получают интервал心跳
4. Отправляют OP_IDENTIFY (op=2) для аутентификации (intents поддерживает комбинацию битовых операций)
5. Получают READY, получают session_id и bot_id, отправляют событие connect meta
6. Цикл心跳 (op=1) и распределение событий (op=0)

### Переподключение при разрыве

- Максимум 50 попыток переподключения, экспоненциальная задержка `min(5 * 2^n, 300)` секунд
- Получение OP_RECONNECT (op=7) сохраняет сессию (Resume); OP_INVALID_SESSION (op=9) переподключается с идентификацией
- При нормальной отправке и получении автоматически сбрасывается счетчик переподключения

### Управление токеном

- access_token действителен 7200 секунд, **автоматически обновляется за 45 секунд до истечения срока** (ленивая проверка при запросе)
- При неудачном обновлении автоматически повторяется 3 раза (возрастающая задержка)
- Заголовки запроса: `Authorization: QQBot {token}` + **`X-Union-Appid: {appid}`** (ново в v5)

## Webhook-подключение (ново в v5)

Установка mode аккаунта в `webhook` позволяет использовать HTTP-вызов обратной связи для получения событий:

```toml
[QQBot_Adapter.accounts.mybot]
appid = "..."
secret = "..."
mode = "webhook"
webhook_path = "/webhook"    # При наличии нескольких webhook аккаунтов автоматически добавляется имя аккаунта для избежания конфликтов
```

- Адаптер регистрирует HTTP-маршруты через ErisPulse router, в логах запуска выводится полный URL обратной связи
- **Проверка подписи Ed25519**: seed = secret циклически заполняется до 32 байт; проверка подписи `X-Signature-Ed25519` для `X-Signature-Timestamp + body`
- Автоматически обрабатывает op=13 проверку подписи handshake (валидация URL обратной связи) и op=0 распределение событий
- Зависит от библиотеки `cryptography` (установлена вместе с адаптером)

## Подписка на события и система openid

1. QQBot использует систему openid вместо QQ-номеров, идентификаторы пользователей/групп являются строками openid
2. Групповые сообщения по умолчанию получают только при упоминании робота (событие `GROUP_AT_MESSAGE_CREATE`)
3. **Получение всех групповых сообщений**: необходимо включить соответствующие разрешения в [QQ Open Platform](https://q.qq.com/) на панели управления роботом (без API можно настроить); после включения неупомянутые групповые сообщения будут поступать через `GROUP_MESSAGE_CREATE`, адаптер полностью поддерживает преобразование (отмечается `qqbot_is_at_message=false`; если сообщение содержит упоминание робота, автоматически распознается как упоминание)
4. **Упоминание**: Упоминание в QQ содержится в имени события, и упоминание в групповом сообщении имеет формат `<@{group_openid}>` (отличается от bot_id в READY). Адаптер автоматически анализирует оба стиля упоминания и вставляет/нормализует упоминание робота, обеспечивая доступность `on_at_message()`/`is_at_message()`. Также автоматически изучает openid робота в каждой группе, обеспечивая распознавание упоминаний в `GROUP_MESSAGE_CREATE` при режиме получения всех групповых сообщений (оригинальный openid сохраняется в упоминании `data.qqbot_openid`)
5. Ответное сообщение: для групповых/личных сообщений необходимо включать `msg_id` или `event_id`, адаптер автоматически кэширует и добавляет
6. `event_id` не может использоваться вместе с мультимедиа (ограничение официального API), адаптер автоматически обрабатывает понижение уровня
7. Отправка может вызвать проверку, результат уведомляется через события `qqbot_audit_pass` / `qqbot_audit_reject`
8. При выходе программы вызовите `shutdown()` для освобождения ресурсов

## Примеры использования

### Обработка групповых сообщений (детектирование упоминания)

```python
from ErisPulse.Core.Event import message

@message.on_at_message()
async def handle_at(event):
    if event.get("platform") != "qqbot":
        return
    text = event.get_text()
    if text == "签到":
        await event.reply("已签到")
```

### Обработка кнопочных взаимодействий

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("detail_type") != "qqbot_interaction":
        return
    button_id = event.get("qqbot_button_id")
    await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
    if button_id == "confirm":
        await qqbot.Send.To("group", event.get("group_id")).Text("已确认")
```

### Запуск множественных аккаунтов

```toml
[QQBot_Adapter.accounts.bot_a]
appid = "A_APPID"
secret = "..."
enabled = true

[QQBot_Adapter.accounts.bot_b]
appid = "B_APPID"
secret = "..."
mode = "webhook"
enabled = true
```

Два аккаунта запускаются параллельно: bot_a использует WebSocket, bot_b использует Webhook, они не влияют друг на друга.