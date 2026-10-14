# ErisPulse ドキュメント

ErisPulse は、アダプターを通じて異なるプラットフォームと対話することができる拡張可能なマルチプラットフォームメッセージ処理フレームワークであり、柔軟なモジュールシステムを提供して機能拡張を可能にします。

> **初めて使う？** [5 分間で始める](quick-start.md) —— インストールから最初のロボットの実行まで、一連の流れで学べる。

---

## 学習の道筋を選択する

目的に応じて、適切な学習の道筋を選択してください。各道筋は、基礎から応用へと順序づけられています。

> [!IMPORTANT]
> **すべてのドキュメントを読む必要はありません。** 大多数の開発者は、**L1コアの5つの記事**（約1〜2時間）を順に読むだけで、90%の機能を独自に開発できます。残りのドキュメントは、特定のシナリオに応じて必要なときに参照する資料です。各記事の冒頭には「この記事を読む必要があるのはいつか」が明記されています。
>
> **L1コアの5つの記事**：[モジュール開発入門](developer-guide/modules/getting-started.md) → [基本概念](getting-started/basic-concepts.md) → [Event 包装クラス](developer-guide/modules/event-wrapper.md) → [設定ファイルの説明](user-guide/configuration.md) → [例外のキャッチ](advanced/errors.md)
>
> アダプター作者は別途：[アダプター開発入門](developer-guide/adapters/getting-started.md) → [イベント変換器](developer-guide/adapters/converter.md) → [SendDSL 詳解](developer-guide/adapters/send-dsl.md)

### 一、私はロボットを使いたい

ロボットを起動し、モジュールをインストールし、設定を行う。

| 進捗 | ドキュメント | 説明 |
|------|------|------|
| **① 上手く使う** | [5分で始める](quick-start.md) | インストール、初期化、実行 —— 唯一の入門 |
| App 直接インストール | [ErisPulse-App クライアント](ecosystem/app.md) | 公式の全プラットフォームクライアント：スマートフォン / PC グラフィカルインターフェースで直接実行・管理、ターミナル不要 |
| ② 深く学ぶ | [最初のロボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラを書く |
| ③ 概念を理解する | [基本概念](getting-started/basic-concepts.md) | アダプター / モジュール / イベントの設計を理解する |
| ④ 実践する | [よくあるタスクの例](getting-started/common-tasks.md) | ストレージ、スケジュールタスク、権限制御 |
| 参考 | [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォーム特徴ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖 / QQ / Telegram…）の違い |

### 二、私はモジュール / アダプターを開発したい

ErisPulse 用に配布可能な拡張機能を開発する。

| タイプ | 入門 | 応用 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発入門](developer-guide/modules/getting-started.md) | [コア概念](developer-guide/modules/core-concepts.md) · [Event 包装クラス](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプター開発** | [アダプター開発入門](developer-guide/adapters/getting-started.md) | [コア概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベント変換器](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術規格** | [規格の概要](standards/README.md) | アダプター開発に必須の [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [APIレスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) 規格 |
| **テストとトラブルシューティング** | [モジュールテスト（ErisPulse-Testing）](developer-guide/testing.md) | ディスパッチの決定プロセス、コマンドがなぜトリガーされないかのトラブルシューティング |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品を PyPI とモジュールストアに公開する |

### 三、私は内部の仕組みを深く理解したい

フレームワークの内部がどのように動作するかを理解する。

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャ概要](architecture.md) | 可視化図：コアアーキテクチャ、初期化プロセス、イベント処理、ライフサイクル、モジュールのロード戦略（`activate_on` イベント駆動の遅延起動を含む）、ローカルプラグインフォルダとモジュールのホットリロードアーキテクチャ（すべてのモジュールソースに対応） |
| [起動プロセスと手動制御](advanced/startup.md) | 起動プロセスの分解、各ステップの手動駆動、ロード失敗の診断 |
| [イベントシステム](api-reference/event-system.md) | 5つのイベントカテゴリの完全なAPI |
| [アダプターシステム](api-reference/adapter-system.md) | アダプターの登録、起動 / 停止、APIの呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |
| [ライフサイクル管理](advanced/lifecycle.md) · [遅延ロード](advanced/lazy-loading.md) · [ルーティングシステム](advanced/router.md) | 内部サブシステム |
| [接続プールとブロードキャスト](advanced/connections.md) · [セッション受信箱](advanced/transcript.md) | 接続を一等資源として扱う：ブロードキャスト / グループ / モジュール間のメッセージの共有と再利用、接続プールの確認；メッセージの記録保持戦略と実行時の上書き |
| [スコープ（scope）](advanced/scope.md) | 3次元のスコープ制御：モジュールの可用性 / イベントの許可 / 出力アクションの制限（メソッドレベルの細かいルール、バインディングの継承 merge を含む） |
| [所有権（owner）システム](advanced/ownership.md) | リソースの所有と自動回収：ownerコンテキスト、所有リソースの全貌、アンロード時のクリーンアップ、設計の境界とモジュール作者のガイド |
| [シャドウモジュールとグレーディング](advanced/shadow.md) | モジュールの新バージョンを別ownerとして並行実行：5つの隔離ゲート、動作のdiff対比、promoteによる正式化と失敗時のロールバック |
| [インタラクティブセッションシステム](advanced/interaction.md) | wait_replyの全解説、セッションタイマー（remind/escalate）、マルチウェイト（select）、セッションの排他リース、受信箱、メッセージトランザクション、トラッキング |
| [モジュール間通信](advanced/module-communication.md) | RPCプロトコル化（module.call）、meta.servicesサービス契約とディレクトリ、特定のイベントemit(to=)、コールドスタートの再再生、イベントの冪等性と重複除去 |
| [Conversation 多輪対話](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL ビルダー](advanced/sql-builder.md) · [ストレージバックエンド](advanced/storage-backends.md) · [HTTPクライアント](advanced/http-client.md) · [国際化](advanced/i18n.md) | 高度なツール |

### 四、エコシステムと公式クライアント

公式クライアント + 必要に応じてインストール可能なエコシステムモジュール（フレームワークの内蔵機能ではない）

| ドキュメント | 説明 |
|------|------|
| [エコシステム概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、なぜこれらの機能が内蔵されていないか |
| [ErisPulse-App](ecosystem/app.md) | 公式の全プラットフォームクライアント（Android / Windows / Linux / macOS）：ネイティブインターフェースで複数のインスタンスを管理、**スマートフォンで直接実行**、デスクトップのトレイに常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web管理パネル + 視窗登録API（モジュールはサイドバーに独自のページを登録できる） |
| [ErisPulse-Cron](ecosystem/cron.md) | タイマーのスケジューラーモジュール：1回限り / 間隔 / Cron式、コールバックに引数を渡す、SQLiteによる永続化、他のモジュールがタイマーのコールバックを委託できる |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、内蔵の中英文字体） |

### 五、私はErisPulseに貢献したい

フレームワークをより良くする

| ドキュメント | 説明 |
|------|------|
| [ErisPulseに貢献する](contributing/README.md) | 貢献の方法の概要：ドキュメント / i18n / バグ / モジュール / アダプター |
| [初めての貢献](contributing/first-contribution.md) | forkからPRの提出まで |

## 開発方法

ErisPulse は以下の2つの開発方法をサポートしています：

- **モジュール開発（推奨）**：独立したモジュールパッケージを作成し、パッケージマネージャーでインストールして管理します。配布や管理が容易です。
- **埋め込み開発**：プロジェクト内で直接ハンドラを書く方法。迅速なプロトタイプ開発に適しています。詳しくは [5 分間で始める](quick-start.md) を参照してください。

## その他

- [ドキュメントスタイルガイド](styleguide/docstring.md) — ドキュメントを貢献する際の書式規則
- [ErisPulse への貢献](contributing/README.md) — プロジェクトに参加するための入口
- [AI による開発支援](ai-support/README.md) — AI プログラミングアシスタント用のプロジェクトのプロンプト

## ヘルプを求める

- GitHub リポジトリ：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問い合わせ / バグ報告：Issue を作成
- 技術的な議論：Discussions を確認

## 関連リンク

- [OneBot12 標準](https://12.onebot.dev/)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)