以下是 ErisPulse SDK 开发文档（模块与适配器开发全量知识库）。请基于文档内容回答；
文档未覆盖的 API 以 SDK 源码 docstring 为准，不要编造不存在的接口或行为。


---


# ErisPulse 完整开发物料
> **注意**：本文档内容较多，建议仅用于具有强大上下文能力的 AI 模型


---



====
框架理解
====


### 架构概览

# アーキテクチャ概要

> [!TIP]
> **この記事を読むタイミング**：フレームワークが背後で何をしているのか、1 つのメッセージがどのように流れるのか、モジュールがどのような順序で初期化されるのか、ホットリロード時に何が起こるのか、または「フレームワークがなぜそのように振る舞うのか」を理解したいときに読んでください。ハンドラを書くだけなら [イベント処理の入門](getting-started/event-handling.md) で十分です。必要なければ飛ばしてください。

ユーザーが送信したメッセージがロボットに返信されるまで、メッセージはアダプタ変換、ミドルウェア、スコープフィルタリング、優先度スケジューリングといった数段階を経ます。モジュールも起動時にすべて読み込まれるわけではありません。この記事では、このチェーンを図で明確に描き、各段階で何ができるかを説明します。

## SDK のコアアーキテクチャ

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
    SDK --> Client["Client<br/>HTTP クライアント"]
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
| **Event** | イベントシステム。command / message / notice / request / meta の 5 種類のイベント処理と、Conversation 多輪対話機能を提供します。|
| **Adapter** | アダプタマネージャー。複数のプラットフォーム用アダプタの登録、起動、停止を管理します。|
| **Module** | モジュールマネージャー。プラグインの登録、ロード、アンロードを管理し、依存関係の宣言とトポロジカルソートをサポートします。|
| **Lifecycle** | ライフサイクルマネージャー。イベント駆動のライフサイクルフックを提供します。|
| **Storage** | SQLite を基にしたキー値ストレージシステム。一般的な SQL チェーン式クエリをサポートします。|
| **Config** | TOML 形式の設定ファイルを管理します。|
| **Logger** | モジュール化されたログシステム。サブロガーをサポートします。|
| **Router** | HTTP/WebSocket ルーティング管理。抽象層を介して下層バックエンド（現在は FastAPI + Uvicorn）をカプセル化し、デコレータールーティング、ミドルウェア、グループ、リクエスト制限、CORS をサポートします。|
| **Client** | 統一 HTTP/WS クライアント（2.8.0 以前は `HttpClient` で、互換性のエイリアスを保持）。抽象層を介して下層リクエストライブラリ（現在は aiohttp）をカプセル化し、リクエスト統計、リトライ、ログ、WebSocket クライアント、ErisPulse の例外体系等功能を提供します。クライアントとサーバーの WebSocket は `WebSocketConnectionBase` 基底クラスを共有します。|

## 初期化の流れ

下図は `sdk.init()` の完全な初期化プロセスを示しています：

```mermaid
flowchart TD
    A["sdk.init()"] --> B["実行環境の準備"]
    B --> B1["設定ファイルのロード"]
    B1 --> B2["グローバル例外処理の設定"]
    B2 --> C["アダプタ & モジュールの発見"]
    C --> D{"並列でロード"}
    D --> D1["PyPI からアダプタをロード"]
    D --> D2["PyPI からモジュールをロード"]
    D1 & D2 --> E["アダプタの登録"]
    E --> E1["アダプタの起動"]
    E1 --> F["モジュールの登録"]
    F --> F1{"依存関係の検証"}
    F1 -->|"依存が不足"| F2["モジュールをスキップして警告を記録"]
    F1 -->|"依存が満たされる"| F3["トポロジカルソート<br/>（Kahn アルゴリズム + 優先度）"]
    F3 --> G["順序にモジュールを初期化<br/>（インスタンス化 + on_load）"]
    F2 --> G
    G --> H["ルーティングサーバーの起動"]
    H --> K["実行準備完了"]
```

### 初期化段階の詳細

> 完全な初期化の流れを分解した（Finder / Loader / Manager / Router）、下層のエントリーポイント（`init()` / `init_task()` / `init_sync()`）と手動での完全起動については [起動プロセスと手動制御](advanced/startup.md) を参照してください。

## イベント処理の流れ

下図は、プラットフォームからハンドラまでのメッセージの完全な流れを示しています：

```mermaid
flowchart LR
    A["プラットフォームの元のメッセージ"] --> B["アダプタが受信"]
    B --> C["OneBot12 標準に変換"]
    C --> D["adapter.emit()"]
    D --> E["ミドルウェアチェーンを実行"]
    E --> F{"イベントの分散"}
    F --> G1["command<br/>コマンドハンドラ"]
    F --> G2["message<br/>メッセージハンドラ"]
    F --> G3["notice<br/>通知ハンドラ"]
    F --> G4["request<br/>リクエストハンドラ"]
    F --> G5["meta<br/>メタイベントハンドラ"]
    G1 & G2 & G3 & G4 & G5 --> H["ハンドラのコールバックを実行"]
    H --> I["event.reply()<br/>SendDSL を通して返信"]
    I --> J["アダプタがプラットフォームに送信"]
```

### イベント処理のチェーンの詳細

上記の図は「結果」です。下に `adapter.emit()` の後でフレームワークが**背後で何をしたか**を分解します。これは 3 層の分散チェーンです：

```mermaid
sequenceDiagram
    participant P as プラットフォーム
    participant A as アダプタマネージャーレイヤー<br/>AdapterManager.emit
    participant T as ハンドラ Task レイヤー<br/>_dispatch_handler_task
    participant E as Event モジュールレイヤー<br/>_process_event

    P->>A: 元のイベント
    A->>A: platform/type/detail_type + 元のフィールドを抽出
    A->>A: [Recv] 受信ログを記録
    A->>A: lifecycle.adapter.event.receive（最も初期のフック）
    A->>A: self フィールドを処理（meta 分岐 / Bot 自動登録）
    A->>A: ミドルウェアチェーン（直列、イベントデータを変更可能）
    A->>A: ハンドラを収集（具体的なタイプ + ワイルドカード *）
    A->>A: アイデンティティの認証 + スコープフィルタリング（Task の作成前に、静かに破棄/スキップ）
    A->>T: asyncio.create_task（fire-and-forget）
    A->>A: lifecycle.adapter.event.dispatched（最後のフック）
    T->>T: 並行信号量を取得（デフォルト上限 64）
    T->>E: Event モジュールに登録されたハンドラを呼び出す
    E->>E: lifecycle.event.pre_process
    E->>E: ignore_self（メッセージイベントはデフォルトで自身を無視）
    E->>E: 優先度順にグループ化：高→低、グループ間は直列、グループ内は並列
    E->>E: グループ内のコピーを実行 + フィールドのマージ（競合は警告）
    E->>E: グループ後の stop() チェックで、より低い優先度をブロック
    T->>T: 遅いログ（1 秒以上かかれば警告、wait_reply 時間は除外）
```

**各ステップでフレームワークが何をしたか、そして何を干预できるか：**

| ステージ | フレームワークが何をしたか | あなたが干预できる |
|------|-------------|-----------|
| 受信 | 標準フィールドを抽出し、`{platform}_raw` の元のデータを保持。`[Recv]` ログを記録 | `adapter.event.receive` を監視して初期イベントを取得 |
| self フィールド | meta イベントは connect/disconnect/heartbeat 分岐を処理。通常のイベントは Bot を自動登録し、`adapter.bot.online` をトリガー | `adapter.bot.online` / `bot.offline` を監視 |
| ミドルウェア | **直列**で実行。戻り値が None でなければイベントデータを置き換える | ミドルウェアを登録してイベントを変更/ブロック |
| 分発と収集 | 具体的なタイプのハンドラを先に取得し、次に `*` ワイルドカードハンドラを取得 | — |
| アイデンティティ次元 | 分発の入口はユーザー > 会話 > Bot > アダプタの順に判定し、イベントを受け取るかどうかを決定（`scope.is_identity_allowed`）。**拒否された場合はイベントは完全に破棄される** | `ErisPulse.scope.identity` をバインド |
| スコープフィルタリング | モジュールの所有者に応じて `scope.is_allowed` を判定（会話レベル > Bot レベル > プラットフォームレベル）。**不通過の場合は静かにスキップ** | スコープのホワイトリスト/ブラックリストを設定 |
| スケジューリング | 各マッチするハンドラは独立した `asyncio.Task` で実行される。`emit()` はハンドラの完了を待たずに即座に返却される | — |
| 優先度 | 高優先度のグループが先に実行される。**グループ間は直列、グループ内は並列**（グループ内の各ハンドラはイベントのコピーを持ち、フィールドをマージし、競合は WARNING として警告）。 | `@command(..., priority=N)` / 登録時に priority を指定 |
| ブロッキング | 各グループの処理後、`event.is_stopped()` をチェックし、マッチした場合は**より低い優先度は実行されない** | `event.mark_processed(stop=True)` / `event.done()` |

> **よくある誤解**：
> 1. **スコープフィルタリングは静かに実行される**— フィルターされたハンドラはエラーもレスポンスも出さず、TRACE ログレベルでのみ表示される（`core.scope.denied`）。"私のモジュールにメッセージが届かない"場合は、まずスコープのバインドを確認してください。
> 2. **ハンドラは天然並列**— フレームワークは各ハンドラに独立した Task を作成しており、**自分で `asyncio.create_task` をラップする必要はない**。
> 3. **同じ優先度のグループ内ではブロッキングされない**— `mark_processed(stop=True)` は、より低い優先度のグループをブロックするだけで、同じグループ内で並行実行中のハンドラは途中で中断されない。
> 4. **遅いログの閾値は固定の 1 秒**— ハンドラの処理時間が 1 秒を超えると、ログに WARNING が出る（`wait_reply` の待機時間は処理時間から除外される）が、実行は中断されない。

> スコープのモジュール次元の 3 級バインド、アイデンティティ次元の認証と出力アクション制限の詳細は [スコープ（scope）](advanced/scope.md) を参照してください。イベントスコープのテキストフィルタリングとコマンドユーザー ACL は [イベント処理の入門](getting-started/event-handling.md) を参照してください。並列上限の設定は [設定ガイド](user-guide/configuration.md#フレームワーク設定) を参照してください。

## ライフサイクルイベント

下図はフレームワーク各コンポーネントのライフサイクルイベントの発生順序を示しています：

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

> 完全なイベント監視方法（`lifecycle.on()` / `once()` / `has_handlers()`）、すべてのライフサイクルイベントリストとデータ形式は [ライフサイクル管理](advanced/lifecycle.md) を参照してください。

## モジュールのロード戦略

ErisPulse は 3 つのモジュールロード戦略をサポートし、`get_load_strategy()` が返す `ModuleLoadStrategy` によって宣言されます：

```mermaid
flowchart TD
    A["モジュールを ModuleManager に登録"] --> B{"ロード戦略"}
    B -->|"lazy_load = true<br/>+ activate_on が宣言されている"| C["ModuleActivator 代理を作成"]
    B -->|"lazy_load = true<br/>activate_on がない"| D["LazyModule 代理を作成"]
    B -->|"lazy_load = false"| E["即時インスタンスを作成"]
    C --> F["イベント/コマンド stub をディスパッチャに登録"]
    F --> G["sdk 属性にマウント"]
    G --> H["イベント到着時にアクティベーションをトリガー"]
    H --> I["インスタンス化 + on_load() + stub の登録解除"]
    D --> J["sdk 属性にマウント"]
    J --> K["最初の属性アクセス時に初期化"]
    E --> L["on_load() を呼び出す"]
    L --> M["sdk 属性にマウント"]
```

> 詳細は [遅延ロードシステム](advanced/lazy-loading.md)、[ライフサイクル管理](advanced/lifecycle.md) およびモジュールのドキュメントを参照してください。

### イベント駆動遅延アクティベーション（`activate_on`）のトリガーアーキテクチャ

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

`activate_on` を使用すると、モジュールは**最初のマッチするイベント/コマンドが到着した時点で**初めてロードされ、常駐メモリを避けることができ、同時にイベントのロスも防げます：

```mermaid
flowchart LR
    subgraph Declare["モジュールの宣言"]
        S1["get_load_strategy() が<br/>ModuleLoadStrategy(activate_on=...) を返す"] --> S2["activate_on の構文：<br/>str / dict / list を自由に混ぜられる"]
        S2 --> S2a["'message' → イベントタイプレベル"]
        S2 --> S2b["{'notice': 'group_member_increase'}<br/>→ タイプ + detail_type"]
        S2 --> S2c["{'command': 'roll'}<br/>→ コマンドトリガー（簡略/リスト）"]
        S2 --> S2d["{'command': {'name': 'dice', 'help': ...,<br/>'aliases': [...], 'hidden': ...}}<br/>→ コマンドトリガー（dict 声明）"]
    end

    subgraph Runtime["実行時"]
        R1["ModuleActivator が stub を登録"] --> R1a["イベント stub → message/notice/request/meta マネージャー<br/>優先度 ACTIVATION_STUB_PRIORITY（極低）"]
        R1 --> R1b["コマンド stub → コマンドマネージャー<br/>占位コマンド（help/usage/group/aliases/hidden のミラーリング）"]
        R1a --> R2{"イベント到着がトリガー"}
        R1b --> R2
        R2 --> R3["owner によるスコープフィルタリング"]
        R3 --> R4["asyncio.Lock による重複アクティベーション防止"]
        R4 --> R5["モジュールのインスタンス化 + on_load() の呼び出し"]
        R5 --> R6["すべての stub の登録解除"]
        R6 --> R7["イベントを真のハンドラに転送"]
    end

    Declare --> Runtime
```

**トリガの意味の要点：**

> 完全な `activate_on` 構文（str / dict / list）、コマンド dict 声明、占位コマンド help のフォールバックチェーン、スコープフィルタリング、失敗の意味については [遅延ロードシステム](advanced/lazy-loading.md#イベント駆動遅延アクティベーションactivate_on) を参照してください。

## 本地プラグインフォルダのアーキテクチャ

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

ローカルプラグイン（`plugins/` ディレクトリ）は、パッケージ化して公開する必要がなく、フレームワークの起動時に自動的に発見され、ロードされます：

```mermaid
flowchart TD
    A["プロジェクトの plugins/ ディレクトリ<br/>（ErisPulse.framework.plugins_dir、複数ディレクトリに対応）"] --> B{"PluginFolderLoader.discover()"}
    B --> C["単一ファイル：dice.py → プラグイン名 = ファイル名"]
    B --> D["パッケージ形式：weather/（__init__.py を含む）→ プラグイン名 = ディレクトリ名"]
    B --> E["無視：__pycache__ / _ で始まる / .py でない / __init__.py がないディレクトリ"]
    C --> F["モジュールのインポート（spec_from_file_location）"]
    D --> G["モジュールのインポート（sys.path + import_module）"]
    F --> H["モジュールクラスの識別：Main（BaseModule の子クラス）を優先し、なければ最初の子クラス"]
    G --> H
    H --> I["entry-point と一致する moduleInfo を構築"]
    I --> J["ModuleLoader.load() で統合<br/>ローカルが優先して PyPI の同名インストールパッケージを上書き"]
    J --> K["インストールパッケージモジュールと共用：<br/>有効状態 / スコープ / meta / i18n / コンテキスト"]
```

**約束と特性：**

- プラグイン名の由来：単一ファイルはファイル名、パッケージ形式はディレクトリ名
- ローカルプラグイン `moduleInfo.meta.source == "plugin_folder"` で、PyPI インストールパッケージモジュールとシームレスに共存
- 同名の場合はローカルが優先（ローカルの上書きデバッグに便利）、無効化された場合は同名の entry-point 条目も削除

## モジュールのホットリロードアーキテクチャ

ホットリロードは**すべてのモジュールソース**に対して一貫しています：ローカルプラグイン（`plugins/` ディレクトリ）、実行時登録（`sdk.module.register()`）、PyPI インストールパッケージモジュールはすべて `sdk.reload_module()` / `sdk.module.reload()` でホットリロードできます。**デフォルトは全量リロード**（トップレベルパッケ名で import キャッシュをクリアし、依存者コードを再インポート、`full=False` は軽量の逃生門）；`sdk.reload_all_modules()` / `sdk.module.reload_all()` で登録済みのすべてのモジュールを一度に全量リロードできます（pip で一括アップデート後に呼び出すことですべてが有効になります）：

```mermaid
flowchart TD
    A["sdk.enable_plugin_hot_reload()<br/>（自動監視、ローカルプラグインディレクトリのみ）"] --> B["PluginReloadWatcher を起動"]
    B --> C["PollingObserver（バックグラウンドデーモンスレッド）<br/>定期的に .py ファイルの mtime を比較"]
    C --> D{"プラグインファイルの変更"}
    D --> E["変更のデューディレイ（デフォルト 1 秒）"]
    E --> F["_handle_change でプラグイン名を解析<br/>（単一ファイル / パッケージ形式）"]
    F --> G["asyncio.run_coroutine_threadsafe<br/>イベントループに戻す"]
    G --> H["sdk.reload_module(name, full=True がデフォルト)<br/>（任意のモジュールに手動で呼び出してもよい）"]
    H --> I["構文検証（ファイルごとに解析）<br/>失敗したらリロードを拒否し、古いインスタンスがサービスを続ける"]
    I --> J["古いインスタンスのアンロード（on_before_unload → on_unload）<br/>依存者を収集し、連鎖リロードを準備"]
    J --> K{"モジュールのソースは？"}
    K -->|"plugin_folder"| L["登録とプラグイン sys.modules をクリア<br/>plugins/ ディレクトリを再スキャン"]
    K -->|"runtime 実行時登録"| M["定義モジュールのキャッシュをクリアし、再インポート<br/>クラス名で再取得（__main__ 守衛）"]
    K -->|"PyPI インストールパッケージ"| N["登録をクリアし、top_level でパッケージをクリア<br/>sys.modules のサブツリーと __pycache__ バイトコード<br/>（メタデータが欠落した場合は、古いモジュールオブジェクトのトップセグメントでバックアップ）<br/>インポートキャッシュをリフレッシュした後、entry-point を再調査"]
    L --> O["再登録 + 再ロード"]
    M --> O
    N --> O
    O --> P["sdk 属性に新しいインスタンスをマウント<br/>新旧クラスのアイデンティティを確認（偽のリロード警告）"]
    P --> Q["依存者への連鎖リロード<br/>（プラグイン/実行時では完全リロード；<br/>PyPI 依存者はデフォルトでコードを再インポート）"]
    L -.->|"ファイルが削除された"| R["ロード結果から削除"]
    M -.->|"定義が安全に再インポートできない"| R
    N -.->|"entry-point が消えた（アンインストールされた）"| R
```

**3 つのソースの違いは発見段階のみ**、検証、アンロード、連鎖リロードは完全に同じです：

- **ローカルプラグイン**（`moduleInfo.meta.source == "plugin_folder"`）：`sys.modules` をクリアした後、`plugins/` ディレクトリを再スキャンします。ファイルが削除された場合は、ロード結果から削除されます。
- **実行時登録**（`source == "runtime"`）：定義モジュールを再インポートし、クラス名で再取得して再登録します。`__main__` に定義されている、またはソースファイルのないクラスは再インポートを拒否します（守衛アラート、エントリースクリプトの再実行を防ぎます）。
- **PyPI インストールパッケージ**：`meta.top_level` に基づいて、`sys.modules` のサブツリーをクリアし、インポートキャッシュをリフレッシュします（entry-point 60 秒キャッシュを突破）。再調査して再インポートします。entry-point が消えた（pip でアンインストールされた）場合は、ロード結果から削除されます。

**デフォルトの意味と信頼性の保証（2.11）：**

- **reload は全量リロード**：デフォルトで、トップレベルパッケージ名に基づいて `sys.modules` をクリアし、依存者コードを再インポートします。`full=False` は、メタデータに基づいてクリアし、PyPI 依存者は直接再インスタンス化するだけです（巨大な依存ツリーのパフォーマンスのための逃生門）。
- **構文検証のゲート**：アンロードのプロセスに入る前に、ファイルごとに構文解析を行い、失敗した場合はリロードを拒否します。古いインスタンスはアンロードされず、サービスを継続します。構文エラーは、モジュールを「半死」状態にすることがありません（巨大なパッケージでファイル数上限を超えた場合は、検証をスキップします）。
- **キャッシュのバックアップ**：`top_level` メタデータが欠落した場合は、「旧モジュールオブジェクト `__name__` 前方一致 → モジュールクラス `__module__` 前方一致」の 2 段階でクリア範囲を推定します。リロードの際には、ソースファイルのバイトコードキャッシュ（`__pycache__`）もクリアし、秒単位で長さが同じ小さな変更でも有効になります。
- **アイデンティティの確認**：リロードが成功した後、新旧のクラスアイデンティティが変化しているかをアサーションし、変化していない場合（C 拡張など、キャッシュがクリアできない場合）は明示的に警告し、`module.reload` イベントに `identity_changed: false` を含めます。`module.get_info()` は `running_identity` / `stale` フィールドで「登録されたバージョン ≠ 実行中のバージョン」を公開します。
- **失敗の確認**：load 失敗の現場（例外 + traceback）は、`module.last_error(名前)` / `get_info()["last_error"]` から直接確認できます。失敗したパスは、そのモジュールの import キャッシュをクリアします。「コードを変更してから再 reload する」ことで、必ず新しいコードを読み込むことができます。
- 重載は、もともと遅延ロードのモジュールを強制的にアクティブにします（明示的なログ）。`reload_all_modules()` は、遅延ロードの戦略を維持し、重載前に既にロード済みのモジュールを再アクティブにし、スリープ（休眠）中のモジュールはスリープのままにします。
- `reload_all_modules()` は依存関係のトポロジカル順序で再ロードし、単一モジュールの失敗は診断を記録してスキップします（全体のロールバックはしない—on_unload の副作用は取り消せないため、単一モジュールのホットリロードのベストエフォートの意味と一致）。重載失敗でロールバックされた状況も同様で、ログには明確に旧インスタンスが終了済みであることが示されます。

## アダプタのホットリロードアーキテクチャ

アダプタのコードレベルのホットリロード（2.11）は、モジュールのパイプラインと同構造です：`sdk.adapter.reload(プラットフォーム名)` / `sdk.reload_adapter(プラットフォーム名)` は、**ローカルプラグイン**と **PyPI インストールパッケージ**の 2 つのソースに対して実行されます：

```mermaid
flowchart TD
    A["sdk.adapter.reload(プラットフォーム名)"] --> B["構文検証（ファイルごとに解析）<br/>失敗したらリロードを拒否し、旧アダプタがサービスを継続"]
    B --> C["スナップショット：adapterInfo / インスタンス / 起動状態 /<br/>起動タスク / bots / sys.modules 条目"]
    C --> D["unload（shutdown でクリーンアップ：<br/>ルーティング/イベント/コマンド/タスク/接続/bot offline + デリグistration）"]
    D --> E["キャッシュのクリア：__pycache__ バイトコード →<br/>sys.modules サブツリー → invalidate_caches<br/>→ finder キャッシュ → プラグインパスの記録"]
    E --> F{"ソースは？"}
    F -->|"プラグインディレクトリ"| G["plugins/ を再スキャン（discover_adapters）"]
    F -->|"PyPI インストールパッケージ"| H["entry-point を再調査して再インポート<br/>（top_level クリア + クラス __module__ バックアップ）"]
    G --> I["再登録 + startup（元の起動状態）<br/>クラスのアイデンティティを確認（偽のリロード警告）"]
    H --> I
    I --> J["adapter.reload イベント<br/>identity_changed / version_old→new / was_started"]
    G -.->|"プラグインが削除された"| K["ロード結果から削除"]
    H -.->|"entry-point が消えた"| K
    I -.->|"失敗"| L["ロールバック：sys.modules /<br/>登録のスタブ / インスタンス / 起動状態を復元"]
```

**モジュールのパイプラインとの違い：**

- アダプタには遅延ロードや依存の連鎖リロードがない：リロードは**依存する他のアダプタには連鎖しない**（警告のみ—依存先は登録表を間接的に消費しており、インスタンスの連鎖的な意味はない）。
- 起動は非同期のチェーン（`startup` は `_run_adapter` で発行され、依存のスキップと指数的バックオフリトライを含む）：起動の一時的な失敗は**リロードの失敗とは見なされない**（コードはすでに新しいものに変わっているため）、結果は `adapter.status.change` で通知される。
- `register()` のインスタンスの再利用の落とし穴（同じオブジェクトは旧インスタンスが再利用される）は、「pyc クリア + sys.modules クリア + アイデンティティの確認」の 3 つの手段でバックアップされる。
- ライフサイクルイベント：`adapter.reload`（payload に `adapter_name` / `success` / `full` / `duration_ms` / `identity_changed` / `version_old→new` / `was_started` / `source` を含む）

## 次に進むべきこと

- **起動/終了を手動で制御したい**：[起動プロセスと手動制御](advanced/startup.md) を参照してください。初期化の各段階を分解し、個別にアダプタやルーティングを起動・停止できます。
- **遅延ロードとスリープを理解したい**：[遅延ロードシステム](advanced/lazy-loading.md) を参照してください。`activate_on` イベント駆動遅延アクティベーションの完全な構文が含まれています。
- **モジュールを書くときにライフサイクルを上手く使う**：[ライフサイクル管理](advanced/lifecycle.md) を参照してください。すべてのライフサイクルイベントと監視方法が含まれています。



====
快速开始
====

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



====
入门指南
====


### 入门指南总览

# 入門ガイド

> [!TIP]
> **この記事を読むタイミング**：ロボットが [5 分鐘のクイックスタート](../quick-start.md) で起動している場合、フレームワークのコアコンセプトと一般的な機能を体系的に理解したい場合に読んでください。まだ起動していない場合は、まずクイックスタートを完了してください。特定の問題を検索したい場合は、対応する個別記事に直接ジャンプしてください。

ロボットが起動した後、ここではフレームワークのコアコンセプトと一般的な機能を体系的に理解するためのガイドを提供します。

## 学習パス

以下はドキュメントのトップページで定義された **L1 コアの5つの主要なドキュメント**です。これらを順番に読むことで（約1–2時間）、90%の機能を独自に開発できます。

| ステップ | 主題 | 説明 |
|------|------|------|
| 1 | [モジュール開発入門](../developer-guide/modules/getting-started.md) | 独立したモジュールパッケージを作成し、モジュールの構造と登録メカニズムを理解する |
| 2 | [基本概念](basic-concepts.md) | ErisPulse のコアアーキテクチャとモジュール設計を理解する |
| 3 | [Event 包装クラス](../developer-guide/modules/event-wrapper.md) | イベントオブジェクトの返信、要求、およびフィールドへのアクセスを習得する |
| 4 | [設定ファイルの説明](../user-guide/configuration.md) | 設定を記入し、ホットアップデートと環境変数による上書きを理解する |
| 5 | [例外のキャッチ](../advanced/errors.md) | フレームワークの例外階層を認識し、クラッシュしない処理チェーンを書く |

このディレクトリには、**必要に応じて参照**できる追加のドキュメントも含まれています。

| ドキュメント | いつ読むか |
|------|-----------|
| [最初のロボットを作成する](first-bot.md) | モジュール化開発を学ぶ前に、まず埋め込み型のプロセッサを書いてみたい場合 |
| [イベント処理入門](event-handling.md) | イベントの種類（メッセージ / コマンド / 通知 / 要求）に応じた処理方法を迅速に確認したい場合 |
| [一般的なタスクの例](common-tasks.md) | ストレージ、定期タスク、権限制御の既存の完全なコードをコピーしたい場合 |
| [IDE補完ガイド](ide-completion.md) | プラットフォーム固有のメソッドのIDE自動補完をしたい場合 |

## 開発方法の選択

ErisPulse は以下の2つの開発方法をサポートしています。

| 方法 | 適用シーン | 説明 |
|------|---------|------|
| **埋め込み開発** | プロトタイプ作成、プロジェクト内の機能 | `main.py` にプロセッサを直接記述し、独立したモジュールを作成する必要はありません。 |
| **モジュール開発**（推奨） | 本番環境、機能の配布 | 独立した Python パッケージを作成し、`epsdk install` を使用してインストールして使用します。 |

> 両方の方法の詳細な比較と例については、[最初のロボットを作成する](first-bot.md) および [モジュール開発の入門](../developer-guide/modules/getting-started.md) を参照してください。

## アーキテクチャ概要

ErisPulse はイベント駆動アーキテクチャを採用しており、以下の主要なシステムで構成されています。

- **アダプタシステム** — 各プラットフォームとの通信を行い、プラットフォームのイベントを統一された OneBot12 標準形式に変換します。
- **イベントシステム** — メッセージ、コマンド、通知、リクエスト、メタイベントの5種類のイベントを処理します。
- **モジュールシステム** — 独立したモジュールにより機能を拡張でき、依存管理や遅延読み込みをサポートします。
- **コアモジュール** — Storage（ストレージ）、Config（設定）、Logger（ログ）、Router（ルーティング）などの基本的な機能を提供します。

> 詳細なアーキテクチャ図と初期化の流れについては、[アーキテクチャ概要](../architecture.md) をご参照ください。

## 次のステップ

上記の学習パス（L1 コアの5つの記事）の順序に従って読むことができます。目的に応じて直接ジャンプすることも可能です。

- **まずは実践したい**：[最初のロボットを作成する](first-bot.md)から始めて、最初の `/hello` コマンドハンドラを書き、次に [モジュール開発の入門](../developer-guide/modules/getting-started.md)に進んでください。
- **まずは原理を理解したい**：[基本概念](basic-concepts.md)を読んで、アダプター / モジュール / イベントがどのように連携するかを理解してください。
- **具体的な問題を解決したい**：[一般的なタスクの例](common-tasks.md)を参照してください。ストレージ、定期的なタスク、権限制御など、そのままコピーできる完全なコード例が用意されています。
- **L1の5つの記事を読了した後**：必要に応じて [高度なトピック](../advanced/README.md) を参照してください。複雑なモジュールについては、まずその中のL2必読の4つの記事から始めてください。



### 创建第一个机器人

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



### 基础概念

# 基礎概念

> [!NOTE]
> **L1 コア必読**——ドキュメントのトップページにある「L1 コア5編」のうち第2編（モジュール開発入門 → **基礎概念** → Event ラッパークラス → 設定ファイルの説明 → 例外キャッチ）。

ユーザーがメッセージを送信してからボットが返信するまでの間に、どのコンポーネントを経由するのでしょうか？アダプターとモジュールはそれぞれ何を担当しているのでしょうか？このドキュメントを読み終えれば、ハンドラーを書く際に直面する設計上の問いに、サンプルをただ写経するのではなく自分で答えられるようになります。

## イベント駆動アーキテクチャ

ErisPulse はイベント駆動アーキテクチャを採用しており、すべてのやり取りはイベントを通じて伝達・処理されます。

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
イベントシステムに投入
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

SDK はすべての機能の統一エントリーポイントであり、コアコンポーネントへのアクセスを提供します。

```python
from ErisPulse import sdk

# コアモジュールへのアクセス
sdk.storage    # ストレージシステム
sdk.config     # 設定システム
sdk.logger     # ログシステム
sdk.adapter    # アダプターシステム
sdk.module     # モジュールシステム
sdk.router     # ルーティングシステム
sdk.client     # HTTP クライアント
sdk.lifecycle  # ライフサイクルシステム
```

> [!WARNING]
> **ルートから統一インポート**：`from ErisPulse.Core import adapter` / `import ErisPulse.Core.adapter`
> このような書き方でバインドされるのはサブモジュールではなく**マネージャーインスタンス**（`AdapterManager` シングルトン）です。`ErisPulse.Core`
> パッケージの re-export は同名のサブモジュールをシャドウイングします。テストの作成、patch、またはモジュールオブジェクト自体が必要な場合は、必ず
> `from ErisPulse import sdk` のルートインポートを使用してください（`sdk.adapter` がマネージャーインスタンスです）。

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
    
    # 返信の送信
    await event.reply(f"ユーザー: {user_id}, プラットフォーム: {platform}")
```

### 3. アダプター

アダプターは ErisPulse と外部プラットフォームの間の橋渡し役です。

**役割：**
- プラットフォームのネイティブイベントを受信
- OneBot12 標準形式に変換
- 標準形式のイベントをプラットフォームに送信

**アダプターの例：**
- Yunhu アダプター：Yunhu プラットフォームと通信
- Telegram アダプター：Telegram Bot API と通信
- OneBot11 アダプター：OneBot11 互換のアプリケーションと通信
- Email アダプター：メールの送受信を処理

### 4. モジュール

モジュールは機能拡張の基本単位であり、以下のことができます：

- イベントハンドラーの登録
- ビジネスロジックの実装
- アダプターを呼び出してメッセージを送信
- コアモジュールが提供するサービスの利用

#### モジュール検出メカニズム

ErisPulse は Python の `importlib.metadata.entry_points` を通じてインストール済みのモジュールを検出します。モジュールは `pyproject.toml` でエントリーポイントを宣言します：

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

SDK の初期化時に、すべての `erispulse.module` グループのエントリーポイントをスキャンし、モジュールクラスを `ModuleManager` に登録します。その後、依存関係に従ってトポロジカルソートし、順次初期化します。

#### 最小構成のモジュール

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

- **登録**：SDK がモジュールクラスを検出し、マネージャーに登録
- **ロード**：モジュールインスタンスを作成し、`on_load(event)` を呼び出す（`event = {"module_name": "MyModule"}`）
- **アンロード**：`on_unload(event)` を呼び出し、リソースをクリーンアップ

#### ロード戦略

`get_load_strategy()` を通じてモジュールのロード動作を宣言します：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # 遅延読み込みするかどうか（デフォルト True）
            priority=0        # ロード優先度、数値が大きいほど先に初期化
        )
```

- **`lazy_load=True`（デフォルト）**：モジュールは初めて `sdk.MyModule` でアクセスされた時に初期化され、起動時間を短縮します
- **`lazy_load=False`**：SDK 起動時に即座に初期化されます。ライフサイクルイベントのリスニングや定期タスクの実行が必要なモジュールに適しています
- **`priority`**：同じ優先度のモジュールは登録順にロードされます。数値が大きいほど先に初期化されます

> 遅延読み込みのメカニズムの詳細については、[遅延読み込みシステム](../advanced/lazy-loading.md) を参照してください。

## イベントタイプ

ErisPulse は 5 種類のイベントをサポートしています：

| イベントタイプ | デコレーター | 説明 |
|---------|--------|------|
| メッセージイベント | `@message.on_message()` | ユーザーが送信したすべてのメッセージ（個人チャット、グループチャット） |
| コマンドイベント | `@command("name")` | コマンドプレフィックスで始まるメッセージ（例：`/hello`） |
| 通知イベント | `@notice.on_friend_add()` など | システム通知（友達追加、グループメンバーの変更など） |
| リクエストイベント | `@request.on_friend_request()` など | ユーザーリクエスト（友達リクエスト、グループ招待） |
| メタイベント | `@meta.on_connect()` など | システムレベルのイベント（接続、切断、ハートビート） |

> 各イベントタイプの詳細な使い方とコード例については、[イベント処理入門](event-handling.md) を参照してください。

## コアモジュールの説明

### Storage（ストレージ）

SQLite ベースのキーバリューストアシステムで、データの永続化に使用されます。

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

`get_child()` メソッドを使用するほかに、**属性アクセス**の方法で子ロガーを作成することもできます。これはより簡潔な**シンタックスシュガー**の書き方です：

```python
# 属性アクセスで子ロガーを作成
sdk.logger.mymodule.info("モジュールメッセージ")

# ネストされたアクセスをサポート
sdk.logger.mymodule.database.info("データベースメッセージ")
```

### Router（ルーティング）

HTTP と WebSocket のルーティング管理。FastAPI + Uvicorn ベース。デコレータールーティング、ミドルウェア、グループ化、レート制限、CORS をサポートします。

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> ルーティング API の全容（WebSocket、ミドルウェア、レート制限、CORS など）については、[ルーティングマネージャー](../advanced/router.md) を参照してください。

### Client（ネットワーククライアント）

統一されたネットワーククライアントで、HTTP リクエスト、WebSocket 接続、コネクションプール管理、自動リトライ、タイムアウト制御、リクエスト統計、ライフサイクルイベント統合を集約しています。

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

> ネットワーククライアント API の全容については、[ネットワーククライアント](../advanced/client.md) を参照してください。

## SendDSL メッセージ送信

アダプターはメソッドチェーンによるメッセージ送信インターフェースを提供します。

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
# ユーザーをメンション
await yunhu.Send.To("group", "G1001").At("U2001").Text("@メッセージ")

# メッセージに返信
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("返信")

# 全員にメンション
await yunhu.Send.To("group", "G1001").AtAll().Text("お知らせ")
```

### Event の返信メソッド

Event オブジェクトは便利な返信メソッドを提供します：

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
            priority=0        # ロード優先度、数値が大きいほど先に初期化
        )
```

**遅延読み込みを無効化すべきシナリオ（`lazy_load=False`）：**
- ライフサイクルイベントをリスニングするモジュール（例：`core.init.complete`）
- 定期タスクやバックグラウンドサービスを起動するモジュール
- 他のモジュールがロードされる前に初期化を完了させる必要があるモジュール

> 遅延読み込みのメカニズムと注意事項の詳細については、[遅延読み込みシステム](../advanced/lazy-loading.md) を参照してください。

## 次のステップ

- **L1 パスに沿って続ける**：次は [Event ラッパークラス](../developer-guide/modules/event-wrapper.md) で、イベントオブジェクトのすべての読み書きメソッドを習得しましょう
- **書きながら学びたい**：[イベント処理入門](event-handling.md) ではイベントタイプ別にコピーしてすぐ使えるハンドラーの書き方を紹介しています。[よくあるタスクの例](common-tasks.md) では、永続化、定期タスク、権限制御などのよく使う機能をカバーしています



### 事件处理入门

# イベント処理入門

> [!TIP]
> **この記事を読むべきタイミング**：ロボットにメッセージ、コマンド、通知、リクエストへの反応をさせたい場合、または応答待ち／対話の実装、コマンドがなぜ実行されないかを調査する場合に読む。フレームワークの設計概要だけ知りたい場合は、[基本概念](basic-concepts.md)を参照するだけでよい。必要なければ飛ばしてもよい。

イベントハンドラーは、ロボットがユーザーのメッセージを理解し、反応する場所です。ここでは、5つのイベントタイプに分けて、直接コピーできる書き方を紹介し、パラメータ解析、権限、スロットリング、対話など、実践的なシナリオもカバーします。

## イベントタイプの概要

ErisPulse は以下のイベントタイプをサポートしています：

| イベントタイプ | 説明 | 適用場面 |
|---------|------|---------|
| メッセージイベント | ユーザーが送信するすべてのメッセージ | チャットロボット、コンテンツフィルタ |
| コマンドイベント | コマンドプレフィックスで始まるメッセージ | コマンド処理、機能の入口 |
| 通知イベント | システム通知（友達追加、グループメンバー変更など） | ホームメッセージ、ステータス通知 |
| リクエストイベント | ユーザーのリクエスト（友達リクエスト、グループ招待） | リクエストの自動処理 |
| 元イベント | システムレベルのイベント（接続、ハートビート） | 接続監視、ステータスチェック |

各タイプには、`notice.on_notice()` / `request.on_request()` / `meta.on_meta()` という汎用のレジスタがあります（このタイプの全イベントを受け取ります）。細分化されたデコレータ（例：`on_group_increase`）は、対応するサブタイプのみをサブスクライブします。細分化されたデコレータを優先的に使用してください。

## メッセージイベント処理

> **強く推奨**：イベントハンドラーの `event` パラメータに `Event` クラスの型注釈を追加してください。実行時には注釈がなくても実行できます（フレームワークがイベントインスタンスを渡します）。注釈は IDE の補完と静的チェックに役立ちます。プロジェクトルートディレクトリで `epsdk types` を実行して、型のスタブを生成することで、**モジュール/アダプターのカスタムメソッド**の補完を得ることができます（[IDE補完](../getting-started/ide-completion.md)を参照）。

### すべてのメッセージを監視

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"受信した {user_id} のメッセージ: {text}")
```

### プライベートメッセージを監視

```python
from ErisPulse.Core.Event import Event
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"こんにちは、{user_id}！これはプライベートメッセージです。")
```

### グループメッセージを監視

```python
from ErisPulse.Core.Event import Event
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ {group_id} で {user_id} がメッセージを送信しました")
```

### @メッセージを監視

```python
from ErisPulse.Core.Event import Event
@message.on_at_message()
async def at_handler(event: Event):
    # @されたユーザーのリストを取得
    mentions = event.get_mentions()
    await event.reply(f"あなたが@したユーザー: {mentions}")
```

### ワイルドカードと正規表現による監視

4つのメッセージデコレータ（`on_message` / `on_private_message` / `on_group_message` / `on_at_message`）は、`pattern`（glob ワイルドカード）と `regex`（正規表現）をサポートしています。一致しないメッセージは**ハンドラーをトリガーしません**：

```python
from ErisPulse.Core.Event import Event
# glob ワイルドカード：* 任意の文字列、? 1文字、[seq] 文字集合
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("签到成功")

# 正規表現：金額を一致させる
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"受信した金額：{event.get_text()}")

# pattern と regex が両方指定された場合、両方を一致させる必要がある
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` もこれら2つのパラメータをサポートしています（[応答待ち機能](../developer-guide/modules/event-wrapper.md#応答待ち機能)を参照）。

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

### コマンドの別名

```python
@command(["help", "h"], aliases=["帮助"], help="ヘルプ情報を表示")
async def help_handler(event):
    await event.reply("ヘルプ情報...")
```

ユーザーは以下のいずれかの方法で呼び出すことができます：
- `/help`
- `/h`
- `/帮助`

### コマンドのパラメータ

```python
@command("echo", help="メッセージを返信")
async def echo_handler(event):
    # コマンドパラメータを取得
    args = event.get_command_args()
    
    if not args:
        await event.reply("返信するメッセージを入力してください")
    else:
        await event.reply(f"あなたが言った: {' '.join(args)}")
```

パラメータは、大文字小文字の違いを保持します（大文字小文字を無視するように設定しても、コマンド名の一致は大文字小文字を無視しますが、パラメータの内容には影響しません）。

### 宣言式パラメータとオプション（args= / options=）

手動でパラメータを解析するには、自分で型変換とエラーメッセージの提示を処理する必要があります。`args=` / `options=` を宣言した後、フレームワークは権限チェックが通った後にコマンドパラメータを自動的に解析し、**名前でハンドラーに注入**します。ユーザーの入力が間違っている場合、自動的にローカライズされたエラーメッセージと用法を返し（例外が発生してクラッシュすることはありません）、`/help <コマンド>` は自動的に用法を表示します：

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

`args=` の位置パラメータの構文：`<count:int>` 必須、`[sides:int=6]` 省略可能（デフォルト値付き）。サポートされる型：

| 型 | 例 | 説明 |
|------|---------|------|
| `str` | `hello` | テキスト（デフォルト型） |
| `int` / `float` | `3` / `0.5` | 数値 |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | ブール値、対話確認（`Event.confirm()`）の確認語リストを再利用 |
| `literal` | `<mode:literal=fast|slow>` | 列挙、指定された値のみを受け入れる；省略形はデフォルトで最初の値を使用 |
| `duration` | `90s`、`1h30m`、`1d` | 時間、秒に換算された float |
| `rest` | `<text:rest>` | 残りの全テキスト（最後に位置する必要がある） |

`options=` は辞書形式で宣言されます：キーはハンドラーのパラメータ名、値はフラグ形式（複数の別名は `/` で区切る）。`bool` に注釈されたパラメータはブールフラグ（存在すれば `True`）です；それ以外（デフォルトは `str`）は値付きオプションで、`--label hello` と `--label=hello` の両方の値をサポートし、型はハンドラーの注釈に従います。オプションは最初に認識され、残りのトークンは `args=` で解析されます（`rest` はオプションを除外した後の残りのテキストをカバーします）。

**動作の要点**：

- 権限チェックはパラメータ解析の前に実行される - 権限がないユーザーは解析をトリガーしない
- 解析失敗（型が不一致 / パラメータ不足 / パラメータ過多 / 未知のオプション）は自動的にローカライズされたエラーと用法を返し、コマンドは引き続き認識される
- 宣言されたパラメータ名はハンドラーの署名に存在する必要がある、そうでなければ登録時に `ValueError` をスローする
- `args=` / `options=` を宣言しないコマンドは、動作が完全に変化しない（後方互換性）

### コマンド管理（cooldown= / rate_limit= / usage_limit= / deprecated=）

手動でクールダウン、レート制限、使用制限、廃止メッセージを宣言で置き換えることができ、これらは任意に組み合わせることができます。

**クールダウン** - 時長の書式は `args=` の `duration` 型と同じ（例：`"30s"`、`"1h30m"`、`"1d"`）：

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="今日のサインインは完了しました")
async def daily_handler(event):
    await event.reply("サインイン完了！")
```

**レート制限** - スライディングウィンドウの宣言は `"回数/時間"` の形式（例：`"5/minute"`、`"10/s"`、`"3/2m"`）：

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("検索結果")
```

**使用制限** - 期間内の総回数の上限（例：`"100/day"`、`"10/hour"`、`"500/30d"`）、上限を超えると実行を拒否：

```python
@command("translate", usage_limit="100/day", usage_limit_key="user",
         usage_limit_reply="今日の翻訳回数は上限に達しました")
async def translate_handler(event):
    ...
```

クールダウン/レート制限とは異なり、使用制限は**永続化されたストレージ**にカウントされます（KV キー `erispulse.usage.<key>`、再起動しても失われません）：
ストレージにアクセスできない場合、自動的にメモリ内カウントに退化し、警告を出します（この場合、使用制限は再起動でリセットされます）。カウントは使用制限の期間が切り替わるたびにリセットされ、モジュールがアンロードされたときにクリアされます。

**廃止** - 呼び出されたときに廃止文を自動的に返し、`deprecated_reject=True` で実行を拒否します：

```python
@command("oldcmd", deprecated="新しいコマンド /newcmd を使用してください", deprecated_reject=True)
async def old_handler(event): ...
```

キー粒度（`cooldown_key=` / `rate_limit_key=`）：`"user"`（デフォルト、同一ユーザーが共有）、`"session"`（同一セッションが共有、同じグループ）、`"global"`（すべてのユーザー、すべてのセッションが共有）。

**動作の要点**：

- クールダウン / レート制限 / 使用制限がヒットした場合、デフォルトでは**静かに破棄**されます（対称的なスコープで静かに）
- `cooldown_reply=` / `rate_limit_reply=` / `usage_limit_reply=` を宣言した場合、ヒットするとその文を返します
- コマンドがヒットした時点で認識されます - 治理がヒットしたコマンドは低優先度のメッセージハンドラーに漏れません
- 治理判定はすべての権限チェックとパラメータ解析が完了し、実際の実行の前に実行されます：権限のないユーザーはトリガーされず、パラメータエラーは消費されません
- クールダウンとレート制限を同時に宣言した場合、クールダウンが先に判定されます（クールダウンがヒットした場合、レート制限のウィンドウは占有されません）；使用制限はクールダウン/レート制限の判定後に実行されます
- `deprecated=` はデフォルトで返信文を返した後**実行を継続**します；`deprecated_reject=True` で実行を拒否します（`command.executed` フックは `success=False, error="deprecated"` と記録されます）
- `/help` のリストと単一コマンドのヘルプは自動的に廃止マークと文を表示します
- クールダウンとレート制限の状態はプロセス内メモリに保持され、モジュールがアンロードされたときに自動的にクリアされます；プロセス間共有 / 再起動時の永続化は対象外です（**使用制限のカウントは除く**——ストレージに永続化されます、上記参照）
- 登録時に検証されます（fail-fast）：構文が無効、キー粒度がホワイトリスト値、reply が主宣言と一致しない場合は `ValueError` をスローします

### ハンドラのスロットリング（throttle=）とデバウンス（debounce=）

メッセージハンドラのスパム防止宣言——同じキーのイベントは間隔内に1回しか処理されず、残りは静かに破棄されます：

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

デバウンスとスロットリングは補完的です：**ウィンドウ内では最後の1つだけ実行**され、前の待機タスクはキャンセルされます（検索候補などの「入力停止後に処理する」シナリオに適しています）：

```python
@sdk.message.on_message(debounce="2s", debounce_key="user")
async def search(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message` はすべてサポートしています；`throttle_key=` / `debounce_key=` はコマンド管理と同じキー粒度（user / session / global）を使用し、時長の書式は `duration` と同じです。スロットリングと `pattern=` / `regex=` などの既存の条件は重複して効果を発揮します（すべて満たす場合にのみトリガーされます）；間隔内に破棄されたイベントは TRACE ログに記録されます；登録時に検証されます；`throttle=` と `debounce=` は意味的に排他的です（同時に宣言すると `ValueError` をスローします）。

> **デバウンスは途中で業務を中断しない**：まだ待機ウィンドウを越えていない待機タスクのみキャンセルされます；すでに越えた、実行中のハンドラは新しいイベントによってキャンセルされません（awaitのどこでも部分的な副作用が発生しないように）。

### 依存注入（Depends）

共通の依存（データベースセッション、設定の読み取りなど）は依存関数として抽出でき、ハンドラは `Depends(依存関数)` をデフォルト値として宣言し、フレームワークは呼び出し前にコンテキストオブジェクトを使って依存関数を呼び出し、名前で注入します：

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

デフォルトで**リクエストレベルのキャッシュ**が有効です：イベントの配信内では、同じ依存関数は一度だけ解析され、すべての注入ポイントで結果を共有します（`get_db` は一度のイベントでデータベースセッションを一度だけ作成します）；リクエストをまたいで自動的に再利用されません。`Depends(get_db, use_cache=False)` を使って、依存のキャッシュを無効にできます。

フレームワークの注入ポイントをすべてオーバーライドします：コマンドハンドラ、イベントハンドラ（`message.on_message()` など）、ライフサイクルフック（`sdk.lifecycle.on`）、SSEルートハンドラ。依存関数の最初の引数は注入ポイントのコンテキストオブジェクトです（イベントの場合は `Event`、ライフサイクルの場合はイベント `data`、ルートの場合は `HttpRequest` / `SseEmitter`）；同期と非同期の依存関数を宣言できます。

**他のモジュールのサービスを宣言**（構文糖衣）：

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(モジュール名, メソッド名, *固定引数)` は、依存関数内で `sdk.module.call(...)` を呼び出すのと同等です。モジュールのインスタンス化（`__init__`）は対象外です；インスタンス化時にはコンテキストオブジェクトがありません。FastAPI でホストされる HTTP ルートは FastAPI の元の `fastapi.Depends` を使用してください。

**動作の要点**：

- 登録時に検証されます（fail-fast）：依存が呼び出せない、または `args=` / `options=` パラメータと重複する場合は `ValueError` をスローします
- 依存関数がスローする例外とハンドラ自身の例外は、同口径で処理されます（コマンドはエラーを自動的に返します）
- `Depends` を宣言しないハンドラはゼロオーバーヘッドです（配布時にリフレクションが一切ありません）
- FastAPI でホストされる HTTP ルートは FastAPI の元の `fastapi.Depends` を使用してください

### コマンドグループ

```python
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    await event.reply("モジュールを再読み込みしました")

@command("admin.stop", group="admin", help="ロボットを停止")
async def stop_handler(event):
    await event.reply("ロボットを停止しました")
```

`group` パラメータはヘルプリストの分類にのみ使用されます；上記例の `admin.reload` は**全体のコマンド名**です（ドットは命名スタイルのため、ユーザーは `/admin.reload` を入力する必要があります）。

### サブコマンド

コマンド名は**スペース区切りの複数トークン形式**に対応し、`/admin add`、`/admin user ban` などのサブコマンドを実現します：

```python
@command("admin", help="管理コマンド")
async def admin_handler(event):
    await event.reply("使い方：/admin add | /admin remove")

@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"管理者 {target} を追加しました")

@command("admin remove", aliases=["a remove"], help="管理者を削除")
async def admin_remove_handler(event):
    await event.reply("管理者を削除しました")
```

マッチングルール（**最長プレフィックスマッチ**）：

- `/admin add x` は `admin add` に優先的にマッチし、`event.get_command_args()` は `["x"]` を返します（サブコマンド名以降の引数）
- `admin` だけが登録されている場合、`/admin add x` は `admin` にマッチし、`get_command_args()` は `["add", "x"]` を返します（歴史的な動作は変更なし）
- 別名は複数トークン形式（例：`a remove`）もサポートし、単一トークンの別名（例：`a`）もサブコマンドに指定できます
- 父子コマンドが同時に登録されている場合、未登録のサブコマンド入力（例：`/admin list x`）は親コマンドにフォールバック

**権限継承**：サブコマンドに `permission` が宣言されていない場合、直近で権限が宣言された祖先コマンド（`admin`）の権限を自動的に継承します——`/admin` を保護すれば、その下のすべてのサブコマンドも自動的に保護されます；サブコマンド自身が宣言した権限が優先されます：

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="管理コマンド")
async def admin_handler(event):
    ...

# permission を再宣言する必要はありません、自動的に is_admin を継承します
@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    ...
```

注意：`master=True` と `hidden` **は継承されません**、必要であればサブコマンドで個別に宣言してください；ユーザー ACL（ホワイトリスト/ブラックリスト）はコマンドのフルネームでマッチし、glob ルールは `"admin*"` のようにサブコマンド全体をカバーできます。

`/help` のコマンド一覧では、サブコマンドは可視の親コマンドの下にインデント表示されます（`admin` → `admin add` は1段階インデント、`admin user` → `admin user ban` は2段階インデント）。

### コマンドの権限とアクセス制御

コマンドの権限は3層に分かれ、上から下へ順に判定されます（**上層が拒否すると下層は判定されません**）：

```python
# ① コマンド権限 ACL（ユーザー側設定）：コマンドのユーザーのホワイトリスト/ブラックリストに基づき、拒否時に「権限不足」を返す
# ② master=True —— フレームワークのオーナーのみ実行可能（フレームワークが自動的にチェックし、拒否時に「権限不足」を返す）
@command("restart", master=True, help="モジュールを再起動")
async def restart_handler(event):
    await event.reply("モジュールを再起動しました")

# ③ permission=呼び出し関数 —— コマンド自身の制御ロジック（True を返す場合に実行される）
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="管理パネル")
async def panel_handler(event):
    await event.reply("管理パネルへようこそ")
```

**コマンドユーザー ACL**（`ErisPulse.event.command.acl`）：ユーザーは任意のコマンドにユーザーのホワイトリスト/ブラックリストを設定でき、コマンド名は正確または glob モードでマッチし、拒否時に「権限不足」を返す：

```toml
# config.toml —— 123456 だけ restart を実行可能；666 は一律拒否
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

判定順序：`deny` がヒット → 拒否；`allow` が空でヒットしない → 拒否；ACL 設定がない場合、`event.command.default_allow` に従う（`false` = 严格モード、ACL がないと拒否；`true` の場合、`master=True` / `permission` にデフォルトで委ねる）。

実行時 API（コマンド名は glob に対応）：

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # 許可リスト
command.deny_user("restart", "onebot11", "666")       # 拒否リスト
command.remove_acl("restart")                          # ホワイトリスト/ブラックリストを削除
command.get_acl("restart")                             # 現在のリストを取得
```

> 命令ハンドラはイベントパッケージからインポートされます：`from ErisPulse.Core.Event import command`；
> または SDK イベントパッケージからアクセスすることもできます：`sdk.Event.command`（これらは同一のシングルトンです）。
> モジュール内では通常 `from ErisPulse.Core.Event import command` としてインポートされています。

コマンドやユーザー間の**イベントレベル**のアクセス制御（特定の人の、特定のグループの、特定の Bot のメッセージを受け取るかどうか）
は、スコープの**アイデンティティ次元**（`scope.identity`）を通じて実現します；**モジュールレベル**の可用性（どのモジュールが使えるか）
は、スコープの**モジュール次元**（`scope.platforms / bots / sessions`）を通じて実現します。
[スコープ（scope）](../advanced/scope.md)を参照してください。

> 建議：コマンド内部でビジネスロジックを連動させるには `master=True` / `permission` を使用します；ユーザー/グループによるアクセス制御にはスコープのアイデンティティ次元を使用します；モジュールの可用性を制御するにはスコープのモジュール次元を使用します。

### コマンドの優先度

```python
# 優先度の数値が大きいほど、実行が早くなります
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("高優先度のハンドラ")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("低優先度のハンドラ")
```

### 並列イベント処理

ErisPulse のイベントシステムは**同優先度は並列、異なる優先度は直列**のスケジューリングモデルを採用しています：

```
イベント到着
    ↓
priority=10 組: [ハンドラC || ハンドラD] 並列 → 結果をマージ
    ↓ (中断されない場合)
priority=0 組: [ハンドラA || ハンドラB] 並列 → 結果をマージ
    ↓
...
```

- **同優先度は並列**：優先度が同じ複数のハンドラは同時に実行され、処理量を向上させます
- **跨優先度は直列**：異なる優先度のグループは順番に実行されます（数値が大きいほど先に実行）、高優先度のハンドラが先に実行されます
- **Copy-On-Write**：ハンドラが変更しない限りコピーを作成せず、オーバーヘッドをゼロにします
- **競合処理**：同優先度の複数ハンドラが同じフィールドを変更した場合、最後に変更された値を使用し、警告ログを記録します
- **中断機構**：任意のハンドラが `event.done()`（デフォルト）または `event.done(claim=False)` を呼び出した後、低優先度のグループをスキップします。認知とブロッキングの違いは下記の[「リンク制御：認知とブロッキング」](#リンク制御認知とブロッキング)を参照してください。

```python
# 例：同優先度ハンドラが並列実行
@message.on_message(priority=0)
async def handler_a(event):
    # タスクAを処理
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # handler_a と並列実行
    event['result_b'] = process_b()

# 異なる優先度が直列実行
@message.on_message(priority=10)
async def handler_c(event):
    # 優先度が最も高く、最初に実行されます
    pass
```

> **並列上限**：すべてのマッチするハンドラのタスクは**即座に作成**されますが、シグナルマニュアルで**同時実行数の上限**が制限され、デフォルト値は **64**（`ErisPulse.framework.handler_max_concurrency`、ホットアップデート可能）です。上限を超えたタスクはシグナルマニュアルでキューイングされ、前のタスクが完了した後に実行されます。イベントのピーク時にはこれが「圧力調整弁」になります。
>
> **遅延ログ**：個々のハンドラが1秒以上かかる場合、フレームワークはログにWARNINGを出力します（`handler_slow`）。`wait_reply`の待機時間は処理時間から差し引かれるため、「返信を待つ」ことで誤って遅延と判定されることはありません。

## ミドルウェア：配布前に変更または拒否

ミドルウェアはイベント配布**の前**に順序実行され、ファイアウォール、リクエスト制限、イベントの脱敏などの正統な実装ポイントです：

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # 拒否：イベントは破棄され、どのハンドラにも渡されず、出力副作用もありません
    data["checked"] = True    # データを変更して配布を続ける
    # Noneを返す：配布、データは変更なし（従来の動作）
    return data
```

| 戻り値 | 行動 |
|--------|------|
| `False` | **拒否**：イベントは即座に破棄され、どのハンドラにも渡されません |
| `dict` | イベントデータを変更して配布を続ける |
| `None` | 配布、データは変更なし |

拒否された場合、フレームワークはTRACEログを出力し、`adapter.event.blocked`ライフサイクルフックをトリガーします（ミドルウェア名と完全なイベントが渡されます）、イベントがなぜ反応しなかったかを監査できます。

## コマンド配布決定チェーン：なぜコマンドが実行されないのか

1つのコマンドメッセージは次のように処理されます：**コマンドテキスト判定 → コマンド名/別名が一致（一致しなかった場合は類似語の提案）→ 一致した時点で認知 → スコープ → ユーザーACL → マスター → 権限 → クールダウン/レート制限 → 使用制限（usage）→ 廃止（deprecated, notice/rejected）→ パラメータ解析 → 実行**（ミドルウェアはイベント層で拒否できる、上節参照）。1つでも満たさなければ処理は中止されます；治験がヒットした場合、デフォルトでは静かに破棄されます；権限の拒否はユーザーに返信されます；廃止は宣言された文を返すか、拒否します。

テスト中 `ErisPulse-Testing` の `dispatch()` はこの決定チェーンを直接返します（`DispatchTrace`、`trace.explain()` は逐行因果を出力）、プロダクション環境では `ErisPulse.Core.Event.start_dispatch_trace()` を使って同じ記録を収集できます。

さらに `ErisPulse.runtime` は3つの診断APIを提供します：`explain_module(モジュール名)` は「モジュールがなぜロードされなかったか」を回答します（未登録 / ラグジュアリー / 設定で無効 / 依存が不足 / SDKのバージョンが満たさない、順に原因を示します）、`explain_event(イベント)` は「イベントがなぜ反応しなかったか」を回答します（アダプターが未登録 / アイデンティティがブロック / モジュールセッションが遮断 / コマンドが一致しない）、`explain_trace(trace_id)` は「このメッセージが返信されなかった理由」を回答します——trace-idからセッションのトランスクリプトを集めて完全な出入力タイムラインを出力し、返信されたか / 未返信 / トランスクリプトが有効化されていないかを結論づけます；`format_report()` を使って人間が読める結論をレンダリングできます。`explain_trace` は[セッショントランスクリプト](../advanced/transcript.md)に依存します、有効化されていない場合は明確にこの結論を返すか、空の結果ではなく。

## スコープフィルタリング：なぜ私のモジュールがメッセージを受け取らないのか

イベントが到着した後、2つの**静か**なフィルタがあります（どちらも返信せず、エラーも出ません）：

1. **アイデンティティ次元**（`ErisPulse.scope.identity`）：イベントが配布エントリーに到着するとき、ユーザー > グループ > Bot > アダプターの順で受け取るかどうかを判定します。
   拒否された**イベント全体**は直接破棄され、どのハンドラ（コマンドディスパッチャを含む）もトリガーされません。
2. **モジュール次元**（`ErisPulse.scope`）：イベントが特定のモジュールのハンドラ/コマンドに到着したとき、セッション > Bot > プラットフォームの順でそのモジュールが利用可能かどうかを判定し、**通過しない場合は静かにスキップ**されます。

```toml
# 例1：特定のグループのすべてのメッセージをブロードキャストしない
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# 例2：MyModuleを特定のBotにブロック
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

この場合、そのグループのメッセージが到着したとき、`MyModule` のコマンドとイベントハンドラは**すべてスケジュールされません**。これはバグではなく、フィルタリング機構です——「モジュールが反応しない」ことを調査するときは、まずスコープのアイデンティティとモジュールのバインディングをチェックしてください。

- フィルタリングログは **TRACE** レベルでのみ表示されます（`core.scope.identity_denied` / `core.scope.denied`）、デフォルトの INFO では痕跡が見えません
- フレームワークのハンドラ（コマンドディスパッチャ `scope_exempt=True`）は**モジュール次元**の影響を受けませんが、**アイデンティティ次元**の影響を受けます（イベント全体が破棄されているため）
- コマンド実行前に3つ目のフィルタがあります：コマンドユーザーACL（拒否時に「権限不足」を返す、上節参照）
- 4つ目のフィルタは**イベント上書き**（下節参照）

> [!NOTE]
> **スコープフィルタリングとイベント認知（claim）の関係**：2つの静かのフィルタはすべてハンドラが**スケジュールされる前**に発生します——フィルタでスキップされたハンドラは実行されず、当然認知状態にも影響を与えません。イベントが認知されたかどうかは、**実際に実行されたハンドラ**（コマンドが認知、返信が認知、明示的に呼び出された）によって決定されます；スコープ拒否自体は認知もブロッキングもしません（静かにスキップし、イベントは配布チェーンを完了します）。

> スコープの設定、マッチングの書式、実行時APIは [スコープ（scope）](../advanced/scope.md) を参照してください。

## イベント上書き：モジュールコードを変更せずに、任意のイベントタイプの動作を上書き

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

イベントハンドラが登録時に宣言されたパラメータ（`pattern` / `regex` / `master` / `hidden` など）は**開発者のデフォルト**です。
一括上書きシステムは、ユーザーが**イベントタイプごとに**任意のモジュールの動作を上書きできるようにします——OneBot12標準タイプ（meta / message / notice / request）とErisPulse拡張タイプ（command）それぞれに専用の上書き可能なパラメータがあります：

| イベントタイプ | 上書き可能なパラメータ | 作用 |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | テキストトリガー条件 + メッセージサブタイプホワイトリスト |
| `notice` | `detail_types` / `pattern` / `regex` | 通知サブタイプホワイトリスト + テキスト条件 |
| `request` | `detail_types` / `pattern` / `regex` | リクエストサブタイプホワイトリスト + テキスト条件 |
| `meta` | `detail_types` | メタイベントサブタイプホワイトリスト（connect / heartbeat など） |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | コマンド実装パラメータ（ユーザー優先） |
| `acl`（command専用） | `allow` / `deny` | コマンドユーザーホワイトリスト/ブラックリスト（コマンド名glob） |

```toml
# message：テキストトリガー条件を上書き（コード内の条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice：特定の通知サブタイプのみを応答
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command：実装パラメータを上書き（ユーザー優先——絞るか、展開するか）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl：コマンドユーザーホワイトリスト/ブラックリスト（globで全グループをカバー）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACLのデフォルト（false = 严格モード：ACLがないと拒否）
acl_default_allow = true
```

実行時API（`from ErisPulse.Core.Event import overrides` または `sdk.Event.overrides`，
**タイプサブネームスペース**——各タイプ対称の `set` / `get` / `delete` 三件套）：

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # messageテキスト条件
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # コマンドパラメータ
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # コマンドユーザーブラックリスト

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # 開発者デフォルトに戻す
```

- 上書き条件とハンドラコード内の条件は**同時に有効**（AND論理）；`command` パラメータは開発者宣言と**深くマージ**（上書きが優先）
- `detail_types`：イベントに `detail_type` がない場合、放行（未知のイベントを誤って殺さない）
- `pattern` / `regex`：テキストがないイベント（connect / heartbeat など）は制約を受けず、直接放行
- `command` 上書きキー `master` は同期ストレージキー `must_master` にマッピング；コマンドの無効化は `acl` deny で行う
- **キー名マッピングの説明**：`overrides.command.set("My", "restart", master=True)` のパラメータ名
  `master` は設定の別名に過ぎず、実際のストレージキーと `get()` で返されるキー名は**`must_master`** に統一されます
  （`get()` は `{"must_master": true}` を返す）——実行時の判定はストレージキーを読み取るので、`master` キー名で取得しないでください
- 設定は変更されると即座に有効化（ホットアップデート）、形式の検証がアラートされます（未知のパラメータ / 壊れた項目は無視）

## リンク制御：認知とブロッキング

> [!NOTE]
> `event.done()` / `event.mark_processed()` の `claim=` / `stop=` パラメータは ErisPulse **2.7.1+** が必要です。

ErisPulse は「認知」と「ブロッキング」の2つの正交的な概念を解き、`event.done()` で統一的に制御し、コマンド処理の周囲にログ、監査、権限などの観察層を重ねることができます。

**2つの概念の正確な定義**：

- **認知（claim）**：イベントがこのハンドラによって処理されたことをマークします（`_processed` に書き込み）。コマンドディスパッチャーは、イベントが既に認知されている場合、**重複処理を防ぎ**ます。典型的なシナリオ：コマンドがマッチした後に認知し、コマンドディスパッチャーが再度介入しないようにします。
- **ブロッキング（stop）**：イベントが**より低い優先度**のハンドラに伝播しないように阻止します（`_propagation_stopped` に書き込み）。より低い優先度のハンドラはこのイベントを見なくなります。典型的なシナリオ：より高い優先度のハンドラがイベントを完全に処理した後、より低い優先度のハンドラが実行されないようにします。

| `event.done(...)` | 認知 | ブロッキング | シナリオ |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | コマンド / ハンドラが処理を完了した標準的な方法 |
| `event.done(stop=False)` | ✔ | ✘ | 認知のみ、低優先度の観察者（ログ / 統計）が引き続き見られるようにする |
| `event.done(claim=False)` | ✘ | ✔ | ブロッキングのみ（例：ファイアウォール / レート制限）、認知はしない |

`event.done(claim=, stop=)` は `event.mark_processed(claim=, stop=)` の別名で、パラメータと動作は完全に等価です。

```python
@command("help")
async def help_cmd(event):
    event.done()            # 認知 + ブロッキング（コマンド処理の完了の標準的な方法）

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # 認知のみ：低優先度は実行される（ログ / 統計）

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # ブロッキングのみ：低優先度は実行されないが、認知はしない
```

### コマンドと返信の block 設定

**コマンドがマッチすると認知**：メッセージが登録されたコマンド名（サブコマンド/別名を含む）にマッチすると、権限や権限判定の結果に関係なく、認知され、デフォルトでブロッキングされます。権限拒否されたコマンドは、低優先度のメッセージハンドラに漏れることはありません（「コマンド拒否後に on_message が再度反応する」二重応答を防ぐ）。

ブロッキングを解除して、低優先度の観察者（ログ / 審査 / 権限）がこれらのメッセージを見られるようにするには、設定を変更できます：

```toml
[ErisPulse.event.command]
block = false   # コマンドメッセージは低優先度のハンドラに流れる

[ErisPulse.event.wait_reply]
block = false   # wait_reply で消費された返信は低優先度のハンドラに流れる
```

> 注意：`block` は**ブロッキング**（stop）のみを制御し、**認知**（claim）には影響しません——マッチしたコマンドは決してメッセージハンドラに重複して消費されません；コマンドにマッチしないメッセージは通常のメッセージハンドラに流れる。

## 通知イベント処理

### 友達追加

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "新朋友"
    await event.reply(f"欢迎添加我为好友，{nickname}！")
```

### グループメンバー増加

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"欢迎新成员 {user_id} 加入群 {group_id}")
```

### グループメンバー減少

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"成员 {user_id} 离开了群 {group_id}")
```

## リクエストイベント処理

### 友達リクエスト

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"收到好友请求: {user_id}, 附言: {comment}")
    
    # 通过适配器 API 处理请求
    # 具体实现请参考各适配器文档
```

### グループ招待リクエスト

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"收到群 {group_id} 的邀请，来自 {user_id}")
```

## 元イベント処理

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

### Bot 状態照会

適切なアダプターが元イベントを送信した後、フレームワークは自動的にBotの状態を追跡し、いつでも照会できます：

```python
from ErisPulse import sdk

# 某個 Bot 是否在线
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot 在线")

# 列出当前所有在线 Bot
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# 获取完整状态摘要
summary = sdk.adapter.get_status_summary()
```

## 交互処理

### reply メソッドを使用した返信送信

`event.reply()` メソッドは、@、返信などの機能をサポートする様々な修飾パラメータを備え、メッセージの送信を容易にします：

```python
# 簡単な返信
await event.reply("你好")

# 異なるタイプのメッセージを送信
await event.reply("http://example.com/image.jpg", method="Image")  # 画像
await event.reply("http://example.com/voice.mp3", method="Voice")  # 音声

# @1人
await event.reply("你好", at_users=["user123"])

# @複数人
await event.reply("大家好", at_users=["user1", "user2", "user3"])

# 返信
await event.reply("返信内容", reply_to="msg_id")

# @全員
await event.reply("公告", at_all=True)

# 組み合わせ: @ユーザー + 返信
await event.reply("内容", at_users=["user1"], reply_to="msg_id")
```

### ユーザーの返信を待つ

```python
@command("ask", help="询问用户")
async def ask_handler(event):
    await event.reply("请输入你的名字:")
    
    # ユーザー返信を待つ、タイムアウト30秒
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"你好，{name}！")
    else:
        await event.reply("等待超时，请重新输入。")
```

> [!TIP]
> **待機中でもコマンドは使用可能**（2.8.3+）：コマンドプレフィックスで始まり、登録済みコマンドに一致するメッセージ（例：`/cancel`）は**コマンドとして実行**され、返信として扱われず、待機は中断されません——ユーザーはいつでもキャンセル/切り替えでき、コマンド実行後も返信を続けることができます。旧来の「テキストをすべて吸収する」動作が必要な場合：設定 `ErisPulse.event.wait_reply.cmdpass = true`、または単回 `wait_reply(cmdpass=True)`。

### 認証付きの待機返信

```python
@command("age", help="询问年龄")
async def age_handler(event):
    def validate_age(event_data):
        """年齢が有効かどうかを検証"""
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

ユーザーの確認または否定を待つ、自動的に組み込みの中英確認語を認識：

```python
@command("confirm", help="确认操作")
async def confirm_handler(event):
    if await event.confirm("确定要执行此操作吗？"):
        await event.reply("已确认，执行中...")
    else:
        await event.reply("已取消")

# 自定义确认语
if await event.confirm("继续吗？", yes_words={"go", "继续"}, no_words={"stop", "停止"}):
    pass
```

### 選択メニュー (choose)

ユーザーは選択番号または選択肢を返信できます：

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

**マージモード**：`merge_prompt=True` の場合、選択肢をプロンプトに組み込み、`method` で1つのメッセージとして送信します：

```python
# Markdownで送信する場合、プロンプトに選択肢を追加
choice = await event.choose(
    "## 请选择颜色\n{options}\n请回复编号",
    ["红色", "绿色", "蓝色"],
    method="Markdown",
    merge_prompt=True,
)
```

> `{options}` は選択肢の挿入位置を制御；記載しない場合はプロンプト末尾に追加。
> `placeholder` パラメータでカスタムプレースホルダを指定できます（例：`placeholder="[choices]"`）。
> `options_format="auto"`（デフォルト）は、`method` に応じてスタイルを自動選択：Markdown→無序リスト、Html→有序リスト、その他→テキストリスト。
> テキスト系メソッド（Text/Markdown/Htmlなど）はデフォルトで選択肢を末尾にマージ；非テキスト系メソッド（Imageなど）はデフォルトで2つのメッセージに分割。

### フォーム収集 (collect)

複数ステップでユーザーの入力を収集します：

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

### 任意イベントを待つ (wait_for)

特定条件を満たす任意のイベントを待つ、同一ユーザーに限らない：

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

### 多段対話 (conversation)

対話可能な多段対話コンテキストを作成します：

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

### 組み込み確認語

ErisPulse は中英の確認語の集合を内蔵しています：

- **確認語** (`CONFIRM_YES_WORDS`): 是、yes、y、确认、确定、好、好的、ok、true、对、嗯、行、同意、没问题...
- **否定語** (`CONFIRM_NO_WORDS`): 否、no、n、取消、不、不要、不行、cancel、false、错、拒绝、不可以...

## イベントデータアクセス

### Event オブジェクトの常用メソッド

```python
@command("info")
async def info_handler(event):
    # 基本情報
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # 発信者情報
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

内蔵メソッドに加えて、各プラットフォームアダプターはプラットフォーム固有のメソッドを登録し、プラットフォーム固有のデータにアクセスしやすくします。

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # プラットフォームに応じて固有メソッドを呼び出す
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram固有メソッド
    elif platform == "email":
        subject = event.get_subject()           # 郵件固有メソッド
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
        # 予期しないエラー
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
    # 特定ユーザーのメッセージのみ処理
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # 特定のキーワードを含むメッセージのみ処理
    if "キーワード" not in event.get_text():
        return
    
    await event.reply("条件が満たされ、メッセージを処理します")
```

## 次に

- **イベントオブジェクト自体を操作したい**：[Event 包装クラスの詳細](../developer-guide/modules/event-wrapper.md)を参照し、Event 全てのメソッドの権威的なリファレンス
- **より複雑なメッセージを送りたい**：[プラットフォーム特性ガイド](../platform-guide/README.md)で SendDSL 鏈式送信、送信ルール、バッチ構築について詳しく説明；[よくあるタスクの例](common-tasks.md)にリトライ / タイムアウト / バッチの既成コードあり
- **機能を書き終えて設定とデプロイをしたい**：[ユーザー使用ガイド](../user-guide/)に進み、設定ファイルと CLI 管理はすべてそこの中にある



### 常见任务示例

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



### IDE 补全

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



====
用户指南
====


### 安装和配置

# インストールリファレンス

> [!TIP]
> **このページを読むべきタイミング**：インストール方法（pip / uv / Docker / ErisPulse-App クライアント）を選ぶ必要があるときや、インストールに失敗してトラブルシューティングが必要なときに読んでください。とにかく最速で動かしたいだけなら、[5分クイックスタート](../quick-start.md) に最短の手順がまとめられているため、不要であればスキップしてください。

## システム要件

- Python 3.10 – 3.14（3.14t のフリースレッド / GIL なしビルドは実験的なサポートであり、フレームワーク側では実験的な CI スモークテストにより継続的に監視していますが、正式な保証は行いません）
- pip または uv（推奨）
- 十分なディスク容量（最低 100MB）

## インストール方法

### 方法 1: pip を使用したインストール

```bash
# ErisPulse のインストール
pip install ErisPulse

# 最新バージョンへのアップグレード
pip install ErisPulse --upgrade
```

### 方法 2: uv を使用したインストール（推奨）

uv はより高速な Python ツールチェーンであり、開発環境での使用が推奨されています。

#### uv のインストール

```bash
# pip を使用して uv をインストール
pip install uv

# インストールの確認
uv --version
```

#### 仮想環境の作成

```bash
# プロジェクトディレクトリの作成
mkdir my_bot && cd my_bot

# Python 3.12 のインストール
uv python install 3.12

# 仮想環境の作成
uv venv
```

#### 仮想環境の有効化

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### ErisPulse のインストール

```bash
# ErisPulse のインストール
uv pip install ErisPulse --upgrade
```

### 方法 3: uv tool を使用したインストール（グローバル CLI、推奨）

`epsdk` をグローバルなコマンドラインツールとして使用したい場合、`uv tool install` が最もクリーンな方法です。epsdk は独立したツール環境で動作し、プロジェクト環境を汚染しません。

```bash
# インストール（.venv をアクティブ化する必要なく、epsdk をすぐに使用可能）
uv tool install ErisPulse

# アップグレード（または `epsdk self-update` を直接実行すると、このプロセスが自動的に実行されます）
uv tool upgrade ErisPulse
```

> [!NOTE]
> ツール環境内の `epsdk` は、プロジェクトディレクトリ内で実行された際に、自動的にプロジェクトの `.venv` を認識します。  
> `epsdk install` はコンポーネントをプロジェクト環境にインストールし、`epsdk run` はプロジェクト環境を使用してロボットを実行します。  
> フレームワーク本体はツール環境から提供され、両者は互いに干渉しません。  
> 一括インストールスクリプト（`get.erisdev.com/install.sh` / `install.ps1`）のメニューには、「グローバル CLI インストール（uv tool）」のオプションも用意されており、uv の自動インストールと手順のガイドが提供されます。

## プロジェクトの初期化とモジュールのインストール

インストールが完了したら、プロジェクトの初期化、モジュールのインストール、実行の全手順は、[5分間で始める](../quick-start.md)を参照してください。

### 方法4：ErisPulse-Appクライアントを使用する（ターミナル不要）

Python環境をインストールしたくないですか？[ErisPulse-App](../ecosystem/app.md) は公式の全プラットフォーム対応クライアントです（Android / Windows / Linux / macOS）。**スマートフォンで直接実行**でき、デスクトップ版はシステムトレイに最小化して常駐させることができます。Python実行環境とErisPulse SDKが内蔵されており、ターミナルや手動設定は不要です。

- [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) から、プラットフォームに応じてダウンロードを選択してください（Android `online`/`offline` APK、Windows `setup.exe`/`zip`、Linux `tar.gz`、macOS `zip`）
- App内でインスタンスを作成して起動し、ネイティブのインターフェースでアダプタとモジュールを管理し、モジュールストアを閲覧します

> 詳細な説明は、[ErisPulse-Appのインストールと使用方法](../ecosystem/app.md)をご覧ください。

## インストールの確認

### インストールの確認

```bash
# ErisPulse のバージョンを確認
epsdk --version
```

### テストの実行

```bash
# プロジェクトを実行
epsdk run main.py
```

上記のような出力が表示された場合、インストールが正常に完了しています。

```
[INFO] ErisPulse の初期化を開始しています...
[INFO] アダプタをロードしました: Yunhu
[INFO] モジュールをロードしました: MyModule
[INFO] ErisPulse の初期化が完了しました
```

## よくある質問

### インストールに失敗する場合

1. Pythonのバージョンがサポート範囲内か確認してください（3.10 ～ 3.14 をサポート。3.14t のフリースレッド / GIL フリービルドは実験的サポートであり、正式な保証はありません）
2. `pip install` の代わりに `uv pip install ErisPulse` を試してください
3. 権限エラーが表示される場合は、`pip install --user ErisPulse` を試すか、仮想環境を使用してください
4. 企業プロキシ環境でSSL証明書エラーが発生する場合は、`pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse` を試してください
5. ネットワーク接続が正常で、pip のパッケージソースにアクセスできることを確認してください

### 設定エラー

1. `config.toml` の構文が正しいか確認してください（TOML形式はインデントや引用符に敏感です）
2. 必須の設定項目がすべて記入されていることを確認してください
3. ターミナルのログで詳細なエラー情報を確認してください
4. `epsdk init` を使用して設定ファイルを再生成してください

### モジュールのインストールに失敗する場合

1. モジュール名のスペルが正しいか確認してください（大文字・小文字は区別されます）
2. ネットワーク接続を確認してください
3. `epsdk list-remote` で利用可能なモジュール一覧を確認してください
4. モジュールが現在使用中の SDK バージョンと互換性があることを確認してください

### Windows PowerShell の実行ポリシー

PowerShell で「このシステムではスクリプトの実行が無効になっているため、ファイルを読み込むことができません」というようなメッセージが表示される場合：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debian/Ubuntu での仮想環境作成の失敗

インストールスクリプトが「仮想環境の作成に失敗しました」というメッセージを表示し、エラー情報に `ensurepip is not available` が含まれている場合、Debian/Ubuntu ではデフォルトで `python3-venv` がインストールされていないことが原因です（システムの Python では `ensurepip` が無効化されています）：

```bash
sudo apt install python3.13-venv   # 実際の Python バージョンに対応するパッケージをインストール
# または汎用メタパッケージをインストール：
sudo apt install python3-venv
```

インストール後、インストールスクリプトを再実行してください。最新のインストールスクリプトは、この問題を検出すると自動的に確認を行い、対応するシステムパッケージのインストールを試みます。また、uv を使用することもできます（`uv venv` は `ensurepip` に依存しません）。

## 次のステップ

- **インストール後にプロジェクトを初期化し、アダプターをインストールする**：[5分クイックスタート](../quick-start.md) に沿って残りの手順を完了しましょう
- **日常的にコマンドラインでコンポーネントを管理する**：[CLI コマンドリファレンス](cli-reference.md) を参照
- **トークンの設定やポートの調整**：[設定ファイルの説明](configuration.md) をご覧ください



### CLI 命令参考

# CLI コマンドリファレンス

> [!TIP]
> **このドキュメントを参照すべきとき**：`epsdk` コマンドの引数を忘れたとき、コンポーネント管理をスクリプトに組み込みたいとき、run / stop / restart の挙動を制御したいときに参照してください。日常的に `init` / `install` / `run` しか使わない場合は、次の一点だけ覚えていれば十分です：`epsdk <コマンド> --help` でいつでも引数の説明を確認できるので、本文を通読する必要はありません。

`epsdk` は ErisPulse のコマンドラインツールです：プロジェクトの初期化、モジュールとアダプターのインストール / アップグレード、コンポーネントの対話式設定、ボットの実行と停止、環境の診断が、すべてこの 1 つのコマンドで行えます。

> **ヒント**：`epsdk`（コマンドなし）のメインヘルプはカテゴリごとにグループ化して表示されます：**プロジェクト**（init / create / run）、**コンポーネント管理**（install / uninstall / upgrade / list / list-remote / types）、**設定と診断**（config / doctor / i18n）、**その他**（self-update / version）。

---

## パッケージ管理コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | モジュール/アダプターのインストール |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | モジュール/アダプターのアンインストール |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | 指定モジュールまたはすべてをアップグレード |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | SDK 自身を更新 |

## 診断コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose] [--fix]` | 環境を診断してヘルスレポートを出力。`--fix` は自動修復を試みます |

### install

ErisPulse のモジュールまたはアダプターパッケージをインストールします。パッケージ名を指定しない場合は対話式インストール画面に入ります。

**エイリアス：** `i`, `add`

> **uv プロジェクト連携**（2.11.1+）：uv 管理下のプロジェクト内（`uv.lock` または `[tool.uv]` が存在する場合）では、
> `install` / `upgrade` / `uninstall` が自動的に `uv add` / `uv remove` へ切り替わります——依存関係は `pyproject.toml` と `uv.lock` に同期して書き込まれ、
> `uv sync` で epsdk がインストールしたコンポーネントが消えることはなくなります。失敗時は自動的に uv pip / pip 経路へフォールバックします。
> `--user` など uv が対応していない引数は直接 pip を使用します。ターゲット環境の解決順序：
> `ERISPULSE_PYTHON` → `UV_PROJECT_ENVIRONMENT` → プロジェクトの `.venv` → `UV_PYTHON` →
> `VIRTUAL_ENV` → 現在のインタープリター（`epsdk doctor` で完全な決定チェーンを確認できます）。

**引数：**

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `[package]...` | | インストールするパッケージ名。複数指定可能 |
| `--upgrade` | `-U` | インストール時に最新バージョンへアップグレード |
| `--pre` | | プレリリース版のインストールを許可 |
| `--editable` | `-e` | 編集可能モードでインストール（パスの指定が必要） |
| `--user` | | ユーザーの site-packages ディレクトリにインストール |
| `--no-deps` | | 依存関係をインストールしない |
| `--target` | `-t` | 指定したディレクトリにインストール |
| `--index-url` | | PyPI ミラーの URL を指定 |
| `--extra-index-url` | | 追加の PyPI ミラー URL（複数回指定可能） |
| `--no-cache-dir` | | キャッシュを無効化 |
| `--requirement` | `-r` | requirements ファイルからインストール |
| `--constraint` | `-c` | 制約ファイルからインストール |
| `--force-reinstall` | | 強制的に再インストール |
| `--ignore-installed` | | インストール済みパッケージを無視 |
| `--compile` | | インストール後に .pyc ファイルをコンパイル |
| `--no-compile` | | インストール後に .pyc ファイルをコンパイルしない |
| `--prefix` | | 指定したプレフィックスディレクトリにインストール |
| `--src` | | 編集可能インストール時に使用するソースディレクトリ |
| `--config-settings` | | ビルドバックエンドに渡す設定（複数回指定可能） |
| `--no-binary` | | バイナリパッケージを使用しないよう制限（形式は `:all:` など） |
| `--only-binary` | | バイナリパッケージのみ使用するよう制限（形式は `:all:` など） |
| `--prefer-binary` | | バイナリパッケージを優先選択 |
| `--build-isolation` | | ビルド分離を有効化 |
| `--no-build-isolation` | | ビルド分離を無効化 |
| `--upgrade-strategy` | | アップグレード戦略：`eager`、`only-if-needed`、`to-satisfy-only` |
| `--break-system-packages` | | システムパッケージマネージャーが管理する Python パッケージの変更を許可 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例：**

```bash
# 単一モジュールをインストール
epsdk install Weather

# 複数モジュールをインストール
epsdk install Yunhu Weather

# ミラーからインストールしてアップグレード
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 編集可能モードでインストール（開発モード）
epsdk install -e ./my-adapter
```

### uninstall

インストール済みの ErisPulse モジュールまたはアダプターパッケージをアンインストールします。パッケージ名を指定しない場合は対話式アンインストール画面に入ります。

**エイリアス：** `rm`, `remove`

**引数：**

| 引数 | 説明 |
|------|------|
| `<package>...` | アンインストールするパッケージ名。複数指定可能 |
| `--no-uv` | uv の代わりに pip を使用 |

**例：**

```bash
# 単一モジュールをアンインストール
epsdk uninstall Weather

# 複数モジュールをアンインストール
epsdk uninstall Yunhu Weather
```

### upgrade

インストール済みの ErisPulse コンポーネントをアップグレードします。パッケージ名を指定しない場合は、対話式ですべてをアップグレードします。

**エイリアス：** `up`

**引数：**

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `[package]...` | | アップグレードするパッケージ名。複数指定可能 |
| `--force` | `-f` | 確認をスキップして強制アップグレード |
| `--pre` | | プレリリース版へのアップグレードを許可 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例：**

```bash
# すべてのパッケージをアップグレード
epsdk upgrade

# 指定パッケージをアップグレード
epsdk upgrade Weather

# 強制アップグレード（確認をスキップ）
epsdk upgrade -f
```

### self-update

ErisPulse SDK 自身を最新バージョンに更新します。

**エイリアス：** `su`, `update`

**引数：**

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `[version]` | | 更新するターゲットのバージョン番号を指定 |
| `--pre` | | プレリリース版への更新を許可 |
| `--force` | `-f` | 確認をスキップして強制更新 |
| `--no-uv` | | uv の代わりに pip を使用 |

**例：**

```bash
# 最新安定版に更新
epsdk self-update

# 指定バージョンに更新
epsdk self-update 1.2.3

# プレリリース版を許可
epsdk self-update --pre

# 強制更新
epsdk self-update -f
```

> [!NOTE]
> `uv tool install ErisPulse` でインストールした場合、このコマンドは自動的に `uv tool upgrade ErisPulse` へ切り替わります（バージョン指定時は `uv tool install ErisPulse==<バージョン> --force`）。pip で直接ツール環境をアップグレードすると、その変更は uv のマニフェスト復元によって消し去られてしまいます。
> Windows での更新は新しいコンソールウィンドウで行われます：現在の CLI はツール環境のファイルロックを解除するために先に終了する必要があり、ウィンドウに完了が表示されたらターミナルを開き直してください。

---

## 情報照会コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | インストール済みコンポーネントの一覧表示 |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | リモートで利用可能なコンポーネントの一覧表示 |
| `version` | `ver` | | SDK と Python のバージョン情報を表示（`-V` と同等） |

### list

インストール済みの ErisPulse モジュールとアダプターを一覧表示します。

**エイリアス：** `l`, `ls`

**引数：**

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定：`modules`、`adapters`、`all`（デフォルト） |
| `--outdated` | `-o` | アップグレード可能なパッケージのみ表示 |

**例：**

```bash
# インストール済みのすべてのコンポーネントを一覧表示
epsdk list

# モジュールのみ一覧表示
epsdk list -t modules

# アダプターのみ一覧表示
epsdk list -t adapters

# アップグレード可能なパッケージのみ表示
epsdk list -o
```

### list-remote

リモートリポジトリで利用可能な ErisPulse モジュールとアダプターを一覧表示します。

**エイリアス：** `lsr`

**引数：**

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `--type` | `-t` | タイプを指定：`modules`、`adapters`、`all`（デフォルト） |
| `--refresh` | `-r` | リモートパッケージリストのキャッシュを強制的に更新 |

**例：**

```bash
# リモートで利用可能なすべてのコンポーネントを一覧表示
epsdk list-remote

# リモートのモジュールのみ一覧表示
epsdk list-remote -t modules

# キャッシュを強制更新してから一覧表示
epsdk list-remote -r
```

---

## 設定コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l] [--json]` | アダプター/モジュールの宣言型設定項目を対話式で設定 |

### config

アダプター/モジュールの宣言型設定項目を対話式で入力します。ウィザードはアダプター/モジュールが宣言する設定クラス（`ConfigClass` / `AccountConfigClass`）によって駆動され、フォームの自動生成と検証が行われるため、config.toml を手書きする必要はありません。

アダプターはさらにマルチアカウント（bot アカウント）管理に対応しています：アカウントの追加/編集/削除、および有効/無効の切り替えです。

**エイリアス：** `cfg`, `conf`

**引数：**

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `[name]` | | ターゲット名（アダプターのプラットフォーム名またはモジュール名）。空欄で対話選択へ |
| `--list` | `-l` | すべてのターゲットの設定状態のみ一覧表示（ウィザードには入りません） |
| `--json` | | すべてのターゲットとその設定状態を JSON で出力（CI / スクリプト用）。ウィザードには入りません |

**例：**

```bash
# すべてのアダプター/モジュールの設定状態を確認
epsdk config --list

# 設定状態を JSON で出力（CI / スクリプト用）
epsdk config --json

# 対話式でターゲットを選択して設定
epsdk config

# 指定したアダプターを直接設定
epsdk config yunhu

# 指定したモジュールを直接設定
epsdk config MyModule
```

**説明：**

- 設定状態は 4 段階に分かれます：`準備完了`（検証通過）、`未完成`（必須項目の欠落または検証失敗）、`未設定`（一度も生成されていない）、`設定なし`（ターゲットが設定クラスを宣言していない）
- フィールド値には出所が表示されます：既存の設定では `（現在:値）` と表示され、未設定の場合は schema のデフォルト値が `（デフォルト:値）` と表示されます。Enter キーを押すだけでその値が保持されます
- シークレット系フィールド（`secret` を宣言）は入力時にエコーバックされず、Enter キーで設定済みの値を保持します
- 対話選択モードでは、個々のウィザードが終了すると選択メニューに戻ります（状態は更新済み）。複数のターゲットを連続して設定でき、空欄入力で終了します
- グローバルフォームの検証に失敗し、再入力を断念した場合、そのウィザードは中断され、設定は一切書き込まれません（「有効だが設定が不完全」という中途半端な状態の発生を防ぎます）
- 保存すると即座に `config/config.toml` に書き込まれ、Dashboard と実行中の SDK のどちらからでも参照できます。実行中のアダプターで新しいアカウント設定を適用する必要がある場合は、プロセスを再起動すれば OK です
- `epsdk install`（対話式インストール）と `epsdk init` でアダプターのインストールに成功した後、設定宣言が検出されると自動的にこのウィザードへ案内します。コマンドラインでパッケージ名を直接指定してインストールした場合は、設定に関するヒントの表示のみ行います

---

## 実行制御コマンド

> [!TIP]
> `epsdk run` はプロジェクトディレクトリ内の `.venv` 仮想環境を自動検出して使用し、ボットを実行します
> （`ERISPULSE_PYTHON` 環境変数でインタープリターを明示的に指定することもできます）。`epsdk install` /
> `uninstall` / `upgrade` / `list` も同様にプロジェクトの仮想環境に対して作用します。

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `run` | `r` | `[script] [--reload] [--strict/--no-strict]` | 指定したスクリプトまたは SDK を実行 |
| `stop` | — | `[--force] [--pid PID]` | 実行中のインスタンスを停止（`epsdk run` で起動されたもの） |
| `restart` | — | `[--force] [--pid PID]` | 実行中のインスタンスを再起動（停止後、元の引数で再起動） |

### run

ErisPulse プロジェクトのスクリプトを実行するか、SDK を直接起動します。ホットリロードモードに対応しています。

**エイリアス：** `r`

**引数：**

| 引数 | 説明 |
|------|------|
| `[script]` | 実行するスクリプトファイル。指定しない場合は SDK を実行 |
| `--reload` | ホットリロードモードを有効化：ファイルの変更を監視し、コンポーネント単位のコードホットリロードを自動的にトリガーします（プロセス全体の再起動は不要）。デフォルトでは `.venv`/`.git` などのディレクトリを無視し（`ErisPulse.framework.watch_ignore_dirs` で設定可能）、プラグインディレクトリはプラグイン用ホットリロード watcher が正確に処理します |
| `--strict` / `--no-strict` | 厳格モードを一時的に有効 / 無効化（今回のみ有効、設定には書き込まれません）。デフォルトは `ErisPulse.framework.strict_mode` に従います |

**例：**

```bash
# SDK を直接実行
epsdk run

# 指定したスクリプトファイルを実行
epsdk run main.py

# ホットリロードモードで実行（ファイル変更でコードレベルのホットリロードを自動トリガー）
epsdk run main.py --reload

# SDK のホットリロードモード
epsdk run --reload

# 一時的な厳格モード：起動前セルフチェックに失敗したら終了し、フレームワークの厳格レベルは今回限り最低 1 に引き上げられます
epsdk run main.py --strict

# 一時的な寛容モード（設定で strict_mode が有効でも、今回はとりあえず動かしたい場合）
epsdk run main.py --no-strict
```

**起動前セルフチェック：** `run` は起動前に `config/config.toml` の解析可能性と、インストール済みコンポーネントの必須設定の完全性を素早くチェックします。厳格性はデフォルトで `ErisPulse.framework.strict_mode` に従います（0 以外のときはチェック失敗で終了、0 のときは警告のみで続行）。設定ファイルが存在しない場合は正常な初回起動と見なされ、通知のみで失敗とは判定されません。`--strict` で一時的に有効化：プリチェックに失敗したら終了し、同時にフレームワークの厳格レベルを今回限り最低 1 に引き上げます（不適合コンポーネントはスキップ。`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数を通じて実行プロセスに伝達され、設定ファイルには書き込まれません）。`--no-strict` はその逆で、一時的に寛容側へ切り下げます。セルフチェック自体に異常が起きた場合は自動的にスキップされ、ネットワークプローブは含まれないため、起動をブロックすることはありません。

> **`--reload` のスーパーバイズ構造**（2.11.1 以降）：`epsdk run --reload` は「スーパーバイザープロセス + リロード worker 子プロセス」構成で動作します。`.py` ファイルの保存でトリガーされるホットリロードは、すべて worker 内で完結します（排他直列・ストーム統合）。モジュール側の構文エラーは全体プリチェックで拒否され、旧インスタンスがサービスを継続します。`sdk.hard_restart()` のとき worker は終了コード 42 で終了し、スーパーバイザープロセスが理由を表示した後、自動的にまったく新しい worker を立ち上げ直します——フレームワーク本体のアップグレード後、新しいコードが即座に有効になります。

### stop

実行中の ErisPulse インスタンス（`epsdk run` で起動され、同一プロジェクトディレクトリ内で実行されているもの）を停止します。
`run` は起動時にスーパーバイザープロセスの PID、現在のフレームワーク子プロセスの PID、元の起動コマンドを
`.erispulse/runtime.json` に書き込み、`stop` はこれに基づいてインスタンスを特定します。

**停止順序：** POSIX ではまずスーパーバイザープロセスに SIGINT を送信します（Ctrl+C と同じグレースフルな終了処理パス——
finally チェーンがフレームワーク子プロセスを自動終了させます）。タイムアウト時には SIGTERM / SIGKILL へと段階的に引き上げます。Windows には
プロセスシグナルのセマンティクスがないため、先にフレームワーク子プロセスを終了させてからスーパーバイザープロセスを終了させます（スーパーバイザーが強制終了をクラッシュと誤認して
再起動してしまうのを防ぐため）。

**引数：**

| 引数 | 説明 |
|------|------|
| `--force` | グレースフル停止をスキップし、直接強制終了します |
| `--pid PID` | 対象プロセスの PID を直接指定します（実行状態ファイルを上書き。非標準の起動方法用） |

**例：**

```bash
# 現在のプロジェクトの実行インスタンスを停止
epsdk stop

# 強制終了
epsdk stop --force
```

### restart

実行中の ErisPulse インスタンスを再起動します：`stop` と同じセマンティクスで停止した後、状態ファイルに記録された
**元の起動コマンド**で再起動します（フォアグラウンドで現在のターミナルを引き継ぎ、新しいインスタンスが新しい実行状態ファイルを書き込みます）。

**コンテナ内インスタンス（PID 1）**：状態ファイルに記録されたインスタンスがコンテナのメインプロセスである場合（`pid == 1`。公式
イメージの `CMD ["epsdk", "run"]` など）は、終了しての再起動は利用できません——PID 1 が終了するとコンテナも終了するためです。この場合、
代わりにフレームワークプロセスへ `SIGUSR1` を送信し、**プロセス内ホットリスタート**（`sdk.restart()`）をトリガーします：
モジュールとアダプターのコードレベルのホットリロードが行われ、`ep i` で新しくインストールしたアダプターが即座に有効になり、コンテナはオンラインを維持します。プロセス全体の再起動
（フレームワーク自体の更新、構造的な設定変更）が必要な場合は、コンテナを再起動してください（`docker restart <コンテナ>`）。詳細は
[デプロイ → コンテナ内再起動](deployment.md#コンテナ内再起動pid-1-インスタンス) を参照してください。

**引数：** `stop` と同じ（`--force` / `--pid PID`）。

**例：**

```bash
# グレースフル再起動（pip でアダプター/モジュールをアップグレードした後にコードを反映させます。実行中のモジュールは
# sdk.reload_module / sdk.adapter.reload によるコードレベルのホットリロードも利用でき、再起動は不要です）
epsdk restart
```

> [!NOTE]
> `python main.py` のように `epsdk run` を経由しない起動方法は、実行状態ファイルを書き込みません——その種の
> プロセスはシステムツールで管理するか、`epsdk stop --pid <PID>` で PID を指定してください。

---

## プロジェクト管理コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--adapter/-a <name>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | ErisPulse プロジェクトを初期化 |
| `create` | — | `{module,adapter,pack} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f] [--local]` | モジュール/アダプターのスキャフォールドを作成。`pack` はローカルプラグインを公開可能なプロジェクトに変換 |

### init

新しい ErisPulse プロジェクトを初期化します。対話式モードとクイックモードに対応。2.8.4 以降は `pyproject.toml`（依存マニフェスト）を生成し、オプションでプロジェクトの `.venv` 仮想環境を作成してフレームワークとアダプターをインストールでき、さらに**任意のディレクトリの指定**にも対応しています。

**引数：**

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `[path]` | | ターゲットパス（親ディレクトリを含められます。例：`../apps/mybot`。名前のみの場合は `--project-name` と同等） |
| `--project-name` | `-n` | プロジェクト名 |
| `--path` | | プロジェクトの親ディレクトリ（`-n` と組み合わせて作成場所を指定） |
| `--adapter` | `-a` | インストールするアダプターを事前選択（引数の繰り返し指定またはカンマ区切りが可能）。指定した場合はアダプターの問い合わせと選択をスキップします |
| `--quick` | `-q` | クイックモード。対話式ウィザードをスキップします（デフォルトで `.venv` を作成し依存関係をインストール） |
| `--force` | `-f` | 既存の設定ファイルを強制上書き |
| `--here` | | 現在のディレクトリで初期化し、サブディレクトリを作成しません |
| `--no-uv` | | uv の代わりに pip を使用 |
| `--no-venv` | | 仮想環境の作成と依存関係のインストールをスキップ |

**例：**

```bash
# 対話式で初期化
epsdk init

# クイック初期化（現在のディレクトリに my_bot/ を作成。pyproject.toml + .venv を含む）
epsdk init -q -n my_bot

# クイック初期化＋アダプター事前インストール（非対話。スクリプト / CI 向け）
epsdk init -q -n my_bot --adapter yunhu,telegram

# 任意のディレクトリを指定して初期化（../apps/mybot）
epsdk init ../apps/mybot

# 親ディレクトリとプロジェクト名を組み合わせ
epsdk init -n my_bot --path ../apps

# 既存の設定を強制上書き
epsdk init -f

# 現在のディレクトリで初期化
epsdk init --here -n my_bot

# プロジェクト構造のみ生成し、仮想環境は作成しない
epsdk init --no-venv -n my_bot
```

init の生成物：`main.py`、`pyproject.toml`（依存マニフェスト）、`config/config.toml` + `config.full.example`、`config/ssl/`、`logs/`、`.gitignore`、`README.md`。仮想環境の作成を選択した場合は、追加で `.venv` が生成され、その中に `erispulse` と選択したアダプターがインストールされます。

> [!NOTE]
> `.gitignore` はグループ化テンプレートです：Python バイトコードとビルド成果物、仮想環境と `.env`、ツールキャッシュ、エディタとシステムファイルなどからなり、さらに**実行時ディレクトリの `config/` と `logs/` を丸ごと除外します**——`config.toml` にはアダプターのトークンなどの機密情報が含まれるため、リポジトリへのコミットは推奨されません。共有用の設定スケルトンには `config.full.example` を使用してください。

> [!WARNING]
> **`uv run epsdk run` でボットを実行しないでください**。`uv run` は `pyproject.toml` が存在しないディレクトリで実行されると**使い捨ての分離環境**を作成します——その中で `epsdk install` によりインストールされたアダプターは永続化されません。プロジェクトディレクトリ内で `epsdk run` を使用するか（プロジェクトの `.venv` を自動使用）、または先に仮想環境をアクティブ化してから実行してください。

### create

ErisPulse モジュールまたはアダプターのスキャフォールドプロジェクトを作成します。`pack` サブコマンドは、ローカルプラグイン（`plugins/` ディレクトリ）を公開可能な標準プロジェクトに変換します。

**引数：**

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `{module,adapter,pack}` | | 作成するタイプ：`module` / `adapter` / `pack`（プラグインをプロジェクトに変換）|
| `--name` | `-n` | プロジェクト名（PascalCase） |
| `--description` | `-d` | プロジェクトの説明 |
| `--author` | `-a` | 作者名 |
| `--email` | `-e` | 作者のメールアドレス |
| `--homepage` | | プロジェクトのホームページ URL |
| `--output` | `-o` | 出力ディレクトリ（デフォルトは現在のディレクトリ） |
| `--force` | `-f` | 既存のディレクトリを強制上書き |
| `--local` | | ローカルプラグインを作成（`module` / `adapter` で利用可能）：`plugins/<name>/` パッケージ構造を生成し、パッケージングなしでインストール可能 |

**例：**

```bash
# 対話式で作成（タイプの選択と情報の入力をガイド）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# ローカルプラグインを作成（プロジェクトの plugins/ ディレクトリに配置され、起動時に自動検出）
epsdk create module -n MyModule --local

# ローカルアダプタープラグインを作成（同上。パッケージング不要で開発）
epsdk create adapter -n MyAdapter --local

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# ローカルプラグインを公開可能なプロジェクトに変換（対話でプラグインを選択 → メタ情報を補完 → 標準プロジェクトを生成）
epsdk create pack

# 完全な引数指定
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 出力ディレクトリを指定
epsdk create module -n MyModule -o ./projects

# 既存のディレクトリを強制上書き
epsdk create module -n MyModule -f
```

---

## 言語コマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | CLI の表示言語を表示または切り替え |

### i18n

現在の CLI の言語を表示、対応言語の一覧表示、表示言語の切り替えを行います。引数を指定しない場合は対話式選択画面に入ります。

**エイリアス：** `language`, `lang`

**引数：**

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `[lang]` | | 切り替える言語コード（例：`zh-CN`、`en`、`ja`、`ru`） |
| `--list` | `-l` | 対応しているすべての言語を一覧表示 |

**例：**

```bash
# 対話式で言語を選択
epsdk i18n

# 英語に切り替え
epsdk i18n en

# 日本語に切り替え
epsdk i18n ja

# 対応しているすべての言語を一覧表示
epsdk i18n --list
```

---

## 型スタブコマンド

| コマンド | エイリアス | 引数 | 説明 |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | IDE 補完を有効にするための型スタブファイルを生成 |

### types

インストール済みの ErisPulse モジュールとアダプターをスキャンし、それぞれに `.pyi` 型スタブファイルを生成します。これにより、IDE で正確なコード補完と型チェックのサポートが得られます。

**エイリアス：** `t`, `stub`

**引数：**

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `--output` | `-o` | 出力パス（デフォルトは現在のディレクトリの `ep-stubs/`） |
| `--force` | | 既存のスタブファイルを強制上書き |
| `--adapters-only` | | アダプターの型スタブのみ生成 |
| `--modules-only` | | モジュールの型スタブのみ生成 |

> **注意：** `--adapters-only` と `--modules-only` は相互に排他で、同時に指定した場合は後者が有効になります。

**例：**

```bash
# インストール済みのすべてのモジュールとアダプターの型スタブを生成
epsdk types

# アダプターのスタブのみ生成
epsdk types --adapters-only

# 指定したディレクトリに出力
epsdk types -o ./typings

# 既存のファイルを強制上書き
epsdk types --force
```

---

## グローバル引数

以下の引数はすべてのコマンドに適用されます：

| 引数 | 短い引数 | 説明 |
|------|--------|------|
| `--help` | `-h` | ヘルプ情報を表示 |
| `--version` | `-V` | バージョン情報を表示 |
| `--verbose` | `-v` | 詳細な出力を表示（`-vv`/`-vvv` のように重ね指定可能） |
| `--no-color` | | カラー出力を無効化（CI / ログ収集に適する） |
| `--no-banner` | | 起動 Banner をスキップ（スクリプト呼び出し / CI 向け。非対話ターミナルと `ERISPULSE_NO_BANNER=1` の場合は自動的にサイレント化） |
| `--yes` | `-y` | すべての対話プロンプトを自動確認（非対話実行） |

---

## 環境診断

### doctor

> [!NOTE]
> このコマンドには ErisPulse **2.7.0+** が必要です。

現在の CLI 実行環境を診断し、ヘルスレポートを出力します。「なぜインストールできない / 接続できない」種の問題の切り分けに使用します。

| 引数 | 説明 |
|------|------|
| `--verbose` | 詳細な診断情報を表示 |
| `--fix` | 診断後に修復可能な問題の自動修復を試みます |

**チェック項目**：
- **Python**：インタープリターのバージョンとパス
- **インストールバックエンド**：`uv` と `pip` のどちらを使用するか
- **ターゲットインタープリター**：パッケージが実際にインストールされるターゲットの Python 環境
- **設定ファイル**：`config/config.toml` が存在するかどうか
- **コンポーネント設定**：インストール済みコンポーネントの宣言型設定の完全性（「インストールしたのに動かない」の多くは必須項目の欠落が原因）
- **設定汚染**（2.11.1+）：過去のアップグレードで残った残留キー（旧バージョンのランタイムがバインドしていたシャドウ状態キーや、遊離した設定セクション）をスキャンし、検出次第通知します
- **PyPI 接続性**：PyPI にアクセスできるか（検出されたコンポーネント数も表示）
- **システムプロキシ**：プロキシが検出されたかどうか

**自動修復（`--fix`）**：
- `config.toml` が存在しない → 現在の言語に応じた初期設定ファイルを生成（`init` によるプロジェクト作成と同じソース）
- コンポーネント設定の「未完成」 → 対話式設定ウィザードを 1 つずつ起動して必須項目を補完（非対話環境では `epsdk config <名前>` の使用を促すヒントを表示）
- 設定汚染の残留キー → 出所を明示した上で確認を経て削除（tomlclass のロスレス経路。コメントと順序は保持）
- Python バージョンが低すぎる、PyPI にアクセスできないなど人手の介入が必要な問題 → 行動提案のみ出力

```bash
# 環境診断を実行
epsdk doctor

# エイリアスを使用
epsdk diag

# 診断して自動修復を試みる
epsdk doctor --fix
```

---

## 対話式インストール

`epsdk install` をパッケージ名を指定せずに実行すると、対話式インストールに入ります：

```bash
epsdk install
```

対話画面で提供されるもの：
1. アダプターの選択
2. モジュールの選択
3. カスタムインストール

## よくある使い方

### モジュールのインストール

```bash
# 単一モジュールをインストール
epsdk install Weather

# 複数モジュールをインストール
epsdk install Yunhu Weather

# モジュールをアップグレード
epsdk install Weather -U
```

### コンポーネントの一覧表示

```bash
# すべてのコンポーネントを一覧表示
epsdk list

# アダプターのみ一覧表示
epsdk list -t adapters

# アップグレード可能なコンポーネントのみ一覧表示
epsdk list -o

# リモートで利用可能なコンポーネントを確認
epsdk list-remote
```

### コンポーネントのアンインストール

```bash
# 単一コンポーネントをアンインストール
epsdk uninstall Weather

# 複数コンポーネントをアンインストール
epsdk uninstall Yunhu Weather
```

### コンポーネントの設定

```bash
# 設定状態を確認
epsdk config --list

# 対話式でターゲットを選択して設定
epsdk config

# 指定したアダプターを設定
epsdk config yunhu
```

### コンポーネントのアップグレード

```bash
# すべてのコンポーネントをアップグレード
epsdk upgrade

# 指定したコンポーネントをアップグレード
epsdk upgrade Weather

# 強制アップグレード
epsdk upgrade -f
```

### プロジェクトの実行

```bash
# 通常実行
epsdk run main.py

# ホットリロードモード
epsdk run main.py --reload
```

### 言語の切り替え

```bash
# 対話式で言語を選択
epsdk i18n

# 直接英語に切り替え
epsdk i18n en

# 対応言語を一覧表示
epsdk i18n --list
```

### 型スタブの生成

```bash
# すべての型スタブを生成
epsdk types

# モジュールの型スタブのみ生成
epsdk types --modules-only
```

### プロジェクトの初期化

```bash
# 対話式で初期化
epsdk init

# クイック初期化
epsdk init -q -n my_bot
```

### スキャフォールドの作成

```bash
# 対話式で作成（タイプの選択と情報の入力をガイド）
epsdk create

# Module プロジェクトを直接作成
epsdk create module -n MyModule

# Adapter プロジェクトを直接作成
epsdk create adapter -n MyAdapter

# 完全な引数指定
epsdk create module -n MyModule -d "モジュールの説明" -a "作者" -e "mail@example.com"

# 既存のディレクトリを強制上書き
epsdk create module -n MyModule -f
```

## 次のステップ

- **コンポーネントをインストールしたら設定を入力**：`epsdk config` の対話式ウィザードを使うか、[設定ファイルの説明](configuration.md) を参照して手動編集
- **コードを書き終えたら IDE 補完が欲しい**：`epsdk types` を実行します。詳細は [型スタブの生成](../getting-started/ide-completion.md) を参照
- **ボットが動かない**：まず `epsdk doctor` で環境を診断し（[環境診断](#環境診断) を参照）、長期デプロイが必要な場合は [デプロイガイド](deployment.md) を参照してください



### 配置文件说明

# 設定ファイルの説明

> [!NOTE]
> **L1 コア必読**——トップページ「読むべき道筋」の5つのコアドキュメントの1つ、モジュール開発に必須。

> 本ドキュメントでは、フレームワーク自身の設定ファイル `config/config.toml` について説明します：各設定セクションの役割、どの設定がホット更新をサポートしているか、環境変数でどのように上書きできるか。サードパーティのモジュールの設定項目は、各モジュールの独自ドキュメントを参照してください。

ErisPulseは、`config/config.toml`というTOML形式の設定ファイルを使用して、プロジェクトの設定を管理します。

## 設定ファイルの位置

設定ファイルはプロジェクトのルートディレクトリの `config/` フォルダ内にあります：

```
project/
├── config/
│   └── config.toml
├── main.py
```

### 複数インスタンスの注意点とロックファイル

フレームワークの起動時に、プロジェクトルートの実行状態ディレクトリ **`.erispulse/`** 内に `config.lock` ロックファイルを作成し、プロセス終了まで保持します（複数インスタンスが同じ設定ディレクトリを共有しているかを検出するため；2.10以前は `config/` ディレクトリの `.erispulse_config.lock` が、アップグレード後に最初の起動時に自動的に削除されます）。ログに「設定ファイルが他のErisPulseインスタンスによって同時に使用されている可能性がある」という警告が出力された場合、**2つ以上のErisPulseプロセスが同じ設定ファイルを書き込んでいる**ことになります（典型的なケース：複数のコンテナが同じホストマシンの `config/` ディレクトリをマウントしている）——同時書き込みは互いに上書きするため、各インスタンスに独立した設定ディレクトリを使用してください。

### 敏感な設定はバージョン管理に含めない

設定ファイルにはトークン（token / API key）などの機密情報が含まれます：フレームワークの初期化と `epsdk init` は、`config/` ディレクトリに `.gitignore` を自動生成します（内容は一行だけ `*` —— **ディレクトリ内のすべてのファイルがバージョン管理対象外になり、無視するファイル自身も除外されます**）；既存の `.gitignore` は上書きされません。`.erispulse/` 実行状態ディレクトリ（インスタンスロック、CLI実行状態ファイル）もローカルマシンの状態に属し、プロジェクトテンプレートの `.gitignore` は既定で無視されています。

## 設定読み込みエラー処理

フレームワークは `config.toml` を読み込む際に、3つのエラー状態を区別し、**操作可能な診断情報を提供**します。静かにデフォルト設定に回帰するのではなく、警告を出力します。

| エラー状態 | 触発条件 | フレームワークの動作 |
|---------|---------|---------|
| ファイルが存在しない | `config.toml` が存在しない | 正常な初回起動、静かに空の設定を使用（警告を出力しない） |
| TOML構文エラー | ファイルは存在するが形式が無効（例：引用符が欠けている、括弧が閉じられていない） | **行番号/列番号と原因**を出力し、**前回の有効な設定を保持して実行を継続**（今回のファイルの変更は有効にならない） |
| 権限/その他のエラー | 読み込み権限がない、IOエラーなど | **明確な原因**を出力し、**前回の有効な設定を保持して実行を継続** |

> **「前回の有効な設定」はデフォルト設定とは異なる**：ファイルが破損した場合、フレームワークは**今回の起動前の最後に解析成功した設定**（実行中にホット更新でファイルを破損させた場合は、旧値を保持）を使用します。故障の対処では、設定がリセットされたと仮定しないでください。

たとえば、`port = 8000`（引用符のない文字列）のように設定を誤って書いた場合、ログは次のように出力されます：

```
[ERROR] [Config] 設定ファイル config/config.toml の構文エラー（第 3 行 第 1 列）: ...
[WARNING] [Config] 設定ファイルの読み込みに失敗しました。前回の有効な設定を使用して実行を継続します。今回のファイルの変更は有効になりません——修復後、再読み込みまたは再起動してください。
```

このように、**デフォルトのINFOレベル**で即座に問題を特定できます。なぜ設定の変更が有効にならないのか困惑する必要はありません。

> **実行中に設定ファイルを破損させた？** ロボットが実行中に `config.toml` を手動編集して構文エラーを導入した場合、フレームワークは次回の書き込み（設定のマージ）時に「設定ファイルが破損しました（構文エラー、第 X 行）、マージ書き込みができない——まず設定ファイルを修復して再起動してください」と出力します。混乱する「書き込み失敗」ではなく、待機中の設定項目は保持され、失われることはありません。

## コメントの保持と最小限の書き込み

config.tomlの**コメントとキーの順序は、フレームワークが書き込んだ後も完全に保持されます**：コード `setConfig()`、CLI設定ウィザードの保存、またはアダプタ/モジュールの初期設定テンプレートの生成など、フレームワークは対象のキーのみを変更します。あなたが書いたコメントや整理された順序は、抹消や再配置されることはありません（tomlclassの無損TOMLエンジンを使用、未触れた内容はバイト単位で保証、ファイルの元のCRLF/LF改行スタイルも変更されません）。

フレームワークは書き込み内容を最小限に抑えます：

- **フレームワークのデフォルト設定は自動的に書き込まれない**：`gc`、`scope`、`transcript`などの組み込みデフォルト値はメモリに駐留し、config.tomlには明示的に設定したキーのみが含まれ、最小化されます。完全な設定項目はプロジェクト内の `config/config.full.example` を参照し、必要に応じてconfig.tomlにコピーして変更してください（設定されていない項目は一律組み込みデフォルト値を使用し、動作は変化しません）
- **`config.full.example` の自動維持**：`epsdk init` を実行したかどうかにかかわらず、フレームワークを起動する（`epsdk run` / `main.py`）と、`config/config.full.example` が欠落している場合、自動的に完全な設定参照が生成されます；ファイルの先頭行にはフレームワークが維持するマークが付いており、生成器の内容が更新（新しい設定項目、新規インストールのコンポーネントなど）された場合、起動時に1回更新されます；先頭行を削除/変更すると、手動で管理し、フレームワークは上書きしません
- **アダプタ/モジュールの設定テンプレート**：初期化時にコメント付きのテンプレートが書き込まれます（フィールドの説明がコメントとして記述されます）；`example` というマークが付いたフィールドは書き込まれず、config.full.example に記録され、参照用です
- **宣言的なコメントの読み込み**：設定ファイル内のコメントはドキュメントそのもの——`ep doctor` と設定検証の失敗通知は、ファイル内の該当フィールドのコメント原文を参照します（コメントを手動で変更した場合でも、通知はファイルの現状に従います）。エラーが出たときに、ドキュメントを再読む必要はありません

## 環境変数による上書き

フレームワークは、`ErisPulse.*` 設定項目を**環境変数で上書き**することをサポートしています（Docker / コンテナ化 / CI 部署に適しています、`config.toml` を変更する必要はありません）。

命名規則：点区切りパス `ErisPulse.<section>.<key>` を大文字にし、`.` を `_` に置換し、`ERISPULSE_` を接頭語として付けます：

| 設定項目 | 環境変数 | 例値 |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

動作の説明：

- **優先度が最も高い**：環境変数は「設定ファイル」および「デフォルト値」を上書きし、元の値の型に応じて自動変換（`bool` / `int` / `float` / カンマ区切りの `list` / 文字列）
- **永続化されない**：上書きは実行中にのみ有効であり、`config.toml` には書き込まれない
- **ホット更新がサポートされている**：実行中に環境変数を変更した後、設定監視の再読み込みと組み合わせて有効になります

```bash
# Docker 部署の例：config.tomlを変更せず、直接ポートを上書き
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> 注：`ErisPulse.server.port` などのフレームワーク設定は `get_server_config()` などのAPIで読み取られ、環境変数の上書きの影響を受けます。

### モジュール設定の環境変数バインディング（2.9.0+）

モジュール自身の宣言的設定（`ConfigClass`）は、フィールドレベルの環境変数バインディングをサポートしています——`field(metadata=...)` で `env` を宣言します：

```python
@dataclass
class MyConfig(BaseConfig):
    api_key: str = field(default="", metadata={
        "description": "API キー",
        "env": "MYMODULE_API_KEY",   # 環境変数バインディング
    })
    retries: int = field(default=3, metadata={"env": "MYMODULE_RETRIES"})
```

動作の説明：

- **優先度**：環境変数 > `config.toml` > 宣言デフォルト値（設定ファイルのホット更新後もこの優先度が維持される）
- **型変換**：環境変数の値はフィールドの注釈に応じて自動変換される——`str` はそのまま、`int` / `float` / `bool`（`true` / `1` / `yes` / `on`）は自動変換、`list` / `dict` はJSON解析を行う；変換に失敗した場合は、その上書きは無視され（設定ファイル/デフォルト値に戻り）、警告が出力される
- **宣言1か所、どこでも有効**：設定の読み取り、ホット更新、検証は同じパイプラインを使用する；設定パネルのSchemaは `env` 名を示し、`config.toml` テンプレートのコメントも利用可能な環境変数を示す（テンプレートには環境変数の実際の値は書き込まれず、漏洩を防ぐ）
- **完全な互換性**：`env` を宣言していないフィールドは動作が変わらない；フレームワークの設定パイプラインを経ないConfigClassの直接インスタンス化は環境変数の影響を受けない

```bash
# Docker 部署の例：config.tomlを変更せず、モジュールのキーを直接注入
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **設定クラス vs モデルフィールド、どちらを使うか？** 設定クラスは「モジュールがどのように動作するか」（動作パラメータ、ホット更新）を管理し、ORMの `Field()` は「ユーザーがどのようなデータを生成したか」（データベーステーブル、クエリ）を管理する。両者は同一の制約語彙と検証エンジンを使用している；対照表は[データモデル層 · どちらの宣言を使うか](../developer-guide/orm.md#どちらの宣言を使うか)を参照してください。

## 設定のホット更新

2.7.0から、フレームワークは設定のホット更新を**体系的にサポート**するようになりました。外部から `config.toml` を変更した後（バックグラウンドのwatcherが5秒ごとにチェック）、またはコードで `setConfig()` を呼び出した後、各コンポーネントは自動的に応答します：

| コンポーネント | ホット更新がサポートされている設定 | 動作 |
|------|----------------|------|
| **ログ Logger** | `logger.level` / `log_files` / `log_dir`（セグメントパラメータを含む）/ `memory_limit` / `format` / `exclude_levels` | 変更検出付きで自動的に再適用 |
| **コマンドシステム CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | 次のメッセージで即時有効 |
| **アダプタの並列処理** | `framework.handler_max_concurrency` | キャッシュシグナルを無効化し、新値で再構築 |
| **アクティブGC** | `framework.proactive_gc_*` | 設定変更で即時GCタスクを再起動し、実行時調整/無効化/再有効化が可能 |
| **マスターシステム Master** | `master.users` | `is_master()` 検査は毎回リアルタイムで読み取り、再起動不要 |
| **モジュール/アダプタ設定** | 各々の設定項目 | `on_config_update(old, new)` コールバックをトリガー |

**再起動が必要な設定**（安全にホット切り替えできない、変更時に「プロセスを再起動後に有効」という警告が出力される）：

| 設定 | 理由 |
|------|------|
| `router.cors.*` / `router.security.*` | 中間件はサービス起動時にFastAPIに書き込まれ、実行時に安全にホット切り替えできない |
| `storage.use_global_db` | SQLiteのファイルハンドルは実行時に開かれているため、パスの切り替えは安全ではない |

> **途中で編集保存に失敗した？** `config.toml` の編集時に一時的な構文エラーが発生した場合、フレームワークは**前回の有効な設定を保持**し、診断ログを出力します。各コンポーネントに空の設定をブロードキャストして（`on_config_update` が空値を受けて誤ってデフォルトに戻るのを防ぐ）`config.toml` の変更が有効にならないようにします。

### ホット更新の内部プロセスの分解

「設定を変更した、各コンポーネントはどのように知るのか？」——背後には検出 → 再読み込み → ブロードキャストのプロセスがあります：

```mermaid
flowchart TD
    A["外部から config.toml を編集"] --> B{"誰が最初に気づく？"}
    B -->|"バックグラウンドのwatcherスレッド<br/>5秒ごとにmtimeをポーリングする"| C["_check_file_change で変更を判定"]
    B -->|"コードで設定を読み取るとき<br/>キャッシュが60秒以上経過している"| C
    C --> D["_load_config でTOMLを再解析"]
    D --> E{"解析に成功した？"}
    E -->|"失敗（構文エラー）"| F["前回の有効な設定を保持<br/>ブロードキャストは行わず、診断ログを出力"]
    E -->|"成功"| G["lifecycle.emit config.updated<br/>old_config / new_config を含む"]
    G --> H["各コンポーネントのリスナーが応答<br/>（logger / scope / コマンド / GC ...）"]
```

**2つの検出経路**（どちらか1つで十分、両方でバックアップ）：

| 経路 | 機制 | 触発タイミング |
|------|------|---------|
| バックグラウンドのwatcher | daemonスレッド `config-watcher` が**5秒**ごとに `wait` でファイルの `mtime` をポーリング | 外部でファイルを編集した後、最大5秒以内に |
| 慣性検出 | 任意の `getConfig()` が読み取るとき、キャッシュが**60秒**以上経過している場合はまずファイルをチェック | 次回の設定読み取り時 |

> **フレームワークは自分自身を誤って傷つけない**：`setConfig()` でファイルを書き込むときは、自身が書き込んだ `mtime` を記録し、watcher はそれを除外して、**外部の編集**のみを変更とみなします。

**2種類の設定変更イベント**：

| イベント | トリガー | データ | 代表的なシーン |
|------|--------|------|---------|
| `config.set` | コード / Dashboard が `setConfig()` を呼び出す | `{key, old_value, new_value}` | 単一キーの書き込み（テンプレート生成、状態記録、実行時の設定変更） |
| `config.updated` | 外部編集後のwatcher/慣性検出が検出 | `{old_config, new_config, config_file}` | 手動で `config.toml` を編集した場合 |

> `setConfig()` はデフォルトで**5秒遅延してファイルに書き込む**（複数の書き込みを1回にまとめる）；`immediate=True` で即時書き込み。watcher が外部の変更を検出した後は、メモリのキャッシュを更新するだけで、**外部の変更をファイルに書き戻すことはしない**。

**自動応答するコンポーネント一覧**（2つのイベントは通常両方をサブスクライブし、応答内容は同じ）：

| コンポーネント | 監視 | 応答 |
|------|------|------|
| Logger | `config.set` + `config.updated` | レベル/ファイル/ディレクトリセグメント/メモリ上限/フォーマット/除外レベルを再適用（変更検出付き、変更がない場合は動かない） |
| Scope | `config.updated` | スコープバインディングのキャッシュを再構築 |
| コマンドシステム | `config.updated` | プレフィックス/大文字小文字/スペースプレフィックス/must_at_bot のパラメータを再解析し、次のメッセージで有効 |
| アダプタの並列処理 | `config.set` + `config.updated` | `handler_max_concurrency` でシグナルを無効化し、再構築 |
| アクティブGC | `config.set` + `config.updated` | `proactive_gc_*` でGCバックグラウンドタスクを即時再起動 |
| アダプタ | `config.updated` にルーティング | 各アダプタの `on_config_update(old, new)` コールバック |
| モジュール | `config.updated` にルーティング | 各モジュールの `on_config_update(old, new)` コールバック |
| ストレージ | `config.updated` | `use_global_db` の変更は**警告のみ**（再起動が必要） |
| ルーター | `config.updated` | `cors.*` / `security.*` の変更は**警告のみ**（再起動が必要） |

## 設定の読み取りと削除API

### getAllConfig：全量設定のスナップショット

外部から `_cache` を直接読み取るのを避ける（外部からプライベート属性を読み取るのはバージョン互換性の保護を受けない）：

```python
config = sdk.config.getAllConfig()     # 深いコピーのスナップショット、原地変更してもフレームワークの状態に影響しない
config["ErisPulse"]["server"]["port"]
```

ビューの口径は `getConfig` と同じ：`setConfig` / `delete` による遅延書き込みも反映され、ファイルの内容と厳密に一致する。

### delConfig：設定キーの削除

`setConfig(key, None)` は値を空にするだけで、キーはファイルに残る；`delConfig` はキーをファイルから**削除**する：

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # 遅延書き込み
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # 即時書き込み
```

- ドット区切りパスをサポート；キーが存在しない場合は `False` を返す
- 書き込みはコメント保持の経路を使用、ファイルの他の内容と順序は影響を受けない
- `config.set` イベントのブロードキャストを再利用（`new_value=None`）：アダプタ / モジュールの `on_config_update` などの既存のリスナーは変更なしで削除を感知できる

## 完全な設定例

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users は2種類の書式が使用可能（どちらか1つを選択）
#   全局のマスター（すべてのプラットフォームに効果）：users = ["123456", "789012"]
#   プラットフォームごとにマスターを指定：users = { yunhu = ["123456"], telegram = ["789012"] }
users = {}

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
log_dir = ""
log_rotation = "size"
log_max_size_mb = 10
log_backup_count = 5
log_rotation_when = "midnight"
memory_limit = 1000
exclude_levels = []

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
backend = "sqlite"
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true

[ErisPulse.i18n]
language = "auto"
```

## サーバー設定

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
# コンテナ / ファイルがマウントされていない環境では、内包PEMの内容を使用（ssl_certfile/keyfileのパスよりも優先）
# ssl_cert = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
# ssl_key = """-----BEGIN PRIVATE KEY-----
# ...
# -----END PRIVATE KEY-----"""
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| host | string | 0.0.0.0 | 監聴するアドレス、0.0.0.0はすべてのインターフェースを意味する |
| port | integer | 8000 | 監聴するポート番号 |
| auto_start | boolean | true | sdk.init()の際に自動的にルーティングサーバーを起動するかどうか。falseに設定するとルーティングサーバーの起動をスキップ（純粋なイベント処理/WebUIなしの状況） |
| ssl_certfile | string | 空 | SSL証明書ファイルのパス |
| ssl_keyfile | string | 空 | SSL秘密鍵ファイルのパス |
| ssl_cert | string | 空 | **内包PEM証明書の内容**（パスではない）。ssl_keyとペアで使用する場合、ssl_certfile/ssl_keyfileのパスよりも優先される。フレームワークはSSLコンテキストを構築するために一時的にファイルを落として、すぐに削除する |
| ssl_key | string | 空 | **内包PEM秘密鍵の内容**（パスではない）、上記と同じ意味 |

> **ポートの占有は致命的なエラーではない**：起動時にportが既に占有されていることが検出された場合、フレームワークはルーティングサーバーの起動をスキップして警告を出力し、**アダプタとモジュールは照常動作する**（HTTP/WS/SSEルーティングとWebUIは利用できない）。ロボットは動くがWebUIが開かないという問題を解決する際には、まずポートを確認すること。

## マスターシステム設定

マスターシステムは「フレームワークマスター」アカウント（Bot管理者）を識別するために使用します。`master.users` は3種類の書式をサポートしています：

```toml
[ErisPulse.master]
# 書式1：全プラットフォームに効果するグローバルマスター（後で追加されるプラットフォームも含む）
users = ["123456", "789012"]

# 書式2：プラットフォームごとにマスターを指定（dict）
# users = { yunhu = ["123456"], telegram = ["789012"] }

# 書式3：グローバルマスターとプラットフォーム専用マスターを共存させる——dict中のglobalキーがグローバルマスターバケツ
# users = { global = ["123456"], yunhu = ["789012"] }
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| users | array / object | 空 | マスターのアカウントリスト。list形式は全プラットフォームに効果するグローバルマスター；dict形式はプラットフォームごとに指定（キーがプラットフォーム名、globalキーがグローバルマスターバケツ）、値は該当プラットフォームのマスターのアカウントリスト |

> **新プラットフォームについて**：list形式とdict中のglobalバケツは「定義1回、全プラットフォームに効果」であり、後で新プラットフォームを接続する必要がない；プラットフォーム専用の条目は、同名（含む前綴/通配符寛容一致）のプラットフォームにのみ効果する。master.add(None, uid)の永続化時にglobalバケツに書き込まれ、既存のプラットフォームの条目には影響しない。

コードでは `master.is_master(event)` または `master.is_master(platform, user_id)` でチェックし、毎回呼び出し時にリアルタイムで設定を読み取る（ホット更新に対応し、再起動不要）：

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("マスター、こんにちは")
```

### 判定チェーンと実行時追加削除

マスター判定チェーンは**設定マスター → 実行時記録 → providerチェーン**です：

```python
from ErisPulse.Core import master

master.is_master(event)                      # イベントから判定
master.is_master("yunhu", "123")             # 明示的に判定
master.add("yunhu", "123")                   # 実行時に追加（デフォルトは永続化；persist=Falseはメモリのみ）
master.remove("yunhu", "123")                # 削除（デフォルトは永続化）
master.list()                                # 総合：{"global": [...], "<platform>": [...]}
```

### 自定義アイデンティティソース（provider）

設定の他に、独自のアイデンティティソースを登録できます：`fn(platform, user_id) -> bool`、
組み込みアイデンティティソース（設定 + 実行時記録）がヒットしなかった場合、順次試行し、いずれかのproviderが許可すればマスターと判定されます。
アダプタの管理者インターフェース、データベースの役割など外部アイデンティティシステムと接続するのに適しています。

登録エントリ `master.provider` はデコレータ / 関数式の2種類の書き方ができ、
登録解除は登録された関数の上の `fn.unregister()` を通じて行います：

```python
from ErisPulse.Core import master

# 書き方1：デコレータ（常駐アイデンティティソース、推奨）
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # 自定義判定ロジック

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # 不要になったら登録解除

# 書き方2：関数式（モジュールロード期に登録 / アンロード期に登録解除）
fn = master.provider(admin_provider)
fn.unregister()
```

> providerの例外はキャッチされてスキップされ、アイデンティティ判定チェーンをブロックしません。
> インスタンスメソッドをバインドした関数は `unregister` が付与できないため、登録/登録解除のペアが必要な場面では**モジュールレベルの関数**を使用してください。

### ユーザー優先：マスターの有効範囲はユーザーが最終決定

コマンドの `master=True` は**開発者のデフォルト**です：ユーザーは
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false`
で絞り込みや緩和を上書きできます（[統一イベントオーバーライド設定](#統一イベントオーバーライド設定eventoverrides)を参照、ユーザーの明示的な設定が有効）。

## ログ設定

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # 明示的なログファイルリスト（log_dirと互換性あり、優先度が高い）
log_dir = ""                  # ログ出力ディレクトリ（設定すると自動的にセグメントローテーション）
log_rotation = "size"         # セグメント方法: "size" / "date" / "none"
log_max_size_mb = 10          # sizeモードの単ファイル上限（MB）
log_backup_count = 5          # 保持する履歴ログファイル数
log_rotation_when = "midnight"  # dateモードのローテーション周期: S/M/H/D/midnight
memory_limit = 1000             # 単一モジュールのメモリログ条数上限（0 = メモリログコピーを無効化）
total_memory_limit = 5000       # 全てのモジュールのメモリログ総条数上限（0 = 制限なし）。超えた場合、ローテーション戦略に従って最も古い記録を削除（最も条数が多いモジュールのキューから優先的に削除）、単一モジュールのmemory_limitとは独立して有効）
exclude_levels = ["EVENT"]
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| level | string | INFO | ログレベル：TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL（TRACE が最低レベル、フレームワーク内部の詳細なデバッグ情報を出力） |
| format | string | rich | ログ出力フォーマット：`rich`（カラー、デフォルト）、`plain`（カラーなしの純文本、ログ収集/パイプライン再転送に適している）、`json`（JSON形式、ELKなどに適している） |
| log_files | array | 空 | ログ出力ファイルのリスト（明示的なパス、セグメントしない） |
| log_dir | string | 空 | ログ出力ディレクトリ（自動作成）。設定すると、ディレクトリ内に `erispulse.log` を書き込み、`log_rotation` に従って自動的にセグメントする；`log_files` と互換性があり、`log_files` が優先される |
| log_rotation | string | size | セグメント方法：`size`（サイズで）、`date`（日付で）、`none`（セグメントしない） |
| log_max_size_mb | float | 10 | sizeモードの単ファイルサイズ上限（MB）、超過後は `.1`/`.2` にバックアップ |
| log_backup_count | integer | 5 | 保持する履歴ログファイル数、超えた古いバックアップは自動的に削除される |
| log_rotation_when | string | midnight | dateモードのローテーション周期：`S`/`M`/`H`/`D`/`midnight`（デフォルトは毎日0時） |
| memory_limit | integer | 1000 | 単一モジュールにメモリに保持するログ条数；`0` はメモリログコピーを無効化（メモリに書き込まない、既存の記録は保持される） |
| total_memory_limit | integer | 5000 | 全てのモジュールのメモリログ総条数上限；`0` は制限なし。超えた場合、ローテーション戦略に従って最も古い記録を削除（最も条数が多いモジュールのキューから優先的に削除）、単一モジュールの `memory_limit` とは独立して有効） |
| exclude_levels | array | 空 | ログレベルを無視する。無視されたログレベルは**完全に破棄**（メモリに書き込まない、ダッシュボードなどのサブスクライバーに送信しない、出力しない、ファイルに書き込まない）。ホット更新が可能 |

また、コードで動的に切り替えることも可能です：

```python
from ErisPulse.Core import logger

# サイズでセグメント：1ファイル10MB、5個保持
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# 日付でセグメント：毎日0時ローテーション、7個保持
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` とセグメント関連の設定は ErisPulse **2.8.0+** が必要です。

> **プライバシー保護**：メッセージの送受信内容は **EVENT** レベル（数値 21）で記録されます。`exclude_levels = ["EVENT"]` に設定することで、バックエンド（ダッシュボードのログパネル）が各グループ/プライベートチャットのメッセージ内容を見ることができなくなり、他のログレベルには影響しません。

設定ファイル（ホット更新が可能）だけでなく、実行時にコードで同等の機能を切り替えることもできます——`/privacy on|off` などの管理コマンドを作る必要はありません：

```python
from ErisPulse import logger

logger.exclude_level("EVENT")        # 実行時に特定のログレベルを無視（exclude_levels設定と同じ意味）
logger.allow_level("EVENT")          # そのログレベルを再有効化
logger.list_excluded_levels()        # 現在無視されているログレベルを確認
logger.set_format("json")            # JSON形式の出力に切り替え（format設定と同じ効果）
```

> [!NOTE]
> `exclude_levels` この機能は ErisPulse **2.8.0+** が必要です。

## フレームワーク設定

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | モジュールの遅延ロードを有効にするかどうか |
| uninit_timeout | integer | 30 | エレガントなシャットダウンの総タイムアウト時間（秒）、これを超えると強制終了。0はタイムアウトを設けない |
| strict_mode | integer | 0 | エスカレーションモードのレベル、下の「エスカレーションモード」を参照 |
| handler_max_concurrency | integer | 64 | イベントハンドラの最大並行タスク数、大きくすると処理能力は上がるがメモリ使用量も増える |
| handler_queue_max_pending | integer | 4096 | イベントのバースト時のキューのバックプレッシャー：1プラットフォームの待機中のハンドラタスク数の上限、超えた場合、新しいイベントのハンドラタスクは直接破棄され、WARNINGを記録する（破棄数はトラブルシューティングで確認可能）；0は上限なし |
| offline_bot_expiry | integer | 3600 | オフラインBotの記録の自動期限切れ時間（秒）、0は期限切れしない |
| plugins_dir | string / list | "plugins" | ローカルプラグインのフォルダ（プロジェクトルートからの相対パス）；プラグインの追加/削除/変更はホットリロードのwatcherによって自動的に検出される |
| watch_ignore_dirs | list | 内部リスト | ホットリロードのファイル監視で無視するディレクトリ名（`.venv`/`.git`/`__pycache__`等）；空リストは**内部リストを全体置換**、`[]`はどのディレクトリも無視しない |
| watch_include_plugin_dirs | boolean | true | `epsdk run --reload` でプラグインのディレクトリをプラグインのホットリロードのwatcherに正確に処理させ、全量監視から除外するかどうか |
| event_dedupe | boolean | true | イベントの冪等性重複除去：同じイベントIDの重複投递（接続層の再送/ゲートウェイの再発）は1回だけ配信される |
| cross_account_policy | string | "off" | 跨アカウントの重複受付ポリシー：同じ物理メッセージが複数のアカウントを通って到達した場合の処理——`off`は無関係（イベントは照常配信）；`mark`は副本来たイベントに`multi_receipt`フィールドを注入して（最初の受付イベントを指す）配信を照常行い、モジュールはそのフィールドを読んで裁決する；`drop`は副本来たイベントを配信の入口で直接破棄（フレームワーク層で重複除去、モジュールは無感覚） |

### アクティブGC設定

SDKの初期化後にアクティブGCバックグラウンドタスクが起動し、周期的にPythonのGCと内部リソースの回収（オフラインBotのクリーンアップなど）を行う。すべてのパラメータはホット更新が可能で、変更時にタスクを即時再起動する。

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | 回収の間隔（秒）、小数点以下も可能。0はアクティブGCを無効化 |
| proactive_gc_generation | integer | 0 | 通常のラウンドのGC世代（0/1/2、0..2に制限）。注意：`gc.collect(2)`は全量GCに相当し、デフォルトは0で軽量に保つ；深いGCは`proactive_gc_full_every`で周期的にトリガーされる |
| proactive_gc_full_every | integer | 20 | Nラウンドごとに全量GCを行う、0は周期的な全量GCを無効化。全量GCは`proactive_gc_memory_growth_mb`のしきい値に制約される |
| proactive_gc_memory_growth_mb | integer | 32 | 全量GCのメモリ増加のしきい値（MB）：前回の全量GC後のメモリベースライン（優先tracemalloc、次にRSS）と比較し、この値に達した場合に全量GCを実行する。0はしきい値を設けない |
| proactive_gc_idle_only | boolean | false | 有効にすると、イベントのバースト（未完了のpending handlerがある）のラウンドではPythonのGCをスキップし、メッセージ処理との競合を避ける；内部リソースの回収には影響しない |
| proactive_gc_gen0_min | integer | 500 | 通常のラウンドのGCのgen0のガベージ量の下限：`gc.get_count()[0]`がこの値より低い場合はスキップ（空のラウンドはほぼゼロコスト）。0は常にGCする |

> **2.7.1 変更**：デフォルトの `proactive_gc_generation` は `2` から `0` に調整され、`proactive_gc_full_every` は `0` から `20` に調整されました。以前は `generation=2` は毎ラウンド最重の全量GCを意味していました；新しいデフォルトはカバーゲージを維持しながら空のラウンドのオーバーヘッドを大幅に低下させます。明示的に設定された以前の値は文字通りの意味で有効です。

### エスカレーションモード

エスカレーションモードは、モジュール/アダプターがロード段階で不正または失敗した場合の処理戦略を制御します。現代のモジュール/アダプターは、それぞれの基底クラス（`BaseModule`/`BaseAdapter`）を継承する必要があります。基底クラスを継承していないコンポーネントは、フレームワークのコンテキストシステムとバックアップクリーンアップに影響を与え、リソースリークを引き起こす可能性があります。

> **2.5.2 変更**：デフォルトのレベルは `1`（スキップ）から `0`（緩和）に調整され、新規ユーザーが初期使用時に遭遇するロード問題を減らしました。基底クラスを継承していないコンポーネントは、警告を出力して試みるだけで、直接拒否されません。旧来の動作を復元するには、`strict_mode = 1` を明示的に設定してください。

| レベル | 名称 | 動作 |
|------|------|------|
| 0 | 緩和（デフォルト） | 不正は警告のみ、基底クラスを継承していないコンポーネントも試みる（旧コンポーネントの互換性） |
| 1 | エスカレーション-スキップ | 基底クラスを継承していないコンポーネントを拒否してスキップし、他の部分は正常に起動する |
| 2 | エスカレーション-致命 | すべての不正を収集して統一的に報告し、起動チェックポイントで一括して中止する |

各レベルで、「ロード/登録/初期化段階でエラーが発生した」コンポーネント自身のクラッシュは常にスキップされます。違いは以下の通りです：

- **0 → 1**：唯一の動作の違いは「基底クラスを継承していない」が「試みる」から「スキップ」になることです。
- **1 → 2**：すべての不正（基底クラスを継承していない、ロード失敗、登録失敗、初期化失敗など）が致命に昇格し、起動チェックポイントで不正リストを集めて一括して中止されます。

#### 例外リスト

いくつかのコンポーネントが一時的に移行できない場合（たとえば、依存する旧モジュールなど）、例外リストに追加することで、不正なコンポーネントでも緩和モードで読み込まれます：

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> あるコンポーネントがエスカレーションモードで拒否された場合、ログには再び読み込まれる方法（例外リストに追加するか、レベルを下げること）が明確に提示されます。

#### CLIとの連携

`epsdk run` の起動前の自己検証（設定ファイルの解析性、コンポーネントの必須設定の完全性）はデフォルトでこの設定に従います：0でない場合、検証に失敗すると起動を拒否します。0の場合は警告を出して続行します。設定を変更せずに一時的に切り替えることもできます：`epsdk run --strict` は今回の起動時に自己検証とエスカレーションレベルを同時に有効にします（レベルは上げるだけ、`ERISPULSE_FRAMEWORK_STRICT_MODE` 環境変数で実行プロセスに伝達されます）、`--no-strict` は今回の起動時に緩和モードに設定し、警告のみ出力します。

## ストレージ設定

2.8.0からストレージエンジンは3種類の非同期バックエンドをサポートし、**APIは完全に一致し、設定は1回の切り替えで可能**です：

| バックエンド | ドライバー | インストール | 特徴 |
|------|------|------|------|
| SQLite（デフォルト） | aiosqlite | 開梱即用 | 零設定、単ファイル、WAL並列 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 既存のMySQLインフラストラクチャ、多インスタンス共有 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | トランザクション能力が強く、高並列 |

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite"（デフォルト）/ "mysql" / "postgres"
use_global_db = false     # 仅 SQLite：使用包内全局数据库 data/config.db

[ErisPulse.storage.mysql]      # backend = "mysql" 时生效
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
# charset = "utf8mb4"
# pool_min = 1
# pool_max = 10

[ErisPulse.storage.postgres]   # backend = "postgres" 时生效
host = "127.0.0.1"
port = 5432
user = "erispulse"
password = ""
database = "erispulse"
# pool_min = 1
# pool_max = 10
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| backend | string | sqlite | ストレージバックエンド：`sqlite` / `mysql` / `postgres`、切り替えでコード変更なし |
| use_global_db | boolean | false | 仅 SQLite：パッケージ内グローバルデータベースを使用するか、プロジェクト独自のデータベースを使用するか |
| storage.mysql.* | table | 上記参照 | MySQL接続パラメータ（host / port / user / password / database / charset / pool） |
| storage.postgres.* | table | 上記参照 | PostgreSQL接続パラメータ（host / port / user / password / database / pool） |

環境変数での上書きもサポート（Docker / 12-factor）：`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`。

> [!TIP]
> - 接続パラメータを変更した後はフレームワークを再起動して有効にする必要がある；接続プールの作成が瞬時失敗すると指数関数的に再試行する
> - バックエンドを切り替える前に検証スクリプトで自検査を行う：`python tests/devs/test_storage_backend_verify.py --backend mysql`
> - トランザクション / ディアレクトの違い / 自定義バックエンドなど詳細な説明は[ストレージバックエンド](../advanced/storage-backends.md)を参照

## イベント設定

### コマンド設定

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| prefix | string | / | コマンドのプレフィックス |
| case_sensitive | boolean | true | 大文字小文字を区別するか（`/Help` と `/help` が異なるコマンドになるか） |
| allow_space_prefix | boolean | false | スペースをプレフィックスとして許可するか |
| must_at_bot | boolean | false | コマンドをトリガーするには@botが必要か（プライベートチャットは制限されない） |

### メッセージ設定

```toml
[ErisPulse.event.message]
ignore_self = true
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| ignore_self | boolean | true | 自身のメッセージを無視するか |

> イベントの重複除去は3層で、各層は1種類の重複を処理：`event_dedupe`（framework、同じイベントIDの重複投递）→ `ignore_self`（本節、自身のメッセージ）→ `cross_account_policy`（framework、多アカウントの内容レベルのコピー）。各層の役割は[アダプターのコアコンセプト](../developer-guide/adapters/core-concepts.md)を参照。

## 会話受信箱設定（transcript）

```toml
[ErisPulse.transcript]
enabled = true
max_per_session = 50
ttl_hours = 168.0
self_echo = "bot"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| enabled | boolean | true | 自動的に受信/送信メッセージを記録するか（無効にすると書き込みを停止し、履歴は照会可能） |
| max_per_session | int | 50 | 1セッションに保持する条数（0 = このセッションの裁断を無効化） |
| ttl_hours | float | 168.0 | グローバル保持時間（時間、0 = 永久に削除しない） |
| self_echo | string | bot | 受信botエコー（`self.user_id == user_id`、OneBotの`report-self-message`など）の処理：`bot` = botとして記録し`meta.self_echo`をマーク；`skip` = 記録しない；`user` = userとして記録（旧動作） |

> 保持戦略のリスクと監査は[会話受信箱](../advanced/transcript.md)を参照；帰属フィールド（`sender` / `meta`）と送信所属（`meta.module`）も同文書を参照。

## 国際化設定

```toml
[ErisPulse.i18n]
language = "auto"
```

| 設定項目 | 型 | デフォルト値 | 説明 |
|---------|------|---------|------|
| language | string | auto | フレームワークの内部テキストの表示言語。`auto`に設定するとシステム言語を自動検出し、`zh-CN`、`zh-TW`、`en`、`ja`、`ru`などの具体的なコードに設定することもできる |

## モジュール設定

各モジュールは設定ファイルで独自の設定を定義できます：

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

モジュール内で設定を読み取り、書き込みます：

```python
from ErisPulse import sdk

# 設定の読み取り
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# 実行時に設定を書き込む（遅延保存）
sdk.config.setConfig("MyModule.timeout", 60)

# ファイルに即時保存
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（約5秒毎に一括保存）を使用し、`immediate=True`で即時永続化する。設定の変更は`config.set`ライフサイクルイベントをトリガーする。

## スコープ設定（scope）

> [!NOTE]
> 本特性は ErisPulse **2.8.0+** が必要です。

スコープは「**どの範囲で有効か**」を宣言します——特定のプラットフォーム / Bot / セッション内でどのモジュールが有効か（① モジュール次元）、特定のユーザー / グループ / Bot / アダプターのイベントを受信するか（② アイデンティティ次元）、モジュールがどの出力呼び出しを実行できるか（③ 出力次元）：

```toml
[ErisPulse.scope]
default_allow = true        # グローバルなデフォルト（false = 明示的な拒否の厳格モード；出力次元には影響しない）
cache_size = 1024           # LRUキャッシュサイズ

# ① モジュール次元（優先度：セッション > Bot > プラットフォーム；エントリは正確/glob/正規表現: 正規表現）
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# 子レベルのバインディングはmerge = trueの時に低優先度のエントリと逐次並列（デフォルトは全体の上書き）
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② アイデンティティ次元（優先度：ユーザー > セッション > Bot > アダプター；各レベルはallowまたはdenyのいずれかを記述）
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # 該当プラットフォームの全てのイベントをエントリで破棄

[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # ユーザーのキーはglob/正規表現: 正規表現をサポート
deny = ["u_bad", "spam_*"]

# ③ 出力次元（デフォルトは全許可；ルールはインラインテーブル、エントリは正確/glob/正規表現: 正規表現をサポート）
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # 送信を全禁止
api = { allow = ["get_*"] }               # クエリ系の標準APIのみ許可
request = { deny = true }                 # リクエストの処理を禁止
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `scope.default_allow` | boolean | グローバルなデフォルト：モジュール/アイデンティティがルールにヒットしなかった場合の許可/拒否（`true`） |
| `scope.cache_size` | integer | LRUキャッシュサイズ（デフォルト 1024） |
| `scope.platforms / bots / sessions` | table | ① モジュールの3段階バインディング：`{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② アイデンティティの4段階バインディング：`{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ 出力のルール：`{allow=[...], deny=true|[...]}`（actionはsend/api/request） |

> 詳細と実行時API（次元化の`sdk.scope.set_module()` / `set_identity()` / `set_action()`、判定の`is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`、および辞書式のデフォルト`get()` / `set()` / `delete()`）は[スコープ（scope）](../advanced/scope.md)を参照してください。

## 統一イベントオーバーライド設定（event.overrides）

統一オーバーライドシステム：**イベントタイプ**ごとに任意のモジュールハンドラの動作をオーバーライドし、モジュールコードを変更せずに動作を変更します。OneBot12標準タイプ（meta / message / notice / request）と拡張タイプ（command）それぞれに独自のオーバーライド可能なパラメータがあります：

```toml
[ErisPulse.event.overrides]

# message：テキストのトリガ条件（コード内の条件とAND）
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta：detail_typeのホワイトリスト（エントリは正確/glob/正規表現: 正規表現をサポート）
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command（拡張タイプ）：実装パラメータのオーバーライド（ユーザーの優先；無効化はacl denyで）
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # 仅框架主人（false则放开开发者的主人限制）
hidden = true               # ヘルプリストで非表示
aliases = ["rs"]            # 生效の別名

# acl（command専用）：コマンドのユーザーのホワイトリスト/ブラックリスト（コマンド名はglob/正規表現: 正規表現、正確なキーが優先）
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # ユーザー識別子 "platform:user_id"
deny = ["onebot11:u_bad"]

# ACLデフォルト：ACLの設定されていないコマンドを許可（true）/厳密に拒否（false）
acl_default_allow = true
```

| 設定項目 | 型 | 説明 |
|---------|------|------|
| `event.overrides.message.<module>` | table | テキスト条件：`{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | モジュールレベルのパラメータオーバーライド（`hidden = true`などのスカラー値） |
| `event.overrides.command.<module>.<command>` | table | コマンドレベルのオーバーライド（コマンドレベルが優先） |
| `event.overrides.acl.<command名>` | table | ユーザーのホワイトリスト/ブラックリスト：`{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACLデフォルト：ACLが設定されていないコマンドを許可（`true`）/厳密に拒否（`false`） |

> 実行時API（`from ErisPulse.Core.Event import overrides`の後、各タイプのサブ名前空間で`overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()`などを呼び出し、または`sdk.Event.overrides`でアクセス）は[イベント処理入門・イベントオーバーライド](../getting-started/event-handling.md#イベントオーバーライドモジュールコードを変更せずに任意のイベントタイプの動作をオーバーライド)を参照してください。

## 次に進む

- **L1の道筋に従って**：次のドキュメント[エラーハンドリング](../advanced/errors.md)、フレームワークをクラッシュさせないエラー処理の書き方を学ぶ
- **手動でTOMLを書きたくない**：`epsdk config`のインタラクティブな設定ツールを使用して宣言的な設定項目を入力する、[CLIコマンドリファレンス・config](cli-reference.md#config)を参照
- **設定ファイルを変更したくない**：環境変数で設定項目を上書きし、[デプロイガイド](deployment.md)のDockerの使い方を参照



### 部署指南

# 部署ガイド

> [!TIP]
> **この記事を読むべきタイミング**：ロボットを長期間稼働させる場合——Docker 部署、systemd / Supervisor プロセス監視、リバースプロキシと SSL、バックアップとアップグレードはすべてここにあります。ローカル開発やデバッグ段階では必要ありません。

ロボットの開発が完了したのは始まりに過ぎません。この記事では、サーバー上に安定的にホストするための 3 つのデプロイ方法（Docker / systemd / Supervisor）と、リバースプロキシ、セキュリティ強化、バックアップをカバーしています。

## Docker 部署（推奨）

ErisPulse は公式の Docker イメージを提供しており、ErisPulse フレームワークと Dashboard 管理パネルが内蔵されています。`linux/amd64` と `linux/arm64` アーキテクチャをサポートしています。

### 早速起動

```bash
# イメージの取得
docker pull erispulse/erispulse:latest

# docker-compose.yml のダウンロード
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Dashboard のログイントークンを設定して起動
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

起動後、`http://localhost:8000/Dashboard` にアクセスし、設定したトークンをパスワードとしてログインします。

### 国内でのイメージ加速

Docker Hub にアクセスできない場合は、GitHub Container Registry を使用してイメージを取得できます：

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

`ghcr.io` のイメージを使用する場合、`docker-compose.yml` 内の `image` を変更する必要があります：

```yaml
services:
  erispulse:
    image: ghcr.io/erispulse/erispulse:latest
```

### docker-compose.yml

```yaml
services:
  erispulse:
    image: erispulse/erispulse:${ERISPULSE_TAG:-latest}
    container_name: ${CONTAINER_NAME:-erispulse}
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
      # Python パッケージディレクトリの永続化
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - LANG=${LANG:-en_US.UTF-8}
      - ERISPULSE_LANG=${ERISPULSE_LANG:-}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    # エレガントなシャットダウンはフレームワーク内のシグナル処理（SIGTERM）で完了、ここでは停止の幅広い時間制限のみ制御
    stop_grace_period: 30s
    restart: on-failure:5
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

> 以上はリポジトリのルートにある [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) と一致しています（リポジトリのバージョンには、イメージ加速と環境変数の説明コメントが追加されています）。直接ダウンロードして使用することを推奨します。

### 環境変数

| 変数 | デフォルト値 | 説明 |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard のポートマッピング |
| `ERISPULSE_TAG` | `latest` | イメージのタグ（バージョンを固定したい場合は具体的なバージョン番号を設定） |
| `CONTAINER_NAME` | `erispulse` | コンテナ名（複数インスタンスのデプロイ時にインスタンスを区別） |
| `ERISPULSE_DASHBOARD_TOKEN` | 自動生成 | Dashboard のログイントークン（強く設定することを推奨） |
| `TZ` | `Asia/Shanghai` | タイムゾーン |
| `LANG` | `en_US.UTF-8` | システム言語、起動時のインターフェース言語を自動検出 |
| `ERISPULSE_LANG` | 空 | 強制的な起動時のインターフェース言語：`zh` / `zh_TW` / `en` / `ja` / `ru`（`LANG` を上書き） |

### データの永続化

`./config` ディレクトリは設定ファイルとデータベースをマウントしており、以下の内容を含んでいます：

- `config/config.toml` — 設定ファイル
- `config/config.db` — SQLite ストレージデータベース
- `config/.packages` — Python site-packages の永続化ボリューム、フレームワーク、アダプタ、およびインストールされたモジュールを保存（最初の起動時にエントリポイントがイメージ内に含まれるバックアップから自動的に初期化され、以降のモジュールのインストールとフレームワークのホットアップデートはこのディレクトリに書き込まれます）

> **フレームワークのアップグレード（pre/rc を含む）とイメージの自己修復**：エントリポイントは、各コンテナ起動時にコアパッケージの整合性を自己チェックし、破損した場合は「ユーザーがインストールしたバージョンを優先」する原則で修復します——永続ボリューム内に明示的にインストール/アップグレードされたバージョン（例：Dashboard でインストールされた pre バージョン）は PyPI から**同じバージョンを再インストール**し、静かにイメージ内バージョンに戻ることはありません。したがって、Dashboard でフレームワークをアップグレードした後、任意回のコンテナ再起動でも目標バージョンを維持します。

## Dashboard 管理パネル

ErisPulse Docker イメージには Dashboard モジュールが内蔵されており、Web ベースの視覚的な管理インターフェースを提供します。

### 機能概要

| 機能 | 説明 |
|------|------|
| ダッシュボード | システム概要、CPU/メモリの監視、稼働時間、イベント統計 |
| ロボット管理 | 各プラットフォームのロボットのオンライン状態と情報を表示 |
| イベントの表示 | 実時イベントストリーム、タイプとプラットフォームでフィルタリング可能 |
| ログの表示 | モジュールとレベルでフィルタリングされたログビューアー |
| モジュール管理 | インストール済みのモジュールとアダプタを表示、ロード、アンロード |
| モジュールストア | リモートで利用可能なパッケージを閲覧してワンクリックでインストール |
| 設定の編集 | `config.toml` をオンラインで編集 |
| ストレージ管理 | Key-Value ストレージデータを閲覧および編集 |
| バックアップ | 設定とストレージデータのエクスポート/インポート |
| 審査ログ | すべての管理操作を記録 |

### Dashboard でモジュールをインストール

Dashboard にはモジュールストア機能が統合されており、以下の方法でモジュールをインストールできます：

1. **ストアからインストール**：リモートのモジュールリストを閲覧し、必要なモジュールを選択してワンクリックでインストール
2. **ローカルパッケージのアップロード**：`.whl` または `.zip` ファイルを直接アップロードしてインストール、開発中のモジュールのテストに便利

> **モジュール開発者の高速テストフロー**：Docker 部署後、Dashboard の「ローカルパッケージのアップロード」機能を使って、ビルドした `.whl` ファイルを直接アップロードしてテストを行うことができます。コンテナを手動で操作する必要はありません。

## プロセス監視とハードリスタート

ErisPulse のハードリスタート (`sdk.hard_restart()`) は**外部監視者**がプロセスの終了コードが 42 のときにプロセスを再起動することに依存しています——SDK 自体は新しいプロセスを起動しません。プロダクション環境では監視者を設定する必要があります。そうでないと、ハードリスタート後にプロセスが自動的に復活しません：

- Docker：公式の compose は `restart: on-failure:5` を使用しています——非ゼロ終了コードは再起動（ハードリスタートの終了コード 42 を上書き）、連続 5 回の上限で死循環を防ぎます；無制限に再起動したい場合は `unless-stopped` に変更してください
- systemd：`Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord：42 を再起動可能な終了コードに追加
- 純粋な Python でカスタム監視者を作成：`Popen` のループ + `returncode == 42` の検出

各監視者の完全な設定例と終了コード 42 の契約に関する説明は [起動フロー → 監視者ガイド](../advanced/startup.md#監視者ガイド) を参照してください。

### コンテナ内の再起動（PID 1 インスタンス）

> このセクションの機能は ErisPulse **2.12+** が必要です。

フレームワークがコンテナの主プロセス（PID 1）として実行されている場合、`epsdk restart` はプロセスを終了して再起動しません——PID 1 を終了するとコンテナが終了します。この場合、フレームワークプロセスに `SIGUSR1` を送信し、フレームワーク内でコンポーネントレベルのソフトリスタート（`sdk.restart()`）を行います：`ep i <パッケージ>` で新しくインストールされたアダプタやアップグレードされたモジュールのコードは即座にホットリロードされ有効になります。

- フレームワーク自身の更新、構造的な設定変更が必要な場合は、コンテナを再起動します：`docker restart <コンテナ>`
- `epsdk stop` は PID 1 インスタンスでは終了の意味です——コンテナも停止します（`restart` ポリシーに従って自動的に再起動するかどうかを決定）

## ヘルスチェック

SDK にはヘルスチェックエンドポイントが内蔵されています：

```bash
# ヘルスチェック
curl http://localhost:8000/health
```

公式の docker-compose.yml にはすでにヘルスチェックが内蔵されています。独自の compose ファイルを作成する際は、以下の例を参考にしてください：

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

## リバースプロキシ

Nginx などのリバースプロキシを通じて Dashboard を公開する必要がある場合：

```nginx
server {
    listen 80;
    server_name bot.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket のサポート（Dashboard の実時イベントストリームに必要）
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL には Let's Encrypt を使用できます：

```bash
sudo certbot --nginx -d bot.example.com
```

## 手動デプロイ（pip）

Docker を使用しない場合、手動でデプロイすることもできます。

### プロダクション環境の設定

```toml
# config/config.toml

[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"
log_files = ["app.log"]
memory_limit = 5000

[ErisPulse.framework]
enable_lazy_loading = true
```

### systemd (Linux)

`/etc/systemd/system/erispulse-bot.service` を作成します：

```ini
[Unit]
Description=ErisPulse Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/erispulse-bot
ExecStart=/opt/erispulse-bot/venv/bin/epsdk run main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

管理：

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

`/etc/supervisor/conf.d/erispulse-bot.conf` を作成します：

```ini
[program:erispulse-bot]
command=/opt/erispulse-bot/venv/bin/python -m ErisPulse run main.py
directory=/opt/erispulse-bot
user=bot
autostart=true
autorestart=true
stderr_logfile=/var/log/erispulse-bot/err.log
stdout_logfile=/var/log/erispulse-bot/out.log
```

### uv tool による分離デプロイ（CLI とプロジェクト環境の分離）

`uv tool install` は `epsdk` を**独立したツール環境**としてインストールし、CLI 自身とプロジェクト依存関係を完全に分離します：CLI のアップグレードはプロジェクトの `.venv` を触らず、プロジェクトの依存関係の変更も CLI に影響しません。

```bash
# 1. グローバルに CLI をインストール（自動的に epsdk / ep コマンドが利用可能になります）
uv tool install ErisPulse

# 2. プロジェクト内にロボットの依存関係のみを配置（.venv は uv で管理）
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # 必要に応じてアダプタを追加

# 3. CLI を使って実行（自動的にプロジェクトの .venv の解釈子を検出して使用）
epsdk run main.py
```

動作の要点：

- `epsdk run` の対象解釈子の解析順序は：`ERISPULSE_PYTHON` 環境変数 → プロジェクト `.venv` → 現在の解釈子；ツール環境は CLI だけを保持し、コンポーネント（アダプタ/モジュール）はプロジェクトの `.venv` にインストールするべきです
- `epsdk install` / `uninstall` / `upgrade` / `list` も同様にプロジェクトの `.venv` に作用し、ツール環境を汚染しません
- CLI のアップグレード：`uv tool upgrade ErisPulse`（または `epsdk self-update`、uv tool 環境下では自動的に `uv tool upgrade` に切り替わります）；プロジェクトの依存関係のアップグレード：プロジェクトディレクトリ内で `uv sync` / `uv add` を実行し、互いに影響しません
- サーバー環境ではツール環境は uv で統一管理されます（`uv tool list` で確認、`uv tool upgrade --all` で一括アップグレード）、手動でグローバルな pip パッケージを管理する必要はありません
- プロジェクトのないディレクトリで `uv run epsdk ...` を実行する場合、**一時的な隔離環境**に落ちます（インストールしたコンポーネントは永続化されません）；サーバーでは常に `epsdk` を直接呼び出すか、まず `cd` でプロジェクトディレクトリに移動するべきです

## セキュリティに関する推奨事項

1. **Dashboard トークンの設定**：強力なランダムなトークンを使用し、デフォルト値は使用しないでください。
2. **ポートをパブリックに公開しない**：リバースプロキシ + SSL を使用しない限り、Dashboard のポートをローカルネットワークに限定してください。
3. **データディレクトリの保護**：`config/` ディレクトリには設定とデータベースが含まれており、適切なファイル権限を設定してください。
4. **定期的な更新**：`epsdk self-update` を使用するか、最新の Docker イメージを取得してください。
5. **root で実行しない**：手動でのデプロイ時には専用ユーザーを作成してください。
6. **Docker の再起動ポリシーの使用**：公式の compose では `restart: on-failure:5` が設定されており、例外的な終了（ハードリセット終了コード 42 を含む）後も自動的に再起動されます。
7. **API ドキュメントエンドポイントの無効化**：`/docs`、`/redoc`、`/openapi.json` はデフォルトで有効で認証がされていないため、パブリック環境で展開する場合は `router.disable_docs()` を呼び出して無効化してください。
8. **Webhook の署名検証**：スキャフォールディングで生成された `verify_request` はデフォルトで許可されていますが、パブリックなコールバックを接続する前に、署名またはトークン検証を実装する必要があります。
9. **セキュリティモデルの境界**：マスター/スコープ体系はプラットフォーム側のユーザーを制約します。ロードされたモジュールは信頼できるコードと見なされます（スコープが設定されていない場合はデフォルトで許可され、モジュールはプロバイダーを登録できます）。信頼できないモジュールをロードしないでください。

## 多インスタンスデプロイ

複数のロボットインスタンスを実行する場合：

1. 各インスタンスは独立したプロジェクトディレクトリと `docker-compose.yml` を使用します。
2. 異なるポート番号を使用します：`ERISPULSE_PORT=8001`
3. 異なるコンテナ名を使用します：`container_name: erispulse-bot2`

> **ストレージバックエンドの注意点**：インスタンス間でステート（セッション受信箱 / ダイアログチェックポイント / コマンドクールダウン）は共有されません（すべてインスタンスのメモリ状態です）。
> 既定の SQLite は単一ファイルのバックエンドであり、**複数インスタンスで同時に開くことはできません**。各インスタンスの `config/` ディレクトリは独立している必要があります。mysql / postgres に切り替えても、それぞれ独立したデータベースになります。現在のバージョンでは、複数インスタンスによる協調（セッション共有 / ロードバランシング）はサポートしていません。同じグループに複数インスタンスが存在する場合、それぞれが個別に応答します。重複を防ぐには、プラットフォーム側または業務側で独自に重複除去を行う必要があります。

## 更新とメンテナンス

### Docker 方式

```bash
# 最新のイメージを取得
docker compose pull

# 新しいイメージを使用して再起動
docker compose up -d
```

### pip 方式

```bash
epsdk self-update
epsdk upgrade
```

### uv tool 方式

```bash
# CLI ツール環境のアップグレード
uv tool upgrade ErisPulse

# プロジェクト依存関係のアップグレード（プロジェクトディレクトリ内で実行）
uv sync
```

### 実行時ホットリロードサーバー設定

リスニングアドレス / ポート / SSL 証明書を変更した後は、プロセスを再起動せずに実行します。任意のコルーチンで `router.reload()` を呼び出します：

```python
await sdk.router.reload(port=9000)                                # ポート変更
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # 証明書のホット交換（証明書の更新シーン）
await sdk.router.reload(host="0.0.0.0", port=9000)                # 省略引数は現在の設定を引き継ぐ
```

- 同じ FastAPI アプリケーションを再利用し、モジュールが登録した HTTP / WebSocket / SSE ルートはすべて保持されます
- 新しい設定（証明書が構築可能、ポートが利用可能）を先に検証してから切り替えます；失敗した場合は旧設定でサービスを復元して `False` を返し、戻り値が `False` = 旧サービスが利用可能であることを保証します
- サーバーが実行されていない場合は `False` を返します（初期起動は `sdk.router.start()` を使用してください）

### バックアップ

定期的に `config/` ディレクトリをバックアップします：

```bash
# Docker 部署
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# または Dashboard の「バックアップ」機能を使ってエクスポート
```

## 次のステップ

- **デプロイ後に可視化管理をしたい**：[ErisPulse-Dashboard](../ecosystem/dashboard.md) をインストールし、ブラウザ上でモジュール、ログ、設定を管理します
- **環境に問題があると疑う**：まず `epsdk doctor` を実行して健康状態レポートを出力し、[CLI コマンドリファレンス · doctor](cli-reference.md#doctor) を参照します
- **フレームワークとコンポーネントの設定を調整したい**：[設定ファイルの説明](configuration.md)を参照し、環境変数の上書きは特にコンテナデプロイに適しています



=====
开发者指南
=====


### 开发者指南总览

# 開発者ガイド

> [!TIP]
> **このドキュメントをいつ読むべきか**：ErisPulse 向けの拡張機能——ボットに機能（モジュール）を追加する、または新しいプラットフォーム（アダプター）に接続する——を開発する準備をしている時に読んでください。ボットを利用するだけなら読み飛ばして、[クイックスタート](../quick-start.md)を直接ご覧ください。

ここからあなたの開発パスを見つけましょう：**モジュール開発**ではコマンドやメッセージハンドラーでボットの機能を拡張でき、**アダプター開発**ではボットを新しいメッセージプラットフォームに接続できます。どちらのパスも、プロジェクトの作成からテスト、公開までの完全な流れを網羅しています。

## 目次

### モジュール開発

1. [モジュール開発入門](modules/getting-started.md) - 最初のモジュールを作成する
2. [モジュールのコア概念](modules/core-concepts.md) - モジュールの核心的な概念とアーキテクチャ
3. [Event ラッパークラス詳解](modules/event-wrapper.md) - Event オブジェクトの完全な説明
4. [モジュールのベストプラクティス](modules/best-practices.md) - 高品質なモジュールを開発するための提案
5. [データモデル層（ORM）](orm.md) - モジュール開発の応用編：宣言的モデル、自動テーブル作成と CRUD

### アダプター開発

1. [アダプター開発入門](adapters/getting-started.md) - 最初のアダプターを作成する
2. [アダプターのコア概念](adapters/core-concepts.md) - アダプターの核心的な概念（start() の2つの書き方と PollingAdapter / WebhookAdapter 接続モード基底クラスを含む）
3. [SendDSL 詳解](adapters/send-dsl.md) - Send メッセージ送信 DSL の完全な説明
4. [イベントコンバーター](adapters/converter.md) - イベントコンバーターの実装
5. [アダプターのベストプラクティス](adapters/best-practices.md) - 高品質なアダプターを開発するための提案

### テストとトラブルシューティング

1. [モジュールテスト（ErisPulse-Testing）](testing.md) - TestBot、イベントファクトリとアサーションインターフェース

### 一般的な規格

1. [設定と UI メタデータ](configuration.md) - 宣言的設定：widget / 条件付き表示・非表示 / 値の形式 / 互換性契約（アダプターとモジュール共通）

### 公開ガイド

- [公開とモジュールストアガイド](publishing.md) - あなたの作品を PyPI と ErisPulse モジュールストアに公開する

## 開発の準備

開発を始める前に、以下を確認してください：

1. [基本概念](../getting-started/basic-concepts.md)を読んでいること
2. [イベント処理](../getting-started/event-handling.md)に精通していること
3. 開発環境（Python >= 3.10）がインストールされていること
4. ErisPulse SDK がインストールされていること

## 開発タイプの選択

ニーズに応じて適切な開発タイプを選択してください：

| 開発タイプ | 適用シーン | 入門ガイド |
|---------|---------|---------|
| **モジュール開発** | ボット機能の拡張、ビジネスロジックの実装、コマンドとメッセージ処理の提供 | [モジュール開発入門](modules/getting-started.md) |
| **アダプター開発** | 新しいメッセージプラットフォームへの接続、クロスプラットフォーム通信の実現、プラットフォーム固有機能の提供 | [アダプター開発入門](adapters/getting-started.md) |

> ボットの機能を拡張したい場合（コマンドの追加やメッセージ処理など）は、**モジュール開発**を選択してください。ボットを新しいプラットフォームに接続する必要がある場合は、**アダプター開発**を選択してください。

## 開発ツール

### プロジェクトテンプレート

ErisPulse は参考としてサンプルプロジェクトを提供しています：

- [モジュールサンプル](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module) - モジュールの完全なプロジェクト構造（コマンド / 設定 / ORM / 依存性注入）
- [Web 機能サンプル](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module-web) - ルーティングデコレーター / ミドルウェア / WebSocket フック / router.app エスケープハッチ
- [インタラクション応用サンプル](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module-interactive) - メッセージトランザクションと受領確認 / ORM 複合一意制約とトランザクション / リクエスト承認 / 送信チェーン
- [運用ガバナンスサンプル](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module-ops) - スレッドタスクの帰属 / 遅延タスク / メモリチェック / プライバシースイッチ
- [アダプターサンプル](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter) - アダプターの完全なプロジェクト構造（[ポーリング](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter-polling) / [Webhook](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter-webhook) バリアントもあり）

### 開発モード

ホットリロードモードで開発すると、コード変更後に自動的にリロードされます：

```bash
epsdk run main.py --reload
```

### デバッグのコツ

`config/config.toml` で DEBUG または TRACE レベルのログを有効にします：

```toml
[ErisPulse.logger]
# DEBUG: モジュールのロード、ルート登録などの開発デバッグ情報を出力
# TRACE: 最低レベル。イベントディスパッチ、ストレージへの書き込み、遅延ロードなどフレームワーク内部の詳細な流れを出力
level = "DEBUG"
```

## モジュールの公開

完全な公開フローについては [公開とモジュールストアガイド](publishing.md) を参照してください。PyPI の公開手順や ErisPulse モジュールストアへの提出フローなどが含まれます。



====
模块开发
====


模块开发
----


### 模块开发入门

# モジュール開発入門

> [!NOTE]
> **L1 コア必読**――トップページの「学習パス」にある5つのコアドキュメントの1つで、モジュール開発に必須です。


このドキュメントに沿って進めると、`/hello` コマンドに応答できる実行可能なモジュールが完成し、モジュールのプロジェクト構造、登録方法、ロード/アンロードフックについても理解できます。今後のすべてのモジュールドキュメントは、この骨組みの上に成り立っています。

## プロジェクト構造

標準的なモジュールの構造：

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py
```

## pyproject.toml 設定

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "モジュール機能の説明"
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
# ルートからのインポートを推奨（2.10+）：よく使うシンボルはルートパッケージから直接インポートでき、深いパスも引き続き互換
from ErisPulse import BaseModule, command

class Main(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
    
    @staticmethod
    def get_load_strategy():
        """モジュールのロード戦略を返します"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[],  # 任意：依存する他のモジュールのリスト
            # 任意：イベント駆動の遅延アクティベーション――トリガーを宣言すると、最初に一致するイベント/コマンドが到着した時点で自動的にロードされます
            # activate_on=[{"command": {"name": "hello", "help": "挨拶を送る"}}],
        )
    
    async def on_load(self, event):
        """モジュールのロード時に呼び出されます"""
        @command("hello", help="挨拶を送る")
        async def hello_command(event):
            name = event.get_user_nickname() or "フレンド"
            await event.reply(f"こんにちは、{name}さん！")
        
        self.logger.info("モジュールがロードされました")
    
    async def on_unload(self, event):
        """モジュールのアンロード時に呼び出されます"""
        self.logger.info("モジュールがアンロードされました")
```

> **設定の読み取り**：上記の基本例では設定を使用していません。設定を読み取る必要がある場合は、ネストした `ConfigClass` を宣言し、`self.cfg` 経由でリアルタイムに読み取る方法が推奨されます（詳細は [モジュールのコア概念](core-concepts.md#宣言的設定推奨) を参照）。`_load_config()` を手動で呼び出す旧式の書き方は非推奨となりました。

## モジュールのテスト

### ローカルテスト

```bash
# プロジェクトディレクトリでモジュールをインストール
epsdk install ./MyModule

# プロジェクトを実行
epsdk run main.py --reload
```

### コマンドのテスト

コマンドを送信してテストします：

```
/hello
```

## コア概念

### BaseModule 基底クラス

すべてのモジュールは `BaseModule` を継承する必要があり、以下のメソッドを提供します：

| メソッド | 説明 | 必須 |
|------|------|------|
| `__init__(self, sdk)` | コンストラクター（フレームワークが `sdk` インスタンスを渡します） | いいえ |
| `get_load_strategy()` | ロード戦略を返します | いいえ |
| `get_meta()` | モジュール紹介のメタ情報を返します（任意） | いいえ |
| `on_load(self, event)` | モジュールのロード時に呼び出されます | はい |
| `on_unload(self, event)` | モジュールのアンロード時に呼び出されます | はい |

### モジュール紹介 meta

> [!NOTE]
> この機能には ErisPulse **2.8.0+** が必要です。

`get_meta()` を通じて、モジュールの紹介メタ情報（このモジュールが何をするのか、どのカテゴリに属するのかなど）を宣言します。
メタ情報はモジュールの**汎用紹介データ**であり、help モジュール、Dashboard のモジュールリスト、モジュールストアなど、さまざまなインターフェース/エコシステムモジュールから利用されます。

`get_load_strategy()` が `ModuleLoadStrategy` を返すのと同様に、**`ModuleMeta` 設定クラスのインスタンスを返すことが推奨されます**（属性の型付け、IDE 補完）。dict を直接返すことにも対応しています：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天気",               # 表示名（デフォルトの登録名）
            description="都市の天気を照会",  # モジュールの概要
            version="1.0.0",
            author="ErisDev",
            group="ツール",               # 機能グループ
            tags=["天気", "照会"],
        )
```

互換的な書き方（dict）：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "天気",
            "description": "都市の天気を照会",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "ツール",
            "tags": ["天気", "照会"],
        }
```

- `module.get_meta("MyModule")` は解決済みのメタ情報を読み取ります（クラス宣言 > 登録 info の優先順位で、該当モジュールのコマンド名が自動補完されます）。
- `module.get_commands_overview()` は「モジュールの meta + その登録コマンド（エイリアス/グループ/ヘルプ）」を集約した、モジュール別に整理されたコマンドの一覧です。
- コマンドの所属モジュールは `cmd_info["owner"]` から取得できます（登録時にコンテキストシステムが自動的に注入します）。

#### meta フィールドの i18n サポート

メタ情報のフィールド値には、プレーンな文字列、または i18n 辞書 `{"i18n": "key.path", "default": "フォールバックテキスト"}`（設定の `description` と同じ規約）を使用できます。
翻訳キーは `I18nClass` で宣言・登録し、`module.get_meta()` が読み取る際に現在の言語のテキストへ自動的に解決されます：

```python
class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        meta_description: I18nKey = I18nKey(
            default="Weather lookup",
            zh_CN="查询城市天气",
            en="Weather lookup",
        )

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天気",
            description={"i18n": "MyModule.meta_description", "default": "Weather lookup"},
        )
```

### SDK オブジェクト

`sdk` オブジェクトを通じてコア機能にアクセスします：

```python
from ErisPulse import sdk

sdk.storage    # ストレージシステム
sdk.config     # 設定システム
sdk.logger     # ログシステム
sdk.adapter    # アダプターシステム
sdk.router     # ルーティングシステム
sdk.lifecycle  # ライフサイクルシステム
```

## 次のステップ

### 学習パスの続き

- [モジュールのコア概念](core-concepts.md) - モジュールアーキテクチャを深く理解する
- [Event ラッパークラス詳解](event-wrapper.md) - Event オブジェクトを学ぶ

### 作成後は

- [モジュールのベストプラクティス](best-practices.md) - 高品質なモジュールを開発する



### 模块核心概念

# モジュールのコアコンセプト

> [!NOTE]
> **L1 コア必読**——トップページの「読み進めパス」にある5本のコアドキュメントの1つで、モジュール開発に必須です。


このドキュメントでは、モジュールのロードからアンロードまでの完全なライフサイクル、宣言型設定とストレージの使い方を解説します——フレームワークが自動でやってくれることと、自分で書くべきことを整理し、読み終えれば全体像がつかめます。

## モジュールのライフサイクル

### ロード戦略

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """モジュールのロード戦略を返す"""
        return ModuleLoadStrategy(
            lazy_load=True,   # 遅延ロードするか即時ロードするか
            priority=0,       # ロード優先度（数値が大きいほど先にロードされる）
            depends=["OtherModule"]  # 任意：依存する他のモジュールを宣言
        )
```

> `depends` で宣言されたモジュールが未登録の場合、現在のモジュールはスキップされ、警告が記録されます。ロード順序はトポロジカルソートで決定され、同一レベルでは `priority` の降順に従います。

> [!NOTE]
> **カスケードアンロード / カスケードリロード**（ErisPulse **2.8.0+**）：他のモジュールから依存されているモジュールをアンロードすると、それに依存しているモジュールは**先にカスケードアンロードされます**（ログにカスケードチェーンが出力されます）。任意のモジュール（ローカルプラグイン / ランタイム登録 / PyPI インストールパッケージ）をホットリロードする際も、依存しているモジュールは同様に**カスケードリロード**され、依存者が無効になったインスタンス参照を保持したまま動作し続けることを防ぎます。循環依存が宣言されている場合は、ロード時に `RuntimeError` で拒否されます。
>
> **reload はフルリロード**（ErisPulse **2.11.0+**）：`reload()` はデフォルトでトップレベルのパッケージ名に基づいて import キャッシュをクリーンアップし、依存者の再インポートを行います。アンロード前に自動で構文チェックを行い（失敗時はアンロードを拒否し、旧インスタンスがサービスを継続）、成功後はコードの同一性を照合します（偽リロードの警告 / `stale` マーク）。ロード失敗時の状況は `sdk.module.last_error(名前)` で直接照会できます（traceback を含む）。

### on_load メソッド

モジュールのロード時に呼び出され、リソースの初期化とイベントハンドラの登録に使用します：

```python
async def on_load(self, event):
    # イベントハンドラを登録
    @command("hello", help="挨拶コマンド")
    async def hello_handler(event):
        await event.reply("こんにちは！")
    
    # SDK 組み込みの HTTP クライアントを使用（コネクションプールは自動管理、session の手動作成は不要）
    # sdk.client からリクエストを送信できます
```

### on_unload メソッド

モジュールのアンロード時に呼び出され、リソースのクリーンアップに使用します：

```python
async def on_unload(self, event):
    # カスタムリソースをクリーンアップ
    # sdk.client はフレームワークが管理するため、手動でクローズする必要はありません
    
    # イベントハンドラを解除（フレームワークが自動的に処理します）
    self.logger.info("モジュールをアンロードしました")
```

> バックグラウンドタスクの作成とクリーンアップ（`self.spawn()` / フレームワークによるフォールバックキャンセル）の詳細は、[ライフサイクル管理](../../advanced/lifecycle.md#バックグラウンドタスクの帰属と自動キャンセル) を参照してください。

### on_before_unload メソッド

> [!NOTE]
> このフックには ErisPulse **2.11.0+** が必要です。

アンロードパイプラインの**最初のステップ**（`on_unload` とリソース回収より前）で発火するオプションフックです——この時点ではモジュールのすべてのリソースがまだ無傷のため、アンロード / 休眠 / リロードの前に状態を `sdk.storage` に保存し、次回の `on_load` で復元するのに適しています（遅延ロード休眠の状態引継ぎはまさにこれに基づいています）：

```python
async def on_before_unload(self, event):
    # event["reason"] はアンロード / リロード / 無効化 / 連鎖 / スリープの意図を示す
    if event["reason"] in ("reload", "dormant"):
        await self.state.aset("snapshot", self.collect_state())
```

フックが失敗した場合は警告が出るだけで、アンロードフローはブロックされません。このフックを宣言していないモジュールの挙動は変わりません。休眠 / 復帰のセマンティクスの詳細は、[遅延ロード休眠](../../advanced/lazy-loading.md#遅延ロード休眠dormant_after) を参照してください。

### アンロードと完全アンロード（purge）

> [!NOTE]
> この機能には ErisPulse **2.8.0+** が必要です。

`unload()` はデフォルトでは**ロードの取り消しのみ**を行い（インスタンスとリソースをアンロード）、登録スタブ（モジュールクラスとメタ情報）は保持します——モジュールは引き続き discover で再検出でき、`register()` を再実行しなくても `load()` で再インスタンス化できます。

**完全アンロード**（モジュールクラスの参照を解放し `sys.modules` をクリーンアップして、プラグインとその専用依存関係を GC で回収できるようにする）が必要な場合は、`purge=True` を渡します：

```python
# ロードの取り消しのみ：登録スタブは保持され、いつでも再 load() できます
await sdk.module.unload("MyModule")

# 完全アンロード：登録スタブを削除 + sys.modules をクリーンアップ（プラグイン由来の場合）
await sdk.module.unload("MyModule", purge=True)
```

| セマンティクス | `unload()` デフォルト | `unload(purge=True)` |
|------|-----------------|----------------------|
| インスタンスとリソースのアンロード（イベント/task/ルート/lifecycle/i18n） | ✅ | ✅ |
| 登録スタブの保持（モジュールクラスとメタ情報） | ✅ | ❌ 削除 |
| `sys.modules` のクリーンアップ（プラグインフォルダ由来のみ） | ❌ | ✅ |
| モジュールクラスが GC で回収可能 | ❌ | ✅ |
| 再ロード | `load()` で直接利用可能 | 先に `register()` + `load()` が必要 |

> `purge=True` の場合、カスケードアンロードされる依存者も同様に purge されます。アンロード後、フレームワークは `gc.collect()` を実行し、モジュールクラス/インスタンスが回収可能かどうかをチェックします。残存参照はログに警告として出力されます（参照元を含む、DEBUG レベル）。

### ライフサイクルの全体像

上記のメソッドをつなげると、フレームワークが1つのモジュールをロード・アンロードする際に**裏で行っているすべての処理**は次のとおりです：

```mermaid
flowchart TD
    subgraph Load["ロード（register → load）"]
        L1["register：モジュールクラスとメタ情報を登録"] --> L2["依存チェック<br/>欠落時はスキップ"]
        L2 --> L3["トポロジカルソート（Kahn + priority）"]
        L3 --> L4["owner を注入（current_owner）"]
        L4 --> L5["設定テンプレートの生成 + i18n 翻訳キーの登録"]
        L5 --> L6["モジュールをインスタンス化（sdk を注入）"]
        L6 --> L7["on_load() を呼び出し"]
        L7 --> L8["sdk 属性へのマウント + emit module.load"]
    end

    subgraph Unload["アンロード（unload）"]
        U1["on_unload() を呼び出し"] --> U2["バックグラウンドタスクのフォールバックキャンセル（self.spawn 帰属）"]
        U2 --> U3["i18n 翻訳キーのクリーンアップ"]
        U3 --> U4["ルート / コマンド / イベントハンドラの削除（owner 別）"]
        U4 --> U5["lifecycle フックのクリーンアップ（owner 別）"]
        U5 --> U6["SDK 属性と遅延ロードプロキシの削除"]
        U6 --> U7["emit module.unload"]
    end

    Load --> Unload
```

**ロード時にフレームワークがやってくれること**（自分で書くのは `on_load` だけで、残りは自動で完了します）：

| ステップ | フレームワークが自動で行うこと |
|------|-------------|
| owner 注入 | インスタンス化の間、`owner_scope` でモジュール名を囲みます——`on_load` 内で登録したコマンド/イベント/フック/バックグラウンドタスクは**自動的にこのモジュールに帰属**し、アンロード時に owner 単位でワンステップでクリーンアップされます |
| 設定テンプレート | `ConfigClass` を宣言したモジュールでは、フレームワークが `ErisPulse.<ModuleName>` 設定セクションを自動生成/自動投入します |
| i18n 翻訳キー | `I18nClass` を宣言したモジュールでは、翻訳キーが自動登録されます（アンロード時に自動登録解除） |
| 依存トポロジ | `depends` の宣言に基づいてソートし、依存されるモジュールが先にロードされることを保証します。循環依存は `RuntimeError` で拒否されます |
| SDK マウント | インスタンス化後に `sdk.<ModuleName>` にマウントされ、`sdk.MyModule.xxx` でアクセスできるようになります |

**アンロード時にフレームワークがクリーンアップしてくれるもの**（上の U1→U7 に対応）：`on_unload` の実行完了後にフォールバックでクリーンアップします——バックグラウンドタスクの強制キャンセル（`self.spawn` で作成されたもの。グレースフルな終了処理は `on_unload` 内で自前に行ってください）、i18n キー、ルート、コマンド/イベントハンドラ、lifecycle フック、最後に SDK 属性を削除します。`purge=True` を指定した場合はさらに登録スタブの削除 + `sys.modules` のクリーンアップが行われます。

> この自動クリーンアップこそが「`on_load`/`on_unload` を書くだけで、手動 unregister は不要」という安心感の根拠です——フレームワークは owner による帰属を利用して、「登録したものを登録者がクリーンアップする」仕組みをワンステップで実現しています。

## SDK オブジェクト

### コアモジュールへのアクセス

```python
from ErisPulse import sdk

# sdk オブジェクトを通じてすべてのコアモジュールにアクセス
sdk.logger.info("ログ")
sdk.storage.set("key", "value")

# モジュール固有の小さな状態（カウンタ/スイッチ/最終実行時刻）には self.state を優先使用——
# キーには自動的に module.state.<モジュール名>. プレフィックスが付き、モジュールのアンロード/リロード後も残ります：
count = self.state.get("runs", 0) + 1
self.state.set("runs", count)            # 同期（任意のコンテキスト）
await self.state.aset("runs", count)     # 非同期パス
await self.state.aget("runs", 0)
config = sdk.config.getConfig("MyModule")
```

### モジュール間の通信

```python
# 他のモジュールにアクセス
other_module = sdk.OtherModule
result = await other_module.some_method()
```

## アダプタ送信メソッドの照会

新しい標準仕様では、`__getattr__` メソッドをオーバーライドしてフォールバック送信メカニズムを実装することが求められるため、`hasattr` メソッドでメソッドの存在を確認できなくなりました。`2.3.5` から、送信メソッドを照会する機能が新たに追加されました。

### サポートされる送信メソッドの一覧表示

```python
# プラットフォームがサポートするすべての送信メソッドを一覧表示
methods = sdk.adapter.list_sends("onebot11")
# 戻り値: ["Text", "Image", "Voice", "Markdown", ...]
```

### メソッドの詳細情報の取得

```python
# 特定のメソッドの詳細情報を取得
info = sdk.adapter.send_info("onebot11", "Text")
# 戻り値:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "テキストメッセージを送信..."
# }
```

## 設定管理

### 宣言型設定（推奨）

v2.5.2 以降、モジュールは `ConfigClass` で設定クラスを宣言でき、アダプタと同じ設定 Schema システムを利用できます。設定は `self.cfg` でリアルタイムに読み込まれ、変更すると即座に反映されます：

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
            "description": {"i18n": "my_module.timeout", "default": "タイムアウト時間（秒）"},
            "ui": {"widget": "number", "group": "advanced", "order": 2},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("モジュールをロードしました")

    async def on_unload(self, event):
        pass

    async def do_something(self):
        cfg = self.cfg  # リアルタイム読み込み、型安全
        api_key = cfg.api_key
        timeout = cfg.timeout
```

`BaseConfig` は汎用の設定基底クラスで、アダプタ、モジュール、外部プロジェクトなどあらゆるシーンに適用できます。設定フィールドは i18n による多言語説明をサポートしています（詳細は [i18n ドキュメント](../../advanced/i18n.md#設定フィールドの多言語化) を参照してください）。

> [!NOTE]
> モジュール（アダプタを含む）のロード、アンロード、起動・停止などのライフサイクルはフレームワークが一元管理します（`module manager` / `scope` が照会・制御 API を提供します）。`ConfigClass` はビジネスパラメータのみを担うべきであり、モジュール内部で「自分を起動すべきかどうか」を再度判定するロジックをネストさせる必要はありません。

設定 Schema システムはさらに以下もサポートしています（v2.8.0+、詳細は [アダプタ core-concepts](../adapters/core-concepts.md#metadata-規約) を参照）：

- **docstring によるフィールド説明の自動生成**：metadata `description` が宣言されていない場合、docstring の `:ivar フィールド名: 説明` や `Attributes:` セクションから自動的にフォールバック抽出します
- **ネストされた dataclass 設定**：フィールドの型がネスト dataclass の場合、schema/テンプレート/検証が再帰的に処理され、WebUI ではネストされたグループとして描画されます
- **`example` の非書き込みフィールド**：`metadata={"example": True}` のフィールドは config.toml に書き込まれず、`config.full.example` にのみ記録されます（冗長でめったに触れない高度な設定項目に適しています）。ユーザーが手動で設定すると通常どおり永続化されます

### 設定のホットアップデート（on_config_update）

モジュールとアダプタが `on_config_update(old, new)` メソッドを実装すると、**このモジュールに関連する設定が実際に変化した**際にフレームワークが自動でルーティングして呼び出します（設定イベントを自分で購読する必要はありません）。token / スイッチ / レートリミットパラメータの変更が**再起動なしで**反映されます：

```python
class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def on_config_update(self, old_config, new_config):
        # ConfigClass を宣言している場合は型安全な設定オブジェクト（未宣言の場合は dict）；
        # 実行時の setConfig() で発火した場合、old_config は None（new のみ値を持つ）
        if old_config is None or new_config.api_key != old_config.api_key:
            self.logger.info("API key が更新されたため、クライアントを再構築します")
            self._client = build_client(new_config.api_key)
```

発火元とルーティングルール：

- **実行時の書き込み**（コードや Dashboard からの `setConfig()` 呼び出し）：設定キーのプレフィックスでルーティングをマッチング——このモジュールの設定キー（またはそのサブキー）の範囲内にある書き込みだけが発火し、その際 `old_config` は `None` になります
- **設定ファイルの編集**（ファイル監視によるツリー全体の比較で発火）：新旧の設定セクションが一致しない場合にのみ発火し、その際 `old` / `new` はそれぞれ変更前・変更後の設定オブジェクトになります
- コールバック内で送出された例外はフレームワークが捕捉して記録し、設定の書き込み自体には影響しません

使い分けの指針：

- `self.cfg` はリアルタイム読み込みです——状態の再構築が不要な単純なパラメータ（タイムアウト秒数など）は次の行のコードで既に新しい値になるため、このフックで手動同期する必要はありません
- 再構築が必要な**ステートフルなリソース**（クライアント接続、コネクションプール、タイマー）のみ、このフックで処理します

### 宣言型翻訳キー（v2.7.0+）

v2.7.0 以降、モジュールは `ConfigClass` を宣言するのと同じように、ネストクラス `I18nClass` で翻訳キーを一括宣言できます。フレームワークはロード時に宣言されたすべての翻訳キーを**自動登録**し、`i18n.register()` を手動で呼び出す必要はありません。また、登録タイミングは設定テンプレートの生成より早いため、設定説明で参照される i18n キーが確実に利用可能になります。

```python
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey

class MyModule(BaseModule):
    # 設定クラス（任意）
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="ようこそ",
            metadata={
                "description": {"i18n": "mymodule.welcome_msg", "default": "ウェルカムメッセージ"},
            },
        )

    # 翻訳キーコレクションクラス（任意）
    class I18nClass(BaseI18n):
        # 属性名から完全なキーパス <モジュール名>.<属性名> が自動的に組み立てられます
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # 言語非依存のフォールバック
            zh_CN="ようこそメッセージ",
            zh_TW="ようこそメッセージ",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
        )
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="こんにちは、{name}！",
            zh_TW="こんにちは、{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )
```

詳細は [i18n の推奨記法](../../advanced/i18n.md#推奨記法i18nclass-による翻訳キーの宣言v270) を参照してください。

### 手動での設定読み込み（廃止予定）

> **廃止予定**：代わりに [宣言型設定](#宣言型設定推奨) + `self.cfg` によるリアルタイム読み込みを使用してください。

```python
class MyModule(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk

    def _load_config(self):
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            self.sdk.config.setConfig("MyModule", {"api_key": "", "timeout": 30})
            return {"api_key": "", "timeout": 30}
        return config
```

## ストレージシステム

### 基本的な使い方

```python
# データを保存
sdk.storage.set("user:123", {"name": "山田太郎"})

# データを取得
user = sdk.storage.get("user:123", {})

# データを削除
sdk.storage.delete("user:123")
```

### トランザクションの使い方

```python
# トランザクションを使用してデータの一貫性を確保
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # いずれかの操作が失敗した場合、すべての変更がロールバックされます
```

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
    sdk.logger.info(f"グループメッセージを受信: {event.get_text()}")
```

### イベントハンドラのライフサイクル

フレームワークはイベントハンドラの登録と登録解除を自動管理するため、`on_load` 内で登録するだけです。

## 遅延ロード機構

### 動作原理

```python
# モジュールは初めてアクセスされたときにのみ初期化されます
result = await sdk.my_module.some_method()
# ↑ ここでモジュールの初期化がトリガーされます
```

### 即時ロード

即時初期化が必要なモジュール（リスナー、タイマーなど）の場合：

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=False,  # 即時ロード
        priority=100
    )
```

## エラー処理

### 例外の捕捉

```python
async def handle_event(self, event):
    try:
        # ビジネスロジック
        await self.process_event(event)
    except ValueError as e:
        self.logger.warning(f"パラメータエラー: {e}")
        await event.reply(f"パラメータエラー: {e}")
    except Exception as e:
        self.logger.error(f"処理に失敗しました: {e}")
        raise
```

### ログ記録

```python
# 異なるログレベルを使用
self.logger.debug("デバッグ情報")    # 詳細なデバッグ情報
self.logger.info("実行状態")      # 通常の実行情報
self.logger.warning("警告情報")  # 警告情報
self.logger.error("エラー情報")    # エラー情報
self.logger.critical("致命的エラー") # 致命的エラー
```



### Event 包装类详解

# Event ラッパークラス詳解

> [!NOTE]
> **L1 コア必読**——トップページの「読書パス」にある5つのコアドキュメントの1つで、モジュール開発に必須です。


ハンドラー内の `event` パラメーターが `.get_text()` / `.reply()` / `.wait_reply()` を直接呼び出せるのは、Event ラッパークラスのおかげです。本ドキュメントはその完全なメソッド一覧です——イベントハンドラーを作成する際に必要に応じて参照し、メソッドのシグネチャと動作はすべてここに記載の内容を基準としてください。

## event パラメーターへの型アノテーション追加

イベントハンドラーの `event` パラメーターは **Event ラッパークラス**（dict のサブクラス）です。`Event` の型アノテーションを追加することを**強く推奨**します（実行時はアノテーションがなくても動作しますが、アノテーションは IDE 補完と静的チェックに役立ちます）：

```python
from ErisPulse.Core.Event import Event

@message.on_private_message()
async def handler(event: Event):
    text = event.get_text()   # IDE がすべての便利メソッドを自動補完
    await event.reply(text)   # スペルミスは静的チェック時に検出できます
```

アノテーションを付けない場合、IDE は Event 上のメソッドを認識できず（`get_text()` / `reply()` / `wait_reply()` / プラットフォーム拡張メソッドのいずれも補完されず）、記憶を頼りに入力するしかありません。

> **区別に注意**：イベントハンドラーコールバックの `event` は **Event ラッパークラス**（`Event` でアノテーション）ですが、モジュールライフサイクルメソッド `on_load` / `on_unload` の `event` は通常の **dict**（`dict` でアノテーション）です。両者を混同しないでください。

## コア特性

- **辞書と完全互換**：Event は dict を継承
- **便利メソッド**：多数の便利メソッドを提供
- **ドットアクセス**：ドットによるイベントフィールドへのアクセスをサポート
- **後方互換**：すべてのメソッドは任意

## コアフィールドメソッド

```python
from ErisPulse.Core.Event import command, Event

@command("info")
async def info_command(event: Event):
    event_id = event.get_id()
    platform = event.get_platform()
    time = event.get_time()
    print(f"ID: {event_id}, プラットフォーム: {platform}, 時刻: {time}")
```

## メッセージイベントメソッド

```python
from ErisPulse.Core.Event import message, Event

@message.on_private_message()
async def private_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"こんにちは、{nickname}さん！")
```

## メッセージタイプ判定

```python
from ErisPulse.Core.Event import message, Event

@message.on_group_message()
async def group_handler(event: Event):
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    await event.reply(f"タイプ: {'個人チャット' if is_private else 'グループチャット'}")
```

## 返信機能

```python
from ErisPulse.Core.Event import command, Event

@command("ask")
async def ask_command(event: Event):
    await event.reply("あなたの名前を入力してください:")
    reply = await event.wait_reply(timeout=30)
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}さん！")

@command("price")
async def price_command(event: Event):
    await event.reply("金額を入力してください（例：5元）:")
    # 返信は正規表現に一致する必要があり、一致しない場合はタイムアウトまで待ち続けます
    reply = await event.wait_reply(timeout=30, regex=r"\d+\s*元")
    if reply:
        await event.reply(f"金額を受け付けました：{reply.get_text()}")
```

#### reply 以外：send_chain

`reply()` では対応できないシナリオ——プラットフォーム固有の修飾メソッド（Expire/Board など）、連続する複数の修飾、
内容パラメーターを持たないアクション型の送信——には `event.send_chain` でターゲットと送信アカウントが設定済みの送信チェーンを取得し、
自由に修飾を追加してから送信してください：

```python
await event.send_chain.At(event.user_id).Text("内容")     # チェーン修飾 + 送信
```

修飾メソッドの一覧は [送信メソッド仕様](../../standards/send-method-spec.md) を参照してください。

## インタラクティブセッションの応用

> [!NOTE]
> このセクションの機能には ErisPulse **2.8.0+** が必要です。

```python
# セッションのタイマーリマインダー：5分間返信がない場合はリマインドし、ユーザーの返信後に自動キャンセル
reminder = event.remind(300, "まだいますか？会話を終えたい場合は「終了」と返信してください")
reminder.cancel()  # 手動でのキャンセルも可能

# タイムアウトエスカレーション：指定時刻に必ず発火（返信ではキャンセルされない）、長時間未処理の場合にオーナーへ通知するなど
event.escalate(1800, lambda e: notify_master("チケットタイムアウト"))

# マルチパス待機：「同意」と「拒否」を同時に待ち、先着順で取得
which, reply = await event.select(
    event.expect(pattern="同意*", user="10001"),
    event.expect(pattern="拒否*", user="10002"),
    timeout=60,
)
if which is None:
    await event.reply("タイムアウト：承認を受信しませんでした")

# セッションレベル待機：同じグループの誰の返信でもマッチ可能（グループ協働）
reply = await event.wait_reply(session=True, prompt="どなたか回答をお願いします！")

# セッション受信箱：現在のセッションの直近20件のメッセージ（ボットを含む、AI コンテキスト / 重複防止の基盤）
messages = await event.history(20)

# メッセージトランザクション：例外発生時にトランザクション内で送信済みのメッセージを自動取り消し
async with event.message_tx():
    await event.reply("処理中です。お待ちください...")
    result = await do_something()
    await event.reply(f"完了：{result}")
```

## コマンド情報の取得

```python
from ErisPulse.Core.Event import command, Event

@command("cmdinfo")
async def cmdinfo_command(event: Event):
    cmd_name = event.get_command_name()
    cmd_args = event.get_command_args()
    await event.reply(f"コマンド: {cmd_name}, 引数: {cmd_args}")
```

## 通知イベントメソッド

```python
from ErisPulse.Core.Event import notice, Event

@notice.on_friend_add()
async def friend_add_handler(event: Event):
    await event.reply("友達登録ありがとうございます！")
```

## メソッド早見表

### コアメソッド

#### イベント基本情報
- `get_id()` - イベントID を取得
- `get_time()` - イベントのタイムスタンプを取得（Unix 秒単位）
- `get_type()` - イベントタイプを取得（message/notice/request/meta）
- `get_detail_type()` - イベントの詳細タイプを取得（private/group/friend など）
- `get_platform()` - プラットフォーム名を取得

#### ボット情報
- `get_self_platform()` - ボットのプラットフォーム名を取得
- `get_self_user_id()` - ボットのユーザーID を取得
- `get_self_account_id()` - ボットのアカウントID を取得（マルチ Bot モード）
- `get_self_info()` - ボットの完全情報辞書を取得

#### セッション識別子
- `get_target_id()` - 統一ターゲット ID を取得（グループチャットは `group_id`、チャンネルは `channel_id`、個人チャットは `user_id` を返し、group → channel → guild → thread → user の順で最初の非空値を採用）
- `get_session_id()` - セッションの一意識別子を取得、形式は `{platform}:{detail_type}:{target_id}`

### メッセージイベントメソッド

#### メッセージ内容
- `get_message()` - メッセージセグメント配列を取得（OneBot12 形式）
- `get_alt_message()` - メッセージの代替テキストを取得
- `get_text()` - プレーンテキスト内容を取得（`get_alt_message()` のエイリアス）
- `get_message_text()` - プレーンテキスト内容を取得（`get_alt_message()` のエイリアス）

#### 送信者情報
- `get_user_id()` - 送信者のユーザーID を取得
- `get_user_nickname()` - 送信者のニックネームを取得
- `get_sender()` - 送信者の完全情報辞書を取得

#### グループ/チャンネル情報
- `get_group_id()` - グループID を取得（グループチャットメッセージ）
- `get_channel_id()` - チャンネルID を取得（チャンネルメッセージ）
- `get_guild_id()` - サーバーID を取得（サーバーメッセージ）
- `get_thread_id()` - トピック/サブチャンネルID を取得（トピックメッセージ）

#### @メッセージ関連
- `has_mention()` - @ボットを含むかどうか
- `get_mentions()` - @されたすべてのユーザーID のリストを取得

### メッセージタイプ判定

#### 基本判定
- `is_message()` - メッセージイベントかどうか
- `is_private_message()` - 個人チャットメッセージかどうか
- `is_group_message()` - グループチャットメッセージかどうか
- `is_at_message()` - @メッセージかどうか（`has_mention()` のエイリアス）

### 通知イベントメソッド

#### 通知操作者
- `get_operator_id()` - 操作者の ID を取得
- `get_operator_nickname()` - 操作者のニックネームを取得

#### 通知タイプ判定
- `is_notice()` - 通知イベントかどうか
- `is_group_member_increase()` - グループメンバー増加イベント
- `is_group_member_decrease()` - グループメンバー減少イベント
- `is_friend_add()` - 友達追加イベント（`detail_type == "friend_increase"` に一致）
- `is_friend_delete()` - 友達削除イベント（`detail_type == "friend_decrease"` に一致）

### リクエストイベントメソッド

#### リクエスト情報
- `get_comment()` - リクエストの添付メッセージを取得

#### リクエストタイプ判定
- `is_request()` - リクエストイベントかどうか
- `is_friend_request()` - 友達リクエストかどうか
- `is_group_request()` - グループリクエストかどうか

#### リクエスト承認（approve / reject）

リクエストハンドラーを登録し、リクエストに対する判断を行います：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend(event):
    request_id = event.get_request_id()   # リクエスト識別子（欠落時は approve/reject が ValueError を送出）
    if event.get_comment() == "合言葉":
        result = await event.approve()    # 承認（備考付き可：approve(comment="ようこそ")）
    else:
        result = await event.reject()     # 拒否
    if result.get("status") != "ok":
        # 標準レスポンス形式、失敗時は message で理由が説明されます（例：34001 リクエストは期限切れ）
        pass

@request.on_group_request()               # グループ申請 / グループ招待
async def handle_group(event):
    await event.approve()
```

> 承認アクションはアダプターの `Request` DSL を通じて実行されます。戻り値、エラーコード、アダプター実装要件については
> [リクエスト操作仕様](../../standards/request-action-spec.md) を参照してください。汎用レジストラー
> `request.on_request()`（タイプを区別しない）も同様に利用できます。

#### チェーン制御（done / is_processed / is_stopped）

- `done(claim=True)` - 取り込み（デフォルト）または後続の低優先度ハンドラーのブロックのみ
- `is_processed()` - 現在のイベントが取り込み済みかどうか
- `is_stopped()` - 現在のイベント処理チェーンがブロックされているかどうか

取り込みとブロックの完全なセマンティクス（優先度の相互作用、コマンドの取り込み）については、
[イベント処理入門 · チェーン制御：取り込みとブロック](../../getting-started/event-handling.md#チェーン制御取り込みとブロック) を参照してください。

### 返信機能

#### 基本返信
- `reply(content, method="Text", at_sender=False, quote=False, at_users=None, reply_to=None, at_all=False, via=None, **kwargs)` - 汎用返信メソッド
  - `content`: 送信内容（テキスト、URL など）
  - `method`: 送信メソッド、デフォルトは "Text"、"Image"/"Voice"/"Video"/"File" などを選択可
  - `at_sender`: 送信者をメンションするかどうか（user_id を自動抽出）
  - `quote`: 現在のメッセージを引用返信するかどうか（message_id を自動抽出）
  - `at_users`: メンションするユーザーのリスト、例：`["user1", "user2"]`
  - `reply_to`: 返信対象のメッセージ ID を手動指定
  - `at_all`: 全メンバーをメンションするかどうか
  - `**kwargs`: 追加パラメーター（例：Mention メソッドの user_id）

- `reply_ob12(message)` - OneBot12 メッセージセグメントを使用して返信
  - `message`: OneBot12 メッセージセグメントのリストまたは辞書、MessageBuilder と組み合わせて構築可能

#### プラットフォーム機能照会
- `supports(method)` - 現在のプラットフォームが特定の送信メソッド（例：`"Image"`、`"Voice"`）をサポートするか確認、`bool` を返します
- `available_methods()` - 現在のプラットフォームで利用可能なすべての送信メソッドを一覧表示、メソッド名のリストを返します

#### 転送機能

> **注意**：転送機能はアダプターの Send DSL を通じて実装する必要があり、Event ラッパークラス自体は直接的な転送メソッドを提供しません。

```python
# メッセージをグループへ転送
adapter = sdk.adapter.get(event.get_platform())
target_id = event.get_group_id()  # または他のグループIDを指定
await adapter.Send.To("group", target_id).Text(event.get_text())
```

> **マルチアカウントデプロイ**：イベント処理チェーン内での送信は**アカウントの明示的な指定が不要**です——フレームワークはイベントディスパッチのエントリポイントで、イベントをトリガーしたアカウント識別子を呼び出しコンテキストに注入します。`Send` / `Api` / `Request` チェーンで明示的に指定されていない場合、自動的にトリガーイベントのアカウントにバインドされます（明示的な `Using()` が常に優先。タイマーなどのイベントコンテキストがないシナリオではデフォルトアカウントを使用します）。つまり、上の例の転送は「このイベントを受信したアカウント」から送信され、追加のコードは不要です。

#### クロスアカウント重複受信

マルチアカウントが同じグループに在籍している場合、同一の物理メッセージが複数のアカウント経由で1回ずつ受信されることがあります。フレームワークは `ErisPulse.framework.cross_account_policy` に従って処理します（デフォルトは `off` で関連付けなし）：

- `mark`：後続のコピーは通常どおりディスパッチされますが、イベントのトップレベルに `multi_receipt` フィールドが注入されます（`{"event_id": 最初に受信したイベントのid, "self_id": 最初に受信したアカウント}`）——モジュールはこのフィールドを読み取り、応答をスキップするかどうかを自ら判断します
- `drop`：コピーはディスパッチのエントリポイントで直接破棄され、モジュールは感知しません

### 返信待機機能

- `wait_reply(prompt=None, timeout=60.0, callback=None, validator=None, method="Text", pattern=None, regex=None)` - ユーザーの返信を待機
  - `prompt`: プロンプトメッセージ。指定した場合はユーザーに送信されます
  - `timeout`: 待機タイムアウト時間（秒）、デフォルトは60秒
  - `callback`: コールバック関数。返信を受信した際に実行されます
  - `validator`: 検証関数。返信が有効かどうかの検証に使用します
  - `method`: プロンプトメッセージの送信メソッド、デフォルトは "Text"
  - `pattern`: glob ワイルドカード（`*` / `?` / `[seq]`）。返信テキストは一致する必要があり、一致しない場合は待機を続けます
  - `regex`: 正規表現。返信テキストは一致する必要があります（`pattern` と `regex` はどちらか一方）。一致しない場合は待機を続けます
  - ユーザーの返信である Event オブジェクトを返し、タイムアウト時は None を返します

#### インタラクションメソッド

- `confirm(prompt=None, timeout=60.0, yes_words=None, no_words=None, method="Text", hint=False)` - 確認対話
  - `True`（確認）/ `False`（否定）/ `None`（タイムアウト）を返します
  - 中国語・英語の確認語の自動認識を内蔵し、語彙セットのカスタマイズも可能
  - `method`: 送信メソッド、デフォルトは "Text"；"Image"/"Markdown" などの非テキスト方式でのプロンプト送信をサポート
  - `hint`: プロンプトの末尾に確認語ヒント（例：「（はい/いいえ）」）を自動追加するかどうか、デフォルトは False

- `choose(prompt, options, timeout=60.0, method="Text", options_format="auto", merge_prompt=False, placeholder="{options}")` - 選択メニュー
  - `options`: 選択肢テキストのリスト
  - 選択肢のインデックス（0 ベース）を返し、タイムアウト時は `None` を返します
  - `method`: 送信メソッド、デフォルトは "Text"；テキスト系メソッド（Text/Markdown/md/Html/h5）はデフォルトで選択肢を末尾にマージします
  - `options_format`: 選択肢の形式（デフォルト： "auto"、method に応じて内蔵スタイルを自動選択）
    - `"auto"`：Markdown→番号なしリスト（`- 1.選択肢`）、Html→番号付きリスト（`<ol>`）、その他→プレーンテキストリスト
    - `"list"`：1行に1つ、例：``1. 選択肢A\n2. 選択肢B``
    - `"inline"`：1行で表示、例：``1.A | 2.B``
    - `"md"`：Markdown 番号なしリスト
    - `"html"`：Html 番号付きリスト
    - `callable`：カスタム関数。``list[str]`` を受け取り ``str`` を返します
  - `merge_prompt`: 1つのメッセージに強制マージして送信するかどうか、デフォルトは False
    - `False`（デフォルト）：テキスト系メソッドは自動マージ；非テキストメソッドは prompt を先に送信し、その後 Text で選択肢を送信します
    - `True`：method が何であれ 1つのメッセージにマージし、ユーザーが指定した method で送信します
  - `placeholder`: 選択肢を挿入するプレースホルダー、デフォルトは `{options}`；prompt 内でこのマーカーが現れる位置が選択肢テキストに置き換えられ、空文字列に設定した場合は常に末尾に追加されます

- `collect(fields, timeout_per_field=60.0)` - フォーム収集
  - `fields`: フィールドのリスト。各項目は `key`、`prompt`、オプションの `validator`、オプションの `method` を含みます
  - `{key: value}` の辞書を返し、いずれかのフィールドがタイムアウトした場合は `None` を返します
  - 各 field は `method` キーで送信メソッドを指定できます。例えば画像を収集する場合は `{"key": "avatar", "prompt": "アイコンを送信してください", "method": "Image"}` を使用します
  - 各 field はオプションで `options` キー（リスト）をサポートし、指定するとそのフィールドは選択問題になります（choose ロジックを自動呼び出し）
  - 各 field はオプションで `options_format`、`merge_prompt`、`placeholder` キーをサポートし、選択肢の形式、メッセージマージ動作、プレースホルダーを制御します

- `wait_for(event_type="message", condition=None, timeout=60.0)` - 任意のイベントを待機
  - `condition`: フィルター関数。`True` を返した場合にマッチします
  - マッチした Event オブジェクトを返し、タイムアウト時は `None` を返します

- `conversation(timeout=60.0)` - マルチターン対話コンテキストを作成
  - `Conversation` オブジェクトを返し、`say()`/`wait()`/`confirm()`/`choose()`/`collect()`/`stop()` をサポートします
  - `is_active` プロパティは対話がアクティブかどうかを示します

#### インタラクションメソッドの例

**confirm() - 確認対話：**

```python
from ErisPulse.Core.Event import Event
@command("delete", help="データを削除")
async def delete_handler(event: Event):
    if await event.confirm("すべてのデータを削除してもよろしいですか？"):
        sdk.storage.delete("all_data")
        await event.reply("データを削除しました")
    else:
        await event.reply("キャンセルしました")
```

**confirm() - ヒント付き：**

```python
# hint=True を指定するとプロンプトの末尾に「（はい/いいえ）」が追加されます
if await event.confirm("続行しますか？", hint=True):
    await event.reply("続行しました")
# ユーザーに表示される内容：続行しますか？（はい/いいえ）
```

**choose() - 選択メニュー：**

```python
from ErisPulse.Core.Event import Event
@command("color", help="色を選択")
async def color_handler(event: Event):
    choice = await event.choose("色を選択してください：", ["赤", "緑", "青"])
    if choice is not None:
        colors = ["赤", "緑", "青"]
        await event.reply(f"選択した色：{colors[choice]}")
```

**choose() - 選択肢のフォーマットとメッセージマージ：**

```python
# inline 形式：選択肢を同じ行に表示
choice = await event.choose("選択してください：", ["A", "B", "C"], options_format="inline")
# 出力：1.A | 2.B | 3.C

# カスタム形式
choice = await event.choose("選択してください：", ["猫", "犬"],
    options_format=lambda opts: " / ".join(opts))
# 出力：猫 / 犬

# options_format="auto"（デフォルト）：method に応じて内蔵スタイルを自動選択
# Markdown → 番号なしリスト
choice = await event.choose(
    "## 選択してください", ["猫", "犬"],
    method="Markdown",  # auto は自動的に md リストと認識
)
# 出力：
# ## 選択してください
# - 1. 猫
# - 2. 犬

# Html → 番号付きリスト
choice = await event.choose(
    "<h2>選択してください</h2>", ["猫", "犬"],
    method="Html", merge_prompt=True,  # auto は自動的に html リストと認識
)
# 出力：
# <h2>選択してください</h2>
# <ol><li>1. 猫</li><li>2. 犬</li></ol>

# マージモード + プレースホルダー
choice = await event.choose(
    "## 選択してください\n{options}\n番号で返信してください",
    ["猫", "犬"],
    method="Markdown", merge_prompt=True,
)

# カスタムプレースホルダー
choice = await event.choose(
    "選択してください: [choices]",
    ["猫", "犬"],
    placeholder="[choices]",
)
```

**collect() - フォーム収集：**

```python
from ErisPulse.Core.Event import Event
@command("register", help="登録")
async def register_handler(event: Event):
    data = await event.collect([
        {"key": "name", "prompt": "名前を入力してください："},
        {"key": "age", "prompt": "年齢を入力してください：",
         "validator": lambda e: e.get_text().isdigit()},
    ])
    if data:
        await event.reply(f"登録が完了しました！{data['name']}さん、{data['age']}歳")
```

**Text 以外のメソッドでの reply：**

```python
await event.reply("http://example.com/img.jpg", method="Image")
await event.reply("http://example.com/audio.mp3", method="Voice")

from ErisPulse.Core.Event import MessageBuilder
segments = MessageBuilder.text("この画像を見てください：").image("http://example.com/img.jpg").build()
await event.reply_ob12(segments)
```

> Conversation マルチターン対話の完全な使い方は [Conversation マルチターン対話](../../advanced/conversation.md) を参照してください。

### コマンド情報

#### コマンド基本
- `get_command_name()` - コマンド名を取得
- `get_command_args()` - コマンド引数のリストを取得
- `get_command_raw()` - コマンドの元テキストを取得
- `get_command_info()` - 完全なコマンド情報辞書を取得
- `is_command()` - コマンドかどうか

### 生データ

- `get_raw()` - プラットフォームの元イベントデータを取得
- `get_raw_type()` - プラットフォームの元イベントタイプを取得

### プラットフォーム拡張メソッド

アダプターは Event ラッパークラスにプラットフォーム固有のメソッドを登録できます。メソッドは対応するプラットフォームの Event インスタンスでのみ使用可能で、他のプラットフォームからアクセスした場合は `AttributeError` が送出されます。

プラットフォームメソッドは `Event.__getattribute__` を通じて内蔵メソッドより優先して適用されるため、`confirm`、`choose`、`collect`、`wait_reply` などの内蔵インタラクションメソッドをオーバーライドして、プラットフォーム独自の実装（ボタン、カードなど）を提供できます。内蔵実装は `_builtin_*` 関数としてエクスポートされ、オーバーライド側から呼び出せます。

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

### 登録済みメソッドの照会

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("email")
# ["get_subject", "get_from", ...]
```

### `hasattr` と `dir` のサポート

```python
hasattr(event, "get_subject")   # platform="email" の場合のみ True を返す
"get_subject" in dir(event)     # 同上
```

### クロスプラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` はプラットフォーム名として `"*"` を渡すことをサポートしており、登録されたメソッドは**すべてのプラットフォーム**の Event インスタンスで使用可能になります。AI 対話、コンテキスト管理など、クロスプラットフォームでの再利用が必要な機能に適しています。

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    # self は Event インスタンスで、イベントデータと内蔵メソッドにアクセス可能
    await self.reply(f"AI: {prompt}")
```

登録後、どのプラットフォームのイベントハンドラーからでも `event.ai_chat(...)` を呼び出せます。

メソッド解決の優先順位（高い順）：プラットフォーム固有メソッド → ワイルドカードメソッド → 内蔵メソッド → 辞書キーアクセス。

> アダプター開発者が拡張メソッドを登録する方法については、[イベントシステム API - クロスプラットフォーム拡張](../../api-reference/event-system.md#クロスプラットフォーム拡張ワイルドカード) を参照してください。



### 模块开发最佳实践

# モジュール開発のベストプラクティス

> [!TIP]
> **この記事を読むタイミング**：最初のモジュールを書いた後に読むことを推奨します（エンジニアリングのベストプラクティス）。必要なければ飛ばしても、他の機能の使用に影響はありません。


ここでは、モジュール開発における工程的な書き方の約束事項をまとめます：非同期処理はイベントループをブロックしないこと、設定は宣言型にすること、他人のリソースを管理する場合はアンロード時に解放すること——これらを守れば、メモリリーク、バックグラウンドタスクの残留、ホットリロードの失敗といった、モジュール開発で最もよくある問題を回避できます。

## モジュール設計

### 1. 単一責任の原則

各モジュールは1つのコア機能だけを担当するべきです：

```python
# 良い設計：各モジュールは1つの機能だけを担当
class WeatherModule(BaseModule):
    """天気情報取得モジュール"""
    pass

class NewsModule(BaseModule):
    """ニュース情報取得モジュール"""
    pass

# 悪い設計：1つのモジュールが複数の無関係な機能を担当
class UtilityModule(BaseModule):
    """天気、ニュース、ジョークなど複数の機能を含む"""
    pass
```

### 2. モジュール命名規則

```toml
[project]
name = "ErisPulse-ModuleName"  # ErisPulse- で始まる名前
```

### 3. 明確な設定管理

宣言型の設定（`ConfigClass` + `BaseConfig`）を使用することを推奨します。これにより、型安全性、自動テンプレート生成、WebUIフォームサポートなどの機能が得られます：

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
        "description": {"i18n": "my_module.cache_ttl", "default": "キャッシュの有効時間（秒）"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # 型安全、リアルタイム読み取り
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

また、手動で設定ストレージを読み書きする方法も引き続き使用できます（[モジュールのコアコンセプト](core-concepts.md#設定管理)を参照）。

### 宣言型の翻訳キー（v2.7.0+）

モジュールは `I18nClass` を使って翻訳キーを一括で宣言し、フレームワークが自動的に i18n システムに登録します。`i18n.register()` を手動で呼び出す必要はありません。

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # プレースホルダー付きの業務翻訳キー
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="ようこそ、{name}！",
            zh_TW="ようこそ、{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # 設定項目の説明の翻訳
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API アドレス",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

詳細な使い方は [i18n ドキュメント](../../advanced/i18n.md#推奨書き方-i18nclass-を使って翻訳キーを宣言する-v270) を参照してください。

## 非同期プログラミング

### 1. 非同期ライブラリの使用

```python
# 推奨：SDK 内部の HTTP クライアント（非同期、自動ログと統計）
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# sdk.client でも同じ効果
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# aiohttp を直接インポートしないこと（フレームワークの統一管理が難しくなる）
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# requests を使用しないこと（同期的で、イベントループをブロックする）
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # イベントループをブロックする
```

### 2. 正しい非同期操作

```python
from ErisPulse.Core.Event import Event  # event: Event 注釈は強く推奨；カスタムメソッドの補完は epsdk types を参照

async def handle_command(self, event: Event):
    # 結果を待つ必要がある長時間処理：直接 await（ライフサイクルが明確）
    result = await self._long_operation()

async def on_load(self, event: dict):
    # バックグラウンドタスク（ポーリング/タイマー/fire-and-forget）：self.spawn() を使用
    # モジュールのアンロード時にフレームワークが on_unload 後にバックグラウンドタスクをキャンセルし、self への参照を保持しない
    self.spawn(self._poll())
```

> [!NOTE]
> バックグラウンドタスクは `self.spawn()` を推奨します（ErisPulse **2.8.0+**）。**2.8.3 以降**では、裸の `asyncio.create_task` も自動的にモジュールに所属します（Task Factory が自動的に登録され、アンロード時にバックグラウンドタスクをキャンセルし、`self` の参照を保持しません）；`self.spawn()` は非メインループスレッドからメインループにスケジュールするサポートや、明示的な `owner=` 指定が可能なため、引き続き推奨されます。**2.8.3 以前**では、裸のタスクは所属せず、`self` の参照を保持してモジュールインスタンスが回収されず（ホットリロードでリーク）、`self.spawn()` を使用する必要があります。詳細は [ライフサイクル管理](../../advanced/lifecycle.md#バックグラウンドタスクの所属と自動キャンセル) を参照してください。

### 3. リソース管理

```python
async def on_load(self, event):
    # SDK クライアントは接続プールを自動管理するため、session の手動作成は不要
    pass
    
async def on_unload(self, event):
    # 自前でクライアントを作成する場合は、リソースの解放を忘れずに
    pass
```

## イベント処理

### 1. Event パッケージクラスの使用

```python
from ErisPulse.Core.Event import Event
# Event パッケージクラスの便利なメソッドを使用
@command("info")
async def info_command(event: Event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"こんにちは、{nickname}！")

# ダイレクトに辞書をアクセスしないこと
@command("info")
async def info_command(event: Event):
    user_id = event["user_id"]  # 明確さに欠け、間違いやすい
```

### 2. 懒惰なロード（Lazy Load）の適切な使用

```python
# 低頻度コマンドモジュール：activate_on トリガーを宣言し、最初の一致するコマンドが到着した時点で自動的にアクティブ化（ロードを遅らせる）
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"command": {"name": "dice", "help": "サイコロを振る", "aliases": ["d"]}},
        ])

# 低頻度リスナー・モジュール：イベントトリガーを宣言し、イベントが到着した時点で自動的にアクティブ化
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True, activate_on=[
            {"notice": "group_member_increase"},
        ])

# 高頻度（メッセージごとに処理する）または起動時に即座に準備が必要なモジュール：即時ロード
class HotListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# ユーティリティ・モジュールは lazy load が適しています
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

> `activate_on` の完全な構文（イベントの3形式 / コマンドの簡略化と dict 声明 / help のフォールバックチェーン）は [Lazy Load モジュールシステム](../../advanced/lazy-loading.md#イベント駆動のlazy-activateactivate_on) を参照してください。

### 3. イベントハンドラの登録

```python
from ErisPulse.Core.Event import Event
async def on_load(self, event):
    # on_load でイベントハンドラを登録
    @command("hello")
    async def hello_handler(event: Event):
        await event.reply("こんにちは！")
    
    @message.on_group_message()
    async def group_handler(event: Event):
        self.logger.info("グループメッセージを受信しました")
    
    # 手動で登録解除は不要、フレームワークが自動的に処理します
```

## ユーティリティ・モジュール：他人のリソースを管理するときはアンロード通知を受け止める

**いつ必要になるか**：あなたのモジュールが他のモジュールのリソース（タイマー、サブスクライバー、接続、キャッシュエントリなど）を管理している場合。これらのリファレンスが、相手のモジュールがアンロードされた後も削除されない場合、相手のインスタンスは永遠に回収されません——これはユーティリティ・モジュールで最もよくあるメモリリークの原因です。

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class MyToolModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {モジュール名: 管理するもの}

    def register(self, entry):
        owner = on_cleanup(self._drop)   # ① 登録時にクリーンアップチェーンに登録し、呼び出し元を自動的に識別
        self._entries.setdefault(owner, []).append(entry)

    def _drop(self, owner: str):
        self._entries.pop(owner, None)   # ② 相手がアンロードされたときにフレームワークが自動的に呼び出す：そのリソースを破棄

    async def on_unload(self, event):
        off_cleanup(self._drop)          # ③ 自分がアンロードされる前にハンドラを解除
```

これで、フレームワークが保証します：

- 相手のモジュールが**アンロード / 禁用**（またはアダプターが閉じる）されたときに、`_drop("相手のモジュール名")` は必ず呼び出されます
- **呼び出し元の識別は自動的**：相手が `on_load` で `sdk.MyToolModule.register(...)` を直接呼び出すか、`sdk.module.call("MyToolModule", "register", ...)` を経由して呼び出すかに関わらず、正しく識別されます
- 時間の管理は不要——ハンドラはフレームワークのクリーンアップチェーン内で呼び出され、リーク診断よりも早く、誤報が発生しません

接続しない場合の結果：相手が `purge` で完全にアンロードされたときにインスタンスが回収されない（リーク診断で「回収不可」と表示される）；もし相手自身が `on_unload` で自分に登録を解除しない場合、リークは永久的になります。

**他人のリソースを管理しない通常のモジュールは、この点を気にする必要はありません**——フレームワークが管理するリソース（コマンド / ハンドラ / ルーティング / バックグラウンドタスクなど）のアンロード時のクリーンアップは自動的です。

> 触発タイミング、呼び出し元識別ルール、タイムアウトとフォールトトレランスなどの詳細は [所有権システム・ユーティリティ・モジュールガイド](../../advanced/ownership.md#ユーティリティ・モジュールガイド他人のモジュールのハンドルを管理する) を参照してください。

## エラー処理

### 1. エラーの分類処理

```python
from ErisPulse.Core.Event import Event
from ErisPulse.Core.Bases.errors import ClientError

async def handle_event(self, event: Event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # 予期された業務エラー
        self.logger.warning(f"業務警告: {e}")
        await event.reply(f"パラメータエラー: {e}")
    except ClientError as e:
        # ネットワークエラー（sdk.client の下層 aiohttp エラーは自動的に変換）
        self.logger.error(f"ネットワークエラー {e.method} {e.url}: {e}")
        await event.reply("ネットワークリクエストに失敗しました。後で再度お試しください。")
    except Exception as e:
        # 予期しないエラー
        self.logger.error(f"不明なエラー: {e}", exc_info=True)
        await event.reply("処理に失敗しました。管理者にお問い合わせください。")
        raise
```

### 2. タイムアウト処理

```python
# 推奨：SDK 内部のクライアントを使用（タイムアウトとリトライが自動で付与）
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"リクエストがタイムアウトしました: {url}")
        raise
```

## ストレージ・システム

### 1. トランザクションの使用

```python
# トランザクションを使用してデータの一貫性を確保
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ トランザクションを使わないとデータの一貫性が保てない
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # ここでエラーが発生すると、上記の設定はロールバックできない
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. バッチ操作

```python
# バッチ操作を使用してパフォーマンスを向上
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ 複数回の呼び出しは効率が悪い
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## ログ記録

### 1. ログレベルの適切な使用

```python
# DEBUG: 詳細なデバッグ情報（開発時のみ）
self.logger.debug(f"入力パラメータ: {params}")

# INFO: 正常な実行情報
self.logger.info("モジュールがロードされました")
self.logger.info(f"リクエストを処理しました: {request_id}")

# WARNING: 警告情報、主な機能に影響しない
self.logger.warning(f"設定項目 {key} が設定されていません。デフォルト値を使用します。")
self.logger.warning("APIの応答が遅いです。最適化が必要かもしれません。")

# ERROR: エラー情報
self.logger.error(f"APIリクエストに失敗しました: {e}")
self.logger.error(f"イベント処理に失敗しました: {e}", exc_info=True)

# CRITICAL: 致命的なエラー、即時対応が必要
self.logger.critical("データベース接続に失敗しました。ロボットは正常に動作できません。")
```

### 2. 構造化ログ

```python
# 構造化ログを使用して、解析しやすくする
self.logger.info(f"リクエストを処理しました: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ 非構造化ログの使用
self.logger.info(f"リクエストを処理しました。ユーザー {user_id} から、{duration} ミリ秒かかりました。")
```

## パフォーマンス最適化

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
            
            # キャッシュ
            self._cache[key] = data
            return data
```

### 2. ブロッキング操作の回避

```python
from ErisPulse.Core.Event import Event
# 非同期操作を使用
async def process_message(self, event: Event):
    # 非同期で処理
    await self._async_process(event)

# ❌ ブロッキング操作
async def process_message(self, event: Event):
    # 同期操作でイベントループをブロック
    result = self._sync_process(event)
```

## セキュリティ

### 1. 敏感データの保護

```python
# 敏感データは設定に保存（宣言型 ConfigClass、secret フィールドはログやエクスポートに含まれない）
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule, BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={"description": "API キー", "secret": True},
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def check_api_key(self):
        if not self.cfg.api_key or self.cfg.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("config.toml に有効な API キーを設定してください")

# ❌ 敏感データのハードコード
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # これを行わないでください！
```

### 2. 入力の検証

```python
from ErisPulse.Core.Event import Event
# ユーザー入力の検証
async def process_command(self, event: Event):
    user_input = event.get_text()
    
    # 入力長の検証
    if len(user_input) > 1000:
        await event.reply("入力が長すぎます。再度入力してください。")
        return
    
    # 入力形式の検証
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("入力形式が正しくありません。")
        return
```

## テスト

### 1. 単体テスト

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_config_defaults(self):
        """設定のデフォルト値をテスト"""
        config = MyModule.ConfigClass()
        assert config.timeout == 30
```

### 2. 統合テスト

```python
@pytest.mark.asyncio
async def test_command_handling():
    """コマンド処理をテスト"""
    module = MyModule()
    await module.on_load({})
    
    # コマンドイベントをシミュレート
    event = create_test_command_event("hello")
    await module.handle_command(event)
```

## HTTP ルーティングのライフサイクル

モジュールが `router` で登録した HTTP/WebSocket ルーティングは、フレームワークによって**所有権の原則**に基づいてライフサイクルが自動管理されます：

- 登録時のネームスペースが所有権の識別子です。**リロード / アンロード時にフレームワークは自動的にその所有権以下のすべてのルーティングと接続リソースをクリーンアップ**し、手動での登録解除は不要です。
- したがって、**`on_load` では必ずルーティングを再登録する必要があります**。インスタンスレベルのブール値フラグを使って「一度だけ登録する」ような最適化は行わないでください：設定のホットリロードは stop/start をトリガーし、**同一インスタンスを再利用するため、フラグが保持されるとルーティングがクリーンアップ後に** **永久的に失われ、エンドポイントが 404 になり、プロセスを再起動しないと復帰しません**

```python
class MyModule(BaseModule):
    async def on_load(self):
        # 毎回ロード時に必ず再登録
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

ルーティングを事前に手動でアンロードしたい場合（動的にエントリをオフラインにするなど）は、明示的に登録解除できます：

```python
from ErisPulse.Core import router

router.unregister_http_route("MyModule", "/api/panel")
```

- ホットリロードの間、クライアント側は一時的にルーティングが 404 になる可能性がありますが、これは一時的な現象です。ブラウザ向けのインタラクティブページでは、404 に対して有限回の自動リトライを実装することを推奨します。

## 部署

### 1. バージョン管理

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

セマンティックバージョニングに従います：
- MAJOR.MINOR.PATCH
- 主バージョン：互換性のない API 変更
- 次バージョン：互換性のある機能追加
- リビジョン番号：互換性のあるバグ修正

### 2. README ヘッダー

`epsdk create` で生成された README には、ErisPulse のヘッダー（ロゴ + バッジ行）が既に含まれています。2 つの推奨モードがあります：

**モード A — ErisPulse ロゴのみ（デフォルト）：**

```markdown
<div align="center">

<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" width="180" alt="MyModule" />

# MyModule

**1行で説明**

<p>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/pypi/v/ErisPulse-MyModule?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://pypi.org/project/ErisPulse-MyModule/"><img src="https://img.shields.io/badge/Python-3.10+-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Python"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ErisPulse/ErisPulse"><img src="https://img.shields.io/badge/Powered_by-ErisPulse-FF6B9D?style=for-the-badge&logo=bookstack&logoColor=white" alt="ErisPulse"></a>
</p>

</div>
```

**モード B — モジュールアイコン × ErisPulse ロゴ（独自アイコンがある場合）：**

```markdown
<div align="center">

<img src=".github/assets/MyModuleIcon.svg" width="120" alt="MyModule" />
<span style="font-size:44px;color:#c8c8c8;margin:0 18px;vertical-align:middle;">×</span>
<img src="https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/.github/assets/ErisPulseLogo.png" height="120" alt="ErisPulse" />

# MyModule
（バッジ行は上と同じ）
</div>
```

必要に応じて、GitHub スター数やダウンロード数などのバッジを追加できます。ロゴはプロジェクトにダウンロードして、相対パスで参照することもできます（`.github/assets/ErisPulseLogo.png`）。



### 数据模型层（ORM）

# データモデル層（ORM）

> [!TIP]
> **このドキュメントを読むべきとき**: データモデル、自動テーブル作成、リレーションマッピングが必要な場合です。不要であれば読み飛ばしても、他の機能の利用には影響しません。

> [!NOTE]
> **ORM は非同期ネイティブです**: すべての CRUD メソッド（`create` / `get` / `save` / `delete` / `create_table` / QuerySet の終端操作）は `async def` であり、イベントループ内でそのまま `await` して呼び出せます。低層ドライバーは aiosqlite / aiomysql / asyncpg（ストレージバックエンドに応じて切り替わります）で、同期ブロッキングは発生しません。KV ストレージの同期 `get`/`set` は互換レイヤーであり、ORM とは無関係です。

2.9.0 からフレームワークに宣言型データモデル層が組み込まれました: `Model` を継承し `Field` でフィールドを宣言するだけで、自動テーブル作成と CRUD（登録・照会・更新・削除）の能力が得られます。モデルは内蔵ストレージ層の上に直接構築されています。SQLite / MySQL / PostgreSQL のどれを使うかは `ErisPulse.storage.backend` の設定で決まり、**バックエンドを切り替えてもモデルコードは一切変更不要**です。

## モデルの宣言

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON カラム。読み書き時に自動シリアライズ
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "プロフィール"})
```

- テーブル名はデフォルトでクラス名を snake_case にしたもの（`UserProfile → user_profile`）になります。`__tablename__ = "xxx"` で上書き可能です
- `Field` の制約語彙は宣言型設定クラスと共通です（`choices` / `ge` / `le` / `max_length`。`description` も同様に i18n 辞書に対応）。バリデーターエンジンは設定検証と共通の実装です

## フィールドパラメータ

| パラメータ | 説明 |
|------|------|
| `default` | デフォルト値（未指定かつ自動増分でない場合 → NOT NULL 必須） |
| `default_factory` | ミュータブルなデフォルト値のファクトリ（例：`list`） |
| `primary_key` | 主キー（複数指定で複合主キーとなり、テーブルレベルの `PRIMARY KEY (a, b)` に集約される） |
| `autoincrement` | 自動増分主キー（暗黙的に主キーを含み、`create` 後に自動的に値が反映される。単一列主キー専用で、複合主キーとは排他） |
| `max_length` | 文字列の最大長（`VARCHAR(n)` を生成、書き込み時にバリデーション） |
| `nullable` | NULL を許可するかどうか（デフォルトは False） |
| `index` | 通常インデックスを生成 |
| `unique` | 一意制約 |
| `choices` / `ge` / `le` | 列挙 / 数値範囲（書き込み時にバリデーション） |
| `description` | 説明（i18n 辞書、設定クラスと同じ形式） |
| `column_type` | SQL の列型定義の上書き |
| `foreign_key` | 列レベルの外部キー制約（`"テーブル.列"`、`REFERENCES` を生成） |
| `on_delete` | 外部キーの削除アクション：`CASCADE` / `SET NULL` / `RESTRICT` / `NO ACTION` / `SET DEFAULT` |
| `auto_now_add` | 挿入時に現在のタイムスタンプ（浮動小数点型のエポック秒）を自動的に書き込む |
| `auto_now` | 挿入時およびインスタンスの `save()` による更新時に自動的に書き込む（`QuerySet.update` の一括パスでは発動しない） |

## 複合主キーと複合一意

複数の `primary_key=True` フィールドで複合主キーを構成し、`get` / `save` / `delete` はすべての主キー列を基にレコードを特定します。
`__unique_together__` で複合一意グループを宣言します（複数グループ可）：

```python
class Membership(Model):
    __tablename__ = "memberships"
    __unique_together__ = (("user_id", "group_id"),)

    user_id: int = Field(primary_key=True)
    group_id: int = Field(primary_key=True)
    role: str = Field(default="member")

m = await Membership.get(user_id=1, group_id=2)
```

- `autoincrement` は複合主キーと排他的であり、共存させるとモデル定義時にエラーが発生します
- `__unique_together__` は一意インデックスで実装されます（インデックス名に `uq_` プレフィックスを付与）：新規テーブルの場合はテーブル作成時に生成され、**既存テーブルに対しては `create_table()` の実行時に自動的に追加作成されます**。再作成は不要です
- 複合主キーのモデルは現時点ではリレーションマッピング（has-many / belongs-to）をサポートしていません。インスタンスアクセス時に明示的にエラーが発生します

## テーブル作成と CRUD

```python
await User.create_table()                      # 冪等（IF NOT EXISTS）

user = await User.create(name="Alice", age=20) # 挿入（オートインクリメント主キーは自動的にインスタンスへ反映）
got = await User.get(id=user.id)               # 等値条件で最初の1件を取得

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # 主キーによる更新（先に制約チェック）。主キーがない場合は挿入にフォールバック（オートインクリメント主キーも同様にインスタンスへ反映）
await user.save(update_fields=["age"])         # 部分カラム更新（ホワイトリスト。それ以外のカラムは書き込まれない）
await user.delete()                            # 主キーによる削除

user, created = await User.get_or_create({"age": 20}, name="Alice")      # 見つかればそのまま返す。なければ作成
user, created = await User.update_or_create({"age": 21}, name="Alice")   # 見つかれば defaults を更新して保存。なければ作成

await User.update_all(User.age > 18, role="adult")  # 一括更新
await User.delete_all(User.age > 100)               # 一括削除
```

> [!NOTE]
> `get_or_create` / `update_or_create` は並行競合下では、2つのコルーチンが同時に作成処理に進む可能性があります——一意制約（主キー / `unique` / `__unique_together__`）により、後から到達した側は `StorageOperationError` を受け取ります。冪等なセマンティクスが必要な場合は、例外を捕捉した後にもう一度再クエリを行ってください。

クエリ式は `> >= < <= == !=`、`in_([...])`、および `&`（AND）/ `|`（OR）の組み合わせをサポートしています：

```python
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all()
```

## トランザクション

ORM の読み書きはフレームワークのストレージ層と同じトランザクションルーティングを共有しています: `storage.atransaction()` のトランザクションコンテキスト内では、`create` / `save` / `delete` およびクエリが自動的にトランザクション接続を再利用し、トランザクションと一体でコミットまたはロールバックされます。単独でコミットされることはありません。

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # ブロック内で例外が発生すると、上の INSERT も一緒にロールバックされます
```

## 宣言型設定クラスとの関係

モデル宣言は `ConfigClass`（`@dataclass + field(metadata=...)`）と**同じ低層を共有**しています。制約語彙、バリデーターエンジン（`validate_field_constraints`）、型カテゴリレジストリ（`python_type_category`）がそれです。ただしクラスの基盤は意図的に分離されています: 設定フィールドはプレーンな値（TOML 往復、一度ロードしてホット更新）、モデルフィールドはカラムデスクリプタ（クラスアクセス = クエリ式、行ごとのインスタンス）。1 つの宣言構文から、それぞれの役割を担う 2 つの基盤が得られます。

### 2 つの宣言の使い分け

| 観点 | 設定クラス `field(metadata=...)` | モデルフィールド `Field()` |
|------|------------------------------|---------------------|
| 適用場面 | モジュールの動作パラメータ（少数、人が読める、ホット更新が必要） | ビジネスデータの記録（多数の行、プログラムによる読み書き、検索が必要） |
| 保存形式 | `config.toml`（コメント保持、TOML 往復） | データベーステーブル（自動テーブル作成、SQL 方言） |
| 値の形式 | プレーンな値（`dataclass` 属性を直接読み取り） | デスクリプタ（クラスアクセス = カラム式、インスタンスアクセス = 行の値） |
| 制約宣言 | `metadata={"choices": ..., "min": ..., "max": ...}` | `Field(choices=..., ge=..., le=..., max_length=...)` |
| 共有基盤 | バリデーターエンジン + 制約語彙 + 型カテゴリレジストリ（共通） | 同左 |

経験則: **「モジュールがどう動くか」は設定クラスで、「ユーザーがどんなデータを生み出したか」はモデルで**扱います。

## 境界と注意点

- バックエンドはグローバルなストレージ設定で決まります。モデルでは `__storage__` クラス属性でカスタム `BaseStorage` インスタンスに上書き可能です（テスト時の注入用）
- `list` / `dict` フィールド（`list[int]`、`dict[str, int]` などのパラメータ化ジェネリクスを含む）は、コンテナ種別ごとに JSON テキストカラムとして保存され、読み書き時に自動シリアライズされます
- 書き込み（`create` / `save`）の前に自動で制約検証が実行され、失敗すると `ValueError`（ローカライズ済みメッセージ）が送出されます
- 自動マイグレーションは**カラム追加**のシナリオに対応済みです（下記参照）。カラム型の変更とカラムの削除は手動で対応する必要があります
- ストレージ接続失敗時の挙動はストレージ層と共通です: フレームワークはクラッシュせず、クールダウン後に自動再接続します

## 自動マイグレーション（フェーズ 2）

`create_table()` はテーブルが既に存在する場合、既存カラムとモデルフィールドを自動的に比較し、**追加されたフィールド**に対して自動で
`ALTER TABLE ADD COLUMN` を実行します（マイグレーション対象カラムは `NOT NULL` 制約を取り除き、既存行には NULL を設定）。
`index=True` を宣言した新規フィールドは、インデックスも同時に作成します。マイグレーションスクリプトを手書きする必要はありません。

```python
# v1 リリース後のモデル進化: email / bio フィールドを追加
class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0)
    email: str = Field(default="")     # 追加: 次 の create_table() で自動的に ADD COLUMN
    bio: str = Field(default="")

await User.create_table()              # 冪等: 追加カラムのみをマイグレーション
```

**境界**: サポートしているのはカラム追加のみです。主キーの変更、カラム型の変更、カラム削除は手動で対応してください（破壊的な
ALTER 誤操作を避けるため）。

## 外部キー（リレーションマッピングの基礎）

`foreign_key="テーブル.カラム"` は列レベルの外部キー制約を宣言し、DDL には `REFERENCES` 句が生成されます。`on_delete` は削除時の動作を宣言します（例：`"CASCADE"` は参照行を連鎖的に削除します）：

```python
class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id", on_delete="CASCADE")

    content: str = Field(max_length=255)
```

## リレーションマッピング（relationship）

モデルクラスの本体の中で、クラス属性として `relationship()` を宣言します。**方向は、外部キーカラムがどちらのテーブルで宣言されているかによって自動的に判定されます**:

```python
from ErisPulse.Core.Bases import Model, Field, relationship

class User(Model):
    __tablename__ = "orm_users"

    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)

    posts = relationship("Post", foreign_key="author")   # 外部キーは相手側のテーブル → has-many

class Post(Model):
    __tablename__ = "posts"

    id: int = Field(primary_key=True, autoincrement=True)
    author: int = Field(foreign_key="orm_users.id")
    content: str = Field(max_length=255)

    writer = relationship("User", foreign_key="author")  # 外部キーは自テーブル側 → belongs-to
```

**has-many**: インスタンス属性はクエリセットを返し、`QuerySet` の全チェーン機能が利用できます。
`create` を使うと、自テーブルの主キーが相手側の外部キーカラムへ自動的に書き込まれます:

```python
alice = await User.get(name="Alice")

posts = await alice.posts.all()                          # このユーザーの全記事
latest = await alice.posts.order_by("-id").first()
total = await alice.posts.count()
hot = await alice.posts.where(Post.content != "").all()  # 相手テーブルのフィールドに対する条件を追加
await alice.posts.delete()                               # このユーザーのものだけを削除

new_post = await alice.posts.create(content="hi")        # author は自動的に alice.id になる
```

**belongs-to**: `await` するだけで相手のインスタンスが得られます（一致がない場合や外部キーが NULL の場合は `None` を返します）:

```python
post = await Post.get(id=1)
writer = await post.writer          # User インスタンスまたは None
await writer.posts.count()          # 双方向で利用可能
```

**ポイント**:

- `related` にはクラス名の文字列を渡します（モデルクラス名レジストリによって遅延解決され、両側の定義順序は問いません）。モデルクラスを直接渡すことも可能です
- リレーションクエリは相手モデルとそれぞれのストレージバックエンドを使用します（バックエンドをまたぐ JOIN には対応していません。リレーションクエリは独立した 2 本の SQL です）
- リレーションクエリはキャッシュされず、アクセスごとに即時クエリが実行されます。`User.where(...)` を使えば任意のカスタムクエリも引き続き可能です

## 次のステップ

### データベースの変更やクラウドデータベースへのデプロイが必要な場合

- [ストレージバックエンド](../advanced/storage-backends.md) — SQLite / MySQL / PostgreSQL の設定と切り替え。モデルコードは一切変更不要です

### テーブル構造が不要で、少数のキーバリューを保存するだけの場合

- [モジュールのコア概念 - ストレージシステム](modules/core-concepts.md#ストレージシステム) — キーバリューストレージの軽量な使い方。モデルの宣言は不要です



=====
适配器开发
=====


适配器开发
-----


### 适配器开发入门

# アダプター開発入門

> [!TIP]
> **いつこのドキュメントを読むべきか**：アダプター開発パスの入口編（必読）。ゼロからアダプターを書く、アダプターの責務境界とプロジェクト構造を理解する、そのすべてがここにあります。読み終えたら、必要に応じて[イベントコンバーター](converter.md)と[SendDSL 詳解](send-dsl.md)へ進んでください。

このドキュメントを最後まで進めると、イベントを受信しメッセージを送信できる最小限の動作するアダプター（メインクラス + コンバーター + Send）が手に入り、各コンポーネントの責務境界も明確になります。新しいプラットフォームへの対応作業は、すべてここから始まります。

## アダプターの概要

### アダプターとは

アダプターは ErisPulse と各メッセージプラットフォームの間の橋渡し役であり、以下を担当します：

1. **順方向変換**：プラットフォームのイベントを受信し、OneBot12 標準形式へ変換する（Converter）
2. **逆方向変換**：OneBot12 メッセージセグメントをプラットフォーム API 呼び出しへ変換する（`Raw_ob12`）
3. プラットフォームとの接続管理（WebSocket/WebHook）
4. 統一された SendDSL メッセージ送信インターフェースの提供

### アダプターのアーキテクチャ

```mermaid
flowchart LR
    subgraph receive["順方向変換（受信）"]
        direction TB
        P1["プラットフォームイベント"] --> C1["Converter.convert()"] --> O1["OneBot12 標準イベント"] --> S1["イベントシステム"] --> M1["モジュール処理"]
    end
    subgraph send["逆方向変換（送信）"]
        direction TB
        M2["モジュールがメッセージを構築"] --> R1["Send.Raw_ob12()"] --> N1["プラットフォームネイティブ API 呼び出し"] --> R2["標準レスポンス形式"]
    end
```

## ディレクトリ構造

標準的なアダプターパッケージの構造：

```
MyAdapter/
├── pyproject.toml          # プロジェクト設定
├── README.md               # プロジェクト説明
├── LICENSE                 # ライセンス
└── MyAdapter/
    ├── __init__.py          # パッケージエントリ
    ├── Core.py               # アダプターメインクラス
    └── Converter.py          # イベントコンバーター
```

## クイックスタート

### 1. プロジェクトの作成

スキャフォールドで完全な骨格（pyproject、メインクラス、コンバーターを含む）を直接生成することをおすすめします：

```bash
# 標準プロジェクト（パッケージ化して公開する用）
epsdk create adapter -n MyAdapter

# ローカルアダプタープラグイン（パッケージ化不要。plugins/ ディレクトリに置くだけで自動読み込みされる。下記「ローカル開発」参照）
epsdk create adapter -n MyAdapter --local
```

スキャフォールドはデフォルトで WebSocket サーバー骨格を生成します。プラットフォームの接続方式が異なる場合は、`--template`
で通信モードのテンプレートを選択できます（生成時に対応する半完成品基底クラスがそのまま使え、`start`/`shutdown` は自分で書く必要がありません）：

```bash
epsdk create adapter -n MyAdapter --template polling   # HTTP ポーリング型（getUpdates による取得）
epsdk create adapter -n MyAdapter --template webhook   # HTTP コールバック型（プラットフォームからのプッシュ）
```

> 3 つの接続モードの違いと半完成品基底クラスの最小実装範囲については
> [アダプターのコア概念 - 接続モード半完成品基底クラス](core-concepts.md#接続モード半完成品基底クラス)を参照してください。
> 完全に動作するサンプルは、リポジトリの `examples/example-adapter-polling/` と `examples/example-adapter-webhook/` を参照してください。

手動で作成することもできます：

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
    "ErisPulse>=2.4.0"  # ErisPulse には aiohttp が内蔵されているため、通常は個別の依存追加は不要
]

[project.urls]
"homepage" = "https://github.com/yourname/MyAdapter"

[project.entry-points."erispulse.adapter"]
"MyAdapter" = "MyAdapter:MyAdapter"
```

### 3. アダプターメインクラスの作成

フレームワークは `ConfigClass` / `AccountConfigClass` による宣言型の設定管理を提供しており、アダプターは設定クラスを宣言するだけで、設定の自動読み込み、検証、設定テンプレートの生成が行われます。

```python
# MyAdapter/Core.py
from dataclasses import dataclass, field
# ルートからのインポートを推奨（2.10+）：よく使うシンボルはルートパッケージから直接インポートでき、深いパスも引き続き互換
from ErisPulse import BaseAdapter, BaseConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """MyAdapter の設定"""
    api_endpoint: str = field(
        default="https://api.example.com",
        metadata={
            "description": {"i18n": "my_adapter.api_endpoint", "default": "API アドレス"},
            "required": False,
            "ui": {"widget": "text", "group": "connection", "order": 1},
        },
    )
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "プラットフォームのトークン"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 2},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # 設定クラスを宣言すると、フレームワークが自動管理
    
    # __init__ をオーバーライドする必要はありません！フレームワークが自動処理します：
    # - self.sdk / self.logger を自動設定
    # - self.cfg による設定のリアルタイム読み取り
    # - self.Send / self.Request を自動初期化
    
    def _setup_converter(self):
        from .Converter import MyPlatformConverter
        return MyPlatformConverter()
```

> ⚠️ **`__init__` について**：新しいバージョンでは `BaseAdapter.__init__(self, sdk=None)` が SDK 参照の保持、ログの初期化、設定の読み込みを自動的に処理します。ほとんどのアダプターでは**`__init__` をオーバーライドする必要がなくなりました**。詳細は [__init__ の注意事項](#init-の注意事項) を参照してください。

> ⚠️ **`super().__init__()` について**：`BaseAdapter.__init__()` は `Send` と `Request` のファクトリーインスタンスの作成を担当します。呼び出しを忘れると、すべてのメッセージ送信とリクエスト操作で `AttributeError` が発生します。詳細は [__init__ の注意事項](#init-の注意事項) を参照してください。

### 4. 必須メソッドの実装

```python
class MyAdapter(BaseAdapter):
    # ... __init__ コード ...
    
    async def start(self):
        """アダプターを起動する（必須実装）"""
        # WebSocket または WebHook ルートを登録
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler
        )
        self.logger.info("アダプターが起動しました")
    
    async def shutdown(self):
        """アダプターをシャットダウンする（必須実装）"""
        router.unregister_websocket(
            module_name="myplatform",
            path="/ws"
        )
        # 接続とリソースをクリーンアップ
        self.logger.info("アダプターをシャットダウンしました")
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出す（必須実装）"""
        raise NotImplementedError("call_api を実装する必要があります")
```

#### Meta イベントの能動的な送信

アダプターは meta イベントを能動的に送信し、フレームワークが Bot のオンライン状態を追跡できるようにすべきです。`emit_meta()` を使えば 1 行で実現できます：

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Bot がオンライン
        await self.emit_meta("connect", bot_id, user_name="MyBot")

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Bot がオフライン
            await self.emit_meta("disconnect", bot_id)
```

> Bot 状態管理と Meta イベントの詳細については、[アダプターのベストプラクティス - Bot 状態管理](best-practices.md#bot-状態管理と-meta-イベント)を参照してください。

### 5. Send クラスの実装

`At`/`AtAll`/`Reply` 修飾子はフレームワークの SendDSL 基底クラスに組み込み実装されており、アダプターが実装するのは `Raw_ob12` と各送信メソッドだけで済みます。

フレームワークは 2 つの重要なヘルパーメソッドを提供します：
- `self._apply_modifiers(message)` — At/AtAll/Reply 修飾子をメッセージセグメントに自動マージ
- `self.send_context` — 送信コンテキスト辞書（`target_type`、`target_id`、`account_id`）を取得

```python
import asyncio

class MyAdapter(BaseAdapter):
    # ... その他のコード ...

    class Send(BaseAdapter.Send):

        def Raw_ob12(self, message, **kwargs):
            """
            OneBot12 形式のメッセージを送信する（必須実装）

            _apply_modifiers を使って修飾子の状態を自動マージし、
            send_context を使って送信コンテキストを取得します。
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

        # Text/Image/Voice/Video/File/Location は SendDSL 基底クラスから継承済みで、
        # デフォルトで Raw_ob12 に委譲されるため、再実装は不要です。
        # プラットフォーム固有のロジックが必要な場合は、個別のメソッドをオーバーライドできます：
        # def Text(self, text: str):
        #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**メディア系送信メソッド（Image/Video/File）の実装のポイント：**

- 基底クラスのデフォルト実装は、`file` パラメーターを OneBot12 メッセージセグメントとして `Raw_ob12` に渡します。アダプターは `Raw_ob12` 内でダウンロード/アップロードを処理する必要があります
- `file` パラメーターは、`bytes` バイナリデータと `str` URL の両方の型をサポートする必要があります
- URL が渡された場合は、まずファイルをダウンロードしてからプラットフォームへアップロードします
- プラットフォームは通常、まずアップロード API を呼び出してファイル識別子を取得し、その後送信 API を呼び出します

**`__getattr__` マジックメソッド：**

- メソッド名の大文字小文字を区別しない（`Text`、`text`、`TEXT` のいずれでも呼び出せる）
- 未定義のメソッドはエラーではなくヒント情報を返すようにする

**`Raw_ob12` メソッド：**

- OneBot12 標準メッセージ形式をプラットフォーム形式に変換して送信する
- `self._apply_modifiers(message)` を使って At/AtAll/Reply 修飾子を自動処理する
- `**self.send_context` を使って送信先情報とアカウント情報を渡す

### 6. コンバーターの実装

```python
# MyAdapter/Converter.py
import time
import uuid

class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォームのネイティブイベントを OneBot12 標準形式に変換する"""
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
        """イベントタイプを変換する"""
        type_map = {
            "message": "message",
            "notice": "notice"
        }
        return type_map.get(event_type, "unknown")
    
    def _convert_detail_type(self, raw_event):
        """詳細タイプを変換する"""
        return "private"  # 簡略化したサンプル
```

### 7. Request クラスの実装（リクエスト操作）

プラットフォームがフレンドリクエストやグループ招待など、Bot が判断を下す必要があるリクエストをサポートしている場合は、`Request` 内部クラスを実装できます：

```python
from ErisPulse import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    # ... Send とその他のコード ...

    class Request(RequestDSL):
        """リクエスト操作の実装（フレンドリクエスト、グループ招待など）"""

        # 公開エントリの accept()/reject() は基底クラスが提供（scope 認証ゲート + タスクラッパー）。
        # アダプターは _do_accept / _do_reject だけをオーバーライドし、標準レスポンスの dict を直接返す
        async def _do_accept(self, **kwargs) -> dict:
            """リクエストを承認する"""
            result = await self._adapter.call_api(
                endpoint="/set_request",
                request_id=self._request_id,
                account_id=self.request_context.get("account_id"),
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

        async def _do_reject(self, **kwargs) -> dict:
            """リクエストを拒否する（_do_accept と同構造：approve=False）"""
            result = await self._adapter.call_api(
                endpoint="/set_request",
                request_id=self._request_id,
                account_id=self.request_context.get("account_id"),
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
```

モジュール開発者向けの使い方：

```python
from ErisPulse import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Event の便利メソッドを使う
    await event.approve()
    # またはアダプター経由で直接操作
    await adapter.myplatform.Request("req_id").accept()
```

> プラットフォームがリクエスト操作をサポートしていない場合は、`Request` 内部クラスを実装しなくても構いません。基底クラスはデフォルトで `retcode=10002`（サポートされていない操作）を返します。詳細は[リクエスト操作仕様](../../standards/request-action-spec.md)を参照してください。

### 8. パッケージエントリの作成

```python
# MyAdapter/__init__.py
from .Core import MyAdapter
```

## ローカル開発（パッケージ化不要）

モジュールと同様に、アダプターもプロジェクトのローカルプラグインディレクトリ（デフォルトは `plugins/`、`ErisPulse.framework.plugins_dir` で設定可能）に置いて直接開発でき、**`pip install -e .` は不要**です：

```bash
# ローカルアダプタープラグインを生成
epsdk create adapter -n MyAdapter --local
# 生成される構造：
# plugins/
# └── MyAdapter/
#     ├── __init__.py
#     ├── Core.py
#     └── Converter.py
```

フレームワークは起動時にプラグインディレクトリを自動スキャンし、その中のモジュールとアダプターを読み込みます（entry-point でインストールしたパッケージと同等の扱い：有効状態、設定宣言、ホットアップデート、アンインストール時のクリーンアップはすべて同一）：

- **識別ルール**：パッケージディレクトリ（`__init__.py` を含む）でも単一の `.py` ファイルでも可。`Main` という名前のクラスを優先的に識別し、なければプラグイン内の最初の `BaseAdapter` / `BaseModule` サブクラスを採用
- **同名上書き**：ローカルプラグインと PyPI からインストールしたアダプターが同名の場合、ローカルプラグインが優先される（上書きデバッグに便利）
- **ホットリロード**：`sdk.enable_plugin_hot_reload()` で有効化されるプラグインディレクトリの監視は、アダプターにも適用されます。アダプターのコードレベルホットリロードは 2.11 から提供——`await sdk.adapter.reload("プラットフォーム名")` または `await sdk.reload_adapter("プラットフォーム名")`（構文の事前チェック → アンインストール時のクリーンアップ → キャッシュクリアと再インポート → 再登録して起動、失敗時は自動ロールバック。詳細は[アーキテクチャ概要](../../architecture.md)を参照）

### ローカルプラグインから公開へ

ローカルでの検証が完了したら、`pack` サブコマンドでプラグインをワンクリックで公開可能な標準プロジェクトに変換できます（対話形式でプラグインを選択、メタ情報を補完し、entry-point を含む pyproject を生成）：

```bash
epsdk create pack
# プラグインディレクトリ内のプラグインを選択 → プロジェクト名/説明/作者を入力 → MyAdapter/ プロジェクトディレクトリを生成
cd MyAdapter
pip install -e .   # 標準インストールに切り替え。その後、公開フローに従って PyPI にアップロード
```

> **ヒント**：変換後は、ローカルプラグインとインストール済みパッケージの重複読み込みを避けるため、`plugins/` 内の元ファイルを削除することをおすすめします（両者が同名の場合はローカルが優先され、インストール済みパッケージが有効になっていると誤認する原因になります）。

## 依存関係の宣言（オプション、2.8.0+）


アダプターは他のアダプターやモジュールへの依存を宣言でき、アダプター間の連携やオプション機能を実現できます：

```python
from typing import ClassVar

class MyAdapter(BaseAdapter):
    # ハード依存：欠落時は起動をスキップ（警告 + status=skipped-dependency イベント）
    depends: ClassVar[dict] = {
        "adapters": ["onebot11"],   # 依存するアダプター（プラットフォーム名で指定）
        "modules": ["TranslateEngine"],  # 依存するモジュール（登録名で指定）
    }
    # ソフト依存：欠落しても起動には影響なし。モジュールのロード/アンロード時にコールバックを受信（オプション機能モード）
    optional_modules: ClassVar[list] = ["TranslateEngine"]
```

- **起動順序**：モジュールへのハード依存を宣言したアダプターは、**モジュールの初期化完了後に**起動が延期されます
- **ソフト依存の通知**：`optional_modules`（またはモジュールへのハード依存）内のモジュールがロードされたときに `on_dependency_ready(module_name)` が呼び出され、アンロードされたときに `on_dependency_lost(module_name)` が呼び出されます（デフォルトは空実装、オーバーライド可）——遅延ロードやホットリロードのシナリオにも対応：

```python
async def on_dependency_ready(self, module_name):
    """ソフト依存モジュールの準備完了：対応するオプション機能を有効化"""
    if module_name == "TranslateEngine":
        self._translate = self.sdk.TranslateEngine

async def on_dependency_lost(self, module_name):
    """ソフト依存モジュールの喪失：機能を縮退"""
    if module_name == "TranslateEngine":
        self._translate = None
```

> [!NOTE]
> この機能には ErisPulse **2.8.0+** が必要です。

## `__init__` の注意事項

アダプター開発では、`__init__` のオーバーライドが関わる可能性のある 3 つの層があります。以下はそれぞれの層での正しいやり方です。

### 1. BaseAdapter 層（ほとんどの場合オーバーライド不要）

`BaseAdapter.__init__(self, sdk=None)` は `Send` / `Request` のファクトリーインスタンスの作成を担当し、以下を自動的に行います：

- `sdk` パラメーターを受け取り、`self.sdk`、`self.logger` を設定
- `ConfigClass` が宣言されている場合、`self.cfg` でグローバル設定をリアルタイムに読み取れる
- `AccountConfigClass` が宣言されている場合、`self.accounts` でマルチアカウント設定をリアルタイムに読み取れる

**ほとんどの場合 `__init__` をオーバーライドする必要はなく**、`ConfigClass` を宣言するだけで済みます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig  # 宣言すればフレームワークが自動管理
    
    async def start(self):
        cfg = self.cfg  # 型安全、リアルタイム読み取り
        ...
```

カスタム初期化が本当に必要な場合は、`super().__init__(sdk)` を呼び出すだけです：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyAdapterConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # sdk を渡す
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

### 2. Send 内部クラス（ほとんどの場合オーバーライド不要）

`SendDSL.__init__` はチェーン呼び出しの状態受け渡し（ターゲットタイプ、ターゲット ID、アカウントなど）を担当します。**ほとんどの場合、メソッドだけをオーバーライドすればよく**（`Raw_ob12`、`Text` など）、`__init__` をオーバーライドする必要はありません。

本当に必要な場合（プラットフォーム固有の状態の初期化など）は、**すべてのパラメーターを透過的に渡す必要があります**：

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        # パラメーター：adapter, target_type, target_id, account_id
        def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
            super().__init__(adapter, target_type, target_id, account_id)  # ← 必ず透過的に渡すこと
            self._my_state = None  # プラットフォーム固有の初期化
```

**なぜ透過的に渡す必要があるのか？** チェーン呼び出しの各ステップでは `self.__class__(...)` で新しいインスタンスが作成されます：

```python
adapter.Send.To("user", "123")               # → Send(adapter, "user", "123", None)
adapter.Send.To("user", "123").Using("bot1")  # → Send(adapter, "user", "123", "bot1")
```

`__init__` のシグネチャが一致しない、または `super()` を呼び出していない場合、チェーン呼び出しは中断されます。

### 3. Request 内部クラス（ほとんどの場合オーバーライド不要）

Send と同様です。パラメーターは `adapter`, `request_id`, `account_id`：

```python
class MyAdapter(BaseAdapter):
    class Request(RequestDSL):
        # パラメーター：adapter, request_id, account_id
        def __init__(self, adapter, request_id=None, account_id=None):
            super().__init__(adapter, request_id, account_id)  # ← 必ず透過的に渡すこと
            self._my_state = None  # プラットフォーム固有の初期化
```

### まとめ

| 層 | いつオーバーライドするか | 必須事項 |
|------|------------|-----------|
| **BaseAdapter** | カスタム初期化ロジックが必要なとき | `super().__init__(sdk)` （sdk パラメーターを渡す） |
| **Send 内部クラス** | 送信関連の状態を初期化する必要があるとき | `super().__init__(adapter, target_type, target_id, account_id)` |
| **Request 内部クラス** | リクエスト関連の状態を初期化する必要があるとき | `super().__init__(adapter, request_id, account_id)` |
| 3 つの層すべて | ほとんどの場合 | **ConfigClass を宣言するだけで済み、`__init__` には触れない** |

### 9. 接続情報とルートディスカバリー

アダプターがルートを登録すると、フレームワークはすべてのルート情報を記録します。ユーザーは以下の API でアダプターの接続アドレスを確認できます：

```python
from ErisPulse import sdk

# アダプターの完全な接続情報を取得
info = sdk.adapter.get_connection_info("myplatform")
# {
#   "platform": "myplatform",
#   "status": "started",
#   "connection": {
#     "base_url": "http://localhost:8080",
#     "http_routes": [
#       {"path": "/myplatform/webhook", "method": "POST",
#        "url": "http://localhost:8080/myplatform/webhook"}
#     ],
#     "websocket_routes": [
#       {"path": "/myplatform/ws",
#        "url": "ws://localhost:8080/myplatform/ws"}
#     ]
#   }
# }

# すべての名前空間（アダプター/モジュール）のルートを一覧表示
namespaces = sdk.router.list_namespaces()
# {"myplatform": {"http": ["/myplatform/webhook"], "websocket": ["/myplatform/ws"]}}

# 名前空間の完全な接続 URL を取得
urls = sdk.router.get_module_urls("myplatform")
# {"base_url": "http://localhost:8080", "http": [...], "websocket": [...]}

# 名前空間の詳細なルート情報を取得
routes = sdk.router.get_module_routes("myplatform")
# {"http": [{"path": "/myplatform/webhook", "methods": ["POST"]}],
#  "websocket": [{"path": "/myplatform/ws", "auth": false}]}
```

> **ヒント**：`get_connection_info()` の戻り値はユーザーに表示する（WebUI など）のに適しており、プラットフォーム側のコールバックアドレスや WebSocket 接続アドレスを設定する際の助けになります。ルート登録時の `module_name` は、アダプターが ErisPulse に登録した `platform` 名と完全に一致している必要があります。一致していないと、ルートディスカバリーが正しく関連付けできません。

### 10. SSE (Server-Sent Events) サポート

ErisPulse にはサーバー非依存の SSE サポートが組み込まれており、モジュールとアダプターは `@sdk.router.sse()` で SSE エンドポイントを登録できます。

#### 基本的な使い方

```python
import asyncio
from ErisPulse import sdk

@sdk.router.sse("MyModule", "/events")
async def event_stream(sse):
    """SSE イベントをプッシュする"""
    count = 0
    while not sse.closed:
        await sse.send({"count": count}, event="update")
        count += 1
        await asyncio.sleep(1)
```

#### リクエストパラメーターの使用

ハンドラーは `request` パラメーターを宣言することで、クライアントのリクエスト情報にアクセスできます：

```python
@sdk.router.sse("MyModule", "/events")
async def event_stream(request, sse):
    token = request.query_params.get("token")
    if not validate_token(token):
        await sse.close()
        return

    while not sse.closed:
        data = await fetch_data(token)
        await sse.send(data)
        await asyncio.sleep(5)
```

#### SseEmitter API

| メソッド | 説明 |
|------|------|
| `sse.send(data, event=None, id=None, retry=None)` | SSE イベントを送信する。str 以外の data は自動的に JSON シリアライズされる |
| `sse.close()` | SSE 接続を優雅に閉じる（安全に呼び出せ、複数回の呼び出し可） |
| `sse.closed` | 接続が閉じられているかどうか |
| `sse.request` | 下層のリクエストオブジェクト（query params、headers の読み取りに使用可） |

#### RouteGroup での使用

```python
api = sdk.router.group("MyModule", "/api", version="1")

@api.sse("/events")
async def events(sse):
    await sse.send({"msg": "hello"})
```

#### ルートディスカバリー

SSE ルートはルートディスカバリー API に自動的に現れます：

```python
# list_namespaces には "sse" キーが含まれる
sdk.router.list_namespaces()
# {"MyModule": {"http": [...], "websocket": [...], "sse": ["/MyModule/events"]}}

# get_module_routes は streaming: true とマークする
sdk.router.get_module_routes("MyModule")
# {"http": [...], "websocket": [...], "sse": [{"path": "/MyModule/events", "streaming": true}]}

# get_module_urls は完全な URL を生成する
sdk.router.get_module_urls("MyModule")
# {"sse": [{"path": "/MyModule/events", "url": "http://localhost:8080/MyModule/events"}]}
```

> **サーバー非依存設計**：`SseEmitter` はコールバックを通じて下層の HTTP フレームワークと疎結合になっています。フレームワークは統一された登録入口として `register_sse()` と `@sse` デコレーターを提供しており、アダプターはどの下層 HTTP フレームワークにも直接依存することなく SSE エンドポイントを実装できます。

## 次のステップ

### アダプターの三大要素を補完する

- [イベントコンバーター](converter.md) - プラットフォームイベント → OneBot12 の実装詳細とよくある落とし穴
- [SendDSL 詳解](send-dsl.md) - メッセージ送信チェーン、修飾メソッドと送信ルール
- [アダプターのコア概念](core-concepts.md) - BaseAdapter / ライフサイクル / マルチアカウントの仕組み解説

### 骨格が動いた後は

- [アダプターのベストプラクティス](best-practices.md) - 接続リトライ、ハートビート、エラー処理のエンジニアリング的な仕上げ
- [公開とモジュールストアガイド](../publishing.md) - PyPI とモジュールストアへの公開



### 适配器核心概念

# アダプタのコア概念

> [!TIP]
> **この記事を読むべきタイミング**：アダプタ開発経路内では必読（BaseAdapter / SendDSL / ライフサイクルなど、コアメカニズムの完全な説明）。開発の立ち上げだけなら [アダプタ開発入門](getting-started.md) を先に読むと良い。"なぜこう書くのか"という疑問が生じた際は、この記事に戻って確認する。

この記事では、アダプタの実行メカニズムを説明します。AdapterManager がどのようにアダプタを登録・イベントを配信するか、`BaseAdapter` が初期化時に何をしてくれたか、設定と複数アカウントの宣言方法など——アダプタを開発する際に「なぜこう書くのか」という疑問が生じた場合、ここに確認してください。

## アダプタアーキテクチャ

### コンポーネント関係

```
正方向変換（受信方向）                           逆方向変換（送信方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ プラットフォーム固有イベント     │                        │ モジュールが構築するメッセージ     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │  アダプタ (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (イベント変換器)    │──→│ │              │ │   │ (逆方向変換エントリポイント)   │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ プラットフォーム API 調用    │
                       │ OneBot12 標準イベント │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準レスポンス形式     │
                       │ イベントシステム         │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ モジュール (イベント処理)  │
                       └──────────────────┘
```

**コアの対称性**：
- **正方向変換**（Converter）：プラットフォーム固有イベント → OneBot12 標準イベント、元データは `{platform}_raw` に保持
- **逆方向変換**（Raw_ob12）：OneBot12 メッセージセグメント → プラットフォーム API 調用、返却は標準レスポンス形式

## AdapterManager アダプタマネージャー

`AdapterManager` は ErisPulse アダプタシステムのコアコンポーネントであり、すべてのプラットフォームアダプタの登録、起動、停止、イベント配信を管理します。

### コア機能

- **アダプタ登録**：複数のプラットフォームアダプタを登録・管理
- **ライフサイクル管理**：アダプタの起動と停止を制御
- **イベント配信**：OneBot12 標準イベントとプラットフォーム固有イベントを配信
- **設定管理**：アダプタの有効/無効状態を管理
- **ミドルウェアサポート**：OneBot12 イベントミドルウェアをサポート

### 基本的な使用方法

```python
from ErisPulse import sdk

# アダプタの登録（通常 Loader が自動で行う）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# すべてのアダプタを起動
await sdk.adapter.startup()

# 指定のアダプタを起動
await sdk.adapter.startup(["myplatform"])
# すべてのアダプタを起動
await sdk.adapter.startup()

# アダプタのインスタンスを取得
my_adapter = sdk.adapter.get("myplatform")
# または属性でアクセス
my_adapter = sdk.adapter.myplatform

# すべてのアダプタを停止
await sdk.adapter.shutdown()
```

### 起動と停止

#### アダプタの起動

```python
# すべての登録済みアダプタを起動
await sdk.adapter.startup()

# 指定のプラットフォームを起動
await sdk.adapter.startup(["platform1", "platform2"])
```

**起動フロー**：

1. `adapter.start` ライフサイクルイベントを送信
2. `adapter.status.change` イベントを送信（starting）
3. 各アダプタを並行起動
4. 起動に失敗した場合は自動的に再試行（指数バックオフ戦略）
5. 起動成功後 `adapter.status.change` イベントを送信（started）

**再試行メカニズム**：

- 最初の4回の再試行：60秒、10分、30分、60分
- 5回目以降：3時間固定間隔

#### アダプタの停止

```python
# すべてのアダプタを停止
await sdk.adapter.shutdown()
```

**停止フロー**：

1. `adapter.stop` ライフサイクルイベントを送信
2. 各アダプタの `shutdown()` メソッドを呼び出す
3. ルーティングサーバーを停止
4. イベントハンドラをクリア
5. `adapter.stopped` ライフサイクルイベントを送信

### 設定管理

#### プラットフォームの状態確認

```python
# プラットフォームが登録されているか確認
exists = sdk.adapter.exists("myplatform")

# プラットフォームが有効か確認
enabled = sdk.adapter.is_enabled("myplatform")

# in 演算子を使用
if "myplatform" in sdk.adapter:
    print("プラットフォームが存在し、有効です")
```

#### プラットフォームの一覧表示

```python
# すべての登録済みプラットフォームを取得
platforms = sdk.adapter.list_registered()

# すべてのプラットフォームとその状態を取得
status_dict = sdk.adapter.list_items()
# 戻り値: {"platform1": true, "platform2": false, ...}

# 有効なプラットフォームのリストを取得
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### イベントのリスニング

#### OneBot12 標準イベント

```python
from ErisPulse import sdk

# すべてのプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"OneBot12 メッセージを受け取りました: {data}")

# 特定のプラットフォームの標準メッセージイベントをリッスン
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"myplatform メッセージを受け取りました: {data}")

# すべてのイベントをリッスン
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"イベントを受け取りました: {data.get('type')}")
```

#### プラットフォーム固有イベント

```python
# 特定のプラットフォームの固有イベントをリッスン
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"固有イベントを受け取りました: {data}")

# すべてのプラットフォームの固有イベントをリッスン（ワイルドカード）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"固有イベントを受け取りました: {data}")
```

#### イベント配信メカニズム

`adapter.emit(event_data)` を呼び出すとき：

1. **ミドルウェア処理**：まずすべての OneBot12 ミドルウェアを実行
2. **標準イベント配信**：マッチする OneBot12 イベントハンドラに配信
3. **固有イベント配信**：元データがあれば、固有イベントハンドラに配信

**マッチルール**：

- 精確マッチ：`@sdk.adapter.on("message")` は `message` イベントのみマッチ
- ワイルドカード：`@sdk.adapter.on("*")` はすべてのイベントにマッチ
- プラットフォームフィルタ：`platform="myplatform"` は指定プラットフォームのイベントのみ配信

### ミドルウェア

#### ミドルウェアの追加

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """ログ記録ミドルウェア"""
    print(f"イベントを処理します: {data.get('type')}")
    return data  # 必須でデータを返す

@sdk.adapter.middleware
async def filter_middleware(data):
    """イベントフィルタミドルウェア"""
    # 不要なイベントをフィルタ
    if data.get("type") == "notice":
        return None  # 戻り値が None の場合、ミドルウェアチェーンはその値を無視し、元のデータをそのまま伝播
    return data  # 必須でデータを返して伝播を続ける
```

#### ミドルウェアの戻り値の契約

| 戻り値 | 行動 |
|--------|------|
| `dict` | イベントペイロードを上書き（後続のハンドラは変更後のイベントを受け取る） |
| `None` | 通過、ペイロードは変更なし（WARNINGを出力するが、明示的に`return data`を推奨） |
| `False` | **拒否**：イベントは破棄され、ハンドラには一切の副作用が発生しない |

拒否はファイアウォール、リクエスト制限、ブラックリストなど「イベントレベルで直接破棄」する場面に適しています（以前は高優先度のイベントハンドラで回避するしかありませんでした）。拒否された場合、フレームワークはTRACEログを出力し、`adapter.event.blocked` ライフサイクルフックをトリガーします（`middleware`ミドルウェア名、完全な`event`、`platform` / `event_type` / `detail_type`を含む）、イベントがなぜ反応しなかったのかを調査するのに便利です：

```python
@sdk.adapter.middleware
async def rate_limit_middleware(data):
    """リクエスト制限ミドルウェア"""
    if _is_rate_limited(data):
        return False  # 拒否：イベントは破棄
    data["rate_marked"] = True
    return data

@sdk.lifecycle.on("adapter.event.blocked")
async def on_event_blocked(data):
    print(f"イベントは {data['middleware']} によって拒否されました: {data['event_type']}")
```

#### ミドルウェアの実行順序

ミドルウェアは登録順に実行され、後から登録されたミドルウェアが先に実行されます。

> **注意**：ミドルウェアが `None` を返した場合（`return data` を忘れている場合）、フレームワークはその返り値を無視して元のデータをそのまま伝播し、warningレベルのログを出力します。これにより、個々のミドルウェアのミスがイベントチェーン全体の中断を引き起こすことはありません。

```python
# 登録順
sdk.adapter.middleware(middleware1)  # 最後に実行
sdk.adapter.middleware(middleware2)  # 中間実行
sdk.adapter.middleware(middleware3)  # 最初に実行

# 実行順：middleware3 -> middleware2 -> middleware1
```

### アダプタインスタンスの取得

#### get() メソッド

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### 属性アクセス

```python
# 属性名でアクセス（大文字小文字を区別しない）
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter 基底クラス

### 基本構造

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """アダプター設定（宣言後はフレームワークが自動管理）"""
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig  # 設定クラスを宣言
    
    # __init__ のオーバーライドは不要。フレームワークが自動的に処理：
    # - self.sdk, self.logger
    # - self.cfg（型安全な設定インスタンス、リアルタイム読み取り）
    # - self.Send, self.Request
    
    async def start(self):
        """アダプターを起動する（実装必須）"""
        cfg = self.cfg  # 自動的に読み込まれた型安全な設定
        pass
    
    async def shutdown(self):
        """アダプターをシャットダウンする（実装必須）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出す（実装必須）"""
        pass
```

### 設定管理

フレームワークは宣言的な設定管理を提供しています。dataclass で設定構造を定義すると、読み込み、検証、テンプレート生成が自動的に処理されます。

#### 単一アカウントの設定

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class TelegramConfig(BaseConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "telegram.token", "default": "Bot Token"},
        "required": True,
        "secret": True,
        "ui": {"widget": "password", "group": "basic", "order": 1},
    })
    proxy: str = field(default="", metadata={
        "description": {"i18n": "telegram.proxy", "default": "プロキシアドレス"},
        "ui": {"widget": "text", "group": "advanced", "order": 10},
    })

class TelegramAdapter(BaseAdapter):
    ConfigClass = TelegramConfig
    
    async def start(self):
        cfg = self.cfg  # 型安全、リアルタイム読み取り
        if not cfg.token:
            raise ValueError("Token が設定されていません")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 複数アカウントの設定

`BotAccountConfig` 基底クラスは `enabled` と `name` フィールドを提供します。ほとんどのアダプターはプラットフォームのプロトコルやログインレスポンスから bot_id を自動取得でき、イベント変換時にアカウント設定へ注入します。

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# ほとんどのアダプター：bot_id は実行時に自動取得されるため設定は不要
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# ログイン時に bot_id を取得できない場合は、設定でユーザーに入力してもらうことができます
@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": {"i18n": "yunhu.bot_id", "default": "ボットID"},
        "required": True,
    })
    token: str = field(default="", metadata={
        "description": {"i18n": "yunhu.token", "default": "Token"},
        "required": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            user_id = await self._login(name, account)
            await self.emit_meta("connect", user_id)
```

#### metadata の規約

フィールドの metadata は、TOML コメント生成と WebUI フォームレンダリングの両方に使用されます：

```python
metadata = {
    "description": str | dict,  # フィールドの説明（i18n 対応）
    "required": bool,         # 必須かどうか（検証 + WebUI の必須マーク）
    "secret": bool,           # 機密情報かどうか（WebUI では *** と表示、ログではマスキング）
    "example": bool,          # 永続化しないフラグ：config.toml に書き込まない（デフォルト値/テンプレートとも除外）、
                              # config.full.example にのみレンダリング；schema には "example": true のマークが付き、
                              # CLI 設定ウィザードではデフォルトでスキップ；ユーザーが手動設定した後は通常どおり永続化
    "min": number, "max": number,  # 数値範囲の検証
    "ui": {                   # WebUI コントロール設定（旧名 "webui" も互換）
        "widget": str,        # コントロールタイプ: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # グループ: "basic" | "advanced" | "connection" など
        "order": int,         # ソートの重み（小さいほど先に表示）
        "options": list,      # select コントロールの選択肢 [{label, value}]、label は i18n 対応
        "placeholder": str | dict,  # 入力フィールドのプレースホルダー（i18n 対応）
    },
    "extra": dict,            # 追加の拡張フィールド（schema へそのまま透過）
}
```

ユーザーに表示されるすべてのテキストフィールドは i18n に対応しており、統一して `{"i18n": "key", "default": "テキスト"}` 形式を使用します。純粋な文字列はそのまま透過されます（後方互換）。対応している i18n フィールド：

| フィールド | 場所 | 説明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | select コントロールの選択肢ラベル |
| `placeholder` | `ui.placeholder` | 入力フィールドのプレースホルダー |
| `group_labels` | `_schema_meta` | グループの表示名（Dashboard のセクションタイトル） |

i18n を使用する場合は、事前に翻訳キーを i18n システムへ登録しておく必要があります（詳細は [i18n ドキュメント](../../advanced/i18n.md#設定フィールドの多言語化) を参照）。

**description / placeholder / options label** の例：

```python
token: str = field(
    default="",
    metadata={
        "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
        "ui": {
            "widget": "text",
            "placeholder": {"i18n": "my_adapter.token.ph", "default": "Token を入力してください"},
        },
    },
)
mode: str = field(
    default="a",
    metadata={
        "description": {"i18n": "my_adapter.mode", "default": "モード"},
        "ui": {
            "widget": "select",
            "options": [
                {"label": {"i18n": "my_adapter.mode.a", "default": "オプションA"}, "value": "a"},
                {"label": "純粋な文字列ラベル", "value": "b"},  # 純粋な文字列はそのまま透過
            ],
        },
    },
)
```

**group_labels** の例（設定クラスの定義後に宣言）：

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "基本設定"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "高度な設定"},
    }
}
```

フレームワークの `resolve_config_schema()` は、現在の言語に応じて上記すべてのフィールドの i18n キーを自動解決します。`get_config_schema()` は i18n 辞書をそのまま透過し、フロントエンド側で解決します。

#### docstring によるフィールド説明の自動生成（v2.8.0+）

metadata で `description` が宣言されていないフィールドについては、フレームワークが設定クラスの docstring からフィールドの説明を自動抽出し、フォールバックとして使用します。一般的な 2 つのスタイルに対応しています（混用可）：

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapter の設定

    :ivar endpoint: プラットフォーム API のアドレス        # reST スタイル
    :ivar timeout: リクエストのタイムアウト秒数
    """

    endpoint: str = "https://api.example.com"   # metadata description なし → コメント/説明は docstring から取得
    timeout: int = 30

    # Google スタイルも同様にサポート（Attributes: セクション）：
    # Attributes:
    #     endpoint: プラットフォーム API のアドレス
```

優先順位：**metadata description > docstring のフィールド説明 > 空**。
i18n 辞書形式の description は影響を受けません（常に優先されます）。

#### ネストした設定（v2.8.0+）

フィールドの型がネストした dataclass の場合、フレームワークは再帰的に処理します：schema は `"type": "table"` + `"fields"` のサブツリーとして表現され（WebUI では折りたたみ可能なネストグループとしてレンダリング）、TOML テンプレートでは `[サブテーブル]` セクションとしてレンダリングされます。デフォルト値 / 補完 / 検証 / i18n 解決はいずれも再帰的に適用されます。

```python
@dataclass
class RetryConfig(BaseConfig):
    """リトライポリシー

    :ivar max_retries: 最大リトライ回数
    """
    max_retries: int = 3
    backoff: float = 0.5

@dataclass
class MyConfig(BaseConfig):
    """MyAdapter の設定"""
    endpoint: str = "https://api.example.com"
    retry: RetryConfig = field(default_factory=RetryConfig)   # ネストした設定セクション
```

生成される TOML テンプレート：

```toml
endpoint = "https://api.example.com"

[retry]
# 最大リトライ回数
max_retries = 3
backoff = 0.5
```

> ネストした型には直接の型アノテーションを推奨します。文字列アノテーション（遅延評価のシナリオなど）の場合は、型が設定クラスの所在モジュールのグローバル名前空間、`__qualname__` の外側クラスの名前空間、またはクラス属性から名前で解決できることを保証する必要があります。

#### 永続化されない example フィールド（v2.8.0+）

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

`example: True` を持つフィールドは以下のとおりです：

- config.toml には書き込まれない（アダプター/モジュールの設定テンプレートとデフォルト値のいずれからも除外され、実行時はコード上のデフォルト値が使用される）
- プロジェクト内の `config.full.example` にのみレンダリングされる（ユーザーの参考用。必要に応じて config.toml へ手動でコピー）
- schema には `"example": true` のマークが付く（パネル側で表示ポリシーを自由に決定可能）。CLI 設定ウィザードではデフォルトでスキップ
- ユーザーが手動でこのキーを設定した後は、通常どおり永続化・ホットアップデートされる（ユーザーの明示的な意図が優先）

「冗長でほとんど触れることのない」高度な設定項目に適しており、ユーザーの config.toml を最小限に保てます。

> ⚠️ `_schema_meta` はクラスレベルのメタデータです（設定フィールドではありません）。dataclass のクラス本体内で宣言する場合は、必ず `ClassVar` アノテーションを付ける必要があります（`_schema_meta: ClassVar[dict] = {...}`）。そうしないと、dataclass に通常のフィールドと見なされます。フレームワークはアンダースコア接頭辞のフィールドに対して防御的な除外を行っています（schema / テンプレート / デフォルト値 / 検証出力のいずれにも含まれません）が、それでも規約に従った宣言を推奨します。

### 宣言的な翻訳キー（v2.7.0+）

アダプターは `ConfigClass` を宣言するのと同じように、ネストクラス `I18nClass` によって翻訳キーを一元的に宣言できます。フレームワークは `__init__` の段階（設定テンプレート生成の前）で、宣言されたすべての翻訳キーを自動登録するため、設定の説明で参照される i18n キーがテンプレート生成時に利用可能であることが保証されます。

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API アドレス",
            zh_TW="API アドレス",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="プラットフォーム Token",
            zh_TW="プラットフォーム Token",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> ``I18nKey.default`` は**言語に依存しないフォールバックテキスト**であり、どの言語にも登録されません。
> 翻訳を有効にするには、少なくとも 1 つの言語パラメータを明示的に渡す必要があります。

詳細な使い方（キーのパス規則、明示的な key パラメータなど）については、[i18n ドキュメント](../../advanced/i18n.md#推奨される書き方i18nclassによる翻訳キーの宣言v270) を参照してください。

### 宣言的なイベント拡張メソッド（v2.7.0+）

アダプターは `EventMixin` を通じて、プラットフォーム固有のイベント拡張メソッドを一元的に宣言できます。フレームワークが現在のプラットフォームへ自動登録します。

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """チャット名を取得する"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """公式メッセージかどうかを判定する"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

登録後は、イベントオブジェクトからこれらのメソッドを直接呼び出せます：

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] 公式メッセージを受信しました")
```

> アダプターのイベント拡張メソッドは、自身のプラットフォーム（``self._platform``）に登録されます。
> モジュールでクロスプラットフォームのイベント拡張が必要な場合は、既存の ``register_event_mixin()`` API を使用してください。

#### アカウントの解決

アダプターが `call_api` を実装する際は、アカウント識別子を具体的なアカウント設定へ解決する必要があります。フレームワークはアカウントのバインディング（`Using()` またはイベントチェーンによる自動バインディングの結果）を標準フィールド `account_id` として `call_api` に渡し、アダプターの実際の消費方法に応じて自動的に適応させます。3 つの消費形態のいずれかを選択でき、フレームワークはシグネチャのパラメータ名と関数本体内の定数によって検出するため、パラメータの位置は問いません：

```python
# 形態 1（推奨）：シグネチャで標準名を宣言
async def call_api(self, endpoint: str, account_id: str | None = None, **params):
    name, account = self._resolve_account(account_id)
    # name: アカウント名, account: 設定インスタンス

# 形態 2（既存互換）：旧名 _account_id。フレームワークが account_id を自動的に旧名へ書き換えて渡す
async def call_api(self, endpoint: str, _account_id: str | None = None, **params):
    name, account = self._resolve_account(_account_id)

# 形態 3：関数本体内で params から取得（定数検出により識別される）
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
```

> アダプターがアカウントフィールドを消費しない場合、フレームワークはそのフィールドを除去し（プラットフォームパラメータへの混入を防止）、WARNING を一度出力します。単一アカウントのアダプターでは消費しなくても構いません（解決は最初に有効化されているアカウントへフォールバックします）。

解決ポリシー：アカウント名の一致 → `bot_id` フィールドの一致 → その他の str フィールドの一致 → 最初に有効化されているアカウント。

**実行時の識別と永続化**（2.12+）：アダプターは接続の確立時 / イベントの到着時に `self.update_bot_id(account_name, bot_id)` を呼び出します。フレームワークは bot_id → アカウントのレジストリを維持し（解決チェーンの第一優先度）、値が変化した際に `accounts.<アカウント名>.bot_id` を設定ストレージへ書き込みます：再起動後はアカウントインスタンスの再構築時に bot_id が付与された状態になるため、第 2 アカウントなどのシナリオにおける解決がアカウントアクティビティによるバックフィルに依存しなくなります（再起動時のウィンドウ期間を解消）。

#### 設定のホットアップデート

サブクラスは `on_config_update()` をオーバーライドして設定変更に応答できます：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token が更新されました。再接続します")
```

### 初期化プロセス

フレームワークは `BaseAdapter.__init__(self, sdk=None)` 内で以下の処理を自動的に行います：

1. **SDK 参照**：`self.sdk`、`self.logger` を設定
2. **Send/Request ファクトリ**：`self.Send` と `self.Request` を作成
3. **設定テンプレート**：`ConfigClass` が宣言されている場合、デフォルトの設定テンプレートを自動生成（初回のみ）
4. **アカウントテンプレート**：`AccountConfigClass` が宣言されている場合、デフォルトのアカウントテンプレートを自動生成（初回のみ）
5. **EventMixin の登録**：`EventMixin` が宣言されている場合、`AdapterManager` によるプラットフォーム名の注入後に自動登録

設定は `self.cfg` / `self.accounts` からリアルタイムに読み込まれます（アクセスのたびに設定ストレージから最新値が読み取られます）。`self.config` は `self.cfg` の互換エイリアスとして引き続き使用できます。

ほとんどのアダプターでは `__init__` のオーバーライドは不要です。カスタム初期化が必要な場合：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # sdk を渡す
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send メッセージ送信 DSL

### 継承関係

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Send 嵌套クラス、BaseAdapter.Send から継承"""
        pass
```

### 利用可能な属性

`Send` クラスは呼び出し時に自動的に以下の属性を設定します：

| 属性 | 説明 | 設定方法 |
|-----|------|---------|
| `_target_id` | 目標ID | `To(id)` または `To(type, id)` |
| `_target_type` | 目標タイプ | `To(type, id)` |
| `_target_to` | 簡略化された目標ID | `To(id)` |
| `_account_id` | 送信アカウントID | `Using(account_id)` |
| `_adapter` | アダプタインスタンス | 自動設定 |
| `_at_user_ids` | @ユーザーIDリスト | `At(user_id)` |
| `_reply_message_id` | レスポンスするメッセージID | `Reply(message_id)` |
| `_at_all` | @全員か | `AtAll()` |

> **推奨**：`self.send_context` 属性を使って `target_type`、`target_id`、`account_id` を一括で取得するようにしてください。個々のインスタンス変数にアクセスするよりも明確です。

### フレームワーク補助メソッド

| メソッド/属性 | 説明 |
|-----------|------|
| `self._apply_modifiers(message)` | At/AtAll/Reply 修飾子の状態をメッセージセグメントリストにマージする |
| `self.send_context` | `target_type`、`target_id`、`account_id` の辞書を返す；`account_id` が明示的に指定されていない場合は、イベント配信チェーンのトリガーアカウントをデフォルトにする |

### 基本メソッド

アダプタは `Raw_ob12` を実装するだけで、標準メソッド（Text/Image/Voice/Video/File）は `SendDSL` 基底クラスから継承され、デフォルトで `Raw_ob12` に委譲されます：

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """OneBot12 メッセージセグメント → プラットフォーム API（必須実装）"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File は基底クラスから継承され、Raw_ob12 にデフォルトで委譲されるため、再実装は不要
    # プラットフォーム固有のロジックが必要な場合は、単一メソッドをオーバーライドすることができる：
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### チェーン修飾メソッド

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self
```

## イベント変換器

### 変換フロー

```
プラットフォーム固有イベント
    ↓
Converter.convert()
    ↓
OneBot12 標準イベント
```

### 必須フィールド

変換後のイベントはすべて以下のフィールドを含む必要があります：

```python
{
    "id": "イベントの唯一識別子",          # 同一アカウントで同じイベントを再送信する際は同じ値にする必要がある（フレームワークが重複を防ぐ）
    "time": 1234567890,           # 10桁の Unix タイムスタンプ
    "type": "message/notice/request/meta",
    "detail_type": "イベントの詳細タイプ",
    "platform": "プラットフォーム名",
    "message_id": "メッセージID",        # メッセージ系イベントは必須
    "self": {
        "platform": "プラットフォーム名",
        "user_id": "ロボットID"     # bot_id と一致する必要がある
    },
    "{platform}_raw": {...},       # 元データ（必須）
    "{platform}_raw_type": "..."    # 元のタイプ（必須）
}
```

> イベント `id` にはアカウントの次元が必要です：同一アカウントで同じイベントを再送信する際は `id` を同じにする必要があります。異なるアカウントが同じグループ/会話で同じ物理メッセージを受け取る場合、`id` は異なる必要があります（たとえば `f"{self.user_id}:{post_type}:{message_id}"` のように）。

### 複数アカウントの重複受信（フレームワークが注入するフィールド）

複数アカウントアダプタの複数のアカウントが同じグループ/会話で、同一の物理メッセージが各アカウントに順次到達する場合、フレームワークは `ErisPulse.framework.cross_account_policy != "off"` の場合、内容ベースの関連付け（同じプラットフォーム + 同じ会話 + 同じ送信者 + 同じ `alt_message` が短い時間内に）を自動的に行い、アダプタは関与する必要はありません：

- `mark`：後続のコピーは `multi_receipt` というトップレベルのフィールド `{"event_id": 初回受理イベントのID, "self_id": 初回受理アカウント}` を注入して通常通り配信され、モジュールはこのフィールドを読んで裁決する
- `drop`：後続のコピーは配信の入口で直接破棄される

`multi_receipt` はフレームワークが注入するオプションのフィールドであり、アダプタの変換器は生成も消費もしません。ポリシーはデフォルトで `off` で、イベントの構造は既存の契約と完全に一致します。

#### 3層の重複防止メカニズムの役割分担

| メカニズム | 設定 | 拦截するもの | 判定依据 |
|------|------|----------|----------|
| イベントの冪等性重複防止 | `ErisPulse.framework.event_dedupe`（デフォルト有効） | 同一イベント id の再接続再送信（同一接続） | イベント `id` |
| 本アカウントの自己発言フィルタ | `ErisPulse.event.message.ignore_self`（デフォルト有効） | 受信アカウント自身のメッセージ（送信者 == 受信アカウント） | `self.user_id` vs `user_id` |
| 複数アカウントの重複受信 | `ErisPulse.framework.cross_account_policy`（デフォルト `off`、`drop` 有効） | **同一物理メッセージが他のアカウントのコピー**——複数アカウントが同じグループで bot A が発言し、bot B も同様のメッセージを1つ受け取る | 内容ベースの関連付け（同プラットフォーム + 同会話 + 同送信者 + 同内容、短い時間内）、キーには self_id は含まれない |

**典型的なシナリオ——複数アカウントが同じグループで発言**：bot A が発言し、同じグループ内の他のアカウント（bot B）も同様のメッセージを1つ受け取る。`cross_account_policy = "drop"` を有効にすると、後続のアカウントのコピーは配信の入口で破棄され、どのモジュールも1回だけ表示されます。

`ignore_self` と `cross_account_policy` の意味は直交しており、2つの組み合わせで表示回数が決まります：

| 組み合わせ | フォローミュールが bot A のメッセージを見る回数 |
|------|--------------------------|
| `drop` + `ignore_self = true`（デフォルト） | 0 または 1 回（先に到着したコピーが A 自身の接続から `ignore_self` でブロックされた場合）——**2回になることはない** |
| `drop` + `ignore_self = false` | 恒定で1回（先に到着したコピーが A 自身の接続からブロックされない限り） |

> `ignore_self` の意味を「自身の全アカウントを排除する」に拡張しないでください：この判定は受信イベントの `self.user_id`（バインドが確立していない期間に失敗する可能性がある、上記の実行時境界を参照）に依存しており、複数アカウントの関連付けは内容ベースの判定であり、`self` 情報に依存しません。また、「各アカウントの受信」は複数アカウントのログや同期系モジュールの既存の依存関係であり、その意味を狭めるのは暗黙の破壊です。複数アカウントの重複は `cross_account_policy` に任せてください。

### 変換器の例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """プラットフォーム固有イベントを OneBot12 標準形式に変換"""
        if not isinstance(raw_event, dict):
            return None
        
        # イベント ID を生成
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # 時間スタンプを変換
        timestamp = raw_event.get("timestamp")
        if timestamp and timestamp > 10**12:
            timestamp = int(timestamp / 1000)
        else:
            timestamp = int(timestamp) if timestamp else int(time.time())
        
        # イベントタイプを変換
        event_type = self._convert_type(raw_event.get("type"))
        detail_type = self._convert_detail_type(raw_event)
        
        # 標準イベントを構築
        onebot_event = {
            "id": str(event_id),
            "time": timestamp,
            "type": event_type,
            "detail_type": detail_type,
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
```

## 接続管理

### start() の2つの正しい書き方

クライアントモードのアダプタ（WebSocketクライアント、HTTPポーリングなど）は `start()` で常駐接続ループを起動する必要があります。フレームワークは2つの書き方をサポートしていますが、**どちらか一方のみ使用できます**。

**書き方1：spawn-返却式（推奨）**——`spawn_client_loop()` でループをプラットフォームに属するバックグラウンドタスクとしてスケジュールし、`start()` は即座に返ります：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # ループタスクは self._platform に属するため、shutdown でフレームワークが自動的にキャンセル
        self.spawn_client_loop(self._connect_loop())
        # start はここで終了——"起動成功"と即座に返す。接続失敗はループ内で再試行

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # 切断は例外 → 下方の退避
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # ループ内で再試行
```

**書き方2：常駐式**——`start()` で接続ループを `await` し、決して返りません：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # 常駐で返らない；ループが例外を投げた場合、フレームワークの再試行チェーンに渡される
```

2つの書き方の違いと共通点：

| | spawn-返却式 | 常駐式 |
|---|---|---|
| `start()` の返り時点 | ループ起動後即座に返る | 接続ループが終了/失敗した時（フレームワークは退避戦略で再試行） |
| 接続失敗の処理 | ループ内で例外を捕まえて退避 | 例外を上昇させ、フレームワークの再試行チェーンに渡す |
| 適用場面 | 複数接続、ルーティング登録後に他のタスクを起動する必要がある場合 | "接続即起動"の意味を持つ単純な実装 |

`spawn_client_loop(coro, *, name="client_loop")` は書き方1のスケジューラーの入り口です：タスクは `self._platform` に属して登録され、アダプタの `shutdown()` 時にフレームワークが自動的にキャンセルされます。ループ内で未捕獲の例外は自動的に記録されます（意図的な切断再接続はループ内で捕まえてください）。

> **唯一の誤った書き方は混用すること**：spawn の後に `await` で同じループを実行すると、`start()` は即座に返る意味を失い、タスクのキャンセル経路が予測不可能になります。

### 接続モードの半完成基底クラス

上記の2つの書き方のほか、最も一般的な2つの接続モードに対してフレームワークは「半完成」の基底クラスを提供しています（`ErisPulse.Core.Bases.adapter_patterns`、ルートパッケージから直接インポート可能）：`start` / `shutdown` のライフサイクルの編集はすべて基底クラスが行い、サブクラスは業務フックを実装するだけです。

#### PollingAdapter（HTTPポーリング型）

「クライアントが定期的にイベントを取得する」プラットフォーム（Telegram getUpdates型）に適しています。基底クラスはspawn-返却式で常駐ポーリングループを起動し、取得失敗は自動的に記録され指数退避されます（基数1秒、上限60秒、成功後はゼロに戻る；定数 `POLLING_ADAPTER_BACKOFF_BASE_SECS` / `POLLING_ADAPTER_BACKOFF_MAX_SECS` は `Core/constants.py` で調整可能）：

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # ポーリング間隔はデフォルト5秒；ConfigClass で poll_interval フィールドを宣言した場合は設定値が優先される（ホットアップデート有効）
    poll_interval = 5.0

    async def fetch_events(self):
        """プラットフォーム固有イベントを一括取得（例外は基底クラスが退避し、try/exceptは不要）"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """1件の固有イベントをOneBot12に変換；Noneを返すとスキップ"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # 普通のアダプタと同じ
```

最小実装面：`fetch_events` / `convert_one` / `call_api`。`start()` でループを起動して即座に返る；`shutdown()` はサブクラスで処理する必要がない（ポーリングループはownerに属して自動的にキャンセルされる）。

#### WebhookAdapter（HTTPコールバック型）

「プラットフォームがコールバックを送信する」プラットフォームに適しています。基底クラスの `start()` はフレームワークの router にコールバック受信ルートを登録します（最終パスは `/{プラットフォーム名}/webhook`、POSTメソッド）、登録は `owner_scope` で行われる——アダプタのアンロード時にownerに従って自動的にクリーンアップされるため、手動で登録解除する必要はない：

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """オプションフック：コールバック検証（デフォルトで許可；Falseを返すと基底クラスが403で拒絶）"""
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """コールバックペイロードをOneBot12に変換；Noneを返すとスキップ"""
        return self.converter.convert(payload)

    async def call_api(self, endpoint: str, **params):
        ...  # 普通のアダプタと同じ
```

最小実装面：`convert` / `call_api`（`verify_request` はオプション）。コールバックアドレスは `sdk.adapter.get_connection_info(platform)` で取得してプラットフォームのバックエンドに設定する。検証に失敗したリクエストは403、ペイロード解析に失敗したリクエストは400、正常なリクエストは `{"status": "ok"}` を返す。

#### 3つのモードの使い分け

| プラットフォームプロトコル | 継承 | フレームワーク |
|---|---|---|
| プラットフォームが接続してくる（WebSocketサーバー） | `BaseAdapter` | `epsdk create adapter`（デフォルト ws-server） |
| 自分がポーリングする（HTTPポーリング） | `PollingAdapter` | `epsdk create adapter --template polling` |
| プラットフォームがコールバックしてくる（HTTPコールバック） | `WebhookAdapter` | `epsdk create adapter --template webhook` |

実行可能な完全な例はリポジトリの `examples/example-adapter/`（ws-server）、`examples/example-adapter-polling/`、`examples/example-adapter-webhook/` を参照してください。

### WebSocket 接続

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """WebSocketルートを登録"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket):
        """WebSocket接続ハンドラ"""
        self.connection = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                onebot_event = self.convert(data)
                if onebot_event:
                    await self.adapter.emit(onebot_event)
        except WebSocketDisconnect:
            self.logger.info("接続が切断されました")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket) -> bool:
        """WebSocket認証"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook 接続

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """WebHookルートを登録"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """WebHookリクエストハンドラ"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> コールバック型のプラットフォームでは、上記の登録/検証/クリーンアップの編集を手動で書く必要はありません——`[WebhookAdapter` 半完成基底クラス](#接続モード半完成基底クラス)を継承し、`convert`（`verify_request` をオーバーライドする場合も可）を実装するだけです。

> **ルート情報の取得**：アダプタが登録したルート（HTTP、WebSocket、SSE）は、`sdk.adapter.get_connection_info(platform)` と `sdk.router.get_module_urls(module_name)` を使って完全な接続アドレス（`base_url` + パス）を取得できます。[アダプタ開発入門 - 接続情報とルート発見](getting-started.md#9-接続情報とルート発見)と [SSE 支持](getting-started.md#10-sse-server-sent-events-サポート)を参照してください。

## API レスポンス標準

フレームワークは `make_response()` と `make_error()` メソッドを使って標準化されたレスポンスを構築し、手動でのレスポンス辞書の構築は不要です。

### 成功レスポンス

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return self.make_response(
            data=raw_response.get("data"),
            message_id=raw_response.get("data", {}).get("message_id", ""),
            raw=raw_response,
        )
    except Exception as e:
        return self.make_error(message=str(e), raw=None)
```

### 手動でレスポンス構築（旧版方式は互換性あり）

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok",
        "retcode": 0,
        "data": {...},
        "message_id": "msg_id",
        "message": "",
        "myplatform_raw": raw_response
    }
```

## 複数アカウントサポート

### 宣言的設定（推奨）

`AccountConfigClass` を宣言して設定クラスを定義した後、フレームワークは自動的に複数アカウントのロード、検証、テンプレート生成を管理します：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={"description": "Bot ID", "required": True})
    token: str = field(default="", metadata={"description": "Token", "required": True, "secret": True})

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"アカウント {name}: {account.bot_id} を起動します")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, account_id: str | None = None, **params):
        name, account = self._resolve_account(account_id)
        # account.token, account.bot_id などのフィールドを使用
```

### アカウント設定ファイル

```toml
[MyAdapter.accounts.account1]
bot_id = "bot_001"
token = "token1"
enabled = true

[MyAdapter.accounts.account2]
bot_id = "bot_002"
token = "token2"
enabled = true
```

### アカウント指定での送信

```python
# Using メソッドでアカウントを指定
my_adapter = adapter.get("myplatform")

# イベントの self.user_id を使用する（推奨、最も汎用的）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# アカウント名を指定
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### イベントのアカウント識別子と Using の関係

フレームワークのイベント返信メカニズムは、イベントの `self` フィールドからアカウント識別子（`account_id` が優先され、`user_id` がバックアップ）を抽出し、`Using` に注入します。アダプタの開発者は、Converter が生成するアカウント識別子がアカウント設定（アカウント名や `bot_id` など）と一致することを保証する必要があります。

**フレームワークが注入する動作**：

```python
# フレームワークがアカウント識別子を抽出するロジック（account_id が優先され、user_id がバックアップ）
account = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# アカウント識別子が空でない場合に Using を注入
if account:
    send_chain = send_chain.Using(account)
```

> **重要な点**：アダプタが1つの Bot 設定しか使用しない場合でも、Converter がアカウント識別子を正しく設定している限り、フレームワークはそれを `Using` に注入します。アダプタは、この識別子が `AccountConfigClass` のアカウント名や `bot_id` などのフィールドと一致していることを保証する必要があります。識別子が空の場合、フレームワークは `Using` を注入せず、その場合、送信は未指定アカウントで処理されます——最初の有効なアカウントにフォールバックします。

明示的に渡された `account_id` が解析できない場合、フレームワークは WARNING を記録し、最初の有効なアカウントにフォールバックします；WARNING に含まれる `platform` / `account_id` / `account` は、アカウントに属さないイベントの原因を特定するのに使用できます。

**イベント処理チェーン内の自動バインディング**：イベント処理チェーン内で送信メソッドを呼び出す際は**明示的に `Using()` を指定する必要はありません**——フレームワークはイベント処理の入口でトリガーイベントのアカウント識別子を注入し、`Send` / `Api` / `Request` チェーンが明示的に `Using()` を指定していない場合、その上下文に基づいてデフォルトでバインディングされます（明示的な `Using()` は常に優先されます；タイマー / スタートタスクなどのイベント上下文がない場面ではデフォルトアカウントの意味が維持されます）。イベントチェーンの自動バインディングは ErisPulse **2.12+** が必要です。

> イベント `self.user_id` / `self.account_id` の代位の生成契約は[イベント変換標準](../../standards/event-conversion.md)を参照してください；このフィールドが恒常的に存在することがアカウント解析のフォールバック意味の前提です——存在しない場合、最初の有効なアカウントにフォールバックし、複数アカウントの場合は「デフォルトアカウントから送信される」ことになります。

## エラー処理

### 接続再試行

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(f"接続に失敗しました、{wait_time}秒後に再試行します")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API エラー処理

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 推奨は SDK 内部のクライアントを使用
        from ErisPulse.Core import client
        from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self._standardize_response(response)
    except ClientTimeoutError:
        self.logger.error(f"リクエストがタイムアウトしました: {endpoint}")
        return self._error_response("リクエストがタイムアウトしました", 32000)
    except ClientError as e:
        self.logger.error(f"ネットワークエラー: {e}")
        return self._error_response("ネットワークリクエストに失敗しました", 33000)
    except Exception as e:
        self.logger.error(f"不明なエラー: {e}")
        return self._error_response(str(e), 34000)
```

> **互換性**：`aiohttp.ClientSession` を使用する古いアダプタコードは影響を受けません。`aiohttp.ClientError` を捕まえることができます。2つの方法は共存できます。新しいコードは `sdk.client` + ErisPulse の例外体系を使用することを推奨します。

## Bot 状態管理

AdapterManager には Bot 状態の追跡システムが内蔵されており、すべての登録された Bot のオンライン状態、アクティブ時間、およびメタ情報を自動的に管理します。

### 自動発見メカニズム

アダプタが `adapter.emit()` を使ってイベントを送信するとき、フレームワークはイベントの `self` フィールドを自動的にチェックします：

- **meta イベント**：`detail_type` に応じて対応する操作を実行（connect で登録/ disconnect でオフラインをマーク/ heartbeat でアクティブ時間を更新）
- **普通のイベント**（message/notice/request）：Bot の自動発見とアクティブ時間の更新

```python
# self フィールドを含むすべてのイベントは自動発見をトリガーします
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" は自動的に登録され（最初に出現した場合）、アクティブ時間を更新されます
```

### Meta イベントタイプ

| `detail_type` | 説明 | フレームワークの動作 |
|---|---|---|
| `connect` | Bot が接続 | Bot を登録し、`adapter.bot.online` ライフサイクルイベントをトリガー |
| `disconnect` | Bot が切断 | Bot のオフラインをマークし、`adapter.bot.offline` ライフサイクルイベントをトリガー |
| `heartbeat` | Bot のハートビート | Bot のアクティブ時間とメタ情報を更新 |

### アダプタが Meta イベントを送信

送信方法（`emit_meta()` で1行送信、ハートビートイベントと手動構成形式）は [アダプタのベストプラクティス - Bot 状態管理と Meta イベント](best-practices.md#bot-状態管理と-meta-イベント) を参照してください。

### `self` フィールドの拡張情報

`self` フィールドは必須の `platform` と `user_id` の他に、以下のオプションフィールドをサポートします：

| フィールド | 説明 |
|---|---|
| `user_name` | Bot のユーザー名 |
| `nickname` | Bot のニックネーム |
| `avatar` | Bot のアイコン URL |
| `account_id` | 複数アカウントの識別子 |

### Bot 状態の照会

照会 API（`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`）は [アダプタシステム API - Bot 状態管理](../../api-reference/adapter-system.md#bot-状態管理) を参照してください。

### Bot ライフサイクルの監視

`adapter.bot.online` / `adapter.bot.offline` ライフサイクルイベントの表と監視例は [アダプタシステム API - Bot 状態管理](../../api-reference/adapter-system.md#bot-状態管理) を参照してください。



### SendDSL 详解

# SendDSL 詳細解説

> [!TIP]
> **この記事を読むべきとき**：アダプター開発パスでは必読（送信 DSL）。不要な場合はスキップしても、他の機能の利用には影響しません。


SendDSL はメッセージ送信を一連のチェーンで完結させます：ターゲット指定、@ / 返信、リトライ / タイムアウト / 遅延、一括送信まで、1 行のチェーン呼び出しで実現できます。本記事では、送信メソッド、修飾メソッド、送信ルール、および送信パイプラインの内部メカニズムを解説します。

## 基本的な呼び出し方法

### 1. タイプと ID を指定

```python
await adapter.Send.To("group", "123").Text("Hello")
```

### 2. ID のみ指定

```python
await adapter.Send.To("123").Text("Hello")
```

### 3. 送信アカウントを指定

```python
await adapter.Send.Using("bot1").Text("Hello")
```

### 4. 組み合わせて使用

```python
await adapter.Send.Using("bot1").To("group", "123").Text("Hello")
```

## メソッドチェーン

```mermaid
flowchart LR
    A["Using / Account<br/>（送信アカウントを選択、任意）"] --> B["To<br/>（ターゲットのタイプと ID を選択）"]
    B --> C["修飾メソッド<br/>At / Reply / Expire / ForMember など"]
    C --> D["送信メソッド<br/>Text / Image / Voice / Video / File / Location / Raw_ob12"]
    D --> E["asyncio.Task を返す"]
```

## 送信メソッド

すべての送信メソッドは `asyncio.Task` オブジェクトを返します。

### 基本メソッド（基底クラス組み込み）

以下の標準メソッドは `SendDSL` 基底クラスに組み込み実装されており、**デフォルトで `Raw_ob12` に委譲**されます。アダプターのサブクラスで再実装しなくてもそのまま使用でき、IDE の補完にも対応します：

| メソッド名 | 説明 | 戻り値 |
|--------|------|---------|
| `Text(text: str)` | テキストメッセージを送信 | `asyncio.Task` |
| `Image(file: bytes \| str)` | 画像を送信 | `asyncio.Task` |
| `Voice(file: bytes \| str)` | 音声を送信（OneBot12 の `audio` セグメント） | `asyncio.Task` |
| `Video(file: bytes \| str)` | 動画を送信 | `asyncio.Task` |
| `File(file: bytes \| str, filename: str = None)` | ファイルを送信 | `asyncio.Task` |
| `Location(latitude: float, longitude: float, title: str = "", content: str = "")` | 位置情報メッセージを送信（OneBot12 の `location` セグメント） | `asyncio.Task` |

アダプターは個々の標準メソッドをオーバーライドして、プラットフォーム固有のロジックを提供できます：

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs):
        # 実装必須
        ...

    # 任意：プラットフォーム固有のロジックを提供するため Text をオーバーライド
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### プロトコルメソッド

| メソッド名 | 説明 | 戻り値 | 必須か |
|--------|------|---------|---------|
| `Raw_ob12(message)` | OneBot12 形式のメッセージを送信 | `asyncio.Task` | **実装必須** |

> **重要**：`Raw_ob12` はアダプターの中核メソッドであり、**実装必須**です。逆変換（OneBot12 → プラットフォーム）の統一エントリーポイントです。未実装の場合、基底クラスは error ログを記録し、標準エラーレスポンス（`status: "failed"`、`retcode: 10002`）を返します。標準メソッド（`Text`、`Image` など）はデフォルトで `Raw_ob12` に委譲されます。

### プラットフォーム固有メソッド

アダプターは `Send` サブクラスにプラットフォーム固有の送信メソッドを追加できます（`event.supports()` / `event.available_methods()` に認識されます）：

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # プラットフォーム固有メソッド
    def Sticker(self, sticker_id: str):
        return self.Raw_ob12([{"type": "sticker", "data": {"id": sticker_id}}])
```

## 修飾メソッド

修飾メソッドはチェーン呼び出しをサポートするために `self` を返します。

### At メソッド

```python
# 単一ユーザーに @
await adapter.Send.To("group", "123").At("456").Text("こんにちは")

# 複数ユーザーに @
await adapter.Send.To("group", "123").At("456").At("789").Text("皆さんこんにちは")
```

### AtAll メソッド

```python
# 全メンバーに @
await adapter.Send.To("group", "123").AtAll().Text("皆さんこんにちは")
```

### Reply メソッド

```python
# メッセージに返信
await adapter.Send.To("group", "123").Reply("msg_id").Text("返信内容")
```

### 修飾の組み合わせ

```python
await adapter.Send.To("group", "123").At("456").Reply("msg_id").Text("@したメッセージへの返信")
```

### プラットフォーム専用修飾メソッド

組み込みの `At`/`AtAll`/`Reply` に加え、アダプターは**プラットフォーム専用の修飾メソッド**を定義できます。この種のメソッドは**`self` を返すだけ**で、デコレーターは一切不要です——フレームワークが自動的に識別します：

- `self`（SendDSL インスタンス）を返す → 修飾メソッド。送信ラップやライフサイクルイベントをトリガーせず、チェーンを継続
- `Task`/`Awaitable` を返す → 送信メソッド

```python
class Send(SendDSL):
    def Raw_ob12(self, message, **kwargs): ...

    # 修飾メソッド：self を返し、送信しない
    def Expire(self, seconds: int):
        self._expire = seconds
        return self

    def ForMember(self, user_id: str):
        self._member = user_id
        return self

    # 送信メソッド：Task を返す。修飾メソッドが設定した状態に依存
    def Board(self, content: str, **kwargs):
        return self.Raw_ob12([{"type": "board", "data": {"text": content}}])
```

使用例：

```python
# 修飾メソッドは連続してチェーンで積み重ね可能
await adapter.Send.To("group", "big").Expire(3600).ForMember("114").Board("ボードの内容")
```

## Event ラッパークラスでの修飾メソッドの使用

> [!NOTE]
> `reply(via=)` と `event.send_chain()` の本機能には ErisPulse **2.7.0+** が必要です。

`event.reply()` はデフォルトで `at_sender`/`at_users`/`at_all`/`quote` などの組み込み修飾パラメータのみを公開しています。プラットフォーム専用修飾メソッドを使用するには、2 つの方法があります：

### 方法 1：reply() の via パラメータ

少数の既知の修飾メソッドに適しています：

```python
await event.reply("ボードの内容", method="Board",
                  via=[("Expire", 3600), ("ForMember", "114514")])
```

`via` はリストであり、各要素は次の形式を取れます：

| 形式 | 等価なチェーン呼び出し |
|------|-------------|
| `"Name"` | `.Name()` |
| `("Name", arg1, arg2)` | `.Name(arg1, arg2)` |
| `("Name", (arg1,), {kw: val})` | `.Name(arg1, kw=val)` |

### 方法 2：event.send_chain()

**連続する複数の修飾メソッド**や**コンテンツ引数を持たないアクション型メソッド**（取り消し、削除など）に適しています。`send_chain()` は `To`/`Using` が設定済みの送信チェーンを返し、任意の修飾メソッドと送信メソッドを自由に追加できます：

```python
# プラットフォーム専用修飾メソッド + ボード送信
await event.send_chain().Expire(3600).Board("1時間後に失効")

# 連続する複数の修飾メソッド
await (event.send_chain()
       .Expire(3600)
       .ForMember("114514")
       .Board("ボードの内容", content_type="markdown"))

# 組み込み修飾メソッドも同様に使用可能
await event.send_chain().At("123").Reply("msg_id").Text("hi")

# コンテンツ引数を持たないアクション型メソッド
await event.send_chain().DismissBoard()
```

> `send_chain()` が返すのは完全な SendDSL インスタンスであるため、**すべてのチェーン機能が利用可能**です——修飾メソッドだけでなく、送信ルールや一括構築も含まれます：

```python
# 送信ルール：リトライ + タイムアウト + 成功コールバック
await (event.send_chain()
       .Retry(3).Timeout(10)
       .Hook(lambda r: print("送信成功"))
       .Text("確実な送信"))

# 遅延送信 + プラットフォーム修飾 + ボード
await event.send_chain().Defer(5).Expire(3600).Board("遅延ボード")

# 一括構築モード
results = await (event.send_chain()
                 .Build()
                 .Text("1文目").Image("pic.jpg").Text("2文目")
                 .send_all())
```

## アカウント管理

### Using メソッド

`Using()` はメッセージ送信に使用するアカウントを指定するために使います。渡された識別子は、以下の優先順位で具体的なアカウントにマッチします（解決はフレームワークが自動的に行います）：

1. **アカウント名** — 設定のキー名（例：`"default"`、`"bot1"`）
2. **`bot_id` フィールド** — アカウント設定内の `bot_id` フィールド（実行時にアダプターが書き込むもので、通常はボットの `self.user_id`）
3. **任意の str フィールド** — 設定内のその他の文字列フィールド
4. **フォールバック** — 最初に有効になっているアカウント

```python
# アカウント名を使用
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# bot_id を使用（通常はイベント内の self.user_id）
await adapter.Send.Using("bot_123").To("user", "123").Text("Hello")
```

> イベント処理のチェーン内で明示的な `Using()` がない場合、フレームワークはイベントを発生させたアカウントを自動的にバインドします（[シームレスなシンタックスシュガー](#シームレスなシンタックスシュガー) を参照）。タイマー／起動タスクなどイベントコンテキストがないシナリオではデフォルトアカウントが使用されます。

### Account メソッド

`Account` メソッドは `Using` と同等です：

```python
await adapter.Send.Account("account1").To("user", "123").Text("Hello")
```

## 非同期処理

### 結果を待機しない

```python
# メッセージはバックグラウンドで送信される
task = adapter.Send.To("user", "123").Text("Hello")

# 他の操作を続けて実行
# ...
```

### 結果を待機する

```python
# await で直接結果を取得
result = await adapter.Send.To("user", "123").Text("Hello")
print(f"送信結果: {result}")

# 先に Task を保存し、後で待機
task = adapter.Send.To("user", "123").Text("Hello")
# ... 他の操作 ...
result = await task
```

## 送信ルールシステム

SendDSL には送信ルールデコレータのセットが組み込まれており、チェーンメソッドでルールを付加し、最終的な送信時に一括適用します。ルールは一般的な本番環境のシナリオをカバーします：タイムアウト制御、失敗時のリトライ、成功時のコールバック、遅延送信、優先度に基づく破棄、進捗監視。

ルールメソッドは **self を返します**（At/AtAll/Reply と同様）ので、送信メソッド（Text/Image など）より前に呼び出す必要があります。ルールは `To`/`Using`/`Account` で作成される新しいインスタンスに伝播します。

### ルールメソッド一覧

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信成功後に実行されるコールバック（複数回呼び出し可能、順番に実行） |
| `.Retry(times=1)` | 失敗時に自動で N 回リトライ（初回を含め合計 N+1 回） |
| `.Timeout(seconds)` | 単回送信のタイムアウト。タイムアウト時は現在の試行をキャンセル（Retry と併用可能） |
| `.Defer(seconds=1.0)` | 遅延送信（プロセス内タイマー、永続化なし） |
| `.Priority(level, drop_if_busy=False)` | 優先度を設定。滞留時は破棄可能 |
| `.OnProgress(callback)` | 各段階の進捗コールバック（`SendContext` を受け取る） |
| `.OnError(callback)` | 最終失敗時のエラーコールバック（1 回のみ発火） |

### 送信成功後に実行するロジック（Hook）

```python
# 同期コールバック
await (adapter.Send.To("user", "123")
       .Hook(lambda r: print(f"送信成功、メッセージID: {r['message_id']}"))
       .Text("こんにちは"))

# 非同期コールバック
async def deduct_points(result):
    await db.update(user_id="123", points=-1)

await adapter.Send.To("user", "123").Hook(deduct_points).Text("ポイント消費")
```

Hook は送信が最終的に成功した場合（リトライでの成功を含む）にのみ実行されます。失敗・タイムアウト・キャンセルでは発火しません。

### 失敗時の自動リトライ（Retry）

```python
# 初回失敗後に 2 回リトライ、合計 3 回試行
result = await adapter.Send.To("user", "123").Retry(2).Text("リトライ付き")
```

リトライのトリガー条件：送信時の例外発生、送信のタイムアウト、`status == "failed"` のレスポンスが返された場合。

### タイムアウト時の自動キャンセル（Timeout）

```python
# 単回送信が 10 秒を超えたらキャンセル
await adapter.Send.To("user", "123").Timeout(10).Text("タイムアウト付き")

# タイムアウト + リトライ：1 回の試行につき 10 秒、最大 3 回
await adapter.Send.To("user", "123").Timeout(10).Retry(2).Text("タイムアウトリトライ")
```

### 進捗監視（OnProgress / OnError）

```python
def on_progress(ctx):
    print(f"段階: {ctx.stage}, 試行: {ctx.attempt + 1}/{ctx.max_attempts}, 経過時間: {ctx.elapsed:.2f}s")
    if ctx.stage == "failed":
        print(f"  エラー: {ctx.error!r}")

async def on_error(ctx):
    await notify_admin(f"{ctx.target_id} への送信失敗: {ctx.error!r}")

await (adapter.Send.To("user", "123")
       .Retry(3).Timeout(10)
       .OnProgress(on_progress)
       .OnError(on_error)
       .Text("監視"))
```

`SendContext` に含まれるフィールド：`task_id`、`platform`、`method`、`target_type`、`target_id`、`bot_id`、`stage`、`attempt`、`max_attempts`、`started_at`、`finished_at`、`elapsed`、`error`、`result`、`extra`。

`stage` の取り得る値：`pending`、`sending`、`retrying`、`success`、`failed`、`timeout`、`cancelled`、`dropped`。

### 遅延送信（Defer）

```python
# 5 秒後に送信
await adapter.Send.To("user", "123").Defer(5).Text("遅延メッセージ")
```

> 注意：遅延はプロセス内のタイマーによるものであり、プロセスの再起動で失われます。永続化は提供されません。

### 優先度と滞留時の破棄（Priority）

```python
# 低優先度メッセージ。キューが滞留した場合は自動的に破棄
result = await (adapter.Send.To("user", "123")
               .Priority(-1, drop_if_busy=True)
               .Text("放棄可能な通知"))
# 破棄された場合、result["status"] == "failed"
```

`drop_if_busy` を有効にすると、送信中タスク数がしきい値（デフォルト 64）を超えた時点で今回の送信を即座に諦めます。グローバルなしきい値は `.PriorityThreshold(n)` で調整できます。

### ルールの組み合わせとバックグラウンド実行

```python
# メインフローをブロックせず、ルールはそのまま有効
task = (adapter.Send.To("user", "123")
        .Hook(lambda r: print("送信成功！"))
        .Retry(3)
        .Timeout(10)
        .OnProgress(on_progress)
        .Text("こんにちは"))

# 他の操作を続けて実行
await handle_next_action()
```

### ルールの伝播

ルールは `To`/`Using`/`Account` で作成される新しいインスタンスに伝播し、チェーン呼び出し中のルール消失を防ぎます：

```python
# ルールは To の前に設定しても、To が作成するインスタンスに伝播する
builder = adapter.Send.Retry(3).Timeout(10)
send = builder.To("user", "123")  # send は引き続き Retry(3) と Timeout(10) を保持
await send.Text("hi")
```

複数インスタンス間でルールは相互に独立しています（hooks リストはディープコピー）。

## 一括構築モード（Build）

単発送モードに加え、SendDSL は一括構築モードもサポートしています：1 つのチェーン内に複数の送信メソッドを記述し、最後にまとめて実行します。「一度に複数のメッセージをまとめて送る」シナリオに適しています。

### 構築モードへの移行

送信メソッドの前に `.Build()` を呼び出すと `SendBuilder` を返します。以後、送信メソッド（Text/Image など）は即時実行されず、送信インテントとして蓄積されます：

```python
results = await (adapter.Send.To("user", "123")
                 .Build()                    # 構築モードへ移行
                 .Text("1文目")
                 .Image("pic.jpg")
                 .Text("2文目")
                 .send_all())                 # 一括実行
# results = [Textの結果, Imageの結果, Textの結果]
```

`.send_all()` は `asyncio.Task` を返し、await するとインテントの順序どおりの結果リストが得られます。

### 並列と逐次

デフォルトは**並列**実行です（同時送信、全体の所要時間は最も遅い 1 件にほぼ等しくなります）。メッセージの到着順序を保証する必要がある場合は `.Sequential()` を呼び出します：

```python
# 逐次：順番に 1 つずつ送信
await (adapter.Send.To("group", "456")
       .Build()
       .Sequential()
       .Text("先にこれを送る").Text("次にこれを送る")
       .send_all())

# 並列（デフォルト、明示的に呼び出すことも可）
await (adapter.Send.To("group", "456")
       .Build()
       .Parallel()
       .Text("並列1").Text("並列2")
       .send_all())
```

### 失敗継続とリトライ

一括実行では「失敗継続」戦略を採用しています：1 件が失敗しても他の送信は中断されません。`.Retry()` と組み合わせると、失敗した項目が自動的にリトライされます（リトライは単一項目に作用し、バッチ全体の再試行ではありません）：

```python
await (adapter.Send.To("user", "123")
       .Build()
       .Retry(2)                       # 各項目が個別に 2 回リトライ
       .Text("失敗する可能性あり").Image("こちらも失敗する可能性あり")
       .send_all())
```

### バッチ全体のルールとコールバック

ルールはバッチ全体に一括して作用します：

| メソッド | 説明 |
|--------|------|
| `.Timeout(seconds)` | 各送信の単回タイムアウト |
| `.Retry(times)` | 各送信が個別にリトライ（失敗継続） |
| `.Defer(seconds)` | バッチ全体の送信を遅延 |
| `.Hook(callback)` | バッチ全体の成功後に発火し、`results` リストを受け取る |
| `.OnError(callback)` | バッチに失敗が存在する場合に発火し、`BatchContext` を受け取る |
| `.OnProgress(callback)` | 各項目の完了時に発火し、`BatchContext` を受け取る |

```python
def on_progress(ctx):
    print(f"進捗: {ctx.completed}/{ctx.total}, 成功 {ctx.succeeded}, 失敗 {ctx.failed}")

async def on_error(ctx):
    print(f"バッチに {ctx.failed} 件の失敗があります")

results = await (adapter.Send.To("user", "123")
               .Build()
               .Retry(2).Timeout(10)
               .OnProgress(on_progress)
               .OnError(on_error)
               .Hook(lambda rs: print("バッチ全体が完了"))
               .Text("a").Text("b").Text("c")
               .send_all())
```

`BatchContext` に含まれるもの：`task_id`、`total`、`completed`、`succeeded`、`failed`、`stage`、`results`、`errors`、`elapsed`、`extra`。

`stage` の取り得る値：`pending`、`sending`、`success`（全件成功）、`partial`（一部成功）、`failed`（全件失敗）。

### 修飾子とルールの継承

`.Build()` より前に指定した At/AtAll/Reply 修飾子とルールはバッチ全体に継承され、各メッセージに作用します：

```python
await (adapter.Send.To("group", "456")
       .At("789")                        # 継承：各メッセージで @789
       .Build()
       .Retry(2)                         # 継承 + 追加：各項目が個別にリトライ
       .Text("@付きの通知")
       .Image("お知らせ画像")
       .send_all())
```

Build に入った後も修飾子を追加できます（バッチ全体に作用）：

```python
await (adapter.Send.To("group", "456")
       .Build()
       .At("111").At("222")             # @ を追加、バッチ全体に作用
       .Text("複数人への @")
       .send_all())
```

### バックグラウンド実行

単発送と同様に、`.send_all()` は Task を返すため、await せずにバックグラウンドで実行させることができます：

```python
task = (adapter.Send.To("user", "123")
        .Build()
        .Hook(lambda rs: print("一括送信が完了"))
        .Text("a").Text("b")
        .send_all())

# メインフローをブロックしない
await do_something_else()
```

## 命名規約

### PascalCase 命名

すべての送信メソッドはアッパーキャメルケース（PascalCase）を使用します：

```python
# ✅ 正しい
def Text(self, text: str):
    pass

def Image(self, file: bytes):
    pass

# ❌ 誤り
def text(self, text: str):
    pass

def send_image(self, file: bytes):
    pass
```

### プラットフォーム固有メソッド

プラットフォーム接頭辞付きメソッドの追加は推奨されません：

```python
# ✅ 推奨
def Sticker(self, sticker_id: str):
    pass

# ❌ 非推奨
def TelegramSticker(self, sticker_id: str):
    pass
```

代わりに `Raw` メソッドを使用してください：

```python
# ✅ 推奨
await adapter.Send.Raw_ob12([{"type": "sticker", ...}])

# ❌ 非推奨
def TelegramSticker(self, ...):
    pass
```

## 送信チェーンの内部分解

`await adapter.Send.To("group", "123").Text("x")` を一度実行する裏側では、フレームワークが以下の一連の処理を実行しています：

```mermaid
flowchart TD
    A["adapter.Send.To(...).Text(...)"] --> B["To/Using チェーンメソッド<br/>呼び出しごとに不変の新インスタンスを返す（順序非依存）"]
    B --> C["__getattribute__ が送信メソッドをインターセプト<br/>ルールラッパーで包む"]
    C --> D["元のメソッド（Text など）を呼び出し<br/>内部で Raw_ob12 に委譲"]
    D --> E["Raw_ob12 が asyncio.create_task(...) を返す"]
    E --> F["[Send] ログを書き込む"]
    F --> G["message.sending を emit（fire-and-forget）"]
    G --> H{"送信ルールが宣言されているか？"}
    H -->|"いいえ"| I["Task done_callback → message.sent を emit"]
    H -->|"はい"| J["apply_send_rules が外側の Task にラップ<br/>リトライ/タイムアウト/遅延/優先度"]
    J --> I
    I --> K["await で標準レスポンス dict を取得"]
```

**各ステップでフレームワークが行っていること：**

| 段階 | フレームワークの動作 |
|------|-------------|
| チェーン合成 | `To`/`Using`/`Account` は呼び出しごとに**不変インスタンスを新規作成**し、設定済みのフィールドを引き継ぎます。そのため `To(...).Using(...)` と `Using(...).To(...)` は**等価**であり、順序に依存しません |
| メソッドラップ | 送信メソッド（`Text` など）は `__getattribute__` によってインターセプトされ、ラッパーで包まれます。修飾メソッド（`To`/`Using`/`At`/`Retry` など）は**ラップされません**。ネストした `Raw_ob12` 呼び出しは `_in_rule_wrap` フラグにより重複ラップを防止します |
| Task 生成 | `Raw_ob12` 内部の `asyncio.create_task()` が Task が実際に生成される箇所です。`Text()` はこの Task を同期的に返すだけで、**ブロックしません** |
| 送信ログ | `[Send] platform/method -> target` のイベントログを書き込みます（`exclude_levels=["EVENT"]` で抑制可能） |
| `message.sending` | 送信メソッドが呼び出された時点で**即座に** fire-and-forget で発火します（リスナーが存在する場合のみ。まず `has_handlers` で短絡評価） |
| `message.sent` | Task の `done_callback` にバインドされます——**ルールがある場合はリトライフロー全体の最終結果をカバー**し、ルールがない場合は元の Task の完了そのものです |

### アカウント解決フォールバックチェーン

`Using()` による明示的な指定（`reply()` による自動注入を含む）や、イベントチェーンで自動バインドされたアカウント識別子は、以下の順序で具体的なアカウントに解決されます：

1. 単一アカウントアダプター（`AccountConfigClass` なし）→ そのまま返す
2. アカウント名と `account_id` の完全一致
3. 各アカウントの `bot_id` フィールドとの一致
4. 各アカウントの任意の `str` フィールド値との一致（`enabled`/`name` を除外）
5. フォールバックとして最初の有効なアカウントを採用：`account_id` が未指定の場合はそのまま採用（デフォルトアカウントのセマンティクス）。明示的に渡された `account_id` が解決できない場合は WARNING を記録した上で採用（WARNING 内の `platform` / `account_id` / `account` は、アカウントに帰属しないイベントの送信元を特定するために使用）
6. 有効なアカウントが一つもない場合（全アカウントが無効化されている場合を含む）→ `ValueError` をスロー：送信可能なアカウントが存在しません

> 渡される `account_id` の優先順位：`Using()` による明示的指定（`event.reply()` による自動注入の `self.user_id` / `self.account_id` 代位を含む）> **イベントディスパッチチェーンによるフォールバック**（イベント処理時に明示的に指定されなかった送信は、イベントをトリガーしたアカウントに自動バインド）> 未指定（デフォルトアカウントのセマンティクス。タイマー／起動タスクなどイベントコンテキストのないシナリオ）。

### シームレスなシンタックスシュガー

> 「イベントチェーン内での `Using()` 不要」「代位アカウント名ルーティング」には ErisPulse **2.12+** が必要です。

| シンタックスシュガー | トリガー条件 | 効果 |
|--------|----------|------|
| イベントチェーン内での `Using()` 不要 | イベント処理チェーン内での `Send` / `Api` / `Request` 呼び出し | イベントをトリガーしたアカウントに自動バインド（ディスパッチ入口が呼び出しコンテキストを注入。`send_context` / `api_context` / `request_context` も同一基準） |
| `reply()` 自動引用 | `quote=True` | イベントの `message_id` を自動取得して `Reply` セグメントを構築 |
| `reply()` 自動アカウントバインド | reply チェーン | 自動で `Using(self.account_id or self.user_id)`——代位アカウント名でそのままルーティング可能 |
| 代位アカウント名ルーティング | 動的アカウントで user_id を未取得 | イベントの `self.account_id` = アカウント名 → アカウント名マッチングにより正しいアカウントに解決 |
| デフォルトアカウントフォールバック | イベントコンテキストなし（タイマー／起動タスク） | 最初の有効なアカウント（既存のセマンティクスは不変） |

### 送信ルールエンジン（リトライ／タイムアウト／遅延）

ルールは `Raw_ob12` が Task を返した**後**に新しい外側の Task としてラップされるため、メインフローには影響しません。重要なポイント：

| ルール | 説明 |
|------|------|
| `Retry(n)` | 合計 `n+1` 回試行。**失敗後はただちに再送、指数バックオフなし** |
| `Timeout(s)` | 単一送信のタイムアウトでキャンセル（`asyncio.wait_for`）。試行回数が残っていればリトライ |
| `Defer(s)` | 送信前に遅延 sleep |
| `Priority(level, drop_if_busy)` | 滞留がしきい値を超えた場合、`{status:"failed", retcode:10002, message:"dropped_low_priority"}` を直接返す |
| `Hook(fn)` | 最終成功時のみ順に実行 |
| `on_progress` / `on_error` | 各段階／最終失敗時のコールバック |

> **注意**：リトライは「即時再送」であり、バックオフ間隔はありません。プラットフォームのレート制限によりバックオフが必要な場合は、`on_error` コールバック内で自ら sleep した後、手動で再送してください。ルールの成功判定は、返される dict の `status == "ok"` を基準とします（`retcode == 0`）。

> 標準レスポンス形式と `retcode` の完全なセマンティクスについては、[API レスポンス仕様](../../standards/api-response.md) を参照してください。

## 戻り値

### Task オブジェクト

すべての送信メソッドは `asyncio.Task` を返します。アダプターは `Raw_ob12` を実装するだけでよく、標準メソッド（Text/Image など）はデフォルトでそれに委譲されます：

```python
import asyncio

def Raw_ob12(self, message, **kwargs):
    async def _do_send():
        segments = self._apply_modifiers(message)
        return await self._adapter.call_api(
            endpoint="/send_message",
            message=segments,
            **self.send_context,
            **kwargs,
        )
    return asyncio.create_task(_do_send())

# Text/Image/Voice/Video/File/Location は基底クラスから継承済みで、自動的に Raw_ob12 に委譲される
# 標準メソッドをオーバーライドする場合は、asyncio.Task を返せばよい：
# def Text(self, text: str):
#     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

### 標準化レスポンス

`call_api` は標準化されたレスポンスを返すべきです。`make_response()` / `make_error()` メソッドの使用を推奨します：

```python
async def call_api(self, endpoint: str, **params):
    try:
        # _do_api_call はアダプターが自前で実装するプラットフォームリクエスト（例示プレースホルダ）
        result = await self._do_api_call(endpoint, **params)
        return self.make_response(
            data=result.get("data"),
            message_id=result.get("message_id", ""),
            raw=result,
        )
    except Exception as e:
        return self.make_error(message=str(e))
```

手動構築もサポートされています（旧バージョンの方式も引き続き互換）：

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

## 完全な使用例

### 基本的な使用

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

### チェーン呼び出し

```python
# ユーザーへの @ + 返信
await my_adapter.Send.To("group", "456").At("789").Reply("msg123").Text("@したメッセージへの返信")

# 全体への @ + 複数の修飾
await my_adapter.Send.Using("bot1").To("group", "456").AtAll().Text("お知らせメッセージ")
```

### 生メッセージとメッセージ構築

`Raw_ob12` は逆変換の中核エントリーポイント（OB12 メッセージセグメントの受信 → プラットフォーム API 呼び出し）であり、`MessageBuilder` はそれと併用するチェーン式メッセージセグメント構築ツールです。

> `Raw_ob12` の完全な実装仕様、`MessageBuilder` の使い方およびコード例については、以下を参照してください：
> - [送信メソッド仕様 §6 逆変換仕様](../../standards/send-method-spec.md#6-反向转换规范onebot12--平台)
> - [送信メソッド仕様 §11 メッセージビルダー](../../standards/send-method-spec.md#11-消息构建器-messagebuilder)



### 适配器开发最佳实践

# アダプタ開発のベストプラクティス

> [!TIP]
> **この記事を読むタイミング**：アダプタの基本構造が動くようになったら読むことを推奨します（工程化のベストプラクティス）。必要なければ飛ばしても、他の機能の使用に影響はありません。

ここでは、アダプタ開発における工程上の約束事項をまとめます。Botの状態報告、接続の再試行とハートビート、複数アカウントの解析、標準化されたエラー応答など、この通りに実装することで、接続切断の無感知、複数アカウントでの送信先ミス、エラーの原因特定困難といったプラットフォーム接続時の一般的な問題を回避できます。

## Botの状態管理とMetaイベント

アダプタは、`adapter.emit()` を使ってMetaイベントを送信し、フレームワークがBotの接続状態、オンライン・オフライン、ハートビート情報を自動的に追跡できるようにする必要があります。

### 1. Metaイベントを送信するタイミング

| イベント | `detail_type` | 発生タイミング | フレームワークの動作 |
|------|--------------|---------|---------|
| 接続 | `"connect"` | Botがプラットフォームと接続したとき | Botを登録し、`adapter.bot.online`のライフサイクルイベントをトリガー |
| 切断 | `"disconnect"` | Botがプラットフォームと切断したとき | Botをオフラインにマークし、`adapter.bot.offline`のライフサイクルイベントをトリガー |
| ハートビート | `"heartbeat"` | 定期的に送信（推奨は30〜60秒） | Botのアクティブタイムとメタ情報を更新 |

### 2. Metaイベントの送信

フレームワークは`emit_meta()`メソッドを提供しており、1行でMetaイベントを送信できます。

```python
class MyAdapter(BaseAdapter):
    async def _ws_handler(self, websocket):
        bot_id = self._get_bot_id()

        # Botがオンラインになったとき：1行でconnectイベントを送信
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="私のロボット")

        try:
            while True:
                data = await websocket.receive_text()
                event = self.convert(data)
                if event:
                    await self.adapter.emit(event)
        except WebSocketDisconnect:
            pass
        finally:
            # Botがオフラインになったとき
            await self.emit_meta("disconnect", bot_id)
```

`emit_meta()` 以外にも、手動で標準的なMetaイベントを構築することもできます（旧バージョンの方法も互換性があります）：

```python
await self.adapter.emit({
    "id": str(uuid4()),
    "time": int(time.time()),
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": bot_id,
        "user_name": "MyBot",
        "avatar": "https://example.com/avatar.jpg",
    },
    "myplatform_raw": raw_data,
    "myplatform_raw_type": "connected",
})
```

### 3. ハートビートイベント

アダプタは、接続が維持されている間、定期的にハートビートイベントを送信し、Botのアクティブタイムを更新する必要があります。

```python
class MyAdapter(BaseAdapter):
    async def _heartbeat_loop(self, bot_id: str):
        while self._connected:
            # フレームワークにmeta heartbeatを送信（1行で完了）
            await self.emit_meta("heartbeat", bot_id)
            await asyncio.sleep(30)
```

### 4. `self`フィールドの自動発見

フレームワークの`adapter.emit()`は、`self`フィールドを含むすべてのイベント（Metaイベントに限らず）を自動的に処理します：

- **通常のイベント**（message/notice/request）の`self`フィールドは自動的にBotとして登録されます
- **`self`フィールドの拡張情報**：`user_name`、`nickname`、`avatar`、`account_id`などのオプションフィールドがサポートされています

```python
# 転換器にselfフィールドを含めることで、Botが自動的に登録されます
onebot_event = {
    "type": "message",
    "detail_type": "private",
    "platform": "myplatform",
    "self": {
        "platform": "myplatform",
        "user_id": "bot123",
        "user_name": "MyBot",
        "nickname": "私のロボット",
    },
    # ... 他のフィールド
}
await self.adapter.emit(onebot_event)
# Bot "bot123" は自動的に登録され、アクティブタイムが更新されます
```

### 5. Botの状態の照会

照会API（`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`）とBotのライフサイクルイベントの表は、[アダプタシステムAPI - Botの状態管理](../../api-reference/adapter-system.md#bot-状態管理)をご覧ください。

## 接続管理

### 1. 接続の再試行の実装

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                self.logger.info("接続に成功しました")
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    # 指数バックオフ戦略
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(
                        f"接続に失敗しました。{wait_time}秒後に再試行します ({retry_count}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("接続に失敗しました。最大再試行回数に達しました")
                    raise
```

### 2. 接続状態の管理

```python
class MyAdapter(BaseAdapter):
    async def start(self):
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

### 3. ハートビート保活とMetaハートビート

アダプタのハートビートは、2つのタスクを同時に行う必要があります：プラットフォームへのハートビート保活送信と、フレームワークへのmeta heartbeatイベント送信。

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        self.connection = await self._connect_to_platform()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        while self.connection:
            try:
                # 1. プラットフォームにハートビート保活を送信
                await self.connection.send_json({"type": "ping"})

                # 2. フレームワークにmeta heartbeatを送信（emit_metaで1行で完了）
                await self.emit_meta("heartbeat", self._bot_id)

                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"ハートビートに失敗しました: {e}")
                break
```

### 4. 接続情報の公開

アダプタが登録したルートは、ユーザーがプラットフォーム側のコールバックアドレスを設定できるように、表示されるべきです。`start()`で接続情報を明示的に出力することを推奨します：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        router.register_websocket(
            module_name=self.platform,
            path="/ws",
            handler=self._ws_handler
        )

        if self.sdk:
            info = self.sdk.adapter.get_connection_info(self.platform)
            if info:
                self.logger.info(f"WebSocketアドレス: "
                    f"{info.get('connection', {}).get('base_url', '')}"
                    f"{info.get('connection', {}).get('websocket_routes', [])}")
```

ユーザーは以下のAPIを使って、アダプタのすべてのルートと接続アドレスを照会できます：

```python
from ErisPulse import sdk

# アダプタレベルの接続情報（推奨）
info = sdk.adapter.get_connection_info("myplatform")

# ルートマネージャーのレベルでの照会
sdk.router.list_namespaces()              # すべての名前空間をリストアップ
sdk.router.get_module_routes("myplatform")  # 詳細なルート情報
sdk.router.get_module_urls("myplatform")    # 完全な接続URL
```

> **注意**：ルート登録時の`module_name`は、ErisPulseに登録されたアダプタの`platform`名と完全に一致する必要があります。一致しないと`get_connection_info()`はルートを関連付けられません。複数アカウントのアダプタは、異なる`module_name`ではなく、各アカウントにサブパス（例：`/account1/webhook`、`/account2/webhook`）を登録する必要があります。

### 5. HTTPルートのライフサイクル

アダプタ/モジュールが`router`を使って登録したHTTP/WebSocketルートは、フレームワークによって**帰属原則**に従ってライフサイクル管理されます：

- 登録時の`module_name`（名前空間）が帰属識別子です。**reload / stop / unloadの際にフレームワークは、該当する帰属内のすべてのルートと接続リソースを自動的にクリーンアップ**します。手動でアン登録する必要はありません。
- したがって、**`start()`（モジュールでは`on_load`）では、必ずルートを再登録する必要があります**。インスタンスレベルのブール値フラグを使って「一度だけ登録」の最適化をしないでください。設定のホットリロード（アカウントフィールドの変更が即座に保存される）は、`stop/start`をトリガーし、**同一インスタンスが再利用される**ため、フラグが残るとルートがクリーンアップ後に**永久に失われ**、エンドポイントが404となり、プロセスの再起動でしか復旧しません

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # 毎回起動時に無条件に再登録（reload後のルートは、前のstopで自動的にクリーンアップされている）
        router.register_http_route(self.platform, "/qr/start", self._qr_start, methods=["POST"])
        router.register_http_route(self.platform, "/qr/poll", self._qr_poll, methods=["POST"])
```

モジュール側も同様です（`on_load`で登録）：

```python
class MyModule(BaseModule):
    async def on_load(self):
        router.register_http_route("MyModule", "/api/panel", self._panel, methods=["GET"])
```

ルートを**事前に手動でアン登録**（例：動的にエントリをオフラインにする）する必要がある場合は、明示的に登録解除できます：

```python
from ErisPulse.Core import router

router.unregister_http_route(self.platform, "/qr/start")
```

- ホットリロードのウィンドウ中、クライアントは一時的にルートが404になる可能性があります。これは一時的な現象です。ブラウザ向けのインタラクティブページは、404に対して有限回の自動リトライを実装することを推奨します

## イベントの変換

### 1. OneBot12標準に厳密に従う

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
            "myplatform_raw": raw_event,  # 保持したまま（必須）
            "myplatform_raw_type": raw_event.get("type", "")  # 元のタイプ（必須）
        }
        return onebot_event
```

### 2. 時間スタンプの標準化

```python
def _convert_timestamp(self, timestamp):
    """10桁の秒単位の時間スタンプに変換"""
    if not timestamp:
        return int(time.time())
    
    # ミリ秒単位の時間スタンプの場合
    if timestamp > 10**12:
        return int(timestamp / 1000)
    
    # 秒単位の時間スタンプの場合
    return int(timestamp)
```

### 3. イベントIDの生成

```python
import uuid

def _generate_event_id(self, raw_event):
    """イベントIDを生成"""
    event_id = raw_event.get("event_id")
    if event_id:
        return str(event_id)
    # プラットフォームがIDを提供していない場合、UUIDを生成
    return str(uuid.uuid4())
```

## SendDSLの実装

`At`/`AtAll`/`Reply`修飾子は、フレームワークのSendDSL基底クラスに既に実装済みです。アダプタは`Raw_ob12`と具体的な送信メソッドを実装するだけで済みます。`self._apply_modifiers(message)`と`self.send_context`を使用して開発を簡素化します。

### 1. Taskオブジェクトを必ず返す

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """推奨実装：フレームワークの補助メソッドを使用"""
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

### 2. 鏈式修飾メソッドはselfを返す

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self # selfを返す
```

### 3. プラットフォーム固有のメソッドをサポート

```python
class Send(BaseAdapter.Send):
    def Sticker(self, sticker_id: str):
        """スタンプ送信"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_sticker",
                message=[{"type": "sticker", "data": {"id": sticker_id}}],
                **self.send_context
            )
        )
    
    def Card(self, card_data: dict):
        """カードメッセージ送信"""
        return asyncio.create_task(
            self._adapter.call_api(
                endpoint="/send_card",
                message=[{"type": "card", "data": {"id": card_data}}],
                **self.send_context
            )
        )
```

## API応答

### 1. 標準化された応答形式

フレームワークは`make_response()`と`make_error()`メソッドを提供し、標準化された応答を構築できます：

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        if raw_response.get("success"):
            return self.make_response(
                data=raw_response.get("data"),
                message_id=raw_response.get("data", {}).get("message_id", ""),
                raw=raw_response,
            )
        else:
            return self.make_error(
                retcode=raw_response.get("code", 10001),
                message=raw_response.get("message", ""),
                raw=raw_response,
            )
    except Exception as e:
        return self.make_error(message=str(e))
```

`make_response()`は、`{platform}_raw`キーを含む応答辞書を自動的に生成します。`make_error()`はデフォルトで`retcode=34000`（Platform Error）を使用します。

### 2. エラーコードの規範

OneBot12標準のエラーコードに従います：

```python
# 1xxxx - 動作リクエストエラー
10001: Bad Request
10002: Unsupported Action
10003: Bad Param

# 2xxxx - 動作ハンドラエラー
20001: Bad Handler
20002: Internal Handler Error

# 3xxxx - 動作実行エラー
31000: Database Error
32000: Filesystem Error
33000: Network Error
34000: Platform Error
35000: Logic Error
```

## 複数アカウントのサポート

### 1. 宣言的構成（推奨）

`AccountConfigClass`を使って構成クラスを宣言した後、フレームワークが複数アカウントのロード、検証、テンプレート生成を自動的に管理します。`BotAccountConfig`基底クラスは`enabled`と`name`フィールドを提供しており、アダプタは宣言する必要はありません：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Bot Token"},
        "required": True,
        "secret": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"アカウント {name} を起動します")
            await self._connect(name, account.token)
            # bot_idはフレームワークがプラットフォームプロトコル/ログイン応答から自動的に取得し、戻し埋めされます
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # name: アカウント名, account: MyBotConfigインスタンス
```

構成ファイルは自動的に生成されます：

```toml
[MyAdapter.accounts.default]
token = ""
enabled = true
name = ""
```

### 2. アカウント選択メカニズム

送信時に指定されたアカウント識別子（`Using()` / イベントチェーンバインド）は、フレームワークが自動的に解析し、以下の優先順位で一致します：

1. **アカウント名** — 構成のキー名と正確に一致
2. **`bot_id`フィールド** — アカウント構成の`bot_id`（実行時に自動的に戻し埋めされます、通常は`event["self"]["user_id"]`）
3. **任意のstrフィールド** — 構成の他の文字列フィールド
4. **デフォルト** — 最初に有効化されたアカウント

アダプタは`call_api`を実装する際、フレームワークが提供するアカウント解析を使って「識別子 → アカウント構成」のマッピングを完了します：

```python
# アカウント名で一致
name, account = self._resolve_account("account1")

# bot_idで一致（最も一般的な方法、イベントから取得）
name, account = self._resolve_account("bot_123")

# 有効化された最初のアカウントを取得（Noneを渡す）
name, account = self._resolve_account(None)
```

## エラーハンドリング

### 1. エラーの分類と処理

`make_error()`を使って標準化されたエラー応答を構築します。`sdk.client`を使ってリクエストする際は、ErisPulseの例外をキャッチします：

```python
from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError

async def call_api(self, endpoint: str, **params):
    try:
        from ErisPulse.Core import client
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self.make_response(data=response, raw=response)
    except ClientTimeoutError:
        self.logger.error(f"リクエストがタイムアウトしました: {endpoint}")
        return self.make_error(retcode=32000, message="リクエストがタイムアウトしました")
    except ClientError as e:
        self.logger.error(f"ネットワークエラー: {e}")
        return self.make_error(retcode=33000, message="ネットワークリクエストに失敗しました")
    except json.JSONDecodeError:
        self.logger.error("JSONの解析に失敗しました")
        return self.make_error(retcode=10006, message="レスポンス形式が無効です")
    except Exception as e:
        self.logger.error(f"未知のエラー: {e}", exc_info=True)
        return self.make_error(message=str(e))
```

> **後方互換性**：`aiohttp`を使用する旧アダプタのコードは影響を受けません。`sdk.client`を使ってリクエストする場合のみ、例外の変換が有効になります。

### 2. ログ記録

フレームワークは、アダプタごとにサブロガーを自動的に作成します（`sdk.logger.get_child("MyAdapter")`）。手動で初期化する必要はありません：

```python
class MyAdapter(BaseAdapter):
    # ConfigClass = ...  # 構成クラスを宣言するとself.loggerが自動的に利用可能になります
    
    async def start(self):
        self.logger.info("アダプタの起動中...")
        # ...
        self.logger.info("アダプタの起動完了")
    
    async def shutdown(self):
        self.logger.info("アダプタの終了中...")
        # ...
        self.logger.info("アダプタの終了完了")
```

## テスト

### 1. 単体テスト

```python
import pytest
from ErisPulse.Core.Bases import BaseAdapter

class TestMyAdapter:
    def test_converter(self):
        """テスト転換器"""
        converter = MyPlatformConverter()
        raw_event = {"type": "message", "content": "Hello"}
        result = converter.convert(raw_event)
        assert result is not None
        assert result["platform"] == "myplatform"
        assert "myplatform_raw" in result
    
    def test_api_response(self):
        """テストAPI応答形式"""
        adapter = MyAdapter()
        response = adapter.call_api("/test", param="value")
        assert "status" in response
        assert "retcode" in response
```

### 2. 集成テスト

```python
@pytest.mark.asyncio
async def test_adapter_start():
    """テストアダプタ起動"""
    adapter = MyAdapter()
    await adapter.start()
    assert adapter._connected is True

@pytest.mark.asyncio
async def test_send_message():
    """テストメッセージ送信"""
    adapter = MyAdapter()
    await adapter.start()
    
    result = await adapter.Send.To("user", "123").Text("Hello")
    assert result is not None
```

## リバースコンバージョンとメッセージ構築

`Raw_ob12`はアダプタが**必ず実装**すべきメソッドであり、OneBot12からプラットフォームへのリバースコンバージョンの統一エントリーポイントです。標準メソッド（`Text`、`Image`など）は`Raw_ob12`に委譲し、修飾子の状態（`At`/`Reply`/`AtAll`）は`Raw_ob12`内でメッセージセグメントにマージする必要があります。

`MessageBuilder`は`Raw_ob12`と併用するメッセージセグメント構築ツールで、チェーン呼び出しと迅速な構築が可能です。

> 完全な実装規範、コード例、使用方法は、以下のドキュメントをご覧ください：
> - [送信メソッド規範 §6 リバースコンバージョン規範](../../standards/send-method-spec.md#6-リバースコンバージョン規範onebot12--プラットフォーム)
> - [送信メソッド規範 §11 メッセージビルダー](../../standards/send-method-spec.md#11-メッセージビルダー-messagebuilder)

## プラットフォームイベントメソッドの拡張

アダプタは、Eventラッパークラスにプラットフォーム固有のメソッドを登録することで、モジュール開発者がプラットフォーム固有のデータに簡単にアクセスできるようにすることができます。

### 1. Mixinクラスを使って一括登録（推奨）

プラットフォームに複数の固有メソッドがある場合、Mixinクラスを使って一括登録することを推奨します：

```python
# アダプタのstart()またはモジュールレベルで登録
from ErisPulse.Core.Event import register_event_mixin

class MyPlatformEventMixin:
    def get_chat_name(self):
        """チャット名を取得"""
        return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

    def is_official_message(self):
        """公式メッセージか判定"""
        raw = self.get("myplatform_raw", {})
        return raw.get("sender", {}).get("is_official", False)

    def get_message_type(self):
        """プラットフォームのメッセージタイプを取得"""
        return self.get("myplatform_raw", {}).get("msg_type", "text")

# 一括登録
register_event_mixin("myplatform", MyPlatformEventMixin)
```

### 2. デコレータを使って個別メソッドを登録

```python
from ErisPulse.Core.Event import register_event_method

@register_event_method("myplatform")
def get_chat_name(self):
    return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")
```

### 3. アダプタの終了時にクリーンアップ

```python
from ErisPulse.Core.Event import unregister_platform_event_methods

class MyAdapter(BaseAdapter):
    async def shutdown(self):
        # プラットフォームイベントメソッドの登録をクリーンアップ
        unregister_platform_event_methods("myplatform")
        # ... その他のクリーンアップ
```

> 詳細な登録とアン登録の説明は、[イベントシステムAPI - プラットフォーム拡張メソッドの登録](../../api-reference/event-system.md#アダプタ登録プラットフォーム拡張メソッド)をご覧ください。

## ドキュメントの維持

### 1. プラットフォーム特性のドキュメントを維持

`docs/ja/platform-guide/`に`{platform}.md`ドキュメントを作成します（他の言語バージョンは自動生成されます）：

```markdown
# プラットフォーム名アダプタドキュメント

## 基本情報
- 対応モジュールバージョン: 1.0.0
- 維持者: あなたの名前

## 支援されるメッセージ送信タイプ
...

## 特有のイベントタイプ
...

## 設定オプション
...
```

### 2. バージョン情報を更新

新しいバージョンをリリースする際、ドキュメントのバージョン情報を更新します：

```toml
[project]
version = "2.0.0"  # バージョン番号を更新
```



### 事件转换器

# イベントコンバーター実装ガイド

> [!TIP]
> **この文書を読むべきタイミング**：アダプター開発パス内では必読（イベントコンバーター）。必要なければスキップしても、他の機能の利用には影響しません。


アダプターがプラットフォームのネイティブイベントを受信すると、イベントコンバーター (Converter) がそれを ErisPulse の統一された OneBot12 標準形式へ変換します。プラットフォームイベントがどのようにフレームワークへ取り込まれるかは、この1つのクラスが決定します。

## Converter の責務

```
プラットフォームネイティブイベント ──→ Converter.convert() ──→ OneBot12 標準イベント
```

Converter は**順方向変換**（受信方向）のみを担当します。つまり、プラットフォームのネイティブイベントデータを OneBot12 標準形式に変換します。逆方向変換（送信方向）は `Send.Raw_ob12()` メソッドが処理します。

### 基本原則

1. **無損失変換**：元のデータは必ず `{platform}_raw` フィールドに完全な形で保持すること
2. **標準互換**：変換後のイベントは OneBot12 標準形式に準拠すること
3. **プラットフォーム拡張**：プラットフォーム固有のデータは `{platform}_` プレフィックス付きフィールドに保存すること

## BaseConverter 基底クラス（推奨）

2.7.0 以降、フレームワークは `BaseConverter` 基底クラス（`ErisPulse.Core.Bases`）を提供しており、OneBot12 イベントの**共通フィールド構築**と**よく使うメッセージセグメントのヘルパー**をカプセル化しているため、コンバーターは型マッピングに集中するだけでよくなります：

```python
from ErisPulse.Core.Bases import BaseConverter


class MyConverter(BaseConverter):
    def __init__(self):
        super().__init__(platform="myplatform")

    def convert(self, raw_event: dict) -> dict | None:
        if not isinstance(raw_event, dict):
            return None
        event_type = raw_event.get("type", "")
        base = self.build_base_event(raw_event, event_type)  # id/time/platform/self/raw
        if event_type == "message":
            base["type"] = "message"
            base["detail_type"] = "group" if raw_event.get("group_id") else "private"
            base["user_id"] = str(raw_event.get("sender_id", ""))
            base["message"] = [self.text(raw_event.get("content", ""))]
            base["alt_message"] = raw_event.get("content", "")
            return base
        return None
```

`build_base_event()` が自動的に埋める共通フィールド：

| フィールド | 供給元 |
|------|------|
| `id` | `raw_event["event_id"]`、未指定時は UUID を自動生成 |
| `time` | `raw_event["timestamp"]`、未指定時は現在時刻 |
| `platform` | コンストラクタで渡された `platform` |
| `self` | `{"platform": ..., "user_id": raw_event["bot_id"]}` |
| `{platform}_raw` | 元のイベント（「無損失変換」の原則を満たす） |
| `{platform}_raw_type` | 元のイベントタイプ |

よく使うメッセージセグメントのヘルパーメソッド（いずれも静的メソッドで、そのまま再利用できます）：

```python
converter.text("hi")          # {"type": "text", "data": {"text": "hi"}}
converter.at("123456")        # {"type": "at", "data": {"user_id": "123456"}}
converter.image("file.png")   # {"type": "image", "data": {"file": "file.png"}}
```

> 手動で実装する場合、`build_base_event` の共通フィールド構築は毎回書く必要があるボイラープレートコードです。`BaseConverter` を使えばこの部分を省略でき、「無損失変換」（元のイベントは常に `{platform}_raw` に入る）も自然に満たされます。

## convert() メソッド

### メソッドシグネチャ

```python
def convert(self, raw_event: dict) -> dict:
    """
    プラットフォームのネイティブイベントを OneBot12 標準形式に変換する

    :param raw_event: プラットフォームのネイティブイベントデータ
    :return: OneBot12 標準形式のイベント辞書
    """
    pass
```

### 戻り値の構造

変換後のイベント辞書には、以下の標準フィールドを含める必要があります：

```python
{
    "id": "イベントの一意なID",
    "time": 1234567890,           # Unix タイムスタンプ（秒）
    "type": "message",             # イベントタイプ
    "detail_type": "private",      # 詳細タイプ
    "platform": "myplatform",      # プラットフォーム名
    "self": {
        "platform": "myplatform",
        "user_id": "bot_user_id"
    },

    # メッセージイベントのフィールド
    "user_id": "sender_id",
    "message": [...],              # OneBot12 メッセージセグメントのリスト
    "alt_message": "プレーンテキストの内容",

    # 元のデータを必ず保持する
    "myplatform_raw": { ... },     # プラットフォームネイティブイベントの完全なデータ
    "myplatform_raw_type": "ネイティブイベントの型名",
}
```

## 必須フィールドのマッピング

### 共通フィールド（すべてのイベントタイプ）

| OB12 フィールド | 型 | 説明 |
|-----------|------|------|
| `id` | str | イベントの一意な識別子 |
| `time` | int | Unix タイムスタンプ（秒） |
| `type` | str | イベントタイプ：`message` / `notice` / `request` / `meta` |
| `detail_type` | str | 詳細タイプ：`private` / `group` / `friend` など |
| `platform` | str | プラットフォーム名。アダプターの登録名と一致させること |
| `self` | dict | ボット情報：`{"platform": "...", "user_id": "..."}` |

### メッセージイベントの追加フィールド

| OB12 フィールド | 型 | 説明 |
|-----------|------|------|
| `user_id` | str | 送信者 ID |
| `message` | list[dict] | OneBot12 メッセージセグメントのリスト |
| `alt_message` | str | プレーンテキストの代替内容 |

### 通知イベントの追加フィールド

| OB12 フィールド | 型 | 説明 |
|-----------|------|------|
| `user_id` | str | 関連するユーザー ID |
| `operator_id` | str | 操作者の ID（グループメンバーの増減など） |

## メッセージセグメントの変換

OneBot12 標準では、以下のメッセージセグメントタイプが定義されています：

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

# @メンション
{"type": "mention", "data": {"user_id": "123"}}

# @全員
{"type": "mention_all", "data": {}}

# 返信
{"type": "reply", "data": {"message_id": "msg_123"}}
```

プラットフォームに対応していないメッセージセグメントタイプがある場合は、そのセグメントを省略するか、最も近い標準タイプに変換できます。

## alt_message のレンダリング規約

`alt_message` はメッセージイベントのプレーンテキストの代替内容で、ログのアーカイブ、`extract_text` によるテキストマッチング、コマンドディスパッチのフォールバックに使用されます。各アダプターは `alt_message` を生成する際、以下の規約に従う必要があります（特に mention セグメントに注意）：

- **mention セグメント**は優先的に `@ニックネーム` とレンダリングします。プラットフォームがニックネームを提供しない場合は `@{user_id}` にフォールバックし、`user_id` が `all`（@全員）の場合は `@メンバー全員` とレンダリングします
- ニックネームと `user_id` の**両方が欠けている場合はそのセグメントを省略**し、空の `"@"` を出力してはいけません。`"@ ヘルプ"` のようになると、テキストマッチングやコマンド解析の基準が汚染されます
- `data.get("user_name", fallback)` の罠に注意：メッセージセグメントの構築時に `user_name` のデフォルトとして空文字列が保存されていると、キーが存在するためにフォールバックが永久に機能しません。`data.get("user_name") or data.get("user_id")` という書き方を使うべきです
- その他のメッセージセグメントのレンダリングスタイル（`[画像]`、`[音声]` など）や、セグメント間の連結方法（`""` または `" "`）は、アダプター自身の既存の方針を維持し、強制的な統一は行いません

```python
# mention セグメントのレンダリング例
data = seg.get("data") or {}
user_id = str(data.get("user_id") or "").strip()
user_name = str(data.get("user_name") or "").strip()
if user_id == "all":
    parts.append("@メンバー全員")
elif user_name:
    parts.append(f"@{user_name}")
elif user_id:
    parts.append(f"@{user_id}")
```

## プラットフォーム拡張フィールド

プラットフォーム固有のデータは、標準フィールドとの衝突を避けるため `{platform}_` プレフィックスを付けて保存する必要があります：

```python
{
    # 標準フィールド
    "type": "message",
    "detail_type": "group",
    # ...

    # プラットフォーム拡張フィールド
    "myplatform_raw": { ... },          # 元のイベントデータ（必須）
    "myplatform_raw_type": "chat",      # 元のイベントタイプ（必須）

    # その他のプラットフォーム固有フィールド
    "myplatform_group_name": "グループ名",
    "myplatform_sender_role": "admin",
}
```

> **重要**：`{platform}_raw` フィールドは必須です。ErisPulse のイベントシステムやモジュールは、プラットフォームの元のデータにアクセスするためにこのフィールドに依存している可能性があります。

## 完全な実装例

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

## リッチメディアメッセージの変換例

実際のプラットフォームのメッセージには、通常、画像、@メンション、返信などのリッチメディアコンテンツが含まれます。以下は、`_convert_message_segments` で複数のメッセージタイプを処理する例です：

```python
def _convert_message_segments(self, raw_content: list) -> list:
    """プラットフォームのネイティブメッセージセグメントのリストを OneBot12 標準メッセージセグメントに変換する"""
    segments = []

    for item in raw_content:
        item_type = item.get("type", "")

        if item_type == "text":
            segments.append({
                "type": "text",
                "data": {"text": item.get("content", "")}
            })

        elif item_type == "image":
            file_url = item.get("url") or item.get("file_id", "")
            segments.append({
                "type": "image",
                "data": {"file": file_url}
            })

        elif item_type == "at":
            segments.append({
                "type": "mention",
                "data": {"user_id": item.get("target_id", "")}
            })

        elif item_type == "reply":
            segments.append({
                "type": "reply",
                "data": {"message_id": item.get("reply_to_id", "")}
            })

        elif item_type == "at_all":
            segments.append({"type": "mention_all", "data": {}})

        else:
            segments.append({
                "type": "text",
                "data": {"text": f"[未対応のメッセージタイプ: {item_type}]"}
            })

    return segments
```

## よくある落とし穴

### 1. `{platform}_raw` フィールドの欠落

これは最もよくある間違いです。元のデータのフィールドが欠落すると、モジュールがプラットフォーム固有の情報にアクセスできなくなります。

```python
base_event["myplatform_raw"] = raw_event        # 必須！
base_event["myplatform_raw_type"] = event_type   # 必須！
```

### 2. タイムスタンプ形式の誤り

OneBot12 標準では、`time` フィールドは Unix 秒単位のタイムスタンプ（整数）でなければなりません。プラットフォームがミリ秒のタイムスタンプや ISO 形式の文字列を返す場合は、変換が必要です：

```python
import time

# ミリ秒 → 秒
"time": raw_event.get("timestamp", 0) // 1000

# ISO 文字列 → 秒
"time": int(time.mktime(time.strptime(raw_event["created_at"], "%Y-%m-%dT%H:%M:%S")))
```

### 3. `self` フィールドの欠落

`self` フィールドにはボット自身の情報が含まれ、`user_id` はボットのアカウント ID です。マルチボットのシナリオでは、このフィールドが極めて重要です：

```python
"self": {
    "platform": self.platform,
    "user_id": raw_event.get("bot_id", ""),   # ボット自身の ID
}
```

### 4. detail_type に非標準の値を使用している

`detail_type` は、`private`、`group`、`friend_increase`、`group_member_increase` など、OneBot12 標準で定義された値を使用しなければなりません。プラットフォーム固有の命名は使用しないでください。

### 5. ラウンドトリップの一貫性

Converter が生成するメッセージセグメントタイプが、Send 側がサポートするメソッドと対応していることを確認してください。たとえば、Converter がプラットフォームの画像メッセージを `{"type": "image", ...}` に変換するなら、Send 側の `Image()` メソッドは画像の送信を処理できる必要があります。

## ベストプラクティス

1. **常に元のデータを保持する**：`{platform}_raw` フィールドは省略できません
2. **標準メッセージセグメントを使用する**：プラットフォームのメッセージはできる限り OneBot12 標準のメッセージセグメントに変換します
3. **detail_type を適切に設定する**：標準タイプ（`private`/`group`/`channel` など）を使用し、独自定義はしないでください
4. **エッジケースを処理する**：元のイベントには一部のフィールドが欠けている可能性があるため、`.get()` を使い適切なデフォルト値を提供します
5. **パフォーマンスへの配慮**：`convert()` はすべてのイベントで呼び出されるため、その中で時間のかかる処理を実行することは避けてください



### 发布与模块商店指南

# リリースとモジュールストアのガイド

> [!TIP]
> **この記事を読む必要があるのはいつか**：作品を PyPI / モジュールストアに公開する場合。必要ない場合は飛ばしても、他の機能の使用に支障はありません。

ErisPulse モジュールストアに開発したモジュールやアダプターを公開し、他のユーザーが簡単に発見してインストールできるようにしましょう。

## モジュールストアの概要

ErisPulse モジュールストアは、集中管理されたモジュール登録表です。ユーザーは CLI ツールを使って、コミュニティが提供したモジュールやアダプターを閲覧、検索、インストールできます。

### 閲覧と発見

```bash
# リモートに利用可能なすべてのパッケージを表示
epsdk list-remote

# モジュールのみを表示
epsdk list-remote -t modules

# アダプターのみを表示
epsdk list-remote -t adapters

# リモートパッケージリストを強制的に更新
epsdk list-remote -r
```

ErisPulse 公式サイト ([https://www.erisdev.com/#market](https://www.erisdev.com/#market)) や [ErisPulse Workbench](https://workbench.erisdev.com/) の「モジュールリスト」からオンラインでモジュールストアを閲覧することもできます。

### 提出可能なタイプ

| タイプ | 説明 | Entry-point 組 |
|------|------|----------------|
| モジュール (Module) | ロボットの機能拡張、業務ロジックの実装 | `erispulse.module` |
| アダプター (Adapter) | 新しいメッセージプラットフォームとの接続 | `erispulse.adapter` |

## 速攻リリース

3ステップで完了：プロジェクトの設定 → PyPI へのリリース → モジュールストアへの提出

### 1. pyproject.toml の設定

プロジェクトディレクトリに `pyproject.toml`、`README.md` が存在することを確認し、タイプに応じて entry-points を設定します。

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

> **注意**：パッケージ名は `ErisPulse-` で始めるのが推奨です。Entry-point のキー名（例：`"MyModule"`）は、SDK 内でのモジュールのアクセス名になります。

### 2. PyPI へのリリース

```bash
# ビルド + リリース（PyPI アカウントが必要）
pip install build twine
python -m build
python -m twine upload dist/*
```

リリースが成功したら、インストールを確認します。

```bash
pip install ErisPulse-MyModule
```

### 3. モジュールストアに提出（ErisPulse Workbench）

モジュールの収録と認証はすべて **ErisPulse Workbench** で行います：**[https://workbench.erisdev.com/](https://workbench.erisdev.com/)**。提出後、`repository_dispatch` でモジュールインデックスリポジトリに配信され、ワークフローが完了するとストアに反映されます（通常数分以内）。

#### 方法1：ウェブサイトから提出（初回推奨）

1. ウェブワークベンチを開き、**GitHub / Codeberg** アカウントでログインします（過去のモジュールは、モジュール詳細ページの「このモジュールを認証」から所有権を取得できます）
2. 左メニューの「新規モジュールを提出」→ フォームに記入：名称 / タイプ（module · adapter）/ PyPI パッケージ名 / 説明（10文字以上）/ 作者 / リポジトリアドレス（github.com または codeberg.org）/ カテゴリ（1 ツール · 2 エンタメ · 3 管理 · 4 通知 · 5 AI · 6 プラットフォーム · 7 分析）/ タグ / 最低 SDK バージョン
3. 提出すると即時有効化され、「未検証」と表示されます（公式審査がまだで、ユーザーがインストール時にリスク警告を確認する必要があります）；「認証審査」が通ると「検証済み」になります

#### 方法2：API による自主提出（CLI / CI 環境）

**① アクセストークンの生成**：ワークベンチの「オープンインターフェース → アクセストークン」ページ → 名前を記入 →「トークン生成」。形式は `epat_` + 40桁の16進数で、**生成時に一度だけ表示されます**；二段階認証を有効にしているアカウントは「動的コード不要」にチェックを付けると、以降のセキュアなエンドポイントで `totp_code` を要求されなくなります。

**② 要求の形式**：

```http
Authorization: Bearer epat_…
Content-Type: application/json
```

リクエストボディは **UTF-8 エンコードの JSON** でなければなりません。Windows 終端ではデフォルトの GBK で、日本語が UTF-8 以外のバイトに変換され、サーバーは拒否します（`415 ENCODING_INVALID` とエラーメッセージが表示され、問題のあるフィールドが明示されます）—— 事前に `chcp 65001` を実行するか、リクエストボディを UTF-8 ファイルに保存して `curl --data-binary @body.json` で送信してください。

**③ モジュールの提出**：

```bash
curl -X POST https://workbench.erisdev.com/api/modules/submit \
  -H "Authorization: Bearer epat_…" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyModule",
    "type": "module",
    "package": "ErisPulse-MyModule",
    "description": "モジュール説明、10文字以上",
    "author": "Your Name",
    "repository": "https://github.com/you/MyModule",
    "category": 1,
    "tags": ["ツール"],
    "i18n": ["ja", "en"],
    "min_sdk_version": ">=2.7.0"
  }'
```

**④ 検索と管理**：`GET /api/modules/ops?name=MyModule&type=module` で提出・審査の進捗を確認できます；`POST /api/modules/manage` で編集 / 転正 / 削除ができます；`POST /api/modules/batch` で一括操作が可能です。完全なエンドポイント一覧は、ワークベンチの「使用文書」（トークン / 所有権の認証 / モジュール管理 / FAQ）をご覧ください。

### 4. 既にリリースしたモジュールの管理

ワークベンチの「モジュールリスト」にログイン → 自分のモジュールの詳細ページで、説明、リポジトリ、タグなどを編集できます（バージョン番号は PyPI から自動同期されます）、削除、所有権の認証を開始できます；API 側は `manage` / `batch` エンドポイントを使用します。

> 提出したばかりのモジュールは、リストに反映されるまで数分かかる場合があります。

## 既にリリースしたモジュールの更新

1. `pyproject.toml` の `version` を更新
2. 再びビルドしてアップロード：`python -m build && python -m twine upload dist/*`
3. モジュールストアは自動的に PyPI 上の最新バージョンを同期します

ユーザーは `epsdk upgrade MyModule` でアップデートできます。

## リリース前のチェックリスト

PyPI にプッシュする前に、以下の項目を一つ一つ確認してください：

### コード品質

- [ ] 公開 API に型注釈を付与（関数の引数と戻り値）
- [ ] 公開メソッドにドキュメント文字列を付与（`"""..."""` 形式、`:param` / `:return` / `:raises` を含む）
- [ ] `ruff check` で警告が発生しない
- [ ] テストカバレッジは 80% 以上
- [ ] `pytest` ですべてのテストが通る

### 兼容性

- [ ] `pyproject.toml` に最低 SDK バージョンを宣言：`dependencies = ["ErisPulse>=x.y.z"]`
- [ ] `get_meta()` の `ModuleMeta(min_sdk_version="x.y.z")` で実行時の最低 SDK バージョンを宣言（アダプターはクラス属性 `min_sdk_version` を使用）—— ユーザー環境の SDK が低すぎる場合、フレームワークはロード時に明確なエラーを表示してロードをスキップし、不明なランタイムエラーを回避します
- [ ] Python 3.10 / 3.11 / 3.12 / 3.13 でテスト
- [ ] 対象オペレーティングシステム（Windows / Linux / macOS、該当する場合）でテスト
- [ ] 循環インポートの依存がない

### 設定

- [ ] 宣言的設定（`ConfigClass` + `BaseConfig` / `BotAccountConfig`）を使用する場合、設定フィールドに `description`（i18n 形式が推奨）と `ui` メタデータを付与
- [ ] i18n 翻訳キーを登録している場合、5言語すべて（zh-CN / zh-TW / en / ja / ru）をカバー
- [ ] 敏感なフィールドには `secret=True` を付与

### ドキュメント

- [ ] `README.md` にインストール方法と基本的な使用例を記載
- [ ] `README.md` に設定方法（設定ファイルの例 + 環境変数）を記載
- [ ] `CHANGELOG.md` にすべての変更を記録
- [ ] アダプターはプラットフォームの機能ドキュメントを更新（サポートする Send タイプ、イベントタイプなど）

### リリース

- [ ] `pyproject.toml` のバージョン番号を更新
- [ ] ビルドが通る：`python -m build`
- [ ] PyPI にアップロード：`python -m twine upload dist/*`
- [ ] インストールの検証が通る：`pip install ErisPulse-xxx && epsdk run`

## 開発モードでのテスト

正式リリース前に、ローカルで編集可能なモードでテストできます：

```bash
epsdk install -e /path/to/MyModule
# または
pip install -e /path/to/MyModule
```

## 一般的な質問

### パッケージ名は `ErisPulse-` で始める必要があるか？

必須ではありませんが、強く推奨します。これは PyPI 上で ErisPulse エコシステムのパッケージをユーザーが識別しやすくするためです。

### 1つのパッケージで複数のモジュールを登録できるか？

できます。`entry-points` に複数のキーと値を設定できます：

```toml
[project.entry-points."erispulse.module"]
"ModuleA" = "MyPackage:ModuleA"
"ModuleB" = "MyPackage:ModuleB"
```

### 審査にはどのくらい時間がかかるか？

通常 1〜3 営業日で完了します。モジュールストアの「マイモジュール」で検証ステータスを確認できます。

## Docker イメージでアプリケーションを配布する

PyPI に公開するのに適していない場合（プライベート依存、事前設定環境が必要な場合）、**GitHub Container Registry (GHCR)** を使って Docker イメージを公開し、他のユーザーが `docker pull` で一発起動できるようにできます。

### 適用シーン

- あなたが**完全なロボットアプリケーション**（モジュール + 設定 + 入口スクリプト）を持っていて、ワンクリックで配布したい
- モジュール/アダプターが**プライベートパッケージ**や特別なインストールフローを必要とするため、PyPI に適していない
- ユーザーの使用を容易にする**オールインワン**のデプロイメントを提供したい

### 1. Dockerfile の作成

ErisPulse 公式イメージをベースに、あなたのモジュールを追加するだけです：

```dockerfile
FROM erispulse/erispulse:latest

LABEL org.opencontainers.image.title="ErisPulse-MyModule" \
      org.opencontainers.image.description="モジュール説明" \
      org.opencontainers.image.url="https://github.com/yourname/ErisPulse-MyModule" \
      org.opencontainers.image.source="https://github.com/yourname/ErisPulse-MyModule"

COPY pyproject.toml README.md ./
COPY MyModule/ ./MyModule/

RUN uv pip install --system -e .
```

モジュールに追加のシステム依存（例：SSH クライアントなど）が必要な場合は、`RUN uv pip install` の後に追加します：

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
```

> `erispulse/erispulse:latest` には ErisPulse、ErisPulse-Dashboard、Python 実行環境、uv が含まれているため、再度インストールする必要はありません。

### 2. GitHub Actions ワークフローの作成

`.github/workflows/docker-publish.yml` に作成します：

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
      - name: コードをチェックアウト
        uses: actions/checkout@v4

      - name: QEMU のセットアップ (多アーキテクチャ対応)
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

> `GITHUB_TOKEN` は GitHub Actions が自動提供するため、手動でキーを作成する必要はありません。

### 3. ビルドのトリガー

コードをプッシュするか、タグを打つと自動的にビルドされます：

```bash
# main ブランチにプッシュしてトリガー
git push origin main

# またはタグを打ってトリガー
git tag v1.0.0
git push origin v1.0.0
```

GitHub リポジトリの **Actions** ページから手動でトリガーすることもできます。

### 4. イメージを公開に設定

GHCR イメージはデフォルトで **private** です。他のユーザーがログインせずにプルできるようにするには、GitHub で公開に設定する必要があります：

1. リポジトリにアクセス → **Packages** → 対応するパッケージをクリック
2. **Package settings** → **Danger Zone** → **Change visibility** → **Public**

### 5. ユーザーの使用

ビルドが完了したら、ユーザーは `docker run` で一行で起動できます：

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

または `docker-compose.yml` を使用：

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

### Docker Hub にも同時に公開する

ワークフローを拡張し、ログインステップの前に Docker Hub にログインし、`images` に Docker Hub のアドレスを追加します：

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

> `DOCKERHUB_USERNAME` と `DOCKERHUB_TOKEN` は、リポジトリの **Settings → Secrets** に追加する必要があります。

### Docker イメージ vs PyPI リリース

| 特性 | Docker イメージ (GHCR) | PyPI リリース |
|------|---------------------|-----------|
| 分布方法 | `docker pull` で一発起動 | `pip install` + 手動設定 |
| 適用範囲 | 完全なアプリケーション/ソリューション | 単一のモジュール/アダプター |
| プライベート依存 | 天然にサポート | プライベート PyPI ソースが必要 |
| モジュールストア | 不適切 | モジュールストアに提出可能 |
| 多アーキテクチャ | amd64/arm64 をサポート | アーキテクチャに依存しない |

両方の方法は互いに矛盾しません——モジュールを PyPI でモジュールストアに公開すると同時に、GHCR でオールインワンの Docker イメージを提供することも可能です。

## 次に進む

### リリース前に品質を確保する

- [モジュールテスト（ErisPulse-Testing）](testing.md) — 上記のチェックリストを自動テストで実行する
- [モジュールのベストプラクティス](modules/best-practices.md) / [アダプターのベストプラクティス](adapters/best-practices.md) — リリース前のエンジニアリングの仕上げ

### リリース後にユーザーが使いやすいようにする

- [CLI コマンド](../user-guide/cli-reference.md) — ユーザー側の `epsdk install` / `epsdk upgrade` の動作
- [プラットフォーム特性ガイド](../platform-guide/README.md) — アダプター開発者がプラットフォームドキュメントを維持する場所



======
API 参考
======


### 核心模块 API

# コアモジュール API

> [!TIP]
> **いつこのドキュメントを読むべきか**：ストレージ、設定、ログ、モジュール管理、ルーティング、HTTP クライアントなどのコア機能を使う必要があり、具体的なメソッドシグネチャを思い出せないときに、本書を素早く参照してください。不要な場合はスキップしてください。

本ドキュメントは、ErisPulse コアモジュールの API クイックリファレンスであり、メソッドシグネチャと簡単な説明を含みます。詳細な使い方やサンプルについては、各モジュールの「完全なドキュメント」リンクをクリックしてください。

## Storage モジュール

設定可能なバックエンド（SQLite/MySQL/PostgreSQL）に基づくキーバリューストアシステムで、汎用 SQL チェーンクエリをサポートし、バックエンドは設定でワンクリックで切り替え可能です。詳細は [ストレージバックエンド](../advanced/storage-backends.md) を参照してください。

### 基本操作

```python
from ErisPulse import sdk

sdk.storage.set("key", "value")
value = sdk.storage.get("key", default_value)
keys = sdk.storage.keys()
sdk.storage.delete("key")
```

### 一括操作

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

### 属性アクセス

```python
sdk.storage.my_key          # sdk.storage.get("my_key") と同等
sdk.storage.my_key = "val"  # sdk.storage.set("my_key", "val") と同等
```

### SQL チェーンクエリ

Storage モジュールは、チェーン呼び出しスタイルの汎用 SQL クエリビルダーを提供し、カスタムテーブルに対する CRUD 操作をサポートします。

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> 完全なチェーンクエリ API（Select/Insert/Update/Delete/Where/OrderBy/Limit、AlterTable、トランザクションなど）については、[SQL クエリビルダー](../advanced/sql-builder.md) を参照してください。

### ストレージバックエンド抽象

`StorageManager` は `BaseStorage` 抽象基底クラスを継承しており、他のストレージメディア（Redis、MySQL など）への拡張をサポートします。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### 非同期インターフェース

Storage モジュールと Config モジュールの両方に非同期メソッド（接頭辞 `a`）が用意されています：**非同期がネイティブの主インターフェースで、同期メソッドは互換レイヤーです**（内部でバックグラウンドのイベントループにブリッジして実行されます）。既存の同期コードを変更する必要はありません。非同期ハンドラ内の新しいコードでは、優先的に非同期メソッドを使用してください。

```python
# 非同期ストレージ
value = await sdk.storage.aget("key")
await sdk.storage.aset("key", "value")
await sdk.storage.adelete("key")
keys = await sdk.storage.aget_all_keys()
await sdk.storage.aclear()

# 非同期一括操作
values = await sdk.storage.aget_multi(["k1", "k2"])
await sdk.storage.aset_multi({"k1": "v1", "k2": "v2"})
await sdk.storage.adelete_multi(["k1", "k2"])

# 非同期設定
value = await sdk.config.agetConfig("MyModule.key")
await sdk.config.asetConfig("MyModule.key", "value")
await sdk.config.aforce_save()
await sdk.config.areload()
```

## Config モジュール

TOML 形式の設定ファイル管理で、ドット区切りのキーパスをサポートします。

### API 概要

| メソッド | 説明 |
|------|------|
| `getConfig(key, default)` | 設定を読み取り。`"MyModule.subkey"` のようなドットパスをサポート |
| `getAllConfig()` | 全設定のスナップショット（ディープコピー、ディスク未書き込みの保留値ビューを含む） |
| `setConfig(key, value, immediate=False)` | 設定を書き込み。`immediate=True` の場合は即座にファイルへ保存 |
| `delConfig(key, immediate=False)` | 設定キーを削除（値を空にするのとは異なる）。ファイルから削除し、`config.set` イベントをトリガー（`new_value=None`） |
| `force_save()` | メモリ内の設定を強制的にファイルへ書き込み |
| `reload()` | ファイルから設定を再読み込み |
| `agetConfig(key, default)` | 非同期で設定を読み取り |
| `agetAllConfig()` | 非同期で全設定スナップショットを取得 |
| `asetConfig(key, value, immediate)` | 非同期で設定を書き込み |
| `adelConfig(key, immediate)` | 非同期で設定キーを削除（動作は `delConfig` と同じ） |
| `aforce_save()` | 非同期で強制保存 |
| `areload()` | 非同期で再読み込み |

### 例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

snapshot = sdk.config.getAllConfig()          # 全量スナップショット（ディープコピー）
sdk.config.delConfig("MyModule.deprecated")  # キーを削除（遅延書き込み）

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)

# 非同期インターフェース（非同期ハンドラ内で優先使用）
snapshot = await sdk.config.agetAllConfig()
await sdk.config.adelConfig("MyModule.deprecated")  # 非同期でキーを削除
```

> `setConfig` はデフォルトで遅延書き込みを採用しており（5 秒ごとに一括保存）、`immediate=True` を設定すると即座に設定ファイルへ永続化されます。設定変更は `config.set` ライフサイクルイベントをトリガーします。
> `delete` も同様に遅延書き込みと `config.set` イベント（`new_value=None`）をサポートしており、既存の `on_config_update` リスナーは変更なしで削除を検知できます。

## Logger モジュール

Rich 出力ベースのモジュール化ロギングシステムで、子ロガーとモジュールレベルの制御をサポートします。

### 基本的な使い方

```python
sdk.logger.debug("デバッグ情報")
sdk.logger.info("実行情報")
sdk.logger.warning("警告情報")
sdk.logger.error("エラー情報")
sdk.logger.critical("致命的エラー")
```

### 子ロガー

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("サブモジュールログ")

child_logger.get_child("utils")  # ネストをサポート
```

### ログレベル制御

```python
sdk.logger.set_level("DEBUG")                          # グローバルレベル
sdk.logger.set_module_level("MyModule", "DEBUG")       # モジュールレベル

# サポートされるレベル（低い順）：
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE は最下位レベル。フレームワーク内部の詳細なデバッグ情報（イベントディスパッチ、ルート登録など）を出力
sdk.logger.set_level("TRACE")                          # すべてのログを有効化
```

### ログ購読（プッシュ方式）

Dashboard などのモジュールが構造化ログをリアルタイムで受信できるようにするもので、レベルフィルタと履歴の再送をサポートします。

> **低レベルログの明示的な購読**：サブスクライバーの `min_level` はグローバルログレベルより低く設定できます。この場合、低レベルログは**一致するサブスクライバーにのみプッシュ**され、コンソールへ出力されず、メモリにも書き込まれないため、メインのログストリームの汚染を避けられます。
>
> ```python
> # グローバルは INFO でも、DEBUG ログを個別に購読可能
> @sdk.logger.handler("debug-tracer", min_level="DEBUG")
> def on_debug(log_data: dict): ...
> ```

```python
# デコレーター方式
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
| `handler(id, *, min_level)(func)` | デコレーター/直接呼び出しの両用。`id` が空の場合は関数名を使用。`min_level` はグローバルレベルより低く設定可能（低レベルログはサブスクライバーにのみプッシュされ、コンソール/メモリには送られない）。登録時に履歴ログを自動再送 |
| `remove_handler(id)` | サブスクライバーを削除 |

### 出力制御

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter モジュール

アダプターマネージャー。マルチプラットフォームアダプターの登録、起動、シャットダウンを管理します。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(platform)` | アダプターインスタンスを取得 |
| `exists(platform)` | アダプターが登録済みか確認 |
| `enable(platform)` / `disable(platform)` | アダプターを有効化/無効化 |
| `is_enabled(platform)` | 有効かどうかを確認 |
| `startup(platforms)` / `shutdown(platforms)` | アダプターを起動/シャットダウン |
| `is_running(platform)` | アダプターが実行中か確認 |
| `list_running()` | 実行中のすべてのアダプターを一覧表示 |
| `platforms` | すべてのプラットフォーム名のリストを取得 |
| `get_info(platform)` | アダプター登録情報（json-safe：meta + クラス名） |
| `get_meta(platform, resolve_i18n=True)` | アダプター紹介メタ情報（`module.get_meta` と整合、i18n 解析をサポート） |

### アダプターイベント

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot ステータス照会

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> 完全なアダプター管理 API については、[アダプターシステム API](adapter-system.md) を参照してください。

## Module モジュール

モジュールマネージャー。プラグインの登録、ロード、アンロードを管理します。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(name)` | モジュールインスタンスまたは遅延ロードプロキシを取得（登録済みだが未ロードの場合はプロキシを返す） |
| `exists(name)` | 登録済みか確認 |
| `is_loaded(name)` | ロード済みか確認 |
| `is_enabled(name)` | 有効か確認 |
| `enable(name)` / `disable(name)` | モジュールを有効化/無効化 |
| `load(name)` / `unload(name)` | モジュールをロード/アンロード |
| `call(module, method, *args, timeout=None, **kwargs)` | 対象モジュールのサービスメソッドをモジュール間で呼び出し（プロトコル化 RPC） |
| `list_registered()` | 登録済みモジュールを一覧表示 |
| `list_loaded()` | ロード済みモジュールを一覧表示 |
| `get_info(name)` | モジュール情報を取得 |
| `get_status_summary()` | モジュールステータスの概要を取得 |

### 属性アクセス

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # 同等のショートカット
```

### モジュール間呼び出し（RPC）

```python
# プロトコル化呼び出し：型付きエラー / 遅延モジュールの自動起動 / owner 帰属 / タイムアウトセマンティクス
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

サービス提供側の直接属性アクセス `sdk.module.Chat.get_history(...)` との違い：

| | `module.call()` | 直接属性アクセス |
|---|---|---|
| 対象が未登録/未有効 | `ModuleNotAvailableError` をスロー | `AttributeError` をスロー |
| 遅延ロードモジュール | 自動的に起動 | 非同期初期化モジュールは RuntimeError をスロー |
| `current_owner` | 対象モジュールに帰属 | 呼び出し元のまま |
| タイムアウト | デフォルト 30 秒、上書き可能 | なし |
| scope 監査 | `actions.<呼び出し元>.call` | なし |

### サービス契約（meta.services）

サービス提供側は `get_meta()` の `services` フィールドで対外ホワイトリストを宣言します（`commands` と対称）。宣言後は呼び出し可能な範囲が限定されます：

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **デフォルト = 開発者は意識不要**：`services` 未宣言時は任意の**公開**メソッドが呼び出し可能（後方互換）。アンダースコア付きプライベートメソッドは常に禁止。制限の主導権はユーザー側の scope 設定にあります
- 宣言後：ホワイトリスト内のメソッドのみ呼び出し可能。範囲外は `ServiceNotProvidedError` をスロー
- 呼び出し元の制限：`scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**サービス紹介（description）**：`services` は dict 形式をサポートし、各サービスの紹介を宣言できます
（純粋な文字列または i18n 辞書に対応）。サービスカタログ / AI 呼び出しポイントの説明として利用されます：

```python
return ModuleMeta(
    services=[
        "get_history",                              # シンプル形式：紹介はメソッド docstring の先頭行から自動取得
        {"name": "translate", "description": "テキストを指定言語に翻訳します"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "会話の要約"}},
    ],
)
```

紹介の解析優先順位：**明示的な description（i18n は現在の言語に解析）> メソッド docstring の先頭行 > 空文字列**。

### サービスカタログ（services）

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': '会話履歴を取得'}]}

sdk.module.services("Chat")  # 指定モジュールのみ照会
```

**明示的に宣言された** `meta.services` を持つモジュールのみを一覧表示します。各サービスにはメソッドシグネチャ文字列
と紹介テキストが付属し、MCP 化（呼び出しポイントの AI への公開）のためのデータ基盤を提供します。

> ターゲット指定のイベント配信はライフサイクル層に属します：`lifecycle.emit(event, data, to="ModuleName")`。
> 詳細は [モジュール間通信](../advanced/module-communication.md) を参照してください。

## Lifecycle モジュール

イベント駆動のライフサイクルマネージャー。イベントの送出とリスニング機能を提供します。

### API 概要

| メソッド | 説明 |
|------|------|
| `on(event, priority=0)` | デコレーターでイベントハンドラを登録。ドット区切りマッチとワイルドカード `*` をサポート |
| `register(event, handler, priority=0)` | 関数形式でハンドラを登録 |
| `unregister(event, handler=None)` | ハンドラを削除 |
| `emit(event, data, to=None)` | イベントを非同期で発火。`to` で owner を指定するとターゲット配信 |
| `emit_sync(event, data, to=None)` | イベントを同期で発火（非同期ハンドラは create_task でスケジュール） |
| `submit_event(event_type, msg, data, source, to=None)` | 標準形式のイベントを送出（旧バージョン互換） |
| `start_timer(id)` / `stop_timer(id)` | パフォーマンスタイマー |

### 例

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"モジュール初期化: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"モジュールイベント: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})

# ターゲット配信：Chat モジュールが登録したフックにのみ配信
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")
```

> 完全な標準イベントリストと詳細な使い方については、[ライフサイクル管理](../advanced/lifecycle.md) を参照してください。

## Router モジュール

HTTP/WebSocket ルートマネージャー。FastAPI + Uvicorn ベースで、デコレータールート、ミドルウェア、グループ化、レート制限、CORS をサポートします。

> 完全なルーティング API ドキュメント（デコレータールート、WebSocket、ミドルウェア、レート制限、CORS、セキュリティヘッダーなど）については、[ルートマネージャー](../advanced/router.md) を参照してください。

### クイックリファレンス

```python
# HTTP ルート
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket ルート
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# ルートグループ
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## HTTP Client モジュール

統合ネットワーククライアント。HTTP リクエスト、WebSocket 接続、接続プール管理、自動リトライ、リクエスト統計、ライフサイクルイベント統合を集約します。

> 完全なネットワーククライアントドキュメント（リクエストメソッド、レスポンスオブジェクト、WebSocket クライアント、例外体系など）については、[ネットワーククライアント](../advanced/client.md) を参照してください。

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
```

## SDK デバッグ

### dump_state()

フレームワークの現在の実行状態のスナップショットをエクスポートします。デバッグと診断に使用します。

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

返される構造には、以下のサブシステムの状態が含まれます：

| フィールド | 説明 |
|------|------|
| `sdk` | SDK 初期化状態、Python バージョン、実行プラットフォーム、タイムスタンプ |
| `adapters` | 登録済み/起動済みアダプターのリスト、各プラットフォームの Bot オンライン状態 |
| `modules` | 登録済み/有効/無効/遅延ロードのモジュールリスト |
| `events` | 各種イベントハンドラの数（message/notice/request/meta/commands） |
| `router` | サーバー実行状態、HTTP/WebSocket ルート数 |

> [!NOTE]
> ErisPulse **2.5.2+** で追加

## Interaction インタラクションセッション

wait_reply の保留待機とセッション排他リースを管理します（`sdk.interaction`）。

### よく使うメソッド

```python
# セッション定時リマインダー：5 分間返信がなければリマインド、ユーザーの返信で自動キャンセル
reminder = event.remind(300, "まだいますか？")
reminder.cancel()  # 手動キャンセル

# タイムアウトエスカレーション：時刻になったら必ず届く（返信ではキャンセルされない）
event.escalate(1800, lambda e: notify_master("30 分間未処理"))

# 複数同時待機：早い者勝ち
which, reply = await event.select(
    event.expect(pattern="同意*", user="A"),
    event.expect(pattern="拒否*", user="B"),
    timeout=60,
)

# セッションレベル待機：同じグループ内の誰の返信でもマッチ
reply = await event.wait_reply(session=True, prompt="誰か答えてくれませんか？")

# セッションの現在の所有者を照会（誰がこのユーザーと対話中か）
owner = sdk.interaction.get_owner_of(event)

# セッション排他リースを取得（使用中の場合は None を返す）
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # 排他的インタラクション
    finally:
        lease.release()

# コンテキストマネージャー形式（使用中の場合は SessionOccupiedError をスロー）
with sdk.interaction.hold(event) as lease:
    ...

# 保留中セッションの統計
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

モジュールのアンロード / アダプターのシャットダウン時には、その保留中の待機とタイマーが自動キャンセルされ（待機側は即座に `None` を返す）、
返信がマッチした時点で scope 権限が自動的に再確認されます（ユーザーがブラックリスト登録 / モジュールのバインド解除の場合は待機を終了）。

> [!NOTE]
> 本セクションの機能は ErisPulse **2.8.0+** で追加

## Transcript セッション受信トレイ

セッションごとの直近メッセージフローの自動記録と照会（`sdk.transcript`）。AI 対話や
繰り返し防止など、コンテキスト記憶系モジュールの共通基盤として機能します。

### よく使うメソッド

```python
# 簡便な照会（推奨）：現在のセッションの直近 20 件（ユーザーとボットを含む、時間昇順）
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# マネージャー API
sdk.transcript.append(event, "user", "テキスト")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

設定（`ErisPulse.transcript`）：`enabled`（デフォルト有効）、`max_per_session`（セッションごとの上限、デフォルト 50）、
`ttl_hours`（グローバル有効期限、デフォルト 168 時間）。データは独立した SQLite テーブルに保存され、超過/期限切れデータは遅延クリーンアップされます。

> [!NOTE]
> 本セクションの機能は ErisPulse **2.8.0+** で追加



### 事件系统 API

# イベントシステム API

> [!TIP]
> **このドキュメントを読むべきタイミング**：コマンドの登録、メッセージ/通知/リクエストイベントのリッスン、または `event.reply()` / `wait_reply()` / `confirm()` などのイベントインタラクションメソッドを使用する必要がある場合に、本文を参照してください。不要であればスキップしてください。

本ドキュメントでは、ErisPulse イベントシステムの API について詳しく説明します。

イベントシステムは、プラットフォームイベントをタイプごとに 5 種類のハンドラーへディスパッチします：

```mermaid
flowchart LR
    A["プラットフォームイベント<br/>（OneBot12 標準）"] --> B{"イベントタイプ"}
    B --> C["command<br/>コマンドハンドラー"]
    B --> D["message<br/>メッセージハンドラー"]
    B --> E["notice<br/>通知ハンドラー"]
    B --> F["request<br/>リクエストハンドラー"]
    B --> G["meta<br/>メタイベントハンドラー"]
    C & D & E & F & G --> H["Event ラッパークラス<br/>reply / get_text / done など"]
```

## Command コマンドモジュール

### コマンドの登録

```python
from ErisPulse.Core.Event import command

# 基本コマンド
@command("hello", help="挨拶を送る")
async def hello_handler(event):
    await event.reply("こんにちは！")

# エイリアス付きコマンド
@command(["help", "h"], aliases=["ヘルプ"], help="ヘルプを表示")
async def help_handler(event):
    pass

# 権限付きコマンド
def is_admin(event):
    return event.get("user_id") in admin_ids

@command("admin", permission=is_admin, help="管理者コマンド")
async def admin_handler(event):
    pass

# 非表示コマンド
@command("secret", hidden=True, help="シークレットコマンド")
async def secret_handler(event):
    pass

# コマンドグループ
@command("admin.reload", group="admin", help="モジュールを再読み込み")
async def reload_handler(event):
    pass

# サブコマンド（スペース区切りの複数トークンからなるコマンド名）
# マッチングには最長プレフィックスを採用：/admin add x は admin add に優先的にヒット（args は ["x"]）。
# サブコマンドで permission が宣言されていない場合、親チェーン上で最も近い位置で権限を宣言している祖先コマンドを継承します
@command("admin add", help="管理者を追加")
async def admin_add_handler(event):
    pass
```

**命名競合ルール**：コマンド名はエイリアスよりも優先されます。既存のコマンドと同名のエイリアスを登録した場合、そのエイリアスは無効となり警告が出力されます。既存のエイリアスと同名のコマンドを登録した場合はコマンド名が優先して有効となり、無効となったエイリアスは自動的に削除されます——いずれの競合の場合も WARNING ログが出力され、サイレントに乗っ取られることはありません。

### コマンド情報

すべてのコマンド照会 API はオプションの**セッションコンテキスト**をサポートしています：`event=`（Event または dict）を渡すか、明示的に `platform=` / `bot_id=` / `session_id=` を渡します（event と併用した場合は明示的パラメータが優先されます）。これにより、スコープモジュールの次元で現在のセッションにおいて利用不可のモジュールのコマンドがフィルタリングされます（詳細は advanced/scope.md を参照）。すべてオプションのキーワード引数であり、渡さない場合は従来通りの全量動作が維持されます。

```python
# コマンドヘルプを取得
help_text = command.help()

# セッション認識ヘルプ：現在のセッションで利用可能なコマンドのみを一覧表示
help_text = command.help(event=event)

# 特定のコマンドを取得（マージ・オーバーライド後の有効なパラメータを返す。セッションで利用不可の場合は None を返す）
cmd_info = command.get_command("admin")
cmd_info = command.get_command("admin", event=event)

# すべてのコマンドを取得（セッション認識時は利用不可モジュールのコマンドをフィルタリング）
all_commands = command.get_commands()
all_commands = command.get_commands(event=event)

# コマンドグループ内のすべてのコマンドを取得（セッション認識フィルタリングに対応）
admin_commands = command.get_group_commands("admin")
admin_commands = command.get_group_commands("admin", event=event)

# すべての可視コマンドを取得
visible_commands = command.get_visible_commands()

# セッション認識の可視コマンド（event または明示的キーワードのいずれかで可）
visible_commands = command.get_visible_commands(event=event)
visible_commands = command.get_visible_commands(
    platform=event.get("platform"),
    bot_id=event.get_self_account_id(),
    session_id=event.get_session_id(),
)
```

### 返信を待つ

```python
# ユーザーの返信を待つ
@command("ask", help="ユーザー情報を尋ねる")
async def ask_command(event):
    reply = await command.wait_reply(
        event,
        prompt="お名前を入力してください:",  # すでに上で送信済み
        timeout=30.0
    )
    
    if reply:
        name = reply.get_text()
        await event.reply(f"こんにちは、{name}さん！")

# 検証付きの返信待ち
def validate_age(event_data):
    try:
        age = int(event_data.get_text())
        return 0 <= age <= 150
    except ValueError:
        return False

@command("age", help="ユーザーの年齢を尋ねる")
async def age_command(event):
    await event.reply("年齢を入力してください:")
    
    reply = await command.wait_reply(
        event,
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"あなたの年齢は {age} 歳です")

# コールバック付きの返信待ち
async def handle_confirmation(reply_event):
    text = reply_event.get_text().lower()
    if text in ["はい", "yes", "y"]:
        await event.reply("操作が確認されました！")
    else:
        await event.reply("操作はキャンセルされました。")

@command("confirm", help="操作を確認")
async def confirm_command(event):
    await command.wait_reply(
        event,
        prompt="'はい'または'いいえ'を入力してください:",
        callback=handle_confirmation
    )
```

## Message メッセージモジュール

### メッセージイベント

```python
from ErisPulse.Core.Event import message

# すべてのメッセージをリッスン
@message.on_message()
async def message_handler(event):
    sdk.logger.info(f"メッセージを受信: {event.get_text()}")

# プライベートメッセージをリッスン
@message.on_private_message()
async def private_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"プライベートチャットから: {user_id}")

# グループメッセージをリッスン
@message.on_group_message()
async def group_handler(event):
    group_id = event.get_group_id()
    sdk.logger.info(f"グループチャットから: {group_id}")

# @メッセージをリッスン
@message.on_at_message()
async def at_handler(event):
    mentions = event.get_mentions()
    sdk.logger.info(f"メンションされたユーザー: {mentions}")
```

### 条件付きリッスン

```python
# 優先度を使用して実行順序を制御
@message.on_message(priority=10)  # 数値が大きいほど優先度が高い
async def high_priority_handler(event):
    pass

# ハンドラー内部で条件フィルタリングを実装
@message.on_message()
async def filtered_handler(event):
    if "キーワード" not in event.get_text():
        return
    # キーワードを含むメッセージを処理
    pass
```

## Notice 通知モジュール

### 通知イベント

```python
from ErisPulse.Core.Event import notice

# フレンド追加
@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    await event.reply("フレンド追加ありがとうございます！")

# フレンド削除
@notice.on_friend_remove()
async def friend_remove_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"フレンド削除: {user_id}")

# グループメンバーの追加
@notice.on_group_increase()
async def member_increase_handler(event):
    user_id = event.get_user_id()
    await event.reply(f"新しいメンバーを歓迎します！")

# グループメンバーの減少
@notice.on_group_decrease()
async def member_decrease_handler(event):
    user_id = event.get_user_id()
    sdk.logger.info(f"グループメンバーが退出: {user_id}")
```

## Request リクエストモジュール

### リクエストイベント

```python
from ErisPulse.Core.Event import request

# フレンドリクエスト
@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    sdk.logger.info(f"フレンドリクエスト: {user_id}, コメント: {comment}")

# グループ招待リクエスト
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"グループ招待: {group_id}, 送信者: {user_id}")
```

## Meta メタイベントモジュール

### メタイベント

```python
from ErisPulse.Core.Event import meta

# 接続イベント
@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} が正常に接続されました")

# 切断イベント
@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"プラットフォーム {platform} が切断されました")

# ハートビートイベント
@meta.on_heartbeat()
async def heartbeat_handler(event):
    sdk.logger.debug("ハートビートを受信")
```

### Bot ステータス照会

アダプターがメタイベントを送信すると、フレームワークは自動的に Bot のステータスを追跡します。照会 API とライフサイクルイベントのリッスンについては、[アダプターシステム API - Bot ステータス管理](adapter-system.md#bot-ステータス管理) を参照してください。

## Event ラッパークラス

Event モジュールのイベントハンドラーは、Event ラッパークラスのインスタンスを受け取ります。これは dict を継承し、便利なメソッドを提供します。メソッドの完全な一覧、パラメータシグネチャ、および動作の詳細については [Event ラッパークラス詳解](../developer-guide/modules/event-wrapper.md) を参照してください。このセクションでは概要のみを紹介します。

### 機能概要

- **イベント基本情報**：`get_id()` / `get_time()` / `get_type()` / `get_detail_type()` / `get_platform()`
- **ボット情報**：`get_self_platform()` / `get_self_user_id()` / `get_self_account_id()` / `get_self_info()`
- **セッション識別**：`get_target_id()`（統一ターゲット ID。`group_id` → `channel_id` → `guild_id` → `thread_id` → `user_id` の順で最初の空でない値を取得）；`get_session_id()`（形式は `{platform}:{detail_type}:{target_id}`、例：`"telegram:private:12345"`）
- **メッセージ内容と送信者**：`get_message()` / `get_alt_message()` / `get_text()` / `get_user_id()` / `get_sender()` / `get_group_id()` など
- **メッセージタイプ判定**：`is_message()` / `is_private_message()` / `is_group_message()` / `is_at_message()` / `has_mention()` / `get_mentions()`
- **返信**：`reply(content, method=..., at_sender=..., quote=..., at_users=..., reply_to=..., at_all=..., via=...)` / `reply_ob12()`；プラットフォーム機能の照会 `supports()` / `available_methods()`；自由送信チェーン `send_chain()` は [SendDSL 詳解](../developer-guide/adapters/send-dsl.md#方法2eventsend_chain) を参照
- **コマンド情報**：`get_command_name()` / `get_command_args()` / `is_command()` など
- **インタラクティブセッション**：`wait_reply()` / `confirm()` / `choose()` / `collect()` / `wait_for()` / `conversation()`
- **ツール**：`to_dict()`（内部キーをフィルタリング）/ `get_raw()` / `get_raw_type()`

> 各メソッドの完全なパラメータ説明と例については [Event ラッパークラス詳解](../developer-guide/modules/event-wrapper.md) を参照してください。マルチターン対話の高度な内容は [Conversation マルチターン対話](../advanced/conversation.md) を参照してください。

### チェーン制御

`event.done(claim=, stop=)` は「クレーム（claim）」と「ブロック（stop）」という 2 つの直交するセマンティクスを統一的に制御します：

- **クレーム（claim）**：イベントが処理済みであることをマークし（`_processed`）、コマンドディスパッチャーはこれに基づいて重複排除をスキップします
- **ブロック（stop）**：低優先度ハンドラーへの伝播を阻止します（`_propagation_stopped`）

```python
# クレーム + ブロック（デフォルト）
event.done()

# クレームのみ、ブロックなし（低優先度のオブザーバーも引き続き確認できる）
event.done(stop=False)

# ブロックのみ、クレームなし（ファイアウォール / レート制限など）
event.done(claim=False)

# mark_processed が本体メソッド、done はそのエイリアス
event.mark_processed()             # event.done() と同等
event.mark_processed(stop=False)   # event.done(stop=False) と同等

# ステータスの照会
event.is_processed()  # クレーム済みかどうか
event.is_stopped()    # 伝播がブロック済みかどうか
```

### プラットフォーム拡張メソッド

アダプターは Event にプラットフォーム固有のメソッドを登録でき、そのメソッドは対応するプラットフォームのインスタンスでのみ利用できます。

#### ユーザー：プラットフォーム拡張メソッドの利用

アダプターがプラットフォーム固有のメソッドを登録すると、イベントハンドラー内で直接呼び出せるようになります。メソッドはプラットフォームごとに異なるため、対応する [プラットフォームドキュメント](../platform-guide/) を参照してください。

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

#### プラットフォームに登録済みのメソッドの照会

```python
from ErisPulse.Core.Event import get_platform_event_methods

# 特定のプラットフォームに登録されているメソッドを確認
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
# メールイベント - メールのメソッドのみ
event = Event({"platform": "email", "email_raw": {"subject": "Hello"}})
event.get_subject()      # ✅ "Hello"
event.get_chat_type()    # ❌ AttributeError

# Telegram イベント - Telegram のメソッドのみ
event = Event({"platform": "telegram", "telegram_raw": {"chat": {"type": "private"}}})
event.get_chat_type()    # ✅ "private"
event.get_subject()      # ❌ AttributeError
```

#### `hasattr` / `dir` のサポート

```python
hasattr(event, "get_subject")   # platform="email" の場合のみ True を返す
"get_subject" in dir(event)     # 同様
```

### アダプター：プラットフォーム拡張メソッドの登録

アダプターはデコレーターを通じて Event にプラットフォーム固有のメソッドを登録できます。メソッドの最初のパラメータは `self`（Event インスタンス）で、イベントデータに自由にアクセスできます。

#### 単一メソッドの登録

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

#### 一括登録（Mixin クラス）

メソッドが多い場合は、Mixin クラスによる一括登録が推奨されます：

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

#### 戻り値の規約

| シナリオ | 戻り値 | ユーザーの使用方法 |
|------|--------|------------|
| データを返す（テキスト、辞書など） | 値をそのまま返す | `subject = event.get_subject()` |
| 操作を実行する（メッセージ送信など） | `asyncio.Task` を返す | `task = event.do_something()` `await` は任意 |

> **推奨**：データを返さないメソッドは `asyncio.Task` を返すようにしてください。そうすることで、`await` するかどうかをユーザーが自由に決定でき、`await` しなかった場合でも操作は最後まで実行されます。

```python
@register_event_method("email")
def forward_email(self, to_address: str):
    """メールを転送する — Task を返し、ユーザーが await するかどうかを自由に決定できる"""
    import asyncio
    return asyncio.create_task(
        self._do_forward(to_address)
    )

# ユーザーは await で結果を待つことができる
await event.forward_email("user@example.com")

# await しない場合でも、操作はバックグラウンドで実行される
event.forward_email("user@example.com")
```

#### メソッドの登録解除

```python
from ErisPulse.Core.Event import unregister_event_method, unregister_platform_event_methods

# 単一メソッドの登録解除
unregister_event_method("email", "get_subject")

# 特定プラットフォームの全メソッドの登録解除（アダプターの shutdown 時に呼び出す）
unregister_platform_event_methods("email")
```

#### 組み込みメソッドのオーバーライド

`register_event_mixin` / `register_event_method` は、Event の組み込みメソッド（`confirm`、`choose`、`collect`、`wait_reply`、`reply` など）のオーバーライドをサポートしています。登録されたプラットフォームメソッドは `Event.__getattribute__` を経由して組み込みメソッドより優先的に有効になるため、アダプターはプラットフォーム特有のインタラクション実装を提供できます。

組み込み実装は `_builtin_*` 関数としてエクスポートされており、オーバーライド側はこれらをフォールバックとして呼び出せます：

```python
from ErisPulse.Core.Event import register_event_mixin, _builtin_choose

class YunhuEventMixin:
    async def choose(self, prompt, options, timeout=60, method="Text"):
        # Yunhu プラットフォームではボタンコンポーネントを使用
        buttons = [[{"text": opt} for opt in options]]
        await self.reply(prompt)
        # ...ボタンコールバックまたはテキスト返信を待つ...
        # 組み込みロジックへフォールバック
        return await _builtin_choose(self, None, options, timeout, "Text")

register_event_mixin("yunhu", YunhuEventMixin)
```

## クロスプラットフォーム拡張（ワイルドカード）

`register_event_method` と `register_event_mixin` は、プラットフォーム名として `"*"` を渡すことをサポートしており、登録されたメソッドは**すべてのプラットフォーム**の Event インスタンスで利用できます。AI 対話、コンテキスト管理など、クロスプラットフォームでの再利用が必要な機能モジュールに適しています。

### クロスプラットフォームメソッドの登録

```python
from ErisPulse.Core.Event.wrapper import register_event_method

@register_event_method("*")
async def ai_chat(self, prompt: str):
    """self は Event インスタンスであり、イベントデータや組み込みメソッドに自由にアクセスできる"""
    await self.reply(f"AI: {prompt}")
```

登録後、すべてのプラットフォームのイベントハンドラーから呼び出せます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handler(event):
    await event.ai_chat(event.get_text())
```

### メソッド解決の優先順位

属性アクセスで Event メソッドを取得する際の解決順序は次の通りです：

1. **プラットフォーム固有メソッド**（現在のプラットフォームのオーバーライド）
2. **ワイルドカードメソッド**（`"*"` で登録されたクロスプラットフォームメソッド）
3. **組み込みメソッド**（`reply`、`confirm` など）
4. **辞書キーとしてのアクセス**

> そのため、ワイルドカードメソッドは組み込みメソッド（`reply` など）をオーバーライドできますが、同名のプラットフォーム固有メソッドがあればさらにそちらが優先されます。

## 優先度システム

イベントハンドラーは優先度をサポートしており、数値が大きいほど優先度が高くなります：

```python
# 高優先度のハンドラーが先に実行される
@message.on_message(priority=10)
async def high_priority_handler(event):
    pass

# 低優先度のハンドラーが後に実行される
@message.on_message(priority=0)
async def low_priority_handler(event):
    pass
```



### 适配器系统 API

# アダプターシステム API

> [!TIP]
> **このドキュメントを読むべきケース**：アダプターの管理（インスタンスの取得、起動・停止、Bot のオンライン状態の確認）、Send DSL によるメッセージ送信、ミドルウェアの登録、またはアダプターへの Bot ステータス報告（meta イベント）の実装が必要な場合に本文をご参照ください。該当しない場合はスキップしてください。

このドキュメントでは、ErisPulse アダプターシステムの API について詳しく説明します。

## Adapter マネージャー

### アダプターの取得

```python
from ErisPulse import sdk

# 名前でアダプターを取得
adapter = sdk.adapter.get("platform_name")

# または、属性で直接アクセスすることもできます
adapter = sdk.adapter.platform_name
```

### アダプターイベントリスナーの使用
> 通常は、イベントの監視/処理には`Event`モジュールを使用することをお勧めします。
>
> また、`Event`モジュールは強力なラッパーを提供しており、モジュール開発にさらに便利さをもたらします。

```python
# OneBot12 標準イベントをリッスン
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 特定プラットフォームの標準イベントをリッスン
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# プラットフォームのネイティブイベントをリッスン
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### アダプターの管理

```python
# すべてのプラットフォームを取得
platforms = sdk.adapter.platforms

# アダプターが存在するかどうかを確認
exists = sdk.adapter.exists("platform_name")

# アダプターの有効化/無効化
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# アダプターの起動/終了
# 以下のメソッドはいずれも引数を渡す場合の例であり、引数なしの場合は登録済みのすべてのアダプターの起動/停止を意味します
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# アダプターが実行中かどうかを確認
is_running = sdk.adapter.is_running("platform_name")

# 実行中のすべてのアダプターを一覧表示
running = sdk.adapter.list_running()

# アダプターのメタ情報を取得（module.get_meta と整合、パネル/ストアなどで利用される）
info = sdk.adapter.get_info("platform_name")   # 登録情報（meta + クラス名、json-safe）
meta = sdk.adapter.get_meta("platform_name")   # 紹介メタ情報（description は i18n 解析に対応）
raw = sdk.adapter.get_meta("platform_name", resolve_i18n=False)  # 生の i18n 辞書をそのまま返す
```

## ミドルウェア

ミドルウェアは、イベントがハンドラーにディスパッチされる前に実行され、イベントデータの変更、フィルタリング、記録などを行うことができます。

### ミドルウェアの登録

```python
@sdk.adapter.middleware
async def my_middleware(event):
    sdk.logger.info(f"ミドルウェア処理: {event}")
    return event
```

### ミドルウェアの実行モデル

- **実行順序**：ミドルウェアは登録順に実行されます（先に登録されたものが先に実行される）
- **データの受け渡し**：各ミドルウェアは、直前のミドルウェアが返した `event` データを受け取ります。いずれかのミドルウェアが `None` を返した場合、その戻り値は無視され、元のデータが保持されたまま引き続き渡されます（同時に `warning` レベルのログが出力されます）
- **データの変更**：ミドルウェアはイベントデータを変更し、変更後の辞書を返すことができます
- **イベントの否決**：ミドルウェアが明示的に `False` を返した場合、イベントは否決されます。イベントは破棄され、どのハンドラーにも渡されず、アウトバウンドの副作用も一切発生しません。否決時には TRACE ログが出力され、`adapter.event.blocked` ライフサイクルフックがトリガーされます（ミドルウェア名と完全なイベントが渡されます）

```python
@sdk.adapter.middleware
async def add_timestamp(event):
    event["processed_at"] = time.time()
    return event

@sdk.adapter.middleware
async def filter_spam(event):
    if event.get("detail_type") == "private":
        text = event.get("alt_message", "")
        if "スパム広告" in text:
            return False  # 否決：イベントは破棄され、どのハンドラーにも渡されません
    return event
```

> **注意**：イベントを否決するのは、明示的に `False` を返した場合のみです（空の辞書 / `0` / `""` などの falsy 値を返しても否決されません）。
> `None` を返した場合も通過し、ペイロードは変更されません。否決されたイベントは、
> `adapter.event.blocked` フックをリッスンすることで、「イベントがなぜ応答しなかったのか」の監査や調査が可能です。

## Send メッセージ送信

### 基本的な送信

```python
# アダプターを取得
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

### サポートされる送信メソッドの照会

```python
# プラットフォームがサポートするすべての送信メソッドを一覧表示
methods = sdk.adapter.list_sends("onebot11")
# 戻り値: ["Text", "Image", "Voice", "Markdown", ...]

# 特定のメソッドの詳細情報を取得
info = sdk.adapter.send_info("onebot11", "Text")
# 戻り値:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "テキストメッセージを送信..."
# }
```

### チェーン装飾

```python
# @ユーザー
await adapter.Send.To("group", "456").At("789").Text("こんにちは")

# @全員
await adapter.Send.To("group", "456").AtAll().Text("皆さん、こんにちは")

# メッセージに返信
await adapter.Send.To("group", "456").Reply("msg_id").Text("返信内容")

# 組み合わせて使用
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("@したメッセージへの返信")
```

## API 呼び出し

### call_api メソッド

> **注意**：`call_api` はプラットフォームのネイティブ API を直接呼び出す低レベルメソッドです。パラメータや戻り値はプラットフォームによって異なる場合があるため、対応するプラットフォームのアダプタードキュメントをご参照ください。**メッセージの送信には Send DSL の使用をお勧めします**。`call_api` は、Send DSL が対応していないシナリオ（プラットフォーム固有のデータの取得やプラットフォーム管理インターフェースの呼び出しなど）でのみ使用してください。

```python
# プラットフォーム API を呼び出す
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# 標準化されたレスポンス
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "msg_id",
    "message": "",
    "{platform}_raw": raw_response
}
```

## アダプター基底クラス

### BaseAdapter のメソッド

```python
from ErisPulse import sdk
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.sdk = sdk
        # アダプターの初期化
        pass
    
    async def start(self):
        """アダプターを起動する（実装必須）"""
        pass
    
    async def shutdown(self):
        """アダプターを終了する（実装必須）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """プラットフォーム API を呼び出す（実装必須）"""
        pass
```

### Send ネストクラス

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """テキストメッセージを送信する"""
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

アダプターは、OneBot12 標準の **`meta` イベント**を送信することで、フレームワークに Bot の接続状態を通知します。システムはそこから自動的に Bot 情報を抽出し、ステータスの追跡を行います。

### meta イベントの報告

アダプターは `meta` イベントを通じて Bot のステータスを報告します。`detail_type` は 3 種類あります：`connect`（登録してオンライン）、`heartbeat`（ハートビートによる生存維持）、`disconnect`（オフラインとしてマーク）。`emit_meta()` を使って 1 行で送信することをお勧めします。meta イベントを送信しない場合でも、フレームワークは通常のイベント（message/notice/request）の `self` フィールドから自動的に Bot を検出します。

- **meta イベントの形式と送信方法**（送信タイミング、`emit_meta()` の使い方、手動での形式構築）については、[アダプターのベストプラクティス - Bot ステータス管理と Meta イベント](../developer-guide/adapters/best-practices.md#bot-状态管理与-meta-事件) をご参照ください
- **自動検出メカニズムとフレームワークの動作**については、[アダプターのコアコンセプト - Bot ステータス管理](../developer-guide/adapters/core-concepts.md#bot-状态管理) をご参照ください

### Bot ステータスの照会

```python
# すべてのアダプターと Bot の完全なステータスを取得（WebUI フレンドリー）
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

# すべての Bot を一覧表示
all_bots = sdk.adapter.list_bots()

# 指定したプラットフォームの Bot を一覧表示
tg_bots = sdk.adapter.list_bots("telegram")

# 単一の Bot の詳細を取得
info = sdk.adapter.get_bot_info("telegram", "123456")

# Bot がオンラインかどうかを確認
if sdk.adapter.is_bot_online("telegram", "123456"):
    print("Bot はオンラインです")
```

### Bot ステータスの値

| ステータス | 説明 |
|------|------|
| `online` | オンライン（イベントを継続的に受信、またはアダプターによる明示的なマーク） |
| `offline` | オフライン（アダプターによる明示的なマーク、またはシステム終了時に自動設定） |
| `unknown` | 不明（登録のみでステータス未確認） |

### ライフサイクルイベント

| イベント名 | 発生タイミング | データ |
|--------|---------|------|
| `adapter.bot.online` | 新しい Bot を初めて自動検出した時 | `{platform, bot_id, status}` |
| `adapter.status.change` | アダプターのステータス変化時 | `{platform, status}`。status のすべての値：`starting` / `started` / `start_failed` / `stopping` / `stopped` / `stop_failed` / `skipped-dependency`（依存するアダプターが未準備のため起動をスキップ）/ `disabled`（設定により無効化） |

```python
# Bot オンラインイベントをリッスン
@sdk.lifecycle.on("adapter.bot.online")
def on_bot_online(event):
    print(f"Bot がオンライン: {event['data']['platform']}/{event['data']['bot_id']}")

# アダプターのステータス変化をリッスン
@sdk.lifecycle.on("adapter.status.change")
def on_status_change(event):
    print(f"アダプター状態: {event['data']['platform']} -> {event['data']['status']}")
```

> システム終了時（`shutdown`）には、すべての Bot が自動的に `offline` としてマークされます。



====
技术标准
====


### 会话类型标准

# ErisPulse セッションタイプ標準

> [!TIP]
> **このドキュメントを読むべきケース**：アダプターでプラットフォームのネイティブセッションを標準タイプ（private/group/channel/guild/thread）にマッピングする場合や、モジュールで `Send.To()` にどのターゲットタイプを渡せばよいかわからない場合、`event.reply()` の自動変換を把握したい場合に本ドキュメントを参照してください。不要な場合はスキップしてください。

このドキュメントでは、受信イベントタイプと送信ターゲットタイプを含む、ErisPulse がサポートするセッションタイプの標準を定義します。

## 1. 基本概念

### 1.1 受信タイプ && 送信タイプ

ErisPulse は2種類のセッションタイプを区別します：

- **受信タイプ（Receive Type）**：受信するイベントの `detail_type` フィールド
- **送信タイプ（Send Type）**：メッセージ送信時に `Send.To()` メソッドへ渡すターゲットタイプ

### 1.2 タイプマッピング関係

```
受信タイプ (detail_type)     送信タイプ (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**重要なポイント**：
- `private` は受信時のタイプであり、送信時の標準タイプは `user` です
- `group`、`channel`、`guild`、`thread` は受信時と送信時でタイプが同じです
- **推奨パス**：`event.reply()` を直接使用する——タイプ変換とターゲット推論が自動的に行われ、手動処理は不要です（`private` → `user` の自動変換はここで行われます）
- **手動送信時**：送信タイプを直接渡してください（例：`Send.To("user", ...)`）。手動で `Send.To("private", ...)` のように受信タイプを渡しても自動変換されますが、推奨されません（§6.1 参照）

## 2. 標準セッションタイプ

### 2.1 OneBot12 標準タイプ

#### private
- **受信タイプ**：`private`
- **送信タイプ**：`user`
- **説明**：一対一のプライベートチャットメッセージ
- **ID フィールド**：`user_id`
- **対応プラットフォーム**：プライベートチャットをサポートするすべてのプラットフォーム

#### group
- **受信タイプ**：`group`
- **送信タイプ**：`group`
- **説明**：グループチャットメッセージ。各種形式のグループ（Telegram の supergroup など）を含みます
- **ID フィールド**：`group_id`
- **対応プラットフォーム**：グループチャットをサポートするすべてのプラットフォーム

#### user
- **受信タイプ**：`user`
- **送信タイプ**：`user`
- **説明**：ユーザータイプ。一部のプラットフォーム（Telegram など）では、プライベートチャットを private ではなく user として表現します
- **ID フィールド**：`user_id`
- **対応プラットフォーム**：Telegram などのプラットフォーム

### 2.2 ErisPulse 拡張タイプ

#### channel
- **受信タイプ**：`channel`
- **送信タイプ**：`channel`
- **説明**：チャンネルメッセージ。複数ユーザーへのブロードキャスト形式のメッセージをサポートします
- **ID フィールド**：`channel_id`
- **対応プラットフォーム**：Discord、Telegram、Line など

#### guild
- **受信タイプ**：`guild`
- **送信タイプ**：`guild`
- **説明**：サーバー/コミュニティメッセージ。通常、Discord の Guild レベルのイベントに使用されます
- **ID フィールド**：`guild_id`
- **対応プラットフォーム**：Discord など

#### thread
- **受信タイプ**：`thread`
- **送信タイプ**：`thread`
- **説明**：トピック/サブチャンネルメッセージ。コミュニティ内のサブディスカッションに使用されます
- **ID フィールド**：`thread_id`
- **対応プラットフォーム**：Discord Threads、Telegram Topics など

## 3. プラットフォームタイプマッピング

### 3.1 マッピングの原則

アダプターは、プラットフォームのネイティブタイプを ErisPulse 標準タイプにマッピングする役割を担います：

```
プラットフォームネイティブタイプ → ErisPulse 標準タイプ → 送信タイプ
```

### 3.2 一般的なプラットフォームのマッピング例

#### Telegram
```
Telegram タイプ         ErisPulse 受信タイプ   送信タイプ
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group
supergroup             group                   group  # group にマッピング
channel                channel                 channel
```

#### Discord
```
Discord タイプ         ErisPulse 受信タイプ   送信タイプ
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
OneBot11 タイプ       ErisPulse 受信タイプ   送信タイプ
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # group にマッピング
```

## 4. カスタムタイプの拡張

### 4.1 カスタムタイプの登録

アダプターはカスタムセッションタイプを登録できます：

```python
from ErisPulse.Core.Event import register_custom_type

# カスタムタイプの登録
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 カスタムタイプの使用

登録後、システムは自動的にこのタイプの変換と推論を処理します：

```python
# 自動推論
receive_type = infer_receive_type(event, platform="MyPlatform")
# 戻り値: "my_custom_type"

# 送信タイプへの変換
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# 戻り値: "custom"

# 対応する ID の取得
target_id = get_target_id(event, platform="MyPlatform")
# 戻り値: event["custom_id"]
```

### 4.3 カスタムタイプの登録解除

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. 自動タイプ推論

イベントに明示的な `detail_type` フィールドがない場合、システムは存在する ID フィールドに基づいてタイプを自動推論します：

> [!NOTE]
> **2.7.0+ での動作変更**：`detail_type` は、**既知のセッションタイプ**（標準またはカスタム）である場合にのみ直接採用されます。notice/request イベントの `detail_type`（`group_member_increase`、`friend_increase` など）は**セマンティックサブタイプ**でありセッションタイプではないため、代わりに ID フィールドに基づいて正しいセッションタイプが推論されます。

### 5.1 推論の優先順位

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
# イベントに group_id のみがある場合
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# 戻り値: "group"（group_id を優先使用）

# イベントに user_id のみがある場合
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# 戻り値: "private"

# notice イベントの detail_type はセマンティックサブタイプであり、2.7.0+ では ID フィールドから推論されます
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# 戻り値: "group"（"group_member_increase" ではなく）
```

## 6. API 使用例

### 6.1 メッセージ送信

```python
from ErisPulse import adapter

# ユーザーに送信
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# グループに送信
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# 自動変換 private → user：受信タイプを手動で渡すのは非推奨の書き方です（互換性の問題が生じる可能性があります）
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# 内部で自動変換されます: Send.To("user", "789")
# 推奨される方法：手動送信時は送信タイプ user を直接使用するか、event.reply() で自動変換を利用してください（6.2 参照）
```

### 6.2 イベントへの返信

```python
from ErisPulse.Core.Event import Event

# Event.reply() は自動的にタイプ変換を処理します（推奨パス）
await event.reply("返信内容")
# 内部で正しい送信タイプが自動的に使用されます（private → user などの変換はここで自動的に行われます）
```

### 6.3 コマンド処理

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # システムが自動的にセッションタイプを処理します
    # group_id か user_id かを手動で判断する必要はありません
    await event.reply("コマンドが正常に実行されました")
```

## 7. コア API リファレンス

### 7.1 タイプ変換

```python
from ErisPulse.Core.Event import convert_to_send_type, convert_to_receive_type

# 受信タイプ → 送信タイプ
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# 送信タイプ → 受信タイプ
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### 7.2 ID フィールドの照会

```python
from ErisPulse.Core.Event import get_id_field, get_receive_type

get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 7.3 ワンステップで送信情報を取得

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# Send.To() に直接使用
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 ターゲット ID の取得

```python
from ErisPulse.Core.Event import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 8. ユーティリティメソッド

```python
from ErisPulse.Core.Event import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

is_standard_type("private")     # True
is_standard_type("custom_type") # False

is_valid_send_type("user")      # True
is_valid_send_type("invalid")   # False

get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

clear_custom_types()                # すべてクリア
clear_custom_types(platform="discord")  # 指定したプラットフォームのみクリア
```

## 9. ベストプラクティス

### 7.1 アダプター開発者

1. **標準マッピングを使用**：新しいタイプを作成するのではなく、可能な限り標準タイプにマッピングしてください
2. **正しい変換**：受信タイプと送信タイプのマッピング関係が正しいことを確認してください
3. **元データの保持**：`{platform}_raw` に元のイベントタイプを保持してください
4. **ドキュメントでの説明**：アダプターのドキュメントでタイプマッピング関係を説明してください

### 7.2 モジュール開発者

1. **ユーティリティメソッドを使用**：`get_send_type_and_target_id()` などのユーティリティメソッドを使用してください
2. **ハードコーディングを避ける**：`if group_id else "private"` のようなコードを書かないでください
3. **すべてのタイプを考慮**：コードは private/group だけでなく、すべての標準タイプをサポートする必要があります
4. **柔軟な設計**：フィールドに直接アクセスするのではなく、イベントラッパーのメソッドを使用してください

### 7.3 タイプ推論

- **detail_type を優先使用**：明示的なフィールドがある場合は推論を行いません
- **推論の適切な使用**：明示的なタイプがない場合にのみ使用してください
- **優先順位に注意**：推論の優先順位を理解し、予期しない結果を避けてください

## 10. よくある質問

### Q1: 送信時に private を user に変換するのはなぜですか？

A: これは OneBot12 標準の要件です。`private` は受信時の概念であり、送信時には `user` を使用する方がセマンティクスに適しています。

### Q2: 新しいセッションタイプをサポートするには？

A: `register_custom_type()` でカスタムタイプを登録するか、標準タイプの `channel`、`guild` などを直接使用してください。

### Q3: イベントに detail_type がない場合は？

A: システムは存在する ID フィールドに基づいて自動的に推論します。優先順位は group > channel > guild > thread > user です。

### Q4: アダプターは Telegram の supergroup をどのようにマッピングしますか？

A: アダプターの変換ロジックで、`supergroup` を標準の `group` タイプにマッピングしてください。

### Q5: メールなどの特殊なプラットフォームはどのように処理しますか？

A: 汎用性のないタイプやプラットフォーム固有のタイプについては、`{platform}_raw` と `{platform}_raw_type` を使用して元データを保持し、アダプター側で処理してください。

## 11. 関連ドキュメント

**アダプター向け（マッピングと変換）**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換仕様
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名とパラメータ仕様
- [アダプター開発ガイド](../developer-guide/adapters/) - アダプター開発の完全ガイド

**モジュール向け（タイプ変換を手動で処理したくない場合）**：
- `event.reply()` を使用するだけで、タイプ変換とターゲット推論が自動的に行われます。詳細は [Event ラッパークラス解説](../developer-guide/modules/event-wrapper.md) を参照してください



### 事件转换标准

# アダプタ標準変換規格

> [!TIP]
> **このドキュメントを読むべきタイミング**：アダプタ内でプラットフォームのネイティブイベントを OneBot12 標準イベントに変換する際、必須フィールド、メッセージセグメント構造、拡張フィールド命名規則（`{platform}_` プレフィックス）、会話タイプの推論を確認する必要がある場合。不要であれば飛ばしてください。

## 1. 核心原則

1. **厳密な互換性**：すべての標準フィールドは OneBot12 規格に完全に準拠する。
2. **明確な拡張**：プラットフォーム固有の機能は `{platform}_` プレフィックスを付ける（例：yunhu_form）。
3. **データの完全性**：元のイベントデータは `{platform}_raw` フィールドに、元のイベントタイプは `{platform}_raw_type` フィールドに保持する。
4. **時間の統一**：すべてのタイムスタンプは 10 位の Unix タイムスタンプ（秒単位）に変換する。
5. **プラットフォームの統一**：`platform` 項目の命名は、ErisPulse に登録した名前/別称と一致する。

## 2. 標準フィールド要件

### 2.1 必須フィールド
| フィールド | 型 | 説明 |
|------|------|------|
| id | string | イベントの一意な識別子 |
| time | integer | Unix タイムスタンプ（秒単位） |
| type | string | イベントのタイプ |
| detail_type | string | イベントの詳細タイプ（[会話タイプ標準](session-types.md)を参照） |
| sub_type | string | イベントのサブタイプ |
| platform | string | プラットフォーム名 |
| self | object | ロボット自身の情報 |
| self.platform | string | プラットフォーム名 |
| self.user_id | string | ロボットのユーザーID |

> **OneBot12 基準**：`self.platform` / `self.user_id` とメッセージイベントの `message_id` は OneBot12 基準で定義されたフィールドであり、フレームワークは基準定義を直接採用し、独自の拡張キー（`self.account_id` は動的アカウントが user_id を取得する前に代用する限定拡張キー、§6 を参照）を導入しない。

**detail_type 規格**：
- ErisPulse 標準会話タイプを使用する（[会話タイプ標準](session-types.md)を参照）
- 対応するタイプ：`private`, `group`, `user`, `channel`, `guild`, `thread`
- アダプタは、プラットフォームのネイティブタイプを標準タイプにマッピングする。

### 2.2 メッセージイベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| message_id | string | メッセージID（OneBot12 基準必須フィールド、アダプタはイベントの最上層に生成する） |
| message | array | メッセージセグメントの配列 |
| alt_message | string | メッセージセグメントの代替テキスト |
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーのニックネーム（オプション） |

### 2.3 通知イベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーのニックネーム（オプション） |
| operator_id | string | 操作者のID（オプション） |

### 2.4 要求イベントフィールド
| フィールド | 型 | 説明 |
|------|------|------|
| user_id | string | ユーザーID |
| user_nickname | string | ユーザーのニックネーム（オプション） |
| comment | string | 要求のコメント（オプション） |
| request_id | string | 要求の識別子（**強く推奨**、同意/拒否操作に使用） |

**`request_id` フィールドの説明**：
- `request_id` は要求イベントの唯一の操作識別子であり、`Request` DSL を通じて同意/拒否操作に使用される。
- アダプタは、プラットフォームのネイティブの要求識別子をこのフィールドにマッピングする。
- プラットフォームに要求IDがない場合、アダプタはユニークな識別子（例：タイムスタンプ+ユーザーIDのハッシュ）を生成する。
- `request_id` が欠落している場合、`event.approve()` / `event.reject()` は `ValueError` をスローする。

## 3. イベント形式の例

### 3.1 メッセージイベント (message)
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
        "text": "抽奖 超级大奖"
      }
    }
  ],
  "alt_message": "抽奖 超级大奖",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  }
}
```

### 3.2 通知イベント (notice)
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

### 3.3 要求イベント (request)
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
  "comment": "请加好友",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. メッセージセグメント標準

### 4.1 標準メッセージセグメント

標準メッセージセグメントにはプラットフォームのプレフィックスを付けない。

| タイプ | 説明 | data フィールド |
|------|------|----------|
| `text` | 純テキスト | `text: str` |
| `image` | 画像 | `file`, `url: str` |
| `voice` | 音声（即時録音の音声、`audio` とは区別） | `file`, `url: str` |
| `audio` | 音楽（再生可能な音楽ファイル、`voice` とは区別） | `file`, `url: str` |
| `video` | 動画 | `file`, `url: str` |
| `file` | ファイル | `file`, `url: str`, `filename: str` |
| `mention` | @ユーザー | `user_id: str`, `user_name: str` |
| `mention_all` | @全員 | data フィールドなし |
| `reply` | 返信 | `message_id: str`, `user_id: str`（返信の元送信者、受信方向はアダプタが可能な限り記入） |
| `location` | 位置 | `latitude: float`, `longitude: float`, `title: str`（オプション）, `content: str`（オプション） |
| `face` | 表情（ErisPulse 跨プラットフォーム拡張セグメント） | `id: str` |
| `keyboard` | ボタン/インラインキーボード（ErisPulse 跨プラットフォーム拡張セグメント） | `rows: list[list[button]]`（4.1.1 参照） |

> **OneBot12 基準とのフィールドマッピング**：メディアセグメント（`image` / `voice` / `audio` / `video` / `file`）は OneBot12 基準では `file_id: str` である。本標準の `file`（送信形態の超集合：URL / 本地パス / bytes）と `url`（受信回路）は、アダプタによってプラットフォームの `file_id` リソースに双方向にマッピングされる。`face` / `keyboard` は OneBot12 基準の外の拡張セグメントである。

**メディアセグメント `file` フィールド形式**（送信方向、`image` / `audio` / `video` / `file` に共通）：

| 形態 | 例 | アダプタの要件 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/a.png` | **必須** |
| 本地ファイルパス | `/tmp/a.png`、`C:\tmp\a.png` | **必須** |
| 二進数データ | `bytes` | **必須** |
| `file://` URI / Base64 / Data URI | `file:///tmp/a.png`、`data:image/png;base64,...` | **推奨** |

> 完全なメディア送信プロトコル（形態判定順序、ファイル名推論、能力降格の段階）は
> [送信方法規格 §2.1](send-method-spec.md#21-媒体消息发送协议image--voice--video--file) を参照。

**フィールドの方向意味**：

- `file`：**送信方向**のコンテンツソース（上記の形態）；**受信方向**はアダプタが可能な限りプラットフォームで取得可能な形態を記入する
  （通常はダウンロード可能な URL、または `get_file` 類のアクションで利用可能なリソース識別子）
- `url`：受信方向のプラットフォームの回路（アダプタがプラットフォームのイベントを変換する際に可能な限り記入し、モジュールが直接取得できるようにする）；送信方向は記入しなくてもよい
- `filename`：`file` セグメントのファイル名（送信方向はオプション、欠落時はアダプタが
  [送信方法規格 §2.1.3](send-method-spec.md) の推論順序に従って生成する；受信方向は**プラットフォームの元のファイル名を記入する**）

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard ボタン/インラインキーボードセグメント（跨プラットフォーム共通）

ボタン/インラインキーボードは、Telegram / 云湖 / QQBot / Kook / Discord 等の複数のプラットフォームで対応しており、**跨プラットフォーム共通概念**であるため、標準メッセージセグメント（プラットフォームのプレフィックスなし）として扱う。アダプタは標準セグメントを
プラットフォームのネイティブ構造に変換する。プラットフォームのネイティブ拡張セグメント（例：`telegram_inline_keyboard`）はそのまま透かす。

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "选项A", "type": "callback", "data": "vote:A"},
        {"label": "官网",   "type": "link",     "data": "https://example.com"}
      ]
    ]
  }
}
```

**フィールドの説明**：

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `rows` | 二次元配列 | はい | 各サブ配列が一行のボタン |
| `rows[][].label` | str | はい | ボタンの表示テキスト |
| `rows[][].type` | str | はい | `callback`（クリックでデータを戻す）/ `link`（URL にジャンプ） |
| `rows[][].data` | str | はい | コールバックデータ（type=callback）またはジャンプアドレス（type=link） |
| `rows[][].*` | Any | いいえ | プラットフォーム特有のオプションフィールド（例：`web_app`、`menus`）、アダプタは能力に応じてマッピングまたは無視する |

**アダプタの変換参考**（完全なマッピングとインタラクティブコールバックイベントの標準は [跨プラットフォームインタラクティブコンポーネント標準](standardization-guide.md) を参照）：

| プラットフォーム | 標準セグメント → プラットフォームのネイティブ |
|------|------------------|
| Telegram | `inline_keyboard`：`[{text, callback_data \| url}]` |
| 云湖 | `buttons`：`[{label, action_type: 2=コールバック \| 1=ジャンプ, ...}]` |
| QQBot | `keyboard.content.rows`：`[{label, type: 2=コールバック \| 0=ジャンプ, data}]`（markdown メッセージ形式が必要） |
| Kook | カードの action-group モジュール |
| Discord | components：`action_row` + `buttons`（custom_id/url） |

### 4.2 プラットフォーム拡張メッセージセグメント

プラットフォーム固有のメッセージセグメントにはプラットフォームのプレフィックスを付ける：

```json
// 云湖 - フォーム
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "报名表"}}

// Telegram - ステッカー
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**拡張メッセージセグメントの要件**：
1. **data 内部のフィールドはプレフィックスを付けない**：`{"type": "yunhu_form", "data": {"form_id": "..."}}` ではなく `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **降格のソリューションを提供する**：モジュールが拡張メッセージセグメントを認識できない場合、アダプタは `alt_message` にテキストの代替を提供する
3. **ドキュメントの完全性**：各拡張メッセージセグメントは、`type`、`data` の構造、使用場面をアダプタのドキュメントで説明する必要がある

## 5. 未知イベントの処理

認識できないイベントタイプに対しては、警告イベントを生成する：
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
プラットフォーム前缀    フィールド名            完全フィールド名
────────    ───────          ──────────
yunhu       command           yunhu_command
telegram    sticker_file_id   telegram_sticker_file_id
onebot11    anonymous         onebot11_anonymous
email       subject           email_subject
```

**要件**：
- `platform` はアダプタ登録時のプラットフォーム名と完全一致する（大文字小文字を区別）
- `field_name` は `snake_case` 命名を使用
- `__` で始まる名前は禁止（Python が予約）
- 標準フィールド（例：`type`、`time`、`message` など）と同名の名前は禁止

### 6.2 メッセージセグメントタイプ命名

**ルール**：`{platform}_{segment_type}`

標準メッセージセグメントタイプ（`text`、`image`、`audio`、`video`、`mention`、`reply` など）は**プラットフォームのプレフィックスを付けない**。プラットフォーム固有のメッセージセグメントタイプのみプレフィックスを付ける。

### 6.3 原始データフィールド命名

以下のフィールド名は**予約フィールド**であり、すべてのアダプタは以下の要件を遵守する：

| 予約フィールド | 型 | 説明 |
|---------|------|------|
| `{platform}_raw` | `any` | プラットフォームの元のイベントデータの完全なコピー |
| `{platform}_raw_type` | `string` | プラットフォームの元のイベントタイプの識別子 |

**要件**：
- `{platform}_raw` は元のデータの深いコピー（参照ではなく）である必要がある
- `{platform}_raw_type` は文字列である必要がある（プラットフォームが数値型を使用している場合も文字列に変換する）
- これらのフィールドはすべてのイベントで**存在する必要がある**（取得できない場合は `null` と空文字列 `""` とする）

### 6.4 プラットフォーム特有のフィールドの例

```json
{
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 嵌套拡張フィールド

拡張フィールドは単純な値でも、ネストされたオブジェクトでもよい：

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
- トップレベルのキーにはプラットフォームのプレフィックスを付ける
- ネストされた内部のフィールドには**プラットフォームのプレフィックスを付けない**
- ネストの深さは 3 層を超えないように推奨

### 6.6 `self` フィールドの拡張

`self` オブジェクトの標準の必須フィールド（`platform`、`user_id`）は §2.1 を参照。以下は ErisPulse が拡張したオプションフィールドである：

| フィールド | 型 | 説明 |
|------|------|------|
| `self.user_name` | `string` | ロボットのニックネーム |
| `self.avatar` | `string` | ロボットのアバターのURL |
| `self.account_id` | `string` | **限定拡張キー（アカウント名の代用）**：動的に注入されたアカウントが `user_id` を取得する前に、アカウント名/アカウント識別子で代用して記入し、イベントの所属を保証する。`self.user_id` が利用可能になったら優先的に記入する。フレームワークは `account_id or user_id` の口径で両方を互換的に扱う——アカウント名の代用時は `reply()` がアカウント名マッチングで正しいアカウントにルーティングされる |

> **実行時境界：イベントは常に `self.user_id` を保持する必要がある**（バインドが確立していない期間も含む）。接続層がバインドテーブルを戻し、connect meta が到着する前に受信したイベントは、ロボットの `user_id` が取得されていない場合はアカウント名で `self.account_id` を代用して注入する（フレームワークは `account_id or user_id` の口径で解析し、アカウント名はアカウント名マッチングルーターで正しいアカウントに戻る）。取得済みの場合は優先的に `self.user_id` を記入する——フレームワークはイベントの任意の段階で「このイベントはどのアカウントから来たのか」を判断できる必要がある。欠落した場合の結果は明確である：`event.reply()` にアカウントを注入せず、アカウントが指定されていない送信は最初の有効なアカウントに降格し、複数アカウントのアダプタでは「デフォルトアカウントから発信された」と表現される。

> **Bot 状態の追跡**：アダプタは `type: "meta"` イベントを送信してフレームワークに Bot の接続状態を通知する。サポートされる `detail_type`：`connect`（オンライン）、`heartbeat`（ハートビート）、`disconnect`（オフライン）。システムはこの中から `self` フィールドの Bot 元情報を自動抽出して状態を追跡する。また、通常のイベントの `self` フィールドも自動的に Bot を発見する。[アダプタシステム API - Bot 状態管理](../api-reference/adapter-system.md)を参照。

---

## 7. 会話タイプの拡張

ErisPulse は OneBot12 標準の `private`、`group` の上に以下の会話タイプを拡張している：

| タイプ | OneBot12 標準 | ErisPulse 拡張 | 説明 |
|------|:-----------:|:------------:|------|
| `private` | ✅ | — | 1対1のプライベートチャット |
| `group` | ✅ | — | グループチャット |
| `user` | — | ✅ | ユーザータイプ（Telegram など） |
| `channel` | — | ✅ | チャンネル（放送型） |
| `guild` | — | ✅ | サーバー/コミュニティ |
| `thread` | — | ✅ | トピック/サブチャンネル |

**アダプタのカスタムタイプ拡張**：

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# アダプタ起動時に登録
register_custom_type(
    receive_type="email",      # 受信イベントの detail_type
    send_type="email",         # 送信時の対象タイプ
    id_field="email_id",       # 対応する ID フィールド名
    platform="email"           # プラットフォーム識別子
)
```

**カスタムタイプの要件**：
- アダプタの `start()` 時に登録し、`shutdown()` 時に登録解除する
- `receive_type` は標準タイプと重複しない
- `id_field` は `{対象}_id` の命名パターンに従う

> 完全な会話タイプの定義とマッピング関係は [会話タイプ標準](session-types.md) を参照。

---

## 8. モジュール開発者ガイド

### 8.1 拡張フィールドのアクセス

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # 標準フィールドのアクセス
    text = event.get_text()
    user_id = event.get_user_id()

    # プラットフォーム拡張フィールドのアクセス - 方法1: 直接 get
    yunhu_command = event.get("yunhu_command")

    # プラットフォーム拡張フィールドのアクセス - 方法2: ポイント式アクセス（Event 包装クラス）
    # event.yunhu_command

    # 原始データのアクセス
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # プラットフォームの判断
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

### 8.3 最適実践

1. **標準フィールドを優先する**：拡張フィールドが必ず存在すると仮定しない
2. **プラットフォームの判断**：拡張フィールドの存在でプラットフォームを推論するのではなく、`event.get_platform()` を使用する
3. **優雅な降格**：拡張メッセージセグメントを処理できない場合は、`alt_message` をバックアップとして使用する
4. **プレフィックスをハードコードしない**：`platform` 変数を使用して動的に結合する

```python
# ✅ 推奨
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ 推奨しない
raw_data = event.get("yunhu_raw")
```

### 8.4 要求イベントの処理

モジュール開発者は `event.approve()` と `event.reject()` を使用して要求イベントを操作できる：

```python
from ErisPulse.Core.Event import request

# フレンドリクエスト：自動で承認
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # 承認
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"{user_name} のフレンドリクエストを承認しました")
    else:
        print(f"フレンドリクエストの承認に失敗しました: {result.get('message')}")

# グループリクエスト：条件に応じて決定
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # 拒否
    result = await event.reject(comment="暫定的に新しいグループに参加しません")
```

**アダプタ経由での直接操作**（イベントハンドラ外のシナリオに適用）：

```python
from ErisPulse import adapter

# request_id で直接操作
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# 特定の Bot アカウントで操作
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# コメントを付けて
await adapter.myplatform.Request("req_abc123").accept(comment="ようこそ")
```

---

## 9. notice / request イベントの会話タイプ推論

### 9.1 問題の背景

notice イベントと request イベントの `detail_type` は**意味のサブタイプ**（例：`group_member_increase`、`friend_increase`）であり、会話タイプ（例：`group`、`private`）ではない。

```
type        detail_type                  含義            会話タイプ
────        ───────────                  ────            ────────
message     group                        グループメッセージ         group（detail_type が会話タイプ）
message     private                      プライベートメッセージ         private（detail_type が会話タイプ）
notice      group_member_increase        グループメンバー増加       group（group_id から推論）
notice      friend_increase              フレンド増加         private（user_id から推論）
request     friend                       フレンドリクエスト         private（user_id から推論）
request     group                        グループリクエスト           group（detail_type が会話タイプ）
```

### 9.2 推論ルール

`infer_receive_type()` の推論順序：

1. `detail_type` が既知の会話タイプ（`private`/`group`/`channel`/`guild`/`thread`/`user`）の場合、そのまま使用
2. `detail_type` がカスタム会話タイプの場合、そのまま使用
3. それ以外（notice/request の意味のサブタイプ）の場合、ID フィールドから推論：
   - `group_id` があれば → `"group"`
   - `channel_id` があれば → `"channel"`
   - `guild_id` があれば → `"guild"`
   - `thread_id` があれば → `"thread"`
   - `user_id` があれば → `"private"`

### 9.3 `event.reply()` の送信先推論

notice/request イベントにおける `event.reply()` の送信先は会話タイプの推論で決定される：

- グループ通知イベント（`group_id` がある）→ グループに返信
- フレンド通知イベント（`user_id` だけがある）→ ユーザーのプライベートチャットに返信

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() はグループ（group/group_789）に送信
    await event.reply("ようこそ！")

    # 管理者に通知したい場合（プライベートチャット）、送信先を明示的に指定する：
    await adapter.Send.To("user", "admin_id").Text(f"新メンバー {user_id} が {group_id} に参加しました")
```

### 9.4 アダプタ開発の推奨

notice/request イベントに正しい ID フィールドを含めるようにする：

| detail_type | 必須の ID フィールド | 推論される会話タイプ |
|-------------|-------------------|---------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend`（リクエスト） | `user_id` | `private` |
| `group`（リクエスト） | `group_id` | `group` |

---

## 10. 関連ドキュメント

**変換器を実装する際に併せて参照**：
- [会話タイプ標準](session-types.md) - 会話タイプの定義とマッピング関係
- [API レスポンス標準](api-response.md) - アダプタ API レスポンス形式の標準

**同じアダプタの送信側**：
- [送信方法規格](send-method-spec.md) - Send クラスのメソッド命名、パラメータ規格および逆変換要件
- [API アクション標準](api-action-spec.md) - OneBot12 標準 API アクションの統一インターフェース

**各プラットフォームの既知の拡張イベントとメッセージセグメントを確認**：
- [各プラットフォームの特徴ドキュメント](../platform-guide/README.md) - 各プラットフォームの特徴や既知の拡張イベント、メッセージセグメントなどを確認できるドキュメントにアクセスできます。



### API 响应标准

# ErisPulse アダプターの標準化された返却値仕様

> [!TIP]
> **この記事を読むタイミング**：アダプター内で `call_api` / Send / Request の返り値を実装する際に、返却値の構造と返却コードが ErisPulse の標準に準拠しているか確認する必要がある場合、または特定の `retcode` の意味を確認したい場合に、本記事を参照してください。必要がない場合は飛ばしてください。

## 1. 説明  
なぜこの規格があるのでしょうか？

各プラットフォームの送信インターフェースが一貫性とOneBot12との互換性を確保するため、ErisPulseアダプターはAPIレスポンス形式においてOneBot12が定義するメッセージ送信返却構造の標準を採用しています。

ただしErisPulseのプロトコルにはいくつかの特殊な定義があります:
- 1. 基本フィールドにおいて、message_idは必須ですが、OneBot12の標準にはこのフィールドはありません。
- 2. 返却内容には、{platform_name}_raw フィールドを追加する必要があります。このフィールドには、元のレスポンスデータを格納します。

## 2. 基礎レスポンス構造
すべてのアクションレスポンスには、以下の基本フィールドを含める必要があります。

| フィールド名 | データ型 | 必須 | 説明 |
|-------|---------|------|------|
| status | string | はい | 実行ステータス。"ok"または"failed"のいずれかに設定する必要があります |
| retcode | int64 | はい | 戻り値コード。OneBot12の戻り値コード規則に従います |
| data | any | はい | レスポンスデータ。成功時はリクエスト結果を含み、失敗時はnull |
| message_id | string | はい | メッセージID。メッセージを識別するためのもので、存在しない場合は空文字列 |
| message | string | はい | エラーメッセージ。成功時は空文字列 |
| {platform_name}_raw | any | いいえ | 元のレスポンスデータ |

オプションフィールド：
| フィールド名 | データ型 | 必須 | 説明 |
|-------|---------|------|------|
| echo | string | いいえ | リクエストにechoフィールドが含まれている場合、その値をそのまま返します |

## 3. 完全なフィールド仕様

### 3.1 一般的なフィールド

#### 成功時のレスポンス例
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

#### 失敗時のレスポンス例
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

### 3.2 戻り値コードの仕様

#### 0 成功（OK）
- 0: 成功（OK）

#### 1xxxx 動作リクエストエラー（Request Error）
| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 10001 | Bad Request | 無効な動作リクエスト |
| 10002 | Unsupported Action | 対応していない動作リクエスト |
| 10003 | Bad Param | 無効な動作リクエストパラメータ |
| 10004 | Unsupported Param | 対応していない動作リクエストパラメータ |
| 10005 | Unsupported Segment | 対応していないメッセージセグメントの種類 |
| 10006 | Bad Segment Data | 無効なメッセージセグメントパラメータ |
| 10007 | Unsupported Segment Data | 対応していないメッセージセグメントパラメータ |
| 10101 | Who Am I | ロボットアカウントが指定されていません |
| 10102 | Unknown Self | 知らないロボットアカウント |

#### 2xxxx 動作ハンドラーエラー（Handler Error）
| エラーコード | エラー名 | 説明 |
|-------|-------|------|
| 20001 | Bad Handler | 動作ハンドラーの実装エラー |
| 20002 | Internal Handler Error | 動作ハンドラーが実行中に例外をスローしました |

#### 3xxxx 動作実行エラー（Execution Error）
| エラーコード範囲 | エラー種別 | 説明 |
|-----------|---------|------|
| 31xxx | Database Error | データベースエラー |
| 32xxx | Filesystem Error | ファイルシステムエラー |
| 33xxx | Network Error | ネットワークエラー |
| 34xxx | Platform Error | ロボットプラットフォームエラー |
| 35xxx | Logic Error | 動作ロジックエラー |
| 36xxx | I Am Tired | 実装が作業を中止することを決定しました |

#### 保留エラーセグメント
- 4xxxx、5xxxx: 保留セグメント、使用しないでください
- 6xxxx～9xxxx: 他のエラーセグメント、実装が独自に使用するためのものです

## 4. 実装要件
1. すべてのレスポンスは、status、retcode、data、message フィールドを含む必要があります。
2. リクエストに非空の echo フィールドが含まれている場合、レスポンスには同じ値の echo フィールドが含まれている必要があります。
3. 戻り値コードは OneBot12 規格に厳密に従う必要があります。
4. エラーメッセージ(message)は人間に読みやすい説明である必要があります。

### 4.1 レスポンス構築ヘルパー：`make_response` / `make_error`

アダプタは、`BaseAdapter` 上の 2 つのヘルパーを使用して標準レスポンスを一貫して構築します。dict を手動で記述する必要はありません。

```python
# 成功（send / call_api / _do_accept など、すべての標準レスポンスを返す位置）
return self.make_response(
    data=result,                    # レスポンスデータ
    message_id=result.get("message_id", ""),
    raw=result,                     # プラットフォームの元のレスポンス → 自動的に {platform}_raw フィールドに追加
)

# 失敗（status は固定で "failed"）
return self.make_error(
    retcode=34100,                  # デフォルトは 34600（SDK Failure）；プラットフォームエラーは独自の 34xxx を渡す
    message="プラットフォームのリスク管理が拒否しました",
    raw=response,
)
```

| ヘルパー | シグネチャ | 意味 |
|------|------|------|
| `make_response` | `(*, status="ok", retcode=0, data=None, message_id="", message="", raw=None)` | 標準構造に従ってレスポンスを構築します。`raw` が `None` でない場合、自動的に `{platform}_raw` キーを追加します（プラットフォーム名は `self._platform` から取得） |
| `make_error` | `(retcode=34600, message="", raw=None)` | `make_response(status="failed", ...)` のショートカットです |

> 手動で等価な dict を記述することも合法です（構造が一致していれば）。ヘルパーの価値は、`{platform}_raw` のプラットフォーム名の自動連結と、フィールドの漏れがないことです。

## 5. 拡張仕様

ErisPulse は OneBot12 標準の返却構造に以下の拡張を行っています。

### 5.1 `message_id` 必須フィールド

OneBot12 標準では `message_id` は `data` オブジェクト内にあり、必須ではありません。ErisPulse ではこれをトップレベルの**必須**フィールドに昇格しています：

- `message_id` を取得できない場合は空文字列 `""` に設定する
- `message_id` が常に存在することを保証し、モジュールは null チェックを行う必要がない

> **両側を区別すること**：本節のトップレベル昇格は**アクション応答**（出力）にのみ適用されます。入力 message **イベント**の `message_id` は OneBot12 基準のトップレベル必須フィールドです。詳細は[イベント変換標準](event-conversion.md)を参照してください。

### 5.2 `{platform}_raw` 原始応答フィールド

返却値には、プラットフォームの原始応答データの完全なコピーを格納する `{platform}_raw` フィールドを含める必要があります：

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
- `{platform}_raw` は原始応答の深コピーであり、参照ではない
- `platform` はアダプタ登録時のプラットフォーム名と完全一致（大文字小文字を区別）
- 原始応答のエラーメッセージも保持し、デバッグに利用できるようにする

### 5.3 フレームワーク拡張返却コード（34xxx プラットフォームエラーセグメントの下3桁カスタム）

OneBot12 規格では、実装者が `3xxxx` の下3桁をカスタムに使用できます。`34xxx` の意味は **Platform Error**（ロボットプラットフォームエラー、例えばプラットフォーム制限により失敗した場合）です。`34xxx` 内部では、役割に応じて以下の層に分けて使用します：

| 下3桁セグメント | 所属 | 用途 |
|---------|------|------|
| `340xx` | アダプタ実装 | リクエスト操作族（Request Not Found / Already Handled / Not Supported / Permission Denied、request-action-spec §7 参照） |
| `341xx`～`345xx` | アダプタ実装 | プラットフォーム側の権限 / リスク管理 / アカウント制限等のエラー（実装者が下3桁を独自に定義し、原始エラーは `{platform}_raw` に格納） |
| `346xx` | **ErisPulse フレームワーク（予約済み）** | フレームワーク自身によるブロックと一般的な失敗、アダプタ/モジュールは使用しない |
| `347xx`～`349xx` | アダプタ実装 | その他のプラットフォーム実行エラー |

ErisPulse フレームワークで現在使用している `346xx` エラーコードは以下の通りです：

| エラーコード | エラーネーム | 説明 |
|-------|-------|------|
| 34600 | SDK Failure | フレームワークの一般的な失敗（`make_error()` のデフォルト返却コード） |
| 34601 | Action Denied | 出力アクションがスコープ `scope.actions` により禁止されているため、呼び出しは行われず、直接この応答を返す |

> **役割の区別**：`34601` は**フレームワークが呼び出し前にブロック**した場合（モジュールはそもそもアクションを発行する資格がない）です。一方、`34004` / `34xxx` プラットフォームコードは**アクションは発行されたがプラットフォームが拒否**した場合（Bot に権限がない、リスク管理対象など）です。モジュールが権限問題を判断する際には、この2つを同時にチェックする必要があります：まず `34601`（モジュール自身が scope で禁止されているか）、次に `34xxx`（プラットフォーム側の制限）を確認します。

返却構造は §2 の標準失敗応答に準拠します：

```json
{
    "status": "failed",
    "retcode": 34601,
    "data": null,
    "message_id": "",
    "message": "action 'send' denied by scope.actions"
}
```

### 5.4 アダプタ実装チェックリスト

- [ ] `status`, `retcode`, `data`, `message_id`, `message` フィールドを含む
- [ ] 返却コードは OneBot12 規格に準拠する（§3.2 参照）
- [ ] `message_id` が常に存在する（取得できない場合は空文字列）
- [ ] `{platform}_raw` にプラットフォームの原始応答データを含む

## 6. 注意事項
- 3xxxxエラーコードについては、下位3桁は実装側で独自に定義可能
- 予約エラーセグメント（4xxxx、5xxxx）の使用を避けること
- **`34600` / `34601` は ErisPulse フレームワークが予約するコード**（§5.3参照）であり、アダプタ/モジュールは使用しないこと
- エラーメッセージは簡潔かつ明瞭にし、デバッグに役立つようにすること

---

## 次のステップ

- **各DSLの戻り値に対応する照会**：[APIアクション標準](api-action-spec.md)（標準アクションのdataフィールド）、[リクエスト操作規格](request-action-spec.md)（リクエスト操作の34001-34004拡張）、[送信メソッド規格](send-method-spec.md)（送信失敗時の降格意味）
- **権限関連の失敗のトラブルシューティング**：まず`34601`（モジュールがscopeによって禁止されている、フレームワークが呼び出し前にブロックする、§5.3を参照）、次に`34xxx`（アクションは発行されたが、プラットフォーム側で拒否された）を確認する



### 发送方法规范

# ErisPulse 送信メソッド規格

> [!TIP]
> **このドキュメントを読むべきタイミング**：アダプターで Send クラスを実装する際、メソッド命名、メディアパラメータ（URL/パス/bytes）のサポート形態、`Raw_ob12` の逆変換、転送メッセージのマージ機能を本文と照らし合わせてください。不要であれば飛ばしてください。

本文は、ErisPulse アダプターにおける Send クラスの送信メソッドの命名規則、パラメータ規則、逆変換要件を定義します。

## 0. キーワードの約束

本文の **必須（MUST）**、**推奨（SHOULD）**、**任意（MAY）** は、RFC 2119 に従い以下の意味で解釈されます：

| キーワード | 意味 | 違反時の影響 |
|--------|------|---------|
| **必須** | 強制要件。フレームワークの動作やクロスプラットフォームの一貫性に依存 | アダプターは規格に準拠していないと見なし、モジュールコードが動作しない可能性がある |
| **推奨** | 強く推奨。十分な理由がない限り、遵守すべき | 違背する場合は、アダプターのドキュメントに理由と代替動作を明記する |
| **任意** | オプション。プラットフォームの能力に応じて決定 | 無 |

## 1. 標準メソッド命名

すべての送信メソッドは **大文字キャメルケース（PascalCase）** を使用し、先頭文字は大文字です。

### 1.1 標準送信メソッド

| メソッド名 | 説明 | パラメータ型 | 実装要件 |
|-------|------|---------|---------|
| `Text` | テキストメッセージを送信 | `str` | 必須 |
| `Image` | 画像を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み、§6.4参照） |
| `Voice` | 音声を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み；プラットフォームが音声をサポートしない場合は§2.1.5に従い降格） |
| `Video` | 動画を送信 | `str` \| `bytes` | 必須（基底クラスに既に実装済み；プラットフォームが動画をサポートしない場合は§2.1.5に従い降格） |
| `File` | ファイルを送信 | `str` \| `bytes`、`filename: str \| None = None` | 必須（基底クラスに既に実装済み） |
| `Location` | 位置情報を送信 | `float` (latitude/longitude)、`title: str = ""`、`content: str = ""` | 必須（基底クラスに既に実装済み） |
| `At` | ユーザー/グループを@する | `str` (user_id) | 修飾メソッド、必要に応じて |
| `Face` | 表情を送信 | `str` (emoji) | 任意 |
| `Reply` | メッセージに返信する | `str` (message_id) | 修飾メソッド、必要に応じて |
| `Forward` | メッセージを転送する | `str` (message_id) | 任意 |
| `Markdown` | Markdownメッセージを送信 | `str` | 任意 |
| `HTML` | HTMLメッセージを送信 | `str` | 任意 |
| `Card` | カードメッセージを送信 | `dict` | 任意 |

> 標準メソッド（`Text`/`Image`/`Voice`/`Video`/`File`/`Location`）は、基底クラス `SendDSL` に内蔵されており、デフォルトで `Raw_ob12` に委譲されるため、アダプターはこれらのメソッドを再実装しなくても型シグネチャを獲得できる。プラットフォームに特別なロジックが必要な場合にのみ、個々のメソッドをオーバーライドする（§6.4参照）。

### 1.2 チェーン修飾メソッド

| メソッド名 | 説明 | パラメータ型 |
|-------|------|---------|
| `At` | ユーザーを@する（複数回呼び出し可） | `str` (user_id) |
| `AtAll` | 全員を@する | 無 |
| `Reply` | メッセージに返信する | `str` (message_id) |

### 1.3 プロトコルメソッド

| メソッド名 | 説明 | 必須か |
|-------|------|---------|
| `Raw_ob12` | OneBot12形式のメッセージセグメントを送信 | 必須 |

**`Raw_ob12` は必須実装のメソッド**です。これはアダプターの主要な責任の一つであり、OneBot12標準メッセージセグメントを受け取り、それをプラットフォームのネイティブAPI呼び出しに変換する必要があります。`Raw_ob12` はOneBot12 → プラットフォームの逆変換（统一入口）であり、モジュールがプラットフォーム固有のメソッドに依存せず、標準メッセージセグメントを使って直接メッセージを送信できるようにします。

**`Raw_ob12` をオーバーライドしない場合の動作**：基底クラスのデフォルト実装は **errorレベル**のログを記録し、標準エラー応答形式（`status: "failed"`, `retcode: 10002`）を返し、アダプター開発者がこのメソッドを実装する必要があることを示します。

### 1.4 推奨の拡張命名規約

アダプターがOneBot12形式以外の生データ（プラットフォーム固有のJSON、XMLなど）を送信する必要がある場合、以下の命名規約を推奨します：

| 推奨メソッド名 | 説明 |
|-----------|------|
| `Raw_json` | 任意のJSONデータを送信 |
| `Raw_xml` | 任意のXMLデータを送信 |

**注意**：これらのメソッドは**基底クラスに提供されたデフォルトメソッドではなく、強制実装も要求されていない**。これらは命名規約としてのみ提供され、アダプターは必要に応じて独自に定義する。これらの形式をサポートしない場合は定義する必要がない。

**メッセージビルダー（MessageBuilder）**：ErisPulseは`MessageBuilder`というツールクラスを提供し、OneBot12メッセージセグメントリストを簡単に構築できるようにし、`Raw_ob12`と併用できる。詳しくは[MessageBuilder 詳解](../advanced/message-builder.md)を参照してください。

## 2. パラメータ規格詳細

### 2.1 メディア送信プロトコル（`Image` / `Voice` / `Video` / `File`）

本節はメディア送信の**統一プロトコル標準**です：モジュールは同一のコードで4つのメディアメソッドを呼び出し、アダプターは`file`パラメータの各種形態をプラットフォームのネイティブアップロード/送信動作に変換する必要があります。

#### 2.1.1 `file` パラメータの合法な形態

| 形態 | 例 | アダプターの要件 |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **必須**で受け入れる |
| 本地ファイルパス | `/path/to/file.jpg`、`C:\path\to\file.jpg` | **必須**で受け入れる |
| 二進データ | `b"\x89PNG..."` | **必須**で受け入れる |
| `file://` URI | `file:///path/to/file.jpg` | **推奨**で受け入れる（ローカルパスに転送して処理） |
| Base64文字列 / Data URI | `iVBORw0KGgo=...`、`data:image/png;base64,...` | **推奨**で受け入れる（OneBot12エコシステムの慣例に準拠） |

> アダプターは**3つの必須形態**で一貫した動作をしなければならない—モジュールがURL、パス、またはbytesを渡しても、受け取るメッセージは同一である。プラットフォームが外部URLを直接使用できない場合（プラットフォームのAPIが外部URLをサポートしない）、アダプターがダウンロード/読み取り後にアップロードする。**モジュールに再試行の形態変更を要求してはならない**。

#### 2.1.2 形態判定順序

アダプターがメディアパラメータの処理を実装する際、**推奨される判定順序**は以下の通りです：

1. `bytes`型 → 直接アップロード
2. 文字列が `http://` / `https://` で始まる → URLとして処理（直接参照またはダウンロード後にアップロード、プラットフォームの能力に応じて）
3. 文字列が `file://` で始まる → プレフィックスを剥がしてローカルパスとして処理
4. その他の文字列 → ローカルパスとして処理（存在すれば読み取りアップロード；存在しない場合は標準エラー応答を返す）

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """形態判定と正規化（例）"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # プラットフォームがURLを参照できない場合にダウンロード
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # 本地パス
        return f.read()
```

#### 2.1.3 `File`のファイル名の意味

`File`メソッドのシグネチャ：`File(file, filename=None)`（`filename`はオプションパラメータ、基底クラスに既に実装済み）。

ファイル名の**推定順序**（アダプターが明示的な`filename`を提供しない場合にこの順序で生成）：

1. 明示的な`filename`パラメータ（最高優先）
2. URLのbasename（例：`https://host/a/b/report.pdf` → `report.pdf`、クエリ文字列を剥がす）
3. 本地パスのbasename（例：`/tmp/data/backup.zip` → `backup.zip`）
4. プラットフォームがデフォルトで生成（例：`file_{timestamp}`；**推奨**は実際の拡張子を保持する—拡張子はプラットフォーム側のタイプ識別とプレビュー動作に影響する）

> `Image` / `Voice` / `Video`も**`filename`を受け入れる**（メッセージセグメント`data.filename`を通じて渡される）が、`File`のファイル名だけがクロスプラットフォームの意味保証がある。

#### 2.1.4 プラットフォーム制限の声明義務

各プラットフォームは、メディアのサイズ上限、形式（MIME）、時長（音声/動画）などの制約が異なる。アダプターは**推奨**：

- アダプターのドキュメントにサポートするメディア形式と制限範囲を声明する
- 超限または非サポートの入力を標準エラー応答（`status: "failed"`；`retcode`は`10002`またはプラットフォーム固有のエラーコード、`message`で原因を説明）を返す。**例外をスローしてモジュールのロジックを中断してはならない**

#### 2.1.5 機能降格の段階

プラットフォームがメディア**形式**をサポートしない場合、以下の段階で降格する（総則「機能降格はエラーを出さない」に従う）：

| 情報 | 降格動作 |
|------|---------|
| `Voice`が音声メッセージをサポートしない | **推奨**は`File`（またはプラットフォームに近縁な形態）で送信；表現できない場合は`retcode=10002`を返す |
| `Video`が動画メッセージをサポートしない | 同上 |
| メディア形式が完全にサポートされていない（ファイル機能がない） | `retcode=10002`を返し、`message`に非サポートのデータ形式を明記する |
| 形態がサポートされていない（例：base64を処理できない） | `retcode=10002`を返し、`message`にモジュールにURL/bytesを使用するよう提示する可能性がある |

**禁止される動作**：静かに破棄（返却なし）、例外をスロー、モジュールにプラットフォーム分岐処理を書かせる。

### 2.2 @ユーザーのパラメータ規格

**メソッド：** `At`（修飾メソッド）

**パラメータ：** `user_id` (`str`)

**要件：**
- `user_id` は文字列型のユーザー識別子であるべき
- 各プラットフォームの `user_id` 形式は異なる可能性がある（数字、UUID、文字列など）
- アダプターは `user_id` をプラットフォーム固有の形式に変換する責任がある
- 実際の送信メソッドの呼び出しは最後の位置に置くこと

**例：**
```python
# 単一の@ユーザー
Send.To("group", "g123").At("123456").Text("你好")

# 複数の@ユーザー（チェーン呼び出し）
send.To("group", "g123").At("123456").At("789012").Text("大家好")
```

### 2.3 返信メッセージのパラメータ規格

**メソッド：** `Reply`（修飾メソッド）

**パラメータ：** `message_id` (`str`)

**要件：**
- `message_id` は文字列型のメッセージ識別子であるべき
- 以前に受信したメッセージのIDであるべき
- 一部のプラットフォームは返信機能をサポートしない可能性があるため、適切に降格する

**例：**
```python
send.To("group", "g123").Reply("msg_123456").Text("收到")
```

### 2.4 合併転送機能（`MergeForward`、オプション）

`MergeForward(nodes)` は**オプションの機能メソッド**です：複数の内容を「合併転送 / フルテキスト折りたたみ」形式で送信し、アダプターはプラットフォームの能力に応じて最適な表示方法を決定します。§1.1の`Forward(from_chat_id, message_id)`（既存メッセージの転送）とは意味が異なり、両者は併存します。

> **標準の背景**：OneBot12のコア標準にはnodeメッセージセグメントも、合併転送APIもありません。"メッセージノード"はOneBot v11エコシステム（go-cqhttp拡張）の実装層の概念であり、v12ではこの種のプラットフォーム固有能力を拡張メカニズムに委ねました。ErisPulseの実装方法は拡張メカニズムの同等物です：**標準メッセージセグメントを追加せず、オプション機能メソッド + `list_sends`ランタイム検出**—`MergeForward`を実装したアダプターは自動的に機能を獲得し、実装していない場合は呼び出し元が普通のテキストに自動的に降格し、モジュールは変更なしです。

**メソッドのシグネチャ：**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    合併転送 / フルテキスト折りたたみメッセージを送信する

    :param nodes: 合併転送ノードの配列（go-cqhttp拡張のOneBot v11ノード形式）：
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # 表示用の送信者ID
                    "nickname": "MyBot",     # 表示用の送信者ニックネーム
                    "content": [            # メッセージセグメントの配列、現在はtextセグメント
                        {"type": "text", "data": {"text": "【1/3】タイトル\n本文…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task、await後に標準応答形式を返す
    """
```

**実装要件：**

1. **プラットフォームに原生の合併転送がある**（OneBot11系）：**必須**でプロトコル専用エンドポイント（`send_group_forward_msg` / `send_private_forward_msg`）を呼び出す—NapCatなどの実装は`send_msg`に含まれるnodeセグメントを拒否する（retcode 1400）；専用エンドポイントが失敗した場合は**`send_msg`にnodeセグメントを直接転送して回復する**。
2. **プラットフォームに原生の転送機能はないが、富文本がある**（云湖 / Telegram / Kook / Discord / Matrixなど）：**推奨**でノードをプラットフォームの富文本折りたたみ形態（HTML折りたたみカード / Card / Embed / blockquoteリスト）にレンダリングする。スタイルの参考と各アダプターのタスクリストは`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照。
3. **両方ない**：**実装しない**（node辞書を純粋なテキストとして発信してはならない）—実装していない場合は`list_sends`に`MergeForward`が含まれず、呼び出し元は自動的に普通のテキストに降格する。
4. **失敗の意味**：標準エラー応答（`status: "failed"`）を返すか、例外をスローしても構わない。呼び出し元は普通のテキスト送信に回復し、内容は失われない。
5. **`MergeForward`内で`Raw_ob12`を再び呼び出して同じnodesを送信してはならない**（OneBot11の`Raw_ob12`はnodeセグメントの自動ルーティングを内蔵しており、循環する）。
6. **出力nodeセグメントの解析**（全アダプターの約束）：各アダプターの`Raw_ob12`のセグメント配分は`node`セグメントを登録するべき—純粋なnodeリストは自動的に本アダプターの合併転送表示にルーティングされる（`MergeForward`があるプラットフォームでは直接呼び出すのと同等；`MergeForward`がないプラットフォームでは各ノードのテキストを「ニックネーム: 本文」として1行ずつ**原文出力**）。混合リスト中のnodeセグメントのテキストは本文に統合される。どのアダプターもnodeセグメントを静かに破棄してはならない。

**プラットフォーム実装形態**（`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照）：

- 原生エンドポイント：OneBot11、SnowLuma（3段階の降格：`send_group/private_forward_msg`専用エンドポイント → `upload_forward_msg`からresidを取得してforwardセグメントを送信 → nodeセグメントを直接送信；SnowLuma APIはNapCatと完全に互換性があり、アダプターはNapCatバックエンドに直接接続できる）
- 折りたたみHTML `<details>` カード：云湖（bot/ユーザー協定）、Email、Sandbox、Allons(Ideaura)
- ホワイトリストHTML / 引用ブロック：Telegram（`<b>`+`<blockquote>`）、Matrix（blockquoteバリエーション、whitelistでdetails/インラインスタイルを除去）
- プラットフォームカード：Kook（Card header+section）、Discord（Embed fields）
- 公式Markdown引用リスト：QQBot（公式mdに折りたたみ構文がないため、サーバ側で無効なタグを拒否する40034011）
- 実装しない（nodeセグメントを原文出力して降格）：OneBot12（標準にnodeセグメントがない）、WeCom、Terminal、Webhook、WechatMp

**呼び出し元の検出例：**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergeForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> 参考実装：`ErisPulse-OneBot11Adapter`（専用エンドポイント → `send_msg`の降格）；レンダリングテンプレートと各アダプターのタスクリストは`SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`を参照。

## 3. プラットフォーム固有メソッド命名

Sendクラスに直接プラットフォームプレフィックスメソッドを追加することは**推奨されない**。一般的なメソッド名または`Raw_{プロトコル}`メソッドを使用することを推奨。

**推奨されない：**
```python
def YunhuForm(self, form_id: str):  # ❌ 推奨されない
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ 推奨されない
    pass
```

**推奨：**
```python
def Form(self, form_id: str):  # ✅ 一般的なメソッド名
    pass

def Sticker(self, sticker_id: str):  # ✅ 一般的なメソッド名
    pass

def Raw_ob12(self, message):  # ✅ OneBot12形式を送信
    pass
```

**拡張メソッド要件**：
- メソッド名はPascalCaseを使用し、プラットフォームプレフィックスを付けない
- 必須で`asyncio.Task`オブジェクトを返す
- 完全な型注釈とドキュメント文字列を提供する
- パラメータ設計は標準メソッドのスタイルとできるだけ一致させる

## 4. パラメータ命名規格

| パラメータ名 | 説明 | 型 |
|-------|------|------|
| `text` | テキスト内容 | `str` |
| `file` | メディア内容（URL / パス / 二進、§2.1.1参照） | `str` / `bytes` |
| `filename` | ファイル名（`File`はオプション、§2.1.3参照） | `str` / `None` |
| `user_id` | ユーザーID | `str` / `int` |
| `group_id` | グループID | `str` / `int` |
| `message_id` | メッセージID | `str` |
| `data` | データオブジェクト（例：カードデータ） | `dict` |

## 5. 戻り値規格

- **送信メソッド**（例：`Text`, `Image`）：**必須**で`asyncio.Task`オブジェクトを返す
- **修飾メソッド**（例：`At`, `Reply`, `AtAll`）：**必須**で`self`を返してチェーン呼び出しを可能にする

---

## 6. 逆変換規格（OneBot12 → プラットフォーム）

アダプターは、プラットフォームのネイティブイベントをOneBot12形式に変換する（正変換）だけでなく、**OneBot12メッセージセグメントをプラットフォームのネイティブAPI呼び出しに変換する**（逆変換）能力も**必須**です。逆変換の統一入口は`Raw_ob12`メソッドです。

### 6.1 変換モデル

```
正変換（受信方向）                逆変換（送信方向）
─────────────────                ─────────────────
プラットフォームネイティブイベント                       OneBot12メッセージセグメントリスト
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12標準イベント（含{platform}_raw）             プラットフォームネイティブAPI呼び出し
（返却は標準応答形式）
```

**コアの対称性**：正変換は原始データを`{platform}_raw`に保持し、逆変換はOneBot12標準形式を受け取り、プラットフォーム呼び出しに還元する。

### 6.2 `Raw_ob12`実装規格

`Raw_ob12`はOneBot12標準メッセージセグメントリストを受け取り、それをプラットフォームのネイティブAPI呼び出しに変換しなければならない。

**メソッドのシグネチャ：**

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    OneBot12標準メッセージセグメントを送信する

    :param message_segments: OneBot12メッセージセグメントリスト
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task、await後に標準応答形式を返す
    """
```

**実装要件：**

1. **すべての標準メッセージセグメントタイプを処理しなければならない**：少なくとも`text`、`image`、`audio`、`video`、`file`、`mention`、`reply`をサポートする
2. **プラットフォーム拡張メッセージセグメントを処理しなければならない**：`{platform}_xxx`形式のメッセージセグメントは、プラットフォームに対応するネイティブ呼び出しに変換する
3. **標準応答形式を返さなければならない**：[API応答標準](api-response.md)に従う
4. **サポートしないメッセージセグメントは警告を記録してスキップし、例外をスローしてメッセージ全体の送信失敗を起こしてはならない**

### 6.3 メッセージセグメント変換ルール

#### 6.3.1 標準メッセージセグメント変換

アダプターは以下の標準メッセージセグメントの変換を実装しなければならない：

| OneBot12メッセージセグメント | 変換要件 |
|----------------|---------|
| `text` | `data.text`をそのまま使用 |
| `image` | `data.file`を§2.1メディアプロトコルに従って処理（3つの必須形態 + 判定順序） |
| `audio` | `image`と同じ処理ロジック |
| `video` | `image`と同じ処理ロジック |
| `file` | `image`と同じ処理ロジック；ファイル名は§2.1.3の推定順序に従って`data.filename`を処理 |
| `mention` | プラットフォームの@ユーザー機構に変換する（例：Telegramの`entities`、云湖の`at_uid`） |
| `reply` | プラットフォームの返信引用機構に変換する |
| `face` | プラットフォームの表情送信機構に変換する、サポートしない場合はスキップ |
| `location` | プラットフォームの位置送信機構に変換する、サポートしない場合はスキップ |

#### 6.3.2 プラットフォーム拡張メッセージセグメント変換

プラットフォームプレフィックス付きのメッセージセグメントは、アダプターが認識して変換するべきです：

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """OneBot12メッセージセグメントをプラットフォームネイティブ形式に変換する"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # プラットフォーム拡張メッセージセグメント → プラットフォームネイティブ呼び出し
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # 標準メッセージセグメント → プラットフォーム同等操作
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # 未知のメッセージセグメント → 警告を記録してスキップ
            logger.warning(f"サポートしないメッセージセグメントタイプ: {seg_type}")
```

#### 6.3.3 複合メッセージセグメント処理

1つのメッセージには複数のメッセージセグメントが含まれる可能性があり、アダプターは複合メッセージを正しく処理する必要があります：

```python
# モジュールがテキスト+画像+@ユーザーのメッセージを送信
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "你好"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**処理戦略**：
- **優先して結合**：プラットフォームが1つのメッセージにテキスト、画像、@などを同時に含められる場合、結合して送信する
- **次善として分割**：プラットフォームが結合をサポートしない場合、順序に従って複数のメッセージに分割して送信する
- **順序の保持**：メッセージセグメントの送信順序はリストの順序と一致する

### 6.4 `Raw_ob12` と標準メソッドの関係

アダプターの標準送信メソッド（`Text`、`Image`など）は**`SendDSL`基底クラスに既に実装されており、デフォルトで`Raw_ob12`に委譲される**ため、アダプターのサブクラスは再実装する必要はない：

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """コア実装：OneBot12メッセージセグメント → プラットフォームAPI（必須実装）"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File/Locationは基底クラスから継承され、Raw_ob12に自動的に委譲される
    # プラットフォーム固有のロジックが必要な場合、メソッドをオーバーライドする：
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**利点**：
- 変換ロジックは`Raw_ob12`の1か所に集中し、重複コードを減らす
- 標準メソッドと`Raw_ob12`の動作は完全に一致する
- モジュールが`Text()`を使うか`Raw_ob12()`を使うかに関わらず、同じ結果を得られる
- 基底クラスが型シグネチャを提供し、IDEは標準メソッドの補完ができる

### 6.5 実装例

```python
class YunhuSend(SendDSL):
    """云湖プラットフォームのSend実装"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12メッセージセグメント → 云湖API呼び出し"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """実際の送信ロジック"""
        # 1. 修飾子の状態を解析
        at_users = self._at_users or []
        reply_to = self._reply_to
        at_all = self._at_all
        
        # 2. メッセージセグメントを変換
        yunhu_elements = []
        for seg in segments:
            seg_type = seg["type"]
            seg_data = seg["data"]
            
            if seg_type == "text":
                yunhu_elements.append({"type": "text", "content": seg_data["text"]})
            elif seg_type == "image":
                yunhu_elements.append({"type": "image", "url": seg_data["file"]})
            elif seg_type == "mention":
                at_users.append(seg_data["user_id"])
            elif seg_type == "reply":
                reply_to = seg_data["message_id"]
            elif seg_type == "yunhu_form":
                # プラットフォーム拡張メッセージセグメント
                yunhu_elements.append({"type": "form", "form_id": seg_data["form_id"]})
            else:
                logger.warning(f"云湖でサポートしていないメッセージセグメント: {seg_type}")
        
        # 3. 云湖APIを呼び出す
        response = await self._call_yunhu_api(yunhu_elements, at_users, reply_to, at_all)
        
        # 4. 標準応答形式を返す
        return {
            "status": "ok" if response["code"] == 0 else "failed",
            "retcode": response["code"],
            "data": {"message_id": response.get("msg_id", ""), "time": int(time.time())},
            "message_id": response.get("msg_id", ""),
            "message": "",
            "yunhu_raw": response
        }
```

---

## 7. メソッド発見

モジュール開発者は、アダプターがサポートする送信メソッドをAPIで照会できる（**モジュールにプラットフォームのメソッドリストをハードコーディングしてはならない**—各アダプターの拡張メソッドはバージョンの進化に伴い変化するため、ランタイムでの発見が基準となる）：

```python
from ErisPulse import adapter

# すべての送信メソッドをリストアップ
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# メソッドの詳細を照会
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "云湖フォームを送信"
# }
```

---

## 9. アダプター開発の注意事項

`BaseAdapter`、`Send`、`Request`の`__init__`を正しくオーバーライドする方法については、[アダプター開発入門 - `__init__`の注意事項](../developer-guide/adapters/getting-started.md#init-注意事项)を参照してください。

---

---

## 10. アダプター実装チェックリスト

### 送信メソッド
- [ ] 標準メソッド（`Text`, `Image`など）は実装済み
- [ ] 戻り値はすべて`asyncio.Task`
- [ ] 修飾メソッド（`At`, `Reply`, `AtAll`）は`self`を返す
- [ ] プラットフォーム拡張メソッドはPascalCaseを使用し、プラットフォームプレフィックスを付けない
- [ ] すべてのメソッドは完全な型注釈とドキュメント文字列を備えている

### メディア送信プロトコル
- [ ] `file`パラメータの**必須形態**（HTTP(S) URL / 本地パス / `bytes`、§2.1.1参照）はすべてサポート
- [ ] 形態判定順序は§2.1.2（bytes → URL → `file://` → パス）に従っている
- [ ] `File`のファイル名推定順序は§2.1.3（明示的な`filename` > URLのbasename > パスのbasename > プラットフォームデフォルト）に従っている
- [ ] プラットフォームのメディア制限（サイズ / MIME / 時長）はアダプターのドキュメントに声明されている（§2.1.4）
- [ ] メディア形式がサポートされていない場合は、§2.1.5の降格段階に従って処理する（近縁な形式に降格するか、`retcode=10002`を返す）、例外をスローしたり、静かに破棄したりしない

### 合併転送（オプション、§2.4参照）
- [ ] プラットフォームに原生の合併転送がある場合、`MergeForward`はプロトコル専用エンドポイントを経由し、失敗した場合は`send_msg`に回復する（OneBot11系）
- [ ] プラットフォームに原生の転送機能はないが、富文本がある場合、`MergeForward`はプラットフォームの折りたたみ形態（HTMLカード / Card / Embed / blockquote）にレンダリングする
- [ ] 両方ない場合は**`MergeForward`を実装しない**、node辞書を純粋なテキストとして発信してはならない
- [ ] `MergeForward`の中で`Raw_ob12`を再呼び出さない（OneBot11の`Raw_ob12`はnodeセグメントの自動ルーティングを内蔵しており、循環する）

### 逆変換
- [ ] `Raw_ob12`は**実装済み**（必須、スキップしてはならない）
- [ ] `Raw_ob12`はすべての標準メッセージセグメント（`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`）を処理できる
- [ ] `Raw_ob12`はプラットフォーム拡張メッセージセグメント（`{platform}_xxx`形式）を処理できる
- [ ] 標準送信メソッド（`Text`, `Image`など）は`Raw_ob12`に委譲しており、個別の変換ロジックを独立して実装していない
- [ ] サポートしていないメッセージセグメントは警告を記録してスキップし、例外をスローしてはならない
- [ ] 複合メッセージセグメントは正しく処理する（結合するか、順序に従って分割する）

---

## 11. メッセージビルダー（MessageBuilder）—アダプター側の注意事項

`MessageBuilder`はErisPulseが提供するOneBot12メッセージセグメント構築ツールであり、**モジュール側**がメッセージを構築するために使用する：チェーン呼び出し（または静的高速構築）により、最終的にOneBot12メッセージセグメントリスト`[{"type": ..., "data": ...}]`を生成し、`Raw_ob12`に直接渡される。

**アダプター側はこれを知るだけでよい**：`Raw_ob12`が受け取るのはこの生成物—`MessageBuilder`かリテラルかに関わらず、`Raw_ob12`は§6.2のセグメント分離ロジックに従って処理するだけで、`MessageBuilder`か手書きかを意識する必要はない。

> 完全な使い方（二重モードメカニズム、すべてのメッセージセグメントメソッド、`copy()` / `clear()`ツールメソッドと例）は[MessageBuilder 詳解](../advanced/message-builder.md)を参照してください。本文では繰り返しません。

---

## 12. 関連ドキュメント

**送信戻り値を実装する際の対応**：
- [API応答標準](api-response.md) - アダプターAPIの応答形式標準

**同一アダプターの他の側面**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換規格、拡張命名とメッセージセグメント標準
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係
- [リクエスト操作規格](request-action-spec.md) - リクエストイベントのフィールド要件、Request DSL（approve/reject）とアダプター実装要件



### 请求操作规范

# ErisPulse リクエスト操作規格

> [!TIP]
> **このドキュメントを読むタイミング**：アダプタが友人リクエスト/グループ招待（リクエストイベントの変換、`accept`/`reject`の実装、異質なエンドポイントのリクエストタイプコンテキスト保持）を処理する必要がある場合、またはモジュールで `event.approve()` / `event.reject()` を使用してリクエストを承認する場合に本文を参照してください。必要がない場合はスキップしてください。

本文書では、ErisPulseアダプタにおけるリクエストイベント操作の標準化された規格を定義します。これには、リクエストイベントのフィールド要件、Request DSLの使用方法、およびアダプタ実装要件が含まれます。

## 1. 概要

リクエストイベント（`type: "request"`）は、OneBot12標準で定義された特別なイベントタイプで、Botが決定を下す必要があるリクエスト（例：友人リクエスト、グループ招待など）を表します。

メッセージイベントとは異なり、リクエストイベントは**双方向の対話**を必要とします：
1. **受信**：アダプタがプラットフォームのネイティブリクエストを標準リクエストイベントに変換
2. **応答**：モジュールが`Request` DSLまたは`Event.approve()`/`Event.reject()`を使用して操作を実行

```
プラットフォームネイティブリクエストイベント
    │
    ▼
Converter.convert()        ← アダプタ実装（正方向変換）
    │
    ▼
標準リクエストイベント (request_idを含む)
    │
    ├─→ モジュールハンドラ @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← リクエストを承認
    │       └─→ event.reject()      ← リクエストを拒否
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← アダプタがオーバーライド
    │               │
    │               ▼
    │       プラットフォームAPI呼び出し
    │
    └─→ または直接アダプタ操作
            await adapter.Request("req_id").accept()
```

## 2. リクエストイベントのフィールド要件

### 2.1 標準フィールド

リクエストイベントは、OneBot12標準フィールドに加えて、以下のフィールドも含む必要があります：

| フィールド | 型 | 必須 | 説明 |
|------|------|------|------|
| `request_id` | string | **強く推奨** | リクエスト操作に使用する識別子 |
| `user_id` | string | はい | リクエストを発起したユーザーID |
| `user_nickname` | string | いいえ | リクエストを発起したユーザーのニックネーム |
| `comment` | string | いいえ | リクエストの付言 |

### 2.2 `request_id` フィールド

`request_id`はリクエスト操作の中心的な識別子です：

- **用途**：`Request` DSLで使用する可操作なリクエストを識別
- **生成ルール**：
  - まず、プラットフォームのネイティブリクエスト識別子（OneBot11の`flag`フィールド、Telegramの`chat_invite_link`など）を使用
  - プラットフォームにネイティブリクエストIDがない場合、アダプタは一意な識別子を生成する必要があります（推奨形式：`{platform}_{timestamp}_{user_id}`）
- **一意性**：同一プラットフォーム範囲内で一意である必要があります
- **欠落時の動作**：`request_id`が欠落している場合、`event.approve()` / `event.reject()`は`ValueError`を送出します

### 2.3 リクエストイベントの例

```json
{
  "id": "evt_123456",
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
  "comment": "友人を追加してください",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 チェーン呼び出し

`Request`は`Send`スタイルと同様のチェーン呼び出しインターフェースを提供します：

```python
# 基本的な使用法
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Botアカウントを指定
await adapter.Request("req_id").Using("bot1").accept()

# 付言を指定（キーワード引数で）
await adapter.Request("req_id").accept(comment="ようこそ")
await adapter.Request("req_id").reject(comment="一時的に追加できません")

# 組み合わせて使用
await adapter.Request("req_id").Using("bot1").accept(comment="ようこそ")
```

### 3.2 メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `Using(account_id)` | 操作を実行するBotアカウントを指定 | `RequestDSL`（チェーン呼び出し可能） |
| `accept(**kwargs)` | リクエストを承認 | `asyncio.Task`（await後に標準応答を返す） |
| `reject(**kwargs)` | リクエストを拒否 | `asyncio.Task`（await後に標準応答を返す） |

### 3.3 戻り値の形式

操作は標準API応答形式を返します：

**成功**：
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**失敗**：
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "リクエストが期限切れまたは存在しません"
}
```

**未実装**（アダプタが`_do_accept`/`_do_reject`をオーバーライドしていない場合）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "プラットフォーム MyAdapter はリクエスト操作 (accept) を実装していません"
}
```

## 4. Event 便利メソッド

`Event`ラッパークラスは、リクエストイベントハンドラで使用する便利メソッドを提供します：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # リクエストIDを取得
    request_id = event.get_request_id()
    if not request_id:
        print("警告：リクエストイベントにrequest_idがありません")
        return
    
    # リクエストを承認
    result = await event.approve()
    
    # またはリクエストを拒否
    # result = await event.reject(comment="一時的に友人を追加できません")
    
    # 結果を確認
    if result.get("status") == "ok":
        print("操作成功")
    else:
        print(f"操作失敗: {result.get('message')}")
```

### 4.1 Event メソッド一覧

| メソッド | 説明 | 戻り値 |
|------|------|--------|
| `get_request_id()` | リクエストIDを取得 | `str` |
| `approve(comment=None)` | 現在のリクエストイベントを承認 | 標準応答形式 |
| `reject(comment=None)` | 現在のリクエストイベントを拒否 | 標準応答形式 |

## 5. アダプタ実装要件

### 5.1 転換器要件

リクエストイベントを転換するアダプタの転換器は、**必ず**`request_id`フィールドを正しく設定する必要があります：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """プラットフォームネイティブリクエストイベントを転換"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" または "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← 重要なフィールド
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    プラットフォームネイティブイベントからリクエストIDを抽出
    
    まずプラットフォームネイティブIDを使用し、なければ一意なIDを生成
    """
    # まずプラットフォームネイティブIDを使用
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # フォールバック：一意なIDを生成
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 内部クラス実装

基底クラスの`accept()` / `reject()`は公開エントリーポイント：内部にscope認証ゲート（`scope.actions.<owner>.request`、無効化時は34601拒否応答を返す）とタスクラッパーを含みます。**アダプタは公開エントリーポイントをオーバーライドしないでください**。オーバーライドすると認証ゲートを迂回します。アダプタは`_do_accept` / `_do_reject`（非同期メソッド、直接標準応答dictを返す）をオーバーライドします。

> **多アカウントへの注意**：`_do_accept` / `_do_reject`内では`call_api`をアダプタ自身が呼び出すため、アカウントは自動的に注入されません。アカウントは`self.request_context.get("account_id")`から取得（`Using()`で明示指定 > イベントチェーン自動バインド、Sendの`send_context`と同口径）し、`account_id`パラメータとして`call_api`に渡す必要があります。そうしないと、多アカウント展開時にデフォルトアカウントに送信され、`request_id`がそのアカウントのセッションに存在しないため、プラットフォームは`invalid`と報告し、典型的な故障形態は「アカウント1のみ操作可能」となります。

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform リクエスト操作実装"""
        
        async def _do_accept(self, **kwargs) -> dict:
            """
            リクエストを承認
            
            :param kwargs: 拡張パラメータ、例：comment="備考"
            :return: 標準応答形式 dict
            """
            try:
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    account_id=self.request_context.get("account_id"),
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
            except Exception as e:
                return {
                    "status": "failed",
                    "retcode": 34001,
                    "data": None,
                    "message_id": "",
                    "message": f"リクエスト操作失敗: {e}",
                }
        
        async def _do_reject(self, **kwargs) -> dict:
            """リクエストを拒否（_do_acceptと同構造：approve=False）"""
```

### 5.3 リクエストタイプコンテキスト保持（異質なエンドポイントアダプタは必須）

#### 5.3.1 契約のギャップ

`Request` DSLは状態を持たないハンドルです：呼び出し元は`request_id`のみを持っています（[§3](#3-request-dsl)）。リクエストタイプは呼び出しパラメータに含まれません。しかし、多くのプラットフォームの承認/拒否エンドポイントは**異質**です。OneBot11系を例にすると：

| リクエストタイプ | エンドポイント |
|---|---|
| 友人追加 | `set_friend_add_request(flag, approve)` |
| グループ申請 / グループ招待 | `set_group_add_request(flag, sub_type, approve)`、`sub_type ∈ {"add", "invite"}` |

呼び出し元は`request_id`しか知らず、エンドポイント選択にはタイプが必要です。このコンテキストはアダプタが補完する必要があります：リクエストイベントはアダプタが受け取り、変換するものであり、タイプ情報は変換時に既に手元にあります。また、`request_id`に対応するリクエストタイプは変化しません。アダプタが独自に保持しない場合、エンドポイントを推測したり、呼び出し元に非標準パラメータを渡す必要が生じます。典型的な故障形態は、**グループ招待が友人エンドポイントに送信され、flagがuser_idとしてプロトコル側で解析されてエラーになる**ことです。

#### 5.3.2 規格要件

プラットフォームエンドポイントが異質（承認/拒否はリクエストタイプに応じてルーティングする必要がある）のアダプタは、`accept` / `reject`実装が以下の条件を満たす必要があります：

1. **イベント側保持**：アダプタがリクエストイベントを受け取るエントリーポイントで、`request_id → {リクエストタイプ, sub_type, group_id, アカウント}`をインスタンス内キャッシュに書き込み、不要なエントリを定期的にクリアする
2. **操作側ルーティング**：`_do_accept` / `_do_reject`内のエンドポイント選択順序は**kwargsの明示的パラメータ > キャッシュ > フォールバックデフォルトエンドポイント + WARNING**。タイプが不明な場合はログを出力し（可観測性）、静かにエンドポイントを選択してはならない
3. **kwargsの予約名**：明示的なオーバーライドパラメータは`request_type` / `sub_type` / `group_id`（アンダースコアなし、跨アダプタで同名同義）とし、`_request_type`などの非公開名は使用しない（標準呼び出し元は渡さない）
4. **アカウントの読み取りと所属チェック**：操作アカウントは基底クラス属性`self.request_context.get("account_id")`から取得（`Using()`で明示指定 > イベントチェーン自動バインド、Sendの`send_context`と同口径）。保持されたイベント到着アカウントはイベントチェーンが欠落した場合のフォールバック（例：ポーリング合成イベント、再起動後の再構築）。**アカウントインスタンスに解析できない場合は即時失敗**（34005を返す）し、デフォルトアカウントに静かに回帰してはならない。回帰すると操作が間違った接続に送信され（flagがデフォルトアカウントのセッションに存在せず、プラットフォームは`invalid`と報告し、多アカウントでは「アカウント1のみ操作可能」という不思議な故障になる）
5. **デフォルト永続化**：保持メディアはデフォルトでフレームワークの統一ストレージ（`self.sdk.storage`）**単一キーの整ブロックスナップショット**。リクエストは低頻度の承認イベント（友人/グループ招待、メッセージ流ではない）であり、イベント到着時に即時書き込み（DB内の足跡は常に1つのキー）。起動時に一度読み込み、実行時の読み取りはオーバーヘッドゼロ。ストレージが利用できない場合はメモリのみに降格（WARNING）、イベントフローをブロックしない
6. **処理後のクリア**：操作が成功したら`request_id`のエントリを削除し、スナップショットを即時書き込み

単一のリクエストエンドポイントを持つプラットフォーム（統一`/set_request`）は保持する必要がない。本節はアダプタ実装の口径であり、`Request` DSL契約は影響を受けない。

#### 5.3.3 統一条目フィールド（メディア依存）

コンテキスト条目は以下の統一フィールド形状で保持する。**フィールド形状は相互運用契約**：メモリdict、KV value、ORM行はすべて同じ形状で保存し、今後の跨アダプタ集約や移行時に形状が一致するようにする。ストレージメディアは選択可能で、メディアの変更によってフィールドの意味が変わらないようにする。

| フィールド | 型 | 必須 | 意味とソース |
|---|---|---|---|
| `request_type` | `str` | はい | リクエストタイプ、イベント`detail_type`（`"friend"` / `"group"`）から取得 |
| `sub_type` | `str \| None` | グループリクエストに必須 | グループリクエストのサブタイプ `"add"` / `"invite"`、プラットフォームネイティブイベントから取得（OB11系`sub_type`） |
| `group_id` | `str \| None` | グループリクエストに必須 | 目標グループID、プラットフォームネイティブイベントから取得 |
| `account` | `str \| None` | 多アカウントに必須 | イベント到着アカウント、イベント`self.user_id`から取得 |
| `ts` | `float` | はい | イベント到着Unixタイムスタンプ（秒）、TTL判定の基準 |

条目一貫性ルール：

- **1対1対応**：1つの`request_id`は1つの条目に対応する。同じ`request_id`の重複イベントは上書きされる（멱등性）
- **処理後の削除**：操作が成功したら条目を削除
- **TTL**：`ts`を基準に、プラットフォーム側のリクエスト有効期限をカバーする1時間程度を推奨。期限切れは未保持扱いとし、フォールバックデフォルトエンドポイント + WARNING
- **キー名（KV永続化時）**：`{アダプタ設定キー}:request_ctx:{request_id}`、跨アダプタの衝突を避ける

#### 5.3.4 参考実装（統一ストレージ単一キースナップショット、デフォルト）

保持メディアは**デフォルトでフレームワークの統一ストレージ**（`self.sdk.storage`）：リクエストイベントは承認系の低頻度イベント（友人/グループ招待、メッセージ流ではない）であり、**イベント到着時に即時書き込み**することで、書き込み負荷を生じない。ストレージ形式は**単一キーの整ブロックスナップショット**：上下文辞書全体を1つのキーとして1回で書き込む（DB内の足跡は常に1つのキー、処理に伴い自動的に収束）。逐個flag分キーにはしない。再起動後は起動時に一度読み込み、実行時の読み取りはオーバーヘッドゼロ。

```python
import time

from ErisPulse.Core import BaseAdapter, RequestDSL


class MyAdapter(BaseAdapter):
    """リクエストエンドポイントが異質なプラットフォーム（友人とグループリクエストが分離）"""

    _REQ_CTX_TTL = 86400   # 保持秒数（プラットフォーム側flag有効期限をカバー、再起動でも失わない）
    _REQ_CTX_MAX = 512     # 条目容量上限

    def __init__(self, sdk=None):
        super().__init__(sdk)
        self._request_ctx: dict[str, dict] = {}   # request_id → リクエストコンテキスト（メモリ状態）
        self._ctx_key = f"{self._get_config_key()}:request_ctx"   # 単一キーの整ブロックスナップショット

    async def start(self):
        # 起動時の読み込み（再起動後も承認可能）；ストレージが利用できない場合はコールドスタート処理
        try:
            loaded = self.sdk.storage.get(self._ctx_key, {}) or {}
            now = time.time()
            self._request_ctx = {k: v for k, v in loaded.items()
                                 if now - v.get("ts", 0) <= self._REQ_CTX_TTL}
        except Exception as e:
            self.logger.warning(f"リクエストコンテキストの読み込み失敗（コールドスタート処理）: {e}")
            self._request_ctx = {}

    def _persist_ctx(self) -> None:
        """単一キーの整ブロックスナップショットを書き込み（ストレージが利用できない場合はメモリのみに降格、イベントフローをブロックしない）"""
        try:
            self.sdk.storage.set(self._ctx_key, self._request_ctx)
        except Exception as e:
            self.logger.warning(f"リクエストコンテキストの書き込み失敗（メモリのみに降格）: {e}")

    def remember_request(self, request_id: str, *, request_type: str,
                         sub_type: str | None = None, group_id: str | None = None,
                         account: str | None = None) -> None:
        """イベント側でリクエストコンテキストを保持（アダプタがリクエストイベントを受け取るエントリーポイントで呼び出す）"""
        now = time.time()
        expired = [k for k, c in self._request_ctx.items() if now - c["ts"] > self._REQ_CTX_TTL]
        for k in expired:
            self._request_ctx.pop(k)
        while len(self._request_ctx) >= self._REQ_CTX_MAX:
            self._request_ctx.pop(min(self._request_ctx, key=lambda k: self._request_ctx[k]["ts"]))
        self._request_ctx[request_id] = {
            "request_type": request_type,   # "friend" / "group"
            "sub_type": sub_type,           # グループリクエストのサブタイプ："add" / "invite"
            "group_id": group_id,
            "account": account,             # イベント到着アカウント（イベントのself.user_id / 代理アカウント名）
            "ts": now,
        }
        self._persist_ctx()

    class Request(RequestDSL):
        """エンドポイントルーティング：kwargsの明示的パラメータ > キャッシュ > フォールバックデフォルトエンドポイント + WARNING"""

        def _route(self, **kwargs) -> dict:
            ctx = {k: kwargs[k] for k in ("request_type", "sub_type", "group_id") if kwargs.get(k)}
            cached = self._adapter._request_ctx.get(self._request_id, {})
            if not ctx.get("request_type"):
                ctx.update({k: v for k, v in cached.items()
                            if k in ("request_type", "sub_type", "group_id") and v})
                ctx.setdefault("account", cached.get("account"))
            if not ctx.get("request_type"):
                self._adapter.logger.warning(f"リクエスト {self._request_id} のタイプが不明、友人エンドポイントにフォールバック")
                ctx["request_type"] = "friend"
            return ctx

        def _resolve_or_fail(self, account):
            """
            承認アカウントの所属チェック：解析失敗は即時失敗（34005）、デフォルトアカウントにフォールバックしない。

            デフォルトアカウントにフォールバックすると、操作が間違った接続に送信され（flagがそのアカウントのセッションに存在せず、
            プラットフォームは`invalid`と報告し、"アカウント1のみ操作可能"という不思議な故障になる）。
            """
            if not account:
                return None, None            # アカウント情報が一切ない場合はデフォルトアカウントの意味を維持
            name, inst = self._adapter._resolve_account(account)
            hit = str(account) == str(name) or str(account) == str(getattr(inst, "bot_id", "") or "")
            if not hit:
                self._adapter.logger.warning(
                    f"リクエスト {self._request_id} のアカウント {account} がアカウントインスタンスに解析できない、デフォルトアカウントへのフォールバックを拒否")
                return None, "34005"
            return (name, inst), None

        async def _do_accept(self, **kwargs) -> dict:
            """リクエストを承認；kwargsのタイプルーティングはrequest_type / sub_type / group_idで明示的にオーバーライド可能"""
            return await self._do_action(approve=True, **kwargs)

        async def _do_reject(self, **kwargs) -> dict:
            """リクエストを拒否（_do_acceptと同構造：approve=False）"""
            return await self._do_action(approve=False, **kwargs)

        async def _do_action(self, approve: bool, **kwargs) -> dict:
            ctx = self._route(**kwargs)
            account = self.request_context.get("account_id") or ctx.get("account")
            resolved, fail = self._resolve_or_fail(account)
            if fail:
                return {
                    "status": "failed", "retcode": 34005, "data": None,
                    "message_id": "", "message": f"リクエストアカウント {account} がアカウントインスタンスに解析できない",
                }
            try:
                if ctx["request_type"] == "group":
                    result = await self._adapter.call_api(
                        endpoint="/set_group_add_request",
                        flag=self._request_id,
                        sub_type=ctx.get("sub_type") or "add",
                        approve=approve,
                        account_id=account,
                    )
                else:
                    result = await self._adapter.call_api(
                        endpoint="/set_friend_add_request",
                        flag=self._request_id,
                        approve=approve,
                        account_id=account,
                    )
                response = {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            except Exception as e:
                response = {
                    "status": "failed", "retcode": 34001, "data": None,
                    "message_id": "", "message": f"リクエスト操作失敗: {e}",
                }
            if response["status"] == "ok":
                self._adapter._request_ctx.pop(self._request_id, None)   # 処理後のクリア
                self._adapter._persist_ctx()
            return response
```

#### 5.3.5 バウンダリと降格

**降格の意味**：統一ストレージが利用できない（接続失敗クールダウン期のfast-fail）場合、書き込みはメモリのみに降格（WARNINGで可観測）、イベントは通常配信される。再起動後は条目が失われ、タイプ不明のフォールバック + WARNING経路をたどる。

**同等のメディア**：ビルトインORM（`request_id`主キーでテーブル作成、[データモデル層](../developer-guide/orm.md)参照）は意味的に同等で、アダプタは必要に応じて選択可能。追加のファイルや新しい依存関係は導入しない。

**マルチインスタンスの境界**：本規格はマルチプロセスインスタンスの協調をカバーしない。ErisPulseは単一プロセスマルチbotモデル（複数アカウントが同一プロセス内、リクエストは所属アカウントと天然に同側）であり、統一ストレージで再起動の意味を満たす。跨インスタンス共有（複数プロセスでアカウントを分散）が必要な場合は別途プロジェクトを立てる。

### 5.4 プラットフォームがリクエスト操作をサポートしていない場合

プラットフォームが友人リクエスト/グループ招待操作をサポートしていない場合（一部のプラットフォームはリクエストを自動処理する）、アダプタは以下のいずれかを行うことができます：

1. **`Request`内部クラスをオーバーライドしない**：基底クラスのデフォルト実装を使用し、`accept()`/`reject()`を呼び出すと`retcode=10002`を返す
2. **`request_id`を生成しない**：`request_id`を生成せず、`event.approve()`が`ValueError`を送出するようにする
3. **ログを記録する**：`_do_accept`/`_do_reject`で警告を記録し、適切なエラーコードを返す

### 5.5 まとめ：SendとRequestの並行

アダプタには2つの並行するDSL内部クラスがあり、それぞれが役割を分担しています：

```
BaseAdapter
├── Send(SendDSL)     ← メッセージ送信
│   ├── Raw_ob12()    ← 必須実装
│   ├── Text()        ← 推奨実装
│   └── Image()       ← 必要に応じて実装
│
└── Request(RequestDSL) ← リクエスト操作
    ├── accept()        ← 公開エントリーポイント（scopeゲート + タスクラッパー、オーバーライドしない）
    ├── reject()        ← 公開エントリーポイント（同上）
    ├── _do_accept()    ← 必要に応じてオーバーライド
    └── _do_reject()    ← 必要に応じてオーバーライド
```

### 5.6 アダプタ`__init__`の注意事項

`Request`内部クラスの`__init__`をオーバーライドする場合、引数を透過的に渡し、`super().__init__()`を呼び出す必要があります。詳しくは[アダプタ開発入門 - `__init__`の注意事項](../developer-guide/adapters/getting-started.md#init-の注意事項)（`Request`も同様、引数は`adapter, request_id, account_id`）を参照してください。

## 6. アダプタ実装チェックリスト

### 基本要件
- [ ] `__init__`をオーバーライドした場合、`super().__init__()`を呼び出している（Send / Requestファクトリーの初期化を確実にする）

### リクエストイベント変換
- [ ] リクエストイベントに`request_id`フィールドが含まれている（強く推奨）
- [ ] `detail_type`が`"friend"`または`"group"`に正しくマッピングされている
- [ ] `{platform}_raw`フィールドにプラットフォームの元のデータを保持している
- [ ] `request_id`の生成ルールがドキュメントに記載されている

### リクエスト操作
- [ ] `Request`内部クラスが実装されている（プラットフォームがリクエスト操作をサポートしている場合）
- [ ] `_do_accept()` / `_do_reject()`がオーバーライドされている（公開エントリーポイント`accept()` / `reject()`はオーバーライドしない——scope認証ゲートを迂回する）
- [ ] 操作は標準API応答形式を返す
- [ ] サポートしていない操作は`retcode=10002`を返す
- [ ] ネットワークエラーは`retcode=33xxx`（API応答標準に準拠）を返す

### リクエストタイプコンテキスト保持（異質なエンドポイントプラットフォーム、§5.3参照）
- [ ] リクエストイベントのエントリーポイントで`request_id → {リクエストタイプ, sub_type, group_id, アカウント}`のコンテキストを保持している
- [ ] 条目のフィールドは§5.3.3の統一条目フィールド表と一致している（`ts`タイムスタンプを含む；`request_id`は1対1対応、処理後に削除）
- [ ] `accept` / `reject`のエンドポイントルーティング順序はkwargsの明示的パラメータ > キャッシュ > フォールバックデフォルトエンドポイント + WARNING
- [ ] タイプのオーバーライドパラメータは保留名`request_type` / `sub_type` / `group_id`（`_request_type`などの非公開名は使用しない）を使用している
- [ ] キャッシュにはTTLと容量上限があり、操作が成功した後に該当条目を削除している
- [ ] 多アカウント：操作アカウントは`self.request_context.get("account_id")`から読み取っている（`Using()` > イベントチェーンのフォールバック、Sendの`send_context`と同口径）；保持されたアカウントはイベントチェーンが欠落した場合のフォールバック（例：ポーリング合成イベント、再起動後の再構築）
- [ ] 承認アカウントの解析失敗は即時失敗（34005）、デフォルトアカウントにフォールバックしない
- [ ] デフォルトは統一ストレージの単一キーのスナップショット：起動時に読み込み、イベント到着/処理後に書き込み、ストレージが利用できない場合はメモリのみに降格（WARNING）、イベントフローをブロックしない

単一のリクエストエンドポイントを持つプラットフォーム（統一`/set_request`）は保持する必要がない。本節はアダプタ実装の口径であり、`Request` DSL契約は影響を受けない。

## 7. エラーコードの拡張

リクエスト操作に関連する**アダプタ実装層**の推奨エラーコード（[API応答標準](api-response.md)§3.2に準拠し、`34xxx`プラットフォームエラーセグメントの下3桁にカスタム定義）：

| エラーコード | エラーネーム | 説明 |
|-------|-------|------|
| 34001 | Request Not Found | リクエストが存在しないまたは期限切れ |
| 34002 | Request Already Handled | リクエストは既に処理済み |
| 34003 | Request Not Supported | プラットフォームはこのタイプのリクエスト操作をサポートしていない |
| 34004 | Permission Denied | Botはこのリクエストを処理する権限がない（プラットフォームが返す） |
| 34005 | Request Account Unresolved | リクエスト所属アカウントがアカウントインスタンスに解析できない（即時失敗、デフォルトアカウントにフォールバックしない） |

> **フレームワークコードとの境界**：上記の`340xx`は**プラットフォーム/アダプタ**が返すリクエスト処理失敗です。ErisPulseフレームワークは`scope.actions`でモジュールの`request`アクションを禁止した場合、**アダプタを呼び出す前に**直接`34601`（Action Denied、[API応答標準§5.3](api-response.md#53-フレームワーク拡張返却コード34xxx-プラットフォームエラーセグメントの下3桁にカスタム定義)）を返します。これらは互いに代替ではなく、まず`34601`フレームワークゲートを通過し、次にプラットフォーム層の`340xx`エラーに到達します。

## 8. 関連ドキュメント

**リクエスト操作を実装する際に併せて参照するべきドキュメント**：
- [イベント変換標準](event-conversion.md) - 完全なイベント変換規格（`request_id`フィールド要件を含む）
- [API応答標準](api-response.md) - アダプタAPI応答形式の標準（操作返却値とエラーコード）
- [ストレージバックエンド](../advanced/storage-backends.md) - 起動後にリクエストコンテキストを永続化する必要がある場合の統一KVストレージ

**同一アダプタの他のDSL**：
- [送信メソッド規格](send-method-spec.md) - Sendクラスのメソッド命名とパラメータ規格
- [セッションタイプ標準](session-types.md) - セッションタイプの定義とマッピング関係



### API 动作标准

# ErisPulse API アクション標準

> [!TIP]
> **このドキュメントを読むべきタイミング**：アダプター内で Api DSL の標準アクション（get_user_info / delete_message など）を実装する場合、またはモジュールからこれらの標準アクションをクロスプラットフォームで呼び出す際に、パラメータや data フィールドを確認したいときに本書を参照してください。必要なければ読み飛ばして構いません。

このドキュメントは、ErisPulse アダプターにおける **OneBot12 標準 API アクション**の統一インターフェース仕様を定義するものであり、モジュール開発者が標準インターフェースに向けてプログラミングできるようにし、プラットフォームネイティブ API へのマッピングはアダプターが担当します。

> **対象範囲**：OneBot12 標準アクションのうち、`ApiDSL` はユーザー / グループ / ギルド（Guild）/
> メッセージ管理 / メタ（Meta）の通常インターフェースに対する強く型付けされたメソッドを提供します
> （`send_message` は `SendDSL.Raw_ob12` が担当）。ファイルリソースアクション
> （`upload_file` / `get_file` / 分割転送）はフォールバックのパススルーとしてのみ保持されており、
> §3.5 の説明を参照してください。プラットフォーム拡張アクションは `Api.call("prefix.action", ...)`
> というエスケープハッチで呼び出します。アクションのパラメータと戻り値の構造は
> OneBot12 仕様（リポジトリ内 `onebot/specs/interface/`）を正とします。

## 1. 設計の背景

ErisPulse では、メッセージセグメント（メッセージの送受信）とイベント形式はすでに OneBot12 標準に完全に準拠していますが、**API アクション呼び出し**（ユーザー情報の取得、グループ一覧の取得、メッセージの取り消しなど）はこれまで統一されておらず——モジュール開発者はプラットフォームごとに異なる `call_api` 呼び出しを書く必要がありました。

`ApiDSL` は強く型付けされた標準アクションメソッドを提供することで、この問題を解決します：

```
モジュールコード（クロスプラットフォーム統一）   アダプター実装（プラットフォーム固有）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  アダプターの call_api / オーバーライド
adapter.Api.get_group_list()      →  アダプターの call_api / オーバーライド
adapter.Api.delete_message("id")  →  アダプターの call_api / オーバーライド
```

## 2. 3 層 DSL の並列構造

ErisPulse のアダプターには、それぞれが役割を担う 3 つの並列した DSL 内部クラスが存在します：

```
BaseAdapter
├── Send(SendDSL)       ← メッセージ送信（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← リクエスト操作（accept/reject）
└── Api(ApiDSL)          ← 標準 API アクション（ユーザー/グループ/ギルド/メッセージ管理/ファイル/メタ）★
```

| DSL | 役割 | メソッドスタイル | 戻り値 |
|-----|------|---------|--------|
| `Send` | メッセージ送信 | メソッドチェーン + `asyncio.Task` | 標準レスポンス |
| `Request` | リクエストイベントの処理 | `asyncio.Task` | 標準レスポンス |
| `Api` | クエリ/管理操作 | `async` メソッド | 標準レスポンス |

## 3. 標準アクション一覧

### 3.1 ユーザー関連

| メソッド | OB12 アクション | パラメータ | data 戻り値 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | なし | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | なし | `list[get_user_info レスポンス]` |

### 3.2 グループ関連

| メソッド | OB12 アクション | パラメータ | data 戻り値 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | なし | `list[get_group_info レスポンス]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info レスポンス]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | なし |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | なし |

### 3.3 メッセージ管理

| メソッド | OB12 アクション | パラメータ | 説明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | メッセージの取り消し/削除 |

> **メッセージ送信**（`send_message`）は `SendDSL` の `Raw_ob12` が担当するため、`ApiDSL` では重複提供しません。

### 3.4 ギルド（Guild）関連

OneBot12 のギルド体系は 2 階層に分かれます：**ギルド（guild）** と **サブチャンネル（channel）**。

| メソッド | OB12 アクション | パラメータ | data 戻り値 |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | なし | `list[get_guild_info レスポンス]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | なし |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info レスポンス]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | なし |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info レスポンス]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | なし |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info レスポンス]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | なし |

> ギルド体系とグループ（group）は互いに独立しています：Discord / QQ ギルド / Kook などのプラットフォームはギルドインターフェースを実装し、
> 従来の QQ / WeChat はグループインターフェースを実装します。両方が同時に存在する場合もあれば、どちらか一方のみの場合もあります。

### 3.5 ファイルリソース操作

> [!WARNING]
> **ファイルリソースモデル（file_id 2 段階方式）は ErisPulse では「フォールバックで利用可能」に位置づけられます**：
> ErisPulse のファイル送受信は「先にアップロードして file_id を取得し、それを参照する」モデルを採用していません——モジュールがファイルを送信するには
> `SendDSL.File(file, filename)` を使用します（URL / パス / バイトは**送信時に直接転送**、
> [送信メソッド仕様](send-method-spec.md) を参照）。
> 本節の `upload_file` / `get_file` / 分割転送アクションはプラットフォーム固有の `file_id` ファイルリソース
> 機能に依存しており、**汎用性が不十分**です。アダプターのバックエンドが当該機能を本来備えている場合にのみパススルーが可能で、フレームワーク内蔵の
> アダプターは**実装せず、実装も推奨しません**。呼び出すと通常 `retcode=10002` が返されます。
> モジュールがクロスプラットフォームでファイルを送信する必要がある場合は `SendDSL.File` を使用し、file_id に依存しないでください。
>
> **展望**：`file_id` リソースモデルのフレームワーク層への標準化は今後の方向性ですが、現在のバージョンでは提供されていません。

一括転送（小さいファイル）：

| メソッド | OB12 アクション | パラメータ | data 戻り値 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` の `type` パラメータ：
- `"url"`：URL 経由でアップロード（`url` の指定が必要）
- `"path"`：ローカルパス経由でアップロード（`path` の指定が必要）
- `"data"`：バイナリデータ経由でアップロード（`data` の指定が必要）

#### 3.5.1 分割転送（大きなファイル、上記のフォールバック対象）

OneBot12 の分割アクションは `stage` で段階を区別します。`ApiDSL` は同一アクションの 3 段階/2 段階を独立したメソッドに分割します
（`offset` はバイトオフセット、`data` は JSON 内では Base64）。以下の表は参照用にのみ残しており、
アダプターは実装する必要がなく、強制的に実装すべきでもありません：

**分割アップロードの 3 ステップ**：`prepare` → `transfer`（断片ごとにループ）→ `finish`

| メソッド | 対応 stage | パラメータ | data 戻り値 |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id`（転送中に使用） |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | なし |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str`（ファイル全体の検証） | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**分割ダウンロードの 2 ステップ**：`prepare` → `transfer`（断片を取得するループ）

| メソッド | 対応 stage | パラメータ | data 戻り値 |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data`（今回の分割断片のバイト列） |

### 3.6 メタ（Meta）アクション

メタアクションは特定のアカウントを対象としないため、`Using()` で Bot を指定する必要はありません。

| メソッド | OB12 アクション | パラメータ | data 戻り値 |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | イベントオブジェクトの配列（メタイベントを除く） |
| `get_supported_actions()` | `get_supported_actions` | なし | `list[str]` サポート対象のアクション名 |
| `get_status()` | `get_status` | なし | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | なし | `impl`, `version`, `onebot_version` |

### 3.7 汎用拡張アクション

| メソッド | 説明 |
|------|------|
| `call(action, **params)` | プラットフォーム拡張アクションのエスケープハッチ。OB12 拡張命名規則 `{prefix}.{action}` に従う |

## 4. 使用方法

### 4.1 基本的な呼び出し

```python
from ErisPulse import adapter

# ユーザー情報を取得（クロスプラットフォーム統一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"ユーザー名: {user_name}")

# グループ一覧を取得
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# メッセージを取り消し
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Bot アカウントの指定（マルチアカウントモード）

```python
# 指定した Bot アカウントで操作を実行
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 プラットフォーム拡張アクション

```python
# プラットフォーム固有の拡張アクションを呼び出す（{prefix}.{action} の命名を推奨）
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 イベントハンドラーでの使用

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # 送信者の詳細情報を取得
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"こんにちは、{user_name}さん！")
```

## 5. アダプター実装

### 5.1 デフォルト動作（ゼロコンフィグ）

`ApiDSL` のデフォルト実装は、標準アクション名を `endpoint` としてそのまま `adapter.call_api()` に渡します：

```python
# ApiDSL のデフォルト実装と等価：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

> **アカウントフィールド**：フレームワークはアダプターの `call_api` における実際の消費方法に応じてアカウントバインディングを自動で適合させます（標準名は `account_id`；旧名 `_account_id` は自動書き換え；関数本体内の `params.pop` も同様に認識）。消費されない場合は、プラットフォームパラメータへの漏出を避けるためこのフィールドを除去し、一度だけヒントを表示します——消費形態の詳細は [アダプター開発 - アカウント解決](../developer-guide/adapters/core-concepts.md#アカウント解決) を参照してください。

**適用シナリオ**：アダプターの基盤となるバックエンド自体が OneBot12 標準アクションプロトコルに準拠している場合、
`call_api` は標準アクション名をそのままサポートします（当該プロトコルに準拠するサーバーに直接接続する場合など）。

### 5.2 標準メソッドのオーバーライド（プラットフォームネイティブ API へのマッピング）

アダプターは個々の標準メソッドをオーバーライドし、プラットフォームネイティブ API にマッピングできます：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 標準 API アクションの実装"""

        async def get_user_info(self, user_id: str) -> dict:
            # プラットフォームネイティブ API へのマッピング
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                # プラットフォーム側エラー：341xx～345xx 段の下 3 桁をカスタム使用（346xx はフレームワーク予約のため使用しないこと）
                return self._adapter.make_error(retcode=34400, message="ユーザーが存在しません")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 サポートされていないアクション

アダプターがオーバーライドしていない標準メソッドはデフォルト実装（`call_api` への委譲）に従います。`call_api` もそのアクションをサポートしていない場合は、標準エラーレスポンスを返す必要があります：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"サポートされていないアクション: {endpoint}")
    # ... プラットフォーム API の呼び出し
```

モジュール開発者は戻り値の `retcode` でサポートされているかどうかを判断できます：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("このプラットフォームはフレンドリストの取得をサポートしていません")
```

## 6. レスポンス形式

すべての `ApiDSL` メソッドは標準 API レスポンス形式を返します（詳細は [API レスポンス標準](api-response.md) を参照）：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **注意**：情報照会系アクションの `message_id` は空文字列です（`message_id` が設定されるのはメッセージ送信系アクションのみです）。

## 7. SendDSL / RequestDSL との関係

| シナリオ | 使用する DSL | 例 |
|------|---------|------|
| メッセージ送信 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| リクエストの承認/拒否 | `Request` | `adapter.Request("req_id").accept()` |
| ユーザー/グループ情報の取得 | `Api` | `adapter.Api.get_user_info("123")` |
| メッセージの取り消し | `Api` | `adapter.Api.delete_message("msg_id")` |
| グループからの退出 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. アダプター実装チェックリスト

### 標準アクション
- [ ] `call_api` が標準アクション名を処理できる（または対応する `ApiDSL` メソッドをオーバーライドする）
- [ ] サポートされていないアクションは `retcode=10002` を返す
- [ ] 戻り値は標準 API レスポンス形式に従う
- [ ] `data` フィールドに OB12 標準で定義されたフィールドが含まれている
- [ ] ギルドプラットフォームは `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel` を実装する必要がある
- [ ] メタアクション（`get_status` / `get_version` / `get_supported_actions`）の実装を推奨
- [ ] **ファイル送受信は `SendDSL.File`（直接転送）を使用**；ファイルリソースアクション（upload_file/get_file/分割転送）の実装は**強制ではない**。バックエンドが `file_id` リソース機能を備えている場合にのみパススルーが必要

### 拡張アクション
- [ ] プラットフォーム拡張アクションは `{prefix}.{action}` の命名を使用する
- [ ] 拡張アクションのパラメータとレスポンスも OB12 のアクション要求/レスポンス構造に従う

## 9. 関連ドキュメント

**Api DSL の戻り値実装時の対照資料**：
- [API レスポンス標準](api-response.md) - アダプター API レスポンス形式の標準

**同一アダプターのその他の DSL**：
- [送信メソッド仕様](send-method-spec.md) - Send クラスのメソッド命名とパラメータ仕様
- [リクエスト操作仕様](request-action-spec.md) - Request DSL の使用方法

**イベント側の関連資料**：
- [イベント変換標準](event-conversion.md) - イベント形式とメッセージセグメントの標準



====
高级主题
====


### 网络客户端

# ネットワーククライアント

> [!TIP]
> **この記事を読むタイミング**：出力用の HTTP / WebSocket リクエストが必要な場合。不要であれば読み飛ばしても、他の機能の使用に影響はありません。

ErisPulse は、HTTP リクエスト、WebSocket 接続、接続プール管理を統合した統一されたネットワーククライアントを提供しています。モジュールやアダプターは、**このクライアントを優先して使用**する必要があります。`aiohttp` / `httpx` / `requests` などのサードパーティライブラリを直接インポートしてはいけません。

## 概要

ネットワーククライアントの主な機能：

- **統一されたインターフェース**：`get` / `post` / `put` / `delete` / `patch` / `request` メソッドを提供
- **WebSocket クライアント**：`ws_connect` を使用してクライアント WebSocket 接続を確立
- **自動ログ記録**：すべてのリクエストに対して自動的にログと統計情報を記録
- **ライフサイクル統合**：リクエストごとに `client.request` ライフサイクルイベントがトリガーされ、WS 接続は `client.ws.connect` イベントをトリガー
- **リトライサポート**：自動リトライ回数と間隔を設定可能
- **タイムアウト制御**：接続タイムアウトとリクエストタイムアウトを個別に制御
- **接続プールの再利用**：aiohttp.ClientSession に基づく接続プール管理
- **例外体系**：aiohttp の例外を ErisPulse の例外 (ClientError 体系) に自動的に変換

## 速習

### HTTP リクエスト

```python
from ErisPulse.Core import client

# GET リクエスト
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST リクエスト
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket 接続

```python
from ErisPulse import client   # 2.10+ からのルートインポート（ErisPulse.Core.client の深いパスも互換性あり）

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

#### 出力接続の自動プール登録（2.10+）

`ws_connect` で確立された接続は**デフォルトでフレームワークの接続プールに登録**されます（`track=False` で無効化可能）：
`connections.list(owner=...)` で確認でき、その接続にブロードキャストが可能です。接続が閉じられたり、リモートが切断されたりすると自動的に登録解除されます。
**モジュールのアンロード / アダプターの停止時に、フレームワークがその名下のすべての出力接続を一括で閉じる**ため、リークを防ぎます。

```python
from ErisPulse import client, connections

ws = await client.ws_connect("wss://example.com/ws")
print(ws.id, ws.owner)   # 登録済み：接続 ID と所有者

# owner コンテキストが利用できない場合（例：ツールスレッドのコールバック）は、明示的に所有者を指定し、アンロード時に自動回収されるようにします：
ws2 = await client.ws_connect("wss://example.com/ws2", owner="MyAdapter")
```

接続プールとブロードキャストの詳細は [接続プールとブロードキャスト](connections.md) を参照してください。

## HttpResponse

すべてのリクエストメソッドは `HttpResponse` オブジェクトを返します：

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP ステータスコード (例: 200, 404)
resp.reason       # str | None - ステータスの説明 (例: "OK")
resp.headers      # 応答ヘッダー (大文字小文字を区別しない)
resp.content_type # str | None - Content-Type
resp.url          # 最終的な URL (リダイレクトにより変更される可能性がある)
resp.raw          # ベースの生の応答オブジェクト (現在は aiohttp.ClientResponse)

# 応答本文の読み取り
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # JSON を解析
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

# JSON リクエスト本文
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# フォームリクエスト本文
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# 原始データ
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# ファイルアップロード (files パラメータを使用、aiohttp をインポートする必要はない)
# 形式: {フィールド名: ファイルオブジェクト/bytes/(filename, file)/(filename, file, content_type)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "プロフィール画像"},            # 任意: 通常のフォームフィールドも同時に送信可能
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# 簡単な書き方: ファイルオブジェクトを直接渡す
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# メモリ内のデータを直接アップロード (ファイルに落とす必要はない)
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

### 一般的な request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## パラメータの説明

### HTTP リクエストパラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `url` | `str` | リクエスト URL |
| `params` | `dict[str, str]` | クエリパラメータ (オプション) |
| `headers` | `dict[str, str]` | 追加のリクエストヘッダー (オプション) |
| `data` | `Any` | リクエスト本文 (フォームまたは原始データ) (オプション) |
| `json` | `Any` | JSON リクエスト本文 (オプション) |
| `files` | `dict[str, Any]` | ファイルアップロードフィールド (オプション、multipart/form-data を自動構築) |
| `timeout` | `float` | 今回のリクエストのタイムアウト (秒) (オプション、デフォルト値を上書き) |
| `max_retries` | `int` | 今回の最大リトライ回数 (オプション、デフォルト値を上書き) |

### ws_connect パラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `url` | `str` | WebSocket サーバーの URL |
| `headers` | `dict[str, str]` | 追加のリクエストヘッダー (オプション) |
| `heartbeat` | `float` | ハートビートの間隔 (秒) (オプション) |

## タイムアウトとリトライ

```python
from ErisPulse.Core import Client

# タイムアウトをカスタムしたクライアントを作成
client = Client(
    timeout=60,           # リクエスト全体のタイムアウト 60秒
    connect_timeout=5,    # 接続のタイムアウト 5秒
    max_retries=3,        # 失敗時に自動リトライ 3回
    retry_delay=2,        # リトライ間隔 2秒
)

# 単回のリクエストでタイムアウトを上書き
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> クライアントクラスは 2.8.0 から `Client` に名前が変更されました（`sdk.client` の属性名は変更されません）；旧名 `HttpClient` は互換性のエイリアスとして残され、古いコードは変更する必要はありません。

## デフォルトヘッダーのカスタマイズ

```python
client = Client(
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

# 統計情報の確認
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# 統計情報のリセット
client.reset_stats()
```

## ライフサイクルイベント

### HTTP リクエストイベント

リクエスト完了後に `client.request` イベントがトリガーされ、監視に利用できます：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### WebSocket 接続イベント

WebSocket 接続確立後に `client.ws.connect` イベントがトリガーされます：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS 接続: {event_data['url']}")
```

## コンテキストマネージャー

```python
# コンテキストマネージャーとして使用し、セッションを自動的に閉じる
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket クライアント

`client.ws_connect()` を使用して WebSocket クライアント接続を確立し、`ClientWebSocket` オブジェクトを返します。クライアントとサーバーの WebSocket は同じ `WebSocketConnectionBase` 基底クラスを共有し、send/receive/iter のインターフェースは完全に一致します。

### 基本的な使い方

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### メッセージの受信

#### 高レベルメソッド（推奨）

メッセージの種類を自動的にフィルタリングし、切断時に `WebSocketDisconnect` をスローします：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# 単一のメッセージ受信
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# メッセージのイテレーション受信 (切断時に自動的に停止)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### 低レベルメソッド

`receive()` と `iter_messages()` を使用して、メッセージの種類を識別し、TEXT / BINARY / CLOSE / ERROR を区別します：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# 単一のメッセージ受信
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# メッセージのイテレーション受信 (CLOSE/ERROR の時点で自動的に停止)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"テキスト: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"バイナリ: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` は、下層ライブラリに依存しない統一された WebSocket メッセージタイプです：

| 属性 | 型 | 説明 |
|------|------|------|
| `type` | `str` | メッセージの種類: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | メッセージのデータ |

### ClientWebSocket の属性

| 属性 | 型 | 説明 |
|------|------|------|
| `url` | `URL` | 接続の URL |
| `headers` | `Headers` | 応答ヘッダー |
| `closed` | `bool` | 接続が閉じられているかどうか |
| `raw` | `object` | 下層の生のオブジェクト (aiohttp.ClientWebSocketResponse) |

### ライフサイクルフック

`サービス側 WebSocketConnection` と同様に、`on_disconnect` と `on_error` のコールバックをサポートします：

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

### 接続の閉じ

```python
await ws.close(code=1000, reason="正常な切断")
```

## 例外体系

ErisPulse は、統一された例外階層を定義しており、`sdk.client` から発生するリクエストは、aiohttp の例外を自動的に ErisPulse の例外に変換します。

> **後方互換性**：`aiohttp.ClientSession` を直接使用する旧モジュール/アダプターは完全に影響を受けません。例外の変換は、`sdk.client` からリクエストを発生させた場合にのみ有効で、`aiohttp` を直接使用するコードは、`aiohttp.ClientError` などの元の例外をキャッチし続けます。両方の方法を共存させることができます。

### 例外階層

```
ErisPulseError
├── ClientError                  # HTTP/WS クライアントリクエスト例外の基底クラス
│   ├── ClientConnectionError    # 接続失敗 (DNS 解析失敗、接続拒否、ネットワーク不可)
│   ├── ClientTimeoutError       # 接続タイムアウトまたはリクエストタイムアウト
│   └── HTTPStatusError          # HTTP 4xx/5xx ステータスコードエラー
└── WebSocketError               # WebSocket 例外の基底クラス
    └── WebSocketDisconnect      # WebSocket 接続切断 (クライアントとサーバー共通)
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

# HTTP リクエスト例外の処理
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("サーバーに接続できません")
except ClientTimeoutError:
    print("リクエストがタイムアウトしました")
except ClientError as e:
    print(f"リクエストが失敗しました: {e}")

# WebSocket 例外の処理
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"接続が切断されました: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocket エラー: {e}")
```

### 統一的なキャッチ

`ClientError` を使用して、HTTP/WS クライアントリクエストのすべての例外を一括でキャッチします：

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"クライアントエラー: {e}")
```

### HTTPStatusError

リクエスト後にステータスコードを確認して例外をスローする必要がある場合、手動で使用できます：

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## アダプターでの使用

アダプターはグローバルクライアントまたは独自のクライアントインスタンスを使用して、プラットフォームAPIリクエストを送信できます：

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
            self.logger.error(f"API 調用が失敗しました: {e}")
            raise
```

> `from ErisPulse import sdk` を使用して `sdk.client` を使うこともできます。効果は同じです。

## 最適な実践

1. **グローバルクライアントを優先する**：`from ErisPulse.Core import client` を使用してグローバルシングルトンを取得し、フレームワークによる統一的な管理と監視が可能
2. **aiohttp の直接インポートを避ける**：`client` を使用して `aiohttp.ClientSession` を代用し、将来の下層実装の変更に伴うコード変更を必要としない。旧コードは直接 aiohttp を使用しても正常に動作し、両方の方法を共存させることができる
3. **ErisPulse 例外体系を使用する**：`sdk.client` からリクエストする際は `aiohttp.ClientError` ではなく `ClientError` をキャッチし、特定の HTTP ライブラリに依存しないコードを保証する。直接 aiohttp を使用する旧コードは影響を受けない
4. **適切なタイムアウトを設定する**：API の応答速度に応じて適切なタイムアウト時間を設定し、長時間のブロッキングを防ぐ
5. **リトライメカニズムを使用する**：不安定な API にはリトライを有効にして信頼性を高める
6. **リクエスト統計を監視する**：`sdk.client.stats` または `client.request` ライフサイクルイベントを使用してリクエスト状況を監視する
7. **WebSocket では高レベルメソッドを使用する**：`iter_text` / `iter_json` などの高レベルメソッドを優先し、メッセージの種類を識別する必要がある場合にのみ `iter_messages` を使用する



### SQL 查询构建器

# SQL クエリビルダ

> [!TIP]
> **このドキュメントを読むタイミング**：チェーン式の SQL クエリやカスタムストレージバックエンドが必要な場合。不要な場合はスキップしても、他の機能の使用に影響はありません。

ErisPulse の Storage モジュールは、チェーン式の呼び出しスタイルを採用した汎用的な SQL クエリビルダを提供し、カスタムテーブルの作成、クエリ、更新、削除操作をサポートしています。

## 架構設計

```
Bases/storage.py                    Core/storage.py
┌─────────────────────┐             ┌──────────────────────────┐
│  BaseStorage (ABC)  │◄────────────│  StorageManager          │
│  BaseQueryBuilder   │             │  (backend dispatch:      │
│    (ABC)            │             │   sqlite/mysql/postgres) │
└─────────────────────┘             │  SQLiteQueryBuilder      │
                                    │  AlterTableBuilder       │
                                    └──────────────────────────┘
```

- `BaseStorage` / `BaseQueryBuilder` は抽象基底クラスで、統一されたインターフェースを定義します。フレームワークには、SQLite / MySQL / PostgreSQL の 3 種類の実装が内蔵されています（カスタムバックエンドもこの方式で拡張可能です。詳しくは[ストレージバックエンド](storage-backends.md)をご覧ください）。
- `StorageManager` は `ErisPulse.storage.backend` 設定に従って具体的なバックエンドをスケジュールします。デフォルトは SQLite で、完全に後方互換性があります。

## 導入

```python
from ErisPulse import sdk
# または
from ErisPulse.Core import storage

# ABC 基底クラス（型注釈またはカスタム実装用）
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## テーブル管理

### テーブル作成

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
    print("users テーブルは既に存在しています")
```

### テーブル削除

```python
sdk.storage.DropTable("users")
```

### テーブル構造の変更

```python
# 列の追加
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()

# テーブル名の変更
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# 連鎖的な複数操作
sdk.storage.AlterTable("users") \
    .AddColumn("phone", "TEXT") \
    .AddColumn("address", "TEXT") \
    .Execute()
```

## チェーン呼び出しによるクエリ

### データの挿入

```python
# 単一行挿入（辞書を渡す）
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# バッチ挿入（辞書のリストを渡す）
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35},
    {"name": "Dave", "age": 40}
]).Execute()
```

### データの取得

> **重要**：`Select()` は `list[tuple]`（タプルのリスト）を返します。辞書ではなく、列の順序に従ってインデックスでアクセスする必要があります。

```python
# 全列を取得
rows = sdk.storage.Table("users").Select().Execute()
# rows: [(1, "Alice", 30), (2, "Bob", 25), ...]

# 指定列を取得
rows = sdk.storage.Table("users").Select("name", "age").Execute()
# rows: [("Alice", 30), ("Bob", 25), ...]

# インデックスで値を取得
for row in rows:
    name = row[0]   # "Alice"
    age = row[1]    # 30
```

#### タプルを辞書に変換

`ToDict()` をチェーン内で呼び出すことを推奨します。SELECT の結果は自動的に辞書で返されます（列名 → 値）：

```python
# ToDict チェーン：結果は list[dict] で、列名はクエリメタデータから自動取得（SELECT * に対しても同様）
rows = sdk.storage.Table("users").Select("name", "age").ToDict().Execute()
# rows: [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}, ...]

for row in rows:
    print(row["name"], row["age"])

# ExecuteOne でも同様に有効
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ToDict() \
    .ExecuteOne()
# row: {"name": "Alice", "age": 30} または None
```

> `ToDict()` はチェーン呼び出しのマーカー（self を返す）です：`ToDict()` を呼び出さないチェーンは元の `list[tuple]` の振る舞いを保ち、完全に後方互換性があります。`copy()` はこのマーカーを保持します。

手動で zip を使用する方法（ToDict と同等、チェーンを変更できない場合に適しています）：

```python
columns = ["id", "name", "age"]
rows = sdk.storage.Table("users").Select(*columns).Execute()

# 方法1：ループ内で zip
for row in rows:
    record = dict(zip(columns, row))
    print(record["name"], record["age"])

# 方法2：一度に辞書のリストに変換
records = [dict(zip(columns, row)) for row in rows]
```

#### 単一行の取得

```python
row = sdk.storage.Table("users").Select("name", "age") \
    .Where("id = ?", 1) \
    .ExecuteOne()

# row は tuple または None
if row is not None:
    name = row[0]  # "Alice"
    age = row[1]   # 30
```

### 条件フィルタ

> `Where(condition, *params)` は、複数のパラメータを渡すことで、複数の `?` プレースホルダに対応します。

```python
# 単一条件（1つのプレースホルダ、1つのパラメータ）
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 18) \
    .Execute()

# 1つの Where で複数のプレースホルダを使用
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ? AND age < ?", 20, 40) \
    .Execute()

# Where を複数回呼び出す（AND で連結）
rows = sdk.storage.Table("users").Select("name") \
    .Where("age > ?", 20) \
    .Where("age < ?", 40) \
    .Execute()
```

### ソート、ページング

```python
# 昇順
rows = sdk.storage.Table("users").Select("name", "age") \
    .OrderBy("name") \
    .Execute()

# 降順
rows = sdk.storage.Table("users").Select("name") \
    .OrderBy("age", desc=True) \
    .Execute()

# ページング
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

`copy()` を使用してビルダーを深くコピーし、基本条件を再利用します：

```python
base = sdk.storage.Table("users").Where("age > ?", 20)

# 同じ条件に基づいてクエリを実行
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

チェーン呼び出しはトランザクションを完全にサポートします：

```python
# トランザクションをコミット
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
# Alice のレコードは依然として存在します
```

## 非同期のネイティブ API

2.8.0 以降、ストレージ層は非同期をネイティブの主インターフェースとしています。すべての終端メソッドには、`a` が付いた非同期版が用意されており、非同期ハンドラ内ではイベントループのブロッキングを避けるために推奨されます：

```python
# 非同期トランザクション
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.aset("key2", {"nested": True})

# 非同期チェーンクエリ
rows = await sdk.storage.Table("users").Select("name", "age").ToDict().aExecute()
row = await sdk.storage.Table("users").Select("*").Where("id = ?", 1).aExecuteOne()
total = await sdk.storage.Table("users").Where("age > ?", 18).aCount()
exists = await sdk.storage.Table("users").Where("name = ?", "Alice").aExists()

# 非同期 KV
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()
```

| 同期（互換層） | 非同期ネイティブ |
|------|------|
| `get` / `set` / `delete` | `aget` / `aset` / `adelete` |
| `get_all_keys` / `clear` | `aget_all_keys` / `aclear` |
| `get_multi` / `set_multi` / `delete_multi` | `aget_multi` / `aset_multi` / `adelete_multi` |
| `transaction()` | `atransaction()` |
| `CreateTable` / `DropTable` / `HasTable` | `aCreateTable` / `aDropTable` / `aHasTable` |
| `Execute` / `ExecuteOne` / `Count` / `Exists` | `aExecute` / `aExecuteOne` / `aCount` / `aExists` |

## 戻り値の説明

| 操作 | 戻り値の型 | 説明 |
|------|---------|------|
| `Select().Execute()` | `list[tuple]` | タプルのリスト、列の順序で並べ替え |
| `Select().ExecuteOne()` | `tuple \| None` | 単一行のタプルまたは None |
| `Insert().Execute()` | `int` | 受影響された行数 |
| `InsertMulti().Execute()` | `int` | 挿入された行数 |
| `Update().Execute()` | `int` | 受影響された行数 |
| `Delete().Execute()` | `int` | 受影響された行数 |
| `Count()` | `int` | 一致する行数 |
| `Exists()` | `bool` | 存在するか |

### 戻り値の処理例

```python
# Select はタプルを返し、インデックスで値を取得します
rows = sdk.storage.Table("users").Select("name", "age").Execute()
first_name = rows[0][0]  # 最初の行、最初の列 name
first_age = rows[0][1]   # 最初の行、2番目の列 age

# 推奨：列名リスト + zip を使って辞書に変換、コードの可読性が向上
cols = ["name", "age"]
rows = sdk.storage.Table("users").Select(*cols).Execute()
for row in rows:
    d = dict(zip(cols, row))
    print(d["name"], d["age"])

# ExecuteOne は単一行のタプルまたは None を返します
row = sdk.storage.Table("users").Select("name").Where("id = ?", 1).ExecuteOne()
name = row[0] if row else None

# Insert/Update/Delete は影響された行数を返します
affected = sdk.storage.Table("users").Delete().Where("age < ?", 18).Execute()
print(f"削除されたレコード数: {affected}")
```

## パラメータ化されたクエリ

すべての WHERE パラメータは `?` プレースホルダを使用し、パラメータは `Where()` の追加引数として渡します（**タプルやリストではありません**）：

```python
# 正しい ✓ — 複数のパラメータを個別に渡す
sdk.storage.Table("users").Where("age > ? AND name = ?", 18, "Alice").Execute()

# 正しい ✓ — Where を複数回呼び出す
sdk.storage.Table("users").Where("age > ?", 18).Where("name = ?", "Alice").Execute()

# 間違っている ✗ — タプルを渡さないでください
sdk.storage.Table("users").Where("age > ? AND name = ?", (18, "Alice")).Execute()
# これはタプル全体を最初のプレースホルダの値として扱います

# 間違っている ✗ — SQL インジェクションのリスクがあります
sdk.storage.Table("users").Where(f"name = '{user_input}'").Execute()
```

### Where パラメータの渡し方

```python
# Where(condition: str, *params: Any)
# params は可変引数で、個別に渡します

# 単一パラメータ
.Where("name = ?", "Alice")

# 複数パラメータ
.Where("age > ? AND age < ?", 18, 60)

# LIKE クエリ
.Where("name LIKE ?", "A%")

# IN クエリ（プレースホルダを手動で構築する必要があります）
.Where("name IN (?, ?, ?)", "Alice", "Bob", "Charlie")
```

## カスタムストレージバックエンド

2.8.0 以降、抽象層は**非同期メソッドをネイティブ契約**としています：`BaseStorage` を継承して非同期抽象メソッドを実装し、同期 `get/set/Execute` などは基底クラスが自動的にブリッジで提供します：

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

class MyQueryBuilder(BaseQueryBuilder):
    async def aExecute(self):
        # 実際の実行ロジックを実装
        ...

    async def aExecuteOne(self):
        ...

    async def aCount(self):
        ...

    async def aExists(self):
        ...


class MyStorage(BaseStorage):
    async def aget(self, key, default=None):
        ...

    async def aset(self, key, value):
        ...

    # 他の非同期抽象メソッドとトランザクション接続のフックを実装 ...
    def Table(self, table_name):
        return MyQueryBuilder(self, table_name)
```

> [!TIP]
> トランザクション接続ルーティング（`conn` キーワード引数）を実装したくない場合は、クラス属性を
> `_SUPPORTS_CONN_ROUTING = False`（デフォルト）のままにしておけば、トランザクション機能は使用可能ですが、隔離性は制限されます。
> 純粋な SQL バックエンドの場合は、`Core/Bases/sql_base.py` の `SQLStorageBase` +
> `SQLQueryBuilder` を直接継承し、接続管理と方言の実行フーニャーを提供するだけで済みます。詳しくは
> [ストレージバックエンド](storage-backends.md)を参照してください。



### 懶加载系统

# ラグロードモジュールシステム

> [!TIP]  
> **この記事を読む必要があるタイミング**：ラグロードモジュールを使用する場合、または activate_on イベント駆動型のアクティベーションを使用する場合。それ以外の場合はスキップしても、他の機能の使用に影響はありません。

ErisPulse SDK のラグロードモジュールシステムは、モジュールの初期化を**実際にアクセスされたタイミングまで遅らせます**。起動フェーズではプレースホルダーエージェントのみを登録し、使用されなかったモジュールは起動時間やメモリを占有しません。

## 概要

ErisPulse のコア機能の 1 つである遅延ロードモジュールシステムは、以下の方法で動作します。

- **遅延初期化**：モジュールは、初めてアクセスされたときにのみ実際に読み込まれ、初期化されます。
- **透明な使用**：開発者にとって、遅延ロードモジュールは通常のモジュールと使用上ほとんど違いがありません。
- **自動依存管理**：モジュールの依存関係は、使用されるときに自動的に初期化されます。
- **ライフサイクルサポート**：`BaseModule` を継承したモジュールに対しては、ライフサイクルメソッドが自動的に呼び出されます。

## 動作原理

### LazyModule クラス

ラグジュアリー・ロード・システムの中心となるのが `LazyModule` クラスです。これは、最初にアクセスされたときにのみモジュールを実際に初期化するラッパーです。

### 初期化プロセス

モジュールが初めてアクセスされたとき、`LazyModule` は以下の操作を実行します：

1. モジュールクラスの `__init__` パラメータ情報を取得します
2. パラメータに基づいて `sdk` リファレンスを渡すかどうかを決定します
3. モジュールの `moduleInfo` 属性を設定します
4. `BaseModule` を継承したモジュールの場合、`on_load` メソッドを呼び出します
5. `module.init` ライフサイクルイベントをトリガーします

## イベント駆動型遅延起動（activate_on）

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

`lazy_load=True` のモジュールはデフォルトで**最初の属性アクセス時**にのみロードされます。モジュールがコマンド/イベントハンドラを登録している場合、従来の方法では `lazy_load=False` として即時ロードするしかありませんでした。`activate_on` は第三の選択肢を提供します：**トリガを宣言し、最初の一致するイベント/コマンドが到着した時点でモジュールを自動的にアクティブ化する**——メモリに常駐させることなく、トリガのエントリポイントを失うこともありません。

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,
            activate_on=[
                # ---- イベントトリガ（受動的到着、ユーザーの意識を必要としない）----
                "message",                                    # タイプレベル：任意のメッセージイベント
                {"notice": "group_member_increase"},          # タイプ + 単一 detail_type
                {"message": ["private", "group"]},            # タイプ + 複数 detail_type

                # ---- コマンドトリガ（能動的入力、Help に表示されるプレースホルダーコマンド）----
                {"command": "roll"},                          # 簡易表記：コマンド名
                {"command": ["roll", "dice"]},                # コマンド名リスト
                {"command": {                                 # dict 形式で宣言（name は必須）
                    "name": "dice",
                    "help": "サイコロを振る",
                    "usage": "/dice",
                    "group": "娯楽",
                    "aliases": ["d"],
                    "hidden": False,
                }},
            ],
        )
```

### コマンド dict 形式の宣言パラメータ

dict 形式は `@command()` デコレータのユーザーレベルのパラメータを反映し、モジュールのロード前にプレースホルダーコマンドを登録するのに使用されます。

| パラメータ | 型 | デフォルト | 説明 |
|------|------|------|------|
| `name` | `str` | **必須** | コマンド名；`on_load` での `@command(name)` と一致する必要がある。一致しない場合、アクティブ化後にプレースホルダーが削除され、コマンドは存在しなくなる |
| `help` | `str` | フォールバックチェーン | Help に表示される説明；未宣言の場合、フォールバックチェーンから値を取得する（以下参照） |
| `usage` | `str` | 自動生成 | 使用法行；デフォルトは `{prefix}{name}` |
| `group` | `str` | `None` | コマンドグループ |
| `aliases` | `list[str]` | `[]` | 別名を同時に登録し、**別名の入力でもトリガとして機能する** |
| `hidden` | `bool` | `False` | `True` の場合、プレースホルダーコマンドも非表示（アクティブ化後の実際のコマンドの非表示の意味と一致）；コマンド名を知っているユーザーの入力でもトリガとして機能する |

**サポートされていない** `priority` / `permission` / `master`：プレースホルダーコマンドの役割はトリガの起動だけであり、権限チェックはアクティブ化後の実際のコマンドが実行する（プレースホルダー段階で権限チェックを行うと、「コマンド入力による起動」が無効になる）。

### 占位コマンドの Help フォールバックチェーン

モジュールがロードされていない場合、Help に表示されるコマンドの説明は以下の順序で取得されます（最初に見つかった値を使用）：

1. dict 形式で宣言されたコマンドレベルの `help`（最も正確）
2. モジュールの `get_meta()` の `description`
3. モジュールの `__description__` 属性
4. パッケージのメタデータの `Summary`（PyPI パッケージの概要）
5. 一般的なメッセージ：「このコマンドは遅延ロードモジュール X から来ています。初めて使用すると、モジュールが自動的にロードされます」

### トリガの意味

- **イベントスタブ**：対応するイベントマネージャーに非常に低い優先度（`ACTIVATION_STUB_PRIORITY`）で登録され、すべての通常のハンドラの後にバックアップとしてトリガされる。アクティブ化後、現在のイベントはモジュールの実際のハンドラに転送される
- **コマンドスタブ**：プレースホルダーコマンドを登録する。アクティブ化後、プレースホルダーは削除され、実際のコマンドがトリガを引き継ぐ
- **再入防止**：`asyncio.Lock` を使用して、並行トリガ時に一度だけアクティブ化されるように保証する
- **スコープフィルタリング**：スタブにはモジュールの所有者アイデンティティが含まれ、モジュールが Bot / セッション / プラットフォームに対して有効化されていない場合はトリガされない
- **失敗時の処理**：アクティブ化に失敗した場合はクールダウン期間（`ACTIVATE_RETRY_COOLDOWN_SECS`、30秒）に入る。クールダウン中はイベントが短絡的に処理され、繰り返し試行されない。クールダウン後に再トリガされると、自動的に再試行され、スタブは全期間保持される
- **重複排除**：同名のコマンドが簡易表記と dict 形式で混在して宣言された場合、重複は排除され（dict が優先される）。dict で `name` が欠落している、またはイベントの `detail_type` が dict として誤って記述された場合は警告が表示され、無視される

> アーキテクチャ図と完全な意味については、[アーキテクチャ概要](../architecture.md#イベント駆動型遅延起動activate_onトリガアーキテクチャ)を参照してください。

## 懒惰ロードの休眠（dormant_after）

> [!NOTE]
> この機能は ErisPulse **2.11.0+** が必要です。

長期間使用されていない遅延ロードモジュールに対して、フレームワークはその**休眠**を可能にします。これにより、実行時のリソース（タスク、接続、イベントの登録など）を解放しますが、遅延ロードプロキシと登録のスタブは保持されます。モジュールは「登録済みだがロードされていない」状態に戻り、次回の属性アクセス、`module.call`、`activate_on` イベントによって**透明に再起動**されます（再インスタンス化され、`on_load` が実行されます）。再起動のための API は一切不要です。休眠後のシステムの状態は、「一度も起動されていない」場合と完全に同一です。

### 宣言方法

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=True,
        dormant_after="30m",   # 30 分間の無使用で自動的に休眠；宣言しない場合は休眠しない（デフォルト）
    )
```

時間の指定は、コマンド管理の `cooldown` と同じ形式です（`90s` / `1h30m` / `1d`）。スクリーナーは固定間隔（60 秒）でスキャンを行い、実際の休眠時刻は閾値 + 最大でスキャン間隔分のずれがあります。また、手動で休眠させることも可能です：`await sdk.module.sleep("モジュール名")`。明示的な `unload` は完全なアンロード（遅延プロキシも削除）になります。

### 状態の継続

休眠前にフレームワークは `on_before_unload(reason="dormant")` をトリガーします（アンロードの最初のステップ、リソースはまだ有効）。モジュールは `sdk.storage` に状態を保存します。再起動後は `on_load` で状態を復元します：

```python
async def on_before_unload(self, event):
    if event["reason"] in ("dormant", "reload", "disable"):
        await self.sdk.storage.aset(f"{self._module_name}:counter", self._count)

async def on_load(self, event):
    self._count = await self.sdk.storage.aget(f"{self._module_name}:counter") or 0
```

### 意味と境界

- **依存先の安全性**：遅延モジュールの依存先は、永続的なプロキシ（`sdk.<Name>`）または `module.call` を通じてアクセスします。休眠前後で動作は一貫しています。直接に実際のインスタンスの参照を持つことは反パターンです（監査ツールで漏れが確認できます）。
- **イベントの到達**：休眠中のモジュールはイベントを受け取らなくなります。イベントによって再起動が必要なモジュールは、`activate_on` を同時に宣言してください（イベントが先に再起動し、その後転送されます）。「コマンドが反応しない」問題を調査する際は、モジュールが休眠状態にあるかどうかを確認してください。
- **再起動失敗時の自己修復**：再起動（再初期化）に失敗した場合、30 秒間のクールダウンに入り、クールダウン後に再びアクセスすると自動的に再試行されます。永久的に失敗することはありません。

## 懒惰ロードの設定

### グローバル設定

設定ファイルでグローバルな遅延ロードを有効または無効にします：

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true=遅延ロードを有効にする(デフォルト), false=遅延ロードを無効にする
```

### モジュールレベルの制御

モジュールは `get_load_strategy()` 静的メソッドを実装することで、ロード戦略を制御できます：

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """モジュールのロード戦略を返す"""
        return ModuleLoadStrategy(
            lazy_load=False,  # Falseを返すと即時ロード
            priority=100      # ロードの優先度、数値が大きいほど優先度が高い
        )
```

## ラグロードモジュールの使用

### 基本的な使い方

開発者にとって、ラグロードモジュールは通常のモジュールと使用方法にほとんど違いはありません：

```python
# SDKを介してラグロードモジュールにアクセス
from ErisPulse import sdk

# 以下のようにアクセスするとモジュールのラグロードがトリガーされます
result = await sdk.my_module.my_method()
```

### モジュールの取得の統一されたエントリーポイント

SDK属性、モジュールマネージャー属性を通じてアクセスする場合でも、`module.get()`で検索する場合でも、
「登録済みだがまだロードされていない」ラグロードモジュールに対しては、すべて同じラグロードプロキシが返り、
そのプロパティにアクセスすることで初めてモジュールの初期化がトリガーされます：

```python
# 3つの方法で取得できるのはすべてラグロードプロキシです（モジュールがロードされていない場合）、動作は一貫しており、ユーザーには透明です
sdk.my_module          # ロードをトリガーするエントリーポイント
sdk.module.my_module   # 同様にラグロードプロキシを返します
sdk.module.get("my_module")  # これもラグロードプロキシを返します。この操作自体はロードをトリガーしません

# プロキシの任意の属性にアクセスすることで、モジュールの初期化が実際に行われます
result = await sdk.my_module.my_method()
```

`module.get()`は**検索**用のインターフェースであり、ロードをトリガーしません：
- モジュールが既にロード済み → 実際のインスタンスを返します
- モジュールが登録済みだが未ロード → ラグロードプロキシを返します（プロパティにアクセスしたときに初期化されます）
- モジュールが未登録 → `None`を返します

明示的にロードをトリガーするには、`await sdk.load_module("my_module")`を使用してください。

### 非同期初期化

非同期初期化が必要なモジュールについては、まず明示的にロードすることを推奨します：

```python
# まずモジュールを明示的にロード
await sdk.load_module("my_module")

# その後モジュールを使用
result = await sdk.my_module.my_method()
```

### 同期初期化

非同期初期化を必要としないモジュールについては、直接アクセスできます：

```python
# 直接アクセスすると自動的に同期初期化されます
result = sdk.my_module.some_sync_method()
```

## 最佳実践

ロード戦略を選択する際は、以下の決定フローを参考にしてください。

```mermaid
flowchart TD
    A["モジュール宣言<br/>get_load_strategy()"] --> B{"起動時に即座に準備が必要か<br/>または高頻度でトリガーされるか？"}
    B -->|"はい"| C["lazy_load=False<br/>即時ロード"]
    B -->|"いいえ"| D{"コマンド / イベントハンドラを登録しているか？"}
    D -->|"はい"| E["lazy_load=True + activate_on<br/>イベント/コマンドが到着した際にアクティベート"]
    D -->|"いいえ"| F["lazy_load=True<br/>最初の属性アクセス時にロード"]
    C --> G["起動時に on_load() を呼び出す"]
    E --> H["stub を登録 → トリガー時にインスタンス化"]
    F --> I["LazyModule 代理"]
```

### 懒惰ロード（lazy_load=True）を使用することを推奨する場面

- 他のモジュールによって呼び出されるだけの受動的なユーティリティモジュール（例：データクエリモジュール、フォーマット変換器など）
- コマンド/イベントハンドラを登録しているが高頻度で使用されないモジュール — `activate_on` を使ってトリガを宣言し、最初の一致するイベント/コマンドが到着した際に自動的にアクティベートする。これにより、lazy_loadを放棄せずに済む。

### 懒惰ロードを禁止することを推奨する場面（lazy_load=False）

- 起動時に即座に準備が必要なモジュール（他のモジュールに基礎サービスを提供するコアモジュールなど）
- 高頻度でトリガーされるリスナー（各メッセージごとに処理が必要） — `activate_on` による転送には1回のアクティベートオーバーヘッドがあるため、高頻度の場面では即時ロードした方が直接的
- タイマータスクモジュール
- アプリケーション起動時に初期化が必要なモジュール

> `priority` パラメータは、即時ロードされるモジュール間の初期化順序を制御します。数値が大きいほど先に初期化されます。同じ優先度のモジュールは登録順にロードされます。

## 注意事項

1. モジュールが遅延ロードを使用している場合、ErisPulse内で他のモジュールによって一度も呼び出されない場合、そのモジュールは決して初期化されません。
2. モジュール内にEventの監視など、他のモジュールを積極的に監視するモジュールが含まれている場合、2つの選択肢があります：`activate_on` トリガーを宣言して遅延ロードを維持し、イベントが到達したときに自動的にアクティブ化するか、または即時ロードを必要とすることを宣言する（`lazy_load=False`）か、さもなければモジュールの正常な業務に影響を及ぼす可能性があります。
3. 特殊な要望がない限り、遅延ロードを無効にすることは推奨しません。そうしないと、依存管理やライフサイクルイベントなどの問題が生じる可能性があります。
4. `activate_on` のコマンド dict 声明において、`name` はモジュールの `on_load` で `@command()` によって登録された実際のコマンド名と一致する必要があります。一致しない場合、モジュールがアクティブ化された後にプレースホルダーコマンドが解除され、宣言と実装が一致しないコマンドは存在しません。



### 生命周期管理

# ライフサイクル管理

> [!TIP]
> **この記事を読むべきタイミング**：フレームワークのライフサイクルイベント（起動 / 加載 / 状態変化）をサブスクライブする必要がある場合。不要な場合はスキップしても、他の機能の使用に影響はありません。

> **この記事でわかること**：ライフサイクルイベントの登録 / トリガー / 定向配信メカニズム、4種類のトリガーAPIの違いと選択方法、フレームワークが事前に埋め込んだすべてのフックポイント（core / module / adapter / server / messageなど）のデータ形式。
>
> **この記事では扱わないこと**：モジュール自身が実装するライフサイクルメソッド（`on_load` / `on_unload`、[モジュール開発ガイド](../developer-guide/modules/getting-started.md)参照）；起動プロセスの各段階の詳細（[起動フローと手動制御](startup.md)参照）。

モジュールのロード失敗、設定の変更、メッセージの送信、コマンドの実行などの節目に通知を受け取り、独自のロジック（監査、統計、アラート、連動）を実行したい場合は、フレームワークのライフサイクルイベントをサブスクライブしてください。フレームワークは各重要な節点にフックポイントを埋め込んでおり、`@sdk.lifecycle.on("イベント名")` で一行で接続できます。本文末尾には、すべてのフックポイントの一覧が付いています。

システムは3種類のトリガー方法をサポートしています：
- `await lifecycle.emit("event", data)` — 精簡版、任意のデータを渡す（`to="Owner"` の場合、指定したオーナーにだけ配信）
- `lifecycle.emit_sync("event", data)` — 同期版（非非同期コンテキストで使用）
- `await lifecycle.submit_event("event", ...)` — 旧版と互換、標準イベント形式を自動構築

## イベント処理メカニズム

### ハンドラの登録

```python
from ErisPulse import sdk

# デコレータ形式
@sdk.lifecycle.on("module.load")
async def on_module_load(data):
    print(f"モジュールのロード: {data}")

# プログラミング形式での登録
sdk.lifecycle.register("module.load", on_module_load, priority=10)

# 登録解除
sdk.lifecycle.unregister("module.load", on_module_load)

# オーナーごとの一括登録解除（モジュール/アダプターのアンロード時にフレームワークが自動的に呼び出す）
removed = sdk.lifecycle.unregister_by_owner("MyModule")
print(f"クリーンアップされたライフサイクルフック: {removed} 個")
```

### 优先度

ハンドラは `priority` パラメータをサポートし、数値が大きいほど先に実行されます（モジュールローダーと同様）：

```python
@sdk.lifecycle.on("adapter.event.receive", priority=10)  # 最初に実行
async def first_handler(data):
    pass

@sdk.lifecycle.on("adapter.event.receive", priority=0)  # 後に実行
async def second_handler(data):
    pass
```

### 点式構造イベント

イベントをトリガーすると、その親イベントもトリガーされます：
- `module.load` をトリガーすると、`module` もトリガーされます
- `adapter.event.receive` をトリガーすると、`adapter.event` と `adapter` もトリガーされます

### ワイルドカード

`*` を登録することで、すべてのイベントをキャッチできます：

```python
@sdk.lifecycle.on("*")
async def on_anything(data):
    print(f"イベントを受信: {data}")
```

### 定向配信（emit to=）

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

`emit()` で `to` パラメータを指定すると、定向配信モードになります。イベントは、その所有者（owner）として登録されたハンドラにだけ配信されます（モジュールの `on_load` 内で登録されたフックは、自動的にそのモジュールに所属します）。他のモジュールやワイルドカード `*` ハンドラは感知しません。

```python
# 投递方：イベントは Chat モジュールが登録したフックにだけ配信
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")

# 訂閱方（Chat モジュール内）：同名フックを登録し、owner は登録時に自動的に記録される
@sdk.lifecycle.on("message_received")
async def on_message_received(data): ...

@sdk.lifecycle.on("message")   # 点式の親プレフィックスも同様に有効（owner でフィルタリング）
async def on_any(data): ...
```

- 対象の owner に登録されたフックがない場合 → イベントは**消費されない**（`has_handlers()` で事前に検出可能）
- `data` が dict の場合、自動的に `_trace_id` を含める（既存値を上書きしない）
- `emit_sync` / `submit_event` でも `to=` パラメータをサポート
- モジュール間通信の3層モデル（RPC / 定向 / ブロードキャスト）は [モジュール間通信](module-communication.md) を参照

### 一回限りの登録（once）

2.7.0 から、`lifecycle.once()` で登録したハンドラは**一度トリガーされると自動的に登録解除**されます。これは「初回完了」のような一回限りのフックに適しています：

```python
@sdk.lifecycle.once("core.init.complete")
async def on_first_ready(data):
    print("初回完了、以降はトリガーされない")
```

- `on()` と同じ優先度パラメータの意味（`priority` 数値が大きいほど先に実行）
- 自動的に登録解除され、手動で `unregister` する必要はない
- 同期/非同期ハンドラの両方をサポート

### 監視者検索（has_handlers）

ホットパスの短絡処理では、`has_handlers()` を使って監視者がいるかどうかを事前に判断し、不要なイベントのループやタスクのスケジューリングを避けることができます：

```python
if sdk.lifecycle.has_handlers("message.sending"):
    await sdk.lifecycle.emit("message.sending", send_ctx)
```

- 精確なイベント名、ワイルドカード `*`、親イベントの3つのマッチングをカバー
- 監視者がいない場合は `False` を返し、`emit` を安全にスキップできる

## フックブレークポイント一覧

プラットフォームからフレームワークに入った 1 件のメッセージが処理完了までに辿る、典型的なライフサイクルイベントのシーケンス：

```mermaid
sequenceDiagram
    participant P as プラットフォーム
    participant A as アダプター
    participant F as フレームワークコア
    participant M as モジュールハンドラー

    P->>A: ネイティブイベント到着
    A->>F: adapter.event.receive（最も早期）
    F->>F: event.pre_process（ハンドラー実行前）
    F->>M: ハンドラーへディスパッチ（コマンド/メッセージ/通知など）
    M->>M: command.matched / command.executed
    M->>F: event.reply()
    F->>F: message.sending（送信前）
    F->>A: SendDSL による送信
    A->>P: プラットフォームへ送信
    A->>F: message.sent（送信完了）
    F->>F: adapter.event.dispatched（ディスパッチ完了）
```

フレームワークには以下のフックブレークポイントが組み込まれており、ユーザーは `@sdk.lifecycle.on()` を使って任意のブレークポイントをリッスンし、カスタムロジックを実装できます。

### コア初期化

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `core.init.start` | SDK 初期化の開始 | `{}` |
| `core.init.stage` | 初期化の各段階の開始（バックグラウンドで発火） | `{"stage": str}`。値：`discovery` / `adapter_register` / `adapter_start` / `module_register` / `module_init` / `adapter_start_deferred` / `router_start` |
| `core.init.complete` | SDK 初期化の完了 | `{"duration": float, "success": bool, "stages": {stage: float}, "adapters": {"enabled": [str], "disabled": [str]}, "modules": {"enabled": [str], "disabled": [str]}, "error": str(失敗時のみ)}` |
| `core.uninit.complete` | SDK のアンイニシャライズ完了 | `{"duration": float, "success": bool, "adapters_closed": int, "modules_unloaded": int, "module_properties_cleared": int, "module_properties_to_clear": [str], "error": str(失敗時のみ)}` |

**例：起動進捗の表示**

```python
@sdk.lifecycle.on("core.init.stage")
def show_stage(data):
    print(f"[起動] フェーズに入りました: {data['stage']}")
```

### 設定変更

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `config.set` | 設定項目が変更された | `{"key": str, "old_value": Any, "new_value": Any}` |
| `config.updated` | config.toml の外部編集後にツリー全体の変更を検出 | `{"old_config": dict, "new_config": dict, "config_file": str}` |

**例：設定の監査**

```python
@sdk.lifecycle.on("config.set")
def audit_config(data):
    print(f"[監査] {data['key']}: {data['old_value']} -> {data['new_value']}")
```

### モジュールライフサイクル

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `module.register` | モジュールクラスがマネージャーに登録される | `{"module_name": str, "success": bool}` |
| `module.load` | モジュールのロード完了（インスタンス化成功）。失敗時は payload に `"error": str, "traceback": str` が追加で含まれる（失敗時の情報は `module.last_error(名前)` でも照会可能） | `{"module_name": str, "success": bool}` |
| `module.init` | モジュールの初期化完了（遅延ロードを含む） | `{"module_name": str, "success": bool}` |
| `module.before_unload` | アンロードパイプラインの最初のステップ（`on_unload` とリソース回収より前に実行。モジュールインスタンスフック `on_before_unload` も同時に発火） | `{"module_name": str, "reason": str}`。`reason` の値：`unload` / `reload` / `disable` / `cascade` / `dormant` |
| `module.sleep` | モジュールのスリープ完了（遅延ロード休眠：リソースは解放済み、アクセス時に自動的に復帰） | `{"module_name": str, "success": bool}` |
| `module.unload` | モジュールのアンロードまたは無効化（`disable` と `unload` は依存側に対等に通知され、`on_dependency_lost` の契約に「無効化」を含む） | `{"module_name": str, "success": bool, "reason": str}`。`reason` の値：`unload` / `reload` / `disable` / `cascade` / `dormant` |
| `module.rollback` | ホットリロード失敗時のロールバック完了（スナップショット復元 + 旧インスタンスの `on_load` 再実行後） | `{"module_name": str, "success": bool}`。`success` は `on_load` の再実行が成功したかを示す（False の場合、旧インスタンスはクリーンアップ済み状態のまま） |
| `module.reload` | モジュールのホットリロード完了（依存側のカスケードリロードを含む） | `{"module_name": str, "success": bool, "full": bool, "duration_ms": int}`。単一モジュールの場合は `"identity_changed": bool`（False = プロセス内で古いコードが実行されている可能性あり、C 拡張のキャッシュなど）と `"version_old": str, "version_new": str` も含まれる。全量リロード（`reload_all`）時は `module_name` が `"All"` となり、payload に `"results": dict[str, bool]` が追加で含まれる |

> **モジュールインスタンスフック `on_before_unload`**：`module.before_unload` イベントに対応するオプションのライフサイクルメソッドです。`event["reason"]` に呼び出しの目的が示されるため、リソース解放前に状態を `sdk.storage` に保存しておき、復帰 / リロード後に `on_load` で復元するのに適しています（遅延ロード休眠の状態継続はまさにこれに基づいています）。フックが失敗した場合は警告が出るだけで、アンロード処理はブロックされません。

### アダプターライフサイクル

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `adapter.load` | アダプターの登録完了 | `{"platform": str, "success": bool}` |
| `adapter.reload` | アダプターのコードレベル ホットリロード完了 | `{"adapter_name": str, "success": bool, "full": bool, "duration_ms": int, "identity_changed": bool, "version_old": str, "version_new": str, "was_started": bool, "source": str}`。`identity_changed=False` = プロセス内で古いコードが実行されている可能性あり |
| `adapter.rollback` | アダプターのホットリロード失敗時ロールバック完了（旧登録状態の復元後） | `{"adapter_name": str, "replayed": bool, "success": bool}`。`replayed=True` は旧インスタンスの `start()` を再実行済みであることを示し、`success` は再実行が成功したかを示す |
| `adapter.start` | アダプターの起動 | `{"platforms": [str]}` |
| `adapter.status.change` | アダプターの状態変化 | `{"platform": str, "status": str, "retry_count": int, "error": str(失敗時のみ)}`。status の全値：`starting` / `started` / `start_failed` / `stopping` / `stopped` / `stop_failed` / `skipped-dependency` / `disabled` |
| `adapter.stop` | アダプターの停止 | `{"platforms": [str]}` |
| `adapter.stopped` | アダプターの停止完了 | `{"platforms": [str]}` |
| `adapter.bot.online` | Bot オンライン | `{"platform": str, "bot_id": str, "info": dict, "status": str}` |
| `adapter.bot.offline` | Bot オフライン | `{"platform": str, "bot_id": str, "status": str}` |

### イベント受信と処理

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `adapter.event.receive` | 外部プラットフォームイベントの受信（最も早期） | `{"platform": str, "event_type": str, "raw_event_type": str}` |
| `adapter.event.blocked` | ミドルウェアによるイベント拒否（`False` を返す。イベントは破棄され、どのハンドラーにも渡されない） | `{"middleware": str, "platform": str, "event_type": str, "detail_type": str, "event": dict, "_trace_id": str}` |
| `adapter.event.dispatched` | イベントのディスパッチ完了 | `{"platform": str, "event_type": str, "raw_event_type": str, "onebot_handlers_count": int}` |
| `event.pre_process` | イベントハンドラー実行開始前 | `{"event_type": str, "platform": str, "detail_type": str}` |

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

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `message.sending` | メッセージ送信直前 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |
| `message.sent` | メッセージ送信完了 | `{"platform": str, "method": str, "detail_type": str, "target_id": str, "bot_id": str}` |

**例：メッセージ送信の監査**

```python
@sdk.lifecycle.on("message.sending")
def log_sending(data):
    print(f"[送信] -> {data['platform']}/{data['detail_type']}/{data['target_id']} via {data['method']}")
```

### コマンドシステム

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `command.matched` | コマンドがマッチし実行直前 | `{"command": str, "args": list[str], "platform": str, "user_id": str}` |
| `command.executed` | コマンド実行完了 | `{"command": str, "args": list[str], "platform": str, "user_id": str, "success": bool, "error": str(失敗時のみ)}` |

**例：コマンド統計**

```python
@sdk.lifecycle.on("command.matched")
def count_commands(data):
    print(f"[コマンド] /{data['command']} from {data['user_id']}@{data['platform']}")
```

### HTTP ルーティング

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `server.request` | HTTP リクエスト受信 | `{"method": str, "path": str, "client_ip": str, "request_id": str}` |
| `server.response` | HTTP レスポンス送信 | `{"method": str, "path": str, "status_code": int, "client_ip": str, "request_id": str}` |

> `request_id` は [X-Request-ID リクエスト相関 ID](router.md#请求关联-idx-request-id) です。クライアントのリクエストヘッダーを優先して使用し、なければ UUID を自動生成します。これを使ってリクエストとレスポンスの 2 つのイベントを関連付けることができます。

**例：リクエストログ**

```python
@sdk.lifecycle.on("server.response")
def log_http(data):
    print(f"[HTTP] {data['method']} {data['path']} -> {data['status_code']}")
```

### WebSocket

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `server.start` | ルーティングサーバーの起動 | `{"base_url": str, "host": str, "port": int, "success": bool, "error": str(失敗時のみ)}` |
| `server.stop` | ルーティングサーバーの停止 | `{}` |
| `server.websocket.connect` | WebSocket 接続の確立 | `{"path": str, "module_name": str, "client_ip": str}` |
| `server.websocket.disconnect` | WebSocket 接続の切断 | `{"path": str, "module_name": str, "reason": str, "error": str(例外時のみ)}` |

**例：WebSocket 接続モニタリング**

```python
@sdk.lifecycle.on("server.websocket.connect")
def on_ws_connect(data):
    print(f"[WS] 接続: {data['path']} from {data['client_ip']}")

@sdk.lifecycle.on("server.websocket.disconnect")
def on_ws_disconnect(data):
    print(f"[WS] 切断: {data['path']} ({data['reason']})")
```

### ストレージ接続状態

ストレージバックエンド接続プールの確立・障害・復旧（いずれもバックグラウンドで発火し、ストレージ操作をブロックしません）：

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `storage.ready` | ストレージバックエンドの接続プール準備完了（イベントループごとの最初のプール構築成功時） | `{"backend": str}` |
| `storage.unreachable` | 接続リトライを使い切りクールダウン期間に移行（期間中の操作は即座に失敗） | `{"backend": str, "error": str, "cooldown": float}` |
| `storage.recovered` | クールダウン終了後に再接続が成功し、ストレージが再び利用可能に | `{"backend": str}` |

**例：ストレージ障害アラート**

```python
@sdk.lifecycle.on("storage.unreachable")
def alert_storage_down(data):
    print(f"[アラート] ストレージバックエンド {data['backend']} に到達できません: {data['error']}、{data['cooldown']}秒後に自動再接続します")

@sdk.lifecycle.on("storage.recovered")
def notify_storage_back(data):
    print(f"[復旧] ストレージバックエンド {data['backend']} が利用可能に戻りました")
```

### HTTP クライアント

`sdk.client` のリクエストと接続イベント（いずれもバックグラウンドで発火）：

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `client.request.success` | HTTP リクエスト成功 | `{"method": str, "url": str, "status": int, "elapsed": float}` |
| `client.request.failed` | HTTP リクエストのリトライを使い切り最終的に失敗 | `{"method": str, "url": str, "error": str, "attempts": int, "elapsed": float}` |
| `client.ws.connect` | WebSocket 接続の確立 | `{"url": str}` |

### 国際化

| フック名 | 発火タイミング | データ |
|---------|---------|------|
| `i18n.language.changed` | フレームワーク言語の切替（`i18n.set_language`） | `{"language": str, "previous": str}` |

## 標準イベント定義

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.stage", "init.complete", "uninit.complete"],
    "module": ["load", "before_unload", "init", "sleep", "unload", "register", "reload"],
    "adapter": [
        "load", "start", "status.change", "reload", "stop", "stopped",
        "event.receive", "event.blocked", "event.dispatched",
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
    "config": ["set", "updated"],
    "storage": ["ready", "unreachable", "recovered"],
    "client": ["request.success", "request.failed", "ws.connect"],
    "i18n": ["language.changed"],
}
```

## 完全なAPIリファレンス

### 登録と解除

| メソッド | 説明 |
|------|------|
| `@lifecycle.on(event, *, priority=0)` | デコレータでハンドラを登録 |
| `lifecycle.register(event, handler, *, priority=0)` | プログラミングで登録 |
| `lifecycle.unregister(event, handler=None)` | ハンドラの登録解除（handler=Noneの場合は、該当イベントのすべてのハンドラを解除） |

### トリガー

| メソッド | 説明 |
|------|------|
| `await lifecycle.emit(event, data=None, *, to=None)` | 非同期でトリガー、ハンドラは**並列実行**（相互にブロックせず、返却時はすべて完了）、返り値は優先度順に連鎖的にdataを置き換え；`to` にオーナーを指定した場合は、特定のオーナーにだけ配信 |
| `lifecycle.fire(event, data=None, *, to=None)` | **バックグラウンドで発行（投げて即離）**：ハンドラはバックグラウンドタスクで並列実行、待機せず、返り値なし；ハンドラがいない場合はオーバーヘッドなし。高頻度ホットパスや観測イベント（`server.request` / `storage.ready`）に適する。停止シーケンスや順序依存消費（`config.set`）は `emit` を使う |
| `lifecycle.emit_sync(event, data=None, *, to=None)` | 同期でトリガー、非同期ハンドラは `create_task` でスケジュール |
| `await lifecycle.submit_event(event_type, *, source, msg, data, to=None, background=False)` | 旧版と互換、標準イベント形式を自動構築；`background=True` の場合は `fire` でバックグラウンドで発行 |

**4種類のトリガーAPIの比較**：

| メソッド | 呼び出し形態 | ハンドラの完了を待つか | 代表的な使用場面 |
|------|---------|------------------|---------|
| `emit` | `await`（非同期） | **待つ**——ハンドラは並列実行、完了時に返却、返り値は優先度順に連鎖的にdataを置き換え | 通常のトリガー；順序依存消費（`config.set`）や停止シーケンスは必ずこれを使う |
| `fire` | 直接呼び出し（同期で返却） | **待たない**——バックグラウンドタスクで並列実行、返り値なし；ハンドラがいない場合はオーバーヘッドなし | 高頻度ホットパスや観測イベント（`server.request` / `storage.ready`） |
| `emit_sync` | 直接呼び出し（同期） | 同期ハンドラは即時完了；非同期ハンドラは `create_task` でスケジュール（返り値は返せない） | 非非同期コンテキスト（同期コード）でイベントをトリガー |
| `submit_event` | `await`（非同期） | 待つ（`background=True` の場合は `fire` と同じで待たない） | 旧版と互換：`source` / `msg` / `timestamp` を自動構築する |

### ユーティリティ

| メソッド | 説明 |
|------|------|
| `lifecycle.start_timer(timer_id)` | タイマーの開始 |
| `lifecycle.get_duration(timer_id)` | 経過時間を取得（秒） |
| `lifecycle.stop_timer(timer_id)` | タイマーを停止し、経過時間を返す |
| `lifecycle.list_hooks()` | すべての登録されたフックとハンドラ数をリストアップ |
| `lifecycle.clear()` | すべてのハンドラとタイマーをクリア |

## モジュールでの使用例

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # 簡単なメッセージ統計を実装
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

## バックグラウンドタスクの帰属と自動キャンセル

> [!NOTE]
> この機能には ErisPulse **2.8.0+** が必要です。

モジュールが作成した asyncio バックグラウンドタスクが `on_unload` 内でキャンセルされないままだと、`self` への参照を保持し続けるためモジュールインスタンスが回収されなくなります（ホットリロード後に古いインスタンスが残留します）。フレームワークは以下のフォールバック機構を提供しています：

- **`self.spawn(coro)`**（モジュール内での推奨）：タスクは自動的にモジュール名に帰属し、モジュールのアンロード時にフレームワークが `on_unload` の**後**で終了していないタスクをフォールバックでキャンセルし、警告を記録します
- **`spawn_background(coro)`**（`ErisPulse.runtime`）：現在の `owner_scope` コンテキストを自動的にキャプチャします。`cancel_owner_tasks(owner)` で帰属ごとにキャンセルでき、`cancel_all_background_tasks()` は `sdk.uninit()` 用のフォールバックです
- **アダプター**：シャットダウン時にプラットフォーム名義のバックグラウンドタスクも同様にフォールバックでキャンセルします

**メインループ登録前のタスク**（2.12+）：`spawn_background()` と `run_main_loop()` は、利用可能なメインループがない場合に一時的なイベントループを作成する代わりに、ペンディングキュー（上限 `PENDING_TASK_QUEUE_MAX`、デフォルト 1024）に入るようになりました。`sdk.run()` がメインループを登録する際に、キューを一括してフラッシュします。キューが満杯の場合は新しいタスクを破棄して警告を発します。owner 指定のキャンセルでは、その owner のペンディングタスクも同時に削除されます。終了時にも滞留タスクが残っている場合は警告を発して破棄します。`run_main_loop()` はエンキューパスでは `None` を返します。

```python
async def on_load(self, event):
    # 推奨：バックグラウンドタスクには self.spawn() を使用。アンロード時にフレームワークが自動的にフォールバックでキャンセルします
    self.spawn(self._poll())

async def on_unload(self, event):
    # 細かな制御が必要なシナリオでは、引き続き自身でキャンセルし、終了処理の完了を待つことを推奨します
    if self._poll_task:
        self._poll_task.cancel()
        await asyncio.gather(self._poll_task, return_exceptions=True)

async def _poll(self):
    while True:
        await asyncio.sleep(60)
        ...
```

> [!IMPORTANT]
> フレームワークのフォールバックは**強制キャンセル**（`cancel_owner_tasks`）であり、`on_unload` が返された後に実行されます。そのため、グレースフルな終了処理が必要なタスク（flush バッファ、状態の永続化、接続のクローズ）は、`on_unload` 内で自身で `cancel()` + `await` を行って完了させる**必要があります**——フォールバックが終了処理を保持してくれるとは期待しないでください。フレームワークが保証するのは「`self` を保持するタスクが残留しないこと」だけであり、「グレースフルさ」は保証しません。結果を `await` する必要があるタスクは直接 `await` し、バックグラウンドタスクに投げないでください。

## 注意事項

1. **ハンドラは同期または非同期**：システムは自動的に正しく呼び出します
2. **データの伝達**：`emit()` モードでは、ハンドラが `None` 以外の値を返すと、後続のハンドラに渡される `data` を変更します
3. **イベント名の命名規則**：点式構造のイベント名を使用することを推奨し、親イベントの監視が容易になります
4. **エラーの隔離**：1つのハンドラの例外は他のハンドラの実行に影響しません
5. **同期トリガーの制限**：`emit_sync()` では非同期ハンドラは fire-and-forget でスケジュールされ、返り値は返せません
6. **ライフサイクルのクリーンアップ**：`sdk.uninit()` を呼び出すと、すべての登録されたハンドラとタイマーがクリアされます
7. **ロード優先性**：フレームワーク初期化段階でイベントを監視したい場合は、高優先度を設定し、遅延ロードを無効化することを推奨します



### 路由系统

# ルーティングマネージャー

> [!TIP]
> **この記事を読むタイミング**：HTTP / WebSocket / SSE ルーティング（接続プールによるブロードキャストを含む）が必要な場合。不要な場合はスキップしても、他の機能の使用に影響はありません。


ErisPulse ルーティングマネージャーは、HTTP および WebSocket ルーティングを一元的に管理し、複数アダプタのルーティング登録とライフサイクル管理をサポートします。内部では抽象層を介してラップされており、現在は FastAPI + Uvicorn が使用されています。

## 概要

ルーティングマネージャーの主な機能：

- **デコレータによるルーティング**：`@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` デコレータによる高速登録
- **自動注入**：ルーティングハンドラは FastAPI クラスをインポートする必要がなく、フレームワークが自動的に抽象オブジェクトを注入
- **ルーティンググループ**：プレフィックスとバージョン番号付きの `RouteGroup` をサポート
- **ルーティングミドルウェア**：glob パターンマッチングによるリクエストのインターセプト
- **リクエスト制限**：スライディングウィンドウによる制限
- **CORS サポート**：ワンクリックで CORS を有効化
- **セキュリティヘッダー**：自動的にセキュリティレスポンスヘッダーを追加
- **自動ドキュメント**：OpenAPI に基づくインタラクティブなドキュメント
- **WebSocket サポート**：WebSocket 接続の完全な管理、カスタム認証およびライフサイクルフック
- **ライフサイクル統合**：ErisPulse ライフサイクルシステムとの深層統合
- **SSL/TLS サポート**：HTTPS および WSS セキュア接続をサポート
- **ホームエントリ**：モジュールをルートルーティング `/` に登録し、国際化をサポートするショートカットボタン

## 抽象型

ErisPulse はサーバーサイドの抽象型を提供し、モジュールが FastAPI に直接依存しないようにします。

| 抽象型 | FastAPI に対応 | 説明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP リクエストのラッパー、インターフェースは完全に互換性があります |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket 接続のラッパー、ライフサイクルフックを追加 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket 接続切断の例外 |

> `WebSocketConnection` は `WebSocketConnectionBase` を継承し、クライアント側の WebSocket (`ClientWebSocket`) と同じ send/receive/iter/close インターフェースを共有します。クライアントとサーバー側の WebSocket は同じビジネスロジックコードを使用できます。
>
> `.raw` 属性を使用して、下層の FastAPI ネイティブオブジェクトにアクセスできます。FastAPI クラスを使用するコードも完全に互換性があります。

## デコレータによるルーティング（推奨）

### 登録形態：単引数（推奨）と二引数

デコレータによるルーティングは二つの形態をサポートし、**単引数を推奨**します。これはコマンド/イベントトリガーと一致し、名前空間は自動的に現在のモジュールに属します。

```python
from ErisPulse import router

# 単引数（推奨）：自動的にモジュール名/hello → 実際のパス /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# 単引数 WebSocket：@ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# 二引数：明示的にモジュール名を指定（ルールは変更なし、モジュール間/ツールコードの登録時に使用）
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> 単引数の形態は、モジュール/アダプタの**ロードコンテキスト**内で登録する必要があります（ロード時にフレームワークが自動的に属するモジュールを注入）。
> 属するコンテキストがない場所で呼び出すと、`ValueError` が発生し、明示的にモジュール名を渡すように通知されます。

### HTTP デコレータ

```python
from ErisPulse import router, HttpRequest

# 抽象型を明示的に注釈することもできます
@router.post("/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **自動注入ルール**：ハンドラの最初の引数が `request` または `req` であり、FastAPI の型注釈がない場合、フレームワークは自動的に `HttpRequest` を注入します。引数がない場合やリクエスト引数名でない場合は影響を受けません。

#### レスポンス返却の約束（2.10+）

ハンドラの返り値は**タプルの約束**（推奨の書き方、明確にステータスコードを制御）をサポートし、dict/str/Response は従来通りです。

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "token が無効です"}, 401
    # (body, status_code, headers) さらにレスポンスヘッダーも追加できます
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# または respond() ヘルパー関数を使用（message はレスポンス本体に自動的にマージされます）
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

パス/クエリパラメータは FastAPI のネイティブ注釈を使用できます（`item_id: int`、`page: int = 1`）。
ミドルウェアは[ルーティングミドルウェア](#ルーティングミドルウェア)のセクションを参照してください。

### WebSocket デコレータ

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# 基本的な WebSocket（単引数の形態）
@router.ws("ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# ライフサイクルフックを含む WebSocket
@router.ws("/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"ユーザー切断: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"接続エラー: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 認証付きの WebSocket（トークンは環境変数から読み込み、コード内にハードコードしないでください）
import os

async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    expected = os.environ.get("ERISPULSE_WS_TOKEN", "")
    return bool(expected) and token == expected

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocket ハンドラと認証ハンドラも自動注入がサポートされます。`WebSocketConnection` を取得するには、パラメータの注釈を必要としません。`fastapi.WebSocket` を注釈することも可能です。ただし、抽象型を使用することを推奨します。

### 接続の自動登録（接続プール、2.10+）

`@ws` / `@sse` で確立された接続は**デフォルトでフレームワークの接続プールに自動登録**されます（`track=False` で無効化）：
ハンドラ内では `ws.id` / `ws.join_group(...)` が使用でき、任意のモジュールで
`connections.list(namespace=...)` を使用して本モジュールの接続を確認し、グループにブロードキャストできます。
[接続プールとブロードキャスト](connections.md)を参照してください。

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

# 限流とドキュメント情報付き
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="データエンドポイント",
    tags=["API"],
)
```

### WebSocket 登録

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

**パラメータの説明：**

| パラメータ | 説明 | デフォルト値 |
|------|------|--------|
| `module_name` | モジュール名（必須） | - |
| `path` | WebSocket パス | - |
| `handler` | ハンドラ関数 | - |
| `auth_handler` | 認証関数、`False` を返すと接続が自動的に切断されます | `None` |
| `auto_accept` | 自動的に `accept()` するかどうか | `True` |

> **推奨**：`auth_handler` を使用して接続を確認するよう推奨します。`auto_accept` を `False` に設定するのは、接続フローを完全に制御する必要がある場合にのみ行います。

## WebSocket ライフサイクルフック

`WebSocketConnection` は切断とエラーのコールバックを提供し、手動の try/catch が不要です。

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # デコレータ方式で登録
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"切断理由: {reason}")

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

ミドルウェアは glob パターンでパスをマッチングできます：

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

## リクエスト関連 ID（X-Request-ID）

2.7.0 から、各 HTTP リクエストには `X-Request-ID` という関連 ID が付与され、ログ / リレーショナルトレースの連携に使用されます：

- **生成ルール**：クライアントが送信した `X-Request-ID` リクエストヘッダーを優先して使用（分散トレースの場面）。なければ、UUID を生成
- **レスポンスヘッダー**：レスポンスには `X-Request-ID` を返し、クライアントがリクエストとログを対応させるのに便利
- **ライフサイクルイベント**：`server.request` と `server.response` イベントのデータに `request_id` フィールドが追加

```python
# モジュールでリクエストイベントを監視し、request_id でリクエスト-レスポンスを連携
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

クライアントはトレースを跨いで ID をカスタマイズできます：

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## リクエスト制限

ルーティングに対してスライディングウィンドウアルゴリズムを使用してリクエスト制限を行います：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

リクエスト制限の形式：`{回数}/{時間ウィンドウ}`、例えば `10/minute`、`100/hour`。

## CORS 設定

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

Router はデフォルトで OpenAPI によるインタラクティブなドキュメントを有効にします：

```python
# ドキュメントを無効化
router.disable_docs()

# ドキュメント情報をカスタマイズ
router.set_docs_info(
    title="My API",
    description="API ドキュメント",
    version="1.0.0"
)
```

## パス処理

ルーティングパスは自動的にモジュール名をプレフィックスとして追加し、衝突を回避します：

```python
# モジュール "my_module" にパス "/api" を登録
# 実際にアクセスするパスは "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> ルーティングパス（モジュール名のプレフィックスを含む）は**大文字小文字を区別**します。登録時のモジュール名が大文字小文字で、実際のパスもその通りです：モジュール名が `Test` の場合、`/api` を登録した実際のパスは `/Test/api` となり、`/test/api` にアクセスすると 404 が返されます。

## システムルーティング

ルーティングマネージャーは以下のシステムルーティングを自動的に提供します：

### ヘルスチェック

```
GET /health
# 返り値:
{"status": "ok", "service": "ErisPulse Router"}
```

### ホームページ

```
GET /
# ErisPulse ブランドページを返す
```

ルートルーティング `/` は ErisPulse ブランドページを表示し、ダッシュボードの可用性を自動検出し、エントリーボタンを追加します。

## ホームエントリ

ルーティングマネージャーは外部モジュールがルートルーティング `/` にショートカットエントリーボタンを登録できるようにし、ユーザーがモジュールの管理ページにすばやくアクセスできるようにします。

### エントリーの登録

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

# 国際化をサポートする登録（i18n ディクショナリ形式）
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "私のパネル"},
    url="/mymodule/admin",
)
```

**パラメータの説明：**

| パラメータ | 型 | 説明 | 必須 |
|------|------|------|------|
| `name` | `str` / `dict` | ボタンの表示テキスト；`{"i18n": "key", "default": "テキスト"}` ディクショナリを渡すと国際化を使用 | はい |
| `url` | `str` | ボタンのリンク先 | はい |
| `icon_svg` | `str` | オプションの SVG イコン | いいえ |

### ダッシュボードの自動登録

`sdk.Dashboard` が利用可能であることが検出された場合、ルーティングマネージャーはダッシュボードボタンを自動的にエントリーリストの先頭に追加します。手動で登録する必要はありません。

## ライフサイクルの統合

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"サーバーが起動しました: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("サーバーが停止中です...")
```

## リクエストオブジェクトの高度なプロパティ

`HttpRequest` は `method` / `query` / `headers` / `json` / `body` の基本的な面に加え、
認証ミドルウェア、切断感知の長時間タスクなどでよく使用される高機能を透過します：

| プロパティ / メソッド | 説明 |
|-------------|------|
| `request.session` | セッション dict（セッションミドルウェアが必要）、リクエスト間で保持 |
| `request.auth` | 認証情報（認証ミドルウェアが書き込む） |
| `request.user` | 現在のユーザーオブジェクト（認証ミドルウェアが書き込む） |
| `request.url_for(name, **params)` | リバースルーティング：ルーティング名から URL を生成 |
| `await request.is_disconnected()` | クライアントが切断されたかどうか（SSE / 長時間タスクのループ終了に使用） |
| `request.raw` | 下層の Starlette リクエストオブジェクト（緊急対応、下節の互換性説明参照） |

## 緊急対応：router.app

`router.app` は下層の FastAPI アプリケーションインスタンスを直接公開します（遅延作成、最初のアクセス時に web スタックをロードし、コアルーティングを登録）。デコレータで表現できない状況をカバーします—サブアプリのマウント、グローバルミドルウェア、FastAPI エコシステムへの接続（StaticFiles / バックグラウンドタスクテンプレートなど）：

```python
from ErisPulse.Core import router
from starlette.staticfiles import StaticFiles

app = router.app
app.mount("/static", StaticFiles(directory="static"), name="static")
```

> [!WARNING]
> **互換性の境界**：`router.app` は緊急対応手段であり、安定した契約ではありません—取得するのは現在の web スタック（FastAPI/Starlette）のインスタンスです。フレームワークが将来的に下層の web 実装を移行した場合、`app` 内部構造（ミドルウェアの順序、Starlette 特定の API）に依存するコードは**破壊的変更**に遭遇します。優先的に `@router.http` / `HttpRequest` 抽象層（`request.raw` も同様）を使用し、`.app` の使用をモジュールの独立したアダプタ層に限定してください—移行時に 1 か所だけを変更すれば済みます。

## 最適実践

1. **優先的に抽象型を使用**：`fastapi.Request` / `fastapi.WebSocket` に依存しないように、`HttpRequest` / `WebSocketConnection` を使用
2. **自動注入を活用**：ハンドラの最初の引数を `request` または `req` とし、型注釈なしでも `HttpRequest` を取得できるように
3. **単引数形態を優先**：モジュールのロードコンテキストでは優先的に単引数形態（自動的に名前空間に属する）を使用；モジュール間/ツールコードの登録時は明示的にモジュール名を渡す
4. **ルーティンググループの使用**：同一モジュールの複数のルーティングは `group()` で整理
5. **セキュリティを考慮**：セキュアな操作には認証メカニズムとセキュリティヘッダーを実装
6. **適切なリクエスト制限**：高頻度のエンドポイントにはリクエスト制限を設定
7. **ライフサイクルフックの使用**：`@ws.on_disconnect` / `@ws.on_error` を使って WebSocket のエラーを処理し、手動の try/catch を避ける
8. **緊急対応の使用を限定**：`router.app` / `request.raw` は抽象層で表現できない場合にのみ使用し、依存を 1 箇所に限定し、フレームワークの下層移行時の適応範囲を最小限に抑える



### MessageBuilder 详解

# MessageBuilder 详解

> [!TIP]
> **この記事を読む必要があるのは**：複雑な / 複数のメッセージセグメントを構築する場合です。必要ない場合は飛ばしても、他の機能の使用に影響はありません。

`MessageBuilder` は ErisPulse が提供する OneBot12 標準のメッセージセグメント構築ツールであり、構造化されたメッセージ内容を構築するために使用します。`Send.Raw_ob12()` と併用します。

## 導入方法

`MessageBuilder` は以下の2つの導入方法をサポートしています（効果は同じで、1つ目の方法を推奨します）：

```python
from ErisPulse.Core.Event import MessageBuilder        # 推奨、パッケージからのエクスポート
from ErisPulse.Core.Event.message_builder import MessageBuilder  # モジュールを直接インポート
```

## 雙モードメカニズム

MessageBuilder は、Python の descriptor メカニズム（`__get__`）を用いて、クラスレベルとインスタンスレベルの異なる動作を実現する 2 つの使用モードを提供します。クラスからメソッドを呼び出す場合、`__get__` は静的メソッドの実行結果を返します。インスタンスから呼び出す場合、`self` を返すことで、メソッドチェーン（連鎖呼び出し）をサポートします。

### チェーン呼び出しモード（インスタンス）

`MessageBuilder()` をインスタンス化して使用し、各メソッドは `self` を返すため、連鎖呼び出し（メソッドチェーン）が可能で、最後に `.build()` を用いてメッセージセグメントのリストを取得します。

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

クラスから直接メソッドを呼び出すことで、各メソッドは直接メッセージセグメントのリストを返し、単一のメッセージセグメント構築に適しています。

```python
# build() を必要とせず、直接 list[dict] を返します
segments = MessageBuilder.text("你好！")
# [{"type": "text", "data": {"text": "你好！"}}]
```

## メッセージセグメントの種類

| メソッド | タイプ | データパラメータ | 説明 |
|------|------|---------|------|
| `text(text)` | text | `text` | テキストメッセージ |
| `image(file)` | image | `file` | 画像メッセージ |
| `audio(file)` | audio | `file` | 音声メッセージ |
| `video(file)` | video | `file` | 動画メッセージ |
| `file(file, filename?)` | file | `file`, `filename` | ファイルメッセージ |
| `mention(user_id, user_name?)` | mention | `user_id`, `user_name` | ユーザーを@でメンション |
| `at(user_id, user_name?)` | mention | `user_id`, `user_name` | `mention` の別名 |
| `reply(message_id)` | reply | `message_id` | メッセージへの返信 |
| `at_all()` | mention_all | - | 全員を@でメンション |
| `custom(type, data)` | 自定義 | 自定義 | 自定義メッセージセグメント |

## Send との連携

構築されたメッセージセグメントのリストは、`Send.Raw_ob12()` を使用して送信されます：

```python
from ErisPulse import sdk
from ErisPulse.Core.Event.message_builder import MessageBuilder

# チェーンで構築 + 送信
segments = (
    MessageBuilder()
    .mention("user123", "張三")
    .text(" こちらの画像をご覧ください")
    .image("https://example.com/photo.jpg")
    .build()
)
await sdk.adapter.myplatform.Send.To("group", "group456").Raw_ob12(segments)
```

### Event との連携（返信）

```python
from ErisPulse.Core.Event import command

@command("report")
async def report_handler(event):
    await event.reply_ob12(
        MessageBuilder()
        .text("📊 日報集計\n")
        .text("本日完了したタスク: 5\n")
        .text("進行中のタスク: 3")
        .build()
    )
```

## ツールメソッド

### copy()

現在のビルダーをコピーし、同じ基礎内容に基づいて複数のメッセージバリエーションを作成します：

```python
base = MessageBuilder().text("基礎内容").mention("admin")

# 同じプレフィックスに基づいて異なるメッセージを構築
msg1 = base.copy().text(" 変体A").build()
msg2 = base.copy().text(" 変体B").image("img.jpg").build()
```

### clear()

追加されたメッセージセグメントをクリアし、同じビルダーを再利用します：

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

## 自定义メッセージセグメント

`custom()` メソッドを使用してプラットフォーム拡張メッセージセグメントを追加します：

```python
# プラットフォーム固有のメッセージセグメントを追加
segments = (
    MessageBuilder()
    .text("フォームに記入してください：")
    .custom("yunhu_form", {"form_id": "12345"})
    .build()
)
```

> 自定义メッセージセグメントは、対応するプラットフォームのアダプターでのみ有効であり、他のアダプターは認識できないメッセージセグメントを無視します。

## 完整例

### 複数要素のメッセージ

```python
segments = (
    MessageBuilder()
    .reply(event.get_id())                    # 元のメッセージに返信
    .mention(event.get_user_id())             # 送信者を@する
    .text(" これはあなたのクエリ結果です：\n")             # テキスト
    .image("https://example.com/chart.png")   # 画像
    .text("\n詳細データは添付ファイルをご覧ください：")
    .file("https://example.com/data.csv", filename="data.csv")
    .build()
)
await event.reply_ob12(segments)
```

### 静的ファクトリ + チェーン混合

```python
# 単一のメッセージセグメントを迅速に構築
simple_msg = MessageBuilder.text("シンプルなテキスト")

# チェーンで複雑なメッセージを構築
complex_msg = (
    MessageBuilder()
    .at_all()
    .text(" 📢 お知らせ：")
    .text("今日の午後3時に会議があります")
    .build()
)
```



### Conversation 多轮对话

# Conversation 多輪対話

> [!TIP]
> **このドキュメントを読む必要があるのはいつですか**：多輪対話のステートマシンとチェックポイントの復元が必要な場合です。必要ない場合はスキップしても、他の機能の使用には影響しません。

1 つのコマンドで複数の質問をユーザーに連続して求める必要がある場合（登録時の情報収集、アンケート、設定のガイドなど）、`Conversation` を使用して、同じセッション内で「質問 → 回答を待つ → 検証 → 次のステップ」をつなげます。タイムアウトや再起動後も、チェックポイントから復元できます。

## 対話の作成

`Event` オブジェクトの `conversation()` メソッドを使用して作成します：

```python
from ErisPulse.Core.Event import command

@command("quiz")
async def quiz_handler(event):
    conv = event.conversation(timeout=30)

    await conv.say("🎮 知識クイズへようこそ！")

    answer = await conv.choose("第1問：Pythonの生みの親は誰ですか？", [
        "Guido van Rossum",
        "James Gosling",
        "Dennis Ritchie",
    ])

    if answer is None:
        await conv.say("タイムアウトしました。また次回お試しください！")
        return

    if answer == 0:
        await conv.say("正解です！")
    else:
        await conv.say("不正解です。正解は Guido van Rossum です")

    conv.stop()
```

## コア API

### say(content, **kwargs)

メッセージを送信し、`self` を返してメソッドチェーンを可能にします：

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
# 単純な待機
resp = await conv.wait()
if resp:
    text = resp.get_text()

# プロンプトを送信して待機
resp = await conv.wait(prompt="名前を入力してください：")

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

内蔵の確認用語：`はい/yes/y/確認/確定/好/ok/true/対/うん/行/同意/問題ない/可能/当然...`

内蔵の否定用語：`否/no/n/キャンセル/不/不要/行かない/cancel/false/間違った/間違った/別/拒否...`

### choose(prompt, options, **kwargs)

ユーザーが選択肢から選ぶのを待機し、選択肢のインデックス（0ベース）または `None` を返します：

```python
choice = await conv.choose("色を選択してください：", ["赤", "緑", "青"])
if choice is not None:
    colors = ["赤", "緑", "青"]
    await conv.say(f"選択した色は {colors[choice]} です")
```

ユーザーは番号（`1`/`2`/`3`）または選択肢のテキスト（`赤`）を入力して選択できます。

`options_format="auto"`（デフォルト）は、method に応じて自動的に内蔵のスタイルを選択します：Markdown→無序リスト、Html→順序付きリスト、その他→純粋なテキストリスト。
また、`"list"`、`"inline"`、`"md"`、`"html"`、またはカスタム関数もサポートします。

`merge_prompt=True` を使用して、プロンプトと選択肢を1つのメッセージに統合することもできます。また、オプション挿入位置を制御するプレースホルダ（デフォルトは `{options}`、`placeholder` でカスタマイズ可能）もサポートします：

```python
choice = await conv.choose(
    "## 選択してください\n{options}",
    ["オプションA", "オプションB"],
    method="Markdown",
    merge_prompt=True,
)

# カスタムプレースホルダ
choice = await conv.choose(
    "選択してください: [choices]",
    ["オプションA", "オプションB"],
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
| `validator` | 関数、Event を受け取り、bool を返す | なし |
| `retry_prompt` | 検証失敗時の再試行プロンプト | `"入力が無効です。再度入力してください"` |
| `max_retries` | 最大再試行回数 | 3 |
| `condition` | 関数、既に収集されたデータの辞書を受け取り、bool を返す | なし |

**条件付きフィールド**：`condition` を使用して、条件が満たされた場合にのみフィールドを収集する動的フォームを実現できます：

```python
data = await conv.collect([
    {"key": "has_car", "prompt": "車をお持ちですか？（はい/いいえ）"},
    {"key": "car_brand", "prompt": "車のブランドを入力してください",
     "condition": lambda d: d.get("has_car", "").lower() in ("はい", "yes", "y")},
])
```

### stop()

手動で対話を終了し、`is_active` を `False` に設定します：

```python
conv.stop()
```

### is_active

対話がアクティブかどうかを返します：

```python
if conv.is_active:
    await conv.say("対話はまだ進行中です")
```

## アクティブ状態の管理

```mermaid
stateDiagram-v2
    state "アクティブ" as active
    state "非アクティブ" as inactive
    [*] --> active: event.conversation()
    active --> active: say / wait / confirm / choose / collect
    active --> inactive: stop()
    active --> inactive: wait() タイムアウト
    active --> inactive: collect() タイムアウトまたは再試行回数超過
    inactive --> [*]
```

以下の状況で対話は自動的に非アクティブになります：

1. `stop()` メソッドを呼び出す
2. `wait()` がタイムアウトして `None` を返す
3. `collect()` がステップのタイムアウトまたは再試行回数超過で `None` を返す

非アクティブになった後、`wait`/`confirm`/`choose`/`collect` のすべてのインタラクションメソッドは即座に `None` を返し、ユーザーからの入力を待続しません。

## 分岐とジャンプ

### @conv.branch(name) デコレータ

`branch()` を使用して対話の分岐を登録し、`goto()` で分岐間をジャンプします：

```python
@command("menu")
async def menu_handler(event):
    conv = event.conversation(timeout=60)

    @conv.branch("main")
    async def main_menu():
        await conv.say("=== メインメニュー ===\n1. 本人情報\n2. 設定\n3. 終了")
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
        await conv.say("=== 本人情報 ===\n名前: Alice\n0. 戻る")
        resp = await conv.wait()
        if resp and resp.get_text().strip() == "0":
            await conv.goto("main")

    @conv.branch("settings")
    async def settings():
        await conv.say("=== 設定 ===\n1. 通知のオン/オフ\n0. 戻る")
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

各対話インスタンスには、分岐間で状態を共有するための `context` 辞書が内蔵されています：

```python
@conv.branch("step1")
async def step1():
    conv.context["username"] = resp.get_text().strip()
    await conv.goto("step2")

@conv.branch("step2")
async def step2():
    name = conv.context.get("username", "未知")
    await conv.say(f"こんにちは、{name}！")
```

### save() / resume() / clear_saved()

対話は永続化をサポートし、タイムアウトや中断後に復元できます：

```python
# 対話状態を保存する（通常は手動で呼び出す必要はありません、下記の「自動チェックポイント」を参照）
await conv.save()

# ... その後、同じセッションで復元する ...
conv2 = event.conversation()
if await conv2.resume():
    await conv2.say("お帰りなさい！以前の対話を続けましょう")
else:
    await conv2.say("以前の対話は見つかりませんでした")

# 保存された対話を削除する
await conv.clear_saved()
```

ストレージキーにはターゲットの次元が含まれます（`conversation:{platform}:{user_id}:{target_id}`）、同じユーザーの異なるセッション間の対話は互いに上書きされません。`resume()` 時に、ターゲットを含まない旧形式のアーカイブは自動的に移行されます。

## 自動チェックポイントと再起動時の復元

### 自動アーカイブ

フレームワークは以下のタイミングで自動的にチェックポイントを管理します。通常、`save()` を手動で呼び出す必要はありません：

| 時機 | 行動 |
|------|------|
| `goto()` / `start()` で分岐をジャンプする | 自動保存（現在の分岐 + context） |
| `stop()` / `wait()` タイムアウト / `collect()` 失敗 | 自動削除（対話の終端状態） |

### チェックポイント TTL

アーカイブにはタイムスタンプが付いており、`ErisPulse.interaction.checkpoint_ttl`（デフォルト 24 時間）を超えるアーカイブはクリーンアップされます：

- **惰性削除**：復元時にアーカイブが期限切れであることが判明した場合、自動的に削除されます
- **バックグラウンドの自動クリーンアップ**：フレームワークには定期的な GC タスクがあり、最初にチェックポイントを使用した後に惰性で起動され、期限切れのアーカイブを列挙して削除し、長期稼働時にストレージ内の期限切れのチェックポイントが無限に蓄積されることを防ぎます。自動的にクリーンアップされたアーカイブは、その後会話メッセージを受け取った場合、"チェックポイントなし"として扱われます

```toml
[ErisPulse.interaction]
checkpoint_ttl = 86400  # 秒
```

### 再起動時の自動復元

フレームワークが再起動した後、メモリ内の待機中のコルーチンは失われますが、チェックポイントは残ります。`register_resume_handler` を使用して**復元ファクトリ**を登録することで、フレームワークは再起動後にその会話の最初のメッセージを受け取ったときに自動的に対話を継続します：

```python
from ErisPulse.Core.Event.wrapper import Conversation

@Conversation.register_resume_handler()  # platform="onebot11" を渡すことでプラットフォームを限定することも可能
def make_conversation(event) -> Conversation:
    # ファクトリの役割：対話を再構築し、すべての分岐を再登録する
    conv = event.conversation(timeout=60)

    @conv.branch("menu")
    async def menu(conv, event):
        ...

    return conv
```

登録後、`menu` 分岐にあったユーザーが再起動前に最初のメッセージを送信した場合、フレームワークは自動的に：コンテキストを復元 → そのメッセージを認証 → 保存された分岐から対話を継続します。ファクトリを登録していない場合、このメカニズムは無駄なコストがかかりません。

### 復元は即座に引き継ぎ

`resume()` が成功した場合、フレームワークは自動的に2つのことを完了します：

1. **セッションの引き継ぎ**：自動的にそのセッションの排他リースを取得します——他のモジュールは `sdk.interaction.get_owner_of(event)` を使用して「このユーザーが対話で占有されている」ことを感知できます；セッションが他のモジュールによって占有されている場合、復元は失敗（False を返す）し、2つの対話が競合することを防ぎます
2. **履歴の持ち込み**：会話の受信箱から最近の10件のメッセージを `conv.recent_history` に取り込みます（AI モジュールが復元された後、LLM のコンテキストが途切れません）；`resume(with_history=0)` でこの機能をオフにできます

```python
if await conv.resume(with_history=20):
    for m in conv.recent_history:
        print(m["role"], ":", m["text"])
```

### 手動復元（自動メカニズムを使用しない場合）

```python
@command("continue")
async def continue_handler(event):
    conv = event.conversation()
    # ... 分岐を登録する ...
    if await conv.resume():
        conv.goto(conv.get_current_branch())
```

## 代表的なフロー・パターン

### ガイド付き登録

```python
@command("register")
async def register_handler(event):
    conv = event.conversation(timeout=60)

    await conv.say("ようこそ、登録へ！")

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
        f"登録情報を確認しますか？\nユーザー名: {data['username']}\nメールアドレス: {data['email']}"
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
    await conv.say("対話モードに入りました。「終了」で終了します")

    while conv.is_active:
        resp = await conv.wait()
        if resp is None:
            await conv.say("タイムアウトしました。対話は終了します")
            break

        text = resp.get_text().strip()

        if text == "終了":
            await conv.say("さようなら！")
            conv.stop()
        elif text == "help":
            await conv.say("利用可能なコマンド：終了、help、status")
        elif text == "status":
            await conv.say("対話はアクティブです")
        else:
            await conv.say(f"あなたが言ったのは：{text}")
```



### 交互会话系统

# インタラクションセッションシステム

> [!TIP]
> **このドキュメントを読むべきタイミング**：wait_reply、マルチターン対話、タイマーリマインダー、セッション排他、リンクトレースが必要な場合。不要であれば読み飛ばしても、他の機能の利用には影響しません。

> **読み終えると分かること**：`wait_reply` の全パラメータの使い方とキャンセル理由、`.got()` による宣言的マルチターンチェーン、
> セッションタイマー（remind / escalate）、マルチパス待機（expect / select）とセッション排他リース。
>
> **本ドキュメントでは扱わない内容**：マルチターン対話の分岐ステートマシンと再起動復帰（[Conversation マルチターン対話](conversation.md) を参照）；
> 受信箱の保持ポリシー調整項目とランタイムオーバーライド（[セッション受信箱](transcript.md) を参照）。

> [!NOTE]
> 本章の内容には ErisPulse **2.8.0+** が必要です。

ErisPulse は「ユーザーとの継続的なインタラクション」をフレームワークレベルのインフラとして実装しています：1 つの `wait_reply` から、
タイマーリマインダー、マルチパス待機、セッション排他、再起動復帰に至るまで、すべてが統一された
**インタラクションセッションマネージャー**（`Core/Event/interaction.py`、`sdk.interaction`）によってスケジューリングされます。

{!--< tips >!--}
本ドキュメントが扱うすべての機能には**所有者（owner）**が備わっています：インタラクション待機、リース、タイマーはすべて
登録時のモジュール名を記録し、モジュールのアンロード / アダプターのシャットダウン時にはフレームワークが自動的にクリーンアップします。待機側はタイムアウトまで待ちぼうけるのではなく、直ちに通知を受け取ります。
これは所有権システムのインタラクション次元への拡張です（[所有権システム](ownership.md) を参照）。
{!--< /tips >!--}

## 返信待機：wait_reply

**ひとことで言うと**：現在のコルーチンを一時停止して対象ユーザーの次のメッセージを待ち、一致すれば返信イベントを返し、タイムアウトまたはキャンセル時は `None` を返します。`pattern` / `regex` / `validator` で不適切な返信をフィルタリングできます。

`wait_reply` はインタラクションセッションの基礎です——現在のコルーチンを一時停止し、対象ユーザーが次のメッセージで「返信」するのを待ちます。

```python
from ErisPulse.Core.Event import command

@command("ask")
async def ask_command(event):
    reply = await event.wait_reply(prompt="お名前を入力してください:", timeout=30)
    if reply is None:
        await event.reply("タイムアウトしました")
        return
    await event.reply(f"こんにちは、{reply.get_text()} さん！")
```

### 全パラメータ一覧

| パラメータ | 説明 | デフォルト |
|------|------|------|
| `prompt` | 一時停止前に送信されるプロンプトメッセージ | None |
| `timeout` | 待機タイムアウト（秒） | 60 |
| `pattern` | glob フィルタ（`*` / `?` / `[seq]`）、不一致時は待機を継続 | None |
| `regex` | 正規表現フィルタ（pattern と同時に指定した場合は両方の一致が必要）、不一致時は待機を継続 | None |
| `validator` | 検証関数（Event を受け取り bool を返す）、失敗時は待機を継続 | None |
| `callback` | 返信受信時に呼ばれるコールバック（戻り値方式の代わりとなるもう一つの書き方） | None |
| `method` | prompt の送信メソッド | "Text" |
| `session` | **セッションレベル待機**：同一セッション（グループ / チャンネル）内の誰の返信でも一致可能 | False |

```python
# 金額（数字）のみ受け付け、それ以外は待機を継続
reply = await event.wait_reply("金額を入力してください:", regex=r"\d+\s*円", timeout=30)

# セッションレベル待機：グループ協力シーンで、どのメンバーの回答でも一致可能
reply = await event.wait_reply(session=True, prompt="どなたか答えていただけませんか？")
```

### 待機とコマンドの境界（コマンドパススルー）

待機中に**登録済みコマンド**（例：`/cancel`）を含むメッセージを受信した場合、デフォルトではコマンドディスパッチャーにそのままパスされて実行され、
返信として消費されません（設定項目 `ErisPulse.event.wait_reply.cmdpass`、`True` にすると反転——
メッセージはすべて返信として扱われます）。判定テキストの基準はコマンドディスパッチと同一です：`alt_message` を優先し、
存在しない場合はメッセージセグメントの連結にフォールバックします（2.10.1 以降、純粋な message セグメントアダプターにも同様に適用されます）。

### 待機がキャンセルされるケース

待機はもはや「タイムアウトを待つだけ」ではありません——以下の場合、待機は**直ちに終了**し（`wait_reply` は `None` を返します）、
呼び出し元がタイムアウトまで待ちぼうけることはありません：

| トリガー | キャンセル理由（`InteractionCancelled.reason`） | 説明 |
|------|------|------|
| 所有モジュールのアンロード / 無効化 | `owner_unload` | 所有クリーンアップ：待機を登録したモジュールが消滅する際、一緒に回収される |
| アダプターのシャットダウン / 再起動 | `platform_stop` | そのプラットフォームで保留中の待機がすべてキャンセルされる |
| 同一セッションが新しい待機 / リースに置き換えられる | `conflict` | 下記「セッション調停」を参照 |
| 返信者がブラックリストに登録 / owner モジュールのバインド解除 | `revoked` | 返信一致時の**権限再チェック**：scope のアイデンティティ次元 + モジュール次元 |
| ユーザーの返信が一致 | —— | 通常パス。返信イベントを返す |

低レベルの例外は `InteractionCancelled`（`InteractionError` 例外体系に属します）です。
`wait_reply` はこれを `None` の返却に変換済みです。理由が必要な呼び出し元は
`sdk.interaction.register()` の低レベル API を直接使用できます。

### 返信一致の完全な判定チェーン

返信メッセージが到着すると、インタラクションマネージャーは以下の順序で判定します（コマンドマッチングの**前に**実行されます。
対話の連続性を優先——メッセージが他の高優先度ハンドラーに引き取られていても、保留中の対話は完結できます）：

```
セッションキーの一致（正確な user 次元 → セッションレベルへのフォールバック）
  → pattern / regex テキストフィルタ（不一致なら待機継続）
  → validator 検証（失敗なら待機継続）
  → 権限再チェック（scope のアイデンティティ次元 + owner のモジュール次元、失敗時は待機終了）
  → 待機側のウェイクアップ + イベントの引き取り（mark_processed）
```

## 宣言的マルチターン：`.got()` チェーン（2.11+）

`@command` は**マルチターンフロー制御プロキシ**を返し、`.got()` で収集ステップを順次宣言します——ステップ関数は
パラメータ名で収集済みの値（コマンド入口パラメータを含む）を受け取り、型は `type=` / アノテーションに従って自動解析されます。
低レベルでは Conversation にコンパイルされます：各ステップが 1 つの分岐、ジャンプ時にチェックポイントを自動保存し、**再起動後もユーザーの
返信は保存済みのステップから継続します**（復帰ファクトリはデコレート時に自動登録され、モジュールのアンロード時に自動的に登録解除されます）。

```python
@command("weather")
async def weather(event):
    pass  # 入口：最初の .got の prompt は自動送信されるため、手動で質問する必要なし

@weather.got("city", prompt="都市名を直接返信してください")
async def weather_city(event, city: str):
    await event.reply(f"{city}：晴れ、25℃")

@weather.got("days", prompt="何日分の予報？", type=int, retry_prompt="数字を入力してください")
async def weather_days(event, city: str, days: int):
    await event.reply(f"{city} の今後 {days} 日間……")
```

### パラメータ説明

| パラメータ | 説明 |
|------|------|
| `name` | 収集値の名前（後続のステップ関数に注入されるパラメータ名；フロー内で一意、重複宣言時は登録時にエラー） |
| `prompt` | そのステップに入る際に自動送信される質問 |
| `timeout` | ステップごとの待機タイムアウト（秒数または `"90s"` / `"1h30m"` の時間文字列、デフォルト 60s） |
| `type` | 値の型（`int` / `float` / `str`…；解析失敗時は `retry_prompt` を自動再送、最大 `max_retries` 回） |
| `validator` / `pattern` / `regex` | 返信のフィルタリングと検証（セマンティクスは [`wait_reply`](#返信待機wait_reply) と同一） |
| `session` | セッションレベル待機（同セッション内の誰でも一致可能） |
| `cmdpass` | コマンドパススルーの三状態（デフォルトでは `/cancel` などのコマンドは待機中も通常どおり実行される） |

### セマンティクスと境界

- **いずれかのステップでタイムアウト / 中断 → フロー全体が終了**し、チェックポイントがクリアされます（`wait_reply` と同じセマンティクス）；
  ステップ関数内ではいつでも `event.reply(...)` で中間結果を出力できます
- **同一ユーザーが同時に持てる保留中のインタラクションは 1 つだけ**——2 つ目のフローの待機が前のものを置き換えます
  （`InteractionCancelled("conflict")`）；排他制御が必要な場合は
  [セッションリース](#セッション排他acquire--hold--get_owner_of) を併用してください
- 収集値はフロー内にのみ存在します；再起動を跨いで複雑な状態を保持するオーケストレーションが必要な場合は、直接
  [Conversation](conversation.md) を使用してください（`context` + `branch/goto` + 手動チェックポイント）
- `@command` が返すのはプロキシオブジェクトです：呼び出し動作、`__name__`、docstring、カスタム属性は
  元の関数と完全に一致します；`command.unregister(プロキシ)` は自動的にアンラップします

## セッションタイマー：remind / escalate

「タイムアウト」を戻り値から、オーケストレーション可能なプリミティブへと変えます。タイマーはインタラクションセッションに紐付けられ、
モジュールのアンロード / アダプターのシャットダウン時に自動キャンセルされます。1 セッションあたりのアクティブな remind の上限は 5 個です。

### remind：返信がないとリマインド

```python
@command("ticket")
async def ticket_command(event):
    await event.reply("チケットを送信しました。処理結果はここで通知します")
    # 5 分間返信がなければ穏やかに 1 度催促；ユーザーの返信で自動的にキャンセルされる
    event.remind(300, "まだいますか？結果が出次第、すぐにお知らせします")
    reply = await event.wait_reply(timeout=3600)
    ...
```

- `event.remind(delay, text=None, *, callback=None)`：期限到来時に現在のセッションへ `text` を送信します
  （または `callback(event)` を実行、同期 / 非同期両対応）。**強制検証**：`text` と
  `callback` はどちらか一方のみ指定できます（どちらも指定しないと `ValueError` がスローされます）
- `Reminder` ハンドルを返します：`reminder.cancel()` で手動キャンセル、`reminder.expired` で状態照会
- ユーザーがそのセッションで**返信すると自動的にキャンセル**されます——これこそが「リマインド」のセマンティクスです：
  リマインドはユーザーが沈黙しているときにだけ現れます
- `Conversation` 内でも同様に利用可能：`conv.remind(120, "まだ考えていますか？")`

### escalate：時刻到来時に確実に実行されるエスカレーション

```python
event.escalate(1800, lambda e: notify_master(f"チケットが 30 分間未処理：{event.get_command_args()}"))
```

`remind` との唯一の違い：**ユーザーの返信ではキャンセルされない**——エスカレーションアクション（オーナーへの通知、有人対応への切り替え）は
「タイムアウト時に必ず届く」という約束であり、手動の `cancel()` / モジュールのアンロード / アダプターのシャットダウンでのみキャンセルされます。

| | `remind` | `escalate` |
|---|---|---|
| 期限到来時の動作 | テキスト送信 / callback 実行 | callback 実行 |
| ユーザーの返信 | **自動キャンセル** | 影響なし |
| 所有クリーンアップ（アンロード / プラットフォーム停止） | キャンセル | キャンセル |
| 1 セッションあたりの上限 | 5 | 無制限（所有クリーンアップが最終的なセーフティネット） |

## マルチパス待機：expect + select

**ひとことで言うと**：`expect` は期待を記述するだけで待機は登録せず、`select` が複数の期待をまとめて保留します。いずれかが先に一致した時点で `(インデックス, 返信イベント)` を返し、一致しなかったものは自動的にクリーンアップされます。

複数の期待を同時に保留し、**早い者勝ち**です——典型的なシーン：管理者の承認を待つと同時にユーザーの取り消しを待つ、
複数人による協調投票など。

```python
which, reply = await event.select(
    event.expect(pattern="承認*", user="10001"),
    event.expect(pattern="拒否*", user="10002"),
    event.expect(validator=lambda e: e.get_text() == "保留", session=True),
    timeout=60,
)
if which is None:
    await event.reply("60 秒以内に承認結果が届きませんでした")
elif which == 0:
    await event.reply("承認済み")
elif which == 1:
    await event.reply("拒否済み")
```

- `event.expect(...)` は**期待の記述**を構築します（待機は何も登録しません）：`pattern` / `regex` / `validator` / `user`（返信者を限定）/ `session`（誰でも回答可能）をサポートします
- `event.select(*expectations, timeout=60)`：一括登録 → いずれかが一致した時点で
  `(インデックス, 返信イベント)` を返す → 一致しなかった待機は自動キャンセル；すべてタイムアウトした場合は `(None, None)` を返します。
  **強制検証**：最低 1 つの expectation を渡す必要があり、そうでなければ `ValueError` がスローされます
- 一致したイベントはすでにフレームワークが引き取り済み（`mark_processed`）のため、他のハンドラーによって重複消費されることはありません

{!--< tips >!--}
`select` はマルチスレッドの `asyncio.wait` による手動オーケストレーションと比べて：期待が不一致のときの自動クリーンアップ、
一致イベントの自動引き取り、権限再チェックと所有クリーンアップがすべて有効——Future を自分で管理する必要はまったくありません。
{!--< /tips >!--}

> [!NOTE]
> 2.10.1 以降、`select` は**集約待機**となりました：すべての期待は単一エントリ + カスタム一致判定に統合され、
> 同一キーの複数パス（同じ user に異なる pattern を 2 つ登録するなど）が互いにキャンセルし合うことはなく、いずれかのパスが先に一致した時点で返ります。
> 返信テキストの判定基準は `alt_message` 優先 + メッセージセグメントへのフォールバック（コマンドディスパッチと同一）です。
>
> 境界に関する説明：`event.wait_for(...)` はアダプターのイベントバスに直接紐付けられ、ミドルウェアと
> detail_type の条件フィルタを**経由しません**（身元の受け入れ判定はディスパッチ入口で担保されます）；完全なパイプラインを必要とする待機には
> `wait_reply` / `select` を使用してください。

## セッション排他：acquire / hold / get_owner_of

所有権は「リソース」から「セッション」へと拡張されます——「このユーザーは現在誰に占有されているか」が第一級のクエリとなります。

```python
# 照会：このセッションは現在、誰が対話中か？（空きの場合は None を返す）
owner = sdk.interaction.get_owner_of(event)
if owner and owner != "MyModule":
    return  # 他のモジュールが対話中のため、邪魔しない

# 排他リース：セッションを独占（deny 戦略、占有中の場合は None を返す）
lease = sdk.interaction.acquire(event)          # デフォルト TTL は 1 時間、ttl= で指定可能
if lease is None:
    return  # すでに占有されている
try:
    ...  # 独占インタラクション
finally:
    lease.release()
```

コンテキストマネージャー形式（取得に失敗すると `SessionOccupiedError` がスローされます）：

```python
with sdk.interaction.hold(event) as lease:
    ...  # 抜ける際に自動解放
```

リースは `renew(ttl)` による延長をサポートします；TTL は遅延期限切れ方式——期限切れのリースは次回アクセス時に自動的にクリーンアップされます。

`Conversation.resume()` で対話を復帰する際、フレームワークは自動的にリースを取得します（
[Conversation マルチターン対話](conversation.md) の「復帰即引き継ぎ」を参照）——
復帰した対話は必然的にセッションを保持するため、他のモジュールが割り込むことはありません。

## セッション受信箱：event.history

> 保持ポリシー（7 日間 / 条数上限）とランタイムオーバーライド API、リスクと監査については[セッション受信箱](transcript.md)の専用ドキュメントを参照してください。

セッションごとの直近メッセージフローの統一記録（ユーザー + ボットの双方）で、AI コンテキスト、
リピート防止、行動分析系モジュールにとっての**共有ファクト基盤**です——各モジュールが個別に履歴を保存する必要はもうありません。

```python
messages = await event.history(20)   # 現在のセッションの直近 20 件、時刻昇順
for m in messages:
    print(m["role"], ":", m["text"])  # role: "user" / "bot"
```

- 自動記録：受信メッセージ（role=user）+ ボットの送信テキスト（role=bot）
- ストレージ：独立した SQLite テーブル、保持ポリシー = セッションごとの上限（デフォルト 50）+ グローバル TTL（デフォルト 7 日間）
- 書き込み方式：メモリバッファ + バックグラウンドでの一括ディスク書き込み（遅延は最大 1 秒）、照会インターフェースはディスク未書き込みのバッファ行を自動的にマージするため、同一プロセス内の「自分の書き込みの読み取り」は影響を受けません；正常終了時（`sdk.uninit` / プロセス終了）には自動的にフラッシュされます。**ハードクラッシュ / 強制終了時には直近約 1 秒分の記録が失われる可能性があります**：この基盤は直近コンテキストキャッシュとしての位置づけであり、監査レベルの永続化には適しません
- 設定：`ErisPulse.transcript = {enabled = true, max_per_session = 50, ttl_hours = 168}`
- マネージャー API：`sdk.transcript.append() / get() / clear()`、`aflush()` / `flush()` による手動フラッシュ

## メッセージトランザクション：message_tx

トランザクション内のすべての送信は自動的に台帳へ記録されます；**異常終了時には送信済みメッセージが逆順に自動取り消しされます**
（アダプターが `delete_message` を実装していない場合はスキップされますが、台帳への記録は通常どおり行われます）。

```python
async with event.message_tx():
    await event.reply("処理中です。お待ちください")
    result = await do_something()          # ここで例外がスローされると →
    await event.reply(f"完了: {result}")   # 直前の「処理中」が自動取り消しされる
```

トランザクション外の送信は台帳に記録されません（ゼロオーバーヘッド）；トランザクション内ではいつでもレシート台帳を読み取れます。典型的な用途は**自己削除ボット**
（送信と同時に遅延取り消しをスケジュール）と送信監査です：

```python
import asyncio
from ErisPulse.runtime import get_send_receipts

async def delayed_delete(adapter, message_id: str, delay: float):
    await asyncio.sleep(delay)
    await adapter.delete_message(message_id)

async with event.message_tx():
    await event.reply("一時的な通知")
    for r in get_send_receipts() or []:
        # 各レシートには platform / bot_id / message_id / trace_id が含まれる
        asyncio.create_task(delayed_delete(adapter, r["message_id"], 30))
```

レシートの読み取りは**トランザクションスコープ**です：`message_tx()` トランザクション内でのみ非 `None` を返し、
トランザクション外では常に `None` です；すべての送信（トランザクション外を含む）を捕捉する必要がある場合は `message.sending/sent`
フックを使用してください（[リンクトレース](#リンクトレースtrace-id) の `trace_id` フィールドを参照）。

## リンクトレース：trace-id

すべての受信イベントは自動的にトレース ID を取得し（`event["id"]` を再利用、欠落時は生成）、以下に渡って引き継がれます：

- ハンドラーコンテキスト（`get_current_trace_id()` で読み取り）
- 送信（`[Send]` ログ行に `[trace:...]` を付加、`message.sending/sent` フックの `trace_id` フィールド）
- ライフサイクルフックデータ（dict に `_trace_id` を自動補完）
- 宛先指定イベント（`lifecycle.emit(..., to=...)`）とメッセージトランザクションレシート

1 つのメッセージが複数のモジュールによってリレー処理される場合でも、チェーン全体を同一の ID で紐付けられます（ログ / スロークエリ / 監査）。

## 他のシステムとの関係

- **所有権**：待機 / リース / タイマーはすべて owner を記録し、アンロード時に即座に回収されます（[所有権システム](ownership.md)）
- **スコープ**：返信一致時の再チェックはアイデンティティ + モジュール次元；モジュール間呼び出しの監査は送信（アウトバウンド）次元で行われます（[スコープ](scope.md)）
- **Conversation**：マルチターン対話はインタラクションセッションの上に構築された分岐ステートマシンです（[Conversation](conversation.md)）。
  その待機も本ページのすべてのキャンセル / 再チェック / 所有セマンティクスを同様に享受します



### 模块间通信

# モジュール間通信

> [!TIP]
> **この記事を読むタイミング**：RPCによるモジュール間呼び出し、サービス契約、宛先指定イベント、またはコールドスタート時のイベントリプレイが必要な場合。必要なければ飛ばしても、他の機能の使用に影響はありません。

> **この記事を読んだ後には**：3層通信モデル（RPC / 宛先指定イベント / ブロードキャスト）の選択のコツ、`meta.services` によるサービス契約とサービスディレクトリ、出向き監査の設定方法、およびラグドウォーキングとコールドスタート時のイベントリプレイについて理解できます。
>
> **この記事では扱いません**：ライフサイクルイベントシステム自体の登録 / 発火 / 優先度のメカニズム（[ライフサイクル管理](lifecycle.md)を参照）；ラグドロードの設定と activate_on の宣言（[ラグドロードシステム](lazy-loading.md)を参照）。

> [!NOTE]
> 本章の内容は ErisPulse **2.8.0+** が必要です。

ErisPulse では、モジュール間には**3層の通信モデル**が存在し、「点対点 → 宛先指定 → ブロードキャスト」の順序で構成されています：

| 層 | API | 意味 | 代表的なシナリオ |
|---|---|---|---|
| **RPC** | `await sdk.module.call("Chat", "get_history", ...)` | 点対点のリクエスト-レスポンス、契約 / 監査 / タイムアウト付き | 他のモジュールの機能を呼び出す（履歴の取得、翻訳、返金など） |
| **宛先指定イベント** | `await lifecycle.emit("message_received", {...}, to="Chat")` | 指定されたモジュールが登録したライフサイクルフックにのみ配信 | 上流の状態変化を下流に通知する（「新しいメッセージを受け取りました」など） |
| **ブロードキャスト** | `await lifecycle.emit("config.updated", {...})` | フレームワーク全体で見えるライフサイクルイベント | 設定のホットアップデート、モジュールの起動 / 終了 |

{!--< tips >!--}
選択のコツ：**返り値が必要な場合は `call` を使い、特定のモジュールのフックに通知したい場合は `emit(..., to=...)` を使い、全員に通知したい場合は `emit(...)` を使う**。
{!--< /tips >!--}

## RPC: module.call

```python
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

`sdk.module.Chat.get_history(...)`（変更なし）の属性アクセスとの違いは以下の通りです：

| | `module.call()` | 属性アクセス |
|---|---|---|
| 目標が登録されていない / 有効になっていない | `ModuleNotAvailableError` をスロー | `AttributeError` をスロー |
| ラグジュアリーなモジュール | **自動的に起動**（イベント駆動モジュールはアクティベーションロックを通過） | 非同期初期化モジュールは `RuntimeError` をスロー |
| `current_owner` | **ターゲットモジュール**に帰属（内部の wait_reply / 送信 / ログは正しい帰属） | 呼び出し元に保持 |
| タイムアウト | 30秒（`timeout=` で上書き、None でタイムアウトなし） | なし |
| scope 審査 | 呼び出し元が出口のゲートを通過 `actions.<呼び出し元>.call` | なし |
| 契約検証 | `meta.services` のホワイトリスト | なし |

### エラー体系

```
ModuleError                      # モジュールシステムのエラー基底クラス
└── ModuleCallError              # 跨モジュール呼び出しの基底クラス（module / method 属性を含む）
    ├── ModuleNotAvailableError  # 目標が登録されていない / 有効になっていない / 起動に失敗
    ├── ServiceNotProvidedError  # メソッドが services ホワイトリストにない / 私的メソッド / 存在しない
    └── ModuleCallTimeoutError   # クロージャー関数がタイムアウト
```

すべて `ErisPulseError` 体系に属し、`from ErisPulse.Core import ModuleCallError` でキャッチ可能です。

## サービス契約: meta.services

サービス提供者は `get_meta()` で公開するホワイトリストを宣言します（`commands` と対称）：

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="チャット",
            services=[
                "get_history",                                       # 簡単な形
                {"name": "translate", "description": "テキストを指定された言語に翻訳する"},  # 説明付き
            ],
        )

    async def get_history(self, session_id, n=20): ...
    async def translate(self, text, target_lang): ...
    def _internal_helper(self): ...   # 下線付きメソッドは外部から呼び出し禁止
```

**開発者は無感覚なデフォルト**：

- `services` を宣言していない → **公開**メソッドはすべて `module.call()` で呼び出せる（属性アクセスと同様）、宣言は不要
- 宣言後 → ホワイトリストに絞られ、越境呼び出しは `ServiceNotProvidedError` をスロー——「これが外部に約束したメソッド」を明示する
- 制限の**主制御権はユーザー側**：`scope.actions` の設定が「誰が誰を呼び出せるか」を決定（後述の審査参照）、モジュール作者の `services` はサービス面の宣言に過ぎず、2つの層は互いに置換不可能

**サービス紹介**：各サービスに人間 / AI が読める説明を付ける——不要なら何も書かなくてよい、説明は**メソッドの docstring 首行**（フレームワークは docstring 形式を要求している）から自動取得：

```python
async def translate(self, text, target_lang):
    """テキストを指定された言語に翻訳する"""    # ← この行がサービス紹介として自動取得される
    ...
```

**パラメータ提示**：呼び出し元（特に AI エージェント）は各パラメータの意味を知る必要がある。不要なら何も書かなくてよい、提示はメソッドの docstring の **`:param:` 行**から自動取得：

```python
async def render_card(self, html, width=800, height=0):
    """HTMLを画像ファイルにレンダリングする

    :param html: レンダリングするHTMLテキスト          ← 自動的にパラメータ提示として取得される
    :param width: 画布の幅ピクセル、0は内容に応じて自動調整
    :param height: 画布の高さピクセル、0は内容に応じて自動調整
    """
```

微調整が必要な場合（docstring を上書き / 多言語対応）は dict 形式で `description` と `parameters` を宣言（両方とも i18n 辞書に対応；`parameters` は**パラメータ**と docstring をマージし、docstring が優先、宣言されたが存在しないパラメータはフィルタリングされる）：

```python
services=[
    {"name": "translate", "description": "テキストを指定された言語に翻訳する"},
    {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "会話の要約"}},
    {
        "name": "render_card",
        "description": "HTMLを画像ファイルにレンダリングする",
        "parameters": {"html": "HTMLテキスト", "width": "幅ピクセル、0は自動調整"},
    },
]
```

## サービスディレクトリ: services()

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': 'テキストを指定された言語に翻訳する',
#            'parameters': {'session_id': 'セッションID', 'n': '返却件数'}}]}

sdk.module.services("Chat")   # 指定されたモジュールのみを照会
```

- **明示的に `meta.services` を宣言したモジュール**のみをリストアップ（宣言していないモジュールはディレクトリに表示されない）
- 各サービスにはメソッドのシグネチャ文字列（`inspect.signature` から抽出）、説明文、パラメータ提示が付く
- **ラグジュアリーなモジュールもディレクトリに表示される**（サービス発見はロードより先に発生）——呼び出し元はこれにより、`call()` でターゲットモジュールを起動するかを判断できる
- トポロジーにも反映される：`sdk.module.get_topology()` の各モジュール項目に `services` フィールドが含まれる

{!--< tips >!--}
**MCP 化の道筋**：サービスディレクトリ（名前 + シグネチャ + 説明 + パラメータ提示）は MCP tool の形状に相当する——各サービスは自然に ``{"name", "description", "parameters"}`` になる。将来、フレームワークは ``services()`` を直接 MCP サーバエンドポイントとして公開し、AI がモジュールの能力を発見して呼び出せるようにする。また、``scope.actions.call`` 審査は AI 呼び出しのセキュリティゲートとして自然に機能する。
{!--< /tips >!--}

## 出力審査: 誰が誰を呼び出せるか

`module.call()` は**呼び出し元モジュール**の立場で scope の出力ゲートを通過する：

```toml
[ErisPulse.scope.actions.CallerModule.call]
deny = ["Chat.get_history"]        # CallerModule が Chat の get_history を呼び出すことを禁止
# allow = ["Chat.get_*"]           # またはホワイトリスト：get で始まるサービスのみを許可
```

- `name` の形式は `<ターゲットモジュール>.<メソッド名>`、正確な一致 / glob / `re:` 正規表現が可能
- フレームワーク層の呼び出し（owner コンテキストがない、例：起動スクリプト）は審査制約を受けない
- 拒否された呼び出しは `ModuleCallError` をスロー（TRACE ログ `core.module.call_denied`）

設定方法は [作用域（scope）](scope.md) の出力側の詳細を参照。

## 指定イベント: lifecycle.emit の to パラメータ

ライフサイクルイベントは指定送信をサポート：`to` でターゲット所有者（owner）を指定すると、イベントはその owner として登録されたフックにのみ配信される（`on_load` 内で登録されたフックは自動的に本モジュールに帰属）、他のモジュールやワイルドカード `*` ハンドラは感知しない。

```python
from ErisPulse.Core.lifecycle import lifecycle

# 投递元：イベントは Chat モジュールが登録したフックにのみ投递される
await lifecycle.emit("message_received", {"text": "hi", "from": "u1"}, to="Chat")

# 訂閱元（Chat モジュール内）：同名のフックを登録し、owner は登録時に自動的に記録される
@lifecycle.on("message_received")
async def on_message_received(data): ...

@lifecycle.on("message")          # 点式の親前缀も同様に有効（owner でフィルタリング）
async def on_any(data): ...
```

意味の詳細：

- ターゲット owner に登録されたフックがない → イベントは**静かに破棄**（**存在しない場所には送らない**）、`lifecycle.has_handlers("message_received")` で事前に検出可能
- `data` が dict の場合、`_trace_id` が自動的に付与される（既存値を上書きしない）、全トラッキングと連携
- ブロードキャストと指定は同じフック登録を共有：`emit(...)` に `to` を指定しないと全フレームワークにブロードキャスト、`to` を指定すると同一イベントはターゲットモジュールにのみ見える
- `emit_sync` / `submit_event`（互換 API）も `to=` パラメータをサポート

> [!NOTE]
> 指定イベントは軽量な通知であり、**ターゲットの検証やラグジュアリーな起動は行わない**；ターゲットの存在性検証、契約審査、または返り値が必要な場合は、[RPC: module.call](#rpcmodulecall) を使用してください。

## ラグジュアリーなモジュールと呼び出し

`module.call()` はラグジュアリーなモジュールに対して**透明な起動**を行う：

- イベント駆動ラグジュアリーなモジュール（`activate_on` で宣言）→ 活性化ロック `_activate()` を通る、活性化後はトリガースタブが自動的に登録解除
- 通常のラグジュアリーなモジュール → 同期初期化または通常のロード経路（冪等）
- 起動に失敗 → `ModuleNotAvailableError`

つまり：**呼び出し元はターゲットモジュールがロードされているかどうかを気にする必要はない**、また、ターゲットを起動するために特定のイベントを待つ必要もない。

指定イベント（`lifecycle.emit(..., to=...)`）はラグジュアリーな起動を行わない——ターゲットがロードされていないとフックが存在しない、イベントは静かに破棄される；確実に送信したい場合は `module.call()` を使用してください。

## クールスタート時の再再生

新規インストール / 再起動のモジュールは一部のチャットを逃した——`get_load_strategy(replay=...)` により、フレームワークはモジュールが準備された後、会話の受信箱に含まれる最近のメッセージを**再再生**してモジュール自身に送る：

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyAIModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=100,
            replay="5m",        # 最近の5分間を再再生（"1h" / "300"秒の形式も可）
        )

    async def on_load(self, event):
        @message.on_message()
        async def handle(e):
            if e.get("replayed"):
                # 合成イベント：コンテキストの補完のみ、送信などの副作用は発生しない
                ...
```

意味の詳細：

- データソースは[会話の受信箱](interaction.md#会話受信箱eventhistory)（`sdk.transcript.recent()`）であり、モジュールのロード完了後にバックグラウンドで実行され、起動をブロックしない
- 合成イベントには `replayed: True` フラグ、`platform / detail_type / user_id / alt_message` が含まれ、**本モジュールのハンドラにのみ分発される**——他のモジュールには再再生の影響を受けない
- 受信箱が有効 / 記録がない / 時間の宣言が不正（`replay_invalid` 警告）の場合は静かにスキップされる

## イベントの冪等性と重複除去

プラットフォームの websocket 再接続後に同じイベントが重複送信されることがよくある（同じ `event["id"]`）——配信エントリは id に基づいて LRU で重複除去（容量 4096）、同じ id のイベントは1回しか配信されない。

```toml
[ErisPulse.framework]
event_dedupe = true   # 既定で有効；テスト環境で固定 id の合成イベントを生成する場合は無効化可能
```

アダプターが**登録**（新接続のライフサイクルの起点）されたときに、自動的に重複除去キャッシュがリセットされる。



### 国际化（i18n）系统

# 国際化 (i18n) システム

> [!TIP]
> **この記事を読む必要があるのは**：多言語の文案、翻訳の登録、言語の検出が必要な場合です。必要ない場合は、他の機能の使用に影響を与えることなく、この記事は飛ばしてください。

ErisPulse v2.5.0 以降、完全な国際化 (i18n) 機能が内蔵されています。フレームワークのコアおよび CLI インターフェースは、システム言語に応じて表示されるテキストを自動的に切り替えることができ、外部モジュールが独自の翻訳を登録することもサポートしています。

## 支援言語

| 言語 | コード | 説明 |
|------|------|------|
| 简体中文 | `zh-CN` | デフォルト言語（フレームワークの原生言語） |
| 繁體中文 | `zh-TW` | 繁体中文（香港/澳门/台湾） |
| English | `en` | 英文（一般的フォールバック言語） |
| 日本語 | `ja` | 日本語 |
| Русский | `ru` | ロシア語 |

## 早速体験

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
language = "zh-TW"
```

`"auto"`（デフォルト値）に設定すると、システム言語を自動検出します。

### コード内で手動で切り替え

```python
from ErisPulse import i18n

# 言語を手動で設定
i18n.set_language("en")
print(i18n.get_language())  # "en"

# 自動検出に戻す
i18n.reset_language()
```

## 言語検出メカニズム

フレームワークは、以下の優先順位でユーザーの言語を検出します：

1. **環境変数 `ERISPULSE_LANG`** — 最も高い優先順位で、テストや一時的な切り替えに使用
2. **Windows API** — `GetUserDefaultLocaleName`（Windowsに限定、Git Bashなどのツールが `LANG` を上書きする影響を受けない）
3. **環境変数** — `LANGUAGE` > `LC_ALL` > `LC_MESSAGES` > `LANG`（Unix/macOSの標準）
4. **システムロケール** — `locale.getlocale()` / `locale.getdefaultlocale()`
5. **デフォルト** — en（英語）

### 近接マッピング原則

検出された言語が正確に一致しない場合、サポートされている言語に近接する原則でマッピングされます：

- `zh-TW`, `zh-HK`, `zh-MO`, `zh-Hant` → **繁体中国語**
- その他のすべての `zh-*`（例: `zh-CN`, `zh-SG`）→ **簡体中国語**
- `en-US`, `en-GB`, `en-AU` など → **英語**
- `ja-JP` → **日本語**
- `ru-RU` → **ロシア語**
- その他の未認識の言語 → **簡体中国語（デフォルト）**

## モジュールでの i18n の使用

独自のモジュールに翻訳テキストを登録することで、多言語をサポートできます。

### 推奨方法：I18nClass を使って翻訳キーを宣言する（v2.7.0+）

v2.7.0 以降、モジュールやアダプターは `ConfigClass` を宣言するのと同じように、ネストされたクラス `I18nClass` を使って翻訳キーを宣言できます。フレームワークはロード時に**自動的に**宣言されたすべての翻訳キーを登録します。手動で `i18n.register()` を呼び出す必要はありません。

```python
from dataclasses import dataclass, field

from ErisPulse.Core.Bases import BaseConfig, BaseI18n, BaseModule, I18nKey


class MyModule(BaseModule):
    # 設定クラス（オプション）
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="欢迎",
            metadata={
                # ここでは i18n キー mymodule.welcome_msg を参照
                "description": {"i18n": "mymodule.welcome_msg", "default": "欢迎消息"},
            },
        )

    # 翻訳キー集合クラス（オプション）
    # 宣言されたキーはフレームワークによって自動的に登録され、
    # ConfigClass がデフォルト設定を生成するよりも優先されます
    class I18nClass(BaseI18n):
        # 属性名が自動的に結合されて完全なキー経路 <モジュール名>.<属性名> になります
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # 言語に依存しないデフォルト値、どの言語にも登録されません
            zh_CN="欢迎消息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
            zh_TW="歡迎訊息",
        )
        # 业务で使用する他の翻訳キー
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )

        # 完全なキー経路を明示的に指定することもできます（属性名の結合を使わない）
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

#### なぜ I18nClass が推奨されるのか？

| シナリオ | 手動 i18n.register() | I18nClass 宣言式 |
|------|-----------------------|------------------|
| 設定の説明に参照される i18n キー | 手動で登録する必要があり、設定生成前に登録する必要がある | フレームワークが設定生成前に自動的に登録する |
| 多言語翻訳の宣言 | on_load() 内に散在する | クラス内で一括して宣言され、一目瞭然 |
| キー名の命名の一貫性 | 拼写ミスが発生しやすい | 属性名がキー名の接尾辞として使用され、IDE による補完が可能 |
| アンロード時のクリーンアップ | 手動で unregister_domain() を呼び出す必要がある | フレームワークが統一されたドメインで登録する |

#### I18nClass のキー経路ルール

- **デフォルト**：``<モジュール登録名>.<属性名>`` を完全なキー経路として使用
  - 例：モジュール名が ``MyModule``、属性 ``welcome`` → キー経路 ``MyModule.welcome``
- **明示的**：``I18nKey(key="...")`` パラメータを使って任意のドット区切り経路を指定
  - 深層ネストされたキー名（例：``mymodule.config.basic.token``）に適している

#### アダプターでの使用

アダプターも `I18nClass` をサポートしており、使用方法は完全に同じです：

```python
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey


class MyAdapter(BaseAdapter):
    @dataclass
    class ConfigClass(BaseConfig):
        endpoint: str = field(
            default="",
            metadata={
                # 設定の説明は adapter.MyAdapter.endpoint キーを参照
                "description": {"i18n": "MyAdapter.endpoint", "default": "API 地址"},
            },
        )

    class I18nClass(BaseI18n):
        # 集中して設定の説明に参照されるキーとその他の業務用キーの多言語訳を宣言
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API адрес",
        )
```

アダプターの `I18nClass` は `__init__` 階段（つまり設定テンプレート生成の前）に自動的に登録され、設定の説明に参照される i18n キーが利用可能になります。

### 手動でカスタム翻訳を登録する（旧方法）

`I18nClass` を使用しない場合、`i18n.register()` を直接呼び出して翻訳テキストを登録することもできます。

```python
from ErisPulse import i18n

# 中文翻訳を登録
i18n.register("zh-CN", {
    "my_module.welcome": "欢迎使用我的模块！",
    "my_module.goodbye": "再见！",
    "my_module.hello": "你好，{name}！",
}, domain="my_module")

# 英文翻訳を登録
i18n.register("en", {
    "my_module.welcome": "Welcome to my module!",
    "my_module.goodbye": "Goodbye!",
    "my_module.hello": "Hello, {name}!",
}, domain="my_module")
```

### 翻訳の使用

```python
from ErisPulse import i18n

# 簡単な翻訳
i18n.t("my_module.welcome")  # 現在の言語が自動的に使用されます

# フォーマットパラメータ付き
i18n.t("my_module.hello", name="Alice")

# デフォルト値を指定（翻訳キーが存在しない場合に返される）
i18n.t("my_module.unknown_key", default="默认文本")
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
            "description": {"i18n": "my_module.welcome_msg", "default": "欢迎消息"},
            "ui": {"widget": "text", "group": "basic", "order": 1},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def on_load(self, event):
        # 実時で設定を読み取る（各アクセスで最新値が反映される）
        self.logger.info(self.cfg.welcome_msg)
        self.logger.info(i18n.t("my_module.welcome"))

    @command("hello")
    async def hello_handler(self, event):
        name = event.get_user_nickname() or "friend"
        await event.reply(i18n.t("my_module.hello", name=name))

    async def on_unload(self, event):
        pass
```

### 翻訳のアンロード

```python
# ドメイン全体の翻訳をアンロード
i18n.unregister_domain("my_module")
```

---

## 設定フィールドの多言語対応

v2.5.2 以降、設定の Schema は i18n を全面的にサポートします。ユーザーが見られるすべてのテキストフィールドは i18n キーを参照でき、WebUI およびその他の消費者は、現在の言語に応じて自動的に対応するテキストに解析します。

### 対応する i18n フィールド

| フィールド | 位置 | 説明 |
|------|------|------|
| `description` | field metadata | フィールドの説明 |
| `options[].label` | `ui.options` | select コントロールのオプションラベル |
| `placeholder` | `ui.placeholder` | 入力欄のプレースホルダー |
| `group_labels` | `_schema_meta` | グループ表示名（Dashboard のセクションタイトル） |

すべての i18n フィールドは `{"i18n": "key", "default": "テキスト"}` の形式を採用し、純粋な文字列はそのまま透過されます（後方互換性を保つため）。

### i18n フィールドの宣言

すべてのユーザーが見られるテキストフィールドは i18n をサポートします：

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

`default` はバックアップテキストです。翻訳が登録されていない場合、または検索に失敗した場合に表示されます。

### secret 脱敏と設定検証

`"secret": True` とマークされたフィールドは、2.7.0 以降、**脱敏保護**が自動で適用されます：

- **テンプレート生成時の脱敏**：`dataclass_to_toml_with_comments()` が設定テンプレートを生成する際、secret フィールドの実際の値はファイルに書き込まれません（空のプレースホルダーとして表示され、機密情報がディスク上に残らないようにします）。
- **一般的な脱敏ツール**：`redact_secret(value)` は非空値を `***` に置き換え、空値はそのまま返します。これはログ出力などの場面で使用できます。

```python
from ErisPulse.Core.Bases.config_schema import redact_secret

redact_secret("sk-xxxxxx")  # '***'
redact_secret("")           # ''
```

**設定検証**（`validate_config()`）は、`required` の非空チェックに加えて、2.7.0 以降、以下の検証もサポートします：

| 検証項目 | メタデータ | 例 |
|--------|--------|------|
| 型の一致 | フィールドの宣言型 | `int` 型のフィールドに文字列を渡すとエラーになります |
| 列挙制約 | `ui.options` またはトップレベルの `options` | 値は許可されたオプションに属している必要があります |
| 数値範囲 | トップレベルの `min` / `max` | `metadata={"min": 1, "max": 65535}` |

```python
from ErisPulse.Core.Bases.config_schema import validate_config

@dataclass
class C(BaseConfig):
    mode: str = field(default="a", metadata={"ui": {"widget": "select", "options": ["a", "b"]}})
    port: int = field(default=80, metadata={"min": 1, "max": 65535})

errors = validate_config(C(mode="x", port=70000))  # 2つのエラー：列挙制約と範囲制約
```

### 設定の翻訳登録

設定フィールドの i18n キーは、通常の翻訳キーと同じように `i18n.register()` を使って登録できます：

```python
from ErisPulse import i18n

# 登録する中国語（default と同じでも、異なるものでも可）
i18n.register("zh-CN", {
    "my_adapter.token": "プラットフォーム Token",
}, domain="my_adapter")

# 登録する英語
i18n.register("en", {
    "my_adapter.token": "Platform Token",
}, domain="my_adapter")
```
> **推奨方法**：`I18nClass` を使って翻訳キーを宣言し、フレームワークが自動的に登録します（上記「推奨方法」の章を参照）。  
> 手動で `i18n.register()` や `register_config_i18n()` を呼び出す必要はありません。

また、便利な関数 `register_config_i18n()` も提供されており、設定クラスからキーを自動的に抽出して登録できます：

```python
from ErisPulse.Core.Bases.config_schema import register_config_i18n

# 自動的に description.default を zh-CN の翻訳として登録
register_config_i18n(MyAdapterConfig, "zh-CN")

# 手動で英語の翻訳を提供
register_config_i18n(MyAdapterConfig, "en", {
    "my_adapter.token": "Platform Token",
})
```

### WebUI での消費方法

`get_config_schema()` が返す schema では、i18n ディクショナリはそのまま透過されます。WebUI のフロントエンドは、現在の言語に応じて `i18n.t()` を呼び出して解析できます。

i18n をサポートしないフロントエンドに直接文字列を返す必要がある場合、`resolve_config_schema()` を使用します。この関数は、`description`、`options[].label`、`placeholder`、`group_labels` をすべて現在の言語の文字列に解析します：

```python
from ErisPulse.Core.Bases.config_schema import resolve_config_schema

# すべての i18n フィールドが現在の言語の文字列に解析されています
schema = resolve_config_schema(MyAdapterConfig)
print(schema["fields"]["token"]["description"])    # "プラットフォーム Token" または "Platform Token"
print(schema["fields"]["token"]["placeholder"])   # "Token を入力してください" または "Enter Token"
print(schema["fields"]["mode"]["options"][0]["label"])  # "モードA" または "Mode A"
print(schema["group_labels"]["basic"])             # "基本設定" または "Basic"
```

> `BaseConfig`、`BotAccountConfig`、`register_config_i18n()`、`resolve_config_schema()`  
> などの型とツール関数の実際の定義は `ErisPulse.Core.Bases.config_schema` にあります。  
> `ErisPulse.runtime.config_schema` は互換性のための shims として残されています。  
> **推奨は `ErisPulse.Core.Bases` から一括でインポートすること**（i18n 翻訳キーに関連する型は例外で、`ErisPulse.Core.Bases.i18n_schema` にあります）。

## API リファレンス

### I18nManager

#### 核心メソッド

| メソッド | 説明 |
|------|------|
| `t(key, default=None, **kwargs)` | 翻訳テキストを取得する（`gettext()` はエイリアス） |
| `set_language(lang)` | 手動で言語を設定する |
| `get_language()` | 現在の言語を取得する |
| `reset_language()` | 自動検出にリセットし、環境を再検出する |
| `get_supported_languages()` | すべてのサポート言語のリストを取得する |
| `has_translation(key, lang=None)` | 翻訳キーが存在するか確認する |
| `register(lang, translations, domain)` | 自定義翻訳を登録する |
| `unregister_domain(domain)` | 指定されたドメインのすべての翻訳をアンロードする |
| `reload()` | 内部翻訳を再読み込みし、言語を再検出する |

#### `t()` メソッドの詳細

```python
def t(self, key, /, default=None, **kwargs):
```

- `key` — 翻訳キー（位置引数のみ、`**kwargs` の `key=` と衝突しない）
- `default` — 翻訳が存在しない場合に返すデフォルト値、デフォルトは `None`（キー名そのものを返す）
- `**kwargs` — 翻訳値中の `{placeholder}` を埋め込むためのフォーマットパラメータ

例：

```python
# 翻訳定義: "greeting": "你好，{name}！欢迎来到{place}。"
i18n.t("greeting", name="Alice", place="ErisPulse")
# 戻り値: "你好，Alice！欢迎来到ErisPulse。"
```

### BaseI18n / I18nKey（宣言的翻訳キー）

v2.7.0 から、`ErisPulse.Core.Bases` はクラス属性に基づく翻訳キーの宣言ツールを提供しています（`ErisPulse.Core.Bases` から統一的にインポートすることを推奨します）：

> ``I18nKey.default`` は**言語に依存しないデフォルトテキスト**であり、どの言語にも登録されません。  
> 翻訳を有効にするには、少なくとも1つの言語パラメータ（``zh_CN=`` / ``en=`` / ``ja=`` など）を明示的に渡す必要があります。  
> これにより、各国の開発者は `default` を自分の母国語で自由に記入でき、フレームワークはその内容を一切仮定しません。

| 名称 | 説明 |
|------|------|
| `I18nKey(default, *, key=None, zh_CN, zh_TW, en, ja, ru)` | 単一の翻訳キーの宣言、`default` は言語に依存しないデフォルト |
| `BaseI18n` | 翻訳キー集合の基底クラス（`BaseConfig` と命名を揃える）、子クラスはクラス属性で複数の `I18nKey` を宣言する |
| `BaseI18n.register(prefix="", domain="app")` | クラスメソッド：宣言されたすべてのキーを i18n システムに登録する |
| `key` | `I18nKey` のエイリアス（より簡潔な書き方） |

使用例：

```python
from ErisPulse.Core.Bases import BaseI18n, key

class MyKeys(BaseI18n):
    # 簡潔なエイリアス書き方
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

# 独立使用（手動で登録）
MyKeys.register(prefix="myapp.", domain="myapp")
```

### SDK インスタンスからのアクセス

```python
from ErisPulse import sdk

# sdk.i18n は直接インポートした i18n と同じオブジェクト
sdk.i18n.set_language("en")
print(sdk.i18n.t("core.sdk.init.starting"))
```

## 実行時設定

### 設定APIを介してi18n設定を読み取る

```python
from ErisPulse.Core.Bases import I18nConfig
from ErisPulse.runtime import get_i18n_config

config = get_i18n_config()
print(config["language"])  # "auto" または具体的な言語コード

# I18nConfig は dataclass であり、設定テンプレートの生成に使用可能
schema = I18nConfig.__dataclass_fields__
```

### 設定項目の説明

`config/config.toml` の `[ErisPulse.i18n]` 部分で：

```toml
[ErisPulse.i18n]
# 表示言語。選択可能な値:
# - "auto"      — システム言語を自動検出（デフォルト）
# - "zh-CN"     — 簡体字中国語
# - "zh-TW"     — 繁体字中国語
# - "en"        — 英語
# - "ja"        — 日本語
# - "ru"        — ロシア語
language = "auto"
```

---

## 最佳実践

### 翻訳キーの命名

ドットで区切られた名前空間形式の命名を推奨します：

```
<モジュール名>.<カテゴリ>.<説明>
```

例：`my_module.command.hello_desc`、`core.adapter.start_failed`

### 多言語のカバー

すべての言語の翻訳を一度に提供する必要はありません。不足している言語は自動的に英語にフォールバックされ、英語もなければキー名そのものが表示されます。

### 動的コンテンツ

ユーザー名、数値などの動的に生成されるコンテンツについては、`{placeholder}` 形式でフォーマットします：

```python
# 翻訳定義
"user_count": "現在オンラインのユーザー：{count} 人"

# 使用
i18n.t("user_count", count=len(users))
```

### ログメッセージ

モジュールがフレームワークの Logger を使用している場合、これらのメッセージも自動的に現在の言語で表示されます：

```python
self.logger.info(i18n.t("my_module.startup"))
```

## CLI i18n との関係

CLI には**独立**した国際化モジュール (`ErisPulse.CLI.i18n`) があり、フレームワークのコアの国際化モジュールとは完全に分離されています。

- **Core i18n** — フレームワークのコアモジュールで使用され、外部モジュールは翻訳を登録できます。
- **CLI i18n** — コマンドラインインターフェース内で使用され、Core と翻訳データを共有しません。

この設計により、CLI の翻訳の変更がフレームワークのコアの安定性に影響を与えることがありません。



### 统一控制面（scope）

# スコープ（scope）

> [!TIP]
> **この記事を読むべきタイミング**：モジュールの可用性、イベントの受信制限、または出力アクションの制限を制御する必要がある場合。不要な場合は飛ばしても、他の機能の使用に影響はありません。

> **読了後は**：3つのスコープ次元（モジュールの可用性 / イベント受信 / 出力アクション）それぞれの設定経路、判定優先順位と拒否時の挙動、実行時のAPIの使い方、およびブロッキングがどのように可視化されるか（`scope.blocked` イベント）を理解できます。
>
> **本記事では対象外**：リソースの所有権と解放回収（[所有権（owner）システム](ownership.md)を参照）；コマンドACLとイベントの上書き（[イベント処理入門](../getting-started/event-handling.md)を参照）。

> [!NOTE]
> この機能は ErisPulse **2.8.0+** が必要です。

スコープは4つの質問に答える：**どのモジュールが使えるか、どのイベントを受け取るか、特定のモジュールがどのようなテキストを処理するか、モジュールが外部にどのようなアクションを実行できるか**。制御権はすべてユーザーに委ねられます。モジュール / アダプタ / プロセッサ / 出力呼び出しの登録時に**上層**（設定 `ErisPulse.scope` または実行時 `sdk.scope`）で一括して宣言し、イベントパイプラインはエントリ、プロセッサフィルタ、出力ゲートで自動的に読み取り、実行します。

| 次元 | 制御対象 | 拒否時の挙動 | 設定経路 |
|------|---------|---------|---------|
| **① モジュール** | どのモジュールが使えるか（プラットフォーム / Bot / セッションの3段階） | フィルタリングされたモジュールはトリガーされず、返信もされません（`scope.blocked` イベントをブロッキング）。対象となるコマンドは既に認証済みで、ブロックされます。 | `scope.platforms / bots / sessions` |
| **② 身分** | イベントを受け取るかどうか（アダプタ / Bot / セッション / ユーザーの4段階） | エントリで完全に破棄されます（`scope.blocked` イベントをブロッキング）。 | `scope.identity.*` |
| **③ 出力** | モジュールがどのような出力呼び出し（メッセージ / API / リクエスト、メソッドレベルの白黒リスト）を実行できるか | 失敗応答（`retcode=34601`）が返されます。 | `scope.actions` |

> **関連システム**：コマンドは特別なメッセージイベントハンドラであり、そのユーザーの白黒リスト（ACL）と実装パラメータの上書きはコマンドシステムが独自に保持します（`ErisPulse.event.command`）。[イベント処理入門](../getting-started/event-handling.md)と[設定ガイド](../user-guide/configuration.md)を参照してください。

{!--< tips >!--}
1. `from ErisPulse.Core import scope` でシングルトンをインポート（`sdk.scope` は同じオブジェクト）
2. 判定：`scope.is_allowed(...)` / `scope.is_identity_allowed(...)` / `scope.is_action_allowed(...)` は、それぞれ①②③の3つのゲートに対応します
3. 読み書き：次元化されたパラメータメソッド（IDEで補完可能）—— `scope.set_module(...)` / `scope.set_identity(...)` / `scope.set_action(...)`；また、辞書式のバックアップとして `scope.get(path)` / `scope.set(path, v)` / `scope.delete(path)` もあります
4. イベントハンドラのテキスト条件の上書きは、[イベント処理入門 · イベントの上書き](../getting-started/event-handling.md#イベントの上書き-モジュールコードを改ざんせず任意のイベントタイプの挙動を上書き)を参照してください；コマンドACL / パラメータの上書きは[イベント処理入門](../getting-started/event-handling.md)を参照してください
{!--< /tips >!--}

## マッチングエントリの構文（全システムで統一）

スコープのすべての「名前リスト」（モジュール名、身元キー、出力エントリ）は、同一のマッチング構文（`ErisPulse.Core.text_match`）を使用します：

| 構文 | 例 | 説明 |
|------|------|------|
| 精確名 | `"Chat"` | 全値比較、**大文字小文字は区別しない** |
| glob | `"Tool*"`、`"spam_*"` | `*` 任意の文字列 / `?` 1文字 / `[seq]` 文字集合、大文字小文字は区別しない |
| 正規表現 | `"re:^Danger.*"` | `re:` で始まる宣言、正規表現 `search` で一致、デフォルトは大文字小文字は区別しない |

- 不正な正規表現は**静かに無効化**される（エラーは発生せず、クラッシュもしない）
- デコレータのパラメータ（`pattern=` / `regex=`）は固定された意味を持つ：`pattern` は glob、`regex` は正規表現のソースコード（`re:` プレフィックスは付けない）；スコープの設定内の正規表現エントリは**必ず** `re:` プレフィックスを付ける必要がある

## グローバルバックアップ：`default_allow`

`default_allow` は**唯一のグローバルバックアップ**スイッチ（デフォルト `true`）で、2つの判定次元に一括して効果を及ぼします：

- **モジュール次元**：どのバインディングにも一致しない → `default_allow` で許可 / 拒否を決定
- **身元次元**：どの戦略にも一致しない → `default_allow` で許可 / 拒否を決定

`false` に設定すると「暗黙の拒否」厳密モードが有効になり、ホワイトリスト方式で管理されるため、**明示的に許可されていないものはすべて拒否**されます。

> **例外**：③ 出力次元は**`default_allow`の影響を受けない**——これは独立した絞り込みスイッチであり、デフォルトはすべて許可され、明示的なルールでのみ制限される（フレームワーク層の owner が空の呼び出しは常に許可される）。このように厳密なグローバルモードでも、すべてのモジュールのメッセージ返信が意図せず遮断されることはない。コマンド ACL には独立した `ErisPulse.event.command.default_allow` バックアップがあり、互いに影響しない。

## 設定ファイル

```toml
[ErisPulse.scope]
default_allow = true        # グローバルバックアップ（false = 暗黙の拒否厳密モード）
cache_size = 1024           # LRUキャッシュサイズ

# ── ① モジュール次元（優先度：セッション > Bot > プラットフォーム）──
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]   # ホワイトリスト：正確な名前 / glob / re: 正規表現
blocked = ["re:^Danger"]
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Chat"]
merge = true                  # プラットフォームレベルのバインディングに追加（デフォルトは全体を上書き）
[ErisPulse.scope.sessions.onebot11."789012345"]
modules = ["Chat"]

# ── ② 身元次元（優先度：ユーザー > セッション > Bot > アダプタ）──
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                   # アダプタ全体のイベントを完全に破棄
[ErisPulse.scope.identity.bots.onebot11."123456"]
deny = true
[ErisPulse.scope.identity.sessions.onebot11."g_blocked"]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]           # ユーザー鍵は glob / re: 正規表現をサポート
deny = ["u_bad", "spam_*"]

# ── ③ 出力次元（デフォルトはすべて許可され、明示的な絞り込みのみ制限）──
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                    # 送信を完全に禁止
api = { allow = ["get_*"] }                               # クエリ系の標準APIのみ許可
request = { deny = true }                                 # リクエスト処理を禁止
```

## ① モジュール次元

**一言で言うと**：プラットフォーム / Bot / セッションの3段階でバインド制御を行い、"このコンテキストでどのモジュールが有効か"を制御します。フィルタリングされたモジュールはトリガされず、応答もしません（一致したコマンドは引き続き認領され、ブロックされます）。

「あるコンテキストで、どのモジュールが有効か」を回答します。デフォルトではすべて開放です。バインドを設定した場合にフィルタリングが開始され、**モジュールとアダプタは一切変更不要です**。

```mermaid
flowchart TD
    A["イベントがモジュールのハンドラ/コマンドに到達"] --> B{"scope.is_allowed<br/>(platform, bot, module, session)"}
    B --> C{"解析チェーン：セッション級 > Bot 級 > プラットフォーム級<br/>（子級 merge = true の場合、各段階で合併）"}
    C -->|"命中"| D["blocked 命中 → 拒否<br/>modules 非空 → 有効リストのみ通過<br/>両方空 → default_allow"]
    C -->|"未命中"| E["default_allow（デフォルト true = 通過）"]
    D -->|"拒否"| Z["応答なし<br/>（`scope.blocked` イベントをブロードキャストしてブロックを通知；一致したコマンドは引き続き認領され、ブロックされる）"]
```

- **解析優先度**：セッション級 > Bot 級 > プラットフォーム級、高優先度のバインドは低優先度を**全体的に上書き**します。  
  子級バインドに `merge = true` を指定した場合は、低優先度と**各項目ごとに合併**されます（`modules` / `blocked` はそれぞれ独立に合併され、`merge` 自体は項目としてカウントされません）。
- **デフォルトの意味**：フィルタリングされたモジュールのコマンドやハンドラはトリガされず、応答もしません。TRACE レベルのログで確認可能（`core.scope.denied`）。  
  同時に `scope.blocked` ライフサイクルイベントをブロードキャストして、誰がブロックされたか、なぜブロックされたかを観測できます。  
  一致した**コマンド**は引き続き認領され、ブロックされます——コマンドのテキストは低優先度のメッセージハンドラに漏れることなく、二重応答の混乱を解消します。
- **フレームワークレベルのハンドラ**（`scope_exempt=True` または owner が空）は影響を受けません。モジュール名が空（フレームワーク層のリソース）の場合は常に通過します。
- **セッション感知のヘルプとコマンド照会**：コマンド照会 API（`command.help` / `get_command` / `get_commands` / `get_group_commands` / `get_visible_commands`、および `module.get_commands_overview`）は、任意の `event=` または明示的な `platform=` / `bot_id=` / `session_id=` キーワードをサポートします。  
  現在のセッションで無効なモジュールのコマンドは結果に含まれません（`get_command` は None を返し、単一コマンドのヘルプは「未登録」として扱われ、デフォルトの意味と一致します）。  
  コンテキストを渡さない場合は、全量の動作を維持します。

### バインドの継承（merge）

デフォルトでは、全体的な上書きの意味が明確で予測可能です。上級バインドに**追加**したい場合は、子級に `merge = true` を指定します：

```toml
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool"]      # プラットフォーム級：Chat、Tool を有効

[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true                    # この Bot の実効値 = ["Chat", "Tool", "Music"]
```

- 合併ルール：`modules` と `blocked` はそれぞれ**合併**されます。バインド内では `blocked` が `modules` より優先されます。
- 鏈式合併：プラットフォーム → Bot → セッションの順に段階的に追加され、各段階で `merge` または上書きを独立して決定します。

## ② 身元次元（イベント受容）

**一言で言うと**：ユーザー／セッション／Bot／アダプターの4段階の戦略に基づき、イベント配信の入口で「受容すべきでないイベント」を完全に破棄し、deny は allow より優先されます。

「どのユーザーのイベントを受け入れるか」を決定します。拒否されたイベントは**配信の入口で完全に破棄**されます——ミドルウェアや任意のハンドラ（フレームワークレベルを含む）には一切渡らず、TRACE レベルのログ（`core.scope.identity_denied`）でのみ確認できます。

- **解析優先度**：ユーザー > セッション > Bot > アダプター。最も具体的に設定された戦略を採用します。deny は allow より優先されます。
- 各段階のバインディングは二元的な戦略です：`{ allow = true }` または `{ deny = true }`
- ユーザーのキーには glob / 正規表現（例：`"spam_*"` で一括してスパムユーザーをブロック）が使用可能です。
- 代表的な使い方——上位階層で deny し、個別のユーザーに対して allow を設定することで「例外的に許可」を実現します：

```toml
[ErisPulse.scope.identity.adapters.onebot11]
deny = true
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]   # アダプター階層で拒否されていても、u_admin のイベントは許可されます
```

## ③ 出站次元（制限モジュールが発信する呼び出し）

**一言で言うと**：メソッド単位のホワイトリスト・ブラックリストによって、モジュールが発信するメッセージ / API / リクエスト呼び出しを制限し、拒否された呼び出しはネットワークリクエストを一切行わず、直接 `retcode=34601` を返します。

制限されるモジュールの**発信アクション**：メッセージ送信 / 標準APIアクション / リクエスト操作。  
3つのアクションはそれぞれ下層DSLに対応します：`Event.reply` と `Send`（send）、`Api` / `call_api`（api）、`Request` の accept/reject（request）。イベントハンドラ実行中にモジュールが発信する出站呼び出しは、モジュールのオーナーを含み、この次元で一括して判定されます。

### 規則の形態（インライン表）

各アクションのルールはインライン表です：`{ allow = [...], deny = true|[...] }`。  
同一アクションには1つのルールしか設定できません（TOMLのキーは重複不可、全禁止と細粒度のどちらか1つを選択）：

```toml
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                                  # 送信を全禁止（Event.reply / Send DSL）
# またはメソッド単位の細粒度設定：send = { allow = ["Text", "Image*"], deny = ["File"] }
api = { allow = ["get_*"] }                             # 限定的に取得系標準APIを許可
# またはアクション単位のブラックリスト：api = { deny = ["set_*", "leave_*"] }
request = { deny = true }                               # リクエストのaccept/reject処理を禁止
```

- `send` の項目は**送信メソッド名**（`Text` / `Image` / `File` ...）に一致する
- `api` の項目は**標準アクション名**（`get_group_info` / `set_group_name` ...）に一致する
- 項目は正確な名前 / glob / `re:` 正規表現（全システムと統一された構文で、大文字小文字は区別しない）
- `allow` に1つの文字列を記述することは、1つの項目のリストと同義です：`send = { allow = "Text" }`

### 判定の意味

**デフォルトは全許可**——設定がなければ、またはオーナーが空（フレームワーク層の内部呼び出し）であれば許可されます。  
ルールが設定された場合、以下の順序で判定されます：

1. `deny = true` → 拒否
2. `deny` リストに呼び出し名が一致 → 拒否
3. `allow` リストが空でなく、呼び出し名が一致しない（または呼び出しに名前がない）→ 拒否
4. その他の場合 → 許可

拒否された呼び出しはネットワークリクエストを一切行わず、標準の失敗レスポンスを直接返します（`retcode = 34601`、[api-response §5.3](../standards/api-response.md#53-フレームワーク拡張返却コード34xxx-プラットフォームエラーセグメントの下3桁カスタマイズ)を参照）。  
3つのアクションは互いに独立しており、1つだけを制限することも可能です。

```python
# 実行時API
sdk.scope.set_action("MyModule", "send", deny=True)              # 送信を全禁止
sdk.scope.set_action("MyModule", "send", allow=["Text"])         # 送信はテキストのみ許可
sdk.scope.is_action_allowed("MyModule", "send", name="Image")    # False
sdk.scope.is_action_allowed("MyModule", "api", name="get_user_info")  # 規則に従って判定
sdk.scope.delete_action("MyModule", "send")                      # 許可を復元
sdk.scope.get_action("MyModule", "send")                         # そのアクションの現在のルール
```

## 実行時API

スコープの実行時APIは3つの層に分かれています：**判定**（3つの質問）、**次元ごとの読み書き**（各次元の `set` / `get` / `delete` パラメータ化メソッド、署名はすべて型注釈付き、IDEで補完可能）、**辞書式バックアップ**（ドット区切りのパスで任意の節に直接アクセス）。

```python
from ErisPulse import sdk

scope = sdk.scope
```

### 判定（3つの質問）

```python
scope.is_allowed("onebot11", "123456", "Chat")                 # ① モジュール次元
scope.is_allowed("onebot11", "123456", "Chat", "789012345")    # セッションレベルを含む
scope.is_allowed("onebot11", "123456", None)                   # フレームワーク層のリソース -> True

scope.is_identity_allowed("onebot11", "123456", "group_9", "u1")   # ② 身元次元

scope.is_action_allowed("MyModule", "send")                    # ④ 出力次元
scope.is_action_allowed("MyModule", "send", name="Image")      # メソッドレベルの細粒度
```

### ① モジュール次元

```python
# バインディング（パラメータによって階層が決まります：session_id > bot_id > プラットフォームレベル）
scope.set_module("onebot11", bot_id="123456", modules=["Chat", "Tool*"])
scope.set_module("onebot11", blocked=["re:^Danger"])                       # プラットフォームレベル
scope.set_module("onebot11", bot_id="123456", session_id="g9", modules=["Chat"])  # セッションレベル
scope.set_module("onebot11", bot_id="123456", modules=["Music"], merge=True)      # 現在のバインディングと並列に結合
scope.set_module("onebot11", bot_id="123456", modules=["Chat"], persist=False)    # 実行時のみ

# 読み取り / 削除
scope.get_module("onebot11", bot_id="123456")   # {"modules": ["Chat"], "blocked": []}
scope.delete_module("onebot11", bot_id="123456")
```

> `merge=True` は**書き込み時に並列に結合**（現在のバインディングとエントリを結合）です；階層間の解析時の `merge = true` 設定は上記の[バインディング継承](#バインディング継承merge)をご覧ください——これらは独立したメカニズムです。

> **実行時バインディング（`persist=False`）の意味**：実行時バインディングは独立したオーバーライド層に保存され、**任意の後続の設定書き込み / 設定ファイルのホットアップデートでも削除されません**（設定ツリーが再構築された後に、書き込み順に自動的に再実行されます、実行時削除も含みます）。これらは永続化されず、プロセスの再起動後に失われます；モジュールのアンロード時に、そのモジュールが書き込んだ実行時バインディングはバックアップでクリーンアップされます。その後、同一のパスで `persist=True` を実行すると、ユーザー永続化の意味で実行時ルールが上書きされます。

### ② 身元次元

```python
# 戦略のバインディング（パラメータによって階層が決まります：user > session > bot > adapter；allow / deny のどちらか一方）
scope.set_identity("onebot11", user_id="u_bad", deny=True)
scope.set_identity("onebot11", user_id="spam_*", deny=True)    # キーは glob / re: 正規表現をサポート
scope.set_identity("onebot11", bot_id="123456", session_id="g9", allow=True)

# 読み取り / 削除
scope.get_identity("onebot11", user_id="u_bad")   # {"deny": True}
scope.delete_identity("onebot11", user_id="u_bad")
```

### ③ 出力次元

```python
# 制限ルールの設定（allow: str|list；deny: bool|str|list；ルール全体の置換）
scope.set_action("MyModule", "send", deny=True)                    # 送信を完全に禁止
scope.set_action("MyModule", "send", allow=["Text"])               # テキスト送信のみ許可
scope.set_action("MyModule", "api", deny=["set_*", "leave_*"])     # 管理系APIを禁止

# 読み取り / 削除
scope.get_action("MyModule", "send")       # {"allow": ["Text"]} 元のルール
scope.delete_action("MyModule", "send")    # 個別のアクションを削除
scope.delete_action("MyModule")            # モジュールのすべてのアクション制限を削除
```

### 一般的な操作

```python
scope.get("platforms")   # 辞書式バックアップ：ドット区切りのパスで任意の節を読み取り
scope.topology()         # 全設定ツリー（ダッシュボード用）
scope.stats()
# {"module_calls": .., "module_filtered": .., "identity_checks": .., "identity_denied": ..,
#  "action_checks": .., "action_denied": .., "cache_hits": .., "cache_misses": ..}
scope.reset_stats()
scope.clear()           # 全設定をクリア（メモリ上でのみ有効）
```

### 高度な操作：辞書式ドット区切りパスバックアップ

次元化されたメソッドは日常的なシナリオをカバーします；任意のノード（または将来追加される次元）に直接アクセスする必要がある場合、**辞書式API**を使用できます——`get` / `set` / `delete` はドット区切りのパスを受け取り（dictの深さのマージ、書き込み後すぐに読み取り可能）、`scope[path]` / `scope[path] = v` / `del scope[path]` / `path in scope` プロトコルも提供します：

```python
scope.set("bots.onebot11.123456", {"modules": ["Chat"], "blocked": []})
scope.set("identity.users.onebot11.u_bad", {"deny": True})
scope.get("actions.MyModule.send")

scope["platforms.onebot11"]        # 読み取り（存在しない場合はKeyErrorを送出）
scope["platforms.onebot11"] = {...}  # 書き込み
del scope["platforms.onebot11"]      # 削除
"actions.MyModule" in scope          # 存在確認
```

## 拦截の可視化：`scope.blocked` イベント

スコープのフィルタリング（モジュールのフィルタ / 身元の拒否）が発生すると、**`scope.blocked`** というライフサイクルイベントがブロードキャストされ、"誰がブロックされたか、どのレベルでブロックされたか"をサブスクライブ、統計、ダッシュボードで表示可能になります——ブロックはデフォルトで返信されませんが、不可知のブラックボックスではありません。

| フィールド | 説明 |
|------|------|
| `dimension` | `"module"`（モジュール次元のフィルタ）/ `"identity"`（身元の受信拒否） |
| `module` | フィルタされたモジュール名（モジュール次元のみ） |
| `platform` / `bot_id` / `session_id` / `user_id` | ブロックが発生したソースコンテキスト |

```python
from ErisPulse.Core.lifecycle import lifecycle

@lifecycle.on("scope.blocked")
def on_blocked(data):
    print(f"ブロックされた：{data['dimension']} {data.get('module') or data.get('user_id')}")
```

- イベントは `fire` でバックグラウンドでブロードキャストされます（リスナーがいない場合はオーバーヘッドがなく、ホットパスを遅らせません）
- キャッシュヒットによる重複のブロックは**再ブロードキャストされません**——同じ組み合わせはキャッシュが失効するたびに1回だけブロードキャストされます
- `adapter.event.blocked`（ミドルウェアによる拒否）とは区別されます：これはイベントレベルの破棄であり、本イベントはスコープの受信ゲートのモジュール / 身元フィルタリングです

## キャッシュとホットアップデート

- `is_allowed` / `is_identity_allowed` / `is_action_allowed` の結果は**LRUキャッシュ**（`scope.cache_size` で調整可能）が付いており、`set` / `delete` / 設定のホットアップデート（`config.updated` / `config.set`）で自動的に失効します
- すべての次元の設定は**即座に有効**になります、再起動は不要です
- スコープは**イベントごとの判断**であり、イベント間で状態を記憶しません：設定が変わると、次のイベントは新しいルールに従います

## 設定フォーマットの検証

ロード時 / ホットアップデート時に各セクションの設定フォーマットを検証します：型の間違ったセクション（例：`platforms` が文字列に設定されている）、不正な出力ルール（例：`allow` が数値に設定されている）、未知のアクション名、未知のトップレベルのキー（例：`alow` というスペルミス）は **WARNING** として出力され、対応するセクション / 条目は無視され、他の合法な設定は正常に有効になります——間違った設定は静かに失効するのではなく、警告されます。

## 一般的な問題と注意事項

### 1. 設定の階層と上書き

- モジュール次元：セッションレベル > Botレベル > プラットフォームレベル、**全体的に上書き**（子レベルで `merge = true` の場合は各エントリを並列に結合）。プラットフォームで `Chat` を許可し、Bot で `Music` を追加したい場合は、Bot レベルで `merge = true` を書くか、両方をリストに書く
- 身元次元：ユーザー > セッション > Bot > アダプタ、**最も具体的な**設定された戦略を取ります（例外許可ができます）
- コマンドのユーザーブラックリスト/ホワイトリスト：正確なコマンド名が glob キーに優先されます（`event.command.acl` を参照）

### 2. モジュール/コマンドが反応しない

まず作用域が原因かどうかを疑います：

```python
from ErisPulse import sdk

print(sdk.scope.is_allowed(event.get_platform(), bot_id, "MyModule", session_id))
print(sdk.scope.is_identity_allowed(event.get_platform(), bot_id, session_id, user_id))
print(sdk.scope.stats())   # module_filtered / identity_denied > 0 なら、ブロック記録がある
```

フィルタされた場合、デフォルトでは返信されません（モジュール次元と身元次元、ルールを暴露しないように）；`scope.blocked` ライフサイクルイベントをブロードキャストし、統計は継続的に蓄積されます；ACL で拒否されたコマンドは「権限不足」の返信を表示します。

### 3. 出力アクションが拒否されたときのトラブルシューティング

```python
from ErisPulse import sdk

print(sdk.scope.get("actions.MyModule"))
print(sdk.scope.stats())   # action_denied > 0 なら、呼び出しがブロックされている
```

ブロックは**明示的**です：拒否された呼び出しは `retcode = 34601` の標準の失敗レスポンスを返し、ネットワークリクエストは発生しません。

### 4. セッション識別子のプラットフォーム間隔離

`(platform, session_id)` 組み合わせが唯一の識別子です。`scope.sessions.onebot11."789"` は onebot11 でのみ作用し、telegram 上で同じ `789` のセッションには影響しません。身元次元のユーザーキーも同様です。

## 拓撲ツリーアプリケーションプログラミングインターフェース

`ModuleManager.get_topology()` と `AdapterManager.get_topology()` は、モジュール/アダプタの所属関係データを提供します。`sdk.get_topology()` は、作用域 `scope` を含む一括集約を行います：

```python
from ErisPulse import sdk

topology = sdk.get_topology()
# {
#   "modules": {                                   # モジュール → 持有するリソース
#     "Chat": {
#       "loaded": True, "enabled": True,
#       "commands": ["chat", "translate"],
#       "handlers": {"message": 2, "notice": 1},
#       "routes": {"http": ["/Chat/api"], "ws": [], "sse": []},
#       "lifecycle_hooks": 3,
#     }
#   },
#   "adapters": {                                  # アダプタ → Bot → 作用域
#     "onebot11": {
#       "status": "started", "enabled": True,
#       "bots": {"123456": {"status": "online", "scope": {...}}},
#       "scope": {"modules": [...], "blocked": [...]},
#     }
#   },
#   "scope": {                                     # 作用域（モジュール / 身元 / 出力アクション）
#     "platforms": {...}, "bots": {...}, "sessions": {...},
#     "identity": {"adapters": {...}, "bots": {...}, "sessions": {...}, "users": {...}},
#     "actions": {...},
#   },
# }
```

- モジュールのトポロジーは、登録されたコマンド、イベントハンドラ、HTTP/WS/SSEルート、ライフサイクルフックを統合し、モジュールリソースツリーを描画するのに便利です。
- アダプタのトポロジーは、各アダプタの状態、下位のBotの状態、およびプラットフォーム/Botレベルの作用域バインディング（モジュール次元）を統合します。
- **JSON安全出力**：`get_topology(json_safe=...)` はデフォルトで `True` であり、返された構造は直接 `json.dumps` できます——モジュール `info` は純粋なデータの `meta` サブテーブルのみ保持されます（`module_class` / `strategy` などの実行時オブジェクトは除外）、その他のノード（アダプタ作者が Bot `info` に挿入した任意のオブジェクトを含む）もバックアップで浄化されます（クラスオブジェクトは `__name__` を取得し、シリアライズできないオブジェクトは `str()` に退化します）。ダッシュボード / WebUI は直接シリアライズして返すことができます；原始オブジェクトが必要な場合は `json_safe=False` を渡します。



### 归属权（owner）系统

# 帰属システム

> [!TIP]
> **いつこのドキュメントを読むべきか**：リソースリークの調査、アンロード時のクリーンアップチェーンの理解、または帰属リソースの宣言を行う際。不要であれば読み飛ばしても、他の機能の利用には影響しません。

> **読み終えると分かること**：owner コンテキストがどのようにリソースを自動帰属させるか、帰属リソースの全体表、アンロード/無効化時の
> クリーンアップチェーンの完全なシーケンス、そしてどのリソースがアンロード時にクリーンアップされないか（設計上の境界）。
>
> **本ドキュメントで扱わないこと**：リソースが「いつ有効になるか」の権限判定（[スコープ](scope.md) を参照）；
> バックグラウンドタスクの推奨記述方法と強制キャンセルの境界（[ライフサイクル管理 · バックグラウンドタスクの帰属と自動キャンセル](lifecycle.md#バックグラウンドタスクの帰属と自動キャンセル) を参照）。


帰属はモジュールの「プラグアンドプレイ」の基石です：モジュールが読み込み期間中に登録したすべてのフレームワークリソースは自動的に記名され、
アンロード/無効化時に記名に基づいて一括回収されます——モジュール作者はリソースを宣言するだけで、クリーンアップロジックを手書きする必要はありません。

> **関連システム**：スコープはイベントディスパッチ時に「リソースが有効かどうか」を決定し、
> 帰属はライフサイクルにおいて「リソースの帰属先と、誰がアンロードされたときに回収されるか」を決定します。
> スコープの詳細は[統一コントロールプレーン](scope.md)を、バックグラウンドタスクの詳細は
> [ライフサイクル管理](lifecycle.md#バックグラウンドタスクの帰属と自動キャンセル)を参照してください。

{!--< tips >!--}
1. 帰属は**登録の瞬間**に `current_owner` に基づいて自動記録され、モジュールコードは一切変更不要
2. アンロード/無効化は同じクリーンアップチェーン（`_cleanup_module_registrations`）を共用し、各ステップの失敗は警告のみで中断しない
3. ユーザー設定セマンティクスのリソース（永続化オーバーライド / scope ルール / コマンド ACL）はモジュールのアンロード時にクリーンアップ**されない**
4. ツールモジュールが管理する外部ハンドルは `on_cleanup(cb)` でクリーンアップチェーンに組み込め、相手モジュールのアンロード時に自動コールバックされる（[ツールモジュールガイド](#ツールモジュールガイド他のモジュールのハンドルを管理する) を参照）
{!--< /tips >!--}

## owner コンテキスト機構

owner はコンテキスト変数 `current_owner` を通じて伝達されます（`ErisPulse.runtime.context`）：

```python
from ErisPulse.runtime import owner_scope, get_current_owner

with owner_scope("MyModule"):
    # この区間内で登録されるすべてのリソースは自動的に MyModule に帰属します
    assert get_current_owner() == "MyModule"
```

フレームワークは以下のタイミングで自動的に owner を注入します（モジュール/アダプターのコードで手動ラップは不要）：

| タイミング | owner 値 | 場所 |
|------|----------|------|
| モジュール `load()` | モジュール名 | インスタンス化 + `on_load` の全期間 |
| アダプター `start()` / `restart()` | プラットフォーム名 | アダプター起動の全期間 |
| `activate_on` 遅延ロード stub 登録 | モジュール名 | プレースホルダーコマンド/ハンドラー登録 |
| イベントハンドラー実行時 | ハンドラーの帰属モジュール名 | handler / コマンドエントリでの再注入 |

実行時の再注入とは、モジュールが `on_load` 内で宣言したコマンドハンドラーの**実行中**に
登録型 API（`sdk.adapter.on()`、`overrides.*.set(persist=False)` など）を呼び出した場合も、
同様に自動的に当該モジュールに帰属することを意味します。

### bind_owner：帰属をコールバックとスレッドエントリに縫い込む

`owner_scope` はコードブロックに作用します。`bind_owner(fn)` はコンテキストを関数そのものに「縫い込み」ます——
ラップした瞬間に `current_owner` をキャプチャし、その後は誰が、どのスレッドやイベントループから呼び出しても、
元の owner の身分で実行されます。新規スレッドはデフォルトで空のコンテキストを持ち
（Timer / watcher / サードパーティのスレッドプールのトリガーパスでは `current_owner` が None になります）、
その中で作成されたタスクは帰属テーブルに入らず、モジュールのアンロード時にキャンセルできません
（loop を跨いだ残留の原因の一つ）が、ラップすれば帰属が随伴します：

```python
from ErisPulse.runtime import bind_owner

class MyModule(BaseModule):
    async def on_load(self, event):
        # サードパーティのスケジューラ / スレッドプールに渡す前にラップします：
        external_scheduler.submit(bind_owner(self._poll))

    async def _poll(self):
        # 実行中は current_owner == "MyModule" となり、アンロード時に正しく回収されます
        ...
```

- `async` 関数は `async` のまま維持され、owner はすべての `await` を跨いで有効になります。通常の関数は同期実行中のみ有効です
- フレームワーク自身のエントリ（`self.spawn()` / コマンドハンドラー）はすでに自動的に帰属を持ち運ぶため、この関数は**フレームワーク外のトリガーパス**（外部スケジューラ、`threading.Timer`、コールバック登録表など）にのみ使用します

## 帰属リソースの全体像

モジュールが読み込みコンテキスト内で登録した以下のリソースはすべて帰属が記録され、アンロード/無効化時に自動回収されます：

| リソース | 登録方法 | クリーンアップ呼び出し |
|------|----------|----------|
| コマンド | `@command()` / コマンド dict 宣言 | `command.unregister_by_owner()` |
| イベントハンドラー | `@message` / `@notice` / `@request` / `@meta` | `handler.unregister_by_owner()` |
| アダプターイベントリスナー | `sdk.adapter.on()` / `raw=True` | `adapter.unregister_handlers_by_owner()` |
| アダプターミドルウェア | `@sdk.adapter.middleware` | 同上 |
| ルーティング（HTTP/WS/SSE） | `router.http()` / `websocket()` / `sse()` | ネームスペース別 + owner 別の二重フォールバック |
| ルーティングミドルウェア | `@router.middleware()` / `add_middleware()` | `router.unregister_all_by_owner()` |
| Dashboard ホームエントリ | `router.register_home_entry()` | `unregister_home_entries_by_owner()` |
| カスタムセッションタイプ | `register_custom_type()` | `unregister_custom_types_by_owner()` |
| プラットフォームイベントメソッドの注入 | `register_event_method()` / `register_event_mixin()` | `unregister_event_methods_by_owner()`（モジュールのアンロード時に自動回収、旧クロージャのリークは解消） |
| バックグラウンドタスク | `self.spawn()` | `cancel_owner_tasks()` |
| 外部帰属クリーンアップフック（ツールモジュール管理） | `runtime.on_cleanup(cb)` | `run_owner_cleanups()`（アンロード/無効化/アダプター終了チェーン内でトリガー） |
| ライフサイクルフック | `lifecycle.register()` | `lifecycle.unregister_by_owner()` |
| マスター身元プロバイダー | `master.provider` | `master.unregister_by_owner()` |
| i18n 翻訳キー | `I18nClass` 宣言（domain=モジュール名） | `i18n.unregister_domain()` |
| イベントオーバーライド（ランタイム） | `overrides.*.set(persist=False)` | `overrides.unregister_by_owner()` |
| インタラクションセッション（wait_reply 待機 / リース） | `event.wait_reply()` / `sdk.interaction.acquire()` | `interaction.cancel_by_owner()`（待機側は即座にキャンセルを受け取る） |
| コンテキストデータ | `runtime/context` owner 別に記録 | モジュール単位で精密にクリーンアップ |

アダプター側の対応リソース（プラットフォーム名を owner とする）は、アダプターの `shutdown()` / `restart()`
時に `_cleanup_adapter_resources` によって回収され、さらに以下を含みます：

| リソース | クリーンアップ呼び出し |
|------|----------|
| アダプター固有の `on()` ハンドラーとミドルウェア | `adapter.unregister_handlers_by_owner(platform)` |
| プラットフォームイベントメソッド拡張（`EventMixin`） | `unregister_platform_event_methods(platform)` |
| カスタムセッションタイプ | `unregister_custom_types_by_owner(platform)` |
| インタラクションセッション（当該プラットフォームで保留中の wait_reply / リース） | `interaction.cancel_by_platform(platform)` |
| i18n 翻訳ドメイン（domain=設定キー） | `i18n.unregister_domain(設定キー)` |
| 細粒度ネームスペースルーティング | `router.unregister_all_by_owner(platform)` |

## アンロード/無効化のクリーンアップシーケンス

`unload()` と `disable()` は同じクリーンアップチェーンを共用します（各ステップは独立した try/except で、
失敗はログ記録のみで**後続のクリーンアップを中断しません**）：

```mermaid
flowchart TD
    A["unload / disable"] --> B["on_unload()（タイムアウト保護）"]
    B --> C["バックグラウンドタスクのフォールバックキャンセル（cancel_owner_tasks）"]
    C --> C1["外部帰属クリーンアップフック<br/>（ツールモジュールの on_cleanup 登録、run_owner_cleanups でトリガー）"]
    C1 --> D["_cleanup_module_registrations<br/>＝ 帰属ファサード ownership.reclaim_sync()"]
    D --> D1["i18n 翻訳ドメイン"]
    D1 --> D2["ルーティング：ネームスペース + owner フォールバック<br/>（ルーティングオブジェクトの同一性による精密削除、<br/>ミドルウェア / ホームエントリを含む）"]
    D2 --> D3["アダプターイベントハンドラー / ミドルウェア"]
    D3 --> D4["コマンド + イベントハンドラー"]
    D4 --> D5["カスタムセッションタイプ"]
    D5 --> D5b["プラットフォームイベントメソッド注入"]
    D5b --> D6["ランタイムイベントオーバーライド（persist=False）"]
    D6 --> D7["マスター身元プロバイダー"]
    D7 --> D8["ライフサイクルフック"]
    D8 --> E["SDK 属性 + 遅延読み込みプロキシの削除"]
    E --> F["自動軽量監査：オーファン owner の警告"]
```

`sdk.uninit()` の終了時には別途グローバルフォールバックがあります：全アダプター shutdown → 全モジュール unload →
`router.stop()`（ルーティング/ミドルウェア/ホームエントリのクリア）→ `cancel_all_background_tasks()` →
イベントハンドラーとフックのクリア。

## 帰属の統一ファサード（ownership）

クリーンアップチェーンの16のステップは帰属統一ファサード `ErisPulse.Core.ownership` の下に集約され、
4つの動詞が「登録解除・カウント・スキャン・監査」をカバーします——各サブシステムの `*_by_owner` 登録解除
関数は変更されず、ファサードの内部実装として維持されます：

| 動詞 | 用途 |
|------|------|
| `ownership.reclaim(owner)` | owner 名下の全リソースを統一的に登録解除（タスクキャンセル → クリーンアップフック → 登録系リソース；非同期完全版） |
| `ownership.reclaim_sync(owner)` | 登録系リソースの登録解除（同期版、同期アンロードパス用） |
| `ownership.counts(owner=None)` | owner の登録中リソースの読み取り専用統計（None は全 owner） |
| `ownership.orphans()` | オーファンスキャン：リソースは登録中だが owner は既に登録解除済み（リークの確証リスト） |
| `ownership.audit(owner, deep=)` | リーク監査レポート（カウント + オーファン + オプションの gc インスタンス全数調査） |

```python
from ErisPulse.Core import ownership

ownership.reclaim_sync("MyModule")       # {'commands': 1, 'routes_http': 2, ...}
ownership.counts("MyModule")             # 登録中リソースのカウント
ownership.orphans()                      # [{"owner": "ghost", "total": 2, ...}]
```

**監査エントリ**：

- アンロード / リロード後の**自動軽量監査**：オーファン owner リソースを検出した時点で WARNING 警告（オーバーヘッドゼロのカウントスキャン）
- `sdk.module.audit(name, deep=True)`：モジュールインスタンスの gc 全数調査——インスタンスが回収できない場合、
  参照元の型を提示（「誰が旧インスタンスを掴んでいるか」を特定）；グローバル一時停止のオーバーヘッドがあるため、明示的なトラブルシューティングにのみ使用
- 深い全数調査は明示的な操作であり、設定キーは設けず、自動修復も行いません

## 入れ子ライフサイクル（ownership.nest）

> 本セクションの機能には ErisPulse **2.12+** が必要です。

あるモジュール（親）が別の一連の owner（子）を管理することを許可し、親が回収されると子も一括して回収されます。典型的なシナリオ：
スクリプトエンジンモジュール内でのサブプラグインの実行、Dashboard によるパネル拡張の管理、ツールモジュールによる外部レジストリエントリの代行管理。

```python
from ErisPulse.Core import ownership

ownership.nest("ScriptEngine", "ScriptEngine.plugin_a")
ownership.nest("ScriptEngine", "ScriptEngine.plugin_b")

ownership.nested_children("ScriptEngine")
# frozenset({"ScriptEngine.plugin_a", "ScriptEngine.plugin_b"})

ownership.unnest("ScriptEngine", "ScriptEngine.plugin_a")
```

| 項目 | 規約 |
|----|------|
| 回収順序 | 子が親より先；同一レベルは登録の逆順（後で登録されたものから回収） |
| 回収範囲 | リソースレベル（タスク / 接続 / ルーティング / コマンド / tracked リソース / クリーンアップフック）、**子のモジュールレベル `on_unload` はトリガーされない** |
| 循環検出 | `nest` は自己循環と既存の逆方向チェーンを拒否し、`False` を返して警告 |
| 子の先行消滅 | 子が独立して回収される（`reclaim` / `reclaim_sync`）際に自動的に `unnest` され、親側に dangling な関係は保持されない |
| タイムアウト | 個々の子の回収は `CLEANUP_CALLBACK_TIMEOUT_SECS` に制約される；タイムアウト時は警告し、親子関係を解除して続行 |
| 可観測性 | `ownership.counts(parent)` に `nested` カウントが追加；`ownership.orphans()` はネスト関係に対して推移閉包を計算し、親が消滅した残留関係も露出される |

**なぜ子の `on_unload` をトリガーしないのか**：モジュールの完全なアンロードはマネージャーレベルのフロー（遅延プロキシ、
sdk 属性、イベントブロードキャスト）を経由する必要がありますが、`ownership` ファサードはリソース回収のみを担当し、
レイヤーを跨ぐ呼び出しはアンロードロックの再入リスクをもたらします。子の `on_unload` が必要な場合は、
親が自身の `on_unload` 内で明示的に呼び出します：

```python
await self.sdk.module.unload(child, reason="cascade")
```

同期エントリ（`sdk.module.disable` など）はまず非同期カスケードをマークし、バックグラウンドタスクが子リソースを回収します；
`reclaim_sync` は非同期カスケードが進行していない場合にのみ、自身で子の登録系リソースをカスケードします。

## ホットリロード失敗時のロールバック

ホットリロードは「**アンロード前のスナップショット → 失敗時の自動復元 → on_load のリプレイ**」です：新バージョンの構文エラー、
依存関係の欠落、読み込み失敗時には、旧インスタンスと登録状態（レジストリエントリ、sdk 属性、sys.modules
エントリ）が自動的に復元され、その後帰属コンテキスト内で**旧インスタンスの `on_load` をリプレイ**します（`reason`
は `"rollback"`）。これにより、アンロード段階で切断された外部リソースが再構築されます；終了後、
`module.rollback` イベント（ペイロード `{module_name, success}`）を発行します。

アダプターのホットリロード失敗も同様に旧登録状態を復元します；旧インスタンスが実行状態にあり、旧起動タスクが既に終了している場合、
ロールバック後に `start()` をリプレイし、`adapter.rollback` イベント（ペイロード
`{adapter_name, replayed, success}`）を発行します。切断 / bot offline などの unload 副作用
は依然として取り消せません。リプレイと `adapter.rollback` イベントには ErisPulse **2.12+** が必要です。

境界に関する注意：

- リプレイの失敗またはタイムアウトは**警告のみ**で、ロールバックを取り消しません——旧インスタンスは「クリーンアップ済み」状態に留まります
  （2.11.2 以前の動作と一致）。ログに明確に提示されます
- サードパーティが実行時に手動でキャッシュした旧インスタンスへの参照は復元範囲外です
- 対象パッケージが既にアンロードされている（entry-point が消失）場合はアンロード成功とみなし、ロールバックしません
- `on_unload` のペイロードには `reason`（`unload` / `reload` / `disable` /
  `cascade` / `dormant` / `load-failed`）が含まれ、モジュールは `reload` 時に
  リロードを跨いで存続すべきリソースのクローズを延期できます

ホットリロードの完全な能力境界、ループを跨ぐセマンティクス、モジュール側のガイドラインについては次のセクションを参照してください。

## ホットリロードの境界

ホットリロードはコードの置換、登録の再構築、失敗したリロードのロールバックが可能です——しかし、それは**プロセスの再起動ではありません**。
回収されるのは**帰属システムに登録されているランタイムリソース**です；どの owner にも属さないリソース、ユーザー
設定セマンティクスのデータ、サードパーティライブラリ内部にキャッシュされた参照は、リロードと共に消えることはありません。

### 能力の境界

| 対象 | リロード後の動作 | 説明 |
|------|-----------|------|
| モジュールコード / クラス定義 | 対応、再インポート | 旧 `sys.modules` エントリはクリアされる |
| `on_unload` / `on_load` | 対応、順次トリガー | 失敗ロールバック時に `on_load` をリプレイ（前セクション参照） |
| コマンド / ハンドラー / ルーティング / ライフサイクルフック | 対応、自動的に登録解除して再登録 | 帰属回収チェーンを経てクリーンアップ |
| `spawn_background` / `spawn_later` / `spawn_thread` | 対応、owner 別にキャンセル | スレッドは観測登録のみで強制終了は不可 |
| メインループ上の任意の `asyncio.create_task` | 対応、自動帰属キャンセル | タスクファクトリが傍受（サードパーティライブラリ内部での作成を含む） |
| ストレージブリッジループ上で派生したタスク | 対応、自動帰属キャンセル | ブリッジループにもタスクファクトリが導入済み |
| `ownership.track()` で登録されたリソース | 対応、`release()` を呼び出し | タスクファクトリが届かない Loop-bound リソース |
| `on_cleanup` フック | 対応、トリガー | ツールモジュールはこれにより管理していたハンドルを破棄 |
| 永続化オーバーライド（`persist=True`）/ 設定ファイル | 非対応、保持 | ユーザーアセット |
| サードパーティライブラリ内部にキャッシュされたオブジェクト参照 | 非対応 | フレームワークからは見えないため、モジュール自身が参照を解除する必要がある |
| モジュールが自身で `new` したイベントループ / 生スレッド | 回収しない | 以下のガイドラインを参照 |

### 3層リソースガバナンス

1. **シームレス傍受層**——イベントループレベルのタスクファクトリ。owner コンテキスト内での任意のタスク作成は自動的に帰属し、
   メインループとストレージブリッジループをカバーします。
2. **帰属化スケジューリング層**——`spawn_background` / `spawn_later` / `spawn_thread`。
3. **協調登録層**——`ownership.track()` / `on_cleanup()`。構造的に
   届かないリソース（Loop-bound 接続プール、サードパーティ client）用です。

### イベントループの境界

| ループ | 作成者 | タスクファクトリ | 用途 |
|------|--------|-----------|------|
| メインループ | `sdk.run()` / `sdk.init()` | 導入済み | すべてのビジネスコード |
| ストレージブリッジループ | `AsyncBridge`（初回の同期ストレージ呼び出し） | 導入済み | 同期ストレージ API のバックグラウンド実行 |
| 一時ループ | `spawn_background` のフォールバック | 未導入、使用後即クローズ | メインループ未準備時の最終手段 |

**一時ループは最終手段です**：呼び出し元スレッドを同期的にブロックし、ループが閉じられた後にコルーチン内部でさらに派生した
サブタスクは失われます（ログに `temp_loop_fallback` 警告が出力されます）。この警告が表示された場合は、モジュールが誤った
タイミングでバックグラウンドタスクをスケジューリングしたことを意味します。

**ループを跨ぐキャンセルはベストエフォートです**：`cancel_owner_tasks` がタスクが他の実行中のループ上にあることを検出した場合、
`call_soon_threadsafe` でキャンセルを投函し `cross_loop_task_residual`
警告を出しますが、その終了を**待機しません**（ループを跨ぐ待機は安全ではないため）。この警告が表示された場合は、
イベントループを自作していないか確認すべきです。

### モジュール側のガイドライン

```python
# 推奨
spawn_background(self._poll())            # 帰属化バックグラウンドタスク
spawn_later(30, lambda: self._cleanup())  # 帰属化遅延タスク
spawn_thread("poller", self._loop_body)   # 帰属化スレッド（エントリは自動的に owner を帯びる）
ownership.track(pool)                     # Loop-bound リソースを明示的に登録
await sdk.storage.aget(key)               # 非同期コンテキストでは非同期 API を直接使用

# 避けるべき
asyncio.create_task(self._poll())         # 生呼び出し：参照がなく GC されやすい
asyncio.new_event_loop()                  # 自作ループ：帰属システムは完全に届かない
threading.Thread(target=self._loop_body)  # 生スレッド：エントリに owner コンテキストがない
self._storage.get(key)                    # 非同期コンテキストでの同期ストレージ呼び出し：メインループをブロックする
```

### トラブルシューティングチェックリスト

1. ログに `cross_loop_task_residual` がある？→ リソースが自作ループ上に存在する
2. ログに `temp_loop_fallback` がある？→ バックグラウンドタスクがメインループの準備前にスケジューリングされた
3. `attached to a different loop` エラー？→ 自作ループまたはループを跨ぐ接続オブジェクトの再利用を確認する
4. `ownership.orphans()` に出力がある？→ owner 名下のリソースがアンロード後も生存している

## 設計上の境界：アンロード時にクリーンアップされないリソース

帰属は**モジュールコードが登録したランタイムリソース**のみを回収します。以下のリソースは**ユーザー設定セマンティクス**に属し
（制御権はユーザーにあり、意図的に設定されている可能性があります）、モジュールのアンロード後も設定と共に永続的に保持されます：

| リソース | セマンティクス | 説明 |
|------|------|------|
| `overrides.*.set(persist=True)` | 永続化オーバーライド | 設定ファイルに書き込まれ、再起動を跨いで有効；モジュールのアンロードでは削除しない（ユーザーの明示的設定） |
| `scope.set_action()` などのスコープルール | 権限コントロールプレーン | ユーザー/Dashboard が管理し、モジュールのアンロードではルールを回収しない |
| `overrides.acl.set(persist=True)` | コマンド ACL | 同上 |
| Conversation `save()` 永続化 | マルチターン会話アーカイブ | データアセットはクリーンアップしない |

ランタイムの一時書き込み（`persist=False`）は owner と共に回収されます——**永続化するかどうかが
「ユーザーアセット」と「モジュールのランタイム状態」の境界線です**。

## 内部実装：帰属の仕組み

**一言で言えば**：アトリビューションチェーン（contextvar の伝播）が「誰の勘定に記録されるか」を決め、キャンセルチェーン（タスク登録表）が「アンロード時にキャンセルできるか」を決めます——2つのチェーンは独立して動作し、リソースが正しくクリーンアップされるには両方が揃う必要があります。

帰属システムは**2つの独立したチェーン**で構成されており、それらの役割分担を理解することが帰属問題のトラブルシューティングの前提です：

### アトリビューションチェーン（contextvar の伝播）

`runtime/context.py` の `current_owner` などの ContextVar は**アトリビューション**を担当します——
「この瞬間にこのコードが登録したリソース/発した呼び出しが誰の勘定に記録されるか」。伝播ルールは Python
contextvars のセマンティクスに従います：

| 実行パス | context が伝播するか | アトリビューション結果 |
|---------|----------------|---------|
| 同期呼び出しチェーン / `await` チェーン | ✅ 伝播 | 正しいアトリビューション |
| `owner_scope` 内の `asyncio.create_task` | ✅ 伝播（task は作成時点の context をコピー） | タスク**内部**のフレームワーク呼び出しは正しくアトリビュートされる |
| `run_in_executor` / 生スレッド | ❌ 非伝播 | アトリビューション喪失 |
| 自作イベントループ | ❌ 非伝播 | アトリビューション喪失 |

> アトリビューション ≠ 登録：context の伝播は「誰の勘定に記録されるか」にのみ影響し、リソースがクリーンアップされるかどうかは
> 後述のキャンセルチェーンに入ったかどうかに依存します。

### キャンセルチェーン（タスク登録表）

`runtime/tasks.py` の `_owner_tasks` 登録表は**ライフサイクル**を担当します——
「owner 名下にどの未完了タスクがあり、アンロード時に一括キャンセルされるか」。タスクが登録表に入る経路：

1. **明示的スケジューリング**：`spawn_background()` / `self.spawn()` → 作成時に
   `current_owner` をキャプチャ（または明示的な `owner=` 引数）→ 登録表に登録；
2. **Task Factory による自動登録**（2.8.3）：`install_owner_task_factory()`
   がフレームワーク起動時にメインイベントループへ導入——**あらゆる**タスク作成（サードパーティライブラリ内部の
   `create_task` を含む）がファクトリを通過する際に `current_owner` を読み取り、None でなければ登録。

登録表は自己クリーンアップします：各タスクには `done_callback` が付いており、完了した時点で表から削除されるため、リークはありません。

### キャンセルシーケンス（モジュールのアンロード）

```
module.unload()
  → on_unload(event)                    # モジュール自身のクリーンアップ（フォールバックのタイムアウト保護）
  → フレームワークが当該 owner のコマンド/イベント/フック/ルーティングを登録解除
  → cancel_owner_tasks(owner)           # タスク登録表によるフォールバックキャンセル
      → 順次 task.cancel()              # 現在キャンセルロジックを実行中のタスク自身を除外
      → await gather(pending, timeout)  # 回収を待機（タイムアウト時はブロックしない）
```

### トラブルシューティングのアプローチ

- **リソースがクリーンアップされない** → 登録表を確認：`get_owner_tasks("MyModule")` にそのタスクが含まれているか；
  含まれていなければ、登録パスが帰属チェーンを通っていない（import 時 / スレッド / 独立ループ）。上の表と突き合わせて特定します。
- **アトリビューションエラー** → エラーが起きた時点の `get_current_owner()` の値を確認；非同期遅延実行
  （コールバック/タスク）のアトリビューションは実行時ではなく作成時の context から取得されます。

## モジュール作者ガイド

### 推奨記述方法

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
from ErisPulse.runtime import owner_scope, spawn_background

class MyModule(BaseModule):
    async def on_load(self, event):
        # フレームワークリソース：自動帰属、手動クリーンアップ不要
        self.task = self.spawn(self.polling())      # バックグラウンドタスク
        sdk.router.register_home_entry("マイモジュール", "/my")  # ホームエントリ

        # モジュール固有リソース：owner_scope で包めば帰属システムに組み込まれる
        with owner_scope("MyModule"):
            self.client.on_event(self._handle)      # 仮想的なカスタム登録

    async def on_unload(self, event):
        # フレームワークリソースは自動回収済み。owner_scope でカバーできない固有リソースのクリーンアップのみ必要
        await self.client.close()
```

### 注意事項

- **import 時の登録は帰属なし**：モジュールのトップレベル（import 時）で登録されたフック/ハンドラーは
  `owner_scope` より前に発生するため、フレームワークレベルのリソース（owner=None）とみなされ**クリーンアップされません**。
  必ず `on_load()` 内で登録してください。
- **カスタム domain の i18n 登録**：`i18n.register(domain=...)` の domain
  がモジュール名と異なる場合は自動回収されません。domain=モジュール名を維持してください。
- **バックグラウンドタスクには `self.spawn()` を推奨**：2.8.3 以降は生の `asyncio.create_task` も**自動的に暗黙帰属**します
  （Task Factory が自動登録し、アンロード時にフォールバックキャンセル）；ただし `self.spawn()` が依然として推奨記述方法です——
  非メインループスレッドからメインループへのスケジューリング、明示的な `owner=` 指定、fire-and-forget の GC 防止に対応しています。
  **2.8.3 以前**のバージョンでは生タスクは帰属しないため、`self.spawn()` を使う必要があります。
- クリーンアップチェーンの「失敗は警告のみ」：単一ステップのクリーンアップ例外は他のリソース回収を妨げません。ログは DEBUG/WARNING
  レベルで確認でき、トラブルシューティング時には TRACE を有効化できます。

### 登録タイミング → 帰属結果の対応表

| 登録シナリオ | 帰属結果 | 説明 |
|---------|---------|------|
| `on_load()` 内でフレームワーク API（コマンド/イベント/lifecycle/ルーティングデコレーター）経由で登録 | モジュールに帰属 | アンロード時に自動登録解除 |
| モジュールのトップレベル（import 時）での登録 | **帰属なし**（owner=None） | クリーンアップされないため使用しないこと |
| `self.spawn()` で作成されたバックグラウンドタスク | モジュールに帰属 | アンロード時に自動キャンセル |
| `owner_scope("Name")` 内でサードパーティ API 経由で登録 | モジュールに帰属 | サードパーティのコールバックが scope 内で同期的に実行されることに依存 |
| 生の `asyncio.create_task`（`loop.create_task` / `ensure_future` を含む） | **自動帰属**（Task Factory、2.8.3+） | 作成の瞬間に `current_owner` を読み取り、owner コンテキスト内で自動登録、アンロード時にフォールバックキャンセル；下記の[内部実装](#内部実装帰属の仕組み)を参照 |
| サードパーティライブラリの非同期コールバック（aiohttp / APScheduler など）内部で作成されたタスク | **自動帰属**（Task Factory、2.8.3+） | コールバック実行時に `current_owner` が注入されていれば（フレームワークハンドラー実行期間など）、タスクは自動登録される |
| `run_in_executor`（スレッドプール） | **帰属なし**（asyncio.Task ではない） | スレッドはタスクファクトリの管轄外のため、ライフサイクルは自己管理が必要 |
| 独立イベントループ（自作 loop）内での登録 | **帰属なし** | Task Factory はメインループにのみ導入；contextvars もイベントループを跨いで伝播しない |

> 原則：**帰属は登録の瞬間の `current_owner` コンテキストに従います**；非同期の遅延、
> スレッドプール、独立ループはいずれもこのコンテキストから離脱します——帰属が必要な場合は明示的に `owner_scope` に入ってください。

## ツールモジュールガイド：他のモジュールのハンドルを管理する

**シナリオ**：定期タスク、レジストリ、接続プールといった「ツールモジュール」は、他のモジュールの代わりにものを保管します——
相手が `on_load` 内で `sdk.Cron.on_trigger(handler)` を呼び出すと、あなたのコンテナには相手のインスタンスを指す
コールバックが保存されます。フレームワークは相手が登録したすべてのフレームワークリソースを自動的にクリーンアップしますが、
あなたの**プライベートコンテナ内の参照**はクリーンアップできません：相手がアンロードされた後もあなたのコンテナがそのインスタンスを引き留めているため、
GC による回収ができません（メモリリーク、`purge` のリーク診断が「回収不可」と報告します）。

**解決策**：相手のものを登録する同じ関数内で `on_cleanup()` を呼び出すと、
フレームワークは相手のアンロード / 無効化時にあなたのクリーンアップ関数を自動的にコールバックします：

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.runtime import off_cleanup, on_cleanup

class CronModule(BaseModule):
    def __init__(self):
        self._entries = {}  # {モジュール名: そのモジュールが管理するコールバックのリスト}

    def on_trigger(self, handler):
        # 呼び出し元モジュール名を自動識別（on_load からの直接呼び出し / module.call いずれも正しく処理）、
        # 戻り値は解析された owner で、そのまま記名キーとして使用可能
        owner = on_cleanup(self._drop)
        self._entries.setdefault(owner, []).append(handler)

    def _drop(self, owner: str):
        """相手モジュールがアンロード/無効化された際にフレームワークが自動的に呼び出す：ハンドルを破棄するだけでよい"""
        self._entries.pop(owner, None)

    async def on_unload(self, event):
        off_cleanup(self._drop)  # ③ 自身のアンロード前にフックを登録解除し、フックテーブルが self を保持するのを回避
```

フレームワークが保証する動作：

| 項目 | 動作 |
|--------|------|
| トリガータイミング | 相手モジュールの unload / disable、またはアダプターの終了——いずれもフレームワークのクリーンアップチェーン内でトリガーされ、purge のリーク診断より早い |
| 呼び出し元の識別 | 直接呼び出しでは `current_owner` を取得；`module.call()` 経由の呼び出しでは呼び出し元（`current_caller`）を取得；`on_cleanup(cb, owner="モジュール名")` で明示的に指定することも可能。**強制検証**：owner が解決できない場合（3つのソースすべてが欠落）は `ValueError` をスロー——プライベートツールモジュールは自身の読み込みコンテキスト内でフックを登録すべきです |
| コールバックシグネチャ | `cb(owner: str)`、同期 / 非同期いずれも可；非同期はタイムアウト保護付き（`CLEANUP_CALLBACK_TIMEOUT_SECS`、デフォルト 10 秒） |
| フォールトトレランス | 個々のコールバックの例外 / タイムアウトはログ記録のみで、他のフックとクリーンアップチェーンには影響しません |
| 重複登録 | 同一の `(owner, callback)` は冪等に重複排除 |

**不要な場合**：相手が登録したのがフレームワークリソース（コマンド、イベントハンドラー、ルーティング、
バックグラウンドタスクなど）であれば、フレームワークが完全に自動でクリーンアップします（上記の[帰属リソースの全体像](#帰属リソースの全体像)を参照）。
あなたのプライベートコンテナ内に保持している相手のハンドルにのみ `on_cleanup` が必要です。
モジュール開発の視点からのクイックリファレンス版は
[ベストプラクティス · ツールモジュール](../developer-guide/modules/best-practices.md#ツールモジュール他のものを管理する際はアンロード通知を受け止める) を参照してください。



### 影子模块与灰度转正

# シャドウモジュールとカナリア昇格

> [!TIP]
> **このドキュメントを読むべきタイミング**：カナリアリリース——新バージョンの並行トライアル実行、動作比較、昇格・ロールバックが必要なとき。不要であればスキップしても、他の機能の利用には影響しません。

> **読み終えるとわかること**：シャドウモジュールの5つの分離ゲート、動作 diff のアライメント方法、
> `promote` による昇格と失敗時のロールバック手順、そしてフレームワークでは防げない誠実な限界。
>
> **このドキュメントでは扱わないこと**：通常モジュールのホットリロードとオーナーのクリーンアップに関する汎用メカニズム
> （[オーナー（owner）システム](ownership.md) を参照）。


シャドウ = 同一モジュールの**新バージョン**であり、独立した owner（例：`roll_shadow`）として本番の旧バージョンと
共存しながらトライアル実行します：実際のイベントの**コピー**を受け取り、そのアウトバウンドは本当に送信されるのではなく
**傍受して記録**されます——`shadow_diff` で2つのバージョンの動作を比較し、無害であることを確認したら `promote` で
ワンクリック昇格、`dismiss` でいつでも破棄できます。**モジュールコードは一切変更不要、全工程がランタイム API 駆動**：
`load / unload / reload` と同種の運用アクションであり、Dashboard / カスタム管理モジュールから直接
呼び出せ、書くべき設定項目は一切ありません。

{!--< tips >!--}
1. 起動：``await sdk.module.shadow_start("roll", source="path/to/v2")``
   ——新バージョンのコードは独立した owner（デフォルトはパス名）として旧バージョンと共存
2. シャドウは実際のディスパッチと依存グラフには参加しません：同名コマンドはシャドウのカタログに入り、ルートは登録のみでマウントせず、
   ライフサイクルブロードキャストはサイレント、`module.call` と依存解決は引き続き v1 を指します
3. 昇格は常に人間が確認します：``await sdk.module.promote_shadow("roll")``、失敗時は
   自動ロールバックで旧インスタンスがサービスを継続；``dismiss_shadow`` でいつでも破棄
{!--< /tips >!--}

## クイックスタート

```python
# v2 コード：通常のモジュールの書き方、シャドウを一切意識しない（任意のディレクトリ、例：downloads/roll_v2/）
```

```python
# 本番ボット内で（Dashboard / 管理モジュールから呼び出し）、1行でカナリアを起動：
await sdk.module.shadow_start("roll", source="downloads/roll_v2")
# → シャドウは独立した owner "roll_v2" として v1 と共存し、アウトバウンドは傍受・記録される

# トライアル実行中に動作を比較：
report = sdk.module.shadow_diff("roll")
# {"shadow_owner": "roll_v2", "count": 3, "aligned": [...]}
```

- **v1 の実際の送信**：受信箱（transcript）からの bot タイムライン
- **v2 の送信意図**：シャドウ台帳（アウトバウンドゲートが記録した「送りたかったもの」）
- 両者は `trace_id` で整列されます——同じメッセージについて、2つのバージョンがそれぞれなぜ発火した/しなかった、
  何を送りたかった/実際に送ったのかが一目瞭然

問題ないことを確認したら昇格：

```python
await sdk.module.promote_shadow("roll")   # 昇格、失敗時は自動的に v1 へロールバック
await sdk.module.dismiss_shadow("roll")   # または：シャドウを破棄
```

## 5つの分離ゲート

| ゲート | メカニズム |
|----|------|
| イベントコピー | シャドウハンドラーはイベントの**独立したコピー**を受け取る（`shadow` マーク付き）——シャドウによる改変 / 引き取り / 伝播停止はコピーにのみ作用し、元のイベントチェーンには影響しない |
| アウトバウンドゲート | シャドウの `Send` DSL と `Api` 呼び出しはすべて傍受して記録（成功形状のフェイクレスポンスを返却）、実際には送信しない——シャドウが重複して返信することはない |
| ストレージオーバーレイ | シャドウの KV 書き込みはメモリ上のオーバーレイに入り、実DBへの永続化は破棄；読み取りはまずオーバーレイを確認し、ミスなら実DBへ透過（カナリアは実際のデータに対して実行）；削除はトゥームストーンとして記録 |
| ルートブロック | シャドウの HTTP/WS/SSE ルートは登録のみでマウントしない；同名コマンドはシャドウのコマンドカタログに入り、プラットフォームイベントメソッドの注入は禁止 |
| ライフサイクルサイレント | シャドウは自身のライフサイクルイベントをブロードキャストせず、エコシステムの依存グラフに参加しない（`module.call` と依存解決は引き続き v1 を指し、未完成品が依存されるのを回避） |

設定の継承：シャドウはデフォルトで**元モジュールの設定セクションを継承**します（そうでないとカナリアの結果が歪みます）。昇格後は設定がそのまま有効になります。

## 誠実な限界（防げないもの）

- フレームワーク経由の送信 / API / KV ストレージ / 統一 HTTP クライアントは**すべて傍受可能**；
  モジュールがフレームワークを迂回して生の `aiohttp` を起動したり、スレッドを立てて外部システムへ書き込むことは——フレームワークでは防げません
- **ORM の読み書きはオーバーレイのセマンティクス外**です（行単位の overlay は SQL レイヤーではクリーンに実装できない）——
  シャドウ期間中は ORM 書き込み分離への依存を避けることを推奨
- **シャドウソースはローカルパス**：新バージョンのコードはパスからインポートされ、独立した owner としてロード；同一 PyPI パッケージは
  同一インタプリタ内では `sys.modules` の単一キー制限を受け、新旧2バージョンの共存は不可能
- リーク監査器（`sdk.module.audit`）はシャドウリソースの帰属を可視化；フレームワークを迂回した副作用も、
  少なくとも無音のままにはなりません

## 昇格とロールバック

`promote` の流れ：現在のバージョンをスナップショット（カスケード依存を含む）→ 完全にアンロード → シャドウが実名で登録・ロード → いずれかのステップで失敗した場合は自動的にロールバックし、旧インスタンスがサービスを継続（ベストエフォートのセマンティクス：`on_unload` で実行された副作用は取り消せず、ロールバック後の旧インスタンスは終了処理済みの状態となる）。昇格に成功したシャドウのリソースは回収され、バインドは解除される。元モジュールの設定セクションはその場で有効になる。

**永続化に関する注意**：promote はランタイムでの切り替えです——再起動後も v2 で実行されるため、新しいバージョンを**永続的にインストール**する必要があります（新バージョンの `pip install -U` 実行 / プラグインファイルの置き換え）。ランタイムの切り替えはパッケージ管理を代行してはくれません。Dashboard の「昇格して永続化」は、昇格の成功後にバックグラウンドで pip を実行し、アップロード時にディスクへ書き込まれた whl 原本をインストールすることで、このステップを自動化します。通常の `promote` ではディスクへの書き込みは行われません。

## 3つのハード境界

| 境界 | 説明 |
|------|------|
| pip 排他 | シャドウ期間は**展開のみでインストールしない**：whl の原本を `shadows/<module>/` に保存するのは昇格後の永続化のためだけであり、シャドウ実行中は pip インストールを行わず、インストール済みパッケージの上書きによる本番環境の挙動ドリフトを回避します |
| promote はディスクに書き込まず | `promote_shadow` は実行時の切り替えのみを行い、パッケージマネージャーには書き込みません。再起動後は v1 にロールバックされます（設定では依然として旧バージョンを指しています）。再起動後も v2 を維持したい場合は「昇格して永続化」または手動の `pip install` を使用してください |
| サードパーティ依存関係 = プロセスにインストール済みのバージョン | シャドウが import するサードパーティライブラリは**現在のプロセスにインストール済みのバージョン**を使用します。whl が宣言する新規依存関係は自動インストールされず、依存関係が不足している場合はシャドウのロードに失敗します（エラーはそのままスローされます） |

> whl の取り込み、`list_shadows` および「昇格して永続化」（`shadow_ingest_whl` /
> `shadow_promote_persist` / `shadow_persist_status`）には ErisPulse **2.12+** が必要です。
> 旧バージョンの SDK では自動的に基本シャドウ（展開して起動するのみで、永続化なし）に縮退し、Dashboard の機能検出により自動的に切り替わります。

運用向けクエリインターフェース：`sdk.module.list_shadows()` は現在のすべてのバインディング
`{元モジュール名: シャドウ owner 名}` を返し、Dashboard / スクリプトでの集約表示に使用できます。

whl の取り込みと「昇格して永続化」の実装は SDK に帰属します：展開 / ディスクへの保存 / pip
オーケストレーションは SDK のバージョン進化に伴って変化し、Dashboard は単なる呼び出しエントリに過ぎません。



### 启动流程与手动控制

# 起動フローと手動制御

> [!TIP]
> **いつこのドキュメントを読むべきか**：起動チェーンを手動で駆動したい、起動順序をカスタマイズしたい、または起動失敗を調査する必要がある場合。不要であればスキップしても、他の機能の使用には影響しません。


ErisPulse の `await sdk.run()` / `await sdk.init()` は、起動チェーン全体を「1行のコード」にカプセル化しています。しかし、起動フローを完全にカスタマイズしたい場合（例：部分ロード、動的登録、ホットプラグ、カスタムロード戦略の注入）、このチェーンの内部で実際に何が起きているのか、そして各ステップをどう手動で駆動するのかを理解する必要があります。

このドキュメントでは、起動チェーンを独立したステップに分解し、それぞれの責務と呼び出し順序を説明し、完全な手動起動の例を示します。

> このドキュメントは、[最初のボット](../getting-started/first-bot.md) を既に実行したことがあり、`sdk.run(keep_running=True/False)` の2つのモードを理解していることを前提としています。本ドキュメントでは `init()` の**内部**におけるチェーンの分解と、`init()`/`init_task()`/`init_sync()` などのより低レベルなエントリポイントに焦点を当てます。

## SDK トップレベルエントリ一覧

`run()` の2つの `keep_running` モードに加え、SDK はいくつかのより低レベルな初期化エントリを提供しています。違いは**非同期性、戻り値、例外のラップ有無**です：

| エントリ | 非同期性 | 戻り値 | 例外処理 | 適用シナリオ |
|------|--------|--------|----------|----------|
| `await sdk.run(True)` | async、ブロックして維持 | `None`（終了時に自動 `uninit`） | モジュール/アダプタのエラーはインターセプトされ、プロセスをダウンさせない | 純粋な bot アプリケーション |
| `await sdk.run(False)` | async、ブロックしない | `None`（自動アンロードしない） | 同上 | 初期化後にカスタムロジックを実行 |
| `await sdk.init()` | async、await 必須 | `bool` | 内部でコンポーネントの例外をキャッチし、失敗時は `False` を返す | ライフサイクルの手動制御（`uninit()` と併用） |
| `sdk.init_task()` | async、Task を返しブロックしない | `asyncio.Task` | `init()` と同様 | 他の初期化の並行実行、またはイベントループがまだ実行されていない場合 |
| `sdk.init_sync()` | **同期**、現在のスレッドをブロック | `bool` | `init()` と同様 | コマンドラインスクリプト、イベントループのない同期エントリ |

> **よくある誤解**：`await sdk.init()` は `await sdk.run(keep_running=False)` と**等価ではありません**。2つの違いがあります：① `init()` は `bool` を返し（失敗時は `False`）、`run()` は `None` を返す；② `init()` は初期化のみを行い**自動アンロードしない**のに対し、`run()` はイベントループ終了時に自動的に `uninit()` します。したがって、手動でアンロードをペアリングしたりカスタムライフサイクルが必要な場合は、`init()` + `uninit()` を使用してください。

## 起動チェーン全体像

`sdk.init()`（正確にはその内部の `Initializer.init()`）は、以下の順序でフレームワーク全体を立ち上げます：

```mermaid
flowchart TD
    A[0. 環境の準備<br/>設定ロード / 例外処理] --> B
    B[1. 並行発見とロード<br/>AdapterLoader.load / ModuleLoader.load<br/>内部で Finder.find_all を呼び出し] --> C
    C[2. アダプタの登録<br/>AdapterLoader.register_to_manager] --> D
    D[3. アダプタの起動<br/>adapter.startup] --> E
    E[4. モジュールの登録<br/>ModuleLoader.register_to_manager] --> F
    F[5. モジュールの初期化<br/>ModuleLoader.initialize_modules<br/>インスタンス化して sdk にマウント] --> G
    G[6. ルーティングサーバーの起動<br/>router.start]
```

対応するコアコンポーネント：

| 層 | コンポーネント | 責務 |
|----|------|------|
| 発見 | `AdapterFinder` / `ModuleFinder` | インストール済みパッケージの entry-points からアダプタ/モジュールを**発見** |
| ロード | `AdapterLoader` / `ModuleLoader` | 発見 + インポート + メタデータ読み取り + 有効/無効の判定、オブジェクトリストを返す |
| 登録 | `*Loader.register_to_manager` | オブジェクトを対応するマネージャーに登録 |
| 管理 | `sdk.adapter` / `sdk.module` | アダプタ/モジュールインスタンスを管理し、起動・停止インターフェースを提供 |
| 初期化 | `ModuleLoader.initialize_modules` | モジュールインスタンスを作成して `sdk` にマウント（依存のトポロジカルソートを処理） |
| ルーティング | `sdk.router` | HTTP / WebSocket サーバー |

> **重要**：`Finder` と `Loader` は2つの層です。`Loader` の内部には**すでに** `Finder` が保持されています（`AdapterLoader` は `AdapterFinder` を、`ModuleLoader` は `ModuleFinder` を内蔵）。ほとんどのシナリオでは `Loader` だけを使用すればよく、「インポートせずに一覧表示だけ」が必要な場合にのみ `Finder` を単独で使用します。

## 各ステップの詳細

### 1. 発見層：Finder

Finder は「どのパッケージがアダプタ/モジュールを提供しているかを見つける」ことだけを担当し、インポートもインスタンス化も行いません。

```python
from ErisPulse.finders import AdapterFinder, ModuleFinder

adapter_finder = AdapterFinder()
module_finder = ModuleFinder()

# すべてのインストール済みアダプタ/モジュールの entry-points を検索
adapter_entries = adapter_finder.find_all()    # list[EntryPoint]
module_entries = module_finder.find_all()      # list[EntryPoint]

# 名前で単一のエントリを検索
entry = module_finder.find_by_name("MyModule")  # EntryPoint | None
```

各 `EntryPoint` は `.load()` で対応するクラスを取得できますが、通常は手動で呼び出す必要はありません——Loader が行います。

### 2. ロード層：Loader

Loader は Finder の上に「インポート + メタデータ読み取り + 有効/無効の判定」を実装しています。

```python
from ErisPulse.loaders import AdapterLoader, ModuleLoader
from ErisPulse import sdk

adapter_loader = AdapterLoader()
module_loader = ModuleLoader()

# load() 内部：finder.find_all() を呼び出し → entry-point を順次処理 → 三つ組を返す
adapter_objs, enabled_adapters, disabled_adapters = await adapter_loader.load(sdk.adapter)
module_objs, enabled_modules, disabled_modules = await module_loader.load(sdk.module)
```

`load()` が返す三つ組：

| 戻り値 | 意味 |
|--------|------|
| `objs` (`dict`) | 名前 → オブジェクト（アダプタクラス / モジュールラッパーオブジェクト） |
| `enabled` (`list[str]`) | 有効化された名前（設定で無効化されていない） |
| `disabled` (`list[str]`) | 無効化された名前 |

#### ロード失敗時の診断情報

モジュール/アダプタがロードまたは初期化段階で例外をスローした場合、フレームワークはそのコンポーネントをスキップして他のコンポーネントのロードを継続し、同時に**ユーザーコードフレームの要約**を出力します。これにより、デフォルトの INFO レベルのままでエラー発生位置を特定でき、手動で DEBUG に切り替える必要はありません：

```
[ERROR] [ModuleLoader] entry-point からのモジュール MyModule のロードに失敗、スキップしました: 'NoneType' object has no attribute 'platform'
  → MyModule/Core.py:42 in on_load
      adapter = sdk.platform
  → AttributeError: 'NoneType' object has no attribute 'platform'
  → ヒント: ログレベルを DEBUG に上げると完全なスタックトレースを確認できます；モジュール MyModule の実装コードを確認してください
```

診断情報は `ErisPulse.runtime.diagnostics` モジュールによって生成され、フレームワーク内部のフレームを自動的にフィルタリングし、あなたのコードフレームのみを保持します。カスタムロードロジックで再利用する場合：

```python
from ErisPulse.runtime import log_diagnostic

try:
    risky_init()
except Exception as e:
    log_diagnostic(e)  # 自動的にユーザーコードフレームを抽出し ERROR ログに書き込む
```

このモジュールは、`extract_user_frame()`（構造化フレーム情報を返す）と `format_diagnostic_block()`（複数行テキストを返す）という2つの低レベル関数も提供しています。

### 3. 登録層：register_to_manager

Loader が生成したオブジェクトをマネージャーに登録し、`sdk.adapter` / `sdk.module` がそれらを認識できるようにします。

```python
# アダプタを登録（bool を返し、すべて成功したかどうかを示す）
await adapter_loader.register_to_manager(enabled_adapters, adapter_objs, sdk.adapter)

# モジュールを登録
await module_loader.register_to_manager(enabled_modules, module_objs, sdk.module)
```

登録後、アダプタはアダプタマネージャーに、モジュールはモジュールマネージャーに登録されていますが、**どちらもまだ起動/インスタンス化されていません**。

### 4. アダプタの起動

```python
# すべての登録済みアダプタを起動
await sdk.adapter.startup()
# またはプラットフォームを指定
await sdk.adapter.startup("yunhu")
await sdk.adapter.startup(["yunhu", "telegram"])
```

> 登録 ≠ 起動。`register_to_manager` は登録のみを行い、`startup` が初めてアダプタの `start()` を呼び出してプラットフォームとの接続を確立します。

### 5. モジュールの初期化

モジュールはアダプタより1ステップ多く——**インスタンス化**して `sdk` にマウントする必要があります（これにより `sdk.MyModule.xxx` で呼び出せるようになります）。このステップでは、モジュール間の依存関係の宣言とトポロジカルソートも処理します。

```python
success = await module_loader.initialize_modules(
    enabled_modules, module_objs, sdk.module, sdk
)
```

インスタンス化に成功すると、モジュールは `sdk.<ModuleName>` に出現します。

### 6. ルーティングサーバーの起動

```python
await sdk.router.start(
    host="0.0.0.0",
    port=8000,
    ssl_certfile=None,
    ssl_keyfile=None,
)
```

ルーティングサーバーは、アダプタの Webhook / WebSocket コールバックを受信する役割を担います。起動しない場合、server モードのアダプタはメッセージを受信できません。

## 完全な手動起動の例

以下のコードは `await sdk.init()` のコアフローと**等価**ですが、各ステップがあなたの手に委ねられており、任意のステップでカスタムロジックを挿入できます：

```python
import asyncio
from ErisPulse import sdk
from ErisPulse.loaders import AdapterLoader, ModuleLoader

async def manual_startup():
    # 0. 環境の準備（設定のロード、グローバル例外処理の登録）
    #    _prepare_environment は init() 内部の前処理ステップ；手動フローでも先に呼び出す必要があり、
    #    呼び出さないと Loader が設定を読めず、すべてのアダプタ/モジュールを誤って無効と判定してしまいます。
    if not await sdk._prepare_environment():
        print("環境準備に失敗しました")
        return False

    # 1. ローダーの作成（内部にそれぞれ Finder を保持）
    adapter_loader = AdapterLoader()
    module_loader = ModuleLoader()

    # 2. 並行発見とロード（init() 内部と同様に gather を使用）
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

    # 6. モジュールの初期化（インスタンス化 + sdk へのマウント）
    if enabled_modules:
        await module_loader.initialize_modules(
            enabled_modules, module_objs, sdk.module, sdk
        )

    # 7. ルーティングサーバーの起動
    await sdk.router.start(host="0.0.0.0", port=8000)

    print("手動起動が完了しました")
    return True

async def main():
    ok = await manual_startup()
    if ok:
        # ブロックして実行を維持（手動フローは自動的にブロックしない）
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### いつ手動起動を使うべきか？

ほとんどの場合、手動起動は**必要ありません**。`await sdk.run()` が上記のすべてを既に行っています。手動起動が価値を持つのは、以下のシナリオのみです：

- **部分ロード**：指定したアダプタ/モジュールのみをロードし、他をスキップする
- **動的登録**：実行時に条件に応じて新しいアダプタ/モジュールを登録する
- **カスタム順序**：デフォルトのロード順序を変更する必要がある場合（例：特定のモジュールを先に起動してからアダプタを起動する）
- **戦略の注入**：Loader にカスタムの厳格モードマネージャーやロード戦略などを注入する
- **デバッグ/診断**：あるステップで失敗した際、手動で駆動して問題を特定する

## 実行時のきめ細かい制御

### ローカルプラグインのホットリロード

`sdk.enable_plugin_hot_reload()` はローカルプラグインディレクトリ（`plugins/`）のソース変更を監視し、自動リロードします：
`epsdk run` では自動的に有効になっているため手動呼び出しは不要です；**素の `sdk.run()` で起動**する場合にプラグインのホットリロードが必要なときは、
`run()` の前に1回呼び出してください（ローカルプラグインディレクトリのみを対象とし、pip でインストールしたモジュール/アダプタには影響しません）：

```python
sdk.enable_plugin_hot_reload()
sdk.run()
```


`sdk.run()` で起動を完了した場合でも、SDK 全体を再起動することなく、実行時に各サブシステムを個別に制御できます：

### アダプタのホット起動・停止

```python
# 特定のアダプタをホットリスタート（接続を修復、他のプラットフォームには影響しない）
await sdk.adapter.shutdown("yunhu")
await sdk.adapter.startup("yunhu")

# 実行中に新しいプラットフォームを立ち上げる
await sdk.adapter.startup("telegram")

# 特定のプラットフォームを一時的にオフラインにする
await sdk.adapter.shutdown("telegram")
```

> `adapter.startup()` はアダプタがマネージャーに**登録済み**であることを要求します。登録は `init()`/`run()` の内部で行われるため、これは起動**後**のきめ細かい制御です。

### ルーティングサーバー

```python
# webhook サーバーを一時的にオフラインにする
await sdk.router.stop()

# 再起動（例：ポートを変更した場合）
await sdk.router.start(host="0.0.0.0", port=9000)
```

### モジュールのオンデマンドロード

```python
# （遅延ロードの可能性がある）モジュールを手動でロードする
await sdk.load_module("MyModule")
```

## グレースフルシャットダウン

2.7.0 以降、`sdk.shutdown()` は**プログラムによるグレースフルシャットダウン**を提供します：シャットダウンイベントを設定し、`await sdk.run(keep_running=True)` で停止しているメインループを戻らせ、さらに `uninit()` をトリガーしてリソースクリーンアップを完了させます。

```python
# 任意のコルーチン内で呼び出し、グレースフル終了をトリガー（run() の停止が戻り、自動的に uninit）
sdk.shutdown()
```

典型的な使用例：

```python
async def shutdown_after_idle():
    await asyncio.sleep(3600)
    sdk.shutdown()  # アイドル1時間後にグレースフル終了
```

**シグナル処理**：`run()` 内部では `SIGTERM` / `SIGHUP` ハンドラーを登録し、システムシグナルをグレースフルシャットダウンに変換します——コンテナオーケストレーション（Docker `docker stop`）や `systemd` がサービスを停止する際、プロセスは強制終了されるのではなく `uninit()` クリーンアップを完了します。また `SIGUSR1` ハンドラーも登録されており、プロセス内ソフトリスタート（`sdk.restart()`）に変換されます——`epsdk restart` はコンテナ内 PID 1 インスタンス（終了するとコンテナが終了し、外部から再起動できない）に対し、代わりにこのシグナルを送信してコンポーネントのホットリロードをトリガーします。SIGUSR1 ホットリスタートチャネルには ErisPulse **2.12+** が必要です。

- Windows は `loop.add_signal_handler` をサポートしないため、シグナルハンドラーは自動的にスキップされます（`sdk.shutdown()` または Ctrl+C によるシャットダウンは引き続き可能）
- `sdk.shutdown()` を繰り返し呼び出すのは安全です（イベントが既に設定された後の再呼び出しは何もしません）

## アンロードフロー

起動の逆操作は `await sdk.uninit()` で、逆順にクリーンアップします：

1. すべてのアダプタをシャットダウン（`adapter.shutdown()`）
2. すべてのモジュールをアンロード
3. すべてのイベントハンドラーをクリーンアップ
4. マネージャーと SDK 上のモジュール属性をクリーンアップ

手動起動のシナリオでは、終了前に `uninit()` を呼び出してグレースフルシャットダウンを保証することを忘れないでください：

```python
try:
    await asyncio.Event().wait()   # 実行を維持
finally:
    await sdk.uninit()
```

## 再起動

SDK は2つの再起動方法を提供しており、どちらも自分で先にアンロードする必要はありません——フレームワークが自動的に処理します：

| 方式 | 呼び出し | 動作 | 適用シナリオ |
|------|------|------|----------|
| ホットリスタート | `await sdk.restart()` | 同一プロセス内での**コンポーネント層コードレベルホットリロード**：全モジュールが統一リロードパイプラインを通過（全体構文事前チェック / スナップショットロールバック / アイデンティティ検証）、アダプタはまず **entry-point を再発見**（実行中に新規インストール/アンインストールされたアダプタが即時有効）してから、1つずつコードレベルでリロード | pip でのアップグレードやコンポーネントインストール後にコードを有効化、モジュールのホット更新 |
| ハードリスタート | `await sdk.hard_restart()` | `uninit()` 後に**終了コード 42** でプロセスを終了し、外部スーパーバイザーが新しいプロセスを立ち上げ | フレームワーク自体のアップグレード（アップグレード後のフレームワークコードは新プロセスでのみ有効）、C 拡張の副作用、リソースリークの疑い |

```python
# ホットリスタート：コンポーネント層コードレベルホットリロード（最も一般的；pip で新規インストールしたアダプタも立ち上がる）
await sdk.restart()

# ハードリスタート：プロセスを終了し、外部スーパーバイザーに再起動を委ねる（下記「スーパーバイザーガイド」参照）
await sdk.hard_restart("sdk self-update")  # スーパーバイザー表示用のオプション reason
```

> **2つの注意点**：
> 1. これらのメソッドはどちらもバックグラウンドタスクで再起動を実行し、**即座に `True` を返します。これは「再起動タスクがスケジュールされた」ことを示すものであり、「再起動が完了した」ことを示すものではありません**。実際の再起動はバックグラウンドで行われ、現在のイベントチェーンの中断を避けます。
> 2. `hard_restart()` の仕組みは：アンロードして設定をディスクにフラッシュした後、**終了コード 42**（`HARD_RESTART_EXIT_CODE`）でプロセスを終了します——**それ自体は新しいプロセスを立ち上げません**。外部スーパーバイザーが終了コード 42 を検出した後に再起動する必要があります。直接 `python main.py` で実行し、スーパーバイザーが何もない場合、プロセスはコード 42 で終了したらそのまま終わり、**自動的に再起動しません**（フレームワークが警告を出します）。

> **ホットリスタートの相互排他と統合**（2.11.1 以降）：すべてのホットリロード操作（単一モジュールリロード / 全量リロード / アダプタリロード / 休眠 / 新規プラグインのホットロード）は全体を通じて相互排他です——保存ストーム下で連続トリガーしても並行で交錯することはなく、進行中の restart が新しいリクエストを受け取ると自動的に統合されます（リクエストが通常のリロードのロック保持期間中に発生した場合も同様に統合・キューイングされ、完了後に最大1ラウンド補完実行します）。構文エラーを含むファイルを保存した場合、全体のリロードラウンドはアンロード前に**集約的な構文事前チェック**で拒否され（すべてのエラーファイルと行番号を一括で列挙）、アダプタ層はこのラウンドのリロードをスキップし、`restart` は失敗と判定し、すべての旧インスタンスがサービスを継続します；修復後に再度 `restart` を実行すればよいだけです。

### いつハードリスタートを使うべきか？

ホットリスタートはすでにほとんどのシナリオをカバーしています（pip でのアップグレード/コンポーネントインストール、モジュールコードのホット更新、**実行中に新規インストールされたアダプタを含む**）。ハードリスタートが必要なのは、以下のシナリオのみです：

- **フレームワーク自体のアップグレード**：ErisPulse 本体をアップグレードした後、新しいフレームワークコードは完全に新しいプロセスでのみ有効になります（Python はロード済みのフレームワークコードを再 import しません）。
- **バイナリライブラリ（C 拡張）の副作用**：ホットリスタートは同一プロセス内で行われるため、C 拡張、開かれたファイルディスクリプタ、スレッドなどのプロセスレベルリソースを解放できません；ハードリスタートは完全に新しいプロセスに切り替わるため、これらの副作用は完全にリセットされます。
- **リソースリークの調査**：メモリやハンドルのリークが疑われる場合、ハードリスタートでクリーンな環境を取得できます。

> Dashboard 管理パネルの「フレームワーク再起動」機能は、内部で `hard_restart()` を呼び出しています。

### 終了コード 42 の契約

ハードリスタートはプロセス間の協調動作です：**SDK は終了（コード 42）を担当し、スーパーバイザーは再起動を担当します**。

| 役割 | 動作 |
|------|------|
| SDK（ハードリスタートされる側） | `uninit()` → 設定をディスクにフラッシュ → ハードリスタートマーカーを書き込み（理由 / PID、スーパーバイザー表示用）→ `os._exit(42)` |
| スーパーバイザー | 子プロセスの終了コードが 42 であることを検出 → ハードリスタート理由を表示 → 同じコマンドを再起動 |

> `sdk.is_supervised()` で現在のプロセスがスーパーバイザーによって起動されたかどうかを照会できます（環境変数 `ERISPULSE_SUPERVISED` を検出）。CLI `run` コマンドは子プロセスを起動する際にこのマーカーを自動的に注入します；systemd / Docker などの外部スーパーバイザーは注入しないため、`is_supervised()` は `False` を返し、この場合ハードリスタート後にフレームワークは「スーパーバイザーが検出されませんでした」という警告を出します。

### スーパーバイザーガイド

あなたに適したスーパーバイザーを選択し、ハードリスタートを実際に機能させましょう：

#### 1. CLI run コマンド（開発/シンプルなデプロイ、推奨）

`epsdk run main.py` には監視ループが組み込まれています：子プロセスの終了コードを検出し、42 の場合は即座に再起動（ハードリスタート理由も表示）；その他の異常終了コードは指数バックオフで自動リトライ；`Ctrl+C` はまず子プロセスをグレースフルに終了させます（コード 0 は正常終了とみなし、再起動しません）。

```bash
epsdk run main.py
```

`epsdk run --reload`（開発用ホットリロードモード、2.11.1 以降）も同様に「監視プロセス + リロード worker 子プロセス」構造を採用しています：worker 内で `.py` ファイルを保存すると**コンポーネントレベルのホットリロード**がトリガーされます（フレームワーク全体は再起動しない）；ハードリスタートは監視プロセスが新しい worker を再起動するため、フレームワークをアップグレードした後の新しいコードは即座に有効になります。

#### きめ細かいリロード判定（2.12+）

`.py` の保存後、実行時のソースコードの帰属に基づいて最小のリロード単位を選択し、パス文字列で推測しません：

| 変更ファイル | 処理 |
|----------|------|
| プラグインディレクトリ（`ErisPulse.framework.plugins_dir`）内 | プラグインホットリロード watcher が処理、dev watcher は重複トリガーしない |
| ロード済みモジュールのソース（`pip install -e` と site-packages を含む） | `sdk.reload_module(モジュール名)` |
| 登録済みアダプタのソース | `sdk.reload_adapter(プラットフォーム名)` |
| エントリスクリプト | プロセスレベル再起動（終了コード 42、スーパーバイザーが再起動） |
| フレームワーク自体のソース（`ErisPulse` パッケージ内） | プロセスレベル再起動 |
| 複数の owner に同時一致 / 帰属不能 | 保守的にプロセスレベル再起動 |

`epsdk upgrade` などの一括アップグレードシナリオでは、`sdk.reload_all_modules()` を使用して登録済みの
全モジュールを一度にリロードできます（依存のトポロジカル順序に従い、単一モジュールの失敗はスキップされロールバックしない）。プロセスの再起動は不要です。

スクリプトモード（`epsdk run main.py --reload`）はスクリプトを worker 化しません：スクリプト子プロセス内に
dev watcher をマウントし、`component_reload_pid` を `.erispulse/runtime.json` に書き込みます；親プロセスは
このマーカーを確認した後、モジュール/アダプタ/プラグインの変更を子プロセスに処理させ、エントリスクリプトまたはフレームワークソースの
変更のみがスクリプトプロセスの再起動を引き起こします。

#### 2. systemd（Linux サーバー）

`RestartForceExitStatus=42` により、終了コード 42 も再起動をトリガーします（デフォルトの `on-failure` は非ゼロコードにのみ有効）：

```ini
[Service]
ExecStart=/usr/bin/python3 /opt/mybot/main.py
Restart=on-failure
RestartForceExitStatus=42
RestartSec=2
User=mybot
```

#### 3. Docker / docker-compose

コンテナ内の PID 1 はアプリケーションプロセスであり、終了コード 42 の後にコンテナが終了します——`restart` ポリシーで自動再起動させます：

```yaml
services:
  bot:
    build: .
    restart: unless-stopped   # すべての終了（42 を含む）で再起動
```

> コンテナ内の `epsdk restart` は PID 1 インスタンスに対して SIGUSR1 によるプロセス内ホットリスタートを行い、コンテナは終了しません；
> プロセス全体の再起動は `restart` ポリシーが担います。詳細は [デプロイ → コンテナ内再起動](../user-guide/deployment.md#容器内重启pid-1-实例) を参照してください。

#### 4. PM2（Node エコシステム運用）

```bash
pm2 start main.py --name mybot --interpreter python3
# 42 は終了コードとみなされ、PM2 はデフォルトで再起動；restart_delay を設定してデバウンス
pm2 set mybot.restart_delay 2000
```

#### 5. supervisord

```ini
[program:mybot]
command=python3 /opt/mybot/main.py
autorestart=true
exitcodes=0,2,42    # 42 も「正常終了だが再起動が必要」とみなす
```

#### 6. 純 Python カスタムスーパーバイザー

```python
import subprocess, sys, time

while True:
    p = subprocess.Popen([sys.executable, "main.py"])
    code = p.wait()
    if code == 42:          # ハードリスタート要求
        time.sleep(0.5)
        continue
    if code == 0:           # 正常終了
        break
    time.sleep(3)           # 異常終了、バックオフリトライ
```

> **スーパーバイザーがない場合の動作**：直接 `python main.py` で実行した場合、`hard_restart()` を呼び出すとプロセスはコード 42 で終了し、再起動されません。この場合は上記のいずれかのスーパーバイザーを導入する必要があります。



### 性能基准与调优

# パフォーマンスベンチマークとチューニング

> [!TIP]
> **いつこのドキュメントを読むべきか**：イベントのスループットやレイテンシの数値に関心がある場合、デプロイ前のキャパシティ評価、バージョンアップグレード前後のパフォーマンスリグレッションを比較したい場合に読んでください。必要がなければ読み飛ばしても、他の機能の利用には影響しません。

## 実測ベンチマーク（2026-10-05、Python 3.13.14）

同一マシン上での前後2回の実測（ウォームアップ + 複数回のサンプリングによるパーセンタイル算出）、NoneBot2 2.5.0 は独立環境の対照。
すべての数値はリポジトリ同梱のベンチマークで再現可能：`python tests/performance/benchmark.py`。

### イベントディスパッチ（ops/s、値が高いほど良い）

| ベンチマーク項目 | ErisPulse | NoneBot2 2.5.0 | 比較 |
|---|---|---|---|
| バス単一ハンドラ逐次レイテンシ | **9,189** | 3,021 | 3.0× |
| バスフラッドスループット（1000 イベント/ラウンド） | **9,877** | 2,055 | 4.8× |
| 10 ハンドラ/イベント スループット | **4,309** | 435 | 9.9× |
| コマンドヒット（/コマンド） | **2,165** | 677 | 3.2× |
| コマンドミス（コマンド以外のメッセージ） | **10,818** | 921 | 11.7× |
| メッセージブリッジ単一ハンドラ（デフォルト全パイプライン） | **2,804** | 2,144 | 1.3× |

### その他サブシステムの能力（最適化後）

| ベンチマーク項目 | ops/s | ベンチマーク項目 | 数値 |
|---|---|---|---|
| getConfig ホット読み取り | 1,086,957 | ORM 単一 create | 407/s |
| KV aset（sqlite） | 1,659 | GET /health（ASGI） | 1,188/s |
| KV aget（sqlite） | 3,333 | module.call RPC | 148,905/s |
| エンドツーエンドメッセージ往復 | 298 | 混合負荷 | 142/s |

### 起動時間

| フェーズ | ErisPulse | NoneBot2 |
|---|---|---|
| インタプリタ空転対照 | 59.5ms | — |
| コールドインポート | 241.7ms | 249.6ms |
| sdk.init / NoneBot init | 30.8ms | 162.3ms |

## ベンチマークの実行とリグレッション比較

```bash
# クイックモード（サンプル数は約1/4、スモークテスト用）
python tests/performance/benchmark.py --quick

# 完全なベースラインをファイルに保存（8スイート：config/event/storage/send/router/module/overall/startup）
python tests/performance/benchmark.py --json baseline.json

# 旧ベースラインとの比較（差分が±5%の閾値内ならノイズとみなす）
python tests/performance/benchmark.py --compare baseline.json

# HTMLレポート / ストレージスイートのバックエンド指定
python tests/performance/benchmark.py --html report.html
python tests/performance/benchmark.py --backend mysql
```

> CI に関する注意：ベンチマークの数値はマシンによって変動するため、`--compare` の ±5% 閾値は**同一マシン**での前後比較（アップグレード検証）にのみ適しており、マシンをまたぐゲート判定には適していません。

## チューニングのポイント

1. **メッセージブリッジの全経路におけるボトルネックはセッション記録**：デフォルトで transcript 記録が有効（2.9 以降はメモリバッファ + バックグラウンドでの一括永続化）；監査要件がない場合は無効化可能で、全経路のスループットは約 2,804 → 3,774 ops/s に向上
2. **GC 管理**：`ErisPulse.framework` の proactive_gc 設定グループ（interval / full_every / memory_growth_mb / `idle_only`）——イベントのピーク時には自動的に GC をスキップ；init フェーズでの `gc.freeze()` は組み込み済み
3. **ストレージバックエンド**：ローカル単体の sqlite（WAL）で十分；マルチインスタンスでデータ層を共有する場合は mysql / postgres に切り替え（[ストレージバックエンド](storage-backends.md) を参照）
4. **ホットパスは最適化組み込み済み**（2.9 以降、設定不要）：transcript の一括永続化、i18n キャッシュ、ログレベルガード、マッチャーの事前コンパイル、設定の遅延書き込みと統一フラッシュ
5. **コマンド制御状態の上限**：クールダウン/レート制限/クォータの状態テーブルは上限 4096 件（超過時は最も古いものから削除）、超大規模グループ向けのデプロイでも調整不要

## メモリ診断

「実行するほどにメモリを多く消費する」問題を調査する際、疑わしい処理の前後にラベル付きのスナップショットを打つことで、同名のラベルが自動的に増分（RSS + tracemalloc 両指標）を計算します。

```python
from ErisPulse.runtime import log_snapshot, snapshot

class MyModule(BaseModule):
    async def on_load(self, event):
        snapshot("MyModule.load")            # dict（ラベルによる RSS delta 含む）を取得して返す

    async def on_unload(self, event):
        log_snapshot("MyModule.unload")      # 同じ口径で取得し TRACE レベルのログに記録
```

- `snapshot(label)` はマシンで読み取れる dict を返し、アサーションや報告に適しています。`log_snapshot(label)` は TRACE レベルのログに直接書き込み、一時的な調査に適しています。
- label は容量制限付きで、呼び出し回数に応じてメモリが漏れることはありません。`/metrics` エンドポイントのプロセス指標と併用することで、長期的な傾向を観察できます。
- モジュールのアンロード後に残る増加は、通常、所有権の欠如を示しています（[所有権システム](ownership.md)の `bind_owner` タスク項目を参照）。



### runtime 工具带

# runtimeツールベルト

> [!TIP]
> **このドキュメントを読むべきタイミング**: `ErisPulse.runtime` パッケージが提供する、直接 import できるランタイムツールを一括で把握したいとき。各機能の詳細な使い方は対応するトピックドキュメントに記載されており、本ページはクイックリファレンス索引 + トピックに属さない一部の機能の使い方説明です。

`ErisPulse.runtime` はフレームワークの集約エクスポート層です。各モジュールに散らばっているランタイムツールを単一のエントリーポイントに集約し、スクリプト、モジュール、アダプターのコードからは統一して `from ErisPulse.runtime import X` の形で利用できるため、深い階層のパスを覚える必要がありません。

## 機能クイックリファレンス

| カテゴリ | 名前 | 用途 | 詳細 |
|------|------|------|------|
| 所有権 | `bind_owner` | owner コンテキストをコールバック / スレッドエントリに紐付ける | [所有権システム](ownership.md) |
| 所有権 | `owner_scope` / `get_current_owner` | コードブロックレベルの所有権コンテキスト | [所有権システム](ownership.md) |
| 所有権 | `get_owner_tasks` / `cancel_owner_tasks` | 特定 owner のバックグラウンドタスクの照会 / キャンセル | [所有権システム](ownership.md) |
| バックグラウンドタスク | `spawn_background` / `spawn_later` / `spawn_thread` | バックグラウンドコルーチン / 遅延タスク / スレッドタスク | [ライフサイクル管理](lifecycle.md) |
| バックグラウンドタスク | `cancel_all_background_tasks` / `run_main_loop` | バックグラウンドタスクの集約とメインループ登録 | [ライフサイクル管理](lifecycle.md) |
| イベントコンテキスト | `get_current_trace_id` | 現在のトレース ID の取得 | [リンクトレーシング](interaction.md#リンクトレーシングtrace-id) |
| イベントコンテキスト | `get_send_receipts` | メッセージトランザクションの送信レシート台帳の取得 | [メッセージトランザクション](interaction.md#メッセージトランザクションmessage_tx) |
| イベントコンテキスト | `get_current_event_account` / `get_current_caller` / `get_handler_waits` | イベントアカウント / 呼び出し元 / 待機テーブルの読み取り | [インタラクションセッションシステム](interaction.md) |
| メモリ | `snapshot` / `log_snapshot` | label 付き RSS + tracemalloc スナップショット（増分を自動計算） | [メモリ診断](performance.md#メモリ診断) |
| メモリ | `get_rss_mb` / `get_traced_mb` | 現在のプロセスのメモリ使用量 | [メモリ診断](performance.md#メモリ診断) |
| 設定パース | `dict_to_dataclass` | dict → 型安全な dataclass インスタンス | 次のセクションを参照 |
| 設定パース | `dataclass_to_defaults_dict` / `dataclass_to_toml_with_comments` | dataclass → デフォルト値 dict / コメント付き TOML シリアライズ | [宣言的設定](../developer-guide/configuration.md) |
| トラブルシューティング | `explain_module` / `explain_event` / `explain_trace` | モジュール / イベント / メッセージチェーンの診断 | [起動時のトラブルシューティング](startup.md) と [イベント処理](../getting-started/event-handling.md) |
| トラブルシューティング | `format_diagnostic_block` / `log_diagnostic` / `extract_user_frame` | 例外診断ブロックの描画とユーザーフレームの抽出 | [起動フロー](startup.md) |
| 例外フォールバック | `setup_exception_handling` / `global_exception_handler` | グローバル例外ハンドラの登録 | [起動フロー](startup.md) |
| セキュリティ | `redact_secret` | ログ / レポート内の機密値のマスキング | [起動フロー](startup.md) |
| メトリクス | `metrics` / `MetricsRegistry` | ランタイムメトリクスレジストリ（`/metrics` エンドポイントのデータソース） | [デプロイガイド](../user-guide/deployment.md) |

## dict_to_dataclass：dict → 型安全オブジェクト

宣言的 dataclass 設定の「逆方向」——任意の dict（API レスポンス、webhook
payload、ユーザー入力）を宣言に従って型安全なインスタンスにパースし、手書きの
`data.get("x", default)` チェーンを置き換えます：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime import dict_to_dataclass

@dataclass
class WebhookPayload:
    order_id: str
    amount: float = 0.0
    tags: list = field(default_factory=list)
    remark: str = ""

payload = dict_to_dataclass(WebhookPayload, {
    "order_id": "A-1024",
    "amount": "99.5",          # str → float 自動変換
    "unknown_key": "無視",      # 未宣言フィールドは自動的に無視
})
payload.amount                   # 99.5（float）
```

- 型変換（str → int/float など）、デフォルト値の補完、ネストされた dataclass の再帰的補完
- 環境変数によるオーバーライド：フィールドに `metadata={"env": "NAME"}` が指定されている場合、優先順位は 環境変数 > データ > デフォルト値
- 宣言的設定クラス（`ConfigClass` / `BaseConfig`）のホットリロードコールバック内部では、まさにこれによって dict → 設定オブジェクトの変換が行われています



====
生态模块
====


### ErisPulse-App 安装与使用

# ErisPulse-App

> [!TIP]
> **このドキュメントを読むべきとき**：スマートフォンやパソコン上でグラフィカルインターフェースを使ってボットインスタンスの作成・実行・管理を行いたい場合——ターミナルに触れず、Python 環境も別途インストールせずに済むようにしたいときに読んでください。不要な場合はスキップしてください。

[ErisPulse-App](https://github.com/ErisPulse/ErisPulse-App) は ErisDev が直接メンテナンスしている**公式マルチプラットフォームクライアント**（Android / Windows / Linux / macOS すべてリリース済み）です。
完全にネイティブなグラフィカル管理インターフェースを提供し、スマートフォンやパソコン上で複数のボットインスタンスを作成・実行・管理できます。
ターミナルも、Python 環境の別途インストールも不要です。

> [!IMPORTANT]
> ErisPulse-App は**スタンドアロンでインストールするクライアントプログラム**であり、`epsdk install` でインストールするモジュールではありません。
> Python ランタイムと ErisPulse SDK が内蔵されており、インストールするだけで使用可能——**スマートフォン上でも直接実行できます**。

## 機能の概要

- **複数インスタンス管理**：複数のインスタンスを作成 / 起動 / 停止 / 削除、ポートとアクセストークンは自動割り当て、新規環境または既存環境のクローンが可能
- **概要ダッシュボード**：アダプター / モジュール / オンラインのロボット / イベント総数の統計、CPU / メモリ使用量のアラート色変更
- **モジュールストア**：検索とタグによる絞り込み、ワンクリックでのインストール / アップグレード / アンインストール、指定バージョンのインストール、pipのミラーソースとGitパッケージのサポート
- **イベントストリーム + イベントビルダー**：リアルタイムのイベント表示、可視化されたテストイベントの構築とアダプターへの送信
- **監視**：ログ / ライフサイクル / 審計の三合一ビュー
- **コマンド管理**：プレフィックスとエイリアスなどのグローバル設定、起動 / 停止とプラットフォームのホワイトリスト / ブラックリスト
- **ロボットの概要 / 設定 / ファイル管理**：ネイティブインターフェースでインスタンスを直接操作
- **バックグラウンド常駐**：Androidのフォアグラウンドサービスによる保活；Windowsではシステムトレイに最小化、ウィンドウを閉じてもインスタンスを中断しない
- **モジュール動的ウィンドウ**：モジュールが登録したページは自動的にサイドナビゲーションに表示（ダッシュボードと同じグループ）、クリックで直ちにアクセス

## サポート対象プラットフォーム

すべてのプラットフォームのインストーラーは [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) からダウンロードできます。必要に応じて選択してください：

| プラットフォーム | インストールパッケージ | 説明 |
|------|--------|------|
| Android | `online-*.apk` / `offline-*.apk` | **スマートフォンで直接実行**、PCは不要 |
| Windows | `windows-x64-setup.exe` / `windows-x64.zip` | インストール版 / インストール不要版 |
| Linux | `linux-x64.tar.gz` | 解凍後すぐに使用可能 |
| macOS | `macos-arm64.zip` | Apple Silicon（arm64） |

Flutter コードベースで全プラットフォームをカバーしています。

## インストール方法（Android / スマートフォンで直接実行）

GitHub Releases から APK をダウンロードしてインストールしてください。2 種類のビルドがあります。

| ビルド | 実行時イメージ | 適用場面 |
|------|-----------|---------|
| `erispulse-app-online-*.apk` | 初回起動時にダウンロード | インストールパッケージが小さく、ネットワーク環境が良い場合に適しています |
| `erispulse-app-offline-*.apk` | APK に事前にパッケージ化 | オフラインで自己完結、インストール後にインターネット接続が不要です |

どちらのビルドもインストール手順は同じです。

1. APK をダウンロードしてインストールし、起動時に通知権限を許可してください（バックグラウンドサービスの維持に使用します）
2. ホーム画面に初期化の横長バナーが表示されたら、実行をクリックして最初の初期化を実行してください（進行状況とログの表示が可能です）
3. インスタンスを作成して起動します
4. App 内の管理画面でアダプタとモデルの API キーを設定します

> オフラインパッケージは自己完結型です。インストール後はネットワーク接続が不要です。初回起動時のダウンロードが遅いまたは不安定な場合は、設定ページでダウンロードソースをミラー（ghfast / gh-proxy）に切り替えてください。

### インストール方法（デスクトップ版：Windows / Linux / macOS）

1. [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) から対応するプラットフォーム用のインストールパッケージをダウンロードしてください。
   （Windows は `setup.exe` または無印の `zip`、Linux は `tar.gz`、macOS は `zip`）
2. インストールして起動します
3. ウェルカムページでインストールする ErisPulse SDK のバージョンを選択してください（デフォルトは最新版です）
4. インスタンスを作成して起動します

---

## 動作原理

```
┌────────────────────────────────────────────────────┐
│  ErisPulse-App (Flutter)                            │
│                                                    │
│  ネイティブ UI ── Dashboard REST / WS API          │
│       │                                            │
│       ├── Android：フォアグラウンドサービス + proot + Ubuntu rootfs│
│       │        + Python + ErisPulse インスタンス     │
│       └── デスクトップ版：内蔵 Python + 直接プロセス管理 │
└────────────────────────────────────────────────────┘
```

- **Android**：インスタンスは、フォアグラウンドサービス（background isolate）によってホストされる proot（ユーザースペース chroot）内で実行されます。UI が閉じても、ロボットは継続的に動作し、クラッシュした場合は自動的に再起動します。
- **デスクトップ版**：インスタンスは、App の直接の子プロセスとして実行されます。Windows では、システムトレイに最小化して常駐（ウィンドウを閉じてもインスタンスは中断されません）。App の再起動後は、まだ実行中のインスタンスの管理を自動的に復元し、終了時にはすべてのインスタンスを一括して停止します。
- すべてのプラットフォームのネイティブ UI は、`127.0.0.1:<port>/Dashboard/*` の REST / WebSocket API を介してインスタンスと通信し、[ErisPulse-Dashboard](dashboard.md) と同じ API を共有します。

## SDKとの関係

- Appに埋め込まれたErisPulse SDK：Android用はUbuntuイメージにパッケージ化され、デスクトップ用はPyPIからインストールされます
  （歓迎ページでバージョンを選択可能、デフォルトは最新版）
- App内のインスタンスとコマンドライン`epsdk`で作成されたインスタンスは同等であり、同じモジュール/アダプタを使用できます
- モジュール開発者は[Dashboardウィンドウ登録API](dashboard.md)を使用してカスタムページを登録できます：
  ウィンドウは自動的にAppのサイドナビゲーションに表示され（Dashboardと同じグループに分類）、クリックすると対応するページがレンダリングされます

---

## 次のステップ

- **デスクトップ / サーバー上でブラウザを使って管理**：[ErisPulse-Dashboard](dashboard.md)（App と同一の API とウィンドウグループを共有）
- **最初のプラットフォームに接続**：App 内蔵の管理画面で設定が完了でき、各プラットフォームの詳細は[プラットフォーム特性一覧](../platform-guide/README.md)を参照
- **コマンドラインに慣れている方へ**：App 内のインスタンスは `epsdk` で作成したものと完全に同等です。[クイックスタート](../quick-start.md)から始めてください



### Dashboard 使用与视窗注册

# ErisPulse-Dashboard

> [!TIP]
> **このドキュメントを読むべきとき**：Web画面でボットを視覚的に管理したい場合（モジュールの有効化・無効化、設定編集、ログ閲覧、イベントストリームの監視など）、または自分のモジュール用のDashboard管理ページを登録したい場合にお読みください。必要ない場合はスキップして構いません。

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) はErisDevが直接メンテナンスする**Web管理パネルモジュール**で、ErisPulseに視覚的なランタイム管理インターフェースを提供します：モジュールの有効化・無効化、設定編集、ログ閲覧、イベントストリーム監視など。

> [!IMPORTANT]
> DashboardはErisPulseフレームワークの**内蔵機能ではありません**。別途インストールが必要です：
>
> ```bash
> epsdk install Dashboard
> ```

Dashboardは、他のErisPulseモジュールがカスタム管理ページをサイドバーに登録することもサポートしています。登録後、ユーザーはDashboard内で直接そのモジュール専用のビューページに切り替えることができ、独立したフロントエンドを別途開発する必要はありません。

> [!NOTE]
> ビュー登録は**オプション機能**です。
>
> - Dashboardモジュールが**未インストール**または**未ロード**の場合、`sdk.Dashboard.register_view()` を呼び出すと例外がスローされます
> - モジュール自体の他の機能に影響が及ばないよう、登録コードは必ず `try/except` で囲んでください
> - 登録前にDashboardが利用可能かどうかを確認することをお勧めします：`hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## 動作原理

```
モジュールの on_load()
  → sdk.Dashboard.register_view(...) を呼び出し
  → Dashboardバックエンドがビュー情報を保存
  → WebSocketでフロントエンドに通知
  → フロントエンドがサイドバーナビ項目 + ページコンテナを動的に作成
  → ユーザーがクリックしてモジュールのビューを表示
```

---

## 登録API

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # 必須、一意の識別子
    title="マイモジュール",             # 中国語名
    title_en="My Module",             # 英語名
    icon_svg='<svg>...</svg>',        # サイドバーアイコンSVG
    html_content='<div>...</div>',     # ページのHTMLコンテンツ
    js_content='function xxx() {}',    # ページのJavaScriptロジック
    css_content='.my-style {}',        # 任意のカスタムCSS
    iframe_url='',                     # iframeモードのURL（html_contentとどちらか一方を指定）
    loader="loadMyModuleView",         # このページに切り替えた際に呼び出されるJS関数名
    group="group_extensions",          # サイドバーグループ
    group_title="",                    # カスタムグループの中国語名
    group_title_en="",                 # カスタムグループの英語名
)
```

### パラメータ説明

| パラメータ | 型 | 必須 | 説明 |
|------|------|------|------|
| `id` | `str` | はい | ビューの一意識別子、モジュール名の使用を推奨 |
| `title` | `str` | いいえ | 中国語表示名、デフォルトは `id` を使用 |
| `title_en` | `str` | いいえ | 英語表示名、デフォルトは `title` を使用 |
| `icon_svg` | `str` | いいえ | サイドバーアイコンの完全なSVG文字列 |
| `html_content` | `str` | いいえ* | インジェクションモードのページHTMLコンテンツ |
| `js_content` | `str` | いいえ | ページのJavaScriptコード |
| `css_content` | `str` | いいえ | ページのカスタムCSSスタイル |
| `iframe_url` | `str` | いいえ* | iframeモードのURL、設定すると `html_content` は無視されます |
| `loader` | `str` | いいえ | ページアクティブ時に自動的に呼び出されるJS関数名 |
| `group` | `str` | いいえ | サイドバーグループ識別子、デフォルトは `group_extensions` |
| `group_title` | `str` | いいえ | カスタムグループの中国語タイトル |
| `group_title_en` | `str` | いいえ | カスタムグループの英語タイトル |

> *`html_content` と `iframe_url` のうち少なくとも一方を指定する必要があります。そうでない場合、ページは空白になります。

---

## 2つのインジェクションモード

### モード1：HTML/JSインジェクション（推奨）

HTML、JS、CSSの文字列を直接提供すると、Dashboardがその内容をページに注入します。このモードはDashboardのスタイルと完全に一致しており、Dashboardが提供するCSSクラス名の使用を推奨します。

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="ハローページ", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">これはサンプルページです</div></div>',
    group="group_tools",
)
```

> APIルートやJSインタラクションなどを含む完全な天気モジュールの例は、下記の[完全なモジュール例](#完全なモジュール例)を参照してください。

### モード2：iframe埋め込み

モジュールが独自のHTMLページURLを提供し（ルートの登録は自身で行う必要があります）、Dashboardがiframeとして埋め込みます。完全に独立したUIや複雑なインタラクションが必要なシナリオに適しています。

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="データ可視化", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> iframeモードでは、認証用の `token` パラメータがURLに自動的に追加されます。

---

## サイドバーグループ

モジュールはビューが属するサイドバーグループを指定できます。Dashboardには以下の組み込みグループがあります：

| グループ識別子 | 中国語名 | 位置 |
|---------|--------|------|
| `group_overview` | 概要 | 第1グループ |
| `group_events` | イベント | 第2グループ |
| `group_extensions` | 拡張 | 第3グループ（デフォルト） |
| `group_system` | システム | 第4グループ |
| `group_tools` | ツール | 第5グループ |

組み込みグループ名を指定すると、モジュールのビューはそのグループの末尾に追加されます：

```python
group="group_tools"  # "ツール"グループに追加
```

カスタムグループ名（`group_` で始まらない名前）を使用することもでき、Dashboardが自動的に新しいグループを作成します：

```python
group="my_group",
group_title="マイグループ",
group_title_en="My Group",
```

---

## よく使うCSSクラス名

モジュールのビューでHTMLインジェクションモードを使用する場合、視覚的一貫性を保つためにDashboardの既存のCSSクラス名を直接使用できます：

| クラス名 | 用途 |
|------|------|
| `page-title` | ページタイトル、例：`<h1 class="page-title">タイトル</h1>` |
| `card` | カードコンテナ |
| `card-header` | カードのタイトルバー |
| `card-body` | カードのコンテンツ領域 |
| `grid-2` | 2カラムグリッドレイアウト |
| `grid-3` | 3カラムグリッドレイアウト |
| `btn` | 基本ボタン |
| `btn-primary` | メインボタン（青） |
| `btn-secondary` | サブボタン |
| `btn-icon` | アイコンボタン |
| `btn-danger` | 危険な操作用ボタン |

DashboardはCSS変数でテーマカラーを制御しており、モジュールのビュー内で直接参照できます：

| CSS変数 | 用途 |
|----------|------|
| `var(--bg-p)` | メイン背景色 |
| `var(--bg-s)` | サブ背景色 |
| `var(--bg-t)` | 第3背景色（カードなど） |
| `var(--tx-p)` | メインテキスト色 |
| `var(--tx-s)` | サブテキスト色 |
| `var(--tx-t)` | 補助テキスト色 |
| `var(--bd)` | ボーダー色 |
| `var(--accent)` | アクセントカラー |
| `var(--ok-c)` | 成功色 |
| `var(--er-c)` | エラー色 |

これらの変数はDashboardのライト/ダークテーマに応じて自動的に切り替わるため、モジュール側で追加の処理は不要です。

---

## 認証とAPI呼び出し

モジュールのビューのJSからモジュール独自のAPIを呼び出す際は、認証のためにDashboardのトークンを付ける必要があります：

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

モジュールのAPIエンドポイントがトークンを検証するかどうかは自由に決定できます。検証が必要な場合は、リクエストヘッダーから抽出できます：

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## 完全なモジュール例

以下は完全な天気モジュールの例で、ビューの登録方法、APIデータの提供方法、アンロード時のリソースクリーンアップ方法を示しています：

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
        self.logger.info("天気モジュールがロードされました")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("天気モジュールがアンロードされました")

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
                    <h1 class="page-title">天気検索</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">現在の天気情報を表示</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">現在の天気</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">「更新」をクリックして読み込み</div>
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
                                           '<p>温度: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>湿度: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = '読み込み失敗: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"Dashboardビューの登録に失敗しました: {e}")
```

---

## ビューの登録解除

モジュールのアンロード時には `unregister_view()` を呼び出して、登録済みのビューをクリーンアップする必要があります：

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

登録解除後、DashboardのフロントエンドはWebSocketを通じてサイドバーナビ項目とページコンテンツをリアルタイムで削除するため、ユーザーがページを再読み込みする必要はありません。

---

## 注意事項

1. **ロード順序** — Dashboardのロード優先度は `99999`（高優先度）です。あなたのモジュールの優先度はこれより低い値（例：`50`）にし、Dashboardが先にロードを完了するようにしてください
2. **防御的プログラミング** — Dashboardモジュールが未インストールまたは未ロードの可能性があるため、ビュー登録時は `try/except` で囲んでください
3. **リソースクリーンアップ** — `on_unload` 内で `unregister_view()` を呼び出し、登録済みのビューを削除してください
4. **IDの一意性** — `id` パラメータはDashboard全体で一意である必要があります。モジュール名をそのまま使用することを推奨します
5. **SVGアイコン** — `icon_svg` は完全な `<svg>` タグである必要があります。サイズは `viewBox="0 0 24 24"` を使用し、`stroke="currentColor"` でDashboardのテーマカラーを継承することを推奨します
6. **JS関数の命名** — `js_content` 内の関数名は一意なもの（例：`loadWeatherView`）にし、他のモジュールとの衝突を避けてください
7. **動的更新** — モジュールがビューを登録/登録解除すると、DashboardのフロントエンドはWebSocketを通じてサイドバーをリアルタイムで更新します。ページの再読み込みは不要です

---

## 次のステップ

- **PCを開かずにスマホでボットを管理したい**：[ErisPulse-App](app.md)（公式マルチプラットフォームクライアント。Dashboardと同じAPIセットを共有しており、モジュールのビューも同様に利用可能）
- **ビューにバックエンドデータAPIを提供したい**：[ルートマネージャー](../advanced/router.md)でHTTPルートを登録します。メソッドの早見表は[コアモジュールAPI - Router](../api-reference/core-modules.md)を参照
- **ビュー内でリアルタイムログ / イベントストリームを表示したい**：[ログサブスクリプション（プッシュモード）](../api-reference/core-modules.md)と[ライフサイクル管理](../advanced/lifecycle.md)



### Cron 定时任务

# ErisPulse-Cron

> [!TIP]  
> **このドキュメントを読む必要があるタイミング**:  
> モジュールで定時/遅延実行のロジック（定時アラーム、周期的な監視、Cron 式によるスケジューリング）が必要で、フレームワークの再起動後にタスクが失われないことを望む場合にこのドキュメントを読む。不要であればスキップしてください。

[ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) は ErisPulse エコシステムの**定時タスクスケジューラーモジュール**であり、他のモジュールに統一された定時タスク API を提供します。このモジュールは、一度限りのタイマー、間隔繰り返し、Cron 式の 3 種類のタスクタイプをサポートし、コールバックにパラメータを渡すことができ、SQLite による永続化により、再起動してもタスクが失われません。

> [!IMPORTANT]  
> Cron は ErisPulse フレームワークの内蔵機能ではなく、個別にインストールする必要があります:  
>  
> ```bash
> epsdk install Cron
> ```

インストール後は `sdk.Cron` を通じてすべてのインターフェースにアクセスできます。  
---

## 機能速覧

- **3 種類のタイミング設定**：1 回限り (`once`)、間隔によるループ (`interval`)、Cron 式 (`cron`)
- **コールバック引数**：`callback_data` を作成時に渡すことで、トリガー時に元のデータを返却し、タスクの元を識別可能
- **永続化**：SQLite に保存 (`sdk.storage`) され、フレームワークの再起動後も自動的に復元
- **遅れ対応戦略**：即時実行 / 飛ばす / 再スケジューリング、タスクごとに選択可能
- **タスク管理**：一時停止、再開、キャンセル、手動実行、期限切れタスクのクリーンアップ
- **Dashboard 連携**：[ErisPulse-Dashboard](dashboard.md) をインストールしている場合、管理ウィンドウが自動的に登録される

## 速習

```python
from ErisPulse import sdk

# 1. コールバックハンドラの登録
@sdk.Cron.on_trigger
async def handle_trigger(info):
    data = info["callback_data"]
    print(f"タスクがトリガーされました: {info['task_id']}, データ: {data}")

# 2. タイマーの作成
task_id = sdk.Cron.once(
    delay=60,
    callback_data={"type": "reminder", "msg": "水分補給の時間です"},
)
```

---

## API 概要

### タスクの作成

```python
# 一回限り：600 秒遅延してトリガー
sdk.Cron.once(delay=600, callback_data={"order_id": "123"}, label="注文のタイムアウト通知")

# 間隔ループ：300 秒ごとにトリガー、最大 100 回
sdk.Cron.interval(interval_seconds=300, callback_data={"monitor": "server-1"}, max_runs=100)

# Cron 式：平日の毎日 9:30
sdk.Cron.cron(expression="30 9 * * 1-5", callback_data={"type": "daily_report"})

# 一般的なオプションパラメータ：trigger_at（絶対タイムスタンプ）、delay（最初の遅延）、timezone、
# max_runs（0=無限）、label、source（作成者モジュール名）、missed_policy（遅れ時のポリシー）
```

一般的な Cron 式：`*/5 * * * *`（5 分ごと）、`0 8 * * *`（毎日 8 時）、`30 9 * * 1-5`（平日の 9:30）、`0 0 1 * *`（毎月 1 日）。

### コールバック

```python
@sdk.Cron.on_trigger
async def my_handler(info):
    # info には task_id / task_type / callback_data / label / source /
    # run_count / max_runs / created_at / last_run / trigger_time が含まれる
    ...
```

複数のハンドラを登録可能で、すべて順次実行され、1 つのハンドラの例外は他のハンドラに影響しない。

### タスクの管理

```python
sdk.Cron.cancel(task_id)                  # キャンセル
sdk.Cron.pause(task_id)                   # 一時停止
sdk.Cron.resume(task_id)                  # 再開（reschedule=True で次回トリガーを再計算）
await sdk.Cron.trigger_now(task_id)       # 手動で即時トリガー（元のスケジュールには影響しない）
sdk.Cron.get_task(task_id)                # 1 つのタスクを取得
sdk.Cron.list_tasks(source="MyModule")    # タスク一覧（source/status/task_type によるフィルタリング可能）
sdk.Cron.delete_task(task_id)             # タスク記録を削除
sdk.Cron.cleanup()                        # 7 日前に完了/キャンセルされたタスクをクリーンアップ
```

### 遅れ時のポリシー（missed_policy）

フレームワークの再起動後に、トリガー時間に遅れたタスクに対して：

| ポリシー | 行為 |
|------|------|
| `fire_immediately` | 即時トリガー（デフォルト） |
| `skip` | 今回のトリガーをスキップし、次回を待つ |
| `reschedule` | 現在時刻から次回トリガーを再計算 |

## モジュールのアンロード時の動作

Cron のタスクデータは**永続化されたアセット**です。タスクを作成したモジュールがアンロードまたは無効化されても、既に作成されたタスクは削除されません。ただし、そのモジュールが登録したコールバックハンドルはクリーンアップされます。所有権システムに基づく[外部クリーンアップフック](../advanced/ownership.md#ツールモジュールガイド-他のモジュールのハンドルを管理する)により、Cron が他のモジュールのコールバックを管理する場合、自動的に所有者を記録します。その他のモジュールがアンロードまたは無効化された際に、そのコールバックハンドルは自動的に破棄され、他のモジュールのインスタンスが正常にリサイクルされることが保証されます。

- タスク作成元のモジュールが**再ロード**された後、`on_trigger` を再び実行することで、再びトリガーを受け取ることができます。
- 使用しなくなったタスクは `sdk.Cron.cancel(task_id)` / `delete_task(task_id)` を使用してクリーンアップできます。

## 次のステップ

- **タスクのトリガー後にユーザーにメッセージを送信**：コールバック内で [Send DSL](../developer-guide/adapters/send-dsl.md) または `event.reply()`（[イベントシステム API](../api-reference/event-system.md) を参照）を使用してリマインダーを送信します。
- **視覚的にスケジュールされたタスクを管理**：[ErisPulse-Dashboard](dashboard.md) をインストールすると、Cron が自動的に管理用のウィンドウを登録します。
- **モジュールのアンインストール時のコールバックのクリーンアップの詳細**：[所有権（owner）システム](../advanced/ownership.md)



### Takumi 图片渲染

# ErisPulse-Takumi

> [!TIP]
> **このドキュメントを読むタイミング**：HTML / ノードツリー / Jinjaテンプレートを画像にレンダリングしてチャットプラットフォームに送信したい場合（統計カード、ランキング、長文の画像）に読む。必要なければスキップしてください。

[ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) は ccd2s が維持する **サードパーティの画像レンダリングモジュール** です。[takumi-py](https://github.com/BalconyJH/takumi-py) に基づいており、Bot が HTML、ノードツリー、Jinja テンプレート、SVG、アニメーションを画像にレンダリングできるようにします。モジュールには **中英文字体**（Noto Sans SC / Roboto / Source Code Pro）が内蔵されており、追加の設定は不要です。

> [!IMPORTANT]
> Takumi **は** ErisPulse フレームワークの組み込み機能ではなく、個別にインストールする必要があります：
>
> ```bash
> epsdk install Takumi
> ```

適用シーン：

- データ/統計をカード画像にレンダリングする
- Markdown / 長文をレイアウトが安定した画像にレンダリングし、プラットフォームのスタイル差異を回避する
- SVG / アニメーションを生成し、動的な視覚効果を実現する
- 中英混排の画像（内蔵フォントで即座に使用可能）

---

## インストールと有効化

```bash
epsdk install Takumi
```

インストール後、モジュールは自動的にロードされ、設定で有効化を確認します：

```toml
[Takumi]
enabled = true
```

---

## 速習

モジュールが自動的にロードされた後、モジュールマネージャーから取得するか、`sdk` ショートカットを使用します：

```python
from ErisPulse import sdk

takumi = sdk.module.get("Takumi")
# 同義の書き方：takumi = sdk.Takumi
```

### HTML のレンダリング

```python
png = takumi.render_html(
    """
    <div class="card">
      <h1>你好，ErisPulse</h1>
      <p>由 Takumi 渲染</p>
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
    height=None,   # 内容に応じて自動的に高さを調整
    lang="zh-CN",
)
```

### ノードツリーのレンダリング

```python
png = takumi.render_node(
    {
        "type": "text",
        "text": "中文和 English 都可直接渲染",
        "style": {"fontSize": 48, "color": "#111827"},
    },
    width=800,
    height=None,
    lang="zh-CN",
)
```

`png` は `bytes` であり、`event.reply(png, method="Image")` を使用して送信できます（[レンダリング結果の送信](#レンダリング結果の送信)を参照）。

---

## レンダリング API

`sdk.Takumi` は、下層の `takumi_py.Renderer` のすべての機能をプロキシしています：すべてのレンダリング、測定、SVG、アニメーション、テンプレートメソッドは `sdk.Takumi` 上で直接呼び出すことができます。これらのメソッドに対して、モジュールは**自動的に内蔵フォントのフォールバックスタック**（`takumi.families`）を注入します。手動で `font_families` を渡す場合は、呼び出し側の設定を尊重します。

### メソッド概要

| カテゴリ | メソッド | 戻り値 | 説明 |
|------|------|------|------|
| 静的レンダリング | `render_html(html, ...)` | `bytes` | HTML文字列をレンダリングする |
| | `render_node(node, ...)` | `bytes` | ノードツリー（dict）をレンダリングする |
| | `render_template(name, ctx, ...)` | `bytes` | Jinjaテンプレートをレンダリングする |
| | `render_compiled(node, ...)` | `bytes` | 事前コンパイルされたノードをレンダリングする |
| SVG 出力 | `render_svg_html(html, ...)` | `str` | SVGを出力する（HTML入力） |
| | `render_svg_node(node, ...)` | `str` | SVGを出力する（ノードツリー入力） |
| | `render_svg_template(name, ctx, ...)` | `str` | SVGを出力する（テンプレート入力） |
| | `render_svg_compiled(node, ...)` | `str` | SVGを出力する（事前コンパイル入力） |
| アニメーション | `render_animation(scenes, ...)` | `bytes` | 複数フレームのアニメーションをエンコードする |
| | `render_sequence_at_time(scenes, time_ms, ...)` | `bytes` | シーケンスの特定の時間フレームを取得する |
| 測定 | `measure_node(node, ...)` | `dict` | ノードツリーのレイアウトを測定する |
| | `measure_html(html, ...)` | `dict` | HTMLのレイアウトを測定する |
| | `measure_compiled(node, ...)` | `dict` | 事前コンパイルされたノードを測定する |
| コンパイル | `compile_node(node)` | `CompiledNode` | ノードツリーをコンパイルする |
| | `compile_html(html, ...)` | `CompiledNode` | HTMLをコンパイルする |
| フォント | `register_font(font)` | `list[str]` | 自定義フォントを登録し、familyリストを返す |
| | `register_fonts(fonts)` | `list[str]` | フォントを一括登録する |

> `CompiledNode` は `resource_urls()` メソッドを公開しており、HTTP(S) イメージ参照を事前に発見できるため、リソースの事前準備が可能です。

### 一般的なパラメータ

以下のパラメータは、静的レンダリングと SVG メソッドに適用されます（アニメーションメソッドには `fps` などがあります。対応する例を参照してください）：

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `stylesheets` | `list[str]` | `None` | ドキュメントレベルの CSS 文字列リスト；内側の `style` は HTML と一緒に解析されます |
| `width` | `int \| None` | `1200` | ビューポートの幅（ピクセル）；`None` はレイアウトに応じて推測されます |
| `height` | `int \| None` | `630` | ブレンドの高さ（ピクセル）；`None` は内容に応じて自動的に高さを調整します（[ビューポートと出力形式](#ビューポートと出力形式)を参照） |
| `lang` | `str \| None` | `None` | BCP-47 言語タグ（例：`zh-CN`）、テキスト整形と改行に影響します |
| `font_families` | `list[str]` | 自動注入 | フォントフォールバックスタック；便利なメソッドは自動的に内蔵フォントを注入します |
| `format` | `str` | `"png"` | 出力形式（[ビューポートと出力形式](#ビューポートと出力形式)を参照） |
| `device_pixel_ratio` | `float` | `1.0` | デバイスピクセル比、出力解像度を制御します |
| `time_ms` | `int` | `0` | アニメーションのサンプリング時刻（ミリ秒） |
| `dithering` | `str` | `"none"` | ドッジングアルゴリズム：`none` / `ordered-bayer` / `floyd-steinberg` |
| `quality` | `int \| None` | `None` | 有損エンコードの品質 |
| `lossless` | `bool \| None` | `None` | 無損圧縮かどうか |
| `images` | `list` | `None` | 今回のレンダリングの画像リソース（`ImageResource` または `(src, bytes)` タプル） |
| `keyframes` | `Mapping` | `None` | 構造化されたキーフレーム、`@keyframes` を書く必要はありません |
| `options` | `RenderOptions` | — | `RenderOptions(...)` でパラメータを一括で渡す、上表のフィールドと同じ |

完全なフィールド定義は `takumi_py.RenderOptions` を参照してください。

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

> `filters={...}` を使用してカスタム Jinja フィルターを注入するか、`environment=...` を使用して完全な `jinja2.Environment` を渡すことができます。テンプレートディレクトリと環境設定は [takumi-py テンプレートドキュメント](https://github.com/BalconyJH/takumi-py/blob/main/docs/guides/templates.md) を参照してください。

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

> 各フレームは `AnimationScene(node, duration_ms=...)` で構成され、`duration_ms` は正数でなければなりません。

---

## ビューポートと出力形式

### 出力形式

| シナリオ | `format` の値 |
|------|---------------|
| 静的画像 | `png`（デフォルト）/ `jpeg` / `jpg` / `webp` / `ico` / `raw` |
| アニメーション | `webp`（デフォルト）/ `apng` / `gif` |

`format="raw"` は行主序の RGBA バイナリを返し、カスタムピクセル処理に使用します。

### `width` と `height` について

`width` と `height` の役割は非対称です：

- `width` は**ビューポートの幅**で、テキストとレイアウトはそれに応じて改行、リフローようにします。**固定値**（例：`800`）でなければなりません。そうでなければ、画布は内容の自然な幅に伸縮し、テキストは改行せず、サイズは制御できません。
- `height` は**画布の高さ**で、内容に応じて増加します。`height` のデフォルト値は `630` です。`height=None` を渡すと、Takumi は**内容に応じて自動的に画布の高さを調整**します（auto viewport）。

> [!TIP]
> **推奨の組み合わせ：固定 `width` + `height=None`。** 固定サイズの画布や切り抜き効果が必要な場合にのみ、具体的な `height` を渡してください。

> [!NOTE]
> `width` / `height` のいずれかは技術的に `None` を渡して、レイアウトに応じて推測させることもできます（ノード自身がサイズを宣言している場合）。両方を渡した場合、出力サイズは確定値になります。

---

## フォント

### 内蔵フォント

| フォント | family | カテゴリ |
|------|--------|------|
| Noto Sans SC | `Noto Sans SC` | sans-serif |
| Roboto | `Roboto` | sans-serif |
| Roboto Italic | `Roboto` | sans-serif（italic） |
| Source Code Pro | `Source Code Pro` | monospace |
| Source Code Pro Italic | `Source Code Pro` | monospace（italic） |

モジュール属性：

| 属性 | 説明 |
|------|------|
| `takumi.fonts` | 内蔵フォントファイル名リスト |
| `takumi.families` | 登録されたフォント familyリスト |

### 自動注入

`sdk.Takumi` 上のすべてのレンダリング、測定、SVG、アニメーション、テンプレートメソッドは、自動的に `takumi.families` をフォントフォールバックスタックとして注入します。`takumi.renderer`（原生インスタンス）または `create_renderer()` で作成された独立したインスタンスを直接呼び出す場合は、`font_families=takumi.families` を手動で渡す必要があります。

### 自定義フォント

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

`register_font` は登録された family 名のリストを返し、後続のレンダリング時に `font_families` として渡すことができます。

---

## レンダラーインスタンス

### 原生 Renderer

`takumi.renderer` は元の `takumi_py.Renderer` インスタンスです。直接呼び出す場合は、`font_families` を手動で渡す必要があります：

```python
png = takumi.renderer.render_html(
    "<div>你好</div>",
    font_families=takumi.families,
    lang="zh-CN",
)
```

### 独立 Renderer

フォント / 画像 / リソースキャッシュを分離する必要がある場合（長寿命プロセス、マルチテナント環境）、独立した `Renderer` を作成できます。内蔵のフォントは自動的に登録されます：

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

`create_renderer()` は `takumi_py.Renderer` の構造子パラメータを受け取ります：

| パラメータ | 型 | デフォルト値 | 説明 |
|------|------|--------|------|
| `load_default_fonts` | `bool` | `False` | takumi-py に含まれるフォントをロードするかどうか（内蔵フォントは常にロードされます） |
| `fonts` | `list[FontResource]` | `None` | 追加で登録する自定義フォント |
| `cache_max_bytes` | `int \| None` | `None` | リソースキャッシュの上限（バイト）；`0` は無効化 |
| `persistent_images` | `list` | `None` | 永続化する画像リソース |

> 独立したインスタンスはモジュールのプロキシを経由しないため、統一された内蔵フォントフォールバックスタックを保持するには、`font_families=takumi.families` を明示的に渡す必要があります。`font_families` を明示的に渡した場合、モジュールは呼び出し側の設定を尊重し、デフォルトのフォールバックスタックを注入しません。`RenderOptions(font_families=...)` でも同様です。

---

## レンダリング結果の送信

レンダリングされた画像は `bytes` であり、イベントの返信として直接送信できます：

```python
from ErisPulse import sdk

takumi = sdk.Takumi
png = takumi.render_html("<div>hello</div>", lang="zh-CN")

# 方法1：Imageメソッドで返信する
await event.reply(png, method="Image")

# 方法2：OneBot12メッセージセグメントで返信する
from ErisPulse.Core.Event import MessageBuilder
await event.reply_ob12(
    MessageBuilder().image(png).build()
)
```

> 画像の異なるプラットフォームでのラッピングは、アダプタによって統一的に処理されます。詳しくは [MessageBuilder 詳解](../advanced/message-builder.md) と [送信メソッド仕様](../standards/send-method-spec.md) を参照してください。

---

## 設定

```toml
[Takumi]
enabled = true
```

---

## 次に進む

- **レンダリング結果を送信する方法**：`event.reply(png, method="Image")` などの返信方法は [イベントシステム API - 返信メソッド](../api-reference/event-system.md) を参照
- **より複雑な出力メッセージの構築**（画像 + 文字 + @）：[メッセージビルダー](../advanced/message-builder.md)
- **レンダリング + 定期送信**：[ErisPulse-Cron](cron.md) と組み合わせて周期的なデータカードを作成



======
平台特性指南
======


### 平台特性总览

# ErisPulse PlatformFeatures ドキュメント

> 基準プロトコル：[OneBot12](https://12.onebot.dev/) 
> 
> 本ドキュメントは**プラットフォーム固有機能ガイド**であり、以下の内容を含みます：
> - 各アダプターが対応するSendメソッドの連鎖呼び出し（チェーン呼び出し）例
> - プラットフォーム固有のイベント/メッセージ形式の説明
> 
> 一般的な使用方法については以下を参照してください：
> - [基本概念](../getting-started/basic-concepts.md)
> - [イベント変換標準](../standards/event-conversion.md)  
> - [APIレスポンス仕様](../standards/api-response.md)

---

## プラットフォーム固有の機能

このセクションは、各アダプターの開発者が保守し、OneBot12 標準との差異と拡張機能を説明するためのものです。以下の各プラットフォームの詳細ドキュメントを参照してください：

- [保守説明](maintain-notes.md)

- [雲湖プラットフォームの特徴](yunhu.md)
- [雲湖ユーザープラットフォームの特徴](yunhu_user.md)
- [Oopzプラットフォームの特徴](oopz.md)
- [Telegramプラットフォームの特徴](telegram.md)
- [OneBot11プラットフォームの特徴](onebot11.md)
- [OneBot12プラットフォームの特徴](onebot12.md)
- [SnowLumaプラットフォームの特徴](snowluma.md)
- [メールプラットフォームの特徴](email.md)
- [Kook(開黒啦)プラットフォームの特徴](kook.md)
- [Matrixプラットフォームの特徴](matrix.md)
- [企業微信プラットフォームの特徴](wecom.md)
- [Bilibiliプラットフォームの特徴](bilibili.md)
- [Minecraftプラットフォームの特徴](minecraft.md)
- [QQ公式ロボットプラットフォームの特徴](qqbot.md)
- [花楓コーヒーハウス](ideaura.md)
- [Discord](discord.md)
- [Webhookプロトコルブリッジ](webhook.md)
- [WeChat公式アカウント](wechatmp.md)

> さらに `sandbox` アダプターもありますが、このアダプターにはプラットフォーム特有のドキュメントを保守する必要はありません。

---

## 共通インターフェース

### Send 連鎖呼び出し
すべてのアダプターが以下の標準的な呼び出し方法に対応しています：

> **注意：** ドキュメント内の `{AdapterName}` は実際のアダプター名（例： `yunhu`、`telegram`、`onebot11`、`email` など）に置き換えてください。

1. タイプとIDを指定： `To(type,id).Func()`
   ```python
   # アダプターインスタンスの取得
   my_adapter = adapter.get("{AdapterName}")
   
   # メッセージの送信
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # 例：
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. IDのみ指定： `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # 例：
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. 送信アカウントを指定： `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # 例：
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. 直接呼び出し： `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # 例：
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### 非同期送信と結果処理

Send DSLのメソッドは `asyncio.Task` オブジェクトを返します。つまり、結果をすぐに待つかどうかを選択できます：

```python
# アダプターインスタンスの取得
my_adapter = adapter.get("{AdapterName}")

# 結果を待たずに、メッセージをバックグラウンドで送信
task = my_adapter.Send.To("user", "123").Text("Hello")

# 送信結果を取得する必要がある場合は、後から待機できます
result = await task
```

#### 送信ルールデコレーター

実際の開発では、送信成功後に後続のロジックを実行する、失敗時に自動リトライ、タイムアウト取消、送信進捗の監視などが必要になることがよくあります。Send DSLには送信ルールデコレーターが組み込まれており、連鎖メソッドを通じてルールを追加できます：

| メソッド | 説明 |
|--------|------|
| `.Hook(callback)` | 送信成功後に実行されるコールバック（複数回呼び出し可能） |
| `.Retry(times=1)` | 失敗時に自動でN回リトライ（初回を含め計N+1回） |
| `.Timeout(seconds)` | 単回送信のタイムアウト、超過で取消（Retryと併用可） |
| `.Defer(seconds)` | 送信を遅延（プロセス内タイマー、永続化なし） |
| `.OnProgress(callback)` | 各段階の進捗コールバック、SendContextを渡す |
| `.OnError(callback)` | 最終失敗時のエラーコールバック（一度のみ発火） |

```python
yunhu = adapter.get("yunhu")

# 送信成功後にポイントを減算
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("消費が完了しました"))

# 失敗時リトライ + タイムアウト取消 + 進捗監視
def on_progress(ctx):
    print(f"段階: {ctx.stage}, 試行: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # 最大3回リトライ
        .Timeout(10)           # 毎回10秒でタイムアウト
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("重要なお知らせ"))
```

ルールメソッドは `self` を返すため、送信メソッド（Text/Imageなど）の前に呼び出す必要があります。`SendContext` には `stage`（pending/sending/retrying/success/failed/timeout）、`attempt`、`elapsed`、`error`、`result` などのフィールドが含まれ、監視に便利です。

#### 一括構築モード（Build）

1つのチェーン内で複数の送信メソッドを構築し、最後に一括実行します。「一度に複数のメッセージを送る」シナリオに適しています：

```python
yunhu = adapter.get("yunhu")

# 複数のメッセージを構築し、一括送信
results = await (yunhu.Send.To("user", "123")
                .Build()                     # ビルドモードに入る
                .Text("通知1")
                .Image("pic.jpg")
                .Text("通知2")
                .send_all())                 # 一括実行
# results = [Text結果, Image結果, Text結果]
```

`.send_all()` はデフォルトで**並列**実行されます（同時送信で効率が高い）。メッセージの到着順序を保証する必要がある場合は、`.Sequential()` を呼び出して逐次実行します：

```python
# 逐次実行（順序保証）+ 失敗時リトライ
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # 順番に送信
       .Retry(2)                     # 失敗した項目はそれぞれリトライ
       .Text("1つ目のメッセージ").Text("2つ目のメッセージ")
       .send_all())
```

一括実行は**失敗継続**ポリシーを採用しています：ある項目が失敗しても他の項目は中断されず、失敗した項目は自動的にリトライされます。一括実行でもバッチ全体の `Hook`（全成功後に発火）、`OnError`（失敗があると発火）、`OnProgress`（進捗コールバック）に対応しています。

> より詳細なルールと一括構築の説明については、[SendDSL 詳解](../developer-guide/adapters/send-dsl.md) を参照してください。

### イベントリスニング
イベントのリスニング方法は3種類あります：

1. プラットフォームネイティブイベントのリスニング：
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"{AdapterName}のネイティブイベントを受信: {data}")
   ```

2. OneBot12標準イベントのリスニング：
   ```python
   from ErisPulse.Core import adapter, logger

   # OneBot12標準イベントをリッスン
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"標準イベントを受信: {data}")

   # 特定プラットフォームの標準イベントをリッスン
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"{AdapterName}の標準イベントを受信: {data}")
   ```

3. Eventモジュールによるリスニング：
    `Event`のイベントは `adapter.on()` 関数をベースとしているため、`Event`が提供するイベント形式はOneBot12標準イベントです

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="挨拶メッセージを送信", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"メッセージを受信: {event}")
    async def notice_handler(event):
        logger.info(f"通知を受信: {event}")
    async def request_handler(event):
        logger.info(f"リクエストを受信: {event}")
    async def command_handler(event):
        logger.info(f"コマンドを受信: {event}")
    ```

中でも最も推奨されるのは `Event` モジュールを使用したイベント処理です。`Event` モジュールは豊富なイベントタイプと豊富なイベント処理メソッドを提供しているためです。

---

## 標準形式
参考用として、ここでは簡単なイベント形式を示します。詳細情報が必要な場合は、上記のリンクを参照してください。

> **注意：** 以下の形式は基本的なOneBot12標準形式であり、各アダプターはこのベースに拡張フィールドを追加している場合があります。詳細は各アダプターの固有機能説明を参照してください。

### 標準イベント形式
すべてのアダプターが実装しなければならないイベント変換形式：
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

### 標準レスポンス形式
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

## コントリビューション

より多くの開発者にアダプタードキュメントの執筆と保守への参加をご案内しています！以下の手順に従ってコントリビューションを提出してください：
1. [ErisPuls](https://github.com/ErisPulse/ErisPulse) リポジトリをForkします。
2. `docs/platform-features/` ディレクトリにMarkdownファイルを作成し、`<プラットフォーム名>.md` の形式で命名します。
3. この `README.md` ファイルに、ご自身が貢献したアダプターへのリンクおよび関連公式ドキュメントを追加します。
4. Pull Request を提出します。

ご支援ありがとうございます！



### OneBot11 适配

# OneBot11プラットフォームの機能ドキュメント

OneBot11Adapterは、OneBot V11プロトコルに基づいて構築されたアダプターです。

---

## ドキュメント情報

- 対応するモジュールのバージョン: 4.6.2
- メンテナー: ErisPulse
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォームの概要: OneBotはチャットボットアプリケーションのインターフェース標準です
- アダプター名: OneBotAdapter
- 対応するプロトコル/APIバージョン: OneBot V11
- 多アカウントのサポート: デフォルトでマルチアカウントアーキテクチャ、複数のOneBotアカウントを同時に設定および実行できます
- 設定のキー名: `OneBotAdapter`

## v5范式更新（4.3.0から）

このアダプターはv5范式への対応を完了しました（段階的なアップグレード、APIの互換性を保持）：

- **BaseConverterの継承**: コンバーターの共通フィールド（id/time/platform/self/raw）は、フレームワークのbuild_base_eventによって構築され、OB11のフィールド名（echo/time/self_id）に上書きされます
- **spawn_backgroundタスクの所有**: Clientモードの接続タスクはRuntime.spawn_backgroundを使用するよう変更されました（所有者に属し、シャットダウン時に自動的に回収されます）
- **フレームワークのソフト依存**: アダプターのインストール時にErisPulseのハード依存を宣言しなくなり、pipの解析時にフレームワークのバージョンを調整する必要がありません。実行時にErisPulse>=2.7.1を検出し、バージョンが低すぎる場合はログに警告を出します
- **起動時のバージョンログ**: 初期化時にOneBotAdapter vX.Y.Zがロードされたことを出力します

既存の機能（4.2.0から対応）：マルチアカウント、Api DSL標準アクションマッピング（get_self_info→get_login_infoなど）、Request DSL（友達/グループリクエスト承認：event.approve() / event.reject()）、EventMixin、i18n。

4.3.1からリクエストイベントの処理は規格に従って実装され、以下の[標準化対応](#標準化対応)の章を参照してください。

---

## 標準Apiアクション（Api DSL）

アダプターはOneBot12標準アクション名を自動的にOB11アクション名にマッピングし、モジュールはプラットフォームを跨いで統一して呼び出すことができます：

| OB12標準アクション | OB11アクション | 説明 |
|--------------|-----------|------|
| get_self_info | get_login_info | フィールドの標準化 user_id/user_name/user_displayname |
| get_user_info | get_stranger_info | フィールドの標準化 |
| delete_message | delete_msg | メッセージの撤回 |
| leave_group | set_group_leave | グループから退出 |
| get_friend_list | get_friend_list | アクション名が一致し、デフォルトで透過 |
| get_group_info | get_group_info | アクション名が一致し、デフォルトで透過 |
| upload_file | upload_group_file / upload_private_file | 拡張 group_id/user_idのオプションパラメータ、filetypeは自動的に検出してルーティング |

### 基本的な使い方

```python
from ErisPulse import sdk
onebot = sdk.adapter.get("onebot11")

# ロボット情報を取得
result = await onebot.Api.get_self_info()
print(result["data"]["user_id"], result["data"]["user_name"])

# メッセージを撤回
await onebot.Api.delete_message(message_id=123456)

# グループファイルをアップロード（filetypeは自動的に検出してupload_group_fileにルーティング）
result = await onebot.Api.upload_file(group_id=123456, file="/path/to/file.zip")

# 指定したアカウントを使用（マルチアカウント）
result = await onebot.Api.Using("main").get_self_info()

# マッピングされていないOB11アクションはcall()を使って実行（NapCat/Lagrangeなどの拡張に共通）
result = await onebot.Api.call("send_poke", group_id=123, user_id=456)
```

### OB11プロトコルの拡張（NapCat/go-cqhttp/SnowLuma に共通）

頻繁に使用される拡張アクションは型付きメソッドとして封印され（`OB11ExtensionApi` mixin）、IDEの補完がサポートされています：

```python
await onebot.Api.send_poke(user_id=789, group_id=123456)
await onebot.Api.set_msg_emoji_like(message_id=123, emoji_id="76")
await onebot.Api.mark_msg_as_read(group_id=123456)
result = await onebot.Api.get_group_msg_history(group_id=123456, count=20)
await onebot.Api.set_essence_msg(message_id=123)
result = await onebot.Api.ocr_image(image="https://example.com/img.png")
```

> 拡張アクションは直接OB11アクション名を使用し、プラットフォームのプレフィックスは付けません。少数の未封印のアクションは`Api.call("action_name", ...)`を使って呼び出します。

### Sendのクエリメソッド（廃止済み）

以下のSendメソッドはまだ使用可能ですが、廃止済みとしてマークされています。Api DSLの使用を推奨します：

| Sendメソッド（廃止） | Api DSLの代替 |
|------------------|-------------|
| `Send.GetLoginInfo()` | `Api.get_self_info()` |
| `Send.GetFriendList()` | `Api.get_friend_list()` |
| `Send.GetGroupInfo()` | `Api.get_group_info(group_id)` |
| `Send.GetGroupList()` | `Api.get_group_list()` |
| `Send.GetGroupMemberInfo(uid)` | `Api.get_group_member_info(gid, uid)` |
| `Send.GetGroupMemberList()` | `Api.get_group_member_list(gid)` |
| `Send.GetMsg(mid)` | `Api.call("get_msg", message_id=mid)` |
| `Send.GetForwardMsg(id)` | `Api.call("get_forward_msg", id=id)` |

## 標準化対応

このセクションは、アダプターがErisPulseの標準化規格に準拠している動作を説明します。規格の詳細はSDKドキュメントの《リクエスト操作規格》（`docs/ja/standards/request-action-spec.md`）と《APIレスポンス規格》（`docs/ja/standards/api-response.md`）を参照してください。

### リクエストイベントの処理（4.3.1から）

アダプターはリクエスト操作規格に従ってリクエストイベントの受信と応答を実装します：

- **コンテキストの保持**: イベントのエントリポイントは`request_id`を`{request_type, sub_type, group_id, account, ts}`にマッピングし、キャッシュします（TTL 3600秒、上限512件、リクエスト処理が成功した後にクリアされます）、後続の`accept()`/`reject()`ルーティングに使用されます
- **エンドポイントの優先度**: `accept()`/`reject()`のkwargsによる明示的なパラメータ（`request_type`/`sub_type`/`group_id`は予約名）> イベントの保持されたコンテキスト > フレンドエンドポイント（`set_friend_add_request`）に回帰し、WARNINGを出力します
- **グループ招待/グループ参加リクエスト**: `request_type == "group"`の場合は、`set_group_add_request`に正しくルーティングされます（グループ参加`sub_type="add"`、招待`sub_type="invite"`）
- **廃止の説明**: 4.3.1以前は、リクエストタイプを指定するために非公開パラメータ`_request_type`を使用していましたが、廃止され、渡されても無視されます

### call_apiのエラーハンドリング

- アカウントが接続されていない、または接続が閉じられている場合、`call_api`は`ConnectionError`をスローせず、標準の失敗レスポンス（`status="failed"`、`retcode=33001`）を返します
- API呼び出しがタイムアウトした場合も、標準の失敗レスポンス（`retcode=33001`）を返します

### アカウントフィールドの両方の互換性

- `call_api`は標準フィールド`account_id`と旧フィールド名`_account_id`（標準名が優先）の両方を受け入れます；フレームワークApiDSLは自動的に適応し、モジュールコードでは`account_id`を使用することを推奨します
- Send DSLの全メソッドは`send_context`を読み取ります：イベントチェーン内では自動的に現在のイベントのソースアカウントを使用し、明示的に`Using()`で指定されたアカウントが優先されます

### エラーコード規格

| retcode | 含意 | 発生場面 |
|---------|------|----------|
| 0 | 成功 | アクションが正常に実行された |
| 33001 | ネットワークエラー | アカウントが接続されていない、接続が閉じられている、API呼び出しがタイムアウトした |
| 10002 | 対応していないアクション | 実装されていないアクションを呼び出した |
| 10003 | パラメータエラー | 必要なパラメータが不足している |

> プラットフォームの元のレスポンスデータは`onebot11_raw`フィールドに保持されます。

---

## 対応するメッセージ送信タイプ

すべての送信メソッドはチェーン式の構文で実現されます。例えば：
```python
from ErisPulse.Core import adapter
onebot = adapter.get("onebot11")

# デフォルトアカウントを使用して送信
await onebot.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを使用して送信
await onebot.Send.Using("main").To("group", group_id).Text("メインアカウントからのメッセージ")

# チェーン式修飾：@ユーザー + レプリー
await onebot.Send.To("group", group_id).At(123456).Reply(msg_id).Text("返信メッセージ")

# @全員
await onebot.Send.To("group", group_id).AtAll().Text("お知らせメッセージ")
```

### 基礎的な送信メソッド

- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像を送信します（URL、Base64、またはbytesをサポート）。
- `.Voice(file: Union[str, bytes], filename: str = "voice.amr")`：音声メッセージを送信します。
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信します。
- `.Face(id: Union[str, int])`：QQ絵文字を送信します。
- `.File(file: Union[str, bytes], filename: str = "file.dat")`：ファイルを送信します（自動的にタイプを判断します）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します（自動的にOB11に変換します）。
- `.Recall(message_id: Union[str, int])`：メッセージを撤回します。

### グループ操作メソッド

以下のメソッドは`To("group", group_id)`で指定されたグループを対象とし、グループコンテキストを使用して操作を実行します：

- `.Kick(user_id, reject_add_request=False)`：グループメンバーを蹴ります。
- `.Ban(user_id, duration=1800)`：グループメンバーを禁止します（秒単位）、0は解禁を意味します。
- `.WholeBan(enable=True)`：全員禁止をオン/オフします。
- `.SetAdmin(user_id, enable=True)`：グループ管理者を設定/解除します。
- `.SetCard(user_id, card="")`：グループ名前を設定します。
- `.SetGroupName(name)`：グループ名を変更します。
- `.Leave(is_dismiss=False)`：グループを退きます（グループ主は解散できます）。
- `.SetTitle(user_id, title="")`：グループタイトルを設定します。
- `.SetPortrait(file)`：グループアイコンを設定します。

### クエリメソッド

- `.GetMsg(message_id)`：メッセージの内容を取得します。
- `.GetForwardMsg(id)`：転送メッセージを取得します。
- `.GetLoginInfo()`：現在のログイン情報（アカウント）を取得します。
- `.GetFriendList()`：友達リストを取得します。
- `.GetGroupInfo()`：グループ情報（`To("group", group_id)`が必要）を取得します。
- `.GetGroupList()`：グループリストを取得します。
- `.GetGroupMemberInfo(user_id)`：グループメンバー情報（`To("group", group_id)`が必要）を取得します。
- `.GetGroupMemberList()`：グループメンバーリスト（`To("group", group_id)`が必要）を取得します。

### 友達操作メソッド

- `.Like(user_id, times=1)`：友達にいいねを送ります（最大10回）。

### チェーン式修飾メソッド（組み合わせて使用可能）

チェーン式修飾メソッドは`self`を返し、チェーン式で呼び出すことができます。最終的な送信メソッドの前に呼び出す必要があります：

- `.At(user_id: Union[str, int], name: str = None)`：指定したユーザーを@します（複数回呼び出すことができます）。
- `.AtAll()`：全員を@します。
- `.Reply(message_id: Union[str, int])`：指定したメッセージに返信します。

### チェーン式呼び出しの例

```python
# 基礎的な送信
await onebot.Send.To("group", 123456).Text("Hello")

# @1人のユーザー
await onebot.Send.To("group", 123456).At(789012).Text("こんにちは")

# @複数のユーザー
await onebot.Send.To("group", 123456).At(111).At(222).At(333).Text("皆さんこんにちは")

# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await onebot.Send.To("group", 123456).Raw_ob12(ob12_msg)

# いいねを送る
await onebot.Send.Like(123456, times=10)

# グループメンバーを禁止
await onebot.Send.To("group", 123456).Ban(789012, duration=3600)

# 解禁
await onebot.Send.To("group", 123456).Ban(789012, duration=0)

# メンバーを蹴る
await onebot.Send.To("group", 123456).Kick(789012)

# グループ管理者を設定
await onebot.Send.To("group", 123456).SetAdmin(789012)

# グループ名を変更
await onebot.Send.To("group", 123456).SetGroupName("新しいグループ名")

# グループ情報を取得
result = await onebot.Send.To("group", 123456).GetGroupInfo()

# 指定されたアカウントで操作
await onebot.Send.Using("main").To("group", 123456).Ban(789012)
```

### 対応していないタイプの処理

未定義の送信メソッドを呼び出した場合、アダプターはテキストの提示を返します：
```python
# 存在しないメソッドを呼び出す
await onebot.Send.To("group", 123456).SomeUnsupportedMethod(arg1, arg2)
# 実際の送信: "[対応していない送信タイプ] メソッド名: SomeUnsupportedMethod, パラメータ: [...]"
```

## リクエスト操作（Request DSL）

アダプターはリクエスト操作DSLを提供し、友達リクエストとグループリクエスト（グループ参加/招待）の承認/拒否操作に使用できます。

### Eventの高速メソッド

リクエストイベントは`event.approve()`と`event.reject()`の高速メソッドをサポートし、内部でRequest DSLを自動的に呼び出します：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

@request.on_group_request()
async def handle_group_request(event):
    group_id = event.get("group_id")
    await event.approve()
```

### 手動でRequest DSLを呼び出す

```python
# リクエストを承認
await onebot.Request("flag_string").accept()

# リクエストを拒否
await onebot.Request("flag_string").reject()

# 指定されたアカウントで操作
await onebot.Request("flag_string").Using("main").accept()
```

### 完全な例

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    comment = event.get("comment", "")

    # 方法1: Eventの高速メソッドを使用
    if comment == "passphrase":
        await event.approve()
    else:
        await event.reject()

    # 方法2: Request DSLを使用
    flag = event.get("flag")
    if comment == "passphrase":
        await onebot.Request(flag).accept()
    else:
        await onebot.Request(flag).reject()
```

### リクエスト操作の戻り値

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "",
    "message": ""
}
```

## イベントタイプのマッピング

### 標準OB12マッピング

| OB11の元のタイプ | 変換後のdetail_type | 説明 |
|--------------|-------------------|------|
| message_type: private | `private` | プライベートメッセージ |
| message_type: group | `group` | グループメッセージ |
| request_type: friend | `friend` | 友達リクエスト |
| request_type: group | `group` | グループリクエスト |
| meta_event_type: heartbeat | `heartbeat` | ハートビート |
| notice_type: group_upload | `group_file_upload` | グループファイルアップロード |
| notice_type: group_admin | `group_admin_change` | グループ管理者の変更 |
| notice_type: group_increase | `group_member_increase` | グループメンバーの増加 |
| notice_type: group_decrease | `group_member_decrease` | グループメンバーの減少 |
| notice_type: group_ban | `group_ban` | グループ禁止 |
| notice_type: friend_add | `friend_increase` | 友達の追加 |
| notice_type: friend_delete | `friend_decrease` | 友達の削除 |
| notice_type: group_recall / friend_recall | `message_recall` | メッセージの撤回 |

### プラットフォーム固有のイベント（onebot11_プレフィックス）

| OB11の元のタイプ | 変換後のdetail_type | 説明 |
|--------------|-------------------|------|
| meta_event_type: lifecycle | `onebot11_lifecycle` | OneBot実装のライフサイクル |
| notify + sub_type: honor | `onebot11_honor` | グループの名誉変更 |
| notify + sub_type: poke | `onebot11_poke` | ぽちり |
| notify + sub_type: lucky_king | `onebot11_lucky_king` | グループのラッキー王 |
| CQコードの未知のタイプ | メッセージセグメント `onebot11_{type}` | 未認識のCQコード |

### イベントの例

```json
// 友達リクエスト
{
  "type": "request",
  "detail_type": "friend",
  "user_id": "789012",
  "comment": "友達を追加してください",
  "request_id": "flag_abc123",
  "flag": "flag_abc123"
}

// ハートビート
{
  "type": "meta_event",
  "detail_type": "heartbeat",
  "interval": 5000,
  "status": {...}
}

// ライフサイクル（プラットフォーム固有）
{
  "type": "meta_event",
  "detail_type": "onebot11_lifecycle",
  "sub_type": "enable"
}

// ぽちり（プラットフォーム固有）
{
  "type": "notice",
  "detail_type": "onebot11_poke",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// グループのラッキー王（プラットフォーム固有）
{
  "type": "notice",
  "detail_type": "onebot11_lucky_king",
  "group_id": "123456",
  "user_id": "789012",
  "target_id": "345678"
}

// 名誉変更（プラットフォーム固有）
{
  "type": "notice",
  "detail_type": "onebot11_honor",
  "group_id": "123456",
  "user_id": "789012",
  "honor_type": "talkative"
}

// CQコード拡張メッセージセグメント
{
  "type": "message",
  "message": [
    {"type": "onebot11_shake", "data": {}}
  ]
}
```

### 拡張フィールドの説明

- すべての固有フィールドは`onebot11_`プレフィックスで識別されます
- 元のイベントデータは`onebot11_raw`フィールドに保持されます
- 元のイベントタイプは`onebot11_raw_type`フィールドに保持されます
- メッセージ内容のCQコードは対応するメッセージセグメントに変換されます（標準タイプはプレフィックスなし、未知タイプは`onebot11_`プレフィックスを付ける）
- レプリーメッセージには`reply`タイプのメッセージセグメントが追加されます
- @メッセージには`mention`タイプのメッセージセグメントが追加されます

## イベント拡張メソッド

OneBot11アダプターはイベントオブジェクトに以下のプラットフォーム固有のメソッドを登録し、イベントハンドラで直接呼び出すことができます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    raw_event = event.get_raw_event()
    raw_self_id = event.get_raw_self_id()
    sender_info = event.get_sender_info()
    sender_role = event.get_sender_role()
```

### メソッドリスト

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_raw_event()` | `dict` | OneBot11の完全な元のイベントデータを取得します |
| `get_raw_self_id()` | `str` | 元のself_id（BotのQQ番号）を取得します |
| `get_sender_info()` | `dict` | 完全な送信者情報を取得します（nickname、role、levelなどの含まれる） |
| `get_sender_role()` | `str` | 送信者がグループ内の役割を取得します（owner/admin/member） |
| `get_sender_level()` | `int` | 送信者のレベルを取得します |
| `get_sender_title()` | `str` | 送信者のグループタイトルを取得します |
| `is_system_message()` | `bool` | 送信者がシステムメッセージかどうかを判断します（sub_type == "system"） |

### 使用例

```python
from ErisPulse.Core.Event import message, command

@message.on_group_message()
async def handle_group(event):
    role = event.get_sender_role()
    if role == "admin" or role == "owner":
        await event.reply("管理者さん、こんにちは！")

    title = event.get_sender_title()
    if title:
        await event.reply(f"あなたのタイトルは: {title}")

@command("whoami")
async def whoami(event):
    info = event.get_sender_info()
    nickname = info.get("nickname", "不明")
    level = event.get_sender_level()
    await event.reply(f"ニックネーム: {nickname}, レベル: {level}")
```

## 設定オプション

OneBot11アダプターはマルチアカウントアーキテクチャを採用しており、各アカウントは独立に設定されます。設定のキー名は`OneBotAdapter`です。

### アカウント設定フィールド

| フィールド | 型 | 必須 | デフォルト値 | 説明 |
|------|------|------|--------|------|
| `bot_id` | `str` | はい | `""` | ロボットのQQ番号、アカウントを識別するために使用されます |
| `mode` | `str` | いいえ | `"server"` | 実行モード：`"server"`（パッシブリッスン）または `"client"`（アクティブ接続） |
| `url` | `str` | いいえ | `"ws://127.0.0.1:3001"` | ClientモードのWebSocketアドレス |
| `token` | `str` | いいえ | `""` | 認証トークン（Clientモードの接続トークン / Serverモードの検証トークン） |
| `server_path` | `str` | いいえ | `"/"` | ServerモードのWebSocketパス |
| `enabled` | `bool` | いいえ | `true` | そのアカウントを有効にするかどうか |
| `name` | `str` | いいえ | `""` | アカウントの備考名 |

### 内部デフォルト値

- 再接続間隔：30秒
- API呼び出しのタイムアウト：30秒

### 設定例

```toml
[OneBotAdapter.accounts.main]
bot_id = "123456789"
mode = "server"
server_path = "/onebot-main"
token = "main_token"
enabled = true

[OneBotAdapter.accounts.backup]
bot_id = "987654321"
mode = "client"
url = "ws://127.0.0.1:3002"
token = "backup_token"
enabled = true

[OneBotAdapter.accounts.test]
bot_id = "111222333"
mode = "client"
url = "ws://127.0.0.1:3003"
enabled = false
```

### デフォルト設定

アカウントが設定されていない場合、アダプターは自動的に以下のように作成されます：
```toml
[OneBotAdapter.accounts.default]
bot_id = ""
mode = "server"
server_path = "/"
enabled = true
```

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、awaitで送信結果を取得できます。返り値はErisPulseアダプターの標準化された返り値規格に従います：

```python
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "123456",
    "message": "",
    "onebot11_raw": {...}
}
```

### 多アカウント送信の構文

```python
# アカウント選択メソッド
await onebot.Send.Using("main").To("group", 123456).Text("メインアカウントのメッセージ")
await onebot.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# bot_idでアカウントを選択
await onebot.Send.Using("123456789").To("group", 123456).Text("QQ番号で選択")

# API呼び出し方式
await onebot.call_api("send_msg", account_id="main", group_id=123456, message="Hello")
```

### アカウント解析の優先順位

`call_api`と`Using()`で`account_id`パラメータの解析の優先順位は以下の通りです：
1. アカウント名と正確に一致する
2. `bot_id`フィールドと一致する
3. アカウントの任意の`str`型フィールドと一致する
4. 最初に有効なアカウントに回帰する

## 非同期処理メカニズム

OneBot11アダプターは非同期非ブロッキング設計を採用しており、以下のことを保証します：
1. メッセージ送信はイベント処理ループをブロックしません
2. 複数の並行送信操作を同時に実行できます
3. APIの応答を適切に処理できます
4. WebSocket接続をアクティブな状態に保ちます
5. 各アカウントが独立して実行されるマルチアカウントの並行処理

## エラーハンドリング

アダプターは包括的なエラーハンドリングメカニズムを提供しています：
1. ネットワーク接続の異常は自動的に再接続されます（各アカウントごとに独立した再接続が可能、間隔は30秒）
2. API呼び出しのタイムアウト処理（固定30秒のタイムアウト、タイムアウト時は`retcode=33001`の標準失敗レスポンスを返します）
3. アカウントが接続されていない、または接続が閉じている場合、`call_api`は`retcode=33001`の標準失敗レスポンスを返し、`ConnectionError`はスローされません
4. 接続失敗時は間隔に従って自動的に再試行します

## イベント処理の強化

マルチアカウントモードでは、すべてのイベントに自動的にアカウント情報が追加されます：
```python
{
    "type": "message",
    "detail_type": "private",
    "self": {"user_id": "123456789", "platform": "onebot11"},
    "platform": "onebot11",
    // ... その他のイベントフィールド
}
```

アダプターは自動的に`self_id → account_name`のマッピングを維持し、`event.reply()`は手動でアカウントを指定しなくても、正しく送信元アカウントにルーティングされます。

## 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = onebot.accounts

# アカウントの接続状態をチェック
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot.connections.items()
}

# アカウントの有効/無効を動的に変更（アダプターの再起動が必要）
onebot.accounts["test"].enabled = False
```

## self_idの自動マッピング

アダプターはOneBotの`self_id`（QQ番号）から`account_name`へのマッピングを自動的に確立し、イベントの返信ルーティングに使用します：

```python
# アダプター内部で自動的に完了
# イベントを受け取ったとき、self.user_idフィールドはbot_idに設定されます
# アダプターは自動的に記録します: self_id("123456789") → account_name("main")

# そのためevent.reply()は正しくアカウントにルーティングされます
@message.on_message()
async def handler(event):
    await event.reply("正しくルーティングされたアカウントに自動送信")
```



### OneBot12 适配

# OneBot12プラットフォームの機能ドキュメント

OneBot12Adapterは、OneBot V12プロトコルに基づいて構築されたアダプタであり、ErisPulseフレームワークのベースラインプロトコルアダプタです。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.6.2
- 維持者: ErisPulse
- プロトコルバージョン: OneBot V12
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: OneBot V12は、ErisPulseフレームワークのベースラインプロトコルである汎用的なチャットボットアプリケーションインターフェース標準です。
- アダプタ名: OneBot12Adapter
- 対応プロトコル/APIバージョン: OneBot V12
- 多アカウント対応: 完全な多アカウントアーキテクチャ、複数のOneBot12アカウントを同時に設定・実行可能

## v5 ファンタジーの更新（4.3.0）

本アダプタはv5ファンタジーに準拠しています（段階的アップグレード、API互換性保持）：

- **BaseConverterの継承**: コンバーターの共通フィールド（id/time/platform/self/raw）は、フレームワークの build_base_event によって構築され、OB11のフィールド名（echo/time/self_id）で上書きされます。
- **spawn_backgroundタスクの所有者**: Clientモードの接続タスクはRuntime.spawn_backgroundに変更され、所有者（owner）が所属し、シャットダウン時に自動的にリソースを回収します。
- **フレームワークのソフト依存**: アダプタのインストール時にErisPulseのハード依存を宣言せず、pipの解析時にフレームワークのバージョンを調整するのを避けています。実行時にErisPulse>=2.7.1を検出し、バージョンが低すぎる場合はログを出力します。
- **起動時のバージョンログ**: 初期化時にOneBot12Adapter vX.Y.Zがロードされたことを出力します。

既存の機能（4.2.0からサポート）：多アカウント、Api DSL標準アクションマッピング（get_self_info→get_login_infoなど）、Request DSL（友人/グループリクエスト承認：event.approve() / event.reject()）、EventMixin、i18n。

## 標準化の対応

本節では、ErisPulseの標準化規格に準拠したアダプタの動作について説明します。規格の詳細は、SDKドキュメントの《リクエスト操作規格》（`docs/ja/standards/request-action-spec.md`）と《APIレスポンス規格》（`docs/ja/standards/api-response.md`）を参照してください。

### リクエストイベントとRequest DSL

- **request_idの保証**: リクエストイベントの透過時に、最上位の `request_id` フィールドを保証します（原生の `request_id` が優先され、OB11スタイルの実装では `flag` フィールドにマッピングされます；両方がない場合は合成されません）。Request DSLが使用するためです。
- **デフォルトアカウントの回帰**: `Request` DSL（`handle_quick_request`アクションに基づく）が明示的に `Using()` を指定してアカウントを指定しない場合、リクエストイベントの元アカウント（`request_context`）に回帰し、イベントチェーン内で `event.approve()`/`event.reject()`が正しくルーティングされるようにします。

### call_apiのエラー処理

- アカウントが接続されていない、または接続が閉じられている場合、`call_api`は `ConnectionError`をスローせず、標準の失敗レスポンス（`status="failed"`、`retcode=33001`）を返します。
- API呼び出しがタイムアウトした場合も、標準の失敗レスポンス（`retcode=33001`）を返します。

### アカウントフィールドの両対応とsend_context

- `call_api`は、標準フィールド `account_id` と旧フィールド名 `_account_id`（標準名が優先）の両方を受け付けます；フレームワークApiDSLは自動的に適応し、モジュールコードでは `account_id` を推奨します。
- `Send`/`Recall`/`Edit`/`Batch`の全メソッドは `send_context`を読み取ります：イベントチェーン内では自動的に現在のイベントの元アカウントを使用し、明示的に `Using()`で指定したアカウントが優先されます。

### イベントフィールドの注入

- すべてのイベントに `self.account_id`（元アカウント名）が注入され、多アカウントモードではイベントが正しく元アカウントにルーティングされます。
- すべてのイベントに `onebot12_raw_type`フィールドが必須で含まれます（元のイベントタイプ、イベント変換規格に準拠）。
- 表情/ステッカーのメッセージセグメント名は `onebot12_sticker`です（`.Sticker()`メソッド内部でこのセグメントを送信します）。

### エラーコード規格

| retcode | 含意 | 発生場面 |
|---------|------|----------|
| 0 | 成功 | アクションが正常に実行された |
| 33001 | ネットワークエラー | アカウントが接続されていない、接続が閉じられている、API呼び出しのタイムアウト |
| 10002 | 対応しないアクション | バックエンドが対応していないアクションリクエスト |
| 10003 | パラメータエラー | 必要なパラメータが不足している |

> バックエンドが返した元のレスポンスデータは `onebot12_raw`フィールドに保持されます。

---

## 標準APIアクション（Api DSL）

OneBot12バックエンドは、すべてのOB12標準アクション名を原生でサポートし、Api DSLはデフォルトでcall_apiを透過的に委譲します（マッピングは不要）：

```python
from ErisPulse import sdk
ob12 = sdk.adapter.get("onebot12")

result = await ob12.Api.get_self_info()
result = await ob12.Api.get_friend_list()
await ob12.Api.delete_message(message_id="MSG_ID")

# アカウントの指定（多アカウント）
result = await ob12.Api.Using("main").get_self_info()

# プラットフォーム拡張アクション
result = await ob12.Api.call("extend_action", param=1)
```

> 対応するアクションは、バックエンドの実装（NapCat/Lagrange/LLOneBotなど）に準拠します；対応していないアクションは、エラーを返してバックエンドに透過的に返されます。

---

## リクエスト操作（Request DSL）

OneBot12標準のhandle_quick_requestアクションに基づき、友人リクエストとグループ参加招待の承認/拒否を処理します。

### Eventの便利メソッド

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    if event.get("platform") != "onebot12":
        return
    comment = event.get("comment", "")
    if comment == "passphrase":
        await event.approve()      # 承認
    else:
        await event.reject()       # 拒否
```

### 手動でのRequest DSLの呼び出し

```python
await ob12.Request("request_flag").accept()
await ob12.Request("request_flag").reject()
await ob12.Request("request_flag").Using("main").accept()
```

---

## 対応するメッセージ送信タイプ

すべての送信メソッドは、チェーン式の構文で実現されます。例えば：

```python
from ErisPulse.Core import adapter
onebot12 = adapter.get("onebot12")

# デフォルトアカウントを使用して送信
await onebot12.Send.To("group", group_id).Text("Hello World!")

# 特定のアカウントを指定して送信
await onebot12.Send.To("group", group_id).Account("main").Text("メインアカウントからのメッセージ")
```

### 大小文字を区別しない呼び出し

すべての送信メソッドとチェーン式修飾メソッドは、大小文字を区別しない呼び出しをサポートし、アダプタは正しい標準メソッド名に自動的にマッピングします：

```python
# 以下のすべての呼び出しは等価です
await onebot12.Send.To("user", 123).Text("hello")
await onebot12.Send.To("user", 123).text("hello")
await onebot12.Send.To("user", 123).TEXT("hello")

# チェーン式修飾メソッドも同様にサポートされます
await onebot12.Send.To("group", 123).At(456).Text("hello")
await onebot12.Send.To("group", 123).at(456).TEXT("hello")
await onebot12.Send.To("group", 123).AT(456).text("hello")
```

### 対応していないメソッドの呼び出し

存在しないメソッドを呼び出した場合、アダプタは例外をスローするのではなく、フレンドリーなテキストの応答を返します：

```python
# 対応していないメソッドを呼び出す
result = await onebot12.Send.To("user", 123).UnsupportedMethod("test")

# 返される結果は送信されたテキストメッセージです
# メッセージ内容: [対応していない送信タイプ] メソッド名: UnsupportedMethod, パラメータ: [args[0]: 'test']
```

### 基本メッセージタイプ

- `.Text(text: str)`：テキストメッセージを送信
- `.Image(file: Union[str, bytes], filename: str = "image.png")`：画像メッセージを送信（URL、Base64、またはbytesをサポート）
- `.Audio(file: Union[str, bytes], filename: str = "audio.ogg")`：音声メッセージを送信
- `.Voice(file: Union[str, bytes], filename: str = "voice.ogg")`：音声メッセージを送信（Audioの別名、OneBot11と互換性がある）
- `.Video(file: Union[str, bytes], filename: str = "video.mp4")`：動画メッセージを送信

### チェーン式修飾メソッド（selfを返してチェーン呼び出しをサポート）

- `.At(user_id: Union[str, int])`：ユーザーを@する（複数回呼び出し可能）
- `.AtAll()`：全員を@する
- `.Reply(message_id: Union[str, int])`：メッセージに返信する

### 原始メッセージの送信

- `.Raw_ob12(message: Union[Dict, List[Dict]], **kwargs)`：OneBot12の原始形式のメッセージを送信（命名規則に準拠）

### その他のメッセージタイプ

- `.Sticker(file_id: str)`：スタンプ/ステッカーを送信（`onebot12_sticker`メッセージセグメント）
- `.Location(latitude: float, longitude: float, title: str = "", content: str = "")`：位置情報を送信

### 管理機能

- `.Recall(message_id: Union[str, int])`：メッセージを撤回する
- `.Edit(message_id: Union[str, int], content: Union[str, List[Dict]])`：メッセージを編集する
- `.Raw(message_segments: List[Dict])`：OneBot12の原生メッセージセグメントを送信
- `.Batch(target_ids: List[str], message: Union[str, List[Dict]], target_type: str = "user")`：複数の宛先にメッセージを送信

## OneBot12標準イベント

OneBot12アダプタはOneBot12標準に完全に準拠しており、イベント形式は変換を必要とせず、フレームワークに直接送信されます。

### 新機能：元のイベントタイプフィールド

`standards/event-conversion.md`規格に準拠し、すべてのイベントは元のイベントタイプフィールド `onebot12_raw_type`を保持します：

```python
{
    "id": "event-id",
    "type": "message",              # イベントタイプ
    "onebot12_raw_type": "message", # 元のイベントタイプ（typeと同じ）
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}
```

### メッセージイベント (Message Events)

```python
# プライベートチャットメッセージ
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
    "detail_type": "private",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "message": [{"type": "text", "data": {"text": "Hello"}}],
    "alt_message": "Hello",
    "time": 1234567890
}

# グループチャットメッセージ
{
    "id": "event-id",
    "type": "message",
    "onebot12_raw_type": "message",
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
# グループメンバーの追加
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
    "detail_type": "group_member_increase",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "operator_id": "operator-id",
    "sub_type": "approve",
    "time": 1234567890
}

# グループメンバーの削除
{
    "id": "event-id",
    "type": "notice",
    "onebot12_raw_type": "notice",
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
# 友人リクエスト
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "friend",
    "self": {"user_id": "bot-id"},
    "user_id": "user-id",
    "comment": "申請メッセージ",
    "request_id": "request-flag",
    "flag": "request-flag",
    "time": 1234567890
}

# グループ招待リクエスト
{
    "id": "event-id",
    "type": "request",
    "onebot12_raw_type": "request",
    "detail_type": "group",
    "self": {"user_id": "bot-id"},
    "group_id": "group-id",
    "user_id": "user-id",
    "comment": "申請メッセージ",
    "request_id": "request-flag",
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
    "onebot12_raw_type": "meta_event",
    "detail_type": "lifecycle",
    "self": {"user_id": "bot-id"},
    "sub_type": "enable",
    "time": 1234567890
}

# ハートビートイベント
{
    "id": "event-id",
    "type": "meta_event",
    "onebot12_raw_type": "meta_event",
    "detail_type": "heartbeat",
    "self": {"user_id": "bot-id"},
    "interval": 5000,
    "status": {"online": true},
    "time": 1234567890
}
```

## 設定オプション

### アカウント設定

各アカウントは以下のオプションを個別に設定できます：

- `mode`: そのアカウントの実行モード ("server" または "client")
- `server_path`: ServerモードでのWebSocketパス
- `server_token`: Serverモードでの認証トークン（オプション）
- `client_url`: Clientモードで接続するWebSocketのURL
- `client_token`: Clientモードでの認証トークン（オプション）
- `enabled`: そのアカウントを有効にするかどうか
- `platform`: プラットフォーム識別子、デフォルトは "onebot12"
- `implementation`: 実装識別子、例えば "go-cqhttp"（オプション）

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

アカウントが設定されていない場合、アダプタは自動的に作成されます：

```toml
[OneBotv12_Adapter.accounts.default]
mode = "server"
server_path = "/onebot12"
enabled = true
platform = "onebot12"
```

## 送信メソッドの戻り値

### メッセージ送信メソッド

`.Text()`, `.Image()`, `.Raw_ob12()`などのすべてのメッセージ送信メソッドは、`asyncio.Task`オブジェクトを返し、`await`で送信結果を取得できます：

```python
task = await onebot12.Send.To("group", 123456).Text("Hello")
```

### チェーン式修飾メソッド

すべてのチェーン式修飾メソッド（`.At()`, `.AtAll()`, `.Reply()`）は`self`を返し、チェーン呼び出しが可能です：

```python
# 複数の修飾メソッドを組み合わせて使用
await onebot12.Send.To("group", 123456).Reply("msg123").At(789).At(790).Text("テキスト")
```

## APIレスポンスの標準

アダプタはErisPulseの標準化された返却規格を遵守します（`standards/api-response.md`）：

```python
# 成功レスポンス
{
    "status": "ok",              // 必須：実行ステータス
    "retcode": 0,                // 必須：返却コード（0は成功）
    "data": {                     // 必須：レスポンスデータ
        "message_id": "123456",
        "time": 1632847927.599013
    },
    "message_id": "123456",       // 必須：メッセージID（無ければ空文字列）
    "message": "",                // 必須：エラーメッセージ（成功時は空）
    "echo": "1234",               // オプション：リクエスト中のechoをそのまま返す
    "onebot12_raw": {...}        // オプション：元のレスポンスデータ
}

# 失敗レスポンス
{
    "status": "failed",           // 必須：実行ステータス
    "retcode": 10003,            // 必須：返却コード（0以外は失敗）
    "data": None,                // 必須：失敗時はnull
    "message_id": "",            // 必須：失敗時は空文字列
    "message": "必要なパラメータが不足しています",    // 必須：エラーメッセージ
    "echo": "1234",              // オプション：リクエスト中のechoをそのまま返す
    "onebot12_raw": {...}        // オプション：元のレスポンスデータ
}
```

### エラーコード規格

OneBot12標準のエラーコードに準拠します：

- **0**: 成功
- **1xxxx**: アクションリクエストエラー
- **2xxxx**: アクションハンドラーエラー
- **3xxxx**: アクション実行エラー（33001はネットワークタイムアウト）

### 多アカウント送信の構文

```python
# アカウント選択方法
await onebot12.Send.Using("main").To("group", 123456).Text("メインアカウントのメッセージ")
await onebot12.Send.Using("backup").To("group", 123456).Image("http://example.com/image.jpg")

# API呼び出し方法
await onebot12.call_api("send_message", account_id="main", 
    detail_type="group", group_id=123456, 
    content=[{"type": "text", "data": {"text": "Hello"}}])
```

## 非同期処理メカニズム

OneBot12アダプタは非同期非ブロッキング設計を採用しています：

1. メッセージ送信はイベント処理ループをブロックしません。
2. 複数の並行送信操作を同時に実行できます。
3. APIレスポンスは適切に処理されます。
4. WebSocket接続はアクティブな状態を維持します。
5. 複数のアカウントを並行して処理し、各アカウントは独立して動作します。

## エラー処理

アダプタは包括的なエラー処理メカニズムを提供します：

1. ネットワーク接続エラーは自動的に再接続されます（各アカウントごとに独立した再接続をサポートし、30秒の間隔で再接続されます）。
2. API呼び出しがタイムアウトした場合の処理（固定30秒のタイムアウト、タイムアウト時は `retcode=33001`の標準失敗レスポンスを返します）。
3. アカウントが接続されていない、または接続が閉じている場合、`call_api`は `retcode=33001`の標準失敗レスポンスを返し、`ConnectionError`をスローしません。
4. 対応していないメソッドの呼び出しは、フレンドリーなテキストの応答を返します。

## イベント処理の強化

多アカウントモードでは、すべてのイベントにアカウント情報が自動的に追加されます：

```python
{
    "type": "message",
    "onebot12_raw_type": "message",  // 元のイベントタイプ
    "detail_type": "private",
    "self": {"user_id": "123456"},  // 送信イベントのアカウントID（標準フィールド）
    "platform": "onebot12",
    // ... その他のイベントフィールド
}
```

## 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = onebot12.accounts

# アカウントの接続状態をチェック
connection_status = {
    account_id: connection is not None and not connection.closed
    for account_id, connection in onebot12.connections.items()
}

# アカウントの有効/無効切り替え（アダプタの再起動が必要）
onebot12.accounts["test"].enabled = False
```

## OneBot12標準の機能

### メッセージセグメントの標準

OneBot12は標準化されたメッセージセグメント形式を使用します：

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

### APIの標準

OneBot12標準API規格に準拠します：

- `send_message`: メッセージを送信
- `delete_message`: メッセージを撤回
- `edit_message`: メッセージを編集
- `get_message`: メッセージを取得
- `get_self_info`: 自身の情報を取得
- `get_user_info`: ユーザー情報を取得
- `get_group_info`: グループ情報を取得

## 最適な実践

1. **設定管理**: 複数の用途を持つロボットを分けて管理するために、多アカウント設定の使用を推奨します。
2. **エラー処理**: 常にAPI呼び出しの返り値のステータスをチェックしてください。
3. **メッセージ送信**: 適切なメッセージタイプを使用し、対応していないメッセージを送信しないようにしてください。
4. **接続監視**: 定期的に接続状態をチェックし、サービスの可用性を確保してください。
5. **パフォーマンス最適化**: バッチ送信の場合はBatchメソッドを使用し、ネットワークのオーバーヘッドを減らしてください。
6. **メソッド呼び出し**: 推奨される大文字キャメルケース（例: `.Text()`）を使用することを推奨しますが、小文字形式もサポートしており、異なるプログラミングスタイルに適応できます（この方法は旧バージョンとの互換性がありません）。



### Telegram 适配

# Telegramプラットフォーム特性ドキュメント

TelegramAdapter は Telegram Bot API をベースに構築されたアダプターで、複数のメッセージタイプとイベント処理をサポートしています。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.3.3
- メンテナー: ErisPulse
- 最終更新: 2026-11-10

## 基本情報

- プラットフォーム概要：Telegram はクロスプラットフォームのインスタントメッセージングソフトウェアです
- アダプター名：TelegramAdapter
- サポートするプロトコル/APIバージョン：Telegram Bot API
- 会話タイプのマッピング：`private` → 送信時は `user`、`group`/`supergroup` → `group`、`channel` → `channel`

## 標準化対応（4.3.3）

本章では、4.3.3 バージョンで完了した標準化対応の内容を説明します：イベントの変更、マルチアカウントの規約、エラーコード規範と Send 規範。

### イベントの変更

1. **グループ参加申請イベントの標準化**：
   - `detail_type` が `telegram_chat_join_request` から標準の `"group"` に変更され、`sub_type="join"` となります
   - `@request.on_group_request()` がこのイベントを直接キャッチできるようになりました
   - `request_id` の合成ルールは変更なし：`tjr_{chat_id}_{user_id}_{date}`
   - イベントは `event.approve()` / `event.reject()` で承認可能です（`approveChatJoinRequest` / `declineChatJoinRequest` に対応）
2. **イベントへの `self.account_id` 注入**：すべてのイベントはそれを生成したアカウント名を保持し、マルチアカウント環境下では `event.reply()` が自動的にそのアカウントで送信を処理します
3. **unknown イベント**：`self.user_id` には bot_id が設定されます（メッセージイベントの動作と一致）

リクエストイベントインターフェースの規約は SDK 標準に従います：[リクエストと承認アクション規範](../standards/request-action-spec.md)。

### アカウントとマルチアカウント

`call_api` は双方向互換のアカウントフィールドをサポートします：標準フィールド `account_id`（ApiDSL.Using ではこの名前を使用）/ 旧エイリアス `_account_id`；フレームワークの ApiDSL は新旧アダプターを自動的に適応させます。

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

await telegram.Api.Using("main").get_self_info()        # 標準的な方法でアカウントを指定
await telegram.Api.get_self_info(account_id="main")     # 標準フィールド account_id を明示的に渡す
```

### エラーコード規範

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（接続失敗、タイムアウトなど） |
| 34100 | プラットフォーム拒否（元のレスポンスは `telegram_raw` フィールドに保持） |
| 10002 | サポートされていないアクション（`get_friend_list` / `get_group_list` など、Telegram Bot API に対応するインターフェースが存在しない） |

### Send 規範

- HTML メソッド名は `HTML` で、`Html` は予約済みエイリアスです
- `Location` のシグネチャに `title` / `content` のオプションパラメータを補完
- `AnswerCallback` / `Raw_json` は send_context アカウントを使用：イベント処理チェーン内で送信 DSL を呼び出す際、自動的に現在のイベントが属するアカウントで送信します

## 標準Apiアクション（Api DSL）

アダプターは OB12 標準アクションを Telegram Bot API にマッピングし、data フィールドを標準化します：

| OB12 標準アクション | Telegram API | data フィールド |
|--------------|--------------|----------|
| get_self_info | getMe | user_id / user_name / user_displayname |
| get_user_info(user_id) | getChat | user_id / user_name / user_displayname |
| get_group_info(group_id) | getChat | group_id / group_name |
| get_group_member_info(group_id, user_id) | getChatMember | user_id / user_name / telegram_role |
| delete_message(message_id) | deleteMessage | メッセージ登録テーブルに基づいて chat_id を自動補完 |
| leave_group(group_id) | leaveChat | - |

拡張アクション：get_group_admin_list(group_id)（管理者リスト）、get_chat_member_count(chat_id)（メンバー数）。

```python
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")

result = await telegram.Api.get_self_info()
result = await telegram.Api.get_group_info(group_id=-100123)
result = await telegram.Api.get_group_admin_list(-100123)
await telegram.Api.delete_message(message_id=55)   # chat_id を自動補完
result = await telegram.Api.Using("main").get_self_info()
```

> Telegram Bot API にはフレンドリスト/グループリストを取得するインターフェースが存在せず、get_friend_list/get_group_list は明示的に
> retcode=10002（サポートされていないアクション）を返します。

---

## リクエスト操作（Request DSL）

グループ参加申請の処理は、approveChatJoinRequest / declineChatJoinRequest に基づきます。4.3.3 以降、`chat_join_request` は標準の `group` リクエストイベント（`sub_type="join"`）にマッピングされ、`@request.on_group_request()` が直接キャッチできるようになりました：

```python
from ErisPulse.Core.Event import request

@request.on_group_request()
async def handle_join_request(event):
    if event.get("platform") != "telegram":
        return
    # event["request_id"] は合成識別子（tjr_{chat_id}_{user_id}_{date}、ルールは変更なし）
    if event.get("sub_type") == "join":
        await event.approve()          # 承認（approveChatJoinRequest）
    # await event.reject()             # 拒否（declineChatJoinRequest）

# 手動呼び出し（対応するリクエストイベントを先に受信してコンテキストを登録しておく必要あり）
await telegram.Request(event["request_id"]).accept()
await telegram.Request(event["request_id"]).reject()
await telegram.Request(event["request_id"]).Using("main").accept()
```

---

## サポートされるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：

```python
from ErisPulse.Core import adapter
telegram = adapter.get("telegram")

await telegram.Send.To("user", user_id).Text("Hello World!")
```

### 基本送信メソッド

| メソッド | 説明 | パラメータ |
|------|------|------|
| `.Text(text)` | プレーンテキストメッセージを送信 | `text: str` |
| `.Face(emoji)` | 絵文字ダイスを送信 | `emoji: str`（例：🎲 🎯 🏀） |
| `.Markdown(text, content_type)` | Markdown 形式のメッセージを送信 | `content_type` のデフォルトは `"MarkdownV2"` |
| `.HTML(text)` | HTML 形式のメッセージを送信（`Html` は予約済みエイリアス） | `text: str` |
| `.MergeForward(nodes, title)` | 結合転送メッセージを送信（タイトル + 各 blockquote 引用ブロック、4096 で切り詰め） | `nodes: List[Dict]`, `title: str` |
| `.Sticker(file)` | ステッカーを送信 | `file: str (file_id/URL) \| bytes` |
| `.Location(lat, lng, title="", content="")` | 位置情報を送信（タイトルと内容はオプション） | `latitude: float, longitude: float, title: str, content: str` |
| `.Venue(lat, lng, title, addr)` | 場所（会場）情報を送信 | タイトルと住所を含む |
| `.Contact(phone, first, last)` | 連絡先を送信 | 電話番号と氏名を含む |

### メディア送信メソッド

すべてのメディアメソッドは `bytes`（アップロード）と `str`（file_id / URL）の2種類の入力をサポートします：

| メソッド | 説明 |
|------|------|
| `.Image(file, caption, content_type)` | 画像を送信 |
| `.Video(file, caption, content_type)` | 動画を送信 |
| `.Voice(file, caption)` | ボイスメッセージを送信 |
| `.Audio(file, caption, content_type)` | 音声を送信 |
| `.File(file, caption)` | ファイルを送信 |
| `.Document(file, caption, content_type)` | File のエイリアス |

### メッセージ管理メソッド

| メソッド | 説明 |
|------|------|
| `.Edit(message_id, text, content_type)` | 既存のメッセージを編集 |
| `.Recall(message_id)` | 指定したメッセージを削除 |
| `.Forward(from_chat_id, message_id)` | メッセージを転送（転送元を保持） |
| `.CopyMessage(from_chat_id, message_id)` | メッセージをコピー（転送元なし） |
| `.AnswerCallback(callback_query_id, text, show_alert)` | コールバッククエリに応答（send_context アカウントを使用） |

### 生メッセージ送信

- `.Raw_ob12(message: List[Dict])`：OneBot12 標準形式のメッセージを送信
- `.Raw_json(json_str: str)`：生の JSON 形式メッセージを送信（send_context アカウントを使用）

### チェーン修飾メソッド

| メソッド | 説明 |
|------|------|
| `.At(user_id)` | 指定ユーザーを@（Telegram entities で実装、複数回呼び出し可能） |
| `.AtAll()` | 全メンバーに@（`@All` テキストを送信） |
| `.Reply(message_id)` | 指定メッセージに返信 |
| `.Keyboard(inline_keyboard)` | インラインキーボードを設定（`list[list[dict]]`） |
| `.ProtectContent(protect)` | コンテンツを保護（転送と保存を防止） |
| `.Silent(silent)` | サイレント送信（ユーザーに通知しない） |

### 送信例

```python
# 基本的なテキスト送信
await telegram.Send.To("user", user_id).Text("Hello World!")

# インラインキーボード付きのメッセージ
from ErisPulse import sdk
telegram = sdk.adapter.get("telegram")
keyboard = [
    [{"text": "ボタン1", "callback_data": "btn1"}, {"text": "ボタン2", "callback_data": "btn2"}],
    [{"text": "公式サイトへ", "url": "https://example.com"}],
]
await telegram.Send.To("group", group_id).Keyboard(keyboard).Text("選択してください：")

# メディア送信（URL 方式）
await telegram.Send.To("group", group_id).Image("https://example.com/image.jpg", caption="画像")

# @ユーザー
await telegram.Send.To("group", group_id).At("6117725680").Text("こんにちは！")

# 返信 + コンテンツ保護
await telegram.Send.To("group", group_id).Reply("12345").ProtectContent().Text("機密メッセージ")

# サイレント送信
await telegram.Send.To("group", group_id).Silent().Text("サイレント通知")

# HTML 形式メッセージ（Html は旧名のエイリアス）
await telegram.Send.To("user", user_id).HTML("<b>太字</b> <i>斜体</i>")

# 位置情報の送信（タイトル付き）
await telegram.Send.To("user", user_id).Location(39.9042, 116.4074, title="天安門", content="北京中心部")

# コールバッククエリへの応答
await telegram.Send.AnswerCallback(callback_query_id, text="処理済み", show_alert=False)

# OneBot12 組み合わせメッセージ
ob12_message = [
    {"type": "text", "data": {"text": "複雑なメッセージ："}},
    {"type": "mention", "data": {"user_id": "6117725680", "user_name": "ユーザー名"}},
    {"type": "reply", "data": {"message_id": "12345"}},
    {"type": "image", "data": {"file": "https://http.cat/200"}}
]
await telegram.Send.To("group", group_id).Raw_ob12(ob12_message)

# ステッカーの送信
await telegram.Send.To("user", user_id).Sticker("CAACAgIAAxkBAA...")  # file_id
```

## 固有イベントタイプ

Telegram イベントの変換は OneBot12 標準に従い、同時に `telegram_` プレフィックスでプラットフォーム拡張を提供します。

### メッセージイベントの detail_type マッピング

| Telegram chat.type | OneBot12 detail_type | 送信ターゲットタイプ |
|---|---|---|
| `private` | `private` | `user` |
| `group` | `group` | `group` |
| `supergroup` | `group` | `group` |
| `channel` | `channel` | `channel` |

### 固有イベントタイプ

| detail_type | 説明 |
|---|---|
| `telegram_callback_query` | コールバッククエリ（インラインキーボードボタンのクリック） |
| `telegram_inline_query` | インラインクエリ |
| `telegram_chosen_inline_result` | 選択されたインライン結果 |
| `telegram_poll` | 投票イベント |
| `telegram_poll_answer` | 投票回答 |
| `telegram_my_chat_member` | Bot 自身のメンバーステータス変更 |
| `telegram_chat_member` | チャットメンバー変更 |
| `telegram_shipping_query` | 配送先クエリ |
| `telegram_pre_checkout_query` | 決済前クエリ |

> チャット参加リクエスト（chat_join_request）は標準の `group` リクエストイベント（`sub_type="join"`）に標準化され、
> detail_type として `telegram_chat_join_request` は使用されなくなりました；関連するプラットフォームフィールド
> （`telegram_chat_join_request_id`、`telegram_chat` など）は引き続き保持されます。

### 標準メッセージセグメントタイプ

変換後のメッセージセグメントは OneBot12 標準形式を使用します：

| メッセージセグメントタイプ | 説明 | data フィールド |
|---|---|---|
| `text` | プレーンテキスト（@ユーザー名を含まない） | `text` |
| `mention` | @ユーザー（標準 OB12） | `user_id`, `user_name` |
| `reply` | 返信引用 | `message_id`, `user_id` |
| `image` | 画像 | `file_id`, `url` |
| `video` | 動画 | `file_id`, `url`, `duration`, `width`, `height` |
| `voice` | ボイス | `file_id`, `url`, `duration` |
| `audio` | 音声 | `file_id`, `url`, `duration`, `title`, `performer` |
| `file` | ファイル | `file_id`, `url`, `file_name`, `file_size`, `mime_type` |
| `location` | 位置情報 | `latitude`, `longitude`, オプションの `title`, `address` |

### プラットフォーム拡張メッセージセグメント

`telegram_` プレフィックスで識別される拡張メッセージセグメント：

| メッセージセグメントタイプ | 説明 | data フィールド |
|---|---|---|
| `telegram_sticker` | ステッカー | `file_id`, `emoji`, `sticker_type`, `url` |
| `telegram_animation` | GIF アニメーション | `file_id`, `url`, `duration`, `caption` |
| `telegram_contact` | 連絡先 | `phone_number`, `first_name`, `last_name`, `user_id` |
| `telegram_inline_keyboard` | インラインキーボード | `inline_keyboard` |

### イベント例

#### グループチャットメッセージ（@メンションを含む）
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
  "self": {
    "platform": "telegram",
    "user_id": "6117725680",
    "account_id": "default"
  },
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
    "username": "erispulse",
    "type": "supergroup"
  }
}
```

#### グループ参加申請イベント（標準化後）
```python
{
  "type": "request",
  "detail_type": "group",
  "sub_type": "join",
  "platform": "telegram",
  "user_id": "6117725680",
  "user_nickname": "申請者のニックネーム",
  "request_id": "tjr_-1002850921906_6117725680_1731212345",
  "group_id": "-1002850921906",
  "comment": "招待リンクの名前",
  "self": {
    "platform": "telegram",
    "user_id": "6117725680",
    "account_id": "default"
  },
  "telegram_chat_join_request_id": "",
  "telegram_chat": {
    "id": -1002850921906,
    "title": "ErisPulse",
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

#### インラインキーボード付きのメッセージ
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

アダプターは以下のプラットフォーム専用メソッドを登録しており、`platform == "telegram"` の場合にのみ使用できます：

### メッセージ関連

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `is_bot_message()` | `bool` | メッセージがボットからのものかどうかを判定 |
| `is_edited_message()` | `bool` | 編集されたメッセージかどうかを判定 |
| `is_topic_message()` | `bool` | トピック（Topic）メッセージかどうかを判定 |
| `get_update_id()` | `int` | Telegram update ID を取得 |
| `get_chat_title()` | `str` | チャットタイトルを取得 |
| `get_chat_username()` | `str` | チャットのユーザー名を取得 |
| `get_forward_from()` | `dict` | 転送元情報を取得 |
| `get_topic_id()` | `str` | トピック ID を取得 |

### コールバッククエリ関連

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_callback_data()` | `str` | コールバッククエリの callback_data を取得 |
| `get_callback_id()` | `str` | コールバッククエリ ID を取得（応答に使用） |

### メッセージセグメントデータの抽出

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

    # メッセージの属性
    if event.is_bot_message():
        return  # ボットのメッセージを無視

    if event.is_edited_message():
        print("これは編集されたメッセージです")

    # チャット情報
    title = event.get_chat_title()
    username = event.get_chat_username()

    # 転送元
    forward = event.get_forward_from()

    # メッセージセグメントデータ
    sticker = event.get_sticker_info()
    contact = event.get_contact_info()
    location = event.get_location()
    keyboard = event.get_inline_keyboard()

    # トピック
    if event.is_topic_message():
        topic_id = event.get_topic_id()

@notice.on_notice()
async def handle_notice(event):
    if event.get("platform") != "telegram":
        return

    if event.get("detail_type") == "telegram_callback_query":
        callback_data = event.get_callback_data()
        callback_id = event.get_callback_id()

        # コールバッククエリへの応答
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.AnswerCallback(callback_id, text="クリックされました")

        # メッセージへの返信（マルチアカウント環境下では自動的にイベントが属するアカウントで処理）
        await event.reply(f"あなたがクリックした内容：{callback_data}")
```

## 拡張フィールドの説明

- すべての固有フィールドは `telegram_` プレフィックスで識別されます
- 元のデータは `telegram_raw` フィールドに保持されます
- 元のイベントタイプは `telegram_raw_type` フィールドに保持されます
- イベントの `self.account_id` はイベントを生成したアカウント名です（マルチアカウント環境下では `event.reply()` が自動的にそのアカウントで処理します）
- チャンネルメッセージは `detail_type="channel"` を使用します
- 個人チャットメッセージは `detail_type="private"` を使用します（送信時は `user` に変換する必要があります）
- トピックメッセージには `thread_id` フィールドが含まれます
- `@` メンションは標準の `mention` メッセージセグメントタイプ（`type: "mention"`）を使用し、テキストには @ユーザー名が含まれません

## 設定オプション

Telegram アダプターはマルチアカウント設定をサポートします：

### 設定例
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true

[Telegram_Adapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
enabled = true
```

### 実行モード

Telegram アダプターは **Polling（ポーリング）** モードのみをサポートし、Webhook モードは削除されました。

### プロキシ設定

プロキシ経由で Telegram API に接続する必要がある場合は、システムレベルのプロキシ（環境変数 `ALL_PROXY` / `HTTPS_PROXY`）を使用してください。

### 旧バージョン設定の移行

旧バージョンの単一 token 設定は自動的に互換性を保ちます：
```toml
# 旧形式（引き続き使用可能ですが、移行を推奨）
[Telegram_Adapter]
token = "YOUR_BOT_TOKEN"
```

新しい形式への移行を推奨します：
```toml
[Telegram_Adapter.accounts.default]
token = "YOUR_BOT_TOKEN"
enabled = true
```



### 云湖适配

# 云湖プラットフォームの特徴ドキュメント

YunhuAdapterは、Yunhuプロトコルに基づいて構築されたアダプターであり、Yunhuのすべての機能モジュールを統合し、一貫したイベント処理とメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.6.2
- メンテナ: ErisPulse
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム紹介: Yunhuは、企業向けのリアルタイムコミュニケーションプラットフォームです。
- アダプタ名: YunhuAdapter
- 多アカウント対応: bot_idで識別可能な複数のYunhuロボットアカウントを構成可能
- 鏈式修飾子対応: .Reply()などの修飾子メソッドをチェーンで使用可能
- OneBot12互換: OneBot12形式のメッセージ送信に対応

## v5 ファンタジー更新（4.4.0）

本アダプターはv5ファンタジーに完全に適合し、増分アップグレードでAPIは互換性を保持しています：

- **公式サービスAPI一覧**（Api DSL拡張メソッド）: 編集メッセージ、一括送信、メッセージリスト、ユーザー/グローバルボード、グループメンバーの禁止、グループメンバーの削除、グループメッセージタイプ制限、グループタグのCRUD、ユーザーにタグを付ける
- **標準 keyboard 段**（跨プラットフォーム相互作用コンポーネント標準）: {"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}} メッセージは自動的にYunhuのbuttonsに変換される。.Buttons(rows) / .Keyboard(rows) 修飾子は汎用構造を受け入れる（元の構造は後方互換）
- **相互作用コールバック標準フィールド**: ボタンクリック/A2UIイベントには interaction_id / button_data という標準フィールドが含まれる
- **spawn_background タスクの所属**: WS接続タスクは `runtime.spawn_background` を使用
- **フレームワークのソフト依存**: ErisPulse>=2.7.1を実行時に検出し、警告を表示する。起動時にバージョンログを出力する

### プラットフォーム拡張アクション（call / Api メソッド）

```python
from ErisPulse import sdk
yunhu = sdk.adapter.get("yunhu")

# Api メソッド（公式サービスAPI）
await yunhu.Api.edit_message(msg_id, recv_id, "group", "text", {"text": "新内容"})
await yunhu.Api.batch_send(["userId1", "userId2"], "text", {"text": "公告"})
await yunhu.Api.get_message_list(group_id, "group", before=10)
await yunhu.Api.set_user_board(chat_id, "group", "看板内容", expire_time=3600)
await yunhu.Api.dismiss_global_board()
await yunhu.Api.gag_group_member(group_id, user_id, 600)      # 禁言600秒、0=解除
await yunhu.Api.remove_group_member(group_id, user_id)
await yunhu.Api.set_group_msg_type_limit(group_id, "text,image")
await yunhu.Api.create_group_tag(group_id, "VIP", color="#FF5733")
await yunhu.Api.add_user_tag(group_id, user_id, "VIP")

# ボタンクリックコールバック（標準フィールド）
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "yunhu" and event.get("button_data"):
        data = event["button_data"]     # 跨プラットフォーム統一取値
        interaction_id = event["interaction_id"]
```

> 完全な標準説明は[跨プラットフォーム相互作用コンポーネント標準](../standards/standardization-guide.md)をご覧ください。

## 標準化対応（4.6.2）

このバージョンではアダプターの標準化が完了し、応答構造とエラーコードは[API応答規格](../standards/api-response.md)に従います。

### アカウントと多アカウントの完結

- **イベント注入 `self.account_id`**（内部アカウント名）: 受信したイベント `self` オブジェクトには、イベントを発生させたアカウント名が含まれており、`event.reply()` は自動的に**受信したアカウント**にルーティングされます。多アカウントの場面では、もう手動で `Using(bot_id)` を使用する必要はありません。
- **`call_api` 双重互換フィールド**: `account_id`（標準名）/ `_account_id`（旧名）の両方でアカウントを指定可能。フレームワークのApiDSL（`Api.Using(...)`）は自動的に適応
- **`Send` は `send_context` を読み取る**（イベントアカウントのバックアップ）: イベント処理コンテキスト内で `Send` を呼び出す場合、デフォルトでは送信元アカウントにフォールバックする

### エラーコード規格

| retcode | 含義 | 说明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | 网络错误 | 云湖服务器失败等网络类异常 |
| 34100 | 平台失败 | 云湖返回失败；原始响应保留在 `yunhu_raw` |
| 10002 | 不支持 | 资源不存在（机器人/用户/群不存在）或平台无对应能力的标准动作 |
| 10003 | 参数错误 | 缺少或无效参数 |

> **4.6.2 変更点**: `_platform` を追加した後、`make_response` はフレームワークによって自動的に `yunhu_raw` を含む。プラットフォームの失敗はすべて `34100` を返す。"机器人/用户/群不存在" は `34001` から `10002`（リソースが存在しない）に変更された。

### 応答構造の調整

元の応答の非標準 `self` フィールドは `data.self_info`（bot_id を含む）に移動し、トップレベルには標準フィールドと `yunhu_raw` だけが残る：

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "self_info": {"user_id": "bot_id"},
    "messageInfo": {"msgId": "..."}
  },
  "message_id": "123456",
  "message": "",
  "yunhu_raw": {}
}
```

### 未知のイベントは静かに破棄されない

認識できないYunhuイベントは、`type="unknown"` イベント（`detail_type` は元のイベントタイプ、元のデータは `yunhu_raw` に保持）を生成し、警告ログを出力する。モジュールはこれに基づいて未対応のイベントタイプを調査できる。

### プラットフォーム拡張メソッドの約定

歴史的なプラットフォーム拡張メソッド（`edit_message` / `batch_send` / `set_user_board` / `gag_group_member` / `create_group_tag` など）は引き続き使用可能。**新しいプラットフォーム拡張はすべて `Api.call("yunhu.xxx", **params)` を通じて行う**（下記「プラットフォーム拡張アクション」を参照）。

---

## 支持するメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実現可能。例えば：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("user", user_id).Text("Hello World!")
```

サポートする送信タイプは以下の通りです：
- `.Text(text: str)`：純粋なテキストメッセージを送信。
- `.Html(html: str)`：HTML形式のメッセージを送信。`.HTML(html)` は別名（標準 Send メソッドの命名と一致させる）。
- `.Markdown(markdown: str)`：Markdown形式のメッセージを送信。
- `.MergeForward(nodes, title="合并聊天记录")`：合併転送メッセージを送信（<details>折りたたみHTMLカードとしてレンダリングされ、htmlチャネルを通じて送信される）。
- `.A2UI(text: str)`：A2UI形式のメッセージを送信。
- `.Image(file: bytes, stream: bool = False, filename: str = None)`：画像メッセージを送信。ストリームアップロードとカスタムファイル名をサポート。
- `.Video(file: bytes, stream: bool = False, filename: str = None)`：動画メッセージを送信。ストリームアップロードとカスタムファイル名をサポート。
- `.File(file: bytes, stream: bool = False, filename: str = None)`：ファイルメッセージを送信。ストリームアップロードとカスタムファイル名をサポート。
- `.Batch(target_ids: List[str], message: str, content_type: str = "text", **kwargs)`：一括メッセージ送信。
- `.Edit(msg_id: str, text: str, content_type: str = "text", buttons: List = None)`：既存のメッセージを編集。
- `.Recall(msg_id: str)`：メッセージを撤回。
- `.Board(content: str, content_type: str = "text")`：公告看板を送信。作用域は `To()` から推測される（ターゲットを指定=ローカル看板、未指定=グローバル看板）。チェーン修飾：`.Expire(duration)` 相対的な期限（秒）、`.ExpireAt(timestamp)` 絶対的な期限（秒単位のタイムスタンプ）、`.ForMember(member_id)` グループメンバー看板；**内容が空の場合は自動的に看板を撤回**。旧式 `Board("local", "公告")` 明示的な scope 書き込みもまだ互換性がある。
- `.DismissBoard()`：公告看板を撤回。作用域は `To()` から推測され、`.ForMember(member_id)` もサポートする。旧式 `DismissBoard("local")` 書き込みもまだ互換性がある。
- `.Stream(content_type: str, content_generator: AsyncGenerator, **kwargs)`：ストリームメッセージを送信。

### グループ管理メソッド

すべてのグループ管理メソッドはチェーン構文でグループを指定する必要がある。例えば：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

await yunhu.Send.To("group", group_id).Kick(user_id)
```

- `.Kick(user_id: str)`：グループメンバーを削除。ロボットは`グループメンバーを削除する権限`が必要。
- `.Ban(user_id: str, duration: int = 600)`：ユーザーを禁止。`duration`は禁止時間（秒）、0は解除、-1は永久禁止。ロボットは`ユーザーを禁止する権限`が必要。
- `.CreateTag(tag: str, color: str = None, desc: str = None, sort: int = None)`：グループタグを作成。`color`は#RRGGBB形式、`sort`が小さいほど前に表示される。ロボットは`タググループを制御する権限`が必要。
- `.EditTag(tag: str, new_tag: str = None, color: str = None, desc: str = None, sort: int = None)`：グループタグを編集。各パラメータはオプションで、指定しない場合は変更しない。ロボットは`タググループを制御する権限`が必要。
- `.DeleteTag(tag: str)`：グループタグを削除。ロボットは`タググループを制御する権限`が必要。
- `.GetTagList()`：グループタグリストを取得。返却データには`list`配列が含まれる。
- `.AddUserTag(user_id: str, tag: str)`：ユーザーにタグを追加。ロボットは`タググループを制御する権限`が必要。
- `.RemoveUserTag(user_id: str, tag: str)`：ユーザーからタグを削除。ロボットは`タググループを制御する権限`が必要。
- `.SetMsgTypeLimit(types: str)`：グループ内のメッセージタイプを制限。`types`はメッセージタイプ名で、複数ある場合はカンマで区切る（例: `"text,image,video"`）、空文字列は制限しない。ロボットは`グループ情報を変更する権限`が必要。

### メッセージ検索メソッド

指定された会話（ユーザー/グループ）の履歴メッセージリストを取得するには、チェーン構文でターゲットを指定する必要がある。例えば：
```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

result = await yunhu.Send.To("group", group_id).GetMessages(before=10)
```

- `.GetMessages(message_id: str = None, before: int = None, after: int = None)`：会話の履歴メッセージを取得。返却データには`list`配列と`total`総数が含まれる。
  - `message_id`：メッセージID（オプション）。指定しない場合、`before`と組み合わせて最近のN件を返す。
  - `before`：指定したメッセージIDの前のN件を返す。
  - `after`：指定したメッセージIDの後のN件を返す。
  - > **注意：** `before` と `after` は少なくとも1つを指定する必要があり、0より大きくなければ、サーバーはメッセージを返さない。

Board 作用域は `To()` によって自動的に推測される：
- `To(target_type, target_id)` を指定 → ローカル看板（指定されたユーザー/グループ）
- `To()` を指定しない → グローバル看板

```python
# ローカル看板（60 秒後相対的な期限）
await yunhu.Send.To("group", group_id).Expire(60).Board("公告", content_type="markdown")

# グループメンバー看板（指定されたメンバーのみ表示）
await yunhu.Send.To("group", group_id).ForMember(user_id).Board("あなた専用")

# 絶対時間の期限
await yunhu.Send.To("group", group_id).ExpireAt(1785208268).Board("指定時間で期限切れ")

# グローバル看板
await yunhu.Send.Board("グローバル公告")

# ローカル看板をクリア（内容が空の場合は自動的に看板を撤回）
await yunhu.Send.To("group", group_id).Board("")
```

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を示すネストされたリストです。各ボタンオブジェクトには以下のフィールドが含まれます：

| フィールド         | タイプ   | 必須 | 説明                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `text`       | string | 是       | ボタン上の文字                                                         |
| `actionType` | int    | 是       | 動作タイプ：<br>`1`: URL に移動<br>`2`: コピー<br>`3`: イベントを報告            |
| `url`        | string | 否       | `actionType=1` の場合、移動先の URL を使用する                         |
| `value`      | string | 否       | `actionType=2` の場合、この値がクリップボードにコピーされる<br>`actionType=3` の場合、この値がサブスクライバに送信される |

例：
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックして移動", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントを報告", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きメッセージ")
```
> **注意：**
> - ユーザーが**イベント報告ボタン**をクリックした場合にのみ、通知を受け取る。**コピー**と**URL移動**は通知を受け取れない。

### チェーン修飾メソッド（組み合わせ可能）

チェーン修飾メソッドは `self` を返し、チェーンで呼び出すことが可能。最終的な送信メソッドの前に呼び出す必要がある：

- `.Reply(message_id: str)`：指定されたメッセージに返信。
- `.At(user_id: str)`：指定されたユーザーを@する。
- `.AtAll()`：全員を@する。
- `.Buttons(buttons: List)`：ボタンを追加する。

### チェーン呼び出しの例

```python
# 基礎的な送信
await yunhu.Send.To("user", user_id).Text("Hello")

# メッセージの返信
await yunhu.Send.To("group", group_id).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await yunhu.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("返信とボタン付きメッセージ")
```

### グループ管理の例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# グループメンバーの削除
await yunhu.Send.To("group", group_id).Kick(user_id)

# ユーザーの禁止（10分間）
await yunhu.Send.To("group", group_id).Ban(user_id, duration=600)

# 禁止の解除
await yunhu.Send.To("group", group_id).Ban(user_id, duration=0)

# 永久禁止
await yunhu.Send.To("group", group_id).Ban(user_id, duration=-1)

# グループタグの作成
await yunhu.Send.To("group", group_id).CreateTag("VIPユーザー", color="#FF5733", desc="VIP会員")

# グループタグの編集
await yunhu.Send.To("group", group_id).EditTag("VIPユーザー", new_tag="SVIPユーザー", color="#33C4FF")

# グループタグの削除
await yunhu.Send.To("group", group_id).DeleteTag("VIPユーザー")

# グループタグリストの取得
result = await yunhu.Send.To("group", group_id).GetTagList()

# ユーザーにタグを追加
await yunhu.Send.To("group", group_id).AddUserTag(user_id, "VIPユーザー")

# ユーザーからタグを削除
await yunhu.Send.To("group", group_id).RemoveUserTag(user_id, "VIPユーザー")

# メッセージタイプの制限
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("text,image,video")

# メッセージタイプの制限を解除
await yunhu.Send.To("group", group_id).SetMsgTypeLimit("")
```

### メッセージ検索の例

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# グループの最近10件のメッセージを取得（合計10件返される）
result = await yunhu.Send.To("group", group_id).GetMessages(before=10)

# グループで指定されたメッセージIDの前の10件を取得（合計11件返される）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10)

# グループで指定されたメッセージIDの前後各10件を取得（合計21件返される）
result = await yunhu.Send.To("group", group_id).GetMessages(message_id="msg_xxx", before=10, after=10)

# ユーザー会話の履歴メッセージを取得
result = await yunhu.Send.To("user", user_id).GetMessages(message_id="msg_xxx", before=10)
```

### OneBot12メッセージサポート

アダプターはOneBot12形式のメッセージを送信することをサポートし、跨プラットフォームメッセージの互換性を確保する：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾と組み合わせて使用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

## 標準APIアクション（ApiDSL）

> [!NOTE]
> この機能には ErisPulse **2.7.0+** および YunhuAdapter **4.3.0+** が必要です。

`Send` チェーン送信に加えて、アダプターは `Api` 内部クラスを提供しており、OneBot12 標準 API アクションと Yunhu プラットフォームの拡張アクションを公開しています。すべてのメソッドは標準レスポンス形式を返します。

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# 情報照会（公開 Web API 経由、認証不要）
result = await yunhu.Api.get_self_info()              # ボット自身の情報
result = await yunhu.Api.get_user_info("7058262")     # 任意のユーザー情報
result = await yunhu.Api.get_group_info("635409929")  # グループ情報

# ファイル操作
result = await yunhu.Api.upload_file(type="path", name="a.png", path="./a.png")
result = await yunhu.Api.get_file("https://chat-file.jwznb.com/xxx")

# メッセージの取り消し（chat_id + chat_type の追加指定が必要）
await yunhu.Api.delete_message("msg_id", chat_id="123", chat_type="group")

# マルチアカウント：Bot アカウントを指定
info = await yunhu.Api.Using("bot1").get_self_info()
```

### サポートされている標準アクション

| メソッド | 説明 | データソース |
|------|------|---------|
| `get_self_info()` | ボット自身の情報 | 公開 Web API（bot-info） |
| `get_user_info(user_id)` | ユーザー情報（任意のユーザーを照会可能） | 公開 Web API（user/homepage） |
| `get_group_info(group_id)` | グループ情報 | 公開 Web API（group-info） |
| `upload_file(*, type, name, ...)` | ファイルのアップロード（image/video/file を自動判定） | Bot オープン API |
| `get_file(file_id)` | ファイルの取得（file_id は URL そのもの、Referer を自動付与してダウンロードし base64 で返す） | プロキシダウンロード |
| `delete_message(message_id, *, chat_id, chat_type)` | メッセージの取り消し | Bot オープン API（/bot/recall） |

#### メディアメッセージとホットリンク保護（4.6.3）

Yunhu メディア CDN（`chat-img.jwznb.com` など）では **Referer によるホットリンク保護** が有効になっています：Referer なしの `GET` は一律 `403` となるため、`Referer: https://im.jwzhd.com/` を付与する必要があります。

- メディアメッセージ（image/video/file/audio）を受信した際、イベント内のメディアセグメントの `data.headers.Referer` には既にこの値が含まれています。独自にダウンロードするモジュールはこのヘッダーを付与してください
- または `call_api("get_file", file_id=<url>)` を直接使用すると、アダプターがプロキシダウンロードして base64 を返します（ホットリンク保護を自動処理）

```python
seg = event["message"][0]          # {"type": "image", "data": {...}}
img = await bot.call_api("get_file", file_id=seg["data"]["url"])
raw_bytes = base64.b64decode(img["data"]["base64"])
```

> **注意**：`get_self_info` / `get_user_info` / `get_group_info` は**非公式の公開 Web API**（chat-web-go.jwzhd.com）で実装されています。これらのインターフェースは認証不要ですが公式ドキュメントではないため、プラットフォームの更新により変更される可能性があります。失敗時には標準エラーレスポンスが返されます。

### サポートされていない標準アクション

以下の標準アクションには Yunhu に対応する API が存在せず、呼び出すと `retcode=10002`（サポートされていない操作）が返されます：
- `get_friend_list`（Bot オープン API の「ボットユーザーリスト」はまだリリース待ちの状態です）
- `get_group_list` / `get_group_member_info` / `get_group_member_list`
- `set_group_name` / `leave_group`

### プラットフォーム拡張アクション

`Api.call("yunhu.xxx", **params)` を使用して Yunhu 固有のアクションを呼び出します（パラメータは OB12 スタイルの命名を採用し、アダプターが自動的に Yunhu のフィールドへ変換します）：

| 拡張アクション | 説明 | 同等の Send メソッド |
|---------|------|---------------|
| `yunhu.recall` | メッセージの取り消し（msg_id, chat_id, chat_type） | `Send.To(...).Recall(msg_id)` |
| `yunhu.kick` | グループメンバーの削除（group_id, user_id） | `Send.To("group", g).Kick(uid)` |
| `yunhu.ban` | ミュート（group_id, user_id, duration） | `Send.To("group", g).Ban(uid, duration)` |
| `yunhu.unban` | ミュート解除（group_id, user_id） | `Send.To("group", g).Ban(uid, duration=0)` |
| `yunhu.tag.create/edit/delete/list` | グループタグの CRUD（group_id, ...） | `Send.To("group", g).CreateTag(...)` など |
| `yunhu.tag.relate` / `yunhu.tag.relate_cancel` | ユーザーへのタグ追加/削除 | `Send.To("group", g).AddUserTag(...)` など |
| `yunhu.set_member_title` / `yunhu.unset_member_title` | **メンバータイトルのセマンティックエイリアス**（タグ≈タイトル、内部的に tag.relate にマッピング） | — |
| `yunhu.msg_type_limit` | グループメッセージタイプの制限（group_id, type） | `Send.To("group", g).SetMsgTypeLimit(...)` |
| `yunhu.get_messages` | 履歴メッセージの取得（chat_id, chat_type, message_id?, before?, after?） | `Send.To(...).GetMessages(...)` |
| `yunhu.bot_info` | 公開 bot-info 照会（bot_id） | — |
| `yunhu.user_homepage` | 公開ユーザーホームページ照会（user_id） | — |

```python
# プラットフォーム拡張の例
await yunhu.Api.call("yunhu.kick", group_id="123", user_id="456")
await yunhu.Api.call("yunhu.set_member_title", group_id="123", user_id="456", title="VIP")
result = await yunhu.Api.call("yunhu.get_messages", chat_id="123", chat_type="group", before=10)
```

> **タグとタイトル**：Yunhu の「タグ」は OneBot12 のグループメンバー `title` とセマンティクス上同等です。`yunhu.set_member_title` は `yunhu.tag.relate` のネイティブなセマンティックエイリアスであり、両者は内部的に同じエンドポイントへマッピングされます。グループメッセージイベントにおける送信者の役割は、`senderUserLevel` から標準の `role` フィールド（owner/admin/member）へマッピングされます。

## 送信メソッドの返り値

すべての送信メソッドは Task オブジェクトを返し、直接 await して送信結果を取得できる。返り値は ErisPulse アダプターの標準化された返り値規格に従う：

```python
{
    "status": "ok",           // 実行状態
    "retcode": 0,             // 返り値コード
    "data": {...},            // 返り値データ（self_info は bot_id を含む、上記「返り値構造の調整」参照）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_raw": {...}        // 元の返り値データ
}
```

> **4.6.2 変更点**：元の返り値の非標準 `self` フィールドは `data.self_info` に移動しました。bot_id を取得するには `result["data"]["self_info"]["user_id"]` を使用してください。

## 特有のイベントタイプ

`platform=="yunhu"` を検証してから本プラットフォームの特有機能を使用する必要があります。

### 核心的な違い点

1. 特有のイベントタイプ：
    - 表形式（例: 表形式のコマンド）: yunhu_form
    - 表情/ステッカー形式のメッセージ: yunhu_expression
    - ボタンクリック: yunhu_button_click
    - A2UIボタンクリック: yunhu_a2ui_button
    - ロボットの設定: yunhu_bot_setting
    - ショートカットメニュー: yunhu_shortcut_menu
2. 標準フィールドの拡張（4.3.0+）:
    - メッセージイベントに標準の `role` フィールドが追加されました（Yunhu の `senderUserLevel` から `owner`/`admin`/`member` にマッピング）
    - 新たに `user_avatar` フィールドが追加されました（送信者のアバター URL）
3. 拡張フィールド:
    - すべての特有フィールドは `yunhu_` で始まるプレフィックスが付いています
    - 元のデータは `yunhu_raw` フィールドに保持されます
    - プライベートチャットでは `self.user_id` はロボットのIDを表します

### 特殊フィールドの例

```python
# 表形式のコマンド
{
  "type": "message",
  "detail_type": "private",
  "yunhu_command": {
    "name": "表形式のコマンド名",
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

# ボタンクリックイベント
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

# A2UIボタンクリックイベント
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
    "source_component_id": "元のコンポーネントID",
    "form_context": {},
    "interaction_json": "インタラクションデータのJSON文字列"
  }
}

### ボタンクリックイベントの処理例

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    """Yunhu通知イベントを処理する

    すべての通知イベントを処理するには、on_notice()デコレータを使用し、
    detail_typeで異なるタイプの通知を区別する
    event.reply()は自動的にYunhuプラットフォームで返信する
    """

# ボタンクリックイベントかどうかを確認
    if event.get("detail_type") == "yunhu_button_click":
        user_id = event.get_user_id()
        user_nickname = event.get_user_nickname()
        button_value = event.get("yunhu_button", {}).get("value", "")

        print(f"ユーザー {user_nickname}({user_id}) がボタンをクリックしました: {button_value}")

# event.reply()を使用して返信（プラットフォームに応じて正しい送信方法を選択する）
        if button_value == "confirm":
            await event.reply("確認ボタンをクリックしました！")
        elif button_value == "cancel":
            await event.reply("操作がキャンセルされました")
        else:
            await event.reply(f"選択を受け付けました: {button_value}")

# ショートカットメニューイベントを処理
    elif event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get("yunhu_menu", {}).get("id", "")
        await event.reply(f"ショートカットメニューが起動しました: {menu_id}")

# ロボットの設定変更
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

### チェーン呼び出しを使ってボタン付きメッセージを送信する

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

buttons = [
    [
        {"text": "確認", "actionType": 3, "value": "confirm"},
        {"text": "キャンセル", "actionType": 3, "value": "cancel"},
        {"text": "詳細を表示", "actionType": 1, "url": "http://example.com/detail"}
    ]
]

# グループにボタン付きメッセージを送信
await yunhu.Send.To("group", "123456").Buttons(buttons).Text("以下の操作を確認してください")

# ユーザーのプライベートチャットにボタン付きメッセージを送信
await yunhu.Send.To("user", "789").Buttons(buttons).Text("あなたの好みの設定を選択してください")
```

### A2UIメッセージの送信

```python
from ErisPulse import sdk

yunhu = sdk.adapter.get("yunhu")

# A2UIメッセージを送信
await yunhu.Send.To("user", user_id).A2UI("A2UIインタラクションカードの内容")
```

# ロボットの設定
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
  "user_id": "メニューを起動したユーザーID",
  "user_nickname": "ユーザーのニックネーム",
  "group_id": "グループID（プライベートチャットの場合）",
  "yunhu_menu": {
    "id": "メニューID",
    "type": "メニューのタイプ(整数)",
    "action": "メニューのアクション(整数)"
  }
}
```

## Event Mixin 拡張メソッド

アダプターは以下のプラットフォーム固有のメソッドを登録し、`platform == "yunhu"` の場合にのみ使用可能：

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_raw_event()` | `dict` | Yunhuの元のイベントデータを取得（`yunhu_raw`） |
| `get_sender_level()` | `str` | 送信者のYunhuの元のレベル（owner/administrator/member/unknown） |
| `get_sender_role()` | `str` | 送信者のOneBot12標準のrole（owner/admin/member） |
| `get_sender_title()` | `str` | 送信者の頭語（標準の`title`フィールドのアクセサ、予約） |
| `get_sender_avatar()` | `str` | 送信者のアバターURL |
| `get_command()` | `dict` | コマンドデータ（コマンドメッセージイベントのみ、`yunhu_command`） |
| `get_button_value()` | `str` | ボタンクリックイベントのvalue（`yunhu_button.value`） |
| `get_a2ui_action()` | `str` | A2UIボタンクリックイベントのactionName |
| `get_a2ui_form_context()` | `dict` | A2UIボタンクリックイベントのフォームコンテキスト |
| `get_menu_id()` | `str` | ショートカットメニューイベントのID（`yunhu_menu.id`） |
| `get_setting()` | `dict` | ロボット設定イベントの設定データ（`yunhu_setting`） |
| `is_command_message()` | `bool` | コマンドメッセージかどうか |
| `is_button_click()` | `bool` | ボタンクリックイベントかどうか |
| `is_a2ui_button()` | `bool` | A2UIボタンクリックイベントかどうか |

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_yunhu_notice(event):
    if event.get("platform") != "yunhu":
        return

    if event.is_button_click():
        value = event.get_button_value()
        await event.reply(f"ボタンをクリックしました: {value}")

    if event.get("detail_type") == "yunhu_shortcut_menu":
        menu_id = event.get_menu_id()
```

## 拡張フィールドの説明

- すべての特有フィールドは `yunhu_` プレフィックスで始まり、標準フィールドとの衝突を避ける
- 元のデータは `yunhu_raw` フィールドに保持され、Yunhuプラットフォームの完全な元のデータにアクセス可能
- `self.user_id` はロボットのIDを表す（設定のbot_idから取得）
- 表形式のコマンドは `yunhu_command` フィールドを通じて構造化データを提供
- ボタンクリックイベントは `yunhu_button` フィールドを通じてボタンに関する情報を提供
- A2UIボタンクリックイベントは `yunhu_a2ui` フィールドを通じてA2UIインタラクションに関する情報を提供
- ロボットの設定変更は `yunhu_setting` フィールドを通じて設定項目のデータを提供
- ショートカットメニュー操作は `yunhu_menu` フィールドを通じてメニューに関する情報を提供
- 表情/ステッカー形式のメッセージは `yunhu_expression` メッセージセグメントを通じてステッカーのデータを提供（sticker_id、ステッカーのパックID、画像のサイズなど）

### 表情/ステッカー形式のメッセージセグメント (yunhu_expression)

ユーザーが表情/ステッカーを送信すると、メッセージセグメントのタイプは `yunhu_expression` となる：

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
| `sticker_id` | string | ステッカーの唯一の識別子 |
| `sticker_pack_id` | string | ステッカーのパックID |
| `expression_id` | string | 表情のID |
| `image_name` | string | 表情の画像のファイルパス |
| `width` | int | 画像の幅（オプション） |
| `height` | int | 画像の高さ（オプション） |

使用例：
```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "yunhu":
        for segment in event.get("message", []):
            if segment.get("type") == "yunhu_expression":
                data = segment["data"]
                print(f"表情パックを受け取りました: sticker_id={data['sticker_id']}, パックID={data['sticker_pack_id']}")
```

---

## 多Bot設定

### 設定の説明

Yunhuアダプターは複数のYunhuロボットアカウントを同時に設定および実行できる。

```toml
# config.toml
[Yunhu_Adapter.accounts.bot1]
token = "your_bot1_token"  # ロボットtoken（必須）
mode = "ws"  # 受信モード（オプション、デフォルトは"ws"、"ws"または"webhook"可）
webhook_path = "/webhook/bot1"  # Webhookのパス（オプション、デフォルトは"/webhook"）
enabled = true  # 有効かどうか（オプション、デフォルトはtrue）

[Yunhu_Adapter.accounts.bot2]
token = "your_bot2_token"  # 第二のロボットのtoken
webhook_path = "/webhook/bot2"  # 独自のwebhookパス
enabled = true
```

**設定項目の説明：**
- `token`：Yunhuプラットフォームが提供するAPI token（必須）
- `mode`：受信モード（オプション、デフォルトは `"ws"`、"ws"または"webhook"可）
- `webhook_path`：Yunhuイベントを受け取るHTTPパス（オプション、デフォルトは"/webhook"、webhookモードのみ使用）
- `enabled`：このアカウントを有効にするかどうか（オプション、デフォルトはtrue）

**重要な注意点：**
1. YunhuプラットフォームのロボットIDは**実行時に自動検出**され、設定に指定する必要はない
2. webhookモードでは、各botに独立した`webhook_path`が必要で、独自のwebhookイベントを受け取れる
3. Yunhuプラットフォームでwebhookを設定する際、各botに該当するURLを設定する必要があります。例えば：
   - Bot1: `https://your-domain.com/webhook/bot1`
   - Bot2: `https://your-domain.com/webhook/bot2`

### Send DSLを使用してBotを指定

`Using()`メソッドを使用して、どのbotを使ってメッセージを送信するかを指定できる。このメソッドは2つのパラメータをサポートする：
- **アカウント名**：設定中のbot名（例: `bot1`, `bot2`）
- **bot_id**：設定中の `bot_id` 値

```python
from ErisPulse.Core import adapter
yunhu = adapter.get("yunhu")

# アカウント名を使ってメッセージを送信
await yunhu.Send.Using("bot1").To("user", "user123").Text("Hello from bot1!")

# bot_idを使ってメッセージを送信（自動的に対応するアカウントにマッチ）
await yunhu.Send.Using("30535459").To("group", "group456").Text("Hello from bot!")

# 指定しない場合は最初に有効なbotを使用
await yunhu.Send.To("user", "user123").Text("Hello from default bot!")
```

> **ヒント:** `bot_id` を使用する場合、システムは設定の中で一致するアカウントを自動的に検索します。これはイベントの返信時に特に便利で、`event["self"]["user_id"]` を使用して同じアカウントに返信することができます。

### イベント内のBot識別子

受信したイベントには、対応する`bot_id`情報が自動的に含まれます（4.6.2以降、内部アカウント名 `self.account_id` も注入）：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu":
        # 送信元のロボットIDを取得
        bot_id = event["self"]["user_id"]
        account_id = event["self"].get("account_id", "")  # 内部アカウント名（例: bot1）
        print(f"メッセージはBot: {bot_id}（アカウント: {account_id}）から来ました")

        # 4.6.2以降、event.reply()は受理アカウントに自動的にルーティングされるので、直接返信できます
        await event.reply("返信メッセージ")

        # まだ明示的にアカウントを指定して送信することもできます
        yunhu = adapter.get("yunhu")
        await yunhu.Send.Using(bot_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

> **ヒント**: `call_api` は、`account_id`（標準名）と `_account_id`（旧名）の両方のアカウントフィールドをサポートしており、フレームワークの ApiDSL の `Using()` とイベントアカウントのバックアップ（`send_context`）は自動的に適応されます。

### ログ情報

アダプターはログに自動的に `bot_id` 情報を含め、デバッグや追跡に便利です。

```
[INFO] [yunhu] [bot:30535459] ユーザー user123 からのプライベートチャットメッセージを受け取りました
[INFO] [yunhu] [bot:12345678] メッセージ送信成功、message_id: abc123
```

### 管理インターフェース

```python
# すべてのアカウント情報を取得
bots = yunhu.bots

# アカウントの有効状態を確認
bot_status = {
    bot_name: bot_config.enabled
    for bot_name, bot_config in yunhu.bots.items()
}

# アカウントの有効/無効を動的に変更（アダプターの再起動が必要）
yunhu.bots["bot1"].enabled = False
```

### 旧設定の互換性

旧版の `[Yunhu_Adapter.bots.*]` 設定（bot_idフィールドを含む）は `accounts` 形式に自動的に移行されます（bot_idは実行時に自動検出され、設定の値は無視されます）。新しい形式への移行を推奨します。



### 邮件适配

# メールプラットフォーム機能ドキュメント

EmailAdapter は SMTP/IMAP プロトコルベースのメールアダプターで、メールの送信・受信・処理をサポートします。

---

## ドキュメント情報

- 対応モジュールバージョン： 4.3.2
- メンテナー: ErisPulse
- 最終更新： 2026-11-10

## 基本情報

- プラットフォーム概要：標準 SMTP/IMAP プロトコルでメールを送受信する汎用アダプター
- アダプター名：EmailAdapter
- マルチアカウント対応：複数のメールアカウントの同時設定をサポート
- 接続方式：IMAP ロングポーリング受信 + SMTP 送信
- 認証方式：メールアドレス + パスワード/認証コード
- OneBot12 互換：OneBot12 形式メッセージの送信に対応

## 設定説明

### グローバル設定（EmailAdapter）

| 設定項目 | 型 | デフォルト値 | 説明 |
|--------|------|--------|------|
| `imap_server` | str | `imap.example.com` | デフォルトの IMAP サーバーアドレス |
| `imap_port` | int | `993` | デフォルトの IMAP ポート |
| `smtp_server` | str | `smtp.example.com` | デフォルトの SMTP サーバーアドレス |
| `smtp_port` | int | `465` | デフォルトの SMTP ポート |
| `ssl` | bool | `true` | デフォルトで SSL を有効にするかどうか |
| `timeout` | int | `30` | デフォルトの接続タイムアウト（秒） |
| `poll_interval` | int | `60` | IMAP ポーリング間隔（秒） |
| `max_retries` | int | `3` | 接続失敗時の最大リトライ回数 |

### アカウント設定（EmailAdapter.accounts）

各アカウントは 1 つの独立したメールボックスに対応します。アカウントレベルの設定はグローバル設定よりも優先されます。

```toml
[EmailAdapter.accounts.default]
email = "user@example.com"
password = "your-password-or-auth-code"
imap_server = "imap.example.com"    # 任意。空欄の場合はグローバルデフォルトを使用
imap_port = 993                      # 任意
smtp_server = "smtp.example.com"    # 任意
smtp_port = 465                      # 任意
ssl = true                           # 任意
timeout = 30                         # 任意
enabled = true

[EmailAdapter.accounts.backup]
email = "backup@example.com"
password = "another-password"
enabled = true
```

## v5 パラダイム更新（4.2.0）

- **Api DSL 最小セット**：get_self_info（メールアドレス）/get_status/get_version/get_supported_actions
- **spawn_background タスクの所属**：IMAP ポーリングタスクは runtime.spawn_background を使用するように変更
- **フレームワークのソフト依存**：実行時に ErisPulse>=2.7.1 を検出して通知、起動時にバージョンログを出力
- インポートパスを Core.Bases に更新。_load_accounts は維持（グローバルデフォルト値のマージは本アダプター固有のロジック）

## 標準化対応（4.3.2）

レスポンス構造とエラーコードは [API レスポンス仕様](../standards/api-response.md) に準拠しています。

### イベントとレスポンスフィールド

- **メッセージイベントにトップレベルの `message_id` を補完**：メールの `Message-ID` ヘッダーから取得
- **`Message-ID` のないメールイベントの id は uuid にフォールバック**：イベントの `id` と `message_id` が空になることがなくなり、id の重複によってイベントが下流の重複排除で破棄されるのを回避
- **`get_self_info` の生データはレスポンスのトップレベル `email_raw` に格納**、標準フィールドには `user_id`（メールアドレス）が含まれます

### HTML 送信メソッド

- `.Html(html: str)`：HTML 形式のメールを送信
- `.HTML(html: str)`：`.Html()` のエイリアス（標準 Send メソッドの命名規則と一貫性を維持）

### エラーコード仕様

| retcode | 意味 | 説明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | ネットワークエラー | SMTP/IMAP 接続系の失敗（タイムアウト、接続拒否など） |
| 34100 | プラットフォーム失敗 | SMTP による拒否（受信者/送信者/データ/認証の拒否）。元のエラーは `email_raw` に保持されます |
| 10003 | パラメーターエラー | パラメーターの欠落または無効 |

### アカウントとマルチアカウント

- `Send` は `send_context` を読み取ります（イベントアカウントへのフォールバック）：イベントコンテキストから `Send` を呼び出す場合、デフォルトで送信元アカウントにフォールバックします
- マルチアカウントでの送信は `Send.Using("アカウント名")` で明示的に指定します

---


### 対応済みプラットフォーム機能

- **受信**：IMAP ポーリングによるメール受信（本文/HTML/添付ファイルをメッセージセグメントに解析）、未読の増分検出
- **送信**：SMTP によるメール送信（Subject/Text/Html/Cc/Bcc/ReplyTo/Attachment）、マルチアカウント対応
- **API**：アカウント情報と実行状態（最小セット）。メールの取り消しやグループなどの概念は適用外

---

## 対応するメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています：

```python
from ErisPulse.Core import adapter
mail = adapter.get("email")

# シンプルなテキストメール
await mail.Send.To("private", "to@example.com").Subject("テスト").Text("本文")

# 添付ファイル付き HTML メール
await mail.Send.To("private", "to@example.com") \
    .Subject("HTMLメール") \
    .Cc(["cc1@example.com", "cc2@example.com"]) \
    .Attachment("report.pdf") \
    .Html("<h1>HTML本文</h1>")

# Raw_ob12 で標準 OB12 メッセージを送信
await mail.Send.To("private", "to@example.com").Raw_ob12([
    {"type": "text", "data": {"text": "メール本文"}},
    {"type": "file", "data": {"file": "/path/to/attachment.pdf"}},
])

# 送信アカウントを指定（マルチアカウント）
await mail.Send.Using("default").To("private", "to@example.com").Text("本文")
```

> 注意：チェーン構文を使用する場合、パラメーターメソッド（Subject / Cc / Attachment など）は、送信メソッド（Text / Html / Raw_ob12）の前に呼び出す必要があります。

### 基本送信メソッド

| メソッド | 説明 |
|------|------|
| `.Text(text: str)` | プレーンテキストのメールを送信 |
| `.Html(html: str)` | HTML 形式のメールを送信（`.HTML(html)` はエイリアス） |
| `.MergeForward(nodes, title)` | 統合転送メールを送信（本文は `<details>` の折りたたみ HTML カード、件名はデフォルトでタイトルを使用） |
| `.Raw_ob12(message, **kwargs)` | OneBot12 形式のメッセージを送信 |

### チェーン修飾メソッド（self を返し、組み合わせて使用可能）

| メソッド | 説明 |
|------|------|
| `.Subject(subject: str)` | メールの件名を設定 |
| `.Cc(emails: Union[str, List[str]])` | CC アドレスを設定 |
| `.Bcc(emails: Union[str, List[str]])` | BCC アドレスを設定 |
| `.ReplyTo(email: str)` | 返信先アドレスを設定 |
| `.Attachment(file, filename: str = None)` | 添付ファイルを追加 |

### OB12 メッセージセグメントの逆変換（Raw_ob12）

| OB12 メッセージセグメント | メール内容への変換 |
|------------|--------------|
| `text` | プレーンテキスト本文 |
| `image` | 画像の添付ファイル |
| `video` | 動画の添付ファイル |
| `file` | ファイルの添付 |
| `audio` | 音声の添付ファイル |
| `markdown` | HTML 本文に変換 |

## 固有のイベントタイプ

### 主な相違点

1. メールイベントはすべて `message` タイプであり、`detail_type` は固定で `private` です
2. `user_id` は送信者の**純粋なメールアドレス**、`user_nickname` は送信者の表示名です
3. `message` メッセージセグメントは標準 OB12 形式（text セグメント + file セグメント）です
4. メールの件名は `email_subject` 拡張フィールドから取得できます
5. 完全な生データは `email_raw` フィールドに保持されます

### 新着メールイベント（email_new）

```json
{
  "id": "<message-id@example.com>",
  "time": 1751990446,
  "type": "message",
  "detail_type": "private",
  "platform": "email",
  "self": {
    "platform": "email",
    "user_id": "bot@example.com"
  },
  "message_id": "<message-id@example.com>",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "メール本文の内容"
      }
    }
  ],
  "alt_message": "メール件名",
  "user_id": "sender@example.com",
  "user_nickname": "Saber"
}
```

### 添付ファイル付きのメール

```json
{
  "message": [
    {
      "type": "text",
      "data": {
        "text": "添付ファイルをご確認ください"
      }
    },
    {
      "type": "file",
      "data": {
        "file_id": "document.pdf",
        "file_name": "document.pdf",
        "size": 102400
      }
    }
  ]
}
```

### 返信メールイベント（email_reply）

メールに `References` または `In-Reply-To` ヘッダーが含まれている場合、`email_raw_type` は `email_reply` になります：

```json
{
  "email_raw_type": "email_reply",
  "email_raw": {
    "references": "<original-msg-id@example.com>",
    "in_reply_to": "<original-msg-id@example.com>"
  }
}
```

## 拡張フィールドの説明

| フィールド | 型 | 説明 |
|------|------|------|
| `email_raw` | dict | 完全な元メールデータ（subject/from/to/date/cc/bcc/text_content/html_content/attachments など） |
| `email_raw_type` | str | 元のイベントタイプ：`email_new`（新着メール）または `email_reply`（返信メール） |
| `email_subject` | str | メール件名（簡易アクセス用） |
| `email_from` | str | 送信者の純粋なメールアドレス（簡易アクセス用） |
| `attachments` | list | 添付ファイルデータのリスト（バイナリの `data` フィールドを含む、後方互換用） |

## 標準イベント例

### 完全なメールイベント

```json
{
  "id": "<abc123@example.com>",
  "time": 1751990446,
  "type": "message",
  "detail_type": "private",
  "platform": "email",
  "self": {
    "platform": "email",
    "user_id": "bot@example.com"
  },
  "message_id": "<abc123@example.com>",
  "message": [
    {
      "type": "text",
      "data": {
        "text": "添付ファイルをご確認ください"
      }
    },
    {
      "type": "file",
      "data": {
        "file_id": "document.pdf",
        "file_name": "document.pdf",
        "size": 102400
      }
    }
  ],
  "alt_message": "会議のお知らせ",
  "user_id": "sender@example.com",
  "user_nickname": "Sender",
  "email_subject": "会議のお知らせ",
  "email_from": "sender@example.com",
  "email_raw": {
    "subject": "会議のお知らせ",
    "from": "\"Sender\" <sender@example.com>",
    "to": "<bot@example.com>",
    "date": "Wed, 9 Jul 2026 02:00:46 +0800",
    "message_id": "<abc123@example.com>",
    "references": "",
    "in_reply_to": "",
    "cc": "",
    "bcc": "",
    "text_content": "添付ファイルをご確認ください",
    "html_content": "<p>添付ファイルをご確認ください</p>",
    "attachments": ["document.pdf"]
  },
  "email_raw_type": "email_new",
  "attachments": [
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 102400,
      "data": "..."
    }
  ]
}
```

## 送信メソッドの戻り値

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "<sent-msg-id@example.com>",
    "time": 1751990446
  },
  "message_id": "<sent-msg-id@example.com>",
  "message": "",
  "email_raw": {
    "success": true,
    "message": "Email sent successfully"
  }
}
```

## イベント処理の例

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_email(event):
    if event.get("platform") != "email":
        return
    # 送信者の純粋なメールアドレス
    sender = event["user_id"]              # sender@example.com
    
    # 送信者の表示名
    nickname = event.get("user_nickname")  # Sender
    
    # メール件名
    subject = event.get("email_subject")   # 会議のお知らせ
    
    # プレーンテキスト本文（最初の text セグメント）
    text = event.get_text()
    
    # 完全な生データ
    raw = event.get("email_raw", {})
    html = raw.get("html_content", "")
    
    # 添付ファイルの処理
    for seg in event.get("message", []):
        if seg["type"] == "file":
            filename = seg["data"]["file_name"]
            size = seg["data"]["size"]
    
    # メールへの返信
    await event.reply(f"受信しました：{subject}")
```



### Kook 适配

# Kookプラットフォームの特徴ドキュメント

KookAdapterは、Kook（開黒啦）Bot WebSocketプロトコルに基づいて構築されたアダプターであり、Kookのすべての機能モジュールを統合し、一貫したイベント処理とメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.3.2
- 維持者: ShanFish
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: Kook（元開黒啦）は、テキスト、音声、ビデオ通信をサポートするコミュニティプラットフォームであり、完全なBot開発インターフェースを提供します。
- アダプター名: KookAdapter
- 多アカウント対応: 複数のKook Botを同時に設定できます。
- 接続方式: WebSocket長接続（Kookゲートウェイ経由）
- 認証方式: Bot Tokenを用いた認証
- 鏈式修飾対応: `.Reply()`、`.At()`、`.AtAll()`などの修飾メソッドをチェーンで使用できます。
- OneBot12互換: OneBot12形式のメッセージ送信をサポートします。

## 設定説明

KookAdapterは複数アカウントの設定に対応しており、各アカウントは独立したKook Botに対応します。

```toml
# config.toml
# アカウント1
[KookAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"     # Kook Bot Token（必須、形式: Bot xxx/xxx）
bot_id = ""                   # BotのユーザーID（オプション、未記入の場合はtokenから解析）
compress = true               # WebSocket圧縮の有効化（オプション、デフォルトはtrue）
enabled = true                # アカウントの有効化（オプション、デフォルトはtrue）

# アカウント2
[KookAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
bot_id = ""
enabled = true
```

> 旧設定の互換性: 旧の単一アカウントの`[KookAdapter]`設定（tokenを含む）が検出された場合、自動的に`accounts.default`に移行されます。

**各アカウントの設定項目説明:**
- `token`: Kook BotのToken（必須）、[Kook開発者センター](https://developer.kookapp.cn)から取得、形式は`Bot xxx/xxx`
- `bot_id`: BotのユーザーID（オプション）、未記入の場合はtokenから自動解析されます。正確性を確保するため、手動で記入することを推奨します。
- `compress`: WebSocketデータ圧縮の有効化（オプション、デフォルトは`true`）、有効化するとzlibでデータを解凍します。
- `enabled`: アカウントの有効化（オプション、デフォルトはtrue）

**API環境:**
- Kook APIの基本アドレス: `https://www.kookapp.cn/api/v3`
- WebSocketゲートウェイはAPIを介して動的に取得: `POST /gateway/index`

## 標準化対応（4.3.2）

### イベントとアカウント

- **イベント `self.account_id` 注入**: すべてのイベントに発生元のアカウント名が注入され、複数アカウント下では`event.reply()`は自動的に該当アカウントで応答されます。

### Api署名対応

| 動作 | 署名 | 説明 |
|------|------|------|
| get_channel_info | `(guild_id, channel_id)` | 新しい署名guild_idが最初のパラメータに；1つの位置パラメータのみ渡された場合、旧署名（channel_idと見なす）を互換します。 |
| get_channel_member_list | `(guild_id, channel_id)` | 同上互換ルール |
| get_guild_info / get_guild_list | - | dataは`guild_id` / `guild_name`などのフィールドを使用（旧`group_*`フィールドは破壊しないように保持） |

### エラーコード規格

エラーコードはSDKの標準化に従い、Kookプラットフォームの元のエラーコード（401xx/4xxxxなど）は直接retcodeとして使用されません：

| retcode | 説明 |
|---------|------|
| 0 | 成功（成功応答`message`は空文字列） |
| 33001 | ネットワークエラー（リクエスト異常、アカウントAPIインスタンスが初期化されていないなど） |
| 34100 | プラットフォームエラー（Kookが0以外のcodeを返した場合；元の応答は`kook_raw`に保持され、元のcodeは`kook_code`フィールドに別途保存） |
| 10002 | 不支持の動作（`get_guild_member_info` / `get_guild_member_list` / `set_guild_name` / `leave_guild` / `leave_channel`は明示的に返す；未知のAPIエンドポイントは例外を投げず、統一して10002を返す） |

## v5範式更新（4.1.0）

このアダプターはv5範式の対応を完了しました（段階的なアップグレード、API互換性あり）：

- **BaseConverter継承**: 転換器の共通フィールドはフレームワーク`build_base_event`で構築されます。
- **Api DSL**: 標準Apiアクションのマッピング（以下を参照）
- **標準 keyboard 段**: `{"type": "keyboard", "data": {"rows": [[{"label", "type": "callback|link", "data"}]]}}` テキスト+キーボードは自動的にKookカードメッセージ（section + action-group）に組み合わされます；.Keyboard(rows)修飾子は汎用構造を受け入れます。
- **spawn_background 任務の帰属**: 接続タスクはruntime.spawn_backgroundを使用します。
- **フレームワークのソフト依存**: ErisPulse>=2.7.1の実行時検出と警告；起動時にバージョンログを出力します。

### 標準Apiアクション

```python
from ErisPulse import sdk
kook = sdk.adapter.get("kook")

result = await kook.Api.get_self_info()              # GET /users/@me
result = await kook.Api.get_user_info(user_id)       # POST /user/view
result = await kook.Api.get_guild_info(guild_id)     # POST /guild/view（dataにguild_id / guild_nameを使用）
result = await kook.Api.get_guild_list()             # POST /guild/list
result = await kook.Api.get_channel_info(guild_id, channel_id)  # POST /channel/view（新しい署名guild_idが最初のパラメータ）
result = await kook.Api.get_channel_list(guild_id)   # POST /channel/list
await kook.Api.delete_message(msg_id)                # POST /message/delete
result = await kook.Api.Using("main").get_self_info()
```

### ボタン（keyboard）

```python
rows = [[{"label": "選択肢A", "type": "callback", "data": "vote:A"},
         {"label": "公式サイト",  "type": "link",     "data": "https://example.com"}]]
await kook.Send.To("channel", channel_id).Keyboard(rows).Text("選択してください")
# テキストとボタンは自動的にKookカードメッセージ（section + action-group）に組み合わされます。

# ボタンクリックのコールバック（標準フィールド）
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_button(event):
    if event.get("platform") == "kook" and event.get("button_data"):
        data = event["button_data"]
```

---

## 支援するメッセージ送信タイプ

すべての送信メソッドはチェーン式構文で実現されます。例えば：
```python
from ErisPulse.Core import adapter
kook = adapter.get("kook")

await kook.Send.To("group", channel_id).Text("Hello World!")
```

支援する送信タイプは以下の通りです：
- `.Text(text: str)`：純粋なテキストメッセージを送信します。
- `.Image(file: bytes | str)`：画像メッセージを送信します。ファイルパス、URL、バイナリデータに対応します。
- `.Video(file: bytes | str)`：ビデオメッセージを送信します。ファイルパス、URL、バイナリデータに対応します。
- `.File(file: bytes | str, filename: str = None)`：ファイルメッセージを送信します。ファイルパス、URL、バイナリデータに対応します。
- `.Voice(file: bytes | str)`：音声メッセージを送信します。ファイルパス、URL、バイナリデータに対応します。
- `.Markdown(text: str)`：KMarkdown形式のメッセージを送信します。
- `.Card(card_data: dict)`：カードメッセージ（CardMessage）を送信します。
- `.MergeForward(nodes, title="合併チャット記録")`：合併転送メッセージを送信します（カードにレンダリング：タイトルheader + 各メッセージごとにsection、KMDエスケープ、≤40ノード）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

### 鏈式修飾メソッド（組み合わせ使用可能）

修飾メソッドは`self`を返すため、チェーンで呼び出すことができます。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定したメッセージに返信（引用）します。
- `.At(user_id: str)`：指定したユーザーを@します。複数回呼び出すことで複数のユーザーを@できます。
- `.AtAll()`：全員を@します。

### 鏈式呼び出しの例

```python
# 基本的な送信
await kook.Send.To("group", channel_id).Text("Hello")

# メッセージの返信
await kook.Send.To("group", channel_id).Reply(msg_id).Text("返信メッセージ")

# ユーザーを@する
await kook.Send.To("group", channel_id).At("user_id").Text("こんにちは")

# 複数のユーザーを@する
await kook.Send.To("group", channel_id).At("user1").At("user2").Text("複数のユーザー@")

# 全員を@する
await kook.Send.To("group", channel_id).AtAll().Text("お知らせ")

# 組み合わせ
await kook.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合メッセージ")
```

### OneBot12メッセージのサポート

アダプターはOneBot12形式のメッセージ送信をサポートし、プラットフォーム間のメッセージ互換性を確保します：

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)

# 鏈式修飾と組み合わせる
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await kook.Send.To("group", channel_id).Reply(msg_id).Raw_ob12(ob12_msg)

# Raw_ob12でmentionとreplyメッセージセグメントを使用
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
    {"type": "reply", "data": {"message_id": "msg_id"}}
]
await kook.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

### 追加操作メソッド

メッセージ送信以外にも、Kookアダプターは以下の操作をサポートします：

```python
# メッセージの編集（KMarkdown type=9とCardMessage type=10のみサポート）
await kook.Send.To("group", channel_id).Edit(msg_id, "**更新後の内容**")

# メッセージの撤回
await kook.Send.To("group", channel_id).Recall(msg_id)

# ファイルのアップロード（ファイルURLの取得）
result = await kook.Send.Upload("C:/path/to/file.jpg")
file_url = result["data"]["url"]
```

## 送信メソッドの戻り値

すべての送信メソッドはTaskオブジェクトを返し、直接awaitして送信結果を取得できます。返り値はErisPulseアダプターの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行状態: "ok" または "failed"
    "retcode": 0,             // 返り値コード（0が成功、プラットフォームエラーは34100）
    "data": {...},            // 応答データ
    "message_id": "xxx",      // メッセージID
    "message": "",            // エラー情報（成功応答は空文字列）
    "kook_raw": {...},        // 元の応答データ
    "kook_code": 0            // Kookの元のcode（エラー時は保存）
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（リクエスト異常、アカウントAPIインスタンスが初期化されていないなど） |
| 34100 | プラットフォームエラー（Kookが0以外のcodeを返した場合、元の応答は`kook_raw`に保持され、元のcodeは`kook_code`に保存） |
| 10002 | 不支持の動作（「標準化対応（4.3.2）」のエラーコード規格を参照）

## 特有のイベントタイプ

`platform=="kook"`の検証が必要です。このプラットフォームの特性を使用するには。

### 核心的な違い

1. **チャンネルシステム**: Kookはサーバー（Guild）とチャンネル（Channel）の2層構造を使用し、チャンネルがメッセージの基本的な送信先です。
2. **メッセージタイプ**: Kookはテキスト(1)、画像(2)、ビデオ(3)、ファイル(4)、音声(8)、KMarkdown(9)、カードメッセージ(10)など、多様なメッセージタイプをサポートします。
3. **プライベートメッセージシステム**: Kookはチャンネルメッセージとプライベートメッセージを区別し、異なるAPIエンドポイントを使用します。
4. **メッセージ番号**: KookのWebSocketは`sn`番号を使用してメッセージの順序性を保証し、メッセージの一時保存と乱序の再配置をサポートします。
5. **メッセージの編集と撤回**: KMarkdownとCardMessageの既送信メッセージの編集とメッセージの撤回をサポートします。

### 拡張フィールド

- すべての特有のフィールドは`kook_`前接辞で識別されます。
- 元のデータは`kook_raw`フィールドに保持されます。
- `kook_raw_type`は元のKookメッセージタイプ番号を識別します（例: `1`はテキスト、`255`は通知イベント）。
- イベント`self.account_id`はイベントを発生させたアカウント名です（複数アカウント下では`event.reply()`は該当アカウントで自動的に受理されます）。

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
  "self": {
    "platform": "kook",
    "user_id": "BotID",
    "account_id": "default"
  },
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
  "alt_message": "画像の内容"
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
    {"type": "text", "data": {"text": "解析後の純粋なテキスト"}}
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
    {"type": "json", "data": {"data": "カードのJSON内容"}}
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
    {"type": "text", "data": {"text": "プライベートメッセージの内容"}}
  ]
}
```

### メッセージセグメントタイプ

Kookのメッセージタイプは`type`フィールドに基づいて対応するメッセージセグメントに自動変換されます：

| Kook type | 変換タイプ | 説明 |
|---|---|---|
| 1 | `text` | テキストメッセージ |
| 2 | `image` | 画像メッセージ |
| 3 | `video` | ビデオメッセージ |
| 4 | `file` | ファイルメッセージ |
| 8 | `record` | 音声メッセージ |
| 9 | `text` | KMarkdownメッセージ（純粋なテキスト内容を抽出） |
| 10 | `json` | カードメッセージ（元のJSON） |

メッセージセグメントの構造例：
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

メッセージに@情報が含まれている場合、メッセージセグメントの前に`mention`メッセージセグメントが挿入されます：

```json
{
  "type": "mention",
  "data": {
    "user_id": "@されたユーザーID"
  }
}
```

### mention_allメッセージセグメント

メッセージが全員を@している場合、`mention_all`メッセージセグメントが挿入されます：

```json
{
  "type": "mention_all",
  "data": {}
}
```

## WebSocket接続

### 接続フロー

1. Bot Tokenを使用して`POST /gateway/index`を呼び出し、WebSocketゲートウェイアドレスを取得します。
2. WebSocketゲートウェイに接続します。
3. HELLO（s=1）シグナルを受信し、接続状態を検証します。
4. ハートビートループを開始します（PING、s=2、30秒ごとに1回）、現在のsnを含みます。
5. メッセージイベント（s=0）を受信し、sn番号を使用して順序性を保証します。
6. ハートビート応答PONG（s=3）を受信します。

### シグナルタイプ

| シグナル | s値 | 説明 |
|------|-----|------|
| HELLO | 1 | サーバーの歓迎シグナル、接続成功後に受信します |
| PING | 2 | クライアントのハートビート、30秒ごとに送信し、現在のsnを含みます |
| PONG | 3 | ハートビート応答 |
| RESUME | 4 | 接続の再開シグナル、snを含みセッションを再開します |
| RECONNECT | 5 | サーバーが再接続を要求するシグナル、再びゲートウェイを取得する必要があります |
| RESUME_ACK | 6 | RESUME成功応答 |

### 断線再接続

- 接続が異常断線した場合、アダプターは自動的に再接続を試みます。
- 以前に`sn > 0`があった場合、まずRESUME（s=4）を試みます。
- RESUMEに失敗した場合、snとメッセージキューをリセットし、完全な新接続（HELLOフロー）を行います。
- RECONNECT（s=5）シグナルを受信した場合、状態をクリアして再接続します。

### メッセージ番号メカニズム

Kook WebSocketは`sn`（増加する番号）を使用してメッセージの順序性を保証します：

- 各メッセージイベント（s=0）を受信するたびに、snが増加します。
- 受信したメッセージのsnが連続していない場合、一時保存モードに入ります。
- 一時保存エリアのメッセージはsn順に並べ替えられ、欠落したメッセージが到着した後に順序に従って処理されます。
- 一時保存エリアがクリアされた後は、自動的に一時保存モードを終了します。

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

    await kook.Send.To("user", user_id).Text(f"あなたが言った: {text}")
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
# 画像送信（URL）
await kook.Send.To("group", channel_id).Image("https://example.com/image.png")

# 画像送信（バイナリ）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await kook.Send.To("group", channel_id).Image(image_bytes)

# ビデオ送信
await kook.Send.To("group", channel_id).Video("https://example.com/video.mp4")

# ファイル送信
await kook.Send.To("group", channel_id).File("https://example.com/file.pdf", filename="document.pdf")

# 音声送信
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
# メッセージ送信
result = await kook.Send.To("group", channel_id).Markdown("**元の内容**")
msg_id = result["data"]["msg_id"]

# メッセージの編集（KMarkdownとCardMessageのみサポート）
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
```



### Matrix 适配

# Matrixプラットフォーム特性ドキュメント

MatrixAdapter は [Matrixプロトコル](https://spec.matrix.org/) をベースに構築されたアダプターで、Matrixプロトコルのすべてのコア機能モジュールを統合し、統一されたイベント処理とメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.6.1
- メンテナー: ErisPulse
- 最終更新: 2026-11-10

## 基本情報

- プラットフォーム概要：Matrixはオープンな分散型通信プロトコルで、プライベートチャットやグループなど複数のシナリオに対応します
- アダプター名：MatrixAdapter
- マルチアカウント対応：複数の Matrix アカウントの同時設定に対応
- 接続方式：Long Polling（Matrix Sync API `/sync` 経由）
- 認証方式：access_token、または user_id + password ログインによる token 取得
- チェーン修飾対応：`.Reply()`、`.At()`、`.AtAll()` などのチェーン修飾メソッドに対応
- OneBot12互換：OneBot12 形式メッセージの送信に対応

## 設定説明

MatrixAdapter はマルチアカウント設定をサポートしており、各アカウントごとに homeserver と認証情報を個別に設定します。

```toml
# config.toml
# アカウント1
[Matrix_Adapter.accounts.default]
homeserver = "https://matrix.org"          # Matrixサーバーアドレス（必須）
access_token = "YOUR_ACCESS_TOKEN"          # アクセストークン（user_id+password のいずれか一方を選択）
user_id = ""                                # MatrixユーザーID（例：@bot:matrix.org）
password = ""                               # Matrixユーザーパスワード
auto_accept_invites = true                  # ルーム招待を自動承認するか（任意、デフォルトtrue）
enabled = true                              # 有効にするか（任意、デフォルトtrue）

# アカウント2
[Matrix_Adapter.accounts.bot2]
homeserver = "https://matrix.example.com"
access_token = "ANOTHER_TOKEN"
enabled = true
```

> 旧設定との互換性：旧式の単一アカウント `[Matrix_Adapter]` 設定（access_token を含む）が検出された場合、自動的に `accounts.default` へ移行されます。

**設定項目の説明（各アカウント）：**
- `homeserver`：Matrixサーバーアドレス（必須）、デフォルトは `https://matrix.org`
- `access_token`：アクセストークン、Matrixクライアントから取得できます。既に token をお持ちの場合はそのまま記入してください
- `user_id`：MatrixユーザーID（例：`@bot:matrix.org`）、`password` と併用してログインします
- `password`：Matrixユーザーパスワード、自動ログインして access_token を取得するために使用します
- `auto_accept_invites`：ルーム招待を自動承認するかどうか、デフォルトは `true`
- `enabled`：このアカウントを有効にするか（任意、デフォルトtrue）
- `encryption_enabled`：エンドツーエンド暗号化を有効にするかどうか、デフォルトは `false`
- `trust_all_devices`：未検証デバイスを自動信頼するかどうか（E2EE）、デフォルトは `true`
- `device_id`：デバイス ID（E2EE、通常は自動取得されるため記入不要）
- `store_path`：暗号化セッション保存ディレクトリ（E2EE）、デフォルトは `data/matrix/<アカウント名>`

**認証方式：**
- 方法1（推奨）：`access_token` を直接指定
- 方法2：`user_id` と `password` を指定すると、アダプターが自動的にログインAPIを呼び出して token を取得します

## v5 パラダイム更新（4.2.0）

- **BaseConverter 継承**：コンバーターの共通フィールドはフレームワークの build_base_event によって構築されます
- **Api DSL**：get_self_info/get_user_info/get_group_info/get_group_list/get_group_member_list/leave_group/delete_message(redact) + メタアクション
- **メッセージイベントへの message_id 追加**（event_id）；メッセージレジストリが delete_message をサポート
- **spawn_background タスク帰属**：同期/ハートビートタスクは runtime.spawn_background を使用するように変更
- **フレームワークのソフト依存**：実行時に ErisPulse>=2.7.1 を検出して通知；起動時にバージョンログを出力
- Matrix にはネイティブのボタン機能がないため、標準 keyboard セグメントは警告なしに無視されます（エラーにはなりません）

## エンドツーエンド暗号化（4.3.0）

4.3.0 から、アダプターは暗号化ルームのエンドツーエンド暗号化（matrix-nio[e2e] / vodozemac ベース）をネイティブサポートします：

```toml
[Matrix_Adapter.accounts.default]
user_id = "@bot:matrix.org"
password = "YOUR_PASSWORD"
encryption_enabled = true       # 有効化（デフォルトは false、既存デプロイへの影響なし）
trust_all_devices = true        # 未検証デバイスを自動信頼（デフォルト；false は厳格モード）
```

- 暗号化ルームでのメッセージ送受信は自動的に復号/暗号化、メディアはエンドツーエンド暗号化（`m.file.encrypted`）
- `device_id` は自動解析・永続化されます；セッションは `store_path`（デフォルト `data/matrix/<アカウント名>`）に保存されます。**削除しないでください**、削除すると過去のメッセージを復号できなくなります
- イベント Mixin に `event.is_encrypted()` を追加；メディアセグメントには `matrix_encrypted_file`（JWK）が付与され、`MatrixAdapter.decrypt_media()` で復号できます
- クロス署名とサーバー側キーバックアップには非対応；Python >= 3.10 が必要です
- 無効または matrix-nio 未インストールの場合は、自動的に平文モードへフォールバックします

詳細は後述の[エンドツーエンド暗号化（E2EE）](#エンドツーエンド暗号化e2ee)セクションおよび[アダプター README](https://github.com/ErisPulse/ErisPulse-MatrixAdapter) を参照してください。

## 標準化アラインメント

このセクションでは、アダプターと ErisPulse 標準化仕様の整合動作について説明します。仕様の詳細は SDK ドキュメント『API レスポンス仕様』（`docs/ja/standards/api-response.md`）および『送信メソッド仕様』（`docs/ja/standards/send-method-spec.md`）を参照してください。

### マルチアカウント受理（4.6.1 以降）

- すべてのイベントに `self.account_id`（送信元アカウント名）が注入されます；access_token ログインのアカウントも、`user_id` が空の場合でもマルチアカウント受理とイベントルーティングを正しく完了できます

### エラーコード標準化（4.6.x）

- **メディアアップロード/ダウンロード失敗とリクエストタイムアウトは一律 33001**（ネットワークエラー）
- **プラットフォーム API 失敗は一律 34100**（プラットフォームエラー）、Matrix errcode は `message` と `matrix_raw` フィールドに保持されます
- **取り消しコンテキスト欠落 10003**：`delete_message` がメッセージの帰属コンテキストを見つけられない場合、パラメータエラーを返します

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 10002 | サポートされていないアクション（例：get_friend_list、Matrix には友人の概念がない） |
| 10003 | 送信先が無効（Matrix ルームとして解析できない）、取り消しコンテキストの欠落 |
| 33001 | ネットワークエラー（メディアアップロード/ダウンロード失敗、リクエストタイムアウト） |
| 34100 | プラットフォーム API 失敗（Matrix errcode は message と matrix_raw に保持） |

### Send 仕様

- Send 全メソッドは `send_context` を読み取ります：イベントチェーン内では自動的に現在のイベント送信元アカウントを使用し、明示的に `Using()` で指定されたアカウントが優先されます
- HTML メソッド：`.Html(html, fallback)` でリッチテキストメッセージを送信；`HTML` は仕様上のスペル別名です（`Html` は既存モジュールとの互換性のため保持）
- `get_group_list` の戻り値の各項目に `group_name` フィールドを補完します（`get_group_info` と一致）

### 標準Apiアクション例

```python
from ErisPulse import sdk
matrix = sdk.adapter.get("matrix")
result = await matrix.Api.get_self_info()            # /account/whoami
result = await matrix.Api.get_group_info(room_id)    # m.room.name
result = await matrix.Api.get_group_list()           # /joined_rooms（各項目に group_name を含む）
await matrix.Api.delete_message(event_id)            # redact（レジストリが room_id を補完）
```

---

### 対応済みプラットフォーム機能

- **イベント**：メッセージ（m.room.message：テキスト/画像/ファイル/音声動画/返信/編集）、メンバー増減（m.room.member）、ルーム名変更などの状態イベント
- **セッション**：プライベートチャット（DM ルーム自動検出）/ グループ（ルーム）；送信は Text/Image/File/Voice/Video/Markdown/Raw_ob12 に対応
- **API**：whoami/profile/joined_rooms/ルーム状態/メンバーリスト/leave/redact（上記の Api DSL を参照）

---

## サポートされるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実装されています。例：
```python
from ErisPulse.Core import adapter
matrix = adapter.get("matrix")

await matrix.Send.To("group", room_id).Text("Hello World!")
```

サポートされる送信タイプ：
- `.Text(text: str)`：プレーンテキストメッセージを送信します。
- `.Image(file: bytes | str)`：画像メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータに対応します。
- `.Voice(file: bytes | str)`：ボイスメッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータに対応します。
- `.Video(file: bytes | str)`：動画メッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータに対応します。
- `.File(file: bytes | str, filename: str = "")`：ファイルメッセージを送信します。ファイルパス、URL、MXC URI、バイナリデータに対応します。
- `.Notice(text: str)`：通知メッセージを送信します（Matrix の m.notice タイプ）。
- `.Html(html: str, fallback: str = "")`：HTML形式のメッセージを送信します。リッチテキストコンテンツに対応します（`HTML` は仕様上のスペル別名）。
- `.MergeForward(nodes, title="チャット履歴の結合")`：結合転送メッセージを送信します（formatted_body blockquote 引用ブロック形式；ホワイトリストにより details/インラインスタイルが剥離されます）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式のメッセージを送信します。

### チェーン修飾メソッド（組み合わせ使用可能）

チェーン修飾メソッドは `self` を返し、チェーン呼び出しに対応しています。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定したメッセージに返信します（Matrix `m.in_reply_to` 関係を使用）。
- `.At(user_id: str)`：指定したユーザーをメンションします（Matrix `m.mentions` フィールドで実装）。
- `.AtAll()`：ルーム内の全員をメンションします（Matrix `@room` メンションで実装）。

### チェーン呼び出し例

```python
# 基本送信（"user" ターゲットはユーザーID（@user:server、DMルームを自動逆引き）またはルームID（!room:server）をサポート）
await matrix.Send.To("user", "@alice:matrix.org").Text("Hello")

# メッセージに返信
await matrix.Send.To("group", room_id).Reply("$event_id").Text("返信メッセージ")

# ユーザーをメンション
await matrix.Send.To("group", room_id).At("@user:matrix.org").Text("こんにちは")

# 全員をメンション
await matrix.Send.To("group", room_id).AtAll().Text("お知らせ通知")

# 組み合わせ使用：返信 + メンション
await matrix.Send.To("group", room_id).Reply("$event_id").At("@user:matrix.org").Text("複合メッセージ")

# HTMLメッセージの送信
await matrix.Send.To("group", room_id).Html("<h1>タイトル</h1><p>内容</p>", fallback="タイトル\n内容")

# 通知メッセージの送信
await matrix.Send.To("group", room_id).Notice("システム通知")
```

### OneBot12メッセージサポート

アダプターは OneBot12 形式のメッセージ送信をサポートし、クロスプラットフォームのメッセージ互換を実現します：

```python
# OneBot12 形式メッセージの送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await matrix.Send.To("user", dm_room_id).Raw_ob12(ob12_msg)

# チェーン修飾との併用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await matrix.Send.To("group", room_id).Reply("$event_id").Raw_ob12(ob12_msg)

# 複雑なメッセージ
ob12_msg = [
    {"type": "text", "data": {"text": "この画像を見てください："}},
    {"type": "image", "data": {"file": "https://example.com/image.png"}},
    {"type": "text", "data": {"text": "悪くないでしょう？"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)

# 位置情報メッセージ（標準 location セグメント → Matrix m.location；テキストと共存する場合は独立したイベントに分割）
ob12_msg = [
    {"type": "text", "data": {"text": "私はここにいます"}},
    {"type": "location", "data": {"latitude": 39.9, "longitude": 116.4, "title": "北京市"}}
]
await matrix.Send.To("group", room_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、await で直接送信結果を取得できます。戻り結果は ErisPulse アダプター標準化戻り値仕様に従います：

```python
{
    "status": "ok",           // 実行状態: "ok" または "failed"
    "retcode": 0,             // 戻りコード
    "data": {...},            // レスポンスデータ
    "message_id": "$event_id", // MatrixイベントID
    "message": "",            // エラーメッセージ
    "matrix_raw": {...}       // 生のレスポンスデータ
}
```

エラーコードの仕様については、前述の[標準化アラインメント](#標準化アラインメント)セクションを参照してください。

## 固有イベントタイプ

本プラットフォームの特性機能を使用するには、`platform=="matrix"` による判定が必要です

### コア差分ポイント

1. **分散型アーキテクチャ**：Matrix は分散型通信プロトコルで、ユーザーIDの形式は `@user:server.domain`、ルームIDの形式は `!room_id:server.domain` です
2. **ルーム概念**：Matrix はグループチャットとプライベートチャットを区別せず、すべてのセッションは「ルーム」です。アダプターは DM（Direct Message）アカウントデータによりプライベートチャットルームを自動識別します
3. **Long Polling 同期**：WebSocket ではなく `/sync` API によるロングポーリングで新イベントを取得します
4. **MXC URI**：メディアファイルは `mxc://server.domain/media_id` 形式で参照されます
5. **HTML リッチテキスト**：`formatted_body` による HTML 形式メッセージの送信に対応します
6. **絵文字リアクション**：メッセージレベルの絵文字リアクション（Reaction）に対応し、従来の返信メッセージとは異なります
7. **メッセージ編集**：`m.replace` 関係による送信済みメッセージの編集に対応します
8. **メッセージ取り消し**：`m.room.redaction` によるメッセージの取り消し/削除に対応します

### 拡張フィールド

- すべての固有フィールドは `matrix_` プレフィックスで識別されます
- 生データは `matrix_raw` フィールドに保持されます
- `matrix_raw_type` は元のMatrixイベントタイプを識別します（例：`m.room.message`、`m.room.member`）

### 特殊フィールド例

```python
# グループメッセージ
{
  "type": "message",
  "detail_type": "group",
  "user_id": "@user:matrix.org",
  "group_id": "!room_id:matrix.org",
  "matrix_room_id": "!room_id:matrix.org"
}

# プライベートチャットメッセージ
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

# メッセージ取り消し
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

Matrixメッセージは `msgtype` に基づいて自動的に対応するメッセージセグメントへ変換されます：

| msgtype | 変換タイプ | 説明 |
|---|---|---|
| m.text | `text` | テキストメッセージ |
| m.notice | `text` | 通知メッセージ |
| m.emote | `text` | アクションメッセージ |
| m.image | `image` | 画像メッセージ |
| m.audio | `audio` | オーディオメッセージ（標準メッセージセグメント名は `audio`；`voice` は送信メソッド名であり、セグメント名ではありません） |
| m.video | `video` | 動画メッセージ |
| m.file | `file` | ファイルメッセージ |
| m.location | `location` | 位置情報メッセージ（latitude/longitude は geo URI から解析） |

> メンション（mention）：メッセージ content 内の `m.mentions`（Matrix v1.11+ 仕様）は標準 `mention` セグメントに変換されます——
> `m.mentions.user_ids` → `mention(user_id=...)`、`m.mentions.room` → `mention(user_id="all")`。

メッセージセグメント構造例：

```json
// テキストメッセージ（HTML付き）
{
  "type": "text",
  "data": {
    "text": "プレーンテキスト内容",
    "html": "<b>HTMLコンテンツ</b>"
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

// 位置情報メッセージ（latitude/longitude は geo URI から解析）
{
  "type": "location",
  "data": {
    "latitude": 39.9,
    "longitude": 116.4,
    "matrix_geo_uri": "geo:39.9,116.4",
    "text": "北京市"
  }
}
```

### Event Mixin メソッド

MatrixAdapter は以下のイベント Mixin メソッドを登録しており、イベント処理内で直接呼び出せます：

| メソッド | 戻り値の型 | 説明 |
|------|----------|------|
| `get_room_id()` | `str` | ルームIDを取得 |
| `get_matrix_event_type()` | `str` | 元のMatrixイベントタイプを取得 |
| `get_matrix_sender()` | `str` | 元の送信者IDを取得 |
| `get_reaction_key()` | `str` | リアクションの絵文字を取得 |
| `is_edited()` | `bool` | メッセージが編集メッセージかどうかを判定 |
| `is_notice()` | `bool` | メッセージが m.notice タイプかどうかを判定 |

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

1. access_token または user_id + password で認証します
2. `/_matrix/client/v3/account/whoami` を呼び出して bot_user_id を取得します
3. connect メタイベントを発行します
4. 初期同期（`/_matrix/client/v3/sync?timeout=0`）を実行して `next_batch` token を取得します
5. DM ルームを検出します（`/_matrix/client/v3/user/{user_id}/account_data/m.direct`）
6. Long Polling 同期ループを開始します（`/_matrix/client/v3/sync?since={next_batch}&timeout=30000`）
7. 各同期で返された新イベントを処理し、変換して発行します

### ハートビートメカニズム

- アダプターは 30 秒ごとに `heartbeat` メタイベントを発行します
- 接続成功時に `connect` メタイベントを発行します
- 切断時に `disconnect` メタイベントを発行します

### ルーム招待

- ルーム招待（`invite` 状態のルーム）を受信した際、`auto_accept_invites` が `true`（デフォルト）に設定されている場合、アダプターは自動的にルームへ参加します
- ルームへの参加には `/_matrix/client/v3/join/{room_id}` API を呼び出します

## エンドツーエンド暗号化（E2EE）

アダプターは 4.3.0 から、暗号化ルームのエンドツーエンド暗号化（matrix-nio[e2e] / vodozemac ベース）をネイティブサポートし、`encryption_enabled = true` で有効化できます。

### 動作メカニズム

- **同期**：有効化後、同期は nio E2EE セッションを経由し、デバイスキーのアップロード、ワンタイムキーの補充、to-device メッセージ（Olm/Megolm セッションキー配布）はすべて自動処理されます；timeline 内の `m.room.encrypted` イベントは自動的に平文イベントへ復号され、その後統一変換が行われます
- **送信**：ターゲットルームが暗号化ルームの場合、自動的に Megolm セッションを共有してペイロードを暗号化します；復号に失敗したイベントはスキップされ、警告が記録されます
- **メディア**：暗号化ルームでのメディアアップロードはエンドツーエンド暗号化（`m.file.encrypted`）です；受信側のメディアセグメントには `matrix_encrypted_file`（JWK、url/key/iv/hashes を含む）が付与され、暗号文をダウンロードした後、`MatrixAdapter.decrypt_media(ciphertext, key, iv, sha256)` で復号できます
- **デバイス**：`device_id` は自動解析（ログインレスポンス → `/whoami` → ローカル永続化）され、パスワードでの再ログイン時は同一デバイスを再利用します；`trust_all_devices = true`（デフォルト）は未検証デバイスを自動信頼（bot シナリオでの慣例）、`false` は厳格モードです
- **フォールバック**：E2EE が無効または matrix-nio が未インストールの場合、自動的に平文 REST パスへフォールバックし、動作は旧版と完全に一致します

### モジュール側インターフェース

- イベント Mixin：`event.is_encrypted()` でメッセージが暗号化ルームからのものかを判定
- メディアセグメントフラグ：`encrypted: true` と `matrix_encrypted_file`（JWK）
- 復号ヘルパー：`MatrixAdapter.decrypt_media(file_bytes, key, iv, hash_value) -> bytes`

### 既知の制限

- クロス署名（cross-signing）とサーバー側キーバックアップ（room key backup）には対応していません
- ローカルセッション保存ディレクトリ（`store_path`、デフォルト `data/matrix/<アカウント名>`）を削除すると、過去のメッセージを復号できなくなります
- 対話式 SAS（絵文字）検証は現時点で未対応で、今後のバージョンで提供予定です

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
        # 絵文字リアクションを処理...
```

### メディアメッセージの送信

```python
# 画像の送信（URL）
await matrix.Send.To("group", room_id).Image("https://example.com/image.png")

# 画像の送信（MXC URI）
await matrix.Send.To("group", room_id).Image("mxc://matrix.org/abc123")

# 画像の送信（バイナリデータ）
with open("image.png", "rb") as f:
    image_bytes = f.read()
await matrix.Send.To("group", room_id).Image(image_bytes)

# 画像の送信（ローカルファイルパス）
await matrix.Send.To("group", room_id).Image("/path/to/image.png")

# ファイルの送信（ファイル名付き）
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
        # 編集メッセージを処理...
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
        print(f"ユーザー {user_id} が削除されました、操作者: {operator_id}")
```



### QQBot 适配

# QQBotプラットフォーム機能ドキュメント

QQBotAdapter は、QQ公式ボット（QQ OpenAPI）プロトコルに基づいて構築されたアダプターです。グループチャット、プライベートチャット、チャンネルなど全シナリオの機能を統合し、OneBot12 標準イベント、標準Apiアクション、リクエスト操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 5.3.3
- メンテナー: ErisPulse
- 最終更新: 2026-11-10

## 基本情報

- プラットフォーム概要：QQ公式ボット開発API、グループチャット、プライベートチャット、チャンネルなど多様なシナリオをサポート
- アダプター名：QQBotAdapter
- 接続方式：**WebSocket 常時接続**（デフォルト）または **Webhook HTTP コールバック**（アカウントごとの設定、Ed25519 署名検証）
- 認証方式：appId + clientSecret で access_token を取得（7200秒、45秒前に自動リフレッシュ）
- APIルートアドレス：`https://api.bot.qq.com`（v5 から公式統一ドメイン、sandbox は廃止）
- OneBot12互換：メッセージ送受信、イベント、**標準Apiアクション**、**リクエスト操作**を完全カバー
- マルチアカウント：対応、`accounts` 下の任意のアカウントを並列実行（websocket/webhook モードの混在可能）

## 設定説明

```toml
# config.toml
[QQBot_Adapter]
intents = "[0, 9, 12, 25, 26, 27]"   # グローバル：購読するイベントの intents（JSON配列、イベント名対応）

[QQBot_Adapter.accounts.default]
appid = "YOUR_APPID"                 # QQボットアプリケーションID（必須）
secret = "YOUR_CLIENT_SECRET"        # QQボットクライアントシークレット（必須）
mode = "websocket"                   # イベント受信方式：websocket / webhook
bot_id = ""                          # ボットID（空欄で自動取得；Using() での特定用に手動入力可）
gateway_url = ""                     # WebSocketゲートウェイアドレス（空欄の場合 /gateway/bot から動的取得）
api_base_url = "https://api.bot.qq.com"  # APIルートアドレス（プロキシ用にカスタマイズ可）
access_token_url = ""                # カスタムトークンAPI（空欄の場合は公式APIを使用）
webhook_path = "/webhook"            # Webhookコールバックパス（mode=webhook 時に有効）
enabled = true
```

**v5 破壊的変更：**
- `sandbox` フィールドは廃止されました：公式は `api.bot.qq.com` に統一されており、旧設定の sandbox は自動的に移行されて無視されます（警告を出力）
- 旧版のフラット設定（`[QQBot_Adapter]` の下に直接 appid/secret を記述）は自動的に `accounts.default` へ移行されます
- フレームワークは**ソフト依存**です：アダプターのインストールでフレームワークバージョンは引き上げられません；実行時に `ErisPulse>=2.7.1` を検出して通知します

**intents の説明（ビット番号またはイベント名をサポート）：**

| ビット | イベント名 | 説明 |
|----|--------|------|
| 0 | GUILDS | チャンネル変更 |
| 1 | GUILD_MEMBERS | チャンネルメンバー変更 |
| 9 | GUILD_MESSAGES | チャンネルメッセージ（プライベートドメインは審査必要） |
| 10 | GUILD_MESSAGE_REACTIONS | チャンネルメッセージリアクション |
| 12 | DIRECT_MESSAGE | チャンネルDM |
| 24 | GROUP_MEMBER | グループメンバー変更（**v5新規**） |
| 25 | GROUP_AND_C2C_EVENT | グループ@メッセージとプライベートチャットメッセージ |
| 26 | INTERACTION | インタラクションイベント（ボタンなど） |
| 27 | MESSAGE_AUDIT | メッセージ審査イベント |
| 28 | FORUMS_EVENT | フォーラムイベント（プライベートドメインのみ） |
| 29 | AUDIO_ACTION | オーディオ操作 |
| 30 | PUBLIC_GUILD_MESSAGES | チャンネルメッセージ（パブリックドメイン） |

```toml
# 2つの書き方は等価
intents = "[0, 9, 12, 25, 26, 27]"
intents = '["GUILDS", "GUILD_MESSAGES", "DIRECT_MESSAGE", "GROUP_AND_C2C_EVENT", "INTERACTION", "MESSAGE_AUDIT"]'
```

## 標準化アラインメント

本セクションでは、アダプターと ErisPulse 標準化仕様に準拠した動作について説明します。仕様の詳細は、SDK ドキュメントの『リクエスト操作仕様』（`docs/ja/standards/request-action-spec.md`）および『API レスポンス仕様』（`docs/ja/standards/api-response.md`）を参照してください。

### エラーコードの標準化（5.3.x）

- **プラットフォームエラーは統一して 34100**：QQ公式 API がエラーを返した場合は `retcode=34100` を返し、元のレスポンス（公式の `code`/`message` を含む）は `qqbot_raw` フィールドに保持されます（メディアアップロード失敗も同様に 34100 を使用）
- **タイムアウトは 33001**：API 呼び出しのタイムアウトは `retcode=33001` を返します（旧 32000 は使用されません）
- **撤回コンテキスト欠落は 10003**：`delete_message` でメッセージの帰属コンテキストが見つからない場合は `retcode=10003` を返します（パラメータエラー）
- **リクエスト系は 34001/34003 を維持**：リクエストが存在しないまたは期限切れの場合は `34001` を返します；リクエストコンテキストにルーティングパラメータが欠落している場合は `34003` を返します

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 10001 | パラメータ欠落/エンドポイントが空 |
| 10002 | サポートされていないアクション |
| 10003 | 送信先/アカウントを特定できない、撤回コンテキスト欠落などのパラメータエラー |
| 33000 | ネットワーク/API呼び出し異常 |
| 33001 | リクエストタイムアウト |
| 34001 | リクエストが存在しないまたは期限切れ（Request DSL） |
| 34003 | リクエストコンテキストにルーティングパラメータが欠落（Request DSL） |
| 34100 | プラットフォームビジネスエラー（元のレスポンスと公式 code は `qqbot_raw` に保持） |

### 通知イベントの命名（5.3.x）

フレンド追加・削除の通知イベントは標準命名に統一されました：

| 公式イベント | 変換後の detail_type | 説明 |
|----------|-------------------|------|
| FRIEND_ADD | `friend_increase` | フレンド追加（旧 `friend_add` は廃止） |
| FRIEND_DEL | `friend_decrease` | フレンド削除（旧 `friend_del` は廃止） |

### リクエストコンテキストの保持（5.3.2 以降）

グループ参加申請イベントのエントリは、`request_id` を申請コンテキスト（グループ/申請者 openid）にマッピングしてキャッシュします（TTL 3600 秒、上限 512 件、リクエスト処理成功後にクリア）。承認実行時は `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}` にルーティングされます。

### 拡張アクションのルーティング（5.3.x）

チャンネルメンバー権限の照会は、プラットフォームプレフィックス付きの拡張アクションを通じて提供されます：

```python
result = await qqbot.Api.call("qqbot.get_channel_member_permissions", channel_id="...", member_id="...")
```

### Stream 送信の send_context 読み取り

ストリーミングメッセージ（`.Stream()`）は `send_context` を読み取ります：イベントチェーン内では現在のイベント発生源アカウントを自動的に使用し、明示的に `Using()` で指定されたアカウントが優先されます。

## メッセージ送信

### 基本送信

```python
from ErisPulse import sdk
qqbot = sdk.adapter.get("qqbot")

# テキストを送信
await qqbot.Send.To("user", user_openid).Text("Hello World!")

# グループチャット@メッセージ（自動的に <qqbot-at-user id="x" /> 形式を使用）
await qqbot.Send.To("group", group_openid).At("member_openid").Text("@あなた")
await qqbot.Send.To("group", group_openid).AtAll().Text("お知らせ")

# チャンネルメッセージ（@ は自動的に <@user_id> 形式を使用）
await qqbot.Send.To("channel", channel_id).Text("チャンネルメッセージ")

# チャンネルDM（先にセッションを作成）
dms = await qqbot.create_dms(user_id, source_guild_id)
await qqbot.Send.To("dms", dms["data"]["guild_id"]).Text("DM")

# メッセージへの返信（パッシブ返信、自動的に msg_id を付与）
await qqbot.Send.To("group", group_openid).Reply(msg_id).Text("返信内容")

# マルチアカウント（Using/Account でアカウント名または bot_id を指定）
await qqbot.Send.Using("account2").To("group", group_openid).Text("2つ目のボットからの送信")
```

### リッチメディア

```python
# URL / ローカルパス / バイナリの3方式をサポート；5MB超過時は自動分割アップロード
await qqbot.Send.To("group", gid).Image("https://example.com/img.png")
await qqbot.Send.To("user", uid).Image("/path/to/local.png")
await qqbot.Send.To("user", uid).Voice(open("audio.mp3", "rb").read())
await qqbot.Send.To("user", uid).Video("https://example.com/v.mp4")
await qqbot.Send.To("user", uid).File(b"...", filename="doc.pdf")

# チャンネル画像は multipart ダイレクトアップロード（file_image）
await qqbot.Send.To("channel", cid).Image(open("img.png", "rb").read())
```

`file_type` のマッピング：画像=1、動画=2、音声=3、ファイル=4（メッセージセグメントタイプから自動判定、`file` セグメントは拡張子から推測）。

### Markdown / Ark / Embed / Keyboard

```python
# ネイティブ Markdown
await qqbot.Send.To("group", gid).Markdown("# タイトル\n- リスト項目")

# テンプレート Markdown
await qqbot.Send.To("user", uid).Markdown(template_id=1, kv=[{"key": "title", "value": "通知"}])
await qqbot.Send.To("user", uid).Markdown(custom_template_id="23456", kv=[...])

# Ark テンプレート
await qqbot.Send.To("user", uid).Ark(23, [{"key": "a", "value": "b"}])

# Embed（チャンネル/チャンネルDMのみ）
await qqbot.Send.To("channel", cid).Embed({"title": "タイトル", "content": "内容"})

# キーボード（自動的に markdown タイプに設定され bot_appid を付与）
keyboard = {"content": {"rows": [[{"label": "確認", "type": 2, "data": "ok"}]]}}
await qqbot.Send.To("group", gid).Keyboard(keyboard).Text("選択してください")

# 一括転送（公式 md には折りたたみ構文がないため引用リストとしてレンダリング；ネイティブ Markdown 権限が必要、失敗時は自動的にプレーンテキストへフォールバック）
await qqbot.Send.To("group", gid).MergeForward(nodes)
```

### ストリーミングメッセージ（v5 新規、1対1チャット）

```python
# 単発のストリーミング送信（input_state=10 で直接完了）
await qqbot.Send.To("user", openid).Stream("回答内容")

# 複数回追記のストリーミング
r = await qqbot.stream_message(openid, "1つ目の部分", input_state=1, msg_id=パッシブmsg_id)
stream_id = r["data"]["id"]
r = await qqbot.stream_message(openid, "2つ目の部分", stream_msg_id=stream_id, index=1, input_state=1)
r = await qqbot.stream_message(openid, "最後の部分", stream_msg_id=stream_id, index=2, input_state=10)
```

### メッセージの撤回

```python
# 標準 Api アクション：メッセージの発生源（グループ/プライベートチャット/チャンネル/DM）に応じて自動的に対応する撤回エンドポイントへルーティング
await qqbot.Api.delete_message(message_id)
```

アダプターは送受信メッセージの帰属先を自動的に登録するため、group_id/channel_id を手動で渡す必要はありません；コンテキストが欠落している場合は `retcode=10003` を返します。

## OneBot12 標準Apiアクション（v5 新規）

```python
# ボット情報
result = await qqbot.Api.get_self_info()

# グループ管理
result = await qqbot.Api.get_group_info(group_openid)          # {group_id, group_name}
result = await qqbot.Api.get_group_member_list(group_openid)   # 自動ページング集約
result = await qqbot.Api.get_group_member_info(group_openid, member_openid)

# チャンネル
result = await qqbot.Api.get_guild_list()
result = await qqbot.Api.get_guild_info(guild_id)
result = await qqbot.Api.get_guild_member_list(guild_id)
result = await qqbot.Api.get_channel_list(guild_id)
result = await qqbot.Api.get_channel_info(guild_id, channel_id)
await qqbot.Api.set_channel_name(guild_id, channel_id, "新しい名前")
await qqbot.Api.leave_channel(guild_id, channel_id)            # サブチャンネルを削除

# メタアクション
result = await qqbot.Api.get_status()   # {"good": bool, "bots": [...]}
result = await qqbot.Api.get_version()  # {"impl": "ErisPulse-QQBotAdapter", "onebot_version": "12"}

# マルチアカウント
result = await qqbot.Api.Using("account2").get_self_info()
```

サポートされている標準アクション：`get_self_info` / `get_group_info` / `get_group_member_info` / `get_group_member_list` / `get_guild_info` / `get_guild_list` / `get_guild_member_info` / `get_guild_member_list` / `get_channel_info` / `get_channel_list` / `set_channel_name` / `leave_channel` / `delete_message` / `get_status` / `get_version` / `get_supported_actions`。サポートされていないアクションは `retcode=10002` を返します（例：`get_friend_list`。QQ公式に対応するAPIがないため）。

## リクエスト操作（Request DSL、v5 新規）

`GROUP_JOIN_REQUEST`（グループ参加申請）イベントは、1対1インタラクションの `request` イベントに変換され、標準化された承認をサポートします：

```python
from ErisPulse.Core.Event import request as request_event

@request_event.on_request()
async def handle_join_request(event):
    if event.get("platform") != "qqbot":
        return
    # 自動承認
    result = await event.approve()
    # または拒否：await event.reject(comment="条件を満たしていません")
    # またはアカウント指定：await qqbot.Request(event["request_id"]).Using("account2").accept()
```

- `request_id` = 公式 `join_request_id`
- アダプターは申請コンテキスト（グループ/申請者 openid）を自動的にキャッシュし、実行時は `POST /v2/groups/{group_openid}/approval_join_request/{member_openid}` にルーティングします
- 拒否には `reject_reason` を付与できます；コンテキストが期限切れの場合は `retcode=34001` を返します

プラットフォームメソッドを直接呼び出すこともできます：

```python
await qqbot.approve_group_join(group_openid, member_openid, join_request_id, approve=True)
await qqbot.approve_group_join(group_openid, member_openid, approve=False, reject_reason="理由")
```

## プラットフォームネイティブAPIメソッド群

アダプターは完全な QQ 公式 API を公開しています（第1引数は多くの場合ターゲットID、`account_id` でアカウントを任意指定可能）：

### ボット / インタラクション
`get_me()`、`reply_interaction(interaction_id, code=0)`

### チャンネル（Guild）
`get_guilds()`、`get_guild(guild_id)`、`mute_guild_all(guild_id, mute_seconds)`、
`get_guild_roles` / `create_guild_role` / `update_guild_role` / `delete_guild_role`、
`get_guild_api_permission`、`demand_guild_api_permission(guild_id, channel_id, path, method, desc)`

### サブチャンネル（Channel）
`get_channels`、`get_channel`、`create_channel(guild_id, name, type=0, ...)`、`update_channel(channel_id, name=..., ...)`、`delete_channel`、
`get_channel_pins`、`pin_message`、`unpin_message`

### チャンネルメンバー
`get_guild_members`、`get_guild_member`、`mute_guild_members`（一括/全チャンネル）、`mute_guild_member`、
`add_guild_member_role` / `remove_guild_member_role`、`kick_guild_member`

### 権限 / お知らせ / リアクション
`get_channel_role_permissions`、`update_channel_role_permissions`、`get_channel_member_permissions`（拡張アクション `qqbot.get_channel_member_permissions`）、`update_channel_member_permissions`、`create_announce`、
`add_reaction`、`delete_reaction`、`get_reaction_users`

### スケジュール / スレッド / オーディオ
`get_schedules`、`get_schedule`、`create_schedule`、`update_schedule`、`delete_schedule`、
`get_threads`、`get_thread`、`publish_thread(channel_id, title, content, format=3)`、`delete_thread`、
`control_audio(channel_id, audio_url, text, status)`、`mic_online`、`mic_offline`

### グループ管理（v2、**一部のAPIはホワイトリストボットのみ開放**）
```python
await qqbot.get_group_info_raw(group_openid)          # グループ情報
await qqbot.get_group_bot_state(group_openid)         # グループ内のボット状態
await qqbot.get_group_members(group_openid)           # メンバーリスト（next_cursor を含む）
await qqbot.get_group_member(group_openid, member_openid)
await qqbot.batch_remove_group_members(group_openid, [member_openid], add_to_blacklist=False)
await qqbot.get_group_member_blacklist(group_openid)
await qqbot.update_group_member_blacklist(group_openid, "add", [member_openid])
await qqbot.get_group_join_requests(group_openid)     # 参加申請リスト
await qqbot.approve_group_join(...)                   # 参加申請の承認
await qqbot.get_group_restrict_setting(group_openid)  # ミュート設定
await qqbot.set_group_restrict(group_openid, [{"op": "add", "member_openid": "...", "mute_expire_at": 123}])
# 参加承認ポリシー
await qqbot.get_join_approval_strategies()
await qqbot.create_join_approval_strategy(strategy_dict)
await qqbot.update_join_approval_strategy(strategy_id, **fields)
await qqbot.delete_join_approval_strategy(strategy_id)
await qqbot.execute_join_approval_strategy(strategy_id)
await qqbot.update_join_approval_strategy_whitelist(strategy_id, "add", [user_ids])
```

### カスタムメニュー / コマンドパネル（v5 新規）
```python
# グローバルカスタムメニュー（C2C のみ有効；サブメニューは最大5項目、ネスト不可）
menu_items = [
    {"type": "send_message", "content": {"label": "ヘルプ", "content": "/help"}},
    {"type": "link", "content": {"label": "公式サイト", "content": "https://example.com"}},
]
await qqbot.update_custom_menu(menu_items)
result = await qqbot.get_custom_menu()

# コマンドパネル（scope: c2c/group/channel/dm；ボットごとに最大20個）
await qqbot.create_command_panel("c2c", [
    {"type": "command", "content": {"label": "天気照会", "content": "/weather"}},
    {"type": "link", "content": {"label": "もっと見る", "content": "https://example.com"}},
], remark="パネルの備考", target_type="all")
await qqbot.get_command_panels("c2c")
await qqbot.get_command_panel(panel_id)
await qqbot.update_command_panel(panel_id, items)
await qqbot.delete_command_panel(panel_id)
await qqbot.update_command_panel_targets(panel_id, "add", user_openids=[...])
```

## WebSocket 接続

### 接続フロー

1. appId + clientSecret で access_token を取得（`POST https://bots.qq.com/app/getAppAccessToken`）
2. `GET /gateway/bot` によりゲートウェイアドレスを動的取得（`gateway_url` 設定時はそれを直接使用）
3. OP_HELLO（op=10）を受信し、ハートビート間隔を取得
4. OP_IDENTIFY（op=2）を送信して認証（intents はビット演算による組み合わせをサポート）
5. READY を受信して session_id と bot_id を取得し、connect meta イベントを送信
6. ハートビートループ（op=1）とイベントディスパッチ（op=0）

### 切断時の再接続

- 最大再接続 50 回、指数バックオフ `min(5 * 2^n, 300)` 秒
- OP_RECONNECT（op=7）受信時はセッションを保持（Resume）；OP_INVALID_SESSION（op=9）の場合は再 Identify
- 送受信が正常な場合は再接続カウントを自動的にリセット

### Token 管理

- access_token の有効期限は 7200 秒、**45秒前に自動リフレッシュ**（リクエスト時の遅延チェック）
- リフレッシュ失敗時は自動的に 3 回リトライ（遅延を増加させながら）
- リクエストヘッダー：`Authorization: QQBot {token}` + **`X-Union-Appid: {appid}`**（v5 新規）

## Webhook 接入（v5 新規）

アカウントの `mode` を `webhook` に設定するだけで、HTTP コールバックでイベントを受信するように変更できます：

```toml
[QQBot_Adapter.accounts.mybot]
appid = "..."
secret = "..."
mode = "webhook"
webhook_path = "/webhook"    # 複数の webhook アカウントがある場合は競合回避のため自動的にアカウント名を追加
```

- アダプターは ErisPulse router を通じて HTTP ルートを登録し、起動ログに完全なコールバック URL が出力されます
- **Ed25519 署名検証**：シード = secret を 32 バイトまで循環埋め込み；`X-Signature-Ed25519` による `X-Signature-Timestamp + body` の署名を検証
- op=13 署名検証ハンドシェイク（コールバックアドレス設定の検証）と op=0 イベントディスパッチを自動処理
- `cryptography` ライブラリに依存（アダプターと共にインストール済み）

## イベント購読と openid 体系

1. QQBot は QQ番号ではなく openid 体系を使用し、ユーザー/グループの識別子はすべて openid 文字列です
2. グループメッセージはデフォルトで、ユーザーがボットを@した場合にのみ受信します（`GROUP_AT_MESSAGE_CREATE`）
3. **すべてのグループメッセージを受信**：[QQオープンプラットフォーム](https://q.qq.com/) のボット管理画面で該当する権限を有効にする必要があります（API では設定できません）；有効化後、非@グループメッセージは `GROUP_MESSAGE_CREATE` でプッシュされ、アダプターは変換を完全にサポートしています（`qqbot_is_at_message=false` とマーク；メッセージ内にボットへの@マークが含まれる場合は自動的に@メッセージとして認識されます）
4. **@検出**：QQ の「被@」はイベント名によって表現され、グループメッセージの @ マークは `<@{グループスペースopenid}>`（READY bot_id とは異なる id 体系）です。アダプターは両方のマークスタイルを自動解析し、ボットの mention セグメントを注入/正規化することで `on_at_message()`/`is_at_message()` を利用可能にします；同時に、各グループにおけるボットの openid を自動学習し、「すべてのグループメッセージを受信」モードの `GROUP_MESSAGE_CREATE` 内の@メッセージも認識できるようにします（元の openid は mention セグメントの `data.qqbot_openid` に保持されます）
5. パッシブ返信：グループ/プライベートチャットメッセージには `msg_id` または `event_id` が必要で、アダプターが自動的にキャッシュして付与します
6. `event_id` はリッチメディアと混在して送信できません（公式制限）。アダプターは自動的にダウングレード処理します
7. 送信は審査をトリガーする場合があり、結果は `qqbot_audit_pass` / `qqbot_audit_reject` イベントで通知されます
8. プログラム終了時は `shutdown()` を呼び出してリソースを解放します

## 使用例

### グループメッセージの処理（@検出）

```python
from ErisPulse.Core.Event import message

@message.on_at_message()
async def handle_at(event):
    if event.get("platform") != "qqbot":
        return
    text = event.get_text()
    if text == "チェックイン":
        await event.reply("チェックインしました")
```

### ボタンインタラクションの処理

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("detail_type") != "qqbot_interaction":
        return
    button_id = event.get("qqbot_button_id")
    await qqbot.reply_interaction(event.get("qqbot_interaction_id"), code=0)
    if button_id == "confirm":
        await qqbot.Send.To("group", event.get("group_id")).Text("確認しました")
```

### マルチアカウント起動

```toml
[QQBot_Adapter.accounts.bot_a]
appid = "A_APPID"
secret = "..."
enabled = true

[QQBot_Adapter.accounts.bot_b]
appid = "B_APPID"
secret = "..."
mode = "webhook"
enabled = true
```

2つのアカウントが並列に起動します：bot_a は WebSocket 経由、bot_b は Webhook 経由で、互いに影響しません。



### 云湖用户端适配

# 云湖用户平台特性文档

YunhuUserAdapter は、云湖用户账户协议に基づき構築されたアダプタです。ユーザーのメールアドレスアカウントを使用してログインし、WebSocket を介してイベントを受信し、一貫したイベント処理とメッセージ操作のインターフェースを提供します。

---

## 文書情報

- 対応モジュールバージョン: 4.6.1
- 維持者: wsu2059
- 最終更新: 2026-11-10

## 基本情報

- プラットフォーム概要：云湖（Yunhu）は企業向けのリアルタイムコミュニケーションプラットフォームです。本アダプタは**ユーザーアカウント**（ロボットアカウントではなく）を使用して対話します。
- アダプタ名: YunhuUserAdapter
- 複数アカウント対応: アカウント名で識別可能な複数のユーザーアカウントを設定できます。
- チェーン修飾子対応: `.Reply()` などのチェーン修飾子メソッドをサポート。
- OneBot12互換: OneBot12形式のメッセージ送信をサポート。
- 通信方式: メールアドレスでログインし、token を取得し、WebSocket を使用してイベントを受信し、HTTP + Protobuf 協定でメッセージを送信。
- 会話タイプ: プライベートチャット（user）、グループチャット（group）、ロボット会話（chat_type=3、4.6.1から `private` にマッピング）をサポート。

## v5 ファンタム更新（4.2.0）

- **BaseConverter 継承**；**spawn_background タスクの所属**（WS 監視タスク）
- **ユーザーAPI全集**（yhchatAPI full.proto / v1 エンドポイント、protobuf over HTTP を使用）：
  - ユーザー：get_user / edit_nickname / edit_avatar
  - 友人：アドレスブック / 申請リスト / 申請 / 承認 / 無視 / 削除
  - グループ：グループ情報 / メンバー一覧 / 作成 / 解散 / 招待 / 除外 / 禁言 / ロボット一覧
  - 会話：会話一覧；メッセージ：一覧 / 撤回 / ボタン報告
- **フレームワークソフト依存**：ErisPulse>=2.7.1 の実行時検出と警告表示；起動時にバージョンログを出力

## 対応プラットフォーム機能リスト

### イベント受信（WebSocket、protobuf エンコード）

| WS cmd | イベント | 説明 |
|--------|--------|------|
| `push_message` | `message` | プライベートチャット/グループ/Bot 会話メッセージ（テキスト/HTML/Markdown/画像/動画/音声/ファイル/絵文字/フォーム/記事/ステッカー/ボタン/A2UI） |
| `edit_message` | `notice` (`message_edit`) | メッセージ編集通知 |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | スーパーファイル共有 |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | ロボット公告ボード |

### Api DSL メソッド対照表（ YunhuHTTPClient → ユーザーAPI v1 エンドポイント ）

| 分類 | Api メソッド | エンドポイント | 説明 |
|------|-------------|---------------|------|
| アカウント | `get_self_info()` | `/user/info` | ログインユーザー情報（ニックネーム/プロフィール画像/user_id） |
| ユーザー | `get_user(user_id)` | `/user/get-user` | ユーザーの詳細情報 |
| ユーザー | `edit_nickname(nickname)` | `/user/edit-nickname` | 自分のニックネームを変更 |
| ユーザー | `edit_avatar(url)` | `/user/edit-avatar` | 自分のプロフィール画像を変更 |
| 友人 | `get_friend_address_book(md5)` | `/friend/address-book-list` | アドレスブック（カーソル付きページング） |
| 友人 | `get_friend_requests()` | `/friend/request-list` | 友人/グループ参加申請リスト |
| 友人 | `friend_apply(user_id, desc)` | `/friend/apply` | 友人追加申請 |
| 友人 | `friend_agree_apply(user_id)` | `/friend/agree-apply` | 友人申請を承認 |
| 友人 | `friend_ignore_apply(user_id)` | `/friend/ignore-apply` | 友人申請を無視 |
| 友人 | `friend_delete(user_id)` | `/friend/delete-friend` | 友人を削除 |
| グループ | `get_group_info(group_id)` | `/group/info` | グループ情報 |
| グループ | `get_group_member_list(group_id)` | `/group/list-member` | グループメンバー一覧（キーワード検索対応） |
| グループ | `create_group(name, ...)` | `/group/create-group` | グループ作成 |
| グループ | `dismiss_group(group_id)` | `/group/dismiss-group` | グループ解散 |
| グループ | `group_invite(group_id, user_ids)` | `/group/invite` | グループに招待 |
| グループ | `group_remove_member(group_id, user_id)` | `/group/remove-member` | グループメンバーを除外 |
| グループ | `group_gag_member(group_id, user_id, 秒)` | `/group/gag-member` | グループメンバーを一時停止（0=解除） |
| グループ | `get_group_bot_list(group_id)` | `/group/bot-list` | グループ内のロボット一覧 |
| 会話 | `get_conversation_list(md5)` | `/conversation/list` | 会話一覧（カーソル付きページング） |
| メッセージ | `get_message_list(chat_id, chat_type, ...)` | `/msg/list-message` | メッセージ一覧（HTTP クライアントのページング変体参照） |
| メッセージ | `delete_message(msg_id, chat_id, chat_type)` | `/msg/recall-msg` | メッセージ撤回（バッチ撤回は HTTP クライアント参照） |
| メッセージ | `button_report(...)` | `/msg/button-report` | ボタンクリック報告 |
| メタアクション | `get_status` / `get_version` / `get_supported_actions` | - | 実行状態/バージョン/サポートアクション |

### 未対応（エンドポイントは既知、full.proto メッセージは完全、必要に応じて拡張可能）

- ユーザー：認証コードログイン、バッジ、金豆記録、電話番号/メールアドレスの紐付け、通知設定、ユーザーデータの保存と取得
- 友人：ノーノイズ（no-notify）、申請記録の削除
- グループ：コマンドリスト、分類、おすすめ、ライブ配信、グループ情報/グループニックネーム/キーワードの編集、グループ参加の自動承認、グループファイル制限、イベント SSE
- 会話：固定/並べ替え/削除、ノーノイズ
- メッセージ：転送、A2UIの提出、メッセージ一覧の画像取得、ファイルのダウンロード記録
- グループタグ：list / relate / relate-cancel / create / edit / delete / members（エンドポイント `/group-tag/*`）

> 拡張方法：`YunhuHTTPClient` に既存のパターンに従ってメソッドを追加する（`_proto_request` / `_json_request` は共通のラッパー）、`Api` クラスで公開するだけ。エンドポイントとメッセージ定義は `yhchatAPI/src/api/v1/*.md` と `yhchatAPI/src/full.proto` を参照。

### ユーザーAPIの例

```python
from ErisPulse import sdk
yunhu_user = sdk.adapter.get("yunhu_user")

result = await yunhu_user.Api.get_self_info()
result = await yunhu_user.Api.get_friend_requests()          # 友人申請リスト
await yunhu_user.Api.friend_agree_apply(user_id)             # 友人申請を承認
result = await yunhu_user.Api.get_group_member_list(group_id)
result = await yunhu_user.Api.get_conversation_list()        # 会話リスト
await yunhu_user.Api.delete_message(msg_id, chat_id, chat_type)  # 撤回
```

## 友人申請処理（4.6.0 新規追加）

云湖ユーザーのWebSocketは**友人申請イベントをプッシュしません**。アダプタはデフォルトで申請リストをポーリングし、標準リクエストイベントに合成します（[リクエスト操作規範](../standards/request-action-spec.md)に従います）：

- **アカウント設定**：`poll_friend_requests = true`（デフォルトで有効）、`poll_interval = 60`（ポーリング間隔秒、最小5秒）；`false`に設定するとポーリングを無効にできます
- **ポーリングロジック**：`/friend/request-list`を間隔で取得し、**新規申請**を差分で合成し、標準リクエストイベントに変換します：
  - `type="request"`、`detail_type="friend"`
  - `request_id` = **申請者の user_id**
  - `user_nickname` / `comment` は申請資料から取得し、元の項目は `yunhu_user_raw` に保持されます
- **イベントの重複除去**：処理済みの申請は重複してイベントを生成しません

### モジュール側の承認（イベント方式）

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    if event.get("platform") != "yunhu_user":
        return

    applicant = event.get("user_id")
    nickname = event.get("user_nickname", "")
    comment = event.get("comment", "")
    print(f"友人申請: {nickname}({applicant}) 附言: {comment}")

    # 友人申請を承認（accept = 友人追加）
    await event.approve()
    # または申請を無視（reject = 無視）
    # await event.reject()
```

### 直接アダプタを呼び出す（Request DSL）

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# request_id は申請者の user_id
await yunhu_user.Request("申请人user_id").accept()   # accept = 友人追加
await yunhu_user.Request("申请人user_id").reject()   # reject = 無視

# 複数アカウント：アカウントを指定して承認
await yunhu_user.Request("申请人user_id").Using("default").accept()
```

> `accept()` は内部で `/friend/agree-apply` を呼び出し、`reject()` は `/friend/ignore-apply` を呼び出します。両方とも `status` / `retcode` / `message` / `yunhu_user_raw` の標準レスポンスを返します。

## 標準化の一致（4.6.1）

レスポンス構造とエラーコードは[APIレスポンス規格](../standards/api-response.md)に従います。

### 標準レスポンス

Api DSL 20のメソッドはすべて、`status` / `retcode` / `data` / `message_id` / `message` の標準レスポンスを返します。プラットフォームの元のデータは `data` と `yunhu_user_raw` に含まれます。`get_self_info` の元のデータはレスポンスの最上位に移動されます。

### エラーコード規格

| retcode | 含義 | 说明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | 網絡エラー | HTTP/WS接続エラー |
| 34100 | プラットフォーム失敗 | 云湖ユーザー端末が失敗した；元のレスポンスは `yunhu_user_raw` に保持されます |
| 10002 | 不支持 | プラットフォームが対応する標準アクションをサポートしていません |
| 10003 | パラメータエラー | request_id、利用可能なアカウントが不足しています |

### イベントフィールド修正

- **`chat_type=3`（ロボット会話）は `private` にマッピング**（元の `"bot"` は非標準受信タイプ；元の chat_type は `yunhu_user_raw` に保持されます）
- **`edit_message` イベントの id に `edit:` プレフィックスを追加**：create イベントと同じ id で下流の重複除去処理に飲み込まれないようにします
- **`message_id` は常に存在します**：存在しない場合は空文字列で補填します
- **イベント `time` はメッセージ自身のタイムスタンプを使用**（秒単位）、アダプタ処理時刻を一律に使用しません

### アカウントと複数アカウント

- `call_api` は `account_id`（標準名）/ `_account_id`（旧名）の両方のアカウントフィールドをサポートし、フレームワーク ApiDSL（`Api.Using(...)`）は自動的に適応します
- `Send` は `send_context`（イベントアカウントのバックアップ）を読み取ります：イベントコンテキストから `Send` を呼び出す場合、デフォルトで元のアカウントにフォールバックします
- イベントの返信は `event.reply()` を直接使用することを推奨し、受理アカウントに自動ルーティングされます

---

## 対応するメッセージ送信タイプ

すべての送信メソッドはチェーン式構文で実現されます。例えば：
```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

await yunhu_user.Send.To("user", user_id).Text("Hello World!")
```

対応する送信タイプは以下の通りです：
- `.Text(text: str, buttons: Optional[List] = None)`：テキストメッセージを送信します。
- `.Html(html: str, buttons: Optional[List] = None)`：HTML形式のメッセージを送信します。
- `.Markdown(markdown: str, buttons: Optional[List] = None)`：Markdown形式のメッセージを送信します。
- `.MergeForward(nodes, title="合併チャット記録")`：合併転送メッセージを送信します（`<details>`折りたたみHTMLカードとしてレンダリングされ、msg_type=8 HTMLチャネルで送信されます）。
- `.Image(file: Union[str, bytes], buttons: Optional[List] = None)`：画像メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Video(file: Union[str, bytes], buttons: Optional[List] = None)`：動画メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Audio(file: Union[str, bytes], buttons: Optional[List] = None)`：音声メッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートし、自動的に音声長を検出します。
- `.Voice(file: Union[str, bytes], buttons: Optional[List] = None)`：`.Audio()`の別名です。
- `.File(file: Union[str, bytes], file_name: Optional[str] = None, buttons: Optional[List] = None)`：ファイルメッセージを送信します。URL、ローカルパス、またはバイナリデータをサポートします。
- `.Face(file: Union[str, bytes], buttons: Optional[List] = None)`：絵文字/ステッカーメッセージを送信します。ステッカーID、ステッカーURL、またはバイナリ画像データをサポートします。
- `.A2ui(a2ui_data: Union[str, Dict, List], buttons: Optional[List] = None)`：A2UIメッセージを送信します（msg_type=14）。A2UI JSONデータはtextフィールドに埋め込まれて送信されます。
- `.Edit(msg_id: str, text: str, content_type: str = "text")`：既存のメッセージを編集します。
- `.Recall(msg_id: str)`：メッセージを撤回します。
- `.Raw_ob12(message: Union[List, Dict])`：OneBot12形式のメッセージを送信します。

### メディアファイル処理

すべてのメディアタイプ（画像、動画、音声、ファイル）は以下の入力方式をサポートします：
- **URL**：`"https://example.com/image.jpg"` — 自動的にダウンロードしてアップロードします
- **ローカルパス**：`"/path/to/file.jpg"` — 自動的に読み取ってアップロードします
- **バイナリデータ**：`open("file.jpg", "rb").read()` — 直接アップロードします

メディアファイルは自動的に七牛云ストレージにアップロードされ、以下の特徴を備えています：
- 自動的に `filetype` ライブラリを使用してファイルタイプとMIMEを検出します
- 自動的にファイルサイズを計算します
- 音声ファイルはMP3、MP4/M4A形式を自動的に検出します

### ボタンパラメータの説明

`buttons` パラメータは、ボタンのレイアウトと機能を示すネストされたリストです。各ボタンオブジェクトには以下のフィールドがあります：

| フィールド         | タイプ   | 必須 | 説明                                                                 |
|--------------------|----------|------|----------------------------------------------------------------------|
| `text`             | string   | はい | ボタンのテキスト                                                     |
| `actionType`       | int      | はい | アクションタイプ：<br>`1`: URLに移動<br>`2`: コピー<br>`3`: クリック報告 |
| `url`              | string   | いいえ | `actionType=1` の場合、移動先のURLを使用します                         |
| `value`            | string   | いいえ | `actionType=2` の場合、この値がクリップボードにコピーされます<br>`actionType=3` の場合、この値がサブスクライバーに送信されます |

例：
```python
buttons = [
    [
        {"text": "コピー", "actionType": 2, "value": "xxxx"},
        {"text": "クリックして移動", "actionType": 1, "url": "http://www.baidu.com"},
        {"text": "イベントを報告", "actionType": 3, "value": "xxxxx"}
    ]
]
await yunhu_user.Send.To("user", user_id).Buttons(buttons).Text("ボタン付きメッセージ")
```

### チェーン修飾子メソッド（組み合わせて使用可能）

チェーン修飾子メソッドは `self` を返し、チェーン呼び出しをサポートします。最終的な送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定されたメッセージに返信します。
- `.At(user_id: str)`：指定されたユーザーを@します（テキスト形式 @user_id）。
- `.AtAll()`：全員を@します（偽@全員、@all テキストを送信します）。
- `.Buttons(buttons: List)`：ボタンを追加します。

> **注意：** ユーザーアカウントは特別なため、管理者でなくても全員を@できますが、`AtAll()` は@全員のテキストを送信するだけです。

### チェーン呼び出しの例

```python
# 基本的な送信
await yunhu_user.Send.To("user", user_id).Text("Hello")

# メッセージへの返信
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Text("返信メッセージ")

# 返信 + ボタン
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Buttons(buttons).Text("返信とボタン付きメッセージ")

# 指定アカウント + 返信 + ボタン
await yunhu_user.Send.Using("default").To("group", group_id).Reply(msg_id).Buttons(buttons).Text("完全なチェーン呼び出し")
```

### OneBot12メッセージのサポート

アダプタはOneBot12形式のメッセージを送信することをサポートし、クロスプラットフォームのメッセージ互換性を確保します：

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12形式のメッセージを送信します。

```python
# OneBot12形式のメッセージを送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await yunhu_user.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾子と組み合わせて使用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await yunhu_user.Send.To("group", group_id).Reply(msg_id).Raw_ob12(ob12_msg)
```

Raw_ob12 は混合メッセージセグメントを自動的にグループ処理します：
- `text`、`mention` タイプは1グループに結合されます
- `image`、`video`、`audio`、`file`、`face`、`markdown`、`html`、`a2ui` などのタイプはそれぞれ独立したグループになります
- `reply` タイプは任意のグループに追加できます

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、await で送信結果を取得できます。返り値は ErisPulse アダプタの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行状態
    "retcode": 0,             // 返り値コード
    "data": {...},            // 返り値データ
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "yunhu_user_raw": {...}   // 元の返り値データ
}
```

## 特有のイベントタイプ

`platform == "yunhu_user"` の検証が必要です。

### 核心的な違い

1. 特有のイベントタイプ：
    - スーパーファイル共有: `yunhu_user_file_send`
    - ロボット公告ボード: `yunhu_user_bot_board`
    - メッセージ編集通知: `message_edit`
    - メッセージ削除通知: `message_delete`（撤回）
2. 特有のメッセージセグメントタイプ：
    - フォームメッセージセグメント: `yunhu_user_form`
    - 記事メッセージセグメント: `yunhu_user_post`
    - ステッカーメッセージセグメント: `yunhu_user_sticker`
    - ボタンメッセージセグメント: `yunhu_user_button`
    - A2UI メッセージセグメント: `a2ui`
3. 拡張フィールド：
    - すべての特有フィールドは `yunhu_user_` プレフィックスで識別されます
    - 元のデータは `yunhu_user_raw` フィールドに保持されます
    - 元のイベントタイプは `yunhu_user_raw_type` フィールドに記録されます
    - プライベートチャットでは `self.user_id` は現在のログインユーザーIDを示します

### 対応する元のイベントタイプ

| 元のイベントタイプ | OneBot12 タイプ | 説明 |
|------------------|----------------|------|
| `push_message`   | `message`      | メッセージのプッシュ（プライベートチャット、グループチャット、Bot 会話） |
| `edit_message`   | `notice` (`message_edit`) | メッセージ編集イベント |
| `file_send_message` | `notice` (`yunhu_user_file_send`) | スーパーファイル共有イベント |
| `bot_board_message` | `notice` (`yunhu_user_bot_board`) | ロボット公告ボードイベント |

> 他のイベントタイプ（`heartbeat_ack`、`draft_input`、`stream_message` など）は無視されます。

### OneBot12 がサポートする detail_type

| OneBot12 detail_type | 云湖 chat_type | 説明 |
|---------------------|---------------|------|
| `private`           | 1             | プライベートメッセージ |
| `group`             | 2             | グループメッセージ |
| `private`           | 3             | ロボット会話（4.6.1から `private` にマッピング、元の `"bot"` は非標準；元の chat_type は `yunhu_user_raw` に保持されます） |

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
    "user_nickname": "送信者ニックネーム",
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
    "user_nickname": "送信者ニックネーム",
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

### ロボット公告ボードイベントの例

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
    "bot_name": "ロボット名",
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
    """云湖用户消息处理"""
    if event.get("platform") != "yunhu_user":
        return
    
    user_id = event.get("user_id", "")
    user_nickname = event.get("user_nickname", "")
    alt_message = event.get("alt_message", "")
    
    print(f"用户 {user_nickname}({user_id}): {alt_message}")
    
    # 检查消息段中的特有类型
    for segment in event.get("message", []):
        seg_type = segment.get("type", "")
        
        if seg_type == "yunhu_user_form":
            form_data = segment["data"]["form"]
            print(f"收到表单消息: {form_data}")
        
        elif seg_type == "yunhu_user_post":
            post_data = segment["data"]
            print(f"收到文章消息: {post_data.get('post_title', '')}")
        
        elif seg_type == "yunhu_user_sticker":
            sticker_url = segment["data"]["file_id"]
            print(f"收到贴纸消息: {sticker_url}")
        
        elif seg_type == "yunhu_user_button":
            buttons = segment["data"]["buttons"]
            print(f"消息包含按钮: {buttons}")
        
        elif seg_type == "a2ui":
            a2ui_data = segment["data"]["a2ui"]
            print(f"收到A2UI消息: {a2ui_data}")
    
    # 使用 event.reply() 自动回复
    await event.reply(f"Echo: {alt_message}")

@notice.on_notice()
async def handle_yunhu_user_notice(event):
    """云湖用户通知事件处理"""
    if event.get("platform") != "yunhu_user":
        return
    
    detail_type = event.get("detail_type", "")
    
    if detail_type == "message_edit":
        message_id = event.get("message_id", "")
        user_nickname = event.get("user_nickname", "")
        edit_time = event.get("edit_time", 0)
        print(f"用户 {user_nickname} 编辑了消息 {message_id}")
    
    elif detail_type == "yunhu_user_file_send":
        file_data = event.get("yunhu_user_file_send", {})
        print(f"收到超级文件分享: {file_data}")
    
    elif detail_type == "yunhu_user_bot_board":
        board_data = event.get("yunhu_user_bot_board", {})
        bot_name = event.get("bot_name", "")
        print(f"机器人 {bot_name} 发布了公告: {board_data.get('content', '')}")
```

## 拡張フィールドの説明

- すべての特有フィールドは `yunhu_user_` プレフィックスで識別し、標準フィールドとの衝突を避ける
- 元のデータは `yunhu_user_raw` フィールドに保持し、云湖プラットフォームの完全な元のデータにアクセスできる
- 元のイベントタイプは `yunhu_user_raw_type` フィールドに記録する（例: `push_message`、`edit_message` など）
- `self.user_id` は現在のログインユーザーIDを示す（ログイン応答から取得）
- スーパーファイル共有は `yunhu_user_file_send` フィールドでファイル共有データを提供
- ロボット公告ボードは `yunhu_user_bot_board` フィールドで公告データを提供

### 特有メッセージセグメントタイプ

#### 表形式メッセージセグメント (yunhu_user_form)

content_type が 5 の場合、メッセージセグメントタイプは `yunhu_user_form` です：

```json
{
    "type": "yunhu_user_form",
    "data": {
        "form": "表单数据"
    }
}
```

#### 記事形式メッセージセグメント (yunhu_user_post)

content_type が 6 の場合、メッセージセグメントタイプは `yunhu_user_post` です：

```json
{
    "type": "yunhu_user_post",
    "data": {
        "post_id": "文章ID",
        "post_title": "文章标题",
        "post_content": "文章内容"
    }
}
```

| フィールド | タイプ | 説明 |
|----------|--------|------|
| `post_id` | string | 文章唯一标识 |
| `post_title` | string | 文章标题 |
| `post_content` | string | 文章内容 |

#### ステッカー形式メッセージセグメント (yunhu_user_sticker)

content_type が 7 の場合、メッセージセグメントタイプは `yunhu_user_sticker` です：

```json
{
    "type": "yunhu_user_sticker",
    "data": {
        "file_id": "贴纸图片URL"
    }
}
```

| フィールド | タイプ | 説明 |
|----------|--------|------|
| `file_id` | string | 贴纸图片URL |

#### ボタン形式メッセージセグメント (yunhu_user_button)

メッセージにボタンが含まれる場合、`yunhu_user_button` メッセージセグメントが追加されます：

```json
{
    "type": "yunhu_user_button",
    "data": {
        "buttons": [[{"text": "按钮文字", "actionType": 3, "value": "值"}]]
    }
}
```

#### A2UI 形式メッセージセグメント (a2ui)

content_type が 14 の場合、メッセージセグメントタイプは `a2ui` です：

```json
{
    "type": "a2ui",
    "data": {
        "a2ui": "A2UI JSON数据"
    }
}
```

---

## 複数アカウントの設定

### 設定の説明

YunhuUserAdapter は複数のユーザーアカウントを同時に設定・実行できます。

```toml
# config.toml
[YunhuUserAdapter]
ws_reconnect_interval = 30  # WebSocket再接続間隔（秒）
ws_timeout = 70             # WebSocketタイムアウト時間（秒）

[YunhuUserAdapter.accounts.default]
email = "user1@example.com"  # ユーザーのメールアドレス（必須）
password = "password1"       # ユーザーのパスワード（必須）
platform = "windows"         # ログインプラットフォーム（オプション、デフォルトはwindows）
device_id = ""               # デバイスID（オプション、未設定時は自動生成）
poll_friend_requests = true  # 友人申請のポーリング（オプション、デフォルトはtrue）
poll_interval = 60           # 友人申請ポーリング間隔（秒、オプション、デフォルトは60、最小5）
enabled = true               # 有効にするかどうか（オプション、デフォルトはtrue）

[YunhuUserAdapter.accounts.account2]
email = "user2@example.com"
password = "password2"
platform = "android"
device_id = "fixed_device_id_2"
enabled = true
```

**設定項目の説明：**
- `email`：ユーザーのメールアドレス（必須）、云湖プラットフォームにログインするため
- `password`：ユーザーのパスワード（必須）
- `platform`：ログインプラットフォームの識別子（オプション、デフォルトは `windows`）、選択肢：`windows`、`macos`、`linux`、`ios`、`android`
- `device_id`：デバイドID（オプション、未設定時は自動生成）、セッションの一貫性を保つために固定値を設定することを推奨
- `poll_friend_requests`：友人申請のポーリングを行うかどうか（オプション、デフォルトは `true`；「友人申請処理」参照）
- `poll_interval`：友人申請ポーリング間隔（秒、オプション、デフォルトは60、最小5）
- `enabled`：アカウントを有効にするかどうか（オプション、デフォルトは `true`）

**アダプタレベルの設定：**
- `ws_reconnect_interval`：WebSocketの再接続間隔（秒、デフォルトは30）
- `ws_timeout`：WebSocketのタイムアウト時間（秒、デフォルトは70）

**重要な注意点：**
1. アダプタはメールアドレスでログインし、token を取得し、WebSocket を使用してイベントを受信します
2. WebSocket接続が切断された場合、最大3回まで自動的に再接続します
3. 各アカウントに固定の `device_id` を設定することを推奨します。これによりセッションの一貫性が保たれます
4. デフォルトのアカウント（デフォルトのメールアドレスとパスワード）は自動的にスキップされます

### Using() メソッドでアカウントを指定して Send DSL を使用する

`Using()` メソッドを使用して、どのアカウントを使ってメッセージを送信するかを指定できます。このメソッドは2種類のパラメータを受け付けます：
- **アカウント名**：設定ファイル中のアカウント名（例：`default`、`account2`）
- **user_id**：ログイン後に取得されるユーザーID

```python
from ErisPulse.Core import adapter
yunhu_user = adapter.get("yunhu_user")

# アカウント名を使ってメッセージを送信
await yunhu_user.Send.Using("default").To("user", "user123").Text("Hello from account1!")

# user_idを使ってメッセージを送信（対応するアカウントを自動的に検索）
await yunhu_user.Send.Using("user_id_here").To("group", "group456").Text("Hello from user!")

# 指定しない場合は最初に有効なアカウントが使用されます
await yunhu_user.Send.To("user", "user123").Text("Hello from default account!")
```

> **注意：** `user_id` を使用する場合、システムは設定ファイルに一致するアカウントを自動的に検索します。これはイベント返信時に特に便利です。`event["self"]["user_id"]` を使用して同じアカウントで返信できます。

### イベント内のアカウント識別子

受信したイベントには自動的に対応するユーザーID情報が含まれます：

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "yunhu_user":
        # 現在のログインユーザーIDを取得
        my_user_id = event["self"]["user_id"]
        print(f"メッセージはアカウント: {my_user_id} から来ています")
        
        # 同じアカウントで返信メッセージを送信
        yunhu_user = adapter.get("yunhu_user")
        await yunhu_user.Send.Using(my_user_id).To(
            event["detail_type"],
            event["user_id"] if event["detail_type"] == "private" else event["group_id"]
        ).Text("返信メッセージ")
```

### ログ情報

アダプタはログに自動的にアカウント情報を含め、デバッグや追跡に便利です：

```
[INFO] 账户 default (user1@example.com) 登录成功，用户ID: 12345678
[INFO] 账户 default WebSocket 监听任务已启动
[INFO] 账户 account2 (user2@example.com) 登录成功，用户ID: 87654321
```

### 管理インターフェース

```python
# すべてのアカウント情報を取得
accounts = yunhu_user.accounts
# 戻り値形式: {"default": {"name": "default", "email": "...", "token": "...", "user_id": "...", ...}, ...}

# アカウントが有効かどうかを確認
for account_name, account_config in yunhu_user._account_configs.items():
    print(f"{account_name}: enabled={account_config.enabled}")

# アカウント名からHTTPクライアントを取得
http_client = yunhu_user._get_http_client("default")

# user_idからアカウントを検索
account_name = yunhu_user._get_account_by_user_id("12345678")
```

## API 呼び出し

アダプタは `call_api` メソッドを提供し、プラットフォームAPIを直接呼び出すことができます：

```python
# メッセージ送信
result = await yunhu_user.call_api("/send", 
    target_type="group", 
    target_id="group_id",
    account_id="default",
    message={"text": "Hello", "msg_type": 1}
)

# メッセージ編集
result = await yunhu_user.call_api("/edit",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id",
    text="新内容",
    content_type="text"
)

# メッセージ撤回
result = await yunhu_user.call_api("/recall",
    target_type="group",
    target_id="group_id",
    msg_id="msg_id"
)

# メッセージ一括撤回
result = await yunhu_user.call_api("/recall_batch",
    target_type="group",
    target_id="group_id",
    msg_id_list=["msg_id_1", "msg_id_2"]
)

# メッセージ一覧取得
result = await yunhu_user.call_api("/list",
    chat_id="group_id",
    chat_type=2,
    msg_count=10,
    msg_id=""
)

# メッセージ編集記録取得
result = await yunhu_user.call_api("/list_edit_record",
    msg_id="msg_id",
    size=10,
    page=1
)

# ボタンイベント報告
result = await yunhu_user.call_api("/button_report",
    chat_id="group_id",
    chat_type=2,
    msg_id="msg_id",
    user_id="user_id",
    button_value="button_value"
)
```

**サポートされるAPIエンドポイント：**

| エンドポイント | 説明 |
|----------------|------|
| `/send`        | メッセージ送信 |
| `/edit`        | メッセージ編集 |
| `/recall`      | メッセージ撤回 |
| `/recall_batch`| メッセージ一括撤回 |
| `/list`        | メッセージ一覧取得 |
| `/list_by_seq` | シーケンスによるメッセージ取得 |
| `/list_by_mid_seq` | メッセージIDとシーケンスによるメッセージ取得 |
| `/list_edit_record` | メッセージ編集記録取得 |
| `/button_report` | ボタンイベント報告 |



### 平台文档维护说明

# ドキュメントの保守に関する説明

このドキュメントは、各アダプタ開発者が保守しており、OneBot12 標準との差異や拡張機能を説明するために使用されます。
アダプタ開発者は、新バージョンをリリースする際に、このドキュメントも同時に更新してください。

## 更新要件

1. プラットフォーム固有の送信方法とパラメータを正確に記述すること  
2. OneBot12 標準との差異点を詳細に説明すること  
3. 明確なコード例とパラメータの説明を提供すること  
4. ドキュメントのフォーマットを統一し、ユーザーが見つけやすいようにすること  
5. バージョン情報とメンテナの連絡先をタイムリーに更新すること

## ドキュメント構造規格

### 1. 基本情報部分
各プラットフォーム機能ドキュメントには、以下の基本情報が含まれている必要があります。
```markdown
# プラットフォーム名アダプタドキュメント

アダプタ名: [アダプタクラス名]
プラットフォーム紹介: [プラットフォームの簡単な紹介]
サポートするプロトコル/APIバージョン: [具体的なプロトコルまたはAPIバージョン]
メンテナ: [メンテナの氏名/チーム名]
対応モジュールバージョン: [バージョン番号]
```

### 2. 支持するメッセージ送信タイプ
すべてのサポートする送信メソッドとそのパラメータを詳細に記述します。
```markdown
## 支持するメッセージ送信タイプ

すべての送信メソッドは、メソッドチェーン構文で実現されます。たとえば:
[コード例]

サポートする送信タイプは以下の通りです。
- メソッド1: 説明
- メソッド2: 説明
- ...

### パラメータの説明
| パラメータ | 型 | 説明 |
|------|------|------|
| パラメータ名 | 型 | 説明 |
```

### 3. 特有のイベントタイプ
プラットフォーム固有のイベントタイプとその形式を詳細に説明します。
```markdown
## 特有のイベントタイプ

[プラットフォーム名]のイベントはOneBot12プロトコルに変換され、標準フィールドはOneBot12プロトコルに完全に準拠しますが、以下の違いがあります。

### 核心的な違い
1. 特有のイベントタイプ:
   - イベントタイプ1: 説明
   - イベントタイプ2: 説明
2. 拡張フィールド:
   - フィールドの説明

### 特殊フィールドの例
[JSON例]
```

### 4. 拡張フィールドの説明
```markdown
## 拡張フィールドの説明

- すべての固有フィールドは、`[platform]_` という接頭辞で識別されます
- 元のデータは、`[platform]_raw` フィールドに保持されます
- [その他の特殊フィールドの説明]
```

### 5. 設定オプション（該当する場合）
```markdown
## 設定オプション

[プラットフォーム名]アダプタは以下の設定オプションをサポートします。

### 基本設定
- 設定項目1: 説明
- 設定項目2: 説明

### 特殊設定
- 特殊設定項目1: 説明
```

## 内容作成規格

### コード例の規格
1. すべてのコード例は実行可能な完全な例でなければなりません。
2. 標準的なインポート方法を使用してください：
```python
from ErisPulse.Core import adapter
[アダプタのインスタンス] = adapter.get("[アダプタ名]")
```
3. 複数の使用シナリオの例を提供してください。

### ドキュメント形式の規格
1. 標準的なMarkdown形式を使用してください。
2. タイトルの階層が明確で、最大4段階のタイトルを使用してください。
3. テーブルは標準的なMarkdownテーブル形式を使用してください。
4. コードブロックには適切な言語識別子を使用してください。

### バージョン更新の説明
ドキュメントを更新するたびに、ドキュメントの最上部にバージョン情報を更新してください：
```markdown
## ドキュメント情報

- 対応モジュールバージョン: [新しいバージョン番号]
- メンテナー: [メンテナー情報]
- 最終更新日: [日付]
```

## 質量チェックリスト

ドキュメントの更新を提出する前に、以下の内容を確認してください：

- [ ] ドキュメントの構造が規格要件に準拠している
- [ ] すべてのコード例が正常に実行できる
- [ ] パラメータの説明が完全かつ正確である
- [ ] イベント形式の例が実際の出力に合致している
- [ ] リンクと引用が正しく無誤である
- [ ] 文法とスペルに誤りがない
- [ ] バージョン情報が更新されている
- [ ] メンテナー情報が正確である

## 参考文書

一貫性を確保するために、以下の文書を参考にしてください：

- [OneBot12標準文書](https://12.onebot.dev/)
- [ErisPulseの基本概念](../getting-started/basic-concepts.md)
- [イベント変換標準](../standards/event-conversion.md)
- [APIレスポンス規格](../standards/api-response.md)
- [その他のプラットフォームアダプタ文書](./)

## 貢献フロー

1. [ErisPulse](https://github.com/ErisPulse/ErisPulse) リポジトリを Fork する
2. `docs/platform-features/` ディレクトリ内で対応するプラットフォームのドキュメントを変更する
3. ドキュメントが上記の規格要件に準拠していることを確認する
4. Pull Request を送信し、変更内容を詳しく説明する

ご質問がある場合は、関連するアダプタのメンテナに連絡するか、プロジェクトの Issues で質問してください。



### 花枫咖啡馆适配

# 花枫咖啡館（RockyChat）プラットフォーム機能ドキュメント

IdeauraAdapter は、花楓コーヒー館（RockyChat）プラットフォームの API を基に構築されたアダプターで、すべてのプラットフォーム機能モジュールを統合し、一貫したイベント処理およびメッセージ操作インターフェースを提供します。

---

## ドキュメント情報

- 対応モジュール: ErisPulse-Ideaura
- 対応モジュールバージョン: 4.3.2
- 維持者: ErisPulse
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: 花楓コーヒー館（RockyChat）は、リアルタイム通信プラットフォームです。
- アダプター名: IdeauraAdapter
- マルチアカウント対応: Bot Token による複数アカウントの設定が可能です。
- チェーン修飾子対応: `.At()`、`.AtAll()`、`.Reply()`、`.Command()` などのチェーン修飾メソッドがサポートされています。
- OneBot12 向け: OneBot12 形式のメッセージ送信が可能です。

## 標準化対応（4.3.2）

### イベントとアカウント

1. **イベント `self.account_id` の注入**: すべてのイベントは、そのイベントが発生したアカウント名を保持しており、マルチアカウント環境では `event.reply()` は自動的に該当アカウントで返信します。
2. **アカウント設定に `bot_id` オプションフィールドを追加**: `IdeauraAccountConfig` は `bot_id` をサポートし、アカウントに対応する Bot ユーザー ID を明示的に指定できます。
3. **友達申請イベントに標準 `request_id` を追加**: `friend_request` / `friend_event` イベントの最上位に `request_id`（`ideaura_request_id` と同じ値）が追加され、`event.approve()` / `event.reject()` で申請を承認・拒否できます。

友達申請処理の例:

```python
from ErisPulse.Core.Event import request

@request.on_request()
async def handle_friend_request(event):
    if event.get("platform") != "ideaura":
        return
    # event["request_id"] は ideaura_request_id と同じ値
    if event.get("detail_type") == "friend":
        await event.approve()    # 友達申請を承認
    # await event.reject()       # 友達申請を拒否
```

インターフェースの規約は SDK の規格に従います: [リクエストと承認アクションの規格](../standards/request-action-spec.md)。

### アクションとエラーコード規格

1. **標準アクション名を HTTP パスに転送しない**: `call_api` に未実装の標準アクション名（例: `get_self_info`）を渡した場合、HTTP パスに転送せず、明示的にエラーコード 10002 を返します。プラットフォームの HTTP パス呼び出しは `/api/` で始まる必要があります。
2. エラーコードが標準化されました（元の HTTP ステータスコード、`-1`、`34000` などの旧値はすべて削除）：

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（リクエスト異常、タイムアウトなど） |
| 34100 | プラットフォームエラー（元のレスポンスは `ideaura_raw` フィールドに保持） |
| 10002 | 対応していないアクション / メッセージセグメント（未実装の標準アクション、Face エモジセグメントなど） |

### Send 規格

- HTML メソッド名は `HTML`（`Html` は予約別名）
- `Face` セグメントは 10002 エラーコードを返し、警告ログを出力します。純文に降格して送信することはなく、無視されます。
- Raw_ob12 で未知のメッセージセグメントが見つかった場合は警告ログを出力し、すべてのセグメントが処理できない場合は 10002 を返します。

## v5 ファンタジア更新（4.1.0）

- **BaseConverter 継承**: 転換器の共通フィールドはフレームワークの build_base_event で構築されます。
- **spawn_background タスクの所属**: アカウント接続タスクは runtime.spawn_background を使用します。
- **フレームワークのソフト依存**: ErisPulse>=2.7.1 を実行時に検出し、警告を出力します。起動時にバージョンログを出力します。
- Request DSL クエリ式インターフェース（`Request(request_id)`）は延期されます。友達申請の承認はイベント `event.approve()` / `event.reject()` で処理できます（「標準化対応（4.3.2）」を参照）。

### 対応プラットフォーム機能

- **イベント**: メッセージ編集/撤回/転送/既読（ideaura_message_*）、友達申請（friend_request）、友達増減（friend_increase/decrease）、オンラインステータス（friend_online/offline）
- **送信**: Text / Image / Markdown / Raw_ob12（チェーン修飾子 Reply/At/AtAll）
- **友達申請承認**: 4.3.2 以降、イベント `event.approve()` / `event.reject()` で対応
- **未対応**: Api DSL（プラットフォーム REST インターフェースが公開された後に追加）、Request DSL クエリ式インターフェース

---

## 支援されるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実現されます。例:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

await ideaura.Send.To("group", "chatroom").Text("Hello World!")
```

サポートされる送信タイプは以下の通りです:

- `.Text(text: str)`：テキストメッセージを送信します。
- `.Image(file, filename: str = None)`：画像メッセージを送信します。bytes/URL/ローカルパスをサポートします。
- `.Video(file, filename: str = None)`：動画メッセージを送信します。bytes/URL/ローカルパスをサポートします。
- `.File(file, filename: str = None)`：ファイルメッセージを送信します。bytes/URL/ローカルパスをサポートします。
- `.Voice(file, filename: str = None)`：音声メッセージを送信します（ファイルとして）。
- `.Face(face_id: str)`：エモジを送信します（4.3.2 以降**プラットフォームはサポートしていません**。retcode=10002 を返し、無視されます。テキストに降格することもありません）。
- `.Markdown(text: str)`：Markdown 形式のメッセージを送信します。
- `.HTML(html: str)`：HTML 形式のメッセージを送信します（`Html` は予約別名）。
- `.MergeForward(nodes, title="合併チャット記録")`：合併転送メッセージを送信します（`<details>` 折りたたみ HTML カードとしてレンダリングされます）。
- `.Edit(message_id: str, text: str, content_type: str = "text")`：既存のメッセージを編集します。
- `.Recall(message_id: str)`：メッセージを撤回します。

### チェーン修飾メソッド（組み合わせて使用可能）

チェーン修飾メソッドは `self` を返し、チェーンで呼び出すことができます。最終的な送信メソッドの前に呼び出す必要があります:

- `.At(user_id: str, name: str = None)`：指定ユーザーを@します。
- `.AtAll()`：全員を@します。
- `.Reply(message_id: str)`：指定メッセージに返信します。
- `.Command(command_id: str)`：Bot コマンドをトリガーします。送信メソッドと組み合わせて使用します（メッセージを指定されたコマンドとして送信します）。

### チェーン呼び出しの例

```python
# 基本送信
await ideaura.Send.To("user", user_id).Text("Hello")

# Bot コマンドのトリガー
await ideaura.Send.To("group", "chatroom").Command("550e8400-e29b-41d4-a716-446655440000").Text("/weather 北京")

# @ユーザー
await ideaura.Send.To("group", "chatroom").At("456").Text("@李四 你好")

# @複数ユーザー
await ideaura.Send.To("group", "chatroom").At("456").At("789").Text("@複数ユーザー")

# メッセージの返信
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Text("返信メッセージ")

# 返信 + @
await ideaura.Send.To("group", "chatroom").Reply(msg_id).At("456").Text("返信して@")

# HTML 形式メッセージ
await ideaura.Send.To("group", "chatroom").HTML("<p>HTML メッセージ</p>")
```

### 異なるターゲットへの送信

```python
# チャットルームに送信
await ideaura.Send.To("group", "chatroom").Text("チャットルームメッセージ")

# トピックに送信
await ideaura.Send.To("group", "topic_id").Text("トピックメッセージ")

# プライベートメッセージ送信
await ideaura.Send.To("user", "user_id").Text("プライベートメッセージ")
```

### OneBot12 メッセージ対応

アダプターは OneBot12 形式のメッセージ送信をサポートし、跨プラットフォームのメッセージ互換性を確保します:

- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式のメッセージを送信します。

```python
# OneBot12 形式メッセージの送信
ob12_msg = [{"type": "text", "data": {"text": "Hello"}}]
await ideaura.Send.To("user", user_id).Raw_ob12(ob12_msg)

# チェーン修飾子と組み合わせて使用
ob12_msg = [{"type": "text", "data": {"text": "返信メッセージ"}}]
await ideaura.Send.To("group", "chatroom").Reply(msg_id).Raw_ob12(ob12_msg)
```

> 未知のメッセージセグメントは警告ログを出力し、無視されます。すべてのメッセージセグメントが処理できない場合は、retcode=10002 を返します。

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、await で送信結果を取得できます。返り値は ErisPulse アダプターの標準化された返り値規格に従います:

```python
{
    "status": "ok",           // 実行状態
    "retcode": 0,             // 返り値コード（0 が成功、エラーコードは「標準化対応（4.3.2）」を参照）
    "data": {...},            // レスポンスデータ
    "self": {...},            // 自身の情報（user_id を含む）
    "message_id": "123456",   // メッセージID
    "message": "",            // エラーメッセージ
    "ideaura_raw": {...}      // 元のレスポンスデータ
}
```

## 特有のイベントタイプ

`platform=="ideaura"` の検査が必要です。

### 核心的な差異点

1. 特有のイベントタイプ:
    - メッセージ編集: ideaura_message_edit
    - メッセージ撤回: ideaura_message_recall
    - メッセージ転送: ideaura_message_forward
    - メッセージ既読: ideaura_message_read
    - 友達拒否: ideaura_friend_rejected
    - 友達オンライン: ideaura_friend_online
    - 友達オフライン: ideaura_friend_offline
    - ユーザー状態変更: ideaura_user_status_change
    - 転送メッセージセグメント: ideaura_forwarded
    - 編集マークセグメント: ideaura_edited
    - Markdownメッセージセグメント: ideaura_markdown
    - HTMLメッセージセグメント: ideaura_html
    - Bot コマンドメッセージセグメント: ideaura_command
2. 拡張フィールド:
    - すべての特有フィールドは `ideaura_` で始まります
    - 元のデータは `ideaura_raw` フィールドに保持されます
    - イベント `self.user_id` は現在のアカウントのユーザーIDを示し、`self.account_id` はアカウント名です

### メッセージ編集イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_edit",
  "platform": "ideaura",
  "message_id": "メッセージID",
  "user_id": "編集者ID",
  "ideaura_new_content": "編集後の内容",
  "ideaura_updated_message": { ... },
  "ideaura_source_type": "chatroom/topic/private"
}
```

### メッセージ撤回イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_recall",
  "platform": "ideaura",
  "message_id": "撤回されたメッセージID",
  "user_id": "撤回者ID",
  "group_id": "chatroom",
  "ideaura_source_type": "chatroom",
  "ideaura_recall_time": "撤回時間",
  "ideaura_is_self": false
}
```

### メッセージ転送イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_forward",
  "platform": "ideaura",
  "message_id": "元のメッセージID",
  "user_id": "転送者ID",
  "ideaura_forward_to": "目的トピックID",
  "ideaura_original_message_id": "元のメッセージID",
  "ideaura_forwarded_message_id": "転送後の新しいメッセージID"
}
```

### メッセージ既読イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_message_read",
  "platform": "ideaura",
  "message_id": "メッセージID",
  "ideaura_reader_id": "既読者ID",
  "ideaura_reader_name": "既読者のニックネーム"
}
```

### 友達オンラインイベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_online",
  "platform": "ideaura",
  "user_id": "友達ID",
  "user_nickname": "友達のニックネーム",
  "ideaura_friend_avatar": "アバターURL",
  "ideaura_presence_status": "online"
}
```

### 友達オフラインイベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_offline",
  "platform": "ideaura",
  "user_id": "友達ID",
  "ideaura_presence_status": "offline"
}
```

### ユーザー状態変更イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_user_status_change",
  "platform": "ideaura",
  "user_id": "ユーザーID",
  "ideaura_status": "新しいステータス",
  "ideaura_previous_status": "前のステータス"
}
```

### 友達リクエストイベント

4.3.2 以降、最上位に標準 `request_id` フィールドが追加され、`ideaura_request_id` と同じ値です。`event.approve()` / `event.reject()` で承認できます:

```python
{
  "type": "request",
  "detail_type": "friend",
  "platform": "ideaura",
  "user_id": "リクエスト者ID",
  "user_nickname": "リクエスト者のニックネーム",
  "request_id": "リクエストID",
  "ideaura_request_id": "リクエストID",
  "ideaura_message": "認証メッセージ"
}
```

### 友達拒否イベント

```python
{
  "type": "notice",
  "detail_type": "ideaura_friend_rejected",
  "platform": "ideaura",
  "user_id": "拒否者ID",
  "user_nickname": "拒否者のニックネーム",
  "ideaura_request_id": "リクエストID",
  "ideaura_requester_id": "リクエスト発起者ID",
  "ideaura_requester_name": "リクエスト発起者のニックネーム"
}
```

### 転送メッセージセグメント (ideaura_forwarded)

転送メッセージを受け取った場合、メッセージセグメントのタイプは `ideaura_forwarded` です:

```json
{
  "type": "ideaura_forwarded",
  "data": {
    "forward_source_id": "1001",
    "original_message_id": "1001"
  }
}
```

| フィールド | タイプ | 説明 |
|------|------|------|
| `forward_source_id` | string | 転送元メッセージID |
| `original_message_id` | string | 元のメッセージID |

### Bot コマンドメッセージセグメント (ideaura_command)

ユーザーが Bot コマンドをトリガーした場合、メッセージセグメントのタイプは `ideaura_command` です:

```json
{
  "type": "ideaura_command",
  "data": {
    "command_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| フィールド | タイプ | 説明 |
|------|------|------|
| `command_id` | string | コマンド UUID |

### イベント処理の例

```python
from ErisPulse.Core.Event import notice, message

@message.on_message()
async def handle_message(event):
    if event.get_platform() == "ideaura":
        # メッセージイベントを処理
        for segment in event.get("message", []):
            if segment.get("type") == "ideaura_forwarded":
                data = segment["data"]
                print(f"転送メッセージ、元ID: {data['forward_source_id']}")

@notice.on_notice()
async def handle_notice(event):
    if event.get_platform() != "ideaura":
        return

    detail_type = event.get("detail_type")

    if detail_type == "ideaura_message_edit":
        new_content = event.get("ideaura_new_content", "")
        print(f"メッセージが編集されました: {new_content}")

    elif detail_type == "ideaura_message_recall":
        message_id = event.get("message_id")
        print(f"メッセージが撤回されました: {message_id}")

    elif detail_type == "ideaura_friend_online":
        friend_name = event.get_user_nickname()
        print(f"友達がオンラインになりました: {friend_name}")

    elif detail_type == "ideaura_user_status_change":
        status = event.get("ideaura_status")
        print(f"ユーザーのステータスが変更されました: {status}")
```

## Event Mixin 拡張メソッド

アダプターは以下のプラットフォーム固有メソッドを登録しており、`platform == "ideaura"` の場合にのみ使用可能です:

| メソッド | 戻り値型 | 説明 |
|------|----------|------|
| `get_source_type()` | `str` | メッセージの送信元タイプ（`chatroom`/`topic`/`private`） |
| `get_sender_name()` | `str` | 送信者のニックネーム |
| `get_sender_avatar()` | `str` | 送信者のアバター URL |
| `is_sender_bot()` | `bool` | 送信者が Bot かどうか |
| `is_receiver_bot()` | `bool` | 受信者が Bot かどうか |
| `get_command_id()` | `str` | トリガーされた Bot コマンド ID（存在する場合、`ideaura_command_id`） |
| `get_command()` | `str` | `get_command_id()` の別名 |
| `get_topic_name()` | `str` | トピックの名前 |
| `get_message_type()` | `str` | メッセージのタイプ（normal/edited/forwarded/quoted） |
| `get_message_subtype()` | `str` | メッセージのサブタイプ（text/image/video/file/markdown/html） |
| `is_self_message()` | `bool` | 自分が送信したメッセージかどうか |

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event.get_platform() != "ideaura":
        return

    # トリガーされた Bot コマンド ID を取得（存在する場合）
    cmd_id = event.get_command_id()
    if cmd_id:
        print(f"コマンドを受け取りました: {cmd_id}")
```

---

## マルチアカウント設定

### 設定の説明

IdeauraAdapter は複数のアカウントを同時に設定および実行できます。**Bot Token** を使用した認証が必要です。

> [!WARNING]
> 4.0.1 以降**メールアドレス/パスワードによるログインは削除され、Bot Token でのみ対応**します。Bot Token は [MSCPO オープンプラットフォーム](https://open.mscpo.com/rockychat/bots) から取得する必要があります（`bot-token-` で始まります）。

```toml
# config.toml
# アカウント1
[IdeauraAdapter.accounts.default]
token = "bot-token-xxxxxx1"      # ロボット API Token（必須）
bot_id = ""                      # Bot ユーザーID（オプション、アカウントに対応する Bot を明示的に指定）
enabled = true                   # 有効かどうか（オプション、デフォルトはtrue）

# アカウント2
[IdeauraAdapter.accounts.bot2]
token = "bot-token-xxxxxx2"
bot_id = ""
enabled = true

# オプション: 自定義サーバーのアドレス
[IdeauraAdapter]
base_url = "https://api.mscpo.com/api/rockychat"
ws_url = "wss://api-cofe.allons-y.uk:3009/mqtt"
heartbeat_interval = 30
```

**設定項目の説明:**
- `token`: ロボット API Token（必須、`bot-token-` で始まる）
- `bot_id`: Bot ユーザーID（オプション、4.3.2 以降対応、アカウントに対応する Bot を明示的に指定）
- `enabled`: アカウントの有効性（オプション、デフォルトはtrue）

**グローバル設定項目:**
- `base_url`: API サーバーのアドレス（オプション、デフォルトは `https://api.mscpo.com/api/rockychat`）
- `ws_url`: WebSocket サーバーのアドレス（オプション、デフォルトは花楓コーヒー館の公式アドレス）
- `heartbeat_interval`: ハートビートの間隔（秒、オプション、デフォルトは30秒）

### Send DSL でアカウントを指定

`Using()` メソッドで送信するアカウントを指定できます:

```python
from ErisPulse.Core import adapter
ideaura = adapter.get("ideaura")

# アカウント名で送信
await ideaura.Send.Using("default").To("user", "user123").Text("Hello from account 1!")

# user_id で送信（自動的に対応するアカウントにマッチ）
await ideaura.Send.Using("456").To("group", "chatroom").Text("Hello from account 2!")

# 指定しない場合は最初に有効なアカウントを使用
await ideaura.Send.To("user", "user123").Text("Hello from default account!")
```

### イベントでのアカウント識別

受信されたイベントには自動的に対応するアカウント情報が含まれます（4.3.2 以降 `self.account_id` はアカウント名です）:

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    if event["platform"] == "ideaura":
        account_id = event["self"]["account_id"]
        print(f"メッセージはアカウント: {account_id} から来ています")
```

---

## 拡張フィールドの説明

- すべての特有フィールドは `ideaura_` で始まり、標準フィールドとの衝突を避ける
- 元のデータは `ideaura_raw` フィールドに保持され、プラットフォームの完全な元のデータにアクセスできる
- `self.user_id` は現在ログインしているアカウントのユーザーIDを示し、`self.account_id` はアカウント名
- `ideaura_source_type`: メッセージの送信元タイプ（`chatroom`/`topic`/`private`）
- `ideaura_sender_name`: 送信者のニックネーム
- `ideaura_sender_avatar`: 送信者のアバターURL
- `ideaura_sender_is_bot`: 送信者がロボットかどうか
- `ideaura_is_self`: 自分が送信したメッセージかどうか（自己メッセージはフィルタリング済み）
- `ideaura_topic_name`: トピックの名前
- `ideaura_message_type`: メッセージのタイプ（normal/edited/forwarded/quoted）
- `ideaura_message_subtype`: メッセージのサブタイプ（text/image/video/file/markdown/html）

### ファイル処理の特性

- ファイルサイズ制限: 10MB（ダウンロードとローカル読み込みの両方に制限があります）
- 自動ファイルタイプ検出: ファイルの魔法のバイトで実際のタイプを検出します
- スマートなファイル名解析: `.bin`/`.dat`/`.tmp` などの意味のない拡張子は自動的に修正されます
- bytes、URL、ローカルパスの3種類のファイル入力方式をサポート
- URL ファイルは自動的にダウンロードされ、サーバーにアップロードされます

### 対応するファイルタイプ

魔法のバイトで自動検出されます:

| タイプ | 拡張子 |
|------|--------|
| 画像 | png, jpg, gif, webp |
| 動画 | mp4, avi, flv |
| 音声 | mp3, wav, ogg |
| ドキュメント | pdf, docx |

---

## 注意事項

1. API サーバーのデフォルトアドレスは `https://api.mscpo.com/api/rockychat`（`base_url` でカスタマイズ可能）です。WebSocket アドレス `wss://api-cofe.allons-y.uk:3009/mqtt` はプラットフォームの固有アドレスであり、アダプター名の変更に伴って変化しません。
2. アダプターは WebSocket 長接続を使用してイベントを受信し、自動再接続（固定5秒の遅延）をサポートします。
3. 自身が送信したメッセージ（`isSelf: true`）は自動的にフィルタリングされ、イベントが発生しません。
4. @全員（`AtAll()`）は管理者権限が必要です。
5. ファイルのアップロードサイズ制限は 10MB です。
6. 音声ファイルは `file` サブタイプとして送信されます（プラットフォームは独立した音声タイプを区別しません）。
7. エモジ（`Face()`）はプラットフォームでサポートされていないため、retcode=10002 を返し、無視されます（テキストに降格することもありません）。
8. プログラム終了時には `shutdown()` を呼び出してリソースを確実に解放してください。



### Discord 适配

# Discord プラットフォーム特性ドキュメント

DiscordAdapter は、Discord Gateway (WebSocket) および REST API v10 プロトコルに基づいて構築されたアダプターであり、Discord Bot のコア機能を統合し、一貫したイベント処理およびメッセージ操作のインターフェースを提供します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.4.3
- メンテナ: ErisPulse
- Discord API バージョン: v10
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: Discord は、サーバー、チャンネル、プライベートメッセージなど多様な会話形式をサポートする、人気のあるコミュニティコミュニケーションプラットフォームであり、Bot 開発のための包括的な API を提供します。
- アダプター名: DiscordAdapter
- 多アカウント対応: 複数の Discord Bot を同時に設定できます。
- 接続方法: Gateway WebSocket（イベント受信）+ REST API（メッセージ送信/インターフェース呼び出し）
- 認証方法: Bot Token（HTTP ヘッダー `Authorization: Bot {token}`、Gateway IDENTIFY ペイロードに token 搭載）
- チェーン修飾子対応: `.Reply()`、`.At()`、`.AtAll()` などのチェーン修飾メソッドに対応
- OneBot12 兼容: OneBot12 形式のメッセージ送信に対応

## 設定説明

DiscordAdapter は複数アカウントの設定をサポートし、各アカウントは個別の Discord Bot に対応します。

```toml
# config.toml

# アカウント1
[DiscordAdapter.accounts.default]
token = "YOUR_BOT_TOKEN"       # Discord Bot Token（必須）
intents = 33281                 # Gateway Intents（オプション、デフォルト 33281）
enabled = true                  # 有効化するかどうか（オプション、デフォルト true）

# アカウント2
[DiscordAdapter.accounts.bot2]
token = "ANOTHER_BOT_TOKEN"
intents = 33281
enabled = true
```

**各アカウントの設定項目説明:**

- `token`: Discord Bot Token（必須）、[Discord Developer Portal](https://discord.com/developers/applications) から取得
- `intents`: Gateway Intents ビットマスク（オプション、デフォルト `33281`）、Bot がサブスクライブするイベントの種類を決定
- `bot_id`: Bot のユーザー ID（オプション、実行時に READY イベントから自動取得、手動入力不要）
- `enabled`: そのアカウントを有効化するかどうか（オプション、デフォルト `true`）

### Gateway Intents

Intents はビットマスクを使用し、各 Intent 値をビット演算 OR (`|`) で計算します：

| Intent | ビット | 値 | 説明 | Privileged |
|-------|------|------|------|------|
| GUILDS | `1 << 0` | 1 | サーバーの作成/削除/更新、チャンネル、ロールの変更 | 否 |
| GUILD_MEMBERS | `1 << 1` | 2 | メンバーの加入/離脱/更新 | 是 |
| GUILD_MESSAGES | `1 << 9` | 512 | サーバーのメッセージ送受信 | 否 |
| MESSAGE_CONTENT | `1 << 15` | 32768 | メッセージ内容（この Intent がない場合 content は空） | 是 |

デフォルト値 `33281` = `GUILDS(1) | GUILD_MESSAGES(512) | MESSAGE_CONTENT(32768)`。

> **注意**: Privileged Intents は Discord Developer Portal → Bot → Privileged Gateway Intents で有効化する必要があります。Bot が 100 以上のサーバーに存在する場合は、Discord 審査も必要です。

**API 環境:**
- Discord REST API 基本アドレス: `https://discord.com/api/v10`
- Gateway WebSocket アドレス: `GET /gateway/bot` で動的に取得、通常は `wss://gateway.discord.gg/?v=10&encoding=json`

## 標準化対応（4.4.3）

### イベント変更

1. **イベント id の一意性**: MESSAGE_UPDATE / MESSAGE_DELETE、REACTION_ADD / REMOVE（REMOVE_ALL / REMOVE_EMOJI 含む）などの派生イベントの `id` は `"イベント名:元のid"`（例: `MESSAGE_UPDATE:123456`）に変更され、CREATE イベントと id が衝突してフレームワークで重複排除されるのを防ぎます。
2. **イベント `self.account_id` の注入**: すべてのイベントに、イベントを生成したアカウント名が含まれ、多アカウント下では `event.reply()` は該当アカウントで自動的に受理・送信されます。
3. **INTERACTION_CREATE イベントの修正**: 元々誤って `type="request"`（detail_type `interaction`）と表示されていましたが、現在は `type="notice"`、`detail_type="discord_interaction"` に変更され、対話データは `discord_interaction` フィールドに保持されます。

### Api 署名対応

| 動作 | 署名 | 説明 |
|------|------|------|
| get_channel_info | `(guild_id, channel_id)` | 新しい署名 guild_id が先頭に、1 つの位置引数のみ渡した場合は旧署名を互換する（channel_id と見なす） |
| get_channel_list | `(guild_id, joined_only=False)` | 新たに joined_only キーワード引数を追加 |
| get_guild_info / get_guild_list | - | data は `guild_id` / `guild_name`（旧 `group_id` / `group_name` フィールドは保持、既存の呼び出し元への破壊を避ける） |

### エラーコード規格化

エラーコードは SDK の標準化に従っており（元の `34000` は使用されない）:

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（接続失敗、タイムアウトなど） |
| 34100 | プラットフォーム拒否（元の応答は `discord_raw` フィールドに保持） |
| 10002 | 不支持の動作（`get_guild_member_list` / `set_guild_name` / `get_channel_member_info` / `get_channel_member_list` / `leave_channel` は明示的に返す、Discord REST には対応する意味がない） |
| 10003 | パラメータエラー（例: メッセージ登録表に該当するコンテキストがないため撤回できない） |

## v5 ファンタジー更新（4.2.0）

このアダプターは v5 ファンタジーに完全に整合しています（増分アップグレード、API 兼容）：

- **BaseConverter 継承**: 転換器の共通フィールドはフレームワーク `build_base_event` で構築されます。
- **Api DSL**: 標準 Api 動作のマッピング（以下を参照）
- **標準 keyboard 段**: Discord components（action row + buttons）に変換；.Keyboard(rows) 修飾子は汎用構造を受け入れる
- **対話コールバックの標準フィールド**: INTERACTION_CREATE イベントには interaction_id / button_data が含まれる
- **spawn_background タスクの所属**: 接続タスクは runtime.spawn_background を使用
- **フレームワークのソフト依存**: ErisPulse>=2.7.1 を実行時に検出して警告を表示；起動時にバージョンログを出力

### 標準 Api 動作

```python
from ErisPulse import sdk
discord = sdk.adapter.get("discord")

result = await discord.Api.get_self_info()                # GET /users/@me
result = await discord.Api.get_user_info(user_id)         # GET /users/{id}
result = await discord.Api.get_guild_info(guild_id)       # GET /guilds/{id}（data は guild_id / guild_name を使用）
result = await discord.Api.get_guild_list()               # GET /users/@me/guilds
result = await discord.Api.get_channel_info(guild_id, channel_id)  # GET /channels/{id}（新しい署名 guild_id が先頭）
result = await discord.Api.get_channel_list(guild_id)     # GET /guilds/{id}/channels
result = await discord.Api.get_guild_member_info(gid, uid)
await discord.Api.delete_message(message_id)              # 登録表は自動的に channel_id を補完
await discord.Api.leave_guild(guild_id)
result = await discord.Api.Using("main").get_self_info()
```

### ボタン（keyboard / components）

```python
rows = [[{"label": "クリック", "type": "callback", "data": "btn:1"},
         {"label": "公式サイト",  "type": "link",     "data": "https://example.com"}]]
await discord.Send.To("channel", channel_id).Keyboard(rows).Text("選択してください")
# 自動的に components に変換：callback → custom_id / link → url
```

---

## 支援されるメッセージ送信タイプ

すべての送信メソッドはチェーン構文で実行されます。例：

```python
from ErisPulse.Core import adapter
discord = adapter.get("discord")

await discord.Send.To("group", channel_id).Text("Hello World!")
```

サポートされる送信タイプは以下の通りです：

- `.Text(text: str)`：テキストメッセージを送信。
- `.Embed(embed: dict | list)`：埋め込みメッセージを送信、1 つまたは複数の Embed をサポート。
- `.MergeForward(nodes, title="合併チャット記録")`：埋め込みメッセージを送信（タイトル + 各メッセージが 1 つの field、25 fields まで、value は 1024 文字まで）。
- `.Image(file: bytes | str, filename: str = "image.png")`：画像を送信、バイトデータまたは URL をサポート。
- `.File(file: bytes | str, filename: str = None)`：ファイルを送信、バイトデータまたは URL をサポート。
- `.Reply(content: str, message_id: str)`：指定メッセージに返信（便利な終端メソッド）。
- `.Raw_ob12(message: List[Dict], **kwargs)`：OneBot12 形式メッセージを送信。
- `.Raw_json(json_str: str)`：任意の Discord API リクエスト JSON を送信。

### チェーン修飾メソッド（複数使用可能）

チェーン修飾メソッドは `self` を返し、チェーンで呼び出すことができます。最終送信メソッドの前に呼び出す必要があります：

- `.Reply(message_id: str)`：指定メッセージに返信（引用）、`message_reference` を設定。
- `.At(user_id: str)`：指定ユーザーを @、`<@user_id>` に変換、複数回呼び出せる。
- `.AtAll()`：全員を @、`@everyone` に変換。

### チェーン呼び出しの例

```python
# 基本送信
await discord.Send.To("group", channel_id).Text("Hello")

# メッセージに返信
await discord.Send.To("group", channel_id).Reply(msg_id).Text("返信メッセージ")

# 便利な返信（1ステップ）
await discord.Send.To("group", channel_id).Reply("返信内容", msg_id)

# ユーザーを @
await discord.Send.To("group", channel_id).At("user_id").Text("こんにちは")

# 複数ユーザーを @
await discord.Send.To("group", channel_id).At("user1").At("user2").Text("複数ユーザー@")

# 全員を @
await discord.Send.To("group", channel_id).AtAll().Text("お知らせ")

# 組み合わせ
await discord.Send.To("group", channel_id).Reply(msg_id).At("user_id").Text("複合メッセージ")

# 埋め込みメッセージ
embed = {
    "title": "通知",
    "description": "これは埋め込みメッセージです",
    "color": 5814783,
    "fields": [{"name": "フィールド", "value": "値", "inline": True}],
}
await discord.Send.To("group", channel_id).Embed(embed)

# 画像送信
await discord.Send.To("group", channel_id).Image("https://example.com/image.png")
```

### プライベートメッセージ送信

プライベートメッセージ送信時、アダプターは自動的に DM チャンネルを作成します：

```python
# プライベートメッセージ送信
await discord.Send.To("user", user_id).Text("プライベートメッセージ内容")
await discord.Send.To("user", user_id).Embed(embed)
```

### メッセージ操作

```python
# メッセージ撤回
await discord.Send.To("group", channel_id).Recall(msg_id)

# OneBot12 形式
ob12_msg = [
    {"type": "text", "data": {"text": "Hello "}},
    {"type": "mention", "data": {"user_id": "user_id"}},
]
await discord.Send.To("group", channel_id).Raw_ob12(ob12_msg)
```

## 送信メソッドの戻り値

すべての送信メソッドは Task オブジェクトを返し、await で送信結果を取得できます。返り値は ErisPulse アダプターの標準化された返り値規格に従います：

```python
{
    "status": "ok",           // 実行状態: "ok" または "failed"
    "retcode": 0,             // 返り値コード（0 が成功）
    "data": {...},            // Discord API 原始応答
    "message_id": "xxx",      // メッセージID（送信メッセージの場合）
    "message": "",            // エラーメッセージ
    "discord_raw": {...}      // 原始応答データ
}
```

### エラーコードの説明

| retcode | 説明 |
|---------|------|
| 0 | 成功 |
| 33001 | ネットワークエラー（接続失敗、タイムアウトなど） |
| 34100 | プラットフォーム拒否（権限不足、パラメータエラーなど、元の応答は `discord_raw` フィールドに保持） |
| 10002 | 不支持の動作（「標準化対応（4.4.3）」のエラーコード規格を参照） |
| 10003 | パラメータエラー（例: 撤回時に該当するメッセージコンテキストがない） |

## 特有のイベントタイプ

`platform == "discord"` を検証してから本プラットフォームの特性を使用する必要があります。

### 核心的な違い

1. **サーバー/チャンネル構造**: Discord はサーバー（Guild）とチャンネル（Channel）の2層構造を使用し、チャンネルがメッセージの基本的な送信ターゲットです。
2. **Gateway イベント**: すべてのイベントは WebSocket Gateway を通じて受信され、Opcode + Dispatch 仕組みを使用します。
3. **Intents 訂正**: 位マスクを使用してイベントタイプを訂正し、`MESSAGE_CONTENT` は Privileged 権限が必要です。
4. **メッセージセグメントタイプ**: テキスト、画像、ファイル、ビデオ、音声、Embed、Sticker などのメッセージセグメントをサポートします。
5. **Mention 形式**: Discord は `<@user_id>` 形式を使用してユーザーのメンションを表します。

### 拡張フィールド

すべての特有のフィールドは `discord_` で始まります：
- `discord_raw`: 原始 Discord イベントデータ
- `discord_raw_type`: 原始イベントのタイプ名（例: `MESSAGE_CREATE`）
- `discord_guild_id`: サーバー ID
- `discord_channel_id`: チャンネル ID
- `discord_interaction`: 対話イベントデータ（INTERACTION_CREATE）

### detail_type マッピング

| Discord の状況 | detail_type | 説明 |
|---|---|---|
| チャンネルメッセージ | `channel` | ErisPulse 拡張タイプ |
| プライベートメッセージ（DM） | `private` | OneBot12 標準タイプ |

### イベントタイプマッピング

| Discord イベント | OneBot12 type | detail_type | 説明 |
|---|---|---|---|
| MESSAGE_CREATE | message | channel/private | メッセージ作成 |
| MESSAGE_UPDATE | message | channel/private | メッセージ編集（id は `MESSAGE_UPDATE:元のid`） |
| MESSAGE_DELETE | notice | group_message_delete / private_message_delete | メッセージ削除（id は `MESSAGE_DELETE:元のid`） |
| MESSAGE_REACTION_ADD | notice | group_message_reaction_add | リアクション追加（id は `MESSAGE_REACTION_ADD:元のid`） |
| MESSAGE_REACTION_REMOVE | notice | group_message_reaction_remove | リアクション削除（id は `MESSAGE_REACTION_REMOVE:元のid`） |
| GUILD_MEMBER_ADD | notice | group_member_increase | メンバー加入 |
| GUILD_MEMBER_REMOVE | notice | group_member_decrease | メンバー離脱 |
| GUILD_MEMBER_UPDATE | notice | group_member_update | メンバー情報更新 |
| GUILD_ROLE_CREATE | notice | group_role_create | ロール作成 |
| GUILD_ROLE_DELETE | notice | group_role_delete | ロール削除 |
| CHANNEL_CREATE | notice | channel_create | チャンネル作成 |
| CHANNEL_DELETE | notice | channel_delete | チャンネル削除 |
| INTERACTION_CREATE | notice | discord_interaction | 対話（ボタン、コマンドなど） |

> 4.4.3 以降、MESSAGE_UPDATE / MESSAGE_DELETE、REACTION_ADD / REMOVE などの非作成イベントの
> `id` はすべて `"イベント名:元のid"` に変更され、MESSAGE_CREATE イベントの id と衝突してフレームワークで重複排除されるのを防ぎます。

### 特殊フィールドの例

```python
# チャンネルテキストメッセージ
{
  "type": "message",
  "detail_type": "channel",
  "user_id": "送信者ID",
  "user_nickname": "ユーザー名",
  "group_id": "チャンネルID",
  "message_id": "メッセージID",
  "self": {
    "platform": "discord",
    "user_id": "BotID",
    "account_id": "default"
  },
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_guild_id": "サーバーID",
  "discord_channel_id": "チャンネルID",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello"
}

# プライベートメッセージ
{
  "type": "message",
  "detail_type": "private",
  "user_id": "送信者ID",
  "user_nickname": "ユーザー名",
  "message_id": "メッセージID",
  "discord_raw": {...},
  "discord_raw_type": "MESSAGE_CREATE",
  "discord_channel_id": "DMチャンネルID",
  "message": [
    {"type": "text", "data": {"text": "プライベートメッセージ内容"}}
  ],
  "alt_message": "プライベートメッセージ内容"
}

# Embed を含むメッセージ
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "discord_embed", "data": {"embed": {...}}}
  ],
  "alt_message": "[埋め込みメッセージ]"
}

# 附件を含むメッセージ
{
  "type": "message",
  "detail_type": "channel",
  "message": [
    {"type": "text", "data": {"text": "この画像を見てください"}},
    {"type": "image", "data": {"file": "画像URL", "url": "画像URL", "file_name": "image.png"}}
  ],
  "alt_message": "この画像を見てください[画像]"
}
```

### メッセージセグメントタイプ

Discord メッセージの内容は `content`、`attachments`、`embeds` フィールドに基づいて対応するメッセージセグメントに自動変換されます：

| 源 | 変換タイプ | 説明 |
|---|---|---|
| content テキスト | `text` | テキスト内容 |
| content `<@id>` | `mention` | ユーザーのメンション |
| content `<@&id>` | `discord_role_mention` | ロールのメンション |
| content `<#id>` | `discord_channel_mention` | チャンネルのメンション |
| attachments (image/*) | `image` | 画像の添付 |
| attachments (video/*) | `video` | ビデオの添付 |
| attachments (audio/*) | `audio` | 音声の添付 |
| attachments (その他の) | `file` | ファイルの添付 |
| embeds | `discord_embed` | 埋め込みメッセージ |
| sticker_items | `discord_sticker` | ステッカー |

### discord_embed メッセージセグメント

```json
{
  "type": "discord_embed",
  "data": {
    "embed": {
      "title": "タイトル",
      "description": "説明",
      "color": 12345,
      "fields": [...],
      "image": {"url": "..."},
      "thumbnail": {"url": "..."},
      "footer": {"text": "..."}
    }
  }
}
```

## Gateway 接続

### 接続フロー

1. `GET /gateway/bot` を呼び出して WebSocket ゲートウェイ URL を取得する
2. `wss://gateway.discord.gg/?v=10&encoding=json` に接続する
3. opcode 10 HELLO を受信: `heartbeat_interval` を含む
4. opcode 2 IDENTIFY を送信: token、intents、properties を含む
5. ハートビートループを開始: `heartbeat_interval` で定期的に opcode 1 Heartbeat を送信
6. opcode 0 Dispatch を受信: イベント配信（`t`=イベント名, `s`=シーケンス番号, `d`=データ）
7. opcode 11 Heartbeat ACK を受信: ハートビート確認

### Opcode 説明

| Opcode | 名称 | 方向 | 説明 |
|--------|------|------|------|
| 0 | Dispatch | 受信 | イベント配信（`t`、`s`、`d` フィールドを含む） |
| 1 | Heartbeat | 送信/受信 | ハートビート（最後の seq を含む） |
| 2 | Identify | 送信 | 身分認証 |
| 6 | Resume | 送信 | セッションの再開 |
| 7 | Reconnect | 受信 | サーバーからの再接続要求 |
| 9 | Invalid Session | 受信 | 無効なセッション |
| 10 | Hello | 受信 | 接続ハンドシェイク（`heartbeat_interval` を含む） |
| 11 | Heartbeat ACK | 受信 | ハートビート確認 |

### 切断再接続と RESUME

- 接続が切断された後、アダプターは自動的に再接続を試みます
- 以前に `session_id` があれば、優先的に RESUME（opcode 6）でセッションを再開します
- RESUME は `token`、`session_id`、最後の `seq` を含み、切断後に漏れたイベントを再送します
- opcode 7（Reconnect）を受信した場合、セッションの状態を保持して再接続します
- opcode 9（Invalid Session）を受信し、`d=false` の場合、セッションをクリアして再 IDENTIFY を行います

### ハートビートメカニズム

- HELLO を受信した後、`heartbeat_interval * random()` ミリ秒待って最初のハートビートを送信します
- その後、`heartbeat_interval` ミリ秒ごとにハートビートを送信します
- ハートビートは最後の `seq` 値を含みます（opcode 1、`d: seq`）
- ハートビートを送信した後、`heartbeat_interval` 内に ACK（opcode 11）が受信されない場合、接続異常と見なし、再接続します

## 使用例

### チャンネルメッセージの処理

```python
from ErisPulse.Core.Event import message
from ErisPulse import sdk

discord = sdk.adapter.get("discord")

@message.on_message()
async def handle_group_msg(event):
    if event.get("platform") != "discord":
        return

    text = event.get_text()
    channel_id = event.get("group_id")

    if text == "hello":
        await discord.Send.To("group", channel_id).Text("Hello!")
```

### プライベートメッセージの処理

```python
@message.on_message()
async def handle_private_msg(event):
    if event.get("platform") != "discord":
        return
    if not event.is_dm():
        return

    text = event.get_text()
    user_id = event.get("user_id")

    await discord.Send.To("user", user_id).Text(f"あなたが言った: {text}")
```

### Embed メッセージの送信

```python
embed = {
    "title": "サーバーのお知らせ",
    "description": "ErisPulse Discord アダプターをご利用いただきありがとうございます",
    "color": 3447003,
    "fields": [
        {"name": "バージョン", "value": "4.4.3", "inline": True},
        {"name": "フレームワーク", "value": "ErisPulse", "inline": True},
    ],
    "footer": {"text": "Powered by ErisPulse"},
    "timestamp": "2025-01-01T00:00:00.000Z",
}
await discord.Send.To("group", channel_id).Embed(embed)
```

### Discord 特有のメソッドの使用

```python
@message.on_message()
async def handle(event):
    if event.get("platform") != "discord":
        return

    channel_id = event.get_channel_id()
    guild_id = event.get_guild_id()
    is_dm = event.is_dm()
    embeds = event.get_embeds()
    attachments = event.get_attachments()

    if embeds:
        await discord.Send.To("group", channel_id).Text(
            f"埋め込みメッセージ {len(embeds)} 個を受け取りました"
        )
```

### 対話イベントの処理

4.4.3 以降、INTERACTION_CREATE は `notice` / `discord_interaction` として配信されます：

```python
from ErisPulse.Core.Event import notice

@notice.on_notice()
async def handle_interaction(event):
    if event.get("platform") != "discord":
        return
    if event.get("detail_type") != "discord_interaction":
        return

    interaction = event.get_interaction_data()  # event["discord_interaction"] と同等
    if interaction.get("type") == 3:  # MESSAGE_COMPONENT
        await event.reply("ボタンがクリックされました！")
```



### Webhook 适配

# Webhook 通用橋接アダプタープラットフォームの機能ドキュメント

WebhookAdapter はプロトコルレベルの双方向橋渡しアダプターであり、特定のプラットフォームに紐付いていません。入力側では外部システムからの POST リクエストの JSON を OneBot12 イベントに変換し、出力側ではモジュールの Send から外部システムに POST します。

---

## ドキュメント情報

- 対応モジュールバージョン: 4.3.2
- メンテナー: ErisPulse
- 最終更新日: 2026-11-10

## 基本情報

- プラットフォーム概要: HTTP リクエストを発行できる任意のシステムが、このアダプターを通じて ErisPulse に接続できます。
- アダプター名: WebhookAdapter
- プラットフォーム識別子: `webhook`
- 多アカウント対応: 各アカウントは独立した橋渡し設定 (bot_id / callback_path / outgoing_url / secret) です。
- フレームワーク要件: ソフト依存 `ErisPulse>=2.7.1`（実行時検出と警告、強制はしません）。

## 接続済みプラットフォーム機能

- **入力**: 外部システムが callback_path に POST → OneBot12 イベントに変換 (json/text セグメントを透過)
- **出力**: モジュール Send → outgoing_url に POST (双方向橋渡し)
- **API**: 橋渡し認証情報と実行状態 (最小限)

## v5 フレームワーク更新 (4.2.0)

- **Api DSL 最小集**: get_self_info/get_status/get_version/get_supported_actions
- **フレームワークソフト依存**: 実行時に ErisPulse>=2.7.1 を検出し警告を出力し、起動時にバージョンログを出力
- インポートパスを Core.Bases に更新

## 標準化対応 (4.3.2)

レスポンス構造とエラーコードは [API レスポンス規格](../standards/api-response.md)に従います。

### イベントフィールド

- **メッセージイベントの `message_id` 補完**: 入力側 body の `message_id` を優先的に透過し、不足時は uuid を補完 (下流で message_id で重複除去/返信時に空値を取得しないように)
- **イベント注入 `self.account_id`** (アカウント名): 多アカウント環境下で `event.reply()` は該当イベントを受理したアカウントに自動ルーティング
- **`alt_message` 空文字列補完**: 入力側で提供されない場合、空文字列を補完し、標準フィールドの完全性を保証
- **JSON セグメント名を `webhook_json` に変更**: プラットフォームプレフィックスなしの裸の `json` セグメントはすべて `webhook_json` に統一 (プラットフォーム拡張セグメント命名規則に従う)
- Converter はフレームワーク `BaseConverter` を再利用 (共通フィールドは `build_base_event` で統一構築)
- `get_self_info` で標準フィールドを補完: `user_id` (アカウント bot_id) / `user_name` / `user_displayname` (`webhook:{アカウント名}`)

### エラーコード規格

| retcode | 含意 | 説明 |
|---------|------|------|
| 0 | 成功 | — |
| 33001 | ネットワークエラー | 出力先 POST 目標失敗 (接続/タイムアウトなど) |
| 10003 | パラメータエラー | 出力 URL 未設定、パラメータ不足など |

### アカウントと多アカウント

- `call_api` は両対応アカウントフィールドをサポート: `account_id` (標準名) / `_account_id` (旧名), フレームワーク ApiDSL (`Api.Using(...)`) は自動的に適応
- `Send` は `send_context` (イベントアカウントのデフォルト) を読み込む: イベントコンテキストから `Send` を呼び出す際、デフォルトで元のアカウントにフォールバック

## 概要

Webhook アダプターは**プロトコルレベルの橋渡し**であり、特定のプラットフォームに紐付いていません。HTTP を通じて送受信を行い、HTTP リクエストを発行できる任意のシステムが ErisPulse に接続できます。

```
入力方向                                出力方向
────────                                ────────
外部システム                                ErisPulse モジュール
   │                                       │
   │ POST JSON                             │ Send.Text(...)
   ▼                                       ▼
┌──────────────────────────────────────────────────┐
│              WebhookAdapter                       │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ 入力ルーティング          │   │ 出力転送          │    │
│  │ GET  (健康チェック)   │   │ client.post()    │    │
│  │ POST (イベント受信)   │   │ → outgoing_url   │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
│           │                      │               │
│           ▼                      │               │
│  ┌──────────────────┐   ┌──────────────────┐    │
│  │ WebhookConverter │   │ Send クラス          │    │
│  │ JSON → OneBot12  │   │ メッセージセグメント → JSON    │    │
│  └────────┬─────────┘   └────────▲─────────┘    │
└───────────┼──────────────────────┼───────────────┘
            ▼                      │
     adapter.emit(event)    call_api("send_message")
            │                      │
            ▼                      │
       ErisPulse イベントシステム ◄────────┘
```

## 多アカウントモデル

各アカウントは独立した橋渡し設定であり、互いに干渉しません:

| アカウント | bot_id | callback_path | outgoing_url | secret |
|------|--------|---------------|--------------|--------|
| `default` | `webhook_bot` | `/webhook/default` | `https://a.com/recv` | `key1` |
| `discord` | `discord_bot` | `/webhook/discord` | `https://b.com/send` | `key2` |

各アカウントは起動時に独立してルーティングを登録し、独立して connect を emit します。

### アカウント設定フィールド

| フィールド | 必須 | 説明 |
|------|------|------|
| `bot_id` | いいえ | Bot 身元 ID (この橋渡しで表示される) |
| `callback_path` | いいえ | 入力側コールバックパス ( `{account}` プレースホルダをサポート) |
| `outgoing_url` | いいえ | 出力先 URL (モジュールがメッセージを送信する際、このアドレスに POST) |
| `secret` | いいえ | 認証キー (空欄の場合は検証を無効化; 設定画面では暗号化して保存) |

## 入力プロトコル

### 1. 健康チェック (GET)

- **パス**: `{callback_path}`
- **メソッド**: `GET`
- **認証**: なし
- **レスポンス**:

```json
{"status": "ok", "account": "default"}
```

### 2. イベント受信 (POST)

- **パス**: `{callback_path}`
- **メソッド**: `POST`
- **Content-Type**: `application/json`
- **認証** (secret 設定時): Header `X-Webhook-Secret` または Query `?secret=`

#### リクエスト Body

```json
{
  "user_id": "u123",
  "user_nickname": "ユーザー名",
  "group_id": "グループID（グループ会話のみ）",
  "detail_type": "private",
  "message_id": "オプション、イベントの message_id として透過 (不足時は uuid で補完)",
  "alt_message": "オプション、純文本文の代替",
  "message": [
    {"type": "text", "data": {"text": "メッセージ内容"}}
  ],
  "raw": {}
}
```

| フィールド | 必須 | 説明 |
|------|------|------|
| `user_id` | はい | 送信者 ID |
| `user_nickname` | いいえ | 送信者ニックネーム |
| `group_id` | いいえ | グループ/チャンネル ID (グループ会話時に提供) |
| `detail_type` | いいえ | 会話タイプ (`private`/`group`)、未指定時はアカウントのデフォルト値を使用 |
| `message_id` | いいえ | メッセージ ID、イベントのトップレベル `message_id` として透過 (不足時は uuid で補完) |
| `alt_message` | いいえ | 純文本文の代替、不足時は空文字列で補完 |
| `message` | はい | OneBot12 メッセージセグメント配列 |
| `raw` | いいえ | 元データ、`webhook_raw` にそのまま保存 |

#### レスポンス

```json
{"status": "ok"}
```

エラーの場合は HTTP ステータスコードを含むレスポンス:

| ステータスコード | 含意 |
|--------|------|
| 400 | 無効な JSON / body がオブジェクトでない |
| 401 | 認証失敗 |
| 404 | 未知のアカウント |
| 500 | イベント配信失敗 |

### 3. フィールドマッピング (入力 JSON → OneBot12 イベント)

| 入力 JSON | OneBot12 イベントフィールド | 説明 |
|-----------|-------------------|------|
| — | `id` | 自動生成 |
| — | `time` | 現在の Unix タイムスタンプ (秒) |
| — | `type` | 固定 `message` |
| `detail_type` | `detail_type` | 未指定時はアカウントのデフォルト値を使用 |
| — | `platform` | 固定 `webhook` |
| — | `self.platform` | 固定 `webhook` |
| — | `self.user_id` | アカウントの `bot_id` |
| — | `self.account_id` | アカウント名 (4.3.2 で注入、多アカウントルーティング) |
| `user_id` | `user_id` | 透過 |
| `user_nickname` | `user_nickname` | 透過 (オプション) |
| `group_id` | `group_id` | 透過 (オプション) |
| `message_id` | `message_id` | 透過、不足時は uuid で補完 (4.3.2) |
| `alt_message` | `alt_message` | 透過、不足時は空文字列で補完 (4.3.2) |
| `message` | `message` | 透過 |
| 完全な body | `webhook_raw` | 元のリクエスト |
| アカウント名 | `webhook_account` | イベントを生成したアカウント名 |
| `type` または `message` | `webhook_raw_type` | 元のイベントタイプ |

> 裸の `json` セグメント (`{"type": "json", ...}`) は、入力/出力の両側で `webhook_json` セグメントに統一されます。

## 出力プロトコル

### 1. メッセージ送信

モジュールが `Send.To(...).Text(...)` などのメソッドを呼び出すと、アダプターは `outgoing_url` に POST を送信します:

- **メソッド**: `POST`
- **Content-Type**: `application/json`
- **認証ヘッダー** (secret 設定時): `X-Webhook-Secret: {secret}`

#### リクエスト Body

```json
{
  "target_type": "private",
  "target_id": "target_user_id",
  "account": "default",
  "message": [
    {"type": "text", "data": {"text": "メッセージ内容"}}
  ],
  "timestamp": 1700000000
}
```

| フィールド | 説明 |
|------|------|
| `target_type` | 目標タイプ (`Send.To(type, id)` から取得、未指定時はアカウントのデフォルト値を使用) |
| `target_id` | 目標 ID (`Send.To` から取得) |
| `account` | 送信アカウント名 |
| `message` | OneBot12 メッセージセグメント配列 |
| `timestamp` | 送信タイムスタンプ (秒) |

### 2. レスポンス標準化

アダプターは出力先からのレスポンスを ErisPulse の標準レスポンス形式に標準化します:

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "...", ...},
  "message_id": "...",
  "message": "",
  "webhook_raw": {}
}
```

ターゲットレスポンス JSON の `message_id` フィールドからメッセージ ID を抽出します。ターゲットが `message_id` を返さない場合、空文字列になります。

リクエストが失敗した場合はエラーレスポンスを返します (`status: "failed"`, `retcode: 33001`)。

## Send メソッド

| メソッド | 説明 |
|------|------|
| `Text(text)` | テキストを送信し、`[{"type":"text","data":{"text":text}}]` にラップ |
| `Image(file)` | 画像を送信し、`[{"type":"image","data":{"file":file}}]` にラップ |
| `Raw_ob12(message)` | OneBot12 原始メッセージセグメントを送信 |
| `Json(data)` | 原始 JSON を透過し、`[{"type":"webhook_json","data":{"raw":data}}]` にラップ |

`At` / `AtAll` / `Reply` 修飾子はフレームワークの基底クラスから提供され、`_apply_modifiers` でメッセージセグメントにマージされます。

## イベント拡張メソッド (WebhookEventMixin)

| メソッド | 説明 |
|------|------|
| `get_raw_data()` | 元のリクエスト body (`webhook_raw`) を取得 |
| `get_detail_type()` | 会話タイプを取得 |
| `get_webhook_account()` | イベントを生成したアカウント名を取得 |

## 機能マトリックス

| 機能 | 対応状況 |
|------|----------|
| 多アカウント | ✅ 各アカウントは独立した橋渡し |
| 入力側認証 | ✅ ヘッダー / クエリの両モード |
| 健康チェック | ✅ GET でステータスを返す |
| 出力側認証 | ✅ ヘッダーに secret を含める |
| OneBot12 標準イベント | ✅ 完全な標準フィールド |
| Meta イベント | ✅ connect / disconnect |
| ルーティング発見 | ✅ `webhook` 名前空間に登録 |
| WebSocket | ❌ HTTP 限定 |
| メディアアップロード | ❌ URL 透過のみ、バイナリを代行送信しない |

## 注意事項

1. **単方向出力**: `outgoing_url` が空欄の場合、このアカウントは入力側のみの受信となり、送信操作はエラーを返します (`retcode: 10003`)
2. **秘钥セキュリティ**: `secret` は設定で暗号化して保存 (metadata secret), 通信は HTTPS を推奨
3. **パスのユニーク性**: 複数アカウントの `callback_path` は互いに異なる必要があり、ルーティングの衝突を避ける
4. **멱등性**: アダプターは入力イベントの重複除去を保証しない、外部システムはリトライ処理を独自に行う必要がある
5. **タイムアウト**: 出力リクエストは ErisPulse 内部の `client` を使用し、グローバルのタイムアウト設定を継承



### 微信公众号适配

# 微信公众号（WechatMp）アダプター - プラットフォーム特性ドキュメント

## 基本情報
- モジュール名: `ErisPulse-WechatMpAdapter`
- プラットフォーム識別子: `mp`（別名: `wechat_mp`）
- モジュールバージョン: 4.3.2
- 維持管理者: ErisPulse
- 最終更新: 2026-11-10
- 依存: `cryptography`

## v5 ファンタジーの更新（4.2.0）

- **BaseConverter の継承**：コンバーターの共通フィールドはフレームワークの build_base_event によって構築されます。
- **Api DSL の最小セット**：get_self_info（appid）/get_status/get_version/get_supported_actions
- **フレームワークのソフト依存**：ErisPulse>=2.7.1 を実行時に検出し、警告を表示します。起動時にバージョンのログを出力します。

## 標準化の整列 (4.3.2)

レスポンス構造とエラーコードは、[API レスポンス規格](../standards/api-response.md)に従います。

### メッセージイベントの補完 message_id

メッセージイベントの最上層に標準の `message_id` フィールドを追加します（WeChat の MsgId を取得し、不足している場合は空文字列で補完）。モジュールは `mp_msg_id` から読み取る必要はありません。

### 標準レスポンス

すべての `call_api` / Send 呼び出しは、標準レスポンスを返します：`status` / `retcode` / `data` / `message_id` / `message` + 最上層の `mp_raw`。**パッシブリプライが成功した場合、`message` は空文字列です**（`data.passive_reply=true` はパッシブリプライとしてブロックされたことを示します）。

### エラーコード規格

| retcode | 含意 | 説明 |
|---------|------|------|
| 0 | 成功 | — |
| 34100 | プラットフォームの失敗 | WeChat API が errcode != 0 を返した場合；**元の errcode は `mp_raw` に保持されます**。token の取得失敗もこのコードに属します |
| 10003 | パラメータのエラー / 未認証 | 認証されていないアカウント（`verified=false`）がパッシブリプライのコンテキスト外でカスタマーメッセージを呼び出した場合 |

### アカウントと複数アカウント

- `call_api` は、標準名の `account_id` と旧名の `_account_id` の両方のアカウントフィールドをサポートします。フレームワーク ApiDSL（`Api.Using(...)`）が自動的に適応します
- `Send` は `send_context`（イベントアカウントをデフォルトとして）を読み取ります
- `get_self_info` は、標準フィールドを補完します：`user_id`（WeChat 公衆号 AppID）/ `user_name` / `user_displayname`（`wechatmp:{アカウント名}`）

---

### 既に接続済みのプラットフォーム機能

- **受信**：WeChat 公衆号のコールバックメッセージと、フォロー/アンフォローなどのイベント（明文/セキュリティモード）、署名検証
- **送信**：カスタマーメッセージ（Text/Image など、Send DSL を経由）
- **API**：アカウント情報（appid）と実行状態（最小限のセット）

## 支援するメッセージ送信タイプ

| 方法 | 説明 | WeChat API |
|------|------|---------|
| `Text(text)` | テキストを送信 | カスタマーサービスメッセージ `message/custom/send` |
| `Image(file)` | 画像を送信（media_id の自動アップロード） | カスタマーサービスメッセージ + `media/upload` |
| `Voice(file)` | 音声を送信（media_id の自動アップロード） | カスタマーサービスメッセージ + `media/upload` |
| `Video(file, title, description)` | 動画を送信（media_id の自動アップロード） | カスタマーサービスメッセージ + `media/upload` |
| `Music(url, title, description, ...)` | 音楽を送信 | カスタマーサービスメッセージ |
| `News(articles)` | 画像付きテキストメッセージを送信 | カスタマーサービスメッセージ |
| `Template(template_id, data, url)` | テンプレートメッセージを送信 | `message/template/send` |
| `Menu(head_content, list, tail_content)` | メニューメッセージを送信 | カスタマーサービスメッセージ `msgmenu` |
| `Raw_ob12(message)` | OneBot12 標準メッセージセグメントを送信 | - |

### メディアファイルの説明
- 3 種類のパラメータタイプをサポート：
  - `str` URL（`http://` / `https://` で始まる）：自動的にダウンロードしてアップロード
  - `str` ローカルファイルパス：自動的に読み取ってアップロード
  - `bytes` バイナリデータ：直接アップロード
  - `str` media_id：`media:` というプレフィックスを付けることで、既にアップロードされた media_id を再利用可能
- アップロード後に有効期限 3 日の臨時素材 `media_id` が取得できる

### 重要な制限事項
- カスタマーサービスメッセージは、ユーザーと公式アカウントが対話した後 **48 時間以内** にのみ送信可能
- 48 時間を超える場合は、テンプレートメッセージを使用する必要がある（ユーザーの許可が必要）
- 認証されていないサービスアカウント（`verified=false`）は、自動送信ができない。受動的な返信のみ可能（上記の「認証済みサービスアカウントと受動的な返信」を参照）

## イベントの種類

### メッセージイベント (message)
すべてのユーザーのメッセージは `detail_type: private`（公式アカウントの1対1の場面）です。

| 微信 MsgType | メッセージセグメントの種類 | 説明 |
|-------------|-----------|------|
| `text` | `text` | テキストメッセージ |
| `image` | `image` | 画像メッセージ |
| `voice` | `voice` | 音声メッセージ（音声認識結果を含む） |
| `video` | `video` | ビデオメッセージ |
| `shortvideo` | `video` | 小型ビデオ（`mp_shortvideo`をマーク） |
| `location` | `location` | 地理位置メッセージ |
| `link` | `text` | リンクメッセージ（テキストに変換） |

### 通知イベント (notice)
イベントは `mp_event` フィールドで具体的な種類を識別します。

| 微信 Event | `mp_event` | 説明 |
|-----------|-----------|------|
| `subscribe` | `subscribe` | 公式アカウントをフォロー |
| `unsubscribe` | `unsubscribe` | フォローを解除 |
| `SCAN` | `scan` | パラメータ付きQRコードをスキャン |
| `LOCATION` | `location_report` | 地理位置を報告 |
| `CLICK` | `menu_click` | 自定義メニューをクリック |
| `VIEW` | `menu_view` | メニューのリンクに遷移 |
| `TEMPLATESENDJOBFINISH` | `template_send_finish` | テンプレートメッセージ送信結果 |
| `MASSSENDJOBFINISH` | `mass_send_finish` | 一斉送信メッセージ送信結果 |

## プラットフォーム拡張フィールド

イベントオブジェクト内の微信特有のフィールド（`mp_` で始まる）：

| フィールド | 型 | 説明 |
|------|------|------|
| `mp_raw` | str | 元の XML データ |
| `mp_raw_type` | str | 元のメッセージ/イベントの型 |
| `mp_msg_id` | str | 微信メッセージ ID |
| `mp_event` | str | イベントの型（イベント通知のみ） |
| `mp_event_key` | str | イベントのキー（メニューのクリック/スキャンなど） |
| `mp_to_user` | str | 受信者の微信号（公式アカウントの元のID） |
| `mp_from_user` | str | 送信者の OpenID |
| `mp_data` | dict | 解析後の XML ディクショナリデータ |

## イベント拡張メソッド

`register_event_mixin("mp", ...)` で登録すると、イベントオブジェクト上で直接以下のメソッドを呼び出すことができます。

| メソッド | 戻り値 | 説明 |
|------|--------|------|
| `get_openid()` | str | 送信者の OpenID |
| `get_msg_type()` | str | 微信の元のメッセージタイプ |
| `get_event()` | str | イベントタイプ（イベント通知のみ） |
| `get_content()` | str | メッセージの純粋なテキスト内容 |
| `get_raw_xml()` | str | 元の XML データ |

## 配置オプション

### 複数アカウントの設定

各アカウントは1つのWeChat公式アカウントに対応します：

```toml
[WechatMpAdapter.accounts.main]
appid = "wx1234567890abcdef"
appsecret = "your_app_secret_here"
token = "your_callback_token"
encoding_aes_key = ""                    # セキュリティモード/互換モードが必要な場合（43文字）
callback_path = "/mp/main"               # コールバックパス
verified = true                          # 認証済みサービスアカウントかどうか（アクティブ送信能力に影響）
enable = true

[WechatMpAdapter.accounts.secondary]
appid = "wx0987654321fedcba"
appsecret = "another_app_secret"
token = "another_callback_token"
callback_path = "/mp/secondary"
enable = true
```

### 設定フィールドの説明

| フィールド | 必須 | 説明 |
|------|------|------|
| `appid` | はい | 公式アカウントの AppID |
| `appsecret` | はい | 公式アカウントの AppSecret（secret） |
| `token` | いいえ | コールバック検証トークン（署名検証を有効にするために推奨） |
| `encoding_aes_key` | いいえ | メッセージの暗号化/復号化キー（43文字、セキュリティモードが必要） |
| `callback_path` | いいえ | コールバックパステンプレート、デフォルトは `/mp/{account}`、`{account}` はアカウント名に置換されます |
| `verified` | いいえ | 認証済み**サービスアカウント**かどうか、デフォルトは `true`（下記を参照） |
| `enable` | いいえ | 有効化するかどうか、デフォルトは true |

### 認証済みサービスアカウントと受動応答（verified）

- `verified = true`（デフォルト、認証済みサービスアカウント）：**カスタマーメッセージ**のアクティブ送信（48時間ウィンドウ内）とテンプレートメッセージを使用可能
- `verified = false`（未認証のサブスクリプションアカウント）：
  - カスタマーメッセージ / テンプレートメッセージは**webhook受動応答のコンテキスト内でのみ送信可能**（ユーザーからのメッセージを受信した後15秒以内、1回の応答のみ）——アダプターは送信を受動応答として自動的に捕捉します
  - アクティブ送信（例：定時タスク）は `retcode=10003` エラー（未認証）を返します

## 暗号化モードの説明

WeChat 公開アカウントは、3 つのメッセージの暗号化/復号化モードを提供しています。

| モード | 説明 | encoding_aes_key | 验証フィールド |
|------|------|-----------------|---------|
| 明文モード | XML を明文で送信 | 不要 | `signature` |
| 兼容モード | 明文と暗号文が同時に存在 | 選択 | `signature` / `msg_signature` |
| 安全モード | 全てを暗号化 | 必須 | `msg_signature` |

このアダプタは自動的に処理します：
- 明文モード：`signature` を検証し、XML を直接解析
- 安全/兼容モード：`Encrypt` フィールドを検出し、`msg_signature` を検証し、AES-256-CBC を使用して復号
- 復号には `cryptography` ライブラリが必要（dependencies に宣言済み）

## コールバックルート

アダプターは、有効なアカウントごとに2つのルート（GET + POST）を登録します。

- **GET**：WeChatサーバーの接続検証。署名を検証した後に `echostr` を返します。
- **POST**：ユーザーのメッセージとイベントを受け取ります。署名を検証→必要に応じて復号化→変換→emit

実際のアクセスパスには、モジュールのプレフィックスが自動的に追加されます。たとえば、ルートを `/mp/main` に登録した場合、実際のアクセスパスは `/mp_{account}_verify/mp/main` および `/mp_{account}_message/mp/main` になります。

## API レスポンス

すべての `call_api` 呼び出しは、標準化されたレスポンスを返します：

- 成功: `status: "ok"`, `retcode: 0`
- 失敗: `status: "failed"`, `retcode: 34100`（プラットフォームのエラー；**元の errcode は `mp_raw` に保持されます**）または `10003`（パラメータエラー / 認証されていない）
- 常に `mp_raw`（元のレスポンス）と、ルートレベルの `message_id`（存在しない場合は空文字列）が含まれます。

