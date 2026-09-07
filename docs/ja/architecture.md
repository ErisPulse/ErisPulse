# 架構概要

このドキュメントでは、ErisPulse SDK の技術的アーキテクチャを可視化した図を通じて紹介し、フレームワークの設計思想とモジュール間の関係を素早く理解できるようにします。

## SDK のコアアーキテクチャ

下図は、SDK のコアモジュール構成とその関係を示しています：

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
    SDK --> Client["Client<br/>HTTP クライアント"]
    Event --> Command["command"]
    Event --> Message["message"]
    Event --> Notice["notice"]
    Event --> Request["request"]
    Event --> Meta["meta"]
    Event --> Conversation["Conversation<br/>会話 + 永続化"]

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
| **Event** | イベントシステム。command / message / notice / request / meta の 5 種類のイベント処理と、Conversation 多段会話に対応。|
| **Adapter** | アダプタ管理器。複数プラットフォームのアダプタの登録、起動、停止を管理。|
| **Module** | モジュール管理器。プラグインの登録、ロード、アンロードを管理。依存関係宣言とトポロジカルソートに対応。|
| **Lifecycle** | ライフサイクル管理器。イベント駆動のライフサイクルフックを提供。|
| **Storage** | SQLite をベースとしたキーバリューストレージシステム。一般的な SQL チェーンクエリをサポート。|
| **Config** | TOML 形式の設定ファイル管理。|
| **Logger** | モジュール化されたログシステム。サブロガーをサポート。|
| **Router** | HTTP/WebSocket ルーティング管理。抽象層を介して下層バックエンド（現在は FastAPI + Uvicorn）をカプセル化。デコレータールーティング、ミドルウェア、グループ、リクエスト制限、CORS をサポート。|
| **Client** | 統一された HTTP/WS クライアント（2.8.0 以前は `HttpClient`、互換エイリアスを保持）。抽象層を介して下層リクエストライブラリ（現在は aiohttp）をカプセル化。リクエスト統計、リトライ、ログ、WebSocket クライアント、ErisPulse の例外体系等功能を提供。クライアントとサーバーの WebSocket は `WebSocketConnectionBase` 基底クラスを共有。|

## 初期化プロセス

下図は、`sdk.init()` の完全な初期化プロセスを示しています：

```mermaid
flowchart TD
    A["sdk.init()"] --> B["実行環境の準備"]
    B --> B1["設定ファイルの読み込み"]
    B1 --> B2["グローバル例外処理の設定"]
    B2 --> C["アダプタ & モジュールの発見"]
    C --> D{"並列ロード"}
    D --> D1["PyPI からアダプタをロード"]
    D --> D2["PyPI からモジュールをロード"]
    D1 & D2 --> E["アダプタの登録"]
    E --> E1["アダプタの起動"]
    E1 --> F["モジュールの登録"]
    F --> F1{"依存関係の検証"}
    F1 -->|"依存が不足"| F2["このモジュールをスキップして警告を記録"]
    F1 -->|"依存が満たされている"| F3["トポロジカルソート<br/>（Kahn アルゴリズム + 優先度）"]
    F3 --> G["順番にモジュールを初期化<br/>（インスタンス化 + on_load）"]
    F2 --> G
    G --> H["ルーティングサーバーの起動"]
    H --> K["準備完了"]
```

### 初期化段階の詳細

> 完全な初期化の流れの分解（Finder / Loader / Manager / Router）、下層エントリーポイント（`init()` / `init_task()` / `init_sync()`）と手動の完全起動については [起動プロセスと手動制御](advanced/startup.md) を参照してください。

## イベント処理プロセス

下図は、プラットフォームからハンドラへのメッセージの完全な流れを示しています：

```mermaid
flowchart LR
    A["プラットフォームの元メッセージ"] --> B["アダプタが受信"]
    B --> C["OneBot12 標準に変換"]
    C --> D["adapter.emit()"]
    D --> E["ミドルウェアチェーンの実行"]
    E --> F{"イベントの分散"}
    F --> G1["command<br/>コマンドハンドラ"]
    F --> G2["message<br/>メッセージハンドラ"]
    F --> G3["notice<br/>通知ハンドラ"]
    F --> G4["request<br/>リクエストハンドラ"]
    F --> G5["meta<br/>メタイベントハンドラ"]
    G1 & G2 & G3 & G4 & G5 --> H["ハンドラのコールバック実行"]
    H --> I["event.reply()<br/>SendDSL を通して返信"]
    I --> J["アダプタがプラットフォームに送信"]
```

### イベント処理の流れの詳細

上記の図は「結果」です。以下は `adapter.emit()` の後でフレームワークが**裏で何をしたか**を分解したものです。これは 3 層の分散の流れです：

```mermaid
sequenceDiagram
    participant P as プラットフォーム
    participant A as アダプタバス層<br/>AdapterManager.emit
    participant T as ハンドラ Task 層<br/>_dispatch_handler_task
    participant E as Event モジュール層<br/>_process_event

    P->>A: 元イベント
    A->>A: platform/type/detail_type + 元フィールドを抽出
    A->>A: [Recv] 受信ログ
    A->>A: lifecycle.adapter.event.receive（初期のフック）
    A->>A: self フィールドの処理（meta 分岐 / Bot 自動登録）
    A->>A: ミドルウェアチェーン（直列、イベントデータを変更可能）
    A->>A: ハンドラの収集（具体的なタイプ + ワイルドカード *）
    A->>A: 身元認証 + スコープフィルタリング（Task の作成前に、静かに無視/スキップ）
    A->>T: asyncio.create_task（fire-and-forget）
    A->>A: lifecycle.adapter.event.dispatched（最後のフック）
    T->>T: 並行信号量の取得（デフォルト上限 64）
    T->>E: Event モジュールに登録されたハンドラの呼び出し
    E->>E: lifecycle.event.pre_process
    E->>E: ignore_self（メッセージイベントはデフォルトで自身を無視）
    E->>E: 優先度順にグループ化：高→低、グループ間は直列、グループ内は並列
    E->>E: グループ内のコピー実行 + フィールドのマージ（衝突は警告）
    E->>E: グループ後の stop() 検査で、より低い優先度をブロック
    T->>T: スローログ（1 秒以上は警告、wait_reply 時間は除外）
```

**フレームワークが何をしたか、そしてあなたが介入できるポイント：**

| 段階 | フレームワークが何をしたか | 介入できるポイント |
|------|-------------|-----------|
| 受信 | 標準フィールドを抽出、`{platform}_raw` 元データを保持；`[Recv]` ログを記録 | `adapter.event.receive` を監視して初期イベントを取得 |
| self フィールド | meta イベントは connect/disconnect/heartbeat 分岐を経る；通常のイベントでは Bot を自動登録し、`adapter.bot.online` をトリガー | `adapter.bot.online` / `bot.offline` を監視 |
| ミドルウェア | **直列**実行、戻り値が None でなければイベントデータを置き換え | ミドルウェアを登録してイベントを変更/ブロック |
| 分発収集 | 先に具体的なタイプのハンドラを取得し、次に `*` ワイルドカードハンドラを取得 | — |
| 身元次元 | 分発エントリはユーザー>会話>Bot>アダプタの順に判定し、**拒否された場合はイベント全体を無視** | `ErisPulse.scope.identity` をバインド |
| スコープフィルタリング | モジュールの所有者に従って `scope.is_allowed` を判定（会話レベル>Botレベル>プラットフォームレベル）、**通過しない場合は静かにスキップ** | スコープのホワイトリスト/ブラックリストを設定 |
| スケジューリング | 各マッチするハンドラごとに独立した `asyncio.Task` を作成、`emit()` はハンドラの完了を待たずに即座に返却 | — |
| 優先度 | 高優先度のグループが先に実行；**グループ間は直列、グループ内は並列**（グループ内はイベントのコピーを持ち、フィールドをマージし、衝突は WARNING で警告）、`mark_processed(stop=True)` は**より低い優先度をブロック** | `@command(..., priority=N)` / 登録時に priority を指定 |
| ブロッキング | 各グループの処理後に `event.is_stopped()` をチェックし、ヒットした場合は**より低い優先度を実行しない** | `event.mark_processed(stop=True)` / `event.done()` |

> **よくある誤解**：
> 1. **スコープフィルタリングは静かに**— フィルタリングされたハンドラはエラーもレスポンスもせず、TRACE レベルのログ（`core.scope.denied`）にのみ表示されます。「私のモジュールがメッセージを受け取っていない」場合は、まずスコープのバインディングを確認してください。
> 2. **ハンドラは天然並列**— フレームワークは各ハンドラに独立した Task を作成しており、**自分で `asyncio.create_task` をラップする必要はありません**。
> 3. **同じ優先度グループ内はブロックしない**— `mark_processed(stop=True)` は**より低い優先度のグループのみをブロック**し、同じグループ内で並列実行されたハンドラは途中で中断されません。
> 4. **スローログの閾値は固定 1 秒**— ハンドラの処理時間が 1 秒を超えるとログに WARNING が表示されます（`wait_reply` は処理時間から除外されます）、ただし実行は中断されません。

> スコープ（scope）のモジュール次元の 3 級バインディング、身元認証と出力アクション制限の詳細は [スコープ（scope）](advanced/scope.md) を参照してください。イベントスコープのテキストフィルタリングとコマンドユーザー ACL は [イベント処理入門](getting-started/event-handling.md) を参照してください。並列上限の設定は [設定ガイド](user-guide/configuration.md#フレームワーク設定) を参照してください。

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

> 完全なイベント監視方法（`lifecycle.on()` / `once()` / `has_handlers()`）、すべてのライフサイクルイベントのリストとデータ形式は [ライフサイクル管理](advanced/lifecycle.md) を参照してください。

## モジュールのロード戦略

ErisPulse は 3 種類のモジュールロード戦略をサポートし、`get_load_strategy()` が返す `ModuleLoadStrategy` で宣言されます：

```mermaid
flowchart TD
    A["モジュールを ModuleManager に登録"] --> B{"ロード戦略"}
    B -->|"lazy_load = true<br/>+ activate_on 声明"| C["ModuleActivator 代理を作成"]
    B -->|"lazy_load = true<br/>activate_on なし"| D["LazyModule 代理を作成"]
    B -->|"lazy_load = false"| E["即時インスタンス作成"]
    C --> F["イベント/コマンド stub をディスパッチャーに登録"]
    F --> G["sdk 属性にマウント"]
    G --> H["イベント到達時にアクティベーション"]
    H --> I["インスタンス化 + on_load() + stub の解除"]
    D --> J["sdk 属性にマウント"]
    J --> K["最初の属性アクセス時に初期化"]
    E --> L["on_load() を呼び出す"]
    L --> M["sdk 属性にマウント"]
```

> 詳細は [遅延ロードシステム](advanced/lazy-loading.md)、[ライフサイクル管理](advanced/lifecycle.md) およびモジュールドキュメントを参照してください。

### イベント駆動遅延アクティベーション（`activate_on`）のトリガーアーキテクチャ

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

`activate_on` を使用すると、モジュールは**最初のマッチするイベント/コマンドが到達したときに初めてロード**され、常駐メモリを避けると同時にイベントのロスを防ぎます：

```mermaid
flowchart LR
    subgraph Declare["モジュールの宣言"]
        S1["get_load_strategy() が<br/>ModuleLoadStrategy(activate_on=...) を返す"] --> S2["activate_on 構文：<br/>str / dict / list 自由に混ぜる"]
        S2 --> S2a["'message' → イベントタイプレベル"]
        S2 --> S2b["{'notice': 'group_member_increase'}<br/>→ タイプ + detail_type"]
        S2 --> S2c["{'command': 'roll'}<br/>→ コマンドトリガー（簡潔/リスト）"]
        S2 --> S2d["{'command': {'name': 'dice', 'help': ...,<br/>'aliases': [...], 'hidden': ...}}<br/>→ コマンドトリガー（dict 声明）"]
    end

    subgraph Runtime["実行時"]
        R1["ModuleActivator が stub を登録"] --> R1a["イベント stub → message/notice/request/meta マネージャー<br/>優先度 ACTIVATION_STUB_PRIORITY（極低）"]
        R1 --> R1b["コマンド stub → コマンドマネージャー<br/>占位コマンド（dict 声明の help/usage/group/aliases/hidden に類似）"]
        R1a --> R2{"トリガーイベントが到達"}
        R1b --> R2
        R2 --> R3["owner に従ってスコープフィルタリング"]
        R3 --> R4["asyncio.Lock で重複アクティベーションを防ぐ"]
        R4 --> R5["モジュールのインスタンス化 + on_load() の呼び出し"]
        R5 --> R6["すべての stub を解除"]
        R6 --> R7["イベントを実際のハンドラに転送"]
    end

    Declare --> Runtime
```

**トリガの意味の要点：**

> 完全な `activate_on` 構文（str / dict / list）、コマンド dict 声明、占位コマンド help 回帰チェーン、スコープフィルタリングと失敗の意味は [遅延ロードシステム](advanced/lazy-loading.md#イベント駆動遅延アクティベーションactivate_on) を参照してください。

## ローカルプラグインフォルダアーキテクチャ

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

ローカルプラグイン（`plugins/` ディレクトリ）は、パッケージ化して公開する必要がなく、フレームワークの起動時に自動的に発見され、ロードされます：

```mermaid
flowchart TD
    A["プロジェクトの plugins/ ディレクトリ<br/>（ErisPulse.framework.plugins_dir、複数ディレクトリをサポート）"] --> B{"PluginFolderLoader.discover()"}
    B --> C["単ファイル：dice.py → プラグイン名 = ファイル名"]
    B --> D["パッケージ形式：weather/（__init__.py を含む）→ プラグイン名 = ディレクトリ名"]
    B --> E["無視：__pycache__ / _ で始まる / .py でない / __init__.py がないディレクトリ"]
    C --> F["モジュールをインポート（spec_from_file_location）"]
    D --> G["モジュールをインポート（sys.path + import_module）"]
    F --> H["モジュールクラスを識別：Main（BaseModule の子クラス）を優先、なければ最初の子クラス"]
    G --> H
    H --> I["entry-point と一致する moduleInfo を構築"]
    I --> J["ModuleLoader.load() で統合<br/>ローカルが PyPI の同名インストールパッケージを上書き"]
    J --> K["インストールパッケージモジュールと共用：<br/>有効状態 / スコープ / meta / i18n / コンテキスト"]
```

**規約と特性：**

- プラグイン名の出典：単ファイルはファイル名、パッケージ形式はディレクトリ名
- ローカルプラグイン `moduleInfo.meta.source == "plugin_folder"` で、PyPI インストールパッケージモジュールとシームレスに共存
- 同名の場合はローカルが優先（ローカルの上書きデバッグに便利）、無効化された場合は同名の entry-point 条目も削除される

## モジュールのホットリロードアーキテクチャ

ホットリロードは**すべてのモジュールソース**に対して一貫して適用されます：ローカルプラグインはファイル変更を監視して自動的にトリガし、任意のモジュールは `sdk.reload_module()` / `sdk.module.reload()` で手動でリロードできます（PyPI インストールパッケージモジュールは pip でアップグレード後に呼び出すことで有効になります）：

```mermaid
flowchart TD
    A["sdk.enable_plugin_hot_reload()<br/>（自動監視、ローカルプラグインディレクトリのみ）"] --> B["PluginReloadWatcher を起動"]
    B --> C["PollingObserver（バックグラウンドデーモンスレッド）<br/>定期的に .py ファイルの mtime を比較"]
    C --> D{"プラグインファイルの変更"}
    D --> E["変更のデバウンス（デフォルト 1 秒）"]
    E --> F["_handle_change でプラグイン名を解析<br/>（単ファイル / パッケージ形式）"]
    F --> G["asyncio.run_coroutine_threadsafe<br/>メインイベントループにスケジュール"]
    G --> H["sdk.reload_module(name)<br/>（任意のモジュールに手動で呼び出しても可）"]
    H --> I["古いインスタンスをアンロード（on_unload をトリガー）<br/>依存者を収集し、連鎖リロードを準備"]
    I --> J{"モジュールの出所？"}
    J -->|"plugin_folder"| K["登録とプラグイン sys.modules のクリーンアップ<br/>plugins/ ディレクトリを再スキャン"]
    J -->|"PyPI インストールパッケージ"| L["登録のクリーンアップ + top_level に従って<br/>パッケージの sys.modules 木をクリーンアップ<br/>エントリポイントを再検索し、再インポート"]
    K --> M["再登録 + 再ロード"]
    L --> M
    M --> N["sdk 属性に新しいインスタンスをマウント"]
    N --> O["依存者を連鎖リロード<br/>（プラグインの完全リロード / PyPI の再インスタンス化）"]
    K -.->|"ファイルが削除された"| P["ロード結果から削除"]
    L -.->|"entry-point が消失した（アンインストール済み）"| P
```

**2 つの出所の違いは発見段階のみ**、登録、ロード、連鎖リロードは完全に同じです：

- **ローカルプラグイン**（`moduleInfo.meta.source == "plugin_folder"`）：`sys.modules` のプラグイン名に対応するクリーンアップ後、`plugins/` ディレクトリを再スキャンします。ファイルが削除された場合は、ロード結果から削除されます。
- **PyPI インストールパッケージ**：`meta.top_level` に従って、`sys.modules` のパッケージのサブツリーをクリーンアップし、エントリポイントの 60 秒キャッシュを突破するためのインポートキャッシュをリフレッシュした後、再検索して再インポートします。entry-point が消失した（pip でアンインストールした）場合は、ロード結果から削除されます。