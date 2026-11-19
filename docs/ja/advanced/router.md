# ルーティングマネージャー

> [!TIP]
> **この記事を読むタイミング**：HTTP / WebSocket / SSE ルーティング（接続プールによるブロードキャストを含む）が必要な場合。不要な場合はスキップしても、他の機能の使用に影響はありません。


ErisPulse ルーティングマネージャーは、HTTP および WebSocket ルーティングを一元的に管理し、複数アダプタのルーティング登録とライフサイクル管理をサポートします。内部では抽象層を介してラップされており、現在は FastAPI + Uvicorn が使用されています。

## 概要

ルーティングマネージャーの主な機能：

- **デコレータによるルーティング**：`@http` / `@get` / `@post` / `@put` / `@delete` / `@ws` デコレータによる高速登録
- **自動注入**：ルーティングハンドラは FastAPI クラスをインポートする必要がなく、フレームワークが自動的に抽象オブジェクトを注入
- **ルーティンググループ**：プレフィックスとバージョン番号付きの `RouteGroup` をサポート
- **ルーティングミドルウェア**：glob パターンマッチングによるリクエストのインターセプト
- **リクエスト制限**：スライディングウィンドウによる制限
- **CORS サポート**：ワンクリックで CORS を有効化
- **セキュリティヘッダー**：自動的にセキュリティレスポンスヘッダーを追加
- **自動ドキュメント**：OpenAPI に基づくインタラクティブなドキュメント
- **WebSocket サポート**：WebSocket 接続の完全な管理、カスタム認証およびライフサイクルフック
- **ライフサイクル統合**：ErisPulse ライフサイクルシステムとの深層統合
- **SSL/TLS サポート**：HTTPS および WSS セキュア接続をサポート
- **ホームエントリ**：モジュールをルートルーティング `/` に登録し、国際化をサポートするショートカットボタン

## 抽象型

ErisPulse はサーバーサイドの抽象型を提供し、モジュールが FastAPI に直接依存しないようにします。

| 抽象型 | FastAPI に対応 | 説明 |
|---------|-------------|------|
| `HttpRequest` | `fastapi.Request` | HTTP リクエストのラッパー、インターフェースは完全に互換性があります |
| `WebSocketConnection` | `fastapi.WebSocket` | WebSocket 接続のラッパー、ライフサイクルフックを追加 |
| `WebSocketDisconnect` | `fastapi.WebSocketDisconnect` | WebSocket 接続切断の例外 |

> `WebSocketConnection` は `WebSocketConnectionBase` を継承し、クライアント側の WebSocket (`ClientWebSocket`) と同じ send/receive/iter/close インターフェースを共有します。クライアントとサーバー側の WebSocket は同じビジネスロジックコードを使用できます。
>
> `.raw` 属性を使用して、下層の FastAPI ネイティブオブジェクトにアクセスできます。FastAPI クラスを使用するコードも完全に互換性があります。

## デコレータによるルーティング（推奨）

### 登録形態：単引数（推奨）と二引数

デコレータによるルーティングは二つの形態をサポートし、**単引数を推奨**します。これはコマンド/イベントトリガーと一致し、名前空間は自動的に現在のモジュールに属します。

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

# 二引数：明示的にモジュール名を指定（ルールは変更なし、モジュール間/ツールコードの登録時に使用）
@router.get("other_module", "/info")
async def get_info(request):
    return {"method": request.method, "path": str(request.url)}
```

> [!NOTE]
> 単引数の形態は、モジュール/アダプタの**ロードコンテキスト**内で登録する必要があります（ロード時にフレームワークが自動的に属するモジュールを注入）。
> 属するコンテキストがない場所で呼び出すと、`ValueError` が発生し、明示的にモジュール名を渡すように通知されます。

### HTTP デコレータ

```python
from ErisPulse import router, HttpRequest

# 抽象型を明示的に注釈することもできます
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

> **自動注入ルール**：ハンドラの最初の引数が `request` または `req` であり、FastAPI の型注釈がない場合、フレームワークは自動的に `HttpRequest` を注入します。引数がない場合やリクエスト引数名でない場合は影響を受けません。

#### レスポンス返却の約束（2.10+）

ハンドラの返り値は**タプルの約束**（推奨の書き方、明確にステータスコードを制御）をサポートし、dict/str/Response は従来通りです。

```python
@router.post("/login")
async def login(request):
    if not check_token(request):
        # (body, status_code) → 401 JSON
        return {"error": "unauthorized", "message": "token が無効です"}, 401
    # (body, status_code, headers) さらにレスポンスヘッダーも追加できます
    return {"user_id": 1}, 200, {"X-Request-Cost": "12ms"}

# または respond() ヘルパー関数を使用（message はレスポンス本体に自動的にマージされます）
from ErisPulse import respond

@router.get("/me")
async def me():
    return respond({"user_id": 1}, status_code=200, message="ok")
```

パス/クエリパラメータは FastAPI のネイティブ注釈を使用できます（`item_id: int`、`page: int = 1`）。
ミドルウェアは[ルーティングミドルウェア](#ルーティングミドルウェア)のセクションを参照してください。

### WebSocket デコレータ

```python
from ErisPulse import WebSocketConnection, WebSocketDisconnect

# 基本的な WebSocket（単引数の形態）
@router.ws("ws")
async def websocket_handler(ws):
    async for msg in ws.iter_text():
        await ws.send_text(f"Echo: {msg}")

# ライフサイクルフックを含む WebSocket
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

# 認証付きの WebSocket（トークンは環境変数から読み込み、コード内にハードコードしないでください）
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

> **注意**：WebSocket ハンドラと認証ハンドラも自動注入がサポートされます。`WebSocketConnection` を取得するには、パラメータの注釈を必要としません。`fastapi.WebSocket` を注釈することも可能です。ただし、抽象型を使用することを推奨します。

### 接続の自動登録（接続プール、2.10+）

`@ws` / `@sse` で確立された接続は**デフォルトでフレームワークの接続プールに自動登録**されます（`track=False` で無効化）：
ハンドラ内では `ws.id` / `ws.join_group(...)` が使用でき、任意のモジュールで
`connections.list(namespace=...)` を使用して本モジュールの接続を確認し、グループにブロードキャストできます。
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

# 限流とドキュメント情報付き
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
| `auth_handler` | 認証関数、`False` を返すと接続が自動的に切断されます | `None` |
| `auto_accept` | 自動的に `accept()` するかどうか | `True` |

> **推奨**：`auth_handler` を使用して接続を確認するよう推奨します。`auto_accept` を `False` に設定するのは、接続フローを完全に制御する必要がある場合にのみ行います。

## WebSocket ライフサイクルフック

`WebSocketConnection` は切断とエラーのコールバックを提供し、手動の try/catch が不要です。

```python
from ErisPulse.Core import WebSocketConnection

@router.ws("my_module", "/ws")
async def my_ws(ws: WebSocketConnection):
    # デコレータ方式で登録
    @ws.on_disconnect
    async def on_close(ws, reason="unknown"):
        print(f"切断理由: {reason}")

    # 直接呼び出すこともできます
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

ミドルウェアは glob パターンでパスをマッチングできます：

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

2.7.0 から、各 HTTP リクエストには `X-Request-ID` という関連 ID が付与され、ログ / リレーショナルトレースの連携に使用されます：

- **生成ルール**：クライアントが送信した `X-Request-ID` リクエストヘッダーを優先して使用（分散トレースの場面）。なければ、UUID を生成
- **レスポンスヘッダー**：レスポンスには `X-Request-ID` を返し、クライアントがリクエストとログを対応させるのに便利
- **ライフサイクルイベント**：`server.request` と `server.response` イベントのデータに `request_id` フィールドが追加

```python
# モジュールでリクエストイベントを監視し、request_id でリクエスト-レスポンスを連携
@sdk.lifecycle.on("server.request")
async def on_request(data):
    print(f"[{data['request_id']}] {data['method']} {data['path']}")

@sdk.lifecycle.on("server.response")
async def on_response(data):
    print(f"[{data['request_id']}] -> {data['status_code']}")
```

クライアントはトレースを跨いで ID をカスタマイズできます：

```bash
curl -H "X-Request-ID: my-trace-id" http://localhost:8080/my_module/health
```

## リクエスト制限

ルーティングに対してスライディングウィンドウアルゴリズムを使用してリクエスト制限を行います：

```python
@router.get("my_module", "/limited", rate_limit="10/minute")
async def limited_endpoint(request):
    return {"ok": True}

@router.post("my_module", "/submit", rate_limit="5/minute")
async def submit_data(request):
    return {"submitted": True}
```

リクエスト制限の形式：`{回数}/{時間ウィンドウ}`、例えば `10/minute`、`100/hour`。

## CORS 設定

```python
router.setup_cors(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

`config.toml` で設定することもできます：

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

`config.toml` で設定することもできます：

```toml
[router.security]
enabled = true
```

## 自動ドキュメント

Router はデフォルトで OpenAPI によるインタラクティブなドキュメントを有効にします：

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
> ルーティングパス（モジュール名のプレフィックスを含む）は**大文字小文字を区別**します。登録時のモジュール名が大文字小文字で、実際のパスもその通りです：モジュール名が `Test` の場合、`/api` を登録した実際のパスは `/Test/api` となり、`/test/api` にアクセスすると 404 が返されます。

## システムルーティング

ルーティングマネージャーは以下のシステムルーティングを自動的に提供します：

### ヘルスチェック

```
GET /health
# 返り値:
{"status": "ok", "service": "ErisPulse Router"}
```

### ホームページ

```
GET /
# ErisPulse ブランドページを返す
```

ルートルーティング `/` は ErisPulse ブランドページを表示し、ダッシュボードの可用性を自動検出し、エントリーボタンを追加します。

## ホームエントリ

ルーティングマネージャーは外部モジュールがルートルーティング `/` にショートカットエントリーボタンを登録できるようにし、ユーザーがモジュールの管理ページにすばやくアクセスできるようにします。

### エントリーの登録

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

# 国際化をサポートする登録（i18n ディクショナリ形式）
router.register_home_entry(
    name={"i18n": "mymodule.home.entry", "default": "私のパネル"},
    url="/mymodule/admin",
)
```

**パラメータの説明：**

| パラメータ | 型 | 説明 | 必須 |
|------|------|------|------|
| `name` | `str` / `dict` | ボタンの表示テキスト；`{"i18n": "key", "default": "テキスト"}` ディクショナリを渡すと国際化を使用 | はい |
| `url` | `str` | ボタンのリンク先 | はい |
| `icon_svg` | `str` | オプションの SVG イコン | いいえ |

### ダッシュボードの自動登録

`sdk.Dashboard` が利用可能であることが検出された場合、ルーティングマネージャーはダッシュボードボタンを自動的にエントリーリストの先頭に追加します。手動で登録する必要はありません。

## ライフサイクルの統合

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("server.start")
async def on_server_start(event):
    print(f"サーバーが起動しました: {event['data']['base_url']}")

@lifecycle.on("server.stop")
async def on_server_stop(event):
    print("サーバーが停止中です...")
```

## リクエストオブジェクトの高度なプロパティ

`HttpRequest` は `method` / `query` / `headers` / `json` / `body` の基本的な面に加え、
認証ミドルウェア、切断感知の長時間タスクなどでよく使用される高機能を透過します：

| プロパティ / メソッド | 説明 |
|-------------|------|
| `request.session` | セッション dict（セッションミドルウェアが必要）、リクエスト間で保持 |
| `request.auth` | 認証情報（認証ミドルウェアが書き込む） |
| `request.user` | 現在のユーザーオブジェクト（認証ミドルウェアが書き込む） |
| `request.url_for(name, **params)` | リバースルーティング：ルーティング名から URL を生成 |
| `await request.is_disconnected()` | クライアントが切断されたかどうか（SSE / 長時間タスクのループ終了に使用） |
| `request.raw` | 下層の Starlette リクエストオブジェクト（緊急対応、下節の互換性説明参照） |

## 緊急対応：router.app

`router.app` は下層の FastAPI アプリケーションインスタンスを直接公開します（遅延作成、最初のアクセス時に web スタックをロードし、コアルーティングを登録）。デコレータで表現できない状況をカバーします—サブアプリのマウント、グローバルミドルウェア、FastAPI エコシステムへの接続（StaticFiles / バックグラウンドタスクテンプレートなど）：

```python
from ErisPulse.Core import router
from starlette.staticfiles import StaticFiles

app = router.app
app.mount("/static", StaticFiles(directory="static"), name="static")
```

> [!WARNING]
> **互換性の境界**：`router.app` は緊急対応手段であり、安定した契約ではありません—取得するのは現在の web スタック（FastAPI/Starlette）のインスタンスです。フレームワークが将来的に下層の web 実装を移行した場合、`app` 内部構造（ミドルウェアの順序、Starlette 特定の API）に依存するコードは**破壊的変更**に遭遇します。優先的に `@router.http` / `HttpRequest` 抽象層（`request.raw` も同様）を使用し、`.app` の使用をモジュールの独立したアダプタ層に限定してください—移行時に 1 か所だけを変更すれば済みます。

## 最適実践

1. **優先的に抽象型を使用**：`fastapi.Request` / `fastapi.WebSocket` に依存しないように、`HttpRequest` / `WebSocketConnection` を使用
2. **自動注入を活用**：ハンドラの最初の引数を `request` または `req` とし、型注釈なしでも `HttpRequest` を取得できるように
3. **単引数形態を優先**：モジュールのロードコンテキストでは優先的に単引数形態（自動的に名前空間に属する）を使用；モジュール間/ツールコードの登録時は明示的にモジュール名を渡す
4. **ルーティンググループの使用**：同一モジュールの複数のルーティングは `group()` で整理
5. **セキュリティを考慮**：セキュアな操作には認証メカニズムとセキュリティヘッダーを実装
6. **適切なリクエスト制限**：高頻度のエンドポイントにはリクエスト制限を設定
7. **ライフサイクルフックの使用**：`@ws.on_disconnect` / `@ws.on_error` を使って WebSocket のエラーを処理し、手動の try/catch を避ける
8. **緊急対応の使用を限定**：`router.app` / `request.raw` は抽象層で表現できない場合にのみ使用し、依存を 1 箇所に限定し、フレームワークの下層移行時の適応範囲を最小限に抑える

## 関連ドキュメント

- [ネットワーククライアント](client.md) - 内部リクエストクライアントを使用してリクエストを送信
- [モジュール開発ガイド](../developer-guide/modules/getting-started.md) - モジュールルーティング登録の理解
- [最適実践](../developer-guide/modules/best-practices.md) - ルーティング使用の推奨事項