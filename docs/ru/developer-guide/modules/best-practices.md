# Лучшие практики разработки модулей

> [!TIP]
> **Когда читать эту статью:** рекомендуется прочитать после написания первого модуля (инженерные лучшие практики). Если не нужно, пропустите — это не повлияет на использование других функций.

Здесь собраны инженерные соглашения по разработке модулей: асинхронные операции не блокируют цикл событий, конфигурация задается декларативно, управляемые ресурсы других модулей освобождаются при отключении — следуя этим правилам, можно избежать утечек памяти, остаточных фоновых задач, сбоев горячей перезагрузки — типичных проблем при разработке модулей.

## Проектирование модуля

### 1. Принцип единственной ответственности

Каждый модуль должен отвечать только за одну основную функцию:

```python
# Хорошее проектирование: каждый модуль отвечает за одну функцию
class WeatherModule(BaseModule):
    """Модуль для запроса погоды"""
    pass

class NewsModule(BaseModule):
    """Модуль для запроса новостей"""
    pass

# Плохое проектирование: один модуль отвечает за несколько несвязанных функций
class UtilityModule(BaseModule):
    """Содержит погоду, новости, шутки и другие функции"""
    pass
```

### 2. Нормы именования модулей

```toml
[project]
name = "ErisPulse-ModuleName"  # Использование префикса ErisPulse-
```

### 3. Четкое управление конфигурацией

Рекомендуется использовать декларативную конфигурацию (`ConfigClass` + `BaseConfig`), чтобы получить типовую безопасность, автоматическое создание шаблонов, поддержку веб-интерфейса и т.д.:

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
        cfg = self.cfg  # Типовая безопасность, получение в реальном времени
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

Также можно продолжать использовать ручной способ чтения и записи конфигурации (см. [Основные концепции модуля](core-concepts.md#управление-конфигурацией)).

### Декларативные ключи перевода (v2.7.0+)

Модуль может объявить ключи перевода с помощью `I18nClass`, и фреймворк автоматически зарегистрирует их в системе перевода, без необходимости вызывать `i18n.register()` вручную.

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # Ключ перевода с плейсхолдером
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

Подробное использование смотрите в [документации по i18n](../../advanced/i18n.md#рекомендуемый-подход-объявление-ключей-перевода-через-i18nclass-v270).

## Асинхронное программирование

### 1. Использование асинхронных библиотек

```python
# Рекомендуется использовать встроенный HTTP-клиент SDK (асинхронный, с автоматической логированием и статистикой)
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

# Не используйте прямой импорт aiohttp (трудно управлять в рамках фреймворка)
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

### 2. Правильное выполнение асинхронных операций

```python
from ErisPulse.Core.Event import Event  # 注解 event: Event получает поддержку IDE

async def handle_command(self, event: Event):
    # Операции, требующие ожидания результата: просто await (жизненный цикл ясен)
    result = await self._long_operation()

async def on_load(self, event: dict):
    # Фоновые задачи (опрос/таймер/fire-and-forget): используйте self.spawn(),
    # при отключении модуля фреймворк в on_unload гарантирует отмену, чтобы избежать утечек
    self.spawn(self._poll())
```

> [!NOTE]
> Рекомендуется использовать `self.spawn()` (ErisPulse **2.8.0+**). **С версии 2.8.3** даже `asyncio.create_task`
> будет автоматически привязан к модулю (Task Factory автоматически регистрирует, отменяет при отключении, не утечка `self`);
> `self.spawn()` по-прежнему рекомендуется — поддерживает переключение потоков, явное указание `owner=`.
> **До версии 2.8.3** фоновые задачи не привязаны, удерживают ссылку на `self`, что приводит к утечке при горячей перезагрузке;
> необходимо использовать `self.spawn()`. Подробнее смотрите в [управление жизненным циклом](../../advanced/lifecycle.md#принадлежность-фоновых-задач-и-автоматическая-отмена).

### 3. Управление ресурсами

```python
async def on_load(self, event):
    # Клиент SDK уже управляет пулы соединений, не нужно создавать сессию вручную
    pass
    
async def on_unload(self, event):
    # Если нужно использовать кастомный клиент, не забудьте освободить ресурсы
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

# А не прямой доступ к словарю
@command("info")
async def info_command(event: Event):
    user_id = event["user_id"]  # Менее понятно, легко ошибиться
```

### 2. Разумное использование ленивой загрузки

```python
# Модуль с редко используемыми командами: объявите триггер activate_on, модуль автоматически активируется при первом совпадении команды (поддерживает ленивую загрузку)
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "Бросить кубик", "aliases": ["d"]}},
        ])

# Модуль с редкими триггерами: объявите триггер события, модуль активируется при наступлении события
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# Модуль, который должен обрабатывать каждое событие или быть готовым при запуске: загружается немедленно
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Утилитарные модули подходят для ленивой загрузки
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> Полный синтаксис `activate_on` (три формы события / сокращённая и dict-декларация команды / цепочка fallback help) смотрите в
> [системе ленивой загрузки модулей](../../advanced/lazy-loading.md#активация-по-событию-activate_on).

### 3. Регистрация обработчиков событий

```python
async def on_load(self, event):
    # Регистрируйте обработчики событий в on_load
    @command("hello")
    async def hello_handler(event: Event):
        await event.reply("Привет!")
    
    @message.on_group_message()
    async def group_handler(event: Event):
        self.logger.info("Получено сообщение в группе")
    
    # Не нужно отменять регистрацию вручную, фреймворк сделает это автоматически
```

## Утилитарные модули: при управлении чужими объектами нужно обрабатывать "уведомления об отключении"

**Когда это нужно:** ваш модуль управляет объектами других модулей (периодические обратные вызовы, подписчики, соединения, кэш и т.д.). Если эти ссылки не будут удалены после отключения модуля, экземпляр модуля не может быть освобождён — это наиболее распространённая причина утечек памяти в утилитарных модулях.

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class MyToolModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {имя модуля: управляемый объект}

    def register(self, entry):
        owner = on_cleanup(self._drop)   # ① При регистрации добавить в цепочку очистки, автоматически определить вызывающий модуль
        self._entries.setdefault(owner, []).append(entry)

    def _drop(self, owner: str):
        self._entries.pop(owner, None)   # ② При отключении модуля фреймворк автоматически вызывает: удалить его объекты

    async def on_unload(self, event):
        off_cleanup(self._drop)          # ③ Перед отключением модуля отменить хук
```

Вот и всё, фреймворк гарантирует:

- При **отключении / отключении** модуля (или при закрытии адаптера) `_drop("имя модуля")` обязательно будет вызван
- **Определение вызывающей стороны полностью автоматическое**: если вызывающий модуль в `on_load` вызывает `sdk.MyToolModule.register(...)`, или через `sdk.module.call("MyToolModule", "register", ...)`, будет правильно определён
- Не нужно беспокоиться о времени — хук вызывается в цепочке очистки фреймворка, раньше диагностики утечек, не будет ложных срабатываний

Последствия отсутствия подключения: при полном отключении модуля экземпляр не может быть освобождён (диагностика утечек сообщает "неосвобождаемый"); если вызывающий модуль сам не отменяет уведомление в `on_unload`, утечка будет постоянной.

**Обычным модулям (не управляющим чужими объектами) не нужно об этом беспокоиться** — очистка ресурсов (команды / обработчики / маршрутизация / фоновые задачи и т.д.) автоматически управляется фреймворком.

> Подробности о времени срабатывания, правилах определения вызывающей стороны, таймаутах и обработке ошибок смотрите в
> [системе принадлежности · руководство для утилитарных модулей](../../advanced/ownership.md#руководство-для-утилитарных-модулей-управление-дескрипторами-других-модулей).

## Обработка ошибок

### 1. Классификация обработки исключений

```python
from ErisPulse.Core.Bases.errors import ClientError

async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # Ожидаемые бизнес-ошибки
        self.logger.warning(f"Предупреждение: {e}")
        await event.reply(f"Ошибка параметра: {e}")
    except ClientError as e:
        # Ошибки сети (нижележащие aiohttp-исключения sdk.client уже преобразованы)
        self.logger.error(f"Ошибка сети {e.method} {e.url}: {e}")
        await event.reply("Сетевой запрос не удался, попробуйте позже")
    except Exception as e:
        # Неожиданные ошибки
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        await event.reply("Обработка не удалась, свяжитесь с администратором")
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

## Система хранения данных

### 1. Использование транзакций

```python
# Используйте транзакции для обеспечения согласованности данных
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ Без транзакций возможна несогласованность данных
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # Если здесь произойдёт ошибка, предыдущая запись не откатится
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. Массовые операции

```python
# Используйте массовые операции для повышения производительности
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
# DEBUG: Подробная отладочная информация (только для разработки)
self.logger.debug(f"Входные параметры: {params}")

# INFO: Информация о нормальной работе
self.logger.info("Модуль загружен")
self.logger.info(f"Обработка запроса: {request_id}")

# WARNING: Предупреждения, не влияющие на основную функциональность
self.logger.warning(f"Параметр {key} не установлен, используется значение по умолчанию")
self.logger.warning("API отвечает медленно, возможно, требуется оптимизация")

# ERROR: Ошибки
self.logger.error(f"Запрос API не удался: {e}")
self.logger.error(f"Ошибка обработки события: {e}", exc_info=True)

# CRITICAL: Критические ошибки, требующие немедленного вмешательства
self.logger.critical("Не удалось подключиться к базе данных, бот не может нормально работать")
```

### 2. Структурированное логирование

```python
# Используйте структурированное логирование для удобства анализа
self.logger.info(f"Обработка запроса: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ Использование неструктурированного логирования
self.logger.info(f"Обработка запроса, от пользователя {user_id}, затрачено {duration} миллисекунд")
```

## Оптимизация производительности

### 1. Использование кэша

```python
class MyModule(BaseModule):
    def __init__(self):
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_data(self, key):
        async with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            
            # Получение данных из базы
            data = await self._fetch_from_db(key)
            
            # Кэширование данных
            self._cache[key] = data
            return data
```

### 2. Избегание блокирующих операций

```python
# Используйте асинхронные операции
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
# Конфиденциальные данные хранятся в конфигурации (декларативный ConfigClass, secret-поля не попадают в логи/экспорт)
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule, BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={"description": "API-ключ", "secret": True},
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def check_api_key(self):
        if not self.cfg.api_key or self.cfg.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Пожалуйста, настройте действительный API-ключ в config.toml")

# ❌ Конфиденциальные данные в коде
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # Не делайте так!
```

### 2. Проверка входных данных

```python
# Проверка пользовательского ввода
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # Проверка длины ввода
    if len(user_input) > 1000:
        await event.reply("Слишком длинный ввод, пожалуйста, повторите")
        return
    
    # Проверка формата ввода
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("Неверный формат ввода")
        return
```

## Тестирование

### 1. Юнит-тесты

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_config_defaults(self):
        """Тестирование значений по умолчанию конфигурации"""
        config = MyModule.ConfigClass()
        assert config.timeout == 30
```

### 2. Интеграционные тесты

```python
@pytest.mark.asyncio
async def test_command_handling():
    """Тестирование обработки команд"""
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

Следуйте семантическому версионированию:
- MAJOR.MINOR.PATCH
- Главная версия: несовместимые изменения API
- Младшая версия: совместимые добавления функций
- Патч: совместимые исправления ошибок

### 2. Заголовок README

README, созданный с помощью `epsdk create`, уже содержит логотип и шапку ErisPulse. Два рекомендуемых подхода:

**Способ A — Только логотип ErisPulse (по умолчанию):**

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

**Способ B — Иконка модуля × Логотип ErisPulse (если есть пользовательская иконка):**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
(Строка с шаблонами та же)
</div>
```

Можно дополнительно добавить шаблоны GitHub Stars, Downloads и т.д. Логотип также можно загрузить в проект (`.github/assets/ErisPulseLogo.png`) и использовать относительный путь.

## Связанные документы

### Возвращение к учебному пути

- [Введение в разработку модулей](getting-started.md) - Создание первого модуля
- [Основные концепции модуля](core-concepts.md) - Понимание архитектуры модуля

### Глубокое изучение по сценариям

- [Обёртка Event](event-wrapper.md) - Подробности обработки событий
- [Руководство по публикации и магазину модулей](../publishing.md) - Публикация модуля в PyPI и магазине модулей