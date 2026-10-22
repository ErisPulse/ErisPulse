# Введение в разработку адаптеров

> [!TIP]
> **Когда читать эту статью**: Входная статья в путь разработки адаптеров (обязательно к прочтению). Здесь описано, как создать адаптер с нуля, понятны границы ответственности адаптера и структура проекта; после прочтения переходите по необходимости в [конвертер событий](converter.md) и [подробное руководство по SendDSL](send-dsl.md).

Следуя этой статье, вы получите минимальный рабочий адаптер, способный принимать события и отправлять сообщения (основной класс + конвертер + Send), и будете четко понимать ответственность каждого компонента — все работы по подключению новой платформы начинаются именно здесь.

## Описание адаптера

### Что такое адаптер

Адаптер — это мост между ErisPulse и различными платформами сообщений, отвечающий за:

1. **Прямое преобразование**: получение событий платформы и их преобразование в стандартный формат OneBot12 (Converter)
2. **Обратное преобразование**: преобразование сегментов сообщений OneBot12 в вызовы API платформы (`Raw_ob12`)
3. управление подключением к платформе (WebSocket/WebHook)
4. предоставление унифицированного интерфейса отправки сообщений SendDSL

### Архитектура адаптера

```mermaid
flowchart LR
    subgraph receive["Прямое преобразование (прием)"]
        direction TB
        P1["Событие платформы"] --> C1["Converter.convert()"] --> O1["Стандартное событие OneBot12"] --> S1["Система событий"] --> M1["Обработка модулем"]
    end
    subgraph send["Обратное преобразование (отправка)"]
        direction TB
        M2["Модуль формирует сообщение"] --> R1["Send.Raw_ob12()"] --> N1["Вызов оригинального API платформы"] --> R2["Стандартный формат ответа"]
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
    ├── Core.py               # Основной класс адаптера
    └── Converter.py          # Конвертер событий
```

## Быстрый старт

### 1. Создание проекта

Рекомендуется использовать шаблон для генерации полной структуры (с pyproject, основным классом и конвертером):

```bash
# Стандартный проект (для публикации)
epsdk create adapter -n MyAdapter

# Локальный адаптер-плагин (не требует упаковки, помещается в каталог plugins и автоматически загружается, см. раздел "Локальная разработка")
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
description = "Адаптер для платформы MyAdapter"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "ErisPulse>=2.4.0"  # ErisPulse уже содержит aiohttp, обычно отдельно зависимость не требуется
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. Создание основного класса адаптера

Кадры предоставили `ConfigClass` / `AccountConfigClass` для декларативного управления конфигурацией. Адаптеру нужно только объявить класс конфигурации, и кадры автоматически загрузят, проверят и сгенерируют шаблон конфигурации.

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
# Рекомендуется корневой импорт (2.10+): часто используемые символы импортируются из корневого пакета, глубокие пути по-прежнему совместимы
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
    ConfigClass = MyAdapterConfig  # Объявление класса конфигурации, кадры автоматически управляют
    
    # Не нужно переопределять __init__! Кадры автоматически обрабатывают:
    # - self.sdk / self.logger автоматически установлены
    # - self.cfg — чтение конфигурации в реальном времени
    # - self.Send / self.Request автоматически инициализированы
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **О `__init__`**: В новой версии `BaseAdapter.__init__(self, sdk=None)` автоматически обрабатывает ссылку на SDK, инициализацию логирования и загрузку конфигурации. Большинству адаптеров **не нужно переопределять `__init__`**. Подробнее см. [Примечания по __init__](#init-注意事项).

> ⚠️ **О `super().__init__()`**: `BaseAdapter.__init__()` отвечает за создание фабрик Send и Request. Если забыть вызвать, все операции отправки сообщений и запросов вызовут `AttributeError`. Подробнее см. [Примечания по __init__](#init-注意事项).

### 4. Реализация обязательных методов

```python
class MyAdapter(BaseAdapter):
    # ... код __init__ ...
    
    async def start(self):
        """Запуск адаптера (обязательно реализовать)"""
        # Регистрация маршрута WebSocket или WebHook
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
        # Очистка соединений и ресурсов
        self.logger.info("Адаптер остановлен")
    
    async def call_api(self, endpoint: str, **params):
        """Вызов API платформы (обязательно реализовать)"""
        raise NotImplementedError("Необходимо реализовать call_api")
```

#### Активная отправка мета-событий

Адаптер должен активно отправлять мета-события, чтобы кадры отслеживали состояние онлайн-бота. Это можно сделать одной строкой с помощью `emit_meta()`:

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

> Подробное описание управления состоянием бота и мета-событий см. в [Рекомендациях по лучшим практикам адаптера - Управление состоянием бота и мета-события](best-practices.md#bot-状态管理与-meta-事件).

### 5. Реализация класса Send

Декораторы `At`/`AtAll`/`Reply` уже реализованы в базовом классе SendDSL, адаптеру нужно только реализовать `Raw_ob12` и конкретные методы отправки.

Кадры предоставляют два ключевых вспомогательных метода:
- `self._apply_modifiers(message)` — автоматически объединяет декораторы At/AtAll/Reply в сегменты сообщения
- `self.send_context` — получает словарь контекста отправки (`target_type`, `target_id`, `account_id`)

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... другие код ...
    
    class Send(BaseAdapter.Send):

        def Raw_ob12(self, message, **kwargs):
            """
            Отправка сообщения в формате OneBot12 (обязательно реализовать)

            Использует _apply_modifiers для автоматического объединения состояний декораторов,
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

        # Методы Text/Image/Voice/Video/File унаследованы от базового класса SendDSL,
        # по умолчанию делегируют Raw_ob12, повторная реализация не требуется.
        # Если нужна платформенно-специфическая логика, можно переопределить отдельные методы:
        # def Text(self, text: str):
        #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Особенности реализации методов отправки медиа (Image/Video/File):**

- Базовая реализация по умолчанию будет передавать параметр `file` в сегменте OneBot12 в метод `Raw_ob12`, адаптер должен обрабатывать загрузку/выгрузку в `Raw_ob12`
- Параметр `file` должен поддерживать как `bytes` (бинарные данные), так и `str` (URL)
- При передаче URL нужно сначала загрузить файл, затем отправить на платформу
- Платформы обычно сначала вызывают загрузочный интерфейс для получения идентификатора файла, затем вызывают интерфейс отправки

**Метод `__getattr__` (магический метод):**

- Реализует нечувствительность к регистру в именах методов (`Text`, `text`, `TEXT` — все вызовы)
- Несуществующие методы должны возвращать информационное сообщение, а не ошибку

**Метод `Raw_ob12`:**

- Преобразует стандартный формат OneBot12 сообщения в платформенно-специфический формат для отправки
- Использует `self._apply_modifiers(message)` для автоматической обработки декораторов At/AtAll/Reply
- Использует `**self.send_context` для передачи информации о цели отправки и учетной записи

### 6. Реализация конвертера

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование оригинального события платформы в стандартный формат OneBot12"""
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

Если платформа поддерживает запросы, такие как запросы на добавление в друзья, приглашения в группы, и т.д., которые требуют решения от бота, можно реализовать внутренний класс `Request`:

```python
from ErisPulse import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Send и другие коды ...

    class Request(RequestDSL):
        """Реализация операций запроса (запросы на добавление в друзья, приглашения в группы и т.д.)"""

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

Способ использования модулями:

```python
from ErisPulse import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Через удобный метод Event
    await event.approve()
    # Или через прямой доступ к адаптеру
    await adapter.myplatform.Request("req_id").accept()
```

> Если платформа не поддерживает операции запроса, можно не реализовывать внутренний класс `Request`. Базовый класс по умолчанию возвращает `retcode=10002` (операция не поддерживается). Подробнее см. [Спецификация операций запроса](../../standards/request-action-spec.md).

### 8. Создание точки входа пакета

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## Локальная разработка (без упаковки)

Подобно модулям, адаптеры также можно размещать в локальном каталоге плагинов (по умолчанию `plugins/`, можно настроить через `ErisPulse.framework.plugins_dir`) и разрабатывать напрямую, **без `pip install -e .`**:

```bash
# Генерация локального адаптера-плагина
epsdk create adapter -n MyAdapter --local
# Структура:
# plugins/
# └── MyAdapter/
#     ├── __init__.py
#     ├── Core.py
#     └── Converter.py
```

Кадры при запуске автоматически сканируют каталог плагинов и загружают в него модули и адаптеры (с тем же статусом, что и установка через entry-point: включение, объявление конфигурации, горячая перезагрузка, очистка при отключении):

- **Правила распознавания**: каталог пакета (с `__init__.py`) или одиночный файл `.py` — оба варианта допустимы; приоритет распознавания `Main`-класса, иначе первый `BaseAdapter` / `BaseModule` подкласс в плагине
- **Переопределение**: при совпадении имени локального плагина и адаптера из PyPI, локальный плагин имеет приоритет (удобно для отладки)
- **Горячая перезагрузка**: `sdk.enable_plugin_hot_reload()` включает мониторинг каталога плагинов, включая адаптеры; горячая перезагрузка кода адаптера доступна с 2.11: `await sdk.adapter.reload("platform_name")` или `await sdk.reload_adapter("platform_name")` (предварительная проверка синтаксиса → очистка → очистка кэша и повторная загрузка → повторная регистрация и запуск, при ошибке автоматическая откатка; подробнее см. [Обзор архитектуры](../../architecture.md))

### От локального плагина к публикации

После локальной проверки можно использовать подкоманду `pack`, чтобы преобразовать плагин в стандартный проект для публикации (интерактивный выбор плагина, дополнение метаинформации, генерация `pyproject` с entry-point):

```bash
epsdk create pack
# Выбор плагина из каталога плагинов → Ввод имени проекта/описания/автора → Генерация каталога MyAdapter/
cd MyAdapter
pip install -e .   # Преобразование в стандартную установку; затем следуйте процессу публикации на PyPI
```

> **Примечание**: После преобразования рекомендуется удалить оригинальный файл из `plugins/`, чтобы избежать повторной загрузки локального плагина и пакета (при совпадении имени локальный имеет приоритет, что может ввести в заблуждение, что пакет активен).

## Объявление зависимостей (опционально, 2.8.0+)

Адаптер может объявлять зависимости от других адаптеров или модулей для реализации взаимодействия адаптеров и опциональных функций:

```python
from typing import ClassVar

class MyAdapter(BaseAdapter):
    # Жёсткая зависимость: при отсутствии пропускает запуск (предупреждение + событие status=skipped-dependency)
    depends: ClassVar[dict] = {
        "adapters": ["onebot11"],   # Зависимые адаптеры (по названию платформы)
        "modules": ["TranslateEngine"],  # Зависимые модули (по зарегистрированному имени)
    }
    # Опциональная зависимость: при отсутствии не влияет на запуск; при загрузке/выгрузке модуля вызывается обратный вызов (опциональный режим функций)
    optional_modules: ClassVar[list] = ["TranslateEngine"]
```

- **Порядок запуска**: адаптеры, объявившие жёсткую зависимость от модуля, будут **отложены до инициализации модуля**
- **Уведомление по опциональной зависимости**: `optional_modules` (или жёсткая зависимость модуля) вызывает `on_dependency_ready(module_name)` при готовности модуля; при выгрузке вызывается `on_dependency_lost(module_name)` (по умолчанию пустой метод, можно переопределить) — для сценариев поздней загрузки и горячей перезагрузки:

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

`BaseAdapter.__init__(self, sdk=None)` отвечает за создание фабрик `Send` / `Request` и автоматически выполняет следующие действия:

- Принимает параметр `sdk` и устанавливает `self.sdk`, `self.logger`
- Если объявлен `ConfigClass`, можно получить доступ к глобальной конфигурации через `self.cfg`
- Если объявлен `AccountConfigClass`, можно получить доступ к многоаккаунтной конфигурации через `self.accounts`

**В большинстве случаев не нужно переопределять `__init__`**, достаточно объявить `ConfigClass`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # После объявления кадры автоматически управляют конфигурацией
    
    async def start(self):
        cfg = self.cfg  # Типобезопасное чтение в реальном времени
        ...
```

Если действительно нужна пользовательская инициализация, вызовите `super().__init__(sdk)`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Передать sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

### 2. Внутренний класс Send (в большинстве случаев не нужно переопределять)

`SendDSL.__init__` отвечает за передачу состояния в цепочке вызовов (тип цели, ID цели, учетная запись). **В большинстве случаев вам нужно переопределить только методы** (`Raw_ob12`, `Text` и т.д.), а не `__init__`.

Если действительно нужно (например, инициализация платформенно-специфического состояния), **обязательно передать все параметры**:

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # Параметры: adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← Обязательно передать
            self._my_state = None  # Инициализация платформенно-специфического состояния
```

**Почему обязательно передавать?** Каждый шаг цепочки вызовов создает новый экземпляр через `self.__class__(...)`:

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

Если `__init__` не совпадает по сигнатуре или не вызывается `super()`, цепочка вызовов прервется.

### 3. Внутренний класс Request (в большинстве случаев не нужно переопределять)

То же самое, что и для Send. Параметры: `adapter`, `request_id`, `account_id`:

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # Параметры: adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← Обязательно передать
            self._my_state = None  # Инициализация платформенно-специфического состояния
```

### Сводка

| Уровень | Когда переопределять | Обязательные действия |
|------|------------|-----------|
| **BaseAdapter** | При необходимости пользовательской инициализации | `super().__init__(sdk)` (передать параметр sdk) |
| **Внутренний класс Send** | При необходимости инициализации состояния отправки | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Внутренний класс Request** | При необходимости инициализации состояния запроса | `super().__init__(adapter, request_id, account_id)` |
| Все три уровня | В большинстве случаев | **Объявите ConfigClass, не трогайте `__init__`** |

### 9. Информация о подключении и обнаружение маршрутов

После регистрации маршрута адаптером кадры запоминают всю информацию о маршрутах. Пользователи могут получить информацию о подключении адаптера с помощью следующих API:

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

# Список всех пространств имён (адаптеров/модулей) с маршрутами
namespaces = sdk.router.list_namespaces()
# {"myplatform": {"http": ["/myplatform/webhook"], "websocket": ["/myplatform/ws"]}}

# Получить полные URL-адреса подключения для пространства имён
urls = sdk.router.get_module_urls("myplatform")
# {"base_url": "http://localhost:8080", "http": [...], "websocket": [...]}

# Получить подробную информацию о маршрутах для пространства имён
routes = sdk.router.get_module_routes("myplatform")
# {"http": [{"path": "/myplatform/webhook", "methods": ["POST"]}],
#  "websocket": [{"path": "/myplatform/ws", "auth": false}]}
```

> **Примечание**: `get_connection_info()` возвращает информацию, подходящую для отображения пользователю (например, в WebUI), помогая настроить адрес обратного вызова или адрес подключения WebSocket на стороне платформы. Имя `module_name`, используемое при регистрации маршрута, должно полностью совпадать с именем `platform`, зарегистрированным в ErisPulse для адаптера, иначе обнаружение маршрута не будет корректно сопоставлено.

### 10. Поддержка SSE (Server-Sent Events)

ErisPulse имеет встроенную поддержку SSE, независимую от сервера, модули и адаптеры могут зарегистрировать конечные точки SSE с помощью `@sdk.router.sse()`.

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
| `sse.send(data, event=None, id=None, retry=None)` | Отправка события SSE. Не строковые `data` автоматически сериализуются в JSON |
| `sse.close()` | Безопасное закрытие подключения SSE (безопасный вызов, может быть вызван несколько раз) |
| `sse.closed` | Подключение уже закрыто |
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

> **Дизайн, независимый от сервера**: `SseEmitter` использует обратные вызовы и декомпозирует от底层 HTTP-фреймворка. Кадры предоставляют `register_sse()` и `@sse` в качестве единого входа для регистрации, адаптеры не должны напрямую зависеть от какого-либо нижележащего HTTP-фреймворка, чтобы реализовать конечные точки SSE.

## Далее

### Завершение основных компонентов адаптера

- [Конвертер событий](converter.md) — реализация преобразования платформенных событий в формат OneBot12 и распространённые ошибки
- [Подробное руководство по SendDSL](send-dsl.md) — цепочка отправки сообщений, методы декораторов и правила отправки
- [Основные концепции адаптера](core-concepts.md) — механизм BaseAdapter / жизненный цикл / многоаккаунтность

### После запуска основной структуры

- [Рекомендации по лучшим практикам адаптера](best-practices.md) — инженерная доработка по повторным попыткам подключения, таймерам, обработке ошибок
- [Руководство по публикации и магазину модулей](../publishing.md) — публикация на PyPI и в магазин модулей