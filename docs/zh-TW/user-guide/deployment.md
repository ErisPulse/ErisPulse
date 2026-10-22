# 部署指南

> [!TIP]
> **什麼時候需要讀這篇**：機器人要長期掛著跑時——Docker 部署、systemd / Supervisor 程序守護、反向代理與 SSL、備份與升級都在這裡。本地開發除錯階段不需要則跳過。

機器人開發完只是開始。這篇涵蓋把它穩定掛在伺服器上所需的三種部署方式（Docker / systemd / Supervisor），以及反向代理、安全強化與備份。

## Docker 部署（推薦）

ErisPulse 提供官方 Docker 映像，內建 ErisPulse 框架和 Dashboard 管理面板，支援 `linux/amd64` 和 `linux/arm64` 架構。

### 快速啟動

```bash
# 拉取映像
docker pull erispulse/erispulse:latest

# 下載 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 設定 Dashboard 登入權杖並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

啟動後存取 `http://localhost:8000/Dashboard`，使用設定的權杖作為密碼登入。

### 國內映像加速

如果 Docker Hub 無法存取，可以使用 GitHub Container Registry 拉取映像：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

使用 ghcr.io 映像時，需要修改 `docker-compose.yml` 中的 image：

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
      # 持久化 Python 套件目錄
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - LANG=${LANG:-en_US.UTF-8}
      - ERISPULSE_LANG=${ERISPULSE_LANG:-}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    # 優雅停機由框架內訊號處理完成（SIGTERM），此處僅控制寬限時長
    stop_grace_period: 30s
    restart: on-failure:5
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

> 以上與儲存庫根目錄的 [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) 保持一致（儲存庫版本開頭另有映像加速與環境變數說明註解），推薦直接下載使用。

### 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard 連接埠映射 |
| `ERISPULSE_TAG` | `latest` | 映像 tag（如需鎖定版本可設為具體版本號） |
| `CONTAINER_NAME` | `erispulse` | 容器名稱（多實例部署時區分實例） |
| `ERISPULSE_DASHBOARD_TOKEN` | 自動產生 | Dashboard 登入權杖（強烈建議設定） |
| `TZ` | `Asia/Shanghai` | 時區 |
| `LANG` | `en_US.UTF-8` | 系統語言，自動偵測啟動介面語言 |
| `ERISPULSE_LANG` | 空 | 強制啟動介面語言：`zh` / `zh_TW` / `en` / `ja` / `ru`（覆寫 `LANG`） |

### 資料持久化

`./config` 目錄掛載了設定檔和資料庫，包含：

- `config/config.toml` — 設定檔
- `config/config.db` — SQLite 儲存資料庫
- `config/.packages` — Python site-packages 持久化卷，儲存框架、配接器和已安裝模組（首次啟動時由入口點從映像內建備份自動初始化，之後的模組安裝與框架熱更新均寫入此目錄）

> **框架升級（含 pre/rc）與映像自癒**：入口點會在每次容器啟動時做核心套件完整性自我檢查，
> 損壞時按「使用者已安裝版本優先」原則修復——持久卷內顯式安裝/升級的版本
> （如 Dashboard 安裝的 pre 版本）會從 PyPI **重裝同版本**，絕不靜默回退到
> 映像內建版本。因此 Dashboard 升級框架後，任意次容器重啟都應保持目標版本。

## Dashboard 管理面板

ErisPulse Docker 映像內建 Dashboard 模組，提供 Web 視覺化管理介面。

### 功能概覽

| 功能 | 說明 |
|------|------|
| 儀表板 | 系統概覽、CPU/記憶體監控、執行時長、事件統計 |
| 機器人管理 | 查看各平台機器人線上狀態和資訊 |
| 事件查看 | 即時事件流，支援按類型和平台篩選 |
| 日誌查看 | 按模組和層級篩選的日誌檢視器 |
| 模組管理 | 查看、載入、卸載已安裝的模組和配接器 |
| 模組商店 | 瀏覽遠端可用套件並一鍵安裝 |
| 設定編輯 | 線上編輯 `config.toml` |
| 儲存管理 | 瀏覽和編輯 Key-Value 儲存資料 |
| 備份 | 匯出/匯入設定和儲存資料 |
| 稽核日誌 | 記錄所有管理操作 |

### 透過 Dashboard 安裝模組

Dashboard 整合了模組商店功能，你可以：

1. **從商店安裝**：瀏覽遠端模組清單，選擇需要的模組一鍵安裝
2. **上傳本地套件**：直接上傳 `.whl` 或 `.zip` 檔案進行安裝，方便測試個人開發的模組

> **模組開發者的快速測試流程**：使用 Docker 部署後，在 Dashboard 中透過「上傳本地套件」功能直接上傳你建置的 `.whl` 檔案進行測試，無需手動操作容器。

## 程序監督與硬重啟

ErisPulse 的硬重啟（`sdk.hard_restart()`）依賴**外部監督者**在程序結束碼為 42 時重新拉起程序——SDK 自己不會拉起新程序。正式環境務必設定監督者，否則硬重啟後程序不會自動恢復：

- Docker：官方 compose 使用 `restart: on-failure:5`——非零結束碼即重啟（覆寫硬重啟的結束碼 42），連續 5 次上限防死循環；需要不限次數可自行改為 `unless-stopped`
- systemd：`Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord：將 42 加入可重啟結束碼
- 純 Python 自訂監督者：以迴圈 `Popen` + 偵測 `returncode == 42`

各監督者的完整設定範例與結束碼 42 契約說明見 [啟動流程 → 監督者指南](../advanced/startup.md#監督者指南)。

## 健康檢查

SDK 內建健康檢查端點：

```bash
# 健康檢查
curl http://localhost:8000/health
```

官方 docker-compose.yml 已內建以下健康檢查；自行撰寫 compose 檔案時可參考：

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
```

## 手動部署（pip）

如果不使用 Docker，也可以手動部署。

### 正式環境設定

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
```

### uv tool 分離部署（CLI 與專案環境隔離）

`uv tool install` 會將 `epsdk` 安裝為**獨立的工具環境**，CLI 自身與專案依賴徹底隔離：升級 CLI 不會動到專案 `.venv`，專案依賴變動也不會影響 CLI。

```bash
# 1. 全域安裝 CLI（自動提供 epsdk / ep 指令）
uv tool install ErisPulse

# 2. 專案內只放機器人依賴（.venv 由 uv 管理）
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # 依需求追加配接器

# 3. 用 CLI 執行（自動偵測並使用專案 .venv 中的直譯器）
epsdk run main.py
```

行為要點：

- `epsdk run` 的目標直譯器解析順序：`ERISPULSE_PYTHON` 環境變數 → 專案 `.venv` → 當前直譯器；工具環境本身只承載 CLI，元件（配接器/模組）應裝進專案 `.venv`
- `epsdk install` / `uninstall` / `upgrade` / `list` 同樣作用於專案 `.venv`，不會污染工具環境
- 升級 CLI：`uv tool upgrade ErisPulse`（或直接 `epsdk self-update`，uv tool 環境下會自動改走 `uv tool upgrade`）；升級專案依賴：在專案目錄執行 `uv sync` / `uv add`，兩者互不影響
- 伺服器情境下工具環境由 uv 統一管理（`uv tool list` 查看、`uv tool upgrade --all` 批次升級），無需手動維護全域 pip 套件
- 若在無專案的目錄用 `uv run epsdk ...` 執行，會落入**一次性隔離環境**（安裝的元件不會持久化）；伺服器上請一律直接呼叫 `epsdk`，或先 `cd` 進專案目錄

## 安全建議

1. **設定 Dashboard 權杖**：使用強隨機權杖，不要使用預設值
2. **不要將連接埠公開到公網**：除非使用反向代理 + SSL，否則將 Dashboard 連接埠限制在內網
3. **保護資料目錄**：`config/` 目錄包含設定和資料庫，設定適當的檔案權限
4. **定期更新**：使用 `epsdk self-update` 或拉取最新 Docker 映像
5. **不要以 root 執行**：手動部署時建立專用使用者
6. **使用 Docker 重啟策略**：官方 compose 的 `restart: on-failure:5` 已確保異常結束（含硬重啟結束碼 42）後自動重啟

## 多實例部署

執行多個機器人實例時：

1. 每個實例使用獨立的專案目錄和 `docker-compose.yml`
2. 使用不同的連接埠號：`ERISPULSE_PORT=8001`
3. 使用不同的容器名稱：`container_name: erispulse-bot2`

## 更新與維護

### Docker 方式

```bash
# 拉取最新映像
docker compose pull

# 重啟以使用新映像
docker compose up -d
```

### pip 方式

```bash
epsdk self-update
epsdk upgrade
```

### uv tool 方式

```bash
# 升級 CLI 工具環境
uv tool upgrade ErisPulse

# 升級專案依賴（在專案目錄內執行）
uv sync
```

### 執行時熱重載伺服器設定

修改監聽位址 / 連接埠 / SSL 憑證後無需重啟程序，在任意協程中呼叫 `router.reload()`：

```python
await sdk.router.reload(port=9000)                                # 換連接埠
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # 熱更換憑證（憑證續期情境）
await sdk.router.reload(host="0.0.0.0", port=9000)                # 未指定的參數沿用當前設定
```

- 重用同一 FastAPI 應用程式，模組註冊的 HTTP / WebSocket / SSE 路由全部保留
- 先驗證新設定（憑證可建置、連接埠可用）再切換；失敗時以舊設定恢復服務並回傳 `False`，
  保證回傳 `False` = 舊服務保持可用
- 伺服器未執行時回傳 `False`（首次啟動請使用 `sdk.router.start()`）

### 備份

定期備份 `config/` 目錄：

```bash
# Docker 部署
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# 或在 Dashboard 中使用「備份」功能匯出
```

## 下一步

- **部署完想視覺化管理**：裝 [ErisPulse-Dashboard](../ecosystem/dashboard.md)，在瀏覽器裡管模組、看日誌、改設定
- **懷疑環境有問題**：先跑 `epsdk doctor` 輸出健康報告，見 [CLI 指令參考 · doctor](cli-reference.md#doctor)
- **要調整框架與元件設定**：查 [設定檔說明](configuration.md)，環境變數覆寫尤其適合容器部署