# Документация по функциональности ErisPulse PlatformFeatures

> Базовый протокол: [OneBot12](https://12.onebot.dev/)
> 
> Этот документ представляет собой **руководство по функциональности платформы**, которое включает:
> - Примеры цепочки вызовов методов Send, поддерживаемые каждым адаптером
> - Описание форматов событий и сообщений, специфичных для платформ
> 
> Общее использование методов смотрите в следующих разделах:
> - [Базовые понятия](../getting-started/basic-concepts.md)
> - [Стандарт конвертации событий](../standards/event-conversion.md)
> - [Спецификация ответов API](../standards/api-response.md)

---

## Функциональность, специфичная для платформы

Этот раздел поддерживается разработчиками каждого адаптера и предназначен для описания различий между этим адаптером и стандартом OneBot12, а также его расширенных функций. Пожалуйста, обратитесь к подробной документации по каждой из следующих платформ:

- [Инструкции по поддержке](maintain-notes.md)

- [Особенности платформы Yunhu](yunhu.md)
- [Особенности платформы Yunhu User](yunhu_user.md)
- [Особенности платформы Telegram](telegram.md)
- [Особенности платформы OneBot11](onebot11.md)
- [Особенности платформы OneBot12](onebot12.md)
- [Особенности платформы Email](email.md)
- [Особенности платформы Kook (开黑啦)](kook.md)
- [Особенности платформы Matrix](matrix.md)
- [Особенности платформы QQ Official Bot](qqbot.md)
- [Ideaura](ideaura.md)
- [Discord](discord.md)
- [Webhook协议桥](webhook.md)
- [微信公众号](wechatmp.md)

> Кроме того, существует адаптер `sandbox`, но для этого адаптера не требуется поддерживать документацию по функциональности платформы.

---

## Общий интерфейс

### Цепочка вызовов Send

Все адаптеры поддерживают следующий стандартный способ вызова:

> **Примечание:** В документации `{AdapterName}` необходимо заменить на фактическое название адаптера (например, `yunhu`, `telegram`, `onebot11`, `email` и т. д.).

1. Указание типа и ID: `To(type, id).Func()`
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
3. Указание аккаунта отправки: `Using(account_id)`
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

Методы Send DSL возвращают объект `asyncio.Task`, что означает, что вы можете выбрать, нужно ли ждать результата сразу:

```python
# Получение экземпляра адаптера
my_adapter = adapter.get("{AdapterName}")

# Не ждем результат, сообщение отправляется в фоновом режиме
task = my_adapter.Send.To("user", "123").Text("Hello")

# Если необходимо получить результат отправки, можно дождаться его позже
result = await task
```

### Слушатель событий

Существует три способа слушать события:

1. Слушатель нативных событий платформы:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено нативное событие {AdapterName}: {data}")
   ```

2. Слушатель стандартных событий OneBot12:
   ```python
   from ErisPulse.Core import adapter, logger

   # Слушание стандартного события OneBot12
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Получено стандартное событие: {data}")

   # Слушание стандартного события для определенной платформы
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено стандартное событие {AdapterName}: {data}")
   ```

3. Слушатель через модуль Event:
    События модуля Event основаны на функции `adapter.on()`, поэтому формат событий, предоставляемый `Event`, представляет собой стандартное событие OneBot12.

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

В целом, наиболее рекомендуется использовать модуль `Event` для обработки событий, так как `Event` предоставляет богатый набор типов событий, а также множество методов обработки событий.

---

## Стандартный формат

Для удобства справки ниже приведен простой формат событий. Если требуется подробная информация, пожалуйста, обратитесь к ссылкам выше.

> **Примечание:** Ниже приведен базовый стандартный формат OneBot12. Адаптеры могут иметь дополнительные расширенные поля на основе этого. За подробностями обратитесь к описанию функциональности конкретного адаптера.

### Стандартный формат событий

Формат конвертации событий, который должны реализовать все адаптеры:
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

### Стандартный формат ответов

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
- [Главный репозиторий](https://github.com/ErisPulse/ErisPulse/)
- [Библиотека адаптера Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Библиотека адаптера Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [Библиотека адаптера OneBot](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

Официальная документация:
- [Документация протокола OneBot V11](https://github.com/botuniverse/onebot-11)
- [Официальная документация Telegram Bot API](https://core.telegram.org/bots/api)
- [Официальная документация Yunhu](https://www.yhchat.com/document/1-3)

## Участие в разработке

Мы приветствуем участие большего числа разработчиков в написании и поддержке документации адаптеров! Пожалуйста, следуйте следующим шагам для отправки вклада:
1. Fork [ErisPulse](https://github.com/ErisPulse/ErisPulse) репозиторий.
2. Создайте Markdown файл в директории `docs/platform-features/` с именем `<PlatformName>.md`.
3. Добавьте ссылку на ваш адаптер и соответствующую официальную документацию в этом файле `README.md`.
4. Отправьте Pull Request.

Спасибо за вашу поддержку!