# 快速開始

> **這是你的第一步。** 用 5 分鐘從零跑起一個 ErisPulse 機器人。
>
> 遇到不理解術語?查看 [術語表](terminology.md)。

## 安裝 ErisPulse

### 一鍵安裝腳本（推薦）

安裝腳本會自動偵測您的環境（Docker、Python、uv），並引導您選擇最適合的安裝方式。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

腳本會引導您完成：

- **Docker 安裝**（偵測到 Docker 時推薦）：選擇映像來源（Docker Hub / GHCR）、版本通道（穩定版 / 預發布版）、Dashboard 管理面板配置、埠設置
- **傳統安裝**：自動建立虛擬環境、選擇 ErisPulse 版本、可選安裝 Dashboard 管理面板模組

### 使用 Docker

Docker 映像已內建 ErisPulse 框架和 Dashboard 管理面板。

```bash
# 下載 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 設置 Dashboard 令牌並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub 不可用？</summary>

使用 GitHub Container Registry 映像，修改 `docker-compose.yml` 中的 image：

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

啟動後訪問 `http://<host>:8000/Dashboard`，使用設置的令牌登入。

### 使用 pip 安裝

確保你的 Python 版本 >= 3.10，然後使用 pip 安裝：

```bash
pip install ErisPulse
```

如果你已安裝 [uv](https://github.com/astral-sh/uv)，也可以使用 `uv pip install ErisPulse`，安裝速度更快。

## 初始化專案

### 互動式初始化（推薦）

```bash
epsdk init
```

這將啟動一個互動式嚮導，引導您完成：
- 專案名稱設置
- 日誌級別配置
- 伺服器配置（主機和埠）
- 适配器選擇和配置
- 專案結構建立

### 快速初始化

```bash
# 指定專案名稱的快速模式
epsdk init -q -n my_bot

# 或者只指定專案名稱
epsdk init -n my_bot
```

### 手動建立專案

如果更喜歡手動建立專案：

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## 安裝模組

### 通過 CLI 安裝

```bash
epsdk install Yunhu AIChat
```

### 查看可用模組

```bash
epsdk list-remote
```

### 互動式安裝

不指定套件名稱時進入互動式安裝介面：

```bash
epsdk install
```

## 執行專案

```bash
# 普通執行
epsdk run main.py

# 熱重載模式（開發時推薦）
epsdk run main.py --reload
```

## 啟用 IDE 補全（可選）

ErisPulse 動態發現模組/适配器，IDE 預設無法補全平台特有方法。
執行以下命令生成類型存根：

```bash
epsdk types
```

生成後用導入的類型作為變數註解即可獲得精確補全（詳見 [IDE 補全指南](./getting-started/ide-completion.md)）：

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # 補全平台特有方法
```

## 專案結構

初始化後的專案結構：

```
my_bot/
├── config/
│   └── config.toml          # 配置檔
└── main.py                  # 入口檔

```

## 配置檔

基本的 `config.toml` 配置：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# 适配器配置
```

## 下一步

機器人跑起來後，你可以按需繼續：

**想了解框架怎麼運作?**
- [基礎概念](getting-started/basic-concepts.md) — 适配器 / 模組 / 事件 的設計
- [架構概覽](architecture.md) — 可視化架構圖

**想實現更多功能?**
- [常見任務示例](getting-started/common-tasks.md) — 儲存、定時任務、權限控制
- [事件處理入門](getting-started/event-handling.md) — 訊息、通知、請求處理

**想開發自己的模組 / 适配器?**
- [模組開發入門](developer-guide/modules/getting-started.md)
- [适配器開發入門](developer-guide/adapters/getting-started.md)

**按需查閱:**
- [配置檔說明](user-guide/configuration.md) · [CLI 命令](user-guide/cli-reference.md) · [部署指南](user-guide/deployment.md)