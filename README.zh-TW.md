<table>
<tr>
<td width="35%" valign="middle" align="center">

<img src=".github/assets/mascot-hero.png" width="320" alt="ErisPulse" />

</td>
<td valign="middle">

[English](README.en.md) | [简体中文](README.md) | **繁體中文** | [日本語](README.ja.md) | [Русский](README.ru.md)

# ErisPulse

**事件驅動的多平台機器人開發框架**

基於 OneBot12 標準介面，一次編寫，多平台部署。靈活的模組系統、熱重載支援和完整的開發者工具鏈，適用於從簡單聊天機器人到複雜自動化系統的各種場景。

> 支援 Vibe Coding 工作流，讓 AI 直接生成可用模組 — [查看](docs/zh-TW/ai-support/README.md)

[![PyPI](https://img.shields.io/pypi/v/ErisPulse?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ErisPulse/)
[![Python](https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://pypi.org/project/ErisPulse/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/erispulse/erispulse)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](https://github.com/ErisPulse/ErisPulse/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/ErisPulse/ErisPulse?style=for-the-badge&logo=github&color=brightgreen)](https://github.com/ErisPulse/ErisPulse)
[![Downloads](https://img.shields.io/pepy/dt/ErisPulse?style=for-the-badge&color=blue)](https://pypi.org/project/ErisPulse/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=for-the-badge)](https://github.com/astral-sh/ruff)
[![Socket](https://img.shields.io/badge/Socket-Secure-2ea043?style=for-the-badge&logo=socket&logoColor=white)](https://socket.dev/pypi/package/erispulse)

[![文檔](https://img.shields.io/badge/文檔-erisdev.com-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white)](https://www.erisdev.com)
[![模組市場](https://img.shields.io/badge/模組市場-erisdev.com-C724B1?style=for-the-badge&logo=webpack&logoColor=white)](https://www.erisdev.com/#market)
[![討論](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github)](https://github.com/ErisPulse/ErisPulse/discussions)

</td>
</tr>
</table>

---

<div align="center">

### 核心特性

</div>

<table>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### ⚡ 事件驅動架構

基於 OneBot12 標準的清晰事件模型，讓訊息處理邏輯更加直觀和高效

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🌐 跨平台相容

模組編寫一次即可在所有平台使用，無需為不同平台重複開發

</td>
</tr>
<tr>
<td width="50%" align="center" valign="top">
<br/>

### 🧩 模組化設計

靈活的模組系統，易於擴展和整合，支援熱插拔模組管理

</td>
<td width="50%" align="center" valign="top">
<br/>

### 🔄 熱重載支援

開發時無需重啟即可重新載入代碼，大幅提升開發迭代效率

</td>
</tr>
</table>

---

### 快速開始

#### 一鍵安裝腳本（推薦）

安裝腳本會自動檢測您的環境（Docker、Python、uv），引導選擇最適合的安裝方式，支援多語言（中文/English/日本語/Русский/繁體中文）。

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

**Docker 安裝演示**

<video src="https://github.com/user-attachments/assets/a367a466-4678-46a9-b101-073a86388ede" controls width="100%"></video>

</td>
<td align="center" width="50%">

**pip 安裝演示**

<video src="https://github.com/user-attachments/assets/a2df4009-dba6-411e-b79d-4454a168d063" controls width="100%"></video>

</td>
</tr>
</table>

#### 使用 Docker (推薦)

```bash
docker pull erispulse/erispulse:latest
```

<details>
<summary>Docker Hub不可用？</summary>

如果 Docker Hub 無法訪問，可以使用 GitHub Container Registry：

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

> 鏡像內建 ErisPulse 框架和 Dashboard 管理面板，支援 `linux/amd64` 和 `linux/arm64` 架構。

啟動後訪問 `http://<host>:<port>/Dashboard`，使用設定的令牌作為密碼登入 Dashboard 管理面板。

</details>

<details>
<summary>使用預發布版本 (Dev)</summary>

設置 `ERISPULSE_CHANNEL=dev` 即可使用預發布版本：

```bash
# 方式一：使用環境變數（推薦）
ERISPULSE_CHANNEL=dev ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d

# 方式二：建置 dev 鏡像
ERISPULSE_BUILD_TARGET=dev docker compose up -d --build
```

如需啟動時自動更新到最新版本（無論 stable 還是 dev），顯式設置 `ERISPULSE_UPDATE_ON_START=true`：

```bash
ERISPULSE_CHANNEL=dev ERISPULSE_UPDATE_ON_START=true docker compose up -d
```

也可以拉取預建置的 dev 鏡像：

```bash
docker pull erispulse/erispulse:dev
```

</details>

<details>
<summary>Docker 環境變量</summary>

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ERISPULSE_CHANNEL` | `stable` | 版本通道：`stable`（穩定版）或 `dev`（預發布版） |
| `ERISPULSE_UPDATE_ON_START` | `false` | 容器啟動時是否自動更新到最新版本（需顯式啟用） |
| `ERISPULSE_DASHBOARD_TOKEN` | 空 | Dashboard 登入令牌 |
| `ERISPULSE_PORT` | `8000` | Dashboard 埠對映 |
| `TZ` | `Asia/Shanghai` | 容器時區 |

> 啟用 `ERISPULSE_UPDATE_ON_START=true` 可確保即使鏡像較舊，容器也能在啟動時自動獲取最新版本。

</details>

#### 1Panel 應用商店

透過 [1Panel](https://1panel.cn) 應用商店一鍵安裝 ErisPulse，詳見 [ErisPulse-1Panel](https://github.com/ErisPulse/ErisPulse-1Panel)。

```bash
bash <(curl -sL https://get-1panel.erisdev.com/install.sh)
```

#### 使用 pip 安裝

```bash
pip install ErisPulse
```

> 也可以使用上方的一鍵安裝腳本，自動檢測環境並引導配置。

#### 運行效果


##### 儀表盤：

[![線上示範](https://img.shields.io/badge/線上示範-Dashboard-FF6B9D?style=for-the-badge&logo=github&logoColor=white)](https://dashdemo.erisdev.com/)

> 💡 線上體驗示範儀表盤：[DashDemo](https://dashdemo.erisdev.com/)

<table>
<tr>
<td width="50%">

<img src=".github/assets/docs/dashboard.png" alt="Dashboard 演示" />

</td>
<td width="50%">

<video src="https://github.com/user-attachments/assets/157191c4-9a84-433c-b311-0c57e3a21151" controls width="100%"></video>

</td>
</tr>
</table>


##### 同一端代碼，多個平台響應：

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

**雲湖**

<img src=".github/assets/demo-yunhu.png" alt="雲湖 演示" />

</td>
</tr>
</table>

#### 初始化項目

```bash
# 交互式初始化
epsdk init

# 快速初始化（指定項目名稱）
epsdk init -q -n my_bot
```

#### 創建第一個機器人

創建 `main.py` 文件：

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

機器人回覆：`你好，{用戶名}！`

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

#### 多輪對話示例

ErisPulse 內建了強大的多輪對話引擎，輕鬆實現引導式操作、資訊收集等交互場景：

```python
from ErisPulse.Core.Event import command, request

@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("歡迎註冊！")
    
    # 多步驟收集用戶資訊，自動驗證
    data = await conv.collect([
        {"key": "name", "prompt": "請輸入姓名"},
        {"key": "age", "prompt": "請輸入年齡",
         "validator": lambda e: e.get_text().strip().isdigit(),
         "retry_prompt": "年齡必須是數字，請重新輸入"},
    ])
    
    if data and await conv.confirm(f"確認註冊？姓名: {data['name']}, 年齡: {data['age']}"):
        # 通過 SendDSL 主動推送通知
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
    
    # 分支跳轉，構建複雜交互流程
    @conv.branch("main")
    async def main_menu():
        await conv.say("=== 主菜單 ===\n1. 個人資訊\n2. 設定\n3. 退出")
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

### 支援的適配器

歡迎您貢獻適配器！

| 適配器 | 說明 |
|--------|------|
| <img src=".github/assets/adapter_logo/kook.svg" height="20" alt="Kook" /> [Kook](https://github.com/shanfishapp/ErisPulse-KookAdapter) | Kook（開黑啦）即時通訊平台 |
| <img src=".github/assets/adapter_logo/matrix.svg" height="20" alt="Matrix" /> [Matrix](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) | Matrix 去中心化通訊協議 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot11](https://github.com/ErisPulse/ErisPulse-OneBot11Adapter) | OneBot v11 通用機器人協議 |
| <img src=".github/assets/adapter_logo/onebot.png" height="20" alt="OneBot" /> [OneBot12](https://github.com/ErisPulse/ErisPulse-OneBot12Adapter) | OneBot v12 標準協議 |
| <img src=".github/assets/adapter_logo/qqbot.svg" height="20" alt="QQ" /> [QQ](https://github.com/ErisPulse/ErisPulse-QQBotAdapter) | QQ 官方機器人平台 |
| <img src=".github/assets/adapter_logo/sandbox.png" height="20" alt="Sandbox" /> [沙箱](https://github.com/ErisPulse/ErisPulse-SandboxAdapter) | 網頁端調試，無需接入真實平台 |
| <img src=".github/assets/adapter_logo/telegram.svg" height="20" alt="Telegram" /> [Telegram](https://github.com/ErisPulse/ErisPulse-TelegramAdapter) | 全球性即時通訊平台 |
| <img src=".github/assets/adapter_logo/email.svg" height="20" alt="Email" /> [郵件](https://github.com/ErisPulse/ErisPulse-EmailAdapter) | 郵件協議收發適配器 |
| <img src=".github/assets/adapter_logo/yunhu.png" height="20" alt="Yunhu" /> [雲湖](https://github.com/ErisPulse/ErisPulse-YunhuAdapter) | 企業級即時通訊平台（機器人接入） |
| [雲湖用戶](https://github.com/wsu2059q/ErisPulse-YunhuUserAdapter) | 基於雲湖用戶協議的接入適配器 |
| [花楓咖啡館](https://github.com/ErisPulse/ErisPulse-Ideaura/) | Allons! \(・ω・) / |

查看 [適配器詳情介紹](docs/zh-TW/platform-guide/README.md)

---

### 應用場景

<div align="center">

| 多平台機器人 | 聊天助手 | 自動化工具 | 訊息轉發 |
|:---:|:---:|:---:|:---:|
| 在多個平台部署<br>相同功能的機器人 | 接入 AI 聊天模組<br>實現娛樂和交互 | 訊息通知、任務管理<br>資訊收集 | 跨平台訊息<br>同步和轉發 |

</div>

---

### 貢獻指南

ErisPulse 項目的健全性還需要您的一份力！我們歡迎各種形式的貢獻：

1. **報告問題** — 在 [GitHub Issues](https://github.com/ErisPulse/ErisPulse/issues) 提交 bug 報告
2. **功能請求** — 透過 [社區討論](https://github.com/ErisPulse/ErisPulse/discussions) 提出新想法
3. **代碼貢獻** — 提交 PR 前請閱讀 [代碼風格](docs/zh-TW/styleguide/) 及 [貢獻指南](CONTRIBUTING.md)
4. **文檔改進** — 幫助完善文檔和示例代碼

[加入社區討論](https://github.com/ErisPulse/ErisPulse/discussions)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ErisPulse/ErisPulse&type=Date)](https://star-history.com/#ErisPulse/ErisPulse&Date)

---

<div align="center">

### 致謝

<img src=".github/assets/thanks.png" width="200" alt="感謝" />

本項目部分代碼基於 [sdkFrame](https://github.com/runoneall/sdkFrame) · 核心適配器標準化層基於 [OneBot12 規範](https://12.onebot.dev/) · 感謝所有為開源社區做出貢獻的開發者和作者

</div>