# 介接器核心概念

了解 ErisPulse 介接器的核心概念是開發介接器的基礎。

## 介接器架構

### 組件關係

```
正向轉換（接收方向）                           反向轉換（發送方向）
─────────────────                           ─────────────────
                                             
┌──────────────────┐                        ┌──────────────────┐
│ 平台原生事件     │                        │ 模組建構訊息     │
└────────┬─────────┘                        └────────┬─────────┘
         │                                           │
         ↓                                           ↓
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│                  │   │ 介接器 (MyAdapter) │   │                  │
│  Converter       │   │ ┌──────────────┐ │   │ Send.Raw_ob12()  │
│  (事件轉換器)    │──→│ │              │ │   │ (反向轉換入口)   │
│                  │   │ │              │ │   │                  │
└──────────────────┘   │ └──────────────┘ │   └────────┬─────────┘
                       └──────────────────┘            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 平台 API 呼叫    │
                       │ OneBot12 標準事件 │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準響應格式     │
                       │ 事件系統         │    └──────────────────┘
                       └────────┬─────────┘
                                │
                                ↓
                       ┌──────────────────┐
                       │ 模組 (處理事件)  │
                       └──────────────────┘
```

**核心對稱性**：
- **正向轉換**（Converter）：平台原生事件 → OneBot12 標準事件，原始資料保留在 `{platform}_raw`
- **反向轉換**（Raw_ob12）：OneBot12 訊息段 → 平台 API 呼叫，返回標準響應格式

## AdapterManager 介接器管理器

`AdapterManager` 是 ErisPulse 介接器系統的核心組件，負責管理所有平台介接器的註冊、啟動、關閉和事件分發。

### 核心功能

- **介接器註冊**：註冊和管理多個平台介接器
- **生命週期管理**：控制介接器的啟動和關閉
- **事件分發**：分發 OneBot12 標準事件和平台原生事件
- **設定管理**：管理介接器的啟用/停用狀態
- **中介軟體支援**：支援 OneBot12 事件中介軟體

### 基本使用

```python
from ErisPulse import sdk

# 註冊介接器（通常由 Loader 自動完成）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# 啟動所有介接器
await sdk.adapter.startup()

# 啟動指定介接器
await sdk.adapter.startup(["myplatform"])
# 啟動全部介接器
await sdk.adapter.startup()

# 取得介接器實例
my_adapter = sdk.adapter.get("myplatform")
# 或透過屬性存取
my_adapter = sdk.adapter.myplatform

# 關閉所有介接器
await sdk.adapter.shutdown()
```

### 啟動和關閉

#### 啟動介接器

```python
# 啟動所有已註冊的介接器
await sdk.adapter.startup()

# 啟動指定平台
await sdk.adapter.startup(["platform1", "platform2"])
```

**啟動流程：**

1. 提交 `adapter.start` 生命週期事件
2. 提交 `adapter.status.change` 事件（starting）
3. 並行啟動各個介接器
4. 如果啟動失敗，自動重試（指數退避策略）
5. 啟動成功後提交 `adapter.status.change` 事件（started）

**重試機制：**

- 前 4 次重試：60秒、10分鐘、30分鐘、60分鐘
- 第 5 次及以後：3 小時固定間隔

#### 關閉介接器

```python
# 關閉所有介接器
await sdk.adapter.shutdown()
```

**關閉流程：**

1. 提交 `adapter.stop` 生命週期事件
2. 呼叫所有介接器的 `shutdown()` 方法
3. 關閉路由伺服器
4. 清空事件處理器
5. 提交 `adapter.stopped` 生命週期事件

### 設定管理

#### 檢查平台狀態

```python
# 檢查平台是否已註冊
exists = sdk.adapter.exists("myplatform")

# 檢查平台是否啟用
enabled = sdk.adapter.is_enabled("myplatform")

# 使用 in 運算子
if "myplatform" in sdk.adapter:
    print("平台存在且已啟用")
```

#### 列出平台

```python
# 列出所有已註冊的平台
platforms = sdk.adapter.list_registered()

# 列出所有平台及其狀態
status_dict = sdk.adapter.list_items()
# 傳回: {"platform1": true, "platform2": false, ...}

# 取得已啟用的平台列表
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### 事件監聽

#### OneBot12 標準事件

```python
from ErisPulse import sdk

# 監聽所有平台的標準訊息事件
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"收到 OneBot12 訊息: {data}")

# 監聽特定平台的標準訊息事件
@sdk.adapter.on("message", platform="myplatform")
async def handle_platform_message(data):
    print(f"收到 myplatform 訊息: {data}")

# 監聽所有事件
@sdk.adapter.on("*")
async def handle_any_event(data):
    print(f"收到事件: {data.get('type')}")
```

#### 平台原生事件

```python
# 監聽特定平台的原生事件
@sdk.adapter.on("raw_event_type", raw=True, platform="myplatform")
async def handle_raw_event(data):
    print(f"收到原生事件: {data}")

# 監聽所有平台的原生事件（萬用字元）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"收到原生事件: {data}")
```

#### 事件分發機制

當呼叫 `adapter.emit(event_data)` 時：

1. **中介軟體處理**：先執行所有 OneBot12 中介軟體
2. **標準事件分發**：分發到匹配的 OneBot12 事件處理器
3. **原生事件分發**：如果存在原始資料，分發到原生事件處理器

**匹配規則：**

- 精確匹配：`@sdk.adapter.on("message")` 只匹配 `message` 事件
- 萬用字元：`@sdk.adapter.on("*")` 匹配所有事件
- 平台過濾：`platform="myplatform"` 只分發指定平台的事件

### 中介軟體

#### 新增中介軟體

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """日誌記錄中介軟體"""
    print(f"處理事件: {data.get('type')}")
    return data  # 必須傳回資料

@sdk.adapter.middleware
async def filter_middleware(data):
    """事件過濾中介軟體"""
    # 過濾不需要的事件
    if data.get("type") == "notice":
        return None  # 傳回 None 時中介軟體鏈會忽略該返回值，保留原資料繼續傳遞
    return data  # 必須傳回資料以繼續傳遞
```

#### 中介軟體執行順序

中介軟體按照註冊順序執行，後註冊的中介軟體先執行。

> **注意**：如果中介軟體返回 `None`（例如忘記 `return data`），框架會忽略該返回值並保留原資料繼續傳遞，同時輸出 warning 級別日誌。這確保了單個中介軟體的失誤不會導致整個事件鏈中斷。

```python
# 註冊順序
sdk.adapter.middleware(middleware1)  # 最後執行
sdk.adapter.middleware(middleware2)  # 中間執行
sdk.adapter.middleware(middleware3)  # 最先執行

# 執行順序：middleware3 -> middleware2 -> middleware1
```

### 取得介接器實例

#### get() 方法

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### 屬性存取

```python
# 透過屬性名稱存取（不區分大小寫）
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter 基類

### 基本結構

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.runtime.config_schema import AdapterConfig, BotAccountConfig

@dataclass
class MyConfig(AdapterConfig):
    """介接器設定（宣告後框架自動管理）"""
    token: str = field(
        default="",
        metadata={
            "description": "Bot Token",
            "required": True,
            "secret": True,
            "webui": {"widget": "password", "group": "basic", "order": 1},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig  # 宣告設定類
    
    # 無需覆寫 __init__，框架自動處理：
    # - self.sdk, self.logger
    # - self.config（類型安全的設定實例）
    # - self.Send, self.Request
    
    async def start(self):
        """啟動介接器（必須實作）"""
        cfg = self.config  # 自動載入的類型安全設定
        pass
    
    async def shutdown(self):
        """關閉介接器（必須實作）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """呼叫平台 API（必須實作）"""
        pass
```

### 設定管理

框架提供了宣告式設定管理，透過 dataclass 定義設定結構，框架自動處理載入、校驗和範本生成。

#### 單帳戶設定

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import AdapterConfig

@dataclass
class TelegramConfig(AdapterConfig):
    token: str = field(default="", metadata={
        "description": "Bot Token",
        "required": True,
        "secret": True,
        "webui": {"widget": "password", "group": "basic", "order": 1},
    })
    proxy: str = field(default="", metadata={
        "description": "代理位址",
        "webui": {"widget": "text", "group": "advanced", "order": 10},
    })

class TelegramAdapter(BaseAdapter):
    ConfigClass = TelegramConfig
    
    async def start(self):
        cfg = self.config  # 類型安全，自動載入
        if not cfg.token:
            raise ValueError("未設定 Token")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 多帳戶設定

```python
from ErisPulse.runtime.config_schema import BotAccountConfig

@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": "機器人ID",
        "required": True,
        "webui": {"widget": "text", "group": "basic", "order": 1},
    })
    token: str = field(default="", metadata={
        "description": "機器人Token",
        "required": True,
        "secret": True,
        "webui": {"widget": "password", "group": "basic", "order": 2},
    })

class YunhuAdapter(BaseAdapter):
    AccountConfigClass = YunhuBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            await self._connect(name, account)
            await self.emit_meta("connect", account.bot_id, user_name=account.name)
```

#### metadata 約定

欄位 metadata 同時服務於 TOML 註釋生成和 WebUI 表單渲染：

```python
metadata = {
    "description": str,       # 欄位描述（TOML註釋 + WebUI label）
    "required": bool,         # 是否必填（校驗 + WebUI 必填標記）
    "secret": bool,           # 是否敏感（WebUI 顯示為 ***，日誌中脫敏）
    "webui": {
        "widget": str,        # 控件類型: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # 分組: "basic" | "advanced" | "connection" 等
        "order": int,         # 排序權重（越小越靠前）
        "options": list,      # select 控件的可選項 [{label, value}]
        "placeholder": str,   # 輸入框佔位符
    }
}
```

#### 帳戶解析

多帳戶介接器可使用 `_resolve_account()` 自動解析目標帳戶：

```python
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
    # name: 帳戶名, account: 設定實例
```

解析策略：帳戶名匹配 → `bot_id` 欄位匹配 → 其他 str 欄位匹配 → 第一個啟用帳戶。

#### 設定熱更新

子類可覆寫 `on_config_update()` 回應設定變更：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token 已更新，將重新連接")
```

### 初始化過程

框架在 `BaseAdapter.__init__(self, sdk=None)` 中自動完成以下工作：

1. **SDK 引用**：設定 `self.sdk`、`self.logger`
2. **Send/Request 工廠**：建立 `self.Send` 和 `self.Request`
3. **設定載入**：如果宣告了 `ConfigClass`，自動載入到 `self.config`
4. **帳戶載入**：如果宣告了 `AccountConfigClass`，自動載入到 `self.accounts`

大多數介接器無需覆寫 `__init__`。如需自訂初始化：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # 傳入 sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send 訊息發送 DSL

### 繼承關係

```python
class MyAdapter(BaseAdapter):
    class Send(BaseAdapter.Send):
        """Send 嵌套類，繼承自 BaseAdapter.Send"""
        pass
```

### 可用屬性

`Send` 類在呼叫時會自動設定以下屬性：

| 屬性 | 說明 | 設定方式 |
|-----|------|---------|
| `_target_id` | 目標ID | `To(id)` 或 `To(type, id)` |
| `_target_type` | 目標類型 | `To(type, id)` |
| `_target_to` | 簡化目標ID | `To(id)` |
| `_account_id` | 發送帳號ID | `Using(account_id)` |
| `_adapter` | 介接器實例 | 自動設定 |
| `_at_user_ids` | @用戶列表 | `At(user_id)` |
| `_reply_message_id` | 回覆的訊息ID | `Reply(message_id)` |
| `_at_all` | 是否@全體 | `AtAll()` |

> **推薦**：使用 `self.send_context` 屬性一次性取得 `target_type`、`target_id`、`account_id`，比直接存取實例變數更清晰。

### 框架輔助方法

| 方法/屬性 | 說明 |
|-----------|------|
| `self._apply_modifiers(message)` | 將 At/AtAll/Reply 修飾器狀態合併到訊息段列表 |
| `self.send_context` | 傳回 `{target_type, target_id, account_id}` 字典 |

### 基本方法

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """推薦實作方式"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    def Text(self, text: str):
        """發送文字訊息"""
        return self.Raw_ob12([
            {"type": "text", "data": {"text": text}}
        ])
```

### 鏈式修飾方法

```python
class Send(BaseAdapter.Send):

    def __init__(self, adapter, target_type=None, target_id=None, account_id=None):
        super().__init__(adapter, target_type, target_id, account_id)
        self.buttons = []

    def Button(self, content: list) -> 'Send':
        self.buttons.append(content)
        return self
```

## 事件轉換器

### 轉換流程

```
平台原始事件
    ↓
Converter.convert()
    ↓
OneBot12 標準事件
```

### 必需欄位

所有轉換後的事件必須包含：

```python
{
    "id": "事件唯一識別",
    "time": 1234567890,           # 10位 Unix 時間戳
    "type": "message/notice/request/meta",
    "detail_type": "事件詳細類型",
    "platform": "平台名稱",
    "self": {
        "platform": "平台名稱",
        "user_id": "機器人ID"
    },
    "{platform}_raw": {...},       # 原始資料（必須）
    "{platform}_raw_type": "..."    # 原始類型（必須）
}
```

### 轉換器示例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """將平台原生事件轉換為 OneBot12 標準格式"""
        if not isinstance(raw_event, dict):
            return None
        
        # 生成事件 ID
        event_id = raw_event.get("event_id") or str(uuid.uuid4())
        
        # 轉換時間戳
        timestamp = raw_event.get("timestamp")
        if timestamp and timestamp > 10**12:
            timestamp = int(timestamp / 1000)
        else:
            timestamp = int(timestamp) if timestamp else int(time.time())
        
        # 轉換事件類型
        event_type = self._convert_type(raw_event.get("type"))
        detail_type = self._convert_detail_type(raw_event)
        
        # 建構標準事件
        onebot_event = {
            "id": str(event_id),
            "time": timestamp,
            "type": event_type,
            "detail_type": detail_type,
            "platform": "myplatform",
            "self": {
                "platform": "myplatform",
                "user_id": str(raw_event.get("bot_id", ""))
            },
            "myplatform_raw": raw_event,
            "myplatform_raw_type": raw_event.get("type", "")
        }
        
        return onebot_event
```

## 連接管理

### WebSocket 連接

```python
from fastapi import WebSocket

class MyAdapter(BaseAdapter):
    async def start(self):
        """註冊 WebSocket 路由"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket: WebSocket):
        """WebSocket 連接處理器"""
        self.connection = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                onebot_event = self.convert(data)
                if onebot_event:
                    await self.adapter.emit(onebot_event)
        except WebSocketDisconnect:
            self.logger.info("連接已斷開")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket: WebSocket) -> bool:
        """WebSocket 認證"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook 連接

```python
from fastapi import Request

class MyAdapter(BaseAdapter):
    async def start(self):
        """註冊 WebHook 路由"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request: Request):
        """WebHook 請求處理器"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

## API 回應標準

框架提供 `make_response()` 和 `make_error()` 方法建構標準化回應，無需手動建構回應字典。

### 成功回應

```python
async def call_api(self, endpoint: str, **params):
    try:
        raw_response = await self._platform_api_call(endpoint, **params)
        
        return self.make_response(
            data=raw_response.get("data"),
            message_id=raw_response.get("data", {}).get("message_id", ""),
            raw=raw_response,
        )
    except Exception as e:
        return self.make_error(message=str(e), raw=None)
```

### 手動建構回應（舊版方式仍然相容）

```python
async def call_api(self, endpoint: str, **params):
    return {
        "status": "ok",
        "retcode": 0,
        "data": {...},
        "message_id": "msg_id",
        "message": "",
        "myplatform_raw": raw_response
    }
```

## 多帳戶支援

### 宣告式設定（推薦）

使用 `AccountConfigClass` 宣告設定類後，框架自動管理多帳戶載入、校驗和範本生成：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BotAccountConfig

@dataclass
class MyBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={"description": "Bot ID", "required": True})
    token: str = field(default="", metadata={"description": "Token", "required": True, "secret": True})

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            self.logger.info(f"啟動帳戶 {name}: {account.bot_id}")
            await self._connect(name, account)
    
    async def call_api(self, endpoint: str, **params):
        account_id = params.pop("account_id", None)
        name, account = self._resolve_account(account_id)
        # 使用 account.token, account.bot_id 等欄位
```

### 帳戶設定檔

```toml
[MyAdapter.accounts.account1]
bot_id = "bot_001"
token = "token1"
enabled = true

[MyAdapter.accounts.account2]
bot_id = "bot_002"
token = "token2"
enabled = true
```

### 指定帳戶發送

```python
# 使用 Using 方法指定帳戶
my_adapter = adapter.get("myplatform")

# 透過帳戶名
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")

# 透過帳戶 ID
await my_adapter.Send.Using("account_id").To("user", "123").Text("Hello")
```

## 錯誤處理

### 連接重試

```python
import asyncio

class MyAdapter(BaseAdapter):
    async def start(self):
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                await self._connect_to_platform()
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = min(60 * (2 ** retry_count), 600)
                    self.logger.warning(f"連接失敗，{wait_time}秒後重試")
                    await asyncio.sleep(wait_time)
                else:
                    raise
```

### API 錯誤處理

```python
async def call_api(self, endpoint: str, **params):
    try:
        # 推薦使用 SDK 內建客戶端
        from ErisPulse.Core import client
        from ErisPulse.Core.Bases.errors import ClientError, ClientTimeoutError
        resp = await client.post(
            f"https://api.platform.com/{endpoint}",
            json=params,
            max_retries=2,
        )
        response = await resp.json()
        return self._standardize_response(response)
    except ClientTimeoutError:
        self.logger.error(f"請求超時: {endpoint}")
        return self._error_response("請求超時", 32000)
    except ClientError as e:
        self.logger.error(f"網路錯誤: {e}")
        return self._error_response("網路請求失敗", 33000)
    except Exception as e:
        self.logger.error(f"未知錯誤: {e}")
        return self._error_response(str(e), 34000)
```

> **向後相容**：直接使用 `aiohttp.ClientSession` 的舊介接器程式碼不受影響，仍然可以擷取 `aiohttp.ClientError`。兩種方式可以共存。推薦新程式碼使用 `sdk.client` + ErisPulse 異常體系。

## Bot 狀態管理

AdapterManager 內建了 Bot 狀態追蹤系統，自動維護所有已註冊 Bot 的線上狀態、活躍時間和元資訊。

### 自動發現機制

當介接器透過 `adapter.emit()` 發送事件時，框架會自動檢查事件中的 `self` 欄位：

- **meta 事件**：根據 `detail_type` 執行對應操作（connect 註冊/斷開標記離線/heartbeat 更新活躍時間）
- **普通事件**（message/notice/request）：自動發現 Bot 並更新活躍時間

```python
# 所有包含 self 欄位的事件都會觸發自動發現
await self.adapter.emit({
    "type": "message",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": "bot123"},
    # ...
})
# Bot "bot123" 已自動註冊（如果首次出現）並更新活躍時間
```

### Meta 事件類型

| `detail_type` | 說明 | 框架行為 |
|---|---|---|
| `connect` | Bot 連接 | 註冊 Bot 並觸發 `adapter.bot.online` 生命週期事件 |
| `disconnect` | Bot 斷開 | 標記 Bot 離線並觸發 `adapter.bot.offline` 生命週期事件 |
| `heartbeat` | Bot 心跳 | 更新 Bot 活躍時間和元資訊 |

### 介接器發送 Meta 事件

使用 `emit_meta()` 一行即可發送 meta 事件：

```python
class MyAdapter(BaseAdapter):
    async def _on_bot_connect(self, bot_id: str):
        # 一行發送 connect 事件
        await self.emit_meta("connect", bot_id, user_name="MyBot", nickname="我的機器人")

    async def _on_bot_disconnect(self, bot_id: str):
        await self.emit_meta("disconnect", bot_id)
```

也支援手動建構（舊版方式仍然相容）：

```python
await self.adapter.emit({
    "type": "meta",
    "detail_type": "connect",
    "platform": "myplatform",
    "self": {"platform": "myplatform", "user_id": bot_id}
})
```

### `self` 欄位擴展資訊

`self` 欄位除必需的 `platform` 和 `user_id` 外，還支援以下可選欄位：

| 欄位 | 說明 |
|---|---|
| `user_name` | Bot 用戶名 |
| `nickname` | Bot 昵稱 |
| `avatar` | Bot 頭像 URL |
| `account_id` | 多帳戶識別 |

### Bot 狀態查詢

```python
from ErisPulse import sdk

# 取得單個 Bot 資訊
info = sdk.adapter.get_bot_info("myplatform", "bot123")
# {"status": "online", "last_active": 1712345678.0, "info": {"nickname": "MyBot"}}

# 列出所有 Bot
all_bots = sdk.adapter.list_bots()

# 列出指定平台的 Bot
platform_bots = sdk.adapter.list_bots("myplatform")

# 檢查 Bot 是否線上
is_online = sdk.adapter.is_bot_online("myplatform", "bot123")

# 取得完整狀態摘要（適合 WebUI 展示）
summary = sdk.adapter.get_status_summary()
# {"adapters": {"myplatform": {"status": "started", "bots": {...}}}}
```

### 監聽 Bot 生命週期

```python
from ErisPulse import sdk

@sdk.lifecycle.on("adapter.bot.online")
async def on_bot_online(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot 上線: {platform}/{bot_id}")

@sdk.lifecycle.on("adapter.bot.offline")
async def on_bot_offline(data):
    platform = data.get("platform")
    bot_id = data.get("bot_id")
    sdk.logger.info(f"Bot 下線: {platform}/{bot_id}")
```

## 相關文件

- [介接器開發入門](getting-started.md) - 建立第一個介接器
- [SendDSL 詳解](send-dsl.md) - 學習訊息發送
- [介接器最佳實踐](best-practices.md) - 開發高品質介接器