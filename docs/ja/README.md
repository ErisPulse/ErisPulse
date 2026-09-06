# ErisPulse ドキュメント

ErisPulse は、アダプターを使用してさまざまなプラットフォームと相互作用できる、拡張可能なマルチプラットフォームメッセージ処理フレームワークであり、機能拡張のために柔軟なモジュールシステムを提供します。

> **初めてご利用ですか？** [5分で始める](docs/ja/quick-start.md) を直接参照してください —— インストールから最初のロボットの実行まで、一連の流れでご案内します。

---

各言語のドキュメントへのリンク:

- [English](README.en.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

## 学習パスの選択

目的に応じて、対応する学習パスを選択してください。各パスは、基本から応用へと順序づけられています。

### 一、ロボットを使いたい

ロボットを起動し、モジュールをインストール、設定を行います。

| 進度 | ドキュメント | 説明 |
|------|------|------|
| **① 初心者向け** | [5 分間クイックスタート](docs/ja/quick-start.md) | インストール、初期化、実行 —— 唯一のスタート地点 |
| App 直接インストール | [ErisPulse-App クライアント](ecosystem/app.md) | 公式の全プラットフォーム対応クライアント：スマホ / PC でグラフィカルインターフェースで直接実行・管理、ターミナル不要 |
| ② 深入り | [最初のロボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラを書く |
| ③ 概念 | [基本概念](getting-started/basic-concepts.md) | アダプタ/モジュール/イベントの設計を理解する |
| ④ 実践 | [よくあるタスクの例](getting-started/common-tasks.md) | ストレージ、定時タスク、権限制御 |
| 参考 | [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォーム特徴ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖/QQ/Telegram…）の違い |

### 二、モジュール / アダプタを開発したい

ErisPulse 用に配布可能な拡張機能を開発します。

| タイプ | 入門 | 応用 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発の入門](developer-guide/modules/getting-started.md) | [コア概念](developer-guide/modules/core-concepts.md) · [Event 包装クラス](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプタ開発** | [アダプタ開発の入門](developer-guide/adapters/getting-started.md) | [コア概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベント変換器](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術規格** | [規格の概要](standards/README.md) | アダプタ開発に必須の [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信方法](standards/send-method-spec.md) · [APIレスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) 規格 |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品を PyPI とモジュールストアに公開する |

### 三、内部原理を深く理解したい

フレームワークの内部動作を理解します。

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャ概要](architecture.md) | 可視化図表：コアアーキテクチャ、初期化フロー、イベント処理、ライフサイクル、モジュールのロード戦略（`activate_on` イベント駆動による遅延起動含む）、ローカルプラグインフォルダとモジュールのホットリロードアーキテクチャ（全てのモジュールソースに対応） |
| [起動フローと手動制御](advanced/startup.md) | 起動フローの分解、各段階の手動駆動、ロード失敗の診断 |
| [イベントシステム](api-reference/event-system.md) | 5 大イベントの完全な API |
| [アダプタシステム](api-reference/adapter-system.md) | アダプタの登録、起動・停止、API 呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |
| [ライフサイクル管理](advanced/lifecycle.md) · [遅延ロード](advanced/lazy-loading.md) · [ルーティングシステム](advanced/router.md) | 内部サブシステム |
| [スコープ（scope）](advanced/scope.md) | 3 次元スコープ制御：モジュールの可用性 / イベントのアクセス制限 / 出力アクションの制限（メソッドレベルの細粒度ルール、バインディングの継承 merge 含む） |
| [所有権（owner）システム](advanced/ownership.md) | リソースの所有権と自動リサイクル：owner コンテキスト、所有リソースの全体像、アンロード時のクリーンアップ、設計境界とモジュール開発者向けガイド |
| [Conversation 多段会話](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL ビルダー](advanced/sql-builder.md) · [HTTP クライアント](advanced/http-client.md) · [国際化](advanced/i18n.md) | 高度なツール |

### 四、エコシステムと公式クライアント

公式クライアント + 必要に応じてインストール可能なエコシステムモジュール（フレームワーク内蔵機能ではありません）。

| ドキュメント | 説明 |
|------|------|
| [エコシステム概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、なぜこれらの機能が内蔵されていないのか |
| [ErisPulse-App](ecosystem/app.md) | 公式の全プラットフォーム対応クライアント（Android / Windows / Linux / macOS）：ネイティブインターフェースで複数インスタンスを管理、**スマホで直接実行**、デスクトップのトレイに常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理パネル + ウィンドウ登録 API（モジュールはサイドバーに独自ページを登録可能） |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、内蔵中英文字体） |

### 五、ErisPulse に貢献したい

フレームワークをより良くする

| ドキュメント | 説明 |
|------|------|
| [ErisPulse への貢献](contributing/README.md) | 貢献方法の概要：ドキュメント / i18n / バグ / モジュール / アダプタ |
| [初めての貢献](contributing/first-contribution.md) | fork から PR 提出まで |

## 開発方法

ErisPulse は以下の 2 つの開発方法をサポートしています：

- **モジュール開発（推奨）**：独立したモジュールパッケージを作成し、パッケージマネージャーでインストールすることで、配布と管理が容易になります。
- **埋め込み開発**：プロトタイプ作成に適した、プロジェクト内で直接プロセッサを記述します。詳しくは [クイックスタート](docs/ja/quick-start.md) を参照してください。

言語切り替え行がある場合、各言語名は `` | `` で区切られ、[**Label**](file) のような形式は使用しないようにしてください。

## その他

- [ドキュメントスタイルガイド](styleguide/docstring.md) — ドキュメントを貢献する際の作成規約
- [ErisPulse への貢献](contributing/README.md) — プロジェクトの共同構築に参加するための入り口
- [AI支援開発](ai-support/README.md) — AIプログラミングアシスタントで使用するプロジェクトのプロンプトを入手する

## ヘルプの取得

- GitHub リポジトリ: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題報告: Issue を送信
- 技術的な議論: Discussions を確認

docs/ja/getting-help.md

## 関連リンク

- [OneBot12 標準](https://12.onebot.dev/)
- [云湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)