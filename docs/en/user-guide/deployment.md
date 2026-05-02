# Deployment Guide

Best practices for deploying ErisPulse bot to production environments.

## Docker Deployment (Recommended)

ErisPulse provides official Docker images with the ErisPulse framework and Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.

### Quick Start

```bash
# Pull the image
docker pull erispulse/erispulse:latest

# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set Dashboard login token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

After startup, access `http://localhost:8000/Dashboard` and login using the token you set as the password.

### Domestic Mirror Acceleration

If Docker Hub is not accessible, you can pull images from GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

When using ghcr.io images, you need to modify the `image` in `docker-compose.yml`:

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
|----------|--------------|-------------|
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `ERISPULSE_DASHBOARD_TOKEN` | Auto-generated | Dashboard login token (highly recommended to set) |
| `TZ` | `Asia/Shanghai` | Timezone |

### Data Persistence

The `./config` directory is mounted for configuration files and database, containing:

- `config/config.toml` — Configuration file
- `config/config.db` — SQLite storage database

## Dashboard Management Panel

The ErisPulse Docker image includes a Dashboard module that provides a web-based management interface.

### Feature Overview

| Feature | Description |
|---------|-------------|
| Dashboard | System overview, CPU/memory monitoring, uptime, event statistics |
| Bot Management | View online status and information of bots on various platforms |
| Event Viewer | Real-time event stream with filtering by type and platform |
| Log Viewer | Log viewer with filtering by module and level |
| Module Management | View, load, and unload installed modules and adapters |
| Module Store | Browse remotely available packages with one-click installation |
| Configuration Editor | Edit `config.toml` online |
| Storage Management | Browse and edit Key-Value storage data |
| Backup | Export/import configuration and storage data |
| Audit Log | Record all management operations |

### Installing Modules via Dashboard

The Dashboard integrates a module store function where you can:

1. **Install from Store**: Browse the remote module list and install needed modules with one click
2. **Upload Local Package**: Directly upload `.whl` or `.zip` files for installation, convenient for testing personally developed modules

> **Quick testing workflow for module developers**: After deploying with Docker, directly upload your built `.whl` file through the "Upload Local Package" function in Dashboard for testing, without manual container operations.

## Health Check

The SDK has built-in health check endpoints:

```bash
# Simple check
curl http://localhost:8000/ping

# Detailed status
curl http://localhost:8000/health
```

Docker health check can be added in `docker-compose.yml`:

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ping"]
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

SSL can be set up with Let's Encrypt:

```bash
sudo certbot --nginx -d bot.example.com
```

## Manual Deployment (pip)

If not using Docker, manual deployment is also possible.

### Production Configuration

```toml
# config/config.toml

[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"
file_output = true
max_lines = 5000

[ErisPulse.module]
lazy_load = true
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

1. **Set Dashboard Token**: Use a strong random token, don't use default values
2. **Don't Expose Port to Public Network**: Unless using reverse proxy + SSL, restrict Dashboard port to internal network
3. **Protect Data Directory**: The `config/` directory contains configuration and database, set appropriate file permissions
4. **Regular Updates**: Use `epsdk self-update` or pull the latest Docker image
5. **Don't Run as Root**: Create a dedicated user for manual deployment
6. **Use Docker Restart Policy**: `restart: unless-stopped` ensures automatic restart after unexpected exits

## Multi-instance Deployment

When running multiple bot instances:

1. Each instance should use a separate project directory and `docker-compose.yml`
2. Use different ports: `ERISPULSE_PORT=8001`
3. Use different container names: `container_name: erispulse-bot2`

## Updates and Maintenance

### Docker Method

```bash
# Pull latest image
docker compose pull

# Restart with new image
docker compose up -d
```

### pip Method

```bash
epsdk self-update
epsdk upgrade
```

### Backup

Regularly backup the `config/` directory:

```bash
# Docker deployment
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Or export using the "Backup" function in Dashboard