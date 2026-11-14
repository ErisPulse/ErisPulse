# Документация ErisPulse PlatformFeatures

> Базовый протокол: [OneBot12](https://12.onebot.dev/)
>
> Данный документ представляет собой **руководство по функциям конкретных платформ** и содержит:
> - Примеры цепочных вызовов метода Send, поддерживаемых каждым адаптером
> - Описание форматов событий/сообщений, специфичных для платформы
>
> Общие сведения об использовании см. в:
> - [Основные концепции](../getting-started/basic-concepts.md)
> - [Стандарты преобразования событий](../standards/event-conversion.md)
> - [Спецификация ответов API](../standards/api-response.md)

---

## Функции конкретных платформ

Этот раздел поддерживается разработчиками каждого адаптера и описывает отличия данного адаптера от стандарта OneBot12 и его расширенные функции. Подробную документацию по каждой платформе см. ниже:

- [Примечания по сопровождению](maintain-notes.md)

- [Особенности платформы Yunhu](yunhu.md)
- [Особенности платформы Yunhu User](yunhu_user.md)
- [Особенности платформы Oopz](oopz.md)
- [Особенности платформы Telegram](telegram.md)
- [Особенности платформы OneBot11](onebot11.md)
- [Особенности платформы OneBot12](onebot12.md)
- [Особенности платформы SnowLuma](snowluma.md)
- [Особенности платформы электронной почты](email.md)
- [Особенности платформы Kook](kook.md)
- [Особенности платформы Matrix](matrix.md)
- [Особенности платформы WeCom (корпоративный WeChat)](wecom.md)
- [Особенности платформы Bilibili](bilibili.md)
- [Особенности платформы Minecraft](minecraft.md)
- [Особенности платформы официальных ботов QQ](qqbot.md)
- [Кофейня Хуафэн (IdeAura)](ideaura.md)
- [Discord](discord.md)
- [Протокольный мост Webhook](webhook.md)
- [Официальный аккаунт WeChat](wechatmp.md)

> Кроме того, существует адаптер `sandbox`, но для него не требуется поддерживать документацию по функциям платформы

---

## Общий интерфейс

### Цепочные вызовы Send
Все адаптеры поддерживают следующие стандартные способы вызова:

> **Внимание:** `{AdapterName}` в документе следует заменить на фактическое имя адаптера (например, `yunhu`, `telegram`, `onebot11`, `email` и т. д.).

1. С указанием типа и ID: `To(type,id).Func()`
   ```python
   # Получение экземпляра адаптера
   my_adapter = adapter.get("{AdapterName}")
   
   # Отправка сообщения
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # Например:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. С указанием только ID: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # Например:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. С указанием аккаунта отправки: `Using(account_id)`
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

#### Асинхронная отправка и обработка результата

Методы Send DSL возвращают объект `asyncio.Task`, что означает, что вы можете сами решить, ждать ли результат немедленно:

```python
# Получение экземпляра адаптера
my_adapter = adapter.get("{AdapterName}")

# Не ждать результат — сообщение отправляется в фоне
task = my_adapter.Send.To("user", "123").Text("Hello")

# Если требуется получить результат отправки, можно дождаться его позже
result = await task
```

#### Декораторы правил отправки

В реальной разработке часто требуется: выполнять последующую логику только после успешной отправки, автоматически повторять при сбое, отменять по таймауту, отслеживать прогресс отправки и т. д. Send DSL имеет встроенный набор декораторов правил отправки, которые добавляются через цепочные методы:

| Метод | Описание |
|--------|------|
| `.Hook(callback)` | Обратный вызов, выполняемый после успешной отправки (можно вызывать несколько раз) |
| `.Retry(times=1)` | Автоматический повтор N раз при сбое (всего N+1 попыток с учётом первой) |
| `.Timeout(seconds)` | Таймаут одной отправки, отмена при превышении (можно комбинировать с Retry) |
| `.Defer(seconds)` | Отложенная отправка (таймер в рамках процесса, без сохранения состояния) |
| `.OnProgress(callback)` | Обратный вызов прогресса на каждом этапе, передаётся SendContext |
| `.OnError(callback)` | Обратный вызов при окончательном сбое (срабатывает только один раз) |

```python
yunhu = adapter.get("yunhu")

# Списание очков только после успешной отправки
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("Списание прошло успешно"))

# Повтор при сбое + отмена по таймауту + мониторинг прогресса
def on_progress(ctx):
    print(f"Этап: {ctx.stage}, Попытка: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # не более 3 повторов
        .Timeout(10)           # таймаут 10 секунд на каждую попытку
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("Важное уведомление"))
```

Методы правил возвращают `self` и должны вызываться до метода отправки (Text/Image и т. д.). `SendContext` содержит такие поля, как `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, `result`, что удобно для мониторинга.

#### Режим пакетной сборки (Build)

В одной цепочке собирается несколько методов отправки, которые затем выполняются все вместе. Подходит для сценария «отправить несколько сообщений за один раз»:

```python
yunhu = adapter.get("yunhu")

# Сборка нескольких сообщений и их единая отправка
results = await (yunhu.Send.To("user", "123")
                .Build()                     # вход в режим сборки
                .Text("Уведомление 1")
                .Image("pic.jpg")
                .Text("Уведомление 2")
                .send_all())                 # единое выполнение
# results = [результат Text, результат Image, результат Text]
```

`.send_all()` по умолчанию выполняется **параллельно** (параллельная отправка, высокая эффективность). Если необходимо гарантировать порядок доставки сообщений, вызовите `.Sequential()` для последовательного выполнения:

```python
# Последовательное выполнение (с гарантией порядка) + повтор при сбое
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # отправка строго по порядку
       .Retry(2)                     # каждый неудавшийся элемент повторяется отдельно
       .Text("Первое сообщение").Text("Второе сообщение")
       .send_all())
```

Пакетное выполнение использует стратегию **продолжения при сбое**: сбой одного элемента не прерывает остальные, неудавшие элементы повторяются автоматически. Пакетная отправка также поддерживает `Hook` для всей партии (срабатывает после полного успеха), `OnError` (срабатывает при наличии сбоев), `OnProgress` (обратный вызов прогресса).

> Более подробное описание правил и пакетной сборки см. в [Подробном руководстве по SendDSL](../developer-guide/adapters/send-dsl.md).

### Прослушивание событий
Существует три способа прослушивания событий:

1. Прослушивание нативных событий платформы:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено нативное событие {AdapterName}: {data}")
   ```

2. Прослушивание стандартных событий OneBot12:
   ```python
   from ErisPulse.Core import adapter, logger

   # Прослушивание стандартных событий OneBot12
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Получено стандартное событие: {data}")

   # Прослушивание стандартных событий конкретной платформы
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено стандартное событие {AdapterName}: {data}")
   ```

3. Прослушивание через модуль Event:
    События `Event` основаны на функции `adapter.on()`, поэтому формат событий, предоставляемых `Event`, представляет собой стандартное событие OneBot12

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="Отправка приветственного сообщения", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"Получено сообщение: {event}")
    async def notice_handler(event):
        logger.info(f"Получено уведомление: {event}")
    async def request_handler(event):
        logger.info(f"Получен запрос: {event}")
    async def command_handler(event):
        logger.info(f"Получена команда: {event}")
    ```

Из перечисленных способов наиболее рекомендуемым является использование модуля `Event` для обработки событий, поскольку модуль `Event` предоставляет богатый набор типов событий и методов их обработки.

---

## Стандартный формат
Для удобства здесь приведён упрощённый формат событий; для получения подробной информации обратитесь к ссылкам выше.

> **Внимание:** приведённые ниже форматы являются базовыми стандартными форматами OneBot12; адаптеры могут добавлять на их основе расширенные поля. Подробности см. в описаниях функций конкретных адаптеров.

### Стандартный формат событий
Формат преобразования событий, который обязаны реализовать все адаптеры:
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
  "message": "Отсутствуют обязательные параметры",
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

Соответствующая официальная документация:
- [Документация протокола OneBot V11](https://github.com/botuniverse/onebot-11)
- [Официальная документация Telegram Bot API](https://core.telegram.org/bots/api)
- [Официальная документация Yunhu](https://www.yhchat.com/document/1-3)

## Внесение вклада

Мы приглашаем больше разработчиков участвовать в написании и поддержке документации адаптеров! Пожалуйста, следуйте этим шагам для отправки вклада:
1. Сделайте форк репозитория [ErisPuls](https://github.com/ErisPulse/ErisPulse).
2. Создайте Markdown-файл в каталоге `docs/platform-features/` и назовите его в формате `<название платформы>.md`.
3. Добавьте в этот файл `README.md` ссылку на ваш адаптер, а также соответствующую официальную документацию.
4. Отправьте Pull Request.

Спасибо за вашу поддержку!