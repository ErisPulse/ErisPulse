# エコシステムモジュール

ErisPulse フレームワーク自体は、イベントシステム、モジュールシステム、設定、ルーティング、ログなどのコア機能のみを提供します。**GUI、画像レンダリング、可視化などの「重い」機能は、標準搭載されていません。** これらの機能は、コミュニティが維持する **サードパーティモジュール** によって提供され、必要に応じてインストールできます。

> [!IMPORTANT]
> 本セクションのドキュメントは、インストール方法が異なる2つのカテゴリに分かれています：
>
> - **モジュール**（例：Dashboard / Takumi）は `epsdk install` を使用してインストールします：
>
>   ```bash
>   epsdk install <モジュール名>
>   ```
>
> - **独立プログラム**（例：ErisPulse-App クライアント）は、対応する GitHub Releases から直接ダウンロードしてインストールします。`epsdk` は不要です。
>
> - **オンラインサービス**（例：ErisPulse ワークベンチ）は、インストールは不要で、ウェブページを開いてログインするだけで使用できます。

---

## 推奨モジュール

### ErisPulse-Dashboard：ブラウザ内の管理パネル

サーバーにロボットを常駐させている場合、モジュールの起動・停止、設定の変更、ログの確認などはターミナルにログインする必要がありますか？Dashboard はこれらの機能をブラウザに移し、モジュールの起動・停止、設定の編集、ログの確認、イベントの監視が可能になります。他のモジュールは、サイドバーにカスタムウィンドウを登録でき、管理ページを一箇所に集めることができます。

```bash
epsdk install Dashboard
```

ドキュメント：[Dashboard の使用とウィンドウ登録](dashboard.md) ｜ プロジェクトページ：[PyPI](https://pypi.org/project/ErisPulse-Dashboard/)

### ErisPulse-Cron：定期実行

毎日自動でサインインのリマインダーを送信したり、Cron 表現式で周期的なタスクを実行したり、数分ごとにデータをポーリングしたいですか？Cron は一回限りのタスク、間隔ごとのタスク、Cron 表現式によるタスクの 3 種類を提供し、コールバックに引数を渡すことができます。SQLite で永続化（再起動してもタスクが失われません）。

```bash
epsdk install Cron
```

ドキュメント：[Cron 定期実行](cron.md) ｜ プロジェクトページ：[GitHub](https://github.com/wsu2059q/ErisPulse-Cron)

### ErisPulse-QvQChat：汎用エージェント

グループ内で単なるキーワード応答ではなく、実用的な AI ヘルパーを導入したいですか？QvQChat は汎用エージェントです：ツールのループでメッセージの送受信、コード実行、コンピュータ操作、画像生成、音声、MCP、サブエージェントをカバーし、ストリーミング対話とツールの連続実行が可能です。内蔵の Dashboard ウィンドウも備えています。さらに、QvQStalker（会話を傍受）、QvQMemes（絵文字）、QvQCompanion（擬人化の伴侶）の 3 つの付属プラグインも用意されています。

```bash
epsdk install ErisPulse-QvQChat
```

ドキュメント：[QvQChat エージェント](qvqchat.md) ｜ プロジェクトページ：[GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-ApiMCP：AI クライアントがロボットを操作できるようにする

Claude Desktop や Claude Code のような MCP をサポートする AI クライアントを使用していますか？ApiMCP はロボットの実行時を 17 個の MCP ツールとして逆方向に公開し、AI が直接メッセージの送受信、インストール済みモジュールの呼び出し、プラットフォームの状態の確認、グループチャットイベントのサブスクライブを行うことができます。ロボットは AI の「手と目」になります。

```bash
epsdk install ErisPulse-ApiMCP
```

ドキュメント：[ApiMCP 使用ガイド](apimcp.md) ｜ プロジェクトページ：[GitHub](https://github.com/wsu2059q/ErisPulse-ApiMCP)

### ErisPulse-Takumi：画像レンダリング

ランキング、戦報、スケジュールカードなど「画像を送る」必要がある場面では、テンプレートを書いて画像にレンダリングし、グループに送信するだけです：HTML / ノードツリー / Jinja / SVG / アニメーション（[takumi-py](https://github.com/BalconyJH/takumi-py) をベース）をサポートし、中英文字体が内蔵されており、すぐに使用できます。

```bash
epsdk install Takumi
```

ドキュメント：[Takumi 画像レンダリング](takumi.md) ｜ プロジェクトページ：[GitHub](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)）

## 公式クライアント（独立プログラム）

### ErisPulse-App：スマホでロボットを直接実行

常時起動しているサーバーがなくても、いつでもインスタンスを作成し、モジュールをインストールして、イベントの流れを確認したいですか？ErisPulse-App は公式の全プラットフォームクライアント（Android / Windows / Linux / macOS）です。ネイティブのインターフェースで複数のロボットインスタンスを作成、実行、管理でき、モジュールストアとイベントビルダーを内蔵しており、**スマートフォンで直接実行**できます。デスクトップのトレイに常駐します。

各プラットフォームのインストーラーはすべて [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) からダウンロードできます。`epsdk` は必要ありません。

ドキュメント：[ErisPulse-Appのインストールと使用方法](app.md)

## 公式オンラインサービス

### ErisPulse ワークベンチ：モジュールストアとホスティングドメインのバックエンド

モジュールをストアに登録したい、`plugin-xxx.erisdev.com` のウェブサイトアドレスをモジュールに割り当てたい、あるいはスクリプトを使ってモジュールを自動的に提出したいですか？ ワークベンチはエコシステムの統合アカウントセンターです。1つのアカウントでモジュールの収録と認証、ホスティングドメインの申請、アクセストークンの生成が可能で、自分のウェブサイトに「ErisPulseアカウントでログイン」をサポートすることもできます。オンラインサービスのみで、**インストールは不要**です。

アクセス：[https://workbench.erisdev.com/](https://workbench.erisdev.com/)

ドキュメント：[ErisPulse ワークベンチ使用ガイド](workbench.md)

---

## 自分のモジュールもここに載せたいですか？

高品質で広く再利用可能な ErisPulse エコシステムモジュールのご推薦を歓迎します。要件は以下の通りです：

1. [PyPI](https://pypi.org/) で公開されており、パッケージ名が `ErisPulse-` で始まること
2. 基本的な README と使用例が提供されていること
3. 積極的にメンテナンスされており、Issue に対応していること

上記の条件を満たすモジュールの作者は、PR を通じてこのディレクトリに `<モジュール名>.md` ドキュメントを追加し、上記のおすすめリストに対応するセクションを補足することができます。