# 模組開發入門

本指南帶你從零開始建立一個 ErisPulse 模組。

## 項目結構

一個標準的模組結構：

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py
```

## pyproject.toml 配置

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "模組功能描述"
readme = "README.md"
requires-python = ">=3.10"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]
dependencies = []

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

## __init__.py

```python
from .Core import Main
```

## Core.py - 基礎模組

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command

class Main(BaseModule):
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
    
    @staticmethod
    def get_load_strategy():
        """返回模組加載策略"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[],  # 可選：依賴的其他模組列表
            # 可選：事件驅動懶激活——宣告觸發器，首個匹配事件/命令到達時自動加載
            # activate_on=[{"command": {"name": "hello", "help": "發送問候"}}],
        )
    
    async def on_load(self, event):
        """模組加載時調用"""
        @command("hello", help="發送問候")
        async def hello_command(event):
            name = event.get_user_nickname() or "朋友"
            await event.reply(f"你好，{name}！")
        
        self.logger.info("模組已加載")
    
    async def on_unload(self, event):
        """模組卸載時調用"""
        self.logger.info("模組已卸載")
```

> **配置讀取**：上面的基礎範例未使用配置。需要讀取配置時，推薦宣告嵌套的 `ConfigClass` 並透過 `self.cfg` 即時讀取（見 [模組核心概念](core-concepts.md#宣告式配置推薦)）。手動呼叫 `_load_config()` 的舊寫法已廢棄。

## 測試模組

### 本地測試

```bash
# 在專案目錄安裝模組
epsdk install ./MyModule

# 運行專案
epsdk run main.py --reload
```

### 測試命令

傳送命令測試：

```
/hello
```

## 核心概念

### BaseModule 基類

所有模組必須繼承 `BaseModule`，提供以下方法：

| 方法 | 說明 | 必須 |
|------|------|------|
| `__init__(self, sdk)` | 建構函式（框架傳入 `sdk` 實例） | 否 |
| `get_load_strategy()` | 返回載入策略 | 否 |
| `get_meta()` | 返回模組介紹元資訊（可選） | 否 |
| `on_load(self, event)` | 模組載入時調用 | 是 |
| `on_unload(self, event)` | 模組卸載時調用 | 是 |

### 模組介紹 meta

> [!NOTE]
> 本特性需要 ErisPulse **2.8.0+**。

透過 `get_meta()` 聲明模組的介紹元資訊（這個模組是用來做什麼的、屬於哪一類等）。  
元資訊是模組的**通用介紹資料**，供 help 模組、Dashboard 模組列表、模組商店等各類介面/生態模組消費。

與 `get_load_strategy()` 返回 `ModuleLoadStrategy` 一致，**推薦返回 `ModuleMeta` 配置類實例**（屬性鍵入、IDE 自動補全），也兼容直接返回 dict：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天氣",               # 顯示名（預設註冊名）
            description="查詢城市天氣",  # 模組簡介
            version="1.0.0",
            author="ErisDev",
            group="工具",               # 功能分組
            tags=["天氣", "查詢"],
        )
```

相容寫法（dict）：

```python
class MyModule(BaseModule):
    @staticmethod
    def get_meta() -> dict:
        return {
            "name": "天氣",
            "description": "查詢城市天氣",
            "version": "1.0.0",
            "author": "ErisDev",
            "group": "工具",
            "tags": ["天氣", "查詢"],
        }
```

- `module.get_meta("MyModule")` 讀取已解析的元資訊（類宣告 > 註冊 info，自動補全該模組的指令名）。
- `module.get_commands_overview()` 聚合「模組 meta + 其註冊的指令（別名/分組/幫助）」，按模組組織的指令總覽。
- 指令歸屬模組透過 `cmd_info["owner"]` 取得（註冊時由上下文系統自動注入）。

#### meta 字段的 i18n 支援

元資訊字段值可用純字串，或 i18n 字典 `{"i18n": "key.path", "default": "兜底文本"}`（與設定 `description` 約定一致）。  
翻譯鍵透過 `I18nClass` 聲明註冊，`module.get_meta()` 讀取時自動解析為當前語言文本：

```python
class MyModule(BaseModule):
    class I18nClass(BaseI18n):
        meta_description: I18nKey = I18nKey(
            default="Weather lookup",
            zh_CN="查詢城市天氣",
            en="Weather lookup",
        )

    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(
            name="天氣",
            description={"i18n": "MyModule.meta_description", "default": "Weather lookup"},
        )
```

### SDK 物件

透過 `sdk` 物件存取核心功能：

```python
from ErisPulse import sdk

sdk.storage    # 儲存系統
sdk.config     # 設定系統
sdk.logger     # 日誌系統
sdk.adapter    # 適配器系統
sdk.router     # 路由系統
sdk.lifecycle  # 生命週期系統
```

## 下一步

- [模組核心概念](core-concepts.md) - 深入了解模組架構
- [Event 包裝類別詳解](event-wrapper.md) - 學習 Event 物件
- [模組最佳實踐](best-practices.md) - 開發高品質模組