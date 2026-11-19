# ErisPulse ドキュメント

ErisPulse はイベント駆動型のモジュール式非同期ボットフレームワークです。ビジネスコードは一度だけ書けば、アダプター経由で QQ、Telegram、Kook、云湖 など複数のプラットフォームにデプロイでき、プラグインシステム、ホットリロード、完全な開発者ツールチェーンが最初から使える状態で提供されます。

> **初めてご利用ですか？** [5分クイックスタート](quick-start.md) を直接ご覧ください —— インストールから最初のボットの実行まで、一気通貫で進められます。

---

## 自分に合ったパスを選ぶ

目標に応じて、対応する学習パスを選択してください。各パス内では、易しいものから難しいものへと順に並んでいます。

> [!IMPORTANT]
> **すべてのドキュメントを読み切る必要はありません。** 大多数の開発者は、**L1 コア5編**
> （約1〜2時間）を順番に読むだけで、機能の90%を独力で開発できるようになります。それ以外の
> ドキュメントはすべて、特定のシナリオ向けの必要に応じた参照資料です。該当するニーズが
> 生じた時点で参照すればよく、各記事の冒頭には「いつこの記事を読むべきか」が明記されています。
>
> **L1 コア5編**：[モジュール開発入門](developer-guide/modules/getting-started.md)
> → [基本概念](getting-started/basic-concepts.md)
> → [Event ラッパークラス](developer-guide/modules/event-wrapper.md)
> → [設定ファイルの説明](user-guide/configuration.md)
> → [例外の捕捉](advanced/errors.md)
>
> アダプター作者にはさらに以下が必要です：[アダプター開発入門](developer-guide/adapters/getting-started.md)
> → [イベントコンバーター](developer-guide/adapters/converter.md)
> → [SendDSL 詳解](developer-guide/adapters/send-dsl.md)

### 一、ボットを使いたい

ボットを動かし、モジュールをインストールし、設定を行います。

| 進行状況 | ドキュメント | 説明 |
|------|------|------|
| **① スタート** | [5分クイックスタート](quick-start.md) | インストール、初期化、実行 —— 唯一のスタート地点 |
| App 直インストール | [ErisPulse-App クライアント](ecosystem/app.md) | 公式全プラットフォームクライアント：スマホ / PC の GUI で直接実行・管理、ターミナル不要 |
| ② 深掘り | [最初のボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラーを書く |
| ③ 概念 | [基本概念](getting-started/basic-concepts.md) | アダプター/モジュール/イベントの設計を理解する |
| ④ 実践 | [よくあるタスクの例](getting-started/common-tasks.md) | ストレージ、定期タスク、権限制御 |
| 参照 | [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参照 | [プラットフォーム特性ガイド](platform-guide/README.md) | 各プラットフォーム（云湖/QQ/Telegram…）の違い |
| 選定 | [選定ガイド](showcase/README.md) | NoneBot2 / AstrBot / LangBot との比較と移行 |

### 二、モジュール / アダプターを開発したい

ErisPulse 用の配布可能な拡張機能を作成します。

| タイプ | 入門 | 応用 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発入門](developer-guide/modules/getting-started.md) | [コア概念](developer-guide/modules/core-concepts.md) · [Event ラッパークラス](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプター開発** | [アダプター開発入門](developer-guide/adapters/getting-started.md) | [コア概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベントコンバーター](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術標準** | [標準仕様の概観](standards/README.md) | アダプター開発が従うべき [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [API レスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) の各仕様 |
| **テストとトラブルシューティング** | [モジュールテスト（ErisPulse-Testing）](developer-guide/testing.md) | ディスパッチ決定チェーンによる「コマンドがなぜ発火しなかったのか」の調査 |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品を PyPI とモジュールストアに公開する |

### 三、仕組みを深く理解したい

フレームワーク内部がどのように動作するかを理解します。まずアーキテクチャと API リファレンスを確認し、その後、下記の対応表に従って各トピックへ進んでください。

**アーキテクチャと API リファレンス**

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャ概観](architecture.md) | 可視化図表：コアアーキテクチャ、初期化フロー、イベント処理、ライフサイクル、モジュール読み込み戦略（`activate_on` によるイベント駆動の遅延アクティベーションを含む）、ローカルプラグインフォルダとモジュールホットリロードアーキテクチャ（すべてのモジュールソースに対応） |
| [イベントシステム](api-reference/event-system.md) | 5大イベントカテゴリの完全な API |
| [アダプターシステム](api-reference/adapter-system.md) | アダプターの登録、起動・停止、API 呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基本機能 |

**L2 必読（本番レベルのモジュールを書くなら避けて通れない）**

| ドキュメント | 説明 |
|------|------|
| [スコープ（scope）](advanced/scope.md) | 3次元スコープ制御：モジュールの可用性 / イベントの受け入れ可否 / 送信アクションの制限（メソッドレベルのきめ細かいルール、バインド継承の merge を含む） |
| [所有権（owner）システム](advanced/ownership.md) | リソースの所有と自動回収：owner コンテキスト、所有リソースの全体像、アンロード時のクリーンアップシーケンス、設計上の境界とモジュール作者向けガイド |
| [ライフサイクル管理](advanced/lifecycle.md) | ライフサイクルイベントシステム：モジュール / アダプターの読み込み、アンロード、リロード、無効化の際にそれぞれ何をすべきか |
| [インタラクションセッションシステム](advanced/interaction.md) | wait_reply 完全解説、セッションタイマー（remind/escalate）、複数同時待ち（select）、セッション相互排他リース、受信箱、メッセージトランザクション、トレーシング |

**シナリオ別グループ（必要に応じて参照）**

| グループ | ドキュメント | 最初の記事を理解しないと陥る落とし穴 |
|------|------|------|
| 起動 | [起動フローと手動制御](advanced/startup.md) · [遅延読み込み](advanced/lazy-loading.md) | 起動チェーン（Finder / Loader / Manager / Router）を理解していないと、モジュールの読み込み失敗時にログを眺めることしかできません |
| 通信接続 | [モジュール間通信](advanced/module-communication.md) · [接続プールとブロードキャスト](advanced/connections.md) · [ルーティングシステム](advanced/router.md) | サービス契約（`meta.services`）のホワイトリストを理解していないと、モジュール間の `module.call` が `ServiceNotProvidedError` で拒否されても理由が分かりません |
| データストレージ | [ストレージバックエンド](advanced/storage-backends.md) · [SQL ビルド](advanced/sql-builder.md) · [ネットワーククライアント](advanced/client.md) | 接続失敗時のクールダウン期間のセマンティクスを理解していないと、データベースに不調が起きたときに「フレームワークが壊れた」と誤認します（実際にはストレージ操作がフェイルファストし、クールダウン後に自動再接続するだけです） |
| メッセージ対話 | [Conversation 多ターン対話](advanced/conversation.md) · [セッション受信箱](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [国際化](advanced/i18n.md) | セッション相互排他リースを理解していないと、2つのモジュールが同じユーザーの返信を同時に待つと互いに追い出されてしまいます |
| パフォーマンス計測 | [パフォーマンスベンチマークとチューニング](advanced/performance.md) | デプロイ前にベンチマーク数値を確認しないと、キャパシティプランニングが当てずっぽうになります。アップグレード後に回帰比較をしないと、パフォーマンス劣化に気付けません |
| シャドウとグレースケール | [シャドウモジュールとグレースケール昇格](advanced/shadow.md) | 5つの分離ゲートを理解しないまま昇格を急ぐと、シャドウの送信メッセージが実際のユーザーに漏れ出てしまいます |

**概念関係の一覧表**

どのサブシステムが何を管轄しているのか分からないときは、この表で該当する行を探してください：

| サブシステム | どのような問題に答えるか | 一言まとめ |
|--------|------------|-----------|
| [通信](advanced/module-communication.md)（module-communication） | モジュール同士はどう呼び合うか、イベントをどう宛先指定で送るか？ | モジュール間は `module.call` を使う。相手が `meta.services` を宣言している場合、ホワイトリスト内のメソッドしか呼べない |
| [権限](advanced/scope.md)（scope） | 誰がこのモジュールを使えるか、誰がイベントを発火できるか、どのアクションを実行できるか？ | 3つのゲート —— モジュールバインド、ID 受け入れ、送信制限。すべてユーザー設定が決定する |
| [所有](advanced/ownership.md)（ownership） | モジュールのアンロード後、そのモジュールが開いた接続、タイマー、サブスクリプションはどこへ？ | 登録した者が所有し、アンロード時に回収。宙ぶらりんのリソースは残さない |
| [遅延読み込みとスリープ](advanced/lazy-loading.md)（lazy-loading） | モジュールはいつ実際に読み込まれ、アイドル後はどこへ？ | `activate_on` は使われるときに目覚め、`dormant_after` でアイドル時にスリープへ |
| [インタラクション](advanced/interaction.md)（interaction） | ユーザーの次の返信をどう待つか、多ターンの収集はどう書くか？ | `wait_reply` は1件を待ち、`.got()` チェーンは複数ターンを収集。リースが衝突を防止する |
| [シャドウとグレースケール](advanced/shadow.md)（shadow） | 新バージョンのモジュールを本番に影響なく試験運用するには？ | シャドウはコピーを受け取り、送信は記録のみ。`promote` は人間の確認後に初めて正式昇格する |
| [ストレージ](advanced/storage-backends.md)（storage-backends） | データはどこに保存され、バックエンドはどう切り替えるか？ | 同一のストレージ API で、sqlite / mysql / postgres を設定で切り替え |

### 四、エコシステムと公式クライアント

公式クライアント + 必要に応じてインストールし、インストール後すぐに使えるエコシステムモジュール（いずれもフレームワークに内蔵された機能ではありません）。

| ドキュメント | 説明 |
|------|------|
| [エコシステム概観](ecosystem/README.md) | エコシステムモジュールのインストール方法、これらが内蔵機能ではない理由 |
| [ErisPulse-QvQChat](ecosystem/qvqchat.md) | 汎用エージェントモジュール：ツールループ / MCP / 長期記憶 / ナレッジベース。サービスを宣言したモジュールは自動的に AI ツールになります |
| [ErisPulse-ApiMCP](ecosystem/apimcp.md) | ボットを逆に MCP ツールとして公開し、Claude などの AI クライアントに直接操作させる |
| [ErisPulse-App](ecosystem/app.md) | 公式全プラットフォームクライアント（Android / Windows / Linux / macOS）：ネイティブ UI で複数インスタンスを管理、**スマホで直接実行**、デスクトップトレイに常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理パネル + ペイン登録 API（モジュールはサイドバーにカスタムページを登録できます） |
| [ErisPulse-Cron](ecosystem/cron.md) | 定期タスクスケジューリングモジュール：単発 / 間隔 / Cron 式、コールバックへの引数渡し、SQLite 永続化、他のモジュールは定期コールバックを委託可能 |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、中国語・英語フォント内蔵） |

### 五、ErisPulse に貢献したい

フレームワークをより良いものに

| ドキュメント | 説明 |
|------|------|
| [ErisPulse への貢献](contributing/README.md) | 貢献方法の概観：ドキュメント / i18n / Bug / モジュール / アダプター |
| [初めての貢献](contributing/first-contribution.md) | fork から PR 提出まで |

---

## 高度な機能のバージョン早見表

バージョン互換性の判断をする場合や、古いプロジェクトを引き継いだ際に「この機能はどのバージョンで導入されたのか」を知りたい場合は、この表で該当項目を探してください（リポジトリルートの [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md) の各バージョンエントリが正とします）。

| バージョン | 導入された機能 |
|------|-----------|
| **2.7** | 本番運用基盤：OneBot12 標準化基底クラス（`ApiDSL` / `BaseConverter`）、設定ホットアップデートの体系化、グレースフルシャットダウンと SIGTERM/SIGHUP シグナル処理、環境変数による設定の上書き、ライフサイクルコールバックフック、Web スタックの遅延読み込み。2.7.1 で設定書き込みの信頼性と GC 世代管理を補強 |
| **2.8** | 権限と通信のスケルトン：3次元スコープ体系（scope）、インタラクションセッションインフラ（リース / チェックポイント / メッセージトランザクション / セッション受信箱 transcript）、モジュール間 RPC のプロトコル化（`module.call` / `meta.services` サービス契約 / 宛先指定イベント emit(to=)）、マルチバックエンド非同期ストレージ（sqlite / mysql / postgres、接続失敗時にフレームワークをブロックしない）、所有権クリーンアップ、設定コメントの保持。2.8.x の後続バージョンは CLI スキャフォールド、サブコマンドなどの磨き込み |
| **2.9** | 「モジュール開発体験」メインライン（EPRFC-2026-001）：宣言型コマンドパラメータ（`args=` / `options=`）とコマンドガバナンス（`cooldown=` / `rate_limit=`）、統一依存性注入（`Depends`）、ミドルウェアによるイベント拒否権、内蔵 ORM（自動マイグレーション + リレーションマッピング）、シャドウモジュールのグレースケール昇格、ディスパッチ決定チェーンの追跡とトラブルシューティング診断、Python 3.14 の正式サポート |
| **2.10** | 接続のファーストクラスリソース化（`connections` レジストリ：ブロードキャスト / ビジネスグループ / モジュール間受け渡しでの再利用 / アンロード時の自動回収）、ルートインポート契約（常用 API はすべて `from ErisPulse import` で可能）、所有権体系の補完、受信箱保持ポリシーのランタイムオーバーライド。2.10.2 でアダプターのローカルプラグインディレクトリ（`plugins/`）+ `epsdk create pack` + tomlclass による損失なしの設定書き込み |
| **2.11**（dev） | 「コードを変更 → 結果を確認」の開発ループ：ホットリロードのデフォルト全量セマンティクス（構文プリチェック + コード同一性の照合 + 依存モジュールのカスケード再エクスポート）、遅延読み込みスリープ（`dormant_after`）、アダプターのコードレベルホットリロード（`sdk.adapter.reload`）、`.got()` コマンドフロー糖衣構文、`epsdk stop` / `restart` によるランタイム制御 |
| **2.12**（dev） | ライフサイクルガバナンスと運用性：ネストされたライフサイクル（`ownership.nest()`）、きめ細かなホットリロード（単一モジュール/単一アダプターの判定、フレームワークソースの変更はプロセス再起動へ）、バックグラウンドタスクの送信待ちキュー、イベントディスパッチチェーンのアカウント自動バインド（`send_context` / `api_context` / `request_context` が同一基準、マルチアカウントモジュールは変更ゼロ）、アカウント横断の重複受付関連付け（`framework.cross_account_policy`）、シャドウモジュールの whl 取り込みと永続化昇格の閉ループ、コンテナ内での `epsdk restart` によるプロセス内ソフト再起動、`SendDSL.Location()` |

## 開発方式

ErisPulse は2つの開発方式をサポートしています：

- **モジュール開発（推奨）**：独立したモジュールパッケージを作成し、パッケージマネージャーでインストールします。配布と管理が容易になります。
- **組み込み開発**：プロジェクト内に直接ハンドラーを記述する方式で、迅速なプロトタイピングに適しています。詳しくは[クイックスタート](quick-start.md)をご覧ください。

## その他

- [ドキュメントスタイルガイド](styleguide/docstring.md) — ドキュメント貢献時の執筆規範
- [ErisPulse への貢献](contributing/README.md) — プロジェクト共同構築への参加入口
- [AI 支援による開発](ai-support/README.md) — AI コーディングアシスタントで使えるプロジェクトプロンプトの入手

## ヘルプの入手

- GitHub リポジトリ：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題の報告：Issue の提出
- 技術ディスカッション：Discussions を参照

## 関連リンク

- [OneBot12 標準](https://12.onebot.dev/)
- [云湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)