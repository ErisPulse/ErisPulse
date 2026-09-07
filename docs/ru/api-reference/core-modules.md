# API основных модулей

Данный документ предоставляет краткое руководство по API основных модулей ErisPulse, включая сигнатуры методов и краткие описания. Подробное использование и примеры можно найти, нажав на ссылку "Полная документация" для каждого модуля.

## Модуль Storage

Система хранения ключ-значение на базе SQLite, поддерживающая универсальные SQL-цепочечные запросы.

### Основные операции

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### Массовые операции

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

### Доступ к свойствам

```python
sdk.storage.my_key          # эквивалентно sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # эквивалентно sdk.storage.set("my_key", "val")
```

### SQL-цепочечные запросы

Модуль Storage предоставляет гибкий SQL-конструктор запросов в стиле цепочек вызовов, поддерживающий CRUD-операции для пользовательских таблиц.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> Полный API цепочечных запросов (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, транзакции и др.) см. в разделе [SQL-конструктор запросов](../advanced/sql-builder.md).

### Абстракция хранилища

`StorageManager` наследуется от абстрактного базового класса `BaseStorage`, что позволяет расширять поддержку других хранилищ (Redis, MySQL и др.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Асинхронные интерфейсы

Модули Storage и Config предоставляют асинхронные методы (с префиксом `a`), которые можно безопасно вызывать в асинхронных обработчиках. Синхронные методы сохраняются без изменений, что не требует модификации существующего кода.

```python
# Асинхронное хранение
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# Асинхронные массовые операции
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

Управление конфигурационными файлами в формате TOML, поддержка ключевых путей, разделённых точками.

### Обзор API

| Метод | Описание |
|------|------|
| `getConfig(key, default)` | Чтение конфигурации, поддержка точечных путей, например `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | Запись конфигурации. При `immediate=True` немедленно сохраняется в файл |
| `force_save()` | Принудительная запись конфигурации из памяти в файл |
| `reload()` | Перезагрузка конфигурации из файла |
| `agetConfig(key, default)` | Асинхронное чтение конфигурации |
| `asetConfig(key, value, immediate)` | Асинхронная запись конфигурации |
| `aforce_save()` | Асинхронное принудительное сохранение |
| `areload()` | Асинхронная перезагрузка |

### Примеры

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` по умолчанию использует отложенную запись (каждые 5 секунд происходит пакетное сохранение), установка `immediate=True` немедленно сохраняет изменения в конфигурационный файл. Изменения конфигурации запускают событие жизненного цикла `config.set`.

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
child_logger.info("Лог подмодуля")

child_logger.get_child("utils")  # Поддержка вложенных логгеров
```

### Контроль уровня логирования

```python
sdk.logger.set_level("DEBUG")                          # Глобальный уровень
sdk.logger.set_module_level("MyModule", "DEBUG")       # Уровень на уровне модуля

# Поддерживаемые уровни (от низкого к высокому):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE - самый низкий уровень, выводит подробную отладочную информацию (распространение событий, регистрация маршрутов и т.д.)
sdk.logger.set_level("TRACE")                          # Включить все логи
```

### Подписка на логи (режим push)

Для модулей, таких как Dashboard, для получения структурированных логов в реальном времени, поддерживается фильтрация по уровню и отправка истории.

> **Явная подписка на логи низкого уровня**: Уровень `min_level` подписчика может быть ниже глобального уровня логирования. В этом случае логи низкого уровня **отправляются только соответствующему подписчику**, не выводятся в консоль и не записываются в память, тем самым предотвращая загрязнение основного потока логов.
>
> ```python
> # Глобальный уровень INFO, но можно отдельно подписаться на DEBUG логи
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# Способ с декоратором
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
| `handler(id, *, min_level)(func)` | Декоратор/прямой вызов. Если `id` пуст, используется имя функции. `min_level` может быть ниже глобального уровня (логи низкого уровня отправляются только подписчикам, не выводятся в консоль/память). При регистрации автоматически отправляются исторические логи |
| `remove_handler(id)` | Удалить подписчика |

### Контроль вывода

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Модуль адаптера

Менеджер адаптеров, отвечающий за регистрацию, запуск и остановку адаптеров для различных платформ.

### Обзор API

| Метод | Описание |
|------|------|
| `get(platform)` | Получить экземпляр адаптера |
| `exists(platform)` | Проверить, зарегистрирован ли адаптер |
| `enable(platform)` / `disable(platform)` | Включить/выключить адаптер |
| `is_enabled(platform)` | Проверить, включен ли адаптер |
| `startup(platforms)` / `shutdown(platforms)` | Запустить/остановить адаптер |
| `is_running(platform)` | Проверить, запущен ли адаптер |
| `list_running()` | Вывести список всех запущенных адаптеров |
| `platforms` | Получить список всех названий платформ |

### События адаптера

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Запрос состояния бота

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> Полный список API управления адаптерами см. в [API системы адаптеров](adapter-system.md).

## Module Модуль

Менеджер модулей, отвечающий за регистрацию, загрузку и выгрузку плагинов.

### Обзор API

| Метод | Описание |
|------|------|
| `get(name)` | Получить экземпляр модуля или ленивый прокси (возвращает прокси, если модуль зарегистрирован, но не загружен) |
| `exists(name)` | Проверить, зарегистрирован ли модуль |
| `is_loaded(name)` | Проверить, загружен ли модуль |
| `is_enabled(name)` | Проверить, включен ли модуль |
| `enable(name)` / `disable(name)` | Включить/отключить модуль |
| `load(name)` / `unload(name)` | Загрузить/выгрузить модуль |
| `list_registered()` | Вывести список зарегистрированных модулей |
| `list_loaded()` | Вывести список загруженных модулей |
| `get_info(name)` | Получить информацию о модуле |
| `get_status_summary()` | Получить сводку статуса модулей |

### Доступ к свойствам

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # Эквивалентный способ доступа
```

## Модуль Lifecycle

Диспетчер жизненного цикла, основанный на событиях, предоставляющий функции отправки и прослушивания событий.

### Обзор API

| Метод | Описание |
|------|------|
| `on(event, priority=0)` | Декоратор для регистрации обработчика событий, поддерживает сопоставление по точке и подстановочный символ `*` |
| `register(event, handler, priority=0)` | Функциональная регистрация обработчика |
| `unregister(event, handler=None)` | Удаление обработчика |
| `emit(event, data)` | Асинхронное триггерное событие |
| `emit_sync(event, data)` | Синхронное триггерное событие |
| `submit_event(event_type, msg, data, source)` | Отправка события в стандартном формате (совместимость со старыми версиями) |
| `start_timer(id)` / `stop_timer(id)` | Таймер производительности |

### Пример

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Инициализация модуля: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Событие модуля: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})
```

> Полный список стандартных событий и подробное использование см. в разделе [Управление жизненным циклом](../advanced/lifecycle.md).

## Модуль Router

Менеджер маршрутизации HTTP/WebSocket, основанный на FastAPI + Uvicorn, поддерживает маршрутизацию с помощью декораторов, промежуточные слои, группировку, ограничение скорости, CORS.

> Полная документация API маршрутизатора (декораторы маршрутов, WebSocket, промежуточные слои, ограничение скорости, CORS, заголовки безопасности и т.д.) доступна в разделе [Маршрутизатор](../advanced/router.md).

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

## Модуль HTTP-клиента

Единый сетевой клиент, объединяющий HTTP-запросы, подключения WebSocket, управление пулом соединений, автоматическую повторную отправку, статистику запросов и интеграцию событий жизненного цикла.

> Полная документация сетевого клиента (методы запросов, объекты ответов, клиент WebSocket, система исключений и т.д.) доступна в разделе [Сетевой клиент](../advanced/http-client.md).

### Быстрая справка

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

## SDK отладка

### dump_state()

Экспорт текущего состояния работы фреймворка, используется для отладки и диагностики.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

Возвращаемая структура содержит состояние следующих подсистем:

| Поле | Описание |
|------|------|
| `sdk` | Состояние инициализации SDK, версия Python, платформа, временная метка |
| `adapters` | Список зарегистрированных/запущенных адаптеров, статус онлайн-бота на каждой платформе |
| `modules` | Список зарегистрированных/включенных/отключенных/лениво загружаемых модулей |
| `events` | Количество обработчиков различных событий (сообщения/уведомления/запросы/метаданные/команды) |
| `router` | Состояние работы сервера, количество маршрутов HTTP/WebSocket |

> Добавлено начиная с версии 2.5.2

## Связанные документы

- [API-системы событий](event-system.md) - API-модуля Event
- [API-системы адаптеров](adapter-system.md) - API-управления адаптерами
- [SQL-конструктор запросов](../advanced/sql-builder.md) - Полная документация SQL-цепного запроса
- [Менеджер маршрутизации](../advanced/router.md) - Полная документация менеджера маршрутизации
- [Сетевой клиент](../advanced/http-client.md) - Полная документация сетевого клиента
- [Управление жизненным циклом](../advanced/lifecycle.md) - Полная документация жизненного цикла