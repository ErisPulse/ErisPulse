# Управление жизненным циклом

ErisPulse предоставляет единую систему перехватчиков/жизненного цикла для мониторинга статуса выполнения компонентов системы, а также реализации таких функций расширения, как аудит, статистика и кастомная логика.

Система поддерживает три способа триггерации:
- `await lifecycle.emit("event", data)` — упрощенная версия, принимает произвольные данные
- `lifecycle.emit_sync("event", data)` — синхронная версия (для неасинхронных контекстов)
- `await lifecycle.submit_event("event", ...)` — совместима с предыдущими версиями, автоматически формирует стандартный формат события

## Механизм обработки событий

### Регистрация обработчиков

```python
from ErisPulse import sdk

# Декораторный режим
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"Модуль загружен: {data}")

# Программная регистрация
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# Отмена регистрации
sdk.lifecycle.unregister("module.load", on_module_load)

# Массовая отмена регистрации по владельцу (вызывается автоматически при выгрузке адаптера/модуля)
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"Очищено {removed} жизненных циклов-перехватчиков")
```

### Приоритет

Обработчики поддерживают параметр `priority`, чем больше значение, тем раньше выполняется обработчик (совпадает с логикой загрузчика модулей):

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # Выполнится первым
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # Выполнится вторым
async def second_handler(data):
    pass
```

### События по точечной структуре

При запуске конкретного события также запускаются родительские события:
- При срабатывании `module.load` также срабатывает `module`
- При срабатывании `adapter.event.receive` также срабатывают `adapter.event` и `adapter`

### Подстановочные знаки

Регистрация `*` перехватывает все события:

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"Получено событие: {data}")
```

### Одноразовая регистрация (once)

Начиная с версии 2.7.0, обработчики, зарегистрированные через `lifecycle.once()`, автоматически удаляются после **одного срабатывания**, что подходит для одноразовых хуков, таких как "первая готовность":

```python
@sdk.lifecycle.once("core.init.complete")
async def on_first_ready(data):
    print("Первая готовность, больше не срабатывает")
```

- Имеет тот же смысл параметра приоритета, что и у `on()` (чем больше значение, тем раньше выполняется)
- Автоматическое удаление, ручное `unregister` не требуется
- Поддерживаются как синхронные, так и асинхронные обработчики

### Запрос обработчиков (has_handlers)

В критических сценариях можно сначала использовать `has_handlers()`, чтобы проверить наличие слушателей, избегая ненужного перебора событий и планирования задач:

```python
if sdk.lifecycle.has_handlers("message.sending"):
    await sdk.lifecycle.emit("message.sending", send_ctx)
```

- Охватывает **точное имя события, подстановочный знак `*`, а также родительские события**
- Возвращает `False`, если нет никаких слушателей, можно безопасно пропустить `emit`

## Обзор точек останова перехватчиков

Фреймворк включает следующие точки останова перехватчиков, пользователи могут отслеживать любую точку с помощью `@sdk.lifecycle.on()` для реализации кастомной логики.

### Инициализация ядра

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `core.init.start` | Начало инициализации SDK | `{}` |
| `core.init.complete` | Завершение инициализации SDK | `{"duration": float, "success": bool, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(только при ошибке)}` |
| `core.uninit.complete` | Завершение деинициализации SDK | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(только при ошибке)}` |

### Изменения конфигурации

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `config.set` | Конфигурационный элемент был изменен | `{"key": str, "old_value": Any, "new_value": Any}` |

**Пример: аудит конфигурации**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[Аудит] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### Жизненный цикл модулей

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `module.register` | Класс модуля зарегистрирован в менеджере | `{"module_name": str, "success": bool}` |
| `module.load` | Модуль загружен (экземпляр создан успешно) | `{"module_name": str, "success": bool}` |
| `module.init` | Модуль инициализирован (включая отложенную загрузку) | `{"module_name": str, "success": bool}` |
| `module.unload` | Модуль выгружен | `{"module_name": str, "success": bool}` |

### Жизненный цикл адаптеров

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `adapter.load` | Зарегистрирование адаптера завершено | `{"platform": str, "success": bool}` |
| `adapter.start` | Запуск адаптера | `{"platforms": [str]}` |
| `adapter.status.change` | Изменение статуса адаптера | `{"platform": str, "status": str, "retry_count": int, "error": str(только при ошибке)}` |
| `adapter.stop` | Остановка адаптера | `{"platforms": [str]}` |
| `adapter.stopped` | Остановка адаптера завершена | `{"platforms": [str]}` |
| `adapter.bot.online` | Бот онлайн | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Бот оффлайн | `{"platform": str, "bot_id": str, "status": str}` |

### Получение и обработка событий

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `adapter.event.receive` | Получено внешнее платформенное событие (раньше всех) | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.dispatched` | Распределение события завершено | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | Перед выполнением обработчика событий | `{"event_type": str, "platform": str, "detail_type": str}` |

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

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `message.sending` | Сообщение скоро будет отправлено | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | Отправка сообщения завершена | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**Пример: аудит отправки сообщений**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[Отправка] -> {data['platform']}/{data['detail_type']}/{data['target_id']} через {data['method']}")
```

### Командная система

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `command.matched` | Команда сопоставлена и скоро будет выполнена | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | Выполнение команды завершено | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(только при ошибке)}` |

**Пример: статистика команд**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[Команда] /{data['command']} от {data['user_id']}@{data['platform']}")
```

### HTTP маршрутизация

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `server.request` | Получен HTTP запрос | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | Отправлен HTTP ответ | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**Пример: лог запросов**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `server.start` | Запуск маршрутизационного сервера | `{"base_url": str, "host": str, "port": int}` |
| `server.stop` | Остановка маршрутизационного сервера | `{}` |
| `server.websocket.connect` | Установлено WebSocket соединение | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket соединение разорвано | `{"path": str, "module_name": str, "reason": str, "error": str(только при исключении)}` |

**Пример: мониторинг WebSocket соединений**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] Подключение: {data['path']} от {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] Отключение: {data['path']} ({data['reason']})")
```

## Определения стандартных событий

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
| `lifecycle.unregister(event, handler=None)` | Отмена регистрации (при handler=None отменяются все обработчики события) |

### Триггеринг

| Метод | Описание |
|------|------|
| `await lifecycle.emit(event, data=None)` | Асинхронный триггер, возвращаемое обработчиком значение не None изменяет data для последующих обработчиков |
| `lifecycle.emit_sync(event, data=None)` | Синхронный триггер, асинхронные обработчики запускаются через create_task |
| `await lifecycle.submit_event(event_type, *, source, msg, data)` | Совместимо с предыдущими версиями, автоматически формирует стандартный формат события |

### Инструменты

| Метод | Описание |
|------|------|
| `lifecycle.start_timer(timer_id)` | Запуск таймера |
| `lifecycle.get_duration(timer_id)` | Получение прошедшего времени (секунды) |
| `lifecycle.stop_timer(timer_id)` | Остановка таймера и возвращение прошедшего времени |
| `lifecycle.list_hooks()` | Вывод списка всех зарегистрированных перехватчиков и количества обработчиков |
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

1. **Обработчики могут быть синхронными или асинхронными**: система автоматически определяет тип и корректно вызывает
2. **Передача данных**: в режиме `emit()`, возвращаемое обработчиком значение не None изменяет `data`, передаваемую в последующие обработчики
3. **Номенклатура событий**: рекомендуется использовать точечную структуру именования событий для удобства использования родительских слушателей
4. **Изоляция ошибок**: исключение в одном обработчике не влияет на выполнение других обработчиков
5. **Ограничения синхронного триггера**: в `emit_sync()` асинхронные обработчики запускаются методом fire-and-forget, возвращаемое значение невозможно получить
6. **Очистка жизненного цикла**: при вызове `sdk.uninit()` все зарегистрированные обработчики и таймеры будут очищены
7. **Приоритет загрузки**: если необходимо прослушивать события на этапе инициализации фреймворка, рекомендуется установить высокий приоритет и отключить отложенную загрузку

## Связанные документы

- [Руководство разработчика модулей](../developer-guide/modules/getting-started.md) — Узнать о методах жизненного цикла модуля
- [Рекомендации по лучшим практикам](../developer-guide/modules/best-practices.md) — Рекомендации по использованию событий жизненного цикла