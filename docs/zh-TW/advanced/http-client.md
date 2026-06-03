# HTTP 客戶端

ErisPulse 提供了統一的 HTTP 客戶端，模組和適配器應優先使用此客戶端發送 HTTP 請求，而非自行匯入 `aiohttp` / `httpx` 等第三方函式庫。

## 概述

HTTP 客戶端的主要功能：

- **統一介面**：提供 `get` / `post` / `put` / `delete` / `patch` / `request` 方法
- **自動日誌**：所有請求自動記錄日誌和統計資訊
- **生命週期整合**：每次請求觸發 `client.request` 生命週期事件
- **重試支援**：可配置自動重試次數和間隔
- **逾時控制**：獨立的連線逾時和請求逾時
- **連線集區複用**：基於 aiohttp.ClientSession 的連線集區管理

## 快速開始

```python
from ErisPulse.Core import client

# GET 請求
resp = await client.get("https://httpbin.org/get")
data = await resp.json()
print(resp.status)  # 200

# POST 請求
resp = await client.post(
    "https://httpbin.org/post",
    json={"key": "value"},
)
data = await resp.json()
```

## HttpResponse

所有請求方法返回 `HttpResponse` 物件：

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP 狀態碼 (如 200, 404)
resp.reason       # str | None - 狀態描述 (如 "OK")
resp.headers      # 回應標頭 (大小寫不敏感)
resp.content_type # str | None - Content-Type
resp.url          # 最終 URL (可能因重定向變化)
resp.raw          # 底層原生回應物件 (目前為 aiohttp.ClientResponse)

# 讀取回應主體
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # 解析 JSON
text = await resp.text("gbk")  # 指定編碼
```

## 請求方法

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

# JSON 請求體
resp = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice", "age": 30},
)

# 表單請求體
resp = await client.post(
    "https://api.example.com/login",
    data={"username": "admin", "password": "123"},
)

# 原始資料
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

### 通用 request

```python
from ErisPulse.Core import client

resp = await client.request(
    "OPTIONS",
    "https://api.example.com/resource",
    headers={"Origin": "https://example.com"},
)
```

## 參數說明

### 請求參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `url` | `str` | 請求 URL |
| `params` | `dict[str, str]` | 查詢參數 (可選) |
| `headers` | `dict[str, str]` | 額外請求標頭 (可選) |
| `data` | `Any` | 請求體 (表單或原始資料) (可選) |
| `json` | `Any` | JSON 請求體 (可選) |
| `timeout` | `float` | 本次請求逾時 (秒) (可選, 覆蓋預設值) |
| `max_retries` | `int` | 本次最大重試次數 (可選, 覆蓋預設值) |

## 逾時與重試

```python
from ErisPulse.Core import HttpClient

# 建立帶自訂逾時的客戶端
client = HttpClient(
    timeout=60,           # 請求總逾時 60s
    connect_timeout=5,    # 連線逾時 5s
    max_retries=3,        # 失敗自動重試 3 次
    retry_delay=2,        # 重試間隔 2s
)

# 單次請求覆蓋逾時
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

## 自訂預設標頭

```python
client = HttpClient(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)
```

## 請求統計

```python
from ErisPulse.Core import client

# 查看統計
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# 重置統計
client.reset_stats()
```

## 生命週期事件

每次請求完成後觸發 `client.request` 事件，可用於監控：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

## 上下文管理

```python
# 作為上下文管理器，自動關閉會話
async with HttpClient(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

## 在適配器中使用

適配器可使用全域客戶端或自行建立客戶端實例發送平台 API 請求：

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

> 也可透過 `from ErisPulse import sdk` 使用 `sdk.client`，效果相同。

## 最佳實踐

1. **優先使用全域客戶端**：使用 `from ErisPulse.Core import client` 取得全域單例，便於框架統一管理和監控
2. **避免直接匯入 aiohttp**：使用 `client` 取代 `aiohttp.ClientSession`，未來更換底層實作無需修改程式碼
3. **合理設定逾時**：根據 API 回應速度設定合理的逾時時間，避免長時間封鎖
4. **使用重試機制**：對不穩定的 API 啟用重試，提高可靠性
5. **監控請求統計**：透過 `sdk.client.stats` 或 `client.request` 生命週期事件監控請求情況

## 相關文件

- [路由管理器](router.md) - HTTP/WebSocket 伺服器端路由
- [適配器開發指南](../developer-guide/adapters/getting-started.md) - 適配器中使用 HTTP 客戶端
- [生命週期管理](lifecycle.md) - 監聽請求事件