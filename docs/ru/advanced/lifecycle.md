# Управление жизненным циклом

ErisPulse предоставляет унифицированную систему хуков/управления жизненным циклом для мониторинга состояния работы различных компонентов системы, а также реализации расширенных функций, таких как аудит, статистика и пользовательская логика.

Система поддерживает три способа вызова:
- `await lifecycle.emit("event", data)` — упрощенная версия, передает произвольные данные
- `lifecycle.emit_sync("event", data)` — синхронная версия (для неасинхронных контекстов)
- `await lifecycle.submit_event("event", ...)` — совместима со старыми версиями, автоматически формирует стандартный формат события

## Механизм обработки событий

### Регистрация обработчиков

```python
from ErisPulse import sdk

# Декораторный паттерн
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"Модуль загружен: {data}")

# Программная регистрация
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# Отмена регистрации
sdk.lifecycle.unregister("module.load", on_module_load)
```

### Приоритет

Обработчики поддерживают параметр `priority`, чем больше значение, тем раньше выполняется (аналогично загрузчику модулей):

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # выполняется первым
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # выполняется позже
async def second_handler(data):
    pass
```

### События с точечной структурой

При срабатывании конкретного события также срабатывают его родительские события:
- При срабатывании `module.load` также срабатывает `module`
- При срабатывании `adapter.event.receive` также срабатывают `adapter.event` и `adapter`

### Шаблоны (Wildcard)

Регистрация `*` захватывает все события:

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"Получено событие: {data}")
```

## Обзор доступных точек хуков

Фреймворк включает в себя следующие точки расширения для хуков, пользователи могут прослушивать любые точки через `@sdk.lifecycle.on()` для реализации пользовательской логики.

### Инициализация ядра

| Имя хука | Время срабатывания | Данные |
|---------|-------------------|--------|
| `core.init.start` | Начало инициализации SDK | `{}` |
| `core.init.complete` | Завершение инициализации SDK | `{"duration": float, "success": bool, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(только при ошибке)}` |
| `core.uninit.complete` | Завершение деинициализации SDK | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(только при ошибке)}` |

### Изменения конфигурации

| Имя хука | Время срабатывания | Данные |
|---------|-------------------|--------|
| `config.set` | Параметр конфигурации изменен | `{"key": str, "old_value": Any, "new_value": Any}` |

**Пример: аудит конфигурации**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[Аудит] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### Жизненный цикл модулей

| Имя хука | Время срабатывания | Данные |
|---------|-------------------|--------|
| `module.register` | Класс модуля зарегистрирован в менеджере | `{"module_name": str, "success": bool}` |
| `module.load` | Модуль загружен (экземпляр создан успешно) | `{"module_name": str, "success": bool}` |
| `module.init` | Модуль инициализирован (включая ленивую загрузку) | `{"module_name": str, "success": bool}` |
| `module.unload` | Модуль выгружен | `{"module_name": str, "success": bool}` |

### Жизненный цикл адаптеров

| Имя хука | Время срабатывания | Данные |
|---------|-------------------|--------|
| `adapter.load` | Зарегистрирование адаптера завершено | `{"platform": str, "success": bool}` |
| `adapter.start` | Адаптер запущен | `{"platforms": [str]}` |
| `adapter.status.change` | Изменение состояния адаптера | `{"platform": str, "status": str, "retry_count": int, "error": str(только при ошибке)}` |
| `adapter.stop` | Адаптер остановлен | `{"platforms": [str]}` |
| `adapter.stopped` | Остановка адаптера завершена | `{"platforms": [str]}` |
| `adapter.bot.online` | Бот вышел в сеть | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Бот вышел из сети | `{"platform": str, "bot_id": str, "status": str}` |

### Получение и обработка событий

| Имя хука | Время срабатывания | Данные |
|---------|-------------------|--------|
| `adapter.event.receive` | Получено внешнее событие платформы (самое раннее) | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.dispatched` | Распределение события завершено | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | Перед началом выполнения обработчика событий | `{"event_type": str, "platform": str, "detail_type": str}` |

**Пример: подсчет событий**

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

| Имя хука | Время срабатывания | Данные |
|---------|-------------------|--------|
| `message.sending` | Сообщение скоро будет отправлено | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | Отправка сообщения завершена | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**Пример: аудит отправки сообщений**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[Отправка] -> {data['platform']}/{data['detail_type']}/{data['target_id']} через {data['method']}")
```

### Система команд

| Имя хука | Время срабатывания | Данные |
|---------|-------------------|--------|
| `command.matched` | Команда сопоставлена и скоро будет выполнена | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | Выполнение команды завершено | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(только при ошибке)}` |

**Пример: подсчет команд**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[Команда] /{data['command']} от {data['user_id']}@{data['platform']}")
```

### HTTP маршруты

| Имя хука | Время срабатывания | Данные |
|---------|-------------------|--------|
| `server.request` | Получение HTTP-запроса | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | Отправка HTTP-ответа | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**Пример: лог запроса**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| Имя хука | Время срабатывания | Данные |
|---------|-------------------|--------|
| `server.start` | Запуск маршрутизатора сервера | `{"base_url": str, "host": str, "port": int}` |
| `server.stop` | Остановка маршрутизатора сервера | `{}` |
| `server.websocket.connect` | Установление соединения WebSocket | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | Разрыв соединения WebSocket | `{"path": str, "module_name": str, "reason": str, "error": str(только при исключении)}` |

**Пример: мониторинг подключения WebSocket**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] Соединение: {data['path']} от {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] Отключение: {data['path']} ({data['reason']})")
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

## Полный справочник API

### Регистрация и отмена

| Метод | Описание |
|------|---------|
| `@lifecycle.on(event, *, priority=0)` | Декоратор для регистрации обработчика |
| `lifecycle.register(event, handler, *, priority=0)` | Программная регистрация |
| `lifecycle.unregister(event, handler=None)` | Отмена регистрации (если handler=None, отменяются все обработчики данного события) |

### Вызов

| Метод | Описание |
|------|---------|
| `await lifecycle.emit(event, data=None)` | Асинхронный вызов, если обработчик возвращает не None, значение модифицирует данные, передаваемые далее |
| `lifecycle.emit_sync(event, data=None)` | Синхронный вызов, асинхронные обработчики вызываются через create_task |
| `await lifecycle.submit_event(event_type, *, source, msg, data)` | Совместимо со старыми версиями, автоматически формирует стандартный формат события |

### Инструменты

| Метод | Описание |
|------|---------|
| `lifecycle.start_timer(timer_id)` | Запуск таймера |
| `lifecycle.get_duration(timer_id)` | Получение затраченного времени (в секундах) |
| `lifecycle.stop_timer(timer_id)` | Остановка таймера и возвращение затраченного времени |
| `lifecycle.list_hooks()` | Вывод списка всех зарегистрированных хуков и количества обработчиков |
| `lifecycle.clear()` | Очистка всех обработчиков и таймеров |

## Пример использования в модуле

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # Реализация простого подсчета сообщений
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

1. **Хэндлеры могут быть синхронными или асинхронными**: Система автоматически определяет тип и корректно вызывает их.
2. **Передача данных**: В режиме `emit()`, если обработчик возвращает не None, это значение изменяет данные, передаваемые следующим обработчикам.
3. **Соглашение об именовании событий**: Рекомендуется использовать точечную структуру именования событий для удобства родительского прослушивания.
4. **Изоляция ошибок**: Ошибки в одном обработчике не влияют на выполнение других обработчиков.
5. **Ограничения синхронного вызова**: В `emit_sync()` асинхронные обработчики вызываются методом fire-and-forget, значение возврата невозможно вернуть обратно.
6. **Очистка жизненного цикла**: При вызове `sdk.uninit()` все зарегистрированные обработчики и таймеры будут очищены.
7. **Приоритет загрузки**: Если требуется прослушивать события на этапе инициализации фреймворка, рекомендуется установить высокий приоритет и отключить ленивую загрузку.

## Связанные документы

- [Руководство по разработке модулей](../developer-guide/modules/getting-started.md) — Узнать о методах жизненного цикла модулей
- [Лучшие практики](../developer-guide/modules/best-practices.md) — Рекомендации по использованию событий жизненного цикла