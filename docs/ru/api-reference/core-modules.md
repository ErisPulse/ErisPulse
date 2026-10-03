# API основных модулей

Документация предоставляет краткое справочное руководство по API основных модулей ErisPulse, включая сигнатуры методов и краткие описания. Подробное использование и примеры можно найти по ссылкам "Полная документация" для каждого модуля.

## Модуль Storage

Система хранения пар ключ-значение на базе SQLite, поддерживающая общие SQL-цепочные запросы.

### Основные операции

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### Пакетные операции

```python
sdk.storage.set_multi({"key1": "val1", "key2": "val2"})
values = sdk.storage.get_multi(["key1", "key2"])
sdk.storage.delete_multi(["key1", "key2"])
```

### Транзакционные операции

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Доступ к свойствам

```python
sdk.storage.my_key          # эквивалентно sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # эквивалентно sdk.storage.set("my_key", "val")
```

### SQL-цепочные запросы

Модуль Storage предоставляет гибкий API для построения SQL-запросов с использованием цепочек вызовов, поддерживающий CRUD-операции для пользовательских таблиц.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> Полный API цепочных запросов (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, транзакции и т.д.) см. в [SQL-построителе запросов](../advanced/sql-builder.md).

### Абстракция хранилища

`StorageManager` наследуется от абстрактного базового класса `BaseStorage`, поддерживает расширение другими хранилищами (Redis, MySQL и т.д.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Асинхронный интерфейс

Модули Storage и Config предоставляют асинхронные методы (префикс `a`), которые можно безопасно использовать в асинхронных обработчиках. Синхронные методы сохраняются без изменений.

```python
# Асинхронное хранилище
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# Асинхронные пакетные операции
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# Асинхронная конфигурация
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()
```

## Модуль Config

Управление конфигурационными файлами в формате TOML, поддержка ключей с разделением точками.

### Обзор API

| Метод | Описание |
|------|------|
| `getConfig(key, default)` | Чтение конфигурации, поддержка точечных путей, например `"MyModule.subkey"` |
| `getAllConfig()` | Полный снимок конфигурации (глубокая копия, включая незаписанные значения) |
| `adelConfig(key, immediate)` | Асинхронное удаление ключа конфигурации |
| `delConfig(key, immediate=False)` | Удаление ключа конфигурации (в отличие от сброса), из файла; вызывает событие `config.set` (`new_value=None`) |
| `setConfig(key, value, immediate=False)` | Запись конфигурации. `immediate=True` немедленно сохраняет в файл |
| `force_save()` | Принудительное сохранение конфигурации из памяти в файл |
| `reload()` | Перезагрузка конфигурации из файла |
| `agetConfig(key, default)` | Асинхронное чтение конфигурации |
| `asetConfig(key, value, immediate)` | Асинхронная запись конфигурации |
| `aforce_save()` | Асинхронное принудительное сохранение |
| `areload()` | Асинхронная перезагрузка |

### Примеры

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

snapshot = sdk.config.getAllConfig()          # Полный снимок (глубокая копия)
sdk.config.delConfig("MyModule.deprecated")  # Удаление ключа (отложенная запись)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` по умолчанию использует отложенную запись (каждые 5 секунд сохраняет пакетно), установка `immediate=True` немедленно сохраняет в файл. Изменения конфигурации вызывают событие жизненного цикла `config.set`.
> `delete` также поддерживает отложенную запись и событие `config.set` (`new_value=None`), существующие обработчики `on_config_update` без изменений могут обнаруживать удаление.

## Модуль Logger

Модульная система логирования, основанная на Rich, поддержка под-логгеров и уровня контроля по модулям.

### Основное использование

```python
sdk.logger.debug("Отладочная информация")
sdk.logger.info("Информация о работе")
sdk.logger.warning("Предупреждение")
sdk.logger.error("Ошибка")
sdk.logger.critical("Критическая ошибка")
```

### Под-логгеры

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Логи подмодуля")

child_logger.get_child("utils")  # Поддержка вложенности
```

### Контроль уровня логирования

```python
sdk.logger.set_level("DEBUG")                          # Глобальный уровень
sdk.logger.set_module_level("MyModule", "DEBUG")       # Уровень по модулю

# Поддерживаемые уровни (от низкого к высокому):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE - самый низкий уровень, выводит подробную отладочную информацию (распределение событий, регистрация маршрутов и т.д.)
sdk.logger.set_level("TRACE")                          # Включить все логи
```

### Подписка на логи (режим push)

Для модулей, таких как Dashboard, поддерживаются структурированные логи с фильтрацией и историей.

> **Явная подписка на низкий уровень логирования**: `min_level` подписчика может быть ниже глобального уровня логирования. В этом случае логи низкого уровня **отправляются только соответствующему подписчику**, не выводятся в консоль и не записываются в память, избегая загрязнения основного потока логов.
>
> ```python
> # Глобально INFO, но можно отдельно подписаться на DEBUG логи
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# Способ декоратора
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "Строгий режим:...",
    # }
    pass

# Прямой вызов
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Метод | Описание |
|------|------|
| `handler(id, *, min_level)(func)` | Декоратор/прямой вызов. `id` пустой, используется имя функции. `min_level` может быть ниже глобального уровня (логи низкого уровня отправляются только подписчику, не выводятся в консоль/память). Регистрация автоматически дополняет исторические логи |
| `remove_handler(id)` | Удаление подписчика |

### Управление выводом

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Модуль Adapter

Менеджер адаптеров, управление регистрацией, запуском и остановкой адаптеров для различных платформ.

### Обзор API

| Метод | Описание |
|------|------|
| `get(platform)` | Получение экземпляра адаптера |
| `exists(platform)` | Проверка наличия зарегистрированного адаптера |
| `enable(platform)` / `disable(platform)` | Включение/выключение адаптера |
| `is_enabled(platform)` | Проверка включения |
| `startup(platforms)` / `shutdown(platforms)` | Запуск/остановка адаптера |
| `is_running(platform)` | Проверка запущенности адаптера |
| `list_running()` | Список запущенных адаптеров |
| `platforms` | Список имен всех платформ |
| `get_info(platform)` | Информация о зарегистрированном адаптере (json-safe: meta + имя класса) |
| `get_meta(platform, resolve_i18n=True)` | Метаинформация адаптера (согласование с `module.get_meta`, поддержка i18n-разрешения) |

### События адаптера

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Запрос состояния бота

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> Полный API управления адаптерами см. в [API системы адаптеров](adapter-system.md).

## Модуль Module

Менеджер модулей, управление регистрацией, загрузкой и выгрузкой плагинов.

### Обзор API

| Метод | Описание |
|------|------|
| `get(name)` | Получение экземпляра модуля или ленивого загрузочного прокси (уже зарегистрирован, но не загружен - возвращает прокси) |
| `exists(name)` | Проверка наличия регистрации |
| `is_loaded(name)` | Проверка загрузки |
| `is_enabled(name)` | Проверка включения |
| `enable(name)` / `disable(name)` | Включение/выключение модуля |
| `load(name)` / `unload(name)` | Загрузка/выгрузка модуля |
| `call(module, method, *args, timeout=None, **kwargs)` | Вызов метода сервиса другого модуля (RPC-протокол) |
| `list_registered()` | Список зарегистрированных модулей |
| `list_loaded()` | Список загруженных модулей |
| `get_info(name)` | Получение информации о модуле |
| `get_status_summary()` | Получение сводки состояния модуля |

### Доступ к свойствам

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # Эквивалентный быстрый способ
```

### Взаимодействие между модулями (RPC)

```python
# Протокольный вызов: типизированные ошибки / ленивая активация модуля / присвоение владельца / семантика таймаута
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Разница между `module.call()` и прямым доступом к свойству сервиса `sdk.module.Chat.get_history(...)`:

| | `module.call()` | Прямой доступ к свойству |
|---|---|---|
| Цель не зарегистрирована/не включена | Выбрасывает `ModuleNotAvailableError` | Выбрасывает `AttributeError` |
| Ленивая загрузка модуля | Автоматически активируется | Асинхронная инициализация модуля выбрасывает RuntimeError |
| `current_owner` | Присваивается к целевому модулю | Сохраняется вызывающий модуль |
| Таймаут | По умолчанию 30 с, можно перезаписать | Нет |
| Аудит scope | `actions.<вызывающий модуль>.call` | Нет |

### Сервисный контракт (meta.services)

Сервисная сторона в `get_meta()` в поле `services` объявляет белый список публичных методов (в симметрии с `commands`), после объявления вызовы ограничиваются:

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **По умолчанию = для разработчиков незаметно**: если не объявлено `services`, любой **публичный** метод может быть вызван (обратная совместимость), методы с подчеркиванием всегда запрещены; основной контроль ограничений на стороне пользователя через scope-конфигурацию
- После объявления: только методы из белого списка доступны, при выходе за границы выбрасывается `ServiceNotProvidedError`
- Ограничения для вызывающей стороны: `scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**Описание сервиса (description)**: `services` поддерживает форму dict для описания каждого сервиса (поддержка строк или i18n-словарей), используется для каталога сервисов / описания точек вызова AI:

```python
return ModuleMeta(
    services=[
        "get_history",                              # Простая форма: описание автоматически берется из первой строки docstring метода
        {"name": "translate", "description": "Перевести текст на указанный язык"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "Суммаризировать диалог"}},
    ],
)
```

Приоритет разбора описания: **явное description (i18n-разрешение в текущем языке) > первая строка docstring метода > пустая строка**.

### Каталог сервисов (services)

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'Получить историю сессии'}]}

sdk.module.services("Chat")  # Только для указанного модуля
```

Выводятся только модули с явно объявленным `meta.services`; каждый сервис сопровождается строкой сигнатуры метода и описанием, что служит основой для данных, предоставляемых AI.

> Направленная доставка событий относится к уровню жизненного цикла: `lifecycle.emit(event, data, to="ModuleName")`, подробнее см. [Взаимодействие между модулями](../advanced/module-communication.md).

## Модуль Lifecycle

Система управления жизненным циклом на основе событий, предоставляет функции отправки и прослушивания событий.

### Обзор API

| Метод | Описание |
|------|------|
| `on(event, priority=0)` | Декоратор для регистрации обработчика события, поддержка точечного сопоставления и шаблонов `*` |
| `register(event, handler, priority=0)` | Функциональная регистрация обработчика |
| `unregister(event, handler=None)` | Удаление обработчика |
| `emit(event, data, to=None)` | Асинхронная отправка события; `to` указывает владельца для направленной доставки |
| `emit_sync(event, data, to=None)` | Синхронная отправка события (для асинхронных обработчиков через create_task) |
| `submit_event(event_type, msg, data, source, to=None)` | Представление события в стандартном формате (совместимо со старыми версиями) |
| `start_timer(id)` / `stop_timer(id)` | Таймер производительности |

### Примеры

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Инициализация модуля: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Событие модуля: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})

# Направленная доставка: событие доставляется только зарегистрированным хукам модуля Chat
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")
```

> Полный список стандартных событий и подробное использование см. в [Управление жизненным циклом](../advanced/lifecycle.md).

## Модуль Router

Менеджер маршрутизации HTTP/WebSocket, на базе FastAPI + Uvicorn, поддержка декораторов маршрутизации, промежуточных обработчиков, группировки, ограничения скорости, CORS.

> Полная документация по API маршрутизатора (декораторы маршрутизации, WebSocket, промежуточные обработчики, ограничение скорости, CORS, заголовки безопасности и т.д.) см. в [Менеджер маршрутизации](../advanced/router.md).

### Краткий справочник

```python
# HTTP-маршрутизация
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket-маршрутизация
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# Группировка маршрутов
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## Модуль HTTP-клиента

Единый сетевой клиент, объединяет HTTP-запросы, WebSocket-соединения, управление пула соединений, автоматические повторные попытки, статистику запросов и интеграцию с событиями жизненного цикла.

> Полная документация по сетевому клиенту (методы запросов, объекты ответов, WebSocket-клиент, система исключений и т.д.) см. в [Сетевой клиент](../advanced/http-client.md).

### Краткий справочник

```python
from ErisPulse.Core import client

# HTTP-запрос
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## SDK отладка

### dump_state()

Экспорт текущего состояния работы фреймворка в виде снимка, используется для отладки и диагностики.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

Возвращаемая структура содержит состояние следующих подсистем:

| Поле | Описание |
|------|------|
| `sdk` | Состояние инициализации SDK, версия Python, платформа, временная метка |
| `adapters` | Список зарегистрированных/запущенных адаптеров, онлайн-статус ботов на платформах |
| `modules` | Список зарегистрированных/включенных/отключенных/лениво загружаемых модулей |
| `events` | Количество обработчиков событий по типам (message/notice/request/meta/commands) |
| `router` | Состояние сервера, количество HTTP/WebSocket-маршрутов |

> [!NOTE]
> Добавлено в ErisPulse **2.5.2+**

## Взаимодействие (Interaction)

Управление ожиданием ответа и сессионными блокировками (сессионные аренды) (sdk.interaction).

### Основные методы

```python
# Напоминание сессии: если в течение 5 минут нет ответа, отправляется напоминание, ответ пользователя автоматически отменяет напоминание
reminder = event.remind(300, "Еще здесь?")
reminder.cancel()  # Ручная отмена

# Увеличение срока: по истечении времени срабатывает обязательно (не отменяется ответом)
event.escalate(1800, lambda e: notify_master("30 минут не обработано"))

# Ожидание нескольких путей: первый поступивший ответ принимается
which, reply = await event.select(
    event.expect(pattern="Согласен*", user="A"),
    event.expect(pattern="Отказ*", user="B"),
    timeout=60,
)

# Сессионное ожидание: любой ответ из той же группы может быть принят
reply = await event.wait_reply(session=True, prompt="Кто-нибудь может помочь?")

# Запрос текущего владельца сессии (кто взаимодействует с пользователем)
owner = sdk.interaction.get_owner_of(event)

# Заявление сессионной блокировки (если занято, возвращает None)
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # Исключительное взаимодействие
    finally:
        lease.release()

# Форма контекстного менеджера (если занято, выбрасывается SessionOccupiedError)
with sdk.interaction.hold(event) as lease:
    ...

# Статистика ожидания сессий
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

При выгрузке модуля / остановке адаптера их ожидающие запросы и таймеры автоматически отменяются (ожидающие немедленно получают `None`), при попадании ответа автоматически проверяется права scope (если пользователь заблокирован / модуль отключен, ожидание завершается).

> [!NOTE]
> Функциональность добавлена в ErisPulse **2.8.0+**

## Транскрипт (Transcript)

Автоматическая запись и запрос последних сообщений в сессии (sdk.transcript), используется как базовый компонент для модулей контекста, таких как AI-диалоги, предотвращение повторов и т.п.

### Основные методы

```python
# Удобный запрос (рекомендуется): последние 20 сообщений текущей сессии (включая пользователя и бота, по времени по возрастанию)
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# API менеджера
sdk.transcript.append(event, "user", "текст")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

Конфигурация (`ErisPulse.transcript`): `enabled` (по умолчанию включено), `max_per_session` (лимит на сессию, по умолчанию 50), `ttl_hours` (время жизни по умолчанию 168 часов). Данные хранятся в отдельной SQLite-таблице, при превышении лимита или истечении срока - ленивая очистка.

> [!NOTE]
> Функциональность добавлена в ErisPulse **2.8.0+**

## Связанные документации

- [API системы событий](event-system.md) - API модуля Event
- [API системы адаптеров](adapter-system.md) - API управления адаптерами
- [SQL-построитель запросов](../advanced/sql-builder.md) - Полная документация по цепочечным SQL-запросам
- [Менеджер маршрутизации](../advanced/router.md) - Полная документация по менеджеру маршрутизации
- [Сетевой клиент](../advanced/http-client.md) - Полная документация по сетевому клиенту
- [Управление жизненным циклом](../advanced/lifecycle.md) - Полная документация по управлению жизненным циклом