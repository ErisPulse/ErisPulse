# ErisPulse 請求操作規範

> [!TIP]
> **什麼時候需要讀這篇**：當你的適配器需要處理好友請求/群邀請（轉換請求事件、實現 `accept`/`reject`，含異構端點的請求類型上下文留存），或模組中要用 `event.approve()` / `event.reject()` 審批請求時對照本文。不需要則跳過。

本文件定義了 ErisPulse 適配器中請求事件操作的標準化規範，包括請求事件的欄位要求、Request DSL 的使用方式和適配器實現要求。

## 1. 概述

請求事件（`type: "request"`）是 OneBot12 標準中定義的特殊事件類型，代表需要 Bot 做出決策的請求（如好友請求、群邀請等）。

與訊息事件不同，請求事件需要**雙向互動**：
1. **接收**：適配器將平台原生請求轉換為標準請求事件
2. **回應**：模組透過 `Request` DSL 或 `Event.approve()`/`Event.reject()` 執行操作

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
    └─→ 或直接透過適配器操作
            await adapter.Request("req_id").accept()
```

## 2. 請求事件欄位要求

### 2.1 標準欄位

請求事件除必須包含 OneBot12 標準欄位外，還需包含以下欄位：

| 欄位 | 類型 | 必選 | 說明 |
|------|------|------|------|
| `request_id` | string | **強烈推薦** | 請求識別符，用於同意/拒絕操作 |
| `user_id` | string | 是 | 請求發起者ID |
| `user_nickname` | string | 否 | 請求發起者暱稱 |
| `comment` | string | 否 | 請求附言 |

### 2.2 `request_id` 欄位

`request_id` 是請求操作的核心識別符：

- **用途**：標識一個可操作的請求，供 `Request` DSL 使用
- **生成規則**：
  - 優先使用平台原生的請求標識（如 OneBot11 的 `flag` 欄位、Telegram 的 `chat_invite_link` 等）
  - 如果平台沒有原生請求ID，適配器應生成一個唯一標識（建議格式：`{platform}_{timestamp}_{user_id}`）
- **唯一性**：在同一平台範圍內應保持唯一
- **缺失行為**：當 `request_id` 缺失時，`event.approve()` / `event.reject()` 將拋出 `ValueError`

### 2.3 請求事件範例

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

### 3.1 鏈式調用

`Request` 提供與 `Send` 風格一致的鏈式調用介面：

```python
# 基本用法
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# 指定 Bot 帳號
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
| `Using(account_id)` | 指定執行操作的 Bot 帳號 | `RequestDSL`（支援鏈式調用） |
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

**未實現**（適配器未重寫 `_do_accept`/`_do_reject`）：
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

| 方法 | 說明 | 返回值 |
|------|------|--------|
| `get_request_id()` | 獲取請求ID | `str` |
| `approve(comment=None)` | 同意當前請求事件 | 標準回應格式 |
| `reject(comment=None)` | 拒絕當前請求事件 | 標準回應格式 |

## 5. 適配器實現要求

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
    
    優先使用平台原生的請求標識，若無則生成唯一ID
    """
    # 優先使用平台原生ID
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

基類的 `accept()` / `reject()` 是公開入口：內建 scope 授權閘口（`scope.actions.<owner>.request`，禁用時直接返回 34601 拒絕回應）與任務包裝，**適配器不要重寫公開入口**——重寫會繞過授權閘口。適配器重寫 `_do_accept` / `_do_reject`（非同步方法，直接返回標準回應 dict）。

> **多帳戶提醒**：`_do_accept` / `_do_reject` 內是適配器自己調 `call_api`，帳戶不會自動注入——帳戶經 `self.request_context.get("account_id")` 獲取（`Using()` 顯式指定 > 事件鏈自動綁定，與 Send 的 `send_context` 同口徑），並作為 `account_id` 參數傳給 `call_api`，否則多帳戶部署下會落到預設帳戶。

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform 請求操作實現"""
        
        async def _do_accept(self, **kwargs) -> dict:
            """
            同意請求
            
            :param kwargs: 擴充參數，如 comment="備註"
            :return: 標準回應格式 dict
            """
            try:
                result = await self._adapter.call_api(
                    endpoint="/set_request",
                    request_id=self._request_id,
                    account_id=self.request_context.get("account_id"),
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
        
        async def _do_reject(self, **kwargs) -> dict:
            """拒絕請求（與 _do_accept 同構：approve=False）"""
```

### 5.3 請求類型上下文留存（異構端點適配器必須）

#### 5.3.1 契約缺口

`Request` DSL 是無狀態句柄：調用方只持 `request_id`（[§3](#3-request-dsl)），請求類型不在調用參數裡。而不少平台的同意/拒絕端點是**異構**的——以 OneBot11 系為例：

| 請求類型 | 端點 |
|---|---|
| 好友添加 | `set_friend_add_request(flag, approve)` |
| 群申請 / 群邀請 | `set_group_add_request(flag, sub_type, approve)`，`sub_type ∈ {"add", "invite"}` |

調用方只知道 `request_id`，端點選擇卻需要類型。這段上下文只可能由適配器補齊：請求事件本就是適配器接收並轉換的（類型資訊在轉換時就在手上），且一個 `request_id` 對應的請求類型不會變。適配器若不自行留存，只能猜測端點或依賴調用方傳非標準參數——典型故障形態是**群邀請被送進好友端點**，flag 被協議端按 user_id 解析而報錯。

#### 5.3.2 規範要求

平台端點異構（同意/拒絕需要按請求類型路由）的適配器，`accept` / `reject` 實現必須滿足：

1. **事件側留存**：適配器收到請求事件的入口處，把 `request_id → {請求類型, sub_type, group_id, 帳戶}` 寫入實例內快取（統一欄位見 §5.3.3），並順手清理過期條目
2. **操作側路由**：`_do_accept` / `_do_reject` 內的端點選擇順序為 **kwargs 顯式傳參 > 快取 > 回退預設端點並記 WARNING**——類型未知必須打日誌（可觀測），不得靜默選端點
3. **kwargs 保留名**：顯式覆蓋參數統一命名 `request_type` / `sub_type` / `group_id`（無底線前綴、跨適配器同名同義）；不使用 `_request_type` 一類私有約定名（標準調用方不會傳）
4. **帳戶讀取與歸屬校驗**：操作帳戶統一經基類屬性 `self.request_context.get("account_id")` 獲取（`Using()` 顯式指定 > 事件鏈自動綁定，與 Send 的 `send_context` 同口徑）；留存條目的事件到達帳戶作為事件鏈缺失時的兜底（如輪詢合成事件、跨重啟重建）。**帳戶無法解析到具體帳戶實例時必須快速失敗**（返回 34005），不得靜默回退預設帳戶——回退會把操作打到錯誤連線（flag 在預設帳戶會話不存在，平台報 invalid，多帳戶下表現為「只有第一個帳戶能操作」）
5. **預設持久化**：留存介質預設為框架統一儲存（`self.sdk.storage`）**單鍵整快照**——請求為低頻批覆類事件，事件到達時即寫透（庫內足跡恆為 1 個鍵）；啟動時一次載入回記憶體，執行時讀路徑零開銷；儲存不可用時降級僅記憶體（WARNING），不阻斷事件流
6. **處理後清理**：操作提交成功後刪除該 `request_id` 條目並同步寫透快照

單一請求端點的平台（如統一 `/set_request`）無需留存，透傳即可。本節是適配器實現口徑，`Request` DSL 契約不受影響。

#### 5.3.3 統一條目欄位（介質無關）

上下文條目按以下統一欄位形狀留存。**欄位形狀是互操作契約**：記憶體 dict、KV value、ORM 行均按同一形狀落存，後續跨適配器聚合或遷移時形狀一致；儲存介質自選，不因介質改變欄位語義。

| 欄位 | 類型 | 必含 | 語義與來源 |
|---|---|---|---|
| `request_type` | `str` | 是 | 請求類型，取自事件 `detail_type`（`"friend"` / `"group"`） |
| `sub_type` | `str \| None` | 群請求必含 | 群請求子類型 `"add"` / `"invite"`，取自平台原生事件（OB11 系 `sub_type`） |
| `group_id` | `str \| None` | 群請求必含 | 目標群 ID，取自平台原生事件 |
| `account` | `str \| None` | 多帳戶必含 | 事件到達帳戶，取自事件 `self.user_id` |
| `ts` | `float` | 是 | 事件到達 Unix 時間戳（秒），TTL 判定基準 |

條目一致性規則：

- **一一對應**：一個 `request_id` 至多對應一個條目；同 `request_id` 的重複事件覆蓋寫入（冪等）
- **處理後刪除**：操作提交成功即刪除條目
- **TTL**：以 `ts` 為基準，建議 1 小時級（覆蓋平台側請求有效期）；過期視同未留存，走回退預設端點 + WARNING
- **鍵名（KV 持久化時）**：`{適配器配置鍵}:request_ctx:{request_id}`，避免跨適配器衝突

#### 5.3.4 參考實現（統一儲存單鍵快照，預設）

留存介質**預設為框架統一儲存**（`self.sdk.storage`）：請求事件是批覆類低頻事件（好友/群請求，非訊息流），**事件到達時即寫透**不會造成寫入壓力。儲存形式為**單鍵整快照**——整個上下文字典作為一個鍵一次寫入（庫內足跡恆為 1 個鍵，隨處理自動收斂），不做逐 flag 分鍵。重啟後啟動時一次載入回記憶體，執行時讀路徑零開銷。

```python
import time

from ErisPulse.Core import BaseAdapter, RequestDSL


class MyAdapter(BaseAdapter):
    """請求端點異構平台（好友與群請求分端點）"""

    _REQ_CTX_TTL = 86400   # 留存秒數（覆蓋平台側 flag 有效期，重啟不丟）
    _REQ_CTX_MAX = 512     # 條目容量上限

    def __init__(self, sdk=None):
        super().__init__(sdk)
        self._request_ctx: dict[str, dict] = {}   # request_id → 請求上下文（記憶體態）
        self._ctx_key = f"{self._get_config_key()}:request_ctx"   # 單鍵整快照

    async def start(self):
        # 啟動載入（重啟後仍可審批）；儲存不可用按冷啟動處理
        try:
            loaded = self.sdk.storage.get(self._ctx_key, {}) or {}
            now = time.time()
            self._request_ctx = {k: v for k, v in loaded.items()
                                 if now - v.get("ts", 0) <= self._REQ_CTX_TTL}
        except Exception as e:
            self.logger.warning(f"請求上下文載入失敗（按冷啟動處理）: {e}")
            self._request_ctx = {}

    def _persist_ctx(self) -> None:
        """單鍵整快照寫透（儲存不可用時降級僅記憶體，不阻斷事件流）"""
        try:
            self.sdk.storage.set(self._ctx_key, self._request_ctx)
        except Exception as e:
            self.logger.warning(f"請求上下文寫透失敗（降級僅記憶體）: {e}")

    def remember_request(self, request_id: str, *, request_type: str,
                         sub_type: str | None = None, group_id: str | None = None,
                         account: str | None = None) -> None:
        """事件側留存請求上下文（適配器收到請求事件的入口處調用）"""
        now = time.time()
        expired = [k for k, c in self._request_ctx.items() if now - c["ts"] > self._REQ_CTX_TTL]
        for k in expired:
            self._request_ctx.pop(k)
        while len(self._request_ctx) >= self._REQ_CTX_MAX:
            self._request_ctx.pop(min(self._request_ctx, key=lambda k: self._request_ctx[k]["ts"]))
        self._request_ctx[request_id] = {
            "request_type": request_type,   # "friend" / "group"
            "sub_type": sub_type,           # 群請求子類型："add" / "invite"
            "group_id": group_id,
            "account": account,             # 事件到達帳戶（事件的 self.user_id / 代位帳戶名）
            "ts": now,
        }
        self._persist_ctx()

    class Request(RequestDSL):
        """端點路由：kwargs 顯式傳參 > 快取 > 回退預設端點 + WARNING"""

        def _route(self, **kwargs) -> dict:
            ctx = {k: kwargs[k] for k in ("request_type", "sub_type", "group_id") if kwargs.get(k)}
            cached = self._adapter._request_ctx.get(self._request_id, {})
            if not ctx.get("request_type"):
                ctx.update({k: v for k, v in cached.items()
                            if k in ("request_type", "sub_type", "group_id") and v})
                ctx.setdefault("account", cached.get("account"))
            if not ctx.get("request_type"):
                self._adapter.logger.warning(f"請求 {self._request_id} 類型未知，按好友端點回退")
                ctx["request_type"] = "friend"
            return ctx

        def _resolve_or_fail(self, account):
            """
            審批帳戶歸屬校驗：解析失敗快速失敗（34005），不回退預設帳戶。

            回退預設帳戶會把操作打到錯誤連線上（flag 在該帳戶會話不存在，
            平台報 invalid，表現為「只有第一個帳戶能操作」的玄學故障）。
            """
            if not account:
                return None, None            # 無任何帳戶資訊時維持預設帳戶語義
            name, inst = self._adapter._resolve_account(account)
            hit = str(account) == str(name) or str(account) == str(getattr(inst, "bot_id", "") or "")
            if not hit:
                self._adapter.logger.warning(
                    f"請求 {self._request_id} 的帳戶 {account} 無法解析，拒絕回退預設帳戶")
                return None, "34005"
            return (name, inst), None

        async def _do_accept(self, **kwargs) -> dict:
            """同意請求；kwargs 類型路由可用 request_type / sub_type / group_id 顯式覆蓋"""
            return await self._do_action(approve=True, **kwargs)

        async def _do_reject(self, **kwargs) -> dict:
            """拒絕請求（與 _do_accept 同構：approve=False）"""
            return await self._do_action(approve=False, **kwargs)

        async def _do_action(self, approve: bool, **kwargs) -> dict:
            ctx = self._route(**kwargs)
            account = self.request_context.get("account_id") or ctx.get("account")
            resolved, fail = self._resolve_or_fail(account)
            if fail:
                return {
                    "status": "failed", "retcode": 34005, "data": None,
                    "message_id": "", "message": f"請求帳戶 {account} 無法解析到帳戶實例",
                }
            try:
                if ctx["request_type"] == "group":
                    result = await self._adapter.call_api(
                        endpoint="/set_group_add_request",
                        flag=self._request_id,
                        sub_type=ctx.get("sub_type") or "add",
                        approve=approve,
                        account_id=account,
                    )
                else:
                    result = await self._adapter.call_api(
                        endpoint="/set_friend_add_request",
                        flag=self._request_id,
                        approve=approve,
                        account_id=account,
                    )
                response = {
                    "status": "ok" if result.get("code") == 0 else "failed",
                    "retcode": result.get("code", 0),
                    "data": None,
                    "message_id": "",
                    "message": result.get("message", ""),
                }
            except Exception as e:
                response = {
                    "status": "failed", "retcode": 34001, "data": None,
                    "message_id": "", "message": f"請求操作失敗: {e}",
                }
            if response["status"] == "ok":
                self._adapter._request_ctx.pop(self._request_id, None)   # 處理後清理
                self._adapter._persist_ctx()
            return response
```

#### 5.3.5 邊界與降級

**降級語義**：統一儲存不可用（連線失敗冷卻期 fast-fail）時寫透降級為僅記憶體（WARNING 可觀測），事件照常分發；重啟後條目丟失走「類型未知回退 + WARNING」路徑。

**等價介質**：內建 ORM（`request_id` 主鍵建表，見 [資料模型層](../developer-guide/orm.md)）語義等價，適配器可按需選用；不引入額外檔案或新依賴。

**多實例邊界**：本規範不覆蓋多進程實例協同——ErisPulse 為單進程多 bot 模型（多帳戶同進程，請求與其所屬帳戶天然同側），統一儲存即滿足重啟語義；跨實例共享（多進程分攤帳戶）需要時再行立項。

### 5.4 平台不支援請求操作

如果平台本身不支援好友請求/群邀請操作（如某些平台自動處理請求），適配器可以：

1. **不重寫 `Request` 內部類**：使用基類預設實現，調用 `accept()`/`reject()` 時返回 `retcode=10002`
2. **在轉換時跳過 `request_id`**：不生成 `request_id`，讓 `event.approve()` 拋出 `ValueError`
3. **記錄日誌**：在 `_do_accept` / `_do_reject` 中記錄警告並返回適當錯誤碼

### 5.5 總結：Send 與 Request 並行

適配器有兩個並行的 DSL 內部類，各司其職：

```
BaseAdapter
├── Send(SendDSL)     ← 訊息發送
│   ├── Raw_ob12()    ← 必須實現
│   ├── Text()        ← 推薦實現
│   └── Image()       ← 按需實現
│
└── Request(RequestDSL) ← 請求操作
    ├── accept()        ← 公開入口（scope 閘口 + 任務包裝，勿重寫）
    ├── reject()        ← 公開入口（同上）
    ├── _do_accept()    ← 按需重寫
    └── _do_reject()    ← 按需重寫
```

### 5.6 適配器 `__init__` 注意事項

重寫 `Request` 內部類的 `__init__` 時，必須透傳參數並調用 `super().__init__()`，詳見 [適配器開發入門 - `__init__` 注意事項](../developer-guide/adapters/getting-started.md#init-注意事項)（`Request` 同理，參數為 `adapter, request_id, account_id`）。

## 6. 適配器實現檢查清單

### 基礎要求
- [ ] 若重寫了 `__init__`，已調用 `super().__init__()`（確保 Send / Request 工廠初始化）

### 請求事件轉換
- [ ] 請求事件包含 `request_id` 欄位（強烈推薦）
- [ ] `detail_type` 正確映射為 `"friend"` 或 `"group"`
- [ ] 保留平台原始資料在 `{platform}_raw` 欄位中
- [ ] `request_id` 生成規則有文件說明

### 請求操作
- [ ] `Request` 內部類已實現（如平台支援請求操作）
- [ ] `_do_accept()` / `_do_reject()` 已重寫（公開入口 `accept()` / `reject()` 勿重寫——繞過 scope 授權閘口）
- [ ] 操作返回標準 API 回應格式
- [ ] 不支援的操作返回 `retcode=10002`
- [ ] 網路錯誤返回 `retcode=33xxx`（遵循 API 回應標準）

### 請求類型上下文留存（異構端點平台，見 §5.3）
- [ ] 請求事件入口已留存 `request_id → {請求類型, sub_type, group_id, 帳戶}` 上下文
- [ ] 條目欄位與 §5.3.3 統一欄位表一致（含 `ts` 時間戳；`request_id` 一一對應、處理後刪除）
- [ ] `accept` / `reject` 端點路由順序為 kwargs 顯式傳參 > 快取 > 回退預設端點 + WARNING
- [ ] 類型覆蓋參數使用保留名 `request_type` / `sub_type` / `group_id`（無 `_request_type` 一類私有約定名）
- [ ] 快取有 TTL 與容量上限，操作提交成功後清理對應條目
- [ ] 多帳戶：操作帳戶經 `self.request_context.get("account_id")` 讀取（`Using()` > 事件鏈兜底），留存帳戶作事件鏈缺失時兜底
- [ ] 審批帳戶解析失敗快速失敗（34005），不回退預設帳戶
- [ ] 預設統一儲存單鍵快照：啟動載入、事件到達/處理後寫透、儲存不可用降級僅記憶體

## 7. 錯誤碼擴展

請求操作相關的**適配器實現層**推薦錯誤碼（遵循 [API 回應標準](api-response.md) §3.2，
落在 `34xxx` 平台錯誤段的低三位自定義）：

| 錯誤碼 | 錯誤名 | 說明 |
|-------|-------|------|
| 34001 | Request Not Found | 請求不存在或已過期 |
| 34002 | Request Already Handled | 請求已被處理 |
| 34003 | Request Not Supported | 平台不支援該類型的請求操作 |
| 34004 | Permission Denied | Bot 無權處理此請求（平台返回） |
| 34005 | Request Account Unresolved | 請求所屬帳戶無法解析到帳戶實例（快速失敗，不回退預設帳戶） |

> **與框架碼的邊界**：以上 `340xx` 是**平台/適配器**返回的請求處理失敗；
> ErisPulse 框架在 `scope.actions` 禁用某模組的 request 動作時，**在調用適配器之前**
> 直接返回 `34601`（Action Denied，見 [API 回應標準 §5.3](api-response.md#53-框架擴展返回碼34xxx-平台錯誤段的低三位自定義)），
> 兩者互不替代：先過 `34601` 框架閘口，再落到平台層 `340xx` 錯誤。

## 8. 相關文件

**實現請求操作時配套對照**：
- [事件轉換標準](event-conversion.md) - 完整的事件轉換規範（含 `request_id` 欄位要求）
- [API 回應標準](api-response.md) - 適配器 API 回應格式標準（操作返回值與錯誤碼）
- [儲存後端](../advanced/storage-backends.md) - 需要跨重啟留存請求上下文時的統一 KV 儲存

**同一適配器的其它 DSL**：
- [發送方法規範](send-method-spec.md) - Send 類的方法命名和參數規範
- [會話類型標準](session-types.md) - 會話類型定義和映射關係