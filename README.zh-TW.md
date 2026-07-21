<img src=".github/assets/mascot-hero.png" align="right" width="300" alt="ErisPulse" style="margin-left: 24px; margin-bottom: 16px; border-radius: 12px;" />

[English](README.md) | [简体中文](README.zh-CN.md) | **繁體中文** | [日本語](README.ja.md) | [Русский](README.ru.md)

# ErisPulse

**一次編寫，部署到 QQ / Telegram / Kook / Yunhu / 微信公眾號 / OneBot12 / ... 多個平台。**

事件驅動的多平台聊天機器人開發框架。

基於 OneBot12 標準接口，一次編寫多平台部署；靈活的插件系統、熱重載支持和完整的開發者工具鏈，適用於從簡單聊天機器人到複雜自動化系統的各種場景。

<p>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="https://hub.docker.com/r/erispulse/erispulse"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen" alt="Stars"></a>
  <a href="https://pepy.tech/project/ErisPulse"><img src="https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue" alt="Downloads"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge" alt="Ruff"></a>
  <a href="https://socket.dev/pypi/package/erispulse"><img src="https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white" alt="Socket"></a>
  <a href="https://www.erisdev.com"><img src="https://img.shields.io/badge/文件-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="文件"></a>
  <a href="https://deepwiki.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/DeepWiki-ErisPulse-8A2BE2?style=for-the-badge&logo=readthedocs&logoColor=white" alt="DeepWiki"></a>
  <a href="https://www.erisdev.com/#market"><img src="https://img.shields.io/badge/模組市場-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white" alt="模組市場"></a>
  <a href="https://github.com/ErisPulse/ErisPulse/discussions"><img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github" alt="討論"></a>
</p>

<br clear="both">

---

<div align="center">

### 核心特性

</div>

<table>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_event_driven.png.png" width="50" alt="事件驅動架構" />

### 事件驅動架構

基於 OneBot12 標準的統一事件模型——不再為每個平台寫一套 if/elif 判斷訊息類型，一份 handler 自動適配所有適配器

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_cross_platform.png.png" width="50" alt="跨平台相容" />

### 跨平台相容

同一份業務代碼在所有平台運行——一次編寫即可服務 QQ / Telegram / Kook / Yunhu / 微信公眾號 等 15+ 平台，無需重複開發

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_modular.png" width="50" alt="模組化設計" />

### 模組化設計

靈活的插件系統支援運行時熱插拔——安裝/卸載/啟用/禁用模組無需重啟進程，像搭積木一樣組裝機器人能力

</td>
</tr>
<tr>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_hot_reload.png" width="50" alt="熱重載" />

### 熱重載

開發循環從重啟 10 秒縮短到 0.5 秒——儲存文件即生效，開發調試體驗接近解釋型腳本語言

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_ai_assist.png" width="50" alt="AI 輔助" />

### AI 輔助

自然語言描述需求直接生成可用模組——不會寫適配器？告訴 AI 你要接入什麼平台，它幫你寫

</td>
<td width="33%" align="center" valign="top">
<br/>

<img src=".github/assets/icon/icon_lightweight.png" width="50" alt="簡潔優雅" />

### 簡潔優雅

直覺化的鏈式 API 設計——@用戶、回覆、重試、批量發送等複雜邏輯一行代碼完成，代碼如羽毛般輕盈可讀

</td>
</tr>
</table>

---

## 工作原理

ErisPulse 透過適配器層屏蔽平台差異，讓業務代碼只關心事件本身：

```mermaid
graph LR
    subgraph Platforms[平台]
        QQ["QQ"]
        TG["Telegram"]
        Kook["Kook"]
        YH["云湖"]
        WX["微信公眾號"]
    end

    subgraph Adapters[適配器層]
        A1["QQ 適配器"]
        A2["Telegram 適配器"]
        A3["Kook 適配器"]
        A4["云湖適配器"]
        A5["微信適配器"]
    end

    Event["Event 事件總線<br/>中間件 → 分發 command/message/notice/request/meta"]

    subgraph Modules[業務模組]
        M1["命令處理器<br/>@command"]
        M2["訊息處理器<br/>@message"]
        M3["你的模組"]
    end

    QQ --> A1
    TG --> A2
    Kook --> A3
    YH --> A4
    WX --> A5

    A1 -->|"OB12 事件"| Event
    A2 -->|"OB12 事件"| Event
    A3 -->|"OB12 事件"| Event
    A4 -->|"OB12 事件"| Event
    A5 -->|"OB12 事件"| Event

    Event -->|"分發"| M1
    Event -->|"分發"| M2
    Event -->|"分發"| M3

    M1 -.->|"event.reply()<br/>SendDSL"| Event
    Event -.->|"發送"| A1
```

- **適配器層**將各平台原生協議轉換為 OneBot12 標準事件，業務模組看不到平台差異
- **Event 總線**先執行中間件鏈，再按事件類型分發到五類處理器
- **你的代碼**透過裝飾器訂閱事件，用 `event.reply()` 或 SendDSL 回覆——回覆訊息沿同一條路徑逆流回平台

完整的模組組成、初始化流程、生命週期事件等設計細節，見[架構概覽](docs/zh-TW/architecture.md)。

---

## 快速開始

### 一鍵安裝腳本（推薦）

安裝腳本會自動偵測您的環境（Docker、Python、uv），引導選擇最適合的安裝方式，支援多語言（中文/English/日本語/Русский/繁體中文）。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

<table>
<tr>
<td align="center" width="50%">

**Docker 安裝示範**

<video src="https://github.com/user-attachments/assets/a367a466-4678-46a9-b101-073a86388ede" controls width="100%"></video>

</td>
<td align="center" width="50%">

**pip 安裝示範**

<video src="https://github.com/user-attachments/assets/a2df4009-dba6-411e-b79d-4454a168d063" controls width="100%"></video>

</td>
</tr>
</table>

### 使用 Docker (推薦)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub不可用？</summary>

如果 Docker Hub 無法存取，可以使用 GitHub Container Registry：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

使用 ghcr.io 鏡像時，需要修改 `docker-compose.yml` 中的 image：
```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

<details>
<summary>快速啟動</summary>

```bash
# 下載 docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# 設定 Dashboard 登入令牌並啟動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

> 鏡像內建 ErisPulse 框架和 Dashboard 管理介面，支援 `linux/amd64` 和 `linux/arm64` 架構。

啟動後存取 `http://<host>:<port>/Dashboard`，使用設定的令牌作為密碼登入 Dashboard 管理介面。

</details>

<details>
<summary>使用預發布版本 (Dev)</summary>

設定 `ERISPULSE_CHANNEL=dev` 即可使用預發布版本：

```bash
# 方式一：使用環境變數（推薦）
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# 方式二：建構 dev 鏡像
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

如需啟動時自動更新到最新版本（無論 stable 還是 dev），顯式設定 `ERISPULSE_UPDATE_ON_START=true`：

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

也可以拉取預建構的 dev 鏡像：

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker 環境變數</summary>

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | 版本通道：`stable`（穩定版）或 `dev`（預發布版） |
| `ERISPULSE_UPDATE_ON_START` | `false` | 容器啟動時是否自動更新到最新版本（需顯式啟用） |
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboard 登入令牌 |
| `ERISPULSE_PORT` | `8000` | Dashboard 端口映射 |
| `TZ` | `Asia/Shanghai` | 容器時區 |

> 啟用 `ERISPULSE_UPDATE_ON_START=true` 可確保即使鏡像較舊，容器也能在啟動時自動獲取最新版本。

</details>

### 1Panel 應用商店

透過 [1Panel](https://1panel.cn) 應用商店一鍵安裝 ErisPulse，詳見 [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel)。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

ErisPulse 已上架 1Panel 第三方應用商店，可使用 [okxlin/appstore](https://github.com/okxlin/appstore) 第三方倉庫安裝。

### 使用 pip 安裝

```bash
pip install ErisPulse
```

> 也可以使用上方的一鍵安裝腳本，自動偵測環境並引導配置。

### 初始化專案

```bash
# 互動式初始化
epsdk init

# 快速初始化（指定專案名稱）
epsdk init -q -n my_bot
```

### 創建第一個機器人

建立 `main.py` 檔案：

<table>
<tr>
<td width="50%" valign="top">

**命令處理器**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="發送問候訊息")
async def hello_handler(event):
    user_name = event.get_user_nickname() or "朋友"
    await event.reply(f"你好，{user_name}！")

@command("ping", help="測試機器人是否在線")
async def ping_handler(event):
    await event.reply("Pong！機器人運行正常。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

</td>
<td width="50%" valign="top">

**效果說明**

發送 `/hello`

機器人回覆：`你好，{使用者名稱}！`

---

發送 `/ping`

機器人回覆：`Pong！機器人運行正常。`

---

**運行方式**

```bash
epsdk run main.py
# 或開發模式
epsdk run main.py --reload
```

</td>
</tr>
</table>

更多詳細說明請參閱：
- [快速開始指南](docs/zh-TW/quick-start.md)
- [入門指南](docs/zh-TW/getting-started/)

---

## 同一份代碼。多個平台。

*完全相同的命令處理器。不同的平台。無需修改任何業務邏輯。*

<table>
<tr>
<td align="center" width="33%">

**Kook**

<img src=".github/assets/demo-kook.png" alt="Kook 演示" />

</td>
<td align="center" width="33%">

**QQ**

<img src=".github/assets/demo-qq.png" alt="QQ 演示" />

</td>
<td align="center" width="33%">

**云湖**

<img src=".github/assets/demo-yunhu.png" alt="云湖 演示" />

</td>
</tr>
</table>

---

## 鏈式發送 DSL

一條鏈式呼叫完成 @、回覆、重試、超時、回調等全部發送邏輯：

```python
yunhu = sdk.adapter.get("yunhu")

# 單發：@使用者 + 回覆 + 重試 + 成功回調
await (yunhu.Send.To("group", "123")
       .At("456").Reply("msg_789")
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("發送成功！"))
       .Text("你好"))

# 批量發送：一條鏈發多條訊息
results = await (yunhu.Send.To("user", "123")
                .Build()
                .Text("通知一")
                .Image("pic.jpg")
                .Retry(2)
                .send_all())
```

> 支援 Hook（成功回調）、Retry（失敗重試）、Timeout（超時取消）、OnProgress（進度監控）、Defer（延遲發送）、Build（批量建構）等鏈式方法，詳見 [SendDSL 文件](docs/zh-TW/developer-guide/adapters/send-dsl.md)。

---

## 多輪對話示例

ErisPulse 內建了強大的多輪對話引擎，輕鬆實現引導式操作、資訊收集等互動場景：

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("歡迎註冊！")
    
    # 多步驟收集使用者資訊，自動驗證
    data = await conv.collect([
        {"key": "name", "prompt": "請輸入姓名"},
        {"key": "age", "prompt": "請輸入年齡",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "年齡必須是數字，請重新輸入"},
    ])
    
    if data and await conv.confirm(f"確認註冊？姓名: {data['name']}, 年齡: {data['age']}"):
        # 透過 SendDSL 主動推送通知
        await sdk.adapter.get(event.get_platform()).Send.To(
            "user", event.get_user_id()
        ).Text(f"註冊成功！歡迎 {data['name']}")
        # 或 await event.reply("註冊成功！")

# 自動處理好友請求
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    
    # 同意請求
    result = await event.approve()
    if result.get("status") == "ok":
        await event.reply(f"已自動通過好友請求，歡迎 {user_name}")
```

<details>
<summary>查看更多 Conversation API（分支跳轉 / 選擇 / 持久化）</summary>

```python
@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)
    
    # 選項式問答
    answer = await conv.choose("Python 的創造者是誰？", [
        "Guido van Rossum",
        "James Gosling", 
        "Dennis Ritchie",
    ])
    
    if answer == 0:
        await conv.say("正確！")
    elif answer is None:
        await conv.say("超時了，下次再來吧！")
    else:
        await conv.say("錯誤了，正確答案是 Guido van Rossum")

@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)
    
    # 分支跳轉，建構複雜互動流程
    @conv.branch("main")
    async def main_menu():
        await conv.say("=== 主選單 ===\n1. 個人資訊\n2. 設定\n3. 退出")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "1":
            await conv.goto("profile")
    
    @conv.branch("profile")
    async def profile():
        await conv.say("姓名: Alice\n0. 返回")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")
    
    await conv.start()
```

詳見 [Conversation 多輪對話](docs/zh-TW/advanced/conversation.md)

</details>

---

## 核心模組

ErisPulse 提供完整的多平台機器人開發工具鏈，核心模組各司其職：

```mermaid
graph TB
    SDK["sdk<br/>統一入口"]

    SDK --> Event["Event<br/>事件系統"]
    SDK --> AdapterMgr["Adapter<br/>適配器管理"]
    SDK --> ModuleMgr["Module<br/>模組管理"]
    SDK --> Router["Router<br/>HTTP/WS 路由"]
    SDK --> Storage["Storage<br/>SQLite 存儲"]
    SDK --> Config["Config<br/>配置管理"]
    SDK --> Lifecycle["Lifecycle<br/>生命週期"]
    SDK --> Logger["Logger<br/>日誌系統"]
    SDK --> Client["HttpClient<br/>HTTP 客戶端"]
```

| 模組 | 說明 |
|------|------|
| **Event** | 事件系統，提供 command / message / notice / request / meta 五類事件 + Conversation 多輪對話 |
| **Adapter** | 適配器管理，BaseAdapter 基類統一事件轉換與 SendDSL 發送，支援 QQ / Telegram / Kook / 云湖 / 微信公眾號 等 15+ 平台 |
| **Module** | 模組管理，BaseModule 基類 + 依賴聲明與拓撲排序加載 |
| **SendDSL** | 鏈式發送，@/回覆/重試/超時/批量等複雜邏輯一行完成 |
| **Router** | HTTP/WebSocket 路由系統（FastAPI + Uvicorn）|
| **Storage** | 基於 SQLite 的鍵值存儲 + 通用 SQL 鏈式查詢 |
| **Config** | TOML 配置管理 |
| **Lifecycle** | 生命週期事件鈎子（core.init / adapter.* / module.*）|
| **Logger** | 模組化日誌系統，支援子日誌器 |
| **HttpClient** | 統一 HTTP/WS 客戶端（基於 aiohttp），內建重試與 ErisPulse 異常體系 |

更多設計細節（初始化流程、生命週期事件、模組加載策略），見[架構概覽](docs/zh-TW/architecture.md)。

---

## 生態

ErisPulse 不僅是框架。裝上就能開始，不需要從零造輪子。

<table>
<tr>
<td align="center" width="25%">

**框架**

核心執行時

統一事件 & 訊息模型

</td>
<td align="center" width="25%">

**Dashboard**

視覺化管理

插件 · 日誌 · 配置

[線上示範 →](https://dashdemo.erisdev.com/)

</td>
<td align="center" width="25%">

**AI Builder**

自然語言 → 可用模組

[立即體驗 →](https://www.erisdev.com/#builder)

</td>
<td align="center" width="25%">

**模組市場**

即裝即用的插件

[瀏覽模組 →](https://www.erisdev.com/#market)

</td>
</tr>
<tr>
<td align="center" width="25%">

**適配器**

15+ 平台接入

</td>
<td align="center" width="25%">

**文件**

[erisdev.com](https://www.erisdev.com)

</td>
<td align="center" width="25%">

**Docker**

多架構支援

`erispulse/erispulse`

</td>
<td align="center" width="25%">

**CLI**

`epsdk` 腳手架工具

</td>
</tr>
</table>

---

## 支援的平台

歡迎您貢獻適配器！

| 適配器 | 說明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（開黑啦）即時通訊平台 |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix 去中心化通訊協定 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 通用機器人協定 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 標準協定 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ 官方機器人平台 |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | 網頁端調試，無需接入真實平台 |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | 全球性即時通訊平台 |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [郵件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | 郵件協定收發適配器 |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業級即時通訊平台（機器人接入） |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [云湖使用者](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 基於云湖使用者協定的接入適配器 |
| [花楓咖啡館](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |
| <img src=".github/assets/adapter_logo/discord.svg" height="20" alt="Discord" /> [Discord](https://github.com/ErisPulse/ErisPulse-DiscordAdapter) | 全球性社群通訊平台，支援伺服器、頻道、私訊 |
| <img src=".github/assets/adapter_logo/webhook.svg" height="20" alt="Webhook" /> [Webhook](https://github.com/ErisPulse/ErisPulse-WebhookAdapter) | 通用 HTTP 橋接適配器，對接任意系統 |
| <img src=".github/assets/adapter_logo/wechatmp.svg" height="20" alt="WechatMp" /> [微信公眾號](https://github.com/ErisPulse/ErisPulse-WechatMpAdapter) | 微信官方公眾號平台 |

查看 [適配器詳情介紹](docs/zh-TW/platform-guide/README.md)

---

## 社區

與我們交流：

- Telegram：<https://t.me/ErisPulse>
- QQ 群：<https://qm.qq.com/q/TOwnCmypcy>
- 云湖群：<https://yhfx.jwznb.com/share?key=VWJL4fTWXepa&ts=1781889199>

---

### 貢獻指南

ErisPulse 項目的健全性還需要您的一份力！我們歡迎各種形式的貢獻：

1. **報告問題** — 在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交 bug 報告
2. **功能請求** — 透過 [社區討論](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法
3. **代碼貢獻** — 提交 PR 前請閱讀 [代碼風格](docs/zh-TW/styleguide/) 及 [貢獻指南](CONTRIBUTING.md)
4. **文件改進** — 幫助完善文件和範例代碼

[加入社區討論](https://github.com/ErisPulse/ErisPulse/discussions)

---

<div align="center">

### 致謝

<img src=".github/assets/thanks.png" width="200" alt="感謝" />

本專案部分代碼基於 [sdkFrame](https://github.com/runoneall/sdkFrame)。

核心適配器標準化層參考並受益於 [OneBot12 規範](https://12.onebot.dev/)。

特別感謝云湖生態與社區。

ErisPulse 的早期探索與成長離不開云湖開發者社區的支持，
許多想法、適配器和實踐經驗都誕生於此。

同時感謝所有為 ErisPulse、OneBot 生態以及開源社區做出貢獻的開發者與專案作者。

</div>