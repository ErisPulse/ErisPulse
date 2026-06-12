# SendDSL: Подробное руководство

SendDSL — это интерфейс отправки сообщений со стилем цепных вызовов, предоставляемый адаптером ErisPulse.

## Основные способы вызова

### 1. Указание типа и ID

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. Указание только ID

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. Указание аккаунта отправки

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. Комбинированное использование

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## Цепочка методов

```
Using/Account() → To() → [Методы-модификаторы] → [Методы отправки]
```

## Методы отправки

Все методы отправки должны возвращать объект `asyncio.Task`.

### Базовые методы

| Имя метода | Описание | Возвращаемое значение |
|--------|------|---------|
| `Text(text: str)` | Отправка текстового сообщения | `asyncio.Task` |
| `Image(file: bytes \| str)` | Отправка изображения | `asyncio.Task` |
| `Voice(file: bytes \| str)` | Отправка голосового сообщения | `asyncio.Task` |
| `Video(file: bytes \| str)` | Отправка видео | `asyncio.Task` |
| `File(file: bytes \| str)` | Отправка файла | `asyncio.Task` |

### Протокольные методы

| Имя метода | Описание | Возвращаемое значение | Обязательно |
|--------|------|---------|---------|
| `Raw_ob12(message)` | Отправка сообщения в формате OneBot12 | `asyncio.Task` | **Обязательная реализация** |

> **Важно**: `Raw_ob12` — это базовый метод адаптера, **его необходимо реализовать**. Это единая точка входа для обратного преобразования (OneBot12 → Платформа). Если не реализовано, базовый класс запишет лог ошибок и вернет стандартный ответ об ошибке (`status: "failed"`, `retcode: 10002`). Стандартные методы (`Text`, `Image` и др.) должны внутри себя делегировать вызовы `Raw_ob12`.

## Методы-модификаторы

Методы-модификаторы возвращают `self`, чтобы поддерживать цепные вызовы.

### Метод At

```python
# @ отдельного пользователя
await adapter.Send.To("group", "123").At("456").Text("Привет")

# @ нескольких пользователей
await adapter.Send.To("group", "123").At("456").At("789").Text("Здравствуйте, все")
```

### Метод AtAll

```python
# @ всем участникам
await adapter.Send.To("group", "123").AtAll().Text("Всем привет")
```

### Метод Reply

```python
# Ответ на сообщение
await adapter.Send.To("group", "123").Reply("msg_id").Text("Текст ответа")
```

### Комбинированные модификаторы

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("Ответ на сообщение, к которому обращены")
```

## Управление аккаунтами

### Метод Using

`Using()` используется для указания аккаунта для отправки сообщения. Передаваемый идентификатор сопоставляется по следующему приоритету:

1. **Имя аккаунта** — ключ в конфигурации (например, `"default"`, `"bot1"`)
2. **Внедренный bot_id** — идентификатор, автоматически внедряемый при преобразовании событий
3. **Любое строковое поле** — другое строковое поле в конфигурации
4. **Fallback** — первый включенный аккаунт

```python
# Использование имени аккаунта
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# Использование bot_id (то есть self.user_id из события)
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

### Метод Account

Метод `Account` эквивалентен `Using`:

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## Асинхронная обработка

### Не ожидание результата

```python
# Сообщение отправляется в фоне
task = adapter.Send.To("user", "123").Text("Hello")

# Выполнение других операций
# ...
```

### Ожидание результата

```python
# Прямое await для получения результата
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"Результат отправки: {result}")

# Сначала сохранение Task, ожидание позже
task = adapter.Send.To("user", "123").Text("Hello")
# ... другие операции ...
result = await task
```

## Соглашения об именовании

### Нейминг PascalCase

Все методы отправки используют верблюжий регистр (PascalCase):

```python
# ✅ Правильно
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ Неправильно
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### Платформенно-специфические методы

Не рекомендуется добавлять методы с префиксом платформы:

```python
# ✅ Рекомендуется
def Sticker(self, sticker_id: str):
    pass

# ❌ Не рекомендуется
def TelegramSticker(self, sticker_id: str):
    pass
```

Используйте методы `Raw` вместо этого:

```python
# ✅ Рекомендуется
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ Не рекомендуется
def TelegramSticker(self, ...):
    pass
```

## Возвращаемое значение

### Объект Task

Все методы отправки возвращают `asyncio.Task`:

```python
import asyncio

def Text(self, text: str):
    return asyncio.create_task(
        self._adapter.call_api(
            endpoint="/send",
            content=text,
            recvId=self._target_id,
            recvType=self._target_type
        )
    )
```

### Стандартизированный ответ

Метод `call_api` должен возвращать стандартизированный ответ. Рекомендуется использовать методы `make_response()` / `make_error()`:

```python
async def call_api(self, endpoint: str, **params):
    try:
        result = await self._do_api_call(endpoint, **params)
        return self.make_response(
            data=result.get("data"),
            message_id=result.get("message_id", ""),
            raw=result,
        )
    except Exception as e:
        return self.make_error(message=str(e))
```

Также поддерживается ручное создание (старый способ по-прежнему совместим):

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok" or "failed",
        "retcode": 0 or error_code,
        "data": {...},
        "message_id": "msg_id" or "",
        "message": "",
        "{platform}_raw": raw_response
    }
```

## Полный пример

### Базовое использование

```python
from ErisPulse.Core import adapter

my_adapter = adapter.get("myplatform")

# Отправка текста
await my_adapter.Send.To("user", "123").Text("Hello World!")

# Отправка изображения
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# Отправка файла
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### Цепные вызовы

```python
# @ пользователя + ответ
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("Ответ на сообщение, к которому обращены")

# @ всех + несколько модификаторов
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("Текст объявления")
```

### Исходные сообщения и построение сообщений

`Raw_ob12` является ключевой точкой входа для обратного преобразования (получение сегментов сообщений OB12 → вызов API платформы), а `MessageBuilder` — это инструмент построения сегментов сообщений в стиле цепочки, используемый в связке с ним.

> Подробные спецификации по реализации `Raw_ob12`, а также инструкции по использованию `MessageBuilder` и примеры кода можно найти:
> - [Спецификация методов отправки §6: Правила обратного преобразования](../../standards/send-method-spec.md#6-правила-обратного-преобразования-onebot12--платформа)
> - [Спецификация методов отправки §11: Построитель сообщений (MessageBuilder)](../../standards/send-method-spec.md#11-построитель-сообщений-messagebuilder)

## Связанные документы

- [Введение в разработку адаптеров](getting-started.md) — Создание адаптера
- [Основные концепции адаптера](core-concepts.md) — Понимание архитектуры адаптера
- [Рекомендуемые практики адаптера](best-practices.md) — Создание адаптеров высокого качества
- [Спецификация методов отправки](../../standards/send-method-spec.md) — Полная спецификация методов отправки