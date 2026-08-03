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

## 相关链接

- PyPI：<https://pypi.org/project/ErisPulse-Takumi/>
- 仓库：<https://github.com/ccd2s/ErispulseTakumi>（作者 [@ccd2s](https://github.com/ccd2s)）
- 底层引擎：<https://github.com/BalconyJH/takumi-py>
