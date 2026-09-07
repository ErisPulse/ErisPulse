# Стандартизированные операции запросов ErisPulse

Данный документ определяет стандартизированные операции с событиями запросов в адаптере ErisPulse, включая требования к полям событий запросов, использование DSL запросов и требования к реализации адаптера.

## 1. Обзор

Событие запроса (type: "request") — это специальный тип события, определённый в стандарте OneBot12, который представляет запрос, требующий принятия решения ботом (например, запрос на добавление в друзья, приглашение в группу и т.д.).

В отличие от событий сообщений, события запросов требуют **двустороннего взаимодействия**:
1. **Приём**: адаптер преобразует родные события запроса платформы в стандартные события запросов
2. **Ответ**: модуль выполняет операции с помощью DSL запросов или методов `Event.approve()`/`Event.reject()`

```
Событие родного запроса платформы
    │
    ▼
Converter.convert()        ← Реализация адаптера (прямое преобразование)
    │
    ▼
Стандартное событие запроса (с request_id)
    │
    ├─→ Обработчик модуля @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← Принять запрос
    │       └─→ event.reject()      ← Отклонить запрос
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← Переопределение в адаптере
    │               │
    │               ▼
    │       Вызов API платформы
    │
    └─→ Или через прямое взаимодействие с адаптером
            await adapter.Request("req_id").accept()
```

## 2. Требования к полям события запроса

### 2.1 Стандартные поля

Событие запроса, помимо обязательных полей стандарта OneBot12, должно содержать следующие поля:

| Поле | Тип | Обязательно | Описание |
|------|------|------|------|
| `request_id` | string | **Рекомендуется** | Идентификатор запроса, используется для принятия/отклонения |
| `user_id` | string | Да | ID пользователя, отправившего запрос |
| `user_nickname` | string | Нет | Никнейм пользователя, отправившего запрос |
| `comment` | string | Нет | Комментарий к запросу |

### 2.2 Поле `request_id`

`request_id` — ключевой идентификатор для операций запроса:

- **Назначение**: идентифицирует запрос, который можно обработать, используется DSL запросов
- **Правила генерации**:
  - Предпочтительно использовать родной идентификатор запроса платформы (например, поле `flag` OneBot11, `chat_invite_link` Telegram и т.д.)
  - Если платформа не предоставляет родной идентификатор, адаптер должен сгенерировать уникальный (рекомендуемый формат: `{platform}_{timestamp}_{user_id}`)
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

## 3. DSL запросов

### 3.1 Цепочка вызовов

`Request` предоставляет интерфейс цепочки вызовов, аналогичный `Send`:

```python
# Базовое использование
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Указание аккаунта бота
await adapter.Request("req_id").Using("bot1").accept()

# Добавление комментария (через kwargs)
await adapter.Request("req_id").accept(comment="Добро пожаловать")
await adapter.Request("req_id").reject(comment="Временно не добавляю")

# Комбинирование
await adapter.Request("req_id").Using("bot1").accept(comment="Добро пожаловать")
```

### 3.2 Список методов

| Метод | Описание | Возвращаемое значение |
|------|------|--------|
| `Using(account_id)` | Указывает аккаунт бота для выполнения операции | `RequestDSL` (поддерживает цепочку вызовов) |
| `accept(**kwargs)` | Принять запрос | `asyncio.Task` (await возвращает стандартный ответ) |
| `reject(**kwargs)` | Отклонить запрос | `asyncio.Task` (await возвращает стандартный ответ) |

### 3.3 Формат возвращаемого значения

Операция возвращает стандартный формат ответа API:

**Успешно**:
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

Класс `Event` предоставляет удобные методы, подходящие для обработчиков событий запросов:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Получение идентификатора запроса
    request_id = event.get_request_id()
    if not request_id:
        print("Предупреждение: событие запроса не содержит request_id")
        return
    
    # Принять запрос
    result = await event.approve()
    
    # Или отклонить запрос
    # result = await event.reject(comment="Временно не добавляю в друзья")
    
    # Проверка результата
    if result.get("status") == "ok":
        print("Операция выполнена успешно")
    else:
        print(f"Операция не удалась: {result.get('message')}")
```

### 4.1 Список методов Event

| Метод | Описание | Возвращаемое значение |
|------|------|--------|
| `get_request_id()` | Получить идентификатор запроса | `str` |
| `approve(comment=None)` | Принять текущее событие запроса | Стандартный формат ответа |
| `reject(comment=None)` | Отклонить текущее событие запроса | Стандартный формат ответа |

## 5. Требования к реализации адаптера

### 5.1 Требования к конвертеру

Конвертер адаптера, при преобразовании событий запросов, **должен** правильно установить поле `request_id`:

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """Преобразование родного события запроса платформы"""
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
    Извлечение идентификатора запроса из родного события платформы
    
    Сначала используется родной идентификатор, если нет — генерируется уникальный
    """
    # Сначала используем родной идентификатор
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # В качестве резервного: генерируем уникальный идентификатор
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
        """Реализация операций запросов для MyPlatform"""
        
        def accept(self, **kwargs):
            """
            Принять запрос
            
            :param kwargs: дополнительные параметры, например comment="Комментарий"
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
                        "message": f"Операция запроса не удалась: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 Платформа не поддерживает операции запросов

Если платформа не поддерживает запросы на добавление в друзья/приглашения в группы (например, некоторые платформы обрабатывают запросы автоматически), адаптер может:

1. **Не переопределять внутренний класс `Request`**: использовать базовую реализацию, при вызове `accept()`/`reject()` возвращать `retcode=10002`
2. **Не генерировать `request_id` при преобразовании**: не создавать `request_id`, чтобы `event.approve()` выбросил `ValueError`
3. **Записывать логи**: в `accept`/`reject` записывать предупреждения и возвращать соответствующие коды ошибок

### 5.4 Итог: Send и Request параллельно

Адаптер имеет два параллельных внутренних класса DSL, каждый из которых отвечает за свою задачу:

```
BaseAdapter
├── Send(SendDSL)     ← Отправка сообщений
│   ├── Raw_ob12()    ← Должен быть реализован
│   ├── Text()        ← Рекомендуется реализовать
│   └── Image()       ← Реализовать по необходимости
│
└── Request(RequestDSL) ← Операции запросов
    ├── accept()        ← Реализовать по необходимости
    └── reject()        ← Реализовать по необходимости
```

### 5.5 Примечания к `__init__` адаптера

При переопределении `__init__` внутреннего класса `Request` необходимо передать параметры и вызвать `super().__init__()`, подробнее см. [Введение в разработку адаптеров - Примечания к `__init__`](../developer-guide/adapters/getting-started.md#init-注意事项) (`Request` аналогично, параметры: `adapter, request_id, account_id`).

## 6. Список проверки реализации адаптера

### Основные требования
- [ ] При переопределении `__init__` вызван `super().__init__()` (успешная инициализация фабрики Send / Request)

### Преобразование событий запросов
- [ ] Событие запроса содержит поле `request_id` (рекомендуется)
- [ ] `detail_type` корректно отображается в `"friend"` или `"group"`
- [ ] Сохраняются исходные данные платформы в поле `{platform}_raw`
- [ ] Правила генерации `request_id` описаны в документации

### Операции запросов
- [ ] Внутренний класс `Request` реализован (если платформа поддерживает операции запросов)
- [ ] Метод `accept()` реализован
- [ ] Метод `reject()` реализован
- [ ] Операции возвращают стандартный формат ответа API
- [ ] Операции, которые не поддерживаются, возвращают `retcode=10002`
- [ ] Ошибки сети возвращают `retcode=33xxx` (соответствует стандарту ответа API)

## 7. Расширение кодов ошибок

Рекомендуемые коды ошибок на уровне реализации адаптера, связанные с операциями запросов (соответствует [стандарту ответа API](api-response.md) §3.2, коды ошибок платформы в диапазоне `34xxx`):

| Код ошибки | Название ошибки | Описание |
|-------|-------|------|
| 34001 | Request Not Found | Запрос не существует или просрочен |
| 34002 | Request Already Handled | Запрос уже обработан |
| 34003 | Request Not Supported | Платформа не поддерживает данную операцию запроса |
| 34004 | Permission Denied | Бот не имеет прав на обработку этого запроса (возвращается платформой) |

> **Граница с кодами фреймворка**: вышеуказанные `340xx` — это **ошибки платформы/адаптера** при обработке запроса; фреймворк ErisPulse при禁用某模块的 request 动作时，**在调用适配器之前** 直接返回 `34601`（Action Denied，见 [API 响应标准 §5.3](api-response.md#53-框架扩展返回码34xxx-平台错误段的低三位自定义)），两者 не заменяют друг друга: сначала проходит `34601` как фреймворк-шлагбаум, затем платформа возвращает `340xx`.

## 8. Связанные документы

- [Стандарт преобразования событий](event-conversion.md) - Полный стандарт преобразования событий
- [Стандарт ответа API](api-response.md) - Стандарт формата ответа API адаптера
- [Спецификация методов отправки](send-method-spec.md) - Назначение и параметры методов класса Send
- [Стандарт типов сессий](session-types.md) - Определения и отображения типов сессий