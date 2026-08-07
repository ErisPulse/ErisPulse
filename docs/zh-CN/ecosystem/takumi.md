# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) 是 ccd2s 维护的 **第三方图片渲染模块**，基于 [takumi-py](https://github.com/BalconyJH/takumi-py)，让 Bot 能够将 HTML、节点树、Jinja 模板、SVG、动画渲染为图片。模块 **内置中英文字体**（Noto Sans SC / Roboto / Source Code Pro），无需额外配置。

> [!IMPORTANT]
> Takumi **不是** ErisPulse 框架的内置功能，需要单独安装：
>
> ```bash
> epsdk install Takumi
> ```

适用场景：

- 将数据/统计渲染为卡片图片
- 将 Markdown / 长文本渲染为排版稳定的图片，规避平台样式差异
- 生成 SVG / 动画，实现动态视觉效果
- 中英混排图文（内置字体开箱即用）

---

## 安装与启用

```bash
epsdk install Takumi
```

安装后模块自动加载，在配置中确认启用：

```toml
[Takumi]
enabled = true
```

---

## 快速上手

模块自动加载后，通过模块管理器获取，或使用 `sdk` 快捷方式：

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# 等价写法：takumi = sdk.Takumi
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
    height=None,   # 按内容自动撑高
    lang="zh-CN",
)
```

### 渲染节点树

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

`png` 是 `bytes`，可通过 `event.reply(png, method="Image")` 发送（详见 [发送渲染结果](#发送渲染结果)）。

---

## 渲染 API

`sdk.Takumi` 代理了底层 `takumi_py.Renderer` 的全部能力：所有渲染、测量、SVG、动画、模板方法都可直接在 `sdk.Takumi` 上调用。对这些方法，模块会在调用时**自动注入内置字体回退栈**（`takumi.families`），无需手动传 `font_families`；若显式传入则尊重调用方设置。

### 方法总览

| 类别 | 方法 | 返回 | 说明 |
|------|------|------|------|
| 静态渲染 | `render_html(html, ...)` | `bytes` | 渲染 HTML 字符串 |
| | `render_node(node, ...)` | `bytes` | 渲染节点树（dict） |
| | `render_template(name, ctx, ...)` | `bytes` | 渲染 Jinja 模板 |
| | `render_compiled(node, ...)` | `bytes` | 渲染预编译节点 |
| SVG 输出 | `render_svg_html(html, ...)` | `str` | 输出 SVG（HTML 输入） |
| | `render_svg_node(node, ...)` | `str` | 输出 SVG（节点树输入） |
| | `render_svg_template(name, ctx, ...)` | `str` | 输出 SVG（模板输入） |
| | `render_svg_compiled(node, ...)` | `str` | 输出 SVG（预编译输入） |
| 动画 | `render_animation(scenes, ...)` | `bytes` | 编码多帧动画 |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | 取序列某一时刻帧 |
| 测量 | `measure_node(node, ...)` | `dict` | 测量节点树布局 |
| | `measure_html(html, ...)` | `dict` | 测量 HTML 布局 |
| | `measure_compiled(node, ...)` | `dict` | 测量预编译节点 |
| 编译 | `compile_node(node)` | `CompiledNode` | 编译节点树 |
| | `compile_html(html, ...)` | `CompiledNode` | 编译 HTML |
| 字体 | `register_font(font)` | `list[str]` | 注册自定义字体，返回 family 列表 |
| | `register_fonts(fonts)` | `list[str]` | 批量注册 |

> `CompiledNode` 暴露 `resource_urls()` 方法，可预先发现待加载的 HTTP(S) 图片引用，便于提前准备资源。

### 通用参数

以下参数适用于静态渲染与 SVG 方法（动画方法另有 `fps` 等，见对应示例）：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `stylesheets` | `list[str]` | `None` | 文档级 CSS 字符串列表；内联 `style` 仍随 HTML 一起解析 |
| `width` | `int \| None` | `1200` | 视口宽度（像素）；`None` 按布局推断 |
| `height` | `int \| None` | `630` | 画布高度（像素）；`None` 按内容自动撑高（见 [视口与输出格式](#视口与输出格式)） |
| `lang` | `str \| None` | `None` | BCP-47 语言标签（如 `zh-CN`），影响文本整形与换行 |
| `font_families` | `list[str]` | 自动注入 | 字体回退栈；便捷方法默认注入内置字体 |
| `format` | `str` | `"png"` | 输出格式（见 [视口与输出格式](#视口与输出格式)） |
| `device_pixel_ratio` | `float` | `1.0` | 设备像素比，控制输出分辨率 |
| `time_ms` | `int` | `0` | 动画采样时刻（毫秒） |
| `dithering` | `str` | `"none"` | 抖动算法：`none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | 有损编码质量 |
| `lossless` | `bool \| None` | `None` | 是否无损编码 |
| `images` | `list` | `None` | 本次渲染的图片资源（`ImageResource` 或 `(src, bytes)` 元组） |
| `keyframes` | `Mapping` | `None` | 结构化关键帧，无需写入 `@keyframes` |
| `options` | `RenderOptions` | — | 以 `RenderOptions(...)` 聚合传参，字段与上表一致 |

完整字段定义见 `takumi_py.RenderOptions`。

### 节点树示例

```python
png = takumi.render_node(
    {
        "type": "container",
        "style": {"padding": "32px", "backgroundColor": "#111827"},
        "children": [
            {"type": "text", "text": "标题", "style": {"fontSize": 32, "color": "white"}},
            {"type": "text", "text": "正文", "style": {"fontSize": 18, "color": "#9ca3af"}},
        ],
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

### Jinja 模板示例

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

> 可通过 `filters={...}` 注入自定义 Jinja 过滤器，或 `environment=...` 传入完整 `jinja2.Environment`。模板目录与环境配置详见 [takumi-py 模板文档](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md)。

### SVG 输出示例

```python
svg = takumi.render_svg_html(
    '<div class="card">Hello</div>',
    stylesheets=[".card { width: 800px; color: black; }"],
    width=800,
    height=None,
)
```

### 动画示例

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

> 每帧由 `AnimationScene(node, duration_ms=...)` 构成，`duration_ms` 必须为正数。

---

## 视口与输出格式

### 输出格式

| 场景 | `format` 取值 |
|------|---------------|
| 静态图片 | `png`（默认） / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| 动画 | `webp`（默认） / `apng` / `gif` |

`format="raw"` 返回行主序 RGBA 字节流，用于自定义像素级处理。

### 关于 width 与 height

`width` 与 `height` 的角色不对称：

- `width` 是**视口宽度**，文本与布局按它换行、回流。**应固定**为具体数值（如 `800`），否则画布会按内容自然宽度拉伸、文字不换行，尺寸不可控。
- `height` 是**画布高度**，随内容增长。`height` 默认值为 `630`；传入 `height=None` 时，Takumi 会**根据内容自动撑高画布**（auto viewport）。

> [!TIP]
> **推荐组合：固定 `width` + `height=None`。** 仅当需要固定尺寸画布或裁切效果时，才传入具体的 `height`。

> [!NOTE]
> `width` / `height` 任一在技术上都可传 `None` 让其按布局推断（如节点自身已声明尺寸时）；两者都给定时，输出尺寸为确定值。

---

## 字体

### 内置字体

| 字体 | family | 类别 |
|------|--------|------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif（italic） |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace（italic） |

模块属性：

| 属性 | 说明 |
|------|------|
| `takumi.fonts` | 内置字体文件名列表 |
| `takumi.families` | 已注册的字体 family 列表 |

### 自动注入

`sdk.Takumi` 上的全部渲染、测量、SVG、动画、模板方法会自动注入 `takumi.families` 作为字体回退栈。若直接调用 `takumi.renderer`（原生实例）或通过 `create_renderer()` 创建的独立实例，则需手动传 `font_families=takumi.families`。

### 自定义字体

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

`register_font` 返回注册的 family 名称列表，可在后续渲染时作为 `font_families` 传入。

---

## 渲染器实例

### 原生 Renderer

`takumi.renderer` 是原始的 `takumi_py.Renderer` 实例。直接调用时需手动传 `font_families`：

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 独立 Renderer

需要隔离字体 / 图片 / 资源缓存时（长生命周期进程、多租户场景），可创建独立的 `Renderer`，内置字体会自动注册：

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>独立 Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=None,
    lang="zh-CN",
)
```

`create_renderer()` 接受 `takumi_py.Renderer` 的构造参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `load_default_fonts` | `bool` | `False` | 是否加载 takumi-py 自带字体（内置字体始终加载） |
| `fonts` | `list[FontResource]` | `None` | 额外注册的自定义字体 |
| `cache_max_bytes` | `int \| None` | `None` | 资源缓存上限（字节）；`0` 禁用 |
| `persistent_images` | `list` | `None` | 持久化图片资源 |

> 独立实例不经过模块代理，因此若要保留统一的内置字体回退栈，需显式传入 `font_families=takumi.families`。若显式传入 `font_families`，模块会尊重调用方设置，不再注入默认回退栈；`RenderOptions(font_families=...)` 同样有效。

---

## 发送渲染结果

渲染得到的图片为 `bytes`，可通过事件回复直接发送：

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# 方式一：以 Image 方法回复
await event.reply(png, method="Image")

# 方式二：通过 OneBot12 消息段回复
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> 不同平台对图片的封装由适配器统一处理。详见 [MessageBuilder 详解](../advanced/message-builder.md) 与 [发送方法规范](../standards/send-method-spec.md)。

---

## 配置

```toml
[Takumi]
enabled = true
```

---

## 相关链接

- PyPI：<https://pypi.org/project/ErisPulse-Takumi/>
- 仓库：<https://github.com/ccd2s/ErisPulse-Takumi>（作者 [@ccd2s](https://github.com/ccd2s)）
- 底层引擎：<https://github.com/BalconyJH/takumi-py>
- takumi-py 文档：<https://github.com/BalconyJH/takumi-py/blob/main/docs/index.md>
