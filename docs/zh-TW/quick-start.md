# 快速開始

> **這是你的第一步。** 用 5 分鐘從零跑起一個 ErisPulse 机器人。

## 安裝 ErisPulse

### 一鍵安裝腳本（推薦）

安裝腳本會自動檢測您的環境（Docker、Python、uv），並引導您選擇最適合的安裝方式。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

腳本會引導您完成：

- **Docker 安裝**（檢測到 Docker 時推薦）：選擇鏡像源（Docker Hub / GHCR）、版本通道（穩定版 / 預發布版）、Dashboard 管理面板配置、端口設置
- **傳統安裝**：自動創建虛擬環境、選擇 ErisPulse 版本、可選安裝 Dashboard 管理面板模塊

### 使用 Docker

Docker 鏡像已內置 ErisPulse 框架和 Dashboard 管理面板。

```bash
# 下載 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 設置 Dashboard 令牌並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub 不可用？</summary>

使用 GitHub Container Registry 鏡像，修改 `docker-compose.yml` 中的 image：

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

啟動後訪問 `http://<host>:8000/Dashboard`，使用設置的令牌登錄。

### 使用 pip 安裝

確保你的 Python 版本 >= 3.10，然後使用 pip 安裝：

```bash
pip install ErisPulse
```

如果你已安裝 [uv](https://github.com/astral-sh/uv)，也可以使用 `uv pip install ErisPulse`，安裝速度更快。

只想把 `epsdk` 命令行工具裝到全局、不污染項目環境時，推薦 `uv tool install`：

```bash
uv tool install ErisPulse
```

安裝後 `epsdk` 全局可用：在項目目錄內運行時會自動感知項目 `.venv`（`epsdk install` 裝進項目環境、`epsdk run` 用項目環境運行），框架本體由工具環境提供。詳見[安裝參考](user-guide/installation.md)。

## 初始化項目

### 交互式初始化（推薦）

```bash
epsdk init
```

這將啟動一個交互式向導，引導您完成：
- 項目名稱設置
- 日誌級別配置
- 伺服器配置（主機和端口）
- 適配器選擇和配置
- 項目結構創建

### 快速初始化

```bash
# 指定項目名稱的快速模式
epsdk init -q -n my_bot

# 或者只指定項目名稱
epsdk init -n my_bot
```

### 手動創建項目

如果更喜歡手動創建項目：

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## 安裝模塊

### 通過 CLI 安裝

```bash
epsdk install Yunhu AIChat
```

### 查看可用模塊

```bash
epsdk list-remote
```

### 交互式安裝

不指定包名時進入交互式安裝界面：

```bash
epsdk install
```

## 運行項目

```bash
# 普通運行
epsdk run main.py

# 熱重載模式（開發時推薦）
epsdk run main.py --reload
```

## 啟用 IDE 補全（可選）

ErisPulse 動態發現模塊/適配器，IDE 默认無法補全平台特有方法。  
運行以下命令生成類型存根：

```bash
epsdk types
```

生成後用導入的類型作為變量標註即可獲得精確補全（詳見 [IDE 補全指南](./getting-started/ide-completion.md)）：

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # 補全平台特有方法
```

## 項目結構

初始化後的項目結構：

```
my_bot/
├── config/
│   └── config.toml          # 配置文件
└── main.py                  # 入口文件

```

## 配置文件

基本的 `config.toml` 配置：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# 適配器配置
```

## 下一步

機器人跑起來後，你可以按需繼續：

**想了解框架怎麼運作?**
- [基礎概念](getting-started/basic-concepts.md) — 適配器 / 模塊 / 事件 的設計
- [架構概覽](architecture.md) — 可視化架構圖

**想實現更多功能?**
- [常見任務示例](getting-started/common-tasks.md) — 存儲、定時任務、權限控制
- [事件處理入門](getting-started/event-handling.md) — 消息、通知、請求處理

**想開發自己的模塊 / 適配器?**
- [模塊開發入門](developer-guide/modules/getting-started.md)
- [適配器開發入門](developer-guide/adapters/getting-started.md)

**按需查閱:**
- [配置文件說明](user-guide/configuration.md) · [CLI 命令](user-guide/cli-reference.md) · [部署指南](user-guide/deployment.md)