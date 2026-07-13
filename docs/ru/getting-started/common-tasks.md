# Примеры распространённых задач

Это руководство предоставляет примеры реализации распространённых функций, которые помогут вам быстро внедрить нужные возможности.

## Содержание

1. Сохранение данных
2. Запланированные задачи
3. Фильтрация сообщений
4. Адаптация для нескольких платформ
5. Отправка сообщений (повтор/тайм-аут/массовая)
6. Контроль доступа
7. Статистика сообщений
8. Поиск
9. Обработка изображений

## Сохранение данных

### Простые счётчики

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="Показывает количество вызовов команды")
async def count_handler(event):
    # Получаем счётчик
    count = sdk.storage.get("command_count", 0)
    
    # Увеличиваем счётчик
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"Это {count}-й вызов этой команды")
```

### Хранение данных пользователя

```python
@command("profile", help="Показывает профиль пользователя")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # Получаем данные пользователя
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
Никнейм: {user_data['nickname']}
Дата регистрации: {user_data['join_date']}
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
    
    # Обновляем данные пользователя
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"Никнейм установлен на: {' '.join(args)}")
```

## Запланированные задачи

### Простые таймеры

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
        
        @command("timer", help="Управление таймерами")
        async def timer_handler(event):
            await event.reply("Таймеры работают...")
    
    def _start_timers(self):
        """Запуск запланированных задач"""
        # Выполнять раз в 60 секунд
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # Выполнять в полночь
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """Задача, выполняемая каждую минуту"""
        self.sdk.logger.info("Выполнение ежеминутной задачи")
        # Ваша логика...
    
    async def _daily_task(self):
        """Задача, выполняемая в полночь (Примечание: рассчитывается по UTC, для локального времени нужно настроить)"""
        import time
        
        while True:
            # Вычисляем время до полуночи
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # Выполняем задачу
            self.sdk.logger.info("Выполнение ежедневной задачи")
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
        sdk.logger.info("Выполнение ежедневной задачи")
    
    # Запуск фоновых задач
    asyncio.create_task(daily_reminder())
```

## Фильтрация сообщений

### Фильтр по ключевым словам

```python
from ErisPulse.Core.Event import message

blocked_words = ["мусор", "реклама", "фишинг"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # Проверяем наличие чувствительных слов
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"Блокировка чувствительного сообщения: {word}")
            return  # Не обрабатываем это сообщение
    
    # Обрабатываем сообщение нормально
    await event.reply(f"Получено: {text}")
```

### Фильтр чёрного списка

```python
# Загружаем чёрный список из конфигурации или хранилища
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"Пользователь в чёрном списке: {user_id}")
        return  # Не обрабатываем
    
    # Обрабатываем нормально
    await event.reply(f"Привет, {user_id}")
```

## Адаптация для нескольких платформ

### Платформо-специфичные ответы

```python
@command("help", help="Показывает справку")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Справка для платформы Yunhu...")
    elif platform == "telegram":
        await event.reply("Справка для Telegram...")
    elif platform == "onebot11":
        await event.reply("Справка для OneBot11...")
    else:
        await event.reply("Общая справочная информация")
```

### Обнаружение платформенных возможностей

```python
@command("rich", help="Отправляет сообщение с богатым форматированием")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # Yunhu поддерживает HTML
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
        # Для других платформ используем обычный текст
        await event.reply("Жирный текст Курсивный текст")
```

## Отправка сообщений (повтор/тайм-аут/массовая)

Помимо простого `event.reply()`, вы можете реализовать более сложные сценарии отправки через адаптер Send DSL: автоматический повтор при сбое, отмена по тайм-ауту, выполнение логики после успеха, массовая отправка нескольких сообщений.

> В приведённых ниже примерах используется `event.get_detail_type()` и `event.get_target_id()` для получения типа и ID назначения из события (для групповых чатов автоматически получается `group_id`, для личных — `user_id`), чтобы избежать жёсткого кодирования.

### Выполнение логики после успешной отправки

```python
@command("pay", help="Симуляция оплаты")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # Списываем баллы только после успешной отправки
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("Оплата прошла успешно, списано 10 баллов"))
```

### Повтор при ошибке + Отмена по тайм-ауту

```python
@command("notice", help="Отправка важного уведомления")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Максимальное количество попыток 3, тайм-аут 10 секунд
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"Не удалось отправить уведомление: {ctx.error}"))
            .Text("Это важное уведомление"))
    # Не ждём, отправляем в фоне
```

### Массовая отправка нескольких сообщений

Отправка нескольких сообщений одной цепочкой, выполнение единообразно:

```python
@command("announce", help="Отправка объявления")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Формируем несколько сообщений, отправляем единообразно (по умолчанию параллельно)
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 Сегодняшнее объявление")
                    .Image("https://example.com/banner.jpg")
                    .Text("Подробности см. на изображении выше")
                    .Retry(2)            # Каждая неудачная запись повторяется отдельно
                    .send_all())
    sdk.logger.info(f"Массовая отправка завершена, всего {len(results)} записей")
```

> Более подробные правила и инструкции по массовой отправке см. в [Руководстве по особенностям платформ](../platform-guide/README.md#правила отправки декораторов).

## Контроль доступа

### Проверка на администратора

```python
# Список владельцев
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """Проверка на владельца фреймворка"""
    return user_id in MASTERS

@command("master", help="Команда владельца фреймворка")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("Недостаточно прав, эта команда доступна только владельцу фреймворка")
        return
    
    await event.reply("Команда владельца успешно выполнена")

@command("addmaster", help="Добавить владельца фреймворка")
async def addmaster_handler(event):
    if not is_master(event.get_user_id()):
        return
    
    args = event.get("text", "").split()
    if len(args) < 2:
        await event.reply("Использование: /addmaster <ID пользователя>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"Добавлен владелец фреймворка: {new_master}")
```

### Права групп

```python
@command("groupinfo", help="Показать информацию о группе")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("Эта команда доступна только в групповых чатах")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"ID группы: {group_id}, Ваш ID: {user_id}")
```

## Статистика сообщений

### Подсчёт сообщений

> **Важно**: В приведённых ниже примерах используется `sdk.storage.get/set` для простого подсчёта. В сценариях с высокой concurrency рекомендуется использовать `sdk.storage.transaction()` для обеспечения атомарности.

```python
@message.on_message()
async def count_handler(event):
    # Получаем статистику
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # Обновляем статистику
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # Сохраняем
    sdk.storage.set("message_stats", stats)

@command("stats", help="Показать статистику сообщений")
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
    
    await event.reply(f"Всего сообщений: {stats['total']}\n\nАктивные пользователи:\n{top_text}")
```

## Поиск

### Простое создание базы данных для поиска

> **Важно**: В приведённых ниже примерах используется список в памяти для хранения истории сообщений, **данные будут потеряны после перезапуска программы**. Для продакшена рекомендуется использовать `sdk.storage` или таблицы SQLite для персистентного хранения.

```python
from ErisPulse.Core.Event import command, message

# Хранилище истории сообщений
message_history = []

@message.on_message()
async def store_handler(event):
    """Сохраняет сообщение для поиска"""
    user_id = event.get_user_id()
    text = event.get_text()
    
    message_history.append({
        "user_id": user_id,
        "text": text,
        "time": event.get_time()
    })
    
    # Ограничиваем количество записей
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
        await event.reply("Сообщения, соответствующие запросу, не найдены")
        return
    
    # Отображение результатов
    result_text = f"Найдено {len(results)} сообщений, соответствующих запросу:\n\n"
    for i, msg in enumerate(results[:10], 1):  # Максимум 10 записей
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## Обработка изображений

### Скачивание и сохранение изображений

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
                # Рекомендуется использовать встроенный клиент SDK для скачивания изображений
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # Сохранение в файл
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"Изображение сохранено: {filename}")
                    await event.reply("Изображение сохранено")
```

### Пример распознавания изображений

> **Важно**: В приведённых ниже примерах используется адрес API-заглушки. При реальном использовании замените его на адрес вашего сервиса распознавания изображений.

```python
from ErisPulse.Core import client

@command("identify", help="Распознать изображение")
async def identify_handler(event):
    """Распознавание изображений в сообщениях"""
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

## Дальнейшие шаги

- [Руководство для пользователей](../user-guide/) — Узнать о конфигурации и управлении модулями
- [Руководство для разработчиков](../developer-guide/) — Научиться разрабатывать модули и адаптеры
- [Расширенные темы](../advanced/) — Глубокое изучение особенностей фреймворка