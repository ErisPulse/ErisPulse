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