# HTTP クライアント

ErisPulse は統一された HTTP クライアントを提供します。モジュールやアダプターは、サードパーティ製ライブラリである `aiohttp` や `httpx` を独自にインポートするのではなく、このクライアントを優先的に使用して HTTP リクエストを送信する必要があります。

## 概要

HTTP クライアントの主な機能：

- **統一インターフェース**：`get` / `post` / `put` / `delete` / `patch` / `request` メソッドを提供
- **自動ログ**：すべてのリクエストのログと統計情報を自動的に記録
- **ライフサイクルの統合**：各リクエストで `client.request` ライフサイクルイベントをトリガー
- **リトライサポート**：自動リトライの回数と間隔を設定可能
- **タイムアウト制御**：接続タイムアウトとリクエストタイムアウトを個別に設定
- **コネクションプールの再利用**：aiohttp.ClientSession に基づくコネクションプール管理

## クイックスタート

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

### リクエストパラメーター

| パラメーター | 型 | 説明 |
|------|------|------|
| `url` | `str` | リクエスト URL |
| `params` | `dict[str, str]` | クエリパラメーター (任意) |
| `headers` | `dict[str, str]` | 追加のリクエストヘッダー (任意) |
| `data` | `Any` | リクエストボディ (フォームまたは生データ) (任意) |
| `json` | `Any` | JSON リクエストボディ (任意) |
| `timeout` | `float` | 今回のリクエストタイムアウト (秒) (任意, デフォルト値を上書き) |
| `max_retries` | `int` | 今回の最大リトライ回数 (任意, デフォルト値を上書き) |

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

各リクエストの完了後に `client.request` イベントがトリガーされ、監視に使用できます。

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

## コンテキスト管理

```python
# コンテキストマネージャーとして使用し、セッションを自動的に閉じる
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## アダプターでの使用

アダプターは、グローバルクライアントを使用するか、独自にクライアントインスタンスを作成してプラットフォーム API リクエストを送信できます。

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases import BaseAdapter

class MyAdapter(BaseAdapter):
    async def call_api(self, endpoint, **params):
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        return await resp.json()
```

> `from ErisPulse import sdk` から `sdk.client` を使用することもでき、効果は同じです。

## ベストプラクティス

1. **グローバルクライアントを優先的に使用**：`from ErisPulse.Core import client` を使用してグローバルシングルトンを取得し、フレームワークによる統一管理と監視を容易にします。
2. **aiohttp の直接インポートを避ける**：`aiohttp.ClientSession` の代わりに `client` を使用することで、将来的に基盤の実装を変更する際にコードを修正する必要がなくなります。
3. **適切なタイムアウトの設定**：API の応答速度に応じて適切なタイムアウト時間を設定し、長時間のブロッキングを回避します。
4. **リトライメカニズムの使用**：不安定な API に対してリトライを有効にし、信頼性を向上させます。
5. **リクエスト統計の監視**：`sdk.client.stats` または `client.request` ライフサイクルイベントを通じてリクエストの状況を監視します。

## 関連ドキュメント

- [ルートマネージャー](router.md) - HTTP/WebSocket サーバー側のルーティング
- [アダプター開発ガイド](../developer-guide/adapters/getting-started.md) - アダプターでの HTTP クライアントの使用
- [ライフサイクル管理](lifecycle.md) - リクエストイベントのリッスン