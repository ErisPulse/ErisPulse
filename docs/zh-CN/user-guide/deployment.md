# 部署指南

将 ErisPulse 机器人部署到生产环境的最佳实践。

## Docker 部署（推荐）

ErisPulse 提供官方 Docker 镜像，内置 ErisPulse 框架和 Dashboard 管理面板，支持 `linux/amd64` 和 `linux/arm64` 架构。

### 快速启动

```bash
# 拉取镜像
docker pull erispulse/erispulse:latest

# 下载 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 设置 Dashboard 登录令牌并启动
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

启动后访问 `http://localhost:8000/Dashboard`，使用设置的令牌作为密码登录。

### 国内镜像加速

如果 Docker Hub 无法访问，可以使用 GitHub Container Registry 拉取镜像：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

使用 ghcr.io 镜像时，需要修改 `docker-compose.yml` 中的 image：

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

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard 端口映射 |
| `ERISPULSE_DASHBOARD_TOKEN` | 自动生成 | Dashboard 登录令牌（强烈建议设置） |
| `TZ` | `Asia/Shanghai` | 时区 |

### 数据持久化

`./config` 目录挂载了配置文件和数据库，包含：

- `config/config.toml` — 配置文件
- `config/config.db` — SQLite 存储数据库

## Dashboard 管理面板

ErisPulse Docker 镜像内置 Dashboard 模块，提供 Web 可视化管理界面。

### 功能概览

| 功能 | 说明 |
|------|------|
| 仪表盘 | 系统概览、CPU/内存监控、运行时长、事件统计 |
| 机器人管理 | 查看各平台机器人在线状态和信息 |
| 事件查看 | 实时事件流，支持按类型和平台过滤 |
| 日志查看 | 按模块和级别过滤的日志查看器 |
| 模块管理 | 查看、加载、卸载已安装的模块和适配器 |
| 模块商店 | 浏览远程可用包并一键安装 |
| 配置编辑 | 在线编辑 `config.toml` |
| 存储管理 | 浏览和编辑 Key-Value 存储数据 |
| 备份 | 导出/导入配置和存储数据 |
| 审计日志 | 记录所有管理操作 |

### 通过 Dashboard 安装模块

Dashboard 集成了模块商店功能，你可以：

1. **从商店安装**：浏览远程模块列表，选择需要的模块一键安装
2. **上传本地包**：直接上传 `.whl` 或 `.zip` 文件进行安装，方便测试个人开发的模块

> **模块开发者的快速测试流程**：使用 Docker 部署后，在 Dashboard 中通过「上传本地包」功能直接上传你构建的 `.whl` 文件进行测试，无需手动操作容器。

## 健康检查

SDK 内置健康检查端点：

```bash
# 简单检查
curl http://localhost:8000/ping

# 详细状态
curl http://localhost:8000/health
```

Docker 健康检查可在 `docker-compose.yml` 中添加：

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 反向代理

如果需要通过 Nginx 等反向代理暴露 Dashboard：

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

    # WebSocket 支持（Dashboard 实时事件流需要）
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL 可使用 Let's Encrypt：

```bash
sudo certbot --nginx -d bot.example.com
```

## 手动部署（pip）

如果不使用 Docker，也可以手动部署。

### 生产环境配置

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

创建 `/etc/systemd/system/erispulse-bot.service`：

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

管理：

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

创建 `/etc/supervisor/conf.d/erispulse-bot.conf`：

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

## 安全建议

1. **设置 Dashboard 令牌**：使用强随机令牌，不要使用默认值
2. **不要暴露端口到公网**：除非使用反向代理 + SSL，否则将 Dashboard 端口限制在内网
3. **保护数据目录**：`config/` 目录包含配置和数据库，设置适当的文件权限
4. **定期更新**：使用 `epsdk self-update` 或拉取最新 Docker 镜像
5. **不要以 root 运行**：手动部署时创建专用用户
6. **使用 Docker 重启策略**：`restart: unless-stopped` 确保异常退出后自动重启

## 多实例部署

运行多个机器人实例时：

1. 每个实例使用独立的项目目录和 `docker-compose.yml`
2. 使用不同的端口号：`ERISPULSE_PORT=8001`
3. 使用不同的容器名：`container_name: erispulse-bot2`

## 更新与维护

### Docker 方式

```bash
# 拉取最新镜像
docker compose pull

# 重启使用新镜像
docker compose up -d
```

### pip 方式

```bash
epsdk self-update
epsdk upgrade
```

### 备份

定期备份 `config/` 目录：

```bash
# Docker 部署
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# 或在 Dashboard 中使用「备份」功能导出
```
