# Многопроходный диалог (Conversation)

Класс `Conversation` предоставляет удобные методы для многоходовых взаимодействий в рамках одного сеанса, подходящие для реализации операций по шагам (guided operations), сбора информации, диалоговых вопросов-ответов и других сценариев.

## Создание диалога

Создается через метод `conversation()` объекта `Event`:

```python
from ErisPulse.Core.Event import command

@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)

    await conv.say("🎮 Добро пожаловать на викторину по знаниям!")

    answer = await conv.choose("Первый вопрос: Кто создатель Python?", [
        "Guido van Rossum",
        "James Gosling",
        "Dennis Ritchie",
    ])

    if answer is None:
        await conv.say("Истекло время, попробуйте снова!")
        return

    if answer == 0:
        await conv.say("Верно!")
    else:
        await conv.say("Неверно, верный ответ: Guido van Rossum")

    conv.stop()
```

## Основной API

### say(content, **kwargs)

Отправляет сообщение, возвращает `self` для поддержки цепных вызовов:

```python
await conv.say("Первая строка").say("Вторая строка").say("Третья строка")
```

Также можно указать метод отправки:

```python
await conv.say("https://example.com/image.jpg", method="Image")
```

### wait(prompt=None, timeout=None)

Ожидает ответ пользователя, возвращает объект `Event` или `None` (если истек таймаут):

```python
# Простое ожидание
resp = await conv.wait()
if resp:
    text = resp.get_text()

# Ожидание после отправки сообщения
resp = await conv.wait(prompt="Пожалуйста, введите ваше имя:")

# Использование пользовательского таймаута (переопределяет таймаут по умолчанию для диалога)
resp = await conv.wait(prompt="Пожалуйста, ответьте в течение 10 секунд:", timeout=10)
```

### confirm(prompt=None, **kwargs)

Ожидает подтверждения пользователя (да/нет), возвращает `True` / `False` / `None` (если таймаут):

```python
result = await conv.confirm("Вы уверены, что хотите удалить все данные?")
if result is True:
    await conv.say("Удалено")
elif result is False:
    await conv.say("Отмена")
else:
    await conv.say("Тайм-аут, ответ не получен")
```

Встроенные распознаваемые слова подтверждения: `Да/yes/y/подтверждено/ок/хорошо/true/правда/угу/согласен/без проблем/можно/конечно...`

Встроенные распознаваемые слова отрицания: `Нет/no/n/отмена/нет/не надо/нельзя/cancel/false/неправильно/неверно/не/отказ...`

### choose(prompt, options, **kwargs)

Ожидает выбора пользователя из опций, возвращает индекс опции (0-based) или `None`:

```python
choice = await conv.choose("Выберите цвет:", ["Красный", "Зеленый", "Синий"])
if choice is not None:
    colors = ["Красный", "Зеленый", "Синий"]
    await conv.say(f"Вы выбрали {colors[choice]}")
```

Пользователь может выбрать, введя номер (например, `1`/`2`/`3`) или текст опции (например, "Красный").

### collect(fields, **kwargs)

Многошаговый сбор информации, возвращает словарь с данными или `None`:

```python
data = await conv.collect([
    {"key": "name", "prompt": "Пожалуйста, введите имя"},
    {"key": "age", "prompt": "Пожалуйста, введите возраст",
     "validator": lambda e: e.get("alt_message", "").strip().isdigit(),
     "retry_prompt": "Возраст должен быть числом, попробуйте снова"},
    {"key": "city", "prompt": "Пожалуйста, введите город"},
])

if data:
    await conv.say(f"Регистрация успешна!\nИмя: {data['name']}\nВозраст: {data['age']}\nГород: {data['city']}")
else:
    await conv.say("Процесс сбора информации прерван")
```

Конфигурация полей:

| Параметр | Описание | Значение по умолчанию |
|------|------|--------|
| `key` | Ключ поля (обязательно) | - |
| `prompt` | Текст приглашения | `"Пожалуйста, введите {key}"` |
| `validator` | Функция валидации, принимает Event, возвращает bool | Нет |
| `retry_prompt` | Текст сообщения при неудаче повторного ввода | `"Некорректный ввод, попробуйте снова"` |
| `max_retries` | Максимальное количество попыток | 3 |
| `condition` | Условная функция, принимает собранный словарь данных, возвращает bool | Нет |

**Условные поля** (condition fields): Использование `condition` позволяет реализовать динамические формы, где поле собирается только при выполнении условия:

```python
data = await conv.collect([
    {"key": "has_car", "prompt": "У вас есть автомобиль? (да/нет)"},
    {"key": "car_brand", "prompt": "Пожалуйста, введите марку",
     "condition": lambda d: d.get("has_car", "").lower() in ("да", "yes", "y")},
])
```

### stop()

Ручное завершение диалога, устанавливает `is_active` в `False`:

```python
conv.stop()
```

### is_active

Свойство, указывающее, находится ли диалог в активном состоянии:

```python
if conv.is_active:
    await conv.say("Диалог всё еще идет")
```

## Управление активным состоянием

Диалог автоматически переходит в неактивное состояние в следующих случаях:

1. Вызов метода `stop()`
2. Метод `wait()` возвращает `None` (истек таймаут)
3. Метод `collect()` возвращает `None` из-за таймаута или исчерпания попыток повторного ввода

После перехода в неактивное состояние все методы взаимодействия (например, `wait`/`confirm`/`choose`/`collect`) будут возвращать `None` без ожидания ввода пользователя.

## Ветвление и переходы

### Декоратор `@conv.branch(name)`

Использует `branch()` для регистрации веток диалога, переходы между ветками осуществляются через `goto()`:

```python
@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)

    @conv.branch("main")
    async def main_menu():
        await conv.say("=== Главное меню ===\n1. Личная информация\n2. Настройки\n3. Выход")
        resp = await conv.wait()
        if resp is None:
            return
        text = resp.get_text().strip()
        if text == "1":
            await conv.goto("profile")
        elif text == "2":
            await conv.goto("settings")
        elif text == "3":
            await conv.say("До свидания!")
            conv.stop()

    @conv.branch("profile")
    async def profile():
        await conv.say("=== Личная информация ===\nИмя: Alice\n0. Вернуться")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    @conv.branch("settings")
    async def settings():
        await conv.say("=== Настройки ===\n1. Переключатель уведомлений\n0. Вернуться")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    await conv.start()  # Начинается с первого зарегистрированного ветки
```

### conv.start(name=None)

Запускает диалог, по умолчанию начиная с первой зарегистрированной ветки:

```python
await conv.start()          # Начать с первой ветки
await conv.start("settings") # Начать с указанной ветки
```

## Контекст и персистентность

### conv.context

Каждый экземпляр диалога имеет встроенный словарь `context` для общего состояния между ветками:

```python
@conv.branch("step1")
async def step1():
    conv.context["username"] = resp.get_text().strip()
    await conv.goto("step2")

@conv.branch("step2")
async def step2():
    name = conv.context.get("username", "Неизвестно")
    await conv.say(f"Привет, {name}!")
```

### save() / resume() / clear_saved()

Диалог поддерживает персистентность (сохранение состояния), которое можно восстановить после тайм-аута или прерывания:

```python
# Сохранение состояния диалога
conv_id = conv.save()
# conv_id = "user_123_group_456"  # Автоматически генерируется на основе пользователя и группы

# ... затем восстановить в том же сеансе ...
conv2 = event.conversation()
if conv2.resume():
    await conv2.say("Добро пожаловать обратно! Продолжим предыдущий диалог")
else:
    await conv2.say("Предыдущий диалог не найден")

# Очистка сохраненного диалога
conv.clear_saved()
```

## Типовые паттерны потоков

### Регистрация по шагам (Guided Registration)

```python
@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)

    await conv.say("Добро пожаловать к регистрации!")

    data = await conv.collect([
        {"key": "username", "prompt": "Пожалуйста, введите имя пользователя (3-20 символов)",
         "validator": lambda e: 3 <= len(e.get_text().strip()) <= 20},
        {"key": "email", "prompt": "Пожалуйста, введите адрес электронной почты",
         "validator": lambda e: "@" in e.get_text() and "." in e.get_text(),
         "retry_prompt": "Неверный формат электронной почты, попробуйте снова"},
    ])

    if not data:
        await event.reply("Регистрация отменена")
        return

    confirmed = await conv.confirm(
        f"Подтвердить регистрационные данные?\nИмя пользователя: {data['username']}\nEmail: {data['email']}"
    )

    if confirmed:
        await conv.say("✅ Регистрация успешна!")
    else:
        await conv.say("❌ Регистрация отменена")
```

### Циклический диалог

```python
@command("chat")
async def chat_handler(event):
    conv = event.conversation(timeout=120)
    await conv.say("Режим диалога активирован, введите «выход» для завершения")

    while conv.is_active:
        resp = await conv.wait()
        if resp is None:
            await conv.say("Тайм-аут, диалог завершен")
            break

        text = resp.get_text().strip()

        if text == "выход":
            await conv.say("До свидания!")
            conv.stop()
        elif text == "помощь":
            await conv.say("Доступные команды: выход, помощь, статус")
        elif text == "статус":
            await conv.say("Диалог активен")
        else:
            await conv.say(f"Вы сказали: {text}")
```

## Связанные документы

- [Класс-обертка Event](../developer-guide/modules/event-wrapper.md) - Все методы объекта Event
- [Основы обработки событий](../getting-started/event-handling.md) - Основы обработки событий