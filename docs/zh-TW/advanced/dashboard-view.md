# Dashboard 視窗註冊

Dashboard 支援其他 ErisPulse 模組將自訂的管理頁面註冊到 Dashboard 的側邊欄中。註冊後，使用者可以直接在 Dashboard 中切換到該模組的專屬視窗頁面，無需額外開發獨立的前端介面。

> **前提條件**
>
> Dashboard 視窗註冊是**可選功能**，需要安裝並載入 [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) 模組。
>
> - 如果 Dashboard 模組**未安裝**或**未載入**，呼叫 `sdk.Dashboard.register_view()` 會拋出異常
> - 請務必使用 `try/except` 包裹註冊程式碼，確保模組本身的其他功能不受影響
> - 建議在註冊前檢查 Dashboard 是否可用：`hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## 工作原理

```
模組 on_load()
  → 呼叫 sdk.Dashboard.register_view(...)
  → Dashboard 後端儲存視窗資訊
  → WebSocket 通知前端
  → 前端動態建立側邊欄導航項 + 頁面容器
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
    js_content='function xxx() {}',    # 頁面 JavaScript 邏輯
    css_content='.my-style {}',        # 可選自訂 CSS
    iframe_url='',                     # iframe 模式 URL（與 html_content 二選一）
    loader="loadMyModuleView",         # 切換到該頁面時呼叫的 JS 函數名
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
| `icon_svg` | `str` | 否 | 側邊欄圖標的完整 SVG 字符串 |
| `html_content` | `str` | 否* | 注入模式的頁面 HTML 內容 |
| `js_content` | `str` | 否 | 頁面 JavaScript 程式碼 |
| `css_content` | `str` | 否 | 頁面自訂 CSS 樣式 |
| `iframe_url` | `str` | 否* | iframe 模式的 URL，設定後忽略 `html_content` |
| `loader` | `str` | 否 | 頁面激活時自動呼叫的 JS 函數名 |
| `group` | `str` | 否 | 側邊欄分組標識，預設 `group_extensions` |
| `group_title` | `str` | 否 | 自訂分組的中文標題 |
| `group_title_en` | `str` | 否 | 自訂分組的英文標題 |

> *`html_content` 和 `iframe_url` 至少提供一個，否則頁面為空白。

---

## 兩種注入模式

### 模式一：HTML/JS 注入（推薦）

直接提供 HTML、JS、CSS 字符串，Dashboard 會將內容注入到頁面中。該模式與 Dashboard 樣式完全一致，推薦使用 Dashboard 提供的 CSS 類名。

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
| `group_extensions` | 擴展 | 第3組（預設） |
| `group_system` | 系統 | 第4組 |
| `group_tools` | 工具 | 第5組 |

指定內建分組名，模組視窗會追加到該分組末尾：

```python
group="group_tools"  # 追加到"工具"分組
```

也可以使用自訂分組名（不以 `group_` 開頭），Dashboard 會自動建立新分組：

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

Dashboard 使用 CSS 變量控制主題色，你可以在模組視窗中直接引用：

| CSS 變量 | 用途 |
|----------|------|
| `var(--bg-p)` | 主背景色 |
| `var(--bg-s)` | 次背景色 |
| `var(--bg-t)` | 三级背景色（卡片等） |
| `var(--tx-p)` | 主文字色 |
| `var(--tx-s)` | 次文字色 |
| `var(--tx-t)` | 輔助文字色 |
| `var(--bd)` | 邊框色 |
| `var(--accent)` | 強調色 |
| `var(--ok-c)` | 成功色 |
| `var(--er-c)` | 錯誤色 |

這些變量會根據 Dashboard 的亮色/暗色主題自動切換，模組無需額外處理。

---

## 認證與 API 呼叫

在模組視窗的 JS 中呼叫模組自己的 API 時，需要攜帶 Dashboard 的 Token 進行認證：

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

模組的 API 端點可以自行決定是否驗證 Token。如果需要驗證，可以從請求頭中提取：

```python
from fastapi.responses import JSONResponse

async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return JSONResponse({"data": "hello"})
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
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">點擊刷新載入</div>
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
                        el.textContent = '載入中...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>城市: ' + (data.city || '--') + '</p>' +
                                           '<p>溫度: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>濕度: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = '載入失敗: ' + e.message;
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

## 註銷視窗

模組卸載時應呼叫 `unregister_view()` 清理已註冊的視窗：

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

註銷後 Dashboard 前端會透過 WebSocket 即時移除側邊欄導航項和頁面內容，無需使用者刷新。

---

## 注意事項

1. **載入順序** — Dashboard 的載入優先級為 `99999`（高優先級），你的模組優先級應低於此值（如 `50`），確保 Dashboard 先載入完成
2. **防禦性編程** — 註冊視窗時使用 `try/except` 包裹，因為 Dashboard 模組可能未安裝或未載入
3. **資源清理** — 在 `on_unload` 中呼叫 `unregister_view()` 移除已註冊的視窗
4. **ID 唯一性** — `id` 參數在整个 Dashboard 中必須唯一，建議直接使用模組名稱
5. **SVG 圖標** — `icon_svg` 應為完整的 `<svg>` 標籤，建議尺寸使用 `viewBox="0 0 24 24"`，使用 `stroke="currentColor"` 繼承 Dashboard 主題色
6. **JS 函數命名** — `js_content` 中的函數名應具有唯一性（如 `loadWeatherView`），避免與其他模組衝突
7. **動態更新** — 模組註冊/註銷視窗後，Dashboard 前端會透過 WebSocket 實時更新側邊欄，無需刷新頁面