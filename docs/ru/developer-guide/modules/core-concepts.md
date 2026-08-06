# Основные концепции модуля

Понимание основных концепций модуля ErisPulse является основой для разработки высококачественных модулей.

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
            lazy_load=True,   # отложенная или немедленная загрузка
            priority=0,       # приоритет загрузки (чем больше число, тем выше приоритет)
            depends=["OtherModule"]  # необязательно: объявление других модулей, от которых зависит текущий
        )
```

> Если модули, объявленные через `depends`, не зарегистрированы, текущий модуль будет пропущен, и будет выведено предупреждение. Порядок загрузки определяется топологической сортировкой, для модулей одного уровня — по убыванию `priority`.

### Метод on_load

Вызывается при загрузке модуля, используется для инициализации ресурсов и регистрации обработчиков событий:

```python
async def on_load(self, event):
    # Регистрация обработчика команд
    @command("hello", help="команда приветствия")
    async def hello_handler(event):
        await event.reply("Привет!")
    
    # Использование встроенного HTTP-клиента SDK (автоматическое управление пулом соединений, создание session вручную не требуется)
    # Запросы можно отправлять через sdk.client
```

### Метод on_unload

Вызывается при卸ождении модуля, используется для очистки ресурсов:

```python
async def on_unload(self, event):
    # Очистка пользовательских ресурсов
    # sdk.client управляется фреймворком, его закрытие вручную не требуется
    
    # Отмена обработчиков событий (фреймворк обрабатывает это автоматически)
    self.logger.info("Модуль был выгружен")

## Объект SDK

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

## Запрос методов отправки адаптера

В связи с тем, что новые стандартные спецификации требуют использования переопределения метода `__getattr__` для реализации механизма резервной отправки, использование метода `hasattr` для проверки существования метода становится невозможным. Начиная с версии `2.3.5`, добавлена функция для запроса методов отправки.

### Список поддерживаемых методов отправки

```python
# Список всех методов отправки, поддерживаемых платформой
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
#     "docstring": "Отправка текстового сообщения..."
# }

## Управление конфигурацией

### Декларативная конфигурация (рекомендуется)

Начиная с версии v2.5.2, модули могут объявлять класс конфигурации через `ConfigClass`, используя ту же систему схем конфигурации, что и адаптеры. Конфигурация считывается в реальном времени через `self.cfg` и вступает в силу немедленно после изменения:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Bases import BaseConfig

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
        self.logger.info("Модуль загружен")

    async def on_unload(self, event):
        pass

    async def do_something(self):
        cfg = self.cfg  # Считывание в реальном времени, с проверкой типов
        api_key = cfg.api_key
        timeout = cfg.timeout
```

`BaseConfig` — это универсальный базовый класс конфигурации, который подходит для адаптеров, модулей, внешних проектов и любых других сценариев. Поля конфигурации поддерживают многоязычные описания i18n (см. [документацию i18n](../../advanced/i18n.md#配置字段多语言)).

### Декларативные ключи переводов (v2.7.0+)

Начиная с версии v2.7.0, модули также могут централизованно объявлять ключи переводов, используя вложенный класс `I18nClass`, подобно тому, как объявляют `ConfigClass`. Фреймворк автоматически **регистрирует** все объявленные ключи переводов при загрузке, не требуя ручного вызова `i18n.register()`, а момент регистрации наступает раньше генерации шаблонов конфигурации, что гарантирует доступность i18n-ключей, используемых в описаниях конфигурации.

```python
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey

class MyModule(BaseModule):
    # Класс конфигурации (необязательно)
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="欢迎",
            metadata={
                "description": {"i18n": "mymodule.welcome_msg", "default": "Приветственное сообщение"},
            },
        )

    # Класс набора ключей переводов (необязательно)
    class I18nClass(BaseI18n):
        # Имена атрибутов автоматически объединяются в полный путь ключа: <имя_модуля>.<имя_атрибута>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # Языко-независимое значение по умолчанию
            zh_CN="欢迎消息",
            zh_TW="歡迎訊息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
        )
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )
```

Подробнее см. [рекомендуемый подход i18n](../../advanced/i18n.md#推荐写法通过-i18nclass-声明翻译键-v270).

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

> **Примечание**: При ручном способе избегайте использования `self.config` в качестве имени атрибута, рекомендуется использовать `self.cfg` или любое другое пользовательское имя, чтобы избежать конфликтов с будущими свойствами фреймворка.

## Система хранения

### Основное использование

```python
# Сохранение данных
sdk.storage.set("user:123", {"name": "Чжан Сань"})

# Получение данных
user = sdk.storage.get("user:123", {})

# Удаление данных
sdk.storage.delete("user:123")
```

### Использование транзакций

```python
# Использование транзакции для обеспечения целостности данных
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # Если какая-либо операция завершится неудачей, все изменения будут откачены

## Обработка событий

### Регистрация обработчиков событий

```python
from ErisPulse.Core.Event import command, message

# Регистрация команды
@command("info", help="Получить информацию")
async def info_handler(event):
    await event.reply("Это информация")

# Регистрация обработчика сообщений
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"Получено групповое сообщение: {event.get_text()}")
```

### Жизненный цикл обработчика событий

Фреймворк автоматически управляет регистрацией и отменой регистрации обработчиков событий; вам нужно зарегистрировать их только в `on_load`.

## Механизм ленивой загрузки

### Принцип работы

```python
# Инициализация модуля происходит только при первом обращении к нему
result = await sdk.my_module.some_method()
# ↑ Здесь срабатывает инициализация модуля
```

### Мгновенная загрузка

Для модулей, которые должны быть инициализированы немедленно (например, слушатели событий, таймеры):

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=False,  # Мгновенная загрузка
        priority=100
    )

## Обработка ошибок

### Перехват исключений

```python
async def handle_event(self, event):
    try:
        # Бизнес-логика
        await self.process_event(event)
    except ValueError as e:
        self.logger.warning(f"Ошибка параметров: {e}")
        await event.reply(f"Ошибка параметров: {e}")
    except Exception as e:
        self.logger.error(f"Сбой обработки: {e}")
        raise
```

### Логирование

```python
# Использование различных уровней логирования
self.logger.debug("Информация отладки")    # Детальная информация для отладки
self.logger.info("Статус работы")          # Информация о нормальном запуске
self.logger.warning("Предупреждение")     # Предупреждение
self.logger.error("Сообщение об ошибке")  # Сообщение об ошибке
self.logger.critical("Критическая ошибка") # Критическая ошибка

## Документация

- [Введение в разработку модулей](getting-started.md) — Создание первого модуля
- [Класс-обертка событий](event-wrapper.md) — Подробное описание обработки событий
- [Лучшие практики](best-practices.md) — Создание модулей высокого качества

## Связанные документы

- [Начало работы с модулем](getting-started.md) — Создание первого модуля
- [Класс-обертка событий](event-wrapper.md) — Подробное описание обработки событий
- [Рекомендации по разработке](best-practices.md) — Создание модулей высокого качества