# ErisPulse API 動作標準

本文檔定義 ErisPulse 適配器中 **OneBot12 標準 API 動作**的統一介面規範，使模組開發者可以面向標準介面編程，由適配器負責映射到平台原生 API。

> **涵蓋範圍**：OneBot12 標準動作中，`ApiDSL` 提供使用者 / 群組 / 頻道（Guild）/
> 消息管理 / 元（Meta）常規介面的強類型方法（`send_message` 由
> `SendDSL.Raw_ob12` 承擔）。檔案資源動作（`upload_file` / `get_file` / 分片）僅作
> 降級透傳保留，見 §3.5 說明。平台擴展動作經 `Api.call("prefix.action", ...)`
> 逃生艙調用。動作參數與回傳結構以 OneBot12 規範（倉庫內 `onebot/specs/interface/`）為準。

## 1. 設計背景

在 ErisPulse 中，訊息段（訊息收發）和事件格式已經完全遵循 OneBot12 標準，但 **API 動作呼叫**（如獲取使用者資訊、獲取群組列表、撤回訊息等）此前未統一——模組開發者必須為每個平台寫不同的 `call_api` 呼叫。

`ApiDSL` 透過提供強類型的標準動作方法，解決這一問題：

```
模組程式碼（跨平台統一）             適配器實作（平台特定）
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  適配器 call_api / 覆蓋
adapter.Api.get_group_list()      →  適配器 call_api / 覆蓋
adapter.Api.delete_message("id")  →  適配器 call_api / 覆蓋
```

## 2. 三層 DSL 並行結構

ErisPulse 適配器有三個並行的 DSL 內部類，各司其職：

```
BaseAdapter
├── Send(SendDSL)       ← 訊息發送（Text/Image/Raw_ob12）
├── Request(RequestDSL)  ← 請求操作（accept/reject）
└── Api(ApiDSL)          ← 標準 API 動作（使用者/群組/頻道/訊息管理/檔案/元）★
```

| DSL | 職責 | 方法風格 | 回傳值 |
|-----|------|---------|--------|
| `Send` | 發送訊息 | 串鏈 + `asyncio.Task` | 標準回應 |
| `Request` | 處理請求事件 | `asyncio.Task` | 標準回應 |
| `Api` | 查詢/管理操作 | `async` 方法 | 標準回應 |

## 3. 標準動作列表

### 3.1 使用者相關

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | 無 | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | 無 | `list[get_user_info 回應]` |

### 3.2 群組相關

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | 無 | `list[get_group_info 回應]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info 回應]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | 無 |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | 無 |

### 3.3 訊息管理

| 方法 | OB12 動作 | 參數 | 說明 |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | 撤回/刪除訊息 |

> **發送訊息**（`send_message`）由 `SendDSL` 的 `Raw_ob12` 處理，不在 `ApiDSL` 中重複。

### 3.4 頻道（Guild）相關

OneBot12 頻道體系分兩級：**頻道（guild）** 與 **子頻道（channel）**。

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | 無 | `list[get_guild_info 回應]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | 無 |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info 回應]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | 無 |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info 回應]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | 無 |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info 回應]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | 無 |

> 頻道體系與群組（group）彼此獨立：Discord / QQ 頻道 / Kook 等平台實作頻道介面，
> 傳統 QQ / 微信實作群組介面，兩者可同時存在或僅其一。

### 3.5 檔案資源操作

> [!WARNING]
> **檔案資源模型（file_id 兩段式）在 ErisPulse 屬"降級可用"**：
> ErisPulse 的檔案收發不走"先上傳拿 file_id 再引用"模型——模組發檔案用
> `SendDSL.File(file, filename)`（URL / 路徑 / 字節**發送時直傳**，見
> [發送方法規範](send-method-spec.md)）。
> 本節 `upload_file` / `get_file` / 分片動作依賴平台特有的 `file_id` 檔案資源
> 能力，**通用性不足**；僅當適配器後端天然具備該能力時才可透傳，框架內建
> 適配器**不實作也不建議實作**，呼叫時通常回傳 `retcode=10002`。
> 模組需要跨平台傳檔案時，請使用 `SendDSL.File`，勿依賴 file_id。
>
> **展望**：`file_id` 資源模型標準化到框架層是未來的方向，當前版本不提供。

整包傳輸（小檔案）：

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

`upload_file` 的 `type` 參數：
- `"url"`：透過 URL 上傳（需提供 `url`）
- `"path"`：透過本地路徑上傳（需提供 `path`）
- `"data"`：透過二進位資料上傳（需提供 `data`）

#### 3.5.1 分片傳輸（大檔案，屬上述降級範圍）

OneBot12 分片動作按 `stage` 區分階段。`ApiDSL` 將同一動作的三/兩階段拆分為獨立方法
（`offset` 為位元組偏移，`data` 在 JSON 中為 Base64）；下表僅為查閱保留，
適配器無需也不應強制實作：

**分片上傳三步**：`prepare` → `transfer`（循環逐片）→ `finish`

| 方法 | 對應 stage | 參數 | data 回傳 |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id`（傳輸期用） |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | 無 |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str`（整檔案校驗） | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**分片下載兩步**：`prepare` → `transfer`（循環取片）

| 方法 | 對應 stage | 參數 | data 回傳 |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data`（本次分片位元組） |

### 3.6 元（Meta）動作

元動作不針對具體帳號，無需 `Using()` 指定 Bot。

| 方法 | OB12 動作 | 參數 | data 回傳 |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | 事件物件陣列（不含元事件） |
| `get_supported_actions()` | `get_supported_actions` | 無 | `list[str]` 支援的動作名 |
| `get_status()` | `get_status` | 無 | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | 無 | `impl`, `version`, `onebot_version` |

### 3.7 通用擴展動作

| 方法 | 說明 |
|------|------|
| `call(action, **params)` | 平台擴展動作的逃生艙，遵循 OB12 擴展命名規則 `{prefix}.{action}` |

## 4. 使用方式

### 4.1 基本呼叫

```python
from ErisPulse import adapter

# 獲取使用者資訊（跨平台統一）
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"使用者名: {user_name}")

# 獲取群組列表
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# 撤回訊息
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 指定 Bot 帳號（多帳戶模式）

```python
# 使用指定 Bot 帳號執行操作
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

## 5. 適配器實作

### 5.1 預設行為（零設定）

`ApiDSL` 的預設實作將標準動作名作為 `endpoint` 直接傳遞給 `adapter.call_api()`：

```python
# ApiDSL 預設實作等價於：
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**適用場景**：當適配器的底層後端自身即遵循 OneBot12 標準動作協議時，
`call_api` 天然支援標準動作名（如直接對接遵循該協議的服務端）。

### 5.2 覆蓋標準方法（映射到平台原生 API）

適配器可覆蓋單個標準方法，將其映射到平台原生 API：

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform 標準 API 動作實作"""

        async def get_user_info(self, user_id: str) -> dict:
            # 映射到平台原生 API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                return self._adapter.make_error(retcode=34600, message="使用者不存在")

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

適配器未覆蓋的標準方法走預設實作（委派給 `call_api`）。如果 `call_api` 也不支援該動作，應回傳標準錯誤回應：

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"不支援的動作: {endpoint}")
    # ... 平台 API 呼叫
```

模組開發者可透過回傳值的 `retcode` 判斷是否支援：

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("該平台不支援獲取好友列表")
```

## 6. 回應格式

所有 `ApiDSL` 方法回傳標準 API 回應格式（詳見 [API 回應標準](api-response.md)）：

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

| 場景 | 使用 DSL | 示例 |
|------|---------|------|
| 發送訊息 | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| 同意/拒絕請求 | `Request` | `adapter.Request("req_id").accept()` |
| 獲取使用者/群資訊 | `Api` | `adapter.Api.get_user_info("123")` |
| 撤回訊息 | `Api` | `adapter.Api.delete_message("msg_id")` |
| 退出群 | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. 適配器實作檢查清單

### 標準動作
- [ ] `call_api` 能處理標準動作名（或覆蓋對應 `ApiDSL` 方法）
- [ ] 不支援的動作回傳 `retcode=10002`
- [ ] 回傳值遵循標準 API 回應格式
- [ ] `data` 字段包含 OB12 標準定義的字段
- [ ] 頻道平台需實作 `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] 元動作（`get_status` / `get_version` / `get_supported_actions`）建議實作
- [ ] **檔案收發用 `SendDSL.File`（直傳）**；檔案資源動作（upload_file/get_file/分片）**不強制實作**，僅當後端具備 `file_id` 資源能力時才需透傳

### 擴展動作
- [ ] 平台擴展動作使用 `{prefix}.{action}` 命名
- [ ] 擴展動作的參數和回應仍遵循 OB12 動作請求/回應結構

## 9. 相關文件

- [API 回應標準](api-response.md) - 適配器 API 回應格式標準
- [發送方法規範](send-method-spec.md) - Send 類的方法命名和參數規範
- [請求操作規範](request-action-spec.md) - Request DSL 的使用方式
- [事件轉換標準](event-conversion.md) - 事件格式和訊息段標準