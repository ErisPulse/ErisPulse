# Основные концепции адаптера

Понимание основных концепций адаптера ErisPulse является основой для разработки адаптеров.

## Архитектура адаптера

### Отношения компонентов

```
Прямое преобразование (направление приема)                           Обратное преобразование (направление отправки)
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ Событие нативного │                        │ Сообщение, сконст- │
│   платформенного  │                        │   рированное мод. │
│     типа          │                        │   (Module)        │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  Адаптер (MyAdapter) │   │ Send.Raw_ob12()  │
│  Преобразователь  │   │ ┌──────────────┐ │   │ (вход для обрат- │
│  (Converter)     │──→│ │              │ │   │  ного преобразова-│
│                  │   │ │              │ │   │  ния)            │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Вызов платформ.  │
                       │ Стандартное собы- │    │    API           │
                       │       тие        │    └────────┬─────────┘
                       │ OneBot12 (OB12)   │             │
                       └────────┬─────────┘             ↓
                                │              ┌──────────────────┐
                       ┌──────────────────┐    │ Стандартный фор- │
                       │  Система событий  │    │   мат ответа      │
                       └────────┬─────────┘    └──────────────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │  Модуль (обработ- │
                       │  ка событий)     │
                       └──────────────────┘
```

**Ключевая симметрия**:
- **Прямое преобразование (Converter)**: Событие нативного типа платформы → Стандартное событие OneBot12. Исходные данные сохраняются в `{platform}_raw`.
- **Обратное преобразование (Raw_ob12)**: Сегмент сообщения OneBot12 → Вызов платформенного API. Возвращает стандартный формат ответа.

## AdapterManager — менеджер адаптеров

`AdapterManager` — это основной компонент системы адаптеров ErisPulse, отвечающий за управление регистрацией, запуском, остановкой и распределением событий всех платформенных адаптеров.

### Основные функции

- **Регистрация адаптера**: Регистрация и управление несколькими адаптерами платформ
- **Управление жизненным циклом**: Управление запуском и остановкой адаптеров
- **Распределение событий**: Распределение стандартных событий OneBot12 и событий нативного типа платформы
- **Управление конфигурацией**: Управление состоянием включения/выключения адаптеров
- **Поддержка Middleware**: Поддержка Middleware OneBot12

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

**Процесс запуска:**

1. Предоставление жизненного цикла события `adapter.start`.
2. Предоставление события `adapter.status.change` (starting).
3. Параллельный запуск отдельных адаптеров.
4. Автоматическая повторная попытка при сбое запуска (стратегия экспоненциальной задержки).
5. После успешного запуска предоставление события `adapter.status.change` (started).

**Механизм повтора:**

- Первые 4 повтора: 60 сек, 10 мин, 30 мин, 60 мин.
- 5-й и последующие повторы: фиксированный интервал 3 часа.

#### Остановка адаптера

```python
# Остановка всех адаптеров
await sdk.adapter.shutdown()
```

**Процесс остановки:**

1. Предоставление жизненного цикла события `adapter.stop`.
2. Вызов метода `shutdown()` для всех адаптеров.
3. Остановка сервера маршрутизации.
4. Очистка обработчиков событий.
5. Предоставление жизненного цикла события `adapter.stopped`.

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

#### Стандартные события OneBot12

```python
from ErisPulse import sdk

# Слушать стандартные события сообщений для всех платформ
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Получено сообщение OneBot12: {data}")

# Слушать стандартные события сообщений для определенной платформы
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"Получено сообщение myplatform: {data}")

# Слушать все события
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"Получено событие: {data.get('type')}")
```

#### События нативного типа платформы

```python
# Слушать нативные события определенной платформы
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Получено нативное событие: {data}")

# Слушать нативные события всех платформ (шаблон)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Получено нативное событие: {data}")
```

#### Механизм распределения событий

При вызове `adapter.emit(event_data)`:

1. **Обработка Middleware**: Сначала выполняются все Middleware OneBot12.
2. **Распределение стандартных событий**: Распределяются к соответствующим обработчикам стандартных событий OneBot12.
3. **Распределение нативных событий**: Если присутствуют исходные данные, распределяются к обработчикам нативных событий.

**Правила сопоставления:**

- Точное сопоставление: `@sdk.adapter.on("message")` сопоставляет только событие `message`.
- Шаблон (wildcard): `@sdk.adapter.on("*")` сопоставляет со всеми событиями.
- Фильтрация платформы: `platform="myplatform"` распределяет только события указанной платформы.

### Middleware

#### Добавление Middleware

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """Middleware для логирования"""
    print(f"Обработка события: {data.get('type')}")
    return data  # Обязан вернуть данные

@sdk.adapter.middleware
async def filter_middleware(data):
    """Middleware для фильтрации событий"""
    # Фильтровать ненужные события
    if data.get("type") == "notice":
        return None  # При возврате None middleware-цепочка игнорирует это значение и передает исходные данные дальше
    return data  # Обязан вернуть данные для продолжения передачи
```

#### Порядок выполнения Middleware

Middleware выполняются в порядке регистрации. Middleware, зарегистрированные позже, выполняются первыми.

> **Примечание**: Если Middleware возвращает `None` (например, забыт `return data`), фреймворк игнорирует это значение и передает исходные данные дальше, одновременно выводя предупреждение в лог. Это гарантирует, что ошибка в одном Middleware не приведет к сбою всей цепочки событий.

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

### Основная структура

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import AdapterConfig, BotAccountConfig

@dataclass
class MyConfig(AdapterConfig):
    """Конфигурация адаптера (декларативная, управляется фреймворком автоматически)"""
    token: str = field(
        default="",
        metadata={
            "description": "Токен бота",
            "required": True,
            "secret": True,
            "webui": {"widget": "password", "group": "basic", "order": 1},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig  # Указание класса конфигурации
    
    # Не требуется переопределять __init__, фреймворк автоматически обрабатывает:
    # - self.sdk, self.logger
    # - self.config (тибобезопасный экземпляр конфигурации)
    # - self.Send, self.Request
    
    async def start(self):
        """Запуск адаптера (необходимо реализовать)"""
        cfg = self.config  # Автоматически загруженная типобезопасная конфигурация
        pass
    
    async def shutdown(self):
        """Остановка адаптера (необходимо реализовать)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Вызов платформенного API (необходимо реализовать)"""
        pass
```

### Управление конфигурацией

Фреймворк предоставляет декларативное управление конфигурацией: конфигурация определяется через dataclass, а фреймворк автоматически обрабатывает загрузку, валидацию и генерацию шаблонов.

#### Конфигурация одного аккаунта

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import AdapterConfig

@dataclass
class TelegramConfig(AdapterConfig):
    token: str = field(default="", metadata={
        "description": "Токен бота",
        "required": True,
        "secret": True,
        "webui": {"widget": "password", "group": "basic", "order": 1},
    })
    proxy: str = field(default="", metadata={
        "description": "Адрес прокси",
        "webui": {"widget": "text", "group": "advanced", "order": 10},
    })

class TelegramAdapter(BaseAdapter):
    ConfigClass = TelegramConfig
    
    async def start(self):
        cfg = self.config  # Типобезопасно, загружается автоматически
        if not cfg.token:
            raise ValueError("Токен не настроен")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Конфигурация нескольких аккаунтов

```python
from ErisPulse.runtime.config_schema import BotAccountConfig

@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": "Идентификатор бота",
        "required": True,
        "webui": {"widget": "text", "group": "basic", "order": 1},
    })
    token: str = field(default="", metadata={
        "description": "Токен бота",
        "required": True,
        "secret": True,
        "webui": {"widget": "password", "group": "basic", "order": 2},
    })

class YunhuAdapter(BaseAdapter):
    AccountConfigClass = YunhuBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            await self._connect(name, account)
            await self.emit_meta("connect", account.bot_id, user_name=account.name)
```

#### Соглашения о metadata

Metadata-поля используются одновременно для генерации комментариев TOML и рендеринга форм WebUI:

```python
metadata = {
    "description": str,       # Описание поля (комментарий TOML + label WebUI)
    "required": bool,         # Обязательное поле (валидация + пометка WebUI)
    "secret": bool,           # Чувствительное поле (показывается как *** в WebUI, маскируется в логах)
    "webui": {
        "widget": str,        # Тип элемента управления: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Группа: "basic" | "advanced" | "connection" и т.д.
        "order": int,         # Вес сортировки (чем меньше, тем раньше)
        "options": list,      # Варианты для select: [{label, value}]
        "placeholder": str,   # Заполнитель для ввода
    }
}
```

#### Разрешение аккаунта

Адаптеры с несколькими аккаунтами могут использовать `_resolve_account()` для автоматического разрешения целевого аккаунта:

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: имя аккаунта, account: экземпляр конфигурации
```

Стратегия разрешения: точное совпадение имени аккаунта → совпадение поля `bot_id` → совпадение других строковых полей → первый включенный аккаунт.

#### Горячее обновление конфигурации

Подклассы могут переопределить `on_config_update()` для отклика на изменения конфигурации:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Токен обновлен, будет выполнено переподключение")
```

### Процесс инициализации

Фреймворк автоматически выполняет следующие действия в `BaseAdapter.__init__(self, sdk=None)`:

1. **Ссылка на SDK**: Установка `self.sdk`, `self.logger`
2. **Фабрика Send/Request**: Создание `self.Send` и `self.Request`
3. **Загрузка конфигурации**: Если указан `ConfigClass`, автоматически загружается в `self.config`
4. **Загрузка аккаунтов**: Если указан `AccountConfigClass`, автоматически загружается в `self.accounts`

Большинству адаптеров не требуется переопределять `__init__`. Для кастомной инициализации:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Передача sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## DSL для отправки сообщений Send

### Наследование

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
| `_account_id` | ID учетной записи отправки | `Using(account_id)` |
| `_adapter` | Экземпляр адаптера | Устанавливается автоматически |
| `_at_user_ids` | Список @пользователей | `At(user_id)` |
| `_reply_message_id` | ID сообщения для ответа | `Reply(message_id)` |
| `_at_all` | Быть @всем | `AtAll()` |

> **Рекомендация**: Используйте свойство `self.send_context`, чтобы получить `target_type`, `target_id`, `account_id` сразу, это более наглядно, чем прямой доступ к экземплярным переменным.

### Вспомогательные методы фреймворка

| Метод/Свойство | Описание |
|-----------|------|
| `self._apply_modifiers(message)` | Объединяет состояние модификаторов At/AtAll/Reply в список сегментов сообщения |
| `self.send_context` | Возвращает словарь `{target_type, target_id, account_id}` |

### Основные методы

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Рекомендуемая реализация"""
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

### Методы цепочки модификаторов

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self
```

## Преобразователь событий

### Процесс преобразования

```
Событие нативного типа платформы (Raw Event)
    ↓
Converter.convert()
    ↓
Стандартное событие OneBot12
```

### Обязательные поля

Все преобразованные события должны содержать:

```python
{
    "id": "Уникальный идентификатор события",
    "time": 1234567890,           # 10-битный Unix-таймстамп
    "type": "message/notice/request/meta",
    "detail_type": "Детальный тип события",
    "platform": "Название платформы",
    "self": {
        "platform": "Название платформы",
        "user_id": "ID бота"
    },
    "{platform}_raw": {...},       # Исходные данные (обязательно)
    "{platform}_raw_type": "..."    # Исходный тип (обязательно)
}
```

### Пример преобразователя

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование события нативного типа платформы в стандартный формат OneBot12"""
        if not isinstance(raw_event, dict):
            return None
        
        # Генерация ID события
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # Преобразование таймстампа
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

## Управление подключением

### WebSocket подключение

```python
from fastapi import WebSocket

class MyAdapter(BaseAdapter):
    async def start(self):
        """Регистрация WebSocket маршрута"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket: WebSocket):
        """Обработчик WebSocket подключения"""
        self.connection = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                onebot_event = self.convert(data)
                if onebot_event:
                    await self.adapter.emit(onebot_event)
        except WebSocketDisconnect:
            self.logger.info("Подключение разорвано")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket: WebSocket) -> bool:
        """Аутентификация WebSocket"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook подключение

```python
from fastapi import Request

class MyAdapter(BaseAdapter):
    async def start(self):
        """Регистрация WebHook маршрута"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request: Request):
        """Обработчик запроса WebHook"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

## Стандарт ответа API

Фреймворк предоставляет методы `make_response()` и `make_error()` для построения стандартизированных ответов, без необходимости ручного создания словарей ответов.

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

### Ручное построение ответа (старый способ по-прежнему совместим)

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

## Поддержка нескольких учетных записей

### Декларативная конфигурация (рекомендуется)

После объявления класса конфигурации с помощью `AccountConfigClass` фреймворк автоматически управляет загрузкой, валидацией и генерацией шаблонов для нескольких аккаунтов:

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

### Отправка от указанного аккаунта

```python
# Использование метода Using для указания аккаунта
my_adapter = adapter.get("myplatform")

# Через имя аккаунта
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Через ID аккаунта
await my_adapter.Send.Using("account_id").To("user", "123").Text("Hello")
```

## Обработка ошибок

### Повтор подключения

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
                    self.logger.warning(f"Сбой подключения, повтор через {wait_time} сек")
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
        self.logger.error(f"Тайм-аут запроса: {endpoint}")
        return self._error_response("Тайм-аут запроса", 32000)
    except ClientError as e:
        self.logger.error(f"Ошибка сети: {e}")
        return self._error_response("Сбой сетевого запроса", 33000)
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}")
        return self._error_response(str(e), 34000)
```

> **Обратная совместимость**: Старый код адаптеров, использующий напрямую `aiohttp.ClientSession`, не затронут и по-прежнему может перехватывать `aiohttp.ClientError`. Оба способа могут сосуществовать. Для нового кода рекомендуется использовать `sdk.client` + иерархию исключений ErisPulse.

## Управление состоянием бота

AdapterManager содержит встроенную систему отслеживания состояния бота, автоматически поддерживающую онлайн-статус, время активности и метаданные всех зарегистрированных ботов.

### Механизм автоматического обнаружения

Когда адаптер отправляет событие через `adapter.emit()`, фреймворк автоматически проверяет поле `self` в событии:

- **meta-событие**: Выполняет соответствующие операции на основе `detail_type` (connect — регистрация / disconnect — отметка оффлайн / heartbeat — обновление активности).
- **Обычные события** (message/notice/request): Автоматическое обнаружение бота и обновление времени активности.

```python
# Все события, содержащие поле self, триггерят автообнаружение
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
| `connect` | Подключение бота | Регистрация бота и триггер события жизненного цикла `adapter.bot.online` |
| `disconnect` | Отключение бота | Пометка бота как офлайн и триггер события жизненного цикла `adapter.bot.offline` |
| `heartbeat` | Пульс бота | Обновление времени активности бота и метаданных |

### Отправка meta-событий адаптером

Использование `emit_meta()` позволяет отправить meta-событие одной строкой:

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # Отправка события connect одной строкой
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="Мой робот")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

Поддерживается также ручное построение (старый способ по-прежнему совместим):

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### Расширенная информация поля `self`

Поле `self` поддерживает следующие необязательные поля, помимо обязательных `platform` и `user_id`:

| Поле | Описание |
|---|---|
| `user_name` | Имя пользователя бота |
| `nickname` | Никнейм бота |
| `avatar` | URL аватара бота |
| `account_id` | Идентификатор для нескольких аккаунтов |

### Запрос состояния бота

```python
from ErisPulse import sdk

# Получение информации о конкретном боте
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# Перечисление всех ботов
all_bots = sdk.adapter.list_bots()

# Перечисление ботов для конкретной платформы
platform_bots = sdk.adapter.list_bots("myplatform")

# Проверка, находится ли бот в сети
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Получение полного сводного состояния (подходит для отображения в WebUI)
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Слушивание жизненного цикла бота

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
    sdk.logger.info(f"Бот оффлайн: {platform}/{bot_id}")
```

## Связанные документы

- [Руководство по разработке адаптера](getting-started.md) - Создание первого адаптера
- [Подробное описание SendDSL](send-dsl.md) - Изучение отправки сообщений
- [Рекомендации по разработке адаптера](best-practices.md) - Создание качественных адаптеров