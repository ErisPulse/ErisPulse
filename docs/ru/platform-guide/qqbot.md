# Документация по функциям платформы QQBot

QQBotAdapter — это адаптер, построенный на основе протокола QQ-бота (QQ OpenAPI), объединяющий функции для чатов в группах, личных сообщений и каналов, предоставляющий стандартные события OneBot12, стандартные API-действия и интерфейсы для выполнения запросов.

## Информация о документации

- Версия соответствующего модуля: 5.0.0
- Ответственный: ErisPulse

## Основная информация

- Краткое описание платформы: Официальный интерфейс разработки ботов QQ, поддерживает различные сценарии, такие как групповые чаты, личные сообщения, каналы и т.д.
- Имя адаптера: QQBotAdapter
- Способ подключения: **WebSocket-длинное соединение** (по умолчанию) или **Webhook HTTP-обратный вызов** (по настройкам аккаунта, проверка подписи Ed25519)
- Способ аутентификации: appId + clientSecret для получения access_token (7200 секунд, автоматическое обновление за 45 секунд до истечения срока действия)
- Корневой адрес API: `https://api.bot.qq.com` (начиная с v5 официальный единый домен, sandbox устарел)
- Совместимость с OneBot12: полная поддержка отправки и получения сообщений, событий, **стандартных API-действий**, **операций запроса**
- Множественные аккаунты: поддерживается, произвольные аккаунты в разделе `accounts` могут работать параллельно (можно смешивать режимы websocket/webhook)

## Конфигурация

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # Глобально: подписанные события intents (JSON массив, поддерживает имена событий)

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # ID приложения QQ-бота (обязательно)
secret = "YOUR_CLIENT_SECRET"        # Секретный ключ клиента QQ-бота (обязательно)
mode = "websocket"                   # Способ получения событий: websocket / webhook
bot_id = ""                          # ID бота (оставьте пустым для автоматического получения; можно вручную указать для использования в Using())
gateway_url = ""                     # URL WebSocket-шлюза (оставьте пустым для динамического получения через /gateway/bot)
api_base_url = "https://api.bot.qq.com"  # Корневой URL API (можно настроить для прокси)
webhook_path = "/webhook"            # Путь обратного вызова webhook (действует при mode=webhook)
enabled = true
```

**Версия v5 — критические изменения:**
- Официальный единый URL `api.bot.qq.com`, конфигурация `sandbox` устарела (старые настройки автоматически переносятся и игнорируются)
- Старая плоская конфигурация (appid/secret непосредственно в `[QQBot_Adapter]`) автоматически переносится в `accounts.default`
- Фреймворк является **опциональной зависимостью**: установка адаптера не влияет на версию фреймворка; в процессе выполнения проверяется наличие `ErisPulse>=2.7.1` и выводится соответствующее уведомление

**Описание intents (поддерживает номера позиций или имена событий):**

| Позиция | Имя события | Описание |
|----|--------|------|
| 0 | GUILDS | Изменения каналов |
| 1 | GUILD_MEMBERS | Изменения участников канала |
| 9 | GUILD_MESSAGES | Сообщения канала (внутриканальные) |
| 12 | DIRECT_MESSAGE | Личные сообщения канала |
| 24 | GROUP_MEMBER | Изменения участников группы (ново в v5) |
| 25 | GROUP_AND_C2C_EVENT | Сообщения упоминания в группе и личные сообщения |
| 26 | INTERACTION | Взаимодействие (кнопки и т.д.) |
| 27 | MESSAGE_AUDIT | События проверки сообщений |
| 30 | PUBLIC_GUILD_MESSAGES | Сообщения канала (внешние каналы) |

## Отправка сообщений

### Базовая отправка

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")

# Упоминание в чате (автоматически использует формат <qqbot-at-user id="x" />)
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@你")

# Сообщение в канале (автоматически использует формат <@user_id>)
await qqbot.Send.To("channel", channel_id).Text("Сообщение в канале")

# Ответ на сообщение (автоматически включает msg_id, не нужно использовать Reply вручную)
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("Содержимое ответа")

# Мультимедиа (URL / локальный путь / бинарные данные; файлы больше 5 МБ загружаются по частям)
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")

# Markdown (в виде исходного текста / шаблона)
await qqbot.Send.To("group", gid).Markdown("# Заголовок\n- Список")
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "Уведомление"}])

# Клавиатура (автоматически устанавливается тип markdown и добавляется bot_appid)
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("Выберите опцию")

# Потоковое сообщение (личный чат)
await qqbot.Send.To("user", openid).Stream("Содержимое ответа")

# Множественные аккаунты
await qqbot.Send.Using("account2").To("group", gid).Text("От второго бота")
```

## OneBot12 стандартный API-действия

```python
result = await qqbot.Api.get_self_info()                     # Информация о боте
result = await qqbot.Api.get_group_info(group_openid)        # Информация о группе
result = await qqbot.Api.get_group_member_list(group_openid) # Список участников группы (автоматическая пагинация)
result = await qqbot.Api.get_guild_list()                    # Список каналов
result = await qqbot.Api.get_channel_list(guild_id)          # Список подканалов
await qqbot.Api.delete_message(message_id)                   # Отмена сообщения (автоматический маршрут по источнику сообщения)
result = await qqbot.Api.get_status()                        # Статус работы нескольких аккаунтов
result = await qqbot.Api.Using("account2").get_self_info()   # Указание аккаунта
```

Поддерживаемые стандартные действия: `get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`. Действия, которые не поддерживаются, возвращают `retcode=10002`.

## Операции с запросами (одобрение заявки на вступление в группу)

Событие `GROUP_JOIN_REQUEST` преобразуется в событие `request` по стандарту OneBot12 и поддерживает стандартизованное одобрение:

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join(event):
    if event.get("platform") == "qqbot":
        await event.approve()                  # Принять
        # await event.reject(comment="Причина")   # Отклонить
```

`request_id` = `join_request_id` от официального API, адаптер автоматически кэширует контекст заявки и маршрутизирует запрос на `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}`.

## @Механизм обнаружения бота (важно)

Факт упоминания бота в QQ официально передаётся через имя события, а упоминание пользователя в группе имеет вид `<@{openid пространства группы}>` (это **не** относится к той же системе идентификаторов, что и bot_id, возвращаемый READY). Адаптер автоматически обрабатывает:

1. **Анализ меток**: `<@openid>` и `<qqbot-at-user>` оба стиля анализируются как упоминания (упоминания не остаются в тексте)
2. **Нормализация имён**: если имя бота, возвращённое `/users/@me`, совпадает с именем в массиве упоминаний, упоминание нормализуется как bot_id (оригинальный openid сохраняется в `data.qqbot_openid`)
3. **Обучение openid**: автоматически обучается openid бота в каждой группе, используется для распознавания упоминаний в режиме "получать все сообщения из группы"
4. **Гарантия вставки**: `GROUP_AT_MESSAGE_CREATE` / `AT_MESSAGE_CREATE` гарантируют наличие упоминания бота

Таким образом, `on_at_message()` / `event.is_at_message()` можно использовать напрямую на платформе qqbot. После включения разрешения "получать все сообщения из группы" упоминания будут отправляться через `GROUP_MESSAGE_CREATE` (событие `GROUP_AT_MESSAGE_CREATE` больше не поступит), адаптер также способен распознавать упоминания.

## Семейство методов платформенных API

Адаптер предоставляет полный набор официальных API QQ (подробности см. в файле platform-features.md репозитория адаптера):

- **Бот**: `get_me()`, `reply_interaction()`
- **Каналы**: `get_guilds/get_guild/mute_guild_all/управление_ролями/api_permission`
- **Подканалы**: `get_channels/get_channel/create_channel/update_channel/delete_channel/pins`
- **Участники канала**: `get_guild_members/get_guild_member/mute/roles/kick`
- **Разрешения/реакции/планы/посты/аудио**: полный набор методов
- **Групповое управление** (некоторые интерфейсы доступны только для ботов из белого списка): `get_group_members/get_group_bot_state/черный_список/входящие_запросы/запрет_речи/стратегии_одобрения`
- **Панели меню**: `get_custom_menu/update_custom_menu/CRUD_панелей_команд`
- **Мультимедиа**: `_upload_media` (URL/путь/бинарные данные, автоматическое разделение на части при размере более 5 МБ), `stream_message` (потоковые сообщения)

## WebSocket / Webhook подключение

### Поток WebSocket

1. appId + clientSecret для получения access_token (автоматическое обновление за 45 с до истечения срока действия, неудача повторяется 3 раза)
2. Используя `GET /gateway/bot` динамически получите адрес шлюза (при настройке `gateway_url` используйте его напрямую)
3. OP_HELLO → Identify/Resume → READY (получение session_id и bot_id) → цикл поддержания соединения
4. Переподключение при разрыве: максимум 50 попыток, экспоненциальная задержка `min(5 * 2^n, 300)` секунд; OP_RECONNECT сохраняет сессию

### Режим Webhook

После установки режима `mode = "webhook"` для аккаунта, через маршрутизатор ErisPulse зарегистрируйте HTTP-маршруты:

- Верификация подписи Ed25519 (семя = secret, заполненное до 32 байт), проверка `X-Signature-Ed25519` для `X-Signature-Timestamp + body`
- Автоматическая обработка рукопожатия верификации подписи op=13 и распределение событий op=0
- Зависимость от библиотеки `cryptography` (устанавливается вместе с адаптером)

## Описание кодов ошибок

| retcode | Описание |
|---------|----------|
| 0 | Успешно |
| 10001 | Отсутствуют параметры |
| 10002 | Действие не поддерживается |
| 10003 | Цель/учетная запись не может быть определена |
| 32000 | Время ожидания запроса истекло |
| 33000 | Аномалия сети/вызов API |
| 34001 | Запрос не существует или просрочен (Request DSL) |
| 34100 | Не удалось загрузить медиафайл |
| 34000+ | Ошибка бизнес-процесса платформы (прозрачный код от официального источника) |

## Использование примеров

### Обработка групповых сообщений (по @)

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

### Обработка взаимодействий

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") == "qqbot_interaction":
        await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
        button_id = event.get("qqbot_button_id", "")
        # Обработка кнопки...
```

### Запуск нескольких аккаунтов

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