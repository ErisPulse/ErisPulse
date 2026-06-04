# API адаптерной системы

В этом документе подробно описывается API системы адаптеров ErisPulse.

## Менеджер адаптеров

### Получение адаптера

```python
from ErisPulse import sdk

# Получить адаптер по имени
adapter = sdk.adapter.get("platform_name")

# Или получить доступ через свойство
adapter = sdk.adapter.platform_name
```

### Слушание событий адаптера
> В общем случае рекомендуется использовать модуль `Event` для прослушивания/обработки событий;
>
> Модуль `Event` также предоставляет мощные обертки, которые могут принести больше удобства при разработке ваших модулей

```python
# Слушать события стандарта OneBot12
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Слушать стандартные события определенной платформы
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Слушать нативные события платформы
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### Управление адаптерами

```python
# Получить все платформы
platforms = sdk.adapter.platforms

# Проверить, существует ли адаптер
exists = sdk.adapter.exists("platform_name")

# Включить / Отключить адаптер
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Запустить / Остановить адаптер
# Ниже показаны примеры с передачей параметров. При отсутствии аргументов запуск/остановка применяется ко всем зарегистрированным адаптерам
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Проверить, работает ли адаптер
is_running = sdk.adapter.is_running("platform_name")

# Вывести список всех работающих адаптеров
running = sdk.adapter.list_running()
```

## Middleware

### Регистрация Middleware

```python
# Добавить Middleware
@sdk.adapter.middleware
async def my_middleware(event):
    # Обработка события
    sdk.logger.info(f"Middleware обработка: {event}")
    return event
```

### Порядок выполнения Middleware

Middleware выполняются в порядке регистрации, до того как событие будет распределено обработчику.

## Отправка сообщений

### Базовая отправка

```python
# Получить адаптер
adapter = sdk.adapter.get("platform")

# Отправить текстовое сообщение
await adapter.Send.To("user", "123").Text("Hello")

# Отправить изображение
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### Указание учетной записи отправки

```python
# Использовать имя учетной записи
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Использовать ID учетной записи
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Запрос поддерживаемых методов отправки

```python
# Вывести список всех методов отправки, поддерживаемых платформой
methods = sdk.adapter.list_sends("onebot11")
# Возвращает: ["Text", "Image", "Voice", "Markdown", ...]

# Получить подробную информацию о методе
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

### Цепочка методов

```python
# @Пользователь
await adapter.Send.To("group", "456").At("789").Text("Привет")

# @Всем участникам
await adapter.Send.To("group", "456").AtAll().Text("Всем привет")

# Ответить на сообщение
await adapter.Send.To("group", "456").Reply("msg_id").Text("Ответное сообщение")

# Комбинированное использование
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("Ответ на сообщение @")
```

## Вызов API

### Метод call_api
> Обратите внимание, что способы вызова API для разных платформ могут отличаться. Пожалуйста, обратитесь к документации адаптера соответствующей платформы.
> Не рекомендуется использовать метод call_api напрямую. Рекомендуется использовать класс Send для отправки сообщений

```python
# Вызов платформенного API
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# Стандартный ответ
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
        """Запустить адаптер (должно быть реализовано)"""
        pass
    
    async def shutdown(self):
        """Остановить адаптер (должно быть реализовано)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Вызов платформенного API (должно быть реализовано)"""
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

## Управление состоянием Bot

Адаптеры уведомляют фреймворк о состоянии подключения Bot, отправляя стандартные **события `meta`** стандарта OneBot12. Система автоматически извлекает информацию о Bot для отслеживания состояния.

### Типы событий meta

Адаптеры должны отправлять следующие три типа событий `meta`:

| `type` | `detail_type` | Описание | Когда срабатывает |
|--------|--------------|---------|-------------------|
| `meta` | `connect` | Bot подключился | Успешное установление соединения адаптера с платформой |
| `meta` | `heartbeat` | Пульсация (Heartbeat) | Отправляется регулярно (рекомендуется каждые 30-60 секунд) |
| `meta` | `disconnect` | Bot отключился | При обнаружении разрыва соединения |

### Расширение поля self

ErisPulse расширяет следующие необязательные поля в стандарте OneBot12 `self`:

| Поле | Тип | Описание |
|------|------|---------|
| `self.platform` | string | Название платформы (стандарт OB12) |
| `self.user_id` | string | ID пользователя Bot (стандарт OB12) |
| `self.user_name` | string | Никнейм Bot (расширение ErisPulse) |
| `self.avatar` | string | URL аватара Bot (расширение ErisPulse) |
| `self.account_id` | string | Идентификатор для нескольких учетных записей (расширение ErisPulse) |

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

Обработка системой: регистрация Bot, пометка как `online`, триггер события жизненного цикла `adapter.bot.online`.

#### heartbeat — Пульсация

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

Обработка системой: обновление времени `last_active` (в пульсации также поддерживается обновление метаданных).

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

Обработка системой: пометка Bot как `offline`, триггер события жизненного цикла `adapter.bot.offline`.

### Автоматическое обнаружение обычных событий

Кроме событий `meta`, поле `self` в обычных событиях (`message`/`notice`/`request`) также будет автоматически обнаружено для регистрации Bot и обновления времени активности. Это означает, что даже если адаптер не отправляет событие `connect`, фреймворк может обнаружить Bot из первого обычного события.

### Пример интеграции адаптера

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # Установление соединения с платформой...
        connection = await self._connect()
        
        # Соединение установлено, отправляем событие connect
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
        # Отключение, отправляем событие disconnect
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

### Запрос состояния Bot

```python
# Получить полное состояние всех адаптеров и Bot (удобно для WebUI)
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

# Вывести список всех Bot
all_bots = sdk.adapter.list_bots()

# Вывести список Bot определенной платформы
tg_bots = sdk.adapter.list_bots("telegram")

# Получить подробную информацию об отдельном Bot
info = sdk.adapter.get_bot_info("telegram", "123456")

# Проверить, онлайн ли Bot
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot онлайн")
```

### Значения состояния Bot

| Состояние | Описание |
|-----------|---------|
| `online` | В сети (постоянно получает события или помечен адаптером) |
| `offline` | Офлайн (помечен адаптером или автоматически при закрытии системы) |
| `unknown` | Неизвестно (зарегистрирован, но статус не подтвержден) |

### События жизненного цикла

| Событие | Когда срабатывает | Данные |
|--------|-------------------|--------|
| `adapter.bot.online` | Первое автоматическое обнаружение нового Bot | `{platform, bot_id, status}` |
| `adapter.status.change` | Изменение состояния адаптера (starting/started/stopping/stopped/stop_failed) | `{platform, status}` |

```python
# Слушать событие включения Bot
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot онлайн: {event['data']['platform']}/{event['data']['bot_id']}")

# Слушать изменение состояния адаптера
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"Состояние адаптера: {event['data']['platform']} -> {event['data']['status']}")
```

> При закрытии системы (`shutdown`) все Bot автоматически помечаются как `offline`.

## См. также

- [API модулей ядра](core-modules.md) - API модулей ядра
- [API системы событий](event-system.md) - API модуля Event
- [Руководство по разработке адаптеров](../developer-guide/adapters/) - Разработка адаптеров платформ