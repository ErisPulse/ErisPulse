# 適配器核心概念

> [!TIP]
> **何時需要閱讀這篇**：在開發適配器的過程中必讀（BaseAdapter / SendDSL / 生命周期等核心機制的完整說明）。若只想起步，可先閱讀 [適配器開發入門](getting-started.md)，遇到「為什麼」層面的疑問再回到本篇查閱。

本文解釋適配器的運行機制：AdapterManager 如何註冊與分發事件、`BaseAdapter` 在初始化時替你做了什麼、配置與多帳戶如何聲明——寫適配器時遇到「為什麼要這樣寫」的疑問，請在這裡查找。

## 適配器架構

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
│                  │   │ 適配器 (MyAdapter) │   │ Send.Raw_ob12()  │
│  Converter       │   │ ┌──────────────┐ │   │ (反向轉換入口)   │
│  (事件轉換器)    │──→│ │              │ │   │                  │
└──────────────────┘   │ │              │ │   └────────┬─────────┘
                       │ └──────────────┘ │            │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 平台 API 調用    │
                       │ OneBot12 標準事件 │    └────────┬─────────┘
                       └────────┬─────────┘             │
                                │                      ↓
                                ↓              ┌──────────────────┐
                       ┌──────────────────┐    │ 標準回應格式     │
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
- **反向轉換**（Raw_ob12）：OneBot12 消息段 → 平台 API 調用，回傳標準回應格式

## AdapterManager 適配器管理器

`AdapterManager` 是 ErisPulse 適配器系統的核心組件，負責管理所有平台適配器的註冊、啟動、關閉和事件分發。

### 核心功能

- **適配器註冊**：註冊和管理多個平台適配器
- **生命週期管理**：控制適配器的啟動和關閉
- **事件分發**：分發 OneBot12 標準事件和平台原生事件
- **配置管理**：管理適配器的啟用/禁用狀態
- **中間件支援**：支援 OneBot12 事件中間件

### 基本使用

```python
from ErisPulse import sdk

# 註冊適配器（通常由 Loader 自動完成）
sdk.adapter.register("myplatform", MyPlatformAdapter)

# 啟動所有適配器
await sdk.adapter.startup()

# 啟動指定適配器
await sdk.adapter.startup(["myplatform"])
# 啟動全部適配器
await sdk.adapter.startup()

# 獲取適配器實例
my_adapter = sdk.adapter.get("myplatform")
# 或透過屬性存取
my_adapter = sdk.adapter.myplatform

# 關閉所有適配器
await sdk.adapter.shutdown()
```

### 啟動和關閉

#### 啟動適配器

```python
# 啟動所有已註冊的適配器
await sdk.adapter.startup()

# 啟動指定平台
await sdk.adapter.startup(["platform1", "platform2"])
```

**啟動流程：**

1. 提交 `adapter.start` 生命週期事件
2. 提交 `adapter.status.change` 事件（starting）
3. 並行啟動各個適配器
4. 如果啟動失敗，自動重試（指數退避策略）
5. 啟動成功後提交 `adapter.status.change` 事件（started）

**重試機制：**

- 前 4 次重試：60秒、10分鐘、30分鐘、60分鐘
- 第 5 次及以後：3 小時固定間隔

#### 關閉適配器

```python
# 關閉所有適配器
await sdk.adapter.shutdown()
```

**關閉流程：**

1. 提交 `adapter.stop` 生命週期事件
2. 調用所有適配器的 `shutdown()` 方法
3. 關閉路由伺服器
4. 清空事件處理器
5. 提交 `adapter.stopped` 生命週期事件

### 配置管理

#### 檢查平台狀態

```python
# 檢查平台是否已註冊
exists = sdk.adapter.exists("myplatform")

# 檢查平台是否啟用
enabled = sdk.adapter.is_enabled("myplatform")

# 使用 in 操作符
if "myplatform" in sdk.adapter:
    print("平台存在且已啟用")
```

#### 列出平台

```python
# 列出所有已註冊的平台
platforms = sdk.adapter.list_registered()

# 列出所有平台及其狀態
status_dict = sdk.adapter.list_items()
# 回傳: {"platform1": true, "platform2": false, ...}

# 獲取已啟用的平台列表
enabled_platforms = [p for p, enabled in status_dict.items() if enabled]
```

### 事件監聽

#### OneBot12 標準事件

```python
from ErisPulse import sdk

# 監聽所有平台的標準訊息事件
@sdk.adapter.on("message")
async def handle_message(data):
    print(f"收到OneBot12訊息: {data}")

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

# 監聽所有平台的原生事件（通配符）
@sdk.adapter.on("*", raw=True)
async def handle_all_raw_events(data):
    print(f"收到原生事件: {data}")
```

#### 事件分發機制

當呼叫 `adapter.emit(event_data)` 時：

1. **中間件處理**：先執行所有 OneBot12 中間件
2. **標準事件分發**：分發到匹配的 OneBot12 事件處理器
3. **原生事件分發**：如果存在原始資料，分發到原生事件處理器

**匹配規則：**

- 精確匹配：`@sdk.adapter.on("message")` 只匹配 `message` 事件
- 通配符：`@sdk.adapter.on("*")` 匹配所有事件
- 平台過濾：`platform="myplatform"` 只分發指定平台的事件

### 中間件

#### 添加中間件

```python
@sdk.adapter.middleware
async def logging_middleware(data):
    """日誌記錄中間件"""
    print(f"處理事件: {data.get('type')}")
    return data  # 必須回傳資料

@sdk.adapter.middleware
async def filter_middleware(data):
    """事件過濾中間件"""
    # 過濾不需要的事件
    if data.get("type") == "notice":
        return None  # 回傳 None 時中間件鏈會忽略該回傳值，保留原資料繼續傳遞
    return data  # 必須回傳資料以繼續傳遞
```

#### 中間件回傳契約

| 回傳值 | 行為 |
|--------|------|
| `dict` | 改寫事件載荷（後續處理器收到改寫後的事件） |
| `None` | 放行，載荷不變（輸出 WARNING 提示——建議顯式 `return data`） |
| `False` | **否決**：事件被丟棄，不進入任何處理器、無任何出站副作用 |

否決適用於防火牆、限流、黑名單等「在事件層面直接丟棄」的場景（此前只能用高優先級事件處理器繞行實現）。否決時框架輸出 TRACE 日誌並觸發 `adapter.event.blocked` 生命週期鈎子（攜帶 `middleware` 中間件名、完整 `event`、`platform` / `event_type` / `detail_type`），便於排查「事件為什麼沒回應」：

```python
@sdk.adapter.middleware
async def rate_limit_middleware(data):
    """限流中間件"""
    if _is_rate_limited(data):
        return False  # 否決：事件被丟棄
    data["rate_marked"] = True
    return data

@sdk.lifecycle.on("adapter.event.blocked")
async def on_event_blocked(data):
    print(f"事件被 {data['middleware']} 否決: {data['event_type']}")
```

#### 中間件執行順序

中間件按照註冊順序執行，後註冊的中間件先執行。

> **注意**：如果中間件回傳 `None`（例如忘記 `return data`），框架會忽略該回傳值並保留原資料繼續傳遞，同時輸出 warning 級別日誌。這確保了單個中間件的失誤不會導致整個事件鏈中斷。

```python
# 註冊順序
sdk.adapter.middleware(middleware1)  # 最後執行
sdk.adapter.middleware(middleware2)  # 中間執行
sdk.adapter.middleware(middleware3)  # 最先執行

# 執行順序：middleware3 -> middleware2 -> middleware1
```

### 獲取適配器實例

#### get() 方法

```python
adapter = sdk.adapter.get("myplatform")
if adapter:
    await adapter.Send.To("user", "123").Text("Hello")
```

#### 屬性存取

```python
# 透過屬性名存取（不區分大小寫）
adapter = sdk.adapter.myplatform
await adapter.Send.To("user", "123").Text("Hello")
```

## BaseAdapter 基類

### 基本結構

```python
from dataclasses import dataclass, field
from ErisPulse.Core import BaseAdapter
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyConfig(BaseConfig):
    """適配器配置（聲明後框架自動管理）"""
    token: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )

class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig  # 聲明配置類
    
    # 無需覆寫 __init__，框架自動處理：
    # - self.sdk, self.logger
    # - self.cfg（類型安全的配置實例，即時讀取）
    # - self.Send, self.Request
    
    async def start(self):
        """啟動適配器（必須實現）"""
        cfg = self.cfg  # 自動加載的類型安全配置
        pass
    
    async def shutdown(self):
        """關閉適配器（必須實現）"""
        pass
    
    async def call_api(self, endpoint: str, **params):
        """呼叫平台 API（必須實現）"""
        pass
```

### 配置管理

框架提供了宣告式配置管理，透過 dataclass 定義配置結構，框架自動處理加載、驗證和範本生成。

#### 單帳戶配置

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class TelegramConfig(BaseConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "telegram.token", "default": "Bot Token"},
        "required": True,
        "secret": True,
        "ui": {"widget": "password", "group": "basic", "order": 1},
    })
    proxy: str = field(default="", metadata={
        "description": {"i18n": "telegram.proxy", "default": "代理地址"},
        "ui": {"widget": "text", "group": "advanced", "order": 10},
    })

class TelegramAdapter(BaseAdapter):
    ConfigClass = TelegramConfig
    
    async def start(self):
        cfg = self.cfg  # 類型安全，即時讀取
        if not cfg.token:
            raise ValueError("未配置 Token")
        await self._connect(cfg.token, proxy=cfg.proxy)
```

#### 多帳戶配置

`BotAccountConfig` 基類提供 `enabled` 和 `name` 字段。絕大多數適配器能從平台協議或登入回應中自動獲取 bot_id，在事件轉換時注入到帳戶配置中。：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

# 大多數適配器：bot_id 運行時自動獲取，無需配置
@dataclass
class MyBotConfig(BotAccountConfig):
    token: str = field(default="", metadata={
        "description": {"i18n": "my_adapter.bot_token", "default": "Token"},
        "required": True,
    })

# 如果登入時無法獲取 bot_id，可以讓使用者在配置中填寫
@dataclass
class YunhuBotConfig(BotAccountConfig):
    bot_id: str = field(default="", metadata={
        "description": {"i18n": "yunhu.bot_id", "default": "機器人ID"},
        "required": True,
    })
    token: str = field(default="", metadata={
        "description": {"i18n": "yunhu.token", "default": "Token"},
        "required": True,
    })

class MyAdapter(BaseAdapter):
    AccountConfigClass = MyBotConfig
    
    async def start(self):
        for name, account in self.enabled_accounts.items():
            user_id = await self._login(name, account)
            await self.emit_meta("connect", user_id)
```

#### metadata 約定

欄位 metadata 同時服務於 TOML 注釋生成和 WebUI 表單渲染：

```python
metadata = {
    "description": str | dict,  # 欄位描述（支援 i18n）
    "required": bool,         # 是否必填（驗證 + WebUI 必填標記）
    "secret": bool,           # 是否敏感（WebUI 顯示為 ***，日誌中脫敏）
    "example": bool,          # 不落盤標誌：不寫入 config.toml（預設值/範本均排除），
                              # 僅渲染進 config.full.example；schema 帶 "example": true 標記，
                              # CLI 配置向導預設跳過；使用者手動設定後正常持久化
    "min": number, "max": number,  # 數值範圍驗證
    "ui": {                   # WebUI 控件配置（舊名 "webui" 仍兼容）
        "widget": str,        # 控件類型: "text" | "switch" | "select" | "number" | "password"
        "group": str,         # 分組: "basic" | "advanced" | "connection" 等
        "order": int,         # 排序權重（越小越靠前）
        "options": list,      # select 控件的可選項 [{label, value}]，label 支援 i18n
        "placeholder": str | dict,  # 輸入框佔位符（支援 i18n）
    },
    "extra": dict,            # 預留擴展欄位（透傳到 schema）
}
```

所有使用者可見的文本欄位均支援 i18n，統一採用 `{"i18n": "key", "default": "文本"}` 格式，
純字串則原樣透傳（向後相容）。支援的 i18n 欄位：

| 欄位 | 位置 | 說明 |
|------|------|------|
| `description` | field metadata | 欄位描述 |
| `options[].label` | `ui.options` | select 控件選項標籤 |
| `placeholder` | `ui.placeholder` | 輸入框佔位符 |
| `group_labels` | `_schema_meta` | 分組顯示名（Dashboard 分區標題） |

使用 i18n 時，需提前將翻譯鍵註冊到 i18n 系統（詳見 [i18n 文檔](../../advanced/i18n.md#配置欄位多語言)）。

**description / placeholder / options label** 範例：

```python
token: str = field(
    default="",
    metadata={
        "description": {"i18n": "my_adapter.token", "default": "Bot Token"},
        "ui": {
            "widget": "text",
            "placeholder": {"i18n": "my_adapter.token.ph", "default": "請輸入 Token"},
        },
    },
)
mode: str = field(
    default="a",
    metadata={
        "description": {"i18n": "my_adapter.mode", "default": "模式"},
        "ui": {
            "widget": "select",
            "options": [
                {"label": {"i18n": "my_adapter.mode.a", "default": "選項A"}, "value": "a"},
                {"label": "純字串標籤", "value": "b"},  # 純字串原樣透傳
            ],
        },
    },
)
```

**group_labels** 範例（在配置類定義後聲明）：

```python
MyConfig._schema_meta = {
    "group_labels": {
        "basic": {"i18n": "my_adapter.group.basic", "default": "基本設定"},
        "advanced": {"i18n": "my_adapter.group.advanced", "default": "進階設定"},
    }
}
```

框架的 `resolve_config_schema()` 會根據當前語言自動解析上述所有欄位的 i18n 鍵；
`get_config_schema()` 則原樣透傳 i18n 字典，由前端自行解析。

#### docstring 自动生成欄位描述（v2.8.0+）

未在 metadata 中聲明 `description` 的欄位，框架會自動從配置類 docstring 中
提取欄位說明作為兜底，支援兩種常見風格（可混用）：

```python
@dataclass
class MyConfig(BaseConfig):
    """
    MyAdapter 配置

    :ivar endpoint: 平台 API 地址        # reST 風格
    :ivar timeout: 請求超時秒數
    """

    endpoint: str = "https://api.example.com"   # 無 metadata description → 注釋/描述取 docstring
    timeout: int = 30

    # Google 風格同樣支援（Attributes: 段）：
    # Attributes:
    #     endpoint: 平台 API 地址
```

優先級：**metadata description > docstring 欄位說明 > 空**。
i18n 字典形式的 description 不受影響（始終優先）。

#### 嵌套配置（v2.8.0+）

欄位類型為嵌套 dataclass 時，框架遞迴處理：schema 以 `"type": "table"` +
`"fields"` 子樹承載（WebUI 渲染為可摺疊嵌套分組），TOML 範本渲染為 `[子表]` 節，
預設值 / 填充 / 驗證 / i18n 解析均遞迴生效。

```python
@dataclass
class RetryConfig(BaseConfig):
    """重試策略

    :ivar max_retries: 最大重試次數
    """
    max_retries: int = 3
    backoff: float = 0.5

@dataclass
class MyConfig(BaseConfig):
    """MyAdapter 配置"""
    endpoint: str = "https://api.example.com"
    retry: RetryConfig = field(default_factory=RetryConfig)   # 嵌套配置段
```

生成的 TOML 範本：

```toml
endpoint = "https://api.example.com"

[retry]
# 最大重試次數
max_retries = 3
backoff = 0.5
```

> 嵌套類型建議使用直接類型註解；字串註解（如延遲求值場景）需保證
> 類型可從配置類所在模組全域、`__qualname__` 外層類命名空間或類屬性中按名解析。

#### 不落盤的 example 字段（v2.8.0+）

```python
gc_interval: int = field(default=300, metadata={"example": True})
```

帶 `example: True` 的欄位：

- 不寫入 config.toml（適配器/模組配置範本與預設值均排除，運行時走代碼預設值）
- 僅渲染進專案內 `config.full.example`（供使用者參考，按需手動複製到 config.toml）
- schema 中帶 `"example": true` 標記（面板可自行決定展示策略），CLI 配置向導預設跳過
- 使用者手動設定該鍵後正常持久化、正常熱更新（使用者顯式意圖優先）

適合「繁雜又很少觸碰」的進階配置項，保持使用者的 config.toml 最小化。

> ⚠️ `_schema_meta` 是類級元資料（非配置欄位）。若在 dataclass 類體內部宣告，
> 必須加 `ClassVar` 註解（`_schema_meta: ClassVar[dict] = {...}`），否則會被
> dataclass 視為普通欄位。框架對下劃線前綴欄位已做防禦性排除（不進入任何
> schema / 範本 / 預設值 / 驗證輸出），但仍建議規範宣告。

### 声明式翻譯鍵（v2.7.0+）

適配器可以像宣告 `ConfigClass` 一樣，透過嵌套類 `I18nClass` 集中宣告翻譯鍵。
框架會在 `__init__` 階段（配置範本生成之前）自動註冊所有宣告的翻譯鍵，
確保配置描述中引用的 i18n 鍵在生成範本時已可用。

```python
from ErisPulse.Core.Bases import BaseAdapter, BaseI18n, I18nKey

class MyAdapter(BaseAdapter):
    class I18nClass(BaseI18n):
        endpoint: I18nKey = I18nKey(
            default="API Endpoint",
            zh_CN="API 地址",
            zh_TW="API 位址",
            en="API Endpoint",
            ja="APIアドレス",
            ru="API 地址",
        )
        token: I18nKey = I18nKey(
            default="Platform Token",
            zh_CN="平台 Token",
            zh_TW="平台權杖",
            en="Platform Token",
            ja="プラットフォームトークン",
            ru="Токен платформы",
        )
```

> ``I18nKey.default`` 是**語言無關的兜底文本**，不會註冊到任何語言。
> 要讓翻譯生效，必須顯式傳入至少一個語言參數。

詳細用法（鍵路徑規則、顯式 key 參數等）見 [i18n 文檔](../../advanced/i18n.md#推薦寫法通過-i18nclass-宣告翻譯鍵-v270)。

### 声明式事件擴展方法（v2.7.0+）

適配器可以透過 `EventMixin` 集中宣告平台特有的事件擴展方法，框架自動註冊到當前平台。

```python
from ErisPulse.Core import BaseAdapter

class MyAdapter(BaseAdapter):
    class EventMixin:
        def get_chat_name(self):
            """獲取聊天名稱"""
            return self.get("myplatform_raw", {}).get("chat", {}).get("name", "")

        def is_official_message(self):
            """判斷是否為官方訊息"""
            raw = self.get("myplatform_raw", {})
            return raw.get("sender", {}).get("is_official", False)
```

註冊後，事件物件直接呼叫這些方法：

```python
@message.on_group_message()
async def handler(event):
    if event.is_official_message():
        chat_name = event.get_chat_name()
        await event.reply(f"[{chat_name}] 官方訊息已收到")
```

> 適配器的事件擴展方法註冊到自身平台（``self._platform``）。
> 模組如需跨平台事件擴展，請使用原有的 ``register_event_mixin()`` API。

#### 帳戶解析

適配器實作 `call_api` 時，需要把帳戶標識解析為具體帳戶配置。框架把帳戶綁定（`Using()` 或事件鏈自動綁定的結果）以標準欄位 `account_id` 傳入 `call_api`，並按適配器的實際消費方式自動適配——三種消費形態任選其一，框架按簽名參數名與函數體常量探測，與參數位置無關：

```python
# 形態一（推薦）：簽名聲明標準名
async def call_api(self, endpoint: str, account_id: str | None = None, **params):
    name, account = self._resolve_account(account_id)
    # name: 帳戶名, account: 配置實例

# 形態二（存量相容）：舊名 _account_id，框架自動把 account_id 改寫為舊名下發
async def call_api(self, endpoint: str, _account_id: str | None = None, **params):
    name, account = self._resolve_account(_account_id)

# 形態三：函數體內從 params 取（被常量探測識別）
async def call_api(self, endpoint: str, **params):
    account_id = params.pop("account_id", None)
    name, account = self._resolve_account(account_id)
```

> 適配器未消費帳戶欄位時，框架剔除該欄位（避免洩漏進平台參數）並提示一次 WARNING；單帳戶適配器可不消費（解析回退第一個啟用帳戶）。

解析策略：帳戶名匹配 → `bot_id` 欄位匹配 → 其他 str 欄位匹配 → 第一個啟用帳戶。

**執行期識別與持久化**（2.12+）：適配器在連線建立 / 事件到達時呼叫 `self.update_bot_id(account_name, bot_id)`——框架維護 bot_id → 帳戶註冊表（解析鏈第一優先級），並在值變化時把 `accounts.<帳戶名>.bot_id` 寫入配置儲存：重啟後帳戶實例重建即自帶 bot_id，第二帳戶等場景的解析不再依賴帳戶活動回填（消除重啟窗口期）。

#### 配置熱更新

子類可覆寫 `on_config_update()` 回應配置變更：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def on_config_update(self, old_config, new_config):
        if old_config.token != new_config.token:
            self.logger.info("Token 已更新，將重新連線")
```

### 初始化過程

框架在 `BaseAdapter.__init__(self, sdk=None)` 中自動完成以下工作：

1. **SDK 引用**：設定 `self.sdk`、`self.logger`
2. **Send/Request 工廠**：建立 `self.Send` 和 `self.Request`
3. **配置範本**：如果聲明了 `ConfigClass`，自動產生預設配置範本（首次）
4. **帳戶範本**：如果聲明了 `AccountConfigClass`，自動產生預設帳戶範本（首次）
5. **EventMixin 註冊**：如果聲明了 `EventMixin`，在 `AdapterManager` 注入平台名後自動註冊

配置透過 `self.cfg` / `self.accounts` 即時讀取（每次存取都從配置儲存讀取最新值）。`self.config` 作為 `self.cfg` 的相容別名仍可使用。

大多數適配器無需覆寫 `__init__`。如需自定義初始化：

```python
class MyAdapter(BaseAdapter):
    ConfigClass = MyConfig
    
    def __init__(self, sdk=None):
        super().__init__(sdk)  # 傳入 sdk
        self.converter = self._setup_converter()
        self.convert = self.converter.convert
```

## Send 消息發送 DSL

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
| `_account_id` | 發送帳戶ID | `Using(account_id)` |
| `_adapter` | 適配器實例 | 自動設定 |
| `_at_user_ids` | @用戶列表 | `At(user_id)` |
| `_reply_message_id` | 回覆的訊息ID | `Reply(message_id)` |
| `_at_all` | 是否@全體 | `AtAll()` |

> **推薦**：使用 `self.send_context` 屬性一次性獲取 `target_type`、`target_id`、`account_id`，比直接存取實例變數更清晰。

### 框架輔助方法

| 方法/屬性 | 說明 |
|-----------|------|
| `self._apply_modifiers(message)` | 將 At/AtAll/Reply 修飾器狀態合併到訊息段列表 |
| `self.send_context` | 回傳 `{target_type, target_id, account_id}` 字典；`account_id` 未顯式指定時兜底當前事件分發鏈路的觸發帳戶 |

### 基本方法

適配器只需實作 `Raw_ob12`，標準方法（Text/Image/Voice/Video/File）已從 `SendDSL` 基類繼承並預設委託給它：

```python
class Send(BaseAdapter.Send):
    def Raw_ob12(self, message, **kwargs):
        """必須實作：OneBot12 消息段 → 平台 API"""
        async def _do_send():
            segments = self._apply_modifiers(message)
            return await self._adapter.call_api(
                endpoint="/send_message",
                message=segments,
                **self.send_context,
                **kwargs
            )
        return asyncio.create_task(_do_send())

    # Text/Image/Voice/Video/File 已從基類繼承，自動委託 Raw_ob12，無需重複實作
    # 如需平台特定邏輯，可覆蓋單個方法：
    # def Text(self, text: str):
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
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
    "id": "事件唯一標識",          # 同一帳戶重推同一事件必須相同（框架據此去重）
    "time": 1234567890,           # 10位 Unix 時間戳
    "type": "message/notice/request/meta",
    "detail_type": "事件詳細類型",
    "platform": "平台名稱",
    "message_id": "訊息ID",        # 訊息類事件必須
    "self": {
        "platform": "平台名稱",
        "user_id": "機器人ID"     # 必須與 bot_id 一致
    },
    "{platform}_raw": {...},       # 原始資料（必須）
    "{platform}_raw_type": "..."    # 原始類型（必須）
}
```

> 事件 `id` 需帶帳戶維度：同一帳戶重推同一事件保持相同 `id`，不同帳戶收到同一條群訊息時 `id` 必須不同（例如 `f"{self.user_id}:{post_type}:{message_id}"`）。

### 跨帳戶重複受理（框架注入欄位）

多帳戶適配器的多個帳戶在同一群/會話時，同一物理訊息會經各帳戶先後到達。框架在 `ErisPulse.framework.cross_account_policy != "off"` 時自動做內容級關聯（同平台 + 同會話 + 同發送者 + 同 `alt_message` 在短視窗內），適配器無需參與：

- `mark`：後續副本注入頂層欄位 `"multi_receipt": {"event_id": 首受理事件id, "self_id": 首受理帳戶}` 後照常分發，模組讀取該欄位自行裁決
- `drop`：後續副本在分發入口直接丟棄

`multi_receipt` 為框架注入的可選欄位，適配器 Converter 不產出也不消費；策略預設 `off` 時事件結構與既有契約完全一致。

#### 三層去重機制分工

| 機制 | 配置 | 拦截什麼 | 判定依據 |
|------|------|----------|----------|
| 事件幂等去重 | `ErisPulse.framework.event_dedupe`（預設開） | 同一事件 id 的重連重推（同連線） | 事件 `id` |
| 本號回聲過濾 | `ErisPulse.event.message.ignore_self`（預設開） | 接收帳戶自己的訊息（發送者 == 接收帳戶） | `self.user_id` vs `user_id` |
| 跨帳戶重複受理 | `ErisPulse.framework.cross_account_policy`（預設 `off`，`drop` 啟用） | **同一物理訊息經其它帳戶的副本**——多帳戶同群時 bot A 發言、bot B 也收到一份 | 內容級關聯（同平台 + 同會話 + 同發送者 + 同內容，短視窗），鍵不含 self_id |

**典型場景——多帳戶同群複讀**：bot A 發言，同群的其他帳戶（bot B）也會收到一份，複讀類模組看到同一內容出現兩次。啟用 `cross_account_policy = "drop"` 後，後續帳戶的副本在分發入口丟棄，任何模組至多看到一次。

與 `ignore_self` 的語義正交，兩者組合決定可見次數：

| 組合 | 複讀模組看到 bot A 的訊息 |
|------|--------------------------|
| `drop` + `ignore_self = true`（預設） | 0 或 1 次（先到副本若經 A 自身連線則被 ignore_self 拒截）——**永不 2 次** |
| `drop` + `ignore_self = false` | 恆定恰好 1 次 |

> 不建議把 `ignore_self` 的語義擴展為「排除本機全部帳戶」：該判定依賴接收事件的 `self.user_id`（綁定未建立的視窗期會失效，見上文執行期邊界），而跨帳戶關聯是內容級判定，不依賴 self 信息；且「逐帳戶接收」是跨帳戶日誌 / 同步類模組的既有依賴，收窄語義屬於隱式破壞。跨帳戶去重交給 `cross_account_policy`。

### 轉換器範例

```python
class MyPlatformConverter:
    def convert(self, raw_event):
        """將平台原生事件轉換為 OneBot12 標準格式"""
        if not isinstance(raw_event, dict):
            return None
        
        # 產生事件 ID
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
        
        # 構建標準事件
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

## 連線管理

### start() 的兩種正確寫法

客戶端模式的適配器（WebSocket 客戶端、HTTP 輪詢等）需要在 `start()` 裡拉起一個
常駐連線循環。框架支援兩種寫法，**都正確，但只能二選一**：

**寫法一：spawn-返回式（推薦）**——經 `spawn_client_loop()` 把循環調度為歸屬本平台
的背景任務，`start()` 立即返回：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        # 循環任務歸屬 self._platform：shutdown 時框架自動取消
        self.spawn_client_loop(self._connect_loop())
        # start 到這裡就結束——"啟動即成功"，連線失敗由循環內重試

    async def _connect_loop(self):
        while True:
            try:
                await self._connect_and_receive()   # 斷開拋異常 → 下方退避
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(5)              # 循環內自行退避重連
```

**寫法二：常駐式**——`start()` 直接 `await` 連線循環，永不返回：

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        await self._connect_loop()   # 常駐不返回；循環拋異常 = start 失敗
```

兩種寫法的差異與共同點：

| | spawn-返回式 | 常駐式 |
|---|---|---|
| `start()` 返回時機 | 拉起循環後立即返回 | 連線循環退出/失敗時（框架按退避策略重試） |
| 連線失敗處理 | 循環內自行捕獲退避 | 異常上拋，交給框架的重試鏈 |
| 適用場景 | 需要快速返回啟動確認（多連線、註冊路由後還要拉起其它任務） | "連線即啟動"語義的簡單實現 |

`spawn_client_loop(coro, *, name="client_loop")` 是寫法一的調度入口：任務按
`self._platform` 歸屬登記，適配器 `shutdown()` 時框架按歸屬自動取消，無需自己
管理任務句柄；循環內未捕獲的異常會自動留痕（預期的斷連重連請在循環內自行捕獲）。

> **唯一錯誤寫法是混用**：spawn 之後又 `await` 同一個循環——這會讓 `start()`
> 失去立即返回語義，任務取消路徑也會變得不可預測。

### 連線模式半成品基類

上一節的兩種寫法之外，最常見的兩類連線模式框架直接提供了「半成品」基類
（`ErisPulse.Core.Bases.adapter_patterns`，根包可直接導入）：`start` / `shutdown`
的生命週期編排全部由基類完成，子類只實現業務鈎子。

#### PollingAdapter（HTTP 輪詢型）

適用於「客戶端定時拉取事件」的平台（Telegram getUpdates 型）。基類以
spawn-返回式拉起常駐輪詢循環，拉取失敗自動留痕並指數退避（基數 1 秒、上限
60 秒，成功後歸零；常量 `POLLING_ADAPTER_BACKOFF_BASE_SECS` /
`POLLING_ADAPTER_BACKOFF_MAX_SECS` 可在 `Core/constants.py` 調整）：

```python
from ErisPulse import PollingAdapter

class MyAdapter(PollingAdapter):
    # 輪詢間隔預設 5 秒；ConfigClass 聲明 poll_interval 欄位後以配置值為準（熱更新生效）
    poll_interval = 5.0

    async def fetch_events(self):
        """拉一批平台原生事件（異常由基類統一退避，無需 try/except）"""
        resp = await self.sdk.client.get(f"{self.cfg.endpoint}/getUpdates")
        data = await resp.json()
        return data.get("result", [])

    def convert_one(self, raw):
        """單條原生事件轉 OneBot12；回傳 None 跳過"""
        return self.converter.convert(raw)

    async def call_api(self, endpoint: str, **params):
        ...  # 與普通適配器相同
```

最小實現面：`fetch_events` / `convert_one` / `call_api`。`start()` 拉起循環後立即
返回；`shutdown()` 無需子類處理（輪詢循環按 owner 歸屬自動取消）。

#### WebhookAdapter（HTTP 回調型）

適用於「平台主動推送回調」的平台。基類的 `start()` 在框架 router 上註冊接收路由
（最終路徑 `/{平台名}/webhook`，POST 方法），註冊包在 `owner_scope` 中——適配器
卸載時按 owner 自動清理，無需手動註銷：

```python
from ErisPulse import WebhookAdapter

class MyAdapter(WebhookAdapter):
    def verify_request(self, request) -> bool:
        """可選鈎子：回調校驗（預設放行；回傳 False 時基類以 403 回絕）"""
        cfg = self.cfg
        if not cfg.token:
            return True
        auth = request.headers.get("authorization", "")
        return auth == f"Bearer {cfg.token}"

    def convert(self, payload):
        """回調載荷轉 OneBot12；回傳 None 跳過"""
        return self.converter.convert(payload)

    async def call_api(self, endpoint: str, **params):
        ...  # 與普通適配器相同
```

最小實現面：`convert` / `call_api`（`verify_request` 可選）。回調地址經
`sdk.adapter.get_connection_info(platform)` 查詢後填到平台後台；校驗失敗的請求
回傳 403、載荷解析失敗回傳 400、正常回傳 `{"status": "ok"}`。

#### 三種模式怎麼選

| 平台協議 | 繼承 | 腳手架 |
|---|---|---|
| 平台連過來（WebSocket 服務端） | `BaseAdapter` | `epsdk create adapter`（預設 ws-server） |
| 我們去拉（HTTP 輪詢） | `PollingAdapter` | `epsdk create adapter --template polling` |
| 平台推過來（HTTP 回調） | `WebhookAdapter` | `epsdk create adapter --template webhook` |

完整可運行範例見倉庫 `examples/example-adapter/`（ws-server）、
`examples/example-adapter-polling/`、`examples/example-adapter-webhook/`。

### WebSocket 連線

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """註冊 WebSocket 路由"""
        router.register_websocket(
            module_name="myplatform",
            path="/ws",
            handler=self._ws_handler,
            auth_handler=self._auth_handler
        )
    
    async def _ws_handler(self, websocket):
        """WebSocket 連線處理器"""
        self.connection = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                onebot_event = self.convert(data)
                if onebot_event:
                    await self.adapter.emit(onebot_event)
        except WebSocketDisconnect:
            self.logger.info("連線已斷開")
        finally:
            self.connection = None
    
    async def _auth_handler(self, websocket) -> bool:
        """WebSocket 認證"""
        token = websocket.query_params.get("token")
        return token == "valid_token"
```

### WebHook 連線

```python
class MyAdapter(BaseAdapter):
    async def start(self):
        """註冊 WebHook 路由"""
        router.register_http_route(
            module_name="myplatform",
            path="/webhook",
            handler=self._webhook_handler,
            methods=["POST"]
        )
    
    async def _webhook_handler(self, request):
        """WebHook 請求處理器"""
        data = await request.json()
        onebot_event = self.convert(data)
        if onebot_event:
            await self.adapter.emit(onebot_event)
        return {"status": "ok"}
```

> 純回調型平台不必手寫上面這套註冊/校驗/清理編排——直接繼承
> [`WebhookAdapter` 半成品基類](#連接模式半成品基類)，只實現 `convert`
> （可選覆寫 `verify_request`）即可。

> **路由資訊查詢**：適配器註冊的路由（HTTP、WebSocket、SSE）可以透過 `sdk.adapter.get_connection_info(platform)` 和 `sdk.router.get_module_urls(module_name)` 查詢完整連線位址（包含 `base_url` + 路徑）。詳見 [適配器開發入門 - 連線資訊與路由發現](getting-started.md#9-連線資訊與路由發現) 和 [SSE 支援](getting-started.md#10-sse-server-sent-events-支援)。

## API 回應標準

框架提供 `make_response()` 和 `make_error()` 方法構造標準化回應，無需手動建構回應字典。

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

### 聲明式配置（推薦）

使用 `AccountConfigClass` 聲明配置類後，框架自動管理多帳戶加載、驗證和範本生成：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BotAccountConfig

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
    
    async def call_api(self, endpoint: str, account_id: str | None = None, **params):
        name, account = self._resolve_account(account_id)
        # 使用 account.token, account.bot_id 等欄位
```

### 帳戶配置檔案

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

# 透過事件中的 self.user_id（推薦，最通用）
await my_adapter.Send.Using(event["self"]["user_id"]).To("user", "123").Text("Hello")

# 透過帳戶名
await my_adapter.Send.Using("account1").To("user", "123").Text("Hello")
```

### 事件的帳戶標識與 Using 的關係

框架的事件回應機制會自動從事件的 `self` 欄位提取帳戶標識（優先 `account_id` 代位，否則 `user_id`），注入 `Using` 後發送。適配器開發者需確保 Converter 產出的帳戶標識能與帳戶配置匹配（帳戶名或 `bot_id` 等欄位）。

**框架注入行為**：

```python
# 框架提取帳戶標識的邏輯（account_id 代位優先，user_id 兜底）
account = self.get("self", {}).get("account_id", "") or self.get("self", {}).get("user_id", "")

# 僅在標識非空時注入 Using
if account:
    send_chain = send_chain.Using(account)
```

> **關鍵點**：即使適配器只使用一個 Bot 配置，只要 Converter 正確設定了帳戶標識，框架就會將其注入 `Using`。適配器需確保該標識與 `AccountConfigClass` 中的帳戶名或 `bot_id` 等欄位一致，從而解析到正確帳戶。標識為空時框架不注入 `Using`，此時發送按未指定帳戶處理——回落第一個啟用的帳戶。

顯式傳入的 `account_id` 無法解析時，框架記錄 WARNING 並回退到第一個啟用帳戶；WARNING 中的 `platform` / `account_id` / `account` 可用於定位未歸屬到帳戶的事件來源。

**事件分發鏈內的自動綁定**：處理事件的鏈路內呼叫發送方法時**無需顯式 `Using()`**——框架在事件分發入口把觸發事件的帳戶標識注入呼叫上下文，`Send` / `Api` / `Request` 鏈路未顯式指定帳戶時據此兜底綁定（顯式 `Using()` 永遠優先；定時器 / 啟動任務等無事件上下文場景維持預設帳戶語義）。事件鏈自動綁定需要 ErisPulse **2.12+**。

> 事件 `self.user_id` / `self.account_id` 代位的產出契約見[事件轉換標準](../../standards/event-conversion.md)；該欄位恆定存在是帳戶解析回退語義的前提——缺失時回落第一個啟用帳戶，多帳戶下即「從預設帳戶發出」。

## 錯誤處理

### 連線重試

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
                    self.logger.warning(f"連線失敗，{wait_time}秒後重試")
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

> **向後相容**：直接使用 `aiohttp.ClientSession` 的舊適配器程式碼不受影響，仍然可以捕獲 `aiohttp.ClientError`。兩種方式可以共存。推薦新程式碼使用 `sdk.client` + ErisPulse 異常體系。

## Bot 狀態管理

AdapterManager 內建了 Bot 狀態追蹤系統，自動維護所有已註冊 Bot 的在線狀態、活躍時間和元資訊。

### 自動發現機制

當適配器透過 `adapter.emit()` 發送事件時，框架會自動檢查事件中的 `self` 欄位：

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
| `connect` | Bot 連線 | 註冊 Bot 並觸發 `adapter.bot.online` 生命週期事件 |
| `disconnect` | Bot 斷開 | 標記 Bot 離線並觸發 `adapter.bot.offline` 生命週期事件 |
| `heartbeat` | Bot 心跳 | 更新 Bot 活躍時間和元資訊 |

### 適配器發送 Meta 事件

發送方式（`emit_meta()` 一行發送、心跳事件與手動建構格式）見 [適配器最佳實踐 - Bot 狀態管理與 Meta 事件](best-practices.md#bot-狀態管理與-meta-事件)。

### `self` 欄位擴展資訊

`self` 欄位除必需的 `platform` 和 `user_id` 外，還支援以下可選欄位：

| 欄位 | 說明 |
|---|---|
| `user_name` | Bot 用戶名 |
| `nickname` | Bot 昵稱 |
| `avatar` | Bot 頭像 URL |
| `account_id` | 多帳戶標識 |

### Bot 狀態查詢

查詢 API（`get_bot_info()` / `list_bots()` / `is_bot_online()` / `get_status_summary()`）見 [適配器系統 API - Bot 狀態管理](../../api-reference/adapter-system.md#bot-狀態管理)。

### 監聽 Bot 生命週期

`adapter.bot.online` / `adapter.bot.offline` 生命週期事件表與監聽範例見 [適配器系統 API - Bot 狀態管理](../../api-reference/adapter-system.md#bot-狀態管理)。

## 相關文件

### 實作層面深入

- [SendDSL 詳解](send-dsl.md) - 學習訊息發送
- [適配器最佳實踐](best-practices.md) - 開發高品質適配器

### 回看起步步驟

- [適配器開發入門](getting-started.md) - 創建第一個適配器