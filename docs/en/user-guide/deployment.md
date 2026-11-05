# Deployment Guide

> [!TIP]
> **When to read this**: When the bot needs to run long-term—Docker deployment, systemd / Supervisor process supervision, reverse proxy and SSL, backup and upgrade are all covered here. Skip during local development and debugging.

After developing the bot, deployment is just the beginning. This guide covers three deployment methods required to run it stably on a server (Docker / systemd / Supervisor), as well as reverse proxy, security hardening, and backup.

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

After starting, access `http://localhost:8000/Dashboard` and use the set token as the password to log in.

### Domestic Mirror Acceleration

If Docker Hub cannot be accessed, you can pull the image from GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

When using the ghcr.io image, you need to modify the image in `docker-compose.yml`:

```yaml
services:
  erispulse:
    image: ghcr.io/erispulse/erispulse:latest
```

### docker-compose.yml

```yaml
services:
  erispulse:
    image: erispulse/erispulse:${ERISPULSE_TAG:-latest}
    container_name: ${CONTAINER_NAME:-erispulse}
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
      # Persistent Python package directory
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - LANG=${LANG:-en_US.UTF-8}
      - ERISPULSE_LANG=${ERISPULSE_LANG:-}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    # Graceful shutdown is handled by the framework's signal handling (SIGTERM), this only controls the grace period
    stop_grace_period: 30s
    restart: on-failure:5
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

> The above is consistent with the [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) in the repository root (the repository version has additional comments on mirror acceleration and environment variable explanations at the top), and it is recommended to download and use it directly.

### Environment Variables

| Variable | Default | Description |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `ERISPULSE_TAG` | `latest` | Image tag (set to a specific version number if you need to lock the version) |
| `CONTAINER_NAME` | `erispulse` | Container name (useful to distinguish instances in multi-instance deployment) |
| `ERISPULSE_DASHBOARD_TOKEN` | auto-generated | Dashboard login token (strongly recommended to set) |
| `TZ` | `Asia/Shanghai` | Timezone |
| `LANG` | `en_US.UTF-8` | System language, automatically detects the language of the startup interface |
| `ERISPULSE_LANG` | empty | Force the startup interface language: `zh` / `zh_TW` / `en` / `ja` / `ru` (overrides `LANG`) |

### Data Persistence

The `./config` directory mounts configuration files and the database, including:

- `config/config.toml` — configuration file
- `config/config.db` — SQLite storage database
- `config/.packages` — persistent Python site-packages volume, saves framework, adapters, and installed modules (automatically initialized from the image's built-in backup on the first startup, and subsequent module installations and framework hot-updates are written to this directory)

> **Framework upgrade (including pre/rc) and image self-healing**: The entrypoint performs a core package integrity self-check on every container startup. If damaged, it repairs according to the "user-installed version priority" principle—explicitly installed/upgraded versions in the persistent volume (such as pre versions installed in the Dashboard) will be reinstalled from PyPI with the same version, without silent rollback to the image's built-in version. Therefore, after the Dashboard upgrades the framework, any container restart should maintain the target version.

## Dashboard Management Panel

The ErisPulse Docker image includes the Dashboard module, providing a web-based visual management interface.

### Feature Overview

| Feature | Description |
|------|------|
| Dashboard | System overview, CPU/memory monitoring, uptime, event statistics |
| Bot Management | View online status and information of bots on each platform |
| Event Viewer | Real-time event stream, supports filtering by type and platform |
| Log Viewer | Log viewer with filtering by module and level |
| Module Management | View, load, and unload installed modules and adapters |
| Module Store | Browse remote available packages and install them with one click |
| Configuration Editor | Edit `config.toml` online |
| Storage Manager | Browse and edit Key-Value storage data |
| Backup | Export/import configuration and storage data |
| Audit Log | Records all management operations |

### Installing Modules via Dashboard

The Dashboard integrates the module store feature, allowing you to:

1. **Install from the store**: Browse the list of remote modules and install the desired ones with one click
2. **Upload local packages**: Directly upload `.whl` or `.zip` files for installation, which is convenient for testing personal-developed modules

> **Quick testing process for module developers**: After deploying with Docker, you can directly upload your built `.whl` file in the Dashboard's "Upload local package" feature for testing, without manually operating the container.

## Process Supervision and Hard Restart

ErisPulse's hard restart (`sdk.hard_restart()`) relies on an **external supervisor** to restart the process when the exit code is 42—the SDK itself does not restart a new process. In production environments, you must configure a supervisor; otherwise, the process will not automatically recover after a hard restart:

- Docker: The official compose uses `restart: on-failure:5`—restarts on any non-zero exit code (overriding the hard restart exit code 42), with a limit of 5 consecutive attempts to prevent dead loops; to allow unlimited attempts, you can change it to `unless-stopped`
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: Add 42 to the list of restartable exit codes
- Pure Python custom supervisor: Use a loop with `Popen` and check `returncode == 42`

Complete configuration examples for each supervisor and the exit code 42 contract are available in [Startup Flow → Supervisor Guide](../advanced/startup.md#Supervisor-Guide).

## Health Check

The SDK includes a built-in health check endpoint:

```bash
# Health check
curl http://localhost:8000/health
```

The official `docker-compose.yml` already includes the following health check; when writing your own compose file, you can reference it:

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

    # WebSocket support (required for Dashboard's real-time event stream)
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL can be used with Let's Encrypt:

```bash
sudo certbot --nginx -d bot.example.com
```

## Manual Deployment (pip)

If you do not use Docker, you can also deploy manually.

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

### uv tool Separated Deployment (CLI and Project Environment Isolation)

`uv tool install` installs `epsdk` as an **independent tool environment**, completely isolating the CLI from project dependencies: upgrading the CLI does not affect the project `.venv`, and changes in project dependencies do not affect the CLI.

```bash
# 1. Install CLI globally (automatically exposes epsdk / ep commands)
uv tool install ErisPulse

# 2. Only keep robot dependencies in the project (the .venv is managed by uv)
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # Add adapters as needed

# 3. Run with CLI (automatically detects and uses the interpreter in the project .venv)
epsdk run main.py
```

Behavior points:

- The target interpreter resolution order for `epsdk run`: `ERISPULSE_PYTHON` environment variable → project `.venv` → current interpreter; the tool environment only hosts the CLI, and components (adapters/modules) should be installed into the project `.venv`
- `epsdk install` / `uninstall` / `upgrade` / `list` also affect the project `.venv`, without polluting the tool environment
- Upgrade CLI: `uv tool upgrade ErisPulse` (or directly `epsdk self-update`, uv tool environment automatically changes to `uv tool upgrade`); upgrade project dependencies: execute `uv sync` / `uv add` in the project directory, the two do not affect each other
- In server scenarios, the tool environment is managed uniformly by uv (use `uv tool list` to view, `uv tool upgrade --all` to upgrade in bulk), without manual maintenance of global pip packages
- If `uv run epsdk ...` is executed in a directory without a project, it falls into a **one-time isolated environment** (installed components are not persisted); on servers, always use `epsdk` directly or first `cd` into the project directory

## Security Recommendations

1. **Set a Dashboard token**: Use a strong random token, do not use the default value
2. **Do not expose ports to the public network**: Unless using a reverse proxy + SSL, restrict the Dashboard port to the internal network
3. **Protect the data directory**: The `config/` directory contains configuration and database, set appropriate file permissions
4. **Regular updates**: Use `epsdk self-update` or pull the latest Docker image
5. **Do not run as root**: Create a dedicated user when deploying manually
6. **Use Docker restart policies**: The official compose's `restart: on-failure:5` ensures automatic restart after abnormal exit (including hard restart exit code 42)

## Multi-Instance Deployment

When running multiple robot instances:

1. Each instance uses a separate project directory and `docker-compose.yml`
2. Use different port numbers: `ERISPULSE_PORT=8001`
3. Use different container names: `container_name: erispulse-bot2`

## Update and Maintenance

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

### Runtime Hot Reload Server Configuration

After modifying the listening address / port / SSL certificate, there is no need to restart the process. In any coroutine, call `router.reload()`:

```python
await sdk.router.reload(port=9000)                                # Change port
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # Hot swap certificate (certificate renewal scenario)
await sdk.router.reload(host="0.0.0.0", port=9000)                # Default parameters use current configuration
```

- Reuse the same FastAPI application, all HTTP / WebSocket / SSE routes registered by modules are retained
- Validate new configurations first (certificate can be built, port is available) before switching; if it fails, restore to the old configuration and return `False`, ensuring that returning `False` means the old service remains available
- Return `False` if the server is not running (use `sdk.router.start()` for the first startup)

### Backup

Regularly back up the `config/` directory:

```bash
# Docker deployment
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Or use the "Backup" feature in the Dashboard to export
```

## Next Steps

- **After deployment, want visual management**: Install [ErisPulse-Dashboard](../ecosystem/dashboard.md), manage modules, view logs, and modify configurations in the browser
- **Suspect environment issues**: First run `epsdk doctor` to output a health report, see [CLI Command Reference · doctor](cli-reference.md#doctor)
- **To adjust framework and component configurations**: Check [Configuration File Description](configuration.md), environment variable overrides are especially suitable for container deployment