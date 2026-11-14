# Лучшие практики разработки модулей

> [!TIP]
> **Когда стоит читать этот документ**: рекомендуется прочитать после написания первого модуля (инженерные лучшие практики). Если это не нужно — пропустите, на использование остального функционала это не влияет.


Здесь собраны инженерные соглашения по написанию модулей: асинхронные операции не блокируют цикл событий, конфигурация объявляется декларативно, ресурсы, взятые на хранение у других модулей, освобождаются при выгрузке — следуя этим правилам, вы избежите самых частых проблем разработки модулей: утечек памяти, остаточных фоновых задач и неработающей горячей перезагрузки.

## Проектирование модулей

### 1. Принцип единственной ответственности

Каждый модуль должен отвечать только за одну ключевую функцию:

```python
# Хорошая архитектура: каждый модуль отвечает за одну функцию
class WeatherModule(BaseModule):
    """Модуль запроса погоды"""
    pass

class NewsModule(BaseModule):
    """Модуль запроса новостей"""
    pass

# Плохая архитектура: один модуль отвечает за несколько несвязанных функций
class UtilityModule(BaseModule):
    """Содержит погоду, новости, шутки и другой функционал"""
    pass
```

### 2. Соглашения об именовании модулей

```toml
[project]
name = "ErisPulse-ModuleName"  # Используйте префикс ErisPulse-
```

### 3. Понятное управление конфигурацией

Рекомендуется использовать декларативную конфигурацию (`ConfigClass` + `BaseConfig`) — она даёт типобезопасность, автоматическую генерацию шаблонов, поддержку форм WebUI и другие возможности:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_url: str = field(default="https://api.example.com", metadata={
        "description": {"i18n": "my_module.api_url", "default": "Адрес API"},
    })
    timeout: int = field(default=30, metadata={
        "description": {"i18n": "my_module.timeout", "default": "Тайм-аут (в секундах)"},
    })
    cache_ttl: int = field(default=3600, metadata={
        "description": {"i18n": "my_module.cache_ttl", "default": "Время жизни кэша (в секундах)"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # Типобезопасно, чтение в реальном времени
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

При желании можно продолжать использовать ручной способ чтения/записи хранилища конфигурации (см. [Основные концепции модулей](core-concepts.md#управление-конфигурацией)).

### Декларативные ключи перевода (v2.7.0+)

Модули могут централизованно объявлять ключи перевода через `I18nClass` — фреймворк автоматически зарегистрирует их в системе i18n, вручную вызывать `i18n.register()` не нужно.

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # Бизнес-ключи перевода с заполнителями
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

Подробности использования см. в [документации i18n](../../advanced/i18n.md#рекомендуемый-подход-объявление-ключей-перевода-через-i18nclass-v270).

## Асинхронное программирование

### 1. Используйте асинхронные библиотеки

```python
# Рекомендуется встроенный HTTP-клиент SDK (асинхронный, с автоматическим логированием и статистикой)
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# Также можно использовать через sdk.client (эффект тот же)
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# Не импортируйте aiohttp напрямую (это затрудняет централизованное управление со стороны фреймворка)
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# Не используйте requests (синхронная библиотека, блокирует цикл событий)
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # Блокирует цикл событий
```

### 2. Правильные асинхронные операции

```python
from ErisPulse.Core.Event import Event  # аннотация event: Event настоятельно рекомендуется; автодополнение кастомных методов — см. epsdk types

async def handle_command(self, event: Event):
    # Долгие операции, результат которых нужно дождаться: прямой await (прозрачный жизненный цикл)
    result = await self._long_operation()

async def on_load(self, event: dict):
    # Фоновые задачи (опрос/таймеры/fire-and-forget): используйте self.spawn(),
    # при выгрузке модуля фреймворк гарантированно отменяет их после on_unload, предотвращая утечку из-за удержания self
    self.spawn(self._poll())
```

> [!NOTE]
> Для фоновых задач рекомендуется `self.spawn()` (ErisPulse **2.8.0+**). Начиная с **2.8.3** «голый» `asyncio.create_task`
> также автоматически и неявно привязывается к модулю (Task Factory регистрирует задачи автоматически, при выгрузке гарантируется отмена — утечка ссылки `self` больше не возникает);
> `self.spawn()` остаётся рекомендуемым способом — он поддерживает планирование из сторонних потоков обратно в главный цикл и явное указание `owner=`.
> В версиях **до 2.8.3** «голые» задачи не привязываются к модулю и удерживают ссылку `self`, из-за чего экземпляр модуля не может быть собран
> (утечка при горячей перезагрузке), обязательно используйте `self.spawn()`. Подробнее см. [Управление жизненным циклом](../../advanced/lifecycle.md#принадлежность-фоновых-задач-и-автоматическая-отмена).

### 3. Управление ресурсами

```python
async def on_load(self, event):
    # SDK-клиент автоматически управляет пулом соединений, вручную создавать session не нужно
    pass
    
async def on_unload(self, event):
    # Если используете собственный клиент — не забудьте освободить ресурсы
    pass
```

## Обработка событий

### 1. Используйте класс-обёртку Event

```python
from ErisPulse.Core.Event import Event
# Используйте удобные методы класса-обёртки Event
@command("info")
async def info_command(event: Event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}!")

# Вместо прямого доступа к словарю
@command("info")
async def info_command(event: Event):
    user_id = event["user_id"]  # Менее наглядно, легко ошибиться
```

### 2. Разумное использование ленивой загрузки

```python
# Модуль редких команд: объявите триггеры activate_on — автоматическая активация при поступлении первой совпавшей команды (ленивая загрузка сохраняется)
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "Бросить кубик", "aliases": ["d"]}},
        ])

# Модуль-слушатель с редкими событиями: объявите триггеры событий — автоматическая активация при поступлении события
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# Модули с частыми срабатываниями (нужно обрабатывать каждое сообщение) или модули, которые должны быть готовы сразу при запуске: немедленная загрузка
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Утилитарным модулям подходит ленивая загрузка
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> Полный синтаксис `activate_on` (три формы событий / краткая запись команд и объявление через dict / цепочка отката help) см. в
> [Системе ленивой загрузки модулей](../../advanced/lazy-loading.md#событийная-ленивая-активацияactivate_on).

### 3. Регистрация обработчиков событий

```python
from ErisPulse.Core.Event import Event
async def on_load(self, event):
    # Регистрация обработчиков событий в on_load
    @command("hello")
    async def hello_handler(event: Event):
        await event.reply("Привет!")
    
    @message.on_group_message()
    async def group_handler(event: Event):
        self.logger.info("Получено сообщение в группе")
    
    # Ручная отмена регистрации не нужна — фреймворк сделает это автоматически
```

## Утилитарные модули: обрабатывайте «уведомления о выгрузке», когда храните данные других модулей

**Когда это нужно**: ваш модуль хранит что-то за другие модули (колбэки по таймеру, подписчиков, соединения, записи кэша и т.д.). Если после выгрузки модуля-владельца эти ссылки продолжают удерживаться, его экземпляр никогда не сможет быть освобождён — это самый частый источник утечек памяти в утилитарных модулях.

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class MyToolModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {имя модуля: хранимые данные}

    def register(self, entry):
        owner = on_cleanup(self._drop)   # ① При регистрации встаём в цепочку очистки, вызывающий определяется автоматически
        self._entries.setdefault(owner, []).append(entry)

    def _drop(self, owner: str):
        self._entries.pop(owner, None)   # ② Вызывается фреймворком автоматически при выгрузке чужого модуля: отбрасываем его данные

    async def on_unload(self, event):
        off_cleanup(self._drop)          # ③ Отменяем регистрацию хука перед собственной выгрузкой
```

И это всё — фреймворк гарантирует:

- При **выгрузке / отключении** чужого модуля (или закрытии адаптера) `_drop("имя чужого модуля")` гарантированно будет вызван
- **Определение вызывающего полностью автоматическое**: вызывающий будет корректно опознан и при прямом вызове `sdk.MyToolModule.register(...)` в `on_load`, и при вызове через `sdk.module.call("MyToolModule", "register", ...)`
- Не нужно заботиться о моменте срабатывания — хук срабатывает внутри цепочки очистки фреймворка, до диагностики утечек, без ложных срабатываний

Последствия отказа от интеграции: при полной выгрузке чужого модуля через `purge` его экземпляр не может быть освобождён (диагностика утечек сообщит «не подлежит освобождению»); если чужой модуль к тому же сам не отменяет регистрацию у вас в своём `on_unload`, утечка становится постоянной.

**Обычным модулям (не хранящим данные других модулей) об этом беспокоиться не нужно** — очистка ресурсов фреймворка (команд / обработчиков / маршрутов / фоновых задач и т.д.) при выгрузке выполняется полностью автоматически.

> Подробности о моменте срабатывания, правилах определения вызывающего, тайм-аутах и отказоустойчивости см. в
> [Системе владения · Руководстве по утилитарным модулям](../../advanced/ownership.md#руководство-по-утилитарным-модулямхранение-дескрипторов-других-модулей).

## Обработка ошибок

### 1. Обработка исключений по категориям

```python
from ErisPulse.Core.Event import Event
from ErisPulse.Core.Bases.errors import ClientError

async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # Ожидаемая бизнес-ошибка
        self.logger.warning(f"Бизнес-предупреждение: {e}")
        await event.reply(f"Ошибка параметров: {e}")
    except ClientError as e:
        # Сетевая ошибка (исключения aiohttp нижележащего уровня sdk.client уже автоматически преобразованы)
        self.logger.error(f"Сетевая ошибка {e.method} {e.url}: {e}")
        await event.reply("Сетевой запрос не удался, попробуйте позже")
    except Exception as e:
        # Неожиданная ошибка
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        await event.reply("Обработка не удалась, обратитесь к администратору")
        raise
```

### 2. Обработка тайм-аутов

```python
# Рекомендуется встроенный клиент SDK (со встроенными тайм-аутами и повторами)
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"Тайм-аут запроса: {url}")
        raise
```

## Система хранения данных

### 1. Используйте транзакции

```python
# Используйте транзакции для обеспечения согласованности данных
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ Без транзакций возможна несогласованность данных
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # Если здесь возникнет ошибка, предыдущие установки не удастся откатить
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. Пакетные операции

```python
# Используйте пакетные операции для повышения производительности
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ Многократные вызовы неэффективны
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## Логирование

### 1. Разумное использование уровней логов

```python
# DEBUG: подробная отладочная информация (только при разработке)
self.logger.debug(f"Входные параметры: {params}")

# INFO: информация о нормальной работе
self.logger.info("Модуль загружен")
self.logger.info(f"Обработка запроса: {request_id}")

# WARNING: предупреждения, не влияющие на основной функционал
self.logger.warning(f"Параметр конфигурации {key} не задан, используется значение по умолчанию")
self.logger.warning("API отвечает медленно, возможно, нужна оптимизация")

# ERROR: сообщения об ошибках
self.logger.error(f"Ошибка запроса к API: {e}")
self.logger.error(f"Не удалось обработать событие: {e}", exc_info=True)

# CRITICAL: критическая ошибка, требуется немедленная обработка
self.logger.critical("Не удалось подключиться к базе данных, бот не может нормально работать")
```

### 2. Структурированные логи

```python
# Используйте структурированные логи для удобного разбора
self.logger.info(f"Обработка запроса: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ Неструктурированные логи
self.logger.info(f"Запрос обработан, от пользователя {user_id}, занял {duration} мс")
```

## Оптимизация производительности

### 1. Используйте кэш

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

### 2. Избегайте блокирующих операций

```python
from ErisPulse.Core.Event import Event
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

### 1. Защита чувствительных данных

```python
# Чувствительные данные хранятся в конфигурации (декларативный ConfigClass, поля secret не попадают в логи/экспорт)
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
            raise ValueError("Настройте действительный API-ключ в config.toml")

# ❌ Жёсткое кодирование чувствительных данных
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # Так делать нельзя!
```

### 2. Валидация входных данных

```python
from ErisPulse.Core.Event import Event
# Валидация пользовательского ввода
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # Проверка длины ввода
    if len(user_input) > 1000:
        await event.reply("Ввод слишком длинный, введите заново")
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
        """Тестирование значений конфигурации по умолчанию"""
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
    
    # Имитация события команды
    event = create_test_command_event("hello")
    await module.handle_command(event)
```

## Жизненный цикл HTTP-маршрутов

Жизненный цикл HTTP/WebSocket-маршрутов, регистрируемых модулем через `router`, автоматически управляется фреймворком по **принципу принадлежности**:

- Пространство имён, указанное при регистрации, является идентификатором принадлежности; **при reload / unload фреймворк автоматически очищает все маршруты и ресурсы соединений этой принадлежности**, ручная отмена регистрации не нужна
- Поэтому **в `on_load` нужно безусловно перерегистрировать маршруты**. Не используйте булевы флаги уровня экземпляра для оптимизации «регистрировать только один раз»: горячая перезагрузка конфигурации вызывает stop/start и **повторно использует тот же экземпляр**, остаточный флаг приведёт к **безвозвратной потере** маршрутов после их очистки — это проявляется как 404 от API и устраняется только перезапуском процесса

```python
class MyModule(BaseModule):
    async def on_load(self):
        # Перерегистрация при каждой загрузке безусловно
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

Если нужно заранее вручную выгрузить маршрут (например, динамически отключить какую-то точку входа), можно отменить регистрацию вручную:

```python
from ErisPulse.Core import router

router.unregister_http_route("MyModule", "/api/panel")
```

- Фронтенд/вызывающая сторона в окне горячей перезагрузки может получать от маршрутов 404 — это временное явление; для интерактивных страниц, ориентированных на браузер, рекомендуется настроить ограниченное число автоматических повторов при 404

## Развёртывание

### 1. Управление версиями

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

Придерживайтесь семантического версионирования:
- MAJOR.MINOR.PATCH
- Мажорная версия: несовместимые изменения API
- Минорная версия: новые функции с обратной совместимостью
- Патч-версия: исправления ошибок с обратной совместимостью

### 2. Шапка README

В README, сгенерированном командой `epsdk create`, уже встроена шапка ErisPulse (логотип + строка бейджей). Два рекомендуемых варианта:

**Вариант A — только логотип ErisPulse (по умолчанию):**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**Описание в одну фразу**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/Лицензия-MIT-blue?style=for-the-badge" alt="Лицензия"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Работает_на-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**Вариант B — иконка модуля × логотип ErisPulse (при наличии собственной иконки):**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
(строка бейджей как выше)
</div>
```

При необходимости можно добавить бейджи GitHub Stars, Downloads и другие. Логотип также можно скачать локально в проект (`.github/assets/ErisPulseLogo.png`) и ссылаться на него по относительному пути.

## Связанные документы

### Вернуться к учебному пути

- [Введение в разработку модулей](getting-started.md) - создание первого модуля
- [Основные концепции модулей](core-concepts.md) - понимание архитектуры модулей

### Углублённое изучение по сценариям

- [Класс-обёртка Event](event-wrapper.md) - подробное описание обработки событий
- [Руководство по публикации и магазину модулей](../publishing.md) - публикация готового модуля на PyPI и в магазине модулей