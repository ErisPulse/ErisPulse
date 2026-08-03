# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) は ccd2s が維持する **サードパーティの画像レンダリングモジュール** で、[takumi-py](https://github.com/BalconyJH/takumi-py) をベースとしています。Bot で画像をレンダリングできます：HTML、ノードツリー、Jinja テンプレート、SVG、アニメーションなども問題なく対応し、**中英両方のフォントが内蔵**されています（Noto Sans SC / Roboto / Source Code Pro）。フォントの追加設定は不要です。

> [!IMPORTANT]  
> Takumi は ErisPulse フレームワークの内蔵機能ではなく、個別にインストールする必要があります：
>
> ```bash
> epsdk install Takumi
> ```

以下の用途に非常に適しています：

- データや統計情報を美しいカード画像として送信する
- Markdown / 長文をレイアウトが安定した画像にレンダリングし、プラットフォームのスタイル差異を回避する
- SVG / アニメーションを生成し、動的な視覚効果を実現する
- 中英混在のテキストを画像として出力する（内蔵フォントで即座に使用可能）

---

## インストールと有効化

```bash
epsdk install Takumi
```

インストール後、モジュールは自動的にロードされ、設定ファイルで有効化を確認してください：

```toml
[Takumi]
enabled = true
```

---

## すぐに始める

モジュールが自動ロードされた後、モジュールマネージャーから取得するか、`sdk` というショートカットを使用できます：

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# 同義の書き方: takumi = sdk.Takumi
```

### HTML のレンダリング

最も一般的な方法 —— HTML + CSS の文字列を PNG にレンダリングします：

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>こんにちは、ErisPulse</h1>
      <p>Takumi でレンダリングされた</p>
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

`png` は `bytes` であり、`event.reply(png, method="Image")` を使用して送信できます（詳細は [レンダリング結果の送信](#レンダリング結果の送信) を参照）。

### ノードツリーのレンダリング

手動で HTML を書く必要がなく、辞書で構造を記述できます。プログラムで構築する場合に適しています：

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "中英両方のテキストを直接レンダリング可能",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=200,
    lang="zh-CN",
)
```

---

## フォントとレンダラー

### 内蔵フォント

Takumi には一般的なフォントがパッケージ化されており、追加インストールは不要です：

| 資源 | 説明 |
|------|------|
| `takumi.fonts` | 内蔵フォントのファイル名リスト |
| `takumi.families` | 登録済みのフォントファミリリスト |

便利なメソッド（`render_html` / `render_node`）は自動的にこのフォントフォールバックスタックを注入します。直接低レベルのレンダラーを呼び出す場合は、`font_families` を手動で渡す必要があります。

### ネイティブレンダラー

`takumi.renderer` は元の `takumi_py.Renderer` インスタンスです。便利なメソッドは自動的に内蔵フォントフォールバックスタックを注入しますが、**レンダラーを直接呼び出す場合は `families` を手動で渡す必要があります**：

```python
png = takumi.renderer.render_html(
    "<div>こんにちは</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 独立レンダラー

フォント / 画像 / リソースのキャッシュを分離する必要がある場合（例：長寿命プロセス、マルチテナント環境）は、新しい `Renderer` を作成できます。内蔵フォントは自動的に登録されます：

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>独立したレンダラー</div>",
    font_families=takumi.families,
    width=800,
    height=200,
    lang="zh-CN",
)
```

`create_renderer()` は `takumi_py.Renderer` のコンストラクタパラメータを受け取ります：

- `load_default_fonts=False`（デフォルト）：内蔵フォントのみをロード
- `load_default_fonts=True`：Takumi が提供するフォントも同時にロード
- `fonts=[...]`：デフォルトに加えて独自のフォントを登録

> 独立インスタンスはモジュールプロキシを経由しないため、統一された内蔵フォントフォールバックスタックを保持するには、明示的に `font_families=takumi.families` を渡す必要があります。

`font_families` を明示的に渡した場合、モジュールは呼び出し元の設定を尊重し、デフォルトのフォールバックスタックを注入しません。`RenderOptions(font_families=...)` も同様に有効です。

---

## レンダリング結果の送信

画像をレンダリングした後、イベントの返信を使って直接送信できます：

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# 方法1: Image メソッドで直接返信
await event.reply(png, method="Image")

# 方法2: OneBot12 メッセージセグメントで返信
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> 画像のラッピングはアダプターによって統一的に処理されるため、下層の差異を気にする必要はありません。詳細は [MessageBuilder 詳解](../advanced/message-builder.md) と [送信メソッド仕様](../standards/send-method-spec.md) を参照してください。

---

## 関連リンク

- PyPI: <https://pypi.org/project/ErisPulse-Takumi/>
- リポジトリ: <https://github.com/ccd2s/ErispulseTakumi>（作者 [@ccd2s](https://github.com/ccd2s)）
- ベースエンジン: <https://github.com/BalconyJH/takumi-py>