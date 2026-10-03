# API системы адаптеров

Документ описывает API-систему адаптеров ErisPulse.

## Менеджер адаптеров

### Получение адаптера

```python
from ErisPulse import sdk

# Получение адаптера по имени
adapter = sdk.adapter.get("platform_name")

# Или можно получить напрямую через атрибут
adapter = sdk.adapter.platform_name
```

### Использование слушателей событий адаптера
> В большинстве случаев рекомендуется использовать модуль `Event` для прослушивания и обработки событий;
>
> Модуль `Event` предоставляет мощные обёртки, которые могут принести больше удобства при разработке модулей

```python
# Прослушивание стандартных событий OneBot12
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Прослушивание стандартных событий определённой платформы
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Прослушивание нативных событий платформы
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
# Приведённые методы показывают только случаи с параметрами, без параметров означает запуск/остановку всех зарегистрированных адаптеров
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Проверка, запущен ли адаптер
is_running = sdk.adapter.is_running("platform_name")

# Получение списка всех запущенных адаптеров
running = sdk.adapter.list_running()

# Чтение метаинформации адаптера (см. module.get_meta, для использования в панели / магазине и т.д.)
info = sdk.adapter.get_info("platform_name")   # Информация о регистрации (meta + имя класса, безопасный для JSON)
meta = sdk.adapter.get_meta("platform_name")   # Метаинформация о введении (description поддерживает i18n-разбор)
raw = sdk.adapter.get_meta("platform_name", resolve_i18n=False)  # Прямая передача исходного словаря i18n
```

## Промежуточные слои (Middleware)

Промежуточные слои выполняются до того, как событие попадает в обработчик, позволяя изменять, фильтровать или записывать данные события.

### Регистрация промежуточного слоя

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"Обработка промежуточным слоем: {event}")
    return event
```

### Модель выполнения промежуточного слоя

- **Порядок выполнения**: промежуточные слои выполняются в порядке их регистрации (раньше зарегистрированные — раньше выполняются)
- **Передача данных**: каждый промежуточный слой получает данные `event`, возвращаемые предыдущим промежуточным слоем; если какой-либо промежуточный слой возвращает `None`, то это значение игнорируется, и передается оригинальная версия данных (при этом выводится предупреждение уровня `warning`)
- **Изменение данных**: промежуточный слой может изменить данные события и вернуть измененный словарь
- **Отклонение события**: промежуточный слой явно возвращает `False`, чтобы отклонить событие — событие отбрасывается, не попадает в обработчики и не вызывает никаких побочных эффектов; при отклонении событие записывается в лог уровня `TRACE` и запускается хук жизненного цикла `adapter.event.blocked` (с именем промежуточного слоя и полным событием)

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
            return False  # Отклонение: событие отбрасывается, не попадает в обработчики
    return event
```

> **Важно**: только явное возвращение `False` отклоняет событие (возвращение пустого словаря / `0` / `""` и других ложных значений не отклоняет); возвращение `None` означает разрешение и неизменность данных. Отклоненные события можно прослушивать, регистрируя хук `adapter.event.blocked` для аудита и выяснения причин, почему событие не было обработано.

## Отправка сообщений (Send)

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
# @пользователь
await adapter.Send.To("group", "456").At("789").Text("Привет")

# @всех
await adapter.Send.To("group", "456").AtAll().Text("Всем привет")

# Ответить на сообщение
await adapter.Send.To("group", "456").Reply("msg_id").Text("Ответ на сообщение")

# Комбинирование
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("Ответ на упомянутое сообщение")
```

## Вызов API

### Метод `call_api`

> **Важно**: `call_api` — это низкоуровневый метод для вызова нативного API платформы, параметры и возвращаемые значения могут отличаться для каждой платформы, см. документацию соответствующего адаптера платформы. **Рекомендуется использовать DSL для отправки сообщений**, `call_api` следует использовать только в тех случаях, когда DSL не поддерживает нужную функциональность (например, получение специфических данных платформы, вызов платформенных интерфейсов управления и т.д.)

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

Адаптер сообщает системе о состоянии подключения бота, отправляя стандартное событие OneBot12 **`meta`**. Система автоматически извлекает информацию о боте из этого события для отслеживания состояния.

### Типы событий `meta`

Адаптер должен отправлять три типа событий `meta`:

| `type` | `detail_type` | Описание | Время срабатывания |
|--------|--------------|----------|-------------------|
| `meta` | `connect` | Бот подключился | После успешного установления соединения адаптера с платформой |
| `meta` | `heartbeat` | Бот отправляет пинг | Регулярно (рекомендуется каждые 30-60 секунд) |
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

Системная обработка: регистрация бота, установка статуса `online`, запуск события жизненного цикла `adapter.bot.online`.

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

Системная обработка: обновление времени `last_active` (в пинге также поддерживаются обновления метаинформации).

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

Системная обработка: установка статуса бота `offline`, запуск события жизненного цикла `adapter.bot.offline`.

### Автоматическое обнаружение обычных событий

Помимо событий `meta`, поля `self` в обычных событиях (`message`/`notice`/`request`) также автоматически обнаруживаются и регистрируются боты, обновляя время активности. Это означает, что даже если адаптер не отправляет событие `connect`, система сможет обнаружить бота из первого обычного события.

### Пример подключения адаптера

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # Установить соединение с платформой...
        connection = await self._connect()
        
        # Успешное подключение, отправить событие `connect`
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
        # Отключение, отправить событие `disconnect`
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

### Получение статуса бота

```python
# Получить полную информацию о статусе всех адаптеров и ботов (удобно для WebUI)
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

### Статусы бота

| Статус | Описание |
|--------|----------|
| `online` | Онлайн (постоянно получает события или адаптер явно помечает) |
| `offline` | Оффлайн (адаптер явно помечает или система автоматически устанавливает при остановке) |
| `unknown` | Неизвестно (зарегистрирован, но статус не подтвержден) |

### События жизненного цикла

| Имя события | Время срабатывания | Данные |
|-------------|-------------------|--------|
| `adapter.bot.online` | При первом обнаружении нового бота | `{platform, bot_id, status}` |
| `adapter.status.change` | При изменении статуса адаптера | `{platform, status}`, возможные значения: `starting` / `started` / `start_failed` / `stopping` / `stopped` / `stop_failed` / `skipped-dependency` (пропущено из-за неготовности зависимых адаптеров) / `disabled` (отключено в конфигурации) |

```python
# Прослушивание события подключения бота
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Бот подключился: {event['data']['platform']}/{event['data']['bot_id']}")

# Прослушивание изменения статуса адаптера
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"Статус адаптера: {event['data']['platform']} -> {event['data']['status']}")
```

> При остановке системы (при `shutdown`), все боты автоматически помечаются как `offline`.

## Связанные документы

- [API основных модулей](core-modules.md) - API основных модулей
- [API системы событий](event-system.md) - API модуля `Event`
- [Руководство по разработке адаптеров](../developer-guide/adapters/) - Разработка адаптеров платформы