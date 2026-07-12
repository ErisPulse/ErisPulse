# Управление жизненным циклом

ErisPulse предоставляет унифицированную систему хуков/жизненного цикла для мониторинга работоспособности различных компонентов системы, а также реализации таких расширяемых функций, как аудит, статистика, пользовательская логика и др.

Система поддерживает три способа триггера:
- `await lifecycle.emit("event", data)` — усеченная версия, передает произвольные данные
- `lifecycle.emit_sync("event", data)` — синхронная версия (для неасинхронных контекстов)
- `await lifecycle.submit_event("event", ...)` — совместима со старыми версиями, автоматически формирует стандартный формат события

## Механизм обработки событий

### Регистрация обработчиков

```python
from ErisPulse import sdk

# Декораторный режим
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"Загрузка модуля: {data}")

# Программная регистрация
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# Отмена регистрации
sdk.lifecycle.unregister("module.load", on_module_load)

# Массовая отмена регистрации по владельцу (вызывается автоматически при выгрузке модуля/адаптера)
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"Очищено {removed} хуков жизненного цикла")
```

### Приоритет

Обработчики поддерживают параметр `priority`, чем больше значение, тем раньше выполняется (согласовано с загрузчиком модулей):

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # Выполняется первым
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # Выполняется позже
async def second_handler(data):
    pass
```

### Иерархическая структура событий

При срабатывании конкретного события также срабатывает его родительское событие:
- При срабатывании `module.load` также срабатывает `module`
- При срабатывании `adapter.event.receive` также срабатывают `adapter.event` и `adapter`

### Шаблонная звезда (*)

Регистрация `*` перехватывает все события:

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"Получено событие: {data}")
```

## Обзор контрольных точек хуков

Внутри фреймворка реализованы следующие контрольные точки хуков, пользователи могут прослушивать любые точки через `@sdk.lifecycle.on()` для реализации пользовательской логики.

### Основная инициализация

| Название хука | Момент триггера | Данные |
|---------|---------|------|
| `core.init.start` | Начало инициализации SDK | `{}` |
| `core.init.complete` | Завершение инициализации SDK | `{"duration": float, "success": bool, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(только при ошибке)}` |
| `core.uninit.complete` | Завершение деинициализации SDK | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(только при ошибке)}` |

### Изменение конфигурации

| Название хука | Момент триггера | Данные |
|---------|---------|------|
| `config.set` | Конфигурация изменена | `{"key": str, "old_value": Any, "new_value": Any}` |

**Пример: аудит конфигурации**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[Аудит] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### Жизненный цикл модулей

| Название хука | Момент триггера | Данные |
|---------|---------|------|
| `module.register` | Регистрация класса модуля в менеджере | `{"module_name": str, "success": bool}` |
| `module.load` | Модуль загружен (успешный инстанцирование) | `{"module_name": str, "success": bool}` |
| `module.init` | Модуль инициализирован (включая ленивую загрузку) | `{"module_name": str, "success": bool}` |
| `module.unload` | Модуль выгружен | `{"module_name": str, "success": bool}` |

### Жизненный цикл адаптеров

| Название хука | Момент триггера | Данные |
|---------|---------|------|
| `adapter.load` | Адаптер зарегистрирован | `{"platform": str, "success": bool}` |
| `adapter.start` | Адаптер запущен | `{"platforms": [str]}` |
| `adapter.status.change` | Состояние адаптера изменилось | `{"platform": str, "status": str, "retry_count": int, "error": str(только при ошибке)}` |
| `adapter.stop` | Адаптер остановлен | `{"platforms": [str]}` |
| `adapter.stopped` | Остановка адаптера завершена | `{"platforms": [str]}` |
| `adapter.bot.online` | Бот в сети | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Бот офлайн | `{"platform": str, "bot_id": str, "status": str}` |

### Получение и обработка событий

| Название хука | Момент триггера | Данные |
|---------|---------|------|
| `adapter.event.receive` | Получено внешнее событие платформы (самое раннее) | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.dispatched` | Распределение события завершено | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | Перед началом выполнения обработчика событий | `{"event_type": str, "platform": str, "detail_type": str}` |

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
        print(f"[Не обработано] {data['platform']}/{data['event_type']}")
```

### Отправка сообщений

| Название хука | Момент триггера | Данные |
|---------|---------|------|
| `message.sending` | Сообщение отправляется | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | Отправка сообщения завершена | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**Пример: аудит отправки сообщений**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[Отправка] -> {data['platform']}/{data['detail_type']}/{data['target_id']} через {data['method']}")
```

### Командная система

| Название хука | Момент триггера | Данные |
|---------|---------|------|
| `command.matched` | Команда сопоставлена и будет выполнена | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | Выполнение команды завершено | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(только при ошибке)}` |

**Пример: статистика команд**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[Команда] /{data['command']} от {data['user_id']}@{data['platform']}")
```

### HTTP маршрутизация

| Название хука | Момент триггера | Данные |
|---------|---------|------|
| `server.request` | Получен HTTP запрос | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | Отправлен HTTP ответ | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**Пример: лог запроса**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| Название хука | Момент триггера | Данные |
|---------|---------|------|
| `server.start` | Запущен сервер маршрутизации | `{"base_url": str, "host": str, "port": int}` |
| `server.stop` | Сервер маршрутизации остановлен | `{}` |
| `server.websocket.connect` | Установлено WebSocket соединение | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket соединение разорвано | `{"path": str, "module_name": str, "reason": str, "error": str(только при исключении)}` |

**Пример: мониторинг WebSocket соединений**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] Соединение: {data['path']} от {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] Разрыв: {data['path']} ({data['reason']})")
```

## Определение стандартных событий

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.complete", "uninit.complete"],
    "module": ["load", "init", "unload", "register"],
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
    "config": ["set"],
}
```

## Полная справка по API

### Регистрация и отмена

| Метод | Описание |
|------|------|
| `@lifecycle.on(event, *, priority=0)` | Декоратор для регистрации обработчика |
| `lifecycle.register(event, handler, *, priority=0)` | Программная регистрация |
| `lifecycle.unregister(event, handler=None)` | Отмена регистрации (если handler=None, отменяются все обработчики для данного события) |

### Триггер

| Метод | Описание |
|------|------|
| `await lifecycle.emit(event, data=None)` | Асинхронный триггер, возвращаемое обработчиком значение, отличное от None, изменяет data |
| `lifecycle.emit_sync(event, data=None)` | Синхронный триггер, асинхронные обработчики запускаются через create_task |
| `await lifecycle.submit_event(event_type, *, source, msg, data)` | Совместимо со старыми версиями, автоматически формирует стандартный формат события |

### Инструменты

| Метод | Описание |
|------|------|
| `lifecycle.start_timer(timer_id)` | Запуск отсчета времени |
| `lifecycle.get_duration(timer_id)` | Получение прошедшего времени (в секундах) |
| `lifecycle.stop_timer(timer_id)` | Остановка отсчета и возвращение прошедшего времени |
| `lifecycle.list_hooks()` | Вывод списка всех зарегистрированных хуков и количества обработчиков |
| `lifecycle.clear()` | Очистка всех обработчиков и таймеров |

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

## Важные примечания

1. **Обработчики могут быть синхронными или асинхронными**: система автоматически определяет и корректно вызывает их
2. **Передача данных**: в режиме `emit()`, возвращаемое обработчиком значение, отличное от None, изменяет data, передаваемое последующим обработчикам
3. **Правила именования событий**: рекомендуется использовать иерархические (точечные) имена для событий для удобства использования прослушивания родительских событий
4. **Изоляция ошибок**: исключение в одном обработчике не влияет на выполнение других обработчиков
5. **Ограничения синхронного триггера**: в `emit_sync()` асинхронные обработчики запускаются в режиме fire-and-forget, возвращаемое значение невозможно вернуть обратно
6. **Очистка жизненного цикла**: при вызове `sdk.uninit()` будут очищены все зарегистрированные обработчики и таймеры
7. **Приоритет загрузки**: если необходимо отслеживать события на этапе инициализации фреймворка, рекомендуется установить высокий приоритет и отключить ленивую загрузку

## Связанные документы

- [Руководство разработчика модулей](../developer-guide/modules/getting-started.md) — ознакомьтесь с методами жизненного цикла модулей
- [Рекомендации по лучшим практикам](../developer-guide/modules/best-practices.md) — рекомендации по использованию событий жизненного цикла