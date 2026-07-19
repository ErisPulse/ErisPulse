# API системы адаптеров

Документ подробно описывает API системы адаптеров ErisPulse.

## Менеджер адаптеров

### Получение адаптера

```python
from ErisPulse import sdk

# Получение адаптера по имени
adapter = sdk.adapter.get("platform_name")

# Или можно получить напрямую через атрибут
adapter = sdk.adapter.platform_name
```

### Использование слушателя событий адаптера
> В большинстве случаев рекомендуется использовать модуль `Event` для прослушивания/обработки событий;
>
> Кроме того, модуль `Event` предоставляет мощные обертки, которые могут принести больше удобства при разработке ваших модулей

```python
# Слушатель стандартного события OneBot12
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Слушатель стандартного события конкретной платформы
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Слушатель нативного события платформы
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### Управление адаптерами

```python
# Получить все платформы
platforms = sdk.adapter.platforms

# Проверить существование адаптера
exists = sdk.adapter.exists("platform_name")

# Включить/отключить адаптер
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Запустить/остановить адаптер
# В следующих методах показаны только случаи с передачей параметров, без параметров запускаются/останавливаются все зарегистрированные адаптеры
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Проверить, запущен ли адаптер
is_running = sdk.adapter.is_running("platform_name")

# Получить список всех запущенных адаптеров
running = sdk.adapter.list_running()
```

## Промежуточные обработчики

Промежуточные обработчики выполняются до того, как событие будет передано обработчику, и могут изменять, фильтровать или записывать данные события.

### Регистрация промежуточных обработчиков

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"Промежуточный обработчик: {event}")
    return event
```

### Модель выполнения промежуточных обработчиков

- **Порядок выполнения**: промежуточные обработчики выполняются в порядке регистрации (ранее зарегистрированные выполняются первыми)
- **Передача данных**: каждый промежуточный обработчик получает данные `event` от предыдущего промежуточного обработчика; если какой-либо промежуточный обработчик возвращает `None`, то это значение игнорируется, и оригинальные данные передаются дальше (выводится лог уровня `warning`)
- **Изменение данных**: промежуточные обработчики могут изменять данные события и возвращать измененный словарь

```python
@sdk.adapter.middleware
async def add_timestamp(event):
    event["processed_at"] = time.time()
    return event

@sdk.adapter.middleware
async def filter_spam(event):
    if event.get("detail_type") == "private":
        text = event.get("alt_message", "")
        if "реклама" in text:
            return None   # Возвращение `None` не останавливает распространение события, просто игнорируется это возвращаемое значение
    return event
```

> **Внимание**: промежуточные обработчики в настоящее время не поддерживают блокировку распространения событий. Если необходимо отфильтровать определенные события, следует реализовать это в обработчике событий с помощью условий.
> Однако вы можете установить обработчик с высоким приоритетом в модуле Event, а затем использовать `event.mark_processed()` внутри обработчика для блокировки обработчиков с низким приоритетом

## Отправка сообщений Send

### Базовая отправка

```python
# Получить адаптер
adapter = sdk.adapter.get("platform")

# Отправить текстовое сообщение
await adapter.Send.To("user", "123").Text("Hello")

# Отправить сообщение с изображением
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### Указание отправляющего аккаунта

```python
# Использовать имя аккаунта
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Использовать ID аккаунта
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Получение поддерживаемых методов отправки

```python
# Получить список всех методов отправки, поддерживаемых платформой
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
#     "docstring": "Отправка текстового сообщения..."
# }
```

### Цепочечные модификаторы

```python
# @пользователя
await adapter.Send.To("group", "456").At("789").Text("Привет")

# @всех участников
await adapter.Send.To("group", "456").AtAll().Text("Всем привет")

# Ответить на сообщение
await adapter.Send.To("group", "456").Reply("msg_id").Text("Содержание ответа")

# Комбинированное использование
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("Ответ на сообщение с @")
```

## Вызов API

### Метод call_api

> **Внимание**: `call_api` — это низкоуровневый метод для прямого вызова оригинального API платформы, параметры и возвращаемые значения могут отличаться для каждой платформы, обратитесь к документации адаптера соответствующей платформы. **Рекомендуется использовать DSL для отправки сообщений**, `call_api` следует использовать только в сценариях, где DSL не поддерживает (например, получение платформенно-специфических данных, вызов платформенно-специфических интерфейсов и т.д.)

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
        """Запуск адаптера (обязательно реализовать)"""
        pass
    
    async def shutdown(self):
        """Остановка адаптера (обязательно реализовать)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Вызов API платформы (обязательно реализовать)"""
        pass
```

### Вложенный класс Send

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """Отправка текстового сообщения"""
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

Адаптер сообщает фреймворку о состоянии подключения бота, отправляя стандартное событие **`meta`** OneBot12. Система автоматически извлекает информацию о боте из этого события для отслеживания состояния.

### Типы событий meta

Адаптер должен отправлять три типа событий `meta`:

| `type` | `detail_type` | Описание | Время срабатывания |
|--------|--------------|----------|-------------------|
| `meta` | `connect` | Бот подключен | После успешного установления соединения адаптера с платформой |
| `meta` | `heartbeat` | Бот пингует | Регулярно отправляется (рекомендуется каждые 30-60 секунд) |
| `meta` | `disconnect` | Бот отключен | При обнаружении разрыва соединения |

### Расширение поля self

ErisPulse расширяет поле `self` стандарта OneBot12 следующими необязательными полями:

| Поле | Тип | Описание |
|------|------|----------|
| `self.platform` | string | Название платформы (стандарт OB12) |
| `self.user_id` | string | ID пользователя бота (стандарт OB12) |
| `self.user_name` | string | Никнейм бота (расширение ErisPulse) |
| `self.avatar` | string | URL аватара бота (расширение ErisPulse) |
| `self.account_id` | string | Идентификатор многоаккаунтности (расширение ErisPulse) |

### Формат события meta

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

Обработка системой: регистрация бота, установка статуса `online`, срабатывание события жизненного цикла `adapter.bot.online`.

#### heartbeat — Пинг

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

Обработка системой: обновление времени `last_active` (в пинге также поддерживается обновление метаинформации).

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

Обработка системой: установка статуса бота `offline`, срабатывание события жизненного цикла `adapter.bot.offline`.

### Автоматическое обнаружение обычных событий

Помимо событий `meta`, обычные события (`message`/`notice`/`request`) также автоматически обнаруживают и регистрируют бота, обновляя время активности. Это означает, что даже если адаптер не отправляет событие `connect`, фреймворк сможет обнаружить бота из первого обычного события.

### Пример подключения адаптера

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # Установление соединения с платформой...
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

### Проверка состояния бота

```python
# Получить полное состояние всех адаптеров и ботов (удобно для WebUI)
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

# Получить список всех ботов
all_bots = sdk.adapter.list_bots()

# Получить список ботов на конкретной платформе
tg_bots = sdk.adapter.list_bots("telegram")

# Получить подробную информацию о боте
info = sdk.adapter.get_bot_info("telegram", "123456")

# Проверить, находится ли бот онлайн
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Бот онлайн")
```

### Значения состояния бота

| Состояние | Описание |
|-----------|----------|
| `online` | Онлайн (постоянно получает события или адаптер активно помечает) |
| `offline` | Оффлайн (адаптер активно помечает или автоматически устанавливает при закрытии системы) |
| `unknown` | Неизвестно (зарегистрирован, но статус не подтвержден) |

### События жизненного цикла

| Имя события | Время срабатывания | Данные |
|-------------|-------------------|--------|
| `adapter.bot.online` | При первом автоматическом обнаружении нового бота | `{platform, bot_id, status}` |
| `adapter.status.change` | При изменении состояния адаптера (starting/started/stopping/stopped/stop_failed) | `{platform, status}` |

```python
# Слушатель события онлайн бота
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Бот онлайн: {event['data']['platform']}/{event['data']['bot_id']}")

# Слушатель изменения состояния адаптера
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"Состояние адаптера: {event['data']['platform']} -> {event['data']['status']}")
```

> При завершении работы системы (shutdown) все боты автоматически помечаются как `offline`.

## Связанные документы

- [API основных модулей](core-modules.md) - API основных модулей
- [API системы событий](event-system.md) - API модуля Event
- [Руководство по разработке адаптеров](../developer-guide/adapters/) - Разработка адаптеров платформы