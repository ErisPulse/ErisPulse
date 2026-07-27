# Основные концепции модуля

Понимание основных концепций модуля ErisPulse — это основа для разработки качественных модулей.

## Жизненный цикл модуля

### Стратегия загрузки

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """Возвращает стратегию загрузки модуля"""
        return ModuleLoadStrategy(
            lazy_load=True,   # Ленивая загрузка или немедленная загрузка
            priority=0,       # Приоритет загрузки (чем больше число, тем раньше загружается)
            depends=["OtherModule"]  # Необязательно: объявление зависимых модулей
        )
```

> Если модули, объявленные в `depends`, не зарегистрированы, текущий модуль будет пропущен с записью предупреждения. Порядок загрузки определяется топологической сортировкой; модули одного уровня упорядочиваются в порядке убывания `priority`.

### Метод on_load

Вызывается при загрузке модуля, используется для инициализации ресурсов и регистрации обработчиков событий:

```python
async def on_load(self, event):
    # Регистрация обработчика событий
    @command("hello", help="Команда приветствия")
    async def hello_handler(event):
        await event.reply("Привет!")
    
    # Использование встроенного HTTP-клиента SDK (автоматическое управление пулом соединений, создание сессии вручную не требуется)
    # Запросы отправляются через sdk.client
```

### Метод on_unload

Вызывается при卸ождении модуля, используется для очистки ресурсов:

```python
async def on_unload(self, event):
    # Очистка пользовательских ресурсов
    # sdk.client управляется фреймворком, вручную закрывать его не нужно
    
    # Отмена регистрации обработчиков событий (фреймворк обрабатывает это автоматически)
    self.logger.info("Модуль был выгружен")
```

## Объекты SDK

### Доступ к основным модулям

```python
from ErisPulse import sdk

# Доступ ко всем основным модулям через объект sdk
sdk.logger.info("Лог")
sdk.storage.set("key", "value")
config = sdk.config.getConfig("MyModule")
```

### Взаимодействие между модулями

```python
# Доступ к другим модулям
other_module = sdk.OtherModule
result = await other_module.some_method()
```

## Запросы методов отправки адаптером

Из-за новых стандартов, требующих реализации механизма отправки «на всякий случай» путем переопределения метода `__getattr__`, невозможно использовать метод `hasattr` для проверки существования методов. Начиная с версии `2.3.5`, добавлена функция запроса методов отправки.

### Перечисление поддерживаемых методов отправки

```python
# Вывод всех методов отправки, поддерживаемых платформой
methods = sdk.adapter.list_sends("onebot11")
# Возвращает: ["Text", "Image", "Voice", "Markdown", ...]
```

### Получение подробной информации о методе

```python
# Получение подробной информации о конкретном методе
info = sdk.adapter.send_info("onebot11", "Text")
# Возвращает:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "Отправка текстовых сообщений..."
# }
```

## Управление конфигурацией

### Декларативная конфигурация (рекомендуется)

Начиная с v2.5.2, модули могут объявлять классы конфигурации через `ConfigClass`, используя ту же систему схем конфигурации, что и адаптеры. Конфигурация читается в реальном времени через `self.cfg` и вступает в силу сразу после изменений:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime.config_schema import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_module.api_key", "default": "API ключ"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )
    timeout: int = field(
        default=30,
        metadata={
            "description": {"i18n": "my_module.timeout", "default": "Время ожидания (сек)"},
            "ui": {"widget": "number", "group": "advanced", "order": 2},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def on_load(self, event):
        self.logger.info("Модуль был загружен")

    async def on_unload(self, event):
        pass

    async def do_something(self):
        cfg = self.cfg  # Чтение в реальном времени, типобезопасно
        api_key = cfg.api_key
        timeout = cfg.timeout
```

`BaseConfig` — это базовый класс конфигурации общего назначения, подходит для адаптеров, модулей, внешних проектов и любых сценариев. Поля конфигурации поддерживают многоязычные описания i18n (см. [документацию i18n](../../advanced/i18n.md#поля-конфигурации-многоязычные)).

### Декларативные ключи перевода (v2.7.0+)

Начиная с v2.7.0, модули могут также централизованно объявлять ключи перевода через вложенный класс `I18nClass`, так же как и `ConfigClass`. Фреймворк будет **автоматически регистрировать** все объявленные ключи перевода при загрузке; вручную вызывать `i18n.register()` не требуется, а момент регистрации наступает до генерации шаблонов конфигурации, что гарантирует, что ключи i18n, используемые в описаниях конфигурации, уже доступны.

```python
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey

class MyModule(BaseModule):
    # Класс конфигурации (необязательно)
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="Welcome",
            metadata={
                "description": {"i18n": "mymodule.welcome_msg", "default": "Приветственное сообщение"},
            },
        )

    # Класс набора ключей перевода (необязательно)
    class I18nClass(BaseI18n):
        # Имена атрибутов автоматически объединяются в полный путь ключа: <имя_модуля>.<имя_атрибута>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # языконезависимое fallback-значение
            zh_CN="Приветственное сообщение",
            zh_TW="Приветственное сообщение",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
        )
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="Привет, {name}!",
            zh_TW="Привет, {name}!",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )
```

Подробнее см. [рекомендуемый способ написания i18n](../../advanced/i18n.md#рекомендуемый-способ-через-i18nclass-объявление-ключей-перевода-v270).

### Ручное чтение конфигурации (совместимый способ)

Если не используется декларативная конфигурация, можно напрямую считывать и записывать хранилище конфигурации:

```python
def _load_config(self):
    config = self.sdk.config.getConfig("MyModule")
    if not config:
        default_config = {
            "api_key": "",
            "timeout": 30
        }
        self.sdk.config.setConfig("MyModule", default_config)
        return default_config
    return config
```

> **Примечание**. В ручном способе избегайте использования `self.config` в качестве имени атрибута, рекомендуется использовать `self.cfg` или другое пользовательское имя, чтобы избежать конфликта с будущими атрибутами фреймворка.

## Система хранения

### Базовое использование

```python
# Хранение данных
sdk.storage.set("user:123", {"name": "Zhang San"})

# Получение данных
user = sdk.storage.get("user:123", {})

# Удаление данных
sdk.storage.delete("user:123")
```

### Использование транзакций

```python
# Использование транзакций для обеспечения целостности данных
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # Если какая-либо операция не удалась, все изменения будут откатаны
```

## Обработка событий

### Регистрация обработчиков событий

```python
from ErisPulse.Core.Event import command, message

# Регистрация команды
@command("info", help="Получение информации")
async def info_handler(event):
    await event.reply("Это информация")

# Регистрация обработчика сообщений
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"Получено групповое сообщение: {event.get_text()}")
```

### Жизненный цикл обработчиков событий

Фреймворк автоматически управляет регистрацией и отменой регистрации обработчиков событий, вам нужно зарегистрировать их только в `on_load`.

## Механизм отложенной загрузки

### Как это работает

```python
# Модуль инициализируется только при первом обращении к нему
result = await sdk.my_module.some_method()
# ↑ Это запускает инициализацию модуля
```

### Немедленная загрузка

Для модулей, требующих немедленной инициализации (например, прослушиватели, таймеры):

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=False,  # Немедленная загрузка
        priority=100
    )
```

## Обработка ошибок

### Перехват исключений

```python
async def handle_event(self, event):
    try:
        # Бизнес-логика
        await self.process_event(event)
    except ValueError as e:
        self.logger.warning(f"Ошибка параметра: {e}")
        await event.reply(f"Ошибка параметра: {e}")
    except Exception as e:
        self.logger.error(f"Не удалось обработать: {e}")
        raise
```

### Логирование

```python
# Использование различных уровней логирования
self.logger.debug("Отладочная информация")    # Подробные отладочные данные
self.logger.info("Состояние работы")      # Информация о нормальном выполнении
self.logger.warning("Предупреждение")  # Информация о предупреждении
self.logger.error("Ошибка")    # Информация об ошибке
self.logger.critical("Критическая ошибка") # Критическая ошибка
```

## Связанные документы

- [Модуль для начинающих](getting-started.md) - Создание первого модуля
- [Класс-обертка события](event-wrapper.md) - Подробное описание обработки событий
- [Лучшие практики](best-practices.md) - Разработка качественных модулей