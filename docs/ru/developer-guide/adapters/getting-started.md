# Начало разработки адаптера

В этом руководстве вы узнаете, как приступить к разработке адаптера для ErisPulse для подключения новых платформ для обмена сообщениями.

## Обзор адаптеров

### Что такое адаптер

Адаптер — это мост между ErisPulse и различными платформами обмена сообщениями, отвечающий за:

1. **Прямое преобразование** (incoming): прием событий платформы и преобразование их в стандартный формат OneBot12 (Converter)
2. **Обратное преобразование** (outgoing): преобразование стандартных сообщений OneBot12 в вызовы API платформы (`Raw_ob12`)
3. Управление подключением к платформе (WebSocket/WebHook)
4. Предоставление универсального интерфейса отправки сообщений SendDSL

### Архитектура адаптера

```
Прямое преобразование (прием)              Обратное преобразование (отправка)
─────────────                        ─────────────
Событие платформы                       Построенное сообщение модуля
    ↓                                    ↓
Converter.convert()               Send.Raw_ob12()
    ↓                                    ↓
Стандартное событие OneBot12           Вызов нативного API платформы
    ↓                                    ↓
Система событий                         Стандартный формат ответа
    ↓
Обработка модулем

## Структура каталогов

Стандартная структура пакета адаптера:

```
MyAdapter/
├── pyproject.toml          # Конфигурация проекта
├── README.md               # Описание проекта
├── LICENSE                 # Лицензия
└── MyAdapter/
    ├── __init__.py          # Точка входа в пакет
    ├── Core.py               # Главный класс адаптера
    └── Converter.py          # Преобразователь событий

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
description = "Платформенный адаптер MyAdapter"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "ErisPulse>=2.4.0"  # ErisPulse уже содержит aiohttp, отдельная зависимость обычно не нужна
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. Создание класса адаптера

Фреймворк предоставляет декларативное управление конфигурацией через `ConfigClass` / `AccountConfigClass`; адаптеру достаточно просто объявить класс конфигурации, и он автоматически загрузится, будет валидирован и сгенерирует шаблон конфигурации.

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig

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
    ConfigClass = MyAdapterConfig  # Объявление класса конфигурации, управление фреймворком автоматически
    
    # Перекрывать __init__ не нужно! Фреймворк автоматически обрабатывает:
    # - self.sdk / self.logger автоматически устанавливаются
    # - self.cfg считывает конфигурацию в реальном времени
    # - self.Send / self.Request автоматически инициализируются
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **О `__init__`**: В новой версии `BaseAdapter.__init__(self, sdk=None)` автоматически обрабатывает ссылки на SDK, инициализацию логирования и загрузку конфигурации. Большинству адаптеров **больше не нужно перекрывать `__init__`**. Подробнее см. [Рекомендации по __init__](#init-рекомендации).

> ⚠️ **О `super().__init__()`**: Метод `BaseAdapter.__init__()` отвечает за создание экземпляров фабрик `Send` и `Request`. Если забыть вызвать этот метод, все операции отправки сообщений и запросов вызовут `AttributeError`. Подробнее см. [Рекомендации по __init__](#init-рекомендации).

### 4. Реализация обязательных методов

```python
class MyAdapter(BaseAdapter):
    # ... код __init__ ...
    
    async def start(self):
        """Запуск адаптера (обязательно к реализации)"""
        # Регистрация WebSocket или WebHook маршрутов
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("Адаптер запущен")
    
    async def shutdown(self):
        """Завершение работы адаптера (обязательно к реализации)"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # Очистка подключений и ресурсов
        self.logger.info("Адаптер остановлен")
    
    async def call_api(self, endpoint: str, **params):
        """Вызов API платформы (обязательно к реализации)"""
        raise NotImplementedError("Необходимо реализовать call_api")
```

#### Активная отправка Meta событий

Адаптер должен активной отправлять meta-события, чтобы фреймворк отслеживал онлайн-статус бота. В одну строку это можно сделать с помощью `emit_meta()`:

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Бот онлайн
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
            # Бот офлайн
            await self.emit_meta("disconnect", bot_id)
```

> Подробные сведения о управлении состоянием бота и описании Meta-событий см. в разделе [Лучшие практики адаптера - Управление состоянием бота](best-practices.md#bot-状态管理与-meta-事件).

### 5. Реализация класса Send

Декораторы `At`/`AtAll`/`Reply` уже реализованы во встроенном базовом классе SendDSL фреймворка, адаптеру нужно реализовать только `Raw_ob12` и конкретные методы отправки.

Фреймворк предоставляет два ключевых вспомогательных метода:
- `self._apply_modifiers(message)` — автоматически объединяет декораторы At/AtAll/Reply в сегменты сообщения
- `self.send_context` — словарь контекста отправки (`target_type`, `target_id`, `account_id`)

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... остальной код ...

    class Send(BaseAdapter.Send):

        def Raw_ob12(self, message, **kwargs):
            """
            Отправка сообщений в формате OneBot12 (обязательно к реализации)

            Использует _apply_modifiers для автоматического объединения состояния декораторов,
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

        # Text/Image/Voice/Video/File унаследованы от базового класса SendDSL,
        # по умолчанию делегируется Raw_ob12, повторная реализация не требуется.
        # Если нужно специфичное поведение платформы, можно переопределить отдельный метод:
        # def Text(self, text: str):
        #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Рекомендации по реализации методов отправки медиа (Image/Video/File):**

- Базовая реализация по умолчанию упаковывает параметр `file` в сегмент сообщения OneBot12 и передает его в `Raw_ob12`, адаптер должен обработать скачивание/отправку внутри `Raw_ob12`
- Параметр `file` должен поддерживать как двоичные данные `bytes`, так и строковые URL
- При передаче URL нужно сначала скачать файл, а затем отправить его на платформу
- Платформе обычно сначала нужно вызвать интерфейс загрузки для получения идентификатора файла, а затем — интерфейс отправки

**Магический метод `__getattr__`:**

- Реализовать регистр нечувствительный к регистру имен методов (`Text`, `text`, `TEXT` все могут вызываться)
- Для неопределенных методов следует возвращать подсказку вместо ошибки

**Метод `Raw_ob12`:**

- Преобразовать стандартный формат сообщений OneBot12 в формат платформы для отправки
- Использовать `self._apply_modifiers(message)` для автоматической обработки декораторов At/AtAll/Reply
- Использовать `**self.send_context` для передачи информации о цели отправки и аккаунте

### 6. Реализация конвертера

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование нативного события платформы в стандартный формат OneBot12"""
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

### 7. Реализация класса Request (операции запроса)

Если ваша платформа поддерживает запросы от друзей, приглашения в группы и другие запросы, требующие принятия решений ботом, можно реализовать внутренний класс `Request`:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Классы Send и остальной код ...

    class Request(RequestDSL):
        """Реализация операций запроса (другие запросы, приглашения в группу и т.д.)"""

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

Способ использования разработчиками модулей:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Через удобные методы Event
    await event.approve()
    # Или напрямую через адаптер
    await adapter.myplatform.Request("req_id").accept()
```

> Если платформа не поддерживает операции запроса, можно не реализовывать внутренний класс `Request`. Базовый класс по умолчанию возвращает `retcode=10002` (неподдерживаемая операция). Подробнее см. [Спецификация операций запроса](../../standards/request-action-spec.md).

### 8. Создание точки входа пакета

```python
# MyAdapter/__init__.py
from .Core import MyAdapter

## Примечания к `__init__`

В разработке адаптеров может потребоваться переопределение `__init__` на трёх уровнях. Ниже приведены правильные подходы для каждого уровня.

### 1. Уровень BaseAdapter (обычно не требуется переопределение)

`BaseAdapter.__init__(self, sdk=None)` отвечает за создание экземпляров фабрик `Send` / `Request` и автоматическое выполнение следующих действий:

- Приём параметра `sdk` и установка `self.sdk` и `self.logger`
- Если объявлен `ConfigClass`, можно читать глобальную конфигурацию в реальном времени через `self.cfg`
- Если объявлен `AccountConfigClass`, можно читать конфигурацию нескольких аккаунтов в реальном времени через `self.accounts`

**В большинстве случаев переопределять `__init__` не нужно**, достаточно объявить `ConfigClass`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # После объявления фреймворк автоматически управляет конфигурацией
    
    async def start(self):
        cfg = self.cfg  # Типобезопасно, чтение в реальном времени
        ...
```

Если всё же требуется собственная инициализация, достаточно вызвать `super().__init__(sdk)`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Передача sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

### 2. Внутренний класс Send (обычно не требуется переопределение)

`SendDSL.__init__` отвечает за передачу состояния для цепных вызовов (тип цели, ID цели, аккаунт и т.д.). **В большинстве случаев нужно переопределять только методы** (`Raw_ob12`, `Text` и т.д.), не обязательно переопределять `__init__`.

Если требуется (например, для инициализации состояния, уникального для платформы), **необходимо транслировать (пробросить) все параметры**:

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # Параметры: adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← Транслировать обязательно
            self._my_state = None  # Инициализация, уникальная для платформы
```

**Почему обязательно транслировать?** Каждый шаг цепного вызова создаёт новый экземпляр через `self.__class__(...)`:

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

Если сигнатура `__init__` не совпадает или не вызван `super()`, цепной вызов прервется.

### 3. Внутренний класс Request (обычно не требуется переопределение)

Аналогично для Send. Параметры: `adapter`, `request_id`, `account_id`:

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # Параметры: adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← Транслировать обязательно
            self._my_state = None  # Инициализация, уникальная для платформы
```

### Резюме

| Уровень | Когда переопределять | Что обязательно делать |
|------|------------|-----------|
| **BaseAdapter** | Когда нужна собственная логика инициализации | `super().__init__(sdk)` (передать параметр sdk) |
| **Внутренний класс Send** | Когда нужна инициализация состояния отправки | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Внутренний класс Request** | Когда нужна инициализация состояния запроса | `super().__init__(adapter, request_id, account_id)` |
| Все уровни | В большинстве случаев | **Достаточно объявить ConfigClass, не трогать `__init__`** |

### 9. Информация о соединении и обнаружение маршрутов

После регистрации маршрутов адаптером, фреймворк записывает всю информацию о маршрутах. Пользователи могут просмотреть адреса соединения адаптера через следующий API:

```python
from ErisPulse import sdk

# Получить полную информацию о соединении адаптера
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

# Вывести список всех пространств имен (адаптер/модуль)
namespaces = sdk.router.list_namespaces()
# {"myplatform": {"http": ["/myplatform/webhook"], "websocket": ["/myplatform/ws"]}}

# Получить полные URL соединения для пространства имен
urls = sdk.router.get_module_urls("myplatform")
# {"base_url": "http://localhost:8080", "http": [...], "websocket": [...]}

# Получить детальную информацию о маршрутах пространства имен
routes = sdk.router.get_module_routes("myplatform")
# {"http": [{"path": "/myplatform/webhook", "methods": ["POST"]}],
#  "websocket": [{"path": "/myplatform/ws", "auth": false}]}
```

> **Подсказка**: Информация, возвращаемая `get_connection_info()`, подходит для отображения пользователю (например, в WebUI), помогая пользователю настроить адрес обратного вызова или адрес подключения WebSocket со стороны платформы. `module_name`, указанный при регистрации маршрута, должен в точности совпадать с именем `platform`, зарегистрированным адаптером в ErisPulse, иначе обнаружение маршрутов не сможет корректно связать их.

### 10. Поддержка SSE (Server-Sent Events)

ErisPulse имеет встроенную платформонезависимую поддержку SSE; модули и адаптеры могут регистрировать конечные точки SSE через `@sdk.router.sse()`.

#### Базовое использование

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

Обработчик может объявить параметр `request` для доступа к информации о клиентском запросе:

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
| `sse.send(data, event=None, id=None, retry=None)` | Отправка события SSE. Данные, не являющиеся строкой, автоматически сериализуются в JSON |
| `sse.close()` | Успешное закрытие соединения SSE (безопасно для вызова, можно несколько раз) |
| `sse.closed` | Закрыто ли соединение |
| `sse.request` | Объект нижележащего запроса (можно использовать для чтения query params, заголовков) |

#### Использование в RouteGroup

```python
api = sdk.router.group("MyModule", "/api", version="1")

@api.sse("/events")
async def events(sse):
    await sse.send({"msg": "hello"})
```

#### Обнаружение маршрутов

Маршруты SSE автоматически появятся в API обнаружения маршрутов:

```python
# list_namespaces будет включать ключ "sse"
sdk.router.list_namespaces()
# {"MyModule": {"http": [...], "websocket": [...], "sse": ["/MyModule/events"]}}

# get_module_routes отметит streaming: true
sdk.router.get_module_routes("MyModule")
# {"http": [...], "websocket": [...], "sse": [{"path": "/MyModule/events", "streaming": true}]}

# get_module_urls сгенерирует полный URL
sdk.router.get_module_urls("MyModule")
# {"sse": [{"path": "/MyModule/events", "url": "http://localhost:8080/MyModule/events"}]}
```

> **Дизайн, не зависящий от сервера**: `SseEmitter` реализует связь через обратные вызовы, что обеспечивает развязку с базовым HTTP-фреймворком. Фреймворк предоставляет `register_sse()` и декоратор `@sse` как единые точки входа для регистрации; адаптеру не требуется прямая зависимость от каких-либо базовых HTTP-фреймворков для реализации конечной точки SSE.

## Далее

- [Основы адаптера](core-concepts.md) — узнайте об архитектуре адаптера
- [Подробное описание SendDSL](send-dsl.md) — изучите отправку сообщений
- [Реализация конвертера](converter.md) — ознакомьтесь с преобразованием событий
- [Рекомендации по разработке адаптеров](best-practices.md) — создавайте высококачественные адаптеры

Пожалуйста, верните полный Markdown-контент после перевода без добавления каких-либо дополнительных слов.