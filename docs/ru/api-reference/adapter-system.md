# API системы адаптеров

Документ подробно описывает API-систему адаптеров ErisPulse.

## Менеджер адаптеров

### Получение адаптера

```python
from ErisPulse import sdk

# Получить адаптер по имени
adapter = sdk.adapter.get("platform_name")

# Или получить напрямую через атрибут
adapter = sdk.adapter.platform_name
```

### Использование прослушивания событий адаптера
> Как правило, рекомендуется использовать модуль `Event` для прослушивания/обработки событий;
>
> Модуль `Event` предоставляет мощные обертки, которые могут принести больше удобства при разработке ваших модулей

```python
# Прослушивание стандартного события OneBot12
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Прослушивание стандартного события определенной платформы
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Прослушивание оригинального события платформы
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### Управление адаптером

```python
# Получить все платформы
platforms = sdk.adapter.platforms

# Проверить существование адаптера
exists = sdk.adapter.exists("platform_name")

# Включить/выключить адаптер
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Запустить/остановить адаптер
# Приведенные методы показывают только случаи с передачей параметров,
# отсутствие параметров означает запуск/остановку всех зарегистрированных адаптеров
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Проверить, запущен ли адаптер
is_running = sdk.adapter.is_running("platform_name")

# Получить список всех запущенных адаптеров
running = sdk.adapter.list_running()
```

## Промежуточные обработчики (Middleware)

Промежуточные обработчики выполняются до отправки события на обработчик, позволяя изменять, фильтровать или записывать данные события.

### Регистрация промежуточного обработчика

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"Middleware обрабатывает: {event}")
    return event
```

### Модель выполнения промежуточного обработчика

- **Порядок выполнения**: промежуточные обработчики выполняются в порядке регистрации (раньше зарегистрированные выполняются первыми)
- **Передача данных**: каждый промежуточный обработчик получает данные `event`, возвращаемые предыдущим промежуточным обработчиком; если какой-либо промежуточный обработчик возвращает `None`, то это значение игнорируется, а исходные данные продолжают передаваться (выводится предупреждение уровня `warning`)
- **Изменение данных**: промежуточный обработчик может изменить данные события и вернуть измененный словарь
- **Отказ от события**: промежуточный обработчик явно возвращает `False`, отклоняя событие — событие отбрасывается, не поступает ни на один обработчик, без каких-либо побочных эффектов; при отклонении событие регистрируется в логах уровня `TRACE` и запускается хук жизненного цикла `adapter.event.blocked` (содержит имя промежуточного обработчика и полное событие)

```python
@sdk.adapter.middleware
async def add_timestamp(event):
    event["processed_at"] = time.time()
    return event

@sdk.adapter.middleware
async def filter_spam(event):
    if event.get("detail_type") == "private":
        text = event.get("alt_message", "")
        if "спам" in text:
            return False  # Отказ: событие отбрасывается, не поступает ни на один обработчик
    return event
```

> **Важно**: только явный возврат `False` отклоняет событие (возврат пустого словаря / `0` / `""` и других ложных значений не отклоняет);
> Возврат `None` означает разрешение и неизменность данных. Отклоненные события можно прослушивать, отслеживая хук `adapter.event.blocked`, чтобы проверить, почему событие не было обработано.

## Отправка сообщений (Send)

### Базовая отправка

```python
# Получить адаптер
adapter = sdk.adapter.get("platform")

# Отправить текстовое сообщение
await adapter.Send.To("user", "123").Text("Hello")

# Отправить изображение
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
#     "docstring": "Отправить текстовое сообщение..."
# }
```

### Цепочечные модификаторы

```python
# @пользователь
await adapter.Send.To("group", "456").At("789").Text("Привет")

# @всех
await adapter.Send.To("group", "456").AtAll().Text("Всем привет")

# Ответить на сообщение
await adapter.Send.To("group", "456").Reply("msg_id").Text("Содержание ответа")

# Комбинированные действия
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("Ответ на упомянутое сообщение")
```

## Вызов API

### Метод `call_api`

> **Важно**: `call_api` — это базовый метод для вызова оригинальных API платформы, параметры и возвращаемые значения могут отличаться для разных платформ, пожалуйста, обратитесь к документации адаптера соответствующей платформы. **Рекомендуется использовать DSL для отправки сообщений**, используйте `call_api` только в случаях, когда DSL не поддерживает нужную функцию (например, получение специфических данных платформы, вызов платформенных интерфейсов управления и т.д.)

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

### Методы `BaseAdapter`

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

### Вложенный класс `Send`

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

Адаптер сообщает системе о состоянии подключения бота, отправляя стандартные события OneBot12 **`meta`**. Система автоматически извлекает информацию о боте из этих событий для отслеживания состояния.

### Типы событий `meta`

Адаптер должен отправлять следующие три события `meta`:

| `type` | `detail_type` | Описание | Время срабатывания |
|--------|--------------|----------|-------------------|
| `meta` | `connect` | Бот подключился | После успешного установления соединения адаптера с платформой |
| `meta` | `heartbeat` | Бот пингует | Регулярно отправляется (рекомендуется каждые 30-60 секунд) |
| `meta` | `disconnect` | Бот отключился | При обнаружении разрыва соединения |

### Расширение поля `self`

ErisPulse расширяет стандартное поле `self` OneBot12 следующими необязательными полями:

| Поле | Тип | Описание |
|------|-----|----------|
| `self.platform` | string | Название платформы (стандарт OB12) |
| `self.user_id` | string | ID пользователя бота (стандарт OB12) |
| `self.user_name` | string | Никнейм бота (расширение ErisPulse) |
| `self.avatar` | string | URL аватара бота (расширение ErisPulse) |
| `self.account_id` | string | Идентификатор аккаунта (расширение ErisPulse) |

### Формат события `meta`

#### `connect` — подключение

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

Обработка системой: регистрация бота, установка статуса `online`, запуск события жизненного цикла `adapter.bot.online`.

#### `heartbeat` — пинг

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

#### `disconnect` — отключение

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

Обработка системой: установка статуса бота `offline`, запуск события жизненного цикла `adapter.bot.offline`.

### Автоматическое обнаружение обычных событий

Помимо событий `meta`, поля `self` в обычных событиях (`message`/`notice`/`request`) также автоматически обнаруживаются и регистрируются бот, обновляется время активности. Это означает, что даже если адаптер не отправляет событие `connect`, фреймворк сможет обнаружить бота из первого обычного события.

### Пример подключения адаптера

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # Установить соединение с платформой...
        connection = await self._connect()
        
        # Успешное подключение, отправить событие connect
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
        # Отключение, отправить событие disconnect
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

### Получение состояния бота

```python
# Получить полную информацию о состоянии всех адаптеров и ботов (удобно для WebUI)
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

# Получить список ботов определенной платформы
tg_bots = sdk.adapter.list_bots("telegram")

# Получить информацию о конкретном боте
info = sdk.adapter.get_bot_info("telegram", "123456")

# Проверить, онлайн ли бот
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Бот онлайн")
```

### Состояния бота

| Состояние | Описание |
|-----------|----------|
| `online` | Онлайн (постоянно получает события или бот активно помечен) |
| `offline` | Оффлайн (активно помечен адаптером или автоматически установлен при завершении системы) |
| `unknown` | Неизвестно (зарегистрирован, но статус не подтвержден) |

### События жизненного цикла

| Название события | Время срабатывания | Данные |
|------------------|--------------------|--------|
| `adapter.bot.online` | При первом обнаружении нового бота | `{platform, bot_id, status}` |
| `adapter.status.change` | При изменении состояния адаптера (starting/started/stopping/stopped/stop_failed) | `{platform, status}` |

```python
# Прослушивание события появления бота
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Бот появился: {event['data']['platform']}/{event['data']['bot_id']}")

# Прослушивание изменения состояния адаптера
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"Состояние адаптера: {event['data']['platform']} -> {event['data']['status']}")
```

> При завершении системы (shutdown) все боты автоматически помечаются как `offline`.

## Связанные документы

- [API-модулей](core-modules.md) - API-модулей
- [API-системы событий](event-system.md) - API-модуля Event
- [Руководство по разработке адаптеров](../developer-guide/adapters/) - Разработка адаптеров платформы