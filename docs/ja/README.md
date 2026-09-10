# ErisPulse ドキュメント

ErisPulse は、アダプターを通じて異なるプラットフォームと対話することができる拡張可能なマルチプラットフォームメッセージ処理フレームワークであり、柔軟なモジュールシステムを提供して機能拡張を可能にします。

> **初めて使う？** [5 分間で始める](quick-start.md) —— インストールから最初のロボットの実行まで、一連の流れで学べる。

---

## あなたの進むべき道を選ぶ

目的に応じて、対応する学習経路を選択してください。各経路は、浅いところから深いところへと順に並んでいます。

### 一、私はロボットを使いたい

ロボットを動かし、モジュールをインストールし、設定を行う。

| 進捗 | ドキュメント | 説明 |
|------|------|------|
| **① 初心者向け** | [5分で始める](docs/ja/quick-start.md) | インストール、初期化、実行 —— すべての出発点 |
| App 直接インストール | [ErisPulse-App クライアント](ecosystem/app.md) | 公式の全プラットフォーム対応クライアント：スマートフォン / パソコンのグラフィカルインターフェースで直接実行と管理、ターミナル不要 |
| ② 深入り学習 | [最初のロボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラの作成 |
| ③ 概念理解 | [基本概念](getting-started/basic-concepts.md) | アダプタ/モジュール/イベントの設計を理解する |
| ④ 実践 | [一般的なタスクの例](getting-started/common-tasks.md) | ストレージ、定期タスク、権限制御 |
| 参考 | [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォーム特徴ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖/QQ/Telegram…）の違い |

### 二、私はモジュール / アダプタを開発したい

ErisPulse 用に配布可能な拡張機能を開発する。

| タイプ | 入門 | 進階 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発の入門](developer-guide/modules/getting-started.md) | [コア概念](developer-guide/modules/core-concepts.md) · [Event 包装クラス](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプタ開発** | [アダプタ開発の入門](developer-guide/adapters/getting-started.md) | [コア概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベント変換器](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術基準** | [基準規格の概要](standards/README.md) | アダプタ開発に必須の [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信方法](standards/send-method-spec.md) · [API レスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) 規格 |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品を PyPI とモジュールストアに公開する |

### 三、私は内部の仕組みを深く理解したい

フレームワークの内部がどのように動作するかを理解する。

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャの概要](architecture.md) | 可視化された図：コアアーキテクチャ、初期化プロセス、イベント処理、ライフサイクル、モジュールのロード戦略（`activate_on` イベント駆動による遅延起動含む）、ローカルプラグインフォルダとモジュールのホットリロードアーキテクチャ（全モジュールソースに対応） |
| [起動プロセスと手動制御](advanced/startup.md) | 起動プロセスの分解、各段階の手動駆動、ロード失敗の診断 |
| [イベントシステム](api-reference/event-system.md) | 5つのイベントタイプの完全な API |
| [アダプタシステム](api-reference/adapter-system.md) | アダプタの登録、起動/停止、API 呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |
| [ライフサイクル管理](advanced/lifecycle.md) · [遅延ロード](advanced/lazy-loading.md) · [ルーティングシステム](advanced/router.md) | 内部サブシステム |
| [スコープ（scope）](advanced/scope.md) | 3次元スコープ制御：モジュールの利用可能性 / イベントのアクセス制限 / 出力アクションの制限（メソッドレベルの細かいルール、バインディング継承 merge 含む） |
| [所有権（owner）システム](advanced/ownership.md) | リソースの所有と自動回収：owner コンテキスト、所有リソースの全体像、アンロード時のクリーンアップ、設計の境界とモジュール開発者ガイド |
| [対話セッションシステム](advanced/interaction.md) | wait_reply の全解説、セッションタイマー（remind/escalate）、多重待ち（select）、セッションの排他リース、受信箱、メッセージトランザクション、ルート追跡 |
| [モジュール間通信](advanced/module-communication.md) | RPC プロトコル化（module.call）、meta.services サービス契約とディレクトリ、特定のイベント emit(to=)、クールスタートの再再生、イベントの冪等性と重複除去 |
| [Conversation 多段対話](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL ビルダー](advanced/sql-builder.md) · [ストレージバックエンド](advanced/storage-backends.md) · [HTTP クライアント](advanced/http-client.md) · [国際化](advanced/i18n.md) | 高度なツール |

### 四、エコシステムと公式クライアント

公式クライアント + 必要に応じてインストール、すぐに使えるエコシステムモジュール（フレームワークの内蔵機能ではありません）。

| ドキュメント | 説明 |
|------|------|
| [エコシステムの概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、なぜこれが内蔵機能ではないのか |
| [ErisPulse-App](ecosystem/app.md) | 公式の全プラットフォーム対応クライアント（Android / Windows / Linux / macOS）：ネイティブインターフェースで複数のインスタンスを管理、**スマートフォンで直接実行**、デスクトップのトレイに常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理パネル + ウィンドウ登録 API（モジュールはサイドバーにカスタムページを登録可能） |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、内蔵中英文字体） |

### 五、私は ErisPulse に貢献したい

フレームワークをより良くする

| ドキュメント | 説明 |
|------|------|
| [ErisPulse への貢献](contributing/README.md) | 貢献の方法の概要：ドキュメント / i18n / Bug / モジュール / アダプタ |
| [初めての貢献](contributing/first-contribution.md) | fork から PR 提出まで |

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