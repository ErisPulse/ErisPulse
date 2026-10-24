# ErisPulse ドキュメント

ErisPulse は、イベント駆動型のモジュラーアシンクロナスロボットフレームワークです。ビジネスロジックを一度だけ記述し、アダプターを介して QQ、Telegram、Kook、雲湖など複数のプラットフォームにデプロイできます。プラグインシステム、ホットリロード、完全な開発者ツールチェーンがすぐに利用可能です。

> **初めて使用しますか？** [5分間クイックスタート](docs/ja/quick-start.md) を直接ご覧ください。インストールから最初のロボットの実行まで、一連の手順を完結します。

## 学習経路の選択

目的に応じて、対応する学習経路を選択してください。各経路は、基礎から応用へと順序づけられています。

> [!IMPORTANT]
> **すべてのドキュメントを読む必要はありません。** 大多数の開発者は、**L1 コア5編**（1–2時間程度）を順番に読むだけで、90%の機能を独自に開発できます。残りのドキュメントは、特定のシナリオ向けのオンデマンドリファレンスです。対応するニーズに遭遇したら、その都度参照してください。各編の冒頭には「この編を読むべきタイミング」が明記されています。
>
> **L1 コア5編**：[モジュール開発入門](developer-guide/modules/getting-started.md) → [基本概念](getting-started/basic-concepts.md) → [Event 包装クラス](developer-guide/modules/event-wrapper.md) → [設定ファイル説明](user-guide/configuration.md) → [例外のキャッチ](advanced/errors.md)
>
> アダプタ作成者は別途：[アダプタ開発入門](developer-guide/adapters/getting-started.md) → [イベント変換器](developer-guide/adapters/converter.md) → [SendDSL 詳解](developer-guide/adapters/send-dsl.md)

### 1. ロボットを使いたい

ロボットを起動し、モジュールをインストールし、設定を行います。

| 進捗 | ドキュメント | 説明 |
|------|------|------|
| **① 初心者向け** | [5分で始める](quick-start.md) | インストール、初期化、実行 —— 唯一のスタート地点 |
| アプリ直装 | [ErisPulse-App クライアント](ecosystem/app.md) | 公式の全プラットフォーム対応クライアント：スマホ / PC でグラフィカルインターフェースで直接実行・管理、ターミナル不要 |
| ② 深入 | [最初のロボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラの作成 |
| ③ 概念 | [基本概念](getting-started/basic-concepts.md) | アダプタ / モジュール / イベントの設計を理解する |
| ④ 実践 | [一般的なタスクの例](getting-started/common-tasks.md) | ストレージ / タイマー / 権限制御 |
| 参考 | [設定ファイル説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォーム特徴ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖 / QQ / Telegram…）の違い |

### 2. モジュール / アダプタを開発したい

ErisPulse 用に配布可能な拡張機能を作成します。

| タイプ | 入門 | 応用 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発入門](developer-guide/modules/getting-started.md) | [コア概念](developer-guide/modules/core-concepts.md) · [Event 包装クラス](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプタ開発** | [アダプタ開発入門](developer-guide/adapters/getting-started.md) | [コア概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベント変換器](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術規格** | [規格概要](standards/README.md) | アダプタ開発に必須の [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [API レスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) 規格 |
| **テストとトラブルシューティング** | [モジュールテスト（ErisPulse-Testing）](developer-guide/testing.md) | 「コマンドがなぜトリガーされないか」を分岐決定するためのトラブルシューティング |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品を PyPI とモジュールストアに公開する |

### 3. 框架の原理を深く理解したい

フレームワークの内部動作を理解します。まずアーキテクチャと API リファレンスを読み、次に以下の対照表に従って各トピックに進んでください。

**アーキテクチャと API リファレンス**

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャ概要](architecture.md) | ビジュアル図表：コアアーキテクチャ、初期化プロセス、イベント処理、ライフサイクル、モジュールロード戦略（`activate_on` イベント駆動のラグジュアリーな起動）、ローカルプラグインフォルダとモジュールのホットリロードアーキテクチャ（すべてのモジュールソースに対応） |
| [イベントシステム](api-reference/event-system.md) | 5種類のイベントの完全な API |
| [アダプタシステム](api-reference/adapter-system.md) | アダプタの登録、起動 / 停止、API 呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |

**L2 必読（プロダクションレベルのモジュールを開発するには避けて通れない）**

| ドキュメント | 説明 |
|------|------|
| [スコープ（scope）](advanced/scope.md) | 3次元スコープ制御：モジュールの可用性 / イベントのアクセス制御 / 出力アクションの制限（メソッドレベルの細かいルール、バインディング継承 merge 含む） |
| [所有権（owner）システム](advanced/ownership.md) | リソースの所有と自動回収：owner コンテキスト、所有リソースの全体像、アンロード時のクリーンアップシーケンス、設計境界とモジュール作成者ガイド |
| [ライフサイクル管理](advanced/lifecycle.md) | ライフサイクルイベントシステム：モジュール / アダプタのロード、アンロード、再ロード、無効化時の処理 |
| [インタラクションセッションシステム](advanced/interaction.md) | wait_reply の完全解説、セッションタイマー（remind/escalate）、マルチウェイティング（select）、セッション排他リース、受信箱、メッセージトランザクション、リンク追跡 |

**シナリオ別分類（必要に応じて参照）**

| 分類 | ドキュメント | 初心者がつまずく原因 |
|------|------|------|
| 実行 / 起動 | [起動プロセスと手動制御](advanced/startup.md) · [ラグジュアリーなロード](advanced/lazy-loading.md) | 起動プロセス（Finder / Loader / Manager / Router）を理解していないと、モジュールのロード失敗時にログをただ見ているだけになる |
| 通信 / 接続 | [モジュール間通信](advanced/module-communication.md) · [接続プールとブラッドキャスト](advanced/connections.md) · [ルーティングシステム](advanced/router.md) | サービス契約（`meta.services`）のホワイトリストを理解していないと、`module.call` が `ServiceNotProvidedError` で拒否され、原因が分からないままになる |
| データ / ストレージ | [ストレージバックエンド](advanced/storage-backends.md) · [SQL ビルダー](advanced/sql-builder.md) · [HTTP クライアント](advanced/http-client.md) | 接続失敗のクールダウン期間の意味を理解していないと、データベースの不安定時にフレームワークが「落ちた」と誤解する（実際はストレージ操作が即座に失敗し、クールダウン後に自動的に再接続される） |
| メッセージ / 会話 | [Conversation マルチラウンド会話](advanced/conversation.md) · [セッション受信箱](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [国際化](advanced/i18n.md) | セッション排他リースを理解していないと、2つのモジュールが同じユーザーの返信を同時に待つと、お互いにキャンセルしてしまう |
| グレーディング / シャドー | [シャドーモジュールとグレーディングの昇格](advanced/shadow.md) | 5つの隔離ゲートを理解していないまま昇格すると、シャドーの出力メッセージが本番ユーザーに外溢してしまう |

**概念関係表**

どのサブシステムが何を担当しているか分からないときは、この表で照らし合わせてください。

| サブシステム | 回答する問題 | 1文で覚える口訣 |
|--------|------------|-----------|
| [通信](advanced/module-communication.md)（module-communication） | モジュール間でどう呼び合うか、どうイベントを送るか？ | 跨モジュールは `module.call` を使う；相手が `meta.services` を宣言している場合は、ホワイトリスト内のメソッドしか呼び出せない |
| [権限](advanced/scope.md)（scope） | 誰がこのモジュールを使えるか、誰がイベントをトリガーできるか、どのアクションが実行できるか？ | 3つのゲート——モジュールバインディング、アイデンティティのアクセス制限、出力制限、すべてはユーザーの設定で決まる |
| [所有](advanced/ownership.md)（ownership） | モジュールがアンロードされた後、開いた接続、タイマー、サブスクリプションはどこに行くのか？ | 登録した者が所有し、アンロード即時回収、ホルダーリソースを残さない |
| [ラグジュアリーなロードと休眠](advanced/lazy-loading.md)（lazy-loading） | モジュールはいつロードされるのか、アイドル状態ではどこに行くのか？ | `activate_on` で使用されるまで起動せず、`dormant_after` でアイドル状態で休眠 |
| [インタラクション](advanced/interaction.md)（interaction） | ユーザーの次の返信をどう待つか、マルチラウンドの収集はどう書くのか？ | `wait_reply` で1つを待つ、`.got()` で複数を連鎖収集、リースで競合を防ぐ |
| [シャドー / グレーディング](advanced/shadow.md)（shadow） | 新バージョンのモジュールを本番に影響を与えることなく試すにはどうすればいいのか？ | シャドーはコピーを受け取り、出力は記録のみ、`promote` は人間が確認して昇格させる |
| [ストレージ](advanced/storage-backends.md)（storage-backends） | データはどこに保存され、バックエンドはどのように切り替えるのか？ | 同じストレージ API を使えば、sqlite / mysql / postgres は設定で切り替えられる |

### 4. エコシステムと公式クライアント

公式クライアント + エコシステムモジュールのインストール（フレームワークに内蔵されていない機能）。

| ドキュメント | 説明 |
|------|------|
| [エコシステム概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、なぜこれらが内蔵機能ではないのか |
| [ErisPulse-App](ecosystem/app.md) | 公式の全プラットフォーム対応クライアント（Android / Windows / Linux / macOS）：ネイティブインターフェースで複数のインスタンスを管理、**スマホで直接実行**、デスクトップのトレイに常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web管理パネル + ウィンドウ登録API（モジュールはサイドバーにカスタムページを登録できる） |
| [ErisPulse-Cron](ecosystem/cron.md) | タイマーのスケジューラモジュール：一回限り / 間隔 / Cron式、コールバックに引数を渡す、SQLiteで永続化、他のモジュールにタイマーのコールバックを委託できる |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、内蔵中英文字体） |

### 5. ErisPulse に貢献したい

フレームワークをより良くする

| ドキュメント | 説明 |
|------|------|
| [ErisPulse への貢献](contributing/README.md) | 貢献方法の概要：ドキュメント / i18n / Bug / モジュール / アダプタ |
| [初めての貢献](contributing/first-contribution.md) | フォークからPR提出まで |

## 高級機能のバージョン比較表

バージョンの互換性を判断する場合、または古いプロジェクトを引き継いで「この機能がどのバージョンで導入されたか」を知りたいときは、この表を参考にしてください（リポジトリルートの [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md) 各バージョンの項目を基準とします）。

| バージョン | 導入された機能 |
|------|-----------|
| **2.7** | プロダクション基盤：OneBot12 標準化基底クラス（`ApiDSL` / `BaseConverter`）、設定のホットリロードの体系化、優雅な終了と SIGTERM/SIGHUP 信号処理、環境変数による設定の上書き、ライフサイクルコールバックフック、Web スタックのラジーロード；2.7.1 では設定の書き込みの信頼性と GC 分代の管理を補強 |
| **2.8** | 権限と通信の骨格：作用域の三次元体系（scope）、インタラクティブなセッションのインフラ（リース / チェックポイント / メッセージトランザクション / セッション受信箱 transcript）、モジュール間の RPC 協定化（`module.call` / `meta.services` サービス契約 / 定向イベント emit(to=)）、複数のバックエンド非同期ストレージ（sqlite / mysql / postgres、接続失敗でもフレームワークをブロックしない）、所有権のクリーンアップ、設定のコメント保持；2.8.x 後のバージョンでは CLI フッタースターラー、サブコマンドなどを整備 |
| **2.9** | 「モジュール開発体験」メインライン（EPRFC-2026-001）：宣言的コマンドパラメータ（`args=` / `options=`）とコマンド管理（`cooldown=` / `rate_limit=`）、統一された依存性注入（`Depends`）、ミドルウェアイベントの否決権、組み込み ORM（自動マイグレーション + 関係マッピング）、影モジュールのグレーディングから正式化、配布決定チェーンの追跡とトラブルシューティング、正式に Python 3.14 をサポート |
| **2.10** | 接続一等リソース（`connections` レジストリ：ブロードキャスト / 業務グループ / 跨モジュールの共有再利用 / 卸載時の自動回収）、ルートインポート契約（一般的な API はすべて `from ErisPulse import` で利用可能）、所有権体系の補完、受信箱の保持戦略のランタイム上書き；2.10.2 ではアダプターのローカルプラグインディレクトリ（`plugins/`）+ `epsdk create pack` + tomlclass による無損失設定書き込みを実装 |
| **2.11**（dev） | 「コードを変更 → 結果を見る」開発の完結ループ：デフォルトで全量のホットリロード（構文の事前チェック + コードのアイデンティティ確認 + 依存者の連鎖的再インポート）、ラジーロードの休眠（`dormant_after`）、アダプターのコードレベルのホットリロード（`sdk.adapter.reload`）、`.got()` コマンドフローサイntax糖、`epsdk stop` / `restart` によるランタイムコントロール |

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