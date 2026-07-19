# OneBot12 Платформенные особенности документации

OneBot12Adapter - это адаптер, построенный на протоколе OneBot V12, который служит базовым протоколом адаптера для фреймворка ErisPulse.

---

## Информация о документации

- Соответствующая версия модуля: 4.0.0
- Ответственный: ErisPulse
- Версия протокола: OneBot V12

## Основная информация

- Краткое описание платформы: OneBot V12 - это универсальный стандарт интерфейса приложения чат-бота, который является базовым протоколом фреймворка ErisPulse
- Название адаптера: OneBot12Adapter
- Поддерживаемые версии протокола/API: OneBot V12
- Поддержка нескольких аккаунтов: Полностью архитектура с поддержкой нескольких аккаунтов, позволяет одновременно настраивать и запускать несколько аккаунтов OneBot12

## Поддерживаемые типы отправки сообщений

Все методы отправки реализованы с использованием цепочечной синтаксиса, например:

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# Отправка с использованием аккаунта по умолчанию
await onebot12.Send.To("group", group_id).Text("Hello World!")

# Отправка с указанием конкретного аккаунта
await onebot12.Send.To("group", group_id).Account("main").Text("Сообщение с основного аккаунта")
```

### Нерегистрозависимый вызов

Все методы отправки и цепочечные модификаторы поддерживают нерегистрозависимый вызов, адаптер автоматически сопоставляет с правильным стандартным именем метода:

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

### Вызов неподдерживаемых методов

При вызове несуществующего метода адаптер возвращает дружественное текстовое уведомление, а не выбрасывает исключение:

```python
# Вызов неподдерживаемого метода
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# Возвращаемый результат - отправленное текстовое сообщение
# Содержание сообщения: [Неподдерживаемый тип отправки] Имя метода: UnsupportedMethod, Параметры: [args[0]: 'test']
```

### Основные типы сообщений

- `.Text(text: str)` - отправка чистого текстового сообщения
- `.Image(file: Union[str, bytes], filename: str = "image.png")` - отправка сообщения с изображением (поддерживает URL, Base64 или bytes)
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")` - отправка аудиосообщения
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")` - отправка голосового сообщения (альтернативное имя Audio, совместимо с OneBot11)
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` - отправка видеосообщения

### Цепочечные модификаторы (возвращают self для поддержки цепочечного вызова)

- `.At(user_id: Union[str, int])` - упоминание пользователя (можно вызывать несколько раз)
- `.AtAll()` - упоминание всех участников
- `.Reply(message_id: Union[str, int])` - ответ на сообщение

### Отправка сообщений в исходном формате

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)` - отправка сообщений в исходном формате OneBot12 (соответствует правилам именования)

### Другие типы сообщений

- `.Sticker(file_id: str)` - отправка стикера/эмодзи
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")` - отправка местоположения

### Управление функции

- `.Recall(message_id: Union[str, int])` - отмена сообщения
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])` - редактирование сообщения
- `.Raw(message_segments: List[Dict])` - отправка нативных OneBot12 сообщений
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")` - массовая отправка сообщений

## OneBot12 стандартные события

OneBot12 адаптер полностью соответствует стандарту OneBot12, формат событий не требует преобразования, напрямую передается в фреймворк.

### Дополнительная функция: поле типа исходного события

Соответствует спецификации `standards/event-conversion.md`, все события сохраняют поле типа исходного события `onebot12_raw_type`:

```python
{
    "id": "event-id",
    "type": "message",              # Тип события
    "onebot12_raw_type": "message", # Исходный тип события (такой же, как и type)
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
# Запрос на добавление в друзья
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "Сообщение заявки",
    "flag": "request-flag",
    "time": 1234567890
}

# Запрос приглашения в группу
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "Сообщение заявки",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### Мета-события (Meta Events)

```python
# События жизненного цикла
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# События心跳
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

### Конфигурация аккаунтов

Каждый аккаунт имеет независимую конфигурацию следующих параметров:

- `mode`: Режим работы аккаунта ("server" или "client")
- `server_path`: Путь WebSocket в режиме Server
- `server_token`: Токен аутентификации в режиме Server (необязательно)
- `client_url`: Адрес WebSocket для подключения в режиме Client
- `client_token`: Токен аутентификации в режиме Client (необязательно)
- `enabled`: Включен ли аккаунт
- `platform`: Идентификатор платформы, по умолчанию "onebot12"
- `implementation`: Идентификатор реализации, например "go-cqhttp" (необязательно)

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

Если не настроены аккаунты, адаптер автоматически создаст:

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## Возвращаемые значения методов отправки

### Методы отправки сообщений
Все методы отправки сообщений (например, `.Text()`, `.Image()`, `.Raw_ob12()` и т.д.) возвращают объект `asyncio.Task`, который можно напрямую ожидать для получения результата отправки:

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### Цепочечные модификаторы
Все цепочечные модификаторы (например, `.At()`, `.AtAll()`, `.Reply()`) возвращают `self`, что поддерживает цепочечный вызов:

```python
# Комбинирование нескольких модификаторов
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("Текст")
```

## Стандарт ответа API

Адаптер следует стандартизированному формату ответа ErisPulse (см. `standards/api-response.md`):

```python
# Успешный ответ
{
    "status": "ok",              // Обязательно: статус выполнения
    "retcode": 0,                // Обязательно: код возврата (0 означает успех)
    "data": {                     // Обязательно: данные ответа
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       // Обязательно: ID сообщения (если нет - пустая строка)
    "message": "",                // Обязательно: сообщение об ошибке (если успех - пустая строка)
    "echo": "1234",               // Необязательно: возвращается без изменений из запроса echo
    "onebot12_raw": {...}        // Необязательно: исходные данные ответа
}

# Ответ об ошибке
{
    "status": "failed",           // Обязательно: статус выполнения
    "retcode": 10003,            // Обязательно: код возврата (ненулевой означает ошибку)
    "data": None,                // Обязательно: при ошибке - null
    "message_id": "",            // Обязательно: при ошибке - пустая строка
    "message": "Отсутствуют необходимые параметры",    // Обязательно: описание ошибки
    "echo": "1234",              // Необязательно: возвращается без изменений из запроса echo
    "onebot12_raw": {...}        // Необязательно: исходные данные ответа
}
```

### Стандарт кодов ошибок

Следует стандартным кодам ошибок OneBot12:

- **0**: Успех
- **1xxxx**: Ошибка запроса действия
- **2xxxx**: Ошибка обработчика действия
- **3xxxx**: Ошибка выполнения действия (33001 - сетевой таймаут)

### Синтаксис отправки сообщений с несколькими аккаунтами

```python
# Метод выбора аккаунта
await onebot12.Send.Using("main").To("group", 123456).Text("Сообщение с основного аккаунта")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# Вызов API
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## Асинхронная обработка

OneBot12 адаптер использует асинхронную неблокирующую архитектуру:

1. Отправка сообщений не блокирует цикл обработки событий
2. Множественные параллельные операции отправки могут выполняться одновременно
3. Ответы API могут обрабатываться своевременно
4. Соединение WebSocket остается активным
5. Параллельная обработка нескольких аккаунтов, каждый аккаунт работает независимо

## Обработка ошибок

Адаптер предоставляет надежную систему обработки ошибок:

1. Автоматическое переподключение при сетевых исключениях (поддерживается независимое переподключение для каждого аккаунта с интервалом 30 секунд)
2. Обработка таймаута вызова API (фиксированный таймаут 30 секунд)
3. Автоматическая повторная отправка при неудачной отправке сообщения (максимум 3 попытки)
4. Вызов несуществующего метода возвращает дружественное текстовое уведомление

## Расширенная обработка событий

В режиме нескольких аккаунтов все события автоматически добавляют информацию об аккаунте:

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

## Управление интерфейсом

```python
# Получение информации обо всех аккаунтах
accounts = onebot12.accounts

# Проверка состояния соединения аккаунта
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# Динамическое включение/отключение аккаунта (требуется перезапуск адаптера)
onebot12.accounts["test"].enabled = False
```

## Стандартные особенности OneBot12

### Стандартные сообщения

OneBot12 использует стандартизированный формат сообщений:

```python
# Текстовое сообщение
{"type": "text", "data": {"text": "Hello"}}

# Сообщение с изображением
{"type": "image", "data": {"file_id": "image-id"}}

# Сообщение с упоминанием
{"type": "mention", "data": {"user_id": "user-id", "user_name": "Username"}}

# Сообщение с ответом
{"type": "reply", "data": {"message_id": "msg-id"}}
```

### Стандарт API

Следует стандартным API OneBot12:

- `send_message`: Отправка сообщения
- `delete_message`: Отмена сообщения
- `edit_message`: Редактирование сообщения
- `get_message`: Получение сообщения
- `get_self_info`: Получение информации о себе
- `get_user_info`: Получение информации о пользователе
- `get_group_info`: Получение информации о группе

## Лучшие практики

1. **Управление конфигурацией**: Рекомендуется использовать конфигурацию с несколькими аккаунтами, разделяя управление ботами с различными целями
2. **Обработка ошибок**: Всегда проверяйте статус возврата вызова API
3. **Отправка сообщений**: Используйте соответствующий тип сообщения, избегайте отправки неподдерживаемых сообщений
4. **Мониторинг соединения**: Регулярно проверяйте состояние соединения, обеспечивая доступность сервиса
5. **Оптимизация производительности**: При массовой отправке используйте метод Batch, чтобы уменьшить сетевой расход
6. **Вызов методов**: Рекомендуется использовать стандартное название с большой буквы (например, `.Text()`), но также поддерживается нижний регистр для совместимости с различными стилями программирования (такой способ может быть несовместим со старыми версиями)