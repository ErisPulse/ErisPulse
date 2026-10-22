# Введение в разработку модулей

> [!NOTE]
> **Обязательная документация уровня L1 (ядро)** — один из пяти ключевых документов в «маршруте чтения» на главной странице, необходим для разработки модулей.


Пройдя этот материал до конца, вы получите работающий модуль, реагирующий на команду `/hello`, а также узнаете о структуре проекта модуля, способе его регистрации и хуках загрузки/выгрузки — вся последующая документация по модулям строится на этом каркасе.

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

## Конфигурация pyproject.toml

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Описание функциональности модуля"
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

## Core.py — базовый модуль

```python
from ErisPulse import sdk
# Рекомендуется корневой импорт (2.10+): часто используемые символы импортируются напрямую из корневого пакета, глубокие пути по-прежнему поддерживаются
from ErisPulse import BaseModule, command

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
            depends=[],  # Необязательно: список других модулей, от которых зависит данный модуль
            # Необязательно: ленивая активация по событиям — объявите триггеры, и модуль автоматически загрузится при поступлении первого совпадающего события/команды
            # activate_on=[{"command": {"name": "hello", "help": "Отправляет приветствие"}}],
        )
    
    async def on_load(self, event):
        """Вызывается при загрузке модуля"""
        @command("hello", help="Отправляет приветствие")
        async def hello_command(event):
            name = event.get_user_nickname() or "друг"
            await event.reply(f"Привет, {name}!")
        
        self.logger.info("Модуль загружен")
    
    async def on_unload(self, event):
        """Вызывается при выгрузке модуля"""
        self.logger.info("Модуль выгружен")
```

> **Чтение конфигурации**: приведённый выше базовый пример не использует конфигурацию. Если требуется чтение конфигурации, рекомендуется объявить вложенный класс `ConfigClass` и читать её в реальном времени через `self.cfg` (см. [Основные концепции модулей](core-concepts.md#声明式配置推荐)). Устаревший подход с ручным вызовом `_load_config()` признан нерекомендуемым.

## Тестирование модуля

### Локальное тестирование

```bash
# Установите модуль из каталога проекта
epsdk install ./MyModule

# Запустите проект
epsdk run main.py --reload
```

### Тестирование команды

Отправьте команду для проверки:

```
/hello
```

## Основные концепции

### Базовый класс BaseModule

Все модули должны наследоваться от `BaseModule` и предоставлять следующие методы:

| Метод | Описание | Обязательный |
|------|------|------|
| `__init__(self, sdk)` | Конструктор (фреймворк передаёт экземпляр `sdk`) | Нет |
| `get_load_strategy()` | Возвращает стратегию загрузки | Нет |
| `get_meta()` | Возвращает метаинформацию о модуле (необязательно) | Нет |
| `on_load(self, event)` | Вызывается при загрузке модуля | Да |
| `on_unload(self, event)` | Вызывается при выгрузке модуля | Да |

### Метаинформация модуля (meta)

> [!NOTE]
> Для этой функции требуется ErisPulse **2.8.0+**.

Через `get_meta()` объявляется вводная метаинформация о модуле (что делает этот модуль, к какой категории относится и т. д.).
Метаинформация — это **универсальные презентационные данные модуля**, используемые help-модулем, списком модулей Dashboard, магазином модулей и другими интерфейсными/экосистемными модулями.

Аналогично `get_load_strategy()`, возвращающему `ModuleLoadStrategy`, **рекомендуется возвращать экземпляр конфигурационного класса `ModuleMeta`** (типизация атрибутов, автодополнение в IDE); также поддерживается возврат dict напрямую:

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="Погода",               # Отображаемое имя (имя по умолчанию при регистрации)
            description="Запрос погоды в городе",  # Краткое описание модуля
            version="1.0.0",
            author="ErisDev",
            group="Инструменты",               # Функциональная группа
            tags=["погода", "запрос"],
        )
```

Совместимый вариант записи (dict):

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "Погода",
            "description": "Запрос погоды в городе",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "Инструменты",
            "tags": ["погода", "запрос"],
        }
```

- `module.get_meta("MyModule")` читает уже разрешённую метаинформацию (объявление в классе > зарегистрированная info, имена команд модуля дополняются автоматически).
- `module.get_commands_overview()` агрегирует «метаинформацию модуля + зарегистрированные им команды (алиасы/группы/справка)» — общий обзор команд, организованный по модулям.
- Принадлежность команды модулю можно получить через `cmd_info["owner"]` (автоматически внедряется системой контекста при регистрации).

#### Поддержка i18n для полей meta

Значениями полей метаинформации могут быть обычные строки или i18n-словарь `{"i18n": "key.path", "default": "резервный текст"}` (по тому же соглашению, что и `description` в конфигурации).
Ключи перевода объявляются и регистрируются через `I18nClass`, а при чтении `module.get_meta()` автоматически разрешаются в текст на текущем языке:

```python
class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        meta_description: I18nKey = I18nKey(
            default="Weather lookup",
            zh_CN="Запрос погоды в городе",
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

Доступ к основной функциональности через объект `sdk`:

```python
from ErisPulse import sdk

sdk.storage    # Система хранения
sdk.config     # Система конфигурации
sdk.logger     # Система логирования
sdk.adapter    # Система адаптеров
sdk.router     # Система маршрутизации
sdk.lifecycle  # Система жизненного цикла
```

## Следующие шаги

### Продолжение пути обучения

- [Основные концепции модулей](core-concepts.md) - подробное изучение архитектуры модулей
- [Подробное руководство по классу-обёртке Event](event-wrapper.md) - изучение объекта Event

### После написания

- [Лучшие практики разработки модулей](best-practices.md) - разработка качественных модулей
- [Руководство по устранению неполадок модулей](../module-troubleshooting.md) - диагностика, когда модуль не загрузился или команда не срабатывает