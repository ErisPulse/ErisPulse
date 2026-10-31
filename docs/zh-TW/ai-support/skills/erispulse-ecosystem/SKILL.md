---
name: erispulse-ecosystem
description: "适用于：了解生态组件（Dashboard/Cron/AI 模块等）与各平台适配器的接入差异。覆盖场景：ErisPulse 框架本身僅提供核心能力（事件系統、模組系統、配置、路由、日誌等），**不內建** GUI、圖片渲染、可視化等「重型」功能。這些能力由社區維護的 **第三方模組** 提供，按需安裝即可。**什麼時候需要閱讀這篇**：當你想使用網頁可視化管理機器人（啟停模組、編輯設定、查看日誌、監控事件流），或想為自己的模組註冊一個 Dashboard 管理頁面時閱讀這篇。不需要則跳過。當你的模組需要定時/延時觸發邏輯（定時提醒、週期監控、Cron 表達式調度），且希望任務在框架重啟後不遺失時讀這篇。不需要則跳過。當你想給機器人加 AI 智慧代理能力（工具循環、串流對話、MCP、長期記憶），或想把自己模組的服務暴露給智慧代理呼叫時讀這篇。不需要則跳過。**什麼時候需要閱讀這篇**：當你想讓 Claude Desktop 等支援 MCP 的 AI 客戶端直接操控你的機器人——發送消息、查看消息、調用模組、管理適配器、觀測事件流——時請閱讀這篇。不需要則可跳過。此部分由各适配器開發者維護，用於說明該適配器與 OneBot12 標準的差異和擴展功能。請參考以下各平台的詳細文件：。"
---

# ErisPulse 生态与多平台

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 生态总览: 55-72 行
- 推薦模組: 74-124 行
- 官方客戶端（獨立程式）: 126-134 行
- 我也想把自己的模組列在這裡？: 136-144 行
- Dashboard: 146-172 行
- 工作原理: 174-185 行
- 註冊 API: 187-225 行
- 兩種注入模式: 227-260 行
- 側邊欄分組: 262-288 行
- 常用 CSS 類名: 290-325 行
- 認證與 API 調用: 327-349 行
- 完整模組示例: 351-461 行
- 注銷視窗: 463-475 行
- 注意事項: 477-487 行
- 定时任务: 489-509 行
- 功能速覽: 511-518 行
- 快速開始: 520-538 行
- API 概覽: 540-593 行
- 模組卸載時的行為: 595-600 行
- 相關連結: 602-607 行
- AI 对话模块: 609-627 行
- 核心能力: 629-648 行
- 模組擴展: 650-720 行
- 事件訂閱: 722-734 行
- 作為服務被呼叫: 736-742 行
- 配套外掛: 744-754 行
- 介面: 756-764 行
- MCP 桥: 766-784 行
- 工作原理: 786-797 行
- Claude Desktop 接入: 799-817 行
- 14 個工具概覽: 819-829 行
- 安全要點: 831-838 行
- 平台指南索引: 840-857 行
- 平台特定功能: 859-885 行
- 通用介面: 887-1065 行
- 標準格式: 1067-1123 行
- 參考連結: 1125-1135 行
- 參與貢獻: 1137-1147 行

## 生态总览

> 来源: `docs/zh-TW/ecosystem/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/ecosystem/README.md）

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

### ErisPulse-Dashboard：瀏覽器裡的管理面板

機器人掛在伺服器上，啟停模組、改設定、看日誌還得登終端機？Dashboard 把這些搬進瀏覽器：模組啟停、設定編輯、日誌查看、事件監控；其他模組還能向側邊欄註冊自訂視窗，管理頁面集中在同一處。

```bash
epsdk install Dashboard
```

文件：[Dashboard 使用與視窗註冊](dashboard.md) ｜ 專案主頁：[PyPI](https://pypi.org/project/ErisPulse-Dashboard/)

### ErisPulse-Cron：排程任務

要每天定時發簽到提醒、按 Cron 表達式跑週期任務、每隔幾分鐘輪詢一次資料？Cron 提供一次性 / 間隔 / Cron 表達式三種任務類型，回呼傳參數，SQLite 持久化（重新啟動不丟任務）。

```bash
epsdk install Cron
```

文件：[Cron 排程任務](cron.md) ｜ 專案主頁：[GitHub](https://github.com/wsu2059q/ErisPulse-Cron)

### ErisPulse-QvQChat：通用智慧代理

想讓群組裡有一個會做事的 AI 助手，而不是只會關鍵字回覆？QvQChat 是通用智慧代理：工具循環涵蓋收發訊息 / 程式碼執行 / 電腦操作 / 生圖 / 語音 / MCP / 子代理，支援串流對話與序列工具回放，內建 Dashboard 視窗。還有 QvQStalker（旁聽插話）、QvQMemes（表情包）、QvQCompanion（擬人陪伴）三個配套外掛。

```bash
epsdk install ErisPulse-QvQChat
```

文件：[QvQChat 智慧代理](qvqchat.md) ｜ 專案主頁：[GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-ApiMCP：讓 AI 用戶端操控機器人

在用 Claude Desktop、Claude Code 這類支援 MCP 的 AI 用戶端？ApiMCP 把機器人執行環境反向開放成 14 個 MCP 工具：AI 可以直接替你收發訊息、呼叫已裝模組、查看平台狀態、訂閱群聊事件——機器人變成 AI 的「手和眼」。

```bash
epsdk install ErisPulse-ApiMCP
```

文件：[ApiMCP 使用指南](apimcp.md) ｜ 專案主頁：[GitHub](https://github.com/wsu2059q/ErisPulse-ApiMCP)

### ErisPulse-Takumi：圖片渲染

排行榜、戰報、日程卡這類要「發圖」的場景，寫個範本渲染成圖片發進群組即可：支援 HTML / 節點樹 / Jinja / SVG / 動畫（基於 [takumi-py](https://github.com/BalconyJH/takumi-py)），內建中英文字型，開箱即用。

```bash
epsdk install Takumi
```

文件：[Takumi 圖片渲染](takumi.md) ｜ 專案主頁：[GitHub](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)）

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

## Dashboard

> 来源: `docs/zh-TW/ecosystem/dashboard.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/ecosystem/dashboard.md）

# ErisPulse-Dashboard

> [!TIP]  
> **什麼時候需要閱讀這篇**：當你想使用網頁可視化管理機器人（啟停模組、編輯設定、查看日誌、監控事件流），或想為自己的模組註冊一個 Dashboard 管理頁面時閱讀這篇。不需要則跳過。

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) 是 ErisDev 直接維護的 **Web 管理面板模組**，為 ErisPulse 提供可視化的運行時管理介面：模組啟停、設定編輯、日誌查看、事件流監控等。

> [!IMPORTANT]  
> Dashboard **不是** ErisPulse 框架的內建功能，需要單獨安裝：  
>  
> ```bash
> epsdk install Dashboard
> ```

Dashboard 還支援其他 ErisPulse 模組將自訂的管理頁面註冊到側邊欄。註冊後，使用者可以直接在 Dashboard 中切換到該模組的專屬視窗頁面，無需額外開發獨立的前端介面。

> [!NOTE]  
> 視窗註冊是**可選功能**。  
> - 如果 Dashboard 模組**未安裝**或**未載入**，呼叫 `sdk.Dashboard.register_view()` 會拋出異常  
> - 請務必使用 `try/except` 包裹註冊程式碼，確保模組本身的其他功能不受影響  
> - 建議在註冊前檢查 Dashboard 是否可用：`hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## 工作原理

```
模組 on_load()
  → 調用 sdk.Dashboard.register_view(...)
  → Dashboard 後端儲存視窗資訊
  → WebSocket 通知前端
  → 前端動態建立側邊欄導航項目 + 頁面容器
  → 使用者點擊即可查看模組視窗
```

---

## 註冊 API

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # 必填，唯一標識
    title="我的模組",                  # 中文名稱
    title_en="My Module",             # 英文名稱
    icon_svg='<svg>...</svg>',        # 側邊欄圖標 SVG
    html_content='<div>...</div>',     # 頁面 HTML 內容
    js_content='function xxx() {}',    # 頁面 JavaScript 逻辑
    css_content='.my-style {}',        # 可選自訂 CSS
    iframe_url='',                     # iframe 模式 URL（與 html_content 二選一）
    loader="loadMyModuleView",         # 切換到該頁面時調用的 JS 函數名
    group="group_extensions",          # 側邊欄分組
    group_title="",                    # 自訂分組中文名
    group_title_en="",                 # 自訂分組英文名
)
```

### 參數說明

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `id` | `str` | 是 | 視窗唯一標識，建議使用模組名稱 |
| `title` | `str` | 否 | 中文顯示名稱，預設使用 `id` |
| `title_en` | `str` | 否 | 英文顯示名稱，預設使用 `title` |
| `icon_svg` | `str` | 否 | 側邊欄圖標的完整 SVG 字串 |
| `html_content` | `str` | 否* | 注入模式的頁面 HTML 內容 |
| `js_content` | `str` | 否 | 頁面 JavaScript 代碼 |
| `css_content` | `str` | 否 | 頁面自訂 CSS 樣式 |
| `iframe_url` | `str` | 否* | iframe 模式的 URL，設置後忽略 `html_content` |
| `loader` | `str` | 否 | 頁面激活時自動調用的 JS 函數名 |
| `group` | `str` | 否 | 側邊欄分組標識，預設 `group_extensions` |
| `group_title` | `str` | 否 | 自訂分組的中文標題 |
| `group_title_en` | `str` | 否 | 自訂分組的英文標題 |

> *`html_content` 和 `iframe_url` 至少提供一個，否則頁面為空白。

---

## 兩種注入模式

### 模式一：HTML/JS 注入（推薦）

直接提供 HTML、JS、CSS 字串，Dashboard 會將內容注入到頁面中。該模式與 Dashboard 樣式完全一致，推薦使用 Dashboard 提供的 CSS 類名。

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="你好頁面", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">這是一個示例頁面</div></div>',
    group="group_tools",
)
```

> 完整的天氣模組示例（包含 API 路由、JS 互動等）請見下方 [完整模組示例](#完整模組示例)。

### 模式二：iframe 嵌入

模組提供自己的 HTML 頁面 URL（需自行註冊路由），Dashboard 以 iframe 方式嵌入。適合需要完全獨立 UI 或複雜互動的場景。

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="數據可視化", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> iframe 模式會自動在 URL 後追加 `token` 參數用於認證。

---

## 側邊欄分組

模組可指定視窗所在的側邊欄分組。Dashboard 內建以下分組：

| 分組標識 | 中文名 | 位置 |
|---------|--------|------|
| `group_overview` | 概覽 | 第1組 |
| `group_events` | 事件 | 第2組 |
| `group_extensions` | 扩展 | 第3組（預設） |
| `group_system` | 系統 | 第4組 |
| `group_tools` | 工具 | 第5組 |

指定內建分組名，模組視窗會追加到該分組末尾：

```python
group="group_tools"  # 追加到"工具"分組
```

也可以使用自訂分組名（不以 `group_` 開頭），Dashboard 會自動創建新分組：

```python
group="my_group",
group_title="我的分組",
group_title_en="My Group",
```

---

## 常用 CSS 類名

模組視窗使用 HTML 注入模式時，可直接使用 Dashboard 已有的 CSS 類名來保持視覺一致性：

| 類名 | 用途 |
|------|------|
| `page-title` | 頁面標題，如 `<h1 class="page-title">標題</h1>` |
| `card` | 卡片容器 |
| `card-header` | 卡片標題欄 |
| `card-body` | 卡片內容區域 |
| `grid-2` | 兩列網格佈局 |
| `grid-3` | 三列網格佈局 |
| `btn` | 基礎按鈕 |
| `btn-primary` | 主按鈕（藍色） |
| `btn-secondary` | 次要按鈕 |
| `btn-icon` | 圖標按鈕 |
| `btn-danger` | 危險操作按鈕 |

Dashboard 使用 CSS 變數控制主題色，你可以在模組視窗中直接引用：

| CSS 變數 | 用途 |
|----------|------|
| `var(--bg-p)` | 主背景色 |
| `var(--bg-s)` | 次背景色 |
| `var(--bg-t)` | 三級背景色（卡片等） |
| `var(--tx-p)` | 主文字色 |
| `var(--tx-s)` | 次文字色 |
| `var(--tx-t)` | 輔助文字色 |
| `var(--bd)` | 邊框色 |
| `var(--accent)` | 強調色 |
| `var(--ok-c)` | 成功色 |
| `var(--er-c)` | 錯誤色 |

這些變數會根據 Dashboard 的亮色/暗色主題自動切換，模組無需額外處理。

---

## 認證與 API 調用

在模組視窗的 JS 中調用模組自己的 API 時，需要攜帶 Dashboard 的 Token 進行認證：

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

模組的 API 端點可以自行決定是否驗證 Token。如果需要驗證，可從請求頭中提取：

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## 完整模組示例

以下是一個完整的天氣模組示例，展示如何註冊視窗、提供 API 數據、以及在卸載時清理資源：

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command


class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("Weather")
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(lazy_load=False, priority=50)

    async def on_load(self, event):
        self._register_routes()
        self._register_dashboard_view()
        self.logger.info("天氣模組已載入")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("天氣模組已卸載")

    def _load_config(self):
        config = self.sdk.config.getConfig("Weather")
        if not config:
            default = {"city": "北京", "api_key": ""}
            self.sdk.config.setConfig("Weather", default)
            return default
        return config

    def _register_routes(self):
        r = self.sdk.router
        r.register_http_route("Weather", "/api/current",
                              handler=self._api_current, methods=["GET"])

    def _unregister_routes(self):
        r = self.sdk.router
        try:
            r.unregister_http_route("Weather", "/api/current")
        except Exception:
            pass

    async def _api_current(self, request):
        return {
            "city": self.config.get("city", "北京"),
            "temp": 25,
            "humidity": 60,
        }

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="天氣", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">天氣查詢</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">查看當前天氣資訊</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">當前天氣</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">點擊刷新加載</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">操作</div>
                            <div class="card-body">
                                <button class="btn btn-primary" onclick="refreshWeather()">刷新</button>
                            </div>
                        </div>
                    </div>
                ''',
                js_content='''
                    async function loadWeatherView() { await refreshWeather(); }
                    async function refreshWeather() {
                        var el = document.getElementById('weather-info');
                        if (!el) return;
                        el.textContent = '加載中...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>城市: ' + (data.city || '--') + '</p>' +
                                           '<p>溫度: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>濕度: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = '加載失敗: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"註冊 Dashboard 視窗失敗: {e}")
```

---

## 注銷視窗

模組卸載時應呼叫 `unregister_view()` 清理已註冊的視窗：

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

註銷後 Dashboard 前端會透過 WebSocket 實時移除側邊欄導航項目和頁面內容，無需使用者刷新。

---

## 注意事項

1. **載入順序** — Dashboard 的載入優先級為 `99999`（高優先級），你的模組優先級應低於此值（如 `50`），確保 Dashboard 先載入完成
2. **防禦性編程** — 註冊視窗時使用 `try/except` 包裹，因為 Dashboard 模組可能未安裝或未載入
3. **資源清理** — 在 `on_unload` 中呼叫 `unregister_view()` 移除已註冊的視窗
4. **ID 唯一性** — `id` 參數在整個 Dashboard 中必須唯一，建議直接使用模組名稱
5. **SVG 圖標** — `icon_svg` 應為完整的 `<svg>` 標籤，建議尺寸使用 `viewBox="0 0 24 24"`，使用 `stroke="currentColor"` 繼承 Dashboard 主題色
6. **JS 函數命名** — `js_content` 中的函數名應具有唯一性（如 `loadWeatherView`），避免與其他模組衝突
7. **動態更新** — 模組註冊/註銷視窗後，Dashboard 前端會透過 WebSocket 實時更新側邊欄，無需刷新頁面

---

## 定时任务

> 来源: `docs/zh-TW/ecosystem/cron.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/ecosystem/cron.md）

# ErisPulse-Cron

> [!TIP]
> **什麼時候需要讀這篇**：當你的模組需要定時/延時觸發邏輯（定時提醒、週期監控、Cron 表達式調度），且希望任務在框架重啟後不遺失時讀這篇。不需要則跳過。

[ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) 是 ErisPulse 生態的**定時任務調度模組**，為其他模組提供統一的定時任務 API：支援一次性定時、間隔循環、Cron 表達式三種任務類型，回呼傳參，SQLite 持久化（重啟不丟任務）。

> [!IMPORTANT]
> Cron **不是** ErisPulse 框架的內建功能，需要單獨安裝：
>
> ```bash
> epsdk install Cron
> ```

安裝後透過 `sdk.Cron` 存取全部介面。

---

## 功能速覽

- **三種定時類型**：一次性（`once`）、間隔循環（`interval`）、Cron 表達式（`cron`）
- **回調傳參**：建立時傳入 `callback_data`，觸發時原樣返回，方便識別任務來源
- **持久化**：任務儲存在 SQLite（經 `sdk.storage`），框架重啟後自動恢復
- **錯過策略**：立即觸發 / 跳過 / 重新排程，可按任務選擇
- **任務管理**：暫停、恢復、取消、手動觸發、清理過期任務
- **Dashboard 集成**：已安裝 [ErisPulse-Dashboard](dashboard.md) 時自動註冊管理視窗

## 快速開始

```python
from ErisPulse import sdk

# 1. 註冊回調處理器
@sdk.Cron.on_trigger
async def handle_trigger(info):
    data = info["callback_data"]
    print(f"任務觸發: {info['task_id']}, 數據: {data}")

# 2. 創建定時任務
task_id = sdk.Cron.once(
    delay=60,
    callback_data={"type": "reminder", "msg": "該喝水了"},
)
```

---

## API 概覽

### 創建任務

```python
# 一次性：延遲 600 秒觸發
sdk.Cron.once(delay=600, callback_data={"order_id": "123"}, label="訂單超時提醒")

# 間隔循環：每 300 秒觸發，最多 100 次
sdk.Cron.interval(interval_seconds=300, callback_data={"monitor": "server-1"}, max_runs=100)

# Cron 表達式：工作日每天 9:30
sdk.Cron.cron(expression="30 9 * * 1-5", callback_data={"type": "daily_report"})

# 通用可選參數：trigger_at（絕對時間戳）、delay（首次延遲）、timezone、
# max_runs（0=無限）、label、source（創建者模組名）、missed_policy（錯過策略）
```

常用 Cron 表達式：`*/5 * * * *`（每 5 分鐘）、`0 8 * * *`（每天早 8 點）、`30 9 * * 1-5`（工作日 9:30）、`0 0 1 * *`（每月 1 號）。

### 回調

```python
@sdk.Cron.on_trigger
async def my_handler(info):
    # info 含 task_id / task_type / callback_data / label / source /
    # run_count / max_runs / created_at / last_run / trigger_time
    ...
```

支援註冊多個 handler，全部依次調用，單個 handler 異常不會影響其他 handler。

### 管理任務

```python
sdk.Cron.cancel(task_id)                  # 取消
sdk.Cron.pause(task_id)                   # 暫停
sdk.Cron.resume(task_id)                  # 恢復（reschedule=True 重新計算下次觸發）
await sdk.Cron.trigger_now(task_id)       # 手動立即觸發（不影響原計劃）
sdk.Cron.get_task(task_id)                # 查看單個任務
sdk.Cron.list_tasks(source="MyModule")    # 列出任務（支援 source/status/task_type 過濾）
sdk.Cron.delete_task(task_id)             # 刪除任務記錄
sdk.Cron.cleanup()                        # 清理 7 天前的已完成/已取消任務
```

### 錯過策略（missed_policy）

框架重啟後，對於錯過觸發時間的任務：

| 策略 | 行為 |
|------|------|
| `fire_immediately` | 立即觸發（預設） |
| `skip` | 跳過本次，等下次 |
| `reschedule` | 從當前時間重新計算下次觸發 |

## 模組卸載時的行為

Cron 的任務資料是**持久化資產**：任務創建方模組被卸載或停用不會刪除已建立的任務。但該模組註冊的回呼句柄會被清除——基於歸屬權系統的[外部清理鉤子](../advanced/ownership.md#工具模組指南托管其它模組的句柄)，Cron 在替其他模組托管回呼時會自動記名，當對方模組被卸載/停用時會自動拋棄其回呼句柄，確保對方模組實例可以被正常回收。

- 任務創建方**重新載入**後重新 `on_trigger` 即恢復接收觸發
- 不再需要的任務可用 `sdk.Cron.cancel(task_id)` / `delete_task(task_id)` 清理

## 相關連結

- [GitHub 儲存庫](https://github.com/wsu2059q/ErisPulse-Cron)
- [PyPI 頁面](https://pypi.org/project/ErisPulse-Cron/)

---

## AI 对话模块

> 来源: `docs/zh-TW/ecosystem/qvqchat.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/ecosystem/qvqchat.md）

# ErisPulse-QvQChat 通用智慧代理

> [!TIP]
> **什麼時候需要讀這篇**：當你想給機器人加 AI 智慧代理能力（工具循環、串流對話、MCP、長期記憶），或想把自己模組的服務暴露給智慧代理呼叫時讀這篇。不需要則跳過。

[ErisPulse-QvQChat](https://pypi.org/project/ErisPulse-QvQChat/) 是一個 **通用智慧代理模組**，圍繞工具循環建構：收發訊息、呼叫生態模組服務、編寫並執行程式碼、操作電腦、生成圖片語音、管理排程任務與長期記憶——全部透過同一套工具協定完成。

> [!IMPORTANT]
> QvQChat 需要單獨安裝：
>
> ```bash
> epsdk install ErisPulse-QvQChat
> ```
>
> 同時需要在「模型池」新增至少一個 OpenAI 相容模型（Base URL、API Key、模型名稱）。

## 核心能力

| 能力 | 說明 |
|---|---|
| 工具循環 | 模型輸出工具呼叫 → 並行執行 → 結果回填 → 繼續推理，直到給出最終回答 |
| 串流對話 | SSE 逐字輸出，工具步驟即時可見；重新整理 / 切走再回來，進度不丟 |
| 上下文壓縮 | 超過 token 閾值自動把舊對話壓縮為摘要（預設 128000 估算，可自訂） |
| 生態服務橋 | 自動發現模組宣告的服務並轉為工具，裝卸模組即增減能力 |
| MCP 用戶端 | stdio 與 Streamable HTTP，MCP 工具併入同一工具集 |
| 子智慧代理 | `spawn_agent` 派出獨立會話的子智慧代理探索任務，只回報結論 |
| 行程內執行 | `run_python_sdk` 主行程內執行 Python，直接存取執行時物件 |
| 電腦操作 | 三級安全沙箱（strict / standard / permissive），危險操作確認，全程稽核 |
| 視覺理解 | 圖片自動注入模型（不支援圖片時自動剝離重試） |
| 附件 | 任意檔案依 hash 去重後寫入磁碟，路徑交給 AI 自行處理；Ctrl+V 貼上截圖 |
| 分享會話 | 臨時唯讀連結（有效期 + token 預算），匯出 Markdown |
| 排程任務 | cron / 一次性 / 間隔，持久化，權限隨建立者 |
| 會話接管 | 管理員可讓智慧代理獨佔一個會話 |
| 人格系統 | 系統提示詞 + 開場對話 + 工具白名單，可按會話綁定 |
| 長期記憶 | 每會話記憶條目，按相似度檢索注入 |
| AI 自動命名 | 會話首輪回覆後自動生成簡短標題 |

## 模組擴展

任何 ErisPulse 模組宣告 `services` 即自動成為 QvQChat 的工具，無需專門介面：

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class Main(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(name="Draw", services=[
            {"name": "draw", "description": "根據描述生成圖片，回傳圖片 URL"},
        ])

    async def draw(self, prompt: str, size: str = "1024x1024"):
        return {"image_url": "https://..."}
```

服務的方法簽名自動對映為工具的 JSON Schema 參數定義，docstring 首行作為參數說明。

### 深度整合（可選）

模組可以額外實作以下任意服務，每個服務**獨立可選**——一個模組可以只做人格擴展，也可以只注入提示詞：

#### `qvq_prompts()` → 注入系統提示詞

回傳 `list[str]` 或 `list[{"text": str, "priority": int}]`，依 `priority` 升冪拼接。

```python
async def qvq_prompts(self):
    return [
        {"text": "畫圖後用 send_message 把圖片發給使用者。", "priority": 10},
        {"text": "支援的風格：動漫、寫實、水彩、像素。", "priority": 20},
    ]
```

#### `qvq_personas()` → 註冊人格預設

回傳人格清單，id 自動加 `ext.<模組名>.` 前綴，模組卸載自動清理。適合專門提供人格擴展的模組（如情感陪伴、翻譯專員、程式碼審查員等）。

```python
async def qvq_personas(self):
    return [
        {"id": "companion", "name": "暖男", "system": "你是一個溫暖體貼的聊天夥伴..."},
        {"id": "coder", "name": "程式碼導師", "system": "...", "tools": ["read_file", "run_python"]},
    ]
```

`tools` 可選限定該人格可用的工具子集。

#### `qvq_schemas()` → 顯式參數 schema

回傳 `dict[服務名, JSON Schema]`，覆寫方法簽名推斷。參數複雜或需要嚴格驗證時使用。

```python
async def qvq_schemas(self):
    return {
        "draw": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "畫面描述"},
                "size": {"type": "string", "enum": ["512x512", "1024x1024"]},
            },
            "required": ["prompt"],
        },
    }
```

### 重新整理時機

深度整合服務的重新整理時機：啟動、模組裝卸、Dashboard「工具」頁手動重新整理。

## 事件訂閱

QvQChat 廣播兩個生命週期事件：

| 事件 | 時機 | 負載 |
|---|---|---|
| `qvq.message` | 收到使用者訊息 | `chat_key` `platform` `sender_id` `sender_name` `text` `is_group` |
| `qvq.replied` | 回覆發出後 | `chat_key` `reply` `tools` |

```python
async def setup(self):
    sdk.lifecycle.on("qvq.message", self.on_message)
```

## 作為服務被呼叫

| 服務 | 簽名 | 說明 |
|---|---|---|
| `chat` | `(session_id, prompt, persona="")` | 與智慧代理對話，回傳文字 |
| `run_prompt` | `(chat_key, prompt, ...)` | 執行提示詞，結果可傳送到目標會話 |
| `get_status` | `()` | 執行狀態摘要 |

## 配套外掛

三個獨立模組擴充了 QvQChat，也順便示範了擴充點能做什麼——安裝 QvQChat 後依需求加裝：

| 外掛 | 用途 |
|---|---|
| [ErisPulse-QvQStalker](https://github.com/wsu2059q/ErisPulse-QvQStalker) | 旁聽群聊自動插話：熱度追蹤、五層判定和衝動值共同決定智慧型代理何時開口，15 項行為參數可在設定頁直接調整 |
| [ErisPulse-QvQMemes](https://github.com/wsu2059q/ErisPulse-QvQMemes) | 給智慧型代理一個表情包習慣：`send_sticker` 工具讓模型自己挑選該發哪張，群組圖片自動收錄並由視覺模型加上標籤 |
| [ErisPulse-QvQCompanion](https://github.com/wsu2059q/ErisPulse-QvQCompanion) | 擬人化陪伴：語氣人設注入、衝動值主動開口、靜默時段與每日上限 |

三個外掛都透過上文「模組擴充」的約定服務接入，本身也是擴充寫法的參考實作。

## 介面

透過 `/QvQChat/view` 獨立存取，或嵌入 Dashboard 側邊欄。

![概覽](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/overview.png)

![對話](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/chat.png)

---

## MCP 桥

> 来源: `docs/zh-TW/ecosystem/apimcp.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/ecosystem/apimcp.md）

# ErisPulse-ApiMCP 使用 AI 客戶端控制機器人

> [!TIP]  
> **什麼時候需要閱讀這篇**：當你想讓 Claude Desktop 等支援 MCP 的 AI 客戶端直接操控你的機器人——發送消息、查看消息、調用模組、管理適配器、觀測事件流——時請閱讀這篇。不需要則可跳過。

[ErisPulse-ApiMCP](https://github.com/wsu2059q/ErisPulse-ApiMCP) 透過 **MCP（Model Context Protocol）** 將機器人的運行時能力開放給 AI 客戶端：安裝後，Claude Desktop 中會新增 14 個工具，AI 可以替你收發消息、排查模組問題、訂閱群聊事件——機器人從「你管理的程式」變成「AI 的手和眼」。

> [!IMPORTANT]  
> ApiMCP 需要單獨安裝，且**必須明確配置 token** 後橋接功能才會啟用：  
>  
> ```bash
> epsdk install ErisPulse-ApiMCP
> ```  
>  
> 在 `config.toml` 的 `[ApiMCP]` 節點中設置 `token = "長隨機串"`（或環境變數 `ERISPULSE_APIMCP_TOKEN`）。未配置時，除了探活端點外所有端點都會返回 503，避免令牌靜默洩漏。

## 工作原理

兩層結構，機器人本體不引入任何 AI 依賴：

- **機器人進程內**：ApiMCP 模組在框架內建 HTTP server 上掛一個 REST 橋（`/apimcp/*`，token 鑑權，預設限流 30 請求/分鐘）
- **獨立進程**：`erispulse-apimcp` 命令用官方 `mcp` SDK 起 stdio server，把 MCP 工具呼叫轉發到機器人 HTTP 橋

```
Claude Desktop ──MCP(stdio)──► erispulse-apimcp ──HTTP──► 機器人進程 REST 橋 ──► sdk.*
```

機器人不線上或橋未配置時，工具回傳可讀錯誤與排查指引，不拋出堆疊。

## Claude Desktop 接入

編輯 `claude_desktop_config.json`（Windows: `%APPDATA%\Claude\`；macOS: `~/Library/Application Support/Claude/`）：

```json
{
  "mcpServers": {
    "erispulse": {
      "command": "erispulse-apimcp",
      "env": {
        "ERISPULSE_APIMCP_URL": "http://127.0.0.1:8000",
        "ERISPULSE_APIMCP_TOKEN": "你的token"
      }
    }
  }
}
```

儲存後完全重新啟動 Claude Desktop，工具列表出現 `erispulse` 伺服器即表示接入成功。任何支援 MCP stdio server 的客戶端（Claude Code、Cursor 等）都能用同樣方式接入。

## 14 個工具概覽

| 類別 | 工具 | 說明 |
|---|---|---|
| 模組 | `list_modules` / `get_module_info` / `call_module` / `reload_module` | 查看與呼叫已安裝模組的公開服務，觸發熱重載 |
| 適配器 | `list_adapters` / `get_adapter_status` / `reload_adapter` | 平台在線狀態；適配器重載預設禁用 |
| 消息 | `send_message` / `recent_messages` | 向任意平台發送文字/圖片/音訊/視訊/檔案；經 [transcript](../advanced/transcript.md) 回看最近消息 |
| 事件 | `subscribe_events` / `unsubscribe` / `poll_events` | 訂閱訊息/通知等事件，環形緩衝（預設 1000 條），增量輪詢 |
| 運行時 | `get_topology` / `sdk_health` | 運行時拓撲（已脫敏）與健康摘要 |

一個典型用法：AI 先 `subscribe_events(["message"])`，然後周期性 `poll_events` 觀察群裡在聊什麼，決定要不要 `send_message` 插話或 `call_module` 觸發某個模組的能力。

## 安全要點

- **token 即完全控制權**：能讀取訊息、發送訊息、呼叫白名單內模組方法。切勿提交至倉庫或貼到公開頻道；多租戶場景請拆分多個機器人實例
- **最小授權**：`module_call_whitelist` 收窄可呼叫模組（支援 `模組.方法` 精確放行），`send_target_whitelist` 收窄發送目標（如只允許發送到某個群組），`allow_adapter_reload` 保持預設關閉
- **只監聽本機**：僅本機使用時把框架 HTTP server 設為 `server.host = "127.0.0.1"`；跨機器必須內網 + 反向代理加 TLS
- 輸出經過鍵名級淨化（密鑰/路徑類鍵整鍵丟棄）；深度淨化是模組自身責任，敏感會話勿開放訂閱

完整配置項目（緩衝容量、回溯視窗、事件類型白名單等）與 REST 端點明細見[項目 README](https://github.com/wsu2059q/ErisPulse-ApiMCP)。

## 平台指南索引

> 来源: `docs/zh-TW/platform-guide/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/zh-TW/platform-guide/README.md）

# ErisPulse PlatformFeatures 文件

> 基線協議：[OneBot12](https://12.onebot.dev/)  
> 
> 本文檔為**平台特定功能指南**，包含：
> - 各適配器支援的Send方法鏈式呼叫範例
> - 平台特有的事件/訊息格式說明
> 
> 通用使用方法請參考：
> - [基礎概念](../getting-started/basic-concepts.md)
> - [事件轉換標準](../standards/event-conversion.md)  
> - [API回應規範](../standards/api-response.md)

---

## 平台特定功能

此部分由各适配器開發者維護，用於說明該適配器與 OneBot12 標準的差異和擴展功能。請參考以下各平台的詳細文件：

- [維護說明](maintain-notes.md)

- [雲湖平台特性](yunhu.md)
- [雲湖用戶平台特性](yunhu_user.md)
- [Telegram 平台特性](telegram.md)
- [OneBot11 平台特性](onebot11.md)
- [OneBot12 平台特性](onebot12.md)
- [SnowLuma 平台特性](snowluma.md)
- [郵件平台特性](email.md)
- [Kook(開黑啦) 平台特性](kook.md)
- [Matrix 平台特性](matrix.md)
- [企業微信平台特性](wecom.md)
- [Bilibili 平台特性](bilibili.md)
- [Minecraft 平台特性](minecraft.md)
- [QQ官方機器人平台特性](qqbot.md)
- [花楓咖啡館](ideaura.md)
- [Discord](discord.md)
- [Webhook協議橋](webhook.md)
- [微信公眾號](wechatmp.md)

> 此外還有 `sandbox` 適配器，但此適配器無需維護平台特性文件

---

## 通用介面

### Send 鏈式呼叫
所有適配器都支援以下標準呼叫方式：

> **注意：** 文件中的 `{AdapterName}` 需替換為實際適配器名稱（如 `yunhu`、`telegram`、`onebot11`、`email` 等）。

1. 指定類型和ID: `To(type,id).Func()`
   ```python
   # 獲取適配器實例
   my_adapter = adapter.get("{AdapterName}")
   
   # 發送訊息
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例如：
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. 僅指定ID: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例如：
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 指定發送帳號: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例如：
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼叫: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("廣播訊息")
   
   # 例如：
   email = adapter.get("email")
   await email.Send.Text("廣播訊息")
   ```

#### 異步發送與結果處理

Send DSL 的方法返回 `asyncio.Task` 對象，這意味著您可以選擇是否立即等待結果：

```python
# 獲取適配器實例
my_adapter = adapter.get("{AdapterName}")

# 不等待結果，訊息在背景發送
task = my_adapter.Send.To("user", "123").Text("Hello")

# 如果需要獲取發送結果，稍後可以等待
result = await task
```

#### 發送規則裝飾器

在實際開發中，經常需要：發送成功後才執行後續邏輯、失敗自動重試、超時取消、發送進度監控等。Send DSL 內建了一套發送規則裝飾器，透過鏈式方法附加規則：

| 方法 | 說明 |
|--------|------|
| `.Hook(callback)` | 發送成功後執行的回調（可多次呼叫） |
| `.Retry(times=1)` | 失敗自動重試 N 次（含首次共 N+1 次） |
| `.Timeout(seconds)` | 單次發送超時，超時取消（可與 Retry 叠加） |
| `.Defer(seconds)` | 延遲發送（進程內定時，不持久化） |
| `.OnProgress(callback)` | 各階段進度回調，傳入 SendContext |
| `.OnError(callback)` | 最終失敗時的錯誤回調（僅觸發一次） |

```python
yunhu = adapter.get("yunhu")

# 發送成功後才扣積分
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消費成功"))

# 失敗重試 + 超時取消 + 進度監控
def on_progress(ctx):
    print(f"階段: {ctx.stage}, 嘗試: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # 最多重試 3 次
        .Timeout(10)           # 每次超時 10 秒
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要通知"))
```

規則方法返回 `self`，必須放在發送方法（Text/Image 等）之前呼叫。`SendContext` 包含 `stage`（pending/sending/retrying/success/failed/timeout）、`attempt`、`elapsed`、`error`、`result` 等欄位，便於監控。

#### 批量建構模式（Build）

一條鏈路中建構多個發送方法，最後統一執行。適用於「一口氣發多條訊息」的場景：

```python
yunhu = adapter.get("yunhu")

# 建構多條訊息，統一發送
results = await (yunhu.Send.To("user", "123")
                .Build()                     # 進入建構模式
                .Text("通知一")
                .Image("pic.jpg")
                .Text("通知二")
                .send_all())                 # 統一執行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` 默認**並行**執行（併發發送，效率高）。需要保證訊息到達順序時呼叫 `.Sequential()` 串行執行：

```python
# 串行執行（保證順序）+ 失敗重試
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # 按順序依次發送
       .Retry(2)                     # 失敗的條目各自重試
       .Text("第一條").Text("第二條")
       .send_all())
```

批量執行採用**失敗繼續**策略：某條失敗不會中斷其他條，失敗的條目自動重試。批量也支援整批的 `Hook`（全部成功後觸發）、`OnError`（有失敗時觸發）、`OnProgress`（進度回調）。

> 更詳細的規則與批量建構說明請參考 [SendDSL 詳解](../developer-guide/adapters/send-dsl.md)。

### 事件監聽
有三種事件監聽方式：

1. 平台原生事件監聽：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}原生事件: {data}")
   ```

2. OneBot12標準事件監聽：
   ```python
   from ErisPulse.Core import adapter, logger

   # 監聽OneBot12標準事件
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"收到標準事件: {data}")

   # 監聽特定平台的標準事件
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}標準事件: {data}")
   ```

3. Event模組監聽：
    `Event`的事件基於 `adapter.on()` 函數，因此`Event`提供的事件格式是一個OneBot12標準事件

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="發送問候訊息", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"收到訊息: {event}")
    async def notice_handler(event):
        logger.info(f"收到通知: {event}")
    async def request_handler(event):
        logger.info(f"收到請求: {event}")
    async def command_handler(event):
        logger.info(f"收到命令: {event}")
    ```

其中，最推薦的是使用 `Event` 模組進行事件處理，因為 `Event` 模組提供了豐富的事件類型，以及豐富的事件處理方法。

## 標準格式  
為方便參考，這裡給出了簡單的事件格式，如果需要詳細資訊，請參考上方的連結。  

> **注意：** 以下格式為基礎 OneBot12 標準格式，各適配器可能在此基礎上有擴展欄位。具體請參考各適配器的特定功能說明。  

### 標準事件格式  
所有適配器必須實現的事件轉換格式：  
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### 標準回應格式  
#### 消息發送成功  
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### 消息發送失敗  
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "缺少必要參數",
  "echo": "1234",
  "{platform}_raw": {...}
}
```  

---

## 參考連結
ErisPulse 項目：
- [主程式庫](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu 適配器程式庫](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram 適配器程式庫](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot 適配器程式庫](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

相關官方文件：
- [OneBot V11 協定文件](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 官方文件](https://core.telegram.org/bots/api)
- [雲湖官方文件](https://www.yhchat.com/document/1-3)

## 參與貢獻

我們歡迎更多開發者參與編寫和維護適配器文件！請按照以下步驟提交貢獻：

1. Fork [ErisPuls](https://github.com/ErisPulse/ErisPulse) 倉庫。
2. 在 `docs/platform-features/` 目錄下建立一個 Markdown 檔案，並以 `<平台名稱>.md` 命名。
3. 在本 `README.md` 檔案中新增您貢獻的適配器連結以及相關官方文件。
4. 提交 Pull Request。

感謝您的支持！
