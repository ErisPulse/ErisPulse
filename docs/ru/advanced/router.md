# Менеджер маршрутизации

Менеджер маршрутизации ErisPulse предоставляет централизованное управление HTTP и WebSocket маршрутизацией, поддерживает регистрацию маршрутов через несколько адаптеров и управление жизненным циклом. В основе лежит абстрактный слой (в данный момент реализован на базе FastAPI + Uvicorn).

## Обзор

Основные функции менеджера маршрутизации:

- **Декораторные маршруты**: Поддержка быстрой регистрации через декораторы `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws`
- **Автоматическая инъекция**: Обработчики маршрутов не требуют импорта типов FastAPI, фреймворк автоматически инъектирует абстрактные объекты
- **Группировка маршрутов**: Поддержка `RouteGroup` с префиксом и номером версии
- **Middleware маршрутов**: Поддержка перехвата запросов с использованием глобальных шаблонов (glob patterns)
- **Ограничение скорости**: Встроенный алгоритм скользящего окна (sliding window rate limiting)
- **Поддержка CORS**: Включение资源共享 между источниками (Cross-Origin Resource Sharing) в один клик
- **Заголовки безопасности**: Автоматическое добавление безопасных заголовков ответа
- **Автоматическая документация**: Интерактивная документация на основе OpenAPI
- **Поддержка WebSocket**: Полное управление подключениями WebSocket, пользовательская аутентификация и хуки жизненного цикла
- **Интеграция жизненного цикла**: Глубокая интеграция с системой жизненного цикла ErisPulse
- **Поддержка SSL/TLS**: Поддержка защищенных подключений HTTPS и WSS

## Абстрактные типы

ErisPulse предоставляет абстрактные типы для серверной части, что позволяет модулям не зависеть напрямую от FastAPI:

| Абстрактный тип | Аналог FastAPI | Описание |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | Обертка HTTP-запроса, интерфейс полностью совместим |
| `WebSocketConnection` | `fastapi.WebSocket` | Обертка WebSocket-соединения, дополнительно предоставляет хуки жизненного цикла |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | Исключение при отключении WebSocket |

> `WebSocketConnection` наследуется от `WebSocketConnectionBase` и совместно использует те же интерфейсы send/receive/iter/close с клиентским WebSocket (`ClientWebSocket`). Клиентские и серверные WebSocket могут использовать один и тот же бизнес-логика код.
>
> Доступ к базовому нативному объекту FastAPI осуществляется через свойство `.raw`. Код, использующий типы FastAPI напрямую, также полностью совместим.

## Декораторные маршруты (Рекомендуется)

### HTTP декораторы

```python
from ErisPulse.Core import router
@router.get("my_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}

# Можно явно указать абстрактный тип
from ErisPulse.Core import HttpRequest

@router.post("my_module", "/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("my_module", "/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("my_module", "/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **Правило автоматической инъекции**: Когда первый параметр обработчика называется `request` или `req` и отсутствует аннотация типа FastAPI, фреймворк автоматически инъектирует `HttpRequest`. Обработчики без параметров или с параметрами, не являющимися запросами, не затрагиваются.

### WebSocket декораторы

```python
from ErisPulse.Core import WebSocketConnection, WebSocketDisconnect

# Базовый WebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket с хуками жизненного цикла
@router.ws("my_module", "/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"Пользователь отключен: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"Ошибка подключения: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket с аутентификацией
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **Примечание**: WebSocket-обработчики и обработчики аутентификации также поддерживают автоматическую инъекцию. Если аннотация параметра — `fastapi.WebSocket`, передается нативный объект; в противном случае передается `WebSocketConnection`.

## Классический способ регистрации

```python
async def hello_handler(request):
    return {"message": "Hello World"}

# Базовая регистрация
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# Регистрация с ограничением скорости и информацией о документации
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="Интерфейс данных",
    tags=["API"],
)
```

### Регистрация WebSocket

```python
from ErisPulse.Core import WebSocketConnection

async def websocket_handler(ws: WebSocketConnection):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# Базовая регистрация
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# Регистрация с аутентификацией (рекомендуется)
async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

**Описание параметров:**

| Параметр | Описание | Значение по умолчанию |
|------|------|--------|
| `module_name` | Имя модуля (обязательно) | - |
| `path` | Путь WebSocket | - |
| `handler` | Функция-обработчик | - |
| `auth_handler` | Функция аутентификации, возвращает `False`, чтобы автоматически закрыть соединение | `None` |
| `auto_accept` | Автоматически ли вызывать `accept()` | `True` |

> **Рекомендация**: Используйте `auth_handler` для подтверждения подключения, вместо отключения `auto_accept`. Устанавливайте `auto_accept=False` только тогда, когда вам нужно полностью контролировать процесс подключения.

## Хуки жизненного цикла WebSocket

`WebSocketConnection` предоставляет регистрацию обратных вызовов для отключения и ошибок, без необходимости вручную использовать try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Регистрация через декоратор
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Причина отключения: {reason}")

    # Можно вызвать напрямую
    async def on_err(ws, error=""):
        print(f"Ошибка: {error}")
    ws.on_error(on_err)

    # Бизнес-логика
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## Группировка маршрутов

```python
# Создание группы маршрутов с префиксом
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# Фактический путь: /my_module/v1/users
```

## Middleware маршрутов

Middleware поддерживает сопоставление путей с использованием глобальных шаблонов (glob patterns):

```python
@router.middleware("/my_module/*")
async def auth_middleware(request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    return await call_next(request)

@router.middleware("/my_module/admin/*")
async def admin_middleware(request, call_next):
    return await call_next(request)
```

## Ограничение скорости (Rate Limiting)

Использование алгоритма скользящего окна (sliding window) для ограничения маршрутов:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Формат ограничения скорости: `{количество}/{интервал времени}`, например, `10/minute`, `100/hour`.

## Конфигурация CORS

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Также можно настроить через `config.toml`:

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## Заголовки безопасности

```python
router.setup_security_headers()
```

Автоматическое добавление безопасных заголовков, таких как `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`.

Также можно настроить через `config.toml`:

```toml
[router.security]
enabled = true
```

## Автоматическая документация

Router по умолчанию включает интерактивную документацию OpenAPI:

```python
# Отключить документацию
router.disable_docs()

# Настроить информацию о документации
router.set_docs_info(
    title="My API",
    description="API документация",
    version="1.0.0"
)
```

## Обработка путей

Путь к маршруту автоматически добавляет имя модуля в качестве префикса, чтобы избежать конфликтов:

```python
# Регистрация пути "/api" в модуль "my_module"
# Фактический путь для доступа: "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## Механизм аутентификации

Рекомендуется использовать `auth_handler` для контроля доступа к подключению:

```python
from ErisPulse.Core import WebSocketConnection

async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

# Декораторный способ
@router.ws("my_module", "/secure_ws", auth_handler=auth_handler)
async def secure_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")

# Классический способ регистрации
router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

Функция `auth_handler` выполняется после установления соединения. Возврат `False` автоматически закрывает соединение (код статуса 1008).

> Устанавливайте `auto_accept=False` только тогда, когда вам нужно полностью контролировать процесс соединения (например, собственный протокол рукопожатия).

## Системные маршруты

Менеджер маршрутизации автоматически предоставляет два системных маршрута:

### Проверка работоспособности

```python
GET /health
# Возвращает:
{"status": "ok", "service": "ErisPulse Router"}
```

### Список маршрутов

```python
GET /routes
# Возвращает информацию обо всех зарегистрированных маршрутах
```

## Интеграция жизненного цикла

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"Сервер запущен: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("Сервер остановлен...")
```

## Рекомендации по использованию

1. **Приоритет абстрактным типам**: Используйте `HttpRequest` / `WebSocketConnection` вместо `fastapi.Request` / `fastapi.WebSocket`, чтобы избежать жестких зависимостей
2. **Используйте автоматическую инъекцию**: Если имя первого параметра обработчика — `request` или `req`, `HttpRequest` будет передан без необходимости в аннотациях типов
3. **Явно передавайте module_name**: Первый параметр декоратора должен быть именем модуля, его нельзя опускать
4. **Используйте группировку маршрутов**: Используйте `group()` для организации нескольких маршрутов одного модуля
5. **Безопасность**: Реализуйте механизмы аутентификации и заголовки безопасности для чувствительных операций
6. **Рациональное ограничение скорости**: Установите лимиты для часто используемых интерфейсов
7. **Используйте хуки жизненного цикла**: Обрабатывайте исключения WebSocket через `@ws.on_disconnect` / `@ws.on_error`, избегая ручного try/catch

## Связанные документы

- [HTTP Клиент](http-client.md) - Отправка запросов с использованием встроенного HTTP-клиента
- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) - Узнайте о регистрации маршрутов модулей
- [Рекомендации по использованию](../developer-guide/modules/best-practices.md) - Советы по использованию маршрутов