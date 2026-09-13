# Руководство по публикации и магазину модулей

Публикуйте свои разработанные модули или адаптеры в магазине модулей ErisPulse, чтобы другие пользователи могли легко находить и устанавливать их.

## Обзор магазина модулей

Магазин модулей ErisPulse — это централизованная регистрация модулей, через которую пользователи могут просматривать, искать и устанавливать модули и адаптеры, предоставленные сообществом, с помощью инструмента командной строки (CLI).

### Просмотр и обнаружение

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

Вы также можете просматривать магазин модулей онлайн на [официальном сайте ErisPulse](https://www.erisdev.com/#market).

### Поддерживаемые типы отправки

| Тип | Описание | Группа entry-point |
|------|------|----------------|
| Модуль (Module) | Расширение функциональности бота, реализация бизнес-логики | `erispulse.module` |
| Адаптер (Adapter) | Подключение к новым платформам сообщений | `erispulse.adapter` |

## Быстрая публикация

Весь процесс состоит из трех шагов: настройка проекта → публикация на PyPI → отправка в магазин модулей.

### 1. Настройка pyproject.toml

Убедитесь, что в директории проекта присутствуют `pyproject.toml` и `README.md`, и настройте entry-points в зависимости от типа:

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

> **Примечание**: Рекомендуется начинать имя пакета с `ErisPulse-`, чтобы пользователи могли легко его распознать. Ключ entry-point (например, `"MyModule"`) будет использоваться как имя модуля в SDK.

### 2. Публикация на PyPI

```bash
# Сборка + публикация (требуется учетная запись PyPI)
pip install build twine
python -m build
python -m twine upload dist/*
```

После успешной публикации проверьте установку:

```bash
pip install ErisPulse-MyModule
```

### 3. Отправка в магазин модулей

Перейдите на [магазин модулей ErisPulse](https://www.erisdev.com/#market), нажмите «Отправить модуль», войдите в систему и заполните информацию о модуле.

Поддерживаемые способы входа: **GitHub**, **Codeberg**, **Yunhu**, выберите любой из них.

Заполните следующие пункты:
- Название модуля, описание, адрес репозитория
- Минимальная версия SDK: если не уверены, укажите версию [последнего релиза ErisPulse](https://pypi.org/project/ErisPulse/)

После отправки модуль будет доступен для установки через источник модулей. Модуль будет помечен как «Не проверено», после проверки администратором он изменится на «Проверено».

> **О статусе проверки**:
> - «Не проверено» означает, что модуль еще не прошел официальную проверку, но это не говорит о наличии ошибок
> - При установке модуля, помеченного как «Не проверено», пользователь получит предупреждение о риске, и ему нужно будет подтвердить установку

### 4. Управление опубликованным модулем

После входа в систему на вкладке «Мои модули» в магазине модулей вы можете:

- **Редактировать** — изменить описание модуля, адрес репозитория, теги и т.д., версия будет автоматически синхронизирована с PyPI
- **Удалить** — удалить модуль из магазина модулей (невозможно отменить)

> Модуль, только что отправленный, может потребоваться несколько минут, чтобы появиться в списке «Мои модули».

## Обновление опубликованного модуля

1. Обновите `version` в `pyproject.toml`
2. Пересоберите и перезагрузите: `python -m build && python -m twine upload dist/*`
3. Магазин модулей автоматически синхронизирует последнюю версию с PyPI

Пользователи могут обновить модуль с помощью `epsdk upgrade MyModule`.

## Список проверки перед публикацией

Перед отправкой на PyPI, проверьте следующие пункты:

### Качество кода

- [ ] Все публичные API имеют аннотации типов (подписи функций и возвращаемые значения)
- [ ] Все публичные методы имеют строку документации (`"""..."""` формат, включая `:param` / `:return` / `:raises`)
- [ ] Прошел проверку `ruff check` (без предупреждений)
- [ ] Крылья тестов ≥ 80%
- [ ] Прошел все тесты `pytest`

### Совместимость

- [ ] `pyproject.toml` объявил минимальную версию SDK: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] Модуль объявил минимальную версию SDK во время выполнения в `get_meta()` с помощью `ModuleMeta(min_sdk_version="x.y.z")` (для адаптеров используется атрибут класса `min_sdk_version`) — если версия SDK пользователя слишком низкая, фреймворк сообщит об ошибке при загрузке и пропустит модуль, а не выдаст трудноотслеживаемые исключения во время выполнения
- [ ] Тестировался на Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] Тестировался на целевой операционной системе (Windows / Linux / macOS, если применимо)
- [ ] Нет циклических зависимостей

### Конфигурация

- [ ] Если используется декларативная конфигурация (`ConfigClass` + `BaseConfig` / `BotAccountConfig`), поля конфигурации имеют `description` (рекомендуется формат i18n) и метаданные `ui`
- [ ] Если зарегистрированы ключи перевода i18n, обеспечено покрытие всех 5 языков (zh-CN / zh-TW / en / ja / ru)
- [ ] Чувствительные поля помечены `secret=True`

### Документация

- [ ] `README.md` содержит инструкции по установке и примеры базового использования
- [ ] `README.md` объясняет способ конфигурации (пример файла конфигурации + переменные среды)
- [ ] `CHANGELOG.md` содержит все изменения
- [ ] Адаптер обновил документацию по функциональности платформы (поддерживаемые типы Send, типы событий и т.д.)

### Публикация

- [ ] `pyproject.toml` версия обновлена
- [ ] Сборка прошла успешно: `python -m build`
- [ ] Загружен на PyPI: `python -m twine upload dist/*`
- [ ] Установка проверена: `pip install ErisPulse-xxx && epsdk run`

## Тестирование в режиме разработки

Перед публикацией можно использовать режим редактирования для локального тестирования:

```bash
epsdk install -e /path/to/MyModule
# или
pip install -e /path/to/MyModule
```

## Часто задаваемые вопросы

### Имя пакета должно начинаться с `ErisPulse-`?

Нет, это не обязательно, но настоятельно рекомендуется. Это помогает пользователям распознавать пакеты экосистемы ErisPulse на PyPI.

### Один пакет может зарегистрировать несколько модулей?

Да. В `entry-points` можно указать несколько пар ключ-значение:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Сколько времени занимает проверка?

Обычно это занимает 1-3 рабочих дня. Вы можете проверить статус проверки в магазине модулей на вкладке «Мои модули».

## Распространение приложений через Docker-образы

Если ваше приложение не подходит для публикации на PyPI (например, содержит частные зависимости или требует предварительной настройки среды), вы можете опубликовать Docker-образ через **GitHub Container Registry (GHCR)**, чтобы другие пользователи могли запускать его с помощью `docker pull`.

### Сценарии использования

- У вас есть **полное приложение-бот** (модуль + конфигурация + скрипт запуска), которое вы хотите распространять одним кликом
- Модуль/адаптер зависит от **приватных пакетов** или имеет специальный процесс установки, который не подходит для PyPI
- Вы хотите предоставить **готовое к использованию** решение для развертывания, чтобы снизить порог входа для пользователей

### 1. Создание Dockerfile

На основе официального образа ErisPulse создайте Dockerfile, добавив только ваш модуль:

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

Если модулю требуются дополнительные системные зависимости (например, клиент SSH), добавьте их после `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` уже содержит ErisPulse, ErisPulse-Dashboard, среду выполнения Python и uv, повторная установка не требуется.

### 2. Создание рабочего потока GitHub Actions

Создайте файл `.github/workflows/docker-publish.yml`:

```yaml
name: Публикация Docker-образа

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
      - name: Клонирование кода
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

      - name: Сборка и отправка Docker-образа
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

> `GITHUB_TOKEN` предоставляется автоматически GitHub Actions, не нужно создавать ключ вручную.

### 3. Запуск сборки

Сборка запускается при отправке кода или создании тега:

```bash
# Отправка на ветку main запускает сборку
git push origin main

# Или создание тега запускает сборку
git tag v1.0.0
git push origin v1.0.0
```

Также можно запустить вручную на странице **Actions** репозитория.

### 4. Настройка образа как публичного

По умолчанию образы GHCR являются **private**, их нужно настроить как Public, чтобы другие пользователи могли получать их без входа:

1. Перейдите в репозиторий → **Packages** → нажмите на соответствующий пакет
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. Использование пользователем

После завершения сборки пользователь может запустить образ одной командой `docker run`:

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

Или с помощью `docker-compose.yml`:

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

### Одновременная публикация на Docker Hub

Расширьте рабочий поток, добавив вход в Docker Hub перед входом в GHCR, и укажите Docker Hub в `images`:

```yaml
      - name: Вход в Docker Hub
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Извлечение Docker-метаданных
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> Необходимо добавить `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN` в **Settings → Secrets** репозитория.

### Docker-образ vs PyPI-публикация

| Характеристика | Docker-образ (GHCR) | PyPI-публикация |
|------|---------------------|-----------|
| Способ распространения | `docker pull` для запуска | `pip install` + ручная настройка |
| Область применения | Полное приложение/решение | Отдельный модуль/адаптер |
| Частные зависимости | Поддерживается нативно | Требует частного PyPI-источника |
| Магазин модулей | Не применимо | Можно отправить в магазин модулей |
| Многоархитектурность | Поддерживает amd64/arm64 | Независим от архитектуры |

Оба способа не исключают друг друга — вы можете одновременно публиковать модуль на PyPI в магазине модулей и предоставлять готовый к использованию Docker-образ через GHCR.