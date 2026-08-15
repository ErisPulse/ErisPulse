# アーキテクチャ概要

このドキュメントでは、ErisPulse SDK の技術的アーキテクチャを視覚的なチャートを用いて紹介し、フレームワークの設計思想とモジュール間の関係をすばやく理解できるようにします。

docs/ja/quick-start.md

## SDK 核心アーキテクチャ

下図は、SDK のコアモジュールの構成とその関係を示しています：

```mermaid
graph TB
    SDK["sdk<br/>統一エントリーポイント"]

    SDK --> Event["Event<br/>イベントシステム"]
    SDK --> Lifecycle["Lifecycle<br/>ライフサイクル管理"]
    SDK --> Logger["Logger<br/>ログ管理"]
    SDK --> Storage["Storage / env<br/>ストレージ管理"]
    SDK --> Config["Config<br/>設定管理"]
    SDK --> AdapterMgr["Adapter<br/>アダプタ管理"]
    SDK --> ModuleMgr["Module<br/>モジュール管理"]
    SDK --> Router["Router<br/>ルーティング管理"]
    SDK --> Client["HttpClient<br/>HTTP クライアント"]
    Event --> Command["command"]
    Event --> Message["message"]
    Event --> Notice["notice"]
    Event --> Request["request"]
    Event --> Meta["meta"]
    Event --> Conversation["Conversation<br/>分岐 + 永続化"]

    AdapterMgr --> BaseAdapter["BaseAdapter"]
    BaseAdapter --> P1["雲湖"]
    BaseAdapter --> P2["Telegram"]
    BaseAdapter --> P3["OneBot11/12"]
    BaseAdapter --> PN["..."]

    ModuleMgr --> BaseModule["BaseModule"]
    BaseModule --> CM["カスタムモジュール"]

    BaseAdapter -.-> SendDSL["SendDSL<br/>メッセージ送信"]
```

### コアモジュールの説明

| モジュール | 説明 |
|------|------|
| **Event** | イベントシステム。command / message / notice / request / meta の5種類のイベント処理と、Conversation 多段対話機能を提供します。|
| **Adapter** | アダプタマネージャー。複数プラットフォーム用アダプタの登録、起動、停止を管理します。|
| **Module** | モジュールマネージャー。プラグインの登録、ロード、アンロードを管理し、依存関係の宣言とトポロジカルソートをサポートします。|
| **Lifecycle** | ライフサイクルマネージャー。イベント駆動型のライフサイクルフックを提供します。|
| **Storage** | SQLite に基づくキーバリューストレージシステム。一般的な SQL チェーンクエリをサポートします。|
| **Config** | TOML 形式の設定ファイル管理。|
| **Logger** | モジュール化されたログシステム。サブロガーをサポートします。|
| **Router** | HTTP/WebSocket ルーティング管理。抽象層を介して下位のバックエンド（現在は FastAPI + Uvicorn）をラップし、デコレーターベースのルーティング、ミドルウェア、グループ化、リクエスト制限、CORS をサポートします。|
| **HttpClient** | 統一された HTTP/WS クライアント。抽象層を介して下位のリクエストライブラリ（現在は aiohttp）をラップし、リクエスト統計、リトライ、ログ、WebSocket クライアント、ErisPulse 例外体系などの機能を提供します。クライアントとサーバーの WebSocket は `WebSocketConnectionBase` 基底クラスを共有します。|

## 初期化フロー

下図は `sdk.init()` の完全な初期化プロセスを示しています：

```mermaid
flowchart TD
    A["sdk.init()"] --> B["実行環境の準備"]
    B --> B1["設定ファイルのロード"]
    B1 --> B2["グローバル例外処理の設定"]
    B2 --> C["アダプタ & モジュールの発見"]
    C --> D{"並列ロード"}
    D --> D1["PyPI からアダプタをロード"]
    D --> D2["PyPI からモジュールをロード"]
    D1 & D2 --> E["アダプタの登録"]
    E --> E1["アダプタの起動"]
    E1 --> F["モジュールの登録"]
    F --> F1{"依存関係の検証"}
    F1 -->|"依存が不足"| F2["モジュールをスキップして警告を記録"]
    F1 -->|"依存が満たされている"| F3["トポロジカルソート<br/>（Kahn アルゴリズム + 優先度）"]
    F3 --> G["順序に従ってモジュールを初期化<br/>（インスタンス化 + on_load）"]
    F2 --> G
    G --> H["ルーティングサーバーの起動"]
    H --> K["実行準備完了"]
```

### 初期化フェーズの詳細

1. **環境準備** - TOML 設定ファイルをロードし、グローバル例外処理を設定
2. **並行発見** - 既にインストールされた PyPI パッケージから同時にアダプタとモジュールを発見
3. **アダプタの登録** - 発見されたアダプタをアダプタマネージャーに登録
4. **アダプタの起動** - 各プラットフォームのアダプタを非同期で起動（モジュールの初期化前に、モジュールが即座にメッセージを送信できるようにする）
5. **モジュールの登録** - 発見されたモジュールをモジュールマネージャーに登録
6. **依存関係の検証** - モジュールが宣言した `depends` 依存が登録されているかを確認し、不足している依存を持つモジュールはスキップ
7. **トポロジカルソート** - Kahn アルゴリズムを使用して依存関係に基づいてモジュールのロード順序をソートし、同レベルでは `priority` で降順に並べる
8. **モジュールの初期化** - ソート順に従ってモジュールのインスタンスを作成し、`on_load` ライフサイクルメソッドを呼び出す
9. **ルーティングサーバーの起動** - Uvicorn を使用して FastAPI ルーティングサーバーを起動

[**English**](docs/en/quick-start.md) | [**中文**](docs/ja/quick-start.md) | [**日本語**](docs/ja/quick-start.md)

## イベント処理フロー

下図は、メッセージがプラットフォームからハンドラへと流れる完全なフローを示しています：

```mermaid
flowchart LR
    A["プラットフォームの元のメッセージ"] --> B["アダプタが受信"]
    B --> C["OneBot12 標準に変換"]
    C --> D["adapter.emit()"]
    D --> E["ミドルウェアチェーンを実行"]
    E --> F{"イベント配信"}
    F --> G1["command<br/>コマンドハンドラ"]
    F --> G2["message<br/>メッセージハンドラ"]
    F --> G3["notice<br/>通知ハンドラ"]
    F --> G4["request<br/>リクエストハンドラ"]
    F --> G5["meta<br/>メタイベントハンドラ"]
    G1 & G2 & G3 & G4 & G5 --> H["ハンドラのコールバック実行"]
    H --> I["event.reply()<br/>SendDSL で返信"]
    I --> J["アダプタがプラットフォームに送信"]
```

### イベント処理の重要なステップ

- **アダプタが受信** - 各プラットフォームのアダプタは WebSocket/Webhook などの方法でネイティブイベントを受信します。
- **OB12 標準化** - プラットフォームのネイティブイベントを統一された OneBot12 標準フォーマットに変換します。
- **ミドルウェア処理** - 登録されたミドルウェア関数を順次実行し、イベントデータを変更できます。
- **イベント配信** - イベントの種類（message/notice/request/meta）に応じて、対応するハンドラに配信します。
- **SendDSL で返信** - ハンドラは `event.reply()` または `SendDSL` のチェーン呼び出しを使って返信を送信します。

## ライフサイクルイベント

下図は、フレームワークの各コンポーネントのライフサイクルイベントの発生順序を示しています：

```mermaid
flowchart LR
    subgraph Core["コア"]
        direction LR
        C1["core.init.start"] --> C2["core.init.complete"]
    end

    subgraph AdapterLife["アダプタ"]
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

### ライフサイクルイベントの監視

これらのイベントを `lifecycle.on()` を使って監視し、カスタムロジックを実行することができます：

```python
from ErisPulse import sdk

# すべてのアダプタイベントを監視
@sdk.lifecycle.on("adapter")
async def on_adapter_event(event_data):
    print(f"アダプタイベント: {event_data}")

# モジュールのロード完了を監視
@sdk.lifecycle.on("module.load")
async def on_module_loaded(event_data):
    print(f"モジュールがロードされました: {event_data}")

# Botのオンラインを監視
@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(event_data):
    print(f"Botがオンラインになりました: {event_data}")

## モジュールロード戦略

ErisPulse は、`get_load_strategy()` が返す `ModuleLoadStrategy` によって宣言される 3 つのモジュールロード戦略をサポートしています：

```mermaid
flowchart TD
    A["モジュールが ModuleManager に登録"] --> B{"ロード戦略"}
    B -->|"lazy_load = true<br/>+ activate_on が宣言されている"| C["ModuleActivator 代理を作成"]
    B -->|"lazy_load = true<br/>activate_on が宣言されていない"| D["LazyModule 代理を作成"]
    B -->|"lazy_load = false"| E["即時インスタンス作成"]
    C --> F["イベント/コマンド stub をディスパッチャに登録"]
    F --> G["sdk 属性にマウント"]
    G --> H["イベントが到達してアクティベーションをトリガー"]
    H --> I["インスタンス化 + on_load() + stub の登録解除"]
    D --> J["sdk 属性にマウント"]
    J --> K["最初の属性アクセス時に初期化"]
    E --> L["on_load() を呼び出す"]
    L --> M["sdk 属性にマウント"]
```

> 詳細は [遅延ロードシステム](advanced/lazy-loading.md)、[ライフサイクル管理](advanced/lifecycle.md) およびモジュールドキュメントを参照してください。

### イベント駆動遅延アクティベーション（`activate_on`）トリガー構造

`activate_on` は、モジュールが**最初の一致するイベント/コマンドが到達したときにのみ**ロードされるようにし、常駐メモリを避けると同時にイベントのロスを防ぎます：

```mermaid
flowchart LR
    subgraph Declare["モジュール宣言"]
        S1["get_load_strategy() が<br/>ModuleLoadStrategy(activate_on=...) を返す"] --> S2["activate_on 構文：<br/>str / dict / list を自由に混合"]
        S2 --> S2a["'message' → イベントタイプレベル"]
        S2 --> S2b["{'notice': 'group_member_increase'}<br/>→ タイプ + detail_type"]
        S2 --> S2c["{'command': 'roll'}<br/>→ コマンドトリガー"]
    end

    subgraph Runtime["実行時"]
        R1["ModuleActivator が stub を登録"] --> R1a["イベント stub → message/notice/request/meta マネージャー<br/>優先度 ACTIVATION_STUB_PRIORITY（極めて低い）"]
        R1 --> R1b["コマンド stub → コマンドマネージャー<br/>隠しプレースホルダコマンド（hidden=True）"]
        R1a --> R2{"トリガーイベントが到達"}
        R1b --> R2
        R2 --> R3["owner に基づくスコープフィルタリング"]
        R3 --> R4["asyncio.Lock で重複アクティベーションを防止"]
        R4 --> R5["モジュールのインスタンス化 + on_load() の呼び出し"]
        R5 --> R6["すべての stub の登録解除"]
        R6 --> R7["イベントを真のハンドラに転送"]
    end

    Declare --> Runtime
```

**トリガーの意味要点：**

1. **stub 登録**：イベント stub は、対応するイベントマネージャーに極めて低い優先度（`ACTIVATION_STUB_PRIORITY`）で登録され、同種のイベントのすべての通常のハンドラの**後に**実行されるようにします。コマンド stub は隠しプレースホルダコマンドとして登録され、コマンドリストを汚染しません。
2. **スコープフィルタリング**：stub にはモジュールの owner 身分が付与され、該当する Bot / セッション / プラットフォームに対して有効でないモジュールはトリガーされません。
3. **再入防止**：`asyncio.Lock` により、並行イベント下でも一度だけアクティベーションされるようにします。
4. **イベント転送**：アクティベーション完了後、現在のイベントは真のハンドラに転送されます（外側のグループループは、stub の後に登録されたハンドラが二度処理されないことを既に検証済みです）。
5. **失敗時の意味**：アクティベーションが失敗した場合、再試行は行われず、stub も同時に登録解除され、毎回イベントに対して繰り返し試行されるのを防ぎます。

## ローカルプラグインフォルダの構造

ローカルプラグイン（`plugins/` ディレクトリ）は、パッケージ化して配布する必要がなく、フレームワークの起動時に自動的に発見され読み込まれます：

```mermaid
flowchart TD
    A["プロジェクトの plugins/ ディレクトリ<br/>（ErisPulse.framework.plugins_dir、複数ディレクトリ対応）"] --> B{"PluginFolderLoader.discover()"}
    B --> C["単一ファイル：dice.py → プラグイン名 = ファイル名"]
    B --> D["パッケージ形式：weather/（__init__.py あり）→ プラグイン名 = ディレクトリ名"]
    B --> E["無視対象：__pycache__ / _ で始まる / .py でない / __init__.py がないディレクトリ"]
    C --> F["モジュールのインポート（spec_from_file_location）"]
    D --> G["モジュールのインポート（sys.path + import_module）"]
    F --> H["モジュールクラスの識別：Main（BaseModule のサブクラス）を優先し、存在しない場合は最初のサブクラス"]
    G --> H
    H --> I["entry-point と同じ moduleInfo を構築"]
    I --> J["ModuleLoader.load() によるマージ<br/>ローカルのモジュールが PyPI の同名インストールパッケージを上書き"]
    J --> K["インストールパッケージモジュールと共有：<br/>有効状態 / スコープ / meta / i18n / コンテキスト"]
```

**規約と特徴：**

- プラグイン名の取得方法：単一ファイルはファイル名、パッケージ形式はディレクトリ名
- ローカルプラグインの `moduleInfo.meta.source == "plugin_folder"` であり、PyPI でインストールされたパッケージモジュールとシームレスに共存
- 同名のモジュールが存在する場合、ローカルのモジュールが優先（ローカルの上書きやデバッグに便利）、無効化された場合、同名の entry-point 条目も同時に削除

[**English**](docs/ja/quick-start.md)

## ローカルプラグインのホットリロードアーキテクチャ

ホットリロードはプラグインファイルの変更を監視し、対応するプラグインを自動的に再読み込みします：

```mermaid
flowchart TD
    A["sdk.enable_plugin_hot_reload()"] --> B["PluginReloadWatcher の起動"]
    B --> C["PollingObserver（バックグラウンドのデーモンスレッド）<br/>定期的に .py ファイルの mtime を比較"]
    C --> D{"プラグインファイルの変更"}
    D --> E["変更のデューディレイ（デフォルト 1 秒）"]
    E --> F["_handle_change でプラグイン名を解析<br/>（単一ファイル / パッケージ形式）"]
    F --> G["asyncio.run_coroutine_threadsafe<br/>メインイベントループへのスケジューリング"]
    G --> H["sdk.reload_plugin(name)"]
    H --> I["古いインスタンスのアンロード（on_unload をトリガー）"]
    I --> J["登録のクリーンアップ（unregister + sdk 属性の削除）"]
    J --> K["sys.modules のクリーンアップで強制的に再インポート"]
    K --> L["再発見 + 再登録 + 再読み込み"]
    L --> M["新しいインスタンスを sdk 属性にマウント"]
    M --> N["ファイルの削除 → 読み込み結果から自動的に削除"]
```

[**English**](docs/ja/quick-start.md)