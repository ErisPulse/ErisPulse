# 生態模組

ErisPulse 框架本身僅提供核心能力（事件系統、模組系統、配置、路由、日誌等），**不內建** GUI、圖片渲染、可視化等「重型」功能。這些能力由社區維護的 **第三方模組** 提供，按需安裝即可。

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

## 推薦模組

### ErisPulse-Dashboard：瀏覽器中的管理面板

機器人掛在伺服器上，啟停模組、改設定、看日誌還得登終端？Dashboard 把這些功能搬到瀏覽器中：模組啟停、設定編輯、日誌查看、事件監控；其他模組還能向側邊欄註冊自訂視窗，管理頁面集中在同一處。

```bash
epsdk install Dashboard
```

文件：[Dashboard 使用與視窗註冊](dashboard.md) ｜ 項目首頁：[PyPI](https://pypi.org/project/ErisPulse-Dashboard/)

### ErisPulse-Cron：定時任務

要每天定時發簽到提醒、按 Cron 表達式執行週期任務、每隔幾分鐘輪詢一次資料？Cron 提供一次性 / 间隔 / Cron 表達式三種任務類型，回調傳參，SQLite 持久化（重啟不丟任務）。

```bash
epsdk install Cron
```

文件：[Cron 定時任務](cron.md) ｜ 項目首頁：[GitHub](https://github.com/wsu2059q/ErisPulse-Cron)

### ErisPulse-QvQChat：通用智能體

想讓群裡有一個會工作的 AI 助手，而不是只會關鍵字回覆？QvQChat 是通用智能體：工具循環覆蓋收發訊息 / 程式碼執行 / 電腦操作 / 生成圖片 / 語音 / MCP / 子智能體，支援流式對話與串行工具回放，內建 Dashboard 視窗。

```bash
epsdk install ErisPulse-QvQChat
```

文件：[QvQChat 智能體](qvqchat.md) ｜ 項目首頁：[GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-Takumi：圖片渲染

排行榜、戰報、日程卡這類需要「發圖」的場景，寫個模板渲染成圖片發進群裡即可：支援 HTML / 節點樹 / Jinja / SVG / 動畫（基於 [takumi-py](https://github.com/BalconyJH/takumi-py)），內建中英文字型，開箱即用。

```bash
epsdk install Takumi
```

文件：[Takumi 圖片渲染](takumi.md) ｜ 項目首頁：[GitHub](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)）

## 官方客戶端（獨立程式）

### ErisPulse-App：手機上直接跑機器人

沒有常開的伺服器，也想隨時建立實例、安裝模組、查看事件流？ErisPulse-App 是官方全平台客戶端（Android / Windows / Linux / macOS）：原生介面建立 / 運行 / 管理多個機器人實例，內建模組商店與事件建構器，**手機直接運行**，桌面托盤常駐。

所有平台的安裝包均從 [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) 下載，無需 `epsdk`。

文件：[ErisPulse-App 安裝與使用](app.md)

## 我也想把自己的模組列在這裡？

歡迎推薦優質的、可被廣泛重用的 ErisPulse 生態模組。要求如下：

1. 已發布到 [PyPI](https://pypi.org/)，且套件名以 `ErisPulse-` 開頭
2. 提供基本的 README 與使用範例
3. 積極維護，對 Issue 有回應

符合以上條件的模組作者可以透過 PR 在本目錄下新增 `<模組名>.md` 文件，並在上方推薦列表中補充對應的小節。