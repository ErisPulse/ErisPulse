# Введение в разработку адаптеров

> [!TIP]
> **Когда читать эту статью**: начальная статья для пути разработки адаптеров (обязательно к прочтению). Здесь вы узнаете, как начать писать адаптер с нуля, а также о границах ответственности адаптера и структуре проекта; после прочтения переходите по необходимости к [Трансформатору событий](converter.md) и [Подробной документации SendDSL](send-dsl.md).

Это руководство поможет вам начать разработку адаптеров ErisPulse для подключения к новым платформам сообщений.

## Описание адаптера

### Что такое адаптер

Адаптер — это мост между ErisPulse и различными платформами сообщений, который отвечает за:

1. **Прямое преобразование**: получение событий с платформы и их преобразование в стандартный формат OneBot12 (Converter)
2. **Обратное преобразование**: преобразование сегментов сообщений OneBot12 в вызовы API платформы (`Raw_ob12`)
3. Управление подключением к платформе (WebSocket/WebHook)
4. Предоставление унифицированного интерфейса отправки сообщений SendDSL

### Архитектура адаптера

```mermaid
flowchart LR
    subgraph receive["Прямое преобразование (прием)"]
        direction TB
        P1["События платформы"] --> C1["Converter.convert()"] --> O1["События в стандарте OneBot12"] --> S1["Система событий"] --> M1["Обработка модулями"]
    end
    subgraph send["Обратное преобразование (отправка)"]
        direction TB
        M2["Модуль формирует сообщение"] --> R1["Send.Raw_ob12()"] --> N1["Вызовы API платформы"] --> R2["Стандартный формат ответа"]
    end
```

## Структура каталогов

Стандартная структура пакета адаптера:

```
MyAdapter/
├── pyproject.toml          # Конфигурация проекта
├── README.md               # Описание проекта
├── LICENSE                 # Лицензия
└── MyAdapter/
    ├── __init__.py          # Точка входа пакета
    ├── Core.py               # Главный класс адаптера
    └── Converter.py          # Трансформатор событий
```

## Быстрый старт

### 1. Создание проекта

Рекомендуется использовать генератор для создания полной структуры проекта (с pyproject, главным классом, трансформатором):

```bash
# Стандартный проект (для публикации)
epsdk create adapter -n MyAdapter

# Локальный адаптер-плагин (без пакетирования, можно поместить в папку plugins/ для автоматической загрузки, см. ниже "Локальная разработка")
epsdk create adapter -n MyAdapter --local
```

Также можно создать вручную:

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
    "ErisPulse>=2.4.0"  # ErisPulse уже включает aiohttp, обычно не нужно отдельно зависеть
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. Создание главного класса адаптера

Рамка предоставляет декларативное управление конфигурацией с помощью `ConfigClass` / `AccountConfigClass`. Адаптеру нужно только объявить класс конфигурации, чтобы рамка автоматически загрузила, проверила и сгенерировала шаблон конфигурации.

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
# Рекомендуется корневой импорт (2.10+): часто используемые символы импортируются напрямую из корневого пакета, глубокие пути по-прежнему совместимы
from ErisPulse import BaseAdapter, BaseConfig

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
    # - self.sdk / self.logger автоматически установлены
    # - self.cfg в реальном времени читает конфигурацию
    # - self.Send / self.Request автоматически инициализированы
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **О `__init__`**: в новой версии `BaseAdapter.__init__(self, sdk=None)` автоматически обрабатывает ссылку на SDK, инициализацию логгера и загрузку конфигурации. Большинству адаптеров **не нужно переопределять `__init__`**. Подробнее см. [Примечания по __init__](#init-注意事项).

> ⚠️ **О `super().__init__()`**: `BaseAdapter.__init__()` отвечает за создание фабрик `Send` и `Request`. Если забыть вызвать, все операции отправки сообщений и запросов будут выдавать `AttributeError`. Подробнее см. [Примечания по __init__](#init-注意事项).

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
            # Бот оффлайн
            await self.emit_meta("disconnect", bot_id)
```

> Подробное руководство по управлению состоянием бота и мета-событиям см. в [Рекомендациях по разработке адаптеров - Управление состоянием бота и мета-события](best-practices.md#bot-状态管理与-meta-事件).

### 5. Реализация класса Send

Декораторы `At`/`AtAll`/`Reply` уже реализованы в базовом классе SendDSL рамки, адаптеру нужно реализовать только `Raw_ob12` и конкретные методы отправки.

Рамка предоставляет два ключевых вспомогательных метода:
- `self._apply_modifiers(message)` — автоматически объединяет декораторы At/AtAll/Reply в сегменты сообщения
- `self.send_context` — получает словарь контекста отправки (`target_type`, `target_id`, `account_id`)

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... остальной код ...
    
    class Send(BaseAdapter.Send):

        def Raw_ob12(self, message, **kwargs):
            """
            Отправка сообщения в формате OneBot12 (обязательно реализовать)

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

        # Методы Text/Image/Voice/Video/File уже унаследованы от базового класса SendDSL,
        # по умолчанию делегируют Raw_ob12, не нужно повторно реализовывать.
        # Если нужна платформо-специфическая логика, можно переопределить отдельный метод:
        # def Text(self, text: str):
        #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Особенности реализации методов отправки медиа (Image/Video/File):**

- Базовая реализация по умолчанию будет封装 `file` параметр как сегмент OneBot12 и передаст его в `Raw_ob12`, адаптер должен обработать загрузку/отправку в `Raw_ob12`
- Параметр `file` должен поддерживать как `bytes` двоичные данные, так и `str` URL
- При передаче URL нужно сначала загрузить файл, затем отправить на платформу
- Платформа обычно сначала вызывает интерфейс загрузки, чтобы получить идентификатор файла, затем вызывает интерфейс отправки

**Метод `__getattr__` магии:**

- Реализует методы с независимым от регистра именем (Text, text, TEXT могут вызываться)
- Несуществующие методы должны возвращать информационное сообщение, а не ошибку

**Метод `Raw_ob12`:**

- Преобразует стандартный формат сообщений OneBot12 в формат платформы и отправляет
- Использует `self._apply_modifiers(message)` для автоматической обработки декораторов At/AtAll/Reply
- Использует `**self.send_context` для передачи информации о цели отправки и учетной записи

### 6. Реализация трансформатора

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
        """Преобразование подробного типа"""
        return "private"  # Упрощённый пример
```

### 7. Реализация класса Request (операции запроса)

Если ваша платформа поддерживает запросы от друзей, приглашения в группы и т.д., требующие решения от бота, вы можете реализовать внутренний класс `Request`:

```python
from ErisPulse import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Send и другие коды ...

    class Request(RequestDSL):
        """Реализация операций запроса (приглашения в друзья, группы и т.д.)"""

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

Способ использования модуля:

```python
from ErisPulse import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Через метод Event
    await event.approve()
    # Или через адаптер напрямую
    await adapter.myplatform.Request("req_id").accept()
```

> Если платформа не поддерживает запросы, можно не реализовывать внутренний класс `Request`. Базовый класс по умолчанию возвращает `retcode=10002` (операция не поддерживается). Подробнее см. [Спецификация операций запроса](../../standards/request-action-spec.md).

### 8. Создание точки входа пакета

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## Локальная разработка (без пакетирования)

Как и модули, адаптеры можно размещать в локальной директории плагинов проекта (по умолчанию `plugins/`, можно настроить через `ErisPulse.framework.plugins_dir`) для разработки, **без `pip install -e .`**:

```bash
# Создание локального адаптера-плагина
epsdk create adapter -n MyAdapter --local
# Структура:
# plugins/
# └── MyAdapter/
#     ├── __init__.py
#     ├── Core.py
#     └── Converter.py
```

При запуске рамки автоматически сканирует директорию плагинов и загружает находящиеся в ней модули и адаптеры (все равно как entry-point пакетов: включение, объявление конфигурации, горячая перезагрузка, очистка при выгрузке):

- **Правила идентификации**: пакетная директория (с `__init__.py`) или одиночный `.py` файл — оба варианта допустимы; приоритет отдается классу с именем `Main`, иначе берется первый найденный подкласс `BaseAdapter` / `BaseModule` в плагине
- **Перекрытие имен**: при совпадении имен локального плагина и пакета из PyPI, локальный плагин имеет приоритет (удобно для отладки)
- **Горячая перезагрузка**: `sdk.enable_plugin_hot_reload()` включает мониторинг директории плагинов, охватывая и адаптеры; горячая перезагрузка кода адаптера доступна с версии 2.11: `await sdk.adapter.reload("PlatformName")` или `await sdk.reload_adapter("PlatformName")` (проверка синтаксиса → очистка и выгрузка → очистка кэша и повторный импорт → повторная регистрация и запуск, при ошибках автоматический откат; подробнее см. [Обзор архитектуры](../../architecture.md))

### От локального плагина к выпуску

После локальной проверки, используйте подкоманду `pack`, чтобы превратить плагин в публичный стандартный проект (интерактивный выбор плагина, дополнение метаинформации, генерация pyproject с entry-point):

```bash
epsdk create pack
# Выбор плагина из директории плагинов → Ввод имени проекта/описания/автора → Генерация каталога MyAdapter/
cd MyAdapter
pip install -e .   # Превращение в стандартный пакет; затем следуйте процессу публикации на PyPI
```

> **Примечание**: после преобразования рекомендуется удалить оригинал из `plugins/`, чтобы избежать повторной загрузки локального плагина и пакета (при совпадении имен локальный имеет приоритет, что может ввести в заблуждение, что пакет заработал).

## Объявление зависимостей (опционально, 2.8.0+)

Адаптер может объявить зависимости от других адаптеров или модулей для обеспечения взаимодействия адаптеров и опциональных функций:

```python
from typing import ClassVar

class MyAdapter(BaseAdapter):
    # Жесткая зависимость: отсутствие приводит к пропуску запуска (предупреждение + статус=skipped-dependency)
    depends: ClassVar[dict] = {
        "adapters": ["onebot11"],   # Зависимые адаптеры (по названию платформы)
        "modules": ["TranslateEngine"],  # Зависимые модули (по зарегистрированному имени)
    }
    # Опциональная зависимость: отсутствие не влияет на запуск; модуль получает обратный вызов при загрузке/выгрузке (опциональный режим функций)
    optional_modules: ClassVar[list] = ["TranslateEngine"]
```

- **Порядок запуска**: адаптеры, объявившие жесткую зависимость от модуля, **откладываются до инициализации модуля**
- **Уведомления по опциональной зависимости**: `optional_modules` (или жесткая зависимость от модуля) вызывает `on_dependency_ready(module_name)` при загрузке модуля; вызывает `on_dependency_lost(module_name)` при выгрузке модуля (по умолчанию пустой реализации, можно переопределить) — переопределение для сценариев поздней загрузки и горячей перезагрузки:

```python
async def on_dependency_ready(self, module_name):
    """Опциональный модуль готов: включить соответствующую опциональную функцию"""
    if module_name == "TranslateEngine":
        self._translate = self.sdk.TranslateEngine

async def on_dependency_lost(self, module_name):
    """Опциональный модуль отсутствует: понизить функциональность"""
    if module_name == "TranslateEngine":
        self._translate = None
```

> [!NOTE]
> Эта функция требует ErisPulse **2.8.0+**.

## Примечания по `__init__`

В разработке адаптеров есть три уровня, где может потребоваться переопределение `__init__`. Ниже приведены правильные подходы для каждого уровня.

### 1. Уровень BaseAdapter (в большинстве случаев не нужно переопределять)

`BaseAdapter.__init__(self, sdk=None)` отвечает за создание фабрик `Send` / `Request` и автоматически выполняет следующее:

- Принимает параметр `sdk` и устанавливает `self.sdk`, `self.logger`
- Если объявлен `ConfigClass`, можно читать глобальную конфигурацию через `self.cfg`
- Если объявлен `AccountConfigClass`, можно читать конфигурацию нескольких учетных записей через `self.accounts`

**В большинстве случаев не нужно переопределять `__init__`**, достаточно объявить `ConfigClass`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # После объявления рамка автоматически управляет конфигурацией
    
    async def start(self):
        cfg = self.cfg  # Типобезопасное, в реальном времени чтение
        ...
```

Если действительно нужно пользовательскую инициализацию, вызовите `super().__init__(sdk)`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Передать sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

### 2. Внутренний класс Send (в большинстве случаев не нужно переопределять)

`SendDSL.__init__` отвечает за передачу состояния при цепочечных вызовах (тип цели, ID цели, учетная запись). **В большинстве случаев вам нужно переопределить только методы** (`Raw_ob12`, `Text` и т.д.), а не `__init__`.

Если действительно нужно (например, инициализация платформо-специфического состояния), **обязательно передать все параметры**:

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # Параметры: adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← Обязательно передать
            self._my_state = None  # Инициализация платформо-специфического состояния
```

**Почему обязательно передавать?** Каждый шаг цепочечного вызова создает новый экземпляр через `self.__class__(...)`:

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

Если сигнатура `__init__` не совпадает или не вызван `super()`, цепочечный вызов прервется.

### 3. Внутренний класс Request (в большинстве случаев не нужно переопределять)

Аналогично Send. Параметры: `adapter`, `request_id`, `account_id`:

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # Параметры: adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← Обязательно передать
            self._my_state = None  # Инициализация платформо-специфического состояния
```

### Сводка

| Уровень | Когда переопределять | Обязательные действия |
|------|------------|-----------|
| **BaseAdapter** | При необходимости пользовательской инициализации | `super().__init__(sdk)` (передать параметр sdk) |
| **Send внутренний класс** | При необходимости инициализации состояния отправки | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request внутренний класс** | При необходимости инициализации состояния запроса | `super().__init__(adapter, request_id, account_id)` |
| Все три уровня | В большинстве случаев | **Объявить ConfigClass, не трогать `__init__`** |

### 9. Информация о подключении и обнаружение маршрутов

Регистрируя маршруты, адаптеры, рамка будет записывать всю информацию о маршрутах. Пользователи могут получить информацию о подключении адаптера с помощью следующих API:

```python
from ErisPulse import sdk

# Получить полную информацию о подключении адаптера
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

# Перечислить все пространства имен (адаптеры/модули) маршрутов
namespaces = sdk.router.list_namespaces()
# {"myplatform": {"http": ["/myplatform/webhook"], "websocket": ["/myplatform/ws"]}}

# Получить полные URL подключения пространства имен
urls = sdk.router.get_module_urls("myplatform")
# {"base_url": "http://localhost:8080", "http": [...], "websocket": [...]}

# Получить подробную информацию о маршрутах пространства имен
routes = sdk.router.get_module_routes("myplatform")
# {"http": [{"path": "/myplatform/webhook", "methods": ["POST"]}],
#  "websocket": [{"path": "/myplatform/ws", "auth": false}]}
```

> **Примечание**: информация, возвращаемая `get_connection_info()`, подходит для отображения пользователю (например, в WebUI), помогая настроить URL обратного вызова или WebSocket на стороне платформы. При регистрации маршрута `module_name` должен полностью совпадать с именем `platform`, зарегистрированным в ErisPulse, иначе обнаружение маршрутов не будет корректно сопоставлено.

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
| `sse.close()` | Безопасное закрытие соединения SSE (безопасный вызов, может быть несколько раз) |
| `sse.closed` | Закрыто ли соединение |
| `sse.request` | Объект базового запроса (можно использовать для чтения query params, headers) |

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

> **Дизайн независимый от сервера**: `SseEmitter` использует обратные вызовы и декомпозирует от底层 HTTP-фреймворка. Рамка предоставляет `register_sse()` и `@sse` декоратор как единый вход для регистрации, адаптеры не должны напрямую зависеть от какого-либо底层 HTTP-фреймворка, чтобы реализовать конечные точки SSE.

## Далее

- [Основные концепции адаптера](core-concepts.md) - Понять архитектуру адаптера
- [Подробности SendDSL](send-dsl.md) - Изучить отправку сообщений
- [Реализация трансформатора](converter.md) - Понять преобразование событий
- [Лучшие практики разработки адаптеров](best-practices.md) - Разрабатывать качественные адаптеры