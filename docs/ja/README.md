# ErisPulse ドキュメント

ErisPulse は、アダプタを使用して異なるプラットフォームと対話できる拡張可能なマルチプラットフォームメッセージ処理フレームワークであり、機能拡張のための柔軟なモジュールシステムを提供します。

> **初めて使う？** [5分で始める](docs/ja/quick-start.md) —— インストールから最初のロボットの実行まで、一連の流れを学べます。
>
> 用語がわからない？[用語集](terminology.md)を参照してください。

---

## あなたの進む道を選択

目標に応じて、対応する学習経路を選択してください。各経路は、浅いところから深いところへと順序付けられています。

### 一、ロボットを使いたい

ロボットを動かし、モジュールをインストールし、設定を行う。

| 進捗 | ドキュメント | 説明 |
|------|--------------|------|
| **① 上手** | [5分で始める](docs/ja/quick-start.md) | インストール、初期化、実行 —— 唯一の出発点 |
| ② 深入 | [最初のロボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラの作成 |
| ③ 概念 | [基本概念](getting-started/basic-concepts.md) | アダプタ/モジュール/イベントの設計を理解する |
| ④ 実践 | [一般的なタスクの例](getting-started/common-tasks.md) | ストレージ、定期タスク、権限制御 |
| 参考 | [設定ファイルの説明](user-guide/configuration.md) · [CLIコマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォームの特徴ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖/QQ/Telegram…）の違い |

### 二、モジュール/アダプタを開発したい

ErisPulse 用に配布可能な拡張機能を開発する。

| タイプ | 入門 | 進階 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発入門](developer-guide/modules/getting-started.md) | [コアコンセプト](developer-guide/modules/core-concepts.md) · [Eventラッパー](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプタ開発** | [アダプタ開発入門](developer-guide/adapters/getting-started.md) | [コアコンセプト](developer-guide/adapters/core-concepts.md) · [SendDSLの詳細](developer-guide/adapters/send-dsl.md) · [イベント変換器](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術標準** | [標準規格の概要](standards/README.md) | アダプタ開発で遵守すべき [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [APIレスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | PyPIやモジュールストアに作品を公開する |

### 三、原理を深く理解したい

フレームワークの内部動作を理解する。

| ドキュメント | 説明 |
|--------------|------|
| [アーキテクチャの概要](architecture.md) | 可視化された図表：コアアーキテクチャ、初期化プロセス、イベント処理、ライフサイクル |
| [起動プロセスと手動制御](advanced/startup.md) | 起動プロセスの分解、各段階の手動駆動、ロード失敗の診断 |
| [イベントシステム](api-reference/event-system.md) | 5種類のイベントの完全なAPI |
| [アダプタシステム](api-reference/adapter-system.md) | アダプタの登録、起動/停止、API呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |
| [ライフサイクル管理](advanced/lifecycle.md) · [遅延ロード](advanced/lazy-loading.md) · [ルーティングシステム](advanced/router.md) | 内部サブシステム |
| [Conversationマルチターン会話](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQLビルダー](advanced/sql-builder.md) · [HTTPクライアント](advanced/http-client.md) · [国際化](advanced/i18n.md) | 高度なツール |
| [Dashboard管理パネル](advanced/dashboard-view.md) | Web管理インターフェースの接続 |

### 四、ErisPulseに貢献したい

フレームワークをより良くする。

| ドキュメント | 説明 |
|--------------|------|
| [ErisPulseに貢献する](contributing/README.md) | 貢献方法の概要：ドキュメント / i18n / Bug / モジュール / アダプタ |
| [初めての貢献](contributing/first-contribution.md) | forkからPRの提出まで |

---

## 開発方法

ErisPulse は2種類の開発方法をサポートしています：

- **モジュール開発（推奨）**：独立したモジュールパッケージを作成し、パッケージマネージャーでインストールすることで、配布と管理が容易になります。
- **埋め込み開発**：プロジェクト内で直接ハンドラを記述し、迅速なプロトタイプ作成に適しています。詳しくは [5分で始める](docs/ja/quick-start.md) を参照してください。

## その他

- [ドキュメントスタイルガイド](styleguide/docstring.md) — ドキュメントを貢献する際の作成規則
- [ErisPulseに貢献する](contributing/README.md) — プロジェクトの共同構築への入り口
- [AI支援開発](ai-support/README.md) — AIプログラミングアシスタント用のプロジェクトプロンプト

## ヘルプを得る

- GitHubリポジトリ: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題報告: Issueを提出
- 技術的な議論: Discussionsを参照

## 関連リンク

- [OneBot12標準](https://12.onebot.dev/)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | **日本語** | [Русский](README.ru.md)