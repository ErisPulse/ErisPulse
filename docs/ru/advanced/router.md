# Маршрутизатор

> [!TIP]
> **Когда нужно читать эту статью**: при необходимости маршрутизации HTTP / WebSocket / SSE (включая трансляцию через пул соединений). Если не требуется — пропустите, это не повлияет на использование других функций.

Маршрутизатор ErisPulse предоставляет единый механизм управления маршрутизацией HTTP и WebSocket, поддерживает регистрацию маршрутов для нескольких адаптеров и управление их жизненным циклом. Внутренняя реализация абстрактного уровня (в настоящее время FastAPI + Uvicorn).

## Обзор

Основные функции маршрутизатора:

- **Маршрутизация с помощью декораторов**: поддержка декораторов `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` для быстрой регистрации
- **Автоматическая инъекция**: обработчики маршрутов не требуют импорта классов FastAPI, фреймворк автоматически инжектирует абстрактные объекты
- **Группировка маршрутов**: поддержка `RouteGroup` с префиксами и версиями
- **Маршрутизация промежуточных обработчиков**: поддержка глобального шаблонного сопоставления запросов
- **Ограничение скорости**: встроенный алгоритм скользящего окна
- **Поддержка CORS**: включение кросс-доменных ресурсов одним кликом
- **Безопасные заголовки**: автоматическое добавление безопасных заголовков ответа
- **Автоматическая документация**: интерактивная документация на основе OpenAPI
- **Поддержка WebSocket**: полное управление подключениями WebSocket, пользовательская аутентификация и хуки жизненного цикла
- **Интеграция с жизненным циклом**: глубокая интеграция с системой жизненного цикла ErisPulse
- **Поддержка SSL/TLS**: поддержка безопасных HTTPS и WSS соединений
- **Главная страница**: поддержка регистрации быстрых кнопок входа модулей на корневом маршруте `/`, поддержка локализации

## Абстрактные типы

ErisPulse предоставляет абстрактные типы для серверной части, позволяя модулям не зависеть напрямую от FastAPI:

| Абстрактный тип | Соответствие FastAPI | Описание |
|----------------|----------------------|----------|
| `HttpRequest` | `fastapi.Request` | Обертка для HTTP-запроса, полностью совместимый интерфейс |
| `WebSocketConnection` | `fastapi.WebSocket` | Обертка для WebSocket-подключения, дополнительные хуки жизненного цикла |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | Исключение разрыва WebSocket-соединения |

> `WebSocketConnection` наследуется от `WebSocketConnectionBase`, и имеет те же интерфейсы send/receive/iter/close, что и клиентский WebSocket (`ClientWebSocket`). Клиентский и серверный WebSocket могут использовать одинаковый бизнес-логический код.
>
> Через свойство `.raw` можно получить доступ к оригинальному объекту FastAPI. Код, использующий типы FastAPI напрямую, также полностью совместим.

## Декораторы маршрутизации (рекомендуется)

### Регистрация маршрутов: одинарный (рекомендуемый) и двойной параметры

Декораторы маршрутизации поддерживают два способа регистрации, **рекомендуется использовать одинарный** — совпадает с триггерами команд / событий, автоматически присваивается пространство имен текущего модуля:

```python
from ErisPulse import router

# Одинарный (рекомендуемый): автоматически присваивается модуль/hello → фактический путь /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# Одинарный WebSocket: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# Двойной параметр: явно указать имя модуля (правила остаются неизменными, используется при регистрации в других модулях/инструментах)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> Одинарный способ требует регистрации в контексте загрузки модуля/адаптера (фреймворк уже инжектирует принадлежность);
> При вызове вне контекста принадлежности будет выброшено исключение `ValueError` с указанием необходимости явно указать имя модуля.

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

> **Правило автоматической инъекции**: если первый параметр обработчика называется `request` или `req` и не имеет аннотации типа FastAPI, фреймворк автоматически инжектирует `HttpRequest`. Обработчики без параметров или с именами параметров, не соответствующими `request`/`req`, не затрагиваются.

#### Ограничение возвращаемых значений (2.10+)

Возвращаемые значения обработчиков поддерживают **формат кортежа** (рекомендуемый способ, явно контролирует код состояния), также допустимы dict/str/Response:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (тело, код_состояния) → JSON с 401
        return {"error": "unauthorized", "message": "invalid token"}, 401
    # (тело, код_состояния, заголовки) также можно добавлять заголовки ответа
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Или использовать вспомогательную функцию respond() (сообщение автоматически объединяется в тело ответа)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Параметры пути / запроса можно использовать с помощью аннотаций FastAPI (например, `item_id: int`, `page: int = 1`), промежуточные обработчики см. в разделе [Маршрутизация промежуточных обработчиков](#маршрутизация-промежуточных-обработчиков).

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

# WebSocket с аутентификацией (токен читается из переменной окружения, не используйте жестко закодированные значения)
import os

async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    expected = os.environ.get("ERISPULSE_WS_TOKEN", "")
    return bool(expected) and token == expected

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **Важно**: WebSocket-обработчики и обработчики аутентификации также поддерживают автоматическую инъекцию. Нет необходимости аннотировать параметры, чтобы получить `WebSocketConnection`. Указание `fastapi.WebSocket` также допускается для передачи оригинального объекта, но рекомендуется использовать абстрактные типы.

### Автоматическая регистрация соединений (пул соединений, 2.10+)

Подключения, созданные с помощью `@ws` / `@sse`, **по умолчанию автоматически регистрируются** в пуле соединений фреймворка (`track=False` отключает это поведение):
внутри handler можно использовать `ws.id` / `ws.join_group(...)`, любые модули могут
`connections.list(namespace=...)` просматривать соединения текущего модуля и транслировать сообщения в группы.
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
    summary="API-интерфейс данных",
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
| `auth_handler` | Функция аутентификации, возвращает `False` для автоматического закрытия соединения | `None` |
| `auto_accept` | Автоматически ли вызывать `accept()` | `True` |

> **Рекомендуется**: использовать `auth_handler` для подтверждения подключения, а не отключать `auto_accept`. Установите `auto_accept=False` только в том случае, если вам нужно полностью контролировать процесс подключения.

## Хуки жизненного цикла WebSocket

`WebSocketConnection` предоставляет обратные вызовы для обработки разрыва и ошибок, без необходимости вручную использовать try/catch:

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

    # Основная бизнес-логика
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

## Маршрутизация промежуточных обработчиков

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

Начиная с версии 2.7.0, каждый HTTP-запрос содержит идентификатор `X-Request-ID`, используемый для логирования / трассировки цепочки запросов:

- **Правило генерации**: сначала используется заголовок `X-Request-ID`, переданный клиентом (для распределённой трассировки); в противном случае генерируется UUID
- **Заголовок ответа**: в ответе возвращается `X-Request-ID`, чтобы клиент мог сопоставить запрос с логами
- **События жизненного цикла**: в данных событий `server.request` и `server.response` добавлено поле `request_id`

```python
# В модуле监听 запросы по request_id для трассировки запросов-ответов
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

Автоматически добавляются безопасные заголовки: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` и др.

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

Пути маршрутов автоматически добавляют префикс с именем модуля, чтобы избежать конфликтов:

```python
# Регистрация пути "/api" для модуля "my_module"
# Фактический путь: "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> Пути маршрутов (включая префикс с именем модуля) **чувствительны к регистру**. Регистрация с именем модуля в верхнем регистре приведет к соответствующему пути: при регистрации модуля "Test" и пути "/api" фактический путь будет "/Test/api", а обращение к "/test/api" вернёт 404.

## Системные маршруты

Маршрутизатор автоматически предоставляет следующие системные маршруты:

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

Главная страница `/` отображает страницу бренда ErisPulse, автоматически определяет доступность Dashboard и добавляет кнопку входа.

## Главная кнопка

Маршрутизатор позволяет внешним модулям регистрировать кнопки быстрого входа на главной странице `/`, чтобы пользователи могли быстро получить доступ к административным страницам модулей.

### Регистрация кнопки

```python
# Простая регистрация
router.register_home_entry(
    name="Мой панель",
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
    name={"i18n": "mymodule.home.entry", "default": "Мой панель"},
    url="/mymodule/admin",
)
```

**Описание параметров:**

| Параметр | Тип | Описание | Обязательно |
|----------|------|----------|------------|
| `name` | `str` / `dict` | Текст кнопки; при передаче словаря `{"i18n": "key", "default": "текст"}` используется локализация | Да |
| `url` | `str` | Адрес ссылки кнопки | Да |
| `icon_svg` | `str` | Необязательный SVG-иконка | Нет |

### Автоматическая регистрация Dashboard

При обнаружении доступности `sdk.Dashboard` маршрутизатор автоматически добавляет кнопку Dashboard в начало списка входов, без необходимости ручной регистрации.

## Интеграция с жизненным циклом

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

1. **Предпочтение абстрактных типов**: используйте `HttpRequest` / `WebSocketConnection` вместо `fastapi.Request` / `fastapi.WebSocket`, чтобы избежать жесткой привязки
2. **Использование автоматической инъекции**: если первый параметр обработчика называется `request` или `req` и не имеет аннотации типа FastAPI, фреймворк автоматически инжектирует `HttpRequest`
3. **Предпочтение одинарного параметра**: в контексте загрузки модуля предпочтительна форма с одним параметром (автоматически присваивается пространство имен); при регистрации в других модулях/инструментах явно указывайте имя модуля
4. **Использование группировки маршрутов**: для нескольких маршрутов одного модуля используйте `group()` для организации
5. **Рассмотрение безопасности**: реализуйте механизмы аутентификации и безопасные заголовки для чувствительных операций
6. **Разумное ограничение скорости**: установите ограничения скорости для часто используемых интерфейсов
7. **Использование хуков жизненного цикла**: обрабатывайте WebSocket-ошибки через `@ws.on_disconnect` / `@ws.on_error`, избегайте ручного try/catch

## Связанные документы

- [Сетевой клиент](client.md) - Использование встроенного HTTP-клиента для отправки запросов
- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) - Ознакомьтесь с регистрацией маршрутов модулей
- [Рекомендуемые практики](../developer-guide/modules/best-practices.md) - Советы по использованию маршрутов