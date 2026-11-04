<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

> ✦ **Всем привет, я маленькая eris!** Талисман ErisPulse и ваш проводник по документации. Если в демоверсиях всплывают ошибки — не пугайтесь: скорее всего, это я пробую всё за вас~

# ErisPulse

**Пишите код один раз — разворачивайте на множестве платформ: QQ / Telegram / Kook / Yunhu / WeChat Official Account / OneBot12 / ...**

Событийно-ориентированный модульный асинхронный фреймворк для ботов на основе стандартного интерфейса OneBot12. Бизнес-код пишется лишь один раз, а адаптеры берут на себя различия между платформами; система плагинов, горячая перезагрузка и полный набор инструментов разработчика доступны из коробки.

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://github.com/botuniverse/onebot-11"><img src="https://img.shields.io/badge/OneBot-11-black?style=for-the-badge" alt="OneBot 11"></a>
  <a href="https://12.onebot.dev/"><img src="https://img.shields.io/badge/OneBot-12-black?style=for-the-badge" alt="OneBot 12"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/Лицензия-MIT-blue?style=for-the-badge" alt="Лицензия"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Загрузки"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/stargazers"><img src="https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=yellow" alt="Звёзды"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge" alt="Ruff"></a>
  <a href="https://socket.dev/pypi/package/erispulse"><img src="https://img.shields.io/badge/Socket-Безопасно-2ea043?style=for-the-badge&logo=socket&logoColor=white" alt="Socket"></a>
  <a href="https://www.erisdev.com"><img src="https://img.shields.io/badge/Документация-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="Документация"></a>
  <a href="https://deepwiki.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/DeepWiki-ErisPulse-8A2BE2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="DeepWiki"></a>
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/Маркет_модулей-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="Маркет модулей"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="Обсуждения"></a>
</p>

<br clear="both">

---

<div align="center">

### Ключевые особенности

</div>

<table>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="Событийно-ориентированная архитектура" />

### Событийно-ориентированная архитектура

Единая событийная модель на базе OneBot12: один обработчик (handler) подходит ко всем адаптерам

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="Кроссплатформенность" />

### Кроссплатформенность

15+ платформ, таких как QQ / Telegram / Kook / Yunhu, — без единого изменения в бизнес-коде

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="Модульная архитектура" />

### Модульная архитектура

Плагины подключаются «на горячую» без перезапуска; области действия (scope) управляются по платформе / боту / диалогу

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="Горячая перезагрузка" />

### Горячая перезагрузка

Сохранили — и сразу работает: горячая перезагрузка быстрая и незаметная

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="Помощь AI" />

### Помощь AI

Опишите требования на естественном языке — и получите готовый рабочий модуль

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="Простота и элегантность" />

### Простота и элегантность

Цепочечный API: упомянуть пользователя, ответить, повторить, разослать массово — всё одной строкой

</td>
</tr>
</table>

---

## Как это работает

ErisPulse скрывает различия платформ на уровне адаптеров, позволяя бизнес-коду заботиться только о самих событиях:

```mermaid
graph LR
    P["15+ платформ<br/>QQ · Telegram · Kook · Yunhu · WeChat Official Account · Email · Webhook ..."]
    A["Слой адаптеров<br/>нативные протоколы → стандартные события OneBot12"]
    Event["Шина событий Event<br/>middleware → распределение command/message/notice/request/meta"]
    M["Бизнес-модули<br/>обработчики @command / @message · ваши модули"]
    P --> A --> Event --> M
    M -.->|"event.reply() / SendDSL"| Event
```

- **Слой адаптеров** преобразует нативные протоколы платформ в стандартные события OneBot12, поэтому бизнес-модули не видят различий между платформами
- **Шина Event** сначала выполняет цепочку middleware, а затем распределяет события по пяти типам обработчиков
- **Ваш код** подписывается на события декораторами и отвечает через `event.reply()` или SendDSL — ответное сообщение возвращается платформе тем же путём в обратном направлении

Подробности дизайна — состав модулей, процесс инициализации, события жизненного цикла и т. д. — см. в [обзоре архитектуры](docs/ru/architecture.md).

---

## Быстрый старт

### Скрипт установки в один клик (рекомендуется)

Скрипт установки автоматически определит ваше окружение (Docker, Python, uv), поможет выбрать наиболее подходящий способ установки и поддерживает несколько языков (中文/English/日本語/Русский/繁體中文).

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
<summary>Docker Hub недоступен?</summary>

Если Docker Hub недоступен, можно использовать GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

При использовании образа из ghcr.io нужно изменить поле image в `docker-compose.yml`:
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>Быстрый запуск</summary>

```bash
# Скачать docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Задать токен входа в Dashboard и запустить
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

После запуска перейдите на `http://<host>:8000/Dashboard` и войдите в панель управления Dashboard с помощью заданного токена.

> В образ встроены фреймворк ErisPulse и панель управления Dashboard; поддерживаются архитектуры `linux/amd64` и `linux/arm64`.
>
> **Персистентность**: конфигурационные файлы и установленные модули/адаптеры сохраняются на хост-машине через монтирование томов и не теряются при перезапуске контейнера. Обновление самого фреймворка выполняется средствами горячего обновления в Dashboard.

</details>

<details>
<summary>Переменные окружения Docker</summary>

| Переменная | Значение по умолчанию | Описание |
|------|--------|------|
| `ERISPULSE_DASHBOARD_TOKEN` | пусто | Токен входа в Dashboard (после установки автоматически записывается в конфигурацию) |
| `ERISPULSE_PORT` | `8000` | Проброс порта Dashboard |
| `ERISPULSE_TAG` | `latest` | Тег образа; можно задать `dev` для пре-релизного образа |
| `CONTAINER_NAME` | `erispulse` | Имя контейнера |
| `TZ` | `Asia/Shanghai` | Часовой пояс контейнера |
| `LANG` | `en_US.UTF-8` | Язык системы; язык стартового интерфейса определяется автоматически |
| `ERISPULSE_LANG` | пусто | Принудительно задать язык стартового интерфейса: `zh` / `zh_TW` / `en` / `ja` / `ru` (переопределяет `LANG`) |

</details>

### Магазин приложений 1Panel

Установите ErisPulse в один клик через магазин приложений [1Panel](https://1panel.cn); подробности см. в [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse доступен в стороннем магазине приложений 1Panel; установить его можно из стороннего репозитория [okxlin/appstore](https://github.com/okxlin/appstore).

### Установка через pip

```bash
pip install ErisPulse
```

Если хотите использовать `epsdk` как глобальную утилиту командной строки, без виртуального окружения, рекомендуем `uv tool install`:

```bash
uv tool install ErisPulse
```

> Можно также воспользоваться скриптом установки в один клик выше: он автоматически определит окружение и проведёт через настройку (в меню скрипта также есть вариант «Глобальная установка CLI (uv tool)»).

### Инициализация проекта

```bash
# Интерактивная инициализация
epsdk init

# Быстрая инициализация (с указанием имени проекта)
epsdk init -q -n my_bot
```

### Создание первого бота

Создайте файл `main.py`:

<table>
<tr>
<td width="50%" valign="top">

**Обработчики команд**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="Отправляет приветственное сообщение")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "друг"
    await event.reply(f"Привет, {user_name}!")

@command("ping", help="Проверяет, на связи ли бот")
async def ping_handler(event):
    await event.reply("Pong! Бот работает штатно.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**Ожидаемый результат**

Отправьте `/hello`

Бот отвечает: `Привет, {имя пользователя}!`

---

Отправьте `/ping`

Бот отвечает: `Pong! Бот работает штатно.`

---

**Как запустить**

```bash
epsdk run main.py
# или режим разработки
epsdk run main.py --reload
```

</td>
</tr>
</table>

Более подробные инструкции:
- [Руководство по быстрому старту](docs/ru/quick-start.md)
- [Руководство для начинающих](docs/ru/getting-started/)

---

## Один и тот же код. Несколько платформ.

*Те же самые обработчики команд. Другие платформы. Без единого изменения бизнес-логики.*

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

## Цепочечный DSL отправки

Упоминание пользователя, ответ, повторы, таймауты, колбэк при успехе — сложная логика отправки в одной цепочке:

```python
yunhu = sdk.adapter.get("yunhu")

# Одиночная отправка: упоминание пользователя + ответ + повторы + колбэк успеха
await (yunhu.Send.To("group", "123").At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Успешно отправлено!")).Text("Привет"))

# Массовая отправка: несколько сообщений одной цепочкой
results = await (yunhu.Send.To("user", "123").Build()
                 .Text("Уведомление 1").Image("pic.jpg").Retry(2).send_all())
```

> Все цепочечные методы — Hook / Retry / Timeout / OnProgress / Defer / Build и другие — описаны в [документации SendDSL](docs/ru/developer-guide/adapters/send-dsl.md).

---

## Пример многошагового диалога

Сбор информации, проверка ввода, подтверждение отправки — без ручного управления состоянием диалога:

```python
from ErisPulse.Core.Event import command

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    await conv.say("Добро пожаловать в регистрацию!")
    data = await conv.collect([
        {"key": "name", "prompt": "Введите имя"},
        {"key": "age", "prompt": "Введите возраст",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "Возраст должен быть числом, введите ещё раз"},
    ])
    if data and await conv.confirm(f"Подтвердить регистрацию? Имя: {data['name']}, возраст: {data['age']}"):
        await event.reply(f"Регистрация успешна! Добро пожаловать, {data['name']}")
```

> Полные возможности — вопросы с вариантами (choose), переходы по веткам (branch / goto), персистентность и другие — в [документации Conversation (многошаговые диалоги)](docs/ru/advanced/conversation.md).

---

## Ключевые модули

Один вход `sdk` объединяет все ключевые возможности:

```mermaid
graph LR
    SDK["Единая точка входа sdk"] --> Event & Adapter & Module & Router & Storage
    SDK --> Config & Lifecycle & Logger & HttpClient
```

| Модуль | Описание |
|------|------|
| **Event** | Система событий: пять типов событий command / message / notice / request / meta + многошаговые диалоги Conversation |
| **Adapter** | Управление адаптерами: базовый класс BaseAdapter унифицирует преобразование событий и отправку через SendDSL; поддержка 15+ платформ, включая QQ / Telegram / Kook / Yunhu / WeChat Official Account |
| **Module** | Управление модулями: базовый класс BaseModule + объявление зависимостей и загрузка в топологическом порядке |
| **SendDSL** | Цепочечная отправка: упоминания / ответы / повторы / таймауты / массовые рассылки и другая сложная логика — одной строкой |
| **Router** | Система HTTP/WebSocket-маршрутизации (FastAPI + Uvicorn) |
| **Storage** | Key-value хранилище на базе SQLite + универсальные цепочечные SQL-запросы |
| **Config** | Управление конфигурацией TOML |
| **Lifecycle** | Хуки событий жизненного цикла (core.init / adapter.* / module.*) |
| **Logger** | Модульная система логирования с поддержкой дочерних логгеров |
| **HttpClient** | Единый HTTP/WS-клиент (на базе aiohttp) со встроенными повторами и системой исключений ErisPulse |

Подробности дизайна (процесс инициализации, события жизненного цикла, стратегии загрузки модулей) — в [обзоре архитектуры](docs/ru/architecture.md).

---

## Области действия (Scope) — трёхмерное пространство контроля прав

Не меняя ни строчки кода модулей, декларативно укажите в конфигурации, «на что распространяется действие»:

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]           # ① Измерение модулей: на этой платформе открыты только эти модули (glob / regex)

[ErisPulse.scope.identity.users.onebot11]
deny = ["u_bad", "spam_*"]            # ② Измерение идентичности: события пользователей из чёрного списка отбрасываются сразу

[ErisPulse.scope.actions.MyModule]
send = { allow = ["Text"] }           # ③ Измерение исходящих действий: этому модулю разрешена отправка только текста
api = { deny = ["set_*", "leave_*"] } #    и запрещены административные API
```

```python
# Можно менять и во время выполнения — применяется сразу (доступ как к словарю, с путями через точку)
sdk.scope.set_action("MyModule", "api", deny=["set_*"])
```

> Подробнее: [Области действия (scope)](docs/ru/advanced/scope.md)

---

## Переопределение событий — меняйте поведение любых типов событий, не трогая код модулей

Сменить триггерное слово или добавить команде ограничение «только для админов» — конфигурация вступает в силу без правки исходников модуля:

```toml
# Переопределение условий срабатывания обработчиков сообщений (объединяется по AND с условиями в коде; поддерживаются все типы: meta/message/notice/request/command)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "болтовня*"

# Переопределение параметров реализации команд (master / hidden / aliases / prefix и др.; приоритет у пользовательских значений)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
```

> Подробнее: [Переопределение событий](docs/ru/getting-started/event-handling.md)

---

## Экосистема

ErisPulse — это больше, чем фреймворк. Установили — и можно начинать, изобретать велосипеды с нуля не нужно.

<table>
<tr>
<td align="center" width="25%">

**Фреймворк**

Основной рантайм

Единые модели событий и сообщений

</td>
<td align="center" width="25%">

**Dashboard**

Визуальное управление

Плагины · Логи · Конфигурация

[Онлайн-демо →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

Естественный язык → готовый модуль

[Попробовать сейчас →](https://builder.erisdev.com)

</td>
<td align="center" width="25%">

**Маркет модулей**

Плагины, готовые к работе сразу после установки

[Смотреть модули →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**Адаптеры**

Интеграция с 15+ платформами

</td>
<td align="center" width="25%">

**ErisPulse-App**

Официальный клиент для нескольких платформ

Работа прямо на телефоне · постоянный значок в трее на десктопе

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

Инструмент скаффолдинга `epsdk`

</td>
</tr>
</table>

---

## Поддерживаемые платформы

Будем рады вашим адаптерам! Не знаете, с чего начать? Взгляните на [руководство по внесению вклада](docs/ru/contributing/README.md).

| Адаптер | Описание |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Платформа мгновенных сообщений Kook (KaiHeiLa) |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Децентрализованный протокол связи Matrix |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | Универсальный бот-протокол OneBot v11 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | Стандартный протокол OneBot v12 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | Официальная бот-платформа QQ |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Песочница](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Отладка в браузере, без подключения к реальной платформе |
| <img src=".github/assets/adapter_logo/terminal.svg" height="20" alt="Terminal" /> [Терминал](https://github.com/ErisPulse/ErisPulse-TerminalAdapter) | Командная строка как чат: разработка и отладка без настройки |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Глобальная платформа мгновенных сообщений |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Почта](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Адаптер отправки и получения почты |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Корпоративная платформа мгновенных сообщений (подключение ботов) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu (пользователь)](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Адаптер подключения на основе пользовательского протокола Yunhu |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Глобальная платформа сообществ: серверы, каналы, личные сообщения |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | Универсальный HTTP-мост для подключения любых систем |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [Официальный аккаунт WeChat](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Официальная платформа аккаунтов WeChat |

Подробнее: [подробный обзор адаптеров](docs/ru/platform-guide/README.md)

---

## Сообщество

Свяжитесь с нами:

- Telegram: <https://t.me/ErisPulse>
- Группа QQ: <https://qm.qq.com/q/TOwnCmypcy>
- Группа Yunhu: <https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

Нашли проект полезным? Поддержите нашу дальнейшую разработку на [Afdian](https://ifdian.net/a/YingXinche)!

---

## Star History

Если ErisPulse вам помог, поставьте Star ⭐ — это самый прямой способ дать проекту заметность среди большего числа разработчиков.

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

### Руководство по внесению вклада

Проекту ErisPulse нужна и ваша помощь! Мы приветствуем вклад в любой форме:

1. **Сообщения об ошибках** — заводите баг-репорты в [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Запросы новых функций** — делитесь идеями в [обсуждениях сообщества](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Вклад в код** — перед отправкой PR прочитайте [стиль кода](docs/ru/styleguide/) и [руководство по внесению вклада](CONTRIBUTING.md)
4. **Улучшение документации** — помогайте дорабатывать документацию и примеры кода

**Первый вклад?** Начните отсюда 👉 [Первый вклад на практике](docs/ru/contributing/first-contribution.md)

[Присоединяйтесь к обсуждениям сообщества](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Благодарности

<img src=".github/assets/thanks.png" width="200" alt="Благодарность" />

Часть кода этого проекта основана на [sdkFrame](https://github.com/runoneall/sdkFrame); уровень стандартизации ключевых адаптеров создавался с опорой на [спецификацию OneBot12](https://12.onebot.dev/) и благодаря ей.

Ранние этапы становления ErisPulse были бы невозможны без поддержки сообщества разработчиков Yunhu — именно там родились многие идеи, адаптеры и практический опыт.

Также благодарим всех разработчиков и авторов проектов, вносящих вклад в ErisPulse, экосистему OneBot и open source.

</div>