# ErisPulse ドキュメント

ErisPulse は、アダプターを使用してさまざまなプラットフォームと相互作用できる、拡張可能なマルチプラットフォームメッセージ処理フレームワークであり、機能拡張のために柔軟なモジュールシステムを提供します。

> **初めてご利用ですか？** [5分で始める](docs/ja/quick-start.md) を直接参照してください —— インストールから最初のロボットの実行まで、一連の流れでご案内します。

---

各言語のドキュメントへのリンク:

- [English](README.en.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

## あなたの学習経路を選択

あなたの目標に応じて、対応する学習経路を選択してください。各経路は、基本から応用へと順序付けられています。

### 一、ロボットを使いたい

ロボットを起動し、モジュールを装着し、設定を行います。

| 進捗 | ドキュメント | 説明 |
|------|------|------|
| **① 初心者向け** | [5分で始める](docs/ja/quick-start.md) | インストール、初期化、実行 —— 唯一のスタート地点 |
| ② 深入 | [最初のロボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラの作成 |
| ③ 概念 | [基本概念](getting-started/basic-concepts.md) | アダプタ/モジュール/イベントの設計を理解する |
| ④ 実践 | [一般的なタスクの例](getting-started/common-tasks.md) | ストレージ、定期タスク、権限制御 |
| 参考 | [設定ファイルの説明](user-guide/configuration.md) · [CLIコマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォームの特徴ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖/QQ/Telegram…）の違い |

### 二、モジュール/アダプタを開発したい

ErisPulse用に配布可能な拡張機能を開発する。

| タイプ | 入門 | 応用 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発の入門](developer-guide/modules/getting-started.md) | [コアコンセプト](developer-guide/modules/core-concepts.md) · [Eventラッパー](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプタ開発** | [アダプタ開発の入門](developer-guide/adapters/getting-started.md) | [コアコンセプト](developer-guide/adapters/core-concepts.md) · [SendDSLの詳細](developer-guide/adapters/send-dsl.md) · [イベントコンバーター](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術基準** | [標準規格の概要](standards/README.md) | アダプタ開発で遵守すべき [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [APIレスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品をPyPIとモジュールストアに公開する |

### 三、内部原理を深く理解したい

フレームワークの内部がどのように動作するかを理解する。

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャの概要](architecture.md) | 可視化図：コアアーキテクチャ、初期化フロー、イベント処理、ライフサイクル |
| [起動フローと手動制御](advanced/startup.md) | 起動フローの分解、各段階の手動駆動、ロード失敗の診断 |
| [イベントシステム](api-reference/event-system.md) | 5つのイベントカテゴリの完全なAPI |
| [アダプタシステム](api-reference/adapter-system.md) | アダプタの登録、起動・停止、API呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Routerなどの基本機能 |
| [ライフサイクル管理](advanced/lifecycle.md) · [遅延ロード](advanced/lazy-loading.md) · [ルーターシステム](advanced/router.md) | 内部サブシステム |
| [Conversation多段対話](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQLビルダー](advanced/sql-builder.md) · [HTTPクライアント](advanced/http-client.md) · [国際化](advanced/i18n.md) | 応用ツール |

### 四、推奨エコシステムモジュール

必要に応じてインストールし、すぐに使える **サードパーティコミュニティモジュール**（フレームワークの内蔵機能ではありません）。

| ドキュメント | 説明 |
|------|------|
| [エコシステムモジュールの概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、なぜこれが内蔵機能ではないかを理解する |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web管理パネル + ウィンドウ登録API（モジュールはサイドバーにカスタムページを登録可能） |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、内蔵中英文字体） |

### 五、ErisPulseに貢献したい

フレームワークをより良くする

| ドキュメント | 説明 |
|------|------|
| [ErisPulseへの貢献](contributing/README.md) | 貢献方法の概要：ドキュメント / i18n / Bug / モジュール / アダプタ |
| [初めての貢献](contributing/first-contribution.md) | forkからPR提出まで |

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