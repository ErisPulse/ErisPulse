# 慢載模組系統

ErisPulse SDK 提供了強大的慢載模組系統，允許模組在實際需要時才進行初始化，從而顯著提升應用啟動速度和記憶體效率。

## 概述

慢載模組系統是 ErisPulse 的核心特性之一，它透過以下方式運作：

- **延遲初始化**：模組只有在第一次被存取時才會實際載入和初始化
- **透明使用**：對開發者而言，慢載模組與一般模組在使用上幾乎沒有差別
- **自動依賴管理**：模組依賴會在被使用時自動初始化
- **生命週期支援**：對於繼承自 `BaseModule` 的模組，會自動呼叫生命週期方法

## 運作原理

### LazyModule 類別

慢載系統的核心是 `LazyModule` 類別，它是一個包裝器，在第一次存取時才實際初始化模組。

### 初始化過程

當模組首次被存取時，`LazyModule` 會執行以下操作：

1. 取得模組類別的 `__init__` 參數資訊
2. 根據參數決定是否傳入 `sdk` 引用
3. 設定模組的 `moduleInfo` 屬性
4. 對於繼承自 `BaseModule` 的模組，呼叫 `on_load` 方法
5. 觸發 `module.init` 生命週期事件

## 配置慢載

### 全域配置

在設定檔中啟用/停用全域慢載：

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true=啟用慢載(預設)，false=停用慢載
```

### 模組層級控制

模組可以透過實作 `get_load_strategy()` 靜態方法來控制載入策略：

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        """傳回模組載入策略"""
        return ModuleLoadStrategy(
            lazy_load=False,  # 傳回 False 表示立即載入
            priority=100      # 載入優先級，數值越大優先級越高
        )
```

## 使用慢載模組

### 基本使用

對開發者而言，慢載模組與一般模組在使用上幾乎沒有差別：

```python
# 透過 SDK 存取慢載模組
from ErisPulse import sdk

# 以下存取會觸發模組慢載
result = await sdk.my_module.my_method()
```

### 統一的模組取得入口

無論是透過 SDK 屬性、模組管理器屬性存取，還是透過 `module.get()` 查詢，對於「已註冊但尚未載入」的慢載模組，都會返回同一個慢載代理，存取其屬性才會真正觸發初始化：

```python
# 三種方式拿到的都是慢載代理（在模組未載入時），行為一致、對使用者透明
sdk.my_module          # 觸發載入的入口
sdk.module.my_module   # 同樣返回慢載代理
sdk.module.get("my_module")  # 也返回慢載代理，本身不會觸發載入

# 存取代理的任意屬性才會真正初始化模組
result = await sdk.my_module.my_method()
```

`module.get()` 是**查詢**介面，本身不觸發載入：
- 模組已載入 → 回傳真實實例
- 模組已註冊但未載入 → 回傳慢載代理（存取屬性才初始化）
- 模組未註冊 → 回傳 `None`

如需顯式觸發載入，請使用 `await sdk.load_module("my_module")`。

### 異步初始化

對於需要異步初始化的模組，建議先顯式載入：

```python
# 先顯式載入模組
await sdk.load_module("my_module")

# 然後使用模組
result = await sdk.my_module.my_method()
```

### 同步初始化

對於不需要異步初始化的模組，可以直接存取：

```python
# 直接存取會自動同步初始化
result = sdk.my_module.some_sync_method()
```

## 最佳實踐

### 推薦使用慢載的場景（lazy_load=True）

- 被動呼叫的工具類（如資料查詢模組，格式轉換器等，僅只在其他模組呼叫時才需要）

### 推薦停用慢載的場景（lazy_load=False）

- 註冊觸發器的模組（如：命令處理器，訊息處理器）
- 生命週期事件監聽器
- 定時任務模組
- 需要在應用啟動時就初始化的模組

> `priority` 參數控制立即載入模組間的初始化順序，數值越大越先初始化。同優先級的模組按註冊順序載入。

## 注意事項

1. 如果您的模組使用了慢載，如果其他模組從未在 ErisPulse 內進行過呼叫，則您的模組永遠不會被初始化。
2. 如果您的模組中包含了如監聽 Event 的模組，或其它主動監聽類似模組，請務必宣告需要立即被載入，否則會影響您模組的正常業務。
3. 我們不建議您停用慢載，除非有特殊需求，否則它可能會為您帶來如依賴管理和生命週期事件等的問題。

## 相關文件

- [模組開發指南](../developer-guide/modules/getting-started.md) - 學習開發模組
- [最佳實踐](../developer-guide/modules/best-practices.md) - 了解更多最佳實踐