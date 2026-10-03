# Руководство по развертыванию

Лучшие практики развертывания бота ErisPulse в производственной среде.

## Docker-развертывание (рекомендуется)

ErisPulse предоставляет официальный образ Docker, включающий фреймворк ErisPulse и панель управления Dashboard, поддерживающий архитектуры `linux/amd64` и `linux/arm64`.

### Быстрый старт

```bash
# Загрузка образа
docker pull erispulse/erispulse:latest

# Загрузка docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Установка токена для входа в Dashboard и запуск
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

После запуска откройте `http://localhost:8000/Dashboard` и войдите, используя установленный токен в качестве пароля.

### Ускорение загрузки образов в Китае

Если Docker Hub недоступен, можно использовать GitHub Container Registry для загрузки образа:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

При использовании образа ghcr.io необходимо изменить `docker-compose.yml` для указания нового образа:

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
      # Постоянное хранение папки Python-пакетов
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    stop_grace_period: 30s
    restart: unless-stopped
```

> Рекомендуется использовать [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) из корня репозитория, он уже содержит вышеуказанные настройки, а также проверки на работоспособность, переменные окружения часового пояса и языка.

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|-----------|----------------------|----------|
| `ERISPULSE_PORT` | `8000` | Порт для Dashboard |
| `ERISPULSE_DASHBOARD_TOKEN` | 自动生成 | Токен для входа в Dashboard (рекомендуется установить) |
| `TZ` | `Asia/Shanghai` | Часовой пояс |
| `LANG` | `en_US.UTF-8` | Системный язык, автоматически определяет язык интерфейса запуска |
| `ERISPULSE_LANG` | пусто | Принудительный язык интерфейса запуска: `zh` / `zh_TW` / `en` / `ja` / `ru` (переопределяет `LANG`) |

### Постоянное хранение данных

Папка `./config` подключена для хранения конфигурации и базы данных, включая:

- `config/config.toml` — конфигурационный файл
- `config/config.db` — база данных SQLite
- `config/.packages` — папка site-packages Python, используемая для постоянного хранения, содержит установленные пакеты (впервые при запуске инициализируется из резервной копии в образе, последующие установки и обновления записываются в эту папку)

> **Обновление фреймворка (включая pre/rc) и самовосстановление образа**: при каждом запуске контейнера точка входа проверяет целостность основных пакетов, при повреждении восстанавливает версию, установленную пользователем — если версия была установлена через Dashboard (например, pre-версия), она будет переустановлена с PyPI в той же версии, без тихого возврата к версии из образа. Таким образом, после обновления Dashboard фреймворк будет оставаться в нужной версии даже после перезапуска контейнера.

## Панель управления Dashboard

В Docker-образе ErisPulse встроен модуль Dashboard, предоставляющий веб-интерфейс для управления.

### Обзор функций

| Функция | Описание |
|--------|----------|
| Панель мониторинга | Обзор системы, мониторинг CPU/памяти, время работы, статистика событий |
| Управление ботами | Просмотр статуса и информации о ботах на разных платформах |
| Просмотр событий | Поток событий в реальном времени, фильтрация по типу и платформе |
| Просмотр логов | Просмотр логов с фильтрацией по модулю и уровню |
| Управление модулями | Просмотр, загрузка, отключение установленных модулей и адаптеров |
| Магазин модулей | Просмотр доступных удаленных пакетов и установка с одного клика |
| Редактирование конфигурации | Онлайн-редактирование `config.toml` |
| Управление хранилищем | Просмотр и редактирование данных хранилища Key-Value |
| Резервное копирование | Экспорт/импорт конфигурации и данных хранилища |
| Журнал аудита | Запись всех операций управления |

### Установка модулей через Dashboard

Dashboard включает функцию магазина модулей, с помощью которой вы можете:

1. **Установить из магазина**: просмотреть список доступных модулей и установить нужный с одного клика
2. **Загрузить локальный пакет**: загрузить `.whl` или `.zip` файл для установки, удобно для тестирования разработанных модулей

> **Быстрый тестовый процесс для разработчиков модулей**: после развертывания в Docker, используйте функцию «Загрузить локальный пакет» в Dashboard для загрузки собранного `.whl` файла и проведения тестирования, без необходимости ручного взаимодействия с контейнером.

## Надзор за процессом и жесткий перезапуск

Жесткий перезапуск ErisPulse (`sdk.hard_restart()`) зависит от внешнего надзирателя, который перезапускает процесс при коде выхода 42 — SDK сам не запускает новый процесс. В производственной среде необходимо настроить надзирателя, иначе после жесткого перезапуска процесс не будет автоматически восстановлен:

- Docker: `restart: unless-stopped` (перезапуск при любом коде выхода, включая 42)
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: добавьте 42 в список перезапускаемых кодов выхода
- Собственный надзиратель на Python: цикл `Popen` + проверка `returncode == 42`

Примеры полной конфигурации надзирателей и описание контракта с кодом выхода 42 см. в разделе [Процесс запуска → Руководство по надзирателям](../advanced/startup.md#Руководство-по-надзирателям).

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

    # Поддержка WebSocket (требуется для потока событий Dashboard)
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

## Ручное развертывание (pip)

Если Docker не используется, можно развернуть вручную.

### Конфигурация для производственной среды

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

1. **Установите токен для Dashboard**: используйте сильный случайный токен, не используйте значения по умолчанию
2. **Не открывайте порт для публичного доступа**: если не используется обратный прокси + SSL, ограничьте порт Dashboard внутренней сетью
3. **Защитите папку с данными**: папка `config/` содержит конфигурацию и базу данных, установите правильные права доступа
4. **Регулярно обновляйтесь**: используйте `epsdk self-update` или обновите Docker-образ
5. **Не запускайте от root**: при ручном развертывании создайте специального пользователя
6. **Используйте стратегию перезапуска Docker**: `restart: unless-stopped`, чтобы автоматически перезапускать процесс при сбое

## Многократное развертывание

При запуске нескольких экземпляров бота:

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

### Горячая перезагрузка серверных конфигураций в режиме работы

После изменения адреса прослушивания / порта / SSL-сертификата перезапуск процесса не требуется. В любом корутине вызовите `router.reload()`:

```python
await sdk.router.reload(port=9000)                                # Смена порта
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # Горячая замена сертификата (сценарий продления)
await sdk.router.reload(host="0.0.0.0", port=9000)                # Параметры по умолчанию используют текущую конфигурацию
```

- Используется один и тот же экземпляр FastAPI, все зарегистрированные HTTP / WebSocket / SSE-маршруты сохраняются
- Сначала проверяется новая конфигурация (можно ли построить сертификат, доступен ли порт), затем происходит переключение; при ошибке сервис возвращается к старой конфигурации и возвращает `False`, гарантируя, что возвращение `False` = старый сервис остается доступным
- При отсутствии запущенного сервера возвращается `False` (при первом запуске используйте `sdk.router.start()`)

### Резервное копирование

Регулярно создавайте резервные копии папки `config/`:

```bash
# Docker-развертывание
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Или используйте функцию «Резервное копирование» в Dashboard для экспорта
```