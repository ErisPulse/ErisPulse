# Система API адаптеров

В этом документе подробно описывается API системы адаптеров ErisPulse.

## Менеджер адаптеров

### Получение адаптера

```python
from ErisPulse import sdk

# Получение адаптера по имени
adapter = sdk.adapter.get("platform_name")

# Или прямой доступ через свойство
adapter = sdk.adapter.platform_name
```

### Использование прослушивателей событий адаптера
> В общем случае рекомендуется использовать модуль `Event` для прослушивания/обработки событий;
>
> При этом модуль `Event` предоставляет мощные обертки, которые упрощают разработку ваших модулей

```python
# Прослушивание события OneBot12 стандартного формата
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Прослушивание стандартного события определённой платформы
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Прослушивание нативного события платформы
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### Управление адаптерами

```python
# Получение всех платформ
platforms = sdk.adapter.platforms

# Проверка существования адаптера
exists = sdk.adapter.exists("platform_name")

# Включение/отключение адаптера
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Запуск/остановка адаптера
# Ниже приведены примеры передачи параметров; без параметров запуск/остановка относятся ко всем зарегистрированным адаптерам
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Проверка, работает ли адаптер
is_running = sdk.adapter.is_running("platform_name")

# Перечисление всех работающих адаптеров
running = sdk.adapter.list_running()
```

## Middleware (промежуточное ПО)

Middleware выполняется до того, как события будут переданы обработчикам, что позволяет изменять, фильтровать или логировать данные событий.

### Регистрация middleware

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"Обработка middleware: {event}")
    return event
```

### Модель выполнения middleware

- **Порядок выполнения** : Middleware выполняются в порядке регистрации (первым исполняется зарегистрированный ранее).
- **Передача данных** : Каждому middleware передаются данные события, возвращённые предыдущим middleware; если middleware возвращает `None`, это значение игнорируется и сохраняются исходные данные для дальнейшей передачи (при этом выводится журнал уровня `warning`).
- **Изменение данных** : Middleware могут изменять данные события и возвращать изменённый словарь.

```python
@sdk.adapter.middleware
async def add_timestamp(event):
    event["processed_at"] = time.time()
    return event

@sdk.adapter.middleware
async def filter_spam(event):
    if event.get("detail_type") == "private":
        text = event.get("alt_message", "")
        if "спам" in text:  # "垃圾广告" -> "спам"
            return None   # Возврат None не предотвращает распространение события, лишь игнорирует это возвращаемое значение
    return event
```

> **Внимание** : Middleware в настоящее время не поддерживают阻断 распространения событий. Для фильтрации определённых событий реализуйте проверку условий внутри обработчиков событий.
> Однако вы можете настроить обработчики с высоким приоритетом в модуле Event и внутри обработчика использовать `event.mark_processed()` для блокировки обработки событий низкого приоритета.

## Отправка сообщений (Send)

### Базовая отправка

```python
# Получение адаптера
adapter = sdk.adapter.get("platform")

# Отправка текстового сообщения
await adapter.Send.To("user", "123").Text("Hello")

# Отправка изображения
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### Указание отправляющего аккаунта

```python
# Использование имени аккаунта
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Использование ID бота
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Запрос поддерживаемых методов отправки

```python
# Перечисление всех методов отправки, поддерживаемых платформой
methods = sdk.adapter.list_sends("onebot11")
# Возвращает: ["Text", "Image", "Voice", "Markdown", ...]

# Получение подробной информации о методе
info = sdk.adapter.send_info("onebot11", "Text")
# Возвращает:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "Отправить текстовое сообщение..."
# }
```

### Цепочка вызовов (Chain calls)

```python
# @ Пользователь
await adapter.Send.To("group", "456").At("789").Text("Привет")

# @ Всем участникам группы
await adapter.Send.To("group", "456").AtAll().Text("Всем привет")

# Ответ на сообщение
await adapter.Send.To("group", "456").Reply("msg_id").Text("Текст ответа")

# Комбинированное использование
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("Ответить на сообщение с упоминанием")
```

## Вызов API

### Метод call_api

> **Внимание** : `call_api` — это базовый метод для прямого вызова нативных API платформы. Параметры и возвращаемые значения могут отличаться в зависимости от платформы; обратитесь к документации адаптера соответствующей платформы. **Рекомендуется использовать Send DSL для отправки сообщений**; используйте `call_api` только в ситуациях, когда Send DSL не поддерживается (например, получение данных, специфичных для платформы, или вызов административных интерфейсов платформы).

```python
# Вызов API платформы
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# Стандартизированный ответ
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "msg_id",
    "message": "",
    "{platform}_raw": raw_response
}
```

## Базовый класс адаптера

### Методы BaseAdapter

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        # Инициализация адаптера
        pass
    
    async def start(self):
        """Запуск адаптера (обязательный к реализации)"""
        pass
    
    async def shutdown(self):
        """Остановка адаптера (обязательный к реализации)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Вызов API платформы (обязательный к реализации)"""
        pass
```

### Вложенный класс Send

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """Отправить текстовое сообщение"""
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
```

## Управление состоянием бота

Адаптеры уведомляют фреймворк о статусе соединения бота, отправляя события **`meta`** по стандарту OneBot12. Система автоматически извлекает информацию о боте для отслеживания состояния.

### Типы событий meta

Адаптеры должны отправлять следующие три события `meta`:

| `type` | `detail_type` | Описание | Срабатывание |
|--------|--------------|----------|--------------|
| `meta` | `connect` | Бот подключился | После успешного установления соединения адаптером с платформой |
| `meta` | `heartbeat` | Пульс бота | Отправляется регулярно (рекомендуется каждые 30-60 секунд) |
| `meta` | `disconnect` | Бот отключился | При обнаружении разрыва соединения |

### Расширение поля self

ErisPulse расширяет следующие необязательные поля в стандартном поле `self` OneBot12:

| Поле | Тип | Описание |
|------|------|----------|
| `self.platform` | string | Название платформы (стандарт OB12) |
| `self.user_id` | string | ID пользователя бота (стандарт OB12) |
| `self.user_name` | string | Никнейм бота (расширение ErisPulse) |
| `self.avatar` | string | URL аватара бота (расширение ErisPulse) |
| `self.account_id` | string | Идентификатор мультиаккаунта (расширение ErisPulse) |

### Формат событий meta

#### connect — Подключение

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345678,
    "type": "meta",
    "detail_type": "connect",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456",
        "user_name": "MyBot",
        "avatar": "https://example.com/avatar.jpg"
    },
    "telegram_raw": {...},
    "telegram_raw_type": "bot_connected"
})
```

Система: регистрирует бота, помечает как `online`, запускает жизненный цикл `adapter.bot.online`.

#### heartbeat — Пульс (Сердцебиение)

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345708,
    "type": "meta",
    "detail_type": "heartbeat",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456"
    }
})
```

Система: обновляет время `last_active` (обновление метаданных также поддерживается при пульсе).

#### disconnect — Отключение

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345738,
    "type": "meta",
    "detail_type": "disconnect",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456"
    }
})
```

Система: помечает бота как `offline`, запускает жизненный цикл `adapter.bot.offline`.

### Автоматическое обнаружение обычных событий

Помимо событий `meta`, поле `self` в обычных событиях (`message`/`notice`/`request`) также автоматически обнаруживается для регистрации бота и обновления времени активности. Это означает, что фреймворк сможет обнаружить бота даже из первого обычного события, если адаптер не отправляет событие `connect`.

### Пример интеграции адаптера

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # Установка соединения с платформой...
        connection = await self._connect()
        
        # Успешное подключение, отправка события connect
        await adapter.emit({
            "id": str(uuid4()),
            "time": int(time.time()),
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": self.bot_id,
                "user_name": self.bot_name,
                "avatar": self.bot_avatar
            },
            "myplatform_raw": raw_data,
            "myplatform_raw_type": "connected"
        })
    
    async def on_disconnect(self):
        # Отключение, отправка события disconnect
        await adapter.emit({
            "id": str(uuid4()),
            "time": int(time.time()),
            "type": "meta",
            "detail_type": "disconnect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": self.bot_id
            }
        })
```

### Запрос статуса бота

```python
# Получение полного статуса всех адаптеров и ботов (удобно для WebUI)
summary = sdk.adapter.get_status_summary()
# {
#     "adapters": {
#         "telegram": {
#             "status": "started",
#             "bots": {
#                 "123456": {
#                     "status": "online",
#                     "last_active": 1712345678.0,
#                     "info": {"nickname": "MyBot"}
#                 }
#             }
#         }
#     }
# }

# Перечисление всех ботов
all_bots = sdk.adapter.list_bots()

# Перечисление ботов определённой платформы
tg_bots = sdk.adapter.list_bots("telegram")

# Получение информации о конкретном боте
info = sdk.adapter.get_bot_info("telegram", "123456")

# Проверка, находится ли бот онлайн
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Бот онлайн")
```

### Значения статуса бота

| Статус | Описание |
|--------|----------|
| `online` | Онлайн (постоянно получает события или помечен адаптером) |
| `offline` | Офлайн (помечен адаптером или автоматически при остановке системы) |
| `unknown` | Неизвестен (зарегистрирован, но статус не подтверждён) |

### Жизненный цикл событий

| Имя события | Срабатывание | Данные |
|-------------|--------------|--------|
| `adapter.bot.online` | Первое автоматическое обнаружение нового бота | `{platform, bot_id, status}` |
| `adapter.status.change` | Изменение статуса адаптера (starting/started/stopping/stopped/stop_failed) | `{platform, status}` |

```python
# Прослушивание события включения бота
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Бот онлайн: {event['data']['platform']}/{event['data']['bot_id']}")

# Прослушивание изменения статуса адаптера
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"Статус адаптера: {event['data']['platform']} -> {event['data']['status']}")
```

> При закрытии системы (`shutdown`) все боты автоматически помечаются как `offline`.

## Связанные документы

- [API модулей ядра](core-modules.md) - API модулей ядра
- [API системы событий](event-system.md) - API модуля Event
- [Руководство по разработке адаптеров](../developer-guide/adapters/) - Разработка платформенных адаптеров