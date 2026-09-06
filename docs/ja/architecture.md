# アーキテクチャ概要

このドキュメントでは、ErisPulse SDK の技術的アーキテクチャを視覚的なチャートを用いて紹介し、フレームワークの設計思想とモジュール間の関係をすばやく理解できるようにします。

docs/ja/quick-start.md

## SDKのコアアーキテクチャ

下図は、SDKのコアモジュール構成とその関係を示しています：

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
    SDK --> Client["Client<br/>HTTPクライアント"]
    Event --> Command["command"]
    Event --> Message["message"]
    Event --> Notice["notice"]
    Event --> Request["request"]
    Event --> Meta["meta"]
    Event --> Conversation["Conversation<br/>分岐 + 永続化"]

    AdapterMgr --> BaseAdapter["BaseAdapter"]
    BaseAdapter --> P1["云湖"]
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
| **Event** | イベントシステム。command / message / notice / request / meta の5種類のイベント処理と、Conversationによる多段対話機能を提供します。|
| **Adapter** | アダプタマネージャー。複数プラットフォームのアダプタの登録、起動、停止を管理します。|
| **Module** | モジュールマネージャー。プラグインの登録、ロード、アンロードを管理し、依存関係の宣言とトポロジカルソートをサポートします。|
| **Lifecycle** | ライフサイクルマネージャー。イベント駆動型のライフサイクルフックを提供します。|
| **Storage** | SQLiteベースのキーバリューストレージシステム。一般的なSQLチェーンクエリをサポートします。|
| **Config** | TOML形式の設定ファイル管理。|
| **Logger** | モジュール化されたログシステム。サブロガーをサポートします。|
| **Router** | HTTP/WebSocketルーティング管理。抽象層を介して下位のバックエンド（現在はFastAPI + Uvicorn）をラップし、デコレーターベースのルーティング、ミドルウェア、グループ化、リクエスト制限、CORSをサポートします。|
| **Client** | 統一HTTP/WSクライアント（2.8.0以前は`HttpClient`、互換性のため別名を保持）。抽象層を介して下位のリクエストライブラリ（現在はaiohttp）をラップし、リクエスト統計、リトライ、ログ、WebSocketクライアント、ErisPulse例外体系などの機能を提供します。クライアントとサーバーのWebSocketは`WebSocketConnectionBase`基底クラスを共有します。|

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

下の図は、プラットフォームからハンドラへのメッセージの完全な転送経路を示しています：

```mermaid
flowchart LR
    A["プラットフォームの元のメッセージ"] --> B["アダプタが受信"]
    B --> C["OneBot12 標準に変換"]
    C --> D["adapter.emit()"]
    D --> E["ミドルウェアチェーンの実行"]
    E --> F{"イベントの配信"}
    F --> G1["command<br/>コマンドハンドラ"]
    F --> G2["message<br/>メッセージハンドラ"]
    F --> G3["notice<br/>通知ハンドラ"]
    F --> G4["request<br/>リクエストハンドラ"]
    F --> G5["meta<br/>メタイベントハンドラ"]
    G1 & G2 & G3 & G4 & G5 --> H["ハンドラのコールバック実行"]
    H --> I["event.reply()<br/>SendDSL で返信"]
    I --> J["アダプタがプラットフォームに送信"]
```

### イベント処理チェーンの詳細

上記の図は「結果」です。下に `adapter.emit()` を分解すると、フレームワークが**背後で何をしているか**がわかります。これは3層に分かれた配信チェーンです：

```mermaid
sequenceDiagram
    participant P as プラットフォーム
    participant A as アダプタバス層<br/>AdapterManager.emit
    participant T as ハンドラ Task 層<br/>_dispatch_handler_task
    participant E as Event モジュール層<br/>_process_event

    P->>A: ネイティブイベント
    A->>A: platform/type/detail_type + 原始フィールドの抽出
    A->>A: [Recv] 受信ログ
    A->>A: lifecycle.adapter.event.receive（初期のフック）
    A->>A: self フィールドの処理（meta 分岐 / Bot 自動登録）
    A->>A: ミドルウェアチェーン（シリアル、イベントデータを変更可能）
    A->>A: handler の収集（具体的なタイプ + ワイルドカード *）
    A->>A: 身元認証 + スコープフィルタリング（Task の作成前に、無視/スキップ）
    A->>T: asyncio.create_task（fire-and-forget）
    A->>A: lifecycle.adapter.event.dispatched（最終のフック）
    T->>T: 並行信号量の取得（デフォルト上限 64）
    T->>E: Event モジュールに登録されたハンドラを呼び出す
    E->>E: lifecycle.event.pre_process
    E->>E: ignore_self（メッセージイベントではデフォルトで自身を無視）
    E->>E: 優先度順にグループ化：高→低、グループ間はシリアル、グループ内は並行
    E->>E: グループ内のコピーを実行 + フィールドのマージ（衝突時は警告）
    E->>E: グループ後、stop() でチェックし、より低い優先度をブロック
    T->>T: 遅いログ（1秒以上かかる場合は警告、wait_reply 時間は除外）
```

**フレームワークが何をし、あなたが介入できるか：**

| 階段 | フレームワークが何をしたか | 介入できるか |
|------|-------------|-----------|
| 受信 | 標準フィールドの抽出、`{platform}_raw` の元データの保持；`[Recv]` ログの書き込み | `adapter.event.receive` を監視して初期イベントを取得 |
| self フィールド | meta イベントは connect/disconnect/heartbeat 分岐；通常のイベントは Bot の自動登録と `adapter.bot.online` のトリガー | `adapter.bot.online` / `bot.offline` を監視 |
| ミドルウェア | **シリアル**に実行し、戻り値が None でなければイベントデータを置換 | ミドルウェアを登録してイベントを変更/ブロック |
| 分配収集 | 先に具体的なタイプの handler を取得し、次に `*` ワイルドカード handler を取得 | — |
| 身元次元 | 分配入口はユーザー>会話>Bot>アダプタの順に判定し、`scope.is_identity_allowed` でイベントを受け取るかを判断し、**拒否された場合はイベント全体を破棄** | `ErisPulse.scope.identity` をバインド |
| スコープフィルタリング | モジュールの所有者に基づいて `scope.is_allowed` を判定（会話レベル>Botレベル>プラットフォームレベル）、**不通過の場合は静かにスキップ** | スコープのホワイトリスト/ブラックリストを設定 |
| スケジューリング | 各マッチする handler に独立した `asyncio.Task` を作成し、`emit()` は handler の完了を待たずに即座に返却 | — |
| 優先度 | 高優先度のグループが先に実行される；**グループ間はシリアル、グループ内は並行**（グループ内の各 handler はイベントのコピーを持ち、フィールドの変更をマージし、衝突時は WARNING を出力） | `@command(..., priority=N)` / 登録時に priority を指定 |
| ブロッキング | 各グループの処理後、`event.is_stopped()` をチェックし、一致した場合は**より低い優先度を実行しない** | `event.mark_processed(stop=True)` / `event.done()` |

> **よくある誤解**：
> 1. **スコープフィルタリングは静かに無視される**——遮断された handler はエラーも返信もせず、TRACE レベルのログ（`core.scope.denied`）にのみ表示される。「私のモジュールがメッセージを受け取っていない」場合は、まずスコープのバインディングを確認。
> 2. **handler は天然に並行実行される**——フレームワークは各 handler に独立した Task を作成しており、**自分で `asyncio.create_task` をラップする必要はない**。
> 3. **同じ優先度のグループ内はブロックされない**——`mark_processed(stop=True)` はより低い優先度のグループをブロックするだけで、同じグループ内で並行実行中の handler は途中で中断されない。
> 4. **遅いログの閾値は固定で1秒**——ハンドラの処理時間が1秒を超えるとログに WARNING を出力する（`wait_reply` の待ち時間は処理時間から除外される）が、実行は中断されない。

> スコープ（scope）のモジュール次元の3段階バインディング、身元認証と出力アクションの制限の詳細は [スコープ（scope）](advanced/scope.md) を参照。イベントスコープのテキストフィルタリングとコマンドユーザー ACL は [イベント処理入門](getting-started/event-handling.md) を参照。並行上限の設定は [設定ガイド](user-guide/configuration.md#フレームワーク設定) を参照。

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

## モジュールのホットリロードアーキテクチャ

ホットリロードは**すべてのモジュールのソース**に対して一貫しています：ローカルプラグインはファイルの変更を監視して自動的にトリガーされ、任意のモジュールは `sdk.reload_module()` / `sdk.module.reload()` を使って手動でリロードできます（pip でインストールされた PyPI パッケージモジュールは pip によるアップグレード後に呼び出すだけで有効になります）：

```mermaid
flowchart TD
    A["sdk.enable_plugin_hot_reload()<br/>（自動監視、ローカルプラグインディレクトリのみ）"] --> B["PluginReloadWatcher を起動"]
    B --> C["PollingObserver（バックグラウンドのデーモンスレッド）<br/>定期的に .py ファイルの mtime を比較"]
    C --> D{"プラグインファイルが変更されたか？"}
    D --> E["変更のデューディレイ（デフォルト1秒）"]
    E --> F["_handle_change でプラグイン名を解析<br/>（単一ファイル / パッケージ形式）"]
    F --> G["asyncio.run_coroutine_threadsafe<br/>メインイベントループにスケジュール"]
    G --> H["sdk.reload_module(name)<br/>（任意のモジュールに対しても手動で呼び出せる）"]
    H --> I["古いインスタンスをアンロード（on_unload をトリガー）<br/>依存モジュールを収集して連鎖リロードの準備"] 
    I --> J{"モジュールのソースは？"}
    J -->|"plugin_folder"| K["登録とプラグイン sys.modules をクリーンアップ<br/>plugins/ ディレクトリを再スキャン"]
    J -->|"PyPI 安装パッケージ"| L["登録をクリーンアップ + top_level に従って<br/>パッケージ sys.modules のサブツリーをクリーンアップ<br/>インポートキャッシュを更新して entry-point を再確認"]
    K --> M["再登録 + 再読み込み"]
    L --> M
    M --> N["sdk 属性に新しいインスタンスをマウント"]
    N --> O["依存モジュールの連鎖リロード<br/>（プラグインの完全リロード / PyPI の再インスタンス化）"]
    K -.->|"ファイルが削除された"| P["ロード結果から削除"]
    L -.->|"entry-point が消滅した（アンインストール済み）"| P
```

**2 種類のソースの違いは発見段階のみ**で、登録、読み込み、連鎖リロードは完全に一貫しています：

- **ローカルプラグイン**（`moduleInfo.meta.source == "plugin_folder"`）：プラグイン名に対応する `sys.modules` をクリーンアップした後、`plugins/` ディレクトリを再スキャンします。ファイルが削除された場合は、ロード結果から削除します。
- **PyPI 安装パッケージ**：`meta.top_level` に従ってパッケージの `sys.modules` のサブツリーをクリーンアップし、インポートキャッシュを更新（entry-point の 60 秒キャッシュを突破）した後、entry-point を再確認して再インポートします。entry-point が消滅した（pip でアンインストールされた）場合は、ロード結果から削除します。