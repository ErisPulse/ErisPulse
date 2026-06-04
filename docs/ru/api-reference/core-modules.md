# API модулей ядра

В этом документе подробно описывается API модулей ядра ErisPulse.

## Модуль Storage

### Основные операции

```python
from ErisPulse import sdk

# Установка значения
sdk.storage.set("key", "value")

# Получение значения
value = sdk.storage.get("key", default_value)

# Получение всех ключей
keys = sdk.storage.keys()

# Удаление значения
sdk.storage.delete("key")
```

### Транзакционные операции

```python
# Использование транзакции для обеспечения целостности данных
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # Если какая-либо операция завершится ошибкой, все изменения будут откачены
```

### Пакетные операции

```python
# Пакетная установка
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# Пакетное получение
values = sdk.storage.get_multi(["key1", "key2", "key3"])

# Пакетное удаление
sdk.storage.delete_multi(["key1", "key2", "key3"])
```

### SQL-запросы с цепочкой вызовов

Модуль Storage предоставляет универсальный конструктор SQL-запросов с поддержкой стиля цепного вызова, а также операции CRUD для пользовательских таблиц.

> Дополнительные сведения см. в разделе [SQL Query Builder](../advanced/sql-builder.md), чтобы получить полную документацию.

```python
from ErisPulse import sdk

# Создание пользовательской таблицы
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0"
})

# Вставка данных
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# Пакетная вставка
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]).Execute()

# Запрос данных
rows = (sdk.storage.Table("users")
    .Select("name", "age")
    .Where("age > ?", 18)
    .OrderBy("name")
    .Limit(10)
    .Execute())

# Обновление данных
sdk.storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()

# Удаление данных
sdk.storage.Table("users").Delete().Where("name = ?", "Bob").Execute()

# Подсчет
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# Проверка существования
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()

# Получение одной записи
row = sdk.storage.Table("users").Select("name", "age").Where("name = ?", "Alice").ExecuteOne()

# Изменение структуры таблицы
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# Проверка существования таблицы
if sdk.storage.HasTable("users"):
    sdk.storage.DropTable("users")

# Цепные операции в транзакции
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Dave", "age": 40}).Execute()
    sdk.storage.Table("users").Update({"age": 41}).Where("name = ?", "Dave").Execute()

# Переиспользование условий запроса
base = sdk.storage.Table("users").Where("age > ?", 20)
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()
count = base.copy().Count()
```

### Абстракция хранилища

`StorageManager` наследуется от абстрактного базового класса `BaseStorage` и поддерживает расширение других носителей хранения (Redis, MySQL и т.д.) в будущем.

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

# BaseStorage определяет унифицированный интерфейс: get/set/delete/Table/CreateTable/DropTable и т.д.
# BaseQueryBuilder определяет интерфейс цепного запроса: Select/Insert/Update/Delete/Where/OrderBy/Limit и т.д.
```

## Модуль Config

### Чтение конфигурации

```python
from ErisPulse import sdk

# Получение конфигурации
config = sdk.config.getConfig("MyModule", {})

# Получение вложенной конфигурации
value = sdk.config.getConfig("MyModule.subkey.value", "default")
```

### Запись конфигурации

```python
# Установка конфигурации
sdk.config.setConfig("MyModule", {"key": "value"})

# Установка вложенной конфигурации
sdk.config.setConfig("MyModule.subkey.value", "new_value")
```

### Пример конфигурации

```python
def _load_config(self):
    config = sdk.config.getConfig("MyModule")
    if not config:
        # Создание конфигурации по умолчанию
        default_config = {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "cache_ttl": 3600
        }
        sdk.config.setConfig("MyModule", default_config, immediate=True)  # Третий параметр — true, конфигурация сохраняется немедленно, что удобно для пользователей, позволяя напрямую изменять файл конфигурации
        return default_config
    return config
```

## Модуль Logger

### Базовое логирование

```python
from ErisPulse import sdk

# Различные уровни логирования
sdk.logger.debug("Отладочная информация")
sdk.logger.info("Информация о работе")
sdk.logger.warning("Предупреждение")
sdk.logger.error("Ошибка")
sdk.logger.critical("Критическая ошибка")
```

### Дочерние логгеры

```python
# Получение дочернего логгера
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Лог дочернего модуля")

# Дочерний модуль также может иметь дочерние логгеры, что позволяет точнее управлять выводом логов
child_logger.get_child("utils")
```

### Вывод логов

```python
# Установка файла вывода
sdk.logger.set_output_file("app.log")

# Сохранение логов в файл
sdk.logger.save_logs("log.txt")
```

## Модуль Adapter

### Получение адаптера

```python
from ErisPulse import sdk

# Получение экземпляра адаптера
adapter = sdk.adapter.get("platform_name")

# Доступ через свойства
adapter = sdk.adapter.platform_name
```

### События адаптера

```python
# Прослушивание стандартных событий
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Прослушивание событий определенной платформы
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Прослушивание нативных событий платформы
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### Управление адаптером

```python
# Получение всех платформ
platforms = sdk.adapter.platforms

# Проверка существования адаптера
exists = sdk.adapter.exists("platform_name")

# Включение/Отключение адаптера
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Запуск/Остановка адаптера
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Проверка, запущен ли адаптер
is_running = sdk.adapter.is_running("platform_name")

# Список всех работающих адаптеров
running = sdk.adapter.list_running()
```

## Модуль Module

### Получение модуля

```python
from ErisPulse import sdk

# Получение экземпляра модуля
module = sdk.module.get("ModuleName")

# Доступ через свойства
module = sdk.module.ModuleName
module = sdk.ModuleName
```

### Управление модулем

```python
# Проверка существования модуля
exists = sdk.module.exists("ModuleName")

# Проверка, загружен ли модуль
is_loaded = sdk.module.is_loaded("ModuleName")

# Проверка, включен ли модуль
is_enabled = sdk.module.is_enabled("ModuleName")

# Включение/Отключение модуля
sdk.module.enable("ModuleName")
sdk.module.disable("ModuleName")

# Загрузка модуля
await sdk.module.load("ModuleName")

# Выгрузка модуля
await sdk.module.unload("ModuleName")

# Список загруженных модулей
loaded = sdk.module.list_loaded()

# Список зарегистрированных модулей
registered = sdk.module.list_registered()

# Получение информации о модуле
info = sdk.module.get_info("ModuleName")

# Получение сводки статуса модуля
summary = sdk.module.get_status_summary()
# {"modules": {"ModuleName": {"status": "loaded", "enabled": True, "is_base_module": True}}}

# Проверка, запущен ли модуль (эквивалентно is_loaded)
is_running = sdk.module.is_running("ModuleName")

# Список всех работающих модулей
running = sdk.module.list_running()
```

## Модуль Lifecycle

### Отправка событий

```python
from ErisPulse import sdk

# Отправка пользовательского события
await sdk.lifecycle.submit_event(
    "custom.event",
    data={"key": "value"},
    source="MyModule",
    msg="Описание пользовательского события"
)
```

### Прослушивание событий

```python
# Прослушивание конкретного события
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Инициализация модуля: {event_data}")

# Прослушивание родительских событий
@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Событие модуля: {event_data}")

# Прослушивание всех событий
@sdk.lifecycle.on("*")
async def handle_any_event(event_data):
    print(f"Системное событие: {event_data}")
```

### Таймер

```python
# Запуск таймера
sdk.lifecycle.start_timer("my_operation")

# ... выполнение операции ...

# Получение длительности
duration = sdk.lifecycle.get_duration("my_operation")

# Остановка таймера
total_time = sdk.lifecycle.stop_timer("my_operation")
```

## Модуль Router

### Абстрактные типы

Router поддерживает два стиля аннотаций типов:

```python
# Абстрактные типы ErisPulse (рекомендуются, высокая переносимость)
from ErisPulse.Core import HttpRequest, WebSocketConnection

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}

# Нативные типы FastAPI (совместимы с существующим кодом)
from fastapi import Request, WebSocket

@sdk.router.get("MyModule", "/api2")
async def handler(request: Request):
    return {"status": "ok"}
```

> Система маршрутизации автоматически внедряет объекты соответствующего типа на основе аннотаций параметров. Подробнее см. в разделе [Router Manager](../advanced/router.md).

### Роутинг с использованием декораторов (рекомендуется)

```python
from ErisPulse import sdk
from fastapi import Request

# Декоратор HTTP-маршрута
@sdk.router.http("MyModule", "/api", methods=["GET", "POST"])
async def api_handler(request: Request):
    return {"status": "ok"}

# Декораторы быстрых методов
@sdk.router.get("MyModule", "/info")
async def get_info(request: Request):
    return {"module": "MyModule"}

@sdk.router.post("MyModule", "/data")
async def post_data(request: Request):
    data = await request.json()
    return {"received": data}

@sdk.router.put("MyModule", "/data/{item_id}")
async def put_data(request: Request):
    return {"updated": True}

@sdk.router.delete("MyModule", "/data/{item_id}")
async def delete_data(request: Request):
    return {"deleted": True}

# Декоратор WebSocket
from fastapi import WebSocket

@sdk.router.ws("MyModule", "/ws")
async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# Декоратор WebSocket с аутентификацией
async def ws_auth(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

@sdk.router.ws("MyModule", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

### Традиционный способ регистрации

```python
from ErisPulse import sdk
from fastapi import Request

async def handler(request: Request):
    data = await request.json()
    return {"status": "ok", "data": data}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/api",
    handler=handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="Интерфейс данных",
    tags=["API"],
)

sdk.router.unregister_http_route("MyModule", "/api")
```

### WebSocket-маршруты

```python
from ErisPulse import sdk
from fastapi import WebSocket

async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# Базовая регистрация (автоматически принимает соединение)
sdk.router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# Регистрация с аутентификацией (рекомендуется: используйте auth_handler для контроля соединения)
async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

sdk.router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)

# Отмена маршрута
sdk.router.unregister_websocket("MyModule", "/ws")
```

**Описание параметров:**

| Параметр | Описание | Значение по умолчанию |
|------|------|--------|
| `module_name` | Имя модуля (обязательно) | - |
| `path` | Путь WebSocket | - |
| `handler` | Обработчик | - |
| `auth_handler` | Функция аутентификации, возвращает `False` для автоматического закрытия соединения | `None` |
| `auto_accept` | Автоматически ли вызывать `accept()` | `True` |

> **Рекомендация:** Используйте `auth_handler` для подтверждения соединения вместо отключения `auto_accept`. Устанавливайте `auto_accept=False` только в том случае, если вам требуется полный контроль над процессом соединения.

### Группы маршрутов

```python
# Создание группы маршрутов
group = sdk.router.group("MyModule", prefix="/v1")

# Регистрация маршрутов внутри группы
@group.get("/users")
async def list_users(request: Request):
    return {"users": []}

@group.post("/users")
async def create_user(request: Request):
    return {"created": True}

# Группа с номером версии
v2 = sdk.router.group("MyModule", prefix="/v2", version="2")
```

### Мидлвары (Middleware)

```python
# Глобальные мидлвары (соответствие glob)
@sdk.router.middleware("/MyModule/*")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    response = await call_next(request)
    return response

# Мидлвары для конкретных путей
@sdk.router.middleware("/MyModule/admin/*")
async def admin_middleware(request: Request, call_next):
    return await call_next(request)
```

### Ограничение скорости (Rate Limiting)

```python
# Установка ограничения скорости для маршрута (скользящее окно)
@sdk.router.get("MyModule", "/limited", rate_limit="10/minute")
async def limited_endpoint(request: Request):
    return {"ok": True}

@sdk.router.post("MyModule", "/submit", rate_limit="5/minute")
async def submit_data(request: Request):
    return {"submitted": True}
```

### Конфигурация CORS

```python
# Программный способ
sdk.router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Способ через файл конфигурации (config.toml)
# [router.cors]
# allow_origins = ["https://example.com"]
# allow_methods = ["GET", "POST"]
# allow_headers = ["*"]
```

### Заголовки безопасности

```python
# Автоматическое добавление заголовков безопасности ответа
sdk.router.setup_security_headers()

# Способ через файл конфигурации (config.toml)
# [router.security]
# enabled = true
```

### Автоматическая документация

```python
# Router по умолчанию включает документацию OpenAPI
# Отключение документации
sdk.router.disable_docs()

# Настройка информации о документации
sdk.router.set_docs_info(
    title="My API",
    description="Документация API",
    version="1.0.0"
)
```

### Информация о маршрутах

```python
app = sdk.router.get_app()
```

## Модуль HTTP Client

### Базовые запросы

```python
from ErisPulse.Core import client

# GET-запрос
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# POST-запрос
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# PUT / DELETE / PATCH
resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})

# Универсальный метод request
resp = await client.request("OPTIONS", "https://api.example.com/resource")
```

### Объект ответа

```python
from ErisPulse.Core import client

resp = await client.get("https://api.example.com/users")

resp.status        # int - HTTP-статус (например, 200, 404)
resp.reason        # str | None - описание статуса (например, "OK")
resp.headers       # заголовки ответа (не чувствительны к регистру)
resp.content_type  # str | None - Content-Type
resp.url           # финальный URL (может измениться в зависимости от перенаправлений)
resp.raw           # базовый нативный объект ответа (в данный момент это aiohttp.ClientResponse)

# Чтение тела ответа
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # парсинг JSON
text = await resp.text("gbk")  # указание кодировки
```

### Параметры запроса

| Параметр | Тип | Описание |
|------|------|------|
| `url` | `str` | URL запроса |
| `params` | `dict[str, str]` | Параметры запроса (необязательно) |
| `headers` | `dict[str, str]` | Дополнительные заголовки запроса (необязательно) |
| `data` | `Any` | Тело запроса (форма или необработанные данные) (необязательно) |
| `json` | `Any` | JSON-тело запроса (необязательно) |
| `timeout` | `float` | Тайм-аут запроса (секунды) (необязательно, переопределяет значение по умолчанию) |
| `max_retries` | `int` | Максимальное количество повторных попыток (необязательно, переопределяет значение по умолчанию) |

### Кастомный клиент

```python
from ErisPulse.Core import HttpClient

# Создание кастомного клиента (не глобальный синглтон)
client = HttpClient(
    timeout=60,
    connect_timeout=5,
    max_retries=3,
    retry_delay=2,
    headers={"Authorization": "Bearer token"},
    user_agent="MyBot/1.0",
)

# Контекстный менеджер, автоматически закрывающий сессию
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
```

### Статистика запросов

```python
from ErisPulse.Core import client

# Просмотр статистики
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# Сброс статистики
client.reset_stats()
```

### События жизненного цикла

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

## См. также

- [Система событий API](event-system.md) - API модуля Event
- [API системы адаптеров](adapter-system.md) - API управления адаптером
- [HTTP-клиент](../advanced/http-client.md) - Полная документация HTTP-клиента
- [Router Manager](../advanced/router.md) - Полная документация менеджера маршрутизации