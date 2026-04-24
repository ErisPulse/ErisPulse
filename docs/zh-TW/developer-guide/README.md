# 開發者指南

本指南協助您開發自訂模組和適配器，以擴充 ErisPulse 的功能。

## 內容列表

### 模組開發

1. [模組開發入門](modules/getting-started.md) - 建立第一個模組
2. [模組核心概念](modules/core-concepts.md) - 模組的核心概念與架構
3. [Event 包裝類詳解](modules/event-wrapper.md) - Event 物件的完整說明
4. [模組最佳實踐](modules/best-practices.md) - 開發高品質模組的建議

### 適配器開發

1. [適配器開發入門](adapters/getting-started.md) - 建立第一個適配器
2. [適配器核心概念](adapters/core-concepts.md) - 適配器的核心概念
3. [SendDSL 詳解](adapters/send-dsl.md) - Send 訊息傳送 DSL 的完整說明
4. [事件轉換器](adapters/converter.md) - 實作事件轉換器
5. [適配器最佳實踐](adapters/best-practices.md) - 開發高品質適配器的建議

### 發布指南

- [發布與模組商店指南](publishing.md) - 將您的作品發布到 PyPI 和 ErisPulse 模組商店

## 開發準備

在開始開發之前，請確保您：

1. 閱讀了[基礎概念](../getting-started/basic-concepts.md)
2. 熟悉了[事件處理](../getting-started/event-handling.md)
3. 安裝了開發環境（Python >= 3.10）
4. 安裝了 ErisPulse SDK

## 開發類型選擇

根據您的需求選擇合適的開發類型：

### 模組開發

**適用場景：**
- 擴充機器人功能
- 實作特定業務邏輯
- 提供指令與訊息處理

**範例：**
- 天氣查詢機器人
- 音樂播放器
- 資料收集工具

**入門指南：** [模組開發入門](modules/getting-started.md)

### 適配器開發

**適用場景：**
- 連接新的訊息平台
- 實作跨平台通訊
- 提供平台特定功能

**範例：**
- Discord 適配器
- Slack 適配器
- 自訂平台適配器

**入門指南：** [適配器開發入門](adapters/getting-started.md)

## 開發工具

### 專案範本

ErisPulse 提供了範例專案作為參考：

- `examples/example-module/` - 模組範例
- `examples/example-adapter/` - 適配器範例

### 開發模式

使用熱重載模式進行開發：

```bash
epsdk run main.py --reload
```

### 除錯技巧

啟用 DEBUG 層級日誌：

```toml
[ErisPulse.logger]
level = "DEBUG"
```

使用模組自己的日誌記錄器：

```python
from ErisPulse import sdk

logger = sdk.logger.get_child("MyModule")
logger.debug("除錯資訊")
```

## 發布您的模組

完整的發布流程請參考 [發布與模組商店指南](publishing.md)，包括：

- PyPI 發布步驟
- ErisPulse 模組商店提交流程
- 適配器的發布

### 快速參考

```bash
# 建構並發布到 PyPI
python -m build
python -m twine upload dist/*
```

然後前往 [ErisPulse-ModuleRepo](https://github.com/ErisPulse/ErisPulse-ModuleRepo/issues/new?template=module_submission.md) 提交到模組商店。

## 相關文件

- [標準規範](../standards/) - 確保相容性的技術標準
- [平台特性指南](../platform-guide/) - 了解各平台適配器的特性