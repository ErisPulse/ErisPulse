<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Русский**

# ErisPulse

**Написано один раз, развернуто на нескольких платформах.**

Фреймворк для разработки событийно-ориентированных мультиплатформенных чат-ботов.

Основан на стандартном интерфейсе OneBot12, что позволяет один раз написать код и развернуть на нескольких платформах. Гибкая система плагинов, поддержка горячей перезагрузки и полный набор инструментов для разработчиков, подходящий для различных сценариев, от простых чат-ботов до сложных автоматизированных систем.

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen" alt="Stars"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Downloads"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge" alt="Ruff"></a>
  <a href="https://socket.dev/pypi/package/erispulse"><img src="https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white" alt="Socket"></a>
  <a href="https://www.erisdev.com"><img src="https://img.shields.io/badge/文档-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="Documentation"></a>
  <a href="https://deepwiki.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/DeepWiki-ErisPulse-8A2BE2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="DeepWiki"></a>
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="Module Market"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="Discussions"></a>
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

Четкая модель событий на основе стандарта OneBot12, что делает логику обработки сообщений более интуитивной и эффективной

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="Кроссплатформенная совместимость" />

### Кроссплатформенная совместимость

Модули плагинов пишутся один раз и могут использоваться на всех платформах, без необходимости повторного разработки для разных платформ

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="Модульная архитектура" />

### Модульная архитектура

Гибкая система плагинов, легко расширяемая и интегрируемая, поддерживает управление модулями с возможностью горячей замены

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="Горячая перезагрузка" />

### Горячая перезагрузка

Во время разработки код можно перезагружать без перезапуска

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="Помощь ИИ" />

### Помощь ИИ

Разработка с помощью ИИ позволяет быстро находить готовые модули для нужных задач

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="Легкость и элегантность" />

### Легкость и элегантность

Интуитивно понятный API, делает код легким и читаемым, как перышко

</td>
</tr>
</table>

### DSL для цепочечной отправки

Одна цепочка вызовов завершает все логику отправки: упоминание, ответ, повтор, таймаут, обратный вызов:

```python
yunhu = sdk.adapter.get("yunhu")

# Одиночная отправка: упоминание пользователя + ответ + повтор + успешный обратный вызов
await (yunhu.Send.To("group", "123")
       .At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("Отправка успешна!"))
       .Text("Привет"))

# Массовая отправка: отправка нескольких сообщений одной цепочкой
results = await (yunhu.Send.To("user", "123")
                .Build()
                .Text("Уведомление 1")
                .Image("pic.jpg")
                .Retry(2)
                .send_all())
```

> Поддержка Hook (обратный вызов при успехе), Retry (повтор при ошибке), Timeout (отмена по таймауту), OnProgress (мониторинг прогресса), Defer (отложенная отправка), Build (построение пакета сообщений) и других методов цепочки. Подробнее см. [документацию по SendDSL](docs/ru/developer-guide/adapters/send-dsl.md).

---

## Один и тот же код. Множество платформ.

*Тот же самый обработчик команд. Разные платформы. Без изменения бизнес-логики.*

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

**云湖**

<img src=".github/assets/demo-yunhu.png" alt="云湖 Демонстрация" />

</td>
</tr>
</table>

---

## Экосистема

ErisPulse — это не просто фреймворк. Установите и начните работать, не нужно создавать колесо с нуля.

<table>
<tr>
<td align="center" width="25%">

**Фреймворк**

Ядро выполнения

Единая модель событий и сообщений

</td>
<td align="center" width="25%">

**Dashboard**

Визуальное управление

Плагины · Журналы · Настройки

[Онлайн демонстрация →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

Естественный язык → Готовые модули

[Опыт использования →](https://www.erisdev.com/#builder)

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

Инструмент epsdk для создания проекта

</td>
</tr>
</table>

---

## Происхождение проекта

ErisPulse не был создан с целью стать фреймворком.

Он начался как проект **Amer** — для синхронизации и взаимодействия сообщений между различными платформами.

По мере увеличения числа подключаемых платформ мы начали поддерживать асинхронную версию ryunhusdk2 и постепенно абстрагировали единые модели событий и адаптеров.

Эти практики в конечном итоге превратились в сегодняшний ErisPulse.

Его цель осталась неизменной:

**Позволить разработчикам сосредоточиться на бизнес-логике, а не на различиях платформ.**

---

### Быстрый старт

#### Сценарий установки с одним кликом (рекомендуется)

Сценарий установки автоматически определит вашу среду (Docker, Python, uv), предложит наиболее подходящий способ установки и поддерживает несколько языков (китайский/English/日本語/Русский/繁體中文).

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

#### Использование Docker (рекомендуется)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Доступ к Docker Hub невозможен?</summary>

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

> Образ содержит фреймворк ErisPulse и панель управления Dashboard, поддерживает архитектуры `linux/amd64` и `linux/arm64`.

После запуска перейдите на `http://<host>:<port>/Dashboard` и используйте установленный токен в качестве пароля для входа в панель управления Dashboard.

</details>

<details>
<summary>Использование предварительной версии (Dev)</summary>

Для использования предварительной версии установите `ERISPULSE_CHANNEL=dev`:

```bash
# Способ 1: Использование переменных окружения (рекомендуется)
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# Способ 2: Сборка образа dev
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

Если необходимо, чтобы при запуске автоматически обновлялась до последней версии (стабильной или dev), явно установите `ERISPULSE_UPDATE_ON_START=true`:

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

Также можно загрузить предварительно собранный образ dev:

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Переменные окружения Docker</summary>

| Переменная | Значение по умолчанию | Описание |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | Канал версий: `stable` (стабильная) или `dev` (предварительная) |
| `ERISPULSE_UPDATE_ON_START` | `false` | Обновлять до последней версии при запуске контейнера (требуется явное включение) |
| `ERISPULSE_DASHBOARD_TOKEN` | пусто | Токен для входа в Dashboard |
| `ERISPULSE_PORT` | `8000` | Порт для Dashboard |
| `TZ` | `Asia/Shanghai` | Часовой пояс контейнера |

> Установка `ERISPULSE_UPDATE_ON_START=true` гарантирует, что даже если образ устарел, контейнер при запуске автоматически обновится до последней версии.

</details>

#### Магазин приложений 1Panel

Установите ErisPulse через [1Panel](https://1panel.cn) приложений, подробнее см. [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse доступен в магазине приложений 1Panel, можно использовать сторонний репозиторий [okxlin/appstore](https://github.com/okxlin/appstore) для установки.

#### Установка через pip

```bash
pip install ErisPulse
```

> Также можно использовать сценарий установки с одним кликом, который автоматически определит среду и подскажет настройки.

#### Инициализация проекта

```bash
# Интерактивная инициализация
epsdk init

# Быстрая инициализация (указание имени проекта)
epsdk init -q -n my_bot
```

#### Создание первого бота

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

@command("ping", help="Тестировать, работает ли бот")
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

Более подробную информацию см.:
- [Руководство по быстрому старту](docs/ru/quick-start.md)
- [Введение](docs/ru/getting-started/)

#### Пример многошагового диалога

ErisPulse имеет встроенную мощную систему многошаговых диалогов, что позволяет легко реализовать интерактивные сценарии, такие как навигация, сбор информации и т.д.:

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Добро пожаловать на регистрацию!")
    
    # Многошаговый сбор информации пользователя с автоматической проверкой
    data = await conv.collect([
        {"key": "name", "prompt": "Введите имя"},
        {"key": "age", "prompt": "Введите возраст",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "Возраст должен быть числом, пожалуйста, введите снова"},
    ])
    
    if data and await conv.confirm(f"Подтвердить регистрацию? Имя: {data['name']}, Возраст: {data['age']}"):
        # Использование SendDSL для активной отправки уведомлений
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"Регистрация прошла успешно! Добро пожаловать {data['name']}")
        # или await event.reply("Регистрация прошла успешно!")

# Автоматическая обработка запросов на добавление в друзья
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # Принять запрос
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"Запрос на добавление в друзья автоматически принят, добро пожаловать {user_name}")
```

<details>
<summary>Больше примеров API Conversation (ветвление, выбор, сохранение)</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # Вопрос с вариантами ответа
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
        await conv.say("Неверно, правильный ответ — Guido van Rossum")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # Ветвление, построение сложных интерактивных процессов
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

См. [Многошаговые диалоги Conversation](docs/ru/advanced/conversation.md)

</details>

---

## Поддерживаемые платформы

Приглашаем к вкладу в адаптеры!

| Адаптер | Описание |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Платформа мгновенных сообщений Kook (开黑啦) |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Децентрализованный протокол мгновенных сообщений Matrix |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | Общий протокол роботов OneBot v11 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | Стандартный протокол OneBot v12 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | Официальная платформа роботов QQ |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Веб-дебаг, без подключения к реальной платформе |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Глобальная платформа мгновенных сообщений Telegram |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Адаптер для отправки и получения электронной почты |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Корпоративная платформа мгновенных сообщений Yunhu (для подключения роботов) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖用户](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Адаптер подключения к пользовательскому протоколу Yunhu |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Глобальная платформа коммуникации Discord, поддерживает серверы, каналы и личные сообщения |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | Общий HTTP-мостовой адаптер для подключения к любым системам |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [微信公众号](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Официальная платформа WeChat для публикаций и роботов |

См. [Описание адаптеров](docs/ru/platform-guide/README.md)

---

### Применение

<div align="center">

| Мультиплатформенный робот | Чат-ассистент | Автоматизация | Пересылка сообщений |
|:---:|:---:|:---:|:---:|
| Развертывание одного и того же робота на нескольких платформах | Подключение модуля ИИ для общения и взаимодействия | Уведомления, управление задачами, сбор данных | Синхронизация и пересылка сообщений между платформами |

</div>

---

## Сообщество

Добро пожаловать в сообщество ErisPulse, где разработчики общаются и совместно строят экосистему.

### 云湖

ID группы: `635409929`

Присоединиться к чату:

https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199

### QQ группа

https://qm.qq.com/q/TOwnCmypcy

### Telegram

https://t.me/ErisPulse

---

### Руководство по вкладу

Здоровье проекта ErisPulse зависит от вашего вклада! Мы приветствуем любые формы вклада:

1. **Сообщение об ошибках** — отправьте отчет об ошибке в [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Запрос функций** — предложите новые идеи через [обсуждения в сообществе](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Кодовый вклад** — перед отправкой PR ознакомьтесь с [стилем кода](docs/ru/styleguide/) и [руководством по вкладу](CONTRIBUTING.md)
4. **Улучшение документации** — помогите улучшить документацию и примеры кода

[Присоединиться к обсуждению](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Благодарности

<img src=".github/assets/thanks.png" width="200" alt="Благодарности" />

Часть кода этого проекта основана на [sdkFrame](https://github.com/runoneall/sdkFrame).

Стандартизированный слой основных адаптеров опирается на и получает пользу от [спецификации OneBot12](https://12.onebot.dev/).

Особая благодарность сообществу и экосистеме Yunhu.

Ранние исследования и развитие ErisPulse невозможно без поддержки сообщества разработчиков Yunhu, многие идеи, адаптеры и практический опыт родились здесь.

Также благодарим всех разработчиков и авторов проектов, внесших вклад в ErisPulse, OneBot и открытую экосистему.

</div>