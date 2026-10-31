---
name: erispulse-ecosystem
description: "适用于：了解生态组件（Dashboard/Cron/AI 模块等）与各平台适配器的接入差异。覆盖场景：ErisPulse フレームワーク自体はコア機能（イベントシステム、モジュールシステム、設定、ルーティング、ログなど）のみを提供し、GUI、画像レンダリング、可視化などの「ヘビー級」機能は**組み込まれていません**。これらの機能は、コミュニティがメンテナンスする**サードパーティモジュール**によって提供されており、必要に応じてインストールするだけで利用できます。**このドキュメントを読むべきとき**：Web画面でボットを視覚的に管理したい場合（モジュールの有効化・無効化、設定編集、ログ閲覧、イベントストリームの監視など）、または自分のモジュール用のDashboard管理ページを登録したい場合にお読みください。必要ない場合はスキップして構いません。**このドキュメントを読む必要があるタイミング**:。**このドキュメントを読む必要があるのは**、ロボットに AI インテリジェントエージェントの機能（ツールループ、ストリーミング対話、MCP、長期記憶）を追加したい場合、または独自のモジュールサービスをインテリジェントエージェントから呼び出せるようにしたい場合です。必要ない場合はこのドキュメントは飛ばしてください。**このドキュメントを読むべきタイミング**：Claude Desktop などの MCP 対応 AI クライアントに、あなたのボットを直接操作させたい場合——メッセージの送信、メッセージの閲覧、モジュールの呼び出し、アダプターの管理、イベントストリームの監視——に読んでください。必要なければ読み飛ばして構いません。このセクションは各アダプター開発者によって保守されており、そのアダプターとOneBot12標準との差分および拡張機能について説明するものです。以下の各プラットフォームの詳細ドキュメントを参照してください：。"
---

# ErisPulse 生态与多平台

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 生态总览: 59-78 行
- 推奨モジュール: 80-130 行
- 公式クライアント（スタンドアロンプログラム）: 132-142 行
- 自分のモジュールもここに載せたいですか？: 144-152 行
- Dashboard: 154-181 行
- 動作原理: 183-194 行
- 登録API: 196-234 行
- 2つのインジェクションモード: 236-269 行
- サイドバーグループ: 271-297 行
- よく使うCSSクラス名: 299-334 行
- 認証とAPI呼び出し: 336-358 行
- 完全なモジュール例: 360-470 行
- ビューの登録解除: 472-484 行
- 注意事項: 486-496 行
- 次のステップ: 498-502 行
- 定时任务: 504-524 行
- 機能速覧: 526-533 行
- 速習: 535-553 行
- API 概要: 555-608 行
- モジュールのアンロード時の動作: 610-615 行
- 関連リンク: 617-622 行
- 次のステップ: 624-628 行
- AI 对话模块: 630-648 行
- 核心能力: 650-669 行
- モジュール拡張: 671-741 行
- イベントのサブスクライブ: 743-755 行
- サービスとして呼び出される: 757-763 行
- 拡張プラグイン: 765-775 行
- インターフェース: 777-785 行
- 次に進む: 787-792 行
- MCP 桥: 794-812 行
- 仕組み: 814-825 行
- Claude Desktop 接続: 827-845 行
- 14 個のツール一覧: 847-857 行
- セキュリティ上の要点: 859-868 行
- 次のステップ: 870-874 行
- 平台指南索引: 876-893 行
- プラットフォーム固有機能: 895-921 行
- 共通インターフェース: 923-1103 行
- 標準形式: 1105-1161 行
- 参考リンク: 1163-1173 行
- コントリビューション: 1175-1184 行

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

## 推奨モジュール

### ErisPulse-Dashboard：ブラウザ内管理パネル

サーバーにロボットを常駐させると、モジュールの起動・停止、設定の変更、ログの確認などはターミナルにログインする必要がありますか？Dashboard はこれらの機能をブラウザに移行します：モジュールの起動・停止、設定の編集、ログの確認、イベントの監視。他のモジュールはサイドバーにカスタムウィンドウを登録でき、管理ページを一か所に集めることができます。

```bash
epsdk install Dashboard
```

ドキュメント：[Dashboard 使用とウィンドウ登録](dashboard.md) ｜ プロジェクトページ：[PyPI](https://pypi.org/project/ErisPulse-Dashboard/)

### ErisPulse-Cron：スケジュールタスク

毎日定期的なチェックイン通知を送信したり、Cron式で周期的なタスクを実行したり、数分ごとにデータをポーリングしたいですか？Cronは一回限りのタスク、間隔をあけたタスク、Cron式のタスクの3種類を提供し、コールバックにパラメータを渡すことができます。SQLiteで永続化（再起動してもタスクが失われません）。

```bash
epsdk install Cron
```

ドキュメント：[Cron 定時タスク](cron.md) ｜ プロジェクトページ：[GitHub](https://github.com/wsu2059q/ErisPulse-Cron)

### ErisPulse-QvQChat：汎用エージェント

グループに単なるキーワード応答を行うだけではなく、実用的なAIアシスタントを配置したいですか？QvQChatは汎用エージェントです：ツールのループでメッセージの送受信、コード実行、コンピュータ操作、画像生成、音声、MCP、サブエージェントをカバーします。ストリーミング対話とツールの連続実行がサポートされ、内蔵のDashboardウィンドウも備えています。QvQStalker（傍聴・介入）、QvQMemes（絵文字）、QvQCompanion（擬人化付き同伴）の3つの付属プラグインもあります。

```bash
epsdk install ErisPulse-QvQChat
```

ドキュメント：[QvQChat エージェント](qvqchat.md) ｜ プロジェクトページ：[GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-ApiMCP：AIクライアントがロボットを操作する

Claude Desktop、Claude CodeなどのMCPに対応したAIクライアントを使用していますか？ApiMCPは14のMCPツールとしてロボットの実行時を逆方向に公開します：AIは直接メッセージの送受信、インストール済みモジュールの呼び出し、プラットフォームの状態の確認、グループチャットイベントのサブスクライブを行うことができます。ロボットはAIの「手と目」になります。

```bash
epsdk install ErisPulse-ApiMCP
```

ドキュメント：[ApiMCP 使用ガイド](apimcp.md) ｜ プロジェクトページ：[GitHub](https://github.com/wsu2059q/ErisPulse-ApiMCP)

### ErisPulse-Takumi：画像レンダリング

ランキング、戦報、スケジュールカードなどの「画像を送る」必要がある場面では、テンプレートを書いて画像にレンダリングしてグループに送信するだけです：HTML / ノードツリー / Jinja / SVG / アニメーション（[takumi-py](https://github.com/BalconyJH/takumi-py) に基づく）をサポートし、内蔵の中英文字体を備え、すぐに使用できます。

```bash
epsdk install Takumi
```

ドキュメント：[Takumi 画像レンダリング](takumi.md) ｜ プロジェクトページ：[GitHub](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)）

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

## 拡張プラグイン

QvQChat を拡張する 3 つの独立したモジュールが、拡張ポイントが何ができるかを示しています。QvQChat をインストールした後、必要に応じてプラグインを追加してください。

| プラグイン | 機能 |
|---|---|
| [ErisPulse-QvQStalker](https://github.com/wsu2059q/ErisPulse-QvQStalker) | チャットをリスニングして自動で発言：話題の注目度、5 段階の判定と衝動値が、AI が発言するタイミングを決定し、15 項目の行動パラメータは設定ページで直接調整可能 |
| [ErisPulse-QvQMemes](https://github.com/wsu2059q/ErisPulse-QvQMemes) | AI に絵文字習慣を付与：`send_sticker` ツールにより、モデルがどの絵文字を送信すべきかを自動選択し、グループ画像は自動収集され、視覚モデルによってラベル付けされる |
| [ErisPulse-QvQCompanion](https://github.com/wsu2059q/ErisPulse-QvQCompanion) | 擬人化された伴侶としての機能：口調やキャラクター設定の注入、衝動値に基づく自発的な発言、静止時間帯と毎日の上限設定 |

3 つのプラグインはすべて、上記の「モジュール拡張」の契約に従ってサービスに接続されており、拡張の実装方法の参考例でもあります。

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

## MCP 桥

> 来源: `docs/ja/ecosystem/apimcp.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/ecosystem/apimcp.md）

# ErisPulse-ApiMCP で AI クライアントからボットを操作する

> [!TIP]
> **このドキュメントを読むべきタイミング**：Claude Desktop などの MCP 対応 AI クライアントに、あなたのボットを直接操作させたい場合——メッセージの送信、メッセージの閲覧、モジュールの呼び出し、アダプターの管理、イベントストリームの監視——に読んでください。必要なければ読み飛ばして構いません。

[ErisPulse-ApiMCP](https://github.com/wsu2059q/ErisPulse-ApiMCP) は、ボットのランタイム機能を **MCP（Model Context Protocol）** 経由で AI クライアントに公開します：インストール後、Claude Desktop には 14 個のツールが追加され、AI があなたに代わってメッセージの送受信、モジュールの問題のトラブルシューティング、グループチャットイベントの購読を行えるようになります——ボットは「あなたが管理するプログラム」から「AI の手と目」へと変わります。

> [!IMPORTANT]
> ApiMCP は別途インストールが必要で、**token を明示的に設定して初めて**ブリッジが有効になります：
>
> ```bash
> epsdk install ErisPulse-ApiMCP
> ```
>
> `config.toml` の `[ApiMCP]` セクションに `token = "長いランダム文字列"` を設定します（または環境変数 `ERISPULSE_APIMCP_TOKEN` を使用）。未設定の場合、ヘルスチェックを除くすべてのエンドポイントが 503 を返し、トークンの意図しない漏洩を防ぎます。

## 仕組み

2層構造となっており、ボット本体には AI への依存を一切導入していません：

- **ボットプロセス内**：ApiMCP モジュールがフレームワーク内蔵の HTTP サーバー上に REST ブリッジをマウントします（`/apimcp/*`、トークン認証、デフォルトのレート制限は 30 リクエスト/分）
- **独立プロセス**：`erispulse-apimcp` コマンドが公式の `mcp` SDK を使用して stdio サーバーを起動し、MCP ツール呼び出しをボットの HTTP ブリッジへ転送します

```
Claude Desktop ──MCP(stdio)──► erispulse-apimcp ──HTTP──► ボットプロセス REST ブリッジ ──► sdk.*
```

ボットがオフラインの場合やブリッジが未設定の場合、ツールは読みやすいエラーメッセージとトラブルシューティングのガイドを返し、スタックトレースはスローしません。

## Claude Desktop 接続

`claude_desktop_config.json` を編集します（Windows: `%APPDATA%\Claude\`、macOS: `~/Library/Application Support/Claude/`）：

```json
{
  "mcpServers": {
    "erispulse": {
      "command": "erispulse-apimcp",
      "env": {
        "ERISPULSE_APIMCP_URL": "http://127.0.0.1:8000",
        "ERISPULSE_APIMCP_TOKEN": "あなたのトークン"
      }
    }
  }
}
```

保存後、Claude Desktop を完全に再起動し、ツールリストに `erispulse` サーバーが表示されれば接続成功です。MCP stdio server をサポートする任意のクライアント（Claude Code、Cursor など）でも、同じ方法で接続できます。

## 14 個のツール一覧

| カテゴリ | ツール | 説明 |
|---|---|---|
| モジュール | `list_modules` / `get_module_info` / `call_module` / `reload_module` | インストール済みモジュールの公開サービスの確認・呼び出し、ホットリロードの実行 |
| アダプター | `list_adapters` / `get_adapter_status` / `reload_adapter` | プラットフォームのオンライン状態。アダプターのリロードはデフォルトで無効 |
| メッセージ | `send_message` / `recent_messages` | 任意のプラットフォームへテキスト/画像/音声/動画/ファイルを送信。[transcript](../advanced/transcript.md) 経由で最近のメッセージを振り返る |
| イベント | `subscribe_events` / `unsubscribe` / `poll_events` | メッセージ/通知などのイベントを購読、リングバッファ（デフォルト 1000 件）、増分ポーリング |
| ランタイム | `get_topology` / `sdk_health` | ランタイムトポロジー（マスキング済み）と健全性サマリー |

典型的な使用例：AI はまず `subscribe_events(["message"])` を実行し、その後定期的に `poll_events` でグループ内の会話を観察し、`send_message` で発言に割り込むか、`call_module` で特定のモジュールの機能を呼び出すかを判断します。

## セキュリティ上の要点

- **トークンは完全な制御権限**：メッセージの読み取り、送信、ホワイトリスト内モジュールメソッドの呼び出しが可能になります。リポジトリへのコミットや公開チャンネルへの貼り付けは絶対にしないでください。マルチテナント環境では複数のボットインスタンスに分割してください
- **最小権限の付与**：`module_call_whitelist` で呼び出し可能なモジュールを絞り込み（`モジュール.メソッド` 形式による精密な許可に対応）、`send_target_whitelist` で送信先を絞り込み（例：特定のグループへの送信のみ許可）、`allow_adapter_reload` はデフォルトの無効状態を維持してください
- **ローカルホストのみでリッスン**：ローカル環境でのみ使用する場合は、フレームワークの HTTP サーバーを `server.host = "127.0.0.1"` に設定してください。マシンをまたぐ場合は、内部ネットワーク + リバースプロキシによる TLS が必須です
- 出力はキー名レベルでサニタイズされます（キー/パス系のキーはキーごと破棄）。深いレベルのサニタイズはモジュール自身の責任であり、機密性の高いセッションではサブスクリプションを開放しないでください

完全な設定項目（バッファ容量、ルックバックウィンドウ、イベントタイプのホワイトリストなど）と REST エンドポイントの詳細については、[プロジェクトの README](https://github.com/wsu2059q/ErisPulse-ApiMCP) を参照してください。

---

## 次のステップ

- **AIを単に操作される存在ではなく、グループ内で「生き」させたい**：QvQChatは正方向——エージェントが能動的にチャットや作業を行う。詳細は [QvQChat 汎用エージェント](qvqchat.md) を参照。ApiMCPは逆方向——外部AIがボットを操作する。両方を同時にインストール可能
- **最近のメッセージのデータがどこから来るのか知りたい**：[会話受信トレイ transcript](../advanced/transcript.md)
- **ボットのHTTP serverについて知りたい**：[ルーティングシステム](../advanced/router.md)

## 平台指南索引

> 来源: `docs/ja/platform-guide/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/platform-guide/README.md）

# ErisPulse PlatformFeatures ドキュメント

> 基準プロトコル：[OneBot12](https://12.onebot.dev/) 
> 
> 本ドキュメントは**プラットフォーム固有機能ガイド**であり、以下の内容を含みます：
> - 各アダプターが対応するSendメソッドの連鎖呼び出し（チェーン呼び出し）例
> - プラットフォーム固有のイベント/メッセージ形式の説明
> 
> 一般的な使用方法については以下を参照してください：
> - [基本概念](../getting-started/basic-concepts.md)
> - [イベント変換標準](../standards/event-conversion.md)  
> - [APIレスポンス仕様](../standards/api-response.md)

---

## プラットフォーム固有機能

このセクションは各アダプター開発者によって保守されており、そのアダプターとOneBot12標準との差分および拡張機能について説明するものです。以下の各プラットフォームの詳細ドキュメントを参照してください：

- [メンテナンスガイド](maintain-notes.md)

- [Yunhuプラットフォーム特性](yunhu.md)
- [Yunhuユーザープラットフォーム特性](yunhu_user.md)
- [Telegramプラットフォーム特性](telegram.md)
- [OneBot11プラットフォーム特性](onebot11.md)
- [OneBot12プラットフォーム特性](onebot12.md)
- [SnowLumaプラットフォーム特性](snowluma.md)
- [メールプラットフォーム特性](email.md)
- [Kookプラットフォーム特性](kook.md)
- [Matrixプラットフォーム特性](matrix.md)
- [WeCom（企業向けWeChat）プラットフォーム特性](wecom.md)
- [Bilibili プラットフォーム特性](bilibili.md)
- [Minecraft プラットフォーム特性](minecraft.md)
- [QQ公式ボットプラットフォーム特性](qqbot.md)
- [花楓珈琲館](ideaura.md)
- [Discord](discord.md)
- [Webhookプロトコルブリッジ](webhook.md)
- [WeChat公式アカウント](wechatmp.md)

> また `sandbox` アダプターもありますが、このアダプターにはプラットフォーム特性ドキュメントの保守は不要です

---

## 共通インターフェース

### Send 連鎖呼び出し
すべてのアダプターが以下の標準的な呼び出し方法に対応しています：

> **注意：** ドキュメント内の `{AdapterName}` は実際のアダプター名（例： `yunhu`、`telegram`、`onebot11`、`email` など）に置き換えてください。

1. タイプとIDを指定： `To(type,id).Func()`
   ```python
   # アダプターインスタンスの取得
   my_adapter = adapter.get("{AdapterName}")
   
   # メッセージの送信
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例：
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. IDのみ指定： `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例：
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 送信アカウントを指定： `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例：
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼び出し： `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # 例：
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### 非同期送信と結果処理

Send DSLのメソッドは `asyncio.Task` オブジェクトを返します。つまり、結果をすぐに待つかどうかを選択できます：

```python
# アダプターインスタンスの取得
my_adapter = adapter.get("{AdapterName}")

# 結果を待たずに、メッセージをバックグラウンドで送信
task = my_adapter.Send.To("user", "123").Text("Hello")

# 送信結果を取得する必要がある場合は、後から待機できます
result = await task
```

#### 送信ルールデコレーター

実際の開発では、送信成功後に後続のロジックを実行する、失敗時に自動リトライ、タイムアウト取消、送信進捗の監視などが必要になることがよくあります。Send DSLには送信ルールデコレーターが組み込まれており、連鎖メソッドを通じてルールを追加できます：

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信成功後に実行されるコールバック（複数回呼び出し可能） |
| `.Retry(times=1)` | 失敗時に自動でN回リトライ（初回を含め計N+1回） |
| `.Timeout(seconds)` | 単回送信のタイムアウト、超過で取消（Retryと併用可） |
| `.Defer(seconds)` | 送信を遅延（プロセス内タイマー、永続化なし） |
| `.OnProgress(callback)` | 各段階の進捗コールバック、SendContextを渡す |
| `.OnError(callback)` | 最終失敗時のエラーコールバック（一度のみ発火） |

```python
yunhu = adapter.get("yunhu")

# 送信成功後にポイントを減算
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消費が完了しました"))

# 失敗時リトライ + タイムアウト取消 + 進捗監視
def on_progress(ctx):
    print(f"段階: {ctx.stage}, 試行: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # 最大3回リトライ
        .Timeout(10)           # 毎回10秒でタイムアウト
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要なお知らせ"))
```

ルールメソッドは `self` を返すため、送信メソッド（Text/Imageなど）の前に呼び出す必要があります。`SendContext` には `stage`（pending/sending/retrying/success/failed/timeout）、`attempt`、`elapsed`、`error`、`result` などのフィールドが含まれ、監視に便利です。

#### 一括構築モード（Build）

1つのチェーン内で複数の送信メソッドを構築し、最後に一括実行します。「一度に複数のメッセージを送る」シナリオに適しています：

```python
yunhu = adapter.get("yunhu")

# 複数のメッセージを構築し、一括送信
results = await (yunhu.Send.To("user", "123")
                .Build()                     # ビルドモードに入る
                .Text("通知1")
                .Image("pic.jpg")
                .Text("通知2")
                .send_all())                 # 一括実行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` はデフォルトで**並列**実行されます（同時送信で効率が高い）。メッセージの到着順序を保証する必要がある場合は、`.Sequential()` を呼び出して逐次実行します：

```python
# 逐次実行（順序保証）+ 失敗時リトライ
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # 順番に送信
       .Retry(2)                     # 失敗した項目はそれぞれリトライ
       .Text("1つ目のメッセージ").Text("2つ目のメッセージ")
       .send_all())
```

一括実行は**失敗継続**ポリシーを採用しています：ある項目が失敗しても他の項目は中断されず、失敗した項目は自動的にリトライされます。一括実行でもバッチ全体の `Hook`（全成功後に発火）、`OnError`（失敗があると発火）、`OnProgress`（進捗コールバック）に対応しています。

> より詳細なルールと一括構築の説明については、[SendDSL 詳解](../developer-guide/adapters/send-dsl.md) を参照してください。

### イベントリスニング
イベントのリスニング方法は3種類あります：

1. プラットフォームネイティブイベントのリスニング：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"{AdapterName}のネイティブイベントを受信: {data}")
   ```

2. OneBot12標準イベントのリスニング：
   ```python
   from ErisPulse.Core import adapter, logger

   # OneBot12標準イベントをリッスン
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"標準イベントを受信: {data}")

   # 特定プラットフォームの標準イベントをリッスン
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"{AdapterName}の標準イベントを受信: {data}")
   ```

3. Eventモジュールによるリスニング：
    `Event`のイベントは `adapter.on()` 関数をベースとしているため、`Event`が提供するイベント形式はOneBot12標準イベントです

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="挨拶メッセージを送信", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"メッセージを受信: {event}")
    async def notice_handler(event):
        logger.info(f"通知を受信: {event}")
    async def request_handler(event):
        logger.info(f"リクエストを受信: {event}")
    async def command_handler(event):
        logger.info(f"コマンドを受信: {event}")
    ```

中でも最も推奨されるのは `Event` モジュールを使用したイベント処理です。`Event` モジュールは豊富なイベントタイプと豊富なイベント処理メソッドを提供しているためです。

---

## 標準形式
参考用として、ここでは簡単なイベント形式を示します。詳細情報が必要な場合は、上記のリンクを参照してください。

> **注意：** 以下の形式は基本的なOneBot12標準形式であり、各アダプターはこのベースに拡張フィールドを追加している場合があります。詳細は各アダプターの固有機能説明を参照してください。

### 標準イベント形式
すべてのアダプターが実装しなければならないイベント変換形式：
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
    {"type": "text", "data": {"text": "こんにちは"}}
  ],
  "alt_message": "こんにちは",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### 標準レスポンス形式
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
ErisPulse プロジェクト：
- [メインリポジトリ](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu アダプターリポジトリ](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram アダプターリポジトリ](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot アダプターリポジトリ](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

関連公式ドキュメント：
- [OneBot V11 プロトコルドキュメント](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 公式ドキュメント](https://core.telegram.org/bots/api)
- [Yunhu公式ドキュメント](https://www.yhchat.com/document/1-3)

## コントリビューション

より多くの開発者にアダプタードキュメントの執筆と保守への参加をご案内しています！以下の手順に従ってコントリビューションを提出してください：
1. [ErisPuls](https://github.com/ErisPulse/ErisPulse) リポジトリをForkします。
2. `docs/platform-features/` ディレクトリにMarkdownファイルを作成し、`<プラットフォーム名>.md` の形式で命名します。
3. この `README.md` ファイルに、ご自身が貢献したアダプターへのリンクおよび関連公式ドキュメントを追加します。
4. Pull Request を提出します。

ご支援ありがとうございます！
