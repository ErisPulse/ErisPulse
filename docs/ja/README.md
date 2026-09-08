# ErisPulse ドキュメント

ErisPulse は、アダプターを通じて異なるプラットフォームと対話することができる拡張可能なマルチプラットフォームメッセージ処理フレームワークであり、柔軟なモジュールシステムを提供して機能拡張を可能にします。

> **初めて使う？** [5 分間で始める](quick-start.md) —— インストールから最初のロボットの実行まで、一連の流れで学べる。

---

## あなたの目的に合わせた学習パス

目的に応じて、対応する学習パスを選択してください。各パスは、浅い内容から深い内容へと順序付けられています。

### 一、ロボットを使いたい

ロボットを動かし、モジュールをインストールし、設定を行う。

| 進捗 | ドキュメント | 説明 |
|------|--------------|------|
| **① 上手く使う** | [5 分間で始める](quick-start.md) | インストール、初期化、実行 —— すべての出発点 |
| App で直接インストール | [ErisPulse-App クライアント](ecosystem/app.md) | 公式の全プラットフォーム対応クライアント：スマホ / PC 用グラフィカルインターフェースで直接実行と管理、ターミナル不要 |
| ② 深入る | [最初のロボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラを書く |
| ③ 概念を理解する | [基本概念](getting-started/basic-concepts.md) | アダプター / モジュール / イベントの設計を理解する |
| ④ 実践する | [よくあるタスクの例](getting-started/common-tasks.md) | ストレージ、定期タスク、権限制御 |
| 参考 | [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォーム特性ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖 / QQ / Telegram…）の違い |

### 二、モジュール / アダプターを開発したい

ErisPulse 用に配布可能な拡張機能を開発する。

| タイプ | 入門 | 進階 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発入門](developer-guide/modules/getting-started.md) | [コア概念](developer-guide/modules/core-concepts.md) · [Event パッケージ](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプター開発** | [アダプター開発入門](developer-guide/adapters/getting-started.md) | [コア概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベント変換器](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術標準** | [標準規格概要](standards/README.md) | アダプター開発時に遵守すべき [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [API 応答](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) 規格 |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品を PyPI やモジュールストアに公開する |

### 三、内部の仕組みを理解したい

フレームワークの内部がどのように動作しているかを理解する。

| ドキュメント | 説明 |
|--------------|------|
| [アーキテクチャ概要](architecture.md) | 可視化された図：コアアーキテクチャ、初期化プロセス、イベント処理、ライフサイクル、モジュールロード戦略（`activate_on` イベント駆動による遅延起動）、ローカルプラグインフォルダとモジュールのホットリロードアーキテクチャ（すべてのモジュールソースに対応） |
| [起動プロセスと手動制御](advanced/startup.md) | 起動プロセスの分解、各段階の手動駆動、ロード失敗の診断 |
| [イベントシステム](api-reference/event-system.md) | 5つのイベントタイプの完全な API |
| [アダプターシステム](api-reference/adapter-system.md) | アダプターの登録、起動 / 停止、API 呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |
| [ライフサイクル管理](advanced/lifecycle.md) · [遅延ロード](advanced/lazy-loading.md) · [ルーティングシステム](advanced/router.md) | 内部サブシステム |
| [スコープ（scope）](advanced/scope.md) | 3次元スコープ制御：モジュールの利用性 / イベントの許可 / 出力アクションの制限（メソッドレベルの細かいルール、バインディング継承 merge を含む） |
| [所有権（owner）システム](advanced/ownership.md) | リソースの所有と自動回収：owner コンテキスト、所有リソースの全景、アンロード時のクリーンアップ、設計の境界とモジュール開発者向けガイド |
| [Conversation 多段対話](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL ビルダー](advanced/sql-builder.md) · [ストアバックエンド](advanced/storage-backends.md) · [HTTP クライアント](advanced/http-client.md) · [国際化](advanced/i18n.md) | 進階ツール |

### 四、エコシステムと公式クライアント

公式クライアント + 必要に応じてインストール可能なエコシステムモジュール（フレームワークに内蔵されていない機能）。

| ドキュメント | 説明 |
|--------------|------|
| [エコシステム概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、なぜこれらが内蔵機能ではないのか |
| [ErisPulse-App](ecosystem/app.md) | 公式の全プラットフォーム対応クライアント（Android / Windows / Linux / macOS）：ネイティブインターフェースで複数のインスタンスを管理、**スマホで直接実行**、デスクトップトレイに常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理パネル + ウィンドウ登録 API（モジュールはサイドバーに独自ページを登録可能） |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、内蔵中英文字体） |

### 五、ErisPulse に貢献したい

フレームワークをより良くする。

| ドキュメント | 説明 |
|--------------|------|
| [ErisPulse への貢献](contributing/README.md) | 貢献方法の概要：ドキュメント / i18n / バグ / モジュール / アダプター |
| [初めての貢献](contributing/first-contribution.md) | Fork から Pull Request の提出まで |

---

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