# Основные концепции адаптера

Понимание основных концепций адаптера ErisPulse является основой для разработки адаптеров.

docs/ru/quick-start.md

## Архитектура адаптера

### Отношения между компонентами

```
Прямое преобразование (направление получения)        Обратное преобразование (направление отправки)
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ События платформы │                        │ Сообщения модуля │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ Адаптер (MyAdapter) │   │ Send.Raw_ob12()  │
│  Converter       │   │ ┌──────────────┐ │   │ (точка входа в обратное преобразование) │
│  (конвертер событий) │──→│ │              │ │   │                  │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Вызов API платформы │
                       │ Стандартные события OneBot12 │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Стандартный формат ответа │
                       │ Система событий │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ Модуль (обработка событий) │
                       └──────────────────┘
```

**Основная симметрия**:
- **Прямое преобразование** (Converter): События платформы → Стандартные события OneBot12, исходные данные сохраняются в `{platform}_raw`
- **Обратное преобразование** (Raw_ob12): Сообщения OneBot12 → Вызов API платформы, возвращается стандартный формат ответа

## AdapterManager адаптер-менеджер

`AdapterManager` — это основной компонент адаптерной системы ErisPulse, отвечающий за управление регистрацией, запуском, остановкой и рассылкой событий для всех адаптеров платформ.

### Основные функции

- **Регистрация адаптеров**: Регистрация и управление несколькими адаптерами платформ.
- **Управление жизненным циклом**: Контроль запуска и остановки адаптеров.
- **Рассылка событий**: Рассылка стандартных событий OneBot12 и событий, специфичных для платформы.
- **Управление конфигурацией**: Управление включением/выключением адаптеров.
- **Поддержка промежуточного ПО (middleware)**: Поддержка промежуточного ПО для событий OneBot12.

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
# Или доступ через свойства
my_adapter = sdk.adapter.myplatform

# Остановка всех адаптеров
await sdk.adapter.shutdown()
```

### Запуск и остановка

#### Запуск адаптера

```python
# Запуск всех зарегистрированных адаптеров
await sdk.adapter.startup()

# Запуск указанных платформ
await sdk.adapter.startup(["platform1", "platform2"])
```

**Процесс запуска:**

1. Выполнение события жизненного цикла `adapter.start`
2. Выполнение события `adapter.status.change` (starting)
3. Параллельный запуск каждого адаптера
4. При неудачном запуске автоматическая повторная попытка (стратегия экспоненциальной отсрочки)
5. После успешного запуска выполнение события `adapter.status.change` (started)

**Механизм повторных попыток:**

- Первые 4 попытки: 60 секунд, 10 минут, 30 минут, 60 минут
- Пятая и последующие попытки: фиксированный интервал в 3 часа

#### Остановка адаптера

```python
# Остановка всех адаптеров
await sdk.adapter.shutdown()
```

**Процесс остановки:**

1. Выполнение события жизненного цикла `adapter.stop`
2. Вызов метода `shutdown()` для всех адаптеров
3. Остановка сервера маршрутизации
4. Очистка обработчиков событий
5. Выполнение события жизненного цикла `adapter.stopped`

### Управление конфигурацией

#### Проверка статуса платформы

```python
# Проверка наличия платформы в списке зарегистрированных
exists = sdk.adapter.exists("myplatform")

# Проверка включения платформы
enabled = sdk.adapter.is_enabled("myplatform")

# Использование оператора in
if "myplatform" in sdk.adapter:
    print("Платформа существует и включена")
```

#### Перечисление платформ

```python
# Перечисление всех зарегистрированных платформ
platforms = sdk.adapter.list_registered()

# Перечисление всех платформ и их статусов
status_dict = sdk.adapter.list_items()
# Возвращается: {"platform1": true, "platform2": false, ...}

# Получение списка включенных платформ
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### Слушатели событий

#### Стандартные события OneBot12

```python
from ErisPulse import sdk

# Слушатель для всех стандартных событий сообщений по OneBot12
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Получено сообщение OneBot12: {data}")

# Слушатель для стандартных событий сообщений определённой платформы
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"Получено сообщение myplatform: {data}")

# Слушатель для всех событий
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"Получено событие: {data.get('type')}")
```

#### События, специфичные для платформы

```python
# Слушатель для событий определённой платформы
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Получено событие: {data}")

# Слушатель для событий всех платформ (с использованием шаблона)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Получено событие: {data}")
```

#### Механизм рассылки событий

При вызове `adapter.emit(event_data)`:

1. **Обработка промежуточного ПО**: Сначала выполняются все промежуточные обработчики OneBot12.
2. **Рассылка стандартных событий**: Рассылка к соответствующим обработчикам событий OneBot12.
3. **Рассылка событий, специфичных для платформы**: Если есть оригинальные данные, рассылка к обработчикам событий, специфичных для платформы.

**Правила сопоставления:**

- Точное сопоставление: `@sdk.adapter.on("message")` сопоставляет только событие `message`.
- Шаблон: `@sdk.adapter.on("*")` сопоставляет все события.
- Фильтрация по платформе: `platform="myplatform"` сопоставляет события только указанной платформы.

### Промежуточное ПО (Middleware)

#### Добавление промежуточного ПО

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """Промежуточное ПО для логирования"""
    print(f"Обработка события: {data.get('type')}")
    return data  # Обязательно возвращать данные

@sdk.adapter.middleware
async def filter_middleware(data):
    """Промежуточное ПО для фильтрации событий"""
    # Фильтрация ненужных событий
    if data.get("type") == "notice":
        return None  # При возврате None промежуточное ПО игнорирует результат и сохраняет исходные данные для передачи дальше
    return data  # Обязательно возвращать данные для продолжения передачи
```

#### Порядок выполнения промежуточного ПО

Промежуточное ПО выполняется в порядке регистрации, последнее зарегистрированное промежуточное ПО выполняется первым.

> **Внимание**: Если промежуточное ПО возвращает `None` (например, забыли `return data`), фреймворк игнорирует результат и сохраняет исходные данные для передачи дальше, при этом выводится предупреждение уровня warning. Это обеспечивает, что ошибка в одном промежуточном ПО не приведёт к остановке всей цепочки событий.

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

#### Доступ через свойства

```python
# Доступ по имени свойства (регистронезависимый)
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")

## Базовый класс BaseAdapter

### Основная структура

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """Конфигурация адаптера (объявляется, затем автоматически управляется фреймворком)"""
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
        """Вызов API платформы (обязательно реализовать)"""
        pass
```

### Управление конфигурацией

Фреймворк предоставляет декларативное управление конфигурацией, с помощью dataclass определяется структура конфигурации, фреймворк автоматически обрабатывает загрузку, проверку и генерацию шаблонов.

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
        cfg = self.cfg  # Типобезопасно, считывается в реальном времени
        if not cfg.token:
            raise ValueError("Токен не настроен")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Конфигурация нескольких аккаунтов

Базовый класс `BotAccountConfig` предоставляет поля `enabled` и `name`. Большинство адаптеров могут автоматически получать bot_id из протокола платформы или ответа на вход, и вставлять его в конфигурацию аккаунта при преобразовании событий.：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# Большинство адаптеров: bot_id получается автоматически во время выполнения, не нужно настраивать
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Токен"},
        "required": True,
    })

# Если при входе невозможно получить bot_id, можно позволить пользователю заполнить в конфигурации
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

#### Соглашения по metadata

Поле metadata используется одновременно для генерации комментариев TOML и рендеринга форм WebUI:

```python
metadata = {
    "description": str | dict,  # Описание поля (поддержка i18n)
    "required": bool,         # Обязательно ли поле (валидация + метка обязательного поля в WebUI)
    "secret": bool,           # Является ли поле чувствительным (в WebUI отображается как ***, в логах маскируется)
    "ui": {                   # Конфигурация элементов управления WebUI (старое имя "webui" по-прежнему совместимо)
        "widget": str,        # Тип элемента управления: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Группа: "basic" | "advanced" | "connection" и т.д.
        "order": int,         # Вес сортировки (чем меньше, тем ближе к началу)
        "options": list,      # Доступные опции для элемента select [{label, value}], label поддерживает i18n
        "placeholder": str | dict,  # Подсказка в поле ввода (поддержка i18n)
    },
    "extra": dict,            # Дополнительные расширенные поля (прозрачно передаются в schema)
}
```

Все пользовательские текстовые поля поддерживают i18n, используется единый формат `{"i18n": "key", "default": "текст"}`,
чистые строки передаются без изменений (для обратной совместимости). Поддерживаемые поля i18n:

| Поле | Позиция | Описание |
|------|------|------|
| `description` | metadata поля | Описание поля |
| `options[].label` | `ui.options` | Метка опций элемента select |
| `placeholder` | `ui.placeholder` | Подсказка в поле ввода |
| `group_labels` | `_schema_meta` | Название группы (заголовок раздела Dashboard) |

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

Функция `resolve_config_schema()` фреймворка автоматически разрешает все вышеуказанные поля i18n в зависимости от текущего языка;
`get_config_schema()` прозрачно передает словарь i18n, и фронтенд самостоятельно его разрешает.

### Декларативные ключи перевода (v2.7.0+)

Адаптер может объявлять ключи перевода, используя вложенный класс `I18nClass`, подобно объявлению `ConfigClass`.
Фреймворк автоматически регистрирует все объявленные ключи перевода на этапе `__init__` (до генерации шаблона конфигурации),
обеспечивая доступность ключей перевода, используемых в описаниях конфигурации, при генерации шаблона.

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

> ``I18nKey.default`` — это **базовый текст, не привязанный к языку**, который не регистрируется ни в одну из языковых версий.
> Чтобы перевод был активен, необходимо явно передать хотя бы один параметр языка.

Подробное использование (правила пути ключей, явный параметр key и т.д.) см. в [документации по i18n](../../advanced/i18n.md#рекомендуемый-способ-объявления-ключей-перевода-через-i18nclass-v270).

### Декларативные методы расширения событий (v2.7.0+)

Адаптер может объявлять методы расширения событий, специфичные для платформы, используя `EventMixin`, фреймворк автоматически регистрирует их в текущей платформе.

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """Получение названия чата"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """Определение, является ли сообщение официальным"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

После регистрации, объекты событий могут напрямую вызывать эти методы:

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] Получено официальное сообщение")
```

> Методы расширения событий адаптера регистрируются в его собственной платформе (``self._platform``).
> Если модули нуждаются в расширении событий на разных платформах, следует использовать API `register_event_mixin()`.

#### Разрешение аккаунтов

Многоаккаунтные адаптеры могут использовать `_resolve_account()` для автоматического разрешения целевого аккаунта:

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: имя аккаунта, account: экземпляр конфигурации
```

Стратегия разрешения: сопоставление имени аккаунта → сопоставление поля `bot_id` → сопоставление других строковых полей → первый включенный аккаунт.

#### Горячее обновление конфигурации

Подклассы могут переопределить `on_config_update()` для реакции на изменения конфигурации:

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

Конфигурация считывается в реальном времени через `self.cfg` / `self.accounts` (каждый доступ считывает последнее значение из хранилища конфигурации). `self.config` как совместимый псевдоним `self.cfg` по-прежнему доступен.

Большинству адаптеров не нужно переопределять `__init__`. Если требуется пользовательская инициализация:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # Передача sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

Пожалуйста, верните напрямую переведенный полный Markdown-контент, без каких-либо дополнительных пояснений.

## DSL для отправки сообщений

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
| `_account_id` | Идентификатор отправляющего аккаунта | `Using(account_id)` |
| `_adapter` | Экземпляр адаптера | Устанавливается автоматически |
| `_at_user_ids` | Список упомянутых пользователей | `At(user_id)` |
| `_reply_message_id` | Идентификатор сообщения для ответа | `Reply(message_id)` |
| `_at_all` | Упоминание всех пользователей | `AtAll()` |

> **Рекомендуется**: Использовать свойство `self.send_context` для получения `target_type`, `target_id`, `account_id` за один вызов, это более понятно, чем прямой доступ к экземплярным переменным.

### Вспомогательные методы фреймворка

| Метод/свойство | Описание |
|-----------|------|
| `self._apply_modifiers(message)` | Объединяет статусы модификаторов At/AtAll/Reply в список сегментов сообщения |
| `self.send_context` | Возвращает словарь `{target_type, target_id, account_id}` |

### Основные методы

Адаптеру нужно реализовать только `Raw_ob12`, стандартные методы (Text/Image/Voice/Video/File) уже унаследованы от базового класса `SendDSL` и по умолчанию делегируются ему:

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Обязательно реализовать: преобразование OneBot12 сегментов сообщения → API платформы"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Методы Text/Image/Voice/Video/File унаследованы от базового класса и автоматически делегируют Raw_ob12, повторная реализация не требуется
    # При необходимости реализации платформенно-специфической логики, можно переопределить отдельные методы:
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
    "time": 1234567890,           # 10-значный Unix-время
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
        """Преобразует исходное событие платформы в стандартный формат OneBot12"""
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

> **Запрос информации о маршруте**: маршруты, зарегистрированные адаптером (HTTP, WebSocket, SSE), можно получить с помощью `sdk.adapter.get_connection_info(platform)` и `sdk.router.get_module_urls(module_name)`, чтобы получить полный адрес соединения (включая `base_url` + путь). Подробнее см. [Введение в разработку адаптеров - Информация о подключении и обнаружение маршрутов](docs/ru/getting-started.md#9-连接信息与路由发现) и [Поддержка SSE](docs/ru/getting-started.md#10-sse-server-sent-events-支持).

## Стандарт ответа API

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

## Поддержка нескольких аккаунтов

### Декларативная конфигурация (рекомендуется)

После использования `AccountConfigClass` для декларативного класса конфигурации, фреймворк автоматически управляет загрузкой, проверкой и генерацией шаблонов для нескольких аккаунтов:

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
        # Использование account.token, account.bot_id и других полей
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

### Отправка с указанием аккаунта

```python
# Использование метода Using для указания аккаунта
my_adapter = adapter.get("myplatform")

# Через self.user_id в событии (рекомендуется, наиболее универсально)
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# Через имя аккаунта
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Связь self.user_id и Using

Механизм ответа событий фреймворка автоматически извлекает `account_id` (в первую очередь) или `user_id` из поля `self` события и передает их в качестве параметра `Using`. Разработчику адаптера необходимо убедиться, что значение `self.user_id` в Converter корректно соответствует `_resolve_account()`.

**Внутреннее поведение фреймворка**:

```python
# Логика извлечения bot_id фреймворком
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Вызов Using только в случае, если bot_id не пустой
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Ключевой момент**: Даже если адаптер использует только одну конфигурацию Bot, при условии, что Converter правильно установил `self.user_id`, фреймворк передаст его в качестве параметра `Using`. Адаптер должен обеспечить соответствие значения `self.user_id` с идентификатором поля в `AccountConfigClass` (например, `bot_id`), чтобы `_resolve_account()` корректно находил нужный аккаунт. Если `self.user_id` пуст, фреймворк не вызовет `Using`, и в этом случае `call_api` получит `account_id` со значением `None`, а `_resolve_account(None)` вернет первый включенный аккаунт.

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
        return self._error_response("Ошибка сетевого запроса", 33000)
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}")
        return self._error_response(str(e), 34000)
```

> **Обратная совместимость**: Старый код адаптера, использующий напрямую `aiohttp.ClientSession`, не затрагивается и по-прежнему может перехватывать `aiohttp.ClientError`. Оба способа могут сосуществовать. Рекомендуется использовать `sdk.client` + систему исключений ErisPulse для нового кода.

## Управление состоянием бота

AdapterManager содержит встроенную систему отслеживания состояния бота, которая автоматически поддерживает онлайн-статус, время активности и метаданные всех зарегистрированных ботов.

### Автоматическая система обнаружения

Когда адаптер отправляет событие через `adapter.emit()`, фреймворк автоматически проверяет поле `self` в событии:

- **Мета-события**: выполнение соответствующих операций в зависимости от `detail_type` (connect - регистрация / disconnect - отмечает как оффлайн / heartbeat - обновляет время активности)
- **Обычные события** (message/notice/request): автоматически обнаруживает бота и обновляет время активности

```python
# Все события, содержащие поле self, запускают автоматическую систему обнаружения
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
| `connect` | Бот подключается | Регистрирует бота и вызывает событие жизненного цикла `adapter.bot.online` |
| `disconnect` | Бот отключается | Отмечает бота как оффлайн и вызывает событие жизненного цикла `adapter.bot.offline` |
| `heartbeat` | Пульс бота | Обновляет время активности и метаданные бота |

### Отправка мета-событий адаптером

Использование `emit_meta()` позволяет отправить мета-событие одной строкой:

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # Отправка события connect одной строкой
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

### Расширенная информация в поле `self`

Поле `self` помимо обязательных `platform` и `user_id` поддерживает следующие необязательные поля:

| Поле | Описание |
|---|---|
| `user_name` | Имя пользователя бота |
| `nickname` | Никнейм бота |
| `avatar` | URL аватара бота |
| `account_id` | Идентификатор многоконтурного аккаунта |

### Запрос состояния бота

```python
from ErisPulse import sdk

# Получение информации о конкретном боте
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# Получение списка всех ботов
all_bots = sdk.adapter.list_bots()

# Получение списка ботов на определённой платформе
platform_bots = sdk.adapter.list_bots("myplatform")

# Проверка, находится ли бот онлайн
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Получение полной сводки состояния (подходит для отображения в WebUI)
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Подписка на события жизненного цикла бота

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

## Связанные документы

- [Введение в разработку адаптеров](getting-started.md) - Создание первого адаптера
- [Подробное руководство SendDSL](send-dsl.md) - Изучение отправки сообщений
- [Рекомендации по разработке адаптеров](best-practices.md) - Разработка высококачественных адаптеров

Пожалуйста, верните непосредственно переведённый полный Markdown-контент, не добавляя никаких других текстов.