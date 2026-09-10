# Основные концепции адаптера

Понимание основных концепций адаптера ErisPulse — это основа для разработки адаптеров.

## Архитектура адаптера

### Отношения между компонентами

```
Прямое преобразование (направление приёма)                      Обратное преобразование (направление отправки)
─────────────────                                           ─────────────────
                                                             
┌──────────────────┐                                        ┌──────────────────┐
│ Платформа-специфич. события │                                        │ Модуль формирует сообщение │
└────────┬─────────┘                                        └────────┬─────────┘
         │                                                           │
         ↓                                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ Адаптер (MyAdapter) │   │ Send.Raw_ob12()  │
│  Converter       │   │ ┌──────────────┐ │   │ (точка входа обратного преобразования)   │
│  (конвертер событий)    │──→│ │              │ │   │                  │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Вызов API платформы    │
                       │ Стандартные события OneBot12 │    └────────┬─────────┘
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
- **Прямое преобразование** (Converter): платформа-специфич. события → события OneBot12, оригинальные данные сохраняются в `{platform}_raw`
- **Обратное преобразование** (Raw_ob12): сообщения OneBot12 → вызов API платформы, возвращается стандартный формат ответа

## AdapterManager (менеджер адаптеров)

`AdapterManager` — это основной компонент системы адаптеров ErisPulse, отвечающий за управление всеми зарегистрированными платформенными адаптерами, их запуск, остановку и распределение событий.

### Основные функции

- **Регистрация адаптеров**: управление несколькими платформенными адаптерами
- **Жизненный цикл**: управление запуском и остановкой адаптеров
- **Распределение событий**: распределение событий OneBot12 и платформы
- **Управление конфигурацией**: управление включением/выключением адаптеров
- **Поддержка промежуточных обработчиков**: поддержка промежуточных обработчиков событий OneBot12

### Основное использование

```python
from ErisPulse import sdk

# Регистрация адаптера (обычно выполняется автоматически Loader)
sdk.adapter.register("myplatform", MyPlatformAdapter)

# Запуск всех адаптеров
await sdk.adapter.startup()

# Запуск указанного адаптера
await sdk.adapter.startup(["myplatform"])
# Запуск всех адаптеров
await sdk.adapter.startup()

# Получение экземпляра адаптера
my_adapter = sdk.adapter.get("myplatform")
# Или через атрибут
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
3. Параллельный запуск адаптеров
4. При неудаче автоматическая повторная попытка (стратегия экспоненциального отступа)
5. После успешного запуска отправка события `adapter.status.change` (started)

**Механизм повторной попытки**:

- Первые 4 попытки: 60 секунд, 10 минут, 30 минут, 60 минут
- Пятая и последующие: фиксированный интервал 3 часа

#### Остановка адаптера

```python
# Остановка всех адаптеров
await sdk.adapter.shutdown()
```

**Процесс остановки**:

1. Отправка события жизненного цикла `adapter.stop`
2. Вызов метода `shutdown()` всех адаптеров
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
# Список всех зарегистрированных платформ
platforms = sdk.adapter.list_registered()

# Список всех платформ и их состояний
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
    print(f"Получено сообщение OneBot12: {data}")

# Обработка стандартных событий сообщений для конкретной платформы
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"Получено сообщение myplatform: {data}")

# Обработка всех событий
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"Получено событие: {data.get('type')}")
```

#### Платформенно-специфич. события

```python
# Обработка событий конкретной платформы
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Получено платформенно-специфич. событие: {data})

# Обработка всех платформенно-специфич. событий (символ подстановки)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Получено платформенно-специфич. событие: {data})
```

#### Механизм распределения событий

При вызове `adapter.emit(event_data)`:

1. **Обработка промежуточными обработчиками**: сначала выполняются все промежуточные обработчики OneBot12
2. **Распределение стандартных событий**: распределение к соответствующим обработчикам событий OneBot12
3. **Распределение платформенно-специфич. событий**: если есть оригинальные данные, распределение к обработчикам платформенно-специфич. событий

**Правила сопоставления**:

- Точное совпадение: `@sdk.adapter.on("message")` только для события `message`
- Символ подстановки: `@sdk.adapter.on("*")` для всех событий
- Фильтрация платформы: `platform="myplatform"` только для событий указанной платформы

### Промежуточные обработчики

#### Добавление промежуточного обработчика

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """Промежуточный обработчик логирования"""
    print(f"Обработка события: {data.get('type')}")
    return data  # Обязательно вернуть данные

@sdk.adapter.middleware
async def filter_middleware(data):
    """Промежуточный обработчик фильтрации"""
    # Фильтрация ненужных событий
    if data.get("type") == "notice":
        return None  # При возврате None промежуточная цепочка игнорирует этот результат, сохраняя исходные данные для передачи
    return data  # Обязательно вернуть данные для продолжения передачи
```

#### Порядок выполнения промежуточных обработчиков

Промежуточные обработчики выполняются в порядке регистрации, последний зарегистрированный промежуточный обработчик выполняется первым.

> **Внимание**: если промежуточный обработчик возвращает `None` (например, забыл `return data`), фреймворк проигнорирует этот результат и сохранит исходные данные для передачи, при этом выведет предупреждение уровня warning. Это гарантирует, что сбой одного промежуточного обработчика не приведёт к прерыванию всей цепочки событий.

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

#### Доступ по атрибуту

```python
# Доступ по имени атрибута (регистр не имеет значения)
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter (базовый класс)

### Основная структура

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """Конфигурация адаптера (объявляется, фреймворк управляет автоматически)"""
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
    ConfigClass = MyConfig  # Объявить класс конфигурации
    
    # Не нужно переопределять __init__, фреймворк обрабатывает автоматически:
    # - self.sdk, self.logger
    # - self.cfg (типобезопасная конфигурация, считывается в реальном времени)
    # - self.Send, self.Request
    
    async def start(self):
        """Запуск адаптера (обязательно реализовать)"""
        cfg = self.cfg  # Автоматически загруженная типобезопасная конфигурация
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

#### Конфигурация с одним аккаунтом

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

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
        cfg = self.cfg  # Типобезопасно, считывается в реальном времени
        if not cfg.token:
            raise ValueError("Не настроен токен")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Конфигурация с несколькими аккаунтами

Базовый класс `BotAccountConfig` предоставляет поля `enabled` и `name`. Большинство адаптеров могут автоматически получать `bot_id` из протокола платформы или ответа при входе, в процессе преобразования событий он вставляется в конфигурацию аккаунта.:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# Большинство адаптеров: bot_id получается автоматически во время выполнения, не нужно конфигурировать
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

Поле metadata служит одновременно для генерации комментариев в TOML и рендеринга форм в WebUI:

```python
metadata = {
    "description": str | dict,  # Описание поля (поддержка i18n)
    "required": bool,         # Обязательно ли заполнять (проверка + метка обязательности в WebUI)
    "secret": bool,           # Является ли чувствительным (в WebUI отображается как ***, в логах маскируется)
    "example": bool,          # Флаг не сохранения: не записывается в config.toml (исключается из значения по умолчанию и шаблона),
                              # только рендерится в config.full.example; schema с "example": true меткой,
                              # конфигурационный гид CLI по умолчанию пропускает; после ручной установки пользователем сохраняется нормально
    "min": number, "max": number,  # Проверка диапазона значений
    "ui": {                   # Настройки элемента управления (старое имя "webui" по-прежнему совместимо)
        "widget": str,        # Тип элемента: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Группа: "basic" | "advanced" | "connection" и т.д.
        "order": int,         # Вес сортировки (чем меньше, тем ближе)
        "options": list,      # Доступные опции для элемента select [{label, value}], label поддерживает i18n
        "placeholder": str | dict,  # Подсказка в поле ввода (поддержка i18n)
    },
    "extra": dict,            # Дополнительные расширенные поля (прозрачно передаются в schema)
}
```

Все пользовательские видимые текстовые поля поддерживают i18n, единый формат: `{"i18n": "ключ", "default": "текст"}`,
чистая строка прозрачно передается (обратная совместимость). Поддерживаемые поля i18n:

| Поле | Позиция | Описание |
|------|------|------|
| `description` | metadata поля | Описание поля |
| `options[].label` | `ui.options` | Метка опции элемента select |
| `placeholder` | `ui.placeholder` | Подсказка в поле ввода |
| `group_labels` | `_schema_meta` | Название раздела (заголовок секции Dashboard) |

При использовании i18n необходимо заранее зарегистрировать ключ перевода в систему i18n (см. [документацию по i18n](../../advanced/i18n.md#конфигурация-многоязычных-полей) для подробностей).

**Примеры `description` / `placeholder` / `options label`**:

```python
token: str = field(
    default="",
    metadata={
        "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
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
                {"label": "Чистая строка метки", "value": "b"},  # Чистая строка передается как есть
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

Метод `resolve_config_schema()` фреймворка автоматически разрешает все перечисленные выше поля i18n в зависимости от текущего языка;
`get_config_schema()` прозрачно передает словарь i18n, и интерфейс будет разрешать его самостоятельно.

#### Автоматическое создание описания полей из docstring (v2.8.0+)

Поле, не объявленное в metadata `description`, фреймворк автоматически извлекает описание из docstring класса конфигурации в качестве запасного варианта, поддерживает два распространенных стиля (можно использовать вместе):

```python
@dataclass
class MyConfig(BaseConfig):
    """
    Конфигурация MyAdapter

    :ivar endpoint: Адрес API платформы        # Стиль reST
    :ivar timeout: Время ожидания в секундах
    """

    endpoint: str = "https://api.example.com"   # Без metadata description → описание из docstring
    timeout: int = 30

    # Также поддерживается стиль Google (раздел Attributes):
    # Attributes:
    #     endpoint: Адрес API платформы
```

Приоритет: **metadata description > описание поля из docstring > пусто**.
Описание в формате i18n-словаря не затрагивается (всегда приоритет).

#### Вложенные конфигурации (v2.8.0+)

При типе поля вложенный dataclass фреймворк рекурсивно обрабатывает: schema с `"type": "table"` +
`"fields"` поддерево (WebUI рендерит как складываемую вложенную группу), TOML шаблон рендерится как `[подтаблица]` секция,
по умолчанию / заполнение / проверка / разрешение i18n рекурсивно применяются.

```python
@dataclass
class RetryConfig(BaseConfig):
    """Стратегия повтора

    :ivar max_retries: Максимальное количество повторных попыток
    """
    max_retries: int = 3
    backoff: float = 0.5

@dataclass
class MyConfig(BaseConfig):
    """Конфигурация MyAdapter"""
    endpoint: str = "https://api.example.com"
    retry: RetryConfig = field(default_factory=RetryConfig)   # Вложенный конфигурационный раздел
```

Сгенерированный TOML шаблон:

```toml
endpoint = "https://api.example.com"

[retry]
# Максимальное количество повторных попыток
max_retries = 3
backoff = 0.5
```

> Рекомендуется использовать прямой тип аннотации для вложенных типов; строковые аннотации (например, для отложенного вычисления) должны гарантировать, что тип можно разрешить из модуля конфигурационного класса, глобально, по `__qualname__` или по имени класса.

#### Не сохраняемые поля `example` (v2.8.0+)

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

Поле с `example: True`:

- Не записывается в config.toml (шаблон конфигурации адаптера/модуля и значения по умолчанию исключаются, используются значения по умолчанию из кода)
- Отображается только в `config.full.example` проекта (для справки, копируются по желанию в config.toml)
- В schema помечается как `"example": true` (интерфейс может самостоятельно решить стратегию отображения), CLI конфигурационный гид по умолчанию пропускает
- После ручной установки пользователем сохраняется нормально, нормально обновляется (приоритет явного намерения пользователя)

Подходит для "многочисленных и редко используемых" настроек, чтобы сохранить config.toml пользователя минимальным.

> ⚠️ `_schema_meta` — это метаданные на уровне класса (не поле конфигурации). Если объявить внутри тела dataclass класса,
> необходимо добавить аннотацию `ClassVar` (`_schema_meta: ClassVar[dict] = {...}`), иначе dataclass будет воспринимать это как обычное поле. Фреймворк защитно исключает поля с подчеркиванием в начале (не включает в любой schema / шаблон / значения по умолчанию / проверки), но рекомендуется соблюдать стандартное объявление.

### Декларативные ключи перевода (v2.7.0+)

Адаптер может декларировать ключи перевода, подобно `ConfigClass`, с помощью вложенного класса `I18nClass`, фреймворк автоматически зарегистрирует все объявленные ключи перевода в `__init__` этапе (до генерации шаблона конфигурации), обеспечивая доступность ключей перевода в описаниях конфигурации при генерации шаблона.

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

> ``I18nKey.default`` — это **языкозависимый запасной текст**, не регистрируется ни в каком языке.
> Чтобы перевод был активен, необходимо явно передать хотя бы один параметр языка.

Подробное использование (правила путей ключей, явный параметр key и т.д.) см. в [документации по i18n](../../advanced/i18n.md#рекомендуемый-способ-объявление-ключей-перевода-через-i18nclass-v270).

### Декларативные расширения событий (v2.7.0+)

Адаптер может декларировать платформенно-специфич. методы расширения событий через `EventMixin`, фреймворк автоматически регистрирует их для текущей платформы.

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """Получить название чата"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """Проверить, является ли сообщение официальным"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

После регистрации, методы расширения событий доступны напрямую в объекте события:

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] Официальное сообщение получено")
```

> Методы расширения событий адаптера регистрируются в собственной платформе (``self._platform``).
> Модули, которые нуждаются в расширении событий на разных платформах, должны использовать старый API ``register_event_mixin()``.

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

Подкласс может переопределить `on_config_update()` для реакции на изменения конфигурации:

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
5. **Регистрация EventMixin**: если объявлен `EventMixin`, автоматически регистрируется в `AdapterManager` после вставки имени платформы

Конфигурация считывается в реальном времени через `self.cfg` / `self.accounts` (каждый доступ читает последнее значение из хранилища конфигурации). `self.config` как совместимый псевдоним `self.cfg` по-прежнему доступен.

Большинству адаптеров не нужно переопределять `__init__`. Если требуется кастомная инициализация:

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

При вызове `Send` автоматически устанавливаются следующие свойства:

| Свойство | Описание | Способ установки |
|-----|------|---------|
| `_target_id` | Идентификатор цели | `To(id)` или `To(type, id)` |
| `_target_type` | Тип цели | `To(type, id)` |
| `_target_to` | Упрощенный идентификатор цели | `To(id)` |
| `_account_id` | Идентификатор отправляемого аккаунта | `Using(account_id)` |
| `_adapter` | Экземпляр адаптера | Автоматически установлен |
| `_at_user_ids` | Список пользователей для упоминания | `At(user_id)` |
| `_reply_message_id` | Идентификатор сообщения для ответа | `Reply(message_id)` |
| `_at_all` | Упоминание всех пользователей | `AtAll()` |

> **Рекомендуется**: использовать свойство `self.send_context` для получения `target_type`, `target_id`, `account_id` за один раз, что делает код более понятным, чем прямой доступ к экземплярным переменным.

### Вспомогательные методы фреймворка

| Метод/свойство | Описание |
|-----------|------|
| `self._apply_modifiers(message)` | Объединение состояний модификаторов At/AtAll/Reply в список сообщений |
| `self.send_context` | Возвращает словарь `{target_type, target_id, account_id}` |

### Основные методы

Адаптер должен реализовать только `Raw_ob12`, стандартные методы (Text/Image/Voice/Video/File) уже унаследованы от базового класса `SendDSL` и по умолчанию делегированы ему:

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Обязательно реализовать: OneBot12 сообщения → платформенный API"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File уже унаследованы от базового класса, автоматически делегируют Raw_ob12, не нужно повторно реализовывать
    # Если нужна платформенно-специфич. логика, можно переопределить отдельный метод:
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Цепочечные модифицирующие методы

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
Платформенно-специфич. событие
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
    "time": 1234567890,           # 10-значный Unix timestamp
    "type": "message/notice/request/meta",
    "detail_type": "Детальный тип события",
    "platform": "Название платформы",
    "self": {
        "platform": "Название платформы",
        "user_id": "ID бота"     # Должен совпадать с bot_id
    },
    "{platform}_raw": {...},       # Оригинальные данные (обязательно)
    "{platform}_raw_type": "..."    # Тип оригинального события (обязательно)
}
```

### Пример конвертера

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразование платформенно-специфич. события в стандартный формат OneBot12"""
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
    
    async def _auth_handler(self, websocket) -> bool:
        """Проверка подключения"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook подключение

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """Регистрация HTTP маршрута"""
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

> **Информация о маршрутах**: зарегистрированные адаптером маршруты (HTTP, WebSocket, SSE) можно получить через `sdk.adapter.get_connection_info(platform)` и `sdk.router.get_module_urls(module_name)`, включая `base_url` + путь. Подробнее см. [Введение в разработку адаптеров - Информация о подключениях и обнаружение маршрутов](getting-started.md#9-информация-о-подключениях-и-обнаружение-маршрутов) и [Поддержка SSE](getting-started.md#10-sse-server-sent-events-поддержка).

## Стандартные ответы API

Фреймворк предоставляет методы `make_response()` и `make_error()` для построения стандартизированных ответов, не нужно вручную создавать словарь ответа.

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

После объявления `AccountConfigClass` фреймворк автоматически управляет загрузкой, проверкой и генерацией шаблонов конфигурации нескольких аккаунтов:

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

### Отправка сообщения с указанием аккаунта

```python
# Использовать метод Using для указания аккаунта
my_adapter = adapter.get("myplatform")

# Рекомендуется использовать self.user_id из события
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# По имени аккаунта
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Соотношение self.user_id и Using

Механизм ответа фреймворка автоматически извлекает `account_id` (приоритет) или `user_id` из поля `self` события, передавая его как параметр `Using`. Разработчику адаптера необходимо обеспечить, чтобы Converter правильно устанавливал `self.user_id`, чтобы `Using` мог сопоставиться.

**Внутренняя логика фреймворка**:

```python
# Логика извлечения bot_id фреймворком
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Вызов Using только при непустом bot_id
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Ключевой момент**: даже если адаптер использует только одну конфигурацию бота, если Converter правильно устанавливает `self.user_id`, фреймворк будет использовать его как параметр `Using`. Адаптер должен убедиться, что `self.user_id` совпадает с идентификатором поля в `AccountConfigClass` (например, `bot_id`), чтобы `_resolve_account()` мог сопоставиться с правильным аккаунтом. Если `self.user_id` пуст, фреймворк не вызовет `Using`, и `call_api` получит `account_id` как `None`, `_resolve_account(None)` вернёт первый включённый аккаунт.

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
                    self.logger.warning(f"Подключение не удалось, повтор через {wait_time} секунд")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### Обработка ошибок API

```python
async def call_api(self, endpoint: str, **params):
    try:
        # Рекомендуется использовать клиент SDK
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
        self.logger.error(f"Запрос таймаут: {endpoint}")
        return self._error_response("Запрос таймаут", 32000)
    except ClientError as e:
        self.logger.error(f"Ошибка сети: {e}")
        return self._error_response("Ошибка сети", 33000)
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}")
        return self._error_response(str(e), 34000)
```

> **Обратная совместимость**: код старых адаптеров, использующих `aiohttp.ClientSession`, не затрагивается, по-прежнему можно перехватывать `aiohttp.ClientError`. Два способа могут сосуществовать. Рекомендуется использовать `sdk.client` + систему исключений ErisPulse для нового кода.

## Управление состоянием бота

`AdapterManager` содержит встроенную систему отслеживания состояния ботов, автоматически отслеживает онлайн-статус, время активности и метаинформацию всех зарегистрированных ботов.

### Автоматическое обнаружение

При отправке событий через `adapter.emit()` фреймворк автоматически проверяет поле `self` событий:

- **Мета-события**: в зависимости от `detail_type` выполняются соответствующие действия (connect — регистрация, disconnect — пометка как отключённого, heartbeat — обновление времени активности)
- **Обычные события** (message/notice/request): автоматически обнаруживаются боты и обновляется время активности

```python
# Все события с полем self будут запускать автоматическое обнаружение
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Бот "bot123" будет автоматически зарегистрирован (если это первый раз) и обновлено время активности
```

### Типы мета-событий

| `detail_type` | Описание | Действие фреймворка |
|---|---|---|
| `connect` | Бот подключился | Регистрация бота и запуск события жизненного цикла `adapter.bot.online` |
| `disconnect` | Бот отключился | Пометка бота как отключённого и запуск события жизненного цикла `adapter.bot.offline` |
| `heartbeat` | Бот отправил heartbeat | Обновление времени активности и метаинформации бота |

### Отправка мета-событий адаптером

Использование `emit_meta()` для отправки мета-событий:

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # Одним вызовом отправить событие connect
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="Мой бот")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

Также поддерживается ручное построение (старый способ по-прежнему совместим):

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### Расширение поля self

Поле `self` помимо обязательных `platform` и `user_id` поддерживает следующие необязательные поля:

| Поле | Описание |
|---|---|
| `user_name` | Имя пользователя бота |
| `nickname` | Никнейм бота |
| `avatar` | URL аватара бота |
| `account_id` | Идентификатор аккаунта |

### Запрос состояния бота

```python
from ErisPulse import sdk

# Получить информацию о боте
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# Список всех ботов
all_bots = sdk.adapter.list_bots()

# Список ботов указанной платформы
platform_bots = sdk.adapter.list_bots("myplatform")

# Проверить, онлайн ли бот
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Получить полную сводку состояния (подходит для отображения в WebUI)
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Отслеживание жизненного цикла бота

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

- [Введение в разработку адаптеров](getting-started.md) - Создание первого адаптера
- [SendDSL подробно](send-dsl.md) - Изучение отправки сообщений
- [Лучшие практики разработки адаптеров](best-practices.md) - Разработка высококачественных адаптеров