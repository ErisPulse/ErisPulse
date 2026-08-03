# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) is a **third-party image rendering module** maintained by ccd2s, based on [takumi-py](https://github.com/BalconyJH/takumi-py), allowing you to render images in your Bot: HTML, node trees, Jinja templates, SVG, and animations are all supported, and it comes with **built-in Chinese and English fonts** (Noto Sans SC / Roboto / Source Code Pro), eliminating the need for additional font configuration.

> [!IMPORTANT]  
> Takumi is **not** a built-in feature of the ErisPulse framework and must be installed separately:  
>  
> ```bash
> epsdk install Takumi
> ```

It is especially suitable for the following scenarios:

- Rendering data/statistics into beautiful card images for sending
- Converting Markdown / long text into stable-formatted images to avoid platform style differences
- Generating SVG / animations for dynamic visual effects
- Mixed Chinese and English text output (built-in fonts work out of the box)

---

## Installation and Activation

```bash
epsdk install Takumi
```

After installation, the module will load automatically. Just confirm it is enabled in the configuration file:

```toml
[Takumi]
enabled = true
```

---

## Quick Start

After the module loads automatically, you can obtain it through the module manager or use the `sdk` shortcut:

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# Equivalent notation: takumi = sdk.Takumi
```

### Rendering HTML

The most commonly used method — rendering a string of HTML + CSS into a PNG:

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

`png` is of type `bytes`, and can be sent using `event.reply(png, method="Image")` (see [Sending Rendered Results](#sending-rendered-results)).

### Rendering Node Tree

No need to write HTML manually; you can describe the structure with a dictionary, suitable for programmatic assembly:

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "Both Chinese and English can be rendered directly",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=200,
    lang="zh-CN",
)
```

---

## Fonts and Renderers

### Built-in Fonts

Takumi has already bundled commonly used fonts, so no additional installation is required:

| Resource | Description |
|----------|-------------|
| `takumi.fonts` | List of built-in font file names |
| `takumi.families` | List of registered font families |

Convenient methods (`render_html` / `render_node`) automatically inject this font fallback stack; if you call the underlying renderer directly, you must pass `font_families` yourself.

### Native Renderer

`takumi.renderer` is the original `takumi_py.Renderer` instance. The convenient methods have automatically injected the built-in font fallback stack; **when calling the renderer directly, you must pass families yourself**:

```python
png = takumi.renderer.render_html(
    "<div>Hello</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### Independent Renderer

When you need to isolate font / image / resource caching (e.g., long-lived processes, multi-tenant scenarios), you can create a new `Renderer`, and the built-in fonts will be automatically registered:

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>Independent Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=200,
    lang="zh-CN",
)
```

`create_renderer()` accepts the constructor parameters of `takumi_py.Renderer`:

- `load_default_fonts=False` (default): Only load built-in fonts
- `load_default_fonts=True`: Load both Takumi's built-in fonts and default fonts
- `fonts=[...]`: Register custom fonts on top of the default ones

> Independent instances do not go through the module proxy, so to retain a unified built-in font fallback stack, you must explicitly pass `font_families=takumi.families`.

If `font_families` is explicitly passed, the module will respect the caller's settings and no longer inject the default fallback stack. `RenderOptions(font_families=...)` is also valid.

---

## Sending Rendered Results

After rendering an image, you can reply directly via the event:

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>Hello</div>", lang="zh-CN")

# Method 1: Reply directly using the Image method
await event.reply(png, method="Image")

# Method 2: Reply using OneBot12 message segments
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> Different platforms handle image encapsulation uniformly through adapters, so there is no need to worry about underlying differences. See [MessageBuilder Detailed Explanation](../advanced/message-builder.md) and [Send Method Specification](../standards/send-method-spec.md).

---

## Related Links

- PyPI: <https://pypi.org/project/ErisPulse-Takumi/>
- Repository: <https://github.com/ccd2s/ErispulseTakumi> (author [@ccd2s](https://github.com/ccd2s))
- Underlying Engine: <https://github.com/BalconyJH/takumi-py>