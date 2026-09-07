# Быстрый старт

> **Это ваш первый шаг.** Запустите робота ErisPulse за 5 минут, начиная с нуля.

## Установка ErisPulse

### Сценарий установки с одним нажатием (рекомендуется)

Сценарий автоматически определяет вашу среду (Docker, Python, uv) и предлагает вам выбрать наиболее подходящий способ установки.

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

Сценарий поможет вам выполнить следующие действия:

- **Установка с помощью Docker** (рекомендуется, если Docker обнаружен): выбор источника образа (Docker Hub / GHCR), канал версий (стабильная / предварительная), настройка панели управления Dashboard, настройка портов
- **Традиционная установка**: автоматическое создание виртуальной среды, выбор версии ErisPulse, необязательная установка модуля панели управления Dashboard

### Использование Docker

В образе Docker уже включены фреймворк ErisPulse и панель управления Dashboard.

```bash
# Загрузка docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Установка токена Dashboard и запуск
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Не удается получить доступ к Docker Hub?</summary>

Используйте образ из GitHub Container Registry, изменив параметр image в файле `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

После запуска перейдите по адресу `http://<host>:8000/Dashboard` и войдите, используя установленный токен.

### Установка с помощью pip

Убедитесь, что у вас установлен Python версии >= 3.10, затем выполните установку с помощью pip:

```bash
pip install ErisPulse
```

Если у вас уже установлен [uv](https://github.com/astral-sh/uv), вы также можете использовать `uv pip install ErisPulse`, что обеспечит более быструю установку.

## Инициализация проекта

### Интерактивная инициализация (рекомендуется)

```bash
epsdk init
```

Это запустит интерактивное руководство, которое поможет вам выполнить следующие шаги:
- Настройка имени проекта
- Настройка уровня логирования
- Настройка сервера (хост и порт)
- Выбор и настройка адаптера
- Создание структуры проекта

### Быстрая инициализация

```bash
# Быстрый режим с указанием имени проекта
epsdk init -q -n my_bot

# Или просто указание имени проекта
epsdk init -n my_bot
```

### Создание проекта вручную

Если вы предпочитаете создавать проект вручную:

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## Установка модуля

### Установка через CLI

```bash
epsdk install Yunhu AIChat
```

### Просмотр доступных модулей

```bash
epsdk list-remote
```

### Интерактивная установка

При отсутствии имени пакета открывается интерактивный интерфейс установки:

```bash
epsdk install
```

## Запуск проекта

```bash
# Обычный запуск
epsdk run main.py

# Режим горячей перезагрузки (рекомендуется при разработке)
epsdk run main.py --reload
```

## Включение автодополнения в IDE (по желанию)

Динамически обнаруживаемые модули/адаптеры ErisPulse не поддерживаются автодополнением в IDE по умолчанию.
Запустите следующую команду для генерации типовых заглушек:

```bash
epsdk types
```

После генерации, используйте импортированные типы для аннотации переменных, чтобы получить точное автодополнение (подробнее см. [Руководство по автодополнению в IDE](./getting-started/ide-completion.md)):

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # Автодополнение методов, специфичных для платформы
```

## Структура проекта

Структура проекта после инициализации:

```
my_bot/
├── config/
│   └── config.toml          # Файл конфигурации
└── main.py                  # Точка входа

```

## Конфигурационный файл

Базовый конфигурационный файл `config.toml`:

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# Конфигурация адаптера
```

## Далее

После запуска робота вы можете продолжить по мере необходимости:

**Хотите узнать, как работает фреймворк?**
- [Основные понятия](getting-started/basic-concepts.md) — архитектура адаптеров / модулей / событий
- [Обзор архитектуры](architecture.md) — визуальная схема архитектуры

**Хотите реализовать больше функций?**
- [Примеры распространённых задач](getting-started/common-tasks.md) — хранение данных, планирование задач, управление правами доступа
- [Введение в обработку событий](getting-started/event-handling.md) — обработка сообщений, уведомлений, запросов

**Хотите разработать свой собственный модуль / адаптер?**
- [Введение в разработку модулей](developer-guide/modules/getting-started.md)
- [Введение в разработку адаптеров](developer-guide/adapters/getting-started.md)

**Справочные материалы по запросу:**
- [Описание файла конфигурации](user-guide/configuration.md) · [Справочник команд CLI](user-guide/cli-reference.md) · [Руководство по развертыванию](user-guide/deployment.md)