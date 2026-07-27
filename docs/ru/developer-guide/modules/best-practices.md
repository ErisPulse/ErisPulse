# Best Practices for Module Development

This document provides best practice recommendations for developing ErisPulse modules.

## Module Design

### 1. Single Responsibility Principle

Each module should be responsible for only one core function:

```python
# Хорошее проектирование: каждый модуль отвечает за одну функцию
class WeatherModule(BaseModule):
    """Модуль получения погоды"""
    pass

class NewsModule(BaseModule):
    """Модуль получения новостей"""
    pass

# Плохое проектирование: один модуль отвечает за несколько несвязанных функций
class UtilityModule(BaseModule):
    """Включает погоду, новости, шутки и другие функции"""
    pass
```

### 2. Module Naming Conventions

```toml
[project]
name = "ErisPulse-ModuleName"  # Использование префикса ErisPulse-
```

### 3. Четкое управление конфигурацией

Рекомендуется использовать декларативную конфигурацию (`ConfigClass` + `BaseConfig`) для получения возможности безопасного типизации, автоматической генерации шаблонов и поддержки форм WebUI:

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_url: str = field(default="https://api.example.com", metadata={
        "description": {"i18n": "my_module.api_url", "default": "Адрес API"},
    })
    timeout: int = field(default=30, metadata={
        "description": {"i18n": "my_module.timeout", "default": "Время ожидания (сек)"},
    })
    cache_ttl: int = field(default=3600, metadata={
        "description": {"i18n": "my_module.cache_ttl", "default": "Время жизни кэша (сек)"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # Безопасность типов, чтение в реальном времени
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

Дополнительно можно продолжить использовать ручное управление чтением и записью настроек хранилища (см. [Основные концепции модулей](docs/ru/core-concepts.md#управление-конфигурацией)).

### Декларативные ключи перевода (v2.7.0+)

Модули могут централизованно объявлять ключи перевода через `I18nClass`, фреймворк автоматически регистрирует их в системе i18n, без необходимости вручную вызывать `i18n.register()`.

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # Бизнес-ключи перевода с плейсхолдерами
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="欢迎你，{name}！",
            zh_TW="歡迎你，{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # Перевод описаний полей конфигурации
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

Подробное использование см. в [документации i18n](docs/ru/advanced/i18n.md#Рекомендуемый подход-Объявление-ключей-через-I18nClass-v270).

## Асинхронное программирование

### 1. Использование асинхронных библиотек

```python
# Рекомендуется использовать встроенный HTTP-клиент SDK (асинхронный, с автоматическим логированием и статистикой)
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# Также можно использовать sdk.client (эффект аналогичен)
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# Не рекомендуется использовать aiohttp напрямую (неудобно для централизованного управления фреймворком)
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# Не рекомендуется использовать requests (синхронный, блокирует цикл событий)
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # Блокирует цикл событий
```

### 2. Правильные асинхронные операции

```python
async def handle_command(self, event):
    # Используйте create_task для выполнения длительных операций в фоновом режиме
    task = asyncio.create_task(self._long_operation())
    
    # Если нужно дождаться результата
    result = await task
```

### 3. Управление ресурсами

```python
async def on_load(self, event):
    # Клиент SDK автоматически управляет пулом соединений, не нужно создавать сессию вручную
    pass
    
async def on_unload(self, event):
    # Если нужно настроить клиент, не забудьте очистить ресурсы
    pass
```

## Обработка событий

### 1. Использование класса-обертки для Event

```python
# Удобный метод с использованием класса-обертки для Event
@command("info")
async def info_command(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}!")

# А не прямой доступ к словарю
@command("info")
async def info_command(event):
    user_id = event["user_id"]  # Менее четко, легко совершить ошибку
```

### 2. Рациональное использование ленивой загрузки

```python
# Модули обработки команд должны загружаться сразу
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Модули-слушатели должны загружаться сразу
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Утилитные модули подходят для ленивой загрузки
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

### 3. Регистрация обработчиков событий

```python
async def on_load(self, event):
    # Регистрация обработчиков событий в on_load
    @command("hello")
    async def hello_handler(event):
        await event.reply("Привет!")
    
    @message.on_group_message()
    async def group_handler(event):
        self.logger.info("Получено сообщение в группе")
    
    # Не нужно вручную отменять регистрацию, фреймворк обрабатывает это автоматически
```

## Обработка ошибок

### 1. Классификация обработки исключений

```python
async def handle_event(self, event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # Ожидаемые бизнес-ошибки
        self.logger.warning(f"Бизнес-предупреждение: {e}")
        await event.reply(f"Ошибка параметров: {e}")
    except aiohttp.ClientError as e:
        # Сетевая ошибка (рекомендуется использовать sdk.client + ClientError вместо этого)
        # Старый код, использующий aiohttp напрямую, все еще будет работать, но новый код рекомендует использовать систему исключений ErisPulse
        self.logger.error(f"Сетевая ошибка: {e}")
        await event.reply("Ошибка сетевого запроса, повторите попытку позже")
    except Exception as e:
        # Неожиданные ошибки
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        await event.reply("Ошибка обработки, обратитесь к администратору")
        raise
```

### 2. Обработка таймаута

```python
# Рекомендуется использовать встроенный клиент SDK (с таймаутом и повторными попытками)
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"Превышен таймаут запроса: {url}")
        raise
```

## Система хранения

### 1. Использование транзакций

```python
# Использование транзакций для обеспечения целостности данных
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ Не использование транзакций может привести к непоследовательности данных
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # Если здесь произойдет ошибка, настройка выше не будет откачена
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. Пакетные операции

```python
# Использование пакетных операций для повышения производительности
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ Низкая эффективность при многократных вызовах
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## Логирование

### 1. Рациональное использование уровней логов

```python
# DEBUG: Подробная информация для отладки (только во время разработки)
self.logger.debug(f"Входные параметры: {params}")

# INFO: Информация о нормальной работе
self.logger.info("Модуль загружен")
self.logger.info(f"Обработка запроса: {request_id}")

# WARNING: Предупреждения, не влияющие на основные функции
self.logger.warning(f"Настройка {key} не задана, используется значение по умолчанию")
self.logger.warning("API отвечает медленно, возможно, требуется оптимизация")

# ERROR: Сообщения об ошибках
self.logger.error(f"Ошибка API-запроса: {e}")
self.logger.error(f"Ошибка обработки события: {e}", exc_info=True)

# CRITICAL: Критические ошибки, требующие немедленного вмешательства
self.logger.critical("Не удалось подключиться к базе данных, бот не может работать нормально")
```

### 2. Структурное логирование

```python
# Использование структурированного логирования для удобства анализа
self.logger.info(f"Обработка запроса: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ Использование неструктурированного логирования
self.logger.info(f"Обработка запроса от пользователя {user_id} заняла {duration} миллисекунд")
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
            
            # Получение из базы данных
            data = await self._fetch_from_db(key)
            
            # Кэширование данных
            self._cache[key] = data
            return data
```

### 2. Избегание блокирующих операций

```python
# Использование асинхронных операций
async def process_message(self, event):
    # Асинхронная обработка
    await self._async_process(event)

# ❌ Блокирующие операции
async def process_message(self, event):
    # Синхронная операция, блокирует цикл событий
    result = self._sync_process(event)
```

## Безопасность

### 1. Защита чувствительных данных

```python
# Чувствительные данные хранятся в конфигурации
class MyModule(BaseModule):
    def _load_config(self):
        config = self.sdk.config.getConfig("MyModule")
        self.api_key = config.get("api_key")
        
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Пожалуйста, настройте действительный API-ключ в config.toml")

# ❌ Жестко заданный код чувствительных данных
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # Так делать не стоит!
```

### 2. Валидация входных данных

```python
# Валидация ввода пользователя
async def process_command(self, event):
    user_input = event.get_text()
    
    # Проверка длины ввода
    if len(user_input) > 1000:
        await event.reply("Слишком длинный ввод, пожалуйста, введите снова")
        return
    
    # Проверка формата ввода
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("Неверный формат ввода")
        return
```

## Тестирование

### 1. Unit-тесты

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_load_config(self):
        """Тестирование загрузки конфигурации"""
        module = MyModule()
        config = module._load_config()
        assert config is not None
        assert "api_url" in config
```

### 2. Интеграционные тесты

```python
@pytest.mark.asyncio
async def test_command_handling():
    """Тестирование обработки команд"""
    module = MyModule()
    await module.on_load({})
    
    # Симуляция события команды
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

Соблюдение семантического версионирования:
- MAJOR.MINOR.PATCH
- MAJOR: несовместимые изменения API
- MINOR: добавление функций, обратная совместимость
- PATCH: исправление проблем, обратная совместимость

### 2. Полноценная документация

```markdown
# README.md

- Краткое описание модуля
- Инструкция по установке
- Инструкция по настройке
- Примеры использования
- Документация API
- Руководство поContributing
```

## Связанные документы

- [Введение в разработку модулей](docs/ru/getting-started.md) - Создание первого модуля
- [Основные концепции модулей](docs/ru/core-concepts.md) - Понимание архитектуры модулей
- [Класс-обертка Event](docs/ru/event-wrapper.md) - Подробное описание обработки событий