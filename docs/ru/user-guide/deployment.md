# Руководство по развертыванию

Лучшие практики развертывания бота ErisPulse в рабочей среде (production).

## Развертывание с Docker (рекомендуется)

ErisPulse предоставляет официальный образ Docker, в котором встроены фреймворк ErisPulse и панель управления Dashboard, поддерживающие архитектуры `linux/amd64` и `linux/arm64`.

### Быстрый старт

```bash
# Вытягивание образа
docker pull erispulse/erispulse:latest

# Загрузка docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Настройка токена входа в Dashboard и запуск
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

После запуска перейдите по адресу `http://localhost:8000/Dashboard` и войдите в систему, используя настроенный токен в качестве пароля.

### Ускорение зеркала в Китае

Если Docker Hub недоступен, можно использовать GitHub Container Registry для скачивания образа:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

При использовании зеркала ghcr.io необходимо изменить поле `image` в `docker-compose.yml`:

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
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    restart: unless-stopped
```

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Порт проброса Dashboard |
| `ERISPULSE_DASHBOARD_TOKEN` | Автоматически генерируется | Токен входа в Dashboard (настоятельно рекомендуется установить) |
| `TZ` | `Asia/Shanghai` | Часовой пояс |

### Хранение данных

Каталог `./config` подключен для хранения конфигурационных файлов и базы данных, включает в себя:

- `config/config.toml` — файл конфигурации
- `config/config.db` — база данных SQLite

## Панель управления Dashboard

Образ Docker ErisPulse включает встроенный модуль Dashboard, предоставляющий веб-интерфейс для визуального управления.

### Обзор функций

| Функция | Описание |
|------|------|
| Панель мониторинга | Обзор системы, мониторинг CPU/памяти, время работы, статистика событий |
| Управление ботами | Просмотр онлайн-статуса и информации ботов на различных платформах |
| Просмотр событий | Поток событий в реальном времени, поддерживается фильтрация по типу и платформе |
| Просмотр логов | Виджеты логов с фильтрацией по модулю и уровню |
| Управление модулями | Просмотр, загрузка и выгрузка установленных модулей и адаптеров |
| Магазин модулей | Просмотр удаленных пакетов и установка одним кликом |
| Редактирование конфигурации | Онлайн-редактирование файла `config.toml` |
| Управление хранилищем | Просмотр и редактирование данных в хранилище Key-Value |
| Резервное копирование | Экспорт/импорт конфигурации и данных хранилища |
| Журнал аудита | Запись всех административных операций |

### Установка модулей через Dashboard

Dashboard интегрирован с функционалом магазина модулей, вы можете:

1. **Установка из магазина**: Просмотр списка удаленных модулей и установка нужных одним кликом
2. **Загрузка локального пакета**: Прямая загрузка файлов `.whl` или `.zip` для установки, удобно для тестирования модулей собственного разработки

> **Быстрый процесс тестирования для разработчиков модулей**: После развертывания через Docker, используя функцию «Загрузка локального пакета» в Dashboard, загрузите собранный файл `.whl` для тестирования, без необходимости ручных действий с контейнером.

## Проверка здоровья

SDK содержит встроенную точку проверки здоровья:

```bash
# Проверка здоровья
curl http://localhost:8000/health
```

Проверка здоровья Docker может быть добавлена в `docker-compose.yml`:

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Обратный прокси

Если необходимо раскрыть Dashboard через обратный прокси, например Nginx:

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

    # Поддержка WebSocket (необходима для потока событий в реальном времени Dashboard)
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL можно использовать Let's Encrypt:

```bash
sudo certbot --nginx -d bot.example.com
```

## Ручное развертывание (pip)

Если не использовать Docker, также возможно ручное развертывание.

### Конфигурация для продакшна

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

1. **Настройте токен Dashboard**: Используйте надежный случайный токен, не используйте значения по умолчанию
2. **Не открывайте порт в интернет**: Если не используется обратный прокси + SSL, ограничьте порт Dashboard локальной сетью
3. **Защитите каталог данных**: В каталоге `config/` содержатся конфигурация и база данных, установите соответствующие права доступа к файлам
4. **Регулярное обновление**: Используйте `epsdk self-update` или обновите образ Docker
5. **Не запускайте от имени root**: При ручном развертывании создайте специального пользователя
6. **Используйте политику перезапуска Docker**: `restart: unless-stopped` обеспечивает автоматический перезапуск после аварийного завершения

## Развертывание нескольких экземпляров

При запуске нескольких экземпляров бота:

1. Используйте независимый каталог проекта и `docker-compose.yml` для каждого экземпляра
2. Используйте разные порты: `ERISPULSE_PORT=8001`
3. Используйте разные имена контейнеров: `container_name: erispulse-bot2`

## Обновление и обслуживание

### Способ с Docker

```bash
# Вытягивание последнего образа
docker compose pull

# Перезапуск с использованием нового образа
docker compose up -d
```

### Способ с pip

```bash
epsdk self-update
epsdk upgrade
```

### Резервное копирование

Регулярное резервное копирование каталога `config/`:

```bash
# Развертывание с Docker
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Или используйте функцию «Резервное копирование» в Dashboard для экспорта