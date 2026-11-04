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

## 関連ドキュメント

**API の参照を続ける**：
- [イベントシステム API](event-system.md) - Event モジュール API
- [アダプターシステム API](adapter-system.md) - Adapter 管理 API

**特定サブシステムの完全なドキュメント**：
- [SQL クエリビルダー](../advanced/sql-builder.md) - SQL チェーンクエリ完全ドキュメント
- [ルートマネージャー](../advanced/router.md) - ルートマネージャー完全ドキュメント
- [ネットワーククライアント](../advanced/client.md) - ネットワーククライアント完全ドキュメント
- [ライフサイクル管理](../advanced/lifecycle.md) - ライフサイクル完全ドキュメント