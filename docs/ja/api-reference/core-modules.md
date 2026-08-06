# コアモジュール API

このドキュメントは、ErisPulse コアモジュールの API クイックリファレンスを提供します。メソッドシグネチャと簡単な説明が含まれています。詳細な使用法と例については、各モジュールの「完全なドキュメント」リンクをクリックしてください。

詳細な用法と例については、各モジュールの「完全なドキュメント」リンクをクリックしてください。

## Storage モジュール

SQLite をベースとしたキーバリューストアシステムで、汎用的な SQL のチェーンクエリをサポートしています。

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

### プロパティアクセス

```python
sdk.storage.my_key          # sdk.storage.get("my_key") と同等
sdk.storage.my_key = "val"  # sdk.storage.set("my_key", "val") と同等
```

### SQL チェーンクエリ

Storage モジュールは、チェーンコールスタイルの汎用的な SQL クエリビルダーを提供し、カスタムテーブルの CRUD 操作をサポートしています。

```python
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})

sdk.storage.Table("users").Insert({"name": "Alice"}).Execute()
rows = sdk.storage.Table("users").Select("name").Where("id > ?", 0).Execute()
```

> 完全なチェーンクエリ API（Select/Insert/Update/Delete/Where/OrderBy/Limit、AlterTable、トランザクション等）については、[SQL クエリビルダー](../advanced/sql-builder.md) を参照してください。

### ストレージバックエンド抽象化

`StorageManager` は `BaseStorage` 抽象基底クラスを継承しており、他のストレージ媒体（Redis、MySQL など）への拡張をサポートしています。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder
```

### 非同期インターフェース

Storage および Config モジュールは両方とも非同期メソッド（プレフィックス `a`）を提供しており、非同期ハンドラー内で安全に呼び出すことができます。同期メソッドは維持されたままです。既存のコードを変更する必要はありません。

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

## Config モジュール

TOML 形式の設定ファイル管理。ドット区切りのキーパスをサポートします。

### API 概要

| メソッド | 説明 |
|------|------|
| `getConfig(key, default)` | 設定を読み込みます。ドット区切りのパス（例: `"MyModule.subkey"`）をサポートします |
| `setConfig(key, value, immediate=False)` | 設定を書き込みます。`immediate=True` の場合、ファイルに即座に保存されます |
| `force_save()` | メモリ内の設定を強制的にファイルに書き込みます |
| `reload()` | ファイルから設定を再読み込みします |
| `agetConfig(key, default)` | 非同期で設定を読み込みます |
| `asetConfig(key, value, immediate)` | 非同期で設定を書き込みます |
| `aforce_save()` | 非同期で強制保存します |
| `areload()` | 非同期で再読み込みします |

### 例

```python
config = sdk.config.getConfig("MyModule", {})
value = sdk.config.getConfig("MyModule.timeout", 30)

sdk.config.setConfig("MyModule", {"key": "value"})
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` はデフォルトで遅延書き込み（5 秒ごとにバッチ保存）を採用しています。`immediate=True` を設定すると、設定ファイルに即座に永続化できます。設定の変更は `config.set` ライフサイクルイベントをトリガーします。

## Logger モジュール

モジュール化されたログシステム。Rich 出力をベースとし、サブロガーおよびモジュール単位での制御をサポートします。

### 基本的な使い方

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

child_logger.get_child("utils")  # ネストに対応
```

### ログレベル制御

```python
sdk.logger.set_level("DEBUG")                          # グローバルレベル
sdk.logger.set_module_level("MyModule", "DEBUG")       # モジュールレベル

# サポートされるレベル（低い順）：
# TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
# TRACE は最低レベルで、フレームワーク内部の詳細なデバッグ情報（イベント配信、ルート登録など）を出力します
sdk.logger.set_level("TRACE")                          # 全ログ有効化
```

### ログ購読（プッシュモード）

Dashboard などのモジュールが構造化ログをリアルタイムで受信するためのものです。レベルによるフィルタリングおよび履歴ログの再送をサポートします。

> **低レベルログの明示的な購読**：購読器の `min_level` は、グローバルログレベルよりも低く設定できます。この場合、低レベルログは**マッチする購読器にのみプッシュ**され、コンソールには出力されず、メモリにも書き込まれないため、メインログストリームの汚染を回避できます。
>
> ```python
> # グローバルレベルが INFO でも、DEBUG ログだけ個別に購読可能
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
| `handler(id, *, min_level)(func)` | デコレータ / 直接呼び出しの両用。`id` が空の場合は関数名を取得します。`min_level` はグローバルレベルより低くできます（低レベルログは購読器にのみプッシュされ、コンソール/メモリへは入りません）。登録時に自動で履歴ログを再送します |
| `remove_handler(id)` | 購読器を削除します |

### 出力制御

```python
sdk.logger.set_output_file("app.log")
sdk.logger.save_logs("log.txt")
sdk.logger.get_logs("MyModule")
sdk.logger.set_memory_limit(1000)

## アダプターモジュール

アダプターマネージャーは、マルチプラットフォームアダプターの登録、起動、およびシャットダウンを管理します。

### API 概要

| メソッド | 説明 |
|------|------|
| `get(platform)` | アダプターメソッドの取得 |
| `exists(platform)` | アダプターが登録されているかチェック |
| `enable(platform)` / `disable(platform)` | アダプターの有効化/無効化 |
| `is_enabled(platform)` | 有効になっているかチェック |
| `startup(platforms)` / `shutdown(platforms)` | アダプターの起動/シャットダウン |
| `is_running(platform)` | アダプターが実行中かチェック |
| `list_running()` | 実行中のアダプターを一覧表示 |
| `platforms` | 全プラットフォーム名リストの取得 |

### アダプターイベント

```python
@sdk.adapter.on("message")
async def handle_message(event):
    pass

@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass
```

### Bot ステータス確認

```python
sdk.adapter.get_bot_info("telegram", "123456")
sdk.adapter.list_bots("telegram")
sdk.adapter.is_bot_online("telegram", "123456")
sdk.adapter.get_status_summary()
```

> 完全なアダプターマネジメント API については、[アダプターシステム API](docs/ja/adapter-system.md) を参照してください。

## Module モジュール

モジュールマネージャーは、プラグインの登録、読み込み、アンインストールを管理します。

### API サマリー

| メソッド | 説明 |
|------|------|
| `get(name)` | モジュールインスタンスを取得する、または遅延読み込みプロキシを取得する（登録済みだが未読込の場合はプロキシを返す） |
| `exists(name)` | 登録済みかどうかを確認する |
| `is_loaded(name)` | 読み込まれたかどうかを確認する |
| `is_enabled(name)` | 有効かどうかを確認する |
| `enable(name)` / `disable(name)` | モジュールを有効化/無効化する |
| `load(name)` / `unload(name)` | モジュールを読み込み/アンインストールする |
| `list_registered()` | 登録済みモジュールを一覧表示する |
| `list_loaded()` | 読み込み済みモジュールを一覧表示する |
| `get_info(name)` | モジュール情報を取得する |
| `get_status_summary()` | モジュールステータスサマリーを取得する |

### プロパティへのアクセス

```python
module = sdk.module.get("ModuleName")
module = sdk.module.ModuleName
module = sdk.ModuleName  # 同等のショートカット

## Lifecycle モジュール

イベント駆動のライフサイクルマネージャーで、イベントの送信と監視機能を提供します。

### API 概要

| メソッド | 説明 |
|------|------|
| `on(event, priority=0)` | デコレータでイベントハンドラーを登録。ドット表記のマッチングとワイルドカード `*` をサポート |
| `register(event, handler, priority=0)` | 関数型でハンドラーを登録 |
| `unregister(event, handler=None)` | ハンドラーを削除 |
| `emit(event, data)` | 非同期でイベントを発行 |
| `emit_sync(event, data)` | 同期的にイベントを発行 |
| `submit_event(event_type, msg, data, source)` | 標準形式のイベントを送信（旧版との互換性） |
| `start_timer(id)` / `stop_timer(id)` | パフォーマンス計時用タイマー |

### サンプル

```python
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"モジュール初期化: {event_data}")

@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"モジュールイベント: {event_data}")

await sdk.lifecycle.emit("custom.event", {"key": "value"})
```

> 標準イベントの完全なリストと詳細な使い方については、[ライフサイクル管理](../advanced/lifecycle.md) を参照してください。

## Router モジュール

HTTP/WebSocket ルーター管理機能。FastAPI + Uvicorn をベースに、デコレータールーター、ミドルウェア、グルーピング、レート制限、CORS をサポートします。

> 詳細なルーター API ドキュメント（デコレータールーター、WebSocket、ミドルウェア、レート制限、CORS、セキュリティヘッダー等）については、[ルーター管理器](../advanced/router.md) を参照してください。

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

## HTTP Client モジュール

統合されたネットワーククライアントで、HTTP リクエスト、WebSocket 接続、コネクションプールの管理、自動再試行、リクエスト統計、およびライフサイクルイベントの統合を提供します。

> リクエストメソッド、レスポンスオブジェクト、WebSocketクライアント、例外体系などの、完全なネットワーククライアントのドキュメントについては、[ネットワーククライアント](../advanced/http-client.md) を参照してください。

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

## SDK デバッグ

### dump_state()

現在実行中のフレームワークの状態スナップショットをエクスポートし、デバッグおよび診断に使用します。

```python
import json
state = sdk.dump_state()
print(json.dumps(state, indent=2, ensure_ascii=False, default=str))
```

返される構造には以下のサブシステムの状態が含まれます：

| フィールド | 説明 |
|------|------|
| `sdk` | SDK の初期化状態、Python バージョン、実行プラットフォーム、タイムスタンプ |
| `adapters` | 登録済み/起動済みのアダプタ一覧、各プラットフォームの Bot オンライン状態 |
| `modules` | 登録済み/有効/無効/遅延読み込みのモジュール一覧 |
| `events` | 各種イベントハンドラの数（message/notice/request/meta/commands） |
| `router` | サーバーの実行状態、HTTP/WebSocket ルート数 |

> 2.5.2 で追加

## 関連ドキュメント

- [イベントシステム API](event-system.md) - Event モジュール API
- [アダプタシステム API](adapter-system.md) - Adapter 管理 API
- [SQL クエリビルダ](../advanced/sql-builder.md) - SQL チェーンクエリ完全ドキュメント
- [ルーターマネージャー](../advanced/router.md) - ルーターマネージャー完全ドキュメント
- [ネットワーククライアント](../advanced/http-client.md) - ネットワーククライアント完全ドキュメント
- [ライフサイクル管理](../advanced/lifecycle.md) - ライフサイクル完全ドキュメント