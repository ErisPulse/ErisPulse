# HTTP клиент

ErisPulse предоставляет единый HTTP-клиент, модули и адаптеры должны использовать этот клиент для отправки HTTP-запросов, вместо самостоятельного импорта сторонних библиотек, таких как `aiohttp` / `httpx`.

## Обзор

Основные функции HTTP-клиента:

- **Единый интерфейс**: предоставляет методы `get` / `post` / `put` / `delete` / `patch` / `request`
- **Автоматическое ведение логов**: все запросы автоматически логируются и собирается статистика
- **Интеграция жизненного цикла**: каждые запросы вызывают событие жизненного цикла `client.request`
- **Поддержка повторных попыток**: настраиваемое количество автоматических повторных попыток и интервалов
- **Управление таймаутами**: отдельные таймауты для соединения и запроса
- **Переиспользование пула соединений**: управление пулом соединений на основе `aiohttp.ClientSession`

## Быстрый старт

```python
from ErisPulse.Core import client

# GET-запрос
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST-запрос
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

## HttpResponse

Все методы запросов возвращают объект `HttpResponse`:

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP-код состояния (например, 200, 404)
resp.reason       # str | None - описание состояния (например, "OK")
resp.headers      # заголовки ответа (регистронезависимые)
resp.content_type # str | None - Content-Type
resp.url          # финальный URL (может измениться из-за перенаправления)
resp.raw          # базовый нативный объект ответа (в данный момент aiohttp.ClientResponse)

# Чтение тела ответа
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # парсинг JSON
text = await resp.text("gbk")  # указанная кодировка
```

## Методы запроса

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# JSON-тело запроса
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# Тело формы
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# Сырые данные
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### Общий метод request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## Описание параметров

### Параметры запроса

| Параметр | Тип | Описание |
|------|------|------|
| `url` | `str` | URL запроса |
| `params` | `dict[str, str]` | Параметры запроса (необязательно) |
| `headers` | `dict[str, str]` | Дополнительные заголовки (необязательно) |
| `data` | `Any` | Тело запроса (форма или сырые данные) (необязательно) |
| `json` | `Any` | JSON-тело запроса (необязательно) |
| `timeout` | `float` | Таймаут этого запроса (секунды) (необязательно, переопределяет значение по умолчанию) |
| `max_retries` | `int` | Максимальное количество повторных попыток для этого запроса (необязательно, переопределяет значение по умолчанию) |

## Таймауты и повторные попытки

```python
from ErisPulse.Core import HttpClient

# Создание клиента с пользовательским таймаутом
client = HttpClient(
    timeout=60,           # общий таймаут запроса 60s
    connect_timeout=5,    # таймаут соединения 5s
    max_retries=3,        # автоматические повторные попытки при неудаче 3 раза
    retry_delay=2,        # задержка между повторными попытками 2s
)

# Переопределение таймаута для одного запроса
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

## Пользовательские заголовки по умолчанию

```python
client = HttpClient(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## Статистика запросов

```python
from ErisPulse.Core import client

# Просмотр статистики
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# Сброс статистики
client.reset_stats()
```

## События жизненного цикла

Событие `client.request` срабатывает после завершения каждого запроса, оно может использоваться для мониторинга:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

## Управление контекстом

```python
# Использование в качестве контекстного менеджера для автоматического закрытия сессии
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## Использование в адаптерах

Адаптеры могут использовать глобальный клиент или создавать собственные экземпляры клиента для отправки запросов к API платформы:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        return await resp.json()
```

> Вы также можете использовать `sdk.client`, импортировав `from ErisPulse import sdk`; эффект будет аналогичным.

## Лучшие практики

1. **Приоритет использования глобального клиента**: используйте `from ErisPulse.Core import client` для получения глобального экземпляра, это упрощает унифицированное управление и мониторинг со стороны фреймворка
2. **Избегайте прямого импорта aiohttp**: используйте `client` вместо `aiohttp.ClientSession`, чтобы в будущем не нужно было менять код при смене базовой реализации
3. **Рациональная настройка таймаутов**: установите разумные таймауты в зависимости от скорости ответа API, чтобы избежать длительной блокировки
4. **Использование механизма повторных попыток**: включите повторные попытки для нестабильных API для повышения надежности
5. **Мониторинг статистики запросов**: отслеживайте состояние запросов через `sdk.client.stats` или событие жизненного цикла `client.request`

## Связанные документы

- [Маршрутизатор](router.md) - серверные маршруты HTTP/WebSocket
- [Руководство по разработке адаптеров](../developer-guide/adapters/getting-started.md) - использование HTTP-клиента в адаптерах
- [Управление жизненным циклом](lifecycle.md) - прослушивание событий запроса