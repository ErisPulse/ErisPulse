# Введение в разработку адаптеров

Это руководство поможет вам начать разработку адаптеров ErisPulse для подключения к новым платформам сообщений.

## Общее описание адаптера

### Что такое адаптер

Адаптер — это мост между ErisPulse и различными платформами сообщений, отвечающий за:

1. **Прямое преобразование**: получение событий платформы и преобразование их в стандартный формат OneBot12 (Converter)
2. **Обратное преобразование**: преобразование сегментов сообщений OneBot12 в вызовы API платформы (`Raw_ob12`)
3. Управление подключением к платформе (WebSocket/WebHook)
4. Предоставление унифицированного интерфейса отправки сообщений SendDSL

### Архитектура адаптера

```
Прямое преобразование (прием)                        Обратное преобразование (отправка)
─────────────                        ─────────────
События платформы                               Формирование сообщения модулем
    ↓                                    ↓
Converter.convert()               Send.Raw_ob12()
    ↓                                    ↓
События в стандарте OneBot12                   Вызовы API платформы
    ↓                                    ↓
Система событий                             Стандартный формат ответа
    ↓
Обработка модулями
```

## Структура каталогов

Стандартная структура пакета адаптера:

```
MyAdapter/
├── pyproject.toml          # Конфигурация проекта
├── README.md               # Описание проекта
├── LICENSE                 # Лицензия
└── MyAdapter/
    ├── __init__.py          # Входная точка пакета
    ├── Core.py               # Основной класс адаптера
    └── Converter.py          # Конвертер событий
```

## Быстрый старт

### 1. Создание проекта

```bash
mkdir MyAdapter && cd MyAdapter
```

### 2. Создание pyproject.toml

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "Адаптер для MyAdapter"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "ErisPulse>=2.4.0"  # ErisPulse уже включает aiohttp, обычно не требуется отдельная зависимость
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. Создание основного класса адаптера

Рамка предоставляет декларативное управление конфигурацией с помощью `ConfigClass` / `AccountConfigClass`, адаптеру нужно только объявить класс конфигурации, чтобы автоматически загружать, проверять и генерировать шаблон конфигурации.

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import BaseConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """Конфигурация MyAdapter"""
    api_endpoint: str = field(
        default="https://api.example.com",
        metadata={
            "description": {"i18n": "my_adapter.api_endpoint", "default": "Адрес API"},
            "required": False,
            "ui": {"widget": "text", "group": "connection", "order": 1},
        },
    )
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Токен платформы"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 2},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # Объявление класса конфигурации, рамка автоматически управляет
    
    # Не нужно переопределять __init__! Рамка автоматически обрабатывает:
    # - self.sdk / self.logger автоматически устанавливаются
    # - self.cfg в реальном времени читает конфигурацию
    # - self.Send / self.Request автоматически инициализируются
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **О __init__**: В новой версии `BaseAdapter.__init__(self, sdk=None)` автоматически обрабатывает ссылку на SDK, инициализацию логгера и загрузку конфигурации. Большинству адаптеров **не нужно переопределять `__init__`**. Подробнее см. [Примечания к __init__](#init-注意事项).

> ⚠️ **О super().__init__()**: `BaseAdapter.__init__()` отвечает за создание фабрик `Send` и `Request`. Если забыть вызвать, все операции отправки сообщений и запросов будут вызывать `AttributeError`. Подробнее см. [Примечания к __init__](#init-注意事项).

### 4. Реализация обязательных методов

```python
class MyAdapter(BaseAdapter):
    # ... код __init__ ...
    
    async def start(self):
        """Запуск адаптера (обязательно реализовать)"""
        # Регистрация маршрутов WebSocket или WebHook
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("Адаптер запущен")
    
    async def shutdown(self):
        """Остановка адаптера (обязательно реализовать)"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # Очистка подключений и ресурсов
        self.logger.info("Адаптер остановлен")
    
    async def call_api(self, endpoint: str, **params):
        """Вызов API платформы (обязательно реализовать)"""
        raise NotImplementedError("Необходимо реализовать call_api")
```

#### Активная отправка мета-событий

Адаптер должен активно отправлять мета-события, чтобы рамка отслеживала состояние онлайн бота. Это можно сделать одной строкой с помощью `emit_meta()`:

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Бот подключился
        await self.emit_meta("connect", bot_id, user_name="MyBot")

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Бот отключился
            await self.emit_meta("disconnect", bot_id)
```

> Подробное описание управления состоянием бота и мета-событий см. в [Рекомендациях по разработке адаптеров - Управление состоянием бота](best-practices.md#bot-状态管理与-meta-事件).

### 5. Реализация класса Send

Модификаторы `At`/`AtAll`/`Reply` уже реализованы в базовом классе SendDSL рамки, адаптеру нужно только реализовать `Raw_ob12` и конкретные методы отправки.

Рамка предоставляет два ключевых вспомогательных метода:
- `self._apply_modifiers(message)` — автоматически объединяет модификаторы At/AtAll/Reply в сегменты сообщения
- `self.send_context` — получает словарь контекста отправки (`target_type`, `target_id`, `account_id`)

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... другие код ...
    
    class Send(BaseAdapter.Send):
        
        def Raw_ob12(self, message, **kwargs):
            """
            Отправка сообщения в формате OneBot12 (обязательно реализовать)

            Использует _apply_modifiers для автоматического объединения состояния модификаторов,
            использует send_context для получения контекста отправки.
            """
            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs
                )
            return asyncio.create_task(_do_send())
        
        def Text(self, text: str):
            """Отправка текстового сообщения"""
            return self.Raw_ob12([
                {"type": "text", "data": {"text": text}}
            ])
        
        def Image(self, file):
            """Отправка изображения"""
            return self.Raw_ob12([
                {"type": "image", "data": {"file": file}}
            ])
```

**Особенности реализации методов отправки медиа-контента (Image/Video/File):**

- Параметр `file` должен поддерживать как `bytes` (бинарные данные), так и `str` (URL)
- При передаче URL нужно сначала загрузить файл, а затем загрузить его на платформу
- Платформа обычно требует сначала вызвать интерфейс загрузки для получения идентификатора файла, а затем вызвать интерфейс отправки

**Метод `__getattr__` магический метод:**

- Реализация методов должна быть нечувствительна к регистру (Text, text, TEXT могут вызываться)
- Неопределенные методы должны возвращать сообщение-подсказку, а не генерировать ошибку

**Метод `Raw_ob12`:**

- Преобразует стандартный формат сообщений OneBot12 в формат платформы для отправки
- Использует `self._apply_modifiers(message)` для автоматической обработки модификаторов At/AtAll/Reply
- Использует `**self.send_context` для передачи информации о цели отправки и учетной записи

### 6. Реализация конвертера

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование событий платформы в стандартный формат OneBot12"""
        if not isinstance(raw_event, dict):
            return None
        
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_event_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
    
    def _convert_event_type(self, event_type):
        """Преобразование типа события"""
        type_map = {
            "message": "message",
            "notice": "notice"
        }
        return type_map.get(event_type, "unknown")
    
    def _convert_detail_type(self, raw_event):
        """Преобразование детального типа"""
        return "private"  # Упрощенный пример
```

### 7. Реализация класса Request (операции запросов)

Если ваша платформа поддерживает запросы от друзей, приглашения в группы и т.д., требующие решения бота, можно реализовать внутренний класс `Request`:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... код Send и другие коды ...

    class Request(RequestDSL):
        """Реализация операций запросов (запросы от друзей, приглашения в группы и т.д.)"""

        def accept(self, **kwargs):
            """Принять запрос"""
            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=True,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            return self._create_task(_do())

        def reject(self, **kwargs):
            """Отклонить запрос"""
            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=False,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            return self._create_task(_do())
```

Способ использования модулем-разработчиком:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Через удобный метод Event
    await event.approve()
    # Или через прямую операцию адаптера
    await adapter.myplatform.Request("req_id").accept()
```

> Если платформа не поддерживает операции запросов, можно не реализовывать внутренний класс `Request`. Базовый класс по умолчанию возвращает `retcode=10002` (операция не поддерживается). Подробнее см. [Спецификация операций запросов](../../standards/request-action-spec.md).

### 8. Создание входной точки пакета

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## Примечания к `__init__`

В разработке адаптеров есть три уровня, где может потребоваться переопределение `__init__`. Ниже приведены правильные подходы для каждого уровня.

### 1. Уровень BaseAdapter (в большинстве случаев не нужно переопределять)

`BaseAdapter.__init__(self, sdk=None)` отвечает за создание фабрик `Send` / `Request` и автоматически выполняет следующие действия:

- Принимает параметр `sdk` и устанавливает `self.sdk`, `self.logger`
- Если объявлен `ConfigClass`, можно в реальном времени читать глобальную конфигурацию через `self.cfg`
- Если объявлен `AccountConfigClass`, можно в реальном времени читать конфигурацию нескольких учетных записей через `self.accounts`

**В большинстве случаев не нужно переопределять `__init__`**, достаточно просто объявить `ConfigClass`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # После объявления рамка автоматически управляет конфигурацией
    
    async def start(self):
        cfg = self.cfg  # Типобезопасное чтение в реальном времени
        ...
```

Если действительно нужно настроить инициализацию, вызовите `super().__init__(sdk)`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Передача sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

### 2. Внутренний класс Send (в большинстве случаев не нужно переопределять)

`SendDSL.__init__` отвечает за передачу состояния цепочечных вызовов (тип цели, ID цели, учетная запись). **В большинстве случаев вам нужно переопределять только методы** (`Raw_ob12`, `Text` и т.д.), а не `__init__`.

Если действительно нужно (например, для инициализации платформы-специфичного состояния), **обязательно передавайте все параметры**:

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # Параметры: adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← Обязательно передавать
            self._my_state = None  # Инициализация платформы-специфичного состояния
```

**Почему обязательно передавать?** Каждый шаг цепочечного вызова создает новый экземпляр через `self.__class__(...)`:

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

Если подпись `__init__` не совпадает или не вызывается `super()`, цепочечный вызов прервется.

### 3. Внутренний класс Request (в большинстве случаев не нужно переопределять)

Как и Send. Параметры: `adapter`, `request_id`, `account_id`:

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # Параметры: adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← Обязательно передавать
            self._my_state = None  # Инициализация платформы-специфичного состояния
```

### Подведение итогов

| Уровень | Когда переопределять | Обязательные действия |
|------|------------|-----------|
| **BaseAdapter** | Когда нужно собственную логику инициализации | `super().__init__(sdk)` (передача параметра sdk) |
| **Send внутренний класс** | Когда нужно инициализировать состояние, связанное с отправкой | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request внутренний класс** | Когда нужно инициализировать состояние, связанное с запросами | `super().__init__(adapter, request_id, account_id)` |
| Все три уровня | В большинстве случаев | **Объявление ConfigClass, без изменения `__init__`** |

### 9. Информация о подключении и обнаружение маршрутов

После регистрации маршрутов адаптером, рамка будет записывать всю информацию о маршрутах. Пользователи могут использовать следующий API для просмотра информации о подключении адаптера:

```python
from ErisPulse import sdk

# Получение полной информации о подключении адаптера
info = sdk.adapter.get_connection_info("myplatform")
# {
#   "platform": "myplatform",
#   "status": "started",
#   "connection": {
#     "base_url": "http://localhost:8080",
#     "http_routes": [
#       {"path": "/myplatform/webhook", "method": "POST",
#        "url": "http://localhost:8080/myplatform/webhook"}
#     ],
#     "websocket_routes": [
#       {"path": "/myplatform/ws",
#        "url": "ws://localhost:8080/myplatform/ws"}
#     ]
#   }
# }

# Перечисление маршрутов всех пространств имен (адаптеров/модулей)
namespaces = sdk.router.list_namespaces()
# {"myplatform": {"http": ["/myplatform/webhook"], "websocket": ["/myplatform/ws"]}}

# Получение полных URL подключения для пространства имен
urls = sdk.router.get_module_urls("myplatform")
# {"base_url": "http://localhost:8080", "http": [...], "websocket": [...]}

# Получение подробной информации о маршрутах пространства имен
routes = sdk.router.get_module_routes("myplatform")
# {"http": [{"path": "/myplatform/webhook", "methods": ["POST"]}],
#  "websocket": [{"path": "/myplatform/ws", "auth": false}]}
```

> **Подсказка**: Информация, возвращаемая `get_connection_info()`, подходит для отображения пользователю (например, в WebUI), помогая настроить адрес обратного вызова или адрес подключения WebSocket на стороне платформы. При регистрации маршрута `module_name` должен полностью совпадать с именем `platform`, зарегистрированным в ErisPulse, иначе обнаружение маршрута не будет корректно сопоставлено.

### 10. Поддержка SSE (Server-Sent Events)

ErisPulse имеет встроенную поддержку SSE, независимую от сервера, модули и адаптеры могут зарегистрировать конечные точки SSE с помощью `@sdk.router.sse()`.

#### Основное использование

```python
import asyncio
from ErisPulse import sdk

@sdk.router.sse("MyModule", "/events")
async def event_stream(sse):
    """Отправка событий SSE"""
    count = 0
    while not sse.closed:
        await sse.send({"count": count}, event="update")
        count += 1
        await asyncio.sleep(1)
```

#### Использование параметров запроса

Обработчик может объявить параметр `request`, чтобы получить информацию о клиентском запросе:

```python
@sdk.router.sse("MyModule", "/events")
async def event_stream(request, sse):
    token = request.query_params.get("token")
    if not validate_token(token):
        await sse.close()
        return

    while not sse.closed:
        data = await fetch_data(token)
        await sse.send(data)
        await asyncio.sleep(5)
```

#### API SseEmitter

| Метод | Описание |
|------|------|
| `sse.send(data, event=None, id=None, retry=None)` | Отправка события SSE. Не строковые данные автоматически сериализуются в JSON |
| `sse.close()` | Аккуратное закрытие соединения SSE (безопасный вызов, может быть многократным) |
| `sse.closed` | Закрыто ли соединение |
| `sse.request` | Объект базового запроса (可用于读取 query params、headers) |

#### Использование в RouteGroup

```python
api = sdk.router.group("MyModule", "/api", version="1")

@api.sse("/events")
async def events(sse):
    await sse.send({"msg": "hello"})
```

#### Обнаружение маршрутов

Маршруты SSE автоматически появляются в API обнаружения маршрутов:

```python
# list_namespaces будет содержать ключ "sse"
sdk.router.list_namespaces()
# {"MyModule": {"http": [...], "websocket": [...], "sse": ["/MyModule/events"]}}

# get_module_routes будет помечать streaming: true
sdk.router.get_module_routes("MyModule")
# {"http": [...], "websocket": [...], "sse": [{"path": "/MyModule/events", "streaming": true}]}

# get_module_urls будет генерировать полный URL
sdk.router.get_module_urls("MyModule")
# {"sse": [{"path": "/MyModule/events", "url": "http://localhost:8080/MyModule/events"}]}
```

> **Дизайн, независимый от сервера**: `SseEmitter` использует обратные вызовы для декомпозиции от базовой HTTP-рамки. Рамка предоставляет `register_sse()` и декоратор `@sse` в качестве единого входа для регистрации, адаптеру не нужно напрямую зависеть от какой-либо базовой HTTP-рамки для реализации конечной точки SSE.

## Далее

- [Основные концепции адаптера](core-concepts.md) - Ознакомьтесь с архитектурой адаптера
- [Подробное руководство по SendDSL](send-dsl.md) - Изучите отправку сообщений
- [Реализация конвертера](converter.md) - Ознакомьтесь с преобразованием событий
- [Рекомендации по разработке адаптеров](best-practices.md) - Разработка качественных адаптеров