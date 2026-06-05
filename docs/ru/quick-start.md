# Быстрый старт

> Столкнулись с непонятными терминами? Ознакомьтесь с [Глоссарием](terminology.md), чтобы получить понятные объяснения.

## Установка ErisPulse

### Скрипт для одной команды (Рекомендуется)

Скрипт автоматически определяет вашу среду (Docker, Python, uv) и направляет вас на выбор наиболее подходящего способа установки.

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

Скрипт проведёт вас через следующие шаги:

- **Docker установка** (рекомендуется, если обнаружен Docker): выбор зеркального репозитория (Docker Hub / GHCR), версии канала (stable / pre-release), конфигурация панели управления Dashboard, настройки портов
- **Традиционная установка**: автоматическое создание виртуального окружения, выбор версии ErisPulse, необязательная установка модуля панели управления Dashboard

### Использование Docker

Docker образ уже содержит фреймворк ErisPulse и панель управления Dashboard.

```bash
# Скачайте docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Настройте токен для Dashboard и запустите
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub недоступен?</summary>

Используйте зеркало GitHub Container Registry и измените `image` в `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

После запуска перейдите на `http://<host>:8000/Dashboard` и войдите в систему, используя настроенный токен.

### Установка через pip

Убедитесь, что ваша версия Python >= 3.10, затем используйте pip для установки:

```bash
pip install ErisPulse
```

Если вы уже установили [uv](https://github.com/astral-sh/uv), вы также можете использовать `uv pip install ErisPulse`, это будет быстрее.

## Инициализация проекта

### Интерактивная инициализация (Рекомендуется)

```bash
epsdk init
```

Это запустит интерактивный мастер, который проведёт вас через:
- настройку названия проекта
- конфигурацию уровня логирования
- конфигурацию сервера (хост и порт)
- выбор и конфигурацию адаптера
- создание структуры проекта

### Быстрая инициализация

```bash
# Быстрый режим с указанием названия проекта
epsdk init -q -n my_bot

# Или просто указать название проекта
epsdk init -n my_bot
```

### Ручное создание проекта

Если вы предпочитаете создать проект вручную:

```bash
mkdir my_bot && cd my_bot
epsdk init
```

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

При запуске без указания имени пакета открывается интерактивный интерфейс установки:

```bash
epsdk install
```

## Запуск проекта

```bash
# Обычный запуск
epsdk run main.py

# Режим автоматической перезагрузки (рекомендуется при разработке)
epsdk run main.py --reload
```

## Структура проекта

Структура проекта после инициализации:

```
my_bot/
├── config/
│   └── config.toml          # Файл конфигурации
└── main.py                  # Файл точки входа

```

## Файл конфигурации

Базовая конфигурация `config.toml`:

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# Конфигурация адаптера
```

## Дальнейшие шаги

- [Обзор руководства по началу работы](getting-started/README.md) - 了解 ErisPulse 的基本概念 (Понимание основных концепций ErisPulse)
- [Создание первого бота](getting-started/first-bot.md) - 创建一个简单的机器人 (Создание простого бота)
- [Руководство для пользователя](user-guide/) - 深入了解配置和模块管理 (Углубленное изучение конфигурации и управления модулями)
- [Руководство для разработчика](developer-guide/) - 开发自定义模块和适配器 (Разработка пользовательских модулей и адаптеров)