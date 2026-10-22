# ErisPulse-Takumi

> [!TIP]
> **什麼時候需要讀這篇**：當你需要把 HTML / 節點樹 / Jinja 範本渲染成圖片傳送到聊天平台（統計卡片、排行榜、圖文長文）時讀這篇。不需要則跳過。

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) 是 ccd2s 維護的 **第三方圖片渲染模組**，基於 [takumi-py](https://github.com/BalconyJH/takumi-py)，讓 Bot 能夠將 HTML、節點樹、Jinja 範本、SVG、動畫渲染為圖片。模組 **內建中英文字型**（Noto Sans SC / Roboto / Source Code Pro），無需額外設定。

> [!IMPORTANT]
> Takumi **不是** ErisPulse 框架的內建功能，需要單獨安裝：
>
> ```bash
> epsdk install Takumi
> ```

適用情境：

- 將資料/統計渲染為卡片圖片
- 將 Markdown / 長文字渲染為排版穩定的圖片，規避平台樣式差異
- 產生 SVG / 動畫，實現動態視覺效果
- 中英混排圖文（內建字型開箱即用）

---

## 安裝與啟用

```bash
epsdk install Takumi
```

安裝後模組自動載入，在設定中確認啟用：

```toml
[Takumi]
enabled = true
```

---

## 快速上手

模組自動載入後，透過模組管理器取得，或使用 `sdk` 捷徑：

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# 等價寫法：takumi = sdk.Takumi
```

### 渲染 HTML

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>你好，ErisPulse</h1>
      <p>由 Takumi 渲染</p>
    </div>
    """,
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
      font-family: "Noto Sans SC";
    }
    """],
    width=800,
    height=None,   # 依內容自動撐高
    lang="zh-CN",
)
```

### 渲染節點樹

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "中文和 English 都可直接渲染",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

`png` 是 `bytes`，可透過 `event.reply(png, method="Image")` 傳送（詳見 [傳送渲染結果](#傳送渲染結果)）。

---

## 渲染 API

`sdk.Takumi` 代理了底層 `takumi_py.Renderer` 的全部能力：所有渲染、測量、SVG、動畫、範本方法都可直接在 `sdk.Takumi` 上呼叫。對這些方法，模組會在呼叫時**自動注入內建字型後備堆疊**（`takumi.families`），無需手動傳 `font_families`；若明確傳入則尊重呼叫方設定。

### 方法總覽

| 類別 | 方法 | 回傳 | 說明 |
|------|------|------|------|
| 靜態渲染 | `render_html(html, ...)` | `bytes` | 渲染 HTML 字串 |
| | `render_node(node, ...)` | `bytes` | 渲染節點樹（dict） |
| | `render_template(name, ctx, ...)` | `bytes` | 渲染 Jinja 範本 |
| | `render_compiled(node, ...)` | `bytes` | 渲染預先編譯節點 |
| SVG 輸出 | `render_svg_html(html, ...)` | `str` | 輸出 SVG（HTML 輸入） |
| | `render_svg_node(node, ...)` | `str` | 輸出 SVG（節點樹輸入） |
| | `render_svg_template(name, ctx, ...)` | `str` | 輸出 SVG（範本輸入） |
| | `render_svg_compiled(node, ...)` | `str` | 輸出 SVG（預先編譯輸入） |
| 動畫 | `render_animation(scenes, ...)` | `bytes` | 編碼多幀動畫 |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | 取序列某一時刻幀 |
| 測量 | `measure_node(node, ...)` | `dict` | 測量節點樹版面 |
| | `measure_html(html, ...)` | `dict` | 測量 HTML 版面 |
| | `measure_compiled(node, ...)` | `dict` | 測量預先編譯節點 |
| 編譯 | `compile_node(node)` | `CompiledNode` | 編譯節點樹 |
| | `compile_html(html, ...)` | `CompiledNode` | 編譯 HTML |
| 字型 | `register_font(font)` | `list[str]` | 註冊自訂字型，回傳 family 清單 |
| | `register_fonts(fonts)` | `list[str]` | 批次註冊 |

> `CompiledNode` 提供 `resource_urls()` 方法，可預先找出待載入的 HTTP(S) 圖片引用，便於提前準備資源。

### 通用參數

以下參數適用於靜態渲染與 SVG 方法（動畫方法另有 `fps` 等，見對應範例）：

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `stylesheets` | `list[str]` | `None` | 文件層級 CSS 字串清單；內嵌 `style` 仍會隨 HTML 一起解析 |
| `width` | `int \| None` | `1200` | 視埠寬度（像素）；`None` 依版面推斷 |
| `height` | `int \| None` | `630` | 畫布高度（像素）；`None` 依內容自動撐高（見 [視埠與輸出格式](#視埠與輸出格式)） |
| `lang` | `str \| None` | `None` | BCP-47 語言標籤（如 `zh-CN`），影響文字塑形與換行 |
| `font_families` | `list[str]` | 自動注入 | 字型後備堆疊；便利方法預設注入內建字型 |
| `format` | `str` | `"png"` | 輸出格式（見 [視埠與輸出格式](#視埠與輸出格式)） |
| `device_pixel_ratio` | `float` | `1.0` | 裝置像素比，控制輸出解析度 |
| `time_ms` | `int` | `0` | 動畫取樣時刻（毫秒） |
| `dithering` | `str` | `"none"` | 抖動演算法：`none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | 有損編碼品質 |
| `lossless` | `bool \| None` | `None` | 是否無損編碼 |
| `images` | `list` | `None` | 本次渲染的圖片資源（`ImageResource` 或 `(src, bytes)` 元組） |
| `keyframes` | `Mapping` | `None` | 結構化關鍵影格，無需寫入 `@keyframes` |
| `options` | `RenderOptions` | — | 以 `RenderOptions(...)` 彙整參數傳入，欄位與上表一致 |

完整欄位定義見 `takumi_py.RenderOptions`。

### 節點樹範例

```python
png = takumi.render_node(
    {
        "type": "container",
        "style": {"padding": "32px", "backgroundColor": "#111827"},
        "children": [
            {"type": "text", "text": "標題", "style": {"fontSize": 32, "color": "white"}},
            {"type": "text", "text": "正文", "style": {"fontSize": 18, "color": "#9ca3af"}},
        ],
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

### Jinja 範本範例

```python
png = takumi.render_template(
    "card.html.jinja",
    {"title": "Takumi", "subtitle": "Jinja to image"},
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
    }
    """],
    width=800,
    height=None,
    lang="zh-CN",
)
```

> 可透過 `filters={...}` 注入自訂 Jinja 過濾器，或以 `environment=...` 傳入完整 `jinja2.Environment`。範本目錄與環境設定詳見 [takumi-py 範本文件](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md)。

### SVG 輸出範例

```python
svg = takumi.render_svg_html(
    '<div class="card">Hello</div>',
    stylesheets=[".card { width: 800px; color: black; }"],
    width=800,
    height=None,
)
```

### 動畫範例

```python
from takumi_py import AnimationScene

webp = takumi.render_animation(
    [
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "black"}},
            duration_ms=100,
        ),
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "white"}},
            duration_ms=100,
        ),
    ],
    width=64,
    height=64,
    fps=20,
    format="webp",
)
```

> 每幀由 `AnimationScene(node, duration_ms=...)` 構成，`duration_ms` 必須為正數。

---

## 視埠與輸出格式

### 輸出格式

| 情境 | `format` 取值 |
|------|---------------|
| 靜態圖片 | `png`（預設） / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| 動畫 | `webp`（預設） / `apng` / `gif` |

`format="raw"` 回傳列主序 RGBA 位元組串流，用於自訂像素級處理。

### 關於 width 與 height

`width` 與 `height` 的角色不對稱：

- `width` 是**視埠寬度**，文字與版面依它換行、迴流。**應固定**為具體數值（如 `800`），否則畫布會依內容自然寬度延展、文字不換行，尺寸不可控。
- `height` 是**畫布高度**，隨內容增長。`height` 預設值為 `630`；傳入 `height=None` 時，Takumi 會**依內容自動撐高畫布**（auto viewport）。

> [!TIP]
> **建議組合：固定 `width` + `height=None`。** 僅在需要固定尺寸畫布或裁切效果時，才傳入具體的 `height`。

> [!NOTE]
> `width` / `height` 任一在技術上皆可傳 `None` 讓其依版面推斷（如節點自身已宣告尺寸時）；兩者都給定時，輸出尺寸為確定值。

---

## 字型

### 內建字型

| 字型 | family | 類別 |
|------|--------|------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif（italic） |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace（italic） |

模組屬性：

| 屬性 | 說明 |
|------|------|
| `takumi.fonts` | 內建字型檔案名稱清單 |
| `takumi.families` | 已註冊的字型 family 清單 |

### 自動注入

`sdk.Takumi` 上的全部渲染、測量、SVG、動畫、範本方法會自動注入 `takumi.families` 作為字型後備堆疊。若直接呼叫 `takumi.renderer`（原生實例）或透過 `create_renderer()` 建立的獨立實例，則需手動傳入 `font_families=takumi.families`。

### 自訂字型

```python
from takumi_py import FontResource

families = takumi.renderer.register_font(
    FontResource(
        font_bytes,
        name="MyFont",
        weight=400,
        style="normal",
        generic_family="sans-serif",
    )
)
```

`register_font` 回傳註冊的 family 名稱清單，可在後續渲染時作為 `font_families` 傳入。

---

## 渲染器實例

### 原生 Renderer

`takumi.renderer` 是原始的 `takumi_py.Renderer` 實例。直接呼叫時需手動傳入 `font_families`：

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 獨立 Renderer

需要隔離字型 / 圖片 / 資源快取時（長生命週期程序、多租戶情境），可建立獨立的 `Renderer`，內建字型會自動註冊：

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>獨立 Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=None,
    lang="zh-CN",
)
```

`create_renderer()` 接受 `takumi_py.Renderer` 的建構參數：

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `load_default_fonts` | `bool` | `False` | 是否載入 takumi-py 自帶字型（內建字型始終載入） |
| `fonts` | `list[FontResource]` | `None` | 額外註冊的自訂字型 |
| `cache_max_bytes` | `int \| None` | `None` | 資源快取上限（位元組）；`0` 停用 |
| `persistent_images` | `list` | `None` | 持久化圖片資源 |

> 獨立實例不經過模組代理，因此若要保留統一的內建字型後備堆疊，需明確傳入 `font_families=takumi.families`。若明確傳入 `font_families`，模組會尊重呼叫方設定，不再注入預設後備堆疊；`RenderOptions(font_families=...)` 同樣有效。

---

## 傳送渲染結果

渲染得到的圖片為 `bytes`，可透過事件回覆直接傳送：

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# 方式一：以 Image 方法回覆
await event.reply(png, method="Image")

# 方式二：透過 OneBot12 訊息段回覆
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> 不同平台對圖片的封裝由轉接器統一處理。詳見 [MessageBuilder 詳解](../advanced/message-builder.md) 與 [傳送方法規範](../standards/send-method-spec.md)。

---

## 設定

```toml
[Takumi]
enabled = true
```

---

## 相關連結

- PyPI：<https://pypi.org/project/ErisPulse-Takumi/>
- 儲存庫：<https://github.com/ccd2s/ErisPulse-Takumi>（作者 [@ccd2s](https://github.com/ccd2s)）
- 底層引擎：<https://github.com/BalconyJH/takumi-py>
- takumi-py 文件：<https://github.com/BalconyJH/takumi-py/blob/main/docs/index.md>

---

## 下一步

- **把渲染結果傳送出去**：`event.reply(png, method="Image")` 等回覆方式見[事件系統 API - 回覆方法](../api-reference/event-system.md)
- **組合更複雜的傳出訊息**（圖 + 文 + @）：[訊息建構器](../advanced/message-builder.md)
- **渲染 + 定時推送**：搭配 [ErisPulse-Cron](cron.md) 製作週期性資料卡片