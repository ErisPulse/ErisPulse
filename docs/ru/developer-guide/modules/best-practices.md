# Рекомендации по разработке модулей

В настоящем документе представлены лучшие практики разработки модулей для ErisPulse.

## Дизайн модуля

### 1. Принцип единственной ответственности

Каждый модуль должен отвечать за одну основную функцию:

```python
# Хороший дизайн: каждый модуль отвечает за одну функцию
class WeatherModule(BaseModule):
    """Модуль для получения погоды"""
    pass

class NewsModule(BaseModule):
    """Модуль для получения новостей"""
    pass

# Плохой дизайн: один модуль отвечает за несколько несвязанных функций
class UtilityModule(BaseModule):
    """Содержит функции погоды, новостей, анекдотов и т.д."""
    pass
```

### 2. Нормы именования модулей

```toml
[project]
name = "ErisPulse-ModuleName"  # Использовать префикс ErisPulse-
```

### 3. Четкое управление конфигурацией

Рекомендуется использовать декларативную конфигурацию (`ConfigClass` + `BaseConfig`), чтобы получить типобезопасность, автоматическое создание шаблонов и поддержку форм веб-интерфейса:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_url: str = field(default="https://api.example.com", metadata={
        "description": {"i18n": "my_module.api_url", "default": "Адрес API"},
    })
    timeout: int = field(default=30, metadata={
        "description": {"i18n": "my_module.timeout", "default": "Время ожидания (секунды)"},
    })
    cache_ttl: int = field(default=3600, metadata={
        "description": {"i18n": "my_module.cache_ttl", "default": "Время жизни кэша (секунды)"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # Типобезопасный доступ к конфигурации
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

Также можно продолжать использовать ручное управление конфигурацией (см. [Основные концепции модуля](core-concepts.md#управление-конфигурацией)).

### Декларативные ключи перевода (v2.7.0+)

Модуль может объявлять ключи перевода через `I18nClass`, и фреймворк автоматически зарегистрирует их в системе i18n, без необходимости вызывать `i18n.register()` вручную.

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # Ключ перевода с подстановками
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="Добро пожаловать, {name}!",
            zh_TW="歡迎你，{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # Описание поля конфигурации
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="Адрес API",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

Подробное использование см. в [документации по i18n](../../advanced/i18n.md#рекомендуемый-способ-объявления-ключей-перевода-через-i18nclass-v270).

## Асинхронное программирование

### 1. Использование асинхронных библиотек

```python
# Рекомендуется использовать встроенный HTTP-клиент SDK (асинхронный, с автоматическим логированием и статистикой)
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# Также можно использовать sdk.client (результат тот же)
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# Не используйте прямой импорт aiohttp (трудно управлять из фреймворка)
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# Не используйте requests (синхронный, блокирует цикл событий)
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # Блокирует цикл событий
```

### 2. Корректное выполнение асинхронных операций

```python
from ErisPulse.Core.Event import Event  # Подсказки IDE доступны через event: Event

async def handle_command(self, event: Event):
    # Длительные операции, результат которых нужно получить: await (жизненный цикл ясен)
    result = await self._long_operation()

async def on_load(self, event: dict):
    # Фоновые задачи (опрос/таймер/fire-and-forget): используйте self.spawn(),
    # модуль при выгрузке автоматически отменяет задачи после on_unload, предотвращая утечку
    self.spawn(self._poll())
```

> [!NOTE]
> Фоновые задачи рекомендуется выполнять через `self.spawn()` (ErisPulse **2.8.0+**), а не `asyncio.create_task` — последний создает задачу без привязки к модулю, которая не будет автоматически отменена при выгрузке, и может привести к утечке памяти. Подробнее см. [Управление жизненным циклом](../../advanced/lifecycle.md#автоматическая-отмена-задач-фоновых-задач).

### 3. Управление ресурсами

```python
async def on_load(self, event):
    # Клиент SDK уже управляет пулом соединений, не нужно создавать session вручную
    pass
    
async def on_unload(self, event):
    # Если нужно использовать собственный клиент, не забудьте очистить ресурсы
    pass
```

## Обработка событий

### 1. Использование обёртки Event

```python
# Использование удобных методов обёртки Event
@command("info")
async def info_command(event: Event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}!")

# Вместо прямого доступа к словарю
@command("info")
async def info_command(event: Event):
    user_id = event["user_id"]  # Менее понятно, легко ошибиться
```

### 2. Разумное использование ленивой загрузки

```python
# Модуль с редко используемыми командами: объявите триггер activate_on, модуль активируется при первом совпадении команды (сохраняя ленивую загрузку)
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "Бросить кубик", "aliases": ["d"]}},
        ])

# Модуль с редкими триггерами событий: объявите триггер activate_on, модуль активируется при поступлении события
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# Модули, часто вызываемые (каждое сообщение) или требующие готовности при запуске: загружайте немедленно
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Инструментальные модули подходят для ленивой загрузки
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> Полный синтаксис `activate_on` (форма триггера события / упрощённая и dict-форма объявления / цепочка help) см. в [системе ленивой загрузки модулей](../../advanced/lazy-loading.md#активация-по-триггеру-activate_on).

### 3. Регистрация обработчиков событий

```python
async def on_load(self, event):
    # Регистрируйте обработчики событий в on_load
    @command("hello")
    async def hello_handler(event: Event):
        await event.reply("Привет!")
    
    @message.on_group_message()
    async def group_handler(event: Event):
        self.logger.info("Получено групповое сообщение")
    
    # Не нужно отменять регистрацию, фреймворк сделает это автоматически
```

## Инструментальные модули: при хранении чужих объектов нужно учитывать "уведомление об отключении"

**Когда это необходимо**: Ваш модуль хранит что-то от имени другого модуля (обратные вызовы по таймеру, подписчики, соединения, кэш и т.д.). Если эти ссылки не будут удалены после выгрузки модуля-владельца, экземпляр не сможет быть освобождён — это наиболее распространённая причина утечек памяти в инструментальных модулях.

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class MyToolModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {имя модуля: хранимые вещи}

    def register(self, entry):
        owner = on_cleanup(self._drop)   # ① При регистрации добавляем в цепочку очистки, автоматически определяется вызывающий модуль
        self._entries.setdefault(owner, []).append(entry)

    def _drop(self, owner: str):
        self._entries.pop(owner, None)   # ② При выгрузке модуля-владельца фреймворк автоматически вызывает: удаляем его объекты

    async def on_unload(self, event):
        off_cleanup(self._drop)          # ③ Перед собственной выгрузкой отменяем хук
```

Таким образом, фреймворк гарантирует:

- При **выгрузке / отключении** модуля-владельца (или при остановке адаптера) `_drop("имя модуля-владельца")` обязательно будет вызван
- **Автоматическое определение вызывающего модуля**: если модуль-владелец вызывает `sdk.MyToolModule.register(...)` или через `sdk.module.call("MyToolModule", "register", ...)` — будет правильно определён владелец
- Не нужно заботиться о времени — хук вызывается в цепочке фреймворка, до диагностики утечек, не приведёт к ложным срабатываниям

Последствия неподключения: при полной выгрузке модуля-владельца экземпляр не может быть освобождён (диагностика утечек сообщает "недостижимый"); если модуль-владелец также не отменяет уведомление, утечка будет постоянной.

**Обычные модули (не хранящие чужие объекты) не должны этим заниматься** — очистка ресурсов (команды / обработчики / маршрутизация / фоновые задачи и т.д.) автоматически выполняется фреймворком.

> Подробности о времени срабатывания, правилах определения вызывающего модуля, таймаутах и обработке ошибок см. в [системе принадлежности · руководство по инструментальным модулям](../../advanced/ownership.md#руководство-по-инструментальным-модулям-хранение-дескрипторов-других-модулей).

## Обработка ошибок

### 1. Классификация обработки исключений

```python
from ErisPulse.Core.Bases.errors import ClientError

async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # Ожидаемая бизнес-ошибка
        self.logger.warning(f"Предупреждение бизнеса: {e}")
        await event.reply(f"Ошибка параметра: {e}")
    except ClientError as e:
        # Ошибка сети (нижележащие исключения aiohttp уже автоматически преобразованы)
        self.logger.error(f"Ошибка сети {e.method} {e.url}: {e}")
        await event.reply("Ошибка запроса, попробуйте позже")
    except Exception as e:
        # Неожиданная ошибка
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        await event.reply("Обработка не удалась, обратитесь к администратору")
        raise
```

### 2. Обработка таймаутов

```python
# Рекомендуется использовать встроенный клиент SDK (с таймаутом и повторами)
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"Таймаут запроса: {url}")
        raise
```

## Система хранения

### 1. Использование транзакций

```python
# Использование транзакций для обеспечения согласованности данных
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ Без транзакций возможна несогласованность данных
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # Если здесь произойдёт ошибка, предыдущий вызов не откатится
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. Массовые операции

```python
# Использование массовых операций для повышения производительности
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ Многократные вызовы менее эффективны
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## Логирование

### 1. Разумное использование уровней логирования

```python
# DEBUG: Подробная отладочная информация (только в разработке)
self.logger.debug(f"Параметры ввода: {params}")

# INFO: Информация о нормальной работе
self.logger.info("Модуль загружен")
self.logger.info(f"Обработка запроса: {request_id}")

# WARNING: Предупреждения, не влияющие на основную функциональность
self.logger.warning(f"Параметр {key} не задан, используется значение по умолчанию")
self.logger.warning("API отвечает медленно, возможно, нужно оптимизировать")

# ERROR: Ошибки
self.logger.error(f"Ошибка API: {e}")
self.logger.error(f"Ошибка обработки события: {e}", exc_info=True)

# CRITICAL: Критические ошибки, требующие немедленного вмешательства
self.logger.critical("Ошибка подключения к базе данных, робот не может нормально работать")
```

### 2. Структурированное логирование

```python
# Использование структурированного логирования для упрощения анализа
self.logger.info(f"Обработка запроса: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ Использование неструктурированного логирования
self.logger.info(f"Обработка запроса, от пользователя {user_id}, заняло {duration} миллисекунд")
```

## Оптимизация производительности

### 1. Использование кэширования

```python
class MyModule(BaseModule):
    def __init__(self):
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_data(self, key):
        async with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            
            # Получение из базы данных
            data = await self._fetch_from_db(key)
            
            # Кэширование данных
            self._cache[key] = data
            return data
```

### 2. Избегание блокирующих операций

```python
# Использование асинхронных операций
async def process_message(self, event: Event):
    # Асинхронная обработка
    await self._async_process(event)

# ❌ Блокирующая операция
async def process_message(self, event: Event):
    # Синхронная операция, блокирует цикл событий
    result = self._sync_process(event)
```

## Безопасность

### 1. Защита конфиденциальных данных

```python
# Конфиденциальные данные хранятся в конфигурации (декларативный ConfigClass, поля с secret не попадают в логи/экспорт)
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule, BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={"description": "Ключ API", "secret": True},
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def check_api_key(self):
        if not self.cfg.api_key or self.cfg.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Укажите действительный ключ API в config.toml")

# ❌ Конфиденциальные данные в коде
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # Не делайте так!
```

### 2. Проверка входных данных

```python
# Проверка входных данных пользователя
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # Проверка длины ввода
    if len(user_input) > 1000:
        await event.reply("Слишком длинный ввод, попробуйте снова")
        return
    
    # Проверка формата ввода
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("Неверный формат ввода")
        return
```

## Тестирование

### 1. Модульные тесты

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_config_defaults(self):
        """Тест значений по умолчанию конфигурации"""
        config = MyModule.ConfigClass()
        assert config.timeout == 30
```

### 2. Интеграционные тесты

```python
@pytest.mark.asyncio
async def test_command_handling():
    """Тест обработки команд"""
    module = MyModule()
    await module.on_load({})
    
    # Симуляция командного события
    event = create_test_command_event("hello")
    await module.handle_command(event)
```

## Развертывание

### 1. Управление версиями

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

Соблюдайте семантическое управление версиями:
- MAJOR.MINOR.PATCH
- Главная версия: несовместимые изменения API
- Подверсия: добавление совместимых функций
- Исправление: исправления совместимых ошибок

### 2. Заголовок README

README, созданный с помощью `epsdk create`, уже содержит логотип и шапку ErisPulse. Два рекомендуемых варианта:

**Вариант A — Только логотип ErisPulse (по умолчанию):**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**Одно предложение описания**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**Вариант B — Иконка модуля × Логотип ErisPulse (если есть пользовательская иконка):**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
(Та же строка с шаблонами)
</div>
```

Можно дополнительно добавить шаблоны GitHub Stars, Downloads и т.д. Логотип можно также загрузить в проект локально (`.github/assets/ErisPulseLogo.png`) и использовать относительный путь.

## Связанные документы

- [Введение в разработку модулей](getting-started.md) - Создание первого модуля
- [Основные концепции модуля](core-concepts.md) - Понимание архитектуры модуля
- [Обёртка Event](event-wrapper.md) - Подробности обработки событий