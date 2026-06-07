# Подробное описание MessageBuilder

`MessageBuilder` — это инструмент для построения сегментов сообщений по стандарту OneBot12, предоставляемый ErisPulse, предназначенный для создания структурированного контента сообщений, используется в сочетании с `Send.Raw_ob12()`.

## Импорт

`MessageBuilder` поддерживает два способа импорта (результат одинаковый, рекомендуется первый):

```python
from ErisPulse.Core.Event import MessageBuilder        # Рекомендуется, через пакет
from ErisPulse.Core.Event.message_builder import MessageBuilder  # Прямой импорт модуля
```

## Двойной механизм

MessageBuilder предоставляет два режима использования, реализуемые через механизм Python descriptors (`__get__`): при вызове метода через класс `__get__` возвращает результат выполнения статического метода; при вызове через экземпляр возвращает `self` для поддержки цепных вызовов.

### Режим цепочки вызовов (экземпляр)

Используйте путем создания экземпляра `MessageBuilder()`. Каждый метод возвращает `self`, поддерживая цепные вызовы; в конце вызовите `.build()` для получения списка сегментов сообщения:

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

Вызывайте методы напрямую через класс. Каждый метод сразу возвращает список сегментов сообщения, подходит для одиночных сообщений:

```python
# Возвращает list[dict] напрямую, без .build()
segments = MessageBuilder.text("Привет!")
# [{"type": "text", "data": {"text": "Привет!"}}]
```

## Типы сегментов сообщений

| Метод | Тип | Параметры данных | Описание |
|------|------|---------|------|
| `text(text)` | text | `text` | Текстовое сообщение |
| `image(file)` | image | `file` | Изображение |
| `audio(file)` | audio | `file` | Аудио |
| `video(file)` | video | `file` | Видео |
| `file(file, filename?)` | file | `file`, `filename` | Файл |
| `mention(user_id, user_name?)` | mention | `user_id`, `user_name` | Упоминание пользователя (@) |
| `at(user_id, user_name?)` | mention | `user_id`, `user_name` | Псевдоним для `mention` |
| `reply(message_id)` | reply | `message_id` | Ответ на сообщение |
| `at_all()` | mention_all | - | Упомянуть всех |
| `custom(type, data)` | 自定义 | 自定义 | Пользовательский сегмент сообщения |

## Использование с Send

Списки сегментов сообщений собираются с помощью `Send.Raw_ob12()`:

```python
from ErisPulse import sdk
from ErisPulse.Core.Event.message_builder import MessageBuilder

# Построение + отправка (цепочкой)
segments = (
    MessageBuilder()
    .mention("user123", "Чжан Сань")
    .text(" Пожалуйста, посмотрите на эту картинку")
    .image("https://example.com/photo.jpg")
    .build()
)
await sdk.adapter.myplatform.Send.To("group", "group456").Raw_ob12(segments)
```

### Ответ на событие

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

## Утилиты

### copy()

Копирует текущий билдер, используется для создания множества вариантов сообщений на основе одного базового содержимого:

```python
base = MessageBuilder().text("Базовое содержание").mention("admin")

# Создание различных сообщений на основе одного префикса
msg1 = base.copy().text(" Вариант A").build()
msg2 = base.copy().text(" Вариант B").image("img.jpg").build()
```

### clear()

Очищает добавленные сегменты сообщения, переиспользуя тот же билдер:

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

## Пользовательские сегменты сообщений

Используйте метод `custom()` для добавления сегментов сообщений с расширениями платформы:

```python
# Добавление специфичных для платформы сегментов сообщений
segments = (
    MessageBuilder()
    .text("Пожалуйста, заполните форму：")
    .custom("yunhu_form", {"form_id": "12345"})
    .build()
)
```

> Пользовательские сегменты сообщений действительны только в адаптерах соответствующих платформ, другие адаптеры проигнорируют непонятные сегменты.

## Полный пример

### Сообщение с несколькими элементами

```python
segments = (
    MessageBuilder()
    .reply(event.get_id())                    # Ответ на исходное сообщение
    .mention(event.get_user_id())             # Упоминание отправителя
    .text(" Это результат вашего запроса：\n")             # Текст
    .image("https://example.com/chart.png")   # Изображение
    .text("\nПодробные данные см. в приложении：")
    .file("https://example.com/data.csv", filename="data.csv")
    .build()
)
await event.reply_ob12(segments)
```

### Смешанное использование: статический + цепной

```python
# Быстрое создание сообщения из одного сегмента
simple_msg = MessageBuilder.text("Простой текст")

# Построение сложного сообщения цепочкой
complex_msg = (
    MessageBuilder()
    .at_all()
    .text(" 📢 Объявление：")
    .text("Сегодня в 15:00 состоится собрание")
    .build()
)
```

## Связанные документы

- [Подробное описание SendDSL адаптера](../developer-guide/adapters/send-dsl.md) - Интерфейс цепочечной отправки Send
- [Стандарты конвертации событий](../standards/event-conversion.md) - Спецификация преобразования сегментов сообщений
- [Классы обертки событий](../developer-guide/modules/event-wrapper.md) - Метод event.reply_ob12()