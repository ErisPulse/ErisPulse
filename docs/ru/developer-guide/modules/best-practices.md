# Лучшие практики разработки модулей

В этом документе представлены рекомендации по разработке модулей ErisPulse.

请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。

再次提醒：如果文档包含语言切换行（各语言名称用 `` | `` 分隔的行），务必严格遵守上方第8条的格式要求，不要写出 ``[**Label**](file)`` 这类错误格式。

## Модульная архитектура

### 1. Принцип единой ответственности

Каждый модуль должен отвечать только за одну основную функцию:

```python
# Хороший дизайн: каждый модуль отвечает только за одну функцию
class WeatherModule(BaseModule):
    """Модуль запроса погоды"""
    pass

class NewsModule(BaseModule):
    """Модуль запроса новостей"""
    pass

# Плохой дизайн: один модуль отвечает за несколько несвязанных функций
class UtilityModule(BaseModule):
    """Содержит несколько функций: погода, новости, шутки и т.д."""
    pass
```

### 2. Правила именования модулей

```toml
[project]
name = "ErisPulse-ModuleName"  # Использовать префикс ErisPulse-
```

### 3. Четкое управление конфигурацией

Рекомендуется использовать декларативную конфигурацию (объект `ConfigClass` + базовый класс `BaseConfig`), что дает возможности, такие как безопасность типов, автоматическое создание шаблонов, поддержку форм на WebUI и др.:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_url: str = field(default="https://api.example.com", metadata={
        "description": {"i18n": "my_module.api_url", "default": "API адрес"},
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
        cfg = self.cfg  # Безопасно для типов, чтение в реальном времени
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

Также можно продолжать использовать ручное управление чтением и записью конфигурации (см. [Основные концепции модуля](core-concepts.md#конфигурация) ).

### Декларативные ключи перевода (v2.7.0+)

Модуль может централизованно объявлять ключи перевода через класс `I18nClass`. Фреймворк автоматически регистрирует их в системе i18n, без необходимости вручную вызывать `i18n.register()`.

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # Ключи перевода бизнес-логики с плейсхолдерами
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="欢迎你，{name}！",
            zh_TW="歡迎你，{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # Переводы описаний полей конфигурации
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

Подробное описание см. в [документации i18n](../../advanced/i18n.md#рекомендуемый подход через-i18nclass-декларировать-ключи-перевода-v270).

## Асинхронное программирование

### 1. Использование асинхронной библиотеки

```python
# Рекомендуется использовать встроенный HTTP-клиент SDK (асинхронный, с автоматическими логами и статистикой)
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# Также можно использовать sdk.client (результат такой же)
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# Не следует импортировать aiohttp напрямую (неудобно для унифицированного управления в рамках фреймворка)
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# Не следует использовать requests (синхронный, блокирует цикл событий)
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # Блокирует цикл событий
```

### 2. Правильная асинхронная операция

```python
async def handle_command(self, event):
    # Используйте create_task для выполнения трудоемких операций на фоне
    task = asyncio.create_task(self._long_operation())
    
    # Если необходимо дождаться результата
    result = await task
```

### 3. Управление ресурсами

```python
async def on_load(self, event):
    # Клиент SDK уже автоматически управляет пулом соединений, создавать session вручную не нужно
    pass
    
async def on_unload(self, event):
    # Если необходимо использовать собственный клиент, не забудьте очистить ресурсы
    pass

## Обработка событий

### 1. Использование класса-обёртки Event

```python
# Удобный метод с использованием класса-обёртки Event
@command("info")
async def info_command(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}!")

# Вместо прямого доступа к словарю
@command("info")
async def info_command(event):
    user_id = event["user_id"]  # менее наглядно, подвержено ошибкам
```

### 2. Оптимальное использование отложенной загрузки

```python
# Модули обработки команд должны загружаться немедленно
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Модули прослушивателей должны загружаться немедленно
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Модули утилит подходят для отложенной загрузки
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
        self.logger.info("Получено сообщение из группы")
    
    # Не нужно вручную отменять регистрацию, фреймворк обрабатывает это автоматически

## Обработка ошибок

### 1. Классификация и обработка исключений

```python
async def handle_event(self, event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # Ожидаемые бизнес-ошибки
        self.logger.warning(f"Бизнес-предупреждение: {e}")
        await event.reply(f"Ошибка параметров: {e}")
    except aiohttp.ClientError as e:
        # Сетевая ошибка (рекомендуется использовать sdk.client + ClientError)
        # Старый код, использующий напрямую aiohttp, по-прежнему будет работать,
        # но в новом коде рекомендуется использовать систему исключений ErisPulse.
        self.logger.error(f"Сетевая ошибка: {e}")
        await event.reply("Не удалось выполнить сетевой запрос, повторите попытку позже")
    except Exception as e:
        # Неожиданные ошибки
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        await event.reply("Ошибка обработки, свяжитесь с администратором")
        raise
```

### 2. Обработка таймаутов

```python
# Рекомендуется использовать встроенный клиент SDK (включает таймауты и перезапросы)
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"Таймаут запроса: {url}")
        raise

## Система хранения

### 1. Использование транзакций

```python
# Использование транзакций для обеспечения согласованности данных
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ Использование без транзакций может привести к несогласованности данных
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # Если здесь произойдет ошибка, вышеустановленные данные не смогут быть откачены
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. Пакетные операции

```python
# Использование пакетных операций для повышения производительности
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ Несколько вызовов неэффективны
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)

## Логирование

### 1. Рациональное использование уровней логирования

```python
# DEBUG: Подробная информация для отладки (только для разработки)
self.logger.debug(f"Входные параметры: {params}")

# INFO: Информация о нормальном функционировании
self.logger.info("Модуль загружен")
self.logger.info(f"Обработка запроса: {request_id}")

# WARNING: Предупреждения, не влияющие на основную функциональность
self.logger.warning(f"Параметр конфигурации {key} не задан, используется значение по умолчанию")
self.logger.warning("Медленный ответ API, возможно, требуется оптимизация")

# ERROR: Сообщения об ошибках
self.logger.error(f"Не удалось выполнить запрос API: {e}")
self.logger.error(f"Не удалось обработать событие: {e}", exc_info=True)

# CRITICAL: Критические ошибки, требующие немедленной обработки
self.logger.critical("Ошибка подключения к базе данных, бот не может работать корректно")
```

### 2. Структурированное логирование

```python
# Использование структурированного логирования для облегчения анализа
self.logger.info(f"Обработка запроса: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ Использование неструктурированного логирования
self.logger.info(f"Запрос обработан, от пользователя {user_id}, время: {duration} мс")

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
    # Синхронная операция, блокирует цикл событий
    result = self._sync_process(event)

## Безопасность

### 1. Защита чувствительных данных

```python
# Чувствительные данные хранятся в конфигурации
class MyModule(BaseModule):
    def _load_config(self):
        config = self.sdk.config.getConfig("MyModule")
        self.api_key = config.get("api_key")
        
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Укажите действующий API-ключ в config.toml")

# ❌ Жесткое кодирование чувствительных данных
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # Не делайте так!
```

### 2. Валидация входных данных

```python
# Проверка пользовательского ввода
async def process_command(self, event):
    user_input = event.get_text()
    
    # Проверка длины ввода
    if len(user_input) > 1000:
        await event.reply("Слишком длинный ввод, пожалуйста, введите заново")
        return
    
    # Проверка формата ввода
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("Неверный формат ввода")
        return

## Тестирование

### 1. Unit Tests

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

## Развертывание

### 1. Управление версиями

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

Соблюдение семантической версии:
- MAJOR.MINOR.PATCH
- Основная версия: изменения API, несовместимые с предыдущими версиями
- Версия MINOR: новые возможности, сохраняющие обратную совместимость
- Редакция (PATCH): исправления ошибок, сохраняющие обратную совместимость

### 2. Заголовок README

README, созданный командой `epsdk create`, уже содержит встроенный заголовок в стиле ErisPulse (Logo + строка бейджей). Две рекомендуемые конфигурации:

**Режим A — только логотип ErisPulse (по умолчанию):**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**Одинокое предложение**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**Режим B — иконка модуля × логотип ErisPulse (при наличии пользовательской иконки):**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
(строка бейджей такая же, как выше)
</div>
```

При необходимости можно добавить бейджи в стиле GitHub (Stars, Downloads и др.). Логотип также можно скачать в локальную папку проекта (`.github/assets/ErisPulseLogo.png`) и ссылаться на него по относительному пути.

Пожалуйста, верните только полностью переведенный Markdown-код без дополнительных комментариев.

## Related Documentation

- [Getting Started with Module Development](getting-started.md) - Creating your first module
- [Core Concepts of Modules](core-concepts.md) - Understanding module architecture
- [Event Wrapper Class](event-wrapper.md) - Detailed event handling