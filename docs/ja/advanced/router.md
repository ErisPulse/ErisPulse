# ルーティングマネージャー

ErisPulseルーティングマネージャーは、統一されたHTTPおよびWebSocketルーティング管理を提供し、マルチアダプターのルーティング登録とライフサイクル管理をサポートしています。下部構造は抽象レイヤーによってカプセル化されています（現在はFastAPI + Uvicorn）。

## 概要

ルーティングマネージャーの主な機能：

- **デコレータールーティング**：`@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` デコレーターによるクイック登録をサポート
- **自動インジェクション**：ルートハンドラーはFastAPIの型をインポートする必要がなく、フレームワークが抽象オブジェクトを自動的にインジェクションします
- **ルートグループ化**：プレフィックスとバージョン番号付きの `RouteGroup` をサポート
- **ルーティングミドルウェア**：globパターンマッチングによるリクエスト傍受をサポート
- **レート制限**：スライディングウィンドウによるレートリミットを内蔵
- **CORSサポート**：ワンクリックでCross-Origin Resource Sharing（クロスオリジンリソース共有）を有効化
- **セキュリティヘッダー**：セキュリティレスポンスヘッダーを自動的に追加
- **自動ドキュメント**：OpenAPIベースのインタラクティブなドキュメント
- **WebSocketサポート**：完全なWebSocket接続管理、カスタム認証、ライフサイクルフック
- **ライフサイクル統合**：ErisPulseライフサイクルシステムと深く統合
- **SSL/TLSサポート**：HTTPSおよびWSSの安全な接続をサポート

## 抽象型

ErisPulseはサーバー側の抽象型を提供しており、モジュールはFastAPIに直接依存する必要がありません：

| 抽象型 | FastAPIでの対応 | 説明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTPリクエストのカプセル化、インターフェースは完全に互換性あり |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket接続のカプセル化、ライフサイクルフックを追加で提供 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket切断例外 |

> `.raw` 属性を使用して、基盤となるFastAPIネイティブオブジェクトにアクセスできます。FastAPIの型を直接使用するコードも完全に互換性があります。

## デコレータールーティング（推奨）

### HTTPデコレーター

```python
from ErisPulse.Core import router
@router.get("my_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}

# 抽象型を明示的に指定することも可能
from ErisPulse.Core import HttpRequest

@router.post("my_module", "/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

# FastAPIの型を引き続き使用することも完全に互換性があります
from fastapi import Request

@router.put("my_module", "/data/{item_id}")
async def update_data(request: Request):
    return {"updated": True}

@router.delete("my_module", "/data/{item_id}")
async def delete_data(request: Request):
    return {"deleted": True}
```

> **自動インジェクションルール**：ハンドラーの最初の引数名が `request` または `req` であり、FastAPIの型アノテーションがない場合、フレームワークは自動的に `HttpRequest` をインジェクションします。パラメータのない、またはリクエストパラメータ名以外のハンドラーには影響しません。

### WebSocketデコレーター

```python
from ErisPulse.Core import WebSocketConnection, WebSocketDisconnect

# 基本的なWebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# ライフサイクルフック付きのWebSocket
@router.ws("my_module", "/ws/chat")
async def chat(ws: WebSocketConnection):
    @ws.on_disconnect
    async def on_disconnect(ws, reason="unknown"):
        print(f"切断しました: {reason}")

    @ws.on_error
    async def on_error(ws, error=""):
        print(f"接続エラー: {error}")

    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 認証付きのWebSocket
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocketハンドラーと認証ハンドラーも自動インジェクションをサポートしています。パラメータのアノテーションが `fastapi.WebSocket` の場合はネイティブオブジェクトが渡され、それ以外の場合は `WebSocketConnection` が渡されます。

## 従来の登録方式

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

# レートリミットとドキュメント情報付き
router.register_http_route(
    module_name="my_module",
    path="/api/data",
    handler=data_handler,
    methods=["POST"],
    rate_limit="10/minute",
    summary="データインターフェース",
    tags=["API"],
)
```

### WebSocket登録

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
| `path` | WebSocketのパス | - |
| `handler` | ハンドラー関数 | - |
| `auth_handler` | 認証関数。`False` を返すと自動的に接続を閉じます | `None` |
| `auto_accept` | 自動的に `accept()` するかどうか | `True` |

> **推奨**：`auto_accept` をオフにするのではなく、`auth_handler` を使用して接続を確認してください。接続フローを完全に制御する必要がある場合にのみ `auto_accept=False` を設定してください。

## WebSocketライフサイクルフック

`WebSocketConnection` は切断やエラー時のコールバック登録を提供しており、手動での try/catch は不要です：

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # デコレーター方式での登録
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"切断理由: {reason}")

    # 直接呼び出しも可能
    async def on_err(ws, error=""):
        print(f"エラー: {error}")
    ws.on_error(on_err)

    # 通常のビジネスロジック
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## ルートグループ化

```python
# プレフィックス付きのルートグループを作成
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

ミドルウェアはglobパターンによるパスマッチングをサポートしています：

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

## レート制限

スライディングウィンドウアルゴリズムを使用してルートのレートリミットを行います：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

レート制限のフォーマット：`{回数}/{時間枠}`、例：`10/minute`、`100/hour`。

## CORS設定

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

`config.toml` で設定することも可能です：

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

`config.toml` で設定することも可能です：

```toml
[router.security]
enabled = true
```

## 自動ドキュメント

RouterはデフォルトでOpenAPIのインタラクティブなドキュメントを有効にしています：

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

ルーティングパスには、競合を避けるためにモジュール名がプレフィックスとして自動的に追加されます：

```python
# モジュール "my_module" にパス "/api" を登録
# 実際のアクセスパスは "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## 認証メカニズム

接続アクセスの制御には `auth_handler` を使用することを推奨します：

```python
from ErisPulse.Core import WebSocketConnection

async def auth_handler(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

# デコレーター方式
@router.ws("my_module", "/secure_ws", auth_handler=auth_handler)
async def secure_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")

# 従来の登録方式
router.register_websocket(
    module_name="my_module",
    path="/secure_ws",
    handler=websocket_handler,
    auth_handler=auth_handler,
)
```

`auth_handler` は接続確立後に実行され、`False` を返すと自動的に接続を閉じます（ステータスコード 1008）。

> 接続フローを完全に制御する必要がある場合（カスタムハンドシェイクプロトコルなど）にのみ、`auto_accept=False` を設定してください。

## システムルート

ルーティングマネージャーは2つのシステムルートを自動的に提供します：

### ヘルスチェック

```python
GET /health
# 戻り値:
{"status": "ok", "service": "ErisPulse Router"}
```

### ルートリスト

```python
GET /routes
# 登録されているすべてのルート情報を返します
```

## ライフサイクル統合

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"サーバーが起動しました: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("サーバーを停止しています...")
```

## ベストプラクティス

1. **抽象型を優先的に使用する**：`HttpRequest` / `WebSocketConnection` を `fastapi.Request` / `fastapi.WebSocket` の代わりに使用し、ハード依存を避ける
2. **自動インジェクションを活用する**：ハンドラーの最初の引数を `request` または `req` と名付けることで、型アノテーションなしで `HttpRequest` を取得できる
3. **明示的に module_name を渡す**：デコレーターの最初の引数はモジュール名でなければならず、省略できない
4. **ルートグループ化を使用する**：同じモジュールの複数のルートには `group()` を使用して整理する
5. **セキュリティを考慮する**：機密性の高い操作には認証メカニズムとセキュリティヘッダーを実装する
6. **適切なレートリミット**：高頻度のインターフェースにはレート制限を設定する
7. **ライフサイクルフックを使用する**：`@ws.on_disconnect` / `@ws.on_error` を使用してWebSocketの例外を処理し、手動の try/catch を避ける

## 関連ドキュメント

- [HTTPクライアント](http-client.md) - 組み込みHTTPクライアントを使用してリクエストを送信
- [モジュール開発ガイド](../developer-guide/modules/getting-started.md) - モジュールのルーティング登録について理解する
- [ベストプラクティス](../developer-guide/modules/best-practices.md) - ルーティングの使用に関する推奨事項