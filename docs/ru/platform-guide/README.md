# Документация по функциям платформы ErisPulse

> Базовый протокол: [OneBot12](https://12.onebot.dev/)  
>  
> Данная документация является **руководством по платформенным функциям** и содержит:  
> - Примеры цепочки вызовов метода Send для различных адаптеров  
> - Описание специфических событий и форматов сообщений платформы  
>  
> Общие методы использования см. в следующих документах:  
> - [Основные понятия](../getting-started/basic-concepts.md)  
> - [Стандарт преобразования событий](../standards/event-conversion.md)  
> - [Стандарт API-ответов](../standards/api-response.md)  

---

## Платформенные функции

Эта часть документации поддерживается разработчиками адаптеров и предназначена для описания отличий и расширений данной платформы от стандарта OneBot12. Пожалуйста, ознакомьтесь с подробной документацией по каждой платформе:

- [Заметки по поддержке](maintain-notes.md)

- [Особенности платформы Yunhu](yunhu.md)
- [Особенности платформы Yunhu User](yunhu_user.md)
- [Особенности платформы Telegram](telegram.md)
- [Особенности платформы OneBot11](onebot11.md)
- [Особенности платформы OneBot12](onebot12.md)
- [Особенности платформы SnowLuma](snowluma.md)
- [Особенности платформы Email](email.md)
- [Особенности платформы Kook (开黑啦)](kook.md)
- [Особенности платформы Matrix](matrix.md)
- [Особенности платформы WeCom (企业微信)](wecom.md)
- [Особенности платформы Bilibili](bilibili.md)
- [Особенности платформы Minecraft](minecraft.md)
- [Особенности платформы QQ Bot](qqbot.md)
- [Особенности платформы Ideaura (花枫咖啡馆)](ideaura.md)
- [Особенности платформы Discord](discord.md)
- [Особенности протокола Webhook](webhook.md)
- [Особенности платформы WeChat MP (微信公众号)](wechatmp.md)

> Также существует адаптер `sandbox`, но для него не требуется отдельная документация по платформенным функциям

---

## Общие интерфейсы

### Цепочка вызовов Send
Все адаптеры поддерживают следующие стандартные вызовы:

> **Важно:** `{AdapterName}` в документации необходимо заменить на фактическое имя адаптера (например, `yunhu`, `telegram`, `onebot11`, `email` и т.д.).

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
3. Указание учетной записи отправки: `Using(account_id)`
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

Методы Send DSL возвращают объект `asyncio.Task`, что позволяет выбирать, нужно ли немедленно ожидать результат:

```python
# Получение экземпляра адаптера
my_adapter = adapter.get("{AdapterName}")

# Отправка сообщения без ожидания результата, сообщение отправляется в фоне
task = my_adapter.Send.To("user", "123").Text("Hello")

# Если нужно получить результат отправки, можно позже ожидать завершения задачи
result = await task
```

#### Декораторы правил отправки

В реальном разработке часто требуется: выполнять последующие действия только после успешной отправки, автоматически повторять отправку при ошибке, отменять отправку по таймауту, отслеживать прогресс отправки и т.д. DSL Send содержит встроенный набор декораторов правил отправки, которые можно добавлять цепочкой:

| Метод | Описание |
|--------|------|
| `.Hook(callback)` | Выполняется после успешной отправки (можно вызывать несколько раз) |
| `.Retry(times=1)` | Автоматически повторяет отправку N раз (включая первую попытку, всего N+1) |
| `.Timeout(seconds)` | Устанавливает таймаут для одной отправки, при превышении отменяет отправку (можно комбинировать с Retry) |
| `.Defer(seconds)` | Откладывает отправку (внутрипроцессное таймерное ожидание, не сохраняется) |
| `.OnProgress(callback)` | Вызывает обратный вызов при каждом этапе отправки, передавая SendContext |
| `.OnError(callback)` | Вызывается при окончательной ошибке отправки (вызывается только один раз) |

```python
yunhu = adapter.get("yunhu")

# Выполняется только после успешной отправки (например, списание баллов)
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消费成功"))

# Повтор отправки + таймаут + отслеживание прогресса
def on_progress(ctx):
    print(f"Этап: {ctx.stage}, Попытка: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Повторит отправку до 3 раз
        .Timeout(10)           # Таймаут на одну отправку 10 секунд
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要通知"))
```

Методы правил возвращают `self`, поэтому они должны вызываться до отправки сообщения (Text/Image и т.д.). `SendContext` содержит поля `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, `result`, что удобно для отслеживания.

#### Режим построения пакетов (Build)

Позволяет построить несколько отправок в одной цепочке и выполнить их одновременно. Подходит для сценариев "отправить сразу несколько сообщений":

```python
yunhu = adapter.get("yunhu")

# Строим несколько сообщений и отправляем их одновременно
results = await (yunhu.Send.To("user", "123")
                .Build()                     # Переходим в режим построения
                .Text("通知一")
                .Image("pic.jpg")
                .Text("通知二")
                .send_all())                 # Выполняем отправку
# results = [результат текста, результат изображения, результат текста]
```

`.send_all()` по умолчанию выполняет отправку **параллельно** (высокая эффективность). Если нужно сохранить порядок доставки, используйте `.Sequential()` для последовательной отправки:

```python
# Последовательная отправка (сохраняет порядок) + повтор при ошибке
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Отправка по порядку
       .Retry(2)                     # Каждая неудачная отправка повторяется
       .Text("第一条").Text("第二条")
       .send_all())
```

Пакетная отправка использует стратегию "продолжать при ошибке": одна неудачная отправка не прерывает другие, неудачные отправки автоматически повторяются. Пакетная отправка также поддерживает общие `Hook` (вызывается после всех успешных отправок), `OnError` (вызывается при наличии ошибок), `OnProgress` (обратный вызов по прогрессу).

> Более подробную информацию о правилах и построении пакетов см. в [SendDSL подробно](../developer-guide/adapters/send-dsl.md).

### Слушатели событий
Существует три способа прослушивания событий:

1. Слушатель событий платформы:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено событие {AdapterName}: {data}")
   ```

2. Слушатель стандартных событий OneBot12:
   ```python
   from ErisPulse.Core import adapter, logger

   # Слушатель стандартных событий OneBot12
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Получено стандартное событие: {data}")

   # Слушатель стандартных событий для конкретной платформы
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено событие {AdapterName}: {data}")
   ```

3. Слушатель событий модуля Event:
    События модуля `Event` основаны на функции `adapter.on()`, поэтому формат событий в `Event` соответствует стандартному событию OneBot12

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="Отправить приветственное сообщение", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"Получено сообщение: {event}")
    async def notice_handler(event):
        logger.info(f"Получено уведомление: {event}")
    async def request_handler(event):
        logger.info(f"Получен запрос: {event}")
    async def command_handler(event):
        logger.info(f"Получена команда: {event}")
    ```

Наиболее рекомендуемый способ обработки событий — использование модуля `Event`, поскольку он предоставляет богатые типы событий и методы обработки событий.

---

## Стандартные форматы
Для удобства приведены простые форматы событий. Подробную информацию см. по ссылкам выше.

> **Важно:** Ниже представлены базовые форматы стандарта OneBot12, каждый адаптер может добавлять расширения. Подробнее см. в описании платформенных функций каждого адаптера.

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
    {"type": "text", "data": {"text": "Привет"}}
  ],
  "alt_message": "Привет",
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
  "message": "Отсутствуют необходимые параметры",
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

Связанные официальные документации:
- [Официальная документация OneBot V11](https://github.com/botuniverse/onebot-11)
- [Официальная документация Telegram Bot API](https://core.telegram.org/bots/api)
- [Официальная документация Yunhu](https://www.yhchat.com/document/1-3)

## Участие в разработке

Мы приветствуем больше разработчиков для написания и поддержки документации адаптеров! Пожалуйста, следуйте следующим шагам для внесения вклада:
1. Сделайте fork репозитория [ErisPulse](https://github.com/ErisPulse/ErisPulse).
2. Создайте Markdown-файл в каталоге `docs/platform-features/` с именем `<название платформы>.md`.
3. Добавьте ссылку на ваш адаптер и соответствующую официальную документацию в этот файл `README.md`.
4. Отправьте Pull Request.

Спасибо за вашу поддержку!