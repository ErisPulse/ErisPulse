# Быстрый старт

> **Это ваш первый шаг.** Запустите бота ErisPulse с нуля всего за 5 минут.
>
> Не понимаете какие-то термины? Посмотрите в [Глоссарий](docs/ru/terminology.md).

## Установка ErisPulse

### Скрипт автоматической установки (рекомендуется)

Скрипт автоматически определит вашу среду (Docker, Python, uv) и подскажет, какой способ установки лучше подойдет.

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

Скрипт проведет вас через:

- **Установка Docker** (рекомендуется при наличии Docker): выбор зеркала (Docker Hub / GHCR), канала версий (стабильный / пре-релиз), конфигурация панели управления Dashboard, настройка портов
- **Традиционная установка**: автоматическое создание виртуальной среды, выбор версии ErisPulse, дополнительная установка панели управления Dashboard

### Использование Docker

Образ Docker уже содержит фреймворк ErisPulse и панель управления Dashboard.

```bash
# Скачайте docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Настройте токен для Dashboard и запустите
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub недоступен?</summary>

Используйте зеркало GitHub Container Registry, изменив `image` в `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

После запуска откройте `http://<host>:8000/Dashboard` и войдите с использованием установленного токена.

### Установка через pip

Убедитесь, что ваша версия Python >= 3.10, затем установите с помощью pip:

```bash
pip install ErisPulse
```

Если вы уже установили [uv](https://github.com/astral-sh/uv), вы также можете использовать `uv pip install ErisPulse` — это будет работать быстрее.

## Инициализация проекта

### Интерактивная инициализация (рекомендуется)

```bash
epsdk init
```

Это запустит интерактивный помощник, который проведет вас через:
- Настройку имени проекта
- Настройку уровня логирования
- Настройку сервера (хост и порт)
- Выбор и настройку адаптера
- Создание структуры проекта

### Быстрая инициализация

```bash
# Быстрый режим с указанием имени проекта
epsdk init -q -n my_bot

# Или только указание имени проекта
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

При отсутствии указания имени пакета вы попадете в интерфейс интерактивной установки:

```bash
epsdk install
```

## Запуск проекта

```bash
# Обычный запуск
epsdk run main.py

# Режим перезагрузки при изменениях (рекомендуется для разработки)
epsdk run main.py --reload
```

## Включение автодополнения в IDE (необязательно)

ErisPulse динамически обнаруживает модули и адаптеры, поэтому IDE по умолчанию не может предлагать автодополнение для платформенно-специфичных методов.
Выполните следующую команду для генерации типов:

```bash
epsdk types
```

После генерации, указывая импортированные типы как переменные, вы получите точное автодополнение (подробнее см. в [Руководстве по автодополнению IDE](docs/ru/getting-started/ide-completion.md)):

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # Автодополнение платформенно-специфичных методов
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

Базовая конфигурация в `config.toml`:

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# Настройки адаптера
```

## Дальнейшие действия

Когда бот запущен, вы можете продолжить работу по мере необходимости:

**Хотите узнать, как работает фреймворк?**
- [Основные концепции](docs/ru/getting-started/basic-concepts.md) — дизайн адаптеров / модулей / событий
- [Обзор архитектуры](docs/ru/architecture.md) — визуальная диаграмма архитектуры

**Хотите реализовать больше функций?**
- [Примеры распространенных задач](docs/ru/getting-started/common-tasks.md) — хранение, планирование задач, контроль прав доступа
- [Введение в обработку событий](docs/ru/getting-started/event-handling.md) — обработка сообщений, уведомлений, запросов

**Хотите разрабатывать свои модули / адаптеры?**
- [Введение в разработку модулей](docs/ru/developer-guide/modules/getting-started.md)
- [Введение в разработку адаптеров](docs/ru/developer-guide/adapters/getting-started.md)

**Справочные материалы по необходимости:**
- [Описание файла конфигурации](docs/ru/user-guide/configuration.md) · [Команды CLI](docs/ru/user-guide/cli-reference.md) · [Руководство по развертыванию](docs/ru/user-guide/deployment.md)