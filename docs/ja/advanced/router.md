# ルーター管理

ErisPulse ルーター管理は統一的な HTTP および WebSocket ルーティングを提供し、マルチアダプタ対応のルート登録とライフサイクル管理をサポートしています。基盤には抽象化層（現在は FastAPI + Uvicorn）を介して実装されています。

## 概要

ルーター管理の主な機能：

- **デコレータールート**：`@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` デコレータによるクイック登録をサポート
- **自動注入**：ルートハンドラーは FastAPI 型のインポート不要、フレームワークが抽象オブジェクトを自動的に注入
- **ルートグループ化**：プレフィックスとバージョン番号付きの `RouteGroup` をサポート
- **ルートミドルウェア**：glob パターンマッチによるリクエスト遮断をサポート
- **レート制限**：スライディングウィンドウアルゴリズムによるレート制限を内蔵
- **CORS サポート**：ワンクリックでクロスオリジンリソースシェアリングを有効化
- **セキュリティヘッダー**：自動的にセキュリティ対応レスポンスヘッダーを追加
- **自動ドキュメント**：OpenAPI ベースの対話型ドキュメント
- **WebSocket サポート**：完全な WebSocket 接続管理、カスタム認証、ライフサイクルフック
- **ライフサイクル連携**：ErisPulse のライフサイクルシステムと深く連携
- **SSL/TLS サポート**：HTTPS および WSS のセキュア接続をサポート
- **ホームエントリ**：モジュールをルートルート `/` に登録してクイックアクセスボタンを提供、多言語対応

## 抽象型

ErisPulse はサーバーサイドの抽象型を提供し、モジュールが FastAPI に直接依存しないようにしています。

| 抽象型 | FastAPI 対応 | 説明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP リクエストラッパー、インターフェースは完全互換 |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket 接続ラッパー、追加でライフサイクルフックを提供 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket 切断例外 |

> `WebSocketConnection` は `WebSocketConnectionBase` を継承しており、クライアント WebSocket (`ClientWebSocket`) と同じ `send/receive/iter/close` インターフェースを共有します。クライアントとサーバーの WebSocket は同じビジネスロジックコードを使用できます。
>
> `.raw` プロパティから基盤の FastAPI ネイティブオブジェクトにアクセスできます。FastAPI 型を直接使用するコードも完全に互換性があります。

## デコレータールート（推奨）

### HTTP デコレータ

```python
from ErisPulse.Core import router
@router.get("my_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}

# 抽象型を明示的に注釈することも可能
from ErisPulse.Core import HttpRequest

@router.post("my_module", "/data")
async def post_data(request: HttpRequest):
    data = await request.json()
    return {"received": data}

@router.put("my_module", "/data/{item_id}")
async def update_data(request):
    return {"updated": True}

@router.delete("my_module", "/data/{item_id}")
async def delete_data(request):
    return {"deleted": True}
```

> **自動注入ルール**：ハンドラーの最初の引数名が `request` または `req` で、かつ FastAPI 型アノテーションがない場合、フレームワークは `HttpRequest` を自動的に注入します。引数がない、またはリクエスト以外の引数名を持つハンドラーは影響を受けません。

### WebSocket デコレータ

```python
from ErisPulse.Core import WebSocketConnection, WebSocketDisconnect

# 基本な WebSocket
@router.ws("my_module", "/ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# ライフサイクルフック付きの WebSocket
@router.ws("my_module", "/ws/chat")
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

@router.ws("my_module", "/secure_ws", auth_handler=ws_auth)
async def secure_ws_handler(ws):
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")
```

> **注意**：WebSocket ハンドラーと認証ハンドラーも自動注入をサポートします。パラメータアノテーションなしで `WebSocketConnection` を取得できます。`fastapi.WebSocket` をアノテートするとネイティブオブジェクトが渡されますが、抽象型の使用を推奨します。

## 伝統的な登録方式

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
    summary="データインターフェース",
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
| `handler` | ハンドラ関数 | - |
| `auth_handler` | 認証関数、`False` を返すと接続が自動的に閉じられます | `None` |
| `auto_accept` | `accept()` を自動的に行うかどうか | `True` |

> **推奨**：`auto_accept` を閉じるのではなく、`auth_handler` を使用して接続確認を行ってください。接続プロセスを完全に制御する必要がある場合のみ `auto_accept=False` を設定してください。

## WebSocket ライフサイクルフック

`WebSocketConnection` は接続切断およびエラーのコールバック登録を提供し、手動の try/catch は不要です：

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

## ルートグループ化

```python
# プレフィックス付きのルートグループ作成
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

ミドルウェアは glob パターンマッチでパスを照合します：

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

ルートに対してスライディングウィンドウアルゴリズムを使用してレート制限を行います：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

レート制限フォーマット：`{回数}/{時間枠}`、例：`10/minute`、`100/hour`。

## CORS 設定

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

`config.toml` から設定することも可能です：

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

`config.toml` から設定することも可能です：

```toml
[router.security]
enabled = true
```

## 自動ドキュメント

Router はデフォルトで OpenAPI 対話型ドキュメントを有効化します：

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

ルートパスはモジュール名をプレフィックスとして自動的に追加され、競合を回避します：

```python
# モジュール "my_module" へのパス "/api" を登録
# 実際のアクセスパスは "/my_module/api"
router.register_http_route("my_module", "/api", handler)
```

## システムルート

ルーター管理は以下のシステムルートを自動的に提供します。

### ヘルスチェック

```
GET /health
# 返り値:
{"status": "ok", "service": "ErisPulse Router"}
```

### ルートページ

```
GET /
# ErisPulse ブランドページを返す
```

ルートルート `/` には ErisPulse のブランドページが表示され、Dashboard の可用性を自動検出してエントリーボタンが追加されます。

## ホームエントリ

ルーター管理により、外部モジュールはルートルート `/` 上でクイックアクセスボタンを登録でき、ユーザーは各モジュールの管理ページに素早くアクセスできます。

### エントリ登録

```python
# 簡単な登録
router.register_home_entry(
    name="マイパネル",
    url="/mymodule/admin",
)

# アイコン付き登録（SVG）
router.register_home_entry(
    name="コンソール",
    url="/console",
    icon_svg='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>',
)

# 国際化対応の登録（プロジェクト i18n 辞書形式）
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "マイパネル"},
    url="/mymodule/admin",
)
```

**パラメータ説明：**

| パラメータ | 型 | 説明 | 必須 |
|------|------|------|------|
| `name` | `str` / `dict` | ボタン表示テキスト；`{"i18n": "key", "default": "テキスト"}` 辞書を渡した場合は国際化を使用 | はい |
| `url` | `str` | ボタンリンク先アドレス | はい |
| `icon_svg` | `str` | オプション SVG アイコンマーク | いいえ |

### Dashboard 自動登録

`sdk.Dashboard` が利用可能な場合、ルーター管理は自動的にエントリリストの先頭に Dashboard ボタンを追加し、手動登録は不要です。

## ライフサイクル連携

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"サーバー起動: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("サーバー停止中...")
```

## ベストプラクティス

1. **抽象型を優先使用**：`HttpRequest` / `WebSocketConnection` を使用して `fastapi.Request` / `fastapi.WebSocket` を置き換え、ハード依存を避ける
2. **自動注入を活用**：ハンドラーの最初の引数名を `request` または `req` とし、型アノテーションなしで `HttpRequest` を取得
3. `module_name` を明示的に渡す：デコレータの最初の引数はモジュール名である必要があり、省略できません
4. **ルートグループ化を使用**：同じモジュールの複数のルートを `group()` で整理する
5. **セキュリティの考慮**：機密な操作には認証機能とセキュリティヘッダーを実装する
6. **適切なレート制限**：高頻度のインターフェースにはレート制限を設定する
7. **ライフサイクルフックを使用**：`@ws.on_disconnect` / `@ws.on_error` を使用して WebSocket 例外を処理し、手動の try/catch を避ける

## 関連ドキュメント

- [HTTP クライアント](http-client.md) - 組み込み HTTP クライアントを使用してリクエストを送信
- [モジュール開発ガイド](../developer-guide/modules/getting-started.md) - モジュールのルート登録について理解する
- [ベストプラクティス](../developer-guide/modules/best-practices.md) - ルート使用に関するアドバイス