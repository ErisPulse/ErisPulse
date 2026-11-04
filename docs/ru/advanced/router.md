# Маршрутизатор

> [!TIP]
> **Когда нужно читать эту статью**: Когда нужны HTTP / WebSocket / SSE маршруты (включая трансляцию в пуле соединений). Если не нужно, пропустите, это не повлияет на использование других функций.

Маршрутизатор ErisPulse обеспечивает единое управление HTTP и WebSocket маршрутизацией, поддерживает регистрацию маршрутов с несколькими адаптерами и управление жизненным циклом. Внутренне маршрутизатор использует абстракцию (в настоящее время FastAPI + Uvicorn).

## Обзор

Основные функции маршрутизатора:

- **Декоратор маршрутизации**: Поддержка декораторов `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` для быстрой регистрации
- **Автоматическая инъекция**: Обработчики маршрутов не требуют импорта типов FastAPI, фреймворк автоматически вставляет абстрактные объекты
- **Группировка маршрутов**: Поддержка `RouteGroup` с префиксом и версией
- **Маршрутизация промежуточного ПО**: Поддержка глобального шаблонного сопоставления запросов
- **Ограничение скорости**: Встроенный алгоритм скользящего окна
- **Поддержка CORS**: Включение кросс-доменного ресурсообмена
- **Безопасные заголовки**: Автоматическое добавление безопасных заголовков ответа
- **Автоматическая документация**: Интерактивная документация на основе OpenAPI
- **Поддержка WebSocket**: Полное управление WebSocket соединениями, пользовательская аутентификация и хуки жизненного цикла
- **Интеграция жизненного цикла**: Глубокая интеграция с системой жизненного цикла ErisPulse
- **Поддержка SSL/TLS**: Поддержка HTTPS и WSS безопасных соединений
- **Главная страница**: Поддержка регистрации кнопок быстрого доступа модулей на корневом маршруте `/`, поддержка локализации

## Абстрактные типы

ErisPulse предоставляет абстрактные типы для сервера, чтобы модули не зависели напрямую от FastAPI:

| Абстрактный тип | Соответствие FastAPI | Описание |
|----------------|----------------------|----------|
| `HttpRequest` | `fastapi.Request` | Обёртка для HTTP запроса, интерфейс полностью совместим |
| `WebSocketConnection` | `fastapi.WebSocket` | Обёртка для WebSocket соединения, дополнительно предоставляются хуки жизненного цикла |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | Исключение разрыва WebSocket соединения |

> `WebSocketConnection` наследуется от `WebSocketConnectionBase`, и имеет те же send/receive/iter/close интерфейсы, что и клиентский WebSocket (`ClientWebSocket`). Клиентский и серверный WebSocket могут использовать одинаковый бизнес-логический код.
>
> Через `.raw` свойство можно получить доступ к базовому объекту FastAPI. Код, использующий типы FastAPI напрямую, также полностью совместим.

## Декоратор маршрутизации (рекомендуется)

### Регистрация: одинарный и двойной параметры

Декоратор маршрутизации поддерживает два способа регистрации, **рекомендуется одинарный параметр** — он совместим с триггерами команд / событий, и пространство имён автоматически присваивается текущему модулю:

```python
from ErisPulse import router

# Одинарный параметр (рекомендуется): автоматически присваивается модуль/имя → фактический путь /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# Одинарный WebSocket: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# Двойной параметр: явно указать имя модуля (правила не меняются, используется при регистрации в других модулях/инструментальном коде)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> Одинарный параметр требует регистрации в контексте загрузки модуля/адаптера (фреймворк уже вставил принадлежность); вызов вне контекста принадлежности вызовет `ValueError` и предупреждение о необходимости явного указания имени модуля.

### HTTP декораторы

```python
from ErisPulse import router, HttpRequest

# Также можно явно указать абстрактный тип
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

> **Правила автоматической инъекции**: Когда первый параметр обработчика называется `request` или `req`, и не имеет аннотации типа FastAPI, фреймворк автоматически вставляет `HttpRequest`. Обработчики без параметров или с другими именами параметров не затрагиваются.

#### Соглашение о возвращаемых значениях (2.10+)

Возвращаемые значения обработчиков поддерживают **кортежное соглашение** (рекомендуемый способ, явно контролирует статус-код), также допустимы dict/str/Response:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "недействительный токен"}, 401
    # (body, status_code, headers) также можно добавить заголовки ответа
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Или использовать вспомогательную функцию respond() (сообщение автоматически объединяется в тело ответа)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Параметры пути / запроса можно использовать с помощью оригинальных аннотаций FastAPI (`item_id: int`, `page: int = 1`), промежуточное ПО см. в разделе [Маршрутизация промежуточного ПО](#маршрутизация-промежуточного-ПО).

### WebSocket декораторы

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

> **Важно**: Обработчики WebSocket и обработчики аутентификации также поддерживают автоматическую инъекцию. Нет необходимости в аннотации параметра, чтобы получить `WebSocketConnection`. Указание `fastapi.WebSocket` также можно передать оригинальный объект, но рекомендуется использовать абстрактный тип.

### Автоматическая регистрация соединений (пул соединений, 2.10+)

Соединения, созданные с помощью `@ws` / `@sse`, **по умолчанию автоматически регистрируются** в пул фреймворка (`track=False` отключает это): в обработчике доступны `ws.id` / `ws.join_group(...)`, любые модули могут использовать `connections.list(namespace=...)` для просмотра соединений модуля и трансляции в группы. Подробнее см. [Пул соединений и трансляция](connections.md).

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
    summary="Данные интерфейс",
    tags=["API"],
)
```

### WebSocket регистрация

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

**Параметры:**

| Параметр | Описание | Значение по умолчанию |
|----------|----------|-----------------------|
| `module_name` | Имя модуля (обязательно) | - |
| `path` | Путь WebSocket | - |
| `handler` | Обработчик | - |
| `auth_handler` | Функция аутентификации, возвращает `False` автоматически закроет соединение | `None` |
| `auto_accept` | Автоматически ли вызывать `accept()` | `True` |

> **Рекомендуется**: Использовать `auth_handler` для подтверждения соединения, а не отключать `auto_accept`. Установите `auto_accept=False` только в том случае, если вам нужно полностью контролировать процесс соединения.

## Хуки жизненного цикла WebSocket

`WebSocketConnection` предоставляет обратные вызовы для отключения и ошибок, без необходимости вручную использовать try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Регистрация декоратором
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Причина отключения: {reason}")

    # Также можно вызвать напрямую
    async def on_err(ws, error=""):
        print(f"Ошибка: {error}")
    ws.on_error(on_err)

    # Обычная бизнес-логика
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## Группировка маршрутов

```python
# Создание маршрута с префиксом
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# Фактический путь: /my_module/v1/users
```

## Промежуточное ПО маршрутизации

Промежуточное ПО поддерживает шаблоны сопоставления путей:

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

Начиная с 2.7.0, каждый HTTP запрос будет содержать ассоциативный идентификатор `X-Request-ID`, используемый для логирования / трассировки цепочек:

- **Правила генерации**: Приоритетно используется `X-Request-ID` из заголовка запроса клиента (для распределённой трассировки); в противном случае генерируется UUID
- **Заголовок ответа**: Ответ содержит обратно `X-Request-ID`, что помогает клиенту сопоставить запрос с логами
- **События жизненного цикла**: В данных событий `server.request` и `server.response` добавлено поле `request_id`

```python
# В модуле прослушивайте события запроса, по request_id связывайте запрос-ответ
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

Автоматически добавляются безопасные заголовки `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` и др.

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
    description="API文档",
    version="1.0.0"
)
```

## Обработка путей

Пути маршрутов автоматически добавляют имя модуля в качестве префикса, чтобы избежать конфликтов:

```python
# Регистрация пути "/api" в модуль "my_module"
# Фактический путь доступа: "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> Пути маршрутов (включая префикс имени модуля) **чувствительны к регистру**. Имя модуля в регистре, как при регистрации, так и при доступе: при регистрации модуля "Test" и пути "/api" фактический путь будет "/Test/api", а доступ по "/test/api" вернёт 404.

## Системные маршруты

Маршрутизатор автоматически предоставляет следующие системные маршруты:

### Проверка работоспособности

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

На корневом маршруте `/` отображается страница бренда ErisPulse, автоматически проверяется доступность Dashboard и добавляются кнопки входа.

## Главная кнопка

Маршрутизатор позволяет внешним модулям регистрировать кнопки быстрого доступа на корневом маршруте `/`, что облегчает пользователям быстрый доступ к страницам управления модулями.

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

# Регистрация с поддержкой международизации (формат словаря i18n проекта)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "Моя панель"},
    url="/mymodule/admin",
)
```

**Параметры:**

| Параметр | Тип | Описание | Обязательно |
|----------|------|----------|------------|
| `name` | `str` / `dict` | Текст кнопки; при передаче словаря `{"i18n": "key", "default": "текст"}` используется международизация | Да |
| `url` | `str` | Адрес ссылки кнопки | Да |
| `icon_svg` | `str` | Необязательная метка иконки SVG | Нет |

### Автоматическая регистрация Dashboard

При обнаружении доступности `sdk.Dashboard`, маршрутизатор автоматически добавляет кнопку Dashboard в начало списка входов, без необходимости ручной регистрации.

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

1. **Предпочтение абстрактных типов**: Используйте `HttpRequest` / `WebSocketConnection` вместо `fastapi.Request` / `fastapi.WebSocket`, чтобы избежать жёсткой зависимости
2. **Использование автоматической инъекции**: Если первый параметр обработчика называется `request` или `req`, без аннотации типа FastAPI, получите `HttpRequest`
3. **Предпочтение одинарного параметра**: В контексте загрузки модуля предпочтительно одинарный параметр (автоматическая принадлежность пространства имён); при регистрации в других модулях/инструментальном коде явно передавайте имя модуля
4. **Использование группировки маршрутов**: Для нескольких маршрутов одного модуля используйте `group()` для организации
5. **Рассмотрение безопасности**: Реализуйте механизмы аутентификации и безопасные заголовки для чувствительных операций
6. **Разумное ограничение скорости**: Установите ограничение скорости для часто вызываемых интерфейсов
7. **Использование хуков жизненного цикла**: Через `@ws.on_disconnect` / `@ws.on_error` обрабатывайте ошибки WebSocket, избегайте ручного try/catch

## Связанные документы

- [Сетевой клиент](client.md) - Использование встроенного клиента для отправки запросов
- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) - Ознакомьтесь с регистрацией маршрутов модуля
- [Лучшие практики](../developer-guide/modules/best-practices.md) - Советы по использованию маршрутов