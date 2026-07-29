# ErisPulse API 動作標準

本文檔定義 ErisPulse 适配器中 **OneBot12 標準 API 動作**的統一介面規範，使模組開發者可以面向標準介面編程，由适配器負責映射到平台原生 API。

## 1. 設計背景

在 ErisPulse 中，訊息段（訊息收發）和事件格式已經完全遵循 OneBot12 標準，但 **API 動作呼叫**（如獲取用戶資訊、獲取群列表、撤回訊息等）此前未統一——模組開發者必須為每個平台寫不同的 `call_api` 呼叫。

`ApiDSL` 通過提供強類型的標準動作方法，解決這個問題：

```
模組代碼（跨平台統一）             适配器實現（平台特定）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  适配器 call_api / 覆蓋
adapter.Api.get_group_list()      →  适配器 call_api / 覆蓋
adapter.Api.delete_message("id")  →  适配器 call_api / 覆蓋
```

## 2. 三層 DSL 並行結構

ErisPulse 适配器有三個並行的 DSL 內部類，各司其職：

```
BaseAdapter
├── Send(SendDSL)       ← 訊息發送（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← 請求操作（accept/reject）
└── Api(ApiDSL)          ← 標準 API 動作（資訊查詢/群管理/訊息管理/檔案操作）★
```

| DSL | 職責 | 方法風格 | 返回值 |
|-----|------|---------|--------|
| `Send` | 發送訊息 | 鏈式 + `asyncio.Task` | 標準響應 |
| `Request` | 處理請求事件 | `asyncio.Task` | 標準響應 |
| `Api` | 查詢/管理操作 | `async` 方法 | 標準響應 |

## 3. 標準動作列表

### 3.1 用戶相關

| 方法 | OB12 動作 | 參數 | data 返回 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | 無 | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | 無 | `list[get_user_info 響應]` |

### 3.2 群組相關

| 方法 | OB12 動作 | 參數 | data 返回 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | 無 | `list[get_group_info 響應]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info 響應]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | 無 |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | 無 |

### 3.3 訊息管理

| 方法 | OB12 動作 | 參數 | 說明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | 撤回/刪除訊息 |

> **發送訊息**（`send_message`）由 `SendDSL` 的 `Raw_ob12` 處理，不在 `ApiDSL` 中重複。

### 3.4 檔案操作

| 方法 | OB12 動作 | 參數 | data 返回 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` 的 `type` 參數：
- `"url"`：透過 URL 上傳（需提供 `url`）
- `"path"`：透過本地路徑上傳（需提供 `path`）
- `"data"`：透過二進位資料上傳（需提供 `data`）

### 3.5 通用擴展動作

| 方法 | 說明 |
|------|------|
| `call(action, **params)` | 平台擴展動作的逃生艙，遵循 OB12 擴展命名規則 `{prefix}.{action}` |

## 4. 使用方式

### 4.1 基本呼叫

```python
from ErisPulse import adapter

# 獲取用戶資訊（跨平台統一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"用戶名: {user_name}")

# 獲取群列表
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# 撤回訊息
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 指定 Bot 賬號（多賬號模式）

```python
# 使用指定 Bot 賬號執行操作
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 平台擴展動作

```python
# 呼叫平台特有的擴展動作（建議使用 {prefix}.{action} 命名）
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 在事件處理器中使用

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # 獲取發送者詳細資訊
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"你好，{user_name}！")
```

## 5. 适配器實現

### 5.1 預設行為（零配置）

`ApiDSL` 的預設實現將標準動作名作為 `endpoint` 直接傳遞給 `adapter.call_api()`：

```python
# ApiDSL 預設實現等價於：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**適用場景**：适配器後端本來就是 OneBot12 實現（如 NapCat、Lagrange 等），`call_api` 天然支援標準動作名。

### 5.2 覆蓋標準方法（映射到平台原生 API）

适配器可覆蓋單個標準方法，將其映射到平台原生 API：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 標準 API 動作實現"""

        async def get_user_info(self, user_id: str) -> dict:
            # 映射到平台原生 API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34001, message="用戶不存在")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 未支援的動作

适配器未覆蓋的標準方法走預設實現（委託給 `call_api`）。如果 `call_api` 也不支援該動作，應返回標準錯誤響應：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"不支援的動作: {endpoint}")
    # ... 平台 API 呼叫
```

模組開發者可透過返回值的 `retcode` 判斷是否支援：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("該平台不支援獲取好友列表")
```

## 6. 響應格式

所有 `ApiDSL` 方法返回標準 API 響應格式（詳見 [API 響應標準](docs/zh-TW/api-response.md)）：

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **注意**：資訊查詢類動作的 `message_id` 為空字串（僅訊息發送類動作才有 `message_id`）。

## 7. 與 SendDSL / RequestDSL 的關係

| 場景 | 使用 DSL | 範例 |
|------|---------|------|
| 發送訊息 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| 同意/拒絕請求 | `Request` | `adapter.Request("req_id").accept()` |
| 獲取用戶/群資訊 | `Api` | `adapter.Api.get_user_info("123")` |
| 撤回訊息 | `Api` | `adapter.Api.delete_message("msg_id")` |
| 退出群 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. 适配器實現檢查清單

### 標準動作
- [ ] `call_api` 能處理標準動作名（或覆蓋對應 `ApiDSL` 方法）
- [ ] 不支援的動作返回 `retcode=10002`
- [ ] 返回值遵循標準 API 響應格式
- [ ] `data` 欄位包含 OB12 標準定義的欄位

### 擴展動作
- [ ] 平台擴展動作使用 `{prefix}.{action}` 命名
- [ ] 擴展動作的參數和響應仍遵循 OB12 動作請求/響應結構

## 9. 相關文檔

- [API 響應標準](docs/zh-TW/api-response.md) - 适配器 API 響應格式標準
- [發送方法規範](docs/zh-TW/send-method-spec.md) - Send 類的方法命名和參數規範
- [請求操作規範](docs/zh-TW/request-action-spec.md) - Request DSL 的使用方式
- [事件轉換標準](docs/zh-TW/event-conversion.md) - 事件格式和訊息段標準