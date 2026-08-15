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
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self.config = self._load_config()
    
    @staticmethod
    def get_load_strategy():
        """Возвращает стратегию загрузки модуля"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[]  # Необязательно: список зависимых модулей
        )
    
    async def on_load(self, event):
        """Вызывается при загрузке модуля"""
        @command("hello", help="Отправляет приветствие")
        async def hello_command(event):
            name = event.get_user_nickname() or "Дружище"
            await event.reply(f"Привет, {name}!")
        
        self.logger.info("Модуль загружен")
    
    async def on_unload(self, event):
        """Вызывается при выгрузке модуля"""
        self.logger.info("Модуль выгружен")
    
    def _load_config(self):
        """Загружает конфигурацию модуля"""
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = {
                "api_url": "https://api.example.com",
                "timeout": 30
            }
            self.sdk.config.setConfig("MyModule", default_config)
            return default_config
        return config

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

## Основные концепции

### Базовый класс BaseModule

Все модули должны наследовать `BaseModule`, предоставляя следующие методы:

| Метод | Описание | Обязательно |
|------|------|------|
| `__init__(self)` | Конструктор | Нет |
| `get_load_strategy()` | Возвращает стратегию загрузки | Нет |
| `get_meta()` | Возвращает метаданные модуля (необязательно) | Нет |
| `on_load(self, event)` | Вызывается при загрузке модуля | Да |
| `on_unload(self, event)` | Вызывается при卸ождении модуля | Да |

### Метаданные модуля

Через `get_meta()` объявляются метаданные модуля (что делает этот модуль, какому классу принадлежит и т.д.).
Метаданные — это **общие данные описания модуля**, потребляемые модулем help, списком модулей в Dashboard, модулем магазина и другими интерфейсными/экосистемными модулями.

Совпадает с возвращаемым значением `get_load_strategy()`, возвращающим `ModuleLoadStrategy`, **рекомендуется возвращать экземпляр конфигурационного класса `ModuleMeta`** (для подсказок типов и автодополнения в IDE), также совместимо с прямым возвратом dict:

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Weather",               # Отображаемое имя (по умолчанию — имя регистрации)
            description="Lookup city weather",  # Краткое описание модуля
            version="1.0.0",
            author="ErisDev",
            group="Tools",               # Группа функций
            tags=["Weather", "Lookup"],
        )
```

Совместимая запись (dict):

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "Weather",
            "description": "Lookup city weather",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "Tools",
            "tags": ["Weather", "Lookup"],
        }
```

- `module.get_meta("MyModule")` читает проанализированные метаданные (объявление класса > зарегистрированная информация, автоматически дополняет имя команды этого модуля).
- `module.get_commands_overview()` агрегирует «метаданные модуля + его зарегистрированные команды (алиасы/группы/справка)», общую сводку команд, сгруппированную по модулям.
- Владельцем команды служит модуль, к которому она принадлежит, через `cmd_info["owner"]` (автоматически внедряется системой контекста при регистрации).

#### Поддержка i18n для полей meta

Значения полей метаданных могут быть строками или словарем i18n `{"i18n": "key.path", "default": "текст-заглушка"}` (в соответствии с соглашением для поля `description`).
Ключи перевода регистрируются через объявление в `I18nClass`, при чтении `module.get_meta()` автоматически разрешаются в текст на текущем языке:

```python
class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        meta_description: I18nKey = I18nKey(
            default="Weather lookup",
            zh_CN="查询城市天气",
            en="Weather lookup",
        )

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Weather",
            description={"i18n": "MyModule.meta_description", "default": "Weather lookup"},
        )
```

### Объект SDK

Доступ к ключевым функциям через объект `sdk`:

```python
from ErisPulse import sdk

sdk.storage    # Система хранения
sdk.config     # Система конфигурации
sdk.logger     # Система логирования
sdk.adapter    # Система адаптеров
sdk.router     # Система маршрутизации
sdk.lifecycle  # Система жизненного цикла

## Следующие шаги

- [Основные концепции модулей](core-concepts.md) — подробное понимание архитектуры модулей
- [Подробное описание класса Event Wrapper](event-wrapper.md) — изучение объекта Event
- [Рекомендации по разработке модулей](best-practices.md) — разработка качественных модулей