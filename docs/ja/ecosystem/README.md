# エコシステムモジュール

ErisPulse フレームワーク自体は、イベントシステム、モジュールシステム、設定、ルーティング、ログなどのコア機能のみを提供し、**GUI、画像レンダリング、可視化などの「重い」機能は内蔵していません**。これらの機能は、コミュニティが維持する**サードパーティモジュール**によって提供され、必要に応じてインストールできます。

> [!IMPORTANT]
> 本セクションのドキュメントは、インストール方法が異なる2種類に分かれています：
>
> - **モジュール**（例：Dashboard / Takumi）は、`epsdk install` を使用してインストールします：
>
>   ```bash
>   epsdk install <モジュール名>
>   ```
>
> - **独立プログラム**（例：ErisPulse-App クライアント）は、対応する GitHub Releases から直接ダウンロードしてインストールします。`epsdk` は不要です。
>

---

## 推荐モジュールと公式クライアント

| 項目 | タイプ | 用途 | ドキュメント |
|------|------|------|------|
| [ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) | 公式クライアント | 公式の全プラットフォームクライアント（Android / Windows / Linux / macOS）：ネイティブインターフェースで複数のインスタンスを作成 / 実行 / 管理、モジュールストアとイベントビルダーを内蔵；**スマートフォンで直接実行可能**、デスクトップのトレイに常駐 | [ErisPulse-App インストールと使用方法](app.md) |
| [ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) | モジュール | Web管理パネル：モジュールの起動 / 停止、設定編集、ログの表示、イベントの監視；他のモジュールがサイドバーにカスタムウィンドウを登録可能 | [Dashboard の使用方法とウィンドウ登録](dashboard.md) |
| [ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) | モジュール | タイミングタスクスケジューラ：1回限り / 間隔 / Cron式、コールバック引数、SQLiteによる永続化（再起動してもタスクが失われない）、Dashboardウィンドウ管理対応 | [Cron 定時タスク](cron.md) |
| [ErisPulse-QvQChat](https://github.com/wsu2059q/ErisPulse-QvQChat) | モジュール | 一般的なエージェント：ツールループ（メッセージの送受信 / コード実行 / コンピュータ操作 / 画像生成 / 音声 / MCP / 子エージェント）、内蔵のDashboard、ストリーミング対話とツールの連続実行 | [QvQChat エージェント](qvqchat.md) |
| [ErisPulse-Takumi](https://github.com/ccd2s/ErispulseTakumi)（作者 [@ccd2s](https://github.com/ccd2s)） | モジュール | 画像レンダリング：HTML / ノードツリー / Jinja / SVG / アニメーション、[takumi-py](https://github.com/BalconyJH/takumi-py) をベース；内蔵の中英文字体、すぐに使用可能 | [Takumi 画像レンダリング](takumi.md) |

---

## 私も自分のモジュールをここに掲載したい！

優れた、再利用可能な ErisPulse エコシステムのモジュールを推薦していただけます。要件は以下の通りです：

1. [PyPI](https://pypi.org/) に公開済みで、パッケージ名は `ErisPulse-` で始まる
2. 基本的な README と使用例を提供している
3. Issue に対して積極的に対応し、メンテナンスしている

上記条件を満たすモジュールの作者は、本ディレクトリに `<モジュール名>.md` ドキュメントを追加する PR を送信し、本表の「推薦モジュール」に一行追加することができます。