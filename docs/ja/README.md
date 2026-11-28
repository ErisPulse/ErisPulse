# ErisPulse ドキュメント

ErisPulse はイベント駆動型のモジュラーアシンクロナスなロボットフレームワークです。ビジネスコードは一度だけ書けば、アダプタを介して QQ、Telegram、Kook、雲湖など複数のプラットフォームにデプロイできます。プラグインシステム、ホットリロード、そして開発者向けの完全なツールチェーンがすぐに利用できます。

> **初めて使う？** [5分で始める](quick-start.md)を直接見てください — インストールから最初のロボットの実行まで、一連の流れを完了します。

---

## 道を選びましょう

目的に応じて、適切な学習経路を選択してください。各経路は難易度の順に並んでいます。

> [!IMPORTANT]
> **すべてのドキュメントを読む必要はありません。** 大多数の開発者は、**L1 コア5編**（約1–2時間）を順に読めば、90%の機能を独自に開発できます。残りのドキュメントは、特定の状況で必要なときに参照するためのものであり、各編の冒頭に「このドキュメントを読む必要があるのはいつか」が明記されています。
>
> **L1 コア5編**：[モジュール開発入門](developer-guide/modules/getting-started.md) → [基本概念](getting-started/basic-concepts.md) → [Event 包装クラス](developer-guide/modules/event-wrapper.md) → [設定ファイルの説明](user-guide/configuration.md) → [例外のキャッチ](advanced/errors.md)
>
> アダプタ開発者は、さらに：[アダプタ開発入門](developer-guide/adapters/getting-started.md) → [イベント変換器](developer-guide/adapters/converter.md) → [SendDSL 詳解](developer-guide/adapters/send-dsl.md) を読む必要があります。

### 一、私はロボットを使いたい

ロボットを起動し、モジュールをインストールし、設定を行います。

| 進捗 | ドキュメント | 説明 |
|------|------|------|
| **① 入門** | [5分で始める](quick-start.md) | インストール、初期化、実行 —— 唯一の出発点 |
| App 直接インストール | [ErisPulse-App クライアント](ecosystem/app.md) | 公式の全プラットフォームクライアント：スマートフォン / PC グラフィカルインターフェースで直接実行・管理、ターミナル不要 |
| ② 深入 | [最初のロボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラの作成 |
| ③ 概念 | [基本概念](getting-started/basic-concepts.md) | アダプタ/モジュール/イベントの設計を理解する |
| ④ 実践 | [一般的なタスクの例](getting-started/common-tasks.md) | ストレージ、定時タスク、権限制御 |
| 参考 | [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) · [アップグレードと移行ガイド](user-guide/migration.md) · [FAQ](user-guide/faq.md) | アップグレード前に移行操作を確認する；トラブルシューティングはまずFAQを参照 |
| 参考 | [プラットフォームの特徴ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖/QQ/Telegram…）の違い |
| 選択 | [選択ガイド](showcase/README.md) | NoneBot2 / AstrBot / LangBot との比較と移行 |

### 二、私はモジュールまたはアダプタを開発したい

ErisPulse 用に配布可能な拡張機能を開発します。

| タイプ | 入門 | 深入 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発入門](developer-guide/modules/getting-started.md) | [基本概念](developer-guide/modules/core-concepts.md) · [Event 包装クラス](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプタ開発** | [アダプタ開発入門](developer-guide/adapters/getting-started.md) | [基本概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベント変換器](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術規格** | [規格の概要](standards/README.md) | アダプタ開発に必須の [会話タイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [API レスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) 規格 |
| **テストとトラブルシューティング** | [モジュールテスト（ErisPulse-Testing）](developer-guide/testing.md) | デプロイの決定に役立つ「コマンドがなぜトリガーされないか」のトラブルシューティング |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品を PyPI とモジュールストアに公開する |

### 三、私は内部の仕組みを理解したい

フレームワークの内部がどのように動作するかを理解します。まずアーキテクチャと API リファレンスを見て、次に下記の対照表に従って各トピックに進んでください。

**アーキテクチャと API リファレンス**

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャ概要](architecture.md) | 可視化された図表：コアアーキテクチャ、初期化プロセス、イベント処理、ライフサイクル、モジュールのロード戦略（`activate_on` イベント駆動による遅延起動）、ローカルプラグインフォルダとモジュールのホットリロードアーキテクチャ（すべてのモジュールソースをサポート） |
| [イベントシステム](api-reference/event-system.md) | 5つのイベントタイプの完全な API |
| [アダプタシステム](api-reference/adapter-system.md) | アダプタの登録、起動・停止、API の呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |

**L2 必読（プロダクションレベルのモジュールを開発するには避けて通れない）**

| ドキュメント | 説明 |
|------|------|
| [スコープ](advanced/scope.md) | 3次元のスコープ制御：モジュールの可用性 / イベントのアクセス制限 / 出力アクションの制限（メソッドレベルの細かいルール、バインディング継承 merge を含む） |
| [所有権（owner）システム](advanced/ownership.md) | リソースの所有と自動回収：owner コンテキスト、所有リソースの全貌、アンロード時のクリーンアップ、設計の境界とモジュール開発者向けガイド |
| [ライフサイクル管理](advanced/lifecycle.md) | ライフサイクルイベントシステム：モジュール / アダプタのロード、アンロード、リロード、無効化時のそれぞれの処理 |
| [対話セッションシステム](advanced/interaction.md) | wait_reply の全解説、セッションタイマー（remind/escalate）、マルチウェイテイング（select）、セッションの排他リース、受信箱、メッセージトランザクション、リンク追跡 |

**シーン別分類（必要に応じて参照）**

| 分類 | ドキュメント | 1編目が分からないとハマるポイント |
|------|------|------|
| 実行と起動 | [起動プロセスと手動制御](advanced/startup.md) · [遅延ロード](advanced/lazy-loading.md) | 起動の流れ（Finder / Loader / Manager / Router）が分からないと、モジュールのロード失敗時にログを見ていても意味不明 |
| 通信と接続 | [モジュール間通信](advanced/module-communication.md) · [接続プールとブロードキャスト](advanced/connections.md) · [ルーティングシステム](advanced/router.md) | サービス契約（`meta.services`）のホワイトリストが分からないと、`module.call` が `ServiceNotProvidedError` で拒否され、原因が分からない |
| データ保存 | [ストレージバックエンド](advanced/storage-backends.md) · [SQL ビルダー](advanced/sql-builder.md) · [ネットワーククライアント](advanced/client.md) | 接続失敗の冷却期間の意味が分からないと、データベースの不安定が発生したときに「フレームワークが落ちた」と誤解してしまう（実際はストレージ操作が失敗し、冷却後に自動的に再接続される） |
| メッセージと会話 | [Conversation 多段会話](advanced/conversation.md) · [会話受信箱](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [国際化](advanced/i18n.md) | 会話の排他リースが分からないと、2つのモジュールが同じユーザーの返信を同時に待つと、お互いにキャンセルしてしまう |
| パフォーマンス観測 | [パフォーマンスのベンチマークとチューニング](advanced/performance.md) | 部署前にベンチマークの数値を確認しないと、容量計画がすべて推測になる；アップグレード後に回帰テストをしないと、パフォーマンスの低下が発見できない |
| グレーディングと影モジュール | [影モジュールとグレーディングの転正](advanced/shadow.md) | 5つの隔離ゲートを知らないまま転正すると、影モジュールの出力が本番ユーザーに漏洩してしまう |

**概念関係表**

どのサブシステムが何を担当しているか分からないときは、この表で確認してください：

| サブシステム | 回答する問題 | 一言口訣 |
|--------|------------|-----------|
| [通信](advanced/module-communication.md)（module-communication） | モジュール間でどのように相互に呼び出し、どのようにイベントを送信するか？ | 跨モジュールは `module.call` を使う；相手が `meta.services` を宣言していると、ホワイトリスト内のメソッドしか呼び出せない |
| [権限](advanced/scope.md)（scope） | 誰がこのモジュールを使えるか、誰がイベントをトリガーできるか、どのアクションを実行できるか？ | 3つのゲート——モジュールのバインディング、アイデンティティのアクセス制限、出力の制限、すべてユーザーの設定で決まる |
| [所有](advanced/ownership.md)（ownership） | モジュールのアンロード後、開いた接続、タイマー、サブスクリプションはどこに行くのか？ | 誰が登録したかが所有者となり、アンロード時にリソースを回収する、ホルダーが残らないようにする |
| [遅延ロードと休眠](advanced/lazy-loading.md)（lazy-loading） | モジュールはいつ実際にロードされるのか、無駄なときはどこに行くのか？ | `activate_on` で使用されるときに起動し、`dormant_after` で無駄なときは休眠する |
| [対話](advanced/interaction.md)（interaction） | ユーザーの次の返信をどのように待つのか、複数段の収集はどのように書くのか？ | `wait_reply` で1つを待つ、`.got()` で連鎖的に複数段を収集、リースで競合を防ぐ |
| [影モジュールとグレーディング](advanced/shadow.md)（shadow） | 新しいモジュールをどのようにして本番に影響を与えることなく試運転するのか？ | 影モジュールはコピーを受け取り、出力は記録するだけ、`promote` で人間が確認して転正する |
| [ストレージ](advanced/storage-backends.md)（storage-backends） | データはどこに保存され、バックエンドはどのように切り替えるのか？ | 一貫したストレージ API で、sqlite / mysql / postgres は設定で切り替えられる |

### 四、エコシステムと公式クライアント

公式クライアント + 必要に応じてインストール可能なエコシステムモジュール（フレームワークの内蔵機能ではありません）。

| ドキュメント | 説明 |
|------|------|
| [エコシステム概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、なぜこれが内蔵機能ではないのか |
| [ErisPulse-QvQChat](ecosystem/qvqchat.md) | 一般的なインテリジェントエージェントモジュール：ツールループ / MCP / 長期記憶 / 知識ベース、サービスを宣言したモジュールは自動的にAIツールになる |
| [ErisPulse-ApiMCP](ecosystem/apimcp.md) | ロボットをMCPツールとして公開し、ClaudeなどのAIクライアントが直接操作できるようにする |
| [ErisPulse-App](ecosystem/app.md) | 公式の全プラットフォームクライアント（Android / Windows / Linux / macOS）：ネイティブインターフェースで複数のインスタンスを管理、**スマートフォンで直接実行**、デスクトップトレイに常駐 |
| [ErisPulse ワークベンチ](ecosystem/workbench.md) | 統一されたアカウントセンター：モジュールの収録と認証、`plugin-xxx.erisdev.com` のホストドメイン、アクセストークンとOAuthログインの接続（オンラインサービス、インストール不要） |
| [ErisPulse ダッシュボード](ecosystem/dashboard.md) | Web管理パネル + ウィンドウのAPI登録（モジュールはサイドバーにカスタムページを登録できる） |
| [ErisPulse クロン](ecosystem/cron.md) | 定時タスクスケジューラモジュール：一回限り / 間隔 / Cron式、コールバックに引数を渡す、SQLiteで永続化、他のモジュールが定時コールバックを委託できる |
| [ErisPulse タクミ](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、内蔵中英文字体） |

### 五、私はErisPulseに貢献したい

フレームワークをより良くする

| ドキュメント | 説明 |
|------|------|
| [ErisPulseへの貢献](contributing/README.md) | 貢献方法の概要：ドキュメント / i18n / バグ / モジュール / アダプタ |
| [初めての貢献](contributing/first-contribution.md) | fork からPRの提出まで |

---
[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

## 高度な機能のバージョン別速查表

バージョンの互換性を判断するとき、または古いプロジェクトを引き継いで「この機能はどのバージョンで導入されたのか」を知りたいときに、この表で照合してください（リポジトリルートの[CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md)の各バージョンの項目を基準とします）。

| バージョン | 導入された機能 |
|------|-----------|
| **2.7** | プロダクション基盤：OneBot12標準化された基底クラス（`ApiDSL` / `BaseConverter`）、設定のホットアップデートシステム化、優雅なシャットダウンとSIGTERM/SIGHUPシグナル処理、環境変数による設定上書き、ライフサイクルコールバックフック、Webスタックの遅延ロード；2.7.1では設定の書き込みの信頼性とGCの世代管理が補完された |
| **2.8** | 権限と通信の骨格：スコープの3次元体系（scope）、インタラクションセッションのインフラ（リース / チェックポイント / メッセージトランザクション / セッション受信箱 transcript）、モジュール間RPCプロトコル化（`module.call` / `meta.services`サービス契約 / 定向イベントemit(to=)）、複数バックエンドの非同期ストレージ（sqlite / mysql / postgres、接続失敗でフレームワークをブロックしない）、所有権のクリーンアップ、設定のコメント保持；2.8.x以降はCLIフッターライブラリ、サブコマンドなどに磨きをかけた |
| **2.9** | 「モジュール開発体験」メインライン（EPRFC-2026-001）：宣言的コマンド引数（`args=` / `options=`）とコマンド管理（`cooldown=` / `rate_limit=`）、一貫した依存注入（`Depends`）、ミドルウェアのイベント否決権、内蔵ORM（自動マイグレーション + 関係マッピング）、影モジュールのグレーディングプロセス、配布決定チェーンの追跡とトラブルシューティング、正式にPython 3.14をサポート |
| **2.10** | 接続を一等リソースとして扱う（`connections`レジストリ：ブロードキャスト / ビジネスグループ / 跨モジュールの再利用 / アンロード時の自動回収）、ルートインポート契約（一般的なAPIはすべて`from ErisPulse import`で使用可能）、所有権体系の補完、受信箱の保持戦略を実行時に上書き可能；2.10.2ではアダプタのローカルプラグインディレクトリ（`plugins/`）+ `epsdk create pack` + tomlclassによる無損失設定書き込み |
| **2.11**（dev） | 「コードを変更 → 効果を確認」の開発ループ：ホットリロードのデフォルトの全量意味（構文検査 + コードアイデンティティ確認 + 依存者連鎖再インポート）、休眠（`dormant_after`）、アダプタコードレベルのホットリロード（`sdk.adapter.reload`）、`.got()`コマンドフロースyntax糖、`epsdk stop` / `restart`による実行時制御 |
| **2.12**（dev） | ライフサイクルの管理と運用性：ネストされたライフサイクル（`ownership.nest()`）、細かいホットリロード（個々のモジュール/アダプタの判定、フレームワークのソース変更はプロセス再起動）、バックグラウンドタスクの待発送キュー、イベント配布チェーンのアカウント自動バインディング（`send_context` / `api_context` / `request_context`が同一口径、複数アカウントモジュールは変更なし）、跨アカウントの重複受理の関連付け（`framework.cross_account_policy`）、影モジュールのwhl取り込みと永続化によるプロセス閉環、コンテナ内`epsdk restart`によるプロセス内ソフトリスタート、`SendDSL.Location()` |

## 開発方法

ErisPulseは2つの開発方法をサポートしています：

- **モジュール開発（推奨）**：独立したモジュールパッケージを作成し、パッケージマネージャーでインストールすることで、配布や管理が容易になります。
- **埋め込み開発**：プロジェクト内で直接ハンドラを記述し、プロトタイプの作成に適しています。詳しくは[快速开始](quick-start.md)を参照してください。

## その他

- [ドキュメントスタイルガイド](styleguide/docstring.md) — ドキュメントを貢献する際の書き方の規範
- [ErisPulseに貢献する](contributing/README.md) — プロジェクトの共同開発への入口
- [AI支援開発](ai-support/README.md) — AIプログラミングアシスタントに使用できるプロジェクトのプロンプト

## ヘルプを得る

- GitHubリポジトリ: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題報告: Issueを投稿
- 技術的な議論: Discussionsを参照

## 関連リンク

- [OneBot12標準](https://12.onebot.dev/)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)