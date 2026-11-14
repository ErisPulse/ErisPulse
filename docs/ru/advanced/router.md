# Менеджер маршрутов

> [!TIP]
> **Когда стоит читать этот документ**: когда требуются маршруты HTTP / WebSocket / SSE (включая широковещательные рассылки через пул соединений). Если нет — можно пропустить, это не влияет на использование остальных функций.

Менеджер маршрутов ErisPulse предоставляет унифицированное управление маршрутами HTTP и WebSocket, поддерживает регистрацию маршрутов нескольких адаптеров и управление жизненным циклом. В основе лежит уровень абстракции (в настоящее время FastAPI + Uvicorn)

## Обзор

Основные функции менеджера маршрутов:

- **Декораторы маршрутов**: поддержка быстрой регистрации с помощью декораторов `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws`
- **Автоматическое внедрение**: обработчикам маршрутов не требуется импортировать типы FastAPI, фреймворк автоматически внедряет абстрактные объекты
- **Группировка маршрутов**: поддержка `RouteGroup` с префиксом и версией
- **Промежуточные обработчики маршрутов**: поддержка перехвата запросов с сопоставлением по glob-паттернам
- **Ограничение скорости**: встроенное ограничение по алгоритму скользящего окна
- **Поддержка CORS**: включение кросс-доменного обмена ресурсами одним вызовом
- **Заголовки безопасности**: автоматическое добавление заголовков безопасности в ответы
- **Автоматическая документация**: интерактивная документация на основе OpenAPI
- **Поддержка WebSocket**: полное управление соединениями WebSocket, настраиваемая аутентификация и хуки жизненного цикла
- **Интеграция с жизненным циклом**: глубокая интеграция с системой жизненного цикла ErisPulse
- **Поддержка SSL/TLS**: поддержка защищённых соединений HTTPS и WSS
- **Главная страница**: поддержка регистрации модулями кнопок быстрого доступа на корневом маршруте `/`, с поддержкой интернационализации

## Абстрактные типы

ErisPulse предоставляет абстрактные типы серверной части, позволяя модулям не зависеть напрямую от FastAPI:

| Абстрактный тип | Аналог в FastAPI | Описание |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | Обёртка HTTP-запроса, полностью совместимый интерфейс |
| `WebSocketConnection` | `fastapi.WebSocket` | Обёртка соединения WebSocket, дополнительно предоставляет хуки жизненного цикла |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | Исключение разрыва соединения WebSocket |

> `WebSocketConnection` наследуется от `WebSocketConnectionBase` и разделяет те же интерфейсы send/receive/iter/close с клиентским WebSocket (`ClientWebSocket`). Клиентский и серверный WebSocket могут использовать один и тот же код бизнес-логики.
>
> Через свойство `.raw` можно получить доступ к нативному объекту FastAPI. Код, напрямую использующий типы FastAPI, также полностью совместим.

## Декораторы маршрутов (рекомендуется)

### Формы регистрации: с одним аргументом (рекомендуется) и с двумя

Декораторы маршрутов поддерживают две формы, **рекомендуется форма с одним аргументом** — она согласуется с командами / триггерами событий, пространство имён автоматически привязывается к текущему модулю:

```python
from ErisPulse import router

# С одним аргументом (рекомендуется): автоматическая привязка имя_модуля/hello → фактический путь /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# WebSocket с одним аргументом: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# С двумя аргументами: явное указание имени модуля (правила не меняются, используется при регистрации из кода других модулей/утилит)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> Форма с одним аргументом требует регистрации в **контексте загрузки** модуля/адаптера (при загрузке фреймворк уже внедряет привязку);
> вызов вне контекста с привязкой вызывает `ValueError` с подсказкой явно передать имя модуля.

### HTTP-декораторы

```python
from ErisPulse import router, HttpRequest

# Также можно явно указывать абстрактный тип
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

> **Правило автоматического внедрения**: когда имя первого параметра обработчика — `request` или `req` и нет аннотации типа FastAPI, фреймворк автоматически внедряет `HttpRequest`. Обработчики без параметров или с иным именем параметра запроса не затрагиваются.

#### Соглашение о возвращаемых значениях (2.10+)

Возвращаемые значения обработчика поддерживают **соглашение с кортежем** (рекомендуемый способ, явное управление кодом состояния), dict/str/Response работают как прежде:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → JSON 401
        return {"error": "unauthorized", "message": "недействительный токен"}, 401
    # (body, status_code, headers) может также содержать заголовки ответа
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Или использовать вспомогательную функцию respond() (message автоматически объединяется в тело ответа)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Параметры пути / запроса можно задавать напрямую нативными аннотациями FastAPI (`item_id: int`, `page: int = 1`),
о промежуточных обработчиках см. раздел [Промежуточные обработчики маршрутов](#промежуточные-обработчики-маршрутов).

### WebSocket-декораторы

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# Базовый WebSocket (форма с одним аргументом)
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

# WebSocket с аутентификацией (токен читается из переменной окружения, не хардкодьте его в коде)
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

> **Примечание**: обработчики WebSocket и обработчики аутентификации также поддерживают автоматическое внедрение. `WebSocketConnection` можно получить без аннотаций параметров. При аннотации `fastapi.WebSocket` также передаётся нативный объект, но рекомендуется использовать абстрактный тип.

### Автоматическая регистрация соединений (пул соединений, 2.10+)

Соединения, установленные через `@ws` / `@sse`, **по умолчанию автоматически регистрируются** в пуле соединений фреймворка (можно отключить с помощью `track=False`):
внутри handler доступны `ws.id` / `ws.join_group(...)`, любой модуль может
просматривать соединения своего модуля через `connections.list(namespace=...)` и рассылать сообщения группам.
Подробнее см. [Пул соединений и широковещательные рассылки](connections.md).

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

# С ограничением скорости и информацией для документации
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
| `auth_handler` | Функция аутентификации, возврат `False` автоматически закрывает соединение | `None` |
| `auto_accept` | Выполнять ли автоматический `accept()` | `True` |

> **Рекомендация**: используйте `auth_handler` для подтверждения соединения вместо отключения `auto_accept`. Устанавливайте `auto_accept=False` только если вам нужен полный контроль над процессом соединения.

## Хуки жизненного цикла WebSocket

`WebSocketConnection` предоставляет регистрацию колбэков отключения и ошибок, не требующую ручного try/catch:

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

    # Обычная бизнес-логика
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

## Промежуточные обработчики маршрутов

Промежуточные обработчики поддерживают сопоставление путей по glob-паттернам:

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

## Идентификатор корреляции запросов (X-Request-ID)

Начиная с 2.7.0, каждый HTTP-запрос содержит идентификатор корреляции `X-Request-ID`, используемый для связывания логов / трассировки:

- **Правило генерации**: сначала используется заголовок запроса `X-Request-ID`, переданный клиентом (сценарий распределённой трассировки); иначе UUID генерируется автоматически
- **Заголовок ответа**: в ответ записывается `X-Request-ID`, что позволяет клиенту сопоставлять запросы с логами
- **События жизненного цикла**: в данные событий `server.request` и `server.response` добавлено поле `request_id`

```python
# Прослушивание событий запросов в модуле, связывание запрос-ответ по request_id
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

Клиент может задать свой ID для трассировки между сервисами:

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## Ограничение скорости

Ограничение скорости маршрутов с использованием алгоритма скользящего окна:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Формат ограничения скорости: `{количество}/{временное_окно}`, например `10/minute`, `100/hour`.

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

## Заголовки безопасности

```python
router.setup_security_headers()
```

Автоматически добавляются заголовки безопасности, такие как `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`.

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

# Настройка информации о документации
router.set_docs_info(
    title="My API",
    description="Документация API",
    version="1.0.0"
)
```

## Обработка путей

К путям маршрутов автоматически добавляется имя модуля в качестве префикса во избежание конфликтов:

```python
# Регистрация пути "/api" для модуля "my_module"
# Фактический путь доступа: "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> Путь маршрута (включая префикс имени модуля) **чувствителен к регистру**. Регистр фактического пути совпадает с регистром имени модуля при регистрации: если имя модуля `Test`, фактический путь для зарегистрированного `/api` будет `/Test/api`, а обращение к `/test/api` вернёт 404.

## Системные маршруты

Менеджер маршрутов автоматически предоставляет следующие системные маршруты:

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

Корневой маршрут `/` отображает страницу бренда ErisPulse, автоматически определяет доступность Dashboard и добавляет кнопку входа.

## Главная страница

Менеджер маршрутов позволяет внешним модулям регистрировать кнопки быстрого доступа на корневом маршруте `/`, что упрощает пользователям быстрый доступ к страницам управления модулей.

### Регистрация точки входа

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

# Регистрация с поддержкой интернационализации (формат i18n-словаря проекта)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "Моя панель"},
    url="/mymodule/admin",
)
```

**Описание параметров:**

| Параметр | Тип | Описание | Обязательный |
|------|------|------|------|
| `name` | `str` / `dict` | Отображаемый текст кнопки; при передаче словаря `{"i18n": "key", "default": "текст"}` используется интернационализация | Да |
| `url` | `str` | Адрес ссылки кнопки | Да |
| `icon_svg` | `str` | Необязательная SVG-иконка | Нет |

### Автоматическая регистрация Dashboard

Когда обнаруживается доступный `sdk.Dashboard`, менеджер маршрутов автоматически добавляет кнопку Dashboard в начало списка точек входа, ручная регистрация не требуется.

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

## Расширенные свойства объекта запроса

Помимо базовых свойств `method` / `query` / `headers` / `json` / `body`,
`HttpRequest` также предоставляет расширенные возможности (часто используются в middleware аутентификации и длительных задачах с отслеживанием отключений):

| Свойство / метод | Описание |
|-------------|------|
| `request.session` | Словарь сессии (требуется поддержка middleware сессий), сохраняется между запросами |
| `request.auth` | Информация аутентификации (записывается middleware аутентификации) |
| `request.user` | Объект текущего пользователя (записывается middleware аутентификации) |
| `request.url_for(name, **params)` | Обратная маршрутизация: генерация URL по имени маршрута |
| `await request.is_disconnected()` | Отключился ли клиент (для выхода из SSE / длительных задач с опросом) |
| `request.raw` | Нативный объект запроса Starlette («аварийный люк», см. описание совместимости в следующем разделе) |

## Аварийный люк: router.app

`router.app` напрямую предоставляет экземпляр приложения FastAPI (создаётся лениво, при первом обращении загружается
web-стек и регистрируются основные маршруты), покрывая сценарии, недостижимые через декораторы — монтирование подприложений, глобальные middleware,
интеграция с экосистемой FastAPI (StaticFiles / шаблоны фоновых задач и т.д.):

```python
from ErisPulse.Core import router
from starlette.staticfiles import StaticFiles

app = router.app
app.mount("/static", StaticFiles(directory="static"), name="static")
```

> [!WARNING]
> **Границы совместимости**: `router.app` — это аварийный люк, а не стабильный контракт — вы получаете экземпляр текущего
> web-стека (FastAPI/Starlette). Если фреймворк в будущем сменит базовую web-реализацию, код, зависящий
> от внутренней структуры `app` (порядок middleware, специфичные для Starlette API), столкнётся с **критическими
> изменениями**. Приоритетно используйте слой абстракции `@router.http` / `HttpRequest` (аналогично
> `request.raw`) и локализуйте использование `.app` в отдельном адаптерном слое модуля — при миграции потребуется изменить только одну точку.

## Лучшие практики

1. **Приоритетное использование абстрактных типов**: используйте `HttpRequest` / `WebSocketConnection` вместо `fastapi.Request` / `fastapi.WebSocket`, чтобы избежать жёсткой зависимости
2. **Использование автоматического внедрения**: назовите первый параметр обработчика `request` или `req`, и вы получите `HttpRequest` без каких-либо аннотаций типов
3. **Приоритет формы с одним аргументом**: в контексте загрузки модуля предпочтительна форма с одним аргументом (автоматическая привязка пространства имён); при регистрации из кода других модулей/утилит явно передавайте имя модуля
4. **Использование группировки маршрутов**: организуйте несколько маршрутов одного модуля с помощью `group()`
5. **Соображения безопасности**: реализуйте механизмы аутентификации и заголовки безопасности для чувствительных операций
6. **Разумное ограничение скорости**: устанавливайте ограничения скорости для часто вызываемых интерфейсов
7. **Использование хуков жизненного цикла**: обрабатывайте исключения WebSocket через `@ws.on_disconnect` / `@ws.on_error`, избегая ручного try/catch
8. **Ограниченное использование аварийного люка**: `router.app` / `request.raw` используйте только когда слой абстракции не может выразить нужное, и локализуйте зависимости в одной точке, сокращая объём адаптации при миграции базовой реализации фреймворка

## Связанная документация

- [Сетевой клиент](client.md) - отправка запросов с помощью встроенного клиента
- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) - знакомство с регистрацией маршрутов модулей
- [Лучшие практики](../developer-guide/modules/best-practices.md) - рекомендации по использованию маршрутов