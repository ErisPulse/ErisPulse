# Менеджер маршрутизации

Менеджер маршрутизации ErisPulse обеспечивает единое управление HTTP и WebSocket маршрутизацией, поддерживает регистрацию маршрутов для нескольких адаптеров и управление их жизненным циклом. В основе лежит абстрактный уровень, реализованный на базе FastAPI + Uvicorn.

## Обзор

Основные функции менеджера маршрутизации:

- **Декораторы маршрутов**: поддержка декораторов `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` для быстрой регистрации
- **Автоматическая инъекция**: обработчики маршрутов не требуют импорта типов FastAPI, фреймворк автоматически инжектирует абстрактные объекты
- **Группировка маршрутов**: поддержка `RouteGroup` с префиксом и версией
- **Маршрутизационные промежуточные обработчики**: поддержка глобального шаблонного сопоставления запросов
- **Ограничение скорости**: встроенный алгоритм скользящего окна
- **Поддержка CORS**: возможность включить кросс-доменные ресурсы одним кликом
- **Безопасные заголовки**: автоматическое добавление безопасных заголовков ответа
- **Автоматическая документация**: интерактивная документация на основе OpenAPI
- **Поддержка WebSocket**: полное управление WebSocket соединениями, пользовательская аутентификация и хуки жизненного цикла
- **Интеграция жизненного цикла**: глубокая интеграция с системой жизненного цикла ErisPulse
- **Поддержка SSL/TLS**: поддержка HTTPS и WSS безопасных соединений
- **Главная страница**: возможность регистрации модуля на корневом маршруте `/` с кнопками быстрого доступа, поддержка локализации

## Абстрактные типы

ErisPulse предоставляет абстрактные типы для серверной части, позволяя модулям не зависеть напрямую от FastAPI:

| Абстрактный тип | Соответствие в FastAPI | Описание |
|-----------------|------------------------|----------|
| `HttpRequest` | `fastapi.Request` | Обертка для HTTP-запроса, интерфейс полностью совместим |
| `WebSocketConnection` | `fastapi.WebSocket` | Обертка для WebSocket-соединения, дополнительно предоставляет хуки жизненного цикла |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | Исключение разрыва WebSocket-соединения |

> `WebSocketConnection` наследуется от `WebSocketConnectionBase` и разделяет с клиентским WebSocket (`ClientWebSocket`) одинаковые интерфейсы send/receive/iter/close. Клиентский и серверный WebSocket могут использовать одинаковый бизнес-логический код.
>
> Через свойство `.raw` можно получить доступ к базовому объекту FastAPI. Код, использующий типы FastAPI напрямую, также полностью совместим.

## Декораторы маршрутов (рекомендуется)

### Регистрация маршрутов: одиночный и двойной параметры

Декораторы маршрутов поддерживают два способа регистрации, **рекомендуется использовать одиночный параметр** — он автоматически присваивает пространство имен текущему модулю:

```python
from ErisPulse import router

# Одиночный параметр (рекомендуется): автоматически присваивается модуль/hello → фактический путь /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# Одиночный WebSocket: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# Двойной параметр: явно указать имя модуля (используется при регистрации в других модулях/инструментальном коде)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> При использовании одиночного параметра требуется регистрация в контексте загрузки модуля/адаптера (фреймворк уже инжектирует принадлежность); вызов вне контекста загрузки приведет к выбросу `ValueError` и указанию на необходимость явного указания имени модуля.

### HTTP декораторы

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

> **Правила автоматической инъекции**: если первый параметр обработчика называется `request` или `req` и не имеет аннотации типа FastAPI, фреймворк автоматически инжектирует `HttpRequest`. Обработчики без параметров или с другими именами параметров не затрагиваются.

#### Соглашение о возвращаемых значениях (2.10+)

Возвращаемые значения обработчиков поддерживают **кортежное соглашение** (рекомендуемый способ, позволяет четко контролировать код состояния), а также dict/str/Response по-прежнему допустимы:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (тело, код_состояния) → 401 JSON
        return {"error": "unauthorized", "message": "неверный токен"}, 401
    # (тело, код_состояния, заголовки) также можно добавить заголовки ответа
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Или с помощью вспомогательной функции respond() (сообщение автоматически объединяется в тело ответа)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Параметры пути / запроса можно использовать через оригинальные аннотации FastAPI (`item_id: int`, `page: int = 1`), промежуточные обработчики см. в разделе [Маршрутизационные промежуточные обработчики](#маршрутизационные-промежуточные-обработчики).

### WebSocket декораторы

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# Базовый WebSocket (одиночный параметр)
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
        print(f"Ошибка соединения: {error}")

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

> **Важно**: обработчики WebSocket и аутентификации также поддерживают автоматическую инъекцию. Нет необходимости аннотировать параметры, чтобы получить `WebSocketConnection`. Указание `fastapi.WebSocket` также допустимо для передачи оригинального объекта, но рекомендуется использовать абстрактный тип.

### Автоматическая регистрация подключений (пул подключений, 2.10+)

Подключения, созданные с помощью `@ws` / `@sse`, **по умолчанию регистрируются** в пуле подключений фреймворка (отключение возможно с помощью `track=False`):  
внутри обработчика доступны `ws.id` / `ws.join_group(...)`, произвольный модуль может  
`connections.list(namespace=...)` просматривать подключения текущего модуля и рассылать сообщения группам.  
См. [Пул подключений и рассылка](connections.md).

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
    summary="Данные API",
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
|----------|----------|-----------------------|
| `module_name` | Имя модуля (обязательно) | - |
| `path` | Путь WebSocket | - |
| `handler` | Обработчик | - |
| `auth_handler` | Функция аутентификации, возвращает `False`, чтобы автоматически закрыть соединение | `None` |
| `auto_accept` | Автоматически ли принимать соединение | `True` |

> **Рекомендуется**: использовать `auth_handler` для подтверждения соединения, а не отключать `auto_accept`. Только если вам нужно полностью контролировать процесс соединения, устанавливайте `auto_accept=False`.

## Хуки жизненного цикла WebSocket

`WebSocketConnection` предоставляет обратные вызовы для отключения и ошибок, без необходимости вручную использовать try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Регистрация через декоратор
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Причина отключения: {reason}")

    # Также можно вызывать напрямую
    async def on_err(ws, error=""):
        print(f"Ошибка: {error}")
    ws.on_error(on_err)

    # Основная бизнес-логика
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

## Маршрутизационные промежуточные обработчики

Промежуточные обработчики поддерживают шаблоны glob для сопоставления путей:

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

Начиная с версии 2.7.0, каждый HTTP-запрос будет содержать уникальный `X-Request-ID`, используемый для логирования и трассировки цепочек:

- **Правило генерации**: приоритетно используется `X-Request-ID` из заголовка запроса (для распределённой трассировки); в противном случае генерируется UUID
- **Заголовок ответа**: ответ будет возвращать `X-Request-ID`, что позволяет клиенту сопоставить запрос с логами
- **События жизненного цикла**: в данных событий `server.request` и `server.response` добавлено поле `request_id`

```python
# В модуле отслеживание событий запроса по request_id для последовательного отображения запроса-ответа
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

Используется алгоритм скользящего окна для ограничения скорости маршрутов:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Формат ограничения скорости: `{количество}/{временной_интервал}`, например `10/minute`, `100/hour`.

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

Автоматически добавляются безопасные заголовки, такие как `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` и другие.

Также можно настроить через `config.toml`:

```toml
[router.security]
enabled = true
```

## Автоматическая документация

Router по умолчанию включает интерактивную документацию на основе OpenAPI:

```python
# Отключение документации
router.disable_docs()

# Настройка информации документации
router.set_docs_info(
    title="My API",
    description="API文档",
    version="1.0.0"
)
```

## Обработка путей

Маршруты автоматически добавляют префикс с именем модуля, чтобы избежать конфликтов:

```python
# Регистрация пути "/api" для модуля "my_module"
# Фактический путь доступа: "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> Маршруты (включая префикс с именем модуля) **чувствительны к регистру**. Имя модуля должно быть в том же регистре, что и при регистрации: если имя модуля `Test`, путь `/api` будет `/Test/api`, а обращение `/test/api` вернет 404.

## Системные маршруты

Менеджер маршрутизации автоматически предоставляет следующие системные маршруты:

### Проверка здоровья

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

Главная страница `/` отображает страницу бренда ErisPulse, автоматически проверяет доступность Dashboard и добавляет кнопку входа.

## Главная кнопка

Менеджер маршрутизации позволяет внешним модулям регистрировать кнопки быстрого доступа на главной странице `/`, что позволяет пользователям быстро открывать страницы управления модулями.

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

# Поддержка локализации (формат словаря i18n проекта)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "Моя панель"},
    url="/mymodule/admin",
)
```

**Описание параметров:**

| Параметр | Тип | Описание | Обязательно |
|----------|------|----------|------|
| `name` | `str` / `dict` | Текст отображения кнопки; при передаче словаря `{"i18n": "key", "default": "текст"}` используется локализация | Да |
| `url` | `str` | Адрес ссылки кнопки | Да |
| `icon_svg` | `str` | Необязательный SVG-иконка | Нет |

### Автоматическая регистрация Dashboard

При обнаружении доступности `sdk.Dashboard` менеджер маршрутизации автоматически добавляет кнопку Dashboard в начало списка входов, без необходимости ручной регистрации.

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

## Рекомендуемые практики

1. **Использование абстрактных типов**: замените `fastapi.Request` / `fastapi.WebSocket` на `HttpRequest` / `WebSocketConnection`, чтобы избежать жесткой зависимости
2. **Использование автоматической инъекции**: если первый параметр обработчика называется `request` или `req`, без аннотации типа FastAPI, получите `HttpRequest`
3. **Явное указание module_name**: первый параметр декоратора должен быть именем модуля, его нельзя опускать
4. **Использование группировки маршрутов**: организуйте несколько маршрутов одного модуля с помощью `group()`
5. **Рассмотрение безопасности**: реализуйте механизмы аутентификации и безопасные заголовки для чувствительных операций
6. **Разумное ограничение скорости**: установите ограничение скорости для частых интерфейсов
7. **Использование хуков жизненного цикла**: обрабатывайте ошибки WebSocket с помощью `@ws.on_disconnect` / `@ws.on_error`, избегайте ручного try/catch

## Связанная документация

- [HTTP клиент](http-client.md) - Использование встроенного HTTP клиента для отправки запросов
- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) - Ознакомьтесь с регистрацией маршрутов модулей
- [Лучшие практики](../developer-guide/modules/best-practices.md) - Рекомендации по использованию маршрутов