---
name: erispulse-getting-started
description: "适用于：第一次接触 ErisPulse，想从零跑起一个机器人并理解核心概念。覆盖场景：ErisPulse は、イベント駆動型のモジュラーアシンクロナスロボットフレームワークです。ビジネスロジックを一度だけ記述し、アダプターを介して QQ、Telegram、Kook、雲湖など複数のプラットフォームにデプロイできます。プラグインシステム、ホットリロード、完全な開発者ツールチェーンがすぐに利用可能です。**1. インストール**（Python >= 3.10）：。**この記事を読むタイミング**：ロボットが動作している状態で、最初の `/hello` コマンドハンドラを実装し、`sdk.run` とコマンドデコレータがそれぞれ何をしているのかを理解したい場合。まだ ErisPulse をインストールしておらず、プロジェクトを初期化していない場合は、まず [5 分間クイックスタート](../quick-start.md) の「インストール」「プロジェクトの初期化」「プロジェクトの実行」の 3 ステップを完了してください。必要ない場合はスキップしてください。ユーザーがメッセージを送ってからボットが返信するまでの間に、どのようなコンポーネントを経由するのでしょうか？アダプターとモジュールはそれぞれ何を担当しているのでしょうか？この記事を読み終えれば、ハンドラーを書く際に直面する設計上の問題を自力で答えられるようになり、例をただ写すだけではなくなります。**このドキュメントを読むべきタイミング**：ボットにメッセージ、コマンド、通知、リクエストへ応答させたい場合や、返信の待機 / マルチターン会話の実装、「コマンドがトリガーされないのはなぜか」のトラブルシューティングが必要なときに読んでください。フレームワークの設計だけを知りたい場合は、[基本概念](basic-concepts.md) を参照すれば十分です。必要なければスキップしてください。**この章を読むタイミング**：ロボットに特定の機能を追加したいときは、各節を参照してください。永続化、定期タスク、メッセージフィルタ、権限制御、一括送信など、各節は直接コピーできる完全な例です。イベント処理の書き方を体系的に学びたい場合は [イベント処理入門](event-handling.md) を先にご覧ください。必要なければ飛ばしてください。**このドキュメントを読むべきケ..."
---

# ErisPulse 快速上手与核心概念

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 文档总入口与阅读路径

> 来源: `docs/ja/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/README.md）

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

## 快速开始

> 来源: `docs/ja/quick-start.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/quick-start.md）

# 速習

> **これが最初の一歩です。** 5 分でゼロから ErisPulse ロボットを起動しましょう。まずは効果を見て、その後各ステップを詳しく説明します。

## 60 秒効果：まずロボットが 1 文だけ返信するようにする

**1. インストール**（Python >= 3.10）：

```bash
pip install ErisPulse
```

**2. プロジェクトの初期化**。ウィザードがプロジェクト名の設定、プラットフォームアダプターの選択、および設定の完了を促し、`main.py` と `config/config.toml` を生成します：

```bash
epsdk init
```

**3. `main.py` を開き、以下の 9 行のコードに置き換えます**：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("ping", help="ロボットがオンラインかどうかをテストする")
async def ping_handler(event):
    await event.reply("Pong！ロボットは正常に動作しています。")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

**4. 実行**：

```bash
epsdk run main.py
```

ターミナルには、フレームワークの起動ログとアダプターの接続情報が出力されます。この時点で、接続したプラットフォームでロボットに `/ping` を送信すると、以下のように返信されます：

> Pong！ロボットは正常に動作しています。

この返信が見られれば、フレームワーク、アダプター、イベント処理の連携が確立されたことを意味します。連携がうまくいかない場合は、文末の[問題が発生した場合](#問題が発生した場合)を参照してください。うまくいく場合は、各ステップの選択肢についても以下に説明します。

## ErisPulse のインストール：3 つの方法

上記では最も直接的な pip を使用しています。環境に応じて選択してください。

### pip を使用したインストール

Python のバージョンが 3.10 以上であることを確認し、pip を使用してインストールします：

```bash
pip install ErisPulse
```

既に [uv](https://github.com/astral-sh/uv) をインストールしている場合は、`uv pip install ErisPulse` を使用して、より高速にインストールできます。

プロジェクト環境を汚染せずに `epsdk` コマンドラインツールをグローバルにインストールしたい場合は、`uv tool install` を推奨します：

```bash
uv tool install ErisPulse
```

インストール後、`epsdk` はグローバルに利用可能になります。プロジェクトディレクトリ内で実行すると、プロジェクトの `.venv` を自動的に感知し、`epsdk install` でプロジェクト環境にインストールし、`epsdk run` でプロジェクト環境で実行されます。フレームワーク本体はツール環境から提供されます。詳しくは[インストールの参考](user-guide/installation.md)を参照してください。

### 1 つでインストールするスクリプト（新規環境に推奨）

インストールスクリプトは、環境（Docker、Python、uv）を自動検出し、最適なインストール方法を選択するよう誘導します。多言語（中国語/English/日本語/Русский/繁体中国語）に対応しています。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

スクリプトは以下を完了するよう誘導します：

- **Docker インストール**（Docker が検出された場合に推奨）：イメージソース（Docker Hub / GHCR）、バージョンチャネル（安定版 / プレビュー版）、Dashboard 管理パネルの設定、ポートの設定を選択
- **グローバル CLI インストール（uv tool、推奨）**：`epsdk` をグローバルコマンドとしてインストールし、仮想環境を必要とせず、uv が Python を自動管理します（システムのバージョンが低くても可能です）；プロジェクトディレクトリ内で実行すると、プロジェクトの `.venv` を自動的に感知します
- **従来のインストール**：自動的に仮想環境を作成し、ErisPulse のバージョンを選択し、オプションで Dashboard 管理パネルモジュールをインストールできます

### Docker を使用する

Docker イメージには、ErisPulse フレームワークと Dashboard 管理パネルが事前インストールされており、`linux/amd64` および `linux/arm64` アーキテクチャをサポートしています。

```bash
# docker-compose.yml をダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard トークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub が利用できない場合？</summary>

GitHub Container Registry のイメージを使用する場合は、`docker-compose.yml` の image を次のように変更します：

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

起動後、`http://<host>:8000/Dashboard` にアクセスし、設定したトークンでログインします。

## プロジェクトの初期化

### インタラクティブな初期化（推奨）

```bash
epsdk init
```

これにより、インタラクティブなガイドが起動し、以下の手順をガイドします：
- プロジェクト名の設定
- ログレベルの設定
- サーバー設定（ホストとポート）
- アダプターの選択と設定
- プロジェクト構造の作成

### ファスト初期化

```bash
# プロジェクト名を指定する高速モード
epsdk init -q -n my_bot

# または、プロジェクト名のみを指定
epsdk init -n my_bot
```

### 手動でのプロジェクト作成

手動でプロジェクトを作成したい場合は：

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## モジュールのインストール

### CLI によるインストール

```bash
epsdk install Yunhu AIChat
```

### 利用可能なモジュールの確認

```bash
epsdk list-remote
```

### インタラクティブなインストール

パッケージ名を指定しない場合、インタラクティブなインストール画面に移行します。

```bash
epsdk install
```

## プロジェクトの実行

```bash
# 通常実行
epsdk run main.py

# ホットリロードモード（開発時に推奨）
epsdk run main.py --reload
```

## IDE補完の有効化（オプション）

ErisPulse はモジュール/アダプターを動的に発見するため、IDE はデフォルトではプラットフォーム固有のメソッドを補完できません。  
以下のコマンドを実行して型のスタブを生成してください：

```bash
epsdk types
```

生成後、インポートした型を変数の型ヒントとして使用することで、正確な補完が得られます（詳細は [IDE補完ガイド](./getting-started/ide-completion.md) を参照してください）：

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # プラットフォーム固有のメソッドの補完
```

## プロジェクト構造

初期化後のプロジェクト構造：

```
my_bot/
├── config/
│   └── config.toml          # 設定ファイル
└── main.py                  # エントリーファイル

```

## 設定ファイル

基本的な `config.toml` 設定：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# アダプターの設定
```

## 次のステップ

ロボットが起動したら、目的に応じて選択してください：

### グループ用ロボットを作りたい（メッセージ処理、グループ管理、通知）

- [イベント処理の入門](getting-started/event-handling.md) — メッセージ、通知、リクエストイベントの書き方
- [一般的なタスクの例](getting-started/common-tasks.md) — ストレージ、定期タスク、権限制御

### 自分のモジュール / アダプターを書きたい

- [基本概念](getting-started/basic-concepts.md) — アダプター / モジュール / イベントの設計を理解する
- [モジュール開発の入門](developer-guide/modules/getting-started.md)
- [アダプター開発の入門](developer-guide/adapters/getting-started.md)
- [アーキテクチャ概要](architecture.md) — 可視化されたアーキテクチャ図

### ロボットを長期的に動かしたい

- [デプロイガイド](user-guide/deployment.md)
- [設定ファイルの説明](user-guide/configuration.md)

### 問題に遭遇した場合

- [最初のロボットを作成する](getting-started/first-bot.md) — 最初のロボットの詳細な手順
- [起動プロセスと手動制御](advanced/startup.md) — モジュール / アダプターのロード失敗の診断
- [CLIコマンドリファレンス](user-guide/cli-reference.md) — `epsdk` のすべてのサブコマンド

## 第一个机器人

> 来源: `docs/ja/getting-started/first-bot.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/getting-started/first-bot.md）

# 最初のロボットを作成する

> [!TIP]
> **この記事を読むタイミング**：ロボットが動作している状態で、最初の `/hello` コマンドハンドラを実装し、`sdk.run` とコマンドデコレータがそれぞれ何をしているのかを理解したい場合。まだ ErisPulse をインストールしておらず、プロジェクトを初期化していない場合は、まず [5 分間クイックスタート](../quick-start.md) の「インストール」「プロジェクトの初期化」「プロジェクトの実行」の 3 ステップを完了してください。必要ない場合はスキップしてください。

クイックスタートを実行したのは第一歩です。この記事では、最初のコマンドハンドラを実装し、フレームワーク内で各行のコードが何を行っているのかを解説します。

## 最初のステップ：最初のコマンドを記述する

`main.py` を開き、シンプルなコマンドハンドラを記述します。

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="挨拶メッセージを送信します")
async def hello_handler(event):
    """hello コマンドを処理します"""
    user_name = event.get_user_nickname() or "友達"
    await event.reply(f"こんにちは、{user_name}！私は ErisPulse ロボットです。")

@command("ping", help="ロボットがオンラインかどうかをテストします")
async def ping_handler(event):
    """ping コマンドを処理します"""
    await event.reply("Pong！ロボットは正常に動作しています。")

async def main():
    """メインエントリーポイント関数"""
    print("ErisPulse を起動しています...")
    
    # keep_running=True（デフォルト）：フレームワークはブロックして実行を維持し、終了信号（例：Ctrl+C）が受信されるまで待ちます
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### `keep_running` パラメータ

`sdk.run(keep_running)` は、フレームワークがブロックして実行を維持するかどうかを制御します。

- **`keep_running=True`（デフォルト）**：`run()` はブロックし続け、終了信号（例：Ctrl+C）が受信されるまで待ちます。これは純粋な bot アプリケーションに適しています。
- **`keep_running=False`**：`run()` は初期化後に即座に返ります。**フレームワークはアンロードされません**——起動されたアダプタ/モジュールはバックグラウンドタスクとしてメッセージイベントの処理を続けます。その後、独自のロジックを実行し、イベントループが終了するまでフレームワークは閉じられません。例：

```python
async def main():
    await sdk.run(keep_running=False)   # 初期化後に即座に返ります
    # フレームワークはバックグラウンドで実行中です。ここでは他の処理を続行できます
    while True:
        await asyncio.sleep(3600)
        print("1時間ごとにチェックします")
```

> `run()` の2つのモードに加えて、`init()`/`uninit()` を使用したライフサイクルの手動制御、個別のアダプタ/ルーティングの起動/停止など、より細かい制御方法もあります。詳細は [起動プロセスと手動制御](../advanced/startup.md) を参照してください。

## 第二ステップ：ロボットの実行

```bash
# 通常実行
epsdk run main.py

# 開発モード（ホットリロードをサポート）
epsdk run main.py --reload
```

## 第三段階：ロボットのテスト

チャットプラットフォームで次のコマンドを送信します：

```
/hello
```

これで、ロボットからの返信が届くはずです。

## コード説明

### コマンドデコレータ

```python
@command("hello", help="挨拶メッセージを送信")
```

- `hello`：コマンド名。ユーザーは `/hello` で呼び出します。
- `help`：コマンドのヘルプ説明。`/help` コマンドで表示されます。

### イベントパラメータ

```python
async def hello_handler(event):
```

`event` パラメータは Event オブジェクトであり、以下を含みます：
- メッセージ内容：`event.get_text()`
- 送信者情報：`event.get_user_id()`、`event.get_user_nickname()`
- プラットフォーム情報：`event.get_platform()`
- グループ情報：`event.get_group_id()`
- 元のデータ：`event.get_raw()`

> 完全な Event オブジェクトのメソッドについては、[Event 包装クラスの詳細](../developer-guide/modules/event-wrapper.md) を参照してください。

### レスポンスの送信

```python
await event.reply("レスポンスの内容")
```

`event.reply()` は、送信者にメッセージを送信するための便利なメソッドです。

## 拡張機能：追加の機能を追加

ErisPulse は、豊富なイベント処理とデータ処理機能を提供します：

- **メッセージの監視**：`@message.on_message()` を使用して、さまざまなメッセージを監視します → [イベント処理の入門](event-handling.md)
- **通知の監視**：`@notice.on_friend_add()` などの通知を監視します → [イベント処理の入門](event-handling.md)
- **データの保存**：`sdk.storage.get/set` を使用してデータを永続化します → [一般的なタスクの例](common-tasks.md)

## よくある質問

### コマンドが反応しない？

1. アダプタが正しく設定されているか確認し、`config/config.toml` 内のアダプタの `status` が `true` であることを確認します。
2. ターミナルのログ出力を確認し、エラー情報（特に `ERROR` レベルのログ）がないか確認します。
3. コマンドのプレフィックスが正しいか確認します（デフォルトは `/` です）。設定ファイルの `[ErisPulse.event.command]` 部分で確認できます。
4. コマンド名のスペルが正しいか、大文字小文字の区別が正しく設定されているか確認します。

### コマンドのプレフィックスを変更するには？

`config.toml` に以下を追加します：

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### 複数のプラットフォームをサポートするには？

ErisPulse は OneBot12 標準を用いて、異なるプラットフォームのイベント形式を統一しています。`@command` および `@message` で登録されたハンドラは、すべてのプラットフォームからのイベントを自動的に受け取ります。イベントの元プラットフォームを区別するには、`event.get_platform()` を使用します：

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("你好！来自云湖")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("你好！")
```

> 詳細な多プラットフォーム対応のテクニックについては、[よくあるタスクの例](common-tasks.md#多プラットフォーム適応) を参照してください。

## 次のステップ

- **学習の流れに従って進む**：[基本概念](basic-concepts.md)を読んで、コマンドプロセッサの背後でフレームワークが何をしているかを理解する
- **より多くのメッセージタイプに対応したい**：[イベント処理の入門](event-handling.md)、メッセージ / 通知 / 要求 / メタイベントのハンドラの書き方
- **実用的な機能を追加したい**：[一般的なタスクの例](common-tasks.md)、永続化、定時タスク、権限制御の既製コード

## 基础概念

> 来源: `docs/ja/getting-started/basic-concepts.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/getting-started/basic-concepts.md）

# 基本概念

> [!NOTE]
> **L1 コア必読**——ドキュメントトップページの「L1 コア5編」のうちの第2編（モジュール開発入門 → **基本概念** → Event ラッパークラス → 設定ファイルの説明 → 例外キャッチ）。

ユーザーがメッセージを送ってからボットが返信するまでの間に、どのようなコンポーネントを経由するのでしょうか？アダプターとモジュールはそれぞれ何を担当しているのでしょうか？この記事を読み終えれば、ハンドラーを書く際に直面する設計上の問題を自力で答えられるようになり、例をただ写すだけではなくなります。

## イベント駆動アーキテクチャ

ErisPulse はイベント駆動アーキテクチャを採用しており、すべての対話はイベントを通じて伝達・処理されます。

### イベントフロー

```
ユーザーがメッセージを送信
      │
      ▼
プラットフォームが受信
      │
      ▼
アダプターがプラットフォームのネイティブイベントを受信
      │
      ▼
OneBot12 標準イベントに変換
      │
      ▼
イベントシステムへ送出
      │
      ▼
登録済みのハンドラーに配信
      │
      ▼
モジュールがイベントを処理
      │
      ▼
アダプターを通じてレスポンスを送信
      │
      ▼
プラットフォームがユーザーに表示
```

### OneBot12 標準

ErisPulse は OneBot12 をコアイベント標準として使用しています。OneBot12 は汎用のチャットボットアプリケーションインターフェース標準であり、統一されたイベント形式を定義しています。

すべてのアダプターはプラットフォーム固有のイベントを OneBot12 形式に変換し、コードの一貫性を保証します。

## コアコンポーネント

### 1. SDK オブジェクト

SDK はすべての機能の統一されたエントリーポイントであり、コアコンポーネントへのアクセスを提供します。

```python
from ErisPulse import sdk

# コアモジュールへのアクセス
sdk.storage    # ストレージシステム
sdk.config     # 設定システム
sdk.logger     # ログシステム
sdk.adapter    # アダプターシステム
sdk.module     # モジュールシステム
sdk.router     # ルーティングシステム
sdk.client     # HTTPクライアント
sdk.lifecycle  # ライフサイクルシステム
```

> [!WARNING]
> **ルートから一括インポート**：`from ErisPulse.Core import adapter` / `import ErisPulse.Core.adapter`
> これらの書き方は**マネージャーインスタンス**（`AdapterManager` シングルトン）にバインドされます。`ErisPulse.Core`
> パッケージの再エクスポートは同名のサブモジュールを覆い隠します。テスト、パッチ、またはモジュールオブジェクト自体が必要な場合は、
> 一律 `from ErisPulse import sdk` ルートインポート（`sdk.adapter` はマネージャーインスタンス）を使用してください。

### 2. Event オブジェクト

Event オブジェクトはイベントデータをラップし、便利なアクセスメソッドを提供します。

```python
@command("info")
async def info_handler(event):
    # イベント情報を取得
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # レスポンスを送信
    await event.reply(f"ユーザー: {user_id}, プラットフォーム: {platform}")
```

### 3. アダプター

アダプターは ErisPulse と外部プラットフォームの間のブリッジです。

**役割：**
- プラットフォームのネイティブイベントを受け取る
- OneBot12 標準形式に変換する
- 標準形式のイベントをプラットフォームに送信する

**例のアダプター：**
- Yunhu アダプター：雲湖プラットフォームとの通信
- Telegram アダプター：Telegram Bot API との通信
- OneBot11 アダプター：OneBot11 兼容アプリとの通信
- Email アダプター：メールの送受信処理

### 4. モジュール

モジュールは機能拡張の基本単位であり、以下を実現できます：
- イベントハンドラの登録
- ビジネスロジックの実装
- アダプターを呼び出してメッセージを送信
- コアモジュールが提供するサービスの利用

#### モジュール発見メカニズム

ErisPulse は Python の `importlib.metadata.entry_points` を使用して、インストール済みのモジュールを発見します。モジュールは `pyproject.toml` でエントリーポイントを宣言します：

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

SDK の初期化時に、`erispulse.module` グループのすべてのエントリーポイントをスキャンし、モジュールクラスを `ModuleManager` に登録し、依存関係に基づいてトポロジカルソートした後、順次初期化します。

#### 最小限のモジュール

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("モジュールがロードされました")

    async def on_unload(self, event):
        self.logger.info("モジュールがアンロードされました")
```

#### モジュールのライフサイクル

- **登録**：SDK がモジュールクラスを発見し、マネージャーに登録
- **ロード**：モジュールインスタンスを作成し、`on_load(event)` を呼び出す（`event = {"module_name": "MyModule"}`）
- **アンロード**：`on_unload(event)` を呼び出し、リソースをクリーンアップ

#### ロード戦略

`get_load_strategy()` を使用して、モジュールのロード動作を宣言します：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # ラグジュアリーなロードかどうか（デフォルトは True）
            priority=0        # ロード優先度、数値が大きいほど初期化が早くなる
        )
```

- **`lazy_load=True`（デフォルト）**：`sdk.MyModule` に初めてアクセスしたときにモジュールを初期化し、起動時間を短縮
- **`lazy_load=False`**：SDK の起動時に即座に初期化し、ライフサイクルイベントを監視するか、定時タスクを実行するモジュールに適しています
- **`priority`**：同じ優先度のモジュールは登録順にロードされ、数値が大きいほど初期化が早くなります

> 詳細なラグジュアリーなロードの仕組みについては、[ラグジュアリーなロードシステム](../advanced/lazy-loading.md)を参照してください。

## イベントタイプ

ErisPulse は 5 種類のイベントをサポートしています：

| イベントタイプ | デコレーター | 説明 |
|---------|--------|------|
| メッセージイベント | `@message.on_message()` | ユーザーが送信したすべてのメッセージ（個人チャット、グループチャット） |
| コマンドイベント | `@command("name")` | コマンドプレフィックスで始まるメッセージ（例：`/hello`） |
| 通知イベント | `@notice.on_friend_add()` など | システム通知（フレンド追加、グループメンバーの変更など） |
| リクエストイベント | `@request.on_friend_request()` など | ユーザーリクエスト（フレンドリクエスト、グループ招待） |
| メタイベント | `@meta.on_connect()` など | システムレベルのイベント（接続、切断、ハートビート） |

> 各イベントタイプの詳細な使い方とコード例については、[イベント処理入門](event-handling.md) を参照してください。

## コアモジュールの説明

### Storage（ストレージ）

SQLite ベースのキーバリューストレージシステムで、データの永続化に使用します。

```python
# 値の設定
sdk.storage.set("key", "value")

# 値の取得
value = sdk.storage.get("key", "default_value")

# 一括操作
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# トランザクション
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config（設定）

TOML 形式の設定ファイル管理。

```python
# 設定の取得
config = sdk.config.getConfig("MyModule", {})

# 設定の保存
sdk.config.setConfig("MyModule", {"key": "value"})

# ネストされた設定の読み取り
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger（ログ）

モジュール化されたログシステム。

```python
# ログの記録
sdk.logger.info("これは情報メッセージです")
sdk.logger.warning("これは警告メッセージです")
sdk.logger.error("これはエラーメッセージです")

# 子ロガーの取得
child_logger = sdk.logger.get_child("submodule")
child_logger.info("サブモジュールのログ")
```

**属性アクセスのシンタックスシュガー**

`get_child()` メソッドを使用する以外に、**属性アクセス**の方法で子ロガーを作成することもできます。これはより簡潔な**シンタックスシュガー**の書き方です：

```python
# 属性アクセスで子ロガーを作成
sdk.logger.mymodule.info("モジュールメッセージ")

# ネストされたアクセスもサポート
sdk.logger.mymodule.database.info("データベースメッセージ")
```

### Router（ルーティング）

FastAPI + Uvicorn ベースの HTTP および WebSocket ルーティング管理。デコレータールーティング、ミドルウェア、グループ化、レート制限、CORS をサポートします。

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> ルーティング API の完全な情報（WebSocket、ミドルウェア、レート制限、CORS など）については、[ルートマネージャー](../advanced/router.md) を参照してください。

### Client（ネットワーククライアント）

統合されたネットワーククライアントで、HTTP リクエスト、WebSocket 接続、コネクションプール管理、自動リトライ、タイムアウト制御、リクエスト統計、ライフサイクルイベント統合を集約しています。

```python
from ErisPulse.Core import client

# HTTP リクエスト
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# リトライとタイムアウト付き
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket 接続
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

> ネットワーククライアント API の完全な情報については、[ネットワーククライアント](../advanced/http-client.md) を参照してください。

## SendDSL メッセージ送信

アダプターはチェーン呼び出しのメッセージ送信インターフェースを提供します。

### 基本的な送信

```python
# アダプターインスタンスの取得
yunhu = sdk.adapter.get("yunhu")

# メッセージの送信
await yunhu.Send.To("user", "U1001").Text("Hello")

# 送信アカウントの指定
await yunhu.Send.Using("bot1").To("group", "G1001").Text("グループメッセージ")
```

### チェーン修飾

```python
# @ユーザー
await yunhu.Send.To("group", "G1001").At("U2001").Text("@メッセージ")

# メッセージへの返信
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("返信")

# @全員
await yunhu.Send.To("group", "G1001").AtAll().Text("お知らせ")
```

### Event 返信メソッド

Event オブジェクトは便利な返信メソッドを提供しています：

```python
@command("test")
async def test_handler(event):
    # シンプルなテキスト返信
    await event.reply("返信内容")
    
    # 画像の送信
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 音声の送信
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## 遅延読み込みシステム

ErisPulse はデフォルトでモジュールの遅延読み込みを有効にしており、モジュールは初めてアクセスされた時（例：`sdk.MyModule`）にのみ初期化されるため、起動速度が大幅に向上します。

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # 遅延読み込みを有効化（デフォルト）
            priority=0        # ロード優先度、数値が大きいほど先に初期化されます
        )
```

**遅延読み込みを無効にする必要があるシナリオ（`lazy_load=False`）：**
- ライフサイクルイベントをリッスンするモジュール（例：`core.init.complete`）
- 定期タスクやバックグラウンドサービスを起動するモジュール
- 他のモジュールがロードされる前に初期化を完了する必要があるモジュール

> 遅延読み込みメカニズムの詳細と注意事項については、[遅延読み込みシステム](../advanced/lazy-loading.md) を参照してください。

## 次のステップ

- **L1 パスに沿って続行**：次は [Event ラッパークラス](../developer-guide/modules/event-wrapper.md) で、イベントオブジェクトのすべての読み書きメソッドを習得します
- **書きながら学びたい**：[イベント処理入門](event-handling.md) ではイベントタイプ別にコピーしてすぐ使えるハンドラーの書き方を紹介しています。[よくあるタスクの例](common-tasks.md) では永続化、定期タスク、権限制御などのよく使う機能を網羅しています

## 事件处理

> 来源: `docs/ja/getting-started/event-handling.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/getting-started/event-handling.md）

# イベント処理入門

> [!TIP]
> **このドキュメントを読むべきタイミング**：ボットにメッセージ、コマンド、通知、リクエストへ応答させたい場合や、返信の待機 / マルチターン会話の実装、「コマンドがトリガーされないのはなぜか」のトラブルシューティングが必要なときに読んでください。フレームワークの設計だけを知りたい場合は、[基本概念](basic-concepts.md) を参照すれば十分です。必要なければスキップしてください。

イベントハンドラーとは、ボットがユーザーの意図を「理解」して反応する場です。このドキュメントでは、5種類のイベントごとにそのままコピーして使える実装例を示し、パラメータ解析、権限、スロットリング、マルチターン対話といった実践的なシナリオも網羅します。

## イベントタイプの概要

ErisPulse は以下のイベントタイプをサポートしています：

| イベントタイプ | 説明 | 適用場面 |
|---------|------|---------|
| メッセージイベント | ユーザーが送信したすべてのメッセージ | チャットボット、コンテンツフィルタ |
| コマンドイベント | コマンド接頭辞で始まるメッセージ | コマンド処理、機能入口 |
| 通知イベント | システム通知（友達追加、グループメンバー変更など） | メッセージ歓迎、ステータス通知 |
| 要求イベント | ユーザーの要求（友達リクエスト、グループ招待） | 要求の自動処理 |
| 元イベント | システムレベルのイベント（接続、ハートビート） | 接続監視、ステータスチェック |

## メッセージイベントの処理

> **ヒント**: IDEの自動補完と型チェックのサポートを得るために、イベントハンドラで `Event` タイプ注釈を使用することを推奨します。

```python
from ErisPulse.Core.Event import Event  # 注釈に使用するイベントタイプをインポート
```

### すべてのメッセージを監視

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"{user_id} からのメッセージ: {text}")
```

### プライベートメッセージを監視

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"こんにちは，{user_id}！これはプライベートメッセージです。")
```

### グループメッセージを監視

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ {group_id} で {user_id} がメッセージを送信しました")
```

### @メッセージを監視

```python
@message.on_at_message()
async def at_handler(event: Event):
    # @されたユーザーのリストを取得
    mentions = event.get_mentions()
    await event.reply(f"あなたは以下のユーザーを@しました: {mentions}")
```

### ワイルドカードと正規表現の監視

4つのメッセージデコレータ（`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`）は `pattern`（glob ワイルドカード）と `regex`（正規表現）をサポートし、一致しないメッセージは**ハンドラをトリガーしません**：

```python
# glob ワイルドカード：* 任意の文字列、? 単一文字、[seq] 文字集合
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("签到成功")

# 正規表現：金額をマッチ
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"受信金額：{event.get_text()}")

# pattern と regex が両方指定された場合 → 両方一致する必要がある
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` もこの2つのパラメータをサポートします（[返信待ち機能](../developer-guide/modules/event-wrapper.md#返信待ち機能)を参照）。

## コマンドイベント処理

### 基本コマンド

```python
from ErisPulse.Core.Event import command

@command("help", help="ヘルプ情報を表示")
async def help_handler(event):
    help_text = """
利用可能なコマンド：
/help - ヘルプを表示
/ping - 接続をテスト
/info - 情報を表示
    """
    await event.reply(help_text)
```

### コマンドエイリアス

```python
@command(["help", "h"], aliases=["帮助"], help="ヘルプ情報を表示")
async def help_handler(event):
    await event.reply("ヘルプ情報...")
```

ユーザーは以下のいずれかの方法で呼び出すことができます：
- `/help`
- `/h`
- `/帮助`

### コマンド引数

```python
@command("echo", help="メッセージを返す")
async def echo_handler(event):
    # コマンド引数を取得
    args = event.get_command_args()
    
    if not args:
        await event.reply("返信するメッセージを入力してください")
    else:
        await event.reply(f"あなたが言った: {' '.join(args)}")
```

引数はユーザー入力の元の大文字小文字を保持します（設定が大文字小文字無視であっても、コマンド名の一致は正規化されますが、引数の内容には影響しません）。

### 宣言的引数とオプション（args= / options=）

手動で引数を解析するには、自分で型変換とエラーメッセージを処理する必要があります。`args=` / `options=` を宣言すると、フレームワークは権限チェックを通過した後にコマンド引数を自動的に解析し、**名前でハンドラに注入**します。ユーザーが入力ミスをした場合、自動的にローカライズされたエラーメッセージと使い方を返し（例外が発生してクラッシュすることはありません）、`/help <コマンド>` でも自動的に使い方が表示されます：

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="サイコロを振る",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"{count}回 {sides}面サイコロを振った、合計点数：{total}")
```

`args=` 位置引数の構文：`<count:int>` 必須、`[sides:int=6]` 省略可能（デフォルト値付き）。サポートされる型：

| 型 | 例 | 説明 |
|------|---------|------|
| `str` | `hello` | テキスト（デフォルト型） |
| `int` / `float` | `3` / `0.5` | 数値 |
| `bool` | `はい` / `yes` / `はい` / `да` / `true` / `no` / `取消` | ブール値、イベント確認（`Event.confirm()`）の確認語リストを再利用 |
| `literal` | `<mode:literal=fast|slow>` | 列挙、指定された値のみを受け入れる；省略形はデフォルトで最初のものを取る |
| `duration` | `90s`、`1h30m`、`1d` | 時間、秒に換算してfloatで返す |
| `rest` | `<text:rest>` | 残りのすべてのテキスト（最後に位置する必要がある） |

`options=` オプションは辞書形式で宣言：キーはハンドラの引数名、値はフラグ形式（複数のエイリアスは `/` で区切る）。注釈が `bool` の引数はブールフラグ（存在すれば `True`）；それ以外（デフォルトは `str`）は値付きオプションで、`--label hello` と `--label=hello` の両方の形式がサポートされ、型はハンドラの注釈に従う。オプションは最初に認識されて除外され、残りのトークンは `args=` に従って解析される（`rest` はオプションを除外した後の残りのテキストをカバーする）。

**動作の要点**：

- 権限チェックは引数解析より先に実行される——権限のないユーザーは解析をトリガーしない
- 解析失敗（型が合わない / 必須引数が足りない / 引数が多すぎる / 未知のオプション）は自動的にローカライズされたエラーと使い方を返し、コマンドは引き継がれる
- 宣言された引数名はハンドラのシグネチャに存在しなければならない、さもなければ登録時に `ValueError` を投げる
- `args=` / `options=` を宣言しないコマンドは動作がまったく変わらない（後方互換性）

### コマンド管理（cooldown= / rate_limit= / usage_limit= / deprecated=）

手動でクールダウン、リミット、使用制限、非推奨メッセージを宣言で置き換え、これらは任意に組み合わせることができる。

**クールダウン**——時間の書式は `args=` の `duration` 型と同じ（例：`"30s"`、`"1h30m"`、`"1d"`）：

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今日のサインイン済み")
async def daily_handler(event):
    await event.reply("サインイン成功！")
```

**リミット**——スライディングウィンドウの宣言 `"回数/ウィンドウ"`（例：`"5/minute"`、`"10/s"`、`"3/2m"`）：

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("検索結果")
```

**制限**——周期内での総回数上限（例：`"100/day"`、`"10/hour"`、`"500/30d"`）、上限を超えると実行を拒否する：

```python
@command("translate", usage_limit="100/day", usage_limit_key="user",
         usage_limit_reply="今日の翻訳回数が上限に達しました")
async def translate_handler(event):
    ...
```

クールダウン / リミットとは異なり、制限のカウントは**永続化されたストレージに保存**される（KVキー `erispulse.usage.<key>`、再起動しても失われない）：
ストレージが利用できない場合は自動的にメモリ内カウントに退化し、警告を出力する（この場合、制限は再起動でリセットされる）。カウントは制限周期の切り替えごとに自動的にリセットされ、モジュールのアンロード時にクリアされる。

**非推奨**——呼び出し時に自動的に非推奨の文を返し、`deprecated_reject=True` で実行を拒否する：

```python
@command("oldcmd", deprecated="代わりに /newcmd を使用してください", deprecated_reject=True)
async def old_handler(event): ...
```

キーの粒度（`cooldown_key=` / `rate_limit_key=`）：`"user"`（デフォルト、同一ユーザーが共有）、
`"session"`（同一セッションが共有、同じグループ内）、`"global"`（すべてのユーザーとセッションが共有）。

**動作の要点**：

- クールダウン / リミット / 制限がヒットした場合、デフォルトでは**静かに破棄**される（作用域の静かさに対応）；`cooldown_reply=` / `rate_limit_reply=` / `usage_limit_reply=` を宣言した場合、ヒットしたらその文を返す
- コマンドがヒットした時点で認識される——管理がヒットしたコマンドは低優先度のメッセージハンドラに漏れることはない
- 管理の判定はすべての権限チェックと引数解析が通過し、実際の実行の直前に行われる：権限のないユーザーはトリガーされず、引数エラーは消費されない
- クールダウンとリミットを同時に宣言した場合、クールダウンが先に判定される（クールダウンがヒットしてもリミットのウィンドウは消費されない）；制限はクールダウン / リミットの判定の後に行われる
- `deprecated=` はデフォルトで返信文を返した後に**実行を続ける**；`deprecated_reject=True` で実行を拒否する（`command.executed` フックは `success=False, error="deprecated"` として記録される）
- `/help` のリストと単一コマンドのヘルプは自動的に非推奨マークと文を表示する
- クールダウンとリミットの状態はプロセス内メモリに保存され、モジュールのアンロード時に自動的にクリアされる；プロセス間共有 / 再起動時の永続化は含まれない（**usageの制限カウントのみ**——ストレージに永続化されている、上記参照）
- 宣言は登録時に検証される（fail-fast）：書式が不正、キーの粒度がホワイトリスト外、replyが主宣言と組み合わされていない場合、すべて `ValueError` を投げる

### ハンドラのスロットリング（throttle=）とデバウンス（debounce=）

メッセージハンドラのスパム防止宣言——同じキーのイベントは間隔内に1件のみ処理され、残りは静かに破棄される：

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

デバウンスとスロットリングは補完的です：**ウィンドウ内では最後の1件のみ実行**され、前の実行中のタスクは自動的にキャンセルされる（例：「入力停止後に処理する」検索連想などに適しています）：

```python
@sdk.message.on_message(debounce="2s", debounce_key="user")
async def search(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message`
はすべてサポートされます；`throttle_key=` / `debounce_key=` はコマンド管理と同じキーの粒度
（user / session / global）で、時間の書式は `duration` と同じです。スロットリングと `pattern=` /
`regex=` などの既存の条件は重複して効果を発揮します（すべて満たす場合にのみトリガー）；間隔内に破棄されたイベントはTRACEログとして記録されます；
宣言は登録時に検証されます；`throttle=` と `debounce=` は意味的に排他的です（両方宣言すると `ValueError` を投げる）。

> **デバウンスは途中で業務を中断しない**：待機ウィンドウを越えていない未実行タスクはキャンセルされる；すでに越えて実行中のハンドラは新しいイベントによってキャンセルされない（任意の await 点で部分副作用が発生するのを避ける）。

### 依存注入（Depends）

共通の依存（データベースセッション、設定の読み取りなど）は依存関数として抽出し、ハンドラは
`Depends(依存関数)` をパラメータのデフォルト値として宣言し、フレームワークは呼び出し前にコンテキストオブジェクトを使って依存関数を自動的に呼び出し、名前で注入する：

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

デフォルトで**リクエストレベルのキャッシュ**が有効です：1回のイベント配信内では、同じ依存関数は1回しか解析されず、すべての注入ポイントで結果を共有します（`get_db` は1回のイベント内で1回だけデータベースセッションを確立します）；リクエスト間では自動的に再利用されません。`Depends(get_db, use_cache=False)` を使用して1つの依存のキャッシュを無効にできます。

フレームワークのすべての注入ポイントをオーバーライドします——コマンドハンドラ、イベントハンドラ（`message.on_message()` など）、ライフサイクルフック（`sdk.lifecycle.on`）、SSEルートハンドラ。依存関数の最初のパラメータは注入ポイントのコンテキストオブジェクト（イベントの場合は `Event`、ライフサイクルの場合はイベント `data`、ルートの場合は `HttpRequest` / `SseEmitter`）です；同期および非同期の依存関数を宣言できます。

**他のモジュールのサービスを宣言する**（糖衣構文）：

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(モジュール名, メソッド名, *固定引数)` は、依存関数内で `sdk.module.call(...)` を呼び出すのと同等です。モジュールのインスタンス化（`__init__`）は対象外です——インスタンス化時にはコンテキストオブジェクトがありません；FastAPIでホストされるHTTPルートはFastAPIの原生 `fastapi.Depends` を使用してください。

**動作の要点**：

- 宣言は登録時に検証される（fail-fast）：依存が呼び出せない、または `args=` / `options=` パラメータと重複する場合、`ValueError` を投げる
- 依存関数が投げた例外は、ハンドラ自身の例外と同じ方法で処理される（コマンドはエラーを自動的に返す）
- `Depends` を宣言しないハンドラはゼロオーバーヘッド（配信時に反射は一切行わない）
- FastAPIでホストされるHTTPルートは、FastAPIの原生 `fastapi.Depends` を使用してください

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    await event.reply("モジュールを再読み込みしました")

@command("admin.stop", group="admin", help="ロボットを停止")
async def stop_handler(event):
    await event.reply("ロボットを停止しました")
```

`group` パラメータはヘルプリストの分類にのみ使用されます；上記の例では `admin.reload` は**全体のコマンド名**（ドットは命名スタイルに過ぎず、ユーザーは `/admin.reload` を入力する必要があります）です。

### サブコマンド

コマンド名は**スペース区切りの複数トークン形式**をサポートし、`/admin add`、`/admin user ban` などのサブコマンドを実現します：

```python
@command("admin", help="管理コマンド")
async def admin_handler(event):
    await event.reply("使い方：/admin add | /admin remove")

@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"{target} を追加しました")

@command("admin remove", aliases=["a remove"], help="管理者を削除")
async def admin_remove_handler(event):
    await event.reply("管理者を削除しました")
```

マッチングルール（**最長接頭辞マッチ**）：

- `/admin add x` は `admin add` に優先的にマッチし、`event.get_command_args()` は `["x"]` を返す（サブコマンド名以降の引数）
- `admin` だけが登録されている場合、`/admin add x` は `admin` にマッチし、`get_command_args()` は `["add", "x"]` を返す（従来の動作は変更なし）
- エイリアスは複数トークン形式（`a remove`）をサポートし、単一トークンエイリアス（`a`）もサブコマンドに指定できる
- 親子コマンドが同時に登録されている場合、登録されていないサブコマンドの入力（例：`/admin list x`）は親コマンドに降格される

**権限の継承**：サブコマンドが `permission` を宣言していない場合、直近に権限を宣言した祖先コマンドを自動的に継承する——`/admin` を保護すれば、その下のすべてのサブコマンドも自動的に保護される；サブコマンド自身が宣言した権限が優先される：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理コマンド")
async def admin_handler(event):
    ...

# permissionを再宣言する必要はない、is_adminを自動的に継承する
@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    ...
```

注意：`master=True` と `hidden` は**継承されない**、必要であればサブコマンドで個別に宣言する必要がある；ユーザーACL（ホワイトリスト/ブラックリスト）はコマンドの完全名でマッチし、globルール（例：`"admin*"`）はサブコマンド全体をカバーできる。

`/help` のコマンド概要では、サブコマンドは表示可能な親コマンドに自動的にインデントして表示される
（`admin` → `admin add` は1段階インデント、`admin user` → `admin user ban` は2段階インデント）。

### コマンドの権限とアクセス制御

コマンドの権限は3層に分かれ、上から下へ順に判定される（**上層が拒否すると下層は見ない**）：

```python
# ① コマンドの権限ACL（ユーザー側設定）：コマンドのユーザーホワイトリスト/ブラックリスト、拒否時は「権限不足」を返す
# ② master=True —— フレームワークのオーナーのみ実行可能（フレームワークが自動的にチェック、拒否時は「権限不足」を返す）
@command("restart", master=True, help="モジュールを再起動")
async def restart_handler(event):
    await event.reply("モジュールを再起動しました")

# ③ permission=呼び出し関数 —— コマンド自身の制御ロジック（Trueを返す場合のみ実行）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理パネル")
async def panel_handler(event):
    await event.reply("管理パネルへようこそ")
```

**コマンドのユーザーACL**（`ErisPulse.event.command.acl`）：ユーザーは任意のコマンドにユーザーホワイトリスト/ブラックリストを設定でき、コマンド名は正確なマッチとglobパターン（例：`"roll*"`）をサポートし、拒否時は「権限不足」を返す：

```toml
# config.toml —— restartコマンドは123456のみ実行可能；666は一律拒否
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny` がヒット → 拒否；`allow` が空でないかつヒットしない → 拒否；ACLが設定されていない場合は
`event.command.default_allow`（`false` = 严格モード、ACLがないと拒否；`true` は開発者側のデフォルト
`master=True` / `permission` に任せる）に従う。実行時API（コマンド名はglobをサポート）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 允許リスト
command.deny_user("restart", "onebot11", "666")       # 拒否リスト
command.remove_acl("restart")                          # ホワイトリスト/ブラックリストを削除
command.get_acl("restart")                             # 現在のリストを取得
```

> コマンドハンドラはイベントパッケージからインポートする：`from ErisPulse.Core.Event import command`；
> またはSDKイベントパッケージからアクセスすることもできる：`sdk.Event.command`（両者は同一のシングルトン）。
> モジュール内では通常、コマンドデコレータからインポートされている（`from ErisPulse.Core.Event import command`）。

コマンド間 / ユーザー間の**イベントレベル**のアクセス制御（特定のユーザー / グループ / Botのメッセージを受信するかどうか）
は作用域**アイデンティティ次元**（`scope.identity`）を通じて行う；**モジュールレベル**の可用性（どのモジュールが使えるか）
は作用域**モジュール次元**（`scope.platforms / bots / sessions`）を通じて行う。
詳細は[作用域（scope）](../advanced/scope.md)を参照してください。

> 建議：コマンド内部でビジネスロジックを連動させる場合は `master=True` / `permission` を使用する；ユーザー / グループごとのアクセス制御を行う場合は作用域アイデンティティ次元を使用する；モジュールの可用性を制御する場合は作用域モジュール次元を使用する。

### コマンドの優先度

```python
# 優先度の数値が大きいほど、実行が早くなる
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先度ハンドラ")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先度ハンドラ")
```

### 並列イベント処理

ErisPulseのイベントシステムは**同優先度で並列、異なる優先度で直列**のスケジューリングモデルを採用しています：

```
イベント到着
    ↓
priority=10 組: [ハンドラC || ハンドラD] 並列 → 結果を結合
    ↓ (中断しない場合)
priority=0 組: [ハンドラA || ハンドラB] 並列 → 結果を結合
    ↓
...
```

- **同優先度で並列**：優先度が同じ複数のハンドラは同時に実行され、スループットを向上させる
- **異なる優先度で直列**：異なる優先度のグループは順番に実行される（数値が大きいほど先に実行）、高優先度ハンドラが先に実行されることを保証する
- **Copy-On-Write**：ハンドラが変更しない場合はコピーを作成せず、ゼロオーバーヘッドを確保する
- **競合処理**：同優先度の複数ハンドラが同じフィールドを変更した場合、最後に変更された値を使用し、警告ログを記録する
- **中断メカニズム**：任意のハンドラが `event.done()`（デフォルト）または `event.done(claim=False)` を呼び出した後、以降の低優先度グループはスキップされる。認領とブロッキングの違いは下記の[「リンク制御：認領とブロッキング」](#リンク制御認領とブロッキング)を参照してください。

```python
# 例：同優先度ハンドラが並列に実行される
@message.on_message(priority=0)
async def handler_a(event):
    # タスクAを処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_aと並列に実行される
    event['result_b'] = process_b()

# 異なる優先度で直列に実行される
@message.on_message(priority=10)
async def handler_c(event):
    # 最も優先度が高い、最初に実行される
    pass
```

> **並列上限**：すべてのマッチするハンドラのTaskは**即座に作成**されるが、シグナルマネージャーによって**同時に実行される数**を制限し、デフォルト上限は **64**（`ErisPulse.framework.handler_max_concurrency`、ホットアップデート可能）。上限を超えたTaskはシグナルマネージャー上でキューに並び、前の処理が完了してから実行される。イベントの洪水時にこれが「圧力緩和弁」になる。
>
> **遅延ログ**：単一ハンドラの処理時間が**1秒**を超える場合、フレームワークはログにWARNINGを出力する（`handler_slow`）。`wait_reply`の待機時間は処理時間から除外され、「返信を待つ」ことで誤って遅延と判定されない。

## ミドルウェア：配分前に変更または拒否

ミドルウェアはイベント配分**の前に**順序実行され、ファイアウォール、レート制限、イベントの脱敏などの正統な実装ポイントである：

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # 拒否：イベントは破棄され、どのハンドラにも渡されず、出力の副作用もない
    data["checked"] = True    # 戻り値が dict の場合：イベントの負荷を変更して配分を続ける
    # 戻り値が None の場合：放行、負荷は変更されない（歴史的な動作）
    return data
```

| 戻り値 | 行動 |
|--------|------|
| `False` | **拒否**：イベントは即座に破棄され、どのハンドラにも渡されない |
| `dict` | イベントの負荷を変更して配分を続ける |
| `None` | 放行、負荷は変更されない |

拒否した場合、フレームワークは TRACE ログを出力し、`adapter.event.blocked` ライフサイクルフックをトリガー（ミドルウェア名と完全なイベント）し、イベントがなぜ応答しなかったかを監査する。

## コマンド配信の決定チェーン：なぜコマンドが発動しなかったのか

1 つのコマンドメッセージは次のように順次処理されます：**コマンドテキストの判定 → コマンド名/別名の一致（一致しなければスペルチェックの提案あり）→ 一致即ち認領 → スコープ → ユーザー ACL → オーナー → 権限 → クールダウン/リクエスト制限 → 使用量制限（usage）→ 廃棄（deprecated、notice/rejected）→ パラメータ解析 → 実行**（ミドルウェアはイベント層で否決することも可能、前節参照）。いずれかのステップで条件を満たさない場合、処理はそこで終了します。配信制限（クールダウン/リクエスト制限/使用量制限）はデフォルトで静かに無視され、権限に関する拒否はユーザーに返信されます。廃棄は宣言通りに返信または拒否されます。

テスト環境の `ErisPulse-Testing` では、`dispatch()` がこの決定チェーン（`DispatchTrace`、`trace.explain()` で各ステップの因果関係を出力）を直接返します。本番環境では `ErisPulse.Core.Event.start_dispatch_trace()` を使用して同様の記録を収集できます。

さらに `ErisPulse.runtime` は、2 組のトラブルシューティング用 API を提供しています：`explain_module(モジュール名)` は「なぜモジュールがロードされなかったのか」を回答します（未登録 / 遅延ロード / 設定による無効化 / 依存関係の欠如 / SDK バージョンが満たさない、各項目に原因を明示）、`explain_event(イベント)` は「なぜイベントが応答されなかったのか」を回答します（アダプタ未登録 / 身元ブラックリスト / モジュールのセッション遮断 / コマンドが一致しない）；併せて `format_report()` を使用して人間が読みやすい形式に整形できます。

## 作用域フィルタ：なぜ私のモジュールがメッセージを受け取らないのか

イベントが到着した後、2つの**静か**なフィルタがある（どちらも返信せず、エラーも出さない）：

1. **アイデンティティ次元**（`ErisPulse.scope.identity`）：イベントが配分エントランスに到着した時点で、ユーザー > グループ > Bot > アダプターの順に判定し、受け取るかどうかを決める。
   拒否された**イベント全体**は破棄され、どのハンドラ（コマンドディスパッチャーを含む）もトリガーされない。
2. **モジュール次元**（`ErisPulse.scope`）：イベントが特定のモジュールのハンドラ/コマンドに到着した時点で、セッション > Bot > プラットフォームの順に判定し、
   このモジュールが利用可能かどうかを確認し、**通過しない場合は静かにスキップ**する。

```toml
# 例1：あるグループのすべてのメッセージを伝播しない
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：MyModuleを特定のBotにブロック
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

この場合、そのグループのメッセージが到着したときに、`MyModule` のコマンドとイベントハンドラは**すべてスケジュールされない**。これはバグではなく、フィルタリング機構である——「モジュールが反応しない」の原因を調査するときは、まず作用域のアイデンティティとモジュールのバインディングを確認する。

- フィルタリングのログは **TRACE** 級にのみ表示される（`core.scope.identity_denied` / `core.scope.denied`）、デフォルトの INFO では痕跡は見えない
- フレームワークのハンドラ（コマンドディスパッチャー `scope_exempt=True`）は**モジュール次元**の影響を受けないが、**アイデンティティ次元**の影響を受ける（イベント全体が破棄されている）
- コマンド実行前の第三のフィルタは、コマンドのユーザー ACL（拒否された場合は「権限不足」を返す、上節参照）
- 第四のフィルタは**イベントオーバーライド**（次節参照）

> [!NOTE]
> **作用域フィルタとイベント認領（claim）の関係**：2つの静かのフィルタはハンドラ
> **スケジュールの前**に発生する——フィルタでスキップされたハンドラは実行されず、当然
> `event.done()` / `mark_processed()` の認領ステータスにも参加しない。イベントが
> 認領されたかどうかは、**実行された**ハンドラ（コマンドが認領された、返信が認領された、明示的に呼び出された）によって決定される；
> 作用域拒否自体は認領もブロックもしない（静かにスキップし、メッセージは残りの配分チェーンを完了する）。

> 作用域の設定、マッチングの構文、実行時 API は [作用域（scope）](../advanced/scope.md)を参照。

## イベントオーバーライド：モジュールのコードを変更せずに、任意のイベントタイプの動作をオーバーライド

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要。

イベントハンドラが登録時に宣言したパラメータ（`pattern` / `regex` / `master` / `hidden` など）は**開発者のデフォルト**に過ぎない。
統一オーバーライドシステムは、ユーザーが**イベントタイプ**ごとに任意のモジュールの動作をオーバーライドできるようにする——OneBot12標準タイプ
（meta / message / notice / request）と ErisPulse 拡張タイプ（command）それぞれに固有のオーバーライド可能なパラメータがある：

| イベントタイプ | オーバーライド可能なパラメータ | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | テキストトリガー条件 + メッセージサブタイプホワイトリスト |
| `notice` | `detail_types` / `pattern` / `regex` | 通知サブタイプホワイトリスト + テキスト条件 |
| `request` | `detail_types` / `pattern` / `regex` | リクエストサブタイプホワイトリスト + テキスト条件 |
| `meta` | `detail_types` | メタイベントサブタイプホワイトリスト（connect / heartbeat など） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | コマンド実装パラメータ（ユーザー優先） |
| `acl`（command専用） | `allow` / `deny` | コマンドのユーザーホワイトリスト/ブラックリスト（コマンド名 glob） |

```toml
# message：テキストトリガー条件をオーバーライド（コード内の条件と AND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice：特定の通知サブタイプのみを応答
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：実装パラメータをオーバーライド（ユーザー優先——制限または開放できる）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：コマンドのユーザーホワイトリスト/ブラックリスト（コマンド名 glob）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACLのデフォルト（false = シャープモード：ACLがない場合は拒否）
acl_default_allow = true
```

実行時 API（`from ErisPulse.Core.Event import overrides` または `sdk.Event.overrides`，
**タイプサブネームスペース**——各タイプに対称的な `set` / `get` / `delete` 三件セット）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # messageのテキスト条件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # コマンドパラメータ
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # コマンドのユーザーブラックリスト

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # 開発者のデフォルトに戻す
```

- オーバーライド条件とハンドラコード内の条件は**同時に有効**（ANDの意味）；`command`のパラメータは開発者の宣言と**深くマージ**（オーバーライドが優先）
- `detail_types`：イベントに `detail_type` がない場合は通過（未知のイベントを誤って破棄しない）
- `pattern` / `regex`：テキストのないイベント（connect / heartbeat など）は制約を受けず、直接通過
- `command`のオーバーライドキー `master` は同期的にストレージキー `must_master` にマッピング；コマンドの禁止はすべて `acl` deny で行う
- **キー名のマッピング説明**：`overrides.command.set("My", "restart", master=True)` のパラメータ名
  `master` は設定の別名に過ぎず、実際のストレージキーと `get()` の返り値のキー名は統一して **`must_master`**
  （`get()` は `{"must_master": true}` を返す）——実行時判定はストレージキーを読み取るため、`master` キー名で読み取らないでください
- 設定は変更すると即座に有効（ホットアップデート）、形式検証の警告（未知のパラメータ / 不正な項目は無視）

## リンク制御：認領とブロック

> [!NOTE]
> `event.done()` / `event.mark_processed()` の `claim=` / `stop=` パラメータはこの機能には ErisPulse **2.7.1+** が必要。

ErisPulse は「認領」と「ブロック」の2つの正交的な意味を分離し、`event.done()` で統一的に制御することで、コマンド処理の周囲にログ、監査、権限などの観察層を重ねることができる。

**2つの概念の正確な定義**：

- **認領（claim）**：イベントがこのハンドラによって処理されたことをマークする（`_processed` に書き込む）。コマンドディスパッチャーは認領されたイベントを見ると**重複処理を防ぐ**——同じメッセージが複数のコマンドハンドラに重複して処理されない。典型的な場面：コマンドがマッチした後に認領し、コマンドディスパッチャーが介入しないようにする。
- **ブロック（stop）**：イベントが**より低い優先度**のハンドラに伝播しないようにする（`_propagation_stopped` に書き込む）。低優先度のハンドラはこのイベントを見ない。典型的な場面：高優先度のハンドラがイベントを完全に処理した後、低優先度のハンドラが実行されないようにする。

| `event.done(...)` | 認領 | ブロック | 場面 |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | コマンド / ハンドラ処理完了の標準的なやり方 |
| `event.done(stop=False)` | ✔ | ✘ | 認領のみ、低優先度の観察者（ログ / 統計）は引き続き見る |
| `event.done(claim=False)` | ✘ | ✔ | ブロックのみ（ファイアウォール / レート制限）、認領はしない |

`event.done(claim=, stop=)` は `event.mark_processed(claim=, stop=)` の別名であり、パラメータと動作は完全に等価。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 認領 + ブロック（コマンド処理完了の標準的なやり方）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 認領のみ：低優先度は引き続き実行（ログ / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # ブロックのみ：低優先度は実行しない、認領はしない
```

### コマンドと返信の block 設定

**コマンドがマッチした時点で認領**：メッセージが登録されたコマンド名（サブコマンド/エイリアスを含む）にマッチした場合、権限や判定の結果に関係なく、認領され、デフォルトでブロックされる——権限拒否されたコマンドは低優先度のメッセージハンドラに漏れない（「コマンドが拒否された後に on_message がもう一度反応する」二重反応を防ぐ）。

ブロックを解除して、低優先度の観察者（ログ / 監査 / 権限）がこれらのメッセージを見られるようにすることができる：

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージは低優先度のハンドラに流れる（認領は影響しない、重複消費はしない）

[ErisPulse.event.wait_reply]
block = false   # wait_reply で消費された返信は低優先度のハンドラに流れる
```

> 注意：`block` は**ブロック**（stop）だけを制御し、**認領**（claim）には影響しない——マッチしたコマンドは決してメッセージハンドラに重複消費されない；コマンドにマッチしなかったメッセージは通常通りメッセージハンドラに流れる。

## 通知イベントの処理

### 友達追加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"欢迎添加我为好友，{nickname}！")
```

### グループメンバーの増加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"欢迎新成员 {user_id} 加入群 {group_id}")
```

### グループメンバーの減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"成员 {user_id} 离开了群 {group_id}")
```

## 要求イベントの処理

### 友達リクエスト

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"收到好友请求: {user_id}, 附言: {comment}")
    
    # 适配器 API でリクエストを処理することができる
    # 具体的な実装は各适配器のドキュメントを参照
```

### グループ招待リクエスト

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"收到群 {group_id} 的邀请，来自 {user_id}")
```

## 元イベントの処理

### 接続イベント

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} 平台已连接")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} 平台已断开连接")
```

### ハートビートイベント

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} 心跳检测")
```

### Bot 状態の照会

适配器が meta イベントを送信した後、フレームワークは自動的に Bot 状態を追跡し、いつでも照会できる：

```python
from ErisPulse import sdk

# 特定の Bot がオンラインかどうかをチェック
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot 在线")

# 現在のすべてのオンライン Bot をリストアップ
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 完全な状態サマリーを取得
summary = sdk.adapter.get_status_summary()
```

## 対話処理

### reply メソッドを使用して返信を送信

`event.reply()` メソッドは、@、返信などの機能をサポートするさまざまな修飾パラメータを提供します：

```python
# 簡単な返信
await event.reply("你好")

# 異なるタイプのメッセージを送信
await event.reply("http://example.com/image.jpg", method="Image")  # 画像
await event.reply("http://example.com/voice.mp3", method="Voice")  # 音声

# @単一ユーザー
await event.reply("你好", at_users=["user123"])

# @複数ユーザー
await event.reply("大家好", at_users=["user1", "user2", "user3"])

# 返信
await event.reply("回复内容", reply_to="msg_id")

# @全員
await event.reply("公告", at_all=True)

# 組み合わせ：@ユーザー + 返信メッセージ
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待つ

```python
@command("ask", help="询问用户")
async def ask_handler(event):
    await event.reply("请输入你的名字:")
    
    # ユーザーの返信を待つ、タイムアウト時間 30 秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超时，请重新输入。")
```

> [!TIP]
> **待機中もコマンドは使用可能**（2.8.3+）：コマンド接頭辞で始まり、登録されたコマンドに一致する
> メッセージ（例：`/cancel`）は**コマンドとして実行**され、返信として扱われず、待機は継続する——
> ユーザーはいつでもキャンセル/切り替えでき、コマンド実行後も返信を続けることができる。旧来の「すべてのテキストを待機中に吸収する」
> 行動が必要な場合は：設定 `ErisPulse.event.wait_reply.cmdpass = true`、または単回
> `wait_reply(cmdpass=True)`。

### 認証付きの待機返信

```python
@command("age", help="询问年龄")
async def age_handler(event):
    def validate_age(event_data):
        """年齢が有効かどうかを認証"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("请输入你的年龄 (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"你的年龄是 {age} 岁")
    else:
        await event.reply("输入无效或超时")
```

### コールバック付きの待機返信

```python
@command("confirm", help="确认操作")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("操作已确认！")
        else:
            await event.reply("操作已取消。")
    
    await event.reply("确认执行此操作吗？(是/否)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### 確認対話 (confirm)

ユーザーの確認または否定を待つ、自動的に組み込みの中英確認語を認識する：

```python
@command("confirm", help="确认操作")
async def confirm_handler(event):
    if await event.confirm("确定要执行此操作吗？"):
        await event.reply("已确认，执行中...")
    else:
        await event.reply("已取消")

# 自定義確認語
if await event.confirm("继续吗？", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### 選択メニュー (choose)

ユーザーは選択番号または選択肢のテキストを返信できる：

```python
@command("choose", help="选择")
async def choose_handler(event):
    choice = await event.choose(
        "请选择颜色：",
        ["红色", "绿色", "蓝色"]
    )
    
    if choice is not None:
        colors = ["红色", "绿色", "蓝色"]
        await event.reply(f"你选择了：{colors[choice]}")
    else:
        await event.reply("超时未选择")
```

**マージモード**：`merge_prompt=True` の場合、オプションをプロンプトにマージし、指定された `method` で1つのメッセージとして送信する：

```python
# Markdown でマージされたプロンプト + オプションを送信
choice = await event.choose(
    "## 请选择颜色\n{options}\n请回复编号",
    ["红色", "绿色", "蓝色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` プレースホルダはオプションの挿入位置を制御する；書かなければプロンプトの末尾に追加される。
> `placeholder` パラメータでプレースホルダをカスタマイズできる（例：`placeholder="[choices]"`）。
> `options_format="auto"`（デフォルト）は method に応じて自動的にスタイルを選択する：Markdown→箇条書き、Html→番号付きリスト、その他の→純粋なテキストリスト。
> テキスト系メソッド（Text/Markdown/Html など）はデフォルトでオプションを末尾にマージする；非テキスト系メソッド（Image など）はデフォルトで2つのメッセージに分割する。

### フォームの収集 (collect)

複数ステップでユーザー入力を収集する：

```python
@command("register", help="注册")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "请输入姓名："},
        {"key": "age", "prompt": "请输入年龄：", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "请输入邮箱："}
    ])
    
    if data:
        await event.reply(f"注册成功！\n姓名：{data['name']}\n年龄：{data['age']}\n邮箱：{data['email']}")
    else:
        await event.reply("注册超时或输入无效")
```

### 任意イベントの待機 (wait_for)

特定の条件を満たす任意のイベントを待つ、同一ユーザーに限らない：

```python
@command("wait_member", help="等待新成员")
async def wait_member_handler(event):
    await event.reply("等待群成员加入...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"欢迎新成员：{evt.get_user_id()}")
    else:
        await event.reply("等待超时")
```

### 連続対話 (conversation)

インタラクティブな連続対話コンテキストを作成する：

```python
@command("survey", help="问卷调查")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("欢迎参与问卷调查！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("对话超时，再见！")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("再见！")
            break
        
        await conv.say(f"你说了：{text}，继续输入或回复'退出'结束")
```

### 組み込みの確認語

ErisPulse は中英の確認語の集合を内蔵しています：

- **確認語** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **否定語** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## イベントデータのアクセス

### Event オブジェクトの一般的なメソッド

```python
@command("info")
async def info_handler(event):
    # 基本情報
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # 送信者情報
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # メッセージ内容
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # グループ情報
    group_id = event.get_group_id()
    
    # ロボット情報
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # 原始データ
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # プラットフォーム情報
    platform = event.get_platform()
    
    # メッセージタイプの判定
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # コマンド情報
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### プラットフォーム拡張メソッド

ビルトインメソッドに加えて、各プラットフォームアダプターはプラットフォーム固有のメソッドを登録し、プラットフォーム特有のデータに簡単にアクセスできます。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出す
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram 固有メソッド
    elif platform == "email":
        subject = event.get_subject()           # メール固有メソッド
```

どのプラットフォームがどのメソッドを登録したかわからない場合は、特定のプラットフォームが登録したメソッドを照会できます：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームが登録した固有メソッドは、対応する [プラットフォームドキュメント](../platform-guide/) を参照してください。

## イベント処理のベストプラクティス

### 1. エラーハンドリング

```python
@command("process")
async def process_handler(event):
    try:
        # ビジネスロジック
        result = await do_some_work()
        await event.reply(f"結果: {result}")
    except ValueError as e:
        # 予期されたビジネスエラー
        await event.reply(f"パラメータエラー: {e}")
    except Exception as e:
        # 予期されないエラー
        sdk.logger.error(f"処理失敗: {e}")
        await event.reply("処理失敗、後で再試行してください")
```

### 2. ログ記録

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"メッセージを処理: {user_id} - {text}")
    
    # モジュール独自のログを使用
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"詳細なデバッグ情報")
```

### 3. 条件処理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """条件処理 - ハンドラ内で判定"""
    # 特定ユーザーのメッセージだけを処理
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 特定キーワードを含むメッセージだけを処理
    if "关键词" not in event.get_text():
        return
    
    await event.reply("条件が満たされた、メッセージを処理します")
```

## 次のステップ

- **イベントオブジェクトそのものを操作したい**：[Event ラッパークラス詳解](../developer-guide/modules/event-wrapper.md) を参照してください。Event の全メソッドに関する権威あるリファレンスです
- **より複雑なメッセージを送りたい**：[プラットフォーム特性ガイド](../platform-guide/README.md) では、SendDSL によるチェーン送信、送信ルール、一括構築について詳しく解説しています。[よくあるタスクの例](common-tasks.md) には、リトライ / タイムアウト / 一括処理のすぐに使えるコードが用意されています
- **機能を実装し終えたら設定とデプロイ**：[ユーザーガイド](../user-guide/) に進みましょう。設定ファイルと CLI の管理はすべてそこにあります

## 常见任务

> 来源: `docs/ja/getting-started/common-tasks.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/getting-started/common-tasks.md）

# 一般的タスクの例

> [!TIP]
> **この章を読むタイミング**：ロボットに特定の機能を追加したいときは、各節を参照してください。永続化、定期タスク、メッセージフィルタ、権限制御、一括送信など、各節は直接コピーできる完全な例です。イベント処理の書き方を体系的に学びたい場合は [イベント処理入門](event-handling.md) を先にご覧ください。必要なければ飛ばしてください。

## 内容リスト

1. データの永続化
2. 定期タスク
3. メッセージフィルタ
4. 多プラットフォーム対応
5. メッセージ送信の高度な機能（リトライ/タイムアウト/一括送信）
6. 権限制御
7. メッセージの統計
8. 検索機能
9. 画像処理

## データの永続化

### 簡単なカウンター

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="コマンドの呼び出し回数を表示")
async def count_handler(event):
    # カウントを取得
    count = sdk.storage.get("command_count", 0)
    
    # カウントを増やす
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"このコマンドは {count} 回目の呼び出しです")
```

### ユーザーのデータの保存

```python
@command("profile", help="個人情報の表示")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # ユーザーのデータを取得
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
ニックネーム: {user_data['nickname']}
加入日: {user_data['join_date']}
メッセージ数: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="ニックネームの設定")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("ニックネームを入力してください")
        return
    
    # ユーザーのデータを更新
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"ニックネームを {' '.join(args)} に設定しました")
```

## 定期タスク

### 簡単なタイマー

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
import asyncio

class TimerModule:
    def __init__(self):
        self.sdk = sdk
        self._tasks = []
    
    async def on_load(self, event):
        """モジュールのロード時に定期タスクを開始"""
        self._start_timers()
        
        @command("timer", help="タイマー管理")
        async def timer_handler(event):
            await event.reply("タイマーが実行中です...")
    
    def _start_timers(self):
        """定期タスクを開始"""
        # 60秒ごとに実行
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # 毎日午前0時に実行
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """毎分実行されるタスク"""
        self.sdk.logger.info("毎分のタスクを実行")
        # あなたのロジック...
    
    async def _daily_task(self):
        """毎日午前0時に実行されるタスク（注：UTC時間で計算されます。ローカル時間が必要な場合は調整してください）"""
        import time
        
        while True:
            # 午前0時までの時間を計算
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # タスクを実行
            self.sdk.logger.info("毎日のタスクを実行")
            # あなたのロジック...
```

### ライフサイクルイベントの使用

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """SDKの初期化完了後に定期タスクを開始"""
    import asyncio
    
    async def daily_reminder():
        """毎日のリマインダー"""
        await asyncio.sleep(86400)  # 24時間
        sdk.logger.info("毎日のタスクを実行")
    
    # バックグラウンドタスクを開始
    asyncio.create_task(daily_reminder())
```

## メッセージフィルタ

### キーワードフィルタ

```python
from ErisPulse.Core.Event import message

blocked_words = ["スパム", "広告", "詐欺"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # 敏感語を含むかチェック
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"フィルタされたメッセージ: {word}")
            return  # このメッセージを処理しない
    
    # 通常のメッセージを処理
    await event.reply(f"受信: {text}")
```

### ブラックリストフィルタ

```python
# 設定ファイルやストレージからブラックリストをロード
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"ブラックリストユーザー: {user_id}")
        return  # このメッセージを処理しない
    
    # 通常のメッセージを処理
    await event.reply(f"こんにちは、{user_id}")
```

## 多プラットフォーム対応

### プラットフォーム固有の応答

```python
@command("help", help="ヘルプを表示")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("yunhuプラットフォームのヘルプ...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("一般的なヘルプ情報")
```

### プラットフォームの機能検出

```python
@command("rich", help="リッチテキストメッセージを送信")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # yunhuはHTMLをサポート
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>太字テキスト</b><i>斜体テキスト</i>"
        )
    elif platform == "telegram":
        # TelegramはMarkdownをサポート
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**太字テキスト** *斜体テキスト*"
        )
    else:
        # その他のプラットフォームはプレーンテキストを使用
        await event.reply("太字テキスト 斜体テキスト")
```

## メッセージ送信の高度な機能（リトライ/タイムアウト/一括送信）

`event.reply()` だけでなく、アダプタの Send DSL を使って、失敗時の自動リトライ、タイムアウト、成功後の処理、複数メッセージの一括送信などのより複雑な送信シナリオを実現できます。

> 以下の例では、`event.get_detail_type()` と `event.get_target_id()` を使用して、イベントからターゲットの種類とIDを取得しています（グループチャットの場合は group_id、プライベートチャットの場合は user_id を自動的に取得）。ハードコードを避けてください。

### 送信成功後に処理を実行

```python
@command("pay", help="支払いをシミュレート")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # 支払い成功後にポイントを減算
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("支払い成功、10ポイントを減算しました"))
```

### 失敗時のリトライ + タイムアウト

```python
@command("notice", help="重要な通知を送信")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 最大3回リトライ、各リトライは10秒でタイムアウト
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"通知送信失敗: {ctx.error}"))
            .Text("これは重要な通知です"))
    # 待たずにバックグラウンドで送信
```

### 複数メッセージの一括送信

1つのチェーンで複数のメッセージを送信し、一括で処理できます：

```python
@command("announce", help="公告を送信")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # 複数のメッセージを作成し、一括で送信（デフォルトは並列）
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 今日の公告")
                    .Image("https://example.com/banner.jpg")
                    .Text("詳細は上記の画像をご覧ください")
                    .Retry(2)            # 失敗した項目はそれぞれリトライ
                    .send_all())
    sdk.logger.info(f"一括送信完了、合計 {len(results)} 件")
```

> より詳細なルールと一括送信の説明は [プラットフォームの機能ガイド](../platform-guide/README.md#送信ルールデコレーター) を参照してください。

## 権限制御

### 管理者チェック

```python
# マスターのリストを設定
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """フレームワークのマスターかチェック"""
    return user_id in MASTERS

@command("master", help="フレームワークマスター用コマンド")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("権限がありません。このコマンドはフレームワークマスターのみ使用できます")
        return
    
    await event.reply("フレームワークマスター用コマンドが正常に実行されました")

@command("addmaster", help="フレームワークマスターを追加")
async def addmaster_handler(event):
    if not is_master(event.get_user_id()):
        return
    
    args = event.get("text", "").split()
    if len(args) < 2:
        await event.reply("使い方: /addmaster <ユーザーID>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"フレームワークマスターを追加しました: {new_master}")
```

### グループ権限

```python
@command("groupinfo", help="グループ情報を表示")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("このコマンドはグループチャットでのみ使用できます")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループID: {group_id}, あなたのID: {user_id}")
```

## メッセージの統計

### メッセージのカウント

> **注意**：以下の例では `sdk.storage.get/set` を使用して簡単なカウントを行っています。高並行な環境では、アトミック性を保証するために `sdk.storage.transaction()` を使用することを推奨します。

```python
@message.on_message()
async def count_handler(event):
    # 統計を取得
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # 統計を更新
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # 保存
    sdk.storage.set("message_stats", stats)

@command("stats", help="メッセージの統計を表示")
async def stats_handler(event):
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    top_users = sorted(
        stats["by_user"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    top_text = "\n".join(
        f"{uid}: {count} 件のメッセージ" for uid, count in top_users
    )
    
    await event.reply(f"総メッセージ数: {stats['total']}\n\n活発なユーザー:\n{top_text}")
```

## 検索機能

### 簡単な検索

> **注意**：以下の例ではメモリ内のリストにメッセージ履歴を保存しています。**アプリケーションの再起動後はデータが失われます**。本番環境では、`sdk.storage` または SQLite テーブルを使用して永続化を推奨します。

```python
from ErisPulse.Core.Event import command, message

# メッセージ履歴を保存
message_history = []

@message.on_message()
async def store_handler(event):
    """メッセージを保存して検索可能にする"""
    user_id = event.get_user_id()
    text = event.get_text()
    
    message_history.append({
        "user_id": user_id,
        "text": text,
        "time": event.get_time()
    })
    
    # 履歴の数を制限
    if len(message_history) > 1000:
        message_history.pop(0)

@command("search", help="メッセージを検索")
async def search_handler(event):
    args = event.get_command_args()
    
    if not args:
        await event.reply("検索キーワードを入力してください")
        return
    
    keyword = " ".join(args)
    results = []
    
    # 履歴を検索
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("一致するメッセージが見つかりません")
        return
    
    # 結果を表示
    result_text = f"{len(results)} 件の一致するメッセージが見つかりました:\n\n"
    for i, msg in enumerate(results[:10], 1):  # 最大10件表示
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## 画像処理

### 画像のダウンロードと保存

```python
from ErisPulse.Core import client

@message.on_message()
async def image_handler(event):
    """画像メッセージを処理"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # SDKの内蔵クライアントを使って画像をダウンロードすることを推奨
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # ファイルに保存
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"画像を保存しました: {filename}")
                    await event.reply("画像を保存しました")
```

### 画像認識の例

> **注意**：以下の例ではプレースホルダAPIアドレスを使用しています。実際の使用では、独自の画像認識サービスに置き換えてください。

```python
from ErisPulse.Core import client

@command("identify", help="画像を認識")
async def identify_handler(event):
    """メッセージ内の画像を認識"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # 画像認識APIを呼び出す
            result = await _identify_image(file_url)
            
            await event.reply(f"認識結果: {result}")
            return
    
    await event.reply("画像が見つかりません")

async def _identify_image(url):
    """画像認識APIを呼び出す (例) - SDKの内蔵クライアントを使用"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "認識失敗")
```

## 次のステップ

- **機能を実装し、長期間実行したい**：[デプロイガイド](../user-guide/deployment.md) を参照し、Docker / systemd デーモンとバックアップアップデートの方法を確認してください。
- **開発した機能を他人に配布したい**：[モジュール開発入門](../developer-guide/modules/getting-started.md) から始め、スクリプトをインストール可能なモジュールにアップグレードしてください。
- **設定を調整したり、「モジュールが反応しない」問題を調査したい**：[設定ファイルの説明](../user-guide/configuration.md) と [スコープ](../advanced/scope.md) を確認してください。

## IDE 补全

> 来源: `docs/ja/getting-started/ide-completion.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/ja/getting-started/ide-completion.md）

# 型スタブ生成（IDE 補完）

> [!TIP]
> **このドキュメントを読むべきケース**：IDE の補完にアダプターのプラットフォーム固有メソッド（例：云湖の `Board`）やモジュールのカスタムメソッドが表示されない場合は、`epsdk types` コマンドを 1 回実行して型スタブを生成すれば解決します。不要であれば読み飛ばしてください。

ErisPulse は entry-points を通じてモジュール/アダプターを動的に検出するため、エントリーポイントからは静的な段階でユーザークラスの具体的な型を知ることができません。
`epsdk types` コマンドは、インストール済みのモジュール/アダプターをスキャンして型スタブファイルを生成します。これにより、ユーザーはこれらの型を変数アノテーションとして使用できるようになり、IDE 補完を受けられます。

## 核心設計原則

スタブファイルは**型のみをエクスポート**し、実行時のインスタンスは一切提供しません。

- すべてのインポートは ``TYPE_CHECKING`` の下で行われ、**実行時のオーバーヘッドはゼロ、動作の変更も一切ありません**
- クラス名はエントリーポイント名の PascalCase 形式を採用します（例: ``yunhu`` → ``Yunhu``）。これは ``sdk.adapter.get()`` / ``sdk.module.get()`` に渡す名前に対応しています
- ユーザーはコード内で通常通り ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` を使用してインスタンスを取得しますが、インポートされた型は**変数の型注釈**にのみ使用します

## 基本的な使い方

プロジェクトのルートディレクトリで実行します：

```bash
epsdk types
```

現在のディレクトリに `_ep_types.py` が生成され、インストール済みのすべてのモジュール/アダプタの型が含まれます。

## コード内での使用方法

```python
from _ep_types import MyModule, Yunhu
from ErisPulse import sdk

# 導入された型を変数の型ヒントとして使用することで、IDE がそのクラスのメソッドを補完します
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← IDE が hello を補完

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← プラットフォーム固有のメソッドを補完
```

## 動作原理

1. `erispulse.adapter` / `erispulse.module` entry-points のスキャン
2. サブプロセスを介して、対象の Python 環境内でインスペクションを行い、各アダプタ/モジュールの実際のクラス情報を収集（モジュールパスと限定名を含む）
3. `.py` ファイルを生成し、以下を含む：
   - `TYPE_CHECKING` の下ではすべての ``from xxx import Yyy as Zzz`` が有効
   - ``Zzz`` は entry-point 名の PascalCase 形式
4. IDE は ``TYPE_CHECKING`` 部分を読み取り、補完を提供する。実行時にはコードは一切実行されない

生成されたスタブの例：

```python
# _ep_types.py（自動生成）
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # アダプタ
    from MyAdapter.Core import MyAdapter as MyAdapter
    from YunhuAdapter.Core import YunhuAdapter as Yunhu

    # モジュール
    from MyModule.Core import Main as MyModule

    __all__ = ['MyAdapter', 'Yunhu', 'MyModule']
```

## コマンドオプション

| オプション | 説明 |
|------|------|
| `-o, --output PATH` | 出力ファイルのパスを指定します（デフォルト: `./_ep_types.py`） |
| `--force` | 既存のスタブファイルを上書きします |
| `--adapters-only` | アダプターのみをスキャンします |
| `--modules-only` | モジュールのみをスキャンします |

## 再生成のタイミング

- 新しいモジュールやアダプターをインストール/アンインストールした後
- モジュール/アダプターが公開 API を更新した後
- IDEの補完が機能しない、または型が期限切れになった場合

## SendDSL 標準メソッドとの関係

`SendDSL` 基底クラスには、標準の送信メソッド（Text/Image/Voice/Video/File）が既に組み込まれており、どのような方法で取得した `SendDSL` インスタンスでも、これらのメソッドが補完されます。  
`types` コマンドは主に、**プラットフォーム固有のメソッド**（例：雲湖の `Board`、沙盒の `Dice`）および**モジュール固有のメソッド**を補完するために使用されます。

## 次のステップ

- **どの送信メソッドがすべてのプラットフォームで共通して使えるか知りたい**：[SendDSL 詳解](../developer-guide/adapters/send-dsl.md) をご覧ください。Text / Image / Voice などの標準メソッドの権威ある説明が載っています
- **独自のアダプターを開発している場合**：[アダプター開発入門](../developer-guide/adapters/getting-started.md) からアダプタープロジェクトの作成を始めましょう
