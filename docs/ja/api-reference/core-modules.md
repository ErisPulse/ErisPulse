# コアモジュール API

> [!TIP]
> **この記事を読むべきタイミング**：ストレージ、設定、ログ、モジュール管理、ルーティング、HTTP クライアントなどのコア機能を使用する際、メソッドのシグネチャが思い出せない場合に、この記事をすばやく参照してください。必要ない場合はスキップしてください。

このドキュメントは、ErisPulse コアモジュールの API の速見リファレンスを提供します。各モジュールの「完全なドキュメント」リンクをクリックして、詳細な使用方法と例をご覧ください。

## Storage モジュール

設定可能なバックエンド（SQLite/MySQL/PostgreSQL）に基づくキー/値ストレージシステムで、汎用的な SQL チェーンクエリがサポートされています。バックエンドは設定によって簡単に切り替えられます。詳細は [ストレージバックエンド](../advanced/storage-backends.md) を参照してください。

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

### 属性アクセス

```python
sdk.storage.my_key          # sdk.storage.get("my_key") と同等
sdk.storage.my_key = "val"  # sdk.storage.set("my_key", "val") と同等
```

### SQL チェーンクエリ

Storage モジュールはチェーン呼び出しスタイルの汎用 SQL クエリビルダーを提供し、カスタムテーブルの CRUD 操作がサポートされています。

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> 完全なチェーンクエリ API（Select/Insert/Update/Delete/Where/OrderBy/Limit、AlterTable、トランザクションなど）は [SQL クエリビルダー](../advanced/sql-builder.md) を参照してください。

### ストレージバックエンド抽象

`StorageManager` は `BaseStorage` 抽象基底クラスを継承し、Redis、MySQL などの他のストレージメディアを拡張可能です。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### 非同期インターフェース

Storage と Config モジュールは非同期メソッド（接頭辞 `a`）を提供しています。**非同期はネイティブの主インターフェースで、同期メソッドは互換性層**（バックグラウンドのイベントループに橋渡し）です。既存の同期コードは変更する必要がありません。非同期ハンドラでは、非同期メソッドを優先的に使用してください。

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
```

## Config モジュール

TOML 形式の設定ファイル管理で、ドット区切りのキー経路がサポートされています。

### API 概要

| メソッド | 説明 |
|------|------|
| `getConfig(key, default)` | 設定を読み込み、ドット経路 `"MyModule.subkey"` などもサポート |
| `getAllConfig()` | 全量設定スナップショット（深いコピー、未保存の待機値も含む） |
| `setConfig(key, value, immediate=False)` | 設定を書き込み。`immediate=True` の場合、ファイルに即座に保存 |
| `delConfig(key, immediate=False)` | 設定キーを削除（空にすることとは異なり、ファイルから削除）；`config.set` イベントをトリガー（`new_value=None`） |
| `force_save()` | メモリ内の設定をファイルに強制的に書き込む |
| `reload()` | ファイルから設定を再読み込み |
| `agetConfig(key, default)` | 非同期で設定を読み込む |
| `agetAllConfig()` | 非同期で全量設定スナップショットを取得 |
| `asetConfig(key, value, immediate)` | 非同期で設定を書き込む |
| `adelConfig(key, immediate)` | 非同期で設定キーを削除（`delConfig` と同じ動作） |
| `aforce_save()` | 非同期で強制保存 |
| `areload()` | 非同期で再読み込み |

### 例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

snapshot = sdk.config.getAllConfig()          # 全量スナップショット（深いコピー）
sdk.config.delConfig("MyModule.deprecated")  # キーを削除（遅延書き込み）

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)

# 非同期インターフェース（非同期ハンドラでは優先的に使用）
snapshot = await sdk.config.agetAllConfig()
await sdk.config.adelConfig("MyModule.deprecated")  # 非同期でキーを削除
```

> `setConfig` はデフォルトで遅延書き込み（5秒ごとのバッチ保存）を使用し、`immediate=True` で即座に設定ファイルに永続化できます。設定の変更は `config.set` ライフサイクルイベントをトリガーします。  
> `delete` は遅延書き込みと `config.set` イベント（`new_value=None`）をサポートし、既存の `on_config_update` 監視者は変更なしで削除を感知できます。

## Logger モジュール

モジュールベースのログシステムで、Rich による出力がサポートされ、サブロガーとモジュールレベルの制御が可能です。

### 基本的な使用法

```python
sdk.logger.debug("デバッグ情報")
sdk.logger.info("実行情報")
sdk.logger.warning("警告情報")
sdk.logger.error("エラー情報")
sdk.logger.critical("致命的エラー")
```

### サブロガー

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("サブモジュールのログ")

child_logger.get_child("utils")  # ネストもサポート
```

### ログレベルの制御

```python
sdk.logger.set_level("DEBUG")                          # グローバルレベル
sdk.logger.set_module_level("MyModule", "DEBUG")       # モジュールレベル

# 支持されるレベル（低い順）：
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE は最低レベルで、イベントの配信、ルーティング登録などのフレームワーク内部の詳細なデバッグ情報を出力
sdk.logger.set_level("TRACE")                          # 全てのログを有効にする
```

### ログのサブスクリプション（プッシュ型）

Dashboard などのモジュールが構造化されたログをリアルタイムに受信できるようにし、レベルのフィルタリングや履歴の補填が可能です。

> **低レベルログの明示的なサブスクリプション**：サブスクライバの `min_level` はグローバルのログレベルより低く設定できます。この場合、低レベルのログは**マッチするサブスクライバにのみプッシュされ**、コンソールには出力されず、メモリにも記録されません。これにより、メインのログストリームが汚染されることを防ぎます。
>
> ```python
> # グローバルが INFO でも、独自に DEBUG ログをサブスクライブ可能
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
    #     "message": "厳密モード：...",
    # }
    pass

# 直接呼び出し方式
sdk.logger.handler("my-handler", min_level="INFO")(on_log)
sdk.logger.remove_handler("my-handler")
```

| メソッド | 説明 |
|------|------|
| `handler(id, *, min_level)(func)` | デコレータ/直接呼び出しの両方に対応。`id` が空の場合は関数名を使用。`min_level` はグローバルレベルより低く設定可能（サブスクライバにのみ送信、コンソール/メモリには出力されない）。登録時に履歴ログが自動的に補填される |
| `remove_handler(id)` | サブスクライバを削除 |

### 出力制御

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter モジュール

アダプタマネージャーで、複数プラットフォームのアダプタの登録、起動、停止を管理します。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(platform)` | アダプタのインスタンスを取得 |
| `exists(platform)` | アダプタが登録されているか確認 |
| `enable(platform)` / `disable(platform)` | アダプタを有効化/無効化 |
| `is_enabled(platform)` | 有効化されているか確認 |
| `startup(platforms)` / `shutdown(platforms)` | アダプタを起動/停止 |
| `is_running(platform)` | アダプタが実行中か確認 |
| `list_running()` | 実行中のアダプタをすべてリスト |
| `platforms` | すべてのプラットフォーム名のリストを取得 |
| `get_info(platform)` | アダプタの登録情報（json-safe：meta + クラス名） |
| `get_meta(platform, resolve_i18n=True)` | アダプタの紹介メタ情報（`module.get_meta` と同期、i18n 解析をサポート） |

### アダプタイベント

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot 状態の照会

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> 完全なアダプタ管理 API は [アダプタシステム API](adapter-system.md) を参照してください。

## Module モジュール

モジュールマネージャーで、プラグインの登録、ロード、アンロードを管理します。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(name)` | モジュールのインスタンスまたは遅延ロードプロキシを取得（登録済みだがロードされていない場合はプロキシを返す） |
| `exists(name)` | 登録されているか確認 |
| `is_loaded(name)` | ロードされているか確認 |
| `is_enabled(name)` | 有効化されているか確認 |
| `enable(name)` / `disable(name)` | モジュールを有効化/無効化 |
| `load(name)` / `unload(name)` | モジュールをロード/アンロード |
| `call(module, method, *args, timeout=None, **kwargs)` | ターゲットモジュールのサービスメソッドを呼び出す（プロトコル化された RPC） |
| `list_registered()` | 登録済みモジュールをすべてリスト |
| `list_loaded()` | ロード済みモジュールをすべてリスト |
| `get_info(name)` | モジュール情報を取得 |
| `get_status_summary()` | モジュールの状態サマリーを取得 |

### 属性アクセス

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # 等価なショートカット
```

### モジュール間呼び出し（RPC）

```python
# プロトコル化された呼び出し：型付けされたエラー / 遅延モジュールの自動起動 / owner の帰属 / タイムアウトの意味
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

サービス側の裸属性アクセス `sdk.module.Chat.get_history(...)` との違い：

| | `module.call()` | 裸属性アクセス |
|---|---|---|
| ターゲットが未登録/無効 | `ModuleNotAvailableError` を投げる | `AttributeError` を投げる |
| 遅延ロードモジュール | 自動起動 | 非同期初期化で `RuntimeError` を投げる |
| `current_owner` | ターゲットモジュールに帰属する | 呼び出し元のまま |
| タイムアウト | デフォルト 30s、オーバーライド可能 | なし |
| scope 審査 | `actions.<呼び出し元>.call` | なし |

### サービス契約（meta.services）

サービス側は `get_meta()` の `services` フィールドで公開ホワイトリストを宣言（`commands` と対称）、宣言後は呼び出し側の制限が厳しくなる：

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **デフォルト = 開発者に影響なし**：`services` を宣言していない場合、任意の**公開**メソッドが呼び出せる（後方互換性）、アンダースコア付きの私的メソッドは常に禁止される；制限の主な制御権はユーザー側の scope 設定にある
- 宣言後：ホワイトリスト内のメソッドのみ呼び出せる、越境すると `ServiceNotProvidedError` を投げる
- 呼び出し側の制限：`scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**サービス紹介（description）**：`services` は各サービスに紹介を宣言できる dict 形態もサポート（純文字列または i18n ディクショナリ）、サービスディレクトリ / AI 呼び出し点の説明に利用できる：

```python
return ModuleMeta(
    services=[
        "get_history",                              # 簡単な形態：紹介はメソッドの docstring 首行から自動取得
        {"name": "translate", "description": "テキストを指定の言語に翻訳する"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "会話の要約"}},
    ],
)
```

紹介の解析優先順位：**明示的な description（i18n は現在の言語に解析）> メソッドの docstring 首行 > 空文字列**。

### サービスディレクトリ（services）

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': '会話履歴を取得'}]}

sdk.module.services("Chat")  # 指定モジュールのみ照会
```

`meta.services` を**明示的に宣言した**モジュールのみをリストし、各サービスにはメソッドのシグネチャ文字列と紹介テキストが付いており、MCP 化（AI に呼び出し点を公開）のためのデータ基盤となる。

> 定向イベント送信はライフサイクル層に属する：`lifecycle.emit(event, data, to="ModuleName")`、[モジュール間通信](../advanced/module-communication.md) を参照してください。

## Lifecycle モジュール

イベント駆動のライフサイクルマネージャーで、イベントの提出と監視機能を提供します。

### API 概要

| メソッド | 説明 |
|------|------|
| `on(event, priority=0)` | イベントハンドラを登録するデコレータ、ドットマッチとワイルドカード `*` をサポート |
| `register(event, handler, priority=0)` | 関数形式でハンドラを登録 |
| `unregister(event, handler=None)` | ハンドラを削除 |
| `emit(event, data, to=None)` | 非同期でイベントをトリガー；`to` に owner を指定すると対象モジュールに送信 |
| `emit_sync(event, data, to=None)` | 同期でイベントをトリガー（非同期ハンドラでは create_task でスケジュール） |
| `submit_event(event_type, msg, data, source, to=None)` | 標準形式のイベントを提出（旧版と互換） |
| `start_timer(id)` / `stop_timer(id)` | パフォーマンス計測タイマー |

### 例

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"モジュール初期化: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"モジュールイベント: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})

# 対象送信：Chat モジュールに登録されたフックにのみ配信
await sdk.lifecycle.emit("message_received", {"text": "hi"}, to="Chat")
```

> 完全な標準イベントリストと詳細な使用法は [ライフサイクル管理](../advanced/lifecycle.md) を参照してください。

## Router モジュール

HTTP/WebSocket ルーティングマネージャーで、FastAPI + Uvicorn をベースにし、デコレータルーティング、ミドルウェア、グループ化、リクエスト制限、CORS をサポートします。

> 完全なルーティング API ドキュメント（デコレータルーティング、WebSocket、ミドルウェア、リクエスト制限、CORS、セキュリティヘッダーなど）は [ルーティングマネージャー](../advanced/router.md) を参照してください。

### 速見リファレンス

```python
# HTTP ルーティング
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket ルーティング
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# ルーティンググループ
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## HTTP Client モジュール

統一されたネットワーククライアントで、HTTPリクエスト、WebSocket接続、接続プール管理、自動リトライ、リクエスト統計、ライフサイクルイベント統合を統合します。

> 完全なネットワーククライアントドキュメント（リクエストメソッド、レスポンスオブジェクト、WebSocketクライアント、例外体系など）は [ネットワーククライアント](../advanced/http-client.md) を参照してください。

### 速見リファレンス

```python
from ErisPulse.Core import client

# HTTPリクエスト
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# WebSocket
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## SDK デバッグ

### dump_state()

フレームワークの現在の実行状態をスナップショットとしてエクスポートし、デバッグや診断に使用します。

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

返却される構造には以下のサブシステムの状態が含まれます：

| フィールド | 説明 |
|------|------|
| `sdk` | SDK初期化状態、Pythonバージョン、実行プラットフォーム、タイムスタンプ |
| `adapters` | 登録済み/起動済みのアダプタリスト、各プラットフォームのBotオンライン状態 |
| `modules` | 登録済み/有効化済み/無効化済み/遅延ロード済みのモジュールリスト |
| `events` | 各種イベントハンドラ数（message/notice/request/meta/commands） |
| `router` | サーバーの実行状態、HTTP/WebSocketルーティング数 |

> [!NOTE]
> ErisPulse **2.5.2+** で追加

## Interaction 交互会話

wait_replyの待機とセッション排他リース（`sdk.interaction`）を管理します。

### 一般的なメソッド

```python
# セッションのタイムアウトリマインダー：5分以内に返信がなければリマインダー、ユーザーの返信で自動キャンセル
reminder = event.remind(300, "まだいますか？")
reminder.cancel()  # 手動キャンセル

# タイムアウトのアップグレード：時間内に必ず到達（返信でキャンセルされない）
event.escalate(1800, lambda e: notify_master("30分未処理"))

# 複数ルートの待機：先着順
which, reply = await event.select(
    event.expect(pattern="同意*", user="A"),
    event.expect(pattern="拒否*", user="B"),
    timeout=60,
)

# セッションレベルの待機：同じグループの誰かの返信で応答
reply = await event.wait_reply(session=True, prompt="誰か答えてくれませんか？")

# セッションの現在の所有者を照会（誰がこのユーザーと対話しているか）
owner = sdk.interaction.get_owner_of(event)

# セッション排他リースの宣言（占有されていたら None を返す）
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # 独占対話
    finally:
        lease.release()

# コンテキストマネージャー形式（占有されていたら SessionOccupiedError を投げる）
with sdk.interaction.hold(event) as lease:
    ...

# セッションの待機統計
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

モジュールのアンロード / アダプタの停止時に、その待機とタイマーは自動的にキャンセルされます（待機者は即座に `None` を返す）、返信がヒットした際には、スコープ権限を再確認します（ユーザーがブラックリストに追加 / モジュールが解除された場合、待機を終了する）。

> [!NOTE]
> 本節の機能は ErisPulse **2.8.0+** で追加

## Transcript 会話受信箱

各セッションの最近のメッセージストリームを自動的に記録・照会する（`sdk.transcript`）、AI対話、重複防止などのコンテキスト記憶型モジュールの共通ベースとして使用されます。

### 一般的なメソッド

```python
# 便利な照会（推奨）：現在のセッションの最近20件（ユーザーとロボットの両方、時間昇順）
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# マネージャーAPI
sdk.transcript.append(event, "user", "テキスト")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

設定（`ErisPulse.transcript`）：`enabled`（デフォルトで有効）、`max_per_session`（各セッションの上限、デフォルト 50）、`ttl_hours`（グローバルの有効期限、デフォルト 168 時間）。データは独立した SQLite テーブルに保存され、上限/期限を超えたものは惰性でクリーンアップされます。

> [!NOTE]
> 本節の機能は ErisPulse **2.8.0+** で追加

## 関連ドキュメント

**API をさらに調べるには**：
- [イベントシステム API](event-system.md) - Event モジュール API
- [アダプタシステム API](adapter-system.md) - Adapter 管理 API

**各サブシステムの完全なドキュメントを参照するには**：
- [SQL クエリビルダー](../advanced/sql-builder.md) - SQL チェーンクエリの完全なドキュメント
- [ルーティングマネージャー](../advanced/router.md) - ルーティングマネージャーの完全なドキュメント
- [ネットワーククライアント](../advanced/http-client.md) - ネットワーククライアントの完全なドキュメント
- [ライフサイクル管理](../advanced/lifecycle.md) - ライフサイクルの完全なドキュメント