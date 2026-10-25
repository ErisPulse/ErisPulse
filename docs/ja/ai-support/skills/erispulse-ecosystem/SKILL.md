---
name: erispulse-ecosystem
description: "适用于：了解生态组件（Dashboard/Cron/AI 模块等）与各平台适配器的接入差异。覆盖场景：ErisPulse フレームワーク自体はコア機能（イベントシステム、モジュールシステム、設定、ルーティング、ログなど）のみを提供し、GUI、画像レンダリング、可視化などの「ヘビー級」機能は**組み込まれていません**。これらの機能は、コミュニティがメンテナンスする**サードパーティモジュール**によって提供されており、必要に応じてインストールするだけで利用できます。**このドキュメントを読むべきとき**：Web画面でボットを視覚的に管理したい場合（モジュールの有効化・無効化、設定編集、ログ閲覧、イベントストリームの監視など）、または自分のモジュール用のDashboard管理ページを登録したい場合にお読みください。必要ない場合はスキップして構いません。**このドキュメントを読む必要があるタイミング**:。**このドキュメントを読む必要があるのは**、ロボットに AI インテリジェントエージェントの機能（ツールループ、ストリーミング対話、MCP、長期記憶）を追加したい場合、または独自のモジュールサービスをインテリジェントエージェントから呼び出せるようにしたい場合です。必要ない場合はこのドキュメントは飛ばしてください。このセクションは、各アダプタの開発者が維持・更新するものであり、OneBot12標準との差異や拡張機能を説明するためのものです。以下の各プラットフォームの詳細ドキュメントを参照してください：。"
---

# ErisPulse 生态与多平台

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 生态总览: 52-71 行
- おすすめモジュール: 73-113 行
- 公式クライアント（スタンドアロンプログラム）: 115-125 行
- 自分のモジュールもここに載せたいですか？: 127-135 行
- Dashboard: 137-164 行
- 動作原理: 166-177 行
- 登録API: 179-217 行
- 2つのインジェクションモード: 219-252 行
- サイドバーグループ: 254-280 行
- よく使うCSSクラス名: 282-317 行
- 認証とAPI呼び出し: 319-341 行
- 完全なモジュール例: 343-453 行
- ビューの登録解除: 455-467 行
- 注意事項: 469-479 行
- 次のステップ: 481-485 行
- 定时任务: 487-507 行
- 機能速覧: 509-516 行
- 速習: 518-536 行
- API 概要: 538-591 行
- モジュールのアンロード時の動作: 593-598 行
- 関連リンク: 600-605 行
- 次のステップ: 607-611 行
- AI 对话模块: 613-631 行
- 核心能力: 633-652 行
- モジュール拡張: 654-724 行
- イベントのサブスクライブ: 726-738 行
- サービスとして呼び出される: 740-746 行
- インターフェース: 748-756 行
- 次に進む: 758-763 行
- 平台指南索引: 765-781 行
- プラットフォーム固有の機能: 783-806 行
- 一般的なインターフェース: 808-990 行
- 標準フォーマット: 992-1048 行
- 参考リンク: 1050-1060 行
- 貢献の参加: 1062-1071 行

## 生态总览

> 来源: `docs/ja/ecosystem/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/ecosystem/README.md）

# エコシステムモジュール

ErisPulse フレームワーク自体はコア機能（イベントシステム、モジュールシステム、設定、ルーティング、ログなど）のみを提供し、GUI、画像レンダリング、可視化などの「ヘビー級」機能は**組み込まれていません**。これらの機能は、コミュニティがメンテナンスする**サードパーティモジュール**によって提供されており、必要に応じてインストールするだけで利用できます。

> [!IMPORTANT]
> このディレクトリ内のドキュメントは2種類に分かれており、インストール方法が異なります：
>
> - **モジュール**（Dashboard / Takumi など）は `epsdk install` でインストールします：
>
>   ```bash
>   epsdk install <モジュール名>
>   ```
>
> - **スタンドアロンプログラム**（ErisPulse-App クライアントなど）は、対応する GitHub Releases から直接ダウンロードしてインストールし、`epsdk` は不要です。

---

## おすすめモジュール

### ErisPulse-Dashboard：ブラウザ上の管理パネル

ボットをサーバー上で運用していると、モジュールの起動・停止、設定変更、ログ確認のたびにターミナルへログインする必要がありますか？Dashboard はこれらをブラウザに移動します：モジュールの起動・停止、設定編集、ログ表示、イベント監視が可能で、他のモジュールもサイドバーにカスタムウィンドウを登録できるため、管理ページが一箇所にまとまります。

```bash
epsdk install Dashboard
```

ドキュメント：[Dashboard の使い方とウィンドウ登録](dashboard.md) ｜ プロジェクトホームページ：[PyPI](https://pypi.org/project/ErisPulse-Dashboard/)

### ErisPulse-Cron：定期タスク

毎日決まった時刻にチェックインリマインダーを送信したり、Cron 式で周期タスクを実行したり、数分おきにデータをポーリングしたりしたい場合は？Cron は一回限り / 間隔 / Cron 式の 3 種類のタスクタイプを提供し、コールバックへの引数渡しや SQLite による永続化（再起動してもタスクは失われません）に対応しています。

```bash
epsdk install Cron
```

ドキュメント：[Cron 定期タスク](cron.md) ｜ プロジェクトホームページ：[GitHub](https://github.com/wsu2059q/ErisPulse-Cron)

### ErisPulse-QvQChat：汎用エージェント

キーワード返信しかできないのではなく、実際に仕事のできる AI アシスタントをグループに置きたいと思いませんか？QvQChat は汎用エージェントです：ツールループはメッセージの送受信 / コード実行 / PC 操作 / 画像生成 / 音声 / MCP / サブエージェントをカバーし、ストリーミング対話と逐次ツールリプレイに対応、Dashboard ウィンドウを内蔵しています。

```bash
epsdk install ErisPulse-QvQChat
```

ドキュメント：[QvQChat エージェント](qvqchat.md) ｜ プロジェクトホームページ：[GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-Takumi：画像レンダリング

ランキング、バトルレポート、スケジュールカードなど「画像を送る」必要がある場面では、テンプレートを書いて画像にレンダリングし、グループに送るだけです：HTML / ノードツリー / Jinja / SVG / アニメーション（[takumi-py](https://github.com/BalconyJH/takumi-py) ベース）をサポートし、中国語・英語フォントを内蔵しているため、すぐに使い始められます。

```bash
epsdk install Takumi
```

ドキュメント：[Takumi 画像レンダリング](takumi.md) ｜ プロジェクトホームページ：[GitHub](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)）

## 公式クライアント（スタンドアロンプログラム）

### ErisPulse-App：スマートフォンで直接ボットを実行

常時起動のサーバーがなくても、いつでもインスタンスの作成、モジュールのインストール、イベントストリームの閲覧がしたいと思いませんか？ErisPulse-App は公式の全プラットフォーム対応クライアント（Android / Windows / Linux / macOS）です。ネイティブインターフェースで複数のボットインスタンスを作成 / 実行 / 管理でき、モジュールストアとイベントビルダーを内蔵し、**スマートフォンで直接実行**可能で、デスクトップトレイに常駐します。

すべてのプラットフォームのインストールパッケージは [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) からダウンロードでき、`epsdk` は不要です。

ドキュメント：[ErisPulse-App のインストールと使い方](app.md)

---

## 自分のモジュールもここに載せたいですか？

高品質で広く再利用可能な ErisPulse エコシステムモジュールのご推薦を歓迎します。要件は以下の通りです：

1. [PyPI](https://pypi.org/) で公開されており、パッケージ名が `ErisPulse-` で始まること
2. 基本的な README と使用例が提供されていること
3. 積極的にメンテナンスされており、Issue に対応していること

上記の条件を満たすモジュールの作者は、PR を通じてこのディレクトリに `<モジュール名>.md` ドキュメントを追加し、上記のおすすめリストに対応するセクションを補足することができます。

## Dashboard

> 来源: `docs/ja/ecosystem/dashboard.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/ecosystem/dashboard.md）

# ErisPulse-Dashboard

> [!TIP]
> **このドキュメントを読むべきとき**：Web画面でボットを視覚的に管理したい場合（モジュールの有効化・無効化、設定編集、ログ閲覧、イベントストリームの監視など）、または自分のモジュール用のDashboard管理ページを登録したい場合にお読みください。必要ない場合はスキップして構いません。

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) はErisDevが直接メンテナンスする**Web管理パネルモジュール**で、ErisPulseに視覚的なランタイム管理インターフェースを提供します：モジュールの有効化・無効化、設定編集、ログ閲覧、イベントストリーム監視など。

> [!IMPORTANT]
> DashboardはErisPulseフレームワークの**内蔵機能ではありません**。別途インストールが必要です：
>
> ```bash
> epsdk install Dashboard
> ```

Dashboardは、他のErisPulseモジュールがカスタム管理ページをサイドバーに登録することもサポートしています。登録後、ユーザーはDashboard内で直接そのモジュール専用のビューページに切り替えることができ、独立したフロントエンドを別途開発する必要はありません。

> [!NOTE]
> ビュー登録は**オプション機能**です。
>
> - Dashboardモジュールが**未インストール**または**未ロード**の場合、`sdk.Dashboard.register_view()` を呼び出すと例外がスローされます
> - モジュール自体の他の機能に影響が及ばないよう、登録コードは必ず `try/except` で囲んでください
> - 登録前にDashboardが利用可能かどうかを確認することをお勧めします：`hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## 動作原理

```
モジュールの on_load()
  → sdk.Dashboard.register_view(...) を呼び出し
  → Dashboardバックエンドがビュー情報を保存
  → WebSocketでフロントエンドに通知
  → フロントエンドがサイドバーナビ項目 + ページコンテナを動的に作成
  → ユーザーがクリックしてモジュールのビューを表示
```

---

## 登録API

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # 必須、一意の識別子
    title="マイモジュール",             # 中国語名
    title_en="My Module",             # 英語名
    icon_svg='<svg>...</svg>',        # サイドバーアイコンSVG
    html_content='<div>...</div>',     # ページのHTMLコンテンツ
    js_content='function xxx() {}',    # ページのJavaScriptロジック
    css_content='.my-style {}',        # 任意のカスタムCSS
    iframe_url='',                     # iframeモードのURL（html_contentとどちらか一方を指定）
    loader="loadMyModuleView",         # このページに切り替えた際に呼び出されるJS関数名
    group="group_extensions",          # サイドバーグループ
    group_title="",                    # カスタムグループの中国語名
    group_title_en="",                 # カスタムグループの英語名
)
```

### パラメータ説明

| パラメータ | 型 | 必須 | 説明 |
|------|------|------|------|
| `id` | `str` | はい | ビューの一意識別子、モジュール名の使用を推奨 |
| `title` | `str` | いいえ | 中国語表示名、デフォルトは `id` を使用 |
| `title_en` | `str` | いいえ | 英語表示名、デフォルトは `title` を使用 |
| `icon_svg` | `str` | いいえ | サイドバーアイコンの完全なSVG文字列 |
| `html_content` | `str` | いいえ* | インジェクションモードのページHTMLコンテンツ |
| `js_content` | `str` | いいえ | ページのJavaScriptコード |
| `css_content` | `str` | いいえ | ページのカスタムCSSスタイル |
| `iframe_url` | `str` | いいえ* | iframeモードのURL、設定すると `html_content` は無視されます |
| `loader` | `str` | いいえ | ページアクティブ時に自動的に呼び出されるJS関数名 |
| `group` | `str` | いいえ | サイドバーグループ識別子、デフォルトは `group_extensions` |
| `group_title` | `str` | いいえ | カスタムグループの中国語タイトル |
| `group_title_en` | `str` | いいえ | カスタムグループの英語タイトル |

> *`html_content` と `iframe_url` のうち少なくとも一方を指定する必要があります。そうでない場合、ページは空白になります。

---

## 2つのインジェクションモード

### モード1：HTML/JSインジェクション（推奨）

HTML、JS、CSSの文字列を直接提供すると、Dashboardがその内容をページに注入します。このモードはDashboardのスタイルと完全に一致しており、Dashboardが提供するCSSクラス名の使用を推奨します。

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="ハローページ", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">これはサンプルページです</div></div>',
    group="group_tools",
)
```

> APIルートやJSインタラクションなどを含む完全な天気モジュールの例は、下記の[完全なモジュール例](#完全なモジュール例)を参照してください。

### モード2：iframe埋め込み

モジュールが独自のHTMLページURLを提供し（ルートの登録は自身で行う必要があります）、Dashboardがiframeとして埋め込みます。完全に独立したUIや複雑なインタラクションが必要なシナリオに適しています。

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="データ可視化", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> iframeモードでは、認証用の `token` パラメータがURLに自動的に追加されます。

---

## サイドバーグループ

モジュールはビューが属するサイドバーグループを指定できます。Dashboardには以下の組み込みグループがあります：

| グループ識別子 | 中国語名 | 位置 |
|---------|--------|------|
| `group_overview` | 概要 | 第1グループ |
| `group_events` | イベント | 第2グループ |
| `group_extensions` | 拡張 | 第3グループ（デフォルト） |
| `group_system` | システム | 第4グループ |
| `group_tools` | ツール | 第5グループ |

組み込みグループ名を指定すると、モジュールのビューはそのグループの末尾に追加されます：

```python
group="group_tools"  # "ツール"グループに追加
```

カスタムグループ名（`group_` で始まらない名前）を使用することもでき、Dashboardが自動的に新しいグループを作成します：

```python
group="my_group",
group_title="マイグループ",
group_title_en="My Group",
```

---

## よく使うCSSクラス名

モジュールのビューでHTMLインジェクションモードを使用する場合、視覚的一貫性を保つためにDashboardの既存のCSSクラス名を直接使用できます：

| クラス名 | 用途 |
|------|------|
| `page-title` | ページタイトル、例：`<h1 class="page-title">タイトル</h1>` |
| `card` | カードコンテナ |
| `card-header` | カードのタイトルバー |
| `card-body` | カードのコンテンツ領域 |
| `grid-2` | 2カラムグリッドレイアウト |
| `grid-3` | 3カラムグリッドレイアウト |
| `btn` | 基本ボタン |
| `btn-primary` | メインボタン（青） |
| `btn-secondary` | サブボタン |
| `btn-icon` | アイコンボタン |
| `btn-danger` | 危険な操作用ボタン |

DashboardはCSS変数でテーマカラーを制御しており、モジュールのビュー内で直接参照できます：

| CSS変数 | 用途 |
|----------|------|
| `var(--bg-p)` | メイン背景色 |
| `var(--bg-s)` | サブ背景色 |
| `var(--bg-t)` | 第3背景色（カードなど） |
| `var(--tx-p)` | メインテキスト色 |
| `var(--tx-s)` | サブテキスト色 |
| `var(--tx-t)` | 補助テキスト色 |
| `var(--bd)` | ボーダー色 |
| `var(--accent)` | アクセントカラー |
| `var(--ok-c)` | 成功色 |
| `var(--er-c)` | エラー色 |

これらの変数はDashboardのライト/ダークテーマに応じて自動的に切り替わるため、モジュール側で追加の処理は不要です。

---

## 認証とAPI呼び出し

モジュールのビューのJSからモジュール独自のAPIを呼び出す際は、認証のためにDashboardのトークンを付ける必要があります：

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

モジュールのAPIエンドポイントがトークンを検証するかどうかは自由に決定できます。検証が必要な場合は、リクエストヘッダーから抽出できます：

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## 完全なモジュール例

以下は完全な天気モジュールの例で、ビューの登録方法、APIデータの提供方法、アンロード時のリソースクリーンアップ方法を示しています：

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command


class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("Weather")
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(lazy_load=False, priority=50)

    async def on_load(self, event):
        self._register_routes()
        self._register_dashboard_view()
        self.logger.info("天気モジュールがロードされました")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("天気モジュールがアンロードされました")

    def _load_config(self):
        config = self.sdk.config.getConfig("Weather")
        if not config:
            default = {"city": "北京", "api_key": ""}
            self.sdk.config.setConfig("Weather", default)
            return default
        return config

    def _register_routes(self):
        r = self.sdk.router
        r.register_http_route("Weather", "/api/current",
                              handler=self._api_current, methods=["GET"])

    def _unregister_routes(self):
        r = self.sdk.router
        try:
            r.unregister_http_route("Weather", "/api/current")
        except Exception:
            pass

    async def _api_current(self, request):
        return {
            "city": self.config.get("city", "北京"),
            "temp": 25,
            "humidity": 60,
        }

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="天気", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">天気検索</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">現在の天気情報を表示</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">現在の天気</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">「更新」をクリックして読み込み</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">操作</div>
                            <div class="card-body">
                                <button class="btn btn-primary" onclick="refreshWeather()">更新</button>
                            </div>
                        </div>
                    </div>
                ''',
                js_content='''
                    async function loadWeatherView() { await refreshWeather(); }
                    async function refreshWeather() {
                        var el = document.getElementById('weather-info');
                        if (!el) return;
                        el.textContent = '読み込み中...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>都市: ' + (data.city || '--') + '</p>' +
                                           '<p>温度: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>湿度: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = '読み込み失敗: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"Dashboardビューの登録に失敗しました: {e}")
```

---

## ビューの登録解除

モジュールのアンロード時には `unregister_view()` を呼び出して、登録済みのビューをクリーンアップする必要があります：

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

登録解除後、DashboardのフロントエンドはWebSocketを通じてサイドバーナビ項目とページコンテンツをリアルタイムで削除するため、ユーザーがページを再読み込みする必要はありません。

---

## 注意事項

1. **ロード順序** — Dashboardのロード優先度は `99999`（高優先度）です。あなたのモジュールの優先度はこれより低い値（例：`50`）にし、Dashboardが先にロードを完了するようにしてください
2. **防御的プログラミング** — Dashboardモジュールが未インストールまたは未ロードの可能性があるため、ビュー登録時は `try/except` で囲んでください
3. **リソースクリーンアップ** — `on_unload` 内で `unregister_view()` を呼び出し、登録済みのビューを削除してください
4. **IDの一意性** — `id` パラメータはDashboard全体で一意である必要があります。モジュール名をそのまま使用することを推奨します
5. **SVGアイコン** — `icon_svg` は完全な `<svg>` タグである必要があります。サイズは `viewBox="0 0 24 24"` を使用し、`stroke="currentColor"` でDashboardのテーマカラーを継承することを推奨します
6. **JS関数の命名** — `js_content` 内の関数名は一意なもの（例：`loadWeatherView`）にし、他のモジュールとの衝突を避けてください
7. **動的更新** — モジュールがビューを登録/登録解除すると、DashboardのフロントエンドはWebSocketを通じてサイドバーをリアルタイムで更新します。ページの再読み込みは不要です

---

## 次のステップ

- **PCを開かずにスマホでボットを管理したい**：[ErisPulse-App](app.md)（公式マルチプラットフォームクライアント。Dashboardと同じAPIセットを共有しており、モジュールのビューも同様に利用可能）
- **ビューにバックエンドデータAPIを提供したい**：[ルートマネージャー](../advanced/router.md)でHTTPルートを登録します。メソッドの早見表は[コアモジュールAPI - Router](../api-reference/core-modules.md)を参照
- **ビュー内でリアルタイムログ / イベントストリームを表示したい**：[ログサブスクリプション（プッシュモード）](../api-reference/core-modules.md)と[ライフサイクル管理](../advanced/lifecycle.md)

## 定时任务

> 来源: `docs/ja/ecosystem/cron.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/ecosystem/cron.md）

# ErisPulse-Cron

> [!TIP]  
> **このドキュメントを読む必要があるタイミング**:  
> モジュールで定時/遅延実行のロジック（定時アラーム、周期的な監視、Cron 式によるスケジューリング）が必要で、フレームワークの再起動後にタスクが失われないことを望む場合にこのドキュメントを読む。不要であればスキップしてください。

[ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) は ErisPulse エコシステムの**定時タスクスケジューラーモジュール**であり、他のモジュールに統一された定時タスク API を提供します。このモジュールは、一度限りのタイマー、間隔繰り返し、Cron 式の 3 種類のタスクタイプをサポートし、コールバックにパラメータを渡すことができ、SQLite による永続化により、再起動してもタスクが失われません。

> [!IMPORTANT]  
> Cron は ErisPulse フレームワークの内蔵機能ではなく、個別にインストールする必要があります:  
>  
> ```bash
> epsdk install Cron
> ```

インストール後は `sdk.Cron` を通じてすべてのインターフェースにアクセスできます。  
---

## 機能速覧

- **3 種類のタイミング設定**：1 回限り (`once`)、間隔によるループ (`interval`)、Cron 式 (`cron`)
- **コールバック引数**：`callback_data` を作成時に渡すことで、トリガー時に元のデータを返却し、タスクの元を識別可能
- **永続化**：SQLite に保存 (`sdk.storage`) され、フレームワークの再起動後も自動的に復元
- **遅れ対応戦略**：即時実行 / 飛ばす / 再スケジューリング、タスクごとに選択可能
- **タスク管理**：一時停止、再開、キャンセル、手動実行、期限切れタスクのクリーンアップ
- **Dashboard 連携**：[ErisPulse-Dashboard](dashboard.md) をインストールしている場合、管理ウィンドウが自動的に登録される

## 速習

```python
from ErisPulse import sdk

# 1. コールバックハンドラの登録
@sdk.Cron.on_trigger
async def handle_trigger(info):
    data = info["callback_data"]
    print(f"タスクがトリガーされました: {info['task_id']}, データ: {data}")

# 2. タイマーの作成
task_id = sdk.Cron.once(
    delay=60,
    callback_data={"type": "reminder", "msg": "水分補給の時間です"},
)
```

---

## API 概要

### タスクの作成

```python
# 一回限り：600 秒遅延してトリガー
sdk.Cron.once(delay=600, callback_data={"order_id": "123"}, label="注文のタイムアウト通知")

# 間隔ループ：300 秒ごとにトリガー、最大 100 回
sdk.Cron.interval(interval_seconds=300, callback_data={"monitor": "server-1"}, max_runs=100)

# Cron 式：平日の毎日 9:30
sdk.Cron.cron(expression="30 9 * * 1-5", callback_data={"type": "daily_report"})

# 一般的なオプションパラメータ：trigger_at（絶対タイムスタンプ）、delay（最初の遅延）、timezone、
# max_runs（0=無限）、label、source（作成者モジュール名）、missed_policy（遅れ時のポリシー）
```

一般的な Cron 式：`*/5 * * * *`（5 分ごと）、`0 8 * * *`（毎日 8 時）、`30 9 * * 1-5`（平日の 9:30）、`0 0 1 * *`（毎月 1 日）。

### コールバック

```python
@sdk.Cron.on_trigger
async def my_handler(info):
    # info には task_id / task_type / callback_data / label / source /
    # run_count / max_runs / created_at / last_run / trigger_time が含まれる
    ...
```

複数のハンドラを登録可能で、すべて順次実行され、1 つのハンドラの例外は他のハンドラに影響しない。

### タスクの管理

```python
sdk.Cron.cancel(task_id)                  # キャンセル
sdk.Cron.pause(task_id)                   # 一時停止
sdk.Cron.resume(task_id)                  # 再開（reschedule=True で次回トリガーを再計算）
await sdk.Cron.trigger_now(task_id)       # 手動で即時トリガー（元のスケジュールには影響しない）
sdk.Cron.get_task(task_id)                # 1 つのタスクを取得
sdk.Cron.list_tasks(source="MyModule")    # タスク一覧（source/status/task_type によるフィルタリング可能）
sdk.Cron.delete_task(task_id)             # タスク記録を削除
sdk.Cron.cleanup()                        # 7 日前に完了/キャンセルされたタスクをクリーンアップ
```

### 遅れ時のポリシー（missed_policy）

フレームワークの再起動後に、トリガー時間に遅れたタスクに対して：

| ポリシー | 行為 |
|------|------|
| `fire_immediately` | 即時トリガー（デフォルト） |
| `skip` | 今回のトリガーをスキップし、次回を待つ |
| `reschedule` | 現在時刻から次回トリガーを再計算 |

## モジュールのアンロード時の動作

Cron のタスクデータは**永続化されたアセット**です。タスクを作成したモジュールがアンロードまたは無効化されても、既に作成されたタスクは削除されません。ただし、そのモジュールが登録したコールバックハンドルはクリーンアップされます。所有権システムに基づく[外部クリーンアップフック](../advanced/ownership.md#ツールモジュールガイド-他のモジュールのハンドルを管理する)により、Cron が他のモジュールのコールバックを管理する場合、自動的に所有者を記録します。その他のモジュールがアンロードまたは無効化された際に、そのコールバックハンドルは自動的に破棄され、他のモジュールのインスタンスが正常にリサイクルされることが保証されます。

- タスク作成元のモジュールが**再ロード**された後、`on_trigger` を再び実行することで、再びトリガーを受け取ることができます。
- 使用しなくなったタスクは `sdk.Cron.cancel(task_id)` / `delete_task(task_id)` を使用してクリーンアップできます。

## 関連リンク

- [GitHub 仓库](https://github.com/wsu2059q/ErisPulse-Cron)
- [PyPI ページ](https://pypi.org/project/ErisPulse-Cron/)

---

## 次のステップ

- **タスクのトリガー後にユーザーにメッセージを送信**：コールバック内で [Send DSL](../developer-guide/adapters/send-dsl.md) または `event.reply()`（[イベントシステム API](../api-reference/event-system.md) を参照）を使用してリマインダーを送信します。
- **視覚的にスケジュールされたタスクを管理**：[ErisPulse-Dashboard](dashboard.md) をインストールすると、Cron が自動的に管理用のウィンドウを登録します。
- **モジュールのアンインストール時のコールバックのクリーンアップの詳細**：[所有権（owner）システム](../advanced/ownership.md)

## AI 对话模块

> 来源: `docs/ja/ecosystem/qvqchat.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/ecosystem/qvqchat.md）

# ErisPulse-QvQChat 通用インテリジェントエージェント

> [!TIP]
> **このドキュメントを読む必要があるのは**、ロボットに AI インテリジェントエージェントの機能（ツールループ、ストリーミング対話、MCP、長期記憶）を追加したい場合、または独自のモジュールサービスをインテリジェントエージェントから呼び出せるようにしたい場合です。必要ない場合はこのドキュメントは飛ばしてください。

[ErisPulse-QvQChat](https://pypi.org/project/ErisPulse-QvQChat/) は、**汎用的なインテリジェントエージェントモジュール**です。ツールループを基盤として、メッセージの送受信、エコシステムモジュールサービスの呼び出し、コードの作成と実行、コンピュータの操作、画像や音声の生成、スケジュールタスクと長期記憶の管理など、すべてを同一のツールプロトコルで行います。

> [!IMPORTANT]
> QvQChat は個別にインストールする必要があります：
>
> ```bash
> epsdk install ErisPulse-QvQChat
> ```
>
> また、「モデルプール」に少なくとも1つの OpenAI 互換モデル（Base URL、API Key、モデル名）を追加する必要があります。

## 核心能力

| 能力 | 说明 |
|---|---|
| 工具循環 | モデルが出力したツール呼び出し → 並列実行 → 結果の埋め込み → 最終回答が出るまで推論を継続 |
| ストリーミング対話 | SSE による逐字出力、ツールのステップがリアルタイムで表示される；リフレッシュや切り替え後に戻っても、進行状況は失われない |
| コンテキスト圧縮 | token の閾値を超えると、古い対話を要約して圧縮（デフォルトは 128000 估算、カスタマイズ可能） |
| エコシステムサービス橋 | モジュールで宣言されたサービスを自動的にツールとして変換、モジュールの追加・削除で機能を増減可能 |
| MCP クライアント | stdio と Streamable HTTP、MCP ツールを同じツールセットに統合 |
| 子インテリジェントエージェント | `spawn_agent` で独立したセッションの子インテリジェントエージェントを起動し、タスクを探索、結果のみを報告 |
| プロセス内実行 | `run_python_sdk` でメインプロセス内で Python を実行し、実行時のオブジェクトに直接アクセス可能 |
| コンピュータ操作 | 3段階のセキュリティサンドボックス（strict / standard / permissive）、危険な操作は確認が必要、全プロセスを監査 |
| 視覚理解 | 画像を自動的にモデルに注入（画像をサポートしない場合、自動的に削除して再試行） |
| 附件 | ハッシュ値に基づいて任意のファイルを重複除去し、AI にパスを渡して処理させる；Ctrl+V でスクリーンショットを貼り付け可能 |
| 会話共有 | 一時的な読み取り専用リンク（有効期間とトークン予算付き）、Markdown でエクスポート可能 |
| 定時タスク | cron / 一回限り / 間隔、永続化、権限は作成者に付与 |
| 会話の引き継ぎ | 管理者はインテリジェントエージェントが特定の会話を独占できるようにできる |
| パーソナリティシステム | システムプロンプト + 初回対話 + ツールホワイトリスト、会話にバインド可能 |
| 長期記憶 | 各会話ごとのメモリ項目、類似度に基づいて検索して注入 |
| AI による自動命名 | 会話の最初の返信後に、簡潔なタイトルを自動生成 |

## モジュール拡張

ErisPulse モジュールが `services` を宣言すると、専用のインターフェースを必要とせず、QvQChat のツールとして自動的に機能します。

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class Main(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(name="Draw", services=[
            {"name": "draw", "description": "説明に基づいて画像を生成し、画像の URL を返す"},
        ])

    async def draw(self, prompt: str, size: str = "1024x1024"):
        return {"image_url": "https://..."}
```

サービスのメソッドシグネチャは自動的にツールの JSON Schema パラメータ定義にマッピングされ、ドキュメント文字列の最初の行はパラメータの説明として使用されます。

### 深度統合（オプション）

モジュールは以下の任意のサービスを追加で実装できます。各サービスは**個別に選択可能**です。つまり、人格拡張のみを行うモジュールもあれば、プロンプトの注入のみを行うモジュールもあります。

#### `qvq_prompts()` → システムプロンプトの注入

`list[str]` または `list[{"text": str, "priority": int}]` を返します。`priority` が昇順に並べ替えられ、連結されます。

```python
async def qvq_prompts(self):
    return [
        {"text": "画像を描画した後、send_message を使って画像をユーザーに送信する。", "priority": 10},
        {"text": "対応するスタイル：アニメ、写実、水彩、ピクセル。", "priority": 20},
    ]
```

#### `qvq_personas()` → 人格プリセットの登録

人格のリストを返します。`id` には自動的に `ext.<モジュール名>.` というプレフィックスが追加され、モジュールのアンロード時に自動的にクリーンアップされます。これは、感情的なサポート、翻訳担当者、コードレビュー担当者など、人格拡張専用のモジュールに適しています。

```python
async def qvq_personas(self):
    return [
        {"id": "companion", "name": "暖男", "system": "あなたは温かく思いやりのあるチャットパートナーです..."},
        {"id": "coder", "name": "コード指導者", "system": "...", "tools": ["read_file", "run_python"]},
    ]
```

`tools` は、その人格が使用できるツールのサブセットを限定することもできます。

#### `qvq_schemas()` → 明示的なパラメータ schema

`dict[サービス名, JSON Schema]` を返し、メソッドシグネチャの推論を上書きします。パラメータが複雑または厳密な検証が必要な場合に使用します。

```python
async def qvq_schemas(self):
    return {
        "draw": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "画面の説明"},
                "size": {"type": "string", "enum": ["512x512", "1024x1024"]},
            },
            "required": ["prompt"],
        },
    }
```

### リフレッシュタイミング

深度統合サービスのリフレッシュタイミングは、起動時、モジュールのロード/アンロード時、およびダッシュボードの「ツール」ページでの手動リフレッシュ時です。

## イベントのサブスクライブ

QvQChat は 2 つのライフサイクルイベントをブロードキャストします：

| イベント | 時機 | ペイロード |
|---|---|---|
| `qvq.message` | ユーザーメッセージ受信時 | `chat_key` `platform` `sender_id` `sender_name` `text` `is_group` |
| `qvq.replied` | レプリが送信された後 | `chat_key` `reply` `tools` |

```python
async def setup(self):
    sdk.lifecycle.on("qvq.message", self.on_message)
```

## サービスとして呼び出される

| サービス | シグネチャ | 説明 |
|---|---|---|
| `chat` | `(session_id, prompt, persona="")` | スマートエージェントと対話し、テキストを返す |
| `run_prompt` | `(chat_key, prompt, ...)` | プロンプトを実行し、結果をターゲットセッションに送信できる |
| `get_status` | `()` | 実行状態の概要 |

## インターフェース

`/QvQChat/view` に独立してアクセスするか、ダッシュボードのサイドバーに埋め込むことができます。

![概要](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/overview.png)

![会話](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/chat.png)

---

## 次に進む

- **自分のモジュールをエージェントツールにする**：`get_meta()` で `services` を宣言するだけで可能。フィールドの意味は [コアモジュール API - サービス契約](../api-reference/core-modules.md) を参照してください。
- **エージェントメッセージのサブスクライブで連携させる**：[ライフサイクルイベント](../advanced/lifecycle.md) を使って `qvq.message` / `qvq.replied` を監視します。
- **エージェントを使わず、ただの複数回対話フォームが欲しい場合**：内蔵の [Conversation 複数回対話](../advanced/conversation.md) がより軽量な選択です。
- **ウェブ管理**：[ErisPulse-Dashboard](dashboard.md) のサイドバーと併用してください。

## 平台指南索引

> 来源: `docs/ja/platform-guide/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/platform-guide/README.md）

# ErisPulse PlatformFeatures ドキュメント

> 基準プロトコル: [OneBot12](https://12.onebot.dev/)  
> 本文書は**プラットフォーム固有の機能ガイド**であり、以下を含む：
> - 各アダプタがサポートするSendメソッドの連鎖呼び出し例
> - プラットフォーム固有のイベント/メッセージフォーマットの説明
> 
> 一般的な使用方法は以下のドキュメントを参照してください：
> - [基本概念](../getting-started/basic-concepts.md)
> - [イベント変換基準](../standards/event-conversion.md)  
> - [APIレスポンス規格](../standards/api-response.md)

---

## プラットフォーム固有の機能

このセクションは、各アダプタの開発者が維持・更新するものであり、OneBot12標準との差異や拡張機能を説明するためのものです。以下の各プラットフォームの詳細ドキュメントを参照してください：

- [維持説明](maintain-notes.md)

- [雲湖プラットフォームの特徴](yunhu.md)
- [雲湖ユーザープラットフォームの特徴](yunhu_user.md)
- [Telegramプラットフォームの特徴](telegram.md)
- [OneBot11プラットフォームの特徴](onebot11.md)
- [OneBot12プラットフォームの特徴](onebot12.md)
- [SnowLumaプラットフォームの特徴](snowluma.md)
- [メールプラットフォームの特徴](email.md)
- [Kook(開黒啦)プラットフォームの特徴](kook.md)
- [Matrixプラットフォームの特徴](matrix.md)
- [QQ公式ロボットプラットフォームの特徴](qqbot.md)
- [花楓コーヒーハウス](ideaura.md)
- [Discord](discord.md)
- [Webhookプロトコルブリッジ](webhook.md)
- [WeChat公式アカウント](wechatmp.md)

> また、`sandbox`アダプタもありますが、このアダプタにはプラットフォーム固有のドキュメントを維持する必要はありません。

---

## 一般的なインターフェース

### Send 鏈式呼び出し

すべてのアダプタは以下の標準的な呼び出し方法をサポートしています：

> **注意:** ドキュメント内の `{AdapterName}` は実際のアダプタ名（例: `yunhu`、`telegram`、`onebot11`、`email` など）に置き換える必要があります。

1. タイプとIDを指定: `To(type,id).Func()`
   ```python
   # アダプタインスタンスを取得
   my_adapter = adapter.get("{AdapterName}")
   
   # メッセージを送信
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. IDのみを指定: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 送信アカウントを指定: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例:
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼び出し: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # 例:
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### 非同期送信と結果処理

Send DSLのメソッドは`asyncio.Task`オブジェクトを返すため、結果を即座に待つか、後で待つかを選択できます：

```python
# アダプタインスタンスを取得
my_adapter = adapter.get("{AdapterName}")

# 結果を待たずにバックグラウンドでメッセージを送信
task = my_adapter.Send.To("user", "123").Text("Hello")

# 送信結果が必要な場合は、後で待つ
result = await task
```

#### 送信ルールデコレータ

実際の開発では、送信が成功した後に後続の処理を実行したい、失敗時に自動でリトライしたい、タイムアウトでキャンセルしたい、送信の進行状況を監視したいなどの要望があります。Send DSLには、これらの要望に応えるための送信ルールデコレータが組み込まれており、送信メソッドの前にチェーンでルールを追加できます：

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信が成功した後に実行されるコールバック（複数回呼び出せる） |
| `.Retry(times=1)` | 失敗時にリトライをN回（初回含む、合計N+1回） |
| `.Timeout(seconds)` | 単回送信のタイムアウト、タイムアウトでキャンセル（Retryと組み合わせ可） |
| `.Defer(seconds)` | 送信を遅延（プロセス内での単純な遅延、永続化はしない） |
| `.OnProgress(callback)` | 各段階の進行状況をコールバック、SendContextを渡す |
| `.OnError(callback)` | 最終的に失敗した際のエラーコールバック（1回のみ発動） |

```python
yunhu = adapter.get("yunhu")

# 送信成功後にポイントを減らす
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消費成功"))

# 失敗リトライ + タイムアウトキャンセル + 進行状況の監視
def on_progress(ctx):
    print(f"段階: {ctx.stage}, 試行: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # 最大3回リトライ
        .Timeout(10)           # 10秒でタイムアウト
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要通知"))
```

ルールメソッドは`self`を返すため、送信メソッド（Text/Imageなど）の前に呼び出す必要があります。`SendContext`には`stage`（pending/sending/retrying/success/failed/timeout）、`attempt`、`elapsed`、`error`、`result`などのフィールドが含まれ、モニタリングに便利です。

#### バッチ構築モード（Build）

1つのチェーンで複数の送信メソッドを構築し、最後にまとめて実行します。これは「一気に複数のメッセージを送信する」ような場面に適しています：

```python
yunhu = adapter.get("yunhu")

# 複数のメッセージを構築し、まとめて送信
results = await (yunhu.Send.To("user", "123")
                .Build()                     # 構築モードに入る
                .Text("通知一")
                .Image("pic.jpg")
                .Text("通知二")
                .send_all())                 # まとめて実行
# results = [Textの結果, Imageの結果, Textの結果]
```

`.send_all()`はデフォルトで**並列**実行（並行送信、効率的）です。順序を保証したい場合は`.Sequential()`で**直列**実行します：

```python
# 直列実行（順序を保証）+ 失敗リトライ
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # 送信順序を保証
       .Retry(2)                     # 失敗した項目はそれぞれリトライ
       .Text("第一条").Text("第二条")
       .send_all())
```

バッチ実行では**失敗継続**戦略を採用しています：1つのメッセージが失敗しても他のメッセージは中断されず、失敗したメッセージは自動でリトライされます。バッチ実行では、全メッセージが成功した後に発動する`Hook`、失敗した場合に発動する`OnError`、進行状況を監視する`OnProgress`もサポートしています。

> さらに詳細なルールとバッチ構築の説明は [SendDSL 詳解](../developer-guide/adapters/send-dsl.md) を参照してください。

### イベント監視

3種類のイベント監視方法があります：

1. プラットフォーム固有のイベント監視：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"受信した{AdapterName}プラットフォームのイベント: {data}")
   ```

2. OneBot12標準イベント監視：
   ```python
   from ErisPulse.Core import adapter, logger

   # OneBot12標準イベントを監視
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"受信した標準イベント: {data}")

   # 特定プラットフォームの標準イベントを監視
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"受信した{AdapterName}プラットフォームの標準イベント: {data}")
   ```

3. Eventモジュールによるイベント監視：
    `Event`のイベントは`adapter.on()`関数に基づいているため、`Event`が提供するイベントフォーマットはOneBot12標準イベントです。

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="挨拶メッセージを送信", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"受信したメッセージ: {event}")
    async def notice_handler(event):
        logger.info(f"受信した通知: {event})
    async def request_handler(event):
        logger.info(f"受信したリクエスト: {event})
    async def command_handler(event):
        logger.info(f"受信したコマンド: {event})
    ```

この中で、最も推奨されるのは`Event`モジュールによるイベント処理です。`Event`モジュールは豊富なイベントタイプとイベント処理メソッドを提供しているためです。

---

## 標準フォーマット
参考のため、ここにイベントフォーマットの簡単な例を示します。詳細情報が必要な場合は、上記のリンクを参照してください。

> **注意:** 以下のフォーマットは基本的なOneBot12標準フォーマットであり、各アダプタはこの上に拡張フィールドを追加する可能性があります。具体的な内容は、各アダプタの特定機能の説明を参照してください。

### 標準イベントフォーマット
すべてのアダプタが実装するイベント変換フォーマット：
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### 標準レスポンスフォーマット
#### メッセージ送信成功
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### メッセージ送信失敗
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "必要なパラメータが不足しています",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## 参考リンク
ErisPulseプロジェクト：
- [主リポジトリ](https://github.com/ErisPulse/ErisPulse/)
- [Yunhuアダプタリポジトリ](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegramアダプタリポジトリ](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBotアダプタリポジトリ](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

関連公式ドキュメント：
- [OneBot V11プロトコルドキュメント](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API公式ドキュメント](https://core.telegram.org/bots/api)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/1-3)

## 貢献の参加

開発者の方々からのさらなる貢献を歓迎します！以下の手順に従って、貢献を提出してください：
1. [ErisPulse](https://github.com/ErisPulse/ErisPulse) リポジトリをForkします。
2. `docs/platform-features/` ディレクトリにMarkdownファイルを作成し、`<プラットフォーム名>.md`という形式で命名します。
3. 本`README.md`ファイルに、ご自身が貢献したアダプタへのリンクと、関連する公式ドキュメントを追加します。
4. Pull Requestを提出します。

ご支援ありがとうございます！
