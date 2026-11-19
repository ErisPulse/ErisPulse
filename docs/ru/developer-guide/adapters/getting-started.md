# Введение в разработку адаптеров

> [!TIP]
> **Когда читать эту статью**: вводная статья по пути разработки адаптеров (обязательно к прочтению). От нуля написать адаптер, понять границы ответственности адаптера и структуру проекта — всё это здесь; прочитав, переходите к [конвертерам событий](converter.md) и [подробному разбору SendDSL](send-dsl.md) по мере необходимости.

Пройдя по этой статье, вы получите минимально рабочий адаптер (класс-основа + конвертер + Send), способный принимать события и отправлять сообщения, а также ясно поймёте, какова ответственность каждого компонента — все работы по подключению новой платформы начинаются именно здесь.

## Адаптер: краткий обзор

### Что такое адаптер

Адаптер — это мост между ErisPulse и различными платформами сообщений, отвечающий за:

1. **Прямое преобразование**: получение событий платформы и преобразование их в стандартный формат OneBot12 (Converter)
2. **Обратное преобразование**: преобразование сегментов сообщений OneBot12 в вызовы API платформы (`Raw_ob12`)
3. Управление подключением к платформе (WebSocket/WebHook)
4. Предоставление унифицированного интерфейса отправки сообщений SendDSL

### Архитектура адаптера

```mermaid
flowchart LR
    subgraph receive["Прямое преобразование (прием)"]
        direction TB
        P1["Событие платформы"] --> C1["Converter.convert()"] --> O1["Стандартное событие OneBot12"] --> S1["Система событий"] --> M1["Модуль обработки"]
    end
    subgraph send["Обратное преобразование (отправка)"]
        direction TB
        M2["Модуль формирует сообщение"] --> R1["Send.Raw_ob12()"] --> N1["Вызов API платформы"] --> R2["Стандартный формат ответа"]
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

Рекомендуется использовать генератор, чтобы получить готовую структуру (включая pyproject, основной класс и конвертер):

```bash
# Стандартный проект (для публикации и установки)
epsdk create adapter -n MyAdapter

# Локальный адаптер-плагин (без упаковки, просто помещается в папку plugins/ и автоматически загружается, см. ниже "Локальная разработка")
epsdk create adapter -n MyAdapter --local
```

Генератор по умолчанию создаёт шаблон сервера WebSocket; при необходимости можно выбрать шаблон для другого типа подключения с помощью `--template` (создаёт готовый базовый класс для соответствующего режима связи, `start`/`shutdown` не нужно писать самостоятельно):

```bash
epsdk create adapter -n MyAdapter --template polling   # Тип HTTP-опроса (getUpdates)
epsdk create adapter -n MyAdapter --template webhook   # Тип HTTP-обратного вызова (платформа отправляет данные)
```

> Различия между тремя типами подключения и минимальная реализация базовых классов см. в [Основных концепциях адаптера - Базовые классы для режимов подключения](core-concepts.md#连接模式半成品基类). Полные рабочие примеры смотри в репозитории `examples/example-adapter-polling/` и `examples/example-adapter-webhook/`.

Также можно создать вручную:

```bash
mkdir MyAdapter && cd MyAdapter
```

### 2. Создание pyproject.toml

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "MyAdapter платформенный адаптер"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "ErisPulse>=2.4.0"  # ErisPulse уже содержит aiohttp, обычно не нужно отдельно зависеть
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. Создание основного класса адаптера

Фреймворк предоставляет `ConfigClass` / `AccountConfigClass` для декларативного управления конфигурацией, адаптеру достаточно объявить класс конфигурации, и фреймворк автоматически загрузит, проверит и сгенерирует шаблон конфигурации.

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
# Рекомендуемый корневой импорт (2.10+): часто используемые символы импортируются напрямую из корневого пакета, глубокие пути по-прежнему совместимы
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
    ConfigClass = MyAdapterConfig  # Объявляем класс конфигурации, фреймворк сам управляет
    
    # Не нужно переопределять __init__! Фреймворк сам обрабатывает:
    # - self.sdk / self.logger автоматически устанавливаются
    # - self.cfg — реальное чтение конфигурации
    # - self.Send / self.Request автоматически инициализируются
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **О `__init__`**: в новой версии `BaseAdapter.__init__(self, sdk=None)` автоматически обрабатывает ссылку на SDK, инициализацию логирования и загрузку конфигурации. Большинству адаптеров **не нужно переопределять `__init__`**. Подробнее см. [Примечания к __init__](#init-注意事项)。

> ⚠️ **О `super().__init__()`**: `BaseAdapter.__init__()` отвечает за создание фабрик `Send` и `Request`. Если забыть вызвать, все операции отправки сообщений и запросов будут вызывать `AttributeError`. Подробнее см. [Примечания к __init__](#init-注意事项)。

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
        # Очистка соединений и ресурсов
        self.logger.info("Адаптер остановлен")
    
    async def call_api(self, endpoint: str, **params):
        """Вызов API платформы (обязательно реализовать)"""
        raise NotImplementedError("Необходимо реализовать call_api")
```

#### Активная отправка мета-событий

Адаптер должен активно отправлять мета-события, чтобы фреймворк отслеживал состояние онлайн-бота. Использование `emit_meta()` позволяет легко выполнить это за один шаг:

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

> Подробное управление состоянием бота и описание мета-событий см. в [Лучшие практики адаптера - Управление состоянием бота и мета-события](best-practices.md#bot-状态管理与-meta-事件)。

### 5. Реализация класса Send

Декораторы `At`/`AtAll`/`Reply` уже реализованы в базовом классе SendDSL, адаптеру нужно только реализовать `Raw_ob12` и конкретные методы отправки.

Фреймворк предоставляет два важных вспомогательных метода:
- `self._apply_modifiers(message)` — автоматически объединяет декораторы At/AtAll/Reply в сегменты сообщения
- `self.send_context` — получает словарь контекста отправки (`target_type`, `target_id`, `account_id`)

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... другие коды ...

    class Send(BaseAdapter.Send):

        def Raw_ob12(self, message, **kwargs):
            """
            Отправка сообщения в формате OneBot12 (обязательно реализовать)

            Использование _apply_modifiers для автоматического объединения состояния декораторов,
            использование send_context для получения контекста отправки.
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

        # Методы Text/Image/Voice/Video/File/Location уже унаследованы от базового класса SendDSL,
        # по умолчанию делегируют вызов Raw_ob12, повторно реализовывать не нужно.
        # Если нужна платформо-специфическая логика, можно переопределить отдельные методы:
        # def Text(self, text: str):
        #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Особенности реализации методов отправки медиа (Image/Video/File):**

- Базовая реализация по умолчанию封装 `file` параметр в сегмент OneBot12 и передаёт его в `Raw_ob12`, адаптер должен обрабатывать загрузку/отправку в `Raw_ob12`
- Параметр `file` должен поддерживать как `bytes` (двоичные данные), так и `str` (URL)
- При передаче URL нужно сначала скачать файл, а затем отправить на платформу
- Платформа обычно требует сначала вызвать загрузочный API для получения идентификатора файла, а затем вызвать API отправки

**Метод `__getattr__` магии:**

- Реализация методов без учёта регистра (Text/text/TEXT могут вызываться)
- Нedefинированные методы должны возвращать информационное сообщение, а не вызывать ошибку

**Метод `Raw_ob12`:**

- Преобразует стандартный формат сообщения OneBot12 в платформо-специфический формат для отправки
- Использует `self._apply_modifiers(message)` для автоматической обработки декораторов At/AtAll/Reply
- Использует `**self.send_context` для передачи информации о цели отправки и аккаунте

### 6. Реализация конвертера

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование платформо-специфичного события в стандартный формат OneBot12"""
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
        return "private"  # Пример упрощения
```

### 7. Реализация класса Request (операции запроса)

Если платформа поддерживает запросы от друзей, приглашения в группы и т.д., которые требуют решения от бота, можно реализовать внутренний класс `Request`:

```python
from ErisPulse import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Send и другие коды ...

    class Request(RequestDSL):
        """Реализация операций запроса (приглашения друзей, групповые приглашения и т.д.)"""

        # Публичные методы accept()/reject() предоставляются базовым классом (авторизация + обёртка задачи),
        # адаптер переопределяет только _do_accept / _do_reject, возвращая стандартный ответ dict
        async def _do_accept(self, **kwargs) -> dict:
            """Согласие с запросом"""
            result = await self._adapter.call_api(
                endpoint="/set_request",
                request_id=self._request_id,
                account_id=self.request_context.get("account_id"),
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

        async def _do_reject(self, **kwargs) -> dict:
            """Отказ от запроса (аналогично _do_accept: approve=False)"""
            result = await self._adapter.call_api(
                endpoint="/set_request",
                request_id=self._request_id,
                account_id=self.request_context.get("account_id"),
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
```

Способ использования модулями:

```python
from ErisPulse import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Через удобный метод Event
    await event.approve()
    # Или через адаптер напрямую
    await adapter.myplatform.Request("req_id").accept()
```

> Если платформа не поддерживает операции запроса, можно не реализовывать внутренний класс `Request`. Базовый класс по умолчанию возвращает `retcode=10002` (операция не поддерживается). Подробнее см. [Спецификация операций запроса](../../standards/request-action-spec.md)。

### 8. Создание точки входа пакета

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## Локальная разработка (без упаковки)

Как и модули, адаптеры можно размещать в локальной директории плагинов (по умолчанию `plugins/`, можно настроить через `ErisPulse.framework.plugins_dir`) и разрабатывать напрямую, **без `pip install -e .`**:

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

При запуске фреймворк автоматически сканирует директорию плагинов и загружает в ней модули и адаптеры (одинаково с entry-point пакетами: включение, объявление конфигурации, горячая перезагрузка, очистка при выгрузке — всё одинаково):

- **Правила идентификации**: пакетная директория (с `__init__.py`) или одиночный `.py` файл — оба варианта допустимы; приоритет отдаётся имени `Main`, иначе первый `BaseAdapter` / `BaseModule` подкласс в плагине
- **Перекрытие**: при одинаковом имени локальный плагин имеет приоритет над PyPI-пакетом (удобно для отладки)
- **Горячая перезагрузка**: `sdk.enable_plugin_hot_reload()` включает мониторинг директории плагинов, включая адаптеры; горячая перезагрузка кода адаптера доступна с 2.11: `await sdk.adapter.reload("platform_name")` или `await sdk.reload_adapter("platform_name")` (предварительная проверка синтаксиса → очистка и удаление → очистка кэша и повторная загрузка → повторная регистрация и запуск, при сбое автоматический откат; подробнее см. [Обзор архитектуры](../../architecture.md)）

### От локального плагина к публикации

После локальной проверки используйте подкоманду `pack`, чтобы превратить плагин в публикуемый стандартный проект (интерактивный выбор плагина, дополнение метаинформации, генерация `pyproject` с entry-point):

```bash
epsdk create pack
# Выбор плагина из директории плагинов → Ввод имени проекта/описания/автора → Генерация каталога MyAdapter/
cd MyAdapter
pip install -e .   # Превращение в стандартный пакет; затем публикация на PyPI по стандартному процессу
```

> **Примечание**: после преобразования рекомендуется удалить оригинальный файл из `plugins/`, чтобы избежать повторной загрузки локального плагина и пакета (при одинаковом имени локальный имеет приоритет, что может создать ложное впечатление, что пакет активен).

## Объявление зависимостей (опционально, 2.8.0+)

Адаптер может объявить зависимости от других адаптеров или модулей для реализации взаимодействия между адаптерами и опциональных функций:

```python
from typing import ClassVar

class MyAdapter(BaseAdapter):
    # Жёсткая зависимость: при отсутствии пропускает запуск (предупреждение + статус=skipped-dependency событие)
    depends: ClassVar[dict] = {
        "adapters": ["onebot11"],   # Зависимые адаптеры (по имени платформы)
        "modules": ["TranslateEngine"],  # Зависимые модули (по зарегистрированному имени)
    }
    # Опциональная зависимость: при отсутствии не влияет на запуск; при загрузке/выгрузке модуля вызывается обратный вызов (опциональный режим функциональности)
    optional_modules: ClassVar[list] = ["TranslateEngine"]
```

- **Порядок запуска**: адаптеры, объявившие жёсткую зависимость от модуля, будут запущены **после инициализации модуля**
- **Уведомления по опциональным зависимостям**: `optional_modules` (или жёсткие зависимости модуля) вызывают `on_dependency_ready(module_name)` при загрузке; `on_dependency_lost(module_name)` при выгрузке (по умолчанию пустые реализации, можно переопределить) — переопределение для сценариев поздней загрузки и горячей перезагрузки:

```python
async def on_dependency_ready(self, module_name):
    """Опциональный модуль готов: включить соответствующую опциональную функцию"""
    if module_name == "TranslateEngine":
        self._translate = self.sdk.TranslateEngine

async def on_dependency_lost(self, module_name):
    """Опциональный модуль утрачен: понизить функциональность"""
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
- Если объявлен `ConfigClass`, через `self.cfg` можно читать глобальную конфигурацию в реальном времени
- Если объявлен `AccountConfigClass`, через `self.accounts` можно читать конфигурацию нескольких аккаунтов в реальном времени

**В большинстве случаев не нужно переопределять `__init__`**, достаточно объявить `ConfigClass`:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # Объявив, фреймворк сам управляет конфигурацией
    
    async def start(self):
        cfg = self.cfg  # Типобезопасно, в реальном времени
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

`SendDSL.__init__` отвечает за передачу состояния при цепочечных вызовах (тип цели, ID цели, аккаунт). **В большинстве случаев нужно переопределять только методы** (`Raw_ob12`, `Text` и т.д.), а не `__init__`.

Если действительно нужно (например, инициализация платформо-специфического состояния), **обязательно передать все параметры**:

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # Параметры: adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← Обязательно передать
            self._my_state = None  # Инициализация платформо-специфического состояния
```

**Почему обязательно передавать?** Каждый шаг цепочечного вызова создаёт новый экземпляр через `self.__class__(...)`:

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

Если подпись `__init__` несовместима или не вызван `super()`, цепочечный вызов прервётся.

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

| Уровень | Когда переопределять | Необходимые действия |
|------|------------|-----------|
| **BaseAdapter** | Когда нужна пользовательская логика инициализации | `super().__init__(sdk)` (передать параметр sdk) |
| **Send внутренний класс** | Когда нужно инициализировать состояние, связанное с отправкой | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request внутренний класс** | Когда нужно инициализировать состояние, связанное с запросами | `super().__init__(adapter, request_id, account_id)` |
| Все три уровня | В большинстве случаев | **Объявить ConfigClass, не трогать `__init__`** |

### 9. Информация о подключении и обнаружение маршрутов

После регистрации маршрутов адаптером фреймворк сохраняет всю информацию о маршрутах. Пользователь может получить полную информацию о подключении адаптера с помощью следующих API:

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

# Вывести все пространства имён (адаптеры/модули) с маршрутами
namespaces = sdk.router.list_namespaces()
# {"myplatform": {"http": ["/myplatform/webhook"], "websocket": ["/myplatform/ws"]}}

# Получить полные URL-адреса для пространства имён
urls = sdk.router.get_module_urls("myplatform")
# {"base_url": "http://localhost:8080", "http": [...], "websocket": [...]}

# Получить подробную информацию о маршрутах для пространства имён
routes = sdk.router.get_module_routes("myplatform")
# {"http": [{"path": "/myplatform/webhook", "methods": ["POST"]}],
#  "websocket": [{"path": "/myplatform/ws", "auth": false}]}
```

> **Примечание**: информация, возвращаемая `get_connection_info()`, подходит для отображения пользователю (например, в WebUI), чтобы помочь настроить URL-адреса обратной связи или WebSocket-подключения на стороне платформы. Имя `module_name`, указанное при регистрации маршрута, должно точно совпадать с именем платформы, зарегистрированной в ErisPulse, иначе обнаружение маршрутов не будет корректно сопоставлено.

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
| `sse.send(data, event=None, id=None, retry=None)` | Отправка события SSE. Не-строковые данные автоматически сериализуются в JSON |
| `sse.close()` | Безопасное завершение соединения SSE (безопасный вызов, может быть вызван несколько раз) |
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

# get_module_routes помечает streaming: true
sdk.router.get_module_routes("MyModule")
# {"http": [...], "websocket": [...], "sse": [{"path": "/MyModule/events", "streaming": true}]}

# get_module_urls сгенерирует полный URL
sdk.router.get_module_urls("MyModule")
# {"sse": [{"path": "/MyModule/events", "url": "http://localhost:8080/MyModule/events"}]}
```

> **Дизайн независимости от сервера**: `SseEmitter` использует обратные вызовы и декомпозирует зависимость от нижележащего HTTP-фреймворка. Фреймворк предоставляет `register_sse()` и `@sse` как единый вход для регистрации, адаптер не должен напрямую зависеть от нижележащего HTTP-фреймворка, чтобы реализовать конечную точку SSE.

## Далее

### Завершение трёх основных компонентов адаптера

- [Конвертеры событий](converter.md) — реализация преобразования платформо-специфичных событий в формат OneBot12 и распространённые ошибки
- [Подробный разбор SendDSL](send-dsl.md) — цепочка отправки сообщений, декораторы и правила отправки
- [Основные концепции адаптера](core-concepts.md) — механизм BaseAdapter / жизненный цикл / многоконтактная модель

### После запуска основного кода

- [Лучшие практики адаптера](best-practices.md) — инженерное завершение: повторное подключение, таймеры, обработка ошибок
- [Руководство по публикации и магазину модулей](../publishing.md) — публикация на PyPI и в магазин модулей