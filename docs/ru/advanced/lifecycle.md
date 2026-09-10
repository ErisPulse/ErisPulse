# Управление жизненным циклом

ErisPulse предоставляет единый систему хуков/жизненного цикла, предназначенную для мониторинга состояния работы различных компонентов системы, а также для реализации расширенных функций, таких как аудит, статистика и пользовательская логика.

Система поддерживает три способа запуска:
- `await lifecycle.emit("event", data)` — упрощённая версия, передача произвольных данных (направленная доставка при `to="Owner"`)
- `lifecycle.emit_sync("event", data)` — синхронная версия (используется в контекстах, не поддерживающих асинхронность)
- `await lifecycle.submit_event("event", ...)` — совместимая со старой версией, автоматическое построение стандартного формата события

## Механизм обработки событий

### Регистрация обработчиков

```python
from ErisPulse import sdk

# Регистрация через декоратор
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"Загрузка модуля: {data}")

# Регистрация через программный вызов
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# Отмена регистрации
sdk.lifecycle.unregister("module.load", on_module_load)

# Массовая отмена по владельцу (автоматически вызывается при выгрузке модуля/адаптера)
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"Удалено {removed} хуков жизненного цикла")
```

### Приоритеты

Обработчики поддерживают параметр `priority`, чем больше значение, тем раньше он будет выполнен (аналогично загрузчику модулей):

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # Выполняется первым
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # Выполняется позже
async def second_handler(data):
    pass
```

### События с точечной структурой

При срабатывании конкретного события также срабатывают его родительские события:
- Срабатывание `module.load` также вызывает `module`
- Срабатывание `adapter.event.receive` также вызывает `adapter.event` и `adapter`

### Шаблоны (wildcards)

Регистрация `*` позволяет поймать все события:

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"Получено событие: {data}")
```

### Направленная рассылка (emit to=)

> [!NOTE]
> Эта функция доступна начиная с ErisPulse **2.8.0+**.

При использовании параметра `to` в `emit()` происходит направленная рассылка: событие будет доставлено только тем обработчикам, которые зарегистрированы с указанным владельцем (хуки, зарегистрированные в `on_load` модуля, автоматически принадлежат этому модулю), остальные модули и обработчики с шаблоном `*` не получат событие.

```python
# Отправка: событие доставляется только хукам, зарегистрированным в модуле Chat
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")

# Подписка (внутри модуля Chat): регистрация хука с тем же именем, владелец автоматически сохраняется
@sdk.lifecycle.on("message_received")
async def on_message_received(data): ...

@sdk.lifecycle.on("message")   # Родительские префиксы также действуют (фильтрация по владельцу)
async def on_any(data): ...
```

- Если у целевого владельца нет зарегистрированных хуков → событие **тихо отбрасывается** (можно заранее проверить с помощью `has_handlers()`)
- При `data` в виде dict автоматически добавляется `_trace_id` (без перезаписи уже существующего значения)
- `emit_sync` / `submit_event` также поддерживают параметр `to=`
- Трехуровневая модель модульного взаимодействия (RPC / направленная / широковещательная) описана в [Модульное взаимодействие](module-communication.md)

### Однократная регистрация (once)

Начиная с версии 2.7.0, обработчики, зарегистрированные через `lifecycle.once()`, автоматически удаляются после первого срабатывания, что удобно для "одноразовых" хуков типа "первичная готовность":

```python
@sdk.lifecycle.once("core.init.complete")
async def on_first_ready(data):
    print("Первичная готовность, дальнейшие срабатывания не произойдут")
```

- Приоритет обработчиков определяется так же, как и в `on()` (`priority`, чем больше, тем раньше)
- Автоматическая отмена регистрации, без необходимости ручного вызова `unregister`
- Поддерживается как синхронные, так и асинхронные обработчики

### Проверка наличия слушателей (has_handlers)

Для оптимизации производительности, в критичных по времени участках кода можно сначала проверить наличие обработчиков с помощью `has_handlers()`, чтобы избежать ненужного перебора событий и запуска задач:

```python
if sdk.lifecycle.has_handlers("message.sending"):
    await sdk.lifecycle.emit("message.sending", send_ctx)
```

- Проверка охватывает три типа совпадений: точное имя события, шаблон `*`, родительские события
- Возвращает `False`, если слушателей нет, что позволяет безопасно пропустить `emit`

## Обзор точек остановки хука

Типичный порядок событий жизненного цикла сообщения от платформы до завершения обработки в рамках фреймворка:

```mermaid
sequenceDiagram
    participant P as Платформа
    participant A as Адаптер
    participant F as Ядро фреймворка
    participant M as Обработчик модуля

    P->>A: Прибытие исходного события
    A->>F: adapter.event.receive (самый ранний)
    F->>F: event.pre_process (перед выполнением обработчика)
    F->>M: Распределение к обработчику (команды/сообщения/уведомления и т.д.)
    M->>M: command.matched / command.executed
    M->>F: event.reply()
    F->>F: message.sending (перед отправкой)
    F->>A: SendDSL отправка
    A->>P: Отправка на платформу
    A->>F: message.sent (отправка завершена)
    F->>F: adapter.event.dispatched (распределение завершено)
```

Фреймворк содержит следующие точки остановки хука, которые пользователи могут прослушивать с помощью `@sdk.lifecycle.on()` для реализации пользовательской логики.

### Ядро инициализации

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `core.init.start` | Начало инициализации SDK | `{}` |
| `core.init.stage` | Начало этапа инициализации (выдается в фоновом режиме) | `{"stage": str}`, значения: `discovery` / `adapter_register` / `adapter_start` / `module_register` / `module_init` / `adapter_start_deferred` / `router_start` |
| `core.init.complete` | Завершение инициализации SDK | `{"duration": float, "success": bool, "stages": {stage: float}, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str (только при неудаче)}` |
| `core.uninit.complete` | Завершение обратной инициализации SDK | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str (только при неудаче)}` |

**Пример: отображение прогресса запуска**

```python
@sdk.lifecycle.on("core.init.stage")
def show_stage(data):
    print(f"[Запуск] Вход в этап: {data['stage']}")
```

### Изменение конфигурации

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `config.set` | Изменение параметра конфигурации | `{"key": str, "old_value": Any, "new_value": Any}` |
| `config.updated` | Обнаружено изменение всей конфигурации после редактирования config.toml | `{"old_config": dict, "new_config": dict, "config_file": str}` |

**Пример: аудит конфигурации**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[Аудит] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### Жизненный цикл модуля

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `module.register` | Регистрация класса модуля в менеджере | `{"module_name": str, "success": bool}` |
| `module.load` | Завершение загрузки модуля (успешное инстанцирование) | `{"module_name": str, "success": bool}` |
| `module.init` | Завершение инициализации модуля (включая ленивую загрузку) | `{"module_name": str, "success": bool}` |
| `module.unload` | Выгрузка модуля | `{"module_name": str, "success": bool}` |
| `module.reload` | Завершение горячей перезагрузки модуля (включая перезагрузку зависимостей) | `{"module_name": str, "success": bool}` |

### Жизненный цикл адаптера

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `adapter.load` | Завершение регистрации адаптера | `{"platform": str, "success": bool}` |
| `adapter.start` | Запуск адаптера | `{"platforms": [str]}` |
| `adapter.status.change` | Изменение состояния адаптера | `{"platform": str, "status": str, "retry_count": int, "error": str (только при неудаче)}` |
| `adapter.stop` | Остановка адаптера | `{"platforms": [str]}` |
| `adapter.stopped` | Завершение остановки адаптера | `{"platforms": [str]}` |
| `adapter.bot.online` | Онлайн бота | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Оффлайн бота | `{"platform": str, "bot_id": str, "status": str}` |

### Прием и обработка событий

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `adapter.event.receive` | Получение внешнего события платформы (самый ранний) | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.dispatched` | Завершение распределения события | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | Начало выполнения обработчика события | `{"event_type": str, "platform": str, "detail_type": str}` |

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

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `message.sending` | Сообщение готовится к отправке | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | Сообщение отправлено | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**Пример: аудит отправки сообщений**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[Отправка] -> {data['platform']}/{data['detail_type']}/{data['target_id']} через {data['method']}")
```

### Командная система

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `command.matched` | Команда сопоставлена и готова к выполнению | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | Команда выполнена | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str (только при неудаче)}` |

**Пример: статистика команд**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[Команда] /{data['command']} от {data['user_id']}@{data['platform']}")
```

### HTTP-маршрутизация

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `server.request` | Получение HTTP-запроса | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | Отправка HTTP-ответа | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**Пример: логирование HTTP-запросов**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `server.start` | Запуск маршрутизатора сервера | `{"base_url": str, "host": str, "port": int, "success": bool, "error": str (только при неудаче)}` |
| `server.stop` | Остановка маршрутизатора сервера | `{}` |
| `server.websocket.connect` | Установление WebSocket-соединения | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | Разрыв WebSocket-соединения | `{"path": str, "module_name": str, "reason": str, "error": str (только при аномалии)}` |

**Пример: мониторинг WebSocket-соединений**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] Подключение: {data['path']} от {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] Отключение: {data['path']} ({data['reason']})")
```

### Состояние подключения к хранилищу

Создание, сбой и восстановление пула подключений к хранилищу (все события происходят в фоновом режиме, не блокируют операции хранилища):

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `storage.ready` | Пул подключений к хранилищу готов (первое успешное создание пула в каждом цикле событий) | `{"backend": str}` |
| `storage.unreachable` | Повторные попытки подключения исчерпаны, вступает период охлаждения (в течение которого операции завершаются мгновенно с ошибкой) | `{"backend": str, "error": str, "cooldown": float}` |
| `storage.recovered` | Период охлаждения завершен, повторное подключение успешно, хранилище снова доступно | `{"backend": str}` |

**Пример: оповещение о сбое хранилища**

```python
@sdk.lifecycle.on("storage.unreachable")
def alert_storage_down(data):
    print(f"[Предупреждение] Хранилище {data['backend']} недоступно: {data['error']}, автоматическое переподключение через {data['cooldown']} секунд")

@sdk.lifecycle.on("storage.recovered")
def notify_storage_back(data):
    print(f"[Восстановление] Хранилище {data['backend']} снова доступно")
```

### HTTP-клиент

События запросов и подключений `sdk.client` (все события происходят в фоновом режиме):

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `client.request.success` | Успешный HTTP-запрос | `{"method": str, "url": str, "status": int, "elapsed": float}` |
| `client.request.failed` | HTTP-запрос неудачен после исчерпания попыток повтора | `{"method": str, "url": str, "error": str, "attempts": int, "elapsed": float}` |
| `client.ws.connect` | Установление WebSocket-соединения | `{"url": str}` |

### Межкультурная локализация

| Имя хука | Точка остановки | Данные |
|---------|---------|------|
| `i18n.language.changed` | Смена языка фреймворка (через `i18n.set_language`) | `{"language": str, "previous": str}` |

## Определение стандартных событий

```python
СТАНДАРТНЫЕ_СОБЫТИЯ = {
    "core": ["init.start", "init.stage", "init.complete", "uninit.complete"],
    "module": ["load", "init", "unload", "register", "reload"],
    "adapter": [
        "load", "start", "status.change", "stop", "stopped",
        "event.receive", "event.dispatched",
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
| `@lifecycle.on(event, *, priority=0)` | Декоратор для регистрации обработчика |
| `lifecycle.register(event, handler, *, priority=0)` | Программная регистрация |
| `lifecycle.unregister(event, handler=None)` | Отмена регистрации (если `handler=None`, отменяются все обработчики события) |

### Вызов

| Метод | Описание |
|------|------|
| `await lifecycle.emit(event, data=None, *, to=None)` | Асинхронный вызов, обработчики выполняются **параллельно** (не блокируются друг другом, возвращаются, когда все завершены), возвращаемые значения не None возвращаются по приоритету в виде цепочки замены `data`; `to` указывает `owner` для направленной доставки |
| `lifecycle.fire(event, data=None, *, to=None)` | **Фоновый вызов (бросил в ведро и ушел)**: обработчики выполняются в фоновых задачах параллельно, без ожидания, без возвращаемого значения; при отсутствии слушателей нулевые накладные расходы. Подходит для частых горячих путей и чисто наблюдаемых событий; для последовательных и чувствительных к порядку потребителей (например, `config.set`) используйте `emit` |
| `lifecycle.emit_sync(event, data=None, *, to=None)` | Синхронный вызов, асинхронные обработчики планируются с помощью `create_task` |
| `await lifecycle.submit_event(event_type, *, source, msg, data, to=None, background=False)` | Совместимость со старой версией, автоматически строит стандартный формат события; при `background=True` используется фоновый вызов `fire` |

### Инструменты

| Метод | Описание |
|------|------|
| `lifecycle.start_timer(timer_id)` | Начать отсчет времени |
| `lifecycle.get_duration(timer_id)` | Получить прошедшее время (в секундах) |
| `lifecycle.stop_timer(timer_id)` | Остановить отсчет времени и вернуть прошедшее время |
| `lifecycle.list_hooks()` | Вывести список всех зарегистрированных хуков и количество обработчиков |
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
            sdk.logger.info(f"Команда выполнена: /{data['command']} от {data['user_id']}")
        
        # Аудит изменений конфигурации
        @sdk.lifecycle.on("config.set")
        def audit(data):
            sdk.logger.info(f"Изменение конфигурации: {data['key']} = {data['new_value']}")
```

## Принадлежность и автоматическое отмена фоновых задач

> [!NOTE]
> Эта функция доступна в ErisPulse **2.8.0+**.

Фоновые задачи asyncio, созданные модулем, если не отменены в `on_unload`, будут удерживать ссылку на `self`, что мешает сборке мусора для экземпляра модуля (старые экземпляры остаются после горячей перезагрузки). Рамка предоставляет следующие механизмы по умолчанию:

- **`self.spawn(coro)`** (рекомендуется в модуле): задача автоматически присваивается имени модуля, и при выгрузке модуля рамка в `on_unload` **после** отменяет неоконченные задачи и записывает предупреждение
- **`spawn_background(coro)`** (`ErisPulse.runtime`): автоматически захватывает текущий контекст `owner_scope`; `cancel_owner_tasks(owner)` отменяет задачи по принадлежности, `cancel_all_background_tasks()` используется для `sdk.uninit()` по умолчанию
- **Адаптеры**: при закрытии адаптера также отменяются фоновые задачи, принадлежащие имени платформы

```python
async def on_load(self, event):
    # Рекомендуется: фоновые задачи использовать self.spawn(), при выгрузке рамка автоматически отменяет
    self.spawn(self._poll())

async def on_unload(self, event):
    # В сценариях с тонкой настройкой по-прежнему рекомендуется отменить и дождаться завершения
    if self._poll_task:
        self._poll_task.cancel()
        await asyncio.gather(self._poll_task, return_exceptions=True)

async def _poll(self):
    while True:
        await asyncio.sleep(60)
        ...
```

> [!IMPORTANT]
> Рамка по умолчанию **принудительно отменяет** задачи (`cancel_owner_tasks`), это происходит после возврата из `on_unload`. Поэтому задачи, требующие аккуратного завершения (очистка буфера, сохранение состояния, закрытие соединений), **обязательно** должны быть отменены и завершены в `on_unload` — не рассчитывайте, что по умолчанию сохранится логика завершения. Рамка гарантирует только «отсутствие задач, удерживающих `self»`, но не «аккуратное» завершение. Задачи, требующие `await` результата, следует вызывать напрямую `await`, а не передавать в фоновую задачу.

## Примечания

1. **Обработчики могут быть синхронными или асинхронными**: система автоматически определяет и правильно вызывает их
2. **Передача данных**: в режиме `emit()`, если обработчик возвращает значение, отличное от None, это изменит данные, передаваемые следующим обработчикам
3. **Нормы именования событий**: рекомендуется использовать точечную структуру для именования событий, что упрощает использование родительских слушателей
4. **Изоляция ошибок**: исключение в одном обработчике не влияет на выполнение других обработчиков
5. **Ограничения синхронного триггера**: в `emit_sync()` асинхронные обработчики запускаются в режиме fire-and-forget, и возвращаемые значения не могут быть переданы обратно
6. **Очистка жизненного цикла**: при вызове `sdk.uninit()` все зарегистрированные обработчики и таймеры будут очищены
7. **Приоритет загрузки**: если необходимо слушать события на этапе инициализации фреймворка, рекомендуется установить высокий приоритет и отключить ленивую загрузку

## Связанные документы

- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) - Ознакомьтесь с методами жизненного цикла модуля
- [Рекомендуемые практики](../developer-guide/modules/best-practices.md) - Советы по использованию событий жизненного цикла