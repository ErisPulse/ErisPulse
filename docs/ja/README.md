# ErisPulse ドキュメント

ErisPulse は、アダプターを介して異なるプラットフォームと対話できる拡張性のあるマルチプラットフォームメッセージ処理フレームワークであり、機能拡張に柔軟なモジュールシステムを提供します。

> **初めてご利用ですか？** [5分で始める](docs/ja/quick-start.md) —— インストールから最初のロボットの実行まで、一連の流れでご案内します。

---

## 道路を選択する

目的に応じて、対応する学習経路を選択してください。各経路は、浅いところから深いところへと順序付けられています。

### 一、ロボットを使いたい

ロボットを動かし、モジュールをインストールし、設定を行う。

| 進捗 | ドキュメント | 説明 |
|------|------|------|
| **① 初心者向け** | [5 分間で始める](docs/ja/quick-start.md) | インストール、初期化、実行 —— 唯一の出発点 |
| App 直接インストール | [ErisPulse-App クライアント](ecosystem/app.md) | 公式の全プラットフォーム対応クライアント：スマホ / PC 用グラフィカルインターフェースで直接実行と管理、ターミナル不要 |
| ② 深入り学習 | [最初のロボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラの作成 |
| ③ 概念理解 | [基本概念](getting-started/basic-concepts.md) | アダプター / モジュール / イベントの設計を理解 |
| ④ 実践 | [一般的なタスク例](getting-started/common-tasks.md) | ストレージ、定期タスク、権限制御 |
| 参考 | [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォーム特徴ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖 / QQ / Telegram…）の違い |

### 二、モジュール / アダプターを開発したい

ErisPulse 用に配布可能な拡張機能を開発する。

| タイプ | 入門 | 進階 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発入門](developer-guide/modules/getting-started.md) | [コアコンセプト](developer-guide/modules/core-concepts.md) · [Event 包装クラス](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプター開発** | [アダプター開発入門](developer-guide/adapters/getting-started.md) | [コアコンセプト](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベント変換器](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術基準** | [基準仕様概要](standards/README.md) | アダプター開発に必須の [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [API 応答](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) 規格 |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品を PyPI とモジュールストアに公開する |

### 三、原理を深く理解したい

フレームワークの内部がどのように動作するかを理解する。

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャ概要](architecture.md) | 可視化図：コアアーキテクチャ、初期化プロセス、イベント処理、ライフサイクル、モジュールロード戦略（`activate_on` イベント駆動による遅延起動を含む）、ローカルプラグインフォルダとモジュールのホットリロードアーキテクチャ（すべてのモジュールソースに対応） |
| [起動プロセスと手動制御](advanced/startup.md) | 起動フローの分解、各段階の手動駆動、ロード失敗の診断 |
| [イベントシステム](api-reference/event-system.md) | 5 大イベントの完全な API |
| [アダプターシステム](api-reference/adapter-system.md) | アダプターの登録、起動 / 停止、API 呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |
| [ライフサイクル管理](advanced/lifecycle.md) · [遅延ロード](advanced/lazy-loading.md) · [ルーティングシステム](advanced/router.md) | 内部サブシステム |
| [スコープ (scope)](advanced/scope.md) | 3 次元スコープ制御：モジュールの可用性 / イベントのアクセス制限 / 出力アクションの制限（メソッドレベルの細かいルール、バインディング継承 merge を含む） |
| [所有権 (owner) システム](advanced/ownership.md) | リソースの所有と自動回収：owner コンテキスト、所有リソースの全体像、アンロードクリーンアップシーケンス、設計境界とモジュール作者のガイド |
| [Conversation 多段対話](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL ビルダー](advanced/sql-builder.md) · [HTTP クライアント](advanced/http-client.md) · [国際化](advanced/i18n.md) | 進階ツール |

### 四、エコシステムと公式クライアント

公式クライアント + 必要に応じてインストール可能なエコシステムモジュール（フレームワークの内蔵機能ではない）。

| ドキュメント | 説明 |
|------|------|
| [エコシステム概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、なぜこれらが内蔵機能ではないのか |
| [ErisPulse-App](ecosystem/app.md) | 公式の全プラットフォーム対応クライアント（Android / Windows / Linux / macOS）：ネイティブインターフェースで複数のインスタンスを管理、**スマホで直接実行**、デスクトップトレイに常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理パネル + ウィンドウ登録 API（モジュールはサイドバーに独自ページを登録可能） |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、内蔵中英文字体） |

### 五、ErisPulse に貢献したい

フレームワークをより良くする

| ドキュメント | 説明 |
|------|------|
| [ErisPulse への貢献](contributing/README.md) | 貢献方法の概要：ドキュメント / i18n / Bug / モジュール / アダプター |
| [初めての貢献](contributing/first-contribution.md) | fork から PR 提出まで |

## 開発方法

ErisPulse では、以下の 2 種類の開発方法をサポートしています。

- **モジュール開発（推奨）**：独立したモジュールパッケージを作成し、パッケージマネージャーでインストールすることで、パッケージの配布や管理が容易になります。
- **埋め込み開発**：プロトタイプを迅速に構築する場合に、プロジェクト内に直接プロセッサを記述します。詳しくは [クイックスタート](docs/ja/quick-start.md) をご参照ください。

## その他

- [ドキュメントスタイルガイド](styleguide/docstring.md) — ドキュメントを貢献する際の作成規範
- [ErisPulse への貢献](contributing/README.md) — プロジェクトへの共同構築への入り口
- [AI支援開発](ai-support/README.md) — AIプログラミングアシスタント用のプロジェクトプロンプトを入手

## ヘルプの取得

- GitHub リポジトリ: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題報告: Issue を作成
- 技術的な議論: Discussions を確認

## 関連リンク

- [OneBot12 標準](https://12.onebot.dev/)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)