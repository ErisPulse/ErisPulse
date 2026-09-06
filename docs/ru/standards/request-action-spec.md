# Стандарт операций запроса ErisPulse

Документ определяет стандартизированный стандарт для операций событий запроса в адаптере ErisPulse, включая требования к полям событий запроса, использование DSL запроса и требования к реализации адаптера.

## 1. Обзор

Событие запроса (`type: "request"`) — это специальный тип событий, определённый в стандарте OneBot12, представляющий запрос, требующий принятия решения ботом (например, запрос на добавление в друзья, приглашение в группу и т.д.).

В отличие от событий сообщений, события запроса требуют **двустороннего взаимодействия**:
1. **Приём**: адаптер преобразует исходное событие запроса платформы в стандартное событие запроса
2. **Ответ**: модуль выполняет операцию с помощью DSL запроса или `Event.approve()`/`Event.reject()`

```
Событие исходного запроса платформы
    │
    ▼
Converter.convert()        ← Реализация адаптера (обратное преобразование)
    │
    ▼
Стандартное событие запроса (с request_id)
    │
    ├─→ Обработчик модуля @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← Согласие с запросом
    │       └─→ event.reject()      ← Отказ в запросе
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← Переопределение адаптером
    │               │
    │               ▼
    │       Вызов API платформы
    │
    └─→ Или непосредственное использование адаптера
            await adapter.Request("req_id").accept()
```

## 2. Требования к полям события запроса

### 2.1 Стандартные поля

Событие запроса, помимо обязательных полей стандарта OneBot12, должно содержать следующие поля:

| Поле | Тип | Обязательно | Описание |
|------|------|------|------|
| `request_id` | string | **Рекомендуется** | Идентификатор запроса, используется для согласия/отказа |
| `user_id` | string | Да | Идентификатор пользователя, отправившего запрос |
| `user_nickname` | string | Нет | Никнейм отправителя |
| `comment` | string | Нет | Комментарий к запросу |

### 2.2 Поле `request_id`

`request_id` — это ключевой идентификатор запроса:

- **Назначение**: идентифицирует запрос, который можно обработать, используется в DSL запроса
- **Правила генерации**:
  - Предпочтительно использовать идентификатор запроса, предоставляемый платформой (например, поле `flag` OneBot11, `chat_invite_link` Telegram и т.д.)
  - Если платформа не предоставляет идентификатор запроса, адаптер должен сгенерировать уникальный идентификатор (рекомендуемый формат: `{platform}_{timestamp}_{user_id}`)
- **Уникальность**: должен быть уникален в пределах одной платформы
- **Поведение при отсутствии**: если `request_id` отсутствует, `event.approve()` / `event.reject()` выбросят `ValueError`

### 2.3 Пример события запроса

```json
{
  "id": "evt_123456",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "Пожалуйста, добавьте в друзья",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. DSL запроса

### 3.1 Цепочечный вызов

`Request` предоставляет интерфейс цепочечного вызова, аналогичный `Send`:

```python
# Базовое использование
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Указание аккаунта бота
await adapter.Request("req_id").Using("bot1").accept()

# С комментарием (через kwargs)
await adapter.Request("req_id").accept(comment="Добро пожаловать")
await adapter.Request("req_id").reject(comment="Временно не добавляю")

# Комбинированное использование
await adapter.Request("req_id").Using("bot1").accept(comment="Добро пожаловать")
```

### 3.2 Список методов

| Метод | Описание | Возвращаемое значение |
|------|------|--------|
| `Using(account_id)` | Указание аккаунта бота для выполнения операции | `RequestDSL` (поддерживает цепочечный вызов) |
| `accept(**kwargs)` | Согласие с запросом | `asyncio.Task` (ожидание возвращает стандартный ответ) |
| `reject(**kwargs)` | Отказ в запросе | `asyncio.Task` (ожидание возвращает стандартный ответ) |

### 3.3 Формат возвращаемого значения

Операция возвращает стандартный формат ответа API:

**Успех**:
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**Ошибка**:
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "Запрос просрочен или не существует"
}
```

**Не реализовано** (адаптер не переопределил `accept`/`reject`):
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "Платформа MyAdapter не реализовала операцию запроса (accept)"
}
```

## 4. Удобные методы Event

Класс `Event` предоставляет удобные методы, подходящие для использования в обработчиках событий запроса:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Получение идентификатора запроса
    request_id = event.get_request_id()
    if not request_id:
        print("Предупреждение: событие запроса не содержит request_id")
        return
    
    # Согласие с запросом
    result = await event.approve()
    
    # Или отказ в запросе
    # result = await event.reject(comment="Временно не добавляю")
    
    # Проверка результата
    if result.get("status") == "ok":
        print("Операция выполнена успешно")
    else:
        print(f"Операция не удалась: {result.get('message')}")
```

### 4.1 Список методов Event

| Метод | Описание | Возвращаемое значение |
|------|------|--------|
| `get_request_id()` | Получение идентификатора запроса | `str` |
| `approve(comment=None)` | Согласие с текущим событием запроса | Стандартный формат ответа |
| `reject(comment=None)` | Отказ в текущем событии запроса | Стандартный формат ответа |

## 5. Требования к реализации адаптера

### 5.1 Требования к конвертеру

Конвертер адаптера при преобразовании событий запроса **должен** правильно устанавливать поле `request_id`:

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """Конвертация исходного события запроса платформы"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" или "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← Ключевое поле
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    Извлечение идентификатора запроса из исходного события платформы
    
    Предпочтительно использовать идентификатор запроса платформы, если нет — генерировать уникальный ID
    """
    # Предпочтительно использовать идентификатор платформы
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # Запасной вариант: генерация уникального ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Реализация внутреннего класса Request

Адаптер переопределяет `accept` и `reject` в внутреннем классе `Request`:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """Реализация операций запроса для MyPlatform"""
        
        def accept(self, **kwargs):
            """
            Согласие с запросом
            
            :param kwargs: Расширенные параметры, например comment="заметка"
            :return: asyncio.Task
            """
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=True,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"Операция запроса не удалась: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """Отказ в запросе"""
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=False,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"Операция запроса не удалась: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 Платформа не поддерживает операции запроса

Если платформа не поддерживает операции запроса/приглашения (например, некоторые платформы обрабатывают запросы автоматически), адаптер может:

1. **Не переопределять внутренний класс `Request`**: использовать базовую реализацию, вызов `accept()`/`reject()` возвращает `retcode=10002`
2. **Не генерировать `request_id` при конвертации**: не создавать `request_id`, заставляя `event.approve()` выбросить `ValueError`
3. **Запись в лог**: в `accept`/`reject` записывать предупреждение и возвращать соответствующий код ошибки

### 5.4 Итог: Send и Request параллельны

Адаптер имеет два параллельных внутренних класса DSL, каждый выполняет свою задачу:

```
BaseAdapter
├── Send(SendDSL)     ← Отправка сообщений
│   ├── Raw_ob12()    ← Обязательно реализовать
│   ├── Text()        ← Рекомендуется реализовать
│   └── Image()       ← Реализовать по мере необходимости
│
└── Request(RequestDSL) ← Операции запроса
    ├── accept()        ← Реализовать по мере необходимости
    └── reject()        ← Реализовать по мере необходимости
```

### 5.5 Примечания к `__init__` адаптера

При переопределении `__init__` внутреннего класса `Request` необходимо передавать параметры и вызывать `super().__init__()` (см. [Введение в разработку адаптеров - Примечания к `__init__`](../developer-guide/adapters/getting-started.md#init-注意事项) (аналогично `Request`, параметры: `adapter, request_id, account_id`)).

## 6. Проверочный список реализации адаптера

### Основные требования
- [ ] При переопределении `__init__` вызван `super().__init__()` (успешная инициализация фабрики Send / Request)

### Преобразование событий запроса
- [ ] Событие запроса содержит поле `request_id` (рекомендуется)
- [ ] `detail_type` правильно отображается в `"friend"` или `"group"`
- [ ] Сохранён исходный данные платформы в поле `{platform}_raw`
- [ ] Правила генерации `request_id` описаны в документации

### Операции запроса
- [ ] Внутренний класс `Request` реализован (если платформа поддерживает операции запроса)
- [ ] Метод `accept()` реализован
- [ ] Метод `reject()` реализован
- [ ] Операция возвращает стандартный формат ответа API
- [ ] Операции, которые платформа не поддерживает, возвращают `retcode=10002`
- [ ] Ошибки сети возвращают `retcode=33xxx` (соответствует стандарту ответа API)

## 7. Расширение кодов ошибок

Рекомендуемые коды ошибок (в рамках `34xxx`, нижние три цифры — пользовательские) для **уровня реализации адаптера** (см. [Стандарт ответа API](api-response.md) §3.2):

| Код ошибки | Название ошибки | Описание |
|-------|-------|------|
| 34001 | Request Not Found | Запрос не существует или просрочен |
| 34002 | Request Already Handled | Запрос уже обработан |
| 34003 | Request Not Supported | Платформа не поддерживает данную операцию запроса |
| 34004 | Permission Denied | Бот не имеет прав на обработку запроса (возвращено платформой) |

> **Граница с кодами фреймворка**: вышеуказанные `340xx` — это **ошибки платформы/адаптера** при обработке запроса; если фреймворк ErisPulse отключает действие `request` модуля в `scope.actions`, **до вызова адаптера** он возвращает `34601` (Action Denied, см. [Стандарт ответа API §5.3](api-response.md#53-фреймворк-расширенные-коды-возврата-34xxx-нижние-три-цифры-пользовательские)), оба уровня ошибок не заменяют друг друга: сначала проходит фреймворк `34601`, затем платформа `340xx`.

## 8. Связанные документы

- [Стандарт преобразования событий](event-conversion.md) — полный стандарт преобразования событий
- [Стандарт ответа API](api-response.md) — стандарт формата ответа API адаптера
- [Спецификация методов отправки](send-method-spec.md) — стандарт именования и параметров методов класса Send
- [Стандарт типов сессий](session-types.md) — определение и сопоставление типов сессий