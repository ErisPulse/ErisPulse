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