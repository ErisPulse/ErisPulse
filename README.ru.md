<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Русский**

# ErisPulse

**Пишите код один раз — развертывайте на QQ / Telegram / Kook / Yunhu / WeChat Official Account / OneBot12 / ... и множестве других платформ.**

Событийно-ориентированный модульный асинхронный фреймворк для ботов на основе стандартного интерфейса OneBot12. Бизнес-код пишется один раз, а адаптеры берут на себя скрытие различий между платформами; система плагинов, горячая перезагрузка и полный набор инструментов разработчика доступны «из коробки».

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://github.com/botuniverse/onebot-11"><img src="https://img.shields.io/badge/OneBot-11-black?style=for-the-badge" alt="OneBot 11"></a>
  <a href="https://12.onebot.dev/"><img src="https://img.shields.io/badge/OneBot-12-black?style=for-the-badge" alt="OneBot 12"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Downloads"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/stargazers"><img src="https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=yellow" alt="Stars"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge" alt="Ruff"></a>
  <a href="https://socket.dev/pypi/package/erispulse"><img src="https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white" alt="Socket"></a>
  <a href="https://www.erisdev.com"><img src="https://img.shields.io/badge/Документация-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="Документация"></a>
  <a href="https://deepwiki.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/DeepWiki-ErisPulse-8A2BE2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="DeepWiki"></a>
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/Маркет-модулей-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="Маркет модулей"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="Обсуждения"></a>
</p>

<br clear="both">

---

<div align="center">

### Ключевые возможности

</div>

<table>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="Событийно-ориентированная архитектура" />

### Событийно-ориентированная архитектура

Единая событийная модель на основе OneBot12: один обработчик работает со всеми адаптерами

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="Кроссплатформенность" />

### Кроссплатформенность

Более 15 платформ: QQ / Telegram / Kook / Yunhu и другие — без единого изменения в бизнес-коде

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="Модульная архитектура" />

### Модульная архитектура

Подключение и отключение плагинов «на лету» без перезапуска; области действия (scope) управляются по платформе / боту / сессии

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="Горячая перезагрузка" />

### Горячая перезагрузка

Изменения применяются сразу после сохранения — быстро и незаметно

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="AI-ассистент" />

### AI-ассистент

Опишите требования на естественном языке и сразу получите готовый модуль

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="Простота и элегантность" />

### Простота и элегантность

Цепочечный API: упоминание пользователя, ответ, повтор, массовая отправка — всё в одной строке

</td>
</tr>
</table>

---

## Как это работает

ErisPulse скрывает различия платформ на уровне адаптеров, позволяя бизнес-коду работать только с событиями:

```mermaid
graph LR
    P["15+ платформ<br/>QQ · Telegram · Kook · Yunhu · WeChat Official Account · Почта · Webhook ..."]
    A["Слой адаптеров<br/>нативные протоколы → стандартные события OneBot12"]
    Event["Шина событий Event<br/>middleware → распределение command/message/notice/request/meta"]
    M["Бизнес-модули<br/>обработчики @command / @message · ваши модули"]
    P --> A --> Event --> M
    M -.->|"event.reply() / SendDSL"| Event
```

- **Слой адаптеров** преобразует нативные протоколы платформ в стандартные события OneBot12, так что бизнес-модули не замечают различий между платформами
- **Шина Event** сначала выполняет цепочку middleware, а затем распределяет события по типам между пятью категориями обработчиков
- **Ваш код** подписывается на события через декораторы и отвечает с помощью `event.reply()` или SendDSL — ответное сообщение проходит тот же путь в обратном направлении к платформе

Полные сведения о дизайне — составе модулей, процессе инициализации, событиях жизненного цикла и т. д. — см. в [обзоре архитектуры](docs/ru/architecture.md).

---

## Быстрый старт

### Скрипт установки в один клик (рекомендуется)

Скрипт установки автоматически определит вашу среду (Docker, Python, uv), поможет выбрать наиболее подходящий способ установки и поддерживает несколько языков (中文/English/日本語/Русский/繁體中文).

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

### Установка через Docker (рекомендуется)

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

После запуска откройте `http://<host>:8000/Dashboard` и войдите в панель управления Dashboard с помощью заданного токена.

> В образ входят фреймворк ErisPulse и панель управления Dashboard; поддерживаются архитектуры `linux/amd64` и `linux/arm64`.
>
> **Персистентность**: файлы конфигурации и установленные модули/адаптеры сохраняются на хост-машине через подключённые тома и не теряются при перезапуске контейнера. Обновление самого фреймворка выполняется через горячее обновление в Dashboard.

</details>

<details>
<summary>Переменные окружения Docker</summary>

| Переменная | По умолчанию | Описание |
|------|--------|------|
| `ERISPULSE_DASHBOARD_TOKEN` | пусто | Токен входа в Dashboard (после установки автоматически записывается в конфигурацию) |
| `ERISPULSE_PORT` | `8000` | Проброс порта Dashboard |
| `ERISPULSE_TAG` | `latest` | Тег образа; можно установить `dev` для использования пре-релизного образа |
| `CONTAINER_NAME` | `erispulse` | Имя контейнера |
| `TZ` | `Asia/Shanghai` | Часовой пояс контейнера |
| `LANG` | `en_US.UTF-8` | Язык системы; язык интерфейса запуска определяется автоматически |
| `ERISPULSE_LANG` | пусто | Принудительно задать язык интерфейса запуска: `zh` / `zh_TW` / `en` / `ja` / `ru` (переопределяет `LANG`) |

</details>

### Магазин приложений 1Panel

Установите ErisPulse в один клик через магазин приложений [1Panel](https://1panel.cn), подробнее см. [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse также доступен в стороннем магазине приложений 1Panel; установить можно из стороннего репозитория [okxlin/appstore](https://github.com/okxlin/appstore).

### Установка через pip

```bash
pip install ErisPulse
```

Если вы хотите использовать `epsdk` как глобальный инструмент командной строки, не создавая виртуальное окружение, рекомендуется `uv tool install`:

```bash
uv tool install ErisPulse
```

> Также можно воспользоваться приведённым выше скриптом установки в один клик — он автоматически определит окружение и проведёт вас по настройке (в меню скрипта также доступен вариант «Глобальная установка CLI (uv tool)»).

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

@command("hello", help="Отправить приветственное сообщение")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "друг"
    await event.reply(f"Привет, {user_name}!")

@command("ping", help="Проверить, на связи ли бот")
async def ping_handler(event):
    await event.reply("Pong! Бот работает исправно.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**Ожидаемый результат**

Отправьте `/hello`

Бот отвечает: `Привет, {имя_пользователя}!`

---

Отправьте `/ping`

Бот отвечает: `Pong! Бот работает исправно.`

---

**Способ запуска**

```bash
epsdk run main.py
# или в режиме разработки
epsdk run main.py --reload
```

</td>
</tr>
</table>

Подробнее смотрите:
- [Руководство по быстрому старту](docs/ru/quick-start.md)
- [Руководство для начинающих](docs/ru/getting-started/)

---

## Один и тот же код. Множество платформ.

*Абсолютно одинаковые обработчики команд. Разные платформы. Без изменения бизнес-логики.*

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

## Цепочечная отправка DSL

Упоминания, ответы, повторы, таймауты, колбэки успеха — вся сложная логика отправки умещается в одну цепочку:

```python
yunhu = sdk.adapter.get("yunhu")

# Одиночная отправка: упоминание + ответ + повтор + колбэк успеха
await (yunhu.Send.To("group", "123").At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Отправка выполнена!")).Text("Привет"))

# Массовая отправка: несколько сообщений одной цепочкой
results = await (yunhu.Send.To("user", "123").Build()
                 .Text("Уведомление 1").Image("pic.jpg").Retry(2).send_all())
```

> Все цепочечные методы — Hook / Retry / Timeout / OnProgress / Defer / Build и др. — описаны в [документации SendDSL](docs/ru/developer-guide/adapters/send-dsl.md).

---

## Пример многошагового диалога

Сбор информации, проверка ввода, подтверждение отправки — без ручного управления состоянием диалога:

```python
from ErisPulse.Core.Event import command

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    await conv.say("Добро пожаловать! Начнём регистрацию.")
    data = await conv.collect([
        {"key": "name", "prompt": "Введите ваше имя"},
        {"key": "age", "prompt": "Введите ваш возраст",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "Возраст должен быть числом, введите снова"},
    ])
    if data and await conv.confirm(f"Подтвердить регистрацию? Имя: {data['name']}, возраст: {data['age']}"):
        await event.reply(f"Регистрация прошла успешно! Добро пожаловать, {data['name']}")
```

> Полные возможности — вопросы с вариантами (choose), ветвление и переходы (branch / goto), персистентность и др. — описаны в разделе [Conversation: многошаговый диалог](docs/ru/advanced/conversation.md).

---

## Основные модули

Единая точка входа `sdk` объединяет все ключевые возможности:

```mermaid
graph LR
    SDK["Единая точка входа sdk"] --> Event & Adapter & Module & Router & Storage
    SDK --> Config & Lifecycle & Logger & HttpClient
```

| Модуль | Описание |
|------|------|
| **Event** | Система событий: пять типов событий command / message / notice / request / meta + многошаговый диалог Conversation |
| **Adapter** | Управление адаптерами: базовый класс BaseAdapter унифицирует преобразование событий и отправку через SendDSL, поддерживает 15+ платформ — QQ / Telegram / Kook / Yunhu / WeChat Official Account и др. |
| **Module** | Управление модулями: базовый класс BaseModule + объявление зависимостей и загрузка в топологическом порядке |
| **SendDSL** | Цепочечная отправка: упоминание / ответ / повтор / таймаут / массовая отправка — сложная логика в одной строке |
| **Router** | Система маршрутизации HTTP/WebSocket (FastAPI + Uvicorn) |
| **Storage** | Хранилище «ключ-значение» на основе SQLite + универсальные цепочечные SQL-запросы |
| **Config** | Управление конфигурацией TOML |
| **Lifecycle** | Хуки событий жизненного цикла (core.init / adapter.* / module.*) |
| **Logger** | Модульная система логирования с поддержкой дочерних логгеров |
| **HttpClient** | Унифицированный HTTP/WS-клиент (на основе aiohttp) со встроенными повторами и системой исключений ErisPulse |

Подробнее о дизайне (процесс инициализации, события жизненного цикла, стратегия загрузки модулей) — см. [обзор архитектуры](docs/ru/architecture.md).

---

## Области действия (Scope) — трёхмерное управление правами

Не меняя ни строчки кода модулей, единообразно объявляйте в конфигурации, «в каком объёме что действует»:

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]           # ① Измерение модулей: на этой платформе открыты только эти модули (glob / регулярные выражения)

[ErisPulse.scope.identity.users.onebot11]
deny = ["u_bad", "spam_*"]            # ② Измерение идентичности: события пользователей из чёрного списка отбрасываются сразу

[ErisPulse.scope.actions.MyModule]
send = { allow = ["Text"] }           # ③ Измерение исходящих действий: этот модуль может отправлять только текст
api = { deny = ["set_*", "leave_*"] } #    и административные API ему запрещены
```

```python
# Можно изменять и во время выполнения — вступает в силу сразу (словарный доступ с точечной нотацией)
sdk.scope.set_action("MyModule", "api", deny=["set_*"])
```

> Подробнее: [Область действия (scope)](docs/ru/advanced/scope.md)

---

## Переопределение событий — меняйте поведение событий любого типа, не трогая код модулей

Смените триггерное слово или добавьте команде ограничение «только для администраторов» — без правки исходников модуля, всё решается конфигурацией:

```toml
# Переопределение условий срабатывания обработчиков сообщений (логическое AND с условиями в коде; поддерживаются все типы meta/message/notice/request/command)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "болталка*"

# Переопределение параметров команды (master / hidden / aliases / prefix и др.; конфигурация имеет приоритет)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
```

> Подробнее: [Переопределение событий](docs/ru/getting-started/event-handling.md)

---

## Экосистема

ErisPulse — это больше, чем фреймворк. Установили — и сразу начали: ничего не нужно изобретать с нуля.

<table>
<tr>
<td align="center" width="25%">

**Фреймворк**

Основная среда выполнения

Единые модели событий и сообщений

</td>
<td align="center" width="25%">

**Dashboard**

Визуальное управление

Плагины · логи · конфигурация

[Онлайн-демо →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

Естественный язык → готовый модуль

[Попробовать сейчас →](https://builder.erisdev.com)

</td>
<td align="center" width="25%">

**Маркет модулей**

Плагины, работающие сразу после установки

[Просмотреть модули →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**Адаптеры**

Подключение 15+ платформ

</td>
<td align="center" width="25%">

**ErisPulse-App**

Официальный мультиплатформенный клиент

Работает прямо на телефоне · живёт в трее на ПК

[Скачать и установить →](https://github.com/ErisPulse/ErisPulse-App/releases)

</td>
<td align="center" width="25%">

**Docker**

Поддержка нескольких архитектур

`erispulse/erispulse`

</td>
<td align="center" width="25%">

**Документация & CLI**

[erisdev.com](https://www.erisdev.com)

Инструмент скаффолдинга `epsdk`

</td>
</tr>
</table>

---

## Поддерживаемые платформы

Будем рады вашему вкладу в адаптеры! Не знаете, с чего начать? Взгляните на [руководство по внесению вклада](docs/ru/contributing/README.md).

| Адаптер | Описание |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Платформа мгновенного обмена сообщениями Kook (KaiHeiLa) |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Децентрализованный коммуникационный протокол Matrix |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | Универсальный протокол ботов OneBot v11 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | Стандартный протокол OneBot v12 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | Официальная бот-платформа QQ |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Песочница" /> [Песочница](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Отладка в веб-интерфейсе без подключения к реальной платформе |
| <img src=".github/assets/adapter_logo/terminal.svg" height="20" alt="Терминал" /> [Терминал](https://github.com/ErisPulse/ErisPulse-TerminalAdapter) | Чат прямо в командной строке — разработка и отладка с нулевой настройкой |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Глобальная платформа мгновенного обмена сообщениями |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Почта" /> [Почта](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Адаптер приёма и отправки электронной почты |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Корпоративная платформа мгновенного обмена сообщениями (подключение ботов) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Пользователь Yunhu](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Адаптер подключения на основе пользовательского протокола Yunhu |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Глобальная платформа для сообществ: серверы, каналы, личные сообщения |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | Универсальный HTTP-мост для интеграции с любыми системами |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [WeChat Official Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Официальная платформа публичных аккаунтов WeChat |

Подробное описание адаптеров: [см. здесь](docs/ru/platform-guide/README.md)

---

## Сообщество

Наши каналы общения:

- Telegram: <https://t.me/ErisPulse>
- QQ-группа: <https://qm.qq.com/q/TOwnCmypcy>
- Группа Yunhu: <https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

Считаете проект полезным? Поддержите нашу дальнейшую разработку через [Afdian](https://ifdian.net/a/YingXinche)!

---

## Star History

Если ErisPulse оказался вам полезен, поставьте Star ⭐ — это самый прямой способ помочь большему числу разработчиков узнать о проекте.

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

### Руководство по внесению вклада

Проекту ErisPulse нужен и ваш вклад! Мы приветствуем любые формы участия:

1. **Сообщения об ошибках** — отправляйте отчёты об ошибках в [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Запросы функций** — предлагайте новые идеи в [обсуждениях сообщества](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Вклад в код** — перед отправкой PR прочитайте [руководство по стилю кода](docs/ru/styleguide/) и [руководство по внесению вклада](CONTRIBUTING.md)
4. **Улучшение документации** — помогайте улучшать документацию и примеры кода

**Первый вклад?** Начните здесь 👉 [Ваш первый вклад на практике](docs/ru/contributing/first-contribution.md)

[Присоединяйтесь к обсуждениям сообщества](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Благодарности

<img src=".github/assets/thanks.png" width="200" alt="Благодарность" />

Часть кода этого проекта основана на [sdkFrame](https://github.com/runoneall/sdkFrame), а слой стандартизации ключевых адаптеров создавался с опорой на [спецификацию OneBot12](https://12.onebot.dev/) и выиграл от неё.

Ранние исследования и рост ErisPulse были бы невозможны без поддержки сообщества разработчиков Yunhu — многие идеи, адаптеры и практический наработки родились именно там.

Также благодарим всех разработчиков и авторов проектов, которые внесли вклад в ErisPulse, экосистему OneBot и open source-сообщество.

</div>