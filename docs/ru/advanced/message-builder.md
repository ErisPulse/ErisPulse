# MessageBuilder — подробное руководство

`MessageBuilder` — это инструмент для построения сообщений стандарта OneBot12, предоставляемый ErisPulse. Он предназначен для построения структурированного содержимого сообщений и используется в сочетании с `Send.Raw_ob12()`.

## Способы импорта

`MessageBuilder` поддерживает два способа импорта (результат одинаковый, рекомендуется использовать первый):

```python
from ErisPulse.Core.Event import MessageBuilder        # Рекомендуется, через пакет
from ErisPulse.Core.Event.message_builder import MessageBuilder  # Прямой импорт модуля
```

## Двухрежимная система

MessageBuilder предоставляет два режима использования, реализованных с помощью механизма описателей Python (`__get__`), обеспечивающих различное поведение на уровне класса и экземпляра: при вызове метода через класс `__get__` возвращает результат выполнения статического метода; при вызове через экземпляр возвращает `self`, что поддерживает цепочечный вызов.

### Режим цепочечного вызова (экземпляр)

Используется путем создания экземпляра `MessageBuilder()`. Каждый метод возвращает `self`, что поддерживает цепочечный вызов, и в конце `.build()` используется для получения списка сообщений:

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

Методы вызываются напрямую через класс, каждый метод возвращает список сообщений напрямую, что подходит для одиночных сообщений:

```python
# Возвращает list[dict] напрямую, без необходимости использовать .build()
segments = MessageBuilder.text("Привет!")
# [{"type": "text", "data": {"text": "Привет!"}}]
```

## Типы сегментов сообщений

| Метод | Тип | Параметры данных | Описание |
|------|------|---------|------|
| `text(text)` | text | `text` | Текстовое сообщение |
| `image(file)` | image | `file` | Сообщение с изображением |
| `audio(file)` | audio | `file` | Аудиосообщение |
| `video(file)` | video | `file` | Видеосообщение |
| `file(file, filename?)` | file | `file`, `filename` | Сообщение с файлом |
| `mention(user_id, user_name?)` | mention | `user_id`, `user_name` | Упоминание пользователя |
| `at(user_id, user_name?)` | mention | `user_id`, `user_name` | Синоним `mention` |
| `reply(message_id)` | reply | `message_id` | Ответ на сообщение |
| `at_all()` | mention_all | - | Упоминание всех участников |
| `custom(type, data)` | пользовательский | пользовательский | Пользовательский сегмент сообщения |

## Использование с Send

Построенный список сообщений отправляется с помощью `Send.Raw_ob12()`:

```python
from ErisPulse import sdk
from ErisPulse.Core.Event.message_builder import MessageBuilder

# Построение и отправка сообщения с использованием цепочки вызовов
segments = (
    MessageBuilder()
    .mention("user123", "张三")
    .text(" Пожалуйста, посмотрите на это изображение")
    .image("https://example.com/photo.jpg")
    .build()
)
await sdk.adapter.myplatform.Send.To("group", "group456").Raw_ob12(segments)
```

### Использование с Event для ответа

```python
from ErisPulse.Core.Event import command

@command("report")
async def report_handler(event):
    await event.reply_ob12(
        MessageBuilder()
        .text("📊 Сводка ежедневного отчёта\n")
        .text("Задачи, выполненные сегодня: 5\n")
        .text("Задачи, находящиеся в процессе: 3")
        .build()
    )
```

## Утилитные методы

### copy()

Копирует текущий билдер, используется для создания нескольких вариантов сообщений на основе одного и того же базового содержания:

```python
base = MessageBuilder().text("Базовое содержание").mention("admin")

# Создание разных сообщений на основе одного и того же префикса
msg1 = base.copy().text(" Вариант A").build()
msg2 = base.copy().text(" Вариант B").image("img.jpg").build()
```

### clear()

Очищает добавленные части сообщения, позволяет повторно использовать один и тот же билдер:

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

Используйте метод `custom()`, чтобы добавить расширенный сегмент сообщения для конкретной платформы:

```python
# Добавление сегмента сообщения, специфичного для платформы
segments = (
    MessageBuilder()
    .text("Пожалуйста, заполните форму:")
    .custom("yunhu_form", {"form_id": "12345"})
    .build()
)
```

> Пользовательские сегменты сообщений действительны только в адаптерах соответствующих платформ, другие адаптеры игнорируют неизвестные сегменты сообщений.

## Полный пример

### Многоэлементное сообщение

```python
segments = (
    MessageBuilder()
    .reply(event.get_id())                    # Ответить на оригинальное сообщение
    .mention(event.get_user_id())             # Упомянуть отправителя
    .text(" Это результат вашего запроса:\n") # Текст
    .image("https://example.com/chart.png")   # Изображение
    .text("\nПодробные данные см. во вложении:")
    .file("https://example.com/data.csv", filename="data.csv")
    .build()
)
await event.reply_ob12(segments)
```

### Статический фабричный метод + цепочечная смесь

```python
# Быстрое создание односегментного сообщения
simple_msg = MessageBuilder.text("Простой текст")

# Цепочечное создание сложного сообщения
complex_msg = (
    MessageBuilder()
    .at_all()
    .text(" 📢 Объявление:")
    .text("Сегодня в 15:00 собрание")
    .build()
)
```

## Связанная документация

- [Подробное руководство по SendDSL адаптера](../developer-guide/adapters/send-dsl.md) - Цепочка интерфейсов отправки сообщений Send
- [Стандарт преобразования событий](../standards/event-conversion.md) - Стандарт преобразования сообщений
- [Обертка Event](../developer-guide/modules/event-wrapper.md) - Метод Event.reply_ob12()