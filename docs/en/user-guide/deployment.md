# Deployment Guide

Best practices for deploying the ErisPulse bot to a production environment.

## Docker Deployment (Recommended)

ErisPulse provides an official Docker image that includes the ErisPulse framework and Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.

### Quick Start

```bash
# Pull the image
docker pull erispulse/erispulse:latest

# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set the Dashboard login token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

After startup, access `http://localhost:8000/Dashboard` and log in using the set token as the password.

### Domestic Image Acceleration

If Docker Hub is inaccessible, you can pull the image from GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

When using the ghcr.io image, you need to modify the `docker-compose.yml` file to update the image:

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

| Variable | Default | Description |
|----------|---------|-------------|
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `ERISPULSE_DASHBOARD_TOKEN` | auto-generated | Dashboard login token (strongly recommended to set) |
| `TZ` | `Asia/Shanghai` | Timezone |

### Data Persistence

The `./config` directory mounts configuration files and the database, including:

- `config/config.toml` — Configuration file
- `config/config.db` — SQLite storage database
- `config/.packages` — Persistent volume for Python site-packages, storing the framework, adapters, and installed modules (automatically initialized from the image's built-in backup during the first startup, and subsequent module installations and framework hot updates are written to this directory)

## Dashboard Management Panel

The ErisPulse Docker image includes the Dashboard module, providing a web-based visual management interface.

### Feature Overview

| Feature | Description |
|---------|-------------|
| Dashboard | System overview, CPU/memory monitoring, uptime, event statistics |
| Robot Management | View online status and information of robots on various platforms |
| Event Viewing | Real-time event stream, with filtering by type and platform |
| Log Viewing | Log viewer with filtering by module and level |
| Module Management | View, load, and unload installed modules and adapters |
| Module Store | Browse remote available packages and install them with one click |
| Configuration Editing | Edit `config.toml` online |
| Storage Management | Browse and edit Key-Value storage data |
| Backup | Export/import configuration and storage data |
| Audit Log | Record all management operations |

### Installing Modules via Dashboard

The Dashboard integrates the module store feature, allowing you to:

1. **Install from the store**: Browse the list of remote modules and install the desired ones with one click
2. **Upload local packages**: Directly upload `.whl` or `.zip` files for installation, convenient for testing locally developed modules

> **Quick testing workflow for module developers**: After deploying with Docker, use the "Upload local package" feature in the Dashboard to directly upload your built `.whl` file for testing, without manual container operations.

## Process Supervision and Hard Restart

The hard restart (`sdk.hard_restart()`) of ErisPulse depends on an **external supervisor** restarting the process when the exit code is 42—the SDK itself does not restart the new process. Production environments must configure a supervisor; otherwise, the process will not automatically recover after a hard restart:

- Docker: `restart: unless-stopped` (restarts on any exit code, including 42)
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: Add 42 to the list of restartable exit codes
- Custom Python supervisor: Loop `Popen` + check `returncode == 42`

Complete configuration examples for each supervisor and the exit code 42 contract are available in [Startup Process → Supervisor Guide](../advanced/startup.md#supervisor-guide).

## Health Check

The SDK includes a built-in health check endpoint:

```bash
# Health check
curl http://localhost:8000/health
```

Docker health checks can be added to `docker-compose.yml`:

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

If you need to expose the Dashboard through a reverse proxy like Nginx:

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

    # WebSocket support (required for Dashboard real-time event stream)
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL can be enabled using Let's Encrypt:

```bash
sudo certbot --nginx -d bot.example.com
```

## Manual Deployment (pip)

If you do not use Docker, you can also deploy manually.

### Production Configuration

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
```

## Security Recommendations

1. **Set Dashboard Token**: Use a strong random token, do not use the default value
2. **Do Not Expose Port to Public**: Unless using a reverse proxy + SSL, restrict the Dashboard port to the internal network
3. **Protect Data Directory**: The `config/` directory contains configuration and database; set appropriate file permissions
4. **Regular Updates**: Use `epsdk self-update` or pull the latest Docker image
5. **Do Not Run as Root**: When deploying manually, create a dedicated user
6. **Use Docker Restart Policy**: `restart: unless-stopped` ensures automatic restart after abnormal exit

## Multi-Instance Deployment

When running multiple robot instances:

1. Each instance uses a separate project directory and `docker-compose.yml`
2. Use different port numbers: `ERISPULSE_PORT=8001`
3. Use different container names: `container_name: erispulse-bot2`

## Updates and Maintenance

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
# Docker deployment
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Or use the "Backup" feature in the Dashboard to export
```