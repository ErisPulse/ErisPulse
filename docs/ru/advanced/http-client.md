# Сетевой клиент

ErisPulse предоставляет единый сетевой клиент, объединяющий HTTP-запросы, WebSocket-соединения и управление пулы соединений. Модули и адаптеры **должны использовать** этот клиент в первую очередь, а не импортировать сторонние библиотеки, такие как `aiohttp` / `httpx` / `requests`.

docs/ru/quick-start.md

## Обзор

Основные функции сетевого клиента:

- **Единый интерфейс**: предоставляет методы `get` / `post` / `put` / `delete` / `patch` / `request`
- **WebSocket-клиент**: установка WebSocket-соединения клиента через `ws_connect`
- **Автоматическая регистрация в журнале**: все запросы автоматически записываются в журнал и собираются статистические данные
- **Интеграция жизненного цикла**: каждый запрос вызывает событие жизненного цикла `client.request`, подключение WebSocket вызывает событие `client.ws.connect`
- **Поддержка повторных попыток**: можно настроить количество и интервал автоматических повторных попыток
- **Управление тайм-аутами**: отдельные настройки тайм-аута подключения и тайм-аута запроса
- **Возможность повторного использования пула соединений**: управление пулом соединений на основе aiohttp.ClientSession
- **Система исключений**: исключения aiohttp автоматически преобразуются в исключения ErisPulse (система ClientError)

[**Переключить язык**](docs/ru/quick-start.md)

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
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket-соединение

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Эхо: {text}")

## HttpResponse

Все методы запроса возвращают объект `HttpResponse`:

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP статус (например, 200, 404)
resp.reason       # str | None - описание статуса (например, "OK")
resp.headers      # заголовки ответа (без учета регистра)
resp.content_type # str | None - Content-Type
resp.url          # финальный URL (может измениться из-за редиректа)
resp.raw          # базовый объект ответа (в настоящее время aiohttp.ClientResponse)

# Чтение тела ответа
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # разбор JSON
text = await resp.text("gbk")  # указание кодировки
```

[**English**](docs/ru/quick-start.md) | [**Русский**](docs/ru/quick-start.md)

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

# Загрузка файлов (используя параметр files, без импорта aiohttp)
# Формат: {имя_поля: объект_файла/bytes/(имя_файла, файл)/(имя_файла, файл, тип_содержимого)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "Аватарка"},            # Необязательно: также передать обычные поля формы
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# Упрощённый синтаксис: передача объекта файла напрямую
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# Прямая загрузка данных из памяти (без сохранения на диск)
import io

resp = await client.post(
    "https://api.example.com/upload",
    files={"file": ("data.txt", io.BytesIO(b"file content"), "text/plain")},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### Общий request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)

## Параметры

### Параметры HTTP-запроса

| Параметр | Тип | Описание |
|------|------|------|
| `url` | `str` | URL-адрес запроса |
| `params` | `dict[str, str]` | Параметры запроса (необязательно) |
| `headers` | `dict[str, str]` | Дополнительные заголовки запроса (необязательно) |
| `data` | `Any` | Тело запроса (форма или сырые данные) (необязательно) |
| `json` | `Any` | Тело запроса в формате JSON (необязательно) |
| `files` | `dict[str, Any]` | Поля для загрузки файлов (необязательно, автоматически формируется multipart/form-data) |
| `timeout` | `float` | Таймаут запроса (секунды) (необязательно, переопределяет значение по умолчанию) |
| `max_retries` | `int` | Максимальное количество повторных попыток для этого запроса (необязательно, переопределяет значение по умолчанию) |

### Параметры ws_connect

| Параметр | Тип | Описание |
|------|------|------|
| `url` | `str` | URL-адрес сервера WebSocket |
| `headers` | `dict[str, str]` | Дополнительные заголовки запроса (необязательно) |
| `heartbeat` | `float` | Интервал между心跳 сообщениями (секунды) (необязательно) |

## Тайм-ауты и повторные попытки

```python
from ErisPulse.Core import Client

# Создание клиента с пользовательскими тайм-аутами
client = Client(
    timeout=60,           # Общий тайм-аут запроса 60 секунд
    connect_timeout=5,    # Тайм-аут подключения 5 секунд
    max_retries=3,        # Автоматические повторные попытки при сбое 3 раза
    retry_delay=2,        # Интервал между повторными попытками 2 секунды
)

# Переопределение тайм-аута для одного запроса
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> Класс клиента с версии 2.8.0 переименован в `Client` (имя свойства `sdk.client` остается неизменным); старое имя `HttpClient` сохранено как совместимое псевдоним, старый код не требует изменений.

[**English**](docs/ru/quick-start.md) | [**简体中文**](docs/ru/quick-start.md) | [**日本語**](README.ja.md) | [**한국어**](README.ko.md)

## Пользовательские заголовки по умолчанию

```python
client = Client(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

[**Перейти к следующему разделу**](docs/ru/quick-start.md)

## Запросы статистики

```python
from ErisPulse.Core import client

# Просмотр статистики
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# Сброс статистики
client.reset_stats()
```

[**English**](docs/ru/quick-start.md)

## Жизненный цикл событий

### События HTTP-запросов

Событие `client.request` срабатывает после завершения каждого запроса и может использоваться для мониторинга:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### События WebSocket-соединений

Событие `client.ws.connect` срабатывает каждый раз после установления WebSocket-соединения:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS-соединение: {event_data['url']}")

## Управление контекстом

```python
# В качестве менеджера контекста, автоматически закрывает сессию
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

См. также: [**Справочник API**](docs/ru/api-reference.md)

## WebSocket клиент

Создайте подключение WebSocket-клиента с помощью `client.ws_connect()`, который возвращает объект `ClientWebSocket`. Клиент и сервер WebSocket используют один и тот же базовый класс `WebSocketConnectionBase`, а интерфейсы send/receive/iter полностью совпадают.

### Основное использование

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Привет")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### Получение сообщений

#### Высокоуровневые методы (рекомендуется)

Автоматически фильтрует типы сообщений и выбрасывает `WebSocketDisconnect` при разрыве соединения:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# Получение одного сообщения
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# Итерация по сообщениям (автоматически останавливается при разрыве)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### Низкоуровневые методы

Используйте `receive()` и `iter_messages()` для обработки необработанных типов сообщений, чтобы различать TEXT / BINARY / CLOSE / ERROR:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# Получение одного необработанного сообщения
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# Итерация по необработанным сообщениям (автоматически останавливается при CLOSE/ERROR)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"Текст: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"Двоичные данные: {len(msg.data)} байт")
```

### WSMessage

`WSMessage` — это единый тип сообщения WebSocket, независимый от базовой библиотеки:

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
| `raw` | `object` | Низкоуровневый объект (aiohttp.ClientWebSocketResponse) |

### Жизненный цикл

Аналогично `серверному WebSocketConnection`, поддерживает обратные вызовы `on_disconnect` и `on_error`:

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
await ws.close(code=1000, reason="Нормальное закрытие")

## Система исключений

ErisPulse определяет единый иерархический уровень исключений, при этом запросы, инициированные через `sdk.client`, автоматически преобразуют исключения aiohttp в исключения ErisPulse.

> **Обратная совместимость**: Старые модули/адаптеры, использующие напрямую `aiohttp.ClientSession`, полностью не затрагиваются. Преобразование исключений применяется только при запросах, инициированных через `sdk.client`, а код, использующий напрямую aiohttp, по-прежнему будет перехватывать исключения, такие как `aiohttp.ClientError`. Оба способа могут сосуществовать.

### Иерархия исключений

```
ErisPulseError
├── ClientError                  # Базовый класс для всех исключений HTTP/WS клиентских запросов
│   ├── ClientConnectionError    # Ошибка соединения (неудачное разрешение DNS, отказ в подключении, недоступность сети)
│   ├── ClientTimeoutError       # Ошибка соединения или запроса по таймауту
│   └── HTTPStatusError          # Ошибка HTTP статуса 4xx/5xx
└── WebSocketError               # Базовый класс исключений WebSocket
    └── WebSocketDisconnect      # Отключение WebSocket (общее для клиента и сервера)
```

### Обработка исключений

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
    print("Невозможно подключиться к серверу")
except ClientTimeoutError:
    print("Запрос превысил лимит времени")
except ClientError as e:
    print(f"Запрос не удался: {e}")

# Обработка исключений WebSocket
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"Соединение разорвано: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"Ошибка WebSocket: {e}")
```

### Единое перехватывание

Используйте `ClientError` для единого перехвата всех исключений HTTP/WS клиентских запросов:

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"Клиентская ошибка: {e}")
```

### HTTPStatusError

Если необходимо проверить код состояния после запроса и выбросить исключение, можно использовать `HTTPStatusError` вручную:

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())

## Использование в адаптере

Адаптер может использовать глобальный клиент или создать экземпляр клиента для отправки запросов к API платформы:

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

> Также можно использовать `sdk.client` через `from ErisPulse import sdk`, результат будет таким же.

## Лучшие практики

1. **Предпочтение глобального клиента**: Используйте `from ErisPulse.Core import client`, чтобы получить глобальный синглтон, что упрощает единое управление и мониторинг в рамках фреймворка
2. **Избегайте прямого импорта aiohttp**: Используйте `client` вместо `aiohttp.ClientSession`, чтобы в будущем при замене реализации на более низком уровне не пришлось изменять код. Старый код, использующий напрямую aiohttp, будет продолжать работать нормально, и оба способа могут сосуществовать
3. **Используйте систему исключений ErisPulse**: При запросах через `sdk.client` перехватывайте `ClientError`, а не `aiohttp.ClientError`, чтобы код не зависел от конкретной библиотеки HTTP. Старый код, использующий напрямую aiohttp, не будет затронут
4. **Разумно задавайте тайм-ауты**: Устанавливайте разумные значения тайм-аутов в зависимости от скорости ответа API, чтобы избежать длительных блокировок
5. **Используйте механизм повторных попыток**: Включайте повторные попытки для нестабильных API, чтобы повысить надежность
6. **Мониторинг статистики запросов**: Мониторинг состояния запросов можно осуществлять через `sdk.client.stats` или события жизненного цикла `client.request`
7. **Использование WebSocket с помощью продвинутых методов**: Предпочтение отдается продвинутым методам, таким как `iter_text` / `iter_json`, и используйте `iter_messages` только в случае необходимости различения типов сообщений

## Руководство по быстрому старту

Перед началом работы с ErisPulse SDK необходимо установить пакет:

```bash
pip install erispulse-sdk
```

### Инициализация глобального клиента

Для начала работы с ErisPulse SDK необходимо инициализировать глобальный клиент. Это можно сделать с помощью следующего кода:

```python
from ErisPulse.Core import client

# Инициализация глобального клиента
client.init(
    api_key="your_api_key_here",  # Замените на ваш API ключ
    base_url="https://api.erispulse.com",  # Опционально: базовый URL API
    timeout=30,  # Опционально: тайм-аут запроса в секундах
)
```

### Пример использования

После инициализации глобального клиента вы можете использовать его для выполнения запросов к API ErisPulse. Ниже приведен пример простого GET-запроса:

```python
import asyncio

async def main():
    try:
        # Выполнение GET-запроса
        response = await client.get("/some-endpoint")
        
        # Обработка ответа
        if response.status == 200:
            data = await response.json()
            print("Данные получены успешно:", data)
        else:
            print(f"Ошибка: {response.status}")
            
    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Запуск асинхронной функции
asyncio.run(main())
```

### Дополнительные методы

Кроме GET-запросов, глобальный клиент поддерживает также POST, PUT, DELETE и другие HTTP-методы:

```python
# POST-запрос
await client.post("/some-endpoint", json={"key": "value"})

# PUT-запрос
await client.put("/some-endpoint", json={"key": "value"})

# DELETE-запрос
await client.delete("/some-endpoint")
```

### Обработка ошибок

ErisPulse SDK предоставляет собственную систему исключений, которая позволяет обрабатывать ошибки HTTP-запросов:

```python
from ErisPulse.Core import ClientError

try:
    response = await client.get("/some-endpoint")
except ClientError as e:
    print(f"Ошибка клиента: {e}")
except Exception as e:
    print(f"Неизвестная ошибка: {e}")
```

### WebSocket

Для работы с WebSocket можно использовать метод `client.ws_connect`:

```python
async def main():
    async with client.ws_connect("/ws-endpoint") as ws:
        # Отправка сообщения
        await ws.send_json({"type": "ping"})
        
        # Получение сообщения
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                print("Получено сообщение:", msg.data)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break

asyncio.run(main())
```

### Мониторинг

Для мониторинга статистики запросов можно использовать `client.stats`:

```python
# Получение статистики
stats = client.stats()
print("Общее количество запросов:", stats.total_requests)
print("Количество успешных запросов:", stats.successful_requests)
print("Количество ошибок:", stats.errors)
```

### Завершение работы

После завершения работы с ErisPulse SDK рекомендуется закрыть глобальный клиент:

```python
await client.close()
```

## API Reference

### `client.get`

Выполняет GET-запрос к указанному URL.

**Параметры:**
- `url` (str): URL-адрес, к которому нужно отправить запрос.
- `params` (Optional[Dict[str, Any]]): Параметры запроса.
- `headers` (Optional[Dict[str, str]]): Заголовки запроса.
- `timeout` (Optional[int]): Тайм-аут запроса в секундах.

**Возвращает:**
- `aiohttp.ClientResponse`: Объект ответа.

**Пример:**
```python
response = await client.get("/users")
```

### `client.post`

Выполняет POST-запрос к указанному URL.

**Параметры:**
- `url` (str): URL-адрес, к которому нужно отправить запрос.
- `data` (Optional[Dict[str, Any]]): Данные для отправки.
- `json` (Optional[Dict[str, Any]]): JSON-данные для отправки.
- `headers` (Optional[Dict[str, str]]): Заголовки запроса.
- `timeout` (Optional[int]): Тайм-аут запроса в секундах.

**Возвращает:**
- `aiohttp.ClientResponse`: Объект ответа.

**Пример:**
```python
response = await client.post("/users", json={"name": "John"})
```

### `client.put`

Выполняет PUT-запрос к указанному URL.

**Параметры:**
- `url` (str): URL-адрес, к которому нужно отправить запрос.
- `data` (Optional[Dict[str, Any]]): Данные для отправки.
- `json` (Optional[Dict[str, Any]]): JSON-данные для отправки.
- `headers` (Optional[Dict[str, str]]): Заголовки запроса.
- `timeout` (Optional[int]): Тайм-аут запроса в секундах.

**Возвращает:**
- `aiohttp.ClientResponse`: Объект ответа.

**Пример:**
```python
response = await client.put("/users/1", json={"name": "Jane"})
```

### `client.delete`

Выполняет DELETE-запрос к указанному URL.

**Параметры:**
- `url` (str): URL-адрес, к которому нужно отправить запрос.
- `params` (Optional[Dict[str, Any]]): Параметры запроса.
- `headers` (Optional[Dict[str, str]]): Заголовки запроса.
- `timeout` (Optional[int]): Тайм-аут запроса в секундах.

**Возвращает:**
- `aiohttp.ClientResponse`: Объект ответа.

**Пример:**
```python
response = await client.delete("/users/1")
```

### `client.ws_connect`

Устанавливает WebSocket-соединение с указанным URL.

**Параметры:**
- `url` (str): URL-адрес, к которому нужно установить соединение.
- `params` (Optional[Dict[str, Any]]): Параметры запроса.
- `headers` (Optional[Dict[str, str]]): Заголовки запроса.
- `timeout` (Optional[int]): Тайм-аут запроса в секундах.

**Возвращает:**
- `aiohttp.ClientWebSocketResponse`: Объект WebSocket-соединения.

**Пример:**
```python
async with client.ws_connect("/ws-endpoint") as ws:
    await ws.send_json({"type": "ping"})
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            print("Получено сообщение:", msg.data)
```

### `client.stats`

Возвращает статистику запросов.

**Возвращает:**
- `ClientStats`: Объект со статистикой запросов.

**Пример:**
```python
stats = client.stats()
print("Общее количество запросов:", stats.total_requests)
print("Количество успешных запросов:", stats.successful_requests)
print("Количество ошибок:", stats.errors)
```

### `client.close`

Закрывает глобальный клиент.

**Пример:**
```python
await client.close()
```

## Лицензия

ErisPulse SDK распространяется под лицензией MIT. Подробнее см. в файле [LICENSE](docs/ru/LICENSE.md).

## Связанные документы

- [Менеджер маршрутизации](router.md) - HTTP/WebSocket маршрутизация сервера (серверное WebSocketConnection и клиент разделяют один и тот же базовый класс)
- [Руководство по разработке адаптеров](../developer-guide/adapters/getting-started.md) - Использование HTTP-клиента в адаптерах
- [Управление жизненным циклом](lifecycle.md) - Отслеживание событий запросов

Пожалуйста, напрямую верните переведённый полный Markdown-контент, не добавляя никаких других слов.