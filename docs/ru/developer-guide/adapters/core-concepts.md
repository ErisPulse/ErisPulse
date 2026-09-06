# Основные понятия адаптера

Понимание основных понятий адаптера ErisPulse является основой для разработки адаптеров.

## Архитектура адаптера

### Отношения между компонентами

```
Прямое преобразование (направление получения)           Обратное преобразование (направление отправки)
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ События платформы │                        │ Сообщения модуля │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ Адаптер (MyAdapter) │   │                  │
│ Преобразователь │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│ (конвертер)      │──→│ │              │ │   │ (входная точка  │
│                  │   │ │              │ │   │ обратного преобразования) │
└──────────────────┘   │ └──────────────┘ │   │                  │
                       └──────────────────┘   └────────┬─────────┘
                                │                      │
                                ↓                      ↓
                       ┌──────────────────┐    ┌──────────────────┐
                       │ События стандарта │    │ Вызов API платформы │
                       │ OneBot12         │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ Стандартный формат │
                       │ Система событий   │    │ ответа           │
                       └────────┬─────────┘    └──────────────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ Модуль (обработка │
                       │ событий)         │
                       └──────────────────┘
```

**Основная симметрия**:
- **Прямое преобразование** (Converter): События платформы → События стандарта OneBot12, исходные данные сохраняются в `{platform}_raw`
- **Обратное преобразование** (Raw_ob12): Сегменты сообщений OneBot12 → Вызов API платформы, возвращается стандартный формат ответа

## AdapterManager адаптер-менеджер

`AdapterManager` — это основной компонент адаптерной системы ErisPulse, отвечающий за управление регистрацией, запуском, остановкой и рассылкой событий всех адаптеров платформ.

### Основные функции

- **Регистрация адаптеров**: Регистрация и управление несколькими адаптерами платформ
- **Управление жизненным циклом**: Управление запуском и остановкой адаптеров
- **Рассылка событий**: Рассылка событий по стандарту OneBot12 и событий оригинальных платформ
- **Управление конфигурацией**: Управление включением/отключением адаптеров
- **Поддержка промежуточных обработчиков (middleware)**: Поддержка промежуточных обработчиков событий OneBot12

### Основное использование

```python
from ErisPulse import sdk

# Регистрация адаптера (обычно выполняется автоматически Loader)
sdk.adapter.register("myplatform", MyPlatformAdapter)

# Запуск всех адаптеров
await sdk.adapter.startup()

# Запуск определённого адаптера
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

#### Запуск адаптеров

```python
# Запуск всех зарегистрированных адаптеров
await sdk.adapter.startup()

# Запуск определённых платформ
await sdk.adapter.startup(["platform1", "platform2"])
```

**Процесс запуска:**

1. Отправка события жизненного цикла `adapter.start`
2. Отправка события `adapter.status.change` (starting)
3. Параллельный запуск каждого адаптера
4. При неудаче автоматическая повторная попытка (стратегия экспоненциальной задержки)
5. После успешного запуска отправка события `adapter.status.change` (started)

**Механизм повторных попыток:**

- Первые 4 попытки: 60 секунд, 10 минут, 30 минут, 60 минут
- С пятой и далее: фиксированная задержка в 3 часа

#### Остановка адаптеров

```python
# Остановка всех адаптеров
await sdk.adapter.shutdown()
```

**Процесс остановки:**

1. Отправка события жизненного цикла `adapter.stop`
2. Вызов метода `shutdown()` всех адаптеров
3. Остановка сервера маршрутизации
4. Очистка обработчиков событий
5. Отправка события жизненного цикла `adapter.stopped`

### Управление конфигурацией

#### Проверка состояния платформ

```python
# Проверка наличия платформы
exists = sdk.adapter.exists("myplatform")

# Проверка включения платформы
enabled = sdk.adapter.is_enabled("myplatform")

# Использование оператора in
if "myplatform" in sdk.adapter:
    print("Платформа существует и включена")
```

#### Список платформ

```python
# Получение списка всех зарегистрированных платформ
platforms = sdk.adapter.list_registered()

# Получение списка всех платформ и их статусов
status_dict = sdk.adapter.list_items()
# Возвращает: {"platform1": true, "platform2": false, ...}

# Получение списка включённых платформ
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### Слушатели событий

#### Стандартные события OneBot12

```python
from ErisPulse import sdk

# Слушатель всех стандартных событий сообщений OneBot12
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Получено событие OneBot12: {data}")

# Слушатель стандартных событий сообщений для определённой платформы
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"Получено событие myplatform: {data}")

# Слушатель всех событий
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"Получено событие: {data.get('type')}")
```

#### Оригинальные события платформ

```python
# Слушатель оригинальных событий для определённой платформы
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Получено оригинальное событие: {data})

# Слушатель всех оригинальных событий (с использованием шаблона)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Получено оригинальное событие: {data})
```

#### Механизм рассылки событий

При вызове `adapter.emit(event_data)`:

1. **Обработка промежуточными обработчиками**: Сначала выполняются все промежуточные обработчики OneBot12
2. **Рассылка стандартных событий**: Рассылка на соответствующие обработчики стандартных событий
3. **Рассылка оригинальных событий**: Если есть оригинальные данные, рассылка на обработчики оригинальных событий

**Правила сопоставления:**

- Точное сопоставление: `@sdk.adapter.on("message")` сопоставляется только с событием `message`
- Шаблон: `@sdk.adapter.on("*")` сопоставляется со всеми событиями
- Фильтрация по платформе: `platform="myplatform"` сопоставляется только с событиями определённой платформы

### Промежуточные обработчики (middleware)

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
        return None  # При возврате None промежуточная цепочка пропускает результат, оставляя исходные данные для передачи
    return data  # Обязательно вернуть данные для продолжения передачи
```

#### Порядок выполнения промежуточных обработчиков

Промежуточные обработчики выполняются в порядке их регистрации, последние зарегистрированные обработчики выполняются первыми.

> **Важно**: Если промежуточный обработчик возвращает `None` (например, забыл `return data`), фреймворк игнорирует этот результат и продолжает передачу исходных данных, выводя предупреждение уровня warning. Это гарантирует, что ошибка одного промежуточного обработчика не приведёт к прерыванию всей цепочки событий.

```python
# Порядок регистрации
sdk.adapter.middleware(middleware1)  # Выполняется последним
sdk.adapter.middleware(middleware2)  # Выполняется посередине
sdk.adapter.middleware(middleware3)  # Выполняется первым

# Порядок выполнения: middleware3 -> middleware2 -> middleware1
```

### Получение экземпляра адаптера

#### Метод `get()`

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### Доступ через атрибуты

```python
# Доступ по имени атрибута (регистронезависимый)
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
    """Конфигурация адаптера (объявляется, а затем автоматически управляется фреймворком)"""
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
    # - self.cfg (типобезопасный экземпляр конфигурации, в реальном времени)
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

Фреймворк предоставляет декларативное управление конфигурацией, определяя структуру конфигурации через dataclass. Фреймворк автоматически обрабатывает загрузку, проверку и генерацию шаблонов.

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
        cfg = self.cfg  # Типобезопасная, в реальном времени
        if not cfg.token:
            raise ValueError("Не настроен токен")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Конфигурация нескольких аккаунтов

Базовый класс `BotAccountConfig` предоставляет поля `enabled` и `name`. Большинство адаптеров могут автоматически получать `bot_id` из протокола платформы или ответа на вход, вставляя его в конфигурацию аккаунта во время преобразования событий.

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# Большинство адаптеров: bot_id получается во время выполнения, не требуется конфигурация
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
    "required": bool,         # Обязательно ли заполнять (проверка + метка обязательного поля в веб-интерфейсе)
    "secret": bool,           # Является ли чувствительным (веб-интерфейс отображает как ***; в логах маскируется)
    "ui": {                   # Конфигурация элемента управления веб-интерфейса (старое имя "webui" по-прежнему поддерживается)
        "widget": str,        # Тип элемента: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Группа: "basic" | "advanced" | "connection" и т.д.
        "order": int,         # Вес сортировки (чем меньше, тем выше)
        "options": list,      # Доступные опции для элемента select [{label, value}], label поддерживает i18n
        "placeholder": str | dict,  # Подсказка в поле ввода (поддержка i18n)
    },
    "extra": dict,            # Дополнительные расширенные поля (прозрачно передаются в schema)
}
```

Все пользовательские текстовые поля поддерживают i18n, используя единый формат `{"i18n": "key", "default": "текст"}`,
чистые строки передаются без изменений (для обратной совместимости). Поддерживаемые поля i18n:

| Поле | Местоположение | Описание |
|------|----------------|----------|
| `description` | metadata поля | Описание поля |
| `options[].label` | `ui.options` | Метки опций элемента select |
| `placeholder` | `ui.placeholder` | Подсказка в поле ввода |
| `group_labels` | `_schema_meta` | Названия групп (заголовки разделов Dashboard) |

Для использования i18n необходимо заранее зарегистрировать ключи перевода в системе i18n (см. [документацию по i18n](../../advanced/i18n.md#многоязычная-конфигурация-полей)).

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
                {"label": "Чистая строка метки", "value": "b"},  # Чистые строки передаются без изменений
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

Метод `resolve_config_schema()` фреймворка автоматически разрешает все перечисленные выше поля i18n на основе текущего языка;
`get_config_schema()` прозрачно передает словарь i18n, и интерфейс будет его обрабатывать самостоятельно.

### Декларативные ключи перевода (v2.7.0+)

Адаптер может объявлять ключи перевода через вложенный класс `I18nClass`, аналогично объявлению `ConfigClass`.
Фреймворк автоматически зарегистрирует все объявленные ключи перевода на этапе `__init__` (до генерации шаблона конфигурации),
обеспечивая доступность ключей i18n, используемых в описаниях конфигурации, при генерации шаблона.

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

> ``I18nKey.default`` — это **безязыковый резервный текст**, который не регистрируется ни в одном языке.
> Чтобы переводы вступили в силу, необходимо явно указать хотя бы один параметр языка.

Подробное использование (правила путей ключей, явный параметр key и т.д.) см. в [документации по i18n](../../advanced/i18n.md#рекомендуемый-способ-объявления-ключа-перевода-через-i18nclass-v270).

### Декларативные методы расширения событий (v2.7.0+)

Адаптер может объявлять методы расширения событий платформы в классе `EventMixin`, которые фреймворк автоматически зарегистрирует для текущей платформы.

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """Получение имени чата"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """Определение, является ли сообщение официальным"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

После регистрации эти методы можно вызывать напрямую на объектах событий:

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] Получено официальное сообщение")
```

> Методы расширения событий адаптера регистрируются для его собственной платформы (``self._platform``).
> Если модули нуждаются в расширении событий для разных платформ, следует использовать старый API ``register_event_mixin()``.

#### Разрешение аккаунта

Адаптеры с несколькими аккаунтами могут использовать `_resolve_account()` для автоматического разрешения целевого аккаунта:

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: имя аккаунта, account: экземпляр конфигурации
```

Стратегия разрешения: сопоставление по имени аккаунта → сопоставление по полю `bot_id` → сопоставление по другим строковым полям → первый включенный аккаунт.

#### Горячая перезагрузка конфигурации

Подклассы могут переопределить `on_config_update()` для реакции на изменения конфигурации:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Токен обновлен, будет повторное подключение")
```

### Процесс инициализации

Фреймворк автоматически выполняет следующие действия в `BaseAdapter.__init__(self, sdk=None)`:

1. **Ссылка на SDK**: Установка `self.sdk`, `self.logger`
2. **Фабрика Send/Request**: Создание `self.Send` и `self.Request`
3. **Шаблон конфигурации**: Если объявлен `ConfigClass`, автоматически генерируется шаблон конфигурации (впервые)
4. **Шаблон аккаунта**: Если объявлен `AccountConfigClass`, автоматически генерируется шаблон аккаунта (впервые)
5. **Регистрация EventMixin**: Если объявлен `EventMixin`, автоматически регистрируется после вставки платформенного имени в `AdapterManager`

Конфигурация читается через `self.cfg` / `self.accounts` в реальном времени (каждый доступ читает последнее значение из хранилища конфигурации). `self.config` как совместимый псевдоним `self.cfg` по-прежнему доступен.

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

При вызове класса `Send` автоматически устанавливаются следующие свойства:

| Свойство | Описание | Способ установки |
|-----|------|---------|
| `_target_id` | Идентификатор цели | `To(id)` или `To(type, id)` |
| `_target_type` | Тип цели | `To(type, id)` |
| `_target_to` | Упрощённый идентификатор цели | `To(id)` |
| `_account_id` | Идентификатор отправляющего аккаунта | `Using(account_id)` |
| `_adapter` | Экземпляр адаптера | Автоматически |
| `_at_user_ids` | Список упомянутых пользователей | `At(user_id)` |
| `_reply_message_id` | Идентификатор сообщения, на которое отвечаем | `Reply(message_id)` |
| `_at_all` | Упоминание всех пользователей | `AtAll()` |

> **Рекомендуется** использовать свойство `self.send_context` для получения `target_type`, `target_id`, `account_id` за один раз, это более понятно, чем прямой доступ к экземплярным переменным.

### Вспомогательные методы фреймворка

| Метод/Свойство | Описание |
|-----------|------|
| `self._apply_modifiers(message)` | Объединяет состояние модификаторов At/AtAll/Reply в список сообщений |
| `self.send_context` | Возвращает словарь `{target_type, target_id, account_id}` |

### Основные методы

Адаптеру нужно реализовать только `Raw_ob12`, стандартные методы (Text/Image/Voice/Video/File) уже унаследованы от базового класса `SendDSL` и по умолчанию делегируются ему:

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Необходимо реализовать: преобразование OneBot12-сегментов сообщения → API платформы"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Методы Text/Image/Voice/Video/File унаследованы от базового класса и автоматически делегируют Raw_ob12, повторно реализовывать не нужно
    # При необходимости специфической логики для платформы, можно переопределить отдельный метод:
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

## События преобразователя

### Процесс преобразования

```
Событие с платформы
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

### Пример преобразователя

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """Преобразует событие с платформы в стандартный формат OneBot12"""
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
```

## Управление подключениями

### WebSocket-соединение

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
        """Обработчик WebSocket-соединения"""
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

### WebHook-соединение

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

> **Информация о маршрутах**: маршруты, зарегистрированные адаптером (HTTP, WebSocket, SSE), можно получить с помощью `sdk.adapter.get_connection_info(platform)` и `sdk.router.get_module_urls(module_name)`, чтобы узнать полный адрес соединения (включая `base_url` + путь). Подробнее см. в [Введение в разработку адаптеров - Информация о соединении и обнаружение маршрутов](docs/ru/getting-started.md#9-连接信息与路由发现) и [Поддержка SSE](docs/ru/getting-started.md#10-sse-server-sent-events-支持).

## Стандарт ответа API

Фреймворк предоставляет методы `make_response()` и `make_error()` для построения стандартизированного ответа, что позволяет избежать ручного построения словаря ответа.

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

### Ручное построение ответа (устаревший способ, но по-прежнему поддерживается)

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

После использования `AccountConfigClass` для декларативной конфигурации класса, фреймворк автоматически управляет загрузкой, проверкой и шаблонной генерацией нескольких учетных записей:

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
            self.logger.info(f"Запуск учетной записи {name}: {account.bot_id}")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # Используем поля account.token, account.bot_id и т.д.
```

### Файл конфигурации учетных записей

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

### Отправка с указанием учетной записи

```python
# Используем метод Using для указания учетной записи
my_adapter = adapter.get("myplatform")

# Через self.user_id в событии (рекомендуется, наиболее универсально)
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# Через имя учетной записи
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### Отношение self.user_id и Using

Механизм ответа событий фреймворка автоматически извлекает `account_id` (в приоритете) или `user_id` из поля `self` события и передает его в качестве параметра `Using`. Разработчику адаптера необходимо обеспечить корректное соответствие значения `self.user_id` в Converter с идентификатором, используемым в `AccountConfigClass` (например, `bot_id`), чтобы `_resolve_account()` мог корректно найти соответствующую учетную запись.

**Внутреннее поведение фреймворка**:

```python
# Логика извлечения bot_id фреймворком
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Вызов Using только при непустом bot_id
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Ключевой момент**: Даже если адаптер использует только одну конфигурацию бота, при правильной настройке Converter для `self.user_id` фреймворк будет передавать его в качестве параметра `Using`. Разработчик адаптера должен обеспечить соответствие значения `self.user_id` с идентификатором, определенным в `AccountConfigClass` (например, `bot_id`), чтобы `_resolve_account()` мог корректно найти нужную учетную запись. Если `self.user_id` пуст, фреймворк не вызывает `Using`, и в `call_api` параметр `account_id` будет равен `None`, при этом `_resolve_account(None)` вернет первую включенную учетную запись.

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
        self.logger.error(f"Превышено время ожидания ответа: {endpoint}")
        return self._error_response("Превышено время ожидания ответа", 32000)
    except ClientError as e:
        self.logger.error(f"Ошибка сети: {e}")
        return self._error_response("Ошибка сети", 33000)
    except Exception as e:
        self.logger.error(f"Неизвестная ошибка: {e}")
        return self._error_response(str(e), 34000)
```

> **Обратная совместимость**: Старый код адаптера, использующий напрямую `aiohttp.ClientSession`, не затронут и по-прежнему может обрабатывать `aiohttp.ClientError`. Оба способа могут сосуществовать. Рекомендуется использовать `sdk.client` + исключения ErisPulse в новом коде.

## Управление состоянием бота

System отслеживания состояния адаптера (AdapterManager) автоматически поддерживает состояние онлайн, время активности и метаданные всех зарегистрированныанных ботов.

### Автоматическая система обнаружения

Когда адаптер отправляет событие через `adapter.emit()`, фреймворк автоматически проверяет поле `self` в событии:

- **Мета-события**: выполняются соответствующие действия в зависимости от `detail_type` (регистрация при подключении / отмечает как отключённый / обновляет время активности при heartbeat)
- **Обычные события** (message/notice/request): автоматически обнаруживаются боты и обновляется время активности

```python
# Все события, содержащие поле self, запускают автоматическую систему обнаружения
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Бот "bot123" автоматически зарегистрирован (если это первый раз) и обновлено время активности
```

### Типы мета-событий

| `detail_type` | Описание | Действие фреймворка |
|---|---|---|
| `connect` | Подключение бота | Регистрация бота и запуск цикла жизни `adapter.bot.online` |
| `disconnect` | Отключение бота | Отмечает бота как отключённый и запускает цикл жизни `adapter.bot.offline` |
| `heartbeat` | Heartbeat бота | Обновляет время активности и метаданные бота |

### Отправка мета-событий адаптером

Используйте `emit_meta()` для отправки мета-событий одной строкой:

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # Отправка события connect одной строкой
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="Мой бот")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

Также поддерживается ручное построение (старый способ всё ещё совместим):

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### Расширение поля `self`

Поле `self` помимо обязательных `platform` и `user_id` поддерживает следующие необязательные поля:

| Поле | Описание |
|---|---|
| `user_name` | Имя пользователя бота |
| `nickname` | Никнейм бота |
| `avatar` | URL аватара бота |
| `account_id` | Идентификатор для нескольких аккаунтов |

### Запрос состояния бота

```python
from ErisPulse import sdk

# Получение информации о боте
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# Получение списка всех ботов
all_bots = sdk.adapter.list_bots()

# Получение списка ботов определённой платформы
platform_bots = sdk.adapter.list_bots("myplatform")

# Проверка, находится ли бот онлайн
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# Получение полного сводного состояния (подходит для отображения в WebUI)
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
    sdk.logger.info(f"Бот в сети: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Бот отключён: {platform}/{bot_id}")
```

## Связанные документы

- [Введение в разработку адаптеров](docs/ru/getting-started.md) - Создание первого адаптера
- [Подробности SendDSL](docs/ru/send-dsl.md) - Изучение отправки сообщений
- [Лучшие практики адаптеров](docs/ru/best-practices.md) - Разработка качественных адаптеров