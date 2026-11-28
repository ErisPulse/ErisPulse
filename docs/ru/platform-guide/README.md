# Документация по функциям платформы ErisPulse

> Базовый протокол: [OneBot12](https://12.onebot.dev/) 
> 
> Данная документация представляет собой **руководство по платформенным функциям**, включающее:
> - Примеры цепочечного вызова метода Send для каждого адаптера
> - Описание платформенно-специфических событий/форматов сообщений
> 
> Общие сведения об использовании см. в:
> - [Основные понятия](../getting-started/basic-concepts.md)
> - [Стандарт преобразования событий](../standards/event-conversion.md)  
> - [Стандарт API-ответов](../standards/api-response.md)

---

## Платформенно-специфические функции

Эта часть поддерживается разработчиками адаптеров и предназначена для описания отличий и расширений от стандарта OneBot12. Пожалуйста, ознакомьтесь с подробной документацией по каждой платформе:

- [Заметки по поддержке](maintain-notes.md)

- [Особенности платформы Yunhu](yunhu.md)
- [Особенности платформы Yunhu User](yunhu_user.md)
- [Особенности платформы Oopz](oopz.md)
- [Особенности платформы Telegram](telegram.md)
- [Особенности платформы OneBot11](onebot11.md)
- [Особенности платформы OneBot12](onebot12.md)
- [Особенности платформы SnowLuma](snowluma.md)
- [Особенности платформы Email](email.md)
- [Особенности платформы Kook(开黑啦)](kook.md)
- [Особенности платформы Matrix](matrix.md)
- [Особенности платформы WeCom](wecom.md)
- [Особенности платформы Bilibili](bilibili.md)
- [Особенности платформы Minecraft](minecraft.md)
- [Особенности платформы QQbot](qqbot.md)
- [Особенности платформы Ideaura](ideaura.md)
- [Особенности платформы Discord](discord.md)
- [Особенности протокола Webhook](webhook.md)
- [Особенности платформы WeChatMP](wechatmp.md)
- [Особенности платформы WeChatClawBot](wechatclaw.md)
- [Особенности платформы Sandbox](sandbox.md)
- [Особенности платформы Terminal](terminal.md)

---

## Общие интерфейсы

### Цепочечный вызов Send
Все адаптеры поддерживают следующий стандартный способ вызова:

> **Примечание:** `{AdapterName}` в документации необходимо заменить на фактическое имя адаптера (например, `yunhu`, `telegram`, `onebot11`, `email` и т.д.).

1. Указание типа и ID: `To(type,id).Func()`
   ```python
   # Получение экземпляра адаптера
   my_adapter = adapter.get("{AdapterName}")
   
   # Отправка сообщения
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # Пример:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. Указание только ID: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # Пример:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. Указание ID отправляющего аккаунта: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # Пример:
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. Прямой вызов: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # Пример:
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### Асинхронная отправка и обработка результатов

Методы Send DSL возвращают объект `asyncio.Task`, что означает, что вы можете выбрать, будете ли вы немедленно ожидать результат:

```python
# Получение экземпляра адаптера
my_adapter = adapter.get("{AdapterName}")

# Отправка сообщения в фоновом режиме без ожидания результата
task = my_adapter.Send.To("user", "123").Text("Hello")

# Если вам нужно получить результат отправки, вы можете подождать его позже
result = await task
```

#### Декораторы правил отправки

В реальном разработке часто требуется: выполнить последующую логику только после успешной отправки, автоматически повторить отправку при сбое, отменить по таймауту, отслеживать ход отправки и т.д. В Send DSL встроена система декораторов правил отправки, которые можно добавлять цепочкой:

| Метод | Описание |
|--------|------|
| `.Hook(callback)` | Выполняется после успешной отправки (может вызываться несколько раз) |
| `.Retry(times=1)` | Автоматически повторяет отправку N раз (включая первую, всего N+1 раз) |
| `.Timeout(seconds)` | Устанавливает таймаут на одну отправку, прерывает при истечении (можно комбинировать с Retry) |
| `.Defer(seconds)` | Откладывает отправку (внутрипроцессное таймерное отложение, не сохраняется) |
| `.OnProgress(callback)` | Вызывает обратный вызов на каждой стадии, передавая SendContext |
| `.OnError(callback)` | Вызывается при окончательном сбое (вызывается только один раз) |

```python
yunhu = adapter.get("yunhu")

# Выполнить логику только после успешной отправки
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消费成功"))

# Повтор отправки + таймаут + отслеживание прогресса
def on_progress(ctx):
    print(f"Этап: {ctx.stage}, попытка: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Повторить до 3 раз
        .Timeout(10)           # Таймаут 10 секунд
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要通知"))
```

Методы правил возвращают `self`, и их необходимо вызывать до отправки методов (Text/Image и т.д.). `SendContext` содержит поля `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, `result`, что позволяет отслеживать.

#### Режим построения пакета (Build)

Построение нескольких отправок в одной цепочке, затем выполнение всех сообщений в одном вызове. Подходит для сценариев "отправить сразу несколько сообщений":

```python
yunhu = adapter.get("yunhu")

# Построение нескольких сообщений, отправка всех
results = await (yunhu.Send.To("user", "123")
                .Build()                     # Вход в режим построения
                .Text("通知一")
                .Image("pic.jpg")
                .Text("通知二")
                .send_all())                 # Выполнить все сообщения
# results = [результат текста, результат изображения, результат текста]
```

`.send_all()` по умолчанию выполняется **параллельно** (параллельная отправка, высокая эффективность). При необходимости сохранить порядок отправки используйте `.Sequential()` для последовательного выполнения:

```python
# Последовательное выполнение (сохраняет порядок) + повтор при сбое
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Последовательная отправка
       .Retry(2)                     # Повтор для неудачных сообщений
       .Text("第一条").Text("第二条")
       .send_all())
```

Пакетная отправка использует стратегию "продолжить при ошибке": если одна из отправок не удалась, это не прерывает другие, неудачные сообщения автоматически повторяются. Пакетная отправка также поддерживает `Hook` для всех сообщений (вызывается после успешной отправки всех), `OnError` (вызывается при наличии ошибок), `OnProgress` (обратный вызов прогресса).

> Подробнее о правилах и построении пакетов см. в [SendDSL подробно](../developer-guide/adapters/send-dsl.md).

### Обработка событий
Есть три способа прослушивания событий:

1. Прослушивание событий на уровне платформы:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено событие {AdapterName}: {data}")
   ```

2. Прослушивание событий по стандарту OneBot12:
   ```python
   from ErisPulse.Core import adapter, logger

   # Прослушивание стандартных событий OneBot12
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Получено стандартное событие: {data}")

   # Прослушивание событий OneBot12 для конкретной платформы
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено событие OneBot12 {AdapterName}: {data}")
   ```

3. Прослушивание событий через модуль Event:
    События модуля `Event` основаны на функции `adapter.on()`, поэтому формат событий, предоставляемый `Event`, является стандартным событием OneBot12

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
Для удобства приведены простые форматы событий, подробную информацию см. по ссылкам выше.

> **Примечание:** Ниже представлен базовый формат стандарта OneBot12, каждый адаптер может расширять его дополнительными полями. Подробнее см. в описании специфических функций каждого адаптера.

### Стандартный формат событий
Все адаптеры должны реализовывать формат преобразования событий:
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

Мы приветствуем всех разработчиков, желающих участвовать в написании и поддержке документации по адаптерам! Пожалуйста, следуйте инструкциям по внесению вклада:
1. Fork [ErisPuls](https://github.com/ErisPulse/ErisPulse) репозитория.
2. Создайте Markdown-файл в директории `docs/platform-features/` с именем в формате `<название платформы>.md`.
3. Добавьте ссылку на ваш вклад в этот файл `README.md` и на соответствующую официальную документацию.
4. Отправьте Pull Request.

Благодарим за вашу поддержку!