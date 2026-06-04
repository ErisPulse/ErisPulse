# ErisPulse Спецификация операций запросов

В этом документе определяется стандартная спецификация операций запросов событий в адаптере ErisPulse, включая требования к полям событий запросов, способ использования DSL запросов и требования к реализации адаптера.

## 1. Обзор

Событие запроса (`type: "request"`) — это специальный тип события, определенный в стандарте OneBot12, представляющий собой запрос, требующий решения от бота (например, запросы в друзья, приглашения в группы и т.д.).

В отличие от событий сообщений, события запросов требуют **двустороннего взаимодействия**:
1. **Прием:** Адаптер преобразует нативный платформенный запрос в стандартное событие запроса.
2. **Ответ:** Модуль выполняет операцию через DSL `Request` или методы `Event.approve()`/`Event.reject()`.

```
Необработанное событие запроса платформы
    │
    ▼
Converter.convert()        ← реализация адаптера (прямое преобразование)
    │
    ▼
Стандартное событие запроса (включая request_id)
    │
    ├─→ Обработчик модуля @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← согласовать запрос
    │       └─→ event.reject()      ← отклонить запрос
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← переопределение адаптера
    │               │
    │               ▼
    │       Вызов платформенного API
    │
    └─→ Или прямая операция через адаптер
            await adapter.Request("req_id").accept()
```

## 2. Требования к полям событий запроса

### 2.1 Стандартные поля

Помимо обязательных полей стандарта OneBot12, событие запроса должно содержать следующие поля:

| Поле | Тип | Обязательно | Описание |
|------|------|------|------|
| `request_id` | string | **Сильно рекомендуется** | Идентификатор запроса, используемый для операций согласования/отклонения |
| `user_id` | string | Да | Идентификатор инициатора запроса |
| `user_nickname` | string | Нет | Никнейм инициатора запроса |
| `comment` | string | Нет | Примечание к запросу |

### 2.2 Поле `request_id`

`request_id` является ключевым идентификатором для операций запроса:

- **Назначение:** Идентификация доступного для обработки запроса для использования в DSL `Request`.
- **Правила генерации**:
  - В первую очередь следует использовать нативный идентификатор запроса платформы (например, поле `flag` в OneBot11, `chat_invite_link` в Telegram и т.д.).
  - Если платформа не предоставляет нативный ID запроса, адаптер должен сгенерировать уникальный идентификатор (рекомендуемый формат: `{platform}_{timestamp}_{user_id}`).
- **Уникальность:** Должен быть уникальным в рамках одной платформы.
- **Поведение при отсутствии:** Когда `request_id` отсутствует, `event.approve()` / `event.reject()` выбросят `ValueError`.

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

## 3. Request DSL

### 3.1 Цепное вызов (Chain Calling)

`Request` предоставляет интерфейс с цепными вызовами (chaining), аналогичный стилю `Send`:

```python
# Базовое использование
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Указание учетной записи бота
await adapter.Request("req_id").Using("bot1").accept()

# Добавление примечания (через kwargs)
await adapter.Request("req_id").accept(comment="Добро пожаловать")
await adapter.Request("req_id").reject(comment="Пока не добавляю")

# Комбинированное использование
await adapter.Request("req_id").Using("bot1").accept(comment="Добро пожаловать")
```

### 3.2 Список методов

| Метод | Описание | Возвращаемое значение |
|------|------|--------|
| `Using(account_id)` | Указание учетной записи бота для выполнения операции | `RequestDSL` (поддержка цепных вызовов) |
| `accept(**kwargs)` | Согласовать запрос | `asyncio.Task` (возвращает стандартный ответ после await) |
| `reject(**kwargs)` | Отклонить запрос | `asyncio.Task` (возвращает стандартный ответ после await) |

### 3.3 Формат возвращаемого значения

Операции возвращают стандартный формат ответа API:

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
    "message": "Запрос истек или не существует"
}
```

**Не реализовано** (адаптер не переопределил `accept`/`reject`):
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "Платформа MyAdapter не реализует операции с запросами (accept)"
}
```

## 4. Удобные методы Event

Класс-обертка `Event` предоставляет удобные методы, подходящие для использования в обработчиках событий запроса:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Проверка ID запроса
    request_id = event.get_request_id()
    if not request_id:
        print("Предупреждение: событие запроса отсутствует request_id")
        return
    
    # Согласовать запрос
    result = await event.approve()
    
    # Или отклонить запрос
    # result = await event.reject(comment="Пока не добавляю в друзья")
    
    # Проверка результата
    if result.get("status") == "ok":
        print("Операция успешна")
    else:
        print(f"Операция не удалась: {result.get('message')}")
```

### 4.1 Список методов Event

| Метод | Описание | Возвращаемое значение |
|------|------|--------|
| `get_request_id()` | Получить ID запроса | `str` |
| `approve(comment=None)` | Согласовать текущее событие запроса | Формат стандартного ответа |
| `reject(comment=None)` | Отклонить текущее событие запроса | Формат стандартного ответа |

## 5. Требования к реализации адаптера

### 5.1 Требования к конвертеру

Конвертер адаптера должен корректно установить поле `request_id` при преобразовании события запроса:

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """Преобразование нативного платформенного события запроса"""
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
    Извлечение ID запроса из нативного события платформы
    
    В первую очередь используется нативный идентификатор платформы, 
    если нет - генерация уникального ID
    """
    # Предпочтение использованию нативного ID платформы
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # Резервный вариант: генерация уникального ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Реализация внутреннего класса Request

Адаптеру достаточно переопределить `accept` и `reject` во внутреннем классе `Request`:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """Реализация операций запросов для MyPlatform"""
        
        def accept(self, **kwargs):
            """
            Согласовать запрос
            
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
                        "message": f"Операция с запросом не удалась: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """Отклонить запрос"""
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
                        "message": f"Операция с запросом не удалась: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 Платформа не поддерживает операции запросов

Если платформа сама не поддерживает операции запросов в друзья/группы (например, некоторые платформы автоматически обрабатывают запросы), адаптер может:

1. **Не переопределять внутренний класс `Request`**: Использовать реализацию по умолчанию базового класса, при вызове `accept()`/`reject()` возвращать `retcode=10002`.
2. **Пропускать `request_id` при преобразовании**: Не генерировать `request_id`, позволяя `event.approve()` выбросить `ValueError`.
3. **Логирование**: В `accept`/`reject` записывать предупреждение и возвращать соответствующий код ошибки.

### 5.4 Итог: Send и Request параллельно

У адаптера есть два параллельных внутренних класса DSL, каждый выполняет свою задачу:

```
BaseAdapter
├── Send(SendDSL)     ← Отправка сообщений
│   ├── Raw_ob12()    ← Необходимо реализовать
│   ├── Text()        ← Рекомендуется реализовать
│   └── Image()       ← Реализация по мере необходимости
│
└── Request(RequestDSL) ← Операции запроса
    ├── accept()        ← Реализация по мере необходимости
    └── reject()        ← Реализация по мере необходимости
```

### 5.5 Примечания к адаптеру `__init__`

При переопределении `__init__` во внутреннем классе `Request`, параметры должны быть транслированы (пропущены), а `super().__init__()` должен быть вызван. Подробнее в разделе [Начало работы с адаптером - Примечания к `__init__`](../../developer-guide/adapters/getting-started.md#init-примечания) (аналогично и для `Request`, параметры: `adapter, request_id, account_id`).

## 6. Чек-лист реализации адаптера

### Базовые требования
- [ ] Если переопределен `__init__`, уже вызван `super().__init__()` (обеспечение инициализации фабрик Send / Request)

### Преобразование событий запроса
- [ ] Событие запроса содержит поле `request_id` (сильно рекомендуется)
- [ ] `detail_type` правильно сопоставлен со значением `"friend"` или `"group"`
- [ ] Исходные данные платформы сохранены в поле `{platform}_raw`
- [ ] Правила генерации `request_id` документированы

### Операции запроса
- [ ] Внутренний класс `Request` реализован (если платформа поддерживает операции запросов)
- [ ] Метод `accept()` реализован
- [ ] Метод `reject()` реализован
- [ ] Операции возвращают стандартный формат ответа API
- [ ] Не поддерживаемые операции возвращают `retcode=10002`
- [ ] Сетевые ошибки возвращают `retcode=33xxx` (соблюдение стандарта ответа API)

## 7. Расширенные коды ошибок

Рекомендуемые коды ошибок, связанные с операциями запросов (соблюдение [Стандарта ответа API](api-response.md) §3.2):

| Код ошибки | Название ошибки | Описание |
|-------|-------|------|
| 34001 | Request Not Found | Запрос не существует или истек |
| 34002 | Request Already Handled | Запрос уже обработан |
| 34003 | Request Not Supported | Платформа не поддерживает операции запросов данного типа |
| 34004 | Permission Denied | У бота нет прав на обработку этого запроса |

## 8. Связанные документы

- [Стандарт преобразования событий](event-conversion.md) - Полная спецификация преобразования событий
- [Стандарт ответа API](api-response.md) - Стандарт формата ответа API адаптера
- [Спецификация методов отправки](send-method-spec.md) - Стандарт именования методов и параметров класса Send
- [Стандарт типов сессий](session-types.md) - Определение типов сессий и отношения сопоставления