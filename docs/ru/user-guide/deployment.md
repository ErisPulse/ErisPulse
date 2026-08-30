# Руководство по развертыванию

Лучшие практики развертывания бота ErisPulse в производственной среде.

Пожалуйста, верните полностью переведенный Markdown-документ, не добавляя никаких других текстов.

Еще раз напоминаем: если документ содержит строки переключения языка (строки, в которых названия языков разделены `` | ``), строго соблюдайте вышеуказанное правило №8, не записывая ошибочный формат вида ``[**Label**](file)``.

## Docker 雅чыруу (сунушталган)

ErisPulse ресми Docker образын түзеткен, ErisPulse фреймворк жана Dashboard администратор панели бар, `linux/amd64` жана `linux/arm64` архитектураларын колдонот.

### Тез баштоо

```bash
# Образды алып келүү
docker pull erispulse/erispulse:latest

# docker-compose.yml файлын түшүрүү
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard кирүү токенин жана ишке киргизүүнү тууралоо
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

Ишке киргизилгенден кийин `http://localhost:8000/Dashboard` сыяктуу URL-ди ачып, кирүү үчүн токенди колдонуңуз.

### Кытайда Docker тездетүү

Эгер Docker Hub жеткиликтүү болбосо, GitHub Container Registry колдонулуучу образды алууга болот:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

ghcr.io образын колдонууда `docker-compose.yml` файлындагы image параметри түзөтүлүшү керек:

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

### Көйгөйлөрдүн орнотуу

| Айлантма | Дефолт | Сүрөттөмө |
|----------|--------|-----------|
| `ERISPULSE_PORT` | `8000` | Dashboard портун ачып берүү |
| `ERISPULSE_DASHBOARD_TOKEN` | автоматтык түрдө түзүлөт | Dashboard кирүү токени (күчтүү түрдө күйгүзүү керек) |
| `TZ` | `Asia/Shanghai` | Убакыт аймактары |

### Данные жана сактоо

`./config` каталогу конфигурация файлдары менен база сактоосу менен байланыштырылган, анын ичинде:

- `config/config.toml` — конфигурация файлы
- `config/config.db` — SQLite сактоо базасы
- `config/.packages` — Python site-packages сактоо том, фреймворк, адаптер жана орнотулган модулдарды сактоо (биринчи ишке киргизилгенде, кийинки модулдардын орнотулушу жана фреймворктын жылуу жаңыртуусу бул каталогка жазылат)

## Панель управления Dashboard

В Docker-образе ErisPulse встроен модуль Dashboard, предоставляющий веб-интерфейс для визуального управления.

### Обзор функций

| Функция | Описание |
|------|------|
| Панель мониторинга | Обзор системы, мониторинг CPU/памяти, время работы, статистика событий |
| Управление роботами | Просмотр состояния и информации о роботах на различных платформах |
| Просмотр событий | Поток событий в реальном времени, фильтрация по типу и платформе |
| Просмотр логов | Просмотр логов с фильтрацией по модулю и уровню |
| Управление модулями | Просмотр, загрузка, выгрузка установленных модулей и адаптеров |
| Магазин модулей | Обзор доступных удалённых пакетов и установка одним кликом |
| Редактирование конфигурации | Онлайн-редактирование `config.toml` |
| Управление хранилищем | Просмотр и редактирование данных хранилища Key-Value |
| Резервное копирование | Экспорт/импорт конфигурации и данных хранилища |
| Журнал аудита | Запись всех операций управления |

### Установка модуля через Dashboard

Dashboard включает функцию магазина модулей, с помощью которой вы можете:

1. **Установка из магазина**: Обзор списка удалённых модулей, выбор нужного модуля и установка одним кликом
2. **Загрузка локального пакета**: Прямая загрузка `.whl` или `.zip` файлов для установки, удобно для тестирования модулей, разработанных самостоятельно

> **Быстрый тестовый процесс для разработчиков модулей**: После развертывания с помощью Docker, в Dashboard через функцию «Загрузить локальный пакет» можно напрямую загрузить собранный вами `.whl` файл для тестирования, без необходимости ручного взаимодействия с контейнером.

## Процессное наблюдение и жесткий перезапуск

Жесткий перезапуск ErisPulse (`sdk.hard_restart()`) зависит от **внешнего наблюдателя**, который перезапускает процесс при коде выхода 42 — SDK сам не запускает новый процесс. В продакшене необходимо настроить наблюдателя, иначе после жесткого перезапуска процесс не восстановится автоматически:

- Docker: `restart: unless-stopped` (перезапуск при любом коде выхода, включая 42)
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: добавить 42 в список кодов выхода для перезапуска
- Чистый Python с пользовательским наблюдателем: цикл `Popen` + проверка `returncode == 42`

Полные примеры конфигурации для различных наблюдателей и описание контракта с кодом выхода 42 см. в [Процесс запуска → Руководство по наблюдателям](../advanced/startup.md#Руководство-по-наблюдателям).

**Важно:** если документ содержит строку переключения языка (строку, где названия языков разделены `` | ``), необходимо строго соблюдать вышеуказанное правило формата, не записывая ошибочную конструкцию вида ``[**Label**](file)``.

## Мониторинг здоровья

SDK включает в себя конечную точку проверки состояния:

```bash
# Проверка состояния
curl http://localhost:8000/health
```

Проверка состояния в Docker может быть добавлена в `docker-compose.yml`:

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

[**中文**](docs/ru/quick-start.md) | [**English**](docs/ru/quick-start.md)

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

    # Поддержка WebSocket (требуется для потоков событий Dashboard)
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL можно использовать с помощью Let's Encrypt:

```bash
sudo certbot --nginx -d bot.example.com

## Ручная развертка (pip)

Если не использовать Docker, можно также развернуть вручную.

### Конфигурация для продакшена

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

## Рекомендации по безопасности

1. **Установка токена Dashboard**: Используйте сильный случайный токен, не используйте значения по умолчанию
2. **Не открывайте порт для публичного доступа**: Ограничьте порт Dashboard на внутренней сети, если не используется обратный прокси + SSL
3. **Защитите каталог данных**: Каталог `config/` содержит конфигурацию и базу данных, установите соответствующие права доступа к файлам
4. **Регулярное обновление**: Используйте `epsdk self-update` или получите последнюю версию Docker-образа
5. **Не запускайте от root**: При ручной установке создайте специального пользователя
6. **Используйте стратегию перезапуска Docker**: `restart: unless-stopped`, чтобы обеспечить автоматический перезапуск при аварийном завершении

[**Руководство**](docs/ru/quick-start.md)

## Множественная развертка экземпляров

При запуске нескольких экземпляров бота:

1. Каждый экземпляр использует отдельный каталог проекта и `docker-compose.yml`
2. Используйте разные порты: `ERISPULSE_PORT=8001`
3. Используйте разные имена контейнеров: `container_name: erispulse-bot2`

docs/ru/quick-start.md

## Обновление и обслуживание

### Способ Docker

```bash
# Получить последний образ
docker compose pull

# Перезапустить с использованием нового образа
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

[**Переключить язык**](docs/ru/switch-language.md)