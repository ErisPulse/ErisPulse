# ErisPulse 請求操作規範

本文檔定義了 ErisPulse 適配器中請求事件操作的標準化規範，包括請求事件的欄位要求、Request DSL 的使用方式和適配器實現要求。

## 1. 概述

請求事件（`type: "request"`）是 OneBot12 標準中定義的特殊事件類型，代表需要 Bot 做出決策的請求（如好友請求、群邀請等）。

與消息事件不同，請求事件需要**雙向互動**：
1. **接收**：適配器將平台原生請求轉換為標準請求事件
2. **響應**：模組通過 `Request` DSL 或 `Event.approve()`/`Event.reject()` 執行操作

```
平台原生請求事件
    │
    ▼
Converter.convert()        ← 適配器實現（正向轉換）
    │
    ▼
標準請求事件 (含 request_id)
    │
    ├─→ 模組處理器 @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← 同意請求
    │       └─→ event.reject()      ← 拒絕請求
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← 適配器重寫
    │               │
    │               ▼
    │       平台 API 調用
    │
    └─→ 或直接通過適配器操作
            await adapter.Request("req_id").accept()
```

## 2. 請求事件字段要求

### 2.1 標準字段

請求事件除必須包含 OneBot12 標準字段外，還需包含以下字段：

| 字段 | 類型 | 必選 | 說明 |
|------|------|------|------|
| `request_id` | string | **強烈推薦** | 請求標識符，用於同意/拒絕操作 |
| `user_id` | string | 是 | 請求發起者ID |
| `user_nickname` | string | 否 | 請求發起者暱稱 |
| `comment` | string | 否 | 請求附言 |

### 2.2 `request_id` 字段

`request_id` 是請求操作的核心標識符：

- **用途**：標識一個可操作的請求，供 `Request` DSL 使用
- **生成規則**：
  - 優先使用平台原生的請求標識（如 OneBot11 的 `flag` 字段、Telegram 的 `chat_invite_link` 等）
  - 如果平台沒有原生請求ID，適配器應生成一個唯一標識（建議格式：`{platform}_{timestamp}_{user_id}`）
- **唯一性**：在同一平台範圍內應保持唯一
- **缺失行為**：當 `request_id` 缺失時，`event.approve()` / `event.reject()` 將拋出 `ValueError`

### 2.3 請求事件示例

```json
{
  "id": "evt_123456",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "請加好友",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 鏈式呼叫

`Request` 提供與 `Send` 風格一致的鏈式呼叫介面：

```python
# 基本用法
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# 指定 Bot 賬號
await adapter.Request("req_id").Using("bot1").accept()

# 附帶備註（透過 kwargs）
await adapter.Request("req_id").accept(comment="歡迎")
await adapter.Request("req_id").reject(comment="暫不添加")

# 組合使用
await adapter.Request("req_id").Using("bot1").accept(comment="歡迎")
```

### 3.2 方法列表

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `Using(account_id)` | 指定執行操作的 Bot 賬號 | `RequestDSL`（支援鏈式呼叫） |
| `accept(**kwargs)` | 同意請求 | `asyncio.Task`（await 後返回標準回應） |
| `reject(**kwargs)` | 拒絕請求 | `asyncio.Task`（await 後返回標準回應） |

### 3.3 返回值格式

操作返回標準 API 回應格式：

**成功**：
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**失敗**：
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "請求已過期或不存在"
}
```

**未實現**（適配器未重寫 `accept`/`reject`）：
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "平台 MyAdapter 未實現請求操作 (accept)"
}
```

## 4. Event 便捷方法

`Event` 包裝類提供了便捷方法，適合在請求事件處理器中使用：

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # 檢查請求ID
    request_id = event.get_request_id()
    if not request_id:
        print("警告：請求事件缺少 request_id")
        return
    
    # 同意請求
    result = await event.approve()
    
    # 或拒絕請求
    # result = await event.reject(comment="暫不添加好友")
    
    # 檢查結果
    if result.get("status") == "ok":
        print("操作成功")
    else:
        print(f"操作失敗: {result.get('message')}")
```

### 4.1 Event 方法列表

| 方法 | 說明 | 回傳值 |
|------|------|--------|
| `get_request_id()` | 取得請求ID | `str` |
| `approve(comment=None)` | 同意當前請求事件 | 標準回應格式 |
| `reject(comment=None)` | 拒絕當前請求事件 | 標準回應格式 |

## 5. 适配器實現要求

### 5.1 轉換器要求

適配器的轉換器在轉換請求事件時，**必須**正確設置 `request_id` 欄位：

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """轉換平台原生請求事件"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" 或 "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← 關鍵欄位
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    從平台原生事件提取請求ID
    
    优先使用平台原生的请求标识，若无则生成唯一ID
    """
    # 优先使用平台原生ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # 兜底：生成唯一ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request 內部類實現

適配器在 `Request` 內部類中重寫 `accept` 和 `reject` 即可：

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform 請求操作實現"""
        
        def accept(self, **kwargs):
            """
            同意請求
            
            :param kwargs: 扩展参数，如 comment="备注"
            :return: asyncio.Task
            """
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=True,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"請求操作失敗: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """拒絕請求"""
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=False,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"請求操作失敗: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 平台不支援請求操作

如果平台本身不支援好友請求/群邀請操作（如某些平台自動處理請求），適配器可以：

1. **不重寫 `Request` 內部類**：使用基類預設實現，調用 `accept()`/`reject()` 時返回 `retcode=10002`
2. **在轉換時跳過 `request_id`**：不生成 `request_id`，讓 `event.approve()` 抛出 `ValueError`
3. **記錄日誌**：在 `accept`/`reject` 中記錄警告並返回適當錯誤碼

### 5.4 總結：Send 與 Request 並行

適配器有兩個並行的 DSL 內部類，各司其職：

```
BaseAdapter
├── Send(SendDSL)     ← 消息發送
│   ├── Raw_ob12()    ← 必須實現
│   ├── Text()        ← 推薦實現
│   └── Image()       ← 按需實現
│
└── Request(RequestDSL) ← 請求操作
    ├── accept()        ← 按需實現
    └── reject()        ← 按需實現
```

### 5.5 適配器 `__init__` 注意事項

重寫 `Request` 內部類的 `__init__` 時，必須透傳參數並調用 `super().__init__()`，詳見 [適配器開發入門 - `__init__` 注意事項](../developer-guide/adapters/getting-started.md#init-注意事项)（`Request` 同理，參數為 `adapter, request_id, account_id`）。

## 6. 适配器實現檢查清單

### 基礎要求
- [ ] 若重寫了 `__init__`，已調用 `super().__init__()`（確保 Send / Request 工廠初始化）

### 請求事件轉換
- [ ] 請求事件包含 `request_id` 字段（強烈推薦）
- [ ] `detail_type` 正確映射為 `"friend"` 或 `"group"`
- [ ] 保留平台原始數據在 `{platform}_raw` 字段中
- [ ] `request_id` 生成規則有文件說明

### 請求操作
- [ ] `Request` 內部類已實現（如平台支援請求操作）
- [ ] `accept()` 方法已實現
- [ ] `reject()` 方法已實現
- [ ] 操作返回標準 API 回應格式
- [ ] 不支援的操作返回 `retcode=10002`
- [ ] 網路錯誤返回 `retcode=33xxx`（遵循 API 回應標準）

## 7. 錯誤碼擴展

請求操作相關的**適配器實現層**推薦錯誤碼（遵循 [API 响应标准](api-response.md) §3.2，  
落在 `34xxx` 平台錯誤段的低三位自定義）：

| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 34001 | Request Not Found | 請求不存在或已過期 |
| 34002 | Request Already Handled | 請求已被處理 |
| 34003 | Request Not Supported | 平台不支援該類型的請求操作 |
| 34004 | Permission Denied | Bot 無權處理此請求（平台返回） |

> **與框架碼的邊界**：以上 `340xx` 是**平台/適配器**返回的請求處理失敗；  
> ErisPulse 框架在 `scope.actions` 禁用某模組的 request 動作時，**在呼叫適配器之前**  
> 直接返回 `34601`（Action Denied，見 [API 响应标准 §5.3](api-response.md#53-框架擴展返回碼34xxx-平台錯誤段的低三位自定義)），  
> 兩者互不替代：先過 `34601` 框架閘口，再落到平台層 `340xx` 錯誤。

## 8. 相關文件

- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範
- [API 回應標準](api-response.md) - 適配器 API 回應格式標準
- [發送方法規範](send-method-spec.md) - Send 類的方法命名和參數規範
- [會話類型標準](session-types.md) - 會話類型定義和映射關係