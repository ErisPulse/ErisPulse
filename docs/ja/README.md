# ErisPulse ドキュメント

ErisPulse は、アダプタを通じて異なるプラットフォームと対話することができる拡張可能なマルチプラットフォームのメッセージ処理フレームワークであり、機能拡張のための柔軟なモジュールシステムを提供します。

> **初めて使う？** [5分で始める](docs/ja/quick-start.md)を直接見てください —— インストールから最初のロボットの実行まで、一連の流れを完結します。

---

## あなたの学習経路を選択してください

目的に応じて、対応する学習経路を選んでください。各経路は、浅いものから深いものへと並べられています。

### 一、ロボットを使いたい

ロボットを起動し、モジュールをインストールし、設定を行います。

| 進捗 | ドキュメント | 説明 |
|------|------|------|
| **① 上手** | [5分で始める](docs/ja/quick-start.md) | インストール、初期化、実行 —— 唯一の出発点 |
| ② 深入 | [最初のロボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラの作成 |
| ③ 概念 | [基本概念](getting-started/basic-concepts.md) | アダプタ/モジュール/イベントの設計を理解する |
| ④ 実践 | [一般的なタスクの例](getting-started/common-tasks.md) | ストレージ、定期タスク、権限制御 |
| 参考 | [設定ファイルの説明](user-guide/configuration.md) · [CLIコマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォーム特徴ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖/QQ/Telegram…）の違い |

### 二、モジュール / アダプタを開発したい

ErisPulse 用に配布可能な拡張機能を開発します。

| タイプ | 入門 | 進階 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発入門](developer-guide/modules/getting-started.md) | [基本概念](developer-guide/modules/core-concepts.md) · [Event ラッパー](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプタ開発** | [アダプタ開発入門](developer-guide/adapters/getting-started.md) | [基本概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベント変換器](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術規格** | [規格概要](standards/README.md) | アダプタ開発で遵守すべき [セッション型](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [APIレスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) 規格 |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) |作品を PyPI とモジュールストアに公開する方法 |

### 三、原理を深く理解したい

フレームワークの内部がどのように動作しているかを理解します。

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャ概要](architecture.md) | 可視化された図表：コアアーキテクチャ、初期化フロー、イベント処理、ライフサイクル |
| [起動プロセスと手動制御](advanced/startup.md) | 起動経路の分解、各段階の手動駆動、読み込み失敗の診断 |
| [イベントシステム](api-reference/event-system.md) | 5つのイベントタイプの完全な API |
| [アダプタシステム](api-reference/adapter-system.md) | アダプタの登録、起動/停止、APIの呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |
| [ライフサイクル管理](advanced/lifecycle.md) · [遅延ロード](advanced/lazy-loading.md) · [ルーティングシステム](advanced/router.md) | 内部のサブシステム |
| [Conversation 多段対話](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQLビルダー](advanced/sql-builder.md) · [HTTPクライアント](advanced/http-client.md) · [国際化](advanced/i18n.md) | 進階ツール |

### 四、推奨エコシステムモジュール

必要に応じてインストールし、すぐに使える **サードパーティのコミュニティモジュール**（フレームワークの内蔵機能ではありません）。

| ドキュメント | 説明 |
|------|------|
| [エコシステムモジュール概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、なぜこれらが内蔵機能ではないかを理解する |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web管理パネル + ウィンドウ登録API（モジュールはサイドバーにカスタムページを登録可能） |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、内蔵中英文字体） |

### 五、ErisPulse に貢献したい

フレームワークをより良くする

| ドキュメント | 説明 |
|------|------|
| [ErisPulse への貢献](contributing/README.md) | 貢献方法の概要：ドキュメント / i18n / Bug / モジュール / アダプタ |
| [初めての貢献](contributing/first-contribution.md) | fork から PR 提出までの流れ |

---

## 開発方法

ErisPulse は2種類の開発方法をサポートしています：

- **モジュール開発（推奨）**：独立したモジュールパッケージを作成し、パッケージマネージャーでインストールすることで、配布や管理が容易になります。
- **埋め込み開発**：プロジェクト内で直接ハンドラを記述する方法で、迅速なプロトタイプ作成に適しています。詳しくは [5分で始める](docs/ja/quick-start.md) を参照してください。

## その他

- [ドキュメントスタイルガイド](styleguide/docstring.md) — ドキュメントを貢献する際の書式規則
- [ErisPulse への貢献](contributing/README.md) — プロジェクトの共同開発への入口
- [AI支援開発](ai-support/README.md) — AIプログラミングアシスタント用のプロジェクトプロンプトを取得する

## ヘルプを得る

- GitHub リポジトリ: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題報告: Issue を作成
- 技術的な議論: Discussions を参照

## 関連リンク

- [OneBot12 標準](https://12.onebot.dev/)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Русский](README.ru.md)