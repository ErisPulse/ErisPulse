# Начало работы с разработкой модулей

В этом руководстве мы расскажем, как создать модуль ErisPulse с нуля.

Документация о модулях ErisPulse

Дополнительные ресурсы

Ресурсы и документация для разработчиков модулей ErisPulse

Документация по API

Как подключить модуль к боту

Документация по API для разработчиков

Документация по API

Справочник по API

Создание нового модуля

Прежде чем писать код, убедитесь, что у вас установлена и настроена переменная среды.

Создайте новую папку для вашего модуля. Выберите любое имя, но обязательно назовите её `MyModule`. Вы можете также назвать её `mysimplemodule`, если предпочитаете.

Теперь перейдите к настройке параметров модуля. Откройте файл конфигурации, который генерируется в папке вашего модуля.

```javascript
// Документация о модулях ErisPulse
module.exports = {
    // Справочник по API
    config: {
        // Создание нового модуля
        name: 'MyModule', // Здесь используйте ваше имя
    },
    // Ресурсы и документация для разработчиков модулей ErisPulse
    run: (context) => {
        // Документация по API для разработчиков
        const { message, args } = context;
        // Документация по API
        if (args[0] === 'docs') {
            message.channel.send('https://docs.erispulse.com/api');
        }
    }
};
```

[Документация по API для разработчиков](docs/ru/api-reference.md)

```javascript
module.exports = {
    config: {
        // Справочник по API
        name: 'MyModule',
        // Ресурсы и документация для разработчиков модулей ErisPulse
        version: '1.0.0',
        description: 'Пример простого модуля для ErisPulse',
        // Дополнительные ресурсы
        usage: '/mymodule [docs]',
        // Документация по API
        cooldown: 0
    },
    // Документация по API для разработчиков
    run: (context) => {
        // Документация по API
        const { message, args } = context;
        if (args[0] === 'docs') {
            // Ресурсы и документация для разработчиков модулей ErisPulse
            message.channel.send('Документация по API: https://docs.erispulse.com/api');
        }
    }
};
```

[Справочник по API](docs/ru/api-reference.md)

```javascript
module.exports = {
    config: {
        name: 'MyModule',
        version: '1.0.0',
        description: 'Пример простого модуля для ErisPulse',
        usage: '/mymodule [docs]',
        cooldown: 0
    },
    run: (context) => {
        const { message, args } = context;
        if (args[0] === 'docs') {
            message.channel.send('Документация по API: https://docs.erispulse.com/api');
        }
    }
};
```

[Ресурсы и документация для разработчиков модулей ErisPulse](docs/ru/contributing.md)

Проверьте настройки в файле конфигурации модуля.

Запустите бота.

Введите команду в Discord.

Вы увидите сообщение, которое мы отправляем в канал.

Теперь вы знаете, как создать модуль для ErisPulse. Вы можете пойти дальше и изучить документацию API, чтобы понять, как использовать контекст и аргументы для создания более сложных команд.

## Структура проекта

Стандартная структура модуля:

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py

## pyproject.toml

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Описание функционала модуля"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = []

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"

## __init__.py

```python
from .Core import Main

## Core.py - Базовый модуль

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command

class Main(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
    
    @staticmethod
    def get_load_strategy():
        """Возвращает стратегию загрузки модуля"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[],  # Опционально: список зависимых других модулей
            # Опционально: ленивая активация на основе событий — объявление триггеров, автоматическая загрузка при первом совпадении события/команды
            # activate_on=[{"command": {"name": "hello", "help": "Отправить приветствие"}}],
        )
    
    async def on_load(self, event):
        """Вызывается при загрузке модуля"""
        @command("hello", help="Отправить приветствие")
        async def hello_command(event):
            name = event.get_user_nickname() or "друг"
            await event.reply(f"Привет, {name}!")
        
        self.logger.info("Модуль загружен")
    
    async def on_unload(self, event):
        """Вызывается при выгрузке модуля"""
        self.logger.info("Модуль выгружен")
```

> **Чтение конфигурации**: приведённый выше базовый пример не использует конфигурацию. При необходимости чтения конфигурации рекомендуется объявить вложенный класс `ConfigClass` и получать доступ к ней через `self.cfg` в режиме реального времени (см. [Основные концепции модулей](core-concepts.md#рекомендуемая-декларативная-конфигурация)). Устаревший способ с ручным вызовом `_load_config()` больше не поддерживается.

## Модуль тестирования

### Локальный тест

```bash
# Установка модуля в каталог проекта
epsdk install ./MyModule

# Запуск проекта
epsdk run main.py --reload
```

### Команда тестирования

Отправка команды на тестирование:

```
/hello

## Основные понятия

### Базовый класс BaseModule

Все модули должны наследовать `BaseModule`, предоставляя следующие методы:

| Метод | Описание | Обязательно |
|------|------|------|
| `__init__(self, sdk)` | Конструктор (фреймворк передает экземпляр `sdk`) | Нет |
| `get_load_strategy()` | Возвращает стратегию загрузки | Нет |
| `get_meta()` | Возвращает метаданные о модуле (необязательно) | Нет |
| `on_load(self, event)` | Вызывается при загрузке модуля | Да |
| `on_unload(self, event)` | Вызывается при выгрузке модуля | Да |

### Мета-информация о модуле

> [!NOTE]
> Эта функция доступна начиная с ErisPulse **2.8.0+**.

Мета-информация о модуле объявляется через `get_meta()`. Она описывает, что делает данный модуль, к какой категории он относится и т.д. Мета-данные являются **общей информацией о модуле**, которую могут использовать различные интерфейсы и экосистемные модули, такие как модуль help, список модулей в Dashboard, магазин модулей и т.д.

Возвращаемое значение `get_load_strategy()` должно быть экземпляром `ModuleLoadStrategy`. **Рекомендуется возвращать экземпляр класса `ModuleMeta`** (поддержка типизации, автодополнение в IDE), но также поддерживается возврат словаря:

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Погода",               # Отображаемое имя (по умолчанию имя регистрации)
            description="Получение погоды в городе",  # Краткое описание модуля
            version="1.0.0",
            author="ErisDev",
            group="Инструменты",               # Группа функций
            tags=["Погода", "Поиск"],
        )
```

Альтернативный способ (возврат словаря):

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "Погода",
            "description": "Получение погоды в городе",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "Инструменты",
            "tags": ["Погода", "Поиск"],
        }
```

- `module.get_meta("MyModule")` читает уже разобранные метаданные (сначала класс, затем информация о регистрации, автоматически дополняется имя команды модуля).
- `module.get_commands_overview()` объединяет «метаданные модуля + зарегистрированные команды (псевдонимы/группы/помощь)», и представляет общий обзор команд, организованных по модулям.
- Модуль, к которому принадлежит команда, можно получить через `cmd_info["owner"]` (автоматически вставляется системой контекста при регистрации).

#### Поддержка i18n для полей мета-информации

Значения полей мета-информации могут быть простыми строками или словарями i18n `{"i18n": "key.path", "default": "текст по умолчанию"}` (согласно соглашению для поля `description`).
Ключи для перевода объявляются через `I18nClass`, а `module.get_meta()` автоматически разбирает их в текст текущего языка:

```python
class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        meta_description: I18nKey = I18nKey(
            default="Weather lookup",
            zh_CN="Получение погоды в городе",
            en="Weather lookup",
        )

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Погода",
            description={"i18n": "MyModule.meta_description", "default": "Weather lookup"},
        )
```

### Объект SDK

Доступ к основным функциям осуществляется через объект `sdk`:

```python
from ErisPulse import sdk

sdk.storage    # Система хранения
sdk.config     # Система конфигурации
sdk.logger     # Система логирования
sdk.adapter    # Система адаптеров
sdk.router     # Система маршрутизации
sdk.lifecycle  # Система жизненного цикла
```

docs/ru/quick-start.md

## Следующие шаги

- [Основные концепции модулей](core-concepts.md) — подробное понимание архитектуры модулей
- [Подробное описание класса Event Wrapper](event-wrapper.md) — изучение объекта Event
- [Рекомендации по разработке модулей](best-practices.md) — разработка качественных модулей