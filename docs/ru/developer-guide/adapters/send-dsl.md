# SendDSL — подробное руководство

SendDSL — это интерфейс для отправки сообщений с цепочкой вызовов, предоставляемый адаптером ErisPulse.

## Базовое использование

### 1. Указание типа и ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. Указание только ID

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. Указание учетной записи отправки

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. Комбинированное использование

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## Цепочка методов

```
Using/Account() → To() → [модификаторы] → [методы отправки]
```

## Методы отправки

Все методы отправки должны возвращать объект `asyncio.Task`.

### Базовые методы

| Метод | Описание | Возвращаемое значение |
|--------|----------|-----------------------|
| `Text(text: str)` | Отправка текстового сообщения | `asyncio.Task` |
| `Image(file: bytes \| str)` | Отправка изображения | `asyncio.Task` |
| `Voice(file: bytes \| str)` | Отправка голосового сообщения | `asyncio.Task` |
| `Video(file: bytes \| str)` | Отправка видео | `asyncio.Task` |
| `File(file: bytes \| str)` | Отправка файла | `asyncio.Task` |

### Методы протокола

| Метод | Описание | Возвращаемое значение | Обязательно ли |
|--------|----------|-----------------------|----------------|
| `Raw_ob12(message)` | Отправка сообщения в формате OneBot12 | `asyncio.Task` | **Должен быть реализован** |

> **Важно**: `Raw_ob12` — это основной метод адаптера, его **нужно реализовать**. Это единая точка входа для обратного преобразования (OneBot12 → Платформа). Если не реализовано, базовый класс записывает error в лог и возвращает стандартный ответ об ошибке (`status: "failed"`, `retcode: 10002`). Стандартные методы (`Text`, `Image` и т.д.) должны внутри делегировать вызов `Raw_ob12`.

## Модификаторы

Модификаторы возвращают `self` для поддержки цепочки вызовов.

### Методы @

```python
# @ одного пользователя
await adapter.Send.To("group", "123").At("456").Text("你好")

# @ нескольких пользователей
await adapter.Send.To("group", "123").At("456").At("789").Text("你们好")
```

### Метод AtAll

```python
# @ всех участников
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Метод Reply

```python
# Ответ на сообщение
await adapter.Send.To("group", "123").Reply("msg_id").Text("回复内容")
```

### Комбинированные модификаторы

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回复@的消息")
```

## Управление учетными записями

### Метод Using

`Using()` используется для указания учетной записи для отправки сообщения. Передаваемый идентификатор сопоставляется методом `_resolve_account()` в следующем порядке приоритета:

1. **Имя учетной записи** — имя ключа в конфигурации (например, `"default"`, `"bot1"`)
2. **Заданный при трансформации bot_id** — идентификатор, автоматически внедряемый при преобразовании события
3. **Любая строка** — другие строковые поля в конфигурации
4. **Резерв** — первая включенная учетная запись

```python
# Использование имени учетной записи
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Использование bot_id (то есть self.user_id из события)
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Метод Account

Метод `Account` эквивалентен `Using`:

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## Асинхронная обработка

### Игнорирование результата

```python
# Сообщение отправляется в фоне
task = adapter.Send.To("user", "123").Text("Hello")

# Продолжение выполнения других операций
# ...
```

### Ожидание результата

```python
# Прямое await для получения результата
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"Результат отправки: {result}")

# Сначала сохраняем Task, ждем позже
task = adapter.Send.To("user", "123").Text("Hello")
# ... другие операции ...
result = await task
```

## Система правил отправки

SendDSL содержит встроенный набор декораторов правил отправки, которые присоединяются через цепочку вызовов и применяются единообразно при окончательной отправке. Правила покрывают распространенные сценарии: управление таймаутами, автоматическая повторная попытка, обратные вызовы при успехе, отложенная отправка, приоритет и сброс, мониторинг прогресса.

Правила методов **возвращают self** (так же как At/AtAll/Reply) и должны вызываться перед методами отправки (Text/Image и т.д.). Правила распространяются на новые экземпляры, созданные через `To`/`Using`/`Account`.

### Список правил

| Метод | Описание |
|--------|----------|
| `.Hook(callback)` | Выполняется после успешной отправки (можно вызвать несколько раз, последовательно) |
| `.Retry(times=1)` | Автоматическая повторная попытка при неудаче N раз (всего N+1 попыток, включая первую) |
| `.Timeout(seconds)` | Таймаут для отдельной отправки, по истечении которого текущая попытка отменяется (можно комбинировать с Retry) |
| `.Defer(seconds=1.0)` | Отложенная отправка (таймер внутри процесса, не персистентное хранилище) |
| `.Priority(level, drop_if_busy=False)` | Установка приоритета; возможен сброс при переполнении очереди |
| `.OnProgress(callback)` | Обратный вызов на каждом этапе прогресса (передает `SendContext`) |
| `.OnError(callback)` | Обратный вызов при финальной ошибке (срабатывает один раз) |

### Логика после успешной отправки (Hook)

```python
# Синхронный обратный вызов
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"Успешная отправка, ID сообщения: {r['message_id']}"))
       .Text("你好"))

# Асинхронный обратный вызов
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("扣积分")
```

Hook выполняется только при окончательной успешной отправке (включая успешную после повторной попытки); не срабатывает при неудаче, таймауте или отмене.

### Автоматическая повторная попытка (Retry)

```python
# Повторить 2 раза после первой неудачи, всего 3 попытки
result = await adapter.Send.To("user", "123").Retry(2).Text("带重试")
```

Условия срабатывания повторной попытки: выбрасывание исключения при отправке, превышение таймаута отправки, или возвращение ответа с `status == "failed"`.

### Автоматическая отмена по таймауту (Timeout)

```python
# Отмена, если отправка занимает более 10 секунд
await adapter.Send.To("user", "123").Timeout(10).Text("带超时")

# Таймаут + повторная попытка: 10 секунд на попытку, максимум 3 попытки
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("超时重试")
```

### Мониторинг прогресса (OnProgress / OnError)

```python
def on_progress(ctx):
    print(f"Этап: {ctx.stage}, Попытка: {ctx.attempt + 1}/{ctx.max_attempts}, Время: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  Ошибка: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"Ошибка при отправке {ctx.target_id}: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("监控"))
```

Поля, содержащиеся в `SendContext`: `task_id`、`platform`、`method`、`target_type`、`target_id`、`bot_id`、`stage`、`attempt`、`max_attempts`、`started_at`、`finished_at`、`elapsed`、`error`、`result`、`extra`.

Возможные значения `stage`: `pending`、`sending`、`retrying`、`success`、`failed`、`timeout`、`cancelled`、`dropped`.

### Отложенная отправка (Defer)

```python
# Отправить через 5 секунд
await adapter.Send.To("user", "123").Defer(5).Text("迟到消息")
```

> Примечание: отложенность основана на таймере внутри процесса, после перезапуска процесса время теряется, персистентное хранилище не предоставляется.

### Приоритет и сброс при переполнении (Priority)

```python
# Сообщение с низким приоритетом, автоматически сбрасывается при переполнении очереди
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("可放弃的通知"))
# Если сброшено, result["status"] == "failed"
```

После включения `drop_if_busy`, когда количество выполняющихся задач отправки превышает порог (по умолчанию 64), отправка в этот раз прекращается напрямую. Глобальный порог можно настроить через `.PriorityThreshold(n)`.

### Комбинирование правил и фоновое выполнение

```python
# Не блокирует основной процесс, правила действуют
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("Отправка успешна！"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("你好"))

# Продолжение выполнения других операций
await handle_next_action()
```

### Распространение правил

Правила распространяются на новые экземпляры, созданные через `To`/`Using`/`Account`, чтобы избежать потери правил в цепочке вызовов:

```python
# Правила установлены до To, также распространяются на экземпляр, созданный To
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send все еще несет Retry(3) и Timeout(10)
await send.Text("hi")
```

Правила для нескольких экземпляров независимы (списки hooks глубокая копия).

## Режим массового построения (Build)

Помимо режима отдельной отправки, SendDSL поддерживает режим массового построения: записать несколько методов отправки в одной цепочке, а затем выполнить их единообразно. Подходит для сценариев «отправить несколько сообщений за один раз».

### Вход в режим построения

Вызов `.Build()` перед методом отправки возвращает `SendBuilder`. После этого методы отправки (Text/Image и т.д.) больше не выполняются немедленно, а накапливаются в намерениях отправки:

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # Вход в режим построения
                 .Text("第一句")
                 .Image("pic.jpg")
                 .Text("第二句")
                 .send_all())                 # Единое выполнение
# results = [Результат Text, Результат Image, Результат Text]
```

`.send_all()` возвращает `asyncio.Task`, после await получается список результатов (в порядке намерений).

### Параллельное и последовательное выполнение

По умолчанию выполняется **параллельно** (конкурентная отправка, общее время примерно равно самому медленному сообщению). Для гарантии порядка прибытия сообщений вызывайте `.Sequential()`:

```python
# Последовательное: отправка по очереди
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("先发这个").Text("再发这个")
       .send_all())

# Параллельное (по умолчанию, можно вызвать явно)
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("并发1").Text("并发2")
       .send_all())
```

### Продолжение при неудаче и повторная попытка

Массовое выполнение использует стратегию **продолжения при неудаче**: сбой одной записи не прерывает отправку других. При использовании `.Retry()` неудачные записи автоматически повторяются (повторная попытка применяется к отдельной записи, а не ко всей партии):

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # Повторить 2 раза для каждой записи
       .Text("可能失败的").Image("也可能失败的")
       .send_all())
```

### Правила и обратные вызовы для целой партии

Правила единообразно применяются ко всей партии:

| Метод | Описание |
|--------|----------|
| `.Timeout(seconds)` | Таймаут для отдельной отправки каждой записи |
| `.Retry(times)` | Повторная попытка для каждой записи отдельно (продолжение при неудаче) |
| `.Defer(seconds)` | Отложенная отправка всей партии |
| `.Hook(callback)` | Срабатывает после полного успеха партии, принимает список `results` |
| `.OnError(callback)` | Срабатывает, когда в партии есть неудачи, принимает `BatchContext` |
| `.OnProgress(callback)` | Срабатывает при завершении каждой записи, принимает `BatchContext` |

```python
def on_progress(ctx):
    print(f"Прогресс: {ctx.completed}/{ctx.total}, Успех {ctx.succeeded}, Ошибки {ctx.failed}")

async def on_error(ctx):
    print(f"В партии {ctx.failed} записей не удалось отправить")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("Партия завершена"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` содержит: `task_id`、`total`、`completed`、`succeeded`、`failed`、`stage`、`results`、`errors`、`elapsed`、`extra`.

Возможные значения `stage`: `pending`、`sending`、`success` (все успешно)、`partial` (частично успешно)、`failed` (все неудачно).

### Наследование модификаторов и правил

Модификаторы At/AtAll/Reply и правила, установленные до `.Build()`, наследуются для всей партии и применяются к каждому сообщению:

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # Наследуется: каждое сообщение помечено @789
       .Build()
       .Retry(2)                         # Наследуется + добавлено: повторить каждое отдельно
       .Text("@你的通知")
       .Image("公告图")
       .send_all())
```

В Build можно все еще добавлять модификаторы (действуют на всю партию):

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # Добавить @, действует на всю партию
       .Text("@多人")
       .send_all())
```

### Фоновое выполнение

Как и для отдельной отправки, `.send_all()` возвращает Task, не обязательно await, чтобы выполнить в фоне:

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("Массовая отправка завершена"))
        .Text("a").Text("b")
        .send_all())

# Не блокирует основной процесс
await do_something_else()
```

## Правила именования

### PascalCase

Все методы отправки используют верблюжий регистр:

```python
# ✅ Правильно
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# �є Ошибка
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### Платформенно-специфические методы

Не рекомендуется добавлять методы с префиксом платформы:

```python
# ✅ Рекомендуется
def Sticker(self, sticker_id: str):
    pass

# �є Не рекомендуется
def TelegramSticker(self, sticker_id: str):
    pass
```

Вместо этого используйте методы `Raw`:

```python
# ✅ Рекомендуется
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# �є Не рекомендуется
def TelegramSticker(self, ...):
    pass
```

## Возвращаемое значение

### Объект Task

Все методы отправки возвращают `asyncio.Task`:

```python
import asyncio

def Text(self, text: str):
    return asyncio.create_task(
        self._adapter.call_api(
            endpoint="/send",
            content=text,
            recvId=self._target_id,
            recvType=self._target_type
        )
    )
```

### Стандартизированные ответы

`call_api` должен возвращать стандартизированный ответ. Рекомендуется использовать методы `make_response()` / `make_error()`:

```python
async def call_api(self, endpoint: str, **params):
    try:
        result = await self._do_api_call(endpoint, **params)
        return self.make_response(
            data=result.get("data"),
            message_id=result.get("message_id", ""),
            raw=result,
        )
    except Exception as e:
        return self.make_error(message=str(e))
```

Также поддерживается ручное построение (старый способ также совместим):

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok" or "failed",
        "retcode": 0 or error_code,
        "data": {...},
        "message_id": "msg_id" or "",
        "message": "",
        "{platform}_raw": raw_response
    }
```

## Полный пример

### Базовое использование

```python
from ErisPulse.Core import adapter

my_adapter = adapter.get("myplatform")

# Отправка текста
await my_adapter.Send.To("user", "123").Text("Hello World!")

# Отправка изображения
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# Отправка файла
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### Цепочка вызовов

```python
# @ пользователя + ответ
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回复@的消息")

# @ всех + несколько модификаторов
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告消息")
```

### Нативные сообщения и построение сообщений

`Raw_ob12` — это ключевая точка входа для обратного преобразования (получение сегментов OB12 → вызов API платформы), а `MessageBuilder` — это инструмент построения цепочек сегментов сообщений, используемый с ним.

> Для полной спецификации реализации `Raw_ob12`, использования `MessageBuilder` и примеров кода см.:
> - [Спецификация методов отправки §6 Правила обратного преобразования](../../standards/send-method-spec.md#6-правила-обратного-преобразованияonebot12--платформа)
> - [Спецификация методов отправки §11 Построитель сообщений](../../standards/send-method-spec.md#11-построитель-сообщений-messagebuilder)

## Связанные документы

- [Введение в разработку адаптера](getting-started.md) — Создание адаптера
- [Основные концепции адаптера](core-concepts.md) — Понимание архитектуры адаптера
- [Рекомендации по адаптеру](best-practices.md) — Создание качественного адаптера
- [Спецификация методов отправки](../../standards/send-method-spec.md) — Полная спецификация методов отправки