# Deployment Guide

> [!TIP]
> **When to read this**: When the bot needs to run long-term—Docker deployment, systemd / Supervisor process management, reverse proxy and SSL, backup and upgrade are all covered here. Skip this section if you are only doing local development and debugging.

After developing the bot, deployment is just the beginning. This guide covers three deployment methods (Docker / systemd / Supervisor), as well as reverse proxy, security hardening, and backup.

## Docker Deployment (Recommended)

ErisPulse provides an official Docker image, which includes the ErisPulse framework and the Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.

### Quick Start

```bash
# Pull the image
docker pull erispulse/erispulse:latest

# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set the Dashboard login token and start the container
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

After starting, access `http://localhost:8000/Dashboard` and log in using the set token as the password.

### Domestic Image Acceleration

If Docker Hub is inaccessible, you can use GitHub Container Registry to pull the image:

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
    image: erispulse/erispulse:${ERISPULSE_TAG:-latest}
    container_name: ${CONTAINER_NAME:-erispulse}
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
      # Persist Python package directory
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - LANG=${LANG:-en_US.UTF-8}
      - ERISPULSE_LANG=${ERISPULSE_LANG:-}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    # Graceful shutdown is handled by framework signal processing (SIGTERM), this only controls the grace period
    stop_grace_period: 30s
    restart: on-failure:5
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

> The above is consistent with the root [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) (the root version also has comments on image acceleration and environment variables), it is recommended to directly download and use it.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `ERISPULSE_TAG` | `latest` | Image tag (set to a specific version number if you want to lock the version) |
| `CONTAINER_NAME` | `erispulse` | Container name (useful for distinguishing instances in multi-instance deployment) |
| `ERISPULSE_DASHBOARD_TOKEN` | auto-generated | Dashboard login token (strongly recommended to set) |
| `TZ` | `Asia/Shanghai` | Timezone |
| `LANG` | `en_US.UTF-8` | System language, automatically detects the startup interface language |
| `ERISPULSE_LANG` | empty | Force startup interface language: `zh` / `zh_TW` / `en` / `ja` / `ru` (overrides `LANG`) |

### Data Persistence

The `./config` directory mounts configuration files and the database, including:

- `config/config.toml` — Configuration file
- `config/config.db` — SQLite storage database
- `config/.packages` — Persistent Python site-packages volume, saves the framework, adapters, and installed modules (automatically initialized from the image's built-in backup during the first startup; subsequent module installations and framework hot-updates are written to this directory)

> **Framework upgrade (including pre/rc) and image self-healing**: The entrypoint performs a core package integrity self-check each time the container starts. If damaged, it repairs based on the "user-installed version priority" principle—explicitly installed/updated versions (such as pre versions installed in Dashboard) are reinstalled from PyPI at the same version, never silently rolled back to the image's built-in version. Therefore, after Dashboard upgrades the framework, any container restart should maintain the target version.

## Dashboard Management Panel

The ErisPulse Docker image includes the Dashboard module, providing a Web-based visual management interface.

### Feature Overview

| Feature | Description |
|---------|-------------|
| Dashboard | System overview, CPU/memory monitoring, uptime, event statistics |
| Bot Management | View online status and information of bots on each platform |
| Event Viewer | Real-time event stream, supports filtering by type and platform |
| Log Viewer | Log viewer with filtering by module and level |
| Module Manager | View, load, and unload installed modules and adapters |
| Module Store | Browse remote available packages and install them with one click |
| Config Editor | Edit `config.toml` online |
| Storage Manager | Browse and edit Key-Value storage data |
| Backup | Export/import configuration and storage data |
| Audit Log | Records all management operations |

### Installing Modules via Dashboard

The Dashboard integrates a module store feature, allowing you to:

1. **Install from the store**: Browse the remote module list and install needed modules with one click
2. **Upload local packages**: Directly upload `.whl` or `.zip` files for installation, convenient for testing personal development modules

> **Quick testing workflow for module developers**: After deploying with Docker, use the "Upload local package" feature in the Dashboard to directly upload your built `.whl` file for testing, without manual container operations.

## Process Supervision and Hard Restart

ErisPulse's hard restart (`sdk.hard_restart()`) depends on an **external supervisor** to restart the process when the exit code is 42—the SDK itself does not restart new processes. Production environments must configure a supervisor; otherwise, the process will not automatically recover after a hard restart:

- Docker: The official compose uses `restart: on-failure:5`—restarts on any non-zero exit code (overrides the hard restart exit code 42), with a maximum of 5 consecutive restarts to prevent dead loops; unlimited restarts can be set by changing to `unless-stopped`
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: Add 42 to the list of restartable exit codes
- Pure Python custom supervisor: Use a loop `Popen` + check `returncode == 42`

Complete configuration examples for each supervisor and the exit code 42 contract are available in [Startup Flow → Supervisor Guide](../advanced/startup.md#Supervisor-Guide).

### Container Restart (PID 1 Instance)

> This feature requires ErisPulse **2.12+**.

When the framework runs as the main process (PID 1) inside a container, `epsdk restart` **does not** terminate and restart the process—terminating PID 1 causes the container to exit. Instead, send `SIGUSR1` to the framework process, which performs an in-process soft restart (component-level, `sdk.restart()`): `ep i <package>` newly installed adapters and upgraded module code are immediately hot-reloaded.

- For a full process restart (framework updates, structural configuration changes), restart the container: `docker restart <container>`
- `epsdk stop` still means termination for PID 1 instances—the container stops (whether it automatically restarts depends on the `restart` policy)

## Health Check

The SDK includes a built-in health check endpoint:

```bash
# Health check
curl http://localhost:8000/health
```

The official `docker-compose.yml` already includes the following health check; when writing your own compose file, you can refer to it:

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

    # WebSocket support (required for Dashboard real-time event streams)
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

If you don't use Docker, you can also deploy manually.

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

Manage the service:

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

`uv tool install` installs `epsdk` as an **independent tool environment**, completely isolating the CLI from project dependencies: upgrading the CLI does not touch the project `.venv`, and project dependency changes do not affect the CLI.

```bash
# 1. Install CLI globally (exposes epsdk / ep commands automatically)
uv tool install ErisPulse

# 2. Only include robot dependencies in the project (managed by uv)
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # Add adapters as needed

# 3. Run with CLI (automatically detects and uses the project .venv interpreter)
epsdk run main.py
```

Behavior points:

- The target interpreter resolution order for `epsdk run`: `ERISPULSE_PYTHON` environment variable → project `.venv` → current interpreter; the tool environment itself only hosts the CLI, components (adapters/modules) should be installed in the project `.venv`
- `epsdk install` / `uninstall` / `upgrade` / `list` also affect the project `.venv`, not the tool environment
- Upgrade CLI: `uv tool upgrade ErisPulse` (or directly `epsdk self-update`, uv tool environment automatically switches to `uv tool upgrade`); upgrade project dependencies: execute `uv sync` / `uv add` in the project directory, both are independent
- In server scenarios, the tool environment is managed by uv (use `uv tool list` to view, `uv tool upgrade --all` to batch upgrade), no need to manually maintain global pip packages
- If `uv run epsdk ...` is used in a directory without a project, it falls into a **one-time isolated environment** (installed components are not persistent); on servers, always use `epsdk` directly, or first `cd` into the project directory

## Security Recommendations

1. **Set Dashboard Token**: Use a strong random token, do not use the default value
2. **Do Not Expose Ports to Public Internet**: Unless using a reverse proxy + SSL, restrict the Dashboard port to the internal network
3. **Protect Data Directory**: The `config/` directory contains configuration and database, set appropriate file permissions
4. **Regular Updates**: Use `epsdk self-update` or pull the latest Docker image
5. **Do Not Run as Root**: Create a dedicated user for manual deployment
6. **Use Docker Restart Policy**: The official compose's `restart: on-failure:5` ensures automatic restart after abnormal exit (including hard restart exit code 42)
7. **Disable API Docs Endpoint**: `/docs`, `/redoc`, `/openapi.json` are enabled by default without authentication; disable with `router.disable_docs()` when deploying publicly
8. **Webhook Signature Verification**: The generated `verify_request` in the scaffold defaults to allowing all requests; implement signature/token verification before integrating public callbacks
9. **Security Model Boundaries**: The owner/scope system constrains platform-side users; loaded modules are considered trusted code (scope not configured defaults to allow, modules can register provider), do not load modules from untrusted sources

## Multi-Instance Deployment

When running multiple bot instances:

1. Each instance uses a separate project directory and `docker-compose.yml`
2. Use different port numbers: `ERISPULSE_PORT=8001`
3. Use different container names: `container_name: erispulse-bot2`

> **Storage Backend Note**: Instances do not share state (session inbox / conversation checkpoints / command cooldown are all instance memory state). The default SQLite is a single-file backend, **not** suitable for simultaneous access by multiple instances; each instance's `config/` directory must be independent. Switching to mysql / postgres only means each instance has its own independent database—current version does not support multi-instance collaboration (shared sessions/load balancing), multiple instances in the same group will respond independently, and deduplication must be handled at the platform or business level.

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

# Upgrade project dependencies (execute in project directory)
uv sync
```

### Hot Reload Server Configuration at Runtime

After modifying the listening address / port / SSL certificate, no process restart is needed. Call `router.reload()` in any coroutine:

```python
await sdk.router.reload(port=9000)                                # Change port
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # Hot swap certificate (for certificate renewal scenarios)
await sdk.router.reload(host="0.0.0.0", port=9000)                # Use current configuration for missing parameters
```

- Reuse the same FastAPI application, all HTTP / WebSocket / SSE routes registered by modules are retained
- Validate the new configuration (certificate can be constructed, port is available) before switching; if failed, restore service with the old configuration and return `False`, ensuring `False` means the old service remains available
- Return `False` if the server is not running (use `sdk.router.start()` for the first startup)

### Backup

Regularly back up the `config/` directory:

```bash
# Docker deployment
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Or use the "Backup" feature in the Dashboard to export
```

## Next Steps

- **After deployment, want visual management**: Install [ErisPulse-Dashboard](../ecosystem/dashboard.md), manage modules, view logs, and edit configurations in the browser
- **Suspecting environment issues**: First run `epsdk doctor` to output a health report, see [CLI Command Reference · doctor](cli-reference.md#doctor)
- **To adjust framework and component configurations**: Check [Configuration File Documentation](configuration.md), environment variable overrides are especially suitable for container deployment