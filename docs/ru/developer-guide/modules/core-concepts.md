# Основные концепции модулей

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
            lazy_load=True,   # Ленивая загрузка или немедленная
            priority=0,       # Приоритет загрузки (чем больше число, тем раньше загружается)
            depends=["OtherModule"]  # Необязательно: объявление других модулей, от которых зависит текущий
        )
```

> Если модули, объявленные в `depends`, не зарегистрированы, текущий модуль будет пропущен и будет записано предупреждение. Порядок загрузки определяется топологической сортировкой, а для модулей одного уровня используется приоритет в порядке убывания.

### Метод on_load

Вызывается при загрузке модуля, используется для инициализации ресурсов и регистрации обработчиков событий:

```python
async def on_load(self, event):
    # Регистрация обработчика событий
    @command("hello", help="Команда приветствия")
    async def hello_handler(event):
        await event.reply("Привет!")
    
    # Использование встроенного HTTP-клиента SDK (автоматическое управление пулом соединений, создание сессии вручную не требуется)
    # Запросы можно отправлять через sdk.client
```

### Метод on_unload

Вызывается при выгрузке модуля, используется для очистки ресурсов:

```python
async def on_unload(self, event):
    # Очистка пользовательских ресурсов
    # sdk.client управляется фреймворком, закрывать его вручную не требуется
    
    # Отмена обработчика событий (фреймворк обрабатывает это автоматически)
    self.logger.info("Модуль был выгружен")
```

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
```

## Запрос методов отправки адаптера

Поскольку новый стандартный протокол требует использования переопределения метода `__getattr__` для реализации механизма отправки на случай неудачи, использование метода `hasattr` для проверки существования метода больше невозможно. С версии 2.3.5 добавлена функция для запроса методов отправки.

### Перечень поддерживаемых методов отправки

```python
# Перечислить все методы отправки, поддерживаемые платформой
methods = sdk.adapter.list_sends("onebot11")
# Возвращает: ["Text", "Image", "Voice", "Markdown", ...]
```

### Получение подробной информации о методе

```python
# Получить подробную информацию о конкретном методе
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

### Чтение конфигурации

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

### Использование конфигурации

```python
async def do_something(self):
    api_key = self.config.get("api_key")
    timeout = self.config.get("timeout", 30)
```

## Система хранения

### Базовое использование

```python
# Сохранить данные
sdk.storage.set("user:123", {"name": "张三"})

# Получить данные
user = sdk.storage.get("user:123", {})

# Удалить данные
sdk.storage.delete("user:123")
```

### Использование транзакций

```python
# Использование транзакции для обеспечения целостности данных
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # Если какая-либо операция завершится ошибкой, все изменения будут откатаны
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

### Жизненный цикл обработчика событий

Фреймворк автоматически управляет регистрацией и отменой регистрации обработчиков событий, вам нужно регистрировать их только в `on_load`.

## Механизм ленивой загрузки

### Как это работает

```python
# Модуль инициализируется только при первом обращении к нему
result = await sdk.my_module.some_method()
# ↑ Здесь срабатывает инициализация модуля
```

### Немедленная загрузка

Для модулей, требующих немедленной инициализации (например, слушателей, таймеров):

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
        self.logger.error(f"Ошибка обработки: {e}")
        raise
```

### Логирование

```python
# Использование различных уровней логирования
self.logger.debug("Отладочная информация")    # Подробная информация для отладки
self.logger.info("Статус работы")              # Нормальная информация о работе
self.logger.warning("Предупреждение")          # Информация о предупреждении
self.logger.error("Информация об ошибке")    # Информация об ошибке
self.logger.critical("Критическая ошибка") # Критическая ошибка
```

## Связанные документы

- [Основы разработки модулей](getting-started.md) - Создание первого модуля
- [Класс обертки событий](event-wrapper.md) - Подробное описание обработки событий
- [Лучшие практики](best-practices.md) - Разработка модулей высокого качества