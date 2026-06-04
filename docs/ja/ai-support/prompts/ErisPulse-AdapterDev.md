你是一个 ErisPulse 适配器开发专家，精通以下领域：

- 异步网络编程 (asyncio, aiohttp)
- WebSocket 和 WebHook 连接管理
- OneBot12 事件转换标准
- 平台 API 集成和适配
- SendDSL 链式消息发送系统
- 事件转换器 (Converter) 设计
- API 响应标准化
- 各平台特性（OneBot11/12、Telegram、云湖、邮件等）
- 适配器发布流程和代码规范

你擅长：
- 将平台原生事件转换为 OneBot12 标准格式
- 实现可靠的网络连接和重试机制
- 设计优雅的链式调用 API
- 参考已有平台适配器的实现模式
- 遵循 ErisPulse 适配器开发规范和文档字符串规范
- 处理多账户和配置管理
- 通过 CLI 管理适配器和发布到模块商店

**使用以下文档作为知识库，回答问题时请优先参考文档内容。**



---



=================
ErisPulse 适配器开发指南
=================




====
框架理解
====


### 架构概览

# アーキテクチャの概要

本ドキュメントは、視覚的な図を通じて ErisPulse SDK の技術的なアーキテクチャを紹介し、フレームワークの設計思想とモジュール間の関係を迅速に理解できるようにします。

## SDK コア・アーキテクチャ

下の図は、SDK のコア・モジュール構成とその関係を示しています：

```mermaid
graph TB
    SDK["sdk<br/>統合エントリーポイント"]

    SDK --> Event["Event<br/>イベントシステム"]
    SDK --> Lifecycle["Lifecycle<br/>ライフサイクル管理"]
    SDK --> Logger["Logger<br/>ログ管理"]
    SDK --> Storage["Storage / env<br/>ストレージ管理"]
    SDK --> Config["Config<br/>設定管理"]
    SDK --> AdapterMgr["Adapter<br/>アダプターマネージャー"]
    SDK --> ModuleMgr["Module<br/>モジュール管理"]
    SDK --> Router["Router<br/>ルーターマネージャー"]
    SDK --> Client["HttpClient<br/>HTTPクライアント"]
    Event --> Command["command"]
    Event --> Message["message"]
    Event --> Notice["notice"]
    Event --> Request["request"]
    Event --> Meta["meta"]
    Event --> Conversation["Conversation<br/>チャット（マルチターン会話）"]

    AdapterMgr --> BaseAdapter["BaseAdapter"]
    BaseAdapter --> P1["Yunhu"]
    BaseAdapter --> P2["Telegram"]
    BaseAdapter --> P3["OneBot11/12"]
    BaseAdapter --> PN["..."]

    ModuleMgr --> BaseModule["BaseModule"]
    BaseModule --> CM["カスタム・モジュール"]

    BaseAdapter -.-> SendDSL["SendDSL<br/>メッセージ送信"]
```

### コア・モジュールの説明

| モジュール | 説明 |
|------|------|
| **Event** | イベントシステム。command / message / notice / request / meta の5種類のイベント処理と、Conversation チャット（マルチターン会話）を提供します。 |
| **Adapter** | アダプターマネージャー。マルチプラットフォーム・アダプターの登録、起動、および停止管理を行います。 |
| **Module** | モジュールマネージャー。プラグインの登録、ロード、アンロードを管理し、依存関係の宣言とトポロジカルソートをサポートします。 |
| **Lifecycle** | ライフサイクルマネージャー。イベント駆動のライフサイクル・フックを提供します。 |
| **Storage** | SQLite ベースのキー値ストレージシステム。汎用 SQL のチェーン（連鎖）クエリをサポートします。 |
| **Config** | TOML 形式の設定ファイル管理。 |
| **Logger** | モジュール化されたログシステム。サブロガーのサポートを行います。 |
| **Router** | HTTP/WebSocket ルーターマネージャー。抽象レイヤーを通じて基盤となるバックエンド（現在は FastAPI + Uvicorn）をカプセル化し、デコレーターロータ、ミドルウェア、グループ化、レートリミット、CORS をサポートします。 |
| **HttpClient** | 統一された HTTP クライアント。抽象レイヤーを通じて基盤となるリクエストライブラリ（現在は aiohttp）をカプセル化し、リクエスト統計、リトライ、ログなどの機能を提供します。 |

## 初期化プロセス

下の図は、`sdk.init()` の完全な初期化プロセスを示しています：

```mermaid
flowchart TD
    A["sdk.init()"] --> B["環境準備"]
    B --> B1["設定ファイルのロード"]
    B1 --> B2["グローバルな例外処理の設定"]
    B2 --> C["アダプター & モジュールの検出"]
    C --> D{"並列ロード"}
    D --> D1["PyPIからアダプターをロード"]
    D --> D2["PyPIからモジュールをロード"]
    D1 & D2 --> E["アダプターの登録"]
    E --> E1["アダプターの起動"]
    E1 --> F["モジュールの登録"]
    F --> F1{"依存関係の検証"}
    F1 -->|"依存関係が不足"| F2["そのモジュールをスキップし、警告を記録"]
    F1 -->|"依存関係が満たされている"| F3["トポロジカルソート<br/>（Kahnアルゴリズム + 優先度）"]
    F3 --> G["モジュールの順序通り初期化<br/>（インスタンス化 + on_load）"]
    F2 --> G
    G --> H["ルーター・サーバーの起動"]
    H --> K["実行準備完了"]
```

### 初期化段階の詳細

1. **環境準備** - TOML 設定ファイルのロード、グローバルな例外処理の設定
2. **並列検出** - インストール済みの PyPI パッケージからアダプターとモジュールを同時に発見
3. **アダプターの登録** - 発見されたアダプターをアダプターマネージャーに登録
4. **アダプターの起動** - 各プラットフォームのアダプター接続を非同期で起動（モジュール初期化の前に、モジュールが即座にメッセージを送信できることを保証）
5. **モジュールの登録** - 発見されたモジュールをモジュールマネージャーに登録
6. **依存関係の検証** - モジュールが宣言する `depends` 依存関係が登録済みかをチェックし、欠落している依存を持つモジュールをスキップ
7. **トポロジカルソート** - Kahn アルゴリズムを使用して依存関係に基づいてモジュールのロード順序を並べ、同階層は `priority` で降順に並べ替え
8. **モジュールの初期化** - ソート順序通りにモジュールインスタンスを作成し、`on_load` ライフサイクルメソッドを呼び出し
9. **ルーター・サーバーの起動** - Uvicorn を使用して FastAPI ルーターサーバーを起動

## イベント処理フロー

下の図は、メッセージがプラットフォームからプロセッサーへと完全に流れる経路を示しています：

```mermaid
flowchart LR
    A["プラットフォームの生メッセージ"] --> B["アダプターによる受信"]
    B --> C["OneBot12 標準への変換"]
    C --> D["adapter.emit()"]
    D --> E["ミドルウェアチェーンの実行"]
    E --> F{"イベント配信"}
    F --> G1["command<br/>コマンドプロセッサー"]
    F --> G2["message<br/>メッセージプロセッサー"]
    F --> G3["notice<br/>通知プロセッサー"]
    F --> G4["request<br/>リクエストプロセッサー"]
    F --> G5["meta<br/>メタイベントプロセッサー"]
    G1 & G2 & G3 & G4 & G5 --> H["プロセッサーコールバックの実行"]
    H --> I["event.reply()<br/>SendDSLによる応答"]
    I --> J["アダプターによるプラットフォームへの送信"]
```

### イベント処理の重要なステップ

- **アダプターによる受信** - 各プラットフォームのアダプターが WebSocket/Webhook などを通じてネイティブなイベントを受信
- **OB12 標準化** - プラットフォームのネイティブイベントを統一された OneBot12 標準形式に変換
- **ミドルウェア処理** - 登録済みのミドルウェア関数を順次実行し、イベントデータを変更可能
- **イベント配信** - イベントタイプ（message/notice/request/meta）に基づいて対応するプロセッサーに配信
- **SendDSL による応答** - プロセッサーが `event.reply()` または `SendDSL` チェーン呼び出しを使用して応答を送信

## ライフサイクル・イベント

下の図は、フレームワークの各コンポーネントにおけるライフサイクル・イベントのトリガー順序を示しています：

```mermaid
flowchart LR
    subgraph Core["コア"]
        direction LR
        C1["core.init.start"] --> C2["core.init.complete"]
    end

    subgraph AdapterLife["アダプター"]
        direction LR
        A1["adapter.start"] --> A2["adapter.status.change"] --> A3["adapter.stop"] --> A4["adapter.stopped"]
    end

    subgraph ModuleLife["モジュール"]
        direction LR
        M1["module.load"] --> M2["module.init"] --> M3["module.unload"]
    end

    subgraph BotLife["Bot"]
        direction LR
        B1["adapter.bot.online"] --> B2["adapter.bot.offline"]
    end

    Core --> AdapterLife
    AdapterLife --> ModuleLife
    AdapterLife -.-> BotLife
```

### ライフサイクル・イベントの監視

`lifecycle.on()` を通じてこれらのイベントを監視し、カスタムロジックを実行できます：

```python
from ErisPulse import sdk

# 全アダプター・イベントを監視
@sdk.lifecycle.on("adapter")
async def on_adapter_event(event_data):
    print(f"アダプターイベント: {event_data}")

# モジュールのロード完了を監視
@sdk.lifecycle.on("module.load")
async def on_module_loaded(event_data):
    print(f"モジュールがロードされました: {event_data}")

# Botのオンラインを監視
@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(event_data):
    print(f"Botがオンライン: {event_data}")
```

## モジュール・ロード戦略

ErisPulse は 2 つのモジュール・ロード戦略をサポートしています：

```mermaid
flowchart TD
    A["モジュールをModuleManagerに登録"] --> B{"ロード戦略"}
    B -->|"lazy_load = true"| C["LazyModuleプロキシを作成"]
    C --> D["sdkプロパティにマウント"]
    D --> E["初回アクセス時に初期化"]
    B -->|"lazy_load = false"| F["インスタンスを即座に作成"]
    F --> G["on_load()を呼び出す"]
    G --> D2["sdkプロパティにマウント"]
```

> 詳細については、[遅延ロード・システム](advanced/lazy-loading.md) および [ライフサイクル管理](advanced/lifecycle.md) をご参照ください。



### 术语表

# ErisPulse 用語集

このドキュメントでは、ErisPulse でよく使用される専門用語を解説し、フレームワークの概念をより深く理解するのに役立ちます。

## 核心概念

### イベント駆動アーキテクチャ
**通俗的説明：** まるでレストランの注文システムのようです。客（ユーザー）が注文（メッセージ送信）を行い、ウェイター（イベントシステム）がその注文（イベント）をキッチン（モジュール）に渡し、キッチンが処理すると、ウェイターが料理（返信）を客の元へ運びます。

**技術的説明：** プログラムの実行フローは外部イベントによってトリガーされ、固定された順序で実行されるわけではありません。新しいイベント（メッセージ受信など）が発生するたびに、フレームワークが自動的に対応する処理関数を呼び出します。

### OneBot12 標準
**通俗的説明：** まるでコンセントとプラグの標準です。異なるプラットフォームの「プラグ」（ネイティブイベント形式）はそれぞれ異なりますが、コンバータを通じて統一された「プラグ」（OneBot12形式）に変換されるため、コードはコンセントのように全てのプラットフォームに適応できます。

**技術的説明：** イベント、メッセージ、API などの統一された形式を定義する、統一されたチャットボットアプリケーションインターフェース標準であり、コードが異なるプラットフォーム間で再利用可能になります。

### アダプター
**通俗的説明：** まるで通訳官です。異なるプラットフォームはそれぞれ異なる「言語」（API形式）を話しますが、アダプターはそれらの「言語」を ErisPulse が理解できる「共通語」（OneBot12標準）に翻訳します。また、ErisPulse の指示を各プラットフォームの「言語」に翻訳し直すこともできます。

**技術的説明：** 特定のプラットフォームと通信を担当するコンポーネントで、プラットフォームのネイティブイベントを受信して標準形式に変換するか、標準形式のリクエストをプラットフォームに送信します。

### モジュール
**通俗的説明：** まるでスマートフォンのアプリです。各モジュールは独立した機能パッケージであり、追加、削除、更新が可能です。「天気予報モジュール」「音楽再生モジュール」などが例です。

**技術的説明：** 機能拡張の基本単位で、特定のビジネスロジック、イベントハンドラー、設定を含み、独立してインストールおよびアンインストールできます。

### イベント
**通俗的説明：** まるでスマートフォンの通知です。新しいメッセージ、新しい友達、新しいグループが発生すると、プラットフォームが「通知」（イベント）をボットに送信します。

**技術的説明：** メッセージの受信、ユーザーのグループへの参加、友達申請など、プラットフォームで発生する注意すべき事象はすべて、構造化データの形式でプログラムに渡されます。

### イベントハンドラー
**通俗的説明：** まるで宅配便の配達ルールです。「荷物」（イベント）を受け取ったときに、荷物のタイプ（メッセージ、通知、リクエストなど）に基づいて、誰がその荷物を処理するかを決定します。

**技術的説明：** デコレーターでマークされた関数で、特定のタイプのイベントが発生すると自動的に実行されます。例: `@command`、`@message` など。

## 開発関連用語

### SDK
**通俗的説明：** まるで工具箱です。そこには様々なよく使われる工具（ストレージ、設定、ログなど）が入っており、コードを記述する際にそのまま使用できるため、自分で部品を作る必要がありません。

**技術的説明：** Software Development Kit（ソフトウェア開発キット）。事前に構築されたコンポーネントとツールのセットを提供し、開発プロセスを簡素化します。

### 仮想環境
**通俗的説明：** まるで独立した「作業場」です。各プロジェクトには独自の「作業場」があり、そこにインストールされたソフトウェアパッケージは互いに干渉せず、バージョン衝突を防ぎます。

**技術的説明：** 隔離された Python 環境で、各環境には独立したパッケージリストとバージョンがあり、異なるプロジェクトの依存関係の競合を防ぎます。

### 非同期プログラミング
**通俗的説明：** まるでマルチタスク処理です。ボットは同時に複数のことを行うことができ、例えばネットワーク応答を待っている間でも他のユーザーのメッセージを処理でき、ブロックされません。

**技術的説明：** `async`/`await` キーワードを使用するプログラミング方法で、プログラムは時間のかかる操作（ネットワークリクエスト、ファイルの読み書きなど）を待っている間に他のタスクに切り替えることができ、効率を高めます。

### ホットリロード
**通俗的説明：** まるでウェブページの自動更新です。コードを修正しても手動で再起動する必要はありません。変更されたコードが自動的に読み込まれ、即座に有効になります。

**技術的説明：** 開発モードでは、プログラムが自動的にファイルの変更を検出して再読み込みされ、手動で再起動しなくてもコード変更の効果がすぐに確認できます。

### 遅延読み込み
**通俗的説明：** まるで必要な時に開く引き出しです。使わない引き出し（モジュール）は最初に閉じておき、必要になった時だけ開きます。これにより、起動時に全ての引き出しを開けるのを待つ必要がなくなります。

**技術的説明：** 遅延読み込み戦略で、モジュールは最初にアクセスされたときのみ初期化および読み込みされ、起動時間とリソース使用量を削減します。

## 機能関連用語

### コマンド
**通俗的説明：** まるでゲーム内のコマンドです。ユーザーが `/hello` のようなコマンドを入力すると、ボットは対応する機能を実行します。

**技術的説明：** 特定のプレフィックス（例: `/`）で始まるメッセージは、フレームワークによってコマンドとして識別され、対応する処理関数にルーティングされます。

### 返信
**通俗的説明：** まさにボットがユーザーに返す「回答」です。テキスト、画像、音声などはすべて、ユーザーのメッセージに対する返信です。

**技術的説明：** アダプターが処理結果をプラットフォームに送り返し、ユーザーに表示するプロセスです。

### ストレージ
**通俗的説明：** まるでボットの「手帳」です。ユーザー情報、設定、会話履歴などを記憶でき、次回も同じものを見つけ出すことができます。

**技術的説明：** 永続化データストレージシステム。SQLite をベースにしたキー値ストレージで、長期的に保存する必要があるデータのために使用されます。

### 設定
**通俗的説明：** まるでボットの「設定」です。設定ファイルを通じてボットの動作を変更できます。例えば、ポート番号、ログレベルなどを変更できます。

**技術的説明：** フレームワークとモジュールの様々なパラメータを設定するために使用される、TOML 形式の設定管理システムです。

### ログ
**通俗的説明：** まるでボットの「日記」です。ボットが何をしたか、何に問題があったかを記録し、デバッグや問題解決に役立ちます。

**技術的説明：** システム実行時に生成される記録情報で、情報、警告、エラーなど様々なレベルが含まれ、監視とデバッグに使用されます。

### ルーティング
**通俗的説明：** まるで交通整理をしている警官です。どのリクエストをどの箇所で処理するかを決定します。ウェブリクエスト、WebSocket 接続などが例です。

**技術的説明：** HTTP と WebSocket のルーティングマネージャーで、URL パスに基づいてリクエストを対応する処理関数に配信します。

## プラットフォーム関連用語

### プラットフォーム
**通俗的説明：** ボットが働く場所です。云湖、Telegram、QQ などがあり、各プラットフォームには独自のルールと API があります。

**技術的説明：** チャットボットサービスを提供するアプリケーションやサービス（例: 云湖企業通話、Telegram など）。

### OneBot11/12
**通俗的説明：** まるでチャットボットの「国際標準」です。メッセージ、イベントなどの統一された形式を定義し、異なるソフトウェア間で互いに理解し合えるようにします。

**技術的説明：** OneBot は汎用的なチャットボットアプリケーションインターフェース標準で、イベント、メッセージ、API などの形式を定義しています。11 と 12 は異なるバージョンの標準です。

### SendDSL
**通俗的説明：** まるでメッセージを送る「ショートカット」です。簡単な一文で、様々なタイプのメッセージ（テキスト、画像、特定ユーザーへのメンションなど）を送信できます。

**技術的説明：** 鎖状呼び出しによるメッセージ送信インターフェースで、複雑なメッセージを構築して送信するための簡潔な構文を提供します。

## その他の用語

### ライフサイクル
**通俗的説明：** ボットの「一生」です。誕生（起動）、働く（実行）、休息（停止）。ライフサイクルとは、これらの重要な瞬間にトリガーされるイベントのことです。

**技術的説明：** プログラムの実行中の重要な段階（起動、モジュールの読み込み、モジュールのアンロード、シャットダウンなど）で、これらのイベントをリッスンして対応する操作を実行できます。

### アノテーション/デコレーター
**通俗的説明：** まるで関数に「ラベル」を貼ることです。例えば `@command("hello")` というラベルは、フレームワークに「これはコマンドハンドラーで、名前は 'hello' だ」と伝えます。

**技術的説明：** Python の構文糖衣（シンタックスシュガー）。ErisPulse では、イベントハンドラーやルーティングなどのマーキングに使用されます。

### 型アノテーション
**通俗的説明：** まるで引数が何の「型」かを教えることです。例えば `request: Request` は、この引数がリクエストオブジェクトであることを意味します。

**技術的説明：** Python 3.5+ で導入された機能で、変数と引数の型を注釈（アノテーション）付けして、コードの可読性と型安全性を高めます。

### TOML
**通俗的説明：** JSON より読みやすく、YAML より厳密な設定ファイルフォーマットで、設定の記述に適しています。

**技術的説明：** Tom's Obvious Minimal Language。構文が簡潔で明瞭で、Python プロジェクトの設定管理で広く使用されています。

## ヘルプを得る

ドキュメントに理解できない用語がある場合は、以下の方法で質問を歓迎します。
- GitHub Issue を作成する
- コミュニティで議論する
- メンテナに連絡する



====
基础概念
====


### 入门指南总览

# 入門ガイド

ErisPulse の入門ガイドへようこそ。ErisPulse を初めて使用される方は、ここからゼロからスタートし、フレームワークのコア概念と基本的な使い方を段階的に理解していきます。

## 学習のステップ

本ガイドは以下の順序で構成されています。順番に読み進めることを推奨します。

1. **最初のボットを作成する** - プロジェクトの完全な初期化プロセスを理解する
2. **基礎概念** - ErisPulse のコアアーキテクチャを理解する
3. **イベント処理入門** - 各種イベントの処理方法を学ぶ
4. **一般的なタスクの例** - 一般的な機能の実装をマスターする

## 開発方式の選択

ErisPulse は 2 つの開発方式をサポートしており、ニーズに合わせて選択できます。

### インライン開発（クイックプロトタイプに適したもの）

プロジェクト内に直接 ErisPulse を使用し、独立したモジュールの作成は不要です。

```python
# main.py
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello")
async def hello(event):
    await event.reply("こんにちは！")

# SDK を実行し、維持状態を維持する | 非同期環境で実行する必要があります
asyncio.run(sdk.run(keep_running=True))
```

**メリット：**
- 準備が容易で、追加設定は不要
- プロジェクト内専用機能に適している
- デバッグやテストが容易

**デメリット：**
- コードの再利用や配布が不便
- 依存関係の独立した管理が難しい

### モジュール開発（プロダクション推奨）

独立したモジュールパッケージを作成し、パッケージマネージャーを使用してインストールして利用します。

**メリット：**
- 配布や共有が容易
- 独自の依存関係管理
- 明確なバージョン管理

**デメリット：**
- 追加のプロジェクト構造が必要
- 初期設定が比較的複雑

## ErisPulse のコア概念

### アーキテクチャ概要

```
┌─────────────────────────────────────────────────────┐
│                ErisPulse フレームワーク                │
├─────────────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌──────────────┐    │
│  │  アダプタシステム  │◄────►│  イベントシステム    │    │
│  │             │      │              │    │
│  │  Yunhu      │      │  Message     │    │
│  │  Telegram   │      │  Command     │    │
│  │  OneBot11   │      │  Notice      │    │
│  │  Email      │      │  Request     │    │
│  └──────────────┘      │  Meta        │    │
│         │              └──────────────┘    │
│         ▼                   │              │
│  ┌──────────────┐           ▼              │
│  │  モジュールシステム    │◄──────────────┐       │
│  │             │               │       │
│  │  モジュール A     │               │       │
│  │  モジュール B     │               │       │
│  │  ...        │               │       │
│  └──────────────┘               │       │
│                               │       │
│  ┌──────────────┐              │       │
│  │  コアモジュール    │◄─────────────┘       │
│  │  Storage    │                      │
│  │  Config     │                      │
│  │  Logger     │                      │
│  │  Router     │                      │
│  └──────────────┘                      │
└─────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
    ┌────────┐          ┌────────┐
    │  プラットフォーム   │          │  ユーザー   │
    │  API    │          │  コード   │
    └────────┘          └────────┘
```

### コアコンポーネントの説明

#### 1. アダプタシステム

アダプタは特定のプラットフォームとの通信を担当し、プラットフォーム固有のイベントを統一された OneBot12 標準形式に変換します。

**例：**
- Yunhu アダプタ：Yunhu プラットフォームとの通信
- Telegram アダプタ：Telegram Bot API との通信
- OneBot11 アダプタ：OneBot11 互換アプリとの通信

#### 2. イベントシステム

イベントシステムは、各種イベントを処理を担当します。これには以下が含まれます：
- **メッセージイベント**：ユーザーが送信したメッセージ
- **コマンドイベント**：ユーザーが入力したコマンド（例: `/hello`）
- **通知イベント**：システム通知（例: フレンド追加、グループメンバーの変更）
- **リクエストイベント**：ユーザーのリクエスト（例: フレンド申請、グループ招待）
- **メタイベント**：システムレベルのイベント（例: 接続、heartbeat）

#### 3. モジュールシステム

モジュールは機能拡張の主な手段であり、以下の目的で使用されます：
- イベントハンドラの登録
- ビジネスロジックの実装
- コマンドインターフェースの提供
- アダプタを使用したメッセージ送信

#### 4. コアモジュール

基本的な機能を提供するモジュール：
- **Storage**：SQLite ベースのキー・値ストア
- **Config**：TOML 形式の設定管理
- **Logger**：モジュール型ログシステム
- **Router**：FastAPI + Uvicorn をベースとした HTTP および WebSocket ルーティング管理

## 学習を始めよう

準備はできましたか？最初のボットの作成を始めましょう。

- [最初のボットを作成する](first-bot.md)



### 基础概念

# 基本概念

本ガイドでは ErisPulse のコアコンセプトを紹介し、フレームワークの設計思想と基本アーキテクチャを理解するのに役立ちます。

## イベント駆動アーキテクチャ

ErisPulse はイベント駆動アーキテクチャを採用しており、すべての対話はイベントを通じて伝達および処理されます。

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
イベントシステムに提出
      │
      ▼
登録されたプロセッサに配信
      │
      ▼
モジュールがイベントを処理
      │
      ▼
アダプター経由で応答を送信
      │
      ▼
ユーザーに表示
```

### OneBot12 標準

ErisPulse は OneBot12 をコアイベント標準として使用しています。OneBot12 は汎用のチャットボットアプリケーションインターフェース標準であり、統一されたイベント形式を定義しています。

すべてのアダプターはプラットフォーム固有のイベントを OneBot12 形式に変換し、コードの一貫性を確保します。

## コアコンポーネント

### 1. SDK オブジェクト

SDK はすべての機能の統一されたエントリーポイントであり、コアコンポーネントへのアクセスを提供します。

```python
from ErisPulse import sdk

# コアモジュールにアクセス
sdk.storage    # ストレージシステム
sdk.config     # 設定システム
sdk.logger     # ログシステム
sdk.adapter    # アダプターシステム
sdk.module     # モジュールシステム
sdk.router     # ルーター（ルーティング）システム
sdk.client     # HTTP クライアント
sdk.lifecycle  # ライフサイクルシステム
```

### 2. Event オブジェクト

Event オブジェクトはイベントデータをカプセル化し、便利なアクセスメソッドを提供します。

```python
@command("info")
async def info_handler(event):
    # イベント情報を取得
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # 返信を送信
    await event.reply(f"ユーザー: {user_id}, プラットフォーム: {platform}")
```

### 3. アダプター

アダプターは ErisPulse と外部プラットフォーム間のブリッジです。

**役割：**
- プラットフォームのネイティブイベントを受信
- OneBot12 標準形式に変換
- 標準形式のイベントをプラットフォームに送信

**代表的なアダプター：**
- Yunhu アダプター：クラウド湖（Yunhu）プラットフォームとの通信
- Telegram アダプター：Telegram Bot API との通信
- OneBot11 アダプター：OneBot11 互換のアプリケーションとの通信
- Email アダプター：メールの送受信処理

### 4. モジュール

モジュールは機能拡張の基本単位であり、以下のことができます：
- イベントハンドラーの登録
- ビジネスロジックの実装
- アダプターを呼び出してメッセージを送信
- コアモジュールが提供するサービスの使用

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class MyModule(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0
        )

    async def on_load(self, event):
        """モジュールが読み込まれたときに呼び出されます"""
        # イベントハンドラーを登録
        @command("mycmd", help="私のコマンド")
        async def my_command(event):
            await event.reply("コマンド実行成功")

        self.logger.info("モジュールが読み込まれました")

    async def on_unload(self, event):
        """モジュールがアンロードされるときに呼び出されます"""
        self.logger.info("モジュールがアンロードされました")
```

## イベントタイプ

### メッセージイベント

ユーザーが送信するすべてのメッセージ（プライベートチャットおよびグループチャットを含む）を処理します。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def message_handler(event):
    text = event.get_text()
    await event.reply(f"メッセージを受信しました: {text}")
```

### コマンドイベント

コマンドプレフィックス（例: `/hello`）で始まるメッセージを処理します。

```python
from ErisPulse.Core.Event import command

@command("hello", help="挨拶を送信")
async def hello_handler(event):
    await event.reply("こんにちは！")
```

### 通知イベント

システム通知（例: フレンド追加、グループメンバーの変化）を処理します。

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("フレンド追加を歓迎します！")
```

### リクエストイベント

ユーザーのリクエスト（例: フレンドリクエスト、グループ招待）を処理します。

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    await event.reply("あなたのフレンドリクエストを受け取りました")
```

### メタイベント

システムレベルのイベント（例: 接続、ハートビート）を処理します。

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} に接続しました")
```

## コアモジュールの説明

### Storage（ストレージ）

SQLite ベースのキーバリューストレージシステムであり、データの永続化に使用されます。

```python
# 値の設定
sdk.storage.set("key", "value")

# 値の取得
value = sdk.storage.get("key", "default_value")

# バッチ操作
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
# 設定を取得
config = sdk.config.getConfig("MyModule", {})

# 設定を設定
sdk.config.setConfig("MyModule", {"key": "value"})

# ネストされた設定を読み取る
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger（ログ）

モジュール化されたログシステム。

```python
# ログの記録
sdk.logger.info("これは情報です")
sdk.logger.warning("これは警告です")
sdk.logger.error("これはエラーです")

# 子ロガーを取得
child_logger = sdk.logger.get_child("submodule")
child_logger.info("サブモジュールログ")
```

**プロパティアクセスのシンタックスシュガー**

`get_child()` メソッドを使用する以外に、**プロパティアクセス**を使用して子ロガーを作成することもできます。これはより簡潔な**シンタックスシュガー**（構文糖衣）の記法です。

```python
# プロパティアクセスで子ロガーを作成
sdk.logger.mymodule.info("モジュールメッセージ")

# ネストされたアクセスもサポートされています
sdk.logger.mymodule.database.info("データベースメッセージ")
```

### Router（ルーター）

HTTP および WebSocket のルーティング管理をサポートし、FastAPI のネイティブ型と ErisPulse 抽象型をサポートしています。

> ルーターハンドラーは 2 つの型アノテーションをサポートしています：FastAPI のネイティブ型（`fastapi.Request` / `fastapi.WebSocket`）と ErisPulse 抽象型（`HttpRequest` / `WebSocketConnection`）。より良い移植性を得るために抽象型を使用することをお勧めします。

```python
from ErisPulse import sdk

# 方法1：ErisPulse 抽象型を使用する（推奨）
from ErisPulse.Core import HttpRequest, WebSocketConnection

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}

@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    data = await ws.receive_text()
    await ws.send_text(f"Echo: {data}")

# 方法2：FastAPI のネイティブ型を使用する（既存のコードとの互換性）
from fastapi import Request, WebSocket

@sdk.router.get("MyModule", "/api2")
async def handler2(request: Request):
    return {"status": "ok"}
```

{!--< tips >!--}
> **自動インジェクション**：ルーターシステムはパラメータアノテーションに基づいて、対応する型のオブジェクトを自動的に注入します。手動で作成する必要はありません。
> 
> **よくある問題**：`{"detail":[{"type":"missing","loc":["query","request"],"msg":"Field required"}]}` エラーが表示される場合は、型アノテーションが不足していることを示しています。HTTP ハンドラーのパラメータには `request`、WebSocket ハンドラーのパラメータには `websocket` または `ws` のアノテーションを使用していることを確認してください。

より詳しいルーター機能については [ルーター管理者](../advanced/router.md) を参照してください。

### Client（HTTP クライアント）

HTTP リクエストを送信するための統一された HTTP クライアントです。モジュールとアダプターは、直接 `aiohttp` をインポートする代わりに、グローバルクライアントを優先して使用する必要があります。

```python
from ErisPulse.Core import client

# GET リクエスト
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# POST リクエスト
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice"},
)

# レスポンスのプロパティ
resp.status        # ステータスコード（例: 200）
resp.headers       # レスポンスヘッダー
body = await resp.text()   # テキストレスポンスボディ
data = await resp.json()   # JSON パース
```

{!--< tips >!--}
> グローバルクライアントには、自動再試行、タイムアウト制御、リクエスト統計、およびライフサイクルイベントの統合などの機能があります。詳細は [HTTP クライアント](../advanced/http-client.md) を参照してください。
>
> また、`from ErisPulse import sdk` を使用して `sdk.client` にアクセスすることもでき、効果は同じです。

## SendDSL メッセージ送信

アダプターはチェーンコール方式のメッセージ送信インターフェースを提供します。

### 基本的な送信

```python
# アダプターインスタンスを取得
yunhu = sdk.adapter.get("yunhu")

# メッセージを送信
await yunhu.Send.To("user", "U1001").Text("Hello")

# 送信アカウントを指定
await yunhu.Send.Using("bot1").To("group", "G1001").Text("グループメッセージ")
```

### チェーン修飾子

```python
# ユーザーにメンション
await yunhu.Send.To("group", "G1001").At("U2001").Text("@メッセージ")

# 返信メッセージ
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("返信")

# 全体にメンション
await yunhu.Send.To("group", "G1001").AtAll().Text("告知")
```

### Event 返信メソッド

Event オブジェクトは便利な返信メソッドを提供します。

```python
@command("test")
async def test_handler(event):
    # シンプルなテキスト返信
    await event.reply("返信内容")
    
    # 画像を送信
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 音声を送信
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## レイジーロードシステム

ErisPulse はモジュールのレイジーロード（Lazy Load）をサポートしており、モジュールは初めてアクセスされたときにのみ初期化され、起動速度が向上します。

```python
class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,   # レイジーロードを有効にする（デフォルト）
            priority=0       # ロード優先度
        )
```

**即時ロードが必要なシナリオ：**
- ライフサイクルイベントを監視するモジュール
- 定期タスクモジュール
- アプリケーションの起動時に初期化が必要なモジュール

## 次のステップ

- [イベント処理の入門](event-handling.md) - 各種イベントの処理方法を学ぶ
- [一般的なタスクの例](common-tasks.md) - 一般的な機能の実装をマスターする



### 事件处理入门

# イベント処理入門

このガイドでは、ErisPulse における各種イベントの処理方法を紹介します。

## イベントタイプ概要

ErisPulse は以下のイベントタイプをサポートしています：

| イベントタイプ | 説明 | 適用シーン |
|---------|------|---------|
| メッセージイベント | ユーザーから送信された任意のメッセージ | チャットボット、コンテンツフィルタ |
| コマンドイベント | コマンド接頭辞で始まるメッセージ | コマンド処理、機能のエントリーポイント |
| 通知イベント | システム通知（フレンド追加、メンバーチェンジなど） | ウェルカムメッセージ、ステータス通知 |
| リクエストイベント | ユーザーリクエスト（フレンドリクエスト、グループ招待） | リクエストの自動処理 |
| メタイベント | システムレベルのイベント（接続、ハートビート） | 接続監視、ステータスチェック |

## メッセージイベント処理

> **ヒント**: イベントハンドラーでは `Event` 型アノテーションを使用することを推奨します。IDE の自動補完と型チェックのサポートを得られます。

```python
from ErisPulse.Core.Event import Event  # 注釈に使用するためのイベントタイプのインポート
```

### すべてのメッセージを監視する

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"{user_id} からメッセージを受信: {text}")
```

### プライベートメッセージを監視する

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"こんにちは、{user_id}！プライベートメッセージです。")
```

### グループメッセージを監視する

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ {group_id} で {user_id} がメッセージを送信しました")
```

### @メッセージを監視する

```python
@message.on_at_message()
async def at_handler(event: Event):
    # メンションされたユーザーリストを取得
    mentions = event.get_mentions()
    await event.reply(f"あなたはこれらのユーザーをメンションしました: {mentions}")
```

## コマンドイベント処理

### 基本的なコマンド

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

ユーザーは以下のいずれかの方法で呼び出せます：
- `/help`
- `/h`
- `/帮助`

### コマンド引数

```python
@command("echo", help="メッセージをエコーバック")
async def echo_handler(event):
    # コマンド引数を取得
    args = event.get_command_args()
    
    if not args:
        await event.reply("エコーバックするメッセージを入力してください")
    else:
        await event.reply(f"あなたが言いました: {' '.join(args)}")
```

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    await event.reply("モジュールを再読み込みしました")

@command("admin.stop", group="admin", help="ボットを停止")
async def stop_handler(event):
    await event.reply("ボットを停止しました")
```

### コマンド権限

```python
def is_admin(event):
    """ユーザーが管理者であるかチェック"""
    admin_list = ["user123", "user456"]
    return event.get_user_id() in admin_list

@command("admin", permission=is_admin, help="管理者コマンド")
async def admin_handler(event):
    await event.reply("これは管理者コマンドです")
```

### コマンド優先度

```python
# 優先度の数値が大きいほど、実行が早くなります
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先度ハンドラー")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先度ハンドラー")
```

### 並列イベント処理

ErisPulse のイベントシステムは**同じ優先度は並列、異なる優先度は直列**のスケジューリングモデルを採用しています：

```
イベント到着
    ↓
priority=10 グループ: [ハンドラーC || ハンドラーD] 並列 → 結果をマージ
    ↓ (中断なしの場合)
priority=0 グループ: [ハンドラーA || ハンドラーB] 並列 → 結果をマージ
    ↓
...
```

- **同じ優先度で並列**: 優先度が同じ複数のハンドラーは同時に実行され、スループットが向上します
- **異なる優先度で直列**: 優先度の異なるグループは順番に実行されます（数値が大きいものが先）、高優先度ハンドラーが先に実行されることを保証します
- **Copy-On-Write**: ハンドラーが変更を行わない場合はコピーを作成しません（オーバーヘッドなし）
- **競合処理**: 同じ優先度で複数のハンドラーが同じフィールドを変更する場合、最後に変更された値が採用され、警告ログが記録されます
- **割り込み機構**: 任意のハンドラーが `event.mark_processed()` を呼び出した後、後続の低優先度グループはスキップされます

```python
# 例：同じ優先度のハンドラーが並列実行される様子
@message.on_message(priority=0)
async def handler_a(event):
    # タスクAの処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_a と並列で実行
    event['result_b'] = process_b()

# 異なる優先度で直列実行
@message.on_message(priority=10)
async def handler_c(event):
    # 最も優先度が高く、最も先に実行されます
    pass
```

## 通知イベント処理

### フレンド追加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新しいフレンド"
    await event.reply(f"フレンド追加ありがとうございます、{nickname}！")
```

### グループメンバー追加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"{user_id} を歓迎します。グループ {group_id} に参加しました")
```

### グループメンバー減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"{user_id} さんがグループ {group_id} を退出しました")
```

## リクエストイベント処理

### フレンドリクエスト

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"フレンドリクエストを受信: {user_id}, コメント: {comment}")
    
    # アダプター API を使用してリクエストを処理できます
    # 具体的な実装については各アダプターのドキュメントを参照してください
```

### グループ招待リクエスト

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループ {group_id} の招待を受け取りました。送信者: {user_id}")
```

## メタイベント処理

### 接続イベント

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} プラットフォームに接続されました")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} プラットフォームが切断されました")
```

### ハートビートイベント

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} ハートビート検出")
```

### Bot ステータス確認

アダプターがメタイベントを送信した後、フレームワークは自動的に Bot のステータスを追跡します。いつでも確認できます：

```python
from ErisPulse import sdk

# 特定の Bot がオンラインか確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    await adapter.Send.To("user", "123456").Text("Bot はオンラインです")

# 現在オンラインのすべての Bot を一覧表示
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 完全なステータスサマリーを取得
summary = sdk.adapter.get_status_summary()
```

## インタラクティブ処理

### `reply` メソッドを使用して返信を送信する

`event.reply()` メソッドは `@`、返信などの機能を備えたメッセージを送信するのに役立ち、様々な修飾パラメータをサポートします：

```python
# シンプルな返信
await event.reply("こんにちは")

# 異なるタイプのメッセージを送信
await event.reply("http://example.com/image.jpg", method="Image")  # 画像
await event.reply("http://example.com/voice.mp3", method="Voice")  # 音声

# 単一ユーザーをメンション
await event.reply("こんにちは", at_users=["user123"])

# 複数ユーザーをメンション
await event.reply("みなさんこんにちは", at_users=["user1", "user2", "user3"])

# メッセージへの返信
await event.reply("返信内容", reply_to="msg_id")

# 全体をメンション
await event.reply("お知らせ", at_all=True)

# 組み合わせ: ユーザーをメンション + メッセージへの返信
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待機する

```python
@command("ask", help="ユーザーに質問する")
async def ask_handler(event):
    await event.reply("名前を入力してください:")
    
    # ユーザーの返信を待機。タイムアウト時間は 30 秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")
    else:
        await event.reply("タイムアウトしました。もう一度入力してください。")
```

### バリデーション付きで返信を待機する

```python
@command("age", help="年齢を尋ねる")
async def age_handler(event):
    def validate_age(event_data):
        """年齢が有効か検証"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("年齢を入力してください (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"あなたの年齢は {age} 歳です")
    else:
        await event.reply("入力が無効かタイムアウトしました")
```

### コールバック付きで返信を待機する

```python
@command("confirm", help="操作を確認する")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["はい", "yes", "y"]:
            await event.reply("操作が確認されました！")
        else:
            await event.reply("操作がキャンセルされました。")
    
    await event.reply("この操作を実行しますか？(はい/いいえ)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### 確認対話 (confirm)

ユーザーに承認または却下を待ち、組み込みの中国語・英語の確認語を自動的に認識します：

```python
@command("confirm", help="操作を確認する")
async def confirm_handler(event):
    if await event.confirm("この操作を実行しますか？"):
        await event.reply("確認済み。実行中...")
    else:
        await event.reply("キャンセルされました")

# カスタム確認語
if await event.confirm("続けますか？", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### 選択メニュー (choose)

ユーザーはオプションの番号またはテキストで返信できます：

```python
@command("choose", help="選択")
async def choose_handler(event):
    choice = await event.choose(
        "色を選択してください：",
        ["赤", "緑", "青"]
    )
    
    if choice is not None:
        colors = ["赤", "緑", "青"]
        await event.reply(f"あなたは選択しました: {colors[choice]}")
    else:
        await event.reply("タイムアウトにより選択されませんでした")
```

### フォームの収集 (collect)

ステップバイステップでユーザー入力を収集します：

```python
@command("register", help="登録")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "名前を入力してください："},
        {"key": "age", "prompt": "年齢を入力してください：", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "メールアドレスを入力してください："}
    ])
    
    if data:
        await event.reply(f"登録成功！\n名前：{data['name']}\n年齢：{data['age']}\nメール：{data['email']}")
    else:
        await event.reply("タイムアウトまたは入力が無効です")
```

### 任意のイベントを待機 (wait_for)

条件を満たす任意のイベントを待ちます。同じユーザーに限定されません：

```python
@command("wait_member", help="新規メンバーを待つ")
async def wait_member_handler(event):
    await event.reply("グループメンバーの加入を待機中...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"新規メンバーを歓迎します：{evt.get_user_id()}")
    else:
        await event.reply("タイムアウトしました")
```

### 多回の対話 (conversation)

対話可能な多回の対話コンテキストを作成します：

```python
@command("survey", help="アンケート調査")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("アンケート調査にご参加ありがとうございます！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("対話がタイムアウトしました。さようなら！")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("さようなら！")
            break
        
        await conv.say(f"あなたは言いました：{text}。続けて入力するか、'退出'と入力して終了してください")
```

### 組み込みの確認語

ErisPulse には中国語と英語の確認語のセットが組み込まれています：

- **確認語** (`CONFIRM_YES_WORDS`): はい、yes、y、確認、確定、よし、良い、ok、true、対、うん、行、同意、問題ありません...
- **否定語** (`CONFIRM_NO_WORDS`): いいえ、no、n、キャンセル、いいえ、しない、ダメ、cancel、false、間違い、拒否、できません...

## イベントデータへのアクセス

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
    
    # Bot 情報
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

組み込みメソッドに加え、各プラットフォームアダプターはプラットフォーム固有のメソッドを登録します。それらを利用して、プラットフォーム固有のデータにアクセスできます。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出し
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram 固有のメソッド
    elif platform == "email":
        subject = event.get_subject()           # メール固有のメソッド
```

特定のプラットフォームにどのメソッドが登録されているかわからない場合は、プラットフォームに登録されているメソッドを確認できます：

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームに登録されている固有のメソッドについては、対応する[プラットフォームガイド](../platform-guide/)を参照してください。

## イベント処理のベストプラクティス

### 1. 例外処理

```python
@command("process")
async def process_handler(event):
    try:
        # ビジネスロジック
        result = await do_some_work()
        await event.reply(f"結果: {result}")
    except ValueError as e:
        # 予期されるビジネスエラー
        await event.reply(f"パラメータエラー: {e}")
    except Exception as e:
        # 予期しないエラー
        sdk.logger.error(f"処理失敗: {e}")
        await event.reply("処理に失敗しました。後でもう一度お試しください")
```

### 2. ロギング

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"メッセージ処理: {user_id} - {text}")
    
    # モジュール独自のロガーを使用
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"詳細デバッグ情報")
```

### 3. 条件処理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """条件処理 - ハンドラー内部で判断"""
    # 特定のユーザーのメッセージのみ処理
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 特定のキーワードを含むメッセージのみ処理
    if "キーワード" not in event.get_text():
        return
    
    await event.reply("条件を満たしました。メッセージを処理します")
```

## 次のステップ

- [よくあるタスクの例](common-tasks.md) - よく使われる機能の実装を学ぶ
- [Event ラッパークラスの詳細](../developer-guide/modules/event-wrapper.md) - Event オブジェクトを詳しく知る
- [ユーザーガイド](../user-guide/) - 設定とモジュール管理を理解する



=====
适配器开发
=====


### 适配器开发入门

# アダプター開発入門

このガイドは、ErisPulse アダプターの開発を開始し、新しいメッセージ プラットフォームに接続するのに役立ちます。

## アダプターの概要

### アダプターとは何か

アダプターは ErisPulse と各メッセージ プラットフォーム間のブリッジであり、以下の責務を負います：

1. **正方向変換**：プラットフォーム イベントを受け取り、OneBot12 標準形式に変換（Converter）
2. **逆方向変換**：OneBot12 メッセージ セグメントをプラットフォーム API コールに変換（`Raw_ob12`）
3. プラットフォームとの接続管理（WebSocket/WebHook）
4. 統一された SendDSL メッセージ送信インターフェースを提供

### アダプターのアーキテクチャ

```
正方向変換（受信）                        逆方向変換（送信）
─────────────                        ─────────────
プラットフォーム イベント                    モジュールが構築するメッセージ
    ↓                                    ↓
Converter.convert()               Send.Raw_ob12()
    ↓                                    ↓
OneBot12 標準イベント                    プラットフォームネイティブ API コール
    ↓                                    ↓
イベントシステム                         標準応答フォーマット
    ↓
モジュールの処理
```

## ディレクトリ構造

標準的なアダプター パッケージ構造：

```
MyAdapter/
├── pyproject.toml          # プロジェクト設定
├── README.md               # プロジェクト説明
├── LICENSE                 # ライセンス
└── MyAdapter/
    ├── __init__.py          # パッケージエントリ
    ├── Core.py               # アダプターのメインクラス
    └── Converter.py          # イベント変換器
```

## クイックスタート

### 1. プロジェクトの作成

```bash
mkdir MyAdapter && cd MyAdapter
```

### 2. pyproject.toml の作成

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "MyAdapterプラットフォームアダプター"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

dependencies = [
    "ErisPulse>=2.4.0"  # ErisPulse には aiohttp が組み込まれているため、通常は個別の依存関係は不要です
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. アダプターのメインクラスの作成

```python
# MyAdapter/Core.py
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core import router, logger, config as config_manager, adapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()  # ← 必須！Send / Request ファクトリインスタンスを作成
        self.sdk = sdk
        self.logger = logger.get_child("MyAdapter")
        self.config_manager = config_manager
        self.adapter = adapter
        
        self.config = self._get_config()
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
        
        self.logger.info("MyAdapter 初期化完了")
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
    
    def _get_config(self):
        config = self.config_manager.getConfig("MyAdapter", {})
        if config is None:
            default_config = {
                "api_endpoint": "https://api.example.com",
                "timeout": 30
            }
            self.config_manager.setConfig("MyAdapter", default_config)
            return default_config
        return config
```

> ⚠️ **`super().__init__()` について**：`BaseAdapter.__init__()` は `Send` と `Request` のファクトリインスタンスの作成を担当します。これを忘れると、すべてのメッセージ送信とリクエスト操作で `AttributeError` が発生します。詳細は [__init__ の注意点](#init-注意事项) を参照してください。

### 4. 必須メソッドの実装

```python
class MyAdapter(BaseAdapter):
    # ... __init__ のコード ...
    
    async def start(self):
        """アダプターの起動（実装必須）"""
        # WebSocket または WebHook ルートの登録
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("アダプターが起動しました")
    
    async def shutdown(self):
        """アダプターのシャットダウン（実装必須）"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # 接続とリソースのクリーンアップ
        self.logger.info("アダプターがシャットダウンしました")
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API の呼び出し（実装必須）"""
        raise NotImplementedError("call_api の実装が必要です")
```

#### メタイベントの主動送信

アダプターはフレームワークが Bot のオンライン状態を追跡できるように、メタイベントを主動的に送信する必要があります：

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot オンライン
        await self.adapter.emit({
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {"platform": "myplatform", "user_id": bot_id}
        })

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Bot オフライン
            await self.adapter.emit({
                "type": "meta",
                "detail_type": "disconnect",
                "platform": "myplatform",
                "self": {"platform": "myplatform", "user_id": bot_id}
            })
```

> Bot の状態管理とメタイベントの詳細については、[アダプターのベストプラクティス - Bot 状態管理](best-practices.md#bot-状态管理与-meta-事件) を参照してください。

### 5. Send クラスの実装

`At`/`AtAll`/`Reply` デコレータ（修飾子）はフレームワークの SendDSL ベースクラスに実装されているため、アダプターは `Raw_ob12` と具体的な送信メソッドを実装するだけで済みます。

フレームワークは2つの重要な補助メソッドを提供します：
- `self._apply_modifiers(message)` — メッセージセグメントに `At`/`AtAll`/`Reply` デコレータを自動的にマージ
- `self.send_context` — 送信コンテキスト辞書（`target_type`、`target_id`、`account_id`）を取得

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... 他のコード ...
    
    class Send(BaseAdapter.Send):
        
        def Raw_ob12(self, message, **kwargs):
            """
            OneBot12 形式メッセージの送信（実装必須）

            _apply_modifiers を使用してデコレータの状態を自動的にマージし、
            send_context を使用して送信コンテキストを取得します。
            """
            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs
                )
            return asyncio.create_task(_do_send())
        
        def Text(self, text: str):
            """テキストメッセージを送信"""
            return self.Raw_ob12([
                {"type": "text", "data": {"text": text}}
            ])
        
        def Image(self, file):
            """画像メッセージを送信"""
            return self.Raw_ob12([
                {"type": "image", "data": {"file": file}}
            ])
```

**メディアクラス送信メソッド（Image/Video/File）の実装のポイント：**

- `file` パラメータは `bytes` バイナリデータと `str` URL の両方をサポートする必要があります
- URL が渡された場合は、まずファイルをダウンロードしてからプラットフォームにアップロードする必要があります
- プラットフォームは通常、送信インターフェースを呼び出す前にアップロードインターフェースを呼び出してファイル識別子を取得する必要があります

**`__getattr__` マジックメソッド：**

- メソッド名の大文字小文字を区別しないように実装（`Text`、`text`、`TEXT` すべて呼び出し可能）
- 未定義のメソッドはエラーを返すのではなく、ヒントメッセージを返すべきです

**`Raw_ob12` メソッド：**

- OneBot12 標準メッセージ形式をプラットフォーム形式に変換して送信
- `self._apply_modifiers(message)` を使用して `At`/`AtAll`/`Reply` デコレータを自動的に処理
- `**self.send_context` を使用して送信先情報とアカウント情報を渡す

### 6. 変換器の実装

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォームネイティブイベントを OneBot12 標準形式に変換"""
        if not isinstance(raw_event, dict):
            return None
        
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_event_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
    
    def _convert_event_type(self, event_type):
        """イベントタイプの変換"""
        type_map = {
            "message": "message",
            "notice": "notice"
        }
        return type_map.get(event_type, "unknown")
    
    def _convert_detail_type(self, raw_event):
        """詳細タイプの変換"""
        return "private"  # 簡略化された例
```

### 7. Request クラスの実装（リクエスト操作）

プラットフォームが Bot が意思決定を行う必要のある要求（フレンドリクエスト、グループ招待など）をサポートしている場合、`Request` 内部クラスを実装できます：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Send と他のコード ...

    class Request(RequestDSL):
        """リクエスト操作の実装（フレンドリクエスト、グループ招待など）"""

        def accept(self, **kwargs):
            """リクエストを承認"""
            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=True,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            return self._create_task(_do())

        def reject(self, **kwargs):
            """リクエストを拒否"""
            async def _do():
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    approve=False,
                    **kwargs,
                )
                return {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            return self._create_task(_do())
```

モジュール開発者が使用する方法：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Event から便利なメソッド経由
    await event.approve()
    # またはアダプターを直接操作
    await adapter.myplatform.Request("req_id").accept()
```

> プラットフォームがリクエスト操作をサポートしていない場合は、`Request` 内部クラスを実装する必要はありません。ベースクラスはデフォルトで `retcode=10002`（サポートされていない操作）を返します。詳細は [リクエスト操作仕様](../../standards/request-action-spec.md) を参照してください。

### 8. パッケージエントリの作成

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## `__init__` の注意点

アダプター開発には `__init__` のオーバーライドに関与する3つのレイヤーがあります。各レイヤーの正しい方法は以下の通りです。

### 1. BaseAdapter レイヤー（`super().__init__()` の呼び出しが必須）

`BaseAdapter.__init__()` は**`Send` と `Request` のファクトリインスタンスの作成**を担当します。アダプターに独自の `__init__` がある場合、必ず親クラスの初期化を呼び出す必要があります：

```python
class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        super().__init__()  # ← 必須！さもないと Send / Request は初期化されません
        self.sdk = sdk
        # ... 他の初期化
```

**呼び出しを忘れた場合の結果**：`adapter.Send.To(...)` と `adapter.Request(...)` の両方が `AttributeError` を返します。

### 2. Send 内部クラス（ほとんどの場合、オーバーライド不要）

`SendDSL.__init__` はチェイン呼び出しの状態の受け渡し（ターゲットタイプ、ターゲットID、アカウントなど）を担当します。**ほとんどの場合、`__init__` をオーバーライドする必要はなく、メソッドだけをオーバーライドする**（`Raw_ob12`、`Text` など）必要があります。

実際に必要な場合（プラットフォーム固有の状態の初期化など）、**すべてのパラメータを透過する**必要があります：

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # パラメータ：adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← パラメータを透過する必要があります
            self._my_state = None  # プラットフォーム固有の初期化
```

**なぜパラメータを透過する必要があるのか**：チェイン呼び出しの各ステップは `self.__class__(...)` を使用して新しいインスタンスを作成します：

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

もし `__init__` のシグネチャが一致しないか `super()` が呼ばれていなければ、チェイン呼び出しは中断します。

### 3. Request 内部クラス（ほとんどの場合、オーバーライド不要）

Send と同様です。パラメータは `adapter`, `request_id`, `account_id` です：

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # パラメータ：adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← パラメータを透過する必要があります
            self._my_state = None  # プラットフォーム固有の初期化
```

### まとめ

| レイヤー | いつオーバーライドするか | 必須なこと |
|------|------------|-----------|
| **BaseAdapter** | アダプターの状態を初期化する必要がある場合 | `super().__init__()` （引数なし） |
| **Send 内部クラス** | 送信関連の状態を初期化する必要がある場合 | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request 内部クラス** | リクエスト関連の状態を初期化する必要がある場合 | `super().__init__(adapter, request_id, account_id)` |
| 3つのレイヤー | ほとんどの場合 | **メソッドだけをオーバーライドし、`__init__` には触れない** |

## 次のステップ

- [アダプターの核心概念](core-concepts.md) - アダプターのアーキテクチャを理解する
- [SendDSL の詳細](send-dsl.md) - メッセージ送信を学ぶ
- [変換器の実装](converter.md) - イベント変換を理解する
- [アダプターのベストプラクティス](best-practices.md) - 高品質なアダプターの開発



### 适配器核心概念

# アダプターのコア概念

ErisPulseアダプターのコア概念を理解することは、アダプター開発の基礎となります。

## アダプターアーキテクチャ

### コンポーネントの関係

```
順方向変換（受信方向）                           逆方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォーム  │                        │ モジュールによる   │
│ ネイティブイベント│                        │ メッセージ構築     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ アダプター        │   │                  │
│  Converter       │   │ (MyAdapter)      │   │ Send.Raw_ob12()  │
│  (イベント       │──→│ ┌──────────────┐ │   │ (逆方向変換      │
│   コンバーター)  │   │ │              │ │   │  エントリ)       │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォーム  │
                       │ OneBot12         │    │ API 呼び出し     │
                       │ 標準イベント     │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準レスポンス   │
                       │ イベントシステム │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ モジュール        │
                       │ (イベント処理)   │
                       └──────────────────┘
```

**コアの対称性**：
- **順方向変換**（Converter）：プラットフォームネイティブイベント → OneBot12 標準イベント、元のデータは `{platform}_raw` に保持されます
- **逆方向変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API 呼び出し、標準のレスポンス形式を返します

## AdapterManager アダプター管理マネージャー

`AdapterManager` は、ErisPulseアダプターシステムのコアコンポーネントであり、すべてのプラットフォームアダプターの登録、起動、終了、およびイベントのディスパッチを管理します。

### コア機能

- **アダプター登録**：複数のプラットフォームアダプターを登録および管理します
- **ライフサイクル管理**：アダプターの起動と終了を制御します
- **イベントディスパッチ**：OneBot12 標準イベントとプラットフォームネイティブイベントをディスパッチします
- **設定管理**：アダプターの有効/無効状態を管理します
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアをサポートします

### 基本的な使用方法

```python
from ErisPulse import sdk

# アダプターの登録（通常はLoaderにより自動的に完了します）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプターを起動
await sdk.adapter.startup()

# 指定したアダプターを起動
await sdk.adapter.startup(["myplatform"])
# すべてのアダプターを起動
await sdk.adapter.startup()

# アダプターインスタンスの取得
my_adapter = sdk.adapter.get("myplatform")
# またはプロパティ経由でアクセス
my_adapter = sdk.adapter.myplatform

# すべてのアダプターを終了
await sdk.adapter.shutdown()
```

### 起動と終了

#### アダプターの起動

```python
# 登録済みのすべてのアダプターを起動
await sdk.adapter.startup()

# 指定したプラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
```

**起動フロー：**

1. `adapter.start` ライフサイクルイベントを送信します
2. `adapter.status.change` イベントを送信します（starting）
3. 各アダプターを並行して起動します
4. 起動失敗時、自動リトライ（指数バックオフ戦略）
5. 起動成功後、`adapter.status.change` イベントを送信します（started）

**リトライメカニズム：**

- 最初の4回のリトライ：60秒、10分、30分、60分
- 5回目以降：3時間の固定間隔

#### アダプターの終了

```python
# すべてのアダプターを終了
await sdk.adapter.shutdown()
```

**終了フロー：**

1. `adapter.stop` ライフサイクルイベントを送信します
2. すべてのアダプターの `shutdown()` メソッドを呼び出します
3. ルーティングサーバーを閉じます
4. イベントプロセッサをクリアします
5. `adapter.stopped` ライフサイクルイベントを送信します

### 設定管理

#### プラットフォーム状態の確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効か確認
enabled = sdk.adapter.is_enabled("myplatform")

# in 演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームは存在し、有効です")
```

#### プラットフォームの一覧

```python
# 登録済みのすべてのプラットフォームを一覧表示
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態を一覧表示
status_dict = sdk.adapter.list_items()
# 返り値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベントリスニング

#### OneBot12 標準イベント

```python
from ErisPulse import sdk

# すべてのプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"OneBot12メッセージを受信: {data}")

# 特定のプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatform メッセージを受信: {data}")

#



### SendDSL 详解

# SendDSL 詳解

SendDSL は、ErisPulse アダプターが提供するメソッドチェーンスタイルのメッセージ送信インターフェースです。

## 基本的な呼び出し方

### 1. タイプとIDを指定する

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. IDのみを指定する

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. 送信アカウントを指定する

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. 組み合わせて使用する

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## メソッドチェーン

```
Using/Account() → To() → [修飾メソッド] → [送信メソッド]
```

## 送信メソッド

すべての送信メソッドは `asyncio.Task` オブジェクトを返す必要があります。

### 基本メソッド

| メソッド名 | 説明 | 戻り値 |
|--------|------|---------|
| `Text(text: str)` | テキストメッセージを送信 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 画像を送信 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 音声を送信 | `asyncio.Task` |
| `Video(file: bytes \| str)` | 動画を送信 | `asyncio.Task` |
| `File(file: bytes \| str)` | ファイルを送信 | `asyncio.Task` |

### プロトコルメソッド

| メソッド名 | 説明 | 戻り値 | 必須 |
|--------|------|---------|---------|
| `Raw_ob12(message)` | OneBot12 形式のメッセージを送信 | `asyncio.Task` | **実装必須** |

> **重要**：`Raw_ob12` はアダプターのコアメソッドであり、**実装が必須**です。これはリバース変換（OneBot12 → プラットフォーム）の統一エントリポイントです。未実装の場合、基底クラスは error ログを記録し、標準エラーレスポンス（`status: "failed"`, `retcode: 10002`）を返します。標準メソッド（`Text`、`Image` など）は内部で `Raw_ob12` に委譲する必要があります。

## 修飾メソッド

修飾メソッドはメソッドチェーンをサポートするために `self` を返します。

### At メソッド

```python
# 単一ユーザーをメンション
await adapter.Send.To("group", "123").At("456").Text("你好")

# 複数ユーザーをメンション
await adapter.Send.To("group", "123").At("456").At("789").Text("你们好")
```

### AtAll メソッド

```python
# 全員をメンション
await adapter.Send.To("group", "123").AtAll().Text("大家好")
```

### Reply メソッド

```python
# メッセージに返信
await adapter.Send.To("group", "123").Reply("msg_id").Text("回复内容")
```

### 組み合わせ修飾

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("回复@的消息")
```

## アカウント管理

### Using メソッド

```python
# アカウント名を使用
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# アカウントIDを使用
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### Account メソッド

`Account` メソッドは `Using` と同等です：

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## 非同期処理

### 結果を待たない

```python
# メッセージはバックグラウンドで送信されます
task = adapter.Send.To("user", "123").Text("Hello")

# 他の操作を続行します
# ...
```

### 結果を待つ

```python
# 直接 await して結果を取得します
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"送信結果: {result}")

# まず Task を保存し、後で待機します
task = adapter.Send.To("user", "123").Text("Hello")
# ... 他の操作 ...
result = await task
```

## 命名規則

### PascalCase 命名

すべての送信メソッドはアッパーキャメルケース（PascalCase）を使用します：

```python
# ✅ 正しい
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ 間違い
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### プラットフォーム固有のメソッド

プラットフォームのプレフィックスを付けたメソッドの追加は推奨されません：

```python
# ✅ 推奨
def Sticker(self, sticker_id: str):
    pass

# ❌ 非推奨
def TelegramSticker(self, sticker_id: str):
    pass
```

代わりに `Raw` メソッドを使用します：

```python
# ✅ 推奨
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ 非推奨
def TelegramSticker(self, ...):
    pass
```

## 戻り値

### Task オブジェクト

すべての送信メソッドは `asyncio.Task` を返します：

```python
import asyncio

def Text(self, text: str):
    return asyncio.create_task(
        self._adapter.call_api(
            endpoint="/send",
            content=text,
            recvId=self._target_id,
            recvType=self._target_type
        )
    )
```

### 標準化されたレスポンス

`call_api` は標準化されたレスポンスを返す必要があります：

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok" or "failed",
        "retcode": 0 or error_code,
        "data": {...},
        "message_id": "msg_id" or "",
        "message": "",
        "{platform}_raw": raw_response
    }
```

## 完全な例

### 基本的な使用方法

```python
from ErisPulse.Core import adapter

my_adapter = adapter.get("myplatform")

# テキストを送信
await my_adapter.Send.To("user", "123").Text("Hello World!")

# 画像を送信
await my_adapter.Send.To("group", "456").Image("https://example.com/image.jpg")

# ファイルを送信
with open("document.pdf", "rb") as f:
    await my_adapter.Send.To("user", "123").File(f.read())
```

### メソッドチェーン

```python
# ユーザーをメンション + 返信
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("回复@的消息")

# 全員をメンション + 複数の修飾
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("公告消息")
```

### 生メッセージとメッセージ構築

`Raw_ob12` はリバース変換のコアエントリポイント（OB12 メッセージセグメントの受信 → プラットフォーム API 呼び出し）であり、`MessageBuilder` はそれと組み合わせて使用されるメソッドチェーン式のメッセージセグメント構築ツールです。

> 完全な `Raw_ob12` の実装仕様、`MessageBuilder` の使用法、およびコード例については以下を参照してください：
> - [送信メソッド仕様 §6 リバース変換仕様](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [送信メソッド仕様 §11 メッセージビルダー](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)

## 関連ドキュメント

- [アダプター開発入門](getting-started.md) - アダプターの作成
- [アダプターのコア概念](core-concepts.md) - アダプターのアーキテクチャを理解する
- [アダプターのベストプラクティス](best-practices.md) - 高品質なアダプターの開発
- [送信メソッド仕様](../../standards/send-method-spec.md) - 送信メソッドの完全な仕様



### 适配器开发最佳实践

# アダプター開発のベストプラクティス

本ドキュメントでは、ErisPulse アダプター開発のベストプラクティスを提供します。

## Botの状態管理とMetaイベント

アダプターは、`adapter.emit()` を通じて積極的に meta イベントを送信し、フレームワークに Bot の接続状態、オンライン/オフライン、ハートビート情報を自動追跡させる必要があります。

### 1. Metaイベントを送信するタイミング

| イベント | `detail_type` | 発生タイミング | フレームワークの動作 |
|------|--------------|---------|---------|
| 接続 | `"connect"` | Bot がプラットフォームとの接続を確立した時 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントをトリガーする |
| 切断 | `"disconnect"` | Bot がプラットフォームから切断された時 | Bot をオフラインとしてマークし、`adapter.bot.offline` ライフサイクルイベントをトリガーする |
| ハートビート | `"heartbeat"` | 定期的に送信（30〜60秒を推奨） | Bot のアクティブ時間とメタ情報を更新する |

### 2. Metaイベントの送信

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Botオンライン：connect イベントを送信
        await self.adapter.emit({
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": bot_id,
                "user_name": "MyBot",
                "nickname": "私のBot",
                "avatar": "https://example.com/avatar.png",
            }
        })

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Botオフライン：disconnect イベントを送信
            await self.adapter.emit({
                "type": "meta",
                "detail_type": "disconnect",
                "platform": "myplatform",
                "self": {
                    "platform": "myplatform",
                    "user_id": bot_id,
                }
            })
```

### 3. ハートビートイベント

アダプターは、接続が生きている間、定期的にハートビートイベントを送信し、Bot のアクティブ時間を更新する必要があります：

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            await self.adapter.emit({
                "type": "meta",
                "detail_type": "heartbeat",
                "platform": "myplatform",
                "self": {
                    "platform": "myplatform",
                    "user_id": bot_id,
                }
            })
            await asyncio.sleep(30)
```

### 4. `self` フィールドの自動検出

フレームワークの `adapter.emit()` は、すべてのイベント（meta イベントだけでなく）の `self` フィールドを自動的に処理します：

- **通常のイベント**（message/notice/request）の `self` フィールドは、Bot を自動的に検出して登録します
- **`self` フィールドの拡張情報**：`user_name`、`nickname`、`avatar`、`account_id` オプションフィールドをサポートします

```python
# コンバーターに self フィールドを含めるだけで Bot が自動登録されます
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "私のBot",
    },
    # ... その他のフィールド
}
await self.adapter.emit(onebot_event)
# Bot "bot123" が自動登録され、アクティブ時間が更新されました
```

### 5. Botの状態照会

フレームワークは以下の照会メソッドを提供します：

```python
from ErisPulse import sdk

# Bot の詳細情報を取得
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# すべての Bot をリストアップ（プラットフォーム別）
all_bots = sdk.adapter.list_bots()

# 指定したプラットフォームの Bot をリストアップ
platform_bots = sdk.adapter.list_bots("myplatform")

# Bot がオンラインかどうかを確認
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 完全なステータスサマリーを取得（WebUIでの表示に適しています）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

## 接続管理

### 1. 再接続の実装

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                self.logger.info("接続成功")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # 指数バックオフ戦略
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"接続失敗、{wait_time}秒後に再試行します ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("接続失敗、最大再試行回数に達しました")
                    raise
```

### 2. 接続状態管理

```python
class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.connection = None
        self._connected = False
    
    async def _ws_handler(self, websocket: WebSocket):
        self.connection = websocket
        self._connected = True
        self.logger.info("接続が確立されました")
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._process_event(data)
        except WebSocketDisconnect:
            self.logger.info("接続が切断されました")
        finally:
            self.connection = None
            self._connected = False
```

### 3. ハートビートキープアライブと Meta ハートビート

アダプターのハートビートは、プラットフォームへのキープアライブ送信と、フレームワークへの meta heartbeat イベント送信の2つのタスクを同時に実行する必要があります。

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. プラットフォームにハートビートを送信してキープアライブ
                await self.connection.send_json({"type": "ping"})

                # 2. フレームワークに meta heartbeat イベントを送信（Bot のアクティブ時間を更新）
                await self.adapter.emit({
                    "type": "meta",
                    "detail_type": "heartbeat",
                    "platform": "myplatform",
                    "self": {
                        "platform": "myplatform",
                        "user_id": self._bot_id,
                    }
                })

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"ハートビート失敗: {e}")
                break
```

## イベント変換

### 1. OneBot12 標準の厳格な遵守

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """イベントを変換"""
        onebot_event = {
            "id": str(raw_event.get("event_id", uuid.uuid4())),
            "time": int(time.time()),
            "type": self._convert_type(raw_event.get("type")),
            "detail_type": self._convert_detail_type(raw_event),
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,  # 元のデータを保持（必須）
            "myplatform_raw_type": raw_event.get("type", "")  # 元のタイプ（必須）
        }
        return onebot_event
```

### 2. タイムスタンプの標準化

```python
def _convert_timestamp(self, timestamp):
    """10桁の秒単位タイムスタンプに変換"""
    if not timestamp:
        return int(time.time())
    
    # ミリ秒単位のタイムスタンプの場合
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # 秒単位のタイムスタンプの場合
    return int(timestamp)
```

### 3. イベント ID の生成

```python
import uuid

def _generate_event_id(self, raw_event):
    """イベント ID を生成"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # プラットフォームが ID を提供していない場合、UUID を生成
    return str(uuid.uuid4())
```

## SendDSL の実装

`At`/`AtAll`/`Reply` 修飾子はフレームワークの SendDSL 基底クラスに組み込まれているため、アダプターは `Raw_ob12` と具体的な送信メソッドを実装するだけで済みます。`self._apply_modifiers(message)` と `self.send_context` を使用して開発を簡素化します。

### 1. Task オブジェクトを返さなければならない

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """推奨される実装：フレームワークのヘルパーメソッドを使用"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    def Text(self, text: str):
        return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 2. チェーン修飾メソッドは self を返す

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # self を返す
```

### 3. プラットフォーム固有のメソッドのサポート

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """スタンプを送信"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                message=[{"type": "sticker", "data": {"id": sticker_id}}],
                **self.send_context
            )
        )
    
    def Card(self, card_data: dict):
        """カードメッセージを送信"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": card_data}],
                **self.send_context
            )
        )
```

## API レスポンス

### 1. レスポンス形式の標準化

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return {
            "status": "ok" if raw_response.get("success") else "failed",
            "retcode": 0 if raw_response.get("success") else raw_response.get("code", 10001),
            "data": raw_response.get("data"),
            "message_id": raw_response.get("data", {}).get("message_id", ""),
            "message": "",
            "myplatform_raw": raw_response
        }
    except Exception as e:
        return {
            "status": "failed",
            "retcode": 34000,
            "data": None,
            "message_id": "",
            "message": str(e),
            "myplatform_raw": None
        }
```

### 2. エラーコード規約

OneBot12 標準のエラーコードに従います：

```python
# 1xxxx - アクションリクエストエラー
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - アクションハンドラエラー
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - アクション実行エラー
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## マルチアカウントサポート

### 1. アカウント設定の検証

```python
def _get_config(self):
    """設定を検証"""
    config = self.config_manager.getConfig("MyAdapter", {})
    accounts = config.get("accounts", {})
    
    if not accounts:
        # デフォルトアカウントを作成
        default_account = {
            "token": "",
            "enabled": False
        }
        config["accounts"] = {"default": default_account}
        self.config_manager.setConfig("MyAdapter", config)
    
    return config
```

### 2. アカウント選択メカニズム

```python
async def _get_account_for_message(self, event):
    """イベントに基づいて送信アカウントを選択"""
    bot_id = event.get("self", {}).get("user_id")
    
    # 一致するアカウントを検索
    for account_name, account_config in self.accounts.items():
        if account_config.get("bot_id") == bot_id:
            return account_name
    
    # 見つからない場合、最初に有効なアカウントを使用
    for account_name, account_config in self.accounts.items():
        if account_config.get("enabled", True):
            return account_name
    
    return None
```

## エラーハンドリング

### 1. 分類別の例外処理

```python
async def call_api(self, endpoint: str, **params):
    try:
        # API リクエストを送信するために SDK 組み込みのクライアントを使用することを推奨します
        from ErisPulse.Core import client
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self._standardize_response(response)
    except aiohttp.ClientError as e:
        # ネットワークエラー（client 使用時、組み込みの再試行メカニズムが先に処理します）
        self.logger.error(f"ネットワークエラー: {e}")
        return self._error_response("ネットワークリクエスト失敗", 33000)
    except asyncio.TimeoutError:
        # タイムアウトエラー
        self.logger.error(f"リクエストタイムアウト: {endpoint}")
        return self._error_response("リクエストタイムアウト", 32000)
    except json.JSONDecodeError:
        # JSON 解析エラー
        self.logger.error("JSON 解析失敗")
        return self._error_response("レスポンス形式エラー", 10006)
    except Exception as e:
        # 不明なエラー
        self.logger.error(f"不明なエラー: {e}", exc_info=True)
        return self._error_response(str(e), 34000)
```

### 2. ログ記録

```python
class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.logger = logger.get_child("MyAdapter")
    
    async def start(self):
        self.logger.info("アダプターを起動中...")
        # ...
        self.logger.info("アダプターの起動が完了しました")
    
    async def shutdown(self):
        self.logger.info("アダ



### 事件转换器

# イベントコンバーター実装ガイド

イベントコンバーター (Converter) はアダプターのコアコンポーネントの一つであり、プラットフォームのネイティブイベントを ErisPulse 統一の OneBot12 標準イベントフォーマットに変換する役割を担います。

## Converter の役割

```
プラットフォームネイティブイベント ──→ Converter.convert() ──→ OneBot12 標準イベント
```

Converter は**順方向変換**（受信方向）のみを担当します。つまり、プラットフォームのネイティブイベントデータを OneBot12 標準フォーマットに変換します。逆方向変換（送信方向）は `Send.Raw_ob12()` メソッドによって処理されます。

### コア原則

1. **ロスレス変換**：元のデータは `{platform}_raw` フィールドに完全に保持する必要があります
2. **標準互換性**：変換されたイベントは OneBot12 標準フォーマットに準拠している必要があります
3. **プラットフォーム拡張**：プラットフォーム固有のデータは `{platform}_` プレフィックスフィールドを使用して保存します

## convert() メソッド

### メソッドシグネチャ

```python
def convert(self, raw_event: dict) -> dict:
    """
    プラットフォームのネイティブイベントを OneBot12 標準フォーマットに変換します

    :param raw_event: プラットフォームのネイティブイベントデータ
    :return: OneBot12 標準フォーマットのイベント辞書
    """
    pass
```

### 戻り値の構造

変換されたイベント辞書には、以下の標準フィールドが含まれている必要があります：

```python
{
    "id": "イベントの一意のID",
    "time": 1234567890,           # Unixタイムスタンプ（秒）
    "type": "message",             # イベントタイプ
    "detail_type": "private",      # 詳細タイプ
    "platform": "myplatform",      # プラットフォーム名
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # メッセージイベントフィールド
    "user_id": "sender_id",
    "message": [...],              # OneBot12 メッセージセグメントのリスト
    "alt_message": "プレーンテキストの内容",

    # 元のデータを保持する必要があります
    "myplatform_raw": { ... },     # プラットフォームのネイティブイベントの完全なデータ
    "myplatform_raw_type": "ネイティブイベントタイプ名",
}
```

## 必須フィールドのマッピング

### 共通フィールド（すべてのイベントタイプ）

| OB12 フィールド | 型 | 説明 |
|-----------------|------|------|
| `id` | str | イベントの一意の識別子 |
| `time` | int | Unixタイムスタンプ（秒） |
| `type` | str | イベントタイプ：`message` / `notice` / `request` / `meta` |
| `detail_type` | str | 詳細タイプ：`private` / `group` / `friend` など |
| `platform` | str | プラットフォーム名、アダプターの登録名と一致 |
| `self` | dict | ボット情報：`{"platform": "...", "user_id": "..."}` |

### メッセージイベントの追加フィールド

| OB12 フィールド | 型 | 説明 |
|-----------------|------|------|
| `user_id` | str | 送信者 ID |
| `message` | list[dict] | OneBot12 メッセージセグメントのリスト |
| `alt_message` | str | プレーンテキストの代替コンテンツ |

### 通知イベントの追加フィールド

| OB12 フィールド | 型 | 説明 |
|-----------------|------|------|
| `user_id` | str | 関連ユーザー ID |
| `operator_id` | str | 操作者 ID（グループメンバーの変更など） |

## メッセージセグメントの変換

OneBot12 標準は以下のメッセージセグメントタイプを定義しています：

```python
# テキスト
{"type": "text", "data": {"text": "Hello"}}

# 画像
{"type": "image", "data": {"file": "https://example.com/img.jpg"}}

# 音声
{"type": "audio", "data": {"file": "https://example.com/audio.mp3"}}

# 動画
{"type": "video", "data": {"file": "https://example.com/video.mp4"}}

# ファイル
{"type": "file", "data": {"file": "https://example.com/doc.pdf"}}

# メンション（@）
{"type": "mention", "data": {"user_id": "123"}}

# 全体メンション（@all）
{"type": "mention_all", "data": {}}

# 返信
{"type": "reply", "data": {"message_id": "msg_123"}}
```

プラットフォームがサポートしていないメッセージセグメントタイプがある場合、そのセグメントを省略するか、最も近い標準タイプに変換することができます。

## プラットフォーム拡張フィールド

プラットフォーム固有のデータは `{platform}_` プレフィックスを使用して保存し、標準フィールドとの競合を避ける必要があります：

```python
{
    # 標準フィールド
    "type": "message",
    "detail_type": "group",
    # ...

    # プラットフォーム拡張フィールド
    "myplatform_raw": { ... },          # 元のイベントデータ（必須）
    "myplatform_raw_type": "chat",      # 元のイベントタイプ（必須）

    # その他のプラットフォーム固有のフィールド
    "myplatform_group_name": "グループ名",
    "myplatform_sender_role": "admin",
}
```

> **重要**：`{platform}_raw` フィールドは必須です。ErisPulse のイベントシステムやモジュールがプラットフォームの元のデータにアクセスするために依存する可能性があります。

## 完全な例

以下は完全な Converter の実装例です：

```python
class MyConverter:
    def __init__(self, platform: str):
        self.platform = platform

    def convert(self, raw_event: dict) -> dict:
        event_type = raw_event.get("type", "")

        base_event = {
            "id": raw_event.get("id", ""),
            "time": raw_event.get("timestamp", 0),
            "platform": self.platform,
            "self": {
                "platform": self.platform,
                "user_id": raw_event.get("self_id", ""),
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": event_type,
        }

        if event_type == "chat":
            return self._convert_message(raw_event, base_event)
        elif event_type == "notification":
            return self._convert_notice(raw_event, base_event)
        elif event_type == "request":
            return self._convert_request(raw_event, base_event)

        return base_event

    def _convert_message(self, raw: dict, base: dict) -> dict:
        base["type"] = "message"
        base["detail_type"] = "group" if raw.get("group_id") else "private"
        base["user_id"] = raw.get("sender_id", "")
        base["message"] = self._convert_message_segments(raw.get("content", ""))
        base["alt_message"] = raw.get("content", "")

        if raw.get("group_id"):
            base["group_id"] = raw["group_id"]

        return base

    def _convert_message_segments(self, content: str) -> list:
        segments = []
        if content:
            segments.append({"type": "text", "data": {"text": content}})
        return segments

    def _convert_notice(self, raw: dict, base: dict) -> dict:
        base["type"] = "notice"
        notification_type = raw.get("notification_type", "")

        if notification_type == "member_join":
            base["detail_type"] = "group_member_increase"
            base["user_id"] = raw.get("user_id", "")
            base["group_id"] = raw.get("group_id", "")
            base["operator_id"] = raw.get("operator_id", "")
        elif notification_type == "friend_add":
            base["detail_type"] = "friend_increase"
            base["user_id"] = raw.get("user_id", "")

        return base

    def _convert_request(self, raw: dict, base: dict) -> dict:
        base["type"] = "request"
        request_type = raw.get("request_type", "")

        if request_type == "friend":
            base["detail_type"] = "friend"
            base["user_id"] = raw.get("user_id", "")
            base["comment"] = raw.get("message", "")
        elif request_type == "group_invite":
            base["detail_type"] = "group"
            base["group_id"] = raw.get("group_id", "")
            base["user_id"] = raw.get("inviter_id", "")

        return base
```

## ベストプラクティス

1. **常に元のデータを保持する**：`{platform}_raw` フィールドは省略できません
2. **標準メッセージセグメントを使用する**：プラットフォームのメッセージを OneBot12 標準のメッセージセグメントに変換するように努めてください
3. **detail_type を適切に設定する**：標準タイプ（`private`/`group`/`channel` など）を使用し、独自に定義しないでください
4. **エッジケースの処理**：元のイベントに一部のフィールドが欠落している可能性があるため、`.get()` を使用して適切なデフォルト値を提供してください
5. **パフォーマンスの考慮**：`convert()` は各イベントで呼び出されるため、時間のかかる操作をその中で実行することは避けてください

## 関連ドキュメント

- [アダプターのコアコンセプト](core-concepts.md) - アダプターの全体アーキテクチャ
- [SendDSL 詳解](send-dsl.md) - 逆方向変換（送信方向）
- [イベント変換標準](../../standards/event-conversion.md) - 公式なイベント変換仕様
- [セッションタイピングシステム](../../advanced/session-types.md) - セッションタイプのマッピングルール



=====
发布与工具
=====


### 发布适配器到模块商店

# 公開とモジュールストアガイド

開発したモジュールやアダプターを ErisPulse モジュールストアに公開し、他のユーザーが簡単に見つけてインストールできるようにしましょう。

## モジュールストアの概要

ErisPulse モジュールストアは一元管理されたモジュールレジストリであり、ユーザーは CLI ツールを使用して、コミュニティによって提供されたモジュールやアダプターを閲覧、検索、インストールできます。

### 閲覧と検索

```bash
# リモートで利用可能なすべてのパッケージを一覧表示
epsdk list-remote

# モジュールのみを表示
epsdk list-remote -t modules

# アダプターのみを表示
epsdk list-remote -t adapters

# リモートパッケージリストを強制的に更新
epsdk list-remote -r
```

[ErisPulse 公式サイト](https://www.erisdev.com/#market) にアクセスして、オンラインでモジュールストアを閲覧することもできます。

### サポートされている提出タイプ

| タイプ | 説明 | Entry-point グループ |
|------|------|----------------|
| モジュール (Module) | ボット機能の拡張、ビジネスロジックの実装 | `erispulse.module` |
| アダプター (Adapter) | 新しいメッセージングプラットフォームの接続 | `erispulse.adapter` |

## クイック公開

プロセス全体はわずか3ステップです：プロジェクトの設定 → PyPI への公開 → モジュールストアへの提出。

### 1. pyproject.toml の設定

プロジェクトディレクトリに `pyproject.toml` と `README.md` が含まれていることを確認し、タイプに応じて entry-points を設定します：

#### モジュール

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "モジュール機能の説明"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [ { name = "yourname" } ]
dependencies = [
    "ErisPulse>=2.0.0",
]

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

#### アダプター

```toml
[project]
name = "ErisPulse-MyAdapter"
version = "1.0.0"
description = "アダプター機能の説明"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **注意**: パッケージ名は `ErisPulse-` で始めることをお勧めします。これにより、ユーザーが認識しやすくなります。Entry-point のキー名（例: `"MyModule"`）は、SDK におけるモジュールのアクセス名として使用されます。

### 2. PyPI への公開

```bash
# ビルド + 公開 (PyPI アカウントが必要)
pip install build twine
python -m build
python -m twine upload dist/*
```

公開成功後、インストールを検証します：

```bash
pip install ErisPulse-MyModule
```

### 3. モジュールストアへの提出

[ErisPulse モジュールストア](https://www.erisdev.com/#market) にアクセスし、「モジュールを提出」をクリックして、ログイン後にモジュール情報を入力します。

サポートされているログイン方法: **GitHub**、**Codeberg**、**Yunhu**（云湖）、いずれか1つを選択してください。

記入のポイント:
- モジュール名、説明、リポジトリURL
- 最低 SDK バージョン: 不明な場合は、[ErisPulse の最新リリース](https://pypi.org/project/ErisPulse/) のバージョン番号を記入してください。

提出直後に反映され、ユーザーはモジュールソースからインストールできるようになります。モジュールは「未検証」としてマークされ、メンテナによる審査を通過すると「検証済み」に変更されます。

> **検証ステータスについて**:
> - 「未検証」はまだ公式な審査を通過していないことを意味するだけで、モジュールに問題があるわけではありません。
> - ユーザーが `epsdk install` で未検証のモジュールをインストールする際、リスクの警告が表示され、確認後にのみインストールを続行できます。

### 4. 公開済みモジュールの管理

モジュールストアで「モジュールを提出」をクリックしてログイン後、「マイモジュール」タブに切り替えると、以下の操作が可能です:

- **編集** — モジュールの説明、リポジトリURL、タグなどの情報を変更します。バージョン番号は PyPI から自動的に同期されます。
- **削除** — モジュールをモジュールストアから削除します（元に戻せません）。

> 提出したばかりのモジュールが「マイモジュール」リストに表示されるまで、数分かかる場合があります。

## 公開済みモジュールの更新

1. `pyproject.toml` の `version` を更新します。
2. 再ビルドしてアップロードします: `python -m build && python -m twine upload dist/*`
3. モジュールストアは PyPI 上の最新バージョンを自動的に同期します。

ユーザーは `epsdk upgrade MyModule` を実行するだけでアップグレードできます。

## 開発モードでのテスト

本番公開前に、編集可能モード（editable mode）を使用してローカルでテストできます:

```bash
epsdk install -e /path/to/MyModule
# または
pip install -e /path/to/MyModule
```

## よくある質問

### パッケージ名は必ず `ErisPulse-` で始める必要がありますか？

必須ではありませんが、強くお勧めします。これにより、ユーザーが PyPI で ErisPulse エコシステムのパッケージを識別しやすくなります。

### 1つのパッケージで複数のモジュールを登録できますか？

はい。`entry-points` に複数のキーと値のペアを設定するだけです:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### 審査にはどのくらい時間がかかりますか？

通常、1〜3営業日以内に完了します。モジュールストアの「マイモジュール」で検証ステータスを確認できます。

## Docker イメージによるアプリケーションの配布

アプリケーションが PyPI への公開に適さない場合（例: プライベートな依存関係を含む、事前設定された環境が必要など）、**GitHub Container Registry (GHCR)** を使用して Docker イメージを公開することで、他のユーザーが `docker pull` でワンクリック起動できるようになります。

### 適用シナリオ

- **完全なボットアプリケーション**（モジュール + 設定 + エントリポイントスクリプト）があり、ワンクリックで配布したい場合
- モジュール/アダプターが**プライベートパッケージ**に依存している、または特殊なインストール手順があり、PyPI に適さない場合
- **すぐに使える**デプロイメントソリューションを提供し、ユーザーの利用ハードルを下げたい場合

### 1. Dockerfile の作成

ErisPulse 公式イメージをベースにビルドし、モジュールを追加するだけです:

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="モジュールの説明" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

モジュールに追加のシステム依存関係（SSH クライアントなど）が必要な場合は、`RUN uv pip install` の後に以下を追加します:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` には、ErisPulse、ErisPulse-Dashboard、Python ランタイム、および uv がすでに含まれているため、再インストールする必要はありません。

### 2. GitHub Actions ワークフローの作成

`.github/workflows/docker-publish.yml` に以下を作成します:

```yaml
name: Docker イメージの公開

on:
  workflow_dispatch:
  push:
    branches:
      - main
    tags:
      - "v*"

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository_owner }}/my-bot

jobs:
  docker-publish:
    runs-on: ubuntu-latest

    steps:
      - name: コードのチェックアウト
        uses: actions/checkout@v4

      - name: QEMU のセットアップ (マルチアーキテクチャサポート)
        uses: docker/setup-qemu-action@v3

      - name: Docker Buildx のセットアップ
        uses: docker/setup-buildx-action@v3

      - name: GitHub Container Registry へのログイン
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Docker メタデータの抽出
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - name: Docker イメージのビルドとプッシュ
        uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

> `GITHUB_TOKEN` は GitHub Actions によって自動的に提供されるため、手動でシークレットを作成する必要はありません。

### 3. ビルドのトリガー

コードをプッシュするか、Tag を作成すると自動的にビルドされます:

```bash
# main ブランチへのプッシュでトリガー
git push origin main

# または Tag の作成でトリガー
git tag v1.0.0
git push origin v1.0.0
```

GitHub リポジトリの **Actions** ページから手動でトリガーすることもできます。

### 4. イメージを公開設定にする

GHCR イメージはデフォルトで **private** に設定されているため、他のユーザーがログインせずにプルできるようにするには、GitHub で Public に設定する必要があります:

1. リポジトリに移動 → **Packages** → 対応する Package をクリック
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. ユーザーによる使用

ビルド完了後、ユーザーは `docker run` を1行実行するだけで起動できます:

```bash
docker run -d \
  --name my-bot \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -e TZ=Asia/Shanghai \
  -e ERISPULSE_DASHBOARD_TOKEN=your-token \
  --restart unless-stopped \
  ghcr.io/<your-username>/my-bot:latest
```

または `docker-compose.yml` を使用します:

```yaml
services:
  my-bot:
    image: ghcr.io/<your-username>/my-bot:latest
    container_name: my-bot
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    environment:
      - TZ=Asia/Shanghai
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    restart: unless-stopped
```

### Docker Hub への同時公開

ワークフローを拡張し、ログインステップの前に Docker Hub へのログインを追加し、`images` に Docker Hub のアドレスを追加します:

```yaml
      - name: Docker Hub へのログイン
        uses: docker/login-action@v3
        with:
          registry: docker.io
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Docker メタデータの抽出
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            docker.io/<your-dockerhub-username>/my-bot
            ghcr.io/${{ github.repository_owner }}/my-bot
```

> リポジトリの **Settings → Secrets** に `DOCKERHUB_USERNAME` と `DOCKERHUB_TOKEN` を追加する必要があります。

### Docker イメージ vs PyPI 公開

| 特徴 | Docker イメージ (GHCR) | PyPI 公開 |
|------|---------------------|-----------|
| 配布方法 | `docker pull` でワンクリック実行 | `pip install` + 手動設定 |
| 適用範囲 | 完全なアプリケーション/ソリューション | 単一のモジュール/アダプター |
| プライベート依存関係 | ネイティブでサポート | プライベート PyPI ソースが必要 |
| モジュールストア | 適用外 | モジュールストアに提出可能 |
| マルチアーキテクチャ | amd64/arm64 をサポート | アーキテクチャに依存しない |

これら2つの方法は矛盾しません。PyPI からモジュールストアにモジュールを公開しつつ、GHCR からすぐに使える Docker イメージを提供することができます。



### CLI 命令参考

# CLI コマンドリファレンス

ErisPulse コマンドラインツールは、プロジェクト管理およびパッケージ管理機能を提供します。

## パッケージ管理コマンド

| コマンド | 引数 | 説明 | 例 |
|-------|------|------|------|
| `install` | `[パッケージ名]... [--upgrade/-U] [--pre]` | モジュール/アダプターをインストールします | `epsdk install Yunhu` |
| `uninstall` | `<パッケージ名>...` | モジュール/アダプターをアンインストールします | `epsdk uninstall old-module` |
| `upgrade` | `[パッケージ名]... [--force/-f] [--pre]` | 指定されたモジュール、またはすべてをアップグレードします | `epsdk upgrade --force` |
| `self-update` | `[バージョン] [--pre] [--force/-f]` | SDK自体を更新します | `epsdk self-update` |

## 情報照会コマンド

| コマンド | 引数 | 説明 | 例 |
|-------|------|------|------|
| `list` | `[--type/-t <type>]` | インストール済みのモジュール/アダプターを一覧表示します | `epsdk list -t modules` |
| | `[--outdated/-o]` | アップグレード可能なパッケージのみを表示します | `epsdk list -o` |
| `list-remote` | `[--type/-t <type>]` | リモートで利用可能なパッケージを一覧表示します | `epsdk list-remote` |
| | `[--refresh/-r]` | 強制的にパッケージリストを更新します | `epsdk list-remote -r` |

## 実行制御コマンド

| コマンド | 引数 | 説明 | 例 |
|-------|------|------|------|
| `run` | `<スクリプト> [--reload]` | 指定されたスクリプトを実行します | `epsdk run main.py --reload` |

## プロジェクト管理コマンド

| コマンド | 引数 | 説明 | 例 |
|-------|------|------|------|
| `init` | `[--project-name/-n <name>]` | 対話形式でプロジェクトを初期化します | `epsdk init -n my_bot` |
| | `[--quick/-q]` | クイックモードで対話をスキップします | `epsdk init -q -n bot` |
| | `[--force/-f]` | 既存の設定を強制上書きします | `epsdk init -f` |
| `create` | `[モジュール\|アダプター]` | スキャフォールドプロジェクトを作成します | `epsdk create` |
| | `[--name/-n <name>]` | プロジェクト名 (PascalCase) | `epsdk create module -n MyModule` |
| | `[--description/-d <desc>]` | プロジェクトの説明 | `epsdk create adapter -d "xxアダプター"` |
| | `[--author/-a <name>]` | 著作者名 | `epsdk create -a yourname` |
| | `[--email/-e <mail>]` | 著作者のメールアドレス | `epsdk create -e you@mail.com` |
| | `[--homepage <url>]` | プロジェクトのホームページ URL | |
| | `[--output/-o <dir>]` | 出力ディレクトリ (デフォルトは現在のディレクトリ) | `epsdk create -o ./projects` |
| | `[--force/-f]` | 既存のディレクトリを強制上書きします | `epsdk create -f` |

## パラメータの説明

### 一般的なパラメータ

| パラメータ | 短いパラメータ | 説明 |
|------|---------|------|
| `--help` | `-h` | ヘルプ情報を表示します |
| `--verbose` | `-v` | 詳細な出力を表示します |

### install のパラメータ

| パラメータ | 説明 |
|------|------|
| `[パッケージ名]` | インストールするパッケージ名。複数指定可能 |
| `--upgrade` | `-U` | インストール時に最新バージョンへアップグレードします |
| `--pre` | プレリリース版（プレリリースバージョン）のインストールを許可します |

### list のパラメータ

| パラメータ | 説明 |
|------|------|
| `--type` | `-t` | 指定するタイプ: `modules`, `adapters`, `all` |
| `--outdated` | `-o` | アップグレード可能なパッケージのみを表示します |

### run のパラメータ

| パラメータ | 説明 |
|------|------|
| `--reload` | ホットリロードモードを有効にし、ファイルの変更を監視します |
| `--no-reload` | ホットリロードモードを無効にします |

## 対話式インストール

`epsdk install` にパッケージ名を指定せず実行すると、対話式インストールが開始されます：

```bash
epsdk install
```

  対話インターフェースは以下のものを提供します：
1. アダプタの選択
2. モジュールの選択
3. カスタムインストール

## よく使われる用法

### モジュールのインストール

```bash
# 単一のモジュールをインストール
epsdk install Weather

# 複数のモジュールをインストール
epsdk install Yunhu Weather

# モジュールをアップグレード
epsdk install Weather -U
```

### モジュールの一覧表示

```bash
# 全てのモジュールを一覧表示
epsdk list

# アダプタのみを表示
epsdk list -t adapters

# アップグレード可能なモジュールのみを表示
epsdk list -o
```

### モジュールのアンインストール

```bash
# 単一のモジュールをアンインストール
epsdk uninstall Weather

# 複数のモジュールをアンインストール
epsdk uninstall Yunhu Weather
```

### モジュールのアップグレード

```bash
# 全てのモジュールをアップグレード
epsdk upgrade

# 指定されたモジュールをアップグレード
epsdk upgrade Weather

# 強制アップグレード
epsdk upgrade -f
```

### プロジェクトの実行

```bash
# 通常の実行
epsdk run main.py

# ホットリロードモード
epsdk run main.py --reload
```

### プロジェクトの初期化

```bash
# 対話形式での初期化
epsdk init

# クイック初期化
epsdk init -q -n my_bot
```

### スキャフォールドの作成

```bash
# 対話式の作成（タイプ選択や情報入力をガイドされます）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全なパラメータ
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 既存のディレクトリを強制上書き
epsdk create module -n MyModule -f



======
API 参考
======


### 适配器系统 API

# アダプターシステム API

このドキュメントでは、ErisPulse アダプターシステムの API を詳細に紹介します。

## Adapter 管理器

### アダプタの取得

```python
from ErisPulse import sdk

# 名前でアダプタを取得
adapter = sdk.adapter.get("platform_name")

# または属性アクセスで直接取得
adapter = sdk.adapter.platform_name
```

### アダプタイベントの監視
> 通常は、`Event`モジュールを使用してイベントの監視/処理を行うことを推奨します。
> 同時に、`Event`モジュールは強力なラッパーを提供し、モジュール開発の利便性を高めます。

```python
# OneBot12 標準イベントを監視
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 特定プラットフォームの標準イベントを監視
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# プラットフォームのネイティブイベントを監視
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### アダプタ管理

```python
# 全プラットフォームを取得
platforms = sdk.adapter.platforms

# アダプタが存在するか確認
exists = sdk.adapter.exists("platform_name")

# アダプタの有効化/無効化
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# アダプタの起動/停止
# 以下のメソッドはすべて引数を渡す例を示しています。引数がない場合は、登録済みのすべてのアダプタの起動/停止を意味します
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# アダプタが実行中か確認
is_running = sdk.adapter.is_running("platform_name")

# 実行中のアダプタを一覧表示
running = sdk.adapter.list_running()
```

## ミドルウェア

### ミドルウェアの登録

```python
# ミドルウェアを追加
@sdk.adapter.middleware
async def my_middleware(event):
    # イベントを処理
    sdk.logger.info(f"ミドルウェア処理: {event}")
    return event
```

### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、イベントがハンドラにルーティングされる前に実行されます。

## Send メッセージ送信

### 基本的な送信

```python
# アダプタを取得
adapter = sdk.adapter.get("platform")

# テキストメッセージを送信
await adapter.Send.To("user", "123").Text("Hello")

# 画像メッセージを送信
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### 送信アカウントの指定

```python
# アカウント名を使用
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# アカウント ID を使用
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### サポートされている送信メソッドのクエリ

```python
# プラットフォームがサポートするすべての送信メソッドを一覧表示
methods = sdk.adapter.list_sends("onebot11")
# 返回: ["Text", "Image", "Voice", "Markdown", ...]

# 特定のメソッドの詳細を取得
info = sdk.adapter.send_info("onebot11", "Text")
# 返回:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "テキストメッセージを送信..."
# }
```

### チェーン構造修飾

```python
# @ユーザー
await adapter.Send.To("group", "456").At("789").Text("こんにちは")

# @全体メンバー
await adapter.Send.To("group", "456").AtAll().Text("皆さんこんにちは")

# メッセージへの返信
await adapter.Send.To("group", "456").Reply("msg_id").Text("返信内容")

# 組み合わせて使用
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("@への返信")
```

## API 呼び出し

### call_api メソッド
> 注意：各プラットフォームの API 呼び出し方法は異なる場合があります。各プラットフォーム固有のアダプタドキュメントを参照してください。
> call_api メソッドを直接使用することは推奨されません。メッセージ送信には Send クラスを使用することを推奨します。

```python
# プラットフォーム API を呼び出す
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# 標準化された応答
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "msg_id",
    "message": "",
    "{platform}_raw": raw_response
}
```

## アダプタの基本クラス

### BaseAdapter メソッド

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        # アダプタを初期化
        pass
    
    async def start(self):
        """アダプタを起動（必須実装）"""
        pass
    
    async def shutdown(self):
        """アダプタを停止（必須実装）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出す（必須実装）"""
        pass
```

### Send ネストクラス

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """テキストメッセージを送信"""
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
```

## Bot ステータス管理

アダプタは、OneBot12 標準の **`meta` イベント**を送信することで、フレームワークに対して Bot の接続状態を通知します。システムは自動的に Bot 情報を抽出し、ステータス追跡を行います。

### meta イベントの種類

アダプタは以下の 3 種類の `meta` イベントを送信すべきです：

| `type` | `detail_type` | 説明 | 実行タイミング |
|--------|--------------|------|---------|
| `meta` | `connect` | Bot 接続開始 | アダプタとプラットフォームの接続に成功した後 |
| `meta` | `heartbeat` | Bot ハートビート | 定期的に送信（推奨 30-60 秒） |
| `meta` | `disconnect` | Bot 接続切断 | 接続切断を検知した時 |

### self フィールドの拡張

ErisPulse は OneBot12 標準の `self` フィールドに以下の拡張フィールドを追加しています：

| フィールド | タイプ | 説明 |
|------|------|------|
| `self.platform` | string | プラットフォーム名（OB12 標準） |
| `self.user_id` | string | Bot ユーザー ID（OB12 標準） |
| `self.user_name` | string | Bot の表示名（ErisPulse 拡張） |
| `self.avatar` | string | Bot のアバター URL（ErisPulse 拡張） |
| `self.account_id` | string | マルチアカウント識別子（ErisPulse 拡張） |

### meta イベントのフォーマット

#### connect — 接続開始

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345678,
    "type": "meta",
    "detail_type": "connect",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456",
        "user_name": "MyBot",
        "avatar": "https://example.com/avatar.jpg"
    },
    "telegram_raw": {...},
    "telegram_raw_type": "bot_connected"
})
```

システム処理：Bot を登録し、`online` としてマーク、`adapter.bot.online` ライフサイクルイベントをトリガーします。

#### heartbeat — ハートビート

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345708,
    "type": "meta",
    "detail_type": "heartbeat",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456"
    }
})
```

システム処理：`last_active` 時間を更新します（ハートビートでもメタ情報の更新がサポートされています）。

#### disconnect — 接続切断

```python
await adapter.emit({
    "id": "unique_id",
    "time": 1712345738,
    "type": "meta",
    "detail_type": "disconnect",
    "platform": "telegram",
    "self": {
        "platform": "telegram",
        "user_id": "123456"
    }
})
```

システム処理：Bot を `offline` としてマークし、`adapter.bot.offline` ライフサイクルイベントをトリガーします。

### 通常イベントの自動検出

`meta` イベントに加え、通常のイベント（`message`/`notice`/`request`）の `self` フィールドも自動的に検出され、Bot を登録してアクティビティ時間を更新します。これは、アダプタが `connect` イベントを送信しなくても、フレームワークが最初の通常イベントから Bot を検出できることを意味します。

### アダプタ実装例

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # プラットフォームと接続を確立...
        connection = await self._connect()
        
        # 接続に成功し、connect イベントを送信
        await adapter.emit({
            "id": str(uuid4()),
            "time": int(time.time()),
            "type": "meta",
            "detail_type": "connect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": self.bot_id,
                "user_name": self.bot_name,
                "avatar": self.bot_avatar
            },
            "myplatform_raw": raw_data,
            "myplatform_raw_type": "connected"
        })
    
    async def on_disconnect(self):
        # 接続切断し、disconnect イベントを送信
        await adapter.emit({
            "id": str(uuid4()),
            "time": int(time.time()),
            "type": "meta",
            "detail_type": "disconnect",
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": self.bot_id
            }
        })
```

### Bot ステータスの照会

```python
# 全アダプタと Bot の完全なステータスを取得（WebUI 友好）
summary = sdk.adapter.get_status_summary()
# {
#     "adapters": {
#         "telegram": {
#             "status": "started",
#             "bots": {
#                 "123456": {
#                     "status": "online",
#                     "last_active": 1712345678.0,
#                     "info": {"nickname": "MyBot"}
#                 }
#             }
#         }
#     }
# }

# 全 Bot を一覧表示
all_bots = sdk.adapter.list_bots()

# 指定プラットフォームの Bot を一覧表示
tg_bots = sdk.adapter.list_bots("telegram")

# 単一の Bot の詳細を取得
info = sdk.adapter.get_bot_info("telegram", "123456")

# Bot がオンラインか確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot オンライン")
```

### Bot ステータス値

| ステータス | 説明 |
|------|------|
| `online` | オンライン（継続的にイベントを受信、またはアダプタが主动でマークした場合） |
| `offline` | オフライン（アダプタが主动でマーク、またはシステムシャットダウン時に自動設定） |
| `unknown` | 不明（登録のみでステータス未確認） |

### ライフサイクルイベント

| イベント名 | 実行タイミング | データ |
|--------|---------|------|
| `adapter.bot.online` | 新しい Bot が自動的に検出された時 | `{platform, bot_id, status}` |
| `adapter.status.change` | アダプタのステータスが変更された時（starting/started/stopping/stopped/stop_failed） | `{platform, status}` |

```python
# Bot オンラインイベントを監視
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot オンライン: {event['data']['platform']}/{event['data']['bot_id']}")

# アダプタのステータス変化を監視
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"アダプタのステータス: {event['data']['platform']} -> {event['data']['status']}")
```

> システムシャットダウン時（`shutdown`）、すべての Bot は自動的に `offline` としてマークされます。

## 関連ドキュメント

- [コアモジュール API](core-modules.md) - コアモジュール API
- [イベントシステム API](event-system.md) - Event モジュール API
- [アダプタ開発ガイド](../developer-guide/adapters/) - プラットフォームアダプタの開発



### 核心模块 API

# コアモジュール API

このドキュメントでは、ErisPulseのコアモジュールAPIについて詳しく説明します。

## Storage モジュール

### 基本的な操作

```python
from ErisPulse import sdk

# 値の設定
sdk.storage.set("key", "value")

# 値の取得
value = sdk.storage.get("key", default_value)

# すべてのキーを取得
keys = sdk.storage.keys()

# 値を削除
sdk.storage.delete("key")
```

### トランザクション操作

```python
# トランザクションを使用してデータの一貫性を確保
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # いずれかの操作が失敗した場合、すべての変更はロールバックされます
```

### バッチ操作

```python
# 一括設定
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# 一括取得
values = sdk.storage.get_multi(["key1", "key2", "key3"])

# 一括削除
sdk.storage.delete_multi(["key1", "key2", "key3"])
```

### SQL チェーン呼び出しクエリ

Storage モジュールは、チェーン呼び出しスタイルの汎用 SQL クエリビルダーを提供し、カスタムテーブルの CRUD 操作をサポートしています。

> 完全なドキュメントについては、[SQL クエリビルダー](../advanced/sql-builder.md)を参照してください。

```python
from ErisPulse import sdk

# カスタムテーブルの作成
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0"
})

# データの挿入
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# 一括挿入
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]).Execute()

# データのクエリ
rows = (sdk.storage.Table("users")
    .Select("name", "age")
    .Where("age > ?", 18)
    .OrderBy("name")
    .Limit(10)
    .Execute())

# データの更新
sdk.storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()

# データの削除
sdk.storage.Table("users").Delete().Where("name = ?", "Bob").Execute()

# カウント
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# 存在性のチェック
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()

# 1件のレコードを取得
row = sdk.storage.Table("users").Select("name", "age").Where("name = ?", "Alice").ExecuteOne()

# テーブル構造の変更
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# テーブルが存在するか確認
if sdk.storage.HasTable("users"):
    sdk.storage.DropTable("users")

# トランザクション内でのチェーン操作
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Dave", "age": 40}).Execute()
    sdk.storage.Table("users").Update({"age": 41}).Where("name = ?", "Dave").Execute()

# クエリ条件の再利用
base = sdk.storage.Table("users").Where("age > ?", 20)
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()
count = base.copy().Count()
```

### ストレージバックエンド抽象

`StorageManager` は `BaseStorage` 抽象基底クラスを継承しており、将来の他のストレージメディア（Redis、MySQL など）の拡張をサポートしています。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

# BaseStorage は統一されたインターフェースを定義します：get/set/delete/Table/CreateTable/DropTable など
# BaseQueryBuilder はチェーンクエリインターフェースを定義します：Select/Insert/Update/Delete/Where/OrderBy/Limit など
```

## Config モジュール

### 設定の読み込み

```python
from ErisPulse import sdk

# 設定を取得
config = sdk.config.getConfig("MyModule", {})

# ネストされた設定を取得
value = sdk.config.getConfig("MyModule.subkey.value", "default")
```

### 設定の書き込み

```python
# 設定を設定
sdk.config.setConfig("MyModule", {"key": "value"})

# ネストされた設定を設定
sdk.config.setConfig("MyModule.subkey.value", "new_value")
```

### 設定の例

```python
def _load_config(self):
    config = sdk.config.getConfig("MyModule")
    if not config:
        # デフォルト設定を作成
        default_config = {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "cache_ttl": 3600
        }
        sdk.config.setConfig("MyModule", default_config, immediate=True)  # 第3引数がTrueの場合、設定は即座に保存されます。ユーザーが設定ファイルを直接変更できるように便利です。
        return default_config
    return config
```

## Logger モジュール

### 基本的なログ

```python
from ErisPulse import sdk

# 異なるログレベル
sdk.logger.debug("デバッグ情報")
sdk.logger.info("実行情報")
sdk.logger.warning("警告情報")
sdk.logger.error("エラー情報")
sdk.logger.critical("致命的なエラー")
```

### 子ログ記録子

```python
# 子ロガーを取得
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("サブモジュールログ")

# サブモジュールはさらにサブモジュールを持つことができ、これによりログ出力をより精確に制御できます
child_logger.get_child("utils")
```

### ログ出力

```python
# 出力ファイルを設定
sdk.logger.set_output_file("app.log")

# ファイルにログを保存
sdk.logger.save_logs("log.txt")
```

## Adapter モジュール

### アダプターの取得

```python
from ErisPulse import sdk

# アダプターインスタンスを取得
adapter = sdk.adapter.get("platform_name")

# プロパティを介してアクセス
adapter = sdk.adapter.platform_name
```

### アダプターエベント

```python
# 標準イベントを監視
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 特定プラットフォームのイベントを監視
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# プラットフォームネイティブイベントを監視
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### アダプター管理

```python
# すべてのプラットフォームを取得
platforms = sdk.adapter.platforms

# アダプターが存在するか確認
exists = sdk.adapter.exists("platform_name")

# アダプターを有効化/無効化
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# アダプターを起動/シャットダウン
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# アダプターが実行中か確認
is_running = sdk.adapter.is_running("platform_name")

# 実行中のすべてのアダプターを一覧表示
running = sdk.adapter.list_running()
```

## Module モジュール

### モジュールの取得

```python
from ErisPulse import sdk

# モジュールインスタンスを取得
module = sdk.module.get("ModuleName")

# プロパティを介してアクセス
module = sdk.module.ModuleName
module = sdk.ModuleName
```

### モジュール管理

```python
# モジュールが存在するか確認
exists = sdk.module.exists("ModuleName")

# モジュールがロード済みか確認
is_loaded = sdk.module.is_loaded("ModuleName")

# モジュールが有効か確認
is_enabled = sdk.module.is_enabled("ModuleName")

# モジュールを有効化/無効化
sdk.module.enable("ModuleName")
sdk.module.disable("ModuleName")

# モジュールをロード
await sdk.module.load("ModuleName")

# モジュールをアンロード
await sdk.module.unload("ModuleName")

# ロード済みのモジュールを一覧表示
loaded = sdk.module.list_loaded()

# 登録済みのモジュールを一覧表示
registered = sdk.module.list_registered()

# モジュール情報を取得
info = sdk.module.get_info("ModuleName")

# モジュールステータスのサマリーを取得
summary = sdk.module.get_status_summary()
# {"modules": {"ModuleName": {"status": "loaded", "enabled": True, "is_base_module": True}}}

# モジュールが実行中か確認（is_loaded と同等）
is_running = sdk.module.is_running("ModuleName")

# 実行中のすべてのモジュールを一覧表示
running = sdk.module.list_running()
```

## Lifecycle モジュール

### イベントの送信

```python
from ErisPulse import sdk

# カスタムイベントを送信
await sdk.lifecycle.submit_event(
    "custom.event",
    data={"key": "value"},
    source="MyModule",
    msg="カスタムイベントの説明"
)
```

### イベント監視

```python
# 特定のイベントを監視
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"モジュール初期化: {event_data}")

# 親レベルのイベントを監視
@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"モジュールイベント: {event_data}")

# すべてのイベントを監視
@sdk.lifecycle.on("*")
async def handle_any_event(event_data):
    print(f"システムイベント: {event_data}")
```

### タイマー

```python
# タイマーを開始
sdk.lifecycle.start_timer("my_operation")

# ... 操作を実行 ...

# 持続時間を取得
duration = sdk.lifecycle.get_duration("my_operation")

# タイマーを停止
total_time = sdk.lifecycle.stop_timer("my_operation")
```

## Router モジュール

### 抽象型

Router は2つの型アノテーションスタイルをサポートしています：

```python
# ErisPulse抽象型（推奨、移植性が高い）
from ErisPulse.Core import HttpRequest, WebSocketConnection

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}

# FastAPIネイティブ型（既存のコードとの互換性）
from fastapi import Request, WebSocket

@sdk.router.get("MyModule", "/api2")
async def handler(request: Request):
    return {"status": "ok"}
```

> ルーターはパラメータアノテーションに基づいて対応するタイプのオブジェクトを自動的に注入します。詳細については、[ルーター管理](../advanced/router.md)を参照してください。

### デコレーターローター（推奨）

```python
from ErisPulse import sdk
from fastapi import Request

# HTTPルーターデコレーター
@sdk.router.http("MyModule", "/api", methods=["GET", "POST"])
async def api_handler(request: Request):
    return {"status": "ok"}

# 短縮メソッドデコレーター
@sdk.router.get("MyModule", "/info")
async def get_info(request: Request):
    return {"module": "MyModule"}

@sdk.router.post("MyModule", "/data")
async def post_data(request: Request):
    data = await request.json()
    return {"received": data}

@sdk.router.put("MyModule", "/data/{item_id}")
async def put_data(request: Request):
    return {"updated": True}

@sdk.router.delete("MyModule", "/data/{item_id}")
async def delete_data(request: Request):
    return {"deleted": True}

# WebSocketデコレーター
from fastapi import WebSocket

@sdk.router.ws("MyModule", "/ws")
async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# 認証付きWebSocketデコレーター
async def ws_auth(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

@sdk.router.ws("MyModule", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

### 従来の登録方式

```python
from ErisPulse import sdk
from fastapi import Request

async def handler(request: Request):
    data = await request.json()
    return {"status": "ok", "data": data}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/api",
    handler=handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="データインターフェース",
    tags=["API"],
)

sdk.router.unregister_http_route("MyModule", "/api")
```

### WebSocketルーター

```python
from ErisPulse import sdk
from fastapi import WebSocket

async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# 基本的な登録（接続を自動的に受け入れる）
sdk.router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# 認証付きの登録（推奨：auth_handlerを使用して接続を制御）
async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

sdk.router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)

# ルーターを解除
sdk.router.unregister_websocket("MyModule", "/ws")
```

**パラメータの説明：**

| パラメータ | 説明 | デフォルト値 |
|------|------|--------|
| `module_name` | モジュール名（必須） | - |
| `path` | WebSocketパス | - |
| `handler` | ハンドラー関数 | - |
| `auth_handler` | 認証関数。`False`を返すと接続が自動的に閉じられます | `None` |
| `auto_accept` | `accept()` を自動的に呼び出すかどうか | `True` |

> **推奨**: `auth_handler` を使用して接続確認を行い、`auto_accept` を無効化（閉じる）の代わりにしてください。接続フローを完全に制御する必要がある場合にのみ、`auto_accept=False` を設定してください。

### ルーターグループ

```python
# ルーターグループを作成
group = sdk.router.group("MyModule", prefix="/v1")

# グループ内でルーターを登録
@group.get("/users")
async def list_users(request: Request):
    return {"users": []}

@group.post("/users")
async def create_user(request: Request):
    return {"created": True}

# バージョン付きのグループ
v2 = sdk.router.group("MyModule", prefix="/v2", version="2")
```

### ルーターミドルウェア

```python
# グローバルミドルウェア（globマッチング）
@sdk.router.middleware("/MyModule/*")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    response = await call_next(request)
    return response

# 特定のパスミドルウェア
@sdk.router.middleware("/MyModule/admin/*")
async def admin_middleware(request: Request, call_next):
    return await call_next(request)
```

### レート制限

```python
# ルーターにレート制限を設定（スライディングウィンドウ）
@sdk.router.get("MyModule", "/limited", rate_limit="10/minute")
async def limited_endpoint(request: Request):
    return {"ok": True}

@sdk.router.post("MyModule", "/submit", rate_limit="5/minute")
async def submit_data(request: Request):
    return {"submitted": True}
```

### CORS設定

```python
# コードによる設定
sdk.router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 設定ファイルによる設定（config.toml）
# [router.cors]
# allow_origins = ["https://example.com"]
# allow_methods = ["GET", "POST"]
# allow_headers = ["*"]
```

### セキュリティヘッダー

```python
# セキュリティヘッダーを自動的に追加
sdk.router.setup_security_headers()

# 設定ファイルによる設定（config.toml）
# [router.security]
# enabled = true
```

### 自動ドキュメント

```python
# RouterはデフォルトでOpenAPIドキュメントを有効にします
# ドキュメントを無効化
sdk.router.disable_docs()

# カスタムドキュメント情報を設定
sdk.router.set_docs_info(
    title="My API",
    description="API ドキュメント",
    version="1.0.0"
)
```

### ルーター情報

```python
app = sdk.router.get_app()
```

## HTTP Client モジュール

### 基本的なリクエスト

```python
from ErisPulse.Core import client

# GETリクエスト
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# POSTリクエスト
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# PUT / DELETE / PATCH
resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})

# 一般的なrequestメソッド
resp = await client.request("OPTIONS", "https://api.example.com/resource")
```

### レスポンスオブジェクト

```python
from ErisPulse.Core import client

resp = await client.get("https://api.example.com/users")

resp.status        # int - HTTPステータスコード (例: 200, 404)
resp.reason        # str | None - ステータスの説明 (例: "OK")
resp.headers       # レスポンスヘッダー (大文字・小文字を区別しない)
resp.content_type  # str | None - Content-Type
resp.url           # 最終的な URL (リダイレクトにより変更される場合があります)
resp.raw           # 基底のネイティブレスポンスオブジェクト (現在は aiohttp.ClientResponse)

# レスポンスボディの読み込み
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # JSONの解析
text = await resp.text("gbk")  # エンコーディングを指定
```

### リクエストパラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `url` | `str



====
高级主题
====


### 生命周期管理

# ライフサイクル管理

ErisPulseは、システム内の各コンポーネントの稼働状態を監視し、監査、統計、カスタムロジックなどの拡張機能を実装するための統一されたフック/ライフサイクルシステムを提供します。

システムは3つのトリガー方法をサポートしています：
- `await lifecycle.emit("event", data)` — 簡易版、任意のデータを渡す
- `lifecycle.emit_sync("event", data)` — 同期版（非同期コンテキスト以外で使用）
- `await lifecycle.submit_event("event", ...)` — 旧バージョン互換、標準イベントフォーマットを自動構築

## イベント処理メカニズム

### ハンドラの登録

```python
from ErisPulse import sdk

# デコレータパターン
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"モジュールロード: {data}")

# プログラムによる登録
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# 登録解除
sdk.lifecycle.unregister("module.load", on_module_load)
```

### 優先度

ハンドラは `priority` パラメータをサポートしており、数値が大きいほど先に実行されます（モジュールローダーと同様）：

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # 最初に実行
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # 後から実行
async def second_handler(data):
    pass
```

### ドット区切りのイベント構造

具体的なイベントをトリガーすると、その親イベントもトリガーされます：
- `module.load` をトリガーすると、`module` もトリガーされます
- `adapter.event.receive` をトリガーすると、`adapter.event` と `adapter` もトリガーされます

### ワイルドカード

`*` を登録するとすべてのイベントをキャプチャします：

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"イベント受信: {data}")
```

## フックポイント一覧

フレームワークには以下のフックポイントが組み込まれており、ユーザーは `@sdk.lifecycle.on()` で任意のポイントをリッスンしてカスタムロジックを実装できます。

### コア初期化

| フック名 | トリガーのタイミング | データ |
|---------|---------|------|
| `core.init.start` | SDK初期化開始 | `{}` |
| `core.init.complete` | SDK初期化完了 | `{"duration": float, "success": bool, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(失敗時のみ)}` |
| `core.uninit.complete` | SDKアンインシャライズ完了 | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(失敗時のみ)}` |

### 設定変更

| フック名 | トリガーのタイミング | データ |
|---------|---------|------|
| `config.set` | 設定項目が変更された | `{"key": str, "old_value": Any, "new_value": Any}` |

**例：設定の監査**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[監査] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### モジュールライフサイクル

| フック名 | トリガーのタイミング | データ |
|---------|---------|------|
| `module.register` | モジュールクラスがマネージャーに登録された | `{"module_name": str, "success": bool}` |
| `module.load` | モジュールのロード完了（インスタンス化成功） | `{"module_name": str, "success": bool}` |
| `module.init` | モジュールの初期化完了（遅延読み込みを含む） | `{"module_name": str, "success": bool}` |
| `module.unload` | モジュールのアンロード | `{"module_name": str, "success": bool}` |

### アダプターライフサイクル

| フック名 | トリガーのタイミング | データ |
|---------|---------|------|
| `adapter.load` | アダプターの登録完了 | `{"platform": str, "success": bool}` |
| `adapter.start` | アダプターの起動 | `{"platforms": [str]}` |
| `adapter.status.change` | アダプターの状態変化 | `{"platform": str, "status": str, "retry_count": int, "error": str(失敗時のみ)}` |
| `adapter.stop` | アダプターの終了 | `{"platforms": [str]}` |
| `adapter.stopped` | アダプターの終了完了 | `{"platforms": [str]}` |
| `adapter.bot.online` | Botオンライン | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Botオフライン | `{"platform": str, "bot_id": str, "status": str}` |

### イベントの受信と処理

| フック名 | トリガーのタイミング | データ |
|---------|---------|------|
| `adapter.event.receive` | 外部プラットフォームイベントの受信（最初期） | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.dispatched` | イベントのディスパッチ完了 | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | イベントハンドラの実行開始前 | `{"event_type": str, "platform": str, "detail_type": str}` |

**例：イベント統計**

```python
event_counter = {}

@sdk.lifecycle.on("adapter.event.receive")
def count_events(data):
    platform = data["platform"]
    event_counter[platform] = event_counter.get(platform, 0) + 1

@sdk.lifecycle.on("adapter.event.dispatched")
def log_unhandled(data):
    if data["onebot_handlers_count"] == 0:
        print(f"[未処理] {data['platform']}/{data['event_type']}")
```

### メッセージ送信

| フック名 | トリガーのタイミング | データ |
|---------|---------|------|
| `message.sending` | メッセージの送信直前 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | メッセージ送信完了 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**例：メッセージ送信の監査**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[送信] -> {data['platform']}/{data['detail_type']}/{data['target_id']} via {data['method']}")
```

### コマンドシステム

| フック名 | トリガーのタイミング | データ |
|---------|---------|------|
| `command.matched` | コマンドがマッチし、実行直前 | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | コマンド実行完了 | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(失敗時のみ)}` |

**例：コマンド統計**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[コマンド] /{data['command']} from {data['user_id']}@{data['platform']}")
```

### HTTPルーティング

| フック名 | トリガーのタイミング | データ |
|---------|---------|------|
| `server.request` | HTTPリクエスト受信 | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | HTTPレスポンス送信 | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**例：リクエストログ**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| フック名 | トリガーのタイミング | データ |
|---------|---------|------|
| `server.start` | ルーティングサーバー起動 | `{"base_url": str, "host": str, "port": int}` |
| `server.stop` | ルーティングサーバー停止 | `{}` |
| `server.websocket.connect` | WebSocket接続確立 | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket接続切断 | `{"path": str, "module_name": str, "reason": str, "error": str(例外時のみ)}` |

**例：WebSocket接続の監視**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] 接続: {data['path']} from {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] 切断: {data['path']} ({data['reason']})")
```

## 標準イベント定義

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.complete", "uninit.complete"],
    "module": ["load", "init", "unload", "register"],
    "adapter": [
        "load", "start", "status.change", "stop", "stopped",
        "event.receive", "event.dispatched",
        "bot.online", "bot.offline",
    ],
    "server": [
        "start", "stop",
        "request", "response",
        "websocket.connect", "websocket.disconnect",
    ],
    "event": ["pre_process"],
    "message": ["sending", "sent"],
    "command": ["matched", "executed"],
    "config": ["set"],
}
```

## 完全なAPIリファレンス

### 登録と解除

| メソッド | 説明 |
|------|------|
| `@lifecycle.on(event, *, priority=0)` | デコレータによるハンドラ登録 |
| `lifecycle.register(event, handler, *, priority=0)` | プログラムによる登録 |
| `lifecycle.unregister(event, handler=None)` | 登録解除（handler=None の場合、そのイベントの全ハンドラを解除） |

### トリガー

| メソッド | 説明 |
|------|------|
| `await lifecycle.emit(event, data=None)` | 非同期トリガー、ハンドラが非 None を返すと data を変更可能 |
| `lifecycle.emit_sync(event, data=None)` | 同期トリガー、非同期ハンドラは create_task でスケジュール |
| `await lifecycle.submit_event(event_type, *, source, msg, data)` | 旧バージョン互換、標準イベントフォーマットを自動構築 |

### ユーティリティ

| メソッド | 説明 |
|------|------|
| `lifecycle.start_timer(timer_id)` | タイマー開始 |
| `lifecycle.get_duration(timer_id)` | 経過時間の取得（秒） |
| `lifecycle.stop_timer(timer_id)` | タイマー停止および経過時間を返す |
| `lifecycle.list_hooks()` | 登録済みのすべてのフックおよびハンドラ数を一覧表示 |
| `lifecycle.clear()` | すべてのハンドラとタイマーをクリア |

## モジュール内での使用例

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # 簡単なメッセージ統計の実装
        self.msg_count = 0
        
        @sdk.lifecycle.on("adapter.event.receive")
        async def count(data):
            if data["event_type"] == "message":
                self.msg_count += 1
        
        # すべてのコマンドを監視
        @sdk.lifecycle.on("command.matched")
        async def log_cmd(data):
            sdk.logger.info(f"コマンド実行: /{data['command']} by {data['user_id']}")
        
        # 設定変更の監査
        @sdk.lifecycle.on("config.set")
        def audit(data):
            sdk.logger.info(f"設定変更: {data['key']} = {data['new_value']}")
```

## 注意事項

1. **ハンドラは同期または非同期が可能**：システムが自動的に識別し、正しく呼び出します
2. **データの受け渡し**：`emit()` モードでは、ハンドラが非 None 値を返すと、後続のハンドラに渡される data が変更されます
3. **イベントの命名規則**：親のリッスンを利用しやすくするため、イベント名にはドット区切り構造を使用することをお勧めします
4. **エラーの分離**：単一のハンドラで例外が発生しても、他のハンドラの実行には影響しません
5. **同期トリガーの制限**：`emit_sync()` では、非同期ハンドラは fire-and-forget 方式でスケジュールされるため、戻り値を返すことができません
6. **ライフサイクルのクリーンアップ**：`sdk.uninit()` を呼び出すと、登録されているすべてのハンドラとタイマーがクリーンアップされます
7. **ロードの優先度**：フレームワークの初期化段階でイベントをリッスンする必要がある場合は、高い優先度を設定し、遅延読み込みを無効にすることをお勧めします

## 関連ドキュメント

- [モジュール開発ガイド](../developer-guide/modules/getting-started.md) - モジュールのライフサイクルメソッドについて
- [ベストプラクティス](../developer-guide/modules/best-practices.md) - ライフサイクルイベントの使用に関する推奨事項



### 懒加载系统

# リアルタイム読み込みモジュールシステム

ErisPulse SDK は、モジュールを実際に必要になったときにのみ初期化できる強力な**リアルタイム読み込み（Lazy Loading）**モジュールシステムを提供しています。

## 概要

リアルタイム読み込みモジュールシステムは、ErisPulse の主要な機能の一つであり、次のように動作します：

- **遅延初期化**：モジュールは、初めてアクセスされたときのみ実際に読み込まれて初期化されます
- **透過的な使用**：開発者にとって、リアルタイム読み込みモジュールは通常のモジュールと使用上ほとんど違いがありません
- **自動依存管理**：モジュールの依存関係は、使用時に自動的に初期化されます
- **ライフサイクルサポート**：`BaseModule` を継承したモジュールの場合、ライフサイクルメソッドが自動的に呼び出されます

## 動作原理

### LazyModule クラス

リアルタイム読み込みシステムのコアは `LazyModule` クラスであり、これは最初のアクセス時のみモジュールを実際に初期化するラッパーです。

### 初期化プロセス

モジュールが初めてアクセスされるとき、`LazyModule` は以下の操作を実行します：

1. モジュールクラスの `__init__` パラメータ情報を取得
2. パラメータに基づいて `sdk` 参照を渡すかどうかを決定
3. モジュールの `moduleInfo` プロパティを設定
4. `BaseModule` を継承したモジュールの場合、`on_load` メソッドを呼び出し
5. `module.init` ライフサイクルイベントをトリガー

## リアルタイム読み込みの設定

### グローバル設定

設定ファイルでグローバルなリアルタイム読み込みを有効化/無効化します：

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true=リアルタイム読み込み有効（デフォルト）、false=リアルタイム読み込み無効
```

### モジュールレベルでの制御

モジュールは `get_load_strategy()` 静的メソッドを実装することで読み込み戦略を制御できます：

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """モジュールの読み込み戦略を返します"""
        return ModuleLoadStrategy(
            lazy_load=False,  # false を返すと即時読み込みを示します
            priority=100      # 読み込み優先度、数値が大きいほど優先度が高くなります
        )
```

## リアルタイム読み込みモジュールの使用

### 基本的な使用方法

開発者にとって、リアルタイム読み込みモジュールは通常のモジュールと使用上ほとんど違いがありません：

```python
# SDK を介してリアルタイム読み込みモジュールにアクセス
from ErisPulse import sdk

# 以下のアクセスはモジュールの遅延読み込みをトリガーします
result = await sdk.my_module.my_method()
```

### 非同期初期化

非同期初期化が必要なモジュールについては、最初に明示的に読み込むことを推奨します：

```python
# モジュールを最初に明示的に読み込み
await sdk.load_module("my_module")

# その後、モジュールを使用します
result = await sdk.my_module.my_method()
```

### 同期初期化

非同期初期化が不要なモジュールについては、直接アクセスできます：

```python
# 直接アクセスは自動的に同期初期化を行います
result = sdk.my_module.some_sync_method()
```

## ベストプラクティス

### リアルタイム読み込みを使用することを推奨するシナリオ（lazy_load=True）

- 受動的に呼び出されるユーティリティクラス
- 受動的なモジュールクラス

### リアルタイム読み込みを無効にすることを推奨するシナリオ（lazy_load=False）

- トリガーを登録するモジュール（例：コマンドハンドラー、メッセージハンドラー）
- ライフサイクルイベントリスナー
- 定期的なタスクモジュール
- アプリケーション起動時に初期化する必要があるモジュール

### 読み込み優先度

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,  # 即時読み込み
            priority=100      # 高優先度、数値が大きいほど優先度が高くなります
        )
```

## 注意事項

1. モジュールがリアルタイム読み込みを使用している場合、他のモジュールから一度も ErisPulse 内で呼び出されない場合、そのモジュールは初期化されない可能性があります。
2. モジュールにイベントを監聴する機能（Event）や、その他のモジュールを積極的に監視する機能が含まれている場合は、すぐに読み込まれる必要があると宣言してください。さもないと、正常な業務動作に影響を及ぼす可能性があります。
3. 特別な要件がない限り、リアルタイム読み込みを無効にすることは推奨しません。それにより、依存関係管理やライフサイクルイベントなどの問題が発生する可能性があります。

## 関連ドキュメント

- [モジュール開発ガイド](../developer-guide/modules/getting-started.md) - モジュールの開発を学ぶ
- [ベストプラクティス](../developer-guide/modules/best-practices.md) - その他のベストプラクティスについて学ぶ



### Dashboard 视窗注册

# Dashboard View の登録

Dashboard は、他の ErisPulse モジュールがカスタム管理ページを Dashboard のサイドバーに登録することをサポートしています。登録後、ユーザーは Dashboard 内でそのモジュール専用の View ページに切り替えることができ、別途独立したフロントエンド インターフェースの開発は不要になります。

> **前提条件**
>
> Dashboard View の登録は**オプション機能**であり、[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) モジュールをインストールして読み込む必要があります。
>
> *   Dashboard モジュールが**インストールされていない**または**読み込まれていない**場合、`sdk.Dashboard.register_view()` を呼び出すと例外が発生します
> *   登録コードを `try/except` で囲むことを強くお勧めします。これは、Dashboard モジュール自体の他の機能に影響を与えないようにするためです
> *   登録前に Dashboard が使用可能かを確認することを推奨します：`hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## 動作原理

```
モジュール on_load()
  → sdk.Dashboard.register_view(...) の呼び出し
  → Dashboard バックエンドで View 情報を保存
  → WebSocket でフロントエンドへ通知
  → フロントエンドでサイドバーのナビゲーション項目とページコンテナを動的に作成
  → ユーザーがクリックしてモジュール View を表示
```

---

## 登録 API

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # 必須、一意の識別子
    title="我的模块",                  # 中国語名
    title_en="My Module",             # 英語名
    icon_svg='<svg>...</svg>',        # サイドバーのアイコン SVG
    html_content='<div>...</div>',     # ページ HTML コンテンツ
    js_content='function xxx() {}',    # ページ JavaScript ロジック
    css_content='.my-style {}',        # オプションのカスタム CSS
    iframe_url='',                     # iframe モード URL（html_content とのどちらか一方）
    loader="loadMyModuleView",         # そのページに切り替える際に呼び出される JS 関数名
    group="group_extensions",          # サイドバーのグループ
    group_title="",                    # カスタムグループの中国語タイトル
    group_title_en="",                 # カスタムグループの英語タイトル
)
```

### パラメータ説明

| パラメータ | 型 | 必須 | 説明 |
|------|------|------|------|
| `id` | `str` | Yes | View の一意の識別子。モジュール名を使用することを推奨します |
| `title` | `str` | No | 中国語表示名。デフォルトは `id` |
| `title_en` | `str` | No | 英語表示名。デフォルトは `title` |
| `icon_svg` | `str` | No | サイドバーのアイコンの完全な SVG 文字列 |
| `html_content` | `str` | No* | 注入モードのページ HTML コンテンツ |
| `js_content` | `str` | No | ページ JavaScript コード |
| `css_content` | `str` | No | ページのカスタム CSS スタイル |
| `iframe_url` | `str` | No* | iframe モードの URL。設定すると `html_content` は無視されます |
| `loader` | `str` | No | ページがアクティブ化されたときに自動的に呼び出される JS 関数名 |
| `group` | `str` | No | サイドバーのグループ識別子。デフォルトは `group_extensions` |
| `group_title` | `str` | No | カスタムグループの中国語タイトル |
| `group_title_en` | `str` | No | カスタムグループの英語タイトル |

> *`html_content` と `iframe_url` の少なくとも一方を指定する必要があります。そうしないと、ページは空になります。

---

## 2つの注入モード

### モード1：HTML/JS 注入（推奨）

HTML、JS、CSS の文字列を直接提供すると、Dashboard はコンテンツをページ内に注入します。このモードは Dashboard のスタイルと完全に一致しており、Dashboard が提供する CSS クラス名を使用することを推奨します。

```python
sdk.Dashboard.register_view(
    id="Weather",
    title="天气", title_en="Weather",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
    html_content='''
        <h1 class="page-title">天气查询</h1>
        <div class="grid-2">
            <div class="card">
                <div class="card-header">当前天气</div>
                <div class="card-body">
                    <div id="weather-info">加载中...</div>
                </div>
            </div>
            <div class="card">
                <div class="card-header">操作</div>
                <div class="card-body">
                    <button class="btn btn-primary" onclick="refreshWeather()">刷新</button>
                </div>
            </div>
        </div>
    ''',
    js_content='''
        async function loadWeatherView() {
            await refreshWeather();
        }
        async function refreshWeather() {
            var el = document.getElementById('weather-info');
            if (!el) return;
            try {
                var token = localStorage.getItem('__ep_tk__');
                var resp = await fetch('/Weather/api/current', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                var data = await resp.json();
                el.innerHTML = '<p>温度: ' + (data.temp || '--') + '°C</p>' +
                               '<p>湿度: ' + (data.humidity || '--') + '%</p>';
            } catch (e) {
                el.textContent = '加载失败: ' + e.message;
            }
        }
    ''',
    loader="loadWeatherView",
    group="group_tools",
)
```

### モード2：iframe 埋め込み

モジュールが独自の HTML ページの URL（ルートの登録が必要）を提供し、Dashboard はそれを iframe で埋め込みます。完全に独立した UI や複雑なインタラクションが必要なシナリオに適しています。

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="数据可视化", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> iframe モードでは、認証のために URL の後に `token` パラメータが自動的に追加されます。

---

## サイドバーのグループ

モジュールは View が属するサイドバーのグループを指定できます。Dashboard には以下の組み込みグループがあります：

| グループ識別子 | 中国語名 | 場所 |
|---------|--------|------|
| `group_overview` | 概览 | 第1グループ |
| `group_events` | 事件 | 第2グループ |
| `group_extensions` | 扩展 | 第3グループ（デフォルト） |
| `group_system` | 系统 | 第4グループ |
| `group_tools` | 工具 | 第5グループ |

組み込みグループ名を指定すると、モジュールの View はそのグループの末尾に追加されます：

```python
group="group_tools"  # "工具" グループに追加
```

カスタムグループ名（`group_` で始まらないもの）を使用することもでき、Dashboard は自動的に新しいグループを作成します：

```python
group="my_group",
group_title="我的分组",
group_title_en="My Group",
```

---

## よく使用される CSS クラス名

モジュール View で HTML 注入モードを使用する場合、視覚的な一貫性を保つために Dashboard で既に定義されている CSS クラス名を直接使用できます：

| クラス名 | 用途 |
|------|------|
| `page-title` | ページタイトル（例：`<h1 class="page-title">タイトル</h1>`） |
| `card` | カードコンテナ |
| `card-header` | カードタイトルバー |
| `card-body` | カードコンテンツエリア |
| `grid-2` | 2列のグリッドレイアウト |
| `grid-3` | 3列のグリッドレイアウト |
| `btn` | 基本ボタン |
| `btn-primary` | メインボタン（青色） |
| `btn-secondary` | 準拠ボタン |
| `btn-icon` | アイコンボタン |
| `btn-danger` | 危険操作ボタン |

Dashboard は CSS 変数を使用してテーマカラーを制御するため、モジュール View で直接それらを参照できます：

| CSS 変数 | 用途 |
|----------|------|
| `var(--bg-p)` | メイン背景色 |
| `var(--bg-s)` | 準拠背景色 |
| `var(--bg-t)` | 3次背景色（カードなど） |
| `var(--tx-p)` | メインテキスト色 |
| `var(--tx-s)` | 準拠テキスト色 |
| `var(--tx-t)` | 補助テキスト色 |
| `var(--bd)` | ボーダー色 |
| `var(--accent)` | アクセント色 |
| `var(--ok-c)` | 成功色 |
| `var(--er-c)` | エラー色 |

これらの変数は、Dashboard のライト/ダークテーマに基づいて自動的に切り替わるため、モジュール側で追加の処理は不要です。

---

## 認証と API 呼び出し

モジュール View の JS でモジュール自身の API を呼び出す場合、認証のために Dashboard の Token を保持する必要があります：

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

モジュールの API エンドポイントは、Token の検証を行うかどうかを独自に決定できます。検証が必要な場合は、リクエストヘッダーから抽出できます：

```python
from fastapi.responses import JSONResponse

async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return JSONResponse({"data": "hello"})
```

---

## 完全なモジュールの例

以下は、View の登録、API データの提供、アンインストール時のリソースクリーンアップ方法を示す完全な天気モジュールの例です：

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command


class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("Weather")
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(lazy_load=False, priority=50)

    async def on_load(self, event):
        self._register_routes()
        self._register_dashboard_view()
        self.logger.info("天气模块已加载")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("天气模块已卸载")

    def _load_config(self):
        config = self.sdk.config.getConfig("Weather")
        if not config:
            default = {"city": "北京", "api_key": ""}
            self.sdk.config.setConfig("Weather", default)
            return default
        return config

    def _register_routes(self):
        r = self.sdk.router
        r.register_http_route("Weather", "/api/current",
                              handler=self._api_current, methods=["GET"])

    def _unregister_routes(self):
        r = self.sdk.router
        try:
            r.unregister_http_route("Weather", "/api/current")
        except Exception:
            pass

    async def _api_current(self, request):
        from fastapi.responses import JSONResponse
        return JSONResponse({
            "city": self.config.get("city", "北京"),
            "temp": 25,
            "humidity": 60,
        })

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="天气", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">天气查询</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">查看当前天气信息</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">当前天气</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">点击刷新加载</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">操作</div>
                            <div class="card-body">
                                <button class="btn btn-primary" onclick="refreshWeather()">刷新</button>
                            </div>
                        </div>
                    </div>
                ''',
                js_content='''
                    async function loadWeatherView() { await refreshWeather(); }
                    async function refreshWeather() {
                        var el = document.getElementById('weather-info');
                        if (!el) return;
                        el.textContent = '加载中...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>城市: ' + (data.city || '--') + '</p>' +
                                           '<p>温度: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>湿度: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = '加载失败: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"登録 Dashboard View 失敗: {e}")
```

---

## View の登録解除

モジュールをアンインストールする際は、`unregister_view()` を呼び出して登録済みの View をクリーンアップする必要があります：

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

登録解除後、Dashboard フロントエンドは WebSocket を介してサイドバーのナビゲーション項目とページコンテンツをリアルタイムで削除するため、ユーザーがページをリフレッシュする必要はありません。

---

## 注意事項

1. **読み込み順序** — Dashboard の読み込み優先度は `99999`（高優先度）です。モジュールの優先度はこれより低い値（例：`50`）である必要があり、Dashboard が先に読み込まれるようにします
2. **防御的プログラミング** — `try/except` で登録を囲むことを行う必要があります。これは、Dashboard モジュールが未インストールや未読み込みである可能性があるためです
3. **リソースクリーンアップ** — `on_unload` で `unregister_view()` を呼び出して登録済みの View を削除してください
4. **ID の一意性** — `id` パラメータは Dashboard 全体で一意である必要があり、モジュール名を直接使用することを推奨します
5. **SVG アイコン** — `icon_svg` は完全な `<svg>` タグである必要があります。サイズには `viewBox="0 0 24 24"` を使用し、Dashboard のテーマカラーを継承するために `stroke="currentColor"` を使用することを推奨します
6. **JS 関数名** — `js_content` 内の関数名は一意である必要があります（例：`loadWeatherView`）。他のモジュールとの競合を避けるためです
7. **動的更新** — モジュールで View を登録/解除した後、Dashboard フロントエンドは WebSocket を介してサイドバーをリアルタイムで更新するため、ページのリフレッシュは不要です



====
技术标准
====


### 会话类型标准

# ErisPulse セッション型標準

本ドキュメントでは、ErisPulse がサポートするセッション型標準を定義しています。これには、イベントを受信するための受信型（Receive Type）と、メッセージを送信するための送信先型（Send Type）が含まれます。

## 1. コアコンセプト

### 1.1 受信型 && 送信型

ErisPulse は 2 種類のセッション型を区別します。

- **受信型（Receive Type）**：イベントを受信する際の `detail_type` フィールド
- **送信型（Send Type）**：メッセージを送信する際の `Send.To()` メソッドのターゲット型

### 1.2 型マッピング関係

```
受信型 (detail_type)       送信型 (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**重要ポイント**：
- `private` は受信時の型であり、送信時には `user` を使用する必要があります
- `group`、`channel`、`guild`、`thread` は受信時と送信時で型は同じです
- システムは自動的に型変換を行うため、手動で処理する必要はありません（受け取った受信型をそのまま送信に使用できることを意味します）。実際には、これらのこと心配する必要はありません。イベントのラッパークラスが存在するため、`event.reply()` メソッドを直接使用でき、型変換について考える必要はありません

## 2. 標準セッション型

### 2.1 OneBot12 標準型

#### private
- **受信型**：`private`
- **送信型**：`user`
- **説明**：1対1のプライベートチャットメッセージ
- **ID フィールド**：`user_id`
- **対象プラットフォーム**：プライベートチャットをサポートするすべてのプラットフォーム

#### group
- **受信型**：`group`
- **送信型**：`group`
- **説明**：グループチャットメッセージ。さまざまな形式のグループ（例：Telegram スーパー群体）を含みます
- **ID フィールド**：`group_id`
- **対象プラットフォーム**：グループチャットをサポートするすべてのプラットフォーム

#### user
- **受信型**：`user`
- **送信型**：`user`
- **説明**：ユーザータイプ。一部のプラットフォーム（例：Telegram）はプライベートチャットを private ではなく user として表現します
- **ID フィールド**：`user_id`
- **対象プラットフォーム**：Telegram などのプラットフォーム

### 2.2 ErisPulse 拡張型

#### channel
- **受信型**：`channel`
- **送信型**：`channel`
- **説明**：チャンネルメッセージ。複数のユーザーへのブロードキャストメッセージをサポート
- **ID フィールド**：`channel_id`
- **対象プラットフォーム**：Discord, Telegram, Line など

#### guild
- **受信型**：`guild`
- **送信型**：`guild`
- **説明**：サーバー/コミュニティメッセージ。通常は Discord Guild レベルのイベントで使用されます
- **ID フィールド**：`guild_id`
- **対象プラットフォーム**：Discord など

#### thread
- **受信型**：`thread`
- **送信型**：`thread`
- **説明**：スレッド/サブチャンネルメッセージ。コミュニティ内のサブディスカッションエリアで使用されます
- **ID フィールド**：`thread_id`
- **対象プラットフォーム**：Discord Threads, Telegram Topics など

## 3. プラットフォーム型マッピング

### 3.1 マッピング原則

アダプターは、プラットフォームのネイティブ型を ErisPulse 標準型にマッピングする責任を負います。

```
プラットフォームネイティブ型 → ErisPulse 標準型 → 送信型
```

### 3.2 一般的なプラットフォームマッピング例

#### Telegram
```
Telegram 型              ErisPulse 受信型      送信型
─────────────────        ────────────────       ───────────
private                private                 user
group                  group                   group  # group にマッピング
supergroup             group                   group
channel                channel                 channel
```

#### Discord
```
Discord 型              ErisPulse 受信型      送信型
─────────────────        ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
OneBot11 型          ErisPulse 受信型      送信型
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # group にマッピング
```

## 4. カスタム型拡張

### 4.1 カスタム型の登録

アダプターはカスタムセッション型を登録できます：

```python
from ErisPulse.Core.Event import register_custom_type

# カスタム型を登録
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 カスタム型の使用

登録後、システムはその型の変換と推論を自動的に処理します：

```python
# 自動推論
receive_type = infer_receive_type(event, platform="MyPlatform")
# 返回: "my_custom_type"

# 送信型へ変換
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# 返回: "custom"

# 対応するIDを取得
target_id = get_target_id(event, platform="MyPlatform")
# 返回: event["custom_id"]
```

### 4.3 カスタム型の解除

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. 自動型推論

イベントに明確な `detail_type` フィールドがない場合、システムは存在する ID フィールドに基づいて型を自動的に推論します：

### 5.1 推論優先順位

```
優先順位（高い順）：
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 使用例

```python
# イベントには group_id のみがある場合
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# 返回: "group"（group_id が優先されるため）

# イベントには user_id のみがある場合
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# 返回: "private"
```

## 6. API 使用例

### 6.1 メッセージの送信

```python
from ErisPulse import adapter

# ユーザーに送信
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# グループに送信
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# 自動変換 private → user（推奨されません。互換性の問題が発生する可能性があります）
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# 内部で自動的に変換されます: Send.To("user", "789") # userをセッション型として直接使用する方がより良い選択です
```

### 6.2 イベントへの返信

```python
from ErisPulse.Core.Event import Event

# Event.reply() は型変換を自動的に処理します
await event.reply("返信内容")
# 内部で適切な送信型が自動的に使用されます
```

### 6.3 コマンドの処理

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # システムはセッション型を自動的に処理します
    # 手動で group_id か user_id を判断する必要はありません
    await event.reply("コマンド実行成功")
```

## 7. ベストプラクティス

### 7.1 アダプター開発者向け

1. **標準マッピングの使用**：可能な限り標準型にマッピングし、新しい型を作成しない
2. **正確な変換**：受信型と送信型のマッピング関係が正しいことを確認する
3. **生データの保持**：`{platform}_raw` に元のイベント型を保持する
4. **ドキュメント化**：アダプタードキュメントに型マッピング関係を説明する

### 7.2 モジュール開発者向け

1. **ツールメソッドの使用**：`get_send_type_and_target_id()` などのツールメソッドを使用する
2. **ハードコーディングの回避**：`if group_id else "private"` のようなコードを書かない
3. **すべての型のサポート**：コードはすべての標準型（private/group だけでなく）をサポートする
4. **柔軟な設計**：イベントラッパーのメソッドを使用し、フィールドに直接アクセスしない

### 7.3 型推論

- **detail_type の優先使用**：明確なフィールドがある場合は、推論を行わない
- **推論の適切な使用**：明確な型がない場合のみ使用する
- **優先順位の認識**：推論の優先順位を理解し、意図しない結果を避ける

## 8. よくある質問（FAQ）

### Q1: なぜ送信時に private を user に変換する必要があるのですか？

A: これは OneBot12 標準の要件です。`private` は受信時の概念であり、送信時には `user` を使用する方がより適切な意味合いになります。

### Q2: 新しいセッション型をどのようにサポートしますか？

A: `register_custom_type()` を使用してカスタム型を登録するか、あるいは標準型（`channel`、`guild` など）を直接使用します。

### Q3: イベントに detail_type がない場合はどうしますか？

A: システムは存在する ID フィールドに基づいて自動的に推論します。優先順位は：group > channel > guild > thread > user です。

### Q4: アダプターは Telegram supergroup をどのようにマッピングしますか？

A: アダプターの変換ロジック内で、`supergroup` を標準の `group` 型にマッピングします。

### Q5: メールなどの特殊なプラットフォームはどう処理しますか？

A: 一般的なものやプラットフォーム固有の型については、`{platform}_raw` と `{platform}_raw_type` を使用して生データを保持し、アダプター側で処理します。

## 9. 関連ドキュメント

- [イベント変換標準](event-conversion.md) - 完全なイベント変換仕様
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名とパラメータ仕様
- [アダプター開発ガイド](../developer-guide/adapters/) - アダプター開発の完全ガイド



### 事件转换标准

# アダプター標準化変換仕様

## 1. コア原則
1. 厳密な互換性：すべての標準フィールドはOneBot12仕様に完全に従う必要があります
2. 明確な拡張：プラットフォーム固有の機能には {platform}_ プレフィックスを追加する必要があります（例：yunhu_form）
3. データの完全性：元のイベントデータは {platform}_raw フィールドに保持し、元のイベントタイプは {platform}_raw_type フィールドに保持する必要があります
4. 時間の統一：すべてのタイムスタンプは10桁のUnixタイムスタンプ（秒単位）に変換する必要があります
5. プラットフォームの統一：platform項目の命名は、ErisPulseで登録した名前/エイリアスと一致する必要があります

## 2. 標準フィールド要件

### 2.1 必須フィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| id | string | イベント固有識別子 |
| time | integer | Unixタイムスタンプ（秒単位） |
| type | string | イベントタイプ |
| detail_type | string | イベント詳細タイプ（詳細は[セッションタイプ標準](session-types.md)を参照） |
| platform | string | プラットフォーム名 |
| self | object | ボット自身の情報 |
| self.platform | string | プラットフォーム名 |
| self.user_id | string | ボットのユーザーID |

**detail_type 仕様**：
- ErisPulse標準のセッションタイプを使用する必要があります（詳細は[セッションタイプ標準](session-types.md)を参照）
- サポートされるタイプ：`private`, `group`, `user`, `channel`, `guild`, `thread`
- アダプターはプラットフォームのネイティブタイプを標準タイプにマッピングする責任があります

### 2.2 メッセージイベントフィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| message | array | メッセージセグメント配列 |
| alt_message | string | メッセージセグメントの代替テキスト |
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーニックネーム（任意） |

### 2.3 通知イベントフィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーニックネーム（任意） |
| operator_id | string | 操作者ID（任意） |

### 2.4 リクエストイベントフィールド
| フィールド | タイプ | 説明 |
|------|------|------|
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーニックネーム（任意） |
| comment | string | リクエストの付言（任意） |
| request_id | string | リクエスト識別子（**強く推奨**、リクエストの承認/拒否操作に使用） |

**`request_id` フィールドの説明**：
- `request_id` はリクエストイベントの固有の操作識別子であり、`HandleRequest` DSLを通じて承認/拒否操作を実行するために使用されます
- アダプターは、リクエストイベントを変換する際に、プラットフォームのネイティブなリクエスト識別子をこのフィールドにマッピングする必要があります
- プラットフォーム自体にリクエストIDがない場合、アダプターは固有の識別子を生成する必要があります（例：タイムスタンプ+ユーザーIDに基づくハッシュなど）
- `request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローします

## 3. イベントフォーマット例

### 3.1 メッセージイベント
```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽選 スーパープライズ"
      }
    }
  ],
  "alt_message": "抽選 スーパープライズ",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽選",
    "args": "スーパープライズ"
  }
}
```

### 3.2 通知イベント
```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 リクエストイベント
```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "フレンド追加してください",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. メッセージセグメント標準

### 4.1 標準メッセージセグメント

標準メッセージセグメントタイプにはプラットフォームプレフィックスを**追加しません**：

| タイプ | 説明 | data フィールド |
|------|------|----------|
| `text` | プレーンテキスト | `text: str` |
| `image` | 画像 | `file: str/bytes`, `url: str` |
| `audio` | 音声 | `file: str/bytes`, `url: str` |
| `video` | 動画 | `file: str/bytes`, `url: str` |
| `file` | ファイル | `file: str/bytes`, `url: str`, `filename: str` |
| `mention` | @ユーザー | `user_id: str`, `user_name: str` |
| `reply` | 返信 | `message_id: str` |
| `face` | 絵文字 | `id: str` |
| `location` | 位置情報 | `latitude: float`, `longitude: float` |

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.2 プラットフォーム拡張メッセージセグメント

プラットフォーム固有のメッセージセグメントにはプラットフォームプレフィックスを追加する必要があります：

```json
// Yunhu - フォーム
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "申込フォーム"}}

// Telegram - ステッカー
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**拡張メッセージセグメント要件**：
1. **data内部のフィールドにはプレフィックスを付けない**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` とし、`{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}` とはしない
2. **フォールバック手段の提供**：モジュールが拡張メッセージセグメントを認識できない可能性があるため、アダプターは `alt_message` でテキストの代替を提供する必要があります
3. **ドキュメントの完全性**：各拡張メッセージセグメントについて、アダプターのドキュメントで `type`、`data` 構造、使用シナリオを説明する必要があります

## 5. 未知のイベント処理

認識できないイベントタイプの場合、警告イベントを生成する必要があります：
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```

---

## 6. 拡張命名規則

### 6.1 フィールド命名

**ルール**：`{platform}_{field_name}`

```
プラットフォームプレフィックス    フィールド名            完全なフィールド名
────────                        ───────                 ──────────
yunhu                           command                 yunhu_command
telegram                        sticker_file_id         telegram_sticker_file_id
onebot11                        anonymous               onebot11_anonymous
email                           subject                 email_subject
```

**要件**：
- `platform` はアダプター登録時のプラットフォーム名と完全に一致する必要があります（大文字小文字を区別）
- `field_name` は `snake_case` で命名します
- 二重アンダースコア `__` で始まる名前は禁止されています（Python予約済み）
- 標準フィールドと同名（`type`、`time`、`message` など）は禁止されています

### 6.2 メッセージセグメントタイプの命名

**ルール**：`{platform}_{segment_type}`

標準メッセージセグメントタイプ（`text`、`image`、`audio`、`video`、`mention`、`reply` など）にはプラットフォームプレフィックスを追加**してはいけません**。プラットフォーム固有のメッセージセグメントタイプのみプレフィックスを追加する必要があります。

### 6.3 生データフィールドの命名

以下のフィールド名は**予約フィールド**であり、すべてのアダプターが従う必要があります：

| 予約フィールド | タイプ | 説明 |
|---------|------|------|
| `{platform}_raw` | `any` | プラットフォームの元のイベントデータの完全なコピー |
| `{platform}_raw_type` | `string` | プラットフォームの元のイベントタイプ識別子 |

**要件**：
- `{platform}_raw` は元のデータのディープコピーである必要があり、参照ではありません
- `{platform}_raw_type` は文字列である必要があり、プラットフォームが数値型を使用している場合でも文字列に変換する必要があります
- これら2つのフィールドはすべてのイベントに**必ず存在する**必要があります（取得できない場合は `null` と空文字列 `""`）

### 6.4 プラットフォーム固有フィールドの例

```json
{
  "yunhu_command": {
    "name": "抽選",
    "args": "スーパープライズ"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 ネストされた拡張フィールド

拡張フィールドは単純な値にすることも、ネストされたオブジェクトにすることもできます：

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**ネストされたフィールドの要件**：
- トップレベルのキーにはプラットフォームプレフィックスを付ける必要があります
- ネストされた内部フィールドにはプラットフォームプレフィックスを**追加しません**
- ネストの深さは3レベルを超えないことを推奨します

### 6.6 `self` フィールドの拡張

`self` オブジェクトの標準必須フィールド（`platform`、`user_id`）については §2.1 を参照してください。以下はErisPulse拡張の任意フィールドです：

| フィールド | タイプ | 説明 |
|------|------|------|
| `self.user_name` | `string` | ボットのニックネーム |
| `self.avatar` | `string` | ボットのアバターURL |
| `self.account_id` | `string` | マルチアカウントモードでのアカウント識別子 |

> **Botステータス追跡**：アダプターは `type: "meta"` イベントを送信することで、フレームワークにBotの接続ステータスを通知します。サポートされる `detail_type`：`connect`（オンライン）、`heartbeat`（ハートビート）、`disconnect`（オフライン）。システムは自動的に `self` フィールドからBotのメタ情報を抽出してステータスを追跡します。さらに、通常のイベント内の `self` フィールドからもBotが自動的に検出されます。詳細は[アダプターシステムAPI - Botステータス管理](../api-reference/adapter-system.md)を参照してください。

---

## 7. セッションタイプの拡張

ErisPulseは、OneBot12標準の `private`、`group` に基づいて、以下のセッションタイプを拡張しています：

| タイプ | OneBot12 標準 | ErisPulse 拡張 | 説明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 1対1プライベートチャット |
| `group` | ✅ | — | グループチャット |
| `user` | — | ✅ | ユーザータイプ（Telegramなど） |
| `channel` | — | ✅ | チャンネル（ブロードキャスト形式） |
| `guild` | — | ✅ | サーバー/コミュニティ |
| `thread` | — | ✅ | トピック/サブチャンネル |

**アダプターのカスタムタイプ拡張**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# アダプター起動時に登録
register_custom_type(
    receive_type="email",      # 受信イベントの detail_type
    send_type="email",         # 送信時のターゲットタイプ
    id_field="email_id",       # 対応する ID フィールド名
    platform="email"           # プラットフォーム識別子
)
```

**カスタムタイプの要件**：
- アダプターの `start()` 時に登録し、`shutdown()` 時に登録解除する必要があります
- `receive_type` は標準タイプと重複する名前にしないでください
- `id_field` は `{ターゲット}_id` の命名パターンに従う必要があります

> 完全なセッションタイプの定義とマッピング関係については、[セッションタイプ標準](session-types.md)を参照してください。

---

## 8. モジュール開発者ガイド

### 8.1 拡張フィールドへのアクセス

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # 標準フィールドへのアクセス
    text = event.get_text()
    user_id = event.get_user_id()

    # プラットフォーム拡張フィールドへのアクセス - 方法1：直接 get
    yunhu_command = event.get("yunhu_command")

    # プラットフォーム拡張フィールドへのアクセス - 方法2：ドット記法アクセス（Event ラッパークラス）
    # event.yunhu_command

    # 生データへのアクセス
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # プラットフォームの判定
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 拡張メッセージセグメントの処理

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 ベストプラクティス

1. **標準フィールドを優先して使用**：拡張フィールドが常に存在すると仮定しないでください
2. **プラットフォームの判定**：拡張フィールドの有無から推測するのではなく、`event.get_platform()` を通じてプラットフォームを判定してください
3. **優雅なフォールバック**：拡張メッセージセグメントを処理できない場合は、`alt_message` をフォールバックとして使用してください
4. **プレフィックスのハードコーディングを避ける**：`platform` 変数を使用して動的に結合してください

```python
# ✅ 推奨
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 非推奨
raw_data = event.get("yunhu_raw")
```

### 8.4 リクエストイベントの処理

モジュール開発者は、`event.approve()` と `event.reject()` を使用してリクエストイベントを操作できます：

```python
from ErisPulse.Core.Event import request

# フレンドリクエスト：自動承認
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # リクエストを承認
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"{user_name} のフレンドリクエストを承認しました")
    else:
        print(f"フレンドリクエストの承認に失敗しました: {result.get('message')}")

# グループ招待：条件に基づいて決定
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # リクエストを拒否
    result = await event.reject(comment="現在新しいグループには参加していません")
```

**アダプターを通じた直接操作**（非イベントハンドラーシナリオに適用）：

```python
from ErisPulse import adapter

# request_id を通じた直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Botアカウントを指定した操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# 備考を添付
await adapter.myplatform.Request("req_abc123").accept(comment="ようこそ")
```

---

## 9. 関連ドキュメント

- [各プラットフォーム特性ドキュメント](../platform-guide/README.md) - 各プラットフォームの特性、既知の拡張イベント、メッセージセグメントなどを理解するためにアクセスできます。
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係
- [送信メソッド仕様](send-method-spec.md) - Sendクラスのメソッド命名、パラメータ仕様、および逆変換要件
- [APIレスポンス標準](api-response.md) - アダプターAPIレスポンスフォーマット標準



### API 响应标准

# ErisPulse アダプター標準化戻り値仕様書

## 1. 説明
この仕様書が存在する理由

各プラットフォームが送信するインターフェースの戻り値の一貫性とOneBot12との互換性を確保するため、ErisPulseアダプターはAPI応答フォーマットにおいてOneBot12定義のメッセージ送信戻り構造標準を採用しています。

しかし、ErisPulseのプロトコルにはいくつかの特殊性定義があります:
- 1. 基本フィールドにおいて、`message_id`は必須ですが、OneBot12標準にはこのフィールドはありません
- 2. 戻り値には `{platform_name}_raw` フィールドを追加する必要があります。これは元の応答データを格納するために使用します

## 2. 基本戻り構造
すべてのアクション応答には、以下の基本フィールドを含める必要があります：

| フィールド名 | データ型 | 必須 | 説明 |
|-------|---------|------|------|
| status | string | Yes | 実行状態。"ok" または "failed" である必要があります |
| retcode | int64 | Yes | 戻り値コード。OneBot12の戻り値規則に従います |
| data | any | Yes | 応答データ。成功時はリクエスト結果を含みます。失敗時は null です |
| message_id | string | Yes | メッセージID。メッセージを識別するために使用します。ない場合は空文字です |
| message | string | Yes | エラーメッセージ。成功時は空文字です |
| {platform_name}_raw | any | No | 元の応答データ |

オプションフィールド：
| フィールド名 | データ型 | 必須 | 説明 |
|-------|---------|------|------|
| echo | string | No | リクエストに echo フィールドが含まれている場合、そのまま返します |

## 3. 完全フィールド仕様

### 3.1 通用フィールド

#### 成功応答例
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": "1234",
        "time": 1632847927.599013
    },
    "message_id": "1234",
    "message": "",
    "echo": "1234",
    "telegram_raw": {...}
}
```

#### 失敗応答例
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "必要なパラメータが不足しています: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 戻り値コード仕様

#### 0 成功（OK）
- 0: 成功（OK）

#### 1xxxx アクションリクエストエラー（Request Error）
| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 10001 | Bad Request | 無効なアクションリクエスト |
| 10002 | Unsupported Action | サポートされていないアクションリクエスト |
| 10003 | Bad Param | 無効なアクションリクエストパラメータ |
| 10004 | Unsupported Param | サポートされていないアクションリクエストパラメータ |
| 10005 | Unsupported Segment | サポートされていないメッセージセグメントタイプ |
| 10006 | Bad Segment Data | 無効なメッセージセグメントパラメータ |
| 10007 | Unsupported Segment Data | サポートされていないメッセージセグメントパラメータ |
| 10101 | Who Am I | ロボットアカウントが指定されていません |
| 10102 | Unknown Self | 未知のロボットアカウント |

#### 2xxxx アクションハンドラー エラー（Handler Error）
| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 20001 | Bad Handler | アクションハンドラー実装エラー |
| 20002 | Internal Handler Error | アクションハンドラー実行時に例外がスローされました |

#### 3xxxx アクション実行エラー（Execution Error）
| エラーコード範囲 | エラー種別 | 説明 |
|-----------|---------|------|
| 31xxx | Database Error | データベースエラー |
| 32xxx | Filesystem Error | ファイルシステムエラー |
| 33xxx | Network Error | ネットワークエラー |
| 34xxx | Platform Error | ロボットプラットフォームエラー |
| 35xxx | Logic Error | アクションロジックエラー |
| 36xxx | I Am Tired | 実装が罷業しました |

#### 予約済みエラーセグメント
- 4xxxx、5xxxx: 予約済みセグメント。使用しないでください
- 6xxxx～9xxxx: その他のエラーセグメント。実装によるカスタム使用用

## 4. 実装要件
1. すべての応答には、`status`、`retcode`、`data`、`message` フィールドを含める必要があります
2. リクエストに空ではない echo フィールドが含まれている場合、応答には同じ値を持つ echo フィールドが含まれている必要があります
3. 戻り値コードは厳密に OneBot12 規格に従う必要があります
4. エラーメッセージ（message）は、人間が読める説明である必要があります

## 5. 拡張仕様

ErisPulse は OneBot12 標準戻り構造に以下の拡張を行っています：

### 5.1 `message_id` 必須フィールド

OneBot12 標準では `message_id` は `data` オブジェクト内部且つ任意です。ErisPulse ではトップレベル**必須**フィールドとしています：

- `message_id` を取得できない場合は、空文字 `""` に設定する必要があります
- `message_id` が常に存在するようにし、モジュールによる null チェックを行う必要はありません

### 5.2 `{platform}_raw` 元の応答フィールド

戻り値には `{platform}_raw` フィールドを含め、プラットフォームの元の応答データの完全なコピーを格納する必要があります：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {"message_id": "1234", "time": 1632847927},
    "message_id": "1234",
    "message": "",
    "telegram_raw": {
        "ok": true,
        "result": {"message_id": 1234, "date": 1632847927, ...}
    }
}
```

**要件**：
- `{platform}_raw` は元の応答のディープコピー（参照ではなく値のコピー）である必要があります
- `platform` はアダプター登録時のプラットフォーム名と完全に一致している必要があります（大文字と小文字が区別されます）
- 元の応答のエラーメッセージも保持する必要があります。デバッグに役立ちます

### 5.3 アダプター実装チェックリスト

- [ ] `status`、`retcode`、`data`、`message_id`、`message` フィールドを含める
- [ ] 戻り値コードは OneBot12 規格に従う（詳細は §3.2 を参照）
- [ ] `message_id` は常に存在する（取得できない場合は空文字）
- [ ] `{platform}_raw` にプラットフォームの元の応答データを含める

## 6. 注意事項
- 3xxxx エラーコードについては、下3桁は実装が独自に定義してもよい
- 予約済みエラーセグメント（4xxxx、5xxxx）の使用は避けてください
- エラーメッセージは簡潔で明確なものである必要があり、デバッグに役立つようにしてください



### 发送方法规范

# ErisPulse 送信方法仕様書

本ドキュメントでは、ErisPulse アダプターの Send クラスにおける送信メソッドの命名規則、パラメータ仕様、およびリバース変換の要件を定義します。

## 1. 標準メソッド命名

すべての送信メソッドは **パスカルケース（PascalCase）** を使用し、最初の文字は大文字にします。

### 1.1 標準送信メソッド

| メソッド名 | 説明 | パラメータ型 |
|-------|------|---------|
| `Text` | テキストメッセージを送信 | `str` |
| `Image` | 画像を送信 | `bytes` \| `str` (URL/パス) |
| `Voice` | 音声を送信 | `bytes` \| `str` (URL/パス) |
| `Video` | 動画を送信 | `bytes` \| `str` (URL/パス) |
| `File` | ファイルを送信 | `bytes` \| `str` (URL/パス) |
| `At` | ユーザー/グループにメンション | `str` (user_id) |
| `Face` | 絵文字を送信 | `str` (emoji) |
| `Reply` | 返信メッセージ | `str` (message_id) |
| `Forward` | メッセージを転送 | `str` (message_id) |
| `Markdown` | Markdown メッセージを送信 | `str` |
| `HTML` | HTML メッセージを送信 | `str` |
| `Card` | カードメッセージを送信 | `dict` |

### 1.2 鏈式修飾子メソッド

| メソッド名 | 説明 | パラメータ型 |
|-------|------|---------|
| `At` | ユーザーにメンション（複数回呼び出し可能） | `str` (user_id) |
| `AtAll` | 全メンバーにメンション | 無し |
| `Reply` | 返信メッセージ | `str` (message_id) |

### 1.3 プロトコルメソッド

| メソッド名 | 説明 | 必須 |
|-------|------|---------|
| `Raw_ob12` | OneBot12 形式メッセージセグメントを送信 | **必須** |

**`Raw_ob12` は必須実装メソッドです。** これはアダプターのコア責務のひとつです。OneBot12 標準メッセージセグメントを受け取り、プラットフォームのネイティブ API 呼び出しに変換します。`Raw_ob12` はリバース変換（OneBot12 → プラットフォーム）の統一されたエントリポイントであり、プラットフォーム固有のメソッドに依存せず、標準メッセージセグメントを直接使用してメッセージを送信できるようにします。

**`Raw_ob12` をオーバーライドしない場合の動作**：ベースクラスのデフォルト実装では、**エラーレベル**のログを出力し、標準エラー応答形式（`status: "failed"`, `retcode: 10002`）を返します。これにより、アダプター開発者はこのメソッドを実装することを強制されます。

### 1.4 推奨される拡張命名規則

OneBot12 形式以外の生データ（プラットフォーム固有の JSON、XML など）の送信をサポートする必要があるアダプターの場合、以下の命名規則を使用することを推奨します。

| 推奨メソッド名 | 説明 |
|-----------|------|
| `Raw_json` | 任意の JSON データを送信 |
| `Raw_xml` | 任意の XML データを送信 |

**注意**：これらのメソッドはベースクラスが提供するデフォルトメソッドでは**ありません**。実装が強制されるわけでもありません。命名規則としての参考にとどまり、アダプターが必要に応じて独自に定義することができます。アダプターがこれらの形式をサポートしていない場合は、定義する必要はありません。

**メッセージビルダー（MessageBuilder）**：ErisPulse は OneBot12 メッセージセグメントリストを簡単に構築できる `MessageBuilder` ツールクラスを提供しており、`Raw_ob12` と組み合わせて使用します。詳細は [メッセージビルダー](#11-メッセージビルダーmessagebuilder) の章を参照してください。

## 2. パラメータ仕様詳細

### 2.1 メディアメッセージパラメータ仕様

メディアメッセージ（`Image`、`Voice`、`Video`、`File`）は 2 種類のパラメータタイプをサポートしています。

#### 2.1.1 文字列パラメータ（URL またはファイルパス）

**形式：** `str`

**サポートタイプ：**
- **URL**：ネットワークリソースのアドレス（例: `https://example.com/image.jpg`）
- **ファイルパス**：ローカルファイルのパス（例: `/path/to/file.jpg` または `C:\\path\\to\\file.jpg`）

**使用シーン：**
- ファイルがネットワーク上にある場合、URL を直接送信
- ファイルがローカルディスクにある場合、ファイルパスを送信
- アダプターが自動的にファイルアップロードを処理することを希望する場合

**推奨**：URL を優先し、URL が利用できない場合はローカルファイルパスを使用すること

**例：**
```python
# URLを使用する
send.Image("https://example.com/image.jpg")

# ローカルファイルパスを使用する
send.Image("/path/to/local/image.jpg")
send.Image("C:\\path\\to\\local\\image.jpg")
```

#### 2.1.2 バイナリデータパラメータ

**形式：** `bytes`

**使用シーン：**
- ファイルがメモリ上に既にある場合（例: ネットワークからダウンロード済み、他のソースから読み込み済み）
- 送信前に処理してから送信する場合（例: 画像の圧縮、形式変換）
- ファイルの重複読み取りを避ける場合

**注意事項：**
- 大きなファイルのアップロードは多くのメモリを消費する可能性があります
- 見合うファイルサイズ制限を設定することを推奨します

**例：**
```python
# ネットワークから読み込んで送信
import requests
image_data = requests.get("https://example.com/image.jpg").content
send.Image(image_data)

# ファイルから読み込んで送信
with open("/path/to/local/image.jpg", "rb") as f:
    image_data = f.read()
send.Image(image_data)
```

#### 2.1.3 パラメータ処理優先順位

アダプターがメディアメッセージパラメータを受け取った場合、以下の順序で処理すべきです。

1. **URL パラメータ**：URL を直接使用して送信（一部のプラットフォームアダプターでは URL をダウンロードしてからアップロードする操作が存在する場合があります）
2. **ファイルパス**：ローカルパスかどうかを検出し、もしそうであればファイルをアップロード
3. **バイナリデータ**：バイナリデータを直接アップロード

**アダプター実装の提案：**
```python
def Image(self, image: Union[bytes, str]):
    if isinstance(image, str):
        # URLかローカルパスかを判断する
        if image.startswith(("http://", "https://")):
            # URLは直接送信
            return self._send_image_by_url(image)
        else:
            # ローカルパスは読み込んでからアップロード
            with open(image, "rb") as f:
                return self._upload_image(f.read())
    elif isinstance(image, bytes):
        # バイナリデータは直接アップロード
        return self._upload_image(image)
```

### 2.2 @ユーザーパラメータ仕様

**メソッド：** `At`（修飾子メソッド）

**パラメータ：** `user_id` (`str`)

**要件：**
- `user_id` は文字列タイプのユーザー識別子であるべきです
- プラットフォームによって `user_id` の形式が異なる場合があります（数値、UUID、文字列など）
- アダプターは `user_id` をプラットフォーム固有の形式に変換する責任を負います
- 真の送信メソッドの呼び出しを最後の位置に置く必要があることに注意してください

**例：**
```python
# 単一のユーザーにメンション
Send.To("group", "g123").At("123456").Text("こんにちは")

# 複数のユーザーにメンション（鏈式呼び出し）
send.To("group", "g123").At("123456").At("789012").Text("皆さんこんにちは")
```

### 2.3 返信メッセージパラメータ仕様

**メソッド：** `Reply`（修飾子メソッド）

**パラメータ：** `message_id` (`str`)

**要件：**
- `message_id` は文字列タイプのメッセージ識別子であるべきです
- 以前受信したメッセージの ID であるべきです
- 一部のプラットフォームでは返信機能をサポートしていない場合がありますが、アダプターは優雅に降格（フォールバック）すべきです

**例：**
```python
send.To("group", "g123").Reply("msg_123456").Text("受信しました")
```

## 3. プラットフォーム固有メソッド命名

Send クラスに直接プラットフォーム接頭辞のメソッドを追加することは**推奨しません**。汎用的なメソッド名や `Raw_{protocol}` メソッドの使用を検討してください。

**推奨されない方法：**
```python
def YunhuForm(self, form_id: str):  # ❌ 推奨されない
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 推奨されない
    pass
```

**推奨される方法：**
```python
def Form(self, form_id: str):  # ✅ 汎用的なメソッド名
    pass

def Sticker(self, sticker_id: str):  # ✅ 汎用的なメソッド名
    pass

def Raw_ob12(self, message):  # ✅ OneBot12 形式を送信
    pass
```

**拡張メソッドの要件**：
- メソッド名はパスカルケースを使用し、プラットフォーム接頭辞をつけない
- `asyncio.Task` オブジェクトを返す必要がある
- 完全な型アノテーションとドキュメント文字列を提供する必要がある
- パラメータの設計は可能な限り標準メソッドのスタイルに一致させる

## 4. パラメータ命名規則

| パラメータ名 | 説明 | 型 |
|-------|------|------|
| `text` | テキスト内容 | `str` |
| `url` / `file` | ファイルの URL またはバイナリデータ | `str` / `bytes` |
| `user_id` | ユーザー ID | `str` / `int` |
| `group_id` | グループ ID | `str



======
平台特性指南
======


### 平台特性总览

# ErisPulse PlatformFeatures ドキュメント

> 基本プロトコル：[OneBot12](https://12.onebot.dev/) 
> 
> 本ドキュメントは**プラットフォーム固有機能ガイド**であり、以下を含みます：
> - 各アダプタがサポートするSendメソッドチェーン（連鎖呼び出し）の例
> - プラットフォーム固有のイベント/メッセージフォーマットの説明
> 
> 一般的な使用方法については以下を参照してください：
> - [基本概念](../getting-started/basic-concepts.md)
> - [イベント変換標準](../standards/event-conversion.md)  
> - [APIレスポンス仕様](../standards/api-response.md)

---

## プラットフォーム固有機能

このセクションは各アダプタ開発者がメンテナンスを行っており、そのアダプタがOneBot12標準との差異と拡張機能を説明するために使用されます。以下の各プラットフォームの詳細なドキュメントを参照してください：

- [メンテナンス説明](maintain-notes.md)

- [雲湖プラットフォーム固有機能](yunhu.md)
- [雲湖ユーザープラットフォーム固有機能](yunhu_user.md)
- [Telegramプラットフォーム固有機能](telegram.md)
- [OneBot11プラットフォーム固有機能](onebot11.md)
- [OneBot12プラットフォーム固有機能](onebot12.md)
- [メールプラットフォーム固有機能](email.md)
- [Kook(開黑啦)プラットフォーム固有機能](kook.md)
- [Matrixプラットフォーム固有機能](matrix.md)
- [QQ公式ボットプラットフォーム固有機能](qqbot.md)
- [花枫カフェ](ideaura.md)

> その他にも `sandbox` アダプタがありますが、このアダプタにはプラットフォーム固有機能のドキュメントメンテナンスは不要です。

---

## 汎用インターフェース

### Send メソッドチェーン
すべてのアダプタは以下の標準的な呼び出し方式をサポートしています：

> **注意：** ドキュメント内の `{AdapterName}` は実際のアダプタ名に置き換えてください（例：`yunhu`、`telegram`、`onebot11`、`email` など）。

1. 型とIDを指定: `To(type,id).Func()`
   ```python
   # アダプタインスタンスの取得
   my_adapter = adapter.get("{AdapterName}")
   
   # メッセージを送信
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例：
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. IDのみを指定: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例：
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 送信アカウントを指定: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例：
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼び出し: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # 例：
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### 非同期送信と結果処理

Send DSLのメソッドは `asyncio.Task` オブジェクトを返します。これは、結果を即座に待機するかどうかを選択できることを意味します：

```python
# アダプタインスタンスの取得
my_adapter = adapter.get("{AdapterName}")

# 結果を待たず、メッセージをバックグラウンドで送信
task = my_adapter.Send.To("user", "123").Text("Hello")

# 送信結果が必要な場合は、後で待機可能です
result = await task
```

### イベント監視
イベント監視方法は3種類あります：

1. プラットフォームネイティブなイベント監視：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}原生事件: {data}")
   ```

2. OneBot12標準イベント監視：
   ```python
   from ErisPulse.Core import adapter, logger

   # OneBot12標準イベントを監視
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"收到标准事件: {data}")

   # 特定プラットフォームの標準イベントを監視
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"收到{AdapterName}标准事件: {data}")
   ```

3. Eventモジュール監視：
    `Event`のイベントは `adapter.on()` 関数に基づいているため、`Event`が提供するイベントフォーマットはOneBot12標準イベントとなります。

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="发送问候消息", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"收到消息: {event}")
    async def notice_handler(event):
        logger.info(f"收到通知: {event}")
    async def request_handler(event):
        logger.info(f"收到请求: {event}")
    async def command_handler(event):
        logger.info(f"收到命令: {event}")
    ```

中でも最も推奨されるのは `Event` モジュールを使用したイベント処理です。これは `Event` モジュールが豊富なイベントタイプと豊富なイベント処理メソッドを提供するためです。

---

## 標準フォーマット
参照しやすいよう、ここでは簡単なイベントフォーマットを示します。詳細が必要な場合は、上のリンクを参照してください。

> **注意：** 以下のフォーマットは基本的なOneBot12標準フォーマットです。各アダプタはこれをベースに拡張フィールドを持っている場合があります。詳細は各アダプタの固有機能の説明を参照してください。

### 標準イベントフォーマット
すべてのアダプタが実装しなければならないイベント変換フォーマット：
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "你好"}}
  ],
  "alt_message": "你好",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### 標準レスポンスフォーマット
#### メッセージ送信成功
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### メッセージ送信失敗
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "缺少必要参数",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## 参考リンク
ErisPulse プロジェクト：
- [メインリポジトリ](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu アダプタライブラリ](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram アダプタライブラリ](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot アダプタライブラリ](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

関連する公式ドキュメント：
- [OneBot V11 プロトコルドキュメント](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API 公式ドキュメント](https://core.telegram.org/bots/api)
- [雲湖公式ドキュメント](https://www.yhchat.com/document/1-3)

## 貢献の招待

私たちはより多くの開発者がアダプタドキュメントの作成とメンテナンスに参加することを歓迎します！以下の手順に従って貢献を提出してください：
1. [ErisPuls](https://github.com/ErisPulse/ErisPulse) リポジトリを Fork してください。
2. `docs/platform-features/` ディレクトリ下に Markdown ファイルを作成し、命名形式を `<プラットフォーム名>.md` としてください。
3. 本 `README.md` ファイルに、あなたが貢献したアダプタへのリンクおよび関連する公式ドキュメントを追加してください。
4. Pull Request を提出してください。

ご支援ありがとうございます！



### OneBot11 适配

# OneBot11プラットフォーム特性ドキュメント

OneBot11Adapter は OneBot V11 プロトコルに基づいて構築されたアダプターです。

---

## ドキュメント情報

- 対応モジュールバージョン: 3.6.0
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：OneBot はチャットボットアプリケーションインターフェース標準です
- アダプター名：OneBotAdapter
- サポートするプロトコル/APIバージョン：OneBot V11
- 複数アカウントサポート：デフォルトで複数アカウントアーキテクチャを採用し、複数のOneBotアカウントの同時設定と実行をサポートします
- 旧設定との互換性：旧バージョンの設定フォーマットと互換性があり、移行のリマインダーを提供します（自動移行ではありません）

## サポートするメッセージ送信タイプ

すべての送信メソッドはメソッドチェーン構文によって実装されています。例：
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# デフォルトアカウントで送信
await onebot.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを指定して送信
await onebot.Send.Using("main").To("group", group_id).Text("主アカウントからのメッセージ")

# メソッドチェーン修飾：ユーザーへのメンション + 返信
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("返信メッセージ")

# 全員へのメンション
await onebot.Send.To("group", group_id).AtAll().Text("アナウンスメッセージ")
```

### 基本送信メソッド

- `.Text(text: str)`：プレーンテキストメッセージを送信します。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像を送信します（URL、Base64、またはbytesをサポート）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：音声メッセージを送信します。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信します。
- `.Face(id: Union[str, int])`：QQのスタンプ/顔文字を送信します。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：ファイルを送信します（タイプを自動判定）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します（自動的にOB11に変換）。
- `.Recall(message_id: Union[str, int])`：メッセージを取り消します。

### メソッドチェーン修飾メソッド（組み合わせ可能）

メソッドチェーン修飾メソッドは `self` を返し、メソッドチェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.At(user_id: Union[str, int], name: str = None)`：指定したユーザーにメンションします（複数回呼び出し可能）。
- `.AtAll()`：全員にメンションします。
- `.Reply(message_id: Union[str, int])`：指定したメッセージに返信します。

### メソッドチェーン呼び出しの例

```python
# 基本送信
await onebot.Send.To("group", 123456).Text("Hello")

# 単一ユーザーにメンション
await onebot.Send.To("group", 123456).At(789012).Text("こんにちは")

# 複数ユーザーにメンション
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("皆さんこんにちは")

# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)
```

### サポートされていないタイプの処理

未定義の送信メソッドが呼び出された場合、アダプターはテキストプロンプトを返します：
```python
# 存在しないメソッドを呼び出し
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# 実際の送信: "[サポートされていない送信タイプ] メソッド名: SomeUnsupportedMethod, パラメータ: [...]"
```

## 固有のイベントタイプ

OneBot11イベントはOneBot12プロトコルに変換されます。標準フィールドはOneBot12プロトコルに完全に準拠していますが、以下の違いがあります：

### 主要な違い

1. 固有のイベントタイプ：
   - CQコード拡張イベント：onebot11_cq_{type}
   - 名誉変更イベント：onebot11_honor
   - Pokeイベント：onebot11_poke
   - 群レッドパッケージラッキーキングイベント：onebot11_lucky_king

2. 拡張フィールド：
   - すべての固有フィールドは `onebot11_` プレフィックスで識別されます
   - 元のCQコードメッセージは `onebot11_raw_message` フィールドに保持されます
   - 元のイベントデータは `onebot11_raw` フィールドに保持されます

### 特殊フィールドの例

```python
// 名誉変更イベント
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "onebot11_honor_type": "talkative",
  "onebot11_operation": "set"
}

// Pokeイベント
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678",
  "onebot11_poke_type": "normal"
}

// 群レッドパッケージラッキーキングイベント
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// CQコードメッセージセグメント
{
  "type": "message",
  "message": [
    {
      "type": "onebot11_face",
      "data": {"id": "123"}
    },
    {
      "type": "onebot11_shake",
      "data": {} 
    }
  ]
}
```

### 拡張フィールドの説明

- すべての固有フィールドは `onebot11_` プレフィックスで識別されます
- 元のCQコードメッセージは `onebot11_raw_message` フィールドに保持されます
- 元のイベントデータは `onebot11_raw` フィールドに保持されます
- メッセージ内容のCQコードは対応するメッセージセグメントに変換されます
- 返信メッセージには `reply` タイプのメッセージセグメントが追加されます
- メンション(@)メッセージには `mention` タイプのメッセージセグメントが追加されます

## 設定オプション

OneBotアダプターは各アカウントに対して以下のオプションを個別に設定します：

### アカウント設定
- `mode`: このアカウントの実行モード ("server" または "client")
- `server_path`: ServerモードでのWebSocketパス
- `server_token`: Serverモードでの認証Token（オプション）
- `client_url`: Clientモードで接続するWebSocketアドレス
- `client_token`: Clientモードでの認証Token（オプション）
- `enabled`: このアカウントを有効にするかどうか

### 内蔵デフォルト値
- 再接続間隔：30秒
- API呼び出しタイムアウト：30秒
- 最大リトライ回数：3回

### 設定例
```toml
[OneBotv11_Adapter.accounts.main]
mode = "server"
server_path = "/onebot-main"
server_token = "main_token"
enabled = true

[OneBotv11_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true

[OneBotv11_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### デフォルト設定
アカウントが設定されていない場合、アダプターは自動的に作成します：
```toml
[OneBotv11_Adapter.accounts.default]
mode = "server"
server_path = "/"
enabled = true
```

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、直接 `await` して送信結果を取得できます。戻り値はErisPulseアダプターの標準化された戻り値仕様に従います：

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // リターンコード
    "data": {...},            // レスポンスデータ
    "self": {...},            // 自身の情報
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "onebot_raw": {...}       // 元のレスポンスデータ
}
```

### 複数アカウント送信構文

```python
# アカウント選択メソッド
await onebot.Send.Using("main").To("group", 123456).Text("主アカウントメッセージ")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API呼び出し方法
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

## 非同期処理メカニズム

OneBotアダプターは非同期ノンブロッキング設計を採用し、以下を保証します：
1. メッセージ送信がイベント処理ループをブロックしないこと
2. 複数の同時送信操作が並行して行えること
3. APIレスポンスがタイムリーに処理されること
4. WebSocket接続がアクティブな状態を維持すること
5. 複数アカウントの並行処理、各アカウントが独立して実行されること

## エラー処理

アダプターは完全なエラー処理メカニズムを提供します：
1. ネットワーク接続例外の自動再接続（各アカウントの独立した再接続をサポート、間隔は30秒）
2. API呼び出しタイムアウト処理（固定30秒タイムアウト）
3. メッセージ送信失敗時のリトライ（最大3回までリトライ）

## イベント処理の強化

複数アカウントモードでは、すべてのイベントにアカウント情報が自動的に追加されます：
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "main"},  // 追加：イベントを送信したアカウントID（標準フィールド）
    "platform": "onebot11",
    // ... その他のイベントフィールド
}
```

## 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = onebot.accounts

# アカウントの接続状態を確認
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# アカウントを動的に有効化/無効化（アダプターの再起動が必要）
onebot.accounts["test"].enabled = False



### OneBot12 适配

# OneBot12プラットフォームの特徴

OneBot12Adapterは、ErisPulseフレームワークのベースラインプロトコルアダプターとして、OneBot V12プロトコルに基づいて構築されたアダプターです。

---

## ドキュメント情報

- 対応モジュールバージョン: 1.0.0
- メンテナ: ErisPulse
- プロトコルバージョン: OneBot V12

## 基本情報

- プラットフォーム概要：OneBot V12は、汎用チャットボットアプリケーションインターフェース標準であり、ErisPulseフレームワークのベースラインプロトコルです。
- アダプター名：OneBot12Adapter
- サポートされるプロトコル/APIバージョン：OneBot V12
- マルチアカウント対応：完全なマルチアカウントアーキテクチャをサポートしており、複数のOneBot12アカウントを同時に設定および実行することができます。

## サポートされるメッセージ送信タイプ

すべての送信メソッドはチェーン構文（メソッドチェーン）で実装されています。例：

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# デフォルトのアカウントで送信
await onebot12.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを指定して送信
await onebot12.Send.To("group", group_id).Account("main").Text("来自主账户的消息")
```

### 基本メッセージタイプ

- `.Text(text: str)`：純テキストメッセージを送信
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像メッセージを送信（URL、Base64、またはbytesをサポート）
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`：音声メッセージを送信
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信

### インタラクションメッセージタイプ

- `.Mention(user_id: Union[str, int], user_name: str = None)`：メンション（@メッセージ）を送信
- `.Reply(message_id: Union[str, int], content: str = None)`：返信メッセージを送信
- `.Sticker(file_id: str)`：ステッカー/絵文字を送信
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`：位置情報を送信

### 管理機能

- `.Recall(message_id: Union[str, int])`：メッセージを撤回
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`：メッセージを編集
- `.Raw(message_segments: List[Dict])`：ネイティブなOneBot12メッセージセグメントを送信
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`：メッセージを一括送信

## OneBot12標準イベント

OneBot12アダプターはOneBot12標準を完全に準拠しており、イベント形式の変換は不要で、そのままフレームワークに送信されます。

### メッセージイベント (Message Events)

```python
# プライベートメッセージ
{
    "id": "event-id",
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}

# グループメッセージ
{
    "id": "event-id",
    "type": "message",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "group_id": "group-id",
    "message": [{"type": "text", "data": {"text": "Hello group"}}],
    "alt_message": "Hello group",
    "time": 1234567890
}
```

### 通知イベント (Notice Events)

```python
# グループメンバー増加
{
    "id": "event-id",
    "type": "notice",
    "detail_type": "group_member_increase",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "approve",
    "time": 1234567890
}

# グループメンバー減少
{
    "id": "event-id",
    "type": "notice", 
    "detail_type": "group_member_decrease",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "leave",
    "time": 1234567890
}
```

### リクエストイベント (Request Events)

```python
# フレンドリクエスト
{
    "id": "event-id",
    "type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "申請メッセージ",
    "flag": "request-flag",
    "time": 1234567890
}

# グループ招待リクエスト
{
    "id": "event-id",
    "type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "申請メッセージ",
    "flag": "request-flag",
    "sub_type": "invite",
    "time": 1234567890
}
```

### メタイベント (Meta Events)

```python
# ライフサイクルイベント
{
    "id": "event-id",
    "type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# ハートビートイベント
{
    "id": "event-id",
    "type": "meta_event",
    "detail_type": "heartbeat",
    "self": {"user_id": "bot-id"},
    "interval": 5000,
    "status": {"online": true},
    "time": 1234567890
}
```

## 設定オプション

### アカウント設定

各アカウントは以下のオプションを独立して設定できます：

- `mode`: このアカウントの実行モード（"server" または "client"）
- `server_path`: Serverモード時のWebSocketパス
- `server_token`: Serverモード時の認証トークン（オプション）
- `client_url`: Clientモード時に接続するWebSocketアドレス
- `client_token`: Clientモード時の認証トークン（オプション）
- `enabled`: このアカウントを有効にするか
- `platform`: プラットフォーム識別子（デフォルトは "onebot12"）
- `implementation`: 実装識別子（例: "go-cqhttp"、オプション）

### 設定例

```toml
[OneBotv12_Adapter.accounts.main]
mode = "server"
server_path = "/onebot12-main"
server_token = "main_token"
enabled = true
platform = "onebot12"
implementation = "go-cqhttp"

[OneBotv12_Adapter.accounts.backup]
mode = "client"
client_url = "ws://127.0.0.1:3002"
client_token = "backup_token"
enabled = true
platform = "onebot12"
implementation = "shinonome"

[OneBotv12_Adapter.accounts.test]
mode = "client"
client_url = "ws://127.0.0.1:3003"
enabled = false
```

### デフォルト設定

アカウントが何も設定されていない場合、アダプターは自動的に以下を作成します：

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、そのままawaitして送信結果を取得できます。戻り値はOneBot12標準に準拠しています：

```python
{
    "status": "ok",           // 実行状態
    "retcode": 0,             // リターンコード
    "data": {...},            // レスポンスデータ
    "self": {"user_id": "account-id"},  // アカウント情報
    "message_id": "123456",   // メッセージID
    "message": ""             // エラーメッセージ
}
```

### マルチアカウント送信構文

```python
# アカウント選択メソッド
await onebot12.Send.Using("main").To("group", 123456).Text("主アカウントのメッセージ")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API呼び出し方式
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## 非同期処理メカニズム

OneBot12アダプターは非同期かつ非ブロッキング設計を採用しています：

1. メッセージ送信はイベント処理ループをブロックしません
2. 複数の並行送信操作を同時に行うことができます
3. API応答をタイムリーに処理できます
4. WebSocket接続は常にアクティブな状態を維持します
5. マルチアカウントの並行処理を行い、各アカウントは独立して動作します

## エラーハンドリング

アダプターは包括的なエラーハンドリングメカニズムを提供します：

1. ネットワーク接続の異常は自動的に再接続します（各アカウントごとに独立して再接続、間隔30秒）
2. API呼び出しのタイムアウト処理（固定30秒のタイムアウト）
3. メッセージ送信の失敗は自動的に再試行します（最大3回）

## イベント処理の強化

マルチアカウントモードでは、すべてのイベントにアカウント情報が自動的に追加されます：

```python
{
    "type": "message",
    "detail_type": "private",
    "platform": "onebot12",
    // ... 他のイベントフィールド
}
```

## 管理インターフェース

```python
# すべてのアカウント情報の取得
accounts = onebot12.accounts

# アカウント接続状態の確認
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# 動的にアカウントの有効化/無効化（アダプターの再起動が必要）
onebot12.accounts["test"].enabled = False
```

## OneBot12標準の特徴

### メッセージセグメント標準

OneBot12は標準化されたメッセージセグメントフォーマットを使用します：

```python
# テキストメッセージセグメント
{"type": "text", "data": {"text": "Hello"}}

# 画像メッセージセグメント
{"type": "image", "data": {"file_id": "image-id"}}

# メンションメッセージセグメント
{"type": "mention", "data": {"user_id": "user-id", "user_name": "Username"}}

# 返信メッセージセグメント
{"type": "reply", "data": {"message_id": "msg-id"}}
```

### API標準

OneBot12標準API仕様に準拠しています：

- `send_message`: メッセージを送信
- `delete_message`: メッセージを削除（撤回）
- `edit_message`: メッセージを編集
- `get_message`: メッセージを取得
- `get_self_info`: 自身の情報を取得
- `get_user_info`: ユーザー情報を取得
- `get_group_info`: グループ情報を取得

## ベストプラクティス

1. **設定管理**: 複数のアカウント設定を使用することをお勧めします。異なる用途のボットを分けて管理します。
2. **エラーハンドリング**: API呼び出しのリターンステータスを常に確認します。
3. **メッセージ送信**: サポートされているメッセージタイプを適切に使用し、非対応のメッセージを送信しないようにします。
4. **接続監視**: 接続状態を定期的にチェックし、サービスの可用性を確保します。
5. **パフォーマンスの最適化**: バッチ送信時はBatchメソッドを使用して、ネットワークオーバーヘッドを減らします。



### Telegram 适配

# Telegram プラットフォーム特性ドキュメント

TelegramAdapterは、Telegram Bot APIに基づいて構築されたアダプターであり、複数のメッセージタイプとイベント処理をサポートしています。

---

## ドキュメント情報

- 対応モジュールバージョン: 3.6.5
- メンテナー: ErisPulse

## 基本情報

- プラットフォーム概要：Telegramはクロスプラットフォームのインスタントメッセージングソフトウェアです
- アダプター名：TelegramAdapter
- サポートするプロトコル/APIバージョン：Telegram Bot API
- セッションタイプのマッピング：`private` → 送信時に `user` を使用、`group`/`supergroup` → `group`、`channel` → `channel`

## サポートするメッセージ送信タイプ

すべての送信メソッドはメソッドチェーン（チェーン構文）によって実装されています。例えば以下の通りです：
```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### 基本的な送信メソッド

| メソッド | 説明 | パラメータ |
|------|------|------|
| `.Text(text)` | 純粋なテキストメッセージを送信 | `text: str` |
| `.Face(emoji)` | ダイススタンプを送信 | `emoji: str`（例：🎲 🎯 🏀） |
| `.Markdown(text, content_type)` | Markdown形式のメッセージを送信 | `content_type` のデフォルトは `"MarkdownV2"` |
| `.HTML(text)` | HTML形式のメッセージを送信 | `text: str` |
| `.Sticker(file)` | ステッカーを送信 | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng)` | 位置情報を送信 | `latitude: float, longitude: float` |
| `.Venue(lat, lng, title, addr)` | 場所を送信 | タイトルと住所を含む |
| `.Contact(phone, first, last)` | 連絡先を送信 | 電話番号と名前を含む |

### メディア送信メソッド

すべてのメディアメソッドは、`bytes`（アップロード）と `str`（file_id / URL）の2種類の入力をサポートしています：

| メソッド | 説明 |
|------|------|
| `.Image(file, caption, content_type)` | 画像を送信 |
| `.Video(file, caption, content_type)` | 動画を送信 |
| `.Voice(file, caption)` | 音声を送信 |
| `.Audio(file, caption, content_type)` | オーディオを送信 |
| `.File(file, caption)` | ファイルを送信 |
| `.Document(file, caption, content_type)` | File のエイリアス |

### メッセージ管理メソッド

| メソッド | 説明 |
|------|------|
| `.Edit(message_id, text, content_type)` | 既存のメッセージを編集 |
| `.Recall(message_id)` | 指定されたメッセージを削除 |
| `.Forward(from_chat_id, message_id)` | メッセージを転送（送信元を保持） |
| `.CopyMessage(from_chat_id, message_id)` | メッセージをコピー（送信元なし） |
| `.AnswerCallback(callback_query_id, text, show_alert)` | コールバッククエリに応答 |

### 生メッセージ送信

- `.Raw_ob12(message: List[Dict])`：OneBot12 標準形式のメッセージを送信
- `.Raw_json(json_str: str)`：生の JSON 形式のメッセージを送信

### チェーン修飾メソッド

| メソッド | 説明 |
|------|------|
| `.At(user_id)` | 指定ユーザーをメンション（Telegram entities により実現、複数回呼び出し可能） |
| `.AtAll()` | 全メンバーをメンション（`@All` テキストを送信） |
| `.Reply(message_id)` | 指定されたメッセージに返信 |
| `.Keyboard(inline_keyboard)` | インラインキーボードを設定（`list[list[dict]]`） |
| `.ProtectContent(protect)` | コンテンツを保護（転送と保存を防止） |
| `.Silent(silent)` | サイレント送信（ユーザーに通知しない） |

### 送信例

```python
# 基本的なテキスト送信
await telegram.Send.To("user", user_id).Text("Hello World!")

# インラインキーボード付きメッセージ
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "ボタン1", "callback_data": "btn1"}, {"text": "ボタン2", "callback_data": "btn2"}],
    [{"text": "公式サイトへ", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("選択してください：")

# メディア送信（URL方式）
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="画像")

# ユーザーのメンション
await telegram.Send.To("group", group_id).At("6117725680").Text("こんにちは！")

# 返信 + コンテンツの保護
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("機密メッセージ")

# サイレント送信
await telegram.Send.To("group", group_id).Silent().Text("サイレント通知")

# コールバッククエリへの応答
await telegram.Send.AnswerCallback(callback_query_id, text="処理済み", show_alert=False)

# OneBot12 複合メッセージ
ob12_message = [
    {"type": "text", "data": {"text": "複雑なメッセージ："}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "ユーザー名"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# ステッカーの送信
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id

# 位置情報の送信
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074)
```

## 固有のイベントタイプ

Telegramのイベント変換はOneBot12標準に準拠しつつ、`telegram_` プレフィックスを通じてプラットフォーム拡張を提供します。

### メッセージイベント detail_type マッピング

| Telegram chat.type | OneBot12 detail_type | 送信先タイプ |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### 固有のイベントタイプ

| detail_type | 説明 |
|---|---|
| `telegram_callback_query` | コールバッククエリ（インラインキーボードボタンのクリック） |
| `telegram_inline_query` | インラインクエリ |
| `telegram_chosen_inline_result` | 選択されたインライン結果 |
| `telegram_poll` | 投票イベント |
| `telegram_poll_answer` | 投票の回答 |
| `telegram_my_chat_member` | Bot 自身のメンバー状態の変更 |
| `telegram_chat_member` | チャットメンバーの変更 |
| `telegram_chat_join_request` | チャット参加リクエスト |
| `telegram_shipping_query` | 配送料金クエリ |
| `telegram_pre_checkout_query` | 支払前クエリ |

### 標準メッセージセグメントタイプ

変換されたメッセージセグメントはOneBot12標準形式を使用します：

| メッセージセグメントタイプ | 説明 | data フィールド |
|---|---|---|
| `text` | 純粋なテキスト（@ユーザー名を含まない） | `text` |
| `mention` | ユーザーのメンション（標準OB12） | `user_id`, `user_name` |
| `reply` | 返信引用 | `message_id`, `user_id` |
| `image` | 画像 | `file_id`, `url` |
| `video` | 動画 | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | 音声 | `file_id`, `url`, `duration` |
| `audio` | オーディオ | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | ファイル | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | 位置 | `latitude`, `longitude`, オプションで `title`, `address` |

### プラットフォーム拡張メッセージセグメント

`telegram_` プレフィックスで識別される拡張メッセージセグメント：

| メッセージセグメントタイプ | 説明 | data フィールド |
|---|---|---|
| `telegram_sticker` | ステッカー | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIFアニメーション | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | 連絡先 | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | インラインキーボード | `inline_keyboard` |

### イベント例

#### グループチャットメッセージ（メンションを含む）
```python
{
  "type": "message",
  "detail_type": "group",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "WSu2059",
  "group_id": "-1002850921906",
  "message_id": "172",
  "message": [
    {"type": "text", "data": {"text": "/it.echo "}},
    {"type": "mention", "data": {"user_id": "", "user_name": "@nm123_91178"}}
  ],
  "alt_message": "/it.echo @nm123_91178",
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### コールバッククエリイベント
```python
{
  "type": "notice",
  "detail_type": "telegram_callback_query",
  "user_id": "123456",
  "user_nickname": "YingXinche",
  "telegram_callback_id": "cb_123",
  "telegram_callback_data": "callback_data",
  "message_id": "msg_456"
}
```

#### インラインクエリイベント
```python
{
  "type": "request",
  "detail_type": "telegram_inline_query",
  "user_id": "789012",
  "user_nickname": "YingXinche",
  "telegram_query_id": "iq_789",
  "telegram_query_text": "search_text",
  "telegram_query_offset": "0"
}
```

#### インラインキーボード付きメッセージ
```python
{
  "type": "message",
  "detail_type": "group",
  "message": [
    {"type": "text", "data": {"text": "選択してください："}},
    {
      "type": "telegram_inline_keyboard",
      "data": {
        "inline_keyboard": [
          [{"text": "ボタン1", "callback_data": "btn1"}],
          [{"text": "アクセス", "url": "https://example.com"}]
        ]
      }
    }
  ]
}
```

## Event Mixin 拡張メソッド

アダプターは以下のプラットフォーム固有のメソッドを登録しており、`platform == "telegram"` の場合にのみ利用可能です：

### メッセージ関連

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `is_bot_message()` | `bool` | メッセージがボットからのものかを判定 |
| `is_edited_message()` | `bool` | 編集されたメッセージかどうかを判定 |
| `is_topic_message()` | `bool` | トピックメッセージかどうかを判定 |
| `get_update_id()` | `int` | Telegram update ID を取得 |
| `get_chat_title()` | `str` | チャットのタイトルを取得 |
| `get_chat_username()` | `str` | チャットのユーザー名を取得 |
| `get_forward_from()` | `dict` | 転送元情報を取得 |
| `get_topic_id()` | `str` | トピック ID を取得 |

### コールバッククエリ関連

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_callback_data()` | `str` | コールバッククエリの callback_data を取得 |
| `get_callback_id()` | `str` | コールバッククエリ ID を取得（応答に使用） |

### メッセージセグメントデータ抽出

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_inline_keyboard()` | `list` | メッセージ内のインラインキーボードを取得 |
| `get_sticker_info()` | `dict` | ステッカー情報を取得 |
| `get_contact_info()` | `dict` | 連絡先情報を取得 |
| `get_location()` | `dict` | 位置情報を取得 |

### 使用例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_message(event):
    if event.get("platform") != "telegram":
        return

    # メッセージ属性
    if event.is_bot_message():
        return  # ボットメッセージを無視

    if event.is_edited_message():
        print("これは編集されたメッセージです")

    # チャット情報
    title = event.get_chat_title()
    username = event.get_chat_username()

    # 転送元
    forward = event.get_forward_from()

    # メッセージセグメントデータ
    sticker = event.get_sticker_info()
    contact



### 云湖适配

# 雲湖プラットフォーム特性ドキュメント

YunhuAdapterは、雲湖プロトコルに基づいて構築されたアダプターであり、全ての雲湖機能モジュールを統合し、統一されたイベント処理とメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 3.10.1
- メンテナ: ErisPulse

## 基本情報

- プラットフォーム概要：雲湖（Yunhu）はエンタープライズレベルのIMプラットフォームです
- アダプター名：YunhuAdapter
- マルチアカウント対応：bot_id を通じて複数の雲湖ボットアカウントを識別・設定できることをサポート
- チェーン修飾子対応：`.Reply()` などのチェーン修飾子メソッドをサポート
- OneBot12互換：OneBot12形式メッセージの送信をサポート

## サポートされるメッセージ送信タイプ

全ての送信メソッドはチェーン構文（メソッドチェーン）で実装されています。例：

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：

- `.Text(text: str)`：プレーンテキストメッセージを送信します。
- `.Html(html: str)`：HTML形式メッセージを送信します。
- `.Markdown(markdown: str)`：Markdown形式メッセージを送信します。
- `.A2UI(text: str)`：A2UI形式メッセージを送信します。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`：画像メッセージを送信します。ストリーミングアップロードとカスタムファイル名に対応しています。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`：動画メッセージを送信します。ストリーミングアップロードとカスタムファイル名に対応しています。
- `.File(file: bytes, stream: bool = False, filename: str = None)`：ファイルメッセージを送信します。ストリーミングアップロードとカスタムファイル名に対応しています。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：メッセージを一括送信します。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：既存のメッセージを編集します。
- `.Recall(msg_id: str)`：メッセージを取り消します（撤回）。
- `.Board(scope: str, content: str, **kwargs)`：掲示板を公告します。scope は `local` と `global` をサポートします。
- `.DismissBoard(scope: str, **kwargs)`：公告掲示板を取り消します。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：ストリーミングメッセージを送信します。

Board の board_type は以下のタイプをサポートします：

- `local`：ユーザー専用の掲示板
- `global`：グローバル掲示板

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を表すネストされたリストです。各ボタンオブジェクトには以下のフィールドが含まれています：

| フィールド         | タイプ   | 必須 | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | ボタン上のテキスト                                                         |
| `actionType` | int    | 是       | アクションタイプ：<br>`1`: URLへジャンプ<br>`2`: コピー<br>`3`: レポート |
| `url`        | string | 否       | `actionType=1` の場合に使用、ジャンプ先の URL を示します                 |
| `value`      | string | 否       | `actionType=2` の場合、その値がクリップボードにコピーされます<br>`actionType=3` の場合、その値がサブスクライブ先に送信されます |

例：

```python
buttons = [
    [
        {"text": "复制", "actionType": 2, "value": "xxxx"},
        {"text": "点击跳转", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "汇报事件", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きメッセージ")
```

> **注意：**
> - ユーザーが**ボタンレポート（Report）イベント**のボタンをクリックした場合にのみ、プッシュ通知を受け取ります。**コピー**と**URLジャンプ**ではプッシュ通知を受け取れません。

### チェーン修飾子メソッド（組み合わせて使用可能）

チェーン修飾子メソッドは `self` を返すため、チェーン呼び出しが可能です。最終的な送信メソッドの前に呼び出す必要があります。

- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.At(user_id: str)`：指定されたユーザーにメンションします。
- `.AtAll()`：全員にメンションします。
- `.Buttons(buttons: List)`：ボタンを追加します。

### チェーン呼び出しの例

```python
# 基本的な送信
await yunhu.Send.To("user", user_id).Text("Hello")

# メッセージへの返信
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("返信とボタン付きのメッセージ")
```

### OneBot12メッセージサポート

アダプターは OneBot12 形式のメッセージ送信をサポートしており、クロスプラットフォームのメッセージ互換性を容易にします。

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式メッセージを送信します。

```python
# OneBot12 形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾子と組み合わせる
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

全ての送信メソッドは `Task` オブジェクトを返し、`await` を直接使用して送信結果を取得できます。返却結果は ErisPulse アダプターの標準化された戻り値仕様に従います。

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // 返り値コード
    "data": {...},            // レスポンスデータ
    "self": {...},            // 自身情報（bot_id を含む）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_raw": {...}        // 原始レスポンスデータ
}
```

## 固有イベントタイプ

このプラットフォームの特性を使用するには、`platform=="yunhu"` を検出する必要があります

### 核心の差異点

1. 固有イベントタイプ：
    - フォーム（フォームコマンドを含む）：yunhu_form
    - スタンプ/絵文字メッセージセグメント：yunhu_expression
    - ボタンクリック：yunhu_button_click
    - A2UIボタンクリック：yunhu_a2ui_button
    - ボット設定：yunhu_bot_setting
    - ショートカットメニュー：yunhu_shortcut_menu
2. 拡張フィールド：
    - 全ての固有フィールドは yunhu_ プレフィックスで識別されます
    - 原始データは yunhu_raw フィールドに保持されます
    - チャットプライベート (`private`) 中の self.user_id はボットIDを表します

### 特殊フィールドの例

```python
# フォームコマンド
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "フォームコマンド名",
    "id": "コマンドID",
    "form": {
      "フィールドID1": {
        "id": "フィールドID1",
        "type": "input/textarea/select/radio/checkbox/switch",
        "label": "フィールドラベル",
        "value": "フィールド値"
      }
    }
  }
}

# ボタンイベント
{
  "type": "notice",
  "detail_type": "yunhu_button_click",
  "user_id": "ボタンをクリックしたユーザーID",
  "user_nickname": "ユーザーのニックネーム",
  "message_id": "メッセージID",
  "yunhu_button": {
    "id": "ボタンID（空の場合あり）",
    "value": "ボタンの値"
  }
}

# A2UIボタンイベント
{
  "type": "notice",
  "detail_type": "yunhu_a2ui_button",
  "user_id": "操作ユーザーID",
  "user_nickname": "ユーザーのニックネーム",
  "message_id": "メッセージID",
  "yunhu_a2ui": {
    "recv_id": "受信者ID",
    "recv_type": "受信者タイプ",
    "action_name": "操作名",
    "source_component_id": "ソースコンポーネントID",
    "form_context": {},
    "interaction_json": "インタラクションデータJSON文字列"
  }
}

### ボタンクリックイベントの処理例

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Yunhu通知イベントを処理します

    すべての通知イベントを処理するために汎用の on_notice() デコレーターを使用し、
    detail_type を通じて異なる種類の通知を区別します
    event.reply() は自動的に Yunhu プラットフォーム経由で返信されます
    """
    # ボタンクリックイベントか確認
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"ユーザー {user_nickname}({user_id}) がボタンをクリックしました: {button_value}")

        # event.reply() を使用して自動返信します（プラットフォームに応じて正しい送信方法を選択します）
        if button_value == "confirm":
            await event.reply("確認ボタンをクリックしました！")
        elif button_value == "cancel":
            await event.reply("操作がキャンセルされました")
        else:
            await event.reply(f"選択を受け取りました: {button_value}")

    # ショートカットメニューイベントを処理
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"ショートカットメニューがトリガーされました: {menu_id}")

    # ボット設定の変更を処理
    elif event.get("detail_type") == "yunhu_bot_setting":
        settings = event.get("yunhu_setting", {})
        await event.reply(f"設定が更新されました: {settings}")

    # A2UIボタンイベントを処理
    elif event.get("detail_type") == "yunhu_a2ui_button":
        a2ui = event.get("yunhu_a2ui", {})
        action_name = a2ui.get("action_name", "")
        form_context = a2ui.get("form_context", {})
        await event.reply(f"A2UI操作: {action_name}, フォームデータ: {form_context}")
```

### ボタン付きメッセージをチェーン呼び出しで送信

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "確認", "actionType": 3, "value": "confirm"},
        {"text": "キャンセル", "actionType": 3, "value": "cancel"},
        {"text": "詳細を見る", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# ボタン付きメッセージをグループに送信
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("以下の操作を確認してください")

# ボタン付きメッセージをユーザーのプライベートチャットに送信
await yunhu.Send.To("user", "789").Buttons(buttons).Text("選好設定を選択してください")
```

### A2UIメッセージの送信

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# A2UIメッセージを送信
await yunhu.Send.To("user", user_id).A2UI("A2UIインタラクションカードの内容")
```

# ボット設定
{
  "type": "notice",
  "detail_type": "yunhu_bot_setting",
  "group_id": "グループID（空の場合あり）",
  "user_nickname": "ユーザーのニックネーム",
  "yunhu_setting": {
    "設定項目ID": {
      "id": "設定項目ID",
      "type": "input/radio/checkbox/select/switch",
      "value": "設定値"
    }
  }
}

# ショートカットメニュー
{
  "type": "notice",
  "detail_type": "yunhu_shortcut_menu",
  "user_id": "メニューをトリガーしたユーザーID",
  "user_nickname": "ユーザーのニックネーム",
  "group_id": "グループID（グループチャットの場合）",
  "yunhu_menu": {
    "id": "メニューID",
    "type": "メニュータイプ(整数)",
    "action": "メニューアクション(整数)"
  }
}
```

## 拡張フィールドの説明

- 全ての固有フィールドは `yunhu_` プレフィックスで識別され、標準フィールドとの競合を避けます
- 原始データは `yunhu_raw` フィールドに保持され、雲湖プラットフォームの完全な原始データにアクセスするのに便利です
- `self.user_id` はボットIDを表します（設定の bot_id から取得）
- フォームコマンドは `yunhu_command` フィールドを通じて構造化データを提供します
- ボタンクリックイベントは `yunhu_button` フィールドを通じてボタンに関する情報を提供します
- A2UIボタンイベントは `yunhu_a2ui` フィールドを通じて A2UI インタラクションに関する情報を提供します
- ボット設定の変更は `yunhu_setting` フィールドを通じて設定項目データを提供します
- ショートカットメニュー操作は `yunhu_menu` フィールドを通じてメニューに関する情報を提供します
- スタンプ/絵文字メッセージは `yunhu_expression` メッセージセグメントを通じてスタンプデータ（sticker_id、パッケージID、画像サイズなど）を提供します

### スタンプ/絵文字メッセージセグメント (yunhu_expression)

ユーザーがスタンプまたは絵文字を送信すると、メッセージセグメントのタイプは `yunhu_expression` になります：

```json
{
  "type": "yunhu_expression",
  "data": {
    "sticker_id": "35154",
    "sticker_pack_id": "1670",
    "expression_id": "0",
    "image_name": "sticker/fabb9077f2ba302402ea871cab3686ad7a3fc52c.gif",
    "width": 500,
    "height": 500
  }
}
```

| フィールド | タイプ | 説明 |
|------|------|------|
| `sticker_id` | string | スタンプの固有識別子 |
| `sticker_pack_id` | string | スタンプパッケージID |
| `expression_id` | string | 絵文字ID |
| `image_name` | string | 絵文字画像ファイルパス |
| `width` | int | 画像の幅（任意） |
| `height` | int | 画像の高さ（任意） |

使用例：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"スタンプを受け取りました: sticker_id={data['sticker_id']}, パックID={data['sticker_pack_id']}")
```

---

## マルチBot設定

### 設定の説明

Yunhu アダプターは、同時に複数の雲湖ボットアカウントを設定・実行することをサポートしています。

```toml
# config.toml
[Yunhu_Adapter.bots.bot1]
bot_id = "30535459"  # ボットID（必須）
token = "your_bot1_token"  # ボットトークン（必須）
webhook_path = "/webhook/bot1"  # Webhookパス（任意、デフォルトは"/webhook"）
enabled = true  # 有効にするかどうか（任意、デフォルトはtrue）

[Yunhu_Adapter.bots.bot2]
bot_id = "12345678"  # 2番目のボットのID
token = "your_bot2_token"  # 2番目のボットのトークン
webhook_path = "/webhook/bot2"  # 独立したwebhookパス
enabled = true
```

**設定項目の説明：**
- `bot_id`：ボットの固有識別子ID（必須）。どのボットによってトリガーされたイベントかを識別するために使用されます
- `token`：雲湖プラットフォームが提供するAPIトークン（必須）
- `webhook_path`：雲湖イベントを受信するHTTPパス（任意、デフォルトは"/webhook"）
- `enabled`：このbotを有効にするかどうか（任意、デフォルトはtrue）

**重要なヒント：**
1. 雲湖プラットフォームのイベントにはボットIDが含まれていないため、設定で明示的に `bot_id` を指定する必要があります
2. 各botには独自の `webhook_path` を持たせる必要があり、それぞれのwebhookイベントを受信できるようにするためです
3. 雲湖プラットフォームでwebhookを設定する際は、各botに対応するURLを設定してください。例：
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Send DSLを使用したBotの指定

`Using()` メソッドを使用して、どのbotを使用してメッセージを送信するかを指定できます。このメソッドは2つのパラメータをサポートします：
- **アカウント名**：設定の bot 名（例: `bot1`, `bot2`）
- **bot_id**：設定の `bot_id` 値

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# アカウント名を使用してメッセージを送信
await yunhu.Send.Using("bot1").To("user", "user123").Text("bot1からのメッセージです！")

# bot_id を使用してメッセージを送信（対応するアカウントを自動的に照合）
await yunhu.Send.Using("30535459").To("group", "group456").Text("botからのメッセージです！")

# 指定がない場合、最初に有効になったbotが使用されます
await yunhu.Send.To("user", "user123").Text("デフォルトbotからのメッセージです！")
```

> **ヒント：** `bot_id` を使用する場合、システムは設定内の一致するアカウントを自動的に検索します。イベントへの返信を処理する際に特に便利です。`event["self"]["user_id"]` を直接使用して、同じアカウントから返信できます。

### イベント内のBot識別子

受信したイベントには、対応する `bot_id` 情報が自動的に含まれます。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # イベントをトリガーしたボットIDを取得
        bot_id = event["self"]["user_id"]
        print(f"メッセージは Bot: {bot_id} から来ました")
        
        # 同じbotで返信メッセージを送信
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

### ログ情報

アダプターはログに自動的に `bot_id` 情報を含めます。デバッグと追跡を容易にします：

```
[INFO] [yunhu] [bot:30535459] プライベートメッセージを受信 (送信者: user123)
[INFO] [yunhu] [bot:12345678] メッセージ送信成功、message_id: abc123
```

### 管理インターフェース

```python
# 全アカウント情報の取得
bots = yunhu.bots

# アカウントが有効か確認
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# アカウントの動的有効化/無効化（アダプターの再起動が必要）
yunhu.bots["bot1"].enabled = False
```

### 旧形式の設定との互換性

システムは旧形式の設定を自動的に互換性を持たせますが、より良いマルチbotサポートを得るために、新形式の設定に移行することをお勧めします。

請直接返回翻译后的完整Markdown内容，不要包含任何其他文字。



### 邮件适配

# メールプラットフォーム特性ドキュメント

MailAdapterはSMTP/IMAPプロトコルに基づいたメールアダプタであり、メールの送信、受信、および処理をサポートしています。

---

## ドキュメント情報

*   対応モジュールバージョン: 1.0.0
*   メンテナ: ErisPulse


## サポートされているメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：
```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# シンプルなテキストメール
await mail.Send.Using("from@example.com").To("to@example.com").Subject("テスト").Text("内容")

# 添付ファイル付きのHTMLメール
await mail.Send.Using("from@example.com")
    .To("to@example.com")
    .Subject("HTMLメール")
    .Cc(["cc1@example.com", "cc2@example.com"])
    .Attachment("report.pdf")
    .Html("<h1>HTMLコンテンツ</h1>")

# 注意：チェーン構文を使用する場合、パラメータメソッド（Text、Html）は送信メソッドの前に設定する必要があります。
```

サポートされている送信タイプは以下の通りです：
*   `.Text(text: str)`：プレーンテキストメールを送信
*   `.Html(html: str)`：HTML形式のメールを送信
*   `.Attachment(file: str, filename: str = None)`：添付ファイルを追加
*   `.Cc(emails: Union[str, List[str]])`：CC（カーボンコピー）を設定
*   `.Bcc(emails: Union[str, List[str]])`：BCC（ブラインドカーボンコピー）を設定
*   `.ReplyTo(email: str)`：返信先アドレスを設定

### 固有パラメータの説明

| パラメータ       | 型               | 説明                          |
|----------------|-------------------|------------------------------|
| Subject        | str               | メール件名                      |
| From           | str               | 送信者アドレス（Usingで設定）    |
| To             | str               | 宛先アドレス                    |
| Cc             | str または List[str] | CCアドレスのリスト              |
| Bcc            | str または List[str] | BCCアドレスのリスト             |
| Attachment     | str または Path    | 添付ファイルのパス              |

## 固有のイベントタイプ

メール受信イベントの形式：
```python
{
  "type": "message",
  "detail_type": "private",  # メールはデフォルトでプライベートチャット
  "platform": "email",
  "self": {"platform": "email", "user_id": account_id},
  "message": [
    {
      "type": "text",
      "data": {
        "text": f"Subject: {subject}\nFrom: {from_}\n\n{text_content}"
      }
    }
  ],
  "email_raw": {
    "subject": subject,
    "from": from_,
    "to": to,
    "date": date,
    "text_content": text_content,
    "html_content": html_content,
    "attachments": [att["filename"] for att in attachments]
  },
  "attachments": [  # 添付データのリスト
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 1024,
      "data": b"..."  # 添付ファイルのバイナリデータ
    }
  ]
}
```

## 拡張フィールドの説明

*   `email_raw`: 原始メールデータを含む
*   `attachments`: 添付データのリスト

## OneBot12プロトコル変換の説明

メールイベントをOneBot12プロトコルに変換する際の主な相違点：

### 主な相違点

1.  固有のフィールド：
    *   `email_raw`: 原始メールデータを含む
    *   `attachments`: 添付データのリスト

2.  特別な処理：
    *   メールの件名と送信者情報はメッセージテキスト内に含まれます
    *   添付データはバイナリ形式で提供されます
    *   HTMLコンテンツはemail_rawフィールド内に保持されます

### 例

```python
{
  "type": "message",
  "platform": "email",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "Subject: 会議通知\nFrom: sender@example.com\n\n添付ファイルをご確認ください"
      }
    }
  ],
  "email_raw": {
    "subject": "会議通知",
    "from": "sender@example.com",
    "to": "receiver@example.com",
    "html_content": "<p>添付ファイルをご確認ください</p>",
    "attachments": ["document.pdf"]
  },
  "attachments": [
    {
      "filename": "document.pdf",
      "data": b"...",  # 添付ファイルのバイナリデータ
      "size": 1024
    }
  ]
}



### Kook 适配

# Kookプラットフォーム特性ドキュメント

KookAdapter は、Kook（旧称开黑啦）Bot WebSocket プロトコルを基に構築されたアダプターで、Kook のすべての機能モジュールを統合し、統一されたイベント処理とメッセージ操作インターフェースを提供します。

---

## 文書情報

- 対応モジュールバージョン: 0.1.0
- メンテナ: ShanFish

## 基本情報

- プラットフォーム紹介：Kook（旧称开黑啦）は、テキスト、音声、ビデオ通信をサポートするコミュニティプラットフォームであり、完全な Bot 開発インターフェースを提供します
- アダプター名：KookAdapter
- 接続方式：WebSocket ロング接続（Kook ゲートウェイ経由）
- 認証方式：Bot Token ベースの認証
- チェーン構文修飾のサポート：`.Reply()`、`.At()`、`.AtAll()` などのチェーン構文修飾メソッドをサポート
- OneBot12互換性：OneBot12 形式メッセージの送信をサポート

## 設定説明

```toml
# config.toml
[KookAdapter]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token（必須、形式: Bot xxx/xxx）
bot_id = ""                   # Bot ユーザーID（任意、未入力の場合は token から解析）
compress = true               # WebSocket 圧縮を有効にするかどうか（任意、デフォルトは true）
```

**設定項目の説明：**
- `token`：Kook Bot の Token（必須）。[Kook Developer Center](https://developer.kookapp.cn) から取得、形式は `Bot xxx/xxx`
- `bot_id`：Bot のユーザーID（任意）。未入力の場合、アダプターは token から自動的に解析を試みます。正確性を確保するために手動で入力することを推奨します
- `compress`：WebSocket データ圧縮を有効にするかどうか（任意、デフォルトは `true`）。有効にすると zlib を使用してデータを展開します

**API環境：**
- Kook API ベースアドレス：`https://www.kookapp.cn/api/v3`
- WebSocket ゲートウェイは API を通じて動的に取得：`POST /gateway/index`

## サポートされているメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：

```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：
- `.Text(text: str)`：テキストメッセージを送信します。
- `.Image(file: bytes | str)`：画像メッセージを送信します。ファイルパス、URL、バイナリデータをサポート。
- `.Video(file: bytes | str)`：ビデオメッセージを送信します。ファイルパス、URL、バイナリデータをサポート。
- `.File(file: bytes | str, filename: str = None)`：ファイルメッセージを送信します。ファイルパス、URL、バイナリデータをサポート。
- `.Voice(file: bytes | str)`：音声メッセージを送信します。ファイルパス、URL、バイナリデータをサポート。
- `.Markdown(text: str)`：KMarkdown形式メッセージを送信します。
- `.Card(card_data: dict)`：カードメッセージ（CardMessage）を送信します。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式メッセージを送信します。

### チェーン構文修飾メソッド（組み合わせ可能）

チェーン構文修飾メソッドは `self` を返し、チェーン呼び出しをサポートします。必ず最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージへの返信（引用）。
- `.At(user_id: str)`：指定したユーザーにメンションします。複数回呼び出すことで複数のユーザーにメンションできます。
- `.AtAll()`：すべてのユーザーにメンションします。

### チェーン構文の使用例

```python
# 基本的な送信
await kook.Send.To("group", channel_id).Text("Hello")

# メッセージへの返信
await kook.Send.To("group", channel_id).Reply(msg_id).Text("返信メッセージ")

# ユーザーへのメンション
await kook.Send.To("group", channel_id).At("user_id").Text("こんにちは")

# 複数ユーザーへのメンション
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("複数ユーザー@")

# 全体へのメンション
await kook.Send.To("group", channel_id).AtAll().Text("お知らせ")

# 組み合わせた使用例
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合メッセージ")
```

### OneBot12メッセージサポート

アダプターは OneBot12 形式のメッセージを送信することをサポートし、クロスプラットフォームメッセージ互換性を容易にします：

```python
# OneBot12 形式メッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# チェーン構文修飾と組み合わせ
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Raw_ob12 で mention と reply メッセージセグメントを使用
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### 追加操作メソッド

メッセージ送信に加え、Kookアダプターは以下の操作もサポートします：

```python
# メッセージの編集（KMarkdown type=9 と CardMessage type=10 のみサポート）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後の内容**")

# メッセージの撤回
await kook.Send.To("group", channel_id).Recall(msg_id)

# ファイルのアップロード（ファイルURLを取得）
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、直接 await して送信結果を取得できます。戻り値は ErisPulse アダプターの標準化された戻り値規則に準拠します：

```python
{
    "status": "ok",           // 実行ステータス: "ok" または "failed"
    "retcode": 0,             // 戻り値コード（Kook API の code）
    "data": {...},            // レスポンスデータ
    "message_id": "xxx",      // メッセージID
    "message": "",            // エラーメッセージ
    "kook_raw": {...}         // 元のレスポンスデータ
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 40100 | Token が無効、または提供されていない |
| 40101 | Token が期限切れ |
| 40102 | Token と Bot が一致しない |
| 40103 | 権限が不足している |
| 40000 | パラメータエラー |
| 40400 | 対象が存在しない |
| 40300 | 操作する権限がない |
| 50000 | サーバー内部エラー |
| -1 | アダプター内部エラー |

## 固有のイベントタイプ

このプラットフォームの機能を使用するには、`platform=="kook"` を使用して検出する必要があります

### 主な違い

1. **チャンネルシステム**：Kook はサーバー（Guild）とチャンネル（Channel）の二層構造を使用しており、チャンネルがメッセージの基本送信ターゲットとなります
2. **メッセージタイプ**：Kook はテキスト(1)、画像(2)、ビデオ(3)、ファイル(4)、音声(8)、KMarkdown(9)、カードメッセージ(10)など、さまざまなメッセージタイプをサポートします
3. **プライベートメッセージシステム**：Kook はチャンネルメッセージとプライベートメッセージを区別し、異なる API エンドポイントを使用します
4. **メッセージシーケンス**：Kook WebSocket は `sn` シーケンス番号を使用してメッセージの順序性を保証し、メッセージの一時保存と順序を考慮した再アレンジをサポートします
5. **メッセージの編集と撤回**：送信済みメッセージの編集（KMarkdown および CardMessage のみ）とメッセージの撤回をサポートします

### 拡張フィールド

- すべての固有のフィールドは `kook_` プレフィックスで識別されます
- 原始データは `kook_raw` フィールドに保持されます
- `kook_raw_type` は元の Kook メッセージタイプ番号（例：`1` はテキスト、`255` は通知イベント）を識別します

### 特殊フィールドの例

```python
# チャンネルテキストメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "channel_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# 画像付きメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "channel_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "2",
  "message": [
    {"type": "image", "data": {"file": "画像URL", "url": "画像URL"}}
  ],
  "alt_message": "画像内容"
}

# KMarkdownメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "9",
  "message": [
    {"type": "text", "data": {"text": "解析済みテキスト"}}
  ]
}

# カードメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "ユーザーID",
  "group_id": "チャンネルID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "10",
  "message": [
    {"type": "json", "data": {"data": "カードJSON内容"}}
  ]
}

# プライベートメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "ユーザーID",
  "message_id": "メッセージID",
  "kook_raw": {...},
  "kook_raw_type": "1",
  "message": [
    {"type": "text", "data": {"text": "プライベートメッセージ内容"}}
  ]
}
```

### メッセージセグメントタイプ

Kook のメッセージタイプは、`type` フィールドに基づいて対応するメッセージセグメントに自動的に変換されます：

| Kook type | 変換タイプ | 説明 |
|---|---|---|
| 1 | `text` | テキストメッセージ |
| 2 | `image` | 画像メッセージ |
| 3 | `video` | ビデオメッセージ |
| 4 | `file` | ファイルメッセージ |
| 8 | `record` | 音声メッセージ |
| 9 | `text` | KMarkdownメッセージ（純テキストコンテンツを抽出） |
| 10 | `json` | カードメッセージ（元のJSON） |

メッセージセグメント構造の例：
```json
{
  "type": "image",
  "data": {
    "file": "画像URL",
    "url": "画像URL"
  }
}
```

### Mentionメッセージセグメント

メッセージに@情報が含まれている場合、メッセージセグメントの前に `mention` メッセージセグメントが挿入されます：

```json
{
  "type": "mention",
  "data": {
    "user_id": "メンションされたユーザーID"
  }
}
```

### mention_allメッセージセグメント

メッセージが@全体の場合、`mention_all` メッセージセグメントが挿入されます：

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket接続

### 接続フロー

1. Bot Token を使用して `POST /gateway/index` を呼び出し、WebSocket ゲートウェイアドレスを取得します
2. WebSocket ゲートウェイに接続します
3. HELLO（s=1）シグナルを受信し、接続状態を検証します
4. ハートビートループを開始します（PING、s=2、30秒ごと）
5. メッセージイベント（s=0）を受信し、`sn` シーケンス番号を使用して順序性を保証します
6. ハートビート応答 PONG（s=3）を受信します

### シグナルタイプ

| シグナル | s値 | 説明 |
|------|-----|------|
| HELLO | 1 | サーバーの歓迎シグナル、接続成功後に受信 |
| PING | 2 | クライアントのハートビート、30秒ごとに送信、現在の sn を持ちます |
| PONG | 3 | ハートビート応答 |
| RESUME | 4 | 接続復帰シグナル、sn を持ち会話を復元します |
| RECONNECT | 5 | サーバーからの再接続要求、ゲートウェイの再取得が必要 |
| RESUME_ACK | 6 | RESUME 成功応答 |

### 接続切断時の再接続

- 接続が異常で切断された場合、アダプターは自動的に再接続を試行します
- 前に `sn > 0` が存在する場合、まず RESUME（s=4）を使用して接続を復帰しようとします
- RESUME に失敗した場合、sn とメッセージキューをリセットし、新しい接続を再開します（HELLO フロー）
- RECONNECT（s=5）シグナルを受信した場合、ステータスをクリアして再接続します

### メッセージシーケンス番号機構

Kook WebSocket は `sn`（増分シーケンス番号）を使用してメッセージの順序性を保証します：

- 各メッセージイベント（s=0）を受信すると、sn が増加します
- 受信したメッセージの sn が連続していない場合、一時保存モードに入ります
- 一時保存領域内のメッセージは sn で並べ替えられ、不足しているメッセージが到着したら順序通りに処理されます
- 一時保存領域がクリアされると、一時保存モードから自動的に退出します

## 使用例

### チャンネルメッセージの処理

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

kook = sdk.adapter.get("kook")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await kook.Send.To("group", channel_id).Text("Hello!")
```

### プライベートメッセージの処理

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "kook":
        return
    if event.get("detail_type") != "private":
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await kook.Send.To("user", user_id).Text(f"あなたは言いました: {text}")
```

### 通知イベントの処理（絵文字反応など）

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "added_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"ユーザー {user_id} がメッセージ {msg_id} に絵文字反応を追加しました")

    elif sub_type == "deleted_reaction":
        emoji = event.get("emoji", {})
        user_id = event.get("user_id")
        msg_id = event.get("message_id")
        print(f"ユーザー {user_id} がメッセージ {msg_id} の絵文字反応を削除しました")
```

### メディアメッセージの送信

```python
# 画像の送信（URL）
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# 画像の送信（バイナリ）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# ビデオの送信
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# ファイルの送信
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# 音声の送信
await kook.Send.To("group", channel_id).Voice("https://example.com/voice.mp3")
```

### KMarkdownとカードメッセージの送信

```python
# KMarkdown
await kook.Send.To("group", channel_id).Markdown("**太字** *斜体* [リンク](https://example.com)")

# カードメッセージ
card = {
    "type": "card",
    "theme": "primary",
    "size": "lg",
    "modules": [
        {"type": "header", "text": {"type": "plain-text", "content": "タイトル"}},
        {"type": "section", "text": {"type": "kmarkdown", "content": "内容"}}
    ]
}
await kook.Send.To("group", channel_id).Card(card)
```

### メッセージの編集と撤回

```python
# メッセージの送信
result = await kook.Send.To("group", channel_id).Markdown("**元の内容**")
msg_id = result["data"]["msg_id"]

# メッセージの編集（KMarkdown および CardMessage のみサポート）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後の内容**")

# メッセージの撤回
await kook.Send.To("group", channel_id).Recall(msg_id)
```

### プライベートメッセージの編集と削除通知の処理

```python
@notice.on_notice()
async def handle_private_notice(event):
    if event.get("platform") != "kook":
        return

    sub_type = event.get("sub_type")

    if sub_type == "updated_private_message":
        msg_id = event.get("message_id")
        content = event.get("content")
        print(f"プライベートメッセージが更新されました: {msg_id}, 新しい内容: {content}")

    elif sub_type == "deleted_private_message":
        msg_id = event.get("message_id")
        print(f"プライベートメッセージが削除されました: {msg_id}")



### Matrix 适配

# Matrixプラットフォーム特性ドキュメント

MatrixAdapterは[Matrixプロトコル](https://spec.matrix.org/)に基づいて構築されたアダプターであり、Matrixプロトコルのすべてのコア機能モジュールを統合し、統一されたイベント処理とメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 1.0.0
- メンテナ: ErisPulse

## 基本情報

- プラットフォーム概要：Matrixはオープンな非中央集権型通信プロトコルであり、ダイレクトメッセージ、グループなどの複数のシナリオをサポートしています。
- アダプター名：MatrixAdapter
- 接続方式：ロングポーリング（Matrix Sync API `/sync` 経由）
- 認証方式：access_token または user_id + password によるログインでトークンを取得
- メソッドチェーン修飾サポート：`.Reply()`、`.At()`、`.AtAll()` などのメソッドチェーン修飾をサポート
- OneBot12互換：OneBot12フォーマットのメッセージ送信をサポート

## 設定説明

```toml
# config.toml
[Matrix_Adapter]
homeserver = "https://matrix.org"          # Matrixサーバーアドレス（必須）
access_token = "YOUR_ACCESS_TOKEN"          # アクセストークン（user_id+password と二択）
user_id = ""                                # MatrixユーザーID（例: @bot:matrix.org）
password = ""                               # Matrixユーザーパスワード
auto_accept_invites = true                  # ルームへの招待を自動的に承諾するか（任意、デフォルトはtrue）
```

**設定項目の説明：**
- `homeserver`：Matrixサーバーアドレス（必須）、デフォルトは `https://matrix.org`
- `access_token`：アクセストークン。Matrixクライアントから取得可能。既存のトークンがある場合は直接入力します。
- `user_id`：MatrixユーザーID（例: `@bot:matrix.org`）、`password` と組み合わせてログインに使用します。
- `password`：Matrixユーザーパスワード。自動ログインで access_token を取得するために使用します。
- `auto_accept_invites`：ルームへの招待を自動的に承諾するかどうか。デフォルトは `true`。

**認証方式：**
- 方式1（推奨）：直接 `access_token` を提供する
- 方式2：`user_id` と `password` を提供すると、アダプターが自動的にログインAPIを呼び出してトークンを取得します。

## サポートするメッセージ送信タイプ

すべての送信メソッドはメソッドチェーン構文で実装されています。例：
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

サポートする送信タイプは以下の通りです：
- `.Text(text: str)`：プレーンテキストメッセージを送信します。
- `.Image(file: bytes | str)`：画像メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.Voice(file: bytes | str)`：音声メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.Video(file: bytes | str)`：動画メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.File(file: bytes | str, filename: str = "")`：ファイルメッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータをサポートします。
- `.Notice(text: str)`：通知メッセージ（Matrixの m.notice タイプ）を送信します。
- `.Html(html: str, fallback: str = "")`：HTMLフォーマットのメッセージを送信します。リッチテキストコンテンツをサポートします。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12フォーマットのメッセージを送信します。

### メソッドチェーン修飾メソッド（組み合わせて使用可能）

メソッドチェーン修飾メソッドは `self` を返し、メソッドチェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定したメッセージに返信します（Matrixの `m.in_reply_to` リレーション経由）。
- `.At(user_id: str)`：指定したユーザーにメンションします（Matrixの `m.mentions` フィールドで実装）。
- `.AtAll()`：ルーム内の全員にメンションします（Matrixの `@room` メンションで実装）。

### メソッドチェーン呼び出し例

```python
# 基本的な送信
await matrix.Send.To("user", dm_room_id).Text("Hello")

# 返信
await matrix.Send.To("group", room_id).Reply("$event_id").Text("返信メッセージ")

# ユーザーへのメンション
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("こんにちは")

# 全員へのメンション
await matrix.Send.To("group", room_id).AtAll().Text("お知らせ")

# 組み合わせ：返信 + メンション
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("複合メッセージ")

# HTMLメッセージの送信
await matrix.Send.To("group", room_id).Html("<h1>タイトル</h1><p>内容</p>", fallback="タイトル\n内容")

# 通知メッセージの送信
await matrix.Send.To("group", room_id).Notice("システム通知")
```

### OneBot12メッセージサポート

アダプターはOneBot12フォーマットのメッセージ送信をサポートしており、クロスプラットフォームのメッセージ互換性に役立ちます：

```python
# OneBot12フォーマットのメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# メソッドチェーン修飾と組み合わせ
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# 複雑なメッセージ
ob12_msg = [
    {"type": "text", "data": {"text": "この画像を見て："}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "いいよね？"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、直接 `await` して送信結果を取得できます。戻り値は ErisPulse アダプターの標準化された戻り値の仕様に従います：

```python
{
    "status": "ok",           // 実行ステータス: "ok" または "failed"
    "retcode": 0,             // リターンコード
    "data": {...},            // レスポンスデータ
    "message_id": "$event_id", // MatrixイベントID
    "message": "",            // エラーメッセージ
    "matrix_raw": {...}       // 生のレスポンスデータ
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 32000 | リクエストタイムアウトまたはメディアのアップロード失敗 |
| 33000 | API呼び出し例外 |
| 34000 | APIが予期しないフォーマットまたはビジネスエラーを返しました |

## 固有のイベントタイプ

`platform=="matrix"` で検出してからこのプラットフォームの特性を使用する必要があります。

### コアな違い

1. **非中央集権型アーキテクチャ**：Matrixは非中央集権型の通信プロトコルであり、ユーザーIDのフォーマットは `@user:server.domain`、ルームIDのフォーマットは `!room_id:server.domain` です。
2. **ルームの概念**：Matrixはグループチャットとダイレクトメッセージを区別せず、すべての会話は「ルーム」です。アダプターはDM（Direct Message）アカウントデータを通じてダイレクトメッセージのルームを自動的に識別します。
3. **ロングポーリング同期**：WebSocketではなく、`/sync` APIを使用してロングポーリングを行い、新しいイベントを取得します。
4. **MXC URI**：メディアファイルは `mxc://server.domain/media_id` フォーマットで参照されます。
5. **HTMLリッチテキスト**：`formatted_body` を通じたHTMLフォーマットのメッセージ送信をサポートします。
6. **絵文字リアクション**：従来の返信メッセージとは異なる、メッセージレベルの絵文字リアクション（Reaction）をサポートします。
7. **メッセージ編集**：`m.replace` リレーションによる送信済みメッセージの編集をサポートします。
8. **メッセージの削除**：`m.room.redaction` によるメッセージの削除をサポートします。

### 拡張フィールド

- すべての固有フィールドは `matrix_` プレフィックスで識別されます。
- 生のデータは `matrix_raw` フィールドに保持されます。
- `matrix_raw_type` は生のMatrixイベントタイプ（例: `m.room.message`、`m.room.member`）を識別します。

### 特殊フィールドの例

```python
# グループメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# ダイレクトメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "@user:matrix.org",
  "matrix_room_id": "!dm_room_id:matrix.org"
}

# 絵文字リアクション
{
  "type": "notice",
  "detail_type": "matrix_reaction",
  "matrix_reaction_event_id": "$reacted_msg_id",
  "matrix_reaction_key": "👍"
}

# メッセージの削除
{
  "type": "notice",
  "detail_type": "matrix_redaction",
  "matrix_redacted_event_id": "$deleted_msg_id"
}

# メッセージ編集
{
  "type": "message",
  "detail_type": "group",
  "matrix_edit": true,
  "matrix_original_event_id": "$original_event_id"
}

# スレッドメッセージ
{
  "type": "message",
  "detail_type": "group",
  "thread_id": "$thread_root_id"
}
```

### メッセージセグメントタイプ

Matrixメッセージは `msgtype` に基づいて対応するメッセージセグメントに自動的に変換されます：

| msgtype | 変換タイプ | 説明 |
|---|---|---|
| m.text | `text` | テキストメッセージ |
| m.notice | `text` | 通知メッセージ |
| m.emote | `text` | アクションメッセージ |
| m.image | `image` | 画像メッセージ |
| m.audio | `voice` | 音声メッセージ |
| m.video | `video` | 動画メッセージ |
| m.file | `file` | ファイルメッセージ |
| m.location | `location` | 位置情報メッセージ |

メッセージセグメントの構造例：

```json
// テキストメッセージ（HTML付き）
{
  "type": "text",
  "data": {
    "text": "プレーンテキスト内容",
    "html": "<b>HTML内容</b>"
  }
}

// 画像メッセージ
{
  "type": "image",
  "data": {
    "url": "mxc://matrix.org/abc123",
    "filename": "photo.png",
    "matrix_mxc": "mxc://matrix.org/abc123",
    "info": {
      "mimetype": "image/png",
      "w": 800,
      "h": 600,
      "size": 123456
    }
  }
}

// 位置情報メッセージ
{
  "type": "location",
  "data": {
    "latitude": 0.0,
    "longitude": 0.0,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "北京市"
  }
}
```

### Event Mixin メソッド

MatrixAdapterは以下のイベントミックスインメソッドを登録しており、イベント処理内で直接呼び出すことができます：

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_room_id()` | `str` | ルームIDを取得 |
| `get_matrix_event_type()` | `str` | 生のMatrixイベントタイプを取得 |
| `get_matrix_sender()` | `str` | 生の送信者IDを取得 |
| `get_reaction_key()` | `str` | リアクションの絵文字を取得 |
| `is_edited()` | `bool` | メッセージが編集されたものか判定 |
| `is_notice()` | `bool` | メッセージが m.notice タイプか判定 |

```python
@message.on_message()
async def handle_message(event):
    if event.get("platform") != "matrix":
        return

    room_id = event.get_room_id()
    event_type = event.get_matrix_event_type()
    sender = event.get_matrix_sender()
    is_edited = event.is_edited()
    is_notice = event.is_notice()
```

## Sync API 接続

### 同期フロー

1. access_token または user_id + password を使用して認証
2. `/_matrix/client/v3/account/whoami` を呼び出して bot_user_id を取得
3. connect メタイベントを発火
4. 初期同期（`/_matrix/client/v3/sync?timeout=0`）を実行し、`next_batch` トークンを取得
5. DMルームを検出（`/_matrix/client/v3/user/{user_id}/account_data/m.direct`）
6. ロングポーリング同期ループを開始（`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`）
7. 毎回の同期で返された新しいイベントを処理し、変換して発火

### ハートビートメカニズム

- アダプターは30秒ごとに1回 `heartbeat` メタイベントを発火します。
- 接続成功時に `connect` メタイベントを発火します。
- 終了時に `disconnect` メタイベントを発火します。

### ルームへの招待

- ルームへの招待（`invite` ステータスのルーム）を受信した際、`auto_accept_invites` が `true`（デフォルト）に設定されている場合、アダプターは自動的にルームに参加します。
- ルームへの参加は `/_matrix/client/v3/join/{room_id}` インターフェースを呼び出します。

## 使用例

### グループメッセージの処理

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

matrix = sdk.adapter.get("matrix")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "matrix":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    room_id = event.get("group_id")

    if text == "hello":
        await matrix.Send.To("group", room_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### 絵文字リアクションの処理

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_reaction(event):
    if event.get("platform") != "matrix":
        return

    if event.get("detail_type") == "matrix_reaction":
        reaction_key = event.get("matrix_reaction_key")
        reacted_event_id = event.get("matrix_reaction_event_id")
        room_id = event.get_room_id()
        # 絵文字リアクションの処理...
```

### メディアメッセージの送信

```python
# 画像を送信（URL）
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# 画像を送信（MXC URI）
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# 画像を送信（バイナリデータ）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# 画像を送信（ローカルファイルパス）
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# ファイルを送信（ファイル名付き）
await matrix.Send.To("group", room_id).File("/path/to/document.pdf", filename="ドキュメント.pdf")
```

### メッセージ編集の処理

```python
@message.on_message()
async def handle_edited_message(event):
    if event.get("platform") != "matrix":
        return

    if event.is_edited():
        original_id = event.get("matrix_original_event_id")
        # 編集されたメッセージの処理...
```

### メンバー変更の監視

```python
@notice.on_notice()
async def handle_member_change(event):
    if event.get("platform") != "matrix":
        return

    detail_type = event.get("detail_type")

    if detail_type == "group_member_increase":
        user_id = event.get("user_id")
        nickname = event.get("user_nickname")
        print(f"ユーザー {nickname} ({user_id}) がルームに参加しました")

    elif detail_type == "group_member_decrease":
        user_id = event.get("user_id")
        operator_id = event.get("operator_id")
        print(f"ユーザー {user_id} が削除されました。操作者: {operator_id}")



### QQBot 适配

# QQBotプラットフォーム特性

QQBotAdapterはQQBot（QQロボットのドキュメント）プロトコルに基づいて構築されたアダプタで、QQBotのすべての機能モジュールを統合し、統一されたイベント処理とメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 1.0.0
- メンテナ: ErisPulse

## 基本情報

- プラットフォーム概要：QQBotはQQ公式が提供するロボットの開発インターフェースであり、グループチャット、プライベートチャット、チャンネルなどの多彩なシナリオをサポートしています。
- アダプター名：QQBotAdapter
- 接続方式：WebSocket ロング接続（QQBotゲートウェイを経由）
- 認証方式：appId + clientSecret に基づいて access_token を取得
- チェーン修飾子のサポート：`.Reply()`、`.At()`、`.AtAll()`、`.Keyboard()` などのチェーン修飾メソッドをサポート
- OneBot12互換性：OneBot12フォーマットメッセージの送信をサポート

## 設定説明

```toml
# config.toml
[QQBot_Adapter]
appid = "YOUR_APPID"          # QQロボットアプリID（必須）
secret = "YOUR_CLIENT_SECRET"  # QQロボットクライアントシークレット（必須）
sandbox = false                 # サンドボックス環境を使用するか（任意、デフォルトはfalse）
intents = [1, 30, 25]          # イベントのインテントビットを購読（任意）
gateway_url = "wss://api.sgroup.qq.com/websocket/"  # カスタムゲートウェイアドレス（任意）
```

**設定項目の説明：**
- `appid`：QQロボットのアプリID（必須）、QQオープンプラットフォームから取得
- `secret`：QQロボットのクライアントシークレット（必須）、QQオープンプラットフォームから取得
- `sandbox`：サンドボックス環境を使用するかどうか。サンドボックス環境APIアドレスは `https://sandbox.api.sgroup.qq.com`
- `intents`：イベント購読インテントリスト。各値は左シフト演算子（<<）を行い、ビットOR演算（|）されます
  - `1`：チャンネル関連イベント
  - `25`：チャンネルメッセージイベント
  - `30`：グループ@メッセージイベント
- `gateway_url`：WebSocketゲートウェイアドレス。デフォルトは `wss://api.sgroup.qq.com/websocket/`

**API環境：**
- 本番環境：`https://api.sgroup.qq.com`
- サンドボックス環境：`https://sandbox.api.sgroup.qq.com`

## サポートされているメッセージ送信タイプ

すべての送信メソッドはチェーン構文を介して実装されています。例：

```python
from ErisPulse.Core import adapter
qqbot = adapter.get("qqbot")

await qqbot.Send.To("user", user_openid).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：

- `.Text(text: str)`：プレーンテキストメッセージを送信。
- `.Image(file: bytes | str)`：画像メッセージを送信。ファイルパス、URL、バイナリデータをサポート。
- `.Markdown(content: str)`：Markdown形式のメッセージを送信。
- `.Ark(template_id: int, kv: list)`：Arkテンプレートメッセージを送信。
- `.Embed(embed_data: dict)`：Embedメッセージを送信。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信。

### チェーン修飾子メソッド（組み合わせ可能）

チェーン修飾子メソッドは `self` を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信。
- `.At(user_id: str)`：指定されたユーザーに@する（`<@user_id>` 形式で内容を挿入）。
- `.AtAll()`：全員に@する（`@所有人` テキストを挿入）。
- `.Keyboard(keyboard: dict)`：キーボードボタンを追加。

### チェーン呼び出しの例

```python
# 基本的な送信
await qqbot.Send.To("user", user_openid).Text("Hello")

# メッセージに返信
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await qqbot.Send.To("group", group_openid).Reply(msg_id).Keyboard(keyboard).Text("返信とボタン付きのメッセージ")

# ユーザーに@する
await qqbot.Send.To("group", group_openid).At("member_openid").Text("こんにちは")

# 組み合わせて使用
await qqbot.Send.To("group", group_openid).Reply(msg_id).At("member_openid").Keyboard(keyboard).Text("複合メッセージ")
```

### OneBot12メッセージサポート

アダプターはOneBot12形式のメッセージ送信をサポートしており、クロスプラットフォームメッセージの互換性を容易にします：

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await qqbot.Send.To("user", user_openid).Raw_ob12(ob12_msg)

# チェーン修飾子と組み合わせる
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await qqbot.Send.To("group", group_openid).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、直接 await を行って送信結果を取得できます。戻り値は ErisPulse アダプターの標準化された戻り値規格に従います：

```python
{
    "status": "ok",           // 実行ステータス: "ok" または "failed"
    "retcode": 0,             // 返りコード
    "data": {...},            // レスポンスデータ
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "qqbot_raw": {...}        // 元のレスポンスデータ
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 10003 | 送信先を特定できない |
| 32000 | リクエストがタイムアウトした |
| 33000 | API呼び出しの異常 |
| 34000 | APIが予期しない形式を返した、またはビジネスエラー |

## 特有のイベントタイプ

本プラットフォームの機能を使用するには、`platform=="qqbot"` の検出が必要です

### 主な差異点

1.  **openid体系**：QQBotはQQ番号ではなくopenidを使用します。ユーザーとグループの識別子はすべてopenid文字列です。
2.  **グループメッセージは必ず@する**：グループ内のメッセージは、ユーザーがロボットに@した場合のみ受信されます（`GROUP_AT_MESSAGE_CREATE`）。
3.  **チャンネルシステム**：QQBotはチャンネル（Guild）とサブチャンネル（Channel）のメッセージとイベントをサポートします。
4.  **メッセージ審査**：送信されたメッセージには審査が必要な場合があり、`qqbot_audit_pass`/`qqbot_audit_reject` イベントで結果が通知されます。
5.  **受動的な返信**：グループメッセージとプライベートチャットメッセージは受動的な返信メカニズムをサポートしており、送信時に `msg_id` を携带する必要があります。

### 拡張フィールド

- すべての特有のフィールドは `qqbot_` プレフィックスで識別されます。
- 元のデータは `qqbot_raw` フィールドに保持されます。
- `qqbot_raw_type` は元のQQBotイベントタイプを識別します（例: `C2C_MESSAGE_CREATE`）。
- 添付ファイルデータは `qqbot_attachment` フィールドを介して元の添付ファイル情報を保存します。

### 特殊フィールドの例

```python
# グループ@メッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "MEMBER_OPENID",
  "group_id": "GROUP_OPENID",
  "qqbot_group_openid": "GROUP_OPENID",
  "qqbot_member_openid": "MEMBER_OPENID",
  "qqbot_event_id": "メッセージイベントID",
  "qqbot_reply_token": "返信トークン"
}

# プライベートチャットメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "USER_OPENID",
  "qqbot_openid": "USER_OPENID",
  "qqbot_event_id": "メッセージイベントID",
  "qqbot_reply_token": "返信トークン"
}

# インタラクションイベント
{
  "type": "notice",
  "detail_type": "qqbot_interaction",
  "qqbot_interaction_id": "インタラクションID",
  "qqbot_interaction_type": "インタラクションタイプ",
  "qqbot_interaction_data": {
    "...": "インタラクションデータ"
  }
}

# メッセージ審査
{
  "type": "notice",
  "detail_type": "qqbot_audit_pass",
  "qqbot_audit_id": "審査ID",
  "qqbot_message_id": "メッセージID"
}

# メッセージ削除
{
  "type": "notice",
  "detail_type": "qqbot_message_delete",
  "message_id": "削除されたメッセージID",
  "operator_id": "操作者ID"
}

# 絵文字の反応
{
  "type": "notice",
  "detail_type": "qqbot_reaction_add",
  "qqbot_raw": {
    "...": "元のデータ"
  }
}
```

### チャンネルメッセージセグメント

チャンネルメッセージは `mentions` フィールドをサポートし、変換後は `mention` メッセージセグメントとして表現されます：

```json
{
  "type": "mention",
  "data": {
    "user_id": "被@ユーザーID",
    "user_name": "被@ユーザーのニックネーム"
  }
}
```

### 添付ファイルメッセージセグメント

QQBotの添付ファイルは `content_type` に基づいて対応するメッセージセグメントに自動的に変換されます：

| content_type プレフィックス | 変換タイプ | 説明 |
|---|---|---|
| `image` | `image` | 画像メッセージ |
| `video` | `video` | 動画メッセージ |
| `audio` | `voice` | 音声メッセージ |
| その他 | `file` | ファイルメッセージ |

添付ファイルメッセージセグメントの構造：

```json
{
  "type": "image",
  "data": {
    "url": "添付ファイルURL",
    "qqbot_attachment": {
      "content_type": "image/png",
      "url": "元の添付ファイルURL"
    }
  }
}
```

## WebSocket接続

### 接続手順

1.  appId + clientSecret を使用して access_token を取得
2.  WebSocketゲートウェイに接続
3.  OP_HELLO（op=10）メッセージを受信し、ハートビート間隔を取得
4.  OP_IDENTIFY（op=2）を送信して認証
5.  READY イベントを受信し、session_id と bot_id を取得
6.  ハートビートループを開始（OP_HEARTBEAT、op=1）
7.  イベントの配信を受信（OP_DISPATCH、op=0）

### 再接続（切断時の再接続）

- 自動再接続をサポート。最大再接続回数は50回です。
- 再接続待ち時間には指数バックオフアルゴリズムを使用：`min(5 * 2^min(count, 6), 300)` 秒
- セッションの復帰（OP_RESUME、op=6）をサポート。session_id + seq を使用して復元します。
- OP_RECONNECT（op=7）または OP_INVALID_SESSION（op=9）を受信したら自動的に再接続がトリガーされます。

### Token更新

- access_token の有効期限は通常7200秒です。
- アダプターは毎回7080秒（7200-120）でtokenを自動更新します。
- 更新インターフェース：`POST https://bots.qq.com/app/getAppAccessToken`

## イベント購読

intents値はビット演算で組み合わせます：

```python
intents = [1, 30, 25]
value = 0
for intent in intents:
    value |= (1 << intent)
```

一般的なintentビット：

| intent値 | 説明 |
|----------|------|
| 1 | チャンネル関連イベント（GUILD_CREATEなど） |
| 25 | チャンネルメッセージイベント（AT_MESSAGE_CREATEなど） |
| 30 | グループ@メッセージイベント（GROUP_AT_MESSAGE_CREATEなど） |

## 使用例

### グループメッセージの処理

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

qqbot = sdk.adapter.get("qqbot")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "qqbot":
        return
    if event.get("detail_type") != "group":
        return

    text = event.get_text()
    group_id = event.get("group_id")

    if text == "hello":
        await qqbot.Send.To("group", group_id).Reply(
            event.get("message_id")
        ).Text("Hello!")
```

### インタラクションイベントの処理

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "qqbot":
        return

    if event.get("detail_type") == "qqbot_interaction":
        interaction_id = event.get("qqbot_interaction_id", "")
        interaction_data = event.get("qqbot_interaction_data", {})
        # インタラクションを処理...
```

### メディアメッセージの送信

```python
# 画像を送信（URL）
await qqbot.Send.To("group", group_openid).Image("https://example.com/image.png")

# 画像を送信（バイナリ）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await qqbot.Send.To("user", user_openid).Image(image_bytes)
```

### メッセージ審査結果の監視

```python
@notice.on_notice()
async def handle_audit(event):
    if event.get("platform") != "qqbot":
        return

    detail_type = event.get("detail_type")

    if detail_type == "qqbot_audit_pass":
        msg_id = event.get("qqbot_message_id")
        print(f"メッセージ審査通過: {msg_id}")

    elif detail_type == "qqbot_audit_reject":
        reason = event.get("qqbot_audit_reject_reason", "")
        print(f"メッセージ審査拒否: {reason}")



### 云湖用户端适配

# Yunhu ユーザープラットフォーム機能ドキュメント

YunhuUserAdapter は、Yunhu ユーザーアカウントプロトコルに基づいて構築されたアダプターです。ユーザーのメールアカウントでログインし、WebSocket を使用してイベントを受信し、統一されたイベント処理およびメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 1.4.0
- メンテナ: wsu2059

## 基本情報

- プラットフォーム概要：Yunhu はエンタープライズ級のインスタントメッセージングプラットフォームです。このアダプターは、**ボットアカウント**ではなく**ユーザーアカウント**を通じて対話します。
- アダプター名：YunhuUserAdapter
- マルチアカウントサポート：アカウント名による識別と複数のユーザーアカウントの設定をサポートしています。
- メソッドチェーンサポート：`.Reply()` などのメソッドチェーンによる修飾をサポートしています。
- OneBot12 互換：OneBot12 フォーマットのメッセージ送信をサポートしています。
- 通信方式：メールログインでトークンを取得し、WebSocket を使用してイベントを受信し、HTTP + Protobuf プロトコルでメッセージを送信します。
- セッションタイプ：プライベートチャット (user)、グループチャット (group)、ボットセッション (bot) をサポートしています。

## サポートするメッセージ送信タイプ

すべての送信メソッドはメソッドチェーン構文で実装されています。例えば：
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

サポートされている送信タイプは以下の通りです：
- `.Text(text: str, buttons: Optional[List] = None)`：プレーンテキストメッセージを送信します。
- `.Html(html: str, buttons: Optional[List] = None)`：HTMLフォーマットのメッセージを送信します。
- `.Markdown(markdown: str, buttons: Optional[List] = None)`：Markdownフォーマットのメッセージを送信します。
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`：画像メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`：動画メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`：音声メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートし、再生時間を自動検出します。
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`：`.Audio()` のエイリアス。
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`：ファイルメッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`：表情/ステッカーメッセージを送信します。ステッカーID、ステッカーURL、または画像のバイナリデータをサポートします。
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`：A2UIメッセージ（メッセージタイプ14）を送信します。A2UI JSONデータは text フィールドに挿入されて送信されます。
- `.Edit(msg_id: str, text: str, content_type: str = "text")`：既存のメッセージを編集します。
- `.Recall(msg_id: str)`：メッセージを取り消します。
- `.Raw_ob12(message: Union[List, Dict])`：OneBot12 フォーマットのメッセージを送信します。

### メディアファイルの処理

すべてのメディアタイプ（画像、動画、音声、ファイル）は以下の入力方法をサポートしています：
- **URL**：`"https://example.com/image.jpg"` — 自動的にダウンロードしてからアップロードします
- **ローカルパス**：`"/path/to/file.jpg"` — 自動的に読み込んでからアップロードします
- **バイナリデータ**：`open("file.jpg", "rb").read()` — 直接アップロードします

メディアファイルは自動的に七牛雲ストレージにアップロードされ、以下の機能をサポートします：
- `filetype` ライブラリによるファイルタイプと MIME の自動検出
- ファイルサイズの自動計算
- 音声ファイルの再生時間の自動検出（MP3、MP4/M4A フォーマットをサポート）

### ボタン引数の説明

`buttons` 引数はネストされたリストであり、ボタンのレイアウトと機能を表します。各ボタンオブジェクトには以下のフィールドが含まれます：

| フィールド   | タイプ | 必須     | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | はい     | ボタンに表示されるテキスト                                           |
| `actionType` | int    | はい     | アクションタイプ：<br>`1`: URLに遷移<br>`2`: コピー<br>`3`: クリックレポート            |
| `url`        | string | いいえ   | `actionType=1` の時に使用され、遷移先の URL を表します                         |
| `value`      | string | いいえ   | `actionType=2` の時、この値がクリップボードにコピーされます<br>`actionType=3` の時、この値がサブスクライバ側に送信されます |

例：
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックして遷移", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントをレポート", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きメッセージ")
```

### メソッドチェーンによる修飾（組み合わせ可能）

メソッドチェーンの修飾メソッドは `self` を返し、チェーン呼び出しをサポートしています。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.At(user_id: str)`：指定されたユーザーを @ します（テキスト形式で @user_id）。
- `.AtAll()`：全員を @ します（擬似的な全員 @ で、@all テキストを送信します）。
- `.Buttons(buttons: List)`：ボタンを追加します。

> **注意：** ユーザーアカウントは特殊であるため、管理者でなくても全員を @ することができますが、ここの `AtAll()` は全員を @ するテキストを送信するだけで、擬似的な全員 @ です。

### メソッドチェーンの呼び出し例

```python
# 基本的な送信
await yunhu_user.Send.To("user", user_id).Text("Hello")

# メッセージへの返信
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("返信とボタン付きのメッセージ")

# アカウント指定 + 返信 + ボタン
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("完全なメソッドチェーン呼び出し")
```

### OneBot12 メッセージサポート

アダプターは OneBot12 フォーマットのメッセージ送信をサポートしており、クロスプラットフォームのメッセージ互換性に役立ちます：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 フォーマットのメッセージを送信します。

```python
# OneBot12 フォーマットのメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# メソッドチェーンによる修飾と組み合わせ
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 は混合メッセージセグメントの自動グループ化処理をサポートしています：
- `text`、`mention` タイプは1つのグループにまとめて送信できます
- `image`、`video`、`audio`、`file`、`face`、`markdown`、`html`、`a2ui` などのタイプはそれぞれ独立したグループになります
- `reply` タイプは任意のグループに添付できます

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、直接 await することで送信結果を取得できます。戻り値は ErisPulse アダプターの標準化された戻り値の仕様に従っています：

```python
{
    "status": "ok",           // 実行ステータス
    "retcode": 0,             // リターンコード
    "data": {...},            // レスポンスデータ
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_user_raw": {...}   // 生のレスポンスデータ
}
```

## 固有のイベントタイプ

`platform == "yunhu_user"` の検出が必要で、その後このプラットフォームの機能を使用します。

### コアとなる相違点

1. 固有のイベントタイプ：
    - スーパーファイル共有：`yunhu_user_file_send`
    - ボット公告掲示板：`yunhu_user_bot_board`
    - メッセージ編集通知：`message_edit`
    - メッセージ削除通知：`message_delete`（取り消し）
2. 固有のメッセージセグメントタイプ：
    - フォームメッセージセグメント：`yunhu_user_form`
    - 記事メッセージセグメント：`yunhu_user_post`
    - ステッカーメッセージセグメント：`yunhu_user_sticker`
    - ボタンメッセージセグメント：`yunhu_user_button`
    - A2UI メッセージセグメント：`a2ui`
3. 拡張フィールド：
    - すべての固有フィールドは `yunhu_user_` プレフィックスで識別されます
    - 生データは `yunhu_user_raw` フィールドに保持されます
    - 生のイベントタイプは `yunhu_user_raw_type` フィールドに記録されます
    - プライベートチャットにおいて、`self.user_id` は現在ログインしているユーザーIDを表します

### サポートする生のイベントタイプ

| 生のイベントタイプ | OneBot12 タイプ | 説明 |
|-------------|--------------|------|
| `push_message` | `message` | メッセージのプッシュ（プライベートチャット、グループチャット、Botセッション） |
| `edit_message` | `notice` (`message_edit`) | メッセージ編集イベント |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | スーパーファイル共有イベント |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | ボット公告掲示板イベント |

> その他のイベントタイプ（`heartbeat_ack`、`draft_input`、`stream_message` など）は無視されます。

### OneBot12 がサポートする detail_type

| OneBot12 detail_type | Yunhu chat_type | 説明 |
|---------------------|---------------|------|
| `private` | 1 | プライベートチャットメッセージ |
| `group` | 2 | グループチャットメッセージ |
| `bot` | 3 | ボットセッション |

### メッセージイベントの例

```python
{
    "id": "event_id",
    "time": 1234567890,
    "type": "message",
    "detail_type": "group",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message": [
        {"type": "text", "data": {"text": "メッセージ内容"}}
    ],
    "alt_message": "メッセージ内容",
    "user_id": "sender_user_id",
    "user_nickname": "送信者のニックネーム",
    "group_id": "group_id",
    "message_id": "msg_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "push_message"
}
```

### メッセージ編集通知の例

```python
{
    "type": "notice",
    "detail_type": "message_edit",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "message_id": "msg_id",
    "user_id": "sender_user_id",
    "user_nickname": "送信者のニックネーム",
    "edit_time": 1234567890,
    "group_id": "group_id",
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "edit_message"
}
```

### スーパーファイル共有イベントの例

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_file_send",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "user_id": "send_user_id",
    "user_nickname": "",
    "yunhu_user_file_send": {
        "send_user_id": "送信者ID",
        "user_id": "受信ユーザーID",
        "send_type": "送信タイプ",
        "data": "ファイルデータ"
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "file_send_message"
}
```

### ボット公告掲示板イベントの例

```python
{
    "type": "notice",
    "detail_type": "yunhu_user_bot_board",
    "platform": "yunhu_user",
    "self": {
        "platform": "yunhu_user",
        "user_id": "your_user_id"
    },
    "bot_id": "bot_id",
    "bot_name": "ボット名",
    "yunhu_user_bot_board": {
        "bot_id": "bot_id",
        "chat_id": "chat_id",
        "chat_type": 1,
        "content": "公告内容",
        "content_type": 1,
        "last_update_time": 1234567890
    },
    "yunhu_user_raw": {...},
    "yunhu_user_raw_type": "bot_board_message"
}
```

### イベント処理の例

```python
from ErisPulse.Core.Event import message, notice

@message.on_message()
async def handle_yunhu_user_message(event):
    """Yunhu ユーザーメッセージを処理"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"ユーザー {user_nickname}({user_id}): {alt_message}")
    
    # メッセージセグメント内の固有タイプをチェック
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"フォームメッセージを受信: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"記事メッセージを受信: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"ステッカーメッセージを受信: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"ボタンを含むメッセージ: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"A2UIメッセージを受信: {a2ui_data}")
    
    # event.reply() を使って自動返信
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """Yunhu ユーザー通知イベントを処理"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"ユーザー {user_nickname} がメッセージ {message_id} を編集しました")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"スーパーファイル共有を受信: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"ボット {bot_name} が公告を公開しました: {board_data.get('content', '')}")
```

## 拡張フィールドの説明

- すべての固有フィールドは `yunhu_user_` プレフィックスで識別され、標準フィールドとの競合を避けます
- 生データは `yunhu_user_raw` フィールドに保持され、Yunhu プラットフォームの完全な生データへのアクセスが容易になります
- 生のイベントタイプは `yunhu_user_raw_type` フィールドに記録されます（例：`push_message`、`edit_message` など）
- `self.user_id` は現在ログインしているユーザーIDを表します（ログインレスポンスから取得）
- スーパーファイル共有は `yunhu_user_file_send` フィールドを通じてファイル共有データを提供します
- ボット公告掲示板は `yunhu_user_bot_board` フィールドを通じて公告データを提供します

### 固有のメッセージセグメントタイプ

#### フォームメッセージセグメント (yunhu_user_form)

content_type が 5 の場合、メッセージセグメントタイプは `yunhu_user_form` になります：

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "フォームデータ"
    }
}
```

#### 記事メッセージセグメント (yunhu_user_post)

content_type が 6 の場合、メッセージセグメントタイプは `yunhu_user_post` になります：

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "記事ID",
        "post_title": "記事タイトル",
        "post_content": "記事内容"
    }
}
```

| フィールド | タイプ | 説明 |
|------|------|------|
| `post_id` | string | 記事のユニーク識別子 |
| `post_title` | string | 記事のタイトル |
| `post_content` | string | 記事の内容 |

#### ステッカーメッセージセグメント (yunhu_user_sticker)

content_type が 7 の場合、メッセージセグメントタイプは `yunhu_user_sticker` になります：

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "ステッカー画像URL"
    }
}
```

| フィールド | タイプ | 説明 |
|------|------|------|
| `file_id` | string | ステッカー画像のURL |

#### ボタンメッセージセグメント (yunhu_user_button)

メッセージにボタンが含まれている場合、`yunhu_user_button` メッセージセグメントが追加されます：

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "ボタンテキスト", "actionType": 3, "value": "値"}]]
    }
}
```

#### A2UI メッセージセグメント (a2ui)

content_type が 14 の場合、メッセージセグメントタイプは `a2ui` になります：

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSONデータ"
    }
}
```

---

## マルチアカウント設定

### 設定説明

YunhuUserAdapter は複数のユーザーアカウントの同時設定と実行をサポートしています。

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket 再接続間隔（秒）
ws_timeout = 70             # WebSocket タイムアウト時間（秒）

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # ユーザーメール（必須）
password = "password1"       # ユーザーパスワード（必須）
platform = "windows"         # ログインプラットフォーム（任意、デフォルトは windows）
device_id = ""               # デバイスID（任意、未入力の場合は自動生成）
enabled = true               # 有効にするかどうか（任意、デフォルトは true）

[YunhuUserAdapter.accounts.account2



### 平台文档维护说明

# ドキュメントメンテナンス手順

このドキュメントは各アダプタの開発者がメンテナンスし、そのアダプタがOneBot12標準とどのような差異や拡張機能を持つかを説明するために使用されます。アダプタの開発者は、新バージョンをリリースする際、このドキュメントを同期して更新してください。

## 更新要件

1. プラットフォーム固有の送信メソッドとパラメータを正確に記述する
2. OneBot12標準との差異点を詳細に説明する
3. 明確なコード例とパラメータの説明を提供する
4. ドキュメントのフォーマットを統一し、ユーザーが参照しやすいようにする
5. バージョン情報とメンテナナーの連絡先をタイムリーに更新する

## ドキュメント構造の基準

### 1. 基本情報のセクション
各プラットフォームの特性ドキュメントには、以下の基本情報が含まれている必要があります：
```markdown
# [プラットフォーム名] アダプタドキュメント

アダプタ名：[アダプタクラス名]
プラットフォーム概要：[プラットフォームの簡略な紹介]
サポートプロトコル/APIバージョン：[具体的なプロトコルまたはAPIバージョン]
メンテナナー：[メンテナナー名/チーム]
対応モジュールバージョン: [バージョン番号]
```

### 2. サポートされているメッセージ送信タイプ
サポートされているすべての送信メソッドとそのパラメータを詳細に記述する：
```markdown
## サポートされているメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：
[コード例]

サポートされている送信タイプは以下の通りです：
- メソッド1：説明
- メソッド2：説明
- ...

### パラメータ説明
| パラメータ | タイプ | 説明 |
|------|------|------|
| パラメータ名 | タイプ | 説明 |
```

### 3. プラットフォーム固有のイベントタイプ
プラットフォーム固有のイベントタイプとフォーマットを詳細に説明する：
```markdown
## プラットフォーム固有のイベントタイプ

[プラットフォーム名]イベントをOneBot12プロトコルに変換します。標準フィールドはOneBot12プロトコルに完全準拠していますが、以下の差異が存在します：

### 主要な差異点
1. 固有のイベントタイプ：
   - イベントタイプ1：説明
   - イベントタイプ2：説明
2. 拡張フィールド：
   - フィールドの説明

### 特殊フィールドの例
[JSONサンプル]
```

### 4. 拡張フィールドの説明
```markdown
## 拡張フィールドの説明

- すべての固有フィールドは `[platform]_` というプレフィックスで識別されます
- 元のデータは `[platform]_raw` フィールドに保持されます
- [その他の特殊フィールドの説明]
```

### 5. 設定オプション（該当する場合）
```markdown
## 設定オプション

[プラットフォーム名] アダプタは、以下の設定オプションをサポートしています：

### 基本設定
- 設定項目1：説明
- 設定項目2：説明

### 特殊設定
- 特殊設定項目1：説明
```

## コンテンツ作成の基準

### コード例の基準
1. すべてのコード例は実行可能な完全な例でなければなりません
2. 標準的なインポート方法を使用する：
```python
from ErisPulse.Core import adapter
[アダプタインスタンス] = adapter.get("[アダプタ名]")
```
3. 様々な使用シナリオの例を提供する

### ドキュメントフォーマットの基準
1. 標準のMarkdown構文を使用する
2. 見出しの階層を明確にし、最大で4段階の見出しを使用する
3. テーブルは標準のMarkdownテーブル形式を使用する
4. コードブロックは適切な言語識別子を使用する

### バージョン更新の説明
ドキュメントを更新する際は、ドキュメントの上部にバージョン情報を更新する：
```markdown
## ドキュメント情報

- 対応モジュールバージョン: [新しいバージョン番号]
- メンテナナー: [メンテナナー情報]
- 最終更新: [日付]
```

## 品質チェックリスト

ドキュメントの更新を提出する前に、以下の項目を確認してください：

- [ ] ドキュメント構造が基準を満たしている
- [ ] すべてのコード例が正常に実行できる
- [ ] パラメータ説明が完全かつ正確である
- [ ] イベントフォーマットの例が実際の出力に一致している
- [ ] リンクや参照が正しい
- [ ] 文法とスペルミスがない
- [ ] バージョン情報が更新されている
- [ ] メンテナナー情報が正確である

## 参考ドキュメント

記述時は、一貫性を保つために以下のドキュメントを参照してください：
- [OneBot12標準ドキュメント](https://12.onebot.dev/)
- [ErisPulseコアコンセプト](../getting-started/basic-concepts.md)
- [イベント変換基準](../standards/event-conversion.md)
- [API応答仕様](../standards/api-response.md)
- [その他のプラットフォームアダプタドキュメント](./)

## コントリビューションフロー

1. [ErisPulse](https://github.com/ErisPulse/ErisPulse) リポジトリをフォークする
2. `docs/platform-features/` ディレクトリ内の該当するプラットフォームドキュメントを修正する
3. ドキュメントが上記の基準に準拠していることを確認する
4. プルリクエストを提出し、修正内容を詳細に説明する

ご不明な点がございましたら、関連するアダプタのメンテナナーに連絡するか、プロジェクトのIssuesでお尋ねください。



====
代码规范
====


### 文档字符串规范

# ErisPulse コメントスタイルガイドライン

EPのコアメソッドを作成する際、メソッドコメントを必ず追加してください。コメントのフォーマットは以下の通りです：

## モジュールドキュメントコメント

各モジュールファイルの先頭には、モジュールドキュメントを含める必要があります：
```python
"""
[モジュール名]
[モジュール機能の説明]

{!--< tips >!--}
重要な使用方法や注意事項
{!--< /tips >!--}
"""
```

## メソッドコメント

### 基本フォーマット
```python
def func(param1: type1, param2: type2) -> return_type:
    """
    [機能の説明]
    
    :param param1: [型1] [パラメータの説明1]
    :param param2: [型2] [パラメータの説明2]
    :return: [戻り値の型] [戻り値の説明]
    """
    pass
```

### 完全フォーマット（複雑なメソッドに適用）
```python
def complex_func(param1: type1, param2: type2 = None) -> Tuple[type1, type2]:
    """
    [機能の詳細な説明]
    [複数行の説明を含めることができます]
    
    :param param1: [型1] [パラメータの説明1]
    :param param2: [型2] [オプションパラメータの説明2] (デフォルト: None)
    
    :return: 
        type1: [戻り値パラメータ1の説明]
        type2: [戻り値パラメータ2の説明]
    
    :raises ErrorType: [エラーの説明]
    """
    pass
```

## 特殊タグ（APIドキュメントの生成に使用）

メソッドコメントに以下の内容が含まれている場合、APIドキュメントの構築時に対応する効果が生じます：

| タグフォーマット | 役割 | 例 |
|---------|------|------|
| `{!--< internal-use >!--}` | 内部使用としてマークし、ドキュメントを生成しない | `{!--< internal-use >!--}` |
| `{!--< ignore >!--}` | このメソッドを無視し、ドキュメントを生成しない | `{!--< ignore >!--}` |
| `{!--< deprecated >!--}` | 非推奨メソッドとしてマークする | `{!--< deprecated >!--} new_func()を使用してください` |
| `{!--< experimental >!--}` | 実験的機能としてマークする | `{!--< experimental >!--} 不安定な可能性があります` |
| `{!--< tips >!--}...{!--< /tips >!--}` | 複数行のヒント内容 | `{!--< tips >!--}\n重要なヒント内容\n{!--< /tips >!--}` |
| `{!--< tips >!--}` | 単一行のヒント内容 | `{!--< tips >!--} 注意: このメソッドは事前に初期化する必要があります` |

## ベストプラクティス

1. **型アノテーション**：Pythonの型アノテーション構文を使用する
   ```python
   def func(param: int) -> str:
   ```

2. **パラメータの説明**：オプションパラメータにはデフォルト値を明記する
   ```python
   :param timeout: [int] タイムアウト時間(秒) (デフォルト: 30)
   ```

3. **戻り値**：複数の戻り値には`Tuple`を使用するか、明確に説明する
   ```python
   :return: 
       str: ステータス情報
       int: ステータスコード
   ```

4. **例外の説明**：`:raises`を使用してスローされる可能性のある例外をマークする
   ```python
   :raises ValueError: パラメータが無効な場合にスローされます
   ```

5. **内部メソッド**：非公開APIには`{!--< internal-use >!--}`タグを追加する

6. **非推奨メソッド**：非推奨メソッドをマークし、代替案を提供する
   ```python
   {!--< deprecated >!--} new_method()を使用してください | 2025-07-09

