# ルーティングマネージャー

> [!TIP]
> **このドキュメントを読むべきケース**：HTTP / WebSocket / SSE ルーティング（接続プールのブロードキャストを含む）が必要な場合。不要であればスキップしても、他の機能の利用には影響しません。


ErisPulse ルーティングマネージャーは、統一された HTTP および WebSocket ルーティング管理を提供し、複数アダプターのルート登録とライフサイクル管理をサポートします。内部は抽象化レイヤーでラップされています（現在は FastAPI + Uvicorn）

## 概要

ルーティングマネージャーの主な機能：

- **デコレータルーティング**：`@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` デコレータによる手軽な登録をサポート
- **自動注入**：ルートハンドラーは FastAPI の型をインポートする必要がなく、フレームワークが抽象オブジェクトを自動的に注入します
- **ルートグループ**：プレフィックスやバージョン番号付きの `RouteGroup` をサポート
- **ルートミドルウェア**：glob パターンマッチングによるリクエストインターセプトをサポート
- **レート制限**：スライディングウィンドウ方式のレート制限を内蔵
- **CORS サポート**：クロスオリジンリソース共有をワンクリックで有効化
- **セキュリティヘッダー**：セキュリティレスポンスヘッダーを自動追加
- **自動ドキュメント**：OpenAPI ベースのインタラクティブドキュメント
- **WebSocket サポート**：完全な WebSocket 接続管理、カスタム認証、ライフサイクルフック
- **ライフサイクル統合**：ErisPulse ライフサイクルシステムとの深い統合
- **SSL/TLS サポート**：HTTPS および WSS の安全な接続をサポート
- **ホームエントリー**：モジュールがルートパス `/` にクイックアクセスボタンを登録でき、国際化に対応

## 抽象型

ErisPulse はサーバーサイドの抽象型を提供し、モジュールが FastAPI に直接依存する必要をなくします：

| 抽象型 | FastAPI 対応 | 説明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP リクエストのラッパー。インターフェースは完全互換 |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket 接続のラッパー。ライフサイクルフックを追加提供 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket 切断例外 |

> `WebSocketConnection` は `WebSocketConnectionBase` を継承しており、クライアント WebSocket（`ClientWebSocket`）と同じ send/receive/iter/close インターフェースを共有します。クライアントとサーバーサイドの WebSocket で、同じビジネスロジックコードを使用できます。
>
> `.raw` プロパティから、基盤の FastAPI ネイティブオブジェクトにアクセスできます。FastAPI の型を直接使用するコードも完全に互換です。

## デコレータルーティング（推奨）

### 登録形式：単一引数（推奨）と二引数

デコレータルーティングには 2 つの形式があり、**単一引数を推奨**します。コマンド / イベントトリガーと同様に、名前空間は現在のモジュールに自動的に帰属します：

```python
from ErisPulse import router

# 単一引数（推奨）：モジュール名/hello に自動帰属 → 実際のパスは /my_module/hello
@router.get("/hello")
async def hello():
    return {"ok": True}

# 単一引数 WebSocket：@ws("chat") → /my_module/chat
@router.ws("chat")
async def chat(ws):
    ...

# 二引数：モジュール名を明示的に指定（ルールは同じ。モジュールをまたぐコードやツールコードからの登録時に使用）
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> 単一引数形式は、モジュール / アダプターの**読み込みコンテキスト**内での登録が必要です（読み込み時にフレームワークが帰属を注入済み）。
> 帰属のないコンテキストで呼び出すと `ValueError` が発生し、モジュール名を明示的に渡すよう促されます。

### HTTP デコレータ

```python
from ErisPulse import router, HttpRequest

# 抽象型を明示的にアノテートすることも可能
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

> **自動注入ルール**：ハンドラーの最初の引数名が `request` または `req` で、FastAPI の型アノテーションがない場合、フレームワークが `HttpRequest` を自動的に注入します。引数がないハンドラーや、リクエスト以外の引数名を持つハンドラーには影響しません。

#### レスポンス返却の規約（2.10+）

ハンドラーの戻り値は**タプル規約**をサポートします（推奨の書き方で、ステータスコードを明確に制御できます）。dict/str/Response は従来どおりです：

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "トークンが無効です"}, 401
    # (body, status_code, headers) ではレスポンスヘッダーも付加できます
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# または respond() ヘルパー関数を使用（message は自動的にレスポンスボディにマージされます）
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

パス / クエリパラメータは FastAPI のネイティブアノテーションをそのまま使用できます（`item_id: int`、`page: int = 1` など）。
ミドルウェアについては[ルートミドルウェア](#ルートミドルウェア)のセクションを参照してください。

### WebSocket デコレータ

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# 基本 WebSocket（単一引数形式）
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

# 認証付き WebSocket（トークンは環境変数から読み込み、コードにハードコードしないこと）
import os

async def ws_auth(ws: WebSocketConnection) -> bool:
    token = ws.query_params.get("token")
    expected = os.environ.get("ERISPULSE_WS_TOKEN", "")
    return bool(expected) and token == expected

@router.ws("secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocket ハンドラーと認証ハンドラーも自動注入をサポートします。引数にアノテーションがなくても `WebSocketConnection` を取得できます。`fastapi.WebSocket` をアノテートすればネイティブオブジェクトも渡せますが、抽象型の使用を推奨します。

### 接続の自動登録（接続プール、2.10+）

`@ws` / `@sse` で確立された接続は、**デフォルトで自動的に**フレームワークの接続プールに登録されます（`track=False` で無効化可能）。
ハンドラー内では `ws.id` / `ws.join_group(...)` が利用でき、任意のモジュールは
`connections.list(namespace=...)` で自身のモジュールの接続を確認したり、グループにブロードキャストできます。
詳細は[接続プールとブロードキャスト](connections.md)を参照してください。

## 従来の登録方式

```python
async def hello_handler(request):
    return {"message": "Hello World"}

# 基本登録
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
    summary="データ API",
    tags=["API"],
)
```

### WebSocket 登録

```python
from ErisPulse.Core import WebSocketConnection

async def websocket_handler(ws: WebSocketConnection):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# 基本登録
router.register_websocket(
    module_name="my_module",
    path="/ws",
    handler=websocket_handler,
)

# 認証付き登録（推奨）
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

**パラメータ説明：**

| パラメータ | 説明 | デフォルト値 |
|------|------|--------|
| `module_name` | モジュール名（必須） | - |
| `path` | WebSocket パス | - |
| `handler` | ハンドラー関数 | - |
| `auth_handler` | 認証関数。`False` を返すと自動的に接続を閉じます | `None` |
| `auto_accept` | 自動的に `accept()` するかどうか | `True` |

> **推奨**：`auto_accept` を無効にする代わりに、`auth_handler` で接続の確認を行ってください。接続フローを完全に制御する必要がある場合にのみ `auto_accept=False` を設定してください。

## WebSocket ライフサイクルフック

`WebSocketConnection` は切断とエラーのコールバック登録を提供するため、手動の try/catch は不要です：

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # デコレータ方式で登録
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"切断理由: {reason}")

    # 直接呼び出すことも可能
    async def on_err(ws, error=""):
        print(f"エラー: {error}")
    ws.on_error(on_err)

    # 通常のビジネスロジック
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")
```

## ルートグループ

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

## ルートミドルウェア

ミドルウェアは glob パターンマッチングによるパス指定をサポートします：

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

2.7.0 以降、すべての HTTP リクエストには、ログ / トレーシングを紐付けるための `X-Request-ID` 関連 ID が付与されます：

- **生成ルール**：クライアントが渡した `X-Request-ID` リクエストヘッダーを優先して使用します（分散トレーシングのシナリオ）。それ以外は UUID を自動生成
- **レスポンスヘッダー**：レスポンスには `X-Request-ID` が書き戻され、クライアントがリクエストとログを対応付けやすくなります
- **ライフサイクルイベント**：`server.request` と `server.response` イベントのデータに `request_id` フィールドが追加されました

```python
# モジュール内でリクエストイベントをリッスンし、request_id でリクエストとレスポンスを紐付ける
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

クライアントは、サービス間トレーシングのために ID をカスタマイズできます：

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## レート制限

スライディングウィンドウアルゴリズムでルートのレート制限を行います：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

レート制限の形式：`{回数}/{時間ウィンドウ}`。例：`10/minute`、`100/hour`。

## CORS 設定

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

`config.toml` による設定も可能です：

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

`config.toml` による設定も可能です：

```toml
[router.security]
enabled = true
```

## 自動ドキュメント

Router はデフォルトで OpenAPI インタラクティブドキュメントを有効にしています：

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

ルートパスには、競合を避けるためにモジュール名が自動的にプレフィックスとして付加されます：

```python
# パス "/api" をモジュール "my_module" に登録
# 実際のアクセスパスは "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

> [!WARNING]
> ルートパス（モジュール名プレフィックスを含む）は**大文字小文字を区別**します。登録時のモジュール名の大文字小文字が、そのまま実際のパスに反映されます。モジュール名が `Test` の場合に `/api` を登録すると実際のパスは `/Test/api` となり、`/test/api` にアクセスすると 404 が返されます。

## システムルート

ルーティングマネージャーは、以下のシステムルートを自動的に提供します：

### ヘルスチェック

```
GET /health
# レスポンス:
{"status": "ok", "service": "ErisPulse Router"}
```

### ルートページ

```
GET /
# ErisPulse ブランドページを返します
```

ルートパス `/` には ErisPulse ブランドページが表示され、Dashboard の可用性を自動検出してエントリーボタンを追加します。

## ホームエントリー

ルーティングマネージャーは、外部モジュールがルートパス `/` にクイックアクセスボタンを登録できるようにし、ユーザーが各モジュールの管理ページへ素早くアクセスできるようにします。

### エントリーの登録

```python
# シンプルな登録
router.register_home_entry(
    name="マイパネル",
    url="/mymodule/admin",
)

# アイコン付きの登録（SVG）
router.register_home_entry(
    name="コンソール",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# 国際化対応の登録（プロジェクトの i18n 辞書形式）
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "マイパネル"},
    url="/mymodule/admin",
)
```

**パラメータ説明：**

| パラメータ | 型 | 説明 | 必須 |
|------|------|------|------|
| `name` | `str` / `dict` | ボタンの表示テキスト。`{"i18n": "key", "default": "テキスト"}` の辞書を渡すと国際化を使用 | はい |
| `url` | `str` | ボタンのリンク先 URL | はい |
| `icon_svg` | `str` | 任意の SVG アイコンマークアップ | いいえ |

### Dashboard 自動登録

`sdk.Dashboard` が利用可能と検出されると、ルーティングマネージャーはエントリーリストの先頭に Dashboard ボタンを自動的に追加します。手動での登録は不要です。

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

1. **抽象型を優先して使用**：`fastapi.Request` / `fastapi.WebSocket` の代わりに `HttpRequest` / `WebSocketConnection` を使用し、ハードな依存を避けます
2. **自動注入を活用**：ハンドラーの最初の引数を `request` または `req` と命名すれば、型アノテーションなしで `HttpRequest` を取得できます
3. **単一引数形式を優先**：モジュール読み込みコンテキストでは単一引数形式を優先します（名前空間に自動帰属）。モジュールをまたぐコードやツールコードからの登録時は、モジュール名を明示的に渡します
4. **ルートグループの使用**：同一モジュールの複数ルートは `group()` で整理します
5. **セキュリティへの配慮**：機密性の高い操作には認証機構とセキュリティヘッダーを実装します
6. **適切なレート制限**：高頻度でアクセスされる API にはレート制限を設定します
7. **ライフサイクルフックの使用**：`@ws.on_disconnect` / `@ws.on_error` で WebSocket の例外を処理し、手動の try/catch を避けます

## 関連ドキュメント

- [ネットワーククライアント](client.md) - 内蔵のリクエストクライアントでリクエストを送信
- [モジュール開発ガイド](../developer-guide/modules/getting-started.md) - モジュールのルート登録について学ぶ
- [ベストプラクティス](../developer-guide/modules/best-practices.md) - ルーティングの使用に関する推奨事項