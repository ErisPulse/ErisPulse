# Руководство по публикации и модулю магазина

Опубликуйте разработанный вами модуль или адаптер в модуле магазина ErisPulse, чтобы другие пользователи могли легко находить и устанавливать их.

## Обзор модуля магазина

Модуль магазина ErisPulse — это централизованный реестр модулей, через который пользователи могут просматривать, искать и устанавливать сообщественные модули и адаптеры с помощью инструмента CLI.

### Просмотр и поиск

```bash
# Показать все пакеты, доступные на удаленном сервере
epsdk list-remote

# Показать только модули
epsdk list-remote -t modules

# Показать только адаптеры
epsdk list-remote -t adapters

# Принудительно обновить список удаленных пакетов
epsdk list-remote -r
```

Вы также можете посетить [официальный сайт ErisPulse](https://www.erisdev.com/#market), чтобы просмотреть модуль магазина онлайн.

### Поддерживаемые типы выпусков

| Тип | Описание | Точка входа (Entry-point) 组 |
|------|------|----------------|
| Модуль (Module) | Расширение функций бота, реализация бизнес-логики | `erispulse.module` |
| Адаптер (Adapter) | Подключение новых платформ обмена сообщениями | `erispulse.adapter` |

## Быстрая публикация

Весь процесс занимает всего три шага: настройка проекта → публикация в PyPI → отправка в модуль магазина.

### 1. Настройка pyproject.toml

Убедитесь, что в каталоге проекта есть файлы `pyproject.toml`, `README.md` и настроены точки входа в зависимости от типа:

#### Модуль

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Описание функций модуля"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### Адаптер

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "Описание функций адаптера"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **Важно**: Имя пакета рекомендуется начинать с `ErisPulse-`, чтобы пользователи могли легко идентифицировать пакеты экосистемы ErisPulse. Ключевое имя точки входа (например, `"MyModule"`) будет использоваться как имя модуля в SDK.

### 2. Публикация в PyPI

```bash
# Сборка и публикация (требуется аккаунт PyPI)
pip install build twine
python -m build
python -m twine upload dist/*
```

После успешной публикации проверьте установку:

```bash
pip install ErisPulse-MyModule
```

### 3. Отправка в модуль магазина

Перейдите на [страницу модуля магазина ErisPulse](https://www.erisdev.com/#market), нажмите «Submit Module» (Отправить модуль), войдите в систему и заполните информацию о модуле.

Поддерживаемые способы входа: **GitHub**, **Codeberg**, **Cloud Lake** — выберите любой из них.

Ключевые моменты при заполнении:
- Название модуля, описание, адрес репозитория
- Минимальная версия SDK: если не уверены, укажите версию [последнего выпуска ErisPulse](https://pypi.org/project/ErisPulse/)

Сразу после отправки изменения вступают в силу, пользователи могут устанавливать модуль через источники. Модуль будет помечен как «Unverified» (Не проверено), статус изменится на «Verified» (Проверено) после одобрения модераторами.

> **О статусе проверки**:
> - «Unverified» (Не проверено) означает, что модуль еще не проходил официальную проверку, это не означает, что в модуле есть проблемы
> - Пользователи, устанавливающие непроверенные модули через `epsdk install`, увидят предупреждение о рисках и должны подтвердить действие для продолжения

### 4. Управление опубликованными модулями

В модуль магазина нажмите «Submit Module» и войдите в систему, затем переключитесь на вкладку «My Modules» (Мои модули), чтобы можно было:

- **Edit** — изменять описание модуля, адрес репозитория, теги и другую информацию; номер версии будет синхронизирован с PyPI
- **Delete** — удалить модуль из модуля магазина (операцию нельзя отменить)

> Только что отправленные модули могут потребоваться несколько минут для отображения в списке «My Modules».

## Обновление опубликованного модуля

1. Обновите версию в `pyproject.toml`
2. Пересоберите и загрузите снова: `python -m build && python -m twine upload dist/*`
3. Модуль магазина автоматически синхронизирует последнюю версию с PyPI

Пользователи могут обновить модуль через `epsdk upgrade MyModule`.

## Чек-лист перед публикацией

Прежде чем публиковать в PyPI, подтвердите каждый пункт из следующего списка:

### Качество кода

- [ ] У всех публичных API есть типовые аннотации (сигнатуры функций и возвращаемые значения)
- [ ] У всех публичных методов есть документированные строки (формат `"""..."""`, содержащие `:param` / `:return` / `:raises`)
- [ ] Пройден `ruff check` (без предупреждений)
- [ ] Покрытие тестами ≥ 80%
- [ ] Все тесты проходят через `pytest`

### Совместимость

- [ ] В `pyproject.toml` указана минимальная версия SDK: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] Проверена работа с Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] Проверена целевая операционная система (Windows / Linux / macOS, если применимо)
- [ ] Нет циклических зависимостей импорта

### Настройка

- [ ] Если используется декларативная конфигурация (`ConfigClass` + `BaseConfig` / `BotAccountConfig`), у полей конфигурации есть `description` (рекомендуется формат i18n) и метаданные `ui`
- [ ] Если зарегистрированы ключи переводов i18n, все 5 языков (zh-CN / zh-TW / en / ja / ru) покрыты
- [ ] Чувствительные поля помечены как `secret=True`

### Документация

- [ ] В `README.md` есть инструкции по установке и базовые примеры использования
- [ ] В `README.md` описан способ конфигурации (пример конфигурационного файла + переменные окружения)
- [ ] В `CHANGELOG.md` записаны все изменения
- [ ] Адаптер обновил документацию по особенностям платформы (поддерживаемые типы Send, типы событий и т. д.)

### Публикация

- [ ] Номер версии в `pyproject.toml` обновлен
- [ ] Сборка прошла успешно: `python -m build`
- [ ] Загружено в PyPI: `python -m twine upload dist/*`
- [ ] Проверка установки прошла: `pip install ErisPulse-xxx && epsdk run`

## Тестирование в режиме разработки

Прежде чем делать официальную публикацию, вы можете протестировать в режиме редактирования (`editable install`) локально:

```bash
epsdk install -e /path/to/MyModule
# или
pip install -e /path/to/MyModule
```

## Часто задаваемые вопросы

### Обязательно ли имя пакета должно начинаться с `ErisPulse-`?

Не обязательно, но очень рекомендуется. Это помогает пользователям идентифицировать пакеты экосистемы ErisPulse на PyPI.

### Можно ли в одном пакете зарегистрировать несколько модулей?

Да. Просто настройте несколько пар ключ-значение в `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Сколько времени занимает проверка?

Обычно занимает 1-3 рабочих дня. Вы можете отслеживать статус проверки в разделе «My Modules» в модуле магазина.

## Развертывание приложения через Docker-образ

Если ваше приложение не подходит для публикации в PyPI (например, содержит приватные зависимости или требует предварительной настройки среды), вы можете опубликовать Docker-образ через **GitHub Container Registry (GHCR)**, чтобы другие пользователи могли запустить его одной командой `docker pull`.

### Сценарии использования

- У вас есть **полноценное ботовое приложение** (модуль + конфигурация + скрипт запуска), и вы хотите распространять его в одном клике
- Модуль/адаптер зависит от **приватных пакетов** или имеет специальный процесс установки, который не подходит для PyPI
- Хотите предоставить **готовое к использованию** решение развертывания и снизить порог входа для пользователей

### 1. Создание Dockerfile

На основе официального образа ErisPulse нужно только добавить ваш модуль:

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="Описание модуля" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

Если модулю требуются дополнительные системные зависимости (например, SSH-клиент и т. д.), добавьте их после `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> Образ `erispulse/erispulse:latest` уже содержит ErisPulse, ErisPulse-Dashboard, Python runtime и uv, повторная установка не требуется.

### 2. Создание рабочего процесса GitHub Actions

Создайте файл `.github/workflows/docker-publish.yml`:

```yaml
name: Publish Docker Image

on:
  workflow_dispatch:
  push:
    branches:
      - main
    tags:
      - "v*"

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository_owner }}/my-bot

jobs:
  docker-publish:
    runs-on: ubuntu-latest

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up QEMU (для многоархитектурной поддержки)
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

> `GITHUB_TOKEN` предоставляется GitHub Actions автоматически, создание секретных ключей вручную не требуется.

### 3. Запуск сборки

Просто отправьте код или отметьте тегом для автоматической сборки:

```bash
# Отправка в main branch запускает сборку
git push origin main

# Или отметка тегом запускает сборку
git tag v1.0.0
git push origin v1.0.0
```

Вы также можете запустить сборку вручную на странице **Actions** в репозитории GitHub.

### 4. Установка образа как публичного

Образы GHCR по умолчанию имеют статус **private**. Чтобы другие пользователи могли скачивать их без входа, нужно установить образ как публичный:

1. Перейдите в репозиторий → **Packages** → нажмите на соответствующий Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. Использование пользователями

После завершения сборки пользователи могут запустить приложение одной командой:

```bash
docker run -d \
  --name my-bot \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -e TZ=Asia/Shanghai \
  -e ERISPULSE_DASHBOARD_TOKEN=your-token \
  --restart unless-stopped \
  ghcr.io/<your-username>/my-bot:latest
```

Или используйте `docker-compose.yml`:

```yaml
services:
  my-bot:
    image: ghcr.io/<your-username>/my-bot:latest
    container_name: my-bot
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    environment:
      - TZ=Asia/Shanghai
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    restart: unless-stopped
```

### Одновременная публикация в Docker Hub

Расширьте рабочий процесс, добавив вход в Docker Hub перед шагом входа в систему, и добавьте адрес Docker Hub в `images`:

```yaml
      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> Необходимо добавить `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN` в **Secrets** настроек репозитория.

### Docker-образ vs Публикация в PyPI

| Особенность | Docker-образ (GHCR) | Публикация в PyPI |
|------|---------------------|-----------|
| Способ распространения | `docker pull` и запуск в один клик | `pip install` + ручная настройка |
| Область применения | Полноценное приложение/решение | Отдельный модуль/адаптер |
| Приватные зависимости | Естественная поддержка | Требуется приватный PyPI-источник |
| Модуль магазина | Неприменимо | Можно отправить в модуль магазина |
| Мультиархитектура | Поддержка amd64/arm64 | Архитектура не важна |

Оба способа не противоречат друг другу — вы можете одновременно публиковать модули в модуль магазина через PyPI и предоставлять готовые Docker-образы через GHCR.