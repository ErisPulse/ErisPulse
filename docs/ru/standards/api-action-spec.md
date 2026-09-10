# Стандарт действий API ErisPulse

Данный документ определяет **единый интерфейс для действий API OneBot12** в адаптерах ErisPulse, позволяющий разработчикам модулей писать код, ориентированный на стандартный интерфейс, а адаптер отвечает за сопоставление с оригинальными API платформы.

> **Охват**: В стандарте OneBot12, `ApiDSL` предоставляет строго типизированные методы для работы с пользователями, группами, каналами (Guild), сообщениями и мета-данными. Метод `send_message` реализован через `SendDSL.Raw_ob12`. Действия с файлами (`upload_file`, `get_file`, фрагментация) поддерживаются только в пониженном режиме, см. §3.5. Расширения платформы вызываются через `Api.call("prefix.action", ...)`. Структура параметров и возвратов соответствует спецификации OneBot12 (см. `onebot/specs/interface/` в репозитории).

## 1. Обоснование

В ErisPulse форматы сообщений и событий полностью соответствуют стандарту OneBot12, но **вызовы действий API** (например, получение информации о пользователе, список групп, удаление сообщения и т.д.) ранее не были унифицированы — разработчики модулей должны были писать отдельный код `call_api` для каждой платформы.

`ApiDSL` решает эту проблему, предоставляя строго типизированные стандартные методы действий:

```
Модульный код (унифицированный для всех платформ)   Адаптер (платформа-специфичный)
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  call_api адаптера / переопределение
adapter.Api.get_group_list()      →  call_api адаптера / переопределение
adapter.Api.delete_message("id")  →  call_api адаптера / переопределение
```

## 2. Трехуровневая параллельная структура DSL

Адаптер ErisPulse имеет три параллельных внутренних класса DSL, каждый со своей задачей:

```
BaseAdapter
├── Send(SendDSL)       ← Отправка сообщений (Text/Image/Raw_ob12)
├── Request(RequestDSL)  ← Обработка запросов (accept/reject)
└── Api(ApiDSL)          ← Стандартные API-действия (пользователи/группы/каналы/управление сообщениями/файлы/мета)★
```

| DSL | Задача | Стиль методов | Возвращаемое значение |
|-----|------|---------|--------|
| `Send` | Отправка сообщений | Цепочка + `asyncio.Task` | Стандартный ответ |
| `Request` | Обработка событий запросов | `asyncio.Task` | Стандартный ответ |
| `Api` | Запросы/управление | `async` методы | Стандартный ответ |

## 3. Список стандартных действий

### 3.1 Действия, связанные с пользователями

| Метод | OB12 действие | Параметры | Возвращаемые данные |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | Нет | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | Нет | `list[get_user_info ответ]` |

### 3.2 Действия, связанные с группами

| Метод | OB12 действие | Параметры | Возвращаемые данные |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | Нет | `list[get_group_info ответ]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info ответ]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | Нет |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | Нет |

### 3.3 Управление сообщениями

| Метод | OB12 действие | Параметры | Описание |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | Удаление/отмена сообщения |

> **Отправка сообщений** (`send_message`) обрабатывается `SendDSL` через `Raw_ob12`, и не включается в `ApiDSL`.

### 3.4 Действия, связанные с каналами (Guild)

Система каналов OneBot12 делится на два уровня: **канал (guild)** и **подканал (channel)**.

| Метод | OB12 действие | Параметры | Возвращаемые данные |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | Нет | `list[get_guild_info ответ]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | Нет |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info ответ]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | Нет |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info ответ]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | Нет |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info ответ]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | Нет |

> Система каналов и групп (group) независимы друг от друга: платформы Discord, QQ, Kook и др. реализуют API каналов, традиционные QQ, WeChat реализуют API групп, обе системы могут существовать одновременно или только одна из них.

### 3.5 Действия с файлами

> [!WARNING]
> **Модель файлов (file_id в двух частях) в ErisPulse является "пониженной"**:
> ErisPulse не использует модель отправки файлов "сначала загрузить, получить file_id, затем ссылаться" — модули отправляют файлы с помощью `SendDSL.File(file, filename)` (URL / путь / байты **отправляются напрямую** во время отправки, см. [спецификацию методов отправки](send-method-spec.md)).
> Действия `upload_file`, `get_file`, фрагментация зависят от специфичных для платформы возможностей `file_id`, **имеют низкую универсальность**; реализуются только если у адаптера есть такая возможность, встроенные адаптеры **не реализуют и не рекомендуют реализовывать**, вызов обычно возвращает `retcode=10002`.
> При необходимости пересылки файлов между платформами, используйте `SendDSL.File`, не полагайтесь на file_id.
>
> **Перспектива**: Стандартизация модели `file_id` до уровня фреймворка — это будущее, в текущей версии не предоставляется.

Отправка целого файла (маленькие файлы):

| Метод | OB12 действие | Параметры | Возвращаемые данные |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

Параметр `type` в `upload_file`:
- `"url"`: через URL (требуется `url`)
- `"path"`: через локальный путь (требуется `path`)
- `"data"`: через бинарные данные (требуется `data`)

#### 3.5.1 Фрагментированная передача (большие файлы, в рамках пониженного режима)

Действия OneBot12 с фрагментами различаются по `stage`. `ApiDSL` разделяет три/два этапа одного действия в отдельные методы (`offset` — смещение в байтах, `data` в JSON — Base64); таблица предназначена только для справки, адаптер не должен и не должен реализовывать:

**Три шага фрагментированной загрузки**: `prepare` → `transfer` (циклическая передача фрагментов) → `finish`

| Метод | Этап | Параметры | Возвращаемые данные |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id` (используется в периоде передачи) |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | Нет |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str` (проверка целостности файла) | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**Два шага фрагментированной загрузки**: `prepare` → `transfer` (циклический получение фрагментов)

| Метод | Этап | Параметры | Возвращаемые данные |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data` (байты текущего фрагмента) |

### 3.6 Мета-действия

Мета-действия не привязаны к конкретному аккаунту и не требуют `Using()` для указания бота.

| Метод | OB12 действие | Параметры | Возвращаемые данные |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | Массив объектов событий (без мета-событий) |
| `get_supported_actions()` | `get_supported_actions` | Нет | `list[str]` поддерживаемые названия действий |
| `get_status()` | `get_status` | Нет | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | Нет | `impl`, `version`, `onebot_version` |

### 3.7 Общие расширенные действия

| Метод | Описание |
|------|------|
| `call(action, **params)` | Экстренный доступ к расширенным действиям платформы, соответствует правилу именования расширений OB12 `{prefix}.{action}` |

## 4. Способы использования

### 4.1 Основные вызовы

```python
from ErisPulse import adapter

# Получение информации о пользователе (унифицированный для всех платформ)
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"Имя пользователя: {user_name}")

# Получение списка групп
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# Отмена сообщения
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Указание аккаунта бота (режим нескольких аккаунтов)

```python
# Выполнение операций с указанным аккаунтом бота
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 Расширенные действия платформы

```python
# Вызов специфичного расширенного действия платформы (рекомендуется использовать {prefix}.{action})
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 Использование в обработчиках событий

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # Получение подробной информации об отправителе
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"Привет, {user_name}!")
```

## 5. Реализация адаптера

### 5.1 Поведение по умолчанию (без настроек)

Стандартная реализация `ApiDSL` передает имя стандартного действия как `endpoint` напрямую в `adapter.call_api()`:

```python
# Стандартная реализация ApiDSL эквивалентна:
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**Сценарии применения**: Когда базовый API адаптера сам следует протоколу стандартных действий OneBot12, `call_api` естественно поддерживает имена стандартных действий (например, напрямую подключается к сервису, соответствующему этому протоколу).

### 5.2 Переопределение стандартных методов (сопоставление с оригинальными API платформы)

Адаптер может переопределить отдельные стандартные методы, сопоставляя их с оригинальными API платформы:

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """Реализация стандартных API действий MyPlatform"""

        async def get_user_info(self, user_id: str) -> dict:
            # Сопоставление с оригинальным API платформы
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34600, message="Пользователь не существует")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 Не поддерживаемые действия

Не покрытые стандартные методы идут по умолчанию (передаются в `call_api`). Если `call_api` также не поддерживает это действие, следует вернуть стандартный ответ об ошибке:

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"Действие не поддерживается: {endpoint}")
    # ... вызов API платформы
```

Разработчики модулей могут определять поддержку по `retcode` в возвращаемом значении:

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("Платформа не поддерживает получение списка друзей")
```

## 6. Формат ответа

Все методы `ApiDSL` возвращают стандартный формат ответа API (см. [стандарт ответа API](api-response.md)):

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **Важно**: У методов получения информации поле `message_id` — пустая строка (только у методов отправки сообщений есть `message_id`).

## 7. Отношения с SendDSL и RequestDSL

| Сценарий | Используемый DSL | Пример |
|------|---------|------|
| Отправка сообщений | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| Согласие/отказ в запросе | `Request` | `adapter.Request("req_id").accept()` |
| Получение информации о пользователе/группе | `Api` | `adapter.Api.get_user_info("123")` |
| Отмена сообщения | `Api` | `adapter.Api.delete_message("msg_id")` |
| Выход из группы | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. Проверочный список реализации адаптера

### Стандартные действия
- [ ] `call_api` может обрабатывать стандартные имена действий (или переопределить соответствующий метод `ApiDSL`)
- [ ] Не поддерживаемые действия возвращают `retcode=10002`
- [ ] Возвращаемые значения соответствуют стандартному формату API
- [ ] Поле `data` содержит поля, определенные в стандарте OB12
- [ ] Платформы с каналами должны реализовать `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] Рекомендуется реализовать мета-действия (`get_status` / `get_version` / `get_supported_actions`)
- [ ] **Отправка файлов через `SendDSL.File` (прямая передача)**; действия с файлами (`upload_file/get_file/фрагментация`) **не обязательны**, реализуются только если у бэкенда есть поддержка `file_id`

### Расширенные действия
- [ ] Расширенные действия платформы используют именование `{prefix}.{action}`
- [ ] Параметры и ответы расширенных действий соответствуют структуре запроса/ответа OB12

## 9. Связанные документы

- [Стандарт ответа API](api-response.md) - стандартный формат ответа API адаптера
- [Спецификация методов отправки](send-method-spec.md) - стандарт именования и параметров методов Send
- [Спецификация действий запросов](request-action-spec.md) - использование DSL Request
- [Стандарт преобразования событий](event-conversion.md) - стандарт формата событий и сегментов сообщений