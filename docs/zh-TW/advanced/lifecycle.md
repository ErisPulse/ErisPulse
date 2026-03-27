# 生命週期管理

ErisPulse 提供完整的生命週期事件系統，用於監控系統各組件的運行狀態。生命週期事件支援點式結構事件監聽，例如可以監聽 `module.init` 來捕獲所有模組初始化事件。

## 標準生命週期事件

系統定義了以下標準事件類別：

```python
STANDARD_EVENTS = {
    "core": ["init.start", "init.complete"],
    "module": ["load", "init", "unload"],
    "adapter": ["load", "start", "status.change", "stop", "stopped"],
    "server": ["start", "stop"]
}
```

## 事件資料格式

所有生命週期事件都遵循標準格式：

```json
{
    "event": "事件名稱",
    "timestamp": 1234567890,
    "data": {},
    "source": "ErisPulse",
    "msg": "事件描述"
}
```

## 事件處理機制

### 點式結構事件

ErisPulse 支援點式結構的事件命名，例如 `module.init`。當觸發具體事件時，也會觸發其父級事件：

- 觸發 `module.init` 事件時，也會觸發 `module` 事件
- 觸發 `adapter.status.change` 事件時，也會觸發 `adapter.status` 和 `adapter` 事件

### 萬用字元事件處理器

可以註冊 `*` 事件處理器來捕獲所有事件。

## 標準生命週期事件

### 核心初始化事件

| 事件名稱 | 觸發時機 | 資料結構 |
|---------|---------|---------|
| `core.init.start` | 核心初始化開始時 | `{}` |
| `core.init.complete` | 核心初始化完成時 | `{"duration": "初始化耗時(秒)", "success": true/false}` |

### 模組生命週期事件

| 事件名稱 | 觸發時機 | 資料結構 |
|---------|---------|---------|
| `module.load` | 模組載入完成時 | `{"module_name": "模組名", "success": true/false}` |
| `module.init` | 模組初始化完成時 | `{"module_name": "模組名", "success": true/false}` |
| `module.unload` | 模組卸載時 | `{"module_name": "模組名", "success": true/false}` |

### 適配器生命週期事件

| 事件名稱 | 觸發時機 | 資料結構 |
|---------|---------|---------|
| `adapter.load` | 適配器載入完成時 | `{"platform": "平台名", "success": true/false}` |
| `adapter.start` | 適配器開始啟動時 | `{"platforms": ["平台名列表"]}` |
| `adapter.status.change` | 適配器狀態發生變化時 | `{"platform": "平台名", "status": "狀態", "retry_count": 重試次數, "error": "錯誤資訊"}` |
| `adapter.stop` | 適配器開始關閉時 | `{}` |
| `adapter.stopped` | 適配器關閉完成時 | `{}` |

### 伺服器生命週期事件

| 事件名稱 | 觸發時機 | 資料結構 |
|---------|---------|---------|
| `server.start` | 伺服器啟動時 | `{"base_url": "基礎url","host": "主機位址", "port": "埠號"}` |
| `server.stop` | 伺服器停止時 | `{}` |

## 使用範例

### 生命週期事件監聽

```python
from ErisPulse.Core import lifecycle

# 監聽特定事件
@lifecycle.on("module.init")
async def module_init_handler(event_data):
    print(f"模組 {event_data['data']['module_name']} 初始化完成")

# 監聽父級事件（點式結構）
@lifecycle.on("module")
async def on_any_module_event(event_data):
    print(f"模組事件: {event_data['event']}")

# 監聽所有事件（萬用字元）
@lifecycle.on("*")
async def on_any_event(event_data):
    print(f"系統事件: {event_data['event']}")
```

### 提交生命週期事件

```python
from ErisPulse.Core import lifecycle

# 基本事件提交
await lifecycle.submit_event(
    "custom.event",
    data={"custom_field": "custom_value"},
    source="MyModule",
    msg="自訂事件描述"
)
```

### 計時器功能

生命週期系統提供計時器功能，用於效能測量：

```python
from ErisPulse.Core import lifecycle

# 開始計時
lifecycle.start_timer("my_operation")

# 執行一些操作...

# 獲取持續時間（不停止計時器）
elapsed = lifecycle.get_duration("my_operation")
print(f"已運行 {elapsed} 秒")

# 停止計時並獲取持續時間
total_time = lifecycle.stop_timer("my_operation")
print(f"操作完成，總耗時 {total_time} 秒")
```

## 模組中使用生命週期

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    async def on_load(self, event):
        # 監聽模組生命週期事件
        @sdk.lifecycle.on("module.load")
        async def on_module_load(event_data):
            module_name = event_data['data'].get('module_name')
            if module_name != "MyModule":
                sdk.logger.info(f"其他模組載入: {module_name}")
        
        # 提交自訂事件
        await sdk.lifecycle.submit_event(
            "custom.ready",
            source="MyModule",
            msg="MyModule 已準備好接收事件"
        )
```

## 注意事項

1. **事件來源標識**：提交自訂事件時，建議設置明確的 `source` 值，便於追蹤事件來源
2. **事件命名規範**：建議使用點式結構命名事件，便於使用父級監聽
3. **計時器命名**：計時器 ID 應具有描述性，避免與其他組件衝突
4. **非同步處理**：所有生命週期事件處理器都是非同步的，不要阻塞事件迴圈
5. **錯誤處理**：在事件處理器中應該做好異常處理，避免影響其他監聽器

## 相關文件

- [模組開發指南](../developer-guide/modules/getting-started.md) - 了解模組生命週期方法
- [最佳實踐](../developer-guide/modules/best-practices.md) - 生命週期事件使用建議