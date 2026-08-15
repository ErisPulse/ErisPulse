# 模組開發入門

本指南將引導您從零開始建立一個 ErisPulse 模組。

## 專案結構

標準的模組結構：

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py

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

## __init__.py

```python
from .Core import Main

## Core.py - 基礎模組

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self.config = self._load_config()
    
    @staticmethod
    def get_load_strategy():
        """傳回模組載入策略"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0,
            depends=[]  # Optional: list of other modules to depend on
        )
    
    async def on_load(self, event):
        """模組載入時呼叫"""
        @command("hello", help="Send greeting")
        async def hello_command(event):
            name = event.get_user_nickname() or "Friend"
            await event.reply(f"Hello, {name}!")
        
        self.logger.info("Module loaded")
    
    async def on_unload(self, event):
        """模組卸載時呼叫"""
        self.logger.info("Module unloaded")
    
    def _load_config(self):
        """載入模組設定"""
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = {
                "api_url": "https://api.example.com",
                "timeout": 30
            }
            self.sdk.config.setConfig("MyModule", default_config)
            return default_config
        return config

## 測試模組

### 本機測試

```bash
# 在專案目錄安裝模組
epsdk install ./MyModule

# 執行專案
epsdk run main.py --reload
```

### 測試指令

傳送指令測試：

```
/hello

## 核心概念

### BaseModule 基類

所有模組必須繼承 `BaseModule`，提供以下方法：

| 方法 | 說明 | 必須 |
|------|------|------|
| `__init__(self)` | 建構函數 | 否 |
| `get_load_strategy()` | 返回載入策略 | 否 |
| `get_meta()` | 返回模組介紹元資訊（選填） | 否 |
| `on_load(self, event)` | 模組載入時呼叫 | 是 |
| `on_unload(self, event)` | 模組卸載時呼叫 | 是 |

### 模組介紹 meta

透過 `get_meta()` 宣告模組的介紹元資訊（這個模組是做什麼的、屬於哪一類等）。
元資訊是模組的**通用介紹資料**，供 help 模組、Dashboard 模組列表、模組商店等各類介面/生態模組消費。

與 `get_load_strategy()` 返回 `ModuleLoadStrategy` 一致，**推薦返回 `ModuleMeta` 設定類別實例**（屬性鍵入、IDE 自動補全），也兼容直接返回 dict：

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

兼容寫法（dict）：

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

- `module.get_meta("MyModule")` 讀取已解析的元資訊（類別宣告 > 註冊 info，自動補全該模組的指令名）。
- `module.get_commands_overview()` 聚合「模組 meta + 其註冊的指令（別名/分組/幫助）」，按模組組織的指令總覽。
- 指令歸屬模組透過 `cmd_info["owner"]` 獲取（註冊時由上下文系統自動注入）。

#### meta 欄位的 i18n 支援

元資訊欄位值可用純字串，或 i18n 字典 `{"i18n": "key.path", "default": "兜底文本"}`（與設定 `description` 約定一致）。
翻譯鍵透過 `I18nClass` 宣告註冊，`module.get_meta()` 讀取時自動解析為當前語言文字：

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

sdk.storage    # 存儲系統
sdk.config     # 設定系統
sdk.logger     # 日誌系統
sdk.adapter    # 适配器系統
sdk.router     # 路由系統
sdk.lifecycle  # 生命週期系統

## 下一階段

- [模組核心概念](core-concepts.md) - 深入了解模組架構
- [Event 包裝類別詳解](event-wrapper.md) - 學習 Event 物件
- [模組最佳實踐](best-practices.md) - 開發高品質模組