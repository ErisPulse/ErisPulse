# Основные концепции адаптера

Понимание основных концепций адаптера ErisPulse является основой для разработки адаптеров.

## Архитектура адаптера

### Отношения компонентов

```
Прямое преобразование (направление получения)               Обратное преобразование (направление отправки)
─────────────────────────────────────────────────           ─────────────────────────────────────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ Нативные события платформы     │                        │ Построенное сообщение модуля     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ Адаптер (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (конвертер событий) │──→│ │              │ │   │ (вход обратного преобразования)   │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Вызов платформенного API    │
                       │ Событие OneBot12 (стандарт) │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Стандартный формат ответа     │
                       │  Система событий         │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │  Модуль (обработка событий)  │
                       └──────────────────┘
```

**Ядро симметрии**:
- **Прямое преобразование** (Converter): Нативные события платформы → Событие OneBot12 (стандарт), исходные данные сохраняются в `{platform}_raw`
- **Обратное преобразование** (Raw_ob12): Сегменты сообщений OneBot12 → Вызов платформенного API, возвращается стандартный формат ответа

## АдаптерAdapterManager

`AdapterManager` является центральным компонентом системы адаптеров ErisPulse, отвечающим за управление регистрацией, запуском, остановкой и распределением событий всех платформенных адаптеров.

### Основные функции

- **Регистрация адаптера**: Регистрация и управление несколькими платформенными адаптерами
- **Управление жизненным циклом**: Управление запуском и остановкой адаптеров
- **Распределение событий**: Распределение событий OneBot12 (стандарт) и нативных событий платформы
- **Управление конфигурацией**: Управление состоянием включения/выключения адаптеров
- **Поддержка middleware**: Поддержка middleware событий OneBot12

### Базовое использование

```python
from ErisPulse import sdk

# Регистрация адаптера (обычно выполняется автоматически загрузчиком)
sdk.adapter.register("myplatform", MyPlatformAdapter)

# Запуск всех адаптеров
await sdk.adapter.startup()

# Запуск указанного адаптера
await sdk.adapter.startup(["myplatform"])
# Запуск всех адаптеров
await sdk.adapter.startup()

# Получение экземпляра адаптера
my_adapter = sdk.adapter.get("myplatform")
# Или доступ через свойство
my_adapter = sdk.adapter.myplatform

# Остановка всех адаптеров
await sdk.adapter.shutdown()
```

### Запуск и остановка

#### Запуск адаптера

```python
# Запуск всех зарегистрированных адаптеров
await sdk.adapter.startup()

# Запуск указанной платформы
await sdk.adapter.startup(["platform1", "platform2"])
```

**Процесс запуска**:

1. Отправка события жизненного цикла `adapter.start`
2. Отправка события `adapter.status.change` (starting)
3. Параллельный запуск отдельных адаптеров
4. При неудачном запуске автоматическая повторная попытка (стратегия экспоненциального затухания)
5. После успешного запуска отправка события жизненного цикла `adapter.status.change` (started)

**Механизм повторных попыток**:

- Первые 4 попытки: 60 секунд, 10 минут, 30 минут, 60 минут
- 5-я и последующие: фиксированный интервал 3 часа

#### Остановка адаптера

```python
# Остановка всех адаптеров
await sdk.adapter.shutdown()
```

**Процесс остановки**:

1. Отправка события жизненного цикла `adapter.stop`
2. Вызов метода `shutdown()` для всех адаптеров
3. Остановка сервера маршрутизации
4. Очистка обработчиков событий
5. Отправка события жизненного цикла `adapter.stopped`

### Управление конфигурацией

#### Проверка состояния платформы

```python
# Проверка, зарегистрирована ли платформа
exists = sdk.adapter.exists("myplatform")

# Проверка, включена ли платформа
enabled = sdk.adapter.is_enabled("myplatform")

# Использование оператора in
if "myplatform" in sdk.adapter:
    print("Платформа существует и включена")
```

#### Перечисление платформ

```python
# Перечисление всех зарегистрированных платформ
platforms = sdk.adapter.list_registered()

# Перечисление всех платформ и их состояний
status_dict = sdk.adapter.list_items()
# Возвращает: {"platform1": true, "platform2": false, ...}

# Получение списка включенных платформ
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### Слушание событий

#### События OneBot12 (стандарт)

```python
from ErisPulse import sdk

# Слушание стандартного события сообщений на всех платформах
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Получено сообщение OneBot12: {data}")

# Слушание стандартного события сообщений конкретной платформы
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"Получено сообщение myplatform: {data}")

# Слушание всех событий
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"Получено событие: {data.get('type')}")
```

#### Нативные события платформы

```python
# Слушание нативных событий конкретной платформы
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Получено нативное событие: {data}")

# Слушание нативных событий всех платформ (шаблон)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Получено нативное событие: {data}")
```

#### Механизм распределения событий

При вызове `adapter.emit(event_data)`:

1. **Обработка middleware**: Сначала выполняются все middleware OneBot12
2. **Распределение стандартных событий**: Распределяются в соответствующие обработчики событий OneBot12
3. **Распределение нативных событий**: Если присутствуют исходные данные, распределяются в обработчики нативных событий

**Правила сопоставления**:

- Точное совпадение: `@sdk.adapter.on("message")` совпадает только с событием `message`
- Шаблон: `@sdk.adapter.on("*")` совпадает со всеми событиями
- Фильтрация по платформе: `platform="myplatform"` распределяет события только указанной платформы

### Middleware

#### Добавление middleware

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """Middleware логирования"""
    print(f"Обработка события: {data.get('type')}")
    return data  # Должен вернуть данные

@sdk.adapter.middleware
async def filter_middleware(data):
    """Middleware фильтрации событий"""
    # Фильтрация ненужных событий
    if data.get("type") == "notice":
        return None  # При возврате None middleware-цепь игнорирует это возвращаемое значение, сохраняя исходные данные для передачи
    return data  # Должен вернуть данные для продолжения передачи
```

#### Порядок выполнения middleware

Middleware выполняются в порядке регистрации, более поздние зарегистрированные middleware выполняются первыми.

> **Примечание**: Если middleware возвращает `None` (например, забыт `return data`), фреймворк игнорирует это возвращаемое значение и сохраняет исходные данные для передачи, одновременно выводя предупреждение уровня warning. Это обеспечивает, что сбой одного middleware не приводит к прерыванию всей цепочки событий.

```python
# Порядок регистрации
sdk.adapter.middleware(middleware1)  # Выполняется последним
sdk.adapter.middleware(middleware2)  # Выполняется вторым
sdk.adapter.middleware(middleware3)  # Выполняется первым

# Порядок выполнения: middleware3 -> middleware2 -> middleware1
```

### Получение экземпляра адаптера

#### Метод get()

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### Доступ через свойства

```python
# Доступ по имени свойства (без учета регистра)
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## Базовый класс BaseAdapter

### Базовая структура

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """Конфигурация адаптера (автоматически управляется фреймворком после объявления)"""
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig  # Объявление класса конфигурации
    
    # Переопределение __init__ не требуется, фреймворк автоматически обрабатывает:
    # - self.sdk, self.logger
    # - self.cfg (экземпляр конфигурации с безопасным типом, чтение в реальном времени)
    # - self.Send, self.Request
    
    async def start(self):
        """Запуск адаптера (обязательно к реализации)"""
        cfg = self.cfg  # Автоматически загруженная конфигурация с безопасным типом
        pass
    
    async def shutdown(self):
        """Остановка адаптера (обязательно к реализации)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Вызов платформенного API (обязательно к реализации)"""
        pass
```

### Управление конфигурацией

Фреймворк обеспечивает декларативное управление конфигурацией, определение структуры конфигурации через dataclass, фреймворк автоматически обрабатывает загрузку, валидацию и генерацию шаблонов.

#### Конфигурация одного аккаунта

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BaseConfig

@dataclass
class TelegramConfig(BaseConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "telegram.token", "default": "Bot Token"},
        "required": True,
        "secret": True,
        "ui": {"widget": "password", "group": "basic", "order": 1},
    })
    proxy: str = field(default="", metadata={
        "description": {"i18n": "telegram.proxy", "default": "Адрес прокси"},
        "ui": {"widget": "text", "group": "advanced", "order": 10},
    })

class TelegramAdapter(BaseAdapter):
    ConfigClass = TelegramConfig
    
    async def start(self):
        cfg = self.cfg  # Безопасный тип, чтение в реальном времени
        if not cfg.token:
            raise ValueError("Токен не настроен")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Конфигурация нескольких аккаунтов

Базовый класс `BotAccountConfig` предоставляет поля `enabled` и `name`. Большинство адаптеров могут автоматически получать `bot_id` из протокола платформы или ответа на вход, и внедрять его в конфигурацию аккаунта во время преобразования событий.：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

# Большинство адаптеров: bot_id автоматически получается во время выполнения, не нужно настраивать
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Токен"},
        "required": True,
    })

# Если bot_id не удается получить при входе в систему, пользователь может заполнить его в конфигурации
@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": {"i18n": "yunhu.bot_id", "default": "ID бота"},
        "required": True,
    })
    token: str = field(default="", metadata={
        "description": {"i18n": "yunhu.token", "default": "Токен"},
        "required": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            user_id = await self._login(name, account)
            await self.emit_meta("connect", user_id)
```

#### Соглашения metadata

Метаданные полей одновременно служат для генерации комментариев TOML и рендеринга форм WebUI:

```python
metadata = {
    "description": str | dict,  # Описание поля (поддержка i18n)
    "required": bool,         # Обязательно (валидация + отметка WebUI)
    "secret": bool,           # Чувствительно (показывается как *** в WebUI, обезличивается в логах)
    "ui": {                   # Конфигурация элементов управления WebUI (старое имя "webui" по-прежнему совместимо)
        "widget": str,        # Тип элемента управления: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Группа: "basic" | "advanced" | "connection" и т.д.
        "order": int,         # Вес сортировки (чем меньше, тем раньше)
        "options": list,      # Варианты для элемента select [{label, value}]
        "placeholder": str,   # Заполнитель для поля ввода
    },
    "extra": dict,            # Дополнительные расширенные поля (передаются в schema)
}
```

`description` поддерживает два формата:

- **Обычная строка** (обратная совместимость): `"Bot Token"`
- **Словарь i18n** (рекомендуется, поддержка многоязычия): `{"i18n": "my_adapter.token", "default": "Bot Token"}`

При использовании словаря i18n необходимо заранее зарегистрировать ключи перевода в системе i18n (подробнее в [документации i18n](../../advanced/i18n.md#конфигурация_полей_многоязычия))。

#### Разбор аккаунтов

Адаптеры с несколькими аккаунтами могут использовать `_resolve_account()` для автоматического разрешения целевого аккаунта:

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: имя аккаунта, account: экземпляр конфигурации
```

Стратегия разрешения: совпадение имени аккаунта → совпадение поля `bot_id` → совпадение других строковых полей → первый включенный аккаунт.

#### Горячее обновление конфигурации

Подклассы могут переопределить `on_config_update()` для реакции на изменения конфигурации:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Токен обновлен, повторное подключение")
```

### Инициализационный процесс

Фреймворк автоматически выполняет следующую работу в `BaseAdapter.__init__(self, sdk=None)`:

1. **Ссылка SDK**: Установка `self.sdk`, `self.logger`
2. **Фабрики Send/Request**: Создание `self.Send` и `self.Request`
3. **Шаблон конфигурации**: Если объявлен `ConfigClass`, автоматически генерируется шаблон конфигурации по умолчанию (при первом запуске)
4. **Шаблон аккаунта**: Если объявлен `AccountConfigClass`, автоматически генерируется шаблон аккаунта по умолчанию (при первом запуске)

Конфигурация считывается в реальном времени через `self.cfg` / `self.accounts` (каждый раз считывается последнее значение из хранилища конфигурации). `self.config` как совместимый псевдоним для `self.cfg` также может использоваться.

Большинству адаптеров не требуется переопределять `__init__`. Если необходимо пользовательская инициализация:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Передача sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## DSL отправки сообщений Send

### Иерархия наследования

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Вложенный класс Send, наследуется от BaseAdapter.Send"""
        pass
```

### Доступные свойства

Класс `Send` автоматически устанавливает следующие свойства при вызове:

| Свойство | Описание | Способ установки |
|-----|------|---------|
| `_target_id` | ID цели | `To(id)` или `To(type, id)` |
| `_target_type` | Тип цели | `To(type, id)` |
| `_target_to` | Упрощенный ID цели | `To(id)` |
| `_account_id` | ID аккаунта отправителя | `Using(account_id)` |
| `_adapter` | Экземпляр адаптера | Устанавливается автоматически |
| `_at_user_ids` | Список @пользователей | `At(user_id)` |
| `_reply_message_id` | ID сообщения для ответа | `Reply(message_id)` |
| `_at_all` | Делать @всем | `AtAll()` |

> **Рекомендация**: Используйте свойство `self.send_context` для одновременного получения `target_type`, `target_id`, `account_id`, это более наглядно, чем прямой доступ к переменным экземпляра.

### Методы вспомогательной функции фреймворка

| Метод/Свойство | Описание |
|-----------|------|
| `self._apply_modifiers(message)` | Объединение состояния модификаторов At/AtAll/Reply со списком сегментов сообщения |
| `self.send_context` | Возвращает словарь `{target_type, target_id, account_id}` |

### Базовые методы

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Рекомендуемый способ реализации"""
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
```

### Цепные методы модификаторов

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self
```

## Конвертер событий

### Процесс преобразования

```
Платформенное нативное событие
    ↓
Converter.convert()
    ↓
Событие OneBot12 (стандарт)
```

### Обязательные поля

Все преобразованные события должны содержать:

```python
{
    "id": "Уникальный идентификатор события",
    "time": 1234567890,           # 10-значная временная метка Unix
    "type": "message/notice/request/meta",
    "detail_type": "Детальный тип события",
    "platform": "Название платформы",
    "self": {
        "platform": "Название платформы",
        "user_id": "ID бота"     # Должен совпадать с bot_id
    },
    "{platform}_raw": {...},       # Исходные данные (обязательно)
    "{platform}_raw_type": "..."    # Исходный тип (обязательно)
}
```

### Пример конвертера

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование нативного события платформы в стандартный формат OneBot12"""
        if not isinstance(raw_event, dict):
            return None
        
        # Генерация ID события
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # Преобразование временной метки
        timestamp = raw_event.get("timestamp")
        if timestamp and timestamp > 10**12:
            timestamp = int(timestamp / 1000)
        else:
            timestamp = int(timestamp) if timestamp else int(time.time())
        
        # Преобразование типа события
        event_type = self._convert_type(raw_event.get("type"))
        detail_type = self._convert_detail_type(raw_event)
        
        # Построение стандартного события
        onebot_event = {
            "id": str(event_id),
            "time": timestamp,
            "type": event_type,
            "detail_type": detail_type,
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
```

## Управление соединениями

### WebSocket соединение

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """Регистрация маршрута WebSocket"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket):
        """Обработчик WebSocket соединения"""
        self.connection = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                onebot_event = self.convert(data)
                if onebot_event:
                    await self.adapter.emit(onebot_event)
        except WebSocketDisconnect:
            self.logger.info("Соединение закрыто")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket) -> bool:
        """Аутентификация WebSocket"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook соединение

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """Регистрация маршрута WebHook"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """Обработчик запросов WebHook"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> **Запрос информации о маршруте**: Маршруты, зарегистрированные адаптерами (HTTP, WebSocket, SSE), могут быть запрошены через `sdk.adapter.get_connection_info(platform)` и `sdk.router.get_module_urls(module_name)` для получения полных адресов соединений (включая `base_url` + путь). Подробнее в [Начало работы с разработкой адаптера - Информация о соединении и обнаружение маршрутов](getting-started.md#9-информация_о_соединении_и_обнаружение_маршрутов) и [Поддержка SSE](getting-started.md#10-поддержка_sse-server_sent_events)。

## Стандарт ответов API

Фреймворк предоставляет методы `make_response()` и `make_error()` для конструирования стандартизированных ответов, без необходимости вручную строить словарь ответа.

### Успешный ответ

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return self.make_response(
            data=raw_response.get("data"),
            message_id=raw_response.get("data", {}).get("message_id", ""),
            raw=raw_response,
        )
    except Exception as e:
        return self.make_error(message=str(e), raw=None)
```

### Ручное построение ответа (старый способ, по-прежнему совместим)

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok",
        "retcode": 0,
        "data": {...},
        "message_id": "msg_id",
        "message": "",
        "myplatform_raw": raw_response
    }
```

## Поддержка нескольких аккаунтов

### Декларативная конфигурация (рекомендуется)

После объявления класса конфигурации через `AccountConfigClass`, фреймворк автоматически управляет загрузкой, валидацией и генерацией шаблонов для нескольких аккаунтов:

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={"description": "ID бота", "required": True})
    token: str = field(default="", metadata={"description": "Токен", "required": True, "secret": True})

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"Запуск аккаунта {name}: {account.bot_id}")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # Использование account.token, account.bot_id и других полей
```

### Файл конфигурации аккаунта

```toml
[MyAdapter.accounts.account1]
bot_id = "bot_001"
token = "token1"
enabled = true

[MyAdapter.accounts.account2]
bot_id = "bot_002"
token = "token2"
enabled = true
```

### Отправка указанному аккаунту

```python
# Использование метода Using для указания аккаунта
my_adapter = adapter.get("myplatform")

# Через self.user_id из события (рекомендуется, наиболее универсально)
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# Через имя аккаунта
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Связь self.user_id и Using

Механизм ответа на события фреймворка автоматически извлекает `account_id` (приоритет) или `user_id` из поля `self` события, передавая его как параметр `Using`. Разработчикам адаптеров необходимо убедиться, что значение `self.user_id` в Converter корректно сопоставляется с `_resolve_account()`.

**Внутреннее поведение фреймворка** (`Event._get_adapter_and_target`):

```python
# Логика извлечения bot_id фреймворком
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Вызов Using только если bot_id не пустой
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Ключевой момент**: Даже если адаптер использует только одну конфигурацию бота, при правильной установке `self.user_id` в Converter, фреймворк передаст его как параметр `Using`. Адаптер должен обеспечить, чтобы `self.user_id` совпадал с идентифицирующим полем в `AccountConfigClass` (например, `bot_id`), чтобы `_resolve_account()` мог сопоставить правильный аккаунт. Если `self.user_id` пуст, фреймворк не вызовет `Using`, в этом случае `account_id`, полученный `call_api`, будет `None`, а `_resolve_account(None)` вернет первый включенный аккаунт.

## Обработка ошибок

### Повторные попытки соединения

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(f"Соединение не удалось, повторная попытка через {wait_time} секунд")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### Обработка ошибок API

```python
async def call_api(self, endpoint: str, **params):
    try:
        # Рекомендуется использовать встроенный клиент SDK
        from ErisPulse.Core import client
        from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self._standardize_response(response)
    except ClientTimeoutError:
        self.logger.error(f"Запрос истек: {endpoint}")
        return self._error_response("Запрос истек", 32000)
    except ClientError as e:
        self.logger.error(f"Ошибка сети: {e}")
        return self._error_response("Ошибка сетевого запроса", 33000)
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}")
        return self._error_response(str(e), 34000)
```

> **Обратная совместимость**: Старый код адаптера, использующий напрямую `aiohttp.ClientSession`, не затронут и все еще может перехватывать `aiohttp.ClientError`. Оба способа могут сосуществовать. Для нового кода рекомендуется использовать `sdk.client` + иерархию исключений ErisPulse.

## Управление состоянием бота

AdapterManager содержит встроенную систему отслеживания состояния бота, автоматически поддерживающую онлайн-статус, время активности и метаданные всех зарегистрированных ботов.

### Автоматическое обнаружение

Когда адаптер отправляет события через `adapter.emit()`, фреймворк автоматически проверяет поле `self` в событии:

- **meta-события**: Выполняются соответствующие операции на основе `detail_type` (connect регистрация/отметка офлайн/heartbeat обновление времени активности)
- **обычные события** (message/notice/request): Автоматическое обнаружение бота и обновление времени активности

```python
# Все события, содержащие поле self, вызывают автоматическое обнаружение
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Бот "bot123" автоматически зарегистрирован (если впервые) и обновлено время активности
```

### Типы meta-событий

| `detail_type` | Описание | Поведение фреймворка |
|---|---|
| `connect` | Подключение бота | Регистрация бота и запуск события жизненного цикла `adapter.bot.online` |
| `disconnect` | Отключение бота | Отметка бота как офлайн и запуск события жизненного цикла `adapter.bot.offline` |
| `heartbeat` | Сердцебиение бота | Обновление времени активности и метаданных бота |

### Отправка meta-событий адаптером

Использование `emit_meta()` позволяет отправить meta-событие одной строкой:

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # Отправка события connect одной строкой
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="Мой_робот")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

Также поддерживается ручное построение (старый способ, по-прежнему совместим):

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### Расширенная информация поля `self`

Помимо обязательных полей `platform` и `user_id`, поле `self` поддерживает следующие необязательные поля:

| Поле | Описание |
|---|---|
| `user_name` | Имя пользователя бота |
| `nickname` | Никнейм бота |
| `avatar` | URL аватара бота |
| `account_id` | Идентификатор для нескольких аккаунтов |

### Запрос состояния бота

```python
from ErisPulse import sdk

# Получение информации об отдельном боте
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# Перечисление всех ботов
all_bots = sdk.adapter.list_bots()

# Перечисление ботов указанной платформы
platform_bots = sdk.adapter.list_bots("myplatform")

# Проверка, онлайн ли бот
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Получение полного сводного статуса (подходит для отображения в WebUI)
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Слушание жизненного цикла бота

```python
from ErisPulse import sdk

@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Бот онлайн: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Бот офлайн: {platform}/{bot_id}")
```

## Связанные документы

- [Начало работы с разработкой адаптера](getting-started.md) - Создание первого адаптера
- [Подробное описание SendDSL](send-dsl.md) - Изучение отправки сообщений
- [Рекомендации по разработке адаптера](best-practices.md) - Разработка качественного адаптера