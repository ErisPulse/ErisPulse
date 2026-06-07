# Лучшие практики разработки модулей

В этом документе представлены рекомендации по лучшим практикам разработки модулей ErisPulse.

## Дизайн модулей

### 1. Принцип единой ответственности

Каждый модуль должен отвечать только за одну основную функцию:

```python
# Хорошая конструкция: каждый модуль отвечает только за одну функцию
class WeatherModule(BaseModule):
    """Модуль погоды"""
    pass

class NewsModule(BaseModule):
    """Модуль новостей"""
    pass

# Плохая конструкция: один модуль отвечает за несколько несвязанных функций
class UtilityModule(BaseModule):
    """Включает в себя погоду, новости, шутки и другие функции"""
    pass
```

### 2. Правила именования модулей

```toml
[project]
name = "ErisPulse-ModuleName"  # Использовать префикс ErisPulse-
```

### 3. Четкое управление конфигурацией

```python
def _load_config(self):
    config = self.sdk.config.getConfig("MyModule")
    if not config:
        default_config = {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "cache_ttl": 3600
        }
        self.sdk.config.setConfig("MyModule", default_config)
        self.logger.warning("Создана конфигурация по умолчанию")
        return default_config
    return config
```

## Асинхронное программирование

### 1. Использование асинхронных библиотек

```python
# Рекомендуется использовать встроенный HTTP-клиент SDK (асинхронный, автоматическое логирование и статистика)
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# Также можно использовать sdk.client (эффект тот же)
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# Не импортируйте aiohttp напрямую (сложно для унифицированного управления фреймворком)
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# Не используйте requests (синхронный, блокирует событийный цикл)
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # Заблокирует событийный цикл
```

### 2. Правильное использование асинхронных операций

```python
async def handle_command(self, event):
    # Используйте create_task для выполнения трудоемких операций в фоне
    task = asyncio.create_task(self._long_operation())
    
    # Если результат нужен
    result = await task
```

### 3. Управление ресурсами

```python
async def on_load(self, event):
    # Клиент SDK автоматически управляет пулом соединений, создание session вручную не требуется
    pass
    
async def on_unload(self, event):
    # Если нужен собственный клиент, не забудьте очистить ресурсы
    pass
```

## Обработка событий

### 1. Использование класса-обертки событий

```python
# Удобный метод с использованием класса-обертки событий
@command("info")
async def info_command(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}!")

# Вместо прямого доступа к словарю
@command("info")
async def info_command(event):
    user_id = event["user_id"]  # Не слишком четко, легко допустить ошибку
```

### 2. Рациональное использование ленивой загрузки

```python
# Модули обработки команд необходимо загружать немедленно
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Модули-слушатели необходимо загружать немедленно
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Утилитарные модули подходят для ленивой загрузки
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

### 3. Регистрация обработчиков событий

```python
async def on_load(self, event):
    # Регистрируем обработчики событий в on_load
    @command("hello")
    async def hello_handler(event):
        await event.reply("Привет!")
    
    @message.on_group_message()
    async def group_handler(event):
        self.logger.info("Получено сообщение в группе")
    
    # Не нужно вручную отменять регистрацию, фреймворк обрабатывает это автоматически
```

## Обработка ошибок

### 1. Категоризация обработки исключений

```python
async def handle_event(self, event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # Ожидаемые бизнес-ошибки
        self.logger.warning(f"Бизнес-предупреждение: {e}")
        await event.reply(f"Ошибка параметров: {e}")
    except aiohttp.ClientError as e:
        # Сетевые ошибки (при использовании sdk.client этот тип исключений встречается редко из-за встроенного механизма повторных попыток)
        self.logger.error(f"Сетевая ошибка: {e}")
        await event.reply("Ошибка сетевого запроса, повторите попытку позже")
    except Exception as e:
        # Непредвиденные ошибки
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        await event.reply("Не удалось обработать, свяжитесь с администратором")
        raise
```

### 2. Обработка тайм-аутов

```python
# Рекомендуется использовать встроенный клиент SDK (с тайм-аутом и повторными попытками)
from ErisPulse.Core import client

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"Тайм-аут запроса: {url}")
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

# ❌ Использование без транзакций может привести к несогласованности данных
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # Если здесь произойдет ошибка, вышеустановленные значения не будут откачены
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. Пакетные операции

```python
# Использование пакетных операций для повышения производительности
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ Несколько вызовов низкой эффективности
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## Логирование

### 1. Рациональное использование уровней логирования

```python
# DEBUG: Подробная отладочная информация (только при разработке)
self.logger.debug(f"Входные параметры: {params}")

# INFO: Информация о нормальном функционировании
self.logger.info("Модуль загружен")
self.logger.info(f"Обработка запроса: {request_id}")

# WARNING: Предупреждения, не влияющие на основные функции
self.logger.warning(f"Параметр {key} не задан, используется значение по умолчанию")
self.logger.warning("API медленно отвечает, возможно, требуется оптимизация")

# ERROR: Информация об ошибках
self.logger.error(f"Ошибка запроса к API: {e}")
self.logger.error(f"Ошибка обработки события: {e}", exc_info=True)

# CRITICAL: Критическая ошибка, требует немедленного реагирования
self.logger.critical("Сбой подключения к базе данных, бот не может работать")
```

### 2. Структурированное логирование

```python
# Использование структурированного логирования для удобства анализа
self.logger.info(f"Обработка запроса: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ Использование неструктурированного логирования
self.logger.info(f"Запрос обработан, от пользователя {user_id}, время {duration} мс")
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
            
            # Получение данных из базы данных
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

# ❌ Блокирующая операция
async def process_message(self, event):
    # Синхронная операция, блокирует событийный цикл
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
            raise ValueError("Пожалуйста, укажите действительный API ключ в config.toml")

# ❌ Хардкод чувствительных данных
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # Так делать нельзя!
```

### 2. Валидация входных данных

```python
# Валидация пользовательского ввода
async def process_command(self, event):
    user_input = event.get_text()
    
    # Проверка длины ввода
    if len(user_input) > 1000:
        await event.reply("Ввод слишком длинный, попробуйте еще раз")
        return
    
    # Проверка формата ввода
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("Неверный формат ввода")
        return
```

## Тестирование

### 1. Юнит-тестирование

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_load_config(self):
        """Тест загрузки конфигурации"""
        module = MyModule()
        config = module._load_config()
        assert config is not None
        assert "api_url" in config
```

### 2. Интеграционное тестирование

```python
@pytest.mark.asyncio
async def test_command_handling():
    """Тест обработки команд"""
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
- MINOR: обратимая функциональность
- PATCH: обратимые исправления ошибок

### 2. Документация

```markdown
# README.md

- Введение в модуль
- Инструкция по установке
- Инструкция по конфигурации
- Примеры использования
- API документация
- Руководство по вкладу
```

## Связанные документы

- [Модульное программирование](getting-started.md) - Создание первого модуля
- [Основные концепции модуля](core-concepts.md) - Понимание архитектуры модулей
- [Класс-обертка событий](event-wrapper.md) - Детализация обработки событий