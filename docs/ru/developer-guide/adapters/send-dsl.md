# Подробное руководство по SendDSL

SendDSL — это интерфейс отправки сообщений в стиле цепочки вызовов, предоставляемый адаптером ErisPulse.

## Основные способы вызова

### 1. Указание типа и идентификатора

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. Указание только идентификатора

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. Указание аккаунта отправки

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

Все методы отправки возвращают объект `asyncio.Task`.

### Основные методы (встроенные в базовый класс)

Следующие стандартные методы реализованы в базовом классе `SendDSL` и **по умолчанию делегируются на `Raw_ob12`**. Подклассы адаптеров не обязаны повторно реализовывать их, и IDE будет их подсказывать:

| Название метода | Описание | Возвращаемое значение |
|-----------------|----------|-----------------------|
| `Text(text: str)` | Отправка текстового сообщения | `asyncio.Task` |
| `Image(file: bytes \| str)` | Отправка изображения | `asyncio.Task` |
| `Voice(file: bytes \| str)` | Отправка голосового сообщения (сегмент `audio` OneBot12) | `asyncio.Task` |
| `Video(file: bytes \| str)` | Отправка видео | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | Отправка файла | `asyncio.Task` |

Адаптер может переопределить отдельный стандартный метод для предоставления платформенно-специфической логики:

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # Обязательно реализовать
        ...

    # Необязательно: переопределить Text для предоставления платформенно-специфической логики
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Методы протокола

| Название метода | Описание | Возвращаемое значение | Обязательно |
|-----------------|----------|-----------------------|------------|
| `Raw_ob12(message)` | Отправка сообщения в формате OneBot12 | `asyncio.Task` | **Обязательно реализовать** |

> **Важно**: `Raw_ob12` — это основной метод адаптера, **обязательно реализовать**. Это единый вход для обратного преобразования (OneBot12 → платформа). Если не реализован, базовый класс будет записывать ошибку и возвращать стандартный ответ об ошибке (`status: "failed"`, `retcode: 10002`). Стандартные методы (`Text`, `Image` и т.д.) по умолчанию делегируются на `Raw_ob12`.

### Платформенно-специфические методы

Адаптер может добавить платформенно-специфические методы отправки в подкласс `Send` (они будут распознаваться `event.supports()` / `event.available_methods()`):

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Платформенно-специфический метод
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## Модификаторы

Модификаторы возвращают `self` для поддержки цепочечных вызовов.

### Метод At

```python
# @одного пользователя
await adapter.Send.To("group", "123").At("456").Text("Привет")

# @нескольких пользователей
await adapter.Send.To("group", "123").At("456").At("789").Text("Приветствую вас")
```

### Метод AtAll

```python
# @всех участников
await adapter.Send.To("group", "123").AtAll().Text("Всем привет")
```

### Метод Reply

```python
# Ответ на сообщение
await adapter.Send.To("group", "123").Reply("msg_id").Text("Содержание ответа")
```

### Комбинированные модификаторы

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("Ответ на сообщение с упоминанием")
```

## Управление аккаунтами

### Метод Using

`Using()` используется для указания аккаунта отправки. Переданный идентификатор будет сопоставлен через `_resolve_account()` по следующему приоритету:

1. **Имя аккаунта** — ключ из конфигурации (например, `"default"`, `"bot1"`)
2. **bot_id, вставленный во время выполнения** — идентификатор, автоматически вставленный из события
3. **Любое строковое поле** — другие строковые поля в конфигурации
4. **Резервный вариант** — первый включенный аккаунт

```python
# Использование имени аккаунта
await adapter.Send.Using("account1").To("user", "123").Text("Привет")

# Использование bot_id (self.user_id из события)
await adapter.Send.Using("bot_123").To("user", "123").Text("Привет")
```

### Метод Account

Метод `Account` эквивалентен `Using`:

```python
await adapter.Send.Account("account1").To("user", "123").Text("Привет")
```

## Асинхронная обработка

### Отправка без ожидания результата

```python
# Сообщение отправляется в фоновом режиме
task = adapter.Send.To("user", "123").Text("Привет")

# Продолжение выполнения других операций
# ...
```

### Ожидание результата

```python
# Непосредственно await для получения результата
result = await adapter.Send.To("user", "123").Text("Привет")
print(f"Результат отправки: {result}")

# Сохранение Task и ожидание позже
task = adapter.Send.To("user", "123").Text("Привет")
# ... другие операции ...
result = await task
```

## Система отправки правил

SendDSL содержит встроенную систему правил отправки через декораторы, которые можно добавлять цепочечными методами и применять при отправке. Правила охватывают распространённые сценарии: контроль таймаута, автоматическая повторная отправка, успешный обратный вызов, отложенная отправка, приоритет и отбрасывание, мониторинг прогресса.

Методы правил **возвращают self** (как At/AtAll/Reply), и их необходимо вызывать до методов отправки (Text/Image и т.д.). Правила распространяются на новые экземпляры, созданные с помощью `To`/`Using`/`Account`.

### Список методов правил

| Метод | Описание |
|--------|----------|
| `.Hook(callback)` | Вызывается после успешной отправки (можно вызывать несколько раз, выполняется по порядку) |
| `.Retry(times=1)` | Автоматическая повторная отправка при неудаче N раз (включая первое, всего N+1 попыток) |
| `.Timeout(seconds)` | Таймаут при отправке, отмена текущей попытки при истечении времени (можно комбинировать с Retry) |
| `.Defer(seconds=1.0)` | Отложенная отправка (внутри процесса, не сохраняется) |
| `.Priority(level, drop_if_busy=False)` | Установка приоритета; при накоплении можно отбросить |
| `.OnProgress(callback)` | Обратный вызов при каждом этапе (передаётся `SendContext`) |
| `.OnError(callback)` | Обратный вызов при финальной ошибке (вызывается только один раз) |

### Логика после успешной отправки (Hook)

```python
# Синхронный обратный вызов
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"Успешная отправка, ID сообщения: {r['message_id']}"))
       .Text("Привет"))

# Асинхронный обратный вызов
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("Списание баллов")
```

Hook вызывается только при успешной отправке (включая повторную); при неудаче, таймауте, отмене не вызывается.

### Автоматическая повторная отправка при неудаче (Retry)

```python
# При первой неудаче повторить 2 раза, всего 3 попытки
result = await adapter.Send.To("user", "123").Retry(2).Text("С повтором")
```

Повторная отправка запускается при следующих условиях: исключение при отправке, таймаут, возврат `status == "failed"`.

### Автоматическая отмена при таймауте (Timeout)

```python
# Если отправка занимает более 10 секунд, отменить
await adapter.Send.To("user", "123").Timeout(10).Text("С таймаутом")

# Таймаут + повтор: каждая попытка 10 секунд, максимум 3 попытки
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("Таймаут с повтором")
```

### Мониторинг прогресса (OnProgress / OnError)

```python
def on_progress(ctx):
    print(f"Этап: {ctx.stage}, Попытка: {ctx.attempt + 1}/{ctx.max_attempts}, Время: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  Ошибка: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"Отправка на {ctx.target_id} не удалась: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("Мониторинг"))
```

`SendContext` содержит следующие поля: `task_id`, `platform`, `method`, `target_type`, `target_id`, `bot_id`, `stage`, `attempt`, `max_attempts`, `started_at`, `finished_at`, `elapsed`, `error`, `result`, `extra`.

Возможные значения `stage`: `pending`, `sending`, `retrying`, `success`, `failed`, `timeout`, `cancelled`, `dropped`.

### Отложенная отправка (Defer)

```python
# Отправить через 5 секунд
await adapter.Send.To("user", "123").Defer(5).Text("Отложенное сообщение")
```

> Примечание: задержка осуществляется внутри процесса, при перезапуске процесса теряется, не сохраняется.

### Приоритет и отбрасывание при накоплении (Priority)

```python
# Низкоприоритетное сообщение, при накоплении в очереди автоматически отбрасывается
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("Уведомление, которое можно отбросить"))
# Если отброшено, result["status"] == "failed"
```

При включении `drop_if_busy`, если количество задач в очереди превышает порог (по умолчанию 64), отправка отменяется. Порог можно изменить с помощью `.PriorityThreshold(n)`.

### Комбинация правил и фоновая отправка

```python
# Не блокировать основной поток, правила всё равно применяются
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("Успешная отправка!"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("Привет"))

# Продолжение выполнения других операций
await handle_next_action()
```

### Распространение правил

Правила распространяются на новые экземпляры, созданные с помощью `To`/`Using`/`Account`, избегая потери правил в цепочечных вызовах:

```python
# Правила, установленные до To, также распространяются на созданный экземпляр
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send по-прежнему содержит Retry(3) и Timeout(10)
await send.Text("hi")
```

Правила отдельных экземпляров независимы (список hooks глубоко копируется).

## Режим построения пакетов (Build)

Помимо режима отправки одного сообщения, SendDSL поддерживает режим построения пакетов: несколько методов отправки в одной цепочке, которые выполняются единовременно. Подходит для отправки нескольких сообщений за один раз.

### Вход в режим построения

Вызов `.Build()` перед методами отправки возвращает `SendBuilder`. После этого методы отправки (Text/Image и т.д.) не выполняются немедленно, а накапливаются в виде отправочных намерений:

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # Вход в режим построения
                 .Text("Первое предложение")
                 .Image("pic.jpg")
                 .Text("Второе предложение")
                 .send_all())                 # Единое выполнение
# results = [результат Text, результат Image, результат Text]
```

`.send_all()` возвращает `asyncio.Task`, ожидание которого дает список результатов (в порядке намерений).

### Параллельная и последовательная отправка

По умолчанию отправка выполняется **параллельно** (одновременно, общее время примерно равно самому медленному). При необходимости сохранения порядка отправки вызывается `.Sequential()`:

```python
# Последовательно: отправка по очереди
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("Сначала это").Text("Потом это")
       .send_all())

# Параллельно (по умолчанию, можно явно указать)
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("Параллельно1").Text("Параллельно2")
       .send_all())
```

### Продолжение при неудаче и повторная отправка

При пакетной отправке используется стратегия **продолжения при неудаче**: неудача одной отправки не прерывает отправку других. При использовании `.Retry()` неудачные отправки будут автоматически повторяться (повтор применяется к каждой отдельной отправке, а не к пакету):

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # Каждая отправка повторяется 2 раза
       .Text("Возможно неудача").Image("Тоже возможно неудача")
       .send_all())
```

### Правила и обратные вызовы для всего пакета

Правила применяются ко всему пакету:

| Метод | Описание |
|--------|----------|
| `.Timeout(seconds)` | Таймаут для каждой отправки |
| `.Retry(times)` | Повтор отправки для каждой отправки (продолжение при неудаче) |
| `.Defer(seconds)` | Отложенная отправка всего пакета |
| `.Hook(callback)` | Вызывается после успешной отправки всего пакета, получает список результатов |
| `.OnError(callback)` | Вызывается при наличии неудачных отправок, получает `BatchContext` |
| `.OnProgress(callback)` | Вызывается при завершении каждой отправки, получает `BatchContext` |

```python
def on_progress(ctx):
    print(f"Прогресс: {ctx.completed}/{ctx.total}, Успешно {ctx.succeeded}, Неудачно {ctx.failed}")

async def on_error(ctx):
    print(f"В пакете {ctx.failed} неудачных отправок")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("Пакет отправлен"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` содержит: `task_id`, `total`, `completed`, `succeeded`, `failed`, `stage`, `results`, `errors`, `elapsed`, `extra`.

Возможные значения `stage`: `pending`, `sending`, `success` (все успешно), `partial` (частично успешно), `failed` (все неудачно).

### Наследование модификаторов и правил

Модификаторы и правила, установленные до `.Build()`, наследуются всеми отправками в пакете:

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # Наследуется: каждая отправка упоминает 789
       .Build()
       .Retry(2)                         # Наследуется + добавляется: каждая отправка повторяется
       .Text("@ваше уведомление")
       .Image("изображение объявления")
       .send_all())
```

После входа в Build можно добавлять модификаторы (они действуют на весь пакет):

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # Добавление упоминаний, действует на весь пакет
       .Text("@многим")
       .send_all())
```

### Фоновая отправка

Как и в случае с отправкой одного сообщения, `.send_all()` возвращает Task, который можно не ожидать, чтобы отправка происходила в фоне:

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("Пакет отправлен"))
        .Text("a").Text("b")
        .send_all())

# Не блокирует основной поток
await do_something_else()
```

## Нормы именования

### Именование в стиле PascalCase

Все методы отправки используют стиль PascalCase:

```python
# ✅ Правильно
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ Неправильно
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### Платформенно-специфические методы

Не рекомендуется добавлять методы с платформенным префиксом:

```python
# ✅ Рекомендуется
def Sticker(self, sticker_id: str):
    pass

# ❌ Не рекомендуется
def TelegramSticker(self, sticker_id: str):
    pass
```

Вместо этого используйте метод `Raw`:

```python
# ✅ Рекомендуется
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ Не рекомендуется
def TelegramSticker(self, ...):
    pass
```

## Возвращаемые значения

### Объект Task

Все методы отправки возвращают `asyncio.Task`. Адаптер должен реализовать только `Raw_ob12`, стандартные методы (Text/Image и т.д.) по умолчанию делегируются на него:

```python
import asyncio

def Raw_ob12(self, message, **kwargs):
    async def _do_send():
        segments = self._apply_modifiers(message)
        return await self._adapter.call_api(
            endpoint="/send_message",
            message=segments,
            **self.send_context,
            **kwargs,
        )
    return asyncio.create_task(_do_send())

# Text/Image/Voice/Video/File унаследованы от базового класса и автоматически делегируются на Raw_ob12
# Если нужно переопределить стандартный метод, верните asyncio.Task:
# def Text(self, text: str):
#     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Стандартизированный ответ

Метод `call_api` должен возвращать стандартизированный ответ. Рекомендуется использовать методы `make_response()` / `make_error()`:

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

Также поддерживается ручное построение (старый способ по-прежнему совместим):

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

### Основное использование

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

### Цепочечные вызовы

```python
# @пользователя + ответ
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("Ответ на сообщение с упоминанием")

# @всех + несколько модификаторов
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("Объявление")
```

### Сырые сообщения и построение сообщений

`Raw_ob12` — это основной вход для обратного преобразования (получение сегментов сообщения OB12 → вызов API платформы), `MessageBuilder` — цепочечный инструмент для построения сегментов сообщений, используемый вместе с ним.

> Полная спецификация реализации `Raw_ob12`, использование `MessageBuilder` и примеры кода см. в:
> - [Спецификация методов отправки §6 Спецификация обратного преобразования](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [Спецификация методов отправки §11 Построитель сообщений](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## Связанные документы

- [Введение в разработку адаптеров](getting-started.md) - Создание адаптера
- [Основные понятия адаптера](core-concepts.md) - Понимание архитектуры адаптера
- [Лучшие практики разработки адаптеров](best-practices.md) - Создание качественных адаптеров
- [Спецификация методов отправки](../../standards/send-method-spec.md) - Полная спецификация методов отправки