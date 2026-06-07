# HTTP-клиент

ErisPulse предоставляет унифицированный HTTP/WS-клиент. Модулям и адаптерам следует отдавать приоритет использованию этого клиента для отправки HTTP-запросов и установления WebSocket-соединений вместо самостоятельного импорта сторонних библиотек, таких как `aiohttp` / `httpx`.

## Обзор

Основные функции HTTP/WS-клиента:

- **Единый интерфейс**: предоставляет методы `get` / `post` / `put` / `delete` / `patch` / `request`
- **WebSocket-клиент**: установление клиентского WebSocket-соединения через `ws_connect`
- **Автоматическое ведение логов**: все запросы автоматически логируются и собирается статистика
- **Интеграция жизненного цикла**: каждый запрос вызывает событие жизненного цикла `client.request`, WS-соединение вызывает событие `client.ws.connect`
- **Поддержка повторных попыток**: настраиваемое количество автоматических повторных попыток и интервалов
- **Управление таймаутами**: отдельные таймауты для соединения и запроса
- **Переиспользование пула соединений**: управление пулом соединений на основе `aiohttp.ClientSession`
- **Иерархия исключений**: исключения `aiohttp` автоматически конвертируются в исключения `ErisPulse` (иерархия `ClientError`)

## Быстрый старт

### HTTP-запросы

```python
from ErisPulse.Core import client

# GET-запрос
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST-запрос
resp = await client.post(
    "https://httpbin.org/post",
    json={"ключ": "значение"},
)
data = await resp.json()
```

### WebSocket-соединение

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Эхо: {text}")
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
    json={"имя": "Alice", "возраст": 30},
)

# Тело формы
resp = await client.post(
    "https://api.example.com/login",
    data={"имя пользователя": "admin", "пароль": "123"},
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

resp = await client.put("https://api.example.com/users/1", json={"имя": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"возраст": 31})
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

### Параметры HTTP-запроса

| Параметр | Тип | Описание |
|------|------|------|
| `url` | `str` | URL запроса |
| `params` | `dict[str, str]` | Параметры запроса (необязательно) |
| `headers` | `dict[str, str]` | Дополнительные заголовки (необязательно) |
| `data` | `Any` | Тело запроса (форма или сырые данные) (необязательно) |
| `json` | `Any` | JSON-тело запроса (необязательно) |
| `timeout` | `float` | Таймаут этого запроса (секунды) (необязательно, переопределяет значение по умолчанию) |
| `max_retries` | `int` | Максимальное количество повторных попыток для этого запроса (необязательно, переопределяет значение по умолчанию) |

### Параметры ws_connect

| Параметр | Тип | Описание |
|------|------|------|
| `url` | `str` | URL WebSocket-сервера |
| `headers` | `dict[str, str]` | Дополнительные заголовки (необязательно) |
| `heartbeat` | `float` | Интервал пульсации (секунды) (необязательно) |

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

### События HTTP-запросов

Событие `client.request` срабатывает после завершения каждого запроса, оно может использоваться для мониторинга:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### События WebSocket-соединения

Событие `client.ws.connect` срабатывает после установления каждого WebSocket-соединения:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS соединение: {event_data['url']}")
```

## Управление контекстом

```python
# Использование в качестве контекстного менеджера для автоматического закрытия сессии
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket-клиент

Установка клиентского WebSocket-соединения через `client.ws_connect()`, возвращает объект `ClientWebSocket`. Клиент и сервер WebSocket совместно используют один и тот же базовый класс `WebSocketConnectionBase`, интерфейсы send/receive/iter идентичны.

### Базовое использование

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Привет")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"тип": "ping"})
```

### Получение сообщений

#### Высокоуровневые методы (рекомендуются)

Автоматическая фильтрация типов сообщений, при разрыве соединения выбрасывается `WebSocketDisconnect`:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# Прием по одной строке
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# Итеративный прием (автоматически останавливается при разрыве соединения)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### Низкоуровневые методы

Использование `receive()` и `iter_messages()` для обработки необработанных типов сообщений, позволяет различать TEXT / BINARY / CLOSE / ERROR:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# Прием необработанного сообщения по одной строке
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# Итеративный прием необработанных сообщений (автоматически останавливается при CLOSE/ERROR)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"Текст: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"Двоичные данные: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` — это унифицированный тип WebSocket-сообщения, не зависящий от базовой библиотеки:

| Свойство | Тип | Описание |
|------|------|------|
| `type` | `str` | Тип сообщения: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | Данные сообщения |

### Свойства ClientWebSocket

| Свойство | Тип | Описание |
|------|------|------|
| `url` | `URL` | URL соединения |
| `headers` | `Headers` | Заголовки ответа |
| `closed` | `bool` | Закрыто ли соединение |
| `raw` | `object` | Базовый нативный объект (aiohttp.ClientWebSocketResponse) |

### Жизненные цикл-хуки

Аналогично `WebSocketConnection` на сервере, поддерживает `on_disconnect` и `on_error` колбэки:

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"Соединение разорвано: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"Ошибка соединения: {error}")
```

### Закрытие соединения

```python
await ws.close(code=1000, reason="Normal closure")
```

## Иерархия исключений

ErisPulse определяет унифицированную иерархию исключений. Запросы, инициированные через `sdk.client`, автоматически конвертируют базовые исключения `aiohttp` в исключения `ErisPulse`.

> **Обратная совместимость**: старые модули/адаптеры, использующие `aiohttp.ClientSession` напрямую, не затронуты. Конвертация исключений работает только при использовании `sdk.client` для запросов; код, использующий `aiohttp` напрямую, по-прежнему будет перехватывать нативные исключения, такие как `aiohttp.ClientError`. Оба способа могут сосуществовать.

### Иерархия исключений

```
ErisPulseError
├── ClientError                  # Базовый класс для всех исключений HTTP/WS-клиента
│   ├── ClientConnectionError    # Ошибка соединения (сбой DNS, отказ в соединении, недоступность сети)
│   ├── ClientTimeoutError       # Таймаут соединения или запроса
│   └── HTTPStatusError          # Ошибка состояния HTTP 4xx/5xx
└── WebSocketError               # Базовый класс для исключений WebSocket
    └── WebSocketDisconnect      # Разрыв WebSocket-соединения (универсальный для клиента и сервера)
```

### Перехват исключений

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import (
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)

# Обработка исключений HTTP-запросов
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("Не удалось подключиться к серверу")
except ClientTimeoutError:
    print("Таймаут запроса")
except ClientError as e:
    print(f"Ошибка запроса: {e}")

# Обработка исключений WebSocket
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Эхо: {text}")
except WebSocketDisconnect as e:
    print(f"Соединение разорвано: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"Ошибка WebSocket: {e}")
```

### Универсальный перехват

Использование `ClientError` для перехвата всех исключений HTTP/WS-клиента:

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"Клиентская ошибка: {e}")
```

### HTTPStatusError

Когда необходимо проверить код состояния после запроса и выбросить исключение, можно использовать вручную:

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## Использование в адаптерах

Адаптеры могут использовать глобальный клиент или создавать собственные экземпляры клиента для отправки запросов на API платформы:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.errors import ClientError

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        try:
            resp = await client.post(
                f"https://api.platform.com/{endpoint}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return await resp.json()
        except ClientError as e:
            self.logger.error(f"Ошибка вызова API: {e}")
            raise
```

> Также можно использовать `sdk.client` через `from ErisPulse import sdk`, эффект будет аналогичным.

## Лучшие практики

1. **Приоритет использования глобального клиента**: используйте `from ErisPulse.Core import client` для получения глобального экземпляра, это упрощает унифицированное управление и мониторинг со стороны фреймворка
2. **Избегайте прямого импорта aiohttp**: используйте `client` вместо `aiohttp.ClientSession`, чтобы в будущем не нужно было менять код при смене базовой реализации
3. **Использование иерархии исключений ErisPulse**: при использовании `sdk.client` перехватывайте `ClientError`, а не `aiohttp.ClientError`, чтобы код не зависел от конкретной HTTP-библиотеки. Старый код, использующий `aiohttp` напрямую, не затронут
4. **Рациональная настройка таймаутов**: установите разумные таймауты в зависимости от скорости ответа API, чтобы избежать длительной блокировки
5. **Использование механизма повторных попыток**: включите повторные попытки для нестабильных API для повышения надежности
6. **Мониторинг статистики запросов**: отслеживайте состояние запросов через `sdk.client.stats` или событие жизненного цикла `client.request`
7. **Использование высокоуровневых методов WebSocket**: отдавайте предпочтение методам `iter_text` / `iter_json` и используйте `iter_messages` только в случае необходимости различать типы сообщений

## Связанные документы

- [Маршрутизатор](router.md) - серверные маршруты HTTP/WebSocket (WebSocketConnection на стороне сервера использует тот же базовый класс, что и на стороне клиента)
- [Руководство по разработке адаптеров](../developer-guide/adapters/getting-started.md) - использование HTTP-клиента в адаптерах
- [Управление жизненным циклом](lifecycle.md) - прослушивание событий запроса