# 快速開始

> 遇到不理解的術語？查看 [術語表](terminology.md) 獲取通俗易懂的解釋。

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

## 初始化項目

### 交互式初始化（推薦）

```bash
epsdk init
```

這將啟動一個交互式向導，引導您完成：

- 項目名稱設置
- 日誌級別配置
- 伺服器配置（主機和端口）
- 适配器選擇和配置
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

ErisPulse 動態發現模塊/适配器，IDE 默认無法補全平台特有方法。  
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
# 适配器配置
```

## 下一步

- [入門指南總覽](getting-started/README.md) - 了解 ErisPulse 的基本概念
- [創建第一個機器人](getting-started/first-bot.md) - 創建一個簡單的機器人
- [用戶使用指南](user-guide/) - 深入了解配置和模塊管理
- [開發者指南](developer-guide/) - 開發自定義模塊和适配器