# Стандартные действия ErisPulse API

> [!TIP]
> **Когда это нужно читать:** Когда вы реализуете стандартные действия API DSL (get_user_info / delete_message и т.д.) в адаптере или вызываете эти стандартные действия между модулями, и вам нужно сверить параметры и поля данных с этой статьей. Если это не требуется, пропустите.

Документ определяет **единый интерфейс стандартных действий OneBot12 API** в адаптере ErisPulse, чтобы разработчики модулей могли программировать с помощью стандартного интерфейса, а адаптер отвечает за отображение на оригинальный API платформы.

> **Охват:** Стандартные действия OneBot12, `ApiDSL` предоставляет методы с сильной типизацией для управления пользователями / группами / каналами (Guild) / сообщениями / мета-данными. Метод `send_message` реализован через `SendDSL.Raw_ob12`. Действия с файлами (upload_file / get_file / фрагментация) поддерживаются только в качестве пониженной совместимости (см. §3.5). Расширения платформы вызываются через `Api.call("prefix.action", ...)`. Параметры и структура возврата действий соответствуют спецификации OneBot12 (в репозитории `onebot/specs/interface/`).

## 1. Дизайн-фон

В ErisPulse форматы сообщений (отправка и получение) и событий полностью соответствуют стандарту OneBot12, но **вызовы API-действий** (например, получение информации о пользователе, получение списка групп, удаление сообщений и т.д.) ранее не были унифицированы — разработчикам модулей приходилось писать разные вызовы `call_api` для каждой платформы.

`ApiDSL` решает эту проблему, предоставляя методы стандартных действий с сильной типизацией:

```
Код модуля (унифицированный для всех платформ)             Реализация адаптера (платформа-специфичная)
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
└── Api(ApiDSL)          ← Стандартные API-действия (пользователи/группы/каналы/управление сообщениями/файлами/мета)★
```

| DSL | Задача | Стиль методов | Возвращаемое значение |
|-----|------|---------|--------|
| `Send` | Отправка сообщений | Цепочка + `asyncio.Task` | Стандартный ответ |
| `Request` | Обработка событий запросов | `asyncio.Task` | Стандартный ответ |
| `Api` | Запросы/управление | `async` методы | Стандартный ответ |

## 3. Список стандартных действий

### 3.1 Действия, связанные с пользователями

| Метод | OB12 Действие | Параметры | Возвращаемые данные |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | Нет | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | Нет | `list[get_user_info ответ]` |

### 3.2 Действия, связанные с группами

| Метод | OB12 Действие | Параметры | Возвращаемые данные |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | Нет | `list[get_group_info ответ]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info ответ]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | Нет |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | Нет |

### 3.3 Управление сообщениями

| Метод | OB12 Действие | Параметры | Примечание |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | Отмена/удаление сообщения |

> **Отправка сообщений** (`send_message`) обрабатывается `SendDSL` через `Raw_ob12`, и не повторяется в `ApiDSL`.

### 3.4 Действия, связанные с каналами (Guild)

Система OneBot12 каналов разделена на два уровня: **канал (guild)** и **подканал (channel)**.

| Метод | OB12 Действие | Параметры | Возвращаемые данные |
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

> Система каналов и групп (group) независимы друг от друга: платформы Discord / QQ каналы / Kook реализуют интерфейс каналов, традиционные QQ / WeChat реализуют интерфейс групп, оба могут существовать одновременно или только один из них.

### 3.5 Действия с файлами

> [!WARNING]
> **Модель файлов (file_id в двух частях) в ErisPulse относится к "пониженной совместимости":** ErisPulse не использует модель "сначала загрузить, получить file_id, затем ссылаться" при отправке файлов — модули отправляют файлы с помощью `SendDSL.File(file, filename)` (URL / путь / байты **отправляются напрямую при отправке**, см. [спецификацию методов отправки](send-method-spec.md)).
> Действия `upload_file` / `get_file` / фрагментация зависят от специфичных для платформы возможностей `file_id`, **недостаточно универсальны**; только если у бэкенда адаптера есть такая возможность, он может пропустить их, встроенные адаптеры фреймворка **не реализуют и не рекомендуют реализовывать**, вызов обычно возвращает `retcode=10002`.
> Модулям, нуждающимся в пересылке файлов между платформами, следует использовать `SendDSL.File`, не полагаться на file_id.
>
> **Перспективы:** Стандартизация модели `file_id` до уровня фреймворка — будущее направление, в текущей версии не предоставляется.

Отправка целого файла (маленький файл):

| Метод | OB12 Действие | Параметры | Возвращаемые данные |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

Параметр `type` метода `upload_file`:
- `"url"`: загрузка по URL (требуется указать `url`)
- `"path"`: загрузка по локальному пути (требуется указать `path`)
- `"data"`: загрузка по двоичным данным (требуется указать `data`)

#### 3.5.1 Фрагментированная передача (большие файлы, относится к пониженной совместимости)

Действия OneBot12 по фрагментации разделены по `stage`. `ApiDSL` разделяет три/два этапа одного действия в отдельные методы (`offset` — смещение в байтах, `data` в JSON — Base64); таблица ниже только для справки, адаптеру не нужно и не следует реализовывать:

**Три этапа фрагментированной загрузки:** `prepare` → `transfer` (циклически по частям) → `finish`

| Метод | Этап | Параметры | Возвращаемые данные |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id` (используется при передаче) |
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

**Два этапа фрагментированной загрузки:** `prepare` → `transfer` (циклически по частям)

| Метод | Этап | Параметры | Возвращаемые данные |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data` (байты текущего фрагмента) |

### 3.6 Мета-действия

Мета-действия не относятся к конкретному аккаунту, не требуют указания `Using()`.

| Метод | OB12 Действие | Параметры | Возвращаемые данные |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | Массив объектов событий (без мета-событий) |
| `get_supported_actions()` | `get_supported_actions` | Нет | `list[str]` поддерживаемые названия действий |
| `get_status()` | `get_status` | Нет | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | Нет | `impl`, `version`, `onebot_version` |

### 3.7 Общие расширенные действия

| Метод | Описание |
|------|------|
| `call(action, **params)` | Эвакуационный люк для расширенных действий платформы, следует правилу именования OneBot12 `{prefix}.{action}` |

## 4. Способы использования

### 4.1 Базовый вызов

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

# Удаление сообщения
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Указание аккаунта бота (режим с несколькими аккаунтами)

```python
# Выполнение операций с указанием аккаунта бота
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 Расширенные действия платформы

```python
# Вызов расширенного действия платформы (рекомендуется использовать имя в формате {prefix}.{action})
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

### 5.1 Стандартное поведение (без настроек)

Стандартная реализация `ApiDSL` передает имя стандартного действия как `endpoint` напрямую в `adapter.call_api()`:

```python
# Стандартная реализация ApiDSL эквивалентна:
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

> **Поле аккаунта:** Фреймворк автоматически адаптирует привязку аккаунта в соответствии с фактическим способом использования `call_api` адаптера (стандартное имя `account_id`; старое имя `_account_id` автоматически переписывается; функция тела `params.pop` также распознает), если поле не используется, оно удаляется, чтобы избежать утечки в параметры платформы, и выводится одно предупреждение — форма потребления см. в [Разработка адаптеров - Анализ аккаунта](../developer-guide/adapters/core-concepts.md#Анализ аккаунта).

**Сценарии применения:** Когда нижний уровень бэкенда адаптера сам следует стандартному протоколу OneBot12 для действий, `call_api` нативно поддерживает имена стандартных действий (например, напрямую взаимодействует с сервисом, соответствующим этому протоколу).

### 5.2 Переопределение стандартных методов (отображение на оригинальный API платформы)

Адаптер может переопределить отдельные стандартные методы, отображая их на оригинальный API платформы:

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """Реализация стандартных API-действий MyPlatform"""

        async def get_user_info(self, user_id: str) -> dict:
            # Отображение на оригинальный API платформы
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                # Ошибка на стороне платформы: используйте диапазон 341xx～345xx для пользовательских последних трех цифр (346xx зарезервирован фреймворком, не используйте)
                return self._adapter.make_error(retcode=34400, message="Пользователь не существует")

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

Не покрытые стандартные методы адаптера используют стандартную реализацию (делегируются в `call_api`). Если `call_api` также не поддерживает это действие, следует вернуть стандартный ответ об ошибке:

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"Не поддерживаемое действие: {endpoint}")
    # ... вызов API платформы
```

Разработчики модулей могут определить поддержку по значению `retcode` в возвращаемом значении:

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("Эта платформа не поддерживает получение списка друзей")
```

## 6. Формат ответа

Все методы `ApiDSL` возвращают стандартный формат ответа API (см. [Стандарт ответа API](api-response.md)):

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

> **Примечание:** `message_id` для действий получения информации пустая строка (только у действий отправки сообщений есть `message_id`).

## 7. Отношения с SendDSL / RequestDSL

| Сценарий | Используемый DSL | Пример |
|------|---------|------|
| Отправка сообщений | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| Принятие/отклонение запросов | `Request` | `adapter.Request("req_id").accept()` |
| Получение информации о пользователе/группе | `Api` | `adapter.Api.get_user_info("123")` |
| Удаление сообщения | `Api` | `adapter.Api.delete_message("msg_id")` |
| Покидание группы | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. Проверочный список реализации адаптера

### Стандартные действия
- [ ] `call_api` может обрабатывать имена стандартных действий (или переопределить соответствующий метод `ApiDSL`)
- [ ] Не поддерживаемые действия возвращают `retcode=10002`
- [ ] Возвращаемые значения соответствуют стандартному формату ответа API
- [ ] Поле `data` содержит поля, определенные в стандарте OB12
- [ ] Платформы с каналами должны реализовать `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] Мета-действия (`get_status` / `get_version` / `get_supported_actions`) рекомендуется реализовать
- [ ] **Отправка файлов с помощью `SendDSL.File` (прямая передача)**; Действия с файлами (upload_file/get_file/фрагментация) **не обязательны**, только если бэкенд обладает возможностью `file_id`, требуется пропуск

### Расширенные действия
- [ ] Расширенные действия платформы используют имя в формате `{prefix}.{action}`
- [ ] Параметры и ответы расширенных действий по-прежнему соответствуют структуре запроса/ответа OneBot12

## 9. Связанные документы

**Сопутствующие документы при реализации возвращаемых значений Api DSL:**
- [Стандарт ответа API](api-response.md) - Стандартный формат ответа API адаптера

**Другие DSL в одном адаптере:**
- [Спецификация методов отправки](send-method-spec.md) - Назначение и параметры методов класса Send
- [Спецификация действий запросов](request-action-spec.md) - Использование Request DSL

**Сопутствующие документы со стороны событий:**
- [Стандарт преобразования событий](event-conversion.md) - Стандарт формата событий и сегментов сообщений