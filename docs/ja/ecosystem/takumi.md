# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) はccd2sによって維持されている **サードパーティ画像レンダリングモジュール** です。[takumi-py](https://github.com/BalconyJH/takumi-py) を基盤としており、Botで画像をレンダリングできます：HTML、ノードツリー、Jinjaテンプレート、SVG、アニメーションなどはお手のものです。また、**組み込みの中国語・英語フォント**（Noto Sans SC / Roboto / Source Code Pro）を搭載しており、追加のフォント設定は不要です。

> [!IMPORTANT]
> Takumi は ErisPulse フレームワークの組み込み機能では**ありません**。個別にインストールする必要があります：
>
> ```bash
> epsdk install Takumi
> ```

以下のシーンに最適です：

- データ/統計を精美なカード画像として送信する
- Markdown / 長文をレイアウトの安定した画像としてレンダリングし、プラットフォームのスタイルの違いを回避する
- SVG / アニメーションを生成し、ダイナミックな視覚効果に使用する
- 中国語・英語の混在した画像・テキスト出力（組み込みフォントで開始できる）

---

翻訳後のMarkdownコンテンツを直接返してください。その他のテキストを含めないでください。

## インストールと有効化

```bash
epsdk install Takumi
```

インストール後、モジュールは自動的に読み込まれます。設定ファイルで有効化を確認してください。

```toml
[Takumi]
enabled = true
```

---

## クイックスタート

モジュールが自動的に読み込まれた後、モジュールマネージャーを経由して取得することもできますし、`sdk` のショートカットを使用することも可能です。

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# 等価な書き方：takumi = sdk.Takumi
```

### HTML をレンダリングする

最も一般的な方法 – HTML + CSS の文字列を PNG に変換する：

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>こんにちは、ErisPulse</h1>
      <p>Takumi がレンダリングしました</p>
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

`png` は `bytes` であり、`event.reply(png, method="Image")` を通じて送信できます（詳細は [送信レンダリング結果](#送信レンダリング結果) を参照してください）。

### ノードツリーをレンダリングする

HTML を手動で記述する必要はありません。辞書で構造を記述するだけでよく、プログラムによる組み立てに適しています。

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "中国語と English を直接レンダリングできます",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=200,
    lang="zh-CN",
)

## フォントとレンダラー

### 内蔵フォント

Takumi には一般的なフォントが同梱されているため、追加のインストールは不要です：

| リソース | 説明 |
|------|------|
| `takumi.fonts` | 内蔵フォントファイル名のリスト |
| `takumi.families` | 登録済みのフォントファミリーリスト |

便利なメソッド（`render_html` / `render_node`）は、自動的にこのフォントフォールバックスタックを注入します。底層のレンダラーを直接呼び出す場合は、`font_families` を独自に渡す必要があります。

### ネイティブ Renderer

`takumi.renderer` は元の `takumi_py.Renderer` インスタンスです。便利なメソッドは自動的に内蔵フォントのフォールバックスタックを注入していますが、**レンダラーを直接呼び出す場合は、`families` を独自に渡す必要があります**：

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 独立 Renderer

フォント / 画像 / リソースキャッシュを隔離する必要がある場合（長いライフサイクルのプロセスやマルチテナントシナリオなど）は、新しい `Renderer` を作成することができます。内蔵フォントは自動的に登録されます：

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

`create_renderer()` は `takumi_py.Renderer` のコンストラクタ引数を受け付けます。

- `load_default_fonts=False`（デフォルト）：内蔵フォントのみをロードします
- `load_default_fonts=True`：Takumi 標準のフォントも併せてロードします
- `fonts=[...]`：デフォルト設定の上にカスタムフォントを登録します

> 独立インスタンスはモジュールプロキシを経由しないため、統一された内蔵フォントのフォールバックスタックを維持するには、明示的に `font_families=takumi.families` を渡す必要があります。

明示的に `font_families` を渡した場合、モジュールは呼び出し元の設定を尊重し、デフォルトのフォールバックスタックの注入は行わなくなります。`RenderOptions(font_families=...)` も同様に有効です。

---

## レンダリング結果の送信

レンダリングして画像を取得した後、イベントで直接送信できます。

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="ja")

# 方法1: Imageメソッドで直接返信
await event.reply(png, method="Image")

# 方法2: OneBot12のメッセージセグメントを通じて返信
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> プラットフォームごとの画像のラッパー処理はアダプターで統一して処理されるため、低レイヤーの違いを気にする必要はありません。詳細は [MessageBuilder の解説](../advanced/message-builder.md) と [送信メソッドの仕様](../standards/send-method-spec.md) を参照してください。

---

---

## 実践での罠（血と涙の教訓）

以下のドキュメントには書かれていないものです。Takumi を使ってデータ可視化モジュール（ソナグラムやレーダーチャートのようなもの、数十のノードがあり、リンクとラベルを描画する必要がある）を構築する際、一行ずつ試行錯誤して得られたものです。重要なポイントをまとめました。あなたの時間を節約し、数時間の無駄道を避けることができます。

### 1. SVG `<text>` は使わないでください。レンダリングされません。

最大の罠、唯一無二のものです。`<svg>` 内でノードを描画し、隣に `<text>` で名前を付ける——**レンダリングされると文字は空になります**。`<text>` に `font-family` を指定しても、`<svg>` のルートで継承を設定しても無駄です。中国語や英語の文字は表示されず、図には中身のない形状だけが残ります。

実験結果の結論：`takumi-py` はインライン SVG のテキスト要素を描画しません。したがって、正しいアプローチは以下の通りです。

- SVG は**形状のみ**（円、線、多角形）を描画
- 文字はすべて **HTML** で処理します：`<svg>` を `position: relative` のコンテナに入れ、絶対配置の `<div>` を使って対応する座標にラベルを被せます

```python
W = H = 600
html = f"""
<div style='position:relative;width:{W}px;height:{H}px'>
  <svg width='{W}' height='{H}' viewBox='0 0 {W} {H}'>
    <!-- 形状のみを描画 -->
  </svg>
  <div style='position:absolute;left:{x}px;top:{y}px;transform:translate(-50%,-50%)'>名前</div>
</div>
"""
```

座標が一致する前提：SVG は**固定**の `width`/`height` を使用します（面倒を避けて `width:100%` と書かないでください）。そうすることでピクセルとコンテナが 1:1 になり、`div` の `left`/`top` に SVG 内の座標を直接入力するだけで済みます。

### 2. CSS は必ず `stylesheets` 経由で、まるごとの HTML ドキュメントを渡さないでください

`render_html(html, ...)` の最初の引数は**本文 HTML** であって、完全なドキュメントではありません。面倒くさがって以下のように渡すと：

```python
takumi.render_html("<!DOCTYPE html><html><head><style>...</style></head><body>...</body></html>")
```

スタイルは**静かに無効になります**——図は出ますが、CSS がないのと同じように、見た目が乱雑になります。デバッグするとき、CSS を間違って書いたと思い込むかもしれませんが、実際は渡し方が間違っています。痛い思いをします。

正しいアプローチは常に：本文を一つの引数、CSS を一つの引数として渡します。

```python
takumi.render_html(body_html, stylesheets=[css_str], width=..., height=..., lang="zh-CN")
```

### 3. `height` は切り取られる高さで、自動的には伸びません

`width` はビューポートの幅、`height` はキャンバスの高さ——**`height` を超える内容は直接切り取られます**、ブラウザのように自動的に下に広がりません。したがって、総高さは自分で見積もる必要があります：各ブロックの高さ + パディング + カードの間隔を足して渡します。

経験則として**多く見積もる**のが正解です。下部に数十ピクセル余白があれば誰も気にしませんが、上部の内容が切り取られるとその図は役に立ちません。動的な内容（リスト項目数が不固定）がある場合は、項目数ごとに現在計算します：

```python
height = padding * 2 + header_h + sum(各項目の高さ) + 間隔 * (項目数 - 1) + 30  # 最後に少し余裕を持たせる
```

### 4. フォントの自動注入は HTML テキストに対してのみ有効です

便利なメソッド（`render_html` / `render_node`）は、組み込みフォントのフォールバックスタックを自動的に挿入しますが、**HTML テキストに対してのみ有効です**。したがって、第 1 条で「文字は HTML で処理する」と述べた理由は、中国語フォントを無料で利用できるというメリットにもなります——自分で `font_families` に気を配る必要がなくなります。

直接下位レイヤーのレンダラー（`takumi.renderer.render_html`）を呼び出す場合は、自分で `font_families=takumi.families` を渡すのを忘れないでください。

### 5. 目を閉じてもデバッグできる小技

スタイルを変更した後、「ある部分の中国語が本当にレンダリングされたか」を確認したいのに、毎回画像を開くのが面倒な場合、生のピクセルを吐き出させて数えさせます：

```python
data = takumi.render_html(body, stylesheets=[css], width=W, height=H,
                          lang="zh-CN", format="raw")  # raw は RGBA バイトストリーム
dark = sum(1 for i in range(0, len(data), 4)
           if data[i] < 120 and data[i+1] < 120 and data[i+2] < 120 and data[i+3] > 128)
```

明るい背景では、「文字あり」と「文字なし」のインクドット数は 4000+ と 0 の違い——一行の `<div>` が本当に有効かどうかは一目でわかります。肉眼で PNG を監視するよりもずっと高速です。第 1 条の SVG の罠も、これで検証しました。

### 6. ダークモード / ライトモード：スタイルシートを切り替えるだけ

Takumi 自体はテーマを気にしません。色はすべて独自の CSS にあります。したがって、明暗の切り替えは特に軽量です——2 つの配色を用意し、現在の時間やユーザー設定に基づいて 1 つを選択して `stylesheets` に入れます：

```python
if 19 <= local_hour or local_hour < 7:
    t = {"page": "#000000", "card": "#1c1c1e", "ink": "#f5f5f7", "sep": "#38383a"}   # ダーク
else:
    t = {"page": "#f5f5f7", "card": "#ffffff", "ink": "#1d1d1f", "sep": "#e5e5ea"}   # ライト
css = CSS_TEMPLATE.replace("__INK__", t["ink"]).replace("__CARD__", t["card"])  # 同様に置換
```

> 小さなヒント：CSS に含まれる `var(--xxx)` 変数は takumi では**必ずしも有効ではありません**。確実にするために、Python で直接色の文字列をテンプレートに置換して、この不安定さを回避してください。

---

このまま翻訳された完全なMarkdownコンテンツを返してください。他の文字を含めないでください。

## 関連リンク

- PyPI: <https://pypi.org/project/ErisPulse-Takumi/>
- リポジトリ: <https://github.com/ccd2s/ErispulseTakumi>（作者 [@ccd2s](https://github.com/ccd2s)）
- 基底エンジン: <https://github.com/BalconyJH/takumi-py>