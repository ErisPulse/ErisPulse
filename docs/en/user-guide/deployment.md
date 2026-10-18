# Deployment Guide

Best practices for deploying the ErisPulse bot to a production environment.

## Docker Deployment (Recommended)

ErisPulse provides an official Docker image, which includes the ErisPulse framework and Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.

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

If Docker Hub is inaccessible, you can pull the image from GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

When using the ghcr.io image, modify the `docker-compose.yml` file's image:

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
      # Persist Python package directory
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    stop_grace_period: 30s
    restart: unless-stopped
```

> It is recommended to directly use the [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) in the repository root, which includes the above configuration along with health checks, timezone, and language environment variables.

### Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `ERISPULSE_DASHBOARD_TOKEN` | Auto-generated | Dashboard login token (strongly recommended to set) |
| `TZ` | `Asia/Shanghai` | Timezone |
| `LANG` | `en_US.UTF-8` | System language, auto-detects the language of the startup interface |
| `ERISPULSE_LANG` | Empty | Force the startup interface language: `zh` / `zh_TW` / `en` / `ja` / `ru` (overrides `LANG`) |

### Data Persistence

The `./config` directory mounts configuration files and the database, including:

- `config/config.toml` — configuration file
- `config/config.db` — SQLite storage database
- `config/.packages` — Python site-packages persistent volume, saves framework, adapters, and installed modules (automatically initialized from the image's built-in backup during the first startup, subsequent module installations and framework hot updates are written to this directory)

> **Framework Upgrade (including pre/rc) and Image Self-Healing**: The entrypoint performs a core package integrity check at each container startup. If damaged, it repairs according to the "user-installed version priority" principle—explicitly installed/upgraded versions in the persistent volume (e.g., pre version installed via Dashboard) will be reinstalled from PyPI **at the same version**, without silently rolling back to the image's built-in version. Therefore, after a Dashboard upgrade of the framework, any number of container restarts should maintain the target version.

## Dashboard Management Panel

The ErisPulse Docker image includes a built-in Dashboard module, providing a web-based visual management interface.

### Feature Overview

| Feature | Description |
|---------|-------------|
| Dashboard | System overview, CPU/memory monitoring, uptime, event statistics |
| Robot Management | View online status and information of robots on various platforms |
| Event Viewing | Real-time event stream, supports filtering by type and platform |
| Log Viewing | Log viewer filtered by module and level |
| Module Management | View, load, and unload installed modules and adapters |
| Module Store | Browse remote available packages and install them with one click |
| Configuration Editing | Edit `config.toml` online |
| Storage Management | Browse and edit Key-Value storage data |
| Backup | Export/import configuration and storage data |
| Audit Log | Records all management operations |

### Installing Modules via Dashboard

The Dashboard integrates a module store feature, allowing you to:

1. **Install from the store**: Browse the list of remote modules and install the desired ones with one click
2. **Upload local packages**: Directly upload `.whl` or `.zip` files for installation, convenient for testing personal development modules

> **Quick testing workflow for module developers**: After deploying with Docker, use the "Upload local package" feature in the Dashboard to directly upload your built `.whl` file for testing, without manual container operations.

## Process Supervision and Hard Restart

ErisPulse's hard restart (`sdk.hard_restart()`) relies on an **external supervisor** to restart the process when the exit code is 42—the SDK itself does not restart new processes. In production environments, a supervisor must be configured; otherwise, the process will not automatically recover after a hard restart:

- Docker: `restart: unless-stopped` (restarts for any exit code, including 42)
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: add 42 to the list of restartable exit codes
- Pure Python custom supervisor: loop `Popen` + check `returncode == 42`

Complete configuration examples for each supervisor and the exit code 42 contract are available in [Startup Flow → Supervisor Guide](../advanced/startup.md#Supervisor-Guide).

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
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

## Reverse Proxy

If you need to expose the Dashboard via a reverse proxy like Nginx:

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

If you do not use Docker, manual deployment is also possible.

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
```

### uv tool for Separated Deployment (CLI and Project Environment Isolation)

`uv tool install` installs `epsdk` as an **independent tool environment**, completely isolating the CLI from project dependencies: upgrading the CLI does not affect the project `.venv`, and changes in project dependencies do not affect the CLI.

```bash
# 1. Install CLI globally (automatically exposes epsdk / ep commands)
uv tool install ErisPulse

# 2. Only include robot dependencies in the project (managed by uv)
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # Add adapters as needed

# 3. Run with CLI (automatically detects and uses the project's .venv interpreter)
epsdk run main.py
```

Behavior points:

- The target interpreter resolution order for `epsdk run`: `ERISPULSE_PYTHON` environment variable → project `.venv` → current interpreter; the tool environment only hosts the CLI, components (adapters/modules) should be installed into the project `.venv`
- `epsdk install` / `uninstall` / `upgrade` / `list` also affect the project `.venv`, without polluting the tool environment
- Upgrade CLI: `uv tool upgrade ErisPulse` (or directly `epsdk self-update`, uv tool environment automatically switches to `uv tool upgrade`); upgrade project dependencies: execute `uv sync` / `uv add` in the project directory, both are independent
- In server scenarios, the tool environment is managed uniformly by uv (use `uv tool list` to view, `uv tool upgrade --all` for batch upgrades), eliminating the need for manual maintenance of global pip packages
- If `uv run epsdk ...` is executed in a directory without a project, it falls into a **one-time isolated environment** (installed components are not persisted); on servers, always use `epsdk` directly, or first `cd` into the project directory

## Security Recommendations

1. **Set Dashboard Token**: Use a strong random token, do not use the default value
2. **Do Not Expose Port to Public Network**: Unless using a reverse proxy + SSL, restrict the Dashboard port to the internal network
3. **Protect Data Directory**: The `config/` directory contains configuration and database, set appropriate file permissions
4. **Regular Updates**: Use `epsdk self-update` or pull the latest Docker image
5. **Do Not Run as Root**: Create a dedicated user when deploying manually
6. **Use Docker Restart Policy**: `restart: unless-stopped` ensures automatic restart after abnormal exits

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

# Restart to use the new image
docker compose up -d
```

### pip Method

```bash
epsdk self-update
epsdk upgrade
```

### uv tool Method

```bash
# Upgrade CLI tool environment
uv tool upgrade ErisPulse

# Upgrade project dependencies (execute within the project directory)
uv sync
```

### Hot Reload Server Configuration at Runtime

After modifying the listening address / port / SSL certificate, no process restart is needed. Call `router.reload()` in any coroutine:

```python
await sdk.router.reload(port=9000)                                # Change port
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # Hot swap certificate (for certificate renewal scenarios)
await sdk.router.reload(host="0.0.0.0", port=9000)                # Use current configuration for missing parameters
```

- Reuse the same FastAPI application, all module-registered HTTP / WebSocket / SSE routes are retained
- Validate new configuration first (certificate can be built, port available) before switching; if failed, restore service with old configuration and return `False`, ensuring `False` means the old service remains available
- Return `False` if the server is not running (use `sdk.router.start()` for initial startup)

### Backup

Regularly back up the `config/` directory:

```bash
# Docker deployment
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Or use the "Backup" feature in the Dashboard to export
```