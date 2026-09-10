# Примеры распространенных задач

В этом руководстве приведены примеры реализации распространенных функций, чтобы помочь вам быстро реализовать часто используемые функции.

## Содержание

1. Данные и постоянное хранение
2. Планирование задач
3. Фильтрация сообщений
4. Многоуровневая адаптация платформ
5. Расширенная отправка сообщений (повторная попытка/тайм-аут/пакетная отправка)
6. Управление правами
7. Статистика сообщений
8. Функция поиска
9. Обработка изображений

## Данные постоянного хранения

### Простой счётчик

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="Посмотреть количество вызовов команды")
async def count_handler(event):
    # Получить счёт
    count = sdk.storage.get("command_count", 0)
    
    # Увеличить счёт
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"Это {count}-й вызов этой команды")
```

### Хранение данных пользователя

```python
@command("profile", help="Посмотреть профиль")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # Получить данные пользователя
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
Ник: {user_data['nickname']}
Дата регистрации: {user_data['join_date']}
Количество сообщений: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="Установить ник")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите ник")
        return
    
    # Обновить данные пользователя
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"Ник установлен на: {' '.join(args)}")
```

## Планировщик задач

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
        """Запуск периодических задач при загрузке модуля"""
        self._start_timers()
        
        @command("timer", help="Управление таймерами")
        async def timer_handler(event):
            await event.reply("Таймеры запущены...")
    
    def _start_timers(self):
        """Запуск периодических задач"""
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
        """Задача, выполняемая каждый день в полночь (замечание: расчет основан на UTC, если нужен локальный часовой пояс, измените самостоятельно)"""
        import time
        
        while True:
            # Вычисление времени до полночи
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
    """Запуск периодических задач после завершения инициализации SDK"""
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
    
    # Обработка сообщения
    await event.reply(f"Получено: {text}")
```

### Фильтрация по чёрному списку

```python
# Загрузка чёрного списка из конфигурации или хранилища
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"Пользователь в чёрном списке: {user_id}")
        return  # Не обрабатывать
    
    # Обычная обработка
    await event.reply(f"Привет, {user_id}")
```

## Многофункциональная адаптация

### Платформенно-специфические ответы

```python
@command("help", help="Показать справку")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Справка по платформе Yunhu...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("Общая информация о справке")
```

### Обнаружение особенностей платформы

```python
@command("rich", help="Отправить богатый текст")
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

## Расширенная отправка сообщений (повтор/таймаут/пакетная отправка)

Помимо простого `event.reply()`, вы можете реализовать более сложные сценарии отправки с помощью DSL-инструментов адаптера: автоматический повтор при неудаче, отмена по таймауту, выполнение логики после успешной отправки, пакетная отправка нескольких сообщений.

> В следующих примерах используются `event.get_detail_type()` и `event.get_target_id()` для получения типа и ID цели из события (для группового чата автоматически берется `group_id`, для личного чата — `user_id`), чтобы избежать жесткой привязки к конкретным значениям.

### Выполнение логики после успешной отправки

```python
@command("pay", help="Симуляция оплаты")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # Вычитание баллов только после успешной отправки
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("Оплата прошла успешно, вычтено 10 баллов"))
```

### Повтор при неудаче + отмена по таймауту

```python
@command("notice", help="Отправка важного уведомления")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Максимум 3 попытки, каждая с таймаутом 10 секунд
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"Не удалось отправить уведомление: {ctx.error}"))
            .Text("Это важное уведомление"))
    # Отправка в фоновом режиме без ожидания
```

### Пакетная отправка нескольких сообщений

Отправка нескольких сообщений по одной цепочке с единым выполнением:

```python
@command("announce", help="Отправка объявления")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Создание нескольких сообщений и их отправка (по умолчанию параллельно)
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 Сегодняшнее объявление")
                    .Image("https://example.com/banner.jpg")
                    .Text("Подробности смотрите на изображении выше")
                    .Retry(2)            # Каждое неудачное сообщение повторяет отправку
                    .send_all())
    sdk.logger.info(f"Пакетная отправка завершена, всего {len(results)} сообщений")
```

> Более полное описание правил и пакетной отправки см. в [Руководстве по особенностям платформы](../platform-guide/README.md#декораторы-правил-отправки).

## Контроль доступа

### Проверка администратора

```python
# Список владельцев
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """Проверка, является ли пользователь владельцем фреймворка"""
    return user_id in MASTERS

@command("master", help="Команда владельца фреймворка")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("Недостаточно прав, эта команда доступна только владельцу фреймворка")
        return
    
    await event.reply("Команда владельца фреймворка выполнена успешно")

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

### Права группы

```python
@command("groupinfo", help="Просмотр информации о группе")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("Эта команда доступна только в групповых чатах")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"ID группы: {group_id}, твой ID: {user_id}")
```

## Статистика сообщений

### Подсчет сообщений

> **Внимание**: В следующем примере для простого подсчета используется `sdk.storage.get/set`. В сценариях с высокой并发ностью рекомендуется использовать `sdk.storage.transaction()`, чтобы гарантировать атомарность.

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

@command("stats", help="Просмотр статистики сообщений")
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

> **Внимание**: В следующем примере история сообщений сохраняется в памяти, **данные будут потеряны при перезапуске программы**. В продакшн-среде рекомендуется использовать `sdk.storage` или SQLite-таблицы для постоянного хранения.

```python
from ErisPulse.Core.Event import command, message

# Хранилище истории сообщений
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
    
    # Ограничение количества записей в истории
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
    
    # Поиск в истории сообщений
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

### Загрузка и хранение изображений

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
                    
                    # Сохранение в файл
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"Изображение сохранено: {filename}")
                    await event.reply("Изображение сохранено")
```

### Пример распознавания изображений

> **Важно**: В следующем примере используется заглушка API-адреса, при фактическом использовании замените на свой собственный сервис распознавания изображений.

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
    """Вызов API распознавания изображений (пример) - используя встроенный клиент SDK"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "Распознавание не удалось")
```

## Далее

- [Руководство пользователя](../user-guide/) - узнать о настройке и управлении модулями
- [Руководство для разработчиков](../developer-guide/) - узнать о разработке модулей и адаптеров
- [Расширенные темы](../advanced/) - углубиться в особенности фреймворка