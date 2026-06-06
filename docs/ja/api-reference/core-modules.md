# コアモジュール API

このドキュメントでは、ErisPulseのコアモジュールのAPIのクイックリファレンスを提供します。メソッドの署名と簡単な説明が含まれています。詳細な使用方法と例については、各モジュールの「完全なドキュメント」リンクをクリックしてください。

## Storage モジュール

SQLite ベースのキーバリューストアシステムで、汎用 SQL のチェーン呼び出しクエリをサポートしています。

### 基本的な操作

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

### プロパティアクセス

```python
sdk.storage.my_key          # sdk.storage.get("my_key") と等価です
sdk.storage.my_key = "val"  # sdk.storage.set("my_key", "val") と等価です
```

### SQL チェーン呼び出しクエリ

Storage モジュールは、チェーン呼び出しスタイルの汎用 SQL クエリビルダーを提供し、カスタムテーブルの CRUD 操作をサポートしています。

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> 完全なチェーン呼び出しクエリ API（Select/Insert/Update/Delete/Where/OrderBy/Limit、AlterTable、トランザクションなど）については、[SQL クエリビルダー](../advanced/sql-builder.md)を参照してください。

### ストレージバックエンド抽象

`StorageManager` は `BaseStorage` 抽象基底クラスを継承しており、将来の他のストレージメディア（Redis、MySQL など）の拡張をサポートしています。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

## Config モジュール

TOML 形式の設定ファイル管理で、ドット（.）で区切られたキーパスをサポートしています。

### API 概要

| メソッド | 説明 |
|------|------|
| `getConfig(key, default)` | 設定を読み込みます。`"MyModule.subkey"` のようなドット区切りのパスをサポートします |
| `setConfig(key, value, immediate=False)` | 設定を書き込みます。`immediate=True` の場合、ファイルにすぐに保存されます |
| `force_save()` | メモリ内の設定を強制的にファイルに書き込みます |
| `reload()` | ファイルから設定を再読み込みします |

### 例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（毎 5 秒でバッチ保存）を使用します。`immediate=True` に設定すると、設定ファイルにすぐに永続化されます。設定の変更は `config.set` ライフサイクルイベントをトリガーします。

## Logger モジュール

モジュール化されたログシステムで、Rich 出力ベースで、サブロガーとモジュールレベルの制御をサポートしています。

### 基本的な使用方法

```python
sdk.logger.debug("デバッグ情報")
sdk.logger.info("実行情報")
sdk.logger.warning("警告情報")
sdk.logger.error("エラー情報")
sdk.logger.critical("致命的なエラー")
```

### サブロガー

```python
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("サブモジュールログ")

child_logger.get_child("utils")  # ネストされたサブモジュールをサポートします
```

### ログレベル制御

```python
sdk.logger.set_level("DEBUG")                          # グローバルレベル
sdk.logger.set_module_level("MyModule", "DEBUG")       # モジュールレベル
```

### 出力制御

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)
```

## Adapter モジュール

アダプターマネージャーで、マルチプラットフォームアダプターの登録、起動、シャットダウンを管理します。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(platform)` | アダプターインスタンスを取得します |
| `exists(platform)` | アダプターが登録されているか確認します |
| `enable(platform)` / `disable(platform)` | アダプターを有効化/無効化します |
| `is_enabled(platform)` | 有効になっているか確認します |
| `startup(platforms)` / `shutdown(platforms)` | アダプターを起動/シャットダウンします |
| `is_running(platform)` | アダプターが実行中か確認します |
| `list_running()` | 実行中のすべてのアダプターを一覧表示します |
| `platforms` | すべてのプラットフォーム名のリストを取得します |

### アダプターエベント

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

> 完全なアダプターマネジメント API については、[アダプターシステム API](adapter-system.md) を参照してください。

## Module モジュール

モジュールマネージャーで、プラグインの登録、読み込み、アンロードを管理します。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(name)` | モジュールインスタンスを取得します |
| `exists(name)` | 登録されているか確認します |
| `is_loaded(name)` | 読み込み済みか確認します |
| `is_enabled(name)` | 有効になっているか確認します |
| `enable(name)` / `disable(name)` | モジュールを有効化/無効化します |
| `load(name)` / `unload(name)` | モジュールを読み込み/アンロードします |
| `list_registered()` | 登録済みのモジュールを一覧表示します |
| `list_loaded()` | 読み込み済みのモジュールを一覧表示します |
| `get_info(name)` | モジュール情報を取得します |
| `get_status_summary()` | モジュールステータスの要約を取得します |

### プロパティアクセス

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # 等価なショートカット
```

## Lifecycle モジュール

イベント駆動型のライフサイクルマネージャーで、イベントの送信と監視機能を提供します。

### API 概要

| メソッド | 説明 |
|------|------|
| `on(event, priority=0)` | デコレーターを使用してイベントハンドラーを登録します。ドット区切りのマッチングとワイルドカード `*` をサポートします |
| `register(event, handler, priority=0)` | 関数型でハンドラーを登録します |
| `unregister(event, handler=None)` | ハンドラーを削除します |
| `emit(event, data)` | 非同期でイベントをトリガーします |
| `emit_sync(event, data)` | 同期でイベントをトリガーします |
| `submit_event(event_type, msg, data, source)` | 標準形式のイベントを送信します（旧バージョンと互換性あり） |
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

> 完全な標準イベントリストと詳細な使用方法については、[ライフサイクル管理](../advanced/lifecycle.md)を参照してください。

## Router モジュール

HTTP/WebSocket ルーターマネージャーで、FastAPI + Uvicorn ベースで、デコレーターローター、ミドルウェア、グループ化、レート制限、CORS をサポートしています。

> 完全なルーター API ドキュメント（デコレーターローター、WebSocket、ミドルウェア、レート制限、CORS、セキュリティヘッダーなど）については、[ルーター管理](../advanced/router.md)を参照してください。

### クイックリファレンス

```python
# HTTP ルーター
@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    return {"status": "ok"}

# WebSocket ルーター
@sdk.router.ws("MyModule", "/ws")
async def ws_handler(ws: WebSocketConnection):
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")

# ルーターグループ
group = sdk.router.group("MyModule", prefix="/v1")
@group.get("/users")
async def list_users(request: HttpRequest):
    return {"users": []}
```

## HTTP Client モジュール

統一された HTTP/WS クライアントで、aiohttp ベースで、リクエスト統計、リトライ、ログ、ErisPulse 例外体系を提供します。

> 完全な HTTP クライアントドキュメント（リクエストメソッド、レスポンスオブジェクト、WebSocket クライアント、例外体系など）については、[HTTP クライアント](../advanced/http-client.md)を参照してください。

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

## 関連ドキュメント

- [イベントシステム API](event-system.md) - Event モジュール API
- [アダプターシステム API](adapter-system.md) - Adapter 管理 API
- [SQL クエリビルダー](../advanced/sql-builder.md) - SQL チェーン呼び出しクエリの完全なドキュメント
- [ルーター管理](../advanced/router.md) - ルーターマネージャーの完全なドキュメント
- [HTTP クライアント](../advanced/http-client.md) - HTTP クライアントの完全なドキュメント
- [ライフサイクル管理](../advanced/lifecycle.md) - ライフサイクルの完全なドキュメント