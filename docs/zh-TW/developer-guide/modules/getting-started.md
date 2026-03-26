# 模組開發入門

本指南帶你從零開始建立一個 ErisPulse 模組。

## 專案結構

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
requires-python = ">=3.9"
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
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")
        self.storage = sdk.storage
        self.config = self._load_config()
    
    @staticmethod
    def get_load_strategy():
        """返回模組載入策略"""
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=True,
            priority=0
        )
    
    async def on_load(self, event):
        """模組載入時呼叫"""
        @command("hello", help="發送問候")
        async def hello_command(event):
            name = event.get_user_nickname() or "朋友"
            await event.reply(f"你好，{name}！")
        
        self.logger.info("模組已載入")
    
    async def on_unload(self, event):
        """模組卸載時呼叫"""
        self.logger.info("模組已卸載")
    
    def _load_config(self):
        """載入模組配置"""
        config = self.sdk.config.getConfig("MyModule")
        if not config:
            default_config = {
                "api_url": "https://api.example.com",
                "timeout": 30
            }
            self.sdk.config.setConfig("MyModule", default_config)
            return default_config
        return config
```

## 測試模組

### 本地測試

```bash
# 在專案目錄安裝模組
epsdk install ./MyModule

# 執行專案
epsdk run main.py --reload
```

### 測試指令

發送指令測試：

```
/hello
```

## 核心概念

### BaseModule 基礎類別

所有模組必須繼承 `BaseModule`，提供以下方法：

| 方法 | 說明 | 必要 |
|------|------|------|
| `__init__(self)` | 建構函式 | 否 |
| `get_load_strategy()` | 返回載入策略 | 否 |
| `on_load(self, event)` | 模組載入時呼叫 | 是 |
| `on_unload(self, event)` | 模組卸載時呼叫 | 是 |

### SDK 物件

通過 `sdk` 物件存取核心功能：

```python
from ErisPulse import sdk

sdk.storage    # 儲存系統
sdk.config     # 設定系統
sdk.logger     # 日誌系統
sdk.adapter    # 介面卡系統
sdk.router     # 路由系統
sdk.lifecycle  # 生命週期系統
```

## 下一步

- [模組核心概念](core-concepts.md) - 深入了解模組架構
- [Event 包裝類別詳解](event-wrapper.md) - 學習 Event 物件
- [模組最佳實踐](best-practices.md) - 開發高品質模組