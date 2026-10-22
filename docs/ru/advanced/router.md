# Маршрутизатор

> [!TIP]
> **Когда нужно читать**: при необходимости маршрутизации HTTP / WebSocket / SSE (включая трансляцию в пуле соединений). Если не нужно — пропустите, это не повлияет на использование других функций.

Маршрутизатор ErisPulse обеспечивает единое управление маршрутизацией HTTP и WebSocket, поддерживает регистрацию маршрутов и управление жизненным циклом с помощью нескольких адаптеров. В основе лежит абстрактный слой (в настоящее время FastAPI + Uvicorn).

## Обзор

Основные функции маршрутизатора:

- **Декораторы маршрутизации**: поддержка декораторов `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` для быстрой регистрации
- **Автоматическая инъекция**: обработчики маршрутов не требуют импорта типов FastAPI, фреймворк автоматически инжектирует абстрактные объекты
- **Группировка маршрутов**: поддержка `RouteGroup` с префиксом и номером версии
- **Промежуточные обработчики маршрутов**: поддержка глобального шаблонного сопоставления запросов
- **Ограничение скорости**: встроенный алгоритм скользящего окна
- **Поддержка CORS**: включение кросс-доменных ресурсов одним кликом
- **Безопасные заголовки**: автоматическое добавление заголовков безопасности
- **Автоматическая документация**: интерактивная документация на основе OpenAPI
- **Поддержка WebSocket**: полное управление подключениями WebSocket, пользовательская аутентификация и хуки жизненного цикла
- **Интеграция жизненного цикла**: глубокая интеграция с системой жизненного цикла ErisPulse
- **Поддержка SSL/TLS**: поддержка безопасных подключений HTTPS и WSS
- **Главная страница**: поддержка быстрых кнопок входа модулей по корневому маршруту `/`, поддержка локализации

## Абстрактные типы

ErisPulse предоставляет абстрактные типы сервера, чтобы модули не зависели напрямую от FastAPI:

| Абстрактный тип | Соответствие FastAPI | Описание |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | Обёртка для HTTP-запроса, интерфейс полностью совместим |
| `WebSocketConnection` | `fastapi.WebSocket` | Обёртка для WebSocket-соединения, дополнительно предоставляет хуки жизненного цикла |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | Исключение разрыва WebSocket-соединения |

> `WebSocketConnection` наследуется от `WebSocketConnectionBase` и разделяет с клиентским WebSocket (`ClientWebSocket`) одинаковые интерфейсы send/receive/iter/close. Клиентский и серверный WebSocket могут использовать одинаковый код бизнес-логики.
>
> Через свойство `.raw` можно получить доступ к базовому объекту FastAPI. Код, использующий типы FastAPI напрямую, также полностью совместим.

## Декораторы маршрутизации (рекомендуется)

### Регистрация: одинарный параметр (рекомендуется) и двойной параметр

Декораторы маршрутизации поддерживают два варианта, **рекомендуется одинарный параметр** — согласуется с триггерами команд / событий, пространство имён автоматически присваивается текущему модулю:

```python
from ErisPulse import router

# Одинарный параметр (рекомендуется): автоматически присваивается модуль/имя/hello → фактический путь /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# Одинарный WebSocket: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# Двойной параметр: явно указать имя модуля (правила не меняются, используется при регистрации между модулями/инструментальным кодом)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> Одинарный параметр требует регистрации в контексте загрузки модуля/адаптера (фреймворк уже инжектирует принадлежность во время загрузки);
> Вызов вне контекста принадлежности вызовет `ValueError` с указанием необходимости явного указания имени модуля.

### HTTP-декораторы

```python
from ErisPulse import router, HttpRequest

# Можно также явно указать абстрактный тип
@router.post("/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **Правила автоматической инъекции**: когда первый параметр обработчика называется `request` или `req` и не имеет аннотации типа FastAPI, фреймворк автоматически инжектирует `HttpRequest`. Обработчики без параметров или с параметрами, не являющимися запросом, не затрагиваются.

#### Соглашение о возвращаемых значениях (2.10+)

Возвращаемое значение обработчика поддерживает **соглашение о кортеже** (рекомендуемый способ, явно контролирует статус-код), dict/str/Response остаются прежними:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "токен недействителен"}, 401
    # (body, status_code, headers) также можно добавить заголовки ответа
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Или использовать вспомогательную функцию respond() (сообщение автоматически объединяется в тело ответа)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Параметры пути / запроса можно использовать напрямую с аннотациями FastAPI (например, `item_id: int` или `page: int = 1`), промежуточные обработчики см. в разделе [Промежуточные обработчики маршрутов](#промежуточные-обработчики-маршрутов).

### WebSocket-декораторы

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# Базовый WebSocket (одинарный параметр)
@router.ws("ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket с хуками жизненного цикла
@router.ws("/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"Пользователь отключился: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"Ошибка подключения: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket с аутентификацией
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **Важно**: обработчики WebSocket и аутентификации также поддерживают автоматическую инъекцию. Без аннотации параметра можно получить `WebSocketConnection`. Указание `fastapi.WebSocket` также может передать оригинальный объект, но рекомендуется использовать абстрактные типы.

### Автоматическая регистрация соединений (пул соединений, 2.10+)

Подключения, созданные с помощью `@ws` / `@sse`, **по умолчанию автоматически регистрируются** в пуле фреймворка (`track=False` отключает эту функцию):
внутри handler `ws.id` / `ws.join_group(...)` доступны, любые модули могут
`connections.list(namespace=...)` просматривать соединения текущего модуля, транслировать в группы.
См. [Пул соединений и трансляция](connections.md).

## Традиционный способ регистрации

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

# С ограничением скорости и информацией о документации
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
| `handler` | Обработчик | - |
| `auth_handler` | Функция аутентификации, возвращает `False` автоматически закроет соединение | `None` |
| `auto_accept` | Автоматически ли вызывать `accept()` | `True` |

> **Рекомендуется**: использовать `auth_handler` для подтверждения соединения, а не отключать `auto_accept`. Только если вы хотите полностью контролировать процесс соединения, установите `auto_accept=False`.

## Хуки жизненного цикла WebSocket

`WebSocketConnection` предоставляет обратные вызовы для отключения и ошибок, без необходимости ручного try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Регистрация декоратором
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Причина отключения: {reason}")

    # Также можно вызывать напрямую
    async def on_err(ws, error=""):
        print(f"Ошибка: {error}")
    ws.on_error(on_err)

    # Обычная бизнес-логика
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## Группировка маршрутов

```python
# Создание маршрутов с префиксом
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# Фактический путь: /my_module/v1/users
```

## Промежуточные обработчики маршрутов

Промежуточные обработчики поддерживают шаблоны сопоставления путей:

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

## Идентификатор запроса (X-Request-ID)

Начиная с версии 2.7.0, каждый HTTP-запрос будет содержать идентификатор `X-Request-ID`, используемый для логирования / трассировки цепочки:

- **Правила генерации**: приоритетно используется `X-Request-ID` из заголовка запроса клиента (для распределённой трассировки); в противном случае генерируется UUID
- **Заголовок ответа**: ответ будет возвращать `X-Request-ID`, что позволяет клиенту сопоставить запрос с логами
- **События жизненного цикла**: в данных событий `server.request` и `server.response` добавлено поле `request_id`

```python
# В модуле прослушивание событий запроса, по request_id сопоставляются запрос-ответ
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

Клиент может задать собственный ID для трассировки между сервисами:

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## Ограничение скорости

Использование алгоритма скользящего окна для ограничения скорости маршрутов:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Формат ограничения скорости: `{количество}/{временной интервал}`, например `10/minute`, `100/hour`.

## Настройка CORS

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

## Безопасные заголовки

```python
router.setup_security_headers()
```

Автоматически добавляются безопасные заголовки, такие как `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` и др.

Также можно настроить через `config.toml`:

```toml
[router.security]
enabled = true
```

## Автоматическая документация

Router по умолчанию включает интерактивную документацию OpenAPI:

```python
# Отключение документации
router.disable_docs()

# Настройка информации документации
router.set_docs_info(
    title="My API",
    description="API 文档",
    version="1.0.0"
)
```

## Обработка путей

Пути маршрутов автоматически добавляют префикс имени модуля, чтобы избежать конфликтов:

```python
# Регистрация пути "/api" в модуле "my_module"
# Фактический путь доступа: "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> Пути маршрутов (включая префикс имени модуля) **чувствительны к регистру**. При регистрации модульное имя каким регистром указано, таким и будет путь: при модульном имени `Test` путь `/api` будет `/Test/api`, обращение `/test/api` вернёт 404.

## Системные маршруты

Маршрутизатор автоматически предоставляет следующие системные маршруты:

### Проверка состояния

```
GET /health
# Возвращает:
{"status": "ok", "service": "ErisPulse Router"}
```

### Главная страница

```
GET /
# Возвращает страницу бренда ErisPulse
```

Главная страница `/` отображает страницу бренда ErisPulse, автоматически проверяет доступность Dashboard и добавляет кнопки входа.

## Главная кнопка

Маршрутизатор позволяет внешним модулям регистрировать кнопки быстрого входа на корневом маршруте `/`, что удобно для быстрого доступа к страницам управления модулями.

### Регистрация кнопки

```python
# Простая регистрация
router.register_home_entry(
    name="Моя панель",
    url="/mymodule/admin",
)

# Регистрация с иконкой (SVG)
router.register_home_entry(
    name="Консоль",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# Регистрация с поддержкой локализации (формат словаря i18n проекта)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "Моя панель"},
    url="/mymodule/admin",
)
```

**Описание параметров:**

| Параметр | Тип | Описание | Обязательно |
|------|------|------|------|
| `name` | `str` / `dict` | Текст кнопки; при передаче словаря `{"i18n": "key", "default": "текст"}` используется локализация | Да |
| `url` | `str` | Адрес ссылки кнопки | Да |
| `icon_svg` | `str` | Необязательный SVG-иконка | Нет |

### Автоматическая регистрация Dashboard

При обнаружении доступности `sdk.Dashboard` маршрутизатор автоматически добавляет кнопку Dashboard в начало списка входов, без необходимости ручной регистрации.

## Интеграция жизненного цикла

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"Сервер запущен: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("Сервер останавливается...")
```

## Лучшие практики

1. **Предпочтение абстрактных типов**: использовать `HttpRequest` / `WebSocketConnection` вместо `fastapi.Request` / `fastapi.WebSocket`, чтобы избежать жёсткой зависимости
2. **Использование автоматической инъекции**: первый параметр обработчика должен называться `request` или `req`, без аннотации типа FastAPI, чтобы получить `HttpRequest`
3. **Предпочтение одинарного параметра**: в контексте загрузки модуля предпочтительно одинарный параметр (автоматическое присвоение пространства имён); при регистрации между модулями/инструментальным кодом явно указывать имя модуля
4. **Использование группировки маршрутов**: использовать `group()` для организации нескольких маршрутов одного модуля
5. **Рассмотрение безопасности**: реализовать механизмы аутентификации и безопасные заголовки для чувствительных операций
6. **Разумное ограничение скорости**: установить ограничение скорости для частых интерфейсов
7. **Использование хуков жизненного цикла**: использовать `@ws.on_disconnect` / `@ws.on_error` для обработки ошибок WebSocket, избегая ручного try/catch

## Связанные документы

- [HTTP-клиент](http-client.md) - Использование встроенного HTTP-клиента для отправки запросов
- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) - Ознакомьтесь с регистрацией маршрутов модуля
- [Лучшие практики](../developer-guide/modules/best-practices.md) - Рекомендации по использованию маршрутов