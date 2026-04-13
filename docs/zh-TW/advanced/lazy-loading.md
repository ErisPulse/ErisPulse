# 延遲載入模組系統

ErisPulse SDK 提供了強大的延遲載入模組系統，允許模組在實際需要時才進行初始化，從而顯著提升應用程式啟動速度和記憶體效率。

## 概述

延遲載入模組系統是 ErisPulse 的核心特性之一，它透過以下方式運作：

- **延遲初始化**：模組只有在第一次被存取時才會實際載入和初始化
- **透明使用**：對於開發者來說，延遲載入模組與一般模組在使用上幾乎沒有區別
- **自動依賴管理**：模組依賴會在被使用時自動初始化
- **生命週期支援**：對於繼承自 `BaseModule` 的模組，會自動呼叫生命週期方法

## 工作原理

### LazyModule 類別

延遲載入系統的核心是 `LazyModule` 類別，它是一個包裝器，在第一次存取時才實際初始化模組。

### 初始化過程

當模組首次被存取時，`LazyModule` 會執行以下操作：

1. 取得模組類別的 `__init__` 參數資訊
2. 根據參數決定是否傳入 `sdk` 參照
3. 設定模組的 `moduleInfo` 屬性
4. 對於繼承自 `BaseModule` 的模組，呼叫 `on_load` 方法
5. 觸發 `module.init` 生命週期事件

## 配置延遲載入

### 全域設定

在組態檔案中啟用/停用全域延遲載入：

```toml
[ErisPulse.framework]
enable_lazy_loading = true  # true=啟用延遲載入(預設)，false=停用延遲載入
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

## 使用延遲載入模組

### 基本使用

對於開發者來說，延遲載入模組與一般模組在使用上幾乎沒有區別：

```python
# 透過 SDK 存取延遲載入模組
from ErisPulse import sdk

# 以下存取會觸發模組延遲載入
result = await sdk.my_module.my_method()
```

### 非同步初始化

對於需要非同步初始化的模組，建議先顯式載入：

```python
# 先顯式載入模組
await sdk.load_module("my_module")

# 然後使用模組
result = await sdk.my_module.my_method()
```

### 同步初始化

對於不需要非同步初始化的模組，可以直接存取：

```python
# 直接存取會自動同步初始化
result = sdk.my_module.some_sync_method()
```

## 最佳實踐

### 建議使用延遲載入的情境 (lazy_load=True)

- 被動呼叫的工具類別
- 被動類模組

### 建議停用延遲載入的情境 (lazy_load=False)

- 註冊觸發器的模組（如：指令處理器、訊息處理器）
- 生命週期事件監聽器
- 定時任務模組
- 需要在應用程式啟動時就初始化的模組

### 載入優先級

```python
from ErisPulse.loaders import ModuleLoadStrategy

class MyModule(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=False,  # 立即載入
            priority=100      # 高優先級，數值越大優先級越高
        )
```

## 注意事項

1. 如果您的模組使用了延遲載入，如果其它模組從未在 ErisPulse 內進行過呼叫，則您的模組永遠不會被初始化。
2. 如果您的模組中包含了諸如監聽 Event 的模組，或其它主動監聽類似模組，請務必宣告需要立即被載入，否則會影響您模組的正常業務。
3. 我們不建議您停用延遲載入，除非有特殊需求，否則它可能為您帶來諸如依賴管理和生命週期事件等的問題。

## 相關文件

- [模組開發指南](../developer-guide/modules/getting-started.md) - 學習開發模組
- [最佳實踐](../developer-guide/modules/best-practices.md) - 瞭解更多最佳實踐