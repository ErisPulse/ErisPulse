# API системы адаптеров

> [!TIP]
> **Когда нужно читать эту статью**: если вам нужно управлять адаптерами (получение экземпляров, запуск/остановка, проверка онлайн-статуса бота), использовать DSL-DSL для отправки сообщений, регистрировать промежуточные обработчики (middleware), или интегрировать отправку статуса бота (события meta) в адаптер, обратитесь к этой статье. Если это не требуется, пропустите.

Данная документация подробно описывает API-систему адаптеров ErisPulse.

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
> В большинстве случаев рекомендуется использовать модуль `Event` для прослушивания/обработки событий;
>
> Кроме того, модуль `Event` предоставляет мощные обертки, которые могут принести больше удобства при разработке ваших модулей

```python
# Обработка стандартного события OneBot12
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# Обработка стандартного события определенной платформы
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# Обработка оригинального события платформы
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### Управление адаптером

```python
# Получение всех платформ
platforms = sdk.adapter.platforms

# Проверка существования адаптера
exists = sdk.adapter.exists("platform_name")

# Включение/отключение адаптера
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# Запуск/остановка адаптера
# В следующих методах показаны только случаи с передачей параметров, без параметров означает запуск/остановку всех зарегистрированных адаптеров
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# Проверка, запущен ли адаптер
is_running = sdk.adapter.is_running("platform_name")

# Получение списка запущенных адаптеров
running = sdk.adapter.list_running()

# Чтение метаинформации адаптера (сопоставление с module.get_meta, для использования панелью / магазином и т.п.)
info = sdk.adapter.get_info("platform_name")   # Регистрационная информация (meta + имя класса, безопасная для JSON)
meta = sdk.adapter.get_meta("platform_name")   # Информация о мета-данных (description поддерживает i18n-разбор)
raw = sdk.adapter.get_meta("platform_name", resolve_i18n=False)  # Передача исходного словаря i18n
```

## Промежуточные обработчики (Middleware)

Промежуточные обработчики выполняются перед распределением событий к обработчикам, позволяя изменять, фильтровать или записывать данные событий.

### Регистрация промежуточного обработчика

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"Middleware обработка: {event}")
    return event
```

### Модель выполнения промежуточного обработчика

- **Порядок выполнения**: промежуточные обработчики выполняются в порядке регистрации (раньше зарегистрированные — раньше выполняются)
- **Передача данных**: каждый промежуточный обработчик получает `event` данные, возвращённые предыдущим промежуточным обработчиком; если какой-либо промежуточный обработчик возвращает `None`, то это значение игнорируется, и передача данных продолжается с оригинальными данными (при этом выводится предупреждение уровня `warning`)
- **Изменение данных**: промежуточный обработчик может изменять данные события и возвращать изменённый словарь
- **Отклонение события**: если промежуточный обработчик явно возвращает `False`, событие отклоняется — событие отбрасывается, не попадает в обработчики и не вызывает никаких побочных эффектов; при отклонении выводится трассировка уровня `TRACE` и запускается хук жизненного цикла `adapter.event.blocked` (содержит имя промежуточного обработчика и полное событие)

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
            return False  # Отклонение: событие отбрасывается, не попадает в обработчики
    return event
```

> **Важно**: только явное возвращение `False` отклоняет событие (возвращение пустого словаря / `0` / `""` и т.д. не отклоняет);
> Возвращение `None` означает, что событие разрешено и нагрузка не изменяется. Отклонённые события можно прослушивать через хук `adapter.event.blocked` для аудита и выявления причин, почему событие не было обработано.

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

# Использование ID аккаунта
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Проверка поддерживаемых методов отправки

```python
# Получение списка всех поддерживаемых методов отправки для платформы
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
#     "docstring": "Отправка текстового сообщения..."
# }
```

### Цепочка модификаторов

```python
# @пользователя
await adapter.Send.To("group", "456").At("789").Text("Привет")

# @всех участников
await adapter.Send.To("group", "456").AtAll().Text("Всем привет")

# Ответ на сообщение
await adapter.Send.To("group", "456").Reply("msg_id").Text("Ответ на сообщение")

# Комбинирование
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("Ответ на сообщение с упоминанием")
```

## Вызов API

### Метод `call_api`

> **Важно**: `call_api` — это низкоуровневый метод для прямого вызова оригинального API платформы, параметры и возвращаемые значения могут отличаться для каждой платформы, пожалуйста, обратитесь к документации соответствующего адаптера платформы. **Рекомендуется использовать DSL для отправки сообщений**, только в случаях, когда DSL не поддерживает нужные функции (например, получение специфических данных платформы, вызов платформенных интерфейсов управления и т.п.), используйте `call_api`.

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

## Управление статусом бота

Адаптер сообщает статус подключения бота, отправляя стандартные события OneBot12 **`meta`**. Система автоматически извлекает информацию о боте из этих событий для отслеживания статуса.

### Отправка события `meta`

Адаптер отправляет события `meta`, чтобы сообщить статус бота, три типа `detail_type`: `connect` (регистрация и онлайн), `heartbeat` (поддержание активности), `disconnect` (отметка о неактивности). Рекомендуется использовать `emit_meta()` для отправки одного события; даже если события `meta` не отправляются, система будет автоматически обнаруживать бота из обычных событий (message/notice/request) по полю `self`.

- **Формат и способ отправки события `meta`** (когда отправлять, использование `emit_meta()`, ручная конструкция) см. в [Рекомендациях по лучшим практикам адаптеров - Управление статусом бота и событиями `meta`](../developer-guide/adapters/best-practices.md#bot-状态管理与-meta-事件)
- **Механизм автоматического обнаружения и поведение системы** см. в [Основных концепциях адаптеров - Управление статусом бота](../developer-guide/adapters/core-concepts.md#bot-状态管理)

### Проверка статуса бота

```python
# Получение полного статуса всех адаптеров и ботов (удобно для веб-интерфейса)
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

# Получение списка ботов определённой платформы
tg_bots = sdk.adapter.list_bots("telegram")

# Получение подробной информации о боте
info = sdk.adapter.get_bot_info("telegram", "123456")

# Проверка, онлайн ли бот
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Бот онлайн")
```

### Значения статуса бота

| Статус | Описание |
|------|------|
| `online` | Онлайн (постоянно получает события или адаптер активно отмечает статус) |
| `offline` | Оффлайн (адаптер активно отмечает или система автоматически устанавливает при остановке) |
| `unknown` | Неизвестно (зарегистрирован, но статус не подтверждён) |

### Жизненные циклы событий

| Имя события | Точка срабатывания | Данные |
|--------|---------|------|
| `adapter.bot.online` | При первом автоматическом обнаружении нового бота | `{platform, bot_id, status}` |
| `adapter.status.change` | При изменении статуса адаптера | `{platform, status}`, возможные значения статуса: `starting` / `started` / `start_failed` / `stopping` / `stopped` / `stop_failed` / `skipped-dependency` (запуск пропущен из-за неподготовленных зависимостей) / `disabled` (отключено в конфигурации) |

```python
# Обработка события онлайн-бота
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Бот онлайн: {event['data']['platform']}/{event['data']['bot_id']}")

# Обработка изменения статуса адаптера
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"Статус адаптера: {event['data']['platform']} -> {event['data']['status']}")
```

> При завершении работы системы (shutdown), все боты автоматически помечаются как `offline`.

## Связанные документы

**Дополнительные API**:
- [API основных модулей](core-modules.md) - API основных модулей
- [API системы событий](event-system.md) - API модуля Event

**Начинаем писать адаптеры**:
- [Руководство по разработке адаптеров](../developer-guide/adapters/) - Разработка адаптеров платформ
- [Руководство по стандартизации адаптеров (общее)](../standards/standardization-guide.md) - Стандарты и чек-лист перед реализацией нового адаптера