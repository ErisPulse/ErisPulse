# Примеры типичных задач

> [!TIP]
> **Когда читать этот документ**: когда нужно добавить боту какую-то конкретную функцию, обращайтесь к нужному разделу — персистентность, задачи по расписанию, фильтрация сообщений, контроль прав, пакетная отправка; каждый раздел — законченный пример, который можно сразу скопировать. Для системного изучения обработки событий сначала прочитайте [Введение в обработку событий](event-handling.md); если это не нужно — пропустите.

## Содержание

1. Персистентность данных
2. Задачи по расписанию
3. Фильтрация сообщений
4. Адаптация к разным платформам
5. Продвинутая отправка сообщений (повторы/таймауты/пакетная отправка)
6. Контроль прав доступа
7. Статистика сообщений
8. Функция поиска
9. Обработка изображений

## Персистентность данных

### Простой счётчик

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="Просмотр количества вызовов команды")
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
@command("profile", help="Просмотр профиля")
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
Дата присоединения: {user_data['join_date']}
Количество сообщений: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="Установить ник")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("Пожалуйста, введите ник")
        return
    
    # Обновить данные пользователя
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"Ник установлен: {' '.join(args)}")
```

## Задачи по расписанию

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
        """Запуск задач по расписанию при загрузке модуля"""
        self._start_timers()
        
        @command("timer", help="Управление таймером")
        async def timer_handler(event):
            await event.reply("Таймер работает...")
    
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
        self.sdk.logger.info("Выполнение минутной задачи")
        # Ваша логика...
    
    async def _daily_task(self):
        """Задача, выполняемая каждый день в полночь (примечание: расчёт по времени UTC; при необходимости локального времени скорректируйте самостоятельно)"""
        import time
        
        while True:
            # Вычислить время до полуночи
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # Выполнить задачу
            self.sdk.logger.info("Выполнение ежедневной задачи")
            # Ваша логика...
```

### Использование событий жизненного цикла

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """Запуск задач по расписанию после инициализации SDK"""
    import asyncio
    
    async def daily_reminder():
        """Ежедневное напоминание"""
        await asyncio.sleep(86400)  # 24 часа
        sdk.logger.info("Выполнение ежедневной задачи")
    
    # Запустить фоновую задачу
    asyncio.create_task(daily_reminder())
```

## Фильтрация сообщений

### Фильтрация по ключевым словам

```python
from ErisPulse.Core.Event import message

blocked_words = ["спам", "реклама", "фишинг"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # Проверить наличие запрещённых слов
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"Заблокировано сообщение с запрещённым словом: {word}")
            return  # Не обрабатывать это сообщение
    
    # Обычная обработка сообщения
    await event.reply(f"Получено: {text}")
```

### Фильтрация по чёрному списку

```python
# Загрузить чёрный список из конфигурации или хранилища
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"Пользователь из чёрного списка: {user_id}")
        return  # Не обрабатывать
    
    # Обычная обработка
    await event.reply(f"Привет, {user_id}")
```

## Адаптация к разным платформам

### Ответы для конкретных платформ

```python
@command("help", help="Показать справку")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Справка для платформы Yunhu...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("Общая справка")
```

### Определение возможностей платформы

```python
@command("rich", help="Отправить форматированное сообщение")
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
        # На других платформах использовать простой текст
        await event.reply("Жирный текст Курсивный текст")
```

## Продвинутая отправка сообщений (повторы/таймауты/пакетная отправка)

Помимо простого `event.reply()`, с помощью Send DSL адаптера можно реализовать более сложные сценарии отправки: автоматический повтор при неудаче, отмена по таймауту, выполнение логики после успешной отправки, пакетная отправка нескольких сообщений.

> В примерах ниже `event.get_detail_type()` и `event.get_target_id()` используются для получения типа цели и ID из события (в групповом чате автоматически берётся group_id, в личном — user_id), чтобы избежать жёсткого кодирования.

### Выполнение логики после успешной отправки

```python
@command("pay", help="Имитация оплаты")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # Списывать баллы только после успешной отправки
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("Оплата прошла успешно, списано 10 баллов"))
```

### Повтор при неудаче + отмена по таймауту

```python
@command("notice", help="Отправить важное уведомление")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Не более 3 повторов, таймаут 10 секунд каждый
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"Не удалось отправить уведомление: {ctx.error}"))
            .Text("Это важное уведомление"))
    # Не ждать, отправка в фоне
```

### Пакетная отправка нескольких сообщений

Несколько сообщений по одной цепочке, единое выполнение:

```python
@command("announce", help="Отправить объявление")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Собрать несколько сообщений и отправить вместе (по умолчанию параллельно)
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 Объявление на сегодня")
                    .Image("https://example.com/banner.jpg")
                    .Text("Подробности смотрите на изображении выше")
                    .Retry(2)            # Каждый неудавшийся элемент повторяется отдельно
                    .send_all())
    sdk.logger.info(f"Пакетная отправка завершена, всего {len(results)} сообщений")
```

> Более полные правила и описание пакетной отправки смотрите в [Руководстве по возможностям платформ](../platform-guide/README.md#发送规则装饰器).

## Контроль прав доступа

### Проверка администратора

```python
# Список владельцев в конфигурации
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """Проверить, является ли пользователь владельцем фреймворка"""
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
    await event.reply(f"Владелец фреймворка добавлен: {new_master}")
```

### Права в группах

```python
@command("groupinfo", help="Просмотр информации о группе")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("Эта команда доступна только в групповых чатах")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"ID группы: {group_id}, ваш ID: {user_id}")
```

## Статистика сообщений

### Подсчёт сообщений

> **Примечание**: в следующих примерах для простого подсчёта используются `sdk.storage.get/set`. В сценариях с высокой конкурентностью рекомендуется использовать `sdk.storage.transaction()` для обеспечения атомарности.

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
    
    await event.reply(f"Всего сообщений: {stats['total']}\n\nАктивные пользователи:\n{top_text}")
```

## Функция поиска

### Простой поиск

> **Примечание**: в следующем примере история сообщений хранится в списке в памяти, **после перезапуска программы данные будут потеряны**. В продакшене рекомендуется использовать `sdk.storage` или таблицу SQLite для персистентного хранения.

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
    
    # Поиск по истории
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("Совпадающих сообщений не найдено")
        return
    
    # Показать результаты
    result_text = f"Найдено {len(results)} совпадающих сообщений:\n\n"
    for i, msg in enumerate(results[:10], 1):  # Показывать максимум 10 сообщений
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
                    
                    # Сохранить в файл
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"Изображение сохранено: {filename}")
                    await event.reply("Изображение сохранено")
```

### Пример распознавания изображений

> **Примечание**: в следующем примере используется адрес-заглушка API; при реальном использовании замените его на свой сервис распознавания изображений.

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
    """Вызов API распознавания изображений (пример) — с использованием встроенного клиента SDK"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "Не удалось распознать")
```

## Дальнейшие шаги

- **Функция написана и должна работать постоянно**: смотрите [Руководство по развёртыванию](../user-guide/deployment.md) — демон Docker / systemd, резервное копирование и обновление
- **Хотите распространять написанные функции среди других**: начните с [Введения в разработку модулей](../developer-guide/modules/getting-started.md) и превратите скрипт в устанавливаемый модуль
- **Нужно настроить конфигурацию или разобраться, почему «модуль не реагирует»**: смотрите [Описание файла конфигурации](../user-guide/configuration.md) и [Области видимости (scope)](../advanced/scope.md)