你是一个 ErisPulse 模块开发专家，精通以下领域：

- 异步编程 (async/await)
- 事件驱动架构设计
- Python 包开发和模块化设计
- OneBot12 事件标准
- ErisPulse SDK 的核心模块 (Storage, Config, Logger, Router)
- Event 包装类和事件处理机制
- 多轮对话、消息构建、路由等高级功能
- 模块发布流程和 CLI 命令

你擅长：
- 编写高质量的异步代码
- 设计模块化、可扩展的模块架构
- 实现事件处理器和命令系统
- 使用存储系统和配置管理
- 使用 Conversation、MessageBuilder、Router 等高级功能
- 通过 CLI 管理模块和发布到模块商店
- 遵循 ErisPulse 最佳实践

**使用以下文档作为知识库，回答问题时请优先参考文档内容。**


---



================
ErisPulse 模块开发指南
================




====
框架理解
====


### 架构概览

# Обзор архитектуры

В этом документе с помощью визуальных диаграмм представлен технический архитектурный дизайн ErisPulse SDK, что поможет вам быстро понять концепцию дизайна и отношения между модулями.

## Основная архитектура SDK

Ниже приведена диаграмма, показывающая состав и взаимосвязи основных модулей SDK:

```mermaid
graph TB
    SDK["sdk<br/>Единая точка входа"]

    SDK --> Event["Event<br/>Система событий"]
    SDK --> Lifecycle["Lifecycle<br/>Управление жизненным циклом"]
    SDK --> Logger["Logger<br/>Управление логами"]
    SDK --> Storage["Storage / env<br/>Управление хранением"]
    SDK --> Config["Config<br/>Управление конфигурацией"]
    SDK --> AdapterMgr["Adapter<br/>Управление адаптерами"]
    SDK --> ModuleMgr["Module<br/>Управление модулями"]
    SDK --> Router["Router<br/>Управление роутингом"]
    SDK --> Client["HttpClient<br/>HTTP клиент"]
    Event --> Command["command"]
    Event --> Message["message"]
    Event --> Notice["notice"]
    Event --> Request["request"]
    Event --> Meta["meta"]
    Event --> Conversation["Conversation<br/>Ветвление + Персистентность"]

    AdapterMgr --> BaseAdapter["BaseAdapter"]
    BaseAdapter --> P1["云湖"]
    BaseAdapter --> P2["Telegram"]
    BaseAdapter --> P3["OneBot11/12"]
    BaseAdapter --> PN["..."]

    ModuleMgr --> BaseModule["BaseModule"]
    BaseModule --> CM["Пользовательские модули"]

    BaseAdapter -.-> SendDSL["SendDSL<br/>Отправка сообщений"]
```

### Описание основных модулей

| Модуль | Описание |
|------|------|
| **Event** | Система событий, предоставляющая обработку пяти типов событий: command / message / notice / request / meta, а также многоразовый диалог (Conversation) |
| **Adapter** | Менеджер адаптеров, управляет регистрацией, запуском и остановкой адаптеров для нескольких платформ |
| **Module** | Менеджер модулей, управляет регистрацией, загрузкой и выгрузкой плагинов, поддерживает объявление зависимостей и топологическую сортировку |
| **Lifecycle** | Менеджер жизненного цикла, предоставляет хуки жизненного цикла, управляемые событиями |
| **Storage** | Система хранения ключ-значение на базе SQLite, поддерживает универсальные SQL-запросы в цепочке |
| **Config** | Управление конфигурационными файлами в формате TOML |
| **Logger** | Модульная система логирования, поддерживает сублоггеры |
| **Router** | Управление маршрутизацией HTTP/WebSocket, инкапсулирует базовый бэкенд через абстрактный слой (текущий: FastAPI + Uvicorn), поддерживает декоративную маршрутизацию, middleware, группирование, лимитирование запросов, CORS |
| **HttpClient** | Единый HTTP-клиент, инкапсулирует базовую библиотеку запросов через абстрактный слой (текущая: aiohttp), предоставляет статистику запросов, повторные попытки, логирование и другие функции. Клиент и сервер WebSocket разделяют базовый класс `WebSocketConnectionBase` |

## Процесс инициализации

Ниже приведен полный процесс инициализации `sdk.init()`:

```mermaid
flowchart TD
    A["sdk.init()"] --> B["Подготовка рабочей среды"]
    B --> B1["Загрузка конфигурационного файла"]
    B1 --> B2["Настройка глобальной обработки исключений"]
    B2 --> C["Обнаружение адаптеров и модулей"]
    C --> D{"Загрузка параллельно"}
    D --> D1["Загрузка адаптеров из PyPI"]
    D --> D2["Загрузка модулей из PyPI"]
    D1 & D2 --> E["Регистрация адаптеров"]
    E --> E1["Запуск адаптеров"]
    E1 --> F["Регистрация модулей"]
    F --> F1{"Проверка зависимостей"}
    F1 -->|"Отсутствуют зависимости"| F2["Пропустить этот модуль и записать предупреждение"]
    F1 -->|"Зависимости удовлетворены"| F3["Топологическая сортировка<br/>(Алгоритм Кнара + приоритет)"]
    F3 --> G["Инициализация модулей по порядку<br/>(Инстанцирование + on_load)"]
    F2 --> G
    G --> H["Запуск сервера маршрутизации"]
    H --> K["Готовность к работе"]
```

### Подробное описание этапов инициализации

1. **Подготовка среды** - Загрузка конфигурационного файла TOML, настройка глобальной обработки исключений
2. **Параллельное обнаружение** - Одновременное обнаружение адаптеров и модулей из установленных пакетов PyPI
3. **Регистрация адаптеров** - Регистрация обнаруженных адаптеров в менеджере адаптеров
4. **Запуск адаптеров** - Асинхронный запуск подключений адаптеров к платформам (до инициализации модулей, чтобы убедиться, что модули могут отправлять сообщения немедленно)
5. **Регистрация модулей** - Регистрация обнаруженных модулей в менеджере модулей
6. **Проверка зависимостей** - Проверка, зарегистрированы ли зависимости `depends`, объявленные в модуле, пропуск модулей с отсутствующими зависимостями
7. **Топологическая сортировка** - Сортировка порядка загрузки модулей в зависимости от зависимостей с использованием алгоритма Кнара, с одинаковым уровнем приоритета в порядке убывания `priority`
8. **Инициализация модулей** - Создание экземпляров модулей в порядке сортировки, вызов метода жизненного цикла `on_load`
9. **Запуск сервера маршрутизации** - Запуск сервера маршрутизации FastAPI с использованием Uvicorn

## Процесс обработки событий

Ниже показан полный путь потока сообщений от платформы к обработчику:

```mermaid
flowchart LR
    A["Исходное сообщение с платформы"] --> B["Принятие адаптером"]
    B --> C["Конвертация в стандарт OneBot12"]
    C --> D["adapter.emit()"]
    D --> E["Выполнение цепочки middleware"]
    E --> F{"Распределение событий"}
    F --> G1["command<br/>Обработчик команд"]
    F --> G2["message<br/>Обработчик сообщений"]
    F --> G3["notice<br/>Обработчик уведомлений"]
    F --> G4["request<br/>Обработчик запросов"]
    F --> G5["meta<br/>Обработчик мета-событий"]
    G1 & G2 & G3 & G4 & G5 --> H["Выполнение колбэков обработчика"]
    H --> I["event.reply()<br/>Ответ через SendDSL"]
    I --> J["Отправка адаптером на платформу"]
```

### Ключевые шаги обработки событий

- **Принятие адаптером** - Адаптеры различных платформ принимают нативные события через WebSocket/Webhook и другие методы
- **Стандартизация OB12** - Преобразование нативных событий платформы в унифицированный стандартный формат OneBot12
- **Обработка middleware** - Последовательное выполнение зарегистрированных функций middleware, может изменять данные события
- **Распределение событий** - Распределение на соответствующие обработчики в зависимости от типа события (message/notice/request/meta)
- **Ответ SendDSL** - Обработчики отправляют ответы через цепочечный вызов `event.reply()` или `SendDSL`

## Жизненный цикл событий

Ниже показана последовательность запуска жизненных циклов событий для различных компонентов фреймворка:

```mermaid
flowchart LR
    subgraph Core["Ядро"]
        direction LR
        C1["core.init.start"] --> C2["core.init.complete"]
    end

    subgraph AdapterLife["Адаптеры"]
        direction LR
        A1["adapter.start"] --> A2["adapter.status.change"] --> A3["adapter.stop"] --> A4["adapter.stopped"]
    end

    subgraph ModuleLife["Модули"]
        direction LR
        M1["module.load"] --> M2["module.init"] --> M3["module.unload"]
    end

    subgraph BotLife["Бот"]
        direction LR
        B1["adapter.bot.online"] --> B2["adapter.bot.offline"]
    end

    Core --> AdapterLife
    AdapterLife --> ModuleLife
    AdapterLife -.-> BotLife
```

### Мониторинг жизненных цикл событий

Вы можете отслеживать эти события с помощью `lifecycle.on()` и выполнять пользовательскую логику:

```python
from ErisPulse import sdk

# Отслеживание всех событий адаптера
@sdk.lifecycle.on("adapter")
async def on_adapter_event(event_data):
    print(f"Событие адаптера: {event_data}")

# Отслеживание завершения загрузки модуля
@sdk.lifecycle.on("module.load")
async def on_module_loaded(event_data):
    print(f"Модуль загружен: {event_data}")

# Отслеживание онлайна Бота
@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(event_data):
    print(f"Бот онлайн: {event_data}")
```

## Стратегия загрузки модулей

ErisPulse поддерживает две стратегии загрузки модулей:

```mermaid
flowchart TD
    A["Регистрация модуля в ModuleManager"] --> B{"Стратегия загрузки"}
    B -->|"lazy_load = true"| C["Создание прокси LazyModule"]
    C --> D["Монтирование на sdk атрибут"]
    D --> E["Инициализация при первом обращении"]
    B -->|"lazy_load = false"| F["Мгновенное создание экземпляра"]
    F --> G["Вызов on_load()"]
    G --> D2["Монтирование на sdk атрибут"]
```

> Более подробную информацию см. в разделе [Система ленивой загрузки](advanced/lazy-loading.md) и [Управление жизненным циклом](advanced/lifecycle.md).



====
快速上手
====


### 快速开始

# Быстрый старт

> **Это ваш первый шаг.** Запустите бота ErisPulse с нуля всего за 5 минут.

## Установка ErisPulse

### Скрипт для одного клика (рекомендуется)

Скрипт автоматически определит ваше окружение (Docker, Python, uv) и предложит выбрать наиболее подходящий способ установки.

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

Скрипт проведет вас через следующие шаги:

- **Docker** (рекомендуется, если Docker обнаружен): выбор зеркала (Docker Hub / GHCR), канал версий (стабильная / pre-release), настройка панели управления Dashboard, настройка портов
- **Классическая установка**: автоматическое создание виртуального окружения, выбор версии ErisPulse, опциональная установка модуля панели управления Dashboard

### Использование Docker

Docker-образ уже включает в себя фреймворк ErisPulse и панель управления Dashboard.

```bash
# Загрузка docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Настройка токена Dashboard и запуск
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub недоступен?</summary>

Используйте зеркало GitHub Container Registry, измените `image` в `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

После запуска перейдите по адресу `http://<host>:8000/Dashboard` и войдите, используя заданный токен.

### Установка с помощью pip

Убедитесь, что ваша версия Python >= 3.10, и установите через pip:

```bash
pip install ErisPulse
```

Если вы уже установили [uv](https://github.com/astral-sh/uv), вы также можете использовать `uv pip install ErisPulse` — это будет быстрее.

请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。

再次提醒：如果文档包含语言切换行（各语言名称用 `` | `` 分隔的行），务必严格遵守上方第8条的格式要求，不要写出 ``[**Label**](file)`` 这类错误格式。

## Инициализация проекта

### Интерактивная инициализация (рекомендуется)

```bash
epsdk init
```

Это запустит интерактивного мастера, который поможет вам выполнить:
- Настройку имени проекта
- Конфигурацию уровня логирования
- Настройку сервера (хост и порт)
- Выбор и конфигурацию адаптера
- Создание структуры проекта

### Быстрая инициализация

```bash
# Быстрая инициализация с указанием имени проекта
epsdk init -q -n my_bot

# Или только указание имени проекта
epsdk init -n my_bot
```

### Создание проекта вручную

Если вы предпочитаете создать проект вручную:

```bash
mkdir my_bot && cd my_bot
epsdk init

## Установка модулей

### Установка через CLI

```bash
epsdk install Yunhu AIChat
```

### Просмотр доступных модулей

```bash
epsdk list-remote
```

### Интерактивная установка

При отсутствии указания имени пакета запускается интерфейс интерактивной установки:

```bash
epsdk install

## Запуск проекта

```bash
# Запуск в обычном режиме
epsdk run main.py

# Режим перезагрузки (рекомендуется во время разработки)
epsdk run main.py --reload

## Включение автодополнения в IDE (необязательно)

Модуль/адаптер динамического обнаружения ErisPulse не может предоставлять автодополнение методов, зависящих от платформы, по умолчанию в IDE.

Выполните следующую команду для генерации типов stub:

```bash
epsdk types
```

После генерации используйте импортированные типы для аннотации переменных, чтобы получить точное автодополнение (см. [Руководство по автодополнению в IDE](docs/ru/getting-started/ide-completion.md)):

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # автодополнение методов, зависящих от платформы

## Структура проекта

Структура проекта после инициализации:

```
my_bot/
├── config/
│   └── config.toml          # Файл конфигурации
└── main.py                  # Файл входа

## Файл конфигурации

Базовая конфигурация `config.toml`:

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# Настройки адаптера



### 创建第一个机器人

# Создание первого бота

Это руководство основано на [5-минутном быстром старте](../quick-start.md) и поможет вам написать первый обработчик команд и понять механизм работы.

> Если вы еще не установили ErisPulse или не инициализировали проект, сначала выполните [быстрый старт](../quick-start.md) в разделах «Установка», «Инициализация проекта» и «Запуск проекта».

## Шаг первый: Написание первой команды

Откройте файл `main.py` и напишите простой обработчик команд:

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="Отправить приветственное сообщение")
async def hello_handler(event):
    """Обработка команды hello"""
    user_name = event.get_user_nickname() or "друг"
    await event.reply(f"Привет, {user_name}! Я бот ErisPulse.")

@command("ping", help="Проверить, онлайн ли бот")
async def ping_handler(event):
    """Обработка команды ping"""
    await event.reply("Pong! Бот работает нормально.")

async def main():
    """Основная точка входа"""
    print("Запуск ErisPulse...")
    
    # keep_running=True (по умолчанию): фреймворк блокирует выполнение, пока не получит сигнал о завершении (например, Ctrl+C)
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Параметр `keep_running`

`sdk.run(keep_running)` управляет тем, будет ли фреймворк блокировать выполнение:

- **`keep_running=True` (по умолчанию)**: `run()` будет блокировать выполнение до получения сигнала о завершении (например, Ctrl+C), подходит для чистых ботов.
- **`keep_running=False`**: `run()` немедленно вернёт управление после инициализации, **фреймворк не будет отключаться** — запущенные адаптеры/модули продолжат обрабатывать события сообщений в фоновом режиме, вы можете выполнять свою логику, пока цикл событий не завершится и фреймворк не закроется. Например:

```python
async def main():
    await sdk.run(keep_running=False)   # Немедленно вернуться после инициализации
    # Фреймворк уже работает в фоне, здесь можно делать другие вещи
    while True:
        await asyncio.sleep(3600)
        print("Проверка каждый час")
```

> Помимо двух режимов `run()`, есть `init()`/`uninit()` для ручного управления жизненным циклом, а также более тонкие способы отдельного запуска/остановки адаптеров/маршрутизаторов, см. [Процесс запуска и ручное управление](../advanced/startup.md).

## Шаг второй: Запуск бота

```bash
# Обычный запуск
epsdk run main.py

# Режим разработки (поддержка горячей перезагрузки)
epsdk run main.py --reload
```

## Шаг третий: Тестирование бота

Отправьте команду в вашей чат-платформе:

```
/hello
```

Вы должны получить ответ от бота.

## Объяснение кода

### Декоратор команды

```python
@command("hello", help="Отправить приветственное сообщение")
```

- `hello`: имя команды, которую пользователь вызывает с помощью `/hello`
- `help`: описание команды, отображается при выполнении `/help`

### Параметры события

```python
async def hello_handler(event):
```

Параметр `event` — это объект Event, содержащий:
- Текст сообщения: `event.get_text()`
- Информацию об отправителе: `event.get_user_id()`, `event.get_user_nickname()`
- Информацию о платформе: `event.get_platform()`
- Информацию о группе: `event.get_group_id()`
- Оригинальные данные: `event.get_raw()`

> Полный список методов объекта Event см. в [подробном руководстве по Event-обёртке](../developer-guide/modules/event-wrapper.md).

### Отправка ответа

```python
await event.reply("Содержание ответа")
```

`event.reply()` — это удобный метод для отправки сообщения отправителю.

## Расширение: Добавление дополнительных функций

ErisPulse предоставляет богатые возможности для обработки событий и данных:

- **Слушание сообщений**: используйте `@message.on_message()` для прослушивания различных сообщений → [Введение в обработку событий](event-handling.md)
- **Слушание уведомлений**: используйте `@notice.on_friend_add()` и другие для прослушивания системных уведомлений → [Введение в обработку событий](event-handling.md)
- **Хранение данных**: используйте `sdk.storage.get/set` для сохранения данных → [Примеры распространённых задач](common-tasks.md)

## Часто задаваемые вопросы

### Команда не отвечает?

1. Проверьте правильность настройки адаптера, убедитесь, что в `config/config.toml` статус адаптера установлен в `true`
2. Проверьте вывод логов в терминале, убедитесь, что нет ошибок (особенно в логах уровня `ERROR`)
3. Убедитесь, что префикс команды указан правильно (по умолчанию это `/`), проверьте раздел `[ErisPulse.event.command]` в конфигурационном файле
4. Убедитесь, что имя команды написано правильно, обратите внимание на настройки чувствительности к регистру

### Как изменить префикс команды?

Добавьте в `config.toml`:

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### Как поддержать несколько платформ?

ErisPulse использует стандарт OneBot12 для унификации формата событий на разных платформах, обработчики, зарегистрированные с помощью `@command` и `@message`, автоматически получают события со всех платформ. С помощью `event.get_platform()` можно определить источник платформы:

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Привет! Из Юньху")
    elif platform == "telegram":
        await event.reply("Hello! Из Telegram")
    else:
        await event.reply("Привет!")
```

> Подробнее о многоуровневой адаптации платформ см. в [Примерах распространённых задач](common-tasks.md#многоуровневая-адаптация-платформ).



### 基础概念

# Основные концепции

В этом руководстве представлены основные концепции ErisPulse, которые помогут вам понять дизайн-мышление и базовую архитектуру фреймворка.

## Архитектура на основе событий

ErisPulse использует архитектуру на основе событий, где все взаимодействия передаются и обрабатываются через события.

### Поток событий

```
Пользователь отправляет сообщение
      │
      ▼
Платформа получает
      │
      ▼
Адаптер получает нативное событие платформы
      │
      ▼
Преобразуется в стандартное событие OneBot12
      │
      ▼
Отправляется в систему событий
      │
      ▼
Распределяется зарегистрированным обработчикам
      │
      ▼
Модуль обрабатывает событие
      │
      ▼
Адаптер отправляет ответ
      │
      ▼
Платформа отображает пользователю
```

### Стандарт OneBot12

ErisPulse использует OneBot12 в качестве стандартного события. OneBot12 — это стандарт универсального интерфейса чат-бота, определяющий унифицированный формат событий.

Все адаптеры преобразуют событие, специфичное для платформы, в формат OneBot12, обеспечивая согласованность кода.

## Основные компоненты

### 1. Объект SDK

SDK является точкой входа для всех функций и предоставляет доступ к основным компонентам.

```python
from ErisPulse import sdk

# Доступ к основным модулям
sdk.storage    # Система хранения
sdk.config     # Система конфигурации
sdk.logger     # Система логирования
sdk.adapter    # Система адаптеров
sdk.module     # Система модулей
sdk.router     # Система маршрутизации
sdk.client     # HTTP клиент
sdk.lifecycle  # Система жизненного цикла
```

### 2. Объект Event

Объект Event инкапсулирует данные о событии и предоставляет удобные методы доступа.

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

Адаптер — это мост между ErisPulse и внешними платформами.

**Обязанности:**
- Получение нативных событий платформы
- Преобразование в стандартный формат OneBot12
- Отправка стандартных событий платформе

**Примеры адаптеров:**
- Адаптер Yunhu: общение с платформой Yunhu
- Адаптер Telegram: общение с Telegram Bot API
- Адаптер OneBot11: общение с приложениями, совместимыми с OneBot11
- Адаптер Email: обработка почтовых сообщений

### 4. Модуль

Модуль — это базовая единица расширения функциональности, которая может:

- Регистрировать обработчики событий
- Реализовывать бизнес-логику
- Вызывать адаптеры для отправки сообщений
- Использовать службы, предоставляемые основными модулями

#### Механизм обнаружения модулей

ErisPulse обнаруживает установленные модули через Python `importlib.metadata.entry_points`. Модули объявляют точки входа в `pyproject.toml`:

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

При инициализации SDK сканируются все точки входа группы `erispulse.module`, классы модулей регистрируются в `ModuleManager`, а затем последовательно инициализируются после топологической сортировки по зависимостям.

#### Минимально рабочий модуль

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("Модуль загружен")

    async def on_unload(self, event):
        self.logger.info("Модуль выгружен")
```

#### Жизненный цикл модуля

- **Регистрация**: SDK обнаруживает класс модуля и регистрирует его в менеджере
- **Загрузка**: Создается экземпляр модуля, вызывается `on_load(event)` (`event = {"module_name": "MyModule"}`)
- **Выгрузка**: Вызывается `on_unload(event)`, ресурсы очищаются

#### Стратегия загрузки

Загрузочное поведение модуля определяется через `get_load_strategy()`:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # Ленивая загрузка (по умолчанию True)
            priority=0        # Приоритет загрузки, чем больше значение, тем раньше инициализация
        )
```

- **`lazy_load=True` (по умолчанию)**: Модуль инициализируется только при первом обращении к `sdk.MyModule`, что снижает время запуска
- **`lazy_load=False`**: Модуль инициализируется сразу при запуске SDK, подходит для модулей, которым нужно прослушивать события жизненного цикла или выполнять фоновые задачи
- **`priority`**: Модули с одинаковым приоритетом загружаются в порядке регистрации; чем больше значение, тем раньше инициализация

> Подробное описание механизма ленивой загрузки см. в разделе [Система ленивой загрузки](../advanced/lazy-loading.md).

## Типы событий

ErisPulse поддерживает 5 типов событий:

| Тип события | Декоратор | Описание |
|------------|-----------|---------|
| Событие сообщения | `@message.on_message()` | Любое сообщение, отправленное пользователем (личные сообщения, чаты) |
| Событие команды | `@command("name")` | Сообщения, начинающиеся с префикса команды (например, `/hello`) |
| Событие уведомления | `@notice.on_friend_add()` и т.д. | Системные уведомления (добавление друга, изменения состава группы и т.д.) |
| Событие запроса | `@request.on_friend_request()` и т.д. | Запросы пользователей (запросы на добавление в друзья, приглашения в группу) |
| Метасобытие | `@meta.on_connect()` и т.д. | Системные события (подключение, отключение, пульс) |

> Подробное использование и примеры кода для каждого типа событий см. в разделе [Введение в обработку событий](event-handling.md).

## Описание основных модулей

### Storage (Хранилище)

Базирующаяся на SQLite система хранения пар ключ-значение для персистентного хранения данных.

```python
# Установка значения
sdk.storage.set("key", "value")

# Получение значения
value = sdk.storage.get("key", "default_value")

# Массовые операции
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
# Запись логов
sdk.logger.info("Это информационное сообщение")
sdk.logger.warning("Это предупреждение")
sdk.logger.error("Это ошибка")

# Получение дочернего логгера
child_logger = sdk.logger.get_child("submodule")
child_logger.info("Лог дочернего модуля")
```

**Синтаксический сахар для доступа к свойствам**

Помимо использования метода `get_child()`, вы также можете создавать дочерние логгеры через **доступ к свойствам**, что является более кратким способом записи **синтаксического сахара**:

```python
# Создание дочернего логгера через доступ к свойствам
sdk.logger.mymodule.info("Сообщение модуля")

# Поддержка вложенного доступа
sdk.logger.mymodule.database.info("Сообщение базы данных")
```

### Router (Маршрутизация)

Управление HTTP и WebSocket маршрутизацией на базе FastAPI + Uvicorn. Поддерживает декораторную маршрутизацию, middleware, группирование, лимитирование запросов, CORS.

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> Полный API маршрутизации (WebSocket, middleware, лимитирование запросов, CORS и т.д.) см. в разделе [Менеджер маршрутизации](../advanced/router.md).

### Client (Сетевой клиент)

Единый сетевой клиент, объединяющий HTTP-запросы, WebSocket-соединения, управление пулом соединений, автоматическую перезагрузку, контроль тайм-аута, статистику запросов и интеграцию событий жизненного цикла.

```python
from ErisPulse.Core import client

# HTTP запрос
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# С перезагрузкой и тайм-аутом
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket соединение
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Эхо: {text}")
```

> Полный API сетевого клиента см. в разделе [Сетевой клиент](../advanced/http-client.md).

## Отправка сообщений SendDSL

Адаптеры предоставляют интерфейс для отправки сообщений с цепочечными вызовами.

### Базовая отправка

```python
# Получение экземпляра адаптера
yunhu = sdk.adapter.get("yunhu")

# Отправка сообщения
await yunhu.Send.To("user", "U1001").Text("Hello")

# Указание аккаунта отправки
await yunhu.Send.Using("bot1").To("group", "G1001").Text("Сообщение группы")
```

### Цепочечные модификаторы

```python
# @Пользователь
await yunhu.Send.To("group", "G1001").At("U2001").Text("@сообщение")

# Ответ на сообщение
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("ответ")

# @Всех
await yunhu.Send.To("group", "G1001").AtAll().Text("объявление")
```

### Методы ответа через Event

Объект Event предоставляет удобные методы для ответов:

```python
@command("test")
async def test_handler(event):
    # Простой текстовый ответ
    await event.reply("Текст ответа")
    
    # Отправка изображения
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # Отправка голосового
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## Система ленивой загрузки

По умолчанию ErisPulse включает ленивую загрузку модулей; модули инициализируются только при первом обращении (например, `sdk.MyModule`), что значительно ускоряет запуск.

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # Включить ленивую загрузку (по умолчанию)
            priority=0        # Приоритет загрузки, чем больше значение, тем раньше инициализация
        )
```

**Сценарии, когда необходимо отключить ленивую загрузку (`lazy_load=False`):**
- Модули, прослушивающие события жизненного цикла (например, `core.init.complete`)
- Модули, запускающие периодические задачи или фоновые службы
- Модули, которым необходимо завершить инициализацию до загрузки других модулей

> Подробное описание механизма ленивой загрузки и рекомендации см. в разделе [Система ленивой загрузки](../advanced/lazy-loading.md).

## Дальнейшие шаги

- [Введение в обработку событий](event-handling.md) — изучите, как обрабатывать различные типы событий
- [Примеры типичных задач](common-tasks.md) — освоите реализацию распространенных функций



### 事件处理入门

# Введение в обработку событий

В этом руководстве рассказывается о том, как обрабатывать различные типы событий в ErisPulse.

## Обзор типов событий

ErisPulse поддерживает следующие типы событий:

| Тип события | Описание | Сценарии использования |
|---------|------|---------|
| Событие сообщения | Любое сообщение, отправленное пользователем | Чат-боты, фильтрация контента |
| Событие команды | Сообщение, начинающееся с префикса команды | Обработка команд, точка входа |
| Событие уведомления | Системные уведомления (добавление друзей, изменение участников группы и т.д.) | Приветствия, уведомления о состоянии |
| Событие запроса | Запросы пользователей (запросы на добавление в друзья, приглашения в группу) | Автоматическая обработка запросов |
| Мета-событие | Системные события (подключение, heartbeat) | Мониторинг подключения, проверка состояния |

## Обработка событий сообщений

> **Примечание**: Рекомендуется использовать аннотацию типа `Event` в обработчиках событий для поддержки автодополнения и проверки типов в IDE.

```python
from ErisPulse.Core.Event import Event  # Импорт типа события для аннотации
```

### Отслеживание всех сообщений

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"Получено сообщение от {user_id}: {text}")
```

### Отслеживание личных сообщений

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"Привет, {user_id}! Это личное сообщение.")
```

### Отслеживание групповых сообщений

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Пользователь {user_id} отправил сообщение в группу {group_id}")
```

### Отслеживание сообщений с упоминанием (@)

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Получение списка упомянутых пользователей
    mentions = event.get_mentions()
    await event.reply(f"Вы упомянули этих пользователей: {mentions}")
```

## Обработка командных событий

### Базовая команда

```python
from ErisPulse.Core.Event import command

@command("help", help="Показать справочную информацию")
async def help_handler(event):
    help_text = """
Доступные команды:
/help - Показать справку
/ping - Проверить соединение
/info - Просмотр информации
    """
    await event.reply(help_text)
```

### Псевдонимы команд

```python
@command(["help", "h"], aliases=["помощь"], help="Показать справочную информацию")
async def help_handler(event):
    await event.reply("Справочная информация...")
```

Пользователь может вызвать команду любым из следующих способов:
- `/help`
- `/h`
- `/помощь`

### Командные аргументы

```python
@command("echo", help="Отправить сообщение обратно")
async def echo_handler(event):
    # Получение аргументов команды
    args = event.get_command_args()
    
    if not args:
        await event.reply("Введите сообщение для повторения")
    else:
        await event.reply(f"Вы сказали: {' '.join(args)}")
```

### Группы команд

```python
@command("admin.reload", group="admin", help="Перезагрузить модуль")
async def reload_handler(event):
    await event.reply("Модуль перезагружен")

@command("admin.stop", group="admin", help="Остановить бота")
async def stop_handler(event):
    await event.reply("Бот остановлен")
```

### Командные права доступа

```python
def is_master(event):
    """Проверка, является ли пользователь владельцем фреймворка"""
    master_list = ["user123", "user456"]
    return event.get_user_id() in master_list

@command("master", permission=is_master, help="Команда владельца фреймворка")
async def master_handler(event):
    await event.reply("Это команда владельца фреймворка")
```

### Приоритет команд

```python
# Чем больше значение приоритета, тем раньше выполнится
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("Обработчик с высоким приоритетом")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Обработчик с низким приоритетом")
```

### Параллельная обработка событий

Система событий ErisPulse использует модель планирования **параллельной обработки с одинаковым приоритетом и последовательной обработки с разным приоритетом**:

```
Событие поступило
    ↓
Группа priority=10: [Обработчик C || Обработчик D] параллельно → Объединение результатов
    ↓ (если не прервано)
Группа priority=0: [Обработчик A || Обработчик B] параллельно → Объединение результатов
    ↓
...
```

- **Параллельная обработка с одинаковым приоритетом**: Обработчики с одинаковым приоритетом выполняются одновременно, что повышает пропускную способность.
- **Последовательная обработка с разным приоритетом**: Группы с разным приоритетом выполняются последовательно (чем больше значение, тем раньше выполняется), обеспечивая выполнение обработчиков с высоким приоритетом первыми.
- **Copy-On-Write**: Обработчики не создают копии, если не вносят изменения, что обеспечивает нулевой накладной расход.
- **Обработка конфликтов**: При модификации одного и того же поля несколькими обработчиками с одинаковым приоритетом используется последнее значение и записывается предупреждение в лог.
- **Механизм прерывания**: После вызова `event.mark_processed()` любым обработчиком пропускаются последующие группы с более низким приоритетом.

```python
# Пример: параллельное выполнение обработчиков с одинаковым приоритетом
@message.on_message(priority=0)
async def handler_a(event):
    # Обработка задачи A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # Выполняется параллельно с handler_a
    event['result_b'] = process_b()

# Последовательное выполнение обработчиков с разным приоритетом
@message.on_message(priority=10)
async def handler_c(event):
    # Самый высокий приоритет, выполняется первым
    pass
```

## Обработка событий уведомлений

### Добавление друга

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "Новый друг"
    await event.reply(f"Добро пожаловать, {nickname}! Добавлены в друзья.")
```

### Увеличение числа участников группы

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать, {user_id}, в группу {group_id}")
```

### Уменьшение числа участников группы

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Пользователь {user_id} покинул группу {group_id}")
```

## Обработка событий запросов

### Запрос на добавление в друзья

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Получен запрос на добавление в друзья: {user_id}, комментарий: {comment}")
    
    # Можно обработать запрос через API адаптера
    # Конкретная реализация см. в документации каждого адаптера
```

### Запрос на приглашение в группу

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Получено приглашение в группу {group_id} от {user_id}")
```

## Обработка мета-событий

### События подключения

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"Подключение к платформе {platform}")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"Отключение от платформы {platform}")
```

### События heartbeat

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"Проверка работоспособности платформы {platform}")
```

### Запрос состояния бота

После отправки мета-события адаптером фреймворк автоматически отслеживает состояние бота, и вы можете в любой момент запросить его:

```python
from ErisPulse import sdk

# Проверка, онлайн ли бот
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Бот онлайн")

# Вывод всех онлайн ботов
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Получение полной сводки состояния
summary = sdk.adapter.get_status_summary()
```

## Интерактивная обработка

### Использование метода reply для отправки ответа

Метод `event.reply()` поддерживает различные параметры для удобной отправки сообщений с упоминаниями, ответами и т.д.:

```python
# Простой ответ
await event.reply("Привет")

# Отправка различных типов сообщений
await event.reply("http://example.com/image.jpg", method="Image")  # Изображение
await event.reply("http://example.com/voice.mp3", method="Voice")  # Голосовое сообщение

# Упоминание одного пользователя
await event.reply("Привет", at_users=["user123"])

# Упоминание нескольких пользователей
await event.reply("Привет всем", at_users=["user1", "user2", "user3"])

# Ответ на сообщение
await event.reply("Содержание ответа", reply_to="msg_id")

# Упоминание всех участников
await event.reply("Объявление", at_all=True)

# Комбинированный вариант: упоминание пользователя + ответ на сообщение
await event.reply("Содержание", at_users=["user1"], reply_to="msg_id")
```

### Ожидание ответа пользователя

```python
@command("ask", help="Запросить имя пользователя")
async def ask_handler(event):
    await event.reply("Введите ваше имя:")
    
    # Ожидание ответа пользователя, таймаут 30 секунд
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")
    else:
        await event.reply("Таймаут ожидания, пожалуйста, повторите ввод.")
```

### Ожидание ответа с проверкой

```python
@command("age", help="Запросить возраст")
async def age_handler(event):
    def validate_age(event_data):
        """Проверка корректности возраста"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("Введите ваш возраст (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"Ваш возраст: {age} лет")
    else:
        await event.reply("Некорректный ввод или превышен таймаут")
```

### Ожидание ответа с обратным вызовом

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["yes", "y", "да", "д"]:
            await event.reply("Действие подтверждено!")
        else:
            await event.reply("Действие отменено.")
    
    await event.reply("Подтвердите выполнение действия? (да/нет)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Подтверждение диалога (confirm)

Ожидание подтверждения или отрицания от пользователя, автоматически распознаются встроенные слова подтверждения на китайском и английском языках:

```python
@command("confirm", help="Подтвердить действие")
async def confirm_handler(event):
    if await event.confirm("Вы уверены, что хотите выполнить это действие?"):
        await event.reply("Подтверждено, выполняется...")
    else:
        await event.reply("Отменено")

# Пользовательские слова подтверждения
if await event.confirm("Продолжить?", yes_words={"go", "продолжить"}, no_words={"stop", "остановить"}):
    pass
```

### Выбор из меню (choose)

Пользователь может ответить номером или текстом опции:

```python
@command("choose", help="Выбор цвета")
async def choose_handler(event):
    choice = await event.choose(
        "Выберите цвет:",
        ["красный", "зеленый", "синий"]
    )
    
    if choice is not None:
        colors = ["красный", "зеленый", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
    else:
        await event.reply("Таймаут выбора")
```

**Режим объединения**: При `merge_prompt=True` опции добавляются в текст сообщения и отправляются одним сообщением с указанным `method`:

```python
# Отправка объединенного сообщения в формате Markdown
choice = await event.choose(
    "## Выберите цвет\n{options}\nОтветьте номером",
    ["красный", "зеленый", "синий"],
    method="Markdown",
    merge_prompt=True,
)
```

> Заполнитель `{options}` управляет позицией вставки опций; если не указан, опции добавляются в конец текста.  
> Позицию можно изменить с помощью параметра `placeholder` (например, `placeholder="[выборы]"`).  
> Параметр `options_format="auto"` (по умолчанию) автоматически выбирает стиль в зависимости от `method`: Markdown→неупорядоченный список, Html→упорядоченный список, другие→простой текстовый список.  
> Для текстовых методов (Text/Markdown/Html и т.д.) опции по умолчанию добавляются в конец сообщения; для не-текстовых методов (Image и т.д.) по умолчанию отправляются два сообщения.

### Сбор формы (collect)

Сбор данных пользователя по шагам:

```python
@command("register", help="Регистрация")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "Введите имя:"},
        {"key": "age", "prompt": "Введите возраст:", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "Введите email:"}
    ])
    
    if data:
        await event.reply(f"Регистрация успешна!\nИмя: {data['name']}\nВозраст: {data['age']}\nEmail: {data['email']}")
    else:
        await event.reply("Таймаут регистрации или некорректный ввод")
```

### Ожидание произвольного события (wait_for)

Ожидание события, соответствующего заданным условиям, независимо от пользователя:

```python
@command("wait_member", help="Ожидание нового участника")
async def wait_member_handler(event):
    await event.reply("Ожидание участника в группу...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Добро пожаловать, {evt.get_user_id()}!")
    else:
        await event.reply("Таймаут ожидания")
```

### Многошаговый диалог (conversation)

Создание интерактивного многошагового диалога:

```python
@command("survey", help="Опрос")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Добро пожаловать в опрос!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Диалог завершен по таймауту, до свидания!")
            break
        
        text = reply.get_text()
        
        if text == "выход":
            await conv.say("До свидания!")
            break
        
        await conv.say(f"Вы сказали: {text}, продолжайте ввод или ответьте 'выход' для завершения")
```

### Встроенные слова подтверждения

ErisPulse включает в себя набор встроенных слов подтверждения на китайском и английском языках:

- **Слова подтверждения** (`CONFIRM_YES_WORDS`): да, yes, y, подтвердить, согласиться, хорошо, ok, true, верно, хорошо, согласен, нормально, и т.д.
- **Слова отрицания** (`CONFIRM_NO_WORDS`): нет, no, n, отменить, не, не надо, не могу, cancel, false, неверно, отказать, нельзя, и т.д.

## Доступ к данным события

### Часто используемые методы объекта Event

```python
@command("info")
async def info_handler(event):
    # Основная информация
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # Информация об отправителе
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # Содержание сообщения
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # Информация о группе
    group_id = event.get_group_id()
    
    # Информация о боте
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # Исходные данные
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # Информация о платформе
    platform = event.get_platform()
    
    # Проверка типа сообщения
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Информация о команде
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Платформенные расширения

Помимо встроенных методов, адаптеры платформ также регистрируют платформенно-специфические методы, что позволяет получить доступ к платформенно-специфическим данным.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов платформенно-специфических методов
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Специфичный для Telegram метод
    elif platform == "email":
        subject = event.get_subject()           # Специфичный для email метод
```

Если вы не уверены, зарегистрирован ли метод для платформы, вы можете запросить список зарегистрированных методов:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> Список платформенно-специфических методов см. в соответствующей [документации платформы](../platform-guide/).

## Лучшие практики обработки событий

### 1. Обработка исключений

```python
@command("process")
async def process_handler(event):
    try:
        # бизнес-логика
        result = await do_some_work()
        await event.reply(f"Результат: {result}")
    except ValueError as e:
        # ожидаемые ошибки бизнес-логики
        await event.reply(f"Ошибка параметра: {e}")
    except Exception as e:
        # неожиданные ошибки
        sdk.logger.error(f"Обработка не удалась: {e}")
        await event.reply("Обработка не удалась, попробуйте позже")
```

### 2. Запись логов

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"Обработка сообщения: {user_id} - {text}")
    
    # Использование логгера модуля
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Детальная отладочная информация")
```

### 3. Условная обработка

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Условная обработка - проверка внутри обработчика"""
    # Обрабатываем только сообщения от определенных пользователей
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Обрабатываем только сообщения с определенным ключевым словом
    if "ключевое_слово" not in event.get_text():
        return
    
    await event.reply("Условие выполнено, обработка сообщения")
```



### IDE 补全

# Генерация типовых заглушек (автодополнение в IDE)

ErisPulse использует entry-points для динамического обнаружения модулей/адаптеров, и типы пользовательских классов не могут быть известны на статическом уровне.
Команда `epsdk types` сканирует установленные модули/адаптеры и генерирует файл с типовыми заглушками, позволяя использовать эти типы для аннотации переменных и получать автодополнение в IDE.

## Основные принципы проектирования

Заглушечный файл **экспортирует только типы**, не предоставляя никаких экземпляров во время выполнения:

- Все импорты находятся внутри ``TYPE_CHECKING``, **без дополнительных накладных расходов во время выполнения, без изменения поведения**
- Имена типов используются в формате PascalCase, основанном на имени entry-point (например, ``yunhu`` → ``Yunhu``), что соответствует именам, передаваемым в ``sdk.adapter.get()`` / ``sdk.module.get()``
- Пользователи по-прежнему используют ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` для получения экземпляров, просто используя импортированные типы для **аннотации переменных**

## Основное использование

Запустите в корневой директории проекта:

```bash
epsdk types
```

В текущей директории будет создан файл `_ep_types.py`, содержащий типы всех установленных модулей/адаптеров.

## Использование в коде

```python
from _ep_types import MyModule, Yunhu
from ErisPulse import sdk

# Используя импортированные типы для аннотации переменных, можно получить автодополнение методов этого класса
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← Автодополнение hello

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← Автодополнение методов, специфичных для платформы
```

## Рабочий процесс

1. Сканирование entry-points `erispulse.adapter` / `erispulse.module`
2. Инспекция с помощью подпроцесса в целевой среде Python для сбора фактической информации о классах каждого адаптера/модуля (включая путь к модулю и полное имя)
3. Генерация `.py` файла, в котором:
   - Все ``from xxx import Yyy as Zzz`` находятся внутри ``TYPE_CHECKING``
   - ``Zzz`` — это имя entry-point в формате PascalCase
4. IDE читает раздел ``TYPE_CHECKING`` для предоставления автодополнения; во время выполнения никакой код не выполняется

Пример сгенерированной заглушки:

```python
# _ep_types.py (сгенерирован автоматически)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Адаптеры
    from MyAdapter.Core import MyAdapter as MyAdapter
    from YunhuAdapter.Core import YunhuAdapter as Yunhu

    # Модули
    from MyModule.Core import Main as MyModule

    __all__ = ['MyAdapter', 'Yunhu', 'MyModule']
```

## Опции команды

| Опция | Описание |
|------|------|
| `-o, --output PATH` | Указывает путь к выходному файлу (по умолчанию `./_ep_types.py`) |
| `--force` | Перезаписывает существующий файл с заглушками |
| `--adapters-only` | Сканирует только адаптеры |
| `--modules-only` | Сканирует только модули |

## Когда перегенерировать

- После установки/удаления новых модулей или адаптеров
- После обновления публичного API модуля/адаптера
- Когда автодополнение в IDE перестает работать или типы устарели

## Связь с методами SendDSL

Базовый класс `SendDSL` уже содержит стандартные методы отправки (Text/Image/Voice/Video/File), и любой экземпляр SendDSL, полученный любым способом, может использовать эти методы. Команда `types` используется для автодополнения **методов, специфичных для платформы** (например, `Board` в Yunhu, `Dice` в Sandbox) и **методов, специфичных для модуля**.



====
模块开发
====


### 模块开发入门

# Основы разработки модулей

Это руководство проведет вас через процесс создания модуля ErisPulse с нуля.

## Структура проекта

Стандартная структура модуля:

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py
```

## Конфигурация pyproject.toml

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Описание функций модуля"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = []

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

## __init__.py

```python
from .Core import Main
```

## Core.py - Основной модуль

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self.config = self._load_config()
    
    @staticmethod
    def get_load_strategy():
        """Возвращает стратегию загрузки модуля"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[]  # Необязательно: список зависимых модулей
        )
    
    async def on_load(self, event):
        """Вызывается при загрузке модуля"""
        @command("hello", help="Отправляет приветствие")
        async def hello_command(event):
            name = event.get_user_nickname() or "друг"
            await event.reply(f"Привет, {name}!")
        
        self.logger.info("Модуль загружен")
    
    async def on_unload(self, event):
        """Вызывается при выгрузке модуля"""
        self.logger.info("Модуль выгружен")
    
    def _load_config(self):
        """Загружает конфигурацию модуля"""
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = {
                "api_url": "https://api.example.com",
                "timeout": 30
            }
            self.sdk.config.setConfig("MyModule", default_config)
            return default_config
        return config
```

## Тестирование модуля

### Локальное тестирование

```bash
# Установить модуль в текущую директорию проекта
epsdk install ./MyModule

# Запустить проект
epsdk run main.py --reload
```

### Тестовая команда

Отправьте команду для тестирования:

```
/hello
```

## Основные понятия

### Базовый класс BaseModule

Все модули должны наследовать `BaseModule`, предоставляя следующие методы:

| Метод | Описание | Обязательно |
|------|------|------|
| `__init__(self)` | Конструктор | Нет |
| `get_load_strategy()` | Возвращает стратегию загрузки | Нет |
| `on_load(self, event)` | Вызывается при загрузке модуля | Да |
| `on_unload(self, event)` | Вызывается при выгрузке модуля | Да |

### Объект SDK

Доступ к основным функциям через объект `sdk`:

```python
from ErisPulse import sdk

sdk.storage    # Система хранения
sdk.config     # Система конфигурации
sdk.logger     # Система логирования
sdk.adapter    # Система адаптеров
sdk.router     # Система маршрутизации
sdk.lifecycle  # Система жизненного цикла
```

## Дальнейшие действия

- [Основные концепции модуля](core-concepts.md) - Глубокое погружение в архитектуру модуля
- [Подробное описание оберток событий](event-wrapper.md) - Изучение объектов Event
- [Лучшие практики разработки модулей](best-practices.md) - Разработка качественных модулей



### 模块核心概念

# Основные концепции модуля

Понимание основных концепций модуля ErisPulse является основой для разработки высококачественных модулей.

## Жизненный цикл модуля

### Стратегия загрузки

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """Возвращает стратегию загрузки модуля"""
        return ModuleLoadStrategy(
            lazy_load=True,   # отложенная или немедленная загрузка
            priority=0,       # приоритет загрузки (чем больше число, тем выше приоритет)
            depends=["OtherModule"]  # необязательно: объявление других модулей, от которых зависит текущий
        )
```

> Если модули, объявленные через `depends`, не зарегистрированы, текущий модуль будет пропущен, и будет выведено предупреждение. Порядок загрузки определяется топологической сортировкой, для модулей одного уровня — по убыванию `priority`.

### Метод on_load

Вызывается при загрузке модуля, используется для инициализации ресурсов и регистрации обработчиков событий:

```python
async def on_load(self, event):
    # Регистрация обработчика команд
    @command("hello", help="команда приветствия")
    async def hello_handler(event):
        await event.reply("Привет!")
    
    # Использование встроенного HTTP-клиента SDK (автоматическое управление пулом соединений, создание session вручную не требуется)
    # Запросы можно отправлять через sdk.client
```

### Метод on_unload

Вызывается при卸ождении модуля, используется для очистки ресурсов:

```python
async def on_unload(self, event):
    # Очистка пользовательских ресурсов
    # sdk.client управляется фреймворком, его закрытие вручную не требуется
    
    # Отмена обработчиков событий (фреймворк обрабатывает это автоматически)
    self.logger.info("Модуль был выгружен")

## Объект SDK

### Доступ к основным модулям

```python
from ErisPulse import sdk

# Доступ ко всем основным модулям через объект sdk
sdk.logger.info("Лог")
sdk.storage.set("key", "value")
config = sdk.config.getConfig("MyModule")
```

### Взаимодействие между модулями

```python
# Доступ к другим модулям
other_module = sdk.OtherModule
result = await other_module.some_method()

## Запрос методов отправки адаптера

В связи с тем, что новые стандартные спецификации требуют использования переопределения метода `__getattr__` для реализации механизма резервной отправки, использование метода `hasattr` для проверки существования метода становится невозможным. Начиная с версии `2.3.5`, добавлена функция для запроса методов отправки.

### Список поддерживаемых методов отправки

```python
# Список всех методов отправки, поддерживаемых платформой
methods = sdk.adapter.list_sends("onebot11")
# Возвращает: ["Text", "Image", "Voice", "Markdown", ...]
```

### Получение подробной информации о методе

```python
# Получение подробной информации о конкретном методе
info = sdk.adapter.send_info("onebot11", "Text")
# Возвращает:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "Отправка текстового сообщения..."
# }

## Управление конфигурацией

### Декларативная конфигурация (рекомендуется)

Начиная с версии v2.5.2, модули могут объявлять класс конфигурации через `ConfigClass`, используя ту же систему схем конфигурации, что и адаптеры. Конфигурация считывается в реальном времени через `self.cfg` и вступает в силу немедленно после изменения:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_module.api_key", "default": "API ключ"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )
    timeout: int = field(
        default=30,
        metadata={
            "description": {"i18n": "my_module.timeout", "default": "Время ожидания (сек)"},
            "ui": {"widget": "number", "group": "advanced", "order": 2},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def on_load(self, event):
        self.logger.info("Модуль загружен")

    async def on_unload(self, event):
        pass

    async def do_something(self):
        cfg = self.cfg  # Считывание в реальном времени, с проверкой типов
        api_key = cfg.api_key
        timeout = cfg.timeout
```

`BaseConfig` — это универсальный базовый класс конфигурации, который подходит для адаптеров, модулей, внешних проектов и любых других сценариев. Поля конфигурации поддерживают многоязычные описания i18n (см. [документацию i18n](../../advanced/i18n.md#配置字段多语言)).

### Декларативные ключи переводов (v2.7.0+)

Начиная с версии v2.7.0, модули также могут централизованно объявлять ключи переводов, используя вложенный класс `I18nClass`, подобно тому, как объявляют `ConfigClass`. Фреймворк автоматически **регистрирует** все объявленные ключи переводов при загрузке, не требуя ручного вызова `i18n.register()`, а момент регистрации наступает раньше генерации шаблонов конфигурации, что гарантирует доступность i18n-ключей, используемых в описаниях конфигурации.

```python
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey

class MyModule(BaseModule):
    # Класс конфигурации (необязательно)
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="欢迎",
            metadata={
                "description": {"i18n": "mymodule.welcome_msg", "default": "Приветственное сообщение"},
            },
        )

    # Класс набора ключей переводов (необязательно)
    class I18nClass(BaseI18n):
        # Имена атрибутов автоматически объединяются в полный путь ключа: <имя_модуля>.<имя_атрибута>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # Языко-независимое значение по умолчанию
            zh_CN="欢迎消息",
            zh_TW="歡迎訊息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
        )
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )
```

Подробнее см. [рекомендуемый подход i18n](../../advanced/i18n.md#推荐写法通过-i18nclass-声明翻译键-v270).

### Ручное чтение конфигурации (совместимый способ)

Если не используется декларативная конфигурация, можно напрямую считывать и записывать хранилище конфигурации:

```python
def _load_config(self):
    config = self.sdk.config.getConfig("MyModule")
    if not config:
        default_config = {
            "api_key": "",
            "timeout": 30
        }
        self.sdk.config.setConfig("MyModule", default_config)
        return default_config
    return config
```

> **Примечание**: При ручном способе избегайте использования `self.config` в качестве имени атрибута, рекомендуется использовать `self.cfg` или любое другое пользовательское имя, чтобы избежать конфликтов с будущими свойствами фреймворка.

## Система хранения

### Основное использование

```python
# Сохранение данных
sdk.storage.set("user:123", {"name": "Чжан Сань"})

# Получение данных
user = sdk.storage.get("user:123", {})

# Удаление данных
sdk.storage.delete("user:123")
```

### Использование транзакций

```python
# Использование транзакции для обеспечения целостности данных
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # Если какая-либо операция завершится неудачей, все изменения будут откачены

## Обработка событий

### Регистрация обработчиков событий

```python
from ErisPulse.Core.Event import command, message

# Регистрация команды
@command("info", help="Получить информацию")
async def info_handler(event):
    await event.reply("Это информация")

# Регистрация обработчика сообщений
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"Получено групповое сообщение: {event.get_text()}")
```

### Жизненный цикл обработчика событий

Фреймворк автоматически управляет регистрацией и отменой регистрации обработчиков событий; вам нужно зарегистрировать их только в `on_load`.

## Механизм ленивой загрузки

### Принцип работы

```python
# Инициализация модуля происходит только при первом обращении к нему
result = await sdk.my_module.some_method()
# ↑ Здесь срабатывает инициализация модуля
```

### Мгновенная загрузка

Для модулей, которые должны быть инициализированы немедленно (например, слушатели событий, таймеры):

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=False,  # Мгновенная загрузка
        priority=100
    )

## Обработка ошибок

### Перехват исключений

```python
async def handle_event(self, event):
    try:
        # Бизнес-логика
        await self.process_event(event)
    except ValueError as e:
        self.logger.warning(f"Ошибка параметров: {e}")
        await event.reply(f"Ошибка параметров: {e}")
    except Exception as e:
        self.logger.error(f"Сбой обработки: {e}")
        raise
```

### Логирование

```python
# Использование различных уровней логирования
self.logger.debug("Информация отладки")    # Детальная информация для отладки
self.logger.info("Статус работы")          # Информация о нормальном запуске
self.logger.warning("Предупреждение")     # Предупреждение
self.logger.error("Сообщение об ошибке")  # Сообщение об ошибке
self.logger.critical("Критическая ошибка") # Критическая ошибка

## Документация

- [Введение в разработку модулей](getting-started.md) — Создание первого модуля
- [Класс-обертка событий](event-wrapper.md) — Подробное описание обработки событий
- [Лучшие практики](best-practices.md) — Создание модулей высокого качества



### Event 包装类详解

# Подробное руководство по Event-обертке

Модуль Event предоставляет мощный Event-обертку, упрощающую обработку событий.

## Основные особенности

- **Полная совместимость с dict**: Event наследуется от dict
- **Удобные методы**: Предоставляется множество удобных методов
- **Доступ через точку**: Поддерживается доступ к полям события через точку
- **Обратная совместимость**: Все методы являются необязательными

## Основные методы полей

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, платформа: {platform}, время: {time}")
```

## Методы событий сообщений

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}!")
```

## Определение типа сообщения

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"Тип: {'личное сообщение' if is_private else 'группа'}")
```

## Функция ответа

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    await event.reply("Пожалуйста, введите ваше имя:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")
```

## Получение информации о команде

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"Команда: {cmd_name}, параметры: {cmd_args}")
```

## Методы событий уведомлений

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("Добро пожаловать в друзья!")
```

## Справочник методов

### Основные методы

#### Основная информация о событии
- `get_id()` - Получить ID события
- `get_time()` - Получить метку времени события (Unix, секунды)
- `get_type()` - Получить тип события (message/notice/request/meta)
- `get_detail_type()` - Получить подробный тип события (private/group/friend и т.д.)
- `get_platform()` - Получить название платформы

#### Информация о боте
- `get_self_platform()` - Получить название платформы бота
- `get_self_user_id()` - Получить ID пользователя бота
- `get_self_account_id()` - Получить ID аккаунта бота (режим с несколькими ботами)
- `get_self_info()` - Получить полную информацию о боте в виде словаря

#### Идентификатор сессии
- `get_target_id()` - Получить единый ID цели (для групповых сообщений возвращает `group_id`, для каналов `channel_id`, для личных сообщений `user_id`, возвращает первый непустой элемент в порядке group → channel → guild → thread → user)
- `get_session_id()` - Получить уникальный идентификатор сессии, формат: `{platform}:{detail_type}:{target_id}`

### Методы событий сообщений

#### Содержимое сообщения
- `get_message()` - Получить массив сегментов сообщения (формат OneBot12)
- `get_alt_message()` - Получить запасной текст сообщения
- `get_text()` - Получить чистый текст (псевдоним `get_alt_message()`)
- `get_message_text()` - Получить чистый текст (псевдоним `get_alt_message()`)

#### Информация об отправителе
- `get_user_id()` - Получить ID пользователя-отправителя
- `get_user_nickname()` - Получить никнейм отправителя
- `get_sender()` - Получить полную информацию об отправителе в виде словаря

#### Информация о группе/канале
- `get_group_id()` - Получить ID группы (для групповых сообщений)
- `get_channel_id()` - Получить ID канала (для сообщений канала)
- `get_guild_id()` - Получить ID сервера (для сообщений сервера)
- `get_thread_id()` - Получить ID темы/подканала (для сообщений темы)

#### Связанные с упоминаниями
- `has_mention()` - Содержит ли сообщение упоминание бота
- `get_mentions()` - Получить список ID всех упомянутых пользователей

### Определение типа сообщения

#### Основные проверки
- `is_message()` - Является ли событием сообщения
- `is_private_message()` - Является ли личным сообщением
- `is_group_message()` - Является ли групповым сообщением
- `is_at_message()` - Является ли сообщением с упоминанием (`has_mention()` псевдоним)

### Методы событий уведомлений

#### Информация об операторе
- `get_operator_id()` - Получить ID оператора
- `get_operator_nickname()` - Получить никнейм оператора

#### Определение типа уведомления
- `is_notice()` - Является ли событием уведомления
- `is_group_member_increase()` - Событие увеличения участников группы
- `is_group_member_decrease()` - Событие уменьшения участников группы
- `is_friend_add()` - Событие добавления друга (соответствует `detail_type == "friend_increase"`)
- `is_friend_delete()` - Событие удаления друга (соответствует `detail_type == "friend_decrease"`)

### Методы событий запросов

#### Информация о запросе
- `get_comment()` - Получить комментарий к запросу

#### Определение типа запроса
- `is_request()` - Является ли событием запроса
- `is_friend_request()` - Является ли запросом дружбы
- `is_group_request()` - Является ли запросом группы

### Функции ответа

#### Базовый ответ
- `reply(content, method="Text", at_sender=False, reply_to_message=False, at_users=None, reply_to=None, at_all=False, **kwargs)` - Общий метод ответа
  - `content`: Содержимое отправки (текст, URL и т.д.)
  - `method`: Метод отправки, по умолчанию "Text", можно выбрать "Image"/"Voice"/"Video"/"File" и т.д.
  - `at_sender`: Упоминать ли отправителя (автоматически извлекает user_id)
  - `quote`: Цитировать ли текущее сообщение (автоматически извлекает message_id)
  - `at_users`: Список упомянутых пользователей, например `["user1", "user2"]`
  - `reply_to`: Ручное указание ID сообщения для ответа
  - `at_all`: Упоминать ли всех участников
  - `**kwargs`: Дополнительные параметры (например, user_id для метода Mention)

- `reply_ob12(message)` - Ответ с использованием OneBot12 сегментов сообщения
  - `message`: Список или словарь сегментов OneBot12, можно использовать MessageBuilder для построения

#### Проверка поддержки платформой
- `supports(method)` - Проверить, поддерживает ли текущая платформа метод отправки (например, `"Image"`, `"Voice"`), возвращает `bool`
- `available_methods()` - Перечислить все доступные методы отправки на текущей платформе, возвращает список названий методов

#### Функция пересылки

> **Важно**: Функция пересылки должна реализовываться через DSL отправки адаптера, Event-обертка сама не предоставляет прямого метода пересылки.

```python
# Переслать сообщение в группу
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # или указать другой ID группы
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### Функция ожидания ответа

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text")` - Ожидать ответа пользователя
  - `prompt`: Подсказка, если указана, будет отправлена пользователю
  - `timeout`: Время ожидания (секунды), по умолчанию 60 секунд
  - `callback`: Функция-обратный вызов, выполняется при получении ответа
  - `validator`: Функция проверки, используется для проверки валидности ответа
  - `method`: Метод отправки подсказки, по умолчанию "Text"
  - Возвращает Event объект с ответом пользователя, при таймауте возвращает None

#### Интерактивные методы

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - Подтверждение диалога
  - Возвращает `True` (подтверждение) / `False` (отрицание) / `None` (таймаут)
  - Встроенные слова подтверждения на китайском и английском автоматически распознаются, можно настроить собственные наборы слов
  - `method`: Метод отправки, по умолчанию "Text"; поддерживает "Image"/"Markdown" и другие не-текстовые методы отправки подсказки
  - `hint`: Добавлять ли автоматически подсказку с словами подтверждения в конец подсказки (например, "（是/否）" ), по умолчанию False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - Меню выбора
  - `options`: Список текстов вариантов
  - Возвращает индекс варианта (0-based), при таймауте возвращает `None`
  - `method`: Метод отправки, по умолчанию "Text"; текстовые методы (Text/Markdown/md/Html/h5) по умолчанию объединяют варианты в конец
  - `options_format`: Формат вариантов (по умолчанию: "auto", автоматически выбирается встроенный стиль в зависимости от method)
    - `"auto"`: Markdown→неупорядоченный список (`- 1. вариант`), Html→упорядоченный список (`<ol>`), другие→простой текстовый список
    - `"list"`: Каждый вариант на отдельной строке, например ``1. ВариантA\n2. ВариантB``
    - `"inline"`: Варианты отображаются в одной строке, например ``1.A | 2.B``
    - `"md"`: Markdown неупорядоченный список
    - `"html"`: Html упорядоченный список
    - `callable`: Пользовательская функция, принимает ``list[str]`` и возвращает ``str``
  - `merge_prompt`: Принудительно объединять ли все в одно сообщение, по умолчанию False
    - `False` (по умолчанию): Текстовые методы объединяют автоматически; не-текстовые методы сначала отправляют prompt, затем Text варианты
    - `True`: Независимо от method объединяются в одно сообщение, отправляется с указанным method
  - `placeholder`: Заполнитель для вставки вариантов, по умолчанию `{options}`; текст с этим маркером заменяется на варианты, если установить пустую строку, варианты всегда добавляются в конец

- `collect(fields, timeout_per_field=60.0)` - Сбор формы
  - `fields`: Список полей, каждое поле содержит `key`, `prompt`, необязательный `validator`, необязательный `method`
  - Возвращает словарь `{key: value}`, при таймауте любого поля возвращает `None`
  - Каждое поле может иметь ключ `method`, указывающий метод отправки, например, при сборе изображения: `{"key": "avatar", "prompt": "Пожалуйста, отправьте аватарку", "method": "Image"}`
  - Каждое поле может иметь ключ `options` (список), при наличии этот пункт становится вопросом с выбором (автоматически вызывается choose логика)
  - Каждое поле может иметь ключи `options_format`, `merge_prompt`, `placeholder`, управляющие форматом вариантов, поведением объединения сообщений и заполнителем

- `wait_for(event_type="message", condition=None, timeout=60.0)` - Ожидать произвольного события
  - `condition`: Фильтрующая функция, возвращает `True` при совпадении
  - Возвращает Event объект с совпадающим событием, при таймауте возвращает `None`

- `conversation(timeout=60.0)` - Создать контекст многошагового диалога
  - Возвращает `Conversation` объект, поддерживающий `say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()`
  - Свойство `is_active` указывает, активен ли диалог

#### Примеры интерактивных методов

**confirm() - Подтверждение диалога:**

```python
@command("delete", help="Удалить данные")
async def delete_handler(event):
    if await event.confirm("Вы уверены, что хотите удалить все данные?"):
        sdk.storage.delete("all_data")
        await event.reply("Данные удалены")
    else:
        await event.reply("Отменено")
```

**confirm() - С подсказкой:**

```python
# hint=True добавит в конец подсказки "（是/否）"
if await event.confirm("Продолжить?", hint=True):
    await event.reply("Продолжено")
# Пользователь увидит: Продолжить?（是/否）
```

**choose() - Меню выбора:**

```python
@command("color", help="Выберите цвет")
async def color_handler(event):
    choice = await event.choose("Выберите цвет:", ["красный", "зеленый", "синий"])
    if choice is not None:
        colors = ["красный", "зеленый", "синий"]
        await event.reply(f"Вы выбрали: {colors[choice]}")
```

**choose() - Форматирование вариантов и объединение сообщений:**

```python
# inline формат: варианты отображаются в одной строке
choice = await event.choose("Выберите:", ["A", "B", "C"], options_format="inline")
# Вывод: 1.A | 2.B | 3.C

# Пользовательская функция форматирования
choice = await event.choose("Выберите:", ["кот", "собака"],
    options_format=lambda opts: " / ".join(opts))
# Вывод: кот / собака

# options_format="auto" (по умолчанию): автоматически выбирается встроенный стиль в зависимости от method
# Markdown → неупорядоченный список
choice = await event.choose(
    "## Выберите", ["кот", "собака"],
    method="Markdown",  # auto автоматически распознает как md список
)
# Вывод:
# ## Выберите
# - 1. кот
# - 2. собака

# Html → упорядоченный список
choice = await event.choose(
    "<h2>Выберите</h2>", ["кот", "собака"],
    method="Html", merge_prompt=True,  # auto автоматически распознает как html список
)
# Вывод:
# <h2>Выберите</h2>
# <ol><li>1. кот</li><li>2. собака</li></ol>

# Режим объединения + заполнитель
choice = await event.choose(
    "## Выберите\n{options}\nПожалуйста, ответьте номером",
    ["кот", "собака"],
    method="Markdown", merge_prompt=True,
)

# Пользовательский заполнитель
choice = await event.choose(
    "Выберите: [choices]",
    ["кот", "собака"],
    placeholder="[choices]",
)
```

**collect() - Сбор формы:**

```python
@command("register", help="Регистрация")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "Введите имя:"},
        {"key": "age", "prompt": "Введите возраст:",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"Регистрация успешна! {data['name']}, {data['age']} лет")
```

**reply с не-Text методами:**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("Посмотрите на это изображение:").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Полное использование многошагового диалога с помощью Conversation см. в [Conversation многошаговый диалог](../../advanced/conversation.md).

### Информация о команде

#### Основа команды
- `get_command_name()` - Получить имя команды
- `get_command_args()` - Получить список аргументов команды
- `get_command_raw()` - Получить исходный текст команды
- `get_command_info()` - Получить полную информацию о команде в виде словаря
- `is_command()` - Является ли событием команды

### Исходные данные

- `get_raw()` - Получить исходные данные события платформы
- `get_raw_type()` - Получить тип исходного события платформы

### Платформенные расширения

Адаптеры могут зарегистрировать платформенно-специфические методы для Event-обертки. Методы доступны только на Event-экземплярах соответствующей платформы, попытка доступа с других платформ вызывает `AttributeError`.

Платформенные методы через `Event.__getattribute__` имеют приоритет над встроенными методами, поэтому можно переопределить встроенные интерактивные методы, такие как `confirm`, `choose`, `collect`, `wait_reply`, предоставляя платформенно-специфические реализации (например, кнопки, карточки). Встроенная реализация экспортируется как `_builtin_*` функции для переопределения.

```python
# Почтовое событие - только почтовые методы
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ Возвращает "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram событие - только Telegram методы
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ Возвращает "private"
event.get_subject()      # ❌ AttributeError

# Встроенные методы всегда доступны
event.get_text()         # ✅ Любая платформа
event.reply("hi")        # ✅ Любая платформа
```

### Проверка зарегистрированных методов

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### Поддержка hasattr и dir

```python
hasattr(event, "get_subject")   # Возвращает True только если platform="email"
"get_subject" in dir(event)     # То же самое
```

### Кросс-платформенное расширение (шаблон)

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` в качестве названия платформы, зарегистрированные методы доступны на Event-экземплярах **всех платформ**. Подходит для функций, требующих кросс-платформенного повторного использования, таких как AI-диалоги, управление контекстом и т.д.

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self - экземпляр Event, можно получить доступ к данным события и встроенным методам
    await self.reply(f"AI: {prompt}")
```

После регистрации, любой обработчик событий на любой платформе может вызывать `event.ai_chat(...)`.

Приоритет методов (от высшего к низшему): платформенно-специфические методы → методы шаблона → встроенные методы → доступ через ключ словаря.

> Способ регистрации расширений адаптерами см. в [API системы событий - кросс-платформенное расширение шаблоном](../../api-reference/event-system.md#кросс-платформенное-расширение-шаблоном).



### 模块开发最佳实践

# Лучшие практики разработки модулей

В этом документе представлены рекомендации по разработке модулей ErisPulse.

请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。

再次提醒：如果文档包含语言切换行（各语言名称用 `` | `` 分隔的行），务必严格遵守上方第8条的格式要求，不要写出 ``[**Label**](file)`` 这类错误格式。

## Модульная архитектура

### 1. Принцип единой ответственности

Каждый модуль должен отвечать только за одну основную функцию:

```python
# Хороший дизайн: каждый модуль отвечает только за одну функцию
class WeatherModule(BaseModule):
    """Модуль запроса погоды"""
    pass

class NewsModule(BaseModule):
    """Модуль запроса новостей"""
    pass

# Плохой дизайн: один модуль отвечает за несколько несвязанных функций
class UtilityModule(BaseModule):
    """Содержит несколько функций: погода, новости, шутки и т.д."""
    pass
```

### 2. Правила именования модулей

```toml
[project]
name = "ErisPulse-ModuleName"  # Использовать префикс ErisPulse-
```

### 3. Четкое управление конфигурацией

Рекомендуется использовать декларативную конфигурацию (объект `ConfigClass` + базовый класс `BaseConfig`), что дает возможности, такие как безопасность типов, автоматическое создание шаблонов, поддержку форм на WebUI и др.:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_url: str = field(default="https://api.example.com", metadata={
        "description": {"i18n": "my_module.api_url", "default": "API адрес"},
    })
    timeout: int = field(default=30, metadata={
        "description": {"i18n": "my_module.timeout", "default": "Время ожидания (сек)"},
    })
    cache_ttl: int = field(default=3600, metadata={
        "description": {"i18n": "my_module.cache_ttl", "default": "Время жизни кэша (сек)"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # Безопасно для типов, чтение в реальном времени
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

Также можно продолжать использовать ручное управление чтением и записью конфигурации (см. [Основные концепции модуля](core-concepts.md#конфигурация) ).

### Декларативные ключи перевода (v2.7.0+)

Модуль может централизованно объявлять ключи перевода через класс `I18nClass`. Фреймворк автоматически регистрирует их в системе i18n, без необходимости вручную вызывать `i18n.register()`.

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # Ключи перевода бизнес-логики с плейсхолдерами
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="欢迎你，{name}！",
            zh_TW="歡迎你，{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # Переводы описаний полей конфигурации
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

Подробное описание см. в [документации i18n](../../advanced/i18n.md#рекомендуемый подход через-i18nclass-декларировать-ключи-перевода-v270).

## Асинхронное программирование

### 1. Использование асинхронной библиотеки

```python
# Рекомендуется использовать встроенный HTTP-клиент SDK (асинхронный, с автоматическими логами и статистикой)
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# Также можно использовать sdk.client (результат такой же)
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# Не следует импортировать aiohttp напрямую (неудобно для унифицированного управления в рамках фреймворка)
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# Не следует использовать requests (синхронный, блокирует цикл событий)
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # Блокирует цикл событий
```

### 2. Правильная асинхронная операция

```python
async def handle_command(self, event):
    # Используйте create_task для выполнения трудоемких операций на фоне
    task = asyncio.create_task(self._long_operation())
    
    # Если необходимо дождаться результата
    result = await task
```

### 3. Управление ресурсами

```python
async def on_load(self, event):
    # Клиент SDK уже автоматически управляет пулом соединений, создавать session вручную не нужно
    pass
    
async def on_unload(self, event):
    # Если необходимо использовать собственный клиент, не забудьте очистить ресурсы
    pass

## Обработка событий

### 1. Использование класса-обёртки Event

```python
# Удобный метод с использованием класса-обёртки Event
@command("info")
async def info_command(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"Привет, {nickname}!")

# Вместо прямого доступа к словарю
@command("info")
async def info_command(event):
    user_id = event["user_id"]  # менее наглядно, подвержено ошибкам
```

### 2. Оптимальное использование отложенной загрузки

```python
# Модули обработки команд должны загружаться немедленно
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Модули прослушивателей должны загружаться немедленно
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# Модули утилит подходят для отложенной загрузки
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

### 3. Регистрация обработчиков событий

```python
async def on_load(self, event):
    # Регистрация обработчиков событий в on_load
    @command("hello")
    async def hello_handler(event):
        await event.reply("Привет!")
    
    @message.on_group_message()
    async def group_handler(event):
        self.logger.info("Получено сообщение из группы")
    
    # Не нужно вручную отменять регистрацию, фреймворк обрабатывает это автоматически

## Обработка ошибок

### 1. Классификация и обработка исключений

```python
async def handle_event(self, event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # Ожидаемые бизнес-ошибки
        self.logger.warning(f"Бизнес-предупреждение: {e}")
        await event.reply(f"Ошибка параметров: {e}")
    except aiohttp.ClientError as e:
        # Сетевая ошибка (рекомендуется использовать sdk.client + ClientError)
        # Старый код, использующий напрямую aiohttp, по-прежнему будет работать,
        # но в новом коде рекомендуется использовать систему исключений ErisPulse.
        self.logger.error(f"Сетевая ошибка: {e}")
        await event.reply("Не удалось выполнить сетевой запрос, повторите попытку позже")
    except Exception as e:
        # Неожиданные ошибки
        self.logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        await event.reply("Ошибка обработки, свяжитесь с администратором")
        raise
```

### 2. Обработка таймаутов

```python
# Рекомендуется использовать встроенный клиент SDK (включает таймауты и перезапросы)
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"Таймаут запроса: {url}")
        raise

## Система хранения

### 1. Использование транзакций

```python
# Использование транзакций для обеспечения согласованности данных
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ Использование без транзакций может привести к несогласованности данных
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # Если здесь произойдет ошибка, вышеустановленные данные не смогут быть откачены
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. Пакетные операции

```python
# Использование пакетных операций для повышения производительности
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ Несколько вызовов неэффективны
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)

## Логирование

### 1. Рациональное использование уровней логирования

```python
# DEBUG: Подробная информация для отладки (только для разработки)
self.logger.debug(f"Входные параметры: {params}")

# INFO: Информация о нормальном функционировании
self.logger.info("Модуль загружен")
self.logger.info(f"Обработка запроса: {request_id}")

# WARNING: Предупреждения, не влияющие на основную функциональность
self.logger.warning(f"Параметр конфигурации {key} не задан, используется значение по умолчанию")
self.logger.warning("Медленный ответ API, возможно, требуется оптимизация")

# ERROR: Сообщения об ошибках
self.logger.error(f"Не удалось выполнить запрос API: {e}")
self.logger.error(f"Не удалось обработать событие: {e}", exc_info=True)

# CRITICAL: Критические ошибки, требующие немедленной обработки
self.logger.critical("Ошибка подключения к базе данных, бот не может работать корректно")
```

### 2. Структурированное логирование

```python
# Использование структурированного логирования для облегчения анализа
self.logger.info(f"Обработка запроса: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ Использование неструктурированного логирования
self.logger.info(f"Запрос обработан, от пользователя {user_id}, время: {duration} мс")

## Оптимизация производительности

### 1. Использование кэша

```python
class MyModule(BaseModule):
    def __init__(self):
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_data(self, key):
        async with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            
            # Получение данных из базы данных
            data = await self._fetch_from_db(key)
            
            # Кэширование данных
            self._cache[key] = data
            return data
```

### 2. Избегание блокирующих операций

```python
# Использование асинхронных операций
async def process_message(self, event):
    # Асинхронная обработка
    await self._async_process(event)

# ❌ Блокирующая операция
async def process_message(self, event):
    # Синхронная операция, блокирует цикл событий
    result = self._sync_process(event)

## Безопасность

### 1. Защита чувствительных данных

```python
# Чувствительные данные хранятся в конфигурации
class MyModule(BaseModule):
    def _load_config(self):
        config = self.sdk.config.getConfig("MyModule")
        self.api_key = config.get("api_key")
        
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("Укажите действующий API-ключ в config.toml")

# ❌ Жесткое кодирование чувствительных данных
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # Не делайте так!
```

### 2. Валидация входных данных

```python
# Проверка пользовательского ввода
async def process_command(self, event):
    user_input = event.get_text()
    
    # Проверка длины ввода
    if len(user_input) > 1000:
        await event.reply("Слишком длинный ввод, пожалуйста, введите заново")
        return
    
    # Проверка формата ввода
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("Неверный формат ввода")
        return

## Тестирование

### 1. Unit Tests

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_load_config(self):
        """Тестирование загрузки конфигурации"""
        module = MyModule()
        config = module._load_config()
        assert config is not None
        assert "api_url" in config
```

### 2. Интеграционные тесты

```python
@pytest.mark.asyncio
async def test_command_handling():
    """Тестирование обработки команд"""
    module = MyModule()
    await module.on_load({})
    
    # Симуляция события команды
    event = create_test_command_event("hello")
    await module.handle_command(event)

## Развертывание

### 1. Управление версиями

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

Соблюдение семантического версионирования:
- MAJOR.MINOR.PATCH
- MAJOR (основная версия): несовместимые изменения API
- MINOR (дополнительная версия): новые возможности, совместимые с предыдущими версиями
- PATCH (исправление версии): исправления ошибок, совместимые с предыдущими версиями

### 2. Заголовок README

`epsdk create` генерирует README с встроенной идентификацией ErisPulse (Logo + полоса бейджей). Два рекомендуемых режима:

**Режим A — только ErisPulse Logo (по умолчанию):**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**Краткое описание**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**Режим B — значок модуля × ErisPulse Logo (при наличии пользовательского значка):**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
(полоса бейджей аналогична выше)
</div>
```

При необходимости можно добавить бейджи GitHub Stars, Downloads и т.д. Логотип также можно скачать в локальную папку проекта (`.github/assets/ErisPulseLogo.png`) и ссылаться через относительный путь.

Пожалуйста, верните полный перевод Markdown, не добавляя ничего лишнего.

Напоминаю: если в документе есть строки переключения языков (строки с названиями языков, разделёнными символом `|`), строго следуйте формату, указанному в пункте 8 выше, и не используйте неверный формат `[[**Label**](file)]`.



=====
发布与工具
=====


### 发布模块到模块商店

# Руководство по публикации и магазину модулей

Опубликуйте свой модуль или адаптер в магазине модулей ErisPulse, чтобы другие пользователи могли легко находить и устанавливать его.

## Обзор магазина модулей

Магазин модулей ErisPulse представляет собой централизованный реестр модулей, через который пользователи могут просматривать, искать и устанавливать модули и адаптеры, предоставленные сообществом, с помощью инструментов командной строки.

### Просмотр и обнаружение

```bash
# Вывести список всех доступных удалённых пакетов
epsdk list-remote

# Показать только модули
epsdk list-remote -t modules

# Показать только адаптеры
epsdk list-remote -t adapters

# Принудительно обновить список удалённых пакетов
epsdk list-remote -r
```

Вы также можете посетить [официальный сайт ErisPulse](https://www.erisdev.com/#market), чтобы просматривать магазин модулей онлайн.

### Поддерживаемые типы публикаций

| Тип | Описание | Группа entry-point |
|------|------|----------------|
| Модуль (Module) | Расширение функциональности бота, реализация бизнес-логики | `erispulse.module` |
| Адаптер (Adapter) | Подключение к новым платформам сообщений | `erispulse.adapter` |

## Быстрая публикация

Весь процесс состоит всего из трёх шагов: настройка проекта → публикация на PyPI → отправка в магазин модулей.

### 1. Настройка pyproject.toml

Убедитесь, что в каталоге проекта присутствуют `pyproject.toml` и `README.md`, а также настройте entry-points в зависимости от типа:

#### Модуль

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Описание функциональности модуля"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### Адаптер

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "Описание функциональности адаптера"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **Примечание**: Рекомендуется начинать имя пакета с `ErisPulse-`, чтобы пользователи могли легко его идентифицировать. Ключ entry-point (например, `"MyModule"`) будет использоваться как имя модуля в SDK.

### 2. Публикация на PyPI

```bash
# Сборка и публикация (требуется аккаунт на PyPI)
pip install build twine
python -m build
python -m twine upload dist/*
```

После успешной публикации проверьте установку:

```bash
pip install ErisPulse-MyModule
```

### 3. Отправка в магазин модулей

Перейдите на [ErisPulse Магазин модулей](https://www.erisdev.com/#market), нажмите «Отправить модуль», войдите в систему и заполните информацию о модуле.

Поддерживаемые способы входа: **GitHub**, **Codeberg**, **Yunhu**, можно выбрать любой.

Важные моменты для заполнения:
- Название модуля, описание, адрес репозитория
- Минимальная версия SDK: если не уверены, укажите версию [последнего релиза ErisPulse](https://pypi.org/project/ErisPulse/)

После отправки изменения вступают в силу немедленно, пользователи могут установить модуль через источник. Модуль будет помечен как «Не проверено», после проверки разработчиком он изменится на «Проверено».

> **О статусе проверки**:
> - «Не проверено» означает, что модуль ещё не прошёл официальную проверку, но не говорит о его проблемах
> - При установке не проверенного модуля через `epsdk install` пользователи получат предупреждение о риске, которое нужно подтвердить для продолжения установки

### 4. Управление опубликованными модулями

После входа в систему на вкладке «Отправить модуль» в магазине модулей, перейдите на вкладку «Мои модули», где можно:

- **Редактировать** — изменить описание модуля, адрес репозитория, теги и т.д., номер версии будет автоматически синхронизирован с PyPI
- **Удалить** — удалить модуль из магазина модулей (необратимо)

> Новые модули могут отображаться в списке «Мои модули» через несколько минут после отправки.

## Обновление опубликованных модулей

1. Обновите `version` в `pyproject.toml`
2. Пересоберите и перезагрузите: `python -m build && python -m twine upload dist/*`
3. Магазин модулей автоматически синхронизирует последнюю версию с PyPI

Пользователи могут обновить модуль с помощью `epsdk upgrade MyModule`.

## Список проверок перед публикацией

Перед отправкой на PyPI, пожалуйста, проверьте следующие пункты:

### Качество кода

- [ ] Все публичные API имеют аннотации типов (подписи функций и возвращаемые значения)
- [ ] Все публичные методы имеют строки документации (`"""..."""` формат, включая `:param` / `:return` / `:raises`)
- [ ] Проходит проверку `ruff check` (без предупреждений)
- [ ] Код покрыт тестами на ≥ 80%
- [ ] Проходят все тесты `pytest`

### Совместимость

- [ ] `pyproject.toml` объявляет минимальную версию SDK: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] Тестировано на Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] Тестировано на целевых операционных системах (Windows / Linux / macOS, если применимо)
- [ ] Нет циклических зависимостей

### Конфигурация

- [ ] Если используется декларативная конфигурация (`ConfigClass` + `BaseConfig` / `BotAccountConfig`), поля конфигурации имеют `description` (рекомендуется в формате i18n) и метаданные `ui`
- [ ] Если зарегистрированы ключи переводов i18n, они покрывают все 5 языков (zh-CN / zh-TW / en / ja / ru)
- [ ] Чувствительные поля помечены `secret=True`

### Документация

- [ ] `README.md` содержит инструкции по установке и примеры использования
- [ ] `README.md` объясняет способ конфигурации (примеры конфигурационных файлов + переменные окружения)
- [ ] `CHANGELOG.md` содержит все изменения
- [ ] Адаптер обновил документацию по функциональности платформы (поддерживаемые типы Send, типы событий и т.д.)

### Публикация

- [ ] Номер версии в `pyproject.toml` обновлён
- [ ] Сборка прошла успешно: `python -m build`
- [ ] Отправлено на PyPI: `python -m twine upload dist/*`
- [ ] Установка проверена: `pip install ErisPulse-xxx && epsdk run`

## Тестирование в режиме разработки

Перед официальной публикацией можно протестировать локально в режиме редактирования:

```bash
epsdk install -e /path/to/MyModule
# или
pip install -e /path/to/MyModule
```

## Часто задаваемые вопросы

### Обязательно ли имя пакета должно начинаться с `ErisPulse-`?

Нет, это не обязательно, но настоятельно рекомендуется. Это помогает пользователям легко идентифицировать пакеты экосистемы ErisPulse на PyPI.

### Можно ли зарегистрировать несколько модулей в одном пакете?

Да. Просто добавьте несколько пар ключ-значение в `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Сколько времени занимает проверка?

Обычно проверка занимает 1–3 рабочих дня. Вы можете проверить статус проверки на вкладке «Мои модули» в магазине модулей.

## Распространение приложений через Docker-образы

Если ваше приложение не подходит для публикации на PyPI (например, содержит приватные зависимости или требует предварительной настройки среды), вы можете опубликовать Docker-образ через **GitHub Container Registry (GHCR)**, чтобы другие пользователи могли запускать его с помощью `docker pull`.

### Сценарии использования

- У вас есть **полное приложение-бот** (модуль + конфигурация + скрипт запуска), которое вы хотите распространить одним кликом
- Модуль/адаптер зависит от **приватных пакетов** или имеет специальный процесс установки, который не подходит для PyPI
- Вы хотите предоставить **готовое решение**, чтобы снизить порог входа для пользователей

### 1. Создание Dockerfile

Создайте Dockerfile на основе официального образа ErisPulse, просто добавив ваш модуль:

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="Описание модуля" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

Если модулю требуются дополнительные системные зависимости (например, клиент SSH и т.д.), добавьте их после `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` уже включает ErisPulse, ErisPulse-Dashboard, Python-интерпретатор и uv, дополнительная установка не требуется.

### 2. Создание рабочего потока GitHub Actions

Создайте файл `.github/workflows/docker-publish.yml`:

```yaml
name: Публикация Docker-образа

on:
  workflow_dispatch:
  push:
    branches:
      - main
    tags:
      - "v*"

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository_owner }}/my-bot

jobs:
  docker-publish:
    runs-on: ubuntu-latest

    steps:
      - name: Клонирование кода
        uses: actions/checkout@v4

      - name: Настройка QEMU (поддержка нескольких архитектур)
        uses: docker/setup-qemu-action@v3

      - name: Настройка Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Вход в GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Извлечение метаданных Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Сборка и отправка Docker-образа
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

> `GITHUB_TOKEN` предоставляется автоматически GitHub Actions, не нужно создавать ключи вручную.

### 3. Запуск сборки

Сборка будет автоматически запускаться при отправке кода или создании тега:

```bash
# Отправка на ветку main запускает сборку
git push origin main

# Или создание тега запускает сборку
git tag v1.0.0
git push origin v1.0.0
```

Также можно запустить вручную на вкладке **Actions** репозитория.

### 4. Настройка образа как публичного

Образы GHCR по умолчанию **приватные**, необходимо изменить на **Public** в настройках GitHub, чтобы другие пользователи могли получать образ без авторизации:

1. Перейдите в репозиторий → **Packages** → нажмите на соответствующий пакет
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. Использование пользователем

После завершения сборки пользователь может запустить его одной командой `docker run`:

```bash
docker run -d \
  --name my-bot \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -e TZ=Asia/Shanghai \
  -e ERISPULSE_DASHBOARD_TOKEN=your-token \
  --restart unless-stopped \
  ghcr.io/<your-username>/my-bot:latest
```

Или с использованием `docker-compose.yml`:

```yaml
services:
  my-bot:
    image: ghcr.io/<your-username>/my-bot:latest
    container_name: my-bot
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    environment:
      - TZ=Asia/Shanghai
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    restart: unless-stopped
```

### Одновременная публикация в Docker Hub

Расширьте рабочий поток, добавив вход в Docker Hub перед шагом входа в GHCR, и добавьте адрес Docker Hub в `images`:

```yaml
      - name: Вход в Docker Hub
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Извлечение Docker-метаданных
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> Необходимо добавить `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN` в настройках секретов репозитория.

### Docker-образ (GHCR) vs PyPI

| Характеристика | Docker-образ (GHCR) | PyPI |
|------|---------------------|-----------|
| Способ распространения | `docker pull` — однострочное запуск | `pip install` + ручная настройка |
| Область применения | Полное приложение/решение | Отдельный модуль/адаптер |
| Приватные зависимости | Встроенная поддержка | Требуется приватный PyPI-репозиторий |
| Магазин модулей | Не поддерживается | Можно отправить в магазин модулей |
| Многоплатформенность | Поддерживает amd64/arm64 | Независим от архитектуры |

Оба способа не исключают друг друга — вы можете одновременно публиковать модуль в магазине модулей через PyPI и предоставлять готовый Docker-образ через GHCR.



### CLI 命令参考

# Справка по командной строке

Инструмент командной строки ErisPulse (`epsdk`) предоставляет функции управления проектами и управления пакетами.

> **Примечание**：Все команды можно просмотреть с подробным описанием параметров через `epsdk <команда> --help`.

---

## Команды управления пакетами

| Команда | Алиас | Параметры | Описание |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | Установка модулей/адаптеров |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | Удаление модулей/адаптеров |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | Обновление указанного модуля или всех |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | Обновление самого SDK |

## Диагностические команды

| Команда | Алиас | Параметры | Описание |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose]` | Диагностика среды и вывод отчета о здоровье |

### install

Установка модуля ErisPulse или пакета адаптера. Если имя пакета не указано, запускается интерактивный интерфейс установки.

**Алиасы：** `i`, `add`

**Параметры：**

| Параметр | Краткий параметр | Описание |
|------|--------|------|
| `[package]...` | | Имя пакета для установки, можно указать несколько |
| `--upgrade` | `-U` | Обновление до последней версии при установке |
| `--pre` | | Разрешить установку предварительных версий |
| `--editable` | `-e` | Установка в режиме редактируемой ссылки (требуется указать путь) |
| `--user` | | Установка в каталог site-packages пользователя |
| `--no-deps` | | Не устанавливать зависимости |
| `--target` | `-t` | Установка в указанный каталог |
| `--index-url` | | Указание адреса зеркала PyPI |
| `--extra-index-url` | | Дополнительный адрес зеркала PyPI (можно указать несколько) |
| `--no-cache-dir` | | Отключение кэширования |
| `--requirement` | `-r` | Установка из файла requirements |
| `--constraint` | `-c` | Установка из файла ограничений |
| `--force-reinstall` | | Принудительная переустановка |
| `--ignore-installed` | | Игнорировать уже установленные пакеты |
| `--compile` | | Компиляция файлов .pyc после установки |
| `--no-compile` | | Не компилировать файлы .pyc после установки |
| `--prefix` | | Установка в указанный каталог префикса |
| `--src` | | Каталог исходного кода для редактируемой установки |
| `--config-settings` | | Передача настроек в бэкенд сборки (можно указать несколько) |
| `--no-binary` | | Ограничение не использовать бинарные пакеты (формат вида `:all:`) |
| `--only-binary` | | Ограничение использовать только бинарные пакеты (формат вида `:all:`) |
| `--prefer-binary` | | Предпочтение бинарным пакетам |
| `--build-isolation` | | Включение изоляции сборки |
| `--no-build-isolation` | | Отключение изоляции сборки |
| `--upgrade-strategy` | | Стратегия обновления：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | Разрешить изменение пакетов Python, управляемых менеджером пакетов системы |
| `--no-uv` | | Использовать pip вместо uv |

**Примеры：**

```bash
# Установка одного модуля
epsdk install Weather

# Установка нескольких модулей
epsdk install Yunhu Weather

# Установка и обновление с зеркала
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Установка в режиме редактируемой ссылки (режим разработки)
epsdk install -e ./my-adapter
```

### uninstall

Удаление установленного модуля ErisPulse или пакета адаптера. Если имя пакета не указано, запускается интерактивный интерфейс удаления.

**Алиасы：** `rm`, `remove`

**Параметры：**

| Параметр | Описание |
|------|------|
| `<package>...` | Имя пакета для удаления, можно указать несколько |
| `--no-uv` | Использовать pip вместо uv |

**Примеры：**

```bash
# Удаление одного модуля
epsdk uninstall Weather

# Удаление нескольких модулей
epsdk uninstall Yunhu Weather
```

### upgrade

Обновление установленного компонента ErisPulse. Если имя пакета не указано, обновляются все компоненты в интерактивном режиме.

**Алиасы：** `up`

**Параметры：**

| Параметр | Краткий параметр | Описание |
|------|--------|------|
| `[package]...` | | Имя пакета для обновления, можно указать несколько |
| `--force` | `-f` | Принудительное обновление, пропуск подтверждения |
| `--pre` | | Разрешить обновление до предварительных версий |
| `--no-uv` | | Использовать pip вместо uv |

**Примеры：**

```bash
# Обновление всех пакетов
epsdk upgrade

# Обновление указанного пакета
epsdk upgrade Weather

# Принудительное обновление (пропуск подтверждения)
epsdk upgrade -f
```

### self-update

Обновление самого SDK ErisPulse до последней версии.

**Алиасы：** `su`, `update`

**Параметры：**

| Параметр | Краткий параметр | Описание |
|------|--------|------|
| `[version]` | | Указание номера целевой версии для обновления |
| `--pre` | | Разрешить обновление до предварительных версий |
| `--force` | `-f` | Принудительное обновление, пропуск подтверждения |
| `--no-uv` | | Использовать pip вместо uv |

**Примеры：**

```bash
# Обновление до последней стабильной версии
epsdk self-update

# Обновление до указанной версии
epsdk self-update 1.2.3

# Обновление с разрешением предварительных версий
epsdk self-update --pre

# Принудительное обновление
epsdk self-update -f
```

---

## Команды запроса информации

| Команда | Алиас | Параметры | Описание |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | Список установленных компонентов |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | Список компонентов, доступных в репозитории |

### list

Вывод списка установленных модулей ErisPulse и адаптеров.

**Алиасы：** `l`, `ls`

**Параметры：**

| Параметр | Краткий параметр | Описание |
|------|--------|------|
| `--type` | `-t` | Указание типа：`modules`、`adapters`、`all` (по умолчанию) |
| `--outdated` | `-o` | Отображение только пакетов, которые можно обновить |

**Примеры：**

```bash
# Список всех установленных компонентов
epsdk list

# Список только модулей
epsdk list -t modules

# Список только адаптеров
epsdk list -t adapters

# Показ только обновляемых пакетов
epsdk list -o
```

### list-remote

Вывод списка модулей ErisPulse и адаптеров, доступных в удаленном репозитории.

**Алиасы：** `lsr`

**Параметры：**

| Параметр | Краткий параметр | Описание |
|------|--------|------|
| `--type` | `-t` | Указание типа：`modules`、`adapters`、`all` (по умолчанию) |
| `--refresh` | `-r` | Принудительное обновление кэша списка пакетов из удаленного репозитория |

**Примеры：**

```bash
# Список всех доступных компонентов в удаленном репозитории
epsdk list-remote

# Список только удаленных модулей
epsdk list-remote -t modules

# Обновление кэша и вывод списка
epsdk list-remote -r
```

---

## Команды управления запуском

| Команда | Алиас | Параметры | Описание |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | Запуск указанного скрипта или SDK |

### run

Запуск скрипта проекта ErisPulse или запуск SDK напрямую. Поддержка режима горячей перезагрузки.

**Алиасы：** `r`

**Параметры：**

| Параметр | Описание |
|------|------|
| `[script]` | Файл скрипта для запуска, если не указан, запускается SDK |
| `--reload` | Включение режима горячей перезагрузки, автоматический перезапуск при изменении файлов |

**Примеры：**

```bash
# Запуск SDK напрямую
epsdk run

# Запуск указанного файла скрипта
epsdk run main.py

# Запуск в режиме горячей перезагрузки (автоматический перезапуск при изменении файлов)
epsdk run main.py --reload

# Запуск SDK в режиме горячей перезагрузки
epsdk run --reload
```

---

## Команды управления проектами

| Команда | Алиас | Параметры | Описание |
|------|------|------|------|
| `init` | — | `[--project-name/-n <name>] [--quick/-q] [--force/-f] [--here] [--no-uv]` | Инициализация проекта ErisPulse |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | Создание каркаса модуля/адаптера |

### init

Инициализация нового проекта ErisPulse. Поддержка интерактивного и быстрого режимов.

**Параметры：**

| Параметр | Краткий параметр | Описание |
|------|--------|------|
| `--project-name` | `-n` | Имя проекта |
| `--quick` | `-q` | Быстрый режим, пропуск интерактивного мастера |
| `--force` | `-f` | Принудительное перезапись существующих файлов конфигурации |
| `--here` | | Инициализация в текущей директории, без создания подпапок |
| `--no-uv` | | Использовать pip вместо uv |

**Примеры：**

```bash
# Интерактивная инициализация
epsdk init

# Быстрая инициализация
epsdk init -q -n my_bot

# Принудительное перезапись существующей конфигурации
epsdk init -f

# Инициализация в текущей директории
epsdk init --here -n my_bot
```

### create

Создание каркасного проекта модуля или адаптера ErisPulse.

**Параметры：**

| Параметр | Краткий параметр | Описание |
|------|--------|------|
| `{module,adapter}` | | Тип для создания：`module` или `adapter` |
| `--name` | `-n` | Имя проекта (PascalCase) |
| `--description` | `-d` | Описание проекта |
| `--author` | `-a` | Имя автора |
| `--email` | `-e` | Email автора |
| `--homepage` | | URL домашней страницы проекта |
| `--output` | `-o` | Каталог вывода (по умолчанию текущая директория) |
| `--force` | `-f` | Принудительное перезапись существующего каталога |

**Примеры：**

```bash
# Интерактивное создание (с подсказкой выбора типа и ввода информации)
epsdk create

# Прямое создание проекта Module
epsdk create module -n MyModule

# Прямое создание проекта Adapter
epsdk create adapter -n MyAdapter

# Полные параметры
epsdk create module -n MyModule -d "Описание модуля" -a "Автор" -e "mail@example.com"

# Указание каталога вывода
epsdk create module -n MyModule -o ./projects

# Принудительное перезапись существующего каталога
epsdk create module -n MyModule -f
```

---

## Команды языка

| Команда | Алиас | Параметры | Описание |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | Просмотр или переключение языка отображения CLI |

### i18n

Просмотр текущего языка CLI, список поддерживаемых языков, переключение языка отображения. Если параметры не указаны, запускается интерактивный интерфейс выбора.

**Алиасы：** `language`, `lang`

**Параметры：**

| Параметр | Краткий параметр | Описание |
|------|--------|------|
| `[lang]` | | Код языка для переключения (например `zh-CN`、`en`、`ja`、`ru`) |
| `--list` | `-l` | Вывод списка всех поддерживаемых языков |

**Примеры：**

```bash
# Интерактивный выбор языка
epsdk i18n

# Переключение на английский
epsdk i18n en

# Переключение на японский
epsdk i18n ja

# Вывод списка всех поддерживаемых языков
epsdk i18n --list
```

---

## Команды типов (Stubs)

| Команда | Алиас | Параметры | Описание |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | Генерация файлов типов stub для поддержки автодополнения в IDE |

### types

Сканирование установленных модулей ErisPulse и адаптеров для генерации файлов типов `.pyi`, обеспечивающих точное автодополнение и проверку типов в IDE.

**Алиасы：** `t`, `stub`

**Параметры：**

| Параметр | Краткий параметр | Описание |
|------|--------|------|
| `--output` | `-o` | Путь для вывода (по умолчанию `ep-stubs/` в текущей директории) |
| `--force` | | Принудительная перезапись существующих файлов stub |
| `--adapters-only` | | Генерация stub типов только для адаптеров |
| `--modules-only` | | Генерация stub типов только для модулей |

> **Внимание：** `--adapters-only` и `--modules-only` взаимоисключают друг друга, при одновременном указании действует последний.

**Примеры：**

```bash
# Генерация stub типов для всех установленных модулей и адаптеров
epsdk types

# Генерация stub типов только для адаптеров
epsdk types --adapters-only

# Вывод в указанный каталог
epsdk types -o ./typings

# Принудительная перезапись существующих файлов
epsdk types --force
```

---

## Глобальные параметры

Следующие параметры применимы ко всем командам：

| Параметр | Краткий параметр | Описание |
|------|--------|------|
| `--help` | `-h` | Отображение справочной информации |
| `--version` | `-V` | Отображение информации о версии |
| `--verbose` | `-v` | Подробный вывод (можно комбинировать с `-vv`/`-vvv`) |
| `--no-color` | | Отключение цветного вывода (для CI / логов) |
| `--yes` | `-y` | Автоматическое подтверждение всех интерактивных запросов (неинтерактивный режим) |

---

## Диагностика окружения

### doctor

Диагностика текущей среды запуска CLI, вывод отчета о здоровье. Используется для устранения проблем типа "почему не устанавливается / не подключается".

| Параметр | Описание |
|------|------|
| `--verbose` | Показ подробной информации диагностики |

**Проверки：**
- **Python**：Версия и путь интерпретатора
- **Backend установки**：Использование `uv` или `pip`
- **Целевой интерпретатор**：Целевая среда Python, куда устанавливаются пакеты
- **Файл конфигурации**：Наличие `config/config.toml`
- **Связь с PyPI**：Возможность доступа к PyPI (и отображение количества найденных компонентов)
- **Прокси системы**：Обнаружение прокси-сервера

```bash
# Диагностика среды выполнения
epsdk doctor

# Использование алиаса
epsdk diag
```

---

## Интерактивная установка

Запуск `epsdk install` без указания имени пакета приводит к интерактивной установке：

```bash
epsdk install
```

Интерфейс предоставляет：
1. Выбор адаптера
2. Выбор модуля
3. Пользовательская установка

## Частые сценарии использования

### Установка модулей

```bash
# Установка одного модуля
epsdk install Weather

# Установка нескольких модулей
epsdk install Yunhu Weather

# Обновление модуля
epsdk install Weather -U
```

### Перечисление компонентов

```bash
# Список всех компонентов
epsdk list

# Список только адаптеров
epsdk list -t adapters

# Список только обновляемых компонентов
epsdk list -o

# Просмотр доступных в удаленном репозитории компонентов
epsdk list-remote
```

### Удаление компонентов

```bash
# Удаление одного компонента
epsdk uninstall Weather

# Удаление нескольких компонентов
epsdk uninstall Yunhu Weather
```

### Обновление компонентов

```bash
# Обновление всех компонентов
epsdk upgrade

# Обновление указанного компонента
epsdk upgrade Weather

# Принудительное обновление
epsdk upgrade -f
```

### Запуск проекта

```bash
# Обычный запуск
epsdk run main.py

# Режим горячей перезагрузки
epsdk run main.py --reload
```

### Переключение языка

```bash
# Интерактивный выбор языка
epsdk i18n

# Переключение на английский
epsdk i18n en

# Вывод списка поддерживаемых языков
epsdk i18n --list
```

### Генерация типов (Stubs)

```bash
# Генерация всех типов stub
epsdk types

# Генерация только типов модулей
epsdk types --modules-only
```

### Инициализация проекта

```bash
# Интерактивная инициализация
epsdk init

# Быстрая инициализация
epsdk init -q -n my_bot
```

### Создание каркаса

```bash
# Интерактивное создание (с подсказкой выбора типа и ввода информации)
epsdk create

# Прямое создание проекта Module
epsdk create module -n MyModule

# Прямое создание проекта Adapter
epsdk create adapter -n MyAdapter

# Полные параметры
epsdk create module -n MyModule -d "Описание модуля" -a "Автор" -e "mail@example.com"

# Принудительная перезапись существующего каталога
epsdk create module -n MyModule -f



======
API 参考
======


### 核心模块 API

# API Ядерного модуля

Этот документ предоставляет краткий справочник по API модуля ядра ErisPulse, включая сигнатуры методов и краткое описание. Дополнительные сведения о деталях использования и примерах можно найти по ссылкам «Полная документация» в каждом модуле.

请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。

再次提醒：如果文档包含语言切换行（各语言名称用 `` | `` 分隔的行），务必严格遵守上方第8条的格式要求，不要写出 ``[**Label**](file)`` 这类错误格式。
```markdown
# Ядерный модуль

ErisPulse использует модульную архитектуру. Основные компоненты системы включают в себя: **ErisPulse**, **Кластер**, **Токен**, **Шина событий**, **Менеджер подключений** и **Утилиты**. Обратите внимание, что токен и другие секретные данные не должны быть видны в коде.

*   **ErisPulse**: Основная библиотека, содержащая все инструменты, необходимые для запуска и управления приложением.
*   **Кластер**: Управляет распределением соединений между узлами.
*   **Токен**: Секретный ключ, связанный с приложением (входит в состав секрета для проверки JWT).
*   **Шина событий**: Система для реализации общих событий и обработчиков.
*   **Менеджер подключений**: Обеспечивает общие подключения к базе данных и другую сетевую инфраструктуру.
*   **Утилиты**: Набор вспомогательных функций для унифицированной обработки данных, системных сообщений, логирования и обработки ошибок.

> **Примечание**:
> 1. Убедитесь, что вы правильно настроили [распределение соединений](docs/ru/configuration/connection-distribution.md).
> 2. Не передавайте и не храните секретные данные в открытом тексте.

## Методы

В этом разделе описаны общие методы, которые можно вызвать из любого места.

| Метод | Описание |
| :--- | :--- |
| `process_request(request_id)` | Принимает `request_id` (идентификатор запроса), определяет тип запроса и соответствующий обработчик. Затем вызывает этот обработчик. |
| `init()` | Инициализирует подключение к базе данных (если оно настроено). Возвращает `Promise<void>`. |
| `start()` | Запускает приложение ErisPulse. Возвращает `Promise<void>`. |
| `stop()` | Останавливает приложение ErisPulse. Возвращает `Promise<void>`. |

## Конфигурация

```typescript
// Доступ к глобальному экземпляру ErisPulse
const pulse = ErisPulse;

// Доступ к конкретным экземплярам модуля
const cluster = pulse.Cluster;
const bus = pulse.Bus;
const token = pulse.Token;
const connectionManager = pulse.ConnectionManager;
```

## Примеры

### Логирование

Этот пример показывает, как вести журнал `INFO` при получении события `token_created`.

```typescript
// Подписка на событие token_created
token.on('token_created', async (payload) => {
    console.log('Токен успешно создан', payload);
    // Логирование в формате INFO
    pulse.Util.logInfo('Токен успешно создан', payload);
});
```

### Запуск приложения

Этот пример демонстрирует базовый сценарий запуска приложения.

```typescript
// Проверяем, загружен ли ErisPulse
if (!ErisPulse) {
    console.error('ErisPulse не найден. Пожалуйста, установите его, запустив `npm install erispulse`.');
    process.exit(1);
}

// Инициализация подключения к базе данных
await pulse.init();

// Запуск приложения
await pulse.start();
```

### Создание токена

Этот пример показывает, как создать новый токен.

```typescript
// Создаем новый токен с именем пользователя
const userToken = await token.create({
    name: 'Имя пользователя',
    permission: 'user',
});

// Создаем токен администратора
const adminToken = await token.create({
    name: 'Администратор',
    permission: 'admin',
});

// Создаем токен с ограниченным доступом
const limitedToken = await token.create({
    name: 'Ограниченный',
    permission: 'limited',
});

// Пример: Создание токена с явным сроком действия
const expiredToken = await token.create({
    name: 'Одноразовый',
    permission: 'single-use',
    expiration: new Date('2023-12-31'), // Срок действия истекает в конце 2023 года
});
```

## Модуль хранилища

База данных на основе SQLite, поддерживающая универсальные SQL-запросы в стиле цепочек вызовов.

### Базовые операции

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### Массовые операции

```python
sdk.storage.set_multi({"key1": "val1", "key2": "val2"})
values = sdk.storage.get_multi(["key1", "key2"])
sdk.storage.delete_multi(["key1", "key2"])
```

### Транзакционные операции

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Доступ к свойствам

```python
sdk.storage.my_key          # эквивалентно sdk.storage.get("my_key")
sdk.storage.my_key = "val"  # эквивалентно sdk.storage.set("my_key", "val")
```

### SQL-запросы в стиле цепочек вызовов

Модуль хранилища предоставляет универсальный конструктор SQL-запросов в стиле цепочек вызовов, поддерживающий операции CRUD для пользовательских таблиц.

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> Полная документация по API для запросов в стиле цепочек (Select/Insert/Update/Delete/Where/OrderBy/Limit, AlterTable, транзакции и др.) доступна по ссылке [SQL-запросы в стиле цепочек](../ru/advanced/sql-builder.md).

### Абстракция хранилища

`StorageManager` наследуется от абстрактного базового класса `BaseStorage`, что позволяет расширять функциональность для других хранилищ (Redis, MySQL и т.д.).

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### Асинхронный интерфейс

Модули Storage и Config предоставляют асинхронные методы (с префиксом `a`), которые можно безопасно вызывать в асинхронных обработчиках. Синхронные методы остаются доступными, изменения в существующем коде не требуются.

```python
# Асинхронное хранилище
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# Асинхронные массовые операции
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# Асинхронная конфигурация
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()

## Модуль Config

Управление конфигурационными файлами в формате TOML, поддерживает пути с разделением точками.

### Обзор API

| Метод | Описание |
|------|------|
| `getConfig(key, default)` | Чтение конфигурации, поддерживает пути с точками, например `"MyModule.subkey"` |
| `setConfig(key, value, immediate=False)` | Запись конфигурации. При `immediate=True` сохранение происходит немедленно в файл |
| `force_save()` | Принудительная запись конфигурации из памяти в файл |
| `reload()` | Перезагрузка конфигурации из файла |
| `agetConfig(key, default)` | Асинхронное чтение конфигурации |
| `asetConfig(key, value, immediate)` | Асинхронная запись конфигурации |
| `aforce_save()` | Асинхронная принудительная сохранение |
| `areload()` | Асинхронная перезагрузка |

### Пример

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` по умолчанию использует отложенную запись (групповое сохранение каждые 5 секунд). Установка `immediate=True` позволяет немедленно сохранить конфигурацию в файл. Изменения конфигурации вызывают событие жизненного цикла `config.set`.

## Модуль логирования

Модульная система логирования на основе вывода библиотеки Rich, поддерживающая дочерние логгеры и управление на уровне модулей.

### Базовое использование

```python
sdk.logger.debug("Отладочная информация")
sdk.logger.info("Информация о запуске")
sdk.logger.warning("Предупреждение")
sdk.logger.error("Сообщение об ошибке")
sdk.logger.critical("Критическая ошибка")
```

### Дочерние логгеры

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("Лог дочернего модуля")

child_logger.get_child("utils")  # Поддержка вложенности
```

### Управление уровнем логирования

```python
sdk.logger.set_level("DEBUG")                          # Глобальный уровень
sdk.logger.set_module_level("MyModule", "DEBUG")       # Уровень модуля

# Поддерживаемые уровни (от низкого к высокому):
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE — самый низкий уровень, выводит подробные отладочные сообщения изнутри фреймворка (распределение событий, регистрация маршрутов и т.д.)
sdk.logger.set_level("TRACE")                          # Включить все логи
```

### Подписка на логи (Push-режим)

Обеспечивает прием структурированных логов модулями, такими как Dashboard, в реальном времени, с поддержкой фильтрации по уровню и повторной отправки истории.

> **Явная подписка на низкоуровневые логи**: `min_level` подписчика может быть ниже глобального уровня логирования. В этом случае низкоуровневые логи **передаются только соответствующим подписчикам**, они не выводятся в консоль и не записываются в память, что предотвращает загрязнение основного потока логов.
>
> ```python
> # Глобальный уровень — INFO, но можно отдельно подписаться на DEBUG логи
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# Способ через декоратор
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "Строгий режим: ...",
    # }
    pass

# Способ прямого вызова
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| Метод | Описание |
|------|------|
| `handler(id, *, min_level)(func)` | Универсальный способ: работает и как декоратор, и при прямом вызове. Если `id` не указан, используется имя функции. Параметр `min_level` может быть ниже глобального уровня (низкоуровневые логи отправляются только подписчикам, не попадая в консоль или память). При регистрации автоматически отправляются исторические логи |
| `remove_handler(id)` | Удаляет подписчика |

### Управление выводом

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)

## Модуль адаптера

Менеджер адаптера, управляющий регистрацией, запуском и остановкой адаптеров для нескольких платформ.

### Обзор API

| Метод | Описание |
|------|------|
| `get(platform)` | Получение экземпляра адаптера |
| `exists(platform)` | Проверка, зарегистрирован ли адаптер |
| `enable(platform)` / `disable(platform)` | Включение / отключение адаптера |
| `is_enabled(platform)` | Проверка, включен ли адаптер |
| `startup(platforms)` / `shutdown(platforms)` | Запуск / остановка адаптера |
| `is_running(platform)` | Проверка, выполняется ли адаптер |
| `list_running()` | Список всех выполняющихся адаптеров |
| `platforms` | Получение списка названий всех платформ |

### События адаптера

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Запрос состояния бота

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> Полный API управления адаптерами см. в [Системе API адаптера](adapter-system.md).

## Модуль

Менеджер модулей управляет регистрацией, загрузкой и выгрузкой плагинов.

### Обзор API

| Метод | Описание |
|------|------|
| `get(name)` | Получает экземпляр модуля или прокси-объект с отложенной загрузкой (возвращает прокси, если модуль зарегистрирован, но не загружен) |
| `exists(name)` | Проверяет, зарегистрирован ли модуль |
| `is_loaded(name)` | Проверяет, загружен ли модуль |
| `is_enabled(name)` | Проверяет, включен ли модуль |
| `enable(name)` / `disable(name)` | Включает/выключает модуль |
| `load(name)` / `unload(name)` | Загружает/выгружает модуль |
| `list_registered()` | Выводит список зарегистрированных модулей |
| `list_loaded()` | Выводит список загруженных модулей |
| `get_info(name)` | Получает информацию о модуле |
| `get_status_summary()` | Получает сводку по состоянию модулей |

### Доступ к свойствам

```python
module = sdk.module.get("ИмяМодуля")
module = sdk.module.ИмяМодуля
module = sdk.ИмяМодуля  # эквивалентное сокращение

## Модуль Lifecycle

Управление жизненным циклом на основе событий с функциями отправки и прослушивания событий.

### Обзор API

| Метод | Описание |
|------|------|
| `on(event, priority=0)` | Регистрация обработчика событий через декоратор, поддерживает сопоставление с точкой и подстановочный символ `*` |
| `register(event, handler, priority=0)` | Функциональная регистрация обработчика |
| `unregister(event, handler=None)` | Удаление обработчика |
| `emit(event, data)` | Асинхронный запуск события |
| `emit_sync(event, data)` | Синхронный запуск события |
| `submit_event(event_type, msg, data, source)` | Отправка события в стандартном формате (совместимо со старыми версиями) |
| `start_timer(id)` / `stop_timer(id)` | Счётчик производительности |

### Пример

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"Инициализация модуля: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"Событие модуля: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})
```

> Полный список стандартных событий и подробное описание использования см. в разделе [Управление жизненным циклом](../advanced/lifecycle.md).

## Модуль Router

Менеджер маршрутизации HTTP/WebSocket на базе FastAPI + Uvicorn, поддерживающий декораторы маршрутизации, middleware, группировку, лимитирование частоты запросов (rate limiting), CORS.

> Более подробную документацию по API маршрутизации (декораторные маршруты, WebSocket, middleware, ограничение скорости запросов, CORS, безопасные заголовки и др.) см. в разделе [Менеджер маршрутизации](../advanced/router.md).

### Краткий обзор

```python
# HTTP маршруты
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket маршруты
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# Группировка маршрутов
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}

## HTTP-клиент

Единый сетевой клиент, объединяющий HTTP-запросы, WebSocket-соединения, управление пулом соединений, автоматические повторы попыток, статистику запросов и интеграцию событий жизненного цикла.

> Подробную документацию по сетевому клиенту (методы запроса, объекты ответа, клиент WebSocket, иерархия исключений и др.) см. в разделе [Сетевой клиент](../ru/advanced/http-client.md).

### Быстрый справочник

```python
from ErisPulse.Core import client

# HTTP-запрос
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Эхо: {text}")

## Отладка SDK

### dump_state()

Экспорт снимка текущего состояния работы фреймворка для целей отладки и диагностики.

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

Структура возврата содержит состояние следующих подсистем:

| Поля | Описание |
|------|------|
| `sdk` | Статус инициализации SDK, версия Python, платформа выполнения, метка времени |
| `adapters` | Список зарегистрированных/запущенных адаптеров, статус онлайн-ботов по каждой платформе |
| `modules` | Список зарегистрированных/включенных/отключенных/лениво загруженных модулей |
| `events` | Количество обработчиков различных типов событий (сообщения/уведомления/запросы/мета/команды) |
| `router` | Статус работы сервера, количество маршрутов HTTP/WebSocket |

> Добавлено в 2.5.2

## Документация

- [API системы событий](event-system.md) - API модуля Event
- [API системы адаптеров](adapter-system.md) - API управления адаптерами
- [Конструктор SQL-запросов](../advanced/sql-builder.md) - Полная документация по SQL-запросам в цепочке
- [Менеджер маршрутов](../advanced/router.md) - Полная документация менеджера маршрутов
- [Сетевой клиент](../advanced/http-client.md) - Полная документация сетевого клиента
- [Управление жизненным циклом](../advanced/lifecycle.md) - Полная документация жизненного цикла



### 事件系统 API

# API системы событий

В этой документации подробно описан API системы событий ErisPulse.

## Модуль команд Command

### Регистрация команд

```python
from ErisPulse.Core.Event import command

# Базовая команда
@command("hello", help="Отправить приветствие")
async def hello_handler(event):
    await event.reply("Здравствуйте!")

# Команда с псевдонимами
@command(["help", "h"], aliases=["помощь"], help="Показать справку")
async def help_handler(event):
    pass

# Команда с правами доступа
def is_admin(event):
    return event.get("user_id") in admin_ids

@command("admin", permission=is_admin, help="Команда администратора")
async def admin_handler(event):
    pass

# Скрытая команда
@command("secret", hidden=True, help="Секретная команда")
async def secret_handler(event):
    pass

# Группа команд
@command("admin.reload", group="admin", help="Перезагрузить модули")
async def reload_handler(event):
    pass
```

### Информация о командах

```python
# Получить справку по команде
help_text = command.help()

# Получить информацию о конкретной команде
cmd_info = command.get_command("admin")

# Получить все команды группы
admin_commands = command.get_group_commands("admin")

# Получить все видимые команды
visible_commands = command.get_visible_commands()
```

### Ожидание ответа

```python
# Ожидание ответа от пользователя
@command("ask", help="Запросить информацию о пользователе")
async def ask_command(event):
    reply = await command.wait_reply(
        event,
        prompt="Введите ваше имя:",  # уже отправлено выше
        timeout=30.0
    )
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Привет, {name}!")

# Ожидание ответа с проверкой
def validate_age(event_data):
    try:
        age = int(event_data.get_text())
        return 0 <= age <= 150
    except ValueError:
        return False

@command("age", help="Запросить возраст пользователя")
async def age_command(event):
    await event.reply("Введите ваш возраст:")
    
    reply = await command.wait_reply(
        event,
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"Ваш возраст: {age} лет")

# Ожидание ответа с колбэком
async def handle_confirmation(reply_event):
    text = reply_event.get_text().lower()
    if text in ["да", "yes", "y"]:
        await event.reply("Операция подтверждена!")
    else:
        await event.reply("Операция отменена.")

@command("confirm", help="Подтвердить операцию")
async def confirm_command(event):
    await command.wait_reply(
        event,
        prompt="Введите 'да' или 'нет':",
        callback=handle_confirmation
    )
```

## Модуль сообщений Message

### События сообщений

```python
from ErisPulse.Core.Event import message

# Слушать все сообщения
@message.on_message()
async def message_handler(event):
    sdk.logger.info(f"Получено сообщение: {event.get_text()}")

# Слушать личные сообщения
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"Личное сообщение от: {user_id}")

# Слушать групповые сообщения
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    sdk.logger.info(f"Групповое сообщение от: {group_id}")

# Слушать сообщения с упоминанием @
@message.on_at_message()
async def at_handler(event):
    mentions = event.get_mentions()
    sdk.logger.info(f"Упомянутый пользователь: {mentions}")
```

### Условное прослушивание

```python
# Использование приоритета для управления порядком выполнения
@message.on_message(priority=10)  # Чем больше число, тем выше приоритет
async def high_priority_handler(event):
    pass

# Реализация условной фильтрации внутри обработчика
@message.on_message()
async def filtered_handler(event):
    if "ключевое_слово" not in event.get_text():
        return
    # Обработка сообщений, содержащих ключевое слово
    pass
```

## Модуль уведомлений Notice

### События уведомлений

```python
from ErisPulse.Core.Event import notice

# Добавление в друзья
@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    await event.reply("Добро пожаловать в друзья!")

# Удаление из друзей
@notice.on_friend_remove()
async def friend_remove_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"Удаление друга: {user_id}")

# Приглашение в группу
@notice.on_group_increase()
async def member_increase_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"Добро пожаловать новому участнику!")

# Выход из группы
@notice.on_group_decrease()
async def member_decrease_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"Участник покинул группу: {user_id}")
```

## Модуль запросов Request

### События запросов

```python
from ErisPulse.Core.Event import request

# Запрос на добавление в друзья
@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    sdk.logger.info(f"Запрос на добавление в друзья: {user_id}, заметка: {comment}")

# Запрос на приглашение в группу
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Приглашение в группу: {group_id}, от: {user_id}")
```

## Модуль мета-событий Meta

### Мета-события

```python
from ErisPulse.Core.Event import meta

# Событие подключения
@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"Платформа {platform} подключена успешно")

# Событие отключения
@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"Платформа {platform} отключена")

# Событие сердечного удара
@meta.on_heartbeat()
async def heartbeat_handler(event):
    sdk.logger.debug("Получен сердечный удар")
```

### Запрос состояния бота

После того как адаптер отправляет мета-событие, платформа автоматически отслеживает состояние бота. Справку по API запросов состояния и событиям жизненного цикла см. в разделе [API системы адаптеров - Управление состоянием бота](adapter-system.md#bot-状态管理).

## Класс-обертка события Event

Обработчики событий модуля Event принимают экземпляр класса-обертки Event, который наследуется от dict и предоставляет удобные методы.

### Основные методы

```python
# Получение информации о событии
event_id = event.get_id()
event_time = event.get_time()
event_type = event.get_type()
detail_type = event.get_detail_type()
platform = event.get_platform()

# Получение информации о боте
self_platform = event.get_self_platform()
self_user_id = event.get_self_user_id()
self_info = event.get_self_info()
```

### Идентификатор сессии

```python
# Унифицированный целевой ID: возвращает group_id для групп, user_id для личных сообщений и т.д.
target_id = event.get_target_id()

# Уникальный идентификатор сессии, формат: {platform}:{detail_type}:{target_id}
session_id = event.get_session_id()
# Пример: "telegram:private:12345", "qq:group:67890"
```

`get_target_id()` возвращает первое непустое значение в следующем порядке: `group_id` → `channel_id` → `guild_id` → `thread_id` → `user_id`. Подходит для сценариев, требующих унифицированной идентификации сессии, таких как управление контекстом и хранение состояния.

### Методы сообщений

```python
# Получение содержимого сообщения
message_segments = event.get_message()
alt_message = event.get_alt_message()
text = event.get_text()

# Получение информации об отправителе
user_id = event.get_user_id()
nickname = event.get_user_nickname()
sender = event.get_sender()

# Получение информации о группе
group_id = event.get_group_id()

# Определение типа сообщения
is_msg = event.is_message()
is_private = event.is_private_message()
is_group = event.is_group_message()

# Сообщения с упоминанием @
is_at = event.is_at_message()
has_mention = event.has_mention()
mentions = event.get_mentions()
```

### Информация о команде

```python
# Получение информации о команде
cmd_name = event.get_command_name()
cmd_args = event.get_command_args()
cmd_raw = event.get_command_raw()

# Проверка, является ли событие командой
is_cmd = event.is_command()
```

### Функции ответа

```python
# Базовый ответ
await event.reply("Это сообщение")

# Указание метода отправки
await event.reply("http://example.com/image.jpg", method="Image")

# Ответ с @пользователем и цитированием сообщения
await event.reply("Привет", at_users=["user1"], reply_to="msg_id")

# @all (всем участникам)
await event.reply("Объявление", at_all=True)

# Использование платформенных методов модификаторов (параметр via)
await event.reply("Контент дашборда", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])

# Получение цепочки отправки, свободное добавление методов модификаторов и методов отправки (подходит для последовательного множества модификаторов / действий)
await event.send_chain().Expire(3600).Board("Контент дашборда")
await event.send_chain().DismissBoard()

# Ответ с использованием сегментов сообщений OneBot12
from ErisPulse.Core.Event import MessageBuilder
msg = MessageBuilder().text("Hello").image("url").build()
await event.reply_ob12(msg)

# Ожидание ответа
reply = await event.wait_reply(timeout=30)
```

### Запрос возможностей платформы

```python
# Проверка, поддерживает ли текущая платформа определенный метод отправки
if event.supports("Image"):
    await event.reply(url, method="Image")

# Перечисление всех доступных методов отправки для текущей платформы
methods = event.available_methods()
# ["Text", "Image", "Voice", ...]
```

### Методы ответа

Метод `reply()` поддерживает указание типа отправки через параметр `method`, а также два удобных логических параметра:

```python
# Простая текстовая реакция
await event.reply("Привет")

# Ответ и @отправителя
await event.reply("Привет", at_sender=True)

# Ответ с цитированием текущего сообщения
await event.reply("Получено", reply_to_message=True)

# Комбинированное использование
await event.reply("Получено", at_sender=True, reply_to_message=True)

# Отправка изображения (с использованием параметра method)
if event.supports("Image"):
    await event.reply("http://example.com/img.jpg", method="Image")
else:
    await event.reply("[Изображение] http://example.com/img.jpg")
```

**Описание параметров**:

| Параметр | Тип | Описание |
|------|------|------|
| `content` | str | Содержимое для отправки |
| `method` | str | Метод отправки, по умолчанию "Text", доступны "Image"/"Voice"/"Video"/"File" и др. |
| `at_sender` | bool | Отправить с упоминанием отправителя (автоматически извлекает user_id) |
| `quote` | bool | Цитировать и ответить на текущее сообщение (автоматически извлекает message_id) |
| `at_users` | list[str] | Список пользователей для упоминания |
| `reply_to` | str | Явно указать ID сообщения для ответа |
| `at_all` | bool | Отправить с упоминанием всех участников |

### Методы взаимодействия

```python
# confirm — подтверждение диалога (возвращает True/False/None)
if await event.confirm("Вы уверены, что хотите выполнить эту операцию?"):
    await event.reply("Подтверждено")

# Отправка подтверждения с использованием не Text метода
if await event.confirm("http://example.com/image.jpg", method="Image"):
    await event.reply("Изображение подтверждено")

# choose — меню выбора (возвращает индекс опции или None)
choice = await event.choose("Выберите цвет:", ["Красный", "Зеленый", "Синий"])

# options_format="auto" (по умолчанию) автоматически выбирает стиль в зависимости от method:
# Markdown→неупорядоченный список (- 1.вариант), Html→упорядоченный список (<ol>), иначе→простой текстовый список
# Методы для текста (Markdown, Html и т.д.) по умолчанию объединяют опции в конец
# merge_prompt=True может принудительно объединять для любого method; placeholder позволяет задать свой плейсхолдер
choice = await event.choose(
    "## Выберите\n{options}", ["A", "B"],
    method="Markdown", merge_prompt=True,
)

# collect — сбор формы (возвращает словарь {key: value} или None)
data = await event.collect([
    {"key": "name", "prompt": "Введите имя:"},
    {"key": "age", "prompt": "Введите возраст:",
     "validator": lambda e: e.get_text().isdigit()},
    {"key": "avatar", "prompt": "Отправьте аватар:", "method": "Image"},
])

# wait_for — ожидание произвольного события, удовлетворяющего условию
evt = await event.wait_for(event_type="notice", condition=lambda e: ..., timeout=120)

# conversation — контекст многоуровневого диалога
conv = event.conversation(timeout=60)
await conv.say("Добро пожаловать!")
```

> Подробное описание параметров методов взаимодействия и дополнительные примеры см. в разделе [Подробное описание класса-обертки события](../developer-guide/modules/event-wrapper.md) и [Многоуровневый диалог Conversation](../advanced/conversation.md).

### Утилитарные методы

```python
# Преобразование в словарь
event_dict = event.to_dict()

# Проверка, обработано ли событие
if not event.is_processed():
    event.mark_processed()

# Получение исходных данных
raw = event.get_raw()
raw_type = event.get_raw_type()
```

### Расширенные методы платформы

Адаптеры могут регистрировать платформенные методы для события, которые доступны только на экземплярах соответствующей платформы.

#### Пользователь: использование расширенных методов платформы

После того как адаптер зарегистрировал платформенные методы, вы можете вызывать их непосредственно в обработчике событий. Методы для разных платформ различаются, пожалуйста, обратитесь к соответствующей [документации платформы](../platform-guide/).

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Вызов платформенных методов в зависимости от платформы
    if platform == "email":
        subject = event.get_subject()           # уникально для почты
        attachments = event.get_attachments()   # уникально для почты
```

#### Запрос зарегистрированных методов платформы

```python
from ErisPulse.Core.Event import get_platform_event_methods

# Просмотр методов, зарегистрированных для конкретной платформы
methods = get_platform_event_methods("email")
# ["get_subject", "get_from", "get_attachments", ...]

# Динамическое определение и вызов
for method_name in get_platform_event_methods(event.get_platform()):
    method = getattr(event, method_name)
    print(f"{method_name}: {method()}")
```

#### Изоляция платформенных методов

Методы, зарегистрированные для разных платформ, не мешают друг другу:

```python
# Событие почты — только почтовые методы
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello"
event.get_chat_type()    # ❌ AttributeError

# Событие Telegram — только методы Telegram
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private"
event.get_subject()      # ❌ AttributeError
```

#### Поддержка hasattr / dir

```python
hasattr(event, "get_subject")   # Возвращает True только при platform="email"
"get_subject" in dir(event)     # То же самое
```

### Адаптер: регистрация расширенных методов платформы

Адаптеры могут регистрировать платформенные методы для Event с помощью декораторов, где первый параметр метода — `self` (экземпляр Event), что позволяет свободно обращаться к данным события.

#### Регистрация отдельного метода

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("email")
def get_subject(self):
    """Получить тему письма"""
    return self.get("email_raw", {}).get("subject", "")

@register_event_method("email")
def get_from(self):
    """Получить отправителя"""
    return self.get("email_raw", {}).get("from", {})
```

#### Банковая регистрация (Mixin класс)

При наличии множества методов рекомендуется использовать Mixin класс для групповой регистрации:

```python
from ErisPulse.Core.Event import register_event_mixin

class EmailEventMixin:
    def get_subject(self):
        return self.get("email_raw", {}).get("subject", "")

    def get_from(self):
        return self.get("email_raw", {}).get("from", {})

    def get_attachments(self):
        return self.get("email_raw", {}).get("attachments", [])

# Регистрация всех методов за один раз
register_event_mixin("email", EmailEventMixin)
```

#### Спецификация возвращаемых значений

| Сценарий | Возвращаемое значение | Способ использования пользователем |
|------|--------|------------|
| Возврат данных (текст, словарь и т.д.) | Прямое возвращаемое значение | `subject = event.get_subject()` |
| Выполнение операций (отправка сообщений и т.д.) | Возвращает `asyncio.Task` | `task = event.do_something()` `await` необязательно |

> **Совет**. Методы, не возвращающие данные, должны возвращать `asyncio.Task`, чтобы пользователь мог самостоятельно решать, выполнять `await` или нет; даже при отсутствии `await` операция будет завершена.

```python
@register_event_method("email")
def forward_email(self, to_address: str):
    """Пересылка письма — возвращает Task, пользователь сам решает, ждать ли"""
    import asyncio
    return asyncio.create_task(
        self._do_forward(to_address)
    )

# Пользователь может ждать результата
await event.forward_email("user@example.com")

# Можно не ждать, операция будет выполняться в фоне
event.forward_email("user@example.com")
```

#### Отмена регистрации метода

```python
from ErisPulse.Core.Event import unregister_event_method, unregister_platform_event_methods

# Отмена регистрации отдельного метода
unregister_event_method("email", "get_subject")

# Отмена регистрации всех методов платформы (вызывается при shutdown адаптера)
unregister_platform_event_methods("email")
```

#### Переопределение встроенных методов

`register_event_mixin` / `register_event_method` поддерживают переопределение встроенных методов Event (таких как `confirm`, `choose`, `collect`, `wait_reply`, `reply` и т.д.). Регистрируемые платформенные методы вступают в силу через `Event.__getattribute__` с приоритетом над встроенными, поэтому адаптеры могут предоставлять платформенные реализации взаимодействия.

Встроенная реализация экспортируется как функции `_builtin_*`, переопределяющая сторона может вызывать их как запасной вариант:

```python
from ErisPulse.Core.Event import register_event_mixin, _builtin_choose

class YunhuEventMixin:
    async def choose(self, prompt, options, timeout=60, method="Text"):
        # Платформа Yunhu использует компоненты кнопок
        buttons = [[{"text": opt} for opt in options]]
        await self.reply(prompt)
        # ...ожидание колбэков кнопок или текстового ответа...
        # Возврат к встроенной логике
        return await _builtin_choose(self, None, options, timeout, "Text")

register_event_mixin("yunhu", YunhuEventMixin)
```

## Кроссплатформенное расширение (шаблоны)

`register_event_method` и `register_event_mixin` поддерживают передачу `"*"` как имени платформы, методы, зарегистрированные таким образом, доступны на экземплярах Event **для всех платформ**. Подходит для функциональных модулей, требующих переиспользования на разных платформах, таких как диалоги ИИ и управление контекстом.

### Регистрация кроссплатформенных методов

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    """self — экземпляр Event, позволяет свободно обращаться к данным события и встроенным методам"""
    await self.reply(f"ИИ: {prompt}")
```

После регистрации обработчики событий всех платформ могут вызывать его:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handler(event):
    await event.ai_chat(event.get_text())
```

### Приоритет разрешения методов

При доступе к методам Event через атрибут, порядок разрешения следующий:

1. **Платформенные методы** (переопределения для текущей платформы)
2. **Методы с шаблоном** (методы, зарегистрированные для `"*"`)
3. **Встроенные методы** (`reply`, `confirm` и т.д.)
4. **Доступ по ключам словаря**

> Таким образом, методы с шаблоном могут переопределять встроенные методы (например, `reply`), но могут быть переопределены далее платформенными методами с тем же именем.

## Система приоритетов

Обработчики событий поддерживают приоритеты, чем больше число, тем выше приоритет:

```python
# Обработчик с высоким приоритетом выполняется первым
@message.on_message(priority=10)
async def high_priority_handler(event):
    pass

# Обработчик с низким приоритетом выполняется последним
@message.on_message(priority=0)
async def low_priority_handler(event):
    pass
```



====
高级主题
====


### Conversation 多轮对话

# Conversation Многошаговый диалог

Класс `Conversation` предоставляет удобные методы для многошагового взаимодействия в рамках одной сессии, что подходит для реализации навигационных действий, сбора информации, диалоговых вопросов и ответов и т.д.

## Создание диалога

Создание диалога через метод `conversation()` объекта `Event`:

```python
from ErisPulse.Core.Event import command

@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)

    await conv.say("🎮 Добро пожаловать на викторину!")

    answer = await conv.choose("Вопрос 1: Кто создатель Python?", [
        "Guido van Rossum",
        "James Gosling",
        "Dennis Ritchie",
    ])

    if answer is None:
        await conv.say("Время вышло, попробуйте снова!")
        return

    if answer == 0:
        await conv.say("Правильно!")
    else:
        await conv.say("Неверно, правильный ответ — Guido van Rossum")

    conv.stop()
```

## Основные API

### say(content, **kwargs)

Отправка сообщения, возвращает `self` для цепочки вызовов:

```python
await conv.say("Первая строка").say("Вторая строка").say("Третья строка")
```

Также можно указать способ отправки:

```python
await conv.say("https://example.com/image.jpg", method="Image")
```

### wait(prompt=None, timeout=None)

Ожидание ответа пользователя, возвращает объект `Event` или `None` (при таймауте):

```python
# Простое ожидание
resp = await conv.wait()
if resp:
    text = resp.get_text()

# Ожидание с подсказкой
resp = await conv.wait(prompt="Введите ваше имя:")

# Использование пользовательского таймаута (переопределяет таймаут по умолчанию)
resp = await conv.wait(prompt="Ответьте в течение 10 секунд:", timeout=10)
```

### confirm(prompt=None, **kwargs)

Ожидание подтверждения пользователя (да/нет), возвращает `True` / `False` / `None` (при таймауте):

```python
result = await conv.confirm("Удалить все данные?")
if result is True:
    await conv.say("Удалено")
elif result is False:
    await conv.say("Отменено")
else:
    await conv.say("Таймаут, ответ не получен")
```

Встроенные слова для подтверждения: `是/yes/y/确认/确定/好/ok/true/对/嗯/行/同意/没问题/可以/当然...`

Встроенные слова для отрицания: `否/no/n/取消/不/不要/不行/cancel/false/错/不对/别/拒绝...`

### choose(prompt, options, **kwargs)

Ожидание выбора пользователя из списка, возвращает индекс (0-based) или `None`:

```python
choice = await conv.choose("Выберите цвет:", ["красный", "зеленый", "синий"])
if choice is not None:
    colors = ["красный", "зеленый", "синий"]
    await conv.say(f"Вы выбрали {colors[choice]}")
```

Пользователь может выбрать по номеру (`1`/`2`/`3`) или по тексту (`красный`).

`options_format="auto"` (по умолчанию) автоматически выбирает стиль в зависимости от метода: Markdown → маркированный список, Html → нумерованный список, другие → текстовый список.
Также поддерживаются `"list"`、`"inline"`、`"md"`、`"html"` или пользовательская функция.

Поддержка `merge_prompt=True` для объединения в одно сообщение, а также позиционные плейсхолдеры для определения места вставки опций (по умолчанию `{options}`, можно изменить через `placeholder`):

```python
choice = await conv.choose(
    "## Выберите\n{options}",
    ["Опция A", "Опция B"],
    method="Markdown",
    merge_prompt=True,
)

# Пользовательский плейсхолдер
choice = await conv.choose(
    "Выберите: [choices]",
    ["Опция A", "Опция B"],
    placeholder="[choices]",
)
```

### collect(fields, **kwargs)

Сбор информации в несколько шагов, возвращает словарь данных или `None`:

```python
data = await conv.collect([
    {"key": "name", "prompt": "Введите имя"},
    {"key": "age", "prompt": "Введите возраст",
     "validator": lambda e: e.get("alt_message", "").strip().isdigit(),
     "retry_prompt": "Возраст должен быть числом, повторите ввод"},
    {"key": "city", "prompt": "Введите город"},
])

if data:
    await conv.say(f"Регистрация успешна!\nИмя: {data['name']}\nВозраст: {data['age']}\nГород: {data['city']}")
else:
    await conv.say("Регистрация прервана")
```

Конфигурация полей:

| Параметр | Описание | Значение по умолчанию |
|------|------|--------|
| `key` | Ключ поля (обязательно) | - |
| `prompt` | Подсказка | `"Введите {key}"` |
| `validator` | Функция валидации, принимает Event, возвращает bool | Нет |
| `retry_prompt` | Подсказка при неудачной валидации | `"Некорректный ввод, повторите"` |
| `max_retries` | Максимальное количество попыток | 3 |
| `condition` | Условная функция, принимает словарь уже собранных данных, возвращает bool | Нет |

**Условные поля**: с помощью `condition` можно реализовать динамическую форму, только при выполнении условия поле будет запрашиваться:

```python
data = await conv.collect([
    {"key": "has_car", "prompt": "Есть ли у вас машина? (да/нет)"},
    {"key": "car_brand", "prompt": "Введите марку автомобиля",
     "condition": lambda d: d.get("has_car", "").lower() in ("да", "yes", "y")},
])
```

### stop()

Ручное завершение диалога, устанавливает `is_active` в `False`:

```python
conv.stop()
```

### is_active

Проверка активности диалога:

```python
if conv.is_active:
    await conv.say("Диалог активен")
```

## Управление активностью

Диалог автоматически становится неактивным в следующих случаях:

1. Вызов метода `stop()`
2. `wait()` возвращает `None` из-за таймаута
3. `collect()` возвращает `None` из-за таймаута или исчерпания попыток повтора

После неактивации все методы взаимодействия (`wait`/`confirm`/`choose`/`collect`) немедленно возвращают `None`, без ожидания ввода пользователя.

## Ветвления и переходы

### @conv.branch(name) декоратор

Использование `branch()` для регистрации ветвей диалога, переход между ветвями через `goto()`:

```python
@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)

    @conv.branch("main")
    async def main_menu():
        await conv.say("=== Главное меню ===\n1. Личная информация\n2. Настройки\n3. Выйти")
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
        await conv.say("=== Личная информация ===\nИмя: Alice\n0. Назад")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    @conv.branch("settings")
    async def settings():
        await conv.say("=== Настройки ===\n1. Переключатель уведомлений\n0. Назад")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    await conv.start()  # Начинаем с первой зарегистрированной ветви
```

### conv.start(name=None)

Запуск диалога, по умолчанию с первой зарегистрированной ветви:

```python
await conv.start()          # С первой ветви
await conv.start("settings") # С указанной ветви
```

## Контекст и сохранение состояния

### conv.context

Внутренний словарь `context` для сохранения состояния между ветвями:

```python
@conv.branch("step1")
async def step1():
    conv.context["username"] = resp.get_text().strip()
    await conv.goto("step2")

@conv.branch("step2")
async def step2():
    name = conv.context.get("username", "неизвестен")
    await conv.say(f"Привет, {name}!")
```

### save() / resume() / clear_saved()

Поддержка сохранения состояния диалога, возможность восстановления после таймаута или прерывания:

```python
# Сохранение состояния диалога
conv_id = conv.save()
# conv_id = "user_123_group_456"  # Генерируется на основе пользователя и группы

# ... позже в том же сеансе ...
conv2 = event.conversation()
if conv2.resume():
    await conv2.say("Добро пожаловать обратно! Продолжим предыдущий диалог")
else:
    await conv2.say("Предыдущий диалог не найден")

# Очистка сохраненного диалога
conv.clear_saved()
```

## Типичные сценарии

### Регистрация с подсказками

```python
@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)

    await conv.say("Добро пожаловать на регистрацию!")

    data = await conv.collect([
        {"key": "username", "prompt": "Введите имя пользователя (3-20 символов)",
         "validator": lambda e: 3 <= len(e.get_text().strip()) <= 20},
        {"key": "email", "prompt": "Введите адрес электронной почты",
         "validator": lambda e: "@" in e.get_text() and "." in e.get_text(),
         "retry_prompt": "Некорректный формат почты, повторите ввод"},
    ])

    if not data:
        await event.reply("Регистрация отменена")
        return

    confirmed = await conv.confirm(
        f"Подтвердите регистрационные данные?\nИмя: {data['username']}\nПочта: {data['email']}"
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
    await conv.say("Вход в диалоговый режим, введите «выход» для завершения")

    while conv.is_active:
        resp = await conv.wait()
        if resp is None:
            await conv.say("Таймаут, диалог завершен")
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



### MessageBuilder 详解

# Подробное руководство по MessageBuilder

`MessageBuilder` — это инструмент для построения структурированных сообщений, соответствующих стандарту OneBot12, предоставленный ErisPulse. Он используется для построения структурированного содержания сообщений и работает в связке с `Send.Raw_ob12()`.

## Способы импорта

`MessageBuilder` поддерживает два способа импорта (результат одинаковый, рекомендуется использовать первый):

```python
from ErisPulse.Core.Event import MessageBuilder        # Рекомендуемый способ, импорт через пакет
from ErisPulse.Core.Event.message_builder import MessageBuilder  # Прямой импорт модуля
```

## Двухрежимная система

MessageBuilder предоставляет два режима использования, реализованных с помощью механизма описателей Python (`__get__`), чтобы обеспечить различное поведение на уровне класса и экземпляра: при вызове метода через класс, `__get__` возвращает результат выполнения статического метода; при вызове через экземпляр возвращается `self` для поддержки цепочки вызовов.

### Режим цепочечных вызовов (экземпляр)

Используется путем создания экземпляра `MessageBuilder()`. Каждый метод возвращает `self`, что позволяет использовать цепочку вызовов, и для получения списка сообщений используется `.build()`:

```python
from ErisPulse.Core.Event.message_builder import MessageBuilder

segments = (
    MessageBuilder()
    .text("Привет!")
    .image("https://example.com/photo.jpg")
    .build()
)
# [
#     {"type": "text", "data": {"text": "Привет!"}},
#     {"type": "image", "data": {"file": "https://example.com/photo.jpg"}}
# ]
```

### Режим быстрого построения (статический)

Методы вызываются напрямую через класс, каждый метод возвращает список сообщений, что подходит для построения одиночных сообщений:

```python
# Непосредственно возвращается list[dict], без .build()
segments = MessageBuilder.text("Привет!")
# [{"type": "text", "data": {"text": "Привет!"}}]
```

## Типы сообщений

| Метод | Тип | Параметры данных | Описание |
|------|------|---------|------|
| `text(text)` | text | `text` | Текстовое сообщение |
| `image(file)` | image | `file` | Сообщение с изображением |
| `audio(file)` | audio | `file` | Аудиосообщение |
| `video(file)` | video | `file` | Видеосообщение |
| `file(file, filename?)` | file | `file`, `filename` | Сообщение с файлом |
| `mention(user_id, user_name?)` | mention | `user_id`, `user_name` | Упоминание пользователя |
| `at(user_id, user_name?)` | mention | `user_id`, `user_name` | Алиас для `mention` |
| `reply(message_id)` | reply | `message_id` | Ответ на сообщение |
| `at_all()` | mention_all | - | Упоминание всех участников |
| `custom(type, data)` | пользовательский | пользовательский | Пользовательский тип сообщения |

## Использование в связке с Send

Построенный список сообщений отправляется через `Send.Raw_ob12()`:

```python
from ErisPulse import sdk
from ErisPulse.Core.Event.message_builder import MessageBuilder

# Построение сообщений в цепочке и отправка
segments = (
    MessageBuilder()
    .mention("user123", "张三")
    .text(" Пожалуйста, посмотрите на это изображение")
    .image("https://example.com/photo.jpg")
    .build()
)
await sdk.adapter.myplatform.Send.To("group", "group456").Raw_ob12(segments)
```

### Использование в ответ на событие

```python
from ErisPulse.Core.Event import command

@command("report")
async def report_handler(event):
    await event.reply_ob12(
        MessageBuilder()
        .text("📊 Сводка ежедневного отчета\n")
        .text("Выполненные задачи сегодня: 5\n")
        .text("Задачи в процессе: 3")
        .build()
    )
```

## Вспомогательные методы

### copy()

Копирует текущий билдер, что позволяет создавать несколько вариантов сообщений на основе одного и того же содержания:

```python
base = MessageBuilder().text("Базовое содержание").mention("admin")

# Создание различных сообщений на основе одного и того же префикса
msg1 = base.copy().text(" Вариант A").build()
msg2 = base.copy().text(" Вариант B").image("img.jpg").build()
```

### clear()

Очищает добавленные сообщения, что позволяет повторно использовать один и тот же билдер:

```python
builder = MessageBuilder()

for user_id in ["user1", "user2", "user3"]:
    builder.clear()
    msg = builder.mention(user_id).text(" Привет!").build()
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

## Пользовательские сообщения

Метод `custom()` используется для добавления расширенных сообщений, специфичных для платформы:

```python
# Добавление специфичного для платформы сообщения
segments = (
    MessageBuilder()
    .text("Пожалуйста, заполните форму:")
    .custom("yunhu_form", {"form_id": "12345"})
    .build()
)
```

> Пользовательские сообщения действительны только в адаптерах соответствующей платформы, другие адаптеры игнорируют неизвестные типы сообщений.

## Полный пример

### Сообщение с несколькими элементами

```python
segments = (
    MessageBuilder()
    .reply(event.get_id())                    # Ответ на исходное сообщение
    .mention(event.get_user_id())             # Упоминание отправителя
    .text(" Это результат вашего запроса:\n")             # Текстовое сообщение
    .image("https://example.com/chart.png")   # Изображение
    .text("\nПодробные данные см. в приложении:")
    .file("https://example.com/data.csv", filename="data.csv")
    .build()
)
await event.reply_ob12(segments)
```

### Смешанное использование статического фабрика и цепочки вызовов

```python
# Быстрое построение простого сообщения
simple_msg = MessageBuilder.text("Простой текст")

# Цепочечное построение сложного сообщения
complex_msg = (
    MessageBuilder()
    .at_all()
    .text(" 📢 Объявление:")
    .text("Сегодня в 15:00 состоится собрание")
    .build()
)
```



### HTTP 客户端

# Сетевой клиент

ErisPulse предоставляет единый сетевой клиент, объединяющий HTTP-запросы, WebSocket-соединения и управление пулом соединений. Модули и адаптеры **должны** использовать этот клиент, а не импортировать сторонние библиотеки, такие как `aiohttp` / `httpx` / `requests`.

## Обзор

Основные функции сетевого клиента:

- **Единый интерфейс**: предоставляет методы `get` / `post` / `put` / `delete` / `patch` / `request`
- **WebSocket-клиент**: через `ws_connect` устанавливает WebSocket-соединение
- **Автоматическое логирование**: все запросы автоматически записываются в лог и статистику
- **Интеграция с жизненным циклом**: каждый запрос вызывает событие `client.request`, а WebSocket-соединение — `client.ws.connect`
- **Поддержка повторных попыток**: настраиваемое количество автоматических повторов и интервал
- **Управление таймаутами**: независимые таймауты подключения и запроса
- **Повторное использование соединений**: управление пулом соединений на основе aiohttp.ClientSession
- **Система исключений**: aiohttp-исключения автоматически преобразуются в исключения ErisPulse (система ClientError)

## Быстрый старт

### HTTP-запросы

```python
from ErisPulse.Core import client

# GET-запрос
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST-запрос
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket-соединение

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## HttpResponse

Все методы запросов возвращают объект `HttpResponse`:

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP-статус (например, 200, 404)
resp.reason       # str | None - описание статуса (например, "OK")
resp.headers      # Заголовки ответа (регистронезависимые)
resp.content_type # str | None - Content-Type
resp.url          # Окончательный URL (может измениться из-за редиректов)
resp.raw          # Оригинальный ответ (aiohttp.ClientResponse)

# Чтение тела ответа
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # Парсинг JSON
text = await resp.text("gbk")  # Указание кодировки
```

## Методы запросов

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# JSON-тело запроса
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# Тело запроса в формате формы
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# Сырые данные
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# Загрузка файлов (используя параметр files, без импорта aiohttp)
# Формат: {имя_поля: объект_файла/bytes/(имя_файла, файл)/(имя_файла, файл, тип_контента)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "Аватар"},            # Опционально: одновременно с обычными полями формы
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# Упрощённый синтаксис: передача объекта файла напрямую
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# Загрузка данных из памяти (без сохранения на диск)
import io

resp = await client.post(
    "https://api.example.com/upload",
    files={"file": ("data.txt", io.BytesIO(b"file content"), "text/plain")},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### Общий запрос

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## Параметры запроса

### Параметры HTTP-запроса

| Параметр | Тип | Описание |
|------|------|------|
| `url` | `str` | URL запроса |
| `params` | `dict[str, str]` | Параметры запроса (опционально) |
| `headers` | `dict[str, str]` | Дополнительные заголовки (опционально) |
| `data` | `Any` | Тело запроса (форма или сырые данные) (опционально) |
| `json` | `Any` | Тело запроса в формате JSON (опционально) |
| `files` | `dict[str, Any]` | Поля для загрузки файлов (опционально, автоматически формирует multipart/form-data) |
| `timeout` | `float` | Таймаут запроса (секунды) (опционально, переопределяет значение по умолчанию) |
| `max_retries` | `int` | Максимальное количество повторных попыток (опционально, переопределяет значение по умолчанию) |

### Параметры ws_connect

| Параметр | Тип | Описание |
|------|------|------|
| `url` | `str` | URL WebSocket-сервера |
| `headers` | `dict[str, str]` | Дополнительные заголовки (опционально) |
| `heartbeat` | `float` | Интервал в секундах для пингов (опционально) |

## Таймауты и повторные попытки

```python
from ErisPulse.Core import HttpClient

# Создание клиента с пользовательскими таймаутами
client = HttpClient(
    timeout=60,           # Общий таймаут запроса 60 секунд
    connect_timeout=5,    # Таймаут подключения 5 секунд
    max_retries=3,        # Автоматические повторные попытки 3 раза
    retry_delay=2,        # Интервал между повторами 2 секунды
)

# Переопределение таймаута для одного запроса
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

## Настройка заголовков по умолчанию

```python
client = HttpClient(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## Статистика запросов

```python
from ErisPulse.Core import client

# Просмотр статистики
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# Сброс статистики
client.reset_stats()
```

## События жизненного цикла

### События HTTP-запросов

Событие `client.request` вызывается после завершения каждого запроса, используется для мониторинга:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### События WebSocket-соединений

Событие `client.ws.connect` вызывается после установления каждого WebSocket-соединения:

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS-соединение: {event_data['url']}")
```

## Контекстный менеджер

```python
# Использование как контекстный менеджер, автоматическое закрытие сессии
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket-клиент

WebSocket-клиент создается через `client.ws_connect()`, возвращается объект `ClientWebSocket`. Клиент и серверная часть WebSocket разделяют один и тот же базовый класс `WebSocketConnectionBase`, интерфейсы send/receive/iter полностью идентичны.

### Основное использование

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### Прием сообщений

#### Рекомендуемые методы (уровень выше)

Автоматически фильтруют типы сообщений, при разрыве соединения выбрасывают `WebSocketDisconnect`:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# Получение одного сообщения
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# Итерация по сообщениям (автоматически останавливается при разрыве)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### Низкоуровневые методы

Использование `receive()` и `iter_messages()` для обработки сообщений в их исходном виде, можно различать типы TEXT / BINARY / CLOSE / ERROR:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# Получение одного сообщения
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# Итерация по сообщениям (автоматически останавливается при CLOSE/ERROR)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"Текст: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"Двоичные данные: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` — единый тип WebSocket-сообщения, не зависит от底层 библиотеки:

| Свойство | Тип | Описание |
|------|------|------|
| `type` | `str` | Тип сообщения: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | Данные сообщения |

### Свойства ClientWebSocket

| Свойство | Тип | Описание |
|------|------|------|
| `url` | `URL` | URL соединения |
| `headers` | `Headers` | Заголовки ответа |
| `closed` | `bool` | Закрыто ли соединение |
| `raw` | `object` | Оригинальный объект (aiohttp.ClientWebSocketResponse) |

### Хуки жизненного цикла

Аналогично `WebSocketConnection` сервера, поддерживаются обратные вызовы `on_disconnect` и `on_error`:

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"Соединение разорвано: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"Ошибка соединения: {error}")
```

### Закрытие соединения

```python
await ws.close(code=1000, reason="Normal closure")
```

## Система исключений

ErisPulse определяет единый иерархический уровень исключений, запросы, инициированные через `sdk.client`, автоматически преобразуют исключения aiohttp в исключения ErisPulse.

> **Обратная совместимость**: старые модули/адаптеры, использующие напрямую `aiohttp.ClientSession`, не затронуты. Преобразование исключений происходит только при использовании `sdk.client`, код, использующий напрямую aiohttp, по-прежнему ловит исключения `aiohttp.ClientError` и другие оригинальные исключения. Оба способа могут сосуществовать.

### Иерархия исключений

```
ErisPulseError
├── ClientError                  # Базовый класс для всех исключений HTTP/WS-клиента
│   ├── ClientConnectionError    # Ошибка подключения (DNS, соединение отклонено, недоступность сети)
│   ├── ClientTimeoutError       # Таймаут подключения или запроса
│   └── HTTPStatusError          # Ошибки HTTP 4xx/5xx
└── WebSocketError               # Базовый класс WebSocket-исключений
    └── WebSocketDisconnect      # Отключение WebSocket (общий для клиента и сервера)
```

### Обработка исключений

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import (
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)

# Обработка исключений HTTP-запросов
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("Невозможно подключиться к серверу")
except ClientTimeoutError:
    print("Запрос превысил таймаут")
except ClientError as e:
    print(f"Запрос не удался: {e}")

# Обработка исключений WebSocket
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"Соединение разорвано: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"Ошибка WebSocket: {e}")
```

### Единое перехватывание

Использование `ClientError` для перехвата всех исключений HTTP/WS-клиента:

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"Ошибка клиента: {e}")
```

### HTTPStatusError

Когда нужно проверить статус-код после запроса и выбросить исключение, можно использовать `HTTPStatusError`:

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## Использование в адаптерах

Адаптеры могут использовать глобальный клиент или создавать экземпляр клиента для отправки платформенных API-запросов:

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.errors import ClientError

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        try:
            resp = await client.post(
                f"https://api.platform.com/{endpoint}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return await resp.json()
        except ClientError as e:
            self.logger.error(f"Ошибка вызова API: {e}")
            raise
```

> Также можно использовать `from ErisPulse import sdk` и `sdk.client`, результат будет идентичен.

## Лучшие практики

1. **Предпочтительное использование глобального клиента**: получение глобального синглтона через `from ErisPulse.Core import client` для упрощения управления и мониторинга фреймворком
2. **Избегайте прямого импорта aiohttp**: использование `client` вместо `aiohttp.ClientSession`, при замене底层 реализации код не потребует изменений. Старый код, использующий напрямую aiohttp, по-прежнему работает, оба способа могут сосуществовать
3. **Использование системы исключений ErisPulse**: при запросах через `sdk.client` ловите `ClientError`, а не `aiohttp.ClientError`, чтобы код не зависел от конкретной HTTP-библиотеки. Код, использующий напрямую aiohttp, не затронут
4. **Разумная настройка таймаутов**: установка разумных таймаутов в зависимости от скорости ответа API, чтобы избежать длительных блокировок
5. **Использование механизма повторных попыток**: включение повторов для нестабильных API, повышение надежности
6. **Мониторинг статистики запросов**: использование `sdk.client.stats` или событий жизненного цикла `client.request` для мониторинга запросов
7. **Использование высокого уровня методов WebSocket**: предпочтительное использование `iter_text` / `iter_json` и других высокого уровня методов, использование `iter_messages` только при необходимости различать типы сообщений



### SQL 查询构建器

# SQL Query Builder

Модуль хранения (Storage) в ErisPulse предоставляет универсальный конструктор SQL-запросов в стиле цепочки вызовов (chain-style), поддерживающий создание пользовательских таблиц, а также операции выборки, обновления и удаления.

## Архитектура

```
Bases/storage.py                    Core/storage.py
┌─────────────────────┐             ┌──────────────────────────┐
│  BaseStorage (ABC)  │◄────────────│  StorageManager          │
│  BaseQueryBuilder   │             │  (конкретная реализация  │
│    (ABC)            │             │   на базе SQLite)        │
└─────────────────────┘             │                          │
                                    │  SQLiteQueryBuilder      │
                                    │  AlterTableBuilder       │
                                    └──────────────────────────┘
```

- `BaseStorage` / `BaseQueryBuilder` — это абстрактные базовые классы, определяющие единый интерфейс, который поддерживает расширение для других носителей хранения (Redis, MySQL и т. д.)
- `StorageManager` — текущая конкретная реализация на базе SQLite, полностью сохраняющая обратную совместимость

## Импорт

```python
from ErisPulse import sdk
# или
from ErisPulse.Core import storage

# Базовые классы ABC (для типизации или пользовательской реализации)
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## Управление таблицами

### Создание таблицы

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0",
    "email": "TEXT"
})
```

### Проверка существования таблицы

```python
if sdk.storage.HasTable("users"):
    print("Таблица users существует")
```

### Удаление таблицы

```python
sdk.storage.DropTable("users")
```

### Изменение структуры таблицы

```python
# Добавление столбца
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()

# Переименование таблицы
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# Цепочка нескольких операций
sdk.storage.AlterTable("users") \
    .AddColumn("phone", "TEXT") \
    .AddColumn("address", "TEXT") \
    .Execute()
```

## Запросы в стиле цепочки (Chain Queries)

### Вставка данных

```python
# Вставка одной строки (передача словаря)
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# Массовая вставка (передача списка словарей)
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
    {"name": "Dave", "age": 40}
]).Execute()
```

### Запрос данных

> **Важно**: `Select()` возвращает `list[tuple]` (список кортежей), а не словарь. Вам необходимо получать значения, обращаясь по индексу в порядке следования столбцов.

```python
# Запрос всех столбцов
rows = sdk.storage.Table("users").Select().Execute()
# rows: [(1, "Alice", 30), (2, "Bob", 25), ...]

# Запрос указанных столбцов
rows = sdk.storage.Table("users").Select("name", "age").Execute()
# rows: [("Alice", 30), ("Bob", 25), ...]

# Получение значения по индексу
for row in rows:
    name = row[0]   # "Alice"
    age = row[1]    # 30
```

#### Преобразование кортежей в словари

```python
columns = ["id", "name", "age"]
rows = sdk.storage.Table("users").Select(*columns).Execute()

# Способ 1: zip внутри цикла
for row in rows:
    record = dict(zip(columns, row))
    print(record["name"], record["age"])

# Способ 2: преобразование списка кортежей в список словарей за один раз
records = [dict(zip(columns, row)) for row in rows]
```

#### Получение одной записи

```python
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ExecuteOne()

# row — это кортеж или None
if row is not None:
    name = row[0]  # "Alice"
    age = row[1]   # 30
```

### Фильтрация по условиям

> `Where(condition, *params)` поддерживает передачу нескольких параметров, соответствующих нескольким заполнителям `?`.

```python
# Одно условие (один заполнитель, один параметр)
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 18) \
    .Execute()

# Использование нескольких заполнителей в одном Where
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ? AND age < ?", 20, 40) \
    .Execute()

# Многократный вызов Where (связано оператором AND)
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 20) \
    .Where("age < ?", 40) \
    .Execute()
```

### Сортировка, пагинация

```python
# По возрастанию
rows = sdk.storage.Table("users").Select("name", "age") \
    .OrderBy("name") \
    .Execute()

# По убыванию
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("age", desc=True) \
    .Execute()

# Пагинация
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("id") \
    .Limit(10) \
    .Offset(20) \
    .Execute()
```

### Обновление данных

```python
# Обновление по условию
sdk.storage.Table("users") \
    .Update({"age": 31}) \
    .Where("name = ?", "Alice") \
    .Execute()

# Полное обновление
sdk.storage.Table("users") \
    .Update({"status": "active"}) \
    .Execute()
```

### Удаление данных

```python
# Удаление по условию
sdk.storage.Table("users") \
    .Delete() \
    .Where("name = ?", "Bob") \
    .Execute()

# Полное удаление
sdk.storage.Table("users").Delete().Execute()
```

### Подсчет и проверка существования

```python
# Подсчет
count = sdk.storage.Table("users").Count()
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# Проверка существования
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()
```

## Повторное использование условий запроса

Используйте `copy()` для глубокого копирования конструктора для повторного использования базовых условий:

```python
base = sdk.storage.Table("users").Where("age > ?", 20)

# Запрос на основе тех же условий
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()

# Подсчет на основе тех же условий
count = base.copy().Count()

# Проверка существования на основе тех же условий
exists = base.copy().Where("name = ?", "Alice").Exists()
```

## Сброс конструктора

```python
builder = sdk.storage.Table("users").Select("name").Where("age > ?", 18)
builder.clear()

# Перестроение запроса
builder.Select("name", "age").Where("name = ?", "Alice")
rows = builder.Execute()
```

## Использование в транзакциях

Операции в стиле цепочки полностью поддерживают транзакции:

```python
# Подтверждение транзакции
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Eve", "age": 22}).Execute()
    sdk.storage.Table("users").Update({"age": 23}).Where("name = ?", "Eve").Execute()

# Пример отката
try:
    with sdk.storage.transaction():
        sdk.storage.Table("users").Delete().Where("name = ?", "Alice").Execute()
        raise Exception("force rollback")
except Exception:
    pass
# Запись Alice все еще существует
```

## Описание возвращаемых значений

| Операция | Тип возвращаемого значения | Описание |
|------|---------|------|
| `Select().Execute()` | `list[tuple]` | Список кортежей, упорядоченных по столбцам |
| `Select().ExecuteOne()` | `tuple \| None` | Один кортеж или None |
| `Insert().Execute()` | `int` | Количество затронутых строк |
| `InsertMulti().Execute()` | `int` | Количество вставленных строк |
| `Update().Execute()` | `int` | Количество затронутых строк |
| `Delete().Execute()` | `int` | Количество затронутых строк |
| `Count()` | `int` | Количество совпавших строк |
| `Exists()` | `bool` | Наличие записи |

### Примеры обработки возвращаемых значений

```python
# Select возвращает кортежи, берем значения по индексу
rows = sdk.storage.Table("users").Select("name", "age").Execute()
first_name = rows[0][0]  # Имя в первой строке, первом столбце
first_age = rows[0][1]   # Возраст в первой строке, втором столбце

# Рекомендуется: преобразование в словарь с помощью списка имен столбцов + zip, код более читаем
cols = ["name", "age"]
rows = sdk.storage.Table("users").Select(*cols).Execute()
for row in rows:
    d = dict(zip(cols, row))
    print(d["name"], d["age"])

# ExecuteOne возвращает один кортеж или None
row = sdk.storage.Table("users").Select("name").Where("id = ?", 1).ExecuteOne()
name = row[0] if row else None

# Insert/Update/Delete возвращают количество затронутых строк
affected = sdk.storage.Table("users").Delete().Where("age < ?", 18).Execute()
print(f"Удалено записей: {affected}")
```

## Параметризованные запросы

Все параметры WHERE используют заполнитель `?`, параметры передаются как последовательные аргументы метода `Where()` (**не** как кортеж или список):

```python
# Верно ✓ — передача нескольких параметров по отдельности
sdk.storage.Table("users").Where("age > ? AND name = ?", 18, "Alice").Execute()

# Верно ✓ — многократный вызов Where
sdk.storage.Table("users").Where("age > ?", 18).Where("name = ?", "Alice").Execute()

# Ошибочно ✗ — не передавайте кортеж
sdk.storage.Table("users").Where("age > ? AND name = ?", (18, "Alice")).Execute()
# Это превратит весь кортеж в значение для первого заполнителя

# Ошибочно ✗ — существует риск SQL-инъекции
sdk.storage.Table("users").Where(f"name = '{user_input}'").Execute()
```

### Правила передачи параметров Where

```python
# Where(condition: str, *params: Any)
# params — переменное число аргументов, передаются по одному

# Один параметр
.Where("name = ?", "Alice")

# Несколько параметров
.Where("age > ? AND age < ?", 18, 60)

# Запрос LIKE
.Where("name LIKE ?", "A%")

# Запрос IN (требуется вручную построить заполнители)
.Where("name IN (?, ?, ?)", "Alice", "Bob", "Charlie")
```

## Пользовательский бэкенд (хранилище)

Наследуйте `BaseStorage` и `BaseQueryBuilder` для реализации пользовательского бэкенда:

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

class MyQueryBuilder(BaseQueryBuilder):
    def Execute(self):
        # Реализация конкретной логики выполнения
        ...

    def ExecuteOne(self):
        ...

    def Count(self):
        ...

    def Exists(self):
        ...


class MyStorage(BaseStorage):
    def get(self, key, default=None):
        ...

    def set(self, key, value):
        ...

    # Реализация других абстрактных методов...
    def Table(self, table_name):
        return MyQueryBuilder(self, table_name)
```



### 路由系统

# Маршрутизатор

Маршрутизатор ErisPulse обеспечивает единое управление HTTP и WebSocket маршрутизацией, поддерживает регистрацию маршрутов и управление жизненным циклом с несколькими адаптерами. В основе лежит абстрактный уровень, реализованный (в настоящее время FastAPI + Uvicorn).

## Обзор

Основные функции маршрутизатора:

- **Декораторы маршрутов**: поддержка быстрой регистрации с помощью декораторов `@http` / `@get` / `@post` / `@put` / `@delete` / `@ws`
- **Автоматическая инъекция**: обработчики маршрутов не требуют импорта типов FastAPI, фреймворк автоматически инжектирует абстрактные объекты
- **Группировка маршрутов**: поддержка `RouteGroup` с префиксом и номером версии
- **Маршрутизация промежуточного ПО**: поддержка шаблонного сопоставления запросов с помощью glob
- **Ограничение скорости**: встроенная система ограничения скорости с использованием скользящего окна
- **Поддержка CORS**: включение кросс-доменных ресурсов одним нажатием
- **Безопасные заголовки**: автоматическое добавление безопасных заголовков ответа
- **Автоматическая документация**: интерактивная документация на основе OpenAPI
- **Поддержка WebSocket**: полное управление подключениями WebSocket, пользовательская аутентификация и хуки жизненного цикла
- **Интеграция жизненного цикла**: глубокая интеграция с системой жизненного цикла ErisPulse
- **Поддержка SSL/TLS**: поддержка безопасных соединений HTTPS и WSS
- **Главная страница**: поддержка регистрации быстрых кнопок модулей на корневом маршруте `/`, поддержка локализации

## Абстрактные типы

ErisPulse предоставляет абстрактные типы для сервера, позволяющие модулям не зависеть напрямую от FastAPI:

| Абстрактный тип | Соответствие FastAPI | Описание |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | Обертка для HTTP-запроса, полная совместимость по интерфейсу |
| `WebSocketConnection` | `fastapi.WebSocket` | Обертка для WebSocket-подключения, дополнительно предоставляет хуки жизненного цикла |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | Исключение разрыва WebSocket-соединения |

> `WebSocketConnection` наследуется от `WebSocketConnectionBase`, разделяя с клиентским WebSocket (`ClientWebSocket`) одинаковые интерфейсы send/receive/iter/close. Клиентский и серверный WebSocket могут использовать одинаковый бизнес-логический код.
>
> Через свойство `.raw` можно получить доступ к базовому объекту FastAPI. Код, использующий типы FastAPI напрямую, также полностью совместим.

## Декораторы маршрутов (рекомендуется)

### HTTP-декораторы

```python
from ErisPulse.Core import router
@router.get("my_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}

# Также можно явно указать абстрактный тип
from ErisPulse.Core import HttpRequest

@router.post("my_module", "/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("my_module", "/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("my_module", "/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **Правило автоматической инъекции**: когда первый параметр обработчика имеет имя `request` или `req` и не имеет аннотации типа FastAPI, фреймворк автоматически инжектирует `HttpRequest`. Обработчики без параметров или с параметрами, не являющимися именем запроса, не затрагиваются.

### WebSocket-декораторы

```python
from ErisPulse.Core import WebSocketConnection, WebSocketDisconnect

# Базовый WebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket с хуками жизненного цикла
@router.ws("my_module", "/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"Пользователь отключился: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"Ошибка соединения: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# WebSocket с аутентификацией
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **Примечание**: WebSocket-обработчики и обработчики аутентификации также поддерживают автоматическую инъекцию. Без аннотации параметров можно получить `WebSocketConnection`. Указание `fastapi.WebSocket` также позволяет передавать оригинальный объект, но рекомендуется использовать абстрактные типы.

## Традиционный способ регистрации

```python
async def hello_handler(request):
    return {"message": "Hello World"}

# Базовая регистрация
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# Регистрация с ограничением скорости и информацией о документации
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="Интерфейс данных",
    tags=["API"],
)
```

### WebSocket-регистрация

```python
from ErisPulse.Core import WebSocketConnection

async def websocket_handler(ws: WebSocketConnection):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# Базовая регистрация
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# Регистрация с аутентификацией (рекомендуется)
async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

**Описание параметров:**

| Параметр | Описание | Значение по умолчанию |
|------|------|--------|
| `module_name` | Имя модуля (обязательно) | - |
| `path` | Путь WebSocket | - |
| `handler` | Функция обработки | - |
| `auth_handler` | Функция аутентификации, возвращающая `False` автоматически закрывает соединение | `None` |
| `auto_accept` | Автоматически ли вызывать `accept()` | `True` |

> **Рекомендуется**: использовать `auth_handler` для подтверждения соединения, а не отключать `auto_accept`. Установите `auto_accept=False` только в том случае, если вам нужно полностью контролировать процесс соединения.

## Хуки жизненного цикла WebSocket

`WebSocketConnection` предоставляет обратные вызовы для отключения и ошибок, без необходимости вручную использовать try/catch:

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # Регистрация с помощью декоратора
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"Причина отключения: {reason}")

    # Также можно вызывать напрямую
    async def on_err(ws, error=""):
        print(f"Ошибка: {error}")
    ws.on_error(on_err)

    # Обычная бизнес-логика
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## Группировка маршрутов

```python
# Создание маршрутизатора с префиксом
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# Фактический путь: /my_module/v1/users
```

## Промежуточное ПО маршрутов

Промежуточное ПО поддерживает шаблоны glob для сопоставления путей:

```python
@router.middleware("/my_module/*")
async def auth_middleware(request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    return await call_next(request)

@router.middleware("/my_module/admin/*")
async def admin_middleware(request, call_next):
    return await call_next(request)
```

## Идентификатор запроса (X-Request-ID)

Начиная с версии 2.7.0, каждый HTTP-запрос будет содержать идентификатор `X-Request-ID`, используемый для логирования и трассировки связей:

- **Правило генерации**: приоритетно используется заголовок `X-Request-ID`, переданный клиентом (для распределенных трассировок); в противном случае генерируется UUID
- **Ответный заголовок**: ответ будет возвращать `X-Request-ID`, что позволяет клиенту сопоставлять запросы с логами
- **События жизненного цикла**: к данным событий `server.request` и `server.response` добавляется поле `request_id`

```python
# В модуле отслеживание событий запроса, сопоставление запросов-ответов по request_id
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

Клиент может использовать собственный идентификатор для трассировки между сервисами:

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## Ограничение скорости

Использование алгоритма скользящего окна для ограничения скорости маршрутов:

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

Формат ограничения скорости: `{количество}/{временной интервал}`, например `10/minute`, `100/hour`.

## Конфигурация CORS

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Также можно настроить через `config.toml`:

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## Безопасные заголовки

```python
router.setup_security_headers()
```

Автоматически добавляются безопасные заголовки, такие как `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` и др.

Также можно настроить через `config.toml`:

```toml
[router.security]
enabled = true
```

## Автоматическая документация

Router по умолчанию включает интерактивную документацию OpenAPI:

```python
# Отключение документации
router.disable_docs()

# Настройка информации документации
router.set_docs_info(
    title="My API",
    description="API документация",
    version="1.0.0"
)
```

## Обработка путей

Маршруты автоматически добавляют имя модуля как префикс, чтобы избежать конфликтов:

```python
# Регистрация пути "/api" для модуля "my_module"
# Фактический доступный путь: "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## Системные маршруты

Маршрутизатор автоматически предоставляет следующие системные маршруты:

### Проверка здоровья

```
GET /health
# Возвращает:
{"status": "ok", "service": "ErisPulse Router"}
```

### Главная страница

```
GET /
# Возвращает страницу бренда ErisPulse
```

На корневом маршруте `/` отображается страница бренда ErisPulse, автоматически проверяется доступность Dashboard и добавляются кнопки входа.

## Главная кнопка

Маршрутизатор позволяет внешним модулям регистрировать кнопки быстрого доступа на корневом маршруте `/`, что облегчает пользователям быстрый доступ к страницам управления модулями.

### Регистрация кнопки

```python
# Простая регистрация
router.register_home_entry(
    name="Моя панель",
    url="/mymodule/admin",
)

# Регистрация с иконкой (SVG)
router.register_home_entry(
    name="Консоль",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# Регистрация с поддержкой локализации (формат словаря i18n проекта)
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "Моя панель"},
    url="/mymodule/admin",
)
```

**Описание параметров:**

| Параметр | Тип | Описание | Обязательно |
|------|------|------|------|
| `name` | `str` / `dict` | Текст отображения кнопки; при передаче словаря `{"i18n": "key", "default": "текст"}` используется локализация | Да |
| `url` | `str` | Ссылка кнопки | Да |
| `icon_svg` | `str` | Необязательный SVG-иконный маркер | Нет |

### Автоматическая регистрация Dashboard

При обнаружении доступности `sdk.Dashboard`, маршрутизатор автоматически добавляет кнопку Dashboard в начало списка входов, без необходимости ручной регистрации.

## Интеграция жизненного цикла

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"Сервер запущен: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("Сервер останавливается...")
```

## Лучшие практики

1. **Предпочтение абстрактных типов**: использование `HttpRequest` / `WebSocketConnection` вместо `fastapi.Request` / `fastapi.WebSocket`, избегание жесткой зависимости
2. **Использование автоматической инъекции**: первый параметр обработчика должен называться `request` или `req`, без аннотации типа можно получить `HttpRequest`
3. **Явный передача module_name**: первый параметр декоратора должен быть именем модуля, не может быть опущен
4. **Использование группировки маршрутов**: использование `group()` для организации нескольких маршрутов одного модуля
5. **Рассмотрение безопасности**: реализация механизмов аутентификации и безопасных заголовков для чувствительных операций
6. **Разумное ограничение скорости**: установка ограничения скорости для высокочастотных интерфейсов
7. **Использование хуков жизненного цикла**: обработка исключений WebSocket с помощью `@ws.on_disconnect` / `@ws.on_error`, избегание ручного try/catch



### 生命周期管理

# Управление жизненным циклом

ErisPulse предоставляет единую систему перехватчиков/жизненного цикла для мониторинга статуса выполнения компонентов системы, а также реализации таких функций расширения, как аудит, статистика и кастомная логика.

Система поддерживает три способа триггерации:
- `await lifecycle.emit("event", data)` — упрощенная версия, принимает произвольные данные
- `lifecycle.emit_sync("event", data)` — синхронная версия (для неасинхронных контекстов)
- `await lifecycle.submit_event("event", ...)` — совместима с предыдущими версиями, автоматически формирует стандартный формат события

## Механизм обработки событий

### Регистрация обработчиков

```python
from ErisPulse import sdk

# Декораторный режим
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"Модуль загружен: {data}")

# Программная регистрация
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# Отмена регистрации
sdk.lifecycle.unregister("module.load", on_module_load)

# Массовая отмена регистрации по владельцу (вызывается автоматически при выгрузке адаптера/модуля)
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"Очищено {removed} жизненных циклов-перехватчиков")
```

### Приоритет

Обработчики поддерживают параметр `priority`, чем больше значение, тем раньше выполняется обработчик (совпадает с логикой загрузчика модулей):

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # Выполнится первым
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # Выполнится вторым
async def second_handler(data):
    pass
```

### События по точечной структуре

При запуске конкретного события также запускаются родительские события:
- При срабатывании `module.load` также срабатывает `module`
- При срабатывании `adapter.event.receive` также срабатывают `adapter.event` и `adapter`

### Подстановочные знаки

Регистрация `*` перехватывает все события:

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"Получено событие: {data}")
```

### Одноразовая регистрация (once)

Начиная с версии 2.7.0, обработчики, зарегистрированные через `lifecycle.once()`, автоматически удаляются после **одного срабатывания**, что подходит для одноразовых хуков, таких как "первая готовность":

```python
@sdk.lifecycle.once("core.init.complete")
async def on_first_ready(data):
    print("Первая готовность, больше не срабатывает")
```

- Имеет тот же смысл параметра приоритета, что и у `on()` (чем больше значение, тем раньше выполняется)
- Автоматическое удаление, ручное `unregister` не требуется
- Поддерживаются как синхронные, так и асинхронные обработчики

### Запрос обработчиков (has_handlers)

В критических сценариях можно сначала использовать `has_handlers()`, чтобы проверить наличие слушателей, избегая ненужного перебора событий и планирования задач:

```python
if sdk.lifecycle.has_handlers("message.sending"):
    await sdk.lifecycle.emit("message.sending", send_ctx)
```

- Охватывает **точное имя события, подстановочный знак `*`, а также родительские события**
- Возвращает `False`, если нет никаких слушателей, можно безопасно пропустить `emit`

## Обзор точек останова перехватчиков

Фреймворк включает следующие точки останова перехватчиков, пользователи могут отслеживать любую точку с помощью `@sdk.lifecycle.on()` для реализации кастомной логики.

### Инициализация ядра

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `core.init.start` | Начало инициализации SDK | `{}` |
| `core.init.complete` | Завершение инициализации SDK | `{"duration": float, "success": bool, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(только при ошибке)}` |
| `core.uninit.complete` | Завершение деинициализации SDK | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(только при ошибке)}` |

### Изменения конфигурации

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `config.set` | Конфигурационный элемент был изменен | `{"key": str, "old_value": Any, "new_value": Any}` |

**Пример: аудит конфигурации**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[Аудит] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### Жизненный цикл модулей

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `module.register` | Класс модуля зарегистрирован в менеджере | `{"module_name": str, "success": bool}` |
| `module.load` | Модуль загружен (экземпляр создан успешно) | `{"module_name": str, "success": bool}` |
| `module.init` | Модуль инициализирован (включая отложенную загрузку) | `{"module_name": str, "success": bool}` |
| `module.unload` | Модуль выгружен | `{"module_name": str, "success": bool}` |

### Жизненный цикл адаптеров

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `adapter.load` | Зарегистрирование адаптера завершено | `{"platform": str, "success": bool}` |
| `adapter.start` | Запуск адаптера | `{"platforms": [str]}` |
| `adapter.status.change` | Изменение статуса адаптера | `{"platform": str, "status": str, "retry_count": int, "error": str(только при ошибке)}` |
| `adapter.stop` | Остановка адаптера | `{"platforms": [str]}` |
| `adapter.stopped` | Остановка адаптера завершена | `{"platforms": [str]}` |
| `adapter.bot.online` | Бот онлайн | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Бот оффлайн | `{"platform": str, "bot_id": str, "status": str}` |

### Получение и обработка событий

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `adapter.event.receive` | Получено внешнее платформенное событие (раньше всех) | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.dispatched` | Распределение события завершено | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | Перед выполнением обработчика событий | `{"event_type": str, "platform": str, "detail_type": str}` |

**Пример: статистика событий**

```python
event_counter = {}

@sdk.lifecycle.on("adapter.event.receive")
def count_events(data):
    platform = data["platform"]
    event_counter[platform] = event_counter.get(platform, 0) + 1

@sdk.lifecycle.on("adapter.event.dispatched")
def log_unhandled(data):
    if data["onebot_handlers_count"] == 0:
        print(f"[Не обработано] {data['platform']}/{data['event_type']}")
```

### Отправка сообщений

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `message.sending` | Сообщение скоро будет отправлено | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | Отправка сообщения завершена | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**Пример: аудит отправки сообщений**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[Отправка] -> {data['platform']}/{data['detail_type']}/{data['target_id']} через {data['method']}")
```

### Командная система

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `command.matched` | Команда сопоставлена и скоро будет выполнена | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | Выполнение команды завершено | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(только при ошибке)}` |

**Пример: статистика команд**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[Команда] /{data['command']} от {data['user_id']}@{data['platform']}")
```

### HTTP маршрутизация

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `server.request` | Получен HTTP запрос | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | Отправлен HTTP ответ | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**Пример: лог запросов**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| Имя перехватчика | Когда срабатывает | Данные |
|---------|---------|------|
| `server.start` | Запуск маршрутизационного сервера | `{"base_url": str, "host": str, "port": int}` |
| `server.stop` | Остановка маршрутизационного сервера | `{}` |
| `server.websocket.connect` | Установлено WebSocket соединение | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket соединение разорвано | `{"path": str, "module_name": str, "reason": str, "error": str(только при исключении)}` |

**Пример: мониторинг WebSocket соединений**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] Подключение: {data['path']} от {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] Отключение: {data['path']} ({data['reason']})")
```

## Определения стандартных событий

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.complete", "uninit.complete"],
    "module": ["load", "init", "unload", "register"],
    "adapter": [
        "load", "start", "status.change", "stop", "stopped",
        "event.receive", "event.dispatched",
        "bot.online", "bot.offline",
    ],
    "server": [
        "start", "stop",
        "request", "response",
        "websocket.connect", "websocket.disconnect",
    ],
    "event": ["pre_process"],
    "message": ["sending", "sent"],
    "command": ["matched", "executed"],
    "config": ["set"],
}
```

## Полная справка по API

### Регистрация и отмена

| Метод | Описание |
|------|------|
| `@lifecycle.on(event, *, priority=0)` | Декоратор для регистрации обработчика |
| `lifecycle.register(event, handler, *, priority=0)` | Программная регистрация |
| `lifecycle.unregister(event, handler=None)` | Отмена регистрации (при handler=None отменяются все обработчики события) |

### Триггеринг

| Метод | Описание |
|------|------|
| `await lifecycle.emit(event, data=None)` | Асинхронный триггер, возвращаемое обработчиком значение не None изменяет data для последующих обработчиков |
| `lifecycle.emit_sync(event, data=None)` | Синхронный триггер, асинхронные обработчики запускаются через create_task |
| `await lifecycle.submit_event(event_type, *, source, msg, data)` | Совместимо с предыдущими версиями, автоматически формирует стандартный формат события |

### Инструменты

| Метод | Описание |
|------|------|
| `lifecycle.start_timer(timer_id)` | Запуск таймера |
| `lifecycle.get_duration(timer_id)` | Получение прошедшего времени (секунды) |
| `lifecycle.stop_timer(timer_id)` | Остановка таймера и возвращение прошедшего времени |
| `lifecycle.list_hooks()` | Вывод списка всех зарегистрированных перехватчиков и количества обработчиков |
| `lifecycle.clear()` | Очистка всех обработчиков и таймеров |

## Пример использования в модуле

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # Реализация простой статистики сообщений
        self.msg_count = 0
        
        @sdk.lifecycle.on("adapter.event.receive")
        async def count(data):
            if data["event_type"] == "message":
                self.msg_count += 1
        
        # Мониторинг всех команд
        @sdk.lifecycle.on("command.matched")
        async def log_cmd(data):
            sdk.logger.info(f"Выполнение команды: /{data['command']} от {data['user_id']}")
        
        # Аудит изменений конфигурации
        @sdk.lifecycle.on("config.set")
        def audit(data):
            sdk.logger.info(f"Изменение конфигурации: {data['key']} = {data['new_value']}")
```

## Важные примечания

1. **Обработчики могут быть синхронными или асинхронными**: система автоматически определяет тип и корректно вызывает
2. **Передача данных**: в режиме `emit()`, возвращаемое обработчиком значение не None изменяет `data`, передаваемую в последующие обработчики
3. **Номенклатура событий**: рекомендуется использовать точечную структуру именования событий для удобства использования родительских слушателей
4. **Изоляция ошибок**: исключение в одном обработчике не влияет на выполнение других обработчиков
5. **Ограничения синхронного триггера**: в `emit_sync()` асинхронные обработчики запускаются методом fire-and-forget, возвращаемое значение невозможно получить
6. **Очистка жизненного цикла**: при вызове `sdk.uninit()` все зарегистрированные обработчики и таймеры будут очищены
7. **Приоритет загрузки**: если необходимо прослушивать события на этапе инициализации фреймворка, рекомендуется установить высокий приоритет и отключить отложенную загрузку



### 懶加载系统

# Система ленивой загрузки модулей

ErisPulse SDK предоставляет мощную систему ленивой загрузки модулей, которая позволяет инициализировать модули только тогда, когда они действительно требуются, значительно повышая скорость запуска приложения и эффективность использования памяти.

## Обзор

Система ленивой загрузки модулей является одной из ключевых особенностей ErisPulse. Она работает следующим образом:

- **Отложенная инициализация**: Модули загружаются и инициализируются только при первом обращении к ним
- **Прозрачное использование**: Для разработчиков ленивые модули практически не отличаются от обычных модулей
- **Автоматическое управление зависимостями**: Зависимости модулей автоматически инициализируются при их использовании
- **Поддержка жизненного цикла**: Для модулей, унаследованных от `BaseModule`, автоматически вызываются методы жизненного цикла

## Принцип работы

### Класс LazyModule

Основой системы ленивой загрузки является класс `LazyModule`, который является обёрткой, инициализирующей модуль только при первом обращении.

### Процесс инициализации

При первом обращении к модулю `LazyModule` выполняет следующие действия:

1. Получает информацию о параметрах `__init__` класса модуля
2. Определяет, следует ли передавать ссылку на `sdk`
3. Устанавливает атрибут `moduleInfo` модуля
4. Для модулей, унаследованных от `BaseModule`, вызывает метод `on_load`
5. Запускает событие жизненного цикла `module.init`

## Конфигурация ленивой загрузки

### Глобальная конфигурация

В файле конфигурации включите/отключите глобальную ленивую загрузку:

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true=включить ленивую загрузку(по умолчанию), false=отключить ленивую загрузку
```

### Управление на уровне модуля

Модуль может контролировать стратегию загрузки, реализовав статический метод `get_load_strategy()`:

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """Возвращает стратегию загрузки модуля"""
        return ModuleLoadStrategy(
            lazy_load=False,  # Возвращает False для немедленной загрузки
            priority=100      # Приоритет загрузки, чем больше значение, тем выше приоритет
        )
```

## Использование ленивых модулей

### Базовое использование

Для разработчиков ленивые модули практически не отличаются от обычных модулей:

```python
# Доступ к ленивому модулю через SDK
from ErisPulse import sdk

# Следующее обращение вызовет ленивую загрузку модуля
result = await sdk.my_module.my_method()
```

### Единый вход для получения модуля

Независимо от того, получаете ли вы модуль через свойство SDK, свойство менеджера модулей или через `module.get()`, для "зарегистрированных, но ещё не загруженных" ленивых модулей будет возвращаться один и тот же прокси-объект ленивой загрузки, и инициализация будет происходить только при обращении к его свойствам:

```python
# Все три способа возвращают один и тот же прокси-объект ленивой загрузки (если модуль не загружен), поведение одинаковое и прозрачно для пользователя
sdk.my_module          # Точка входа, вызывающая загрузку
sdk.module.my_module   # Также возвращает прокси-объект ленивой загрузки
sdk.module.get("my_module")  # Также возвращает прокси-объект ленивой загрузки, сам вызов не запускает загрузку

# Инициализация модуля происходит только при обращении к любому свойству прокси-объекта
result = await sdk.my_module.my_method()
```

`module.get()` — это **интерфейс запроса**, сам по себе не запускает загрузку:
- Если модуль уже загружен → возвращается реальный экземпляр
- Если модуль зарегистрирован, но не загружен → возвращается прокси-объект ленивой загрузки (инициализация происходит при обращении к свойствам)
- Если модуль не зарегистрирован → возвращается `None`

Для явной загрузки используйте `await sdk.load_module("my_module")`.

### Асинхронная инициализация

Для модулей, требующих асинхронной инициализации, рекомендуется сначала явно загрузить модуль:

```python
# Сначала явно загрузите модуль
await sdk.load_module("my_module")

# Затем используйте модуль
result = await sdk.my_module.my_method()
```

### Синхронная инициализация

Для модулей, не требующих асинхронной инициализации, можно обращаться напрямую:

```python
# Прямое обращение автоматически инициализирует модуль синхронно
result = sdk.my_module.some_sync_method()
```

## Рекомендуемые практики

### Рекомендуемые сценарии для ленивой загрузки (lazy_load=True)

- Пассивные утилитарные классы (например, модули для запросов данных, преобразователи форматов и т.д., которые требуются только при вызове из других модулей)

### Рекомендуемые сценарии для отключения ленивой загрузки (lazy_load=False)

- Модули, регистрирующие триггеры (например, обработчики команд, обработчики сообщений)
- Слушатели событий жизненного цикла
- Модули для планирования задач
- Модули, которые должны инициализироваться при запуске приложения

> Параметр `priority` управляет порядком инициализации модулей, загружаемых немедленно. Чем больше значение, тем раньше модуль будет инициализирован. Модули с одинаковым приоритетом загружаются в порядке регистрации.

## Примечания

1. Если ваш модуль использует ленивую загрузку и другие модули никогда не обращались к нему в ErisPulse, ваш модуль никогда не будет инициализирован.
2. Если ваш модуль содержит такие компоненты, как слушатели событий или другие активно отслеживающие модули, обязательно укажите, что он должен загружаться немедленно, иначе это может повлиять на нормальную работу вашего модуля.
3. Мы не рекомендуем отключать ленивую загрузку, если у вас нет особых потребностей, поскольку это может привести к проблемам с управлением зависимостями и событиями жизненного цикла.



### 会话类型系统

# Система типов сессий

Система типов сессий ErisPulse отвечает за определение и управление типами сессий сообщений (личный чат, групповой чат, каналы и т.д.), а также предоставляет автоматическое преобразование между типами получения и типами отправки.

## Определение типов

### Типы получения (ReceiveType)

Типы получения берутся из поля `detail_type` событий OneBot12 и описывают сцену сессии события:

| Тип | Описание | Поле ID |
|------|----------|---------|
| `private` | Сообщение личного чата | `user_id` |
| `group` | Сообщение группового чата | `group_id` |
| `channel` | Сообщение канала | `channel_id` |
| `guild` | Сообщение сервера | `guild_id` |
| `thread` | Сообщение темы / подканала | `thread_id` |
| `user` | Сообщение пользователя (расширенное) | `user_id` |

### Типы отправки (SendType)

Типы отправки используются для указания цели отправки в `Send.To(type, id)`:

| Тип | Описание |
|------|----------|
| `user` | Отправить пользователю |
| `group` | Отправить в группу |
| `channel` | Отправить в канал |
| `guild` | Отправить на сервер |
| `thread` | Отправить в тему |

## Картирование типов

Существует стандартное отношение отображения между типами получения и типами отправки:

```
Получение (Receive)          Отправка (Send)
─────────────          ──────────
private        ──→     user
group          ──→     group
channel        ──→     channel
guild          ──→     guild
thread         ──→     thread
user           ──→     user
```

Ключевое различие: **используйте "private" при получении и "user" при отправке**. Это стандартный дизайн OneBot12 — событие описывает "сценарий личного чата", а отправка описывает "цель пользователя".

## Автоматическое определение

Когда у события нет четкого поля `detail_type`, система автоматически определит тип сессии на основе полей ID, присутствующих в событии:

**Приоритет**: `group_id` > `channel_id` > `guild_id` > `thread_id` > `user_id`

```python
from ErisPulse.Core.Event.session_type import infer_receive_type

# Есть group_id → определяется как group
event1 = {"group_id": "123", "user_id": "456"}
print(infer_receive_type(event1))  # "group"

# Есть только user_id → определяется как private
event2 = {"user_id": "456"}
print(infer_receive_type(event2))  # "private"
```

## Основные API

### Преобразование типов

```python
from ErisPulse.Core.Event.session_type import (
    convert_to_send_type,
    convert_to_receive_type,
)

# Тип получения → Тип отправки
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# Тип отправки → Тип получения
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### Запрос полей ID

```python
from ErisPulse.Core.Event.session_type import get_id_field, get_receive_type

# Получить имя поля ID по типу
get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

# Получить тип по полю ID
get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### Получение информации об отправке за один шаг

```python
from ErisPulse.Core.Event.session_type import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# Использовать прямо в Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### Получение целевого ID

```python
from ErisPulse.Core.Event.session_type import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## Регистрация пользовательских типов

Адаптер может регистрировать пользовательские сопоставления для типов сессий, специфичных для платформы:

```python
from ErisPulse.Core.Event.session_type import register_custom_type, unregister_custom_type

# Регистрация пользовательского типа
register_custom_type(
    receive_type="thread_reply",     # Имя типа получения
    send_type="thread",              # Соответствующий тип отправки
    id_field="thread_reply_id",      # Соответствующее поле ID
    platform="discord"               # Имя платформы (необязательно)
)

# Использование пользовательского типа
convert_to_send_type("thread_reply", platform="discord")  # → "thread"
get_id_field("thread_reply", platform="discord")          # → "thread_reply_id"

# Отмена регистрации пользовательского типа
unregister_custom_type("thread_reply", platform="discord")
```

> **При указании `platform`** зарегистрированные типы получения будут иметь префикс платформы (например, `discord_thread_reply`), чтобы избежать конфликтов типов между разными платформами.

## Утилиты

```python
from ErisPulse.Core.Event.session_type import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

# Проверка, является ли это стандартным типом
is_standard_type("private")  # True
is_standard_type("custom_type")  # False

# Проверка, является ли тип отправки допустимым
is_valid_send_type("user")  # True
is_valid_send_type("invalid")  # False

# Получение всех стандартных типов
get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

# Очистка пользовательских типов
clear_custom_types()                # очистить все
clear_custom_types(platform="discord")  # очистить только для указанной платформы
```



### 国际化（i18n）系统

# Система интернационализации (i18n)

В ErisPulse версии 2.5.0 встроена полная поддержка интернационализации. Интерфейс ядра фреймворка и CLI автоматически переключают отображаемый текст в зависимости от системного языка, а также поддерживают регистрацию внешними модулями собственных переводов.

> Пример: [English](docs/ru/index.md) | [Русский](docs/ru/ru.md) | [Español](docs/ru/es.md) | [Français](docs/ru/fr.md) | [日本語](docs/ru/ja.md)
>
> [English](docs/ru/en.md) | [Русский](docs/ru/ru.md) | [Español](docs/ru/es.md) | [Français](docs/ru/fr.md) | [日本語](docs/ru/ja.md)

## Поддерживаемые языки

| Язык | Код | Описание |
|------|------|------|
| Упрощенный китайский | `zh-CN` | Язык по умолчанию (родной язык фреймворка) |
| Традиционный китайский | `zh-TW` | Традиционный китайский (Гонконг/Макао/Тайвань) |
| English | `en` | Английский (универсальный язык по умолчанию) |
| 日本語 | `ja` | Японский |
| Русский | `ru` | Русский |

## Быстрое знакомство

### Переключение через переменные окружения

```bash
# Windows PowerShell
$env:ERISPULSE_LANG = "en"
epsdk run

# macOS / Linux
ERISPULSE_LANG=ja epsdk run
```

### Переключение через файл конфигурации

Добавьте в `config/config.toml`:

```toml
[ErisPulse.i18n]
language = "zh-TW"
```

Установка значения `"auto"` (по умолчанию) включает автоматическое определение системного языка.

### Ручное переключение в коде

```python
from ErisPulse import i18n

# Ручное установка языка
i18n.set_language("en")
print(i18n.get_language())  # "en"

# Сброс до автоматического определения
i18n.reset_language()
```

---

## Механизм определения языка

Фреймворк определяет язык пользователя с следующими приоритетами:

1. **Переменная среды `ERISPULSE_LANG`** — самый высокий приоритет, используется для тестирования и временного переключения
2. **Windows API** — `GetUserDefaultLocaleName` (только для Windows, не затрагивается `LANG` от инструментов вроде Git Bash)
3. **Переменные среды** — `LANGUAGE` > `LC_ALL` > `LC_MESSAGES` > `LANG` (стандарт Unix/macOS)
4. **Системная локаль** — `locale.getlocale()` / `locale.getdefaultlocale()`
5. **Fallback** — en (английский)

### Принцип ближайшего соответствия

Когда определенный язык не является точным совпадением, он сопоставляется с поддерживаемым языком по принципу ближайшего соответствия:

- `zh-TW`, `zh-HK`, `zh-MO`, `zh-Hant` → **Традиционный китайский**
- Все остальные `zh-*` (например, `zh-CN`, `zh-SG`) → **Упрощенный китайский**
- `en-US`, `en-GB`, `en-AU` и т. д. → **Английский**
- `ja-JP` → **Японский**
- `ru-RU` → **Русский**
- Все остальные неопознанные языки → **Упрощенный китайский (fallback)**

---

Пожалуйста, верните только полностью переведенный Markdown-контент без дополнительных комментариев.

## Использование i18n в модуле

Вы можете зарегистрировать тексты переводов для своего модуля, чтобы ваш модуль также поддерживал несколько языков.

### Рекомендуемый способ: Объявление ключей переводов через I18nClass (v2.7.0+)

Начиная с версии v2.7.0, модули/адаптеры могут объявлять ключи переводов, используя вложенный класс `I18nClass`, так же, как это делается для `ConfigClass`. Фреймворк автоматически **регистрирует** все объявленные ключи переводов во время загрузки, без необходимости вручную вызывать `i18n.register()`.

```python
from dataclasses import dataclass, field

from ErisPulse.Core.Bases import BaseConfig, BaseI18n, BaseModule, I18nKey


class MyModule(BaseModule):
    # Класс конфигурации (необязательно)
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="Welcome",
            metadata={
                # Здесь ссылается ключ i18n mymodule.welcome_msg
                "description": {"i18n": "mymodule.welcome_msg", "default": "Welcome Message"},
            },
        )

    # Класс коллекции ключей переводов (необязательно)
    # Объявленные ключи автоматически регистрируются фреймворком, приоритет раньше генерации конфигурации ConfigClass
    class I18nClass(BaseI18n):
        # Имена атрибутов автоматически объединяются в полный путь ключа: <имя_модуля>.<имя_атрибута>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # Независимый от языка запасной вариант, не регистрируется ни в одном языке
            zh_CN="Добро пожаловать",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
            zh_TW="歡迎訊息",
        )
        # Другие ключи переводов для бизнес-логики
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="Привет, {name}!",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )

        # Можно явно указать полный путь ключа (не использовать объединение имен атрибутов)
        custom: I18nKey = I18nKey(
            key="mymodule.deep.nested.key",
            default="Default text",
            zh_CN="Дефолтный текст",
            zh_TW="預設文本",
            en="Default text",
            ja="デフォルトテキスト",
            ru="Текст по умолчанию",
        )
```

#### Почему рекомендован I18nClass?

| Сценарий | Ручной i18n.register() | Объявление I18nClass |
|------|-----------------------|------------------|
| i18n ключ, ссылаемый в описании конфигурации | Нужно вручную зарегистрировать и сделать это до генерации конфигурации | Фреймворк автоматически регистрирует перед генерацией конфигурации |
| Объявление переводов для нескольких языков | Распределено по различным on_load() | Сосредоточено в классе, видно сразу |
| Согласованность имен ключей | Легко допустить опечатку | Имена атрибутов используются как суффиксы ключей, IDE может предлагать автодополнение |
| Очистка при卸рузке | Нужно вручную unregister_domain() | Фреймворк использует единый домен для регистрации |

#### Правила путей ключей I18nClass

- **По умолчанию**: Используйте ``<имя_регистрации_модуля>.<имя_атрибута>`` как полный путь ключа
  - Пример: имя модуля ``MyModule``, атрибут ``welcome`` → путь ключа ``MyModule.welcome``
- **Явно**: Укажите любой путь через точку с помощью параметра ``I18nKey(key="...")``
  - Подходит для ключей с глубокой вложенностью (например, ``mymodule.config.basic.token``)

#### Использование в адаптере

Адаптеры также поддерживают `I18nClass`, использование полностью аналогично:

```python
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey


class MyAdapter(BaseAdapter):
    @dataclass
    class ConfigClass(BaseConfig):
        endpoint: str = field(
            default="",
            metadata={
                # Описание конфигурации ссылается на ключ adapter.MyAdapter.endpoint
                "description": {"i18n": "MyAdapter.endpoint", "default": "API адрес"},
            },
        )

    class I18nClass(BaseI18n):
        # Централизованное объявление ключей, на которые ссылается описание конфигурации, и других бизнес-ключей
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API адрес",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
```

`I18nClass` адаптера автоматически регистрируется на этапе `__init__` (то есть до создания шаблона конфигурации), что гарантирует, что i18n ключи, используемые в описаниях конфигурации, уже доступны.

### Ручная регистрация пользовательских переводов (старый способ)

Если не использовать `I18nClass`, вы также можете напрямую вызывать `i18n.register()` для регистрации текстов переводов.

```python
from ErisPulse import i18n

# Регистрация китайского перевода
i18n.register("zh-CN", {
    "my_module.welcome": "Добро пожаловать в мой модуль!",
    "my_module.goodbye": "До свидания!",
    "my_module.hello": "Привет, {name}!",
}, domain="my_module")

# Регистрация английского перевода
i18n.register("en", {
    "my_module.welcome": "Welcome to my module!",
    "my_module.goodbye": "Goodbye!",
    "my_module.hello": "Hello, {name}!",
}, domain="my_module")
```

### Использование переводов

```python
from ErisPulse import i18n

# Простой перевод
i18n.t("my_module.welcome")  # Автоматически использует текущий язык

# С параметрами форматирования
i18n.t("my_module.hello", name="Alice")

# Указание значения по умолчанию (возвращается, если ключ перевода не существует)
i18n.t("my_module.unknown_key", default="Значение по умолчанию")
```

### Использование в классе модуля

```python
from dataclasses import dataclass, field
from ErisPulse import i18n
from ErisPulse.Core.Bases import BaseConfig, BaseModule

@dataclass
class MyModuleConfig(BaseConfig):
    welcome_msg: str = field(
        default="Welcome",
        metadata={
            "description": {"i18n": "my_module.welcome_msg", "default": "Добро пожаловать"},
            "ui": {"widget": "text", "group": "basic", "order": 1},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def on_load(self, event):
        # Чтение конфигурации в реальном времени (отражает последнее значение при каждом доступе)
        self.logger.info(self.cfg.welcome_msg)
        self.logger.info(i18n.t("my_module.welcome"))

    @command("hello")
    async def hello_handler(self, event):
        name = event.get_user_nickname() or "друг"
        await event.reply(i18n.t("my_module.hello", name=name))

    async def on_unload(self, event):
        pass
```

###卸载 переводов

```python
# Отвязка переводов для всего домена
i18n.unregister_domain("my_module")
```

---

Пожалуйста, верните переведенный полный Markdown-контент без дополнительных слов.

## Полиграфические настройки полей

С версии 2.5.2 схема конфигурации полностью поддерживает i18n. Все текстовые поля, видимые пользователям, могут ссылаться на ключи i18n. WebUI и другие потребители автоматически разрешают их в соответствующий текст в зависимости от текущего языка.

### Поддерживаемые поля i18n

| Поле | Позиция | Описание |
|------|---------|----------|
| `description` | метаданные поля | Описание поля |
| `options[].label` | `ui.options` | Метки опций элемента select |
| `placeholder` | `ui.placeholder` | Подсказка ввода |
| `group_labels` | `_schema_meta` | Отображаемое имя группы (Заголовок раздела Dashboard) |

Единый формат: `{"i18n": "ключ", "default": "текст"}`, простые строки передаются без изменений (для обратной совместимости).

### Объявление полей i18n

Все текстовые поля, видимые пользователям, поддерживают i18n:

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    # описание i18n
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Токен платформы"},
            "required": True,
            "secret": True,
            "ui": {
                "widget": "password",
                "group": "basic",
                "order": 1,
                # подсказка i18n
                "placeholder": {"i18n": "my_adapter.token.ph", "default": "Введите Token"},
            },
        },
    )
    # метки i18n
    mode: str = field(
        default="a",
        metadata={
            "description": {"i18n": "my_adapter.mode", "default": "Режим работы"},
            "ui": {
                "widget": "select",
                "group": "basic",
                "order": 2,
                "options": [
                    {"label": {"i18n": "my_adapter.mode.a", "default": "Режим A"}, "value": "a"},
                    {"label": {"i18n": "my_adapter.mode.b", "default": "Режим B"}, "value": "b"},
                ],
            },
        },
    )

    # group_labels i18n (отображаемое имя группы)
    _schema_meta = {
        "group_labels": {
            "basic": {"i18n": "my_adapter.group.basic", "default": "Основные настройки"},
        }
    }
```

`default` — это текст-заполнитель (fallback) — отображается, когда перевод не зарегистрирован или не найден.

### Скрытие секретов и проверка конфигурации

Поля с тегом `"secret": True` автоматически получают **защиту от засекречивания** (начиная с 2.7.0):

- **Шаблон с засекречиванием**: функция `dataclass_to_toml_with_comments()` при генерации шаблона конфигурации не записывает реальные значения secret-полей в файл (они отображаются как пустые плейсхолдеры), чтобы избежать попадания чувствительных данных на диск
- **Утилита общего засекречивания**: `redact_secret(value)` заменяет непустое значение на `***`, пустое возвращает как есть, может использоваться для вывода в логи и т.д.

```python
from ErisPulse.Core.Bases.config_schema import redact_secret

redact_secret("sk-xxxxxx")  # '***'
redact_secret("")           # ''
```

**Проверка конфигурации** (`validate_config()`) кроме проверки на непустоту `required` поддерживает начиная с 2.7.0:

| Тип проверки | Метаданные | Пример |
|--------------|------------|--------|
| Соответствие типа | Объявленный тип поля | передача строки в поле `int` вызывает ошибку |
| Ограничения перечисления | `ui.options` или глобальное `options` | значение должно принадлежать разрешенным опциям |
| Числовые диапазоны | Глобальные `min` / `max` | `metadata={"min": 1, "max": 65535}` |

```python
from ErisPulse.Core.Bases.config_schema import validate_config

@dataclass
class C(BaseConfig):
    mode: str = field(default="a", metadata={"ui": {"widget": "select", "options": ["a", "b"]}})
    port: int = field(default=80, metadata={"min": 1, "max": 65535})

errors = validate_config(C(mode="x", port=70000))  # две ошибки: перечисление + диапазон
```

### Регистрация перевода конфигурации

Ключи i18n для полей конфигурации такие же, как и обычные ключи перевода; их регистрация выполняется через `i18n.register()`:

```python
from ErisPulse import i18n

# Регистрация китайского (совпадает с default, можно и другим)
i18n.register("zh-CN", {
    "my_adapter.token": "Токен платформы",
}, domain="my_adapter")

# Регистрация английского
i18n.register("en", {
    "my_adapter.token": "Platform Token",
}, domain="my_adapter")
```
> **Рекомендуемый способ**: используйте `I18nClass` для объявления ключей перевода, фреймворк автоматически зарегистрирует их (см. раздел «Рекомендуемый способ» выше),
> вручную вызывать `i18n.register()` или `register_config_i18n()` не требуется.

Также предоставлена удобная функция `register_config_i18n()`, которая может автоматически извлекать ключи из класса конфигурации и регистрировать их:

```python
from ErisPulse.Core.Bases.config_schema import register_config_i18n

# Автоматическое извлечение description.default как перевода на китайский
register_config_i18n(MyAdapterConfig, "zh-CN")

# Ручное предоставление английского перевода
register_config_i18n(MyAdapterConfig, "en", {
    "my_adapter.token": "Platform Token",
})
```

### Как WebUI потребляет i18n

Словарь i18n в схеме, возвращаемой `get_config_schema()`, передается без изменений. Frontend WebUI может разрешать ключи в текст с помощью `i18n.t()` в зависимости от текущего языка.

Если необходимо, чтобы сервер разрешал их в строки напрямую (например, возвращал переднему модулю, который не поддерживает i18n), используйте `resolve_config_schema()`. Она разрешит `description`、`options[].label`、`placeholder` и `group_labels` в текст текущего языка:

```python
from ErisPulse.Core.Bases.config_schema import resolve_config_schema

# Все поля i18n разрешены в строки текущего языка
schema = resolve_config_schema(MyAdapterConfig)
print(schema["fields"]["token"]["description"])    # "Токен платформы" или "Platform Token"
print(schema["fields"]["token"]["placeholder"])   # "Введите Token" или "Enter Token"
print(schema["fields"]["mode"]["options"][0]["label"])  # "Режим A" или "Mode A"
print(schema["group_labels"]["basic"])             # "Основные настройки" или "Basic"
```

> Типы и утилиты, такие как `BaseConfig`、`BotAccountConfig`、`register_config_i18n()`、`resolve_config_schema()`,
> имеют фактическое определение в `ErisPulse.Core.Bases.config_schema`.
> `ErisPulse.runtime.config_schema` сохранен для совместимости shim,
> **рекомендуется импортировать из `ErisPulse.Core.Bases` единообразно** (кроме типов, связанных с ключами переводов i18n,
> они находятся в `ErisPulse.Core.Bases.i18n_schema`).

## API Справка

### I18nManager

#### Основные методы

| Метод | Описание |
|------|------|
| `t(key, default=None, **kwargs)` | Получить текст перевода (`gettext()` является псевдонимом) |
| `set_language(lang)` | Вручную задать язык |
| `get_language()` | Получить текущий язык |
| `reset_language()` | Сбросить до автоопределения (и переопределить окружение) |
| `get_supported_languages()` | Получить список всех поддерживаемых языков |
| `has_translation(key, lang=None)` | Проверить, существует ли ключ перевода |
| `register(lang, translations, domain)` | Зарегистрировать пользовательские переводы |
| `unregister_domain(domain)` | Отключить все переводы указанного домена |
| `reload()` | Перезагрузить встроенные переводы и переопределить язык |

#### Подробно о методе `t()`

```python
def t(self, key, /, default=None, **kwargs):
```

- `key` — ключ перевода (только позиционный аргумент, не должен конфликтовать с `key=` в `**kwargs`)
- `default` — значение по умолчанию, возвращаемое, если перевод не найден; по умолчанию `None` (возвращает сам ключ)
- `**kwargs` — аргументы форматирования, используются для заполнения `{placeholder}` в переводе

Пример:

```python
# Определение перевода: "greeting": "Привет, {name}! Добро пожаловать в {place}."
i18n.t("greeting", name="Alice", place="ErisPulse")
# Возвращает: "Привет, Alice! Добро пожаловать в ErisPulse."
```

### BaseI18n / I18nKey (Декларативные ключи перевода)

Начиная с версии v2.7.0, `ErisPulse.Core.Bases` предоставляет инструменты декларации ключей перевода на основе свойств класса (рекомендуется импортировать из `ErisPulse.Core.Bases`):

> ``I18nKey.default`` является **языковым независимым фоллбэком**, он не регистрируется ни для одного языка.
> Чтобы переводы вступили в силу, необходимо явно передать хотя бы один языковой параметр (``zh_CN=`` / ``en=`` / ``ja=`` и т.д.).
> Это позволяет разработчикам из разных стран свободно использовать свой родной язык для заполнения ``default``; фреймворк не делает никаких предположений.

| Название | Описание |
|------|------|
| `I18nKey(default, *, key=None, zh_CN, zh_TW, en, ja, ru)` | Объявление одного ключа перевода; `default` — языковая независимая fallback |
| `BaseI18n` | Базовый класс коллекции ключей перевода (наименование соответствует `BaseConfig`), подклассы объявляют несколько `I18nKey` как свойства класса |
| `BaseI18n.register(prefix="", domain="app")` | Статический метод: зарегистрировать все объявленные ключи в систему i18n |
| `key` | Псевдоним для `I18nKey` (более краткая запись) |

Пример использования:

```python
from ErisPulse.Core.Bases import BaseI18n, key

class MyKeys(BaseI18n):
    # Краткая запись с псевдонимом
    hello = key(
        default="Hello",
        zh_CN="你好",
        zh_TW="你好",
        en="Hello",
        ja="こんにちは",
        ru="Привет",
    )
    bye = key(
        default="Bye",
        zh_CN="再见",
        zh_TW="再見",
        en="Bye",
        ja="さようなら",
        ru="До свидания",
    )

# Независимое использование (ручная регистрация)
MyKeys.register(prefix="myapp.", domain="myapp")
```

### Доступ к SDK инстансу

```python
from ErisPulse import sdk

# sdk.i18n и импортированный напрямую i18n — это один и тот же объект
sdk.i18n.set_language("ru")
print(sdk.i18n.t("core.sdk.init.starting"))
```

---

> **[**Русский**](docs/ru/api-reference.md)** | [**English**](api-reference.md)** | [**日本語**](api-reference.md)**

## Конфигурация во время выполнения

### Чтение конфигурации i18n через API конфигурации

```python
from ErisPulse.Core.Bases import I18nConfig
from ErisPulse.runtime import get_i18n_config

config = get_i18n_config()
print(config["language"])  # "auto" или конкретный код языка

# I18nConfig — это dataclass, его можно использовать для создания шаблона конфигурации
schema = I18nConfig.__dataclass_fields__
```

### Описание параметров конфигурации

В разделе `[ErisPulse.i18n]` файла `config/config.toml`:

```toml
[ErisPulse.i18n]
# Отображаемый язык, доступные значения:
# - "auto"      — автоопределение языка системы (по умолчанию)
# - "zh-CN"     — упрощенный китайский
# - "zh-TW"     — традиционный китайский
# - "en"        — английский
# - "ja"        — японский
# - "ru"        — русский
language = "auto"
```

---

## Best Practices

### Нейминг ключей перевода

Рекомендуется использовать формат именования с разделением точками:

```
<Module Name>.<Category>.<Description>
```

Например: `my_module.command.hello_desc`, `core.adapter.start_failed`

### Глобальное покрытие переводов

Не обязательно предоставлять переводы для всех языков сразу. Если для языка нет перевода, он автоматически переключится на английский; если и английского перевода нет, будет отображаться само имя ключа.

### Динамический контент

Для динамически генерируемого контента (такого как имя пользователя, количество и т.д.), используйте форматирование `{placeholder}`:

```python
# Определение перевода
"user_count": "Текущих онлайн пользователей: {count}"

# Использование
i18n.t("user_count", count=len(users))
```

### Логируемые сообщения

Если ваш модуль использует фреймворк Logger, эти сообщения также автоматически будут использовать текущий язык:

```python
self.logger.info(i18n.t("my_module.startup"))

## Связь с CLI i18n

CLI имеет **отдельный** модуль интернационализации (`ErisPulse.CLI.i18n`), который полностью декouple'd от модуля интернационализации ядра фреймворка.

- **Core i18n** — используется модулем ядра фреймворка, внешние модули могут регистрировать переводы
- **CLI i18n** — используется внутри командной строки, не использует общие данные переводов с Core

Такой дизайн гарантирует, что изменения переводов CLI не повлияют на стабильность ядра фреймворка.



### 启动流程与手动控制

# Процесс запуска и ручное управление

В ErisPulse `await sdk.run()` / `await sdk.init()` объединяют всю цепочку запуска в "одну строку кода". Однако, если вам нужно полностью настроить процесс запуска (например, частичная загрузка, динамическая регистрация, горячая замена, внедрение пользовательской стратегии загрузки), вам нужно понимать, что происходит внутри этой цепочки, и как ручным образом управлять каждым шагом.

В этой статье мы разбиваем цепочку запуска на отдельные этапы, объясняем их обязанности, порядок вызова и приводим пример ручного полного запуска.

> В этой статье предполагается, что вы уже запустили [первого робота](../getting-started/first-bot.md) и знакомы с двумя режимами `sdk.run(keep_running=True/False)`. В этой статье фокусируется на разборе цепочки внутри `init()` и более низкоуровневых входных точках, таких как `init()`/`init_task()`/`init_sync()`.

## Обзор верхнего уровня SDK

Помимо двух режимов `keep_running` в `run()`, SDK предоставляет несколько более низкоуровневых точек инициализации, различающихся по **асинхронности, возвращаемому значению и обработке исключений**:

| Точка входа | Асинхронность | Возвращаемое значение | Обработка исключений | Сценарии использования |
|-------------|---------------|-----------------------|----------------------|-------------------------|
| `await sdk.run(True)` | async, блокирующий | `None` (автоматически `uninit` при остановке) | Ошибки модулей/адаптеров перехватываются, не ломают процесс | Простое приложение-бот |
| `await sdk.run(False)` | async, не блокирующий | `None` (не автоматически удаляется) | То же, что и выше | Инициализация, затем выполнение пользовательской логики |
| `await sdk.init()` | async, требует await | `bool` | **Не обернуты**, исключения поднимаются выше | Ручное управление жизненным циклом (с `uninit()`) |
| `sdk.init_task()` | async, возвращает Task, не блокирует | `asyncio.Task` | То же, что и `init()` | Параллельное выполнение других инициализаций или когда цикл событий еще не запущен |
| `sdk.init_sync()` | **Синхронный**, блокирует текущий поток | `bool` | То же, что и `init()` | Скрипты командной строки, синхронные входные точки без цикла событий |

> **Частая ошибка**: `await sdk.init()` **не эквивалентно** `await sdk.run(keep_running=False)`. Два различия: ① `init()` возвращает `bool`, `run()` возвращает `None`; ② `run()` оборачивает процесс инициализации и выполнения в try/except (перехватывает ошибки модулей/адаптеров, чтобы не сломать процесс), в то время как `init()` не оборачивает, исключения сразу поднимаются выше. При необходимости сопровождения выгрузки или пользовательской обработки исключений используйте `init()` + `uninit()`.

## Общий обзор цепочки запуска

`sdk.init()` (точнее, его внутренний `Initializer.init()`) запускает всю систему в следующем порядке:

```mermaid
flowchart TD
    A[0. Подготовка окружения<br/>Загрузка конфигурации / Обработка исключений] --> B
    B[1. Параллельное обнаружение и загрузка<br/>AdapterLoader.load / ModuleLoader.load<br/>Внутренний вызов Finder.find_all] --> C
    C[2. Регистрация адаптера<br/>AdapterLoader.register_to_manager] --> D
    D[3. Запуск адаптера<br/>adapter.startup] --> E
    E[4. Регистрация модуля<br/>ModuleLoader.register_to_manager] --> F
    F[5. Инициализация модуля<br/>ModuleLoader.initialize_modules<br/>Создание экземпляра и привязка к sdk] --> G
    G[6. Запуск сервера маршрутизации<br/>router.start]
```

Соответствующие основные компоненты:

| Уровень | Компонент | Обязанности |
|---------|-----------|-------------|
| Обнаружение | `AdapterFinder` / `ModuleFinder` | Обнаружение адаптеров/модулей из entry-points установленных пакетов |
| Загрузка | `AdapterLoader` / `ModuleLoader` | Обнаружение + импорт + чтение метаданных + определение включения/отключения, возвращает список объектов |
| Регистрация | `*Loader.register_to_manager` | Регистрация объектов в соответствующих менеджерах |
| Управление | `sdk.adapter` / `sdk.module` | Хранение экземпляров адаптеров/модулей, предоставление интерфейсов запуска/остановки |
| Инициализация | `ModuleLoader.initialize_modules` | Создание экземпляров модулей и привязка к `sdk` (обработка топологической сортировки зависимостей) |
| Маршрутизация | `sdk.router` | HTTP / WebSocket сервер |

> **Важно**: `Finder` и `Loader` — это два уровня. `Loader` внутри **уже содержит** `Finder` (`AdapterLoader` содержит `AdapterFinder`, `ModuleLoader` содержит `ModuleFinder`). В большинстве сценариев вам нужно использовать только `Loader`, только когда нужно "перечислить, но не импортировать", вы будете использовать `Finder` отдельно.

## Подробное объяснение каждого этапа

### 1. Уровень обнаружения: Finder

Finder только отвечает за "найти, какие пакеты предоставляют адаптеры/модули", не импортирует и не создает экземпляры.

```python
from ErisPulse.finders import AdapterFinder, ModuleFinder

adapter_finder = AdapterFinder()
module_finder = ModuleFinder()

# Найти все установленные entry-points адаптеров/модулей
adapter_entries = adapter_finder.find_all()    # list[EntryPoint]
module_entries = module_finder.find_all()      # list[EntryPoint]

# Найти по имени
entry = module_finder.find_by_name("MyModule")  # EntryPoint | None
```

Каждый `EntryPoint` можно `.load()` для получения соответствующего класса, но обычно вам не нужно вызывать это вручную — `Loader` сделает это.

### 2. Уровень загрузки: Loader

Loader делает "импорт + чтение метаданных + определение включения/отключения" поверх `Finder`.

```python
from ErisPulse.loaders import AdapterLoader, ModuleLoader
from ErisPulse import sdk

adapter_loader = AdapterLoader()
module_loader = ModuleLoader()

# load() внутри: вызывает finder.find_all() → обрабатывает каждый entry-point → возвращает триплет
adapter_objs, enabled_adapters, disabled_adapters = await adapter_loader.load(sdk.adapter)
module_objs, enabled_modules, disabled_modules = await module_loader.load(sdk.module)
```

Триплет, возвращаемый `load()`:

| Возвращаемое значение | Значение |
|-----------------------|----------|
| `objs` (`dict`) | Имя → объект (класс адаптера / обёртка модуля) |
| `enabled` (`list[str]`) | Имена, включённые (не отключены в конфигурации) |
| `disabled` (`list[str]`) | Имена, отключённые |

#### Информация для диагностики при сбое загрузки

Когда модуль/адаптер выбрасывает исключение на этапе загрузки или инициализации, фреймворк пропускает этот компонент и продолжает загрузку других компонентов, при этом выводя **суммарную информацию о кадре пользовательского кода**, что позволяет вам определить местоположение ошибки даже при уровне логирования INFO, без необходимости включать DEBUG:

```
[ERROR] [ModuleLoader] Загрузка модуля MyModule из entry-point не удалась, пропущен: 'NoneType' object has no attribute 'platform'
  → MyModule/Core.py:42 in on_load
      adapter = sdk.platform
  → AttributeError: 'NoneType' object has no attribute 'platform'
  → Подсказка: Повысьте уровень логирования до DEBUG, чтобы увидеть полный стек; проверьте реализацию модуля MyModule
```

Информация для диагностики генерируется модулем `ErisPulse.runtime.diagnostics`, автоматически фильтруя внутренние кадры фреймворка и оставляя только кадры вашего кода. Если вам нужно повторно использовать это в пользовательской логике загрузки:

```python
from ErisPulse.runtime import log_diagnostic

try:
    risky_init()
except Exception as e:
    log_diagnostic(e)  # Автоматически извлекает кадры пользовательского кода и записывает в ERROR лог
```

Этот модуль также предоставляет два низкоуровневых функции: `extract_user_frame()` (возвращает структурированную информацию о кадре) и `format_diagnostic_block()` (возвращает многострочный текст).

### 3. Уровень регистрации: register_to_manager

Регистрация объектов, созданных Loader, в менеджере, чтобы `sdk.adapter` / `sdk.module` могли их распознавать.

```python
# Регистрация адаптера (возвращает bool, означающий, были ли все успешны)
await adapter_loader.register_to_manager(enabled_adapters, adapter_objs, sdk.adapter)

# Регистрация модуля
await module_loader.register_to_manager(enabled_modules, module_objs, sdk.module)
```

После регистрации адаптеры появляются в `sdk.adapter._adapters`, классы модулей — в `sdk.module`, но **они ещё не запущены/инициализированы**.

### 4. Запуск адаптера

```python
# Запуск всех зарегистрированных адаптеров
await sdk.adapter.startup()
# Или указать платформу
await sdk.adapter.startup("yunhu")
await sdk.adapter.startup(["yunhu", "telegram"])
```

> Регистрация ≠ Запуск. `register_to_manager` только регистрирует; `startup` вызывает `start()` адаптера, устанавливая соединение с платформой.

### 5. Инициализация модуля

Модули имеют дополнительный шаг — **инициализацию** и привязку к `sdk` (чтобы вы могли вызывать `sdk.MyModule.xxx`). Этот шаг также обрабатывает объявления зависимостей модулей и топологическую сортировку.

```python
success = await module_loader.initialize_modules(
    enabled_modules, module_objs, sdk.module, sdk
)
```

После успешной инициализации модуль появляется в `sdk.<ModuleName>`.

### 6. Запуск сервера маршрутизации

```python
await sdk.router.start(
    host="0.0.0.0",
    port=8000,
    ssl_certfile=None,
    ssl_keyfile=None,
)
```

Сервер маршрутизации отвечает за получение webhook / WebSocket-вызовов от адаптеров. Без запуска его серверные адаптеры не могут получать сообщения.

## Полный пример ручного запуска

Следующий код **эквивалентен** ядро процесса `await sdk.init()`, но каждый шаг доступен вам, чтобы вставить пользовательскую логику в любой момент:

```python
import asyncio
from ErisPulse import sdk
from ErisPulse.loaders import AdapterLoader, ModuleLoader

async def manual_startup():
    # 0. Подготовка окружения (загрузка конфигурации, регистрация обработки исключений)
    #    _prepare_environment — это предварительный шаг внутри init(); ручной процесс также должен сначала вызвать его,
    #    иначе Loader не сможет прочитать конфигурацию и по ошибке отключит все адаптеры/модули.
    if not await sdk._prepare_environment():
        print("Подготовка окружения не удалась")
        return False

    # 1. Создание загрузчиков (внутри каждый содержит Finder)
    adapter_loader = AdapterLoader()
    module_loader = ModuleLoader()

    # 2. Параллельное обнаружение и загрузка (как в init() используется gather)
    (adapter_objs, enabled_adapters, disabled_adapters), \
    (module_objs, enabled_modules, disabled_modules) = await asyncio.gather(
        adapter_loader.load(sdk.adapter),
        module_loader.load(sdk.module),
    )

    # 3. Регистрация адаптера
    await adapter_loader.register_to_manager(
        enabled_adapters, adapter_objs, sdk.adapter
    )

    # 4. Запуск адаптера
    if enabled_adapters:
        await sdk.adapter.startup()

    # 5. Регистрация модуля
    await module_loader.register_to_manager(
        enabled_modules, module_objs, sdk.module
    )

    # 6. Инициализация модуля (инстанцирование + привязка к sdk)
    if enabled_modules:
        await module_loader.initialize_modules(
            enabled_modules, module_objs, sdk.module, sdk
        )

    # 7. Запуск сервера маршрутизации
    await sdk.router.start(host="0.0.0.0", port=8000)

    print("Ручной запуск завершён")
    return True

async def main():
    ok = await manual_startup()
    if ok:
        # Блокирующее ожидание (ручной процесс не блокирует автоматически)
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### Когда использовать ручной запуск?

В большинстве случаев **не нужно** использовать ручной запуск, `await sdk.run()` уже делает всё это. Ручной запуск имеет ценность только в следующих сценариях:

- **Частичная загрузка**: загрузка только определённых адаптеров/модулей, пропуск других
- **Динамическая регистрация**: регистрация новых адаптеров/модулей во время выполнения по условиям
- **Нестандартный порядок**: требуется изменить стандартный порядок загрузки (например, запустить модуль перед адаптером)
- **Внедрение стратегий**: внедрение пользовательских стратегий управления, строгих режимов и т.д. в Loader
- **Отладка/диагностика**: при сбое на каком-либо этапе, ручное управление для локализации проблемы

## Тонкое управление во время выполнения

Даже если вы использовали `sdk.run()` для запуска, вы по-прежнему можете управлять подсистемами отдельно во время выполнения, без необходимости перезапуска всего SDK:

### Горячая перезагрузка адаптеров

```python
# Горячая перезагрузка адаптера (восстановление соединения, без влияния на другие платформы)
await sdk.adapter.shutdown("yunhu")
await sdk.adapter.startup("yunhu")

# Запуск новой платформы во время работы
await sdk.adapter.startup("telegram")

# Временное отключение платформы
await sdk.adapter.shutdown("telegram")
```

> `adapter.startup()` требует, чтобы адаптер **был зарегистрирован** в менеджере. Регистрация происходит внутри `init()`/`run()`, поэтому это тонкое управление **после** запуска.

### Сервер маршрутизации

```python
# Временное отключение webhook-сервера
await sdk.router.stop()

# Перезапуск (например, при смене порта)
await sdk.router.start(host="0.0.0.0", port=9000)
```

### Модули по требованию

```python
# Ручная загрузка модуля (возможно, ленивая загрузка)
await sdk.load_module("MyModule")
```

## Аккуратное завершение

Начиная с версии 2.7.0, `sdk.shutdown()` предоставляет **программное аккуратное завершение**: установка события завершения, которое заставляет главный цикл, висящий в `await sdk.run(keep_running=True)`, вернуться, что ведёт к вызову `uninit()` и завершению очистки ресурсов.

```python
# Вызов из любого корутины, вызывает аккуратный выход (run() висит и возвращает, автоматически uninit)
sdk.shutdown()
```

Типичные сценарии использования:

```python
async def shutdown_after_idle():
    await asyncio.sleep(3600)
    sdk.shutdown()  # Аккуратный выход после 1 часа бездействия
```

**Обработка сигналов**: `run()` внутри регистрирует обработчики `SIGTERM` / `SIGHUP`, преобразуя системные сигналы в аккуратное завершение — при остановке контейнера (Docker `docker stop`) или остановке службы `systemd`, процесс пройдёт через `uninit()` для очистки, а не будет принудительно убит.

- Windows не поддерживает `loop.add_signal_handler`, обработчик сигнала будет автоматически пропущен (можно использовать `sdk.shutdown()` или Ctrl+C для вызова завершения)
- Повторный вызов `sdk.shutdown()` безопасен (после установки события повторный вызов не делает ничего)

## Процесс выгрузки

Обратная операция запуска — это `await sdk.uninit()`, который очищает в обратном порядке:

1. Закрытие всех адаптеров (`adapter.shutdown()`)
2. Выгрузка всех модулей
3. Очистка всех обработчиков событий
4. Очистка менеджеров и атрибутов модулей в SDK

В сценариях ручного запуска не забудьте вызвать `uninit()` перед выходом для обеспечения аккуратного завершения:

```python
try:
    await asyncio.Event().wait()   # Поддержание работы
finally:
    await sdk.uninit()
```

## Перезапуск

SDK предоставляет два способа перезапуска, без необходимости предварительной выгрузки — фреймворк сам обрабатывает:

| Способ | Вызов | Поведение | Сценарии использования |
|--------|-------|-----------|-------------------------|
| Горячий перезапуск | `await sdk.restart()` | Внутри одного процесса `uninit()` и повторный `init()`, перезагрузка адаптеров/модулей | Перезагрузка конфигурации, горячая замена модулей |
| Жёсткий перезапуск | `await sdk.hard_restart()` | `uninit()` и выход из процесса, новый процесс запускается родительским процессом (`epsdk run`) | Подозрения на утечку памяти/ресурсов, полная перезагрузка |
| | | | |

```python
# Горячий перезапуск: перезагрузка в том же процессе (наиболее часто используемый)
await sdk.restart()

# Жёсткий перезапуск: выход из процесса, должен быть запущен через `epsdk run main.py` для эффекта
await sdk.hard_restart()
```

> **Два важных замечания**:
> 1. Эти методы выполняют перезапуск в фоновой задаче, **немедленно возвращают `True`, означающее "задача перезапуска запланирована"**, а не "перезапуск завершён". Реальный перезапуск происходит в фоне, чтобы избежать прерывания текущей цепочки событий.
> 2. `hard_restart()` **должен быть запущен через `epsdk run main.py`, чтобы сработать**. Его принцип: после выгрузки процесс завершается с кодом 42, родительский процесс `epsdk run` обнаруживает код 42 и запускает новый процесс; если процесс запущен напрямую через `python main.py`, он завершится с кодом 42 и просто завершится, не перезапустившись автоматически.

### Когда использовать жёсткий перезапуск?

Жёсткий перезапуск — это не просто "более полный перезапуск", он более подходит и даже эффективнее в следующих сценариях:

- **Побочные эффекты двоичных библиотек (C-расширения)**: горячий перезапуск происходит в одном процессе, не может освободить C-расширения, открытые файловые дескрипторы, потоки и другие ресурсы процесса; жёсткий перезапуск меняет процесс, полностью удаляя эти побочные эффекты.
- **Поиск утечек ресурсов**: при подозрении на утечку памяти или дескрипторов, жёсткий перезапуск даёт чистую среду.
- **Частые перезапуски, чувствительные к производительности**: жёсткий перезапуск исключает затраты на выгрузку → перезагрузку в одном процессе, фактически более эффективен, чем горячий перезапуск.

> Функция "перезапуск фреймворка" в панели управления Dashboard вызывает `hard_restart()`.
> Кроме того, жёсткий перезапуск требует **обязательного** использования команды `epsdk run` для запуска, иначе программа просто выбросит код 42 и завершится, так как `run` проверяет код 42 для перезапуска процесса, и это нужно учитывать.



====
技术标准
====


### 会话类型标准

# Стандарт типов сессий ErisPulse

Этот документ определяет стандарты типов сессий, поддерживаемых ErisPulse, включая типы событий для получения и целевые типы для отправки.

## 1. Основные концепции

### 1.1 Тип получения && Тип отправки

ErisPulse различает два типа сессий:

- **Тип получения (Receive Type)**: поле `detail_type` для получаемых событий
- **Тип отправки (Send Type)**: целевой тип для метода `Send.To()` при отправке сообщений

### 1.2 Карта соответствия типов

```
Тип получения (detail_type)     Тип отправки (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**Ключевые моменты**:
- `private` — это тип при получении, при отправке необходимо использовать `user`
- `group`、`channel`、`guild`、`thread` имеют одинаковые типы для получения и отправки
- Система автоматически выполняет преобразование типов, ручная обработка не требуется (это означает, что вы можете использовать полученный тип получения для отправки напрямую), но на практике вам не нужно об этом думать. Существование класса-обертки Event позволяет вам использовать метод `event.reply()` напрямую, не задумываясь о преобразовании типов

## 2. Стандартные типы сессий

### 2.1 Стандарт OneBot12

#### private
- **Тип получения**: `private`
- **Тип отправки**: `user`
- **Описание**: Сообщения личного чата (1 на 1)
- **Поля ID**: `user_id`
- **Поддерживаемые платформы**: Все платформы, поддерживающие личные чаты

#### group
- **Тип получения**: `group`
- **Тип отправки**: `group`
- **Описание**: Сообщения группового чата, включая различные формы групп (например, Telegram supergroup)
- **Поля ID**: `group_id`
- **Поддерживаемые платформы**: Все платформы, поддерживающие групповые чаты

#### user
- **Тип получения**: `user`
- **Тип отправки**: `user`
- **Описание**: Тип пользователя, некоторые платформы (например, Telegram) используют `user` для обозначения личных чатов, а не `private`
- **Поля ID**: `user_id`
- **Поддерживаемые платформы**: Telegram и другие платформы

### 2.2 Расширенные типы ErisPulse

#### channel
- **Тип получения**: `channel`
- **Тип отправки**: `channel`
- **Описание**: Сообщения канала, поддерживают широковещательные сообщения для нескольких пользователей
- **Поля ID**: `channel_id`
- **Поддерживаемые платформы**: Discord, Telegram, Line и другие

#### guild
- **Тип получения**: `guild`
- **Тип отправки**: `guild`
- **Описание**: Сообщения сервера / сообщества, обычно используются для событий уровня Discord Guild
- **Поля ID**: `guild_id`
- **Поддерживаемые платформы**: Discord и другие

#### thread
- **Тип получения**: `thread`
- **Тип отправки**: `thread`
- **Описание**: Сообщения тредов / тем, используются для подфорумов в сообществах
- **Поля ID**: `thread_id`
- **Поддерживаемые платформы**: Discord Threads, Telegram Topics и другие

## 3. Карта соответствия типов платформ

### 3.1 Принципы сопоставления

Адаптеры отвечают за сопоставление нативных типов платформ со стандартными типами ErisPulse:

```
Нативный тип платформы → Стандартный тип ErisPulse → Тип отправки
```

### 3.2 Примеры сопоставления для популярных платформ

#### Telegram
```
Тип Telegram          Тип получения ErisPulse    Тип отправки
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group
supergroup             group                   group  # сопоставляется с group
channel                channel                 channel
```

#### Discord
```
Тип Discord          Тип получения ErisPulse    Тип отправки
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
Тип OneBot11        Тип получения ErisPulse    Тип отправки
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # сопоставляется с group
```

## 4. Расширение пользовательских типов

### 4.1 Регистрация пользовательского типа

Адаптеры могут регистрировать пользовательские типы сессий:

```python
from ErisPulse.Core.Event import register_custom_type

# Регистрация пользовательского типа
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 Использование пользовательского типа

После регистрации система автоматически обрабатывает преобразование и вывод типа:

```python
# Автоматический вывод
receive_type = infer_receive_type(event, platform="MyPlatform")
# Возврат: "my_custom_type"

# Преобразование в тип отправки
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# Возврат: "custom"

# Получение соответствующего ID
target_id = get_target_id(event, platform="MyPlatform")
# Возврат: event["custom_id"]
```

### 4.3 Отмена регистрации пользовательского типа

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. Автоматическое определение типа

Когда у события отсутствует явное поле `detail_type`, система автоматически определяет тип на основе существующих полей ID:

### 5.1 Приоритет определения

```
Приоритет (от высокого к низкому):
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 Пример использования

```python
# У события есть только group_id
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# Возврат: "group" (используется group_id)

# У события есть только user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# Возврат: "private"
```

## 6. Примеры использования API

### 6.1 Отправка сообщений

```python
from ErisPulse import adapter

# Отправка пользователю
await adapter.myplatform.Send.To("user", "123").Text("Привет")

# Отправка в группу
await adapter.myplatform.Send.To("group", "456").Text("Привет")

# Автоматическое преобразование private → user (не рекомендуется, могут быть проблемы совместимости)
await adapter.myplatform.Send.To("private", "789").Text("Привет")
# Внутренне автоматически преобразуется в: Send.To("user", "789") # Прямое использование "user" как типа сессии — более оптимальный выбор
```

### 6.2 Ответ на событие

```python
from ErisPulse.Core.Event import Event

# Метод Event.reply() автоматически обрабатывает преобразование типа
await event.reply("Содержание ответа")
# Внутренне автоматически используется правильный тип отправки
```

### 6.3 Обработка команд

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # Система автоматически обрабатывает тип сессии
    # Не нужно вручную проверять group_id или user_id
    await event.reply("Команда выполнена успешно")
```

## 7. Рекомендации по лучшим практикам

### 7.1 Разработчики адаптеров

1. **Используйте стандартные соответствия**: По возможности сопоставляйте со стандартными типами, а не создавайте новые
2. **Правильное преобразование**: Убедитесь, что соответствие между типом получения и типом отправки верное
3. **Сохранение исходных данных**: Храните исходный тип события в `{platform}_raw`
4. **Документация**: Описывайте соответствия типов в документации адаптера

### 7.2 Разработчики модулей

1. **Используйте вспомогательные методы**: Используйте такие методы, как `get_send_type_and_target_id()`
2. **Избегайте жесткого кодирования**: Не пишите код типа `if group_id else "private"`
3. **Учитывайте все типы**: Код должен поддерживать все стандартные типы, а не только private/group
4. **Гибкий дизайн**: Используйте методы объекта-обертки событий, а не прямой доступ к полям

### 7.3 Определение типа

- **Приоритет у detail_type**: Если есть явное поле, определение не выполняется
- **Используйте определение осмысленно**: Используйте только при отсутствии явного типа
- **Учитывайте приоритет**: Знайте приоритет определения, чтобы избежать неожиданных результатов

## 8. Часто задаваемые вопросы

### Q1: Почему при отправке `private` преобразуется в `user`?

A: Это требование стандарта OneBot12. `private` — это понятие при получении, а использование `user` при отправке более семантически верно.

### Q2: Как поддерживать новые типы сессий?

A: Зарегистрируйте пользовательский тип через `register_custom_type()` или используйте стандартные типы, такие как `channel` или `guild`.

### Q3: Что делать, если у события нет detail_type?

A: Система автоматически определит тип на основе существующих полей ID. Приоритет: group > channel > guild > thread > user.

### Q4: Как адаптер сопоставляет Telegram supergroup?

A: В логике преобразования адаптера сопоставьте `supergroup` со стандартным типом `group`.

### Q5: Как обрабатывать специальные платформы, такие как электронная почта?

A: Для не универсальных или специфичных для платформы типов используйте `{platform}_raw` и `{platform}_raw_type` для сохранения исходных данных, адаптер сам обрабатывает это.

## 9. Связанные документы

- [Стандарт преобразования событий](event-conversion.md) - Полная спецификация преобразования событий
- [Спецификация методов отправки](send-method-spec.md) - Правила именования и параметров методов класса Send
- [Руководство по разработке адаптеров](../developer-guide/adapters/) - Полное руководство по разработке адаптеров



====
生态模块
====


### Dashboard 使用与视窗注册

# ErisPulse-Dashboard

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) — это модуль **Web-панели управления**, поддерживаемый напрямую ErisDev, предоставляющий ErisPulse визуальный интерфейс управления во время выполнения: запуск и остановка модулей, редактирование конфигурации, просмотр логов, мониторинг потока событий и многое другое.

> [!IMPORTANT]
> Dashboard **не является** встроенной функцией фреймворка ErisPulse и требует отдельной установки:
>
> ```bash
> epsdk install Dashboard
> ```

Dashboard также поддерживает регистрацию пользовательских страниц управления другими модулями ErisPulse в боковой панели. После регистрации пользователи могут переключиться на собственную страницу окна модуля прямо в Dashboard без необходимости дополнительной разработки отдельного интерфейса.

> [!NOTE]
> Регистрация окон является **необязательной функцией**.
>
> - Если модуль Dashboard **не установлен** или **не загружен**, вызов `sdk.Dashboard.register_view()` вызовет исключение
> - Обязательно обертывайте код регистрации в `try/except`, чтобы убедиться, что другие функции модуля не затронуты
> - Рекомендуется проверить доступность Dashboard перед регистрацией: `hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## Принцип работы

```
Модуль on_load()
  → Вызов sdk.Dashboard.register_view(...)
  → Бэкенд Dashboard сохраняет информацию о окне
  → WebSocket уведомляет фронтенд
  → Фронтенд динамически создает элемент навигации боковой панели + контейнер страницы
  → Пользователь нажимает для просмотра окна модуля
```

---

## API регистрации

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # Обязательно, уникальный идентификатор
    title="Мой модуль",                  # Отображаемое название (китайский язык)
    title_en="My Module",             # Отображаемое название (английский язык)
    icon_svg='<svg>...</svg>',        # SVG-иконка для боковой панели
    html_content='<div>...</div>',     # HTML-содержимое страницы
    js_content='function xxx() {}',    # Логика JavaScript страницы
    css_content='.my-style {}',        # Дополнительный пользовательский CSS
    iframe_url='',                     # URL для режима iframe (выбирается либо html_content)
    loader="loadMyModuleView",         # Имя функции JS, вызываемой при переключении
    group="group_extensions",          # Группа в боковой панели
    group_title="",                    # Название группы на китайском языке
    group_title_en="",                 # Название группы на английском языке
)
```

### Описание параметров

| Параметр | Тип | Обязательно | Описание |
|------|------|------|------|
| `id` | `str` | Да | Уникальный идентификатор окна, рекомендуется использовать имя модуля |
| `title` | `str` | Нет | Отображаемое имя на китайском языке, по умолчанию используется `id` |
| `title_en` | `str` | Нет | Отображаемое имя на английском языке, по умолчанию используется `title` |
| `icon_svg` | `str` | Нет | Полная строка SVG для иконки боковой панели |
| `html_content` | `str` | Нет* | Содержимое HTML страницы в режиме внедрения |
| `js_content` | `str` | Нет | Код JavaScript страницы |
| `css_content` | `str` | Нет | Пользовательские CSS-стили страницы |
| `iframe_url` | `str` | Нет* | URL для режима iframe, после установки html_content игнорируется |
| `loader` | `str` | Нет | Имя функции JS, автоматически вызываемой при активации страницы |
| `group` | `str` | Нет | Идентификатор группы боковой панели, по умолчанию `group_extensions` |
| `group_title` | `str` | Нет | Название группы на китайском языке |
| `group_title_en` | `str` | Нет | Название группы на английском языке |

> *`html_content` и `iframe_url` должны быть предоставлены хотя бы один, иначе страница будет пустой.

---

## Два режима внедрения

### Режим 1: HTML/JS внедрение (рекомендуется)

Прямая передача строк HTML, JS и CSS, Dashboard внедряет содержимое в страницу. Этот режим полностью соответствует стилю Dashboard, рекомендуется использовать предоставленные CSS-классы.

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="Приветствие", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">Это пример страницы</div></div>',
    group="group_tools",
)
```

> Полный пример погодного модуля (включая API-роуты, JS-взаимодействие и т.д.) см. ниже [Полный пример модуля](#полный-пример-модуля).

### Режим 2: Внедрение iframe

Модуль предоставляет свой URL страницы HTML (необходимо самостоятельно зарегистрировать маршрут), Dashboard внедряет его через iframe. Подходит для сценариев, требующих полностью независимого UI или сложного взаимодействия.

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="Визуализация данных", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> Режим iframe автоматически добавляет параметр `token` в конец URL для аутентификации.

---

## Группы боковой панели

Модуль может указать, в какой группе боковой панели находится окно. В Dashboard встроены следующие группы:

| Идентификатор группы | Китайское название | Позиция |
|---------|--------|------|
| `group_overview` | Обзор | 1-я группа |
| `group_events` | События | 2-я группа |
| `group_extensions` | Расширения | 3-я группа (по умолчанию) |
| `group_system` | Система | 4-я группа |
| `group_tools` | Инструменты | 5-я группа |

Указывая встроенное имя группы, окно модуля будет добавлено в конец этой группы:

```python
group="group_tools"  # Добавить в группу "Инструменты"
```

Также можно использовать пользовательское имя группы (не начинается с `group_`), Dashboard автоматически создаст новую группу:

```python
group="my_group",
group_title="Моя группа",
group_title_en="My Group",
```

---

## Часто используемые CSS-классы

При использовании HTML-режима внедрения для окна модуля можно напрямую использовать уже существующие CSS-классы Dashboard для сохранения визуальной согласованности:

| Класс | Назначение |
|------|------|
| `page-title` | Заголовок страницы, например `<h1 class="page-title">Заголовок</h1>` |
| `card` | Контейнер карточки |
| `card-header` | Заголовок карточки |
| `card-body` | Область содержимого карточки |
| `grid-2` | Сетка из двух колонок |
| `grid-3` | Сетка из трех колонок |
| `btn` | Базовая кнопка |
| `btn-primary` | Основная кнопка (синяя) |
| `btn-secondary` | Второстепенная кнопка |
| `btn-icon` | Кнопка с иконкой |
| `btn-danger` | Кнопка опасного действия |

Dashboard использует CSS-переменные для управления цветами темы, вы можете ссылаться на них напрямую в окне модуля:

| CSS-переменная | Назначение |
|----------|------|
| `var(--bg-p)` | Основной цвет фона |
| `var(--bg-s)` | Вторичный цвет фона |
| `var(--bg-t)` | Третичный цвет фона (карточки и т.д.) |
| `var(--tx-p)` | Основной цвет текста |
| `var(--tx-s)` | Вторичный цвет текста |
| `var(--tx-t)` | Дополнительный цвет текста |
| `var(--bd)` | Цвет границ |
| `var(--accent)` | Цвет акцента |
| `var(--ok-c)` | Цвет успеха |
| `var(--er-c)` | Цвет ошибки |

Эти переменные автоматически переключаются в зависимости от светлой/темной темы Dashboard, дополнительная обработка в модуле не требуется.

---

## Аутентификация и вызовы API

При вызове собственного API модуля в JS окна модуля необходимо пройти аутентификацию, используя токен Dashboard:

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

Точка API модуля может самостоятельно решать, проверять ли токен. Если требуется проверка, ее можно извлечь из заголовка запроса:

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## Полный пример модуля

Ниже приведен полный пример погодного модуля, показывающий, как зарегистрировать окно, предоставить API-данные и очистить ресурсы при卸ождении:

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command


class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("Weather")
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(lazy_load=False, priority=50)

    async def on_load(self, event):
        self._register_routes()
        self._register_dashboard_view()
        self.logger.info("Погодный модуль загружен")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("Погодный модуль выгружен")

    def _load_config(self):
        config = self.sdk.config.getConfig("Weather")
        if not config:
            default = {"city": "Пекин", "api_key": ""}
            self.sdk.config.setConfig("Weather", default)
            return default
        return config

    def _register_routes(self):
        r = self.sdk.router
        r.register_http_route("Weather", "/api/current",
                              handler=self._api_current, methods=["GET"])

    def _unregister_routes(self):
        r = self.sdk.router
        try:
            r.unregister_http_route("Weather", "/api/current")
        except Exception:
            pass

    async def _api_current(self, request):
        return {
            "city": self.config.get("city", "Пекин"),
            "temp": 25,
            "humidity": 60,
        }

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="Погода", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">Запрос погоды</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">Просмотр текущей информации о погоде</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">Текущая погода</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">Нажмите обновить для загрузки</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">Действия</div>
                            <div class="card-body">
                                <button class="btn btn-primary" onclick="refreshWeather()">Обновить</button>
                            </div>
                        </div>
                    </div>
                ''',
                js_content='''
                    async function loadWeatherView() { await refreshWeather(); }
                    async function refreshWeather() {
                        var el = document.getElementById('weather-info');
                        if (!el) return;
                        el.textContent = 'Загрузка...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>Город: ' + (data.city || '--') + '</p>' +
                                           '<p>Температура: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>Влажность: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = 'Ошибка загрузки: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"Не удалось зарегистрировать окно Dashboard: {e}")
```

---

## Отмена регистрации окна

При выгрузке модуля следует вызывать `unregister_view()` для очистки зарегистрированного окна:

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

После отмены регистрации фронтенд Dashboard через WebSocket в реальном времени удаляет элементы навигации боковой панели и содержимое страницы, обновление страницы пользователем не требуется.

---

## Важные замечания

1. **Порядок загрузки** — Приоритет загрузки Dashboard — `99999` (высокий), приоритет вашего модуля должен быть ниже этого значения (например, `50`), чтобы убедиться, что Dashboard загружен первым
2. **Защищенное программирование** — При регистрации окна используйте `try/except`, так как модуль Dashboard может не быть установлен или загружен
3. **Очистка ресурсов** — Вызывайте `unregister_view()` в `on_unload` для удаления зарегистрированного окна
4. **Уникальность ID** — Параметр `id` должен быть уникальным во всем Dashboard, рекомендуется использовать имя модуля напрямую
5. **SVG-иконки** — `icon_svg` должно быть полным тегом `<svg>`, рекомендуется использовать размер `viewBox="0 0 24 24"` и `stroke="currentColor"` для наследования цвета темы Dashboard
6. **Имена функций JS** — Имена функций в `js_content` должны быть уникальными (например, `loadWeatherView`), чтобы избежать конфликтов с другими модулями
7. **Динамическое обновление** — После регистрации/отмены регистрации окна фронтенд Dashboard через WebSocket в реальном времени обновляет боковую панель, обновление страницы пользователя не требуется



### Takumi 图片渲染

# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) — это модуль для рендеринга изображений от **ccd2s**, основанный на [takumi-py](https://github.com/BalconyJH/takumi-py), который позволяет ботам конвертировать HTML, узловые деревья, шаблоны Jinja, SVG и анимации в изображения. Модуль **встроен шрифты китайского и английского языков** (Noto Sans SC / Roboto / Source Code Pro), дополнительные настройки не требуются.

> [!IMPORTANT]
> Takumi **не** является встроенной функцией фреймворка ErisPulse, его необходимо установить отдельно:
>
> ```bash
> epsdk install Takumi
> ```

Используемые сценарии:

- Рендеринг данных / статистики в виде карточек изображений
- Конвертация Markdown / длинного текста в изображения с гарантированной типографикой, чтобы избежать различий в стилях платформ
- Генерация SVG / анимаций для создания динамических визуальных эффектов
- Смешанные китайско-английские иллюстрации (встроенные шрифты готовы к использованию)

---

## Установка и активация

```bash
epsdk install Takumi
```

После установки модуль загружается автоматически. Подтвердите включение в конфигурации:

```toml
[Takumi]
enabled = true

## Быстрый старт

После автоматической загрузки модулей их можно получить через менеджер модулей или с помощью сокращённого способа `sdk`:

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# Эквивалентная запись: takumi = sdk.Takumi
```

### Рендеринг HTML

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>Привет, ErisPulse</h1>
      <p>Сгенерировано с помощью Takumi</p>
    </div>
    """,
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
      font-family: "Noto Sans SC";
    }
    """],
    width=800,
    height=None,   # Автоматическое расширение по содержимому
    lang="zh-CN",
)
```

### Рендеринг дерева узлов

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "Китайский и English можно рендерить напрямую",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

`png` — это `bytes`, которые можно отправить через `event.reply(png, method="Image")` (см. [Отправка результата рендеринга](#отправка-результата-рендеринга)).

---

## API Rendering

`sdk.Takumi` проксирует все возможности базового `takumi_py.Renderer`: все операции рендеринга, измерения, SVG, анимации и методы шаблонов можно вызывать напрямую через `sdk.Takumi`. Для этих методов модуль автоматически внедряет стек встроенных шрифтов-запасных (`takumi.families`) при вызове, без необходимости вручную передавать `font_families`; если значение явно передано, оно переопределяет настройки вызывающего объекта.

### Обзор методов

| Категория | Метод | Возврат | Описание |
|-----------|-------|---------|----------|
| Статический рендеринг | `render_html(html, ...)` | `bytes` | Рендеринг строки HTML |
| | `render_node(node, ...)` | `bytes` | Рендеринг дерева узлов (dict) |
| | `render_template(name, ctx, ...)` | `bytes` | Рендеринг шаблона Jinja |
| | `render_compiled(node, ...)` | `bytes` | Рендеринг предварительно скомпилированного узла |
| SVG вывод | `render_svg_html(html, ...)` | `str` | Вывод SVG (вход: HTML) |
| | `render_svg_node(node, ...)` | `str` | Вывод SVG (вход: дерево узлов) |
| | `render_svg_template(name, ctx, ...)` | `str` | Вывод SVG (вход: шаблон) |
| | `render_svg_compiled(node, ...)` | `str` | Вывод SVG (вход: предварительно скомпилированный) |
| Анимация | `render_animation(scenes, ...)` | `bytes` | Кодирование многокадровой анимации |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | Получение кадра последовательности в заданный момент времени |
| Измерение | `measure_node(node, ...)` | `dict` | Измерение верстки дерева узлов |
| | `measure_html(html, ...)` | `dict` | Измерение верстки HTML |
| | `measure_compiled(node, ...)` | `dict` | Измерение предварительно скомпилированного узла |
| Компиляция | `compile_node(node)` | `CompiledNode` | Компиляция дерева узлов |
| | `compile_html(html, ...)` | `CompiledNode` | Компиляция HTML |
| Шрифты | `register_font(font)` | `list[str]` | Регистрация пользовательского шрифта, возвращает список семейств |
| | `register_fonts(fonts)` | `list[str]` | Массовая регистрация |

> `CompiledNode` предоставляет метод `resource_urls()`, позволяющий заранее обнаружить ссылки на HTTP(S) изображения, подлежащие загрузке, что упрощает подготовку ресурсов.

### Общие параметры

Следующие параметры применяются к методам статического рендеринга и SVG (для методов анимации предусмотрены дополнительные параметры, такие как `fps`, см. соответствующие примеры):

| Параметр | Тип | Значение по умолчанию | Описание |
|----------|-----|----------------------|----------|
| `stylesheets` | `list[str]` | `None` | Список строк CSS на уровне документа; встроенные `style` всё равно анализируются вместе с HTML |
| `width` | `int \| None` | `1200` | Ширина области просмотра (пиксели); `None` — определить из верстки |
| `height` | `int \| None` | `630` | Высота холста (пиксели); `None` — автоматически растянуть по содержимому (см. [Viewport and Output Format](#viewport-and-output-format)) |
| `lang` | `str \| None` | `None` | Языковая метка BCP-47 (например, `zh-CN`), влияет на текстовую верстку и переносы строк |
| `font_families` | `list[str]` | Автоматическое внедрение | Стек шрифтов-запасных; в удобных методах по умолчанию внедряются встроенные шрифты |
| `format` | `str` | `"png"` | Формат вывода (см. [Viewport and Output Format](#viewport-and-output-format)) |
| `device_pixel_ratio` | `float` | `1.0` | Коэффициент пикселей устройства, управляет разрешением вывода |
| `time_ms` | `int` | `0` | Момент выборки анимации (в миллисекундах) |
| `dithering` | `str` | `"none"` | Алгоритм дизеринга: `none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | Качество кодирования с потерями |
| `lossless` | `bool \| None` | `None` | Кодирование без потерь |
| `images` | `list` | `None` | Ресурсы изображений для текущего рендеринга (`ImageResource` или кортеж `(src, bytes)`) |
| `keyframes` | `Mapping` | `None` | Структурированные ключевые кадры, не требуют записи `@keyframes` |
| `options` | `RenderOptions` | — | Группировка аргументов через `RenderOptions(...)`; поля соответствуют таблице выше |

Полное определение полей см. в `takumi_py.RenderOptions`.

### Пример дерева узлов

```python
png = takumi.render_node(
    {
        "type": "container",
        "style": {"padding": "32px", "backgroundColor": "#111827"},
        "children": [
            {"type": "text", "text": "Заголовок", "style": {"fontSize": 32, "color": "white"}},
            {"type": "text", "text": "Основной текст", "style": {"fontSize": 18, "color": "#9ca3af"}},
        ],
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

### Пример шаблона Jinja

```python
png = takumi.render_template(
    "card.html.jinja",
    {"title": "Takumi", "subtitle": "Jinja to image"},
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
    }
    """],
    width=800,
    height=None,
    lang="zh-CN",
)
```

> Пользовательские фильтры Jinja можно внедрить через `filters={...}` или передать полный `jinja2.Environment` через `environment=...`. Подробности о каталоге шаблонов и настройках среды см. в [документации шаблонов takumi-py](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md).

### Пример вывода SVG

```python
svg = takumi.render_svg_html(
    '<div class="card">Hello</div>',
    stylesheets=[".card { width: 800px; color: black; }"],
    width=800,
    height=None,
)
```

### Пример анимации

```python
from takumi_py import AnimationScene

webp = takumi.render_animation(
    [
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "black"}},
            duration_ms=100,
        ),
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "white"}},
            duration_ms=100,
        ),
    ],
    width=64,
    height=64,
    fps=20,
    format="webp",
)
```

> Каждый кадр составлен через `AnimationScene(node, duration_ms=...)`, где `duration_ms` должно быть положительным числом.

---

## Viewport и формат вывода

### Формат вывода

| Сценарий | Значение `format` |
|------|---------------|
| Статичное изображение | `png` (по умолчанию) / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| Анимация | `webp` (по умолчанию) / `apng` / `gif` |

`format="raw"` возвращает поток байтов RGBA в формате строка-первый (row-major) для кастомной обработки на уровне пикселей.

### О width и height

Роли `width` и `height` не симметричны:

- `width` — это**ширина области просмотра (viewport width)**, текст и макет перестраиваются с учетом ширины. Должен быть**фиксированным** конкретным значением (например, `800`), иначе холст будет растягиваться до естественной ширины содержимого, текст не будет переноситься, а размер будет неконтролируемым.
- `height` — это**высота холста**, она растет по мере наполнения контентом. Значение по умолчанию для `height` равно `630`; при передаче `height=None` Takumi **автоматически увеличит высоту области просмотра в соответствии с содержимым** (auto viewport).

> [!TIP]
> **Рекомендуемая комбинация: фиксированный `width` + `height=None`.** Передавайте конкретное значение `height` только тогда, когда вам нужен холст фиксированного размера или эффект обрезки.

> [!NOTE]
> Технически значение `width` / `height` можно передать как `None`, чтобы разрешить выводу определять его на основе макета (например, когда узел сам объявляет свой размер); если оба значения заданы, размер вывода определен однозначно.

---

## Шрифты

### Встроенные шрифты

| Шрифт | family | Категория |
|------|--------|------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif（italic） |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace（italic） |

Свойства модуля:

| Свойство | Описание |
|------|------|
| `takumi.fonts` | Список имен файлов встроенных шрифтов |
| `takumi.families` | Список зарегистрированных шрифтов `family` |

### Автоматическая инъекция

Все методы рендеринга, измерения, SVG, анимации и шаблонов на `sdk.Takumi` автоматически внедряют `takumi.families` как стек отложенных шрифтов. Если вы напрямую вызываете `takumi.renderer` (нативный экземпляр) или создаете независимый экземпляр через `create_renderer()`, необходимо вручную передать `font_families=takumi.families`.

### Пользовательские шрифты

```python
from takumi_py import FontResource

families = takumi.renderer.register_font(
    FontResource(
        font_bytes,
        name="MyFont",
        weight=400,
        style="normal",
        generic_family="sans-serif",
    )
)
```

`register_font` возвращает список имен зарегистрированных `family`, которые можно передать как `font_families` при последующем рендеринге.

---

## Экземпляр рендерера

### Встроенный Renderer

`takumi.renderer` — это оригинальный экземпляр `takumi_py.Renderer`. При прямом вызове необходимо вручную передать `font_families`:

```python
png = takumi.renderer.render_html(
    "<div>Привет</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### Отдельный Renderer

При необходимости изолировать кэш шрифтов / изображений / ресурсов (долговременные процессы, сценарии мульти-аренды) можно создать отдельный `Renderer`, встроенные шрифты будут автоматически зарегистрированы:

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>Отдельный Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=None,
    lang="zh-CN",
)
```

`create_renderer()` принимает конструкторные аргументы `takumi_py.Renderer`:

| Параметр | Тип | Значение по умолчанию | Описание |
|------|------|--------|------|
| `load_default_fonts` | `bool` | `False` | Загружать ли шрифты, входящие в состав takumi-py (встроенные шрифты всегда загружаются) |
| `fonts` | `list[FontResource]` | `None` | Дополнительные зарегистрированные пользовательские шрифты |
| `cache_max_bytes` | `int \| None` | `None` | Лимит размера кэша ресурсов (байты); `0` отключает |
| `persistent_images` | `list` | `None` | Персистентные ресурсы изображений |

> Отдельный экземпляр не проходит через модульный прокси, поэтому для сохранения унифицированного стека отступов встроенных шрифтов необходимо явно передать `font_families=takumi.families`. Если явно передать `font_families`, модуль будет уважать настройки вызывающей стороны и не внедрять стек отступов по умолчанию; эквивалентно этому работает и `RenderOptions(font_families=...)`.

---

## Отправка результатов рендеринга

Полученное изображение — это `bytes`, которое можно отправить напрямую через ответ на событие:

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="ru-RU")

# Способ 1: ответ через метод Image
await event.reply(png, method="Image")

# Способ 2: ответ через сегмент сообщения OneBot12
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> Обработка инкапсуляции изображений для разных платформ выполняется адаптером. Подробнее см. [MessageBuilder 详解](../ru/advanced/message-builder.md) и [发送方法规范](../ru/standards/send-method-spec.md).

---

## Настройка

```toml
[Takumi]
enabled = true
```

---

## Ссылки

- PyPI: <https://pypi.org/project/ErisPulse-Takumi/>
- Репозиторий: <https://github.com/ccd2s/ErisPulse-Takumi> (автор [@ccd2s](https://github.com/ccd2s))
- Движок: <https://github.com/BalconyJH/takumi-py>
- Документация takumi-py: <https://github.com/BalconyJH/takumi-py/blob/main/docs/index.md>



====
平台概览
====


### 平台特性与 SendDSL 通用语法

# Документация по функциям платформы ErisPulse

> Базовый протокол: [OneBot12](https://12.onebot.dev/) 
> 
> Данный документ является **гидом по платформенным функциям**, который включает:
> - Примеры цепочечного вызова методов отправки, поддерживаемых различными адаптерами
> - Описание специфических событий/форматов сообщений платформы
> 
> Общие методы использования см. в:
> - [Основные понятия](../getting-started/basic-concepts.md)
> - [Стандарт преобразования событий](../standards/event-conversion.md)  
> - [Спецификация ответов API](../standards/api-response.md)

---

## Платформенные функции

Эта часть поддерживается разработчиками адаптеров и предназначена для описания отличий и расширений, внесённых в адаптер по сравнению со стандартом OneBot12. Для получения подробной информации см. документацию по каждой платформе:

- [Заметки по поддержке](maintain-notes.md)

- [Особенности платформы Yunhu](docs/ru/yunhu.md)
- [Особенности платформы Yunhu User](docs/ru/yunhu_user.md)
- [Особенности платформы Telegram](docs/ru/telegram.md)
- [Особенности платформы OneBot11](docs/ru/onebot11.md)
- [Особенности платформы OneBot12](docs/ru/onebot12.md)
- [Особенности платформы Email](docs/ru/email.md)
- [Особенности платформы Kook(开黑啦)](docs/ru/kook.md)
- [Особенности платформы Matrix](docs/ru/matrix.md)
- [Особенности платформы QQ официального бота](docs/ru/qqbot.md)
- [Особенности платформы Huafen Coffeehouse](docs/ru/ideaura.md)
- [Особенности платформы Discord](docs/ru/discord.md)
- [Особенности протокола моста Webhook](docs/ru/webhook.md)
- [Особенности платформы WeChat Official Account](docs/ru/wechatmp.md)

> Кроме того, есть адаптер `sandbox`, но для него не требуется документация по платформенным функциям

---

## Общие интерфейсы

### Цепочечный вызов метода Send
Все адаптеры поддерживают следующий стандартный способ вызова:

> **Важно:** `{AdapterName}` в документации нужно заменить на фактическое имя адаптера (например, `yunhu`, `telegram`, `onebot11`, `email` и т.д.).

1. Указание типа и ID: `To(type,id).Func()`
   ```python
   # Получение экземпляра адаптера
   my_adapter = adapter.get("{AdapterName}")
   
   # Отправка сообщения
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # Например:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. Только указание ID: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # Например:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. Указание отправляющего аккаунта: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # Например:
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. Прямой вызов: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # Например:
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### Асинхронная отправка и обработка результатов

Методы Send DSL возвращают объект `asyncio.Task`, что означает, что вы можете выбрать, будете ли вы немедленно ожидать результат:

```python
# Получение экземпляра адаптера
my_adapter = adapter.get("{AdapterName}")

# Не ожидание результата, сообщение отправляется в фоновом режиме
task = my_adapter.Send.To("user", "123").Text("Hello")

# Если нужно получить результат отправки, можно подождать позже
result = await task
```

#### Декораторы правил отправки

В реальном разработке часто требуется: выполнение последующей логики только после успешной отправки, автоматическая повторная попытка при сбое, отмена при таймауте, мониторинг прогресса отправки и т.д. DSL Send содержит набор встроенных декораторов правил отправки, которые можно добавлять цепочечным способом:

| Метод | Описание |
|--------|------|
| `.Hook(callback)` | Вызов обратного вызова при успешной отправке (можно вызывать несколько раз) |
| `.Retry(times=1)` | Автоматическая повторная попытка N раз (включая первую, всего N+1 попыток) |
| `.Timeout(seconds)` | Таймаут единичной отправки, отмена при истечении времени (можно использовать вместе с Retry) |
| `.Defer(seconds)` | Отложенная отправка (внутрипроцессное таймерное ожидание, не сохраняется) |
| `.OnProgress(callback)` | Обратный вызов прогресса на каждом этапе, передаёт SendContext |
| `.OnError(callback)` | Обратный вызов при окончательном сбое (вызывается только один раз) |

```python
yunhu = adapter.get("yunhu")

# Вычитание очков только после успешной отправки
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消费成功"))

# Повторная попытка + таймаут + мониторинг прогресса
def on_progress(ctx):
    print(f"Этап: {ctx.stage}, попытка: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Максимум 3 повторные попытки
        .Timeout(10)           # Таймаут 10 секунд на каждую попытку
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要通知"))
```

Методы правил возвращают `self`, и их необходимо вызывать до методов отправки (Text/Image и т.д.). `SendContext` содержит поля `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, `result` и другие, что помогает в мониторинге.

#### Режим построения пакетов (Build)

Построение нескольких методов отправки в одной цепочке, с последующим единым выполнением. Подходит для сценариев "отправка нескольких сообщений за один раз":

```python
yunhu = adapter.get("yunhu")

# Построение нескольких сообщений, отправка в едином порядке
results = await (yunhu.Send.To("user", "123")
                .Build()                     # Переход в режим построения
                .Text("通知一")
                .Image("pic.jpg")
                .Text("通知二")
                .send_all())                 # Единое выполнение
# results = [результат Text, результат Image, результат Text]
```

`.send_all()` по умолчанию выполняется **параллельно** (высокая эффективность). При необходимости сохранения порядка сообщений вызовите `.Sequential()` для последовательного выполнения:

```python
# Последовательное выполнение (сохранение порядка) + повторная попытка при сбое
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Последовательная отправка
       .Retry(2)                     # Каждая неудачная отправка повторяется
       .Text("第一条").Text("第二条")
       .send_all())
```

Пакетное выполнение использует стратегию "продолжение при сбое": если одна отправка не удалась, это не прерывает другие, и неудачные отправки автоматически повторяются. Пакетная отправка также поддерживает `Hook` для всей группы (вызывается при успешной отправке всех сообщений), `OnError` (вызывается при наличии сбоев), и `OnProgress` (обратный вызов прогресса).

> Более подробное описание правил и построения пакетов см. в [Подробном разборе SendDSL](../developer-guide/adapters/send-dsl.md).

### Обработка событий
Существует три способа прослушивания событий:

1. Прослушивание оригинальных событий платформы:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено оригинальное событие {AdapterName}: {data}")
   ```

2. Прослушивание стандартных событий OneBot12:
   ```python
   from ErisPulse.Core import adapter, logger

   # Прослушивание стандартного события OneBot12
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Получено стандартное событие: {data}")

   # Прослушивание стандартного события конкретной платформы
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Получено стандартное событие {AdapterName}: {data}")
   ```

3. Прослушивание через модуль Event:
    События в модуле `Event` основаны на функции `adapter.on()`, поэтому формат событий, предоставляемый `Event`, является стандартным событием OneBot12

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="发送问候消息", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"Получено сообщение: {event}")
    async def notice_handler(event):
        logger.info(f"Получено уведомление: {event}")
    async def request_handler(event):
        logger.info(f"Получен запрос: {event}")
    async def command_handler(event):
        logger.info(f"Получена команда: {event}")
    ```

Наиболее рекомендуемым способом является использование модуля `Event` для обработки событий, поскольку модуль `Event` предоставляет богатый набор типов событий и методов обработки событий.

---

## Стандартные форматы
Для удобства приведены простые форматы событий. Для получения подробной информации см. ссылки выше.

> **Важно:** Ниже приведён базовый стандартный формат OneBot12, каждый адаптер может расширять его дополнительными полями. Для получения конкретной информации см. описание специфических функций каждого адаптера.

### Стандартный формат событий
Все адаптеры должны реализовывать формат преобразования событий:
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### Стандартный формат ответа
#### Успешная отправка сообщения
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### Неудачная отправка сообщения
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "缺少必要参数",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## Ссылки

Проект ErisPulse:
- [Основной репозиторий](https://github.com/ErisPulse/ErisPulse/)
- [Репозиторий адаптера Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Репозиторий адаптера Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [Репозиторий адаптера OneBot](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

Связанные официальные документации:
- [Официальная документация протокола OneBot V11](https://github.com/botuniverse/onebot-11)
- [Официальная документация Telegram Bot API](https://core.telegram.org/bots/api)
- [Официальная документация Yunhu](https://www.yhchat.com/document/1-3)

## Участие в разработке

Мы приветствуем больше разработчиков, участвующих в написании и поддержке документации адаптеров! Пожалуйста, следуйте следующим шагам для внесения вклада:
1. Fork [ErisPuls](https://github.com/ErisPulse/ErisPulse) репозитория.
2. Создайте Markdown файл в каталоге `docs/platform-features/` и назовите его в формате `<имя платформы>.md`.
3. Добавьте ссылку на ваш вклад в адаптер и соответствующую официальную документацию в этот файл `README.md`.
4. Отправьте Pull Request.

Спасибо за вашу поддержку!

