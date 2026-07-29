# ErisPulse API Стандарт действий

В этом документе определяется унифицированный интерфейсный стандарт для стандартных API-действий OneBot12 в адаптере ErisPulse, что позволяет разработчикам модулей программировать, ориентируясь на стандартный интерфейс, а адаптеру — обеспечивать отображение на нативные API платформ.

## 1. Фон проектирования

В ErisPulse формат сегментов сообщений (передача и прием) и формат событий уже полностью соответствуют стандарту OneBot12, но **вызовы API-действий** (такие как получение информации о пользователе, получение списка групп, отмена сообщения и т. д.) ранее не были унифицированы — разработчикам модулей приходилось писать разные вызовы `call_api` для каждой платформы.

`ApiDSL` решает эту проблему, предоставляя типизированные методы стандартных действий:

```
Код модуля (унифицированный для всех платформ)             Реализация адаптера (платформа-зависимая)
─────────────────────────────────────────              ──────────────────────────────────────────
adapter.Api.get_user_info("123")  →  адаптер call_api / перекрытие
adapter.Api.get_group_list()      →  адаптер call_api / перекрытие
adapter.Api.delete_message("id")  →  адаптер call_api / перекрытие
```

## 2. Параллельная трехслойная структура DSL

В адаптере ErisPulse есть три параллельных внутренних класса DSL, каждый из которых выполняет свою роль:

```
BaseAdapter
├── Send(SendDSL)       ← Отправка сообщений (Text/Image/Raw_ob12)
├── Request(RequestDSL)  ← Операции запроса (accept/reject)
└── Api(ApiDSL)          ← Стандартные API-действия (запрос информации/управление группами/управление сообщениями/операции с файлами) ★
```

| DSL | Обязанности | Стиль методов | Возвращаемое значение |
|-----|------------|--------------|----------------------|
| `Send` | Отправка сообщений | Цепной + `asyncio.Task` | Стандартный ответ |
| `Request` | Обработка событий запросов | `asyncio.Task` | Стандартный ответ |
| `Api` | Запрос/управление операциями | `async` методы | Стандартный ответ |

## 3. Список стандартных действий

### 3.1 Пользовательские

| Метод | OB12 Действие | Параметры | Возвращаемые данные |
|------|--------------|----------|--------------------|
| `get_self_info()` | `get_self_info` | Нет | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | Нет | `list[ответ get_user_info]` |

### 3.2 Групповые

| Метод | OB12 Действие | Параметры | Возвращаемые данные |
|------|--------------|----------|--------------------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | Нет | `list[ответ get_group_info]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[ответ get_group_member_info]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | Нет |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | Нет |

### 3.3 Управление сообщениями

| Метод | OB12 Действие | Параметры | Примечание |
|------|--------------|----------|-----------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | Отмена/удаление сообщения |

> **Отправка сообщений** (`send_message`) обрабатывается `Raw_ob12` из `SendDSL` и не дублируется в `ApiDSL`.

### 3.4 Операции с файлами

| Метод | OB12 Действие | Параметры | Возвращаемые данные |
|------|--------------|----------|--------------------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

Параметр `type` в `upload_file`:
- `"url"`: Загрузка по URL (необходимо предоставить `url`)
- `"path"`: Загрузка по локальному пути (необходимо предоставить `path`)
- `"data"`: Загрузка двоичными данными (необходимо предоставить `data`)

### 3.5 Общие расширенные действия

| Метод | Примечание |
|------|-----------|
| `call(action, **params)` | «Заглушка» для платформенных расширенных действий, соблюдающая правила именования OB12 `{prefix}.{action}` |

## 4. Способ использования

### 4.1 Базовый вызов

```python
from ErisPulse import adapter

# Получение информации о пользователе (унифицированное для всех платформ)
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

### 4.2 Указание учетной записи бота (режим нескольких учетных записей)

```python
# Использование указанной учетной записи бота для выполнения операций
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 Платформенные расширенные действия

```python
# Вызов специфичного для платформы расширенного действия (рекомендуется использовать формат {prefix}.{action})
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 Использование в обработчике событий

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

### 5.1 Поведение по умолчанию (нулевая конфигурация)

Базовая реализация `ApiDSL` передает имена стандартных действий как `endpoint` прямо в `adapter.call_api()`:

```python
# Базовая реализация ApiDSL эквивалентна:
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**Применимые сценарии**: Внутренняя часть адаптера сама реализует OneBot12 (например, NapCat, Lagrange и т. д.), где `call_api` естественным образом поддерживает имена стандартных действий.

### 5.2 Перекрытие стандартных методов (отображение на нативное API платформы)

Адаптер может перекрыть одно стандартное действие, отобразив его на нативное API платформы:

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """Реализация стандартных API-действий MyPlatform"""

        async def get_user_info(self, user_id: str) -> dict:
            # Отображение на нативное API платформы
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34001, message="Пользователь не существует")

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

### 5.3 Неподдерживаемые действия

Стандартные методы, не перекрытые адаптером, используют базовую реализацию (делегируются в `call_api`). Если `call_api` также не поддерживает это действие, следует вернуть стандартный ответ об ошибке:

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"Unsupported action: {endpoint}")
    # ... вызов платформенного API
```

Разработчики модулей могут определить поддержку по коду ошибки в возвращаемом значении:

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("Эта платформа не поддерживает получение списка друзей")
```

## 6. Формат ответа

Все методы `ApiDSL` возвращают стандартный формат API-ответа (см. [Стандарт API-ответа](docs/ru/api-response.md)):

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

> **Важно**: Для действий по запросу информации поле `message_id` пустая строка (поле `message_id` есть только у действий по отправке сообщений).

## 7. Связь с SendDSL / RequestDSL

| Сценарий | Использовать DSL | Пример |
|---------|-----------------|--------|
| Отправка сообщения | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| Принятие/отклонение запроса | `Request` | `adapter.Request("req_id").accept()` |
| Получение информации о пользователе/группе | `Api` | `adapter.Api.get_user_info("123")` |
| Отмена сообщения | `Api` | `adapter.Api.delete_message("msg_id")` |
| Выход из группы | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. Чек-лист реализации адаптера

### Стандартные действия
- [ ] `call_api` может обрабатывать имена стандартных действий (или перекрывать соответствующий метод `ApiDSL`)
- [ ] Для неподдерживаемых действий возвращается `retcode=10002`
- [ ] Возвращаемое значение соответствует стандартному формату API-ответа
- [ ] Поле `data` содержит поля, определенные в стандарте OB12

### Расширенные действия
- [ ] Платформенные расширенные действия используют формат имен `{prefix}.{action}`
- [ ] Параметры и ответы расширенных действий по-прежнему следуют структуре запросов/ответов OB12

## 9. Справочные документы

- [Стандарт API-ответа](docs/ru/api-response.md) — стандарт формата ответа API адаптера
- [Спецификация метода отправки](docs/ru/send-method-spec.md) — стандарты именования и параметров методов класса Send
- [Спецификация действий запроса](docs/ru/request-action-spec.md) — способ использования Request DSL
- [Стандарт преобразования событий](docs/ru/event-conversion.md) — стандарты формата событий и сегментов сообщений