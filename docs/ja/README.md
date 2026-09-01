# ErisPulse ドキュメント

ErisPulse は、アダプターを介して異なるプラットフォームと対話できる拡張可能なマルチプラットフォームメッセージ処理フレームワークであり、柔軟なモジュールシステムを提供して機能拡張を可能にします。

> **初めて使う？** まずは [5 分鐘のクイックスタート](docs/ja/quick-start.md) を見てください —— インストールから最初のロボットの実行まで、一連の流れを完結します。

---

## あなたの目的に応じた学習経路を選択

目的に応じて、対応する学習経路を選択してください。各経路は、浅い内容から深い内容へと順序付けられています。

### 一、ロボットを使いたい

ロボットを起動し、モジュールをインストールし、設定を行う。

| 進捗 | ドキュメント | 説明 |
|------|--------------|------|
| **① 上手く使う** | [5 分鐘のクイックスタート](docs/ja/quick-start.md) | インストール、初期化、実行 —— 唯一の導入手順 |
| App 直接インストール | [ErisPulse-App クライアント](docs/ja/ecosystem/app.md) | 公式の全プラットフォーム用クライアント：スマホ / PC 用グラフィカルインターフェースで直接実行・管理、ターミナル不要 |
| ② 深入る | [最初のロボットを作成する](docs/ja/getting-started/first-bot.md) | 最初のコマンドハンドラの作成 |
| ③ 概念理解 | [基本概念](docs/ja/getting-started/basic-concepts.md) | アダプター / モジュール / イベントの設計を理解する |
| ④ 実践 | [一般的なタスクの例](docs/ja/getting-started/common-tasks.md) | ストレージ、定期タスク、権限制御 |
| 参考 | [設定ファイルの説明](docs/ja/user-guide/configuration.md) · [CLI コマンド](docs/ja/user-guide/cli-reference.md) · [デプロイガイド](docs/ja/user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォーム特性ガイド](docs/ja/platform-guide/README.md) | 各プラットフォーム（云湖 / QQ / Telegram…）の違い |

### 二、モジュール / アダプターを開発したい

ErisPulse 用に配布可能な拡張機能を開発する。

| タイプ | 入門 | 進階 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発の入門](docs/ja/developer-guide/modules/getting-started.md) | [コアコンセプト](docs/ja/developer-guide/modules/core-concepts.md) · [Event 包装クラス](docs/ja/developer-guide/modules/event-wrapper.md) · [ベストプラクティス](docs/ja/developer-guide/modules/best-practices.md) |
| **アダプター開発** | [アダプター開発の入門](docs/ja/developer-guide/adapters/getting-started.md) | [コアコンセプト](docs/ja/developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](docs/ja/developer-guide/adapters/send-dsl.md) · [イベント変換器](docs/ja/developer-guide/adapters/converter.md) · [ベストプラクティス](docs/ja/developer-guide/adapters/best-practices.md) |
| **技術標準** | [標準規格の概要](docs/ja/standards/README.md) | アダプター開発に必須の [セッションタイプ](docs/ja/standards/session-types.md) · [イベント変換](docs/ja/standards/event-conversion.md) · [送信メソッド](docs/ja/standards/send-method-spec.md) · [API レスポンス](docs/ja/standards/api-response.md) · [リクエスト操作](docs/ja/standards/request-action-spec.md) 規格 |
| **公開** | [公開とモジュールストア](docs/ja/developer-guide/publishing.md) | 作品を PyPI とモジュールストアに公開する方法 |

### 三、フレームワークの内部原理を理解したい

フレームワークの内部がどのように動作するかを理解する。

| ドキュメント | 説明 |
|--------------|------|
| [アーキテクチャの概要](docs/ja/architecture.md) | 可視化された図表：コアアーキテクチャ、初期化プロセス、イベント処理、ライフサイクル、モジュールのロード戦略（`activate_on` イベント駆動の遅延起動を含む）、ローカルプラグインフォルダとホットリロードアーキテクチャ |
| [起動プロセスと手動制御](docs/ja/advanced/startup.md) | 起動の流れの分解、各段階の手動駆動、ロード失敗の診断 |
| [イベントシステム](docs/ja/api-reference/event-system.md) | 5つのイベントタイプの完全な API |
| [アダプターシステム](docs/ja/api-reference/adapter-system.md) | アダプターの登録、起動 / 停止、API 呼び出し |
| [コアモジュール](docs/ja/api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |
| [ライフサイクル管理](docs/ja/advanced/lifecycle.md) · [遅延ロード](docs/ja/advanced/lazy-loading.md) · [ルーティングシステム](docs/ja/advanced/router.md) | 内部サブシステム |
| [統一制御面（scope）](docs/ja/advanced/scope.md) | 5次元の権限制御：モジュールの可用性 / イベントのアクセス制限 / コマンド ACL / テキストフィルタ / パラメータの上書き |
| [Conversation 多輪対話](docs/ja/advanced/conversation.md) · [MessageBuilder](docs/ja/advanced/message-builder.md) · [SQL ビルダー](docs/ja/advanced/sql-builder.md) · [HTTP クライアント](docs/ja/advanced/http-client.md) · [国際化](docs/ja/advanced/i18n.md) | 高度なツール |

### 四、エコシステムと公式クライアント

公式クライアント + 必要に応じてインストール可能なエコシステムモジュール（フレームワークの内包機能ではありません）。

| ドキュメント | 説明 |
|--------------|------|
| [エコシステムの概要](docs/ja/ecosystem/README.md) | エコシステムモジュールのインストール方法、なぜこれらの機能が内包されていないのか |
| [ErisPulse-App](docs/ja/ecosystem/app.md) | 公式の全プラットフォームクライアント（Android / Windows / Linux / macOS）：ネイティブインターフェースで複数のインスタンスを管理、**スマホで直接実行**、デスクトップのトレイに常駐 |
| [ErisPulse-Dashboard](docs/ja/ecosystem/dashboard.md) | Web 管理パネル + ウィンドウ登録 API（モジュールはサイドバーに独自ページを登録可能） |
| [ErisPulse-Takumi](docs/ja/ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、内包された中英文字体） |

### 五、ErisPulse に貢献したい

フレームワークをより良くする。

| ドキュメント | 説明 |
|--------------|------|
| [ErisPulse への貢献](docs/ja/contributing/README.md) | 貢献の方法の概要：ドキュメント / i18n / バグ / モジュール / アダプター |
| [初めての貢献](docs/ja/contributing/first-contribution.md) | fork から PR 提出までの流れ |

---

## 開発方法

ErisPulse は 2 つの開発方法をサポートしています：

- **モジュール開発（推奨）**：独立したモジュールパッケージを作成し、パッケージマネージャーでインストールすることで、配布および管理が容易になります。
- **埋め込み開発**：プロジェクト内で直接ハンドラを記述し、迅速なプロトタイプ作成に適しています。詳しくは [クイックスタート](docs/ja/quick-start.md) を参照してください。

## その他

- [ドキュメントスタイルガイド](docs/ja/styleguide/docstring.md) — ドキュメントを貢献する際の記述規範
- [ErisPulse への貢献](docs/ja/contributing/README.md) — プロジェクトの共同構築の入口
- [AI支援開発](docs/ja/ai-support/README.md) — AIプログラミングアシスタント用のプロジェクトプロンプト

## ヘルプを得る

- GitHub リポジトリ: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題報告: Issue を作成
- 技術的な議論: Discussions を確認

## 関連リンク

- [OneBot12 標準](https://12.onebot.dev/)
- [云湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)