# Руководство по развертыванию

Лучшие практики развертывания бота ErisPulse в рабочей среде.

## Docker-развертывание (рекомендуется)

ErisPulse предоставляет официальный образ Docker, включающий фреймворк ErisPulse и панель управления Dashboard, поддерживающий архитектуры `linux/amd64` и `linux/arm64`.

### Быстрый старт

```bash
# Скачивание образа
docker pull erispulse/erispulse:latest

# Скачивание docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Установка токена доступа к Dashboard и запуск
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

После запуска перейдите по адресу `http://localhost:8000/Dashboard` и войдите, используя установленный токен в качестве пароля.

### Ускорение загрузки образов в Китае

Если Docker Hub недоступен, можно использовать GitHub Container Registry для загрузки образа:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

При использовании образа ghcr.io необходимо изменить параметр image в файле `docker-compose.yml`:

```yaml
services:
  erispulse:
    image: ghcr.io/erispulse/erispulse:latest
```

### docker-compose.yml

```yaml
services:
  erispulse:
    image: erispulse/erispulse:latest
    container_name: erispulse
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
      # Объединение каталога пакетов Python
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    stop_grace_period: 30s
    restart: unless-stopped
```

> Рекомендуется использовать файл [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) из корня репозитория, он содержит вышеуказанные настройки, а также проверки на работоспособность, переменные окружения часового пояса и языка.

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Порт для Dashboard |
| `ERISPULSE_DASHBOARD_TOKEN` | 自动生成 | Токен доступа к Dashboard (рекомендуется установить) |
| `TZ` | `Asia/Shanghai` | Часовой пояс |
| `LANG` | `en_US.UTF-8` | Язык системы, автоматически определяется для интерфейса запуска |
| `ERISPULSE_LANG` | пусто | Принудительный язык интерфейса запуска: `zh` / `zh_TW` / `en` / `ja` / `ru` (переопределяет `LANG`) |

### Хранение данных

Каталог `./config` смонтирован для хранения конфигурационных файлов и базы данных, включая:

- `config/config.toml` — конфигурационный файл
- `config/config.db` — база данных SQLite
- `config/.packages` — каталог site-packages Python, сохраняющий фреймворк, адаптеры и установленные модули (в первый запуск инициализируется автоматически из резервной копии внутри образа, последующие установки модулей и горячие обновления фреймворка записываются в этот каталог)

> **Обновление фреймворка (включая pre/rc) и самовосстановление образа**: точка входа выполняет автоматическую проверку целостности основных пакетов при каждом запуске контейнера,
> при повреждении пакетов восстанавливает их на основе установленных пользователем версий,
> поврежденные пакеты, установленные вручную (например, предварительные версии, установленные через Dashboard), переустанавливаются из PyPI **в той же версии**, без тихого возврата к версии внутри образа. Таким образом, после обновления фреймворка через Dashboard, при любом перезапуске контейнера будет сохранена целевая версия.

## Панель управления Dashboard

В Docker-образе ErisPulse встроен модуль Dashboard, предоставляющий веб-интерфейс для управления.

### Обзор функций

| Функция | Описание |
|------|------|
| Панель мониторинга | Обзор системы, мониторинг CPU/памяти, время работы, статистика событий |
| Управление ботами | Просмотр состояния и информации о ботах на разных платформах |
| Просмотр событий | Поток событий в реальном времени, фильтрация по типу и платформе |
| Просмотр логов | Просмотр логов с фильтрацией по модулю и уровню |
| Управление модулями | Просмотр, загрузка, удаление установленных модулей и адаптеров |
| Магазин модулей | Просмотр доступных удаленных пакетов и установка их одним кликом |
| Редактирование конфигурации | Онлайн-редактирование `config.toml` |
| Управление хранилищем | Просмотр и редактирование данных хранилища Key-Value |
| Резервное копирование | Экспорт/импорт конфигурации и данных хранилища |
| Журнал аудита | Запись всех операций управления |

### Установка модулей через Dashboard

Dashboard включает функцию магазина модулей, с помощью которой вы можете:

1. **Установить из магазина**: просмотреть список доступных удаленных модулей и установить нужный одним кликом
2. **Загрузить локальный пакет**: загрузить `.whl` или `.zip` файл для установки, удобно для тестирования собственных разработок

> **Быстрый тест для разработчиков модулей**: после развертывания с помощью Docker, вы можете загрузить `.whl` файл, созданный вами, через функцию "Загрузить локальный пакет" в Dashboard для тестирования, без необходимости ручного взаимодействия с контейнером.

## Надзор за процессами и принудительный перезапуск

Принудительный перезапуск ErisPulse (`sdk.hard_restart()`) зависит от **внешнего надзирателя**, который перезапускает процесс при выходном коде 42 — SDK сам не запускает новый процесс. В рабочей среде необходимо настроить надзирателя, иначе процесс не будет автоматически восстанавливаться после принудительного перезапуска:

- Docker: `restart: unless-stopped` (перезапуск при любом выходном коде, включая 42)
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: добавить 42 в список перезапускаемых кодов выхода
- Чистый Python с пользовательским надзирателем: цикл `Popen` + проверка `returncode == 42`

Примеры полной конфигурации надзирателей и описание соглашения по выходному коду 42 см. в разделе [Процесс запуска → Руководство по надзирателям](../advanced/startup.md#Руководство-по-надзирателям).

## Проверка работоспособности

SDK включает конечную точку проверки работоспособности:

```bash
# Проверка работоспособности
curl http://localhost:8000/health
```

Проверку работоспособности в Docker можно добавить в `docker-compose.yml`:

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

## Обратный прокси

Если необходимо выставить Dashboard через обратный прокси, например, Nginx:

```nginx
server {
    listen 80;
    server_name bot.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Поддержка WebSocket (необходима для потоков событий Dashboard)
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL можно настроить с помощью Let's Encrypt:

```bash
sudo certbot --nginx -d bot.example.com
```

## Ручное развертывание (pip)

Если не использовать Docker, можно развернуть вручную.

### Настройка для рабочей среды

```toml
# config/config.toml

[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"
log_files = ["app.log"]
memory_limit = 5000

[ErisPulse.framework]
enable_lazy_loading = true
```

### systemd (Linux)

Создайте `/etc/systemd/system/erispulse-bot.service`:

```ini
[Unit]
Description=ErisPulse Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/erispulse-bot
ExecStart=/opt/erispulse-bot/venv/bin/epsdk run main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Управление:

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

Создайте `/etc/supervisor/conf.d/erispulse-bot.conf`:

```ini
[program:erispulse-bot]
command=/opt/erispulse-bot/venv/bin/python -m ErisPulse run main.py
directory=/opt/erispulse-bot
user=bot
autostart=true
autorestart=true
stderr_logfile=/var/log/erispulse-bot/err.log
stdout_logfile=/var/log/erispulse-bot/out.log
```

### uv tool: разделение развертывания (отдельное окружение CLI и проекта)

`uv tool install` устанавливает `epsdk` в **отдельное окружение инструментов**, полностью изолируя CLI от зависимостей проекта: обновление CLI не затрагивает `.venv` проекта, а изменения зависимостей проекта не влияют на CLI.

```bash
# 1. Установка CLI глобально (автоматически доступны команды epsdk / ep)
uv tool install ErisPulse

# 2. В проекте размещаются только зависимости бота (`.venv` управляется uv)
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # Добавить адаптеры по мере необходимости

# 3. Запуск с помощью CLI (автоматически определяет и использует интерпретатор из `.venv` проекта)
epsdk run main.py
```

Особенности поведения:

- Порядок поиска целевого интерпретатора `epsdk run`: переменная окружения `ERISPULSE_PYTHON` → `.venv` проекта → текущий интерпретатор; окружение инструментов содержит только CLI, компоненты (адаптеры/модули) должны устанавливаться в `.venv` проекта
- Команды `epsdk install` / `uninstall` / `upgrade` / `list` действуют на `.venv` проекта, не влияя на окружение инструментов
- Обновление CLI: `uv tool upgrade ErisPulse` (или `epsdk self-update`, в окружении uv tool автоматически переключается на `uv tool upgrade`); обновление зависимостей проекта: в директории проекта выполнить `uv sync` / `uv add`, оба процесса не влияют друг на друга
- На сервере окружение инструментов управляется через uv (`uv tool list` для просмотра, `uv tool upgrade --all` для пакетного обновления), без ручного обслуживания глобальных пакетов pip
- Если использовать `uv run epsdk ...` в директории без проекта, создается **одноразовое изолированное окружение** (установленные компоненты не сохраняются); на сервере всегда используйте `epsdk` напрямую или сначала перейдите в директорию проекта

## Рекомендации по безопасности

1. **Установите токен доступа к Dashboard**: используйте сильный случайный токен, не используйте значение по умолчанию
2. **Не открывайте порт для публичного доступа**: если не используете обратный прокси + SSL, ограничьте порт Dashboard только внутренней сетью
3. **Защитите каталог данных**: каталог `config/` содержит конфигурацию и базу данных, установите соответствующие права доступа к файлам
4. **Регулярно обновляйте**: используйте `epsdk self-update` или обновите Docker-образ
5. **Не запускайте от root**: при ручном развертывании создайте специального пользователя
6. **Используйте стратегию перезапуска Docker**: `restart: unless-stopped` для автоматического перезапуска при аварийном завершении

## Развертывание нескольких экземпляров

При запуске нескольких экземпляров бота:

1. Каждый экземпляр использует отдельную директорию проекта и `docker-compose.yml`
2. Используйте разные порты: `ERISPULSE_PORT=8001`
3. Используйте разные имена контейнеров: `container_name: erispulse-bot2`

## Обновление и обслуживание

### Способ Docker

```bash
# Скачивание последнего образа
docker compose pull

# Перезапуск с использованием нового образа
docker compose up -d
```

### Способ pip

```bash
epsdk self-update
epsdk upgrade
```

### Способ uv tool

```bash
# Обновление окружения инструментов CLI
uv tool upgrade ErisPulse

# Обновление зависимостей проекта (выполняется в директории проекта)
uv sync
```

### Горячая перезагрузка конфигурации сервера в режиме реального времени

После изменения адреса прослушивания / порта / SSL-сертификата перезапуск процесса не требуется. В любом корутине вызовите `router.reload()`:

```python
await sdk.router.reload(port=9000)                                # Смена порта
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # Горячая замена сертификата (сценарий продления)
await sdk.router.reload(host="0.0.0.0", port=9000)                # Непереданные параметры берутся из текущей конфигурации
```

- Используется один и тот же экземпляр FastAPI, все зарегистрированные HTTP / WebSocket / SSE-маршруты сохраняются
- Новая конфигурация проверяется (сертификат может быть построен, порт доступен) перед переключением; при неудаче обслуживание возвращается к старой конфигурации и возвращается `False`,
  гарантируя, что возвращение `False` = старая служба остается доступной
- Если сервер не запущен, возвращается `False` (первый запуск следует использовать `sdk.router.start()`)

### Резервное копирование

Регулярно создавайте резервные копии каталога `config/`:

```bash
# Docker-развертывание
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Или используйте функцию "Резервное копирование" в Dashboard для экспорта
```