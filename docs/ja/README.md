# ErisPulse ドキュメント

ErisPulse はイベント駆動型のモジュール式非同期ボットフレームワークです。ビジネスコードは一度だけ書けば、アダプターを通じて QQ、Telegram、Kook、云湖（Yunhu）など複数のプラットフォームにデプロイでき、プラグインシステム、ホットリロード、完全な開発者ツールチェーンがすぐに使えます。

> **初めてのご利用ですか？** [5 分クイックスタート](quick-start.md) を直接ご覧ください —— インストールから最初のボットの実行まで、一気通貫で完了します。

---

## 自分に合ったパスを選ぶ

目標に応じて、対応する学習パスを選択してください。各パスの内部は基礎から応用へと順に並んでいます。

> [!IMPORTANT]
> **すべてのドキュメントを読み通す必要はありません。** 大多数の開発者は、**L1 コア 5 編**を順番に読み終えるだけ
> （約 1〜2 時間）で、機能の 90% を独自に開発できるようになります。残りのドキュメントは、すべて特定のシナリオ向けの
> 必要に応じた参照資料です——対応するニーズが生じたときに読めばよく、各編の冒頭には「いつこの編を読むべきか」が記載されています。
>
> **L1 コア 5 編**：[モジュール開発入門](developer-guide/modules/getting-started.md)
> → [基本概念](getting-started/basic-concepts.md)
> → [Event ラッパークラス](developer-guide/modules/event-wrapper.md)
> → [設定ファイルの説明](user-guide/configuration.md)
> → [例外キャッチ](advanced/errors.md)
>
> アダプター作者にはさらに以下が必要です：[アダプター開発入門](developer-guide/adapters/getting-started.md)
> → [イベントコンバーター](developer-guide/adapters/converter.md)
> → [SendDSL 詳解](developer-guide/adapters/send-dsl.md)

### 一、ボットを使いたい

ボットを動かし、モジュールをインストールし、設定を行います。

| 進捗 | ドキュメント | 説明 |
|------|------|------|
| **① 入門** | [5 分クイックスタート](quick-start.md) | インストール、初期化、実行 —— 唯一のスタート地点 |
| App 直インストール | [ErisPulse-App クライアント](ecosystem/app.md) | 公式全プラットフォームクライアント：スマホ / PC の GUI で直接実行・管理でき、ターミナル不要 |
| ② 深掘り | [最初のボットを作成する](getting-started/first-bot.md) | 最初のコマンドハンドラーを書く |
| ③ 概念 | [基本概念](getting-started/basic-concepts.md) | アダプター / モジュール / イベントの設計を理解する |
| ④ 実践 | [よくあるタスクの例](getting-started/common-tasks.md) | ストレージ、定時タスク、権限制御 |
| 参考 | [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイガイド](user-guide/deployment.md) | 必要に応じて参照 |
| 参考 | [プラットフォーム特性ガイド](platform-guide/README.md) | 各プラットフォーム（云湖/QQ/Telegram…）の差異 |
| 選定 | [選定ガイド](showcase/README.md) | NoneBot2 / AstrBot / LangBot との比較と移行 |

### 二、モジュール / アダプターを開発したい

ErisPulse 向けの配布可能な拡張を書きます。

| 種類 | 入門 | 応用 |
|------|------|------|
| **モジュール開発**（推奨） | [モジュール開発入門](developer-guide/modules/getting-started.md) | [コア概念](developer-guide/modules/core-concepts.md) · [Event ラッパークラス](developer-guide/modules/event-wrapper.md) · [ベストプラクティス](developer-guide/modules/best-practices.md) |
| **アダプター開発** | [アダプター開発入門](developer-guide/adapters/getting-started.md) | [コア概念](developer-guide/adapters/core-concepts.md) · [SendDSL 詳解](developer-guide/adapters/send-dsl.md) · [イベントコンバーター](developer-guide/adapters/converter.md) · [ベストプラクティス](developer-guide/adapters/best-practices.md) |
| **技術標準** | [標準仕様の概要](standards/README.md) | アダプター開発が従わなければならない [セッションタイプ](standards/session-types.md) · [イベント変換](standards/event-conversion.md) · [送信メソッド](standards/send-method-spec.md) · [API レスポンス](standards/api-response.md) · [リクエスト操作](standards/request-action-spec.md) 仕様 |
| **テストとトラブルシューティング** | [モジュールテスト（ErisPulse-Testing）](developer-guide/testing.md) | ディスパッチ決定チェーンで「コマンドがなぜ発火しなかったのか」を調査 |
| **公開** | [公開とモジュールストア](developer-guide/publishing.md) | 作品を PyPI とモジュールストアに公開する |

### 三、仕組みを深く理解したい

フレームワーク内部がどのように動作するかを理解します。まずアーキテクチャと API リファレンスを確認し、その後、下の対応表に従って各トピックに進んでください。

**アーキテクチャと API リファレンス**

| ドキュメント | 説明 |
|------|------|
| [アーキテクチャ概要](architecture.md) | 可視化図表：コアアーキテクチャ、初期化フロー、イベント処理、ライフサイクル、モジュール読み込み戦略（`activate_on` によるイベント駆動の遅延アクティベーションを含む）、ローカルプラグインフォルダとモジュールホットリロードアーキテクチャ（すべてのモジュールソースに対応） |
| [イベントシステム](api-reference/event-system.md) | 5 大カテゴリのイベントに対する完全な API |
| [アダプターシステム](api-reference/adapter-system.md) | アダプターの登録、起動・停止、API 呼び出し |
| [コアモジュール](api-reference/core-modules.md) | Storage / Config / Logger / Router などの基礎機能 |

**L2 必読（本番レベルのモジュールを書くなら必須）**

| ドキュメント | 説明 |
|------|------|
| [スコープ（scope）](advanced/scope.md) | 三次元スコープ制御：モジュール可用性 / イベント准入 / 発信アクション制限（メソッドレベルの細粒度ルール、バインド継承の merge を含む） |
| [所有権（owner）システム](advanced/ownership.md) | リソースの所有と自動回収：owner コンテキスト、所有リソースの全体像、アンロード時のクリーンアップシーケンス、設計境界とモジュール作者ガイド |
| [ライフサイクル管理](advanced/lifecycle.md) | ライフサイクルイベントシステム：モジュール / アダプターの読み込み、アンロード、リロード、無効化時にそれぞれ何をすべきか |
| [インタラクションセッションシステム](advanced/interaction.md) | wait_reply 完全解説、セッションタイマー（remind / escalate）、マルチウェイ待機（select）、セッション排他リース、インボックス、メッセージトランザクション、トレーシング |

**シナリオ別グループ（必要に応じて参照）**

| グループ | ドキュメント | 最初の 1 編を理解しないと陥る落とし穴 |
|------|------|------|
| 実行と起動 | [起動フローと手動制御](advanced/startup.md) · [遅延読み込み](advanced/lazy-loading.md) | 起動チェーン（Finder / Loader / Manager / Router）を理解していないと、モジュールの読み込み失敗時にログをただ眺めるしかありません |
| 通信と接続 | [モジュール間通信](advanced/module-communication.md) · [コネクションプールとブロードキャスト](advanced/connections.md) · [ルーティングシステム](advanced/router.md) | サービス契約（`meta.services`）のホワイトリストを理解していないと、モジュール間の `module.call` が `ServiceNotProvidedError` で拒否されても理由が分かりません |
| データストレージ | [ストレージバックエンド](advanced/storage-backends.md) · [SQL ビルダー](advanced/sql-builder.md) · [HTTP クライアント](advanced/http-client.md) | 接続失敗時のクールダウン期間のセマンティクスを理解していないと、データベースの不安定時に「フレームワークが壊れた」と誤判断します（実際はストレージ操作がフェイルファストし、クールダウン後に自動再接続される仕様です） |
| メッセージと対話 | [Conversation マルチターン対話](advanced/conversation.md) · [セッションインボックス](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [国際化](advanced/i18n.md) | セッション排他リースを理解していないと、2 つのモジュールが同じユーザーの返信を同時に待つと互いに追い出し合います |
| シャドウカナリア | [シャドウモジュールとカナリア昇格](advanced/shadow.md) | 5 つの隔離ゲートを理解しないまま早期昇格すると、シャドウの発信メッセージが実ユーザーへ漏れ出ます |

**概念の関係一覧表**

どのサブシステムが何を担当しているのか分からないときは、この表で当てはまるものを探してください：

| サブシステム | どんな問題に答えるか | 一言まとめ |
|--------|------------|-----------|
| [通信](advanced/module-communication.md)（module-communication） | モジュール同士はどうやって相互呼び出しやイベントの宛先指定送信をするのか？ | モジュール間は `module.call` を使う。相手が `meta.services` を宣言している場合は、ホワイトリスト内のメソッドしか呼び出せない |
| [権限](advanced/scope.md)（scope） | このモジュールを誰が使えるか、誰がイベントを発火できるか、どんなアクションを実行できるか？ | 3 つのゲート——モジュールバインド、ID 准入、発信制限。すべてユーザー設定で決まる |
| [所有](advanced/ownership.md)（ownership） | モジュールのアンロード後、それが開いた接続、タイマー、サブスクリプションはどうなるのか？ | 登録した者が所有し、アンロード時に回収。ぶら下がりリソースは残さない |
| [遅延読み込みとスリープ](advanced/lazy-loading.md)（lazy-loading） | モジュールはいつ実際に読み込まれ、アイドル後はどうなるのか？ | `activate_on` で使うときに起床、`dormant_after` でアイドル時にスリープ |
| [インタラクション](advanced/interaction.md)（interaction） | ユーザーの次の返信をどう待つか、複数ターンの収集はどう書くか？ | `wait_reply` で 1 件待ち、`.got()` チェーンで複数ターンを収集。リースが競合を防ぐ |
| [シャドウカナリア](advanced/shadow.md)（shadow） | 新バージョンのモジュールを本番に影響を与えずに試験運用するには？ | シャドウはコピーを受信し、発信は記録のみ。`promote` は人の確認があって初めて昇格 |
| [ストレージ](advanced/storage-backends.md)（storage-backends） | データはどこに保存され、バックエンドはどう切り替えるのか？ | 同一のストレージ API で、sqlite / mysql / postgres を設定で切り替え |

### 四、エコシステムと公式クライアント

公式クライアント + 必要に応じてインストールでき、入れたらすぐ使えるエコシステムモジュール（いずれもフレームワークの組み込み機能ではありません）。

| ドキュメント | 説明 |
|------|------|
| [エコシステム概要](ecosystem/README.md) | エコシステムモジュールのインストール方法、これらが組み込み機能でない理由 |
| [ErisPulse-QvQChat](ecosystem/qvqchat.md) | 汎用エージェントモジュール：ツールループ / MCP / 長期記憶 / ナレッジベース。サービスを宣言したモジュールは自動的に AI ツールになります |
| [ErisPulse-ApiMCP](ecosystem/apimcp.md) | ボットを逆に MCP ツールとして公開し、Claude などの AI クライアントから直接操作できるようにします |
| [ErisPulse-App](ecosystem/app.md) | 公式全プラットフォームクライアント（Android / Windows / Linux / macOS）：ネイティブ UI で複数インスタンスを管理、**スマホで直接実行**可能、デスクトップのトレイに常駐 |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web 管理パネル + ビュー登録 API（モジュールはサイドバーへカスタムページを登録できます） |
| [ErisPulse-Cron](ecosystem/cron.md) | 定時タスクスケジューリングモジュール：単発 / インターバル / Cron 式、コールバックへの引数渡し、SQLite 永続化。他のモジュールは定時コールバックを委託可能 |
| [ErisPulse-Takumi](ecosystem/takumi.md) | 画像レンダリング（HTML / ノードツリー / SVG / アニメーション、中国語・英語フォント内蔵） |

### 五、ErisPulse に貢献したい

フレームワークをより良くする。

| ドキュメント | 説明 |
|------|------|
| [ErisPulse への貢献](contributing/README.md) | 貢献方法の概要：ドキュメント / i18n / バグ / モジュール / アダプター |
| [初めての貢献](contributing/first-contribution.md) | fork から PR の提出まで |

---

## 高度な機能のバージョン早見表

バージョン互換性の判断や、古いプロジェクトを引き継いだ際に「この機能はどのバージョンで導入されたのか」を知りたいときは、この表で確認してください（内容はリポジトリルートの [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md) の各バージョンエントリが正とします）。

| バージョン | 導入された機能 |
|------|-----------|
| **2.7** | 本番対応基盤：OneBot12 標準化基底クラス（`ApiDSL` / `BaseConverter`）、設定ホットリロードの体系化、グレースフルシャットダウンと SIGTERM/SIGHUP シグナル処理、環境変数による設定上書き、ライフサイクルコールバックフック、Web スタックの遅延読み込み。2.7.1 で設定書き込みの信頼性と GC 世代別管理を補完 |
| **2.8** | 権限と通信の骨格：スコープ三次元体系（scope）、インタラクションセッション基盤（リース / チェックポイント / メッセージトランザクション / セッションインボックス transcript）、モジュール間 RPC のプロトコル化（`module.call` / `meta.services` サービス契約 / 宛先指定イベント emit(to=)）、マルチバックエンド非同期ストレージ（sqlite / mysql / postgres、接続失敗でもフレームワークをブロックしない）、所有権クリーンアップ、設定コメントの保持。2.8.x の後続バージョンは CLI スキャフォールドやサブコマンドなどの改良 |
| **2.9** | 「モジュール開発体験」メインライン（EPRFC-2026-001）：宣言型コマンドパラメータ（`args=` / `options=`）とコマンドガバナンス（`cooldown=` / `rate_limit=`）、統一された依存性注入（`Depends`）、ミドルウェアによるイベント否決権、組み込み ORM（自動マイグレーション + リレーションマッピング）、シャドウモジュールのカナリア昇格、ディスパッチ決定チェーンのトレーシングと診断、Python 3.14 の正式サポート |
| **2.10** | 接続のファーストクラスリソース化（`connections` レジストリ：ブロードキャスト / ビジネスグループ / モジュール間の受け渡しと再利用 / アンロード時の自動回収）、ルートインポート契約（主要 API はすべて `from ErisPulse import` で利用可能）、所有権体系の補完、インボックス保持ポリシーのランタイム上書き。2.10.2 でアダプターのローカルプラグインディレクトリ（`plugins/`）+ `epsdk create pack` + tomlclass による非破壊設定書き込み |
| **2.11**（dev） | 「コード変更 → 結果確認」の開発ループ：ホットリロードのデフォルト全量セマンティクス（構文プリチェック + コード同一性の照合 + 依存モジュールのカスケード再インポート）、遅延読み込みスリープ（`dormant_after`）、アダプターのコードレベルホットリロード（`sdk.adapter.reload`）、`.got()` コマンドフロー糖衣構文、`epsdk stop` / `restart` によるランタイム制御 |

## 開発方式

ErisPulse は 2 つの開発方式をサポートしています：

- **モジュール開発（推奨）**：独立したモジュールパッケージを作成し、パッケージマネージャーでインストールすることで、配布と管理が容易になります。
- **埋め込み開発**：プロジェクト内に直接ハンドラーを記述します。迅速なプロトタイピングに適しています。詳細は [クイックスタート](quick-start.md) をご覧ください。

## その他

- [ドキュメントスタイルガイド](styleguide/docstring.md) — ドキュメント貢献時の執筆規範
- [ErisPulse への貢献](contributing/README.md) — プロジェクトの共同開発に参加する入口
- [AI 支援開発](ai-support/README.md) — AI コーディングアシスタント向けのプロジェクトプロンプトの入手

## ヘルプの入手

- GitHub リポジトリ：[https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- 問題の報告：Issue の提出
- 技術的な議論：Discussions の参照

## 関連リンク

- [OneBot12 標準](https://12.onebot.dev/)
- [云湖公式ドキュメント](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)