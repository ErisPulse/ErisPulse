# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) is a **third-party image rendering module** maintained by ccd2s. Based on [takumi-py](https://github.com/BalconyJH/takumi-py), it allows you to render images in your Bot: HTML, node trees, Jinja templates, SVG, and animations are all no problem. Moreover, it **includes built-in fonts** (Noto Sans SC / Roboto / Source Code Pro), so no additional font configuration is needed.

> [!IMPORTANT]
> Takumi is **not** a built-in feature of the ErisPulse framework and requires separate installation:
>
> ```bash
> epsdk install Takumi
> ```

It is suitable for the following scenarios:

- Rendering data/statistics into exquisite card images for sending
- Rendering Markdown / long texts into images with stable layout, avoiding platform style differences
- Generating SVG / animations for dynamic visual effects
- Bilingual text and image output (built-in fonts work out of the box)

---

## Installation and Activation

```bash
epsdk install Takumi
```

After installation, the module loads automatically. Simply enable it in the configuration file:

```toml
[Takumi]
enabled = true

## Quick Start

Once modules are automatically loaded, obtain them via the Module Manager, or use the `sdk` shortcut:

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# Equivalent writing: takumi = sdk.Takumi
```

### Render HTML

The most common method — rendering a segment of HTML + CSS string into PNG:

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>Hello, ErisPulse</h1>
      <p>Rendered by Takumi</p>
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

`png` is `bytes`, which can be sent via `event.reply(png, method="Image")` (see [Sending Rendered Results](#sending-rendered-results) for details).

### Render Node Tree

No need to write HTML manually; describe the structure using a dictionary. It is suitable for procedural assembly:

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

Please return the complete translated Markdown content directly without any other text.

## Fonts and Renderer

### Built-in Fonts

Takumi has bundled common fonts, no additional installation required:

| Resource | Description |
|------|------|
| `takumi.fonts` | List of built-in font file names |
| `takumi.families` | List of registered font families |

Convenience methods (`render_html` / `render_node`) automatically inject this font fallback stack; if you call the underlying renderer directly, you need to pass in `font_families` yourself.

### Native Renderer

`takumi.renderer` is the raw `takumi_py.Renderer` instance. Convenience methods automatically inject the built-in font fallback stack; **when calling the renderer directly, you must pass in `families`**:

```python
png = takumi.renderer.render_html(
    "<div>Hello World</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### Standalone Renderer

If isolation of fonts / images / resource caches is required (e.g., long-lived processes, multi-tenant scenarios), you can create a new `Renderer`; built-in fonts are registered automatically:

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>Standalone Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=200,
    lang="zh-CN",
)
```

`create_renderer()` accepts the constructor arguments of `takumi_py.Renderer`:

- `load_default_fonts=False` (default): Only load built-in fonts
- `load_default_fonts=True`: Load both built-in and Takumi bundled fonts
- `fonts=[...]`: Register custom fonts on top of defaults

> Standalone instances do not go through the module proxy, so to preserve a unified built-in font fallback stack, you must explicitly pass `font_families=takumi.families`.

If you explicitly pass `font_families`, the module will respect the caller's settings and will no longer inject the default fallback stack. `RenderOptions(font_families=...)` is also valid.

---

## Sending Rendered Results

After the image is rendered, you can send it directly via an event reply:

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# Method 1: Reply directly using the Image method
await event.reply(png, method="Image")

# Method 2: Reply via OneBot12 message segments
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> Different platforms encapsulate images uniformly via adapters; no need to worry about underlying differences. See [MessageBuilder Details](../advanced/message-builder.md) and [Send Method Specifications](../standards/send-method-spec.md).

---

Please return the complete translated Markdown content directly without any other text.

## Practical Pitfalls (Hard-earned Lessons)

The following content is not found in the documentation. It was tested line by line while using Takumi to build an entire data visualization module (sonar charts, radar charts, etc., with dozens of nodes and the need to draw connections and labels). I've noted the valuable findings here to help you save a few hours of detours.

### 1. Don't Use SVG `<text>`, It Doesn't Render

The biggest pitfall, bar none. You want to draw nodes in an `<svg>` and annotate them with a `<text>` tag next to them—**the rendered text is empty**. Whether you add `font-family` to the `<text>` tag or set inheritance on the `<svg>` root, it doesn't work. Chinese and English text do not display at all; the chart is left with only the naked shapes.

Tested conclusion: `takumi-py` does not render inline SVG text elements. So the correct approach is:

- SVG only draws **shapes** (circles, lines, polygons)
- All text goes through **HTML**: put the `<svg>` inside a `position: relative` container, and use absolutely positioned `<div>` tags to cover the corresponding coordinates with labels

```python
W = H = 600
html = f"""
<div style='position:relative;width:{W}px;height:{H}px'>
  <svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>
    <!-- Only draw circles and lines -->
  </svg>
  <div style='position:absolute;left:{x}px;top:{y}px;transform:translate(-50%,-50%)'>Name</div>
</div>
"""
```

The prerequisite for correct coordinate matching: SVG must use **fixed** `width`/`height` (don't be lazy and write `width:100%`). This ensures 1:1 pixel mapping with the container, so the div's `left`/`top` can simply be filled with the coordinates inside the SVG.

### 2. CSS Must Go Through `stylesheets`, Don't Stuff the Entire HTML Document

The first parameter of `render_html(html, ...)` is the **body HTML**, not the complete document. If you are lazy and pass one:

```python
takumi.render_html("<!DOCTYPE html><html><head><style>...</style></head><body>...</body></html>")
```

Styles will **silently fail**—the chart will be generated, but it will look messy, just like it has no CSS. When debugging, you will suspect you wrote the CSS wrong, but actually, the passing method is incorrect. Unjustly.

The correct way is always: one parameter for body, one parameter for CSS.

```python
takumi.render_html(body_html, stylesheets=[css_str], width=..., height=..., lang="zh-CN")
```

### 3. `height` Is the Clipping Height, It Won't Auto-Expand

`width` is the viewport width, `height` is the canvas height—**content exceeding `height` is directly clipped**, just like in an image format, it won't automatically grow downward like a browser. Therefore, the total height must be estimated by yourself: sum of the height of each block + padding + card spacing, and pass that in.

The rule of thumb is **prefer more over less**. Leaving extra white space at the bottom is fine, but if the top content is clipped, the chart is useless. For dynamic content (variable number of list items), calculate it on the fly:

```python
height = padding * 2 + header_h + sum(每项高) + 间隙 * (项数 - 1) + 30  # Leave some buffer at the end
```

### 4. Font Auto-Injection Only Handles HTML Text

Convenient methods (`render_html` / `render_node`) will automatically inject the built-in font fallback stack, but it **only applies to HTML text**. That's why "text goes through HTML" in point #1 is beneficial—you also get the Chinese fonts for free without having to worry about `font_families`.

If you directly call the low-level renderer (`takumi.renderer.render_html`), you must pass `font_families=takumi.families` yourself. Don't forget.

### 5. A Debugging Trick That Works With Eyes Closed

After changing styles, you want to verify "whether a specific chunk of Chinese was actually rendered", but you are too lazy to open the image every time? Let it spit out the raw pixels to count:

```python
data = takumi.render_html(body, stylesheets=[css], width=W, height=H,
                          lang="zh-CN", format="raw")  # raw is RGBA byte stream
dark = sum(1 for i in range(0, len(data), 4)
           if data[i] < 120 and data[i+1] < 120 and data[i+2] < 120 and data[i+3] > 128)
```

In a light background, the difference in ink dot counts between "has text" and "no text" is 4000+ and 0 respectively—you can tell at a glance whether that line of `<div>` is taking effect or not. This is much faster than staring at a PNG with your eyes, which is how I verified the SVG pitfall in point #1.

### 6. Dark/Light Theme: Just Swap the Stylesheet

Takumi itself doesn't care what theme you use; all colors are in your own CSS. So making light/dark switching is very lightweight—prepare two sets of colors, and based on the current hour or user settings, choose one set to stuff into `stylesheets`:

```python
if 19 <= local_hour or local_hour < 7:
    t = {"page": "#000000", "card": "#1c1c1e", "ink": "#f5f5f7", "sep": "#38383a"}   # dark
else:
    t = {"page": "#f5f5f7", "card": "#ffffff", "ink": "#1d1d1f", "sep": "#e5e5ea"}   # light
css = CSS_TEMPLATE.replace("__INK__", t["ink"]).replace("__CARD__", t["card"])  # and so on
```

> Note: CSS built-in `var(--xxx)` variables may not necessarily work in Takumi. For safety, directly replace the color strings into the template in Python to bypass this uncertainty.

---

## Related Links

- PyPI: <https://pypi.org/project/ErisPulse-Takumi/>
- Repository: <https://github.com/ccd2s/ErispulseTakumi> (Author [@ccd2s](https://github.com/ccd2s))
- Underlying Engine: <https://github.com/BalconyJH/takumi-py>