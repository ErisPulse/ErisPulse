# Документация по функциям платформы ErisPulse

> Базовый протокол: [OneBot12](https://12.onebot.dev/) 
> 
> В этом документе содержится **руководство по платформенно-специфичным функциям**, включающее:
> - Примеры цепочки вызовов метода Send для каждого адаптера
> - Объяснение платформенно-специфичных форматов событий/сообщений
> 
> Общие методы использования см. в:
> - [Основные концепции](../getting-started/basic-concepts.md)
> - [Стандарт преобразования событий](../standards/event-conversion.md)  
> - [Спецификация ответов API](../standards/api-response.md)

---

## Платформенно-специфические функции

Эта секция поддерживается разработчиками адаптеров и предназначена для описания отличий и расширений адаптера от стандарта OneBot12. Пожалуйста, обратитесь к подробной документации для каждой платформы:

- [Заметки по поддержке](maintain-notes.md)

- [Особенности платформы Yunhu](yunhu.md)
- [Особенности платформы пользователей Yunhu](yunhu_user.md)
- [Особенности платформы Telegram](telegram.md)
- [Особенности платформы OneBot11](onebot11.md)
- [Особенности платформы OneBot12](onebot12.md)
- [Особенности платформы электронной почты](email.md)
- [Особенности платформы Kook (开黑啦)](kook.md)
- [Особенности платформы Matrix](matrix.md)
- [Особенности платформы официального бота QQ](qqbot.md)
- [HuaFeng Coffee House](ideaura.md)
- [Discord](discord.md)
- [Webhook-мост протокола](webhook.md)
- [Особенности платформы WeChat Public Account](wechatmp.md)

> Кроме того, существует адаптер `sandbox`, но для него не требуется документация по платформенно-специфическим функциям.

---

## Общие интерфейсы

### Chain-вызов Send
Все адаптеры поддерживают следующий стандартный способ вызова:

> **Важно:** `{AdapterName}` в документации нужно заменить на фактическое имя адаптера (например, `yunhu`, `telegram`, `onebot11`, `email` и т.д.).

1. Указание типа и идентификатора: `To(type,id).Func()`
   ```python
   # Получение экземпляра адаптера
   my_adapter = adapter.get("{AdapterName}")
   
   # Отправка сообщения
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # Например:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. Только указание идентификатора: `To(id).Func()`
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

Методы Send DSL возвращают объект `asyncio.Task`, что означает, что вы можете выбрать, нужно ли немедленно ожидать результат:

```python
# Получение экземпляра адаптера
my_adapter = adapter.get("{AdapterName}")

# Не ждать результата, сообщение отправляется в фоне
task = my_adapter.Send.To("user", "123").Text("Hello")

# Если нужно получить результат отправки, можно ожидать позже
result = await task
```

#### Декораторы правил отправки

В реальном разработке часто требуется: выполнять последующую логику только после успешной отправки, автоматически повторять отправку при сбое, отменять при таймауте, отслеживать прогресс отправки и т.д. В Send DSL встроена система декораторов правил отправки, которые можно добавлять цепочкой методов:

| Метод | Описание |
|--------|------|
| `.Hook(callback)` | Выполняется после успешной отправки (можно вызывать несколько раз) |
| `.Retry(times=1)` | Автоматически повторяет отправку N раз (включая первую, всего N+1 раз) |
| `.Timeout(seconds)` | Останавливает отправку при превышении времени (можно использовать вместе с Retry) |
| `.Defer(seconds)` | Откладывает отправку (внутрипроцессное таймерное ожидание, не сохраняется) |
| `.OnProgress(callback)` | Вызывает обратный вызов на каждом этапе, передаёт SendContext |
| `.OnError(callback)` | Вызывается при окончательном сбое (вызывается только один раз) |

```python
yunhu = adapter.get("yunhu")

# Вычитание баллов только после успешной отправки
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("Успешная покупка"))

# Повтор отправки + отмена при таймауте + отслеживание прогресса
def on_progress(ctx):
    print(f"Этап: {ctx.stage}, Попытка: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Повторяет до 3 раз
        .Timeout(10)           # Каждая отправка имеет таймаут 10 секунд
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("Важное уведомление"))
```

Методы правил возвращают `self`, и их необходимо вызывать до отправки методов (Text/Image и т.д.). `SendContext` содержит поля `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, `result` и т.д., что полезно для отслеживания.

#### Режим построения пакетов (Build)

В одной цепочке можно построить несколько методов отправки, а затем выполнить их все сразу. Подходит для сценариев "отправить несколько сообщений за один раз":

```python
yunhu = adapter.get("yunhu")

# Строим несколько сообщений и отправляем их одновременно
results = await (yunhu.Send.To("user", "123")
                .Build()                     # Переходим в режим построения
                .Text("Уведомление 1")
                .Image("pic.jpg")
                .Text("Уведомление 2")
                .send_all())                 # Выполняем все сообщения
# results = [результат Text, результат Image, результат Text]
```

`.send_all()` по умолчанию выполняется **параллельно** (параллельная отправка, высокая эффективность). Если нужно гарантировать порядок доставки, вызовите `.Sequential()` для последовательного выполнения:

```python
# Последовательное выполнение (гарантирует порядок) + повтор при сбое
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Отправка по порядку
       .Retry(2)                     # Каждая неудачная отправка будет повторена
       .Text("Первое сообщение").Text("Второе сообщение")
       .send_all())
```

Пакетная отправка использует стратегию "продолжать при сбое": если одна отправка не удалась, это не прерывает другие, и неудачные сообщения автоматически повторяются. Пакетная отправка также поддерживает `Hook` для всех успешных отправок, `OnError` при наличии ошибок и `OnProgress` для обратного вызова о прогрессе.

> Подробное описание правил и построения пакетов см. в разделе [SendDSL详解](../developer-guide/adapters/send-dsl.md).

### Обработка событий
Существует три способа обработки событий:

1. Обработка событий на уровне платформы:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено событие от {AdapterName}: {data}")
   ```

2. Обработка стандартных событий OneBot12:
   ```python
   from ErisPulse.Core import adapter, logger

   # Обработка стандартного события OneBot12
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Получено стандартное событие: {data}")

   # Обработка стандартного события для конкретной платформы
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено событие от {AdapterName}: {data}")
   ```

3. Обработка событий через модуль `Event`:
    События в модуле `Event` основаны на функции `adapter.on()`, поэтому формат событий, предоставляемых `Event`, соответствует стандарту OneBot12.

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

Наиболее рекомендуемый способ обработки событий — использование модуля `Event`, поскольку он предоставляет богатый набор типов событий и методов обработки.

## Стандартный формат
Для удобства справки здесь приведён простой формат событий. Для получения подробной информации, пожалуйста, обратитесь к ссылкам выше.

> **Примечание:** Ниже представлен базовый стандартный формат OneBot12, который может быть дополнен адаптерами. Для получения подробной информации, пожалуйста, обратитесь к описанию специфических функций каждого адаптера.

### Стандартный формат событий
Формат преобразования событий, который должен реализовать каждый адаптер:
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

## Ссылки
Проект ErisPulse:
- [Основной репозиторий](https://github.com/ErisPulse/ErisPulse/)
- [Библиотека адаптера Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Библиотека адаптера Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [Библиотека адаптера OneBot](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

Связанная официальная документация:
- [Официальная документация протокола OneBot V11](https://github.com/botuniverse/onebot-11)
- [Официальная документация Telegram Bot API](https://core.telegram.org/bots/api)
- [Официальная документация Yunhu](https://www.yhchat.com/document/1-3)

## Участие в разработке

Мы приветствуем больше разработчиков, желающих участвовать в написании и поддержке документации адаптеров! Пожалуйста, выполните следующие шаги, чтобы отправить свой вклад:
1. Сделайте форк репозитория [ErisPuls](https://github.com/ErisPulse/ErisPulse).
2. Создайте файл Markdown в каталоге `docs/platform-features/` и назовите его в формате `<platform-name>.md`.
3. Добавьте ссылку на ваш вклад в адаптер и соответствующую официальную документацию в этот файл `README.md`.
4. Отправьте Pull Request.

Благодарим за вашу поддержку!