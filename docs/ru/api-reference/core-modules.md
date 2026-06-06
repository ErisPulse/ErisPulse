# API основных модулей ядра

В этом документе представлен быстрый справочник по API основных модулей ядра ErisPulse, включая сигнатуры методов и краткое описание. Подробные инструкции и примеры доступны по ссылкам "Полная документация" для каждого модуля.

## Модуль Storage

Базирующаяся на SQLite система хранения ключей, поддерживающая универсальный конструктор SQL-запросов со стилем цепного вызова.

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

### Доступ по атрибутам

```python
sdk.storage.my_key          # Эквивалент sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # Эквивалент sdk.storage.set("my_key", "val")
```

### SQL-запросы с цепочкой вызовов

Модуль Storage предоставляет универсальный конструктор SQL-запросов со стилем цепного вызова, поддерживающий CRUD-операции для пользовательских таблиц.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> Полное API для цепных запросов (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, транзакции и т.д.) см. в разделе [SQL Query Builder](../advanced/sql-builder.md).

### Абстракция хранилища

`StorageManager` наследуется от абстрактного базового класса `BaseStorage` и поддерживает расширение других носителей хранения (Redis, MySQL и т.д.) в будущем.

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## Модуль Config

Управление файлами конфигурации в формате TOML, поддерживающее раздельные по точкам пути ключей.

### Обзор API

| Метод | Описание |
|------|------|
| `getConfig(key, default)` | Чтение конфигурации, поддерживает пути с точками, например `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | Запись конфигурации. При `immediate=True` сохранение в файл выполняется немедленно |
| `force_save()` | Принудительная запись конфигурации из памяти в файл |
| `reload()` | Перезагрузка конфигурации из файла |

### Пример

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> По умолчанию `setConfig` использует отложенную запись (пакетное сохранение каждые 5 секунд). Установка `immediate=True` обеспечивает немедленное постоянное сохранение в файл. Изменения конфигурации запускают событие жизненного цикла `config.set`.

## Модуль Logger

Модульная система логирования, основанная на Rich, поддерживающая вложенные дочерние логгеры и управление уровнем на уровне модулей.

### Базовое использование

```python
sdk.logger.debug("Отладочная информация")
sdk.logger.info("Информация о работе")
sdk.logger.warning("Предупреждение")
sdk.logger.error("Ошибка")
sdk.logger.critical("Критическая ошибка")
```

### Дочерние логгеры

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Лог дочернего модуля")

child_logger.get_child("utils")  # Поддержка вложенности
```

### Управление уровнем логирования

```python
sdk.logger.set_level("DEBUG")                          # Глобальный уровень
sdk.logger.set_module_level("MyModule", "DEBUG")       # Уровень модуля
```

### Управление выводом

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Модуль Adapter

Менеджер адаптеров, управляющий регистрацией, запуском и остановкой адаптеров для нескольких платформ.

### Обзор API

| Метод | Описание |
|------|------|
| `get(platform)` | Получение экземпляра адаптера |
| `exists(platform)` | Проверка, зарегистрирован ли адаптер |
| `enable(platform)` / `disable(platform)` | Включение/Отключение адаптера |
| `is_enabled(platform)` | Проверка, включен ли адаптер |
| `startup(platforms)` / `shutdown(platforms)` | Запуск/Остановка адаптеров |
| `is_running(platform)` | Проверка, запущен ли адаптер |
| `list_running()` | Список всех запущенных адаптеров |
| `platforms` | Получение списка имен всех платформ |

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

> Полный API управления адаптерами см. в разделе [Adapter System API](adapter-system.md).

## Модуль Module

Менеджер модулей, управляющий регистрацией, загрузкой и выгрузкой плагинов.

### Обзор API

| Метод | Описание |
|------|------|
| `get(name)` | Получение экземпляра модуля |
| `exists(name)` | Проверка, зарегистрирован ли модуль |
| `is_loaded(name)` | Проверка, загружен ли модуль |
| `is_enabled(name)` | Проверка, включен ли модуль |
| `enable(name)` / `disable(name)` | Включение/Отключение модуля |
| `load(name)` / `unload(name)` | Загрузка/Выгрузка модуля |
| `list_registered()` | Список зарегистрированных модулей |
| `list_loaded()` | Список загруженных модулей |
| `get_info(name)` | Получение информации о модуле |
| `get_status_summary()` | Получение сводки статуса модуля |

### Доступ по атрибутам

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # Эквивалентная сокращенная запись
```

## Модуль Lifecycle

Менеджер жизненного цикла, управляемый событиями, предоставляющий функционал отправки и прослушивания событий.

### Обзор API

| Метод | Описание |
|------|------|
| `on(event, priority=0)` | Регистрация обработчика событий с помощью декоратора, поддерживает точечное совпадение и подстановочный знак `*` |
| `register(event, handler, priority=0)` | Функциональная регистрация обработчика |
| `unregister(event, handler=None)` | Удаление обработчика |
| `emit(event, data)` | Асинхронный запуск события |
| `emit_sync(event, data)` | Синхронный запуск события |
| `submit_event(event_type, msg, data, source)` | Отправка события в стандартном формате (совместимо с предыдущими версиями) |
| `start_timer(id)` / `stop_timer(id)` | Системный таймер для измерения производительности |

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

> Полный список стандартных событий и подробное описание см. в разделе [Lifecycle Management](../advanced/lifecycle.md).

## Модуль Router

Менеджер маршрутизации HTTP/WebSocket, основанный на FastAPI + Uvicorn, поддерживающий декораторную маршрутизацию, промежуточное ПО, группы, ограничение частоты запросов (Rate Limiting), CORS.

> Полный документ по API маршрутизации (декораторная маршрутизация, WebSocket, middleware, Rate Limiting, CORS, заголовки безопасности и т.д.) см. в разделе [Router Manager](../advanced/router.md).

### Быстрый справочник

```python
# HTTP маршруты
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket маршруты
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

Унифицированный HTTP/WS клиент на основе aiohttp, предоставляющий статистику запросов, повторные попытки, логирование и систему исключений ErisPulse.

> Полная документация HTTP клиента (методы запросов, объекты ответов, WebSocket клиент, система исключений и т.д.) см. в разделе [HTTP Client](../advanced/http-client.md).

### Быстрый справочник

```python
from ErisPulse.Core import client

# HTTP запросы
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## См. также

- [Система событий API](event-system.md) - API модуля Event
- [API системы адаптеров](adapter-system.md) - API управления адаптером
- [SQL Query Builder](../advanced/sql-builder.md) - Полная документация по SQL-запросам
- [Router Manager](../advanced/router.md) - Полная документация менеджера маршрутизации
- [HTTP Client](../advanced/http-client.md) - Полная документация HTTP клиента
- [Lifecycle Management](../advanced/lifecycle.md) - Полная документация жизненного цикла