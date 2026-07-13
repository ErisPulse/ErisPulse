# Маршрутизатор

Маршрутизатор ErisPulse предоставляет унифицированное управление HTTP и WebSocket маршрутами, поддерживая регистрацию маршрутов и управление жизненным циклом с помощью нескольких адаптеров. В основе реализовано через абстрактный слой (на данный момент FastAPI + Uvicorn)

## Обзор

Основные функции маршрутизатора:

- **Декораторные маршруты**: поддержка декораторов быстрой регистрации `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws`
- **Автоматическая инъекция**: для обработчиков маршрутов не нужно импортировать типы FastAPI, фреймворк автоматически внедряет абстрактные объекты
- **Группировка маршрутов**: поддержка `RouteGroup` с префиксом и номером версии
- **Маршрутные middleware**: поддержка перехвата запросов по glob-шаблонам
- **Лимитирование запросов**: встроенный алгоритм скользящего окна
- **Поддержка CORS**:一键开启跨域资源共享
- **Безопасные заголовки**: автоматическое добавление безопасных заголовков ответа
- **Автодокументация**: интерактивная документация на основе OpenAPI
- **Поддержка WebSocket**: полное управление соединениями WebSocket, кастомная аутентификация и хуки жизненного цикла
- **Интеграция жизненного цикла**: глубокая интеграция с системой жизненного цикла ErisPulse
- **Поддержка SSL/TLS**: поддержка безопасных соединений HTTPS и WSS
- **Главная страница**: поддержка регистрации быстрых кнопок входа для модулей на корневом маршруте `/`, поддержка интернационализации

## Абстрактные типы

ErisPulse предоставляет абстрактные типы для серверной части, позволяя модулям не зависеть напрямую от FastAPI:

| Абстрактный тип | Соответствие FastAPI | Описание |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | Обертка HTTP запроса, интерфейс полностью совместим |
| `WebSocketConnection` | `fastapi.WebSocket` | Обертка WebSocket соединения, дополнительно предоставляет хуки жизненного цикла |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | Исключение при разрыве WebSocket |

> `WebSocketConnection` наследуется от `WebSocketConnectionBase` и имеет те же интерфейсы отправки/получения/итерации/закрытия, что и клиентский WebSocket (`ClientWebSocket`). Клиентские и серверные WebSocket могут использовать один и тот же бизнес-код.
>
> Через свойство `.raw` можно получить базовый нативный объект FastAPI. Код, использующий нативные типы FastAPI, также полностью совместим.

## Декораторные маршруты (рекомендуется)

### HTTP декораторы

```python
from ErisPulse.Core import router
@router.get("my_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}

# Явное указание абстрактных типов также возможно
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

> **Правила автоматической инъекции**: когда первый параметр обработчика называется `request` или `req` и отсутствует аннотация типа FastAPI, фреймворк автоматически внедряет `HttpRequest`. Обработчики без параметров или с параметрами, не являющимися запросами, не затрагиваются.

### WebSocket декораторы

```python
from ErisPulse.Core import WebSocketConnection, WebSocketDisconnect

# Базовый WebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Эхо: {msg}")

# WebSocket с хуками жизненного цикла
@router.ws("my_module", "/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"Пользователь отключен: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"Ошибка соединения: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Эхо: {msg}")

# WebSocket с аутентификацией
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Эхо: {data}")
```

> **Примечание**: обработчики WebSocket и аутентификации также поддерживают автоматическую инъекцию. `WebSocketConnection` доступна без аннотаций параметров. Можно передать нативный объект, указав `fastapi.WebSocket`, но рекомендуется использовать абстрактные типы.

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

# С ограничением скорости и документацией
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
        await ws.send_text(f"Эхо: {msg}")

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
| `handler` | Функция обработчика | - |
| `auth_handler` | Функция аутентификации, возврат `False` автоматически закроет соединение | `None` |
| `auto_accept` | Автоматически вызывать `accept()` | `True` |

> **Рекомендация**: используйте `auth_handler` для подтверждения соединения вместо отключения `auto_accept`. Устанавливайте `auto_accept=False` только при необходимости полного контроля потока соединений.

## Хуки жизненного цикла WebSocket

`WebSocketConnection` предоставляет регистрацию колбэков для разрыва соединения и ошибок, без необходимости вручную писать try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Регистрация через декоратор
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Причина отключения: {reason}")

    # Или вызов напрямую
    async def on_err(ws, error=""):
        print(f"Ошибка: {error}")
    ws.on_error(on_err)

    # Нормальная бизнес-логика
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

# Реальный путь: /my_module/v1/users
```

## Middleware маршрутов

Middleware поддерживают glob-шаблоны для сопоставления путей:

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

## Ограничение скорости

Лимитирование запросов для маршрутов с использованием алгоритма скользящего окна:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Формат ограничения скорости: `{количество}/{временное окно}`, например `10/minute` или `100/hour`.

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

## Безопасные заголовки

```python
router.setup_security_headers()
```

Автоматически добавляются такие безопасные заголовки, как `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` и другие.

Также можно настроить через `config.toml`:

```toml
[router.security]
enabled = true
```

## Автодокументация

Router по умолчанию включает интерактивную документацию OpenAPI:

```python
# Отключить документацию
router.disable_docs()

# Настроить информацию о документации
router.set_docs_info(
    title="My API",
    description="Документация API",
    version="1.0.0"
)
```

## Обработка путей

Пути маршрутов автоматически добавляют имя модуля как префикс, чтобы избежать конфликтов:

```python
# Регистрация пути "/api" в модуле "my_module"
# Реальный доступный путь: "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## Системные маршруты

Маршрутизатор автоматически предоставляет следующие системные маршруты:

### Проверка работоспособности

```
GET /health
# Возвращает:
{"status": "ok", "service": "ErisPulse Router"}
```

### Корневая страница

```
GET /
# Возвращает страницу бренда ErisPulse
```

Корневой маршрут `/` отображает страницу бренда ErisPulse, автоматически проверяет доступность Dashboard и добавляет кнопку входа.

## Главная страница (входы)

Маршрутизатор позволяет внешним модулям регистрировать кнопки быстрых входов на корневом маршруте `/`, чтобы пользователи могли быстро обращаться к административным страницам модулей.

### Регистрация входа

```python
# Простая регистрация
router.register_home_entry(
    name="Моя панель",
    url="/mymodule/admin",
)

# Регистрация с иконкой (SVG)
router.register_home_entry(
    name="Панель управления",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# Регистрация с поддержкой интернационализации (формат словаря i18n проекта)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "Моя панель"},
    url="/mymodule/admin",
)
```

**Описание параметров:**

| Параметр | Тип | Описание | Обязательный |
|------|------|------|------|
| `name` | `str` / `dict` | Текст, отображаемый на кнопке; для интернационализации используйте словарь `{"i18n": "key", "default": "текст"}` | Да |
| `url` | `str` | Адрес ссылки кнопки | Да |
| `icon_svg` | `str` | Необязательный SVG-маркер иконки | Нет |

### Автоматическая регистрация Dashboard

Когда обнаруживается доступность `sdk.Dashboard`, маршрутизатор автоматически добавляет кнопку Dashboard в начало списка входов без необходимости ручной регистрации.

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

## Лучшие практики

1. **Приоритет использования абстрактных типов**: используйте `HttpRequest` / `WebSocketConnection` вместо `fastapi.Request` / `fastapi.WebSocket`, чтобы избежать жестких зависимостей
2. **Используйте автоматическую инъекцию**: называйте первый параметр обработчика `request` или `req`, чтобы получить `HttpRequest` без каких-либо аннотаций типов
3. **Явно указывайте `module_name`**: первый параметр декоратора должен быть именем модуля, его нельзя опускать
4. **Используйте группировку маршрутов**: используйте `group()` для организации нескольких маршрутов одного модуля
5. **Учет безопасности**: реализуйте механизмы аутентификации и безопасные заголовки для чувствительных операций
6. **Рациональное ограничение скорости**: устанавливайте лимиты для частых интерфейсов
7. **Используйте хуки жизненного цикла**: обрабатывайте исключения WebSocket через `@ws.on_disconnect` / `@ws.on_error`, избегая ручного написания try/catch

## Связанные документы

- [HTTP клиент](docs/ru/http-client.md) - отправка запросов с помощью встроенного HTTP клиента
- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) - узнайте, как регистрировать маршруты модулей
- [Лучшие практики](../developer-guide/modules/best-practices.md) - рекомендации по использованию маршрутов