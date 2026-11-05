# ルーティングマネージャー

> [!TIP]  
> **この章を読む必要があるのはいつか**：HTTP / WebSocket / SSE ルーティング（接続プールによるブロードキャスト含む）が必要な場合。不要であればスキップしても、他の機能の使用に影響はありません。

ErisPulse ルーティングマネージャーは、HTTP および WebSocket ルーティングを統一的に管理し、複数のアダプタールーティングの登録とライフサイクル管理をサポートします。内部では抽象層を封印しており、現在は FastAPI + Uvicorn が使用されています。

## 概要

ルーティングマネージャーの主な機能は以下の通りです：

- **デコレータルーティング**：`@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` デコレータによる登録
- **自動インジェクション**：ルーティングハンドラは FastAPI クラスをインポートする必要がなく、フレームワークが抽象オブジェクトを自動的に注入します
- **ルーティンググループ**：接頭辞とバージョン付きの `RouteGroup` をサポート
- **ルーティングミドルウェア**：glob パターンマッチングによるリクエストのインターセプト
- **レート制限**：スライディングウィンドウによる制限
- **CORS サポート**：クロスドメインリソース共有をワンクリックで有効化
- **セキュリティヘッダー**：自動的にセキュリティレスポンスヘッダーを追加
- **自動ドキュメント**：OpenAPI に基づくインタラクティブなドキュメント
- **WebSocket サポート**：WebSocket 接続の完全な管理、カスタム認証、ライフサイクルフック
- **ライフサイクル統合**：ErisPulse のライフサイクルシステムと深く統合
- **SSL/TLS サポート**：HTTPS および WSS セキュア接続をサポート
- **ホームエントリ**：モジュールがルートルート `/` に登録可能なクイックエントリボタンをサポートし、国際化も可能

## 抽象型

ErisPulse はサーバーアプリケーションの抽象型を提供しており、モジュールは FastAPI に直接依存する必要がありません。

| 抽象型 | FastAPI 対応 | 説明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP リクエストをラップし、インターフェースは完全に互換性がある |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket 接続をラップし、ライフサイクルフックを追加 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket 接続切断時の例外 |

> `WebSocketConnection` は `WebSocketConnectionBase` を継承しており、クライアント側の WebSocket (`ClientWebSocket`) と `send/receive/iter/close` インターフェースを共有します。クライアントとサーバーの WebSocket は同じビジネスロジックコードを使用できます。  
> `.raw` 属性を介して、下層の FastAPI ネイティブオブジェクトにアクセスできます。FastAPI クラスを使用したコードも完全に互換性があります。

## デコレータルーティング（推奨）

### 登録形態：単引数（推奨）と二引数

デコレータルーティングは二つの形態をサポートしていますが、**単引数の形態を推奨**します。これは、コマンド / イベントトリガーと同様に、名前空間が自動的に現在のモジュールに属します。

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

# 二引数：明示的にモジュール名を指定（ルールは変更なし、跨モジュール/ツールコード登録時に使用）
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]  
> 単引数の形態は、モジュール/アダプターの**ロードコンテキスト**で登録する必要があります（ロード時にフレームワークが自動的に名前空間を注入）。  
> 名前空間が属さないコンテキストで呼び出すと、`ValueError` が発生し、明示的にモジュール名を渡すように通知されます。

### HTTP デコレータ

```python
from ErisPulse import router, HttpRequest

# 抽象型を明示的に指定することも可能
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

> **自動インジェクションルール**：ハンドラの最初の引数が `request` または `req` で、FastAPI 型の注釈がない場合、フレームワークは自動的に `HttpRequest` を注入します。引数がない、またはリクエスト引数名でないハンドラは影響を受けません。

#### レスポンス返却の約束事（2.10+）

ハンドラの返り値は**タプルの約束事**（推奨の書き方、明確にステータスコードを制御）をサポートし、dict/str/Response は従来通りです。

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "token 无效"}, 401
    # (body, status_code, headers) さらにレスポンスヘッダーも追加可能
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# または respond() ヘルパー関数を使用（message はレスポンス本体に自動的にマージ）
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

パス/クエリパラメータは FastAPI のネイティブ注釈（`item_id: int`、`page: int = 1`）を使用して直接指定できます。  
ミドルウェアは[ルーティングミドルウェア](#ルーティングミドルウェア)の節を参照してください。

### WebSocket デコレータ

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# 基本的な WebSocket（単引数形態）
@router.ws("ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# ライフサイクルフック付きの WebSocket
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

# 認証付きの WebSocket
async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    return token == "secret"

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocket ハンドラと認証ハンドラも自動インジェクションが可能です。引数の注釈がなくても `WebSocketConnection` を取得できます。`fastapi.WebSocket` を注釈しても、ネイティブオブジェクトを渡すことができますが、抽象型の使用を推奨します。

### 接続の自動登録（接続プール、2.10+）

`@ws` / `@sse` で確立された接続は**デフォルトでフレームワークの接続プールに自動登録**されます（`track=False` でオフにできます）：  
ハンドラ内では `ws.id` / `ws.join_group(...)` が使用可能で、任意のモジュールは `connections.list(namespace=...)` を使用して、本モジュールの接続を確認し、グループにブロードキャストできます。  
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

# レート制限とドキュメント情報付き
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
| `auth_handler` | 認証関数、False を返すと接続が自動的に閉じられる | `None` |
| `auto_accept` | 自動的に `accept()` するかどうか | `True` |

> **推奨**：`auth_handler` を使用して接続を確認する、`auto_accept` を `False` に設定するのではなく。接続フローを完全に制御する必要がある場合にのみ `auto_accept=False` を設定してください。

## WebSocket ライフサイクルフック

`WebSocketConnection` は切断とエラーのコールバックを登録するためのメソッドを提供しており、手動の try/catch は不要です。

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # デコレータ方式で登録
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"切断原因: {reason}")

    # 直接呼び出すことも可能
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

ミドルウェアは glob パターンによるパスマッチをサポートします：

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

2.7.0 以降、各 HTTP リクエストには `X-Request-ID` という関連 ID が含まれており、ログ / リンクトレースの連携に使用されます：

- **生成ルール**：まず、クライアントが送信した `X-Request-ID` リクエストヘッダーを優先します（分散トレースの場面）；なければ、UUID を自動生成します
- **レスポンスヘッダー**：レスポンスには `X-Request-ID` が返されます。クライアントはリクエストとログを対応させるために使用できます
- **ライフサイクルイベント**：`server.request` および `server.response` イベントのデータに `request_id` フィールドが追加されます

```python
# モジュール内でリクエストイベントをリッスンし、request_id でリクエスト-レスポンスを連携
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

クライアントは、サービス間トレースのために独自の ID を指定できます：

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## レート制限

ルーティングに対してスライディングウィンドウアルゴリズムによる制限を実装します：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

レート制限の形式：`{回数}/{時間ウィンドウ}`、例えば `10/minute`、`100/hour` など。

## CORS 設定

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

`config.toml` でも設定できます：

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

`config.toml` でも設定できます：

```toml
[router.security]
enabled = true
```

## 自動ドキュメント

Router はデフォルトで OpenAPI によるインタラクティブなドキュメントを有効にしています：

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
> ルーティングパス（モジュール名プレフィックスを含む）は**大文字小文字を区別**します。登録時のモジュール名が大文字小文字で、実際のパスもその通りです：モジュール名が `Test` の場合、`/api` を登録した実際のパスは `/Test/api` です。`/test/api` にアクセスすると 404 が返されます。

## システムルーティング

ルーティングマネージャーは以下のシステムルーティングを自動的に提供します：

### ヘルスチェック

```
GET /health
# 返却値:
{"status": "ok", "service": "ErisPulse Router"}
```

### ホームページ

```
GET /
# 返却値: ErisPulse ブランドページ
```

ルートパス `/` には ErisPulse ブランドページが表示され、Dashboard の利用可能性を自動的に検出し、エントリーボタンを追加します。

## ホームエントリ

ルーティングマネージャーは外部モジュールがルートパス `/` にクイックエントリーボタンを登録できるようにし、ユーザーがモジュールの管理ページにすばやくアクセスできるようにします。

### エントリの登録

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

# 国際化に対応した登録（i18n ディクショナリ形式）
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "私のパネル"},
    url="/mymodule/admin",
)
```

**パラメータの説明：**

| パラメータ | 型 | 説明 | 必須 |
|------|------|------|------|
| `name` | `str` / `dict` | ボタンに表示するテキスト；`{"i18n": "key", "default": "テキスト"}` ディクショナリを渡すと国際化を使用 | 是 |
| `url` | `str` | ボタンのリンク先 | 是 |
| `icon_svg` | `str` | オプションの SVG イコンマーク | 否 |

### Dashboard の自動登録

`sdk.Dashboard` が利用可能であることを検出した場合、ルーティングマネージャーは Dashboard ボタンをエントリーリストの先頭に自動的に追加します。手動での登録は不要です。

## ライフサイクルの統合

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"サーバーが起動しました: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("サーバーが停止しています...")
```

## 最適な実践方法

1. **抽象型を優先する**：`HttpRequest` / `WebSocketConnection` を `fastapi.Request` / `fastapi.WebSocket` に代えて使用し、ハード依存を避ける
2. **自動インジェクションを活用する**：ハンドラの最初の引数を `request` または `req` とし、型注釈なしでも `HttpRequest` を取得できる
3. **単引数形態を優先する**：モジュールロードコンテキストでは単引数形態（自動的に名前空間に属する）を優先する；跨モジュール/ツールコードの登録時には明示的にモジュール名を渡す
4. **ルーティンググループを使用する**：同一モジュールの複数のルーティングは `group()` で整理する
5. **セキュリティを考慮する**：機密操作には認証メカニズムとセキュリティヘッダーを実装する
6. **適切なレート制限を設定する**：高頻度のエンドポイントにはレート制限を設定する
7. **ライフサイクルフックを使用する**：`@ws.on_disconnect` / `@ws.on_error` を使用して WebSocket の例外を処理し、手動の try/catch を避ける

## 関連ドキュメント

- [ネットワーククライアント](client.md) - 内部リクエストクライアントを使用してリクエストを送信する
- [モジュール開発ガイド](../developer-guide/modules/getting-started.md) - モジュールルーティング登録の概要
- [ベストプラクティス](../developer-guide/modules/best-practices.md) - ルーティングの使用に関する推奨事項