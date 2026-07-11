# Примеры распространённых задач

Это руководство предоставляет примеры реализации распространённых функций, помогая вам быстро реализовать часто используемые возможности.

## Содержание

1. Хранение данных
2. Периодические задачи
3. Фильтрация сообщений
4. Адаптация для нескольких платформ
5. Расширенная отправка сообщений (повтор/тайм-аут/пакетная)
6. Управление правами доступа
7. Статистика сообщений
8. Функции поиска
9. Обработка изображений

## Хранение данных

### Простая функция подсчёта

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="Просмотр количества вызовов команды")
async def count_handler(event):
    # Получение счётчика
    count = sdk.storage.get("command_count", 0)
    
    # Увеличение счётчика
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"Это {count}-й вызов этой команды")
```

### Хранение данных пользователя

```python
@command("profile", help="Просмотр профиля")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # Получение данных пользователя
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
Ник: {user_data['nickname']}
Дата вступления: {user_data['join_date']}
Сообщений: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="Установить ник")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите ник")
        return
    
    # Обновление данных пользователя
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"Ник установлен на: {' '.join(args)}")
```

## Периодические задачи

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
        
        @command("timer", help="Управление таймером")
        async def timer_handler(event):
            await event.reply("Таймер работает...")
    
    def _start_timers(self):
        """Запуск периодических задач"""
        # Выполнять раз в 60 секунд
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # Выполнять в полночь
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """Задача, выполняемая каждую минуту"""
        self.sdk.logger.info("Выполнение задачи каждую минуту")
        # Ваша логика...
    
    async def _daily_task(self):
        """Задача, выполняемая в полночь (Примечание: основано на времени UTC, при необходимости измените на локальное время)"""
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

### Фильтр по ключевым словам

```python
from ErisPulse.Core.Event import message

blocked_words = ["мусор", "реклама", "фишинг"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # Проверка наличия чувствительных слов
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"Блокировка чувствительного сообщения: {word}")
            return  # Не обрабатывать это сообщение
    
    # Обработка сообщения нормально
    await event.reply(f"Получено: {text}")
```

### Фильтр чёрного списка

```python
# Загрузка чёрного списка из конфигурации или хранилища
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"Пользователь в чёрном списке: {user_id}")
        return  # Не обрабатывать
    
    # Обработка нормально
    await event.reply(f"Привет, {user_id}")
```

## Адаптация для нескольких платформ

### Ответы, специфичные для платформы

```python
@command("help", help="Показать справку")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Справка по платформе Yunhu...")
    elif platform == "telegram":
        await event.reply("Справка по платформе Telegram...")
    elif platform == "onebot11":
        await event.reply("Справка OneBot11...")
    else:
        await event.reply("Общая справка")
```

### Определение особенностей платформы

```python
@command("rich", help="Отправить богатое сообщение")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # Yunhu поддерживает HTML
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>Жирный текст</b><i>Курсив</i>"
        )
    elif platform == "telegram":
        # Telegram поддерживает Markdown
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**Жирный текст** *Курсив*"
        )
    else:
        # Другие платформы используют обычный текст
        await event.reply("Жирный текст Курсив")
```

## Расширенная отправка сообщений (повтор/тайм-аут/пакетная)

Помимо простого `event.reply()`, вы можете реализовать более сложные сценарии отправки с помощью Send DSL адаптера: автоматический повтор при сбое, отмена по тайм-ауту, выполнение логики после успеха, отправка нескольких сообщений пакетом.

> В следующих примерах используется `event.get_detail_type()` и `event.get_target_id()` для получения типа и ID цели из события (для групповых чатов автоматически берётся group_id, для личных чатов автоматически берётся user_id), чтобы избежать жёстко прописанных значений.

### Выполнение логики после успешной отправки

```python
@command("pay", help="Моделирование оплаты")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # Вычесть очки только после успешной отправки
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("Оплата успешна, вычтено 10 очков"))
```

### Повтор при сбое + Отмена по тайм-ауту

```python
@command("notice", help="Отправить важное уведомление")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Повторить не более 3 раз, тайм-аут 10 секунд
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"Не удалось отправить уведомление: {ctx.error}"))
            .Text("Это важное уведомление"))
    # Не дожидаться, отправка в фоне
```

### Отправка нескольких сообщений пакетом

Отправка нескольких сообщений по одному каналу, единое выполнение:

```python
@command("announce", help="Отправить объявление")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Построить несколько сообщений, отправить их единообразно (по умолчанию параллельно)
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 Сегодняшнее объявление")
                    .Image("https://example.com/banner.jpg")
                    .Text("Подробности см. на изображении выше")
                    .Retry(2)            # Отдельные повторы для неудачных элементов
                    .send_all())
    sdk.logger.info(f"Пакетная отправка завершена, всего {len(results)} сообщений")
```

> Более полные правила и пояснения по пакетной отправке см. в [Руководстве по особенностям платформы](../platform-guide/README.md#правила-декораторов-отправки).

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
        await event.reply("Введите ID администратора для добавления")
        return
    
    new_admin = args[0]
    ADMINS.append(new_admin)
    await event.reply(f"Администратор добавлен: {new_admin}")
```

### Права доступа в группах

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

> **Внимание**: следующие примеры используют `sdk.storage.get/set` для простого подсчёта. В сценариях с высокой concurrency рекомендуется использовать `sdk.storage.transaction()` для обеспечения атомарности.

```python
@message.on_message()
async def count_handler(event):
    # Получение статистики
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # Обновление статистики
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # Сохранение
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

## Функции поиска

### Простой поиск

> **Внимание**: следующие примеры используют список в памяти для хранения истории сообщений, **данные будут потеряны после перезагрузки программы**. В рабочей среде рекомендуется использовать `sdk.storage` или таблицы SQLite для персистентного хранения.

```python
from ErisPulse.Core.Event import command, message

# Хранение истории сообщений
message_history = []

@message.on_message()
async def store_handler(event):
    """Хранение сообщений для поиска"""
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
    
    # Поиск по истории записей
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("Сообщения не найдены")
        return
    
    # Отображение результатов
    result_text = f"Найдено {len(results)} подходящих сообщений:\n\n"
    for i, msg in enumerate(results[:10], 1):  # Максимум отображать 10
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

> **Внимание**: в следующих примерах используется фиктивный адрес API, при реальном использовании замените его на адрес вашего сервиса распознавания изображений.

```python
from ErisPulse.Core import client

@command("identify", help="Распознавание изображения")
async def identify_handler(event):
    """Распознавание изображения в сообщении"""
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

- [Руководство для пользователей](../user-guide/) — 了解配置和模块管理
- [Руководство для разработчиков](../developer-guide/) — 学习开发模块和适配器
- [Продвинутые темы](../advanced/) — 了解 возможности фреймворка глубже

Пожалуйста, верните только полный переведенный Markdown-код без каких-либо других слов.