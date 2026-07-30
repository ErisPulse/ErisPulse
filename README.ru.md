<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Русский**

# ErisPulse

**Написано один раз, развернуто на QQ / Telegram / Kook / Yunhu / WeChat Public Account / OneBot12 / ... на нескольких платформах.**

Фреймворк для разработки мультиплатформенных чат-ботов на основе событий.

Основан на стандарте OneBot12, что позволяет развернуть одно приложение на нескольких платформах; гибкая система плагинов, поддержка горячей перезагрузки и полный набор инструментов для разработчиков, подходящий для различных сценариев — от простых чат-ботов до сложных автоматизированных систем.

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen" alt="Stars"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Downloads"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge" alt="Ruff"></a>
  <a href="https://socket.dev/pypi/package/erispulse"><img src="https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white" alt="Socket"></a>
  <a href="https://www.erisdev.com"><img src="https://img.shields.io/badge/文档-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="文档"></a>
  <a href="https://deepwiki.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/DeepWiki-ErisPulse-8A2BE2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="DeepWiki"></a>
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="模块市场"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="讨论"></a>
</p>

<br clear="both">

---

<div align="center">

### Основные возможности

</div>

<table>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="Архитектура на основе событий" />

### Архитектура на основе событий

Единая модель событий на основе стандарта OneBot12 — больше не нужно писать отдельные if/elif для каждого платформенного типа, один обработчик автоматически адаптируется ко всем адаптерам

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="Кроссплатформенная совместимость" />

### Кроссплатформенная совместимость

Один и тот же код бизнес-логики работает на всех платформах — один раз написано, можно обслуживать QQ / Telegram / Kook / Yunhu / WeChat Public Account и другие 15+ платформ, без повторного разработки

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="Модульная архитектура" />

### Модульная архитектура

Гибкая система плагинов поддерживает горячую подстановку модулей во время выполнения — установка/удаление/включение/отключение модулей без перезапуска процесса, как конструктор для сборки функций бота

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="Горячая перезагрузка" />

### Горячая перезагрузка

Цикл разработки сокращен с 10 секунд перезапуска до 0.5 секунд — сохранение файла применяется сразу, опыт разработки и отладки приближается к интерпретируемым языкам

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="Помощь ИИ" />

### Помощь ИИ

Описание требований на естественном языке напрямую генерирует готовый модуль — не умеете писать адаптер? Скажите ИИ, на какую платформу подключаться, и он поможет вам написать код

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="Легкость и элегантность" />

### Легкость и элегантность

Интуитивно понятный API в виде цепочки вызовов — @пользователя, ответ, повтор, массовая отправка и другие сложные логики выполняются одной строкой, код легкий и читаемый, как перо

</td>
</tr>
</table>

---

## Принцип работы

ErisPulse скрывает различия платформ через слой адаптеров, позволяя бизнес-логике работать только с событиями:

```mermaid
graph LR
    subgraph Platforms[Платформы]
        QQ["QQ"]
        TG["Telegram"]
        Kook["Kook"]
        YH["Yunhu"]
        WX["WeChat Public Account"]
    end

    subgraph Adapters[Слой адаптеров]
        A1["Адаптер QQ"]
        A2["Адаптер Telegram"]
        A3["Адаптер Kook"]
        A4["Адаптер Yunhu"]
        A5["Адаптер WeChat Public Account"]
    end

    Event["Event Event Bus<br/>Middleware → Распределение command/message/notice/request/meta"]

    subgraph Modules[Бизнес-модули]
        M1["Обработчик команд<br/>@command"]
        M2["Обработчик сообщений<br/>@message"]
        M3["Ваш модуль"]
    end

    QQ --> A1
    TG --> A2
    Kook --> A3
    YH --> A4
    WX --> A5

    A1 -->|"OB12 событие"| Event
    A2 -->|"OB12 событие"| Event
    A3 -->|"OB12 событие"| Event
    A4 -->|"OB12 событие"| Event
    A5 -->|"OB12 событие"| Event

    Event -->|"Распределение"| M1
    Event -->|"Распределение"| M2
    Event -->|"Распределение"| M3

    M1 -.->|"event.reply()<br/>SendDSL"| Event
    Event -.->|"Отправка"| A1
```

- **Слой адаптеров** преобразует протоколы платформ в стандартные события OneBot12, бизнес-модули не видят различий платформ
- **Event Bus** сначала выполняет цепочку middleware, затем распределяет события по пяти типам обработчиков
- **Ваш код** подписывается на события с помощью декораторов, использует `event.reply()` или SendDSL для ответа — ответное сообщение отправляется по тому же пути обратно на платформу

Детали архитектуры, структура модулей, процесс инициализации, жизненный цикл событий и т.д., см. в [Обзоре архитектуры](docs/ru/architecture.md).

---

## Быстрый старт

### Сценарий установки с одной командой (рекомендуется)

Сценарий автоматически определяет среду (Docker, Python, uv), предлагает подходящий способ установки, поддерживает несколько языков (китайский/English/日本語/Русский/繁體中文).

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

<table>
<tr>
<td align="center" width="50%">

**Демонстрация установки через Docker**

<video src="https://github.com/user-attachments/assets/a367a466-4678-46a9-b101-073a86388ede" controls width="100%"></video>

</td>
<td align="center" width="50%">

**Демонстрация установки через pip**

<video src="https://github.com/user-attachments/assets/a2df4009-dba6-411e-b79d-4454a168d063" controls width="100%"></video>

</td>
</tr>
</table>

### Использование Docker (рекомендуется)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Недоступен Docker Hub?</summary>

Если Docker Hub недоступен, можно использовать GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

При использовании образа ghcr.io необходимо изменить `docker-compose.yml`:
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>Быстрый запуск</summary>

```bash
# Скачать docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Установить токен для входа в Dashboard и запустить
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

После запуска перейдите по адресу `http://<host>:8000/Dashboard` и войдите в панель управления с установленным токеном.

> Образ содержит фреймворк ErisPulse и панель управления Dashboard, поддерживает архитектуры `linux/amd64` и `linux/arm64`.
>
> **Долговременное хранение**: конфигурационные файлы и установленные модули/адаптеры сохраняются на хост-машине через тома, при перезапуске контейнера данные не теряются. Обновление фреймворка выполняется через горячее обновление в Dashboard.

</details>

<details>

</details>

<details>
<summary>Переменные окружения Docker</summary>

| Переменная | Значение по умолчанию | Описание |
|------|--------|------|
| `ERISPULSE_DASHBOARD_TOKEN` | пусто | Токен для входа в Dashboard (автоматически записывается в конфигурацию) |
| `ERISPULSE_PORT` | `8000` | Порт для Dashboard |
| `ERISPULSE_TAG` | `latest` | Тег образа, можно установить `dev` для предварительного выпуска |
| `ERISPULSE_BUILD_TARGET` | `production` | Цель сборки: `production` (стабильная версия) или `dev` (предварительный выпуск) |
| `CONTAINER_NAME` | `erispulse` | Имя контейнера |
| `TZ` | `Asia/Shanghai` | Часовой пояс контейнера |
| `LANG` | `en_US.UTF-8` | Язык системы, автоматически определяется язык интерфейса запуска |
| `ERISPULSE_LANG` | пусто | Принудительный язык интерфейса запуска: `zh` / `zh_TW` / `en` / `ja` / `ru` (переопределяет `LANG`) |

</details>

### Магазин приложений 1Panel

Установите ErisPulse через [1Panel](https://1panel.cn) одним кликом, подробнее в [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse доступен в стороннем репозитории [okxlin/appstore](https://github.com/okxlin/appstore) для установки через магазин приложений 1Panel.

### Установка через pip

```bash
pip install ErisPulse
```

> Также можно использовать сценарий установки с одной командой, который автоматически определяет среду и направляет на настройку.

### Инициализация проекта

```bash
# Интерактивная инициализация
epsdk init

# Быстрая инициализация (указать имя проекта)
epsdk init -q -n my_bot
```

### Создание первого бота

Создайте файл `main.py`:

<table>
<tr>
<td width="50%" valign="top">

**Обработчик команд**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="Отправить приветственное сообщение")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "друг"
    await event.reply(f"Привет, {user_name}!")

@command("ping", help="Проверить, работает ли бот")
async def ping_handler(event):
    await event.reply("Pong! Бот работает нормально.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**Описание эффекта**

Отправка `/hello`

Бот отвечает: `Привет, {имя пользователя}!`

---

Отправка `/ping`

Бот отвечает: `Pong! Бот работает нормально.`

---

**Способы запуска**

```bash
epsdk run main.py
# или в режиме разработки
epsdk run main.py --reload
```

</td>
</tr>
</table>

Дополнительные подробности см. в:
- [Руководство по быстрому старту](docs/ru/quick-start.md)
- [Введение](docs/ru/getting-started/)

---

## Один и тот же код. Разные платформы.

*Одинаковые обработчики команд. Разные платформы. Без изменений бизнес-логики.*

<table>
<tr>
<td align="center" width="33%">

**Kook**

<img src=".github/assets/demo-kook.png" alt="Демонстрация Kook" />

</td>
<td align="center" width="33%">

**QQ**

<img src=".github/assets/demo-qq.png" alt="Демонстрация QQ" />

</td>
<td align="center" width="33%">

**Yunhu**

<img src=".github/assets/demo-yunhu.png" alt="Демонстрация Yunhu" />

</td>
</tr>
</table>

---

## Цепочка вызовов DSL для отправки

Одним цепочным вызовом выполняется вся логика отправки: @пользователя, ответ, повтор, таймаут, обратный вызов:

```python
yunhu = sdk.adapter.get("yunhu")

# Одиночная отправка: @пользователя + ответ + повтор + успешный обратный вызов
await (yunhu.Send.To("group", "123")
       .At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Отправка успешна!"))
       .Text("Привет"))

# Массовая отправка: одна цепочка для нескольких сообщений
results = await (yunhu.Send.To("user", "123")
                .Build()
                .Text("Уведомление 1")
                .Image("pic.jpg")
                .Retry(2)
                .send_all())
```

> Поддержка Hook (успешный обратный вызов), Retry (повтор при ошибке), Timeout (отмена по таймауту), OnProgress (мониторинг прогресса), Defer (отложенная отправка), Build (построение пакета) и других цепочных методов, см. [Документацию по SendDSL](docs/ru/developer-guide/adapters/send-dsl.md).

---

## Примеры многократных диалогов

ErisPulse включает мощный движок многократных диалогов, легко реализующий сценарии с подсказками, сбором информации и т.д.:

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Добро пожаловать на регистрацию!")
    
    # Многоэтапный сбор информации пользователя, автоматическая проверка
    data = await conv.collect([
        {"key": "name", "prompt": "Пожалуйста, введите имя"},
        {"key": "age", "prompt": "Пожалуйста, введите возраст",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "Возраст должен быть числом, пожалуйста, повторите ввод"},
    ])
    
    if data and await conv.confirm(f"Подтвердить регистрацию? Имя: {data['name']}, Возраст: {data['age']}"):
        # Использование SendDSL для активной отправки уведомления
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"Регистрация прошла успешно! Добро пожаловать, {data['name']}")
        # или await event.reply("Регистрация прошла успешно!")

# Автоматическая обработка запроса на добавление в друзья
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # Принять запрос
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"Запрос на добавление в друзья автоматически принят, добро пожаловать, {user_name}")
```

<details>
<summary>Больше примеров API Conversation (ветвления / выбор / сохранение)</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # Вариантный вопрос
    answer = await conv.choose("Кто создатель Python?", [
        "Guido van Rossum",
        "James Gosling", 
        "Dennis Ritchie",
    ])
    
    if answer == 0:
        await conv.say("Правильно!")
    elif answer is None:
        await conv.say("Время вышло, попробуйте снова!")
    else:
        await conv.say("Неправильно, правильный ответ — Guido van Rossum")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # Ветвление, построение сложного интерактивного процесса
    @conv.branch("main")
    async def main_menu():
        await conv.say("=== Главное меню ===\n1. Личная информация\n2. Настройки\n3. Выйти")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "1":
            await conv.goto("profile")
    
    @conv.branch("profile")
    async def profile():
        await conv.say("Имя: Alice\n0. Вернуться")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")
    
    await conv.start()
```

См. [Многократные диалоги Conversation](docs/ru/advanced/conversation.md)

</details>

---

## Основные модули

ErisPulse предоставляет полный набор инструментов для разработки мультиплатформенных ботов, каждый модуль отвечает за свою задачу:

```mermaid
graph TB
    SDK["sdk<br/>Единый вход"]

    SDK --> Event["Event<br/>Система событий"]
    SDK --> AdapterMgr["Adapter<br/>Управление адаптерами"]
    SDK --> ModuleMgr["Module<br/>Управление модулями"]
    SDK --> Router["Router<br/>HTTP/WS маршрутизация"]
    SDK --> Storage["Storage<br/>SQLite хранилище"]
    SDK --> Config["Config<br/>Управление конфигурацией"]
    SDK --> Lifecycle["Lifecycle<br/>Жизненный цикл"]
    SDK --> Logger["Logger<br/>Система логирования"]
    SDK --> Client["HttpClient<br/>HTTP клиент"]
```

| Модуль | Описание |
|------|------|
| **Event** | Система событий, предоставляющая пять типов событий: command / message / notice / request / meta + многократные диалоги Conversation |
| **Adapter** | Управление адаптерами, базовый класс BaseAdapter унифицирует преобразование событий и SendDSL, поддерживает QQ / Telegram / Kook / Yunhu / WeChat Public Account и другие 15+ платформ |
| **Module** | Управление модулями, базовый класс BaseModule + декларация зависимостей и топологическая сортировка загрузки |
| **SendDSL** | Цепочка отправки, @пользователя, ответ, повтор, таймаут, массовая отправка и другие сложные логики выполняются одной строкой |
| **Router** | Система маршрутизации HTTP/WebSocket (FastAPI + Uvicorn) |
| **Storage** | Хранилище на основе SQLite + универсальный SQL цепочный запрос |
| **Config** | Управление конфигурацией в формате TOML |
| **Lifecycle** | Точки вызова жизненного цикла (core.init / adapter.* / module.*) |
| **Logger** | Модульная система логирования, поддерживает под-логгеры |
| **HttpClient** | Единый HTTP/WS клиент (на основе aiohttp), встроенные повторы и исключения ErisPulse |

Детали архитектуры (процесс инициализации, события жизненного цикла, стратегия загрузки модулей), см. в [Обзоре архитектуры](docs/ru/architecture.md).

---

## Экосистема

ErisPulse — это не просто фреймворк. Можно сразу начать работать, не нужно создавать колесо с нуля.

<table>
<tr>
<td align="center" width="25%">

**Фреймворк**

Основной рантайм

Единая модель событий и сообщений

</td>
<td align="center" width="25%">

**Dashboard**

Визуальное управление

Плагины · Логи · Конфигурация

[Онлайн демонстрация →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

Естественный язык → готовый модуль

[Опыт использования →](https://builder.erisdev.com)

</td>
<td align="center" width="25%">

**Модульный рынок**

Готовые плагины для установки

[Просмотр модулей →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**Адаптеры**

Подключение к 15+ платформам

</td>
<td align="center" width="25%">

**Документация**

[erisdev.com](https://www.erisdev.com)

</td>
<td align="center" width="25%">

**Docker**

Поддержка нескольких архитектур

`erispulse/erispulse`

</td>
<td align="center" width="25%">

**CLI**

Инструмент epsdk для создания проектов

</td>
</tr>
</table>

---

## Поддерживаемые платформы

Приглашаем к contribute! Не знаете, с чего начать? Смотрите [Руководство по contribute](docs/ru/contributing/README.md).

| Адаптер | Описание |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Платформа мгновенных сообщений Kook |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Децентрализованный протокол общения Matrix |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | Общий протокол роботов OneBot v11 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | Стандартный протокол OneBot v12 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | Официальная платформа роботов QQ |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Веб-среда отладки, без подключения к реальной платформе |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Глобальная платформа мгновенных сообщений Telegram |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Адаптер для отправки и получения протокола электронной почты |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Корпоративная платформа мгновенных сообщений Yunhu (подключение роботов) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Адаптер подключения на основе протокола Yunhu User |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Глобальная платформа общения Discord, поддержка серверов, каналов и личных сообщений |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | Общий адаптер HTTP-моста, подключение к любой системе |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [WeChat Public Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Официальная платформа WeChat Public Account |

Смотрите [детальное описание адаптеров](docs/ru/platform-guide/README.md)

---

## Сообщество

Общайтесь с нами:

- Telegram: <https://t.me/ErisPulse>
- QQ группа: <https://qm.qq.com/q/TOwnCmypcy>
- Yunhu группа: <https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

---

### Руководство по contribute

Здоровье проекта ErisPulse нуждается в вашем вкладе! Мы приветствуем любые формы contribute:

1. **Сообщения об ошибках** — отправьте отчет об ошибке в [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Запросы на функции** — предложите новые идеи через [общение в сообществе](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Кодовый contribute** — перед отправкой PR прочтите [стиль кода](docs/ru/styleguide/) и [руководство по contribute](CONTRIBUTING.md)
4. **Улучшение документации** — помогите улучшить документацию и примеры кода

**Первый contribute?** Начните здесь 👉 [Первый contribute](docs/ru/contributing/first-contribution.md)

[Присоединиться к обсуждению сообщества](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Благодарности

<img src=".github/assets/thanks.png" width="200" alt="Благодарности" />

Часть кода этого проекта основана на [sdkFrame](https://github.com/runoneall/sdkFrame).

Стандартизированный слой основных адаптеров основан на и вдохновлен спецификации [OneBot12](https://12.onebot.dev/).

Особая благодарность экосистеме и сообществу Yunhu.

Ранние исследования и развитие ErisPulse невозможны без поддержки сообщества разработчиков Yunhu, многие идеи, адаптеры и практический опыт родились здесь.

Также благодарим всех разработчиков и авторов проектов, внесших вклад в ErisPulse, OneBot и экосистему open source.

</div>