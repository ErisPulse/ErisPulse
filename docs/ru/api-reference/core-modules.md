# API основных модулей

> [!TIP]
> **Когда стоит читать этот документ**: когда вам нужны базовые возможности — хранилище, конфигурация, логирование, управление модулями, маршрутизация, HTTP-клиент и т.д. — и вы не помните точные сигнатуры методов, быстро сверьтесь с этим документом. Если это не нужно — пропустите.

Этот документ представляет собой краткий справочник по API основных модулей ErisPulse, содержащий сигнатуры методов и краткие описания. Подробное использование и примеры смотрите по ссылкам «Полная документация» соответствующих модулей.

## Модуль Storage

Система key-value хранилища на основе настраиваемого бэкенда (SQLite/MySQL/PostgreSQL) с поддержкой универсальных цепочечных SQL-запросов; бэкенд переключается одним параметром конфигурации, подробнее см. [Бэкенды хранилища](../advanced/storage-backends.md).

### Базовые операции

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

### Транзакции

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Доступ через атрибуты

```python
sdk.storage.my_key          # эквивалентно sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # эквивалентно sdk.storage.set("my_key", "val")
```

### Цепочечные SQL-запросы

Модуль Storage предоставляет универсальный конструктор SQL-запросов в цепочечном стиле, поддерживающий CRUD-операции с пользовательскими таблицами.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> Полный API цепочечных запросов (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, транзакции и т.д.) см. [Конструктор SQL-запросов](../advanced/sql-builder.md).

### Абстракция бэкендов хранилища

`StorageManager` наследуется от абстрактного базового класса `BaseStorage` и поддерживает расширение другими носителями данных (Redis, MySQL и т.д.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Асинхронный интерфейс

Модули Storage и Config предоставляют асинхронные методы (с префиксом `a`): **асинхронный интерфейс является основным нативным, а синхронные методы — слоем совместимости** (внутри они мостятся на фоновый цикл событий). Существующий синхронный код менять не нужно; в новом коде внутри асинхронных обработчиков предпочитайте асинхронные методы.

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

Управление файлами конфигурации в формате TOML с поддержкой путей ключей, разделённых точками.

### Обзор API

| Метод | Описание |
|------|------|
| `getConfig(key, default)` | Чтение конфигурации, поддерживает пути через точку, например `"MyModule.subkey"` |
| `getAllConfig()` | Полный снимок конфигурации (глубокая копия, включая ещё не сохранённые на диск отложенные значения) |
| `setConfig(key, value, immediate=False)` | Запись конфигурации. При `immediate=True` немедленно сохраняется в файл |
| `delConfig(key, immediate=False)` | Удаление ключа конфигурации (в отличие от установки пустого значения), удаляется из файла; инициирует событие `config.set` (`new_value=None`) |
| `force_save()` | Принудительно записывает конфигурацию из памяти в файл |
| `reload()` | Перезагружает конфигурацию из файла |
| `agetConfig(key, default)` | Асинхронное чтение конфигурации |
| `agetAllConfig()` | Асинхронное получение полного снимка конфигурации |
| `asetConfig(key, value, immediate)` | Асинхронная запись конфигурации |
| `adelConfig(key, immediate)` | Асинхронное удаление ключа конфигурации (поведение как у `delConfig`) |
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

# Асинхронный интерфейс (приоритет в асинхронных обработчиках)
snapshot = await sdk.config.agetAllConfig()
await sdk.config.adelConfig("MyModule.deprecated")  # Асинхронное удаление ключа
```

> `setConfig` по умолчанию использует отложенную запись (пакетное сохранение каждые 5 секунд); установка `immediate=True` обеспечивает немедленное сохранение в файл конфигурации. Изменения конфигурации инициируют событие жизненного цикла `config.set`.
> `delete` также поддерживает отложенную запись и событие `config.set` (`new_value=None`); существующие подписчики `on_config_update` узнают об удалении без каких-либо изменений кода.

## Модуль Logger

Модульная система логирования с выводом на основе Rich; поддерживает дочерние логгеры и управление уровнями по модулям.

### Базовое использование

```python
sdk.logger.debug("Отладочная информация")
sdk.logger.info("Рабочая информация")
sdk.logger.warning("Предупреждение")
sdk.logger.error("Ошибка")
sdk.logger.critical("Критическая ошибка")
```

### Дочерние логгеры

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Лог дочернего модуля")

child_logger.get_child("utils")  # поддерживает вложенность
```

### Управление уровнем логирования

```python
sdk.logger.set_level("DEBUG")                          # Глобальный уровень
sdk.logger.set_module_level("MyModule", "DEBUG")       # Уровень модуля

# Поддерживаемые уровни (от низкого к высокому):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE — самый низкий уровень, выводит подробную внутреннюю отладочную информацию фреймворка (распространение событий, регистрацию маршрутов и т.д.)
sdk.logger.set_level("TRACE")                          # Включить все логи
```

### Подписка на логи (push-режим)

Позволяет таким модулям, как Dashboard, получать структурированные логи в реальном времени; поддерживает фильтрацию по уровню и досылку истории.

> **Явная подписка на логи низких уровней**: `min_level` подписчика может быть ниже глобального уровня логирования. В этом случае логи низких уровней **отправляются только подходящим подписчикам**, не выводятся в консоль и не записываются в память, что позволяет не засорять основной поток логов.
>
> ```python
> # Глобальный уровень INFO, но всё равно можно отдельно подписаться на DEBUG-логи
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# Через декоратор
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "Строгий режим: ...",
    # }
    pass

# Прямой вызов
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Метод | Описание |
|------|------|
| `handler(id, *, min_level)(func)` | Декоратор/прямой вызов. Если `id` пуст, берётся имя функции. `min_level` может быть ниже глобального уровня (логи низких уровней отправляются только подписчикам, не попадают в консоль/память). При регистрации автоматически досылаются исторические логи |
| `remove_handler(id)` | Удаляет подписчика |

### Управление выводом

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Модуль Adapter

Менеджер адаптеров, управляет регистрацией, запуском и остановкой многоплатформенных адаптеров.

### Обзор API

| Метод | Описание |
|------|------|
| `get(platform)` | Получает экземпляр адаптера |
| `exists(platform)` | Проверяет, зарегистрирован ли адаптер |
| `enable(platform)` / `disable(platform)` | Включает/отключает адаптер |
| `is_enabled(platform)` | Проверяет, включён ли адаптер |
| `startup(platforms)` / `shutdown(platforms)` | Запускает/останавливает адаптеры |
| `is_running(platform)` | Проверяет, запущен ли адаптер |
| `list_running()` | Перечисляет все запущенные адаптеры |
| `platforms` | Возвращает список названий всех платформ |
| `get_info(platform)` | Информация о регистрации адаптера (json-safe: meta + имя класса) |
| `get_meta(platform, resolve_i18n=True)` | Метаданные описания адаптера (согласовано с `module.get_meta`, поддерживает i18n-разбор) |

### События адаптера

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Запрос состояния ботов

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> Полный API управления адаптерами см. [API системы адаптеров](adapter-system.md).

## Модуль Module

Менеджер модулей, управляет регистрацией, загрузкой и выгрузкой плагинов.

### Обзор API

| Метод | Описание |
|------|------|
| `get(name)` | Получает экземпляр модуля или ленивый прокси (возвращает прокси, если модуль зарегистрирован, но не загружен) |
| `exists(name)` | Проверяет, зарегистрирован ли модуль |
| `is_loaded(name)` | Проверяет, загружен ли модуль |
| `is_enabled(name)` | Проверяет, включён ли модуль |
| `enable(name)` / `disable(name)` | Включает/отключает модуль |
| `load(name)` / `unload(name)` | Загружает/выгружает модуль |
| `call(module, method, *args, timeout=None, **kwargs)` | Межмодульный вызов сервисного метода целевого модуля (протоколированный RPC) |
| `list_registered()` | Перечисляет зарегистрированные модули |
| `list_loaded()` | Перечисляет загруженные модули |
| `get_info(name)` | Получает информацию о модуле |
| `get_status_summary()` | Получает сводку статусов модулей |

### Доступ через атрибуты

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # эквивалентное сокращение
```

### Межмодульные вызовы (RPC)

```python
# Протоколированный вызов: типизированные ошибки / автопробуждение ленивых модулей / атрибуция owner / семантика тайм-аута
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Отличия от прямого доступа к атрибуту провайдера `sdk.module.Chat.get_history(...)`:

| | `module.call()` | Прямой доступ к атрибуту |
|---|---|---|
| Цель не зарегистрирована/не включена | Выбрасывается `ModuleNotAvailableError` | Выбрасывается `AttributeError` |
| Лениво загружаемый модуль | Автопробуждение | Модуль с асинхронной инициализацией выбрасывает RuntimeError |
| `current_owner` | Атрибутируется целевому модулю | Остаётся за вызывающим |
| Тайм-аут | По умолчанию 30 с, можно переопределить | Нет |
| Аудит scope | `actions.<вызывающий>.call` | Нет |

### Контракты сервисов (meta.services)

Провайдер объявляет белый список внешних методов в поле `services` метода `get_meta()` (симметрично `commands`); после объявления поверхность вызовов сужается:

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **По умолчанию = незаметно для разработчика**: если `services` не объявлены, можно вызывать любой **публичный** метод (обратная совместимость); приватные методы с подчёркиванием всегда запрещены; основной контроль ограничений — на стороне пользователя через конфигурацию scope
- После объявления: вызывать можно только методы из белого списка; при выходе за его пределы выбрасывается `ServiceNotProvidedError`
- Ограничение вызывающей стороны: `scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**Описания сервисов (description)**: `services` поддерживает форму dict, позволяя объявить описание для каждого сервиса (поддерживается простая строка или i18n-словарь); используется каталогом сервисов / описаниями точек вызова AI:

```python
return ModuleMeta(
    services=[
        "get_history",                              # Простая форма: описание автоматически берётся из первой строки docstring метода
        {"name": "translate", "description": "Переводит текст на указанный язык"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Резюме диалога"}},
    ],
)
```

Приоритет разбора описания: **явное description (i18n преобразуется к текущему языку) > первая строка docstring метода > пустая строка**.

### Каталог сервисов (services)

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Получает историю сессии'}]}

sdk.module.services("Chat")  # Запрашивает только указанный модуль
```

Перечисляются только модули с **явно объявленными** `meta.services`; для каждого сервиса прилагаются строка сигнатуры метода и текст описания, что закладывает основу данных для MCP-изации (предоставления точек вызова AI).

> Направленная доставка событий относится к слою жизненного цикла: `lifecycle.emit(event, data, to="ModuleName")`,
> подробнее см. [Межмодульное взаимодействие](../advanced/module-communication.md).

## Модуль Lifecycle

Событийно-ориентированный менеджер жизненного цикла, предоставляет отправку и прослушивание событий.

### Обзор API

| Метод | Описание |
|------|------|
| `on(event, priority=0)` | Декоратор для регистрации обработчика событий, поддерживает точечное сопоставление и подстановочный знак `*` |
| `register(event, handler, priority=0)` | Функциональная регистрация обработчика |
| `unregister(event, handler=None)` | Удаляет обработчик |
| `emit(event, data, to=None)` | Асинхронно инициирует событие; при указании `to` выполняется направленная доставка |
| `emit_sync(event, data, to=None)` | Синхронно инициирует событие (асинхронные обработчики планируются через create_task) |
| `submit_event(event_type, msg, data, source, to=None)` | Отправляет событие в стандартном формате (совместимость со старой версией) |
| `start_timer(id)` / `stop_timer(id)` | Таймеры производительности |

### Примеры

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Инициализация модуля: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Событие модуля: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})

# Направленная доставка: распределяется только хукам, зарегистрированным модулем Chat
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")
```

> Полный список стандартных событий и подробное использование см. [Управление жизненным циклом](../advanced/lifecycle.md).

## Модуль Router

Менеджер HTTP/WebSocket-маршрутов на основе FastAPI + Uvicorn; поддерживает маршруты через декораторы, промежуточное ПО, группы, ограничение частоты запросов, CORS.

> Полную документацию по API маршрутов (маршруты через декораторы, WebSocket, промежуточное ПО, ограничение скорости, CORS, заголовки безопасности и т.д.) см. [Менеджер маршрутов](../advanced/router.md).

### Краткий справочник

```python
# HTTP-маршрут
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket-маршрут
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# Группа маршрутов
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## Модуль HTTP Client

Унифицированный сетевой клиент, объединяющий HTTP-запросы, WebSocket-соединения, управление пулом соединений, автоматические повторы, статистику запросов и интеграцию с событиями жизненного цикла.

> Полную документацию по сетевому клиенту (методы запросов, объекты ответов, WebSocket-клиент, иерархия исключений и т.д.) см. [Сетевой клиент](../advanced/http-client.md).

### Краткий справочник

```python
from ErisPulse.Core import client

# HTTP-запрос
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## Отладка SDK

### dump_state()

Экспортирует снимок текущего состояния работы фреймворка для отладки и диагностики.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

Возвращаемая структура содержит состояние следующих подсистем:

| Поле | Описание |
|------|------|
| `sdk` | Статус инициализации SDK, версия Python, платформа выполнения, метка времени |
| `adapters` | Список зарегистрированных/запущенных адаптеров, статус онлайн ботов на каждой платформе |
| `modules` | Список зарегистрированных/включённых/отключённых/лениво загружаемых модулей |
| `events` | Количество обработчиков различных типов событий (message/notice/request/meta/commands) |
| `router` | Статус работы сервера, количество HTTP/WebSocket-маршрутов |

> [!NOTE]
> Добавлено в ErisPulse **2.5.2+**

## Interaction: интерактивные сессии

Управление приостановленными ожиданиями wait_reply и эксклюзивными арендами (lease) сессий (`sdk.interaction`).

### Основные методы

```python
# Таймер напоминания для сессии: напомнит, если 5 минут нет ответа, автоматически отменяется при ответе пользователя
reminder = event.remind(300, "Вы ещё здесь?")
reminder.cancel()  # Ручная отмена

# Эскалация по тайм-ауту: гарантированно срабатывает по истечении срока (не отменяется ответом)
event.escalate(1800, lambda e: notify_master("Не обработано 30 минут"))

# Многоканальное ожидание: побеждает тот, кто ответит первым
which, reply = await event.select(
    event.expect(pattern="Согласен*", user="A"),
    event.expect(pattern="Отказ*", user="B"),
    timeout=60,
)

# Ожидание уровня сессии: ответ любого участника группы может сработать
reply = await event.wait_reply(session=True, prompt="Кто может помочь ответить?")

# Запрос текущего владельца сессии (кто сейчас взаимодействует с этим пользователем)
owner = sdk.interaction.get_owner_of(event)

# Объявление эксклюзивной аренды сессии (возвращает None, если занята)
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # Эксклюзивное взаимодействие
    finally:
        lease.release()

# Форма контекстного менеджера (при занятости выбрасывает SessionOccupiedError)
with sdk.interaction.hold(event) as lease:
    ...

# Статистика приостановленных сессий
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

При выгрузке модуля / закрытии адаптера его приостановленные ожидания и таймеры автоматически отменяются (ожидающая сторона немедленно получает `None`);
при совпадении ответа права scope автоматически перепроверяются (если пользователь в чёрном списке или модуль отвязан, ожидание прекращается).

> [!NOTE]
> Возможности этого раздела добавлены в ErisPulse **2.8.0+**

## Transcript: почтовый ящик сессии

Автоматическая запись и запрос потока недавних сообщений каждой сессии (`sdk.transcript`), служит общей основой для модулей контекстной памяти, таких как AI-диалоги, защита от повторов и т.д.

### Основные методы

```python
# Удобный запрос (рекомендуется): последние 20 сообщений текущей сессии (включая пользователя и бота, в порядке возрастания времени)
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# API менеджера
sdk.transcript.append(event, "user", "Текст")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

Конфигурация (`ErisPulse.transcript`): `enabled` (включено по умолчанию), `max_per_session` (лимит на сессию, по умолчанию 50),
`ttl_hours` (глобальное время истечения, по умолчанию 168 часов). Данные хранятся в отдельной таблице SQLite; очистка при превышении лимита или истечении срока выполняется лениво.

> [!NOTE]
> Возможности этого раздела добавлены в ErisPulse **2.8.0+**

## Связанные документы

**Продолжить изучение API**:
- [API системы событий](event-system.md) - API модуля Event
- [API системы адаптеров](adapter-system.md) - API управления адаптерами

**Полная документация по отдельным подсистемам**:
- [Конструктор SQL-запросов](../advanced/sql-builder.md) - Полная документация по цепочечным SQL-запросам
- [Менеджер маршрутов](../advanced/router.md) - Полная документация по менеджеру маршрутов
- [Сетевой клиент](../advanced/http-client.md) - Полная документация по сетевому клиенту
- [Управление жизненным циклом](../advanced/lifecycle.md) - Полная документация по жизненному циклу