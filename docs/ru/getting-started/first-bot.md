# Создание первого бота

Это руководство проведет вас от нуля к созданию простого бота ErisPulse.

## Шаг 1: Создание проекта

Используйте инструмент CLI для инициализации проекта:

```bash
# Интерактивная инициализация
epsdk init

# Или быстрая инициализация
epsdk init -q -n my_first_bot
```

Следуйте подсказкам для завершения настройки. Рекомендуется выбрать:
- Имя проекта: my_first_bot
- Уровень логов: INFO
- Сервер: конфигурация по умолчанию
- Адаптер: выберите нужную платформу (например, Yunhu)

## Шаг 2: Просмотр структуры проекта

Структура проекта после инициализации:

```
my_first_bot/
├── config/
│   └── config.toml
├── main.py
└── requirements.txt
```

## Шаг 3: Написание первой команды

Откройте `main.py` и напишите простого обработчика команд:

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="发送问候消息")
async def hello_handler(event):
    """处理 hello 命令"""
    user_name = event.get_user_nickname() or "друг"
    await event.reply(f"Привет, {user_name}! Я бот ErisPulse.")

@command("ping", help="Тестирование доступности бота")
async def ping_handler(event):
    """Обработка команды ping"""
    await event.reply("Pong! Бот работает нормально.")

async def main():
    """Главная функция входа"""
    print("Инициализация ErisPulse...")
    # Запуск SDK и удержание запущенным
    await sdk.run(keep_running=True)

    # Или
    # await sdk.run(keep_running=False)
    # ...Сделайте что-нибудь
    # Можно делать все, что угодно
    # Использование await sdk.init() эквивалентно `sdk.run(keep_running=False)`

    print("ErisPulse инициализирован успешно!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Шаг 4: Запуск бота

```bash
# Обычный запуск
epsdk run main.py

# Режим разработчика (поддержка горячего перезагрузки)
epsdk run main.py --reload
```

## Шаг 5: Тестирование бота

Отправьте команду в вашем мессенджере:

```
/hello
```

Вы должны получить ответ от бота.

## Пояснение кода

### Декоратор команды

```python
@command("hello", help="发送问候消息")
```

- `hello` : имя команды, пользователь вызывает через `/hello`
- `help` : справка по команде, отображается в команде `/help`

### Параметры события

```python
async def hello_handler(event):
```

Параметр `event` — это объект Event, содержащий:
- Содержимое сообщения
- Информацию об отправителе
- Информацию о платформе
- И так далее...

### Отправка ответа

```python
await event.reply("回复内容")
```

Метод `event.reply()` — это удобный способ отправить сообщение отправителю.

## Расширение: добавление дополнительных функций

### Добавление прослушивания сообщений

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    """Прослушивание всех сообщений"""
    text = event.get_text()
    if "привет" in text:
        await event.reply("Привет!")
```

### Добавление прослушивания уведомлений

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    """Прослушивание события добавления друга"""
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать в друзья! Ваш ID: {user_id}")
```

### Использование системы хранения

```python
# Получение счетчика
count = sdk.storage.get("hello_count", 0)

# Увеличение счетчика
count += 1
sdk.storage.set("hello_count", count)

await event.reply(f"Это {count}-й вызов команды hello")
```

## Часто задаваемые вопросы

### Бот не отвечает на команду?

1. Проверьте, правильно ли настроен адаптер.
2. Просмотрите логи вывода, чтобы убедиться в отсутствии ошибок.
3. Убедитесь, что префикс команды верен (по умолчанию это `/`).

### Как изменить префикс команды?

Добавьте в `config.toml`:

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### Как поддерживать несколько платформ?

Код автоматически адаптируется ко всем загруженным платформенным адаптерам. Убедитесь лишь в совместимости вашей логики:

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Привет! От Yunhu")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
```

## Далее

- [Основные понятия](basic-concepts.md) — глубокое понимание концепций ErisPulse
- [Основные понятия](basic-concepts.md) — глубокое понимание концепций ErisPulse
- [Основы обработки событий](event-handling.md) — изучение обработки различных событий
- [Примеры распространенных задач](common-tasks.md) — освоение дополнительных полезных функций