# Основные концепции

В этом руководстве представлены основные концепции ErisPulse, которые помогут вам понять дизайн-философию и базовую архитектуру фреймворка.

## Архитектура, управляемая событиями

ErisPulse использует архитектуру, управляемую событиями (event-driven), где все взаимодействия осуществляются через обработку событий.

### Поток событий

```
Пользователь отправляет сообщение
      │
      ▼
Платформа получает сообщение
      │
      ▼
Адаптер получает нативные события платформы
      │
      ▼
Преобразование в стандартное событие OneBot12
      │
      ▼
Отправка в систему событий
      │
      ▼
Распределение зарегистрированным обработчикам
      │
      ▼
Модуль обрабатывает событие
      │
      ▼
Отправка ответа через адаптер
      │
      ▼
Отображение пользователю платформой
```

### Стандарт OneBot12

ErisPulse использует OneBot12 в качестве стандарта основных событий. OneBot12 — это универсальный стандарт интерфейса чат-ботов, определяющий единый формат событий.

Все адаптеры преобразуют событийные данные, специфичные для платформы, в формат OneBot12, обеспечивая согласованность кода.

## Основные компоненты

### 1. Объект SDK

SDK — это единая точка входа для всех функций, предоставляющая доступ к основным компонентам.

```python
from ErisPulse import sdk

# Доступ к основным модулям
sdk.storage    # Система хранения
sdk.config     # Система конфигурации
sdk.logger     # Система логирования
sdk.adapter    # Система адаптеров
sdk.module     # Система модулей
sdk.router     # Система маршрутизации
sdk.client     # HTTP-клиент
sdk.lifecycle  # Система жизненного цикла
```

### 2. Объект Event

Объект Event инкапсулирует данные события, предоставляя удобные методы доступа.

```python
@command("info")
async def info_handler(event):
    # Получение информации о событии
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # Отправка ответа
    await event.reply(f"Пользователь: {user_id}, Платформа: {platform}")
```

### 3. Адаптер

Адаптер служит мостом между ErisPulse и внешними платформами.

**Обязанности:**
- Получать нативные события платформы
- Преобразовывать в стандартный формат OneBot12
- Отправлять события стандартного формата в платформу

**Примеры адаптеров:**
- Адаптер Yunhu: взаимодействие с платформой Yunhu
- Адаптер Telegram: взаимодействие с Telegram Bot API
- Адаптер OneBot11: взаимодействие с приложениями, совместимыми с OneBot11
- Почтовый адаптер: обработка входящей и исходящей почты

### 4. Модуль

Модуль — это базовая единица расширения функционала, способная:

- Регистрировать обработчики событий
- Реализовывать бизнес-логику
- Вызывать адаптеры для отправки сообщений
- Использовать сервисы, предоставляемые основными модулями

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class MyModule(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0
        )

    async def on_load(self, event):
        """Вызывается при загрузке модуля"""
        # Регистрация обработчика событий
        @command("mycmd", help="Моя команда")
        async def my_command(event):
            await event.reply("Команда выполнена успешно")

        self.logger.info("Модуль загружен")

    async def on_unload(self, event):
        """Вызывается при выгрузке модуля"""
        self.logger.info("Модуль выгружен")
```

## Типы событий

### Событие сообщения

Обработка любых сообщений, отправляемых пользователями (включая личные и групповые чаты).

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    text = event.get_text()
    await event.reply(f"Получено сообщение: {text}")
```

### Событие команды

Обработка сообщений, начинающихся с префикса команды (например, `/hello`).

```python
from ErisPulse.Core.Event import command

@command("hello", help="Отправка приветствия")
async def hello_handler(event):
    await event.reply("Привет!")
```

### Событие уведомления

Обработка системных уведомлений (например, добавление в друзья, изменения участников группы).

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("Добро пожаловать в друзья!")
```

### Событие запроса

Обработка запросов пользователей (например, запросы на добавление в друзья, приглашения в группы).

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    await event.reply("Ваш запрос на добавление в друзья получен")
```

### Метасобытие

Обработка системных событий уровня (например, подключение, пульсация/heartbeat).

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} подключено успешно")
```

## Описание основных модулей

### Storage (Хранилище)

Базирующаяся на SQLite система хранения ключ-значение для персистентных данных.

```python
# Установка значения
sdk.storage.set("key", "value")

# Получение значения
value = sdk.storage.get("key", "default_value")

# Пакетные операции
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# Транзакция
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config (Конфигурация)

Управление файлами конфигурации в формате TOML.

```python
# Получение конфигурации
config = sdk.config.getConfig("MyModule", {})

# Установка конфигурации
sdk.config.setConfig("MyModule", {"key": "value"})

# Чтение вложенной конфигурации
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger (Логирование)

Модульная система логирования.

```python
# Запись в лог
sdk.logger.info("Это информационное сообщение")
sdk.logger.warning("Это предупреждение")
sdk.logger.error("Это ошибка")

# Получение дочернего логгера
child_logger = sdk.logger.get_child("submodule")
child_logger.info("Лог подмодуля")
```

**Синтаксический сахар для доступа к атрибутам**

Помимо метода `get_child()`, вы также можете создавать дочерние логгеры через **доступ к атрибутам**, это более лаконичный способ:

```python
# Создание дочернего логгера через атрибут
sdk.logger.mymodule.info("Сообщение модуля")

# Поддержка вложенного доступа
sdk.logger.mymodule.database.info("Сообщение базы данных")
```

### Router (Маршрутизация)

Управление маршрутизацией HTTP и WebSocket, поддерживающая нативные типы FastAPI и абстрактные типы ErisPulse.

> Роутеры поддерживают два типа аннотаций: нативные типы FastAPI (`fastapi.Request` / `fastapi.WebSocket`) и абстрактные типы ErisPulse (`HttpRequest` / `WebSocketConnection`). Рекомендуется использовать абстрактные типы для лучшей переносимости.

```python
from ErisPulse import sdk

# Способ 1: Использование абстрактных типов ErisPulse (рекомендуется)
from ErisPulse.Core import HttpRequest, WebSocketConnection

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}

@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    data = await ws.receive_text()
    await ws.send_text(f"Эхо: {data}")

# Способ 2: Использование нативных типов FastAPI (совместимо со старым кодом)
from fastapi import Request, WebSocket

@sdk.router.get("MyModule", "/api2")
async def handler2(request: Request):
    return {"status": "ok"}
```

{!--< tips >!--}
> **Автоматическая инъекция**: Система маршрутизации автоматически внедряет объекты соответствующих типов на основе аннотаций параметров, без необходимости ручного создания.
> 
> **Частые проблемы**: Если вы видите ошибку `{"detail":[{"type":"missing","loc":["query","request"],"msg":"Field required"}]}`, значит, отсутствуют аннотации типов. Убедитесь, что параметры обработчиков HTTP используют аннотацию `request`, а обработчики WebSocket — `websocket` или `ws`.

Дополнительные функции маршрутизации см. в разделе [Руководство по маршрутизатору](../advanced/router.md).

### Client (HTTP-клиент)

Единый HTTP-клиент для отправки HTTP-запросов. Модулям и адаптерам следует предпочитать глобальный клиент вместо прямого импорта `aiohttp`.

```python
from ErisPulse.Core import client

# GET запрос
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# POST запрос
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice"},
)

# Свойства ответа
resp.status        # Код статуса (например, 200)
resp.headers       # Заголовки ответа
body = await resp.text()   # Текстовое тело ответа
data = await resp.json()   # Разбор JSON
```

{!--< tips >!--}
> Глобальный клиент поддерживает автоматическую переаттестацию, управление таймаутами, статистику запросов и интеграцию с событиями жизненного цикла. Подробнее см. в разделе [HTTP-клиент](../advanced/http-client.md).
>
> Также можно использовать `sdk.client` через `from ErisPulse import sdk`, эффект будет одинаковым.

## Отправка сообщений через SendDSL

Адаптеры предоставляют интерфейс для отправки сообщений с поддержкой цепных вызовов (чейнинг).

### Базовая отправка

```python
# Получение экземпляра адаптера
yunhu = sdk.adapter.get("yunhu")

# Отправка сообщения
await yunhu.Send.To("user", "U1001").Text("Hello")

# Указание аккаунта отправителя
await yunhu.Send.Using("bot1").To("group", "G1001").Text("Сообщение группы")
```

### Цепные модификаторы

```python
# @пользователя
await yunhu.Send.To("group", "G1001").At("U2001").Text("@сообщение")

# Ответ на сообщение
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("ответ")

# @всем
await yunhu.Send.To("group", "G1001").AtAll().Text("уведомление")
```

### Методы ответа Event

Объект Event предоставляет удобные методы для ответов:

```python
@command("test")
async def test_handler(event):
    # Простая текстовая реакция
    await event.reply("Содержимое ответа")
    
    # Отправка изображения
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # Отправка голосового
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## Система ленивой загрузки

ErisPulse поддерживает ленивую загрузку модулей; модули инициализируются только при первом обращении к ним, что ускоряет запуск системы.

```python
class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,   # Включить ленивую загрузку (по умолчанию)
            priority=0       # Приоритет загрузки
        )
```

**Сценарии с немедленной загрузкой:**
- Модули, прослушивающие события жизненного цикла
- Модули периодических задач (таймеров)
- Модули, требующие инициализации при запуске приложения

## Далее

- [Введение в обработку событий](event-handling.md) — научитесь обрабатывать различные типы событий
- [Примеры распространенных задач](common-tasks.md) — освоите реализацию типичных функций