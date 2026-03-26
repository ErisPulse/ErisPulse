# 介面卡系統 API

本文件詳細介紹了 ErisPulse 介面卡系統的 API。

## Adapter 管理器

### 取得介面卡

```python
from ErisPulse import sdk

# 透過名稱取得介面卡
adapter = sdk.adapter.get("platform_name")

# 透過屬性存取
adapter = sdk.adapter.platform_name
```

### 介面卡事件監聽

```python
# 監聽 OneBot12 標準事件
@sdk.adapter.on("message")
async def handle_message(event):
    pass

# 監聽特定平台的標準事件
@sdk.adapter.on("message", platform="yunhu")
async def handle_yunhu_message(event):
    pass

# 監聽平台原生事件
@sdk.adapter.on("raw_event", raw=True, platform="yunhu")
async def handle_raw_event(data):
    pass
```

### 介面卡管理

```python
# 取得所有平台
platforms = sdk.adapter.platforms

# 檢查介面卡是否存在
exists = sdk.adapter.exists("platform_name")

# 啟用/停用介面卡
sdk.adapter.enable("platform_name")
sdk.adapter.disable("platform_name")

# 啟動/關閉介面卡
await sdk.adapter.startup(["platform1", "platform2"])
await sdk.adapter.shutdown()
```

## 中介軟體

### 註冊中介軟體

```python
# 新增中介軟體
@sdk.adapter.middleware
async def my_middleware(event):
    # 處理事件
    sdk.logger.info(f"中介軟體處理: {event}")
    return event
```

### 中介軟體執行順序

中介軟體依照註冊順序執行，在事件分發到處理器之前執行。

## Send 訊息發送

### 基本發送

```python
# 取得介面卡
adapter = sdk.adapter.get("platform")

# 發送文字訊息
await adapter.Send.To("user", "123").Text("Hello")

# 發送圖片訊息
await adapter.Send.To("group", "456").Image("https://example.com/image.jpg")
```

### 指定發送帳號

```python
# 使用帳戶名稱
await adapter.Send.Using("account1").To("user", "123").Text("Hello")

# 使用帳戶 ID
await adapter.Send.Using("bot_id").To("user", "123").Text("Hello")
```

### 查詢支援的發送方法
> 由於新的標準規範要求使用重寫 `__getattr__` 方法來實現兜底發送機制，導致無法使用 `hasattr` 方法來檢查方法是否存在，故從 `2.3.5-dev.3` 開始，新增 `list_sends` 方法來查詢支援的所有發送方法。

```python
# 列出平台支援的所有發送方法
methods = sdk.adapter.list_sends("onebot11")
# 回傳: ["Text", "Image", "Voice", "Markdown", ...]

# 取得某個方法的詳細資訊
info = sdk.adapter.send_info("onebot11", "Text")
# 回傳:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "發送文字訊息..."
# }
```

### 鏈式修飾

```python
# @使用者
await adapter.Send.To("group", "456").At("789").Text("你好")

# @全體成員
await adapter.Send.To("group", "456").AtAll().Text("大家好")

# 回覆訊息
await adapter.Send.To("group", "456").Reply("msg_id").Text("回覆內容")

# 組合使用
await adapter.Send.To("group", "456").At("789").Reply("msg_id").Text("回覆@的訊息")
```

## API 呼叫

### call_api 方法
> 注意，各個平台的 API 呼叫方式可能不同，請參考對應平台介面卡文件
> 並不建議直接使用 call_api 方法，建議使用 Send 類別進行訊息發送

```python
# 呼叫平台 API
result = await adapter.call_api(
    endpoint="/send",
    content="Hello",
    recvId="123",
    recvType="user"
)

# 標準化回應
{
    "status": "ok",
    "retcode": 0,
    "data": {...},
    "message_id": "msg_id",
    "message": "",
    "{platform}_raw": raw_response
}
```

## 介面卡基類

### BaseAdapter 方法

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    def __init__(self, sdk):
        # 初始化介面卡
        pass
    
    async def start(self):
        """啟動介面卡（必須實作）"""
        pass
    
    async def shutdown(self):
        """關閉介面卡（必須實作）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """呼叫平台 API（必須實作）"""
        pass
```

### Send 巢狀類別

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        def Text(self, text: str):
            """發送文字訊息"""
            import asyncio
            return asyncio.create_task(
                self._adapter.call_api(
                    endpoint="/send",
                    content=text,
                    recvId=self._target_id,
                    recvType=self._target_type
                )
            )
```

## 相關文件

- [核心模組 API](core-modules.md) - 核心模組 API
- [事件系統 API](event-system.md) - Event 模組 API
- [介面卡開發指南](../developer-guide/adapters/) - 開發平台介面卡