# Основные концепции адаптера

Понимание основных концепций адаптера ErisPulse является основой для разработки адаптеров.

## Архитектура адаптера

### Соотношение компонентов

```
Прямое преобразование (направление получения)                           Обратное преобразование (направление отправки)
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ Платформа: собственные события     │                        │ Модуль: построение сообщения     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ Адаптер (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (конвертер событий)    │──→│ │              │ │   │ (точка входа обратного преобразования)   │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Вызов платформенного API    │
                       │ Стандартное событие OneBot12 │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Стандартный формат ответа     │
                       │ Система событий         │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ Модуль (обработка событий)  │
                       └──────────────────┘
```

**Основная симметрия**:
- **Прямое преобразование** (Converter): платформа: собственные события → стандартное событие OneBot12, исходные данные сохраняются в `{platform}_raw`
- **Обратное преобразование** (Raw_ob12): OneBot12 сообщение → вызов платформенного API, возвращается стандартный формат ответа

## AdapterManager - менеджер адаптеров

`AdapterManager` является основным компонентом системы адаптеров ErisPulse, отвечающим за управление регистрацией, запуском, остановкой и рассылкой событий всех платформенных адаптеров.

### Основные функции

- **Регистрация адаптеров**: регистрация и управление несколькими платформенными адаптерами
- **Управление жизненным циклом**: контроль запуска и остановки адаптеров
- **Рассылка событий**: рассылка стандартных событий OneBot12 и платформенных собственных событий
- **Управление конфигурацией**: управление состоянием включения/отключения адаптеров
- **Поддержка промежуточных обработчиков**: поддержка промежуточных обработчиков событий OneBot12

### Основное использование

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
# Или через доступ к атрибуту
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
3. Параллельный запуск каждого адаптера
4. Если запуск не удался, автоматическая повторная попытка (стратегия экспоненциального отступа)
5. После успешного запуска отправка события `adapter.status.change` (started)

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
2. Вызов метода `shutdown()` у всех адаптеров
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

#### Список платформ

```python
# Получение списка всех зарегистрированных платформ
platforms = sdk.adapter.list_registered()

# Получение списка всех платформ и их состояний
status_dict = sdk.adapter.list_items()
# Возвращает: {"platform1": true, "platform2": false, ...}

# Получение списка включенных платформ
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### Слушатели событий

#### Стандартные события OneBot12

```python
from ErisPulse import sdk

# Слушание всех стандартных событий сообщений
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Получено OneBot12 сообщение: {data}")

# Слушание стандартных событий сообщений для определенной платформы
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"Получено сообщение myplatform: {data})

# Слушание всех событий
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"Получено событие: {data.get('type')}")
```

#### Платформенные собственные события

```python
# Слушание собственных событий для определенной платформы
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Получено собственное событие: {data}")

# Слушание собственных событий для всех платформ (символ подстановки)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Получено собственное событие: {data}")
```

#### Механизм рассылки событий

При вызове `adapter.emit(event_data)`:

1. **Обработка промежуточными обработчиками**: сначала выполняются все промежуточные обработчики OneBot12
2. **Рассылка стандартных событий**: рассылка к соответствующим обработчикам стандартных событий OneBot12
3. **Рассылка собственных событий**: если есть исходные данные, рассылка к обработчикам собственных событий

**Правила сопоставления**:

- Точное совпадение: `@sdk.adapter.on("message")` только для события `message`
- Символ подстановки: `@sdk.adapter.on("*")` для всех событий
- Фильтрация по платформе: `platform="myplatform"` только для событий указанной платформы

### Промежуточные обработчики

#### Добавление промежуточного обработчика

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """Промежуточный обработчик для логирования"""
    print(f"Обработка события: {data.get('type')}")
    return data  # Обязательно вернуть данные

@sdk.adapter.middleware
async def filter_middleware(data):
    """Промежуточный обработчик для фильтрации событий"""
    # Фильтрация ненужных событий
    if data.get("type") == "notice":
        return None  # Если возвращается None, промежуточный обработчик пропустит это значение, сохранив исходные данные для продолжения передачи
    return data  # Обязательно вернуть данные для продолжения передачи
```

#### Порядок выполнения промежуточных обработчиков

Промежуточные обработчики выполняются в порядке их регистрации, последние зарегистрированные обработчики выполняются первыми.

> **Важно**: если промежуточный обработчик возвращает `None` (например, забыли `return data`), фреймворк проигнорирует это возвращаемое значение, сохранит исходные данные и продолжит передачу, одновременно выведя предупреждение уровня warning. Это гарантирует, что ошибка в одном промежуточном обработчике не приведет к прерыванию всей цепочки событий.

```python
# Порядок регистрации
sdk.adapter.middleware(middleware1)  # Выполняется последним
sdk.adapter.middleware(middleware2)  # Выполняется посередине
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

#### Доступ к атрибуту

```python
# Доступ через имя атрибута (без учета регистра)
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter - базовый класс

### Основная структура

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """Конфигурация адаптера (объявляется, фреймворк автоматически управляет)"""
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Токен бота"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig  # Объявление класса конфигурации
    
    # Не нужно переопределять __init__, фреймворк автоматически обрабатывает:
    # - self.sdk, self.logger
    # - self.cfg (типобезопасный экземпляр конфигурации, считывается в реальном времени)
    # - self.Send, self.Request
    
    async def start(self):
        """Запуск адаптера (обязательно реализовать)"""
        cfg = self.cfg  # Автоматически загруженная типобезопасная конфигурация
        pass
    
    async def shutdown(self):
        """Остановка адаптера (обязательно реализовать)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Вызов платформенного API (обязательно реализовать)"""
        pass
```

### Управление конфигурацией

Фреймворк предоставляет декларативное управление конфигурацией, определяя структуру конфигурации с помощью dataclass, фреймворк автоматически обрабатывает загрузку, проверку и генерацию шаблонов.

#### Конфигурация для одного аккаунта

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BaseConfig

@dataclass
class TelegramConfig(BaseConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "telegram.token", "default": "Токен бота"},
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
        cfg = self.cfg  # Типобезопасно, считывается в реальном времени
        if not cfg.token:
            raise ValueError("Токен не настроен")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Конфигурация для нескольких аккаунтов

Базовый класс `BotAccountConfig` предоставляет поля `enabled` и `name`. Большинство адаптеров могут автоматически получать bot_id из платформенного протокола или ответа на вход, вставляя его в конфигурацию аккаунта во время преобразования событий.:

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

# Для большинства адаптеров: bot_id получается во время выполнения, не нужно настраивать
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Токен"},
        "required": True,
    })

# Если при входе невозможно получить bot_id, можно позволить пользователю ввести его в конфигурации
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

#### Соглашение о metadata

Поле metadata служит как для генерации комментариев TOML, так и для рендеринга веб-интерфейса формы:

```python
metadata = {
    "description": str | dict,  # Описание поля (поддержка i18n)
    "required": bool,         # Обязательно ли поле (проверка + метка обязательного поля в веб-интерфейсе)
    "secret": bool,           # Является ли поле конфиденциальным (отображается как *** в веб-интерфейсе, маскируется в логах)
    "ui": {                   # Конфигурация элемента управления веб-интерфейсом (старое имя "webui" по-прежнему совместимо)
        "widget": str,        # Тип элемента управления: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Группа: "basic" | "advanced" | "connection" и т.д.
        "order": int,         # Вес сортировки (чем меньше, тем выше)
        "options": list,      # Варианты для элемента select [{label, value}], label поддерживает i18n
        "placeholder": str | dict,  # Подсказка для поля ввода (поддержка i18n)
    },
    "extra": dict,            # Дополнительные расширенные поля (прозрачно передаются в схему)
}
```

Все пользовательские видимые текстовые поля поддерживают i18n, используя единый формат `{"i18n": "key", "default": "текст"}`,
чистые строки передаются без изменений (для обратной совместимости). Поддерживаемые поля i18n:

| Поле | Позиция | Описание |
|------|------|------|
| `description` | metadata поля | Описание поля |
| `options[].label` | `ui.options` | Метка опций элемента select |
| `placeholder` | `ui.placeholder` | Подсказка для поля ввода |
| `group_labels` | `_schema_meta` | Название отображаемой группы (заголовок раздела панели управления) |

При использовании i18n необходимо заранее зарегистрировать ключи перевода в систему i18n (см. [документацию по i18n](../../advanced/i18n.md#конфигурационные-поля-многоязычность)).

**Примеры `description` / `placeholder` / `options label`:**

```python
token: str = field(
    default="",
    metadata={
        "description": {"i18n": "my_adapter.token", "default": "Токен бота"},
        "ui": {
            "widget": "text",
            "placeholder": {"i18n": "my_adapter.token.ph", "default": "Введите токен"},
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
                {"label": "Чистая строка метки", "value": "b"},  # Чистая строка передается без изменений
            ],
        },
    },
)
```

**Пример `group_labels`** (объявляется после определения класса конфигурации):

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "Основные настройки"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "Дополнительные настройки"},
    }
}
```

Метод `resolve_config_schema()` фреймворка автоматически разрешает все вышеуказанные поля i18n в зависимости от текущего языка;
`get_config_schema()` прозрачно передает словарь i18n, и интерфейс будет сам разбирать его.

#### Разрешение аккаунтов

Многоаккаунтный адаптер может использовать `_resolve_account()` для автоматического разрешения целевого аккаунта:

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: имя аккаунта, account: экземпляр конфигурации
```

Стратегия разрешения: совпадение имени аккаунта → совпадение поля `bot_id` → совпадение других строковых полей → первый включенный аккаунт.

#### Горячая перезагрузка конфигурации

Подклассы могут переопределить `on_config_update()` для реакции на изменения конфигурации:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Токен обновлен, переподключение")
```

### Процесс инициализации

Фреймворк автоматически выполняет следующие действия в `BaseAdapter.__init__(self, sdk=None)`:

1. **Ссылка на SDK**: установка `self.sdk`, `self.logger`
2. **Фабрика Send/Request**: создание `self.Send` и `self.Request`
3. **Шаблон конфигурации**: если объявлен `ConfigClass`, автоматически генерируется шаблон конфигурации (впервые)
4. **Шаблон аккаунта**: если объявлен `AccountConfigClass`, автоматически генерируется шаблон аккаунта (впервые)

Конфигурация читается в реальном времени через `self.cfg` / `self.accounts` (каждый раз при доступе читается последнее значение из хранилища конфигурации). `self.config` как совместимый псевдоним `self.cfg` по-прежнему доступен.

Большинству адаптеров не нужно переопределять `__init__`. Если требуется пользовательская инициализация:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # передать sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## DSL для отправки сообщений Send

### Наследование

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Вложенный класс Send, наследующий BaseAdapter.Send"""
        pass
```

### Доступные свойства

Класс `Send` автоматически устанавливает следующие свойства при вызове:

| Свойство | Описание | Способ установки |
|-----|------|---------|
| `_target_id` | Идентификатор цели | `To(id)` или `To(type, id)` |
| `_target_type` | Тип цели | `To(type, id)` |
| `_target_to` | Упрощенный идентификатор цели | `To(id)` |
| `_account_id` | Идентификатор отправляющего аккаунта | `Using(account_id)` |
| `_adapter` | Экземпляр адаптера | Автоматически установлен |
| `_at_user_ids` | Список @ пользователей | `At(user_id)` |
| `_reply_message_id` | Идентификатор сообщения для ответа | `Reply(message_id)` |
| `_at_all` | Отправлять @ всем | `AtAll()` |

> **Рекомендуется**: использовать свойство `self.send_context` для получения `target_type`, `target_id`, `account_id` за один раз, это более ясно, чем прямой доступ к экземплярным переменным.

### Вспомогательные методы фреймворка

| Метод/свойство | Описание |
|-----------|------|
| `self._apply_modifiers(message)` | Объединить состояние модификаторов At/AtAll/Reply в список сообщений |
| `self.send_context` | Возвращает словарь `{target_type, target_id, account_id}` |

### Основные методы

Адаптер должен реализовать только `Raw_ob12`, стандартные методы (Text/Image/Voice/Video/File) уже унаследованы от базового класса SendDSL и по умолчанию делегированы ему:

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Обязательно реализовать: OneBot12 сообщение → платформенный API"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File унаследованы от базового класса, автоматически делегированы Raw_ob12, не нужно повторно реализовывать
    # Если нужны платформенные специфичные логики, можно переопределить отдельные методы:
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
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

## Конвертер событий

### Процесс преобразования

```
Платформа: исходное событие
    ↓
Converter.convert()
    ↓
OneBot12 стандартное событие
```

### Обязательные поля

Все преобразованные события должны содержать:

```python
{
    "id": "Уникальный идентификатор события",
    "time": 1234567890,           # 10-значный Unix timestamp
    "type": "message/notice/request/meta",
    "detail_type": "Детальный тип события",
    "platform": "Название платформы",
    "self": {
        "platform": "Название платформы",
        "user_id": "ID бота"     # Должен совпадать с bot_id
    },
    "{platform}_raw": {...},       # Исходные данные (обязательно)
    "{platform}_raw_type": "..."    # Тип исходных данных (обязательно)
}
```

### Пример конвертера

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование платформенного исходного события в стандартный формат OneBot12"""
        if not isinstance(raw_event, dict):
            return None
        
        # Генерация уникального идентификатора события
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
        
        # Создание стандартного события
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

### WebSocket подключение

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
            self.logger.info("Соединение разорвано")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket) -> bool:
        """Аутентификация WebSocket"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook подключение

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """Регистрация WebHook маршрута"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """Обработчик WebHook запроса"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> **Информация о маршрутах**: маршруты, зарегистрированные адаптером (HTTP, WebSocket, SSE), можно получить через `sdk.adapter.get_connection_info(platform)` и `sdk.router.get_module_urls(module_name)`, чтобы узнать полный адрес подключения (включая `base_url` + путь). Подробнее см. [Введение в разработку адаптеров - Информация о подключении и обнаружение маршрутов](getting-started.md#9-информация-о-подключении-и-обнаружение-маршрутов) и [Поддержка SSE](getting-started.md#10-sse-server-sent-events-поддержка).

## Стандартный формат ответа API

Фреймворк предоставляет методы `make_response()` и `make_error()` для построения стандартизированных ответов, без необходимости вручную создавать словарь ответа.

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

## Поддержка нескольких аккаунтов

### Декларативная конфигурация (рекомендуется)

После объявления `AccountConfigClass` фреймворк автоматически управляет загрузкой, проверкой и генерацией шаблонов для нескольких аккаунтов:

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
        # Использовать account.token, account.bot_id и т.д.
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

### Отправка с указанием аккаунта

```python
# Использование метода Using для указания аккаунта
my_adapter = adapter.get("myplatform")

# Через self.user_id в событии (рекомендуется, наиболее универсально)
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# Через имя аккаунта
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Отношение self.user_id и Using

Механизм ответа событий фреймворка автоматически извлекает `account_id` (приоритет) или `user_id` из поля `self` события, передавая его как параметр `Using`. Разработчикам адаптеров необходимо убедиться, что Converter правильно устанавливает `self.user_id`, чтобы `_resolve_account()` мог корректно сопоставить правильный аккаунт.

**Внутреннее поведение фреймворка** (`Event._get_adapter_and_target`):

```python
# Логика извлечения bot_id фреймворком
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Вызов Using только если bot_id не пуст
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Ключевой момент**: даже если адаптер использует только одну конфигурацию бота, если Converter правильно устанавливает `self.user_id`, фреймворк передаст его как параметр `Using`. Разработчикам адаптеров необходимо убедиться, что `self.user_id` совпадает с идентификатором поля в `AccountConfigClass` (например, `bot_id`), чтобы `_resolve_account()` мог сопоставить правильный аккаунт. Если `self.user_id` пуст, фреймворк не вызовет `Using`, и `call_api` получит `account_id` как `None`, `_resolve_account(None)` вернет первый включенный аккаунт.

## Обработка ошибок

### Переподключение

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
                    self.logger.warning(f"Подключение не удалось, повтор через {wait_time} секунд")
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
        self.logger.error(f"Сетевая ошибка: {e}")
        return self._error_response("Ошибка сети", 33000)
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}")
        return self._error_response(str(e), 34000)
```

> **Обратная совместимость**: код старых адаптеров, использующих `aiohttp.ClientSession`, не затронут, по-прежнему можно перехватывать `aiohttp.ClientError`. Оба способа могут сосуществовать. Рекомендуется для нового кода использовать `sdk.client` + систему исключений ErisPulse.

## Управление статусом бота

`AdapterManager` встроен в систему отслеживания статуса бота, автоматически поддерживает онлайн-статус, время активности и метаинформацию всех зарегистрированных ботов.

### Автоматическая система обнаружения

Когда адаптер отправляет событие через `adapter.emit()`, фреймворк автоматически проверяет поле `self` в событии:

- **Meta события**: в зависимости от `detail_type` выполняются соответствующие действия (connect регистрирует / отмечает отключение как оффлайн / heartbeat обновляет время активности)
- **Обычные события** (message/notice/request): автоматически обнаруживаются боты и обновляется время активности

```python
# Все события с полем self запускают автоматическую систему обнаружения
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Бот "bot123" автоматически зарегистрирован (если это первый раз) и обновлено время активности
```

### Типы мета-событий

| `detail_type` | Описание | Поведение фреймворка |
|---|---|---|
| `connect` | Бот подключился | Регистрация бота и отправка события жизненного цикла `adapter.bot.online` |
| `disconnect` | Бот отключился | Отметка бота как оффлайн и отправка события жизненного цикла `adapter.bot.offline` |
| `heartbeat` | Бот отправил heartbeat | Обновление времени активности и метаинформации бота |

### Отправка мета-событий адаптером

Использование `emit_meta()` для отправки мета-событий:

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # Одной строкой отправить событие connect
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="Мой бот")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

Также поддерживается ручное создание (старый способ по-прежнему совместим):

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### Расширенная информация в поле self

Поле `self` помимо обязательных `platform` и `user_id` поддерживает следующие дополнительные поля:

| Поле | Описание |
|---|---|
| `user_name` | Имя пользователя бота |
| `nickname` | Никнейм бота |
| `avatar` | URL аватара бота |
| `account_id` | Идентификатор аккаунта |

### Запрос статуса бота

```python
from ErisPulse import sdk

# Получение информации о боте
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# Получение списка всех ботов
all_bots = sdk.adapter.list_bots()

# Получение списка ботов указанной платформы
platform_bots = sdk.adapter.list_bots("myplatform")

# Проверка, онлайн ли бот
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Получение полного сводного статуса (подходит для отображения в веб-интерфейсе)
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Наблюдение за жизненным циклом бота

```python
from ErisPulse import sdk

@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Бот вошел в онлайн: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Бот вышел из онлайн: {platform}/{bot_id}")
```

## Связанная документация

- [Введение в разработку адаптеров](getting-started.md) - Создание первого адаптера
- [Подробное руководство по SendDSL](send-dsl.md) - Изучение отправки сообщений
- [Лучшие практики разработки адаптеров](best-practices.md) - Создание качественных адаптеров