# API основных модулей

> [!TIP]
> **Когда следует читать эту статью**: когда вам нужно использовать основные возможности, такие как хранилище, конфигурация, логирование, управление модулями, маршрутизация, HTTP-клиент и т.д., и вы не помните точные сигнатуры методов, обратитесь к этой статье для быстрого ознакомления. Если не нужно, пропустите.

Документация предоставляет быструю справочную информацию по API основных модулей ErisPulse, включая сигнатуры методов и краткие пояснения. Для подробного использования и примеров щелкните по ссылкам "Полная документация" для каждого модуля.

## Модуль Storage

Система хранения пар ключ-значение на основе настраиваемого бэкенда (SQLite/MySQL/PostgreSQL), поддерживающая общие SQL-цепные запросы, бэкенд можно переключить одним кликом, подробнее см. [Хранилище бэкендов](../advanced/storage-backends.md).

### Основные операции

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### Пакетные операции

```python
sdk.storage.set_multi({"key1": "val1", "key2": "val2"})
values = sdk.storage.get_multi(["key1", "key2"])
sdk.storage.delete_multi(["key1", "key2"])
```

### Транзакционные операции

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Доступ по свойствам

```python
sdk.storage.my_key          # эквивалентно sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # эквивалентно sdk.storage.set("my_key", "val")
```

### SQL-цепные запросы

Модуль Storage предоставляет гибкий API для построения SQL-запросов в стиле цепных вызовов, поддерживающий CRUD-операции для пользовательских таблиц.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> Полный API цепных SQL-запросов (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, транзакции и т.д.) см. в [SQL-построителе запросов](../advanced/sql-builder.md).

### Абстракция хранилища бэкендов

`StorageManager` наследуется от абстрактного базового класса `BaseStorage`, поддерживает расширение другими хранилищами (Redis, MySQL и т.д.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Асинхронный интерфейс

Модули Storage и Config предоставляют асинхронные методы (префикс `a`): **асинхронные методы являются основными, синхронные методы являются совместимыми слоем** (внутренне мостятся к фоновому циклу событий для выполнения). Существующий синхронный код не требует изменений; новые коды в асинхронных обработчиках следует использовать асинхронные методы.

```python
# Асинхронное хранилище
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# Асинхронные пакетные операции
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# Асинхронная конфигурация
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()
```

## Модуль Config

Управление конфигурационными файлами в формате TOML, поддерживает ключевые пути с разделением точками.

### Обзор API

| Метод | Описание |
|------|------|
| `getConfig(key, default)` | Чтение конфигурации, поддерживает пути с точками, например `"MyModule.subkey"` |
| `getAllConfig()` | Полный снимок конфигурации (глубокая копия, включая незаписанные значения) |
| `setConfig(key, value, immediate=False)` | Запись конфигурации. `immediate=True` немедленно сохраняет в файл |
| `delConfig(key, immediate=False)` | Удаление ключа конфигурации (в отличие от установки в пустое значение), удаляет из файла; вызывает событие `config.set` (`new_value=None`) |
| `force_save()` | Принудительное сохранение конфигурации из памяти в файл |
| `reload()` | Перезагрузка конфигурации из файла |
| `agetConfig(key, default)` | Асинхронное чтение конфигурации |
| `agetAllConfig()` | Асинхронный получение полного снимка конфигурации |
| `asetConfig(key, value, immediate)` | Асинхронная запись конфигурации |
| `adelConfig(key, immediate)` | Асинхронное удаление ключа конфигурации (поведение аналогично `delConfig`) |
| `aforce_save()` | Асинхронное принудительное сохранение |
| `areload()` | Асинхронная перезагрузка |

### Примеры

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

snapshot = sdk.config.getAllConfig()          # Полный снимок (глубокая копия)
sdk.config.delConfig("MyModule.deprecated")  # Удаление ключа (отложенная запись)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)

# Асинхронный интерфейс (в асинхронных обработчиках предпочтительно использовать)
snapshot = await sdk.config.agetAllConfig()
await sdk.config.adelConfig("MyModule.deprecated")  # Асинхронное удаление ключа
```

> `setConfig` по умолчанию использует отложенную запись (каждые 5 секунд пакетное сохранение), установка `immediate=True` немедленно сохраняет в конфигурационный файл. Изменения конфигурации вызывают событие жизненного цикла `config.set`.
> `delete` также поддерживает отложенную запись и событие `config.set` (`new_value=None`), существующие слушатели `on_config_update` без изменений могут обнаруживать удаление.

## Модуль Logger

Модульная система логирования, основанная на Rich, поддерживает под-логгеры и контроль на уровне модуля.

### Основное использование

```python
sdk.logger.debug("Отладочная информация")
sdk.logger.info("Информация о работе")
sdk.logger.warning("Предупреждение")
sdk.logger.error("Ошибка")
sdk.logger.critical("Критическая ошибка")
```

### Под-логгеры

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Лог под-модуля")

child_logger.get_child("utils")  # Поддержка вложенности
```

### Управление уровнем логирования

```python
sdk.logger.set_level("DEBUG")                          # Глобальный уровень
sdk.logger.set_module_level("MyModule", "DEBUG")       # Уровень на уровне модуля

# Поддерживаемые уровни (от низкого к высокому):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE - самый низкий уровень, выводит подробную отладочную информацию (распределение событий, регистрация маршрутов и т.д.)
sdk.logger.set_level("TRACE")                          # Включить все логи
```

### Подписка на логи (режим push)

Для модулей, таких как Dashboard, для получения структурированных логов в реальном времени, поддерживаются фильтрация по уровню и историческое восстановление.

> **Явная подписка на низкий уровень логирования**: подписчик может иметь `min_level` ниже глобального уровня логирования. В этом случае логи низкого уровня **отправляются только соответствующему подписчику**, не выводятся в консоль и не записываются в память, чтобы избежать загрязнения основного потока логов.
>
> ```python
> # Глобально INFO, но можно отдельно подписаться на DEBUG логи
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# Способ декоратора
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "Строгий режим:...",
    # }
    pass

# Прямой вызов
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Метод | Описание |
|------|------|
| `handler(id, *, min_level)(func)` | Декоратор/прямой вызов. `id` пустой, берется имя функции. `min_level` может быть ниже глобального уровня (логи низкого уровня отправляются только подписчику, не идут в консоль/память). При регистрации автоматически восстанавливает исторические логи |
| `remove_handler(id)` | Удалить подписчика |

### Управление выводом

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Модуль Adapter

Менеджер адаптеров, управляет регистрацией, запуском и остановкой адаптеров для различных платформ.

### Обзор API

| Метод | Описание |
|------|------|
| `get(platform)` | Получить экземпляр адаптера |
| `exists(platform)` | Проверить, зарегистрирован ли адаптер |
| `enable(platform)` / `disable(platform)` | Включить/выключить адаптер |
| `is_enabled(platform)` | Проверить, включен ли |
| `startup(platforms)` / `shutdown(platforms)` | Запустить/остановить адаптеры |
| `is_running(platform)` | Проверить, запущен ли адаптер |
| `list_running()` | Перечислить все запущенные адаптеры |
| `platforms` | Получить список всех платформ |
| `get_info(platform)` | Информация о зарегистрированном адаптере (json-safe: meta + имя класса) |
| `get_meta(platform, resolve_i18n=True)` | Метаинформация адаптера (согласование с `module.get_meta`, поддержка i18n解析) |

### События адаптера

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Запрос статуса бота

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> Полный API управления адаптерами см. в [API системы адаптеров](adapter-system.md).

## Модуль Module

Менеджер модулей, управляет регистрацией, загрузкой и выгрузкой плагинов.

### Обзор API

| Метод | Описание |
|------|------|
| `get(name)` | Получить экземпляр модуля или ленивый загрузочный прокси (при регистрации, но не загрузке, возвращается прокси) |
| `exists(name)` | Проверить, зарегистрирован ли |
| `is_loaded(name)` | Проверить, загружен ли |
| `is_enabled(name)` | Проверить, включен ли |
| `enable(name)` / `disable(name)` | Включить/выключить модуль |
| `load(name)` / `unload(name)` | Загрузить/выгрузить модуль |
| `call(module, method, *args, timeout=None, **kwargs)` | Вызов метода сервиса другого модуля (протоколизированный RPC) |
| `list_registered()` | Перечислить зарегистрированные модули |
| `list_loaded()` | Перечислить загруженные модули |
| `get_info(name)` | Получить информацию о модуле |
| `get_status_summary()` | Получить сводку состояния модуля |

### Доступ по свойствам

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # Эквивалентный сокращенный способ
```

### Вызов между модулями (RPC)

```python
# Протоколизированный вызов: типизированные ошибки / ленивые модули автоматически пробуждаются / owner присваивается / семантика таймаута
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Различия между `module.call()` и прямым доступом к свойству:

| | `module.call()` | Прямой доступ к свойству |
|---|---|---|
| Цель не зарегистрирована/не включена | Выбрасывает `ModuleNotAvailableError` | Выбрасывает `AttributeError` |
| Ленивая загрузка модуля | Автоматически пробуждается | Асинхронная инициализация модуля выбрасывает RuntimeError |
| `current_owner` | Присваивается к целевому модулю | Сохраняется вызывающий модуль |
| Таймаут | По умолчанию 30 секунд, можно перекрыть | Нет |
| Проверка scope | `actions.<вызывающий модуль>.call` | Нет |

### Сервисный контракт (meta.services)

Сервисная сторона в `get_meta()` в поле `services` объявляет белый список для внешнего доступа (симметрично `commands`), после объявления доступ к вызову сужается:

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **По умолчанию = для разработчика незаметно**: если не объявлен `services`, доступны любые **публичные** методы (для обратной совместимости), методы с подчеркиванием всегда запрещены; основной контроль доступа находится в настройках scope пользователя
- После объявления: доступны только методы из белого списка, при выходе за пределы выбрасывается `ServiceNotProvidedError`
- Ограничение вызывающей стороны: `scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**Описание сервиса (description)**: `services` поддерживает словарную форму для описания каждого сервиса (поддерживает чистую строку или словарь i18n), для каталога сервисов / потребления описания точек вызова AI:

```python
return ModuleMeta(
    services=[
        "get_history",                              # Простая форма: описание автоматически берется из первой строки docstring метода
        {"name": "translate", "description": "Перевести текст на указанный язык"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Суммаризировать диалог"}},
    ],
)
```

Приоритет разбора описания: **явное описание (i18n разбирается на текущий язык) > первая строка docstring метода > пустая строка**.

### Каталог сервисов (services)

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Получить историю сессии'}]}

sdk.module.services("Chat")  # Получить только для указанного модуля
```

Перечисляются только модули с явно объявленным `meta.services`; каждый сервис сопровождается строкой сигнатуры метода и описанием текста, что обеспечивает данные для MCP (экспозиция точек вызова для AI).

> Направленная отправка событий относится к уровню жизненного цикла: `lifecycle.emit(event, data, to="ModuleName")`, подробнее см. [Взаимодействие между модулями](../advanced/module-communication.md).

## Модуль Lifecycle

Система управления жизненным циклом на основе событий, предоставляет функции отправки и прослушивания событий.

### Обзор API

| Метод | Описание |
|------|------|
| `on(event, priority=0)` | Декоратор для регистрации обработчика событий, поддерживает точечные совпадения и подстановочные знаки `*` |
| `register(event, handler, priority=0)` | Функциональная регистрация обработчика |
| `unregister(event, handler=None)` | Удаление обработчика |
| `emit(event, data, to=None)` | Асинхронная отправка события; `to` указывает на владельца, если направлена отправка |
| `emit_sync(event, data, to=None)` | Синхронная отправка события (в асинхронных обработчиках с помощью create_task) |
| `submit_event(event_type, msg, data, source, to=None)` | Подача стандартного события (совместимость со старыми версиями) |
| `start_timer(id)` / `stop_timer(id)` | Таймер производительности |

### Примеры

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Инициализация модуля: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Событие модуля: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})

# Направленная отправка: отправка только обработчикам, зарегистрированным в модуле Chat
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")
```

> Полный список стандартных событий и подробное использование см. в [Управление жизненным циклом](../advanced/lifecycle.md).

## Модуль Router

Менеджер маршрутизации HTTP/WebSocket, на основе FastAPI + Uvicorn, поддерживает маршрутизацию с декораторами, промежуточные обработчики, группировку, ограничение скорости, CORS.

> Полная документация API маршрутизатора (маршрутизация с декораторами, WebSocket, промежуточные обработчики, ограничение скорости, CORS, заголовки безопасности и т.д.) см. в [Менеджер маршрутизации](../advanced/router.md).

### Краткий справочник

```python
# HTTP маршрутизация
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket маршрутизация
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# Группировка маршрутов
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## Модуль HTTP Client

Единый клиент для сетевых запросов, объединяет HTTP-запросы, WebSocket-соединения, управление пула соединений, автоматические повторные попытки, статистику запросов и интеграцию событий жизненного цикла.

> Полная документация сетевого клиента (методы запросов, объекты ответов, WebSocket-клиент, иерархия исключений и т.д.) см. в [Сетевой клиент](../advanced/client.md).

### Краткий справочник

```python
from ErisPulse.Core import client

# HTTP запрос
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## SDK отладка

### dump_state()

Экспорт снимка текущего состояния работы фреймворка, используется для отладки и диагностики.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

Возвращаемая структура содержит состояние следующих подсистем:

| Поле | Описание |
|------|------|
| `sdk` | Состояние инициализации SDK, версия Python, платформа, временная метка |
| `adapters` | Список зарегистрированных/запущенных адаптеров, статус онлайн-бота каждой платформы |
| `modules` | Список зарегистрированных/включенных/отключенных/лениво загружаемых модулей |
| `events` | Количество обработчиков различных типов событий (message/notice/request/meta/commands) |
| `router` | Статус сервера, количество HTTP/WebSocket маршрутов |

> [!NOTE]
> Добавлено в ErisPulse **2.5.2+**

## Взаимодействие (Interaction)

Управление ожиданием wait_reply и сеансовыми взаимосвязями (sdk.interaction).

### Основные методы

```python
# Таймер напоминания сеанса: если нет ответа в течение 5 минут, напомнить, ответ пользователя автоматически отменяет
reminder = event.remind(300, "Еще здесь?")
reminder.cancel()  # Ручная отмена

# Превышение таймаута: обязательно срабатывает по истечении времени (не отменяется ответом)
event.escalate(1800, lambda e: notify_master("Не обработано 30 минут"))

# Ожидание нескольких путей: первый, кто ответит, побеждает
which, reply = await event.select(
    event.expect(pattern="同意*", user="A"),
    event.expect(pattern="拒绝*", user="B"),
    timeout=60,
)

# Сеансовое ожидание: любой ответ в группе может быть принят
reply = await event.wait_reply(session=True, prompt="Кто-нибудь может помочь ответить?")

# Запрос текущего владельца сеанса (кто взаимодействует с пользователем)
owner = sdk.interaction.get_owner_of(event)

# Заявление сеансового взаимосвязи (если занято, возвращает None)
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # Исключительное взаимодействие
    finally:
        lease.release()

# Форма контекстного менеджера (если занято, выбрасывается SessionOccupiedError)
with sdk.interaction.hold(event) as lease:
    ...

# Статистика сеансов
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

При выгрузке модуля/остановке адаптера ожидания и таймеры автоматически отменяются (ожидание немедленно возвращает `None`), при срабатывании ответа автоматически проверяется разрешение scope (если пользователь исключен/модуль отключен, ожидание прекращается).

> [!NOTE]
> Функциональность в этом разделе добавлена в ErisPulse **2.8.0+**

## Транскрипт (Transcript)

Автоматическая запись и запрос последних сообщений для каждого сеанса (sdk.transcript), используется как база для модулей контекстной памяти, таких как AI-диалоги и предотвращение повторений.

### Основные методы

```python
# Удобный запрос (рекомендуется): последние 20 сообщений текущего сеанса (включая пользователя и бота, по возрастанию времени)
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# Методы менеджера
sdk.transcript.append(event, "user", "Текст")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

Конфигурация (`ErisPulse.transcript`): `enabled` (по умолчанию включено), `max_per_session` (максимум на сеанс, по умолчанию 50), `ttl_hours` (время жизни по умолчанию, по умолчанию 168 часов). Данные хранятся в отдельной таблице SQLite, при превышении лимита или истечении срока удаляются лениво.

> [!NOTE]
> Функциональность в этом разделе добавлена в ErisPulse **2.8.0+**

## Связанные документы

**Продолжить изучение API**:
- [API системы событий](event-system.md) - API модуля Event
- [API системы адаптеров](adapter-system.md) - API управления адаптерами

**Глубокое изучение документации по подсистемам**:
- [SQL-построитель запросов](../advanced/sql-builder.md) - Полная документация SQL-цепных запросов
- [Менеджер маршрутизации](../advanced/router.md) - Полная документация менеджера маршрутизации
- [Сетевой клиент](../advanced/client.md) - Полная документация сетевого клиента
- [Управление жизненным циклом](../advanced/lifecycle.md) - Полная документация жизненного цикла