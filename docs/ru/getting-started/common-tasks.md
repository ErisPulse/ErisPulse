# Примеры распространённых задач

Этот гайд предоставляет примеры реализации распространённых функций, чтобы помочь вам быстро достичь типичных задач.

## Содержание

1. Персистентность данных
2. Плановые задачи
3. Фильтрация сообщений
4. Адаптация для нескольких платформ
5. Управление правами доступа
6. Статистика сообщений
7. Функция поиска
8. Обработка изображений

## Персистентность данных

### Простой счётчик

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="Просмотреть количество вызовов команды")
async def count_handler(event):
    # Получить счётчик
    count = sdk.storage.get("command_count", 0)
    
    # Увеличить счётчик
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"Это {count}-й вызов этой команды")
```

### Хранение данных пользователя

```python
@command("profile", help="Просмотреть профиль")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # Получить данные пользователя
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
Никнейм: {user_data['nickname']}
Дата присоединения: {user_data['join_date']}
Количество сообщений: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="Установить никнейм")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("Пожалуйста, введите никнейм")
        return
    
    # Обновить данные пользователя
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"Никнейм установлен на: {' '.join(args)}")
```

## Плановые задачи

### Простой таймер

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
import asyncio

class TimerModule:
    def __init__(self):
        self.sdk = sdk
        self._tasks = []
    
    async def on_load(self, event):
        """Запуск запланированных задач при загрузке модуля"""
        self._start_timers()
        
        @command("timer", help="Управление таймером")
        async def timer_handler(event):
            await event.reply("Таймер работает...")
    
    def _start_timers(self):
        """Запуск запланированных задач"""
        # Выполнять каждые 60 секунд
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # Выполнять в полночь
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """Задача, выполняемая каждую минуту"""
        self.sdk.logger.info("Задача выполняется каждую минуту")
        # Ваша логика...
    
    async def _daily_task(self):
        """Задача, выполняемая в полночь"""
        import time
        
        while True:
            # Вычисление времени до полуночи
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # Выполнение задачи
            self.sdk.logger.info("Ежедневная задача выполняется")
            # Ваша логика...
```

### Использование событий жизненного цикла

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """Запуск запланированных задач после завершения инициализации SDK"""
    import asyncio
    
    async def daily_reminder():
        """Ежедневное напоминание"""
        await asyncio.sleep(86400)  # 24 часа
        self.sdk.logger.info("Выполнение ежедневной задачи")
    
    # Запуск фоновых задач
    asyncio.create_task(daily_reminder())
```

## Фильтрация сообщений

### Фильтрация по ключевым словам

```python
from ErisPulse.Core.Event import message

blocked_words = ["мусор", "реклама", "фишинг"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # Проверка на наличие чувствительных слов
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"Заблокировано чувствительное сообщение: {word}")
            return  # Не обрабатывать это сообщение
    
    # Обработка сообщения в обычном режиме
    await event.reply(f"Получено: {text}")
```

### Фильтрация по черному списку

```python
# Загрузка черного списка из конфигурации или хранилища
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"Пользователь в черном списке: {user_id}")
        return  # Не обрабатывать
    
    # Обработка в обычном режиме
    await event.reply(f"Привет, {user_id}")
```

## Адаптация для нескольких платформ

### Ответы, специфичные для платформы

```python
@command("help", help="Показать справку")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Справка по платформе YUNHU...")
    elif platform == "telegram":
        await event.reply("Справка по платформе Telegram...")
    elif platform == "onebot11":
        await event.reply("Справка OneBot11...")
    else:
        await event.reply("Общая справочная информация")
```

### Определение возможностей платформы

```python
@command("rich", help="Отправить форматированное сообщение")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # YUNHU поддерживает HTML
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>Жирный текст</b><i>Курсивный текст</i>"
        )
    elif platform == "telegram":
        # Telegram поддерживает Markdown
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**Жирный текст** *Курсивный текст*"
        )
    else:
        # Для других платформ используется обычный текст
        await event.reply("Жирный текст Курсивный текст")
```

## Управление правами доступа

### Проверка администратора

```python
# Настройка списка администраторов
ADMINS = ["user123", "user456"]

def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMINS

@command("admin", help="Команда администратора")
async def admin_handler(event):
    user_id = event.get_user_id()
    
    if not is_admin(user_id):
        await event.reply("Недостаточно прав, эта команда доступна только администраторам")
        return
    
    await event.reply("Команда администратора выполнена успешно")

@command("addadmin", help="Добавить администратора")
async def addadmin_handler(event):
    if not is_admin(event.get_user_id()):
        return
    
    args = event.get_command_args()
    if not args:
        await event.reply("Введите ID администратора, которого нужно добавить")
        return
    
    new_admin = args[0]
    ADMINS.append(new_admin)
    await event.reply(f"Администратор добавлен: {new_admin}")
```

### Права групп

```python
@command("groupinfo", help="Просмотреть информацию о группе")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("Эта команда доступна только в групповых чатах")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"ID группы: {group_id}, ваш ID: {user_id}")
```

## Статистика сообщений

### Подсчет сообщений

```python
@message.on_message()
async def count_handler(event):
    # Получить статистику
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # Обновить статистику
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # Сохранить
    sdk.storage.set("message_stats", stats)

@command("stats", help="Просмотреть статистику сообщений")
async def stats_handler(event):
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    top_users = sorted(
        stats["by_user"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    top_text = "\n".join(
        f"{uid}: {count} сообщений" for uid, count in top_users
    )
    
    await event.reply(f"Общее количество сообщений: {stats['total']}\n\nАктивные пользователи:\n{top_text}")
```

## Функция поиска

### Простой поиск

```python
from ErisPulse.Core.Event import command, message

# Хранение истории сообщений
message_history = []

@message.on_message()
async def store_handler(event):
    """Сохранить сообщения для поиска"""
    user_id = event.get_user_id()
    text = event.get_text()
    
    message_history.append({
        "user_id": user_id,
        "text": text,
        "time": event.get_time()
    })
    
    # Ограничить количество записей истории
    if len(message_history) > 1000:
        message_history.pop(0)

@command("search", help="Поиск сообщений")
async def search_handler(event):
    args = event.get_command_args()
    
    if not args:
        await event.reply("Пожалуйста, введите ключевое слово для поиска")
        return
    
    keyword = " ".join(args)
    results = []
    
    # Поиск в истории сообщений
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("Совпадающие сообщения не найдены")
        return
    
    # Отображение результатов
    result_text = f"Найдено {len(results)} сообщений, соответствующих запросу:\n\n"
    for i, msg in enumerate(results[:10], 1):  # Отображать не более 10
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## Обработка изображений

### Скачивание и хранение изображений

```python
from ErisPulse.Core import client

@message.on_message()
async def image_handler(event):
    """Обработка сообщений с изображениями"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # Рекомендуется использовать встроенный клиент SDK для загрузки изображений
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # Сохранить в файл
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"Изображение сохранено: {filename}")
                    await event.reply("Изображение сохранено")
```

### Пример распознавания изображений

```python
from ErisPulse.Core import client

@command("identify", help="Распознать изображение")
async def identify_handler(event):
    """Распознать изображение в сообщении"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # Вызов API распознавания изображений
            result = await _identify_image(file_url)
            
            await event.reply(f"Результат распознавания: {result}")
            return
    
    await event.reply("Изображение не найдено")

async def _identify_image(url):
    """Вызов API распознавания изображений (пример) - использование встроенного клиента SDK"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "Распознавание не удалось")
```

## Далее

- [Руководство для пользователей](../user-guide/) - Узнайте о конфигурации и управлении модулями
- [Руководство для разработчиков](../developer-guide/) - Изучите разработку модулей и адаптеров
- [Расширенные темы](../advanced/) - Глубокое понимание возможностей фреймворка