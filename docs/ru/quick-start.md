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

## Далее

После того как бот запущен, вы можете продолжить работу в зависимости от необходимости:

**Хотите узнать, как работает фреймворк?**
- [Основные концепции](getting-started/basic-concepts.md) — дизайн адаптеров / модулей / событий
- [Обзор архитектуры](architecture.md) — визуальная диаграмма архитектуры

**Хотите реализовать больше функций?**
- [Примеры распространенных задач](getting-started/common-tasks.md) — хранение, запланированные задачи, контроль прав доступа
- [Введение в обработку событий](getting-started/event-handling.md) — сообщения, уведомления, обработка запросов

**Хотите разработать свой модуль / адаптер?**
- [Введение в разработку модулей](developer-guide/modules/getting-started.md)
- [Введение в разработку адаптеров](developer-guide/adapters/getting-started.md)

**По мере необходимости:**
- [Описание конфигурационных файлов](user-guide/configuration.md) · [Команды CLI](user-guide/cli-reference.md) · [Руководство по развертыванию](user-guide/deployment.md)