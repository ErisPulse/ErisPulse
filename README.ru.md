<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Русский**

# ErisPulse

**Написан один раз, развернут на QQ / Telegram / Kook / Yunhu / WeChat Official Account / OneBot12 / ... нескольких платформах.**

Фреймворк разработки чат-ботов с событийно-ориентированной архитектурой.

На основе стандарта OneBot12, один раз написано, развернуто на нескольких платформах; гибкая система плагинов, поддержка горячей перезагрузки и полный инструментарий для разработчиков, подходит для различных сценариев, от простых чат-ботов до сложных автоматизированных систем.

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

### Основные особенности

</div>

<table>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="Архитектура на основе событий" />

### Архитектура на основе событий

Единая модель событий на основе стандарта OneBot12 — больше не нужно писать для каждой платформы отдельный блок if/elif для определения типа сообщения, один обработчик автоматически адаптируется ко всем адаптерам

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="Кросс-платформенная совместимость" />

### Кросс-платформенная совместимость

Один и тот же код бизнес-логики работает на всех платформах — один раз написано, можно обслуживать QQ / Telegram / Kook / Yunhu / WeChat Official Account и более 15 платформ, без повторного разработки

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="Модульная архитектура" />

### Модульная архитектура

Гибкая система плагинов поддерживает горячую подмену модулей во время выполнения — установка/удаление/включение/отключение модулей без перезапуска процесса, в сочетании с системой сфер, точное управление доступностью модулей по платформе / Bot / сессии, как конструктор, собирайте возможности бота

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="Горячая перезагрузка" />

### Горячая перезагрузка

Локальные плагины применяются сразу после сохранения файла (0,5-секундный перезапуск), любой модуль (включая пакеты PyPI) `sdk.reload_module()` — одна строка для горячей перезагрузки, опыт разработки и отладки близок к скриптам интерпретатора

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="Помощь ИИ" />

### Помощь ИИ

Описание требований на естественном языке напрямую генерирует доступный модуль — не умеете писать адаптер? Скажите ИИ, на какую платформу вы хотите подключиться, и он поможет вам написать

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="Лёгкость и элегантность" />

### Лёгкость и элегантность

Интуитивно понятный API в виде цепочки — @пользователя, ответ, повтор, массовая отправка и другие сложные логики выполняются одной строкой, код как перышко — лёгкий и читаемый

</td>
</tr>
</table>

---

## Области видимости (Scope) — трёхмерная система управления правами

Без изменения кода модуля, в конфигурации можно объявить "в каком диапазоне он будет действовать":

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]           # ① Модульный уровень: на этой платформе доступны только эти модули (glob / регулярное выражение)

[ErisPulse.scope.identity.users.onebot11]
deny = ["u_bad", "spam_*"]            # ② Уровень идентификации: события пользователей из чёрного списка будут отбрасываться

[ErisPulse.scope.actions.MyModule]
send = { allow = ["Text"] }           # ③ Выходной уровень: этот модуль может отправлять только текст
api = { deny = ["set_*", "leave_*"] } #    и запрещает использование API-методов управления
```

```python
# Также можно вызывать в режиме выполнения, изменения вступают в силу немедленно (поддержка точечных путей в виде словаря)
sdk.scope.set_action("MyModule", "api", deny=["set_*"])
```

> Подробнее см. [Области видимости (scope)](docs/ru/advanced/scope.md)

---

## Переопределение событий — без изменения кода модуля, переопределение поведения любого типа события

```toml
# Переопределение условия запуска обработчика сообщений (AND с условиями в коде; поддержка всех типов: meta/message/notice/request/command)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# Переопределение реализации команды (параметры master / hidden / aliases / prefix и т.д., приоритет у пользователя)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
```

> Подробнее см. [Переопределение событий](docs/ru/getting-started/event-handling.md)

---

## Принцип работы

ErisPulse скрывает различия между платформами через слой адаптеров, позволяя бизнес-коду заботиться только о событиях:

```mermaid
graph LR
    subgraph Platforms[Платформы]
        QQ["QQ"]
        TG["Telegram"]
        Kook["Kook"]
        YH["Yunhu"]
        WX["WeChat Official Account"]
    end

    subgraph Adapters[Слой адаптеров]
        A1["QQ адаптер"]
        A2["Telegram адаптер"]
        A3["Kook адаптер"]
        A4["Yunhu адаптер"]
        A5["WeChat адаптер"]
    end

    Event["Event событийный буфер<br/>中间件 → 分发 command/message/notice/request/meta"]

    subgraph Modules[Бизнес-модули]
        M1["Командный обработчик<br/>@command"]
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

    Event -->|"Раздача"| M1
    Event -->|"Раздача"| M2
    Event -->|"Раздача"| M3

    M1 -.->|"event.reply()<br/>SendDSL"| Event
    Event -.->|"Отправка"| A1
```

- **Слой адаптеров** преобразует протоколы платформ в стандартные события OneBot12, бизнес-модули не видят различий между платформами
- **Событийный буфер** сначала выполняет цепочку промежуточного ПО, затем по типу события раздаёт обработчики пяти категорий
- **Ваш код** подписывается на события с помощью декораторов, использует `event.reply()` или SendDSL для ответа — ответное сообщение отправляется по тому же пути обратно на платформу

Подробная информация о составе модулей, процессе инициализации, жизненного цикла и т.д., см. [Обзор архитектуры](docs/ru/architecture.md).

---

## Быстрый старт

### Сценарий однокнопочного установки (рекомендуется)

Сценарий установки автоматически определит вашу среду (Docker, Python, uv), предложит выбрать наиболее подходящий способ установки, поддерживает несколько языков (китайский / English / 日本語 / Русский / 繁體中文).

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

При использовании образа ghcr.io необходимо изменить `docker-compose.yml`, изменив значение image:
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

После запуска перейдите по адресу `http://<host>:8000/Dashboard`, используя установленный токен для входа в панель управления Dashboard.

> Образ содержит фреймворк ErisPulse и панель управления Dashboard, поддерживает архитектуры `linux/amd64` и `linux/arm64`.
>
> **Постоянное хранение:** конфигурационные файлы и установленные модули/адаптеры сохраняются на хост-машине с помощью томов, при перезапуске контейнера они не будут потеряны. Обновление самого фреймворка выполняется через горячую замену в Dashboard.

</details>

<details>
<summary>Переменные окружения Docker</summary>

| Переменная | Значение по умолчанию | Описание |
|------|--------|------|
| `ERISPULSE_DASHBOARD_TOKEN` | пусто | Токен для входа в Dashboard (автоматически записывается в конфигурацию) |
| `ERISPULSE_PORT` | `8000` | Порт для Dashboard |
| `ERISPULSE_TAG` | `latest` | Тег образа, можно установить `dev` для предварительного выпуска |
| `ERISPULSE_BUILD_TARGET` | `production` | Цель сборки: `production` (стабильный выпуск) или `dev` (предварительный выпуск) |
| `CONTAINER_NAME` | `erispulse` | Имя контейнера |
| `TZ` | `Asia/Shanghai` | Часовой пояс контейнера |
| `LANG` | `en_US.UTF-8` | Язык системы, автоматически определяет язык начального интерфейса |
| `ERISPULSE_LANG` | пусто | Принудительный язык начального интерфейса: `zh` / `zh_TW` / `en` / `ja` / `ru` (переопределяет `LANG`) |

</details>

### Магазин приложений 1Panel

Установите ErisPulse через [1Panel](https://1panel.cn) из магазина приложений, см. [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse уже доступен в стороннем магазине приложений 1Panel, можно использовать сторонний репозиторий [okxlin/appstore](https://github.com/okxlin/appstore).

### Установка через pip

```bash
pip install ErisPulse
```

> Также можно использовать сценарий однокнопочной установки, который автоматически определит среду и предложит настройку.

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

**Командный обработчик**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="Отправить приветственное сообщение")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "друг"
    await event.reply(f"Привет, {user_name}!")

@command("ping", help="Проверить, онлайн ли бот")
async def ping_handler(event):
    await event.reply("Pong! Бот работает нормально.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**Описание эффекта**

Отправить `/hello`

Бот отвечает: `Привет, {имя пользователя}!`

---

Отправить `/ping`

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

Более подробная информация см. в:
- [Руководство по быстрому старту](docs/ru/quick-start.md)
- [Введение](docs/ru/getting-started/)

---

## Один и тот же код. Разные платформы.

*Одинаковые обработчики команд. Разные платформы. Без изменения бизнес-логики.*

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

## Цепочка отправки DSL

Одна цепочка вызовов выполняет все логику отправки: @пользователя, ответ, повтор, таймаут, обратный вызов и т.д.:

```python
yunhu = sdk.adapter.get("yunhu")

# Одиночная отправка: @пользователя + ответ + повтор + успешный обратный вызов
await (yunhu.Send.To("group", "123")
       .At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Отправка успешна!"))
       .Text("Привет"))

# Массовая отправка: одна цепочка отправляет несколько сообщений
results = await (yunhu.Send.To("user", "123")
                .Build()
                .Text("Уведомление 1")
                .Image("pic.jpg")
                .Retry(2)
                .send_all())
```

> Поддержка Hook (успешный обратный вызов), Retry (повтор при неудаче), Timeout (отмена по таймауту), OnProgress (мониторинг прогресса), Defer (отложенная отправка), Build (массовое построение) и других методов цепочки, см. [Документацию по SendDSL](docs/ru/developer-guide/adapters/send-dsl.md).

---

## Примеры многошаговых диалогов

ErisPulse содержит мощный движок многошаговых диалогов, легко реализовать сценарии с пошаговым взаимодействием, сбором информации и т.д.:

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Добро пожаловать на регистрацию!")
    
    # Многошаговый сбор информации пользователя, автоматическая валидация
    data = await conv.collect([
        {"key": "name", "prompt": "Введите имя"},
        {"key": "age", "prompt": "Введите возраст",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "Возраст должен быть числом, введите снова"},
    ])
    
    if data and await conv.confirm(f"Подтвердите регистрацию? Имя: {data['name']}, Возраст: {data['age']}"):
        # Использование SendDSL для активной отправки уведомления
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"Регистрация успешна! Добро пожаловать {data['name']}")
        # или await event.reply("Регистрация успешна!")

# Обработка запроса на добавление в друзья
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # Согласие на запрос
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"Запрос на добавление в друзья успешно принят, добро пожаловать {user_name}")
```

<details>
<summary>Подробнее о Conversation API (ветвление / выбор / сохранение)</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # Варианты ответа
    answer = await conv.choose("Кто создатель Python?", [
        "Guido van Rossum",
        "James Gosling", 
        "Dennis Ritchie",
    ])
    
    if answer == 0:
        await conv.say("Правильно!")
    elif answer is None:
        await conv.say("Время вышло, приходите в следующий раз!")
    else:
        await conv.say("Неверно, правильный ответ — Guido van Rossum")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # Ветвление, построение сложных интерактивных сценариев
    @conv.branch("main")
    async def main_menu():
        await conv.say("=== Главное меню ===\n1. Личная информация\n2. Настройки\n3. Выход")
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

См. [Многошаговые диалоги Conversation](docs/ru/advanced/conversation.md)

</details>

---

## Основные модули

ErisPulse предоставляет полный инструментарий для разработки чат-ботов на разных платформах, основные модули выполняют свои функции:

```mermaid
graph TB
    SDK["sdk<br/>Единый вход"]

    SDK --> Event["Event<br/>Система событий"]
    SDK --> AdapterMgr["Adapter<br/>Менеджер адаптеров"]
    SDK --> ModuleMgr["Module<br/>Менеджер модулей"]
    SDK --> Router["Router<br/>HTTP/WS маршрутизация"]
    SDK --> Storage["Storage<br/>SQLite хранилище"]
    SDK --> Config["Config<br/>Менеджер конфигураций"]
    SDK --> Lifecycle["Lifecycle<br/>Жизненный цикл"]
    SDK --> Logger["Logger<br/>Система логирования"]
    SDK --> Client["HttpClient<br/>HTTP клиент"]
```

| Модуль | Описание |
|------|------|
| **Event** | Система событий, предоставляющая пять типов событий: command / message / notice / request / meta, а также многошаговые диалоги Conversation |
| **Adapter** | Менеджер адаптеров, базовый класс BaseAdapter унифицирует преобразование событий и SendDSL отправку, поддержка более 15 платформ: QQ / Telegram / Kook / Yunhu / WeChat Official Account |
| **Module** | Менеджер модулей, базовый класс BaseModule + декларация зависимостей и топологическая сортировка загрузки |
| **SendDSL** | Цепочка отправки, @пользователя, ответ, повтор, таймаут, массовая отправка и другие сложные логики выполняются одной строкой |
| **Router** | Система маршрутизации HTTP/WebSocket (FastAPI + Uvicorn) |
| **Storage** | Хранилище на основе SQLite + универсальный SQL цепочечный запрос |
| **Config** | Менеджер конфигураций в формате TOML |
| **Lifecycle** | События жизненного цикла (core.init / adapter.* / module.*) |
| **Logger** | Модульная система логирования, поддержка под-логгеров |
| **HttpClient** | Единый HTTP/WS клиент (на основе aiohttp), встроенные повторы и исключения ErisPulse |

Более подробная информация о процессе инициализации, событиях жизненного цикла, стратегии загрузки модулей, см. [Обзор архитектуры](docs/ru/architecture.md).

---

## Экосистема

ErisPulse — это не просто фреймворк. Установите и начните работать, не нужно писать с нуля.

<table>
<tr>
<td align="center" width="25%">

**Фреймворк**

Основной исполняемый модуль

Единая модель событий и сообщений

</td>
<td align="center" width="25%">

**Dashboard**

Визуальное управление

Плагины · Логи · Конфигурации

[Онлайн демонстрация →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

Естественный язык → доступный модуль

[Онлайн демонстрация →](https://builder.erisdev.com)

</td>
<td align="center" width="25%">

**Модульный магазин**

Готовые плагины для установки

[Просмотр модулей →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**Адаптеры**

Поддержка более 15 платформ

</td>
<td align="center" width="25%">

**ErisPulse-App**

Официальный клиент для нескольких платформ

Работает на телефоне · Запускается в трее

[Скачать и установить →](https://github.com/ErisPulse/ErisPulse-App/releases)

</td>
<td align="center" width="25%">

**Docker**

Поддержка нескольких архитектур

`erispulse/erispulse`

</td>
<td align="center" width="25%">

**Документация и CLI**

[erisdev.com](https://www.erisdev.com)

`epsdk` инструмент для создания проектов

</td>
</tr>
</table>

---

## Поддерживаемые платформы

Мы приветствуем вклад в развитие адаптеров! Не знаете с чего начать? Посмотрите [руководство по вкладу](docs/ru/contributing/README.md).

| Адаптер | Описание |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Платформа мгновенных сообщений Kook (开黑啦) |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Децентрализированный протокол общения Matrix |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | Общий протокол роботов OneBot v11 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | Стандартный протокол OneBot v12 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | Платформа официальных роботов QQ |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Веб-дебаг, без подключения к реальной платформе |
| <img src=".github/assets/adapter_logo/terminal.svg" height="20" alt="Terminal" /> [Terminal](https://github.com/ErisPulse/ErisPulse-TerminalAdapter) | Терминал как чат, нулевая конфигурация для разработки и отладки |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Глобальная платформа мгновенных сообщений |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Адаптер для отправки и получения по протоколу электронной почты |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Корпоративная платформа мгновенных сообщений (подключение роботов) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Адаптер подключения по пользовательскому протоколу Yunhu |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Глобальная платформа коммуникации, поддержка серверов, каналов, личных сообщений |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | Общий адаптер HTTP-моста, подключение к любой системе |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [WeChat Official Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Платформа официальных аккаунтов WeChat |

Смотрите подробное описание [адаптеров](docs/ru/platform-guide/README.md)

---

## Сообщество

Общайтесь с нами:

- Telegram: <https://t.me/ErisPulse>
- QQ группа: <https://qm.qq.com/q/TOwnCmypcy>
- Yunhu группа: <https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

---

### Руководство по вкладу

Здоровье проекта ErisPulse зависит от вашей помощи! Мы приветствуем вклад любого вида:

1. **Сообщение об ошибке** — отправьте отчёт об ошибке в [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Запрос функции** — предложите новую идею через [обсуждения сообщества](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Вклад в код** — перед отправкой PR ознакомьтесь с [стилем кода](docs/ru/styleguide/) и [руководством по вкладу](CONTRIBUTING.md)
4. **Улучшение документации** — помогите улучшить документацию и примеры кода

**Первый вклад?** Начните здесь 👉 [Первый вклад на практике](docs/ru/contributing/first-contribution.md)

[Присоединиться к обсуждению сообщества](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Благодарности

<img src=".github/assets/thanks.png" width="200" alt="Спасибо" />

Некоторый код проекта основан на [sdkFrame](https://github.com/runoneall/sdkFrame).

Стандартизированный слой основных адаптеров вдохновлен и опирается на [спецификацию OneBot12](https://12.onebot.dev/).

Особая благодарность экосистеме и сообществу Yunhu.

Ранние исследования и развитие ErisPulse обязаны поддержке сообщества разработчиков Yunhu, многие идеи, адаптеры и практические навыки родились здесь.

Также благодарим всех, кто внес вклад в ErisPulse, OneBot-экосистему и открытые проекты.

</div>