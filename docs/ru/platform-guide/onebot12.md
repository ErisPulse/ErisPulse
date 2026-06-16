# Документация по особенностям платформы OneBot12

OneBot12Adapter — это адаптер, основанный на протоколе OneBot V12, выполняющий роль базового протокольного адаптера для фреймворка ErisPulse.

---

## Информация о документации

- Версия соответствующего модуля: 4.0.0
- Разработчик: ErisPulse
- Версия протокола: OneBot V12

## Основная информация

- Описание платформы: OneBot V12 — это универсальный стандарт интерфейса для приложений чат-ботов, служащий базовым протоколом для фреймворка ErisPulse.
- Название адаптера: OneBot12Adapter
- Поддерживаемая версия протокола/API: OneBot V12
- Поддержка нескольких учетных записей: Полная архитектура с поддержкой нескольких учетных записей, позволяет одновременно настраивать и запускать несколько учетных записей OneBot12

## Типы поддерживаемых сообщений для отправки

Все методы отправки реализованы через цепочечный синтаксис (fluent interface), например:

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# Отправка с использованием учетной записи по умолчанию
await onebot12.Send.To("group", group_id).Text("Hello World!")

# Отправка с использованием указанной учетной записи
await onebot12.Send.To("group", group_id).Account("main").Text("Сообщение от главного аккаунта")
```

### Нерегистрозависимый вызов

Все методы отправки и цепочечные модификаторы поддерживают нерегистрозависимый вызов, адаптер автоматически сопоставляет правильное имя метода:

```python
# Все следующие вызовы эквивалентны
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# Цепочечные модификаторы также поддерживают
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### Вызов несуществующих методов

При вызове несуществующего метода адаптер возвращает дружелюбное текстовое сообщение, а не выбрасывает исключение:

```python
# Вызов несуществующего метода
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# Возвращается текстовое сообщение
# Содержимое: [Неподдерживаемый тип отправки] Метод: UnsupportedMethod, параметры: [args[0]: 'test']
```

### Типы базовых сообщений

- `.Text(text: str)`: отправка сообщения только с текстом
- `.Image(file: Union[str, bytes], filename: str = "image.png")`: отправка сообщения с изображением (поддерживаются URL, Base64 или байты)
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`: отправка аудиосообщения
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")`: отправка голосового сообщения (别名 для Audio, совместимость с OneBot11)
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`: отправка видеосообщения

### Цепочечные модификаторы (возвращает self для поддержки цепочечного вызова)

- `.At(user_id: Union[str, int])`: упоминание пользователя (@, может вызываться несколько раз)
- `.AtAll()`: упоминание всех участников
- `.Reply(message_id: Union[str, int])`: ответ на сообщение

### Отправка оригинальных сообщений

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)`: отправка сообщения в оригинальном формате OneBot12 (соответствует стандартному названию)

### Другие типы сообщений

- `.Sticker(file_id: str)`: отправка стикера / эмодзи-пакета
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`: отправка геолокации

### Управляющие функции

- `.Recall(message_id: Union[str, int])`: отзыв (отмена) сообщения
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`: редактирование сообщения
- `.Raw(message_segments: List[Dict])`: отправка нативных сегментов сообщений OneBot12
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`: пакетная отправка сообщений

## Стандартные события OneBot12

Адаптер OneBot12 полностью соответствует стандарту OneBot12, формат событий не требует преобразования и напрямую передается в фреймворк.

### Нововведение: Поле типа события

Соответствует спецификации `standards/event-conversion.md`, все события сохраняют поле исходного типа события `onebot12_raw_type`:

```python
{
    "id": "event-id",
    "type": "message",              # Тип события
    "onebot12_raw_type": "message", # Исходный тип события (совпадает с type)
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}
```

### События сообщений (Message Events)

```python
# Личное сообщение
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}

# Групповое сообщение
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "group_id": "group-id",
    "message": [{"type": "text", "data": {"text": "Hello group"}}],
    "alt_message": "Hello group",
    "time": 1234567890
}
```

### События уведомлений (Notice Events)

```python
# Увеличение участников группы
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_increase",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "approve",
    "time": 1234567890
}

# Уменьшение участников группы
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_decrease",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "leave",
    "time": 1234567890
}
```

### События запросов (Request Events)

```python
# Запрос в друзья
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "сообщение заявки",
    "flag": "request-flag",
    "time": 1234567890
}

# Запрос на вступление в группу
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "сообщение заявки",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### Метасобытия (Meta Events)

```python
# Событие жизненного цикла
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# Событие сердцебиения
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "heartbeat",
    "self": {"user_id": "bot-id"},
    "interval": 5000,
    "status": {"online": true},
    "time": 1234567890
}
```

## Параметры конфигурации

### Конфигурация учетных записей

Каждая учетная запись имеет независимую конфигурацию следующих параметров:

- `mode`: режим работы этой учетной записи ("server" или "client")
- `server_path`: путь WebSocket в режиме Server
- `server_token`: токен аутентификации в режиме Server (необязательно)
- `client_url`: адрес WebSocket для подключения в режиме Client
- `client_token`: токен аутентификации в режиме Client (необязательно)
- `enabled`: следует ли включить эту учетную запись
- `platform`: идентификатор платформы, по умолчанию "onebot12"
- `implementation`: идентификатор реализации, например "go-cqhttp" (необязательно)

### Пример конфигурации

```toml
[OneBotv12_Adapter.accounts.main]
mode = "server"
server_path = "/onebot12-main"
server_token = "main_token"
enabled = true
platform = "onebot12"
implementation = "go-cqhttp"

[OneBotv12_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true
platform = "onebot12"
implementation = "shinonome"

[OneBotv12_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### Конфигурация по умолчанию

Если не настроены никакие учетные записи, адаптер автоматически создаст:

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## Возвращаемое значение методов отправки

### Методы отправки сообщений

Все методы отправки сообщений (например, `.Text()`, `.Image()`, `.Raw_ob12()` и т.д.) возвращают объект `asyncio.Task`, который можно напрямую ожидать (await), чтобы получить результат отправки:

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### Цепочечные модификаторы

Все цепочечные модификаторы (например, `.At()`, `.AtAll()`, `.Reply()`) возвращают `self`, что поддерживает цепочечный вызов:

```python
# Комбинирование нескольких модификаторов
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("текст")
```

## Стандарт API

Адаптер следует стандартизированному формату возврата ErisPulse (см. `standards/api-response.md`):

```python
# Успешный ответ
{
    "status": "ok",              // Обязательно: статус выполнения
    "retcode": 0,                // Обязательно: код возврата (0 означает успех)
    "data": {                     // Обязательно: данные ответа
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       // Обязательно: ID сообщения (если нет — пустая строка)
    "message": "",                // Обязательно: сообщение об ошибке (успех — пустая строка)
    "echo": "1234",               // Необязательно: возвращается как есть из запроса
    "onebot12_raw": {...}        // Необязательно: исходные данные ответа
}

# Неуспешный ответ
{
    "status": "failed",           // Обязательно: статус выполнения
    "retcode": 10003,            // Обязательно: код возврата (ненулевой означает ошибку)
    "data": None,                // Обязательно: null при ошибке
    "message_id": "",            // Обязательно: пустая строка при ошибке
    "message": "Отсутствуют необходимые параметры",    // Обязательно: описание ошибки
    "echo": "1234",              // Необязательно: возвращается как есть из запроса
    "onebot12_raw": {...}        // Необязательно: исходные данные ответа
}
```

### Коды ошибок

Следует стандартным кодам ошибок OneBot12:

- **0**: Успех
- **1xxxx**: Ошибка запроса действия
- **2xxxx**: Ошибка обработчика действия
- **3xxxx**: Ошибка выполнения действия (33001 — сетевой тайм-аут)

### Синтаксис отправки для нескольких учетных записей

```python
# Способ выбора учетной записи
await onebot12.Send.Using("main").To("group", 123456).Text("Сообщение от главного аккаунта")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# Способ вызова API
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## Механизм асинхронной обработки

OneBot12Adapter использует асинхронный неблокирующий дизайн:

1. Отправка сообщений не блокирует цикл обработки событий
2. Несколько операций отправки могут выполняться одновременно
3. Ответы API могут обрабатываться своевременно
4. Соединения WebSocket поддерживаются в активном состоянии
5. Обработка нескольких учетных записей одновременно, каждая учетная запись работает независимо

## Обработка ошибок

Адаптер предоставляет надежную систему обработки ошибок:

1. Автоматическое переподключение при нарушении сетевого соединения (поддержка независимого переподключения для каждой учетной записи, с интервалом 30 секунд)
2. Обработка тайм-аутов вызовов API (фиксированный тайм-аут 30 секунд)
3. Автоматическая повторная попытка при неудаче отправки сообщения (максимум 3 попытки)
4. Вызов несуществующих методов возвращает дружелюбное текстовое сообщение

## Улучшение обработки событий

В режиме нескольких учетных записей все события автоматически получают информацию об учетной записи:

```python
{
    "type": "message",
    "onebot12_raw_type": "message",  // Исходный тип события
    "detail_type": "private",
    "self": {"user_id": "123456"},  // ID аккаунта, отправившего событие (стандартное поле)
    "platform": "onebot12",
    // ... другие поля события
}
```

## Интерфейсы управления

```python
# Получение информации о всех учетных записях
accounts = onebot12.accounts

# Проверка статуса соединения учетной записи
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# Динамическое включение/выключение учетной записи (требуется перезапуск адаптера)
onebot12.accounts["test"].enabled = False
```

## Стандартные возможности OneBot12

### Стандарт сегментов сообщений

OneBot12 использует стандартизированный формат сегментов сообщений:

```python
# Сегмент текстового сообщения
{"type": "text", "data": {"text": "Hello"}}

# Сегмент изображения
{"type": "image", "data": {"file_id": "image-id"}}

# Сегмент упоминания
{"type": "mention", "data": {"user_id": "user-id", "user_name": "Username"}}

# Сегмент ответа
{"type": "reply", "data": {"message_id": "msg-id"}}
```

### Стандарт API

Соответствует спецификации стандартного API OneBot12:

- `send_message`: отправка сообщения
- `delete_message`: отзыв сообщения
- `edit_message`: редактирование сообщения
- `get_message`: получение сообщения
- `get_self_info`: получение информации о себе
- `get_user_info`: получение информации о пользователе
- `get_group_info`: получение информации о группе

## Лучшие практики

1. **Управление конфигурацией**: рекомендуется использовать конфигурацию с несколькими учетными записями для раздельного управления ботами разного назначения
2. **Обработка ошибок**: всегда проверяйте статус возврата при вызове API
3. **Отправка сообщений**: используйте подходящие типы сообщений, избегайте отправки неподдерживаемых сообщений
4. **Мониторинг соединений**: регулярно проверяйте статус соединения, обеспечивая доступность сервиса
5. **Оптимизация производительности**: используйте метод Batch при пакетной отправке для снижения сетевых затрат
6. **Методы вызова**: рекомендуется использовать стандартные имена в стиле "BigCamelCase" (например, `.Text()`), но также поддерживается нижний регистр для совместимости с различными стилями программирования (такой способ может быть несовместим со старыми версиями)