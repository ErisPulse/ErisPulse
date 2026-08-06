# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) 是由 ccd2s 維護的 **第三方圖片渲染模組**，基於 [takumi-py](https://github.com/BalconyJH/takumi-py)，讓你在 Bot 中渲染出圖片：HTML、節點樹、Jinja 模板、SVG、動畫都不在話下，並且 **內建中英文字體**（Noto Sans SC / Roboto / Source Code Pro），無需額外配置字體。

> [!IMPORTANT]
> Takumi **不是** ErisPulse 框架的內建功能，需要單獨安裝：
>
> ```bash
> epsdk install Takumi
> ```

非常適合以下場景：

- 把資料/統計渲染成精緻的卡片圖片發送
- 把 Markdown / 長文字渲染成排版穩定的圖片，避免平台樣式差異
- 產生 SVG / 動畫，用於動態視覺效果
- 中英混排的圖文輸出（內建字體開箱即用）

---

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 安裝與啟用

```bash
epsdk install Takumi
```

安裝後模組會自動載入，在設定檔中確認啟用即可：

```toml
[Takumi]
enabled = true
```

---

## 快速上手

模組自動載入後，透過模組管理器獲取，也可以用 `sdk` 快捷方式：

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# 等價寫法：takumi = sdk.Takumi
```

### 渲染 HTML

最常用的方式 —— 把一段 HTML + CSS 字串渲染成 PNG：

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
      height: 400px;
      padding: 48px;
      color: white;
      background: #111827;
      font-family: "Noto Sans SC";
    }
    """],
    width=800,
    height=400,
    lang="zh-TW",
)
```

`png` 是 `bytes`，可透過 `event.reply(png, method="Image")` 發送（詳見 [發送渲染結果](#發送渲染結果)）。

### 渲染節點樹

無需手寫 HTML，用字典描述結構即可，適合程序化拼裝：

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "中文和 English 都可直接渲染",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=200,
    lang="zh-TW",
)
```

---

## 字體與渲染器

### 內建字體

Takumi 已打包常用字體，無需額外安裝：

| 資源 | 說明 |
|------|------|
| `takumi.fonts` | 內建字體檔案名稱列表 |
| `takumi.families` | 已註冊的字體 family 列表 |

便捷方法（`render_html` / `render_node`）會自動注入這套字體回退堆疊；如果你直接呼叫底層 renderer，則需要自行傳入 `font_families`。

### 原生 Renderer

`takumi.renderer` 是原始的 `takumi_py.Renderer` 實例。便捷方法已自動注入內建字體回退堆疊；**直接呼叫 renderer 時需自行傳入 families**：

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 獨立 Renderer

需要隔離字體 / 圖片 / 資源快取時（例如長生命週期程序、多租戶場景），可以建立一個新的 `Renderer`，內建字體會自動註冊：

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>獨立 Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=200,
    lang="zh-CN",
)
```

`create_renderer()` 接受 `takumi_py.Renderer` 的建構參數：

- `load_default_fonts=False`（預設）：僅載入內建字體
- `load_default_fonts=True`：同時載入 Takumi 自帶字體
- `fonts=[...]`：在預設基礎上註冊自訂字體

> 獨立實例不經過模組代理，因此若要保留統一的內建字體回退堆疊，需顯式傳入 `font_families=takumi.families`。

若顯式傳入 `font_families`，模組會尊重呼叫方設定，不再注入預設回退堆疊。`RenderOptions(font_families=...)` 同樣有效。

---

## 發送渲染結果

渲染得到圖片後，可以透過事件回覆直接發送：

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# 方式一：直接以 Image 方法回覆
await event.reply(png, method="Image")

# 方式二：透過 OneBot12 訊息段回覆
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> 不同平台對圖片的封裝由適配器統一處理，無需關心底層差異。詳見 [MessageBuilder 詳解](../advanced/message-builder.md) 與 [發送方法規範](../standards/send-method-spec.md)。

---

## 實戰避坑（踩出來的慘痛教訓）

下面這些文件裡沒寫，是拿 Takumi 做一整個數據可視化模組（聲呐圖、雷達圖那種，節點幾十個、還要畫連線和標籤）時一行行試出來的。挑值錢的記一下，能幫你少走幾小時彎路。

### 1. 別用 SVG `<text>`，它不渲染

最大的坑，沒有之一。你想在 `<svg>` 裡畫節點、旁邊用 `<text>` 標個名字——**渲染出來文字是空的**。不管給 `<text>` 加 `font-family`，還是在 `<svg>` 根上設繼承，都沒用，中英文一律不顯示，圖裡只剩裸的形狀。

實測結論：`takumi-py` 不繪製內聯 SVG 的文本元素。所以正確套路是：

- SVG 只畫**形狀**（圓、線、多邊形）
- 文字全部走 **HTML**：把 `<svg>` 丟進一個 `position: relative` 的容器，再用絕對定位的 `<div>` 把標籤蓋到對應座標上

```python
W = H = 600
html = f"""
<div style='position:relative;width:{W}px;height:{H}px'>
  <svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>
    <!-- 只畫圓和線 -->
  </svg>
  <div style='position:absolute;left:{x}px;top:{y}px;transform:translate(-50%,-50%)'>名字</div>
</div>
"""
```

座標對得上的前提：SVG 用**固定**的 `width`/`height`（別圖省事寫 `width:100%`），這樣像素和容器 1:1，div 的 `left`/`top` 直接填 SVG 裡的座標即可。

### 2. CSS 必須走 `stylesheets`，別塞整篇 HTML 文檔

`render_html(html, ...)` 的第一個參數是**正文 HTML**，不是完整文檔。你要是圖省事傳一個：

```python
takumi.render_html("<!DOCTYPE html><html><head><style>...</style></head><body>...</body></html>")
```

樣式會**靜默失效**——圖照樣出，但跟沒 CSS 一樣，亂七八糟。排錯時你還會懷疑自己 CSS 寫錯了，其實是傳法不對，冤。

正確姿勢永遠是：正文一個參數、CSS 一個參數。

```python
takumi.render_html(body_html, stylesheets=[css_str], width=..., height=..., lang="zh-TW")
```

### 3. `height` 是裁切高度，不會自動撐高

`width` 是視口寬，`height` 是畫布高——**超出 `height` 的內容直接被切掉**，不會像瀏覽器那樣自動往下長。所以總高度得自己估：每個區塊高 + padding + 卡片間距，加起來傳進去。

經驗是**寧多勿少**。底部多幾十像素留白沒人盯，頂部內容被切一刀那這張圖就廢了。遇到動態內容（列表項數不定）就按項數現算：

```python
height = padding * 2 + header_h + sum(每項高) + 間隙 * (項數 - 1) + 30  # 末尾留點保險
```

### 4. 字體自動注入只管 HTML 文本

便捷方法（`render_html` / `render_node`）會自動把內置字體回退堆塞進去，但**只對 HTML 文本生效**。所以第 1 條說"文字走 HTML"還有這層好處——順帶白嫖了中文字體，不用自己操心 `font_families`。

要是你直接調底層 renderer（`takumi.renderer.render_html`），就得自己傳 `font_families=takumi.families`，別忘。

### 5. 一個不睜眼也能調試的小技巧

改完樣式想確認"某段中文到底渲沒渲染出來"，又懶得每次開圖看？讓它吐原始像素來數：

```python
data = takumi.render_html(body, stylesheets=[css], width=W, height=H,
                          lang="zh-TW", format="raw")  # raw 是 RGBA 字節流
dark = sum(1 for i in range(0, len(data), 4)
           if data[i] < 120 and data[i+1] < 120 and data[i+2] < 120 and data[i+3] > 128)
```

淺色背景下，"有文字"和"沒文字"的墨點數是 4000+ 和 0 的區別——一眼就能看出你那行 `<div>` 到底生效沒。比肉眼看 PNG 快多了，第 1 條那個 SVG 坑我就是這麼驗出來的。

### 6. 深淺色主題：換套 stylesheet 就行

Takumi 本身不在乎你什麼主題，顏色全在你自己的 CSS 裡。所以做明暗切換特別輕——備兩套顏色，按當前小時或用戶設置挑一套塞進 `stylesheets`：

```python
if 19 <= local_hour or local_hour < 7:
    t = {"page": "#000000", "card": "#1c1c1e", "ink": "#f5f5f7", "sep": "#38383a"}   # 深色
else:
    t = {"page": "#f5f5f7", "card": "#ffffff", "ink": "#1d1d1f", "sep": "#e5e5ea"}   # 淺色
css = CSS_TEMPLATE.replace("__INK__", t["ink"]).replace("__CARD__", t["card"])  # 以此類推
```

> 小提醒：CSS 自帶的 `var(--xxx)` 變量在 takumi 裡**不一定吃**，穩妥起見在 Python 裡直接把顏色字串替換進模板，繞開這個不確定性。

## 相關連結

- PyPI：<https://pypi.org/project/ErisPulse-Takumi/>
- 倉庫：<https://github.com/ccd2s/ErispulseTakumi>（作者 [@ccd2s](https://github.com/ccd2s)）
- 底層引擎：<https://github.com/BalconyJH/takumi-py>