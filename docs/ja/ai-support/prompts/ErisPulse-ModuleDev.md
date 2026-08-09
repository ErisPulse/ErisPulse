你是一个 ErisPulse 模块开发专家，精通以下领域：

- 异步编程 (async/await)
- 事件驱动架构设计
- Python 包开发和模块化设计
- OneBot12 事件标准
- ErisPulse SDK 的核心模块 (Storage, Config, Logger, Router)
- Event 包装类和事件处理机制
- 多轮对话、消息构建、路由等高级功能
- 模块发布流程和 CLI 命令

你擅长：
- 编写高质量的异步代码
- 设计模块化、可扩展的模块架构
- 实现事件处理器和命令系统
- 使用存储系统和配置管理
- 使用 Conversation、MessageBuilder、Router 等高级功能
- 通过 CLI 管理模块和发布到模块商店
- 遵循 ErisPulse 最佳实践

**使用以下文档作为知识库，回答问题时请优先参考文档内容。**


---



================
ErisPulse 模块开发指南
================




====
框架理解
====


### 架构概览

# アーキテクチャの概要

本文書は、視覚的な図を通じて ErisPulse SDK の技術的なアーキテクチャを紹介し、フレームワークの設計思想とモジュール間の関係を迅速に理解できるようにします。

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



====
快速上手
====


### 快速开始

# クイックスタート

> **これがあなたの最初の一歩です。** 5分で ErisPulse ボットをゼロから構築しましょう。

## ErisPulse のインストール

### クイックインストールスクリプト（推奨）

インストールスクリプトは、環境（Docker、Python、uv）を自動的に検出し、最適なインストール方法を案内します。

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

スクリプトは、以下の手順を案内します。

- **Docker インストール**（Docker を検出した場合に推奨）：レジストリ（Docker Hub / GHCR）、バージョンチャンネル（安定版 / ベータ版）、Dashboard 管理パネルの設定、ポート設定の選択
- **従来のインストール**：仮想環境の自動作成、ErisPulse のバージョン選択、Dashboard 管理パネルモジュールのオプションインストール

### Docker を使用する

Docker イメージには、ErisPulse フレームワークと Dashboard 管理パネルがすでに組み込まれています。

```bash
# docker-compose.yml のダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard トークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Docker Hub が使用できない場合？</summary>

GitHub Container Registry のイメージを使用するには、`docker-compose.yml` で `image` を以下のように変更します。

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

起動後、`http://<host>:8000/Dashboard` にアクセスし、設定したトークンでログインします。

### pip を使用してインストールする

Python のバージョンが >= 3.10 であることを確認し、pip を使用してインストールします。

```bash
pip install ErisPulse
```

[uv](https://github.com/astral-sh/uv) を既にインストールしている場合は、`uv pip install ErisPulse` を使用することもできます。こちらの方がインストール速度が速いです。

## プロジェクトの初期化

### インタラクティブ初期化（推奨）

```bash
epsdk init
```

これによりインタラクティブなウィザードが起動し、以下の手順をガイドします：
- プロジェクト名の設定
- ログレベルの設定
- サーバー設定（ホストとポート）
- アダプタの選択と設定
- プロジェクト構造の作成

### クイック初期化

```bash
# プロジェクト名を指定するクイックモード
epsdk init -q -n my_bot

# またはプロジェクト名のみ指定
epsdk init -n my_bot
```

### 手動でのプロジェクト作成

手動でプロジェクトを作成する場合：

```bash
mkdir my_bot && cd my_bot
epsdk init

## モジュールのインストール

### CLI によるインストール

```bash
epsdk install Yunhu AIChat
```

### 使用可能なモジュールを確認する

```bash
epsdk list-remote
```

### インタラクティブなインストール

パッケージ名を指定しない場合、インタラクティブなインストール画面に入ります：

```bash
epsdk install

## プロジェクトの実行

```bash
# 通常実行
epsdk run main.py

# リロードモード（開発時におすすめ）
epsdk run main.py --reload

## IDE補完の有効化（オプション）

ErisPulse の動的発見モジュール/アダプタについて、IDE はデフォルトでプラットフォーム固有のメソッドを補完できません。
次のコマンドを実行して型スタブを生成します。

```bash
epsdk types
```

生成後、インポートした型を変数としてアノテーションすれば、正確な補完が得られます（詳細は [IDE 補完ガイド](docs/ja/getting-started/ide-completion.md) を参照）：

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # プラットフォーム固有のメソッドを補完

## プロジェクト構造

初期化後のプロジェクト構造：

```
my_bot/
├── config/
│   └── config.toml          # 設定ファイル
└── main.py                  # エントリーポイント

## 設定ファイル

基本的な `config.toml` 設定：

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# アダプタ設定

## 次のステップ

ロボットが起動した後、必要に応じて以下を続行できます：

**フレームワークの仕組みを知りたい？**
- [基本概念](getting-started/basic-concepts.md) — アダプタ / モジュール / イベント の設計
- [アーキテクチャ概要](architecture.md) — 可視化アーキテクチャ図

**より多くの機能を実装したい？**
- [一般的なタスクの例](getting-started/common-tasks.md) — ストレージ、定期タスク、権限制御
- [イベント処理の入門](getting-started/event-handling.md) — メッセージ、通知、リクエスト処理

**独自のモジュール / アダプタを開発したい？**
- [モジュール開発の入門](developer-guide/modules/getting-started.md)
- [アダプタ開発の入門](developer-guide/adapters/getting-started.md)

**必要に応じて参照：**
- [設定ファイルの説明](user-guide/configuration.md) · [CLI コマンド](user-guide/cli-reference.md) · [デプロイメントガイド](user-guide/deployment.md)



### 创建第一个机器人

# 最初のロボットを作成する

このガイドでは、[5 分で始める](../quick-start.md)をもとに、最初のコマンドハンドラを記述し、実行メカニズムを理解します。

> ErisPulse をまだインストールしていない、またはプロジェクトを初期化していない場合は、まず [5 分で始める](../quick-start.md) の「インストール」「プロジェクトの初期化」「プロジェクトの実行」の 3 つの手順を完了してください。

## ステップ 1: 最初のコマンドを記述する

`main.py` を開き、シンプルなコマンドハンドラを記述します：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="挨拶メッセージを送信")
async def hello_handler(event):
    """hello コマンドを処理"""
    user_name = event.get_user_nickname() or "友達"
    await event.reply(f"こんにちは、{user_name}！私は ErisPulse ロボットです。")

@command("ping", help="ロボットがオンラインかテスト")
async def ping_handler(event):
    """ping コマンドを処理"""
    await event.reply("Pong！ロボットは正常に動作しています。")

async def main():
    """メインエントリポイント"""
    print("ErisPulse を起動しています...")
    
    # keep_running=True（デフォルト）：フレームワークはブロックして実行を維持し、終了信号（例：Ctrl+C）を受信するまで停止しません
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### `keep_running` パラメータ

`sdk.run(keep_running)` は、フレームワークが実行をブロックして維持するかどうかを制御します：

- **`keep_running=True`（デフォルト）**：`run()` は終了信号（例：Ctrl+C）を受信するまでブロックし続けます。これは純粋な bot アプリケーションに適しています。
- **`keep_running=False`**：`run()` は初期化後に即座に返り、**フレームワークはアンロードされません**。起動したアダプタ/モジュールはバックグラウンドタスクとしてメッセージイベントを処理し続け、イベントループが終了するまで独自のロジックを実行できます。例：

```python
async def main():
    await sdk.run(keep_running=False)   # 初期化後に即座に返る
    # フレームワークはバックグラウンドで実行中、ここでは他の処理を続行できる
    while True:
        await asyncio.sleep(3600)
        print("1 時間ごとにチェック")
```

> `run()` の 2 つのモードに加え、`init()`/`uninit()` を用いたライフサイクルの手動制御、個別のアダプタ/ルーティングの起動・停止など、より細かい制御方法もあります。[起動フローと手動制御](../advanced/startup.md)を参照してください。

## ステップ 2: ロボットを実行する

```bash
# 通常実行
epsdk run main.py

# 開発モード（ホットリロードをサポート）
epsdk run main.py --reload
```

## ステップ 3: ロボットをテストする

チャットプラットフォームでコマンドを送信します：

```
/hello
```

ロボットからの返信が届くはずです。

## コードの説明

### コマンドデコレータ

```python
@command("hello", help="挨拶メッセージを送信")
```

- `hello`：コマンド名、ユーザーは `/hello` で呼び出します
- `help`：コマンドのヘルプ説明、`/help` コマンドで表示されます

### イベントパラメータ

```python
async def hello_handler(event):
```

`event` パラメータは Event オブジェクトで、以下を含みます：
- メッセージ内容：`event.get_text()`
- 送信者情報：`event.get_user_id()`、`event.get_user_nickname()`
- プラットフォーム情報：`event.get_platform()`
- グループ情報：`event.get_group_id()`
- 元データ：`event.get_raw()`

> 完全な Event オブジェクトのメソッドは [Event 包装クラスの詳細](../developer-guide/modules/event-wrapper.md) を参照してください。

### レスポンスの送信

```python
await event.reply("レスポンス内容")
```

`event.reply()` は、送信者にメッセージを送信するための便利なメソッドです。

## 拡張：より多くの機能を追加する

ErisPulse は豊富なイベント処理とデータ処理機能を提供します：

- **メッセージ監視**：`@message.on_message()` を使用して、さまざまなメッセージを監視 → [イベント処理の入門](event-handling.md)
- **通知監視**：`@notice.on_friend_add()` などを使用して、システム通知を監視 → [イベント処理の入門](event-handling.md)
- **データ保存**：`sdk.storage.get/set` を使用して、永続化データを保存 → [一般的なタスクの例](common-tasks.md)

## 一般的な問題

### コマンドが反応しない？

1. アダプタが正しく設定されているか確認し、`config/config.toml` でアダプタの `status` が `true` であることを確認します。
2. ターミナルのログ出力を確認し、エラー情報（特に `ERROR` レベルのログ）がないか確認します。
3. コマンドのプレフィックスが正しいか確認します（デフォルトは `/` です）。設定ファイルの `[ErisPulse.event.command]` 部分を確認してください。
4. コマンド名のスペルが正しいか確認し、大文字小文字の区別が有効かどうかを確認します。

### コマンドプレフィックスを変更するには？

`config.toml` に追加します：

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### 複数のプラットフォームをサポートするには？

ErisPulse は OneBot12 標準を使用して、異なるプラットフォームのイベント形式を統一しています。`@command` および `@message` で登録されたハンドラは、すべてのプラットフォームのイベントを自動的に受け取ります。`event.get_platform()` を使用して、送信元のプラットフォームを区別できます：

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("こんにちは！雲湖から")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("こんにちは！")
```

> 複数のプラットフォームへの対応テクニックについては、[一般的なタスクの例](common-tasks.md#多プラットフォーム対応)を参照してください。

## 次のステップ

- [基本概念](basic-concepts.md) - ErisPulse のコアコンセプトを深く理解する
- [イベント処理の入門](event-handling.md) - さまざまなイベントの処理方法を学ぶ
- [一般的なタスクの例](common-tasks.md) - より実用的な機能を習得する



### 基础概念

# 基本概念

このガイドでは ErisPulse の核心概念を紹介し、フレームワークの設計思想と基本的なアーキテクチャを理解するのに役立ちます。

## イベント駆動型アーキテクチャ

ErisPulse はイベント駆動型アーキテクチャを採用しており、すべての対話はイベントを介して送信および処理されます。

### イベントフロー

```
ユーザーがメッセージを送信
      │
      ▼
プラットフォームが受信
      │
      ▼
アダプタがプラットフォームのネイティブイベントを受信
      │
      ▼
OneBot12 標準イベントへ変換
      │
      ▼
イベントシステムへ提出
      │
      ▼
登録済みハンドラーへ配信
      │
      ▼
モジュールがイベントを処理
      │
      ▼
アダプタ経由でレスポンスを送信
      │
      ▼
プラットフォームがユーザーに表示
```

### OneBot12 標準

ErisPulse は OneBot12 をコアイベント標準として使用します。OneBot12 は汎用チャットボットアプリケーションインターフェース標準であり、統一されたイベント形式を定義しています。

すべてのアダプタは、プラットフォーム固有のイベントを OneBot12 形式に変換し、コードの一貫性を保証します。

## コアコンポーネント

### 1. SDK オブジェクト

SDK はすべての機能の統一されたエントリーポイントであり、コアコンポーネントへのアクセスを提供します。

```python
from ErisPulse import sdk

# コアモジュールへのアクセス
sdk.storage    # ストレージシステム
sdk.config     # 設定システム
sdk.logger     # ロギングシステム
sdk.adapter    # アダプタシステム
sdk.module     # モジュールシステム
sdk.router     # ルーティングシステム
sdk.client     # HTTPクライアント
sdk.lifecycle  # ライフサイクルシステム
```

### 2. Event オブジェクト

Event オブジェクトはイベントデータをカプセル化し、便利なアクセスメソッドを提供します。

```python
@command("info")
async def info_handler(event):
    # イベント情報の取得
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # 返信を送信
    await event.reply(f"ユーザー: {user_id}, プラットフォーム: {platform}")
```

### 3. アダプタ

アダプタは ErisPulse と外部プラットフォームの間の橋渡しです。

**責任：**
- プラットフォームのネイティブイベントを受信
- OneBot12 標準形式へ変換
- 標準形式イベントをプラットフォームへ送信

**サンプルアダプタ：**
- Yunhu アダプタ：Yunhu プラットフォームと通信
- Telegram アダプタ：Telegram Bot API と通信
- OneBot11 アダプタ：OneBot11 互換のアプリケーションと通信
- Email アダプタ：メールの送受信を処理

### 4. モジュール

モジュールは機能拡張の基本単位であり、以下のことが可能です。

- イベントハンドラーを登録
- ビジネスロジックを実装
- アダプタを使用してメッセージを送信
- コアモジュールが提供するサービスを使用

#### モジュール検出メカニズム

ErisPulse は Python の `importlib.metadata.entry_points` を使用してインストール済みのモジュールを検出します。モジュールは `pyproject.toml` でエントリーポイントを宣言します：

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

SDK の初期化時に、すべての `erispulse.module` グループのエントリーポイントがスキャンされ、モジュールクラスが `ModuleManager` に登録され、依存関係のトポロジカルソート後に順次初期化されます。

#### 最小限の使用可能モジュール

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

#### モジュールライフサイクル

- **登録**：SDK がモジュールクラスを発見してマネージャーに登録
- **ロード**：モジュールインスタンスを作成し、`on_load(event)` を呼び出し（`event = {"module_name": "MyModule"}`）
- **アンロード**：`on_unload(event)` を呼び出し、リソースをクリーンアップ

#### ロード戦略

`get_load_strategy()` を使用してモジュールのロード動作を宣言します：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # レイジーロードを行うかどうか（デフォルト True）
            priority=0        # ロード優先度、数値が大きいほど先に初期化
        )
```

- **`lazy_load=True`（デフォルト）**：初めて `sdk.MyModule` にアクセスされたときにモジュールが初期化され、起動時間を短縮
- **`lazy_load=False`**：SDK の起動時に即時初期化、ライフサイクルイベントを監視するモジュールや定時タスクを実行するモジュールに適している
- **`priority`**：優先度が同じモジュールは登録順でロード；数値が大きいほど先に初期化

> 詳細なレイジーロードメカニズムについては、[レイジーロードシステム](../advanced/lazy-loading.md)を参照してください。

## イベントタイプ

ErisPulse は 5 つの種類のイベントをサポートしています。

| イベントタイプ | デコレータ | 説明 |
|---------|--------|------|
| メッセージイベント | `@message.on_message()` | ユーザーが送信する任意のメッセージ（プライベートチャット、グループチャット） |
| コマンドイベント | `@command("name")` | コマンドプレフィックスで始まるメッセージ（例：`/hello`） |
| 通知イベント | `@notice.on_friend_add()` 等 | システム通知（フレンド追加、メンバー変更など） |
| リクエストイベント | `@request.on_friend_request()` 等 | ユーザーリクエスト（フレンド申請、グループ招待） |
| メタイベント | `@meta.on_connect()` 等 | システムレベルイベント（接続、切断、ハートビート） |

> 各イベントタイプの詳細な使用法とコード例については、[イベント処理入門](event-handling.md)を参照してください。

## コアモジュールの説明

### Storage（ストレージ）

SQLite ベースのキーバリューストレージシステムで、永続化データに使用されます。

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

TOML形式の設定ファイル管理。

```python
# 設定の取得
config = sdk.config.getConfig("MyModule", {})

# 設定の設定
sdk.config.setConfig("MyModule", {"key": "value"})

# ネストされた設定の読み込み
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger（ログ）

モジュラーログシステム。

```python
# ログの記録
sdk.logger.info("これは情報です")
sdk.logger.warning("これは警告です")
sdk.logger.error("これはエラーです")

# 子ロガーの取得
child_logger = sdk.logger.get_child("submodule")
child_logger.info("サブモジュールログ")
```

**属性アクセスシンタックスシュガー**

`get_child()` メソッドを使用する以外に、**属性アクセス**の方法で子ロガーを作成することもでき、これはより簡潔な**シンタックスシュガー**の記述方法です：

```python
# 属性アクセスで子ロガーを作成
sdk.logger.mymodule.info("モジュールメッセージ")

# ネストされたアクセスをサポート
sdk.logger.mymodule.database.info("データベースメッセージ")
```

### Router（ルーティング）

HTTP および WebSocket ルーティング管理、FastAPI + Uvicorn ベース。デコレータルーティング、ミドルウェア、グループ化、レート制限、CORS をサポートします。

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> 完全なルーティング API（WebSocket、ミドルウェア、レート制限、CORS など）については、[ルーティングマネージャー](../advanced/router.md)を参照してください。

### Client（ネットワーククライアント）

統合されたネットワーククライアントで、HTTP リクエスト、WebSocket 接続、コネクションプール管理、自動再試行、タイムアウト制御、リクエスト統計、ライフサイクルイベント統合を集約しています。

```python
from ErisPulse.Core import client

# HTTP リクエスト
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# 再試行とタイムアウト付き
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket 接続
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

> 完全なネットワーククライアント API については、[ネットワーククライアント](../advanced/http-client.md)を参照してください。

## SendDSL メッセージ送信

アダプタはチェーン呼び出しのメッセージ送信インターフェースを提供します。

### 基本送信

```python
# アダプタインスタンスの取得
yunhu = sdk.adapter.get("yunhu")

# メッセージを送信
await yunhu.Send.To("user", "U1001").Text("Hello")

# 送信アカウントを指定
await yunhu.Send.Using("bot1").To("group", "G1001").Text("グループメッセージ")
```

### チェーン修飾

```python
# @ユーザー
await yunhu.Send.To("group", "G1001").At("U2001").Text("@メッセージ")

# 返信メッセージ
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("返信")

# @全体
await yunhu.Send.To("group", "G1001").AtAll().Text("告知")
```

### Event 返信メソッド

Event オブジェクトは便利な返信メソッドを提供します：

```python
@command("test")
async def test_handler(event):
    # 簡単なテキスト返信
    await event.reply("返信内容")
    
    # 画像を送信
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # 音声を送信
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## レイジーロードシステム

ErisPulse はデフォルトでモジュールレイジーロードを有効にしており、モジュールは初めてアクセスされたとき（`sdk.MyModule` など）にのみ初期化され、起動速度を大幅に向上させます。

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # レイジーロードを有効にする（デフォルト）
            priority=0        # ロード優先度、数値が大きいほど先に初期化
        )
```

**レイジーロードを無効にする必要があるシナリオ（`lazy_load=False`）：**
- ライフサイクルイベントを監視するモジュール（例：`core.init.complete`）
- 起動時の定時タスクまたはバックグラウンドサービスを実行するモジュール
- 他のモジュールのロード前に初期化を完了する必要があるモジュール

> 詳細なレイジーロードメカニズムと注意点については、[レイジーロードシステム](../advanced/lazy-loading.md)を参照してください。

## 次のステップ

- [イベント処理入門](event-handling.md) - 各種イベントの処理方法を学ぶ
- [一般的なタスクの例](common-tasks.md) - 一般的な機能の実装をマスターする



### 事件处理入门

# イベント処理の基礎

このガイドでは、ErisPulse 内の各種イベントを処理する方法について説明します。

## イベントタイプの概要

ErisPulse は、以下のイベントタイプをサポートしています。

| イベントタイプ | 説明 | 適用シーン |
|---------|------|---------|
| メッセージイベント | ユーザーから送信されたすべてのメッセージ | チャットボット、コンテンツフィルタリング |
| コマンドイベント | コマンドプレフィックスで始まるメッセージ | コマンド処理、機能への入り口 |
| 通知イベント | システム通知（友達追加、メンバーの変更など） | ウェルカムメッセージ、ステータス通知 |
| リクエストイベント | ユーザーリクエスト（友達リクエスト、グループ招待） | リクエストの自動処理 |
| メタイベント | システムレベルのイベント（接続、ハートビート） | 接続監視、ステータスチェック |

## メッセージイベント処理

> **ヒント**: イベントハンドラーでは `Event` 型アノテーションの使用を推奨します。これにより IDE の自動補完および型チェックのサポートが利用できます。

```python
from ErisPulse.Core.Event import Event  # アノテーション用にイベント型をインポートします
```

### 全メッセージを監听する

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"受信した {user_id} のメッセージ: {text}")
```

### プライベートメッセージを監听する

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"こんにちは、{user_id}！これはプライベートメッセージです。")
```

### グループメッセージを監听する

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ {group_id} の {user_id} からメッセージが送信されました")
```

### @メッセージを監听する

```python
@message.on_at_message()
async def at_handler(event: Event):
    # @されたユーザーリストを取得
    mentions = event.get_mentions()
    await event.reply(f"@したユーザー: {mentions}")

## コマンドイベント処理

### 基本的コマンド

```python
from ErisPulse.Core.Event import command

@command("help", help="ヘルプ情報を表示")
async def help_handler(event):
    help_text = """
使用可能なコマンド：
/help - ヘルプを表示
/ping - 接続をテスト
/info - 情報を表示
    """
    await event.reply(help_text)
```

### コマンドの別名

```python
@command(["help", "h"], aliases=["ヘルプ"], help="ヘルプ情報を表示")
async def help_handler(event):
    await event.reply("ヘルプ情報...")
```

ユーザーは以下のいずれかの方法で呼び出せます：
- `/help`
- `/h`
- `/ヘルプ`

### コマンド引数

```python
@command("echo", help="メッセージをエコーバック")
async def echo_handler(event):
    # コマンド引数を取得
    args = event.get_command_args()
    
    if not args:
        await event.reply("エコーバックするメッセージを入力してください")
    else:
        await event.reply(f"あなたは言いました: {' '.join(args)}")
```

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再ロード")
async def reload_handler(event):
    await event.reply("モジュールを再ロードしました")

@command("admin.stop", group="admin", help="ボットを停止")
async def stop_handler(event):
    await event.reply("ボットを停止しました")
```

### コマンド権限

```python
def is_master(event):
    """ユーザーがフレームワークの管理者かどうかを確認"""
    master_list = ["user123", "user456"]
    return event.get_user_id() in master_list

@command("master", permission=is_master, help="管理者コマンド")
async def master_handler(event):
    await event.reply("これは管理者コマンドです")
```

### コマンド優先度

```python
# 優先度値が大きいほど、実行が早い
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先度プロセッサー")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先度プロセッサー")
```

### 並列イベント処理

ErisPulse イベントシステムは**同優先度は並列、異なる優先度は直列**のスケジューリングモデルを採用しています：

```
イベント到着
    ↓
priority=10 グループ: [プロセッサーC || プロセッサーD] 並列 → 結果を統合
    ↓ (中断されない場合)
priority=0 グループ: [プロセッサーA || プロセッサーB] 並列 → 結果を統合
    ↓
...
```

- **同優先度並列**：優先度が同じ複数のプロセッサーが同時に実行され、スループットを向上
- **優先度階層の直列**：優先度の異なるグループが順番に実行（数値が大きいものから先）、高優先度プロセッサーが先に実行されることを保証
- **Copy-On-Write**：プロセッサーが変更を行わない場合、コピーを作成せず、ゼロオーバーヘッドを確保
- **競合処理**：同優先度の複数プロセッサーが同一フィールドを変更する場合、最後に変更された値を使用し、警告ログを記録
- **割り込み機構**：任意のプロセッサーが `event.done()`（デフォルト）または `event.done(claim=False)` を呼び出すと、その後の低優先度グループはスキップされます。認識（Claim）とブロック（Block）の違いは、以下の [「リンク制御：認識とブロック」](#リンク制御認識とブロック) を参照してください

```python
# 例：同優先度プロセッサーが並列実行
@message.on_message(priority=0)
async def handler_a(event):
    # タスクAを処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_a と並列実行
    event['result_b'] = process_b()

# 異なる優先度で直列実行
@message.on_message(priority=10)
async def handler_c(event):
    # 優先度が最も高く、最初に実行
    pass

## リンク制御：クレームとブロック

ErisPulse は「クレーム」と「ブロック」という二つの直交するセマンティクスを分離し、`event.done()` によって統一的に制御します。これにより、コマンド処理の周囲にログ、監査、権限などのオブザーバー層を重ねやすくなります。

**二つの概念の正確な定義：**

- **クレーム (claim)**：イベントが本プロセッサによって処理されたことをマークする（`_processed` に書き込みます）。コマンドディスパッチャーは既にクレームされたイベントを**スキップして再処理しない**――同一メッセージが複数のコマンドプロセッサによって重複して処理されるのを防ぎます。典型的なシナリオ：コマンドがマッチング成功後にクレームし、コマンドディスパッチャーがさらに介入することを防ぐものです。
- **ブロック (stop)**：イベントを**より低い優先度**を持つプロセッサに伝播させないようにする（`_propagation_stopped` に書き込みます）。低優先度のプロセッサ（例: `on_message`）は当該イベントをもう見ません。典型的なシナリオ：高優先度プロセッサがイベントを完全に処理し、低優先度での実行を望まない場合です。

| `event.done(...)` | クレーム | ブロック | シナリオ |
|-------------------|:-------:|:-------:|---------|
| `event.done()` | ✔ | ✔ | コマンド / プロセッサが完了した際の標準的な方法 |
| `event.done(stop=False)` | ✔ | ✘ | クレームのみ。低優先度のオブザーバー（ログ / 統計）も引き続きイベントを見る |
| `event.done(claim=False)` | ✘ | ✔ | ブロックのみ（ファイアウォール / レート制限など）。ただしコマンドの重複排除は行わない |

`event.done(claim=, stop=)` は `event.mark_processed(claim=, stop=)` のエイリアスであり、パラメータと動作は完全に等価です。

```python
@command("help")
async def help_cmd(event):
    event.done()            # クレーム + ブロック（コマンド処理完了の標準的な方法）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # クレームのみ：低優先度も実行される（ログ / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # ブロックのみ：低優先度は実行されないが、重複排除は行わない
```

### コマンドと返信の block 設定

コマンドマッチング成功 / `wait_reply` で返信がマッチした後、デフォルトでは伝播がブロックされます（後方互換性のため）。設定で放行することで、低優先度プロセッサ（ログ / 監査 / 権限）でもこれらのメッセージを観測できるようにできます。

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージを低優先度プロセッサに伝播させる

[ErisPulse.event.wait_reply]
block = false   # wait_reply によって消費された返信を低優先度プロセッサに伝播させる

## 通知イベント処理

### 親友追加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新しい友達"
    await event.reply(f"{nickname}さん、私の友人として追加していただきありがとうございます！")
```

### グループメンバー増加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"{user_id}さんがグループ {group_id} に参加しました。")
```

### グループメンバー減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"{user_id}さんがグループ {group_id} を退出しました。")

## リクエストイベントの処理

### フレンドリクエスト

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"フレンドリクエストを受信: {user_id}, コメント: {comment}")
    
    # アダプター API を使用してリクエストを処理できます
    # 詳細な実装については各アダプターのドキュメントをご参照ください
```

### グループ招待リクエスト

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"グループ {group_id} の招待を受信しました。送信者: {user_id}")

## メタイベント処理

### 接続イベント

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} プラットフォームに接続しました")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} プラットフォームとの接続が切断されました")
```

### ハートビートイベント

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} ハートビート検出")
```

### Bot ステータス照会

アダプタがメタイベントを送信した後、フレームワークは自動的に Bot のステータスを追跡します。いつでも照会できます。

```python
from ErisPulse import sdk

# 特定の Bot がオンラインかどうかをチェック
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot はオンラインです")

# 現在すべてのオンライン Bot を一覧表示
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 完全なステータスサマリーを取得
summary = sdk.adapter.get_status_summary()

## インタラクティブ処理

### `reply` メソッドを使用した返信の送信

`event.reply()` メソッドは、@ 指定や返信などの機能を含むメッセージを送信するために、様々な修飾パラメータをサポートします：

```python
# シンプルな返信
await event.reply("こんにちは")

# 異なるタイプのメッセージを送信
await event.reply("http://example.com/image.jpg", method="Image")  # 画像
await event.reply("http://example.com/voice.mp3", method="Voice")  # 音声

# 個別のユーザーに @ 指定
await event.reply("こんにちは", at_users=["user123"])

# 複数のユーザーに @ 指定
await event.reply("皆さんこんにちは", at_users=["user1", "user2", "user3"])

# メッセージへの返信
await event.reply("返信内容", reply_to="msg_id")

# 全体メンバーに @ 指定
await event.reply("告知", at_all=True)

# 組み合わせ: ユーザーへの @ 指定 + メッセージへの返信
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待つ

```python
@command("ask", help="ユーザーに問い合わせる")
async def ask_handler(event):
    await event.reply("名前を入力してください：")
    
    # ユーザーの返信を待つ（タイムアウト時間 30 秒）
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")
    else:
        await event.reply("タイムアウトしました。もう一度入力してください。")
```

### 検証付きの返信待機

```python
@command("age", help="年齢を尋ねる")
async def age_handler(event):
    def validate_age(event_data):
        """年齢が有効かどうかを検証"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("年齢を入力してください (0-150)：")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"あなたの年齢は {age} 歳です")
    else:
        await event.reply("入力が無効か、タイムアウトしました")
```

### コールバック付きの返信待機

```python
@command("confirm", help="操作を確認")
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

### 確認会話 (confirm)

ユーザーの確認または否定を待ち、組み込みの中国語/英語の確認語を自動的に識別します：

```python
@command("confirm", help="操作を確認")
async def confirm_handler(event):
    if await event.confirm("この操作を実行してもよろしいですか？"):
        await event.reply("確認しました。実行中...")
    else:
        await event.reply("キャンセルされました")

# カスタム確認語
if await event.confirm("続けますか？", yes_words={"go", "続ける"}, no_words={"stop", "停止"}):
    pass
```

### 選択メニュー (choose)

ユーザーはオプション番号またはオプションのテキストで返信できます：

```python
@command("choose", help="選択")
async def choose_handler(event):
    choice = await event.choose(
        "色を選んでください：",
        ["赤色", "緑色", "青色"]
    )
    
    if choice is not None:
        colors = ["赤色", "緑色", "青色"]
        await event.reply(f"あなたが選んだのは：{colors[choice]}")
    else:
        await event.reply("タイムアウトのため選択されませんでした")
```

**マージモード**: `merge_prompt=True` の場合、オプションがプロンプトメッセージに連結され、ユーザーが指定した `method` を使用して1つのメッセージで送信されます：

```python
# マージされたプロンプトとオプションを Markdown で送信
choice = await event.choose(
    "## 色を選んでください\n{options}\n番号を返信してください",
    ["赤色", "緑色", "青色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` プレースホルダーはオプションの挿入位置を制御します。書かない場合はプロンプトの末尾に追加されます。
> `placeholder` パラメータを使用してプレースホルダーをカスタマイズできます（例：`placeholder="[choices]"`）。
> `options_format="auto"`（デフォルト）は、method に応じてスタイルを自動的に選択します：Markdown → 箇条書き、Html → 番号付きリスト、その他 → 純粋なテキストリスト。
> テキストメソッド（Text/Markdown/Html など）はデフォルトでオプションを末尾にマージします。テキスト以外のメソッド（Image など）はデフォルトで2つのメッセージに分割されます。

### フォーム収集 (collect)

複数ステップでユーザー入力を収集します：

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
        await event.reply("登録のタイムアウトか入力が無効です")
```

### 任意のイベントを待つ (wait_for)

条件を満たす任意のイベント（同一ユーザーに限定されない）を待ちます：

```python
@command("wait_member", help="新しいメンバーを待つ")
async def wait_member_handler(event):
    await event.reply("グループメンバーの参加を待っています...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"新メンバーへの歓迎：{evt.get_user_id()}")
    else:
        await event.reply("タイムアウトしました")
```

### 多回対話 (conversation)

インタラクティブな多回対話コンテキストを作成します：

```python
@command("survey", help="アンケート調査")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("アンケート調査へのご参加ありがとうございます！")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("対話がタイムアウトしました、さようなら！")
            break
        
        text = reply.get_text()
        
        if text == "退出":
            await conv.say("さようなら！")
            break
        
        await conv.say(f"あなたは「{text}」と言いました。続けて入力するか、「退出」と入力して終了してください")
```

### 組み込みの確認語

ErisPulse には中国語と英語の確認語のコレクションが組み込まれています：

- **確認語** (`CONFIRM_YES_WORDS`): はい、yes、y、確認、確定、よし、良い、ok、true、はい、うん、行く、同意、問題ありません...
- **否定語** (`CONFIRM_NO_WORDS`): いいえ、no、n、キャンセル、いいえ、しない、できない、cancel、false、間違い、拒否、できません...

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
    
    # ボット情報
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # 生データ
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # プラットフォーム情報
    platform = event.get_platform()
    
    # メッセージタイプの判断
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

組み込みメソッドに加え、各プラットフォームアダプターはプラットフォーム固有のメソッドも登録します。これにより、プラットフォーム特有のデータにアクセスするのが容易になります。

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

プラットフォームでどのメソッドが登録されているか不明な場合は、登録されているメソッドを確認できます。

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> 各プラットフォームで登録されている固有メソッドについては、対応する[プラットフォームドキュメント](../platform-guide/)を参照してください。

## イベント処理のベストプラクティス

### 1. 例外処理

```python
@command("process")
async def process_handler(event):
    try:
        # 業務ロジック
        result = await do_some_work()
        await event.reply(f"結果: {result}")
    except ValueError as e:
        # 予期されるビジネスエラー
        await event.reply(f"パラメータエラー: {e}")
    except Exception as e:
        # 予期しないエラー
        sdk.logger.error(f"処理失敗: {e}")
        await event.reply("処理に失敗しました。しばらく待ってから再試行してください")
```

### 2. ログ記録

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"メッセージを処理中: {user_id} - {text}")
    
    # モジュールの独自ロガーを使用
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"詳細デバッグ情報")
```

### 3. 条件処理

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """条件処理 - ハンドラー内で判断"""
    # 特定のユーザーからのメッセージのみ処理
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 特定のキーワードを含むメッセージのみ処理
    if "キーワード" not in event.get_text():
        return
    
    await event.reply("条件を満たしました、メッセージを処理します")

## 次のステップ

- [一般的なタスクの例](common-tasks.md) - 基本機能の実装を学ぶ（メッセージ送信の高度な機能：リトライ/タイムアウト/バッチを含む）
- [プラットフォームの機能ガイド](../platform-guide/README.md) - Send DSL のチェーン送信、送信ルール、バッチ構築の完全な説明
- [Event ラッパークラスの詳細](../developer-guide/modules/event-wrapper.md) - Event オブジェクトについて深く理解する
- [ユーザーガイド](../user-guide/) - 設定とモジュール管理について理解する



### IDE 补全

# タイプのスタブ生成（IDEの補完）

ErisPulse はエントリーポイントを用いてモジュール/アダプターを動的に発見します。エントリーポイントは静的レベルでユーザーのクラスの具体的な型を知ることができません。  
`epsdk types` コマンドは、インストールされているモジュール/アダプターをスキャンして、タイプのスタブファイルを生成し、ユーザーがこれらの型を変数の注釈として使用して IDE の補完を得られるようにします。

## コア設計原則

スタブファイルは**型のみをエクスポート**し、実行時のインスタンスを提供しません：

- すべてのインポートは ``TYPE_CHECKING`` の下にあり、**実行時のオーバーヘッドはゼロ、動作の変更はゼロ**
- クラス名はエントリーポイント名の PascalCase 形式（例：``yunhu`` → ``Yunhu``）を使用し、``sdk.adapter.get()`` / ``sdk.module.get()`` に渡す名前に対応
- ユーザーはコード内で ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` を通常通り使用してインスタンスを取得しますが、インポートされた型を**変数の注釈**として使用します

## 基本的な使い方

プロジェクトのルートディレクトリで実行します：

```bash
epsdk types
```

現在のディレクトリに `_ep_types.py` を生成し、インストールされているすべてのモジュール/アダプターの型を含みます。

## コードでの使用

```python
from _ep_types import MyModule, Yunhu
from ErisPulse import sdk

# インポートされた型を変数の注釈として使用することで、IDE がそのクラスのメソッドを補完します
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← IDE が hello を補完

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← プラットフォーム固有のメソッドを補完
```

## 動作原理

1. `erispulse.adapter` / `erispulse.module` のエントリーポイントをスキャンします
2. ターゲットの Python 環境でサブプロセスを使用して内部調査を行い、各アダプター/モジュールの実際のクラス情報を収集します（モジュールパスと限定名を含む）
3. `.py` ファイルを生成し、その中で：
   - ``from xxx import Yyy as Zzz`` はすべて ``TYPE_CHECKING`` の下にあります
   - ``Zzz`` はエントリーポイント名の PascalCase 形式です
4. IDE は ``TYPE_CHECKING`` 部分を読み取り、補完を提供します。実行時にはコードは一切実行されません

生成されたスタブの例：

```python
# _ep_types.py（自動生成）
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # アダプター
    from MyAdapter.Core import MyAdapter as MyAdapter
    from YunhuAdapter.Core import YunhuAdapter as Yunhu

    # モジュール
    from MyModule.Core import Main as MyModule

    __all__ = ['MyAdapter', 'Yunhu', 'MyModule']
```

## コマンドオプション

| オプション | 説明 |
|------|------|
| `-o, --output PATH` | 出力ファイルのパスを指定（デフォルト：`./_ep_types.py`） |
| `--force` | 既存のスタブファイルを上書きします |
| `--adapters-only` | アダプターのみをスキャンします |
| `--modules-only` | モジュールのみをスキャンします |

## 再生成のタイミング

- 新しいモジュールまたはアダプターをインストール/アンインストールした後
- モジュール/アダプターが公開 API を更新した後
- IDE の補完が失効または型が古くなった場合

## SendDSL 標準メソッドとの関係

`SendDSL` 基底クラスには標準の送信メソッド（Text/Image/Voice/Video/File）が既に内蔵されています。どのような方法で取得した SendDSL インスタンスでも、これらのメソッドの補完が可能です。  
`types` コマンドは、**プラットフォーム固有のメソッド**（例：雲湖の `Board`、沙盒の `Dice`）と**モジュール固有のメソッド**の補完を主に行います。



====
模块开发
====


### 模块开发入门

# モジュール開発入門

本ガイドでは、ゼロから ErisPulse モジュールを作成する方法を説明します。

## プロジェクト構成

標準的なモジュール構成：

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py
```

## pyproject.toml の設定

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "モジュールの機能説明"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = []

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

## __init__.py

```python
from .Core import Main
```

## Core.py - 基本モジュール

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self.config = self._load_config()
    
    @staticmethod
    def get_load_strategy():
        """モジュールのロード戦略を返します"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[]  # オプション：依存する他のモジュールのリスト
        )
    
    async def on_load(self, event):
        """モジュールのロード時に呼び出されます"""
        @command("hello", help="挨拶を送信")
        async def hello_command(event):
            name = event.get_user_nickname() or "友達"
            await event.reply(f"こんにちは、{name}！")
        
        self.logger.info("モジュールがロードされました")
    
    async def on_unload(self, event):
        """モジュールのアンロード時に呼び出されます"""
        self.logger.info("モジュールがアンロードされました")
    
    def _load_config(self):
        """モジュール設定をロードします"""
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = {
                "api_url": "https://api.example.com",
                "timeout": 30
            }
            self.sdk.config.setConfig("MyModule", default_config)
            return default_config
        return config
```

## モジュールのテスト

### ローカルテスト

```bash
# プロジェクトディレクトリにモジュールをインストール
epsdk install ./MyModule

# プロジェクトを実行
epsdk run main.py --reload
```

### テストコマンド

コマンドを送信してテスト：

```
/hello
```

## コア概念

### BaseModule 基底クラス

すべてのモジュールは `BaseModule` を継承する必要があり、以下のメソッドを提供します：

| メソッド | 説明 | 必須 |
|------|------|------|
| `__init__(self)` | コンストラクタ | いいえ |
| `get_load_strategy()` | ロード戦略を返します | いいえ |
| `on_load(self, event)` | モジュールのロード時に呼び出されます | はい |
| `on_unload(self, event)` | モジュールのアンロード時に呼び出されます | はい |

### SDK オブジェクト

`sdk` オブジェクトを通じてコア機能にアクセスします：

```python
from ErisPulse import sdk

sdk.storage    # ストレージシステム
sdk.config     # 設定システム
sdk.logger     # ログシステム
sdk.adapter    # アダプタシステム
sdk.router     # ルータシステム
sdk.lifecycle  # ライフサイクルシステム
```

## 次のステップ

- [モジュールのコア概念](core-concepts.md) - モジュールアーキテクチャを深く理解する
- [Event ラッパークラスの詳細](event-wrapper.md) - Event オブジェクトを学ぶ
- [モジュールのベストプラクティス](best-practices.md) - 高品質なモジュールを開発する



### 模块核心概念

# モジュールの基本概念

ErisPulse モジュールの基本概念を理解することは、高品質なモジュールを作成するための基盤となります。

## モジュールのライフサイクル

### ロード戦略

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """モジュールのロード戦略を返します"""
        return ModuleLoadStrategy(
            lazy_load=True,   # 延遅ロードか即時ロードか
            priority=0,       # ロード優先度（数値が大きいほど先にロードされます）
            depends=["OtherModule"]  # オプション：依存する他のモジュールを宣言
        )
```

> `depends` で宣言されたモジュールが未登録の場合、現在のモジュールはスキップされ、警告が記録されます。ロード順序はトポロジカルソートによって決定され、同じ階層では `priority` 降順になります。

### on_load メソッド

モジュールのロード時に呼び出され、リソースの初期化やイベントハンドラーの登録に使用されます：

```python
async def on_load(self, event):
    # イベントハンドラーを登録
    @command("hello", help="挨拶コマンド")
    async def hello_handler(event):
        await event.reply("こんにちは！")
    
    # SDKの組み込みHTTPクライアントを使用（接続プールを自動管理するため、手動でセッションを作成する必要はありません）
    # sdk.client からリクエストを送信できます
```

### on_unload メソッド

モジュールのアンロード時に呼び出され、リソースのクリーンアップに使用されます：

```python
async def on_unload(self, event):
    # カスタムリソースのクリーンアップ
    # sdk.client はフレームワークが管理するため、手動で閉じる必要はありません
    
    # イベントハンドラーのキャンセル（フレームワークが自動的に処理します）
    self.logger.info("モジュールがアンロードされました")

## SDK オブジェクト

### コアモジュールへのアクセス

```python
from ErisPulse import sdk

# sdk オブジェクトを通じてすべてのコアモジュールにアクセスする
sdk.logger.info("ログ")
sdk.storage.set("キー", "値")
config = sdk.config.getConfig("MyModule")
```

### モジュール間通信

```python
# 他のモジュールにアクセスする
other_module = sdk.OtherModule
result = await other_module.some_method()

## アダプタ送信方法の照会

新しい標準仕様では、フォールバック送信機構を実装するために `__getattr__` メソッドを上書きすることが求められるため、`hasattr` メソッドを使用してメソッドの存在を確認することができなくなりました。バージョン `2.3.5` 以降、送信方法を照会する機能が追加されました。

### サポートされている送信方法のリスト

```python
# プラットフォームがサポートするすべての送信方法を一覧表示する
methods = sdk.adapter.list_sends("onebot11")
# 返回: ["Text", "Image", "Voice", "Markdown", ...]
```

### メソッドの詳細情報の取得

```python
# 特定のメソッドの詳細情報を取得する
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

## 設定管理

### 宣言的設定（推奨）

v2.5.2 以降、モジュールは `ConfigClass` を使用して設定クラスを宣言できるようになりました。アダプターと同じ設定 Schema システムを使用します。設定は `self.cfg` でリアルタイムに読み出され、変更後はすぐに有効になります：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_module.api_key", "default": "API キー"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )
    timeout: int = field(
        default=30,
        metadata={
            "description": {"i18n": "my_module.timeout", "default": "タイムアウト（秒）"},
            "ui": {"widget": "number", "group": "advanced", "order": 2},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def on_load(self, event):
        self.logger.info("モジュールがロードされました")

    async def on_unload(self, event):
        pass

    async def do_something(self):
        cfg = self.cfg  # リアルタイム読み出し、型安全
        api_key = cfg.api_key
        timeout = cfg.timeout
```

`BaseConfig` は汎用的な設定基底クラスで、アダプター、モジュール、外部プロジェクトなどあらゆるシーンに適用できます。設定フィールドは i18n 多言語記述をサポートしています（詳細は [i18n ドキュメント](../../advanced/i18n.md#設定フィールド多言語)をご参照ください）。

### 宣言的翻訳キー（v2.7.0+）

v2.7.0 以降、モジュールは `ConfigClass` を宣言するのと同様に、ネストされた `I18nClass` クラスを使って翻訳キーを一括で宣言することもできます。フレームワークはロード時に宣言されたすべての翻訳キーを**自動的に登録**するため、手動で `i18n.register()` を呼び出す必要はありません。また、設定テンプレートの生成より早いタイミングで登録されるため、設定記述で参照する i18n キーが利用可能であることが保証されます。

```python
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey

class MyModule(BaseModule):
    # 設定クラス（任意）
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="欢迎",
            metadata={
                "description": {"i18n": "mymodule.welcome_msg", "default": "ウェルカムメッセージ"},
            },
        )

    # 翻訳キーセットクラス（任意）
    class I18nClass(BaseI18n):
        # プロパティ名が自動的に完全なキーパスに連結されます：<モジュール名>.<プロパティ名>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # 言語に依存しないフォールバック
            zh_CN="欢迎消息",
            zh_TW="歡迎訊息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
        )
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )
```

詳細は [i18n 推奨の記述方法](../../advanced/i18n.md#推奨の記述方法I18nClassで翻訳キーを宣言するv270) を参照してください。

### 手動による設定の読み込み（互換方式）

宣言的設定を使用しない場合、直接設定ストレージに対して読み書きすることも可能です。

```python
def _load_config(self):
    config = self.sdk.config.getConfig("MyModule")
    if not config:
        default_config = {
            "api_key": "",
            "timeout": 30
        }
        self.sdk.config.setConfig("MyModule", default_config)
        return default_config
    return config
```

> **注意**：手動方式の場合は `self.config` をプロパティ名として使用しないでください。`self.cfg` または独自の名前を使用することをお勧めします。そうしないと、将来的なフレームワークのプロパティとの競合を避けることができません。

请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。

再次提醒：如果文档包含语言切换行（各语言名称用 `` | `` 分隔的行），务必严格遵守上方第8条的格式要求，不要写出 ``[**Label**](file)`` 这类错误格式。

## ストレージシステム

### 基本的な使用方法

```python
# データを保存
sdk.storage.set("user:123", {"name": "張三"})

# データを取得
user = sdk.storage.get("user:123", {})

# データを削除
sdk.storage.delete("user:123")
```

### トランザクションの使用

```python
# トランザクションを使用してデータの一貫性を確保
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # どの操作か失敗した場合、すべての変更はロールバックされます

## イベント処理

### イベントハンドラの登録

```python
from ErisPulse.Core.Event import command, message

# コマンドを登録
@command("info", help="情報を取得")
async def info_handler(event):
    await event.reply("これは情報です")

# メッセージハンドラを登録
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"グループメッセージを受信しました: {event.get_text()}")
```

### イベントハンドラのライフサイクル

フレームワークは自動的にイベントハンドラの登録と登録解除を管理します。`on_load` で登録するだけでよいです。

## レイジー ローディング機構

### 動作原理

```python
# モジュールが初めてアクセスされたときにのみ初期化される
result = await sdk.my_module.some_method()
# ↑ ここでモジュール初期化がトリガーされる
```

### すぐにロード

すぐに初期化する必要があるモジュール（リスナー、タイマーなど）の場合：

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=False,  # すぐにロード
        priority=100
    )

## エラー処理

### 例外の捕捉

```python
async def handle_event(self, event):
    try:
        # 業務ロジック
        await self.process_event(event)
    except ValueError as e:
        self.logger.warning(f"パラメータエラー: {e}")
        await event.reply(f"パラメータエラー: {e}")
    except Exception as e:
        self.logger.error(f"処理失敗: {e}")
        raise
```

### ログ記録

```python
# ログレベルの使い分け
self.logger.debug("デバッグ情報")    # 詳細なデバッグ情報
self.logger.info("実行状態")        # 正常実行の情報
self.logger.warning("警告情報")    # 警告情報
self.logger.error("エラー情報")    # エラー情報
self.logger.critical("致命的なエラー") # 致命的なエラー



### Event 包装类详解

# Event 包装クラスの詳細解説

Event モジュールは、強力な Event 包装クラスを提供し、イベント処理を簡素化します。

## 核心機能

- **完全な辞書互換性**：Event は dict を継承
- **便利なメソッド**：多数の便利なメソッドを提供
- **点アクセス**：ドット記法でイベントフィールドにアクセス可能
- **後方互換性**：すべてのメソッドはオプション

## 核心フィールドメソッド

```python
from ErisPulse.Core.Event import command

@command("info")
async def info_command(event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, プラットフォーム: {platform}, 時間: {time}")
```

## メッセージイベントメソッド

```python
from ErisPulse.Core.Event import message

@message.on_private_message()
async def private_handler(event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"こんにちは、{nickname}！")
```

## メッセージタイプ判断

```python
from ErisPulse.Core.Event import message

@message.on_group_message()
async def group_handler(event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"タイプ: {'プライベートチャット' if is_private else 'グループチャット'}")
```

## 返信機能

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    await event.reply("あなたの名前を入力してください:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")
```

## コマンド情報取得

```python
from ErisPulse.Core.Event import command

@command("cmdinfo")
async def cmdinfo_command(event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"コマンド: {cmd_name}, 引数: {cmd_args}")
```

## 通知イベントメソッド

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    await event.reply("友達として追加してくれてありがとう！")
```

## メソッド速見表

### 核心メソッド

#### イベント基本情報
- `get_id()` - イベントIDを取得
- `get_time()` - イベントタイムスタンプ（Unix秒）を取得
- `get_type()` - イベントタイプを取得（message/notice/request/meta）
- `get_detail_type()` - イベント詳細タイプを取得（private/group/friend等）
- `get_platform()` - プラットフォーム名を取得

#### ロボット情報
- `get_self_platform()` - ロボットのプラットフォーム名を取得
- `get_self_user_id()` - ロボットのユーザIDを取得
- `get_self_account_id()` - ロボットのアカウントIDを取得（多Botモード）
- `get_self_info()` - ロボットの完全な情報辞書を取得

#### 会話識別子
- `get_target_id()` - 統一されたターゲットIDを取得（グループチャットは group_id を返す、チャンネルは channel_id を返す、プライベートチャットは user_id を返す、group → channel → guild → thread → user の順で最初の非空値を返す）
- `get_session_id()` - セッションの唯一の識別子を取得、形式は `{platform}:{detail_type}:{target_id}`

### メッセージイベントメソッド

#### メッセージ内容
- `get_message()` - メッセージセグメント配列を取得（OneBot12形式）
- `get_alt_message()` - メッセージの代替テキストを取得
- `get_text()` - 純粋なテキスト内容を取得（`get_alt_message()` の別名）
- `get_message_text()` - 純粋なテキスト内容を取得（`get_alt_message()` の別名）

#### 送信者情報
- `get_user_id()` - 送信者のユーザIDを取得
- `get_user_nickname()` - 送信者のニックネームを取得
- `get_sender()` - 送信者の完全な情報辞書を取得

#### グループ/チャンネル情報
- `get_group_id()` - グループIDを取得（グループメッセージ）
- `get_channel_id()` - チャンネルIDを取得（チャンネルメッセージ）
- `get_guild_id()` - サーバIDを取得（サーバメッセージ）
- `get_thread_id()` - トピック/サブチャンネルIDを取得（トピックメッセージ）

#### @メッセージ関連
- `has_mention()` - @ロボットを含むかどうか
- `get_mentions()` - すべての@されたユーザIDリストを取得

### メッセージタイプ判断

#### 基本判断
- `is_message()` - メッセージイベントかどうか
- `is_private_message()` - プライベートチャットメッセージかどうか
- `is_group_message()` - グループチャットメッセージかどうか
- `is_at_message()` - @メッセージかどうか（`has_mention()` の別名）

### 通知イベントメソッド

#### 通知操作者
- `get_operator_id()` - 操作者のIDを取得
- `get_operator_nickname()` - 操作者のニックネームを取得

#### 通知タイプ判断
- `is_notice()` - 通知イベントかどうか
- `is_group_member_increase()` - グループメンバー増加イベント
- `is_group_member_decrease()` - グループメンバー減少イベント
- `is_friend_add()` - 友達追加イベント（`detail_type == "friend_increase"` に一致）
- `is_friend_delete()` - 友達削除イベント（`detail_type == "friend_decrease"` に一致）

### 要求イベントメソッド

#### 要求情報
- `get_comment()` - 要求の付言を取得

#### 要求タイプ判断
- `is_request()` - 要求イベントかどうか
- `is_friend_request()` - 友達要求かどうか
- `is_group_request()` - グループ要求かどうか

### 返信機能

#### 基本返信
- `reply(content, method="Text", at_sender=False, reply_to_message=False, at_users=None, reply_to=None, at_all=False, **kwargs)` - 一般的な返信メソッド
  - `content`: 送信内容（テキスト、URLなど）
  - `method`: 送信方法、デフォルトは "Text"、"Image"/"Voice"/"Video"/"File" など
  - `at_sender`: 送信者を@するかどうか（自動的に user_id を抽出）
  - `quote`: 現在のメッセージを引用して返信するかどうか（自動的に message_id を抽出）
  - `at_users`: @するユーザリスト、例：`["user1", "user2"]`
  - `reply_to`: 手動で指定された返信メッセージID
  - `at_all`: 全体を@するかどうか
  - `**kwargs`: 余分なパラメータ（例：Mentionメソッドの user_id）

- `reply_ob12(message)` - OneBot12メッセージセグメントを使って返信
  - `message`: OneBot12メッセージセグメントのリストまたは辞書、MessageBuilderを使って構築可能

#### プラットフォーム能力確認
- `supports(method)` - 現在のプラットフォームが特定の送信方法（例："Image"、"Voice"）をサポートしているかを確認し、`bool`を返す
- `available_methods()` - 現在のプラットフォームで利用可能なすべての送信方法をリスト形式で返す

#### 転送機能

> **注意**: 転送機能はアダプタの Send DSL を通じて実装する必要があり、Event 包装クラス自体は直接の転送メソッドを提供していません。

```python
# メッセージをグループに転送
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # または他のグループIDを指定
await adapter.Send.To("group", target_id).Text(event.get_text())
```

### 返信待ち機能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text")` - ユーザの返信を待つ
  - `prompt`: プロンプトメッセージ、提供された場合ユーザに送信
  - `timeout`: 待ち時間のタイムアウト（秒）、デフォルトは60秒
  - `callback`: 返信を受け取ったときに実行されるコールバック関数
  - `validator`: 返信が有効かどうかを検証する関数
  - `method`: プロンプトメッセージを送信する方法、デフォルトは "Text"
  - ユーザの返信された Event オブジェクトを返す、タイムアウト時は None を返す

#### インタラクティブメソッド

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - 確認対話
  - 戻り値は `True`（確認）/ `False`（否定）/ `None`（タイムアウト）
  - 内部的に中英語の確認語を自動認識し、独自の語集をカスタマイズ可能
  - `method`: 送信方法、デフォルトは "Text"、"Image"/"Markdown" などの非テキスト方式もサポート
  - `hint`: プロンプトの末尾に自動的に確認語のプロンプトを追加するかどうか、デフォルトは False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - 選択メニュー
  - `options`: 選択肢のテキストリスト
  - 戻り値は選択肢のインデックス（0ベース）、タイムアウト時は `None` を返す
  - `method`: 送信方法、デフォルトは "Text"、テキスト系メソッド (Text/Markdown/md/Html/h5) はデフォルトで選択肢を末尾に結合
  - `options_format`: 選択肢のフォーマット（デフォルト: "auto"、methodに応じて自動的に内蔵スタイルを選択）
    - `"auto"`：Markdown→無序リスト（`- 1.選択肢`）、Html→有序リスト（`<ol>`）、その他→純粋なテキストリスト
    - `"list"`：各行に1つ、例：``1. 選択肢A\n2. 選択肢B``
    - `"inline"`：1行に表示、例：``1.A | 2.B``
    - `"md"`：Markdown無序リスト
    - `"html"`：Html有序リスト
    - `callable`：カスタム関数、``list[str]``を受け取り``str``を返す
  - `merge_prompt`: 強制的に1つのメッセージとして送信するかどうか、デフォルトは False
    - `False`（デフォルト）：テキスト系メソッドは自動的に結合；非テキスト系メソッドはまずpromptを送信してからText選択肢を送信
    - `True`：どんなmethodでも1つのメッセージに結合し、ユーザが指定したmethodで送信
  - `placeholder`: 選択肢を挿入するプレースホルダ、デフォルトは `{options}`；promptにこのマーカーが現れる場所に選択肢テキストを置き換え、空文字列に設定すると常に末尾に追加

- `collect(fields, timeout_per_field=60.0)` - フォーム収集
  - `fields`: フィールドリスト、各項目には `key`、`prompt`、オプションの `validator`、オプションの `method` が含まれる
  - 戻り値は `{key: value}` 辞書、いずれかのフィールドがタイムアウトした場合は `None` を返す
  - 各フィールドは `method` キーで送信方法を指定可能、例：画像を収集する際には `{"key": "avatar", "prompt": "プロフィール画像を送ってください", "method": "Image"}`
  - 各フィールドはオプションの `options` キー（リスト）を提供し、該当するフィールドは選択問題になる（自動的に choose ロジックを呼び出す）
  - 各フィールドはオプションの `options_format`、`merge_prompt`、`placeholder` キーを制御し、選択肢のフォーマット、メッセージの結合動作、プレースホルダを制御

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 任意のイベントを待つ
  - `condition`: 条件関数、`True` を返す場合に一致
  - 戻り値は一致する Event オブジェクト、タイムアウト時は `None` を返す

- `conversation(timeout=60.0)` - 複数ラウンド対話コンテキストを作成
  - 戻り値は `Conversation` オブジェクト、`say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()` をサポート
  - `is_active` 属性は対話がアクティブかどうかを示す

#### インタラクティブメソッドの例

**confirm() - 確認対話：**

```python
@command("delete", help="データを削除")
async def delete_handler(event):
    if await event.confirm("すべてのデータを削除してもよろしいですか？"):
        sdk.storage.delete("all_data")
        await event.reply("データを削除しました")
    else:
        await event.reply("キャンセルしました")
```

**confirm() - プロンプト付き：**

```python
# hint=True でプロンプトの末尾に "（はい/いいえ）" を追加
if await event.confirm("続行してもよろしいですか？", hint=True):
    await event.reply("続行しました")
# ユーザに表示される内容：続行してもよろしいですか？（はい/いいえ）
```

**choose() - 選択メニュー：**

```python
@command("color", help="色を選択")
async def color_handler(event):
    choice = await event.choose("色を選択してください：", ["赤", "緑", "青"])
    if choice is not None:
        colors = ["赤", "緑", "青"]
        await event.reply(f"選択した色は：{colors[choice]}")
```

**choose() - 選択肢のフォーマットとメッセージの結合：**

```python
# inline 形式：選択肢を1行に表示
choice = await event.choose("選択してください：", ["A", "B", "C"], options_format="inline")
# 出力：1.A | 2.B | 3.C

# 自定義フォーマット
choice = await event.choose("選択してください：", ["猫", "犬"],
    options_format=lambda opts: " / ".join(opts))
# 出力：猫 / 犬

# options_format="auto"（デフォルト）：methodに応じて内蔵スタイルを自動選択
# Markdown → 無序リスト
choice = await event.choose(
    "## 選択してください", ["猫", "犬"],
    method="Markdown",  # auto は自動的に md リストを認識
)
# 出力：
# ## 選択してください
# - 1. 猫
# - 2. 犬

# Html → 有序リスト
choice = await event.choose(
    "<h2>選択してください</h2>", ["猫", "犬"],
    method="Html", merge_prompt=True,  # auto は自動的に html リストを認識
)
# 出力：
# <h2>選択してください</h2>
# <ol><li>1. 猫</li><li>2. 犬</li></ol>

# 合併モード + プレースホルダ
choice = await event.choose(
    "## 選択してください\n{options}\n番号を返信してください",
    ["猫", "犬"],
    method="Markdown", merge_prompt=True,
)

# 自定義プレースホルダ
choice = await event.choose(
    "選択してください: [choices]",
    ["猫", "犬"],
    placeholder="[choices]",
)
```

**collect() - フォーム収集：**

```python
@command("register", help="登録")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "名前を入力してください："},
        {"key": "age", "prompt": "年齢を入力してください：",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"登録完了！{data['name']}、{data['age']}歳")
```

**非 Text メソッドの reply：**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("この画像を見てください：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> 完全な Conversation 多ラウンド対話の使い方は [Conversation 多ラウンド対話](../../advanced/conversation.md) を参照してください。

### コマンド情報

#### コマンド基本
- `get_command_name()` - コマンド名を取得
- `get_command_args()` - コマンド引数のリストを取得
- `get_command_raw()` - コマンドの元のテキストを取得
- `get_command_info()` - 完全なコマンド情報辞書を取得
- `is_command()` - コマンドかどうか

### 元データ

- `get_raw()` - プラットフォームの元のイベントデータを取得
- `get_raw_type()` - プラットフォームの元のイベントタイプを取得

### プラットフォーム拡張メソッド

アダプタは Event 包装クラスにプラットフォーム固有のメソッドを登録できます。メソッドは対応するプラットフォームの Event インスタンスでのみ利用可能で、他のプラットフォームでアクセスすると `AttributeError` をスローします。

プラットフォームメソッドは `Event.__getattribute__` により、内蔵メソッドよりも優先して有効になるため、`confirm`、`choose`、`collect`、`wait_reply` などの内蔵インタラクティブメソッドを覆い、プラットフォーム特有の実装（例：ボタン、カードなど）を提供できます。内蔵実装は `_builtin_*` 関数としてエクスポートされ、覆い書きする側が呼び出すことができます。

```python
# メールイベント - メールメソッドのみ
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello" を返す
event.get_chat_type()    # ❌ AttributeError

# Telegram イベント - Telegram メソッドのみ
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private" を返す
event.get_subject()      # ❌ AttributeError

# 内蔵メソッドは常に利用可能
event.get_text()         # ✅ どのプラットフォームでも
event.reply("hi")        # ✅ どのプラットフォームでも
```

### 登録されたメソッドの照会

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` と `dir` のサポート

```python
hasattr(event, "get_subject")   # platform="email" のみで True を返す
"get_subject" in dir(event)     # 同上
```

### 跨プラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` は `"*"` をプラットフォーム名として渡すことができ、登録されたメソッドは**すべてのプラットフォーム**の Event インスタンスで利用可能になります。AI対話、コンテキスト管理など、跨プラットフォームで再利用可能な機能に適しています。

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self は Event インスタンス、イベントデータと内蔵メソッドにアクセス可能
    await self.reply(f"AI: {prompt}")
```

登録後、どのプラットフォームのイベントハンドラでも `event.ai_chat(...)` を呼び出すことができます。

メソッドの優先順位（高から低）：プラットフォーム固有のメソッド → ワイルドカードメソッド → 内蔵メソッド → 辞書キーのアクセス。

> アダプタ開発者が拡張メソッドを登録する方法は [イベントシステム API - 跨プラットフォーム拡張ワイルドカード](../../api-reference/event-system.md#跨プラットフォーム拡張ワイルドカード) を参照してください。



### 模块开发最佳实践

# モジュール開発におけるベストプラクティス

このドキュメントでは、ErisPulse モジュール開発に関するベストプラクティスを提供します。

以下のルールに従って変換してください。

1.  Markdown形式を維持する（見出し、リスト、コードブロック、リンク、画像など）
2.  用語を正確に翻訳し、専門性を保つ
3.  コードブロック内のコードロジックは翻訳しないが、コード内の中国語コメント、文字列は日本語に翻訳する
4.  原文の構造とトーンを維持する
5.  用語について、日本語の対応用語が不明な場合は英語の原語を保持する
6.  その他の説明や注釈は追加せず、翻訳後のコンテンツのみを返す
7.  翻訳後のドキュメントに中国語（固有名詞を除く）が残らないようにする。これにはコードブロック内のコメントと文字列も含まれる
8.  翻訳後のMarkdownコンテンツを直接出力する。```markdown```などのコードブロックで囲まない

**重要：パス置換ルール**
-   ドキュメントリンク内の `docs/ja/` を `docs/ja/` に置換する
-   例：`docs/ja/quick-start.md` は `docs/ja/quick-start.md` に変更する
-   現在の言語バージョンではないファイルを指し示すリンク（`README.xx.md` 形式のリンクなど）については、変更せずそのまま保持する
-   これにより、正しい言語バージョンのドキュメントを指すようにする

## モジュール設計

### 1. 単一責任の原則

各モジュールは1つのコア機能のみを担当する必要があります。

```python
# 良い設計：各モジュールは1つの機能のみを担当する
class WeatherModule(BaseModule):
    """天気照会モジュール"""
    pass

class NewsModule(BaseModule):
    """ニュース照会モジュール"""
    pass

# 悪い設計：1つのモジュールが複数の非関連な機能を担当する
class UtilityModule(BaseModule):
    """天気、ニュース、ジョークなど複数の機能を含む"""
    pass
```

### 2. モジュール命名規則

```toml
[project]
name = "ErisPulse-ModuleName"  # ErisPulse- プレフィックスを使用
```

### 3. 明確な設定管理

宣言的設定（`ConfigClass` + `BaseConfig`）を使用することを推奨します。これにより、型安全性、自動テンプレート生成、WebUI フォームサポートなどの機能が得られます。

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_url: str = field(default="https://api.example.com", metadata={
        "description": {"i18n": "my_module.api_url", "default": "API アドレス"},
    })
    timeout: int = field(default=30, metadata={
        "description": {"i18n": "my_module.timeout", "default": "タイムアウト時間（秒）"},
    })
    cache_ttl: int = field(default=3600, metadata={
        "description": {"i18n": "my_module.cache_ttl", "default": "キャッシュ有効期間（秒）"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # 型安全性があり、即時読み込み
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

また、手動での設定ストレージの読み書きを引き続き使用することも可能です（[モジュールの核心的な概念](core-concepts.md#設定管理)を参照）。

### 宣言的翻訳キー（v2.7.0+）

モジュールは `I18nClass` を使用して翻訳キーを集中して宣言できます。フレームワークは i18n システムに自動的に登録されるため、手動で `i18n.register()` を呼び出す必要はありません。

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # プレースホルダー付きのビジネス翻訳キー
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="欢迎你，{name}！",
            zh_TW="歡迎你，{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # 設定フィールドの説明の翻訳
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

詳細な使用方法については、[i18n ドキュメント](../../advanced/i18n.md#推奨される書き方 -i18nclass-で翻訳キーを宣言する-v270)を参照してください。

## 非同期プログラミング

### 1. 非同期ライブラリの使用

```python
# SDK 内蔵の HTTP クライアント（非同期、自動ログと統計）を推奨します
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# sdk.client を使用することもできます（同じ効果です）
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# aiohttp を直接インポートしないでください（フレームワークの統一管理が不便です）
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# requests を使用しないでください（同期で、イベントループをブロックします）
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # イベントループをブロックします
```

### 2. 適切な非同期操作

```python
async def handle_command(self, event):
    # 長時間実行される操作をバックグラウンドで実行するために create_task を使用します
    task = asyncio.create_task(self._long_operation())
    
    # 結果を待つ必要がある場合
    result = await task
```

### 3. リソース管理

```python
async def on_load(self, event):
    # SDK クライアントは自動的に接続プールを管理しているため、手動でセッションを作成する必要はありません
    pass
    
async def on_unload(self, event):
    # カスタムクライアントが必要な場合は、リソースのクリーンアップを忘れないでください
    pass

## イベント処理

### 1. Event クラスの使用

```python
# Event クラスを利用する便利なメソッド
@command("info")
async def info_command(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"こんにちは、{nickname}！")

# 辞書を直接アクセスする代わりに
@command("info")
async def info_command(event):
    user_id = event["user_id"]  # 不明確で、エラーが発生しやすい
```

### 2. 適切な Lazy Load（遅延読み込み）の使用

```python
# コマンド処理モジュールは即時読み込みが必要
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# リスナーモジュールは即時読み込みが必要
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# ユーティリティモジュールは遅延読み込みに適している
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

### 3. イベントハンドラーの登録

```python
async def on_load(self, event):
    # on_load でイベントハンドラーを登録
    @command("hello")
    async def hello_handler(event):
        await event.reply("こんにちは！")
    
    @message.on_group_message()
    async def group_handler(event):
        self.logger.info("グループメッセージを受信しました")
    
    # 手動で登録解除する必要はありません。フレームワークが自動的に処理します

## エラー処理

### 1. 例外処理の分類

```python
async def handle_event(self, event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # 予期されるビジネスエラー
        self.logger.warning(f"ビジネス警告: {e}")
        await event.reply(f"パラメータエラー: {e}")
    except aiohttp.ClientError as e:
        # ネットワークエラー（sdk.client + ClientError の使用を推奨）
        # 旧コードは aiohttp を直接使用しても動作しますが、新コードでは ErisPulse 例外体系を使用することを推奨します
        self.logger.error(f"ネットワークエラー: {e}")
        await event.reply("ネットワークリクエストに失敗しました。しばらく待ってから再試行してください")
    except Exception as e:
        # 予期しないエラー
        self.logger.error(f"不明なエラー: {e}", exc_info=True)
        await event.reply("処理に失敗しました。管理者にお問い合わせください")
        raise
```

### 2. タイムアウト処理

```python
# SDK 内蔵クライアント（タイムアウトとリトライ機能付き）の使用を推奨
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"リクエストタイムアウト: {url}")
        raise

## ストレージシステム

### 1. トランザクションを使用する

```python
# トランザクションを使用してデータの一貫性を確保
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ トランザクションを使用しないと、データの一貫性が損なわれる可能性があります
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # ここでエラーが発生すると、上記の設定はロールバックされません
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. バッチ操作

```python
# バッチ操作を使用してパフォーマンスを向上させる
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ 複数回呼び出すと効率が悪い
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)

## ロギング

### 1. ログレベルを適切に使用する

```python
# DEBUG: 詳細なデバッグ情報（開発時のみ）
self.logger.debug(f"入力パラメータ: {params}")

# INFO: 正常な実行時の情報
self.logger.info("モジュールが読み込まれました")
self.logger.info(f"リクエストを処理中: {request_id}")

# WARNING: 警告メッセージ。主要な機能には影響しない
self.logger.warning(f"設定項目 {key} が設定されていません、デフォルト値を使用します")
self.logger.warning("API レスポンスが遅い、最適化の必要がある可能性があります")

# ERROR: エラーメッセージ
self.logger.error(f"API リクエストに失敗しました: {e}")
self.logger.error(f"イベントの処理に失敗しました: {e}", exc_info=True)

# CRITICAL: 致命的なエラー、即座に対処が必要
self.logger.critical("データベース接続に失敗しました、ボットを正常に実行できません")
```

### 2. 構造化されたロギング

```python
# 構造化されたログを使用すると解析が容易になります
self.logger.info(f"リクエストを処理中: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ 非構造化ログを使用
self.logger.info(f"リクエストを処理しました。ユーザー {user_id} からのもの、所要時間 {duration} ミリ秒")

## パフォーマンスの最適化

### 1. キャッシュの使用

```python
class MyModule(BaseModule):
    def __init__(self):
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_data(self, key):
        async with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            
            # データベースから取得
            data = await self._fetch_from_db(key)
            
            # データをキャッシュ
            self._cache[key] = data
            return data
```

### 2. ブロッキング操作の回避

```python
# 非同期操作の使用
async def process_message(self, event):
    # 非同期処理
    await self._async_process(event)

# ❌ ブロッキング操作
async def process_message(self, event):
    # 同期操作、イベントループをブロック
    result = self._sync_process(event)

## セキュリティ

### 1. 敏感データの保護

```python
# 設定に敏感データを保存
class MyModule(BaseModule):
    def _load_config(self):
        config = self.sdk.config.getConfig("MyModule")
        self.api_key = config.get("api_key")
        
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("config.toml で有効な API キーを設定してください")

# ❌ 機密情報をハードコーディングするのは避けてください
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # このようなことはしないでください！
```

### 2. 入力値の検証

```python
# ユーザー入力を検証
async def process_command(self, event):
    user_input = event.get_text()
    
    # 入力の長さを検証
    if len(user_input) > 1000:
        await event.reply("入力が長すぎます。もう一度入力してください")
        return
    
    # 入力の形式を検証
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("入力形式が正しくありません")
        return

## テスト

### 1. 単体テスト

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_load_config(self):
        """設定の読み込みをテスト"""
        module = MyModule()
        config = module._load_config()
        assert config is not None
        assert "api_url" in config
```

### 2. 統合テスト

```python
@pytest.mark.asyncio
async def test_command_handling():
    """コマンドの処理をテスト"""
    module = MyModule()
    await module.on_load({})
    
    # コマンドイベントのシミュレーション
    event = create_test_command_event("hello")
    await module.handle_command(event)

## 部署

### 1. バージョン管理

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

セマンティックバージョニング（Semantic Versioning）に従います：
- MAJOR.MINOR.PATCH
- メジャーバージョン：互換性のない API の変更
- マイナーバージョン：下位互換のある機能の追加
- パッチバージョン：下位互換のある問題の修正

### 2. README ヘッダー

`epsdk create` で生成された README には、ErisPulse のヘッダー識別子（ロゴ + バッジ行）が既に組み込まれています。2つの推奨モードがあります。

**モード A — ErisPulse ロゴのみ（デフォルト）：**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**一文で説明**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**モード B — モジュールアイコン × ErisPulse ロゴ（カスタムアイコンがある場合）：**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docs/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
（バッジ行は上記と同じ）
</div>
```

GitHub Stars、Downloads などのバッジを必要に応じて追加できます。ロゴもプロジェクトローカルにダウンロード可能です（`.github/assets/ErisPulseLogo.png`）し、相対パスで参照してください。



=====
发布与工具
=====


### 发布模块到模块商店

# 公開とモジュールストアガイド

開発したモジュールまたはアダプターを ErisPulse モジュールストアに公開し、他のユーザーが簡単に発見・インストールできるようにします。

## モジュールストアの概要

ErisPulse モジュールストアは集中型のモジュールレジストリであり、ユーザーは CLI ツールを通じてコミュニティが貢献したモジュールやアダプターを閲覧・検索・インストールできます。

### 閲覧と検索

```bash
# リモートで利用可能なすべてのパッケージを一覧表示
epsdk list-remote

# モジュールのみ表示
epsdk list-remote -t modules

# アダプターのみ表示
epsdk list-remote -t adapters

# リモートパッケージリストを強制更新
epsdk list-remote -r
```

[ErisPulse 公式サイト](https://www.erisdev.com/#market) にアクセスしてオンラインでモジュールストアを閲覧することもできます。

### サポートされているリリースタイプ

| タイプ | 説明 | Entry-point グループ |
|------|------|----------------|
| モジュール (Module) | ボットの機能拡張、ビジネスロジックの実装 | `erispulse.module` |
| アダプター (Adapter) | 新しいメッセージプラットフォームとの接続 | `erispulse.adapter` |

## クイック公開

プロセスは全工程で3ステップのみです。プロジェクトの設定 → PyPI への公開 → モジュールストアへの登録。

### 1. pyproject.toml の設定

プロジェクトディレクトリに `pyproject.toml`、`README.md` が含まれていることを確認し、タイプに合わせて entry-points を設定します。

#### モジュール

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "モジュールの機能説明"
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
description = "アダプターの機能説明"
requires-python = ">=3.10"

[project.entry-points."erispulse.adapter"]
"myplatform" = "MyAdapter:MyAdapter"
```

> **注意**: パッケージ名は `ErisPulse-` で始まることを推奨します。これはユーザーが識別しやすいためです。Entry-point のキー名（例: `"MyModule"`）は、SDK 内でのモジュールアクセス名になります。

### 2. PyPI への公開

```bash
# ビルド + 公開（PyPI アカウントが必要）
pip install build twine
python -m build
python -m twine upload dist/*
```

公開後、インストールを検証します：

```bash
pip install ErisPulse-MyModule
```

### 3. モジュールストアへの登録

[ErisPulse モジュールストア](https://www.erisdev.com/#market) に移動し、「モジュールを提出」をクリックして、ログイン後にモジュール情報を入力します。

サポートされているログイン方法: **GitHub**、**Codeberg**、**雲湖**（Yunhu）。いずれか一つを選択できます。

入力のポイント:
- モジュール名、説明、リポジトリアドレス
- 最低 SDK バージョン: 不確かな場合は、[ErisPulse 最新版](https://pypi.org/project/ErisPulse/) のバージョン番号を入力してください。

登録後、即座に有効になります。ユーザーはモジュールソースからインストールできます。モジュールは「未検証」でマークされます。メンテナが承認すると「検証済み」に変更されます。

> **検証状態について**:
> - 「未検証」はまだ公式な承認を受けていないことを示しており、モジュールに問題があることを意味しません
> - ユーザーが `epsdk install` で未検証モジュールをインストールするときは、リスクに関する警告が表示されます。続行する前に確認が必要です

### 4. 発行済みモジュールの管理

モジュールストアで「モジュールを提出」をクリックしてログインしたら、「マイモジュール」タブに切り替えて、以下ができます:
- **編集** — モジュールの説明、リポジトリアドレス、タグなどを変更します。バージョン番号は PyPI から自動的に同期されます
- **削除** — モジュールストアからモジュールを削除します（取り消しできません）

> 登録直後のモジュールは、数分かかることがありますが「マイモジュール」リストに表示されます。

## 発行済みモジュールの更新

1. `pyproject.toml` 内の `version` を更新します
2. 再構築してアップロード: `python -m build && python -m twine upload dist/*`
3. モジュールストアは PyPI の最新バージョンを自動的に同期します

ユーザーは `epsdk upgrade MyModule` でアップグレードできます。

## 公開前チェックリスト

PyPI へプッシュする前に、以下の項目を逐一確認してください。

### コード品質

- [ ] すべての公開 API に型注釈（関数のシグネチャと戻り値）
- [ ] すべての公開メソッドにドキュメント文字列（`"""..."""` 形式、`:param` / `:return` / `:raises` を含む）
- [ ] `ruff check` に合格（警告なし）
- [ ] テストカバレッジ ≥ 80%
- [ ] `pytest` がすべてのテストに合格

### 互換性

- [ ] `pyproject.toml` に最低 SDK バージョンを宣言: `dependencies = ["ErisPulse>=x.y.z"]`
- [ ] Python 3.10 / 3.11 / 3.12 / 3.13 をテスト済み
- [ ] ターゲットOS（Windows / Linux / macOS、該当する場合）をテスト済み
- [ ] 循環インポート依存なし

### 設定

- [ ] 宣言的設定（`ConfigClass` + `BaseConfig` / `BotAccountConfig`）を使用している場合、設定フィールドに `description`（推奨 i18n 形式）と `ui` メタデータがあるか
- [ ] i18n 翻訳キーを登録している場合、すべての 5 か国語（zh-CN / zh-TW / en / ja / ru）をカバーしているか
- [ ] 機密フィールドに `secret=True` がマークされているか

### ドキュメント

- [ ] `README.md` にインストール手順と基本的な使用例がある
- [ ] `README.md` に設定方法の説明（設定ファイルの例 + 環境変数）
- [ ] `CHANGELOG.md` にすべての変更を記録している
- [ ] アダプターでプラットフォームの仕様ドキュメントが更新されている（サポートされている Send タイプ、イベントタイプなど）

### 公開

- [ ] `pyproject.toml` のバージョン番号が更新されている
- [ ] ビルド成功: `python -m build`
- [ ] PyPI へのプッシュ完了: `python -m twine upload dist/*`
- [ ] インストール検証成功: `pip install ErisPulse-xxx && epsdk run`

## 開発モードでのテスト

正式に公開する前に、編集可能モードでローカルでテストできます:

```bash
epsdk install -e /path/to/MyModule
# または
pip install -e /path/to/MyModule
```

## よくある質問

### パッケージ名は必ず `ErisPulse-` で始まりますか？

必須ではありませんが、強く推奨します。これによりユーザーは PyPI 上で ErisPulse エコシステムのパッケージを識別しやすくなります。

### 1つのパッケージに複数のモジュールを登録できますか？

はい。`entry-points` で複数のキーバリューペアを設定します:

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### 承認にどのくらい時間がかかりますか？

通常、1〜3 営業日で完了します。モジュールストアの「マイモジュール」で検証状態を確認できます。

## Docker イメージ経由でのアプリ配布

アプリが PyPI に公開するのに適していない場合（プライベート依存関係を含む、事前設定された環境が必要など）、**GitHub Container Registry (GHCR)** を使用して Docker イメージを公開し、他のユーザーが `docker pull` でワンクリックで起動できるようにします。

### 適用シナリオ

- **完全なボットアプリ**（モジュール + 設定 + エントリースクリプト）があり、ワンクリックで配布したい場合
- モジュール/アダプターが**プライベートパッケージ**に依存している、または特殊なインストールフローがあるため PyPI には適さない場合
- ユーザーの使用ハードルを下げるために、**すぐに使える（アンパックして動く）** デプロイソリューションを提供したい場合

### 1. Dockerfile の作成

ErisPulse 公式イメージをベースに構築し、独自のモジュールのみを追加します:

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

モジュールに追加のシステム依存関係（SSH クライアントなど）が必要な場合は、`RUN uv pip install` の後に追加します:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` には ErisPulse、ErisPulse-Dashboard、Python ランタイム、uv が含まれており、再インストールの必要はありません。

### 2. GitHub Actions ワークフローの作成

`.github/workflows/docker-publish.yml` に作成します:

```yaml
name: Docker イメージを公開

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

      - name: QEMU のセットアップ (マルチアーキテクチャ対応)
        uses: docker/setup-qemu-action@v3

      - name: Docker Buildx のセットアップ
        uses: docker/setup-buildx-action@v3

      - name: GitHub Container Registry にログイン
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

      - name: Docker イメージの構築とプッシュ
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

> `GITHUB_TOKEN` は GitHub Actions から自動的に提供されるため、手動でシークレットを作成する必要はありません。

### 3. ビルドのトリガー

コードをプッシュまたはタグ付けすると、ビルドが自動的にトリガーされます:

```bash
# main ブランチへのプッシュでトリガー
git push origin main

# またはタグ付けでトリガー
git tag v1.0.0
git push origin v1.0.0
```

GitHub リポジトリの **Actions** ページからでも手動でトリガーできます。

### 4. イメージをパブリックに設定する

GHCR イメージはデフォルトで **private** です。他のユーザーがログインなしでプルできるようにするには、GitHub でパブリックに設定する必要があります:

1. リポジトリへ移動 → **Packages** → 対応するパッケージをクリック
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. ユーザーが使用する方法

ビルドが完了したら、ユーザーは `docker run` で1行で起動できます:

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

### Docker Hub へも同時に公開

ワークフローを拡張し、ログインステップの前に Docker Hub ログインを追加し、`images` に Docker Hub のアドレスを追加します:

```yaml
      - name: Docker Hub にログイン
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
| 配布方式 | `docker pull` でワンクリック実行 | `pip install` + 手動設定 |
| 対象範囲 | 完全なアプリケーション/ソリューション | 単一のモジュール/アダプター |
| プライベート依存 | 自然にサポート | プライベート PyPI ソースが必要 |
| モジュールストア | 適用外 | モジュールストアに提出可能 |
| マルチアーキテクチャ | amd64/arm64 をサポート | アーキテクチャに依存しない |

2つの方法は競合しません — PyPI を経由してモジュールストアにモジュールを公開しつつ、GHCR を経由してすぐに使える Docker イメージを提供できます。



### CLI 命令参考

# CLI コマンドリファレンス

ErisPulse コマンドラインツール（`epsdk`）は、プロジェクト管理およびパッケージ管理機能を提供します。

> **ヒント**: すべてのコマンドは `epsdk <command> --help` で詳細なパラメータ説明を確認できます。

---

## パッケージ管理コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | モジュール/アダプタをインストール |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | モジュール/アダプタをアンインストール |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 指定したモジュールをアップグレード、またはすべてをアップグレード |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | SDK 自体を更新 |

## 診断コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose]` | 環境を診断し、ヘルスレポートを出力 |

### install

ErisPulse モジュールまたはアダプタパッケージをインストールします。パッケージ名を指定しない場合、対話型インストール画面になります。

**エイリアス:** `i`, `add`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `[package]...` | | インストールするパッケージ名。複数指定可能 |
| `--upgrade` | `-U` | インストール時に最新バージョンへアップグレード |
| `--pre` | | プリリリース版のインストールを許可 |
| `--editable` | `-e` | 編集可能モードでインストール（パスを指定必要） |
| `--user` | | ユーザーの site-packages ディレクトリへインストール |
| `--no-deps` | | 依存関係をインストールしない |
| `--target` | `-t` | 指定のディレクトリへインストール |
| `--index-url` | | PyPI ミラーソースアドレスを指定 |
| `--extra-index-url` | | 追加の PyPI ミラーソースアドレス（複数指定可能） |
| `--no-cache-dir` | | キャッシュを無効化 |
| `--requirement` | `-r` | requirements ファイルからインストール |
| `--constraint` | `-c` | constraint ファイルからインストール |
| `--force-reinstall` | | 強制的に再インストール |
| `--ignore-installed` | | 既にインストール済みのパッケージを無視 |
| `--compile` | | インストール後、.pyc ファイルをコンパイル |
| `--no-compile` | | インストール後、.pyc ファイルをコンパイルしない |
| `--prefix` | | 指定のプレフィックスディレクトリへインストール |
| `--src` | | 編集可能インストール時のソースディレクトリ |
| `--config-settings` | | ビルドバックエンドへ渡す設定（複数指定可能） |
| `--no-binary` | | バイナリパッケージを使用しないように制限（`:all:` のような形式） |
| `--only-binary` | | バイナリパッケージのみ使用するように制限（`:all:` のような形式） |
| `--prefer-binary` | | バイナリパッケージを優先 |
| `--build-isolation` | | ビルド隔離を有効化 |
| `--no-build-isolation` | | ビルド隔離を無効化 |
| `--upgrade-strategy` | | アップグレード戦略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | システムパッケージマネージャーが管理する Python パッケージの変更を許可 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例:**

```bash
# 単一のモジュールをインストール
epsdk install Weather

# 複数のモジュールをインストール
epsdk install Yunhu Weather

# ミラーソースからインストールしてアップグレード
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 編集可能モードでインストール（開発モード）
epsdk install -e ./my-adapter
```

### uninstall

既にインストールされた ErisPulse モジュールまたはアダプタパッケージをアンインストールします。パッケージ名を指定しない場合、対話型アンインストール画面になります。

**エイリアス:** `rm`, `remove`

**引数:**

| 引数 | 説明 |
|------|------|
| `<package>...` | アンインストールするパッケージ名。複数指定可能 |
| `--no-uv` | uv の代わりに pip を使用 |

**例:**

```bash
# 単一のモジュールをアンインストール
epsdk uninstall Weather

# 複数のモジュールをアンインストール
epsdk uninstall Yunhu Weather
```

### upgrade

既にインストールされた ErisPulse コンポーネントをアップグレードします。パッケージ名を指定しないと、対話型で全件をアップグレードします。

**エイリアス:** `up`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `[package]...` | | アップグレードするパッケージ名。複数指定可能 |
| `--force` | `-f` | 強制的にアップグレード、確認をスキップ |
| `--pre` | | プリリリース版へのアップグレードを許可 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例:**

```bash
# すべてのパッケージをアップグレード
epsdk upgrade

# 指定したパッケージをアップグレード
epsdk upgrade Weather

# 強制アップグレード（確認をスキップ）
epsdk upgrade -f
```

### self-update

ErisPulse SDK 自体を最新バージョンへ更新します。

**エイリアス:** `su`, `update`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `[version]` | | 更新対象のバージョン番号を指定 |
| `--pre` | | プリリリース版への更新を許可 |
| `--force` | `-f` | 強制的に更新、確認をスキップ |
| `--no-uv` | | uv の代わりに pip を使用 |

**例:**

```bash
# 最新の安定版へ更新
epsdk self-update

# 指定バージョンへ更新
epsdk self-update 1.2.3

# プリリリース版を許可
epsdk self-update --pre

# 強制更新
epsdk self-update -f
```

---

## 情報照会コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | インストール済みコンポーネントを一覧表示 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | リモートで利用可能なコンポーネントを一覧表示 |

### list

インストール済みの ErisPulse モジュールとアダプタを一覧表示します。

**エイリアス:** `l`, `ls`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定：`modules`、`adapters`、`all`（デフォルト） |
| `--outdated` | `-o` | アップグレード可能なパッケージのみ表示 |

**例:**

```bash
# インストール済みのすべてのコンポーネントを一覧表示
epsdk list

# モジュールのみを一覧表示
epsdk list -t modules

# アダプタのみを一覧表示
epsdk list -t adapters

# アップグレード可能なパッケージのみ表示
epsdk list -o
```

### list-remote

リモートリポジトリで利用可能な ErisPulse モジュールとアダプタを一覧表示します。

**エイリアス:** `lsr`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定：`modules`、`adapters`、`all`（デフォルト） |
| `--refresh` | `-r` | リモートパッケージリストキャッシュを強制的に更新 |

**例:**

```bash
# すべてのリモート利用可能コンポーネントを一覧表示
epsdk list-remote

# リモートモジュールのみを一覧表示
epsdk list-remote -t modules

# キャッシュを強制的に更新して一覧表示
epsdk list-remote -r
```

---

## 実行制御コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | 指定したスクリプトまたは SDK を実行 |

### run

ErisPulse プロジェクトスクリプトを実行、または SDK を直接起動します。ホットリロードモードに対応しています。

**エイリアス:** `r`

**引数:**

| 引数 | 説明 |
|------|------|
| `[script]` | 実行するスクリプトファイル。指定しない場合は SDK を実行 |
| `--reload` | ホットリロードモードを有効化。ファイルの変更を監視し、自動的に再起動 |

**例:**

```bash
# SDK を直接実行
epsdk run

# 指定したスクリプトファイルを実行
epsdk run main.py

# ホットリロードモードで実行（ファイル変更時に自動再起動）
epsdk run main.py --reload

# SDK ホットリロードモード
epsdk run --reload
```

---

## プロジェクト管理コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `init` | — | `[--project-name/-n <name>] [--quick/-q] [--force/-f] [--here] [--no-uv]` | ErisPulse プロジェクトを初期化 |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | モジュール/アダプタのスキャフォールドを作成 |

### init

新しい ErisPulse プロジェクトを初期化します。対話モードとクイックモードをサポートしています。

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `--project-name` | `-n` | プロジェクト名 |
| `--quick` | `-q` | クイックモード。対話ウィザードをスキップ |
| `--force` | `-f` | 既存の設定ファイルを強制的に上書き |
| `--here` | | 現在のディレクトリで初期化。サブディレクトリを作成しない |
| `--no-uv` | | uv の代わりに pip を使用 |

**例:**

```bash
# 対話型で初期化
epsdk init

# クイック初期化
epsdk init -q -n my_bot

# 既存の設定を強制的に上書き
epsdk init -f

# 現在のディレクトリで初期化
epsdk init --here -n my_bot
```

### create

ErisPulse モジュールまたはアダプタのスキャフォールドプロジェクトを作成します。

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `{module,adapter}` | | 作成するタイプ：`module` または `adapter` |
| `--name` | `-n` | プロジェクト名（PascalCase） |
| `--description` | `-d` | プロジェクトの説明 |
| `--author` | `-a` | 作者名 |
| `--email` | `-e` | 作者のメールアドレス |
| `--homepage` | | プロジェクトのホームページ URL |
| `--output` | `-o` | 出力ディレクトリ（デフォルトは現在のディレクトリ） |
| `--force` | `-f` | 既存のディレクトリを強制的に上書き |

**例:**

```bash
# 対話型で作成（タイプと情報入力の誘導）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全な引数
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 出力ディレクトリを指定
epsdk create module -n MyModule -o ./projects

# 既存のディレクトリを強制的に上書き
epsdk create module -n MyModule -f
```

---

## 言語コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | CLI 表示言語の確認または切り替え |

### i18n

現在の CLI 言語を確認、サポートされている言語を一覧表示、表示言語を切り替えます。パラメータを指定しない場合、対話型の選択画面になります。

**エイリアス:** `language`, `lang`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `[lang]` | | 切り替える言語コード（例: `zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | サポートされているすべての言語を一覧表示 |

**例:**

```bash
# 対話型で言語を選択
epsdk i18n

# 英語へ切り替え
epsdk i18n en

# 日本語へ切り替え
epsdk i18n ja

# サポートされている言語を一覧表示
epsdk i18n --list
```

---

## 型スタブコマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | IDE 自補のための型スタブファイルを生成 |

### types

インストール済みの ErisPulse モジュールとアダプタをスキャンし、`.pyi` 型スタブファイルを生成して、IDE で正確なコード補完と型チェックのサポートを得ます。

**エイリアス:** `t`, `stub`

**引数:**

| 引数 | 短引数 | 説明 |
|------|--------|------|
| `--output` | `-o` | 出力先パス（デフォルトは現在のディレクトリ下の `ep-stubs/`） |
| `--force` | | 既存のスタブファイルを強制的に上書き |
| `--adapters-only` | | アダプタの型スタブのみ生成 |
| `--modules-only` | | モジュールの型スタブのみ生成 |

> **注意:** `--adapters-only` と `--modules-only` は排他的です。両方を同時に指定した場合、後者が有効になります。

**例:**

```bash
# すべてのインストール済みモジュールとアダプタに対して型スタブを生成
epsdk types

# アダプタのスタブのみ生成
epsdk types --adapters-only

# 指定したディレクトリへ出力
epsdk types -o ./typings

# 既存のファイルを強制的に上書き
epsdk types --force
```

---

## 全体パラメータ

以下のパラメータはすべてのコマンドに適用されます：

| パラメータ | 短引数 | 説明 |
|------|--------|------|
| `--help` | `-h` | ヘルプ情報を表示 |
| `--version` | `-V` | バージョン情報を表示 |
| `--verbose` | `-v` | 詳細な出力を表示（`-vv`/`-vvv` で累積） |
| `--no-color` | | 色の出力を無効化（CI / ログ収集向け） |
| `--yes` | `-y` | すべての対話プロンプトを自動確認（非対話実行時） |

---

## 環境診断

### doctor

現在の CLI 実行環境を診断し、ヘルスレポートを出力します。「なぜインストールできない / 接続できないのか」といった問題の原因特定に使用します。

| パラメータ | 説明 |
|------|------|
| `--verbose` | 詳細な診断情報を表示 |

**確認項目**:
- **Python**: インタプリタのバージョンとパス
- **インストールバックエンド**: `uv` または `pip` を使用
- **ターゲットインタプリタ**: パッケージが実際にインストールされる Python 環境
- **設定ファイル**: `config/config.toml` が存在するか
- **PyPI 接続性**: PyPI へのアクセス可否（見つかったコンポーネント数を表示）
- **システムプロキシ**: プロキシの検出有無

```bash
# 実行環境診断
epsdk doctor

# エイリアスを使用
epsdk diag
```

---

## 対話型インストール

`epsdk install` でパッケージ名を指定せずに実行すると対話型インストールになります：

```bash
epsdk install
```

対話画面では以下が提供されます：
1. アダプタ選択
2. モジュール選択
3. カスタムインストール

## よく使われる使用例

### モジュールをインストール

```bash
# 単一のモジュールをインストール
epsdk install Weather

# 複数のモジュールをインストール
epsdk install Yunhu Weather

# モジュールをアップグレード
epsdk install Weather -U
```

### コンポーネントを一覧表示

```bash
# すべてのコンポーネントを一覧表示
epsdk list

# アダプタのみを一覧表示
epsdk list -t adapters

# アップグレード可能なコンポーネントのみを一覧表示
epsdk list -o

# リモートで利用可能なコンポーネントを確認
epsdk list-remote
```

### コンポーネントをアンインストール

```bash
# 単一のコンポーネントをアンインストール
epsdk uninstall Weather

# 複数のコンポーネントをアンインストール
epsdk uninstall Yunhu Weather
```

### コンポーネントをアップグレード

```bash
# すべてのコンポーネントをアップグレード
epsdk upgrade

# 指定したコンポーネントをアップグレード
epsdk upgrade Weather

# 強制アップグレード
epsdk upgrade -f
```

### プロジェクトを実行

```bash
# 通常の実行
epsdk run main.py

# ホットリロードモード
epsdk run main.py --reload
```

### 言語を切り替え

```bash
# 対話型で言語を選択
epsdk i18n

# 英語へ直接切り替え
epsdk i18n en

# サポートされている言語を一覧表示
epsdk i18n --list
```

### 型スタブを生成

```bash
# すべての型スタブを生成
epsdk types

# モジュールの型スタブのみ生成
epsdk types --modules-only
```

### プロジェクトを初期化

```bash
# 対話型で初期化
epsdk init

# クイック初期化
epsdk init -q -n my_bot
```

### スキャフォールドを作成

```bash
# 対話型で作成（タイプと情報入力の誘導）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全な引数
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 既存のディレクトリを強制的に上書き
epsdk create module -n MyModule -f



======
API 参考
======


### 核心模块 API

# コアモジュール API

このドキュメントは、ErisPulse コアモジュールの API クイックリファレンスを提供します。メソッドシグネチャと簡単な説明が含まれています。詳細な使用法と例については、各モジュールの「完全なドキュメント」リンクをクリックしてください。

詳細な用法と例については、各モジュールの「完全なドキュメント」リンクをクリックしてください。

## Storage モジュール

SQLite をベースとしたキーバリューストアシステムで、汎用的な SQL のチェーンクエリをサポートしています。

### 基本操作

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### バッチ操作

```python
sdk.storage.set_multi({"key1": "val1", "key2": "val2"})
values = sdk.storage.get_multi(["key1", "key2"])
sdk.storage.delete_multi(["key1", "key2"])
```

### トランザクション操作

```python
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### プロパティアクセス

```python
sdk.storage.my_key          # sdk.storage.get("my_key") と同等
sdk.storage.my_key = "val"  # sdk.storage.set("my_key", "val") と同等
```

### SQL チェーンクエリ

Storage モジュールは、チェーンコールスタイルの汎用的な SQL クエリビルダーを提供し、カスタムテーブルの CRUD 操作をサポートしています。

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> 完全なチェーンクエリ API（Select/Insert/Update/Delete/Where/OrderBy/Limit、AlterTable、トランザクション等）については、[SQL クエリビルダー](../advanced/sql-builder.md) を参照してください。

### ストレージバックエンド抽象化

`StorageManager` は `BaseStorage` 抽象基底クラスを継承しており、他のストレージ媒体（Redis、MySQL など）への拡張をサポートしています。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### 非同期インターフェース

Storage および Config モジュールは両方とも非同期メソッド（プレフィックス `a`）を提供しており、非同期ハンドラー内で安全に呼び出すことができます。同期メソッドは維持されたままです。既存のコードを変更する必要はありません。

```python
# 非同期ストレージ
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# 非同期バッチ操作
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# 非同期設定
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()

## Config モジュール

TOML 形式の設定ファイル管理。ドット区切りのキーパスをサポートします。

### API 概要

| メソッド | 説明 |
|------|------|
| `getConfig(key, default)` | 設定を読み込みます。ドット区切りのパス（例: `"MyModule.subkey"`）をサポートします |
| `setConfig(key, value, immediate=False)` | 設定を書き込みます。`immediate=True` の場合、ファイルに即座に保存されます |
| `force_save()` | メモリ内の設定を強制的にファイルに書き込みます |
| `reload()` | ファイルから設定を再読み込みします |
| `agetConfig(key, default)` | 非同期で設定を読み込みます |
| `asetConfig(key, value, immediate)` | 非同期で設定を書き込みます |
| `aforce_save()` | 非同期で強制保存します |
| `areload()` | 非同期で再読み込みします |

### 例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（5 秒ごとにバッチ保存）を採用しています。`immediate=True` を設定すると、設定ファイルに即座に永続化できます。設定の変更は `config.set` ライフサイクルイベントをトリガーします。

## Logger モジュール

モジュール化されたログシステム。Rich 出力をベースとし、サブロガーおよびモジュール単位での制御をサポートします。

### 基本的な使い方

```python
sdk.logger.debug("デバッグ情報")
sdk.logger.info("実行情報")
sdk.logger.warning("警告情報")
sdk.logger.error("エラー情報")
sdk.logger.critical("致命的なエラー")
```

### サブロガー

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("サブモジュールログ")

child_logger.get_child("utils")  # ネストに対応
```

### ログレベル制御

```python
sdk.logger.set_level("DEBUG")                          # グローバルレベル
sdk.logger.set_module_level("MyModule", "DEBUG")       # モジュールレベル

# サポートされるレベル（低い順）：
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE は最低レベルで、フレームワーク内部の詳細なデバッグ情報（イベント配信、ルート登録など）を出力します
sdk.logger.set_level("TRACE")                          # 全ログ有効化
```

### ログ購読（プッシュモード）

Dashboard などのモジュールが構造化ログをリアルタイムで受信するためのものです。レベルによるフィルタリングおよび履歴ログの再送をサポートします。

> **低レベルログの明示的な購読**：購読器の `min_level` は、グローバルログレベルよりも低く設定できます。この場合、低レベルログは**マッチする購読器にのみプッシュ**され、コンソールには出力されず、メモリにも書き込まれないため、メインログストリームの汚染を回避できます。
>
> ```python
> # グローバルレベルが INFO でも、DEBUG ログだけ個別に購読可能
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# デコレータ方式
@sdk.logger.handler("my-handler", min_level="INFO")
def on_log(log_data: dict):
    # log_data = {
    #     "timestamp": "2026-06-29T22:00:00.123456",
    #     "level": "WARNING", "level_num": 30,
    #     "module": "ErisPulse.Core.adapter",
    #     "message": "厳格モード：...",
    # }
    pass

# 直接呼び出し方式
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| メソッド | 説明 |
|------|------|
| `handler(id, *, min_level)(func)` | デコレータ / 直接呼び出しの両用。`id` が空の場合は関数名を取得します。`min_level` はグローバルレベルより低くできます（低レベルログは購読器にのみプッシュされ、コンソール/メモリへは入りません）。登録時に自動で履歴ログを再送します |
| `remove_handler(id)` | 購読器を削除します |

### 出力制御

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)

## アダプターモジュール

アダプターマネージャーは、マルチプラットフォームアダプターの登録、起動、およびシャットダウンを管理します。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(platform)` | アダプターメソッドの取得 |
| `exists(platform)` | アダプターが登録されているかチェック |
| `enable(platform)` / `disable(platform)` | アダプターの有効化/無効化 |
| `is_enabled(platform)` | 有効になっているかチェック |
| `startup(platforms)` / `shutdown(platforms)` | アダプターの起動/シャットダウン |
| `is_running(platform)` | アダプターが実行中かチェック |
| `list_running()` | 実行中のアダプターを一覧表示 |
| `platforms` | 全プラットフォーム名リストの取得 |

### アダプターイベント

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot ステータス確認

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> 完全なアダプターマネジメント API については、[アダプターシステム API](docs/ja/adapter-system.md) を参照してください。

## Module モジュール

モジュールマネージャーは、プラグインの登録、読み込み、アンインストールを管理します。

### API サマリー

| メソッド | 説明 |
|------|------|
| `get(name)` | モジュールインスタンスを取得する、または遅延読み込みプロキシを取得する（登録済みだが未読込の場合はプロキシを返す） |
| `exists(name)` | 登録済みかどうかを確認する |
| `is_loaded(name)` | 読み込まれたかどうかを確認する |
| `is_enabled(name)` | 有効かどうかを確認する |
| `enable(name)` / `disable(name)` | モジュールを有効化/無効化する |
| `load(name)` / `unload(name)` | モジュールを読み込み/アンインストールする |
| `list_registered()` | 登録済みモジュールを一覧表示する |
| `list_loaded()` | 読み込み済みモジュールを一覧表示する |
| `get_info(name)` | モジュール情報を取得する |
| `get_status_summary()` | モジュールステータスサマリーを取得する |

### プロパティへのアクセス

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # 同等のショートカット

## Lifecycle モジュール

イベント駆動のライフサイクルマネージャーで、イベントの送信と監視機能を提供します。

### API 概要

| メソッド | 説明 |
|------|------|
| `on(event, priority=0)` | デコレータでイベントハンドラーを登録。ドット表記のマッチングとワイルドカード `*` をサポート |
| `register(event, handler, priority=0)` | 関数型でハンドラーを登録 |
| `unregister(event, handler=None)` | ハンドラーを削除 |
| `emit(event, data)` | 非同期でイベントを発行 |
| `emit_sync(event, data)` | 同期的にイベントを発行 |
| `submit_event(event_type, msg, data, source)` | 標準形式のイベントを送信（旧版との互換性） |
| `start_timer(id)` / `stop_timer(id)` | パフォーマンス計時用タイマー |

### サンプル

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"モジュール初期化: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"モジュールイベント: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})
```

> 標準イベントの完全なリストと詳細な使い方については、[ライフサイクル管理](../advanced/lifecycle.md) を参照してください。

## Router モジュール

HTTP/WebSocket ルーター管理機能。FastAPI + Uvicorn をベースに、デコレータールーター、ミドルウェア、グルーピング、レート制限、CORS をサポートします。

> 詳細なルーター API ドキュメント（デコレータールーター、WebSocket、ミドルウェア、レート制限、CORS、セキュリティヘッダー等）については、[ルーター管理器](../advanced/router.md) を参照してください。

### クイックリファレンス

```python
# HTTP ルーター
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket ルーター
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# ルーターグループ
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}

## HTTP Client モジュール

統合されたネットワーククライアントで、HTTP リクエスト、WebSocket 接続、コネクションプールの管理、自動再試行、リクエスト統計、およびライフサイクルイベントの統合を提供します。

> リクエストメソッド、レスポンスオブジェクト、WebSocketクライアント、例外体系などの、完全なネットワーククライアントのドキュメントについては、[ネットワーククライアント](../advanced/http-client.md) を参照してください。

### クイックリファレンス

```python
from ErisPulse.Core import client

# HTTP リクエスト
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")

## SDK デバッグ

### dump_state()

現在実行中のフレームワークの状態スナップショットをエクスポートし、デバッグおよび診断に使用します。

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

返される構造には以下のサブシステムの状態が含まれます：

| フィールド | 説明 |
|------|------|
| `sdk` | SDK の初期化状態、Python バージョン、実行プラットフォーム、タイムスタンプ |
| `adapters` | 登録済み/起動済みのアダプタ一覧、各プラットフォームの Bot オンライン状態 |
| `modules` | 登録済み/有効/無効/遅延読み込みのモジュール一覧 |
| `events` | 各種イベントハンドラの数（message/notice/request/meta/commands） |
| `router` | サーバーの実行状態、HTTP/WebSocket ルート数 |

> 2.5.2 で追加



### 事件系统 API

# イベントシステム API

本ドキュメントでは、ErisPulse のイベントシステムの API について詳しく説明します。

## Command コマンドモジュール

### コマンドの登録

```python
from ErisPulse.Core.Event import command

# 基本的なコマンド
@command("hello", help="挨拶を送信")
async def hello_handler(event):
    await event.reply("こんにちは！")

# エイリアス付きのコマンド
@command(["help", "h"], aliases=["ヘルプ"], help="ヘルプを表示")
async def help_handler(event):
    pass

# 権限付きのコマンド
def is_admin(event):
    return event.get("user_id") in admin_ids

@command("admin", permission=is_admin, help="管理者コマンド")
async def admin_handler(event):
    pass

# 非表示コマンド
@command("secret", hidden=True, help="秘密のコマンド")
async def secret_handler(event):
    pass

# コマンドグループ
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    pass
```

### コマンド情報

```python
# コマンドのヘルプを取得
help_text = command.help()

# 特定のコマンドを取得
cmd_info = command.get_command("admin")

# コマンドグループ内のすべてのコマンドを取得
admin_commands = command.get_group_commands("admin")

# 可視化されたすべてのコマンドを取得
visible_commands = command.get_visible_commands()
```

### 返信の待機

```python
# ユーザーからの返信を待機
@command("ask", help="ユーザー情報を尋ねる")
async def ask_command(event):
    reply = await command.wait_reply(
        event,
        prompt="あなたの名前を入力してください:",  # すでに上記で送信済み
        timeout=30.0
    )
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}！")

# 検証付きの返信待機
def validate_age(event_data):
    try:
        age = int(event_data.get_text())
        return 0 <= age <= 150
    except ValueError:
        return False

@command("age", help="ユーザーの年齢を尋ねる")
async def age_command(event):
    await event.reply("あなたの年齢を入力してください:")
    
    reply = await command.wait_reply(
        event,
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"あなたの年齢は {age} 歳です")

# コールバック付きの返信待機
async def handle_confirmation(reply_event):
    text = reply_event.get_text().lower()
    if text in ["はい", "yes", "y"]:
        await event.reply("操作が確定しました！")
    else:
        await event.reply("操作がキャンセルされました。")

@command("confirm", help="操作を確認する")
async def confirm_command(event):
    await command.wait_reply(
        event,
        prompt="'はい'または'いいえ'を入力してください:",
        callback=handle_confirmation
    )

## Message メッセージモジュール

### メッセージイベント

```python
from ErisPulse.Core.Event import message

# すべてのメッセージを監視
@message.on_message()
async def message_handler(event):
    sdk.logger.info(f"受信メッセージ: {event.get_text()}")

# プライベートチャットメッセージを監視
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"プライベートチャットから: {user_id}")

# グループチャットメッセージを監視
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    sdk.logger.info(f"グループチャットから: {group_id}")

# @メッセージを監視
@message.on_at_message()
async def at_handler(event):
    mentions = event.get_mentions()
    sdk.logger.info(f"メンションされたユーザー: {mentions}")
```

### 条件付き監視

```python
# 優先度を使用して実行順序を制御
@message.on_message(priority=10)  # 数値が大きいほど優先度が高い
async def high_priority_handler(event):
    pass

# ハンドラ内部で条件フィルタを実装
@message.on_message()
async def filtered_handler(event):
    if "キーワード" not in event.get_text():
        return
    # キーワードを含むメッセージを処理
    pass

## 通知モジュール

### 通知イベント

```python
from ErisPulse.Core.Event import notice

# フレンド追加
@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    await event.reply("友達として追加してくれてありがとう！")

# フレンド削除
@notice.on_friend_remove()
async def friend_remove_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"フレンド削除: {user_id}")

# グループメンバー増加
@notice.on_group_increase()
async def member_increase_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"新メンバーようこそ！")

# グループメンバー減少
@notice.on_group_decrease()
async def member_decrease_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"メンバー退会: {user_id}")

## リクエスト モジュール (Request モジュール)

### リクエスト イベント

```python
from ErisPulse.Core.Event import request

# フレンドリクエスト
@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    sdk.logger.info(f"フレンドリクエスト: {user_id}, 注釈: {comment}")

# グループ招待リクエスト
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ招待: {group_id}, から: {user_id}")

## メタ イベント モジュール

### メタ イベント

```python
from ErisPulse.Core.Event import meta

# 接続イベント
@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} への接続に成功しました")

# 切断イベント
@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} から切断されました")

# ハートビートイベント
@meta.on_heartbeat()
async def heartbeat_handler(event):
    sdk.logger.debug("ハートビートを受信しました")
```

### Bot 状態照会

アダプタがメタイベントを送信した後、フレームワークは自動的に Bot の状態を追跡します。照会 API およびライフサイクルイベントの監視については、[アダプタシステム API - Bot 状態管理](adapter-system.md#bot-状态管理) を参照してください。

## イベント クラス

Event モジュールのイベントハンドラーは、dict を継承したイベントラッパークラスのインスタンスを受け取ります。これには便利なメソッドが提供されています。

### 基本メソッド

```python
# イベント情報の取得
event_id = event.get_id()
event_time = event.get_time()
event_type = event.get_type()
detail_type = event.get_detail_type()
platform = event.get_platform()

# ボット情報の取得
self_platform = event.get_self_platform()
self_user_id = event.get_self_user_id()
self_info = event.get_self_info()
```

### セッション識別子

```python
# 統一されたターゲット ID：グループチャットは group_id、プライベートチャットは user_id など
target_id = event.get_target_id()

# セッション固有の識別子、形式: {platform}:{detail_type}:{target_id}
session_id = event.get_session_id()
# 例: "telegram:private:12345"、"qq:group:67890"
```

`get_target_id()` は以下の順序で最初の非空値を返します：`group_id` → `channel_id` → `guild_id` → `thread_id` → `user_id`。コンテキスト管理や状態保存など、統一された識別子でセッションを管理する必要があるシーンに適しています。

### メッセージ関連メソッド

```python
# メッセージ内容の取得
message_segments = event.get_message()
alt_message = event.get_alt_message()
text = event.get_text()

# 送信者情報の取得
user_id = event.get_user_id()
nickname = event.get_user_nickname()
sender = event.get_sender()

# グループ情報の取得
group_id = event.get_group_id()

# メッセージタイプの判定
is_msg = event.is_message()
is_private = event.is_private_message()
is_group = event.is_group_message()

# メッセージへの @ について
is_at = event.is_at_message()
has_mention = event.has_mention()
mentions = event.get_mentions()
```

### コマンド情報

```python
# コマンド情報の取得
cmd_name = event.get_command_name()
cmd_args = event.get_command_args()
cmd_raw = event.get_command_raw()

# コマンドかどうかの判定
is_cmd = event.is_command()
```

### 返信機能

```python
# 基本的な返信
await event.reply("これはメッセージです")

# 送信方法を指定する
await event.reply("http://example.com/image.jpg", method="Image")

# ユーザーへの @ と返信メッセージ
await event.reply("こんにちは", at_users=["user1"], reply_to="msg_id")

# 全体への @
await event.reply("お知らせ", at_all=True)

# プラットフォーム固有の修飾メソッドを使用（via パラメータ）
await event.reply("看板内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])

# 送信チェーンを取得し、自由に修飾メソッドと送信方法を追加（連続する複数の修飾/アクション型メソッドに適しています）
await event.send_chain().Expire(3600).Board("看板内容")
await event.send_chain().DismissBoard()

# OneBot12 メッセージセグメントを使用した返信
from ErisPulse.Core.Event import MessageBuilder
msg = MessageBuilder().text("Hello").image("url").build()
await event.reply_ob12(msg)

# 返信の待機
reply = await event.wait_reply(timeout=30)
```

### プラットフォーム機能の確認

```python
# 現在のプラットフォームが特定の送信方法をサポートしているかを確認
if event.supports("Image"):
    await event.reply(url, method="Image")

# 現在のプラットフォームで利用可能なすべての送信方法を一覧表示
methods = event.available_methods()
# ["Text", "Image", "Voice", ...]
```

### 返信メソッド

`reply()` メソッドは `method` パラメータで送信タイプを指定し、2つの便利なブールパラメータをサポートしています。

```python
# 簡単なテキスト返信
await event.reply("こんにちは")

# 送信者への @付き返信
await event.reply("こんにちは", at_sender=True)

# 現在のメッセージを引用した返信
await event.reply("受信しました", reply_to_message=True)

# 組み合わせ
await event.reply("受信しました", at_sender=True, reply_to_message=True)

# 画像の送信（method パラメータを使用）
if event.supports("Image"):
    await event.reply("http://example.com/img.jpg", method="Image")
else:
    await event.reply("[画像] http://example.com/img.jpg")
```

**パラメータの説明**：

| パラメータ | 型 | 説明 |
|------|------|------|
| `content` | str | 送信内容 |
| `method` | str | 送信方法、デフォルトは "Text"、選択肢は "Image"/"Voice"/"Video"/"File" など |
| `at_sender` | bool | 送信者を @ するか（自動的に user_id を抽出） |
| `quote` | bool | 現在のメッセージを引用して返信するか（自動的に message_id を抽出） |
| `at_users` | list[str] | 指定したユーザーリストを @ |
| `reply_to` | str | 手動で指定したメッセージ ID を返信先とする |
| `at_all` | bool | 全体を @ するか |

### インタラクションメソッド

```python
# confirm — 会話の確定（True/False/None を返す）
if await event.confirm("この操作を実行しますか？"):
    await event.reply("確定しました")

# Text 以外の方式で確認プロンプトを送信
if await event.confirm("http://example.com/image.jpg", method="Image"):
    await event.reply("画像の提示を確認しました")

# choose — 選択メニュー（オプションのインデックスまたは None を返す）
choice = await event.choose("色を選んでください：", ["赤", "緑", "青"])

# options_format="auto"（デフォルト）method に合わせて自動でスタイルを選択します：
# Markdown→順序なしリスト（- 1.オプション）、Html→順序付きリスト（<ol>）、その他→プレーンテキストリスト
# テキスト系メソッド（Markdown/Html 等）はデフォルトで末尾にオプションを統合します
# merge_prompt=True を指定すると任意の method で強制的に統合が可能です。placeholder でプレースホルダーをカスタマイズできます
choice = await event.choose(
    "## 選択してください\n{options}", ["A", "B"],
    method="Markdown", merge_prompt=True,
)

# collect — フォーム収集（{key: value} の辞書または None を返す）
data = await event.collect([
    {"key": "name", "prompt": "お名前を入力してください："},
    {"key": "age", "prompt": "年齢を入力してください：",
     "validator": lambda e: e.get_text().isdigit()},
    {"key": "avatar", "prompt": "アバターを送信してください：", "method": "Image"},
])

# wait_for — 条件を満たす任意のイベントを待機する
evt = await event.wait_for(event_type="notice", condition=lambda e: ..., timeout=120)

# conversation — 多ラウンド会話のコンテキスト
conv = event.conversation(timeout=60)
await conv.say("ようこそ！")
```

> 詳細なインタラクションメソッドのパラメータ説明やその他の例については、[Event クラスの詳細](../developer-guide/modules/event-wrapper.md)と[Conversation 多ラウンド会話](../advanced/conversation.md)を参照してください。

### ユーティリティメソッド

```python
# ディクショナリへ変換（アンダースコアで始まる内部キーはフィルタリングされます）
event_dict = event.to_dict()

# 原始データの取得
raw = event.get_raw()
raw_type = event.get_raw_type()
```

### 処理制御

`event.done(claim=, stop=)` は、「認証」と「ブロック」の2つの直交するセマンティクスを統一して制御します：

- **認証（claim）**：イベントが処理済みであることをマーク（`_processed`）、コマンドディスパッチャーはこれによりスキップします。
- **ブロック（stop）**：低優先度のハンドラーへの伝播を防ぐ（`_propagation_stopped`）。

```python
# 認証 + ブロック（デフォルト）
event.done()

# 認証のみ、ブロックしない（低優先度のオブザーバーでも確認可能）
event.done(stop=False)

# ブロックのみ、認証しない（ファイアウォール / レート制限など）
event.done(claim=False)

# mark_processed はメインメソッドで、done はそのエイリアスです
event.mark_processed()             # event.done() と等価
event.mark_processed(stop=False)   # event.done(stop=False) と等価

# ステータスの確認
event.is_processed()  # 既に認証済みか
event.is_stopped()    # 伝播がブロック済みか
```

### プラットフォーム拡張メソッド

アダプターは Event にプラットフォーム固有のメソッドを登録でき、それらは対応するプラットフォームのインスタンスでのみ使用可能です。

#### ユーザー：プラットフォーム拡張メソッドの使用

アダプターがプラットフォーム固有のメソッドを登録した後は、イベントハンドラー内で直接呼び出せます。各プラットフォームのメソッドは異なりますが、対応する[プラットフォームガイド](../platform-guide/)を参照してください。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出す
    if platform == "email":
        subject = event.get_subject()           # メール固有
        attachments = event.get_attachments()   # メール固有
```

#### プラットフォームで登録されたメソッドの確認

```python
from ErisPulse.Core.Event import get_platform_event_methods

# 特定のプラットフォームに登録されているメソッドを表示
methods = get_platform_event_methods("email")
# ["get_subject", "get_from", "get_attachments", ...]

# 動的に判定して呼び出す
for method_name in get_platform_event_methods(event.get_platform()):
    method = getattr(event, method_name)
    print(f"{method_name}: {method()}")
```

#### プラットフォームメソッドの分離

異なるプラットフォームで登録されたメソッドは互いに干渉しません：

```python
# メールイベント - メール固有のメソッドのみ
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram イベント - Telegram 固有のメソッドのみ
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private"
event.get_subject()      # ❌ AttributeError
```

#### `hasattr` / `dir` サポート

```python
hasattr(event, "get_subject")   # platform="email" の時のみ True を返します
"get_subject" in dir(event)     # 同上
```

### アダプター：プラットフォーム拡張メソッドの登録

アダプターはデコレータを使用して Event にプラットフォーム固有のメソッドを登録できます。メソッドの最初のパラメータは `self`（Event インスタンス）で、自由にイベントデータにアクセスできます。

#### 単一のメソッド登録

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("email")
def get_subject(self):
    """メールの件名を取得"""
    return self.get("email_raw", {}).get("subject", "")

@register_event_method("email")
def get_from(self):
    """送信者を取得"""
    return self.get("email_raw", {}).get("from", {})
```

#### 複数のメソッド登録（Mixin クラス）

メソッドが多い場合は、Mixin クラスを使用して一括登録することを推奨します：

```python
from ErisPulse.Core.Event import register_event_mixin

class EmailEventMixin:
    def get_subject(self):
        return self.get("email_raw", {}).get("subject", "")

    def get_from(self):
        return self.get("email_raw", {}).get("from", {})

    def get_attachments(self):
        return self.get("email_raw", {}).get("attachments", [])

# すべてのメソッドを一度に登録
register_event_mixin("email", EmailEventMixin)
```

#### 返り値の仕様

| 場合 | 返り値 | ユーザー使用方法 |
|------|--------|------------|
| データの返却（テキスト、辞書など） | 直接返り値 | `subject = event.get_subject()` |
| 操作の実行（メッセージ送信など） | `asyncio.Task` を返す | `task = event.do_something()` 可選で `await` |

> **推奨**：データ以外の返り値を持つメソッドは `asyncio.Task` を返すようにします。これにより、ユーザーが自分で `await` するかどうかを選択でき、`await` しなくても操作は実行完了します。

```python
@register_event_method("email")
def forward_email(self, to_address: str):
    """メールを転送 — Task を返すため、ユーザーが await するかどうかを決定できます"""
    import asyncio
    return asyncio.create_task(
        self._do_forward(to_address)
    )

# ユーザーは await して結果を待機できます
await event.forward_email("user@example.com")

# または await せず、バックグラウンドで操作を実行できます
event.forward_email("user@example.com")
```

#### メソッドの登録解除

```python
from ErisPulse.Core.Event import unregister_event_method, unregister_platform_event_methods

# 単一のメソッドを登録解除
unregister_event_method("email", "get_subject")

# 特定のプラットフォームのすべてのメソッドを登録解除（アダプターシャットダウン時に呼び出します）
unregister_platform_event_methods("email")
```

#### 組み込みメソッドのオーバーライド

`register_event_mixin` / `register_event_method` は、Event の組み込みメソッド（`confirm`、`choose`、`collect`、`wait_reply`、`reply` など）のオーバーライドをサポートします。登録されたプラットフォーム固有のメソッドは、Event.__getattribute__ を通じて組み込みメソッドより優先して適用されるため、アダプターはプラットフォーム独自のインタラクション実装を提供できます。

組み込み実装は `_builtin_*` 関数としてエクスポートされており、オーバーライドする側はそれらをフォールバックとして呼び出せます：

```python
from ErisPulse.Core.Event import register_event_mixin, _builtin_choose

class YunhuEventMixin:
    async def choose(self, prompt, options, timeout=60, method="Text"):
        # 雲湖プラットフォームはボタンコンポーネントを使用
        buttons = [[{"text": opt} for opt in options]]
        await self.reply(prompt)
        # ...ボタンのコールバックやテキスト応答を待機...
        # 組み込みロジックにフォールバック
        return await _builtin_choose(self, None, options, timeout, "Text")

register_event_mixin("yunhu", YunhuEventMixin)

## 跨プラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` はプラットフォーム名として `"*"` を渡すことをサポートしており、登録されたメソッドは**すべてのプラットフォーム**の Event インスタンス上で使用可能です。AI対話やコンテキスト管理など、プラットフォームをまたがって再利用する必要がある機能モジュールに適しています。

### 跨プラットフォームメソッドの登録

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    """self は Event インスタンスであり、イベントデータや組み込みメソッドに自由にアクセス可能です"""
    await self.reply(f"AI: {prompt}")
```

登録後、すべてのプラットフォームのイベントハンドラから呼び出すことができます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handler(event):
    await event.ai_chat(event.get_text())
```

### メソッド解決の優先順位

Event メソッドに属性アクセスする場合、解決順序は以下のようになります：

1. **プラットフォーム固有のメソッド**（現在のプラットフォームでのオーバーライド）
2. **ワイルドカードメソッド**（`"*"` で登録された跨プラットフォームメソッド）
3. **組み込みメソッド**（`reply`、`confirm` など）
4. **辞書キーによるアクセス**

> そのため、ワイルドカードメソッドは組み込みメソッド（`reply` など）をオーバーライドすることは可能ですが、同名のプラットフォーム固有のメソッドによってさらにオーバーライドされます。

## 優先順位システム

イベントハンドラーは優先順位をサポートしており、数値が大きいほど優先度が高くなります：

```python
# 高優先度のハンドラーは先に実行されます
@message.on_message(priority=10)
async def high_priority_handler(event):
    pass

# 低優先度のハンドラーは後に実行されます
@message.on_message(priority=0)
async def low_priority_handler(event):
    pass



====
高级主题
====


### Conversation 多轮对话

# Conversation 多輪対話

`Conversation` クラスは、同じセッション内で複数回のやり取りを行う便利な方法を提供し、ガイド付き操作、情報収集、対話形式の質問応答などの場面に適しています。

## 対話の作成

`Event` オブジェクトの `conversation()` メソッドを使用して作成します：

```python
from ErisPulse.Core.Event import command

@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)

    await conv.say("🎮 知識クイズへようこそ！")

    answer = await conv.choose("第1問：Pythonの作成者は誰ですか？", [
        "Guido van Rossum",
        "James Gosling",
        "Dennis Ritchie",
    ])

    if answer is None:
        await conv.say("タイムアウトしました。次回お試しください！")
        return

    if answer == 0:
        await conv.say("正解です！")
    else:
        await conv.say("不正解です。正解は Guido van Rossum です")

    conv.stop()
```

## コア API

### say(content, **kwargs)

メッセージを送信し、`self` を返してメソッドチェーンが可能になります：

```python
await conv.say("1行目").say("2行目").say("3行目")
```

送信方法を指定することもできます：

```python
await conv.say("https://example.com/image.jpg", method="Image")
```

### wait(prompt=None, timeout=None)

ユーザーからの返信を待機し、`Event` オブジェクトまたは `None`（タイムアウト）を返します：

```python
# 簡単な待機
resp = await conv.wait()
if resp:
    text = resp.get_text()

# プロンプトを送信して待機
resp = await conv.wait(prompt="あなたの名前を入力してください：")

# カスタムタイムアウトを使用（対話のデフォルトタイムアウトを上書き）
resp = await conv.wait(prompt="10秒以内に返信してください：", timeout=10)
```

### confirm(prompt=None, **kwargs)

ユーザーの確認（はい/いいえ）を待機し、`True` / `False` / `None`（タイムアウト）を返します：

```python
result = await conv.confirm("すべてのデータを削除してもよろしいですか？")
if result is True:
    await conv.say("削除しました")
elif result is False:
    await conv.say("キャンセルしました")
else:
    await conv.say("タイムアウトしました")
```

内部的に認識される確認用語：`はい/yes/y/確認/確定/好/ok/true/対/うん/行/同意/問題ない/可能/当然...`

内部的に認識される否定用語：`否/no/n/キャンセル/不/不要/行かない/cancel/false/間違っている/違っている/別/拒否...`

### choose(prompt, options, **kwargs)

ユーザーが選択肢から選択するのを待機し、選択肢のインデックス（0ベース）または `None` を返します：

```python
choice = await conv.choose("色を選択してください：", ["赤", "緑", "青"])
if choice is not None:
    colors = ["赤", "緑", "青"]
    await conv.say(f"選択した色は {colors[choice]} です")
```

ユーザーは、番号（`1`/`2`/`3`）または選択肢のテキスト（`赤`）を入力することで選択できます。

`options_format="auto"`（デフォルト）は、method に応じて自動的に組み込みのスタイルを選択します：Markdown→非順序リスト、Html→順序リスト、その他→単純なテキストリスト。
`"list"`、`"inline"`、`"md"`、`"html"` またはカスタム関数もサポートします。

`merge_prompt=True` を使用して1つのメッセージに統合し、プレースホルダで選択肢の挿入位置を制御できます（デフォルトは `{options}`、`placeholder` でカスタマイズ可能）：

```python
choice = await conv.choose(
    "## 選択してください\n{options}",
    ["選択肢A", "選択肢B"],
    method="Markdown",
    merge_prompt=True,
)

# カスタムプレースホルダ
choice = await conv.choose(
    "選択してください: [choices]",
    ["選択肢A", "選択肢B"],
    placeholder="[choices]",
)
```

### collect(fields, **kwargs)

複数ステップで情報を収集し、データ辞書または `None` を返します：

```python
data = await conv.collect([
    {"key": "name", "prompt": "名前を入力してください"},
    {"key": "age", "prompt": "年齢を入力してください",
     "validator": lambda e: e.get("alt_message", "").strip().isdigit(),
     "retry_prompt": "年齢は数字でなければなりません。再度入力してください"},
    {"key": "city", "prompt": "都市を入力してください"},
])

if data:
    await conv.say(f"登録完了！\n名前: {data['name']}\n年齢: {data['age']}\n都市: {data['city']}")
else:
    await conv.say("登録が中断されました")
```

フィールドの設定：

| パラメータ | 説明 | デフォルト値 |
|------|------|--------|
| `key` | フィールドのキー名（必須） | - |
| `prompt` | プロンプトメッセージ | `"{key} を入力してください"` |
| `validator` | 関数を受け取り、bool を返す検証関数 | なし |
| `retry_prompt` | 検証失敗時の再入力プロンプト | `"入力が無効です。再度入力してください"` |
| `max_retries` | 最大再試行回数 | 3 |
| `condition` | 関数を受け取り、bool を返す条件関数 | なし |

**条件付きフィールド**：`condition` を使用して動的フォームを実現し、条件が満たされた場合にのみフィールドを収集できます：

```python
data = await conv.collect([
    {"key": "has_car", "prompt": "車をお持ちですか？（はい/いいえ）"},
    {"key": "car_brand", "prompt": "車種を入力してください",
     "condition": lambda d: d.get("has_car", "").lower() in ("はい", "yes", "y")},
])
```

### stop()

手動で対話を終了し、`is_active` を `False` に設定します：

```python
conv.stop()
```

### is_active

対話がアクティブかどうか：

```python
if conv.is_active:
    await conv.say("対話はまだ進行中です")
```

## アクティブ状態の管理

以下の状況で、対話は自動的に非アクティブになります：

1. `stop()` メソッドが呼び出された
2. `wait()` がタイムアウトして `None` を返した
3. `collect()` がいずれかのステップでタイムアウトまたは再試行回数を超え、`None` を返した

非アクティブになった後、`wait`/`confirm`/`choose`/`collect` などのすべてのインタラクションメソッドは即座に `None` を返し、ユーザーからの入力を待つことはありません。

## 分岐とジャンプ

### @conv.branch(name) デコレータ

`branch()` を使用して対話の分岐を登録し、`goto()` を使用して分岐間をジャンプできます：

```python
@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)

    @conv.branch("main")
    async def main_menu():
        await conv.say("=== メインメニュー ===\n1. 情報\n2. 設定\n3. 終了")
        resp = await conv.wait()
        if resp is None:
            return
        text = resp.get_text().strip()
        if text == "1":
            await conv.goto("profile")
        elif text == "2":
            await conv.goto("settings")
        elif text == "3":
            await conv.say("さようなら！")
            conv.stop()

    @conv.branch("profile")
    async def profile():
        await conv.say("=== 情報 ===\n名前: Alice\n0. 戻る")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    @conv.branch("settings")
    async def settings():
        await conv.say("=== 設定 ===\n1. 通知の切り替え\n0. 戻る")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    await conv.start()  # 最初に登録された分岐から開始
```

### conv.start(name=None)

対話を開始し、デフォルトでは最初に登録された分岐から開始します：

```python
await conv.start()          # 最初の分岐から開始
await conv.start("settings") # 指定された分岐から開始
```

## コンテキストと永続化

### conv.context

各対話インスタンスには、分岐間で状態を共有するための組み込みの `context` 辞書があります：

```python
@conv.branch("step1")
async def step1():
    conv.context["username"] = resp.get_text().strip()
    await conv.goto("step2")

@conv.branch("step2")
async def step2():
    name = conv.context.get("username", "不明")
    await conv.say(f"こんにちは、{name}！")
```

### save() / resume() / clear_saved()

対話は永続化が可能で、タイムアウトや中断後に復元できます：

```python
# 対話の状態を保存
conv_id = conv.save()
# conv_id = "user_123_group_456"  # ユーザーとグループに基づいて自動生成

# ... 同じセッション内で後で復元 ...
conv2 = event.conversation()
if conv2.resume():
    await conv2.say("戻ってきました！以前の対話を再開します")
else:
    await conv2.say("以前の対話が見つかりませんでした")

# 保存された対話を削除
conv.clear_saved()
```

## 一般的なフロー・パターン

### ガイド付き登録

```python
@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)

    await conv.say("登録へようこそ！")

    data = await conv.collect([
        {"key": "username", "prompt": "ユーザー名を入力してください（3-20文字）",
         "validator": lambda e: 3 <= len(e.get_text().strip()) <= 20},
        {"key": "email", "prompt": "メールアドレスを入力してください",
         "validator": lambda e: "@" in e.get_text() and "." in e.get_text(),
         "retry_prompt": "メールアドレスの形式が正しくありません。再度入力してください"},
    ])

    if not data:
        await event.reply("登録がキャンセルされました")
        return

    confirmed = await conv.confirm(
        f"登録情報の確認？\nユーザー名: {data['username']}\nメールアドレス: {data['email']}"
    )

    if confirmed:
        await conv.say("✅ 登録完了！")
    else:
        await conv.say("❌ 登録がキャンセルされました")
```

### ループ対話

```python
@command("chat")
async def chat_handler(event):
    conv = event.conversation(timeout=120)
    await conv.say("対話モードに入りました。「退出」で終了します")

    while conv.is_active:
        resp = await conv.wait()
        if resp is None:
            await conv.say("タイムアウトしました。対話が終了します")
            break

        text = resp.get_text().strip()

        if text == "退出":
            await conv.say("さようなら！")
            conv.stop()
        elif text == "help":
            await conv.say("利用可能なコマンド：退出、help、status")
        elif text == "status":
            await conv.say("対話はアクティブです")
        else:
            await conv.say(f"入力内容：{text}")
```



### MessageBuilder 详解

# MessageBuilder 詳細

`MessageBuilder` は、ErisPulseが提供するOneBot12標準のメッセージセグメント構築ツールです。構造化されたメッセージ内容を構築し、`Send.Raw_ob12()` と組み合わせて使用します。

## 導入方法

`MessageBuilder` は以下の2つの導入方法をサポートしています（効果は同じで、1つ目の方法を推奨します）：

```python
from ErisPulse.Core.Event import MessageBuilder        # 推奨、パッケージ経由でのエクスポート
from ErisPulse.Core.Event.message_builder import MessageBuilder  # モジュール直接インポート
```

## ダブルモードメカニズム

MessageBuilder は2つの使用モードを提供し、Pythonのデスクリプタ機構（`__get__`）を通じてクラスレベルとインスタンスレベルでの異なる動作を実現します：クラスからメソッドを呼び出す場合、`__get__` は静的メソッドの実行結果を返します；インスタンスからメソッドを呼び出す場合、`self` を返してチェーンコールをサポートします。

### チェーンコールモード（インスタンス）

`MessageBuilder()` をインスタンス化して使用します。各メソッドは `self` を返し、チェーンコールをサポートし、最後に `.build()` を使ってメッセージセグメントのリストを取得します：

```python
from ErisPulse.Core.Event.message_builder import MessageBuilder

segments = (
    MessageBuilder()
    .text("你好！")
    .image("https://example.com/photo.jpg")
    .build()
)
# [
#     {"type": "text", "data": {"text": "你好！"}},
#     {"type": "image", "data": {"file": "https://example.com/photo.jpg"}}
# ]
```

### 快速構築モード（静的）

クラスから直接メソッドを呼び出します。各メソッドは直接メッセージセグメントのリストを返し、単一セグメントのメッセージに適しています：

```python
# 直接 list[dict] を返します。.build() は不要です。
segments = MessageBuilder.text("你好！")
# [{"type": "text", "data": {"text": "你好！"}}]
```

## メッセージセグメントのタイプ

| メソッド | タイプ | データパラメータ | 説明 |
|------|------|---------|------|
| `text(text)` | text | `text` | テキストメッセージ |
| `image(file)` | image | `file` | 画像メッセージ |
| `audio(file)` | audio | `file` | 音声メッセージ |
| `video(file)` | video | `file` | 動画メッセージ |
| `file(file, filename?)` | file | `file`, `filename` | ファイルメッセージ |
| `mention(user_id, user_name?)` | mention | `user_id`, `user_name` | @メンション（ユーザー指定） |
| `at(user_id, user_name?)` | mention | `user_id`, `user_name` | `mention` のエイリアス |
| `reply(message_id)` | reply | `message_id` | 返信メッセージ |
| `at_all()` | mention_all | - | @全員（全員メンション） |
| `custom(type, data)` | カスタム | カスタム | カスタムメッセージセグメント |

## Send と組み合わせて使用する

構築したメッセージセグメントのリストは、`Send.Raw_ob12()` を通じて送信します。

```python
from ErisPulse import sdk
from ErisPulse.Core.Event.message_builder import MessageBuilder

# チェーン構築 + 送信
segments = (
    MessageBuilder()
    .mention("user123", "张三")
    .text(" 请查看这张图片")
    .image("https://example.com/photo.jpg")
    .build()
)
await sdk.adapter.myplatform.Send.To("group", "group456").Raw_ob12(segments)
```

### Event と組み合わせた返信

```python
from ErisPulse.Core.Event import command

@command("report")
async def report_handler(event):
    await event.reply_ob12(
        MessageBuilder()
        .text("📊 日报汇总\n")
        .text("今日完成任务: 5\n")
        .text("进行中任务: 3")
        .build()
    )
```

## ユーティリティメソッド

### copy()

現在のビルダーをコピーし、同じ基本内容に基づいて複数のメッセージバリエーションを作成するために使用します。

```python
base = MessageBuilder().text("基础内容").mention("admin")

# 同じプレフィックスに基づいて異なるメッセージを構築
msg1 = base.copy().text(" 变体A").build()
msg2 = base.copy().text(" 变体B").image("img.jpg").build()
```

### clear()

追加されたメッセージセグメントをクリアし、同じビルダーを再利用します。

```python
builder = MessageBuilder()

for user_id in ["user1", "user2", "user3"]:
    builder.clear()
    msg = builder.mention(user_id).text(" 你好！").build()
    await adapter.Send.To("user", user_id).Raw_ob12(msg)
```

### len() / bool()

```python
builder = MessageBuilder()
print(bool(builder))   # False

builder.text("Hello")
print(len(builder))    # 1
print(bool(builder))   # True
```

## カスタムメッセージセグメント

`custom()` メソッドを使用して、プラットフォーム拡張のメッセージセグメントを追加します。

```python
# プラットフォーム固有のメッセージセグメントを追加
segments = (
    MessageBuilder()
    .text("请填写表单：")
    .custom("yunhu_form", {"form_id": "12345"})
    .build()
)
```

> カスタムメッセージセグメントは、対応するプラットフォームのアダプターでのみ有効です。他のアダプターは認識しないメッセージセグメントを無視します。

## 完全な例

### マルチエレメントメッセージ

```python
segments = (
    MessageBuilder()
    .reply(event.get_id())                    # 元のメッセージに返信
    .mention(event.get_user_id())             # 送信者に@メンション
    .text(" 这是你的查询结果：\n")             # テキスト
    .image("https://example.com/chart.png")   # 画像
    .text("\n详细数据见附件：")
    .file("https://example.com/data.csv", filename="data.csv")
    .build()
)
await event.reply_ob12(segments)
```

### スタティックファクトリ + チェーンの組み合わせ

```python
# 単一セグメントのメッセージを迅速に構築
simple_msg = MessageBuilder.text("简单文本")

# 複雑なメッセージをチェーン構築
complex_msg = (
    MessageBuilder()
    .at_all()
    .text(" 📢 公告：")
    .text("今天下午3点开会")
    .build()
)
```



### HTTP 客户端

# ネットワーククライアント

ErisPulse は、HTTPリクエスト、WebSocket接続、および接続プール管理を統合した統一されたネットワーククライアントを提供しています。モジュールやアダプターは、**aiohttp / httpx / requests** などのサードパーティライブラリを直接インポートするのではなく、このクライアントを優先的に使用する必要があります。

## 概要

ネットワーククライアントの主な機能：

- **統一インターフェース**：`get` / `post` / `put` / `delete` / `patch` / `request` メソッドを提供
- **WebSocketクライアント**：`ws_connect` を通じてクライアント側のWebSocket接続を確立
- **自動ログ**：すべてのリクエストに対して自動的にログと統計情報を記録
- **ライフサイクル統合**：各リクエストは `client.request` ライフサイクルイベントをトリガーし、WebSocket接続は `client.ws.connect` イベントをトリガー
- **リトライサポート**：自動リトライ回数と間隔を設定可能
- **タイムアウト制御**：接続タイムアウトとリクエストタイムアウトを個別に制御
- **接続プールの再利用**：aiohttp.ClientSessionに基づく接続プール管理
- **例外体系**：aiohttpの例外は自動的にErisPulseの例外（ClientError体系）に変換される

## 快速開始

### HTTPリクエスト

```python
from ErisPulse.Core import client

# GETリクエスト
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POSTリクエスト
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket接続

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## HttpResponse

すべてのリクエストメソッドは `HttpResponse` オブジェクトを返します：

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTPステータスコード (例: 200, 404)
resp.reason       # str | None - ステータス説明 (例: "OK")
resp.headers      # レスポンスヘッダー (大文字小文字を区別しない)
resp.content_type # str | None - Content-Type
resp.url          # 最終URL (リダイレクトにより変化する可能性がある)
resp.raw          # ベースの生のレスポンスオブジェクト (現在はaiohttp.ClientResponse)

# レスポンスボディの読み取り
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # JSONを解析
text = await resp.text("gbk")  # 指定されたエンコーディング
```

## リクエストメソッド

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# JSONリクエストボディ
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# フォームリクエストボディ
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# バイナリデータ
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# ファイルアップロード (filesパラメータを使用、aiohttpをインポートする必要なし)
# 形式: {フィールド名: ファイルオブジェクト/bytes/(filename, file)/(filename, file, content_type)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "プロフィール画像"},            # 任意: 通常のフォームフィールドを同時に送信
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# 簡略化された書き方: ファイルオブジェクトを直接渡す
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# メモリ内データを直接アップロード (ファイルを保存する必要なし)
import io

resp = await client.post(
    "https://api.example.com/upload",
    files={"file": ("data.txt", io.BytesIO(b"file content"), "text/plain")},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### 一般的なrequest

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## パラメータの説明

### HTTPリクエストパラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `url` | `str` | リクエストURL |
| `params` | `dict[str, str]` | クエリパラメータ (オプション) |
| `headers` | `dict[str, str]` | 追加のリクエストヘッダー (オプション) |
| `data` | `Any` | リクエストボディ (フォームまたはバイナリデータ) (オプション) |
| `json` | `Any` | JSONリクエストボディ (オプション) |
| `files` | `dict[str, Any]` | ファイルアップロードフィールド (オプション、multipart/form-dataを自動的に構築) |
| `timeout` | `float` | 今回のリクエストのタイムアウト (秒) (オプション、デフォルト値を上書き) |
| `max_retries` | `int` | 今回の最大リトライ回数 (オプション、デフォルト値を上書き) |

### ws_connect パラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `url` | `str` | WebSocketサーバーのURL |
| `headers` | `dict[str, str]` | 追加のリクエストヘッダー (オプション) |
| `heartbeat` | `float` | ハートビート間隔 (秒) (オプション) |

## タイムアウトとリトライ

```python
from ErisPulse.Core import HttpClient

# カスタムタイムアウトを持つクライアントを作成
client = HttpClient(
    timeout=60,           # リクエスト全体のタイムアウト 60秒
    connect_timeout=5,    # 接続のタイムアウト 5秒
    max_retries=3,        # 失敗時の自動リトライ 3回
    retry_delay=2,        # リトライ間隔 2秒
)

# 今回のリクエストでタイムアウトを上書き
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

## デフォルトヘッダーのカスタマイズ

```python
client = HttpClient(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## リクエスト統計

```python
from ErisPulse.Core import client

# 統計を確認
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# 統計をリセット
client.reset_stats()
```

## ライフサイクルイベント

### HTTPリクエストイベント

各リクエストの完了後に `client.request` イベントがトリガーされ、モニタリングに使用できます：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### WebSocket接続イベント

WebSocket接続が確立された後に `client.ws.connect` イベントがトリガーされます：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS接続: {event_data['url']}")
```

## コンテキストマネージャー

```python
# コンテキストマネージャーとして使用し、セッションを自動的に閉じる
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocketクライアント

`client.ws_connect()` を通じてWebSocketクライアント接続を確立し、`ClientWebSocket` オブジェクトを返します。クライアントとサーバー側のWebSocketは同じ `WebSocketConnectionBase` 基底クラスを共有し、send/receive/iterインターフェースは完全に同じです。

### 基本的な使い方

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### メッセージの受信

#### 高レベルメソッド (推奨)

メッセージの種類を自動的にフィルタリングし、切断時に `WebSocketDisconnect` をスローします：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# 1件のメッセージを受信
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# 受信のイテレーション (切断時に自動的に停止)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### 低レベルメソッド

`receive()` と `iter_messages()` を使用して、元のメッセージの種類を処理し、TEXT / BINARY / CLOSE / ERROR を区別できます：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# 1件のメッセージを受信
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# メッセージのイテレーション (CLOSE/ERROR時に自動的に停止)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"テキスト: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"バイナリ: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` は、下層ライブラリに依存しない統一されたWebSocketメッセージの型です：

| 属性 | 型 | 説明 |
|------|------|------|
| `type` | `str` | メッセージの種類: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | メッセージのデータ |

### ClientWebSocket 属性

| 属性 | 型 | 説明 |
|------|------|------|
| `url` | `URL` | 接続URL |
| `headers` | `Headers` | レスポンスヘッダー |
| `closed` | `bool` | 接続が閉じられているかどうか |
| `raw` | `object` | 下層の生のオブジェクト (aiohttp.ClientWebSocketResponse) |

### ライフサイクルフック

`サービス側 WebSocketConnection` と同じで、`on_disconnect` と `on_error` コールバックをサポートします：

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"接続が切断されました: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"接続エラー: {error}")
```

### 接続の切断

```python
await ws.close(code=1000, reason="正常な切断")
```

## 例外体系

ErisPulse は、統一された例外階層を定義しています。`sdk.client` からリクエストを発行すると、下層の aiohttp 例外が自動的に ErisPulse 例外に変換されます。

> **後方互換性**：aiohttp.ClientSession を直接使用する古いモジュール/アダプターは、完全に影響を受けません。例外の変換は `sdk.client` からリクエストを発行する場合にのみ有効で、aiohttp を直接使用するコードは依然として `aiohttp.ClientError` などの生の例外をキャッチします。2つの方法は共存可能です。

### 例外階層

```
ErisPulseError
├── ClientError                  # HTTP/WSクライアントリクエスト例外の基底クラス
│   ├── ClientConnectionError    # 接続失敗 (DNS解析失敗、接続拒否、ネットワーク到達不能)
│   ├── ClientTimeoutError       # 接続タイムアウトまたはリクエストタイムアウト
│   └── HTTPStatusError          # HTTP 4xx/5xxステータスコードエラー
└── WebSocketError               # WebSocket例外の基底クラス
    └── WebSocketDisconnect      # WebSocket接続が切断された (クライアントとサーバー共通)
```

### 例外のキャッチ

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import (
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)

# HTTPリクエスト例外の処理
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("サーバーに接続できません")
except ClientTimeoutError:
    print("リクエストがタイムアウトしました")
except ClientError as e:
    print(f"リクエストが失敗しました: {e}")

# WebSocket例外の処理
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"接続が切断されました: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocketエラー: {e}")
```

### 統一されたキャッチ

`ClientError` を使用して、HTTP/WSクライアントリクエストのすべての例外を統一的にキャッチします：

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"クライアントエラー: {e}")
```

### HTTPStatusError

リクエスト後にステータスコードをチェックして例外をスローする必要がある場合、手動で使用できます：

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## アダプターでの使用

アダプターは、グローバルクライアントまたは独自のクライアントインスタンスを使用して、プラットフォームAPIリクエストを送信できます：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.errors import ClientError

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        try:
            resp = await client.post(
                f"https://api.platform.com/{endpoint}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return await resp.json()
        except ClientError as e:
            self.logger.error(f"API呼び出しに失敗しました: {e}")
            raise
```

> `from ErisPulse import sdk` を使用して `sdk.client` を使うことも可能で、効果は同じです。

## 最適な実践

1. **グローバルクライアントを優先する**：`from ErisPulse.Core import client` を使用してグローバルシングルトンを取得し、フレームワークの統一管理と監視を容易にする
2. **aiohttpの直接インポートを避ける**：`client` を使用して `aiohttp.ClientSession` を置き換え、将来の下層実装の変更に伴うコードの変更を必要としない。古いコードで直接 aiohttp を使用しても正常に動作し、2つの方法は共存可能
3. **ErisPulseの例外体系を使用する**：`sdk.client` からリクエストする際は `aiohttp.ClientError` ではなく `ClientError` をキャッチし、特定のHTTPライブラリに依存しないコードを確保する。直接 aiohttp を使用する古いコードは影響を受けない
4. **適切なタイムアウトを設定する**：APIの応答速度に応じて適切なタイムアウト時間を設定し、長時間のブロッキングを避ける
5. **リトライメカニズムを使用する**：不安定なAPIに対してリトライを有効化し、信頼性を向上させる
6. **リクエスト統計を監視する**：`sdk.client.stats` または `client.request` ライフサイクルイベントを使用してリクエスト状況を監視する
7. **WebSocketで高レベルメソッドを使用する**：`iter_text` / `iter_json` などの高レベルメソッドを優先し、メッセージの種類を区別する必要がある場合にのみ `iter_messages` を使用する



### SQL 查询构建器

# SQLクエリビルダー

ErisPulseのStorageモジュールは、メソッドチェーンスタイルの汎用SQLクエリビルダーを提供し、カスタムテーブルの作成、クエリ、更新、削除操作をサポートしています。

## アーキテクチャ設計

```
Bases/storage.py                    Core/storage.py
┌─────────────────────┐             ┌──────────────────────────┐
│  BaseStorage (ABC)  │◄────────────│  StorageManager          │
│  BaseQueryBuilder   │             │  (SQLite concrete impl)  │
│    (ABC)            │             │                          │
└─────────────────────┘             │  SQLiteQueryBuilder      │
                                    │  AlterTableBuilder       │
                                    └──────────────────────────┘
```

- `BaseStorage` / `BaseQueryBuilder` は抽象基底クラスであり、統一されたインターフェースを定義し、将来的に他のストレージメディア（Redis、MySQLなど）への拡張をサポートします。
- `StorageManager` は現在のSQLiteの具体的な実装であり、完全な下位互換性があります。

## インポート

```python
from ErisPulse import sdk
# または
from ErisPulse.Core import storage

# ABC基底クラス（型アノテーションまたはカスタム実装用）
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## テーブル管理

### テーブルの作成

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0",
    "email": "TEXT"
})
```

### テーブルの存在確認

```python
if sdk.storage.HasTable("users"):
    print("users テーブルは既に存在します")
```

### テーブルの削除

```python
sdk.storage.DropTable("users")
```

### テーブル構造の変更

```python
# 列の追加
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()

# テーブル名の変更
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# 複数操作のチェーン
sdk.storage.AlterTable("users") \
    .AddColumn("phone", "TEXT") \
    .AddColumn("address", "TEXT") \
    .Execute()
```

## メソッドチェーンによるクエリ

### データの挿入

```python
# 単一行の挿入（辞書を渡す）
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# バッチ挿入（辞書のリストを渡す）
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
    {"name": "Dave", "age": 40}
]).Execute()
```

### データのクエリ

> **重要**: `Select()` は `list[tuple]`（タプルのリスト）を返し、辞書ではありません。列の順序に従ってインデックスでアクセスする必要があります。

```python
# すべての列をクエリ
rows = sdk.storage.Table("users").Select().Execute()
# rows: [(1, "Alice", 30), (2, "Bob", 25), ...]

# 指定した列をクエリ
rows = sdk.storage.Table("users").Select("name", "age").Execute()
# rows: [("Alice", 30), ("Bob", 25), ...]

# インデックスで値を取得
for row in rows:
    name = row[0]   # "Alice"
    age = row[1]    # 30
```

#### タプルを辞書に変換

```python
columns = ["id", "name", "age"]
rows = sdk.storage.Table("users").Select(*columns).Execute()

# 方法1：ループ内でzipを使用
for row in rows:
    record = dict(zip(columns, row))
    print(record["name"], record["age"])

# 方法2：一括で辞書のリストに変換
records = [dict(zip(columns, row)) for row in rows]
```

#### 単一レコードの取得

```python
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ExecuteOne()

# rowはtupleまたはNone
if row is not None:
    name = row[0]  # "Alice"
    age = row[1]   # 30
```

### 条件フィルタリング

> `Where(condition, *params)` は複数のパラメータの渡しをサポートし、複数の `?` プレースホルダに対応します。

```python
# 単一条件（1つのプレースホルダ、1つのパラメータ）
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 18) \
    .Execute()

# 1つのWhereで複数のプレースホルダを使用
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ? AND age < ?", 20, 40) \
    .Execute()

# Whereの複数呼び出し（ANDで接続）
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 20) \
    .Where("age < ?", 40) \
    .Execute()
```

### ソート、ページネーション

```python
# 昇順
rows = sdk.storage.Table("users").Select("name", "age") \
    .OrderBy("name") \
    .Execute()

# 降順
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("age", desc=True) \
    .Execute()

# ページネーション
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("id") \
    .Limit(10) \
    .Offset(20) \
    .Execute()
```

### データの更新

```python
# 条件付き更新
sdk.storage.Table("users") \
    .Update({"age": 31}) \
    .Where("name = ?", "Alice") \
    .Execute()

# 全件更新
sdk.storage.Table("users") \
    .Update({"status": "active"}) \
    .Execute()
```

### データの削除

```python
# 条件付き削除
sdk.storage.Table("users") \
    .Delete() \
    .Where("name = ?", "Bob") \
    .Execute()

# 全件削除
sdk.storage.Table("users").Delete().Execute()
```

### カウントと存在確認

```python
# カウント
count = sdk.storage.Table("users").Count()
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# 存在確認
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()
```

## クエリ条件の再利用

`copy()` を使用してビルダーをディープコピーし、基本条件を再利用します：

```python
base = sdk.storage.Table("users").Where("age > ?", 20)

# 同じ条件に基づいてクエリ
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()

# 同じ条件に基づいてカウント
count = base.copy().Count()

# 同じ条件に基づいて存在確認
exists = base.copy().Where("name = ?", "Alice").Exists()
```

## ビルダーのリセット

```python
builder = sdk.storage.Table("users").Select("name").Where("age > ?", 18)
builder.clear()

# クエリを再構築
builder.Select("name", "age").Where("name = ?", "Alice")
rows = builder.Execute()
```

## トランザクションでの使用

メソッドチェーン操作はトランザクションを完全にサポートしています：

```python
# トランザクションのコミット
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Eve", "age": 22}).Execute()
    sdk.storage.Table("users").Update({"age": 23}).Where("name = ?", "Eve").Execute()

# ロールバックの例
try:
    with sdk.storage.transaction():
        sdk.storage.Table("users").Delete().Where("name = ?", "Alice").Execute()
        raise Exception("force rollback")
except Exception:
    pass
# Aliceのレコードはまだ存在しています
```

## 戻り値の説明

| 操作 | 戻り値の型 | 説明 |
|------|---------|------|
| `Select().Execute()` | `list[tuple]` | タプルのリスト、列の順序で並び替え |
| `Select().ExecuteOne()` | `tuple \| None` | 単一のタプルまたはNone |
| `Insert().Execute()` | `int` | 影響を受けた行数 |
| `InsertMulti().Execute()` | `int` | 挿入された行数 |
| `Update().Execute()` | `int` | 影響を受けた行数 |
| `Delete().Execute()` | `int` | 影響を受けた行数 |
| `Count()` | `int` | 一致した行数 |
| `Exists()` | `bool` | 存在するかどうか |

### 戻り値の処理例

```python
# Selectはタプルを返し、インデックスで値を取得
rows = sdk.storage.Table("users").Select("name", "age").Execute()
first_name = rows[0][0]  # 最初の行の最初の列 name
first_age = rows[0][1]   # 最初の行の2番目の列 age

# 推奨：列名リスト + zipで辞書に変換すると、コードが読みやすくなります
cols = ["name", "age"]
rows = sdk.storage.Table("users").Select(*cols).Execute()
for row in rows:
    d = dict(zip(cols, row))
    print(d["name"], d["age"])

# ExecuteOneは単一のタプルまたはNoneを返します
row = sdk.storage.Table("users").Select("name").Where("id = ?", 1).ExecuteOne()
name = row[0] if row else None

# Insert/Update/Deleteは影響を受けた行数を返します
affected = sdk.storage.Table("users").Delete().Where("age < ?", 18).Execute()
print(f"{affected} 件のレコードを削除しました")
```

## パラメータ化クエリ

すべてのWHEREパラメータは `?` プレースホルダを使用し、パラメータは `Where()` の後続の引数として渡されます（タプルやリストでは**ありません**）：

```python
# 正しい ✓ — 複数のパラメータを個別に渡す
sdk.storage.Table("users").Where("age > ? AND name = ?", 18, "Alice").Execute()

# 正しい ✓ — Whereの複数呼び出し
sdk.storage.Table("users").Where("age > ?", 18).Where("name = ?", "Alice").Execute()

# 間違い ✗ — タプルを渡さないでください
sdk.storage.Table("users").Where("age > ? AND name = ?", (18, "Alice")).Execute()
# これはタプル全体が最初のプレースホルダの値として扱われます

# 間違い ✗ — SQLインジェクションのリスクがあります
sdk.storage.Table("users").Where(f"name = '{user_input}'").Execute()
```

### Whereのパラメータ渡しルール

```python
# Where(condition: str, *params: Any)
# paramsは可変長引数なので、個別に渡すだけです

# 単一パラメータ
.Where("name = ?", "Alice")

# 複数パラメータ
.Where("age > ? AND age < ?", 18, 60)

# LIKEクエリ
.Where("name LIKE ?", "A%")

# INクエリ（プレースホルダを手動で構築する必要があります）
.Where("name IN (?, ?, ?)", "Alice", "Bob", "Charlie")
```

## カスタムストレージバックエンド

`BaseStorage` と `BaseQueryBuilder` を継承してカスタムストレージバックエンドを実装します：

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

class MyQueryBuilder(BaseQueryBuilder):
    def Execute(self):
        # 具体的な実行ロジックを実装
        ...

    def ExecuteOne(self):
        ...

    def Count(self):
        ...

    def Exists(self):
        ...


class MyStorage(BaseStorage):
    def get(self, key, default=None):
        ...

    def set(self, key, value):
        ...

    # その他の抽象メソッドを実装...
    def Table(self, table_name):
        return MyQueryBuilder(self, table_name)
```



### 路由系统

# ルーティングマネージャー

ErisPulse ルーティングマネージャーは、HTTP および WebSocket のルーティングを統一的に管理し、複数アダプタのルーティング登録とライフサイクル管理をサポートします。内部では抽象層を封印しています（現在は FastAPI + Uvicorn）

## 概要

ルーティングマネージャーの主な機能：

- **デコレータルーティング**：`@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` デコレータによる高速登録
- **自動インジェクション**：ルーティングハンドラは FastAPI クラスをインポートする必要がなく、フレームワークが抽象オブジェクトを自動的に注入します
- **ルーティンググループ**：プレフィックスとバージョン番号付きの `RouteGroup` をサポート
- **ルーティングミドルウェア**：glob モードマッチングによるリクエストのインターセプト
- **レート制限**：スライディングウィンドウ方式のリクエスト制限
- **CORSサポート**：ワンクリックで CORS を有効化
- **セキュリティヘッダー**：自動的にセキュリティレスポンスヘッダーを追加
- **自動ドキュメント**：OpenAPI に基づくインタラクティブなドキュメント
- **WebSocketサポート**：WebSocket接続の完全な管理、カスタム認証、ライフサイクルフック
- **ライフサイクル統合**：ErisPulse ライフサイクルシステムと深く統合
- **SSL/TLSサポート**：HTTPS および WSS セキュア接続をサポート
- **ホームエントリ**：モジュールがルートルート `/` に登録されたクイックエントリボタンをサポート、国際化に対応

## 抽象型

ErisPulse はサーバー側の抽象型を提供し、モジュールが FastAPI に直接依存しないようにします：

| 抽象型 | FastAPI対応 | 説明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTPリクエストのラッパー、インターフェースは完全に互換性があります |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket接続のラッパー、ライフサイクルフックを追加 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket切断例外 |

> `WebSocketConnection` は `WebSocketConnectionBase` を継承しており、クライアント側の WebSocket (`ClientWebSocket`) と同じ send/receive/iter/close インターフェースを共有します。クライアントとサーバー側の WebSocket は同じビジネスロジックコードを使用できます。
>
> `.raw` 属性を介して、下層の FastAPI ネイティブオブジェクトにアクセスできます。直接 FastAPI クラスを使用するコードも完全に互換性があります。

## デコレータルーティング（推奨）

### HTTPデコレータ

```python
from ErisPulse.Core import router
@router.get("my_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}

# 明示的に抽象型を指定することもできます
from ErisPulse.Core import HttpRequest

@router.post("my_module", "/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("my_module", "/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("my_module", "/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **自動インジェクションルール**：ハンドラの最初の引数が `request` または `req` で、FastAPI型の注釈がない場合、フレームワークは自動的に `HttpRequest` を注入します。引数がなく、またはリクエスト引数名でないハンドラは影響を受けません。

### WebSocketデコレータ

```python
from ErisPulse.Core import WebSocketConnection, WebSocketDisconnect

# 基本的なWebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# ライフサイクルフック付きのWebSocket
@router.ws("my_module", "/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"ユーザー切断: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"接続エラー: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 認証付きのWebSocket
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocketハンドラと認証ハンドラも自動インジェクションをサポートします。引数の注釈がなくても `WebSocketConnection` を取得できます。`fastapi.WebSocket` を注釈してもネイティブオブジェクトを渡すことができますが、抽象型の使用を推奨します。

## 伝統的な登録方法

```python
async def hello_handler(request):
    return {"message": "Hello World"}

# 基本的な登録
router.register_http_route(
    module_name="my_module",
    path="/hello",
    handler=hello_handler,
    methods=["GET"],
)

# レート制限とドキュメント情報付き
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="データインターフェース",
    tags=["API"],
)
```

### WebSocket登録

```python
from ErisPulse.Core import WebSocketConnection

async def websocket_handler(ws: WebSocketConnection):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 基本的な登録
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# 認証付きの登録（推奨）
async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

**パラメータ説明：**

| パラメータ | 説明 | デフォルト値 |
|------|------|--------|
| `module_name` | モジュール名（必須） | - |
| `path` | WebSocketパス | - |
| `handler` | ハンドラ関数 | - |
| `auth_handler` | 認証関数、`False`を返すと接続が自動的に切断されます | `None` |
| `auto_accept` | 自動的に `accept()` を行うかどうか | `True` |

> **推奨**：接続確認には `auth_handler` を使用してください。`auto_accept` を `False` に設定するのは、接続フローを完全に制御したい場合に限り、`auth_handler` を使用することを推奨します。

## WebSocketライフサイクルフック

`WebSocketConnection` は切断とエラーのコールバックを登録する機能を提供し、手動の try/catch が不要です：

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # デコレータ方式で登録
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"切断原因: {reason}")

    # 直接呼び出すこともできます
    async def on_err(ws, error=""):
        print(f"エラー: {error}")
    ws.on_error(on_err)

    # 通常のビジネスロジック
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## ルーティンググループ

```python
# プレフィックス付きのルーティンググループを作成
group = router.group("my_module", prefix="/v1")

@group.get("/users")
async def list_users(request):
    return {"users": []}

@group.post("/users")
async def create_user(request):
    return {"created": True}

# 実際のパス: /my_module/v1/users
```

## ルーティングミドルウェア

ミドルウェアは glob モードでパスをマッチングします：

```python
@router.middleware("/my_module/*")
async def auth_middleware(request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    return await call_next(request)

@router.middleware("/my_module/admin/*")
async def admin_middleware(request, call_next):
    return await call_next(request)
```

## リクエスト関連ID（X-Request-ID）

2.7.0以降、各HTTPリクエストには `X-Request-ID` 関連IDが付与され、ログ / リンクトレースの連携に使用されます：

- **生成ルール**：クライアントが送信した `X-Request-ID` リクエストヘッダーを優先して使用（分散トレースの場面）；なければUUIDを自動生成
- **レスポンスヘッダー**：レスポンスに `X-Request-ID` を返し、クライアントがリクエストとログを対応させるのに便利です
- **ライフサイクルイベント**：`server.request` と `server.response` イベントデータに `request_id` フィールドが追加されました

```python
# モジュール内でリクエストイベントを監視し、request_id でリクエスト-レスポンスを連携
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

クライアントは、サービス間トレースのために独自のIDを設定できます：

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## レート制限

スライディングウィンドウアルゴリズムを使用してルートのリクエスト制限を行います：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

レート制限の形式：`{回数}/{時間ウィンドウ}`、例えば `10/minute`、`100/hour`。

## CORS設定

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

`config.toml` で設定することもできます：

```toml
[router.cors]
allow_origins = ["https://example.com"]
allow_methods = ["GET", "POST"]
allow_headers = ["*"]
```

## セキュリティヘッダー

```python
router.setup_security_headers()
```

`X-Content-Type-Options`、`X-Frame-Options`、`X-XSS-Protection` などのセキュリティヘッダーを自動的に追加します。

`config.toml` で設定することもできます：

```toml
[router.security]
enabled = true
```

## 自動ドキュメント

Router はデフォルトで OpenAPI インタラクティブドキュメントを有効にしています：

```python
# ドキュメントを無効化
router.disable_docs()

# ドキュメント情報をカスタマイズ
router.set_docs_info(
    title="My API",
    description="APIドキュメント",
    version="1.0.0"
)
```

## パス処理

ルーティングパスは自動的にモジュール名をプレフィックスとして追加し、衝突を回避します：

```python
# モジュール "my_module" にパス "/api" を登録
# 実際のアクセスパスは "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## システムルート

ルーティングマネージャーは以下のシステムルートを自動的に提供します：

### ヘルスチェック

```
GET /health
# 戻り値:
{"status": "ok", "service": "ErisPulse Router"}
```

### ルートページ

```
GET /
# 戻り値: ErisPulseブランドページ
```

ルートルート `/` は ErisPulse ブランドページを表示し、ダッシュボードの可用性を自動検出し、エントリーボタンを追加します。

## ホームエントリ

ルーティングマネージャーは外部モジュールがルートルート `/` にクイックエントリーボタンを登録できるようにし、ユーザーが各モジュールの管理ページに素早くアクセスできるようにします。

### エントリの登録

```python
# 簡単な登録
router.register_home_entry(
    name="私のパネル",
    url="/mymodule/admin",
)

# イコン付きの登録（SVG）
router.register_home_entry(
    name="コンソール",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# 国際化に対応した登録（i18n辞書形式）
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "私のパネル"},
    url="/mymodule/admin",
)
```

**パラメータ説明：**

| パラメータ | 型 | 説明 | 必須 |
|------|------|------|------|
| `name` | `str` / `dict` | ボタン表示テキスト；`{"i18n": "key", "default": "テキスト"}`辞書を渡すと国際化を使用します | はい |
| `url` | `str` | ボタンリンクアドレス | はい |
| `icon_svg` | `str` | オプションのSVGアイコンマーク | いいえ |

### ダッシュボードの自動登録

`sdk.Dashboard` が利用可能であることが検出された場合、ルーティングマネージャーはダッシュボードボタンを自動的にエントリーリストの先頭に追加し、手動の登録は不要です。

## ライフサイクル統合

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"サーバーが起動しました: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("サーバーが停止中です...")
```

## 最適実践

1. **抽象型を優先する**：`HttpRequest` / `WebSocketConnection` を `fastapi.Request` / `fastapi.WebSocket` に代えて使用し、ハード依存を避ける
2. **自動インジェクションを利用する**：ハンドラの最初の引数を `request` または `req` とし、型注釈なしで `HttpRequest` を取得できる
3. **module_nameを明示的に渡す**：デコレータの最初の引数はモジュール名でなければならず、省略できない
4. **ルーティンググループを使用する**：同一モジュールの複数のルーティングは `group()` で整理する
5. **セキュリティを考慮する**：機密操作には認証メカニズムとセキュリティヘッダーを実装する
6. **適切なレート制限を設定する**：高頻度インターフェースにはレート制限を設定する
7. **ライフサイクルフックを使用する**：`@ws.on_disconnect` / `@ws.on_error` を使って WebSocket の例外を処理し、手動の try/catch を避ける



### 生命周期管理

# ライフサイクル管理

ErisPulse は、システムの各コンポーネントの実行状態を監視し、監査、統計、カスタムロジックなどの拡張機能を実現するために、統一されたフック/ライフサイクルシステムを提供します。

システムは3つのトリガー方法をサポートしています。
- `await lifecycle.emit("event", data)` — 簡易版、任意のデータを渡す
- `lifecycle.emit_sync("event", data)` — 同期版（非同期コンテキストで使用）
- `await lifecycle.submit_event("event", ...)` — 旧版との互換性、標準イベント形式を自動構築

## イベント処理メカニズム

### ハンドラの登録

```python
from ErisPulse import sdk

# デコレータモード
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"モジュールの読み込み: {data}")

# プログラムによる登録
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# 登録解除
sdk.lifecycle.unregister("module.load", on_module_load)

# 所有者ごとの一括登録解除（モジュール/アダプタのアンインストール時にフレームワークが自動的に呼び出す）
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"ライフサイクルフックを {removed} 個クリアしました")
```

### 優先度

ハンドラは `priority` パラメータをサポートし、数値が大きいほど先に実行されます（モジュールローダーと一致）：

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # 最優先で実行
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # あとで実行
async def second_handler(data):
    pass
```

### ドット表記構造のイベント

具体的なイベントをトリガーすると、その親イベントもトリガーされます。
- `module.load` をトリガーすると、`module` もトリガーされます
- `adapter.event.receive` をトリガーすると、`adapter.event` と `adapter` もトリガーされます

### ワイルドカード

`*` を登録するとすべてのイベントをキャッチします：

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"イベントを受信しました: {data}")
```

### 一回限りの登録（once）

2.7.0 以降、`lifecycle.once()` で登録されたハンドラは**一度トリガーされたら自動的に登録解除**されます。「初回準備完了」のような一回限りのフックに適しています：

```python
@sdk.lifecycle.once("core.init.complete")
async def on_first_ready(data):
    print("初回準備完了、その後はトリガーされません")
```

- `on()` と同じ優先度パラメータの意味（数値が大きいほど先に実行）
- 自動的に登録解除されるため、手動で `unregister` する必要がない
- 同期/非同期ハンドラの両方をサポート

### リスナーの確認（has_handlers）

熱路径（パフォーマンスが重要なパス）でのショートサーキットのため、無駄なイベントの遍歴やタスクのスケジューリングを避けるために `has_handlers()` ですでにリスナーが存在するかを先に判断できます：

```python
if sdk.lifecycle.has_handlers("message.sending"):
    await sdk.lifecycle.emit("message.sending", send_ctx)
```

- 精確なイベント名、ワイルドカード `*`、親イベントの3種類のマッチングをカバー
- リスナーが一切ない場合は `False` を返し、安全に `emit` をスキップできる

## フックブレークポイント一覧

フレームワークには以下のフックブレークポイントが組み込まれており、ユーザーは `@sdk.lifecycle.on()` を使用して任意のブレークポイントを監視し、カスタムロジックを実装できます。

### コア初期化

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `core.init.start` | SDK の初期化開始 | `{}` |
| `core.init.complete` | SDK の初期化完了 | `{"duration": float, "success": bool, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(失敗時のみ)}` |
| `core.uninit.complete` | SDK の逆初期化完了 | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(失敗時のみ)}` |

### 設定変更

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `config.set` | 設定項目が変更された | `{"key": str, "old_value": Any, "new_value": Any}` |

**例：設定監査**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[監査] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### モジュールライフサイクル

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `module.register` | モジュールクラスがマネージャーに登録された | `{"module_name": str, "success": bool}` |
| `module.load` | モジュールの読み込み完了（インスタンス化成功） | `{"module_name": str, "success": bool}` |
| `module.init` | モジュールの初期化完了（遅延読み込みを含む） | `{"module_name": str, "success": bool}` |
| `module.unload` | モジュールのアンロード | `{"module_name": str, "success": bool}` |

### アダプタライフサイクル

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `adapter.load` | アダプタの登録完了 | `{"platform": str, "success": bool}` |
| `adapter.start` | アダプタの開始 | `{"platforms": [str]}` |
| `adapter.status.change` | アダプタの状態変更 | `{"platform": str, "status": str, "retry_count": int, "error": str(失敗時のみ)}` |
| `adapter.stop` | アダプタの停止 | `{"platforms": [str]}` |
| `adapter.stopped` | アダプタの停止完了 | `{"platforms": [str]}` |
| `adapter.bot.online` | Bot オンライン | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Bot オフライン | `{"platform": str, "bot_id": str, "status": str}` |

### イベント受信と処理

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `adapter.event.receive` | 外部プラットフォームからのイベント受信（最早期） | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.dispatched` | イベント配信完了 | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
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

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `message.sending` | メッセージの送信直前 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | メッセージの送信完了 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**例：メッセージ送信監査**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[送信] -> {data['platform']}/{data['detail_type']}/{data['target_id']} via {data['method']}")
```

### コマンドシステム

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `command.matched` | コマンドがマッチし、実行直前 | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | コマンドの実行完了 | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(失敗時のみ)}` |

**例：コマンド統計**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[コマンド] /{data['command']} from {data['user_id']}@{data['platform']}")
```

### HTTP ルーティング

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `server.request` | HTTP リクエスト受信 | `{"method": str, "path": str, "client_ip": str}` |
| `server.response` | HTTP レスポンス送信 | `{"method": str, "path": str, "status_code": int, "client_ip": str}` |

**例：リクエストログ**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| フック名 | トリガー時機 | データ |
|---------|---------|------|
| `server.start` | ルーター サーバーの開始 | `{"base_url": str, "host": str, "port": int}` |
| `server.stop` | ルーター サーバーの停止 | `{}` |
| `server.websocket.connect` | WebSocket 接続確立 | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket 接続切断 | `{"path": str, "module_name": str, "reason": str, "error": str(例外時のみ)}` |

**例：WebSocket 接続監視**

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

## 完全な API リファレンス

### 登録とキャンセル

| メソッド | 説明 |
|------|------|
| `@lifecycle.on(event, *, priority=0)` | デコレータでハンドラを登録 |
| `lifecycle.register(event, handler, *, priority=0)` | プログラムによる登録 |
| `lifecycle.unregister(event, handler=None)` | 登録解除（handler=None の場合、そのイベントのすべてのハンドラをキャンセル） |

### トリガー

| メソッド | 説明 |
|------|------|
| `await lifecycle.emit(event, data=None)` | 非同期トリガー、ハンドラが非 None を返すと data を変更 |
| `lifecycle.emit_sync(event, data=None)` | 同期トリガー、非同期ハンドラは create_task でスケジュール |
| `await lifecycle.submit_event(event_type, *, source, msg, data)` | 旧版との互換性、標準イベント形式を自動構築 |

### ユーティリティ

| メソッド | 説明 |
|------|------|
| `lifecycle.start_timer(timer_id)` | タイマー開始 |
| `lifecycle.get_duration(timer_id)` | 経過時間の取得（秒） |
| `lifecycle.stop_timer(timer_id)` | タイマー停止と経過時間の返却 |
| `lifecycle.list_hooks()` | 登録されたすべてのフックとハンドラ数のリスト |
| `lifecycle.clear()` | すべてのハンドラとタイマーをクリア |

## モジュールでの使用例

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # 簡易メッセージ統計を実装
        self.msg_count = 0
        
        @sdk.lifecycle.on("adapter.event.receive")
        async def count(data):
            if data["event_type"] == "message":
                self.msg_count += 1
        
        # すべてのコマンドを監視
        @sdk.lifecycle.on("command.matched")
        async def log_cmd(data):
            sdk.logger.info(f"コマンド実行: /{data['command']} by {data['user_id']}")
        
        # 設定変更監査
        @sdk.lifecycle.on("config.set")
        def audit(data):
            sdk.logger.info(f"設定変更: {data['key']} = {data['new_value']}")
```

## 注意事項

1. **ハンドラは同期または非同期にできる**：システムは自動的に識別し、正しく呼び出します
2. **データの受け渡し**：`emit()` モードでは、ハンドラが非 None 値を返すと、その値が後続のハンドラに渡される data に適用されます
3. **イベント命名規則**：親イベントの監視を容易にするために、ドット表記構造でイベント名を付けることを推奨します
4. **エラー隔離**：単一のハンドラの例外は、他のハンドラの実行に影響しません
5. **同期トリガーの制限**：`emit_sync()` では非同期ハンドラは fire-and-forget 方式でスケジュールされ、返却値は伝播されません
6. **ライフサイクルのクリア**：`sdk.uninit()` を呼び出すと、すべての登録済みハンドラとタイマーがクリアされます
7. **読み込みの優先性**：フレームワークの初期化段階でイベントを監視する必要がある場合は、高い優先度を設定し遅延読み込みを無効にすることを推奨します



### 懶加载系统

# ラグロードモジュールシステム

ErisPulse SDK は、モジュールを実際に必要になるまで初期化しない強力なラグロードモジュールシステムを提供し、アプリケーションの起動速度とメモリ効率を大幅に向上させます。

## 概要

ラグロードモジュールシステムは、ErisPulse のコア機能の一つであり、以下の方法で動作します：

- **遅延初期化**：モジュールは、初めてアクセスされたときにのみ実際にロードおよび初期化されます
- **透明な使用**：開発者にとって、ラグロードモジュールは通常のモジュールと使用方法にほとんど違いがありません
- **自動依存管理**：モジュールの依存関係は、使用時に自動的に初期化されます
- **ライフサイクルサポート**：`BaseModule` を継承したモジュールに対しては、ライフサイクルメソッドが自動的に呼び出されます

## 動作原理

### LazyModule クラス

ラグロードシステムの中心は、`LazyModule` クラスです。これは、最初のアクセス時にのみ実際にモジュールを初期化するラッパーです。

### 初期化プロセス

モジュールが初めてアクセスされたとき、`LazyModule` は以下の操作を実行します：

1. モジュールクラスの `__init__` の引数情報を取得します
2. 引数に基づいて `sdk` 参照を渡すかどうかを決定します
3. モジュールの `moduleInfo` 属性を設定します
4. `BaseModule` を継承したモジュールに対しては `on_load` メソッドを呼び出します
5. `module.init` ライフサイクルイベントを発生させます

## ラグロードの設定

### グローバル設定

設定ファイルでグローバルなラグロードを有効/無効にします：

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true=ラグロードを有効にする(デフォルト), false=ラグロードを無効にする
```

### モジュールレベルの制御

モジュールは、`get_load_strategy()` 静的メソッドを実装することで、ロード戦略を制御できます：

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """モジュールロード戦略を返す"""
        return ModuleLoadStrategy(
            lazy_load=False,  # False を返すと即時ロード
            priority=100      # ロード優先度、数値が大きいほど優先度が高い
        )
```

## ラグロードモジュールの使用

### 基本的な使用

開発者にとって、ラグロードモジュールは通常のモジュールと使用方法にほとんど違いがありません：

```python
# SDK を通じてラグロードモジュールにアクセス
from ErisPulse import sdk

# 以下のようなアクセスはモジュールのラグロードをトリガーします
result = await sdk.my_module.my_method()
```

### 一貫したモジュール取得エントリ

SDK 属性、モジュールマネージャー属性を通じてアクセスする場合、または `module.get()` を使って検索する場合、
「登録済みだがまだロードされていない」ラグロードモジュールに対しては、同じラグロードプロキシが返され、
そのプロパティにアクセスすることで初めて初期化がトリガーされます：

```python
# 3 つの方法で取得されるのはすべてラグロードプロキシ（モジュールがロードされていない場合）、動作は一貫しており、ユーザーには透明です
sdk.my_module          # ロードをトリガーするエントリ
sdk.module.my_module   # 同様にラグロードプロキシを返します
sdk.module.get("my_module")  # ラグロードプロキシを返しますが、自体はロードをトリガーしません

# プロキシの任意のプロパティにアクセスすることで、モジュールが実際に初期化されます
result = await sdk.my_module.my_method()
```

`module.get()` は**検索**インターフェースであり、自体はロードをトリガーしません：
- モジュールがロード済み → 実際のインスタンスを返します
- モジュールが登録済みだがロードされていない → ラグロードプロキシを返します（プロパティにアクセスすることで初期化されます）
- モジュールが登録されていない → `None` を返します

明示的にロードをトリガーするには、`await sdk.load_module("my_module")` を使用してください。

### 非同期初期化

非同期初期化が必要なモジュールについては、まず明示的にロードすることを推奨します：

```python
# まずモジュールを明示的にロードします
await sdk.load_module("my_module")

# その後、モジュールを使用します
result = await sdk.my_module.my_method()
```

### 同期初期化

非同期初期化が必要ないモジュールについては、直接アクセスできます：

```python
# 直接アクセスすることで自動的に同期初期化されます
result = sdk.my_module.some_sync_method()
```

## 最適な実践

### ラグロードを使用することを推奨する場面（lazy_load=True）

- 他のモジュールが呼び出すときにのみ必要な受動的なユーティリティクラス（データクエリモジュール、フォーマット変換器など）

### ラグロードを無効にすることを推奨する場面（lazy_load=False）

- トリガーを登録するモジュール（コマンドプロセッサ、メッセージプロセッサなど）
- ライフサイクルイベントリスナー
- タイミングタスクモジュール
- アプリケーション起動時に初期化が必要なモジュール

> `priority` パラメータは、即時ロードモジュール間の初期化順序を制御します。数値が大きいほど先に初期化されます。同優先度のモジュールは、登録順にロードされます。

## 注意事項

1. あなたのモジュールがラグロードを使用している場合、他のモジュールがErisPulse内で一度も呼び出さない限り、あなたのモジュールは決して初期化されません。
2. あなたのモジュールにイベントを監視するモジュールや、そのようなモジュールを積極的に監視するモジュールが含まれている場合、必ず即時ロードが必要であることを宣言してください。そうしないと、モジュールの正常な業務に影響を与えます。
3. 特殊な要件がない限り、ラグロードを無効にすることは推奨しません。そうしないと、依存管理やライフサイクルイベントなどの問題が発生する可能性があります。



### 会话类型系统

# セッションタイプシステム

ErisPulse セッションタイプシステムは、メッセージのセッションタイプ（プライベートチャット、グループチャット、チャンネルなど）の定義と管理を担当し、受信タイプと送信タイプ間の自動変換を提供します。

## タイプ定義

### 受信タイプ (ReceiveType)

受信タイプはOneBot12イベントの `detail_type` フィールドから取得され、イベントのセッションシナリオを表します：

| タイプ | 説明 | ID フィールド |
|------|------|---------|
| `private` | プライベートメッセージ | `user_id` |
| `group` | グループメッセージ | `group_id` |
| `channel` | チャンネルメッセージ | `channel_id` |
| `guild` | サーバーメッセージ | `guild_id` |
| `thread` | スレッド/サブチャンネルメッセージ | `thread_id` |
| `user` | ユーザーメッセージ（拡張） | `user_id` |

### 送信タイプ (SendType)

送信タイプは、`Send.To(type, id)` で送信先を指定するために使用されます：

| タイプ | 説明 |
|------|------|
| `user` | ユーザーに送信 |
| `group` | グループに送信 |
| `channel` | チャンネルに送信 |
| `guild` | サーバーに送信 |
| `thread` | スレッドに送信 |

## タイプマッピング

受信タイプと送信タイプの間にはデフォルトのマッピング関係があります：

```
受信 (Receive)          送信
─────────────          ──────────
private        ──→     user
group          ──→     group
channel        ──→     channel
guild          ──→     guild
thread         ──→     thread
user           ──→     user
```

重要な違い：**受信時には `private` を使用し、送信時には `user` を使用します**。これは OneBot12 標準の設計であり、イベントは「プライベートチャットのシナリオ」を記述し、送信は「ユーザーのターゲット」を記述するためです。

## 自動推論

イベントに明示的な `detail_type` フィールドがない場合、システムはイベント内に存在する ID フィールドに基づいてセッションタイプを自動的に推論します：

**優先度**：`group_id` > `channel_id` > `guild_id` > `thread_id` > `user_id`

```python
from ErisPulse.Core.Event.session_type import infer_receive_type

# group_id がある → group に推論
event1 = {"group_id": "123", "user_id": "456"}
print(infer_receive_type(event1))  # "group"

# user_id のみ → private に推論
event2 = {"user_id": "456"}
print(infer_receive_type(event2))  # "private"
```

## コア API

### タイプ変換

```python
from ErisPulse.Core.Event.session_type import (
    convert_to_send_type,
    convert_to_receive_type,
)

# 受信タイプ → 送信タイプ
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# 送信タイプ → 受信タイプ
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### ID フィールドのクエリ

```python
from ErisPulse.Core.Event.session_type import get_id_field, get_receive_type

# タイプに基づいて ID フィールド名を取得
get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

# ID フィールドに基づいてタイプを取得
get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### ワンステップで送信情報を取得

```python
from ErisPulse.Core.Event.session_type import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# Send.To() に直接使用
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### ターゲット ID の取得

```python
from ErisPulse.Core.Event.session_type import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## カスタムタイプの登録

アダプターは、プラットフォーム固有のセッションタイプのカスタムマッピングを登録できます：

```python
from ErisPulse.Core.Event.session_type import register_custom_type, unregister_custom_type

# カスタムタイプの登録
register_custom_type(
    receive_type="thread_reply",     # 受信タイプ名
    send_type="thread",              # 対応する送信タイプ
    id_field="thread_reply_id",      # 対応する ID フィールド
    platform="discord"               # プラットフォーム名（オプション）
)

# カスタムタイプの使用
convert_to_send_type("thread_reply", platform="discord")  # → "thread"
get_id_field("thread_reply", platform="discord")          # → "thread_reply_id"

# カスタムタイプの登録解除
unregister_custom_type("thread_reply", platform="discord")
```

> **platform を指定した場合**、登録された受信タイプにはプラットフォームのプレフィックス（例：`discord_thread_reply`）が付加され、異なるプラットフォーム間でのタイプの競合を回避します。

## ユーティリティメソッド

```python
from ErisPulse.Core.Event.session_type import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

# 標準タイプかどうかを確認
is_standard_type("private")  # True
is_standard_type("custom_type")  # False

# 送信タイプが有効かどうかを確認
is_valid_send_type("user")  # True
is_valid_send_type("invalid")  # False

# すべての標準タイプを取得
get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

# カスタムタイプをクリア
clear_custom_types()                # すべてクリア
clear_custom_types(platform="discord")  # 指定したプラットフォームのもののみクリア
```



### 国际化（i18n）系统

# 国際化 (i18n) システム

ErisPulse v2.5.0 より、完全な国際化サポートが組み込まれています。フレームワークのコアおよび CLI インターフェースは、システム言語に応じて自動的に表示テキストを切り替えられます。また、外部モジュールが独自の翻訳を登録することもサポートしています。

请直接返回翻译后的完整Markdown内容，不要包含任何其他文字。

再次提醒：如果文档包含语言切换行（各语言名称用 `` | `` 分隔的行），务必严格遵守上方第8条的格式要求，不要写出 ``[**Label**](file)`` 这类错误格式。
*这段中文提示我也翻译成日语，因为我需要这个翻译工作按照上述指令完整执行。*

# 国際化 (i18n) システム

ErisPulse v2.5.0 より、完全な国際化サポートが組み込まれています。フレームワークのコアおよび CLI インターフェースは、システム言語に応じて自動的に表示テキストを切り替えられます。また、外部モジュールが独自の翻訳を登録することもサポートしています。

*ここで注意：ドキュメントに言語切り替え行（各言語名が `` | `` で区切られた行）が含まれている場合、上記の第8条の形式要件を厳格に守るようにしてください。``[**Label**](file)`` のような誤った形式は書かないでください。*

## サポートされている言語

| 言語 | コード | 説明 |
|------|------|------|
| 簡体字中国語 | `zh-CN` | デフォルト言語（フレームワークのネイティブ言語） |
| 繁体字中国語 | `zh-TW` | 繁体字中国語（香港/マカオ/台湾） |
| English | `en` | 英語（汎用フォールバック言語） |
| 日本語 | `ja` | 日本語 |
| Русский | `ru` | ロシア語 |

## クイック体験

### 環境変数による切り替え

```bash
# Windows PowerShell
$env:ERISPULSE_LANG = "en"
epsdk run

# macOS / Linux
ERISPULSE_LANG=ja epsdk run
```

### 設定ファイルによる切り替え

`config/config.toml` に以下を追加します：

```toml
[ErisPulse.i18n]
language = "ja"
```

`"auto"`（デフォルト値）に設定すると、システム言語を自動的に検出します。

### コード内での手動切り替え

```python
from ErisPulse import i18n

# 言語を手動で設定
i18n.set_language("en")
print(i18n.get_language())  # "en"

# 自動検出にリセット
i18n.reset_language()
```

---

## 言語検出メカニズム

フレームワークは、ユーザーの言語を以下の優先順位で検出します。

1. **環境変数 `ERISPULSE_LANG`** — 最優先度、テストおよび一時的な切り替えに使用
2. **Windows API** — `GetUserDefaultLocaleName`（Windows のみ。Git Bash などのツールが `LANG` に影響を与えない）
3. **環境変数** — `LANGUAGE` > `LC_ALL` > `LC_MESSAGES` > `LANG`（Unix/macOS 標準）
4. **システム Locale** — `locale.getlocale()` / `locale.getdefaultlocale()`
5. **フォールバック（最終手段）** — en（英語）

### 近似マッピングの原則

検出された言語が完全に一致しない場合、近似マッピングの原則に従ってサポートされている言語にマッピングされます。

- `zh-TW`, `zh-HK`, `zh-MO`, `zh-Hant` → **繁体字中国語**
- その他すべての `zh-*`（例: `zh-CN`, `zh-SG`）→ **簡体字中国語**
- `en-US`, `en-GB`, `en-AU` など → **英語**
- `ja-JP` → **日本語**
- `ru-RU` → **ロシア語**
- その他認識されない言語 → **簡体字中国語（フォールバック）**

---

## モジュールで i18n を使用する

独自のモジュールの翻訳テキストを登録することで、そのモジュールでも多言語に対応させることができます。

### 推奨される記法: I18nClass を用いて翻訳キーを宣言する（v2.7.0+）

v2.7.0 以降、モジュールやアダプターは `ConfigClass` を宣言するのと同様に、ネストされたクラス `I18nClass` を用いて翻訳キーを宣言できます。フレームワークは読み込み時に宣言されたすべての翻訳キーを**自動的に登録**するため、手動で `i18n.register()` を呼び出す必要はありません。

```python
from dataclasses import dataclass, field

from ErisPulse.Core.Bases import BaseConfig, BaseI18n, BaseModule, I18nKey


class MyModule(BaseModule):
    # 設定クラス（任意）
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="欢迎",
            metadata={
                # ここでは i18n キー mymodule.welcome_msg を参照しています
                "description": {"i18n": "mymodule.welcome_msg", "default": "ウェルカムメッセージ"},
            },
        )

    # 翻訳キーセットクラス（任意）
    # 宣言されたキーはフレームワークによって自動的に登録されます。ConfigClass によるデフォルト設定生成より優先度が高くなります。
    class I18nClass(BaseI18n):
        # プロパティ名が自動的に完全なキーパスに結合されます：<モジュール名>.<プロパティ名>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # 言語に依存しないフォールバック値。どの言語にも登録されません。
            zh_CN="欢迎消息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
            zh_TW="歡迎訊息",
        )
        # その他のビジネスで使用する翻訳キー
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )

        # 完全なキーパスを明示的に指定することもできます（プロパティ名の結合は使用しません）
        custom: I18nKey = I18nKey(
            key="mymodule.deep.nested.key",
            default="Default text",
            zh_CN="默认文本",
            zh_TW="預設文本",
            en="Default text",
            ja="デフォルトテキスト",
            ru="Текст по умолчанию",
        )
```

#### なぜ I18nClass が推奨されますか？

| 場面 | 手動 i18n.register() | I18nClass 宣言型 |
|------|-----------------------|------------------|
| 設定説明で参照される i18n キー | 手動で登録する必要があり、設定生成前に完了させる必要がある | フレームワークが設定生成前に自動的に登録する |
| 多言語翻訳の宣言 | 各 on_load() 内に散在する | クラス内に集中しており一目で分かる |
| キー名の命名一貫性 | スペルミスを起こしやすい | プロパティ名がキー名のサフィックスとなるため、IDE の補完機能が利用できる |
| アンインストール時のクリーンアップ | 手動で unregister_domain() が必要 | フレームワークが一貫したドメインで登録する |

#### I18nClass のキーパスルール

- **デフォルト**: 完全なキーパスとして `<モジュール登録名>.<プロパティ名>` を使用します
  - 例: モジュール名が `MyModule`、プロパティ `welcome` の場合 → キーパス `MyModule.welcome`
- **明示的**: `I18nKey(key="...")` 引数を用いて任意のドット区切りパスを指定できます
  - 深くネストされたキー名（例: `mymodule.config.basic.token`）に適しています

#### アダプターでの使用

アダプターも `I18nClass` をサポートしており、使用方法は全く同じです：

```python
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey


class MyAdapter(BaseAdapter):
    @dataclass
    class ConfigClass(BaseConfig):
        endpoint: str = field(
            default="",
            metadata={
                # 設定説明でアダプターのキーを参照しています: adapter.MyAdapter.endpoint
                "description": {"i18n": "MyAdapter.endpoint", "default": "API アドレス"},
            },
        )

    class I18nClass(BaseI18n):
        # 設定説明で参照するキーや、その他のビジネスキーの多言語翻訳をクラス内で一元宣言します
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
```

アダプターの `I18nClass` は `__init__` 階段（つまり設定テンプレート生成前に）自動的に登録されるため、設定説明で参照される i18n キーが使用可能であることが保証されます。

### 手動登録による独自翻訳の定義（旧い記法）

`I18nClass` を使用しない場合でも、`i18n.register()` を直接呼び出して翻訳テキストを登録することができます。

```python
from ErisPulse import i18n

# 中国語翻訳を登録
i18n.register("zh-CN", {
    "my_module.welcome": "欢迎使用我的模块！",
    "my_module.goodbye": "再见！",
    "my_module.hello": "你好，{name}！",
}, domain="my_module")

# 英語翻訳を登録
i18n.register("en", {
    "my_module.welcome": "Welcome to my module!",
    "my_module.goodbye": "Goodbye!",
    "my_module.hello": "Hello, {name}!",
}, domain="my_module")
```

### 翻訳の使用方法

```python
from ErisPulse import i18n

# シンプルな翻訳
i18n.t("my_module.welcome")  # 現在の言語が自動的に使用されます

# 書式付きパラメータ付き
i18n.t("my_module.hello", name="Alice")

# デフォルト値の指定（翻訳キーが存在しない場合に返す値）
i18n.t("my_module.unknown_key", default="デフォルトテキスト")
```

### モジュールクラスでの使用

```python
from dataclasses import dataclass, field
from ErisPulse import i18n
from ErisPulse.Core.Bases import BaseConfig, BaseModule

@dataclass
class MyModuleConfig(BaseConfig):
    welcome_msg: str = field(
        default="欢迎",
        metadata={
            "description": {"i18n": "my_module.welcome_msg", "default": "ウェルカムメッセージ"},
            "ui": {"widget": "text", "group": "basic", "order": 1},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def on_load(self, event):
        # リアルタイムで設定を読み込み（アクセスするたびに最新値が反映されます）
        self.logger.info(self.cfg.welcome_msg)
        self.logger.info(i18n.t("my_module.welcome"))

    @command("hello")
    async def hello_handler(self, event):
        name = event.get_user_nickname() or "friend"
        await event.reply(i18n.t("my_module.hello", name=name))

    async def on_unload(self, event):
        pass
```

### 翻訳のアンインストール

```python
# ドメイン全体の翻訳をアンインストール
i18n.unregister_domain("my_module")

## 構成フィールドの多言語

v2.5.2 より、構成 Schema は i18n を全面的にサポートしています。すべてのユーザーに表示されるテキストフィールドは i18n キーを参照でき、WebUI およびその他のコンシューマは現在の言語に基づいて対応するテキストに自動的に解決されます。

### サポートされている i18n フィールド

| フィールド | 場所 | 説明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | select コントロールのオプションラベル |
| `placeholder` | `ui.placeholder` | 入力欄のプレースホルダー |
| `group_labels` | `_schema_meta` | グループ表示名（Dashboard パーティションタイトル） |

統一的に `{"i18n": "key", "default": "テキスト"}` 形式を使用し、純粋な文字列の場合はそのまま透過します（後方互換性のため）。

### i18n フィールドの宣言

すべてのユーザー表示テキストフィールドは i18n をサポートしています：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    # description i18n
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "プラットフォーム Token"},
            "required": True,
            "secret": True,
            "ui": {
                "widget": "password",
                "group": "basic",
                "order": 1,
                # placeholder i18n
                "placeholder": {"i18n": "my_adapter.token.ph", "default": "Token を入力してください"},
            },
        },
    )
    # options label i18n
    mode: str = field(
        default="a",
        metadata={
            "description": {"i18n": "my_adapter.mode", "default": "実行モード"},
            "ui": {
                "widget": "select",
                "group": "basic",
                "order": 2,
                "options": [
                    {"label": {"i18n": "my_adapter.mode.a", "default": "モードA"}, "value": "a"},
                    {"label": {"i18n": "my_adapter.mode.b", "default": "モードB"}, "value": "b"},
                ],
            },
        },
    )

    # group_labels i18n（グループ表示名）
    _schema_meta = {
        "group_labels": {
            "basic": {"i18n": "my_adapter.group.basic", "default": "基本設定"},
        }
    }
```

`default` はフォールバックテキストです。翻訳が登録されていない場合や検索に失敗した場合に表示されます。

### secret のマスキングと構成の検証

`"secret": True` とマークされたフィールドは、**マスキング保護**を自動的に取得します（2.7.0 より）：

- **テンプレート生成時のマスキング**：`dataclass_to_toml_with_comments()` で構成テンプレートを生成する際、secret フィールドの実際の値はファイルに書き込まれません（空のプレースホルダーとして表示され、機密情報のディスクへの書き込みを防ぎます）
- **汎用的なマスキングツール**：`redact_secret(value)` は非空値を `***` に置換し、空値はそのまま返します。ログ出力などのシナリオで使用できます。

```python
from ErisPulse.Core.Bases.config_schema import redact_secret

redact_secret("sk-xxxxxx")  # '***'
redact_secret("")           # ''
```

**構成の検証**（`validate_config()`）は、`required` の非空チェックに加え、2.7.0 より以下をサポートしています：

| 校驗項目 | メタデータ | 例 |
|--------|--------|------|
| 型の一致 | フィールド宣言型 | `int` フィールドに文字列が渡されるとエラー |
| 列挙制約 | `ui.options` またはトップレベルの `options` | 値は許可されたオプションに属している必要があります |
| 数値範囲 | トップレベルの `min` / `max` | `metadata={"min": 1, "max": 65535}` |

```python
from ErisPulse.Core.Bases.config_schema import validate_config

@dataclass
class C(BaseConfig):
    mode: str = field(default="a", metadata={"ui": {"widget": "select", "options": ["a", "b"]}})
    port: int = field(default=80, metadata={"min": 1, "max": 65535})

errors = validate_config(C(mode="x", port=70000))  # 2つのエラー：列挙 + 範囲
```

### 構成翻訳の登録

構成フィールドの i18n キーは通常の翻訳キーと同様に、`i18n.register()` を使用して登録します：

```python
from ErisPulse import i18n

# 中国語を登録（default と一致しても良いし、異なっても良い）
i18n.register("zh-CN", {
    "my_adapter.token": "プラットフォーム Token",
}, domain="my_adapter")

# 英語を登録
i18n.register("en", {
    "my_adapter.token": "Platform Token",
}, domain="my_adapter")
```
> **推奨される書き方**：`I18nClass` を使用して翻訳キーを宣言すると、フレームワークが自動的に登録します（詳細は上記の「推奨される書き方」セクションを参照）。
> 手動で `i18n.register()` または `register_config_i18n()` を呼び出す必要はありません。

`register_config_i18n()` という便利な関数も提供されており、設定クラスからキーを自動的に抽出して登録できます：

```python
from ErisPulse.Core.Bases.config_schema import register_config_i18n

# 設定クラスから description.default を自動的に抽出して zh-CN 翻訳として登録
register_config_i18n(MyAdapterConfig, "zh-CN")

# 手動で英語の翻訳を提供
register_config_i18n(MyAdapterConfig, "en", {
    "my_adapter.token": "Platform Token",
})
```

### WebUI での利用

`get_config_schema()` が返すスキーマでは、i18n 辞書がそのまま透過されます。WebUI のフロントエンドは現在の言語に基づいて `i18n.t()` を呼び出して解決できます。

サーバーサイドで直接文字列に解決する必要がある場合（例：i18n をサポートしていないフロントエンドに返す場合など）、`resolve_config_schema()` を使用します。これは `description`、`options[].label`、`placeholder`、`group_labels` をすべて現在の言語のテキストに解決します。

```python
from ErisPulse.Core.Bases.config_schema import resolve_config_schema

# すべての i18n フィールドが現在の言語の文字列に解決されています
schema = resolve_config_schema(MyAdapterConfig)
print(schema["fields"]["token"]["description"])    # "プラットフォーム Token" または "Platform Token"
print(schema["fields"]["token"]["placeholder"])   # "Token を入力してください" または "Enter Token"
print(schema["fields"]["mode"]["options"][0]["label"])  # "モードA" または "Mode A"
print(schema["group_labels"]["basic"])             # "基本設定" または "Basic"
```

> `BaseConfig`、`BotAccountConfig`、`register_config_i18n()`、`resolve_config_schema()`
> などの型とユーティリティ関数の実際の定義は `ErisPulse.Core.Bases.config_schema` にあります。
> `ErisPulse.runtime.config_schema` は互換性のための shim として維持されていますが、
> **`ErisPulse.Core.Bases` から統一してインポートすることを推奨します**（i18n 翻訳キー関連の型は除き、それらは `ErisPulse.Core.Bases.i18n_schema` にあります）。

## API リファレンス

### I18nManager

#### コアメソッド

| メソッド | 説明 |
|------|------|
| `t(key, default=None, **kwargs)` | 翻訳テキストを取得（`gettext()` の別名） |
| `set_language(lang)` | 手動で言語を設定 |
| `get_language()` | 現在の言語を取得 |
| `reset_language()` | 自動検出にリセット（環境再検出も実行） |
| `get_supported_languages()` | サポートされている全言語のリストを取得 |
| `has_translation(key, lang=None)` | 翻訳キーが存在するかチェック |
| `register(lang, translations, domain)` | カスタム翻訳を登録 |
| `unregister_domain(domain)` | 指定されたドメインの全翻訳をアンインストール |
| `reload()` | 内蔵翻訳を再読み込みして言語を再検出 |

#### `t()` メソッド詳細

```python
def t(self, key, /, default=None, **kwargs):
```

- `key` — 翻訳キー（位置引数のみ、`**kwargs` の `key=` と競合しない）
- `default` — 翻訳が存在しない場合に返すデフォルト値、デフォルトは `None`（キー名自体を返す）
- `**kwargs` — フォーマットパラメータ。翻訳値内の `{placeholder}` を埋めるために使用

例：

```python
# 翻訳定義: "greeting": "こんにちは、{name}！{place}へようこそ。"
i18n.t("greeting", name="Alice", place="ErisPulse")
# 返回: "こんにちは、Alice！ErisPulseへようこそ。"
```

### BaseI18n / I18nKey（宣言的翻訳キー）

v2.7.0 より、`ErisPulse.Core.Bases` はクラス属性ベースの翻訳キー宣言ツール（`ErisPulse.Core.Bases` から一括インポートすることを推奨）を提供しています：

> ``I18nKey.default`` は**言語に依存しないフォールバックテキスト**であり、どの言語にも登録されません。
> 翻訳を有効にするには、少なくとも1つの言語パラメータ（``zh_CN=`` / ``en=`` / ``ja=`` など）を明示的に渡す必要があります。
> こうすることで、各国の開発者は自身の母語で自由に ``default`` を入力でき、フレームワークは何も前提としません。

| 名称 | 説明 |
|------|------|
| `I18nKey(default, *, key=None, zh_CN, zh_TW, en, ja, ru)` | 単一の翻訳キー宣言。`default` は言語に依存しないフォールバック |
| `BaseI18n` | 翻訳キーセットの基底クラス（命名規則は `BaseConfig` に準拠）。サブクラスはクラス属性で複数の `I18nKey` を宣言 |
| `BaseI18n.register(prefix="", domain="app")` | クラスメソッド：宣言された全キーを i18nシステムに登録 |
| `key` | `I18nKey` のエイリアス（記述を簡潔にするため） |

使用例：

```python
from ErisPulse.Core.Bases import BaseI18n, key

class MyKeys(BaseI18n):
    # 簡潔なエイリアス記法
    hello = key(
        default="Hello",
        zh_CN="你好",
        zh_TW="你好",
        en="Hello",
        ja="こんにちは",
        ru="Привет",
    )
    bye = key(
        default="Bye",
        zh_CN="再见",
        zh_TW="再見",
        en="Bye",
        ja="さようなら",
        ru="До свидания",
    )

# 単独使用（手動登録）
MyKeys.register(prefix="myapp.", domain="myapp")
```

### SDK インスタンスからアクセス

```python
from ErisPulse import sdk

# sdk.i18n は直接インポートした i18n オブジェクトと同じです
sdk.i18n.set_language("en")
print(sdk.i18n.t("core.sdk.init.starting"))
```

---

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文檔包含語言切換行（各語言名稱用 `` | `` 分隔的行），務必嚴格遵守上方第 8 條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## ランタイム設定

### 設定 API を使用して i18n 設定を読み込む

```python
from ErisPulse.Core.Bases import I18nConfig
from ErisPulse.runtime import get_i18n_config

config = get_i18n_config()
print(config["language"])  # "auto" または具体的な言語コード

# I18nConfig は dataclass なので、設定テンプレートを生成するために使用できます
schema = I18nConfig.__dataclass_fields__
```

### 設定項目の説明

`config/config.toml` の `[ErisPulse.i18n]` セクション:

```toml
[ErisPulse.i18n]
# 表示言語。オプション:
# - "auto"      — システム言語を自動検出 (デフォルト)
# - "zh-CN"     — 簡体字中国語
# - "zh-TW"     — 繁体字中国語
# - "en"        — 英語
# - "ja"        — 日本語
# - "ru"        — ロシア語
language = "auto"
```

---

## ベストプラクティス

### 翻訳キーの命名

ドット区切りの名前空間形式の命名を使用することを推奨します。

```
<モジュール名>.<カテゴリ>.<説明>
```

例: `my_module.command.hello_desc`、`core.adapter.start_failed`

### 多言語対応

すべての言語の翻訳を一度に提供する必要はありません。欠けている言語は自動的に英語にフォールバックし、英語も存在しない場合はキー名自体が表示されます。

### 動的なコンテンツ

動的に生成されたコンテンツ（ユーザー名、数値など）の場合は、`{placeholder}` 形式でフォーマットします。

```python
# 翻訳定義
"user_count": "現在オンラインのユーザー：{count} 人"

# 使用
i18n.t("user_count", count=len(users))
```

### ログメッセージ

モジュールでフレームワークの Logger を使用している場合、これらのメッセージも自動的に現在の言語が使用されます。

```python
self.logger.info(i18n.t("my_module.startup"))
```

---

## CLI i18n との関係

CLI は**独立した**国際化モジュール（`ErisPulse.CLI.i18n`）を持ち、フレームワークコアの国際化モジュールと完全に非依存です。

- **Core i18n** — フレームワークコアモジュールで使用され、外部モジュールが翻訳を登録可能
- **CLI i18n** — コマンドラインインターフェース内部で使用され、Core と翻訳データを共有しない

この設計により、CLI の翻訳の変更がフレームワークコアの安定性に影響しないことが保証されます。

請直接返回翻译后的完整Markdown内容，不要包含任何其他文字。

再次提醒：如果文档包含语言切换行（各语言名称用 `` | `` 分隔的行），务必严格遵守上方第8条的格式要求，不要写出 ``[**Label**](file)`` 这类错误格式。



### 启动流程与手动控制

# 起動プロセスと手動制御

ErisPulse の `await sdk.run()` / `await sdk.init()` は、一連の起動プロセスを「一行のコード」にラップしています。しかし、部分的なロード、動的登録、ホットプラグ、カスタムロード戦略の注入など、完全にカスタム起動プロセスが必要な場合、このプロセスの内部で何が起こっているのか、および各ステップを手動で駆動する方法を理解する必要があります。

本文では、起動プロセスを独立したステップに分解し、それぞれの役割と呼び出し順序を説明し、手動で完全な起動を行うための例を示します。

> 本文では、[最初のロボット](../getting-started/first-bot.md)を実行し、`sdk.run(keep_running=True/False)` の2つのモードを理解していることを前提としています。本文では、`init()` **内部**のプロセス分解と、`init()` / `init_task()` / `init_sync()` などのより低レベルなエントリポイントに焦点を当てます。

## SDK トップレベルエントリ一覧

`run()` の2つの `keep_running` モードに加えて、SDK には異なった**非同期性、戻り値、および例外のラッピング**を持ついくつかの低レベルな初期化エントリが提供されています。

| エントリ | 非同期性 | 戻り値 | 例外処理 | 適用シーン |
|------|--------|--------|----------|----------|
| `await sdk.run(True)` | async、ブロックして維持 | `None`（終了時に自動 `uninit`） | モジュール/アダプタエラーが捕捉され、プロセスをクラッシュさせない | ロボットアプリケーションのみ |
| `await sdk.run(False)` | async、ブロックしない | `None`（自動アンロードしない） | 同上 | 初期化後にカスタムロジックを実行 |
| `await sdk.init()` | async、`await` 必須 | `bool` | **ラップしない**、例外は上に投げられる | ライフサイクルを手動で制御（`uninit()` と併用） |
| `sdk.init_task()` | async、`Task` を返してブロックしない | `asyncio.Task` | `init()` と同じ | 並列で他の初期化を実行する、またはイベントループがまだ実行されていない |
| `sdk.init_sync()` | **同期**、現在のスレッドをブロック | `bool` | `init()` と同じ | コマンドラインスクリプト、イベントループのない同期エントリ |

> **よくある誤解**：`await sdk.init()` **は** `await sdk.run(keep_running=False)` **と等価ではありません**。2点の違いがあります：① `init()` は `bool` を返し、`run()` は `None` を返す；② `run()` は初期化と実行プロセスを `try/except` でラップし（モジュール/アダプタエラーを捕捉してクラッシュを防ぐ）、`init()` はラップせず、例外は直接上に投げられます。アンロードやカスタム例外処理が必要な場合は、`init()` + `uninit()` を使用してください。

## 起動プロセスの概要

`sdk.init()`（正確にはその内部の `Initializer.init()`）は、以下の順序でフレームワーク全体を起動します：

```mermaid
flowchart TD
    A[0. 環境準備<br/>設定のロード / 例外処理] --> B
    B[1. 並列発見とロード<br/>AdapterLoader.load / ModuleLoader.load<br/>内部で Finder.find_all を呼び出す] --> C
    C[2. アダプタの登録<br/>AdapterLoader.register_to_manager] --> D
    D[3. アダプタの起動<br/>adapter.startup] --> E
    E[4. モジュールの登録<br/>ModuleLoader.register_to_manager] --> F
    F[5. モジュールの初期化<br/>ModuleLoader.initialize_modules<br/>インスタンス化して sdk にマウント] --> G
    G[6. ルーティングサーバーの起動<br/>router.start]
```

対応するコアコンポーネント：

| 層 | コンポーネント | 役割 |
|----|------|------|
| 発見 | `AdapterFinder` / `ModuleFinder` | 既にインストールされたパッケージの entry-points から**発見**する |
| ロード | `AdapterLoader` / `ModuleLoader` | 発見 + インポート + メタデータの読み取り + 有効/無効の判断、オブジェクトリストを返す |
| 登録 | `*Loader.register_to_manager` | オブジェクトを対応するマネージャーに登録する |
| 管理 | `sdk.adapter` / `sdk.module` | アダプタ/モジュールのインスタンスを維持し、起動/停止のインターフェースを提供する |
| 初期化 | `ModuleLoader.initialize_modules` | モジュールのインスタンスを作成し、`sdk` にマウントする（依存関係のトポロジカルソートを処理） |
| ルーティング | `sdk.router` | HTTP / WebSocket サーバー |

> **重要**：`Finder` と `Loader` は2つの層です。`Loader` は内部で**すでに** `Finder` を保持しています（`AdapterLoader` は `AdapterFinder` を、`ModuleLoader` は `ModuleFinder` を持っています）。ほとんどのシーンでは `Loader` を使用するだけで十分です。"インポートせずにリストする"必要がある場合にのみ `Finder` を個別に使用します。

## 各ステップの詳細

### 1. 発見層：Finder

Finder は「どのパッケージがアダプタ/モジュールを提供しているか」を発見するだけです。インポートやインスタンス化はしません。

```python
from ErisPulse.finders import AdapterFinder, ModuleFinder

adapter_finder = AdapterFinder()
module_finder = ModuleFinder()

# すべてのインストール済みアダプタ/モジュールの entry-points を検索
adapter_entries = adapter_finder.find_all()    # list[EntryPoint]
module_entries = module_finder.find_all()      # list[EntryPoint]

# 名前で単一の検索
entry = module_finder.find_by_name("MyModule")  # EntryPoint | None
```

各 `EntryPoint` は `.load()` で対応するクラスを得られますが、通常は手動で呼び出す必要はありません。`Loader` が行います。

### 2. ロード層：Loader

Loader は Finder の上に「インポート + メタデータの読み取り + 有効/無効の判断」を行っています。

```python
from ErisPulse.loaders import AdapterLoader, ModuleLoader
from ErisPulse import sdk

adapter_loader = AdapterLoader()
module_loader = ModuleLoader()

# load() 内部：finder.find_all() を呼び出す → 各 entry-point を処理 → 3タプルを返す
adapter_objs, enabled_adapters, disabled_adapters = await adapter_loader.load(sdk.adapter)
module_objs, enabled_modules, disabled_modules = await module_loader.load(sdk.module)
```

`load()` が返す3タプル：

| 戻り値 | 含意 |
|--------|------|
| `objs` (`dict`) | 名称 → オブジェクト（アダプタクラス / モジュールラッパー） |
| `enabled` (`list[str]`) | 有効化された名称（設定で無効化されていない） |
| `disabled` (`list[str]`) | 無効化された名称 |

#### ロード失敗時の診断情報

モジュール/アダプタがロードまたは初期化段階で例外を送出した場合、フレームワークはそのコンポーネントをスキップして他のコンポーネントのロードを続け、**ユーザーのコードフレームの要約**を出力します。これにより、通常の INFO レベルでもエラー箇所を特定でき、手動で DEBUG モードを再開する必要がありません。

```
[ERROR] [ModuleLoader] entry-point からモジュール MyModule のロードに失敗しました。スキップしました: 'NoneType' object has no attribute 'platform'
  → MyModule/Core.py:42 in on_load
      adapter = sdk.platform
  → AttributeError: 'NoneType' object has no attribute 'platform'
  → ヒント: ログレベルを DEBUG に上げると完全なスタックトレースを表示できます。モジュール MyModule の実装コードを確認してください。
```

診断情報は `ErisPulse.runtime.diagnostics` モジュールによって生成され、フレームワーク内部のフレームは自動的にフィルタリングされ、ユーザーのコードフレームのみが残ります。カスタムロードロジックで再利用する場合は：

```python
from ErisPulse.runtime import log_diagnostic

try:
    risky_init()
except Exception as e:
    log_diagnostic(e)  # 自動的にユーザーのコードフレームを抽出して ERROR ログに記録
```

このモジュールには、`extract_user_frame()`（構造化されたフレーム情報を返す）と `format_diagnostic_block()`（複数行のテキストを返す）という2つの低レベル関数もあります。

### 3. 登録層：register_to_manager

Loader が出力したオブジェクトをマネージャーに登録し、`sdk.adapter` / `sdk.module` がそれらを認識できるようにします。

```python
# アダプタの登録（すべて成功した場合は bool を返す）
await adapter_loader.register_to_manager(enabled_adapters, adapter_objs, sdk.adapter)

# モジュールの登録
await module_loader.register_to_manager(enabled_modules, module_objs, sdk.module)
```

登録後、アダプタは `sdk.adapter._adapters` に、モジュールクラスは `sdk.module` に登録されますが、**まだ起動/インスタンス化されていません**。

### 4. アダプタの起動

```python
# すべての登録済みアダプタを起動
await sdk.adapter.startup()
# または特定のプラットフォームを指定
await sdk.adapter.startup("yunhu")
await sdk.adapter.startup(["yunhu", "telegram"])
```

> 登録 ≠ 起動。`register_to_manager` は単に登録するだけです。`startup` でアダプタの `start()` を呼び出し、プラットフォームとの接続を確立します。

### 5. モジュールの初期化

モジュールはアダプタよりも1ステップ多く、**インスタンス化**して `sdk` にマウントする必要があります（これにより `sdk.MyModule.xxx` で呼び出すことができます）。このステップでは、モジュール間の依存宣言とトポロジカルソートも処理されます。

```python
success = await module_loader.initialize_modules(
    enabled_modules, module_objs, sdk.module, sdk
)
```

インスタンス化に成功すると、モジュールは `sdk.<ModuleName>` に表示されます。

### 6. ルーティングサーバーの起動

```python
await sdk.router.start(
    host="0.0.0.0",
    port=8000,
    ssl_certfile=None,
    ssl_keyfile=None,
)
```

ルーティングサーバーは、アダプタの Webhook / WebSocket コールバックを受け取ります。起動しないと、サーバーモードのアダプタはメッセージを受け取れません。

## 完全な手動起動の例

以下のコードは `await sdk.init()` のコアプロセスと**等価**ですが、各ステップが明示的に表示されており、任意の段階でカスタムロジックを挿入できます。

```python
import asyncio
from ErisPulse import sdk
from ErisPulse.loaders import AdapterLoader, ModuleLoader

async def manual_startup():
    # 0. 環境準備（設定のロード、グローバル例外処理の登録）
    #    _prepare_environment は init() 内部の前置ステップです。手動プロセスでも先に呼び出す必要があります。
    #    そうしないと、Loader は設定を読み取れず、すべてのアダプタ/モジュールを誤って無効化と判断します。
    if not await sdk._prepare_environment():
        print("環境準備に失敗しました")
        return False

    # 1. ローダーの作成（内部でそれぞれ Finder を保持）
    adapter_loader = AdapterLoader()
    module_loader = ModuleLoader()

    # 2. 並列発見とロード（init() 内部と同じ gather を使用）
    (adapter_objs, enabled_adapters, disabled_adapters), \
    (module_objs, enabled_modules, disabled_modules) = await asyncio.gather(
        adapter_loader.load(sdk.adapter),
        module_loader.load(sdk.module),
    )

    # 3. アダプタの登録
    await adapter_loader.register_to_manager(
        enabled_adapters, adapter_objs, sdk.adapter
    )

    # 4. アダプタの起動
    if enabled_adapters:
        await sdk.adapter.startup()

    # 5. モジュールの登録
    await module_loader.register_to_manager(
        enabled_modules, module_objs, sdk.module
    )

    # 6. モジュールの初期化（インスタンス化 + sdk にマウント）
    if enabled_modules:
        await module_loader.initialize_modules(
            enabled_modules, module_objs, sdk.module, sdk
        )

    # 7. ルーティングサーバーの起動
    await sdk.router.start(host="0.0.0.0", port=8000)

    print("手動起動完了")
    return True

async def main():
    ok = await manual_startup()
    if ok:
        # プログラムを維持する（手動プロセスでは自動的にブロックされない）
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### いつ手動起動が必要か？

ほとんどの場合、手動起動は必要ありません。`await sdk.run()` で上記のすべてが行われています。手動起動は以下のシナリオでのみ価値があります：

- **部分的なロード**：指定されたアダプタ/モジュールのみをロードし、他のものをスキップ
- **動的登録**：実行時に条件に応じて新しいアダプタ/モジュールを登録
- **カスタム順序**：デフォルトのロード順序を乱す（例：特定のモジュールを起動してからアダプタを起動）
- **戦略の注入**：Loader にカスタムの厳密モードマネージャー、ロード戦略などを注入
- **デバッグ/診断**：特定の段階で失敗した場合、手動で駆動して問題を特定

## 実行時細粒度制御

`sdk.run()` で起動した後でも、SDK 全体を再起動することなく、各サブシステムを個別に制御できます。

### アダプタのホット起動/停止

```python
# アダプタのホットリスタート（接続を修復し、他のプラットフォームに影響しない）
await sdk.adapter.shutdown("yunhu")
await sdk.adapter.startup("yunhu")

# 実行中に新しいプラットフォームを起動
await sdk.adapter.startup("telegram")

# 一時的にプラットフォームをオフラインにする
await sdk.adapter.shutdown("telegram")
```

> `adapter.startup()` はアダプタが**マネージャーに登録されている**ことを要求します。登録は `init()` / `run()` 内部で行われるため、これは起動**後の**細粒度制御です。

### ルーティングサーバー

```python
# 一時的に webhook サーバーをオフラインにする
await sdk.router.stop()

# 再起動（例：ポートを変更した場合）
await sdk.router.start(host="0.0.0.0", port=9000)
```

### モジュールのオンデマンドロード

```python
# モジュールを手動でロードする（おそらく遅延ロードのモジュール）
await sdk.load_module("MyModule")
```

## エレガントなシャットダウン

2.7.0 以降、`sdk.shutdown()` は**プログラムによるエレガントなシャットダウン**を提供します：シャットダウンイベントを設定し、`await sdk.run(keep_running=True)` で待機中のメインループが返り、`uninit()` がリソースのクリーンアップをトリガーします。

```python
# 任意のコルーチンで呼び出し、エレガントな終了をトリガー（run() は待機を返し、自動 uninit）
sdk.shutdown()
```

典型的な用途：

```python
async def shutdown_after_idle():
    await asyncio.sleep(3600)
    sdk.shutdown()  # 空き1時間後にエレガントに終了
```

**シグナル処理**：`run()` 内部では `SIGTERM` / `SIGHUP` ハンドラが登録され、システムシグナルをエレガントなシャットダウンに変換します——コンテナ編成（Docker `docker stop`）や `systemd` でサービスを停止する場合、プロセスは `uninit()` のクリーンアップを完了してから強制終了されます。

- Windows は `loop.add_signal_handler` をサポートしていません。シグナルハンドラは自動的にスキップされます（`sdk.shutdown()` または Ctrl+C でシャットダウンをトリガーできます）
- `sdk.shutdown()` を繰り返し呼び出すことは安全です（イベントが設定された後は無操作になります）

## アンロードプロセス

起動の逆操作は `await sdk.uninit()` で、逆順でリソースを解放します：

1. すべてのアダプタを閉じる（`adapter.shutdown()`）
2. すべてのモジュールをアンロードする
3. すべてのイベントハンドラをクリーンアップする
4. マネージャーと SDK 上のモジュール属性をクリーンアップする

手動起動の場合は、終了前に `uninit()` を呼び出してエレガントなシャットダウンを保証してください：

```python
try:
    await asyncio.Event().wait()   # プログラムを維持
finally:
    await sdk.uninit()
```

## リスタート

SDK には2種類のリスタート方法があります。どちらも事前にアンロードする必要はありません——フレームワークが自動的に処理します：

| 方法 | 呼び出し | 行動 | 適用シーン |
|------|------|------|----------|
| ホットリスタート | `await sdk.restart()` | 同一プロセス内で `uninit()` の後に再 `init()`、アダプタ/モジュールを再ロード | 設定の再ロード、モジュールのホットアップデート |
| ハードリスタート | `await sdk.hard_restart()` | `uninit()` の後にプロセスを終了し、親プロセス（`epsdk run`）が新しいプロセスを起動 | メモリ/リソースリークが疑われる、完全にクリーンなリスタートが必要な場合 |

```python
# ホットリスタート：同一プロセス内で再ロード（最も一般的）
await sdk.restart()

# ハードリスタート：プロセスを終了し、`epsdk run` で起動した場合にのみ有効
await sdk.hard_restart()
```

> **2点注意**：
> 1. これらのメソッドはバックグラウンドタスクで実行され、**即座に `True` を返す**ことで「リスタートタスクがスケジュールされた」ことを示します。リスタートが完了したわけではありません。実際のリスタートはバックグラウンドで行われ、現在のイベントフローを中断しません。
> 2. `hard_restart()` **は `epsdk run main.py` で起動した場合にのみ有効です**。その原理は、アンロード後に**終了コード 42** でプロセスを終了し、`epsdk run` の親プロセスが 42 を検出して新しいプロセスを再起動することです。`python main.py` で直接起動した場合は、42 で終了した後プロセスが終了し、自動的に再起動されません。

### ハードリスタートはいつ使うか？

ハードリスタートは「より徹底的なリスタート」だけでなく、以下のシナリオでより適切で、場合によってはより効率的です：

- **バイナリライブラリ（C拡張）の副作用**：ホットリスタートは同じプロセス内で行われるため、C拡張、開いたファイルディスクリプタ、スレッドなどのプロセスレベルのリソースを解放できません。ハードリスタートでは新しいプロセスが起動され、これらの副作用は完全にクリアされます。
- **リソースリークの調査**：メモリやハンドルのリークが疑われる場合、ハードリスタートはクリーンな環境を得ることができます。
- **頻繁なリスタートに性能が敏感な場合**：ハードリスタートは同じプロセス内でアンロード→再ロードのオーバーヘッドを省くため、実際にはホットリスタートよりも効率的です。

> ダッシュボード管理パネルの「フレームワークリスタート」機能は、下層で `hard_restart()` を呼び出しています。
> また、ハードリスタートは **`epsdk` の `run` コマンドを使用して起動しなければ効果がありません**。`run` コマンドは 42 退出コードを検出してプロセスを再起動するため、`python main.py` で起動した場合は 42 でプロセスが終了し、自動的に再起動されません。この点は注意してください！！



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



====
生态模块
====


### Dashboard 使用与视窗注册

# ErisPulse-Dashboard

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) は、ErisDev が直接メンテナンスしている **Web 管理パネルモジュール** であり、ErisPulse に視覚的なランタイム管理インターフェースを提供します：モジュールの起動停止、設定の編集、ログの閲覧、イベントストリームの監視など。

> [!IMPORTANT]
> Dashboard は **ErisPulse フレームワークの組み込み機能ではありません**。別途インストールが必要です：
>
> ```bash
> epsdk install Dashboard
> ```

Dashboard では、他の ErisPulse モジュールがカスタムの管理ページをサイドバーに登録することもサポートしています。登録すると、ユーザーは Dashboard で該当モジュールの専用ウィンドウページに切り替えるだけでよく、追加の独立したフロントエンドインターフェースの開発は不要です。

> [!NOTE]
> ウィンドウ登録は**オプション機能**です。
>
> - Dashboard モジュールが**インストールされていない**または**読み込まれていない**場合、`sdk.Dashboard.register_view()` を呼び出すと例外がスローされます
> - モジュール自体の他の機能に影響を与えないように、登録コードは必ず `try/except` で囲んでください
> - 登録前に Dashboard が使用可能かどうかを確認することをお勧めします：`hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## 動作原理

```
モジュール on_load()
  → sdk.Dashboard.register_view(...) の呼び出し
  → Dashboard バックエンドでウィンドウ情報を保存
  → WebSocket でフロントエンドに通知
  → フロントエンドがサイドバーのナビゲーション項目 + ページコンテナを動的に作成
  → ユーザーがクリックすればモジュールのウィンドウを閲覧可能
```

---

## 登録 API

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # 必須、一意の識別子
    title="マイモジュール",            # 中国語表示名
    title_en="My Module",             # 英語表示名
    icon_svg='<svg>...</svg>',        # サイドバーのアイコン SVG
    html_content='<div>...</div>',     # ページ HTML コンテンツ
    js_content='function xxx() {}',    # ページ JavaScript ロジック
    css_content='.my-style {}',        # オプションのカスタム CSS
    iframe_url='',                     # iframe モード URL（html_content との二択）
    loader="loadMyModuleView",         # このページに切り替えたときに呼び出される JS 関数名
    group="group_extensions",          # サイドバーのグループ
    group_title="",                    # カスタムグループの中国語タイトル
    group_title_en="",                 # カスタムグループの英語タイトル
)
```

### パラメータ説明

| パラメータ | 型 | 必須 | 説明 |
|------|------|------|------|
| `id` | `str` | Yes | ウィンドウの一意の識別子。モジュール名を使用することをお勧めします |
| `title` | `str` | No | 中国語表示名。デフォルトは `id` を使用 |
| `title_en` | `str` | No | 英語表示名。デフォルトは `title` を使用 |
| `icon_svg` | `str` | No | サイドバーのアイコンの完全な SVG 文字列 |
| `html_content` | `str` | No* | インジェクションモードのページ HTML コンテンツ |
| `js_content` | `str` | No | ページ JavaScript コード |
| `css_content` | `str` | No | ページのカスタム CSS スタイル |
| `iframe_url` | `str` | No* | iframe モードの URL。設定すると `html_content` は無視されます |
| `loader` | `str` | No | ページがアクティブになったときに自動的に呼び出される JS 関数名 |
| `group` | `str` | No | サイドバーのグループ識別子。デフォルトは `group_extensions` |
| `group_title` | `str` | No | カスタムグループの中国語タイトル |
| `group_title_en` | `str` | No | カスタムグループの英語タイトル |

> *`html_content` と `iframe_url` の少なくとも一方を提供してください。そうしないと、ページは空になります。

---

## 2つのインジェクションモード

### モード1：HTML/JS インジェクション（推奨）

HTML、JS、CSS の文字列を直接提供し、Dashboard はコンテンツをページにインジェクトします。このモードは Dashboard のスタイルと完全に一致しており、Dashboard が提供する CSS クラス名を使用することを推奨します。

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="こんにちはページ", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">これはサンプルページです</div></div>',
    group="group_tools",
)
```

> 完全な天気モジュールの例（API ルート、JS インタラクションなどを含む）は、下記の[完全なモジュールの例](#完全なモジュールの例)を参照してください。

### モード2：iframe 埋め込み

モジュールが独自の HTML ページ URL（ルートの登録が必要）を提供し、Dashboard は iframe 方式で埋め込みます。完全に独立した UI または複雑なインタラクションが必要なシーンに適しています。

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="データビジュアライザー", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> iframe モードでは、認証用の `token` パラメータが URL の後に自動的に追加されます。

---

## サイドバーのグループ

モジュールはウィンドウが配置されるサイドバーのグループを指定できます。Dashboard には以下のグループが組み込まれています：

| グループ識別子 | 中国語名 | 位置 |
|---------|--------|------|
| `group_overview` | 概要 | 第1グループ |
| `group_events` | イベント | 第2グループ |
| `group_extensions` | 拡張 | 第3グループ（デフォルト） |
| `group_system` | システム | 第4グループ |
| `group_tools` | ツール | 第5グループ |

組み込みのグループ名を指定すると、モジュールのウィンドウはそのグループの末尾に追加されます：

```python
group="group_tools"  # "ツール" グループに追加
```

カスタムグループ名（`group_` で始まらないもの）も使用できます。Dashboard は自動的に新しいグループを作成します：

```python
group="my_group",
group_title="マイグループ",
group_title_en="My Group",
```

---

## 一般的な CSS クラス名

モジュールのウィンドウが HTML インジェクションモードを使用する場合、視覚的な一貫性を維持するために Dashboard の既存の CSS クラス名を直接使用できます：

| クラス名 | 用途 |
|------|------|
| `page-title` | ページタイトル。例: `<h1 class="page-title">タイトル</h1>` |
| `card` | カードコンテナ |
| `card-header` | カードのタイトルバー |
| `card-body` | カードのコンテンツエリア |
| `grid-2` | 2列のグリッドレイアウト |
| `grid-3` | 3列のグリッドレイアウト |
| `btn` | 基本ボタン |
| `btn-primary` | プライマリボタン（青） |
| `btn-secondary` | セカンダリボタン |
| `btn-icon` | アイコンボタン |
| `btn-danger` | 危険操作ボタン |

Dashboard は CSS 変数を使用してテーマカラーを制御するため、モジュールのウィンドウで直接参照できます：

| CSS 変数 | 用途 |
|----------|------|
| `var(--bg-p)` | メイン背景色 |
| `var(--bg-s)` | サブ背景色 |
| `var(--bg-t)` | 3段階背景色（カードなど） |
| `var(--tx-p)` | メインテキスト色 |
| `var(--tx-s)` | サブテキスト色 |
| `var(--tx-t)` | 補助テキスト色 |
| `var(--bd)` | ボーダーカラー |
| `var(--accent)` | アクセントカラー |
| `var(--ok-c)` | 成功色 |
| `var(--er-c)` | エラーカラー |

これらの変数は Dashboard のライト/ダークモードのテーマに応じて自動的に切り替わるため、モジュールに追加の処理は不要です。

---

## 認証と API 呼び出し

モジュールのウィンドウの JS でモジュール自身の API を呼び出す際は、認証のため Dashboard のトークンを含める必要があります：

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

モジュールの API エンドポイントは、トークンを検証するかどうかを独自に決定できます。検証が必要な場合は、リクエストヘッダーから抽出できます：

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## 完全なモジュールの例

以下は、ウィンドウの登録方法、API データの提供、およびアンインストール時のリソースクリーンアップ方法を示す、完全な天気モジュールの例です。

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
        self.logger.info("天気モジュールが読み込まれました")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("天気モジュールがアンインストールされました")

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
        return {
            "city": self.config.get("city", "北京"),
            "temp": 25,
            "humidity": 60,
        }

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="天気", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">天気照会</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">現在の天気情報を表示</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">現在の天気</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">クリックして更新</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">操作</div>
                            <div class="card-body">
                                <button class="btn btn-primary" onclick="refreshWeather()">更新</button>
                            </div>
                        </div>
                    </div>
                ''',
                js_content='''
                    async function loadWeatherView() { await refreshWeather(); }
                    async function refreshWeather() {
                        var el = document.getElementById('weather-info');
                        if (!el) return;
                        el.textContent = '読み込み中...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>都市: ' + (data.city || '--') + '</p>' +
                                           '<p>気温: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>湿度: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = '読み込みに失敗: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"Dashboard ウィンドウの登録に失敗しました: {e}")
```

---

## ウィンドウの登録解除

モジュールのアンインストール時に、登録済みのウィンドウをクリーンアップするために `unregister_view()` を呼び出す必要があります：

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

登録解除後、Dashboard フロントエンドは WebSocket を通じてサイドバーのナビゲーション項目とページのコンテンツをリアルタイムで削除するため、ユーザーがページをリフレッシュする必要はありません。

---

## 注意事項

1. **読み込み順序** — Dashboard の読み込み優先度は `99999`（高優先度）です。Dashboard が先に読み込み完了するように、あなたのモジュールの優先度はこの値より低く設定してください（例: `50`）
2. **防御的なプログラミング** — ウィンドウの登録時に `try/except` で囲む必要があります。Dashboard モジュールがインストールされていないか、読み込まれていない可能性があるため
3. **リソースのクリーンアップ** — `on_unload` で `unregister_view()` を呼び出して、登録済みのウィンドウを削除してください
4. **ID の一意性** — `id` パラメータは全体の Dashboard 内で一意である必要があります。モジュール名を直接使用することをお勧めします
5. **SVG アイコン** — `icon_svg` は完全な `<svg>` タグである必要があります。サイズには `viewBox="0 0 24 24"` を使用することを推奨します。Dashboard のテーマカラーを継承するために `stroke="currentColor"` を使用してください
6. **JS 関数名の命名** — `js_content` 内の関数名は一意である必要があります（例: `loadWeatherView` ）。他のモジュールと衝突しないようにしてください
7. **動的更新** — モジュールがウィンドウを登録/解除した後、Dashboard フロントエンドは WebSocket を通じてサイドバーをリアルタイムで更新するため、ページのリフレッシュは不要です



### Takumi 图片渲染

# ErisPulse-Takumi

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) は ccd2s によってメンテナンスされている **サードパーティの画像レンダリングモジュール** です。[takumi-py](https://github.com/BalconyJH/takumi-py) をベースとしており、Bot が HTML、ノードツリー、Jinja テンプレート、SVG、アニメーションを画像としてレンダリングできるようにします。モジュールには **日本語と英語のフォント**（Noto Sans SC / Roboto / Source Code Pro）が標準搭載されており、追加の設定は不要です。

> [!IMPORTANT]
> Takumi は ErisPulse フレームワークの組み込み機能ではありません。個別にインストールが必要です：
>
> ```bash
> epsdk install Takumi
> ```

適用シナリオ：

- データ/統計をカード画像としてレンダリング
- Markdown / 長いテキストをスタイルの崩れが少ない画像としてレンダリングし、プラットフォームごとのスタイルの差異を回避
- SVG / アニメーションを生成して動的な視覚効果を実現
- 日本語と英語の混在したテキスト付き画像（標準搭載のフォントを使用可能）

---

Please return the complete translated Markdown content below.

## インストールと有効化

```bash
epsdk install Takumi
```

インストール後、モジュールは自動的に読み込まれます。設定で有効を確認してください。

```toml
[Takumi]
enabled = true
```

---

## クイックスタート

モジュールは自動的にロードされた後、モジュールマネージャーを通じて取得するか、`sdk` ショートカットを使用します：

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# 同等の書き方：takumi = sdk.Takumi
```

### HTML をレンダリング

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>こんにちは、ErisPulse</h1>
      <p>Takumi によってレンダリングされました</p>
    </div>
    """,
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
      font-family: "Noto Sans SC";
    }
    """],
    width=800,
    height=None,   # コンテンツに応じて自動的に高さを拡張
    lang="zh-CN",
)
```

### ノードツリーをレンダリング

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "中国語と English は直接レンダリング可能です",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

`png` は `bytes` です。`event.reply(png, method="Image")` を通じて送信できます（詳細は [Rendering results sending](docs/ja/rendering-results.md) を参照）。

## レンダリング API

`sdk.Takumi` は、底層の `takumi_py.Renderer` の全能力をプロキシしています：すべてのレンダリング、測定、SVG、アニメーション、テンプレートメソッドは `sdk.Takumi` で直接呼び出すことができます。これらのメソッドについては、モジュールは呼び出し時に**自動的に埋め込みフォントフォールバックスタック**（`takumi.families`）を注入するため、`font_families` を手動で渡す必要はありません。明示的に渡された場合は、呼び出し元の設定を尊重します。

### メソッド概要

| カテゴリ | メソッド | 戻り値 | 説明 |
|------|------|------|------|
| 静的レンダリング | `render_html(html, ...)` | `bytes` | HTML 文字列をレンダリング |
| | `render_node(node, ...)` | `bytes` | ノードツリー（dict）をレンダリング |
| | `render_template(name, ctx, ...)` | `bytes` | Jinja テンプレートをレンダリング |
| | `render_compiled(node, ...)` | `bytes` | コンパイル済みノードをレンダリング |
| SVG 出力 | `render_svg_html(html, ...)` | `str` | SVG を出力（HTML 入力） |
| | `render_svg_node(node, ...)` | `str` | SVG を出力（ノードツリー入力） |
| | `render_svg_template(name, ctx, ...)` | `str` | SVG を出力（テンプレート入力） |
| | `render_svg_compiled(node, ...)` | `str` | SVG を出力（コンパイル済み入力） |
| アニメーション | `render_animation(scenes, ...)` | `bytes` | マルチフレームアニメーションをエンコード |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | シーケンスの特定の時刻のフレームを取得 |
| 測定 | `measure_node(node, ...)` | `dict` | ノードツリーのレイアウトを測定 |
| | `measure_html(html, ...)` | `dict` | HTML のレイアウトを測定 |
| | `measure_compiled(node, ...)` | `dict` | コンパイル済みノードを測定 |
| コンパイル | `compile_node(node)` | `CompiledNode` | ノードツリーをコンパイル |
| | `compile_html(html, ...)` | `CompiledNode` | HTML をコンパイル |
| フォント | `register_font(font)` | `list[str]` | カスタムフォントを登録し、family リストを返す |
| | `register_fonts(fonts)` | `list[str]` | 一括登録 |

> `CompiledNode` は `resource_urls()` メソッドを公開しており、事前に読み込む必要がある HTTP(S) 画像参照を検出できます。これにより、リソースを事前に準備しやすくなります。

### 一般的なパラメータ

以下のパラメータは、静的レンダリングと SVG メソッドに適用されます（アニメーションメソッドには `fps` などがあり、対応する例を参照してください）：

| パラメータ | タイプ | デフォルト値 | 説明 |
|------|------|--------|------|
| `stylesheets` | `list[str]` | `None` | ドキュメントレベルの CSS 文字列のリスト。インライン `style` は HTML とともに解析されます |
| `width` | `int \| None` | `1200` | ビューポートの幅（ピクセル）。`None` はレイアウトから推論します |
| `height` | `int \| None` | `630` | キャンバスの高さ（ピクセル）。`None` はコンテンツに応じて自動的に高さを拡張します（[ビューポートと出力形式](#ビューポートと出力形式)を参照） |
| `lang` | `str \| None` | `None` | BCP-47 言語タグ（例：`zh-CN`）。テキスト整形と改行に影響します |
| `font_families` | `list[str]` | 自動注入 | フォントフォールバックスタック。便宜上のメソッドでは埋め込みフォントがデフォルトで注入されます |
| `format` | `str` | `"png"` | 出力形式（[ビューポートと出力形式](#ビューポートと出力形式)を参照） |
| `device_pixel_ratio` | `float` | `1.0` | デバイスピクセル比。出力解像度を制御します |
| `time_ms` | `int` | `0` | アニメーションのサンプリング時刻（ミリ秒） |
| `dithering` | `str` | `"none"` | ディザリングアルゴリズム：`none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | 有損圧縮の品質 |
| `lossless` | `bool \| None` | `None` | 無損圧縮を行うかどうか |
| `images` | `list` | `None` | 今回のレンダリングの画像リソース（`ImageResource` または `(src, bytes)` のタプル） |
| `keyframes` | `Mapping` | `None` | 構造化されたキーフレーム。`@keyframes` を記述する必要はありません |
| `options` | `RenderOptions` | — | `RenderOptions(...)` で集約してパラメータを渡します。フィールドは上の表と一致します |

完全なフィールド定義については `takumi_py.RenderOptions` を参照してください。

### ノードツリーの例

```python
png = takumi.render_node(
    {
        "type": "container",
        "style": {"padding": "32px", "backgroundColor": "#111827"},
        "children": [
            {"type": "text", "text": "タイトル", "style": {"fontSize": 32, "color": "white"}},
            {"type": "text", "text": "本文", "style": {"fontSize": 18, "color": "#9ca3af"}},
        ],
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

### Jinja テンプレートの例

```python
png = takumi.render_template(
    "card.html.jinja",
    {"title": "Takumi", "subtitle": "Jinja to image"},
    stylesheets=["""
    .card {
      width: 800px;
      padding: 48px;
      color: white;
      background: #111827;
    }
    """],
    width=800,
    height=None,
    lang="zh-CN",
)
```

> `filters={...}` を使用してカスタム Jinja フィルターを注入したり、`environment=...` を使用して完全な `jinja2.Environment` を渡したりできます。テンプレートディレクトリと環境設定の詳細については、[takumi-py テンプレートドキュメント](https://github.com/BalconyJH/takumi-py/blob/main/docs/ja/guides/templates.md)を参照してください。

### SVG 出力の例

```python
svg = takumi.render_svg_html(
    '<div class="card">Hello</div>',
    stylesheets=[".card { width: 800px; color: black; }"],
    width=800,
    height=None,
)
```

### アニメーションの例

```python
from takumi_py import AnimationScene

webp = takumi.render_animation(
    [
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "black"}},
            duration_ms=100,
        ),
        AnimationScene(
            {"type": "container", "style": {"width": "100%", "height": "100%", "backgroundColor": "white"}},
            duration_ms=100,
        ),
    ],
    width=64,
    height=64,
    fps=20,
    format="webp",
)
```

> 各フレームは `AnimationScene(node, duration_ms=...)` で構成されます。`duration_ms` は正数である必要があります。

---

## ビューポートと出力形式

### 出力形式

| 場面 | `format` 取値 |
|------|---------------|
| 静止画像 | `png`（デフォルト） / `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| アニメーション | `webp`（デフォルト） / `apng` / `gif` |

`format="raw"` は、カスタムなピクセル単位の処理を行うため、行優先（row-major）の RGBA バイトストリームを返します。

### 幅 (`width`) と高さ (`height`) について

`width` と `height` の役割は非対称です。

- `width` は**ビューポート幅**であり、テキストとレイアウトはこれに従って改行・リフローします。**固定値（例: `800`）にする**必要があります。さもないと、キャンバスがコンテンツの自然な幅に引き伸ばされ、テキストが改行されず、サイズが制御不能になります。
- `height` は**キャンバス高さ**であり、コンテンツの増加に応じて伸びます。`height` のデフォルト値は `630` です。`height=None` を渡すと、Takumi は**コンテンツに合わせてキャンバスの高さを自動的に広げます**（auto viewport）。

> [!TIP]
> **推奨される組み合わせ：`width` を固定 + `height=None`。** 固定サイズのキャンバスやトリミング効果が必要な場合のみ、具体的な `height` を指定してください。

> [!NOTE]
> `width` / `height` のどちらかを技術的に `None` として渡せば、レイアウトからの推論（ノード自体がサイズを宣言している場合など）に任せることができます。両方の値が指定された場合、出力サイズは確定した値となります。

---

## フォント

### 標準装備のフォント

| フォント | family | カテゴリ |
|------|--------|------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif（italic） |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace（italic） |

モジュールプロパティ：

| プロパティ | 説明 |
|------|------|
| `takumi.fonts` | 標準装備のフォントファイル名リスト |
| `takumi.families` | 登録済みフォント family リスト |

### 自動注入

`sdk.Takumi` のすべてのレンダリング、測定、SVG、アニメーション、テンプレートメソッドは、自動的に `takumi.families` をフォントフォールバックスタックとして注入されます。直接 `takumi.renderer`（ネイティブインスタンス）を呼び出すか、`create_renderer()` で作成された独立したインスタンスの場合は、手動で `font_families=takumi.families` を渡す必要があります。

### カスタムフォント

```python
from takumi_py import FontResource

families = takumi.renderer.register_font(
    FontResource(
        font_bytes,
        name="MyFont",
        weight=400,
        style="normal",
        generic_family="sans-serif",
    )
)
```

`register_font` は登録された family 名リストを返し、後続のレンダリング時に `font_families` として渡すことができます。

---

## レンダラー インスタンス

### 原生 Renderer

`takumi.renderer` は、生の `takumi_py.Renderer` インスタンスです。直接呼び出す際は、`font_families` を手動で渡す必要があります：

```python
png = takumi.renderer.render_html(
    "<div>こんにちは</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 独立 Renderer

フォント / 画像 / リソースのキャッシュを分離する必要がある場合（長寿命プロセス、マルチテナントシナリオなど）、独立した `Renderer` を作成できます。組み込みフォントは自動的に登録されます：

```python
renderer = takumi.create_renderer(cache_max_bytes=64 * 1024 * 1024)

png = renderer.render_html(
    "<div>独立 Renderer</div>",
    font_families=takumi.families,
    width=800,
    height=None,
    lang="zh-CN",
)
```

`create_renderer()` は、`takumi_py.Renderer` のコンストラクタ引数を受け入れます：

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `load_default_fonts` | `bool` | `False` | takumi-py に付属するフォントを読み込むかどうか（組み込みフォントは常に読み込まれます） |
| `fonts` | `list[FontResource]` | `None` | 追加で登録するカスタムフォント |
| `cache_max_bytes` | `int \| None` | `None` | リソースキャッシュの上限（バイト）；`0` で無効化 |
| `persistent_images` | `list` | `None` | 永続化する画像リソース |

> 独立インスタンスはモジュールプロキシを経由しないため、統一された組み込みフォントのフォールバックスタックを維持するには、明示的に `font_families=takumi.families` を渡す必要があります。`font_families` を明示的に渡した場合、モジュールは呼び出し元の設定を尊重し、デフォルトのフォールバックスタックを注入しなくなります；`RenderOptions(font_families=...)` も有効です。

---

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## レンダリング結果を送信

レンダリングされた画像は `bytes` 形式で、イベントで直接返信して送信できます：

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# 方法1：Imageメソッドで返信
await event.reply(png, method="Image")

# 方法2：OneBot12メッセージセグメントで返信
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> 各プラットフォームの画像のパッケージ化はアダプターが一括で処理します。詳細は [MessageBuilder 詳細](../advanced/message-builder.md) と [送信メソッド仕様](../standards/send-method-spec.md) を参照してください。

---

## 設定

```toml
[Takumi]
enabled = true
```

---



====
平台概览
====


### 平台特性与 SendDSL 通用语法

# ErisPulse PlatformFeatures ドキュメント

> 基準プロトコル: [OneBot12](https://12.onebot.dev/) 
> 
> 本文ドキュメントは**プラットフォーム固有の機能ガイド**であり、以下を含む：
> - 各アダプターがサポートするSendメソッドのチェーン呼び出し例
> - プラットフォーム固有のイベント/メッセージフォーマットの説明
> 
> 一般的な使用方法については、以下を参照してください：
> - [基本概念](../getting-started/basic-concepts.md)
> - [イベント変換標準](../standards/event-conversion.md)  
> - [APIレスポンス規格](../standards/api-response.md)

---

## プラットフォーム固有の機能

このセクションは、各アダプター開発者が維持し、OneBot12標準との差異や拡張機能を説明するためのものです。以下の各プラットフォームの詳細ドキュメントを参照してください：

- [維持説明](maintain-notes.md)

- [雲湖プラットフォームの特性](docs/ja/yunhu.md)
- [雲湖ユーザープラットフォームの特性](docs/ja/yunhu_user.md)
- [Telegramプラットフォームの特性](docs/ja/telegram.md)
- [OneBot11プラットフォームの特性](docs/ja/onebot11.md)
- [OneBot12プラットフォームの特性](docs/ja/onebot12.md)
- [メールプラットフォームの特性](docs/ja/email.md)
- [Kook(開黒啦)プラットフォームの特性](docs/ja/kook.md)
- [Matrixプラットフォームの特性](docs/ja/matrix.md)
- [QQ公式ロボットプラットフォームの特性](docs/ja/qqbot.md)
- [花楓コーヒーショップ](docs/ja/ideaura.md)
- [Discord](docs/ja/discord.md)
- [Webhookプロトコルブリッジ](docs/ja/webhook.md)
- [WeChat公式アカウント](docs/ja/wechatmp.md)

> さらに `sandbox` アダプターもありますが、このアダプターにはプラットフォーム固有の機能ドキュメントを維持する必要はありません

---

## 一般的なインターフェース

### Send チェーン呼び出し
すべてのアダプターは以下の標準呼び出し方法をサポートしています：

> **注意:** ドキュメント内の `{AdapterName}` は実際のアダプター名（例: `yunhu`、`telegram`、`onebot11`、`email` など）に置き換えてください。

1. タイプとIDを指定: `To(type,id).Func()`
   ```python
   # アダプターインスタンスを取得
   my_adapter = adapter.get("{AdapterName}")
   
   # メッセージを送信
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. IDのみを指定: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 送信アカウントを指定: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例:
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼び出し: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("ブロードキャストメッセージ")
   
   # 例:
   email = adapter.get("email")
   await email.Send.Text("ブロードキャストメッセージ")
   ```

#### 非同期送信と結果処理

Send DSL のメソッドは `asyncio.Task` オブジェクトを返します。これは、結果を即座に待つかどうかを選択できるということを意味します：

```python
# アダプターインスタンスを取得
my_adapter = adapter.get("{AdapterName}")

# 結果を待たずに、バックグラウンドでメッセージを送信
task = my_adapter.Send.To("user", "123").Text("Hello")

# 送信結果を取得する必要がある場合は、後で待つことができます
result = await task
```

#### 送信ルールデコレーター

実際の開発では、送信成功後に後続のロジックを実行する、失敗時に自動的にリトライする、タイムアウトで取り消す、送信の進行状況を監視するなどの処理が必要な場合があります。Send DSL には、ルールをチェーンメソッドで追加するための送信ルールデコレーターが組み込まれています：

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信成功後に実行されるコールバック（複数回呼び出し可能） |
| `.Retry(times=1)` | 失敗時に自動的に N 回リトライする（最初の送信を含めて合計 N+1 回） |
| `.Timeout(seconds)` | 単一送信のタイムアウト、タイムアウトで取り消す（Retry と重ねて使用可能） |
| `.Defer(seconds)` | 送信を遅延させる（プロセス内でのタイマー、永続化はしない） |
| `.OnProgress(callback)` | 各段階の進行状況コールバック、SendContext を渡す |
| `.OnError(callback)` | 最終的に失敗したときのエラーコールバック（1回のみ発動） |

```python
yunhu = adapter.get("yunhu")

# 送信成功後にポイントを減らす
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消費成功"))

# 失敗リトライ + タイムアウトキャンセル + 進行状況監視
def on_progress(ctx):
    print(f"段階: {ctx.stage}, 試行: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # 最大3回リトライ
        .Timeout(10)           # 各回10秒のタイムアウト
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要な通知"))
```

ルールメソッドは `self` を返すため、送信メソッド（Text/Image など）の前に呼び出す必要があります。`SendContext` には `stage`（pending/sending/retrying/success/failed/timeout）、`attempt`、`elapsed`、`error`、`result` などのフィールドが含まれており、監視に便利です。

#### バッチ構築モード（Build）

1つのチェーンで複数の送信メソッドを構築し、最後に一括で実行します。これは「一気に複数のメッセージを送信する」状況に適しています：

```python
yunhu = adapter.get("yunhu")

# 複数のメッセージを構築し、一括送信
results = await (yunhu.Send.To("user", "123")
                .Build()                     # 構築モードに入る
                .Text("通知1")
                .Image("pic.jpg")
                .Text("通知2")
                .send_all())                 # 一括実行
# results = [Textの結果, Imageの結果, Textの結果]
```

`.send_all()` はデフォルトで**並列**に実行されます（並行送信、効率が高い）。メッセージの到達順序を保証する必要がある場合は、`.Sequential()` を呼び出して逐次実行します：

```python
# 逐次実行（順序を保証）+ 失敗リトライ
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # 順に送信
       .Retry(2)                     # 失敗した項目は個別にリトライ
       .Text("1番目のメッセージ").Text("2番目のメッセージ")
       .send_all())
```

バッチ実行は**失敗しても継続**する戦略を採用しています：1つのメッセージが失敗しても他のメッセージの送信を中断せず、失敗した項目は自動的にリトライされます。バッチ送信にも全体の `Hook`（すべて成功後に発動）、`OnError`（失敗があった場合に発動）、`OnProgress`（進行状況コールバック）がサポートされています。

> より詳細なルールとバッチ構築の説明は [SendDSL 詳解](../developer-guide/adapters/send-dsl.md) を参照してください。

### イベントのリッスン
3種類のイベントリッスン方法があります：

1. プラットフォーム固有のイベントリッスン：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"受信した{AdapterName}プラットフォーム固有のイベント: {data}")
   ```

2. OneBot12標準イベントリッスン：
   ```python
   from ErisPulse.Core import adapter, logger

   # OneBot12標準イベントをリッスン
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"受信した標準イベント: {data}")

   # 特定プラットフォームの標準イベントをリッスン
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"受信した{AdapterName}標準イベント: {data}")
   ```

3. Eventモジュールによるリッスン：
    `Event`のイベントは `adapter.on()` 関数に基づいているため、`Event`が提供するイベント形式はOneBot12標準イベントです

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="挨拶メッセージを送信", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"受信したメッセージ: {event}")
    async def notice_handler(event):
        logger.info(f"受信した通知: {event}")
    async def request_handler(event):
        logger.info(f"受信したリクエスト: {event}")
    async def command_handler(event):
        logger.info(f"受信したコマンド: {event}")
    ```

この中で、最も推奨されるのは `Event` モジュールを使用したイベント処理です。`Event` モジュールは豊富なイベントタイプとイベント処理メソッドを提供するためです。

---

## 標準フォーマット
参考の便宜上、ここでは簡易なイベントフォーマットを示します。詳細情報が必要な場合は、上記のリンクを参照してください。

> **注意:** 以下のフォーマットは基本的な OneBot12 標準フォーマットであり、各アダプターはこの上に拡張フィールドを追加する可能性があります。具体的な内容は、各アダプターの特定機能の説明を参照してください。

### 標準イベントフォーマット
すべてのアダプターが実装しなければならないイベント変換フォーマット：
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
    {"type": "text", "data": {"text": "こんにちは"}}
  ],
  "alt_message": "こんにちは",
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
  "message": "必要なパラメータが不足しています",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## 貢献について

私たちは、より多くの開発者の皆様にアダプターのドキュメントの作成と維持にご参加いただきたいと考えています！以下の手順に従って貢献を提出してください：
1. [ErisPuls](https://github.com/ErisPulse/ErisPulse) リポジトリをForkしてください。
2. `docs/platform-features/` ディレクトリ内にMarkdownファイルを作成し、`<プラットフォーム名>.md` の形式で命名してください。
3. 本 `README.md` ファイルに、ご貢献のアダプターへのリンクと関連する公式ドキュメントを追加してください。
4. Pull Requestを提出してください。

皆様のご支援に感謝いたします！

