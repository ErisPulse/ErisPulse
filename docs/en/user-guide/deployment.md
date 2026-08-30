# Deployment Guide

Best practices for deploying the ErisPulse bot to a production environment.



## Docker Deployment (Recommended)

ErisPulse provides an official Docker image with the ErisPulse framework and Dashboard management panel built in, supporting the `linux/amd64` and `linux/arm64` architectures.

### Quick Start

```bash
# Pull the image
docker pull erispulse/erispulse:latest

# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set the Dashboard login token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

After starting, access `http://localhost:8000/Dashboard` and log in using the set token as the password.

### Domestic Image Acceleration

If Docker Hub is inaccessible, you can pull the image using GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

When using the ghcr.io image, you need to modify the `image` in `docker-compose.yml`:

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

### Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `ERISPULSE_DASHBOARD_TOKEN` | Auto-generated | Dashboard login token (strongly recommended to set) |
| `TZ` | `Asia/Shanghai` | Timezone |

### Data Persistence

The `./config` directory mounts configuration files and the database, including:

- `config/config.toml` — Configuration file
- `config/config.db` — SQLite storage database

## Dashboard Management Panel

The ErisPulse Docker image includes a built-in Dashboard module, providing a web-based visualization management interface.

### Feature Overview

| Feature | Description |
|---------|-------------|
| Dashboard | System overview, CPU/memory monitoring, uptime, event statistics |
| Robot Management | View online status and information of robots across platforms |
| Event Viewing | Real-time event stream, supports filtering by type and platform |
| Log Viewing | Log viewer with filtering by module and level |
| Module Management | View, load, and unload installed modules and adapters |
| Module Store | Browse remote available packages and install them with one click |
| Configuration Editing | Edit `config.toml` online |
| Storage Management | Browse and edit Key-Value storage data |
| Backup | Export/import configuration and storage data |
| Audit Logs | Record all management operations |

### Installing Modules via Dashboard

The Dashboard integrates the module store functionality, allowing you to:

1. **Install from Store**: Browse the remote module list and install required modules with one click
2. **Upload Local Package**: Directly upload `.whl` or `.zip` files for installation, convenient for testing personal developed modules

> **Quick Testing Process for Module Developers**: After deploying with Docker, directly upload your built `.whl` file through the "Upload Local Package" feature in the Dashboard for testing, without manual container operations.

[**Quick Start**](docs/en/quick-start.md) | [**Configuration**](docs/en/configuration.md) | [**Modules**](docs/en/modules.md) | [**Dashboard**](docs/en/dashboard.md) | [**FAQ**](docs/en/faq.md)

## Process Supervision and Hard Restart

The hard restart of ErisPulse (`sdk.hard_restart()`) depends on an **external supervisor** to restart the process when the exit code is 42 — the SDK itself does not restart a new process. A supervisor must be configured in production environments; otherwise, the process will not automatically recover after a hard restart:

- Docker: `restart: unless-stopped` (restarts for any exit code, including 42)
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: add 42 to the list of restartable exit codes
- Custom Python supervisor: loop `Popen` + detect `returncode == 42`

Complete configuration examples for each supervisor and the exit code 42 contract are described in [Startup Flow → Supervisor Guide](../advanced/startup.md#supervisor-guide).

## Health Check

The SDK includes built-in health check endpoints:

```bash
# Health check
curl http://localhost:8000/health
```

Docker health checks can be added in `docker-compose.yml`:

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```


## Reverse Proxy

If you need to expose the Dashboard through a reverse proxy such as Nginx:

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

    # WebSocket support (required for Dashboard real-time event streams)
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL can be obtained using Let's Encrypt:

```bash
sudo certbot --nginx -d bot.example.com

## Manual Deployment (pip)

If you don't use Docker, you can also deploy manually.

### Production Environment Configuration

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

Create `/etc/systemd/system/erispulse-bot.service`:

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

Management:

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

Create `/etc/supervisor/conf.d/erispulse-bot.conf`:

```ini
[program:erispulse-bot]
command=/opt/erispulse-bot/venv/bin/python -m ErisPulse run main.py
directory=/opt/erispulse-bot
user=bot
autostart=true
autorestart=true
stderr_logfile=/var/log/erispulse-bot/err.log
stdout_logfile=/var/log/erispulse-bot/out.log

## Security Recommendations

1. **Set Dashboard Token**: Use a strong random token, do not use the default value
2. **Do not expose port to public network**: Unless using reverse proxy + SSL, restrict Dashboard port to internal network
3. **Protect data directory**: The `config/` directory contains configuration and database, set appropriate file permissions
4. **Regular updates**: Use `epsdk self-update` or pull the latest Docker image
5. **Do not run as root**: When deploying manually, create a dedicated user
6. **Use Docker restart policy**: `restart: unless-stopped` ensures automatic restart after abnormal exit



## Multi-Instance Deployment

When running multiple robot instances:

1. Each instance uses an independent project directory and `docker-compose.yml`
2. Use different port numbers: `ERISPULSE_PORT=8001`
3. Use different container names: `container_name: erispulse-bot2`

For document links, replace `docs/en/` with `docs/en/`:


## Update and Maintenance

### Docker Method

```bash
# Pull the latest image
docker compose pull

# Restart using the new image
docker compose up -d
```

### pip Method

```bash
epsdk self-update
epsdk upgrade
```

### Backup

Regularly back up the `config/` directory:

```bash
# For Docker deployment
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Or use the "Backup" function in the Dashboard to export
```

[**English**](docs/en/quick-start.md)