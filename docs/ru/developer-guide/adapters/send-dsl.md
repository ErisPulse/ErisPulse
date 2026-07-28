# SendDSL Подробное описание

SendDSL — это интерфейс для отправки сообщений в стиле цепного вызова, предоставляемый адаптером ErisPulse.

## Базовый способ вызова

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
Using/Account() → To() → [Методы-модификаторы] → [Методы отправки]
```

## Методы отправки

Все методы отправки возвращают объект `asyncio.Task`.

### Базовые методы (встроены в базовый класс)

Следующие стандартные методы уже реализованы в базовом классе `SendDSL`, **по умолчанию делегируются `Raw_ob12`**. Подклассы адаптера могут использовать их напрямую, не реализуя заново, и IDE сможет их автодополнить:

| Имя метода | Описание | Возвращаемое значение |
|--------|------|---------|
| `Text(text: str)` | Отправка текстового сообщения | `asyncio.Task` |
| `Image(file: bytes \| str)` | Отправка изображения | `asyncio.Task` |
| `Voice(file: bytes \| str)` | Отправка голосового (сегмент `audio` OneBot12) | `asyncio.Task` |
| `Video(file: bytes \| str)` | Отправка видео | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | Отправка файла | `asyncio.Task` |

Адаптер может переопределить отдельные стандартные методы для предоставления специфической для платформы логики:

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # Необходимо реализовать
        ...

    # Необязательно: переопределить Text для платформенной логики
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### Методы протокола

| Имя метода | Описание | Возвращаемое значение | Обязательно |
|--------|------|---------|---------|
| `Raw_ob12(message)` | Отправка сообщения в формате OneBot12 | `asyncio.Task` | **Обязательно реализовать** |

> **Важно**：`Raw_ob12` — это основной метод адаптера, **обязательно должен быть реализован**. Это единая точка входа для обратного преобразования (OneBot12 → Платформа). Если не реализовано, базовый класс запишет в лог ошибку и вернет стандартный ответ об ошибке (`status: "failed"`, `retcode: 10002`). Стандартные методы (`Text`, `Image` и т.д.) по умолчанию делегируют `Raw_ob12`.

### Платформенные специфические методы

Адаптер может добавлять платформенные специфические методы отправки в подкласс `Send` (будут определяться через `event.supports()` / `event.available_methods()`):

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Платформенные специфические методы
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## Методы-модификаторы

Методы-модификаторы возвращают `self` для поддержки цепного вызова.

### Метод At

```python
# @один пользователь
await adapter.Send.To("group", "123").At("456").Text("Привет")

# @несколько пользователей
await adapter.Send.To("group", "123").At("456").At("789").Text("Здравствуйте, все")
```

### Метод AtAll

```python
# @всем участникам
await adapter.Send.To("group", "123").AtAll().Text("Всем привет")
```

### Метод Reply

```python
# Ответ на сообщение
await adapter.Send.To("group", "123").Reply("msg_id").Text("Ответное сообщение")
```

### Комбинированные модификаторы

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("Ответ на сообщение @")
```

### Платформенные специфические методы-модификаторы

Помимо встроенных `At`/`AtAll`/`Reply`, адаптер может определять **платформенные специфические методы-модификаторы**. Такие методы должны **возвращать только `self`**, без использования декораторов — фреймворк распознает их автоматически:

- Возвращает `self` (экземпляр SendDSL) → Метод-модификатор, не запускает отправку/обработку событий жизненного цикла, цепочка продолжается
- Возвращает `Task`/`Awaitable` → Метод отправки

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # Метод-модификатор: возвращает self, не отправляет
    def Expire(self, seconds: int):
        self._expire = seconds
        return self

    def ForMember(self, user_id: str):
        self._member = user_id
        return self

    # Метод отправки: возвращает Task, использует состояния, заданные модификаторами
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

Использование:

```python
# Методы-модификаторы можно цеплять последовательно
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("Содержание панели")
```

## Использование методов-модификаторов в классе Event Wrapper

Метод `event.reply()` по умолчанию раскрывает только встроенные модификаторы, такие как `at_sender`/`at_users`/`at_all`/`quote`. Чтобы использовать платформенные специфические методы-модификаторы, есть два способа:

### Способ 1: параметр `via` в reply()

Подходит для небольшого количества известных методов-модификаторов:

```python
await event.reply("Содержание панели", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

Параметр `via` — это список, каждый элемент может быть:

| Форма | Эквивалентная цепочка вызовов |
|------|-------------|
| `"Имя"` | `.Имя()` |
| `("Имя", arg1, arg2)` | `.Имя(arg1, arg2)` |
| `("Имя", (arg1,), {kw: val})` | `.Имя(arg1, kw=val)` |

### Способ 2: event.send_chain()

Подходит для **последовательного применения нескольких методов-модификаторов** или **действий без параметра содержимого** (например, отмена отправки, удаление). `send_chain()` возвращает цепочку отправки с настроенным `To`/`Using`, к которой можно свободно добавлять любые методы-модификаторы и методы отправки:

```python
# Платформенный специфический метод-модификатор + отправка панели
await event.send_chain().Expire(3600).Board("Истекает через час")

# Последовательное применение нескольких методов-модификаторов
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("Содержание панели", content_type="markdown"))

# Встроенные методы-модификаторы тоже доступны
await event.send_chain().At("123").Reply("msg_id").Text("привет")

# Действие без параметра содержимого
await event.send_chain().DismissBoard()
```

## Управление учетными записями

### Метод Using

`Using()` используется для указания учетной записи для отправки сообщения. Передаваемый идентификатор сопоставляется с помощью `_resolve_account()` в следующем порядке приоритета:

1. **Имя учетной записи** — имя ключа в конфигурации (например, `"default"`、`"bot1"`)
2. **Инъецированный bot_id** — идентификатор, автоматически инъецируемый при преобразовании события
3. **Любое строковое поле** — другие строковые поля в конфигурации
4. **Фоллбэк** — первая включенная учетная запись

```python
# Использование имени учетной записи
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Использование bot_id (то есть self.user_id в событии)
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Метод Account

Метод `Account` эквивалентен `Using`:

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## Асинхронная обработка

### Не ожидание результата

```python
# Сообщение отправляется в фоне
task = adapter.Send.To("user", "123").Text("Hello")

# Продолжение выполнения других операций
# ...
```

### Ожидание результата

```python
# Прямой await для получения результата
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"Результат отправки: {result}")

# Сначала сохраняем Task, ждем позже
task = adapter.Send.To("user", "123").Text("Hello")
# ... другие операции ...
result = await task
```

## Система правил отправки

SendDSL встроил набор правил-декораторов для отправки, которые прикрепляются через цепочку методов и единообразно применяются при финальной отправке. Правила охватывают распространенные сценарии производства: управление таймаутом, повторные попытки при сбое, обратные вызовы при успехе, отложенная отправка, сброс приоритета и мониторинг прогресса.

Правила методов должны **возвращать `self`** (как `At`/`AtAll`/`Reply`) и должны вызываться перед методами отправки (`Text`/`Image` и т.д.). Правила распространяются на новые экземпляры, создаваемые `To`/`Using`/`Account`.

### Обзор методов правил

| Метод | Описание |
|--------|------|
| `.Hook(callback)` | Обратный вызов, выполняемый после успешной отправки (можно вызвать несколько раз, выполняется последовательно) |
| `.Retry(times=1)` | Автоматическая повторная попытка N раз при ошибке (всего N+1 попыток, включая первую) |
| `.Timeout(seconds)` | Таймаут для единичной отправки, при превышении текущая попытка отменяется (можно комбинировать с Retry) |
| `.Defer(seconds=1.0)` | Отложенная отправка (таймер внутри процесса, без сохранения) |
| `.Priority(level, drop_if_busy=False)` | Установка приоритета; можно сбросить при переполнении очереди |
| `.OnProgress(callback)` | Обратный вызов прогресса на этапах (передает `SendContext`) |
| `.OnError(callback)` | Обратный вызов об ошибке в случае финального сбоя (срабатывает один раз) |

### Логика после успешной отправки (Hook)

```python
# Синхронный обратный вызов
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"Успешная отправка, message_id: {r['message_id']}"))
       .Text("Привет"))

# Асинхронный обратный вызов
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("Списание баллов")
```

Hook выполняется только при окончательной успешной отправке (включая успешные попытки после повторов); сбой, таймаут, отмена не запускают его.

### Автоматическая повторная попытка при ошибке (Retry)

```python
# Повторить 2 раза после первой ошибки, всего 3 попытки
result = await adapter.Send.To("user", "123").Retry(2).Text("С повтором")
```

Условия срабатывания повтора: выброс исключения при отправке, превышение таймаута отправки или возврат ответа с `status == "failed"`.

### Автоматический таймаут и отмена (Timeout)

```python
# Отменить, если отправка занимает более 10 секунд
await adapter.Send.To("user", "123").Timeout(10).Text("С таймаутом")

# Таймаут + Повтор: по 10 секунд на попытку, максимум 3 попытки
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

Поля, содержащиеся в `SendContext`: `task_id`、`platform`、`method`、`target_type`、`target_id`、`bot_id`、`stage`、`attempt`、`max_attempts`、`started_at`、`finished_at`、`elapsed`、`error`、`result`、`extra`.

Возможные значения `stage`: `pending`、`sending`、`retrying`、`success`、`failed`、`timeout`、`cancelled`、`dropped`.

### Отложенная отправка (Defer)

```python
# Отправить через 5 секунд
await adapter.Send.To("user", "123").Defer(5).Text("Опоздавшее сообщение")
```

> Примечание: задержка — это таймер внутри процесса, при перезапуске процесса она теряется, сохранение не поддерживается.

### Приоритет и сброс при переполнении (Priority)

```python
# Низкоприоритетное сообщение, сбрасывается при переполнении очереди
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("Уведомление, которое можно отменить"))
# Если сброшено, result["status"] == "failed"
```

После включения `drop_if_busy`, когда количество активных задач отправки превышает порог (по умолчанию 64), отправка этой попытки напрямую отменяется. Глобальный порог можно настроить через `.PriorityThreshold(n)`.

### Комбинация правил и фоновой выполнения

```python
# Не блокирует основной поток, правила работают
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

Правила распространяются на новые экземпляры, создаваемые `To`/`Using`/`Account`, чтобы избежать потери правил в цепочке вызовов:

```python
# Правила, установленные до To, также распространяются на экземпляр, создаваемый To
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send все еще содержит Retry(3) и Timeout(10)
await send.Text("привет")
```

Правила нескольких экземпляров независимы друг от друга (списки hooks глубоко копируются).

## Режим пакетного построения (Build)

Помимо режима одинарной отправки, SendDSL поддерживает режим пакетного построения: запись нескольких методов отправки в одной цепочке с единым выполнением в конце. Подходит для сценариев «отправить сразу несколько сообщений».

### Вход в режим построения

Вызов `.Build()` перед методом отправки возвращает `SendBuilder`. Впоследствии методы отправки (`Text`/`Image` и т.д.) больше не выполняются немедленно, а накапливаются как намерения отправки:

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # Вход в режим построения
                 .Text("Первая фраза")
                 .Image("pic.jpg")
                 .Text("Вторая фраза")
                 .send_all())                 # Единое выполнение
# results = [Результат Text, Результат Image, Результат Text]
```

`.send_all()` возвращает `asyncio.Task`, после await получаем список результатов (в порядке намерений).

### Параллельное и последовательное выполнение

По умолчанию выполняется **параллельно** (отправка с конкурентностью, общее время примерно равно самому медленному элементу). Чтобы гарантировать порядок доставки сообщений, вызовите `.Sequential()`:

```python
# Последовательное: отправка по порядку
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("Сначала это").Text("Потом это")
       .send_all())

# Параллельное (по умолчанию, можно явно вызвать)
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("Конкурент 1").Text("Конкурент 2")
       .send_all())
```

### Продолжение при ошибке и повтор

Пакетное выполнение использует стратегию **продолжения при ошибке**: ошибка одной записи не останавливает отправку других. В сочетании с `.Retry()`, неудачные записи будут автоматически повторяться (попытка применяется к отдельной записи, а не к всей партии):

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # Каждая запись отдельно повторяет 2 раза
       .Text("Возможно упадет").Image("Возможно тоже упадет")
       .send_all())
```

### Правила и обратные вызовы для целой партии

Правила единообразно применяются ко всей партии:

| Метод | Описание |
|--------|------|
| `.Timeout(seconds)` | Таймаут для каждой отправки |
| `.Retry(times)` | Повтор для каждой отправки отдельно (продолжение при ошибке) |
| `.Defer(seconds)` | Отложенная отправка всей партии |
| `.Hook(callback)` | Срабатывает после успешного выполнения всей партии, получает список `results` |
| `.OnError(callback)` | Срабатывает, если есть ошибки в партии, получает `BatchContext` |
| `.OnProgress(callback)` | Срабатывает при завершении каждой записи, получает `BatchContext` |

```python
def on_progress(ctx):
    print(f"Прогресс: {ctx.completed}/{ctx.total}, Успешно {ctx.succeeded}, Ошибок {ctx.failed}")

async def on_error(ctx):
    print(f"В партии {ctx.failed} ошибок")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("Партия выполнена"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` содержит: `task_id`、`total`、`completed`、`succeeded`、`failed`、`stage`、`results`、`errors`、`elapsed`、`extra`.

Возможные значения `stage`: `pending`、`sending`、`success` (все успешно)、`partial` (частично успешно)、`failed` (все неудачно).

### Наследование модификаторов и правил

Модификаторы `At`/`AtAll`/`Reply` и правила до `.Build()` наследуются всей партии и применяются к каждому сообщению:

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # Наследование: каждое сообщение @789
       .Build()
       .Retry(2)                         # Наследование + добавление: каждая запись отдельно повторяет
       .Text("Уведомление @")
       .Image("Изображение объявления")
       .send_all())
```

После входа в Build можно также добавлять модификаторы (применяются ко всей партии):

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # Добавить @, применяется ко всей партии
       .Text("@несколько")
       .send_all())
```

### Фоновое выполнение

Как и при одинарной отправке, `.send_all()` возвращает Task, его можно не await, чтобы он выполнялся в фоне:

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("Пакетная отправка завершена"))
        .Text("a").Text("b")
        .send_all())

# Не блокирует основной поток
await do_something_else()
```

## Правила именования

### Именование PascalCase

Все методы отправки используют PascalCase:

```python
# ✅ Правильно
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# �і Не правильно
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### Платформенные специфические методы

Рекомендуется не добавлять методы с префиксом платформы:

```python
# ✅ Рекомендуется
def Sticker(self, sticker_id: str):
    pass

# �і Не рекомендуется
def TelegramSticker(self, sticker_id: str):
    pass
```

Используйте метод `Raw` вместо этого:

```python
# ✅ Рекомендуется
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# �і Не рекомендуется
def TelegramSticker(self, ...):
    pass
```

## Возвращаемые значения

### Объект Task

Все методы отправки возвращают `asyncio.Task`. Адаптеру достаточно реализовать `Raw_ob12`, стандартные методы (`Text`/`Image` и т.д.) по умолчанию делегируют ему:

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

# Text/Image/Voice/File унаследованы от базового класса и автоматически делегируют Raw_ob12
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

Также поддерживается ручное построение (старый способ тоже совместим):

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

### Цепочный вызов

```python
# @пользователь + ответ
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("Ответ на сообщение @")

# @всем + несколько модификаторов
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("Уведомление о заседании")
```

### Исходные сообщения и построение сообщений

`Raw_ob12` — это основная точка входа для обратного преобразования (получение сегментов OB12 → вызов платформенного API), `MessageBuilder` — инструмент для построения цепочки сегментов сообщения, используемый в паре с ним.

> Подробные спецификации полной реализации `Raw_ob12`, руководство по использованию `MessageBuilder` и кодовые примеры см. в:
> - [Спецификация методов отправки §6 Спецификация обратного преобразования](../../standards/send-method-spec.md#6-спецификация-обратного-преобразованияonebot12--платформа)
> - [Спецификация методов отправки §11 Билдер сообщений MessageBuilder](../../standards/send-method-spec.md#11-билдер-сообщений-messagebuilder)

## Связанные документы

- [Введение в разработку адаптера](getting-started.md) - создание адаптера
- [Основные концепции адаптера](core-concepts.md) - понимание архитектуры адаптера
- [Лучшие практики адаптера](best-practices.md) - разработка качественного адаптера
- [Спецификация методов отправки](../../standards/send-method-spec.md) - полная спецификация методов отправки

Пожалуйста, верните полный Markdown-контент перевода без добавления каких-либо других слов.