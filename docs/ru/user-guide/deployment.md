# Руководство по развертыванию

Лучшие практики развертывания бота ErisPulse в производственной среде.

## Docker 集成 (Рекомендуется)

ErisPulse предоставляет официальный Docker-образ, включающий фреймворк ErisPulse и панель управления Dashboard, поддерживает архитектуры `linux/amd64` и `linux/arm64`.

### Быстрый старт

```bash
# Загрузка образа
docker pull erispulse/erispulse:latest

# Загрузка docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Установка токена для входа в Dashboard и запуск
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

После запуска перейдите по адресу `http://localhost:8000/Dashboard` и используйте установленный токен в качестве пароля для входа.

### Ускорение загрузки образа в Китае

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
      # Сохранение директории Python-пакетов
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    stop_grace_period: 30s
    restart: unless-stopped
```

> Рекомендуется использовать файл [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) из корня репозитория, он уже содержит вышеуказанные настройки, а также проверку работоспособности, переменные окружения для часового пояса и языка.

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Порт для панели управления Dashboard |
| `ERISPULSE_DASHBOARD_TOKEN` | 自动生成 | Токен для входа в Dashboard (рекомендуется установить) |
| `TZ` | `Asia/Shanghai` | Часовой пояс |
| `LANG` | `en_US.UTF-8` | Системный язык, автоматически определяет язык интерфейса запуска |
| `ERISPULSE_LANG` | пусто | Принудительный язык интерфейса запуска: `zh` / `zh_TW` / `en` / `ja` / `ru` (переопределяет `LANG`) |

### Сохранение данных

Директория `./config` монтируется для хранения конфигурационных файлов и базы данных, включая:

- `config/config.toml` — конфигурационный файл
- `config/config.db` — база данных SQLite
- `config/.packages` — директория site-packages Python, сохраняющая фреймворк, адаптеры и установленные модули (при первом запуске инициализируется автоматически из резервной копии в образе, последующие установки модулей и горячие обновления фреймворка записываются в эту директорию)

> **Обновление фреймворка (включая pre/rc) и самовосстановление образа**: точка входа выполняет проверку целостности основных пакетов при каждом запуске контейнера, при повреждении восстанавливает пакеты по принципу "приоритет установленной пользователем версии" — если версия была явно установлена/обновлена в сохранённом томе (например, предварительная версия, установленная через Dashboard), то она будет переустановлена из PyPI **в той же версии**, без тихого возврата к версии из образа. Таким образом, после обновления фреймворка через Dashboard, при любом перезапуске контейнера будет сохраняться целевая версия.

## Панель управления Dashboard

В Docker-образе ErisPulse встроен модуль Dashboard, предоставляющий веб-интерфейс для визуального управления.

### Обзор функций

| Функция | Описание |
|------|------|
| Панель мониторинга | Обзор системы, мониторинг CPU/памяти, время работы, статистика событий |
| Управление ботами | Просмотр статуса и информации о ботах на различных платформах |
| Просмотр событий | Поток событий в реальном времени, фильтрация по типу и платформе |
| Просмотр логов | Просмотр логов с фильтрацией по модулю и уровню |
| Управление модулями | Просмотр, загрузка, выгрузка установленных модулей и адаптеров |
| Магазин модулей | Просмотр удалённых доступных пакетов и установка с помощью одной кнопки |
| Редактирование конфигурации | Онлайн-редактирование `config.toml` |
| Управление хранилищем | Просмотр и редактирование данных хранилища Key-Value |
| Резервное копирование | Экспорт/импорт конфигурации и данных хранилища |
| Журнал аудита | Запись всех операций управления |

### Установка модулей через Dashboard

Dashboard включает функцию магазина модулей, с помощью которой вы можете:

1. **Установка из магазина**: Просмотр удалённого списка модулей, выбор нужного модуля и установка с помощью одной кнопки
2. **Загрузка локального пакета**: Прямая загрузка `.whl` или `.zip` файлов для установки, удобно для тестирования собственных разработок модулей

> **Быстрый тестовый процесс для разработчиков модулей**: После развертывания с помощью Docker, в Dashboard используйте функцию «Загрузка локального пакета» для прямой загрузки собранного вами `.whl` файла для тестирования, без необходимости ручного взаимодействия с контейнером.

## Мониторинг процессов и жесткий перезапуск

Жесткий перезапуск ErisPulse (`sdk.hard_restart()`) зависит от **внешнего монитора**, который перезапускает процесс при коде выхода 42 — SDK сам не запускает новый процесс. В продакшен-среде обязательно настройте монитор, иначе после жесткого перезапуска процесс не восстановится автоматически:

- Docker: `restart: unless-stopped` (перезапуск при любом коде выхода, включая 42)
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: добавьте 42 в список кодов выхода для перезапуска
- Чистый Python с пользовательским монитором: цикл `Popen` + проверка `returncode == 42`

Полные примеры конфигурации мониторов и описание контракта с кодом выхода 42 см. в разделе [Процесс запуска → Руководство по мониторам](../advanced/startup.md#Руководство-по-мониторам).

## Проверка состояния

В SDK встроен конечный эндпоинт для проверки состояния:

```bash
# Проверка состояния
curl http://localhost:8000/health
```

Для проверки состояния в Docker можно добавить в `docker-compose.yml`:

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

Если необходимо выставить Dashboard через обратный прокси-сервер, например, Nginx:

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

    # Поддержка WebSocket (требуется для потоковых событий Dashboard)
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Для SSL можно использовать Let's Encrypt:

```bash
sudo certbot --nginx -d bot.example.com
```

## Ручная установка (pip)

Если вы не используете Docker, вы также можете выполнить ручную установку.

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

Создайте файл `/etc/systemd/system/erispulse-bot.service`:

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

Создайте файл `/etc/supervisor/conf.d/erispulse-bot.conf`:

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

1. **Установите токен для Dashboard**: Используйте сильный случайный токен, не оставляйте значение по умолчанию
2. **Не открывайте порт для публичного доступа**: Если не используется обратный прокси + SSL, ограничьте порт Dashboard доступом только из локальной сети
3. **Защитите каталог данных**: Каталог `config/` содержит конфигурацию и базу данных, установите соответствующие права доступа к файлам
4. **Регулярно обновляйте**: Используйте `epsdk self-update` или получите последнюю версию Docker-образа
5. **Не запускайте от root**: При ручной установке создайте специального пользователя
6. **Используйте стратегию перезапуска Docker**: `restart: unless-stopped`, чтобы обеспечить автоматический перезапуск после аварийного завершения

## Множественный запуск экземпляров

При запуске нескольких экземпляров роботов:

1. Каждый экземпляр использует отдельный каталог проекта и `docker-compose.yml`
2. Используйте разные порты: `ERISPULSE_PORT=8001`
3. Используйте разные имена контейнеров: `container_name: erispulse-bot2`

## Обновление и обслуживание

### Способ Docker

```bash
# Получение последней версии образа
docker compose pull

# Перезапуск с использованием нового образа
docker compose up -d
```

### Способ pip

```bash
epsdk self-update
epsdk upgrade
```

### Резервное копирование

Регулярно создавайте резервную копию каталога `config/`:

```bash
# Развертывание с использованием Docker
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Или используйте функцию «Резервное копирование» в Dashboard для экспорта
```