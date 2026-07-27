# 模組開發最佳實踐

本文檔提供了 ErisPulse 模組開發的最佳實踐建議。

## 模組設計

### 1. 單一職責原則

每個模組應該只負責一個核心功能：

```python
# 好的設計：每個模組只負責一個功能
class WeatherModule(BaseModule):
    """天氣查詢模組"""
    pass

class NewsModule(BaseModule):
    """新聞查詢模組"""
    pass

# 不好的設計：一個模組負責多個不相關的功能
class UtilityModule(BaseModule):
    """包含天氣、新聞、笑話等多個功能"""
    pass
```

### 2. 模組命名規範

```toml
[project]
name = "ErisPulse-ModuleName"  # 使用 ErisPulse- 前綴
```

### 3. 清晰的配置管理

推薦使用宣告式配置（`ConfigClass` + `BaseConfig`），獲得類型安全、自動範本生成、WebUI 表單支援等能力：

```python
from dataclasses import dataclass, field
from ErisPulse.runtime.config_schema import BaseConfig

@dataclass
class MyModuleConfig(BaseConfig):
    api_url: str = field(default="https://api.example.com", metadata={
        "description": {"i18n": "my_module.api_url", "default": "API 位址"},
    })
    timeout: int = field(default=30, metadata={
        "description": {"i18n": "my_module.timeout", "default": "逾時時間（秒）"},
    })
    cache_ttl: int = field(default=3600, metadata={
        "description": {"i18n": "my_module.cache_ttl", "default": "快取存活時間（秒）"},
    })

class MyModule(BaseModule):
    ConfigClass = MyModuleConfig

    async def do_something(self):
        cfg = self.cfg  # 類型安全，即時讀取
        await self._fetch(cfg.api_url, timeout=cfg.timeout)
```

也可以在繼續使用手動方式讀寫配置儲存（見[模組核心概念](core-concepts.md#配置管理)）。

### 宣告式翻譯鍵（v2.7.0+）

模組可以透過 `I18nClass` 集中宣告翻譯鍵，框架自動註冊到 i18n 系統，無需手動呼叫 `i18n.register()`。

```python
from ErisPulse.Core.Bases import BaseI18n, I18nKey

class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        # 帶預留位置的業務翻譯鍵
        welcome: I18nKey = I18nKey(
            default="Welcome, {name}!",
            zh_CN="歡迎你，{name}！",
            zh_TW="歡迎你，{name}！",
            en="Welcome, {name}!",
            ja="ようこそ、{name}！",
            ru="Добро пожаловать, {name}!",
        )
        # 配置欄位描述的翻譯
        api_url: I18nKey = I18nKey(
            default="API URL",
            zh_CN="API 位址",
            zh_TW="API 位址",
            en="API URL",
            ja="API URL",
            ru="API URL",
        )
```

詳細用法見 [i18n 文檔](../../advanced/i18n.md#推薦寫法透過-i18nclass-宣告翻譯鍵-v270)。

## 非同步編程

### 1. 使用非同步函式庫

```python
# 推薦使用 SDK 內建 HTTP 客戶端（非同步，自動日誌和統計）
from ErisPulse.Core import client

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await client.get(url)
        return await resp.json()

# 也可透過 sdk.client 使用（效果相同）
from ErisPulse import sdk

class MyModule(BaseModule):
    async def fetch_data(self, url):
        resp = await sdk.client.get(url)
        return await resp.json()

# 不要使用 aiohttp 直接匯入（不便於框架統一管理）
import aiohttp

class MyModule(BaseModule):
    async def fetch_data(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

# 不要使用 requests（同步，會阻塞事件迴圈）
import requests

class MyModule(BaseModule):
    def fetch_data(self, url):
        return requests.get(url).json()  # 會阻塞事件迴圈
```

### 2. 正確的非同步操作

```python
async def handle_command(self, event):
    # 使用 create_task 讓耗時操作在背景執行
    task = asyncio.create_task(self._long_operation())
    
    # 如果需要等待結果
    result = await task
```

### 3. 資源管理

```python
async def on_load(self, event):
    # SDK 客戶端已自動管理連線池，無需手動建立 session
    pass
    
async def on_unload(self, event):
    # 如需自訂客戶端，記得清理資源
    pass
```

## 事件處理

### 1. 使用 Event 包裝類別

```python
# 使用 Event 包裝類別的便捷方法
@command("info")
async def info_command(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    await event.reply(f"你好，{nickname}！")

# 而非直接存取字典
@command("info")
async def info_command(event):
    user_id = event["user_id"]  # 不夠清晰，容易出錯
```

### 2. 合理使用懶載入

```python
# 命令處理模組需要立即載入
class CommandModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# 監聽器模組需要立即載入
class ListenerModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=False)

# 工具模組適合懶載入
class UtilityModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(lazy_load=True)
```

### 3. 事件處理器註冊

```python
async def on_load(self, event):
    # 在 on_load 中註冊事件處理器
    @command("hello")
    async def hello_handler(event):
        await event.reply("你好！")
    
    @message.on_group_message()
    async def group_handler(event):
        self.logger.info("收到群訊息")
    
    # 不需要手動註銷，框架會自動處理
```

## 錯誤處理

### 1. 分類異常處理

```python
async def handle_event(self, event):
    try:
        result = await self._process(event)
    except ValueError as e:
        # 預期的業務錯誤
        self.logger.warning(f"業務警告: {e}")
        await event.reply(f"參數錯誤: {e}")
    except aiohttp.ClientError as e:
        # 網路錯誤（推薦使用 sdk.client + ClientError 替代）
        # 舊程式碼直接用 aiohttp 仍可正常運作，但新程式碼推薦使用 ErisPulse 異常體系
        self.logger.error(f"網路錯誤: {e}")
        await event.reply("網路請求失敗，請稍後重試")
    except Exception as e:
        # 未預期的錯誤
        self.logger.error(f"未知錯誤: {e}", exc_info=True)
        await event.reply("處理失敗，請聯繫管理員")
        raise
```

### 2. 逾時處理

```python
# 推薦使用 SDK 內建客戶端（自帶逾時和重試）
from ErisPulse.Core import client
from ErisPulse.Core.Bases.errors import ClientTimeoutError

async def fetch_with_timeout(self, url, timeout=30):
    try:
        resp = await client.get(url, timeout=timeout)
        return await resp.json()
    except ClientTimeoutError:
        self.logger.warning(f"請求逾時: {url}")
        raise
```

## 儲存系統

### 1. 使用事務

```python
# 使用事務確保資料一致性
async def update_user(self, user_id, data):
    with self.sdk.storage.transaction():
        self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
        self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])

# ❌ 不使用事務可能導致資料不一致
async def update_user(self, user_id, data):
    self.sdk.storage.set(f"user:{user_id}:profile", data["profile"])
    # 如果這裡出錯，上面的設定無法回滾
    self.sdk.storage.set(f"user:{user_id}:settings", data["settings"])
```

### 2. 批次操作

```python
# 使用批次操作提高效能
def cache_multiple_items(self, items):
    self.sdk.storage.set_multi({
        f"item:{k}": v for k, v in items.items()
    })

# ❌ 多次呼叫效率低
def cache_multiple_items(self, items):
    for k, v in items.items():
        self.sdk.storage.set(f"item:{k}", v)
```

## 日誌記錄

### 1. 合理使用日誌層級

```python
# DEBUG: 詳細的偵錯資訊（僅開發時）
self.logger.debug(f"輸入參數: {params}")

# INFO: 正常運行資訊
self.logger.info("模組已載入")
self.logger.info(f"處理請求: {request_id}")

# WARNING: 警告資訊，不影響主要功能
self.logger.warning(f"設定項 {key} 未設定，使用預設值")
self.logger.warning("API 回應慢，可能需要優化")

# ERROR: 錯誤資訊
self.logger.error(f"API 請求失敗: {e}")
self.logger.error(f"處理事件失敗: {e}", exc_info=True)

# CRITICAL: 致命錯誤，需要立即處理
self.logger.critical("資料庫連線失敗，機器人無法正常運行")
```

### 2. 結構化日誌

```python
# 使用結構化日誌，便於解析
self.logger.info(f"處理請求: request_id={request_id}, user_id={user_id}, duration={duration}ms")

# ❌ 使用非結構化日誌
self.logger.info(f"處理請求了，來自使用者 {user_id}，用時 {duration} 毫秒")
```

## 效能優化

### 1. 使用快取

```python
class MyModule(BaseModule):
    def __init__(self):
        self._cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_data(self, key):
        async with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            
            # 從資料庫獲取
            data = await self._fetch_from_db(key)
            
            # 快取資料
            self._cache[key] = data
            return data
```

### 2. 避免阻塞性操作

```python
# 使用非同步操作
async def process_message(self, event):
    # 非同步處理
    await self._async_process(event)

# ❌ 阻塞性操作
async def process_message(self, event):
    # 同步操作，阻礙事件迴圈
    result = self._sync_process(event)
```

## 安全性

### 1. 敏感資料保護

```python
# 敏感資料儲存在設定中
class MyModule(BaseModule):
    def _load_config(self):
        config = self.sdk.config.getConfig("MyModule")
        self.api_key = config.get("api_key")
        
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            raise ValueError("請在 config.toml 中設定有效的 API 金鑰")

# ❌ 敏感資料硬編碼
class MyModule(BaseModule):
    API_KEY = "sk-1234567890"  # 不要這樣做！
```

### 2. 輸入驗證

```python
# 驗證使用者輸入
async def process_command(self, event):
    user_input = event.get_text()
    
    # 驗證輸入長度
    if len(user_input) > 1000:
        await event.reply("輸入過長，請重新輸入")
        return
    
    # 驗證輸入格式
    if not re.match(r'^[a-zA-Z0-9]+$', user_input):
        await event.reply("輸入格式不正確")
        return
```

## 測試

### 1. 單元測試

```python
import pytest
from ErisPulse.Core.Bases import BaseModule

class TestMyModule:
    def test_load_config(self):
        """測試設定載入"""
        module = MyModule()
        config = module._load_config()
        assert config is not None
        assert "api_url" in config
```

### 2. 整合測試

```python
@pytest.mark.asyncio
async def test_command_handling():
    """測試命令處理"""
    module = MyModule()
    await module.on_load({})
    
    # 模擬命令事件
    event = create_test_command_event("hello")
    await module.handle_command(event)
```

## 部署

### 1. 版本管理

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
```

遵循語義化版本：
- MAJOR.MINOR.PATCH
- 主版本：不相容的 API 變更
- 次版本：向下相容的功能新增
- 修訂號：向下相容的問題修正

### 2. 文檔完善

```markdown
# README.md

- 模組簡介
- 安裝說明
- 設定說明
- 使用範例
- API 文檔
- 貢獻指南
```

## 相關文檔

- [模組開發入門](getting-started.md) - 建立第一個模組
- [模組核心概念](core-concepts.md) - 理解模組架構
- [Event 包裝類別](event-wrapper.md) - 事件處理詳解

請直接傳回翻譯後的完整 Markdown 內容，不要包含任何其他文字。