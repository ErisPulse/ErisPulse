# API ядра

Документация предоставляет быструю справочную информацию о API ядра ErisPulse, включая сигнатуры методов и краткие описания. Подробное использование и примеры можно найти по ссылкам "Полная документация" для каждого модуля.

## Модуль Storage

Система хранения ключ-значение на базе SQLite, поддерживающая общие SQL-запросы в стиле цепочки.

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

### Доступ к свойствам

```python
sdk.storage.my_key          # эквивалентно sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # эквивалентно sdk.storage.set("my_key", "val")
```

### SQL-цепочка запросов

Модуль Storage предоставляет гибкий SQL-конструктор запросов в стиле цепочки, поддерживающий CRUD-операции для пользовательских таблиц.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> Полный API цепочки запросов (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, транзакции и т.д.) см. в [SQL-конструкторе запросов](../advanced/sql-builder.md).

### Абстракция хранилища

`StorageManager` наследуется от абстрактного базового класса `BaseStorage`, что позволяет расширять поддержку других хранилищ (Redis, MySQL и др.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## Модуль Config

Управление конфигурационными файлами в формате TOML, поддержка ключей с точечной нотацией.

### Обзор API

| Метод | Описание |
|------|------|
| `getConfig(key, default)` | Чтение конфигурации, поддержка точечных путей, например `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | Запись конфигурации. `immediate=True` — немедленное сохранение в файл |
| `force_save()` | Принудительное сохранение конфигурации из памяти в файл |
| `reload()` | Перезагрузка конфигурации из файла |

### Примеры

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` по умолчанию использует отложенную запись (каждые 5 секунд происходит пакетное сохранение), установка `immediate=True` обеспечивает немедленное сохранение в конфигурационный файл. Изменения конфигурации запускают событие жизненного цикла `config.set`.

## Модуль Logger

Модульная система логирования на основе Rich, поддержка под-логгеров и контроля на уровне модулей.

### Основное использование

```python
sdk.logger.debug("Отладочная информация")
sdk.logger.info("Информационные сообщения")
sdk.logger.warning("Предупреждения")
sdk.logger.error("Ошибки")
sdk.logger.critical("Критические ошибки")
```

### Под-логгеры

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Логи подмодуля")

child_logger.get_child("utils")  # поддержка вложенности
```

### Управление уровнем логирования

```python
sdk.logger.set_level("DEBUG")                          # глобальный уровень
sdk.logger.set_module_level("MyModule", "DEBUG")       # уровень для модуля

# Поддерживаемые уровни (от низкого к высокому):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE — самый низкий уровень, выводит подробную отладочную информацию (распространение событий, регистрация маршрутов и т.д.)
sdk.logger.set_level("TRACE")                          # включает все логи
```

### Подписка на логи (режим push)

Позволяет Dashboard и другим модулям получать структурированные логи в реальном времени, поддержка фильтрации по уровню и исторических сообщений.

```python
# декораторный способ
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "Строгий режим:...",
    # }
    pass

# прямой вызов
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Метод | Описание |
|------|------|
| `handler(id, *, min_level)(func)` | Декоратор/прямой вызов. При пустом `id` используется имя функции. При регистрации автоматически отправляются исторические логи |
| `remove_handler(id)` | Удаление подписчика |

### Управление выводом

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Модуль Adapter

Менеджер адаптеров, управление регистрацией, запуском и остановкой адаптеров для различных платформ.

### Обзор API

| Метод | Описание |
|------|------|
| `get(platform)` | Получение экземпляра адаптера |
| `exists(platform)` | Проверка наличия зарегистрированного адаптера |
| `enable(platform)` / `disable(platform)` | Включение/отключение адаптера |
| `is_enabled(platform)` | Проверка включения |
| `startup(platforms)` / `shutdown(platforms)` | Запуск/остановка адаптера |
| `is_running(platform)` | Проверка запущенности адаптера |
| `list_running()` | Список запущенных адаптеров |
| `platforms` | Список всех зарегистрированных платформ |

### События адаптеров

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

> Полный API управления адаптерами см. в [API системы адаптеров](adapter-system.md).

## Модуль Module

Менеджер модулей, управление регистрацией, загрузкой и выгрузкой плагинов.

### Обзор API

| Метод | Описание |
|------|------|
| `get(name)` | Получение экземпляра модуля |
| `exists(name)` | Проверка наличия зарегистрированного модуля |
| `is_loaded(name)` | Проверка загрузки |
| `is_enabled(name)` | Проверка включения |
| `enable(name)` / `disable(name)` | Включение/отключение модуля |
| `load(name)` / `unload(name)` | Загрузка/выгрузка модуля |
| `list_registered()` | Список зарегистрированных модулей |
| `list_loaded()` | Список загруженных модулей |
| `get_info(name)` | Получение информации о модуле |
| `get_status_summary()` | Получение сводки состояния модуля |

### Доступ к свойствам

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # эквивалентный короткий способ
```

## Модуль Lifecycle

Система управления жизненным циклом на основе событий, предоставляет функции отправки и слушания событий.

### Обзор API

| Метод | Описание |
|------|------|
| `on(event, priority=0)` | Декоратор для регистрации обработчика событий, поддержка точечного сопоставления и подстановочных знаков `*` |
| `register(event, handler, priority=0)` | Функциональная регистрация обработчика |
| `unregister(event, handler=None)` | Удаление обработчика |
| `emit(event, data)` | Асинхронный запуск события |
| `emit_sync(event, data)` | Синхронный запуск события |
| `submit_event(event_type, msg, data, source)` | Отправка события в стандартном формате (совместимость с устаревшими версиями) |
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
```

> Полный список стандартных событий и подробное использование см. в [управлении жизненным циклом](../advanced/lifecycle.md).

## Модуль Router

Менеджер маршрутизации HTTP/WebSocket, основанный на FastAPI + Uvicorn, поддержка декораторных маршрутов, промежуточного ПО, группировки, ограничения скорости, CORS.

> Полная документация API маршрутизации (декораторные маршруты, WebSocket, промежуточное ПО, ограничение скорости, CORS, заголовки безопасности и т.д.) см. в [менеджере маршрутизации](../advanced/router.md).

### Быстрый обзор

```python
# HTTP-маршруты
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket-маршруты
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Эхо: {text}")

# Группировка маршрутов
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## Модуль HTTP-клиент

Единый сетевой клиент, объединяющий HTTP-запросы, WebSocket-соединения, управление пулом соединений, автоматические повторные попытки, статистику запросов и интеграцию с событиями жизненного цикла.

> Полная документация сетевого клиента (методы запросов, объекты ответов, WebSocket-клиент, система исключений и т.д.) см. в [сетевом клиенте](../advanced/http-client.md).

### Быстрый обзор

```python
from ErisPulse.Core import client

# HTTP-запросы
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Эхо: {text}")
```

## SDK: отладка

### dump_state()

Экспорт текущего состояния работы фреймворка для отладки и диагностики.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

Возвращаемая структура содержит состояние следующих подсистем:

| Поле | Описание |
|------|------|
| `sdk` | Состояние инициализации SDK, версия Python, платформа, временная метка |
| `adapters` | Список зарегистрированных/запущенных адаптеров, статус онлайн ботов по платформам |
| `modules` | Список зарегистрированных/включенных/отключенных/лениво загруженных модулей |
| `events` | Количество обработчиков событий по категориям (message/notice/request/meta/commands) |
| `router` | Статус работы сервера, количество HTTP/WebSocket-маршрутов |

> Добавлено в 2.5.2

## Связанная документация

- [API системы событий](event-system.md) - API модуля Event
- [API системы адаптеров](adapter-system.md) - API управления адаптерами
- [SQL-конструктор запросов](../advanced/sql-builder.md) - Полная документация SQL-цепочки запросов
- [Менеджер маршрутизации](../advanced/router.md) - Полная документация менеджера маршрутизации
- [Сетевой клиент](../advanced/http-client.md) - Полная документация сетевого клиента
- [Управление жизненным циклом](../advanced/lifecycle.md) - Полная документация управления жизненным циклом