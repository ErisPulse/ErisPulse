# Основные концепции адаптера

Понимание основных концепций адаптера ErisPulse — это основа разработки адаптеров.

## Архитектура адаптера

### Отношения компонентов

```
Прямое преобразование (направление приема)                     Обратное преобразование (направление отправки)
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
                                                                
┌──────────────────┐                                        ┌──────────────────┐
│ Нативные события платформы                               │ Сообщения, собранные модулем
└────────┬─────────┘                                        └────────┬─────────┘
         │                                                        │
         ↓                                                        ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ Адаптер (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (Конвертер событий)│──→│ │              │ │   │ (Точка входа обратного преобразования)│
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Вызов платформенного API
                       │ Стандартное событие OneBot12 │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Стандартный формат ответа
                       │ Система событий     │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ Модуль (обработка событий)  │
                       └──────────────────┘
```

**Ключевая симметрия**:
- **Прямое преобразование** (Converter): Нативное событие платформы → Стандартное событие OneBot12, исходные данные сохраняются в `{platform}_raw`
- **Обратное преобразование** (Raw_ob12): Сегменты сообщений OneBot12 → Вызов платформенного API, возвращается стандартный формат ответа

## AdapterManager Менеджер адаптеров

`AdapterManager` — это основной компонент системы адаптеров ErisPulse, отвечающий за регистрацию, запуск, остановку и рассылку событий всех платформенных адаптеров.

### Основные функции

- **Регистрация адаптера**: Регистрация и управление несколькими платформенными адаптерами
- **Управление жизненным циклом**: Управление запуском и остановкой адаптеров
- **Рассылка событий**: Распределение стандартных событий OneBot12 и нативных событий платформы
- **Управление конфигурацией**: Управление состоянием включения/выключения адаптеров
- **Поддержка middleware**: Поддержка middleware для событий OneBot12

### Базовое использование

```python
from ErisPulse import sdk

# Регистрация адаптера (обычно выполняется автоматически классом Loader)
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
4. Автоматическая повторная попытка при сбое запуска (экспоненциальная стратегия с отступом)
5. После успешного запуска отправка события `adapter.status.change` (started)

**Механизм повторной попытки**:

- Первые 4 повтора: 60 сек, 10 мин, 30 мин, 60 мин
- 5-й и последующие повторы: фиксированный интервал 3 часа

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

# Перечисление всех платформ и их статуса
status_dict = sdk.adapter.list_items()
# Возврат: {"platform1": true, "platform2": false, ...}

# Получение списка включенных платформ
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### Слушание событий

#### Стандартные события OneBot12

```python
from ErisPulse import sdk

# Слушание стандартных событий сообщений всех платформ
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Получено сообщение OneBot12: {data}")

# Слушание стандартных событий сообщений определенной платформы
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
# Слушание нативных событий определенной платформы
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Получено нативное событие: {data}")

# Слушание нативных событий всех платформ (шаблон)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Получено нативное событие: {data}")
```

#### Механизм рассылки событий

При вызове `adapter.emit(event_data)`:

1. **Обработка middleware**: Сначала выполняются все middleware OneBot12
2. **Рассылка стандартных событий**: Распределение на соответствующие обработчики событий OneBot12
3. **Рассылка нативных событий**: Если есть исходные данные, распределение на обработчики нативных событий

**Правила соответствия**:

- Точное соответствие: `@sdk.adapter.on("message")` соответствует только событию `message`
- Шаблон: `@sdk.adapter.on("*")` соответствует всем событиям
- Фильтрация платформы: `platform="myplatform"` распределяет события только указанной платформы

### Middleware

#### Добавление middleware

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """Middleware для ведения журнала"""
    print(f"Обработка события: {data.get('type')}")
    return data  # Необходимо вернуть данные

@sdk.adapter.middleware
async def filter_middleware(data):
    """Middleware для фильтрации событий"""
    # Фильтрация ненужных событий
    if data.get("type") == "notice":
        return None  # При возврате None цепочка middleware игнорирует это возвращаемое значение и передает исходные данные
    return data  # Необходимо вернуть данные для продолжения передачи
```

#### Порядок выполнения middleware

Middleware выполняются в порядке регистрации, срабатывают в порядке обратном регистрации (последний зарегистрированный выполняется первым).

> **Важно** : Если middleware возвращает `None` (например, забыта строка `return data`), фреймворк игнорирует это возвращаемое значение и передает исходные данные, одновременно выводя предупреждение уровня warning. Это гарантирует, что ошибка одного middleware не приведет к прерыванию всей цепочки событий.

```python
# Порядок регистрации
sdk.adapter.middleware(middleware1)  # Выполнится последним
sdk.adapter.middleware(middleware2)  # Выполнится средним
sdk.adapter.middleware(middleware3)  # Выполнится первым

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
    """Конфигурация адаптера (после объявления фреймворк управляет автоматически)"""
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
    
    # Переопределение __init__ не требуется, фреймворк обрабатывает автоматически:
    # - self.sdk, self.logger
    # - self.cfg (экземпляр конфигурации с типобезопасностью, чтение в реальном времени)
    # - self.Send, self.Request
    
    async def start(self):
        """Запуск адаптера (необходимо реализовать)"""
        cfg = self.cfg  # Автоматически загруженная конфигурация с типобезопасностью
        pass
    
    async def shutdown(self):
        """Остановка адаптера (необходимо реализовать)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Вызов платформенного API (необходимо реализовать)"""
        pass
```

### Управление конфигурацией

Фреймворк предоставляет декларативное управление конфигурацией: с помощью dataclass определяется структура конфигурации, а фреймворк автоматически обрабатывает загрузку, проверку и генерацию шаблонов.

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
        cfg = self.cfg  # Типобезопасно, чтение в реальном времени
        if not cfg.token:
            raise ValueError("Токен не настроен")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Конфигурация нескольких аккаунтов

Базовый класс `BotAccountConfig` предоставляет поля `enabled` и `name`. Большинство адаптеров могут автоматически получить bot_id из протокола платформы или ответа о входе в систему и внедрить его в конфигурацию аккаунта при преобразовании событий.：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

# Большинство адаптеров: bot_id автоматически получается во время выполнения, без настройки
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# Если во время входа невозможно получить bot_id, можно позволить пользователю заполнить его в конфигурации
@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": {"i18n": "yunhu.bot_id", "default": "Идентификатор бота"},
        "required": True,
    })
    token: str = field(default="", metadata={
        "description": {"i18n": "yunhu.token", "default": "Token"},
        "required": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            user_id = await self._login(name, account)
            await self.emit_meta("connect", user_id)
```

####约定 metadata

Поле metadata служит одновременно для генерации комментариев TOML и рендеринга формы WebUI:

```python
metadata = {
    "description": str | dict,  # Описание поля (поддерживает i18n)
    "required": bool,         # Обязательно ли (проверка + метка обязательности в WebUI)
    "secret": bool,           # Чувствительно ли (в WebUI отображается как ***, маскируется в логах)
    "ui": {                   # Настройка элемента WebUI (старое имя "webui" все еще совместимо)
        "widget": str,        # Тип элемента: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Группа: "basic" | "advanced" | "connection" и т.д.
        "order": int,         # Вес порядка (чем меньше, тем ближе к началу)
        "options": list,      # Варианты для элемента select [{label, value}], label поддерживает i18n
        "placeholder": str | dict,  # Заполнитель поля ввода (поддерживает i18n)
    },
    "extra": dict,            # Дополнительные поля расширения (прозрачны в schema)
}
```

Все текстовые поля, видимые пользователю, поддерживают i18n, формат унифицирован как `{"i18n": "ключ", "default": "текст"}`,
простые строки передаются как есть (обратная совместимость). Поддерживаемые поля i18n:

| Поле | Позиция | Описание |
|------|------|------|
| `description` | field metadata | Описание поля |
| `options[].label` | `ui.options` | Метка варианта select |
| `placeholder` | `ui.placeholder` | Заполнитель поля ввода |
| `group_labels` | `_schema_meta` | Название группы (заголовок раздела Dashboard) |

При использовании i18n необходимо заранее зарегистрировать ключи перевода в системе i18n (см. [i18n документация](../../advanced/i18n.md#конфигурация полей многоязычности) для деталей).

**Примеры description / placeholder / options label**:

```python
token: str = field(
    default="",
    metadata={
        "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
        "ui": {
            "widget": "text",
            "placeholder": {"i18n": "my_adapter.token.ph", "default": "Введите Token"},
        },
    },
)
mode: str = field(
    default="a",
    metadata={
        "description": {"i18n": "my_adapter.mode", "default": "Режим"},
        "ui": {
            "widget": "select",
            "options": [
                {"label": {"i18n": "my_adapter.mode.a", "default": "Вариант A"}, "value": "a"},
                {"label": "Простая строка", "value": "b"},  # Простая строка передается как есть
            ],
        },
    },
)
```

**Пример group_labels** (объявляется после определения класса конфигурации):

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "Основные настройки"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "Расширенные настройки"},
    }
}
```

`resolve_config_schema()` фреймворка автоматически разрешает ключи i18n для всех вышеперечисленных полей в зависимости от текущего языка;
`get_config_schema()` передает словарь i18n как есть, разрешение выполняется на стороне фронтенда.

#### Разбор аккаунтов

Адаптеры с несколькими аккаунтами могут использовать `_resolve_account()` для автоматического разрешения целевого аккаунта:

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: имя аккаунта, account: экземпляр конфигурации
```

Стратегия разрешения: соответствие имени аккаунта → соответствие поля `bot_id` → соответствие другим полям str → первый включенный аккаунт.

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

В `BaseAdapter.__init__(self, sdk=None)` фреймворк автоматически выполняет следующие действия:

1. **Ссылка на SDK**: Установка `self.sdk`, `self.logger`
2. **Фабрика Send/Request**: Создание `self.Send` и `self.Request`
3. **Шаблон конфигурации**: Если объявлен `ConfigClass`, автоматически генерируется шаблон конфигурации по умолчанию (при первом использовании)
4. **Шаблон аккаунта**: Если объявлен `AccountConfigClass`, автоматически генерируется шаблон аккаунта по умолчанию (при первом использовании)

Конфигурация считывается в реальном времени через `self.cfg` / `self.accounts` (при каждом обращении читаются последние значения из хранилища конфигурации). `self.config` как совместимый псевдоним `self.cfg` все еще может использоваться.

Переопределять `__init__` не требуется для большинства адаптеров. При необходимости пользовательской инициализации:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Передача sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send DSL для отправки сообщений

### Иерархия наследования

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Вложенный класс Send, наследуется от BaseAdapter.Send"""
        pass
```

### Доступные свойства

При вызове класса `Send` автоматически устанавливаются следующие свойства:

| Свойство | Описание | Способ установки |
|-----|------|---------|
| `_target_id` | ID цели | `To(id)` или `To(type, id)` |
| `_target_type` | Тип цели | `To(type, id)` |
| `_target_to` | Упрощенный ID цели | `To(id)` |
| `_account_id` | ID отправляющего аккаунта | `Using(account_id)` |
| `_adapter` | Экземпляр адаптера | Автоматически |
| `_at_user_ids` | Список @пользователей | `At(user_id)` |
| `_reply_message_id` | ID сообщения для ответа | `Reply(message_id)` |
| `_at_all` | Использовать @всем | `AtAll()` |

> **Рекомендация**: Используйте свойство `self.send_context` для одновременного получения `target_type`, `target_id`, `account_id`, что clearer, чем прямой доступ к переменным экземпляра.

### Вспомогательные методы фреймворка

| Метод/свойство | Описание |
|-----------|------|
| `self._apply_modifiers(message)` | Слияние состояний модификаторов At/AtAll/Reply в список сегментов сообщения |
| `self.send_context` | Возврат словаря `{target_type, target_id, account_id}` |

### Основные методы

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
Исходное событие платформы
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
    "time": 1234567890,           # 10-битный временной штамп Unix
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
        
        # Преобразование временного штампа
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

## Управление подключениями

### WebSocket соединение

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """Регистрация WebSocket маршрута"""
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
        """Обработчик запроса WebHook"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> **Запрос информации о маршрутах**: Маршруты, зарегистрированные адаптером (HTTP, WebSocket, SSE), можно получить через `sdk.adapter.get_connection_info(platform)` и `sdk.router.get_module_urls(module_name)` для получения полного адреса подключения (включая `base_url` + путь). См. подробности в [Введение в разработку адаптера - Информация о подключении и обнаружение маршрутов](getting-started.md#9-информация-о-подключении-и-обнаружение-маршрутов) и [Поддержка SSE](getting-started.md#10-sse-server-sent-events-поддержка).

## Стандарт ответа API

Фреймворк предоставляет методы `make_response()` и `make_error()` для построения стандартизированных ответов, без необходимости вручную собирать словарь ответа.

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

### Ручное построение ответа (старый способ также совместим)

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

После объявления класса конфигурации с помощью `AccountConfigClass`, фреймворк автоматически управляет загрузкой, проверкой и генерацией шаблонов для нескольких аккаунтов:

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
        # Использование полей account.token, account.bot_id и т.д.
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

# Через self.user_id в событии (рекомендуется, наиболее универсально)
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# Через имя аккаунта
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Связь self.user_id и Using

Механизм отклика на события фреймворка автоматически извлекает `account_id` (приоритет) или `user_id` из поля `self` события и передает его как параметр `Using`. Разработчики адаптеров должны обеспечить, чтобы значение `self.user_id` в Converter корректно соответствовало тому, с чем может сопоставить `_resolve_account()`.

**Внутреннее поведение фреймворка** (`Event._get_adapter_and_target`):

```python
# Логика извлечения bot_id фреймворком
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Вызов Using только если bot_id не пуст
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Ключевой момент** : Даже если адаптер использует только одну конфигурацию Bot, при условии, что Converter корректно устанавливает `self.user_id`, фреймворк передаст его как параметр `Using`. Адаптер должен убедиться, что `self.user_id` соответствует идентификаторному полю в `AccountConfigClass` (такому как `bot_id`), чтобы `_resolve_account()` мог сопоставить правильный аккаунт. Если `self.user_id` пуст, фреймворк не будет вызывать `Using`, в этом случае `account_id`, полученный `call_api`, будет `None`, а `_resolve_account(None)` вернет первый включенный аккаунт.

## Обработка ошибок

### Повторное подключение

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
                    self.logger.warning(f"Подключение не удалось, повторная попытка через {wait_time} сек")
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
        self.logger.error(f"Запрос превышает тайм-аут: {endpoint}")
        return self._error_response("Запрос превышает тайм-аут", 32000)
    except ClientError as e:
        self.logger.error(f"Сетевая ошибка: {e}")
        return self._error_response("Не удалось выполнить сетевой запрос", 33000)
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}")
        return self._error_response(str(e), 34000)
```

> **Обратная совместимость** : Старый код адаптера, использующий `aiohttp.ClientSession` напрямую, не затронут, по-прежнему можно перехватывать `aiohttp.ClientError`. Два способа могут сосуществовать. Рекомендуется для нового кода использовать `sdk.client` + систему исключений ErisPulse.

## Управление состоянием бота

Внутри `AdapterManager` встроена система отслеживания состояния бота, которая автоматически поддерживает онлайн-статус, время активности и метаданные всех зарегистрированных ботов.

### Механизм автоматического обнаружения

Когда адаптер отправляет событие через `adapter.emit()`, фреймворк автоматически проверяет поле `self` в событии:

- **Событие meta**: Выполняются соответствующие действия на основе `detail_type` (регистрация/отметка оффлайн при разъединении/обновление времени активности для heartbeat)
- **Обычное событие** (message/notice/request): Автоматическое обнаружение бота и обновление времени активности

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

### Типы событий meta

| `detail_type` | Описание | Поведение фреймворка |
|---|---|---|
| `connect` | Подключение бота | Регистрация бота и отправка события жизненного цикла `adapter.bot.online` |
| `disconnect` | Отключение бота | Пометка бота как офлайн и отправка события жизненного цикла `adapter.bot.offline` |
| `heartbeat` | Сердцебиение бота | Обновление времени активности бота и метаданных |

### Отправка событий meta адаптером

Использование `emit_meta()` позволяет отправить событие meta одной строкой:

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # Отправка события connect одной строкой
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="Мой робот")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

Поддерживается и ручное построение (старый способ также совместим):

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
| `nickname` | Ник бота |
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

# Перечисление ботов указанной платформы
platform_bots = sdk.adapter.list_bots("myplatform")

# Проверка, онлайн ли бот
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Получение полной сводки статуса (подходит для отображения в WebUI)
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
    sdk.logger.info(f"Бот оффлайн: {platform}/{bot_id}")
```

## Связанные документы

- [Введение в разработку адаптера](getting-started.md) - Создание первого адаптера
- [Подробно о SendDSL](send-dsl.md) - Изучение отправки сообщений
- [Рекомендации по разработке адаптеров](best-practices.md) - Разработка высококачественных адаптеров