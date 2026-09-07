# Руководство по развертыванию

Рекомендации по развертыванию бота ErisPulse в производственной среде.

## Docker-развертывание (рекомендуется)

ErisPulse предоставляет официальный Docker-образ, включающий фреймворк ErisPulse и панель управления Dashboard, поддерживающий архитектуры `linux/amd64` и `linux/arm64`.

### Быстрый старт

```bash
# Загрузка образа
docker pull erispulse/erispulse:latest

# Загрузка docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Настройка токена доступа к Dashboard и запуск
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

После запуска перейдите по адресу `http://localhost:8000/Dashboard` и войдите, используя заданный токен в качестве пароля.

### Ускорение загрузки образов в Китае

Если Docker Hub недоступен, можно использовать GitHub Container Registry для загрузки образа:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

При использовании образа из ghcr.io, необходимо изменить `docker-compose.yml`, указав `image`:

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
      # Объем для сохранения пакетов Python
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    stop_grace_period: 30s
    restart: unless-stopped
```

> Рекомендуется использовать [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) из корневого каталога репозитория, так как он уже содержит вышеуказанные настройки, а также проверки работоспособности, переменные окружения часового пояса и языка.

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Порт для доступа к Dashboard |
| `ERISPULSE_DASHBOARD_TOKEN` | 自动生成 | Токен для доступа к Dashboard (рекомендуется задать) |
| `TZ` | `Asia/Shanghai` | Часовой пояс |
| `LANG` | `en_US.UTF-8` | Язык системы, автоматически определяется язык интерфейса запуска |
| `ERISPULSE_LANG` | пусто | Принудительный язык интерфейса запуска: `zh` / `zh_TW` / `en` / `ja` / `ru` (переопределяет `LANG`) |

### Сохранение данных

Каталог `./config` монтируется для хранения конфигурации и базы данных, включая:

- `config/config.toml` — конфигурационный файл
- `config/config.db` — база данных SQLite
- `config/.packages` — том для сохранения пакетов Python, хранит фреймворк, адаптеры и установленные модули (при первом запуске инициализируется из резервной копии в образе, последующие установки модулей и обновления фреймворка записываются в этот каталог)

## Панель управления Dashboard

В Docker-образе ErisPulse встроен модуль Dashboard, предоставляющий веб-интерфейс для управления.

### Обзор функций

| Функция | Описание |
|------|------|
| Панель | Обзор системы, мониторинг CPU и памяти, время работы, статистика событий |
| Управление ботами | Просмотр статуса и информации о ботах на разных платформах |
| Просмотр событий | Поток событий в реальном времени, фильтрация по типу и платформе |
| Просмотр логов | Просмотр логов с фильтрацией по модулю и уровню |
| Управление модулями | Просмотр, загрузка и выгрузка установленных модулей и адаптеров |
| Магазин модулей | Просмотр доступных удаленных пакетов и установка с одного клика |
| Редактирование конфигурации | Онлайн-редактирование `config.toml` |
| Управление хранилищем | Просмотр и редактирование данных хранилища Key-Value |
| Резервное копирование | Экспорт/импорт конфигурации и данных хранилища |
| Журнал аудита | Запись всех операций управления |

### Установка модулей через Dashboard

Dashboard интегрирован с магазином модулей, позволяя:

1. **Установка из магазина**: просмотр списка удаленных модулей и установка нужного с одного клика
2. **Загрузка локального пакета**: загрузка `.whl` или `.zip` для установки, удобно для тестирования разработанных модулей

> **Быстрый тест для разработчиков модулей**: после развертывания в Docker, используйте функцию «Загрузить локальный пакет» в Dashboard для загрузки `.whl`-файла вашего модуля, без необходимости ручного взаимодействия с контейнером.

## Надзор за процессом и принудительный перезапуск

Принудительный перезапуск ErisPulse (`sdk.hard_restart()`) зависит от **внешнего надзирателя**, который перезапускает процесс при коде выхода 42 — сам SDK не перезапускает процесс. В производственной среде необходимо настроить надзирателя, иначе процесс не восстановится после принудительного перезапуска:

- Docker: `restart: unless-stopped` (перезапуск при любом коде выхода, включая 42)
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: добавить 42 в список кодов перезапуска
- Собственный надзиратель на Python: цикл `Popen` + проверка `returncode == 42`

Примеры настроек для различных надзирателей и описание контракта с кодом выхода 42 см. в [руководстве по надзирателям](../advanced/startup.md#надзиратели).

## Проверка работоспособности

SDK включает конечную точку проверки работоспособности:

```bash
# Проверка работоспособности
curl http://localhost:8000/health
```

Проверка работоспособности Docker-контейнера может быть добавлена в `docker-compose.yml`:

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

Для доступа к Dashboard через обратный прокси, например, Nginx:

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

    # Поддержка WebSocket (требуется для потока событий Dashboard)
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

Если Docker не используется, можно развернуть вручную.

### Настройка для production

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

## Рекомендации по безопасности

1. **Установите токен доступа к Dashboard**: используйте сильный случайный токен, не оставляйте значение по умолчанию
2. **Не открывайте порт для публичного доступа**: если не используется обратный прокси + SSL, ограничьте доступ к порту Dashboard только локальной сетью
3. **Защитите каталог данных**: каталог `config/` содержит конфигурацию и базу данных, установите соответствующие права доступа
4. **Регулярно обновляйте**: используйте `epsdk self-update` или обновляйте Docker-образ
5. **Не запускайте от root**: при ручном развертывании создайте специального пользователя
6. **Используйте стратегию перезапуска Docker**: `restart: unless-stopped` для автоматического перезапуска при сбое

## Развертывание нескольких экземпляров

Для запуска нескольких экземпляров бота:

1. Каждый экземпляр использует отдельный каталог проекта и `docker-compose.yml`
2. Используйте разные порты: `ERISPULSE_PORT=8001`
3. Используйте разные имена контейнеров: `container_name: erispulse-bot2`

## Обновление и обслуживание

### Docker-метод

```bash
# Загрузка последнего образа
docker compose pull

# Перезапуск с новым образом
docker compose up -d
```

### pip-метод

```bash
epsdk self-update
epsdk upgrade
```

### Резервное копирование

Регулярно делайте резервную копию каталога `config/`:

```bash
# Docker-развертывание
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Или используйте функцию «Резервное копирование» в Dashboard
```