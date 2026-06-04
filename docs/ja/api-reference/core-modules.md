# コアモジュール API

このドキュメントでは、ErisPulseのコアモジュールAPIについて詳しく説明します。

## Storage モジュール

### 基本的な操作

```python
from ErisPulse import sdk

# 値の設定
sdk.storage.set("key", "value")

# 値の取得
value = sdk.storage.get("key", default_value)

# すべてのキーを取得
keys = sdk.storage.keys()

# 値を削除
sdk.storage.delete("key")
```

### トランザクション操作

```python
# トランザクションを使用してデータの一貫性を確保
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # いずれかの操作が失敗した場合、すべての変更はロールバックされます
```

### バッチ操作

```python
# 一括設定
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# 一括取得
values = sdk.storage.get_multi(["key1", "key2", "key3"])

# 一括削除
sdk.storage.delete_multi(["key1", "key2", "key3"])
```

### SQL チェーン呼び出しクエリ

Storage モジュールは、チェーン呼び出しスタイルの汎用 SQL クエリビルダーを提供し、カスタムテーブルの CRUD 操作をサポートしています。

> 完全なドキュメントについては、[SQL クエリビルダー](../advanced/sql-builder.md)を参照してください。

```python
from ErisPulse import sdk

# カスタムテーブルの作成
sdk.storage.CreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "age": "INTEGER DEFAULT 0"
})

# データの挿入
sdk.storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()

# 一括挿入
sdk.storage.Table("users").InsertMulti([
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]).Execute()

# データのクエリ
rows = (sdk.storage.Table("users")
    .Select("name", "age")
    .Where("age > ?", 18)
    .OrderBy("name")
    .Limit(10)
    .Execute())

# データの更新
sdk.storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()

# データの削除
sdk.storage.Table("users").Delete().Where("name = ?", "Bob").Execute()

# カウント
count = sdk.storage.Table("users").Where("age > ?", 18).Count()

# 存在性のチェック
exists = sdk.storage.Table("users").Where("name = ?", "Alice").Exists()

# 1件のレコードを取得
row = sdk.storage.Table("users").Select("name", "age").Where("name = ?", "Alice").ExecuteOne()

# テーブル構造の変更
sdk.storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
sdk.storage.AlterTable("users").RenameTo("members").Execute()

# テーブルが存在するか確認
if sdk.storage.HasTable("users"):
    sdk.storage.DropTable("users")

# トランザクション内でのチェーン操作
with sdk.storage.transaction():
    sdk.storage.Table("users").Insert({"name": "Dave", "age": 40}).Execute()
    sdk.storage.Table("users").Update({"age": 41}).Where("name = ?", "Dave").Execute()

# クエリ条件の再利用
base = sdk.storage.Table("users").Where("age > ?", 20)
rows = base.copy().Select("name").OrderBy("name").Limit(5).Execute()
count = base.copy().Count()
```

### ストレージバックエンド抽象

`StorageManager` は `BaseStorage` 抽象基底クラスを継承しており、将来の他のストレージメディア（Redis、MySQL など）の拡張をサポートしています。

```python
from ErisPulse.Core.Bases.storage import BaseStorage, BaseQueryBuilder

# BaseStorage は統一されたインターフェースを定義します：get/set/delete/Table/CreateTable/DropTable など
# BaseQueryBuilder はチェーンクエリインターフェースを定義します：Select/Insert/Update/Delete/Where/OrderBy/Limit など
```

## Config モジュール

### 設定の読み込み

```python
from ErisPulse import sdk

# 設定を取得
config = sdk.config.getConfig("MyModule", {})

# ネストされた設定を取得
value = sdk.config.getConfig("MyModule.subkey.value", "default")
```

### 設定の書き込み

```python
# 設定を設定
sdk.config.setConfig("MyModule", {"key": "value"})

# ネストされた設定を設定
sdk.config.setConfig("MyModule.subkey.value", "new_value")
```

### 設定の例

```python
def _load_config(self):
    config = sdk.config.getConfig("MyModule")
    if not config:
        # デフォルト設定を作成
        default_config = {
            "api_url": "https://api.example.com",
            "timeout": 30,
            "cache_ttl": 3600
        }
        sdk.config.setConfig("MyModule", default_config, immediate=True)  # 第3引数がTrueの場合、設定は即座に保存されます。ユーザーが設定ファイルを直接変更できるように便利です。
        return default_config
    return config
```

## Logger モジュール

### 基本的なログ

```python
from ErisPulse import sdk

# 異なるログレベル
sdk.logger.debug("デバッグ情報")
sdk.logger.info("実行情報")
sdk.logger.warning("警告情報")
sdk.logger.error("エラー情報")
sdk.logger.critical("致命的なエラー")
```

### 子ログ記録子

```python
# 子ロガーを取得
child_logger = sdk.logger.get_child("MyModule")
child_logger.info("サブモジュールログ")

# サブモジュールはさらにサブモジュールを持つことができ、これによりログ出力をより精確に制御できます
child_logger.get_child("utils")
```

### ログ出力

```python
# 出力ファイルを設定
sdk.logger.set_output_file("app.log")

# ファイルにログを保存
sdk.logger.save_logs("log.txt")
```

## Adapter モジュール

### アダプターの取得

```python
from ErisPulse import sdk

# アダプターインスタンスを取得
adapter = sdk.adapter.get("platform_name")

# プロパティを介してアクセス
adapter = sdk.adapter.platform_name
```

### アダプターエベント

```python
# 標準イベントを監視
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 特定プラットフォームのイベントを監視
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# プラットフォームネイティブイベントを監視
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### アダプター管理

```python
# すべてのプラットフォームを取得
platforms = sdk.adapter.platforms

# アダプターが存在するか確認
exists = sdk.adapter.exists("platform_name")

# アダプターを有効化/無効化
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# アダプターを起動/シャットダウン
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown(["platform1", "platform2"])

# アダプターが実行中か確認
is_running = sdk.adapter.is_running("platform_name")

# 実行中のすべてのアダプターを一覧表示
running = sdk.adapter.list_running()
```

## Module モジュール

### モジュールの取得

```python
from ErisPulse import sdk

# モジュールインスタンスを取得
module = sdk.module.get("ModuleName")

# プロパティを介してアクセス
module = sdk.module.ModuleName
module = sdk.ModuleName
```

### モジュール管理

```python
# モジュールが存在するか確認
exists = sdk.module.exists("ModuleName")

# モジュールがロード済みか確認
is_loaded = sdk.module.is_loaded("ModuleName")

# モジュールが有効か確認
is_enabled = sdk.module.is_enabled("ModuleName")

# モジュールを有効化/無効化
sdk.module.enable("ModuleName")
sdk.module.disable("ModuleName")

# モジュールをロード
await sdk.module.load("ModuleName")

# モジュールをアンロード
await sdk.module.unload("ModuleName")

# ロード済みのモジュールを一覧表示
loaded = sdk.module.list_loaded()

# 登録済みのモジュールを一覧表示
registered = sdk.module.list_registered()

# モジュール情報を取得
info = sdk.module.get_info("ModuleName")

# モジュールステータスのサマリーを取得
summary = sdk.module.get_status_summary()
# {"modules": {"ModuleName": {"status": "loaded", "enabled": True, "is_base_module": True}}}

# モジュールが実行中か確認（is_loaded と同等）
is_running = sdk.module.is_running("ModuleName")

# 実行中のすべてのモジュールを一覧表示
running = sdk.module.list_running()
```

## Lifecycle モジュール

### イベントの送信

```python
from ErisPulse import sdk

# カスタムイベントを送信
await sdk.lifecycle.submit_event(
    "custom.event",
    data={"key": "value"},
    source="MyModule",
    msg="カスタムイベントの説明"
)
```

### イベント監視

```python
# 特定のイベントを監視
@sdk.lifecycle.on("module.init")
async def handle_module_init(event_data):
    print(f"モジュール初期化: {event_data}")

# 親レベルのイベントを監視
@sdk.lifecycle.on("module")
async def handle_any_module_event(event_data):
    print(f"モジュールイベント: {event_data}")

# すべてのイベントを監視
@sdk.lifecycle.on("*")
async def handle_any_event(event_data):
    print(f"システムイベント: {event_data}")
```

### タイマー

```python
# タイマーを開始
sdk.lifecycle.start_timer("my_operation")

# ... 操作を実行 ...

# 持続時間を取得
duration = sdk.lifecycle.get_duration("my_operation")

# タイマーを停止
total_time = sdk.lifecycle.stop_timer("my_operation")
```

## Router モジュール

### 抽象型

Router は2つの型アノテーションスタイルをサポートしています：

```python
# ErisPulse抽象型（推奨、移植性が高い）
from ErisPulse.Core import HttpRequest, WebSocketConnection

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}

# FastAPIネイティブ型（既存のコードとの互換性）
from fastapi import Request, WebSocket

@sdk.router.get("MyModule", "/api2")
async def handler(request: Request):
    return {"status": "ok"}
```

> ルーターはパラメータアノテーションに基づいて対応するタイプのオブジェクトを自動的に注入します。詳細については、[ルーター管理](../advanced/router.md)を参照してください。

### デコレーターローター（推奨）

```python
from ErisPulse import sdk
from fastapi import Request

# HTTPルーターデコレーター
@sdk.router.http("MyModule", "/api", methods=["GET", "POST"])
async def api_handler(request: Request):
    return {"status": "ok"}

# 短縮メソッドデコレーター
@sdk.router.get("MyModule", "/info")
async def get_info(request: Request):
    return {"module": "MyModule"}

@sdk.router.post("MyModule", "/data")
async def post_data(request: Request):
    data = await request.json()
    return {"received": data}

@sdk.router.put("MyModule", "/data/{item_id}")
async def put_data(request: Request):
    return {"updated": True}

@sdk.router.delete("MyModule", "/data/{item_id}")
async def delete_data(request: Request):
    return {"deleted": True}

# WebSocketデコレーター
from fastapi import WebSocket

@sdk.router.ws("MyModule", "/ws")
async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# 認証付きWebSocketデコレーター
async def ws_auth(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

@sdk.router.ws("MyModule", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

### 従来の登録方式

```python
from ErisPulse import sdk
from fastapi import Request

async def handler(request: Request):
    data = await request.json()
    return {"status": "ok", "data": data}

sdk.router.register_http_route(
    module_name="MyModule",
    path="/api",
    handler=handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="データインターフェース",
    tags=["API"],
)

sdk.router.unregister_http_route("MyModule", "/api")
```

### WebSocketルーター

```python
from ErisPulse import sdk
from fastapi import WebSocket

async def websocket_handler(websocket: WebSocket):
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")

# 基本的な登録（接続を自動的に受け入れる）
sdk.router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# 認証付きの登録（推奨：auth_handlerを使用して接続を制御）
async def auth_handler(websocket: WebSocket) -> bool:
    token = websocket.query_params.get("token")
    return token == "secret"

sdk.router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)

# ルーターを解除
sdk.router.unregister_websocket("MyModule", "/ws")
```

**パラメータの説明：**

| パラメータ | 説明 | デフォルト値 |
|------|------|--------|
| `module_name` | モジュール名（必須） | - |
| `path` | WebSocketパス | - |
| `handler` | ハンドラー関数 | - |
| `auth_handler` | 認証関数。`False`を返すと接続が自動的に閉じられます | `None` |
| `auto_accept` | `accept()` を自動的に呼び出すかどうか | `True` |

> **推奨**: `auth_handler` を使用して接続確認を行い、`auto_accept` を無効化（閉じる）の代わりにしてください。接続フローを完全に制御する必要がある場合にのみ、`auto_accept=False` を設定してください。

### ルーターグループ

```python
# ルーターグループを作成
group = sdk.router.group("MyModule", prefix="/v1")

# グループ内でルーターを登録
@group.get("/users")
async def list_users(request: Request):
    return {"users": []}

@group.post("/users")
async def create_user(request: Request):
    return {"created": True}

# バージョン付きのグループ
v2 = sdk.router.group("MyModule", prefix="/v2", version="2")
```

### ルーターミドルウェア

```python
# グローバルミドルウェア（globマッチング）
@sdk.router.middleware("/MyModule/*")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        return {"error": "Unauthorized"}
    response = await call_next(request)
    return response

# 特定のパスミドルウェア
@sdk.router.middleware("/MyModule/admin/*")
async def admin_middleware(request: Request, call_next):
    return await call_next(request)
```

### レート制限

```python
# ルーターにレート制限を設定（スライディングウィンドウ）
@sdk.router.get("MyModule", "/limited", rate_limit="10/minute")
async def limited_endpoint(request: Request):
    return {"ok": True}

@sdk.router.post("MyModule", "/submit", rate_limit="5/minute")
async def submit_data(request: Request):
    return {"submitted": True}
```

### CORS設定

```python
# コードによる設定
sdk.router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 設定ファイルによる設定（config.toml）
# [router.cors]
# allow_origins = ["https://example.com"]
# allow_methods = ["GET", "POST"]
# allow_headers = ["*"]
```

### セキュリティヘッダー

```python
# セキュリティヘッダーを自動的に追加
sdk.router.setup_security_headers()

# 設定ファイルによる設定（config.toml）
# [router.security]
# enabled = true
```

### 自動ドキュメント

```python
# RouterはデフォルトでOpenAPIドキュメントを有効にします
# ドキュメントを無効化
sdk.router.disable_docs()

# カスタムドキュメント情報を設定
sdk.router.set_docs_info(
    title="My API",
    description="API ドキュメント",
    version="1.0.0"
)
```

### ルーター情報

```python
app = sdk.router.get_app()
```

## HTTP Client モジュール

### 基本的なリクエスト

```python
from ErisPulse.Core import client

# GETリクエスト
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# POSTリクエスト
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# PUT / DELETE / PATCH
resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})

# 一般的なrequestメソッド
resp = await client.request("OPTIONS", "https://api.example.com/resource")
```

### レスポンスオブジェクト

```python
from ErisPulse.Core import client

resp = await client.get("https://api.example.com/users")

resp.status        # int - HTTPステータスコード (例: 200, 404)
resp.reason        # str | None - ステータスの説明 (例: "OK")
resp.headers       # レスポンスヘッダー (大文字・小文字を区別しない)
resp.content_type  # str | None - Content-Type
resp.url           # 最終的な URL (リダイレクトにより変更される場合があります)
resp.raw           # 基底のネイティブレスポンスオブジェクト (現在は aiohttp.ClientResponse)

# レスポンスボディの読み込み
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # JSONの解析
text = await resp.text("gbk")  # エンコーディングを指定
```

### リクエストパラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `url` | `str