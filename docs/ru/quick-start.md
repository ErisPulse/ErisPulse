# Быстрый старт

> **Это ваш первый шаг.** Запустите робота ErisPulse за 5 минут.

## Установка ErisPulse

### Сценарий установки с одним нажатием (рекомендуется)

Сценарий установки автоматически определит вашу среду (Docker, Python, uv) и предложит выбрать наиболее подходящий способ установки.

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

Сценарий проведёт вас через:

- **Установка Docker** (рекомендуется, если Docker обнаружен): выбор источника образа (Docker Hub / GHCR), канал версий (стабильный / предварительный), настройка панели управления Dashboard, настройка портов
- **Традиционная установка**: автоматическое создание виртуальной среды, выбор версии ErisPulse, опциональная установка модуля панели управления Dashboard

### Использование Docker

Docker-образ уже включает в себя фреймворк ErisPulse и панель управления Dashboard.

```bash
# Скачать docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Установить токен Dashboard и запустить
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Не доступен Docker Hub?</summary>

Используйте образ из GitHub Container Registry, изменив `image` в `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

После запуска перейдите по адресу `http://<host>:8000/Dashboard` и войдите, используя установленный токен.

### Установка с помощью pip

Убедитесь, что ваша версия Python >= 3.10, затем установите с помощью pip:

```bash
pip install ErisPulse
```

Если у вас установлен [uv](https://github.com/astral-sh/uv), вы также можете использовать `uv pip install ErisPulse`, установка будет быстрее.

## Инициализация проекта

### Интерактивная инициализация (рекомендуется)

```bash
epsdk init
```

Это запустит интерактивное руководство, которое проведёт вас через:
- Настройку имени проекта
- Конфигурацию уровня логирования
- Настройку сервера (хост и порт)
- Выбор и настройку адаптера
- Создание структуры проекта

### Быстрая инициализация

```bash
# Быстрый режим с указанием имени проекта
epsdk init -q -n my_bot

# Или просто с указанием имени проекта
epsdk init -n my_bot
```

### Ручное создание проекта

Если вы предпочитаете создавать проект вручную:

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

Если не указать имя пакета, откроется интерактивное окно установки:

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

## Включение автодополнения IDE (необязательно)

ErisPulse динамически обнаруживает модули/адаптеры, но IDE по умолчанию не может дополнять методы, специфичные для платформы. Запустите следующую команду для генерации типовых заглушек:

```bash
epsdk types
```

После генерации используйте импортированные типы для аннотации переменных, чтобы получить точное автодополнение (подробнее в [Руководстве по автодополнению IDE](./getting-started/ide-completion.md)):

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # Дополнение специфичных методов платформы
```

## Структура проекта

Структура проекта после инициализации:

```
my_bot/
├── config/
│   └── config.toml          # Файл конфигурации
└── main.py                  # Точка входа

```

## Файл конфигурации

Базовый файл `config.toml`:

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# Конфигурация адаптера
```

## Дальнейшие действия

После запуска робота, вы можете продолжить по своему усмотрению:

**Хотите узнать, как работает фреймворк?**
- [Основные понятия](getting-started/basic-concepts.md) — Архитектура адаптеров / модулей / событий
- [Обзор архитектуры](architecture.md) — Визуальная схема архитектуры

**Хотите реализовать больше функций?**
- [Примеры распространённых задач](getting-started/common-tasks.md) — Хранение данных, планирование задач, контроль доступа
- [Введение в обработку событий](getting-started/event-handling.md) — Обработка сообщений, уведомлений, запросов

**Хотите разработать свой собственный модуль / адаптер?**
- [Введение в разработку модулей](developer-guide/modules/getting-started.md)
- [Введение в разработку адаптеров](developer-guide/adapters/getting-started.md)

**Дополнительная справка:**
- [Описание файла конфигурации](user-guide/configuration.md) · [Справочник команд CLI](user-guide/cli-reference.md) · [Руководство по развертыванию](user-guide/deployment.md)