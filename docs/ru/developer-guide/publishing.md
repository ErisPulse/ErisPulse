# Руководство по публикации и модулю магазина

Опубликуйте разработанные вами модули или адаптеры в магазине модулей ErisPulse, чтобы другие пользователи могли легко обнаружить и установить их.

## Обзор модуля магазина

Магазин модулей ErisPulse — это централизованный реестр модулей, через который пользователи могут просматривать, искать и устанавливать модули и адаптеры, внесенные сообществом, с помощью инструмента CLI.

### Просмотр и поиск

```bash
# Вывести список всех доступных удаленных пакетов
epsdk list-remote

# Показать только модули
epsdk list-remote -t modules

# Показать только адаптеры
epsdk list-remote -t adapters

# Принудительно обновить список удаленных пакетов
epsdk list-remote -r
```

Вы также можете посетить [Сайт ErisPulse](https://www.erisdev.com/#market), чтобы просмотреть магазин модулей онлайн.

### Поддерживаемые типы (Submission types)

| Тип (Type) | Описание | Группа Entry-point |
|------------|----------|-------------------|
| Модуль (Module) | Расширение функционала бота, реализация бизнес-логики | `erispulse.module` |
| Адаптер (Adapter) | Подключение новых платформ обмена сообщениями | `erispulse.adapter` |

## Быстрая публикация

Весь процесс занимает всего три шага: настройка проекта → публикация на PyPI → отправка в магазин модулей.

### 1. Настройка pyproject.toml

Убедитесь, что в каталоге проекта есть файлы `pyproject.toml` и `README.md`, и настройте entry-points в соответствии с типом:

#### Модуль (Module)

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Описание функционала модуля"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### Адаптер (Adapter)

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "Описание функционала адаптера"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **Примечание**: Рекомендуется, чтобы имя пакета начиналось с `ErisPulse-`, чтобы пользователи могли легко его идентифицировать. Имя ключа точки входа (например, `"MyModule"`) будет использоваться как имя модуля для доступа к нему в SDK.

### 2. Публикация на PyPI

```bash
# Сборка + публикация (требуется аккаунт PyPI)
pip install build twine
python -m build
python -m twine upload dist/*
```

Проверьте установку после успешной публикации:

```bash
pip install ErisPulse-MyModule
```

### 3. Отправка в магазин модулей

Перейдите в [Магазин модулей ErisPulse](https://www.erisdev.com/#market), нажмите «Отправить модуль», введите информацию о модуле после входа в систему.

Доступные методы входа: **GitHub**, **Codeberg**, **Cloud Lake** (выберите один).

Основные моменты:
- Имя модуля, описание, адрес репозитория
- Минимальная версия SDK: если не уверены, введите номер версии [последнего релиза ErisPulse](https://pypi.org/project/ErisPulse/) 

Действует сразу после отправки; пользователи могут установить через источник модулей. Модуль помечается как «Неверифицированный», и статус меняется на «Верифицированный» после утверждения модератором.

> **О статусе верификации**:
> - «Неверифицированный» означает только, что он еще не прошел официальную проверку, это не означает, что в модуле есть проблемы
> - Пользователи будут получать предупреждение о рисках при установке неверифицированного модуля через `epsdk install`, и только после подтверждения смогут продолжить установку

### 4. Управление опубликованными модулями

В магазине модулей нажмите «Отправить модуль» и войдите в систему, чтобы перейти на вкладку «Мои модули», где вы можете:

- **Редактировать** — изменить описание модуля, адрес репозитория, теги и другую информацию; номер версии будет синхронизироваться с PyPI автоматически
- **Удалить** — удалить модуль из магазина модулей (необратимо)

> Только что отправленный модуль может потребоваться несколько минут для отображения в списке «Мои модули».

## Обновление опубликованных модулей

1. Обновите `version` в `pyproject.toml`
2. Повторно соберите и загрузите: `python -m build && python -m twine upload dist/*`
3. Магазин модулей автоматически синхронизирует последнюю версию с PyPI

Пользователи могут обновить модуль через `epsdk upgrade MyModule`.

## Тестирование в режиме разработки

Перед официальным релизом вы можете протестировать в локальной среде в режиме редактирования (editable mode):

```bash
epsdk install -e /path/to/MyModule
# или
pip install -e /path/to/MyModule
```

## Часто задаваемые вопросы

### Имя пакола должно начинаться с `ErisPulse-`?

Не обязательно, но настоятельно рекомендуется. Это помогает пользователям идентифицировать пакеты экосистемы ErisPulse на PyPI.

### Можно ли зарегистрировать несколько модулей в одном пакете?

Да. Просто настройте несколько пар ключ-значение в `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Как долго длится проверка?

Обычно занимает 1-3 рабочих дня. Вы можете проверить статус верификации в разделе «Мои модули» магазина модулей.

## Распространение приложений через образ Docker

Если ваше приложение не подходит для публикации на PyPI (например, содержит частные зависимости или требует предварительной настройки окружения), вы можете опубликовать образ Docker через **GitHub Container Registry (GHCR)**, чтобы другие пользователи могли выполнить `docker pull` для быстрого запуска.

### Сценарии использования

- У вас есть **полноценное приложение бота** (модуль + конфигурация + скрипт запуска), которое вы хотите распространить одним нажатием
- Модули/адаптеры зависят от **частных пакетов** или имеют особый процесс установки, что неудобно для PyPI
- Вы хотите предоставить решение **«готовое к запуску»**, чтобы снизить порог входа для пользователей

### 1. Создание Dockerfile

Создайте на основе официального образа ErisPulse, просто добавив ваш модуль:

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

Если модулю требуются дополнительные системные зависимости (например, SSH-клиент и т.д.), добавьте их после `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` уже включает ErisPulse, ErisPulse-Dashboard, Python runtime и uv, повторная установка не требуется.

### 2. Создание workflow в GitHub Actions

Создайте файл `.github/workflows/docker-publish.yml`:

```yaml
name: Публикация образа Docker

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
      - name: Проверка кода
        uses: actions/checkout@v4

      - name: Настройка QEMU (поддержка нескольких архитектур)
        uses: docker/setup-qemu-action@v3

      - name: Настройка Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Вход в GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Извлечение метаданных Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Сборка и публикация образа Docker
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

> `GITHUB_TOKEN` автоматически предоставляется GitHub Actions, создавать секрет вручную не требуется.

### 3. Запуск сборки

Успешная отправка кода или тегов автоматически запустит сборку:

```bash
# Отправить в main для запуска
git push origin main

# Или создать тег для запуска
git tag v1.0.0
git push origin v1.0.0
```

Также можно запустить сборку вручную на странице **Actions** репозитория GitHub.

### 4. Сделание образа публичным

Образы GHCR по умолчанию имеют статус **private**, чтобы другие пользователи могли скачивать их без входа в систему, нужно сделать их **Public** в настройках GitHub:

1. Перейдите в репозиторий → **Packages** → нажмите на соответствующий Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. Использование пользователем

После сборки пользователь может запустить все в одну строку с помощью `docker run`:

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

Или использовать `docker-compose.yml`:

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

### Публикация одновременно в Docker Hub

Расширьте workflow, добавив вход в Docker Hub перед шагом входа, и добавьте адрес Docker Hub в секцию `images`:

```yaml
      - name: Вход в Docker Hub
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Извлечение метаданных Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github