---
name: erispulse-communication
description: "适用于：模块间通信（RPC/定向/广播）、HTTP/WS 客户端、连接管理。覆盖场景：**Когда читать эту статью**: при необходимости вызова между модулями (RPC), определении контракта сервиса, целевой рассылке событий или восстановлении при холодном запуске. Если это не требуется — пропустите, это не повлияет на использование других функций.。**Когда нужно читать эту статью**: если вам нужны пулы соединений WebSocket/SSE, группы рассылки, пересылка между модулями или просмотр подключений. Если это не требуется, можно пропустить, это не повлияет на использование других функций.。**Когда нужно читать эту статью**: при необходимости исходящих HTTP / WebSocket-запросов. Если не нужно, можно пропустить, это не повлияет на использование других функций.。**Когда нужно читать**: при необходимости маршрутизации HTTP / WebSocket / SSE (включая трансляцию в пуле соединений). Если не нужно — пропустите, это не повлияет на использование других функций.。"
---

# ErisPulse 通信与连接

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 模块间通信

> 来源: `docs/ru/advanced/module-communication.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ru/advanced/module-communication.md）

# Коммуникация между модулями

> [!TIP]
> **Когда читать эту статью**: при необходимости вызова между модулями (RPC), определении контракта сервиса, целевой рассылке событий или восстановлении при холодном запуске. Если это не требуется — пропустите, это не повлияет на использование других функций.

> **Что вы узнаете**: мнемоника выбора модели коммуникации (RPC / целевое событие / широковещательное), `meta.services` как контракт и каталог сервисов, конфигурация аудита исходящих вызовов, ленивое пробуждение и восстановление при холодном запуске.
>
> **В этой статье не рассматривается**: механизм регистрации / запуска / приоритетов самого события жизненного цикла (см. [Управление жизненным циклом](lifecycle.md)); конфигурация ленивого загрузки и объявление activate_on (см. [Система ленивой загрузки](lazy-loading.md)).

> [!NOTE]
> Содержание этой главы требует ErisPulse **2.8.0+**.

В ErisPulse между модулями существует **трехуровневая модель коммуникации**, отсортированная по "точка-точка → целевая → широковещательная":

| Уровень | API | Семантика | Типичные сценарии |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | Точечный запрос-ответ с контрактом / аудитом / таймаутом | Вызов функционала другого модуля (получение истории, перевод, возврат средств) |
| **Целевое событие** | `await lifecycle.emit("message_received", {...}, to="Chat")` | Рассылка только модулям, зарегистрировавшим жизненный цикл-хук | Уведомление о состоянии от upstream в downstream ("получено новое сообщение") |
| **Широковещательное событие** | `await lifecycle.emit("config.updated", {...})` | Событие жизненного цикла, видимое по всей рамочной архитектуре | Горячая перезагрузка конфигурации, появление/исчезновение модулей |

{!--< tips >!--}
Мнемоника выбора: **используйте `call`, если нужно получить ответ, используйте `emit(..., to=...)`, если нужно уведомить только один модуль, используйте `emit(...)` для уведомления всех**.
{!--< /tips >!--}

## RPC: module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

Различия между `module.call()` и прямым доступом к атрибуту `sdk.module.Chat.get_history(...)` (без изменений):

| | `module.call()` | Прямой доступ к атрибуту |
|---|---|---|
| Целевой модуль не зарегистрирован / не активирован | Выбрасывает `ModuleNotAvailableError` | Выбрасывает `AttributeError` |
| Ленивая загрузка модуля | **Автоматически активируется** (модули, управляемые событиями, используют блокировку активации) | Асинхронная инициализация модуля выбрасывает RuntimeError |
| `current_owner` | Присваивается **целевому модулю** (его внутренние wait_reply / отправка / логи корректно привязаны) | Сохраняется вызывающий модуль |
| Таймаут | По умолчанию 30 секунд (`timeout=` позволяет перезаписать, `None` отключает таймаут) | Нет |
| scope аудит | Вызыватель проходит через контрольный пункт `actions.<вызыватель>.call` | Нет |
| Проверка контракта | Белый список `meta.services` | Нет |

### Система исключений

```
ModuleError                      # Базовый класс исключений модульной системы
└── ModuleCallError              # Базовый класс для вызовов между модулями (содержит атрибуты module / method)
    ├── ModuleNotAvailableError  # Целевой модуль не зарегистрирован / не активирован / активация не удалась
    ├── ServiceNotProvidedError  # Метод не в белом списке / приватный метод / не существует
    └── ModuleCallTimeoutError   # Время ожидания асинхронного метода истекло
```

Все исключения входят в систему `ErisPulseError`, можно поймать их через `from ErisPulse.Core import ModuleCallError`.

## Контракт сервиса: meta.services

Поставщик сервиса объявляет белый список предоставляемых методов в `get_meta()` (в симметрии с `commands`):

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="聊天",
            services=[
                "get_history",                                       # Простая форма
                {"name": "translate", "description": "把文本翻译成指定语言"},  # С описанием
            ],
        )

    async def get_history(self, session_id, n=20): ...
    async def translate(self, text, target_lang): ...
    def _internal_helper(self): ...   # Методы с подчеркиванием всегда запрещены для внешнего вызова
```

**По умолчанию разработчик не замечает**:

- Если `services` не объявлен → все **публичные** методы по умолчанию доступны для `module.call()` (как и при прямом доступе к атрибуту),
  без необходимости каких-либо объявления
- После объявления → доступ сужается до белого списка, вызов за пределами списка выбрасывает `ServiceNotProvidedError` — используется для маркировки
  "эти методы — те, что публично обещаны"
- Основной контроль за ограничениями находится у пользователя: `scope.actions` определяет "кто может вызывать кого" (см. аудит ниже),
  `services` модуля автора — лишь объявление сервиса, два уровня не заменяют друг друга

**Описание сервиса**: для каждого сервиса можно добавить описание, читаемое человеком / ИИ — если не нужно, ничего не пишите,
описание автоматически берется из **первой строки docstring** (рамка уже требует стиля docstring):

```python
async def translate(self, text, target_lang):
    """把文本翻译成指定语言"""    # ← Эта строка автоматически становится описанием сервиса
    ...
```

**Подсказки по параметрам**: вызывающей стороне (особенно ИИ-агентам) нужно знать, что означает каждый параметр. Если не нужно, ничего не пишите,
подсказки автоматически берутся из **`:param:` строк docstring**:

```python
async def render_card(self, html, width=800, height=0):
    """渲染 HTML 为图片文件

    :param html: 要渲染的 HTML 文本          ← Автоматически становится подсказкой параметра
    :param width: 画布宽度像素，0 为按内容自适应
    :param height: 画布高度像素，0 为按内容自适应
    """
```

Для тонкой настройки (переопределение docstring / мультиязычность) используйте словарь для описания `description` и `parameters`
(оба поддерживают словарь i18n; `parameters` объединяется с docstring по параметрам, при явном объявление параметра в словаре он имеет приоритет,
объявленные параметры, которых нет в сигнатуре, будут отфильтрованы):

```python
services=[
    {"name": "translate", "description": "把文本翻译成指定语言"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "摘要对话"}},
    {
        "name": "render_card",
        "description": "渲染 HTML 为图片文件",
        "parameters": {"html": "HTML 文本", "width": "宽度像素，0 为自适应"},
    },
]
```

## Служба каталога: services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': '把文本翻译成指定语言',
#            'parameters': {'session_id': '会话 ID', 'n': '返回条数'}}]}

sdk.module.services("Chat")   # Только для определенного модуля
```

- В каталоге перечислены **только модули с явно объявленным** `meta.services` (модули без объявления не появляются в каталоге)
- Каждый сервис снабжен строкой сигнатуры метода (`inspect.signature`), описанием и подсказками по параметрам
- **Ленивые модули также попадают в каталог** (обнаружение сервисов происходит до загрузки) — вызывающая сторона может решить,
  нужно ли `call()` для активации целевого модуля
- Также включены в топологию: `sdk.module.get_topology()` для каждого модуля содержит поле `services`

{!--< tips >!--}
**Путь к MCP**: каталог сервисов (имя + сигнатура + описание + подсказки по параметрам) — это форма MCP tool —
каждый сервис по сути имеет вид ``{"name", "description", "parameters"}``.
В будущем фреймворк может напрямую экспортировать ``services()`` как конечную точку MCP-сервера, чтобы ИИ мог обнаруживать и вызывать возможности модуля;
``scope.actions.call`` аудит становится естественным брандмауэром безопасности для вызовов ИИ.
{!--< /tips >!--}

## Аудит исходящих вызовов: кто может вызывать кого

Каждый вызов `module.call()` проходит через контрольный пункт `scope` исходящих вызовов **от имени вызывающего модуля**:

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # Запретить CallerModule вызывать Chat.get_history
# allow = ["Chat.get_*"]           # Или белый список: разрешить вызывать только сервисы Chat, начинающиеся на get_
```

- Формат `name` — `<目标模块>.<方法名>`, поддерживает точное / шаблон / `re:` регулярное выражение
- Вызовы фреймворка (без контекста owner, например, запуск скриптов) не подвергаются аудиту
- Отказ в вызове выбрасывает `ModuleCallError` (TRACE лог `core.module.call_denied`)

Способы настройки см. в [Scope](scope.md) в разделе исходящего аудита.

## Направленные события: параметр to в lifecycle.emit

События жизненного цикла поддерживают направленную передачу: указание `to` для целевого владельца (owner) заставляет событие доставляться только хукам, зарегистрированным с этим
владельцем (хуки, зарегистрированные в `on_load`, автоматически присваиваются владельцу модуля),
остальные модули и обработчики с `*` не получают уведомления.

```python
from ErisPulse.Core.lifecycle import lifecycle

# Отправитель: событие доставляется только хукам, зарегистрированным модулем Chat
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# Подписчик (внутри модуля Chat): регистрирует хук с таким же именем, owner автоматически записывается при регистрации
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # Префикс родительского события также действует (фильтруется по owner)
async def on_any(data): ...
```

Семантические детали:

- Если у целевого владельца нет зарегистрированных хуков → событие **тихо отбрасывается** (не отправляется туда, где его нет),
  можно заранее проверить наличие хуков с помощью `lifecycle.has_handlers("message_received")`
- Если `data` — словарь, автоматически добавляется `_trace_id` (не перезаписывает уже существующее значение), интегрируется с системой трассировки
- Широковещательные и направленные события используют одну и ту же систему регистрации хуков: `emit(...)` без `to` рассылает по всей системе,
  с `to` — одно и то же событие видно только целевому модулю
- `emit_sync` / `submit_event` (совместимый API) также поддерживают параметр `to=`

> [!NOTE]
> Направленные события — это лёгкие уведомления, **не проверяются на существование целевого модуля и не активируют ленивую загрузку**; если нужно проверить существование цели,
> аудит контракта или получить возвращаемое значение, используйте [RPC: module.call](#rpcmodulecall).

## Ленивая загрузка и вызов

`module.call()` прозрачно активирует ленивые модули:

- Модули, управляемые событиями (`activate_on` объявлен) → используют блокировку активации `_activate()`, после активации stub-триггер автоматически удаляется
- Обычные ленивые модули → синхронная инициализация или обычный путь загрузки (идемпотентно)
- Активация не удалась → `ModuleNotAvailableError`

То есть: **вызывающий модуль не должен заботиться о том, загружен ли целевой модуль**, и не нужно ждать какого-либо события для его активации.

Направленные события (`lifecycle.emit(..., to=...)`) не активируют ленивую загрузку — если целевой модуль не загружен, у него нет хуков,
событие тихо отбрасывается; если нужно гарантировать доставку, используйте `module.call()`.

## Воспроизведение при холодном запуске

Новый / перезапущенный модуль пропустил часть чата — `get_load_strategy(replay=...)` позволяет фреймворку после готовности модуля
**воспроизвести последние сообщения из почтового ящика сессии** для этого модуля:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # Воспроизвести последние 5 минут (возможны и другие форматы: "1h" / "300" секунд)
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # Синтезированное событие: только для восстановления контекста, не вызывает побочных эффектов, таких как отправка
                ...
```

Семантические детали:

- Источник данных — [почтовый ящик сессии](interaction.md#会话收件箱eventhistory) (`sdk.transcript.recent()`),
  воспроизведение происходит в фоне после загрузки модуля, не блокируя запуск
- Синтезированное событие снабжается флагом `replayed: True`, полными `platform / detail_type / user_id / alt_message`,
  **доставляется только обработчикам этого модуля** — другие модули не затрагиваются воспроизведением
- Если почтовый ящик не включен / нет записей / указано недопустимое время воспроизведения (`replay_invalid` предупреждение) — тихо пропускается

## Дедупликация событий

При повторном подключении websocket-платформы часто повторно отправляются одни и те же события (с одинаковым `event["id"]`) — на входе распределения по id делается
LRU-дедупликация (емкость 4096), одно и то же событие доставляется только один раз.

```toml
[ErisPulse.framework]
event_dedupe = true   # По умолчанию включено; в тестовой среде можно отключить для фиксированных id синтезированных событий
```

При регистрации адаптера (начало жизненного цикла нового подключения) автоматически сбрасывается кэш дедупликации.

## Связанные документы

- [Система взаимодействий](interaction.md) - wait_reply / таймеры / многопоточное ожидание / взаимное исключение сессий
- [Scope](scope.md) - полная конфигурация аудита исходящих вызовов
- [Система ownership](ownership.md) - как контекст owner проходит через межмодульные вызовы
- [Система ленивой загрузки](lazy-loading.md) - ленивая загрузка и активация на основе событий (activate_on)
- [Управление жизненным циклом](lifecycle.md) - механизм широковещательной шины событий

## 连接管理

> 来源: `docs/ru/advanced/connections.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ru/advanced/connections.md）

# Пул соединений и трансляция

> [!TIP]
> **Когда нужно читать эту статью**: если вам нужны пулы соединений WebSocket/SSE, группы рассылки, пересылка между модулями или просмотр подключений. Если это не требуется, можно пропустить, это не повлияет на использование других функций.

> **Что вы узнаете**: как три типа соединений автоматически регистрируются в реестре, API подписки и трансляции по группам, повторное использование и управление между модулями, а также семантика очистки соединений при выгрузке модуля.
>
> **В этой статье не рассматривается**: регистрация маршрутов WebSocket / SSE и хуки жизненного цикла соединений (см. [Менеджер маршрутов](router.md)); HTTP-запросы от клиента (см. [Сетевой клиент](http-client.md)).

Соединения (серверные WebSocket / SSE / клиентские WebSocket) в ErisPulse являются **ресурсами первого класса на уровне фреймворка**:
при установлении соединения они автоматически регистрируются в едином реестре, поддерживают трансляцию, подписку на группы и передачу/повторное использование между модулями,
а при выгрузке модуля фреймворк автоматически закрывает и освобождает соединения — бизнес-логике больше не нужно создавать собственные коллекции `_ws_clients`, и не нужно беспокоиться о утечках из-за забытой очистки.

> Примеры в этой документации используют **импорт на уровне корня** (рекомендуется начиная с версии 2.10+):
> `from ErisPulse import connections, router, client, WebSocketConnection`

## Обзор

```python
from ErisPulse import connections, router, WebSocketConnection

# Сервер: соединение автоматически регистрируется, handler добавляет в бизнес-группу
@router.ws("MyModule", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")            # Название группы полностью определяется бизнес-логикой
    async for msg in ws.iter_text():
        ...                             # При разрыве соединения фреймворк автоматически отменяет регистрацию и очищает группу

# В любом месте: трансляция в группу (возвращает подробности успеха/неудачи)
result = await connections.broadcast({"type": "notify"}, group="room:1")
if not result.ok:
    ...                                 # result.failed: {id соединения: исключение}
```

Три вида соединений объединяются в единую таблицу регистрации:

| kind | Источник | Владелец owner | Описание |
|------|------|-----------|------|
| `server` | `@router.ws(...)` / `register_websocket(...)` | Модуль, зарегистрировавший маршрут | При разрыве автоматически отменяется регистрация |
| `sse` | `@router.sse(...)` / `register_sse(...)` | Модуль, зарегистрировавший маршрут | Трансляция через `sse.send()` |
| `client` | `await client.ws_connect(url)` | Текущий модуль (или явно указанный `owner=`) | При закрытии/разрыве удалённой стороны автоматически отменяется регистрация; при остановке адаптера фреймворк закрывает все соединения |

Для отключения автоматической регистрации: передайте `track=False` в маршрут или при исходящем соединении, старый код будет работать без изменений.

## Просмотр пула соединений

```python
from ErisPulse import connections

# Просмотр пула соединений модуля ("Сколько активных соединений сейчас у модуля?")
conns = connections.list(namespace="Dashboard")
for conn in conns:
    print(conn.id, conn.kind, conn.groups, conn.meta)

# Фильтрация по другим параметрам (все условия AND)
connections.list(owner="MyAdapter", kind="client")
connections.list(group="tenant:acme")

# Общая статистика (подсчёт по всем измерениям)
stats = connections.stats()
# {'total': 5, 'by_kind': {...}, 'by_namespace': {...}, 'by_owner': {...}, 'groups': {...}}

# Подсчёт аудита принадлежности (модуль ownership также доступен)
from ErisPulse import ownership
ownership.counts("Dashboard")   # {'connections': 3, ...}
```

У каждого соединения можно получить идентификационную информацию: `conn.id` (вроде `Dashboard:1a2b3c4d`), `conn.namespace`, `conn.owner`, `conn.kind`, `conn.groups`, `conn.meta` (свободный словарь бизнес-логики).

## Трансляция и подписка

### Группы (модель подписки)

Группы — это **плоские строки**, их именование полностью определяется бизнес-логикой (комнаты / арендаторы / темы...),
вложенные уровни выражаются соглашениями в именах (например `tenant:acme/room:1`), фреймворк не ограничивает формат.

Операции возможны в двух направлениях:

```python
# Направление 1: соединение активно присоединяется/отключается (внутри handler)
@router.ws("Chat", "/ws")
async def handle(ws: WebSocketConnection):
    ws.join_group("room:1")        # Эквивалентно connections.assign(ws.id, "room:1")
    ws.leave_group("room:1")

# Направление 2: управление пассивно распределяет (внутри маршрута / других модулях)
connections.assign(conn_id, "tenant:acme")
connections.dismiss(conn_id, "tenant:acme")   # Без указания группы = выход из всех групп
```

При разрыве соединения автоматически выходят из всех групп, бизнес-логика не должна очищать.

### Трансляция

```python
result = await connections.broadcast(
    data,                       # Для WS используется send_json; для SSE — send (автоматическая сериализация JSON)
    namespace="Dashboard",      # Фильтр по пространству имён
    group="room:1",             # Фильтр по группе
    kind="sse",                 # Фильтр по типу соединения
    owner="MyAdapter",          # Фильтр по владельцу
    ids={conn_id, ...},         # Явное указание кандидатов (фильтры всё ещё действуют)
    exclude={conn_id},          # Исключение некоторых соединений
    timeout=10.0,               # Таймаут отправки на одно соединение (не общий)
    concurrency=64,             # Максимальное количество одновременных отправок
    raise_on_error=False,       # При True выбрасывается первое исключение при неудаче
)
result.total      # Общее количество целевых соединений (исключая предварительно)
result.sent       # Список успешно отправленных соединений
result.failed     # {id соединения: исключение} (таймаут/разрыв/ошибка отправки)
result.excluded   # Исключённые соединения
result.ok         # Успешна ли отправка всем
```

Фильтры между собой работают по правилу **AND**; неудача одного соединения не влияет на другие; соединения из `ids`, которых уже не существует, учитываются в `failed` (чтобы бизнес-логика знала полную картину).

### События жизненного цикла

При регистрации/удалении соединения/изменении групп генерируются стандартные события жизненного цикла, которые могут подписываться Dashboard и другие, для отображения в реальном времени:

```python
from ErisPulse import lifecycle

@lifecycle.on("connection.registered")
async def on_registered(data): ...
@lifecycle.on("connection.unregistered")
async def on_unregistered(data): ...
@lifecycle.on("connection.group.joined")
async def on_joined(data): ...
@lifecycle.on("connection.group.left")
async def on_left(data): ...
```

## Передача / повторное использование между модулями

Соединение является зарегистрированным ресурсом фреймворка, любой модуль может получить его по ID и **повторно использовать** —
не нужно создавать новое соединение, и не нужно знать, кто его создал:

```python
from ErisPulse import connections

conn = connections.get("Dashboard:1a2b3c4d")   # Если не существует/разорвано выбрасывается ConnectionNotFoundError
await conn.send_json({"ping": 1})              # Любой модуль может отправить
conn.join_group("someone-elses-room")          # Также может участвовать в группах
```

**Принадлежность и права закрытия**:

- Владелец модуль, создавший соединение, имеет исключительное право закрытия. При вызове `close()` из не владельца выбрасывается `ConnectionPermissionError` (импорт `from ErisPulse import ConnectionPermissionError`);
- Операции отправки и присоединения доступны для всех модулей, не требуют авторизации;
- При выгрузке модуля / остановке адаптера фреймворк **закрывает и отменяет регистрацию** всех его соединений (серверных и исходящих), ссылки на уже полученные соединения при отправке получат результат неудачи, подписка на событие `connection.unregistered` позволит отслеживать;
- Внутренний путь освобождения фреймворка использует `close(force=True)` для обхода проверки.

> Объяснение: проверка прав закрытия зависит от контекста владельца во время выполнения (например `owner_scope` / событийная диспетчеризация / `spawn_background` и т.д. автоматически передают). Вызовы без контекста принадлежности (старый код без контекста) разрешаются, чтобы не нарушить работу; новые вызовы в контексте владельца будут защищены.

## Исходящие соединения (клиентская сторона)

```python
from ErisPulse import client

ws = await client.ws_connect("wss://example.com/ws")
ws.id          # Уже зарегистрирован, доступен для поиска/трансляции через connections
ws.owner       # Текущий модуль (при недоступности контекста владельца рекомендуется явно указать)

# При недоступности контекста владельца (например, в обратном вызове из потока инструментов) явно указать, чтобы при выгрузке могло автоматически освободиться:
ws = await client.ws_connect("wss://example.com/ws", owner="MyAdapter")
```

При активном разрыве удалённой стороны, локальном `close()` или выгрузке модуля автоматически отменяется регистрация; с момента выгрузки старые способы создания и управления соединениями без регистрации и очистки устарели.

## Передача между потоками

Для доступа к соединению из подпотока (трансляция / отправка / закрытие) используйте стандартные средства фреймворка для возврата в главный цикл, **не используйте вручную `run_coroutine_threadsafe`**:

```python
from ErisPulse import run_main_loop, spawn_later, spawn_thread

# Блокирующий вызов из подпотока:
run_main_loop(connections.broadcast({"tick": 1}, group="room:1"), timeout=5)

# Фоновый поток + задержанная задача (принадлежность владельца, автоматически отменяется при выгрузке):
def push_tick():
    return connections.broadcast({"tick": 1}, group="room:1")
spawn_later(30, push_tick, owner="MyModule")
```

## Семантика выгрузки и очистки

Цепочка возврата принадлежности при выгрузке модуля / остановке адаптера последовательно: отмена фоновых задач и таймеров принадлежащих владельцу → **закрытие и отмена регистрации принадлежащих соединений** → вызов хука on_cleanup → отмена регистрации маршрутов/обработчиков и других ресурсов. Подробнее см. [Система принадлежности (owner)](ownership.md).

> [!WARNING]
> Начиная с версии 2.10, выгрузка модуля приводит к закрытию его зарегистрированных WS/SSE/исходящих соединений. Компоненты, зависящие от "сохранения соединений после выгрузки" (например, старая версия Dashboard-отправки), должны быть осведомлены — это ожидаемое поведение для предотвращения утечек соединений.

## Справочник API

| API | Описание |
|-----|------|
| `connections.get(id)` | Получение соединения (вход между модулями), выбрасывает `ConnectionNotFoundError` при отсутствии |
| `connections.list(namespace=, owner=, group=, kind=)` | Фильтрация и поиск списка соединений |
| `connections.stats(namespace=, owner=)` | Подсчёт статистики по измерениям |
| `connections.assign(id, *groups)` / `dismiss(id, *groups)` | Добавление/удаление групп со стороны управления |
| `await connections.broadcast(data, ...)` | Трансляция, возвращает `BroadcastResult` |
| `await connections.close(id, force=False)` | Закрытие и отмена регистрации (с проверкой прав) |
| `await connections.close_owner(owner)` | Закрытие и отмена регистрации всех соединений владельца (вызывается в цепочке выгрузки) |
| `conn.join_group(*groups)` / `conn.leave_group(*groups)` | Присоединение/выход из групп со стороны соединения |
| `conn.send_json / send_text / iter_text / ...` | Отправка и приём (интерфейсы сервера/клиента одинаковы) |
| `conn.meta` | Словарь бизнес-метаданных |
| `conn.close(force=False)` | Закрытие (не владелец выбрасывает `ConnectionPermissionError`) |

## Связанные документы

- **Регистрация WS / SSE маршрутов на стороне сервера** → [Менеджер маршрутов](router.md)
- **Установление исходящего WebSocket-соединения на стороне клиента** → [Сетевой клиент](xclient.md)
- **Как соединения восстанавливаются при выгрузке модуля** → [Система принадлежности (owner)](ownership.md)
- **Исключения, связанные с соединениями (ConnectionNotFoundError / ConnectionPermissionError)** → [Иерархия исключений и руководство по обработке](errors.md)

## HTTP 客户端

> 来源: `docs/ru/advanced/http-client.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ru/advanced/http-client.md）

# Сетевой клиент

> [!TIP]
> **Когда нужно читать эту статью**: при необходимости исходящих HTTP / WebSocket-запросов. Если не нужно, можно пропустить, это не повлияет на использование других функций.

ErisPulse предоставляет унифицированный сетевой клиент, объединяющий HTTP-запросы, WebSocket-соединения и управление пулами соединений. Модули и адаптеры **должны использовать** этот клиент, а не самостоятельно импортировать сторонние библиотеки, такие как `aiohttp`, `httpx`, `requests`.

## Обзор

Основные функции сетевого клиента:

- **Единый интерфейс**: предоставляет методы `get` / `post` / `put` / `delete` / `patch` / `request`
- **WebSocket-клиент**: установление WebSocket-соединения с помощью `ws_connect`
- **Автоматическая запись логов**: все запросы автоматически записываются в логи и статистику
- **Интеграция с жизненным циклом**: каждый запрос вызывает событие жизненного цикла `client.request`, а подключение WebSocket — событие `client.ws.connect`
- **Поддержка повторных попыток**: можно настроить количество и интервал автоматических повторных попыток
- **Управление тайм-аутами**: независимые тайм-ауты подключения и запроса
- **Повторное использование пула соединений**: управление пулом соединений на основе aiohttp.ClientSession
- **Система исключений**: исключения aiohttp автоматически преобразуются в исключения ErisPulse (система ClientError)

## Быстрый старт

### HTTP-запросы

```python
from ErisPulse.Core import client

# GET-запрос
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST-запрос
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket-соединение

```python
from ErisPulse import client   # Импорт с корня (с версии 2.10, совместим с глубоким ErisPulse.Core.client)

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

#### Автоматическая регистрация исходящих соединений в пуле (с версии 2.10)

Соединения, созданные через `ws_connect`, **по умолчанию автоматически регистрируются** в пуле соединений фреймворка (отключение посредством `track=False`):
их можно просматривать с помощью `connections.list(owner=...)`, рассылать сообщения; при закрытии соединения или разрыве удалённой стороны оно автоматически удаляется из пула;
**при выгрузке модуля / остановке адаптера фреймворк автоматически закрывает** все исходящие соединения, связанные с ним, предотвращая утечки.

```python
from ErisPulse import client, connections

ws = await client.ws_connect("wss://example.com/ws")
print(ws.id, ws.owner)   # Уже зарегистрировано: id соединения и владелец

# При отсутствии контекста owner (например, в обратном вызове из рабочего потока) явно укажите владельца, чтобы корректно произошла автоматическая выгрузка:
ws2 = await client.ws_connect("wss://example.com/ws2", owner="MyAdapter")
```

См. подробнее [Пул соединений и трансляция](connections.md).

## HttpResponse

Все методы запроса возвращают объект `HttpResponse`:

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP-код состояния (например, 200, 404)
resp.reason       # str | None - описание состояния (например, "OK")
resp.headers      # заголовки ответа (без учета регистра)
resp.content_type # str | None - Content-Type
resp.url          # окончательный URL (может измениться из-за перенаправления)
resp.raw          # базовый необработанный объект ответа (в настоящее время aiohttp.ClientResponse)

# Чтение тела ответа
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # разбор JSON
text = await resp.text("gbk")  # указать кодировку
```

## Методы запроса

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# Тело запроса в формате JSON
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# Тело запроса в формате формы
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# Сырые данные
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# Загрузка файлов (используя параметр files, без необходимости импортировать aiohttp)
# Формат: {имя_поля: файл/bytes/(имя_файла, файл)/(имя_файла, файл, тип_содержимого)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "Аватар"},            # Необязательно: можно передавать обычные поля формы
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# Упрощённый синтаксис: передача объекта файла напрямую
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# Загрузка данных из памяти (без сохранения на диск)
import io

resp = await client.post(
    "https://api.example.com/upload",
    files={"file": ("data.txt", io.BytesIO(b"file content"), "text/plain")},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### Общий request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## Параметры

### Параметры HTTP-запроса

| Параметр | Тип | Описание |
|------|------|------|
| `url` | `str` | URL-адрес запроса |
| `params` | `dict[str, str]` | Параметры запроса (необязательно) |
| `headers` | `dict[str, str]` | Дополнительные заголовки запроса (необязательно) |
| `data` | `Any` | Тело запроса (форма или необработанные данные) (необязательно) |
| `json` | `Any` | Тело запроса в формате JSON (необязательно) |
| `files` | `dict[str, Any]` | Поля для загрузки файлов (необязательно, автоматически создает multipart/form-data) |
| `timeout` | `float` | Таймаут запроса (секунды) (необязательно, переопределяет значение по умолчанию) |
| `max_retries` | `int` | Максимальное количество повторных попыток запроса (необязательно, переопределяет значение по умолчанию) |

### Параметры ws_connect

| Параметр | Тип | Описание |
|------|------|------|
| `url` | `str` | URL-адрес WebSocket-сервера |
| `headers` | `dict[str, str]` | Дополнительные заголовки запроса (необязательно) |
| `heartbeat` | `float` | Интервал в секундах для отправки心跳 (необязательно) |

## Тайм-ауты и повторные попытки

```python
from ErisPulse.Core import Client

# Создание клиента с пользовательскими тайм-аутами
client = Client(
    timeout=60,           # Общий тайм-аут запроса 60 секунд
    connect_timeout=5,    # Тайм-аут подключения 5 секунд
    max_retries=3,        # Автоматические повторные попытки при сбое 3 раза
    retry_delay=2,        # Интервал между повторными попытками 2 секунды
)

# Переопределение тайм-аута для одного запроса
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> Класс клиента с версии 2.8.0 переименован в `Client` (имя свойства `sdk.client` остается неизменным); старое имя `HttpClient` сохранено как совместимый псевдоним, поэтому старый код не требует изменений.

## Пользовательские заголовки по умолчанию

```python
client = Client(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## Статистика запросов

```python
from ErisPulse.Core import client

# Просмотр статистики
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# Сброс статистики
client.reset_stats()
```

## Жизненный цикл событий

### События HTTP-запросов

Событие `client.request` срабатывает после завершения каждого запроса и может использоваться для мониторинга:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### События WebSocket-соединений

Событие `client.ws.connect` срабатывает после установления каждого WebSocket-соединения:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS соединение: {event_data['url']}")
```

## Управление контекстом

```python
# Использование как контекстный менеджер для автоматического закрытия сессии
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket клиент

Создайте WebSocket-клиентское соединение с помощью `client.ws_connect()`, возвращается объект `ClientWebSocket`. Клиентские и серверные WebSocket-соединения используют один и тот же базовый класс `WebSocketConnectionBase`, интерфейсы send/receive/iter полностью совпадают.

### Основное использование

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### Получение сообщений

#### Высокоуровневые методы (рекомендуется)

Автоматически фильтрует типы сообщений и при разрыве соединения выбрасывает `WebSocketDisconnect`:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# Получение одного сообщения
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# Итерация по сообщениям (автоматически останавливается при разрыве соединения)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### Низкоуровневые методы

Используйте `receive()` и `iter_messages()` для обработки необработанных типов сообщений, можно различать TEXT / BINARY / CLOSE / ERROR:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# Получение одного необработанного сообщения
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# Итерация по необработанным сообщениям (автоматически останавливается при CLOSE/ERROR)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"Текст: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"Двоичные данные: {len(msg.data)} байт")
```

### WSMessage

`WSMessage` — это единый тип WebSocket-сообщения, не зависящий от базовой библиотеки:

| Свойство | Тип | Описание |
|------|------|------|
| `type` | `str` | Тип сообщения: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | Данные сообщения |

### Свойства ClientWebSocket

| Свойство | Тип | Описание |
|------|------|------|
| `url` | `URL` | URL соединения |
| `headers` | `Headers` | Заголовки ответа |
| `closed` | `bool` | Закрыто ли соединение |
| `raw` | `object` | Низкоуровневый объект (aiohttp.ClientWebSocketResponse) |

### Жизненный цикл

Поддерживает такие же хуки, как и `серверное WebSocketConnection`, включая `on_disconnect` и `on_error`:

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"Соединение разорвано: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"Ошибка соединения: {error}")
```

### Закрытие соединения

```python
await ws.close(code=1000, reason="Нормальное закрытие")
```

## Система исключений

ErisPulse определяет единый иерархический уровень исключений, при этом запросы, инициированные через `sdk.client`, автоматически преобразуют исключения aiohttp в исключения ErisPulse.

> **Обратная совместимость**: Старые модули/адаптеры, использующие напрямую `aiohttp.ClientSession`, остаются неизменными. Преобразование исключений действует только при запросах через `sdk.client`, при прямом использовании aiohttp код по-прежнему будет перехватывать исключения, такие как `aiohttp.ClientError`. Оба способа могут сосуществовать.

### Иерархия исключений

```
ErisPulseError
├── ClientError                  # Базовый класс для всех исключений HTTP/WS клиентских запросов
│   ├── ClientConnectionError    # Ошибка подключения (неудачное разрешение DNS, отказ в подключении, недоступность сети)
│   ├── ClientTimeoutError       # Ошибка таймаута подключения или запроса
│   └── HTTPStatusError          # Ошибка HTTP 4xx/5xx кода состояния
└── WebSocketError               # Базовый класс исключений WebSocket
    └── WebSocketDisconnect      # Отключение WebSocket (общее для клиента и сервера)
```

### Обработка исключений

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import (
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)

# Обработка исключений при HTTP-запросах
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("Невозможно подключиться к серверу")
except ClientTimeoutError:
    print("Запрос превысил лимит времени")
except ClientError as e:
    print(f"Запрос не удался: {e}")

# Обработка исключений при WebSocket
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"Соединение разорвано: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"Ошибка WebSocket: {e}")
```

### Общее перехватывание

Для общего перехвата всех исключений HTTP/WS клиентских запросов можно использовать `ClientError`:

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"Ошибка клиента: {e}")
```

### HTTPStatusError

Если нужно вручную проверить код состояния после запроса и выбросить исключение, можно использовать `HTTPStatusError`:

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## Использование в адаптере

Адаптер может использовать глобальный клиент или создать экземпляр клиента для отправки запросов к API платформы:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.errors import ClientError

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        try:
            resp = await client.post(
                f"https://api.platform.com/{endpoint}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return await resp.json()
        except ClientError as e:
            self.logger.error(f"Ошибка вызова API: {e}")
            raise
```

> Также можно использовать `sdk.client` через `from ErisPulse import sdk`, результат будет таким же.

## Рекомендации по лучшим практикам

1. **Предпочтение глобального клиента**: Используйте `from ErisPulse.Core import client` для получения глобального синглтона, что облегчает единое управление и мониторинг в рамках фреймворка
2. **Избегайте прямого импорта aiohttp**: Используйте `client` вместо `aiohttp.ClientSession`, чтобы в будущем, при смене базовой реализации, не пришлось изменять код. Старый код, использующий напрямую aiohttp, будет продолжать работать корректно, и оба способа могут сосуществовать
3. **Использование исключений ErisPulse**: При использовании `sdk.client` перехватывайте `ClientError`, а не `aiohttp.ClientError`, чтобы код не зависел от конкретной библиотеки HTTP. Старый код, использующий напрямую aiohttp, не будет затронут
4. **Разумная установка таймаутов**: Устанавливайте разумные значения таймаутов в зависимости от скорости ответа API, чтобы избежать длительных блокировок
5. **Использование механизма повтора запросов**: Включайте повтор запросов для нестабильных API, чтобы повысить надежность
6. **Мониторинг статистики запросов**: Мониторинг состояния запросов осуществляется через `sdk.client.stats` или события жизненного цикла `client.request`
7. **Использование WebSocket с помощью высоконадежных методов**: Предпочтение следует отдавать высоконадежным методам, таким как `iter_text` / `iter_json`, и использовать `iter_messages` только в том случае, если требуется различать типы сообщений

## Связанные документы

- [Менеджер маршрутизации](router.md) - HTTP/WebSocket серверные маршруты (серверное WebSocketConnection и клиент разделяют один и тот же базовый класс)
- [Руководство по разработке адаптеров](../developer-guide/adapters/getting-started.md) - Использование HTTP-клиентов в адаптерах
- [Управление жизненным циклом](lifecycle.md) - Наблюдение за событиями запросов

## 路由

> 来源: `docs/ru/advanced/router.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ru/advanced/router.md）

# Маршрутизатор

> [!TIP]
> **Когда нужно читать**: при необходимости маршрутизации HTTP / WebSocket / SSE (включая трансляцию в пуле соединений). Если не нужно — пропустите, это не повлияет на использование других функций.

Маршрутизатор ErisPulse обеспечивает единое управление маршрутизацией HTTP и WebSocket, поддерживает регистрацию маршрутов и управление жизненным циклом с помощью нескольких адаптеров. В основе лежит абстрактный слой (в настоящее время FastAPI + Uvicorn).

## Обзор

Основные функции маршрутизатора:

- **Декораторы маршрутизации**: поддержка декораторов `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` для быстрой регистрации
- **Автоматическая инъекция**: обработчики маршрутов не требуют импорта типов FastAPI, фреймворк автоматически инжектирует абстрактные объекты
- **Группировка маршрутов**: поддержка `RouteGroup` с префиксом и номером версии
- **Промежуточные обработчики маршрутов**: поддержка глобального шаблонного сопоставления запросов
- **Ограничение скорости**: встроенный алгоритм скользящего окна
- **Поддержка CORS**: включение кросс-доменных ресурсов одним кликом
- **Безопасные заголовки**: автоматическое добавление заголовков безопасности
- **Автоматическая документация**: интерактивная документация на основе OpenAPI
- **Поддержка WebSocket**: полное управление подключениями WebSocket, пользовательская аутентификация и хуки жизненного цикла
- **Интеграция жизненного цикла**: глубокая интеграция с системой жизненного цикла ErisPulse
- **Поддержка SSL/TLS**: поддержка безопасных подключений HTTPS и WSS
- **Главная страница**: поддержка быстрых кнопок входа модулей по корневому маршруту `/`, поддержка локализации

## Абстрактные типы

ErisPulse предоставляет абстрактные типы сервера, чтобы модули не зависели напрямую от FastAPI:

| Абстрактный тип | Соответствие FastAPI | Описание |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | Обёртка для HTTP-запроса, интерфейс полностью совместим |
| `WebSocketConnection` | `fastapi.WebSocket` | Обёртка для WebSocket-соединения, дополнительно предоставляет хуки жизненного цикла |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | Исключение разрыва WebSocket-соединения |

> `WebSocketConnection` наследуется от `WebSocketConnectionBase` и разделяет с клиентским WebSocket (`ClientWebSocket`) одинаковые интерфейсы send/receive/iter/close. Клиентский и серверный WebSocket могут использовать одинаковый код бизнес-логики.
>
> Через свойство `.raw` можно получить доступ к базовому объекту FastAPI. Код, использующий типы FastAPI напрямую, также полностью совместим.

## Декораторы маршрутизации (рекомендуется)

### Регистрация: одинарный параметр (рекомендуется) и двойной параметр

Декораторы маршрутизации поддерживают два варианта, **рекомендуется одинарный параметр** — согласуется с триггерами команд / событий, пространство имён автоматически присваивается текущему модулю:

```python
from ErisPulse import router

# Одинарный параметр (рекомендуется): автоматически присваивается модуль/имя/hello → фактический путь /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# Одинарный WebSocket: @ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# Двойной параметр: явно указать имя модуля (правила не меняются, используется при регистрации между модулями/инструментальным кодом)
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> Одинарный параметр требует регистрации в контексте загрузки модуля/адаптера (фреймворк уже инжектирует принадлежность во время загрузки);
> Вызов вне контекста принадлежности вызовет `ValueError` с указанием необходимости явного указания имени модуля.

### HTTP-декораторы

```python
from ErisPulse import router, HttpRequest

# Можно также явно указать абстрактный тип
@router.post("/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **Правила автоматической инъекции**: когда первый параметр обработчика называется `request` или `req` и не имеет аннотации типа FastAPI, фреймворк автоматически инжектирует `HttpRequest`. Обработчики без параметров или с параметрами, не являющимися запросом, не затрагиваются.

#### Соглашение о возвращаемых значениях (2.10+)

Возвращаемое значение обработчика поддерживает **соглашение о кортеже** (рекомендуемый способ, явно контролирует статус-код), dict/str/Response остаются прежними:

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "токен недействителен"}, 401
    # (body, status_code, headers) также можно добавить заголовки ответа
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# Или использовать вспомогательную функцию respond() (сообщение автоматически объединяется в тело ответа)
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

Параметры пути / запроса можно использовать напрямую с аннотациями FastAPI (например, `item_id: int` или `page: int = 1`), промежуточные обработчики см. в разделе [Промежуточные обработчики маршрутов](#промежуточные-обработчики-маршрутов).

### WebSocket-декораторы

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# Базовый WebSocket (одинарный параметр)
@router.ws("ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket с хуками жизненного цикла
@router.ws("/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"Пользователь отключился: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"Ошибка подключения: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket с аутентификацией
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **Важно**: обработчики WebSocket и аутентификации также поддерживают автоматическую инъекцию. Без аннотации параметра можно получить `WebSocketConnection`. Указание `fastapi.WebSocket` также может передать оригинальный объект, но рекомендуется использовать абстрактные типы.

### Автоматическая регистрация соединений (пул соединений, 2.10+)

Подключения, созданные с помощью `@ws` / `@sse`, **по умолчанию автоматически регистрируются** в пуле фреймворка (`track=False` отключает эту функцию):
внутри handler `ws.id` / `ws.join_group(...)` доступны, любые модули могут
`connections.list(namespace=...)` просматривать соединения текущего модуля, транслировать в группы.
См. [Пул соединений и трансляция](connections.md).

## Традиционный способ регистрации

```python
async def hello_handler(request):
    return {"message": "Hello World"}

# Базовая регистрация
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# С ограничением скорости и информацией о документации
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="Интерфейс данных",
    tags=["API"],
)
```

### Регистрация WebSocket

```python
from ErisPulse.Core import WebSocketConnection

async def websocket_handler(ws: WebSocketConnection):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# Базовая регистрация
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# Регистрация с аутентификацией (рекомендуется)
async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

**Описание параметров:**

| Параметр | Описание | Значение по умолчанию |
|------|------|--------|
| `module_name` | Имя модуля (обязательно) | - |
| `path` | Путь WebSocket | - |
| `handler` | Обработчик | - |
| `auth_handler` | Функция аутентификации, возвращает `False` автоматически закроет соединение | `None` |
| `auto_accept` | Автоматически ли вызывать `accept()` | `True` |

> **Рекомендуется**: использовать `auth_handler` для подтверждения соединения, а не отключать `auto_accept`. Только если вы хотите полностью контролировать процесс соединения, установите `auto_accept=False`.

## Хуки жизненного цикла WebSocket

`WebSocketConnection` предоставляет обратные вызовы для отключения и ошибок, без необходимости ручного try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Регистрация декоратором
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Причина отключения: {reason}")

    # Также можно вызывать напрямую
    async def on_err(ws, error=""):
        print(f"Ошибка: {error}")
    ws.on_error(on_err)

    # Обычная бизнес-логика
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## Группировка маршрутов

```python
# Создание маршрутов с префиксом
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# Фактический путь: /my_module/v1/users
```

## Промежуточные обработчики маршрутов

Промежуточные обработчики поддерживают шаблоны сопоставления путей:

```python
@router.middleware("/my_module/*")
async def auth_middleware(request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    return await call_next(request)

@router.middleware("/my_module/admin/*")
async def admin_middleware(request, call_next):
    return await call_next(request)
```

## Идентификатор запроса (X-Request-ID)

Начиная с версии 2.7.0, каждый HTTP-запрос будет содержать идентификатор `X-Request-ID`, используемый для логирования / трассировки цепочки:

- **Правила генерации**: приоритетно используется `X-Request-ID` из заголовка запроса клиента (для распределённой трассировки); в противном случае генерируется UUID
- **Заголовок ответа**: ответ будет возвращать `X-Request-ID`, что позволяет клиенту сопоставить запрос с логами
- **События жизненного цикла**: в данных событий `server.request` и `server.response` добавлено поле `request_id`

```python
# В модуле прослушивание событий запроса, по request_id сопоставляются запрос-ответ
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

Клиент может задать собственный ID для трассировки между сервисами:

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## Ограничение скорости

Использование алгоритма скользящего окна для ограничения скорости маршрутов:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Формат ограничения скорости: `{количество}/{временной интервал}`, например `10/minute`, `100/hour`.

## Настройка CORS

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Также можно настроить через `config.toml`:

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## Безопасные заголовки

```python
router.setup_security_headers()
```

Автоматически добавляются безопасные заголовки, такие как `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` и др.

Также можно настроить через `config.toml`:

```toml
[router.security]
enabled = true
```

## Автоматическая документация

Router по умолчанию включает интерактивную документацию OpenAPI:

```python
# Отключение документации
router.disable_docs()

# Настройка информации документации
router.set_docs_info(
    title="My API",
    description="API 文档",
    version="1.0.0"
)
```

## Обработка путей

Пути маршрутов автоматически добавляют префикс имени модуля, чтобы избежать конфликтов:

```python
# Регистрация пути "/api" в модуле "my_module"
# Фактический путь доступа: "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> Пути маршрутов (включая префикс имени модуля) **чувствительны к регистру**. При регистрации модульное имя каким регистром указано, таким и будет путь: при модульном имени `Test` путь `/api` будет `/Test/api`, обращение `/test/api` вернёт 404.

## Системные маршруты

Маршрутизатор автоматически предоставляет следующие системные маршруты:

### Проверка состояния

```
GET /health
# Возвращает:
{"status": "ok", "service": "ErisPulse Router"}
```

### Главная страница

```
GET /
# Возвращает страницу бренда ErisPulse
```

Главная страница `/` отображает страницу бренда ErisPulse, автоматически проверяет доступность Dashboard и добавляет кнопки входа.

## Главная кнопка

Маршрутизатор позволяет внешним модулям регистрировать кнопки быстрого входа на корневом маршруте `/`, что удобно для быстрого доступа к страницам управления модулями.

### Регистрация кнопки

```python
# Простая регистрация
router.register_home_entry(
    name="Моя панель",
    url="/mymodule/admin",
)

# Регистрация с иконкой (SVG)
router.register_home_entry(
    name="Консоль",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# Регистрация с поддержкой локализации (формат словаря i18n проекта)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "Моя панель"},
    url="/mymodule/admin",
)
```

**Описание параметров:**

| Параметр | Тип | Описание | Обязательно |
|------|------|------|------|
| `name` | `str` / `dict` | Текст кнопки; при передаче словаря `{"i18n": "key", "default": "текст"}` используется локализация | Да |
| `url` | `str` | Адрес ссылки кнопки | Да |
| `icon_svg` | `str` | Необязательный SVG-иконка | Нет |

### Автоматическая регистрация Dashboard

При обнаружении доступности `sdk.Dashboard` маршрутизатор автоматически добавляет кнопку Dashboard в начало списка входов, без необходимости ручной регистрации.

## Интеграция жизненного цикла

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"Сервер запущен: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("Сервер останавливается...")
```

## Лучшие практики

1. **Предпочтение абстрактных типов**: использовать `HttpRequest` / `WebSocketConnection` вместо `fastapi.Request` / `fastapi.WebSocket`, чтобы избежать жёсткой зависимости
2. **Использование автоматической инъекции**: первый параметр обработчика должен называться `request` или `req`, без аннотации типа FastAPI, чтобы получить `HttpRequest`
3. **Предпочтение одинарного параметра**: в контексте загрузки модуля предпочтительно одинарный параметр (автоматическое присвоение пространства имён); при регистрации между модулями/инструментальным кодом явно указывать имя модуля
4. **Использование группировки маршрутов**: использовать `group()` для организации нескольких маршрутов одного модуля
5. **Рассмотрение безопасности**: реализовать механизмы аутентификации и безопасные заголовки для чувствительных операций
6. **Разумное ограничение скорости**: установить ограничение скорости для частых интерфейсов
7. **Использование хуков жизненного цикла**: использовать `@ws.on_disconnect` / `@ws.on_error` для обработки ошибок WebSocket, избегая ручного try/catch

## Связанные документы

- [HTTP-клиент](http-client.md) - Использование встроенного HTTP-клиента для отправки запросов
- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) - Ознакомьтесь с регистрацией маршрутов модуля
- [Лучшие практики](../developer-guide/modules/best-practices.md) - Рекомендации по использованию маршрутов
