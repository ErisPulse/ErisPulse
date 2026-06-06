# HTTP クライアント

ErisPulse は統一された HTTP/WS クライアントを提供します。モジュールやアダプターは、サードパーティ製ライブラリである `aiohttp` や `httpx` を独自にインポートするのではなく、このクライアントを優先的に使用して HTTP リクエストを送信し、WebSocket 接続を確立する必要があります。

## 概要

HTTP/WS クライアントの主な機能：

- **統一インターフェース**：`get` / `post` / `put` / `delete` / `patch` / `request` メソッドを提供
- **WebSocket クライアント**：`ws_connect` を使用してクライアント WebSocket 接続を確立
- **自動ログ**：すべてのリクエストのログと統計情報を自動的に記録
- **ライフサイクル統合**：各リクエストで `client.request` ライフサイクルイベントをトリガー、WS 接続で `client.ws.connect` イベントをトリガー
- **リトライサポート**：自動リトライの回数と間隔を設定可能
- **タイムアウト制御**：接続タイムアウトとリクエストタイムアウトを個別に設定
- **コネクションプールの再利用**：aiohttp.ClientSession に基づくコネクションプール管理
- **例外体系**：aiohttp 例外が自動的に ErisPulse 例外 (ClientError 体系) に変換されます

## クイックスタート

### HTTP リクエスト

```python
from ErisPulse.Core import client

# GET リクエスト
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST リクエスト
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

### WebSocket 接続

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

## HttpResponse

すべてのリクエストメソッドは `HttpResponse` オブジェクトを返します：

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP ステータスコード (例: 200, 404)
resp.reason       # str | None - ステータスの説明 (例: "OK")
resp.headers      # レスポンスヘッダー (大文字小文字を区別しない)
resp.content_type # str | None - Content-Type
resp.url          # 最終 URL (リダイレクトにより変更される可能性あり)
resp.raw          # 基盤となるネイティブレスポンスオブジェクト (現在は aiohttp.ClientResponse)

# レスポンスボディの読み取り
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # JSON の解析
text = await resp.text("gbk")  # エンコーディングの指定
```

## リクエストメソッド

### GET

```python
from ErisPulse.Core import client

resp = await client.get(
    "https://api.example.com/users",
    params={"page": "1", "limit": "10"},
    headers={"Authorization": "Bearer token"},
)
```

### POST

```python
from ErisPulse.Core import client

# JSON リクエストボディ
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# フォームリクエストボディ
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# 生データ
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)
```

### PUT / DELETE / PATCH

```python
from ErisPulse.Core import client

resp = await client.put("https://api.example.com/users/1", json={"name": "Bob"})
resp = await client.delete("https://api.example.com/users/1")
resp = await client.patch("https://api.example.com/users/1", json={"age": 31})
```

### 汎用 request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## パラメーターの説明

### HTTP リクエストパラメーター

| パラメーター | 型 | 説明 |
|------|------|------|
| `url` | `str` | リクエスト URL |
| `params` | `dict[str, str]` | クエリパラメーター (任意) |
| `headers` | `dict[str, str]` | 追加のリクエストヘッダー (任意) |
| `data` | `Any` | リクエストボディ (フォームまたは生データ) (任意) |
| `json` | `Any` | JSON リクエストボディ (任意) |
| `timeout` | `float` | 今回のリクエストタイムアウト (秒) (任意, デフォルト値を上書き) |
| `max_retries` | `int` | 今回の最大リトライ回数 (任意, デフォルト値を上書き) |

### ws_connect パラメーター

| パラメーター | 型 | 説明 |
|------|------|------|
| `url` | `str` | WebSocket サーバー URL |
| `headers` | `dict[str, str]` | 追加のリクエストヘッダー (任意) |
| `heartbeat` | `float` | ハートビート間隔 (秒) (任意) |

## タイムアウトとリトライ

```python
from ErisPulse.Core import HttpClient

# カスタムタイムアウト付きのクライアントを作成
client = HttpClient(
    timeout=60,           # リクエスト総合タイムアウト 60s
    connect_timeout=5,    # 接続タイムアウト 5s
    max_retries=3,        # 失敗時に自動リトライ 3 回
    retry_delay=2,        # リトライ間隔 2s
)

# 単一リクエストでタイムアウトを上書き
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

## カスタムデフォルトヘッダー

```python
client = HttpClient(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## リクエスト統計

```python
from ErisPulse.Core import client

# 統計の確認
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# 統計のリセット
client.reset_stats()
```

## ライフサイクルイベント

### HTTP リクエストイベント

各リクエストの完了後に `client.request` イベントがトリガーされ、監視に使用できます。

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### WebSocket 接続イベント

各 WebSocket 接続の確立後に `client.ws.connect` イベントがトリガーされます。

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS 接続: {event_data['url']}")
```

## コンテキスト管理

```python
# コンテキストマネージャーとして使用し、セッションを自動的に閉じる
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## WebSocket クライアント

`client.ws_connect()` を使用して WebSocket クライアント接続を確立し、`ClientWebSocket` オブジェクトを返します。クライアントとサーバーの WebSocket は同じ `WebSocketConnectionBase` 基クラスを共有し、send/receive/iter インターフェースは完全に一致しています。

### 基本用法

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### メッセージの受信

#### 高度なメソッド (推奨)

メッセージタイプを自動的にフィルタリングし、切断時に `WebSocketDisconnect` をスローします：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# 1件ずつ受信
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# 反復して受信 (切断時に自動停止)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### 低レベルメソッド

`receive()` と `iter_messages()` を使用して生のメッセージタイプを処理し、TEXT / BINARY / CLOSE / ERROR を区別できます：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# 1件ずつ生のメッセージを受信
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# 生のメッセージを反復 (CLOSE/ERROR 時に自動停止)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"テキスト: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"バイナリ: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` は統一された WebSocket メッセージタイプで、基盤となるライブラリに依存しません：

| 属性 | 型 | 説明 |
|------|------|------|
| `type` | `str` | メッセージタイプ: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | メッセージデータ |

### ClientWebSocket 属性

| 属性 | 型 | 説明 |
|------|------|------|
| `url` | `URL` | 接続 URL |
| `headers` | `Headers` | レスポンスヘッダー |
| `closed` | `bool` | 接続が既に閉じられているかどうか |
| `raw` | `object` | 基盤となるネイティブオブジェクト (aiohttp.ClientWebSocketResponse) |

### ライフサイクルフック

`サーバー側 WebSocketConnection` と一致し、`on_disconnect` および `on_error` コールバックをサポートします：

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"接続切断: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"接続エラー: {error}")
```

### 接続の閉じ方

```python
await ws.close(code=1000, reason="Normal closure")
```

## 例外体系

ErisPulse は統一された例外階層を定義し、`sdk.client` を介して発行されたリクエストは、基盤となる aiohttp 例外を自動的に ErisPulse 例外に変換します。

> **後方互換性**：`aiohttp.ClientSession` を直接使用する古いモジュール/アダプターは完全に影響を受けません。例外変換は `sdk.client` を介してリクエストが発行された場合にのみ有効です。aiohttp を直接使用するコードは依然として `aiohttp.ClientError` などのネイティブ例外をキャッチします。2つの方法は共存可能です。

### 例外階層

```
ErisPulseError
├── ClientError                  # すべての HTTP/WS クライアントリクエスト例外の基底クラス
│   ├── ClientConnectionError    # 接続失敗 (DNS 解析失敗、接続拒否、ネットワーク不可達)
│   ├── ClientTimeoutError       # 接続タイムアウトまたはリクエストタイムアウト
│   └── HTTPStatusError          # HTTP 4xx/5xx ステータスコードエラー
└── WebSocketError               # WebSocket 例外基底クラス
    └── WebSocketDisconnect      # WebSocket 接続切断 (クライアントとサーバー共通)
```

### 例外のキャッチ

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import (
    ClientError,
    ClientConnectionError,
    ClientTimeoutError,
    HTTPStatusError,
    WebSocketDisconnect,
    WebSocketError,
)

# HTTP リクエスト例外処理
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("サーバーに接続できません")
except ClientTimeoutError:
    print("リクエストがタイムアウトしました")
except ClientError as e:
    print(f"リクエスト失敗: {e}")

# WebSocket 例外処理
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"接続切断: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocket エラー: {e}")
```

### 統一的なキャッチ

`ClientError` を使用してすべての HTTP/WS クライアントリクエスト例外を統一的にキャッチします：

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"クライアントエラー: {e}")
```

### HTTPStatusError

リクエスト後にステータスコードを確認し、例外をスローする必要がある場合、手動で使用できます：

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())
```

## アダプターでの使用

アダプターは、グローバルクライアントを使用するか、独自にクライアントインスタンスを作成してプラットフォーム API リクエストを送信できます。

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.errors import ClientError

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        try:
            resp = await client.post(
                f"https://api.platform.com/{endpoint}",
                json=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return await resp.json()
        except ClientError as e:
            self.logger.error(f"API コール失敗: {e}")
            raise
```

> `from ErisPulse import sdk` から `sdk.client` を使用することもでき、効果は同じです。

## ベストプラクティス

1. **グローバルクライアントを優先的に使用**：`from ErisPulse.Core import client` を使用してグローバルシングルトンを取得し、フレームワークによる統一管理と監視を容易にします。
2. **aiohttp の直接インポートを避ける**：`aiohttp.ClientSession` の代わりに `client` を使用することで、将来的に基盤の実装を変更する際にコードを修正する必要がなくなります。
3. **ErisPulse 例外体系の使用**：`sdk.client` を介してリクエストする場合、`aiohttp.ClientError` ではなく `ClientError` をキャッチし、コードが特定の HTTP ライブラリに依存しないようにします。aiohttp を直接使用する古いコードは影響を受けません。
4. **適切なタイムアウトの設定**：API の応答速度に応じて適切なタイムアウト時間を設定し、長時間のブロッキングを回避します。
5. **リトライメカニズムの使用**：不安定な API に対してリトライを有効にし、信頼性を向上させます。
6. **リクエスト統計の監視**：`sdk.client.stats` または `client.request` ライフサイクルイベントを通じてリクエストの状況を監視します。
7. **WebSocket の高度なメソッドの使用**：優先して `iter_text` / `iter_json` などの高度なメソッドを使用し、メッセージタイプを区別する必要がある場合のみ `iter_messages` を使用します。

## 関連ドキュメント

- [ルートマネージャー](router.md) - HTTP/WebSocket サーバー側のルーティング（サーバー側 WebSocketConnection はクライアントと同じ基底クラスを共有）
- [アダプター開発ガイド](../developer-guide/adapters/getting-started.md) - アダプターでの HTTP クライアントの使用
- [ライフサイクル管理](lifecycle.md) - リクエストイベントのリッスン