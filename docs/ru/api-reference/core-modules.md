# API Ядерного модуля

Этот документ предоставляет краткий справочник по API модуля ядра ErisPulse, включая сигнатуры методов и краткое описание. Дополнительные сведения о деталях использования и примерах можно найти по ссылкам «Полная документация» в каждом модуле.


```markdown
# Ядерный модуль

ErisPulse использует модульную архитектуру. Основные компоненты системы включают в себя: **ErisPulse**, **Кластер**, **Токен**, **Шина событий**, **Менеджер подключений** и **Утилиты**. Обратите внимание, что токен и другие секретные данные не должны быть видны в коде.

*   **ErisPulse**: Основная библиотека, содержащая все инструменты, необходимые для запуска и управления приложением.
*   **Кластер**: Управляет распределением соединений между узлами.
*   **Токен**: Секретный ключ, связанный с приложением (входит в состав секрета для проверки JWT).
*   **Шина событий**: Система для реализации общих событий и обработчиков.
*   **Менеджер подключений**: Обеспечивает общие подключения к базе данных и другую сетевую инфраструктуру.
*   **Утилиты**: Набор вспомогательных функций для унифицированной обработки данных, системных сообщений, логирования и обработки ошибок.

> **Примечание**:
> 1. Убедитесь, что вы правильно настроили [распределение соединений](docs/ru/configuration/connection-distribution.md).
> 2. Не передавайте и не храните секретные данные в открытом тексте.

## Методы

В этом разделе описаны общие методы, которые можно вызвать из любого места.

| Метод | Описание |
| :--- | :--- |
| `process_request(request_id)` | Принимает `request_id` (идентификатор запроса), определяет тип запроса и соответствующий обработчик. Затем вызывает этот обработчик. |
| `init()` | Инициализирует подключение к базе данных (если оно настроено). Возвращает `Promise<void>`. |
| `start()` | Запускает приложение ErisPulse. Возвращает `Promise<void>`. |
| `stop()` | Останавливает приложение ErisPulse. Возвращает `Promise<void>`. |

## Конфигурация

```typescript
// Доступ к глобальному экземпляру ErisPulse
const pulse = ErisPulse;

// Доступ к конкретным экземплярам модуля
const cluster = pulse.Cluster;
const bus = pulse.Bus;
const token = pulse.Token;
const connectionManager = pulse.ConnectionManager;
```

## Примеры

### Логирование

Этот пример показывает, как вести журнал `INFO` при получении события `token_created`.

```typescript
// Подписка на событие token_created
token.on('token_created', async (payload) => {
    console.log('Токен успешно создан', payload);
    // Логирование в формате INFO
    pulse.Util.logInfo('Токен успешно создан', payload);
});
```

### Запуск приложения

Этот пример демонстрирует базовый сценарий запуска приложения.

```typescript
// Проверяем, загружен ли ErisPulse
if (!ErisPulse) {
    console.error('ErisPulse не найден. Пожалуйста, установите его, запустив `npm install erispulse`.');
    process.exit(1);
}

// Инициализация подключения к базе данных
await pulse.init();

// Запуск приложения
await pulse.start();
```

### Создание токена

Этот пример показывает, как создать новый токен.

```typescript
// Создаем новый токен с именем пользователя
const userToken = await token.create({
    name: 'Имя пользователя',
    permission: 'user',
});

// Создаем токен администратора
const adminToken = await token.create({
    name: 'Администратор',
    permission: 'admin',
});

// Создаем токен с ограниченным доступом
const limitedToken = await token.create({
    name: 'Ограниченный',
    permission: 'limited',
});

// Пример: Создание токена с явным сроком действия
const expiredToken = await token.create({
    name: 'Одноразовый',
    permission: 'single-use',
    expiration: new Date('2023-12-31'), // Срок действия истекает в конце 2023 года
});
```

## Модуль хранилища

База данных на основе SQLite, поддерживающая универсальные SQL-запросы в стиле цепочек вызовов.

### Базовые операции

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

### SQL-запросы в стиле цепочек вызовов

Модуль хранилища предоставляет универсальный конструктор SQL-запросов в стиле цепочек вызовов, поддерживающий операции CRUD для пользовательских таблиц.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> Полная документация по API для запросов в стиле цепочек (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, транзакции и др.) доступна по ссылке [SQL-запросы в стиле цепочек](../ru/advanced/sql-builder.md).

### Абстракция хранилища

`StorageManager` наследуется от абстрактного базового класса `BaseStorage`, что позволяет расширять функциональность для других хранилищ (Redis, MySQL и т.д.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Асинхронный интерфейс

Модули Storage и Config предоставляют асинхронные методы (с префиксом `a`), которые можно безопасно вызывать в асинхронных обработчиках. Синхронные методы остаются доступными, изменения в существующем коде не требуются.

```python
# Асинхронное хранилище
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

## Модуль Config

Управление конфигурационными файлами в формате TOML, поддерживает пути с разделением точками.

### Обзор API

| Метод | Описание |
|------|------|
| `getConfig(key, default)` | Чтение конфигурации, поддерживает пути с точками, например `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | Запись конфигурации. При `immediate=True` сохранение происходит немедленно в файл |
| `force_save()` | Принудительная запись конфигурации из памяти в файл |
| `reload()` | Перезагрузка конфигурации из файла |
| `agetConfig(key, default)` | Асинхронное чтение конфигурации |
| `asetConfig(key, value, immediate)` | Асинхронная запись конфигурации |
| `aforce_save()` | Асинхронная принудительная сохранение |
| `areload()` | Асинхронная перезагрузка |

### Пример

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` по умолчанию использует отложенную запись (групповое сохранение каждые 5 секунд). Установка `immediate=True` позволяет немедленно сохранить конфигурацию в файл. Изменения конфигурации вызывают событие жизненного цикла `config.set`.

## Модуль логирования

Модульная система логирования на основе вывода библиотеки Rich, поддерживающая дочерние логгеры и управление на уровне модулей.

### Базовое использование

```python
sdk.logger.debug("Отладочная информация")
sdk.logger.info("Информация о запуске")
sdk.logger.warning("Предупреждение")
sdk.logger.error("Сообщение об ошибке")
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

# Поддерживаемые уровни (от низкого к высокому):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE — самый низкий уровень, выводит подробные отладочные сообщения изнутри фреймворка (распределение событий, регистрация маршрутов и т.д.)
sdk.logger.set_level("TRACE")                          # Включить все логи
```

### Подписка на логи (Push-режим)

Обеспечивает прием структурированных логов модулями, такими как Dashboard, в реальном времени, с поддержкой фильтрации по уровню и повторной отправки истории.

> **Явная подписка на низкоуровневые логи**: `min_level` подписчика может быть ниже глобального уровня логирования. В этом случае низкоуровневые логи **передаются только соответствующим подписчикам**, они не выводятся в консоль и не записываются в память, что предотвращает загрязнение основного потока логов.
>
> ```python
> # Глобальный уровень — INFO, но можно отдельно подписаться на DEBUG логи
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# Способ через декоратор
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "Строгий режим: ...",
    # }
    pass

# Способ прямого вызова
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Метод | Описание |
|------|------|
| `handler(id, *, min_level)(func)` | Универсальный способ: работает и как декоратор, и при прямом вызове. Если `id` не указан, используется имя функции. Параметр `min_level` может быть ниже глобального уровня (низкоуровневые логи отправляются только подписчикам, не попадая в консоль или память). При регистрации автоматически отправляются исторические логи |
| `remove_handler(id)` | Удаляет подписчика |

### Управление выводом

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)

## Модуль адаптера

Менеджер адаптера, управляющий регистрацией, запуском и остановкой адаптеров для нескольких платформ.

### Обзор API

| Метод | Описание |
|------|------|
| `get(platform)` | Получение экземпляра адаптера |
| `exists(platform)` | Проверка, зарегистрирован ли адаптер |
| `enable(platform)` / `disable(platform)` | Включение / отключение адаптера |
| `is_enabled(platform)` | Проверка, включен ли адаптер |
| `startup(platforms)` / `shutdown(platforms)` | Запуск / остановка адаптера |
| `is_running(platform)` | Проверка, выполняется ли адаптер |
| `list_running()` | Список всех выполняющихся адаптеров |
| `platforms` | Получение списка названий всех платформ |

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

> Полный API управления адаптерами см. в [Системе API адаптера](adapter-system.md).

## Модуль

Менеджер модулей управляет регистрацией, загрузкой и выгрузкой плагинов.

### Обзор API

| Метод | Описание |
|------|------|
| `get(name)` | Получает экземпляр модуля или прокси-объект с отложенной загрузкой (возвращает прокси, если модуль зарегистрирован, но не загружен) |
| `exists(name)` | Проверяет, зарегистрирован ли модуль |
| `is_loaded(name)` | Проверяет, загружен ли модуль |
| `is_enabled(name)` | Проверяет, включен ли модуль |
| `enable(name)` / `disable(name)` | Включает/выключает модуль |
| `load(name)` / `unload(name)` | Загружает/выгружает модуль |
| `list_registered()` | Выводит список зарегистрированных модулей |
| `list_loaded()` | Выводит список загруженных модулей |
| `get_info(name)` | Получает информацию о модуле |
| `get_status_summary()` | Получает сводку по состоянию модулей |

### Доступ к свойствам

```python
module = sdk.module.get("ИмяМодуля")
module = sdk.module.ИмяМодуля
module = sdk.ИмяМодуля  # эквивалентное сокращение

## Модуль Lifecycle

Управление жизненным циклом на основе событий с функциями отправки и прослушивания событий.

### Обзор API

| Метод | Описание |
|------|------|
| `on(event, priority=0)` | Регистрация обработчика событий через декоратор, поддерживает сопоставление с точкой и подстановочный символ `*` |
| `register(event, handler, priority=0)` | Функциональная регистрация обработчика |
| `unregister(event, handler=None)` | Удаление обработчика |
| `emit(event, data)` | Асинхронный запуск события |
| `emit_sync(event, data)` | Синхронный запуск события |
| `submit_event(event_type, msg, data, source)` | Отправка события в стандартном формате (совместимо со старыми версиями) |
| `start_timer(id)` / `stop_timer(id)` | Счётчик производительности |

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

> Полный список стандартных событий и подробное описание использования см. в разделе [Управление жизненным циклом](../advanced/lifecycle.md).

## Модуль Router

Менеджер маршрутизации HTTP/WebSocket на базе FastAPI + Uvicorn, поддерживающий декораторы маршрутизации, middleware, группировку, лимитирование частоты запросов (rate limiting), CORS.

> Более подробную документацию по API маршрутизации (декораторные маршруты, WebSocket, middleware, ограничение скорости запросов, CORS, безопасные заголовки и др.) см. в разделе [Менеджер маршрутизации](../advanced/router.md).

### Краткий обзор

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

## HTTP-клиент

Единый сетевой клиент, объединяющий HTTP-запросы, WebSocket-соединения, управление пулом соединений, автоматические повторы попыток, статистику запросов и интеграцию событий жизненного цикла.

> Подробную документацию по сетевому клиенту (методы запроса, объекты ответа, клиент WebSocket, иерархия исключений и др.) см. в разделе [Сетевой клиент](../ru/advanced/http-client.md).

### Быстрый справочник

```python
from ErisPulse.Core import client

# HTTP-запрос
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Эхо: {text}")

## Отладка SDK

### dump_state()

Экспорт снимка текущего состояния работы фреймворка для целей отладки и диагностики.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

Структура возврата содержит состояние следующих подсистем:

| Поля | Описание |
|------|------|
| `sdk` | Статус инициализации SDK, версия Python, платформа выполнения, метка времени |
| `adapters` | Список зарегистрированных/запущенных адаптеров, статус онлайн-ботов по каждой платформе |
| `modules` | Список зарегистрированных/включенных/отключенных/лениво загруженных модулей |
| `events` | Количество обработчиков различных типов событий (сообщения/уведомления/запросы/мета/команды) |
| `router` | Статус работы сервера, количество маршрутов HTTP/WebSocket |

> Добавлено в 2.5.2

## Документация

- [API системы событий](event-system.md) - API модуля Event
- [API системы адаптеров](adapter-system.md) - API управления адаптерами
- [Конструктор SQL-запросов](../advanced/sql-builder.md) - Полная документация по SQL-запросам в цепочке
- [Менеджер маршрутов](../advanced/router.md) - Полная документация менеджера маршрутов
- [Сетевой клиент](../advanced/http-client.md) - Полная документация сетевого клиента
- [Управление жизненным циклом](../advanced/lifecycle.md) - Полная документация жизненного цикла