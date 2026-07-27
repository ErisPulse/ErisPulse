# Основные концепции адаптера

Понимание основных концепций адаптера ErisPulse является основой для разработки адаптеров.

## Архитектура адаптера

### Отношения между компонентами

```
Прямое преобразование (направление получения)                           Обратное преобразование (направление отправки)
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ Платформо-специфичное событие     │                        │ Сообщение, сформированное модулем     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  Адаптер (MyAdapter) │   │ Send.Raw_ob12()  │
│  Converter       │   │ ┌──────────────┐ │   │ (точка входа обратного преобразования)   │
│  (конвертер событий)    │──→│ │              │ │   │                  │
│                  │   │ │              │ │   └────────┬─────────┘
└──────────────────┘   │ └──────────────┘ │            │
                       └──────────────────┘            ↓
                                │              ┌──────────────────┐
                       ┌──────────────────┐    │ Вызов API платформы    │
                       │ Стандартное событие OneBot12 │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                │              ┌──────────────────┐
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
- **Прямое преобразование** (Converter): платформо-специфичное событие → стандартное событие OneBot12, оригинальные данные сохраняются в `{platform}_raw`
- **Обратное преобразование** (Raw_ob12): сегмент сообщения OneBot12 → вызов API платформы, возвращается стандартный формат ответа

## AdapterManager (менеджер адаптеров)

`AdapterManager` является основным компонентом системы адаптеров ErisPulse, отвечающим за управление регистрацией, запуском, остановкой и распределением событий всех платформо-специфичных адаптеров.

### Основные функции

- **Регистрация адаптеров**: регистрация и управление несколькими платформо-специфичными адаптерами
- **Управление жизненным циклом**: контроль запуска и остановки адаптеров
- **Распределение событий**: распределение стандартных событий OneBot12 и платформо-специфичных событий
- **Управление конфигурацией**: управление состоянием включения/отключения адаптеров
- **Поддержка промежуточного ПО**: поддержка промежуточного ПО для событий OneBot12

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
# Или через доступ по свойству
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

1. Выполняется событие жизненного цикла `adapter.start`
2. Выполняется событие `adapter.status.change` (starting)
3. Параллельный запуск каждого адаптера
4. Если запуск не удался, автоматическая повторная попытка (стратегия экспоненциальной задержки)
5. После успешного запуска выполняется событие `adapter.status.change` (started)

**Механизм повторных попыток:**

- Первые 4 попытки: 60 секунд, 10 минут, 30 минут, 60 минут
- Пятая и последующие попытки: фиксированный интервал в 3 часа

#### Остановка адаптера

```python
# Остановка всех адаптеров
await sdk.adapter.shutdown()
```

**Процесс остановки:**

1. Выполняется событие жизненного цикла `adapter.stop`
2. Вызывается метод `shutdown()` для всех адаптеров
3. Останавливается сервер маршрутизации
4. Очищаются обработчики событий
5. Выполняется событие жизненного цикла `adapter.stopped`

### Управление конфигурацией

#### Проверка статуса платформы

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

# Получение списка всех платформ и их статусов
status_dict = sdk.adapter.list_items()
# Возвращает: {"platform1": true, "platform2": false, ...}

# Получение списка включенных платформ
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### Подписка на события

#### Стандартные события OneBot12

```python
from ErisPulse import sdk

# Подписка на стандартные сообщения от всех платформ
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"Получено сообщение OneBot12: {data}")

# Подписка на стандартные сообщения от указанной платформы
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"Получено сообщение myplatform: {data}")

# Подписка на все события
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"Получено событие: {data.get('type')}")
```

#### Платформо-специфичные события

```python
# Подписка на платформо-специфичное событие
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"Получено платформо-специфичное событие: {data}")

# Подписка на платформо-специфичные события всех платформ (шаблон)
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"Получено платформо-специфичное событие: {data}")
```

#### Механизм распределения событий

При вызове `adapter.emit(event_data)`:

1. **Обработка промежуточного ПО**: сначала выполняются все промежуточные обработчики OneBot12
2. **Распределение стандартных событий**: распределяются к соответствующим обработчикам стандартных событий OneBot12
3. **Распределение платформо-специфичных событий**: если есть оригинальные данные, распределяются к обработчикам платформо-специфичных событий

**Правила сопоставления:**

- Точное сопоставление: `@sdk.adapter.on("message")` только для события `message`
- Шаблон: `@sdk.adapter.on("*")` для всех событий
- Фильтрация по платформе: `platform="myplatform"` только для событий указанной платформы

### Промежуточное ПО

#### Добавление промежуточного ПО

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """Промежуточное ПО для логирования"""
    print(f"Обработка события: {data.get('type')}")
    return data  # Обязательно вернуть данные

@sdk.adapter.middleware
async def filter_middleware(data):
    """Промежуточное ПО для фильтрации событий"""
    # Фильтрация ненужных событий
    if data.get("type") == "notice":
        return None  # При возврате None промежуточное ПО игнорирует результат и сохраняет исходные данные для продолжения передачи
    return data  # Обязательно вернуть данные для продолжения передачи
```

#### Порядок выполнения промежуточного ПО

Промежуточное ПО выполняется в порядке регистрации, последний зарегистрированный промежуточное ПО выполняется первым.

> **Важно**: если промежуточное ПО возвращает `None` (например, забыли `return data`), фреймворк игнорирует этот результат и сохраняет исходные данные для продолжения передачи, при этом выводится предупреждение уровня warning. Это гарантирует, что ошибка в одном промежуточном ПО не приведет к прерыванию всей цепочки событий.

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

#### Доступ по свойству

```python
# Доступ по имени свойства (без учета регистра)
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter (базовый класс)

### Основная структура

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """Конфигурация адаптера (объявление автоматически управляет фреймворком)"""
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
    # - self.cfg (типобезопасный экземпляр конфигурации, чтение в реальном времени)
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
        cfg = self.cfg  # Типобезопасно, чтение в реальном времени
        if not cfg.token:
            raise ValueError("Токен не настроен")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### Конфигурация для нескольких аккаунтов

Базовый класс `BotAccountConfig` предоставляет поля `enabled` и `name`. Большинство адаптеров могут автоматически получать bot_id из платформенного протокола или ответа на вход, вставляя его в конфигурацию аккаунта при преобразовании событий.：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

# Большинство адаптеров: bot_id получается во время выполнения, не требует настройки
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

#### Соглашения по metadata

Поле metadata одновременно используется для генерации комментариев TOML и отображения веб-формы UI:

```python
metadata = {
    "description": str | dict,  # Описание поля (поддержка i18n)
    "required": bool,         # Обязательно ли поле (проверка + метка обязательного поля в UI)
    "secret": bool,           # Секретное ли поле (отображается как *** в UI, маскируется в логах)
    "ui": {                   # Конфигурация элемента управления UI (старое имя "webui" по-прежнему совместимо)
        "widget": str,        # Тип элемента управления: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # Группа: "basic" | "advanced" | "connection" и т.д.
        "order": int,         # Вес сортировки (чем меньше, тем ближе)
        "options": list,      # Варианты для элемента select [{label, value}], label поддерживает i18n
        "placeholder": str | dict,  # Подсказка в поле ввода (поддержка i18n)
    },
    "extra": dict,            # Дополнительные расширенные поля (передаются в schema)
}
```

Все пользовательские текстовые поля поддерживают i18n, используя единый формат `{"i18n": "key", "default": "text"}`,
чистые строки передаются без изменений (для обратной совместимости). Поддерживаемые поля i18n:

| Поле | Позиция | Описание |
|------|------|------|
| `description` | metadata поля | Описание поля |
| `options[].label` | `ui.options` | Метка опций для элемента select |
| `placeholder` | `ui.placeholder` | Подсказка в поле ввода |
| `group_labels` | `_schema_meta` | Название группы (заголовок раздела в Dashboard) |

При использовании i18n необходимо заранее зарегистрировать ключи перевода в системе i18n (см. [документацию по i18n](../../advanced/i18n.md#конфигурационные_поля_многоязычие)).

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

Метод `resolve_config_schema()` фреймворка автоматически разрешает все вышеуказанные поля i18n в зависимости от текущего языка;
`get_config_schema()` передает i18n-словарь без изменений, и фронтенд сам разбирает его.

### Декларативные ключи перевода (v2.7.0+)

Адаптер может объявлять ключи перевода, как и `ConfigClass`, с помощью вложенного класса `I18nClass`. Фреймворк автоматически зарегистрирует все объявленные ключи перевода на этапе `__init__` (до генерации шаблона конфигурации),
обеспечивая доступность ключей перевода, используемых в описании конфигурации, при генерации шаблона.

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="Адрес API",
            zh_TW="API 地址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="Адрес API",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="Токен платформы",
            zh_TW="平台權杖",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> ``I18nKey.default`` — это **безопасный текст без привязки к языку**, который не регистрируется ни в одном языке.
> Чтобы перевод был активен, необходимо явно передать хотя бы один параметр языка.

Детальное использование (правила путей ключей, явный параметр key и т.д.) см. в [документации по i18n](../../advanced/i18n.md#рекомендуемый_способ_объявления_ключей_перевода_через_i18nclass_v270).

#### Разрешение аккаунта

Многоаккаунтный адаптер может использовать `_resolve_account()` для автоматического разрешения целевого аккаунта:

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: имя аккаунта, account: экземпляр конфигурации
```

Стратегия разрешения: сопоставление по имени аккаунта → сопоставление по полю `bot_id` → сопоставление по другим строковым полям → первый включенный аккаунт.

#### Горячая замена конфигурации

Подклассы могут переопределять `on_config_update()` для реакции на изменения конфигурации:

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Токен обновлен, будет выполнено повторное подключение")
```

### Процесс инициализации

Фреймворк автоматически выполняет следующие действия в `BaseAdapter.__init__(self, sdk=None)`:

1. **Ссылка на SDK**: установка `self.sdk`, `self.logger`
2. **Фабрика Send/Request**: создание `self.Send` и `self.Request`
3. **Шаблон конфигурации**: если объявлен `ConfigClass`, автоматически генерируется шаблон конфигурации (в первый раз)
4. **Шаблон аккаунта**: если объявлен `AccountConfigClass`, автоматически генерируется шаблон аккаунта (в первый раз)

Конфигурация читается в реальном времени через `self.cfg` / `self.accounts` (каждый доступ читает последнее значение из хранилища конфигурации). `self.config` как совместимый псевдоним `self.cfg` все еще доступен.

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
        """Вложенный класс Send, наследующийся от BaseAdapter.Send"""
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
| `_adapter` | Экземпляр адаптера | Автоматически установлено |
| `_at_user_ids` | Список пользователей для упоминания | `At(user_id)` |
| `_reply_message_id` | Идентификатор сообщения для ответа | `Reply(message_id)` |
| `_at_all` | Упоминание всех пользователей | `AtAll()` |

> **Рекомендуется**: использовать свойство `self.send_context` для получения `target_type`, `target_id`, `account_id` за один раз, это более ясно, чем прямой доступ к экземплярным переменным.

### Вспомогательные методы фреймворка

| Метод/Свойство | Описание |
|-----------|------|
| `self._apply_modifiers(message)` | Объединение состояний модификаторов At/AtAll/Reply в список сегментов сообщения |
| `self.send_context` | Возвращает словарь `{target_type, target_id, account_id}` |

### Основные методы

Адаптер должен реализовать только `Raw_ob12`, стандартные методы (Text/Image/Voice/Video/File) уже наследуются от базового класса `SendDSL` и по умолчанию делегируются ему:

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """Обязательно реализовать: сегменты OneBot12 → вызов API платформы"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File уже наследуются от базового класса, автоматически делегируются Raw_ob12, не нужно повторно реализовывать
    # Если нужна платформо-специфическая логика, можно переопределить отдельный метод:
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
Оригинальное событие платформы
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
        """Преобразование платформо-специфичного события в стандартный формат OneBot12"""
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
        """WebSocket аутентификация"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook подключение

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """Регистрация HTTP маршрута WebHook"""
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

> **Информация о маршрутах**: маршруты, зарегистрированные адаптером (HTTP, WebSocket, SSE), можно запросить с помощью `sdk.adapter.get_connection_info(platform)` и `sdk.router.get_module_urls(module_name)` для получения полного адреса подключения (включая `base_url` + путь). Подробнее см. [Введение в разработку адаптеров - Информация о подключении и обнаружение маршрутов](getting-started.md#9-информация_о_подключении_и_обнаружение_маршрутов) и [Поддержка SSE](getting-started.md#10-sse-server-sent-events-поддержка).

## Стандартные ответы API

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
        # Использование account.token, account.bot_id и т.д.
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

### Отношение между self.user_id и Using

Механизм ответа событий фреймворка автоматически извлекает `account_id` (приоритет) или `user_id` из поля `self` события, передавая его в качестве параметра `Using`. Разработчикам адаптеров необходимо убедиться, что Converter правильно устанавливает значение `self.user_id`, чтобы `_resolve_account()` мог правильно сопоставить аккаунт.

**Внутреннее поведение фреймворка** (`Event._get_adapter_and_target`):

```python
# Логика извлечения bot_id фреймворком
bot_id = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# Вызывается Using только при непустом bot_id
if bot_id:
    send_chain = send_chain.Using(bot_id)
```

> **Ключевой момент**: даже если адаптер использует только одну конфигурацию бота, если Converter правильно устанавливает `self.user_id`, фреймворк будет передавать его как параметр `Using`. Адаптер должен убедиться, что значение `self.user_id` совпадает с идентификатором поля в `AccountConfigClass` (например, `bot_id`), чтобы `_resolve_account()` мог правильно сопоставить аккаунт. Если `self.user_id` пуст, фреймворк не вызывает `Using`, и в этом случае `call_api` получает `account_id` как `None`, а `_resolve_account(None)` возвращает первый включенный аккаунт.

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

> **Обратная совместимость**: код старых адаптеров, использующих `aiohttp.ClientSession`, не затрагивается и по-прежнему может перехватывать `aiohttp.ClientError`. Оба способа могут сосуществовать. Рекомендуется использовать `sdk.client` + исключительную систему ErisPulse в новом коде.

## Управление состоянием бота

AdapterManager включает систему отслеживания состояния ботов, автоматически поддерживающую онлайн-статус, время активности и метаинформацию для всех зарегистрированных ботов.

### Автоматическая обнаружение

Когда адаптер отправляет событие через `adapter.emit()`, фреймворк автоматически проверяет поле `self` в событии:

- **Meta события**: в зависимости от `detail_type` выполняются соответствующие операции (connect регистрирует / отмечает отключение как оффлайн / heartbeat обновляет время активности)
- **Обычные события** (message/notice/request): автоматически обнаруживаются боты и обновляется время активности

```python
# Все события с полем self автоматически запускают автоматическую обнаружку
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Бот "bot123" автоматически зарегистрирован (если появился впервые) и обновлено время активности
```

### Типы meta событий

| `detail_type` | Описание | Поведение фреймворка |
|---|---|---|
| `connect` | Бот подключился | Регистрация бота и запуск события жизненного цикла `adapter.bot.online` |
| `disconnect` | Бот отключился | Отметка бота как оффлайн и запуск события жизненного цикла `adapter.bot.offline` |
| `heartbeat` | Бот отправил heartbeat | Обновление времени активности и метаинформации бота |

### Отправка meta событий адаптером

Использование `emit_meta()` позволяет отправить meta событие одной строкой:

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

### Расширение поля self

Поле self помимо обязательных `platform` и `user_id` поддерживает следующие необязательные поля:

| Поле | Описание |
|---|---|
| `user_name` | Имя пользователя бота |
| `nickname` | Никнейм бота |
| `avatar` | URL аватара бота |
| `account_id` | Идентификатор аккаунта |

### Запрос состояния бота

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

# Получение полного сводного состояния (подходит для отображения в WebUI)
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### Подписка на жизненный цикл бота

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

- [Введение в разработку адаптеров](docs/ru/getting-started.md) - Создание первого адаптера
- [SendDSL подробно](docs/ru/send-dsl.md) - Изучение отправки сообщений
- [Лучшие практики разработки адаптеров](docs/ru/best-practices.md) - Разработка высококачественных адаптеров