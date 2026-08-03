# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) 是由 ccd2s 維護的 **第三方圖片渲染模組**，基於 [takumi-py](https://github.com/BalconyJH/takumi-py)，讓您在 Bot 中渲染出圖片：HTML、節點樹、Jinja 模板、SVG、動畫都不在話下，並且 **內建中英文字型**（Noto Sans SC / Roboto / Source Code Pro），無需額外配置字型。

> [!IMPORTANT]  
> Takumi **不是** ErisPulse 框架的內置功能，需要單獨安裝：  
>  
> ```bash
> epsdk install Takumi
> ```

非常適合以下場景：

- 將資料/統計渲染成精美的卡片圖片發送
- 將 Markdown / 長文本渲染成排版穩定的圖片，避免平台樣式差異
- 生成 SVG / 動畫，用於動態視覺效果
- 中英混排的圖文輸出（內建字型開箱即用）

---

## 安裝與啟用

```bash
epsdk install Takumi
```

安裝後模組會自動加載，在配置文件中確認啟用即可：

```toml
[Takumi]
enabled = true
```

---

## 快速入門

模組自動加載後，透過模組管理器獲取，也可以用 `sdk` 快捷方式：

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
    lang="zh-CN",
)
```

`png` 是 `bytes`，可透過 `event.reply(png, method="Image")` 發送（詳見 [發送渲染結果](#發送渲染結果)）。

### 渲染節點樹

無需手寫 HTML，用字典描述結構即可，適合程式化拼裝：

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "中文和 English 都可直接渲染",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=200,
    lang="zh-CN",
)
```

---

## 字型與渲染器

### 內建字型

Takumi 已經打包了常用字型，無需額外安裝：

| 資源 | 說明 |
|------|------|
| `takumi.fonts` | 內建字型檔案名列表 |
| `takumi.families` | 已註冊的字型 family 列表 |

便捷方法（`render_html` / `render_node`）會自動注入這套字型回退堆疊；如果你直接調用底層 renderer，則需要自行傳入 `font_families`。

### 原生 Renderer

`takumi.renderer` 是原始的 `takumi_py.Renderer` 實例。便捷方法已自動注入內建字型回退堆疊；**直接調用 renderer 時需自行傳入 families**：

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 獨立 Renderer

需要隔離字型 / 圖片 / 資源快取時（例如長生命週期進程、多租戶場景），可以創建一個新的 `Renderer`，內建字型會自動註冊：

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

- `load_default_fonts=False`（預設）：僅加載內建字型
- `load_default_fonts=True`：同時加載 Takumi 自帶字型
- `fonts=[...]`：在預設基礎上註冊自訂字型

> 獨立實例不經過模組代理，因此若要保留統一的內建字型回退堆疊，需顯式傳入 `font_families=takumi.families`。

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

# 方式二：透過 OneBot12 消息段回覆
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> 不同平台對圖片的封裝由適配器統一處理，無需關心底層差異。詳見 [MessageBuilder 詳解](../advanced/message-builder.md) 與 [發送方法規範](../standards/send-method-spec.md)。

---

## 相關連結

- PyPI：<https://pypi.org/project/ErisPulse-Takumi/>
- 倉庫：<https://github.com/ccd2s/ErispulseTakumi>（作者 [@ccd2s](https://github.com/ccd2s)）
- 底層引擎：<https://github.com/BalconyJH/takumi-py>