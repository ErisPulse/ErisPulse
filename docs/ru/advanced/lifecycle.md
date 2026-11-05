# Управление жизненным циклом

> [!TIP]
> **Когда нужно читать эту статью**: когда необходимо подписаться на события жизненного цикла фреймворка (запуск / загрузка / изменение состояния). Если не нужно, пропустите, это не повлияет на использование других функций.

> **Что вы узнаете**: механизм регистрации / триггеров / направленной передачи событий жизненного цикла, различия и выбор между четырьмя наборами API триггеров, а также все предустановленные точки вставки хуков (core / module / adapter / server / message и т.д.), их форматы данных.
>
> **В этой статье не рассматривается**: методы жизненного цикла, которые модуль должен реализовать сам (`on_load` / `on_unload`, см. [Руководство по разработке модулей](../developer-guide/modules/getting-started.md)); подробности о стадиях запуска (см. [Последовательность запуска и ручное управление](startup.md)).

Если вы хотите получать уведомления о таких событиях, как сбой загрузки модуля, изменение конфигурации, отправка сообщения, выполнение команды, и выполнять собственную логику (аудит, статистика, оповещения, взаимодействие), просто подписывайтесь на события жизненного цикла фреймворка — фреймворк предустановил точки вставки хуков в каждом ключевом узле, и вы можете подключиться всего одной строкой `@sdk.lifecycle.on("имя_события")`. В конце статьи приведен полный список точек вставки.

Система поддерживает три способа триггеризации:
- `await lifecycle.emit("event", data)` — упрощённая версия, передача произвольных данных (`to="Owner"` для направленной доставки)
- `lifecycle.emit_sync("event", data)` — синхронная версия (для не-асинхронных контекстов)
- `await lifecycle.submit_event("event", ...)` — совместимость со старой версией, автоматическое построение стандартного формата события

## Механизм обработки событий

### Регистрация обработчиков

```python
from ErisPulse import sdk

# Декораторный способ
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"Модуль загружен: {data}")

# Программная регистрация
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# Отмена регистрации
sdk.lifecycle.unregister("module.load", on_module_load)

# Массовая отмена регистрации по владельцу (фреймворк автоматически вызывает при выгрузке модуля/адаптера)
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"Удалено {removed} хуков жизненного цикла")
```

### Приоритет

Обработчики поддерживают параметр `priority`, чем больше значение, тем раньше они выполняются (аналогично загрузчику модулей):

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # Выполняется первым
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # Выполняется позже
async def second_handler(data):
    pass
```

### События с точечной структурой

При триггере конкретного события также триггерятся его родительские события:
- При триггере `module.load` также триггерится `module`
- При триггере `adapter.event.receive` также триггерятся `adapter.event` и `adapter`

### Подстановочные знаки

Регистрация `*` ловит все события:

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"Получено событие: {data}")
```

### Направленная передача (emit to=)

> [!NOTE]
> Эта функция доступна в ErisPulse **2.8.0+**.

При указании параметра `to` в `emit()` событие переходит в режим направленной передачи: событие доставляется только обработчикам, зарегистрированным с этим владельцем (хуки, зарегистрированные в `on_load` модуля, автоматически принадлежат этому модулю), другие модули и обработчики с подстановочным знаком `*` не получают уведомления.

```python
# Отправитель: событие доставляется только хукам, зарегистрированным модулем Chat
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")

# Пользователь (внутри модуля Chat): регистрируем хук с тем же именем, owner автоматически записывается при регистрации
@sdk.lifecycle.on("message_received")
async def on_message_received(data): ...

@sdk.lifecycle.on("message")   # Префикс родительского события также действует (фильтруется по owner)
async def on_any(data): ...
```

- Если у целевого владельца нет зарегистрированных хуков → событие **не будет обработано** (можно заранее проверить с помощью `has_handlers()`)
- При `data` как dict автоматически добавляется `_trace_id` (не перезаписывает уже существующее значение)
- `emit_sync` / `submit_event` также поддерживают параметр `to=`
- Модульное взаимодействие в трехуровневой модели (RPC / направленная / широковещательная) см. в [Модульном взаимодействии](module-communication.md)

### Одноразовая регистрация (once)

Начиная с версии 2.7.0, обработчики, зарегистрированные через `lifecycle.once()`, автоматически отменяются после одного срабатывания, что подходит для одноразовых хуков, таких как "первичная готовность":

```python
@sdk.lifecycle.once("core.init.complete")
async def on_first_ready(data):
    print("Первичная готовность, дальнейшие срабатывания не будут происходить")
```

- Семантика параметра приоритета `priority` такая же, как у `on()`
- Автоматически отменяется, не нужно вручную `unregister`
- Поддерживает как синхронные, так и асинхронные обработчики

### Наблюдение за слушателями (has_handlers)

В сценариях с короткой цепочкой можно сначала использовать `has_handlers()` для проверки наличия слушателей, чтобы избежать ненужного перебора событий и планирования задач:

```python
if sdk.lifecycle.has_handlers("message.sending"):
    await sdk.lifecycle.emit("message.sending", send_ctx)
```

- Охватывает **точное имя события, подстановочный знак `*` и родительские события**
- Возвращает `False`, если нет слушателей, можно безопасно пропустить `emit`

## Список точек вставки хуков

Последовательность событий жизненного цикла, когда сообщение от платформы поступает в фреймворк и обрабатывается:

```mermaid
sequenceDiagram
    participant P as Платформа
    participant A as Адаптер
    participant F as Ядро фреймворка
    participant M as Обработчики модулей

    P->>A: Пришло исходное событие
    A->>F: adapter.event.receive (самый ранний)
    F->>F: event.pre_process (перед выполнением обработчиков)
    F->>M: Доставка обработчикам (команды/сообщения/уведомления и т.д.)
    M->>M: command.matched / command.executed
    M->>F: event.reply()
    F->>F: message.sending (перед отправкой)
    F->>A: SendDSL отправка
    A->>P: Отправка на платформу
    A->>F: message.sent (отправка завершена)
    F->>F: adapter.event.dispatched (доставка завершена)
```

Фреймворк включает следующие точки вставки хуков, которые можно прослушивать с помощью `@sdk.lifecycle.on()` для реализации пользовательской логики.

### Инициализация ядра

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `core.init.start` | Начало инициализации SDK | `{}` |
| `core.init.stage` | Начало инициализации на каждой стадии (выpusкается в фоне) | `{"stage": str}`, значения: `discovery` / `adapter_register` / `adapter_start` / `module_register` / `module_init` / `adapter_start_deferred` / `router_start` |
| `core.init.complete` | Завершение инициализации SDK | `{"duration": float, "success": bool, "stages": {stage: float}, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(только при неудаче)}` |
| `core.uninit.complete` | Завершение обратной инициализации SDK | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(только при неудаче)}` |

**Пример: отображение прогресса запуска**

```python
@sdk.lifecycle.on("core.init.stage")
def show_stage(data):
    print(f"[Запуск] Вход в стадию: {data['stage']}")
```

### Изменение конфигурации

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `config.set` | Изменение конфигурационного параметра | `{"key": str, "old_value": Any, "new_value": Any}` |
| `config.updated` | После изменения config.toml обнаружено изменение всей конфигурации | `{"old_config": dict, "new_config": dict, "config_file": str}` |

**Пример: аудит конфигурации**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[Аудит] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### Жизненный цикл модуля

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `module.register` | Регистрация класса модуля в менеджере | `{"module_name": str, "success": bool}` |
| `module.load` | Завершение загрузки модуля (успешное инстанцирование); в случае ошибки payload дополнительно содержит `"error": str, "traceback": str` (сцена ошибки также доступна через `module.last_error(имя)`) | `{"module_name": str, "success": bool}` |
| `module.init` | Завершение инициализации модуля (включая ленивую загрузку) | `{"module_name": str, "success": bool}` |
| `module.before_unload` | Первый шаг в цепочке выгрузки (до `on_unload` и освобождения ресурсов; хук экземпляра модуля `on_before_unload` также срабатывает синхронно) | `{"module_name": str, "reason": str}`; `reason` значения: `unload` / `reload` / `disable` / `cascade` / `dormant` |
| `module.sleep` | Завершение засыпания модуля (ленивая загрузка: ресурсы освобождены, при обращении автоматически пробуждается) | `{"module_name": str, "success": bool}` |
| `module.unload` | Выгрузка или отключение модуля (`disable` и `unload` равнозначны для уведомления зависимостей; контракт `on_dependency_lost` включает "отключение") | `{"module_name": str, "success": bool, "reason": str}`; `reason` значения: `unload` / `reload` / `disable` / `cascade` / `dormant` |
| `module.rollback` | Завершение отката после неудачной горячей перезагрузки (восстановление снапшота + повтор выполнения `on_load` старого экземпляра) | `{"module_name": str, "success": bool}`; `success` указывает, успешно ли повтор `on_load` (если `False`, старый экземпляр остаётся в завершённом состоянии) |
| `module.reload` | Завершение горячей перезагрузки модуля (включая повторную перезагрузку зависимостей) | `{"module_name": str, "success": bool, "full": bool, "duration_ms": int}`; для отдельного модуля дополнительно содержит `"identity_changed": bool` (`False` = в процессе может всё ещё выполняться старый код, например, кэш C-расширений) и `"version_old": str, "version_new": str`; при полной перезагрузке (`reload_all`) `module_name` = `"All"`, payload дополнительно содержит `"results": dict[str, bool]` |

> **Хук экземпляра модуля `on_before_unload`**: соответствующий метод жизненного цикла, связанный с событием `module.before_unload` — `event["reason"]` указывает причину, подходит для сохранения состояния в `sdk.storage` перед освобождением ресурсов, восстановление при пробуждении/перезагрузке происходит в `on_load` (состояние ленивой загрузки продолжается благодаря этому). Ошибка хука только предупреждает, не блокирует процесс выгрузки.

### Жизненный цикл адаптера

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `adapter.load` | Завершение регистрации адаптера | `{"platform": str, "success": bool}` |
| `adapter.reload` | Завершение горячей перезагрузки кода адаптера | `{"adapter_name": str, "success": bool, "full": bool, "duration_ms": int, "identity_changed": bool, "version_old": str, "version_new": str, "was_started": bool, "source": str}`; `identity_changed=False` = в процессе может всё ещё выполняться старый код |
| `adapter.start` | Запуск адаптера | `{"platforms": [str]}` |
| `adapter.status.change` | Изменение состояния адаптера | `{"platform": str, "status": str, "retry_count": int, "error": str(только при неудаче)}`; полные значения `status`: `starting` / `started` / `start_failed` / `stopping` / `stopped` / `stop_failed` / `skipped-dependency` / `disabled` |
| `adapter.stop` | Остановка адаптера | `{"platforms": [str]}` |
| `adapter.stopped` | Завершение остановки адаптера | `{"platforms": [str]}` |
| `adapter.bot.online` | Бот в сети | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Бот не в сети | `{"platform": str, "bot_id": str, "status": str}` |

### Прием и обработка событий

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `adapter.event.receive` | Получено событие от внешней платформы (самый ранний) | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.blocked` | Промежуточный слой отклонил событие (возврат `False`, событие отбрасывается и не поступает в обработчики) | `{"middleware": str, "platform": str, "event_type": str, "detail_type": str, "event": dict, "_trace_id": str}` |
| `adapter.event.dispatched` | Завершение доставки события | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | Начало выполнения обработчиков события | `{"event_type": str, "platform": str, "detail_type": str}` |

**Пример: статистика событий**

```python
event_counter = {}

@sdk.lifecycle.on("adapter.event.receive")
def count_events(data):
    platform = data["platform"]
    event_counter[platform] = event_counter.get(platform, 0) + 1

@sdk.lifecycle.on("adapter.event.dispatched")
def log_unhandled(data):
    if data["onebot_handlers_count"] == 0:
        print(f"[Необработано] {data['platform']}/{data['event_type']}")
```

### Отправка сообщений

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `message.sending` | Сообщение готово к отправке | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | Сообщение отправлено | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**Пример: аудит отправки сообщений**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[Отправка] -> {data['platform']}/{data['detail_type']}/{data['target_id']} через {data['method']}")
```

### Командная система

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `command.matched` | Команда сопоставлена и готова к выполнению | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | Команда выполнена | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(только при неудаче)}` |

**Пример: статистика команд**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[Команда] /{data['command']} от {data['user_id']}@{data['platform']}")
```

### HTTP-роутинг

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `server.request` | Получен HTTP-запрос | `{"method": str, "path": str, "client_ip": str, "request_id": str}` |
| `server.response` | Отправлен HTTP-ответ | `{"method": str, "path": str, "status_code": int, "client_ip": str, "request_id": str}` |

> `request_id` — это [идентификатор X-Request-ID](router.md#идентификатор-запроса-idx-request-id): приоритетно используется из заголовка клиента, иначе генерируется UUID, с его помощью можно связать событие запроса и ответа.

**Пример: логирование HTTP-запросов**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `server.start` | Запуск сервера маршрутизации | `{"base_url": str, "host": str, "port": int, "success": bool, "error": str(только при неудаче)}` |
| `server.stop` | Остановка сервера маршрутизации | `{}` |
| `server.websocket.connect` | Установлено WebSocket-соединение | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | Отключено WebSocket-соединение | `{"path": str, "module_name": str, "reason": str, "error": str(только при аномальном отключении)}` |

**Пример: мониторинг WebSocket-соединений**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] Подключение: {data['path']} от {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] Отключение: {data['path']} ({data['reason']})")
```

### Состояние подключения хранилища

Создание, сбой и восстановление пула подключений к хранилищу (все события происходят в фоне, не блокируют операции хранилища):

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `storage.ready` | Готовность пула подключений к хранилищу (первое успешное создание пула в цикле событий) | `{"backend": str}` |
| `storage.unreachable` | Повторные попытки подключения исчерпаны, вступает в силу период охлаждения (в течение которого операции быстро завершаются с ошибкой) | `{"backend": str, "error": str, "cooldown": float}` |
| `storage.recovered` | Охлаждение завершён, соединение восстановлено, хранилище снова доступно | `{"backend": str}` |

**Пример: оповещение о сбое хранилища**

```python
@sdk.lifecycle.on("storage.unreachable")
def alert_storage_down(data):
    print(f"[Оповещение] Хранилище {data['backend']} недоступно: {data['error']}, автоматическое переподключение через {data['cooldown']} секунд")

@sdk.lifecycle.on("storage.recovered")
def notify_storage_back(data):
    print(f"[Восстановление] Хранилище {data['backend']} снова доступно")
```

### HTTP-клиент

События запросов и подключений клиента `sdk.client` (все события происходят в фоне):

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `client.request.success` | HTTP-запрос выполнен успешно | `{"method": str, "url": str, "status": int, "elapsed": float}` |
| `client.request.failed` | HTTP-запрос не удался после исчерпания попыток | `{"method": str, "url": str, "error": str, "attempts": int, "elapsed": float}` |
| `client.ws.connect` | Установлено WebSocket-соединение | `{"url": str}` |

### Многоязычность

| Название хука | Время триггера | Данные |
|---------|---------|------|
| `i18n.language.changed` | Смена языка фреймворка (`i18n.set_language`) | `{"language": str, "previous": str}` |

## Стандартное определение событий

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.stage", "init.complete", "uninit.complete"],
    "module": ["load", "before_unload", "init", "sleep", "unload", "register", "reload"],
    "adapter": [
        "load", "start", "status.change", "reload", "stop", "stopped",
        "event.receive", "event.blocked", "event.dispatched",
        "bot.online", "bot.offline",
    ],
    "server": [
        "start", "stop",
        "request", "response",
        "websocket.connect", "websocket.disconnect",
    ],
    "event": ["pre_process"],
    "message": ["sending", "sent"],
    "command": ["matched", "executed"],
    "config": ["set", "updated"],
    "storage": ["ready", "unreachable", "recovered"],
    "client": ["request.success", "request.failed", "ws.connect"],
    "i18n": ["language.changed"],
}
```

## Полная справочная документация API

### Регистрация и отмена

| Метод | Описание |
|------|------|
| `@lifecycle.on(event, *, priority=0)` | Декораторная регистрация обработчика |
| `lifecycle.register(event, handler, *, priority=0)` | Программная регистрация |
| `lifecycle.unregister(event, handler=None)` | Отмена регистрации (если handler=None, отменяются все обработчики события) |

### Триггеризация

| Метод | Описание |
|------|------|
| `await lifecycle.emit(event, data=None, *, to=None)` | Асинхронный триггер, обработчики выполняются **параллельно** (взаимно не блокируются, возврат происходит после завершения всех), возвращаемое значение не None возвращается по цепочке с заменой data в порядке приоритета; `to` указывает владельца для направленной доставки |
| `lifecycle.fire(event, data=None, *, to=None)` | **Отправка в фоне (бросить в корзину)**: обработчики выполняются в фоновых задачах параллельно, без ожидания, без возврата; если нет слушателей, нулевые накладные расходы. Подходит для частых горячих путей и чистых наблюдений; для последовательных сценариев и последовательного потребления (например `config.set`) используйте `emit` |
| `lifecycle.emit_sync(event, data=None, *, to=None)` | Синхронный триггер, асинхронные обработчики запускаются через create_task |
| `await lifecycle.submit_event(event_type, *, source, msg, data, to=None, background=False)` | Совместимость со старой версией, автоматическое построение стандартного формата события; `background=True` использует `fire` для фоновой отправки |

**Сравнение четырех триггерных API**:

| Метод | Форма вызова | Ожидание завершения обработчиков | Типичные сценарии |
|------|---------|------------------|---------|
| `emit` | `await` (асинхронно) | **Ожидание** — обработчики выполняются параллельно, возврат происходит после завершения всех, возвращаемое значение возвращается по цепочке | Обычный триггер; последовательное потребление (например `config.set`) и цепочки остановки обязательно должны использовать его |
| `fire` | Прямой вызов (синхронный возврат) | **Не ожидание** — фоновые задачи выполняются параллельно, без возврата; если нет слушателей, нулевые накладные расходы | Частые горячие пути и чистые наблюдения (например `server.request` / `storage.ready`) |
| `emit_sync` | Прямой вызов (синхронно) | Синхронные обработчики завершаются немедленно; асинхронные обработчики запускаются через `create_task` (возвращаемое значение не может быть возвращено) | Триггер события в не-асинхронном контексте (синхронный код) |
| `submit_event` | `await` (асинхронно) | Ожидание (если `background=True`, то как `fire` не ожидает) | Совместимость со старой версией: автоматическое построение стандартного формата события (`source` / `msg` / `timestamp`) |

### Инструменты

| Метод | Описание |
|------|------|
| `lifecycle.start_timer(timer_id)` | Начать таймер |
| `lifecycle.get_duration(timer_id)` | Получить продолжительность (в секундах) |
| `lifecycle.stop_timer(timer_id)` | Остановить таймер и вернуть продолжительность |
| `lifecycle.list_hooks()` | Вывести все зарегистрированные хуки и количество обработчиков |
| `lifecycle.clear()` | Очистить все обработчики и таймеры |

## Пример использования в модуле

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # Реализация простой статистики сообщений
        self.msg_count = 0
        
        @sdk.lifecycle.on("adapter.event.receive")
        async def count(data):
            if data["event_type"] == "message":
                self.msg_count += 1
        
        # Мониторинг всех команд
        @sdk.lifecycle.on("command.matched")
        async def log_cmd(data):
            sdk.logger.info(f"Выполнение команды: /{data['command']} от {data['user_id']}")
        
        # Аудит изменений конфигурации
        @sdk.lifecycle.on("config.set")
        def audit(data):
            sdk.logger.info(f"Изменение конфигурации: {data['key']} = {data['new_value']}")
```

## Принадлежность фоновых задач и автоматическая отмена

> [!NOTE]
> Эта функция доступна в ErisPulse **2.8.0+**.

Фоновые задачи, созданные модулем, если не отменены в `on_unload`, будут удерживать ссылку на `self`, что приведёт к невозможности удаления экземпляра модуля (оставшиеся экземпляры после горячей перезагрузки). Фреймворк предоставляет следующие механизмы по умолчанию:

- **`self.spawn(coro)`** (рекомендуется использовать в модуле): задача автоматически принадлежит имени модуля, модуль отменяет не завершённые задачи после `on_unload` и записывает предупреждение
- **`spawn_background(coro)`** (в `ErisPulse.runtime`): автоматически захватывает текущее окружение `owner_scope`; `cancel_owner_tasks(owner)` отменяет задачи по принадлежности, `cancel_all_background_tasks()` используется для `sdk.uninit()` по умолчанию
- **Адаптеры**: при остановке отменяются фоновые задачи по имени платформы

```python
async def on_load(self, event):
    # Рекомендуется: фоновые задачи использовать self.spawn(), фреймворк автоматически отменяет по умолчанию
    self.spawn(self._poll())

async def on_unload(self, event):
    # В сценариях с тонким контролем всё равно рекомендуется отменить и дождаться завершения
    if self._poll_task:
        self._poll_task.cancel()
        await asyncio.gather(self._poll_task, return_exceptions=True)

async def _poll(self):
    while True:
        await asyncio.sleep(60)
        ...
```

> [!IMPORTANT]
> Фреймворк принудительно отменяет (`cancel_owner_tasks`), это происходит после возврата из `on_unload`. Поэтому задачи, требующие элегантного завершения (flush буфера, сохранение состояния, закрытие соединения), **должны** быть отменены и завершены в `on_unload` — не рассчитывайте на по умолчанию. Фреймворк гарантирует только «не оставлять задач, удерживающих `self»`, но не гарантирует «элегантность». Задачи, требующие `await` результата, следует вызывать напрямую, не бросать в фоновые задачи.

## Примечания

1. **Обработчики могут быть синхронными или асинхронными**: система автоматически распознаёт и правильно вызывает
2. **Передача данных**: в режиме `emit()`, если обработчик возвращает ненулевое значение, оно изменяет передаваемые последующим обработчикам данные
3. **Нормализация имен событий**: рекомендуется использовать точечную структуру для именования событий, что упрощает использование родительских слушателей
4. **Изоляция ошибок**: ошибка одного обработчика не влияет на выполнение других обработчиков
5. **Ограничение синхронного триггера**: в `emit_sync()` асинхронные обработчики запускаются в фоне без ожидания, возвращаемое значение не может быть возвращено
6. **Очистка жизненного цикла**: при вызове `sdk.uninit()` все зарегистрированные обработчики и таймеры будут очищены
7. **Приоритет загрузки**: если необходимо слушать события на этапе инициализации фреймворка, рекомендуется установить высокий приоритет и отключить ленивую загрузку

## Связанная документация

Выберите следующий шаг:

- **Хочу увидеть, как события проходят от адаптера до обработчика** → [Обзор архитектуры](../architecture.md)
- **Хочу узнать, какие методы жизненного цикла нужно реализовать при разработке модуля (on_load / on_unload)** → [Руководство по разработке модулей](../developer-guide/modules/getting-started.md)
- **Хочу обеспечить отмену фоновых задач и очистку ресурсов** → [Система принадлежности (owner)](ownership.md)
- **Хочу узнать о стадиях запуска (источники событий core.init.*)** → [Последовательность запуска и ручное управление](startup.md)
- **Хочу узнать рекомендации по использованию событий жизненного цикла** → [Лучшие практики модулей](../developer-guide/modules/best-practices.md)