# 部署指南

將 ErisPulse 機器人部署到生產環境的最佳實踐。

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

再次提醒：如果文檔包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## Docker 部署（推薦）

ErisPulse 提供官方 Docker 鏡像，內建 ErisPulse 框架和 Dashboard 管理介面，支援 `linux/amd64` 和 `linux/arm64` 架構。

### 快速啟動

```bash
# 拉取鏡像
docker pull erispulse/erispulse:latest

# 下載 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 設定 Dashboard 登入令牌並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

啟動後，請前往 `http://localhost:8000/Dashboard`，使用設定的令牌作為密碼登入。

### 國內鏡像加速

如果 Docker Hub 無法存取，可以使用 GitHub Container Registry 拉取鏡像：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

使用 ghcr.io 鏡像時，需要修改 `docker-compose.yml` 中的 image：

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

### 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard 端口映射 |
| `ERISPULSE_DASHBOARD_TOKEN` | 自動產生 | Dashboard 登入令牌（強烈建議設定） |
| `TZ` | `Asia/Shanghai` | 時區 |

### 數據持久化

`./config` 目錄掛載了配置文件和資料庫，包含：

- `config/config.toml` — 配置文件
- `config/config.db` — SQLite 存儲資料庫
- `config/.packages` — Python site-packages 持久化卷，保存框架、適配器和已安裝模組（首次啟動時由入口點從鏡像內建備份自動初始化，之後的模組安裝與框架熱更新均寫入此目錄）

## Dashboard 管理介面

ErisPulse Docker 鏡像內建 Dashboard 模組，提供 Web 可視化管理介面。

### 功能概覽

| 功能 | 說明 |
|------|------|
| 介面板 | 系統概覽、CPU/記憶體監控、運行時間、事件統計 |
| 機器人管理 | 查看各平台機器人線上狀態和資訊 |
| 事件檢視 | 實時事件流，支援按類型和平台過濾 |
| 日誌檢視 | 按模組和層級過濾的日誌檢視器 |
| 模組管理 | 查看、載入、卸載已安裝的模組和適配器 |
| 模組商店 | 瀏覽遠端可用套件並一鍵安裝 |
| 配置編輯 | 在線編輯 `config.toml` |
| 儲存管理 | 瀏覽和編輯 Key-Value 儲存資料 |
| 備份 | 導出/匯入配置和儲存資料 |
| 審計日誌 | 記錄所有管理操作 |

### 透過 Dashboard 安裝模組

Dashboard 整合了模組商店功能，你可以：

1. **從商店安裝**：瀏覽遠端模組列表，選擇需要的模組一鍵安裝
2. **上傳本機套件**：直接上傳 `.whl` 或 `.zip` 檔案進行安裝，方便測試個人開發的模組

> **模組開發者的快速測試流程**：使用 Docker 部署後，在 Dashboard 中透過「上傳本機套件」功能直接上傳你建構的 `.whl` 檔案進行測試，無需手動操作容器。

## 進程監督與硬重啟

ErisPulse 的硬重啟（`sdk.hard_restart()`）依賴**外部監督者**在進程退出碼為 42 時重新拉起進程——SDK 自己不會拉起新進程。生產環境務必配置監督者，否則硬重啟後進程不會自動恢復：

- Docker：`restart: unless-stopped`（任何退出碼都會重啟，包含 42）
- systemd：`Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord：將 42 加入可重啟退出碼
- 純 Python 自定義監督者：循環 `Popen` + 檢測 `returncode == 42`

各監督者的完整配置示例與退出碼 42 契約說明見 [啟動流程 → 監督者指南](../advanced/startup.md#監督者指南)。

## 健康檢查

SDK 內建健康檢查端點：

```bash
# 健康檢查
curl http://localhost:8000/health
```

Docker 健康檢查可在 `docker-compose.yml` 中添加：

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），請務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 反向代理

如果需要透過 Nginx 等反向代理公開 Dashboard：

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

    # WebSocket 支援（Dashboard 即時事件流需要）
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

## 手動部署 (pip)

如果不使用 Docker，也可以手動部署。

### 生產環境配置

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

建立 `/etc/systemd/system/erispulse-bot.service`：

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

建立 `/etc/supervisor/conf.d/erispulse-bot.conf`：

```ini
[program:erispulse-bot]
command=/opt/erispulse-bot/venv/bin/python -m ErisPulse run main.py
directory=/opt/erispulse-bot
user=bot
autostart=true
autorestart=true
stderr_logfile=/var/log/erispulse-bot/err.log
stdout_logfile=/var/log/erispulse-bot/out.log

## 安全建議

1. **設定 Dashboard 令牌**：使用強大的隨機令牌，不要使用預設值
2. **不要將端口暴露到公網**：除非使用反向代理 + SSL，否則將 Dashboard 端口限制在內網
3. **保護資料目錄**：`config/` 目錄包含配置和資料庫，設定適當的檔案權限
4. **定期更新**：使用 `epsdk self-update` 或拉取最新的 Docker 鏡像
5. **不要以 root 運行**：手動部署時建立專用使用者
6. **使用 Docker 重啟策略**：`restart: unless-stopped` 確保異常退出後自動重啟

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 多實例部署

執行多個機器人實例時：

1. 每個實例使用獨立的專案目錄和 `docker-compose.yml`
2. 使用不同的端口號：`ERISPULSE_PORT=8001`
3. 使用不同的容器名：`container_name: erispulse-bot2`

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），請務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 更新與維護

### Docker 方式

```bash
# 拉取最新鏡像
docker compose pull

# 重啟並使用新鏡像
docker compose up -d
```

### pip 方式

```bash
epsdk self-update
epsdk upgrade
```

### 備份

定期備份 `config/` 目錄：

```bash
# Docker 部署
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# 或在 Dashboard 中使用「備份」功能導出
```

[**English**](../en-US/quick-start.md) | [**简体中文**](../zh-CN/quick-start.md)