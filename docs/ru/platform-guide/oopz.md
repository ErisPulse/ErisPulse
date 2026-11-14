# Документация по особенностям платформы Oopz

## Информация о документе

| Параметр | Значение |
|---|---|
| Версия модуля | 0.1.0 |
| Идентификатор платформы | `oopz` |
| Сопровождающие | Команда ErisPulse |
| Последнее обновление | 2026-11-13 |

> [!IMPORTANT]
> Данный проект никак не связан с Oopz (нет официального разрешения, нет официального сотрудничества, официальная поддержка не предоставляется). У Oopz нет официальной бот-платформы; данный адаптер основан на протоколе, полученном сообществом путём реверс-инжиниринга, и подключается **от имени аккаунта пользователя**, поэтому может перестать работать в любой момент — используйте второй (запасной) аккаунт. Подробнее см. заявление и предупреждение о рисках в README.

## Основная информация

- Класс адаптера: `OopzAdapter` (entry-point `oopz`)
- Способ подключения: WebSocket (`wss://ws.oopz.cn`) + REST-шлюз (`https://gateway.oopz.cn`), заголовки запросов с RSA-подписью + JWT
- Учётные данные: «либо логин-пароль, либо токен» — `password` (номер телефона + пароль + приватный ключ клиента, автоматический вход и продление, **рекомендуется**) или `token` (набор из четырёх компонентов: uid/JWT/device_id/приватный ключ; запасной вариант только на случай, когда вход по паролю блокируется риск-контролем; при истечении срока JWT требуется ручное повторное извлечение)
- Мультиаккаунтность: поддерживается (`[Oopz_Adapter.accounts.<name>]`), источник события помечается через `self.account_id`
- Мягкая зависимость от фреймворка: ErisPulse ≥ 2.7.1

## Модель сессий

| Цель ErisPulse | Понятие Oopz | Описание |
|---|---|---|
| `Send.To("group", <ID канала>)` | Канал (channel) | Домен автоматически определяется адаптером через «кэш channel→area + сканирование присоединённых доменов» |
| `Send.To("user", <UID собеседника>)` | Сессия личных сообщений | Автоматически отправляется `PATCH /client/v1/chat/v1/to` для открытия сессии с кэшированием sessionId |
| Поле `guild_id` / семантика guild | Домен (area) | Операции уровня домена выполняются через `get_guild_*` и административные расширения `oopz.*` |

## Соответствие стандарту (0.1.0)

### Спецификация кодов ошибок

| retcode | Значение |
|---|---|
| 0 | Успех |
| 10002 | Неподдерживаемое действие / деградация сегмента сообщения (отправка голоса, видео, файлов, upload_file, keyboard и т.д.) |
| 10003 | Отсутствующие/недопустимые параметры (например, не удаётся определить домен, к которому относится канал) |
| 33001 | Сетевая ошибка / ограничение частоты (при 429 учитывается Retry-After с одним повтором) |
| 34100 | Платформа вернула ошибку (исходный ответ в `oopz_raw`) |
| 34005 | Аккаунт не разрешён (не настроен или сессия не установлена) |

### Структура ответа

Все ответы содержат `status / retcode / data / message_id / message / oopz_raw`; `message_id` в ответе на отправку берётся из возвращённого платформой `messageId`; `data.self_info.user_id` заполняется в `get_self_info`.

### Полнота полей событий

- Во всех событиях обязательны `id / time / type / detail_type / sub_type / platform / self`, при этом `oopz_raw` + `oopz_raw_type` присутствуют всегда
- События сообщений на верхнем уровне обязательно содержат `message_id`; строки временных меток в микросекундах нормализуются в секунды
- `id` события дедуплицируется в рамках аккаунта (`<account>:<тип>:<платформенный ID>`)
- Неизвестные события преобразуются в `type="unknown"` + `warning` и не отбрасываются молча
- Внутренние кадры протокола (рукопожатие/аутентификация/heartbeat/подписка) не порождают платформенных событий

### Семантика деградации

- Сегменты отправки `voice/audio/video/file` → `retcode=10002` (платформа поддерживает загрузку только изображений), без выброса исключений
- Цель отправки `guild` → `retcode=10003` (укажите канал)
- Недействительный JWT в режиме token → `retcode=34100` с предложением обновить учётные данные; в режиме password автоматически выполняется повторный вход и одна повторная попытка

## Поддерживаемые типы отправки сообщений

| Метод | Реализация на платформе |
|---|---|
| `Text` | Текст (двойная запись text/content) |
| `Image` | Загрузка через подписанный билет COS (только изображения), текстовый плейсхолдер `![IMAGEw{w}h{h}]({fileKey})` + attachments |
| `At / AtAll / Reply` | `mentionList` / `isMentionAll` / `referenceMessageId` |
| Модификатор `Important()` | Стиль объявления `styleTags=["IMPORTANT"]` |
| `Recall(messageId)` | `recallGim` (канал) / `recallIm` (личные сообщения, отзывать можно только собственные сообщения) |
| `Raw_ob12` | Сегменты OneBot12 → payload платформы (text/mention/mention_all/reply/image; остальные сегменты деградируют в 10002) |
| Voice/Video/File/Keyboard | Не поддерживается → 10002 |

## Стандартные действия API (ApiDSL)

### Поддерживаемые стандартные действия

`get_self_info`, `get_user_info`, `get_friend_list`, `get_group_info` (объединённая информация о канале и его домене), `get_group_list` (плоский список каналов присоединённых доменов), `get_guild_info`, `get_guild_list`, `get_channel_list`, `get_guild_members`, `delete_message` (требуется контекст `channel_id` или `user_id`), `get_file` (URL вложения → base64), `leave_guild`, `get_status`, `get_version`, `get_supported_actions`

### Неподдерживаемые стандартные действия (retcode=10002)

`send_message` (используется Send DSL), `upload_file`, `get_latest_events`, `set_group_name`, `set_group_admin`, `set_group_leave`, `set_group_card`, `leave_group`, `leave_channel`

### Расширенные действия платформы (oopz.*)

| Действие | Обязательные параметры | Описание |
|---|---|---|
| `oopz.create_channel` | `area_id, name` | Необязательные: `channel_type/group_id/secret/max_member` |
| `oopz.delete_channel` | `area_id, channel_id` | |
| `oopz.mute_member` / `oopz.unmute_member` | `area_id, user_id` | Мут (запрет сообщений), количество минут `duration` автоматически приводится к ближайшей ступени (5 минут/1 час/1 день/3 дня/7 дней) |
| `oopz.mute_mic` / `oopz.unmute_mic` | `area_id, user_id` | Мут микрофона |
| `oopz.kick_member` | `area_id, user_id` | Исключение из домена |
| `oopz.block_user` / `oopz.unblock_user` | `area_id, user_id` | Чёрный список домена |
| `oopz.get_area_members` | `area_id` | Необязательные: `offset_start/offset_end` |
| `oopz.get_assignable_roles` | `area_id, target_id` | Назначаемые роли |
| `oopz.assign_role` / `oopz.revoke_role` | `area_id, target_id, role_id` | Внутри считывается полный список ролей, затем отправляется целиком |
| `oopz.react_message` / `oopz.unreact_message` | `message_id, channel_id, emoji` | Необязательные: `user_id` (личные сообщения)/`area_id` |
| `oopz.get_reactions` | `message_id` | Необязательные: `message_ids` (≤50)/`user_id` |
| `oopz.get_reaction_persons` | `message_id, channel_id, emoji` | Пагинация пользователей, оставивших реакцию |
| `oopz.top_message` | `message_id, area_id, channel_id` | Закрепление/снятие (`cancel=True`) |
| `oopz.get_history_messages` | `area_id, channel_id` | Необязательный `size` (по умолчанию 50) |
| `oopz.get_friend_requests` | — | Список заявок в друзья |
| `oopz.respond_friend_request` | `target, friend_request_id, agree` | Одобрение (обычно используется Request DSL) |

## Обработка заявок в друзья

- Событие: `request/friend`, `request_id` — **составной stateless-ключ** `<target>:<friendRequestId>`
- `event.approve()` / `event.reject()` → POST `/client/v1/friendship/v1/response`
- Единый гомогенный эндпоинт, таблица хранения контекста типа запроса не требуется

## Возвращаемое значение методов отправки

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "14283..."},
  "message_id": "14283...",
  "message": "",
  "oopz_raw": {"messageId": "14283...", "timestamp": "..."}
}
```

## Специфические типы событий

- Дополнительные поля событий сообщений: `oopz_area_id`, `guild_id` (сообщения каналов); `oopz_reference_message_id` (ответы)
- Расширения уведомлений: `oopz_edited_text`, `oopz_emoji`, `oopz_reaction_type`, `oopz_persons`, `oopz_from_channel`, `oopz_channel_name`, `oopz_channel_type`, `oopz_area_name`, `oopz_role_id`, `oopz_role_name`, `oopz_ban_until`, `oopz_login_state`
- Удобные методы `EventMixin`: `get_raw_event()`, `get_area_id()`, `get_edited_text()`, `get_emoji()`, `get_reaction_type()`, `get_voice_persons()`