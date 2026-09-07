# API системы адаптеров

В данном документе подробно описывается API системы адаптеров ErisPulse.

## Менеджер адаптеров

### Получение адаптера

```python
from ErisPulse import sdk

# Получение адаптера по имени
adapter = sdk.adapter.get("platform_name")

# Или можно получить напрямую через атрибут
adapter = sdk.adapter.platform_name
```

### Использование обработчиков событий адаптера
> В большинстве случаев рекомендуется использовать модуль `Event` для прослушивания/обработки событий.
>
> Кроме того, модуль `Event` предоставляет мощные обертки, которые могут принести больше удобства при разработке ваших модулей

```python
# Прослушивание стандартного события OneBot12
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Прослушивание стандартного события конкретной платформы
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Прослушивание оригинального события платформы
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
# В следующих методах показаны только случаи с передачей параметров, отсутствие параметров означает запуск/остановку всех зарегистрированных адаптеров
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Проверка, запущен ли адаптер
is_running = sdk.adapter.is_running("platform_name")

# Получение списка всех запущенных адаптеров
running = sdk.adapter.list_running()
```

## Middleware

Middleware выполняется до того, как событие будет передано обработчику. Он может изменять, фильтровать или регистрировать данные события.

### Регистрация middleware

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"Middleware обрабатывает: {event}")
    return event
```

### Модель выполнения middleware

- **Порядок выполнения**: Middleware выполняется в порядке регистрации (ранее зарегистрированные middleware выполняются первыми)
- **Передача данных**: Каждый middleware получает данные `event`, возвращённые предыдущим middleware. Если middleware возвращает `None`, то это значение игнорируется, и передача данных продолжается с исходными данными (при этом выводится предупреждение уровня `warning`)
- **Изменение данных**: Middleware может изменять данные события и возвращать изменённый словарь

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
            return None   # Возвращение `None` не останавливает распространение события, а игнорирует это возвращаемое значение
    return event
```

> **Важно**: Middleware в настоящее время не поддерживает блокировку распространения событий. Если необходимо отфильтровать определённые события, реализуйте это через условные проверки в обработчике событий.  
> Однако вы можете установить обработчик с высоким приоритетом в модуле Event и использовать `event.mark_processed()` внутри обработчика для блокировки обработки событий с низким приоритетом.

## Отправка сообщений

### Основная отправка

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

# Использовать ID бота
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

### Цепочка модификаторов

```python
# @пользователя
await adapter.Send.To("group", "456").At("789").Text("你好")

# @всех участников
await adapter.Send.To("group", "456").AtAll().Text("大家好")

# Ответить на сообщение
await adapter.Send.To("group", "456").Reply("msg_id").Text("回复内容")

# Комбинировать
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("回复@的消息")
```

## API 调ов

### Метод call_api

> **Внимание**: `call_api` — это базовый метод для прямого вызова API платформы, параметры и возвращаемые значения могут отличаться в зависимости от платформы. Пожалуйста, ознакомьтесь с документацией адаптера соответствующей платформы. **Рекомендуется использовать Send DSL для отправки сообщений**, используйте `call_api` только в сценариях, которые не поддерживаются Send DSL (например, для получения специфических данных платформы, вызова административных интерфейсов платформы и т.д.).

```python
# Вызов API платформы
result = await adapter.call_api(
    endpoint="/send",
    content="Привет",
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
        """Запуск адаптера (должен быть реализован)"""
        pass
    
    async def shutdown(self):
        """Остановка адаптера (должен быть реализован)"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """Вызов API платформы (должен быть реализован)"""
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

Адаптер сообщает фреймворку о состоянии подключения бота, отправляя **события `meta`** в соответствии со стандартом OneBot12. Система автоматически извлекает информацию о боте из этих событий для отслеживания состояния.

### Типы событий `meta`

Адаптер должен отправлять три типа событий `meta`:

| `type` | `detail_type` | Описание | Время срабатывания |
|--------|--------------|----------|-------------------|
| `meta` | `connect` | Бот подключился | После успешного установления соединения адаптера с платформой |
| `meta` | `heartbeat` | Бот отправил сигнал поддержания связи | Регулярно (рекомендуется каждые 30-60 секунд) |
| `meta` | `disconnect` | Бот отключился | При обнаружении разрыва соединения |

### Расширение поля `self`

ErisPulse расширяет стандартный OneBot12-файл `self` следующими необязательными полями:

| Поле | Тип | Описание |
|------|-----|----------|
| `self.platform` | string | Название платформы (стандарт OB12) |
| `self.user_id` | string | ID пользователя бота (стандарт OB12) |
| `self.user_name` | string | Никнейм бота (расширение ErisPulse) |
| `self.avatar` | string | URL аватара бота (расширение ErisPulse) |
| `self.account_id` | string | Идентификатор многоконтурной учетной записи (расширение ErisPulse) |

### Формат событий `meta`

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

Системная обработка: регистрация бота, установка статуса `online`, срабатывание жизненного цикла `adapter.bot.online`.

#### heartbeat — Сигнал поддержания связи

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

Системная обработка: обновление времени `last_active` (сигнал поддержания связи также поддерживает обновление метаинформации).

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

Системная обработка: установка статуса бота `offline`, срабатывание жизненного цикла `adapter.bot.offline`.

### Автоматическое обнаружение бота в обычных событиях

Помимо событий `meta`, обычные события (`message`/`notice`/`request`) также содержат поле `self`, которое автоматически обнаруживает и регистрирует бота, обновляя время активности. Это означает, что даже если адаптер не отправляет событие `connect`, фреймворк сможет обнаружить бота из первого обычного события.

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

### Запрос состояния бота

```python
# Получение полной информации обо всех адаптерах и ботах (удобно для WebUI)
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

# Получение списка всех ботов
all_bots = sdk.adapter.list_bots()

# Получение списка ботов на определенной платформе
tg_bots = sdk.adapter.list_bots("telegram")

# Получение информации о конкретном боте
info = sdk.adapter.get_bot_info("telegram", "123456")

# Проверка онлайн-статуса бота
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Бот в сети")
```

### Значения состояния бота

| Состояние | Описание |
|-----------|----------|
| `online` | Онлайн (постоянное получение событий или активная маркировка адаптером) |
| `offline` | Оффлайн (активная маркировка адаптером или автоматическая установка при остановке системы) |
| `unknown` | Неизвестно (зарегистрирован, но статус не подтвержден) |

### Жизненные циклы событий

| Имя события | Время срабатывания | Данные |
|-------------|-------------------|--------|
| `adapter.bot.online` | При первом обнаружении нового бота | `{platform, bot_id, status}` |
| `adapter.status.change` | При изменении состояния адаптера (starting/started/stopping/stopped/stop_failed) | `{platform, status}` |

```python
# Подписка на событие подключения бота
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Бот подключился: {event['data']['platform']}/{event['data']['bot_id']}")

# Подписка на изменение состояния адаптера
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"Состояние адаптера: {event['data']['platform']} -> {event['data']['status']}")
```

> При остановке системы (shutdown) все боты автоматически помечаются как `offline`.

## Связанные документы

- [API основных модулей](core-modules.md) - API основных модулей
- [API системы событий](event-system.md) - API модуля Event
- [Руководство по разработке адаптеров](../developer-guide/adapters/) - Разработка адаптеров для платформ