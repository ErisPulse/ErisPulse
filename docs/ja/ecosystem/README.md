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