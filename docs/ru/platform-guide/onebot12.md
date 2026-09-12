# Документация по функциям платформы OneBot12

OneBot12Adapter — это адаптер, построенный на основе протокола OneBot V12, выступающий в качестве базового протокольного адаптера для фреймворка ErisPulse.

---

## Информация о документе

- Версия соответствующего модуля: 4.3.0
- Ответственный: ErisPulse
- Версия протокола: OneBot V12

## Основная информация

- Краткое описание платформы: OneBot V12 — это универсальный стандарт интерфейса приложений для чат-ботов, базовый протокол для фреймворка ErisPulse.
- Название адаптера: OneBot12Adapter
- Поддерживаемые версии протокола/API: OneBot V12
- Поддержка нескольких аккаунтов: Полностью архитектура с поддержкой нескольких аккаунтов, позволяет одновременно настроить и запустить несколько OneBot12-аккаунтов.

## Обновление парадигмы v5 (4.3.0)

Адаптер успешно обновлён до парадигмы v5 (постепенное обновление, совместимость API):

- **Наследование BaseConverter**: Общие поля преобразователя (id/time/platform/self/raw) создаются с помощью build_base_event фреймворка, и переопределяются по именам полей OB11 (echo/time/self_id)
- **Принадлежность задачи spawn_background**: Задача подключения в режиме Client теперь использует runtime.spawn_background (принадлежит owner, автоматически освобождается при завершении)
- **Мягкая зависимость от фреймворка**: Установка адаптера больше не требует жёсткой зависимости от ErisPulse, что предотвращает изменение версии фреймворка при разрешении зависимостей pip; во время выполнения проверяется ErisPulse>=2.7.1, и при слишком низкой версии выводится предупреждение в лог
- **Журнал версии при запуске**: При инициализации выводится сообщение о загрузке OneBotAdapter v4.3.0

Доступные возможности (поддержка начиная с 4.2.0): мультиаккаунт, стандартные действия Api DSL (get_self_info→get_login_info и т.д.), Request DSL (одобрение/отклонение запросов на добавление в друзья/в группу: event.approve() / event.reject()), EventMixin, i18n.

---

## Стандартные действия API (DSL API)

OneBot12 поддерживает все стандартные имена действий OB12, API DSL по умолчанию напрямую делегирует call_api (без отображения):

```python
from ErisPulse import sdk
ob12 = sdk.adapter.get("onebot12")

result = await ob12.Api.get_self_info()
result = await ob12.Api.get_friend_list()
await ob12.Api.delete_message(message_id="MSG_ID")

# Указание аккаунта (множественные аккаунты)
result = await ob12.Api.Using("main").get_self_info()

# Расширения платформы
result = await ob12.Api.call("extend_action", param=1)
```

> Поддерживаемые действия определяются реализацией бэкенда (NapCat/Lagrange/LLOneBot и др.); действия, которые не поддерживаются бэкендом, возвращают ошибку и прозрачно передаются.

## Операции с запросами (Request DSL)

На основе стандарта OneBot12, действие handle_quick_request обрабатывает запросы от друзей и приглашения в группы, позволяя принять или отклонить их:

### Удобные методы Event

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    if event.get("platform") != "onebot12":
        return
    comment = event.get("comment", "")
    if comment == "passphrase":
        await event.approve()      # Принять
    else:
        await event.reject()       # Отклонить
```

### Ручное вызов Request DSL

```python
await ob12.Request("request_flag").accept()
await ob12.Request("request_flag").reject()
await ob12.Request("request_flag").Using("main").accept()
```

## Типы поддерживаемых сообщений

Все методы отправки реализованы с использованием цепочечного синтаксиса, например:

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# Отправка с использованием аккаунта по умолчанию
await onebot12.Send.To("group", group_id).Text("Hello World!")

# Отправка с указанием конкретного аккаунта
await onebot12.Send.To("group", group_id).Account("main").Text("Сообщение от основного аккаунта")
```

### Неразличительность регистра

Все методы отправки и методы цепочечного вызова поддерживают неразличительность регистра, адаптер автоматически сопоставляет правильные имена методов:

```python
# Все следующие вызовы эквивалентны
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# Методы цепочечного вызова также поддерживают неразличительность регистра
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### Вызов несуществующих методов

При вызове несуществующего метода адаптер возвращает удобное текстовое уведомление, а не выбрасывает исключение:

```python
# Вызов несуществующего метода
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# Возвращаемый результат — текстовое сообщение
# Текст сообщения: [Неподдерживаемый тип отправки] Имя метода: UnsupportedMethod, Параметры: [args[0]: 'test']
```

### Основные типы сообщений

- `.Text(text: str)` — отправка текстового сообщения
- `.Image(file: Union[str, bytes], filename: str = "image.png")` — отправка сообщения с изображением (поддержка URL, Base64 или bytes)
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")` — отправка аудиосообщения
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")` — отправка голосового сообщения (альтернативное имя для Audio, совместимо с OneBot11)
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")` — отправка видеосообщения

### Методы цепочечного вызова (возвращают self для поддержки цепочечного вызова)

- `.At(user_id: Union[str, int])` — упоминание пользователя (метод можно вызывать несколько раз)
- `.AtAll()` — упоминание всех участников
- `.Reply(message_id: Union[str, int])` — ответ на сообщение

### Отправка сообщений в исходном формате

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)` — отправка сообщения в формате OneBot12 (соответствует правилам именования)

### Другие типы сообщений

- `.Sticker(file_id: str)` — отправка стикера/эмодзи
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")` — отправка геолокации

### Функции управления

- `.Recall(message_id: Union[str, int])` — удаление сообщения
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])` — редактирование сообщения
- `.Raw(message_segments: List[Dict])` — отправка сообщений в формате OneBot12
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")` — отправка сообщений в пакетном режиме

## Стандартные события OneBot12

Адаптер OneBot12 полностью соответствует стандарту OneBot12, формат событий не требует преобразования и передаётся непосредственно в фреймворк.

### Нововведение: Поле типа исходного события

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

# Сообщение в группе
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
    "comment": "Сообщение приглашения",
    "flag": "request-flag",
    "time": 1234567890
}

# Запрос на приглашение в группу
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "Сообщение приглашения",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### События метаданных (Meta Events)

```python
// Событие жизненного цикла
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

// Событие пульсации
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

Для каждого аккаунта можно настроить следующие параметры:

- `mode`: Режим работы аккаунта ("server" или "client")
- `server_path`: Путь WebSocket для режима "server"
- `server_token`: Токен аутентификации для режима "server" (необязательно)
- `client_url`: Адрес WebSocket для режима "client"
- `client_token`: Токен аутентификации для режима "client" (необязательно)
- `enabled`: Включён ли аккаунт
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

Если не настроены никакие аккаунты, адаптер создаст следующую конфигурацию по умолчанию:

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## Возвращаемые значения методов отправки

### Методы отправки сообщений
Все методы отправки сообщений (например, `.Text()`, `.Image()`, `.Raw_ob12()` и т. д.) возвращают объект `asyncio.Task`, который можно непосредственно ожидать для получения результата отправки:

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### Методы цепочечного изменения
Все методы цепочечного изменения (например, `.At()`, `.AtAll()`, `.Reply()`) возвращают `self`, что позволяет использовать цепочку вызовов:

```python
# Комбинирование нескольких методов изменения
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("Текст")
```

## Стандарт ответа API

Адаптер следует стандартизированному формату возврата ErisPulse (`standards/api-response.md`):

```python
# Успешный ответ
{
    "status": "ok",              # Обязательно: статус выполнения
    "retcode": 0,                # Обязательно: код возврата (0 означает успех)
    "data": {                     # Обязательно: данные ответа
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       # Обязательно: ID сообщения (пустая строка, если отсутствует)
    "message": "",                # Обязательно: сообщение об ошибке (пусто при успехе)
    "echo": "1234",               # Необязательно: возвращается как есть из запроса echo
    "onebot12_raw": {...}        # Необязательно: исходные данные ответа
}

# Ответ об ошибке
{
    "status": "failed",           # Обязательно: статус выполнения
    "retcode": 10003,            # Обязательно: код возврата (ненулевой означает ошибку)
    "data": None,                # Обязательно: значение null при ошибке
    "message_id": "",            # Обязательно: пустая строка при ошибке
    "message": "Отсутствуют обязательные параметры",    # Обязательно: описание ошибки
    "echo": "1234",              # Необязательно: возвращается как есть из запроса echo
    "onebot12_raw": {...}        # Необязательно: исходные данные ответа
}
```

### Спецификация кодов ошибок

Следует стандартным кодам ошибок OneBot12:

- **0**: Успех
- **1xxxx**: Ошибка запроса действия
- **2xxxx**: Ошибка обработчика действия
- **3xxxx**: Ошибка выполнения действия (33001 — тайм-аут сети)

### Синтаксис отправки с несколькими аккаунтами

```python
# Метод выбора аккаунта
await onebot12.Send.Using("main").To("group", 123456).Text("Сообщение от основного аккаунта")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# Способ вызова API
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## Асинхронная обработка

Адаптер OneBot12 использует асинхронную неблокирующую архитектуру:

1. Отправка сообщений не блокирует цикл обработки событий
2. Множественные операции отправки могут выполняться одновременно
3. Ответы API обрабатываются своевременно
4. Соединение WebSocket остается активным
5. Параллельная обработка нескольких аккаунтов, каждый аккаунт работает независимо

## Обработка ошибок

Адаптер предоставляет комплексную систему обработки ошибок:

1. Автоматическое повторное подключение при сетевых сбоях (поддерживается независимое повторное подключение для каждого аккаунта с интервалом 30 секунд)
2. Обработка превышения времени ожидания вызова API (фиксированное время ожидания 30 секунд)
3. Автоматическая повторная отправка сообщений при неудачной отправке (максимум 3 попытки повтора)
4. При вызове не поддерживаемых методов возвращается понятное текстовое уведомление

## Расширенная обработка событий

В режиме нескольких учетных записей все события автоматически сопровождаются информацией об учетной записи:

```python
{
    "type": "message",
    "onebot12_raw_type": "message",  // Исходный тип события
    "detail_type": "private",
    "self": {"user_id": "123456"},  // ID учетной записи, отправившей событие (стандартное поле)
    "platform": "onebot12",
    // ... другие поля события
}
```

## Управление интерфейсом

```python
# Получить информацию обо всех аккаунтах
accounts = onebot12.accounts

# Проверить статус подключения аккаунта
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# Динамически включить/отключить аккаунт (требуется перезапуск адаптера)
onebot12.accounts["test"].enabled = False
```

## Стандартные возможности OneBot12

### Стандартный формат сообщений

OneBot12 использует стандартизированный формат сообщений:

```python
# Текстовое сообщение
{"type": "text", "data": {"text": "Привет"}}

# Изображение
{"type": "image", "data": {"file_id": "image-id"}}

# Упоминание
{"type": "mention", "data": {"user_id": "user-id", "user_name": "Username"}}

# Ответ на сообщение
{"type": "reply", "data": {"message_id": "msg-id"}}
```

### Стандартные API

Соблюдение стандартных API OneBot12:

- `send_message`: Отправка сообщения
- `delete_message`: Отмена сообщения
- `edit_message`: Редактирование сообщения
- `get_message`: Получение сообщения
- `get_self_info`: Получение информации о себе
- `get_user_info`: Получение информации о пользователе
- `get_group_info`: Получение информации о группе

## Рекомендуемые практики

1. **Управление конфигурацией**: Рекомендуется использовать конфигурации с несколькими аккаунтами для разделения роботов с различным назначением
2. **Обработка ошибок**: Всегда проверяйте статус возвращаемых API-вызовов
3. **Отправка сообщений**: Используйте подходящие типы сообщений, избегайте отправки не поддерживаемых сообщений
4. **Мониторинг подключения**: Регулярно проверяйте состояние подключения, обеспечивая доступность сервиса
5. **Оптимизация производительности**: При массовой отправке используйте метод Batch для уменьшения сетевых накладных расходов
6. **Вызовы методов**: Рекомендуется использовать стандартное название с большой буквы (например, `.Text()`), но также поддерживается нижний регистр для обеспечения совместимости с различными стилями программирования (такой способ может быть несовместим со старыми версиями)