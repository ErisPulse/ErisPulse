<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Русский**

# ErisPulse

**Написано один раз, развернуто на нескольких платформах.**

Фреймворк разработки событийно-ориентированных мультиплатформенных чат-ботов.

Основан на стандарте OneBot12, что позволяет разработать код один раз и развернуть на нескольких платформах. Гибкая система плагинов, поддержка горячей перезагрузки и полный набор инструментов для разработчиков, подходящий для различных сценариев — от простых чат-ботов до сложных автоматизированных систем.

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue)](https://pepy.tech/project/ErisPulse)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://github.com/astral-sh/ruff)
[![Socket](https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white)](https://socket.dev/pypi/package/erispulse)
[![文档](https://img.shields.io/badge/文档-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white)](https://www.erisdev.com)
[![模块市场](https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white)](https://www.erisdev.com/#market)
[![讨论](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### Основные особенности

</div>

<table>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### ⚡ Архитектура на основе событий

Четкая модель событий на основе стандарта OneBot12, что делает логику обработки сообщений более интуитивной и эффективной

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🌐 Совместимость с несколькими платформами

Модули плагинов можно написать один раз и использовать на всех платформах, без повторного разработки для каждой платформы

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 🧩 Модульная архитектура

Гибкая система плагинов, легко расширяемая и интегрируемая, поддержка горячей загрузки модулей

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🔄 Горячая перезагрузка + ИИ-помощник

Разработка без перезапуска кода при изменении; ИИ-помощник упрощает создание модулей по запросу

</td>
</tr>
</table>

---

## Один и тот же код. Несколько платформ.

*Одинаковые обработчики команд. Разные платформы. Без изменения бизнес-логики.*

<table>
<tr>
<td align="center" width="33%">

**Kook**

![](https://github.com/ErisPulse/ErisPulse/blob/main/.github/assets/demo-kook.png?raw=true)

</td>
<td align="center" width="33%">

**QQ**

![](https://github.com/ErisPulse/ErisPulse/blob/main/.github/assets/demo-qq.png?raw=true)

</td>
<td align="center" width="33%">

**Yunhu**

![](https://github.com/ErisPulse/ErisPulse/blob/main/.github/assets/demo-yunhu.png?raw=true)

</td>
</tr>
</table>

---

## Экосистема

ErisPulse — это не просто фреймворк. Установите и начните использовать, без необходимости создавать всё с нуля.

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

Плагины · Логи · Конфигурации

[Онлайн демонстрация →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

Естественный язык → готовые модули

[Опыт использования →](https://www.erisdev.com/#builder)

</td>
<td align="center" width="25%">

**Модульный рынок**

Готовые плагины

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

Утилита `epsdk` для создания проектов

</td>
</tr>
</table>

---

## Происхождение проекта

ErisPulse не был создан просто ради создания фреймворка.

Он первоначально возник как проект **Amer** — для синхронизации и взаимодействия сообщений между различными платформами.

По мере увеличения числа подключаемых платформ мы начали поддерживать асинхронную версию **ryunhusdk2**, постепенно абстрагируя единые модели событий и систему адаптеров.

Эти практики привели к появлению ErisPulse.

Его цель всегда оставалась неизменной:

**Позволить разработчикам сосредоточиться на бизнес-логике, а не на различиях платформ.**

---

### Быстрый старт

#### Сценарий установки с одной командой (рекомендуется)

Сценарий установки автоматически определит вашу среду (Docker, Python, uv), направит вас к наилучшему способу установки и поддерживает несколько языков (китайский/English/日本語/Русский/繁體中文).

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

> Образ включает в себя фреймворк ErisPulse и панель управления Dashboard, поддерживает архитектуры `linux/amd64` и `linux/arm64`.

После запуска перейдите по адресу `http://<host>:<port>/Dashboard` и используйте установленный токен как пароль для входа в панель управления Dashboard.

</details>

<details>
<summary>Использование предрелизной версии (Dev)</summary>

Для использования предрелизной версии установите `ERISPULSE_CHANNEL=dev`:

```bash
# Способ 1: Использование переменных окружения (рекомендуется)
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# Способ 2: Сборка образа dev
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

Для автоматического обновления до последней версии при запуске (независимо от стабильной или dev версии), явно установите `ERISPULSE_UPDATE_ON_START=true`:

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
| `ERISPULSE_CHANNEL` | `stable` | Канал версии: `stable` (стабильная) или `dev` (предрелизная) |
| `ERISPULSE_UPDATE_ON_START` | `false` | Автоматическое обновление до последней версии при запуске контейнера (требуется явное включение) |
| `ERISPULSE_DASHBOARD_TOKEN` | пустая строка | Токен для входа в Dashboard |
| `ERISPULSE_PORT` | `8000` | Порт для доступа к Dashboard |
| `TZ` | `Asia/Shanghai` | Часовой пояс контейнера |

> Включение `ERISPULSE_UPDATE_ON_START=true` гарантирует, что даже при использовании устаревшего образа контейнер будет обновляться до последней версии при запуске.

</details>

#### Магазин приложений 1Panel

Установите ErisPulse через [1Panel](https://1panel.cn) с помощью магазина приложений, подробнее смотрите в [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### Установка через pip

```bash
pip install ErisPulse
```

> Также можно использовать сценарий установки с одной командой, который автоматически определит среду и направит вас к настройке.

#### Инициализация проекта

```bash
# Интерактивная инициализация
epsdk init

# Быстрая инициализация (с указанием имени проекта)
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

@command("ping", help="Проверить, работает ли бот")
async def ping_handler(event):
    await event.reply("Pong! Бот работает нормально.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**Описание результатов**

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

#### Пример многошагового диалога

ErisPulse включает мощный движок многошаговых диалогов, что позволяет легко реализовать последовательные действия, сбор информации и другие интерактивные сценарии:

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
         "retry_prompt": "Возраст должен быть числом, попробуйте снова"},
    ])
    
    if data and await conv.confirm(f"Подтвердить регистрацию? Имя: {data['name']}, Возраст: {data['age']}"):
        # Использование SendDSL для отправки уведомлений
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"Регистрация успешна! Добро пожаловать, {data['name']}")
        # или await event.reply("Регистрация успешна!")

# Автоматическая обработка запросов на добавление в друзья
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # Принять запрос
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"Автоматически приняли запрос на добавление в друзья, добро пожаловать, {user_name}")
```

<details>
<summary>Подробнее о Conversation API (ветвление / выбор / сохранение)</summary>

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

Смотрите [Многошаговые диалоги (Conversation)](docs/ru/advanced/conversation.md)

</details>

---

## Поддерживаемые платформы

Мы приветствуем вклад в создание адаптеров!

| Адаптер | Описание |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Платформа мгновенных сообщений Kook (开黑啦) |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Децентрализованный протокол обмена сообщениями Matrix |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | Общий протокол роботов OneBot v11 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | Стандартный протокол OneBot v12 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | Официальная платформа роботов QQ |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Веб-дебаг, без подключения к реальной платформе |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Глобальная платформа мгновенных сообщений Telegram |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Адаптер для отправки и получения сообщений по протоколу Email |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Корпоративная платформа мгновенных сообщений Yunhu (для подключения роботов) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Адаптер для подключения к платформе Yunhu по протоколу Yunhu User |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Глобальная платформа коммуникации Discord, поддержка серверов, каналов и личных сообщений |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | Общий адаптер HTTP-моста, подключение к любым системам |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [WeChat Official Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Официальная платформа WeChat для публикации в официальных аккаунтах |

Смотрите [Детальное описание адаптеров](docs/ru/platform-guide/README.md)

---

### Применение

<div align="center">

| Мультиплатформенный бот | Чат-ассистент | Автоматизация | Пересылка сообщений |
|:---:|:---:|:---:|:---:|
| Развертывание бота с одинаковой функциональностью на нескольких платформах | Подключение модуля ИИ-чата для развлечений и взаимодействия | Уведомления, управление задачами, сбор данных | Синхронизация и пересылка сообщений между платформами |

</div>

---

## Сообщество

Добро пожаловать в сообщество ErisPulse, где вы можете обмениваться опытом и участвовать в развитии экосистемы.

### Yunhu

ID группы: `635409929`

Присоединиться к чату:

https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199

### QQ группа

https://qm.qq.com/q/TOwnCmypcy

### Telegram

https://t.me/ErisPulse

---

### Руководство по вкладу

Здоровье проекта ErisPulse требует вашего вклада! Мы приветствуем любые формы участия:

1. **Сообщение об ошибках** — отправьте отчет о багах в [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Запрос на функции** — предложите новые идеи через [Обсуждения сообщества](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Вклад в код** — перед отправкой PR ознакомьтесь с [Стилем кода](docs/ru/styleguide/) и [Руководством по вкладу](CONTRIBUTING.md)
4. **Улучшение документации** — помогите улучшить документацию и примеры кода

[Присоединиться к обсуждению сообщества](https://github.com/ErisPulse/ErisPulse/discussions)

---

## История звезд

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

<div align="center">

### Благодарности

![](https://github.com/ErisPulse/ErisPulse/blob/main/.github/assets/thanks.png?raw=true)

Часть кода этого проекта основана на [sdkFrame](https://github.com/runoneall/sdkFrame).

Стандартизированный уровень ядра адаптера основан на и получает пользу от [спецификации OneBot12](https://12.onebot.dev/).

Особая благодарность экосистеме и сообществу Yunhu.

Ранние исследования и развитие ErisPulse невозможно без поддержки сообщества разработчиков Yunhu, многие идеи, адаптеры и практический опыт родились здесь.

Также благодарим всех разработчиков и авторов проектов, внесших вклад в ErisPulse, OneBot и открытую экосистему.

</div>
