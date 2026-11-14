# 模組核心概念

> [!NOTE]
> **L1 核心必讀**——首頁「閱讀路徑」中的五篇核心文件之一，模組開發必備。


這篇講清模組從載入到卸載的完整生命週期、宣告式設定與儲存的用法——哪些事框架自動替你做、你只需要寫什麼，看完就有數。

## 模組生命週期

### 載入策略

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """返回模組載入策略"""
        return ModuleLoadStrategy(
            lazy_load=True,   # 懶載入還是立即載入
            priority=0,       # 載入優先級（數值越大越先載入）
            depends=["OtherModule"]  # 可選：宣告依賴的其他模組
        )
```

> `depends` 宣告的模組如果未註冊，當前模組將被跳過並記錄警告。載入順序由拓撲排序決定，同層級按 `priority` 降序。

> [!NOTE]
> **級聯卸載 / 級聯重載**（ErisPulse **2.8.0+**）：卸載被其它模組依賴的模組時，依賴它的模組會**先被級聯卸載**（日誌說明級聯鏈）；熱重載任意模組（本地外掛 / 執行時註冊 / PyPI 安裝包）時，依賴它的模組同樣**級聯重載**，避免依賴者持有失效實例參考繼續執行。宣告循環依賴會在載入時以 `RuntimeError` 拒絕。
>
> **reload 即全量重載**（ErisPulse **2.11.0+**）：`reload()` 預設按頂層套件名清理 import 快取並重導依賴者程式碼，卸載前自動語法預檢（失敗拒絕卸載、舊實例繼續服務），成功後核對程式碼身分（假重載告警 / `stale` 標記）；load 失敗現場可經 `sdk.module.last_error(名字)` 直接查詢（含 traceback）。

### on_load 方法

模組載入時呼叫，用於初始化資源和註冊事件處理器：

```python
async def on_load(self, event):
    # 註冊事件處理器
    @command("hello", help="問候命令")
    async def hello_handler(event):
        await event.reply("你好！")
    
    # 使用 SDK 內建 HTTP 用戶端（自動管理連線池，無需手動建立 session）
    # 透過 sdk.client 即可發送請求
```

### on_unload 方法

模組卸載時呼叫，用於清理資源：

```python
async def on_unload(self, event):
    # 清理自訂資源
    # sdk.client 由框架管理，無需手動關閉
    
    # 取消事件處理器（框架會自動處理）
    self.logger.info("模組已卸載")
```

> 背景任務的建立與清理（`self.spawn()` / 框架兜底取消）詳見 [生命週期管理](../../advanced/lifecycle.md#背景任務歸屬與自動取消)。

### on_before_unload 方法

> [!NOTE]
> 本鉤子需要 ErisPulse **2.11.0+**。

卸載流水線**第一步**（先於 `on_unload` 與資源回收）觸發的可選鉤子——此時模組的一切
資源仍然完好，適合在卸載 / 歸眠 / 重載前把狀態保存到 `sdk.storage`，下次 `on_load`
恢復（懶載入休眠的狀態接續即基於此）：

```python
async def on_before_unload(self, event):
    # event["reason"] 標註來意：unload / reload / disable / cascade / dormant
    if event["reason"] in ("reload", "dormant"):
        await self.state.aset("snapshot", self.collect_state())
```

鉤子失敗僅告警，不阻塞卸載流程；未宣告該鉤子的模組行為不變。歸眠 / 喚醒語義詳見
[懶載入休眠](../../advanced/lazy-loading.md#懶載入休眠dormant_after)。

### 卸載與徹底卸載（purge）

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

`unload()` 預設只**取消載入**（卸載實例與資源），但保留註冊存根（模組類別與元資訊）——模組仍可被 discover 重新發現、`load()` 重新實例化，無需重新 `register()`。

當需要**徹底卸載**（釋放模組類別參考、清理 `sys.modules`，讓外掛及其獨占依賴可被 GC 回收）時，傳入 `purge=True`：

```python
# 只取消載入：保留註冊存根，可隨時重新 load()
await sdk.module.unload("MyModule")

# 徹底卸載：刪除註冊存根 + 清理 sys.modules（外掛來源）
await sdk.module.unload("MyModule", purge=True)
```

| 語義 | `unload()` 預設 | `unload(purge=True)` |
|------|-----------------|----------------------|
| 卸載實例與資源（事件/task/路由/lifecycle/i18n） | ✅ | ✅ |
| 保留註冊存根（模組類別與元資訊） | ✅ | ❌ 刪除 |
| 清理 `sys.modules`（僅外掛資料夾來源） | ❌ | ✅ |
| 模組類別可被 GC 回收 | ❌ | ✅ |
| 重新載入 | `load()` 直接可用 | 需先 `register()` + `load()` |

> `purge=True` 時級聯卸載的依賴者同樣被 purge；卸載後框架會 `gc.collect()` 並檢查模組類別/實例是否可回收，殘留參考會在日誌中告警（含參考方，DEBUG 級）。

### 生命週期全景

把上面的方法串起來，框架在載入與卸載一個模組時，**在背後為你做的全部事情**：

```mermaid
flowchart TD
    subgraph Load["載入（register → load）"]
        L1["register：登記模組類別與元資訊"] --> L2["依賴校驗<br/>缺失則跳過"]
        L2 --> L3["拓撲排序（Kahn + priority）"]
        L3 --> L4["owner 注入 current_owner"]
        L4 --> L5["產生設定範本 + 註冊 i18n 翻譯鍵"]
        L5 --> L6["實例化模組（注入 sdk）"]
        L6 --> L7["呼叫 on_load()"]
        L7 --> L8["掛載到 sdk 屬性 + emit module.load"]
    end

    subgraph Unload["卸載（unload）"]
        U1["呼叫 on_unload()"] --> U2["兜底取消背景任務（self.spawn 歸屬）"]
        U2 --> U3["清理 i18n 翻譯鍵"]
        U3 --> U4["移除路由 / 命令 / 事件處理器（按 owner）"]
        U4 --> U5["清理 lifecycle 鉤子（按 owner）"]
        U5 --> U6["移除 SDK 屬性 + 懶載入代理"]
        U6 --> U7["emit module.unload"]
    end

    Load --> Unload
```

**載入時框架幫你做了什麼**（你只需寫 `on_load`，其餘自動完成）：

| 環節 | 框架自動做的 |
|------|-------------|
| owner 注入 | 實例化期間用 `owner_scope` 包住模組名——你 `on_load` 裡註冊的命令/事件/鉤子/背景任務**自動歸屬本模組**，卸載時按 owner 一鍵清理 |
| 設定範本 | 宣告了 `ConfigClass` 的模組，框架自動產生/填充 `ErisPulse.<ModuleName>` 設定區段 |
| i18n 翻譯鍵 | 宣告了 `I18nClass` 的模組，翻譯鍵自動註冊（卸載時自動取消註冊） |
| 依賴拓撲 | 按 `depends` 宣告排序，確保被依賴模組先載入；循環依賴以 `RuntimeError` 拒絕 |
| SDK 掛載 | 實例化後掛到 `sdk.<ModuleName>`，你才能 `sdk.MyModule.xxx` 存取 |

**卸載時框架幫你清理的**（對應上面的 U1→U7）：`on_unload` 跑完後再兜底清理——背景任務強制取消（`self.spawn` 建立的，優雅收尾請在 `on_unload` 自行做）、i18n 鍵、路由、命令/事件處理器、lifecycle 鉤子，最後移除 SDK 屬性。`purge=True` 額外刪除註冊存根 + 清理 `sys.modules`。

> 這些自動清理就是「你只需寫 `on_load`/`on_unload`，不用手動 unregister」的底氣——框架用 owner 歸屬把「誰註冊的誰清理」做成了一鍵式。

## SDK 物件

### 存取核心模組

```python
from ErisPulse import sdk

# 透過 sdk 物件存取所有核心模組
sdk.logger.info("日誌")
sdk.storage.set("key", "value")

# 模組自有小狀態（計數器/開關/上次執行時間）優先用 self.state——
# 鍵自動帶 module.state.<模組名>. 前綴，模組卸載重載後仍在：
count = self.state.get("runs", 0) + 1
self.state.set("runs", count)            # 同步（任意上下文）
await self.state.aset("runs", count)     # 非同步路徑
await self.state.aget("runs", 0)
config = sdk.config.getConfig("MyModule")
```

### 模組間通訊

```python
# 存取其他模組
other_module = sdk.OtherModule
result = await other_module.some_method()
```

## 適配器發送方法查詢

由於新的標準規範要求使用重寫 `__getattr__` 方法來實現兜底發送機制，導致無法使用 `hasattr` 方法來檢查方法是否存在。從 `2.3.5` 開始，新增了查詢發送方法的功能。

### 列出支援的發送方法

```python
# 列出平台支援的所有發送方法
methods = sdk.adapter.list_sends("onebot11")
# 返回: ["Text", "Image", "Voice", "Markdown", ...]
```

### 取得方法詳細資訊

```python
# 取得某個方法的詳細資訊
info = sdk.adapter.send_info("onebot11", "Text")
# 返回:
# {
#     "name": "Text",
#     "parameters": [
#         {"name": "text", "type": "str", "default": null, "annotation": "str"}
#     ],
#     "return_type": "Awaitable[Any]",
#     "docstring": "發送文字訊息..."
# }
```

## 配置管理

### 聲明式配置（推薦）

從 v2.5.2 起，模組可透過 `ConfigClass` 聲明配置類，與適配器使用同一套配置 Schema 系統。配置透過 `self.cfg` 即時讀取，修改後立即生效：

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Bases import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_key: str = field(
        default="",
        metadata={
            "description": {"i18n": "my_module.api_key", "default": "API 密鑰"},
            "required": True,
            "secret": True,
            "ui": {"widget": "password", "group": "basic", "order": 1},
        },
    )
    timeout: int = field(
        default=30,
        metadata={
            "description": {"i18n": "my_module.timeout", "default": "超時時間（秒）"},
            "ui": {"widget": "number", "group": "advanced", "order": 2},
        },
    )

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("模組已載入")

    async def on_unload(self, event):
        pass

    async def do_something(self):
        cfg = self.cfg  # 即時讀取，類型安全
        api_key = cfg.api_key
        timeout = cfg.timeout
```

`BaseConfig` 是通用配置基類，適用於適配器、模組、外部專案等任何場景。配置欄位支援 i18n 多語言描述（詳見 [i18n 文檔](../../advanced/i18n.md#配置欄位多語言)）。

> [!NOTE]
> 模組（含適配器）的載入、卸載、啟停等生命週期由框架統一管理（`module manager` / `scope` 提供查詢與控制 API）。`ConfigClass` 只應承載業務參數，模組無需在內部再次嵌套判斷「自己要不要啟動」的邏輯。

配置 Schema 系統還支援（v2.8.0+，詳見 [適配器 core-concepts](../adapters/core-concepts.md#metadata-約定)）：

- **docstring 自動生成欄位描述**：未聲明 metadata `description` 時，自動從 docstring 的 `:ivar 字段: 說明` 或 `Attributes:` 段提取兜底
- **嵌套 dataclass 配置**：欄位類型為嵌套 dataclass 時，schema/模板/校驗遞迴處理，WebUI 渲染為嵌套分組
- **`example` 不落盤欄位**：`metadata={"example": True}` 的欄位不寫入 config.toml，僅記錄在 `config.full.example`（適合繁雜又很少觸碰的進階配置項目），使用者手動設定後正常持久化

### 配置熱更新（on_config_update）

模組與適配器實作 `on_config_update(old, new)` 方法後，框架在**本模組相關配置實際變化**
時自動路由呼叫（無需自行訂閱配置事件），改 token / 開關 / 限流參數**免重啟**生效：

```python
class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    def on_config_update(self, old_config, new_config):
        # 聲明了 ConfigClass 時為類型安全配置物件（未聲明則為 dict）；
        # 運行時 setConfig() 觸發時 old_config 為 None（僅 new 有值）
        if old_config is None or new_config.api_key != old_config.api_key:
            self.logger.info("API key 已更新，重建客戶端")
            self._client = build_client(new_config.api_key)
```

觸發來源與路由規則：

- **運行時寫入**（程式碼或 Dashboard 調用 `setConfig()`）：按配置鍵前綴匹配路由——只有
  落在本模組配置鍵（或其子鍵）內的寫入才觸發，此時 `old_config` 為 `None`
- **配置檔案編輯**（檔案監聽觸發整樹對比）：新舊配置節不相等才觸發，此時 `old` / `new`
  分別為變更前後的配置物件
- 回呼內拋出的例外被框架捕獲記錄，不影響配置寫入本身

使用口徑：

- `self.cfg` 是即時讀取——不需要重建狀態的簡單參數（如超時秒數）在下一行程式碼就是新值，
  無需在此鉤子手動同步
- 需要重建的**有狀態資源**（客戶端連線、連線池、定時器）才在此鉤子處理

### 聲明式翻譯鍵（v2.7.0+）

從 v2.7.0 起，模組還可以像聲明 `ConfigClass` 一樣，透過嵌套類 `I18nClass` 集中聲明翻譯鍵。框架會在載入時**自動註冊**所有聲明的翻譯鍵，無需手動呼叫 `i18n.register()`，且註冊時機早於配置模板生成，確保配置描述中引用的 i18n 鍵已可用。

```python
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, I18nKey

class MyModule(BaseModule):
    # 配置類（可選）
    @dataclass
    class ConfigClass(BaseConfig):
        welcome_msg: str = field(
            default="歡迎",
            metadata={
                "description": {"i18n": "mymodule.welcome_msg", "default": "歡迎訊息"},
            },
        )

    # 翻譯鍵集合類（可選）
    class I18nClass(BaseI18n):
        # 屬性名自動拼接為完整鍵路徑：<模組名>.<屬性名>
        welcome_msg: I18nKey = I18nKey(
            default="Welcome Message",   # 語言無關的兜底
            zh_CN="歡迎訊息",
            zh_TW="歡迎訊息",
            en="Welcome Message",
            ja="ウェルカムメッセージ",
            ru="Приветственное сообщение",
        )
        hello: I18nKey = I18nKey(
            default="Hello, {name}!",
            zh_CN="你好，{name}！",
            zh_TW="你好，{name}！",
            en="Hello, {name}!",
            ja="こんにちは、{name}！",
            ru="Привет, {name}!",
        )
```

詳情見 [i18n 推薦寫法](../../advanced/i18n.md#推薦寫法通過-i18nclass-聲明翻譯鍵-v270)。

### 手動讀取配置（已廢棄）

> **已廢棄**：請改用 [聲明式配置](#聲明式配置推薦) + `self.cfg` 即時讀取。

```python
class MyModule(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk

    def _load_config(self):
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            self.sdk.config.setConfig("MyModule", {"api_key": "", "timeout": 30})
            return {"api_key": "", "timeout": 30}
        return config
```

## 儲存系統

### 基本使用

```python
# 儲存資料
sdk.storage.set("user:123", {"name": "張三"})

# 取得資料
user = sdk.storage.get("user:123", {})

# 刪除資料
sdk.storage.delete("user:123")
```

### 事務使用

```python
# 使用事務確保資料一致性
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
    # 如果任何操作失敗，所有變更都會回滾
```

## 事件處理

### 事件處理器註冊

```python
from ErisPulse.Core.Event import command, message

# 註冊命令
@command("info", help="取得資訊")
async def info_handler(event):
    await event.reply("這是資訊")

# 註冊訊息處理器
@message.on_group_message()
async def group_handler(event):
    sdk.logger.info(f"收到群訊息: {event.get_text()}")
```

### 事件處理器生命週期

框架會自動管理事件處理器的註冊和取消註冊，你只需要在 `on_load` 中註冊即可。

## 懶載入機制

### 工作原理

```python
# 模組首次被存取時才會初始化
result = await sdk.my_module.some_method()
# ↑ 這裡會觸發模組初始化
```

### 立即載入

對於需要立即初始化的模組（如監聽器、定時器）：

```python
@staticmethod
def get_load_strategy():
    return ModuleLoadStrategy(
        lazy_load=False,  # 立即載入
        priority=100
    )
```

## 錯誤處理

### 例外捕獲

```python
async def handle_event(self, event):
    try:
        # 業務邏輯
        await self.process_event(event)
    except ValueError as e:
        self.logger.warning(f"參數錯誤: {e}")
        await event.reply(f"參數錯誤: {e}")
    except Exception as e:
        self.logger.error(f"處理失敗: {e}")
        raise
```

### 日誌記錄

```python
# 使用不同的日誌級別
self.logger.debug("除錯資訊")    # 詳細除錯資訊
self.logger.info("執行狀態")      # 正常執行資訊
self.logger.warning("警告訊息")  # 警告訊息
self.logger.error("錯誤訊息")    # 錯誤訊息
self.logger.critical("致命錯誤") # 致命錯誤
```

## 相關文件

### 繼續學習路徑

- [Event 包裝類別](event-wrapper.md) - 事件處理詳解

### 深入與排查

- [模組最佳實踐](best-practices.md) - 開發高品質模組
- [模組開發入門](getting-started.md) - 回看第一個模組的搭建步驟