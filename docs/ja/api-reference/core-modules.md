# コアモジュール API

本文書は、ErisPulse コアモジュールの API のクイックリファレンスを提供します。メソッドの署名と簡潔な説明が含まれています。詳細な使い方や例については、各モジュールの「完全ドキュメント」リンクをクリックしてください。

## Storage モジュール

SQLite をベースとしたキー/値ストアシステムで、一般的な SQL チェーンクエリをサポートします。

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

Storage モジュールは、カスタムテーブルの CRUD 操作をサポートするチェーン呼び出しスタイルの一般的な SQL クエリビルダーを提供します。

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> 完全なチェーンクエリ API (Select/Insert/Update/Delete/Where/OrderBy/Limit、AlterTable、トランザクションなど) は、[SQL クエリビルダー](../advanced/sql-builder.md)を参照してください。

### ストレージバックエンド抽象

`StorageManager` は `BaseStorage` 抽象基底クラスを継承し、Redis、MySQL などの他のストレージメディアを拡張可能です。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### 非同期インターフェース

Storage と Config モジュールは、非同期メソッド（接頭辞 `a`）を提供し、非同期ハンドラで安全に呼び出すことができます。同期メソッドは引き続き保持され、既存のコードを変更する必要はありません。

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

TOML 形式の設定ファイル管理で、ドット区切りのキー経路をサポートします。

### API 概要

| メソッド | 説明 |
|------|------|
| `getConfig(key, default)` | 設定を読み込み、ドット経路 `"MyModule.subkey"` などもサポート |
| `setConfig(key, value, immediate=False)` | 設定を書き込み。`immediate=True` の場合、ファイルに即時保存 |
| `force_save()` | メモリ内の設定をファイルに強制的に書き込み |
| `reload()` | ファイルから再読み込み |
| `agetConfig(key, default)` | 非同期で設定を読み込み |
| `asetConfig(key, value, immediate)` | 非同期で設定を書き込み |
| `aforce_save()` | 非同期で強制保存 |
| `areload()` | 非同期で再読み込み |

### 例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（5秒ごとのバッチ保存）を使用します。`immediate=True` を設定すると、設定ファイルに即時永続化されます。設定の変更は `config.set` ライフサイクルイベントをトリガーします。

## Logger モジュール

モジュール化されたログシステムで、Rich をベースにし、サブロガーとモジュールレベルの制御をサポートします。

### 基本的な使い方

```python
sdk.logger.debug("デバッグ情報")
sdk.logger.info("実行情報")
sdk.logger.warning("警告情報")
sdk.logger.error("エラー情報")
sdk.logger.critical("致命エラー")
```

### サブロガー

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("サブモジュールログ")

child_logger.get_child("utils")  # 嵌套もサポート
```

### ログレベル制御

```python
sdk.logger.set_level("DEBUG")                          # グローバルレベル
sdk.logger.set_module_level("MyModule", "DEBUG")       # モジュールレベル

# 使用可能なレベル（低い順）:
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE は最低レベルで、イベントの配信、ルーティング登録などのフレームワーク内部の詳細なデバッグ情報を出力
sdk.logger.set_level("TRACE")                          # 全てのログを有効化
```

### ログサブスクリプション（プッシュモード）

Dashboard などのモジュールが構造化されたログをリアルタイムで受信するための機能で、レベルのフィルタリングと履歴の補送が可能です。

> **低レベルログの明示的なサブスクリプション**：サブスクライバの `min_level` はグローバルなログレベルより低く設定できます。この場合、低レベルのログは**一致するサブスクライバにのみプッシュ**され、コンソールには出力されず、メモリにも書き込まれません。これにより、メインのログストリームが汚染されることを回避できます。
>
> ```python
> # グローバルは INFO ですが、個別に DEBUG ログをサブスクライブできます
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
| `handler(id, *, min_level)(func)` | デコレータ/直接呼び出しの両方に対応。`id` が空の場合は関数名を使用。`min_level` はグローバルレベルより低く設定可能（低レベルログはサブスクライバにのみプッシュされ、コンソールやメモリには出力されない）。登録時に履歴ログの補送も自動的に行われる |
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
| `get(platform)` | アダプタインスタンスを取得 |
| `exists(platform)` | アダプタが登録されているか確認 |
| `enable(platform)` / `disable(platform)` | アダプタを有効化/無効化 |
| `is_enabled(platform)` | アダプタが有効化されているか確認 |
| `startup(platforms)` / `shutdown(platforms)` | アダプタを起動/停止 |
| `is_running(platform)` | アダプタが実行中か確認 |
| `list_running()` | 実行中のアダプタをすべてリスト |
| `platforms` | 登録されたプラットフォーム名のリストを取得 |

### アダプタイベント

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot 状態照会

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> 完全なアダプタ管理 API は、[アダプタシステム API](adapter-system.md) を参照してください。

## Module モジュール

モジュールマネージャーは、プラグインの登録、ロード、アンロードを管理します。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(name)` | モジュールインスタンスまたは遅延ロードプロキシを取得（登録済みだがロードされていない場合はプロキシを返す） |
| `exists(name)` | 登録されているか確認 |
| `is_loaded(name)` | ロードされているか確認 |
| `is_enabled(name)` | 有効化されているか確認 |
| `enable(name)` / `disable(name)` | モジュールを有効化/無効化 |
| `load(name)` / `unload(name)` | モジュールをロード/アンロード |
| `call(module, method, *args, timeout=None, **kwargs)` | 指定モジュールのサービスメソッドを呼び出す（プロトコル化された RPC） |
| `emit_to(module, event, data)` | 指定モジュールにライフサイクルイベントを送信 |
| `list_registered()` | 登録済みモジュールを一覧表示 |
| `list_loaded()` | ロード済みモジュールを一覧表示 |
| `get_info(name)` | モジュール情報を取得 |
| `get_status_summary()` | モジュールの状態概要を取得 |

### 属性アクセス

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # 等価なショートカット
```

### モジュール間呼び出し（RPC）

```python
# プロトコル化された呼び出し：型付きエラー / 遅延モジュールの自動起動 / owner帰属 / タイムアウト設定
result = await sdk.module.call("Chat", "get_history", session_id, n=20)
```

サービス側の属性アクセス `sdk.module.Chat.get_history(...)` との違い：

| | `module.call()` | 属性アクセス |
|---|---|---|
| 目標が未登録/未有効化 | `ModuleNotAvailableError` をスロー | `AttributeError` をスロー |
| 遅延ロードモジュール | 自動起動 | 非同期初期化モジュールは `RuntimeError` をスロー |
| `current_owner` | 目標モジュールに帰属 | 呼び出し元のまま |
| タイムアウト | 30秒（カスタマイズ可能） | なし |
| scope 審査 | `actions.<呼び出し元>.call` | なし |

### サービス契約（meta.services）

`get_meta()` の `services` フィールドで外部公開白名单を宣言し、宣言後は呼び出し範囲を絞る：

```python
class ChatModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(services=["get_history", "translate"])

    async def get_history(self, session_id, n=20): ...
```

- **デフォルト = 開発者無感覚**：`services` を宣言していない場合、任意の**公開**メソッドが呼び出せる（後方互換性）、アンダースコア付きのプライベートメソッドは常に禁止；制限の主制御権はユーザー側の scope 設定
- 宣言後：白名单内のメソッドのみ呼び出せる、越境時は `ServiceNotProvidedError` をスロー
- 呼び出し側制限：`scope.set_action("CallerModule", "call", deny="Chat.get_history")`

**サービス紹介（description）**：`services` は各サービスに説明を宣言するための dict 形態もサポート（純文字列または i18n 辞書）、サービスディレクトリや AI 呼び出し点の消費説明に利用：

```python
return ModuleMeta(
    services=[
        "get_history",                              # 簡単な形態：説明はメソッドの docstring 1行目を自動的に利用
        {"name": "translate", "description": "テキストを指定言語に翻訳する"},
        {"name": "summarize", "description": {"i18n": "Chat.meta.svc.summarize", "default": "会話の要約"}},
    ],
)
```

説明の解析優先順位：**明示的な description（i18n は現在の言語に解析）> メソッドの docstring 1行目 > 空文字列**。

### サービスディレクトリ（services）

```python
sdk.module.services()
# {'Chat': [{'name': 'get_history', 'signature': '(session_id, n=20)',
#            'description': '会話履歴を取得'}]}

sdk.module.services("Chat")  # 特定モジュールのみを照会
```

`meta.services` を**明示的に宣言**したモジュールのみを一覧表示；各サービスにはメソッドのシグネチャ文字列と説明テキストが付いており、MCP 化（AI に呼び出し点を公開）のためのデータ基盤を提供する。

### 定向イベント（emit_to）

```python
# 投递側：目標モジュールが有効化された後に module.<名称>.<イベント> に投递
await sdk.module.emit_to("Chat", "message_received", {"text": "hi"})

# 訂正側（Chat モジュール内）：命名空間のフックを登録
lifecycle.on("module.Chat.message_received", handler)
lifecycle.on("module.Chat", handler)  # またはそのモジュールのすべての定向イベントを受信
```

> [!NOTE]
> 本節の機能は ErisPulse **2.8.0+** で追加されました。

## Lifecycle モジュール

イベント駆動のライフサイクルマネージャーで、イベントの送信と監視機能を提供します。

### API 概要

| メソッド | 説明 |
|------|------|
| `on(event, priority=0)` | デコレータでイベントハンドラを登録し、ドットマッチとワイルドカード `*` をサポート |
| `register(event, handler, priority=0)` | 関数形式でハンドラを登録 |
| `unregister(event, handler=None)` | ハンドラを削除 |
| `emit(event, data)` | 非同期でイベントをトリガー |
| `emit_sync(event, data)` | 同期でイベントをトリガー |
| `submit_event(event_type, msg, data, source)` | 標準形式のイベントを送信（旧版と互換性あり） |
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
```

> 完全な標準イベントリストと詳細な使い方は、[ライフサイクル管理](../advanced/lifecycle.md)を参照してください。

## Router モジュール

HTTP/WebSocket ルーティングマネージャーで、FastAPI + Uvicorn をベースにし、デコレータルーティング、ミドルウェア、グループ、リクエスト制限、CORS をサポートします。

> 完全なルーティング API ドキュメント（デコレータルーティング、WebSocket、ミドルウェア、リクエスト制限、CORS、セキュリティヘッダーなど）は、[ルーティングマネージャー](../advanced/router.md)を参照してください。

### クイックリファレンス

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

統一されたネットワーククライアントで、HTTPリクエスト、WebSocket接続、接続プール管理、自動リトライ、リクエスト統計、ライフサイクルイベントの統合を統合します。

> 完全なネットワーククライアントドキュメント（リクエストメソッド、レスポンスオブジェクト、WebSocketクライアント、例外体系など）は、[ネットワーククライアント](../advanced/http-client.md)を参照してください。

### クイックリファレンス

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

フレームワークの現在の実行状態のスナップショットをエクスポートし、デバッグと診断に使用します。

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

返却される構造には以下のサブシステムの状態が含まれます：

| フィールド | 説明 |
|------|------|
| `sdk` | SDK の初期化状態、Python バージョン、実行プラットフォーム、タイムスタンプ |
| `adapters` | 登録/起動済みのアダプタのリスト、各プラットフォームの Bot のオンライン状態 |
| `modules` | 登録/有効化/無効化/遅延ロードされたモジュールのリスト |
| `events` | 各種イベントハンドラの数（message/notice/request/meta/commands） |
| `router` | サーバーの実行状態、HTTP/WebSocket ルート数 |

> [!NOTE]
> ErisPulse **2.5.2+** で追加

## Interaction 交互会話

`sdk.interaction` を使用して、wait_reply 挂起待ちと会話の排他リース（lease）を管理します。

### 常用方法

```python
# 会話の定期的なリマインダー：5 分間返信がない場合にリマインダーを送信し、ユーザーが返信すると自動的にキャンセルされます。
reminder = event.remind(300, "まだいますか？")
reminder.cancel()  # 手動でキャンセル

# タイムアウトによるアップグレード：指定時間に必ず到達します（返信によってキャンセルされません）。
event.escalate(1800, lambda e: notify_master("30 分間未処理"))

# 複数の待ち：先着順
which, reply = await event.select(
    event.expect(pattern="同意*", user="A"),
    event.expect(pattern="拒绝*", user="B"),
    timeout=60,
)

# 会話レベルの待ち：同じグループ内の誰からの返信でも一致します。
reply = await event.wait_reply(session=True, prompt="誰か答えてくれますか？")

# 現在の会話の所有者を照会（誰がこのユーザーと対話しているか）
owner = sdk.interaction.get_owner_of(event)

# 会話の排他リースを宣言（占有されている場合は None を返します）。
lease = sdk.interaction.acquire(event)
if lease:
    try:
        ...  # 独占的な対話
    finally:
        lease.release()

# コンテキストマネージャー形式（占有されている場合は SessionOccupiedError が送出されます）。
with sdk.interaction.hold(event) as lease:
    ...

# 挂起中の会話の統計
sdk.interaction.counts()  # {'waits': 2, 'leases': 1, 'timers': 3, 'owners': {'Chat': 3}}
```

モジュールのアンロードやアダプターの停止時に、その間の待機とタイマーは自動的にキャンセルされます（待機側は即座に `None` を返します）。  
返信が一致した場合、scope 権限を自動的に再確認します（ユーザーがブロックされている場合やモジュールが解除されている場合は、待機が終了します）。

> [!NOTE]
> 本機能は ErisPulse **2.8.0** 以降で追加されました。

## Transcript 会話受信箱

AI 対話、重複防止などのコンテキスト記憶モジュールの共通基盤として、各会話の最近のメッセージストリームの自動記録と照会（`sdk.transcript`）。

### 常用方法

```python
# 便利な照会（推奨）：現在の会話の最近20件（ユーザーとロボットを含む、時間昇順）
messages = await event.history(20)
for m in messages:
    print(m["role"], ":", m["text"])

# マネージャー API
sdk.transcript.append(event, "user", "テキスト")
sdk.transcript.get(event, n=20)
sdk.transcript.clear(event)
```

設定（`ErisPulse.transcript`）：`enabled`（デフォルトで有効）、`max_per_session`（1会話あたりの上限、デフォルト50）、`ttl_hours`（グローバルな有効期限、デフォルト168時間）。データは独立した SQLite テーブルに保存され、上限を超えた場合や期限切れになった場合は惰性でクリーニングされます。

> [!NOTE]
> この機能は ErisPulse **2.8.0+** で追加されました。

## 関連文書

- [イベントシステム API](event-system.md) - Event モジュール API
- [アダプタシステム API](adapter-system.md) - アダプタ管理 API
- [SQL クエリビルダー](../advanced/sql-builder.md) - SQL チェーンクエリの完全ドキュメント
- [ルーティングマネージャー](../advanced/router.md) - ルーティングマネージャーの完全ドキュメント
- [ネットワーククライアント](../advanced/http-client.md) - ネットワーククライアントの完全ドキュメント
- [ライフサイクル管理](../advanced/lifecycle.md) - ライフサイクルの完全ドキュメント