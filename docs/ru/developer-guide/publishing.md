# Руководство по публикации и магазину модулей

> [!TIP]
> **Когда читать этот документ**: при публикации вашей работы на PyPI / в магазин модулей. Если это не требуется, пропустите — это не повлияет на использование других функций.

Опубликуйте разработанные вами модули или адаптеры в магазине модулей ErisPulse, чтобы другие пользователи могли легко находить и устанавливать их.

## Обзор магазина модулей

Магазин модулей ErisPulse представляет собой централизованный реестр модулей, где пользователи могут просматривать, искать и устанавливать модули и адаптеры, предоставленные сообществом, с помощью инструментов командной строки.

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

Вы также можете посетить [официальный сайт ErisPulse](https://www.erisdev.com/#market) или раздел «Список модулей» в [ErisPulse Workbench](https://workbench.erisdev.com/), чтобы просмотреть магазин модулей онлайн. Все функции управления аккаунтом, модулями и доменами хостинга в Workbench описаны в [ErisPulse Workbench](../ecosystem/workbench.md).

### Поддерживаемые типы публикаций

| Тип | Описание | Группа Entry-point |
|------|------|----------------|
| Модуль (Module) | Расширение функциональности бота, реализация бизнес-логики | `erispulse.module` |
| Адаптер (Adapter) | Подключение к новым платформам сообщений | `erispulse.adapter` |

## Быстрый публикационный процесс

Весь процесс состоит всего из трех шагов: настройка проекта → публикация на PyPI → отправка в магазин модулей.

### 1. Настройка pyproject.toml

Убедитесь, что в директории проекта присутствуют файлы `pyproject.toml` и `README.md`, а также настройте entry-points в зависимости от типа:

#### Модуль

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

#### Адаптер

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "Описание функционала адаптера"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **Важно**: Рекомендуется начинать имя пакета с префикса `ErisPulse-`, чтобы пользователи могли легко его распознать. Ключи entry-point (например, `"MyModule"`) будут использоваться как имена модуля в SDK.

### 2. Публикация на PyPI

```bash
# Сборка + публикация (требуется аккаунт PyPI)
pip install build twine
python -m build
python -m twine upload dist/*
```

После успешной публикации проверьте установку:

```bash
pip install ErisPulse-MyModule
```

### 3. Отправка в магазин модулей (ErisPulse Workbench)

Все модули и сертификации объединены в системе **ErisPulse Workbench**: **[https://workbench.erisdev.com/](https://workbench.erisdev.com/)**. После отправки модуль будет опубликован в индексе через `repository_dispatch`, после чего workflow завершится и модуль появится в магазине (обычно это занимает несколько минут). Подробности о входе в работу, токенах, привязке и доменах хостинга см. в [ErisPulse Workbench](../ecosystem/workbench.md).

#### Способ 1: Отправка через веб-интерфейс (рекомендуется для первого использования)

1. Откройте рабочую платформу и войдите с помощью аккаунта **GitHub / Codeberg** (в старых версиях модулей можно найти «Привязать этот модуль» на странице деталей модуля).
2. Слева выберите «Отправить новый модуль» → заполните форму: имя / тип (module · adapter) / имя пакета на PyPI / описание (не менее 10 символов) / автор / ссылка на репозиторий (github.com или codeberg.org) / категория (1 Инструменты · 2 Развлечения · 3 Управление · 4 Уведомления · 5 ИИ · 6 Платформа · 7 Анализ) / теги / минимальная версия SDK.
3. После отправки модуль появится и будет помечен как «не проверен» (это означает, что официальная проверка еще не проведена, и при установке пользователи получат предупреждение о риске, которое нужно подтвердить); после прохождения «сертификационной проверки» статус изменится на «проверен».

#### Способ 2: Автоматическая отправка через API (для CLI / CI-сценариев)

**① Создание токена доступа**: на странице «Открытые интерфейсы → Токены доступа» в рабочей платформе → введите имя → нажмите «Создать токен». Формат токена: `epat_` + 40 шестнадцатеричных цифр, **показывается только при создании**; для аккаунтов с включенной двухфакторной аутентификацией можно поставить галочку «Без динамического кода», после чего для чувствительных интерфейсов больше не потребуется `totp_code`.

**② Правила вызова**:

```http
Authorization: Bearer epat_…
Content-Type: application/json
```

Тело запроса должно быть в кодировке **UTF-8**. В терминале Windows по умолчанию используется GBK, и китайские символы будут записаны в байтах, отличных от UTF-8, что приведет к отклонению сервером (ошибка `415 ENCODING_INVALID` и указание на проблемное поле) — сначала выполните `chcp 65001`, или сохраните тело запроса в файле UTF-8 и отправьте с помощью `curl --data-binary @body.json`.

**③ Отправка модуля**:

```bash
curl -X POST https://workbench.erisdev.com/api/modules/submit \
  -H "Authorization: Bearer epat_…" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyModule",
    "type": "module",
    "package": "ErisPulse-MyModule",
    "description": "Описание модуля, не менее 10 символов",
    "author": "Your Name",
    "repository": "https://github.com/you/MyModule",
    "category": 1,
    "tags": ["Инструменты"],
    "i18n": ["zh", "en"],
    "min_sdk_version": ">=2.7.0"
  }'
```

**④ Просмотр и управление**: `GET /api/modules/ops?name=MyModule&type=module` для проверки статуса отправки и проверки; `POST /api/modules/manage` для редактирования / подтверждения / удаления; `POST /api/modules/batch` для массовых операций. Полный список эндпоинтов см. в встроенном «Документе по использованию» рабочей платформы (токены / привязка / управление модулями / FAQ).

### 4. Управление опубликованными модулями

Войдите в рабочую платформу → «Список модулей» → на странице деталей своего модуля можно редактировать описание, репозиторий, теги и т.д. (номер версии автоматически синхронизируется с PyPI), удалить модуль, начать процесс привязки; в API используйте эндпоинты `manage` / `batch`.

> Новый отправленный модуль может появиться в списке через несколько минут.

## Обновление опубликованного модуля

1. Обновите `version` в `pyproject.toml`
2. Пересоберите и загрузите: `python -m build && python -m twine upload dist/*`
3. Магазин модулей автоматически синхронизирует последнюю версию с PyPI

Пользователи могут обновиться с помощью `epsdk upgrade MyModule`.

## Чек-лист перед публикацией

Перед публикацией на PyPI проверьте по пунктам следующее:

### Качество кода

- [ ] Все публичные API имеют аннотации типов (сигнатуры функций и возвращаемые значения)
- [ ] Все публичные методы имеют docstring (формат `"""..."""` с `:param` / `:return` / `:raises`)
- [ ] Пройден `ruff check` (без предупреждений)
- [ ] Покрытие тестами ≥ 80%
- [ ] Все тесты в `pytest` пройдены успешно

### Совместимость

- [ ] В `pyproject.toml` объявлена минимальная версия SDK: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] Модуль объявляет минимальную версию SDK во время выполнения через `ModuleMeta(min_sdk_version="x.y.z")` в `get_meta()` (для адаптеров — атрибут класса `min_sdk_version`) — если версия SDK в окружении пользователя слишком низкая, фреймворк на этапе загрузки выдаст понятную ошибку и пропустит модуль, а не вызовет трудноотслеживаемое исключение во время выполнения
- [ ] Протестировано на Python 3.10 / 3.11 / 3.12 / 3.13
- [ ] Протестировано на целевых ОС (Windows / Linux / macOS, если применимо)
- [ ] Отсутствуют циклические импорты

### Конфигурация

- [ ] Если используется декларативная конфигурация (`ConfigClass` + `BaseConfig` / `BotAccountConfig`), поля конфигурации имеют `description` (рекомендуется формат i18n) и метаданные `ui`
- [ ] Если зарегистрированы ключи i18n-переводов, они покрыты для всех 5 языков (zh-CN / zh-TW / en / ja / ru)
- [ ] Чувствительные поля помечены `secret=True`

### Документация

- [ ] В `README.md` есть инструкции по установке и базовые примеры использования
- [ ] В `README.md` описан способ конфигурации (пример конфигурационного файла + переменные окружения)
- [ ] В `CHANGELOG.md` зафиксированы все изменения
- [ ] Для адаптера обновлена документация по возможностям платформы (поддерживаемые типы Send, типы событий и т.д.)

### Публикация

- [ ] Номер версии в `pyproject.toml` обновлён
- [ ] Сборка прошла успешно: `python -m build`
- [ ] Загружено на PyPI: `python -m twine upload dist/*`
- [ ] Проверка установки пройдена: `pip install ErisPulse-xxx && epsdk run`

## Тестирование в режиме разработки

Перед официальной публикацией можно протестировать локально в режиме редактируемой установки (editable):

```bash
epsdk install -e /path/to/MyModule
# или
pip install -e /path/to/MyModule
```

## Часто задаваемые вопросы

### Должно ли имя пакета начинаться с `ErisPulse-`?

Это не обязательно, но настоятельно рекомендуется. Это помогает пользователям находить пакеты экосистемы ErisPulse на PyPI.

### Может ли один пакет регистрировать несколько модулей?

Да. Достаточно настроить несколько пар «ключ–значение» в `entry-points`:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### Сколько времени занимает проверка?

Обычно проверка завершается в течение 1–3 рабочих дней. Статус верификации можно посмотреть в магазине модулей в разделе «Мои модули».

## Распространение приложений через Docker-образы

Если ваше приложение не подходит для публикации на PyPI (например, содержит приватные зависимости или требует преднастроенное окружение), можно опубликовать Docker-образ через **GitHub Container Registry (GHCR)**, чтобы другие пользователи могли запустить его одной командой `docker pull`.

### Сценарии применения

- У вас есть **полноценное бот-приложение** (модуль + конфигурация + входной скрипт), которое вы хотите распространять одним действием
- Модуль/адаптер зависит от **приватных пакетов** или имеет особый процесс установки, что не подходит для PyPI
- Вы хотите предоставить решение для развёртывания **«из коробки»**, снизив порог входа для пользователей

### 1. Создание Dockerfile

Соберите образ на базе официального образа ErisPulse, добавив лишь ваш модуль:

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

Если модулю требуются дополнительные системные зависимости (например, SSH-клиент), добавьте после `RUN uv pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` уже содержит ErisPulse, ErisPulse-Dashboard, среду выполнения Python и uv, повторная установка не требуется.

### 2. Создание workflow для GitHub Actions

Создайте в `.github/workflows/docker-publish.yml`:

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
      - name: Извлечение кода
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

      - name: Сборка и публикация Docker-образа
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

> `GITHUB_TOKEN` предоставляется автоматически GitHub Actions, создавать секрет вручную не нужно.

### 3. Запуск сборки

Сборка запускается автоматически при отправке кода или создании тега:

```bash
# Запуск при отправке в ветку main
git push origin main

# Или запуск при создании тега
git tag v1.0.0
git push origin v1.0.0
```

Также можно запустить вручную на странице **Actions** репозитория GitHub.

### 4. Установка образа как публичного

Образы в GHCR по умолчанию **приватные (private)**; чтобы другие пользователи могли скачивать их без авторизации, нужно установить Public в настройках GitHub:

1. Перейдите в репозиторий → **Packages** → нажмите на соответствующий Package
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. Использование пользователями

После завершения сборки пользователи могут запустить образ одной командой `docker run`:

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

Расширьте workflow, добавив вход в Docker Hub перед шагом авторизации, и добавьте адрес Docker Hub в `images`:

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
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> Необходимо добавить `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN` в **Settings → Secrets** репозитория.

### Docker-образ vs публикация на PyPI

| Характеристика | Docker-образ (GHCR) | Публикация на PyPI |
|------|---------------------|-----------|
| Способ распространения | Запуск одной командой `docker pull` | `pip install` + ручная настройка |
| Область применения | Полные приложения/решения | Отдельные модули/адаптеры |
| Приватные зависимости | Поддерживаются естественно | Требуется приватный PyPI-репозиторий |
| Магазин модулей | Неприменимо | Можно отправить в магазин модулей |
| Мультиархитектурность | Поддержка amd64/arm64 | Независимо от архитектуры |

Эти два способа не противоречат друг другу — вы можете одновременно публиковать модули через PyPI в магазин модулей и предоставлять готовые к использованию Docker-образы через GHCR.

## Что дальше

### Проверка качества перед публикацией

- [Тестирование модулей (ErisPulse-Testing)](testing.md) — прогоните приведённый выше чек-лист с помощью автоматизированных тестов
- [Лучшие практики модулей](modules/best-practices.md) / [Лучшие практики адаптеров](adapters/best-practices.md) — финальная инженерная подготовка перед публикацией

### После публикации: помогите пользователям начать работу

- [Команды CLI](../user-guide/cli-reference.md) — поведение `epsdk install` / `epsdk upgrade` на стороне пользователя
- [Руководство по возможностям платформ](../platform-guide/README.md) — куда авторам адаптеров помещать документацию по платформам