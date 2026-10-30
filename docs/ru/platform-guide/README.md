# Документация функций платформы ErisPulse

> Базовый протокол: [OneBot12](https://12.onebot.dev/) 
> 
> Документация предназначена для **специфичных функций платформы**, включая:
> - Примеры цепочки вызовов метода Send для каждого адаптера
> - Объяснение платформенно-специфичных событий/форматов сообщений
> 
> Общие сведения о использовании см. в:
> - [Основные понятия](../getting-started/basic-concepts.md)
> - [Стандарт преобразования событий](../standards/event-conversion.md)  
> - [Стандарт ответа API](../standards/api-response.md)

---

## Платформенно-специфичные функции

Эта часть поддерживается разработчиками адаптеров и предназначена для описания отличий и расширений, внесённых в протокол OneBot12. Пожалуйста, ознакомьтесь с подробной документацией по каждой платформе:

- [Примечания по поддержке](maintain-notes.md)

- [Особенности платформы Yunhu](yunhu.md)
- [Особенности платформы Yunhu User](yunhu_user.md)
- [Особенности платформы Telegram](telegram.md)
- [Особенности платформы OneBot11](onebot11.md)
- [Особенности платформы OneBot12](onebot12.md)
- [Особенности платформы SnowLuma](snowluma.md)
- [Особенности платформы Email](email.md)
- [Особенности платформы Kook (开黑啦)](kook.md)
- [Особенности платформы Matrix](matrix.md)
- [Особенности платформы Enterprise WeChat](wecom.md)
- [Особенности платформы QQ Bot](qqbot.md)
- [Особенности платформы Ideaura (花枫咖啡馆)](ideaura.md)
- [Особенности платформы Discord](discord.md)
- [Особенности протокола Webhook](webhook.md)
- [Особенности платформы WeChat MP](wechatmp.md)

> Кроме того, существует адаптер `sandbox`, но для него не требуется документация платформенно-специфичных функций

---

## Общие интерфейсы

### Цепочка вызовов Send
Все адаптеры поддерживают следующие стандартные вызовы:

> **Важно:** `{AdapterName}` в документации нужно заменить на фактическое имя адаптера (например, `yunhu`, `telegram`, `onebot11`, `email` и т.д.).

1. Указание типа и ID: `To(type,id).Func()`
   ```python
   # Получение экземпляра адаптера
   my_adapter = adapter.get("{AdapterName}")
   
   # Отправка сообщения
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # Например:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. Указание только ID: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # Например:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. Указание отправляющего аккаунта: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # Например:
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. Прямой вызов: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # Например:
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### Асинхронная отправка и обработка результатов

Методы DSL Send возвращают объект `asyncio.Task`, что означает, что вы можете выбрать, будете ли вы ожидать результат сразу:

```python
# Получение экземпляра адаптера
my_adapter = adapter.get("{AdapterName}")

# Отправка сообщения без ожидания результата
task = my_adapter.Send.To("user", "123").Text("Hello")

# Если нужно получить результат, можно ожидать позже
result = await task
```

#### Декораторы правил отправки

В реальном разработке часто требуется: выполнить последующую логику только после успешной отправки, автоматически повторить отправку при ошибке, отменить при таймауте, отслеживать прогресс отправки и т.д. В Send DSL встроена система декораторов правил отправки, которые можно добавлять цепочкой:

| Метод | Описание |
|--------|------|
| `.Hook(callback)` | Выполняется после успешной отправки (может быть вызвано несколько раз) |
| `.Retry(times=1)` | Автоматически повторяет отправку N раз (включая первую, всего N+1 раз) |
| `.Timeout(seconds)` | Устанавливает таймаут на одну отправку, при таймауте отменяет (можно использовать вместе с Retry) |
| `.Defer(seconds)` | Откладывает отправку (внутри процесса, не сохраняется) |
| `.OnProgress(callback)` | Обратный вызов на этапах отправки, передаёт SendContext |
| `.OnError(callback)` | Обратный вызов при финальной ошибке (вызывается только один раз) |

```python
yunhu = adapter.get("yunhu")

# Выполнить логику только после успешной отправки
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消费成功"))

# Повтор отправки + таймаут + отслеживание прогресса
def on_progress(ctx):
    print(f"Этап: {ctx.stage}, Попытка: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Максимум 3 повтора
        .Timeout(10)           # Таймаут 10 секунд
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要通知"))
```

Методы правил возвращают `self`, и их нужно вызывать до методов отправки (Text/Image и т.д.). `SendContext` содержит поля `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, `result`, что удобно для мониторинга.

#### Режим построения пакетов (Build)

Построение нескольких методов отправки в одной цепочке, затем их выполнение. Подходит для сценариев "отправить несколько сообщений сразу":

```python
yunhu = adapter.get("yunhu")

# Построение нескольких сообщений и их отправка
results = await (yunhu.Send.To("user", "123")
                .Build()                     # Вход в режим построения
                .Text("通知一")
                .Image("pic.jpg")
                .Text("通知二")
                .send_all())                 # Выполнение
# results = [результат Text, результат Image, результат Text]
```

`.send_all()` по умолчанию выполняется **параллельно** (высокая эффективность). Если нужно гарантировать порядок доставки, используйте `.Sequential()` для последовательного выполнения:

```python
# Последовательное выполнение (гарантирует порядок) + повтор при ошибке
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Отправка по очереди
       .Retry(2)                     # Каждая неудачная отправка повторяется
       .Text("第一条").Text("第二条")
       .send_all())
```

Пакетная отправка использует стратегию "продолжить при ошибке": если одна отправка не удалась, другие продолжают. Неудачные отправки автоматически повторяются. Пакетная отправка также поддерживает `Hook` для всех сообщений (вызывается после успешной отправки всех), `OnError` (вызывается при наличии ошибок), `OnProgress` (обратный вызов прогресса).

> Более подробное описание правил и построения пакетов см. в [SendDSL详解](../developer-guide/adapters/send-dsl.md).

### Слушатели событий
Есть три способа слушания событий:

1. Слушание событий платформы напрямую:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено событие платформы {AdapterName}: {data}")
   ```

2. Слушание событий по стандарту OneBot12:
   ```python
   from ErisPulse.Core import adapter, logger

   # Слушание стандартного события OneBot12
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Получено стандартное событие: {data}")

   # Слушание стандартного события платформы
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено событие платформы {AdapterName}: {data}")
   ```

3. Слушание событий через модуль Event:
    События в модуле Event основаны на функции `adapter.on()`, поэтому формат событий в Event соответствует стандарту OneBot12.

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="Отправить приветственное сообщение", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"Получено сообщение: {event}")
    async def notice_handler(event):
        logger.info(f"Получено уведомление: {event})
    async def request_handler(event):
        logger.info(f"Получен запрос: {event})
    async def command_handler(event):
        logger.info(f"Получена команда: {event})
    ```

Наиболее рекомендуется использовать модуль `Event` для обработки событий, поскольку он предоставляет богатый набор типов событий и методов обработки.

---

## Стандартные форматы
Для удобства приведены базовые форматы событий. Для подробностей см. вышеуказанные ссылки.

> **Важно:** Ниже приведён базовый стандартный формат OneBot12; каждый адаптер может расширять его. За подробностями см. описание платформенно-специфичных функций каждого адаптера.

### Стандартный формат событий
Все адаптеры должны реализовать формат преобразования событий:
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### Стандартный формат ответа
#### Успешная отправка сообщения
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### Неудачная отправка сообщения
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "缺少必要参数",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## Ссылки
Проект ErisPulse:
- [Основной репозиторий](https://github.com/ErisPulse/ErisPulse/)
- [Репозиторий адаптера Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Репозиторий адаптера Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [Репозиторий адаптера OneBot](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

Официальная документация:
- [Официальная документация OneBot V11](https://github.com/botuniverse/onebot-11)
- [Официальная документация Telegram Bot API](https://core.telegram.org/bots/api)
- [Официальная документация Yunhu](https://www.yhchat.com/document/1-3)

## Участие в разработке

Мы приветствуем всех разработчиков, желающих участвовать в написании и поддержке документации адаптеров! Пожалуйста, следуйте инструкциям:
1. Fork-ните [ErisPuls](https://github.com/ErisPulse/ErisPulse).
2. Создайте в каталоге `docs/platform-features/` файл Markdown с именем `<имя_платформы>.md`.
3. Добавьте ссылку на ваш адаптер и соответствующую официальную документацию в этот файл `README.md`.
4. Отправьте Pull Request.

Благодарим за поддержку!