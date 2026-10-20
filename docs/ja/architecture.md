# アーキテクチャ概要

このドキュメントでは、ErisPulse SDKの技術的アーキテクチャを可視化した図解により、フレームワークの設計思想とモジュール間の関係を迅速に理解できるようご案内します。

## SDKコアアーキテクチャ

以下の図は、SDKのコアモジュール構成とその関係を示しています：

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
| **Event** | イベントシステム。command / message / notice / request / metaの5種類のイベント処理、およびConversationによる多段対話処理を提供。|
| **Adapter** | アダプタマネージャー。複数プラットフォーム用アダプタの登録、起動、停止を管理。|
| **Module** | モジュールマネージャー。プラグインの登録、ロード、アンロードを管理。依存関係の宣言とトポロジカルソートをサポート。|
| **Lifecycle** | ライフサイクルマネージャー。イベント駆動のライフサイクルフックを提供。|
| **Storage** | SQLiteベースのキーバリューストレージシステム。一般的なSQLチェーンクエリをサポート。|
| **Config** | TOML形式の設定ファイル管理。|
| **Logger** | モジュール化されたログシステム。サブロガーをサポート。|
| **Router** | HTTP/WebSocketルーティング管理。抽象層を介して下層バックエンド（現在はFastAPI + Uvicorn）をカプセル化。デコレータルーティング、ミドルウェア、グループ、リクエスト制限、CORSをサポート。|
| **Client** | 統一されたHTTP/WSクライアント（2.8.0以前は`HttpClient`、互換エイリアスを保持）。抽象層を介して下層リクエストライブラリ（現在はaiohttp）をカプセル化。リクエスト統計、リトライ、ログ、WebSocketクライアント、ErisPulseの例外体系を提供。クライアントとサーバーのWebSocketは`WebSocketConnectionBase`基底クラスを共有。|

## 初期化フロー

以下の図は、`sdk.init()`の完全な初期化プロセスを示しています：

```mermaid
flowchart TD
    A["sdk.init()"] --> B["実行環境の準備"]
    B --> B1["設定ファイルの読み込み"]
    B1 --> B2["グローバル例外処理の設定"]
    B2 --> C["アダプタ & モジュールの検出"]
    C --> D{"並行的にロード"}
    D --> D1["PyPIからアダプタをロード"]
    D --> D2["PyPIからモジュールをロード"]
    D1 & D2 --> E["アダプタの登録"]
    E --> E1["アダプタの起動"]
    E1 --> F["モジュールの登録"]
    F --> F1{"依存関係の検証"}
    F1 -->|"依存関係が不足"| F2["モジュールをスキップし、警告を記録"]
    F1 -->|"依存関係が満たされている"| F3["トポロジカルソート<br/>（Kahnアルゴリズム + 優先度）"]
    F3 --> G["順序に従ってモジュールを初期化<br/>（インスタンス化 + on_load）"]
    F2 --> G
    G --> H["ルーティングサーバーの起動"]
    H --> K["準備完了"]
```

### 初期化フェーズの詳細

> 完全な初期化の流れを分解した（Finder / Loader / Manager / Router）、下層エントリポイント（`init()` / `init_task()` / `init_sync()`）と手動の完全起動は [起動フローと手動制御](advanced/startup.md) を参照してください。

## イベント処理フロー

以下の図は、プラットフォームからハンドラへのメッセージの完全な転送経路を示しています：

```mermaid
flowchart LR
    A["プラットフォームの元のメッセージ"] --> B["アダプタが受信"]
    B --> C["OneBot12標準に変換"]
    C --> D["adapter.emit()"]
    D --> E["ミドルウェアチェーンの実行"]
    E --> F{"イベントの分散"}
    F --> G1["command<br/>コマンドハンドラ"]
    F --> G2["message<br/>メッセージハンドラ"]
    F --> G3["notice<br/>通知ハンドラ"]
    F --> G4["request<br/>リクエストハンドラ"]
    F --> G5["meta<br/>メタイベントハンドラ"]
    G1 & G2 & G3 & G4 & G5 --> H["ハンドラのコールバック実行"]
    H --> I["event.reply()<br/>SendDSLを介した返信"]
    I --> J["アダプタがプラットフォームに送信"]
```

### イベント処理チェーンの詳細

上記の図は「結果」です。下に`adapter.emit()`を展開したフレームワークが**裏で何をしているか**を示します。これは3層の分散チェーンです：

```mermaid
sequenceDiagram
    participant P as プラットフォーム
    participant A as アダプタマネージャ層<br/>AdapterManager.emit
    participant T as ハンドラ Task 層<br/>_dispatch_handler_task
    participant E as Event モジュール層<br/>_process_event

    P->>A: 元のイベント
    A->>A: platform/type/detail_type + 元のフィールドを抽出
    A->>A: [Recv] 受信ログを記録
    A->>A: lifecycle.adapter.event.receive（初期のフック）
    A->>A: selfフィールドを処理（meta分岐 / Bot自動登録）
    A->>A: ミドルウェアチェーン（シーケンシャル、イベントデータを変更可能）
    A->>A: ハンドラを収集（具体的なタイプ + ワイルドカード *）
    A->>A: アイデンティティ認証 + スコープフィルタリング（Task作成前、静かに破棄/スキップ）
    A->>T: asyncio.create_task（fire-and-forget）
    A->>A: lifecycle.adapter.event.dispatched（最後のフック）
    T->>T: 並行信号量の取得（デフォルト上限 64）
    T->>E: Eventモジュールに登録されたハンドラを呼び出す
    E->>E: lifecycle.event.pre_process
    E->>E: ignore_self（メッセージイベントはデフォルトで自身を無視）
    E->>E: 優先度順にグループ化：高→低、グループ間はシーケンシャル、グループ内は並行
    E->>E: グループ内のコピーを実行 + フィールドをマージ（衝突警告）
    E->>E: グループ後、stop()でチェックし、より低い優先度をブロック
    T->>T: スローログ（1秒以上かかるとWARNING、wait_reply時間は除外）
```

**フレームワークが何をしたか、そしてあなたが介入できる部分：**

| フェーズ | フレームワークが何をしたか | 介入できる部分 |
|------|-------------|-----------|
| 受信 | 標準フィールドを抽出、`{platform}_raw`の元データを保持；`[Recv]`ログを記録 | `adapter.event.receive`を監視して初期イベントを取得 |
| selfフィールド | metaイベントはconnect/disconnect/heartbeat分岐；通常のイベントはBotを自動登録し`adapter.bot.online`をトリガー | `adapter.bot.online` / `bot.offline`を監視 |
| ミドルウェア | **シーケンシャル**に実行、戻り値がNoneでなければイベントデータを置換 | ミドルウェアを登録してイベントを変更/ブロック |
| 分散収集 | 先に具体的なタイプのハンドラを取得し、次に`*`ワイルドカードハンドラを取得 | — |
| アイデンティティ | 分散の入口はユーザー>会話>Bot>アダプタの順でイベントの受信を判定（`scope.is_identity_allowed`）、**拒否された場合、イベントは完全に破棄** | `ErisPulse.scope.identity`をバインド |
| スコープフィルタリング | モジュールのownerに基づいて`scope.is_allowed`を判定（会話レベル>Botレベル>プラットフォームレベル）、**通過しない場合、静かにスキップ** | スコープのホワイトリスト/ブラックリストを設定 |
| スケジューリング | 各マッチするハンドラは独立した`asyncio.Task`、`emit()`は**ハンドラの完了を待たずに即座に返却** | — |
| 優先度 | 高優先度のグループが先に実行；**グループ間はシーケンシャル、グループ内は並行**（グループ内のハンドラはイベントのコピーを持ち、フィールドをマージし、衝突時はWARNINGを出力） | `@command(..., priority=N)` / 登録時にpriorityを指定 |
| ブロッキング | 各グループ処理後、`event.is_stopped()`をチェックし、ヒットした場合**より低い優先度は実行されない** | `event.mark_processed(stop=True)` / `event.done()` |

> **よくある誤解**:
> 1. **スコープフィルタリングは静かである**— フィルタリングされたハンドラはエラーもレスポンスも出さず、TRACEレベルのログ（`core.scope.denied`）でのみ表示される。「モジュールがメッセージを受け取らない」場合は、まずスコープのバインドを確認すること。
> 2. **ハンドラは天然に並行である**— フレームワークは各ハンドラに対して独立したTaskを作成しており、**自分で`asyncio.create_task`をラップする必要はない**。
> 3. **同じ優先度のグループ内ではブロッキングしない**— `mark_processed(stop=True)`は、より低い優先度のグループをブロックするだけで、同じグループ内の並行実行中のハンドラは途中で中断されない。
> 4. **スローログの閾値は固定の1秒である**— ハンドラの処理時間が1秒を超えるとログにWARNINGが出力される（`wait_reply`の待ち時間は処理時間から除外される）が、処理は中断されない。

> スコープ（scope）のモジュール次元の3段階のバインド、アイデンティティ次元の認証と出力アクション制限の詳細は [スコープ（scope）](advanced/scope.md) を参照してください。イベントスコープのテキストフィルタリングとコマンドユーザーACLは [イベント処理入門](getting-started/event-handling.md) を参照してください。並行上限の設定は [設定ガイド](user-guide/configuration.md#フレームワーク設定) を参照してください。

## ライフサイクルイベント

以下の図は、フレームワークの各コンポーネントのライフサイクルイベントの発生順序を示しています：

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

> 完全なイベントリスナーのメソッド（`lifecycle.on()` / `once()` / `has_handlers()`）、全ライフサイクルイベントのリストとデータ形式は [ライフサイクル管理](advanced/lifecycle.md) を参照してください。

## モジュールロード戦略

ErisPulseは、`get_load_strategy()`が返す`ModuleLoadStrategy`で宣言される3種類のモジュールロード戦略をサポートします：

```mermaid
flowchart TD
    A["モジュールをModuleManagerに登録"] --> B{"ロード戦略"}
    B -->|"lazy_load = true<br/>+ activate_on宣言"| C["ModuleActivatorプロキシを作成"]
    B -->|"lazy_load = true<br/>activate_onなし"| D["LazyModuleプロキシを作成"]
    B -->|"lazy_load = false"| E["即時インスタンス作成"]
    C --> F["イベント/コマンドstubをディスパッチャに登録"]
    F --> G["sdk属性にマウント"]
    G --> H["イベント到着時にアクティベーションをトリガー"]
    H --> I["インスタンス化 + on_load() + stubの登録解除"]
    D --> J["sdk属性にマウント"]
    J --> K["最初の属性アクセス時に初期化"]
    E --> L["on_load()を呼び出す"]
    L --> M["sdk属性にマウント"]
```

> 詳細は [遅延ロードシステム](advanced/lazy-loading.md)、[ライフサイクル管理](advanced/lifecycle.md)、およびモジュールドキュメントを参照してください。

### イベント駆動遅延アクティベーション（`activate_on`）のトリガーアーキテクチャ

> [!NOTE]
> この機能はErisPulse **2.8.0以降**が必要です。

`activate_on`は、モジュールを**最初のマッチするイベント/コマンドが到着したときに初めてロード**するようにします。これにより、メモリ常駐を避けることができ、イベントのロスもありません：

```mermaid
flowchart LR
    subgraph Declare["モジュールの宣言"]
        S1["get_load_strategy()が返す<br/>ModuleLoadStrategy(activate_on=...)"] --> S2["activate_onの構文：<br/>str / dict / listの自由な混合"]
        S2 --> S2a["'message' → イベントタイプレベル"]
        S2 --> S2b["{'notice': 'group_member_increase'}<br/>→ タイプ + detail_type"]
        S2 --> S2c["{'command': 'roll'}<br/>→ コマンドトリガー（簡略/リスト）"]
        S2 --> S2d["{'command': {'name': 'dice', 'help': ...,<br/>'aliases': [...], 'hidden': ...}}<br/>→ コマンドトリガー（dict宣言）"]
    end

    subgraph Runtime["実行時"]
        R1["ModuleActivatorがstubを登録"] --> R1a["イベントstub → message/notice/request/metaマネージャー<br/>優先度ACTIVATION_STUB_PRIORITY（極めて低い）"]
        R1 --> R1b["コマンドstub → コマンドマネージャー<br/>プレースホルダーコマンド（dict宣言のhelp/usage/group/aliases/hiddenを反映）"]
        R1a --> R2{"イベント到着をトリガー"}
        R1b --> R2
        R2 --> R3["ownerに基づいてスコープフィルタリング"]
        R3 --> R4["asyncio.Lockで重複アクティベーションを防止"]
        R4 --> R5["モジュールのインスタンス化 + on_load()の呼び出し"]
        R5 --> R6["全てのstubを登録解除"]
        R6 --> R7["イベントを実際のハンドラに転送"]
    end

    Declare --> Runtime
```

**トリガーセマンティクスの要点：**

> 完全な`activate_on`の構文（str / dict / list）、コマンドdict宣言、プレースホルダのhelpのフォールバックチェーン、スコープフィルタリング、失敗のセマンティクスは [遅延ロードシステム](advanced/lazy-loading.md#イベント駆動遅延アクティベーションactivate_on) を参照してください。

## 本地プラグインフォルダアーキテクチャ

> [!NOTE]
> この機能はErisPulse **2.8.0以降**が必要です。

ローカルプラグイン（`plugins/`ディレクトリ）は、パッケージ化して公開する必要がなく、フレームワークの起動時に自動的に検出されロードされます：

```mermaid
flowchart TD
    A["プロジェクトのplugins/ディレクトリ<br/>（ErisPulse.framework.plugins_dir、複数ディレクトリをサポート）"] --> B{"PluginFolderLoader.discover()"}
    B --> C["単ファイル：dice.py → プラグイン名 = ファイル名"]
    B --> D["パッケージ形式：weather/（含__init__.py）→ プラグイン名 = ディレクトリ名"]
    B --> E["無視：__pycache__ / _で始まる / .py以外 / __init__.pyのないディレクトリ"]
    C --> F["モジュールのインポート（spec_from_file_location）"]
    D --> G["モジュールのインポート（sys.path + import_module）"]
    F --> H["モジュールクラスの識別：Main（BaseModuleの子クラス）を優先、なければ最初の子クラス"]
    G --> H
    H --> I["entry-pointと一致するmoduleInfoを構築"]
    I --> J["ModuleLoader.load()で統合<br/>ローカルが優先してPyPIの同名インストールパッケージを上書き"]
    J --> K["インストールパッケージモジュールと共用：<br/>有効状態 / スコープ / meta / i18n / コンテキスト"]
```

**規約と特性：**

- プラグイン名の取得元：単ファイルはファイル名、パッケージ形式はディレクトリ名
- 本地プラグイン`moduleInfo.meta.source == "plugin_folder"`、PyPIインストールパッケージモジュールとシームレスに共存
- 同名の場合はローカルが優先（ローカル上書きデバッグ用）、無効化された場合は同名のentry-point項目も削除

## モジュールのホットリロードアーキテクチャ

ホットリロードは**全てのモジュールソース**に対して一貫しています：ローカルプラグイン（`plugins/`ディレクトリ）、実行時登録（`sdk.module.register()`）、PyPIインストールパッケージモジュールはすべて`sdk.reload_module()` / `sdk.module.reload()`でホットリロード可能——**デフォルトは全量リロード**（トップレベルパッケ名に基づいてimportキャッシュをクリアし、依存者コードを再インポート、`full=False`は軽量の安全弁）、`sdk.reload_all_modules()` / `sdk.module.reload_all()`で一度に全量リロード可能（pipで一括アップデート後に呼び出すと全てが有効になります）：

```mermaid
flowchart TD
    A["sdk.enable_plugin_hot_reload()<br/>（自動監視、ローカルプラグインディレクトリのみ）"] --> B["PluginReloadWatcherの起動"]
    B --> C["PollingObserver（バックグラウンド守護スレッド）<br/>定期的に.pyファイルのmtimeを比較"]
    C --> D{"プラグインファイルの変更"}
    D --> E["変更のデブースティング（デフォルト1秒）"]
    E --> F["_handle_changeでプラグイン名を解析<br/>（単ファイル / パッケージ形式）"]
    F --> G["asyncio.run_coroutine_threadsafe<br/>イベントループにスケジュール"]
    G --> H["sdk.reload_module(name, full=Trueがデフォルト)<br/>（任意のモジュールに手動で呼び出しても可）"]
    H --> I["構文検証（ファイルごとに解析）<br/>失敗すればリロードを拒否、旧インスタンスがサービスを継続"]
    I --> J["旧インスタンルのアンロード（on_before_unload → on_unload）<br/>依存者を収集し、連鎖リロードを準備"]
    J --> K{"モジュールのソースは？"}
    K -->|"plugin_folder"| L["登録とプラグインsys.modulesをクリア<br/>plugins/ディレクトリを再スキャン"]
    K -->|"runtime実行時登録"| M["定義モジュールのキャッシュをクリアし、再インポート<br/>クラス名で再取得（__main__ガード）"]
    K -->|"PyPIインストールパッケージ"| N["登録をクリアし、top_levelに基づいてパッケージ<br/>sys.modulesのサブツリーと__pycache__バイトコードをクリア<br/>（メタデータが欠落した場合は、旧モジュールオブジェクトのトップセグメントでバックアップ）<br/>インポートキャッシュをリフレッシュした後、entry-pointを再調査"]
    L --> O["再登録 + 再ロード"]
    M --> O
    N --> O
    O --> P["sdk属性に新インスタンルをマウント<br/>新旧クラスのアイデンティティを確認（偽リロード警告）"]
    P --> Q["依存者への連鎖リロード<br/>（プラグイン/実行時：完全リロード；<br/>PyPI依存者：デフォルトでコードを再インポート）"]
    L -.->|"ファイルが削除された"| R["ロード結果から削除"]
    M -.->|"定義が安全に再インポートできない"| R
    N -.->|"entry-pointが消滅した（アンインストールされた）"| R
```

**3つのソースの差異は発見フェーズのみで、検証、アンロード、連鎖リロードは完全に一致します：**

- **ローカルプラグイン**（`moduleInfo.meta.source == "plugin_folder"`）：`sys.modules`をクリアした後、`plugins/`ディレクトリを再スキャン；ファイルが削除された場合はロード結果から削除
- **実行時登録**（`source == "runtime"`）：定義モジュールのキャッシュをクリアし、再インポート、クラス名で再取得し、再登録；`__main__` / 元ファイルのないクラスは再インポートを拒否（ガード警告、エントリスクリプトの再実行を防ぐ）
- **PyPIインストールパッケージ**：`meta.top_level`に基づいてパッケージの`sys.modules`サブツリーをクリアし、インポートキャッシュをリフレッシュ（entry-pointの60秒キャッシュを突破）後、再調査して再インポート；entry-pointが消滅した（pipでアンインストール）場合はロード結果から削除

**デフォルトの意味と信頼性保証（2.11）：**

- **reloadは全量リロード**：デフォルトでトップレベルパッケ名に基づいて`sys.modules`をクリアし、依存者コードを再インポート；`full=False`はメタデータのみをクリアし、PyPI依存者は再インスタンス化（巨大な依存ツリーのパフォーマンス用の安全弁）
- **構文検証のゲート**：アンロードプロセスに入る前にファイルごとに構文解析、失敗すればリロードを拒否——旧インスタンルはアンロードされず、サービスを継続、構文エラーはモジュールを「半死状態」にすることなく、大容量パッケージのファイル数上限を超えた場合は検証をスキップ
- **キャッシュのバックアップ**：`top_level`メタデータが欠落した場合は「旧モジュールオブジェクト`__name__`の接頭辞 → モジュールクラス`__module__`の接頭辞」の2段階でクリア範囲を推定；リロード時に元ファイルのバイトコードキャッシュ（`__pycache__`）もクリアし、同じ秒数・同じ長さの小さな変更も有効
- **アイデンティティの確認**：リロード成功後に新旧クラスのアイデンティティ変化をアサーションし、変化がない場合（C拡張などキャッシュがクリアできない）は明示的に警告し、`module.reload`イベントに`identity_changed: false`を添付；`module.get_info()`は`running_identity` / `stale`フィールドで「登録バージョン ≠ 実行バージョン」を公開
- **失敗の可視化**：ロード失敗の現場（例外 + traceback）は`module.last_error(名前)` / `get_info()["last_error"]`で直接確認可能、失敗経路は同時にそのモジュールのimportキャッシュをクリアする——「コードを変更して再リロード」を1回行うと必ず新しいコードを読み込む
- 重載は元の遅延ロードモジュールを強制的にアクティブにする（明示的なログ）；`reload_all_modules()`は遅延ロード戦略を維持し、重載前に既にロード済みのモジュールを再アクティブ化し、休眠中のモジュールは休眠のまま
- `reload_all_modules()`は依存トポロジ順に再ロードし、単一モジュールの失敗は診断を記録してスキップ（全体のロールバックはない——on_unload副作用は元に戻せない、単一モジュールのホットリロードのベストエフォートの意味と一致）；失敗した場合もロールバックされた状態は同様、ログは旧インスタンルが完了済みであることを明確に示す

## アダプタのホットリロードアーキテクチャ

アダプタのコードレベルのホットリロード（2.11）は、モジュールパイプラインと同構造です：`sdk.adapter.reload(プラットフォーム名)` / `sdk.reload_adapter(プラットフォーム名)`は**ローカルプラグイン**と**PyPIインストールパッケージ**の両方のソースに対して実行されます——

```mermaid
flowchart TD
    A["sdk.adapter.reload(プラットフォーム名)"] --> B["構文検証（ファイルごとに解析）<br/>失敗すればリロードを拒否、旧アダプタがサービスを継続"]
    B --> C["スナップショット：adapterInfo / インスタンス / 起動状態 /<br/>起動タスク / bots / sys.modulesエントリ"]
    C --> D["unload（shutdownでクリーンアップ：<br/>ルーティング/イベント/コマンド/タスク/接続/bot offline + デレジストレーション）"]
    D --> E["キャッシュのクリア：__pycache__バイトコード →<br/>sys.modulesサブツリー → invalidate_caches<br/>→ finderキャッシュ → プラグインパス記録"]
    E --> F{"ソースは？"}
    F -->|"プラグインディレクトリ"| G["plugins/を再スキャン（discover_adapters）"]
    F -->|"PyPIインストールパッケージ"| H["entry-pointを再調査して再インポート<br/>（top_levelでクリア + クラス__module__でバックアップ）"]
    G --> I["再登録 + startup（元の起動状態）<br/>クラスのアイデンティティを確認（偽リロード警告）"]
    H --> I
    I --> J["adapter.reloadイベント<br/>identity_changed / version_old→new / was_started"]
    G -.->|"プラグインが削除された"| K["ロード結果から削除"]
    H -.->|"entry-pointが消滅した"| K
    I -.->|"失敗"| L["ロールバック：sys.modules /<br/>登録のスタブ / インスタンス / 起動状態を復元"]
```

**モジュールパイプラインとの違い：**

- アダプタには遅延ロードと依存の連鎖がありません：リロードは**依存する他のアダプタに連鎖しない**（警告のみ——登録表を間接的に消費するが、インスタンスの連鎖的な意味はない）
- 起動は非同期のチェーン（`startup`は`_run_adapter`で発行され、依存をスキップし、指数的退避リトライを含む）：起動が一時的に失敗しても**リロード失敗と判定しない**（コードはすでに新しいものに置き換わっている）、結果は`adapter.status.change`で通知される
- `register()`のインスタンスの再利用の罠（同じオブジェクトであれば旧インスタンスが再利用される）は「pycクリア + sys.modulesクリア + アイデンティティの確認」の3つの手段でバックアップ
- ライフサイクルイベント：`adapter.reload`（payloadには`adapter_name` / `success` / `full` / `duration_ms` / `identity_changed` / `version_old→new` / `was_started` / `source`が含まれる）