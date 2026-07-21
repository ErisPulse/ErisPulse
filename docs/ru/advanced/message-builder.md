# Подробное руководство по MessageBuilder

`MessageBuilder` — это инструмент для построения структурированных сообщений, соответствующих стандарту OneBot12, предоставленный ErisPulse. Он используется для построения структурированного содержания сообщений и работает в связке с `Send.Raw_ob12()`.

## Способы импорта

`MessageBuilder` поддерживает два способа импорта (результат одинаковый, рекомендуется использовать первый):

```python
from ErisPulse.Core.Event import MessageBuilder        # Рекомендуемый способ, импорт через пакет
from ErisPulse.Core.Event.message_builder import MessageBuilder  # Прямой импорт модуля
```

## Двухрежимная система

MessageBuilder предоставляет два режима использования, реализованных с помощью механизма описателей Python (`__get__`), чтобы обеспечить различное поведение на уровне класса и экземпляра: при вызове метода через класс, `__get__` возвращает результат выполнения статического метода; при вызове через экземпляр возвращается `self` для поддержки цепочки вызовов.

### Режим цепочечных вызовов (экземпляр)

Используется путем создания экземпляра `MessageBuilder()`. Каждый метод возвращает `self`, что позволяет использовать цепочку вызовов, и для получения списка сообщений используется `.build()`:

```python
from ErisPulse.Core.Event.message_builder import MessageBuilder

segments = (
    MessageBuilder()
    .text("Привет!")
    .image("https://example.com/photo.jpg")
    .build()
)
# [
#     {"type": "text", "data": {"text": "Привет!"}},
#     {"type": "image", "data": {"file": "https://example.com/photo.jpg"}}
# ]
```

### Режим быстрого построения (статический)

Методы вызываются напрямую через класс, каждый метод возвращает список сообщений, что подходит для построения одиночных сообщений:

```python
# Непосредственно возвращается list[dict], без .build()
segments = MessageBuilder.text("Привет!")
# [{"type": "text", "data": {"text": "Привет!"}}]
```

## Типы сообщений

| Метод | Тип | Параметры данных | Описание |
|------|------|---------|------|
| `text(text)` | text | `text` | Текстовое сообщение |
| `image(file)` | image | `file` | Сообщение с изображением |
| `audio(file)` | audio | `file` | Аудиосообщение |
| `video(file)` | video | `file` | Видеосообщение |
| `file(file, filename?)` | file | `file`, `filename` | Сообщение с файлом |
| `mention(user_id, user_name?)` | mention | `user_id`, `user_name` | Упоминание пользователя |
| `at(user_id, user_name?)` | mention | `user_id`, `user_name` | Алиас для `mention` |
| `reply(message_id)` | reply | `message_id` | Ответ на сообщение |
| `at_all()` | mention_all | - | Упоминание всех участников |
| `custom(type, data)` | пользовательский | пользовательский | Пользовательский тип сообщения |

## Использование в связке с Send

Построенный список сообщений отправляется через `Send.Raw_ob12()`:

```python
from ErisPulse import sdk
from ErisPulse.Core.Event.message_builder import MessageBuilder

# Построение сообщений в цепочке и отправка
segments = (
    MessageBuilder()
    .mention("user123", "张三")
    .text(" Пожалуйста, посмотрите на это изображение")
    .image("https://example.com/photo.jpg")
    .build()
)
await sdk.adapter.myplatform.Send.To("group", "group456").Raw_ob12(segments)
```

### Использование в ответ на событие

```python
from ErisPulse.Core.Event import command

@command("report")
async def report_handler(event):
    await event.reply_ob12(
        MessageBuilder()
        .text("📊 Сводка ежедневного отчета\n")
        .text("Выполненные задачи сегодня: 5\n")
        .text("Задачи в процессе: 3")
        .build()
    )
```

## Вспомогательные методы

### copy()

Копирует текущий билдер, что позволяет создавать несколько вариантов сообщений на основе одного и того же содержания:

```python
base = MessageBuilder().text("Базовое содержание").mention("admin")

# Создание различных сообщений на основе одного и того же префикса
msg1 = base.copy().text(" Вариант A").build()
msg2 = base.copy().text(" Вариант B").image("img.jpg").build()
```

### clear()

Очищает добавленные сообщения, что позволяет повторно использовать один и тот же билдер:

```python
builder = MessageBuilder()

for user_id in ["user1", "user2", "user3"]:
    builder.clear()
    msg = builder.mention(user_id).text(" Привет!").build()
    await adapter.Send.To("user", user_id).Raw_ob12(msg)
```

### len() / bool()

```python
builder = MessageBuilder()
print(bool(builder))   # False

builder.text("Hello")
print(len(builder))    # 1
print(bool(builder))   # True
```

## Пользовательские сообщения

Метод `custom()` используется для добавления расширенных сообщений, специфичных для платформы:

```python
# Добавление специфичного для платформы сообщения
segments = (
    MessageBuilder()
    .text("Пожалуйста, заполните форму:")
    .custom("yunhu_form", {"form_id": "12345"})
    .build()
)
```

> Пользовательские сообщения действительны только в адаптерах соответствующей платформы, другие адаптеры игнорируют неизвестные типы сообщений.

## Полный пример

### Сообщение с несколькими элементами

```python
segments = (
    MessageBuilder()
    .reply(event.get_id())                    # Ответ на исходное сообщение
    .mention(event.get_user_id())             # Упоминание отправителя
    .text(" Это результат вашего запроса:\n")             # Текстовое сообщение
    .image("https://example.com/chart.png")   # Изображение
    .text("\nПодробные данные см. в приложении:")
    .file("https://example.com/data.csv", filename="data.csv")
    .build()
)
await event.reply_ob12(segments)
```

### Смешанное использование статического фабрика и цепочки вызовов

```python
# Быстрое построение простого сообщения
simple_msg = MessageBuilder.text("Простой текст")

# Цепочечное построение сложного сообщения
complex_msg = (
    MessageBuilder()
    .at_all()
    .text(" 📢 Объявление:")
    .text("Сегодня в 15:00 состоится собрание")
    .build()
)
```

## Связанные документы

- [Подробное руководство по SendDSL адаптера](../developer-guide/adapters/send-dsl.md) - интерфейс Send для цепочечной отправки
- [Стандарт преобразования событий](../standards/event-conversion.md) - стандарт преобразования сообщений
- [Обертка Event](../developer-guide/modules/event-wrapper.md) - метод Event.reply_ob12()