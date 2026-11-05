# ErisPulse ドキュメント

ErisPulse はイベント駆動のモジュール型非同期ボットフレームワークです——ビジネスコードは一度だけ書けば、アダプターを通じて QQ、Telegram、Kook、雲湖（Yunhu）など複数のプラットフォームにデプロイでき、プラグインシステム・ホットリロード・完全な開発者ツールチェーンがすぐに使えます。

> **初めて使う場合**は、まず [5 分クイックスタート](quick-start.md) へ —— インストールから最初のボットの実行まで、一気に完結できます。

---

## 学習パスを選ぶ

目標に応じて、対応する学習パスを選んでください。各パスの中身は初級から順に並んでいます。

> [!IMPORTANT]
> **すべてのドキュメントを読む必要はありません。** ほとんどの開発者は、**L1 コア 5 編**を
> 順番に読むだけ（約 1～2 時間）で、機能の 90% を独力で開発できます。それ以外のドキュメントは、
> すべて特定のシナリオ向けの必要時に参照する資料です——該当するニーズが出たときに読めばよく、
> 各記事の冒頭には「いつこの記事を読むべきか」が明記されています。
>
> **L1 コア 5 編**：[モジュール開発入門](developer-guide/modules/getting-started.md)
> → [基本概念](getting-started/basic-concepts.md)
> → [Event ラッパークラス](developer-guide/modules/event-wrapper.md)
> → [設定ファイルの説明](user-guide/configuration.md)
> → [例外の捕捉](advanced/errors.md)
>
> アダプター作者はさらに以下が必要です：[アダプター開発入門](developer-guide/adapters/getting-started.md)
> → [イベントコンバーター](developer-guide/adapters/converter.md)
> → [SendDSL 詳解](developer-guide/adapters/send-dsl.md)

### 一、ボットを使いたい

ボットを動かし、モジュールをインストールし、設定を行う。

| 進度 | ドキュメント | 説明 |
|------|------|------|
| **① スタート** | [5 分クイックスタート](quick-start.md) | インストール、初期化、実行 —— 唯一のスタート地点 |
| App で直接導入 | [ErisPulse-App クライアント](ecosystem/app.md) | 公式全プラットフォーム対応クライアント：スマホ / PC の GUI で直接実行・管理、ターミナル不要 |
| ② 深掘り | [最初のボットを作る](getting-started/first-bot.md) | 最初のコマンドハンドラーを作成 |
| ③ 概念 | [基本概念](getting-started/basic-concepts.md) | アダプター/モジュール/イベントの設計を理解する |
| ④ 実践 | [よくあるタスクの例](getting-started/common-tasks.md) | ストレージ、定期タスク、権限制御 |
| リファレンス | [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| リファレンス | [プラットフォーム機能ガイド](platform-guide/README.md) | 各プラットフォーム（雲湖/QQ/Telegram…）の差異 |
| 選定 | [選定ガイド](showcase/README.md) | NoneBot2 / AstrBot / LangBot との比較と移行 |

### 二、モジュール / アダプターを開発したい

ErisPulse 向けに配布可能な拡張を作成する。

| 種類 | 入門 | 発展 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発入門](developer-guide/modules/getting-started.md) | [コア概念](developer-guide/modules/core-concepts.md) · [Event ラッパークラス](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプター開発** | [アダプター開発入門](developer-guide/adapters/getting-started.md) | [コア概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベントコンバーター](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術標準** | [標準仕様の概要](standards/README.md) | アダプター開発で必ず従うべき [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [API レスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) の各仕様 |
| **テストとトラブルシューティング** | [モジュールテスト（ErisPulse-Testing）](developer-guide/testing.md) | ディスパッチ決定チェーンで「コマンドがなぜ発火しなかったのか」を調査 |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品を PyPI とモジュールストアに公開する |

### 三、原理を深く理解したい

フレームワーク内部の仕組みを学ぶ。まずアーキテクチャと API リファレンスを見てから、下の対照表に従って各トピックへ進む。

**アーキテクチャと API リファレンス**

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャ概要](architecture.md) | 視覚化された図表：コアアーキテクチャ、初期化フロー、イベント処理、ライフサイクル、モジュールロード戦略（`activate_on` によるイベント駆動の遅延アクティベーションを含む）、ローカルプラグインフォルダとモジュールホットリロードのアーキテクチャ（すべてのモジュールソースに対応） |
| [イベントシステム](api-reference/event-system.md) | 5 大カテゴリのイベントの完全な API |
| [アダプターシステム](api-reference/adapter-system.md) | アダプターの登録、起動・停止、API 呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基礎機能 |

**L2 必読（本番レベルのモジュールを書くなら避けて通れない）**

| ドキュメント | 説明 |
|------|------|
| [スコープ（scope）](advanced/scope.md) | 3 次元のスコープ制御：モジュールの利用可否 / イベントの受け入れ / 送信アクションの制限（メソッドレベルの細粒度ルール、バインディング継承の merge を含む） |
| [オーナーシップ（owner）システム](advanced/ownership.md) | リソースのオーナー管理と自動回収：owner コンテキスト、オーナー管理下リソースの全体像、アンロード時のクリーンアップシーケンス、設計上の境界とモジュール作者向けガイド |
| [ライフサイクル管理](advanced/lifecycle.md) | ライフサイクルイベントシステム：モジュール / アダプターのロード、アンロード、リロード、無効化の際にそれぞれ何をすべきか |
| [インタラクションセッションシステム](advanced/interaction.md) | wait_reply 完全解説、セッションタイマー（remind/escalate）、マルチウェイ待機（select）、セッション排他リース、インボックス、メッセージトランザクション、トレーシング |

**シナリオ別グループ（必要に応じて参照）**

| グループ | ドキュメント | 最初の記事を理解しないと踏む落とし穴 |
|------|------|------|
| 起動とスタートアップ | [起動フローと手動制御](advanced/startup.md) · [遅延ロード](advanced/lazy-loading.md) | 起動チェーン（Finder / Loader / Manager / Router）を理解していないと、モジュールのロード失敗時にログを前にして途方に暮れるしかない |
| 通信と接続 | [モジュール間通信](advanced/module-communication.md) · [接続プールとブロードキャスト](advanced/connections.md) · [ルーティングシステム](advanced/router.md) | サービス契約（`meta.services`）のホワイトリストを理解していないと、モジュールをまたぐ `module.call` が `ServiceNotProvidedError` で拒否されても理由が分からない |
| データストレージ | [ストレージバックエンド](advanced/storage-backends.md) · [SQL ビルダー](advanced/sql-builder.md) · [ネットワーククライアント](advanced/client.md) | 接続失敗時のクールダウン期間のセマンティクスを理解していないと、データベースが不安定になったときに「フレームワークが壊れた」と誤判断する（実際はストレージ操作がフェイルファストし、クールダウン後に自動再接続するだけ） |
| メッセージと対話 | [Conversation マルチターン対話](advanced/conversation.md) · [セッションインボックス](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [国際化](advanced/i18n.md) | セッション排他リースを理解していないと、2 つのモジュールが同一ユーザーの返信を同時に待つと互いを蹴り合ってしまう |
| シャドウとカナリア | [シャドウモジュールとカナリア昇格](advanced/shadow.md) | 5 つの隔離ゲートを理解しないまま早めに昇格させると、シャドウの送信メッセージが実ユーザーに漏れ出る |

**概念の関係早見表**

どのサブシステムが何を担っているか分からないときは、この表で該当箇所を探してください：

| サブシステム | どんな問題に答えるか | 一言まとめ |
|--------|------------|-----------|
| [通信](advanced/module-communication.md)（module-communication） | モジュール間でどう呼び合うか、イベントをどう宛先指定で送るか？ | モジュールをまたぐには `module.call` を使う。相手が `meta.services` を宣言している場合、呼べるのはホワイトリスト内のメソッドだけ |
| [権限](advanced/scope.md)（scope） | 誰がこのモジュールを使えるか、誰がイベントを発火できるか、どのアクションを実行できるか？ | 3 つのゲート——モジュールバインド、アイデンティティの受け入れ、送信制限。すべてユーザー設定が決める |
| [オーナーシップ](advanced/ownership.md)（ownership） | モジュールのアンロード後、それが開いた接続・タイマー・購読はどこへ行く？ | 登録した者がオーナー、アンロードすれば即回収。ぶら下がったリソースは残さない |
| [遅延ロードと休眠](advanced/lazy-loading.md)（lazy-loading） | モジュールはいつ実際にロードされ、アイドル後はどこへ行く？ | `activate_on` は使うときに目覚め、`dormant_after` でアイドル時は眠りに戻る |
| [インタラクション](advanced/interaction.md)（interaction） | ユーザーの次の返信をどう待つか、マルチターンの収集はどう書くか？ | `wait_reply` は 1 件待ち、`.got()` チェーンで複数ターン収集。リースが衝突を防ぐ |
| [シャドウ/カナリア](advanced/shadow.md)（shadow） | 新バージョンのモジュールを本番に影響を与えずに試験運用するには？ | シャドウはコピーを受け取り、送信は記録のみ。`promote` は人の確認があって初めて昇格する |
| [ストレージ](advanced/storage-backends.md)（storage-backends） | データはどこに保存するか、バックエンドはどう切り替えるか？ | 同じストレージ API で、sqlite / mysql / postgres を設定で切り替え |

### 四、エコシステムと公式クライアント

公式クライアント + 必要に応じてインストールし、入れたらすぐ使えるエコシステムモジュール（いずれもフレームワークの内蔵機能ではありません）。

| ドキュメント | 説明 |
|------|------|
| [エコシステムの概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、これらが内蔵機能でない理由 |
| [ErisPulse-QvQChat](ecosystem/qvqchat.md) | 汎用エージェントモジュール：ツールループ / MCP / 長期記憶 / ナレッジベース。サービスを宣言したモジュールは自動的に AI ツールになる |
| [ErisPulse-ApiMCP](ecosystem/apimcp.md) | ボットを逆に MCP ツールとして公開し、Claude などの AI クライアントから直接操作できるようにする |
| [ErisPulse-App](ecosystem/app.md) | 公式全プラットフォーム対応クライアント（Android / Windows / Linux / macOS）：ネイティブ UI で複数インスタンスを管理、**スマホで直接実行**、デスクトップトレイに常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理パネル + ビュー登録 API（モジュールはサイドバーにカスタムページを登録可能） |
| [ErisPulse-Cron](ecosystem/cron.md) | 定期タスクスケジューリングモジュール：単発 / インターバル / Cron 式、コールバックへの引数渡し、SQLite 永続化、他のモジュールは定期コールバックを委託可能 |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、中国語・英語フォント内蔵） |

### 五、ErisPulse に貢献したい

フレームワークをより良いものにする

| ドキュメント | 説明 |
|------|------|
| [ErisPulse への貢献](contributing/README.md) | 貢献方法の概要：ドキュメント / i18n / バグ / モジュール / アダプター |
| [初めての貢献](contributing/first-contribution.md) | fork から PR 提出まで |

---

## 高度な機能のバージョン早見表

バージョン互換性の判定を行うときや、古いプロジェクトを引き継いで「この機能はどのバージョンで導入されたのか」を知りたいときは、この表で該当箇所を確認してください（内容はリポジトリルートの [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md) の各バージョンエントリが正となります）。

| バージョン | 導入された機能 |
|------|-----------|
| **2.7** | 本番運用の基盤：OneBot12 標準化基底クラス（`ApiDSL` / `BaseConverter`）、設定ホットリロードの体系化、グレースフルシャットダウンと SIGTERM/SIGHUP シグナル処理、環境変数による設定オーバーライド、ライフサイクルコールバックフック、Web スタックの遅延ロード。2.7.1 で設定書き込みの信頼性と GC 世代管理を補完 |
| **2.8** | 権限と通信の骨格：3 次元スコープ体系（scope）、インタラクションセッションインフラ（リース / チェックポイント / メッセージトランザクション / セッションインボックス transcript）、モジュール間 RPC のプロトコル化（`module.call` / `meta.services` サービス契約 / 宛先指定イベント emit(to=)）、マルチバックエンド非同期ストレージ（sqlite / mysql / postgres、接続失敗でもフレームワークをブロックしない）、オーナーシップクリーンアップ、設定コメントの保持。2.8.x の後続バージョンは CLI スキャフォールドやサブコマンドなどの磨き込み |
| **2.9** | 「モジュール開発体験」メインライン（EPRFC-2026-001）：宣言型コマンドパラメータ（`args=` / `options=`）とコマンドガバナンス（`cooldown=` / `rate_limit=`）、統一依存性注入（`Depends`）、ミドルウェアのイベント否決権、内蔵 ORM（自動マイグレーション + リレーションマッピング）、シャドウモジュールのカナリア昇格、ディスパッチ決定チェーンのトレースとトラブルシューティング診断、Python 3.14 の正式サポート |
| **2.10** | 接続の第一級リソース化（`connections` レジストリ：ブロードキャスト / 業務グルーピング / モジュール間受け渡しの再利用 / アンロード時の自動回収）、ルートインポート契約（よく使う API はすべて `from ErisPulse import` でインポート可能）、オーナーシップ体系の補完、インボックス保持ポリシーのランタイムオーバーライド。2.10.2 でアダプターのローカルプラグインディレクトリ（`plugins/`）+ `epsdk create pack` + tomlclass によるロスレス設定書き込み |
| **2.11**（dev） | 「コードを変更 → 結果を確認」の開発ループ：ホットリロードのデフォルト完全セマンティクス（構文事前チェック + コードアイデンティティ照合 + 依存側へのカスケード再エクスポート）、遅延ロード休眠（`dormant_after`）、アダプターのコードレベルホットリロード（`sdk.adapter.reload`）、`.got()` コマンドフローの糖衣構文、`epsdk stop` / `restart` ランタイム制御 |

## 開発スタイル

ErisPulse は 2 つの開発スタイルをサポートしています：

- **モジュール開発（推奨）**：独立したモジュールパッケージを作成し、パッケージマネージャーでインストールします。配布と管理が容易です。
- **埋め込み型開発**：プロジェクト内に直接ハンドラーを記述します。迅速なプロトタイピングに適しています。詳細は [クイックスタート](quick-start.md) を参照してください。

## その他

- [ドキュメントスタイルガイド](styleguide/docstring.md) — ドキュメントに貢献する際の執筆規約
- [ErisPulse への貢献](contributing/README.md) — プロジェクト共同構築への参加入口
- [AI 支援開発](ai-support/README.md) — AI コーディングアシスタント向けのプロジェクトプロンプトの入手

## ヘルプの入手

- GitHub リポジトリ：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題の報告：Issue を提出
- 技術的な議論：Discussions を参照

## 関連リンク

- [OneBot12 標準](https://12.onebot.dev/)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)