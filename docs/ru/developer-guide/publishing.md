# Руководство по публикации и магазину модулей

> [!TIP]
> **Когда читать это**: при публикации модуля или адаптера на PyPI / магазин модулей. Если не нужно, пропустите, это не повлияет на использование других функций.

Опубликуйте свой модуль или адаптер в магазине модулей ErisPulse, чтобы другие пользователи могли легко находить и устанавливать его.

## Обзор магазина модулей

Магазин модулей ErisPulse — это централизованный реестр модулей, где пользователи могут просматривать, искать и устанавливать модули и адаптеры, предоставленные сообществом, с помощью инструментов командной строки.

### Просмотр и обнаружение

```bash
# Вывести список всех доступных удалённых пакетов
epsdk list-remote

# Показать только модули
epsdk list-remote -t modules

# Показать только адаптеры
epsdk list-remote -t adapters

# Принудительно обновить список удалённых пакетов
epsdk list-remote -r
```

Вы также можете просматривать магазин модулей онлайн на [официальном сайте ErisPulse](https://www.erisdev.com/#market).

### Поддерживаемые типы публикаций

| Тип | Описание | Группа entry-point |
|------|------|----------------|
| Модуль (Module) | Расширение функциональности бота, реализация бизнес-логики | `erispulse.module` |
| Адаптер (Adapter) | Подключение к новым платформам сообщений | `erispulse.adapter` |

## Быстрая публикация

Весь процесс состоит всего из трёх шагов: настройка проекта → публикация на PyPI → отправка в магазин модулей.

### 1. Настройка pyproject.toml

Убедитесь, что в каталоге проекта есть файлы `pyproject.toml` и `README.md`, и настройте entry-points в зависимости от типа:

#### Модуль

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Описание функциональности модуля"
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
description = "Описание функциональности адаптера"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **Внимание**: Рекомендуется, чтобы имя пакета начиналось с `ErisPulse-`, чтобы пользователи могли легко распознать пакеты экосистемы ErisPulse. Ключ entry-point (например, `"MyModule"`) будет использоваться в качестве имени модуля в SDK.

### 2. Публикация на PyPI

```bash
# Сборка и публикация (требуется аккаунт на PyPI)
pip install build twine
python -m build
python -m twine upload dist/*
```

После успешной публикации проверьте установку:

```bash
pip install ErisPulse-MyModule
```

### 3. Отправка в магазин модулей

Перейдите на [ErisPulse Marketplace](https://www.erisdev.com/#market), нажмите «Добавить модуль», войдите в систему и заполните информацию о модуле.

Поддерживаемые способы входа: **GitHub**, **Codeberg**, **Yunhu**, выберите любой.

Основные пункты заполнения:
- Название модуля, описание, адрес репозитория
- Минимальная версия SDK: если не уверены, введите версию [последнего релиза ErisPulse](https://pypi.org/project/ErisPulse/)

После отправки модуль будет доступен для установки. Модуль будет помечен как «Не проверен», после проверки администратором он станет «Проверен».

> **О статусе проверки**:
> - «Не проверен» означает, что модуль ещё не прошёл официальную проверку, но не обязательно, что в нём есть проблемы
> - При установке не проверенного модуля пользователь получит предупреждение о риске, и ему нужно будет подтвердить установку

### 4. Управление опубликованными модулями

После входа на странице «Добавить модуль» перейдите на вкладку «Мои модули», где вы можете:

- **Редактировать** — изменить описание модуля, адрес репозитория, теги и т. д., номер версии будет автоматически синхронизирован с PyPI
- **Удалить** — удалить модуль из магазина модулей (необратимо)

> Новый модуль может появиться в списке «Мои модули» через несколько минут.

## Обновление опубликованного модуля

1. Обновите `version` в `pyproject.toml`
2. Пересоберите и перезагрузите: `python -m build && python -m twine upload dist/*`
3. Магазин модулей будет автоматически синхронизировать новую версию с PyPI

Пользователи могут обновить модуль с помощью `epsdk upgrade MyModule`.

## Проверочный список перед публикацией

Перед отправкой на PyPI, проверьте следующие пункты:

### Качество кода

- [ ] Все публичные API имеют аннотации типов (подписи и возвращаемые значения функций)
- [ ] Все публичные методы имеют строку документации (`"""..."""` формат, включая `:param` / `:return` / `:raises`)
- [ ] Проходит проверку `ruff check` (без предупреждений)
- [ ] Крытие тестами ≥ 80%
- [ ] Проходит все тесты `pytest`

### Совместимость

- [ ] `pyproject.toml` объявляет минимальную версию SDK: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] В `get_meta()` методе `ModuleMeta(min_sdk_version="x.y.z")` объявлен минимальный SDK для запуска (для адаптеров используется атрибут класса `min_sdk_version`) — если SDK в пользовательской среде слишком старый, фреймворк будет явно сообщать об ошибке и пропускать модуль, а не генерировать трудно отслеживаемые исключения во время выполнения
- [ ] Протестировано на Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] Протестировано на целевой операционной системе (Windows / Linux / macOS, если применимо)
- [ ] Отсутствуют циклические зависимости

### Конфигурация

- [ ] Если используется декларативная конфигурация (`ConfigClass` + `BaseConfig` / `BotAccountConfig`), поля конфигурации имеют `description` (рекомендуется в формате i18n) и метаданные `ui`
- [ ] Если зарегистрированы ключи переводов i18n, они покрывают все 5 языков (zh-CN / zh-TW / en / ja / ru)
- [ ] Чувствительные поля помечены `secret=True`

### Документация

- [ ] `README.md` содержит инструкции по установке и примеры использования
- [ ] `README.md` объясняет способ конфигурации (примеры конфигурационного файла + переменные окружения)
- [ ] `CHANGELOG.md` содержит все изменения
- [ ] Адаптер обновил документацию по функциональности платформы (поддерживаемые типы Send, типы событий и т. д.)

### Публикация

- [ ] Номер версии в `pyproject.toml` обновлён
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

### Обязательно ли имя пакета должно начинаться с `ErisPulse-`?

Нет, не обязательно, но настоятельно рекомендуется. Это поможет пользователям легко распознавать пакеты экосистемы ErisPulse на PyPI.

### Можно ли зарегистрировать несколько модулей в одном пакете?

Да. В `entry-points` можно зарегистрировать несколько ключей:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Сколько времени занимает проверка?

Обычно 1–3 рабочих дня. Вы можете проверить статус проверки в магазине модулей в разделе «Мои модули».

## Распространение приложений через Docker-образы

Если ваше приложение не подходит для публикации на PyPI (например, содержит приватные зависимости или требует предварительной настройки окружения), вы можете опубликовать Docker-образ через **GitHub Container Registry (GHCR)**, чтобы другие пользователи могли запускать его с помощью `docker pull`.

### Сценарии использования

- У вас есть **полное приложение бота** (модуль + конфигурация + скрипт запуска), которое вы хотите распространять одним кликом
- Модуль/адаптер зависит от **приватных пакетов** или имеет специальный процесс установки, непригодный для PyPI
- Вы хотите предоставить **готовое решение для развертывания**, чтобы снизить порог входа для пользователей

### 1. Создание Dockerfile

Основываясь на официальном образе ErisPulse, добавьте ваш модуль:

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

Если модулю нужны дополнительные системные зависимости (например, клиент SSH), добавьте их после `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` уже содержит ErisPulse, ErisPulse-Dashboard, Python-интерпретатор и uv, их не нужно устанавливать повторно.

### 2. Создание GitHub Actions workflow

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

По умолчанию образы GHCR являются **private**, их нужно сделать Public, чтобы другие пользователи могли получать их без входа:

1. Перейдите в репозиторий → **Packages** → нажмите на соответствующий пакет
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. Использование пользователем

После завершения сборки пользователь может запустить образ одной командой:

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

### Публикация на Docker Hub

Расширьте workflow, добавив вход в Docker Hub перед шагом входа в GHCR, и укажите Docker Hub в `images`:

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

### Docker-образы (GHCR) vs PyPI

| Характеристика | Docker-образ (GHCR) | Публикация на PyPI |
|------|---------------------|-----------|
| Способ распространения | `docker pull` — запуск одним кликом | `pip install` + ручная настройка |
| Область применения | Полное приложение/решение | Отдельный модуль/адаптер |
| Приватные зависимости | Поддерживается по умолчанию | Требуется приватный PyPI |
| Магазин модулей | Не поддерживается | Можно отправить в магазин модулей |
| Многие архитектуры | Поддерживает amd64/arm64 | Независим от архитектуры |

Эти два способа не исключают друг друга — вы можете одновременно публиковать модуль на PyPI в магазине модулей и предоставлять готовый Docker-образ через GHCR.

## Далее

### Убедитесь в качестве перед публикацией

- [Модульные тесты (ErisPulse-Testing)](testing.md) — запустите автоматические тесты, чтобы проверить контрольный список
- [Лучшие практики модулей](modules/best-practices.md) / [Лучшие практики адаптеров](adapters/best-practices.md) — завершите инженерную часть перед публикацией

### Публикация и использование пользователями

- [Команды CLI](../user-guide/cli-reference.md) — поведение пользователей `epsdk install` / `epsdk upgrade`
- [Руководство по функциональности платформы](../platform-guide/README.md) — документация адаптера для авторов