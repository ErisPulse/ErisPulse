# Введение в разработку адаптеров

В этом руководстве вы научитесь разрабатывать адаптеры для ErisPulse для подключения новых платформ обмена сообщениями.

## Введение в адаптеры

### Что такое адаптер

Адаптер — это мост между ErisPulse и различными платформами обмена сообщениями, который отвечает за:

1. **Прямое преобразование** (Converter): приём событий платформы и преобразование их в стандартный формат OneBot12
2. **Обратное преобразование** (Raw_ob12): преобразование сообщений OneBot12 в вызовы API платформы
3. Управление соединением с платформой (WebSocket/WebHook)
4. Предоставление универсального интерфейса отправки сообщений SendDSL

### Архитектура адаптера

```
Прямое преобразование (приём)                        Обратное преобразование (отправка)
─────────────                        ─────────────
Событие платформы                               Конструкция сообщения модулем
    ↓                                    ↓
Converter.convert()               Send.Raw_ob12()
    ↓                                    ↓
Стандартное событие OneBot12                   Вызов нативного API платформы
    ↓                                    ↓
Система событий                             Стандартный формат ответа
    ↓
Обработка модулем
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
description = "Адаптер платформы MyAdapter"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "ErisPulse>=2.4.0"  # В ErisPulse уже встроен aiohttp, отдельная зависимость обычно не требуется
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. Создание главного класса адаптера

框架提供了 `ConfigClass` / `AccountConfigClass` декларативное управление конфигурацией, адаптеру нужно просто объявить класс конфигурации, и фреймворк автоматически загрузит, проверит и сгенерирует шаблон конфигурации.

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import AdapterConfig

@dataclass
class MyAdapterConfig(AdapterConfig):
    """MyAdapter 配置"""
    api_endpoint: str = field(
        default="https://api.example.com",
        metadata={
            "description": "API 地址",
            "required": False,
            "webui": {"widget": "text", "group": "connection", "order": 1},
        },
    )
    token: str = field(
        default="",
        metadata={
            "description": "平台 Token",
            "required": True,
            "secret": True,
            "webui": {"widget": "password", "group": "basic", "order": 2},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # 声明配置类，框架自动管理
    
    # 不需要覆写 __init__！框架自动处理：
    # - self.sdk / self.logger 自动设置
    # - self.config 自动加载配置
    # - self.Send / self.Request 自动初始化
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **关于 `__init__`**：新版本中 `BaseAdapter.__init__(self, sdk=None)` 会自动处理 SDK 引用、日志初始化 и конфигурации. Большинство адаптеров **не нужно переопределять `__init__`**. См. [Примечания по `__init__`](#init-примечания).

> ⚠️ **关于 `super().__init__()`**：`BaseAdapter.__init__()` отвечает за создание экземпляров `Send` и `Request`. Если забыть вызвать этот метод, все операции по отправке сообщений и запросы приведут к ошибке `AttributeError`. См. [Примечания по `__init__`](#init-примечания).

### 4. Реализация обязательных методов

```python
class MyAdapter(BaseAdapter):
    # ... код __init__ ...
    
    async def start(self):
        """Запуск адаптера (обязательная реализация)"""
        # Регистрация WebSocket или WebHook маршрутов
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("Адаптер запущен")
    
    async def shutdown(self):
        """Остановка адаптера (обязательная реализация)"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # Очистка соединений и ресурсов
        self.logger.info("Адаптер остановлен")
    
    async def call_api(self, endpoint: str, **params):
        """Вызов API платформы (обязательная реализация)"""
        raise NotImplementedError("Необходимо реализовать call_api")
```

#### Активная отправка Meta-событий

Адаптер должен активно отправлять meta-события, чтобы фреймворк мог отслеживать онлайн-статус бота. Используя `emit_meta()` можно сделать это одной строкой:

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

> Более подробную информацию о управлении состоянием бота и Meta-событиях см. в [Рекомендациях по разработке адаптеров - Управление состоянием бота](best-practices.md#bot-управление-состоянием-и-meta-событиями).

### 5. Реализация класса Send

Декораторы `At`/`AtAll`/`Reply` уже встроены в базовый класс SendDSL фреймворка, адаптеру нужно реализовать только `Raw_ob12` и конкретные методы отправки.

Фреймворк предоставляет два важных вспомогательных метода:
- `self._apply_modifiers(message)` — автоматическое объединение декораторов At/AtAll/Reply в сообщение
- `self.send_context` — получение словаря контекста отправки (`target_type`, `target_id`, `account_id`)

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... другой код ...
    
    class Send(BaseAdapter.Send):
        
        def Raw_ob12(self, message, **kwargs):
            """
            Отправка сообщения в формате OneBot12 (обязательная реализация)

            Используйте _apply_modifiers для автоматического объединения состояния декораторов,
            используйте send_context для получения контекста отправки.
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
            """Отправка сообщения с изображением"""
            return self.Raw_ob12([
                {"type": "image", "data": {"file": file}}
            ])
```

**Ключевые моменты реализации для медиа-методов (Image/Video/File):**

- Параметр `file` должен поддерживать как бинарные данные `bytes`, так и строки `str` URL
- При передаче URL необходимо сначала скачать файл, а затем загрузить его на платформу
- Для платформы обычно требуется сначала вызвать интерфейс загрузки для получения идентификатора файла, а затем вызвать интерфейс отправки

**Магический метод `__getattr__`:**

- Реализуйте регистр названий методов без учета регистра (`Text`, `text`, `TEXT` работают)
- Для неопределенных методов следует возвращать сообщение-подсказку, а не ошибку

**Метод `Raw_ob12`:**

- Преобразует стандартный формат сообщений OneBot12 в формат платформы для отправки
- Используйте `self._apply_modifiers(message)` для автоматической обработки декораторов At/AtAll/Reply
- Используйте `**self.send_context` для передачи информации о цели отправки и учетной записи

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

### 7. Реализация класса Request (операции запросов)

Если ваша платформа поддерживает запросы от друзей и приглашения в группы, требующие решений от бота, можно реализовать внутренний класс `Request`:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... код Send и другие ...

    class Request(RequestDSL):
        """Реализация операций запроса (друг, приглашение в группу и т.д.)"""

        def accept(self, **kwargs):
            """Принятие запроса"""
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
            """Отклонение запроса"""
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

Пример использования модуля разработчиком:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Через удобные методы Event
    await event.approve()
    # Или через прямой доступ к адаптеру
    await adapter.myplatform.Request("req_id").accept()
```

> Если платформа не поддерживает операции запроса, класс `Request` можно не реализовывать. Базовый класс по умолчанию возвращает `retcode=10002` (неподдерживаемая операция). См. [Спецификация операций запроса](../../standards/request-action-spec.md).

### 8. Создание точки входа пакета

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## Рекомендации по `__init__`

В разработке адаптеров три уровня могут требовать переопределения `__init__`. Ниже описаны правильные подходы для каждого уровня.

### 1. Слой BaseAdapter (обязательно вызывать `super().__init__()`)

`BaseAdapter.__init__()` отвечает за **создание экземпляров фабрик `Send` и `Request`**. Если у адаптера есть свой `__init__`, необходимо вызвать инициализацию родительского класса:

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        super().__init__()  # ← Обязательно! Иначе Send / Request не будут инициализированы
        self.sdk = sdk
        # ... другая инициализация
```

**Последствия забыть вызвать**:`adapter.Send.To(...)` и `adapter.Request(...)` вызовут ошибку `AttributeError`.

### 2. Внутренний класс Send (в большинстве случаев не требуется переопределять)

`SendDSL.__init__` отвечает за передачу состояния для цепного вызова (тип цели, ID цели, учетная запись и т.д.). **В большинстве случаев вам нужно переопределять только методы** (`Raw_ob12`, `Text` и т.д.), не нужно переопределять `__init__`.

Если действительно необходимо (например, для инициализации специфичного для платформы состояния), **необходимо передать все параметры**:

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # Параметры: adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← Необходимо передать
            self._my_state = None  # Инициализация специфичная для платформы
```

**Почему необходимо передавать параметры?** Каждый шаг цепного вызова создает новый экземпляр через `self.__class__(...)`:

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

Если сигнатура `__init__` не совпадает или не вызван `super()`, цепной вызов прервется.

### 3. Внутренний класс Request (в большинстве случаев не требуется переопределять)

Аналогично с Send. Параметры: `adapter`, `request_id`, `account_id`:

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # Параметры: adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← Необходимо передать
            self._my_state = None  # Инициализация специфичная для платформы
```

### Итог

| Уровень | Когда переопределять | Обязательные действия |
|------|------------|-----------|
| **BaseAdapter** | Требуется инициализация состояния адаптера | `super().__init__()` (без параметров) |
| **Внутренний класс Send** | Требуется инициализация состояния отправки | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Внутренний класс Request** | Требуется инициализация состояния запроса | `super().__init__(adapter, request_id, account_id)` |
| **Все три уровня** | В большинстве случаев | **Только переопределять методы, не трогать `__init__`** |

## Дальнейшие шаги

- [Концепции ядра адаптера](core-concepts.md) - понимание архитектуры адаптера
- [Подробное описание SendDSL](send-dsl.md) - изучение отправки сообщений
- [Реализация конвертера](converter.md) - понимание преобразования событий
- [Рекомендации по разработке адаптеров](best-practices.md) - разработка качественного адаптера