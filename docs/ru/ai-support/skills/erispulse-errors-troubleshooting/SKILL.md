---
name: erispulse-errors-troubleshooting
description: "适用于：遇到异常/组件不工作时的诊断路径：异常总览、排障指南、bug 追踪。覆盖场景：Все пользовательские исключения ErisPulse наследуются от `ErisPulseError`. Исключения底层 библиотек (например, aiohttp, aiomysql и др.) будут перехвачены внутри фреймворка и преобразованы в соответствующие исключения ErisPulse. В коде бизнес-логики **не следует зависеть от типов исключений底层 библиотек**.。This document records known bugs of the ErisPulse SDK and their repair status, arranged in chronological order of repair version.。"
---

# ErisPulse 异常体系与排障

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 异常捕获总览

> 来源: `docs/ru/advanced/errors.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ru/advanced/errors.md）

# Система исключений и руководство по обработке

> [!NOTE]
> **Обязательное к прочтению на уровне L1** — одна из пяти ключевых статей в "пути чтения" на главной странице, обязательна для разработки модулей.

Все пользовательские исключения ErisPulse наследуются от `ErisPulseError`. Исключения底层 библиотек (например, aiohttp, aiomysql и др.) будут перехвачены внутри фреймворка и преобразованы в соответствующие исключения ErisPulse. В коде бизнес-логики **не следует зависеть от типов исключений底层 библиотек**.

{!--< tips >!--}
1. Для широкого перехвата: перехватите `ErisPulseError` (базовый класс всех исключений фреймворка)
2. Для точной обработки: перехватывайте по модулям (например, `ModuleCallTimeoutError`, `StorageUnreachableError`)
3. Операции с хранилищем по умолчанию не выбрасывают исключения: при сбое записывается в лог и возвращается `False / None / default`; для отслеживания изменений состояния подключений подписывайтесь на события `storage.unreachable` / `storage.recovered`
{!--< /tips >!--}

## Обзор исключений

```text
ErisPulseError                      # Базовый класс всех исключений фреймворка
├── ClientError                     # Базовый класс исключений HTTP/WS клиента (Core/client)
│   ├── ClientConnectionError       # Ошибка на уровне соединения: неудача разрешения DNS, отказ в подключении, недоступность сети
│   ├── ClientTimeoutError          # Ошибка таймаута запроса
│   └── HTTPStatusError             # Ошибка HTTP статус-кода (например, 4xx/5xx и raise_for_status)
├── WebSocketError                  # Базовый класс исключений WebSocket (WebSocket соединение в Core/client)
│   └── WebSocketDisconnect         # Отключение WebSocket (общее для сервера/клиента)
├── ConnectionRegistryError         # Базовый класс исключений реестра соединений (Core/connections, 2.10+)
│   ├── ConnectionNotFoundError     # Соединение не существует/было отключено и отменено (connections.get/close)
│   └── ConnectionPermissionError   # Закрытие чужого соединения без прав (закрытие доступно только создателю)
├── StorageError                    # Базовый класс исключений хранилища (Core/storage)
│   └── StorageUnreachableError     # Недоступен бэкенд хранилища (исчерпаны попытки подключения: недоступна база данных/ошибка учетных данных)
├── InteractionError                # Базовый класс исключений интерактивной сессии (Core/Event/interaction)
│   ├── InteractionCancelled        # Приостановленное ожидание/аренда отменена (wait_reply возвращает None)
│   └── SessionOccupiedError        # Исключительная аренда сессии занята (hold() не удалось получить)
├── ModuleError                     # Базовый класс исключений модульной системы (Core/module)
│   └── ModuleCallError             # Базовый класс исключений вызова модуля
│       ├── ModuleNotAvailableError # Целевой модуль не зарегистрирован/не активен/инициализация не удалась (включая ленивую загрузку)
│       ├── ServiceNotProvidedError # Целевой модуль не объявил эту услугу (не в белом списке meta.services)
│       └── ModuleCallTimeoutError  # Выполнение вызываемого метода превысило таймаут (по умолчанию 30s)
├── ShadowError                     # Базовый класс исключений теневого модуля (Core/shadow)
│   ├── ShadowStateError            # Недопустимое состояние: целевой модуль не загружен/уже есть активный теневой модуль/не привязан теневой модуль (start/dismiss)
│   ├── ShadowSourceError           # Источник теневого модуля недоступен: путь не существует/отсутствует загрузчик/ошибка загрузки (start)
│   └── ShadowPromoteError          # Ошибка повышения: теневой модуль не зарегистрирован/не загружен/загрузчик не имеет снимка/ошибка перезагрузки (promote)
└── StrictModeError                 # Критическое нарушение строгого режима (прерывает процесс запуска, loaders/strict)
```

## Структурированные свойства

После перехвата исключения можно получить структурированные свойства (без необходимости разбора текста сообщения):

| Исключение | Свойства |
|------|------|
| `ClientError` (с подклассами) | `.url` URL запроса, `.method` метод запроса, `.attempts` количество попыток (когда исчерпаны повторные попытки) |
| `HTTPStatusError` | `.status` код состояния, `.message` сообщение ответа |
| `WebSocketDisconnect` | `.code` код закрытия, `.reason` причина закрытия |
| `ConnectionNotFoundError` | `.connection_id` идентификатор подключения |
| `ConnectionPermissionError` | `.connection_id` идентификатор целевого подключения, `.owner` владелец подключения |
| `StorageUnreachableError` | `.backend` имя бэкенда (sqlite/mysql/postgres), `.cooldown` время охлаждения в секундах |
| `ModuleCallError` (с подклассами) | `.module` имя целевого модуля, `.method` имя целевого метода |
| `ModuleCallTimeoutError` | Наследует `.module/.method`, также есть `.timeout` лимит времени ожидания (секунды) |
| `InteractionCancelled` | `.reason` причина отмены, `.wait_key` ключ сессии |
| `SessionOccupiedError` | `.wait_key` ключ сессии, `.owner` владелец |
| `StrictModeError` | `.violations` список нарушений |

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await sdk.client.post(url, json=payload)
except ClientError as e:
    print(f"Запрос не удался {e.method} {e.url}, всего попыток {e.attempts}: {e}")
```

## Описание исключений и места их возникновения

### Серия исключений Client — `Core/client.py` / `Core/Bases/client.py`

Исключения `sdk.client` / HTTP-клиента и WebSocket-клиента при发起 запросов:

| Исключение | Место возникновения | Типичные сценарии |
|-----------|---------------------|-------------------|
| `ClientError` | Уровень обёртки запросов | Другие клиентские ошибки (низкоуровневые aiohttp-исключения уже преобразованы) |
| `ClientConnectionError` | Этап установки соединения | Целевой сервис недоступен, DNS-ошибка, соединение отклонено |
| `ClientTimeoutError` | Этап выполнения запроса | Превышение времени ожидания запроса |
| `HTTPStatusError` | `raise_for_status()` | Код состояния ответа 4xx/5xx |

```python
from ErisPulse.Core.Bases.errors import ClientTimeoutError

try:
    resp = await sdk.client.get("https://api.example.com", timeout=5)
except ClientTimeoutError:
    ...
```

### Серия исключений WebSocket — `Core/client.py` (`send` / `receive`)

| Исключение | Место возникновения | Типичные сценарии |
|-----------|---------------------|-------------------|
| `WebSocketError` | Методы WS-приёма/передачи | Соединение закрыто, получено неожиданное сообщение, низкоуровневые WS-исключения |
| `WebSocketDisconnect` | Методы WS-приёма/передачи | Удалённая сторона корректно разорвала соединение (фреймворк автоматически переподключится) |

### Серия исключений регистрации соединений — `Core/connections.py` (2.10+)

| Исключение | Место возникновения | Типичные сценарии |
|-----------|---------------------|-------------------|
| `ConnectionNotFoundError` | `connections.get` / `assign` / `dismiss` / `close` | Идентификатор соединения не существует или уже отключён |
| `ConnectionPermissionError` | Некорректный вызов `conn.close()` | Переключение модулей при закрытии чужого соединения (отправка и группы не ограничены) |

### Серия исключений Storage — `Core/storage` / `Core/Bases/sql_base.py`

| Исключение | Место возникновения | Типичные сценарии |
|-----------|---------------------|-------------------|
| `StorageError` | Уровень хранения | Базовый класс исключений, связанных с хранением |
| `StorageUnreachableError` | Этап создания пула | База данных недоступна / неверные учетные данные / сетевая изоляция, исчерпаны попытки повтора |

> **Семантика неудачных операций хранения**: Операции KV и запросов по умолчанию **не выбрасывают** исключений — в случае неудачи запись в лог ERROR и возврат `False` / `None` / `default` (чтобы избежать блокировки работы фреймворка из-за проблем с соединением). Следовательно, бизнес-код обычно **не** перехватывает `StorageUnreachableError` (он в основном используется для прямого взаимодействия с底层存储 или пользовательских backends). Для получения информации о состоянии соединения во время выполнения следует подписываться на события жизненного цикла `storage.unreachable` / `storage.recovered` (см. [События жизненного цикла](lifecycle.md#Состояние_соединения_хранилища)).

Поведение при неудачном подключении описано в разделе [Backend хранения → Поведение при неудачном подключении](storage-backends.md#Поведение_при_неудачном_подключении).

### Взаимодействие — `Core/Event/interaction.py`

`wait_reply` / сеанс аренды / таймер напоминания:

| Исключение | Место возникновения | Типичные сценарии |
|-----------|---------------------|-------------------|
| `InteractionError` | Уровень взаимодействия сессии | Базовый класс исключений сессии взаимодействия |
| `InteractionCancelled` | При отмене ожидания | Установлено на ожидаемом future (ожидание может перехватить и получить `.reason`) |
| `SessionOccupiedError` | При неудачной аренде `hold()` | Сеанс уже занят другим владельцем (`.owner` позволяет узнать владельца) |

При отмене ожидания (выгрузка модуля / закрытие платформы / новое ожидание в той же сессии заменяет предыдущее), `wait_reply` **возвращает `None`** вместо выброса исключения (`InteractionCancelled` внутренне преобразуется); для различения причин отмены следует перехватывать его напрямую.

### Серия исключений Module — `Core/module.py` (`sdk.module.call`)

| Исключение | Место возникновения | Типичные сценарии |
|-----------|---------------------|-------------------|
| `ModuleError` | Система модулей | Базовый класс исключений системы модулей |
| `ModuleCallError` | `module.call()` | Базовый класс исключений вызова модуля |
| `ModuleNotAvailableError` | `module.call()` / ленивое получение атрибута | Целевой модуль не зарегистрирован / не включён / инициализация не удалась |
| `ServiceNotProvidedError` | `module.call()` | Метод не объявлен в белом списке `meta.services` целевого модуля |
| `ModuleCallTimeoutError` | `module.call()` | Вызываемая корутина превысила время ожидания (по умолчанию 30 сек.) |

"Целевой модуль недоступен" в зависимости от пути доступа:

| Путь доступа | Исключение |
|--------------|------------|
| `await sdk.module.call("X", "method")` | `ModuleNotAvailableError` (типизированное) |
| `sdk.module.X.attr` (ленивое получение атрибута, после неудачной инициализации) | `ModuleNotAvailableError` |
| `sdk.module.X` (при обращении к неактивированному модулю) | `AttributeError` (стандартное поведение Python, `hasattr` зависит от этой семантики) |

```python
from ErisPulse.Core.Bases.errors import ModuleNotAvailableError, ServiceNotProvidedError

try:
    history = await sdk.module.call("Chat", "get_history", session_id, n=20)
except ModuleNotAvailableError:
    ...  # Целевой модуль не существует / не включён
except ServiceNotProvidedError:
    ...  # Целевой модуль не предоставляет этот сервис
```

### Серия исключений Shadow — `Core/shadow.py` (тенированные модули)

| Исключение | Место возникновения | Типичные сценарии |
|-----------|---------------------|-------------------|
| `ShadowError` | Механизм тенирования | Базовый класс исключений тенирования (общий перехват всех ошибок теней) |
| `ShadowStateError` | `shadow_start()` / `dismiss_shadow()` | Цель не загружена / уже активная тень / тень не привязана |
| `ShadowSourceError` | `shadow_start()` | Исходный путь не существует / отсутствует загрузчик плагинов / класс для загрузки отсутствует / загрузка не удалась |
| `ShadowPromoteError` | `promote_shadow()` | Тень не зарегистрирована / не загружена / загрузчик не поддерживает снапшоты / неудачная перезагрузка при повышении |

### Внутренняя проверка параметров фреймворка (ValueError)

Проверка параметров строителя запросов к хранилищу (пустой тип столбца, `Insert` не dict, небезопасный тип столбца и т.д.) выбрасывает стандартный `ValueError` — такие ошибки относятся к **ошибкам программирования на этапе разработки**, нормальный бизнес-код не должен перехватывать их, а должен исправлять вызов.

Неудача стандартных действий адаптера **не выбрасывает исключений**: возвращается словарь ответа с `retcode` (семантика протокола, например, `retcode=10002` означает, что действие не реализовано) — это параллельный канал ошибок по сравнению с `ClientError` на уровне клиента. При разработке адаптера необходимо обрабатывать оба канала.

## Рекомендации по перехвату

```python
from ErisPulse.Core import ErisPulseError  # Базовый класс экспортируется через Core

try:
    ...
except ErisPulseError as e:
    ...  # Общий перехват: все пользовательские исключения фреймворка
```

- При разработке модулей: перехватывайте по необходимости (см. таблицу выше), в самом внешнем уровне можно использовать `ErisPulseError` для общего перехвата
- Все исключения экспортируются через `ErisPulse.Core` (включая `SessionOccupiedError` / `InteractionCancelled` / `StrictModeError`), также можно импортировать из `ErisPulse.Core.Bases.errors`
- Полное определение см. в `src/ErisPulse/Core/Bases/errors.py`

## Отключение шумного складывания

При остановке (или отмене фонового цикла) долгоживущих процессов, цикл событий часто выводит серию бесполезных сообщений вида `Task was destroyed but it is pending!`, которые являются шумом от интерпретатора. Встроенная в фреймворк **функция складывания подобных шумов** позволяет за 2-секундный интервал снизить уровень подобных сообщений до TRACE, объединить их и вывести только один раз, добавив в конец суффикс «(ещё N подобных сообщений было складываний)». Это сознательное снижение шума: наличие суффикса складывания не означает, что фреймворк подавил настоящие исключения. Бизнес-исключения (все категории в таблице выше) выводятся полностью. Складывание применяется только к шумам от интерпретатора при завершении, бизнес-исключения не затрагиваются. Какие уровни исключений заслуживают сохранения в логах, а какие можно снизить/складывать, определяется по правилам [инженерной надежности ·分级异常留痕](../styleguide/engineering.md#1-异常留痕分级).

## Связанные документы

Выберите в зависимости от намерения:

- **Операции с хранилищем возвращают `False` / `None`, хотите узнать статус соединения** → [Хранилище · Поведение при сбое соединения](storage-backends.md#Поведение-при-сбое-соединения), или подписка на [события storage.unreachable / storage.recovered](lifecycle.md#Состояние-соединения-с-хранилищем)
- **`wait_reply` возвращает `None`, хотите узнать, что отменило ожидание** → [Система интерактивных сессий](interaction.md) (таблица причин отмены)
- **`module.call` выбрасывает исключение вызова модуля** → [Межмодульная коммуникация](module-communication.md)
- **Ошибки подключения / WebSocket** → [Сетевой клиент](http-client.md) (иерархия ClientError) и [Пул соединений и трансляции](connections.md) (исключения регистра соединений)

## 已知问题追踪

> 来源: `docs/ru/bug-tracker.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ru/bug-tracker.md）

# Bug Tracker

This document records known bugs of the ErisPulse SDK and their repair status, arranged in chronological order of repair version.

> **To the reader**
> No software is inherently perfect, and even the most careful developers may leave small errors. This tracker includes only issues that have a practical impact on operation—those too minor to even reach the "minor" level will not appear here. The list may seem to have a large number of "severe" items, but the original intention of publicly recording these bugs is to make troubleshooting and tracing smoother, not to create anxiety: problems that can be seen, recorded, and repaired are proof that the project is constantly improving. There is no need to be anxious when seeing this list; it is a troubleshooting tool, not a source of fear.

> **How to read & maintenance convention**
> - Each bug record contains structured fields such as problem description, root cause analysis, affected version range, repair solution, etc. It is recommended to check the "affected version" before upgrading to see if it covers the current used version.
> - If you need to add a new bug item, please supplement content at the corresponding position, following the field specifications and severity/type classification below.

---

## Field Description

### Mandatory Fields

| Field | Description |
|------|------|
| **Problem** | The external manifestation of the bug, the abnormal phenomenon observable by users. Try to provide error messages or typical scenarios |
| **Cause** | Root cause analysis, pointing to specific code defects (including "root cause chain" diagrams for complex scenarios) |
| **Affected Version** | Affected version interval, format `introduced version - fixed version` (including both dev versions) |
| **Fixed Version** | The specific version number that fixed the bug |
| **Fixed Content** | Brief description of the repair solution, including key code changes |
| **Fixed Date** | The release date of the corresponding repair version, in `YYYY/MM/DD` format |
| **Severity** | As per the "Severity Classification" below |
| **Type** | As per the "Type Classification" below, can be combined (e.g., `Adapter / Router`) |

### Optional Fields

| Field | Description | Applicable Scenarios |
|------|------|---------|
| **Reproduction Steps** | The minimal reproducible path to trigger the bug | Complex bugs, occasional bugs are recommended to supplement |
| **关联** | Related Issue / PR / Commit links | Supplement when there are external discussion records |
| **Regression Test** | Test case location for verifying repair and preventing regression | Supplement when corresponding pytest cases are written |

---

## Severity Classification

| Identifier | Level | Judgment Standard | Typical Manifestations |
|------|------|---------|---------|
| 🔴 | Severe | Causes process crash, data loss/damage, core functionality completely unusable, security vulnerabilities | OOM Kill, message cannot be sent, module cannot be loaded, hot reload failure |
| 🟡 | Medium | Function abnormal but has workaround, non-core functionality failure, occasional problems | Status judgment error, repeated trigger, cache expiration, inaccurate error prompt |
| 🟢 | Minor | Does not affect core functionality, only code quality or experience issues, potential risks not triggered | Deprecated API, dead code, missing warning logs |

---

## Type Classification

| Type | Coverage Range |
|------|---------|
| Configuration System | `ConfigManager`, configuration read/write, configuration Schema, hot update |
| Event System | `Event` module (command/message/notice/request/meta), event distribution, processor registration |
| Adapter | `AdapterManager`, `BaseAdapter`, account parsing, Bot status, middleware |
| Router | `RouterManager`, HTTP/WebSocket/SSE routing, rate limiting, CORS |
| Client | `HttpClient`, `ClientWebSocket`, aiohttp wrapper |
| Storage | `StorageManager`, SQLite, SQL builder, nested key |
| Loading System | `Loader`, `LazyModule`, `ModuleInitializer`, strict mode, module discovery |
| CLI | `epsdk` command, `init`/`run`/`install`, parameter parsing, signal handling |
| Runtime | `sdk.run`/`restart`/`uninit`, lifecycle, signal, subprocess |

---

## Item Template

When adding a new bug item, follow the following format:

```markdown
### [BUG-XXX] Title

**Problem**: Problem description (error message or typical phenomenon)
**Cause**: Root cause analysis
**Affected Version**: Introduced version - Fixed version
**Fixed Version**: x.x.x
**Fixed Content**: Repair solution
**Fixed Date**: YYYY/MM/DD

<!-- Optional fields -->
**Reproduction Steps**: (Recommended to supplement for complex bugs)
**关联**: (Issue/PR links)
**Regression Test**: (Test case path)

**Severity**: 🔴 Severe | 🟡 Medium | 🟢 Minor
**Type**: Configuration System / Event System / Adapter / Router / Client / Storage / Loading System / CLI / Runtime
```

---

## Statistics Overview

| Severity | Quantity |
|--------|------|
| 🔴 Severe | 16 |
| 🟡 Medium | 26 |
| 🟢 Minor | 3 |
| **Total** | **45** |

| Type | Quantity |
|------|------|
| Event System | 12 |
| Configuration System | 12 |
| Adapter | 7 |
| CLI | 3 |
| Storage | 3 |
| Loading System | 4 |
| Router | 2 |
| Client | 1 |
| Runtime | 1 |

> Note: A single bug can belong to multiple types, the above table counts by primary type.  
> Note: BUG-028 / BUG-031 numbering gaps (abandoned during registration, numbering stability is maintained by not recycling or reordering).

---

## Fixed Bugs

### [BUG-001] Event handler duplicate registration leads to multiple event processing

**Problem**: When using multiple `@message` / `@notice` decorators to register handlers, the same event is triggered multiple times, causing commands to be executed multiple times and logs to be output repeatedly.

**Cause**: `BaseEventHandler` registers handlers to the adapter event bus without deduplication logic. Each decorator mounts once to the bus, and the event is called multiple times during distribution.

**Affected Version**: 2.2.0-dev.0 - 2.2.1-dev.0

**Fixed Version**: 2.2.1-dev.0

**Fixed Content**: Optimize `BaseEventHandler` to ensure each event type registers only once to the adapter bus, avoiding multiple triggers.

**Fixed Date**: 2025/08/18

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-002] Init command adapter configuration path type error

**Problem**: When using the `ep init` command for interactive initialization, selecting the configuration adapter results in a type error:

```
Interactive initialization failed: unsupported operand type(s) for /: 'str' and 'str'
```

**Cause**: In version 2.3.7, when adjusting the configuration file path, the method parameter type is inconsistent. `_configure_adapters_interactive_sync` receives a `str` type parameter, but internally uses the `Path` `/` operator to concatenate paths.

**Affected Version**: 2.3.7 - 2.3.9-dev.1

**Fixed Version**: 2.3.9-dev.1

**Fixed Content**: Change the parameter type of `_configure_adapters_interactive_sync` from `str` to `Path`, and pass a `Path` object directly when calling.

**Fixed Date**: 2026/03/23

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-003] Command events become invalid after restart

**Problem**: After calling `sdk.restart()`, commands registered via `@command` cannot be triggered, manifested as the robot not responding after sending a command.

**Cause**: After `adapter.shutdown()` clears the event bus, the `_linked_to_adapter_bus` status of `BaseEventHandler` is not reset to `False`, causing the `_process_event` method to think it is already mounted to the adapter bus and skip the re-mounting operation.

**Affected Version**: 2.2.x - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fixed Content**: Introduce `_linked_to_adapter_bus` status tracking. After `_clear_handlers()` disconnects the bus, the next `register()` automatically re-mounts, adapting to shutdown/restart scenarios.

**Fixed Date**: 2026/04/09

**Severity**: 🔴 Severe

**Type**: Event System

---

### [BUG-004] Lifecycle event handlers not cleared

**Problem**: After `sdk.restart()`, old lifecycle event handlers still exist and are repeatedly triggered, causing the same event to be processed multiple times.

**Cause**: The `lifecycle._handlers` dictionary is never cleared in `uninit()`, so old handlers and new handlers both exist after restart.

**Affected Version**: 2.3.0 - 2.4.0-dev.2

**Fixed Version**: 2.4.0-dev.3

**Fixed Content**: Clear `lifecycle._handlers` in the cleanup process of `Uninitializer` (after all events are submitted), adapting to shutdown/restart scenarios.

**Fixed Date**: 2026/04/09

**Severity**: 🟡 Medium

**Type**: Runtime

---

### [BUG-005] Event.is_friend_add/is_friend_delete detail_type inconsistent with OB12 standard

**Problem**: `Event.is_friend_add()` checks `detail_type == "friend_add"`, `Event.is_friend_delete()` checks `detail_type == "friend_delete"`, but OneBot12 standard defines the `detail_type` values as `"friend_increase"` and `"friend_decrease"`. This is inconsistent with the values used in `notice.py`'s `on_friend_add`/`on_friend_remove` decorators, causing the corresponding `is_friend_add()`/`is_friend_delete()` judgment methods to return `False` when handlers registered via decorators are triggered.

**Cause**: `wrapper.py` uses non-standard naming, while `notice.py` uses the correct OB12 standard naming.

**Affected Version**: Since implementation

**Fixed Version**: 2.4.2-dev.1

**Fixed Content**: Change the matching value of `is_friend_add()` from `"friend_add"` to `"friend_increase"`, and `is_friend_delete()` from `"friend_delete"` to `"friend_decrease"`.

**Fixed Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-006] adapter.clear() does not clear _started_instances, causing incorrect state after restart

**Problem**: The `AdapterManager.clear()` method clears `_adapters`, `_adapter_info`, processors, and `_bots`, but omits `_started_instances`. If the adapter is running and `clear()` is called, `_started_instances` retains dangling references, causing incorrect state judgment after restart.

**Cause**: When `_started_instances` was introduced in 2.4.0-dev.1, it was not cleared synchronously in `clear()`.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fixed Content**: Add `self._started_instances.clear()` in the `clear()` method.

**Fixed Date**: 2026/04/13

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-007] command.wait_reply() uses deprecated asyncio.get_event_loop()

**Problem**: The `CommandHandler.wait_reply()` method uses `asyncio.get_event_loop()` to create futures and get timestamps, which has been deprecated in Python 3.10+. In asynchronous contexts, `asyncio.get_running_loop()` should be used. This is inconsistent with `wrapper.py`'s `wait_for()` method, which uses `get_running_loop()`.

**Cause**: The old API was used during development, and the newly added `wait_for()` method used the correct API but did not retroactively fix the old code.

**Affected Version**: 2.3.0-dev.0

**Fixed Version**: 2.4.2-dev.1

**Fixed Content**: Replace two instances of `asyncio.get_event_loop()` in `command.py` with `asyncio.get_running_loop()`.

**Fixed Date**: 2026/04/13

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-008] Bot offline events are repeatedly submitted during shutdown

**Problem**: When calling `adapter.shutdown()` to close all adapters, `_update_bot_status()` repeatedly submits Bot offline events during the shutdown process, causing the same batch of Bots to be marked offline multiple times and triggering multiple `adapter.bot.offline` lifecycle events.

**Cause**: The Bot status tracking system introduced in 2.4.0-dev.1 did not set a "shutting down" flag during `shutdown()`, so `_update_bot_status()` could not distinguish between normal offline and cascading offline during shutdown.

**Affected Version**: 2.4.0-dev.1 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.1

**Fixed Content**: Add `_is_being_shutdown` flag in `AdapterManager`. Set it to True at the start of `shutdown()` and clear it at the end; `_update_bot_status()` skips repeated submissions during shutdown after checking the flag.

**Fixed Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Adapter

---

### [BUG-009] LazyModule synchronously accessing BaseModule leads to incomplete initialization

**Problem**: When users synchronously access properties of a lazily loaded BaseModule, the module uses `loop.create_task()` for asynchronous initialization but does not wait, leading to race conditions when properties are accessed before initialization is complete.

**Cause**: `_ensure_initialized()` uses `loop.create_task(self._initialize())` and returns immediately, without ensuring initialization is complete.

**Affected Version**: 2.4.0-dev.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fixed Content**: Change the initialization of BaseModule in synchronous contexts to use `asyncio.run(self._initialize())`, ensuring initialization is complete before returning. Maintain transparent proxy characteristics, so users do not need to perceive the difference between synchronous and asynchronous contexts.

**Fixed Date**: 2026/04/21

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-010] Multi-threaded configuration system writing leads to data loss

**Problem**: In a multi-threaded environment, when multiple threads simultaneously call `config.setConfig()`, the `_flush_config()` read-modify-write operation is not atomic, potentially causing some writes to be lost.

**Cause**: Although `_flush_config()` uses `RLock`, there is no file lock protection for file read and write, and the `_schedule_write` Timer may be triggered multiple times, causing overwrites.

**Affected Version**: 2.3.0 - 2.4.2-dev.1

**Fixed Version**: 2.4.2-dev.2

**Fixed Content**:
1. Add file locking mechanism (`_file_lock`) to ensure atomic file operations
2. Use temporary files for writing and then atomically rename (`os.replace`/`os.rename`)
3. Improve `_schedule_write` Timer cancellation and rescheduling logic

**Fixed Date**: 2026/04/21

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-011] Windows Ctrl+C cannot stop the program

**Problem**: When running `python main.py` directly on Windows, pressing Ctrl+C does not terminate the program. The program starts normally and outputs routing server information, but Ctrl+C has no response, requiring termination via the task manager. However, it can be stopped normally when started via `epsdk run`—but `epsdk run` runs via a subprocess model.

**Cause**: The Hypercorn ASGI server's `serve()` function internally registers its own SIGINT handler, overriding Python's default `KeyboardInterrupt` handling mechanism. When Hypercorn is started as a background task via `asyncio.create_task()`, its internal shutdown process cannot be triggered (because it expects the `worker_serve` mode), causing the Ctrl+C signal to be swallowed by Hypercorn without triggering any cleanup actions.

**Affected Version**: 2.3.6 - 2.4.2

**Fixed Version**: 2.4.3-dev.0

**Fixed Content**:
1. Switch ASGI server from Hypercorn to Uvicorn (`pyproject.toml` dependency change)
2. Use `uvicorn.Server._serve()` to start the server directly, **bypassing** the `capture_signals` signal handling context manager
3. Use `server.should_exit = True` for graceful shutdown, canceling the background task if timeout occurs
4. Synchronize removal of subprocess running model and `runtime/cleanup.py` cleanup module (subprocess cleanup mechanism no longer needed)

**Fixed Date**: 2026/04/28

**Severity**: 🔴 Severe

**Type**: CLI / Runtime

---

### [BUG-012] Hot restart after updating module code does not take effect

**Problem**: After executing `sdk.restart()` soft restart, the new code (such as new API routes) of modules/adapters upgraded via `epsdk install` does not take effect; old logic is still running. The latest code can only be loaded by completely restarting the process.

**Cause**: `_do_restart()` calls `entry_point.load()` during re-initialization, but this function returns cached module objects from `sys.modules` rather than reloading from disk.

**Affected Version**: Early versions - 2.4.3-dev.1

**Fixed Version**: 2.4.3-dev.1

**Fixed Content**: Clear cached module/adaptor package modules in `sys.modules` before `init()` after `uninit()`, so `entry_point.load()` loads the latest code from disk. Add `_collect_top_level_modules()` and `_invalidate_module_cache()` helper methods, deriving top-level module names via `top_level.txt` or entry-point value.

**Fixed Date**: 2026/05/03

**Severity**: 🔴 Severe

**Type**: Loading System / Runtime

---

### [BUG-013] Module loading strategy sorting logic error

**Problem**: `ModuleLoadStrategy` provides a `priority` field to declare initialization priority, but the implementation of the loading strategy has an error, causing modules not to be initialized in the expected priority order, but rather in the default order of `entry_points()`. When modules have initialization dependencies, they cannot ensure correct initialization order via `priority`.

**Cause**: The sorting logic in the implementation of the loading strategy is incorrect, and `initialize_modules()` does not sort the module list by `priority`.

**Affected Version**: 2.3.4 - 2.4.5-dev.2

**Fixed Version**: 2.4.5-dev.3

**Fixed Content**: Before traversing `initialize_modules()`, sort the module list by `priority` in descending order. Modules with the same priority maintain their original relative order (stable sorting).

**Fixed Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Loading System

---

### [BUG-014] Adapter middleware returning None causes event data loss

**Problem**: When `adapter.emit()` executes the OneBot12 middleware chain, if a middleware returns `None` (e.g., forget to `return data`), subsequent middleware and all event handlers receive `processed_data` as `None`, causing event processing to fail completely.

**Cause**: The middleware chain implementation `processed_data = await middleware(processed_data)` does not check if the return value is `None`, directly overwriting the previous processing result.

**Affected Version**: unknown - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fixed Content**: Ignore the return value if middleware returns `None`, retain the original data, and output a warning-level log.

**Fixed Date**: 2026/05/15

**Severity**: 🔴 Severe

**Type**: Adapter / Event System

---

### [BUG-015] Configuration file path depends on working directory

**Problem**: The configuration file path of `ConfigManager` is `config/config.toml` by default, which depends on `os.getcwd()` in runtime. If the working directory changes during runtime (e.g., via `os.chdir()`), configuration file read/write operations will point to the wrong location, leading to configuration loss or reading old data.

**Cause**: In `__init__`, the relative path is directly stored without being resolved to an absolute path during initialization.

**Affected Version**: 2.3.7 - 2.4.5-dev.3

**Fixed Version**: 2.4.5-dev.4

**Fixed Content**: In `ConfigManager.__init__()`, if the passed path is a relative path, automatically resolve it to an absolute path using `os.path.abspath()`.

**Fixed Date**: 2026/05/15

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-016] BaseStorage confuses storing None value with non-existent key

**Problem**: `BaseStorage.get_multi()` / `__getattr__()` cannot distinguish between "key does not exist" and "key's value is None", causing users to be treated as if the key does not exist when they explicitly store `None` and then read it.

**Cause**: The value retrieval logic directly uses `value is None` to determine if the key exists, lacking an independent "missing" marker.

**Affected Version**: Early versions - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fixed Content**: Introduce `_SENTINEL` sentinel value to distinguish between "key does not exist" and "value is None", no longer confusing the two.

**Fixed Date**: 2026/06/07

**Severity**: 🟡 Medium

**Type**: Storage

---

### [BUG-017] WebSocket route auto_accept flag lost after service restart

**Problem**: After a service restart (such as `sdk.restart()`), the `auto_accept` configuration of all WebSocket routes becomes `False`, and the originally expected auto-accept connections remain pending, causing the client to wait for a long time without receiving a response, manifesting as a WS connection hang.

**Cause**: `_restore_routes_from_records()` hardcodes `auto_accept` as `False` when restoring routes from persistent records, not reading the real value from the record; also, when the route storage tuple expands from a binary tuple to a ternary tuple, the restoration logic is not synchronized.

**Affected Version**: 2.3.8-dev.0 - 2.4.6-dev.6

**Fixed Version**: 2.4.6-dev.6

**Fixed Content**: Route storage tuple expands to `(handler, auth_handler, auto_accept)`, and `_restore_routes_from_records()` reads the real `auto_accept` value from the record instead of hardcoding `False`.

**Fixed Date**: 2026/06/07

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-018] Concurrent calls of HTTP/WS client lead to crashes and connection leaks

**Problem**: The HTTP and WebSocket clients in `Core/client.py` have multiple stability defects in concurrent scenarios, leading to connection leaks or process crashes:
- Concurrent calls of `ClientWebSocket.receive()` may cause aiohttp to throw `Concurrent call to receive() is not allowed`
- `_get_http_session()` / `_get_ws_session()` concurrent calls may create multiple sessions, and `_drain_sessions()` does not close old connections, causing connection leaks
- `request()`'s exception handling order is wrong: `except ClientConnectionError` (ErisPulse exception) is never triggered, aiohttp connection errors are caught by the general `except Exception`, leading to the "retry + session rebuild" logic (dead code) never executed
- `send_json()` ignores the `mode="binary"` parameter; `_get_ws_session()` does not pass default request headers

**Cause**: The client was initially implemented (2.4.6-dev.5) without concurrent protection and improper handling of aiohttp exception hierarchy and ErisPulse custom exception inheritance.

**Affected Version**: 2.4.6-dev.5 - 2.4.8

**Fixed Version**: 2.4.8

**Fixed Content**:
1. Add `_recv_lock` to serialize all `receive()` / `receive_text()` / `receive_bytes()` calls
2. Add `_session_lock` to protect session creation; `_drain_sessions()` is changed to an asynchronous method and truly closes old sessions
3. Refactor `request()` exception handling order: `asyncio.TimeoutError` → `aiohttp.ClientConnectionError` (triggers session rebuild) → `aiohttp.ClientError` → `ClientError` (transparent pass) → `Exception`
4. Fix `send_json()` mode handling, `_get_ws_session()` default request headers, `close()` concurrent race, `HttpResponse.__aexit__` repeated `release()`

**Fixed Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Client

---

### [BUG-019] Adapter hot reload causes route conflicts and reload failure

**Problem**: When third-party modules (such as Dashboard) trigger adapter hot reload, or adapter startup fails and retries, old routes (such as `onebot11_default`) are not cleaned up, causing `WebSocket path ... already registered` conflicts, leading to reload failure. A complete restart is required to restore.

**Cause**: `AdapterManager.shutdown()` only cleans up routes via `unregister_all_by_namespace(platform)`, but adapters (such as OneBot11) register WebSocket routes with `onebot11_{account_name}` as the namespace, resulting in a granularity mismatch and cleaning being an empty operation; startup failure retry routes are also not cleaned up from previous residual routes.

**Affected Version**: Early versions - 2.4.9

**Fixed Version**: 2.4.9

**Fixed Content**:
1. Route registration automatically tracks `owner → namespace` relationships via `current_owner` ContextVar
2. Add `unregister_all_by_owner(owner)`, cleaning up by owner during stop/restart, covering fine-grained namespaces
3. Add `_stop_adapter(platform)` primitive ("stop equals clean"), binding stopping adapter and reclaiming its registered resources in one call, used by `restart()` and startup failure retry
4. Add framework-level `adapter.restart(platform)` API, third-party modules should call this method instead of directly operating adapter instances

**Fixed Date**: 2026/06/12

**Severity**: 🔴 Severe

**Type**: Adapter / Router

---

### [BUG-020] Subprocess mode `ep run <script>` cannot find sub-packages in script's directory

**Problem**: When running a script with `ep r .\main.py` in non-hot-reload mode, if the script has relative imports (e.g., `from qg import ...`), it reports `No module named 'qg'` error. However, `--reload` mode works normally.

**Cause**: Non-hot-reload mode directly calls `runpy.run_path()` to execute the script, which does not automatically add the script's directory to `sys.path`. In contrast, `--reload` mode runs via `subprocess.Popen` subprocess, which automatically inherits the current working directory, and `sys.path[0]` is the script's directory, so it works.

**Affected Version**: 2.5.0 - 2.5.2-dev.0

**Fixed Version**: 2.5.2-dev.0

**Fixed Content**: Before calling `runpy.run_path()`, manually insert the script's directory into `sys.path[0]`.

**Fixed Date**: 2026/06/27

**Severity**: 🟡 Medium

**Type**: CLI

---

### [BUG-021] SQL query builder rejects valid wildcard and list expressions

**Problem**: The `_build_select_sql()` method of `SQLiteQueryBuilder` calls `_validate_identifier()` for all SELECT columns, which uses a strict whitelist regular expression `^[a-zA-Z_][a-zA-Z0-9_]*$`, causing legitimate SQL syntax to be mistakenly judged as unsafe column names:
- `SELECT *` — `*` is a standard SQL wildcard
- `SELECT COUNT(*)` — aggregate function
- `SELECT users.name` — qualified column name
- `SELECT col AS alias` — column alias

Among them, `Select("*")` is used by Cron and other modules, causing module `on_load` execution to fail and the module cannot load.

**Cause**: In version 2.4.6, SQL injection protection was enhanced, and `_validate_identifier()` whitelist validation was introduced. This validation applies to all column names, but does not distinguish between read end (SELECT/ORDER BY) and write end (INSERT/UPDATE). SELECT columns allow complex SQL expressions and should not be restricted by simple identifier whitelist.

**Affected Version**: 2.4.6 - 2.5.2-dev.1

**Fixed Version**: 2.5.2-dev.2

**Fixed Content**: Change SELECT/ORDER BY column validation from whitelist mode to blacklist mode:
1. Add `_validate_select_column()` function, only intercepting SQL injection dangerous characters (`;` `'` `"` `--` `/*` `*/` `\x00` newline)
2. Allow any valid SQL column expressions (`*`, `table.*`, `table.column`, `COUNT(*)`, `col AS alias`, etc.)
3. INSERT/UPDATE column names still maintain strict whitelist validation (only allow simple identifiers)

**Fixed Date**: 2026/06/29

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-022] _resolve_account() account resolution regression (_accounts_data not filled)

**Problem**: After the configuration system was refactored in 2.5.2, multi-account adapters that declared `AccountConfigClass` reported `ValueError("AccountConfigClass not declared, cannot resolve account")` when calling methods that require sending messages, such as `wait_reply` and `reply`, even if the adapter correctly configured multi-account information. Account resolution still failed.

**Cause**: In 2.5.2-dev.5, `_load_accounts()` (responsible for reading configuration + validation + filling `_accounts_data`) was refactored into `_ensure_accounts_exist()` (only generates configuration template), but `_resolve_account()` still checks `self._accounts_data is None`. Since `_ensure_accounts_exist()` no longer fills `_accounts_data`, this attribute remains `None`, causing `_resolve_account()` to return `(None, None)` early, and downstream calls to `_resolve_account` (such as `call_api`) receive `None`, triggering an error.

**Root Cause Chain**:
```
_load_accounts() was deleted
  → __init__ no longer fills _accounts_data
    → _accounts_data is always None
      → _resolve_account() checks _accounts_data is None → return (None, None)
        → downstream calls to _resolve_account (e.g. call_api) get None
          → triggers error
```

**Affected Version**: 2.5.2-dev.5 - 2.5.2

**Fixed Version**: 2.5.3

**Fixed Content**: In `BaseAdapter.__init__`, after `self._ensure_accounts_exist()`, restore the filling of `_accounts_data`:
```python
if self.AccountConfigClass is not None:
    self._ensure_accounts_exist()
    self._accounts_data = self.accounts  # restore filling, data source is real-time read accounts attribute
```
The logic of `_resolve_account()` remains unchanged, fully backward compatible:
- Adapters that do not declare `AccountConfigClass`: `_accounts_data` remains `None` → returns `(None, None)`
- Adapters that declare `AccountConfigClass`: `_accounts_data` is filled → normal resolution
- Adapters that override `_load_accounts` or manually set `_accounts_data`: overwrite after `super().__init__()`, highest priority

**Fixed Date**: 2026/07/07

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-023] After modifying account configuration, adapter cache is not refreshed, causing account resolution failure

**Problem**: After users modify the multi-account adapter's account configuration (such as filling in the token) through the Dashboard, the adapter still uses the old cache, and calling methods related to sending messages reports `未找到可用账户 (account_id=default)` error. The process must be restarted to make the new configuration effective.

**Cause**: `_accounts_data` is only read from the configuration storage once at `BaseAdapter.__init__`, and is never refreshed afterwards. `AdapterManager._run_adapter()` and `restart()` do not re-read the account configuration before calling `adapter.start()`, causing the cache and actual configuration to be out of sync.

**Affected Version**: 2.4.6 - 2.5.4

**Fixed Version**: 2.5.4

**Fixed Content**: In `AdapterManager._run_adapter()` and `restart()`, before calling `adapter.start()`, refresh `adapter._accounts_data = adapter.accounts` to ensure that the latest configuration is used each time the adapter starts.

**Fixed Date**: 2026/07/09

**Severity**: 🔴 Severe

**Type**: Adapter / Configuration System

---

### [BUG-024] storage.set() writing large numeric key triggers OOM Kill

**Problem**: When calling `storage.set()` to write a nested key path containing a large numeric field (such as QQ group number `871684833`), the process is killed by the container OOM (exit code -9), and the service crashes and cannot recover.

**Cause**: In the recursive implementation of `_set_nested_value`, the pure numeric field in the nested key path is mistakenly judged as a list index by `isdigit()`, triggering `current.extend([None] * (index - len(current) + 1))`, attempting to allocate hundreds of millions of elements, instantly exhausting memory.

**Root Cause Chain**:
```
The key path contains a pure numeric field (such as group number 871684833)
  → isdigit() mistakenly judged as an array index
    → extend([None] * (871684833 - len(current) + 1))
      → Attempt to allocate hundreds of millions of elements
        → Memory exhausted → Container OOM Kill (exit code -9)
```

**Affected Version**: 2.5.1 - 2.5.5

**Fixed Version**: 2.5.5

**Fixed Content**:
1. Always use a dictionary when pre-creating intermediate layers, no longer guessing the container type based on whether the next segment is a number.
2. Only when the container itself is a list and the index is less than `STORAGE_MAX_LIST_INDEX` (10000) do we process the index, skipping large indexes safely.
3. Change the recursive implementation to an iterative one, eliminating potential infinite recursion in the original code.
4. Add the `STORAGE_MAX_LIST_INDEX` constant to `Core/constants.py`, centrally managing the safe upper limit for indexes.

**Fixed Date**: 2026/07/10

**Reproduction Steps**:
```python
# Trigger by writing a nested key path containing a large number field (such as QQ group number)
await sdk.storage.aset("groups.871684833.name", "某群")
# → Process memory instantly surges, killed by OOM
```

**Regression Test**: `tests/unit/test_unit_storage.py` adds 4 regression test cases
- `test_nested_key_numeric_segment_as_dict_key` — precisely reproduces the OOM scenario
- `test_nested_key_numeric_segment_multiple` — multiple consecutive numeric fields as dictionary keys
- `test_nested_key_existing_list_index_set_within_limit` — reasonable index write to existing list
- `test_nested_key_list_index_safety_limit` — safety limit for large indexes

**Severity**: 🔴 Severe

**Type**: Storage

---

### [BUG-025] on_config_update callback not called by core router

**Problem**: The `on_config_update(old, new)` callback is defined in the base class (BaseModule / BaseAdapter), but the core framework does not subscribe it to configuration change events. As a result, when modifying the configuration through the configuration management panel, it can be triggered, but when manually editing `config.toml` or calling `setConfig()`, the `on_config_update` callback is not triggered.

**Cause**: `ConfigManager` emits `config.set` / `config.updated` lifecycle events when the configuration changes, but lacks the subscription logic to forward these events to each component's `on_config_update` method.

**Root Cause Chain**:
```
Core does not subscribe to config.set / config.updated
  → Configuration change events are not forwarded
    → on_config_update is not called
      → Manual editing file / code setConfig does not trigger hot update callback
```

**Affected Version**: All versions

**Fixed Version**: 2.6.2

**Fixed Content**: `ModuleManager` / `AdapterManager` register subscriptions for `config.set` (covering code `setConfig()` path) and `config.updated` (covering manual file editing path), match by configuration key prefix and call the corresponding component's `on_config_update`, passing type-safe configuration objects. Also fix `_flush_config()` not synchronizing `_config_mtime` after writing the file, avoiding the framework's own writing being mistakenly judged as external modification and repeatedly triggering `config.updated`.

**Compatibility Note**: Configuration hot updates are now maintained by the framework core. Previously, the configuration management panel triggered it on behalf of the framework, which has been removed. After upgrading the framework, the configuration management panel must also be upgraded, otherwise double triggering will occur (core + panel each call once). The signature and semantics of `on_config_update` remain unchanged, subclasses do not need to modify.

**Fixed Date**: 2026/07/23

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-026] notice/request event reply target inference error

**Problem**: In group notification events (such as member joining a group `group_member_increase`), calling `event.reply()` sends the message to the user's private chat who triggered the event, not to the group where the event occurred. Similarly, in friend notification events, the reply target may be incorrect.

**Cause**: `infer_receive_type()` directly returns the `detail_type` as the session type. For message events, this is correct (the `detail_type` values `private`/`group` are session types), but for notice/request events, the `detail_type` is a semantic subtype (such as `group_member_increase`, `friend_increase`), not a session type. Subsequent `convert_to_send_type()` and `get_id_field()` find no value in the mapping table, defaulting back to `"user"` / `"user_id"`, causing the reply target to be incorrect.

**Root Cause Chain**:
```
notice event detail_type="group_member_increase"
  → infer_receive_type() directly returns "group_member_increase"
    → convert_to_send_type("group_member_increase") not in mapping table → default "user"
    → get_id_field("group_member_increase") not in mapping table → default "user_id"
      → target_id = event["user_id"]  ← new member's private chat (not group)
```

**Affected Version**: All versions

**Fixed Version**: 2.7.0-dev.3

**Fixed Content**: `infer_receive_type()` adds a check—only returns `detail_type` directly if it is a known session type (standard or custom type); otherwise, infers the correct session type based on the ID field (`group_id` / `channel_id` / `user_id` etc.).

**Regression Test**: `tests/unit/test_unit_session_type.py` → `TestNoticeRequestTypeInference` (10 test cases)

**Fixed Date**: 2026/07/29

**Severity**: 🟢 Minor

**Type**: Event System

---

### [BUG-027] Route rate limiting cleanup task uses fixed window causing long window rate limiting rules to fail

**Problem**: When setting route rate limiting to a long window rule (such as `100/hour`, `{"requests": 100, "window": 3600}`), the rate limiting is ineffective—practically behaving like `100/minute` (approximately 6000 requests per hour), completely failing to provide the expected hourly protection.

**Cause**: `_apply_rate_limit` parses the actual `window` (up to 3600 seconds) for each route, and per-request checks use this window; however, the background cleanup task `_cleanup_expired_rate_limits` uses a fixed constant `DEFAULT_RATE_LIMIT_WINDOW_SECS` (60 seconds) as the cleanup threshold for all routes. Thus, `100/hour` routes have timestamps earlier than 60 seconds cleared by the cleanup task, so the hour window never accumulates close to 100 records, severely weakening the rate limiting.

**Root Cause Chain**:
```
_apply_rate_limit parses window=3600 (100/hour)
  → per-request checks use 3600s retention time (correct)
  → but _cleanup_expired_rate_limits uses fixed max_window=60s to clean up
    → timestamps earlier than 60 seconds are cleared
      → the hour window only retains records from the last 1 minute
        → 100/hour effectively degrades to ~100/minute (relaxed by about 60 times)
```

**Affected Version**: 2.6.0-dev.0 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fixed Content**: Add `_rate_limit_windows: dict[str, int]` to record the actual window for each route; `_apply_rate_limit` writes the window when creating entries for the first time; `_cleanup_expired_rate_limits` cleans up according to each key's own window (fallback to default if missing); clean up and maintain both dictionaries synchronously with `stop()`.

**Fixed Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_router.py` → `TestRateLimit::test_cleanup_respects_per_route_window`

**Severity**: 🔴 Severe

**Type**: Router

---

### [BUG-029] Configuration listener task broadcasts incomplete TOML and silently swallows exceptions

**Problem**: When the user manually edits `config.toml` and saves halfway (producing a temporary syntax error), the configuration monitoring background thread detects the mtime change, reloads the configuration, but fails to load and still broadcasts an empty configuration `{}` as `config.updated`, causing adapters/modules' `on_config_update` to receive an empty configuration, mistakenly assuming all configuration items have been cleared and reverting to default values. Additionally, the listener loop silently swallows all exceptions with `except Exception: pass`, making it impossible to troubleshoot watcher failures.

**Cause**: Two defects overlap:
1. `_load_config` writes `self._cache` as `{}` when TOML syntax errors/permission errors occur, but the background listener thread `_watch_loop` and cache timeout path `_check_cache_validity` broadcast `_emit_config_updated(new_config={})` unconditionally after calling `_load_config()`, treating the "empty cache from failed load" as a real change.
2. `_watch_loop` uses `except Exception: pass` without logging any exceptions.

**Root Cause Chain**:
```
User saves halfway → TOML syntax error
  → _load_config() erases _cache = {}
    → _watch_loop unconditionally _emit_config_updated(new_config={})
      → Adapters/modules on_config_update receive empty config
        → Mistakes configuration as cleared, reverts to default values
```

**Affected Version**: 2.6.2-dev.1 - 2.7.0-dev.4

**Fixed Version**: 2.7.0-dev.5

**Fixed Content**:
1. `_load_config` returns a `bool`; on TOML syntax error/permission error/other errors, it **retains the last valid cache** (instead of erasing to `{}`), only records diagnostic logs, and returns `False`
2. `_watch_loop` and `_check_cache_validity` only emit `config.updated` if `_load_config()` returns `True`
3. `_watch_loop`'s `except Exception` is changed to log at warning level (new i18n key `core.config.watcher_error`, five languages synchronized)

**Fixed Date**: 2026/07/31

**Regression Test**: `tests/unit/test_unit_config.py` → `test_malformed_toml_preserves_last_valid_cache`, `test_permission_denied_logs_clear_message` (updated to verify cache retention + return False)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-030] Configuration watcher race condition causes setConfig delayed write silently loses data

**Problem**: Multiple users report that after using `config.setConfig(key, value)` (default `immediate=False`), their module configuration is not written to `config.toml`, while other module configurations are normal. Setting `immediate=True` (force flush) can avoid this. This manifests as configuration written during runtime is lost after the next restart, while configuration generated during startup remains.

**Cause**: Two overlapping defects:
1. **Logical defect**: `_watch_loop` unconditionally `_dirty_keys.clear()` when `_check_file_change()` returns `True`, but `_check_file_change()` only uses `!=` to compare mtime. The framework's own `_flush_config` writing also changes mtime—although `_flush_config` updates `_config_mtime` after writing, the watcher thread may still observe mtime differences (and gaps in coarse-grained file systems) between file writing and mtime assignment, mistakenly judging it as "external modification" and clearing all pending keys.
2. **Thread defect**: `_watch_loop` operates `_write_timer`/`_dirty_keys` without holding `_lock`, causing data races with `setConfig` (holds lock to write `_dirty_keys`), `_schedule_write` (holds lock to write `_write_timer`).

**Root Cause Chain**:
```
Module A setConfig(immediate=True) → flush writes, mtime changes
  → User module setConfig(immediate=False) → enters _dirty_keys, flushes in 5s
    → Watcher polling, _check_file_change observes mtime difference from its own previous write
      → _dirty_keys.clear() → User module's pending keys are silently discarded
        → Configuration missing after restart
```

**Affected Version**: 2.6.0 - 2.7.0

**Fixed Version**: 2.7.1

**Fixed Content**:
1. Add `_last_self_write_mtime` field; `_flush_config` records it after writing; `_check_file_change` compares it first when mtime changes, matching it to judge as "self-write" and return `False`
2. `_watch_loop` holds `_lock` throughout; retains `_dirty_keys` for actual external modification (merge semantics), next flush merges with external content (dirty keys take precedence), no `clear()`
3. `getConfig`/`_check_cache_validity` paths are unaffected (their reload does not clear dirty keys)

**Fixed Date**: 2026/08/06

**Regression Test**: `tests/unit/test_unit_config.py` → `test_self_write_not_detected_as_external`, `test_external_change_preserves_dirty_keys`, `test_flush_merges_dirty_with_external`

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-032] "Write after read" reads old value without delay

**Problem**: After `config.setConfig()` (default `immediate=False` delayed for about 5 seconds) writes a dot-separated key, immediately reading its **parent/ancestor node** (e.g., `set_erispulse_section("scope.actions.MyModule", {...})` followed by `get_erispulse_config()`) returns the old value, the written sub-key "disappears", only visible after the flush. Scenarios like scope configuration hot updates ("write-read-write") are affected (exposed by test plugin `/t_section` use case in 2.8.0).

**Cause**: `setConfig` stores dot-separated keys as **flat** in the dirty queue `_dirty_keys`, only `getConfig`'s **exact key query** hits the dirty queue; tree-path queries (e.g., `getConfig("ErisPulse.scope")`) only go through the cache tree, not overlaying dirty values—creating a read-you-just-write disconnect during the delay flush (`_flush_config` merges dirty keys into cache and clears the queue) period.

**Affected Version**: 2.6.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.1

**Fixed Content**: `getConfig` introduces dirty overlay semantics—① exact match in dirty key returns directly (unchanged original behavior); ② if dirty key is an ancestor of the query, take the longest matching ancestor and parse the remaining path in its sub-tree; ③ if dirty key is a descendant of the query, build an overlay sub-tree (`_dirty_overlay`) and deep merge with the cache sub-tree (`_deep_merge`, override priority, no modification of original cache object). No dirty keys go through the original fast path, zero additional overhead.

**Fixed Date**: 2026/09/04

**Regression Test**: `tests/unit/test_unit_config.py` → `test_get_config_overlays_dirty_descendant`, `test_get_config_overlay_merges_with_cache_siblings`, `test_get_config_overlay_new_branch`, `test_get_config_dirty_ancestor_query`, `test_get_config_dirty_exact_key_still_wins`

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-033] wait_reply hangup replies are starved by high-priority processors

**Problem**: When a module calls `wait_reply()` to wait for a user reply, if that reply message is claimed by a higher-priority event handler (`mark_processed()`), the command dispatcher sees the `_processed` flag at the entry and returns directly, never executing the reply matching logic at the end of the dispatcher—waiting parties receive no reply, only timeout and return `None`. Typical trigger scenario: robots using high-priority message handlers (recording/auditing/blocking classes) have random failures in all dialog interactions.

**Cause**: Reply matching `_check_pending_reply` hangs at the end of `_handle_message` (only executed if command matching fails), while `_processed` checking is before it—the order of claim checking and reply matching is reversed. Interactive waiting is a framework-level session continuation mechanism, not a competitive processor, and should not be affected by other processors' claim.

**Affected Version**: 2.2.0-dev.0 - 2.8.0-dev.1

**Fixed Version**: 2.8.0-dev.2

**Fixed Content**: Reply matching is moved to the entry of `_handle_message` (before `_processed` checking, only for message events): first try to complete the pending conversation, if matched, the event is marked as processed, and the rest of the check naturally short-circuits; if not matched, continue the original command matching process. The matching chain is delegated to a new interaction session manager (`Core/Event/interaction.py`), which also gains the ability to cancel and review permissions by affiliation.

**Fixed Date**: 2026/09/08

**Regression Test**: `tests/unit/test_unit_interaction.py` (TestRegisterResolve matched/unmatched/claim mark), `tests/unit/test_unit_event.py` (full chain of wait_reply)

**Severity**: 🟡 Medium

**Type**: Event System / Command System

---

### [BUG-034] Runtime binding with persist=False is silently overwritten by any subsequent configuration write

**Problem**: `scope.set_module(..., persist=False)` writes only to memory `self._data`; but scope subscribes to `config.set` / `config.updated` events, and any code writing configuration (e.g., a module loading its own default configuration) triggers scope to rebuild the configuration tree from the configuration file, causing all previous runtime bindings to be silently lost (reverting to default allow), with no log warning. Scenarios depending on runtime binding (Dashboard "runtime only" switches, module runtime dynamic disable) revert after unrelated module writing configuration.

**Cause**: Root cause chain: `scope.set/delete(persist=False)` only writes to memory (`Core/scope.py`) → any `setConfig` triggers `config.set` event → `_on_config_updated` unconditionally `_load_config()` → `_apply_tree()` replaces `self._data = {...}` as a whole → runtime bindings not in the configuration file are discarded.

**Affected Version**: 2.8.0-dev.2 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fixed Content**: Introduce a runtime overlay layer `_runtime_overrides` (with deletion sentinel): `persist=False` writes/Deletes are recorded in the overlay layer, `_apply_tree()` rebuilds the persistent layer from the configuration file and then reapplies the overlay in order of write; `persist=True` writes/Deletes clear the corresponding overlay records (user persistence semantics take precedence); `config.set` only filters by event key, `config.updated` compares new and old scope, rebuilding only if scope actually changes (avoiding unnecessary overwriting of unrelated writes); add `unregister_by_owner()` for module unloading to clean up with the caller.
**Fixed Date**: 2026/09/09

**Reproduction Steps**: ① `scope.set_module("testplat", blocked=["TestB"], persist=False)` → returns False; ② any module executes `config.setConfig("HelpModule", {...})` → triggers scope rebuild; ③ `scope.is_allowed("testplat", None, "TestB")` returns True (expected still False).
**关联**: Issue #432
**Regression Test**: `tests/unit/test_unit_scope.py::TestRuntimeOverrideSurvival` (irrelevant write survives/rebuild reapplies/deletion sentinel/persistence clears/unprecise invalidation/owner cleanup)

**Severity**: 🟡 Medium
**Type**: Configuration System / Runtime

---

### [BUG-035] Configuration panel select options and dict fields render as [object Object]

**Problem**: In the WebUI configuration panel, select field options display as `[object Object]` (e.g., dynamically generated color style options); undeclared control type dict fields (e.g., `stalker_mode`, `knowledge_base` and other nested configuration segments) display as `[object Object]` in text boxes, making them impossible to view and edit.

**Cause**: Two separate defects: ① The framework i18n parser `_resolve_i18n_text` only restores dictionaries with an `i18n` key, so options with only a `default` key (dynamic text without `i18n` key) are passed through as-is, and the frontend `esc(label)` string cast gets `[object Object]`; ② The Dashboard rendering branch only does JSON textarea for array types, dict values fall into the plain text input branch and are cast by `String()`. Additionally, if a module declares `_schema_meta` as a regular dataclass field (missing `ClassVar` annotation), it is treated as a configuration field and enters the schema, exacerbating the confusion.

**Affected Version**: 2.7.0 - 2.8.0-dev.2
**Fixed Version**: 2.8.0-dev.2
**Fixed Content**: ① `_resolve_i18n_text` supports dictionaries with only a `default` key, restoring them to text; ② The framework's schema/template/default value/population/validation always excludes fields with underscores at the beginning (misdeclaration harmless); ③ Dashboard select option label objects fall back to parsing (prioritizing `default`), dict/table fields render as JSON textarea (saving path as `tp=object` JSON.parse back, complete round trip).
**Fixed Date**: 2026/09/09

**Regression Test**: `tests/unit/test_unit_config.py::TestResolveI18nDefaultOnlyDict`, `TestSchemaUnderscoreFieldExclusion`

**Severity**: 🟡 Medium
**Type**: Configuration System

---

### [BUG-036] Configuration write fails intermittently (ENOENT) when multiple instances share a configuration directory

**Problem**: In Docker deployment scenarios (multiple containers mounting the same host configuration directory), log messages intermittently show two consecutive `Failed to write configuration file ... [Errno 2] No such file or directory: '...config.toml.tmp' -> '...config.toml'`. This configuration write is discarded (the old configuration is fully retained, no configuration loss is observed), functionality is unaffected, but repeated warnings interfere with troubleshooting, and pending configuration items must wait for the next write to be written to disk.

**Cause**: Root cause chain: `_flush_config` / `setConfigTemplate` uses a **fixed-name** temporary file `config.toml.tmp` to carry new content, `write()` does not `fsync` before directly `rename()`ing. Two ErisPulse instances sharing the same configuration directory may have B instance `open("w")` truncate A instance's currently writing temporary file → A rename fails as the target has been taken or content truncated by B, reporting ENOENT (i.e., the user's log shows two consecutive error messages). In reported cases, only the write failure warning is observed (old configuration retained); if the timing overlap is more extreme, rename may output an empty/semi-truncated `config.toml` (potential risk, not yet exploded in real environments). In single-instance scenarios, ext4's delayed allocation also has a "rename metadata before data block is written" crash window (SIGKILL / power failure). `_file_lock` is a process-level `threading.RLock`, which does not constrain cross-process/cross-container writes.

**Affected Version**: 2.2.0-dev.0 - 2.8.0

**Fixed Version**: 2.8.1

**Fixed Content**: Configuration writing is unified to `_atomic_write_text()`: generate a process-unique temporary file (eliminating fixed-name contention, multiple instances degrade to last-writer-wins, no ENOENT); write and `flush + fsync` to force data to disk (eliminating the "rename effective, data not written" window); `os.replace` atomically replaces the target (POSIX/Windows are atomic, either the disk has the complete old content or the complete new content); additional fsync of the configuration directory on POSIX. All three write points (`_flush_config`, `setConfigTemplate`, root directory configuration migration) switch; exception path cleanup logic is refactored with the unique temporary file name. Add **multi-instance detection**: acquire a lock (POSIX `flock` / Windows `msvcrt.locking`) on the configuration directory lock file `.erispulse_config.lock` at startup, output an i18n warning if occupied (does not block startup), and the lock is automatically released by the OS when the process exits, with no ghost locks.

**Fixed Date**: 2026/09/13

**Reproduction Steps**: ① Two containers mount the same host `config/` directory and run ErisPulse simultaneously; ② Trigger configuration write (e.g., module registration default configuration) in any instance; ③ Observe log messages with ENOENT write failure warnings, this write is discarded (old configuration retained).

**关联**: User report (1Panel container ×2)

**Regression Test**: `tests/unit/test_unit_config_atomic_write.py` (content fully written/no temporary file residue/write failure preserves old file/multi-instance concurrent write always valid/lock file creation/multi-instance warning/migration atomic write)

**Severity**: 🟢 Minor

**Type**: Configuration System

---

### [BUG-037] Space-separated command names registered as subcommands never trigger

**Problem**: After registering a subcommand with a space-separated command name (e.g., `@command("admin add")`), the command can be registered normally and appears in the help list, but when the user sends `/admin add`, the robot never responds—the input is matched as the parent token command `admin` with parameters `["add"]`; if the parent token is also unregistered, there is no response. Only when using dot-separated naming (e.g., `admin.reload`, treated as a single token) can this be avoided.

**Cause**: Root cause chain: `CommandHandler.__call__` stores any command name (including space-separated) as a key in the flat `self.commands` dictionary → in the distribution phase `_try_execute_command`, only the first token of the message is matched (`cmd_name = parts[0]`) → multi-token command names as dictionary keys are never found. The registration and matching phases have inconsistent assumptions about the command name space, and there is no registration warning (silent failure).

**Affected Version**: From the introduction of the command system onwards - 2.8.0

**Fixed Version**: 2.8.1

**Fixed Content**: The matching layer changes to **longest prefix matching**: from the longest candidate (`" ".join(parts[:n])`, with `n` capped by the maximum number of token segments in registered command names/aliases, cached in `_max_name_tokens`) down to the shortest, matching triggers execution with the remaining tokens as parameters, downstream scope/ACL/overwrite/master/permission chains naturally apply to the full command name. Accompanying semantics: when parent and child commands coexist, unregistered child commands fall back to the parent command (historical behavior unchanged); if a child command does not declare `permission`, it inherits the most recently declared ancestor command's permission (protecting the parent command protects all its child commands); only registering single-token commands matches in the first round, distribution overhead is consistent with the original. `unregister` / `unregister_by_owner` / full cleanup synchronously maintains the token count cache.

**Fixed Date**: 2026/09/13

**Reproduction Steps**: ① Register a subcommand with a space-separated command name in a module, e.g., `@command("admin add")`; ② Send `/admin add x`; ③ Before the fix, there is no response (or it is caught by the `/admin` command as a parameter), after the fix, `admin add` triggers and `get_command_args()` returns `["x"]`.

**Regression Test**: `tests/unit/test_unit_command_subcommand.py` (longest prefix matching/only subcommand triggers/tertiary nesting/case-insensitive two modes/single and multi-token alias/event payload full name/lifecycle hook full name/permission inheritance six examples/ACL glob full name/master/unregister fallback and cache recalculation)

**Severity**: 🟡 Medium

**Type**: Event System

---

### [BUG-038] Runtime bindings with persist=False are written to disk along with persistent writes, "reviving" from disk after module unloading

**Problem**: Runtime bindings written with `scope.set(path, value, persist=False)` (documented promise not to write to disk, lost after process restart, cleared after module unloading) are written to disk along with any unrelated `persist=True` write (default, e.g., module `set_module` / WebUI save configuration), and after the module is unloaded and the binding is cleared, the binding is "revived" from disk after the next configuration reload, continuing to work and remaining after process restart—contrary to the "runtime binding not to disk" semantic contract, and extremely difficult to trace.

**Cause**: Root cause chain: `ScopeManager.set()` first writes the value to the memory configuration tree `_data` (runtime bindings are also directly written to `_data`), and the persistent branch applies a deep copy snapshot of the entire `_data` tree to `update_erispulse_config` for differential writing to disk → the snapshot mixes in the `persist=False` binding values. `delete(persist=True)` is the same source: the live reference (parent node) is handed over to the delayed write dirty queue, and during the dirty write window, the live reference exists in the dirty queue, causing cross-write contamination windows.

**Affected Version**: 2.8.0-dev.2 - 2.9.0-dev.0

**Fixed Version**: 2.9.0-dev.2

**Fixed Content**: Introduce a persistent baseline `_persisted_tree` (the configuration tree is refreshed from the disk-loaded, validated tree as the mirror of disk truth): `set(persist=True)` only applies the current change to the baseline and submits the differential to the persistent layer; "read after write" uses the memory final state snapshot to directly restore, no longer going through `_apply_tree` to pollute the baseline. `delete(persist=True)` is the same口径: the deep copy of the baseline subtree is handed over to the persistent layer; `set_action` replaces semantics first delete then write, old rule keys do not remain in the persistent content.

**Fixed Date**: 2026/09/27

**Reproduction Steps**: ① The module executes `scope.set("bots.p.debug_mode", {"blocked": ["X"]}, persist=False)`; ② Trigger any persistent write (e.g., another module calls `set_module`); ③ Open `config/config.toml`, see `debug_mode` has been written (before the fix); ④ Unload the module (runtime binding is cleared) and trigger configuration reload, `scope.get("bots.p.debug_mode")` still returns the binding value.

**Regression Test**: `tests/unit/test_unit_scope.py::TestPersistBaseline` (runtime bindings do not write to disk with unrelated persistent writes / unloading does not revive after configuration reload / delete submits baseline subtree without runtime sibling keys / set_action replacement leaves no residual key / cache_size configuration takes effect)

**Severity**: 🔴 Severe

**Type**: Configuration System

---

### [BUG-039] Inconsistent read/write when section write and dotted write coexist (dotted overwrite lost)

**Problem**: During the delay flush window, when both section write (`setConfig("Mod", {...})`, such as `BaseModule.cfg` writing back) and dotted write (`setConfig("Mod.key", v)`, such as configuration hot update / test tool overwrite) coexist, there are two variants: Variant A (read path) — `getConfig("Mod")` returns the old section read snapshot, not seeing the later dotted overwrite (dotted read path is normal); Variant B (write path, heavier) — if dotted write is before section write (test tool injects overwrite → module `self.cfg = ...` writes back, a common timing), flush applies dirty keys in insertion order, section write replaces the entire section, **dotted overwrite is permanently lost on disk**. Production environment "configuration hot update + module runtime write back" combination can trigger this, unrelated to test environment (ErisPulse-DailyCard test feedback exposed).

**Cause**: `getConfig` first (exact match in `_dirty_keys`) returns directly `return self._dirty_keys[key]`, completely bypassing the fourth segment `_dirty_overlay` descendant overlay; `_flush_config` applies dirty keys in insertion order, section write happens after dotted write, replacing the dotted values. Also: `getConfig` returning (exact match / ancestor subtree / overlay merge) is changed to `copy.deepcopy` isolation copy, no longer leaking dirty queue internal references; no dirty key fast path and pure cache read behavior unchanged.

**Affected Version**: 2.6.0 - 2.9.0-dev.2

**Fixed Version**: 2.9.0-dev.2

**Fixed Content**: In the dirty window, unify **specificity-first** semantics — dotted (more specific) dirty values take precedence over section (wider) dirty values, read path and flush path use the same口径: ① `getConfig` after exact match in dirty key still overlays `_dirty_overlay` descendant dirty values (non-dict values return overlay subtree, same口径 as ③+④ scalar edges); ② `_flush_config` applies dirty keys in path depth order (section/ancestor first, dotted/daughter later, stable sort keeps same depth write order). Cost: In the same dirty window (about 5 seconds), section write back cannot overwrite still pending dotted write — read path fixed, read-modify-write naturally carries dotted values, actual impact surface is extremely small. ③ Involved dirty value `getConfig` returns (exact match / ancestor subtree / overlay merge) changed to `copy.deepcopy` isolation copy, no longer leak dirty queue internal reference; no dirty key fast path and pure cache read behavior unchanged.

**Fixed Date**: 2026/09/28

**Reproduction Steps**: ① `setConfig("FB.y", 1)`; ② `setConfig("FB", {"z": 2})`; ③ `force_save()` — before the fix, disk only has `[FB] z = 2` (y lost), after the fix `{"y": 1, "z": 2}`; Variant A: after steps ①② without flush, `getConfig("FB")` — before the fix does not contain `y`, after the fix visible.

**Regression Test**: `tests/unit/test_unit_config.py::TestSectionAndDottedDirtyConsistency` (Variant A two insertion orders / Variant B flush and order irrelevant / three-layer mixed survival / isolation copy / ancestor subtree isolation)

**Severity**: 🟡 Medium

**Type**: Configuration System

---

### [BUG-040] Command tail parameters in platform-split messages are silently lost

**Problem**: When a platform splits a message into multiple text segments (such as `/kick` with a mention segment in between, or input method segmentation), command distribution only takes the first text segment for matching — `/艾特 @xxx 123` is parsed as an unparameterized `艾特`, and commands declared with `args=` report "missing parameters," with no trace left.
**Cause**: The text extraction loop in `command.py` takes the first `type=="text"` segment and `break`s, discarding all other segments (including all non-text segments).
**Affected Version**: 2.6.0 (command distribution introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fixed Content**: Command text is changed to collect all text segments in order and concatenate them with spaces; mention/image layers no longer cause the entire command to fail to parse; also complete malformed segment tolerance (message is None/string/non-dict segment no longer crashes the distributor).
**Regression Test**: tests/unit/test_unit_command_multiseg.py

**Severity**: 🟡 Medium
**Type**: Event System

---

### [BUG-041] Rejected commands rerun via alt_message chain: duplicate replies and permission function side effects triggered twice

**Problem**: When the adapter's `alt_message` and message segment text are inconsistent (such as alt containing @text prefix), when a command is rejected by scope/ACL/master/permission, the distributor uses alt_message to rerun the entire chain — the user receives two "permission denied" replies, and custom permission functions (often with database/counter side effects) are called twice.
**Cause**: The reject path `return False` and "no command matched" share the same return value, so the distributor assumes alt fallback is possible; however, the event was already claimed before rejection, and the rerun only executes reply and permission judgment again.
**Affected Version**: 2.9.0 (governance/permission chain formed) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fixed Content**: Text processing changed to three-state contract (unmatched/consumed/rejected) — after matching a registered command (regardless of rejection), alt fallback is not used; only when no command is matched is alt fallback retained.
**Regression Test**: tests/unit/test_unit_command_multiseg.py::test_denied_command_not_rerun_via_alt

**Severity**: 🟡 Medium
**Type**: Event System

---

### [BUG-042] wait_reply registered in command handler is immediately consumed by the same trigger message

**Problem**: When `wait_reply` / registering interaction wait is called within a command execution body, the wait is immediately consumed by the same command message — the interaction flow's first question is skipped, and the "user reply" is actually the command text itself (wrong answer/data pollution).
**Cause**: `_handle_message` calls `interaction.resolve` twice, at the beginning and end, and the second resolve at the end consumes the wait registered during execution; cmdpass closing with alt missing scenario判定 as empty string directly allows, exacerbating the problem.
**Affected Version**: 2.8.0 (interaction session system introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fixed Content**: The distribution chain is converged to a single `interaction.resolve` (at the beginning), and the second call at the end is deleted; waits are unified to be consumed by the next message.
**Regression Test**: tests/unit/test_unit_command_multiseg.py::test_wait_reply_not_consumed_by_command_trigger

**Severity**: 🟡 Medium
**Type**: Event System

---

### [BUG-043] select() with same key multiple paths silently cancels the former

**Problem**: When `event.select()` derives multiple expectations for the same session key (same user different pattern, multiple session expectations, etc.), the latter registration cancels the former with "conflict," and select directly throws `InteractionCancelled` instead of the documented timeout returning `(None, None)`.
**Cause**: Each path independently calls `interaction.register`, and its mutual exclusion semantics cancel the previous wait with `REASON_CONFLICT` for the same key; the comment claims "multiple paths for the same user are independent due to event copy" is incorrect — the copy only changes `user_id`, the keys for the same user are completely identical.
**Affected Version**: 2.9.0 (select introduced) - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fixed Content**: Select is changed to aggregate waits — all expectations are merged into a single item with a custom matcher (key set registration, sharing the same future), and any path match returns the corresponding index; multiple paths for the same key naturally coexist.
**Regression Test**: tests/unit/test_unit_command_multiseg.py::test_select_same_user_multi_branch

**Severity**: 🟡 Medium
**Type**: Event System

---

### [BUG-044] BaseConverter.at() produces OB11 legacy "at" segment, framework-wide mention detection does not recognize

**Problem**: When the adapter uses `BaseConverter.at()` to assemble inbound events, `must_at_bot` / `has_mention()` / `on_at_message` / all framework mention detection and construction side (MessageBuilder/sending modifiers) are all for OB12's `"mention"`, two tracks coexist with no warning.
**Affected Version**: Not earlier than 2.5.0 - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fixed Content**: `at()` changed to produce `{"type": "mention", "data": {"user_id": ...}}` (method name retained alias, new `mention` alias added).
**Regression Test**: tests/unit/test_unit_command_multiseg.py::test_converter_at_produces_mention

**Severity**: 🟡 Medium
**Type**: Adapter

---

### [BUG-045] Interaction primitives permanently timeout and command penetration fail on adapters without alt_message

**Problem**: When the adapter only fills the message segment and does not fill `alt_message`, `confirm` / `choose` / `collect` wait for the user's plain text reply (such as "yes") indefinitely; registered commands cannot penetrate during the waiting period; `Event.get_text()` returns an empty string causing scaffolding examples to fail silently.
**Cause**: All the above paths directly take `alt_message` string, with no message segment fallback — the framework's "alt_message is an optional field of the adapter" contract, where only segment filling is a legal form.
**Affected Version**: All interaction primitive introduction versions - 2.10.0
**Fixed Version**: 2.10.1-dev.0
**Fixed Content**: Unify to `alt_message` priority + text segment fallback `extract_text`口径 (five places for value/verification in interaction primitives, cmdpass judgment, `Event.get_text()/get_message_text()`).
**Regression Test**: tests/unit/test_unit_command_multiseg.py

**Severity**: 🟡 Medium
**Type**: Event System

---

### [BUG-046] Declaration-based configuration template's nested sub-table header drifts to top-level table

**Problem**: When declaring a nested dataclass in the configuration (ConfigClass with nested dataclass fields), the sub-table header `[Nested]` in the first generated configuration template falls to the top level instead of the component section — the adapter cannot read `cfg.嵌套字段` value; `config.full.example` has the same error.
**Cause**: The template generator renders the relative table header (e.g., `[Nested]`) for the nested dataclass, while TOML table header semantics are absolute paths from the root; `setConfigTemplate` old implementation moves the parsed table object into the component section, and `full.example` directly concatenates text, neither path anchors the relative table header to the component path.
**Affected Version**: 2.10.0 - 2.10.1 (nested dataclass template rendering introduced with this version)
**Fixed Version**: 2.10.2
**Fixed Content**: `setConfigTemplate` precisely re-anchors table headers (e.g., `[Nested]` → `[ComponentName.Nested]`) based on the template's parsed sub-table path; `config.full.example` generation side changes to pass `_prefix` to directly produce absolute table headers.
**Regression Test**: tests/unit/test_unit_config.py::TestTomlclassEngineMigration::test_template_write_idempotent_and_nested_anchored

**Severity**: 🟡 Medium
**Type**: Configuration System / Adapter

---

### [BUG-047] Full enumeration of service directory misses lazy-loaded modules

**Problem**: `sdk.module.services()` full enumeration skips un-instantiated (lazy-loaded) modules — modules declaring `meta.services` do not appear in the directory, so discovery-based consumers (AI agents, help module, etc.) cannot find their services; single-module precise query `services("Name")` and topology `get_topology()` are unaffected.
**Cause**: The `ModuleManager.services()` full enumeration branch skips un-contract cached modules at the point of on-site contract parsing, even after parsing the contract, still unconditionally `continue` — the original intent was to skip modules that do not declare services, but actually skips un-loaded modules; loaded modules are unaffected as they write the contract cache on loading.
**Affected Version**: 2.9.0 - 2.10.1 (module RPC and service directory introduced with 2.9.0)
**Fixed Version**: 2.10.2
**Fixed Content**: Delete the unconditional skip, unify by "only skip if the parsing result is empty" judgment; un-loaded modules parse `get_meta().services` on-site (same口径 as `module.call()` whitelist), modules declaring services are included in the directory.
**Regression Test**: tests/unit/test_unit_module_rpc.py::TestServicesDirectory::test_lazy_declared_module_in_full_directory

**Severity**: 🟡 Medium
**Type**: Loading System

---

### [BUG-048] Session inbox query API loses message attribution (sender and event metadata)

**Problem**: All query interfaces of the inbox (`get()` / `get_by_trace()` / `event.history()`) return records with only `role/text/ts/event_id` — the storage layer's existing `sender` column is discarded by the query layer, making it impossible to distinguish different members' messages in group chat replay (AI misattributes member B as the previous conversation's member A); inbound records do not archive event metadata at the time of the event, so retrospective lookup gets the "current nickname" instead of the "then nickname."
**Cause**: The comment when adding the `sender` column in 2.8.0 stated it was used for "replaying message source," but the select and return construction did not carry it (implementation oversight); metadata archiving was never designed — `append()` has no meta channel, and the table structure has no corresponding column.
**Affected Version**: 2.8.0 - 2.11.0 (sender column introduced with 2.8.0)
**Fixed Version**: 2.11.1-dev.0
**Fixed Content**: Add `meta` column (whitelist contract: inbound nickname/self_id/sub_type/message_id, outbound sending context and module; old table automatically migrates, backend does not support ALTER silently falls back to `{}`); `append()` adds `meta` parameter throughout memory buffer and batch writing; `get` / `recent` / `get_by_trace()` / `event.history()` uniformly return `sender` + `meta` (JSON damage falls back to `{}`).
**关联**: #467 (same batch #468 / #469 / #470)
**Regression Test**: tests/unit/test_unit_transcript_attribution.py::TestSenderMetaReadback / TestMetaMigration

**Severity**: 🟡 Medium
**Type**: Session Inbox / Storage System

---

### [BUG-049] Inbound bot self-message echo recorded as user, polluting inbox attribution

**Problem**: In platforms/protocols that enable message echo (OneBot v11 `report-self-message`, Telegram outgoing, etc.), when the bot sends a message itself and reports it as a message event, the inbox records it as `role="user"` — the robot's self-message and real user input are indistinguishable, downstream modules treat the robot's self-message as user input (responding to what the "user" said based on it), and role statistics are distorted.
**Cause**: The inbound automatic record point (`Core/adapter.py`) records `role="user"` for all `event_type == "message"` unconditionally, without consuming the `self` field for bot echo detection — while the subsequent bot self-detection logic is already consuming the same field (recordable at the time of recording).
**Affected Version**: 2.8.0 - 2.11.0 (inbox automatic record introduced with 2.8.0)
**Fixed Version**: 2.11.1-dev.0
**Fixed Content**: Before recording, identify echo by `self.user_id == user_id`, and process according to the new configuration `ErisPulse.transcript.self_echo` three modes: `"bot"` (default) records `role="bot"` + `sender=self_id` + `meta.self_echo=true`; `"skip"` does not record; `"user"` maintains the original behavior. For non-echo platforms (self missing or not equal), each field returns unchanged.
**关联**: #470 (dependent on #467's meta column to carry self_echo marker)
**Regression Test**: tests/unit/test_unit_transcript_attribution.py::TestSelfEcho

**Severity**: 🟡 Medium
**Type**: Adapter / Session Inbox
