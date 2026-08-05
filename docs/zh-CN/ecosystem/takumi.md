# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) 是ccd2s维护的 **第三方图片渲染模块**，基于 [takumi-py](https://github.com/BalconyJH/takumi-py)，让你在 Bot 中渲染出图片：HTML、节点树、Jinja 模板、SVG、动画都不在话下，并且 **内置中英文字体**（Noto Sans SC / Roboto / Source Code Pro），无需额外配置字体。

> [!IMPORTANT]
> Takumi **不是** ErisPulse 框架的内置功能，需要单独安装：
>
> ```bash
> epsdk install Takumi
> ```

非常适合以下场景：

- 把数据/统计渲染成精美的卡片图片发送
- 把 Markdown / 长文本渲染成排版稳定的图片，避免平台样式差异
- 生成 SVG / 动画，用于动态视觉效果
- 中英混排的图文输出（内置字体开箱即用）

---

## 安装与启用

```bash
epsdk install Takumi
```

安装后模块会自动加载，在配置文件中确认启用即可：

```toml
[Takumi]
enabled = true
```

---

## 快速上手

模块自动加载后，通过模块管理器获取，也可以用 `sdk` 快捷方式：

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# 等价写法：takumi = sdk.Takumi
```

### 渲染 HTML

最常用的方式 —— 把一段 HTML + CSS 字符串渲染成 PNG：

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

`png` 是 `bytes`，可通过 `event.reply(png, method="Image")` 发送（详见 [发送渲染结果](#发送渲染结果)）。

### 渲染节点树

无需手写 HTML，用字典描述结构即可，适合程序化拼装：

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

## 字体与渲染器

### 内置字体

Takumi 已经打包了常用字体，无需额外安装：

| 资源 | 说明 |
|------|------|
| `takumi.fonts` | 内置字体文件名列表 |
| `takumi.families` | 已注册的字体 family 列表 |

便捷方法（`render_html` / `render_node`）会自动注入这套字体回退栈；如果你直接调用底层 renderer，则需要自行传入 `font_families`。

### 原生 Renderer

`takumi.renderer` 是原始的 `takumi_py.Renderer` 实例。便捷方法已自动注入内置字体回退栈；**直接调用 renderer 时需自行传入 families**：

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 独立 Renderer

需要隔离字体 / 图片 / 资源缓存时（例如长生命周期进程、多租户场景），可以创建一个新的 `Renderer`，内置字体会自动注册：

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>独立 Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=200,
    lang="zh-CN",
)
```

`create_renderer()` 接受 `takumi_py.Renderer` 的构造参数：

- `load_default_fonts=False`（默认）：仅加载内置字体
- `load_default_fonts=True`：同时加载 Takumi 自带字体
- `fonts=[...]`：在默认基础上注册自定义字体

> 独立实例不经过模块代理，因此若要保留统一的内置字体回退栈，需显式传入 `font_families=takumi.families`。

若显式传入 `font_families`，模块会尊重调用方设置，不再注入默认回退栈。`RenderOptions(font_families=...)` 同样有效。

---

## 发送渲染结果

渲染得到图片后，可以通过事件回复直接发送：

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# 方式一：直接以 Image 方法回复
await event.reply(png, method="Image")

# 方式二：通过 OneBot12 消息段回复
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> 不同平台对图片的封装由适配器统一处理，无需关心底层差异。详见 [MessageBuilder 详解](../advanced/message-builder.md) 与 [发送方法规范](../standards/send-method-spec.md)。

---

## 实战避坑（踩出来的血泪）

下面这些文档里没写，是拿 Takumi 做一整个数据可视化模块（声呐图、雷达图那种，节点几十个、还要画连线和标签）时一行行试出来的。挑值钱的记一下，能帮你少走几小时弯路。

### 1. 别用 SVG `<text>`，它不渲染

最大的坑，没有之一。你想在 `<svg>` 里画节点、旁边用 `<text>` 标个名字——**渲染出来文字是空的**。不管给 `<text>` 加 `font-family`，还是在 `<svg>` 根上设继承，都没用，中英文一律不显示，图里只剩裸的形状。

实测结论：`takumi-py` 不绘制内联 SVG 的文本元素。所以正确套路是：

- SVG 只画**形状**（圆、线、多边形）
- 文字全部走 **HTML**：把 `<svg>` 丢进一个 `position: relative` 的容器，再用绝对定位的 `<div>` 把标签盖到对应坐标上

```python
W = H = 600
html = f"""
<div style='position:relative;width:{W}px;height:{H}px'>
  <svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>
    <!-- 只画圆和线 -->
  </svg>
  <div style='position:absolute;left:{x}px;top:{y}px;transform:translate(-50%,-50%)'>名字</div>
</div>
"""
```

坐标对得上的前提：SVG 用**固定**的 `width`/`height`（别图省事写 `width:100%`），这样像素和容器 1:1，div 的 `left`/`top` 直接填 SVG 里的坐标即可。

### 2. CSS 必须走 `stylesheets`，别塞整篇 HTML 文档

`render_html(html, ...)` 的第一个参数是**正文 HTML**，不是完整文档。你要是图省事传一个：

```python
takumi.render_html("<!DOCTYPE html><html><head><style>...</style></head><body>...</body></html>")
```

样式会**静默失效**——图照样出，但跟没 CSS 一样，乱七八糟。排错时你还会怀疑自己 CSS 写错了，其实是传法不对，冤。

正确姿势永远是：正文一个参数、CSS 一个参数。

```python
takumi.render_html(body_html, stylesheets=[css_str], width=..., height=..., lang="zh-CN")
```

### 3. `height` 是裁切高度，不会自动撑高

`width` 是视口宽，`height` 是画布高——**超出 `height` 的内容直接被切掉**，不会像浏览器那样自动往下长。所以总高度得自己估：每个区块高 + padding + 卡片间距，加起来传进去。

经验是**宁多勿少**。底部多几十像素留白没人盯，顶部内容被切一刀那这张图就废了。遇到动态内容（列表项数不定）就按项数现算：

```python
height = padding * 2 + header_h + sum(每项高) + 间隙 * (项数 - 1) + 30  # 末尾留点保险
```

### 4. 字体自动注入只管 HTML 文本

便捷方法（`render_html` / `render_node`）会自动把内置字体回退栈塞进去，但**只对 HTML 文本生效**。所以第 1 条说"文字走 HTML"还有这层好处——顺带白嫖了中文字体，不用自己操心 `font_families`。

要是你直接调底层 renderer（`takumi.renderer.render_html`），就得自己传 `font_families=takumi.families`，别忘。

### 5. 一个不睁眼也能调试的小技巧

改完样式想确认"某段中文到底渲没渲染出来"，又懒得每次开图看？让它吐原始像素来数：

```python
data = takumi.render_html(body, stylesheets=[css], width=W, height=H,
                          lang="zh-CN", format="raw")  # raw 是 RGBA 字节流
dark = sum(1 for i in range(0, len(data), 4)
           if data[i] < 120 and data[i+1] < 120 and data[i+2] < 120 and data[i+3] > 128)
```

浅色背景下，"有文字"和"没文字"的墨点数是 4000+ 和 0 的区别——一眼就能看出你那行 `<div>` 到底生效没。比肉眼盯 PNG 快多了，第 1 条那个 SVG 坑我就是这么验出来的。

### 6. 深浅色主题：换套 stylesheet 就行

Takumi 本身不在乎你什么主题，颜色全在你自己的 CSS 里。所以做明暗切换特别轻——备两套颜色，按当前小时或用户设置挑一套塞进 `stylesheets`：

```python
if 19 <= local_hour or local_hour < 7:
    t = {"page": "#000000", "card": "#1c1c1e", "ink": "#f5f5f7", "sep": "#38383a"}   # 深色
else:
    t = {"page": "#f5f5f7", "card": "#ffffff", "ink": "#1d1d1f", "sep": "#e5e5ea"}   # 浅色
css = CSS_TEMPLATE.replace("__INK__", t["ink"]).replace("__CARD__", t["card"])  # 以此类推
```

> 小提醒：CSS 自带的 `var(--xxx)` 变量在 takumi 里**不一定吃**，稳妥起见在 Python 里直接把颜色字符串替换进模板，绕开这个不确定性。

---

## 相关链接

- PyPI：<https://pypi.org/project/ErisPulse-Takumi/>
- 仓库：<https://github.com/ccd2s/ErispulseTakumi>（作者 [@ccd2s](https://github.com/ccd2s)）
- 底层引擎：<https://github.com/BalconyJH/takumi-py>
