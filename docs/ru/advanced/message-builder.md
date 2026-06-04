# Подробное описание MessageBuilder

`MessageBuilder` — это инструмент для построения сегментов сообщений по стандарту OneBot12, предоставляемый ErisPulse, предназначенный для создания структурированного контента сообщений, используется в сочетании с `Send.Raw_ob12()`.

## Двойной механизм режимов

MessageBuilder предлагает два режима использования, реализующие разное поведение на уровне класса и на уровне экземпляра через механизм Python descriptors:

### Режим цепочки вызовов (экземпляр)

Используйте путем создания экземпляра `MessageBuilder()`. Каждый метод возвращает `self`, поддерживая цепные вызовы; в конце вызовите `.build()` для получения списка сегментов сообщения:

```python
from ErisPulse.Core.Event.message_builder import MessageBuilder

segments = (
    MessageBuilder()
    .text("你好！")
    .image("https://example.com/photo.jpg")
    .build()
)
# [
#     {"type": "text", "data": {"text": "你好！"}},
#     {"type": "image", "data": {"file": "https://example.com/photo.jpg"}}
# ]
```

### Режим быстрого построения (статический)

Вызывайте методы напрямую через класс. Каждый метод сразу возвращает список сегментов сообщения, подходит для одиночных сообщений:

```python
# Возвращает list[dict] напрямую, без .build()
segments = MessageBuilder.text("你好！")
# [{"type": "text", "data": {"text": "你好！"}}]
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
    .mention("user123", "张三")
    .text(" 请查看这张图片")
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
        .text("📊 日报汇总\n")
        .text("今日完成任务: 5\n")
        .text("进行中任务: 3")
        .build()
    )
```

## Утилиты

### copy()

Копирует текущий билдер, используется для создания множества вариантов сообщений на основе одного базового содержимого:

```python
base = MessageBuilder().text("基础内容").mention("admin")

# Создание различных сообщений на основе одного префикса
msg1 = base.copy().text(" 变体A").build()
msg2 = base.copy().text(" 变体B").image("img.jpg").build()
```

### clear()

Очищает добавленные сегменты сообщения, переиспользуя тот же билдер:

```python
builder = MessageBuilder()

for user_id in ["user1", "user2", "user3"]:
    builder.clear()
    msg = builder.mention(user_id).text(" 你好！").build()
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
    .text("请填写表单：")
    .custom("yunhu_form", {"form_id": "12345"})
    .build()
)
```

> Пользовательские сегменты сообщений действительны только в адаптерах соответствующих платформ, другие адапторы проигнорируют непонятные сегменты.

## Полный пример

### Сообщение с несколькими элементами

```python
segments = (
    MessageBuilder()
    .reply(event.get_id())                    # Ответ на исходное сообщение
    .mention(event.get_user_id())             # Упоминание отправителя
    .text(" 这是你的查询结果：\n")             # Текст
    .image("https://example.com/chart.png")   # Изображение
    .text("\n详细数据见附件：")
    .file("https://example.com/data.csv", filename="data.csv")
    .build()
)
await event.reply_ob12(segments)
```

### Смешанное использование: статический + цепной

```python
# Быстрое создание сообщения из одного сегмента
simple_msg = MessageBuilder.text("简单文本")

# Построение сложного сообщения цепочкой
complex_msg = (
    MessageBuilder()
    .at_all()
    .text(" 📢 公告：")
    .text("今天下午3点开会")
    .build()
)
```

## Связанные документы

- [Подробное описание SendDSL адаптера](../developer-guide/adapters/send-dsl.md) - Интерфейс цепочечной отправки Send
- [Стандарты конвертации событий](../standards/event-conversion.md) - Спецификация преобразования сегментов сообщений
- [Классы обертки событий](../developer-guide/modules/event-wrapper.md) - Метод event.reply_ob12()