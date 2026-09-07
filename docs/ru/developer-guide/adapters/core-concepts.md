# Основные понятия адаптера

Понимание основных понятий адаптера ErisPulse является основой для разработки адаптера.

## Архитектура адаптера

### Отношения между компонентами

```
Прямое преобразование (направление получения)             Обратное преобразование (направление отправки)
─────────────────────────────────────────────────────   ─────────────────────────────────────────────────────
                                                       
┌────────────────────────────┐                          ┌────────────────────────────┐
│ События платформы          │                          │ Сообщения, сформированные модулем │
│ (native events)            │                          └────────────┬─────────────┘
└────────────┬─────────────┘                                             │
             │                                                             │
             ↓                                                             ↓
┌────────────────────────────┐   ┌────────────────────────────┐   ┌────────────────────────────┐
│                            │   │ Адаптер (MyAdapter)        │   │                            │
│ Преобразователь (Converter) │   │ ┌──────────────────────┐ │   │ Send.Raw_ob12()            │
│ (event converter)          │───▶ │ │                      │ │   │ (точка входа для обратного │
│                            │   │ │                      │ │   │ преобразования)            │
└────────────────────────────┘   │ └──────────────────────┘ │   │                            │
                                 └──────────────────────────┘   └────────────┬─────────────┘
                                                              │
                                                              ↓
                                                      ┌────────────────────────────┐
                                                      │ Вызов API платформы        │
                                                      └────────────┬─────────────┘
                                                                   │
                                                                   ↓
                                                      ┌────────────────────────────┐
                                                      │ Стандартный формат ответа   │
                                                      └────────────┬─────────────┘
                                                                   │
                                                                   ↓
                                                      ┌────────────────────────────┐
                                                      │ Система событий             │
                                                      └────────────┬─────────────┘
                                                                   │
                                                                   ↓
                                                      ┌────────────────────────────┐
                                                      │ Модуль (обработка событий)  │
                                                      └────────────────────────────┘
```

**Основная симметрия**:
- **Прямое преобразование** (Converter): События платформы → События стандарта OneBot12, исходные данные сохраняются в `{platform}_raw`
- **Обратное преобразование** (Raw_ob12): Сегменты сообщений OneBot12 → Вызов API платформы, возвращается стандартный формат ответа

## AdapterManager адаптер-менеджер

`AdapterManager` — основной компонент системы адаптеров ErisPulse, отвечающий за управление регистрацией, запуском, остановкой и распределением событий для всех адаптеров платформ.

### Основные функции

- **Регистрация адаптеров**: Регистрация и управление несколькими адаптерами платформ.
- **Управление жизненным циклом**: Контроль запуска и остановки адаптеров.
- **Распределение событий**: Распределение событий стандарта OneBot12 и событий, специфичных для платформы.
- **Управление конфигурацией**: Управление включением/выключением адаптеров.
- **Поддержка промежуточного ПО (middleware)**: Поддержка промежуточного ПО для событий стандарта OneBot12.

### Основное использование

```python
from ErisPulse import sdk

# Регистрация адаптера (обычно выполняется автоматически загрузчиком)
sdk.adapter.register("myplatform", MyPlatformAdapter)

# Запуск всех адаптеров
await sdk.adapter.startup()

# Запуск указанных адаптеров
await sdk.adapter.startup(["myplatform"])
# Запуск всех адаптеров
await sdk.adapter.startup()

# Получение экземпляра адаптера
my_adapter = sdk.adapter.get("myplatform")
# Или доступ через атрибут
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

1. Отправка события жизненного цикла `adapter.start`.
2. Отправка события `adapter.status.change` (starting).
3. Параллельный запуск каждого адаптера.
4. При неудаче автоматическая повторная попытка (стратегия экспоненциальной задержки).
5. После успешного запуска отправка события `adapter.status.change` (started).

**Механизм повторных попыток:**

- Первые 4 попытки: 60 секунд, 10 минут, 30 минут, 60 минут.
- С пятой попытки и далее: фиксированная задержка в 3 часа.

#### Остановка адаптера

```python
# Остановка всех адаптеров
await sdk.adapter.shutdown()
```

**Процесс остановки:**

1. Отправка события жизненного цикла `adapter.stop`.
2. Вызов метода `shutdown()` для всех адаптеров.
3. Остановка сервера маршрутизации.
4. Очистка обработчиков событий.
5. Отправка события жизненного цикла `adapter.stopped`.

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

### Обработка событий

#### Стандартные события OneBot12

```python
from ErisPulse import sdk

# Обработка всех стандартных событий сообщений OneBot12
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Получено событие OneBot12: {data}")

# Обработка стандартных событий сообщений для определенной платформы
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"Получено событие myplatform: {data}")

# Обработка всех событий
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"Получено событие: {data.get('type')}")
```

#### События, специфичные для платформы

```python
# Обработка событий, специфичных для платформы
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Получено событие: {data}")

# Обработка всех событий, специфичных для платформы (с использованием шаблона)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Получено событие: {data}")
```

#### Механизм распределения событий

При вызове `adapter.emit(event_data)`:

1. **Обработка промежуточного ПО (middleware)**: Сначала выполняются все промежуточные обработчики OneBot12.
2. **Распределение стандартных событий**: Распределение событий по соответствующим обработчикам OneBot12.
3. **Распределение событий, специфичных для платформы**: Если есть исходные данные, они распределяются по обработчикам событий, специфичных для платформы.

**Правила сопоставления:**

- Точное сопоставление: `@sdk.adapter.on("message")` сопоставляет только событие `message`.
- Шаблон: `@sdk.adapter.on("*")` сопоставляет все события.
- Фильтрация по платформе: `platform="myplatform"` сопоставляет события только для указанной платформы.

### Промежуточное ПО (Middleware)

#### Добавление промежуточного ПО

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """Промежуточное ПО для логирования"""
    print(f"Обработка события: {data.get('type')}")
    return data  # Должно возвращать данные

@sdk.adapter.middleware
async def filter_middleware(data):
    """Промежуточное ПО для фильтрации событий"""
    # Фильтрация ненужных событий
    if data.get("type") == "notice":
        return None  # При возврате None промежуточное ПО игнорирует результат и сохраняет исходные данные для передачи
    return data  # Должно возвращать данные для продолжения передачи
```

#### Порядок выполнения промежуточного ПО

Промежуточное ПО выполняется в порядке регистрации, последнее зарегистрированное промежуточное ПО выполняется первым.

> **Важно**: Если промежуточное ПО возвращает `None` (например, забыто `return data`), фреймворк игнорирует результат и сохраняет исходные данные для передачи, при этом выводится предупреждение уровня warning. Это гарантирует, что ошибка одного промежуточного ПО не приведет к остановке всей цепочки событий.

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

#### Доступ через атрибуты

```python
# Доступ по имени атрибута (без учета регистра)
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## Базовый класс BaseAdapter

### Основная структура

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """Конфигурация адаптера (объявлена, управление автоматическое)"""
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
    # - self.cfg (типобезопасный экземпляр конфигурации, актуальный)
    # - self.Send, self.Request
    
    async def start(self):
        """Запуск адаптера (обязательно реализовать)"""
        cfg = self.cfg  # Автоматически загруженная, типобезопасная конфигурация
        pass
    
    async def shutdown(self):
        """Остановка адаптера (обязательно реализовать)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Вызов API платформы (обязательно реализовать)"""
        pass
```

### Управление конфигурацией

Фреймворк предоставляет декларативное управление конфигурацией, определяя структуру конфигурации через dataclass, фреймворк автоматически обрабатывает загрузку, проверку и генерацию шаблонов.

#### Конфигурация одного аккаунта

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

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
        cfg = self.cfg  # Типобезопасный, актуальный доступ
        if not cfg.token:
            raise ValueError("Токен не настроен")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Конфигурация нескольких аккаунтов

Базовый класс `BotAccountConfig` предоставляет поля `enabled` и `name`. Большинство адаптеров могут автоматически получать bot_id из протокола платформы или ответа на вход, в процессе преобразования событий вставляя его в конфигурацию аккаунта.:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# Большинство адаптеров: bot_id получается автоматически во время выполнения, не требует конфигурации
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

Поле metadata служит как для генерации комментариев в TOML, так и для отображения форм в WebUI:

```python
metadata = {
    "description": str | dict,  # Описание поля (поддержка i18n)
    "required": bool,         # Обязательно ли поле (валидация + метка обязательного в WebUI)
    "secret": bool,           # Является ли поле секретным (отображается как *** в WebUI, маскируется в логах)
    "ui": {                   # Конфигурация элемента управления в WebUI (старое имя "webui" по-прежнему поддерживается)
        "widget": str,        # Тип элемента: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Группа: "basic" | "advanced" | "connection" и т.д.
        "order": int,         # Вес сортировки (чем меньше, тем ближе к началу)
        "options": list,      # Доступные варианты для элемента select [{label, value}], label поддерживает i18n
        "placeholder": str | dict,  # Подсказка в поле ввода (поддержка i18n)
    },
    "extra": dict,            # Дополнительные расширения (прозрачно передаются в schema)
}
```

Все пользовательские текстовые поля поддерживают i18n, используя единый формат `{"i18n": "key", "default": "text"}`,
чистые строки передаются без изменений (для обратной совместимости). Поддерживаемые поля i18n:

| Поле | Позиция | Описание |
|------|---------|----------|
| `description` | metadata поля | Описание поля |
| `options[].label` | `ui.options` | Метки вариантов для элемента select |
| `placeholder` | `ui.placeholder` | Подсказка в поле ввода |
| `group_labels` | `_schema_meta` | Названия групп (заголовки разделов в Dashboard) |

При использовании i18n необходимо заранее зарегистрировать ключи перевода в системе i18n (см. [документацию по i18n](../../advanced/i18n.md#многоязычные-конфигурационные-поля)).

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

**Пример `group_labels` (объявляется после определения класса конфигурации):**

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "Основные настройки"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "Дополнительные настройки"},
    }
}
```

Метод `resolve_config_schema()` фреймворка автоматически разрешает все i18n ключи в зависимости от текущего языка;
`get_config_schema()` прозрачно передает i18n словарь, фронтенд должен самостоятельно разрешать ключи.

### Декларативные ключи перевода (v2.7.0+)

Адаптер может объявлять ключи перевода, как и `ConfigClass`, через вложенный класс `I18nClass`. Фреймворк автоматически регистрирует все объявленные ключи перевода на этапе `__init__` (до генерации шаблона конфигурации),
обеспечивая доступность ключей i18n, используемых в описании конфигурации, при генерации шаблона.

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="平台 Token",
            zh_TW="平台權杖",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> ``I18nKey.default`` — это **безязыковый резервный текст**, он не регистрируется ни в какой языковой версии.
> Чтобы переводы работали, необходимо явно передать хотя бы один параметр языка.

Подробное использование (правила путей ключей, явный параметр key и т.д.) смотрите в [документации по i18n](../../advanced/i18n.md#рекомендуемый-способ-объявления-ключей-перевода-через-i18nclass-v270).

### Декларативные методы расширения событий (v2.7.0+)

Адаптер может объявлять методы расширения событий платформы через `EventMixin`, фреймворк автоматически регистрирует их в текущей платформе.

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """Получить имя чата"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """Определить, является ли сообщение официальным"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

После регистрации методы можно вызывать напрямую из объекта события:

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] Официальное сообщение получено")
```

> Методы расширения событий адаптера регистрируются в его платформе (``self._platform``).
> Если модулю требуется расширение событий для нескольких платформ, используйте старый API ``register_event_mixin()``.

#### Разрешение аккаунта

Многоаккаунтный адаптер может использовать `_resolve_account()` для автоматического разрешения целевого аккаунта:

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: имя аккаунта, account: экземпляр конфигурации
```

Стратегия разрешения: сопоставление по имени аккаунта → сопоставление по полю `bot_id` → сопоставление по другим строковым полям → первый включенный аккаунт.

#### Горячая перезагрузка конфигурации

Подклассы могут переопределить `on_config_update()` для обработки изменений конфигурации:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Токен обновлен, будет выполнено повторное подключение")
```

### Процесс инициализации

Фреймворк автоматически выполняет следующие действия в `BaseAdapter.__init__(self, sdk=None)`:

1. **Ссылка на SDK**: Установка `self.sdk`, `self.logger`
2. **Фабрика Send/Request**: Создание `self.Send` и `self.Request`
3. **Шаблон конфигурации**: Если объявлен `ConfigClass`, автоматически генерируется шаблон конфигурации (в первый раз)
4. **Шаблон аккаунта**: Если объявлен `AccountConfigClass`, автоматически генерируется шаблон аккаунта (в первый раз)
5. **Регистрация EventMixin**: Если объявлен `EventMixin`, автоматически регистрируется в `AdapterManager` после вставки имени платформы

Конфигурация считывается в реальном времени через `self.cfg` / `self.accounts` (каждый доступ читает актуальные значения из хранилища конфигурации). `self.config` как совместимый псевдоним `self.cfg` по-прежнему доступен.

Большинству адаптеров не нужно переопределять `__init__`. Если требуется пользовательская инициализация:

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
        """Вложенный класс Send, наследующийся от BaseAdapter.Send"""
        pass
```

### Доступные свойства

Класс `Send` автоматически устанавливает следующие свойства при вызове:

| Свойство | Описание | Способ установки |
|-----|------|---------|
| `_target_id` | Идентификатор цели | `To(id)` или `To(type, id)` |
| `_target_type` | Тип цели | `To(type, id)` |
| `_target_to` | Упрощённый идентификатор цели | `To(id)` |
| `_account_id` | Идентификатор аккаунта отправки | `Using(account_id)` |
| `_adapter` | Экземпляр адаптера | Автоматически |
| `_at_user_ids` | Список упомянутых пользователей | `At(user_id)` |
| `_reply_message_id` | Идентификатор сообщения для ответа | `Reply(message_id)` |
| `_at_all` | Упоминание всех | `AtAll()` |

> **Рекомендуется** использовать свойство `self.send_context` для получения `target_type`, `target_id`, `account_id` в одном словаре, это более ясно, чем прямой доступ к переменным экземпляра.

### Вспомогательные методы фреймворка

| Метод/Свойство | Описание |
|-----------|------|
| `self._apply_modifiers(message)` | Объединяет статус модификаторов At/AtAll/Reply в список сообщений |
| `self.send_context` | Возвращает словарь `{target_type, target_id, account_id}` |

### Основные методы

Адаптеру нужно реализовать только `Raw_ob12`, стандартные методы (Text/Image/Voice/Video/File) уже наследуются от базового класса `SendDSL` и по умолчанию делегируются ему:

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Обязательно реализовать: преобразование OneBot12-сегментов сообщения → API платформы"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Методы Text/Image/Voice/Video/File наследуются от базового класса и автоматически делегируются Raw_ob12, повторная реализация не требуется
    # При необходимости реализации платформенно-специфической логики можно переопределить отдельные методы:
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

## События-конвертеры

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
    "time": 1234567890,           # 10-значный Unix-время
    "type": "message/notice/request/meta",
    "detail_type": "Тип события",
    "platform": "Название платформы",
    "self": {
        "platform": "Название платформы",
        "user_id": "ID бота"     # Должно совпадать с bot_id
    },
    "{platform}_raw": {...},       # Исходные данные (обязательно)
    "{platform}_raw_type": "..."    # Тип исходных данных (обязательно)
}
```

### Пример конвертера

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование исходного события платформы в стандартный формат OneBot12"""
        if not isinstance(raw_event, dict):
            return None
        
        # Генерация идентификатора события
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
        
        # Формирование стандартного события
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

### WebSocket-подключение

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """Регистрация WebSocket-маршрута"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket):
        """Обработчик WebSocket-подключения"""
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
    
    async def _auth_handler(self, websocket) -> bool:
        """Аутентификация WebSocket"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook-подключение

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """Регистрация WebHook-маршрута"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """Обработчик WebHook-запроса"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> **Информация о маршрутах**: зарегистрированные адаптером маршруты (HTTP, WebSocket, SSE) можно получить с помощью `sdk.adapter.get_connection_info(platform)` и `sdk.router.get_module_urls(module_name)`, чтобы узнать полный адрес подключения (включая `base_url` + путь). Подробнее см. [Введение в разработку адаптеров - Информация о подключениях и обнаружение маршрутов](docs/ru/getting-started.md#9-连接信息与路由发现) и [Поддержка SSE](docs/ru/getting-started.md#10-sse-server-sent-events-支持).

## Стандартный ответ API

Фреймворк предоставляет методы `make_response()` и `make_error()` для построения стандартизированного ответа, без необходимости вручную формировать словарь ответа.

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

### Ручное построение ответа (старый способ по-прежнему поддерживается)

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

После использования `AccountConfigClass` для декларативного описания конфигурации, фреймворк автоматически управляет загрузкой, проверкой и генерацией шаблонов для нескольких аккаунтов:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

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

### Конфигурационный файл аккаунта

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

### Отправка сообщений с указанием аккаунта

```python
# Использование метода Using для указания аккаунта
my_adapter = adapter.get("myplatform")

# Через self.user_id в событии (рекомендуется, наиболее универсально)
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# Через имя аккаунта
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Связь между self.user_id и Using

Механизм ответа в событиях фреймворка автоматически извлекает `account_id` (в приоритете) или `user_id` из поля `self` события и передает их в качестве параметра `Using`. Разработчикам адаптеров необходимо обеспечить корректное соответствие значения `self.user_id` в Converter с методом `_resolve_account()`.

**Внутреннее поведение фреймворка**:

```python
# Логика извлечения bot_id в фреймворке
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Вызов Using только при непустом bot_id
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Ключевой момент**: Даже если адаптер использует только одну конфигурацию бота, если Converter правильно установит `self.user_id`, фреймворк передаст его в качестве параметра `Using`. Адаптер должен обеспечить соответствие значения `self.user_id` с идентификатором поля в `AccountConfigClass` (например, `bot_id`), чтобы `_resolve_account()` мог корректно найти нужный аккаунт. Если `self.user_id` пуст, фреймворк не вызовет `Using`, и `call_api` получит `account_id` в виде `None`, при этом `_resolve_account(None)` вернет первый включенный аккаунт.

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
                    self.logger.warning(f"Ошибка подключения, повторная попытка через {wait_time} секунд")
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
        return self._error_response("Ошибка сети", 33000)
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}")
        return self._error_response(str(e), 34000)
```

> **Обратная совместимость**: Старый код адаптеров, использующий `aiohttp.ClientSession`, не затронут и по-прежнему может перехватывать `aiohttp.ClientError`. Оба способа могут сосуществовать. Рекомендуется использовать `sdk.client` + исключительную систему ErisPulse для нового кода.

## Управление статусом бота

AdapterManager содержит встроенную систему отслеживания статуса бота, автоматически поддерживает онлайн-статус, время активности и метаданные всех зарегистрированных ботов.

### Автоматическая система обнаружения

Когда адаптер отправляет событие через `adapter.emit()`, фреймворк автоматически проверяет поле `self` в событии:

- **Мета-события**: выполняет соответствующие действия в зависимости от `detail_type` (регистрация при подключении/отключение и отмечает как неактивный/heartbeat обновляет время активности)
- **Обычные события** (message/notice/request): автоматически обнаруживает бота и обновляет время активности

```python
# Все события, содержащие поле self, запускают автоматическую регистрацию
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Бот "bot123" будет автоматически зарегистрирован (если это первый раз) и обновлено время активности
```

### Типы мета-событий

| `detail_type` | Описание | Поведение фреймворка |
|---|---|---|
| `connect` | Подключение бота | Регистрирует бота и запускает событие жизненного цикла `adapter.bot.online` |
| `disconnect` | Отключение бота | Отмечает бота как неактивный и запускает событие жизненного цикла `adapter.bot.offline` |
| `heartbeat` | Событие heartbeat | Обновляет время активности и метаданные бота |

### Отправка мета-событий адаптером

Используйте `emit_meta()` для отправки мета-событий всего одной строкой:

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # Отправка события connect одной строкой
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="Мой бот")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

Также поддерживается ручная конструкция (старый способ по-прежнему совместим):

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### Расширенная информация в поле `self`

Поле `self` помимо обязательных `platform` и `user_id` поддерживает следующие необязательные поля:

| Поле | Описание |
|---|---|
| `user_name` | Имя пользователя бота |
| `nickname` | Никнейм бота |
| `avatar` | URL аватара бота |
| `account_id` | Идентификатор для нескольких аккаунтов |

### Запрос статуса бота

```python
from ErisPulse import sdk

# Получение информации о конкретном боте
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# Получение списка всех ботов
all_bots = sdk.adapter.list_bots()

# Получение списка ботов на указанной платформе
platform_bots = sdk.adapter.list_bots("myplatform")

# Проверка, находится ли бот онлайн
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Получение полного сводного статуса (подходит для отображения в WebUI)
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
    sdk.logger.info(f"Бот подключился: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Бот отключился: {platform}/{bot_id}")
```

## Связанные документы

- [Введение в разработку адаптеров](docs/ru/getting-started.md) - Создание первого адаптера
- [Подробное руководство по SendDSL](docs/ru/send-dsl.md) - Изучение отправки сообщений
- [Лучшие практики разработки адаптеров](docs/ru/best-practices.md) - Разработка качественных адаптеров