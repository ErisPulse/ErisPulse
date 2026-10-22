# ErisPulse-Takumi

> [!TIP]
> **このドキュメントを読むタイミング**：HTML / ノードツリー / Jinjaテンプレートを画像にレンダリングしてチャットプラットフォームに送信したい場合（統計カード、ランキング、長文の画像）に読む。必要なければスキップしてください。

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) は ccd2s が維持する **サードパーティの画像レンダリングモジュール** です。[takumi-py](https://github.com/BalconyJH/takumi-py) に基づいており、Bot が HTML、ノードツリー、Jinja テンプレート、SVG、アニメーションを画像にレンダリングできるようにします。モジュールには **中英文字体**（Noto Sans SC / Roboto / Source Code Pro）が内蔵されており、追加の設定は不要です。

> [!IMPORTANT]
> Takumi **は** ErisPulse フレームワークの組み込み機能ではなく、個別にインストールする必要があります：
>
> ```bash
> epsdk install Takumi
> ```

適用シーン：

- データ/統計をカード画像にレンダリングする
- Markdown / 長文をレイアウトが安定した画像にレンダリングし、プラットフォームのスタイル差異を回避する
- SVG / アニメーションを生成し、動的な視覚効果を実現する
- 中英混排の画像（内蔵フォントで即座に使用可能）

---

## インストールと有効化

```bash
epsdk install Takumi
```

インストール後、モジュールは自動的にロードされ、設定で有効化を確認します：

```toml
[Takumi]
enabled = true
```

---

## 速習

モジュールが自動的にロードされた後、モジュールマネージャーから取得するか、`sdk` ショートカットを使用します：

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# 同義の書き方：takumi = sdk.Takumi
```

### HTML のレンダリング

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
    height=None,   # 内容に応じて自動的に高さを調整
    lang="zh-CN",
)
```

### ノードツリーのレンダリング

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

`png` は `bytes` であり、`event.reply(png, method="Image")` を使用して送信できます（[レンダリング結果の送信](#レンダリング結果の送信)を参照）。

---

## レンダリング API

`sdk.Takumi` は、下層の `takumi_py.Renderer` のすべての機能をプロキシしています：すべてのレンダリング、測定、SVG、アニメーション、テンプレートメソッドは `sdk.Takumi` 上で直接呼び出すことができます。これらのメソッドに対して、モジュールは**自動的に内蔵フォントのフォールバックスタック**（`takumi.families`）を注入します。手動で `font_families` を渡す場合は、呼び出し側の設定を尊重します。

### メソッド概要

| カテゴリ | メソッド | 戻り値 | 説明 |
|------|------|------|------|
| 静的レンダリング | `render_html(html, ...)` | `bytes` | HTML文字列をレンダリングする |
| | `render_node(node, ...)` | `bytes` | ノードツリー（dict）をレンダリングする |
| | `render_template(name, ctx, ...)` | `bytes` | Jinjaテンプレートをレンダリングする |
| | `render_compiled(node, ...)` | `bytes` | 事前コンパイルされたノードをレンダリングする |
| SVG 出力 | `render_svg_html(html, ...)` | `str` | SVGを出力する（HTML入力） |
| | `render_svg_node(node, ...)` | `str` | SVGを出力する（ノードツリー入力） |
| | `render_svg_template(name, ctx, ...)` | `str` | SVGを出力する（テンプレート入力） |
| | `render_svg_compiled(node, ...)` | `str` | SVGを出力する（事前コンパイル入力） |
| アニメーション | `render_animation(scenes, ...)` | `bytes` | 複数フレームのアニメーションをエンコードする |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | シーケンスの特定の時間フレームを取得する |
| 測定 | `measure_node(node, ...)` | `dict` | ノードツリーのレイアウトを測定する |
| | `measure_html(html, ...)` | `dict` | HTMLのレイアウトを測定する |
| | `measure_compiled(node, ...)` | `dict` | 事前コンパイルされたノードを測定する |
| コンパイル | `compile_node(node)` | `CompiledNode` | ノードツリーをコンパイルする |
| | `compile_html(html, ...)` | `CompiledNode` | HTMLをコンパイルする |
| フォント | `register_font(font)` | `list[str]` | 自定義フォントを登録し、familyリストを返す |
| | `register_fonts(fonts)` | `list[str]` | フォントを一括登録する |

> `CompiledNode` は `resource_urls()` メソッドを公開しており、HTTP(S) イメージ参照を事前に発見できるため、リソースの事前準備が可能です。

### 一般的なパラメータ

以下のパラメータは、静的レンダリングと SVG メソッドに適用されます（アニメーションメソッドには `fps` などがあります。対応する例を参照してください）：

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `stylesheets` | `list[str]` | `None` | ドキュメントレベルの CSS 文字列リスト；内側の `style` は HTML と一緒に解析されます |
| `width` | `int \| None` | `1200` | ビューポートの幅（ピクセル）；`None` はレイアウトに応じて推測されます |
| `height` | `int \| None` | `630` | ブレンドの高さ（ピクセル）；`None` は内容に応じて自動的に高さを調整します（[ビューポートと出力形式](#ビューポートと出力形式)を参照） |
| `lang` | `str \| None` | `None` | BCP-47 言語タグ（例：`zh-CN`）、テキスト整形と改行に影響します |
| `font_families` | `list[str]` | 自動注入 | フォントフォールバックスタック；便利なメソッドは自動的に内蔵フォントを注入します |
| `format` | `str` | `"png"` | 出力形式（[ビューポートと出力形式](#ビューポートと出力形式)を参照） |
| `device_pixel_ratio` | `float` | `1.0` | デバイスピクセル比、出力解像度を制御します |
| `time_ms` | `int` | `0` | アニメーションのサンプリング時刻（ミリ秒） |
| `dithering` | `str` | `"none"` | ドッジングアルゴリズム：`none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | 有損エンコードの品質 |
| `lossless` | `bool \| None` | `None` | 無損圧縮かどうか |
| `images` | `list` | `None` | 今回のレンダリングの画像リソース（`ImageResource` または `(src, bytes)` タプル） |
| `keyframes` | `Mapping` | `None` | 構造化されたキーフレーム、`@keyframes` を書く必要はありません |
| `options` | `RenderOptions` | — | `RenderOptions(...)` でパラメータを一括で渡す、上表のフィールドと同じ |

完全なフィールド定義は `takumi_py.RenderOptions` を参照してください。

### ノードツリーの例

```python
png = takumi.render_node(
    {
        "type": "container",
        "style": {"padding": "32px", "backgroundColor": "#111827"},
        "children": [
            {"type": "text", "text": "タイトル", "style": {"fontSize": 32, "color": "white"}},
            {"type": "text", "text": "本文", "style": {"fontSize": 18, "color": "#9ca3af"}},
        ],
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

### Jinja テンプレートの例

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

> `filters={...}` を使用してカスタム Jinja フィルターを注入するか、`environment=...` を使用して完全な `jinja2.Environment` を渡すことができます。テンプレートディレクトリと環境設定は [takumi-py テンプレートドキュメント](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md) を参照してください。

### SVG 出力の例

```python
svg = takumi.render_svg_html(
    '<div class="card">Hello</div>',
    stylesheets=[".card { width: 800px; color: black; }"],
    width=800,
    height=None,
)
```

### アニメーションの例

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

> 各フレームは `AnimationScene(node, duration_ms=...)` で構成され、`duration_ms` は正数でなければなりません。

---

## ビューポートと出力形式

### 出力形式

| シナリオ | `format` の値 |
|------|---------------|
| 静的画像 | `png`（デフォルト）/ `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| アニメーション | `webp`（デフォルト）/ `apng` / `gif` |

`format="raw"` は行主序の RGBA バイナリを返し、カスタムピクセル処理に使用します。

### `width` と `height` について

`width` と `height` の役割は非対称です：

- `width` は**ビューポートの幅**で、テキストとレイアウトはそれに応じて改行、リフローようにします。**固定値**（例：`800`）でなければなりません。そうでなければ、画布は内容の自然な幅に伸縮し、テキストは改行せず、サイズは制御できません。
- `height` は**画布の高さ**で、内容に応じて増加します。`height` のデフォルト値は `630` です。`height=None` を渡すと、Takumi は**内容に応じて自動的に画布の高さを調整**します（auto viewport）。

> [!TIP]
> **推奨の組み合わせ：固定 `width` + `height=None`。** 固定サイズの画布や切り抜き効果が必要な場合にのみ、具体的な `height` を渡してください。

> [!NOTE]
> `width` / `height` のいずれかは技術的に `None` を渡して、レイアウトに応じて推測させることもできます（ノード自身がサイズを宣言している場合）。両方を渡した場合、出力サイズは確定値になります。

---

## フォント

### 内蔵フォント

| フォント | family | カテゴリ |
|------|--------|------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif（italic） |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace（italic） |

モジュール属性：

| 属性 | 説明 |
|------|------|
| `takumi.fonts` | 内蔵フォントファイル名リスト |
| `takumi.families` | 登録されたフォント familyリスト |

### 自動注入

`sdk.Takumi` 上のすべてのレンダリング、測定、SVG、アニメーション、テンプレートメソッドは、自動的に `takumi.families` をフォントフォールバックスタックとして注入します。`takumi.renderer`（原生インスタンス）または `create_renderer()` で作成された独立したインスタンスを直接呼び出す場合は、`font_families=takumi.families` を手動で渡す必要があります。

### 自定義フォント

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

`register_font` は登録された family 名のリストを返し、後続のレンダリング時に `font_families` として渡すことができます。

---

## レンダラーインスタンス

### 原生 Renderer

`takumi.renderer` は元の `takumi_py.Renderer` インスタンスです。直接呼び出す場合は、`font_families` を手動で渡す必要があります：

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 独立 Renderer

フォント / 画像 / リソースキャッシュを分離する必要がある場合（長寿命プロセス、マルチテナント環境）、独立した `Renderer` を作成できます。内蔵のフォントは自動的に登録されます：

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

`create_renderer()` は `takumi_py.Renderer` の構造子パラメータを受け取ります：

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `load_default_fonts` | `bool` | `False` | takumi-py に含まれるフォントをロードするかどうか（内蔵フォントは常にロードされます） |
| `fonts` | `list[FontResource]` | `None` | 追加で登録する自定義フォント |
| `cache_max_bytes` | `int \| None` | `None` | リソースキャッシュの上限（バイト）；`0` は無効化 |
| `persistent_images` | `list` | `None` | 永続化する画像リソース |

> 独立したインスタンスはモジュールのプロキシを経由しないため、統一された内蔵フォントフォールバックスタックを保持するには、`font_families=takumi.families` を明示的に渡す必要があります。`font_families` を明示的に渡した場合、モジュールは呼び出し側の設定を尊重し、デフォルトのフォールバックスタックを注入しません。`RenderOptions(font_families=...)` でも同様です。

---

## レンダリング結果の送信

レンダリングされた画像は `bytes` であり、イベントの返信として直接送信できます：

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# 方法1：Imageメソッドで返信する
await event.reply(png, method="Image")

# 方法2：OneBot12メッセージセグメントで返信する
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> 画像の異なるプラットフォームでのラッピングは、アダプタによって統一的に処理されます。詳しくは [MessageBuilder 詳解](../advanced/message-builder.md) と [送信メソッド仕様](../standards/send-method-spec.md) を参照してください。

---

## 設定

```toml
[Takumi]
enabled = true
```

---

## 関連リンク

- PyPI：<https://pypi.org/project/ErisPulse-Takumi/>
- リポジトリ：<https://github.com/ccd2s/ErisPulse-Takumi>（作者 [@ccd2s](https://github.com/ccd2s)）
- 下層エンジン：<https://github.com/BalconyJH/takumi-py>
- takumi-py ドキュメント：<https://github.com/BalconyJH/takumi-py/blob/main/docs/index.md>

---

## 次に進む

- **レンダリング結果を送信する方法**：`event.reply(png, method="Image")` などの返信方法は [イベントシステム API - 返信メソッド](../api-reference/event-system.md) を参照
- **より複雑な出力メッセージの構築**（画像 + 文字 + @）：[メッセージビルダー](../advanced/message-builder.md)
- **レンダリング + 定期送信**：[ErisPulse-Cron](cron.md) と組み合わせて周期的なデータカードを作成