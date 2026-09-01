# Руководство по развертыванию

Лучшие практики развертывания бота ErisPulse в производственной среде.

## Docker-развертывание (рекомендуется)

ErisPulse предоставляет официальный Docker-образ, включающий фреймворк ErisPulse и панель управления Dashboard, поддерживающий архитектуры `linux/amd64` и `linux/arm64`.

### Быстрый старт

```bash
# Загрузка образа
docker pull erispulse/erispulse:latest

# Загрузка docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Установка токена для входа в Dashboard и запуск
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

После запуска перейдите по адресу `http://localhost:8000/Dashboard` и войдите, используя установленный токен в качестве пароля.

### Ускорение загрузки образов в Китае

Если Docker Hub недоступен, можно использовать GitHub Container Registry для загрузки образа:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

При использовании образа из ghcr.io необходимо изменить параметр `image` в `docker-compose.yml`:

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
| `ERISPULSE_PORT` | `8000` | Порт для панели управления Dashboard |
| `ERISPULSE_DASHBOARD_TOKEN` | 自动生成 | Токен для входа в Dashboard (рекомендуется установить) |
| `TZ` | `Asia/Shanghai` | Часовой пояс |

### Сохранение данных

Каталог `./config` монтируется для хранения конфигурации и базы данных, включая:

- `config/config.toml` — файл конфигурации
- `config/config.db` — база данных SQLite
- `config/.packages` — том для сохранения site-packages Python, хранит фреймворк, адаптеры и установленные модули (при первом запуске инициализируется из резервной копии в образе, последующие установки модулей и обновления фреймворка записываются в этот каталог)

## Панель управления Dashboard

В Docker-образе ErisPulse встроен модуль Dashboard, предоставляющий веб-интерфейс для визуального управления.

### Краткий обзор функций

| Функция | Описание |
|------|------|
| Панель | Обзор системы, мониторинг CPU/памяти, время работы, статистика событий |
| Управление роботами | Просмотр состояния и информации о роботах на разных платформах |
| Просмотр событий | Поток событий в реальном времени, фильтрация по типу и платформе |
| Просмотр логов | Просмотр логов с фильтрацией по модулю и уровню |
| Управление модулями | Просмотр, загрузка, выгрузка установленных модулей и адаптеров |
| Магазин модулей | Просмотр доступных удаленных пакетов и установка их одним нажатием |
| Редактирование конфигурации | Онлайн-редактирование файла `config.toml` |
| Управление хранилищем | Просмотр и редактирование данных хранилища Key-Value |
| Резервное копирование | Экспорт/импорт конфигурации и данных хранилища |
| Журнал аудита | Запись всех управляющих действий |

### Установка модулей через Dashboard

Dashboard включает функцию магазина модулей, с помощью которой вы можете:

1. **Установить из магазина**: просмотрите список доступных удаленных модулей и установите нужный одним нажатием
2. **Загрузить локальный пакет**: загрузите `.whl` или `.zip` файл для установки, удобно для тестирования собственных разработок

> **Быстрый тест для разработчиков модулей**: после развертывания с помощью Docker, используйте функцию "Загрузить локальный пакет" в Dashboard для загрузки и тестирования вашего собранного `.whl` файла, без необходимости ручных действий с контейнером.

## Надзор за процессами и принудительный перезапуск

Принудительный перезапуск ErisPulse (`sdk.hard_restart()`) зависит от **внешнего надзирателя**, который перезапускает процесс при выходном коде 42 — сам SDK не перезапускает процесс. В производственной среде обязательно настройте надзирателя, иначе после принудительного перезапуска процесс не восстановится:

- Docker: `restart: unless-stopped` (перезапуск при любом выходном коде, включая 42)
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: добавьте 42 в список кодов перезапуска
- Чистый Python-надзиратель: цикл `Popen` + проверка `returncode == 42`

Полные примеры конфигурации надзирателей и описание контракта с выходным кодом 42 см. в [руководстве по надзирателям](../advanced/startup.md#Руководство-по-надзирателям).

## Проверка работоспособности

SDK включает конечную точку проверки работоспособности:

```bash
# Проверка работоспособности
curl http://localhost:8000/health
```

Проверку работоспособности Docker можно добавить в `docker-compose.yml`:

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

    # Поддержка WebSocket (требуется для потока событий Dashboard)
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL можно использовать с Let's Encrypt:

```bash
sudo certbot --nginx -d bot.example.com
```

## Ручная установка (pip)

Если Docker не используется, можно развернуть вручную.

### Настройка для производственной среды

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

1. **Установите токен для Dashboard**: используйте сильный случайный токен, не оставляйте значение по умолчанию
2. **Не открывайте порт для публичного доступа**: если не используете обратный прокси + SSL, ограничьте доступ к порту Dashboard локальной сетью
3. **Защитите каталог данных**: каталог `config/` содержит конфигурацию и базу данных, установите соответствующие права доступа к файлам
4. **Регулярно обновляйте**: используйте `epsdk self-update` или загружайте последний Docker-образ
5. **Не запускайте от root**: при ручной установке создайте специального пользователя
6. **Используйте стратегию перезапуска Docker**: `restart: unless-stopped` для автоматического перезапуска при сбое

## Развертывание нескольких экземпляров

При запуске нескольких экземпляров роботов:

1. Используйте отдельный каталог проекта и `docker-compose.yml` для каждого экземпляра
2. Используйте разные порты: `ERISPULSE_PORT=8001`
3. Используйте разные имена контейнеров: `container_name: erispulse-bot2`

## Обновление и обслуживание

### Способ Docker

```bash
# Загрузка последнего образа
docker compose pull

# Перезапуск с новым образом
docker compose up -d
```

### Способ pip

```bash
epsdk self-update
epsdk upgrade
```

### Резервное копирование

Регулярно резервируйте каталог `config/`:

```bash
# Docker-развертывание
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Или используйте функцию "Резервное копирование" в Dashboard
```