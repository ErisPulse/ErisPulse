<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Русский**

# ErisPulse

**Фреймворк разработки событийно-ориентированных мультиплатформенных роботов**

На основе стандарта OneBot12, написание кода один раз, развертывание на нескольких платформах. Гибкая система плагинов, поддержка горячей перезагрузки и полный набор инструментов для разработчиков, подходит для различных сценариев, от простых чат-ботов до сложных автоматизированных систем.

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
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/模块市场-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="模块市场"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="讨论"></a>
</p>

<br clear="both">

---

<div align="center">

### Основные особенности · Конструктор модулей AI

</div>

> 👉 **Опишите задачу естественным языком, AI изучит официальную документацию и сгенерирует готовый код модуля/адаптера, который можно скачать**
> [**Попробовать прямо сейчас → `https://www.erisdev.com/#builder`**](https://www.erisdev.com/#builder)
>
> Поддерживаемые типы модулей: адаптеры, функциональные модули, шаблоны плагинов
>
> Также поддерживается рабочий процесс Vibe Coding — после загрузки AI-материалов можно отправить их AI для использования [Посмотреть](docs/ru/ai-support/README.md)

<table>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### ⚡ Архитектура на основе событий

Четкая модель событий на основе стандарта OneBot12, делает логику обработки сообщений более понятной и эффективной

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🌐 Совместимость с разными платформами

Написание модуля/плагина один раз, можно использовать на всех платформах, без необходимости повторного разработки для каждой платформы

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 🧩 Модульная архитектура

Гибкая система плагинов, легко расширяемая и интегрируемая, поддерживает управление модулями с возможностью горячей замены

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🔄 Горячая перезагрузка + AI-помощь

При разработке код можно перезагружать без перезапуска; AI-помощь в разработке позволяет превратить требования в готовые модули

</td>
</tr>
</table>

---

### Быстрый старт

#### Сценарий установки одним нажатием (рекомендуется)

Сценарий автоматически определит вашу среду (Docker, Python, uv), предложит выбрать наиболее подходящий способ установки, поддерживает несколько языков (китайский/English/японский/Русский/китайский традиционный).

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
<summary>Не работает Docker Hub?</summary>

Если Docker Hub недоступен, можно использовать GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

При использовании образа ghcr.io необходимо изменить `docker-compose.yml` в параметре image:
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>Быстрый запуск</summary>

```bash
# Скачать docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Установить токен для доступа к Dashboard и запустить
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> В образе встроен фреймворк ErisPulse и панель управления Dashboard, поддерживает архитектуры `linux/amd64` и `linux/arm64`.

После запуска перейдите по адресу `http://<host>:<port>/Dashboard` и используйте установленный токен в качестве пароля для входа в панель управления Dashboard.

</details>

<details>
<summary>Использование предрелизной версии (Dev)</summary>

Установка `ERISPULSE_CHANNEL=dev` позволит использовать предрелизную версию:

```bash
# Способ 1: Использование переменных окружения (рекомендуется)
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# Способ 2: Сборка образа dev
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

Если необходимо автоматически обновляться до последней версии при запуске (независимо от стабильной или dev версии), явно установите `ERISPULSE_UPDATE_ON_START=true`:

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
| `ERISPULSE_CHANNEL` | `stable` | Канал версий: `stable` (стабильная версия) или `dev` (предрелизная версия) |
| `ERISPULSE_UPDATE_ON_START` | `false` | Автоматическое обновление до последней версии при запуске контейнера (требуется явное включение) |
| `ERISPULSE_DASHBOARD_TOKEN` | пустая строка | Токен для входа в Dashboard |
| `ERISPULSE_PORT` | `8000` | Порт для панели управления Dashboard |
| `TZ` | `Asia/Shanghai` | Часовой пояс контейнера |

> Установка `ERISPULSE_UPDATE_ON_START=true` гарантирует, что даже если образ устарел, контейнер автоматически получит последнюю версию при запуске.

</details>

#### Магазин приложений 1Panel

Установите ErisPulse одним нажатием через [1Panel](https://1panel.cn) приложений, подробнее см. [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel).

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### Установка через pip

```bash
pip install ErisPulse
```

> Также можно использовать сценарий установки, который автоматически определит среду и предложит настройки.

#### Результаты выполнения

##### Панель управления:

[![Онлайн демонстрация](https://img.shields.io/badge/Online%20Demo-Dashboard-FF6B9D?style=for-the-badge&logo=github&logoColor=white)](https://dashdemo.erisdev.com/)

> 💡 Онлайн-демонстрация панели управления: [DashDemo](https://dashdemo.erisdev.com/)

<table>
<tr>
<td width="50%">

<img src=".github/assets/docs/dashboard.png" alt="Dashboard демонстрация" />

</td>
<td width="50%">

<video src="https://github.com/user-attachments/assets/157191c4-9a84-433c-b311-0c57e3a21151" controls width="100%"></video>

</td>
</tr>
</table>


##### Один и тот же код, несколько платформ:

<table>
<tr>
<td align="center" width="33%">

**Kook**

<img src=".github/assets/demo-kook.png" alt="Kook демонстрация" />

</td>
<td align="center" width="33%">

**QQ**

<img src=".github/assets/demo-qq.png" alt="QQ демонстрация" />

</td>
<td align="center" width="33%">

**Yunhu**

<img src=".github/assets/demo-yunhu.png" alt="Yunhu демонстрация" />

</td>
</tr>
</table>

#### Инициализация проекта

```bash
# Интерактивная инициализация
epsdk init

# Быстрая инициализация (указать имя проекта)
epsdk init -q -n my_bot
```

#### Создание первого робота

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

@command("ping", help="Проверить, работает ли робот")
async def ping_handler(event):
    await event.reply("Pong! Робот работает нормально.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**Описание результатов**

Отправка `/hello`

Робот отвечает: `Привет, {имя пользователя}!`

---

Отправка `/ping`

Робот отвечает: `Pong! Робот работает нормально.`

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

Более подробная информация:
- [Руководство по быстрому старту](docs/ru/quick-start.md)
- [Введение](docs/ru/getting-started/)

#### Примеры многоконтактного диалога

ErisPulse имеет встроенный мощный движок многоконтактного диалога, который легко реализует навигационные операции, сбор информации и другие интерактивные сценарии:

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Добро пожаловать на регистрацию!")
    
    # Многошаговый сбор информации от пользователя, автоматическая проверка
    data = await conv.collect([
        {"key": "name", "prompt": "Пожалуйста, введите имя"},
        {"key": "age", "prompt": "Пожалуйста, введите возраст",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "Возраст должен быть числом, пожалуйста, введите снова"},
    ])
    
    if data and await conv.confirm(f"Подтвердить регистрацию? Имя: {data['name']}, возраст: {data['age']}"):
        # Использование SendDSL для отправки уведомлений
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
        await conv.say("Время вышло, попробуйте снова в следующий раз!")
    else:
        await conv.say("Неверно, правильный ответ — Guido van Rossum")

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

Смотрите [Многоконтактный диалог Conversation](docs/ru/advanced/conversation.md)

</details>

---

### Поддерживаемые адаптеры

Приглашаем к участию в разработке адаптеров!

| Адаптер | Описание |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Платформа мгновенных сообщений Kook (开黑啦) |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Децентрализованный протокол общения Matrix |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | Общий протокол роботов OneBot v11 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | Стандартный протокол OneBot v12 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | Официальная платформа роботов QQ |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [Sandbox](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | Веб-дебаг, без подключения к реальной платформе |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | Глобальная платформа мгновенных сообщений Telegram |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [Email](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | Адаптер для отправки и получения электронной почты |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | Корпоративная платформа мгновенных сообщений (подключение роботов) |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [Yunhu User](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | Адаптер для подключения к платформе Yunhu по пользовательскому протоколу |
| [花枫咖啡馆](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | Глобальная платформа коммуникации Discord, поддержка серверов, каналов и личных сообщений |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | Общий адаптер для HTTP-моста, подключение к любой системе |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [WeChat Official Account](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | Официальная платформа публичных аккаунтов WeChat |

Смотрите [Подробное описание адаптеров](docs/ru/platform-guide/README.md)

---

### Сценарии использования

<div align="center">

| Мультиплатформенный робот | Чат-ассистент | Автоматизация | Пересылка сообщений |
|:---:|:---:|:---:|:---:|
| Развертывание робота с одинаковой функциональностью на нескольких платформах | Подключение модуля чат-ассистента AI для развлечений и взаимодействия | Уведомления, управление задачами, сбор данных | Синхронизация и пересылка сообщений между платформами |

</div>

---

### Руководство по вкладу

Здоровье проекта ErisPulse зависит и от вас! Мы приветствуем любые формы участия:

1. **Сообщение об ошибках** — отправьте отчет об ошибках в [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues)
2. **Запрос на функцию** — предложите новые идеи через [Обсуждения сообщества](https://github.com/ErisPulse/ErisPulse/discussions)
3. **Вклад в код** — перед отправкой PR ознакомьтесь с [стилем кода](docs/ru/styleguide/) и [руководством по вкладу](CONTRIBUTING.md)
4. **Улучшение документации** — помогите улучшить документацию и примеры кода

[Присоединиться к обсуждению сообщества](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

<div align="center">

### Благодарности

<img src=".github/assets/thanks.png" width="200" alt="Спасибо" />

Часть кода этого проекта основана на [sdkFrame](https://github.com/runoneall/sdkFrame) · Ядро адаптера стандартизировано по [спецификации OneBot12](https://12.onebot.dev/) · Благодарим всех разработчиков и авторов, внесших вклад в сообщество открытого программного обеспечения

</div>