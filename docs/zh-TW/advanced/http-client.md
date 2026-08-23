# 網路客戶端

ErisPulse 提供了統一的網路客戶端，聚合了 HTTP 請求、WebSocket 連接和連接池管理。模組和適配器**必須優先使用**此客戶端，而非自行導入 `aiohttp` / `httpx` / `requests` 等第三方庫。

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），請務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 概述

網路客戶端的主要功能：

- **統一介面**：提供 `get` / `post` / `put` / `delete` / `patch` / `request` 方法
- **WebSocket 客戶端**：透過 `ws_connect` 建立客戶端 WebSocket 連接
- **自動日誌**：所有請求自動記錄日誌和統計資訊
- **生命週期整合**：每次請求觸發 `client.request` 生命週期事件，WS 連接觸發 `client.ws.connect` 事件
- **重試支援**：可配置自動重試次數和間隔
- **超時控制**：獨立的連接超時和請求超時
- **連接池複用**：基於 aiohttp.ClientSession 的連接池管理
- **異常體系**：aiohttp 異常自動轉換為 ErisPulse 異常 (ClientError 体系)

請直接返回翻譯後的完整Markdown內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），請務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## 快速入門

### HTTP 請求

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

### WebSocket 連接

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

再次提醒：如果文件包含語言切換行（各語言名稱用 `` | `` 分隔的行），請務必嚴格遵守上方第8條的格式要求，不要寫出 ``[**Label**](file)`` 這類錯誤格式。

## HttpResponse

所有請求方法都會返回 `HttpResponse` 物件：

```python
from ErisPulse.Core import client

resp = await client.get("https://httpbin.org/get")

resp.status       # int - HTTP 狀態碼 (例如 200, 404)
resp.reason       # str | None - 狀態描述 (例如 "OK")
resp.headers      # 回應標頭 (大小寫不敏感)
resp.content_type # str | None - Content-Type
resp.url          # 最終 URL (可能因重定向而變更)
resp.raw          # 底層原生回應物件 (目前為 aiohttp.ClientResponse)

# 讀取回應主體
body = await resp.read()       # bytes
text = await resp.text()       # str
data = await resp.json()       # 解析 JSON
text = await resp.text("gbk")  # 指定編碼
```

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

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

# 原始數據
resp = await client.post(
    "https://api.example.com/upload",
    data=b"raw bytes",
    headers={"Content-Type": "application/octet-stream"},
)

# 文件上傳 (使用 files 參數, 無需導入 aiohttp)
# 格式: {字段名: 文件物件/bytes/(檔名, 檔案)/(檔名, 檔案, content_type)}
resp = await client.post(
    "https://api.example.com/upload",
    data={"description": "頭像"},            # 可選: 同時攜帶普通表單字段
    files={
        "file": ("photo.png", open("photo.png", "rb"), "image/png"),
    },
)

# 簡化寫法: 直接傳文件物件
resp = await client.post(
    "https://api.example.com/upload",
    files={"file": open("photo.png", "rb")},
)

# 內存數據直接上傳 (無需落盤)
import io

resp = await client.post(
    "https://api.example.com/upload",
    files={"file": ("data.txt", io.BytesIO(b"file content"), "text/plain")},
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

## 參數說明

### HTTP 請求參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `url` | `str` | 請求 URL |
| `params` | `dict[str, str]` | 查詢參數 (可選) |
| `headers` | `dict[str, str]` | 額外請求頭 (可選) |
| `data` | `Any` | 請求主體 (表單或原始數據) (可選) |
| `json` | `Any` | JSON 請求主體 (可選) |
| `files` | `dict[str, Any]` | 檔案上傳欄位 (可選, 自動建立 multipart/form-data) |
| `timeout` | `float` | 本次請求超時 (秒) (可選, 覆蓋預設值) |
| `max_retries` | `int` | 本次最大重試次數 (可選, 覆蓋預設值) |

### ws_connect 參數

| 參數 | 類型 | 說明 |
|------|------|------|
| `url` | `str` | WebSocket 伺服器 URL |
| `headers` | `dict[str, str]` | 額外請求頭 (可選) |
| `heartbeat` | `float` | 心跳間隔秒數 (可選) |

## 超時與重試

```python
from ErisPulse.Core import Client

# 建立帶自訂超時的客戶端
client = Client(
    timeout=60,           # 請求總超時 60 秒
    connect_timeout=5,    # 連線超時 5 秒
    max_retries=3,        # 失敗自動重試 3 次
    retry_delay=2,        # 重試間隔 2 秒
)

# 單次請求覆蓋超時
resp = await client.get("https://slow-api.example.com/data", timeout=120)
```

> [!NOTE]
> 客戶端類別自 2.8.0 版起更名為 `Client`（`sdk.client` 屬性名不變）；舊名 `HttpClient` 保留為相容別名，舊代碼無需修改。

[**簡體中文**](docs/zh-TW/timeout-retry.md) | [**繁體中文**](docs/zh-TW/timeout-retry.md) | [**English**](docs/en/timeout-retry.md)

## 自訂預設標頭

```python
client = Client(
    headers={
        "Authorization": "Bearer token",
        "X-App-Id": "my-app",
    },
    user_agent="MyBot/1.0",
)

## 請求統計

```python
from ErisPulse.Core import client

# 查看統計
stats = client.stats
# {"total_requests": 42, "total_errors": 1, "total_bytes_sent": 0, "total_bytes_received": 0}

# 重設統計
client.reset_stats()

## 生命週期事件

### HTTP 請求事件

每次請求完成後觸發 `client.request` 事件，可用於監控：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.request")
async def on_request(event_data):
    print(f"{event_data['method']} {event_data['url']} -> {event_data['status']} ({event_data['elapsed']}s)")
```

### WebSocket 連接事件

每次 WebSocket 連接建立後觸發 `client.ws.connect` 事件：

```python
from ErisPulse.Core import lifecycle

@lifecycle.on("client.ws.connect")
async def on_ws_connect(event_data):
    print(f"WS 連接: {event_data['url']}")

## 上下文管理

```python
# 作為上下文管理器，自動關閉會話
async with Client(timeout=30) as client:
    resp = await client.get("https://httpbin.org/get")
    data = await resp.json()
```

7. **重要：路徑替換規則**
   - 將文件連結中的 `docs/zh-TW/` 替換為 `docs/zh-TW/`
   - 例如：`docs/zh-TW/quick-start.md` 應改為 `docs/zh-TW/quick-start.md`
   - 對於指向非當前語言版本文件的連結（如 `README.xx.md` 形式的連結），保持原樣不要修改
   - 這確保連結指向正確語言的文件版本

## WebSocket 客戶端

透過 `client.ws_connect()` 建立 WebSocket 客戶端連接，回傳 `ClientWebSocket` 物件。客戶端與服務端 WebSocket 共享相同的 `WebSocketConnectionBase` 基類，send/receive/iter 接口完全一致。

### 基本用法

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws", heartbeat=30)

await ws.send_text("Hello")
await ws.send_bytes(b"\x00\x01\x02")
await ws.send_json({"type": "ping"})
```

### 接收訊息

#### 高階方法 (推薦)

自動過濾訊息類型，斷開時拋出 `WebSocketDisconnect`：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import WebSocketDisconnect

ws = await client.ws_connect("wss://example.com/ws")

# 單筆接收
text = await ws.receive_text()    # str
data = await ws.receive_bytes()   # bytes
obj = await ws.receive_json()     # dict / list

# 迭代接收 (斷開時自動停止)
async for text in ws.iter_text():
    print(text)

async for data in ws.iter_bytes():
    print(data)

async for obj in ws.iter_json():
    print(obj)
```

#### 低階方法

使用 `receive()` 和 `iter_messages()` 處理原始訊息類型，可區分 TEXT / BINARY / CLOSE / ERROR：

```python
from ErisPulse.Core import client
from ErisPulse.Core.Bases.websocket import WSMessage

ws = await client.ws_connect("wss://example.com/ws")

# 單筆接收原始訊息
msg = await ws.receive()
# msg.type  -> WSMessage.TEXT / WSMessage.BINARY / WSMessage.CLOSE / WSMessage.ERROR
# msg.data  -> str | bytes | None

# 迭代原始訊息 (CLOSE/ERROR 時自動停止)
async for msg in ws.iter_messages():
    if msg.type == WSMessage.TEXT:
        print(f"文本: {msg.data}")
    elif msg.type == WSMessage.BINARY:
        print(f"二進位: {len(msg.data)} bytes")
```

### WSMessage

`WSMessage` 是統一的 WebSocket 訊息類型，不依賴底層函式庫：

| 屬性 | 類型 | 說明 |
|------|------|------|
| `type` | `str` | 訊息類型: `WSMessage.TEXT` / `WSMessage.BINARY` / `WSMessage.CLOSE` / `WSMessage.ERROR` |
| `data` | `Any` | 訊息資料 |

### ClientWebSocket 屬性

| 屬性 | 類型 | 說明 |
|------|------|------|
| `url` | `URL` | 連接 URL |
| `headers` | `Headers` | 回應標頭 |
| `closed` | `bool` | 連接是否已關閉 |
| `raw` | `object` | 底層原生物件 (aiohttp.ClientWebSocketResponse) |

### 生命週期鉤子

與 `服務端 WebSocketConnection` 一致，支援 `on_disconnect` 和 `on_error` 回呼：

```python
from ErisPulse.Core import client

ws = await client.ws_connect("wss://example.com/ws")

@ws.on_disconnect
async def handle_disconnect(ws, reason="unknown"):
    print(f"連接斷開: {reason}")

@ws.on_error
async def handle_error(ws, error=""):
    print(f"連接錯誤: {error}")
```

### 關閉連接

```python
await ws.close(code=1000, reason="Normal closure")

## 異常體系

ErisPulse 定義了統一的異常層級，透過 `sdk.client` 發起的請求會自動將底層 aiohttp 異常轉換為 ErisPulse 異常。

> **向後相容**：直接使用 `aiohttp.ClientSession` 的舊模組/適配器完全不受影響。異常轉換僅在透過 `sdk.client` 發起請求時生效，直接使用 aiohttp 的程式碼仍然捕獲 `aiohttp.ClientError` 等原生異常。兩種方式可以共存。

### 異常層級

```
ErisPulseError
├── ClientError                  # 所有 HTTP/WS 客戶端請求異常的基類
│   ├── ClientConnectionError    # 連線失敗 (DNS 解析失敗、連線被拒絕、網路不可達)
│   ├── ClientTimeoutError       # 連線超時或請求超時
│   └── HTTPStatusError          # HTTP 4xx/5xx 狀態碼錯誤
└── WebSocketError               # WebSocket 異常基類
    └── WebSocketDisconnect      # WebSocket 連線中斷 (客戶端和服務端通用)
```

### 異常捕獲

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

# HTTP 請求異常處理
try:
    resp = await client.get("https://api.example.com/data")
    data = await resp.json()
except ClientConnectionError:
    print("無法連接到伺服器")
except ClientTimeoutError:
    print("請求超時")
except ClientError as e:
    print(f"請求失敗: {e}")

# WebSocket 異常處理
try:
    ws = await client.ws_connect("wss://example.com/ws")
    async for text in ws.iter_text():
        await ws.send_text(f"Echo: {text}")
except WebSocketDisconnect as e:
    print(f"連線中斷: code={e.code}, reason={e.reason}")
except WebSocketError as e:
    print(f"WebSocket 錯誤: {e}")
```

### 統一捕獲

使用 `ClientError` 統一捕獲所有 HTTP/WS 客戶端請求異常：

```python
from ErisPulse.Core.Bases.errors import ClientError

try:
    resp = await client.get("https://api.example.com/data")
except ClientError as e:
    print(f"客戶端錯誤: {e}")
```

### HTTPStatusError

當需要在請求後檢查狀態碼並拋出異常時，可手動使用：

```python
from ErisPulse.Core.Bases.errors import HTTPStatusError

resp = await client.get("https://api.example.com/data")
if resp.status >= 400:
    raise HTTPStatusError(resp.status, await resp.text())

## 在適配器中使用

適配器可以使用全域客戶端或自行建立客戶端實例來發送平台 API 請求：

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
            self.logger.error(f"API 調用失敗: {e}")
            raise
```

> 也可以透過 `from ErisPulse import sdk` 使用 `sdk.client`，效果相同。

## 重要：路徑替換規則
- 將文件連結中的 `docs/zh-TW/` 替換為 `docs/zh-TW/`
- 例如：`docs/zh-TW/quick-start.md` 應改為 `docs/zh-TW/quick-start.md`
- 對於指向非當前語言版本文件的連結（如 `README.xx.md` 形式的連結），保持原樣不要修改
- 這確保了連結指向正確語言的文件版本

## 最佳實踐

1. **優先使用全域客戶端**：使用 `from ErisPulse.Core import client` 取得全域單例，便於框架統一管理和監控
2. **避免直接導入 aiohttp**：使用 `client` 替代 `aiohttp.ClientSession`，未來更換底層實作無需修改程式碼。舊程式碼直接使用 aiohttp 仍可正常運作，兩種方式可以共存
3. **使用 ErisPulse 異常體系**：透過 `sdk.client` 發出請求時捕獲 `ClientError` 而非 `aiohttp.ClientError`，確保程式碼不依賴特定 HTTP 庫。直接使用 aiohttp 的舊程式碼不受影響
4. **合理設定超時**：根據 API 回應速度設定合理的超時時間，避免長時間阻塞
5. **使用重試機制**：對不穩定的 API 啟用重試，提高可靠性
6. **監控請求統計**：透過 `sdk.client.stats` 或 `client.request` 生命週期事件監控請求情況
7. **WebSocket 使用高階方法**：優先使用 `iter_text` / `iter_json` 等高階方法，僅在需要區分訊息類型時使用 `iter_messages`

請直接返回翻譯後的完整 Markdown 內容，不要包含任何其他文字。

## 相關文件

- [路由管理器](router.md) - HTTP/WebSocket 服務端路由（服務端 WebSocketConnection 與客戶端共享同一基類）
- [適配器開發指南](../developer-guide/adapters/getting-started.md) - 適配器中使用 HTTP 客戶端
- [生命週期管理](lifecycle.md) - 監聽請求事件