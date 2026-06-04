# API Справочник

Этот раздел содержит справочную документацию по API фреймворка ErisPulse.

## Список документации

- [API основных модулей](core-modules.md) - API основных модулей, таких как хранилище, конфигурация, логирование и т.д.
- [API системы событий](event-system.md) - Справка по API модуля Event
- [API системы адаптеров](adapter-system.md) - Справка по API менеджера адаптеров
- [Автоматически генерируемое API ErisPulse](auto_api/README.md) - Справка по автоматически генерируемому API

## Обзор API

### Основные модули

ErisPulse SDK предоставляет следующие основные модули:

| Модуль | Путь | Описание |
|------|------|------|
| `sdk.storage` | `sdk.storage` | Система хранения |
| `sdk.config` | `sdk.config` | Управление конфигурацией |
| `sdk.logger` | `sdk.logger` | Система логирования |
| `sdk.adapter` | `sdk.adapter` | Управление адаптерами |
| `sdk.module` | `sdk.module` | Управление модулями |
| `sdk.lifecycle` | `sdk.lifecycle` | Управление жизненным циклом |
| `sdk.router` | `sdk.router` | Управление маршрутизацией |

### Система событий

Модуль Event предоставляет следующие подмодули:

| Модуль | Путь | Описание |
|------|------|------|
| `command` | `ErisPulse.Core.Event.command` | Обработка команд |
| `message` | `ErisPulse.Core.Event.message` | События сообщений |
| `notice` | `ErisPulse.Core.Event.notice` | События уведомлений |
| `request` | `ErisPulse.Core.Event.request` | События запросов |
| `meta` | `ErisPulse.Core.Event.meta` | Метасобытия |

### Базовые классы

ErisPulse предоставляет следующие базовые классы:

| Базовый класс | Путь | Описание |
|------|------|------|
| `BaseModule` | `ErisPulse.Core.Bases.BaseModule` | Базовый класс модуля |
| `BaseAdapter` | `ErisPulse.Core.Bases.BaseAdapter` | Базовый класс адаптера |

## Примеры использования

### Доступ к основным модулям

```python
from ErisPulse import sdk

# Система хранения
sdk.storage.set("key", "value")
value = sdk.storage.get("key")

# Управление конфигурацией
config = sdk.config.getConfig("MyModule")

# Система логирования
sdk.logger.info("Логгер информации")

# Управление адаптерами
adapter = sdk.adapter.get("platform")
await adapter.Send.To("user", "123").Text("Hello")

# Управление модулями
module = sdk.module.get("ModuleName")

# Управление жизненным циклом
await sdk.lifecycle.submit_event("custom.event", msg="Пользовательское событие")

# Управление маршрутизацией
sdk.router.register_http_route("MyModule", "/api", handler, ["GET"])
```

### Использование системы событий

```python
from ErisPulse.Core.Event import command, message, notice, request, meta

# Обработка команд
@command("hello", help="Команда приветствия")
async def hello_handler(event):
    await event.reply("Привет!")

# Обработка сообщений
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"Получено групповое сообщение: {event.get_text()}")

# Обработка уведомлений
@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("Добро пожаловать в друзья!")

# Обработка запросов
@request.on_friend_request()
async def friend_request_handler(event):
    pass

# Обработка метасобытий
@meta.on_connect()
async def connect_handler(event):
    sdk.logger.info("Успешное подключение к платформе")
```

### Наследование базовых классов

```python
from ErisPulse.Core.Bases import BaseModule

class MyModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
    
    async def on_load(self, event):
        """Загрузка модуля"""
        pass
    
    async def on_unload(self, event):
        """Выгрузка модуля"""
        pass
```

## Связанные документы

- [Основные понятия](../getting-started/basic-concepts.md) - Понимание основных концепций фреймворка
- [Руководство по разработке модулей](../developer-guide/modules/) - Разработка пользовательских модулей
- [Руководство по разработке адаптеров](../developer-guide/adapters/) - Разработка платформенных адаптеров