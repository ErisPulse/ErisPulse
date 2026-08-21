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

## 初期化プロセス

下図は `sdk.init()` の完全な初期化プロセスを示しています：

```mermaid
flowchart TD
    A["sdk.init()"] --> B["実行環境の準備"]
    B --> B1["設定ファイルの読み込み"]
    B1 --> B2["グローバル例外処理の設定"]
    B2 --> C["アダプタ & モジュールの発見"]
    C --> D{"並列ロード"}
    D --> D1["PyPIからアダプタのロード"]
    D --> D2["PyPIからモジュールのロード"]
    D1 & D2 --> E["アダプタの登録"]
    E --> E1["アダプタの起動"]
    E1 --> F["モジュールの登録"]
    F --> F1{"依存関係の検証"}
    F1 -->|"依存関係が不足"| F2["該当モジュールをスキップし、警告を記録"]
    F1 -->|"依存関係が満たされている"| F3["トポロジカルソート<br/>（Kahnアルゴリズム + 優先度）"]
    F3 --> G["順序に従ってモジュールを初期化<br/>（インスタンス化 + on_load）"]
    F2 --> G
    G --> H["ルーティングサーバーの起動"]
    H --> K["実行準備完了"]
```

### 初期化段階の詳細

> 完全な初期化フローの分解（Finder / Loader / Manager / Router）、下層エントリポイント（`init()` / `init_task()` / `init_sync()`）および手動での完全起動については [起動プロセスと手動制御](advanced/startup.md) を参照してください。

## イベント処理フロー

下図は、メッセージがプラットフォームからハンドラへと流れる完全な経路を示しています：

```mermaid
flowchart LR
    A["プラットフォームの元のメッセージ"] --> B["アダプタ受信"]
    B --> C["OneBot12 標準に変換"]
    C --> D["adapter.emit()"]
    D --> E["ミドルウェアチェーンの実行"]
    E --> F{"イベント配信"}
    F --> G1["command<br/>コマンドハンドラ"]
    F --> G2["message<br/>メッセージハンドラ"]
    F --> G3["notice<br/>通知ハンドラ"]
    F --> G4["request<br/>リクエストハンドラ"]
    F --> G5["meta<br/>メタイベントハンドラ"]
    G1 & G2 & G3 & G4 & G5 --> H["ハンドラのコールバック実行"]
    H --> I["event.reply()<br/>SendDSL による返信"]
    I --> J["アダプタがプラットフォームに送信"]
```

### イベント処理の詳細な流れ

上記の図は「結果」です。以下は `adapter.emit()` を分解した後、フレームワークが**背景で何を行っているか**を示すものです。これは3層に分かれた配信の流れです：

```mermaid
sequenceDiagram
    participant P as プラットフォーム
    participant A as アダプタバス層<br/>AdapterManager.emit
    participant T as ハンドラ Task 層<br/>_dispatch_handler_task
    participant E as Event モジュール層<br/>_process_event

    P->>A: ネイティブイベント
    A->>A: platform/type/detail_type + 元のフィールドの抽出
    A->>A: [Recv] 受信ログ
    A->>A: lifecycle.adapter.event.receive（初期のフック）
    A->>A: self フィールドの処理（meta 分岐 / Bot の自動登録）
    A->>A: ミドルウェアチェーン（シーケンシャル、イベントデータの変更可）
    A->>A: handler の収集（具体的なタイプ + ワイルドカード *）
    A->>A: スコープフィルタリング（Task の作成前に、静かにスキップ）
    A->>T: asyncio.create_task（fire-and-forget）
    A->>A: lifecycle.adapter.event.dispatched（最後のフック）
    T->>T: 並行処理のシグナルマネージャーの取得（デフォルト上限 64）
    T->>E: Event モジュールに登録されたハンドラの呼び出し
    E->>E: lifecycle.event.pre_process
    E->>E: ignore_self（メッセージイベントではデフォルトで自身を無視）
    E->>E: 優先度順にグループ化：高→低、グループ間はシーケンシャル、グループ内は並行
    E->>E: グループ内のコピーを実行 + フィールドのマージ（競合警告）
    E->>E: グループ後の stop() 検査で、より低い優先度をブロック
    T->>T: スローなログ（1秒以上かかると警告、wait_reply 時間は除外）
```

**フレームワークが何を行ったか、そしてあなたが何を介入できるか：**

| 階段 | フレームワークが何を行ったか | 介入できる内容 |
|------|-------------|-----------|
| 受信 | 標準フィールドの抽出、`{platform}_raw` の元データの保持；`[Recv]` ログの記録 | `adapter.event.receive` を監視して初期のイベントを取得 |
| self フィールド | meta イベントは connect/disconnect/heartbeat 分岐を経る；通常のイベントは Bot を自動登録し、`adapter.bot.online` をトリガー | `adapter.bot.online` / `bot.offline` を監視 |
| ミドルウェア | **シーケンシャル**に実行、戻り値が None でなければイベントデータを置き換え | ミドルウェアを登録してイベントを変更/ブロック |
| 分配・収集 | 先に具体的なタイプの handler を取り、次に `*` ワイルドカードの handler を取り | — |
| スコープフィルタリング | owner に基づいて `scope.is_allowed` を判定（セッションレベル > Bot レベル > プラットフォームレベル）、**不正な場合は静かにスキップ** | スコープのホワイトリスト/ブラックリストを設定 |
| スケジューリング | 各マッチする handler に独立した `asyncio.Task` を作成、`emit()` は **handler の完了を待たずに即座に返却** | — |
| 優先度 | 高優先度のグループが先に実行、**グループ間はシーケンシャル、グループ内は並行**（グループ内では各 handler がイベントのコピーを持ち、フィールドを変更して元のイベントにマージ、競合時は WARNING を出力） | `@command(..., priority=N)` / 登録時に priority を指定 |
| ブロック | 各グループの処理後に `event.is_stopped()` をチェックし、一致すれば**より低い優先度を実行しない** | `event.mark_processed(stop=True)` / `event.done()` |

> **よくある誤解**：
> 1. **スコープフィルタリングは静かに**——遮断された handler はエラーも返答もせず、TRACE レベルのログ（`core.scope.denied`）にのみ表示されます。「自分のモジュールがメッセージを受け取っていない」場合は、まずスコープのバインドを確認してください。
> 2. **handler は天然に並行**——フレームワークは各 handler に独立した Task を作成しているので、**自分で `asyncio.create_task` をラップする必要はありません**。
> 3. **同じ優先度のグループ内ではブロックしない**——`mark_processed(stop=True)` は、より低い優先度のグループをブロックするだけで、同じグループ内の既に並行実行中の handler は途中で中断されません。
> 4. **スローなログの閾値は固定の1秒**——ハンドラの処理時間が1秒を超えると、ログに WARNING が出力されます（`wait_reply` の待機時間は処理時間から除外されていますが、実行は中断されません）。

> スコープの3段階のバインドと優先度の詳細は [スコープシステム](advanced/scope.md) を参照してください。claim/ブロックの完全な意味は [イベント処理の入門](getting-started/event-handling.md) を参照してください。並行処理の上限の設定は [設定ガイド](user-guide/configuration.md#フレームワーク設定) を参照してください。

## ライフサイクルイベント

下図は、フレームワークの各コンポーネントがライフサイクルイベントをどのように発生させるかを示しています：

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

### ライフサイクルイベントの監視

> 完全なイベント監視メソッド（`lifecycle.on()` / `once()` / `has_handlers()`）、すべてのライフサイクルイベントリストとデータ形式は [ライフサイクル管理](advanced/lifecycle.md) を参照してください。

## モジュールのロード戦略

ErisPulse は、`get_load_strategy()` が返す `ModuleLoadStrategy` によって宣言される 3 つのモジュールロード戦略をサポートしています：

```mermaid
flowchart TD
    A["モジュールが ModuleManager に登録"] --> B{"ロード戦略"}
    B -->|"lazy_load = true<br/>+ activate_on 声明"| C["ModuleActivator 代理を作成"]
    B -->|"lazy_load = true<br/>activate_on なし"| D["LazyModule 代理を作成"]
    B -->|"lazy_load = false"| E["即時インスタンスを作成"]
    C --> F["イベント/コマンド stub をディスパッチャに登録"]
    F --> G["sdk 属性にマウント"]
    G --> H["イベントが到達すると活性化がトリガー"]
    H --> I["インスタンス化 + on_load() + stub の登録解除"]
    D --> J["sdk 属性にマウント"]
    J --> K["最初の属性アクセス時に初期化"]
    E --> L["on_load() を呼び出す"]
    L --> M["sdk 属性にマウント"]
```

> 詳細については、[遅延ロードシステム](advanced/lazy-loading.md)、[ライフサイクル管理](advanced/lifecycle.md) およびモジュールのドキュメントを参照してください。

### イベント駆動の遅延活性化（`activate_on`）トリガー構造

> [!NOTE]
> この機能には ErisPulse **2.8.0+** が必要です。

`activate_on` により、モジュールは**最初の一致するイベント/コマンドが到達した時点で**のみロードされるようになり、メモリ常駐を回避しながら、イベントのロスを防ぐことができます：

```mermaid
flowchart LR
    subgraph Declare["モジュールの宣言"]
        S1["get_load_strategy() が<br/>ModuleLoadStrategy(activate_on=...) を返す"] --> S2["activate_on 構文：<br/>str / dict / list を自由に混合"]
        S2 --> S2a["'message' → イベントタイプレベル"]
        S2 --> S2b["{'notice': 'group_member_increase'}<br/>→ タイプ + detail_type"]
        S2 --> S2c["{'command': 'roll'}<br/>→ コマンドトリガー（省略形/リスト）"]
        S2 --> S2d["{'command': {'name': 'dice', 'help': ...,<br/>'aliases': [...], 'hidden': ...}}<br/>→ コマンドトリガー（dict 声明）"]
    end

    subgraph Runtime["実行時"]
        R1["ModuleActivator が stub を登録"] --> R1a["イベント stub → message/notice/request/meta マネージャー<br/>優先度 ACTIVATION_STUB_PRIORITY（極めて低い）"]
        R1 --> R1b["コマンド stub → コマンドマネージャー<br/>プレースホルダーコマンド（dict 声明の help/usage/group/aliases/hidden を反映）"]
        R1a --> R2{"トリガーイベントが到達"}
        R1b --> R2
        R2 --> R3["owner によるスコープフィルタリング"]
        R3 --> R4["asyncio.Lock で重複活性化を防止"]
        R4 --> R5["モジュールのインスタンス化 + on_load() の呼び出し"]
        R5 --> R6["すべての stub の登録解除"]
        R6 --> R7["イベントを実際のハンドラに転送"]
    end

    Declare --> Runtime
```

**トリガーの意味要点：**

> 完全な `activate_on` 構文（str / dict / list）、コマンド dict 声明、プレースホルダーコマンドの help フォールバックチェーン、スコープフィルタリング、および失敗時の意味については、[遅延ロードシステム](advanced/lazy-loading.md#イベント駆動の遅延活性化activate_on) を参照してください。

## ローカルプラグインフォルダのアーキテクチャ

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

ローカルプラグイン（`plugins/` 目录）はパッケージ化して公開する必要がなく、フレームワークの起動時に自動的に発見・ロードされます：

```mermaid
flowchart TD
    A["プロジェクトの plugins/ 目录<br/>（ErisPulse.framework.plugins_dir、複数目录をサポート）"] --> B{"PluginFolderLoader.discover()"}
    B --> C["単一ファイル：dice.py → プラグイン名 = ファイル名"]
    B --> D["パッケージ形式：weather/（含 __init__.py）→ プラグイン名 = 目录名"]
    B --> E["無視対象：__pycache__ / _ で始まる / .py でない / __init__.py が存在しない目录"]
    C --> F["モジュールのインポート（spec_from_file_location）"]
    D --> G["モジュールのインポート（sys.path + import_module）"]
    F --> H["モジュールクラスの識別：Main（BaseModule の子クラス）を優先し、存在しない場合は最初の子クラス"]
    G --> H
    H --> I["entry-point と一致する moduleInfo を構築"]
    I --> J["ModuleLoader.load() で統合<br/>ローカルのモジュールが PyPI に同名のインストールパッケージを上書き"]
    J --> K["インストールパッケージのモジュールと共有：<br/>有効状態 / スコープ / meta / i18n / コンテキスト"]
```

**規約と特性：**

- プラグイン名の取得方法：単一ファイルはファイル名、パッケージ形式は目录名
- ローカルプラグインの `moduleInfo.meta.source == "plugin_folder"` であり、PyPI でインストールされたパッケージモジュールとシームレスに共存
- 同名のモジュールがある場合、ローカルのモジュールが優先（ローカルでの上書きデバッグが可能）、無効化された場合、同名の entry-point 条目も同時に削除

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