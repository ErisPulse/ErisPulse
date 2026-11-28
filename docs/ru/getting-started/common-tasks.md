# Примеры распространённых задач

> [!TIP]
> **Когда это нужно прочитать:** Когда вы хотите добавить роботу какую-то конкретную функцию, читайте по разделам — сохранение данных, расписание задач, фильтрация сообщений, контроль доступа, массовая отправка. Каждый раздел — это готовый пример, который можно скопировать и сразу использовать. Если хотите систематически изучить обработку событий, сначала посмотрите [Введение в обработку событий](event-handling.md); если не нужно, пропустите этот раздел.

## Содержание

1. Сохранение данных
2. Расписание задач
3. Фильтрация сообщений
4. Адаптация к разным платформам
5. Расширенная отправка сообщений (повтор/таймаут/массовая)
6. Контроль доступа
7. Статистика сообщений
8. Функция поиска
9. Обработка изображений

## Сохранение данных

### Простой счётчик

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="Посмотреть количество вызовов команды")
async def count_handler(event):
    # Получить счётчик
    count = await sdk.storage.aget("command_count", 0)
    
    # Увеличить счётчик
    count += 1
    await sdk.storage.aset("command_count", count)
    
    await event.reply(f"Это {count}-й вызов данной команды")
```

### Хранение данных пользователя

```python
@command("profile", help="Посмотреть профиль")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # Получить данные пользователя
    user_data = await sdk.storage.aget(f"user:{user_id}", {
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
        await event.reply("Введите никнейм")
        return
    
    # Обновить данные пользователя
    user_data = await sdk.storage.aget(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    await sdk.storage.aset(f"user:{user_id}", user_data)
    
    await event.reply(f"Никнейм установлен как: {' '.join(args)}")
```

## Расписание задач

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
        """Запуск задач при загрузке модуля"""
        self._start_timers()
        
        @command("timer", help="Управление таймером")
        async def timer_handler(event):
            await event.reply("Таймер запущен...")
    
    def _start_timers(self):
        """Запуск задач по расписанию"""
        # Выполнять каждые 60 секунд
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # Выполнять каждый день в полночь
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """Задача, выполняемая каждую минуту"""
        self.sdk.logger.info("Выполнение задачи каждую минуту")
        # Ваша логика...
    
    async def _daily_task(self):
        """Задача, выполняемая каждый день в полночь (учтите, что используется UTC, если нужен локальный часовой пояс, настройте самостоятельно)"""
        import time
        
        while True:
            # Вычисление времени до полуночи
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # Выполнение задачи
            self.sdk.logger.info("Выполнение ежедневной задачи")
            # Ваша логика...
```

### Использование событий жизненного цикла

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """Запуск задач после завершения инициализации SDK"""
    import asyncio
    
    async def daily_reminder():
        """Ежедневное напоминание"""
        await asyncio.sleep(86400)  # 24 часа
        sdk.logger.info("Выполнение ежедневной задачи")
    
    # Запуск фоновой задачи
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
    
    # Проверка на наличие запрещённых слов
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"Заблокировано сообщение: {word}")
            return  # Не обрабатывать это сообщение
    
    # Нормальная обработка сообщения
    await event.reply(f"Получено: {text}")
```

### Фильтрация по чёрному списку

```python
# Загрузка чёрного списка из конфигурации или хранилища
blacklist = await sdk.storage.aget("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"Пользователь в чёрном списке: {user_id}")
        return  # Не обрабатывать
    
    # Нормальная обработка
    await event.reply(f"Привет, {user_id}")
```

## Адаптация к разным платформам

### Платформенно-специфичные ответы

```python
@command("help", help="Показать справку")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Справка для платформы Yunhu...")
    elif platform == "telegram":
        await event.reply("Справка для Telegram...")
    elif platform == "onebot11":
        await event.reply("Справка для OneBot11...")
    else:
        await event.reply("Общая информация о справке")
```

### Обнаружение особенностей платформы

```python
@command("rich", help="Отправить сообщение с разметкой")
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
        # Другие платформы используют обычный текст
        await event.reply("Жирный текст Курсивный текст")
```

## Расширенная отправка сообщений (повтор/таймаут/массовая)

Помимо простого `event.reply()`, вы можете использовать DSL отправки через адаптер для реализации более сложных сценариев: автоматическое повторение при сбое, отмена по таймауту, выполнение логики после успешной отправки, массовая отправка нескольких сообщений.

> В следующих примерах `event.get_detail_type()` и `event.get_target_id()` используются для получения типа цели и её ID (для групп автоматически берётся `group_id`, для личных сообщений — `user_id`), чтобы избежать жёсткой привязки к коду.

### Выполнение логики после успешной отправки

```python
@command("pay", help="Симуляция оплаты")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # Вычитание очков только после успешной отправки
    send_result = await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
                         .Text("Оплата прошла успешно, 10 очков сняты"))
    if send_result:
        await sdk.storage.aset(f"points:{user_id}", -10)
```

### Повтор при сбое + отмена по таймауту

```python
@command("notice", help="Отправить важное уведомление")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Максимально 3 попытки, каждая с таймаутом 10 секунд
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"Не удалось отправить уведомление: {ctx.error}"))
            .Text("Это важное уведомление"))
    # Отправка в фоновом режиме
```

### Массовая отправка нескольких сообщений

Отправка нескольких сообщений по одной цепочке, с единым управлением:

```python
@command("announce", help="Отправить объявление")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Сбор нескольких сообщений, отправка в едином потоке (по умолчанию параллельно)
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 Сегодняшнее объявление")
                    .Image("https://example.com/banner.jpg")
                    .Text("Подробная информация на изображении выше")
                    .Retry(2)            # Повтор для неудачных сообщений
                    .send_all())
    sdk.logger.info(f"Массовая отправка завершена, всего {len(results)} сообщений")
```

> Более подробные правила и описание массовой отправки см. в [Руководстве по особенностям платформ](../platform-guide/README.md#правила-декораторов-отправки).

## Контроль доступа

### Проверка на права администратора

```python
# Список владельцев
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """Проверка, является ли пользователь владельцем"""
    return user_id in MASTERS

@command("master", help="Команда владельца")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("Недостаточно прав, эта команда доступна только владельцу")
        return
    
    await event.reply("Команда владельца выполнена успешно")

@command("addmaster", help="Добавить владельца")
async def addmaster_handler(event):
    if not is_master(event.get_user_id()):
        return
    
    args = event.get("text", "").split()
    if len(args) < 2:
        await event.reply("Использование: /addmaster <ID пользователя>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"Добавлен владелец: {new_master}")
```

### Проверка в группе

```python
@command("groupinfo", help="Показать информацию о группе")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("Эта команда доступна только в группах")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"ID группы: {group_id}, ваш ID: {user_id}")
```

## Статистика сообщений

### Подсчёт сообщений

> **Внимание:** В следующем примере используется `sdk.storage.get/set` для простого подсчёта. В сценариях с высокой нагрузкой рекомендуется использовать `sdk.storage.transaction()` для обеспечения атомарности.

```python
@message.on_message()
async def count_handler(event):
    # Получить статистику
    stats = await sdk.storage.aget("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # Обновить статистику
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # Сохранить
    await sdk.storage.aset("message_stats", stats)

@command("stats", help="Показать статистику сообщений")
async def stats_handler(event):
    stats = await sdk.storage.aget("message_stats", {
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

> **Внимание:** В следующем примере используется встроенная память для хранения истории сообщений, **данные будут потеряны при перезапуске**. В продакшене рекомендуется использовать `sdk.storage` или таблицу SQLite для постоянного хранения.

```python
from ErisPulse.Core.Event import command, message

# Хранение истории сообщений
message_history = []

@message.on_message()
async def store_handler(event):
    """Сохранение сообщений для поиска"""
    user_id = event.get_user_id()
    text = event.get_text()
    
    message_history.append({
        "user_id": user_id,
        "text": text,
        "time": event.get_time()
    })
    
    # Ограничение количества записей
    if len(message_history) > 1000:
        message_history.pop(0)

@command("search", help="Поиск сообщений")
async def search_handler(event):
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите ключевое слово для поиска")
        return
    
    keyword = " ".join(args)
    results = []
    
    # Поиск в истории
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("Сообщения не найдены")
        return
    
    # Отображение результатов
    result_text = f"Найдено {len(results)} сообщений:\n\n"
    for i, msg in enumerate(results[:10], 1):  # Показать максимум 10 сообщений
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
                # Рекомендуется использовать встроенный клиент SDK для скачивания
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

> **Внимание:** В следующем примере используется заглушка API, на практике замените на свой сервис распознавания изображений.

```python
from ErisPulse.Core import client

@command("identify", help="Распознать изображение")
async def identify_handler(event):
    """Распознавание изображений в сообщении"""
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
    """Вызов API распознавания изображений (пример) — используем встроенный клиент SDK"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "Распознавание не удалось")
```

## Далее

- **Функционал готов, нужно запустить на постоянной основе:** Посмотрите [Руководство по развертыванию](../user-guide/deployment.md), как использовать Docker / systemd для фоновой работы и резервного копирования.
- **Хотите распространить свой функционал:** Начните с [Введения в разработку модулей](../developer-guide/modules/getting-started.md), чтобы превратить скрипт в модуль, который можно установить.
- **Нужно настроить или отладить "модуль не работает":** Ознакомьтесь с [Описанием конфигурационного файла](../user-guide/configuration.md) и [Областью действия (scope)](../advanced/scope.md).