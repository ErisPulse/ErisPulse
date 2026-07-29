# SendDSL: подробное описание

SendDSL — это интерфейс для отправки сообщений в стиле цепочки вызовов, предоставляемый адаптером ErisPulse.

## Основной способ использования

### 1. Указание типа и ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. Указание только ID

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

## Метод цепочки

```
Using/Account() → To() → [модификаторы] → [метод отправки]
```

## Методы отправки

Все методы отправки возвращают объект `asyncio.Task`.

### Базовые методы (реализованы в базовом классе)

Ниже перечислены стандартные методы, которые уже реализованы в базовом классе `SendDSL`, **по умолчанию делегируются в `Raw_ob12`**. Подклассам адаптера не требуется их переопределять для использования, и IDE может предложить автодополнение:

| Имя метода | Описание | Возвращаемое значение |
|--------|------|---------|
| `Text(text: str)` | Отправить текстовое сообщение | `asyncio.Task` |
| `Image(file: bytes \| str)` | Отправить изображение | `asyncio.Task` |
| `Voice(file: bytes \| str)` | Отправить голосовое (OneBot12 сегмент `audio`) | `asyncio.Task` |
| `Video(file: bytes \| str)` | Отправить видео | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | Отправить файл | `asyncio.Task` |

Адаптер может переопределить отдельный стандартный метод для предоставления платформенной логики:

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # Необходимо реализовать
        ...

    # Опционально: переопределить Text для предоставления платформенной логики
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Протокольные методы

| Имя метода | Описание | Возвращаемое значение | Обязательно |
|--------|------|---------|---------|
| `Raw_ob12(message)` | Отправить сообщение в формате OneBot12 | `asyncio.Task` | **Необходимо реализовать** |

> **Важно**: `Raw_ob12` — это основной метод адаптера, **его необходимо реализовать**. Это единая точка входа для обратного преобразования (OneBot12 → Платформа). Если не реализовано, базовый класс будет записывать error в лог и возвращать стандартный ответ об ошибке (`status: "failed"`, `retcode: 10002`). Стандартные методы (`Text`, `Image` и т.д.) по умолчанию делегируют в `Raw_ob12`.

### Платформенные специфические методы

Адаптер может добавлять специфичные для платформы методы отправки в подклассе `Send` (они будут распознаваться через `event.supports()` / `event.available_methods()`):

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Платформенные специфические методы
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## Модификаторы

Модификаторы возвращают `self` для поддержки цепочного вызова.

### Метод At

```python
# @ одного пользователя
await adapter.Send.To("group", "123").At("456").Text("Привет")

# @ нескольких пользователей
await adapter.Send.To("group", "123").At("456").At("789").Text("Всем привет")
```

### Метод AtAll

```python
# @ всех участников
await adapter.Send.To("group", "123").AtAll().Text("Всем привет")
```

### Метод Reply

```python
# Ответить на сообщение
await adapter.Send.To("group", "123").Reply("msg_id").Text("Содержимое ответа")
```

### Комбинированные модификаторы

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("Ответить на @"
```

### Платформенные специфические модификаторы

Помимо встроенных `At`/`AtAll`/`Reply`, адаптер может определять **платформенные специфические модификаторы**. Такие методы **должны просто возвращать `self`** и не требуют никаких декораторов — фреймворк распознает их автоматически:

- Возвращает `self` (экземпляр SendDSL) → модификатор, не запускает отправку/обработчики жизненного цикла, цепочка продолжается
- Возвращает `Task`/`Awaitable` → метод отправки

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Модификатор: возвращает self, не отправляет
    def Expire(self, seconds: int):
        self._expire = seconds
        return self

    def ForMember(self, user_id: str):
        self._member = user_id
        return self

    # Метод отправки: возвращает Task, зависит от состояния, установленного модификаторами
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

Пример использования:

```python
# Модификаторы можно накладывать последовательно
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("Контент панели")
```

## Использование модификаторов в классе-обертке Event

Метод `event.reply()` по умолчанию раскрывает только встроенные модификаторы: `at_sender`/`at_users`/`at_all`/`quote`. Для использования платформенных специфических модификаторов есть два способа:

### Способ 1: параметр `via` у reply()

Подходит для небольшого количества известных модификаторов:

```python
await event.reply("Содержимое панели", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

`via` — это список, каждый элемент может быть:

| Формат | Эквивалент цепочного вызова |
|------|-------------|
| `"Name"` | `.Name()` |
| `("Name", arg1, arg2)` | `.Name(arg1, arg2)` |
| `("Name", (arg1,), {kw: val})` | `.Name(arg1, kw=val)` |

### Способ 2: event.send_chain()

Подходит для **последовательного применения нескольких модификаторов** или **действий без параметра контента** (например, отмена, удаление). `send_chain()` возвращает настроенную цепочку отправки с `To`/`Using`, к которой можно свободно добавлять любые модификаторы и методы отправки:

```python
# Платформенный специфический модификатор + отправка панели
await event.send_chain().Expire(3600).Board("Панель истечет через час")

# Последовательное применение нескольких модификаторов
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("Контент панели", content_type="markdown"))

# Встроенные модификаторы также доступны
await event.send_chain().At("123").Reply("msg_id").Text("привет")

# Действие без параметра контента
await event.send_chain().DismissBoard()
```

> `send_chain()` возвращает полный экземпляр SendDSL, поэтому **все возможности цепочек доступны** — не только модификаторы, но и правила отправки и пакетное построение:

```python
# Правила отправки: повтор попытки + таймаут + колбэк успеха
await (event.send_chain()
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Отправка успешна"))
       .Text("Надежная отправка"))

# Отложенная отправка + платформенный модификатор + панель
await event.send_chain().Defer(5).Expire(3600).Board("Отложенная панель")

# Режим пакетного построения
results = await (event.send_chain()
                 .Build()
                 .Text("Первая фраза").Image("pic.jpg").Text("Вторая фраза")
                 .send_all())
```

## Управление аккаунтами

### Метод Using

`Using()` используется для указания аккаунта, от которого будет отправлено сообщение. Передаваемый идентификатор будет сопоставлен методом `_resolve_account()` с учетом следующего приоритета:

1. **Имя аккаунта** — ключ из конфигурации (например, `"default"`, `"bot1"`)
2. **bot_id, внедренный во время выполнения** — идентификатор, автоматически внедряемый при преобразовании события
3. **Любое строковое поле** — другие строковые поля в конфигурации
4. **Резервный вариант** — первый включенный аккаунт

```python
# Использование имени аккаунта
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

### Не ожидать результата

```python
# Сообщение будет отправлено в фоне
task = adapter.Send.To("user", "123").Text("Hello")

# Продолжить выполнение других операций
# ...
```

### Ожидание результата

```python
# Получить результат напрямую через await
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"Результат отправки: {result}")

# Сначала сохранить Task, затем ждать
task = adapter.Send.To("user", "123").Text("Hello")
# ... другие операции ...
result = await task
```

## Система правил отправки

SendDSL内置了一套 правил для отправки, которые применяются унифицированно при финальной отправке. Правила покрывают распространенные сценарии: контроль таймаута, автоматические повторы, колбэки успеха, отложенная отправка, приоритетная отбраковка, мониторинг прогресса.

Методы правил **возвращают `self`** (как и At/AtAll/Reply) и должны вызываться **до** методов отправки (Text/Image и т.д.). Правила распространяются на новые экземпляры, созданные через `To`/`Using`/`Account`.

### Обзор методов правил

| Метод | Описание |
|--------|------|
| `.Hook(callback)` | Выполняется после успешной отправки (может вызываться несколько раз, последовательно) |
| `.Retry(times=1)` | Автоматическая перезапись N раз при неудаче (всего N+1 попыток) |
| `.Timeout(seconds)` | Таймаут одной отправки; по истечении отменяет текущую попытку (можно комбинировать с Retry) |
| `.Defer(seconds=1.0)` | Отложенная отправка (внутри процесса, без сохранения) |
| `.Priority(level, drop_if_busy=False)` | Установка приоритета; при переполнении можно выбрасывать |
| `.OnProgress(callback)` | Колбэки прогресса на этапах (передает `SendContext`) |
| `.OnError(callback)` | Колбэк об ошибке при окончательном провале (срабатывает только один раз) |

### Логика после успешной отправки (Hook)

```python
# Синхронный колбэк
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"Отправка успешна, ID сообщения: {r['message_id']}"))
       .Text("Привет"))

# Асинхронный колбэк
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("Вычесть баллы")
```

Hook выполняется только при окончательной успешной отправке (включая успешные повторы); неудача, таймаут или отмена не запускают его.

### Автоматический повтор (Retry)

```python
# Повторить 2 раза после первой неудачи, всего 3 попытки
result = await adapter.Send.To("user", "123").Retry(2).Text("С повтором")
```

Условия для перезапуска: выбрасывание исключения при отправке, превышение таймаута отправки или возвращение `status == "failed"` в ответе.

### Автоматический таймаут (Timeout)

```python
# Отмена, если одна отправка занимает более 10 секунд
await adapter.Send.To("user", "123").Timeout(10).Text("С таймаутом")

# Таймаут + повторы: каждая попытка 10 секунд, максимум 3 раза
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("Повтор с таймаутом")
```

### Мониторинг прогресса (OnProgress / OnError)

```python
def on_progress(ctx):
    print(f"Этап: {ctx.stage}, Попытка: {ctx.attempt + 1}/{ctx.max_attempts}, Время: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  Ошибка: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"Отправка для {ctx.target_id} не удалась: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("Мониторинг"))
```

`SendContext` содержит поля: `task_id`、`platform`、`method`、`target_type`、`target_id`、`bot_id`、`stage`、`attempt`、`max_attempts`、`started_at`、`finished_at`、`elapsed`、`error`、`result`、`extra`.

Возможные значения `stage`: `pending`、`sending`、`retrying`、`success`、`failed`、`timeout`、`cancelled`、`dropped`.

### Отложенная отправка (Defer)

```python
# Отправить через 5 секунд
await adapter.Send.To("user", "123").Defer(5).Text("Задержанное сообщение")
```

> Примечание: задержка — это таймер внутри процесса; перезапуск процесса приведет к потере, сохранение не предусмотрено.

### Приоритет и сброс при переполнении (Priority)

```python
# Сообщение низкого приоритета, сбрасывается при переполнении очереди
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("Уведомление, которое можно проигнорировать"))
# Если было сброшено, result["status"] == "failed"
```

При включенном `drop_if_busy`, когда количество активных задач отправки превышает порог (по умолчанию 64), отправка просто отменяется. Глобальный порог можно настроить через `.PriorityThreshold(n)`.

### Комбинация правил и фоновое выполнение

```python
# Не блокирует основной поток, правила работают
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("Отправка успешна!"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("Привет"))

# Продолжить выполнение других операций
await handle_next_action()
```

### Распространение правил

Правила распространяются на новые экземпляры, созданные через `To`/`Using`/`Account`, чтобы избежать потери правил в цепочке:

```python
# Правила, установленные до To, также распространяются на экземпляр, созданный To
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send по-прежнему содержит Retry(3) и Timeout(10)
await send.Text("hi")
```

Правила независимы между разными экземплярами (списки hooks делаются глубоким копированием).

## Режим пакетного построения (Build)

Помимо одноэлементного режима, SendDSL поддерживает режим пакетного построения: запись нескольких методов отправки в одну цепочку с последующим единым выполнением. Подходит для сценариев "отправить сразу несколько сообщений".

### Вход в режим построения

Вызов `.Build()` перед методами отправки возвращает `SendBuilder`. После этого методы отправки (Text/Image и т.д.) больше не выполняются немедленно, а накапливаются как намерения отправки:

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # Вход в режим построения
                 .Text("Первая фраза")
                 .Image("pic.jpg")
                 .Text("Вторая фраза")
                 .send_all())                 # Единое выполнение
# results = [Результат Text, Результат Image, Результат Text]
```

`.send_all()` возвращает `asyncio.Task`; после await вы получаете список результатов (в порядке намерений).

### Параллельное и последовательное выполнение

По умолчанию выполняется **параллельно** (отправка конвейером, общее время примерно равно самой долгой). Для гарантии порядка доставки следует вызвать `.Sequential()`:

```python
# Последовательное: отправлять по порядку
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("Сначала это").Text("Потом это")
       .send_all())

# Параллельное (по умолчанию, можно вызвать явно)
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("Конкурентное1").Text("Конкурентное2")
       .send_all())
```

### Продолжение после ошибки и перезапись

Пакетное выполнение использует стратегию **продолжения после ошибки**: сбой одной записи не прерывает отправку остальных. В сочетании с `.Retry()`, неудачные записи автоматически перезапускаются (перезапись применяется к записи, а не ко всей партии):

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # Каждая запись перезапускается 2 раза
       .Text("Возможно упадет").Image("Возможно упадет тоже")
       .send_all())
```

### Правила и колбэки для всей партии

Правила применяются единообразно ко всей партии:

| Метод | Описание |
|--------|------|
| `.Timeout(seconds)` | Таймаут одной отправки |
| `.Retry(times)` | Повтор для каждой записи (продолжение после ошибки) |
| `.Defer(seconds)` | Отложенная отправка всей партии |
| `.Hook(callback)` | Срабатывает, когда вся партия успешно отправлена, принимает список `results` |
| `.OnError(callback)` | Срабатывает при наличии неудач в партии, принимает `BatchContext` |
| `.OnProgress(callback)` | Срабатывает при завершении каждой записи, принимает `BatchContext` |

```python
def on_progress(ctx):
    print(f"Прогресс: {ctx.completed}/{ctx.total}, Успешно {ctx.succeeded}, Ошибок {ctx.failed}")

async def on_error(ctx):
    print(f"В партии {ctx.failed} неудач")

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

Модификаторы и правила At/AtAll/Reply, установленные до `.Build()`, наследуются и применяются к каждой записи:

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # Наследуется: каждая запись @789
       .Build()
       .Retry(2)                         # Наследование + добавление: каждая запись перезапускается
       .Text("@Твое уведомление")
       .Image("Изображение объявления")
       .send_all())
```

После входа в Build модификаторы все еще можно добавлять (применяются ко всей партии):

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # Добавить @, применить ко всей партии
       .Text("@Много людей")
       .send_all())
```

### Фоновое выполнение

Так же, как и при одноэлементной отправке, `.send_all()` возвращает Task, его можно не await, чтобы он выполнялся в фоне:

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("Пакетная отправка завершена"))
        .Text("a").Text("b")
        .send_all())

# Не блокирует основной поток
await do_something_else()
```

## Соглашения об именовании

### Именование PascalCase

Все методы отправки используют PascalCase:

```python
# ✅ Правильно
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# �і Ошибка
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### Платформенные специфические методы

Не рекомендуется добавлять методы с префиксом платформы:

```python
# ✅ Рекомендуется
def Sticker(self, sticker_id: str):
    pass

# �і Не рекомендуется
def TelegramSticker(self, sticker_id: str):
    pass
```

Лучше использовать метод `Raw`:

```python
# ✅ Рекомендуется
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# �і Не рекомендуется
def TelegramSticker(self, ...):
    pass
```

## Возвращаемые значения

### Объект Task

Все методы отправки возвращают `asyncio.Task`. Адаптеру нужно реализовать только `Raw_ob12`; стандартные методы (Text/Image и т.д.) по умолчанию делегируют ему:

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

# Text/Image/Voice/File наследуются от базового класса и делегируют в Raw_ob12
# Если нужно переопределить стандартный метод, достаточно вернуть asyncio.Task:
# def Text(self, text: str):
#     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Стандартизированный ответ

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

Поддерживается и ручное построение (старый способ совместим):

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

### Цепочное использование

```python
# @ пользователь + ответ
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("Ответ @"
```

### Исходные сообщения и построение сообщений

`Raw_ob12` — это ключевая точка входа для обратного преобразования (получение сегментов OB12 → вызов платформенного API), а `MessageBuilder` — вспомогательный инструмент построения цепочек сегментов.

> Полная спецификация `Raw_ob12`, использование `MessageBuilder` и примеры кода см.:
> - [Спецификация методов отправки §6 Спецификация обратного преобразования](../../standards/send-method-spec.md#6-спецификация-обратного-преобразования-onebot12--платформа)
> - [Спецификация методов отправки §11 Построитель сообщений](../../standards/send-method-spec.md#11-построитель-сообщений-messagebuilder)

## Ссылки

- [Введение в разработку адаптера](getting-started.md) — создание адаптера
- [Основные концепции адаптера](core-concepts.md) — понимание архитектуры адаптера
- [Рекомендации по адаптеру](best-practices.md) — разработка качественного адаптера
- [Спецификация методов отправки](../../standards/send-method-spec.md) — полная спецификация методов отправки