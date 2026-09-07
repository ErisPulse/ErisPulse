# コアモジュール API

本文書では、ErisPulse コアモジュールの API のクイックリファレンスを提供します。メソッドのシグネチャと簡単な説明を含んでいます。詳細な使い方や例については、各モジュールの「完全なドキュメント」リンクをクリックしてください。

## Storage モジュール

SQLite をベースとしたキー/値ストレージシステムで、汎用的な SQL チェーンクエリをサポートしています。

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
sdk.storage.my_key          # sdk.storage.get("my_key") に等しい
sdk.storage.my_key = "val"  # sdk.storage.set("my_key", "val") に等しい
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

Storage および Config モジュールには、非同期メソッド（接頭辞 `a`）が用意されており、非同期ハンドラで安全に呼び出すことができます。同期メソッドも引き続き利用可能で、既存のコードを変更する必要はありません。

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

TOML 形式の設定ファイルを管理し、ドット区切りのキー経路をサポートします。

### API 概要

| メソッド | 説明 |
|------|------|
| `getConfig(key, default)` | 設定を読み取ります。ドット区切りの経路（例: `"MyModule.subkey"`）をサポートします |
| `setConfig(key, value, immediate=False)` | 設定を書き込みます。`immediate=True` の場合、ファイルに即時保存されます |
| `force_save()` | メモリ内の設定をファイルに強制的に書き込みます |
| `reload()` | ファイルから設定を再読み込みします |
| `agetConfig(key, default)` | 非同期で設定を読み取ります |
| `asetConfig(key, value, immediate)` | 非同期で設定を書き込みます |
| `aforce_save()` | 非同期で強制的に保存します |
| `areload()` | 非同期で再読み込みします |

### 使用例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（5秒ごとに一括保存）を使用します。`immediate=True` を設定すると、設定ファイルに即時永続化されます。設定の変更は `config.set` ライフサイクルイベントをトリガーします。

## Logger モジュール

モジュール化されたログシステムで、Rich 出力を基盤としており、サブロガーとモジュールレベルの制御をサポートしています。

### 基本的な使い方

```python
sdk.logger.debug("デバッグ情報")
sdk.logger.info("実行情報")
sdk.logger.warning("警告情報")
sdk.logger.error("エラーメッセージ")
sdk.logger.critical("致命的なエラー")
```

### サブロガー

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("サブモジュールのログ")

child_logger.get_child("utils")  # 嵌套もサポート
```

### ログレベルの制御

```python
sdk.logger.set_level("DEBUG")                          # グローバルなレベル
sdk.logger.set_module_level("MyModule", "DEBUG")       # モジュールごとのレベル

# 利用可能なレベル（低い順）：
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE は最低レベルで、イベントの配信やルーティング登録などの内部詳細なデバッグ情報を出力します。
sdk.logger.set_level("TRACE")                          # 全てのログを有効化
```

### ログのサブスクリプション（プッシュ型）

Dashboard などのモジュールが構造化されたログをリアルタイムで受け取るための機能で、レベルのフィルタリングや履歴の再送信が可能です。

> **低レベルのログを明示的にサブスクライブする**：サブスクライバーの `min_level` はグローバルなログレベルより低く設定できます。この場合、低レベルのログは**該当するサブスクライバーにのみプッシュされ**、コンソールには出力されず、メモリにも保存されません。これにより、メインのログストリームが汚染されることを防ぎます。
>
> ```python
> # グローバルレベルが INFO でも、個別に DEBUG ログをサブスクライブできます
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
| `handler(id, *, min_level)(func)` | デコレータ/直接呼び出しの両方に対応。`id` が空の場合は関数名が使用されます。`min_level` はグローバルレベルより低く設定可能（低レベルのログはサブスクライバーにのみプッシュされ、コンソールやメモリには出力されません）。登録時に履歴ログの補送も自動的に行われます。 |
| `remove_handler(id)` | サブスクライバーを削除します。 |

### 出力の制御

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter モジュール

プラットフォームごとのアダプタを登録、起動、停止を管理するアダプタマネージャー。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(platform)` | アダプタインスタンスを取得 |
| `exists(platform)` | アダプタが登録されているか確認 |
| `enable(platform)` / `disable(platform)` | アダプタを有効化/無効化 |
| `is_enabled(platform)` | 有効化されているか確認 |
| `startup(platforms)` / `shutdown(platforms)` | アダプタを起動/停止 |
| `is_running(platform)` | アダプタが実行中か確認 |
| `list_running()` | 実行中のアダプタをすべてリスト表示 |
| `platforms` | すべてのプラットフォーム名のリストを取得 |

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

> 完全なアダプタ管理APIは、[アダプタシステムAPI](adapter-system.md) を参照してください。

## Module 模块

モジュールマネージャー。プラグインの登録、ロード、アンロードを管理します。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(name)` | モジュールインスタンスまたは遅延ロードプロキシを取得します（登録済みだがロードされていない場合はプロキシを返します） |
| `exists(name)` | 登録済みかどうかを確認します |
| `is_loaded(name)` | ロード済みかどうかを確認します |
| `is_enabled(name)` | 有効かどうかを確認します |
| `enable(name)` / `disable(name)` | モジュールを有効化/無効化します |
| `load(name)` / `unload(name)` | モジュールをロード/アンロードします |
| `list_registered()` | 登録済みモジュールを一覧表示します |
| `list_loaded()` | ロード済みモジュールを一覧表示します |
| `get_info(name)` | モジュール情報を取得します |
| `get_status_summary()` | モジュールの状態概要を取得します |

### 属性アクセス

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # 等価なショートカット
```

## Lifecycle モジュール

イベント駆動のライフサイクル管理機能を提供し、イベントの送信と監視を実現します。

### API 概要

| メソッド | 説明 |
|------|------|
| `on(event, priority=0)` | イベントハンドラを登録するデコレータ。ドット記法とワイルドカード `*` をサポート |
| `register(event, handler, priority=0)` | 関数形式でハンドラを登録 |
| `unregister(event, handler=None)` | ハンドラを削除 |
| `emit(event, data)` | 非同期でイベントをトリガー |
| `emit_sync(event, data)` | 同期でイベントをトリガー |
| `submit_event(event_type, msg, data, source)` | 標準形式のイベントを送信（旧バージョンとの互換性） |
| `start_timer(id)` / `stop_timer(id)` | パフォーマンス計測タイマー |

### 使用例

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"モジュール初期化: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"モジュールイベント: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})
```

> 完全な標準イベント一覧と詳細な使い方については、[ライフサイクル管理](../advanced/lifecycle.md) を参照してください。

## Router モジュール

HTTP/WebSocket ルーティングマネージャー。FastAPI + Uvicorn をベースに、デコレーターベースのルーティング、ミドルウェア、グループ化、リクエスト制限、CORS をサポートします。

> デコレーターベースのルーティング、WebSocket、ミドルウェア、レート制限、CORS、セキュリティヘッダーなど、ルーティング API の完全なドキュメントは、[ルーティングマネージャー](../advanced/router.md) を参照してください。

### 速見参考

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

# ルーティンググループ化
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## HTTP クライアントモジュール

統一されたネットワーククライアントで、HTTPリクエスト、WebSocket接続、接続プール管理、自動リトライ、リクエスト統計、ライフサイクルイベントの統合を提供します。

> 完全なネットワーククライアントのドキュメント（リクエストメソッド、レスポンスオブジェクト、WebSocketクライアント、例外体系など）は、[ネットワーククライアント](../advanced/http-client.md)を参照してください。

### 速攻リファレンス

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

## SDKのデバッグ

### dump_state()

フレームワークの現在の実行状態のスナップショットをエクスポートし、デバッグと診断に使用します。

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

返却される構造には、以下のサブシステムの状態が含まれます：

| フィールド | 説明 |
|------|------|
| `sdk` | SDKの初期化状態、Pythonバージョン、実行プラットフォーム、タイムスタンプ |
| `adapters` | 登録/起動済みのアダプタリスト、各プラットフォームのBotのオンライン状態 |
| `modules` | 登録/有効化/無効化/遅延ロードされたモジュールリスト |
| `events` | 各種イベントハンドラの数（message/notice/request/meta/commands） |
| `router` | サーバーの実行状態、HTTP/WebSocketルート数 |

> 2.5.2で追加

## 関連ドキュメント

- [イベントシステム API](event-system.md) - Event モジュール API
- [アダプターシステム API](adapter-system.md) - Adapter 管理 API
- [SQL クエリビルダー](../advanced/sql-builder.md) - SQL チェーン式クエリの完全なドキュメント
- [ルーティングマネージャー](../advanced/router.md) - ルーティングマネージャーの完全なドキュメント
- [ネットワーククライアント](../advanced/http-client.md) - ネットワーククライアントの完全なドキュメント
- [ライフサイクル管理](../advanced/lifecycle.md) - ライフサイクルの完全なドキュメント