# Начало работы с разработкой модулей

В этом руководстве вы научитесь создавать модуль ErisPulse с нуля.

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
```

## Настройка pyproject.toml

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
```

## __init__.py

```python
from .Core import Main
```

## Core.py - Основной модуль

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
            depends=[],  # Опционально: список других модулей, от которых зависит
            # Опционально: ленивая активация по событию — объявите триггер, модуль загрузится при первом совпадении события/команды
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

> **Чтение конфигурации**: В приведённом базовом примере конфигурация не используется. При необходимости чтения конфигурации рекомендуется объявить вложенный класс `ConfigClass` и получать доступ к настройкам через `self.cfg` в режиме реального времени (см. [Основные концепции модуля](docs/ru/core-concepts.md#рекомендуемая-декларативная-конфигурация)). Устаревший способ с ручным вызовом `_load_config()` больше не поддерживается.

## Тестирование модуля

### Локальное тестирование

```bash
# Установка модуля в директории проекта
epsdk install ./MyModule

# Запуск проекта
epsdk run main.py --reload
```

### Команды тестирования

Отправка тестовой команды:

```
/hello
```

## Основные понятия

### Базовый класс BaseModule

Все модули должны наследоваться от `BaseModule` и предоставлять следующие методы:

| Метод | Описание | Обязательно |
|------|------|------|
| `__init__(self, sdk)` | Конструктор (фреймворк передаёт экземпляр `sdk`) | Нет |
| `get_load_strategy()` | Возвращает стратегию загрузки | Нет |
| `get_meta()` | Возвращает мета-информацию о модуле (необязательно) | Нет |
| `on_load(self, event)` | Вызывается при загрузке модуля | Да |
| `on_unload(self, event)` | Вызывается при выгрузке модуля | Да |

### Мета-информация модуля

> [!NOTE]
> Эта функция доступна начиная с ErisPulse **2.8.0+**.

С помощью `get_meta()` объявляется мета-информация о модуле (для чего он предназначен, к какой категории относится и т.д.).  
Мета-информация — это **общие сведения о модуле**, которые могут использоваться различными интерфейсами и экосистемными модулями, такими как модуль help, список модулей в Dashboard, модуль магазина и т.д.

Как и в случае с `get_load_strategy()`, возвращая `ModuleLoadStrategy`, **рекомендуется возвращать экземпляр класса `ModuleMeta`** (с типизацией атрибутов и автодополнением в IDE), но допускается также возвращать словарь:

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Погода",             # Отображаемое имя (по умолчанию имя регистрации)
            description="Получение погоды в городе",  # Краткое описание модуля
            version="1.0.0",
            author="ErisDev",
            group="Инструменты",        # Группа функций
            tags=["Погода", "Поиск"],
        )
```

Альтернативный способ (возвращение словаря):

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

- `module.get_meta("MyModule")` читает уже разобранные мета-данные (приоритет класса > регистрационной информации, автоматически дополняется имя команды модуля).
- `module.get_commands_overview()` объединяет «мета-информацию модуля + зарегистрированные команды (псевдонимы/группы/помощь)», организуя обзор команд по модулям.
- Модуль, к которому принадлежит команда, можно получить через `cmd_info["owner"]` (автоматически вставляется в контекст при регистрации).

#### Поддержка i18n для полей мета-информации

Значения полей мета-информации могут быть обычной строкой или словарём i18n `{"i18n": "key.path", "default": "текст по умолчанию"}` (в соответствии с соглашением для `description` в конфигурации).  
Ключи перевода объявляются через `I18nClass`, а `module.get_meta()` при чтении автоматически преобразует их в текст текущего языка:

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
            name="Погода",
            description={"i18n": "MyModule.meta_description", "default": "Weather lookup"},
        )
```

### Объект SDK

Для доступа к основным функциям используется объект `sdk`:

```python
from ErisPulse import sdk

sdk.storage    # Система хранения
sdk.config     # Система конфигурации
sdk.logger     # Система логирования
sdk.adapter    # Система адаптеров
sdk.router     # Система маршрутизации
sdk.lifecycle  # Система жизненного цикла
```

## Далее

- [Основные понятия модуля](core-concepts.md) - Глубокое понимание архитектуры модуля
- [Подробное объяснение Event-обертки](event-wrapper.md) - Изучение объекта Event
- [Лучшие практики модуля](best-practices.md) - Разработка высококачественных модулей