# 生態模組

ErisPulse 框架本身只提供核心能力（事件系統、模組系統、配置、路由、日誌等），**不內建** GUI、圖片渲染、可視化等「重型」功能。這些能力由社區維護的 **第三方模組** 提供，按需安裝即可。

> [!IMPORTANT]
> 本目錄下的文件分為兩類，安裝方式不同：
>
> - **模組**（如 Dashboard / Takumi）使用 `epsdk install` 安裝：
>
>   ```bash
>   epsdk install <模組名>
>   ```
>
> - **獨立程式**（如 ErisPulse-App 客戶端）直接從對應 GitHub Releases 下載安裝，無需 `epsdk`。
>
> - **線上服務**（如 ErisPulse 工作台）無需安裝，打開網頁登入即可使用。

---

## 推薦模組

### ErisPulse-Dashboard：瀏覽器裡的管理介面

機器人掛在伺服器上，啟停模組、改配置、看日誌還得登終端？Dashboard 把這些搬進瀏覽器：模組啟停、配置編輯、日誌查看、事件監控；其他模組還能向側邊欄註冊自定義視窗，管理頁面集中在同一處。

```bash
epsdk install Dashboard
```

文件：[Dashboard 使用與視窗註冊](dashboard.md) ｜ 項目首頁：[PyPI](https://pypi.org/project/ErisPulse-Dashboard/)

### ErisPulse-Cron：定時任務

要每天定時發簽到提醒、按 Cron 表達式跑週期任務、每隔幾分鐘輪詢一次資料？Cron 提供一次性 / 间隔 / Cron 表達式三種任務類型，回調傳參，SQLite 持久化（重啟不丟任務）。

```bash
epsdk install Cron
```

文件：[Cron 定時任務](cron.md) ｜ 項目首頁：[GitHub](https://github.com/wsu2059q/ErisPulse-Cron)

### ErisPulse-QvQChat：通用智能體

想讓群裡有一個會工作的 AI 助手，而不是只會關鍵詞回覆？QvQChat 是通用智能體：工具循環覆蓋收發訊息 / 程式碼執行 / 電腦操作 / 產生圖片 / 語音 / MCP / 子智能體，支援流式對話與串行工具回放，內建 Dashboard 視窗。還有 QvQStalker（旁聽插話）、QvQMemes（表情包）、QvQCompanion（擬人陪伴）三個配套插件。

```bash
epsdk install ErisPulse-QvQChat
```

文件：[QvQChat 智能體](qvqchat.md) ｜ 項目首頁：[GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-ApiMCP：讓 AI 客戶端操控機器人

在用 Claude Desktop、Claude Code 這類支援 MCP 的 AI 客戶端？ApiMCP 把機器人運行時反向開放成 17 個 MCP 工具：AI 可以直接替你收發訊息、呼叫已裝模組、查看平台狀態、訂閱群聊事件——機器人變成 AI 的「手和眼」。

```bash
epsdk install ErisPulse-ApiMCP
```

文件：[ApiMCP 使用指南](apimcp.md) ｜ 項目首頁：[GitHub](https://github.com/wsu2059q/ErisPulse-ApiMCP)

### ErisPulse-Takumi：圖片渲染

排行榜、戰報、日程卡這類要「發圖」的場景，寫個模板渲染成圖片發進群裡即可：支援 HTML / 節點樹 / Jinja / SVG / 動畫（基於 [takumi-py](https://github.com/BalconyJH/takumi-py)），內建中英文字型，開箱即用。

```bash
epsdk install Takumi
```

文件：[Takumi 圖片渲染](takumi.md) ｜ 項目首頁：[GitHub](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)）

## 官方客戶端（獨立程式）

### ErisPulse-App：手機上直接跑機器人

沒有常開的伺服器，也想隨時建立實例、安裝模組、看事件流？ErisPulse-App 是官方全平台客戶端（Android / Windows / Linux / macOS）：原生介面建立 / 運行 / 管理多個機器人實例，內建模組商店與事件建構器，**手機直接運行**，桌面托盤常駐。

所有平台的安裝包均從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下載，無需 `epsdk`。

文件：[ErisPulse-App 安裝與使用](app.md)

## 官方線上服務

### ErisPulse 工作台：模組商店與託管域名的後台

模組要進商店、想給模組配一個 `plugin-xxx.erisdev.com` 的網站地址、或者想用腳本自動提交模組？工作台是生態的統一帳號中心：一個帳號管理模組收錄與認證、申請託管域名、產生訪問令牌，還能讓你的網站支援「用 ErisPulse 賬號登入」。純線上服務，**無需安裝**。

訪問：[https://workbench.erisdev.com/](https://workbench.erisdev.com/)

文件：[ErisPulse 工作台使用指南](docs/zh-TW/workbench.md)

---

## 我也想把自己的模組列在這裡？

歡迎推薦優質的、可被廣泛重用的 ErisPulse 生態模組。要求：

1. 已發布到 [PyPI](https://pypi.org/)，且包名以 `ErisPulse-` 開頭
2. 提供基本的 README 與使用範例
3. 積極維護，對 Issue 有回應

滿足以上條件的模組作者可以透過 PR 在本目錄下新增 `<模組名>.md` 文件，並在上方推薦列表中補充對應小節。