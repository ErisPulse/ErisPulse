# Маршрутизатор

Маршрутизатор ErisPulse обеспечивает единое управление HTTP и WebSocket маршрутизацией, поддерживает регистрацию маршрутов с несколькими адаптерами и управление их жизненным циклом. В основе лежит абстрактный слой (в настоящее время FastAPI + Uvicorn).

## Обзор

Основные функции маршрутизатора:

- **Декоратор маршрутов**: поддержка быстрой регистрации маршрутов с помощью декораторов `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws`
- **Автоматическая инъекция**: обработчики маршрутов не требуют импорта типов FastAPI, фреймворк автоматически инжектирует абстрактные объекты
- **Группировка маршрутов**: поддержка `RouteGroup` с префиксом и номером версии
- **Маршрутизатор промежуточного ПО**: поддержка глобального режима сопоставления для перехвата запросов
- **Ограничение скорости**: встроенный скользящий оконный режим ограничения
- **Поддержка CORS**: включение кросс-доменного资源共享 одним кликом
- **Безопасные заголовки**: автоматическое добавление безопасных заголовков ответа
- **Автоматическая документация**: интерактивная документация на основе OpenAPI
- **Поддержка WebSocket**: полное управление подключениями WebSocket, пользовательская аутентификация и жизненный цикл
- **Интеграция жизненного цикла**: глубокая интеграция с системой жизненного цикла ErisPulse
- **Поддержка SSL/TLS**: поддержка безопасных соединений HTTPS и WSS
- **Главная точка входа**: поддержка модуля с быстрой регистрацией кнопки входа по корневому маршруту `/`, поддержка локализации

## Абстрактные типы

ErisPulse предоставляет абстрактные типы сервера, которые позволяют модулям не зависеть напрямую от FastAPI:

| Абстрактный тип | Соответствие FastAPI | Описание |
|----------------|----------------------|----------|
| `HttpRequest` | `fastapi.Request` | Обёртка над HTTP-запросом, полная совместимость интерфейса |
| `WebSocketConnection` | `fastapi.WebSocket` | Обёртка над WebSocket-соединением, дополнительные хуки жизненного цикла |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | Исключение при разрыве WebSocket-соединения |

> `WebSocketConnection` наследуется от `WebSocketConnectionBase` и разделяет с клиентским WebSocket (`ClientWebSocket`) одинаковые интерфейсы send/receive/iter/close. Бизнес-логика может быть одинаковой как для клиента, так и для сервера.
>
> С помощью свойства `.raw` можно получить доступ к базовому объекту FastAPI. Код, использующий типы FastAPI, также полностью совместим.

## Декораторы маршрутов (рекомендуется)

### HTTP декораторы

```python
from ErisPulse.Core import router
@router.get("my_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}

# Также можно явно указать абстрактный тип
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

> **Правила автоматической инъекции**: если первый параметр обработчика имеет имя `request` или `req` и не имеет аннотации типа FastAPI, фреймворк автоматически инжектирует `HttpRequest`. Обработчики без параметров или с параметрами, не являющимися именем запроса, не затрагиваются.

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

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **Примечание**: WebSocket обработчики и обработчики аутентификации также поддерживают автоматическую инъекцию. `WebSocketConnection` можно получить без аннотации параметра. Использование аннотации `fastapi.WebSocket` также передаст оригинальный объект, но рекомендуется использовать абстрактный тип.

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

# С ограничением частоты и документацией
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
|----------|----------|-----------------------|
| `module_name` | Имя модуля (обязательно) | - |
| `path` | Путь WebSocket | - |
| `handler` | Обработчик | - |
| `auth_handler` | Функция аутентификации, возвращает `False` для автоматического закрытия соединения | `None` |
| `auto_accept` | Автоматически вызывать `accept()` | `True` |

> **Рекомендуется** использовать `auth_handler` для подтверждения соединения, а не отключать `auto_accept`. Установите `auto_accept=False` только в том случае, если вам нужно полностью контролировать процесс подключения.

## WebSocket 生命周期钩子

`WebSocketConnection` позволяет зарегистрировать обратные вызовы при отключении и ошибках, без необходимости использовать try/catch вручную:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Регистрация через декоратор
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Причина отключения: {reason}")

    # Также можно вызвать напрямую
    async def on_err(ws, error=""):
        print(f"Ошибка: {error}")
    ws.on_error(on_err)

    # Основная бизнес-логика
    async for msg in ws.iter_text():
        await ws.send_text(f"Эхо: {msg}")
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

## Маршрутизация промежуточного программного обеспечения

Промежуточное программное обеспечение поддерживает сопоставление с помощью шаблонов glob:

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

Начиная с версии 2.7.0, каждый HTTP-запрос содержит идентификатор `X-Request-ID`, используемый для логирования и трассировки цепочек:

- **Правила генерации**: приоритетно используется заголовок `X-Request-ID`, переданный клиентом (для распределённой трассировки); в противном случае генерируется UUID
- **Заголовок ответа**: ответ также содержит `X-Request-ID`, что позволяет клиенту сопоставить запрос с логами
- **События жизненного цикла**: в данных событий `server.request` и `server.response` добавлено поле `request_id`

```python
# В модуле отслеживайте события запроса, используя request_id для сопоставления запроса и ответа
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

Ограничение скорости маршрутов осуществляется с использованием алгоритма скользящего окна:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Формат ограничения скорости: `{количество}/{временной интервал}`, например `10/minute`, `100/hour`.

## CORS Configuration

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

CORS can also be configured via `config.toml`:

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

Автоматически добавляются заголовки безопасности, такие как `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` и другие.

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
    title="Мой API",
    description="Документация API",
    version="1.0.0"
)
```

## Обработка путей

Пути маршрутизации автоматически добавляют имя модуля в качестве префикса, чтобы избежать конфликтов:

```python
# Регистрация пути "/api" для модуля "my_module"
# Фактический доступный путь: "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## Системные маршруты

Менеджер маршрутизации автоматически предоставляет следующие системные маршруты:

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

Корневой маршрут `/` отображает страницу бренда ErisPulse, автоматически определяет доступность Dashboard и добавляет кнопку входа.

## Главная точка входа

Менеджер маршрутизации позволяет внешним модулям регистрировать кнопки быстрого доступа на корневом маршруте `/`, что упрощает пользователям быстрый переход на страницы управления соответствующих модулей.

### Регистрация входа

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

**Описание параметров:**

| Параметр | Тип | Описание | Обязателен |
|----------|------|----------|-----------|
| `name` | `str` / `dict` | Текст отображения кнопки; при передаче словаря `{"i18n": "key", "default": "текст"}` используется международизация | Да |
| `url` | `str` | Адрес ссылки кнопки | Да |
| `icon_svg` | `str` | Необязательный SVG-код иконки | Нет |

### Автоматическая регистрация Dashboard

При обнаружении доступности `sdk.Dashboard`, менеджер маршрутизации автоматически добавляет кнопку Dashboard в начало списка входов, без необходимости ручной регистрации.

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

1. **Предпочтение абстрактным типам**: Используйте `HttpRequest` / `WebSocketConnection` вместо `fastapi.Request` / `fastapi.WebSocket`, чтобы избежать жесткой привязки
2. **Использование автоматической инъекции**: Первый параметр обработчика должен называться `request` или `req`, чтобы получить `HttpRequest` без каких-либо аннотаций типов
3. **Явное передача module_name**: Первый аргумент декоратора должен быть именем модуля, его нельзя опускать
4. **Использование группировки маршрутов**: Для нескольких маршрутов одного модуля используйте `group()` для организации
5. **Рассмотрение безопасности**: Реализуйте механизмы аутентификации и безопасные заголовки для чувствительных операций
6. **Разумное ограничение скорости**: Установите ограничение скорости для интерфейсов с высокой частотой вызовов
7. **Использование циклов жизненного цикла**: Используйте `@ws.on_disconnect` / `@ws.on_error` для обработки исключений WebSocket, избегая ручного try/catch

## Связанные документы

- [HTTP-клиент](http-client.md) - Использование встроенного HTTP-клиента для отправки запросов
- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) - Ознакомьтесь с регистрацией маршрутов модуля
- [Рекомендуемые практики](../developer-guide/modules/best-practices.md) - Советы по использованию маршрутов